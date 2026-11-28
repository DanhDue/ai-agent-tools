#!/usr/bin/env python3
"""
Antigravity Quota Dashboard with Card-style Progress Bars.

Color Rules:
  >= 50%           : GREEN (#72bc82)
  >= 10% and < 50% : AMBER (#f59e0b)
  < 10%            : RED   (#ef4444)

Usage:
  agy-quota                 # Check current active profile
  agy-quota <profile>       # Check specific profile (e.g. danhdue, mommy)
  agy-quota all             # Check all profiles from ~/.zshrc
  agy-quota all --table     # Compact table summary for all profiles
"""

import sys
import os
import re
import json
import time
import datetime
import subprocess
import signal
import http.server
import socketserver
import urllib.parse
import urllib.request
import sqlite3
import base64
import hashlib
import importlib.util
import random
import shlex
import shutil
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SERVER_STARTUP_MTIME: int = int(Path(__file__).stat().st_mtime)
_RELOAD_PENDING: bool = False

GEMINI_MODEL_CANDIDATES = (
    "gemini-3.8-flash-low",
    "gemini-4-hydrogen-low",
    "gemini-3.8-flash-medium",
    "gemini-4-hydrogen-medium",
    "gemini-3.8-flash-high",
)
CLAUDE_MODEL_CANDIDATES = (
    "claude-sonnet-5-5-low",
    "claude-sonnet-4-6",
    "claude-sonnet-5-5-medium",
    "claude-opus-5-5-low",
    "claude-opus-4-6-thinking",
    "gpt-oss-120b-medium",
)
ARGON_MODEL_CANDIDATES = (
    "gemini-4-argon-low",
    "gemini-4-argon-medium",
    "gemini-4-argon-high",
)

_REFRESH_SESSION_MOD = None


def _load_refresh_session_module():
    """Dynamically locate and load sibling refresh_session.py module."""
    global _REFRESH_SESSION_MOD
    if _REFRESH_SESSION_MOD is not None:
        return _REFRESH_SESSION_MOD
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "skills" / "refresh-session" / "resources" / "scripts" / "refresh_session.py",
        Path(REAL_HOME) / ".gemini" / "config" / "plugins" / "d3nexus" / "skills" / "refresh-session" / "resources" / "scripts" / "refresh_session.py",
    ]
    for cand in candidates:
        if cand.is_file():
            spec = importlib.util.spec_from_file_location("d3nexus_refresh_session", str(cand))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                _REFRESH_SESSION_MOD = mod
                return mod
    return None


def is_bucket_activated(
    bucket: dict | None,
    window_seconds: int,
    now_ts: float | None = None,
    freeze_grace_sec: int = 180,
) -> bool:
    """Delegate bucket-activation check to refresh_session module with built-in fallback."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "is_bucket_activated"):
        return mod.is_bucket_activated(bucket, window_seconds, now_ts=now_ts, freeze_grace_sec=freeze_grace_sec)
    if not bucket or bucket.get("unavailable"):
        return False
    if "available" in bucket and not bucket.get("available"):
        return False
    frac = bucket.get("fraction") if bucket.get("fraction") is not None else bucket.get("remaining_fraction")
    if frac is not None and float(frac) < 0.999:
        return True
    if "used some" in str(bucket.get("description") or "").lower():
        return True
    reset_str = str(bucket.get("resetTime") or bucket.get("reset_time") or "").strip()
    if reset_str:
        try:
            dt = datetime.datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
            now = now_ts if now_ts is not None else time.time()
            rem = dt.timestamp() - now
            if 0 < rem < (window_seconds - freeze_grace_sec):
                return True
        except Exception:
            pass
    return False


def parse_agy_models_output(stdout: str) -> list[str]:
    """Parse model IDs from `agy models` stdout."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "parse_agy_models_output"):
        return mod.parse_agy_models_output(stdout)
    models = []
    for raw in (stdout or "").splitlines():
        tok = raw.strip().split()[0] if raw.strip() else ""
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{2,}", tok) and tok not in models:
            models.append(tok)
    return models


HYBRID_MODELS_TTL_SECONDS = 86400
_MODELS_NOISE_TOKENS = {"model", "models", "available", "id", "name"}
_RAW_ARGON_SKU_LABELS = {
    "gemini-argon-wtu-weekly": "Gemini 4 Argon",
    "gemini-argon-weekly": "Gemini 4 Argon",
    "gemini-argon": "Gemini 4 Argon",
}


def _canonical_model_label(model_id: str, inline_label: str = "") -> str:
    """Map an `agy models` ID to its clean human-readable family label."""
    mid = model_id.lower()
    if "orchestrator" in mid:
        if "argon" in mid or "g1-pro" in mid:
            return "Orchestrator (Argon)"
        if "carbon" in mid:
            return "Orchestrator (Carbon)"
        return "Orchestrator"
    if "carbon" in mid and "gemini" in mid:
        m = re.search(r"gemini-(\d+(?:[.-]\d+)?)-carbon", mid)
        ver = m.group(1).replace("-", ".") if m else "4"
        return f"Gemini {ver} Carbon"
    if "argon" in mid:
        m = re.search(r"gemini-(\d+(?:[.-]\d+)?)-argon", mid)
        ver = m.group(1).replace("-", ".") if m else "4"
        return f"Gemini {ver} Argon"
    if "hydrogen" in mid:
        m = re.search(r"gemini-(\d+(?:[.-]\d+)?)-hydrogen", mid)
        ver = m.group(1).replace("-", ".") if m else "4"
        return f"Gemini {ver} Hydrogen"
    if "flash" in mid and "gemini" in mid:
        m = re.search(r"gemini-(\d+(?:[.-]\d+)?)-flash", mid)
        ver = m.group(1).replace("-", ".") if m else "3.8"
        suffix = " Flash-Lite" if "lite" in mid else " Flash"
        return f"Gemini {ver}{suffix}"
    if any(k in mid for k in ("claude", "sonnet", "opus", "haiku")):
        variant = "Sonnet" if "sonnet" in mid else ("Opus" if "opus" in mid else "Haiku")
        m = re.search(r"(?:sonnet|opus|haiku)-(\d+(?:[.-]\d+)?)", mid)
        ver = f" {m.group(1).replace('-', '.')}" if m else ""
        return f"Claude {variant}{ver}"
    if "gpt-oss-120b" in mid:
        return "GPT-OSS 120B"
    if inline_label:
        return inline_label
    return model_id


def parse_agy_models_catalog(stdout: str) -> list[dict]:
    """Parse `agy models` stdout into structured `{id, label, quotaFamily, tags}` entries."""
    if not isinstance(stdout, str) or not stdout.strip():
        return []
    inline_labels: dict[str, str] = {}
    for raw in stdout.splitlines():
        parts = raw.strip().split(None, 1)
        if len(parts) == 2:
            inline_labels.setdefault(parts[0], parts[1].strip())

    catalog: list[dict] = []
    for model_id in parse_agy_models_output(stdout):
        mid = model_id.lower()
        if mid in _MODELS_NOISE_TOKENS:
            continue
        tags: list[str] = []
        if "carbon" in mid:
            tags.append("carbon")
        if "argon" in mid or ("orchestrator" in mid and "g1-pro" in mid):
            tags.append("argon")
        if "orchestrator" in mid:
            tags.append("orchestrator")
        if "hydrogen" in mid:
            tags.append("hydrogen")
        if "flash" in mid:
            tags.append("flash")
        if any(k in mid for k in ("claude", "sonnet", "opus", "haiku")):
            tags.append("claude")
        if "gpt" in mid:
            tags.append("gpt")
        if "g1-pro" in mid:
            tags.append("g1-pro")

        if "claude" in tags or "gpt" in tags:
            quota_family = "claude"
        elif "argon" in tags:
            quota_family = "argon"
        elif "gemini" in mid or any(
            t in tags for t in ("carbon", "hydrogen", "flash", "orchestrator")
        ):
            quota_family = "gemini"
        else:
            quota_family = "other"

        catalog.append(
            {
                "id": model_id,
                "label": _canonical_model_label(model_id, inline_labels.get(model_id, "")),
                "quotaFamily": quota_family,
                "tags": tags,
            }
        )
    return catalog


_GROUP_MODELS_PREFIX_RE = re.compile(r"^models\s+within\s+this\s+group\s*:\s*", re.IGNORECASE)
_PROSE_DESC_MARKERS = (
    "for paid ",
    "quota is ",
    "available on ",
    "within each group",
    "limits will last",
    "you have used",
)


def parse_usage_group_models(groups: list) -> dict:
    """Extract normalized model names and deterministic SHA-256 signature from `/usage` groups."""
    group_descriptions: dict[str, str] = {"gemini": "", "claude": "", "argon": ""}
    group_models: dict[str, list[str]] = {"gemini": [], "claude": [], "argon": []}
    has_dedicated_argon = False
    sig_pairs: list[tuple[str, str]] = []

    if isinstance(groups, list):
        for g in groups:
            if not isinstance(g, dict):
                continue
            raw_name = g.get("name")
            norm_name = re.sub(r"\s+", " ", str(raw_name or "")).strip()
            g_low = norm_name.lower()
            raw_desc = g.get("description")
            norm_desc = (
                re.sub(r"\s+", " ", raw_desc).strip() if isinstance(raw_desc, str) else ""
            )
            sig_pairs.append((g_low, norm_desc))

            family: str | None = None
            if "argon" in g_low:
                family = "argon"
                has_dedicated_argon = True
            elif "claude" in g_low or "gpt" in g_low:
                family = "claude"
            elif "gemini" in g_low:
                family = "gemini"

            if family is None:
                continue
            if norm_desc and not group_descriptions[family]:
                group_descriptions[family] = norm_desc

            has_models_prefix = bool(_GROUP_MODELS_PREFIX_RE.match(norm_desc))
            if (
                any(marker in norm_desc.lower() for marker in _PROSE_DESC_MARKERS)
                and not has_models_prefix
            ):
                continue

            stripped_desc = _GROUP_MODELS_PREFIX_RE.sub("", norm_desc).strip()
            seen_lower = {m.lower() for m in group_models[family]}
            for token in stripped_desc.split(","):
                clean = re.sub(r"\s+", " ", token).strip()
                if not clean:
                    continue
                mapped = _RAW_ARGON_SKU_LABELS.get(clean.lower(), clean)
                if mapped.lower() not in seen_lower:
                    group_models[family].append(mapped)
                    seen_lower.add(mapped.lower())

    sig_payload = json.dumps(sorted(sig_pairs), ensure_ascii=False, separators=(",", ":"))
    group_desc_sig = hashlib.sha256(sig_payload.encode("utf-8")).hexdigest()[:16]
    return {
        "groupDescriptions": group_descriptions,
        "groupModels": group_models,
        "groupDescSig": group_desc_sig,
        "hasDedicatedArgonGroup": has_dedicated_argon,
    }


def classify_argon_mode(
    groups: list | None,
    group_models: dict | None = None,
    model_catalog: list[dict] | None = None,
    available_models: list[str] | None = None,
    cached_entry: dict | None = None,
) -> str:
    """Classify profile Argon quota mode as `'separate'`, `'shared_gemini'`, or `'none'`."""
    usage_parsed = parse_usage_group_models(groups if isinstance(groups, list) else [])
    if usage_parsed["hasDedicatedArgonGroup"]:
        return "separate"

    gm = group_models if isinstance(group_models, dict) else usage_parsed["groupModels"]
    gem_desc_low = (usage_parsed["groupDescriptions"].get("gemini") or "").lower()
    gem_models_low = " ".join(str(x).lower() for x in (gm.get("gemini") or []))
    if "argon" in gem_desc_low or "argon" in gem_models_low:
        return "shared_gemini"

    for entry in model_catalog or []:
        if isinstance(entry, dict):
            if "argon" in (entry.get("tags") or []) or entry.get("quotaFamily") == "argon":
                return "shared_gemini"

    for mid in available_models or []:
        m_low = str(mid).lower()
        if "argon" in m_low or ("orchestrator" in m_low and "g1-pro" in m_low):
            return "shared_gemini"

    no_live_descriptions = not any(usage_parsed["groupDescriptions"].values())
    if (
        no_live_descriptions
        and not model_catalog
        and not available_models
        and isinstance(cached_entry, dict)
    ):
        cached_caps = cached_entry.get("capabilities")
        allowed_cached = (
            ("shared_gemini", "none")
            if groups
            else ("separate", "shared_gemini", "none")
        )
        if isinstance(cached_caps, dict) and cached_caps.get("argonMode") in allowed_cached:
            return str(cached_caps["argonMode"])

    return "none"


def _reconcile_group_models(
    usage_parsed: dict,
    model_catalog: list[dict],
    cached_entry: dict | None = None,
) -> dict[str, list[str]]:
    """Reconcile `/usage` group descriptions with `agy models` catalog entries."""
    base = usage_parsed.get("groupModels") or {}
    merged: dict[str, list[str]] = {
        "gemini": list(base.get("gemini") or []),
        "claude": list(base.get("claude") or []),
        "argon": list(base.get("argon") or []),
    }

    if (
        not any(merged.values())
        and not model_catalog
        and isinstance(cached_entry, dict)
        and isinstance(cached_entry.get("groupModels"), dict)
    ):
        cgm = cached_entry["groupModels"]
        for fam in ("gemini", "claude", "argon"):
            merged[fam] = list(cgm.get(fam) or [])
        return merged

    had_gemini_desc = bool(merged["gemini"])
    had_claude_desc = bool(merged["claude"])
    has_dedicated_argon = bool(usage_parsed.get("hasDedicatedArgonGroup"))

    if not has_dedicated_argon:
        seen_argon = {x.lower() for x in merged["argon"]}
        for item in merged["gemini"]:
            if "argon" in item.lower() and item.lower() not in seen_argon:
                merged["argon"].append(item)
                seen_argon.add(item.lower())
    elif not merged["argon"]:
        merged["argon"].append("Gemini 4 Argon")

    for entry in model_catalog or []:
        if not isinstance(entry, dict):
            continue
        fam = entry.get("quotaFamily")
        lbl = str(entry.get("label") or "").strip()
        tags = entry.get("tags") or []
        if not lbl or fam not in ("gemini", "claude", "argon"):
            continue
        if fam == "argon":
            if lbl.lower() not in {x.lower() for x in merged["argon"]}:
                merged["argon"].append(lbl)
        elif fam == "gemini":
            if not had_gemini_desc or "orchestrator" in tags:
                if lbl == "Orchestrator" and any(
                    "orchestrator" in x.lower() for x in merged["gemini"] + merged["argon"]
                ):
                    continue
                if lbl.lower() not in {x.lower() for x in merged["gemini"]}:
                    merged["gemini"].append(lbl)
        elif fam == "claude" and not had_claude_desc:
            if lbl.lower() not in {x.lower() for x in merged["claude"]}:
                merged["claude"].append(lbl)

    return merged


def _derive_profile_capabilities(
    tier: str,
    plan_name: str,
    has_dedicated_argon: bool,
    argon_mode: str,
    group_models: dict,
    model_catalog: list[dict],
    available_models: list[str],
) -> dict:
    """Compute `{tier, hasCarbon, hasArgon, argonMode, hasOrchestrator, badges}`."""
    has_argon = argon_mode != "none"
    labels_low = " ".join(
        str(x).lower()
        for fam in ("gemini", "claude", "argon")
        for x in (group_models.get(fam) or [])
    )
    has_carbon = (
        ("carbon" in labels_low)
        or any("carbon" in (m.get("tags") or []) for m in (model_catalog or []))
        or any("carbon" in str(mid).lower() for mid in (available_models or []))
    )
    has_orchestrator = (
        ("orchestrator" in labels_low)
        or any("orchestrator" in (m.get("tags") or []) for m in (model_catalog or []))
        or any("orchestrator" in str(mid).lower() for mid in (available_models or []))
    )

    plan_up = str(plan_name or "").upper()
    if tier == "FREE":
        cap_tier = "FREE"
    elif "ULTRA" in plan_up:
        cap_tier = "ULTRA"
    else:
        cap_tier = "PRO"

    badges = [cap_tier]
    if has_carbon:
        badges.append("Carbon")
    if has_argon:
        badges.append("Argon")
    if has_orchestrator:
        badges.append("Orchestrator")

    return {
        "tier": cap_tier,
        "hasCarbon": has_carbon,
        "hasArgon": has_argon,
        "argonMode": argon_mode,
        "hasOrchestrator": has_orchestrator,
        "badges": badges,
    }


