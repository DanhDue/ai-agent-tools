"""Unit and integration tests for layered task review and fix pass limits.

Covers BDD scenarios:
- TRC-HP-01: Layered persona configuration resolves default and overridden task review and fix pass limits
- TRC-EC-01: Invalid or boolean task review limit values in personas.json raise PersonaConfigError
- TRC-FR-01: Missing optional persona config layers fall back to kit defaults while malformed JSON fails closed
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
KIT_DEFAULTS_FILE = SCRIPTS_DIR / "personas.default.json"
REPO_PROJECT_PERSONAS_FILE = REPO_ROOT / ".agents" / "config" / "personas.json"
DEV_CONFIG_SCRIPT = SCRIPTS_DIR / "dev_config.py"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import persona_config  # noqa: E402


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _run_dev_config(
    args: list[str],
    *,
    cwd: Path,
    real_home: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HOME"] = str(real_home)
    env["REAL_HOME"] = str(real_home)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
        "AGY_ASSISTANT_MODEL",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(DEV_CONFIG_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_trc_hp_01_layered_task_review_limits_and_status_json(tmp_path: Path) -> None:
    """TRC-HP-01: Resolve default and overridden task review/fix limits and expose them via status."""
    assert getattr(persona_config, "resolve_task_review_limits", None) is not None, (
        "persona_config.resolve_task_review_limits must exist"
    )
    assert getattr(persona_config, "DEFAULT_MAX_TASK_REVIEW_PASSES", None) == 2
    assert getattr(persona_config, "DEFAULT_MAX_FIX_PASSES", None) == 1

    kit_data = json.loads(KIT_DEFAULTS_FILE.read_text(encoding="utf-8"))
    assert kit_data["max_task_review_passes"] == 2
    assert kit_data["max_fix_passes"] == 1

    assert REPO_PROJECT_PERSONAS_FILE.is_file(), (
        f"Missing repo project config: {REPO_PROJECT_PERSONAS_FILE}"
    )
    repo_proj_data = json.loads(REPO_PROJECT_PERSONAS_FILE.read_text(encoding="utf-8"))
    assert repo_proj_data == {
        "schema_version": 1,
        "max_task_review_passes": 2,
        "max_fix_passes": 1,
    }

    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()

    assert persona_config.resolve_task_review_limits(project, real_home=real_home) == (
        2,
        1,
    )
    assert persona_config.resolve_task_review_limits(
        REPO_ROOT, real_home=real_home
    ) == (2, 1)

    res_default_json = _run_dev_config(
        ["status", "--json"], cwd=project, real_home=real_home
    )
    assert res_default_json.returncode == 0, res_default_json.stderr
    status_payload = json.loads(res_default_json.stdout)
    assert status_payload["task_review_limits"] == {
        "max_task_review_passes": 2,
        "max_fix_passes": 1,
    }

    res_default_human = _run_dev_config(["status"], cwd=project, real_home=real_home)
    assert res_default_human.returncode == 0, res_default_human.stderr
    assert "max_task_review_passes=2" in res_default_human.stdout
    assert "max_fix_passes=1" in res_default_human.stdout

    _write_json(
        real_home / ".d3nexus" / "personas.json",
        {"schema_version": 1, "max_task_review_passes": 3, "max_fix_passes": 2},
    )
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"schema_version": 1, "max_fix_passes": 1},
    )

    assert persona_config.resolve_task_review_limits(project, real_home=real_home) == (
        3,
        1,
    )

    res_override_json = _run_dev_config(
        ["status", "--json"], cwd=project, real_home=real_home
    )
    assert res_override_json.returncode == 0, res_override_json.stderr
    override_payload = json.loads(res_override_json.stdout)
    assert override_payload["task_review_limits"] == {
        "max_task_review_passes": 3,
        "max_fix_passes": 1,
    }


@pytest.mark.parametrize(
    ("override_payload", "bad_key"),
    [
        ({"schema_version": 1, "max_task_review_passes": 0}, "max_task_review_passes"),
        ({"schema_version": 1, "max_task_review_passes": -1}, "max_task_review_passes"),
        (
            {"schema_version": 1, "max_task_review_passes": True},
            "max_task_review_passes",
        ),
        (
            {"schema_version": 1, "max_task_review_passes": "2"},
            "max_task_review_passes",
        ),
        (
            {"schema_version": 1, "max_task_review_passes": False},
            "max_task_review_passes",
        ),
        (
            {"schema_version": 1, "max_task_review_passes": None},
            "max_task_review_passes",
        ),
        ({"schema_version": 1, "max_fix_passes": -1}, "max_fix_passes"),
        ({"schema_version": 1, "max_fix_passes": False}, "max_fix_passes"),
        ({"schema_version": 1, "max_fix_passes": True}, "max_fix_passes"),
        ({"schema_version": 1, "max_fix_passes": "1"}, "max_fix_passes"),
        ({"schema_version": 1, "max_fix_passes": None}, "max_fix_passes"),
    ],
)
def test_trc_ec_01_invalid_task_review_limits_raise_persona_config_error(
    tmp_path: Path,
    override_payload: dict[str, Any],
    bad_key: str,
) -> None:
    """TRC-EC-01: Invalid or boolean task review limit values raise PersonaConfigError naming key."""
    assert getattr(persona_config, "resolve_task_review_limits", None) is not None, (
        "persona_config.resolve_task_review_limits must exist"
    )
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(project / ".agents" / "config" / "personas.json", override_payload)

    with pytest.raises(persona_config.PersonaConfigError, match=bad_key):
        persona_config.load_persona_config(project, real_home=real_home)

    with pytest.raises(persona_config.PersonaConfigError, match=bad_key):
        persona_config.resolve_task_review_limits(project, real_home=real_home)


def test_trc_ec_01_boundary_zero_fix_passes_and_merged_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TRC-EC-01: Boundary valid limits (1, 0), fallback defaults, and merged validator branches."""
    assert getattr(persona_config, "resolve_task_review_limits", None) is not None, (
        "persona_config.resolve_task_review_limits must exist"
    )
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {"schema_version": 1, "max_task_review_passes": 1, "max_fix_passes": 0},
    )
    assert persona_config.resolve_task_review_limits(project, real_home=real_home) == (
        1,
        0,
    )

    base_cfg = json.loads(KIT_DEFAULTS_FILE.read_text(encoding="utf-8"))
    base_cfg.pop("max_task_review_passes", None)
    base_cfg.pop("max_fix_passes", None)
    persona_config.validate_merged_config(base_cfg)

    for key, bad_val in (
        ("max_task_review_passes", 0),
        ("max_task_review_passes", True),
        ("max_fix_passes", -1),
        ("max_fix_passes", False),
    ):
        bad_cfg = dict(base_cfg)
        bad_cfg[key] = bad_val
        with pytest.raises(persona_config.PersonaConfigError, match=key):
            persona_config.validate_merged_config(bad_cfg)

    monkeypatch.setattr(persona_config, "load_persona_config", lambda *_a, **_kw: {})
    assert persona_config.resolve_task_review_limits(project, real_home=real_home) == (
        2,
        1,
    )


