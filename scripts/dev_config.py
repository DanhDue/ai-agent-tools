#!/usr/bin/env python3
"""CLI for layered persona model configuration, low-quota mode, and quota gate."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import shlex
import sys
from types import ModuleType
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from persona_config import PersonaBinding

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_module_by_path(name: str, path: Path, *, extra_sys_path: Path | None = None) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    if not path.is_file():
        raise RuntimeError(f"Required module file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    inserted = False
    if extra_sys_path is not None and str(extra_sys_path) not in sys.path:
        sys.path.insert(0, str(extra_sys_path))
        inserted = True
    try:
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    finally:
        if inserted:
            try:
                sys.path.remove(str(extra_sys_path))
            except ValueError:
                pass
    return mod


_pc = _load_module_by_path("persona_config", _SCRIPTS_DIR / "persona_config.py")
PERSONAS: tuple[str, ...] = _pc.PERSONAS
ALLOWED_CLIS: frozenset[str] = _pc.ALLOWED_CLIS
PersonaConfigError = _pc.PersonaConfigError

_SUBCOMMANDS = frozenset(
    {
        "status",
        "models",
        "preset",
        "set",
        "reset",
        "low-quota",
        "checkpoint",
        "quota-check",
        "resolve",
    }
)
PROVIDER_PRESETS: dict[str, str] = {
    "agy": "default",
    "claude": "all-claude",
    "codex": "all-codex",
}
_POOL_KEYS = ("gemini5h", "argonWeekly", "geminiWeekly", "creditsPool")


class _DevConfigParser(argparse.ArgumentParser):
    """ArgumentParser subclass that exits with code 1 on usage errors."""

    def error(self, message: str) -> NoReturn:
        print(f"Error: {message}", file=sys.stderr)
        raise SystemExit(1)


def _detect_profile(project_root: Path, *, real_home: Path | str | None = None) -> str:
    resume_mod = _load_module_by_path("resume_context", _SCRIPTS_DIR / "resume_context.py")
    resolved_home = _pc.get_real_home(real_home)
    profile = str(
        resume_mod.detect_current_profile(project_root, real_home=resolved_home) or ""
    ).strip()
    return profile or os.environ.get("USER", "").strip() or "default"


def _load_external_review_module() -> ModuleType:
    review_path = (
        _SCRIPTS_DIR.parent
        / "skills"
        / "dev-implementation"
        / "resources"
        / "scripts"
        / "run_external_review.py"
    )
    return _load_module_by_path(
        "run_external_review",
        review_path,
        extra_sys_path=review_path.parent,
    )


def _load_quota_thresholds(project_root: Path, review_mod: ModuleType) -> dict[str, float]:
    thresholds: dict[str, float] = {
        str(k): float(v) for k, v in dict(review_mod.QUOTA_THRESHOLDS).items()
    }
    review_cfg = project_root / ".devtool" / "review_config.json"
    if review_cfg.is_file():
        try:
            data = json.loads(review_cfg.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            data = None
        if isinstance(data, Mapping) and isinstance(data.get("quota_thresholds"), Mapping):
            for key, val in data["quota_thresholds"].items():
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    thresholds[str(key)] = float(val)
    return thresholds


def _agy_status_ok(payload: Mapping[str, Any]) -> bool:
    if "status" in payload or "success" in payload:
        status = str(payload.get("status", ""))
        return status == "ACTIVE" or bool(payload.get("success"))
    return True


def _evaluate_binding_quota(
    binding: PersonaBinding,
    payload: Mapping[str, Any],
    thresholds: Mapping[str, float],
) -> tuple[bool, str, str | None]:
    has_pool = any(isinstance(payload.get(k), Mapping) for k in _POOL_KEYS)
    if (
        not payload
        or (payload.get("success") is False and not has_pool)
        or ("error" in payload and not has_pool)
    ):
        return True, "", "quota_unknown"

    pool = _pc.quota_pool_for(binding)
    if pool == "argonWeekly":
        argon = payload.get("argonWeekly")
        frac = float(argon.get("fraction", 0.0)) if isinstance(argon, Mapping) else 0.0
        ok = _agy_status_ok(payload) and frac >= thresholds["agy_argon_min_fraction"]
        return ok, f"Argon={frac * 100:.1f}%", None

    if pool == "gemini5h":
        g5h = payload.get("gemini5h")
        frac = float(g5h.get("fraction", 0.0)) if isinstance(g5h, Mapping) else 0.0
        ok = _agy_status_ok(payload) and frac >= thresholds["5h_min_fraction"]
        return ok, f"5H={frac * 100:.1f}%", None

    status = str(payload.get("status", ""))
    if binding.cli in ("claude", "codex"):
        g5h = payload.get("gemini5h")
        g7d = payload.get("geminiWeekly")
        frac_5h = float(g5h.get("fraction", 0.0)) if isinstance(g5h, Mapping) else 0.0
        frac_7d = float(g7d.get("fraction", 0.0)) if isinstance(g7d, Mapping) else 0.0
        ok = (
            status == "ACTIVE"
            and frac_5h >= thresholds["5h_min_fraction"]
            and frac_7d > thresholds["7d_min_fraction"]
        )
        return ok, f"5H={frac_5h * 100:.1f}%, 7D={frac_7d * 100:.1f}%, status={status}", None

    if binding.cli == "kiro":
        cp_raw = payload.get("creditsPool") or payload.get("gemini5h")
        cp = cp_raw if isinstance(cp_raw, Mapping) else {}
        frac = float(cp.get("fraction", 0.0))
        limit = float(cp.get("limit", 1000.0))
        remaining = float(cp.get("remaining", frac * limit))
        ok = (
            status.startswith("ACTIVE")
            and frac >= thresholds["kiro_min_fraction"]
            and remaining >= thresholds["kiro_min_credits"]
        )
        return ok, f"monthly={frac * 100:.1f}% ({remaining:.1f} credits), status={status}", None

    return True, "", "quota_unknown"


def _validate_persona_name(persona: str) -> None:
    if persona not in PERSONAS:
        raise PersonaConfigError(
            f"Unknown persona '{persona}'; expected one of {', '.join(PERSONAS)}"
        )


def _validate_scope(scope: str) -> None:
    if scope not in ("global", "project"):
        raise PersonaConfigError(f"Invalid scope '{scope}'; expected 'global' or 'project'")


def cmd_status(
    project_root: Path,
    *,
    json_output: bool = False,
    real_home: Path | None = None,
) -> int:
    """Display resolved persona bindings, presets, turn budget, low-quota state, and warnings."""
    cfg = _pc.load_persona_config(project_root, real_home=real_home)
    bindings = _pc.resolve_all_personas(project_root, real_home=real_home)
    profile = _detect_profile(project_root, real_home=real_home)
    lq_state = _pc.low_quota_state(project_root, profile, real_home=real_home)
    base_turns = int(cfg["checkpoint_policy"]["max_orchestrator_turns_before_checkpoint"])
    eff_turns = _pc.effective_turn_budget(project_root, profile, real_home=real_home)

    warnings = _pc.detect_legacy_warnings(project_root)
    personas_payload: dict[str, Any] = {}
    for persona, binding in bindings.items():
        on_path = _pc.resolve_cli_binary(binding.cli) is not None
        if not on_path:
            warnings.append(
                f"CLI '{binding.cli}' for persona '{persona}' "
                f"(model '{binding.alias}') was not found on PATH."
            )
        entry = asdict(binding)
        entry["cli_on_path"] = on_path
        personas_payload[persona] = entry

    payload: dict[str, Any] = {
        "schema_version": cfg["schema_version"],
        "active_preset": cfg["active_preset"],
        "presets": list(cfg["presets"].keys()),
        "profile": profile,
        "turn_budget": {"base": base_turns, "effective": eff_turns},
        "low_quota": lq_state,
        "personas": personas_payload,
        "warnings": warnings,
    }
    if json_output:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Active preset: {cfg['active_preset']} (presets: {', '.join(payload['presets'])})")
    print(f"Profile: {profile} | Turn budget: {eff_turns} (base {base_turns})")
    if lq_state:
        print(f"Low-quota mode: ON (expires_at={lq_state.get('expires_at', 'none')})")
    else:
        print("Low-quota mode: OFF")
    print()
    print(
        f"{'Persona':<24} {'CLI':<7} {'Model ID':<28} {'Effort':<8} "
        f"{'Fallback':<15} {'Sources'}"
    )
    for persona in PERSONAS:
        b = bindings[persona]
        src_str = f"model={b.sources['model']}, effort={b.sources['effort']}"
        cli_tag = b.cli if personas_payload[persona]["cli_on_path"] else f"{b.cli}(!)"
        fb = b.fallback_alias or "-"
        print(
            f"{persona:<24} {cli_tag:<7} {b.model_id:<28} {b.effort:<8} {fb:<15} {src_str}"
        )
    if warnings:
        print("\nWarnings:")
        for w in warnings:
            print(f"  - {w}")
    return 0


def cmd_models(
    project_root: Path,
    *,
    persona: str | None = None,
    json_output: bool = False,
    fetcher: Callable[[str], dict[str, Any]] | None = None,
    real_home: Path | None = None,
) -> int:
    """List the merged model catalogue with resolved IDs, PATH availability, and active users."""
    if persona is not None:
        _validate_persona_name(persona)
    cfg = _pc.load_persona_config(project_root, real_home=real_home)
    bindings = _pc.resolve_all_personas(project_root, real_home=real_home)

    usage_by_alias: dict[str, list[str]] = {}
    for p_name in PERSONAS:
        usage_by_alias.setdefault(bindings[p_name].alias, []).append(p_name)

    quota_cache: dict[str, dict[str, Any]] = {}
    thresholds: dict[str, float] | None = None
    if fetcher is not None:
        review_mod = _load_external_review_module()
        thresholds = _load_quota_thresholds(project_root, review_mod)

    current_alias = bindings[persona].alias if persona else None
    aliases = list(cfg["models"].keys())
    if current_alias and current_alias in aliases:
        aliases.remove(current_alias)
        aliases.insert(0, current_alias)

    entries: list[dict[str, Any]] = []
    for alias in aliases:
        m = cfg["models"][alias]
        efforts = list(m["efforts"])
        resolved_ids = {eff: str(m["id"]).replace("{effort}", eff) for eff in efforts}
        pool = _pc.derive_quota_pool(m, alias)
        cli = str(m["cli"])
        on_path = _pc.resolve_cli_binary(cli) is not None
        quota_line: str | None = None
        if fetcher is not None and thresholds is not None:
            if cli not in quota_cache:
                try:
                    quota_cache[cli] = dict(fetcher(cli) or {})
                except Exception:
                    quota_cache[cli] = {}
            probe = _pc.PersonaBinding(
                persona=persona or "programmer",
                alias=alias,
                cli=cli,
                model_id=resolved_ids[efforts[0]],
                effort=efforts[0],
                quota_pool=pool,
                fallback_alias=None,
                sources={},
            )
            _, q_line, warn = _evaluate_binding_quota(probe, quota_cache[cli], thresholds)
            quota_line = q_line or warn
        entries.append(
            {
                "alias": alias,
                "cli": cli,
                "id": m["id"],
                "efforts": efforts,
                "resolved_ids": resolved_ids,
                "quota_pool": pool,
                "cli_on_path": on_path,
                "used_by": usage_by_alias.get(alias, []),
                "quota_line": quota_line,
            }
        )

    payload: dict[str, Any] = {"models": entries}
    if persona is not None:
        payload["persona"] = persona
        payload["current_alias"] = current_alias
    if json_output:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"{'Alias':<16} {'CLI':<7} {'PATH':<6} {'Pool':<12} {'Efforts':<22} {'Used By'}")
    for e in entries:
        eff_str = ",".join(e["efforts"])
        used_str = ",".join(e["used_by"]) or "-"
        path_str = "yes" if e["cli_on_path"] else "no"
        print(
            f"{e['alias']:<16} {e['cli']:<7} {path_str:<6} {e['quota_pool']:<12} "
            f"{eff_str:<22} {used_str}"
        )
    return 0


def cmd_models_add(
    project_root: Path,
    *,
    alias: str,
    cli: str,
    model_id: str,
    efforts_raw: str,
    quota_pool: str | None = None,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Add or replace a model alias in the target layer."""
    _validate_scope(scope)
    if cli not in ALLOWED_CLIS:
        raise PersonaConfigError(
            f"Unsupported cli '{cli}'; allowed: {', '.join(sorted(ALLOWED_CLIS))}"
        )
    efforts = [item.strip() for item in efforts_raw.split(",") if item.strip()]
    if not efforts:
        raise PersonaConfigError(f"Invalid efforts '{efforts_raw}'; must list at least one effort")
    entry: dict[str, Any] = {"cli": cli, "id": model_id, "efforts": efforts}
    if quota_pool is not None:
        entry["quota_pool"] = quota_pool
    _pc.derive_quota_pool(entry, alias)

    def _mutate(layer: dict[str, Any]) -> None:
        models = layer.setdefault("models", {})
        if not isinstance(models, dict):
            raise PersonaConfigError("Invalid 'models' section; expected JSON object")
        models[alias] = entry

    _pc.locked_update_layer(project_root, scope, _mutate, real_home=real_home)
    print(f"Added model '{alias}' ({cli}: {model_id}) in {scope} scope.")
    return 0


