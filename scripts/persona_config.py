#!/usr/bin/env python3
"""Layered persona configuration, dispatch argv/env builders, and failure classification."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any

PERSONAS: tuple[str, ...] = ("ai_architect_reviewer", "orchestrator", "programmer")
ALLOWED_CLIS: frozenset[str] = frozenset({"agy", "claude", "codex", "kiro"})
ALLOWED_QUOTA_POOLS: frozenset[str] = frozenset({"argonWeekly", "gemini5h", "provider"})
AGY_QUOTA_POOLS: frozenset[str] = frozenset({"argonWeekly", "gemini5h"})
SCHEMA_VERSION: int = 1
DEFAULT_TURN_BUDGET: int = 8
DEFAULT_LOW_QUOTA_HOURS: float = 5.0
DEFAULT_MAX_TASK_REVIEW_PASSES: int = 2
DEFAULT_MAX_FIX_PASSES: int = 1
DEFAULT_MAX_PRINCIPAL_REVIEW_PASSES: int = 3
DEFAULT_MAX_CROSS_MODEL_REVIEW_PASSES: int = 3
REVIEW_PRIORITY_PROVIDERS: tuple[str, ...] = ("claude", "codex", "kiro", "agy")
REVIEW_PROVIDERS: tuple[str, ...] = ("claude", "codex", "kiro", "agy", "ollama")
REVIEW_THINKING_LEVELS: tuple[str, ...] = (
    "none",
    "light",
    "low",
    "medium",
    "high",
    "xhigh",
    "extra-high",
)
DEFAULT_REVIEW_QUOTA_THRESHOLDS: dict[str, float] = {
    "5h_min_fraction": 0.15,
    "7d_min_fraction": 0.02,
    "kiro_min_fraction": 0.03,
    "kiro_min_credits": 15.0,
    "agy_argon_min_fraction": 0.10,
}
DEFAULT_REVIEW_PROVIDERS: dict[str, dict[str, str]] = {
    "claude": {"model": "claude-opus", "effort": "high"},
    "codex": {"model": "codex-gpt", "effort": "high"},
    "kiro": {"model": "kiro-opus", "effort": "high"},
    "agy": {"model": "argon", "effort": "high"},
    "ollama": {
        "model": "gemma4:31b-it-qat",
        "effort": "high",
        "host": "http://localhost:11434",
    },
}

KIT_DEFAULTS_PATH: Path = Path(__file__).resolve().with_name("personas.default.json")
_LAYER_RANK: dict[str, int] = {
    "kit": 0,
    "legacy": 1,
    "global": 2,
    "project": 3,
    "cli": 4,
}
_ALLOWED_OVERRIDE_FIELDS: frozenset[str] = frozenset(
    {"model", "effort", "fallback_model", "profile"}
)
_ALLOWED_CLI_OVERRIDE_FIELDS: frozenset[str] = frozenset(
    {"model", "effort", "fallback_model"}
)
_PROFILE_NAME_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9_-]+$")
_ALLOWED_TOP_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "active_preset",
        "models",
        "presets",
        "overrides",
        "checkpoint_policy",
        "low_quota",
        "max_task_review_passes",
        "max_fix_passes",
        "max_principal_review_passes",
        "max_cross_model_review_passes",
        "review",
    }
)
_ALLOWED_REVIEW_KEYS: frozenset[str] = frozenset(
    {"provider_priority", "providers", "quota_thresholds"}
)
_ALLOWED_REVIEW_PROVIDER_FIELDS: frozenset[str] = frozenset(
    {"model", "effort", "thinking_level", "host"}
)
_FRACTION_THRESHOLD_KEYS: frozenset[str] = frozenset(
    {
        "5h_min_fraction",
        "7d_min_fraction",
        "kiro_min_fraction",
        "agy_argon_min_fraction",
    }
)
_REVIEW_THINKING_LEVEL_SET: frozenset[str] = frozenset(REVIEW_THINKING_LEVELS)
_REVIEW_PRIORITY_SET: frozenset[str] = frozenset(REVIEW_PRIORITY_PROVIDERS)
_REVIEW_PROVIDER_SET: frozenset[str] = frozenset(REVIEW_PROVIDERS)
_CODEX_EFFORT_MAP: dict[str, str] = {
    "light": "low",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "xhigh": "extra-high",
    "extra-high": "extra-high",
    "none": "none",
}
_MODEL_FAILURE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pat, re.IGNORECASE)
    for pat in (
        r"CLI binary '[^']+' not found on PATH",
        r"command not found",
        r"Failed to spawn process",
        r"\b429\b.*too many requests",
        r"resource_?exhausted",
        r"quota (exceeded|exhausted)",
        r"rate.?limit(ed)? exceeded",
        r"usage limit",
        r"\b401\b.*unauthori[sz]ed",
        r"\b403\b.*forbidden",
        r"not authenticated",
        r"please (log|sign) in",
        r"login required",
        r"invalid model selection",
        r"not recognized as a known model",
    )
)


class PersonaConfigError(ValueError):
    """Raised when persona configuration or resolution validation fails."""


@dataclass(frozen=True)
class PersonaBinding:
    """Resolved model, CLI, quota pool, and layer provenance for a persona."""

    persona: str
    alias: str
    cli: str
    model_id: str
    effort: str
    quota_pool: str
    fallback_alias: str | None
    sources: dict[str, str]
    profile: str | None = None


@dataclass(frozen=True)
class ReviewLimits:
    """Resolved independent pass limits and source layer provenance."""

    max_task_review_passes: int
    max_fix_passes: int
    max_principal_review_passes: int
    max_cross_model_review_passes: int
    sources: dict[str, str]


@dataclass(frozen=True)
class ReviewProviderBinding:
    """Resolved external review provider model, effort, optional host, and source."""

    provider: str
    model: str
    model_id: str
    effort: str
    host: str | None
    source: str


@dataclass(frozen=True)
class ResolvedReviewConfig:
    """Resolved external review priority, providers, quota thresholds, and pass limits."""

    provider_priority: tuple[str, ...]
    providers: dict[str, ReviewProviderBinding]
    quota_thresholds: dict[str, float]
    limits: ReviewLimits
    sources: dict[str, str]

    def max_rounds_for_kind(self, kind: str) -> int:
        """Return the configured round cap for 'principal', 'code', or 'epic'."""
        if kind == "principal":
            return self.limits.max_principal_review_passes
        if kind in ("code", "epic"):
            return self.limits.max_cross_model_review_passes
        raise PersonaConfigError(
            f"Unknown review kind '{kind}'; expected 'principal', 'code', or 'epic'"
        )


def get_real_home(real_home: Path | str | None = None) -> Path:
    """Resolve the host user's real HOME directory even inside an isolated profile."""
    if real_home is not None:
        return Path(real_home).expanduser()
    current = os.path.expanduser("~")
    if "/antigravity_homes/" in current:
        return Path(current.split("/antigravity_homes/", 1)[0])
    if current.endswith("/antigravity_homes"):
        return Path(current[: -len("/antigravity_homes")])
    env_real = os.environ.get("REAL_HOME")
    return Path(env_real).expanduser() if env_real else Path(current)