def test_trc_fr_01_missing_layers_and_malformed_json_fail_closed(
    tmp_path: Path,
) -> None:
    """TRC-FR-01: Missing layers fall back to kit defaults; malformed JSON fails closed."""
    assert getattr(persona_config, "resolve_task_review_limits", None) is not None, (
        "persona_config.resolve_task_review_limits must exist"
    )
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()

    assert persona_config.resolve_task_review_limits(
        project, real_home=str(real_home)
    ) == (2, 1)
    assert persona_config.resolve_task_review_limits(
        tmp_path / "unconfigured_workspace",
        real_home=real_home,
    ) == (2, 1)

    proj_cfg = project / ".agents" / "config" / "personas.json"
    proj_cfg.parent.mkdir(parents=True, exist_ok=True)
    proj_cfg.write_text("{bad", encoding="utf-8")

    with pytest.raises(
        persona_config.PersonaConfigError, match=r"\.agents/config/personas\.json"
    ):
        persona_config.resolve_task_review_limits(project, real_home=real_home)

    proj_cfg.unlink()
    global_cfg = real_home / ".d3nexus" / "personas.json"
    global_cfg.parent.mkdir(parents=True, exist_ok=True)
    global_cfg.write_text("{bad", encoding="utf-8")

    with pytest.raises(
        persona_config.PersonaConfigError, match=r"\.d3nexus/personas\.json"
    ):
        persona_config.resolve_task_review_limits(project, real_home=real_home)