def _is_models_cache_warm(
    cached_entry: dict | None,
    live_sig: str,
    now_ts: float | None = None,
) -> bool:
    """Return True when cached model catalog has matching signature and age <= 24h."""
    if not isinstance(cached_entry, dict) or not live_sig:
        return False
    if cached_entry.get("groupDescSig") != live_sig:
        return False
    if "modelCatalog" not in cached_entry and "availableModels" not in cached_entry:
        return False
    fetched_raw = str(cached_entry.get("modelsFetchedAt") or "").strip()
    if not fetched_raw:
        return False
    try:
        dt = datetime.datetime.fromisoformat(fetched_raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        now_val = now_ts if now_ts is not None else time.time()
        age = now_val - dt.timestamp()
        return -300.0 <= age <= HYBRID_MODELS_TTL_SECONDS
    except Exception:
        return False


def _is_separate_argon_cached(cached_entry: dict | None) -> bool:
    """Return True only when cached profile uses a standalone (`separate`) Argon bucket."""
    if not isinstance(cached_entry, dict):
        return False
    caps = cached_entry.get("capabilities")
    arg_w = cached_entry.get("argonWeekly") or {}
    if isinstance(caps, dict) and caps.get("argonMode") in (
        "separate",
        "shared_gemini",
        "none",
    ):
        return caps.get("argonMode") == "separate" and not bool(
            arg_w.get("unavailable", False)
        )
    if arg_w.get("sharedPool") is True or arg_w.get("mode") == "shared_gemini":
        return False
    return bool(cached_entry.get("hasArgon", False)) and not bool(
        arg_w.get("unavailable", False)
    )


def select_model_from_candidates(available_models: list[str], candidates, default: str) -> str:
    """Select first available preferred model ID, or safe default."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "select_model_from_candidates"):
        return mod.select_model_from_candidates(available_models, candidates, default)
    avail = set(available_models or [])
    for c in candidates:
        if c in avail:
            return c
    return candidates[0] if candidates else default


def evaluate_claude_5h_session(
    api_data: dict | None,
    now_utc: datetime.datetime | None = None,
) -> tuple[bool, int, int, str]:
    """Delegate Claude 5H active evaluation to refresh_session module with built-in fallback."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "evaluate_claude_5h_session"):
        return mod.evaluate_claude_5h_session(api_data, now_utc=now_utc)
    data = api_data or {}
    five_h = data.get("five_hour") or {}
    utilization_5h = float(five_h.get("utilization") or 0)
    resets_at_iso = str(five_h.get("resets_at") or "").strip()
    limits = data.get("limits") or []
    session_limit_active = any(
        isinstance(item, dict)
        and item.get("kind") == "session"
        and bool(item.get("is_active"))
        for item in limits
    )
    now_ref = now_utc or datetime.datetime.now(datetime.timezone.utc)
    rem_sec_5h = 0
    resets_at_ts = 0
    local_reset = ""
    if resets_at_iso:
        try:
            dt_5h = datetime.datetime.fromisoformat(resets_at_iso.replace("Z", "+00:00"))
            resets_at_ts = int(dt_5h.timestamp())
            local_reset = dt_5h.astimezone().strftime("%H:%M:%S")
            rem_sec_5h = max(0, int((dt_5h - now_ref).total_seconds()))
        except (TypeError, ValueError):
            pass
    is_active = bool(
        (rem_sec_5h > 0 and (utilization_5h > 0 or session_limit_active or rem_sec_5h <= 5 * 3600 + 60))
        or (session_limit_active and not resets_at_iso)
    )
    return is_active, rem_sec_5h, resets_at_ts, local_reset


def is_codex_5h_active(
    rate_limit: dict | None,
    grace_sec: int = 30,
) -> tuple[bool, int, int, float]:
    """Delegate Codex 5H active evaluation to refresh_session module with built-in fallback."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "is_codex_5h_active"):
        return mod.is_codex_5h_active(rate_limit, grace_sec=grace_sec)
    pw = (rate_limit or {}).get("primary_window") or {}
    p_used = float(pw.get("used_percent") or 0)
    p_rem_sec = int(pw.get("reset_after_seconds") or 0)
    p_win_sec = int(pw.get("limit_window_seconds") or 5 * 3600) or (5 * 3600)
    is_active = bool(
        p_rem_sec > 0 and (p_used > 0 or p_rem_sec < max(1, p_win_sec - grace_sec))
    )
    return is_active, p_rem_sec, p_win_sec, p_used


def has_valid_fallback_oauth_token(profile_home: str | Path) -> bool:
    """Delegate fallback OAuth file check to refresh_session module with built-in fallback."""
    mod = _load_refresh_session_module()
    fn = getattr(mod, "has_valid_fallback_oauth_token", None) if mod else None
    if callable(fn):
        res = fn(profile_home)
        if isinstance(res, bool):
            return res
    home = Path(profile_home)
    for rel_path in (
        Path(".gemini") / "antigravity-cli" / "antigravity-oauth-token",
        Path(".gemini") / "jetski-standalone-oauth-token",
    ):
        token_path = home / rel_path
        if not os.path.isfile(token_path):
            continue
        try:
            raw = token_path.read_text(encoding="utf-8").strip()
            payload = json.loads(raw) if raw else None
        except Exception:
            continue
        token = payload.get("token") if isinstance(payload, dict) else None
        if isinstance(token, dict) and any(
            isinstance(token.get(k), str) and bool(token[k].strip())
            for k in ("refresh_token", "access_token")
        ):
            return True
        if isinstance(token, str) and token.strip():
            return True
    return False


# ANSI Colors & Styling
GREEN       = "\033[38;2;114;188;130m"      # Soft Green (#72bc82)
AMBER       = "\033[38;2;245;158;11m"       # Amber / Orange (#f59e0b)
RED         = "\033[38;2;239;68;68m"        # Red (#ef4444)
GRAY        = "\033[38;2;148;163;184m"      # Slate / Gray (#94a3b8)
DIM         = "\033[38;2;100;116;139m"      # Slate-500 Dim (#64748b)
BORDER      = "\033[38;2;51;65;85m"         # Border color (#334155)
TRACK_GRAY  = "\033[38;2;30;41;59m"         # Deep Slate (#1e293b)
WHITE       = "\033[1;37m"                  # Bold White
CYAN        = "\033[38;2;56;189;248m"       # Cyan (#38bdf8)
TIMER       = "\033[38;2;251;191;36m"       # Gold / Amber Timer (#fbbf24)
RESET       = "\033[0m"
BOLD        = "\033[1m"

# Model & Status Badges
def format_priority_tag(priority: object = 50) -> str:
    """Format ANSI badge for dynamic account priority."""
    try:
        prio_val = int(priority)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        prio_val = 50
    return f"\033[48;2;24;27;38m\033[38;2;160;174;192m Priority: {prio_val} \033[0m"


TAG_ULTRA        = "\033[48;2;124;58;237m\033[1;37m ✦ ULTRA \033[0m"
TAG_PRO          = "\033[48;2;59;102;245m\033[1;37m ◆ PRO \033[0m"
TAG_PRIORITY     = format_priority_tag(50)
TAG_CARBON       = "\033[48;2;14;116;144m\033[38;2;165;243;252m ◈ Carbon \033[0m"
TAG_ARGON        = "\033[48;2;38;25;56m\033[38;2;192;132;252m ✣ Argon \033[0m"
TAG_ORCHESTRATOR = "\033[48;2;20;83;45m\033[38;2;134;239;172m ⚙ Orchestrator \033[0m"
TAG_HIGH     = "\033[48;2;76;29;149m\033[38;2;216;180;254m High \033[0m"
TAG_MED      = "\033[48;2;30;58;138m\033[38;2;191;219;254m Med \033[0m"
TAG_LOW      = "\033[48;2;15;23;42m\033[38;2;148;163;184m Low \033[0m"
TAG_INACTIVE = "\033[48;2;30;41;59m\033[38;2;148;163;184m INACTIVE \033[0m"

def _derive_real_home() -> str:
    """Host user's real HOME, derived (never hard-coded); strips /antigravity_homes/<profile> when inside a profile."""
    home = os.environ.get("REAL_HOME") or os.path.expanduser("~")
    return home.split("/antigravity_homes")[0] if "/antigravity_homes" in home else home


REAL_HOME = _derive_real_home()
KC_PASS = "H@No!a@12345"
AGY_BIN = "/opt/homebrew/bin/agy"
SESSION_STORE_DB = Path(REAL_HOME) / ".devtool" / "state" / ".session_store.db"
SALT = "d3nexus-session-salt-2026"


def _decode_jwt_claims_unverified(token: object) -> dict:
    """Decode non-secret JWT payload claims locally without signature verification or network calls."""
    if not isinstance(token, str) or token.count(".") != 2:
        return {}
    try:
        seg = token.split(".")[1]
        seg += "=" * (-len(seg) % 4)
        raw = base64.urlsafe_b64decode(seg.encode("ascii")).decode("utf-8")
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def read_antigravity_vscdb_email(profile: str) -> str | None:
    """Read authenticated Google email from profile state.vscdb (modern data/User or legacy Library path) in read-only SQLite URI mode."""
    p_home = Path(REAL_HOME) / "antigravity_homes" / profile
    candidates = (
        p_home / "data" / "User" / "globalStorage" / "state.vscdb",
        p_home
        / "Library"
        / "Application Support"
        / "Antigravity"
        / "User"
        / "globalStorage"
        / "state.vscdb",
    )
    for db_path in candidates:
        if not db_path.is_file():
            continue
        con = None
        try:
            uri = f"{db_path.resolve().as_uri()}?mode=ro"
            con = sqlite3.connect(uri, uri=True, timeout=1.0)
            cur = con.cursor()
            cur.execute(
                "SELECT value FROM ItemTable WHERE key = 'antigravityAuthStatus' LIMIT 1;"
            )
            row = cur.fetchone()
            if row and row[0]:
                parsed = json.loads(row[0])
                if isinstance(parsed, dict):
                    raw_email = parsed.get("email")
                    if isinstance(raw_email, str) and raw_email.strip():
                        return raw_email.strip()

            cur.execute(
                "SELECT value FROM ItemTable WHERE key = 'google.google-antigravity' LIMIT 1;"
            )
            row2 = cur.fetchone()
            if row2 and row2[0]:
                parsed2 = json.loads(row2[0])
                if isinstance(parsed2, dict):
                    storage = parsed2.get("antigravity-storage")
                    if isinstance(storage, dict):
                        login_user = storage.get("agy.onboarding.lastLoginUsername")
                        if isinstance(login_user, str) and login_user.strip():
                            return login_user.strip()
        except Exception:
            pass
        finally:
            if con is not None:
                try:
                    con.close()
                except Exception:
                    pass
    return None


def _parse_antigravity_oauth_json(raw_text: str) -> dict:
    """Decode raw or go-keyring-base64 OAuth JSON into `{access_token, email, auth_method, expiry}`."""
    txt = str(raw_text or "").strip()
    if not txt:
        return {}
    if txt.startswith("go-keyring-base64:"):
        b64_part = txt[len("go-keyring-base64:") :].strip()
        b64_part += "=" * (-len(b64_part) % 4)
        try:
            txt = base64.b64decode(b64_part.encode("ascii")).decode("utf-8")
        except Exception:
            return {}
    try:
        payload = json.loads(txt)
    except Exception:
        return {}
    if not isinstance(payload, dict):
        return {}

    tok = payload.get("token")
    access_token = ""
    expiry = ""
    id_tok_email = ""
    if isinstance(tok, dict):
        access_token = str(tok.get("access_token") or "").strip()
        expiry = str(tok.get("expiry") or "").strip()
        claims = _decode_jwt_claims_unverified(tok.get("id_token"))
        if isinstance(claims.get("email"), str):
            id_tok_email = claims["email"].strip()
    elif isinstance(tok, str):
        access_token = tok.strip()

    email = str(payload.get("id_token_email") or id_tok_email or "").strip()
    auth_method = str(payload.get("auth_method") or "").strip()
    out: dict[str, str] = {}
    if access_token:
        out["access_token"] = access_token
    if email:
        out["email"] = email
    if auth_method:
        out["auth_method"] = auth_method
    if expiry:
        out["expiry"] = expiry
    return out


def read_antigravity_oauth_record(profile: str) -> dict:
    """Read profile OAuth metadata (`email`, `auth_method`, in-memory `access_token`) from Keychain or fallback token file."""
    wait_for_launch_lock()
    profile_home = Path(REAL_HOME) / "antigravity_homes" / profile
    kc = profile_home / "Library" / "Keychains" / f"{profile}.keychain-db"
    if kc.is_file():
        try:
            subprocess.run(
                ["security", "unlock-keychain", "-p", KC_PASS, str(kc)],
                capture_output=True,
                timeout=2.0,
            )
            res = subprocess.run(
                [
                    "security",
                    "find-generic-password",
                    "-s",
                    "gemini",
                    "-a",
                    "antigravity",
                    "-w",
                    str(kc),
                ],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if res.returncode == 0 and res.stdout:
                parsed = _parse_antigravity_oauth_json(res.stdout)
                if parsed:
                    return parsed
        except Exception:
            pass

    for rel_path in (
        Path(".gemini") / "antigravity-cli" / "antigravity-oauth-token",
        Path(".gemini") / "jetski-standalone-oauth-token",
    ):
        token_path = profile_home / rel_path
        if not token_path.is_file():
            continue
        try:
            parsed = _parse_antigravity_oauth_json(
                token_path.read_text(encoding="utf-8")
            )
            if parsed:
                return parsed
        except Exception:
            continue
    return {}


def fetch_antigravity_google_license(
    profile: str,
    access_token: str | None = None,
) -> dict:
    """Query Google AICode `GET /v1alpha:fetchLicenses` for live userTier (`g1-ultra-tier`, `g1-pro-tier`, `free-tier`) and tierDisplayName."""
    tok = str(access_token or "").strip()
    if not tok:
        oauth_rec = read_antigravity_oauth_record(profile)
        tok = str(oauth_rec.get("access_token") or "").strip()
    if not tok:
        return {}

    req = urllib.request.Request(
        "https://aicode.googleapis.com/v1alpha:fetchLicenses",
        method="GET",
        headers={
            "Authorization": f"Bearer {tok}",
            "Accept": "application/json",
            "User-Agent": "antigravity-cli/2.7.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            if getattr(resp, "status", 200) != 200:
                return {}
            body = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return {}

    if not isinstance(body, dict):
        return {}
    licenses = body.get("licenses")
    if not isinstance(licenses, list) or not licenses or not isinstance(licenses[0], dict):
        return {}

    lic = licenses[0]
    user_tier = str(lic.get("userTier") or "").strip()
    display_name = str(lic.get("tierDisplayName") or "").strip()
    up_sub = lic.get("upgradeSubscription") if isinstance(lic.get("upgradeSubscription"), dict) else {}
    upgrade_text = str(up_sub.get("text") or "").strip()
    upgrade_url = str(up_sub.get("url") or "").strip()

    combined_low = f"{user_tier} {display_name}".lower()
    if "ultra" in combined_low:
        canonical_tier = "ULTRA"
    elif "free" in combined_low or "starter" in combined_low:
        canonical_tier = "FREE"
    elif "pro" in combined_low or "standard" in combined_low:
        canonical_tier = "PRO"
    else:
        canonical_tier = ""

    out: dict[str, str] = {}
    if user_tier:
        out["userTier"] = user_tier
    if display_name:
        out["tierDisplayName"] = display_name
    if canonical_tier:
        out["tier"] = canonical_tier
    if upgrade_text:
        out["upgradeText"] = upgrade_text
    if upgrade_url:
        out["upgradeUrl"] = upgrade_url
    return out


def normalize_antigravity_account(
    profile: str,
    capabilities: dict | None,
    argon_mode: str = "none",
    email: str | None = None,
    license_info: dict | None = None,
    oauth_info: dict | None = None,
    credits_info: dict | None = None,
) -> dict:
    """Normalize Antigravity tier, priority (80/60/50/20), and non-secret AccountMeta."""
    caps = capabilities if isinstance(capabilities, dict) else {}
    lic = license_info if isinstance(license_info, dict) else {}
    oauth = oauth_info if isinstance(oauth_info, dict) else {}
    cred = credits_info if isinstance(credits_info, dict) else {}

    lic_tier = str(lic.get("tier") or "").strip().upper()
    user_tier_raw = str(lic.get("userTier") or "").strip()
    disp_name_raw = str(lic.get("tierDisplayName") or "").strip()
    combined_lic_low = f"{user_tier_raw} {disp_name_raw}".lower()
    if not lic_tier and combined_lic_low.strip():
        if "ultra" in combined_lic_low:
            lic_tier = "ULTRA"
        elif "free" in combined_lic_low or "starter" in combined_lic_low:
            lic_tier = "FREE"
        elif "pro" in combined_lic_low or "standard" in combined_lic_low:
            lic_tier = "PRO"

    cap_tier = str(lic_tier or caps.get("tier") or "PRO").strip().upper()
    eff_argon = str(argon_mode or caps.get("argonMode") or "none").strip()

    if cap_tier == "ULTRA":
        tier, plan_label, plan_type, priority = "ULTRA", "ULTRA", "ultra", 80
    elif cap_tier == "FREE":
        tier, plan_label, plan_type, priority = "FREE", "FREE", "free", 20
    elif eff_argon == "separate":
        tier, plan_label, plan_type, priority = "PRO", "PRO", "pro_argon", 60
    else:
        tier, plan_label, plan_type, priority = "PRO", "PRO", "pro", 50

    oauth_email = str(oauth.get("email") or "").strip()
    vscdb_email = read_antigravity_vscdb_email(profile) or ""
    explicit_email = str(email).strip() if isinstance(email, str) and email.strip() else ""
    synthetic_fallback = f"{profile}@gmail.com"
    non_synthetic_explicit = (
        explicit_email if explicit_email and explicit_email != synthetic_fallback else ""
    )
    resolved_email = (
        oauth_email
        or vscdb_email
        or non_synthetic_explicit
        or explicit_email
        or synthetic_fallback
    )
    account_meta: dict[str, object] = {
        "provider": "antigravity",
        "vendorLabel": "GOOGLE",
        "planType": plan_type,
        "planLabel": plan_label,
        "authSource": "antigravity-oauth",
        "cliCommand": f"{profile}-cli",
        "configPath": f"~/antigravity_homes/{profile}",
        "secondaryPath": f"~/antigravity_homes/{profile}/Library/Keychains/{profile}.keychain-db",
    }
    if user_tier_raw:
        account_meta["userTier"] = user_tier_raw
    if disp_name_raw:
        account_meta["tierDisplayName"] = disp_name_raw
    auth_method = str(oauth.get("auth_method") or oauth.get("authMethod") or "").strip()
    if auth_method:
        account_meta["authMethod"] = auth_method
    upgrade_text = str(lic.get("upgradeText") or "").strip()
    if upgrade_text:
        account_meta["upgradeText"] = upgrade_text
    upgrade_url = str(lic.get("upgradeUrl") or cred.get("upgradeUrl") or "").strip()
    if upgrade_url:
        account_meta["upgradeUrl"] = upgrade_url
    if "remainingCredits" in cred and cred["remainingCredits"] is not None:
        try:
            rem_cr = int(cred["remainingCredits"])
            account_meta["remainingCredits"] = rem_cr
            account_meta["creditsSummary"] = f"{rem_cr} AI credits remaining"
        except (TypeError, ValueError):
            pass

    return {
        "email": resolved_email,
        "tier": tier,
        "planLabel": plan_label,
        "vendorLabel": "GOOGLE",
        "priority": priority,
        "accountMeta": account_meta,
    }

NATURAL_PROMPTS = [
    "Explain HTTP status 200 in 5 words.",
    "What is POSIX standard?",
    "Python list comprehension syntax.",
    "Bash command for disk free space.",
    "Define idempotent in REST API in 5 words.",
    "What is git commit hash SHA?",
    "Explain difference between TCP and UDP in 1 line.",
    "Write a regex for matching digits in 5 chars.",
]


GLOBAL_REFRESH_INTERVAL_SECONDS = 1800  # 30 minutes


def wait_for_launch_lock(timeout: float = 3.0) -> None:
    """Wait if any profile is currently in its 1.5s atomic launch window."""
    lock_dir = "/tmp/ag_launch.lock"
    if os.path.exists(lock_dir):
        start = time.time()
        while os.path.exists(lock_dir) and (time.time() - start < timeout):
            time.sleep(0.1)


def build_clean_host_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a clean host environment stripped of leaked IDE, Electron, and profile variables."""
    env = dict(os.environ if base_env is None else base_env)
    env["HOME"] = REAL_HOME
    for exact_key in (
        "AGY_PROFILE",
        "AGY_CLI_MODE",
        "AGY_ENABLE_HUB",
        "TERM_PROGRAM",
        "TERM_PROGRAM_VERSION",
        "TERM_SESSION_ID",
        "TMPDIR",
        "ZDOTDIR",
    ):
        env.pop(exact_key, None)
    for key in list(env.keys()):
        if key.startswith(("VSCODE_", "ANTIGRAVITY_", "ELECTRON_", "CHROME_")):
            env.pop(key, None)
    return env


def build_profile_cli_env(profile: str) -> dict[str, str]:
    """Return a sanitized host environment scoped to a single Antigravity profile."""
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    tmpdir_path = f"/tmp/ag_{profile}"
    os.makedirs(tmpdir_path, exist_ok=True)
    env = build_clean_host_env()
    env.update({
        "HOME": ag_home,
        "AGY_PROFILE": profile,
        "AGY_CLI_MODE": "1",
        "TMPDIR": tmpdir_path,
        "BROWSER": "true",
    })
    return env


def init_session_store_db():
    try:
        SESSION_STORE_DB.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(SESSION_STORE_DB))
        con.execute("""
        CREATE TABLE IF NOT EXISTS session_store (
            profile_hash TEXT PRIMARY KEY,
            reset_5h INTEGER NOT NULL,
            reset_weekly INTEGER NOT NULL,
            fraction_5h REAL NOT NULL,
            last_checked INTEGER NOT NULL,
            last_ping INTEGER NOT NULL,
            is_active INTEGER NOT NULL
        );
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to init session_store.db: {e}\n")


def get_global_meta(key: str, default: str = "") -> str:
    init_session_store_db()
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("SELECT value FROM system_metadata WHERE key = ?", (key,))
        row = cur.fetchone()
        con.close()
        return row[0] if row else default
    except Exception:
        return default


def set_global_meta(key: str, value: str):
    init_session_store_db()
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO system_metadata (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value;
        """, (key, value))
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to set global meta: {e}\n")


def get_last_refresh_all_time() -> int:
    val = get_global_meta("last_refresh_all_timestamp", "0")
    try:
        return int(val)
    except ValueError:
        return 0


def record_refresh_all_time(ts: int | None = None):
    now = int(ts or time.time())
    set_global_meta("last_refresh_all_timestamp", str(now))


def hash_profile(name: str) -> str:
    return hashlib.sha256(f"{SALT}:{name}".encode("utf-8")).hexdigest()[:24]


def save_session_record(profile: str, reset_5h: int, reset_weekly: int, fraction_5h: float, is_active: bool, last_ping: int | None = None):
    init_session_store_db()
    h = hash_profile(profile)
    now = int(time.time())
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("""
            INSERT INTO session_store (profile_hash, reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(profile_hash) DO UPDATE SET
                reset_5h=excluded.reset_5h,
                reset_weekly=excluded.reset_weekly,
                fraction_5h=excluded.fraction_5h,
                last_checked=excluded.last_checked,
                last_ping=COALESCE(excluded.last_ping, session_store.last_ping),
                is_active=excluded.is_active;
        """, (h, int(reset_5h), int(reset_weekly), float(fraction_5h), now, int(last_ping or now), 1 if is_active else 0))
        con.commit()
        con.close()
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to save session record: {e}\n")


def get_session_record(profile: str) -> dict | None:
    init_session_store_db()
    h = hash_profile(profile)
    try:
        con = sqlite3.connect(str(SESSION_STORE_DB), timeout=5.0)
        cur = con.cursor()
        cur.execute("SELECT reset_5h, reset_weekly, fraction_5h, last_checked, last_ping, is_active FROM session_store WHERE profile_hash = ?", (h,))
        row = cur.fetchone()
        con.close()
        if not row:
            return None
        return {
            "reset_5h": row[0],
            "reset_weekly": row[1],
            "fraction_5h": row[2],
            "last_checked": row[3],
            "last_ping": row[4],
            "is_active": bool(row[5]),
        }
    except Exception:
        return None


def get_color(pct: float) -> str:
    """Return ANSI color based on quota percentage."""
    if pct >= 50.0:
        return GREEN
    elif pct >= 10.0:
        return AMBER
    else:
        return RED


def get_color_pair(pct: float) -> tuple:
    """Return (active_fill_color, consumed_track_color) based on quota percentage."""
    if pct >= 50.0:
        return GREEN, "\033[38;2;22;101;52m"     # Deep Forest Green (#166534)
    elif pct >= 10.0:
        return AMBER, "\033[38;2;120;53;15m"     # Deep Amber (#78350f)
    else:
        return RED, "\033[38;2;127;29;29m"       # Deep Crimson (#7f1d1d)


def str_vis_width(s: str) -> int:
    """Compute visual terminal width ignoring ANSI escape codes."""
    w = 0
    in_esc = False
    for ch in s:
        if ch == "\033":
            in_esc = True
            continue
        if in_esc:
            if ch == "m":
                in_esc = False
            continue
        if ch in ("⏱", "⏳"):
            w += 2
        else:
            w += 1
    return w


def format_countdown(reset_time_str: str) -> str:
    """Calculate remaining time to full reset from now."""
    if not reset_time_str or reset_time_str.startswith("1970"):
        return "⏱ --"
    try:
        dt = datetime.datetime.fromisoformat(reset_time_str.replace("Z", "+00:00"))
        if dt.year <= 1970:
            return "⏱ --"
        now = datetime.datetime.now(datetime.timezone.utc)
        diff = dt - now
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "⏱ --"
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        if days > 0:
            return f"⏱ {days}d {hours}h"
        elif hours > 0:
            return f"⏱ {hours}h {minutes}m"
        elif minutes > 0:
            return f"⏱ {minutes}m"
        else:
            return "⏱ --"
    except Exception:
        return "⏱ --"


def render_card(icon: str, icon_color: str, title: str, timer_str: str, fraction: float, width: int = 45, tags: str = None, available: bool = True) -> list:
    """Render a card-style UI box with progress bar matching the reference image."""
    inner_w = width - 2

    # Top border
    top = f"{BORDER}╭" + "─" * inner_w + f"╮{RESET}"
    bot = f"{BORDER}╰" + "─" * inner_w + f"╯{RESET}"

    if not available:
        # Inactive / unavailable model: styled in slate gray with NO right text as requested
        left_styled = f" {DIM}{icon}{RESET} {DIM}{title}{RESET} {TAG_INACTIVE}"
        left_raw = f" {icon} {title}  INACTIVE "

        sp = max(1, inner_w - str_vis_width(left_raw) - 1)
        content = f"{BORDER}│{RESET}{left_styled}{' ' * sp}{BORDER}│{RESET}"
        bar_w = inner_w - 4
        bar_line = f"{BORDER}│{RESET}  [{BORDER}{'░' * bar_w}{RESET}]  {BORDER}│{RESET}"
        return [top, content, bar_line, bot]

    fraction = max(0.0, min(1.0, fraction))
    pct = fraction * 100.0
    color = get_color(pct)

    # Left text (icon + title + tags)
    left_styled = f" {icon_color}{icon}{RESET} {WHITE}{title}{RESET}"
    left_raw = f" {icon} {title}"
    if tags:
        left_styled += f" {tags}"
        left_raw += "  High   Med   Low "

    pct_text = f"{color}{pct:5.1f}%{RESET}"
    pct_raw = f"{pct:5.1f}%"

    timer_styled = f"{TIMER}{timer_str}{RESET}"
    timer_raw = timer_str

    vis_used = str_vis_width(left_raw) + str_vis_width(timer_raw) + str_vis_width(pct_raw)
    sp_total = max(2, inner_w - vis_used - 1)
    sp1 = max(1, sp_total // 2)
    sp2 = max(1, sp_total - sp1)

    content = f"{BORDER}│{RESET}{left_styled}{' ' * sp1}{timer_styled}{' ' * sp2}{pct_text} {BORDER}│{RESET}"

    # Progress bar line
    bar_w = inner_w - 4
    filled = int(round(fraction * bar_w))
    empty = bar_w - filled
    fill_color, track_color = get_color_pair(pct)
    bar_line = f"{BORDER}│{RESET}  [{fill_color}{'█' * filled}{RESET}{track_color}{'░' * empty}{RESET}]  {BORDER}│{RESET}"

    return [top, content, bar_line, bot]


RESERVED_NON_PROFILES = {
    "Library", "System", "Shared", "AllProjects", "Projects", "fvm",
    "claude", "codex", "kiro", "anthropic", "openai", ".gemini", ".antigravity",
    ".antigravity-ide"
}


def is_valid_antigravity_profile(profile_name: str, homes_dir: str | None = None) -> bool:
    """Validate whether a name corresponds to an actual Antigravity profile account."""
    if not profile_name or profile_name.startswith(".") or profile_name.startswith("-"):
        return False
    if profile_name in RESERVED_NON_PROFILES:
        return False
    if not re.match(r"^[a-zA-Z0-9_-]+$", profile_name):
        return False

    h_dir = homes_dir or f"{REAL_HOME}/antigravity_homes"
    ag_home = os.path.join(h_dir, profile_name)

    if not os.path.exists(ag_home) or os.path.islink(ag_home) or not os.path.isdir(ag_home):
        return False

    if profile_name == "default":
        zshrc_path = os.path.expanduser("~/.zshrc")
        if os.path.exists(zshrc_path):
            try:
                with open(zshrc_path, "r", encoding="utf-8", errors="ignore") as f:
                    if "ag_run default" not in f.read():
                        return False
            except Exception:
                return False
        else:
            return False

    has_gemini = os.path.exists(os.path.join(ag_home, ".gemini"))
    has_ag = os.path.exists(os.path.join(ag_home, ".antigravity"))
    has_data = os.path.exists(os.path.join(ag_home, "data"))
    has_kc = os.path.exists(os.path.join(ag_home, "Library/Keychains"))
    return bool(has_gemini or has_ag or has_data or has_kc)


def get_all_profiles() -> list:
    """Discover all actual Antigravity profile accounts directly from antigravity_homes directory."""
    profiles = []
    homes_dir = f"{REAL_HOME}/antigravity_homes"
    if os.path.isdir(homes_dir):
        for d in sorted(os.listdir(homes_dir)):
            if is_valid_antigravity_profile(d, homes_dir=homes_dir):
                profiles.append(d)

    # Also check ~/.zshrc for aliases as fallback or aliases with distinct names
    zshrc_path = os.path.expanduser("~/.zshrc")
    if os.path.exists(zshrc_path):
        try:
            with open(zshrc_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    m = re.search(r"antigravity_homes/([a-zA-Z0-9_-]+)", line)
                    if m:
                        p = m.group(1)
                        if is_valid_antigravity_profile(p, homes_dir=homes_dir) and p not in profiles:
                            profiles.append(p)
                    m2 = re.match(r"^alias\s+([a-zA-Z0-9_-]+)='ag_run\s+([a-zA-Z0-9_-]+)'", line.strip())
                    if m2:
                        p2 = m2.group(2)
                        if is_valid_antigravity_profile(p2, homes_dir=homes_dir) and p2 not in profiles:
                            profiles.append(p2)
        except Exception:
            pass

    return sorted(list(set(profiles)))


def get_profiles_from_zshrc() -> list:
    """Backward compatibility alias to get_all_profiles()."""
    return get_all_profiles()


LAST_BLOCKED_PROBE = {}


def unblock_profile(profile: str):
    """Clear disabled marker, archive historical appeal logs, and update in-memory cache."""
    marker_file = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity", "tos_disabled.json")
    if os.path.isfile(marker_file):
        try:
            os.remove(marker_file)
        except Exception:
            pass

    log_dir = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity/log")
    if os.path.isdir(log_dir):
        import glob
        for lf in glob.glob(os.path.join(log_dir, "cli-*.log")):
            try:
                with open(lf, "rb") as f:
                    content = f.read().decode("utf-8", errors="ignore").lower()
                if "submit an appeal" in content or "violation of terms of service" in content:
                    os.rename(lf, lf + ".resolved")
            except Exception:
                pass

    if CACHED_PROFILES_DATA and profile in CACHED_PROFILES_DATA:
        CACHED_PROFILES_DATA[profile]["isAppeal"] = False
        CACHED_PROFILES_DATA[profile]["status"] = "ACTIVE"


def probe_blocked_profile(profile: str) -> dict:
    """Safely test whether an individual blocked profile has been unblocked by Google.
    Includes anti-spam cooldown, randomized humanized jitter, token verification, and real model inference probe.
    """
    now = time.time()
    last_time = LAST_BLOCKED_PROBE.get(profile, 0)
    cooldown = 30  # 30 seconds cooldown per profile to prevent Google WAF rate-limit
    if (now - last_time) < cooldown:
        remaining = int(cooldown - (now - last_time))
        return {
            "profile": profile,
            "success": False,
            "status": "COOLDOWN",
            "cooldown": True,
            "error": f"Vui lòng đợi thêm {remaining}s trước khi kiểm tra lại tài khoản này để bảo vệ khỏi rate limit.",
            "remaining_cooldown": remaining
        }

    # 1. Verify auth token exists in keychain (PREVENTS BROWSER POPUP)
    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_auth_needed": True,
            "error": "Profile chưa có token xác thực trong Keychain. Cần đăng nhập CLI trước."
        }

    LAST_BLOCKED_PROBE[profile] = now

    # 2. Apply randomized humanized jitter (1.8s - 3.2s) to prevent bot detection
    jitter_sec = round(random.uniform(1.8, 3.2), 2)
    time.sleep(jitter_sec)

    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    env = build_profile_cli_env(profile)

    # 3. CRITICAL: Test real model inference with a lightweight prompt from NATURAL_PROMPTS
    # Google's /usage endpoint does NOT check the ToS model suspension flag!
    # Only sending a real generation prompt reveals whether the Gemini model is still disabled.
    prompt = random.choice(NATURAL_PROMPTS)
    cmd = [AGY_BIN, "-p", prompt]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
        dur = round(time.time() - t0, 2)
        all_out = (proc.stdout or "") + " " + (proc.stderr or "")

        appeal_err_id = check_profile_appeal_status(profile, all_out)
        low_out = all_out.lower()
        is_blocked = (
            bool(appeal_err_id) or
            "submit an appeal" in low_out or
            "violation of terms of service" in low_out or
            "service has been disabled" in low_out or
            proc.returncode != 0
        )

        if is_blocked:
            err_id = appeal_err_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
            if not appeal_err_id:
                record_profile_disabled(profile, err_id)
            disabled_data = format_profile_for_dashboard(profile, {
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": err_id
            })
            update_cached_profile(profile, disabled_data)
            return {
                "profile": profile,
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": err_id,
                "duration": dur,
                "jitter": jitter_sec,
                "data": disabled_data,
                "error": f"Tài khoản {profile} vẫn đang bị Google tạm ngưng (ToS Violation). Vui lòng gửi đơn kháng nghị (Submit an appeal). Mã lỗi: {err_id}"
            }

        # 4. Prompt succeeded with returncode 0! Verify standalone Argon only when argonMode == "separate"
        current = _peek_cached_profile(profile)
        has_argon = _is_separate_argon_cached(current)
        if has_argon:
            time.sleep(round(random.uniform(1.8, 3.2), 2))
            other_prompts = [p for p in NATURAL_PROMPTS if p != prompt] or NATURAL_PROMPTS
            prompt_argon = random.choice(other_prompts)
            cmd_arg = [AGY_BIN, "--model", "gemini-4-argon-low", "-p", prompt_argon]
            try:
                proc_arg = subprocess.run(cmd_arg, env=env, capture_output=True, text=True, timeout=25)
                all_arg_out = (proc_arg.stdout or "") + " " + (proc_arg.stderr or "")
                appeal_arg_id = check_profile_appeal_status(profile, all_arg_out)
                low_arg_out = all_arg_out.lower()
                is_arg_blocked = (
                    bool(appeal_arg_id) or
                    "submit an appeal" in low_arg_out or
                    "violation of terms of service" in low_arg_out or
                    "service has been disabled" in low_arg_out
                )
                if is_arg_blocked:
                    err_id = appeal_arg_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                    if not appeal_arg_id:
                        record_profile_disabled(profile, err_id)
                    disabled_data = format_profile_for_dashboard(profile, {
                        "success": False,
                        "status": "DISABLED",
                        "is_appeal": True,
                        "error_id": err_id
                    })
                    update_cached_profile(profile, disabled_data)
                    return {
                        "profile": profile,
                        "success": False,
                        "status": "DISABLED",
                        "is_appeal": True,
                        "error_id": err_id,
                        "duration": dur,
                        "jitter": jitter_sec,
                        "data": disabled_data,
                        "error": f"Tài khoản {profile} bị chặn ToS khi gọi mô hình Argon (Submit an appeal). Mã lỗi: {err_id}"
                    }
                if "is not recognized" in low_arg_out or "invalid model selection" in low_arg_out:
                    current["hasArgon"] = False
                    if "argonWeekly" in current:
                        current["argonWeekly"]["unavailable"] = True
                        current["argonWeekly"]["countdown"] = "Unavailable N/A"
                    update_cached_profile(profile, current)
            except Exception:
                pass

        # 5. All model checks passed! Google has truly unblocked the account!
        unblock_profile(profile)
        res = fetch_quota_for_profile(profile, force_probe=True)
        formatted = format_profile_for_dashboard(profile, res)
        update_cached_profile(profile, formatted)
        LAST_BLOCKED_PROBE.pop(profile, None)
        return {
            "profile": profile,
            "success": True,
            "status": "ACTIVE",
            "unblocked": True,
            "duration": dur,
            "jitter": jitter_sec,
            "data": formatted,
            "message": f"🎉 Tuyệt vời! Tài khoản {profile} đã được Google mở khóa thành công!"
        }
    except subprocess.TimeoutExpired:
        return {"profile": profile, "success": False, "status": "ERROR", "duration": 25.0, "error": "Kiểm tra bị quá hạn (25s)"}
    except Exception as e:
        return {"profile": profile, "success": False, "status": "ERROR", "error": str(e)}


def record_profile_disabled(profile: str, error_id: str):
    """Persist disabled/appeal status to disk in profile's .gemini/antigravity/tos_disabled.json."""
    try:
        marker_dir = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity")
        os.makedirs(marker_dir, exist_ok=True)
        marker_file = os.path.join(marker_dir, "tos_disabled.json")
        with open(marker_file, "w") as f:
            json.dump({
                "profile": profile,
                "error_id": error_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2",
                "timestamp": time.time(),
                "disabled_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": "Violation of Terms of Service (Submit an appeal)"
            }, f, indent=2)
    except Exception:
        pass


def check_profile_appeal_status(profile: str, out_text: str = "") -> str:
    """Check if profile has been disabled for Terms of Service violation (submit an appeal).
    Returns Error ID string if disabled, or empty string '' if not disabled.
    """
    if out_text:
        low = out_text.lower()
        if "submit an appeal" in low or "violation of terms of service" in low or "service has been disabled" in low:
            m = re.search(r'([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}(?:-\d+)?)', out_text)
            err_id = m.group(1) if m else "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
            record_profile_disabled(profile, err_id)
            return err_id
        return ""

    # Check marker file in profile directory (Single Source of Truth)
    marker_file = os.path.join(REAL_HOME, "antigravity_homes", profile, ".gemini/antigravity", "tos_disabled.json")
    if os.path.isfile(marker_file):
        try:
            with open(marker_file, "r") as f:
                data = json.load(f)
                return data.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
        except Exception:
            pass

    return ""


def check_profile_auth_token(profile: str) -> bool:
    """Check in ~8ms whether profile has an active gemini token in Keychain or fallback file.
    CRITICAL: If False, running agy will attempt to open the web browser for OAuth!
    We MUST NOT execute agy when this returns False.
    """
    wait_for_launch_lock()
    profile_home = Path(REAL_HOME) / "antigravity_homes" / profile
    kc = str(profile_home / "Library" / "Keychains" / f"{profile}.keychain-db")
    if os.path.isfile(kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, kc], capture_output=True)
        res = subprocess.run(["security", "find-generic-password", "-s", "gemini", "-a", "antigravity", kc], capture_output=True)
        if res.returncode == 0:
            return True
    return has_valid_fallback_oauth_token(profile_home)


def _query_agy_models_stdout(env: dict[str, str], cwd: str) -> str | None:
    """Invoke `agy models` inside an isolated cwd, returning stdout or None on failure/timeout."""
    try:
        res = subprocess.run(
            [AGY_BIN, "models"],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=25,
        )
        if res.returncode == 0:
            return res.stdout or ""
    except Exception:
        pass
    return None


def _query_agy_credits(env: dict[str, str], cwd: str) -> dict | None:
    """Invoke `agy --output-format json -p /credits` inside an isolated cwd, returning parsed credits dict or None."""
    try:
        res = subprocess.run(
            [AGY_BIN, "--output-format", "json", "-p", "/credits"],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode == 0 and res.stdout:
            payload = json.loads(res.stdout.strip())
            if isinstance(payload, dict) and payload.get("status") != "ERROR":
                cmd_data = (payload.get("command") or {}).get("data")
                if isinstance(cmd_data, dict) and "remaining_credits" in cmd_data:
                    out: dict[str, object] = {
                        "remainingCredits": int(cmd_data.get("remaining_credits") or 0)
                    }
                    up_uri = str(cmd_data.get("upgrade_uri") or "").strip()
                    if up_uri:
                        out["upgradeUrl"] = up_uri
                    return out
    except (Exception, AssertionError):
        pass
    return None


def _extract_cached_google_license_and_credits(cached_entry: dict | None) -> tuple[dict, dict, dict]:
    """Extract cached `(license_info, oauth_info, credits_info)` from a profile's cached accountMeta."""
    if not isinstance(cached_entry, dict):
        return {}, {}, {}
    meta = cached_entry.get("accountMeta")
    if not isinstance(meta, dict):
        return {}, {}, {}
    lic: dict[str, str] = {}
    for k in ("userTier", "tierDisplayName", "upgradeText", "upgradeUrl"):
        val = meta.get(k)
        if isinstance(val, str) and val.strip():
            lic[k] = val.strip()
    if lic.get("userTier") or lic.get("tierDisplayName"):
        comb = f"{lic.get('userTier', '')} {lic.get('tierDisplayName', '')}".lower()
        if "ultra" in comb:
            lic["tier"] = "ULTRA"
        elif "free" in comb or "starter" in comb:
            lic["tier"] = "FREE"
        elif "pro" in comb or "standard" in comb:
            lic["tier"] = "PRO"
    oauth: dict[str, str] = {}
    auth_m = meta.get("authMethod")
    if isinstance(auth_m, str) and auth_m.strip():
        oauth["auth_method"] = auth_m.strip()
    cred: dict[str, object] = {}
    if "remainingCredits" in meta and meta["remainingCredits"] is not None:
        cred["remainingCredits"] = meta["remainingCredits"]
    return lic, oauth, cred


def fetch_quota_for_profile(
    profile: str,
    force_probe: bool = False,
    batch_mode: bool = False,
    cached_override: dict | None = None,
) -> dict:
    """Execute agy --output-format json -p '/usage' (plus Hybrid + Cache `agy models` and Google license discovery) for a profile."""
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    if not os.path.isdir(ag_home):
        return {"profile": profile, "success": False, "error": f"Profile home not found: {ag_home}"}

    # 1. Fast check if account was disabled for ToS violation (submit an appeal)
    if not force_probe:
        appeal_err_id = check_profile_appeal_status(profile)
        if appeal_err_id:
            return {
                "profile": profile,
                "success": False,
                "status": "DISABLED",
                "is_appeal": True,
                "error_id": appeal_err_id,
                "duration": 0.05,
                "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)"
            }

    # 2. Fast check if account has CLI auth token in Keychain (PREVENTS agy FROM OPENING BROWSER!)
    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_appeal": False,
            "duration": 0.05,
            "error": "Profile chưa đăng nhập CLI. Cần đăng nhập bằng Terminal trước khi lấy Quota."
        }

    # 3. Unlock Keychain
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    # 4. Build isolated environment
    env = build_profile_cli_env(profile)

    cmd = [AGY_BIN, "--output-format", "json", "-p", "/usage"]
    t0 = time.time()
    try:
        with tempfile.TemporaryDirectory(prefix=f"agy_usage_{profile}_") as sandbox_cwd:
            proc = subprocess.run(cmd, env=env, cwd=sandbox_cwd, capture_output=True, text=True, timeout=45)
            duration = time.time() - t0
            all_out = (proc.stdout or "") + " " + (proc.stderr or "")

            appeal_out_id = check_profile_appeal_status(profile, all_out)
            if appeal_out_id:
                return {
                    "profile": profile,
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": appeal_out_id,
                    "duration": duration,
                    "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)"
                }

            if proc.returncode != 0:
                return {
                    "profile": profile,
                    "success": False,
                    "duration": duration,
                    "error": proc.stderr.strip() or f"Process exited with code {proc.returncode}"
                }

            stdout = proc.stdout.strip()
            data = json.loads(stdout)
            cmd_data = (data.get("command") or {}).get("data") or {}
            raw_groups = cmd_data.get("groups")
            groups = raw_groups if isinstance(raw_groups, list) else []
            plan_raw = str(
                cmd_data.get("plan_name")
                or cmd_data.get("tier")
                or cmd_data.get("tier_name")
                or ""
            ).strip()

            cached_entry = dict(_peek_cached_profile(profile))
            if isinstance(cached_override, dict):
                cached_entry.update(cached_override)
            cached_lic, cached_oauth, cached_cred = _extract_cached_google_license_and_credits(
                cached_entry
            )

            usage_parsed = parse_usage_group_models(groups)
            group_desc_sig = usage_parsed["groupDescSig"]

            should_fetch_models = (not batch_mode) or (
                not _is_models_cache_warm(cached_entry, group_desc_sig)
            )
            has_warm_cached_license = bool(
                cached_lic.get("userTier") or cached_lic.get("tierDisplayName")
            )

            # Read live OAuth metadata from Keychain (local-only, zero network calls)
            oauth_info = read_antigravity_oauth_record(profile) or cached_oauth

            # ANTI-BAN / RATE-LIMIT GUARD:
            # In batch_mode ("Refresh tất cả" across 20+ profiles), skip calling
            # aicode.googleapis.com/v1alpha:fetchLicenses when the 24h hybrid cache
            # already holds the profile's verified Google license tier.
            if should_fetch_models or not has_warm_cached_license:
                live_license = fetch_antigravity_google_license(
                    profile,
                    access_token=oauth_info.get("access_token") if isinstance(oauth_info, dict) else None,
                )
            else:
                live_license = {}
            license_info = live_license if live_license else cached_lic

            if not plan_raw and license_info.get("tierDisplayName"):
                plan_raw = str(license_info["tierDisplayName"]).strip()

            plan_up = plan_raw.upper()
            lic_tier = str(license_info.get("tier") or "").strip().upper()
            items = parse_quota_items(groups)
            has_5h = items["gem_5h"]["available"] or items["cld_5h"]["available"]
            if lic_tier in ("ULTRA", "PRO", "FREE"):
                tier = lic_tier
            elif "ULTRA" in plan_up:
                tier = "ULTRA"
            elif "FREE" in plan_up or (groups and not has_5h):
                tier = "FREE"
            else:
                tier = "PRO"

            models_stdout = (
                _query_agy_models_stdout(env, sandbox_cwd) if should_fetch_models else None
            )
            credits_info = (
                (_query_agy_credits(env, sandbox_cwd) if tier != "FREE" else None)
                if should_fetch_models
                else cached_cred
            )
            if credits_info is None and cached_cred:
                credits_info = cached_cred

        if models_stdout is not None:
            available_models = parse_agy_models_output(models_stdout)
            model_catalog = parse_agy_models_catalog(models_stdout)
            models_fetched_at = datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        else:
            available_models = list(cached_entry.get("availableModels") or [])
            cached_cat = cached_entry.get("modelCatalog")
            model_catalog = (
                list(cached_cat)
                if isinstance(cached_cat, list)
                else (
                    parse_agy_models_catalog("\n".join(available_models))
                    if available_models
                    else []
                )
            )
            models_fetched_at = str(cached_entry.get("modelsFetchedAt") or "")

        group_models = _reconcile_group_models(usage_parsed, model_catalog, cached_entry)
        argon_mode = classify_argon_mode(
            groups,
            group_models=group_models,
            model_catalog=model_catalog,
            available_models=available_models,
            cached_entry=cached_entry,
        )
        capabilities = _derive_profile_capabilities(
            tier=tier,
            plan_name=plan_raw,
            has_dedicated_argon=bool(usage_parsed["hasDedicatedArgonGroup"]),
            argon_mode=argon_mode,
            group_models=group_models,
            model_catalog=model_catalog,
            available_models=available_models,
        )
        safe_oauth_info = {
            k: v for k, v in (oauth_info or {}).items() if k in ("email", "auth_method", "expiry")
        }
        norm_acct = normalize_antigravity_account(
            profile,
            capabilities,
            argon_mode,
            email=safe_oauth_info.get("email"),
            license_info=license_info,
            oauth_info=safe_oauth_info,
            credits_info=credits_info,
        )

        return {
            "profile": profile,
            "success": True,
            "duration": duration,
            "groups": groups,
            "email": norm_acct["email"],
            "tier": capabilities["tier"],
            "planLabel": norm_acct["planLabel"],
            "vendorLabel": norm_acct["vendorLabel"],
            "priority": norm_acct["priority"],
            "plan_name": plan_raw,
            "groupModels": group_models,
            "groupDescSig": group_desc_sig,
            "availableModels": available_models,
            "modelCatalog": model_catalog,
            "modelsFetchedAt": models_fetched_at,
            "argonMode": argon_mode,
            "capabilities": capabilities,
            "accountMeta": norm_acct["accountMeta"],
            "licenseInfo": license_info,
            "oauthInfo": safe_oauth_info,
            "creditsInfo": credits_info or {},
        }
    except subprocess.TimeoutExpired:
        return {"profile": profile, "success": False, "duration": 45.0, "error": "Request timed out (45s)"}
    except Exception as e:
        return {"profile": profile, "success": False, "error": str(e)}


def parse_quota_items(groups: list) -> dict:
    """Extract standard buckets including description into a structured dictionary."""
    items = {
        "gem_5h": {"fraction": 1.0, "reset_time": "", "description": "", "available": False},
        "gem_weekly": {"fraction": 1.0, "reset_time": "", "description": "", "available": False},
        "cld_5h": {"fraction": 1.0, "reset_time": "", "description": "", "available": False},
        "cld_weekly": {"fraction": 1.0, "reset_time": "", "description": "", "available": False},
        "argon_5h": None,
        "argon_weekly": {"fraction": 0.0, "reset_time": "", "description": "", "available": False},
    }

    for g in groups:
        g_name = g.get("name", "").lower()
        if "gemini models" in g_name:
            for b in g.get("buckets", []):
                entry = {
                    "fraction": b.get("remaining_fraction", 1.0),
                    "reset_time": b.get("reset_time", ""),
                    "description": b.get("description", ""),
                    "available": True,
                }
                if b.get("window") == "5h":
                    items["gem_5h"] = entry
                elif b.get("window") == "weekly":
                    items["gem_weekly"] = entry
        elif "claude" in g_name:
            for b in g.get("buckets", []):
                entry = {
                    "fraction": b.get("remaining_fraction", 1.0),
                    "reset_time": b.get("reset_time", ""),
                    "description": b.get("description", ""),
                    "available": True,
                }
                if b.get("window") == "5h":
                    items["cld_5h"] = entry
                elif b.get("window") == "weekly":
                    items["cld_weekly"] = entry
        elif "argon" in g_name:
            for b in g.get("buckets", []):
                entry = {
                    "fraction": b.get("remaining_fraction", 1.0),
                    "reset_time": b.get("reset_time", ""),
                    "description": b.get("description", ""),
                    "available": True,
                }
                if b.get("window") == "5h":
                    items["argon_5h"] = entry
                elif b.get("window") == "weekly":
                    items["argon_weekly"] = entry

    return items


def _resolve_result_model_meta(result: dict) -> tuple[dict[str, list[str]], str, dict]:
    """Extract or derive `(group_models, argon_mode, capabilities)` from a quota result dict."""
    groups = result.get("groups") or []
    usage_parsed = parse_usage_group_models(groups)
    model_catalog = result.get("modelCatalog") if isinstance(result.get("modelCatalog"), list) else []
    available_models = (
        result.get("availableModels") if isinstance(result.get("availableModels"), list) else []
    )
    group_models = (
        result["groupModels"]
        if isinstance(result.get("groupModels"), dict)
        else _reconcile_group_models(usage_parsed, model_catalog)
    )
    argon_mode = str(
        result.get("argonMode")
        or classify_argon_mode(groups, group_models, model_catalog, available_models)
    )
    items = parse_quota_items(groups)
    has_5h = items["gem_5h"]["available"] or items["cld_5h"]["available"]
    tier = str(result.get("tier") or ("PRO" if has_5h else "FREE"))
    capabilities = (
        result["capabilities"]
        if isinstance(result.get("capabilities"), dict)
        else _derive_profile_capabilities(
            tier=tier,
            plan_name=str(result.get("plan_name") or ""),
            has_dedicated_argon=bool(usage_parsed["hasDedicatedArgonGroup"]),
            argon_mode=argon_mode,
            group_models=group_models,
            model_catalog=model_catalog,
            available_models=available_models,
        )
    )
    return group_models, argon_mode, capabilities


def _short_card_group_title(models: list[str], suffix: str, fallback: str) -> str:
    """Build a bounded <=23-char card header from dynamic group model names."""
    if not models:
        return fallback
    lead = models[0]
    candidate = f"{lead} {suffix}".strip()
    if len(candidate) <= 23:
        return candidate
    return fallback


def print_dashboard_cards(result: dict):
    """Render the full Dashboard matching the user's reference image."""
    profile = result["profile"]
    if not result.get("success"):
        if result.get("is_appeal") or result.get("status") == "DISABLED":
            print(f"\n{BOLD}{RED}❌ PROFILE: {profile}{RESET}  \033[48;2;127;29;29m\033[1;37m 🚫 BỊ KHÓA (APPEAL NEEDED) \033[0m")
            print(f"  {RED}Trạng thái: Tài khoản bị Google vô hiệu hóa do vi phạm Điều khoản dịch vụ!{RESET}")
            print(f"  {AMBER}Chi tiết lỗi: This service has been disabled in this account for violation of Terms of Service.{RESET}")
            print(f"  {CYAN}👉 Cần gửi đơn kháng nghị (Submit an appeal) tới Google để khôi phục tài khoản:{RESET}")
            print(f"     {BOLD}{WHITE}https://docs.google.com/forms/d/e/1FAIpQLScOJWibQ_-hYuVv63kJTgEqlgAaOwRLGFTbXm-QY1gz8U0CGA/viewform{RESET}\n")
            return

        print(f"\n{BOLD}{RED}❌ PROFILE: {profile}{RESET}  \033[38;2;245;158;11m🔑 AUTH NEEDED\033[0m")
        print(f"  {RED}Trạng thái: Chưa xác thực CLI ({result.get('error', 'Authentication or timeout')}){RESET}")
        print(f"  {CYAN}👉 Để đăng nhập CLI cho profile này, hãy chạy lệnh:{RESET}")
        print(f"     {BOLD}{WHITE}{profile}-cli{RESET}\n")
        return

    items = parse_quota_items(result.get("groups", []))
    group_models, argon_mode, capabilities = _resolve_result_model_meta(result)

    # Determine status tag based only on available buckets
    avail_fractions = [
        item["fraction"] for item in items.values()
        if item and item.get("available")
    ]
    if not avail_fractions or min(avail_fractions) <= 0.0:
        status_tag = "\033[38;2;239;68;68m🔴 EXHAUSTED\033[0m"
    else:
        status_tag = "\033[38;2;114;188;130m🟢 ACTIVE\033[0m"

    has_5h = items["gem_5h"].get("available", False) or items["cld_5h"].get("available", False)
    cap_tier = capabilities.get("tier") or ("PRO" if has_5h else "FREE")
    norm_acct = normalize_antigravity_account(profile, {"tier": cap_tier, **capabilities}, argon_mode)
    dyn_priority = result.get("priority") if isinstance(result.get("priority"), int) else norm_acct["priority"]
    if cap_tier == "ULTRA":
        tier_tag = TAG_ULTRA
        priority_tag = format_priority_tag(dyn_priority)
    elif has_5h:
        tier_tag = TAG_PRO
        priority_tag = format_priority_tag(dyn_priority)
    else:
        tier_tag = "\033[48;2;217;119;6m\033[1;37m FREE \033[0m"
        priority_tag = format_priority_tag(20)

    extra_badges: list[str] = []
    if capabilities.get("hasCarbon"):
        extra_badges.append(TAG_CARBON)
    if capabilities.get("hasArgon") or items["argon_weekly"].get("available", False):
        extra_badges.append(TAG_ARGON)
    if capabilities.get("hasOrchestrator"):
        extra_badges.append(TAG_ORCHESTRATOR)
    extra_tag_str = ("  " + "  ".join(extra_badges)) if extra_badges else ""

    print(f"\n{BOLD}{WHITE}✦ Profile: {CYAN}{profile}{RESET}  {tier_tag}  {priority_tag}{extra_tag_str}  {status_tag}")
    if group_models.get("gemini"):
        print(f"  {CYAN}✦ Gemini Models{RESET} : {GRAY}{', '.join(group_models['gemini'])}{RESET}")
    if group_models.get("claude"):
        print(f"  \033[38;2;251;146;60m✺ Claude & GPT{RESET}  : {GRAY}{', '.join(group_models['claude'])}{RESET}")
    if group_models.get("argon"):
        argon_note = " (Shared Gemini)" if argon_mode == "shared_gemini" else ""
        print(f"  \033[38;2;192;132;252m✣ Argon Models{RESET}  : {GRAY}{', '.join(group_models['argon'])}{argon_note}{RESET}")

    # Row 1: Gemini 5H  &  Claude 5H
    gem_5h_time = format_countdown(items["gem_5h"]["reset_time"])
    cld_5h_time = format_countdown(items["cld_5h"]["reset_time"])
    gem_5h_title = _short_card_group_title(group_models.get("gemini", []), "5H", "Gemini 3.8 / Pro 5H")
    cld_5h_title = _short_card_group_title(group_models.get("claude", []), "5H", "Claude 5.5 / GPT 5H")
    c1 = render_card("✦", CYAN, gem_5h_title, gem_5h_time, items["gem_5h"]["fraction"], width=45, available=items["gem_5h"]["available"])
    c2 = render_card("✺", "\033[38;2;251;146;60m", cld_5h_title, cld_5h_time, items["cld_5h"]["fraction"], width=45, available=items["cld_5h"]["available"])
    for l1, l2 in zip(c1, c2):
        print(l1 + "  " + l2)

    # Row 2: Gemini Weekly  &  Claude Weekly
    gem_w_time = format_countdown(items["gem_weekly"]["reset_time"])
    cld_w_time = format_countdown(items["cld_weekly"]["reset_time"])
    c3 = render_card("✦", CYAN, "Gemini Weekly", gem_w_time, items["gem_weekly"]["fraction"], width=45, available=items["gem_weekly"]["available"])
    c4 = render_card("✺", "\033[38;2;251;146;60m", "Claude Weekly", cld_w_time, items["cld_weekly"]["fraction"], width=45, available=items["cld_weekly"]["available"])
    for l3, l4 in zip(c3, c4):
        print(l3 + "  " + l4)

    # Row 3: Argon 5H (if present)
    if items["argon_5h"] is not None:
        arg_5h_time = format_countdown(items["argon_5h"]["reset_time"])
        c5_5h = render_card("✦", CYAN, "Gemini 4 Argon 5H", arg_5h_time, items["argon_5h"]["fraction"], width=92, available=items["argon_5h"]["available"])
        for l in c5_5h:
            print(l)

    # Row 4: Argon Weekly (independent separate bucket OR mirrored Shared Gemini Pool)
    if argon_mode == "shared_gemini":
        arg_w_avail = bool(items["gem_weekly"]["available"])
        arg_w_frac = items["gem_weekly"]["fraction"]
        arg_w_time = format_countdown(items["gem_weekly"]["reset_time"])
        arg_w_title = (
            "Gemini 4 Carbon & Argon Weekly (Shared Gemini)"
            if capabilities.get("hasCarbon")
            else "Gemini 4 Argon Weekly (Shared Gemini)"
        )
    else:
        arg_w_avail = bool(items["argon_weekly"]["available"]) and argon_mode == "separate"
        arg_w_frac = items["argon_weekly"]["fraction"]
        arg_w_time = format_countdown(items["argon_weekly"]["reset_time"])
        arg_w_title = "Gemini 4 Argon Weekly"
    tags_str = f"{TAG_HIGH} {TAG_MED} {TAG_LOW}" if arg_w_avail else None
    c5 = render_card("✦", CYAN, arg_w_title, arg_w_time, arg_w_frac, width=92, tags=tags_str, available=arg_w_avail)
    for l in c5:
        print(l)

    # Actions footer matching /refresh-session: Refresh nhanh, Kích hoạt & Lên lịch
    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh {profile}{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Kích hoạt\033[0m     : {DIM}check-quota ping {profile}{RESET}")
    print(f"   \033[38;2;192;132;252m⏰ Lên lịch\033[0m      : {DIM}/refresh-session schedule --time 07:00 --delay 30{RESET}\n")


def render_mini_bar(item: dict, width: int = 14) -> str:
    """Render a compact progress bar for tabular summary with unified consumed track color.
    When inactive, renders a muted gray bar with no text as requested."""
    if not item or not item.get("available", True):
        return f"{GRAY}[{'░' * width}]{RESET}       "
    fraction = max(0.0, min(1.0, item["fraction"]))
    pct = fraction * 100.0
    fill_color, track_color = get_color_pair(pct)
    filled = int(round(fraction * width))
    empty = width - filled
    return f"[{fill_color}{'█' * filled}{RESET}{track_color}{'░' * empty}{RESET}] {fill_color}{pct:5.1f}%{RESET}"


def print_all_summary(results: list, show_providers: bool = True):
    """Print an executive multi-profile summary table strictly aligned to 122 chars."""
    table_w = 122
    if show_providers:
        print(f"\n{BOLD}{CYAN}=== AI AGENT PROVIDERS (CLAUDE, CODEX, KIRO) ==={RESET}")
        try:
            c_data = fetch_claude_quota()
            print_claude_card(c_data)
        except Exception:
            pass
        try:
            o_data = fetch_codex_quota()
            print_codex_card(o_data)
        except Exception:
            pass
        try:
            k_data = fetch_kiro_quota()
            print_kiro_card(k_data)
        except Exception:
            pass
    print(f"\n{BOLD}{WHITE}{'=' * table_w}{RESET}")
    print(f"{BOLD}{CYAN}                      ANTIGRAVITY ACCOUNTS QUOTA DASHBOARD (ALL PROFILES){RESET}")
    print(f"{BOLD}{WHITE}{'=' * table_w}{RESET}")
    print(f"{BOLD}{'Profile':<18} | {'Gemini Weekly':<23} | {'Gemini 5H':<23} | {'Claude Weekly':<23} | {'Argon Weekly':<23}{RESET}")
    print(f"{DIM}{'-' * table_w}{RESET}")

    cols_w = 23 * 4 + 3 * 3  # 101 chars across the 4 quota columns

    for res in results:
        profile = res["profile"]
        if not res.get("success"):
            if res.get("is_appeal") or res.get("status") == "DISABLED":
                err_msg = "Vi phạm ToS / Cần kháng nghị (Submit Appeal)"
                msg = f"  \033[38;2;239;68;68m🚫 DISABLED\033[0m - {RED}{err_msg}{RESET}"
                pad = max(1, cols_w - str_vis_width(msg))
                print(f"{BOLD}{profile:<18}{RESET} |{msg}{' ' * pad}|")
                continue

            err_msg = "Chưa đăng nhập CLI"
            msg = f"  \033[38;2;245;158;11m🔑 AUTH NEEDED\033[0m - {RED}{err_msg}{RESET} {DIM}({profile}-cli){RESET}"
            pad = max(1, cols_w - str_vis_width(msg))
            print(f"{BOLD}{profile:<18}{RESET} |{msg}{' ' * pad}|")
            continue

        items = parse_quota_items(res.get("groups", []))
        group_models, argon_mode, _caps = _resolve_result_model_meta(res)
        argon_item = (
            dict(items["gem_weekly"])
            if argon_mode == "shared_gemini"
            else items["argon_weekly"]
        )
        bar_gem_w = render_mini_bar(items["gem_weekly"])
        bar_gem_5h = render_mini_bar(items["gem_5h"])
        bar_cld_w = render_mini_bar(items["cld_weekly"])
        bar_arg_w = render_mini_bar(argon_item)

        print(f"{BOLD}{profile:<18}{RESET} | {bar_gem_w} | {bar_gem_5h} | {bar_cld_w} | {bar_arg_w}")
        if argon_mode == "shared_gemini" or any(group_models.values()):
            sub_parts: list[str] = []
            if argon_mode == "shared_gemini":
                mirrored_pct = max(0.0, min(1.0, float(argon_item.get("fraction", 0.0)))) * 100.0
                mirrored_rst = format_countdown(argon_item.get("reset_time", ""))
                sub_parts.append(f"Argon: (Shared Gemini) {mirrored_pct:5.1f}% {mirrored_rst}")
            roster = (group_models.get("gemini") or []) + (group_models.get("claude") or [])
            if roster:
                roster_txt = ", ".join(roster)
                if len(roster_txt) > 54:
                    roster_txt = roster_txt[:51] + "..."
                sub_parts.append(f"Models: {roster_txt}")
            if sub_parts:
                detail = " · ".join(sub_parts)
                print(f"{'':<18} | {DIM}↳ {detail}{RESET}")

    print(f"{BOLD}{WHITE}{'=' * table_w}{RESET}\n")


def get_dashboard_html_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "skills" / "check-quota" / "resources" / "dashboard" / "quota_dashboard.html",
        Path(REAL_HOME) / "AllProjects/ai-agent-tools/skills/check-quota/resources/dashboard/quota_dashboard.html",
        Path(REAL_HOME) / "Projects/ai-agent-tools/skills/check-quota/resources/dashboard/quota_dashboard.html",
        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


CACHED_PROFILES_DATA: dict = {}
CACHED_HTML_MTIME: float = 0.0


def _resolve_host_username() -> str:
    """Resolve the host OS username dynamically without machine-specific fallbacks."""
    return (
        os.environ.get("USER")
        or os.environ.get("LOGNAME")
        or Path(REAL_HOME).name
    )


def get_claude_oauth_token() -> tuple[str | None, str | None, bool]:
    """Retrieve Claude Code OAuth access token.

    Returns (token, email, is_logged_in).
    Checks:
    1. Environment variable CLAUDE_CODE_OAUTH_TOKEN
    2. macOS Keychain item 'Claude Code-credentials'
       - If access token is empty or expired but refresh token exists, auto-refreshes via platform.claude.com/v1/oauth/token
    3. Plaintext fallback ~/.claude/.credentials.json
    """
    # 1. Environment variable
    env_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if env_token and env_token.strip():
        return env_token.strip(), None, True

    # 2. macOS Keychain
    try:
        user = _resolve_host_username()
        cmd = ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2.0)
        if proc.returncode != 0:
            proc = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-a", user, "-w"],
                capture_output=True, text=True, timeout=2.0
            )

        if proc.returncode == 0 and proc.stdout:
            stdout_clean = proc.stdout.strip()
            if stdout_clean.startswith("{") and stdout_clean.endswith("}"):
                data = json.loads(stdout_clean)
                oauth = data.get("claudeAiOauth", {})
                access_token = (oauth.get("accessToken") or "").strip()
                refresh_token = (oauth.get("refreshToken") or "").strip()
                expires_at = oauth.get("expiresAt") or 0
                now_ms = int(time.time() * 1000)

                # Valid unexpired access token
                if access_token and (expires_at == 0 or expires_at > now_ms + 60000):
                    return access_token, None, True

                # Expired or empty access token, but refresh token exists
                if refresh_token:
                    try:
                        refresh_url = "https://platform.claude.com/v1/oauth/token"
                        payload = json.dumps({
                            "grant_type": "refresh_token",
                            "refresh_token": refresh_token,
                            "client_id": "9d1c250a-e61b-44d9-88ed-5944d1962f5e",
                        }).encode("utf-8")
                        req = urllib.request.Request(
                            refresh_url,
                            data=payload,
                            headers={
                                "Content-Type": "application/json",
                                "User-Agent": "claude-cli/2.1.231",
                                "Accept": "application/json",
                            }
                        )
                        with urllib.request.urlopen(req, timeout=5.0) as r_resp:
                            if r_resp.status == 200:
                                r_data = json.loads(r_resp.read().decode("utf-8"))
                                new_acc = r_data.get("access_token")
                                new_ref = r_data.get("refresh_token") or refresh_token
                                exp_in = r_data.get("expires_in", 3600)
                                if new_acc:
                                    data["claudeAiOauth"]["accessToken"] = new_acc
                                    data["claudeAiOauth"]["refreshToken"] = new_ref
                                    data["claudeAiOauth"]["expiresAt"] = now_ms + (exp_in * 1000)
                                    try:
                                        subprocess.run(
                                            ["security", "add-generic-password", "-U", "-s", "Claude Code-credentials",
                                             "-a", user, "-w", json.dumps(data)],
                                            capture_output=True, timeout=2.0
                                        )
                                    except Exception:
                                        pass
                                    return new_acc, None, True
                    except Exception as ref_err:
                        sys.stderr.write(f"Warning: Claude token auto-refresh failed: {ref_err}\n")
    except Exception as kc_err:
        sys.stderr.write(f"Warning: Keychain read for Claude failed: {kc_err}\n")

    # 3. Plaintext fallback credentials
    cred_file = Path(REAL_HOME) / ".claude" / ".credentials.json"
    if cred_file.is_file():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                c_json = json.load(f)
            oauth = c_json.get("claudeAiOauth", {})
            token = (oauth.get("accessToken") or "").strip()
            if token:
                return token, None, True
        except Exception:
            pass

    return None, None, False


_ORIG_GET_CLAUDE_OAUTH_TOKEN = get_claude_oauth_token


def _extract_non_secret_claude_oauth_fields(oauth: object, auth_source: str) -> dict:
    """Extract strictly non-secret subscription metadata from claudeAiOauth dict."""
    if not isinstance(oauth, dict):
        return {}
    hints: dict[str, str] = {}
    sub_type = oauth.get("subscriptionType")
    if isinstance(sub_type, str) and sub_type.strip():
        hints["subscriptionType"] = sub_type.strip()
    rate_tier = oauth.get("rateLimitTier")
    if isinstance(rate_tier, str) and rate_tier.strip():
        hints["rateLimitTier"] = rate_tier.strip()
    if auth_source:
        hints["authSource"] = auth_source
    return hints


def _read_claude_oauth_hints() -> dict:
    """Read non-secret subscriptionType and rateLimitTier from Keychain or .credentials.json."""
    hints: dict[str, str] = {}
    env_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
    if env_token and env_token.strip():
        hints["authSource"] = "env"

    should_probe_keychain = (
        get_claude_oauth_token is _ORIG_GET_CLAUDE_OAUTH_TOKEN
        or getattr(subprocess.run, "__module__", "") != "subprocess"
    )
    if should_probe_keychain:
        try:
            user = _resolve_host_username()
            proc = subprocess.run(
                ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
                capture_output=True,
                text=True,
                timeout=2.0,
            )
            if proc.returncode != 0:
                proc = subprocess.run(
                    [
                        "security",
                        "find-generic-password",
                        "-s",
                        "Claude Code-credentials",
                        "-a",
                        user,
                        "-w",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                )
            if proc.returncode == 0 and proc.stdout:
                stdout_clean = proc.stdout.strip()
                if stdout_clean.startswith("{") and stdout_clean.endswith("}"):
                    parsed = json.loads(stdout_clean)
                    if isinstance(parsed, dict):
                        kc_hints = _extract_non_secret_claude_oauth_fields(
                            parsed.get("claudeAiOauth"), "keychain"
                        )
                        if kc_hints.get("subscriptionType") or kc_hints.get("rateLimitTier"):
                            return kc_hints
        except Exception:
            pass

    cred_file = Path(REAL_HOME) / ".claude" / ".credentials.json"
    if cred_file.is_file():
        try:
            with open(cred_file, "r", encoding="utf-8") as f:
                c_json = json.load(f)
            if isinstance(c_json, dict):
                file_hints = _extract_non_secret_claude_oauth_fields(
                    c_json.get("claudeAiOauth"), "credentials_file"
                )
                if file_hints.get("subscriptionType") or file_hints.get("rateLimitTier"):
                    return file_hints
                if not hints.get("authSource") and isinstance(c_json.get("claudeAiOauth"), dict):
                    hints["authSource"] = "credentials_file"
        except Exception:
            pass

    return hints


def normalize_claude_account(
    oauth_hints: dict | None,
    oauth_acc: dict | None,
    api_data: dict | None,
    is_live: bool = False,
) -> dict:
    """Normalize Claude tier, priority (110/105/102/100/98/40), models, and non-secret AccountMeta."""
    hints = oauth_hints if isinstance(oauth_hints, dict) else {}
    acc = oauth_acc if isinstance(oauth_acc, dict) else {}
    api = api_data if isinstance(api_data, dict) else {}

    sub_type = str(
        hints.get("subscriptionType")
        or acc.get("subscriptionType")
        or api.get("subscription_type")
        or api.get("subscriptionType")
        or ""
    ).strip().lower()
    rate_tier = str(
        hints.get("rateLimitTier")
        or acc.get("rateLimitTier")
        or acc.get("organizationRateLimitTier")
        or acc.get("userRateLimitTier")
        or api.get("rate_limit_tier")
        or api.get("rateLimitTier")
        or ""
    ).strip()
    rate_low = rate_tier.lower()
    org_type = str(
        acc.get("organizationType")
        or api.get("organization_type")
        or api.get("organizationType")
        or ""
    ).strip().lower()
    billing_type = str(acc.get("billingType") or api.get("billing_type") or "").strip()
    billing_low = billing_type.lower()
    auth_source = str(
        hints.get("authSource")
        or ("live_api" if is_live else ("claude_json_cache" if acc else "unauthenticated"))
    ).strip()
    has_max = bool(acc.get("has_claude_max") or acc.get("hasClaudeMax") or api.get("has_claude_max"))

    if "20x" in rate_low or sub_type in ("max_20x", "claude_max_20x"):
        plan_label, plan_type, priority = "CLAUDE MAX 20X", "max_20x", 110
    elif "5x" in rate_low or sub_type in ("max_5x", "claude_max_5x"):
        plan_label, plan_type, priority = "CLAUDE MAX 5X", "max_5x", 105
    elif "enterprise" in sub_type or "enterprise" in org_type or "enterprise" in rate_low:
        plan_label, plan_type, priority = "CLAUDE ENTERPRISE", "enterprise", 105
    elif "max" in sub_type or "claude_max" in org_type or "claude_max" in rate_low or has_max:
        plan_label, plan_type, priority = "CLAUDE MAX", "max", 105
    elif "team" in sub_type or "team" in org_type or "claude_team" in rate_low:
        plan_label, plan_type, priority = "CLAUDE TEAM", "team", 102
    elif (
        sub_type in ("api", "apikey", "api_key", "console")
        or org_type in ("api", "console")
        or billing_low in ("api", "prepaid_api", "console")
        or auth_source == "api_key"
    ):
        plan_label, plan_type, priority = "CLAUDE API", "api", 98
    elif sub_type in ("free", "claude_free") or org_type in ("free", "claude_free") or "claude_free" in rate_low:
        plan_label, plan_type, priority = "CLAUDE FREE", "free", 40
    else:
        plan_label, plan_type, priority = "CLAUDE PRO", "pro", 100

    available_models = (
        ["Claude Sonnet 4.6", "Claude Haiku 4.5"]
        if plan_type == "free"
        else ["Claude Opus 4.6", "Claude Sonnet 4.6", "Claude Haiku 4.5"]
    )
    limits_raw = api.get("limits")
    if isinstance(limits_raw, list):
        seen_low = {m.lower() for m in available_models}
        for lim in limits_raw:
            if not isinstance(lim, dict):
                continue
            scope = lim.get("scope")
            model_obj = scope.get("model") if isinstance(scope, dict) else None
            if isinstance(model_obj, dict):
                disp = str(model_obj.get("display_name") or model_obj.get("id") or "").strip()
                if disp and disp.lower() not in seen_low:
                    available_models.append(disp)
                    seen_low.add(disp.lower())

    extra_usage = api.get("extra_usage") if isinstance(api.get("extra_usage"), dict) else {}
    extra_enabled = bool(
        extra_usage.get("is_enabled")
        if "is_enabled" in extra_usage
        else acc.get("hasExtraUsageEnabled", False)
    )
    extra_summary = ""
    if extra_enabled:
        used_cr = extra_usage.get("used_credits")
        lim_cr = extra_usage.get("monthly_limit")
        if used_cr is not None and lim_cr is not None:
            extra_summary = f"Extra usage: {used_cr} / {lim_cr}"
        else:
            extra_summary = "Extra usage enabled"

    org_name = str(acc.get("organizationName") or acc.get("organization_name") or "").strip()
    account_meta: dict[str, object] = {
        "provider": "claude",
        "vendorLabel": "ANTHROPIC",
        "planType": plan_type,
        "planLabel": plan_label,
        "cliCommand": "claude",
        "configPath": "~/.claude.json",
        "secondaryPath": "~/.claude/.credentials.json",
        "extraUsageEnabled": extra_enabled,
    }
    if org_name:
        account_meta["organizationName"] = org_name
    if org_type:
        account_meta["organizationType"] = org_type
    if billing_type:
        account_meta["billingType"] = billing_type
    if rate_tier:
        account_meta["rateLimitTier"] = rate_tier
    if auth_source:
        account_meta["authSource"] = auth_source
    if extra_summary:
        account_meta["extraUsageSummary"] = extra_summary

    return {
        "tier": plan_label,
        "planLabel": plan_label,
        "vendorLabel": "ANTHROPIC",
        "priority": priority,
        "availableModels": available_models,
        "accountMeta": account_meta,
    }


def _merge_claude_utilization(existing_cache: dict | None, new_util: dict, account_uuid: str = "") -> dict:
    """Merge live Claude usage into cached utilization without clobbering omitted richer fields."""
    mod = _load_refresh_session_module()
    if mod and hasattr(mod, "merge_claude_utilization"):
        return mod.merge_claude_utilization(existing_cache, new_util, account_uuid=account_uuid)
    cache = existing_cache if isinstance(existing_cache, dict) else {}
    existing_util = cache.get("utilization")
    existing_uuid = str(cache.get("accountUuid") or "").strip()
    target_uuid = str(account_uuid or "").strip()
    if not isinstance(existing_util, dict) or (existing_uuid and target_uuid and existing_uuid != target_uuid):
        return dict(new_util)
    merged = {**existing_util, **new_util}
    if "limits" not in new_util and isinstance(existing_util.get("limits"), list):
        five_h = new_util.get("five_hour")
        seven_d = new_util.get("seven_day")
        synced_limits = []
        for entry in existing_util["limits"]:
            if not isinstance(entry, dict):
                synced_limits.append(entry)
                continue
            item = dict(entry)
            if item.get("kind") == "session" and isinstance(five_h, dict):
                if five_h.get("utilization") is not None:
                    item["percent"] = five_h["utilization"]
                if five_h.get("resets_at"):
                    item["resets_at"] = five_h["resets_at"]
            elif item.get("kind") == "weekly_all" and isinstance(seven_d, dict):
                if seven_d.get("utilization") is not None:
                    item["percent"] = seven_d["utilization"]
                if seven_d.get("resets_at"):
                    item["resets_at"] = seven_d["resets_at"]
            synced_limits.append(item)
        merged["limits"] = synced_limits
    return merged


def update_claude_json_cache(u: dict, account_uuid: str = ""):
    """Synchronize freshly fetched live usage into ~/.claude.json cachedUsageUtilization."""
    claude_json_path = Path(REAL_HOME) / ".claude.json"
    if claude_json_path.is_file():
        try:
            with open(claude_json_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            if not account_uuid:
                account_uuid = c_data.get("oauthAccount", {}).get("accountUuid", "")
            merged_util = _merge_claude_utilization(
                c_data.get("cachedUsageUtilization"),
                u,
                account_uuid=account_uuid,
            )
            c_data["cachedUsageUtilization"] = {
                "fetchedAtMs": int(time.time() * 1000),
                "accountUuid": account_uuid,
                "utilization": merged_util,
            }
            with open(claude_json_path, "w", encoding="utf-8") as f:
                json.dump(c_data, f, indent=2)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to update .claude.json cache: {e}\n")


def _humanize_claude_key(key: str) -> str:
    """Convert snake_case Claude quota key or suffix into a readable display label."""
    raw = str(key or "").strip()
    if raw.startswith("seven_day_"):
        raw = raw[len("seven_day_"):]
    tokens = [tok for tok in raw.split("_") if tok]
    if not tokens:
        return "Scoped"
    special = {"oauth": "OAuth", "api": "API", "ai": "AI", "cli": "CLI"}
    return " ".join(special.get(tok.lower(), tok.capitalize()) for tok in tokens)


def _format_claude_surface_label(surface: object) -> str:
    """Extract readable surface name from string or dict scope.surface."""
    if isinstance(surface, dict):
        val = str(surface.get("display_name") or surface.get("name") or surface.get("id") or "").strip()
    elif isinstance(surface, str):
        val = surface.strip()
    else:
        val = ""
    if not val:
        return ""
    if re.fullmatch(r"[a-z0-9_]+", val):
        return _humanize_claude_key(val)
    return val


def _extract_claude_scope_label(scope: object) -> str:
    """Extract combined model + surface label from a Claude limit scope object."""
    if not isinstance(scope, dict):
        return ""
    model = scope.get("model")
    if isinstance(model, dict):
        model_label = str(model.get("display_name") or model.get("name") or model.get("id") or "").strip()
    elif isinstance(model, str):
        model_label = model.strip()
    else:
        model_label = ""
    surface_label = _format_claude_surface_label(scope.get("surface"))
    if model_label and surface_label:
        return f"{model_label} · {surface_label}"
    return model_label or surface_label


def _format_claude_bucket_timing(
    resets_at_iso: str,
    group: str,
    now_utc: datetime.datetime,
) -> tuple[int, str, str]:
    """Compute (reset_ts, reset_local, countdown) for a Claude quota bucket."""
    resets_at_ts = 0
    local_reset = ""
    rem_sec = 0
    iso_str = str(resets_at_iso or "").strip()
    if iso_str:
        try:
            dt = datetime.datetime.fromisoformat(iso_str)
            resets_at_ts = int(dt.timestamp())
            local_reset = dt.astimezone().strftime("%H:%M:%S" if group == "session" else "%d/%m %H:%M")
            rem_sec = max(0, int((dt - now_utc).total_seconds()))
        except (ValueError, TypeError):
            resets_at_ts = 0

    if group == "session":
        countdown = (
            f"⏱ {rem_sec // 3600}h {(rem_sec % 3600) // 60}m"
            if rem_sec > 0
            else "⏱ 5h 00m (Reset xong)"
        )
    else:
        if rem_sec > 0:
            days = rem_sec // 86400
            hours = (rem_sec % 86400) // 3600
            mins = (rem_sec % 3600) // 60
            countdown = f"⏱ {days}d {hours}h" if days > 0 else f"⏱ {hours}h {mins}m"
        else:
            countdown = "⏱ 7d 00h (Reset xong)"
    if local_reset and rem_sec > 0:
        countdown += f" ({local_reset})"
    return resets_at_ts, local_reset, countdown


def _build_claude_share_info(share_entry: object) -> dict | None:
    """Normalize weekly_scoped_shares entry into UI/CLI-friendly shareInfo metadata."""
    if not isinstance(share_entry, dict):
        return None
    limit_idx = share_entry.get("limit_index")
    used_pct = share_entry.get("used_percent_of_weekly")
    allowance_pct = share_entry.get("allowance_percent_of_weekly")
    if allowance_pct is not None and used_pct is not None:
        label = f"Allowance: {allowance_pct}% of weekly (used {used_pct}%)"
    elif allowance_pct is not None:
        label = f"Allowance: {allowance_pct}% of weekly"
    elif used_pct is not None:
        label = f"Used {used_pct}% of weekly"
    else:
        label = ""
    return {
        "limitIndex": limit_idx,
        "usedPercentOfWeekly": used_pct,
        "allowancePercentOfWeekly": allowance_pct,
        "label": label,
    }


def _slugify_bucket_id(text: str, fallback: str) -> str:
    """Generate a safe lowercase ASCII slug identifier for a dynamic bucket."""
    slug = re.sub(r"[^a-z0-9]+", "_", str(text or "").lower()).strip("_")
    return slug or fallback


def _make_claude_bucket(
    *,
    bucket_id: str,
    name: str,
    group: str,
    kind: str,
    scope_label: str,
    raw_percent: object,
    resets_at_iso: str,
    now_utc: datetime.datetime,
    severity: str = "normal",
    is_active: bool = False,
    is_live: bool = False,
    share_info: dict | None = None,
    unavailable: bool = False,
) -> dict:
    """Construct a normalized Claude quota bucket dictionary."""
    try:
        utilization = float(raw_percent if raw_percent is not None else 0.0)
    except (TypeError, ValueError):
        utilization = 0.0
    utilization = max(0.0, min(100.0, utilization))
    fraction = max(0.0, min(1.0, (100.0 - utilization) / 100.0))
    resets_at_ts, local_reset, countdown = _format_claude_bucket_timing(
        resets_at_iso, group, now_utc
    )
    return {
        "id": bucket_id,
        "name": name,
        "group": group,
        "kind": kind,
        "scopeLabel": scope_label,
        "fraction": fraction,
        "utilization": utilization,
        "countdown": countdown,
        "resetTime": str(resets_at_iso or ""),
        "resetTimeLocal": local_reset,
        "resetTimeTs": resets_at_ts,
        "severity": str(severity or "normal"),
        "isActive": bool(is_active),
        "isLive": bool(is_live),
        "shareInfo": share_info,
        "unavailable": bool(unavailable),
    }


def build_claude_quota_buckets(
    api_data: dict | None,
    now_utc: datetime.datetime | None = None,
    is_live: bool = False,
) -> list[dict]:
    """Normalize Anthropic limits[], weekly_scoped_shares, five_hour, seven_day, and seven_day_* into ordered buckets."""
    data = api_data if isinstance(api_data, dict) else {}
    now_ref = now_utc or datetime.datetime.now(datetime.timezone.utc)

    shares_raw = data.get("weekly_scoped_shares")
    share_by_idx: dict[int, dict] = {}
    if isinstance(shares_raw, list):
        for sh in shares_raw:
            if isinstance(sh, dict) and isinstance(sh.get("limit_index"), int):
                share_by_idx[sh["limit_index"]] = sh

    buckets: list[dict] = []
    seen_ids: set[str] = set()
    seen_scopes: set[str] = set()
    has_session = False
    has_weekly_all = False

    def _unique_id(base_id: str) -> str:
        cand = base_id
        suffix = 2
        while cand in seen_ids:
            cand = f"{base_id}_{suffix}"
            suffix += 1
        seen_ids.add(cand)
        return cand

    limits_raw = data.get("limits")
    if isinstance(limits_raw, list):
        for idx, entry in enumerate(limits_raw):
            if not isinstance(entry, dict):
                continue
            kind = str(entry.get("kind") or "").strip() or f"limit_{idx}"
            group = str(entry.get("group") or ("session" if kind == "session" else "weekly")).strip()
            scope_label = _extract_claude_scope_label(entry.get("scope"))
            raw_pct = entry.get("percent")
            if raw_pct is None:
                raw_pct = entry.get("utilization")
            resets_at_iso = str(entry.get("resets_at") or "").strip()
            severity = str(entry.get("severity") or "normal").strip()
            is_active = bool(entry.get("is_active"))
            share_info = _build_claude_share_info(share_by_idx.get(idx))

            if kind == "session" or (group == "session" and not scope_label):
                has_session = True
                name = "Claude 5H Session Window"
                bucket_id = _unique_id("session")
            elif kind == "weekly_all":
                has_weekly_all = True
                name = "Claude 7D Weekly Remaining"
                bucket_id = _unique_id("weekly_all")
            else:
                prefix = "Claude 5H" if group == "session" else ("Claude 7D" if group == "weekly" or kind.startswith("weekly") else "Claude")
                label_part = scope_label or _humanize_claude_key(kind)
                name = f"{prefix} — {label_part}"
                slug = _slugify_bucket_id(scope_label or kind, f"idx_{idx}")
                bucket_id = _unique_id(f"{kind}_{slug}" if scope_label else kind)
                if scope_label:
                    seen_scopes.add(scope_label.lower())

            buckets.append(
                _make_claude_bucket(
                    bucket_id=bucket_id,
                    name=name,
                    group=group,
                    kind=kind,
                    scope_label=scope_label,
                    raw_percent=raw_pct,
                    resets_at_iso=resets_at_iso,
                    now_utc=now_ref,
                    severity=severity,
                    is_active=is_active,
                    is_live=is_live,
                    share_info=share_info,
                    unavailable=bool(entry.get("locked_reason")),
                )
            )

    if not has_session:
        five_h = data.get("five_hour") if isinstance(data.get("five_hour"), dict) else {}
        is_act_5h, _, _, _ = evaluate_claude_5h_session(data, now_utc=now_ref)
        buckets.append(
            _make_claude_bucket(
                bucket_id=_unique_id("session"),
                name="Claude 5H Session Window",
                group="session",
                kind="session",
                scope_label="",
                raw_percent=five_h.get("utilization", 0),
                resets_at_iso=str(five_h.get("resets_at") or ""),
                now_utc=now_ref,
                is_active=is_act_5h,
                is_live=is_live,
                unavailable=bool(five_h.get("locked_reason")),
            )
        )

    if not has_weekly_all:
        seven_d = data.get("seven_day") if isinstance(data.get("seven_day"), dict) else {}
        buckets.append(
            _make_claude_bucket(
                bucket_id=_unique_id("weekly_all"),
                name="Claude 7D Weekly Remaining",
                group="weekly",
                kind="weekly_all",
                scope_label="",
                raw_percent=seven_d.get("utilization", 0),
                resets_at_iso=str(seven_d.get("resets_at") or ""),
                now_utc=now_ref,
                is_live=is_live,
                unavailable=bool(seven_d.get("locked_reason")),
            )
        )

    for key, val in data.items():
        if not key.startswith("seven_day_") or key == "seven_day_breakdown":
            continue
        if not isinstance(val, dict) or not any(k in val for k in ("utilization", "percent", "resets_at")):
            continue
        scope_label = _humanize_claude_key(key)
        raw_suffix = key[len("seven_day_"):].lower()
        if scope_label.lower() in seen_scopes or raw_suffix in seen_scopes:
            continue
        seen_scopes.add(scope_label.lower())
        raw_pct = val.get("utilization")
        if raw_pct is None:
            raw_pct = val.get("percent", 0)
        buckets.append(
            _make_claude_bucket(
                bucket_id=_unique_id(key),
                name=f"Claude 7D — {scope_label}",
                group="weekly",
                kind=key,
                scope_label=scope_label,
                raw_percent=raw_pct,
                resets_at_iso=str(val.get("resets_at") or ""),
                now_utc=now_ref,
                is_live=is_live,
                unavailable=bool(val.get("locked_reason")),
            )
        )

    return buckets


def fetch_claude_quota() -> dict:
    claude_json_path = Path(REAL_HOME) / ".claude.json"
    email = "Anthropic Claude Pro / Team"
    account_uuid = ""
    c_data = {}
    if claude_json_path.is_file():
        try:
            with open(claude_json_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            oauth_acc = c_data.get("oauthAccount", {})
            if oauth_acc.get("emailAddress"):
                email = oauth_acc["emailAddress"]
            account_uuid = oauth_acc.get("accountUuid", "")
        except Exception as e:
            sys.stderr.write(f"Error reading .claude.json: {e}\n")

    token, token_email, is_logged_in = get_claude_oauth_token()
    if token_email:
        email = token_email

    api_data = None
    is_live = False

    # 1. Primary: Query Anthropic Live API if token is available
    if token:
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "claude-cli/2.1.231",
                "Accept": "application/json",
                "Content-Type": "application/json",
                "anthropic-beta": "claude-code-20250219",
            }
            req = urllib.request.Request("https://api.anthropic.com/api/oauth/usage", headers=headers)
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                if resp.status == 200:
                    raw_data = json.loads(resp.read().decode("utf-8"))
                    api_data = raw_data.get("utilization", raw_data)
                    is_live = True
                    update_claude_json_cache(api_data, account_uuid)
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to fetch live Claude quota from Anthropic API: {e}\n")

    # 2. Fallback: cachedUsageUtilization from .claude.json
    if not api_data:
        api_data = c_data.get("cachedUsageUtilization", {}).get("utilization", {})

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    quota_buckets = build_claude_quota_buckets(api_data, now_utc=now_utc, is_live=is_live)

    session_bucket = next(
        (b for b in quota_buckets if b["kind"] == "session" or b["group"] == "session"),
        quota_buckets[0],
    )
    weekly_bucket = next(
        (b for b in quota_buckets if b["kind"] == "weekly_all"),
        next((b for b in quota_buckets if b["group"] == "weekly"), quota_buckets[-1]),
    )

    is_active_5h, _, eval_resets_ts, eval_local_reset = evaluate_claude_5h_session(
        api_data, now_utc=now_utc
    )
    if session_bucket["isActive"]:
        is_active_5h = True

    fraction_5h = session_bucket["fraction"]
    resets_at_5h_iso = session_bucket["resetTime"]
    local_reset_5h = eval_local_reset or session_bucket["resetTimeLocal"]
    resets_at_5h_ts = eval_resets_ts or session_bucket.get("resetTimeTs", 0)
    countdown_5h = session_bucket["countdown"]

    fraction_7d = weekly_bucket["fraction"]
    resets_at_7d_iso = weekly_bucket["resetTime"]
    local_reset_7d = weekly_bucket["resetTimeLocal"]
    resets_at_7d_ts = weekly_bucket.get("resetTimeTs", 0)
    countdown_7d = weekly_bucket["countdown"]

    # Status handling
    if not is_logged_in and not is_live:
        status = "NEED_LOGIN"
        email_display = f"{email} (Chưa đăng nhập CLI - Run 'claude auth login')"
        countdown_5h_card = "Cần đăng nhập"
    elif is_active_5h or fraction_5h > 0:
        status = "ACTIVE"
        email_display = email
        countdown_5h_card = countdown_5h
    else:
        status = "IDLE"
        email_display = email
        countdown_5h_card = countdown_5h

    # Save to hashed SQLite session store
    save_session_record("claude", resets_at_5h_ts, resets_at_7d_ts, fraction_5h, is_active_5h)

    oauth_acc = c_data.get("oauthAccount", {}) if isinstance(c_data, dict) else {}
    oauth_hints = _read_claude_oauth_hints()
    norm_claude = normalize_claude_account(oauth_hints, oauth_acc, api_data, is_live=is_live)

    public_buckets = [
        {k: v for k, v in b.items() if k != "resetTimeTs"}
        for b in quota_buckets
    ]

    return {
        "profile": "claude",
        "displayName": "Claude Code",
        "isProvider": True,
        "providerType": "claude",
        "tier": norm_claude["tier"],
        "planLabel": norm_claude["planLabel"],
        "vendorLabel": norm_claude["vendorLabel"],
        "priority": norm_claude["priority"],
        "email": email_display,
        "status": status,
        "isSessionActive": is_active_5h,
        "resetTime": resets_at_5h_iso,
        "resetTimeLocal": local_reset_5h,
        "remainingCountdown": countdown_5h_card,
        "hasArgon": True,
        "availableModels": norm_claude["availableModels"],
        "accountMeta": norm_claude["accountMeta"],
        "quotaBuckets": public_buckets,
        "gemini5h": {
            "name": session_bucket["name"],
            "fraction": fraction_5h,
            "countdown": countdown_5h,
            "resetTime": resets_at_5h_iso,
            "resetTimeLocal": local_reset_5h,
            "unavailable": session_bucket["unavailable"],
            "isLive": is_live,
        },
        "claude5h": {
            "name": "Claude Session Tier",
            "fraction": 1.0,
            "countdown": "Anthropic Live API" if is_live else "Local Cache",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": weekly_bucket["name"],
            "fraction": fraction_7d,
            "countdown": countdown_7d,
            "resetTime": resets_at_7d_iso,
            "resetTimeLocal": local_reset_7d,
            "unavailable": weekly_bucket["unavailable"],
        },
        "claudeWeekly": {
            "name": "Anthropic Rate Limit Scope",
            "fraction": 1.0,
            "countdown": "Normal Severity",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "Anthropic Model Roster (Claude 3.7 Sonnet / Opus 3.5)",
            "fraction": 1.0,
            "countdown": "Sẵn sàng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
            "tags": True,
        },
    }


def normalize_codex_account(api_data: dict | None, auth_data: dict | None) -> dict:
    """Normalize OpenAI Codex tier, priority (98/96/95/92/35), JWT claims, models, and AccountMeta."""
    api = api_data if isinstance(api_data, dict) else {}
    auth = auth_data if isinstance(auth_data, dict) else {}
    tokens = auth.get("tokens") if isinstance(auth.get("tokens"), dict) else {}

    id_claims = _decode_jwt_claims_unverified(tokens.get("id_token"))
    acc_claims = _decode_jwt_claims_unverified(tokens.get("access_token"))

    id_auth_ns = (
        id_claims.get("https://api.openai.com/auth")
        if isinstance(id_claims.get("https://api.openai.com/auth"), dict)
        else {}
    )
    acc_auth_ns = (
        acc_claims.get("https://api.openai.com/auth")
        if isinstance(acc_claims.get("https://api.openai.com/auth"), dict)
        else {}
    )
    id_prof_ns = (
        id_claims.get("https://api.openai.com/profile")
        if isinstance(id_claims.get("https://api.openai.com/profile"), dict)
        else {}
    )
    acc_prof_ns = (
        acc_claims.get("https://api.openai.com/profile")
        if isinstance(acc_claims.get("https://api.openai.com/profile"), dict)
        else {}
    )

    auth_mode = str(auth.get("auth_mode") or "").strip().lower()
    has_api_key = bool(auth.get("OPENAI_API_KEY")) and not tokens.get("access_token") and not tokens.get("id_token")

    raw_plan = str(
        api.get("plan_type")
        or id_auth_ns.get("chatgpt_plan_type")
        or acc_auth_ns.get("chatgpt_plan_type")
        or ""
    ).strip().lower()
    if not raw_plan and (auth_mode in ("apikey", "api_key", "api") or has_api_key):
        raw_plan = "apikey"

    if raw_plan == "pro":
        plan_label, plan_type, priority = "CHATGPT PRO", "pro", 98
    elif raw_plan == "enterprise":
        plan_label, plan_type, priority = "CHATGPT ENTERPRISE", "enterprise", 98
    elif raw_plan in ("team", "business"):
        plan_label, plan_type, priority = "CHATGPT TEAM", "team", 96
    elif raw_plan == "edu":
        plan_label, plan_type, priority = "CHATGPT EDU", "edu", 96
    elif raw_plan in ("apikey", "api_key", "api"):
        plan_label, plan_type, priority = "OPENAI API", "apikey", 92
    elif raw_plan == "free":
        plan_label, plan_type, priority = "CHATGPT FREE", "free", 35
    else:
        plan_label, plan_type, priority = "CHATGPT PLUS", "plus", 95

    resolved_email = ""
    for candidate in (
        api.get("email"),
        id_claims.get("email"),
        id_prof_ns.get("email"),
        acc_claims.get("email"),
        acc_prof_ns.get("email"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            resolved_email = candidate.strip()
            break
    if not resolved_email:
        resolved_email = f"OpenAI Codex ({plan_label})"

    model_usage = api.get("model_usage")
    available_models: list[str] = []
    if isinstance(model_usage, dict):
        available_models = [
            str(m)
            for m, info in model_usage.items()
            if isinstance(info, dict) and info.get("available")
        ]

    credits_obj = api.get("rate_limit_reset_credits")
    credits_count = (
        int(credits_obj.get("available_count", 0) or 0)
        if isinstance(credits_obj, dict)
        else 0
    )
    credits_summary = (
        f"{credits_count} reset credits available" if credits_count > 0 else ""
    )

    org_name = ""
    for ns in (id_auth_ns, acc_auth_ns):
        orgs = ns.get("organizations")
        if isinstance(orgs, list) and orgs and isinstance(orgs[0], dict):
            title = str(orgs[0].get("title") or "").strip()
            if title:
                org_name = title
                break

    auth_source = (
        "apikey"
        if plan_type == "apikey"
        else (
            "wham_live"
            if api
            else ("codex_jwt" if (id_claims or acc_claims) else "codex_local")
        )
    )
    account_meta: dict[str, object] = {
        "provider": "codex",
        "vendorLabel": "OPENAI",
        "planType": plan_type,
        "planLabel": plan_label,
        "authSource": auth_source,
        "cliCommand": "codex",
        "configPath": "~/.codex/auth.json",
        "secondaryPath": "~/.codex/logs_2.sqlite",
        "resetCredits": credits_count,
    }
    if org_name:
        account_meta["organizationName"] = org_name
    if credits_summary:
        account_meta["creditsSummary"] = credits_summary

    return {
        "email": resolved_email,
        "tier": plan_label,
        "planLabel": plan_label,
        "vendorLabel": "OPENAI",
        "priority": priority,
        "availableModels": available_models,
        "resetCredits": credits_count,
        "accountMeta": account_meta,
    }


def fetch_codex_quota() -> dict:
    # 1. Primary: Query real-time Plan limits from OpenAI backend API
    auth_json_path = Path(REAL_HOME) / ".codex" / "auth.json"
    auth_data: dict = {}
    if auth_json_path.is_file():
        try:
            with open(auth_json_path, "r", encoding="utf-8") as f:
                loaded_auth = json.load(f)
            if isinstance(loaded_auth, dict):
                auth_data = loaded_auth
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to read ~/.codex/auth.json: {e}\n")

    if auth_data:
        try:
            tokens = auth_data.get("tokens", {}) if isinstance(auth_data.get("tokens"), dict) else {}
            token = tokens.get("access_token")
            account_id = tokens.get("account_id")

            if token:
                headers = {
                    "Authorization": f"Bearer {token}",
                    "User-Agent": "codex/0.167.0",
                    "Accept": "application/json",
                }
                if account_id:
                    headers["ChatGPT-Account-ID"] = account_id

                req = urllib.request.Request("https://chatgpt.com/backend-api/wham/usage", headers=headers)
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    api_data = json.loads(resp.read().decode())

                rl = api_data.get("rate_limit", {})
                pw = rl.get("primary_window", {})
                sw = rl.get("secondary_window", {})

                p_used = pw.get("used_percent", 0)
                p_rem_sec = pw.get("reset_after_seconds", 0)
                p_reset_ts = pw.get("reset_at", 0)

                s_used = sw.get("used_percent", 0)
                s_rem_sec = sw.get("reset_after_seconds", 0)
                s_reset_ts = sw.get("reset_at", 0)

                norm_codex = normalize_codex_account(api_data, auth_data)
                credits_count = norm_codex["resetCredits"]

                fraction_5h = max(0.0, min(1.0, (100.0 - float(p_used)) / 100.0))
                fraction_7d = max(0.0, min(1.0, (100.0 - float(s_used)) / 100.0))

                dt_5h = datetime.datetime.fromtimestamp(p_reset_ts) if p_reset_ts else None
                local_reset_5h = dt_5h.strftime("%H:%M:%S") if dt_5h else ""
                iso_reset_5h = dt_5h.astimezone(datetime.timezone.utc).isoformat() if dt_5h else ""

                dt_7d = datetime.datetime.fromtimestamp(s_reset_ts) if s_reset_ts else None
                local_reset_7d = dt_7d.strftime("%d/%m %H:%M") if dt_7d else ""
                iso_reset_7d = dt_7d.astimezone(datetime.timezone.utc).isoformat() if dt_7d else ""

                countdown_5h = f"⏱ {p_rem_sec // 3600}h {(p_rem_sec % 3600) // 60}m ({local_reset_5h})" if p_rem_sec > 0 else "⏱ 5h 00m (Reset xong)"
                countdown_7d = f"⏱ {s_rem_sec // 86400}d {(s_rem_sec % 86400) // 3600}h ({local_reset_7d})" if s_rem_sec > 0 else "⏱ 7d 00h (Reset xong)"

                is_active, _, _, _ = is_codex_5h_active(rl)
                status = "ACTIVE" if rl.get("allowed", True) else "EXHAUSTED"

                # Save to hashed SQLite session store
                save_session_record("codex", p_reset_ts, s_reset_ts, fraction_5h, is_active)

                roster_label = (
                    f"OpenAI Model Roster ({', '.join(norm_codex['availableModels'][:3])})"
                    if norm_codex["availableModels"]
                    else "OpenAI Model Roster (gpt-4.5 / o3-mini)"
                )
                return {
                    "profile": "codex",
                    "displayName": "OpenAI Codex",
                    "isProvider": True,
                    "providerType": "codex",
                    "tier": norm_codex["tier"],
                    "planLabel": norm_codex["planLabel"],
                    "vendorLabel": norm_codex["vendorLabel"],
                    "priority": norm_codex["priority"],
                    "email": norm_codex["email"],
                    "status": status,
                    "isSessionActive": is_active,
                    "resetTime": iso_reset_5h,
                    "resetTimeLocal": local_reset_5h,
                    "remainingCountdown": countdown_5h,
                    "hasArgon": True,
                    "resetCredits": credits_count,
                    "availableModels": norm_codex["availableModels"],
                    "accountMeta": norm_codex["accountMeta"],
                    "gemini5h": {
                        "name": "Codex 5-Hour Limit",
                        "fraction": fraction_5h,
                        "countdown": countdown_5h,
                        "resetTime": iso_reset_5h,
                        "resetTimeLocal": local_reset_5h,
                        "unavailable": False,
                    },
                    "claude5h": {
                        "name": "Codex Reasoning Effort",
                        "fraction": 1.0,
                        "countdown": "Low / Med / High",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                    },
                    "geminiWeekly": {
                        "name": "Codex Weekly Limit",
                        "fraction": fraction_7d,
                        "countdown": countdown_7d,
                        "resetTime": iso_reset_7d,
                        "resetTimeLocal": local_reset_7d,
                        "unavailable": False,
                    },
                    "claudeWeekly": {
                        "name": "OpenAI Reset Credits",
                        "fraction": 1.0,
                        "countdown": f"{credits_count} Available",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                    },
                    "argonWeekly": {
                        "name": roster_label,
                        "fraction": 1.0,
                        "countdown": "Sẵn sàng",
                        "resetTime": "",
                        "resetTimeLocal": "",
                        "unavailable": False,
                        "tags": True,
                    },
                }
        except Exception as e:
            sys.stderr.write(f"Warning: Failed to fetch online OpenAI Codex quota: {e}\n")

    # 2. Fallback: local logs_2.sqlite
    sqlite_path = Path(REAL_HOME) / ".codex" / "logs_2.sqlite"
    max_ts = 0
    if sqlite_path.is_file():
        try:
            con = sqlite3.connect(str(sqlite_path), timeout=3.0)
            cur = con.cursor()
            cur.execute("SELECT max(ts) FROM logs;")
            row = cur.fetchone()
            con.close()
            if row and row[0]:
                max_ts = row[0]
        except Exception as e:
            sys.stderr.write(f"Error reading codex logs_2.sqlite: {e}\n")

    now_ts = int(time.time())
    delta_sec = now_ts - max_ts if max_ts > 0 else 999999
    window_sec = 5 * 3600

    if delta_sec < window_sec:
        rem_sec = window_sec - delta_sec
        reset_ts = max_ts + window_sec
        local_reset_5h = datetime.datetime.fromtimestamp(reset_ts).strftime("%H:%M:%S")
        reset_iso = datetime.datetime.fromtimestamp(reset_ts, tz=datetime.timezone.utc).isoformat()
        fraction_5h = rem_sec / window_sec
        countdown_5h = f"⏱ {rem_sec // 3600}h {(rem_sec % 3600) // 60}m ({local_reset_5h})"
        is_active = True
        status = "ACTIVE"
    else:
        rem_sec = 0
        reset_ts = now_ts
        local_reset_5h = "Reset xong"
        reset_iso = ""
        fraction_5h = 1.0
        countdown_5h = "⏱ 5h 00m (Reset xong)"
        is_active = False
        status = "IDLE"

    # Save to hashed SQLite session store
    save_session_record("codex", reset_ts, 0, fraction_5h, is_active)

    norm_offline = normalize_codex_account(None, auth_data)

    return {
        "profile": "codex",
        "displayName": "OpenAI Codex",
        "isProvider": True,
        "providerType": "codex",
        "tier": norm_offline["tier"],
        "planLabel": norm_offline["planLabel"],
        "vendorLabel": norm_offline["vendorLabel"],
        "priority": norm_offline["priority"],
        "email": norm_offline["email"],
        "status": status,
        "isSessionActive": is_active,
        "resetTime": reset_iso,
        "resetTimeLocal": local_reset_5h,
        "remainingCountdown": countdown_5h,
        "hasArgon": True,
        "availableModels": norm_offline["availableModels"],
        "accountMeta": norm_offline["accountMeta"],
        "gemini5h": {
            "name": "Codex 5H Rolling Session",
            "fraction": fraction_5h,
            "countdown": countdown_5h,
            "resetTime": reset_iso,
            "resetTimeLocal": local_reset_5h,
            "unavailable": False,
        },
        "claude5h": {
            "name": "Codex Reasoning Effort",
            "fraction": 1.0,
            "countdown": "Low / Med / High",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "geminiWeekly": {
            "name": "OpenAI Weekly Limit (Chỉ trượt 5H Session)",
            "fraction": 1.0,
            "countdown": "Không áp dụng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "claudeWeekly": {
            "name": "OpenAI Auth Session",
            "fraction": 1.0,
            "countdown": "OAuth Active",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
        },
        "argonWeekly": {
            "name": "OpenAI Model Roster (gpt-4.5 / o3-mini)",
            "fraction": 1.0,
            "countdown": "Sẵn sàng",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": False,
            "tags": True,
        },
    }


def get_kiro_bin_path() -> str | None:
    candidate = shutil.which("kiro-cli") or shutil.which("kiro")
    if candidate and os.path.isfile(candidate):
        return candidate
    local_bin = os.path.join(REAL_HOME, ".local", "bin", "kiro-cli")
    if os.path.isfile(local_bin):
        return local_bin
    return None


def parse_kiro_whoami_email(output: str) -> str | None:
    if not output or "not logged in" in output.lower():
        return None
    m = re.search(r"Email:\s*([^\s\r\n]+)", output)
    if m:
        return m.group(1).strip()
    return None


def normalize_kiro_account(
    api_data: dict | None,
    email: str = "",
    cached_entry: dict | None = None,
    whoami_auth: str = "",
) -> dict:
    """Normalize Kiro tier, priority (94/92/90/30), credits summary, and offline cache fallback."""
    cached = cached_entry if isinstance(cached_entry, dict) else {}
    api = api_data if isinstance(api_data, dict) else {}

    if api:
        sub_info = (
            api.get("subscriptionInfo")
            if isinstance(api.get("subscriptionInfo"), dict)
            else {}
        )
        raw_title = str(sub_info.get("subscriptionTitle") or "").strip()
        sub_type = str(sub_info.get("type") or "").strip()
        overage_cfg = (
            api.get("overageConfiguration")
            if isinstance(api.get("overageConfiguration"), dict)
            else {}
        )
        overage_status = str(overage_cfg.get("overageStatus") or "DISABLED").strip()

        used = 0.0
        limit = 1000.0
        has_explicit_limit = False
        overage_rate_summary = ""
        bonuses_count = 0
        bonus_credits = 0.0
        breakdowns = api.get("usageBreakdownList")
        if isinstance(breakdowns, list) and breakdowns:
            b0 = breakdowns[0] if isinstance(breakdowns[0], dict) else {}
            used = float(
                b0.get("currentUsageWithPrecision", b0.get("currentUsage", 0.0)) or 0.0
            )
            if "usageLimitWithPrecision" in b0 or "usageLimit" in b0:
                limit = float(
                    b0.get("usageLimitWithPrecision", b0.get("usageLimit", 1000.0))
                    or 0.0
                )
                has_explicit_limit = True
            ov_cap = b0.get("overageCap")
            ov_rate = b0.get("overageRate") or overage_cfg.get("overageRate")
            currency = str(b0.get("currency") or "USD")
            if ov_rate is not None:
                overage_rate_summary = f"{ov_rate} {currency}/credit" + (
                    f" (cap {ov_cap})" if ov_cap else ""
                )
            bonuses = b0.get("bonuses")
            if isinstance(bonuses, list):
                bonuses_count = len(bonuses)
                for bon in bonuses:
                    if isinstance(bon, dict):
                        bonus_credits += float(bon.get("usageLimit", 0.0) or 0.0)

        title_up = raw_title.upper()
        type_up = sub_type.upper()
        if (
            "POWER" in title_up
            or "POWER" in type_up
            or (has_explicit_limit and limit >= 10000)
        ):
            plan_label = title_up or "KIRO POWER"
            plan_type, priority = "power", 94
        elif (
            "PRO+" in title_up
            or "PRO_PLUS" in title_up
            or "PRO_PLUS" in type_up
            or "PROPLUS" in type_up
            or (has_explicit_limit and limit >= 2000)
        ):
            plan_label = "KIRO PRO+" if title_up in ("", "KIRO PRO_PLUS") else title_up
            plan_type, priority = "pro_plus", 92
        elif (
            "FREE" in title_up
            or "FREE" in type_up
            or (has_explicit_limit and 0 < limit <= 100)
        ):
            plan_label = title_up or "KIRO FREE"
            plan_type, priority = "free", 30
        elif "STUDENT" in title_up or "STUDENT" in type_up:
            plan_label = title_up or "KIRO STUDENT"
            plan_type, priority = "student", 90
        else:
            plan_label = title_up or ("KIRO PRO" if has_explicit_limit else "KIRO STUDENT")
            plan_type = "pro" if "PRO" in plan_label else "student"
            priority = 90

        credits_summary = f"Used: {used:,.2f} / {limit:,.1f} credits"
        if bonus_credits > 0:
            credits_summary += f" (+{bonus_credits:,.0f} bonus)"
        elif bonuses_count > 0:
            credits_summary += f" ({bonuses_count} bonus)"

        resolved_email = (email or "").strip() or "Kiro CLI User"
        auth_source = whoami_auth.strip() or ("builder_id" if email else "kiro_cli")
        account_meta: dict[str, object] = {
            "provider": "kiro",
            "vendorLabel": "KIRO",
            "planType": plan_type,
            "planLabel": plan_label,
            "authSource": auth_source,
            "cliCommand": "kiro-cli",
            "configPath": "~/.local/share/kiro-cli",
            "creditsSummary": credits_summary,
            "overageStatus": overage_status,
        }
        if sub_type:
            account_meta["rateLimitTier"] = sub_type
        if overage_rate_summary:
            account_meta["overageRateSummary"] = overage_rate_summary

        return {
            "email": resolved_email,
            "tier": plan_label,
            "planLabel": plan_label,
            "vendorLabel": "KIRO",
            "priority": priority,
            "used": used,
            "limit": limit,
            "overageStatus": overage_status,
            "availableModels": ["auto (1.0x)", "claude-sonnet-4.5", "claude-haiku-4.5"],
            "accountMeta": account_meta,
        }

    # Offline / transient fallback: preserve cached metadata when available
    cached_tier = str(cached.get("tier") or "").strip()
    plan_label = str(cached.get("planLabel") or cached_tier or "KIRO").strip()
    tier = cached_tier or plan_label
    lbl_up = plan_label.upper()
    if isinstance(cached.get("priority"), (int, float)):
        priority = int(cached["priority"])
    elif "POWER" in lbl_up:
        priority = 94
    elif "PRO+" in lbl_up or "PRO_PLUS" in lbl_up:
        priority = 92
    elif "FREE" in lbl_up:
        priority = 30
    else:
        priority = 90

    cached_email = str(cached.get("email") or "").strip()
    if cached_email and (
        "Chưa đăng nhập" in cached_email or "Not Installed" in cached_email
    ):
        cached_email = ""
    resolved_email = (email or "").strip() or cached_email or "Kiro CLI User"

    cached_cp = (
        dict(cached["creditsPool"])
        if isinstance(cached.get("creditsPool"), dict)
        else None
    )
    cached_meta = (
        dict(cached["accountMeta"])
        if isinstance(cached.get("accountMeta"), dict)
        else {}
    )
    overage_status = str(
        cached.get("overageStatus") or cached_meta.get("overageStatus") or "DISABLED"
    )
    if not cached_meta:
        plan_type = (
            "power"
            if priority == 94
            else (
                "pro_plus"
                if priority == 92
                else ("free" if priority == 30 else ("student" if "STUDENT" in lbl_up else "pro"))
            )
        )
        cached_meta = {
            "provider": "kiro",
            "vendorLabel": "KIRO",
            "planType": plan_type,
            "planLabel": plan_label,
            "authSource": whoami_auth.strip() or "cached",
            "cliCommand": "kiro-cli",
            "configPath": "~/.local/share/kiro-cli",
            "overageStatus": overage_status,
        }
        if cached_cp:
            cached_meta["creditsSummary"] = (
                f"Used: {float(cached_cp.get('used', 0.0)):,.2f} / "
                f"{float(cached_cp.get('limit', 1000.0)):,.1f} credits"
            )

    return {
        "email": resolved_email,
        "tier": tier,
        "planLabel": plan_label,
        "vendorLabel": "KIRO",
        "priority": priority,
        "creditsPool": cached_cp,
        "overageStatus": overage_status,
        "availableModels": list(
            cached.get("availableModels")
            or ["auto (1.0x)", "claude-sonnet-4.5", "claude-haiku-4.5"]
        ),
        "accountMeta": cached_meta,
    }


def parse_kiro_usage_limits(
    api_data: dict, email: str = "", whoami_auth: str = ""
) -> dict:
    norm_kiro = normalize_kiro_account(api_data, email=email, whoami_auth=whoami_auth)
    tier = norm_kiro["tier"]
    overage_status = norm_kiro["overageStatus"]
    used = float(norm_kiro["used"])
    limit = float(norm_kiro["limit"])

    remaining = max(0.0, limit - used)
    fraction = max(0.0, min(1.0, remaining / limit)) if limit > 0 else 0.0

    next_date_reset = float(api_data.get("nextDateReset", 0.0))
    now_ts = time.time()
    reset_iso = ""
    local_reset = ""
    countdown = "⏱ Hết hạn"

    if next_date_reset > 0:
        dt_reset = datetime.datetime.fromtimestamp(next_date_reset, tz=datetime.timezone.utc)
        reset_iso = dt_reset.isoformat()
        local_reset = dt_reset.astimezone().strftime("%d/%m")
        rem_sec = max(0, int(next_date_reset - now_ts))
        days = rem_sec // 86400
        hours = (rem_sec % 86400) // 3600
        countdown = f"⏱ {days}d {hours:02d}h ({local_reset})"

    status = "ACTIVE"
    if fraction <= 0.0 and overage_status == "DISABLED":
        status = "EXHAUSTED"

    # Save to hashed SQLite session store
    save_session_record("kiro", int(next_date_reset), int(next_date_reset), fraction, True)

    return {
        "profile": "kiro",
        "displayName": "Kiro CLI",
        "isProvider": True,
        "providerType": "kiro",
        "tier": tier,
        "planLabel": norm_kiro["planLabel"],
        "vendorLabel": norm_kiro["vendorLabel"],
        "priority": norm_kiro["priority"],
        "email": norm_kiro["email"],
        "status": status,
        "success": True,
        "isSessionActive": True,
        "resetTime": reset_iso,
        "resetTimeLocal": local_reset,
        "remainingCountdown": countdown,
        "hasArgon": False,
        "isCreditOnly": True,
        "availableModels": norm_kiro["availableModels"],
        "accountMeta": norm_kiro["accountMeta"],
        "creditsPool": {
            "name": "Monthly Credits Pool",
            "used": round(used, 2),
            "limit": round(limit, 2),
            "remaining": round(remaining, 2),
            "fraction": fraction,
            "countdown": countdown,
            "resetDate": local_reset,
            "unavailable": False,
        },
        "gemini5h": {
            "name": "Monthly Credits Pool",
            "fraction": fraction,
            "countdown": countdown,
            "resetTime": reset_iso,
            "resetTimeLocal": local_reset,
            "unavailable": False,
        },
        "claude5h": None,
        "geminiWeekly": None,
        "overageStatus": overage_status,
        "defaultModel": "auto (1.0x)",
    }


def fetch_kiro_quota() -> dict:
    kiro_bin = get_kiro_bin_path()
    if not kiro_bin:
        return {
            "profile": "kiro",
            "displayName": "Kiro CLI",
            "isProvider": True,
            "providerType": "kiro",
            "tier": "KIRO",
            "priority": 90,
            "email": "Kiro CLI (Not Installed)",
            "status": "UNAVAILABLE",
            "success": False,
            "isSessionActive": False,
            "resetTime": "",
            "resetTimeLocal": "",
            "remainingCountdown": "Unavailable",
            "hasArgon": False,
            "isCreditOnly": True,
            "gemini5h": {
                "name": "Monthly Credits Pool",
                "fraction": 0.0,
                "countdown": "N/A",
                "resetTime": "",
                "resetTimeLocal": "",
                "unavailable": True,
            },
        }

    env = {
        "HOME": REAL_HOME,
        "PATH": f"{REAL_HOME}/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin",
    }

    # 1. Check whoami
    email = ""
    whoami_auth = ""
    try:
        whoami_proc = subprocess.run([kiro_bin, "whoami"], env=env, capture_output=True, text=True, timeout=3.0)
        whoami_out = whoami_proc.stdout or ""
        email = parse_kiro_whoami_email(whoami_out) or ""
        if "builder id" in whoami_out.lower():
            whoami_auth = "builder_id"
        elif "iam" in whoami_out.lower() or "sso" in whoami_out.lower():
            whoami_auth = "iam_sso"
        if whoami_proc.returncode != 0 or not email:
            return {
                "profile": "kiro",
                "displayName": "Kiro CLI",
                "isProvider": True,
                "providerType": "kiro",
                "tier": "KIRO",
                "vendorLabel": "KIRO",
                "priority": 90,
                "email": "Chưa đăng nhập (Run 'kiro-cli login')",
                "status": "NOT LOGGED IN",
                "success": False,
                "isSessionActive": False,
                "resetTime": "",
                "resetTimeLocal": "",
                "remainingCountdown": "Chưa đăng nhập",
                "hasArgon": False,
                "isCreditOnly": True,
                "gemini5h": {
                    "name": "Monthly Credits Pool",
                    "fraction": 0.0,
                    "countdown": "Chưa đăng nhập",
                    "resetTime": "",
                    "resetTimeLocal": "",
                    "unavailable": True,
                },
            }
    except Exception as e:
        sys.stderr.write(f"Warning: kiro-cli whoami error: {e}\n")

    # 2. Query GetUsageLimits via KAS token
    try:
        kas_proc = subprocess.run([kiro_bin, "chat", "_", "get-kas-token"], env=env, capture_output=True, text=True, timeout=4.0)
        if kas_proc.returncode == 0 and kas_proc.stdout:
            kas_json = json.loads(kas_proc.stdout)
            kas_data = kas_json.get("data", {})
            token = kas_data.get("accessToken")
            profile_arn = kas_data.get("profileArn")

            if token and profile_arn:
                req = urllib.request.Request(
                    "https://q.us-east-1.amazonaws.com",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/x-amz-json-1.0",
                        "x-amz-target": "AmazonCodeWhispererService.GetUsageLimits",
                        "User-Agent": "kiro-cli/3.1.0",
                    },
                    data=json.dumps({"profileArn": profile_arn}).encode("utf-8"),
                )
                with urllib.request.urlopen(req, timeout=4.0) as resp:
                    api_data = json.loads(resp.read().decode("utf-8"))
                    return parse_kiro_usage_limits(api_data, email=email, whoami_auth=whoami_auth)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to fetch online Kiro quota: {e}\n")

    # 3. Fallback: session store + HTML cached snapshot
    cached_profile = _peek_cached_profile("kiro")
    norm_kiro = normalize_kiro_account(
        None, email=email, cached_entry=cached_profile, whoami_auth=whoami_auth
    )
    cached = get_session_record("kiro")
    cached_cp = norm_kiro.get("creditsPool")
    if cached or isinstance(cached_cp, dict):
        fraction = (
            float(cached_cp["fraction"])
            if isinstance(cached_cp, dict) and "fraction" in cached_cp
            else float((cached or {}).get("fraction_5h", 1.0))
        )
        reset_ts = int((cached or {}).get("reset_5h", 0))
        now_ts = time.time()
        rem_sec = max(0, int(reset_ts - now_ts))
        days = rem_sec // 86400
        hours = (rem_sec % 86400) // 3600
        local_date = (
            datetime.datetime.fromtimestamp(reset_ts).strftime("%d/%m")
            if reset_ts > 0
            else str((cached_cp or {}).get("resetDate") or "")
        )
        countdown = (
            f"⏱ {days}d {hours:02d}h ({local_date})"
            if reset_ts > 0
            else str((cached_cp or {}).get("countdown") or "⏱ Cached")
        )
        cp_limit = float((cached_cp or {}).get("limit", 1000.0) or 1000.0)
        cp_used = float(
            (cached_cp or {}).get("used", round(max(0.0, cp_limit * (1.0 - fraction)), 2))
        )
        cp_rem = float(
            (cached_cp or {}).get("remaining", round(max(0.0, cp_limit - cp_used), 2))
        )
        return {
            "profile": "kiro",
            "displayName": "Kiro CLI",
            "isProvider": True,
            "providerType": "kiro",
            "tier": norm_kiro["tier"],
            "planLabel": norm_kiro["planLabel"],
            "vendorLabel": norm_kiro["vendorLabel"],
            "priority": norm_kiro["priority"],
            "email": norm_kiro["email"],
            "status": "ACTIVE (Cached)",
            "success": True,
            "isSessionActive": True,
            "resetTime": "",
            "resetTimeLocal": local_date,
            "remainingCountdown": countdown,
            "hasArgon": False,
            "isCreditOnly": True,
            "overageStatus": norm_kiro["overageStatus"],
            "availableModels": norm_kiro["availableModels"],
            "accountMeta": norm_kiro["accountMeta"],
            "creditsPool": {
                "name": "Monthly Credits Pool",
                "used": round(cp_used, 2),
                "limit": round(cp_limit, 2),
                "remaining": round(cp_rem, 2),
                "fraction": fraction,
                "countdown": countdown,
                "resetDate": local_date,
                "unavailable": False,
            },
            "gemini5h": {
                "name": "Monthly Credits Pool",
                "fraction": fraction,
                "countdown": countdown,
                "resetTime": "",
                "resetTimeLocal": local_date,
                "unavailable": False,
            },
        }

    return {
        "profile": "kiro",
        "displayName": "Kiro CLI",
        "isProvider": True,
        "providerType": "kiro",
        "tier": norm_kiro["tier"],
        "planLabel": norm_kiro["planLabel"],
        "vendorLabel": norm_kiro["vendorLabel"],
        "priority": norm_kiro["priority"],
        "email": norm_kiro["email"],
        "status": "IDLE",
        "success": False,
        "isSessionActive": False,
        "resetTime": "",
        "resetTimeLocal": "",
        "remainingCountdown": "Unknown",
        "hasArgon": False,
        "isCreditOnly": True,
        "availableModels": norm_kiro["availableModels"],
        "accountMeta": norm_kiro["accountMeta"],
        "gemini5h": {
            "name": "Monthly Credits Pool",
            "fraction": 0.0,
            "countdown": "N/A",
            "resetTime": "",
            "resetTimeLocal": "",
            "unavailable": True,
        },
    }


_TERMINAL_ESCAPE_RE = re.compile(r"\x1b(?:\[[0-9;?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[@-Z\\-_])")
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]+")


def _sanitize_terminal_text(value: object) -> str:
    """Strip ANSI escape sequences and control characters before terminal output."""
    if value is None:
        return ""
    cleaned = _TERMINAL_ESCAPE_RE.sub("", str(value))
    cleaned = _CONTROL_CHARS_RE.sub(" ", cleaned)
    return " ".join(cleaned.split())


def _extract_claude_bucket_render_args(bucket: dict) -> tuple[str, str, float, bool, str]:
    """Normalize a Claude bucket dict into sanitized render_card inputs and share label."""
    title = _sanitize_terminal_text(bucket.get("name") or bucket.get("scopeLabel") or "Claude Quota") or "Claude Quota"
    countdown = _sanitize_terminal_text(bucket.get("countdown") or "")
    raw_fraction = bucket.get("fraction", 1.0)
    try:
        fraction = max(0.0, min(1.0, float(1.0 if raw_fraction is None else raw_fraction)))
    except (TypeError, ValueError):
        fraction = 1.0
    available = not bool(bucket.get("unavailable", False))
    share = bucket.get("shareInfo") if isinstance(bucket.get("shareInfo"), dict) else {}
    share_label = _sanitize_terminal_text(share.get("label") or "")
    return title, countdown, fraction, available, share_label


def print_claude_card(data: dict):
    tier = _sanitize_terminal_text(data.get("tier", "ANTHROPIC")) or "ANTHROPIC"
    email = _sanitize_terminal_text(data.get("email", ""))
    status = _sanitize_terminal_text(data.get("status", "ACTIVE")) or "ACTIVE"
    g5h = data.get("gemini5h") if isinstance(data.get("gemini5h"), dict) else {}
    g7d = data.get("geminiWeekly") if isinstance(data.get("geminiWeekly"), dict) else {}
    raw_buckets = data.get("quotaBuckets")
    buckets = [b for b in raw_buckets if isinstance(b, dict)] if isinstance(raw_buckets, list) else []
    if not buckets:
        buckets = [b for b in (g5h, g7d) if b] or [g5h, g7d]
    is_live = bool(g5h.get("isLive", False) or any(bool(b.get("isLive", False)) for b in buckets))

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status in ("NEED_LOGIN", "AUTH NEEDED"):
        status_tag = "\033[38;2;245;158;11m🔑 NEED LOGIN\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;194;65;12m\033[1;38;2;254;215;170m ✺ {tier} \033[0m"
    tag_priority = format_priority_tag(data.get("priority", 100))
    api_source_tag = "\033[38;2;56;189;248m[Live API]\033[0m" if is_live else "\033[38;2;156;163;175m[Local Cache]\033[0m"

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;251;146;60m✺ Claude Code{RESET}  {tier_tag}  {tag_priority}  {api_source_tag}  {status_tag}")
    if email:
        print(f"  {DIM}Account: {email}{RESET}")

    claude_orange = "\033[38;2;251;146;60m"
    for idx in range(0, len(buckets), 2):
        title1, cd1, frac1, avail1, share1 = _extract_claude_bucket_render_args(buckets[idx])
        if idx + 1 < len(buckets):
            title2, cd2, frac2, avail2, share2 = _extract_claude_bucket_render_args(buckets[idx + 1])
            c1 = render_card("✺", claude_orange, title1, cd1, frac1, width=45, available=avail1)
            c2 = render_card("✺", claude_orange, title2, cd2, frac2, width=45, available=avail2)
            for l1, l2 in zip(c1, c2):
                print(l1 + "  " + l2)
            row_shares = [(t, s) for t, s in ((title1, share1), (title2, share2)) if s]
        else:
            c1 = render_card("✺", claude_orange, title1, cd1, frac1, width=92, available=avail1)
            for line in c1:
                print(line)
            row_shares = [(title1, share1)] if share1 else []
        for title, share_label in row_shares:
            print(f"  {DIM}↳ {title}: {share_label}{RESET}")

    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh claude{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Đăng nhập CLI\033[0m : {DIM}claude auth login{RESET}\n")


def print_codex_card(data: dict):
    tier = data.get("tier", "OPENAI")
    email = data.get("email", "")
    status = data.get("status", "ACTIVE")
    g5h = data.get("gemini5h", {})
    g7d = data.get("geminiWeekly", {})
    frac_5h = g5h.get("fraction", 1.0)
    frac_7d = g7d.get("fraction", 1.0)
    cd_5h = g5h.get("countdown", "")
    cd_7d = g7d.get("countdown", "")

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status in ("NEED_LOGIN", "AUTH NEEDED"):
        status_tag = f"\033[38;2;245;158;11m🔑 NEED LOGIN\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;16;185;129m\033[1;38;2;209;250;229m 🟢 {tier} \033[0m"
    tag_priority = format_priority_tag(data.get("priority", 95))

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;52;211;153m🟢 OpenAI Codex{RESET}  {tier_tag}  {tag_priority}  {status_tag}")
    if email:
        print(f"  {DIM}Account: {email}{RESET}")

    c1 = render_card("✦", "\033[38;2;52;211;153m", "Codex 5-Hour Limit", cd_5h, frac_5h, width=45)
    c2 = render_card("✦", "\033[38;2;52;211;153m", "Codex Weekly Limit", cd_7d, frac_7d, width=45)
    for l1, l2 in zip(c1, c2):
        print(l1 + "  " + l2)

    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh codex{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Đăng nhập CLI\033[0m : {DIM}codex auth login{RESET}\n")


def print_kiro_card(data: dict):
    tier = data.get("tier", "KIRO")
    email = data.get("email", "")
    status = data.get("status", "ACTIVE")
    cp = data.get("creditsPool", {})
    used = cp.get("used", 0.0)
    limit = cp.get("limit", 1000.0)
    remaining = cp.get("remaining", limit - used)
    fraction = cp.get("fraction", 1.0)
    pct = fraction * 100.0
    countdown = cp.get("countdown", "")

    if status == "ACTIVE":
        status_tag = f"\033[38;2;114;188;130m🟢 {status}\033[0m"
    elif status == "NOT LOGGED IN":
        status_tag = f"\033[38;2;245;158;11m🔑 {status}\033[0m"
    else:
        status_tag = f"\033[38;2;239;68;68m🔴 {status}\033[0m"

    tier_tag = f"\033[48;2;88;28;135m\033[1;38;2;216;180;254m 👻 {tier} \033[0m"
    tag_priority = format_priority_tag(data.get("priority", 90))

    print(f"\n{BOLD}{WHITE}✦ Provider: \033[38;2;192;132;252m👻 Kiro CLI{RESET}  {tier_tag}  {tag_priority}  {status_tag}")
    if email:
        print(f"  {DIM}Email: {email}{RESET}")

    fill_col, track_col = get_color_pair(pct)
    bar_w = 40
    filled = int(round(fraction * bar_w))
    empty = bar_w - filled
    bar_str = f"[{fill_col}{'█' * filled}{RESET}{track_col}{'░' * empty}{RESET}] {fill_col}{pct:5.1f}% remaining{RESET}"

    w = 72
    print(f" ┌{'─' * w}┐")
    print(f" │  {BOLD}Monthly Credits Pool{RESET}{' ' * (w - 22)}│")
    print(f" │  {bar_str}{' ' * max(0, w - str_vis_width(bar_str) - 2)}│")
    sub_text = f"{remaining:,.2f} / {limit:,.1f} credits (Used: {used:,.2f})   {countdown}"
    print(f" │  {DIM}{sub_text}{RESET}{' ' * max(0, w - str_vis_width(sub_text) - 2)}│")
    print(f" ├{'─' * w}┤")
    footer_text = f"Default Model: auto (1.0x)   •   Overages: {data.get('overageStatus', 'Disabled')}"
    print(f" │  {DIM}{footer_text}{RESET}{' ' * max(0, w - str_vis_width(footer_text) - 2)}│")
    print(f" └{'─' * w}┘")
    print(f" {DIM}⚙️  Actions:{RESET}")
    print(f"   \033[38;2;56;189;248m⚡ Refresh nhanh\033[0m : {DIM}check-quota refresh kiro{RESET}")
    print(f"   \033[38;2;114;188;130m🎯 Quản lý account\033[0m: {DIM}kiro-cli whoami{RESET}\n")


def load_cached_profiles() -> dict:
    global CACHED_PROFILES_DATA, CACHED_HTML_MTIME
    p = get_dashboard_html_path()
    disk_mtime = p.stat().st_mtime if p.is_file() else 0.0
    if CACHED_PROFILES_DATA and (
        CACHED_HTML_MTIME == 0.0 or disk_mtime <= 0.0 or disk_mtime == CACHED_HTML_MTIME
    ):
        if "claude" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["claude"] = fetch_claude_quota()
        if "codex" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["codex"] = fetch_codex_quota()
        if "kiro" not in CACHED_PROFILES_DATA:
            CACHED_PROFILES_DATA["kiro"] = fetch_kiro_quota()
        return CACHED_PROFILES_DATA
    if p.is_file():
        try:
            content = p.read_text(encoding="utf-8")
            marker = "const PROFILES_DATA ="
            end_marker = "\n};"
            idx1 = content.find(marker)
            if idx1 != -1:
                idx2 = content.find(end_marker, idx1)
                if idx2 != -1:
                    raw_json = content[idx1 + len(marker):idx2 + len(end_marker)].strip()
                    if raw_json.endswith(";"):
                        raw_json = raw_json[:-1].strip()
                    CACHED_PROFILES_DATA = json.loads(raw_json)
                    CACHED_HTML_MTIME = p.stat().st_mtime
                    allowed_providers = {"claude", "codex", "kiro"}
                    purged_keys = [k for k in list(CACHED_PROFILES_DATA.keys()) if k not in allowed_providers and not is_valid_antigravity_profile(k)]
                    if purged_keys:
                        for k in purged_keys:
                            del CACHED_PROFILES_DATA[k]
                        try:
                            formatted_json = json.dumps(CACHED_PROFILES_DATA, indent=2, ensure_ascii=False)
                            new_content = content[:idx1 + len(marker)] + " " + formatted_json + ";" + content[idx2 + len(end_marker):]
                            p.write_text(new_content, encoding="utf-8")
                            CACHED_HTML_MTIME = p.stat().st_mtime
                            sync_copies = [
                                Path.home() / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                                Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
                            ]
                            for sc in sync_copies:
                                if sc.is_file() and sc != p:
                                    try:
                                        sc.write_text(new_content, encoding="utf-8")
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    if "claude" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["claude"] = fetch_claude_quota()
                    if "codex" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["codex"] = fetch_codex_quota()
                    if "kiro" not in CACHED_PROFILES_DATA:
                        CACHED_PROFILES_DATA["kiro"] = fetch_kiro_quota()
                    return CACHED_PROFILES_DATA
        except Exception as e:
            sys.stderr.write(f"Failed to load cached profiles: {e}\n")
    CACHED_PROFILES_DATA = {
        "claude": fetch_claude_quota(),
        "codex": fetch_codex_quota(),
        "kiro": fetch_kiro_quota(),
    }
    return CACHED_PROFILES_DATA


_ORIG_LOAD_CACHED_PROFILES = load_cached_profiles


def _peek_cached_profile(profile: str) -> dict:
    """Read-only lookup of a single profile's cached entry without external provider side effects."""
    if load_cached_profiles is not _ORIG_LOAD_CACHED_PROFILES:
        data = load_cached_profiles()
        return dict(data.get(profile, {})) if isinstance(data, dict) else {}
    p = get_dashboard_html_path()
    disk_mtime = p.stat().st_mtime if p.is_file() else 0.0
    if (
        CACHED_PROFILES_DATA
        and profile in CACHED_PROFILES_DATA
        and (CACHED_HTML_MTIME == 0.0 or disk_mtime <= 0.0 or disk_mtime == CACHED_HTML_MTIME)
    ):
        entry = CACHED_PROFILES_DATA.get(profile)
        return dict(entry) if isinstance(entry, dict) else {}
    if p.is_file():
        try:
            content = p.read_text(encoding="utf-8")
            marker = "const PROFILES_DATA ="
            end_marker = "\n};"
            idx1 = content.find(marker)
            if idx1 != -1:
                idx2 = content.find(end_marker, idx1)
                if idx2 != -1:
                    raw_json = content[idx1 + len(marker):idx2 + len(end_marker)].strip()
                    if raw_json.endswith(";"):
                        raw_json = raw_json[:-1].strip()
                    parsed = json.loads(raw_json)
                    if isinstance(parsed, dict) and isinstance(parsed.get(profile), dict):
                        return dict(parsed[profile])
        except Exception:
            pass
    return {}


def _preserve_cached_model_meta(target: dict, cached_entry: dict) -> dict:
    """Copy existing model discovery and account metadata onto `DISABLED` / `AUTH NEEDED` payloads."""
    for key in (
        "tier",
        "priority",
        "planLabel",
        "vendorLabel",
        "accountMeta",
        "availableModels",
        "modelCatalog",
        "groupModels",
        "capabilities",
        "modelsFetchedAt",
        "groupDescSig",
    ):
        if key in cached_entry:
            target[key] = cached_entry[key]
    return target


def update_cached_profile(profile: str, data: dict):
    global CACHED_PROFILES_DATA, CACHED_HTML_MTIME
    if not CACHED_PROFILES_DATA:
        load_cached_profiles()
    CACHED_PROFILES_DATA[profile] = data
    try:
        p = get_dashboard_html_path()
        if p.is_file():
            content = p.read_text(encoding="utf-8")
            marker = "const PROFILES_DATA ="
            end_marker = "\n};"
            idx1 = content.find(marker)
            if idx1 != -1:
                idx2 = content.find(end_marker, idx1)
                if idx2 != -1:
                    formatted_json = json.dumps(CACHED_PROFILES_DATA, indent=2, ensure_ascii=False)
                    new_content = content[:idx1 + len(marker)] + " " + formatted_json + ";" + content[idx2 + len(end_marker):]
                    p.write_text(new_content, encoding="utf-8")
                    CACHED_HTML_MTIME = p.stat().st_mtime
                    sync_copies = [
                        Path.home() / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / ".gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/config/plugins/d3nexus/skills/check-quota/resources/dashboard/quota_dashboard.html",
                        Path(REAL_HOME) / "antigravity_homes/huynhminhtien0510/.gemini/antigravity/brain/faba533a-ed61-4a6e-8b53-bfbf7926cccf/quota_dashboard.html",
                    ]
                    for sc in sync_copies:
                        if sc.is_file() and sc != p:
                            try:
                                sc.write_text(new_content, encoding="utf-8")
                            except Exception:
                                pass
    except Exception as e:
        sys.stderr.write(f"Failed to persist updated cache to HTML: {e}\n")


def format_profile_for_dashboard(profile: str, result: dict) -> dict:
    if profile == "claude":
        return fetch_claude_quota()
    if profile == "codex":
        return fetch_codex_quota()
    if profile == "kiro":
        return fetch_kiro_quota()

    current = _peek_cached_profile(profile)
    cached_lic, cached_oauth, cached_cred = _extract_cached_google_license_and_credits(
        current
    )
    res_oauth = result.get("oauthInfo") if isinstance(result.get("oauthInfo"), dict) else {}
    oauth_info = res_oauth or read_antigravity_oauth_record(profile) or cached_oauth
    safe_oauth_info = {
        k: v for k, v in (oauth_info or {}).items() if k in ("email", "auth_method", "expiry")
    }
    res_lic = result.get("licenseInfo") if isinstance(result.get("licenseInfo"), dict) else {}
    explicit_plan_name = str(result.get("plan_name") or "").strip()
    if res_lic:
        license_info = res_lic
    elif explicit_plan_name:
        plan_low = explicit_plan_name.lower()
        if "ultra" in plan_low:
            inferred_tier = "ULTRA"
        elif "free" in plan_low or "starter" in plan_low:
            inferred_tier = "FREE"
        elif "pro" in plan_low or "standard" in plan_low:
            inferred_tier = "PRO"
        else:
            inferred_tier = ""
        license_info = (
            {"tier": inferred_tier, "tierDisplayName": explicit_plan_name}
            if inferred_tier
            else {}
        )
    else:
        license_info = cached_lic
    res_cred = result.get("creditsInfo") if isinstance(result.get("creditsInfo"), dict) else {}
    credits_info = res_cred or cached_cred

    oauth_email = str(safe_oauth_info.get("email") or "").strip()
    vscdb_email = read_antigravity_vscdb_email(profile)
    explicit_email = str(result.get("email") or "").strip()
    cached_email = str(current.get("email") or "").strip()
    synthetic_fallback = f"{profile}@gmail.com"
    email = (
        oauth_email
        or vscdb_email
        or (explicit_email if explicit_email != synthetic_fallback else "")
        or (cached_email if cached_email != synthetic_fallback else "")
        or explicit_email
        or cached_email
        or synthetic_fallback
    )
    tier = current.get("tier", "PRO")
    priority = current.get("priority", 50)
    fallback_norm = normalize_antigravity_account(
        profile,
        current.get("capabilities") if isinstance(current.get("capabilities"), dict) else {"tier": tier},
        str((current.get("capabilities") or {}).get("argonMode") or "none"),
        email=email,
        license_info=license_info,
        oauth_info=safe_oauth_info,
        credits_info=credits_info,
    )

    if result.get("is_appeal") or result.get("status") == "DISABLED":
        appeal_err_id = result.get("error_id") or check_profile_appeal_status(profile) or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
        return _preserve_cached_model_meta({
            "email": email,
            "tier": tier,
            "planLabel": current.get("planLabel") or str(tier),
            "vendorLabel": current.get("vendorLabel") or "GOOGLE",
            "priority": priority,
            "accountMeta": fallback_norm["accountMeta"],
            "status": "DISABLED",
            "isAppeal": True,
            "appealReason": "This service has been disabled in this account for violation of Terms of Service. Please submit an appeal to continue using this product.",
            "errorId": appeal_err_id,
            "hasArgon": current.get("hasArgon", False),
            "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "geminiWeekly": {"name": "Gemini Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "claudeWeekly": {"name": "Claude Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
            "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True, "tags": True},
        }, current)

    if not result.get("success"):
        appeal_err_id = check_profile_appeal_status(profile)
        if appeal_err_id:
            return _preserve_cached_model_meta({
                "email": email,
                "tier": tier,
                "planLabel": current.get("planLabel") or str(tier),
                "vendorLabel": current.get("vendorLabel") or "GOOGLE",
                "priority": priority,
                "accountMeta": fallback_norm["accountMeta"],
                "status": "DISABLED",
                "isAppeal": True,
                "appealReason": "This service has been disabled in this account for violation of Terms of Service. Please submit an appeal to continue using this product.",
                "errorId": appeal_err_id,
                "hasArgon": current.get("hasArgon", False),
                "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "geminiWeekly": {"name": "Gemini Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "claudeWeekly": {"name": "Claude Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True},
                "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Bị khóa", "unavailable": True, "tags": True},
            }, current)
        return _preserve_cached_model_meta({
            "email": email,
            "tier": tier,
            "planLabel": current.get("planLabel") or str(tier),
            "vendorLabel": current.get("vendorLabel") or "GOOGLE",
            "priority": priority,
            "accountMeta": fallback_norm["accountMeta"],
            "status": "AUTH NEEDED",
            "isAppeal": False,
            "hasArgon": current.get("hasArgon", False),
            "gemini5h": {"name": "Gemini 3.8 / Pro 5H", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "claude5h": {"name": "Claude 5.5 / GPT 5H", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "geminiWeekly": {"name": "Gemini Weekly", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "claudeWeekly": {"name": "Claude Weekly", "fraction": 1.0, "countdown": "⏱ Auth needed", "unavailable": True},
            "argonWeekly": {"name": "Gemini 4 Argon Weekly", "fraction": 0.0, "countdown": "⏱ Auth needed", "unavailable": True, "tags": True},
        }, current)

    raw_groups = result.get("groups")
    groups = raw_groups if isinstance(raw_groups, list) else []
    items = parse_quota_items(groups)
    usage_parsed = parse_usage_group_models(groups)
    group_desc_sig = str(result.get("groupDescSig") or usage_parsed["groupDescSig"])

    available_models = (
        list(result["availableModels"])
        if isinstance(result.get("availableModels"), list)
        else list(current.get("availableModels") or [])
    )
    if isinstance(result.get("modelCatalog"), list):
        model_catalog = list(result["modelCatalog"])
    elif isinstance(current.get("modelCatalog"), list):
        model_catalog = list(current["modelCatalog"])
    elif available_models:
        model_catalog = parse_agy_models_catalog("\n".join(available_models))
    else:
        model_catalog = []

    models_fetched_at = str(
        result.get("modelsFetchedAt")
        if result.get("modelsFetchedAt") is not None
        else (current.get("modelsFetchedAt") or "")
    )
    group_models = (
        result["groupModels"]
        if isinstance(result.get("groupModels"), dict)
        else _reconcile_group_models(usage_parsed, model_catalog, current)
    )
    argon_mode = str(
        result.get("argonMode")
        or classify_argon_mode(
            groups,
            group_models=group_models,
            model_catalog=model_catalog,
            available_models=available_models,
            cached_entry=current,
        )
    )

    has_5h = items["gem_5h"]["available"] or items["cld_5h"]["available"]
    plan_raw = str(
        result.get("plan_name")
        or license_info.get("tierDisplayName")
        or ""
    ).strip()
    plan_up = plan_raw.upper()
    lic_tier = str(license_info.get("tier") or result.get("tier") or "").strip().upper()
    if lic_tier in ("ULTRA", "PRO", "FREE"):
        base_tier = lic_tier
    elif "ULTRA" in plan_up:
        base_tier = "ULTRA"
    elif "FREE" in plan_up or (groups and not has_5h):
        base_tier = "FREE"
    else:
        base_tier = "PRO" if has_5h else "FREE"

    capabilities = _derive_profile_capabilities(
        tier=base_tier,
        plan_name=plan_raw,
        has_dedicated_argon=bool(usage_parsed["hasDedicatedArgonGroup"]),
        argon_mode=argon_mode,
        group_models=group_models,
        model_catalog=model_catalog,
        available_models=available_models,
    )
    norm_acct = normalize_antigravity_account(
        profile,
        capabilities,
        argon_mode,
        email=email,
        license_info=license_info,
        oauth_info=safe_oauth_info,
        credits_info=credits_info,
    )
    tier = norm_acct["tier"]
    priority = norm_acct["priority"]
    has_argon = argon_mode != "none"

    is_exhausted = (
        items["gem_5h"]["fraction"] == 0 and
        items["cld_5h"]["fraction"] == 0 and
        items["gem_weekly"]["fraction"] == 0 and
        items["cld_weekly"]["fraction"] == 0
    )
    status = "EXHAUSTED" if is_exhausted else "ACTIVE"

    gem_5h_reset = items["gem_5h"]["reset_time"]
    gem_w_reset = items["gem_weekly"]["reset_time"]

    gem_5h_ts = 0
    local_5h_reset = ""

    if gem_5h_reset and not gem_5h_reset.startswith("1970"):
        try:
            dt_5h = datetime.datetime.fromisoformat(gem_5h_reset.replace("Z", "+00:00"))
            if dt_5h.year > 1970:
                gem_5h_ts = int(dt_5h.timestamp())
                local_5h_reset = dt_5h.astimezone().strftime("%H:%M:%S")
        except Exception:
            pass

    is_gem_active = is_bucket_activated(items["gem_5h"], 5 * 3600)
    is_cld_active = is_bucket_activated(items["cld_5h"], 5 * 3600)
    is_5h_active = is_gem_active or is_cld_active

    gem_w_ts = 0
    local_w_reset = ""
    if gem_w_reset and not gem_w_reset.startswith("1970"):
        try:
            dt_w = datetime.datetime.fromisoformat(gem_w_reset.replace("Z", "+00:00"))
            if dt_w.year > 1970:
                gem_w_ts = int(dt_w.timestamp())
                local_w_reset = dt_w.astimezone().strftime("%d/%m %H:%M")
        except Exception:
            pass

    # Save to hashed SQLite session store!
    save_session_record(profile, gem_5h_ts, gem_w_ts, items["gem_5h"]["fraction"], is_5h_active)

    countdown_5h_str = format_countdown(gem_5h_reset) if (gem_5h_reset and not gem_5h_reset.startswith("1970")) else "⏱ --"
    if local_5h_reset and countdown_5h_str != "⏱ --":
        countdown_5h_str += f" ({local_5h_reset})"

    cld_5h_reset = items["cld_5h"]["reset_time"]
    local_cld_5h_reset = ""
    if cld_5h_reset and not cld_5h_reset.startswith("1970"):
        try:
            dt_cld = datetime.datetime.fromisoformat(cld_5h_reset.replace("Z", "+00:00"))
            if dt_cld.year > 1970:
                local_cld_5h_reset = dt_cld.astimezone().strftime("%H:%M:%S")
        except Exception:
            pass

    countdown_cld_str = format_countdown(cld_5h_reset) if (cld_5h_reset and not cld_5h_reset.startswith("1970")) else "⏱ --"
    if local_cld_5h_reset and countdown_cld_str != "⏱ --":
        countdown_cld_str += f" ({local_cld_5h_reset})"

    countdown_w_str = format_countdown(gem_w_reset) if (gem_w_reset and not gem_w_reset.startswith("1970")) else "⏱ --"
    if local_w_reset and countdown_w_str != "⏱ --":
        countdown_w_str += f" ({local_w_reset})"

    cld_w_reset = items["cld_weekly"]["reset_time"]
    local_cld_w_reset = ""
    if cld_w_reset and not cld_w_reset.startswith("1970"):
        try:
            dt_cw = datetime.datetime.fromisoformat(cld_w_reset.replace("Z", "+00:00"))
            if dt_cw.year > 1970:
                local_cld_w_reset = dt_cw.astimezone().strftime("%d/%m %H:%M")
        except Exception:
            pass

    countdown_cld_w_str = format_countdown(cld_w_reset) if (cld_w_reset and not cld_w_reset.startswith("1970")) else "⏱ --"
    if local_cld_w_reset and countdown_cld_w_str != "⏱ --":
        countdown_cld_w_str += f" ({local_cld_w_reset})"

    gemini_weekly_bucket = {
        "name": "Gemini Weekly",
        "fraction": items["gem_weekly"]["fraction"],
        "countdown": countdown_w_str,
        "resetTime": gem_w_reset,
        "resetTimeLocal": local_w_reset,
        "unavailable": not items["gem_weekly"]["available"],
    }

    if argon_mode == "shared_gemini":
        shared_argon_title = (
            "Gemini 4 Carbon & Argon Weekly"
            if capabilities.get("hasCarbon")
            else "Gemini 4 Argon Weekly"
        )
        argon_weekly_bucket = {
            "name": shared_argon_title,
            "fraction": gemini_weekly_bucket["fraction"],
            "countdown": gemini_weekly_bucket["countdown"],
            "resetTime": gemini_weekly_bucket["resetTime"],
            "resetTimeLocal": gemini_weekly_bucket["resetTimeLocal"],
            "unavailable": gemini_weekly_bucket["unavailable"],
            "tags": True,
            "sharedPool": True,
            "mode": "shared_gemini",
        }
    elif argon_mode == "separate":
        countdown_arg_str = (
            format_countdown(items["argon_weekly"]["reset_time"])
            if (items["argon_weekly"]["reset_time"] and not items["argon_weekly"]["reset_time"].startswith("1970"))
            else ("⏱ --" if items["argon_weekly"]["available"] else "Unavailable N/A")
        )
        argon_weekly_bucket = {
            "name": "Gemini 4 Argon Weekly",
            "fraction": items["argon_weekly"]["fraction"] if items["argon_weekly"]["available"] else 0.0,
            "countdown": countdown_arg_str,
            "resetTime": items["argon_weekly"]["reset_time"],
            "unavailable": not items["argon_weekly"]["available"],
            "tags": True,
            "sharedPool": False,
            "mode": "separate",
        }
    else:
        argon_weekly_bucket = {
            "name": "Gemini 4 Argon Weekly",
            "fraction": 0.0,
            "countdown": "Unavailable N/A",
            "resetTime": "",
            "unavailable": True,
            "tags": True,
            "sharedPool": False,
            "mode": "none",
        }

    return {
        "email": norm_acct["email"],
        "tier": tier,
        "planLabel": norm_acct["planLabel"],
        "vendorLabel": norm_acct["vendorLabel"],
        "priority": priority,
        "accountMeta": norm_acct["accountMeta"],
        "status": status,
        "isAppeal": False,
        "isSessionActive": is_5h_active,
        "resetTime": gem_5h_reset,
        "resetTimeLocal": local_5h_reset,
        "hasArgon": has_argon,
        "gemini5h": {
            "name": "Gemini 3.8 / Pro 5H",
            "fraction": items["gem_5h"]["fraction"],
            "countdown": countdown_5h_str,
            "resetTime": gem_5h_reset,
            "resetTimeLocal": local_5h_reset,
            "unavailable": not items["gem_5h"]["available"],
        },
        "claude5h": {
            "name": "Claude 5.5 / GPT 5H",
            "fraction": items["cld_5h"]["fraction"],
            "countdown": countdown_cld_str,
            "resetTime": items["cld_5h"]["reset_time"],
            "unavailable": not items["cld_5h"]["available"],
        },
        "geminiWeekly": gemini_weekly_bucket,
        "claudeWeekly": {
            "name": "Claude Weekly",
            "fraction": items["cld_weekly"]["fraction"],
            "countdown": countdown_cld_w_str,
            "resetTime": items["cld_weekly"]["reset_time"],
            "unavailable": not items["cld_weekly"]["available"],
        },
        "argonWeekly": argon_weekly_bucket,
        "availableModels": available_models,
        "modelCatalog": model_catalog,
        "groupModels": group_models,
        "capabilities": capabilities,
        "modelsFetchedAt": models_fetched_at,
        "groupDescSig": group_desc_sig,
    }


def apply_activated_countdown_estimates(profile_data: dict, now_utc: datetime.datetime | None = None) -> dict:
    """Ensure all 5H and Weekly buckets have estimated active countdown timers following successful activation."""
    if not isinstance(profile_data, dict):
        return profile_data
    if now_utc is None:
        now_utc = datetime.datetime.now(datetime.timezone.utc)

    # 5-Hour rolling window
    est_5h_dt = now_utc + datetime.timedelta(hours=5)
    est_5h_iso = est_5h_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    local_5h = est_5h_dt.astimezone().strftime("%H:%M:%S")

    # 7-Day (Weekly) rolling window
    est_7d_dt = now_utc + datetime.timedelta(days=7)
    est_7d_iso = est_7d_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    local_7d = est_7d_dt.astimezone().strftime("%d/%m %H:%M")

    def _is_invalid_or_past(reset_str: str) -> bool:
        if not reset_str or reset_str.startswith("1970"):
            return True
        try:
            dt = datetime.datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
            return dt.year <= 1970 or (dt - now_utc).total_seconds() <= 60
        except Exception:
            return True

    # 1. Gemini 5H
    g5 = profile_data.get("gemini5h")
    if isinstance(g5, dict) and not g5.get("unavailable"):
        if _is_invalid_or_past(g5.get("resetTime", "")):
            g5["resetTime"] = est_5h_iso
            g5["resetTimeLocal"] = local_5h
            g5["countdown"] = f"⏱ 4h 59m ({local_5h})"
        else:
            loc = g5.get("resetTimeLocal", "")
            g5["countdown"] = format_countdown(g5["resetTime"]) + (f" ({loc})" if loc else "")
        if g5.get("fraction", 0.0) == 0.0:
            g5["fraction"] = 1.0

    # 2. Claude 5H
    c5 = profile_data.get("claude5h")
    if isinstance(c5, dict) and not c5.get("unavailable"):
        if _is_invalid_or_past(c5.get("resetTime", "")):
            c5["resetTime"] = est_5h_iso
            c5["resetTimeLocal"] = local_5h
            c5["countdown"] = f"⏱ 4h 59m ({local_5h})"
        else:
            loc = c5.get("resetTimeLocal", "")
            c5["countdown"] = format_countdown(c5["resetTime"]) + (f" ({loc})" if loc else "")
        if c5.get("fraction", 0.0) == 0.0:
            c5["fraction"] = 1.0

    # 3. Gemini Weekly
    gw = profile_data.get("geminiWeekly")
    if isinstance(gw, dict) and not gw.get("unavailable"):
        if _is_invalid_or_past(gw.get("resetTime", "")):
            gw["resetTime"] = est_7d_iso
            gw["resetTimeLocal"] = local_7d
            gw["countdown"] = f"⏱ 6d 23h ({local_7d})"
        else:
            loc = gw.get("resetTimeLocal", "")
            gw["countdown"] = format_countdown(gw["resetTime"]) + (f" ({loc})" if loc else "")
        if gw.get("fraction", 0.0) == 0.0:
            gw["fraction"] = 1.0

    # 4. Claude Weekly
    cw = profile_data.get("claudeWeekly")
    if isinstance(cw, dict) and not cw.get("unavailable"):
        if _is_invalid_or_past(cw.get("resetTime", "")):
            cw["resetTime"] = est_7d_iso
            cw["resetTimeLocal"] = local_7d
            cw["countdown"] = f"⏱ 6d 23h ({local_7d})"
        else:
            loc = cw.get("resetTimeLocal", "")
            cw["countdown"] = format_countdown(cw["resetTime"]) + (f" ({loc})" if loc else "")
        if cw.get("fraction", 0.0) == 0.0:
            cw["fraction"] = 1.0

    # 5. Argon Weekly
    aw = profile_data.get("argonWeekly")
    if isinstance(aw, dict) and not aw.get("unavailable"):
        is_shared = aw.get("sharedPool") or aw.get("mode") == "shared_gemini"
        if is_shared and isinstance(gw, dict):
            aw["resetTime"] = gw.get("resetTime", est_7d_iso)
            aw["resetTimeLocal"] = gw.get("resetTimeLocal", local_7d)
            aw["countdown"] = gw.get("countdown", f"⏱ 6d 23h ({local_7d})")
            aw["fraction"] = gw.get("fraction", 1.0)
        elif _is_invalid_or_past(aw.get("resetTime", "")):
            aw["resetTime"] = est_7d_iso
            aw["resetTimeLocal"] = local_7d
            aw["countdown"] = f"⏱ 6d 23h ({local_7d})"
            if aw.get("fraction", 0.0) == 0.0:
                aw["fraction"] = 1.0
        else:
            loc = aw.get("resetTimeLocal", "")
            aw["countdown"] = format_countdown(aw["resetTime"]) + (f" ({loc})" if loc else "")

    # Top-level session state
    profile_data["isSessionActive"] = True
    if _is_invalid_or_past(profile_data.get("resetTime", "")):
        profile_data["resetTime"] = est_5h_iso
        profile_data["resetTimeLocal"] = local_5h

    return profile_data


def execute_ping_profile(profile: str, force: bool = False) -> dict:
    # 1. Provider: Claude Code
    if profile == "claude":
        claude_quota = fetch_claude_quota()
        if claude_quota.get("isSessionActive") and not force:
            rem = claude_quota.get("remainingCountdown", "5h")
            msg = f"Phiên Claude 5H đang active ({rem}). Bỏ qua ping."
            return {
                "profile": "claude",
                "success": True,
                "status": "ACTIVE",
                "isSessionActive": True,
                "skipped": True,
                "duration_ms": 5,
                "message": msg,
            }
        t0 = time.time()
        try:
            env = os.environ.copy()
            env["HOME"] = REAL_HOME
            claude_bin = shutil.which("claude") or "/usr/local/bin/claude"
            cmd = [
                claude_bin,
                "--safe-mode",
                "--disable-slash-commands",
                "--tools", "",
                "--model", "haiku",
                "-p", "1"
            ]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            dur = int((time.time() - t0) * 1000)
            if res.returncode == 0:
                fetch_claude_quota()  # update session store
                return {"profile": "claude", "success": True, "duration_ms": dur, "message": f"Kích hoạt Claude thành công ({dur}ms)"}
            return {"profile": "claude", "success": False, "duration_ms": dur, "error": res.stderr.strip() or f"Code {res.returncode}"}
        except subprocess.TimeoutExpired:
            return {"profile": "claude", "success": False, "duration_ms": 25000, "error": "Request timed out (25s)"}
        except Exception as e:
            return {"profile": "claude", "success": False, "duration_ms": 50, "error": str(e)}

    # 2. Provider: OpenAI Codex
    if profile == "codex":
        codex_quota = fetch_codex_quota()
        if codex_quota.get("isSessionActive") and not force:
            rem = codex_quota.get("remainingCountdown", "5h")
            msg = f"Phiên Codex 5H đang active ({rem}). Bỏ qua ping."
            return {
                "profile": "codex",
                "success": True,
                "status": "ACTIVE",
                "isSessionActive": True,
                "skipped": True,
                "duration_ms": 5,
                "message": msg,
            }
        t0 = time.time()
        try:
            env = os.environ.copy()
            env["HOME"] = REAL_HOME
            codex_bin = shutil.which("codex") or "/usr/local/bin/codex"
            cmd = [
                codex_bin,
                "exec",
                "1",
                "--ephemeral",
                "--skip-git-repo-check",
            ]
            res = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            dur = int((time.time() - t0) * 1000)
            if res.returncode == 0:
                fetch_codex_quota()  # update session store
                return {"profile": "codex", "success": True, "duration_ms": dur, "message": f"Kích hoạt Codex thành công ({dur}ms)"}
            return {"profile": "codex", "success": False, "duration_ms": dur, "error": res.stderr.strip() or f"Code {res.returncode}"}
        except subprocess.TimeoutExpired:
            return {"profile": "codex", "success": False, "duration_ms": 25000, "error": "Request timed out (25s)"}
        except Exception as e:
            return {"profile": "codex", "success": False, "duration_ms": 50, "error": str(e)}

    # 3. Provider: Kiro CLI
    if profile == "kiro":
        k_data = fetch_kiro_quota()
        update_cached_profile("kiro", k_data)
        rem = k_data.get("remainingCountdown", "")
        return {
            "profile": "kiro",
            "success": True,
            "duration_ms": 150,
            "message": f"Kiro Quota đã được đồng bộ ({rem})"
        }

    # 4. Antigravity profile:
    ag_home = f"{REAL_HOME}/antigravity_homes/{profile}"
    if not os.path.isdir(ag_home):
        return {"profile": profile, "success": False, "error": f"Profile home not found: {ag_home}"}

    appeal_err_id = check_profile_appeal_status(profile)
    if appeal_err_id:
        return {
            "profile": profile,
            "success": False,
            "status": "DISABLED",
            "is_appeal": True,
            "error_id": appeal_err_id,
            "duration_ms": 50,
            "error": "Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal)",
        }

    if not check_profile_auth_token(profile):
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_appeal": False,
            "duration_ms": 50,
            "error": "Profile chưa đăng nhập CLI. Cần đăng nhập bằng Terminal trước khi ping.",
        }

    t0 = time.time()
    cached_p = _peek_cached_profile(profile)

    # Always probe live quota before deciding which buckets need activation
    live_q = fetch_quota_for_profile(profile)
    if live_q.get("status") == "DISABLED" or live_q.get("is_appeal"):
        err_id = live_q.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
        return {
            "profile": profile,
            "success": False,
            "status": "DISABLED",
            "is_appeal": True,
            "error_id": err_id,
            "duration_ms": int((time.time() - t0) * 1000),
            "error": live_q.get("error") or f"Tài khoản bị vô hiệu hóa (Mã lỗi: {err_id})",
        }
    if live_q.get("status") == "AUTH NEEDED":
        return {
            "profile": profile,
            "success": False,
            "status": "AUTH NEEDED",
            "is_appeal": False,
            "duration_ms": int((time.time() - t0) * 1000),
            "error": live_q.get("error") or "Profile chưa đăng nhập CLI.",
        }

    tier = str(live_q.get("tier") or cached_p.get("tier") or "").upper()
    if tier == "FREE":
        return {
            "profile": profile,
            "success": False,
            "status": "FREE",
            "skipped": True,
            "duration_ms": int((time.time() - t0) * 1000),
            "error": "Tài khoản FREE không hỗ trợ kích hoạt session 5H / Argon.",
        }

    if not live_q.get("success") and not cached_p:
        return {
            "profile": profile,
            "success": False,
            "duration_ms": int((time.time() - t0) * 1000),
            "error": live_q.get("error") or "Không thể kiểm tra quota live trước khi ping.",
        }

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_ts = time.time()

    if live_q.get("success") and live_q.get("groups"):
        q_items = parse_quota_items(live_q["groups"])
        gem_bucket = q_items["gem_5h"]
        cld_bucket = q_items["cld_5h"]
        live_argon_mode = str(
            live_q.get("argonMode")
            or classify_argon_mode(
                live_q.get("groups"),
                group_models=live_q.get("groupModels"),
                model_catalog=live_q.get("modelCatalog"),
                available_models=live_q.get("availableModels"),
                cached_entry=cached_p,
            )
        )
        if live_argon_mode == "separate":
            arg_bucket = q_items["argon_weekly"]
        else:
            arg_bucket = {
                "fraction": 0.0,
                "reset_time": "",
                "description": "",
                "available": False,
            }
        effective_argon_mode = live_argon_mode
    else:
        gem_bucket = _bucket_from_cached_entry(
            cached_p.get("gemini5h"), default_available=(tier != "FREE")
        )
        cld_bucket = _bucket_from_cached_entry(
            cached_p.get("claude5h"), default_available=(tier != "FREE")
        )
        cached_separate_argon = _is_separate_argon_cached(cached_p)
        arg_bucket = _bucket_from_cached_entry(
            cached_p.get("argonWeekly"),
            default_available=cached_separate_argon,
        )
        if not cached_separate_argon:
            arg_bucket["available"] = False
        effective_argon_mode = (
            "separate"
            if cached_separate_argon
            else str((cached_p.get("capabilities") or {}).get("argonMode") or "none")
        )

    gemini_available = bool(gem_bucket.get("available"))
    claude_available = bool(cld_bucket.get("available"))
    has_argon = bool(arg_bucket.get("available"))

    gem_rem_sec = _parse_reset_rem_sec(str(gem_bucket.get("reset_time") or ""), now_utc)
    cld_rem_sec = _parse_reset_rem_sec(str(cld_bucket.get("reset_time") or ""), now_utc)
    argon_rem_sec = _parse_reset_rem_sec(
        str(arg_bucket.get("reset_time") or ""), now_utc, default=7 * 86400
    )

    is_gemini_active = is_bucket_activated(gem_bucket, 5 * 3600, now_ts=now_ts)
    is_claude_active = is_bucket_activated(cld_bucket, 5 * 3600, now_ts=now_ts)
    is_argon_active = is_bucket_activated(arg_bucket, 7 * 86400, now_ts=now_ts)

    argon_fraction = float(arg_bucket.get("fraction", 0.0) or 0.0)
    is_argon_near_reset = has_argon and (0 < argon_rem_sec < 7 * 3600)
    is_argon_max_7d = has_argon and not is_argon_active and (argon_fraction >= 0.999)

    should_ping_gemini = gemini_available and (force or not is_gemini_active)
    should_ping_claude = claude_available and (force or not is_claude_active)
    should_ping_argon = (
        has_argon
        and not is_argon_near_reset
        and (force or is_argon_max_7d)
    )

    # If all eligible buckets are already active, skip cleanly
    if not should_ping_gemini and not should_ping_claude and not should_ping_argon:
        active_parts = []
        if gemini_available:
            active_parts.append(f"Gemini 5H ({int(gem_rem_sec // 3600)}h {int((gem_rem_sec % 3600) // 60)}m)")
        if claude_available:
            cld_str = f"{int(cld_rem_sec // 3600)}h {int((cld_rem_sec % 3600) // 60)}m" if cld_rem_sec > 60 else "active"
            active_parts.append(f"Claude 5H ({cld_str})")
        if has_argon:
            if is_argon_near_reset:
                active_parts.append("Argon < 7h (bỏ qua)")
            else:
                active_parts.append("Argon đã kích hoạt")
        elif effective_argon_mode == "shared_gemini":
            active_parts.append("Argon (Shared Gemini Pool)")
        else:
            active_parts.append("Không hỗ trợ Argon")

        msg = f"Tất cả models đang trong phiên hoạt động ({', '.join(active_parts)}). Bỏ qua ping."
        cached_p = _peek_cached_profile(profile) or {}
        post_q_data = None
        if cached_p:
            post_q_data = apply_activated_countdown_estimates(dict(cached_p), now_utc)
            update_cached_profile(profile, post_q_data)
        return {
            "profile": profile,
            "success": True,
            "status": "ACTIVE",
            "isSessionActive": True,
            "skipped": True,
            "duration_ms": 5,
            "message": msg,
            "pinged_gemini": False,
            "pinged_claude": False,
            "pinged_argon": False,
            "post_quota": post_q_data,
        }

    # Unlock keychain if needed
    wait_for_launch_lock()
    profile_kc = f"{ag_home}/Library/Keychains/{profile}.keychain-db"
    if os.path.exists(profile_kc):
        subprocess.run(["security", "unlock-keychain", "-p", KC_PASS, profile_kc], capture_output=True)

    env = build_profile_cli_env(profile)

    pinged_gemini = False
    pinged_claude = False
    pinged_argon = False
    jitter_applied = 0.0
    used_prompts: list[str] = []
    failures: list[str] = []
    act_names: list[str] = []

    with tempfile.TemporaryDirectory(prefix=f"agy_ping_{profile}_") as sandbox_cwd:
        pre_discovered = live_q.get("availableModels")
        available_models = (
            list(pre_discovered)
            if isinstance(pre_discovered, list) and pre_discovered
            else _discover_profile_models(env, sandbox_cwd)
        )
        bucket_plan = []
        if should_ping_gemini:
            gem_model = select_model_from_candidates(
                available_models, GEMINI_MODEL_CANDIDATES, GEMINI_MODEL_CANDIDATES[0]
            )
            bucket_plan.append(("gemini", "Gemini 3.8 / Pro 5H", gem_model, (0.0, 0.0)))
        if should_ping_claude:
            cld_model = select_model_from_candidates(
                available_models, CLAUDE_MODEL_CANDIDATES, CLAUDE_MODEL_CANDIDATES[0]
            )
            cld_label = "Claude 5.5" if "5-5" in cld_model else f"Claude 5H ({cld_model})"
            bucket_plan.append(("claude", cld_label, cld_model, (1.5, 2.5)))
        if should_ping_argon:
            arg_model = select_model_from_candidates(
                available_models, ARGON_MODEL_CANDIDATES, ARGON_MODEL_CANDIDATES[0]
            )
            bucket_plan.append(("argon", "Argon 7D", arg_model, (1.8, 3.0)))

        for key, label, model_id, jitter_range in bucket_plan:
            if (pinged_gemini or pinged_claude) and jitter_range[1] > 0:
                j = round(random.uniform(*jitter_range), 2)
                jitter_applied += j
                time.sleep(j)

            choices = [p for p in NATURAL_PROMPTS if p not in used_prompts] or NATURAL_PROMPTS
            prompt = random.choice(choices)
            used_prompts.append(prompt)

            res = _ping_agy_model(profile, label, model_id, prompt, env, sandbox_cwd, timeout=50)
            if res.get("disabled"):
                return {**res["response"], "duration_ms": int((time.time() - t0) * 1000)}
            if res.get("ok"):
                act_names.append(label)
                if key == "gemini":
                    pinged_gemini = True
                elif key == "claude":
                    pinged_claude = True
                elif key == "argon":
                    pinged_argon = True
            else:
                if res.get("invalid_model") and key == "argon":
                    cached_p["hasArgon"] = False
                    if "argonWeekly" in cached_p:
                        cached_p["argonWeekly"]["unavailable"] = True
                        cached_p["argonWeekly"]["countdown"] = "Unavailable N/A"
                    update_cached_profile(profile, cached_p)
                failures.append(f"{label}: {res.get('error', 'Ping thất bại')}")

    total_dur = int((time.time() - t0) * 1000)
    jitter_applied = round(jitter_applied, 2)

    seed_model_meta: dict = {}
    live_fetched_at = str(live_q.get("modelsFetchedAt") or "").strip()
    if isinstance(live_q.get("availableModels"), list) and (
        live_q["availableModels"] or live_fetched_at
    ):
        seed_model_meta["availableModels"] = list(live_q["availableModels"])
    elif available_models:
        seed_model_meta["availableModels"] = list(available_models)

    if isinstance(live_q.get("modelCatalog"), list) and (
        live_q["modelCatalog"] or live_fetched_at
    ):
        seed_model_meta["modelCatalog"] = list(live_q["modelCatalog"])
    elif seed_model_meta.get("availableModels"):
        seed_model_meta["modelCatalog"] = parse_agy_models_catalog(
            "\n".join(seed_model_meta["availableModels"])
        )

    if live_fetched_at:
        seed_model_meta["modelsFetchedAt"] = live_fetched_at
    elif seed_model_meta.get("availableModels"):
        seed_model_meta["modelsFetchedAt"] = datetime.datetime.now(
            datetime.timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%SZ")

    live_sig = str(live_q.get("groupDescSig") or "").strip()
    if not live_sig and isinstance(live_q.get("groups"), list) and live_q["groups"]:
        live_sig = str(parse_usage_group_models(live_q["groups"])["groupDescSig"] or "")
    if live_sig:
        seed_model_meta["groupDescSig"] = live_sig

    if isinstance(live_q.get("groupModels"), dict):
        seed_model_meta["groupModels"] = live_q["groupModels"]
    if isinstance(live_q.get("capabilities"), dict):
        seed_model_meta["capabilities"] = live_q["capabilities"]

    # Post-ping quota refresh to update dashboard immediately
    post_q = fetch_quota_for_profile(
        profile, batch_mode=True, cached_override=seed_model_meta or None
    )
    post_quota_formatted = None
    if post_q.get("success"):
        post_q_merged = dict(post_q)
        for meta_key in (
            "availableModels",
            "modelCatalog",
            "modelsFetchedAt",
            "groupDescSig",
        ):
            if meta_key in seed_model_meta and not post_q_merged.get(meta_key):
                post_q_merged[meta_key] = seed_model_meta[meta_key]
        post_quota_formatted = format_profile_for_dashboard(profile, post_q_merged)
    elif cached_p:
        post_quota_formatted = dict(cached_p)

    if post_quota_formatted and (len(failures) == 0 or act_names):
        post_quota_formatted = apply_activated_countdown_estimates(post_quota_formatted, now_utc)
        update_cached_profile(profile, post_quota_formatted)
    elif post_quota_formatted:
        update_cached_profile(profile, post_quota_formatted)

    jitter_str = f", Jitter {jitter_applied}s" if jitter_applied > 0 else ""
    if act_names and not failures:
        msg = f"Kích hoạt thành công {' & '.join(act_names)}{jitter_str} ({total_dur}ms)"
    elif act_names and failures:
        msg = f"Kích hoạt một phần: Đã bật {' & '.join(act_names)}; Lỗi: {'; '.join(failures)}"
    elif failures:
        msg = f"Kích hoạt thất bại: {'; '.join(failures)}"
    else:
        msg = f"Đã kiểm tra phiên làm việc của {profile} ({total_dur}ms)"

    result = {
        "profile": profile,
        "success": len(failures) == 0,
        "duration_ms": total_dur,
        "message": msg,
        "pinged_gemini": pinged_gemini,
        "pinged_claude": pinged_claude,
        "pinged_argon": pinged_argon,
        "jitter_seconds": jitter_applied,
        "details": {"failures": failures, "activated": act_names},
    }
    if failures:
        result["error"] = "; ".join(failures)
    if post_quota_formatted is not None:
        result["post_quota"] = post_quota_formatted
    return result


def _parse_reset_rem_sec(reset_str: str, now_utc: datetime.datetime, default: float = 0.0) -> float:
    """Parse ISO UTC reset_time string into remaining seconds from now_utc."""
    if not reset_str:
        return default
    try:
        dt = datetime.datetime.fromisoformat(reset_str.replace("Z", "+00:00"))
        return (dt - now_utc).total_seconds()
    except Exception:
        return default


def _bucket_from_cached_entry(entry: dict | None, default_available: bool = True) -> dict:
    """Convert cached dashboard bucket dict into normalized live-bucket format."""
    if not entry:
        return {"fraction": 1.0, "reset_time": "", "description": "", "available": default_available}
    return {
        "fraction": entry.get("fraction", 1.0),
        "reset_time": entry.get("resetTime", ""),
        "description": entry.get("description", ""),
        "available": not bool(entry.get("unavailable", False)),
    }


def _discover_profile_models(env: dict[str, str], cwd: str) -> list[str]:
    """Query `agy models` for the active profile inside an isolated temp cwd."""
    try:
        res = subprocess.run(
            [AGY_BIN, "models"],
            env=env,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=25,
        )
        if res.returncode == 0:
            return parse_agy_models_output(res.stdout or "")
    except Exception:
        pass
    return []


def _ping_agy_model(
    profile: str,
    bucket_label: str,
    model_id: str,
    prompt: str,
    env: dict[str, str],
    cwd: str,
    timeout: int = 50,
) -> dict:
    """Ping a single Antigravity model inside an isolated sandbox directory."""
    cmd = [AGY_BIN, "--model", model_id, "--disable-slash-commands", "-p", prompt]
    try:
        res = subprocess.run(cmd, env=env, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        out_all = f"{res.stdout or ''} {res.stderr or ''}"
        appeal_id = check_profile_appeal_status(profile, out_all)
        low_out = out_all.lower()
        if appeal_id or "submit an appeal" in low_out or "violation of terms of service" in low_out or "service has been disabled" in low_out:
            err_id = appeal_id or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
            record_profile_disabled(profile, err_id)
            disabled_data = format_profile_for_dashboard(
                profile,
                {"success": False, "status": "DISABLED", "is_appeal": True, "error_id": err_id},
            )
            update_cached_profile(profile, disabled_data)
            return {
                "ok": False,
                "disabled": True,
                "response": {
                    "profile": profile,
                    "success": False,
                    "status": "DISABLED",
                    "is_appeal": True,
                    "error_id": err_id,
                    "error": f"Tài khoản bị vô hiệu hóa do vi phạm Điều khoản (Terms of Service / Submit an appeal). Mã lỗi: {err_id}",
                },
            }
        if "is not recognized" in low_out or "invalid model selection" in low_out:
            return {"ok": False, "invalid_model": True, "error": f"Model {model_id} không khả dụng"}
        if res.returncode == 0:
            return {"ok": True}
        err_txt = (res.stderr or res.stdout or "").strip() or f"Exit code {res.returncode}"
        return {"ok": False, "error": err_txt}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{bucket_label} ping timed out ({timeout}s)"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def scan_all_profiles_parallel(profiles: list) -> list:
    results = []
    # Use max_workers=3 and staggered submission to eliminate burst traffic to Google Cloud endpoints
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_profile = {}
        for p in profiles:
            future_to_profile[executor.submit(fetch_quota_for_profile, p, False, True)] = p
            time.sleep(0.2)
        for future in as_completed(future_to_profile):
            try:
                res = future.result()
                results.append(res)
            except Exception as e:
                p = future_to_profile[future]
                results.append({"profile": p, "success": False, "error": str(e)})
    results.sort(key=lambda x: profiles.index(x["profile"]) if x["profile"] in profiles else 999)
    return results


def _check_and_schedule_hot_reload(server: object) -> None:
    """Schedule graceful daemon shutdown + execv reload if agy_quota.py mtime changed on disk."""
    global _RELOAD_PENDING
    if _RELOAD_PENDING or not isinstance(server, socketserver.BaseServer):
        return
    try:
        cur_mtime = int(Path(__file__).stat().st_mtime)
    except OSError:
        return
    if cur_mtime != SERVER_STARTUP_MTIME:
        _RELOAD_PENDING = True
        threading.Thread(target=server.shutdown, daemon=True).start()


def parse_refresh_profiles_query(query: dict[str, list[str]]) -> list[str] | None:
    """Parse optional `profiles` query parameter for `/api/refresh-all`.

    Returns None when absent (full refresh), or a validated deduplicated list of
    profile/provider names when provided (filtered refresh).
    """
    if "profiles" not in query:
        return None
    seen: set[str] = set()
    targets: list[str] = []
    for raw_entry in query.get("profiles", []):
        for part in str(raw_entry or "").split(","):
            name = part.strip()
            if not name:
                continue
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
                raise ValueError(f"Invalid profile name: {name}")
            if name not in seen:
                seen.add(name)
                targets.append(name)
    return targets


class QuotaDashboardHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if "/favicon.ico" in self.path:
            return
        try:
            code = args[1] if len(args) > 1 else "-"
            color = GREEN if str(code).startswith("2") else (AMBER if str(code).startswith("3") else RED)
            sys.stdout.write(f"  {GRAY}[{time.strftime('%H:%M:%S')}]{RESET} {CYAN}{self.command}{RESET} {self.path} {color}{code}{RESET}\n")
            sys.stdout.flush()
        except Exception:
            pass

    def _maybe_trigger_hot_reload(self) -> None:
        _check_and_schedule_hot_reload(getattr(self, "server", None))

    def send_json(self, data, status=200):
        try:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        except Exception:
            pass
        self._maybe_trigger_hot_reload()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _read_json_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except (AttributeError, TypeError, ValueError):
            length = 0
        if length <= 0 or not getattr(self, "rfile", None):
            return {}
        try:
            raw = self.rfile.read(length).decode("utf-8", errors="ignore")
            data = json.loads(raw) if raw.strip() else {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _safe_schedule_status(self) -> dict:
        mod = _load_refresh_session_module()
        if not mod or not hasattr(mod, "get_schedule_status"):
            return {"success": False, "schedules": [], "by_profile": {}}
        try:
            st = mod.get_schedule_status()
            return st if isinstance(st, dict) else {"success": True, "schedules": [], "by_profile": {}}
        except Exception as exc:
            return {"success": False, "error": str(exc), "schedules": [], "by_profile": {}}

    def _handle_api_schedule(self, query: dict, method: str = "GET") -> None:
        mod = _load_refresh_session_module()
        if not mod:
            self.send_json({"success": False, "error": "Không tìm thấy module refresh_session.py"}, status=500)
            return

        if method == "GET":
            status = self._safe_schedule_status()
            status.setdefault("success", True)
            self.send_json(status)
            return

        body = self._read_json_body() if method in ("POST", "DELETE") else {}
        action = str(body.get("action") or query.get("action", ["remove" if method == "DELETE" else "set"])[0]).lower()

        if action in ("remove", "delete", "uninstall"):
            remove_all = bool(body.get("all"))
            raw_profiles = body.get("profiles") or ([] if body.get("profile") is None else [body.get("profile")])
            if isinstance(raw_profiles, str):
                raw_profiles = [x.strip() for x in raw_profiles.split(",") if x.strip()]
            q_prof = query.get("profile", [""])[0]
            if not raw_profiles and q_prof:
                raw_profiles = [x.strip() for x in q_prof.split(",") if x.strip()]
            for p in raw_profiles:
                if not re.fullmatch(r"[A-Za-z0-9_-]+", str(p)):
                    self.send_json({"success": False, "error": f"Tên profile không hợp lệ: {p}"}, status=400)
                    return

            time_str = body.get("time") or query.get("time", [None])[0]
            raw_delay = body.get("delay") if "delay" in body else query.get("delay", [None])[0]
            delay_val = int(raw_delay) if raw_delay is not None and str(raw_delay) != "" else None
            target_arg = None if remove_all else (",".join(raw_profiles) if raw_profiles else None)
            try:
                res = mod.uninstall_schedule(target=target_arg, time_str=time_str, delay=delay_val)
            except ValueError as exc:
                self.send_json({"success": False, "error": str(exc)}, status=400)
                return
            status = self._safe_schedule_status()
            self.send_json({
                "success": bool(res.get("success", True)),
                "message": "Đã cập nhật lịch LaunchAgent trên hệ thống.",
                "error": res.get("error"),
                **{k: v for k, v in status.items() if k != "success"},
            })
            return

        # Action: set / add multi-schedule
        raw_profiles = body.get("profiles")
        if raw_profiles is None and body.get("profile"):
            raw_profiles = [body.get("profile")]
        if isinstance(raw_profiles, str):
            raw_profiles = [x.strip() for x in raw_profiles.split(",") if x.strip()]
        if not raw_profiles:
            q_prof = query.get("profile", [""])[0]
            raw_profiles = [x.strip() for x in q_prof.split(",") if x.strip()]
        if not raw_profiles:
            self.send_json({"success": False, "error": "Cần chọn ít nhất 1 profile để lên lịch."}, status=400)
            return

        for p in raw_profiles:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", str(p)):
                self.send_json({"success": False, "error": f"Tên profile không hợp lệ: {p}"}, status=400)
                return

        cached = load_cached_profiles()
        blocked_free = []
        blocked_other = []
        for p in raw_profiles:
            pdata = cached.get(p, {})
            if p == "kiro" or pdata.get("isCreditOnly"):
                blocked_other.append(f"{p} (credit pool)")
            elif pdata.get("tier") == "FREE":
                blocked_free.append(p)
            elif pdata.get("status") in ("DISABLED", "AUTH NEEDED") or pdata.get("isAppeal"):
                blocked_other.append(f"{p} ({pdata.get('status')})")
        if blocked_free:
            self.send_json({
                "success": False,
                "error": f"Tài khoản FREE ({', '.join(blocked_free)}) không hỗ trợ lên lịch kích hoạt.",
            }, status=400)
            return
        if blocked_other:
            self.send_json({
                "success": False,
                "error": f"Profile không đủ điều kiện lên lịch: {', '.join(blocked_other)}",
            }, status=400)
            return

        time_str = str(body.get("time") or query.get("time", [""])[0]).strip()
        try:
            hour, minute = mod.parse_flexible_time(time_str)
        except Exception as exc:
            self.send_json({"success": False, "error": f"Giờ không hợp lệ (chấp nhận 00:00-23:59): {exc}"}, status=400)
            return

        try:
            delay_val = int(body.get("delay") if "delay" in body else query.get("delay", [30])[0])
        except (TypeError, ValueError):
            self.send_json({"success": False, "error": "Offset giây không hợp lệ."}, status=400)
            return
        if not (0 <= delay_val <= 60):
            self.send_json({"success": False, "error": "Offset giây phải trong khoảng 0 - 60s."}, status=400)
            return

        if body.get("replace"):
            mod.uninstall_schedule(target=",".join(raw_profiles))

        inst = mod.install_schedule(hour, minute, target=",".join(raw_profiles), delay=delay_val)
        status = self._safe_schedule_status()
        if not inst.get("success"):
            self.send_json({
                "success": False,
                "error": inst.get("error") or "Không thể kích hoạt macOS LaunchAgent.",
                **{k: v for k, v in status.items() if k != "success"},
            }, status=500)
            return

        self.send_json({
            "success": True,
            "message": f"Đã cài đặt lịch {hour:02d}:{minute:02d} (+{delay_val}s) cho {', '.join(raw_profiles)}",
            "plist_path": inst.get("plist_path"),
            "label": inst.get("label"),
            **{k: v for k, v in status.items() if k != "success"},
        })

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/schedule":
            self._handle_api_schedule(query, method="POST")
            return
        self.do_GET()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if parsed.path == "/api/schedule":
            self._handle_api_schedule(query, method="DELETE")
            return
        self.send_json({"success": False, "error": "Method Not Allowed"}, status=405)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if path in ("/", "/index.html", "/quota_dashboard.html"):
            html_p = get_dashboard_html_path()
            if html_p.is_file():
                content = html_p.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                self.wfile.flush()
            else:
                self.send_error(404, "Dashboard HTML not found")
            self._maybe_trigger_hot_reload()
            return

        if path == "/api/status":
            last_rf = get_last_refresh_all_time()
            now = int(time.time())
            if last_rf == 0:
                last_rf = now
                record_refresh_all_time(last_rf)
            elapsed = max(0, now - last_rf)
            can_auto = elapsed >= GLOBAL_REFRESH_INTERVAL_SECONDS
            sched = self._safe_schedule_status()
            self.send_json({
                "success": True,
                "server_code_mtime": SERVER_STARTUP_MTIME,
                "profiles": load_cached_profiles(),
                "last_refresh_all": last_rf,
                "elapsed_seconds": elapsed,
                "can_auto_refresh": can_auto,
                "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS,
                "schedules": sched.get("schedules", []),
                "schedules_by_profile": sched.get("by_profile", {}),
            })
            return

        if path == "/api/schedule":
            self._handle_api_schedule(query, method="GET")
            return

        if path == "/api/check-blocked":
            profile = query.get("profile", [""])[0]
            if not profile:
                self.send_json({"success": False, "error": "Thiếu tham số profile"}, status=400)
                return
            res = probe_blocked_profile(profile)
            self.send_json(res)
            return

        if path == "/api/refresh":
            profile = query.get("profile", ["danhdue"])[0]
            if query.get("check_blocked", ["0"])[0] in ("1", "true", "True") or query.get("check_appeal", ["0"])[0] in ("1", "true", "True"):
                res = probe_blocked_profile(profile)
                self.send_json(res)
                return
            if profile == "claude":
                f_data = fetch_claude_quota()
                update_cached_profile("claude", f_data)
                self.send_json({"success": True, "profile": "claude", "duration_ms": 5, "data": f_data, "error": None})
                return
            if profile == "codex":
                f_data = fetch_codex_quota()
                update_cached_profile("codex", f_data)
                self.send_json({"success": True, "profile": "codex", "duration_ms": 5, "data": f_data, "error": None})
                return
            if profile == "kiro":
                f_data = fetch_kiro_quota()
                update_cached_profile("kiro", f_data)
                self.send_json({"success": True, "profile": "kiro", "duration_ms": 5, "data": f_data, "error": None})
                return

            cached = load_cached_profiles().get(profile, {})
            was_auth_needed = not cached or cached.get("status") == "AUTH NEEDED"
            has_auth = check_profile_auth_token(profile)

            # Post-login validation probe:
            if has_auth and was_auth_needed:
                ping_res = execute_ping_profile(profile)
                if ping_res.get("is_appeal") or ping_res.get("status") == "DISABLED":
                    err_id = ping_res.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                    record_profile_disabled(profile, err_id)
                    formatted = format_profile_for_dashboard(profile, ping_res)
                    update_cached_profile(profile, formatted)
                    self.send_json({
                        "success": False,
                        "isAppeal": True,
                        "status": "DISABLED",
                        "profile": profile,
                        "data": formatted,
                        "error": ping_res.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                    })
                    return

            result = fetch_quota_for_profile(profile)
            formatted = format_profile_for_dashboard(profile, result)
            update_cached_profile(profile, formatted)
            if result.get("is_appeal") or result.get("status") == "DISABLED":
                self.send_json({
                    "success": False,
                    "isAppeal": True,
                    "status": "DISABLED",
                    "profile": profile,
                    "data": formatted,
                    "error": result.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                })
                return
            if result.get("status") == "AUTH NEEDED" or not result.get("success"):
                self.send_json({
                    "success": False,
                    "isAuthNeeded": True,
                    "status": "AUTH NEEDED",
                    "profile": profile,
                    "data": formatted,
                    "error": result.get("error", "Profile chưa đăng nhập CLI")
                })
                return
            self.send_json({
                "success": True,
                "profile": profile,
                "duration_ms": int(result.get("duration", 0) * 1000),
                "data": formatted,
                "error": None
            })
            return

        if path == "/api/ping":
            profile = query.get("profile", ["danhdue"])[0]
            force = query.get("force", ["0"])[0] in ("1", "true", "True")
            ping_res = execute_ping_profile(profile, force=force)
            if profile == "claude":
                f_data = fetch_claude_quota()
                update_cached_profile("claude", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "claude",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return
            if profile == "codex":
                f_data = fetch_codex_quota()
                update_cached_profile("codex", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "codex",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return
            if profile == "kiro":
                f_data = fetch_kiro_quota()
                update_cached_profile("kiro", f_data)
                self.send_json({
                    "success": ping_res.get("success", False),
                    "profile": "kiro",
                    "duration_ms": ping_res.get("duration_ms", 10),
                    "data": f_data,
                    "message": ping_res.get("message"),
                    "skipped": ping_res.get("skipped", False)
                })
                return

            if ping_res.get("is_appeal") or ping_res.get("status") == "DISABLED":
                err_id = ping_res.get("error_id") or "856698b5-d43c-4198-962b-4db7fc3c4adb-2"
                record_profile_disabled(profile, err_id)
                formatted = format_profile_for_dashboard(profile, ping_res)
                update_cached_profile(profile, formatted)
                self.send_json({
                    "success": False,
                    "isAppeal": True,
                    "status": "DISABLED",
                    "profile": profile,
                    "data": formatted,
                    "error": ping_res.get("error", "Tài khoản bị vô hiệu hóa (Submit an appeal)")
                })
                return
            post_q = ping_res.get("post_quota")
            if isinstance(post_q, dict) and not post_q.get("groups"):
                formatted = apply_activated_countdown_estimates(post_q, datetime.datetime.now(datetime.timezone.utc))
                update_cached_profile(profile, formatted)
            else:
                result = post_q if (isinstance(post_q, dict) and post_q.get("groups")) else fetch_quota_for_profile(profile)
                formatted = format_profile_for_dashboard(profile, result) if result.get("groups") else load_cached_profiles().get(profile, {})
                if isinstance(formatted, dict):
                    formatted = apply_activated_countdown_estimates(formatted, datetime.datetime.now(datetime.timezone.utc))
                    update_cached_profile(profile, formatted)
            self.send_json({
                "success": bool(ping_res.get("success", False)),
                "profile": profile,
                "duration_ms": ping_res.get("duration_ms", 500),
                "data": formatted,
                "message": ping_res.get("message"),
                "error": ping_res.get("error"),
                "details": ping_res.get("details", {}),
                "skipped": ping_res.get("skipped", False),
            })
            return

        if path == "/api/refresh-all":
            is_auto = query.get("auto", ["0"])[0] in ("1", "true", "True")
            raw_query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            try:
                requested_profiles = parse_refresh_profiles_query(raw_query)
            except ValueError as exc:
                self.send_json({"success": False, "error": str(exc)}, status=400)
                return

            now = int(time.time())
            last_rf = get_last_refresh_all_time()
            if last_rf == 0:
                last_rf = now
                record_refresh_all_time(last_rf)
            elapsed = max(0, now - last_rf)

            # 30-Minute guard for automated init & reload triggers:
            if is_auto and elapsed < GLOBAL_REFRESH_INTERVAL_SECONDS:
                self.send_json({
                    "success": True,
                    "skipped": True,
                    "reason": f"Throttled: last refresh was {elapsed // 60}m ago (< 30m). Manual refresh required.",
                    "profiles": load_cached_profiles(),
                    "last_refresh_all": last_rf,
                    "elapsed_seconds": elapsed,
                    "can_auto_refresh": False,
                    "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS
                })
                return

            is_filtered = requested_profiles is not None
            requested_set = set(requested_profiles or [])
            formatted_all = {}

            # 1. AI Providers: Claude, Codex & Kiro
            if not is_filtered or "claude" in requested_set:
                c_data = fetch_claude_quota()
                formatted_all["claude"] = c_data
                update_cached_profile("claude", c_data)

            if not is_filtered or "codex" in requested_set:
                x_data = fetch_codex_quota()
                formatted_all["codex"] = x_data
                update_cached_profile("codex", x_data)

            if not is_filtered or "kiro" in requested_set:
                k_data = fetch_kiro_quota()
                formatted_all["kiro"] = k_data
                update_cached_profile("kiro", k_data)

            # 2. Antigravity Profiles
            all_agy_profiles = get_all_profiles()
            if is_filtered:
                known_agy_set = set(all_agy_profiles)
                target_agy_profiles = [
                    p
                    for p in (requested_profiles or [])
                    if p not in ("claude", "codex", "kiro") and p in known_agy_set
                ]
            else:
                target_agy_profiles = all_agy_profiles

            if target_agy_profiles:
                results = scan_all_profiles_parallel(target_agy_profiles)
                for r in results:
                    p = r["profile"]
                    f_data = format_profile_for_dashboard(p, r)
                    formatted_all[p] = f_data
                    update_cached_profile(p, f_data)

            if not is_filtered:
                record_refresh_all_time(now)
                resp_last_rf = now
                resp_elapsed = 0
                resp_can_auto = False
            else:
                resp_last_rf = last_rf
                resp_elapsed = elapsed
                resp_can_auto = elapsed >= GLOBAL_REFRESH_INTERVAL_SECONDS

            self.send_json({
                "success": True,
                "skipped": False,
                "filtered": is_filtered,
                "refreshed_count": len(formatted_all),
                "refreshed_profiles": list(formatted_all.keys()),
                "profiles": formatted_all,
                "last_refresh_all": resp_last_rf,
                "elapsed_seconds": resp_elapsed,
                "can_auto_refresh": resp_can_auto,
                "interval_seconds": GLOBAL_REFRESH_INTERVAL_SECONDS
            })
            return

        if path == "/api/login":
            profile = query.get("profile", [""])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return
            if profile == "claude":
                cli_cmd = "claude auth login"
            elif profile == "codex":
                cli_cmd = "codex auth login"
            elif profile == "kiro":
                cli_cmd = "kiro-cli login"
            else:
                cli_cmd = f"{profile}-cli"
            osa = f'''tell application "Terminal"
                activate
                do script "{cli_cmd}"
            end tell'''
            subprocess.run(["osascript", "-e", osa], env=build_clean_host_env(), capture_output=True)
            self.send_json({"success": True, "message": f"Terminal opened for {profile} login"})
            return

        if path == "/api/open-cli":
            profile = query.get("profile", ["danhdue"])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return
            if profile == "claude":
                cli_cmd = "claude"
            elif profile == "codex":
                cli_cmd = "codex"
            elif profile == "kiro":
                cli_cmd = "kiro-cli"
            else:
                target_profile = "danhdue" if profile == "default" else profile
                cli_cmd = f"source ~/.zshrc && ag_run {shlex.quote(target_profile)} cli"
            osa = f'''tell application "Terminal"
                activate
                do script "{cli_cmd}"
            end tell'''
            subprocess.run(["osascript", "-e", osa], env=build_clean_host_env(), capture_output=True)
            self.send_json({"success": True, "message": f"Terminal opened for {profile} CLI"})
            return

        if path == "/api/open-ide":
            profile = query.get("profile", ["danhdue"])[0]
            if not profile or not re.fullmatch(r"[a-zA-Z0-9_-]+", profile):
                self.send_json({"success": False, "error": "Invalid profile name"}, 400)
                return

            target_profile = "danhdue" if profile == "default" else profile
            clean_env = build_clean_host_env()

            # Trigger profile CLI command directly (e.g. 'danhdue', 'hau') from a sanitized host environment
            cmd = (
                "unset ELECTRON_RUN_AS_NODE ELECTRON_NO_ASAR TERM_PROGRAM TERM_PROGRAM_VERSION "
                "TERM_SESSION_ID AGY_PROFILE AGY_CLI_MODE ZDOTDIR VSCODE_GIT_IPC_HANDLE "
                "VSCODE_IPC_HOOK_CLI VSCODE_RESOLVING_ENVIRONMENT; "
                f"if type {target_profile} >/dev/null 2>&1; then {target_profile}; "
                f"else ag_run {shlex.quote(target_profile)}; fi"
            )
            subprocess.Popen(
                ["zsh", "-ic", cmd],
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            self.send_json({"success": True, "message": f"Đã kích hoạt lệnh '{target_profile}' mở Antigravity IDE"})
            return

        self.send_error(404, "API endpoint not found")


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


PID_FILE = Path("/tmp/agy_quota_server.pid")
LOG_FILE = Path("/tmp/agy_quota_server.log")


def is_server_alive(port: int = 8765) -> bool:
    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1.5)
        return req.status == 200
    except Exception:
        return False


def get_server_pid(port: int = 8765) -> int | None:
    if PID_FILE.is_file():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, 0)
            return pid
        except Exception:
            try:
                PID_FILE.unlink(missing_ok=True)
            except Exception:
                pass
    try:
        out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL).strip()
        if out:
            pids = [int(p) for p in out.split() if p.isdigit()]
            if pids:
                return pids[0]
    except Exception:
        pass
    return None


def stop_server(port: int = 8765) -> bool:
    pid = get_server_pid(port)
    alive = is_server_alive(port)
    if not pid and not alive:
        print(f"\n{AMBER}ℹ️ Quota Web Server hiện không chạy trên cổng {port}.{RESET}\n")
        return False

    print(f"\n{CYAN}🛑 Đang dừng Quota Web Server (PID {pid or 'unknown'})...{RESET}")
    killed = False
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            for _ in range(25):
                time.sleep(0.1)
                try:
                    os.kill(pid, 0)
                except OSError:
                    killed = True
                    break
            if not killed:
                os.kill(pid, signal.SIGKILL)
                killed = True
        except Exception:
            pass

    try:
        out = subprocess.check_output(["lsof", "-ti", f":{port}"], text=True, stderr=subprocess.DEVNULL).strip()
        for p in out.split():
            if p.isdigit():
                try:
                    os.kill(int(p), signal.SIGKILL)
                    killed = True
                except Exception:
                    pass
    except Exception:
        pass

    PID_FILE.unlink(missing_ok=True)
    print(f"{BOLD}{GREEN}✅ Đã dừng Quota Web Server thành công.{RESET}\n")
    return True


def status_server(port: int = 8765):
    alive = is_server_alive(port)
    pid = get_server_pid(port)
    if alive:
        pid_str = f" (PID {pid})" if pid else ""
        print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đang HOẠT ĐỘNG{pid_str}:{RESET}")
        print(f"     URL : {WHITE}http://127.0.0.1:{port}{RESET}")
        print(f"     Logs: {GRAY}{LOG_FILE}{RESET}")
        print(f"  💡 Mở dashboard: {CYAN}check-quota --ui{RESET}")
        print(f"  🛑 Dừng server : {AMBER}check-quota --stop{RESET}\n")
    else:
        print(f"\n{GRAY}ℹ️ Quota Web Server hiện KHÔNG HOẠT ĐỘNG.{RESET}")
        print(f"  🚀 Chạy {CYAN}check-quota --ui{RESET} để khởi động ngầm.\n")


def _get_running_server_code_mtime(port: int = 8765) -> int | None:
    """Query running daemon /api/status for its server_code_mtime."""
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=1.5) as resp:
            if getattr(resp, "status", 200) != 200:
                return None
            payload = json.loads(resp.read().decode("utf-8"))
            val = payload.get("server_code_mtime") if isinstance(payload, dict) else None
            return int(val) if isinstance(val, (int, float)) else None
    except Exception:
        return None


def start_server_daemon(port: int = 8765, auto_open: bool = True):
    if is_server_alive(port):
        current_mtime = int(Path(__file__).stat().st_mtime)
        running_mtime = _get_running_server_code_mtime(port)
        if running_mtime == current_mtime:
            pid = get_server_pid(port)
            pid_str = f" (PID {pid})" if pid else ""
            print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đã đang hoạt động{pid_str} tại:{RESET} {WHITE}http://127.0.0.1:{port}{RESET}")
            if auto_open:
                print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt...{RESET}\n")
                subprocess.run(["open", f"http://127.0.0.1:{port}"])
            print(f"  {GRAY}💡 Dừng server bất cứ lúc nào bằng lệnh: {WHITE}check-quota --stop{RESET}\n")
            return
        stop_server(port)

    # Cleanup any stuck PID/port
    if PID_FILE.is_file() or get_server_pid(port):
        stop_server(port)

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    log_fp = open(LOG_FILE, "a", encoding="utf-8")
    log_fp.write(f"\n--- Quota Server daemon starting at {datetime.datetime.now().isoformat()} ---\n")
    log_fp.flush()

    script_path = str(Path(__file__).resolve())
    cmd = [sys.executable, script_path, "_serve", "--port", str(port)]
    proc = subprocess.Popen(
        cmd,
        env=build_clean_host_env(),
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=log_fp,
        stderr=log_fp,
        close_fds=True
    )
    PID_FILE.write_text(str(proc.pid))

    ready = False
    for _ in range(35):
        time.sleep(0.1)
        if is_server_alive(port):
            ready = True
            break
        if proc.poll() is not None:
            break

    if not ready:
        print(f"\n{RED}❌ Không thể khởi động Quota Web Server ngầm.{RESET}")
        print(f"  Vui lòng xem chi tiết lỗi tại: {WHITE}{LOG_FILE}{RESET}\n")
        return

    url = f"http://127.0.0.1:{port}"
    print(f"\n{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"{BOLD}{GREEN}  🚀 AI MULTI-PROFILE QUOTA LIVE WEB SERVER (DAEMON){RESET}")
    print(f"     URL : {WHITE}{url}{RESET}")
    print(f"     PID : {WHITE}{proc.pid}{RESET}  |  Logs: {GRAY}{LOG_FILE}{RESET}")
    print(f"{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"  ✨ {BOLD}Chạy ngầm độc lập (Detached Process):{RESET}")
    print(f"     • Bạn có thể {BOLD}{GREEN}tắt Terminal này hoàn toàn{RESET}, web vẫn tiếp tục hoạt động!")
    print(f"     • Tự động kết nối và tương tác Live Refresh với 23 profiles.")
    print(f"     • Dừng server khi cần bằng lệnh: {BOLD}{AMBER}check-quota --stop{RESET}\n")

    if auto_open:
        print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt mặc định...{RESET}\n")
        subprocess.run(["open", url])


def run_internal_serve(port: int = 8765):
    # Ignore SIGHUP so terminal closing never kills the daemon
    if hasattr(signal, "SIGHUP"):
        signal.signal(signal.SIGHUP, signal.SIG_IGN)

    def handle_term(signum, frame):
        try:
            PID_FILE.unlink(missing_ok=True)
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_term)
    signal.signal(signal.SIGINT, handle_term)

    PID_FILE.write_text(str(os.getpid()))

    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingTCPServer(("127.0.0.1", p), QuotaDashboardHandler)
            port = p
            break
        except OSError:
            continue

    if not httpd:
        sys.stderr.write(f"Cannot bind to port {port}..{port+9}\n")
        sys.exit(1)

    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
        if not _RELOAD_PENDING:
            PID_FILE.unlink(missing_ok=True)
    if _RELOAD_PENDING:
        os.execv(sys.executable, [sys.executable, *sys.argv])


def run_quota_web_server(port: int = 8765, auto_open: bool = True):
    if is_server_alive(port):
        pid = get_server_pid(port)
        pid_str = f" (PID {pid})" if pid else ""
        print(f"\n{BOLD}{GREEN}⚡ Quota Web Server đã đang hoạt động{pid_str} tại:{RESET} {WHITE}http://127.0.0.1:{port}{RESET}")
        if auto_open:
            print(f"  {CYAN}🌐 Đang mở Quota Dashboard trong trình duyệt...{RESET}\n")
            subprocess.run(["open", f"http://127.0.0.1:{port}"])
        print(f"  {GRAY}💡 Dừng server bất cứ lúc nào bằng lệnh: {WHITE}check-quota --stop{RESET}\n")
        return

    httpd = None
    for p in range(port, port + 10):
        try:
            httpd = ThreadingTCPServer(("127.0.0.1", p), QuotaDashboardHandler)
            port = p
            break
        except OSError:
            continue

    if not httpd:
        print(f"\n{RED}❌ Không thể bind cổng từ {port} đến {port + 9}. Vui lòng thử lại.{RESET}\n")
        return

    PID_FILE.write_text(str(os.getpid()))
    url = f"http://127.0.0.1:{port}"
    print(f"\n{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"{BOLD}{GREEN}  🚀 AI MULTI-PROFILE QUOTA LIVE WEB SERVER (FOREGROUND){RESET}")
    print(f"     URL: {WHITE}{url}{RESET}")
    print(f"{BOLD}{CYAN}{'='*86}{RESET}")
    print(f"  ⚡ {BOLD}Tính năng tương tác trực tiếp (Interactive Endpoints):{RESET}")
    print(f"     • {CYAN}GET  /api/status{RESET}            : Xem quota tất cả 23 profiles")
    print(f"     • {CYAN}GET  /api/refresh?profile=p{RESET} : Live Refresh 110ms cho profile p")
    print(f"     • {CYAN}GET  /api/ping?profile=p{RESET}    : Gửi 1-token kích hoạt countdown 5H & tuần")
    print(f"     • {CYAN}GET  /api/refresh-all{RESET}       : Quét song song và cập nhật toàn bộ profiles")
    print(f"     • {CYAN}GET  /api/login?profile=p{RESET}   : Mở Terminal thực hiện p-cli để đăng nhập")
    print(f"     • {CYAN}GET  /api/open-cli?profile=p{RESET}: Mở Terminal chạy CLI cho profile p")
    print(f"     • {CYAN}GET  /api/open-ide?profile=p{RESET}: Mở Antigravity IDE (GUI) cho profile p")
    print(f"\n  🌐 Đang mở Quota Dashboard trên trình duyệt mặc định...")
    print(f"  💡 Nhấn {AMBER}Ctrl + C{RESET} trong Terminal để dừng server bất kỳ lúc nào.\n")

    if auto_open:
        subprocess.run(["open", url])

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{AMBER}🛑 Server đã dừng an toàn (Ctrl+C). Tạm biệt!{RESET}\n")
    finally:
        httpd.server_close()
        PID_FILE.unlink(missing_ok=True)


def main():
    args = sys.argv[1:]
    target = args[0] if args else None

    # Handle internal server runner
    if target == "_serve":
        port = 8765
        if "--port" in args:
            idx = args.index("--port")
            if idx + 1 < len(args) and args[idx + 1].isdigit():
                port = int(args[idx + 1])
        run_internal_serve(port=port)
        return

    # Handle stop
    if target in ("--stop", "stop", "-k", "--kill"):
        stop_server(port=8765)
        return

    # Handle status
    if target in ("--status", "status"):
        status_server(port=8765)
        return

    # Handle help
    if target in ("-h", "--help", "help"):
        print(f"\n{BOLD}{CYAN}Antigravity Quota CLI (check-quota / agy-quota){RESET}")
        print("Usage:")
        print("  check-quota                     Xem quota cho profile hiện tại")
        print("  check-quota <profile>           Xem quota cho profile cụ thể (e.g. danhdue, tess)")
        print("  check-quota all                 Quét và hiển thị chi tiết tất cả profiles")
        print("  check-quota all --table         Bảng tóm tắt gọn gàng 122 ký tự cho tất cả profiles")
        print("  check-quota ping <profile>      Gửi 1-token kích hoạt countdown 5H & tuần (Ping Model)")
        print("  check-quota refresh <profile>   Làm mới quota và đồng bộ session qua /usage")
        print("  check-quota --ui                Mở Quota Dashboard trực quan (chạy ngầm, tắt terminal thoải mái)")
        print("  check-quota --ui -f             Chạy Quota Dashboard ở foreground terminal (dành cho debug)")
        print("  check-quota --stop              Dừng Quota Dashboard Web Server đang chạy ngầm")
        print("  check-quota --status            Kiểm tra trạng thái Quota Web Server\n")
        return

    # Handle UI/Web Dashboard
    if target in ("--web", "--ui", "dashboard", "--dashboard", "web", "ui"):
        auto_open = "--no-open" not in args
        if "--static" in args or "--file" in args:
            found_dash = get_dashboard_html_path()
            if found_dash.is_file():
                print(f"\n{GREEN}🌐 Opening Quota Dashboard file in browser: {found_dash}{RESET}\n")
                subprocess.run(["open", str(found_dash)])
            else:
                print(f"\n{RED}❌ Quota dashboard file not found.{RESET}\n")
            return
        if "--foreground" in args or "-f" in args:
            run_quota_web_server(port=8765, auto_open=auto_open)
        else:
            start_server_daemon(port=8765, auto_open=auto_open)
        return

    # Detect default profile if none specified
    if not target or target == "current":
        env_profile = os.environ.get("AGY_PROFILE")
        if not env_profile:
            home = os.environ.get("HOME", "")
            if "antigravity_homes" in home:
                env_profile = os.path.basename(home)
            else:
                env_profile = "danhdue"
        target = env_profile

    if target in ("ping", "activate"):
        sub_target = args[1] if len(args) > 1 and not args[1].startswith("-") else "danhdue"
        force = "--force" in args or "-f" in args
        print(f"\n{CYAN}🎯 Kích hoạt phiên làm việc cho '{sub_target}' (force={force})...{RESET}")
        res = execute_ping_profile(sub_target, force=force)
        if res.get("skipped"):
            print(f"{AMBER}⏭️  {res.get('message')}{RESET}\n")
            return
        if res.get("success"):
            print(f"{GREEN}✅ {res.get('message')}{RESET}\n")
        else:
            print(f"{RED}❌ {res.get('error')}{RESET}\n")
        return

    if target in ("check-blocked", "test-blocked"):
        sub_target = args[1] if len(args) > 1 else "d3molt"
        print(f"\n{CYAN}⚡ Kiểm tra trạng thái tài khoản bị khóa '{sub_target}' (kèm Anti-Bot Jitter)...{RESET}")
        res = probe_blocked_profile(sub_target)
        if res.get("unblocked"):
            print(f"{BOLD}{GREEN}{res.get('message')}{RESET}\n")
        elif res.get("cooldown"):
            print(f"{AMBER}⏳ {res.get('error')}{RESET}\n")
        elif res.get("is_appeal"):
            print(f"{RED}🚫 {res.get('error')}{RESET}\n")
        else:
            print(f"{RED}❌ {res.get('error', 'Lỗi kiểm tra')}{RESET}\n")
        return

    if target == "refresh":
        sub_target = args[1] if len(args) > 1 else "danhdue"
        print(f"\n{CYAN}⚡ Running quick refresh for '{sub_target}'...{RESET}")
        if sub_target == "claude":
            c_data = fetch_claude_quota()
            update_cached_profile("claude", c_data)
            print(f"{GREEN}✅ Claude Code refreshed successfully!{RESET}\n")
            return
        if sub_target == "codex":
            x_data = fetch_codex_quota()
            update_cached_profile("codex", x_data)
            print(f"{GREEN}✅ OpenAI Codex refreshed successfully!{RESET}\n")
            return
        if sub_target == "kiro":
            k_data = fetch_kiro_quota()
            update_cached_profile("kiro", k_data)
            print(f"{GREEN}✅ Kiro CLI refreshed successfully!{RESET}\n")
            return
        ag_home = f"{REAL_HOME}/antigravity_homes/{sub_target}"
        if not os.path.isdir(ag_home):
            print(f"{RED}❌ Profile home not found: {ag_home}{RESET}\n")
            return
        t0 = time.time()
        post_q = fetch_quota_for_profile(sub_target)
        dur = int((time.time() - t0) * 1000)
        if post_q.get("status") == "AUTH NEEDED":
            print(f"{AMBER}⚠️ Profile '{sub_target}' chưa đăng nhập CLI. Vui lòng chạy '{sub_target}-cli' trong Terminal để đăng nhập trước.{RESET}\n")
            return
        if post_q.get("is_appeal") or post_q.get("status") == "DISABLED":
            formatted_dis = format_profile_for_dashboard(sub_target, post_q)
            update_cached_profile(sub_target, formatted_dis)
            print(f"\n{RED}🚫 LỖI: Tài khoản '{sub_target}' đã bị VÔ HIỆU HÓA do vi phạm Điều khoản dịch vụ!{RESET}")
            print(f"  {AMBER}Thông báo từ Google: This service has been disabled in this account for violation of Terms of Service.{RESET}")
            print(f"  {CYAN}👉 Vui lòng gửi đơn kháng nghị (Submit an appeal) tới Google để tiếp tục sử dụng:{RESET}")
            print(f"     {WHITE}https://docs.google.com/forms/d/e/1FAIpQLScOJWibQ_-hYuVv63kJTgEqlgAaOwRLGFTbXm-QY1gz8U0CGA/viewform{RESET}\n")
            return
        if post_q.get("success"):
            formatted = format_profile_for_dashboard(sub_target, post_q)
            update_cached_profile(sub_target, formatted)
            print(f"{GREEN}✅ Refreshed profile '{sub_target}' in {dur}ms! Session quota synchronized.{RESET}\n")
        else:
            err_msg = post_q.get("error", "Refresh failed")
            if "timed out" in str(err_msg).lower():
                print(f"{RED}❌ Refresh timed out (45s){RESET}\n")
            else:
                print(f"{RED}❌ Refresh failed ({dur}ms): {err_msg}{RESET}\n")
        return

    if target == "all":
        filter_providers = "--providers" in args
        filter_active = "--active" in args
        filter_login = "--login" in args or "--auth-needed" in args
        filter_blocked = "--blocked" in args or "--disabled" in args

        if filter_providers:
            print(f"\n{BOLD}{CYAN}=== AI AGENT PROVIDERS (CLAUDE, CODEX, KIRO) ==={RESET}")
            try:
                c_data = fetch_claude_quota()
                print_claude_card(c_data)
            except Exception:
                pass
            try:
                o_data = fetch_codex_quota()
                print_codex_card(o_data)
            except Exception:
                pass
            try:
                k_data = fetch_kiro_quota()
                print_kiro_card(k_data)
            except Exception:
                pass
            return

        profiles = get_all_profiles()

        print(f"{CYAN}Scanning quota for {len(profiles)} profiles in parallel...{RESET}")
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_profile = {}
            for p in profiles:
                future_to_profile[executor.submit(fetch_quota_for_profile, p, False, True)] = p
                time.sleep(0.2)
            for future in as_completed(future_to_profile):
                res = future.result()
                results.append(res)
                print(f"  • {res['profile']}: {'DONE' if res.get('success') else 'FAILED'}")

        results.sort(key=lambda x: profiles.index(x["profile"]) if x["profile"] in profiles else 999)
        for r in results:
            formatted = format_profile_for_dashboard(r["profile"], r)
            update_cached_profile(r["profile"], formatted)

        if filter_active:
            results = [r for r in results if r.get("success")]
        elif filter_login:
            results = [r for r in results if not r.get("success") and not r.get("is_appeal") and r.get("status") != "DISABLED"]
        elif filter_blocked:
            results = [r for r in results if r.get("is_appeal") or r.get("status") == "DISABLED"]

        if "--table" in args:
            print_all_summary(results, show_providers=(not filter_active and not filter_login and not filter_blocked))
        else:
            if not filter_active and not filter_login and not filter_blocked:
                try:
                    c_data = fetch_claude_quota()
                    print_claude_card(c_data)
                except Exception:
                    pass
                try:
                    o_data = fetch_codex_quota()
                    print_codex_card(o_data)
                except Exception:
                    pass
                try:
                    k_data = fetch_kiro_quota()
                    print_kiro_card(k_data)
                except Exception:
                    pass
            for r in results:
                print_dashboard_cards(r)
    elif target in ("claude", "anthropic"):
        result = fetch_claude_quota()
        print_claude_card(result)
    elif target in ("codex", "openai"):
        result = fetch_codex_quota()
        print_codex_card(result)
    elif target == "kiro":
        result = fetch_kiro_quota()
        print_kiro_card(result)
    else:
        if target.startswith("-"):
            print(f"\n{RED}❌ Lỗi: Đối số hoặc cờ không hợp lệ: '{target}'. Gõ 'check-quota --help' để xem hướng dẫn.{RESET}\n")
            return
        if not is_valid_antigravity_profile(target):
            print(f"\n{RED}❌ Lỗi: Profile '{target}' không tồn tại hoặc không phải là profile Antigravity hợp lệ.{RESET}\n")
            return
        # Single profile dashboard
        result = fetch_quota_for_profile(target)
        print_dashboard_cards(result)


if __name__ == "__main__":
    main()