def global_config_path(real_home: Path | str | None = None) -> Path:
    """Return the global persona configuration path under REAL_HOME."""
    return get_real_home(real_home) / ".d3nexus" / "personas.json"


def project_config_path(project_root: Path) -> Path:
    """Return the project-scoped persona configuration path."""
    return Path(project_root) / ".agents" / "config" / "personas.json"


def config_path_for_scope(
    project_root: Path,
    scope: str,
    *,
    real_home: Path | str | None = None,
) -> Path:
    """Return the configuration file path for 'global' or 'project' scope."""
    if scope == "global":
        return global_config_path(real_home)
    if scope == "project":
        return project_config_path(project_root)
    raise PersonaConfigError(f"Invalid scope '{scope}'; expected 'global' or 'project'")


def _validate_task_review_limits(cfg: Mapping[str, Any]) -> None:
    max_rev = cfg.get("max_task_review_passes", DEFAULT_MAX_TASK_REVIEW_PASSES)
    if type(max_rev) is not int or max_rev < 1:
        raise PersonaConfigError(
            f"Invalid max_task_review_passes '{max_rev}'; must be a positive integer"
        )
    max_fix = cfg.get("max_fix_passes", DEFAULT_MAX_FIX_PASSES)
    if type(max_fix) is not int or max_fix < 0:
        raise PersonaConfigError(
            f"Invalid max_fix_passes '{max_fix}'; must be a non-negative integer"
        )
    max_principal = cfg.get(
        "max_principal_review_passes", DEFAULT_MAX_PRINCIPAL_REVIEW_PASSES
    )
    if type(max_principal) is not int or max_principal < 1:
        raise PersonaConfigError(
            f"Invalid max_principal_review_passes '{max_principal}'; "
            "must be a positive integer"
        )
    max_cross = cfg.get(
        "max_cross_model_review_passes", DEFAULT_MAX_CROSS_MODEL_REVIEW_PASSES
    )
    if type(max_cross) is not int or max_cross < 1:
        raise PersonaConfigError(
            f"Invalid max_cross_model_review_passes '{max_cross}'; "
            "must be a positive integer"
        )


