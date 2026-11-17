#!/usr/bin/env python3
"""Layered persona configuration, dispatch argv/env builders, and failure classification."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import copy
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import json
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

KIT_DEFAULTS_PATH: Path = Path(__file__).resolve().with_name("personas.default.json")
_LAYER_RANK: dict[str, int] = {"kit": 0, "global": 1, "project": 2, "cli": 3}
_ALLOWED_OVERRIDE_FIELDS: frozenset[str] = frozenset(
    {"model", "effort", "fallback_model", "profile"}
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
    }
)
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


def _read_layer_json(path: Path, *, required: bool = False) -> dict[str, Any]:
    if not path.is_file():
        if required:
            raise PersonaConfigError(f"Missing required persona config file: {path}")
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PersonaConfigError(f"Failed to read persona config '{path}': {exc}") from exc
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
    return raw


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key == "models" and isinstance(result.get(key), dict) and isinstance(value, Mapping):
            merged_models = copy.deepcopy(result[key])
            for alias, entry in value.items():
                if (
                    isinstance(entry, Mapping)
                    and {"cli", "id", "efforts"}.issubset(entry)
                ):
                    merged_models[alias] = copy.deepcopy(dict(entry))
                elif isinstance(merged_models.get(alias), dict) and isinstance(entry, Mapping):
                    merged_models[alias] = _deep_merge(merged_models[alias], entry)
                else:
                    merged_models[alias] = copy.deepcopy(entry)
            result[key] = merged_models
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
        return "argonWeekly" if "argon" in model_id else "gemini5h"
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
            raise PersonaConfigError(f"Unknown model alias '{model_alias}' in {context}")
    if not partial or "effort" in binding_cfg:
        if not isinstance(effort, str) or not effort.strip():
            raise PersonaConfigError(f"Invalid effort '{effort}' in {context}")
        if check_effort_against_model and isinstance(model_alias, str) and model_alias in models:
            allowed_efforts = models[model_alias]["efforts"]
            if effort not in allowed_efforts:
                raise PersonaConfigError(
                    f"Unsupported effort '{effort}' for model '{model_alias}' in {context}; "
                    f"allowed: {', '.join(allowed_efforts)}"
                )
    if fallback is not None and (not isinstance(fallback, str) or fallback not in models):
        raise PersonaConfigError(f"Unknown fallback_model '{fallback}' in {context}")


def _validate_profile_name(profile: Any, context: str) -> None:
    if not isinstance(profile, str) or not _PROFILE_NAME_RE.fullmatch(profile):
        raise PersonaConfigError(
            f"Invalid profile '{profile}' in {context}; "
            "expected characters matching ^[a-zA-Z0-9_-]+$"
        )


def _validate_presets_and_overrides(cfg: Mapping[str, Any], models: Mapping[str, Any]) -> None:
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
            if persona not in preset_map or not isinstance(preset_map[persona], Mapping):
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
            if not isinstance(expires_at, str) or _parse_utc_timestamp(expires_at) is None:
                raise PersonaConfigError(
                    f"Invalid low_quota expires_at '{expires_at}' for profile '{profile}'"
                )


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
    real_home: Path | None = None,
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
            preset_layer = layer_data.get("presets", {}).get(active_preset, {}).get(persona, {})
            if isinstance(preset_layer, Mapping) and field in preset_layer:
                field_layer = layer_name
        sources[field] = _max_layer(preset_source, field_layer)

    for layer_name, layer_data in layers:
        ov = layer_data.get("overrides", {}).get(persona)
        if not isinstance(ov, Mapping):
            continue
        for field in ("model", "effort", "fallback_model", "profile"):
            if field in ov:
                values[field] = ov[field]
                sources[field] = layer_name

    if cli_overrides:
        bad_cli_keys = set(cli_overrides) - _ALLOWED_OVERRIDE_FIELDS
        if bad_cli_keys:
            bad = min(bad_cli_keys)
            raise PersonaConfigError(f"Unknown CLI override field '{bad}'")
        for field in ("model", "effort", "fallback_model", "profile"):
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
    profile = values.get("profile")
    if profile is not None:
        _validate_profile_name(profile, f"persona '{persona}'")
        if entry["cli"] != "agy" and _LAYER_RANK[sources["profile"]] < _LAYER_RANK[sources["model"]]:
            # SE-15: a profile inherited from a lower layer is ignored when a higher layer
            # binds a model that is not an agy model; it leaves the binding and `sources`.
            profile = None
            del sources["profile"]
        elif entry["cli"] != "agy":
            raise PersonaConfigError(
                f"Invalid profile '{profile}' for persona '{persona}' "
                f"(set by the {sources['profile']} layer): a profile applies only to "
                f"an agy model, but '{alias}' uses '{entry['cli']}'"
            )
    return PersonaBinding(
        persona=persona,
        alias=alias,
        cli=str(entry["cli"]),
        model_id=model_id,
        effort=effort,
        quota_pool=quota_pool,
        fallback_alias=fallback_alias,
        sources=sources,
        profile=profile,
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
    base_turns = int(cfg["checkpoint_policy"]["max_orchestrator_turns_before_checkpoint"])
    if low_quota_state(project_root, profile, now=now, real_home=real_home) is not None:
        return max(1, base_turns // 2)
    return base_turns


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

    if cli == "agy":
        if mode == "read-only":
            return ["agy", "--sandbox", "--mode", "plan", "--model", model_id, "--effort", effort]
        return ["agy", "--model", model_id, "--effort", effort, "--mode", "auto"]
    if cli == "claude":
        perm_flags = (
            ["--permission-mode", "plan"]
            if mode == "read-only"
            else ["--dangerously-skip-permissions"]
        )
        return ["claude", "-p", "--model", model_id, "--effort", effort, *perm_flags]
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
            "--effort",
            effort,
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
) -> list[str]:
    """Report legacy review_config.json persona keys and AGY_* env vars that are ignored."""
    warnings: list[str] = []
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
    env_map = os.environ if env is None else env
    for var_name in ("AGY_PROGRAMMER_MODEL", "AGY_PROGRAMMER_EFFORT", "AGY_ASSISTANT_MODEL"):
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

            layer_copy = copy.deepcopy(global_data if scope == "global" else project_data)
            mutator(layer_copy)
            if "schema_version" not in layer_copy:
                layer_copy["schema_version"] = SCHEMA_VERSION

            if scope == "global":
                _merge_and_validate([("kit", kit_data), ("global", layer_copy), ("project", {})])
                merged = _merge_and_validate(
                    [("kit", kit_data), ("global", layer_copy), ("project", project_data)]
                )
            else:
                merged = _merge_and_validate(
                    [("kit", kit_data), ("global", global_data), ("project", layer_copy)]
                )

            _atomic_write_json(target_path, layer_copy)
            return merged
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)