def _find_alias_references(cfg: Mapping[str, Any], alias: str) -> list[str]:
    refs: list[str] = []
    for preset_name, preset_map in cfg.get("presets", {}).items():
        if not isinstance(preset_map, Mapping):
            continue
        for persona_name, binding in preset_map.items():
            if not isinstance(binding, Mapping):
                continue
            if binding.get("model") == alias:
                refs.append(f"presets.{preset_name}.{persona_name}.model")
            if binding.get("fallback_model") == alias:
                refs.append(f"presets.{preset_name}.{persona_name}.fallback_model")
    for persona_name, ov in cfg.get("overrides", {}).items():
        if not isinstance(ov, Mapping):
            continue
        if ov.get("model") == alias:
            refs.append(f"overrides.{persona_name}.model")
        if ov.get("fallback_model") == alias:
            refs.append(f"overrides.{persona_name}.fallback_model")
    return refs


def cmd_models_remove(
    project_root: Path,
    *,
    alias: str,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Remove a model alias from the target layer if nothing in merged config references it."""
    _validate_scope(scope)
    merged = _pc.load_persona_config(project_root, real_home=real_home)
    refs = _find_alias_references(merged, alias)
    if refs:
        raise PersonaConfigError(
            f"Cannot remove model alias '{alias}': referenced by {', '.join(refs)}"
        )

    def _mutate(layer: dict[str, Any]) -> None:
        models = layer.get("models")
        if not isinstance(models, dict) or alias not in models:
            raise PersonaConfigError(
                f"Model alias '{alias}' is not defined in the {scope} layer"
            )
        models.pop(alias)

    _pc.locked_update_layer(project_root, scope, _mutate, real_home=real_home)
    print(f"Removed model '{alias}' from {scope} scope.")
    return 0


def _write_active_preset(
    project_root: Path,
    *,
    name: str,
    scope: str,
    real_home: Path | None = None,
) -> dict[str, Any]:
    _validate_scope(scope)

    def _mutate(layer: dict[str, Any]) -> None:
        layer["active_preset"] = name

    merged: dict[str, Any] = _pc.locked_update_layer(
        project_root,
        scope,
        _mutate,
        real_home=real_home,
    )
    return merged


def _masked_layer_for_binding(
    binding: PersonaBinding,
    expected_alias: str,
    expected_effort: str,
    fallback_layer: str,
) -> str | None:
    differing_layers: list[str] = []
    if binding.alias != expected_alias:
        differing_layers.append(binding.sources.get("model", fallback_layer))
    if binding.effort != expected_effort:
        differing_layers.append(binding.sources.get("effort", fallback_layer))
    if not differing_layers:
        return None
    rank = _pc._LAYER_RANK
    return max(differing_layers, key=lambda layer: int(rank.get(layer, -1)))


def cmd_preset(
    project_root: Path,
    *,
    name: str,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Set active_preset in the global or project layer."""
    _write_active_preset(project_root, name=name, scope=scope, real_home=real_home)
    if scope == "global":
        proj_path = _pc.project_config_path(project_root)
        if proj_path.is_file():
            try:
                proj_data = json.loads(proj_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                proj_data = {}
            if isinstance(proj_data, Mapping):
                if "active_preset" in proj_data and proj_data["active_preset"] != name:
                    print(
                        f"Warning: project layer masks global preset '{name}' with "
                        f"'{proj_data['active_preset']}'.",
                        file=sys.stderr,
                    )
                elif proj_data.get("overrides"):
                    masked = ", ".join(sorted(proj_data["overrides"]))
                    print(
                        f"Warning: project overrides ({masked}) remain active over "
                        f"global preset '{name}'.",
                        file=sys.stderr,
                    )
    print(f"Set active_preset to '{name}' in {scope} scope.")
    return 0


def cmd_provider(
    project_root: Path,
    *,
    provider: str,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Apply the mapped preset for a provider shortcut and print resulting bindings."""
    preset_name = PROVIDER_PRESETS.get(provider)
    if preset_name is None:
        allowed = ", ".join(PROVIDER_PRESETS)
        raise PersonaConfigError(
            f"Unknown provider '{provider}'; expected one of {allowed}"
        )
    merged = _write_active_preset(
        project_root,
        name=preset_name,
        scope=scope,
        real_home=real_home,
    )
    bindings = _pc.resolve_all_personas(project_root, real_home=real_home)
    preset_bindings = merged["presets"][preset_name]

    print(f"active_preset: {preset_name} ({scope})")
    for persona in PERSONAS:
        b = bindings[persona]
        print(f"{persona}: {b.cli} {b.model_id} {b.effort}")
        expected = preset_bindings[persona]
        mask_layer = _masked_layer_for_binding(
            b,
            str(expected["model"]),
            str(expected["effort"]),
            scope,
        )
        if mask_layer is not None:
            print(
                f"warning: {persona} is still bound to {b.alias} {b.effort} by the "
                f'{mask_layer} layer; run "dev_config.py reset {persona} --scope {mask_layer}"',
                file=sys.stderr,
            )
    return 0


def cmd_set(
    project_root: Path,
    *,
    persona: str,
    model: str,
    effort: str,
    fallback: str | None = None,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Set persona model/effort override (and optional fallback_model) in target scope."""
    _validate_scope(scope)
    _validate_persona_name(persona)

    def _mutate(layer: dict[str, Any]) -> None:
        overrides = layer.setdefault("overrides", {})
        if not isinstance(overrides, dict):
            raise PersonaConfigError("Invalid 'overrides' section; expected JSON object")
        entry: dict[str, Any] = {"model": model, "effort": effort}
        if fallback is not None:
            entry["fallback_model"] = fallback
        overrides[persona] = entry

    _pc.locked_update_layer(project_root, scope, _mutate, real_home=real_home)
    print(f"Set {persona} -> {model} ({effort}) in {scope} scope.")
    return 0


def cmd_reset(
    project_root: Path,
    *,
    persona: str | None = None,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Clear one persona override or all overrides in target scope."""
    _validate_scope(scope)
    if persona is not None:
        _validate_persona_name(persona)

    def _mutate(layer: dict[str, Any]) -> None:
        if persona is None:
            layer["overrides"] = {}
            return
        overrides = layer.get("overrides")
        if isinstance(overrides, dict):
            overrides.pop(persona, None)

    _pc.locked_update_layer(project_root, scope, _mutate, real_home=real_home)
    target = persona if persona is not None else "all personas"
    print(f"Reset overrides for {target} in {scope} scope.")
    return 0


def cmd_low_quota(
    project_root: Path,
    action: str,
    *,
    hours: float = _pc.DEFAULT_LOW_QUOTA_HOURS,
    profile: str | None = None,
    now: datetime | None = None,
    real_home: Path | None = None,
) -> int:
    """Enable or disable profile-scoped low-quota mode in the global configuration layer."""
    if action not in ("on", "off"):
        raise PersonaConfigError(f"Invalid low-quota action '{action}'; expected 'on' or 'off'")
    if action == "on" and hours <= 0:
        raise PersonaConfigError(f"Invalid --for duration '{hours}'; must be positive")

    resolved_profile = (
        profile.strip()
        if isinstance(profile, str) and profile.strip()
        else _detect_profile(project_root, real_home=real_home)
    )
    current_now = now if now is not None else datetime.now(timezone.utc)
    if current_now.tzinfo is None:
        current_now = current_now.replace(tzinfo=timezone.utc)
    else:
        current_now = current_now.astimezone(timezone.utc)

    def _mutate(layer: dict[str, Any]) -> None:
        low_quota = layer.setdefault("low_quota", {})
        if not isinstance(low_quota, dict):
            raise PersonaConfigError("Invalid 'low_quota' section; expected JSON object")
        if action == "on":
            expires_dt = current_now + timedelta(hours=hours)
            low_quota[resolved_profile] = {
                "enabled": True,
                "expires_at": expires_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
        else:
            low_quota.pop(resolved_profile, None)

    _pc.locked_update_layer(project_root, "global", _mutate, real_home=real_home)
    if action == "on":
        print(f"Enabled low-quota mode for profile '{resolved_profile}' for {hours}h.")
    else:
        print(f"Disabled low-quota mode for profile '{resolved_profile}'.")
    return 0


def cmd_checkpoint(
    project_root: Path,
    *,
    turns: int,
    scope: str = "global",
    real_home: Path | None = None,
) -> int:
    """Set max_orchestrator_turns_before_checkpoint in target scope."""
    _validate_scope(scope)
    if turns < 1:
        raise PersonaConfigError(
            f"Invalid checkpoint turns '{turns}'; must be a positive integer"
        )

    def _mutate(layer: dict[str, Any]) -> None:
        policy = layer.setdefault("checkpoint_policy", {})
        if not isinstance(policy, dict):
            raise PersonaConfigError("Invalid 'checkpoint_policy' section; expected JSON object")
        policy["max_orchestrator_turns_before_checkpoint"] = turns

    _pc.locked_update_layer(project_root, scope, _mutate, real_home=real_home)
    print(f"Set max_orchestrator_turns_before_checkpoint={turns} in {scope} scope.")
    return 0


def cmd_quota_check(
    project_root: Path,
    *,
    personas: Sequence[str] | None = None,
    json_output: bool = False,
    fetcher: Callable[[str], dict[str, Any]] | None = None,
    real_home: Path | None = None,
) -> int:
    """Check quota sufficiency for resolved personas against quota_thresholds."""
    target_personas = tuple(personas) if personas is not None else PERSONAS
    for persona in target_personas:
        _validate_persona_name(persona)

    review_mod = _load_external_review_module()
    thresholds = _load_quota_thresholds(project_root, review_mod)
    active_fetcher = fetcher if fetcher is not None else review_mod._default_quota_fetcher

    quota_cache: dict[str, dict[str, Any]] = {}
    results: list[dict[str, Any]] = []
    for persona in target_personas:
        binding = _pc.resolve_persona(persona, project_root, real_home=real_home)
        if binding.cli not in quota_cache:
            try:
                quota_cache[binding.cli] = dict(active_fetcher(binding.cli) or {})
            except Exception:
                quota_cache[binding.cli] = {}
        ok, quota_line, warning = _evaluate_binding_quota(
            binding,
            quota_cache[binding.cli],
            thresholds,
        )
        results.append(
            {
                "persona": persona,
                "cli": binding.cli,
                "alias": binding.alias,
                "sufficient": ok,
                "quota_line": quota_line,
                "warning": warning,
            }
        )

    overall_sufficient = all(item["sufficient"] for item in results)
    if json_output:
        print(json.dumps({"sufficient": overall_sufficient, "personas": results}, indent=2))
    else:
        for item in results:
            state = "OK" if item["sufficient"] else "INSUFFICIENT"
            detail = item["quota_line"] or item["warning"] or ""
            print(f"{item['persona']} ({item['cli']}/{item['alias']}): {state} [{detail}]")
    return 0 if overall_sufficient else 2


def cmd_resolve(
    project_root: Path,
    *,
    persona: str,
    fmt: str = "json",
    mode: str = "write",
    real_home: Path | None = None,
) -> int:
    """Resolve one persona binding as JSON or shell-joined dispatch argv."""
    _validate_persona_name(persona)
    if fmt not in ("json", "argv"):
        raise PersonaConfigError(f"Invalid format '{fmt}'; expected 'json' or 'argv'")
    if mode not in ("read-only", "write"):
        raise PersonaConfigError(f"Invalid mode '{mode}'; expected 'read-only' or 'write'")

    binding = _pc.resolve_persona(persona, project_root, real_home=real_home)
    argv = _pc.build_dispatch_argv(binding, mode)
    if fmt == "argv":
        print(shlex.join(argv))
        return 0
    payload = asdict(binding)
    payload["argv"] = argv
    print(json.dumps(payload, indent=2))
    return 0


def _normalize_argv(argv: Sequence[str]) -> list[str]:
    tokens = list(argv)
    normalized: list[str] = []
    has_subcommand = False
    skip_next = False
    for tok in tokens:
        if skip_next:
            normalized.append(tok)
            skip_next = False
            continue
        if tok == "--provider":
            normalized.append(tok)
            skip_next = True
            continue
        if tok in _SUBCOMMANDS:
            has_subcommand = True
        if tok == "--models":
            normalized.append("models")
        elif tok == "--low-quota":
            normalized.append("low-quota")
        else:
            normalized.append(tok)
    return tokens if has_subcommand else normalized


def _add_top_level_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project-root",
        type=Path,
        default=None,
        help="Repository root (defaults to current working directory).",
    )
    parser.add_argument(
        "--provider",
        default=None,
        help="Bind all personas to one provider's preset (agy, claude, codex).",
    )
    parser.add_argument(
        "--scope",
        default=argparse.SUPPRESS,
        help="Target configuration layer ('global' or 'project'; default: global).",
    )


def _build_parser() -> _DevConfigParser:
    parser = _DevConfigParser(prog="dev_config.py")
    _add_top_level_options(parser)
    sub = parser.add_subparsers(dest="command", required=False, parser_class=_DevConfigParser)

    p_status = sub.add_parser("status", help="Show resolved persona bindings and warnings.")
    p_status.add_argument("--json", action="store_true")

    p_models = sub.add_parser("models", help="Inspect or modify the model catalogue.")
    p_models.add_argument("--persona", default=None)
    p_models.add_argument("--json", action="store_true")
    models_sub = p_models.add_subparsers(dest="models_action", parser_class=_DevConfigParser)

    p_madd = models_sub.add_parser("add", help="Add or replace a model alias.")
    p_madd.add_argument("alias")
    p_madd.add_argument("--cli", required=True)
    p_madd.add_argument("--id", required=True, dest="model_id")
    p_madd.add_argument("--efforts", required=True)
    p_madd.add_argument("--quota-pool", default=None)
    p_madd.add_argument("--scope", default=argparse.SUPPRESS)

    p_mrm = models_sub.add_parser("remove", help="Remove a model alias from a layer.")
    p_mrm.add_argument("alias")
    p_mrm.add_argument("--scope", default=argparse.SUPPRESS)

    p_preset = sub.add_parser("preset", help="Select active preset.")
    p_preset.add_argument("name")
    p_preset.add_argument("--scope", default=argparse.SUPPRESS)

    p_set = sub.add_parser("set", help="Override a persona model and effort.")
    p_set.add_argument("persona")
    p_set.add_argument("model")
    p_set.add_argument("effort")
    p_set.add_argument("--fallback", default=None)
    p_set.add_argument("--scope", default=argparse.SUPPRESS)

    p_reset = sub.add_parser("reset", help="Clear persona overrides.")
    p_reset.add_argument("persona", nargs="?", default=None)
    p_reset.add_argument("--scope", default=argparse.SUPPRESS)

    p_lq = sub.add_parser("low-quota", help="Toggle profile-scoped low-quota mode.")
    p_lq.add_argument("action")
    p_lq.add_argument("--for", dest="hours", type=float, default=_pc.DEFAULT_LOW_QUOTA_HOURS)
    p_lq.add_argument("--profile", default=None)

    p_cp = sub.add_parser("checkpoint", help="Configure turn budget between checkpoints.")
    p_cp.add_argument("--turns", type=int, required=True)
    p_cp.add_argument("--scope", default=argparse.SUPPRESS)

    p_qc = sub.add_parser("quota-check", help="Evaluate quota gate for personas.")
    p_qc.add_argument("--personas", default=None)
    p_qc.add_argument("--json", action="store_true")

    p_res = sub.add_parser("resolve", help="Resolve persona binding or dispatch argv.")
    p_res.add_argument("persona")
    p_res.add_argument("--format", dest="fmt", default="json")
    p_res.add_argument("--mode", default="write")

    return parser


def _dispatch_args(args: argparse.Namespace, project_root: Path) -> int:
    cmd = args.command
    if getattr(args, "provider", None) is not None:
        if cmd is not None:
            raise PersonaConfigError(f"Cannot combine --provider with subcommand '{cmd}'")
        return cmd_provider(
            project_root,
            provider=args.provider,
            scope=getattr(args, "scope", "global"),
        )

    scope = getattr(args, "scope", "global")
    scoped = (
        cmd in ("preset", "set", "reset", "checkpoint")
        or (cmd == "models" and args.models_action in ("add", "remove"))
    )
    if hasattr(args, "scope") and not scoped:
        raise PersonaConfigError(f"Subcommand '{cmd}' does not accept --scope")

    if cmd == "status":
        return cmd_status(project_root, json_output=bool(args.json))
    if cmd == "models":
        if args.models_action == "add":
            return cmd_models_add(
                project_root,
                alias=args.alias,
                cli=args.cli,
                model_id=args.model_id,
                efforts_raw=args.efforts,
                quota_pool=args.quota_pool,
                scope=scope,
            )
        if args.models_action == "remove":
            return cmd_models_remove(project_root, alias=args.alias, scope=scope)
        return cmd_models(project_root, persona=args.persona, json_output=bool(args.json))
    if cmd == "preset":
        return cmd_preset(project_root, name=args.name, scope=scope)
    if cmd == "set":
        return cmd_set(
            project_root,
            persona=args.persona,
            model=args.model,
            effort=args.effort,
            fallback=args.fallback,
            scope=scope,
        )
    if cmd == "reset":
        return cmd_reset(project_root, persona=args.persona, scope=scope)
    if cmd == "low-quota":
        return cmd_low_quota(
            project_root,
            args.action,
            hours=args.hours,
            profile=args.profile,
        )
    if cmd == "checkpoint":
        return cmd_checkpoint(project_root, turns=args.turns, scope=scope)
    if cmd == "quota-check":
        parsed_personas: tuple[str, ...] | None = None
        if args.personas is not None:
            items = tuple(p.strip() for p in args.personas.split(",") if p.strip())
            if not items:
                raise PersonaConfigError(f"Invalid --personas '{args.personas}'")
            parsed_personas = items
        return cmd_quota_check(
            project_root,
            personas=parsed_personas,
            json_output=bool(args.json),
        )
    if cmd == "resolve":
        return cmd_resolve(project_root, persona=args.persona, fmt=args.fmt, mode=args.mode)
    raise PersonaConfigError(f"Unknown command '{cmd}'")


def _dispatch_provider_shortcut(
    normalized: Sequence[str],
    parser: _DevConfigParser,
) -> int:
    top_parser = _DevConfigParser(prog="dev_config.py", add_help=False)
    _add_top_level_options(top_parser)
    top_args, rest = top_parser.parse_known_args(normalized)
    if rest:
        subcmd = next((tok for tok in rest if tok in _SUBCOMMANDS), None)
        if subcmd is not None:
            raise PersonaConfigError(f"Cannot combine --provider with subcommand '{subcmd}'")
        parser.error(f"unrecognized arguments: {' '.join(rest)}")
    if top_args.provider is None:
        parser.error("a subcommand or --provider is required")
    project_root = (top_args.project_root or Path.cwd()).resolve()
    return cmd_provider(
        project_root,
        provider=top_args.provider,
        scope=getattr(top_args, "scope", "global"),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    raw = sys.argv[1:] if argv is None else argv
    normalized = _normalize_argv(raw)
    parser = _build_parser()
    has_help = any(tok in ("-h", "--help") for tok in normalized)
    has_provider = any(
        tok == "--provider" or tok.startswith("--provider=") for tok in normalized
    )
    try:
        if has_provider and not has_help:
            return _dispatch_provider_shortcut(normalized, parser)

        args = parser.parse_args(normalized)
        if args.provider is None and args.command is None:
            parser.error("a subcommand or --provider is required")
        project_root = (args.project_root or Path.cwd()).resolve()
        return _dispatch_args(args, project_root)
    except PersonaConfigError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