def _is_valid_ollama_host(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    if not stripped.startswith(("http://", "https://")):
        return False
    return bool(stripped.split("://", 1)[1])


def _normalize_review_provider_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    if "model" in entry:
        normalized["model"] = entry["model"]
    if "effort" in entry:
        normalized["effort"] = entry["effort"]
    elif "thinking_level" in entry:
        normalized["effort"] = entry["thinking_level"]
    if "host" in entry:
        normalized["host"] = entry["host"]
    return normalized


def _validate_review_priority(priority: Any) -> tuple[str, ...]:
    if not isinstance(priority, list) or not priority:
        raise PersonaConfigError(
            "Invalid review.provider_priority; must be a non-empty list of providers"
        )
    seen: set[str] = set()
    validated: list[str] = []
    for item in priority:
        if not isinstance(item, str) or item not in _REVIEW_PRIORITY_SET:
            raise PersonaConfigError(
                f"Invalid provider '{item}' in review.provider_priority; "
                f"allowed: {', '.join(REVIEW_PRIORITY_PROVIDERS)}"
            )
        if item in seen:
            raise PersonaConfigError(
                f"Duplicate provider '{item}' in review.provider_priority"
            )
        seen.add(item)
        validated.append(item)
    return tuple(validated)


def _validate_review_quota_thresholds(thresholds: Any) -> dict[str, float]:
    if not isinstance(thresholds, Mapping):
        raise PersonaConfigError(
            "Configuration 'review.quota_thresholds' must be an object"
        )
    validated: dict[str, float] = {}
    for key, val in thresholds.items():
        if key not in DEFAULT_REVIEW_QUOTA_THRESHOLDS:
            raise PersonaConfigError(
                f"Unknown key '{key}' in review.quota_thresholds; "
                f"allowed: {', '.join(DEFAULT_REVIEW_QUOTA_THRESHOLDS)}"
            )
        if (
            isinstance(val, bool)
            or not isinstance(val, (int, float))
            or not math.isfinite(val)
        ):
            raise PersonaConfigError(
                f"Invalid review.quota_thresholds.{key} '{val}'; "
                "must be a finite number"
            )
        fval = float(val)
        if key in _FRACTION_THRESHOLD_KEYS:
            if not 0.0 <= fval <= 1.0:
                raise PersonaConfigError(
                    f"Invalid review.quota_thresholds.{key} '{val}'; "
                    "must be in [0.0, 1.0]"
                )
        elif fval < 0.0:
            raise PersonaConfigError(
                f"Invalid review.quota_thresholds.{key} '{val}'; must be >= 0.0"
            )
        validated[key] = fval
    return validated


def _resolve_review_provider_model(
    provider: str,
    model: str,
    effort: str,
    models: Mapping[str, Any],
) -> tuple[str, str]:
    trimmed = model.strip()
    if trimmed in models:
        entry = models[trimmed]
        alias_cli = str(entry["cli"])
        if alias_cli != provider:
            raise PersonaConfigError(
                f"Review provider '{provider}' cannot use model alias '{trimmed}' "
                f"(belongs to cli '{alias_cli}', expected '{provider}')"
            )
        entry_efforts = entry["efforts"]
        template_id = str(entry["id"])
        if entry_efforts == ["none"]:
            return template_id, "none"
        if "{effort}" in template_id:
            if effort not in entry_efforts:
                raise PersonaConfigError(
                    f"Unsupported effort '{effort}' for review provider '{provider}' "
                    f"model alias '{trimmed}'; allowed: {', '.join(entry_efforts)}"
                )
            return template_id.replace("{effort}", effort), effort
        return template_id, effort
    return trimmed, effort


def _validate_review_section(
    review: Any,
    models: Mapping[str, Any] | None = None,
    *,
    partial: bool = False,
) -> None:
    if not isinstance(review, Mapping):
        raise PersonaConfigError("Configuration 'review' must be an object")
    unknown_keys = set(review) - _ALLOWED_REVIEW_KEYS
    if unknown_keys:
        bad = min(unknown_keys)
        raise PersonaConfigError(f"Unknown key '{bad}' in configuration 'review'")
    if "provider_priority" in review:
        _validate_review_priority(review["provider_priority"])
    if "quota_thresholds" in review:
        _validate_review_quota_thresholds(review["quota_thresholds"])
    if "providers" in review:
        providers = review["providers"]
        if not isinstance(providers, Mapping):
            raise PersonaConfigError(
                "Configuration 'review.providers' must be an object"
            )
        for provider, entry in providers.items():
            if provider not in _REVIEW_PROVIDER_SET:
                raise PersonaConfigError(
                    f"Unknown review provider '{provider}' in review.providers; "
                    f"allowed: {', '.join(REVIEW_PROVIDERS)}"
                )
            if not isinstance(entry, Mapping):
                raise PersonaConfigError(
                    f"Configuration 'review.providers.{provider}' must be an object"
                )
            bad_fields = set(entry) - _ALLOWED_REVIEW_PROVIDER_FIELDS
            if bad_fields:
                bad = min(bad_fields)
                raise PersonaConfigError(
                    f"Unknown field '{bad}' in review.providers.{provider}"
                )
            if not partial or "model" in entry:
                model_val = entry.get("model")
                if not isinstance(model_val, str) or not model_val.strip():
                    raise PersonaConfigError(
                        f"Invalid model '{model_val}' in review.providers.{provider}.model; "
                        "must be a non-empty string"
                    )
            if "effort" in entry:
                eff_val = entry["effort"]
                if (
                    not isinstance(eff_val, str)
                    or eff_val not in _REVIEW_THINKING_LEVEL_SET
                ):
                    raise PersonaConfigError(
                        f"Invalid effort '{eff_val}' in review.providers.{provider}.effort; "
                        f"allowed: {', '.join(REVIEW_THINKING_LEVELS)}"
                    )
            if "thinking_level" in entry:
                tl_val = entry["thinking_level"]
                if (
                    not isinstance(tl_val, str)
                    or tl_val not in _REVIEW_THINKING_LEVEL_SET
                ):
                    raise PersonaConfigError(
                        f"Invalid thinking_level '{tl_val}' in "
                        f"review.providers.{provider}.thinking_level; "
                        f"allowed: {', '.join(REVIEW_THINKING_LEVELS)}"
                    )
            if "host" in entry:
                if provider != "ollama":
                    raise PersonaConfigError(
                        f"Field 'host' is only allowed for review provider 'ollama', "
                        f"not '{provider}' (review.providers.{provider}.host)"
                    )
                if not _is_valid_ollama_host(entry["host"]):
                    raise PersonaConfigError(
                        f"Invalid host '{entry['host']}' in review.providers.ollama.host; "
                        "must start with http:// or https://"
                    )
            if models is not None and "model" in entry:
                norm = _normalize_review_provider_entry(entry)
                eff = str(norm.get("effort", "high"))
                _resolve_review_provider_model(
                    provider, str(norm["model"]).strip(), eff, models
                )


def _read_layer_json(path: Path, *, required: bool = False) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise PersonaConfigError(f"Missing required persona config file: {path}")
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PersonaConfigError(
            f"Failed to read persona config '{path}': {exc}"
        ) from exc
    if not isinstance(raw, dict):
        raise PersonaConfigError(f"Persona config '{path}' must be a JSON object")
    if "schema_version" in raw:
        sv = raw["schema_version"]
        if type(sv) is not int or sv != SCHEMA_VERSION:
            raise PersonaConfigError(
                f"Unsupported schema_version '{sv}' in '{path}'; expected {SCHEMA_VERSION}"
            )
    unknown_keys = set(raw) - _ALLOWED_TOP_KEYS
    if unknown_keys:
        bad = min(unknown_keys)
        raise PersonaConfigError(f"Unknown top-level key '{bad}' in '{path}'")
    _validate_task_review_limits(raw)
    if "review" in raw:
        _validate_review_section(raw["review"], models=None, partial=True)
    return raw


def _merge_review_section(
    base: Mapping[str, Any], overlay: Mapping[str, Any]
) -> dict[str, Any]:
    merged_review = copy.deepcopy(dict(base))
    for rkey, rval in overlay.items():
        if (
            rkey == "providers"
            and isinstance(merged_review.get("providers"), dict)
            and isinstance(rval, Mapping)
        ):
            merged_provs = copy.deepcopy(merged_review["providers"])
            for provider, p_entry in rval.items():
                if isinstance(p_entry, Mapping):
                    norm_entry = _normalize_review_provider_entry(p_entry)
                    if isinstance(merged_provs.get(provider), dict):
                        merged_provs[provider] = _deep_merge(
                            merged_provs[provider], norm_entry
                        )
                    else:
                        merged_provs[provider] = copy.deepcopy(norm_entry)
                else:
                    merged_provs[provider] = copy.deepcopy(p_entry)
            merged_review["providers"] = merged_provs
        elif isinstance(merged_review.get(rkey), dict) and isinstance(rval, Mapping):
            merged_review[rkey] = _deep_merge(merged_review[rkey], rval)
        else:
            merged_review[rkey] = copy.deepcopy(rval)
    return merged_review


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if (
            key == "models"
            and isinstance(result.get(key), dict)
            and isinstance(value, Mapping)
        ):
            merged_models = copy.deepcopy(result[key])
            for alias, entry in value.items():
                if isinstance(entry, Mapping) and {"cli", "id", "efforts"}.issubset(
                    entry
                ):
                    merged_models[alias] = copy.deepcopy(dict(entry))
                elif isinstance(merged_models.get(alias), dict) and isinstance(
                    entry, Mapping
                ):
                    merged_models[alias] = _deep_merge(merged_models[alias], entry)
                else:
                    merged_models[alias] = copy.deepcopy(entry)
            result[key] = merged_models
        elif (
            key == "review"
            and isinstance(result.get(key), dict)
            and isinstance(value, Mapping)
        ):
            result[key] = _merge_review_section(result[key], value)
        elif isinstance(result.get(key), dict) and isinstance(value, Mapping):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def derive_quota_pool(entry: Mapping[str, Any], alias: str = "<model>") -> str:
    """Validate explicit quota_pool or derive it from the model entry's cli and id."""
    cli = entry.get("cli")
    if not isinstance(cli, str) or cli not in ALLOWED_CLIS:
        raise PersonaConfigError(f"Invalid cli '{cli}' for model '{alias}'")
    explicit = entry.get("quota_pool")
    if explicit is not None:
        if not isinstance(explicit, str) or explicit not in ALLOWED_QUOTA_POOLS:
            raise PersonaConfigError(
                f"Invalid quota_pool '{explicit}' for model '{alias}'"
            )
        if cli == "agy" and explicit not in AGY_QUOTA_POOLS:
            raise PersonaConfigError(
                f"Invalid quota_pool '{explicit}' for agy model '{alias}'; "
                "expected 'argonWeekly' or 'gemini5h'"
            )
        if cli != "agy" and explicit != "provider":
            raise PersonaConfigError(
                f"Invalid quota_pool '{explicit}' for {cli} model '{alias}'; "
                "expected 'provider'"
            )
        return explicit
    if cli == "agy":
        model_id = str(entry.get("id", "")).lower()
        if "argon" in model_id or ("orchestrator" in model_id and "g1-pro" in model_id):
            return "argonWeekly"
        return "gemini5h"
    return "provider"


def _validate_model_entry(alias: str, entry: Any) -> None:
    if not isinstance(alias, str) or not alias.strip():
        raise PersonaConfigError(f"Invalid model alias '{alias}'")
    if not isinstance(entry, Mapping):
        raise PersonaConfigError(f"Model entry '{alias}' must be an object")
    cli = entry.get("cli")
    if not isinstance(cli, str) or cli not in ALLOWED_CLIS:
        raise PersonaConfigError(
            f"Unsupported cli '{cli}' for model '{alias}'; "
            f"allowed: {', '.join(sorted(ALLOWED_CLIS))}"
        )
    model_id = entry.get("id")
    if not isinstance(model_id, str) or not model_id.strip():
        raise PersonaConfigError(f"Invalid model id '{model_id}' for model '{alias}'")
    efforts = entry.get("efforts")
    if (
        not isinstance(efforts, list)
        or not efforts
        or any(not isinstance(e, str) or not e.strip() for e in efforts)
    ):
        raise PersonaConfigError(f"Invalid efforts '{efforts}' for model '{alias}'")
    if "none" in efforts:
        if len(efforts) > 1:
            raise PersonaConfigError(
                f"Invalid efforts '{efforts}' for model '{alias}': "
                "'none' cannot be combined with other efforts"
            )
        if "{effort}" in model_id:
            raise PersonaConfigError(
                f"Invalid model id '{model_id}' for model '{alias}': "
                "'{effort}' placeholder is not allowed when efforts is ['none']"
            )
    derive_quota_pool(entry, alias)


def _validate_binding_ref(
    context: str,
    binding_cfg: Mapping[str, Any],
    models: Mapping[str, Any],
    *,
    partial: bool,
    check_effort_against_model: bool = True,
) -> None:
    model_alias = binding_cfg.get("model")
    effort = binding_cfg.get("effort")
    fallback = binding_cfg.get("fallback_model")
    if not partial or "model" in binding_cfg:
        if not isinstance(model_alias, str) or model_alias not in models:
            raise PersonaConfigError(
                f"Unknown model alias '{model_alias}' in {context}"
            )
    if not partial or "effort" in binding_cfg:
        if not isinstance(effort, str) or not effort.strip():
            raise PersonaConfigError(f"Invalid effort '{effort}' in {context}")
        if (
            check_effort_against_model
            and isinstance(model_alias, str)
            and model_alias in models
        ):
            allowed_efforts = models[model_alias]["efforts"]
            if effort not in allowed_efforts:
                raise PersonaConfigError(
                    f"Unsupported effort '{effort}' for model '{model_alias}' in {context}; "
                    f"allowed: {', '.join(allowed_efforts)}"
                )
    if fallback is not None and (
        not isinstance(fallback, str) or fallback not in models
    ):
        raise PersonaConfigError(f"Unknown fallback_model '{fallback}' in {context}")


def _validate_profile_name(profile: Any, context: str) -> None:
    if not isinstance(profile, str) or not _PROFILE_NAME_RE.fullmatch(profile):
        raise PersonaConfigError(
            f"Invalid profile '{profile}' in {context}; "
            "expected characters matching ^[a-zA-Z0-9_-]+$"
        )


def _validate_presets_and_overrides(
    cfg: Mapping[str, Any], models: Mapping[str, Any]
) -> None:
    presets = cfg.get("presets")
    if not isinstance(presets, Mapping) or not presets:
        raise PersonaConfigError("Configuration 'presets' must be a non-empty object")
    active_preset = cfg.get("active_preset")
    if not isinstance(active_preset, str) or active_preset not in presets:
        raise PersonaConfigError(f"Unknown active_preset '{active_preset}'")

    for preset_name, preset_map in presets.items():
        if not isinstance(preset_map, Mapping):
            raise PersonaConfigError(f"Preset '{preset_name}' must be an object")
        for persona_key in preset_map:
            if persona_key not in PERSONAS:
                raise PersonaConfigError(
                    f"Unknown persona '{persona_key}' in preset '{preset_name}'"
                )
        for persona in PERSONAS:
            if persona not in preset_map or not isinstance(
                preset_map[persona], Mapping
            ):
                raise PersonaConfigError(
                    f"Preset '{preset_name}' is missing binding for persona '{persona}'"
                )
            _validate_binding_ref(
                f"presets.{preset_name}.{persona}",
                preset_map[persona],
                models,
                partial=False,
                check_effort_against_model=(preset_name == active_preset),
            )

    overrides = cfg.get("overrides", {})
    if not isinstance(overrides, Mapping):
        raise PersonaConfigError("Configuration 'overrides' must be an object")
    for persona_key, ov in overrides.items():
        if persona_key not in PERSONAS:
            raise PersonaConfigError(f"Unknown persona '{persona_key}' in overrides")
        if not isinstance(ov, Mapping):
            raise PersonaConfigError(f"Override for '{persona_key}' must be an object")
        bad_fields = set(ov) - _ALLOWED_OVERRIDE_FIELDS
        if bad_fields:
            bad = min(bad_fields)
            raise PersonaConfigError(
                f"Unknown override field '{bad}' for persona '{persona_key}'"
            )
        _validate_binding_ref(f"overrides.{persona_key}", ov, models, partial=True)
        if "profile" in ov:
            _validate_profile_name(ov["profile"], f"overrides.{persona_key}")


def _validate_policy_and_low_quota(cfg: Mapping[str, Any]) -> None:
    policy = cfg.get("checkpoint_policy")
    if not isinstance(policy, Mapping):
        raise PersonaConfigError("Configuration 'checkpoint_policy' must be an object")
    turns = policy.get("max_orchestrator_turns_before_checkpoint")
    if type(turns) is not int or turns < 1:
        raise PersonaConfigError(
            f"Invalid max_orchestrator_turns_before_checkpoint '{turns}'; "
            "must be a positive integer"
        )

    low_quota = cfg.get("low_quota", {})
    if not isinstance(low_quota, Mapping):
        raise PersonaConfigError("Configuration 'low_quota' must be an object")
    for profile, entry in low_quota.items():
        if not isinstance(profile, str) or not profile.strip():
            raise PersonaConfigError(f"Invalid low_quota profile '{profile}'")
        if not isinstance(entry, Mapping) or type(entry.get("enabled")) is not bool:
            raise PersonaConfigError(
                f"Invalid low_quota entry for profile '{profile}'; 'enabled' boolean required"
            )
        expires_at = entry.get("expires_at")
        if expires_at is not None:
            if (
                not isinstance(expires_at, str)
                or _parse_utc_timestamp(expires_at) is None
            ):
                raise PersonaConfigError(
                    f"Invalid low_quota expires_at '{expires_at}' for profile '{profile}'"
                )
    _validate_task_review_limits(cfg)


def validate_merged_config(cfg: Mapping[str, Any]) -> None:
    """Validate merged persona configuration against the schema and model catalogue."""
    sv = cfg.get("schema_version")
    if type(sv) is not int or sv != SCHEMA_VERSION:
        raise PersonaConfigError(
            f"Unsupported schema_version '{sv}'; expected {SCHEMA_VERSION}"
        )
    models = cfg.get("models")
    if not isinstance(models, Mapping) or not models:
        raise PersonaConfigError("Configuration 'models' must be a non-empty object")
    for alias, entry in models.items():
        _validate_model_entry(alias, entry)
    _validate_presets_and_overrides(cfg, models)
    _validate_policy_and_low_quota(cfg)
    if "review" in cfg:
        _validate_review_section(cfg["review"], models=models, partial=False)


def _load_layers(
    project_root: Path,
    *,
    real_home: Path | str | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    kit = _read_layer_json(KIT_DEFAULTS_PATH, required=True)
    glb = _read_layer_json(global_config_path(real_home))
    prj = _read_layer_json(project_config_path(project_root))
    return [("kit", kit), ("global", glb), ("project", prj)]


def _merge_and_validate(layers: list[tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for _, data in layers:
        merged = _deep_merge(merged, data)
    validate_merged_config(merged)
    for persona in PERSONAS:
        _resolve_from_layers(persona, layers, merged)
    return merged


def load_persona_config(
    project_root: Path,
    *,
    real_home: Path | str | None = None,
) -> dict[str, Any]:
    """Load, deep-merge, and validate kit, global, and project persona configurations."""
    layers = _load_layers(project_root, real_home=real_home)
    return _merge_and_validate(layers)


def _max_layer(first: str, second: str) -> str:
    return first if _LAYER_RANK[first] >= _LAYER_RANK[second] else second


def _resolve_from_layers(
    persona: str,
    layers: list[tuple[str, dict[str, Any]]],
    merged: Mapping[str, Any],
    *,
    cli_overrides: Mapping[str, str] | None = None,
) -> PersonaBinding:
    if persona not in PERSONAS:
        raise PersonaConfigError(
            f"Unknown persona '{persona}'; expected one of {', '.join(PERSONAS)}"
        )

    active_preset = str(merged["active_preset"])
    preset_source = "kit"
    for layer_name, layer_data in layers:
        if "active_preset" in layer_data:
            preset_source = layer_name

    values: dict[str, Any] = {}
    sources: dict[str, str] = {}
    preset_binding = merged["presets"][active_preset][persona]
    for field in ("model", "effort", "fallback_model"):
        values[field] = preset_binding.get(field)
        field_layer = "kit"
        for layer_name, layer_data in layers:
            preset_layer = (
                layer_data.get("presets", {}).get(active_preset, {}).get(persona, {})
            )
            if isinstance(preset_layer, Mapping) and field in preset_layer:
                field_layer = layer_name
        sources[field] = _max_layer(preset_source, field_layer)

    for layer_name, layer_data in layers:
        ov = layer_data.get("overrides", {}).get(persona)
        if not isinstance(ov, Mapping):
            continue
        for field in ("model", "effort", "fallback_model"):
            if field in ov:
                values[field] = ov[field]
                sources[field] = layer_name

    if cli_overrides:
        bad_cli_keys = set(cli_overrides) - _ALLOWED_CLI_OVERRIDE_FIELDS
        if bad_cli_keys:
            bad = min(bad_cli_keys)
            raise PersonaConfigError(f"Unknown CLI override field '{bad}'")
        for field in ("model", "effort", "fallback_model"):
            if field in cli_overrides and cli_overrides[field] is not None:
                values[field] = cli_overrides[field]
                sources[field] = "cli"

    models = merged["models"]
    alias = values["model"]
    effort = values["effort"]
    fallback_alias = values.get("fallback_model")

    if not isinstance(alias, str) or alias not in models:
        raise PersonaConfigError(
            f"Unknown model alias '{alias}' for persona '{persona}'"
        )
    entry = models[alias]
    if not isinstance(effort, str) or effort not in entry["efforts"]:
        raise PersonaConfigError(
            f"Unsupported effort '{effort}' for model '{alias}' (persona '{persona}'); "
            f"allowed: {', '.join(entry['efforts'])}"
        )
    if fallback_alias is not None and (
        not isinstance(fallback_alias, str) or fallback_alias not in models
    ):
        raise PersonaConfigError(
            f"Unknown fallback_model '{fallback_alias}' for persona '{persona}'"
        )

    model_id = str(entry["id"]).replace("{effort}", effort)
    quota_pool = derive_quota_pool(entry, alias)
    return PersonaBinding(
        persona=persona,
        alias=alias,
        cli=str(entry["cli"]),
        model_id=model_id,
        effort=effort,
        quota_pool=quota_pool,
        fallback_alias=fallback_alias,
        sources=sources,
        profile=None,
    )


def resolve_persona(
    persona: str,
    project_root: Path,
    *,
    cli_overrides: dict[str, str] | None = None,
    real_home: Path | None = None,
) -> PersonaBinding:
    """Resolve one persona's model, effort, quota pool, and per-field layer provenance."""
    layers = _load_layers(project_root, real_home=real_home)
    merged = _merge_and_validate(layers)
    return _resolve_from_layers(persona, layers, merged, cli_overrides=cli_overrides)


def resolve_all_personas(
    project_root: Path,
    *,
    real_home: Path | None = None,
) -> dict[str, PersonaBinding]:
    """Resolve bindings for all three AI personas."""
    layers = _load_layers(project_root, real_home=real_home)
    merged = _merge_and_validate(layers)
    return {p: _resolve_from_layers(p, layers, merged) for p in PERSONAS}


def _parse_utc_timestamp(raw: str) -> datetime | None:
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def low_quota_state(
    project_root: Path,
    profile: str,
    *,
    now: datetime | None = None,
    real_home: Path | None = None,
) -> dict[str, Any] | None:
    """Return active global low-quota state for `profile`, or None if disabled/expired."""
    _ = project_root
    global_data = _read_layer_json(global_config_path(real_home))
    low_quota = global_data.get("low_quota")
    if not isinstance(low_quota, Mapping):
        return None
    entry = low_quota.get(profile)
    if not isinstance(entry, Mapping) or entry.get("enabled") is not True:
        return None
    current_now = now if now is not None else datetime.now(timezone.utc)
    if current_now.tzinfo is None:
        current_now = current_now.replace(tzinfo=timezone.utc)
    else:
        current_now = current_now.astimezone(timezone.utc)
    expires_raw = entry.get("expires_at")
    if isinstance(expires_raw, str):
        expires_dt = _parse_utc_timestamp(expires_raw)
        if expires_dt is None or current_now >= expires_dt:
            return None
    return dict(entry)


def effective_turn_budget(
    project_root: Path,
    profile: str,
    *,
    now: datetime | None = None,
    real_home: Path | None = None,
) -> int:
    """Return turn budget N, halved (minimum 1) while low-quota mode is active for profile."""
    cfg = load_persona_config(project_root, real_home=real_home)
    base_turns = int(
        cfg["checkpoint_policy"]["max_orchestrator_turns_before_checkpoint"]
    )
    if low_quota_state(project_root, profile, now=now, real_home=real_home) is not None:
        return max(1, base_turns // 2)
    return base_turns


def _read_legacy_review_config(project_root: Path) -> dict[str, Any]:
    """Read legacy .devtool/review_config.json safely; return {} if absent or malformed."""
    path = Path(project_root) / ".devtool" / "review_config.json"
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, Mapping):
        return {}

    parsed: dict[str, Any] = {}
    max_rounds = raw.get("max_rounds")
    if type(max_rounds) is int and max_rounds >= 1:
        parsed["max_rounds"] = max_rounds

    priority = raw.get("provider_priority")
    if isinstance(priority, list) and priority:
        try:
            parsed["provider_priority"] = list(_validate_review_priority(priority))
        except PersonaConfigError:
            pass

    thresholds_raw = raw.get("quota_thresholds")
    if isinstance(thresholds_raw, Mapping):
        valid_thresholds: dict[str, float] = {}
        for key, val in thresholds_raw.items():
            if key not in DEFAULT_REVIEW_QUOTA_THRESHOLDS:
                continue
            try:
                valid_thresholds.update(_validate_review_quota_thresholds({key: val}))
            except PersonaConfigError:
                continue
        if valid_thresholds:
            parsed["quota_thresholds"] = valid_thresholds

    providers_raw = raw.get("providers")
    if isinstance(providers_raw, Mapping):
        valid_providers: dict[str, dict[str, str]] = {}
        for cli in REVIEW_PROVIDERS:
            entry = providers_raw.get(cli)
            if not isinstance(entry, Mapping):
                continue
            cleaned: dict[str, str] = {}
            model_val = entry.get("model")
            if isinstance(model_val, str) and model_val.strip():
                cleaned["model"] = model_val.strip()
            eff_raw = (
                entry.get("effort")
                if "effort" in entry
                else entry.get("thinking_level")
            )
            if isinstance(eff_raw, str) and eff_raw in _REVIEW_THINKING_LEVEL_SET:
                cleaned["effort"] = eff_raw
            if cli == "ollama" and _is_valid_ollama_host(entry.get("host")):
                cleaned["host"] = str(entry["host"]).strip()
            if cleaned:
                valid_providers[cli] = cleaned
        if valid_providers:
            parsed["providers"] = valid_providers

    return parsed


def _resolve_review_limits_from_layers(
    layers: list[tuple[str, dict[str, Any]]],
    merged: Mapping[str, Any],
    legacy: Mapping[str, Any],
) -> ReviewLimits:
    layer_map = dict(layers)
    global_layer = layer_map.get("global", {})
    project_layer = layer_map.get("project", {})
    sources: dict[str, str] = {}

    if "max_task_review_passes" not in merged:
        task_passes = DEFAULT_MAX_TASK_REVIEW_PASSES
        sources["max_task_review_passes"] = "kit"
    else:
        task_passes = int(merged["max_task_review_passes"])
        if "max_task_review_passes" in project_layer:
            sources["max_task_review_passes"] = "project"
        elif "max_task_review_passes" in global_layer:
            sources["max_task_review_passes"] = "global"
        else:
            sources["max_task_review_passes"] = "kit"

    if "max_fix_passes" not in merged:
        fix_passes = DEFAULT_MAX_FIX_PASSES
        sources["max_fix_passes"] = "kit"
    else:
        fix_passes = int(merged["max_fix_passes"])
        if "max_fix_passes" in project_layer:
            sources["max_fix_passes"] = "project"
        elif "max_fix_passes" in global_layer:
            sources["max_fix_passes"] = "global"
        else:
            sources["max_fix_passes"] = "kit"

    legacy_rounds = legacy.get("max_rounds")
    resolved_external: dict[str, int] = {}
    for key, default_val in (
        ("max_principal_review_passes", DEFAULT_MAX_PRINCIPAL_REVIEW_PASSES),
        ("max_cross_model_review_passes", DEFAULT_MAX_CROSS_MODEL_REVIEW_PASSES),
    ):
        if key in project_layer:
            resolved_external[key] = int(project_layer[key])
            sources[key] = "project"
        elif key in global_layer:
            resolved_external[key] = int(global_layer[key])
            sources[key] = "global"
        elif type(legacy_rounds) is int and legacy_rounds >= 1:
            resolved_external[key] = legacy_rounds
            sources[key] = "legacy"
        else:
            resolved_external[key] = int(merged.get(key, default_val))
            sources[key] = "kit"

    return ReviewLimits(
        max_task_review_passes=task_passes,
        max_fix_passes=fix_passes,
        max_principal_review_passes=resolved_external["max_principal_review_passes"],
        max_cross_model_review_passes=resolved_external[
            "max_cross_model_review_passes"
        ],
        sources=sources,
    )


def resolve_review_limits(
    project_root: Path,
    *,
    real_home: Path | str | None = None,
) -> ReviewLimits:
    """Resolve all four independent pass limits with per-key layer provenance."""
    merged = load_persona_config(project_root, real_home=real_home)
    layers = _load_layers(project_root, real_home=real_home)
    legacy = _read_legacy_review_config(project_root)
    return _resolve_review_limits_from_layers(layers, merged, legacy)


def resolve_task_review_limits(
    project_root: Path,
    *,
    real_home: Path | str | None = None,
) -> tuple[int, int]:
    """Resolve layered (max_task_review_passes, max_fix_passes) limits for a workspace."""
    limits = resolve_review_limits(project_root, real_home=real_home)
    return (limits.max_task_review_passes, limits.max_fix_passes)


def resolve_review_config(
    project_root: Path,
    *,
    real_home: Path | str | None = None,
) -> ResolvedReviewConfig:
    """Resolve layered external review priority, providers, quota thresholds, and limits."""
    layers = _load_layers(project_root, real_home=real_home)
    merged = _merge_and_validate(layers)
    legacy = _read_legacy_review_config(project_root)
    limits = _resolve_review_limits_from_layers(layers, merged, legacy)

    layer_map = dict(layers)
    kit_review = layer_map.get("kit", {}).get("review", {})
    global_review = layer_map.get("global", {}).get("review", {})
    project_review = layer_map.get("project", {}).get("review", {})
    models = merged["models"]
    sources: dict[str, str] = {}

    if isinstance(project_review, Mapping) and "provider_priority" in project_review:
        priority = tuple(project_review["provider_priority"])
        sources["provider_priority"] = "project"
    elif isinstance(global_review, Mapping) and "provider_priority" in global_review:
        priority = tuple(global_review["provider_priority"])
        sources["provider_priority"] = "global"
    elif "provider_priority" in legacy:
        priority = tuple(legacy["provider_priority"])
        sources["provider_priority"] = "legacy"
    else:
        kit_prio = (
            kit_review.get("provider_priority")
            if isinstance(kit_review, Mapping)
            else None
        )
        priority = tuple(kit_prio) if kit_prio else REVIEW_PRIORITY_PROVIDERS
        sources["provider_priority"] = "kit"

    kit_th = (
        kit_review.get("quota_thresholds", {})
        if isinstance(kit_review, Mapping)
        else {}
    )
    global_th = (
        global_review.get("quota_thresholds", {})
        if isinstance(global_review, Mapping)
        else {}
    )
    project_th = (
        project_review.get("quota_thresholds", {})
        if isinstance(project_review, Mapping)
        else {}
    )
    legacy_th = legacy.get("quota_thresholds", {})
    quota_thresholds: dict[str, float] = {}
    for key, default_val in DEFAULT_REVIEW_QUOTA_THRESHOLDS.items():
        if isinstance(project_th, Mapping) and key in project_th:
            quota_thresholds[key] = float(project_th[key])
            sources[f"quota_thresholds.{key}"] = "project"
        elif isinstance(global_th, Mapping) and key in global_th:
            quota_thresholds[key] = float(global_th[key])
            sources[f"quota_thresholds.{key}"] = "global"
        elif isinstance(legacy_th, Mapping) and key in legacy_th:
            quota_thresholds[key] = float(legacy_th[key])
            sources[f"quota_thresholds.{key}"] = "legacy"
        elif isinstance(kit_th, Mapping) and key in kit_th:
            quota_thresholds[key] = float(kit_th[key])
            sources[f"quota_thresholds.{key}"] = "kit"
        else:
            quota_thresholds[key] = float(default_val)
            sources[f"quota_thresholds.{key}"] = "kit"

    kit_provs = (
        kit_review.get("providers", {}) if isinstance(kit_review, Mapping) else {}
    )
    global_provs = (
        global_review.get("providers", {}) if isinstance(global_review, Mapping) else {}
    )
    project_provs = (
        project_review.get("providers", {})
        if isinstance(project_review, Mapping)
        else {}
    )
    legacy_provs = legacy.get("providers", {})
    providers: dict[str, ReviewProviderBinding] = {}
    for cli in REVIEW_PROVIDERS:
        base_entry: dict[str, Any] = dict(DEFAULT_REVIEW_PROVIDERS[cli])
        kit_entry = kit_provs.get(cli) if isinstance(kit_provs, Mapping) else None
        if isinstance(kit_entry, Mapping):
            base_entry.update(_normalize_review_provider_entry(kit_entry))

        has_project = isinstance(project_provs, Mapping) and cli in project_provs
        has_global = isinstance(global_provs, Mapping) and cli in global_provs
        has_legacy = isinstance(legacy_provs, Mapping) and cli in legacy_provs

        effective_entry = dict(base_entry)
        if has_project or has_global:
            if has_global:
                effective_entry.update(
                    _normalize_review_provider_entry(global_provs[cli])
                )
            if has_project:
                effective_entry.update(
                    _normalize_review_provider_entry(project_provs[cli])
                )
            provider_source = "project" if has_project else "global"
            model_raw = str(effective_entry["model"]).strip()
            effort_raw = str(effective_entry.get("effort", "high"))
            model_id, resolved_effort = _resolve_review_provider_model(
                cli, model_raw, effort_raw, models
            )
        elif has_legacy:
            legacy_candidate = dict(base_entry)
            legacy_candidate.update(legacy_provs[cli])
            try:
                model_raw = str(legacy_candidate["model"]).strip()
                effort_raw = str(legacy_candidate.get("effort", "high"))
                model_id, resolved_effort = _resolve_review_provider_model(
                    cli, model_raw, effort_raw, models
                )
                effective_entry = legacy_candidate
                provider_source = "legacy"
            except PersonaConfigError:
                model_raw = str(base_entry["model"]).strip()
                effort_raw = str(base_entry.get("effort", "high"))
                model_id, resolved_effort = _resolve_review_provider_model(
                    cli, model_raw, effort_raw, models
                )
                effective_entry = base_entry
                provider_source = "kit"
        else:
            model_raw = str(base_entry["model"]).strip()
            effort_raw = str(base_entry.get("effort", "high"))
            model_id, resolved_effort = _resolve_review_provider_model(
                cli, model_raw, effort_raw, models
            )
            provider_source = "kit"

        host_val = (
            str(effective_entry["host"]).strip()
            if cli == "ollama" and effective_entry.get("host") is not None
            else None
        )
        providers[cli] = ReviewProviderBinding(
            provider=cli,
            model=model_raw,
            model_id=model_id,
            effort=resolved_effort,
            host=host_val,
            source=provider_source,
        )
        sources[f"providers.{cli}"] = provider_source

    return ResolvedReviewConfig(
        provider_priority=priority,
        providers=providers,
        quota_thresholds=quota_thresholds,
        limits=limits,
        sources=sources,
    )


def quota_pool_for(binding: PersonaBinding) -> str:
    """Return the quota pool consumed by `binding` without inspecting its alias."""
    return binding.quota_pool


def resolve_cli_binary(cli: str) -> str | None:
    """Return the path to the CLI binary on PATH, checking kiro-cli before kiro."""
    if cli == "kiro":
        return shutil.which("kiro-cli") or shutil.which("kiro")
    return shutil.which(cli)


def build_dispatch_argv(binding: PersonaBinding, mode: str) -> list[str]:
    """Build headless CLI argv for `binding` in 'read-only' or 'write' mode."""
    if mode not in ("read-only", "write"):
        raise PersonaConfigError(
            f"Invalid dispatch mode '{mode}'; expected 'read-only' or 'write'"
        )
    cli = binding.cli
    model_id = binding.model_id
    effort = binding.effort
    effort_args = [] if effort == "none" else ["--effort", effort]

    if cli == "agy":
        if mode == "read-only":
            return [
                "agy",
                "--sandbox",
                "--mode",
                "plan",
                "--model",
                model_id,
                *effort_args,
            ]
        return ["agy", "--model", model_id, *effort_args, "--mode", "auto"]
    if cli == "claude":
        perm_flags = (
            ["--permission-mode", "plan"]
            if mode == "read-only"
            else ["--dangerously-skip-permissions"]
        )
        return ["claude", "-p", "--model", model_id, *effort_args, *perm_flags]
    if cli == "codex":
        sandbox = "read-only" if mode == "read-only" else "workspace-write"
        mapped_effort = _CODEX_EFFORT_MAP.get(effort.lower(), effort)
        return [
            "codex",
            "exec",
            "--sandbox",
            sandbox,
            "--model",
            model_id,
            "-c",
            f"model_reasoning_effort={mapped_effort}",
            "-",
        ]
    if cli == "kiro":
        kiro_bin = (
            "kiro-cli"
            if shutil.which("kiro-cli") or not shutil.which("kiro")
            else "kiro"
        )
        return [
            kiro_bin,
            "chat",
            "--no-interactive",
            "--trust-all-tools",
            "--wrap",
            "never",
            "--model",
            model_id,
            *effort_args,
        ]
    raise PersonaConfigError(f"Unsupported cli '{cli}'")


def build_dispatch_env(
    argv: list[str],
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return environment for dispatch, restoring host HOME for Kiro when isolated."""
    env = dict(os.environ) if base_env is None else dict(base_env)
    if not argv or Path(argv[0]).name not in ("kiro-cli", "kiro"):
        return env
    home = env.get("HOME", "")
    if "/antigravity_homes/" not in home:
        return env
    real_home = Path(home.split("/antigravity_homes/", 1)[0])
    if (real_home / "Library" / "Application Support" / "kiro-cli").exists() or (
        real_home / ".kiro"
    ).exists():
        env["HOME"] = str(real_home)
    return env


def classify_dispatch_failure(exit_code: int, stdout: str, stderr: str) -> str | None:
    """Classify non-zero dispatch outcome as 'model_unavailable' or 'task_failure'."""
    _ = stdout
    if exit_code == 0:
        return None
    if exit_code == 127:
        return "model_unavailable"
    for pattern in _MODEL_FAILURE_PATTERNS:
        if pattern.search(stderr):
            return "model_unavailable"
    return "task_failure"


def detect_legacy_warnings(
    project_root: Path,
    env: Mapping[str, str] | None = None,
    *,
    real_home: Path | str | None = None,
) -> list[str]:
    """Report legacy personas.json profile keys, review_config.json settings, and AGY_* env vars."""
    warnings: list[str] = []
    for layer_label, cfg_path in (
        ("global", global_config_path(real_home)),
        ("project", project_config_path(project_root)),
    ):
        if not cfg_path.is_file():
            continue
        try:
            layer_doc = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(layer_doc, Mapping):
            continue
        ov_map = layer_doc.get("overrides")
        if not isinstance(ov_map, Mapping):
            continue
        for persona_key in PERSONAS:
            ov_entry = ov_map.get(persona_key)
            if isinstance(ov_entry, Mapping) and "profile" in ov_entry:
                warnings.append(
                    f"Legacy setting '{layer_label} personas.json overrides.{persona_key}.profile' "
                    "is ignored; configure pool priority and concurrency on Task Dashboard "
                    "or via 'dev-config profiles set'."
                )
    review_cfg = Path(project_root) / ".devtool" / "review_config.json"
    if review_cfg.is_file():
        try:
            data = json.loads(review_cfg.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            data = None
        if isinstance(data, Mapping):
            providers = data.get("providers")
            if isinstance(providers, Mapping):
                for key in ("programmer", "assistant"):
                    if key in providers:
                        warnings.append(
                            f"Legacy setting '.devtool/review_config.json providers.{key}' "
                            "is ignored; configure personas via dev-config instead."
                        )
            review_keys = [
                key
                for key in ("provider_priority", "max_rounds", "quota_thresholds")
                if key in data
            ]
            if isinstance(providers, Mapping):
                reviewer_provs = [cli for cli in REVIEW_PROVIDERS if cli in providers]
                if reviewer_provs:
                    review_keys.append(f"providers ({', '.join(reviewer_provs)})")
            if review_keys:
                warnings.append(
                    "Legacy '.devtool/review_config.json' defines review settings "
                    f"({', '.join(review_keys)}) used only as fallback; "
                    "migrate via 'dev-config review' / 'dev-config limits'."
                )
    env_map = os.environ if env is None else env
    for var_name in (
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
        "AGY_ASSISTANT_MODEL",
    ):
        if env_map.get(var_name):
            warnings.append(
                f"Legacy environment variable '{var_name}' is ignored; "
                "configure personas via dev-config instead."
            )
    return warnings


def _atomic_write_json(target_path: Path, data: Mapping[str, Any]) -> None:
    payload = json.dumps(data, indent=2) + "\n"
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target_path.parent,
            prefix=f".{target_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            tmp_path = handle.name
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


def locked_update_layer(
    project_root: Path,
    scope: str,
    mutator: Callable[[dict[str, Any]], None],
    *,
    real_home: Path | str | None = None,
) -> dict[str, Any]:
    """Atomically read, mutate, validate, and replace a global or project persona file under flock."""
    target_path = config_path_for_scope(project_root, scope, real_home=real_home)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target_path.with_name(f"{target_path.name}.lock")
    with open(lock_path, "a", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            kit_data = _read_layer_json(KIT_DEFAULTS_PATH, required=True)
            global_path = global_config_path(real_home)
            project_path = project_config_path(project_root)

            global_data = _read_layer_json(global_path)
            project_data = _read_layer_json(project_path)

            layer_copy = copy.deepcopy(
                global_data if scope == "global" else project_data
            )
            mutator(layer_copy)
            if "schema_version" not in layer_copy:
                layer_copy["schema_version"] = SCHEMA_VERSION

            if scope == "global":
                _merge_and_validate(
                    [("kit", kit_data), ("global", layer_copy), ("project", {})]
                )
                merged = _merge_and_validate(
                    [
                        ("kit", kit_data),
                        ("global", layer_copy),
                        ("project", project_data),
                    ]
                )
            else:
                merged = _merge_and_validate(
                    [
                        ("kit", kit_data),
                        ("global", global_data),
                        ("project", layer_copy),
                    ]
                )

            _atomic_write_json(target_path, layer_copy)
            return merged
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
