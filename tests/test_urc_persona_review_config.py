"""Unit and integration tests for layered external review config and pass limits.

Covers BDD scenarios:
- URC-HP-01: Kit defaults resolve all four independent pass limits and external review settings
- URC-EC-01: Review provider model accepts both catalogue aliases with effort expansion and raw model IDs
- URC-EC-02: Legacy review_config.json serves as read-only fallback only for keys absent from both project and global layers
- URC-AR-01: Global personas.json beats auto-seeded legacy .devtool/review_config.json while project personas.json beats global
- URC-FR-01: Invalid pass limits, duplicate or unknown priorities, out-of-range thresholds, and CLI-mismatched aliases are rejected with PersonaConfigError
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
KIT_DEFAULTS_FILE = SCRIPTS_DIR / "personas.default.json"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import persona_config  # noqa: E402


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _require_review_api() -> tuple[Any, Any]:
    resolve_limits = getattr(persona_config, "resolve_review_limits", None)
    resolve_config = getattr(persona_config, "resolve_review_config", None)
    if resolve_limits is None:
        pytest.fail("persona_config.resolve_review_limits is not implemented yet")
    if resolve_config is None:
        pytest.fail("persona_config.resolve_review_config is not implemented yet")
    return resolve_limits, resolve_config


def _assert_kit_defaults_resolve_limits_and_review_config(tmp_path: Path) -> None:
    resolve_limits, resolve_config = _require_review_api()

    real_home = tmp_path / "home"
    project = tmp_path / "repo"
    real_home.mkdir()
    project.mkdir()

    assert getattr(persona_config, "DEFAULT_MAX_PRINCIPAL_REVIEW_PASSES", None) == 3
    assert getattr(persona_config, "DEFAULT_MAX_CROSS_MODEL_REVIEW_PASSES", None) == 3
    assert getattr(persona_config, "REVIEW_PRIORITY_PROVIDERS", None) == (
        "claude",
        "codex",
        "kiro",
        "agy",
    )
    assert getattr(persona_config, "REVIEW_PROVIDERS", None) == (
        "claude",
        "codex",
        "kiro",
        "agy",
        "ollama",
    )
    assert getattr(persona_config, "REVIEW_THINKING_LEVELS", None) == (
        "none",
        "light",
        "low",
        "medium",
        "high",
        "xhigh",
        "extra-high",
    )
    assert getattr(persona_config, "DEFAULT_REVIEW_QUOTA_THRESHOLDS", None) == {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "kiro_min_fraction": 0.03,
        "kiro_min_credits": 15.0,
        "agy_argon_min_fraction": 0.10,
    }

    kit_data = json.loads(KIT_DEFAULTS_FILE.read_text(encoding="utf-8"))
    assert kit_data["max_task_review_passes"] == 2
    assert kit_data["max_fix_passes"] == 1
    assert kit_data["max_principal_review_passes"] == 3
    assert kit_data["max_cross_model_review_passes"] == 3
    assert kit_data["review"]["provider_priority"] == [
        "claude",
        "codex",
        "kiro",
        "agy",
    ]

    limits = resolve_limits(project, real_home=real_home)
    assert limits.max_task_review_passes == 2
    assert limits.max_fix_passes == 1
    assert limits.max_principal_review_passes == 3
    assert limits.max_cross_model_review_passes == 3
    assert limits.sources == {
        "max_task_review_passes": "kit",
        "max_fix_passes": "kit",
        "max_principal_review_passes": "kit",
        "max_cross_model_review_passes": "kit",
    }
    assert persona_config.resolve_task_review_limits(project, real_home=real_home) == (
        2,
        1,
    )

    cfg = resolve_config(project, real_home=real_home)
    assert cfg.provider_priority == ("claude", "codex", "kiro", "agy")
    assert cfg.sources["provider_priority"] == "kit"
    assert cfg.limits == limits
    assert cfg.max_rounds_for_kind("principal") == 3
    assert cfg.max_rounds_for_kind("code") == 3
    assert cfg.max_rounds_for_kind("epic") == 3

    assert cfg.providers["claude"].model == "claude-opus"
    assert cfg.providers["claude"].model_id == "opus"
    assert cfg.providers["claude"].effort == "high"
    assert cfg.providers["claude"].host is None
    assert cfg.providers["claude"].source == "kit"

    assert cfg.providers["codex"].model == "codex-gpt"
    assert cfg.providers["codex"].model_id == "gpt-6.1-sol"
    assert cfg.providers["codex"].effort == "high"
    assert cfg.providers["codex"].host is None
    assert cfg.providers["codex"].source == "kit"

    assert cfg.providers["kiro"].model == "kiro-opus"
    assert cfg.providers["kiro"].model_id == "claude-opus-5.5"
    assert cfg.providers["kiro"].effort == "high"
    assert cfg.providers["kiro"].host is None
    assert cfg.providers["kiro"].source == "kit"

    assert cfg.providers["agy"].model == "argon"
    assert cfg.providers["agy"].model_id == "gemini-4-argon-high"
    assert cfg.providers["agy"].effort == "high"
    assert cfg.providers["agy"].host is None
    assert cfg.providers["agy"].source == "kit"

    assert cfg.providers["ollama"].model == "gemma4:31b-it-qat"
    assert cfg.providers["ollama"].model_id == "gemma4:31b-it-qat"
    assert cfg.providers["ollama"].effort == "high"
    assert cfg.providers["ollama"].host == "http://localhost:11434"
    assert cfg.providers["ollama"].source == "kit"

    assert cfg.quota_thresholds == {
        "5h_min_fraction": 0.15,
        "7d_min_fraction": 0.02,
        "kiro_min_fraction": 0.03,
        "kiro_min_credits": 15.0,
        "agy_argon_min_fraction": 0.10,
    }
    for key in cfg.quota_thresholds:
        assert cfg.sources[f"quota_thresholds.{key}"] == "kit"


def test_urc_hp_01_kit_defaults_resolve_limits_and_review_config(
    tmp_path: Path,
) -> None:
    """URC-HP-01: Top-level entry point for V1 RED and default kit resolution check."""
    _assert_kit_defaults_resolve_limits_and_review_config(tmp_path)


class Test_Integration:
    """[Tier C - Integration] Layered filesystem integration tests for persona_config review schema."""

    def test_urc_hp_01_kit_defaults_resolve_limits_and_review_config(
        self, tmp_path: Path
    ) -> None:
        """URC-HP-01: Kit defaults resolve all four pass limits and external review settings."""
        _assert_kit_defaults_resolve_limits_and_review_config(tmp_path)

    def test_urc_ec_01_review_provider_alias_expansion_and_raw_model_ids(
        self, tmp_path: Path
    ) -> None:
        """URC-EC-01: Review providers expand catalogue aliases, fixed-effort aliases, and raw IDs."""
        _, resolve_config = _require_review_api()

        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        _write_json(
            real_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "review": {
                    "providers": {
                        "agy": {"model": "argon", "effort": "medium"},
                        "claude": {
                            "model": "claude-sonnet-4-6",
                            "thinking_level": "low",
                        },
                        "codex": {"model": "codex-gpt", "effort": "low"},
                    }
                },
            },
        )

        cfg = resolve_config(project, real_home=real_home)
        assert cfg.providers["agy"].model == "argon"
        assert cfg.providers["agy"].model_id == "gemini-4-argon-medium"
        assert cfg.providers["agy"].effort == "medium"
        assert cfg.providers["agy"].source == "global"

        assert cfg.providers["claude"].model == "claude-sonnet-4-6"
        assert cfg.providers["claude"].model_id == "claude-sonnet-4-6"
        assert cfg.providers["claude"].effort == "low"
        assert cfg.providers["claude"].source == "global"

        assert cfg.providers["codex"].model == "codex-gpt"
        assert cfg.providers["codex"].model_id == "gpt-6.1-sol"
        assert cfg.providers["codex"].effort == "low"
        assert cfg.providers["codex"].source == "global"

        _write_json(
            project / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "models": {
                    "custom-agy": {
                        "cli": "agy",
                        "id": "gemini-4-custom-{effort}",
                        "efforts": ["medium", "high"],
                    }
                },
                "review": {
                    "providers": {
                        "agy": {"model": "orchestrator-argon"},
                        "ollama": {
                            "model": "qwen2.5-coder:32b",
                            "host": "https://ollama.internal:11434",
                        },
                    }
                },
            },
        )

        cfg_fixed = resolve_config(project, real_home=real_home)
        assert cfg_fixed.providers["agy"].model == "orchestrator-argon"
        assert cfg_fixed.providers["agy"].model_id == "gemini-pro-orchestrator-g1-pro"
        assert cfg_fixed.providers["agy"].effort == "none"
        assert cfg_fixed.providers["agy"].source == "project"
        assert cfg_fixed.providers["ollama"].model_id == "qwen2.5-coder:32b"
        assert cfg_fixed.providers["ollama"].host == "https://ollama.internal:11434"
        assert cfg_fixed.providers["ollama"].source == "project"

        _write_json(
            project / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "models": {
                    "custom-agy": {
                        "cli": "agy",
                        "id": "gemini-4-custom-{effort}",
                        "efforts": ["medium", "high"],
                    }
                },
                "review": {
                    "providers": {
                        "agy": {"model": "custom-agy", "effort": "high"},
                    }
                },
            },
        )
        cfg_custom = resolve_config(project, real_home=real_home)
        assert cfg_custom.providers["agy"].model_id == "gemini-4-custom-high"
        assert cfg_custom.providers["agy"].effort == "high"
        assert cfg_custom.providers["agy"].source == "project"

    def test_urc_ec_02_legacy_review_config_read_only_fallback_and_warnings(
        self, tmp_path: Path
    ) -> None:
        """URC-EC-02: Legacy .devtool/review_config.json provides read-only fallback and warnings."""
        _, resolve_config = _require_review_api()

        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        legacy_path = project / ".devtool" / "review_config.json"
        _write_json(
            legacy_path,
            {
                "provider_priority": ["kiro", "agy"],
                "max_rounds": 5,
                "quota_thresholds": {"5h_min_fraction": 0.30},
                "providers": {
                    "codex": {"model": "gpt-legacy", "thinking_level": "medium"},
                    "ollama": {
                        "model": "qwen-legacy:latest",
                        "host": "http://127.0.0.1:11434",
                    },
                    "programmer": {
                        "model": "gemini-3.8-flash",
                        "thinking_level": "high",
                    },
                },
            },
        )
        before_bytes = legacy_path.read_bytes()

        cfg = resolve_config(project, real_home=real_home)
        assert legacy_path.read_bytes() == before_bytes

        assert cfg.provider_priority == ("kiro", "agy")
        assert cfg.sources["provider_priority"] == "legacy"

        assert cfg.limits.max_task_review_passes == 2
        assert cfg.limits.max_fix_passes == 1
        assert cfg.limits.max_principal_review_passes == 5
        assert cfg.limits.max_cross_model_review_passes == 5
        assert cfg.limits.sources["max_task_review_passes"] == "kit"
        assert cfg.limits.sources["max_fix_passes"] == "kit"
        assert cfg.limits.sources["max_principal_review_passes"] == "legacy"
        assert cfg.limits.sources["max_cross_model_review_passes"] == "legacy"
        assert cfg.max_rounds_for_kind("principal") == 5
        assert cfg.max_rounds_for_kind("code") == 5

        assert cfg.quota_thresholds["5h_min_fraction"] == 0.30
        assert cfg.sources["quota_thresholds.5h_min_fraction"] == "legacy"
        assert cfg.quota_thresholds["7d_min_fraction"] == 0.02
        assert cfg.sources["quota_thresholds.7d_min_fraction"] == "kit"

        assert cfg.providers["codex"].model == "gpt-legacy"
        assert cfg.providers["codex"].model_id == "gpt-legacy"
        assert cfg.providers["codex"].effort == "medium"
        assert cfg.providers["codex"].source == "legacy"
        assert cfg.sources["providers.codex"] == "legacy"

        assert cfg.providers["ollama"].model_id == "qwen-legacy:latest"
        assert cfg.providers["ollama"].host == "http://127.0.0.1:11434"
        assert cfg.providers["ollama"].source == "legacy"

        assert cfg.providers["claude"].model_id == "opus"
        assert cfg.providers["claude"].source == "kit"

        warnings = persona_config.detect_legacy_warnings(project, env={})
        joined = "\n".join(warnings)
        assert ".devtool/review_config.json" in joined
        assert "providers.programmer" in joined
        assert "dev-config review" in joined or "dev-config limits" in joined

        legacy_path.write_text("{corrupt json", encoding="utf-8")
        cfg_corrupt = resolve_config(project, real_home=real_home)
        assert cfg_corrupt.provider_priority == ("claude", "codex", "kiro", "agy")
        assert cfg_corrupt.sources["provider_priority"] == "kit"
        assert cfg_corrupt.limits.max_principal_review_passes == 3
        assert cfg_corrupt.limits.sources["max_principal_review_passes"] == "kit"

        legacy_path.write_text("[]", encoding="utf-8")
        cfg_list = resolve_config(project, real_home=real_home)
        assert cfg_list.sources["provider_priority"] == "kit"

        _write_json(
            legacy_path,
            {
                "provider_priority": ["ollama"],
                "max_rounds": True,
                "quota_thresholds": {
                    "5h_min_fraction": 2.5,
                    "kiro_min_credits": -5,
                    "unknown": 0.5,
                },
                "providers": {
                    "claude": {"model": "codex-gpt", "effort": "high"},
                    "codex": {"model": "   ", "thinking_level": "bogus"},
                    "ollama": {"model": "local-tag", "host": "ftp://bad"},
                },
            },
        )
        cfg_bad_legacy = resolve_config(project, real_home=real_home)
        assert cfg_bad_legacy.provider_priority == ("claude", "codex", "kiro", "agy")
        assert cfg_bad_legacy.sources["provider_priority"] == "kit"
        assert cfg_bad_legacy.limits.max_principal_review_passes == 3
        assert cfg_bad_legacy.limits.sources["max_principal_review_passes"] == "kit"
        assert cfg_bad_legacy.quota_thresholds["5h_min_fraction"] == 0.15
        assert cfg_bad_legacy.sources["quota_thresholds.5h_min_fraction"] == "kit"
        assert cfg_bad_legacy.providers["claude"].model_id == "opus"
        assert cfg_bad_legacy.providers["claude"].source == "kit"
        assert cfg_bad_legacy.providers["codex"].model_id == "gpt-6.1-sol"
        assert cfg_bad_legacy.providers["codex"].source == "kit"
        assert cfg_bad_legacy.providers["ollama"].model_id == "local-tag"
        assert cfg_bad_legacy.providers["ollama"].host == "http://localhost:11434"
        assert cfg_bad_legacy.providers["ollama"].source == "legacy"

    def test_urc_ar_01_global_beats_legacy_and_project_beats_global(
        self, tmp_path: Path
    ) -> None:
        """URC-AR-01: Global personas.json beats legacy review_config.json and project beats global."""
        _, resolve_config = _require_review_api()

        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        _write_json(
            project / ".devtool" / "review_config.json",
            {
                "provider_priority": ["claude", "codex", "kiro", "agy"],
                "max_rounds": 3,
                "quota_thresholds": {
                    "5h_min_fraction": 0.25,
                    "7d_min_fraction": 0.08,
                },
                "providers": {
                    "agy": {"model": "legacy-argon", "thinking_level": "medium"},
                },
            },
        )
        _write_json(
            real_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_fix_passes": 2,
                "max_principal_review_passes": 2,
                "review": {
                    "provider_priority": ["codex", "kiro"],
                    "quota_thresholds": {"5h_min_fraction": 0.20},
                    "providers": {
                        "agy": {"model": "argon"},
                    },
                },
            },
        )

        before_project = resolve_config(project, real_home=real_home)
        assert before_project.provider_priority == ("codex", "kiro")
        assert before_project.sources["provider_priority"] == "global"
        assert before_project.limits.max_fix_passes == 2
        assert before_project.limits.sources["max_fix_passes"] == "global"
        assert before_project.limits.max_principal_review_passes == 2
        assert before_project.limits.sources["max_principal_review_passes"] == "global"
        assert before_project.limits.max_cross_model_review_passes == 3
        assert (
            before_project.limits.sources["max_cross_model_review_passes"] == "legacy"
        )
        assert before_project.quota_thresholds["5h_min_fraction"] == 0.20
        assert before_project.sources["quota_thresholds.5h_min_fraction"] == "global"
        assert before_project.quota_thresholds["7d_min_fraction"] == 0.08
        assert before_project.sources["quota_thresholds.7d_min_fraction"] == "legacy"
        assert before_project.providers["agy"].model_id == "gemini-4-argon-high"
        assert before_project.providers["agy"].effort == "high"
        assert before_project.providers["agy"].source == "global"

        _write_json(
            project / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 1,
                "max_task_review_passes": 4,
                "max_fix_passes": 0,
                "review": {
                    "provider_priority": ["agy", "claude"],
                    "quota_thresholds": {"5h_min_fraction": 0.40},
                    "providers": {
                        "agy": {"effort": "low"},
                    },
                },
            },
        )

        after_project = resolve_config(project, real_home=real_home)
        assert after_project.provider_priority == ("agy", "claude")
        assert after_project.sources["provider_priority"] == "project"
        assert after_project.limits.max_principal_review_passes == 1
        assert after_project.limits.sources["max_principal_review_passes"] == "project"
        assert after_project.limits.max_cross_model_review_passes == 3
        assert after_project.limits.sources["max_cross_model_review_passes"] == "legacy"
        assert after_project.limits.max_task_review_passes == 4
        assert after_project.limits.sources["max_task_review_passes"] == "project"
        assert after_project.limits.max_fix_passes == 0
        assert after_project.limits.sources["max_fix_passes"] == "project"
        assert after_project.quota_thresholds["5h_min_fraction"] == 0.40
        assert after_project.sources["quota_thresholds.5h_min_fraction"] == "project"
        assert after_project.providers["agy"].model == "argon"
        assert after_project.providers["agy"].model_id == "gemini-4-argon-low"
        assert after_project.providers["agy"].effort == "low"
        assert after_project.providers["agy"].source == "project"

    @pytest.mark.parametrize(
        ("layer_payload", "expected_fragment"),
        [
            (
                {"schema_version": 1, "max_principal_review_passes": 0},
                "max_principal_review_passes",
            ),
            (
                {"schema_version": 1, "max_principal_review_passes": -2},
                "max_principal_review_passes",
            ),
            (
                {"schema_version": 1, "max_principal_review_passes": True},
                "max_principal_review_passes",
            ),
            (
                {"schema_version": 1, "max_principal_review_passes": "3"},
                "max_principal_review_passes",
            ),
            (
                {"schema_version": 1, "max_principal_review_passes": None},
                "max_principal_review_passes",
            ),
            (
                {"schema_version": 1, "max_cross_model_review_passes": 0},
                "max_cross_model_review_passes",
            ),
            (
                {"schema_version": 1, "max_cross_model_review_passes": True},
                "max_cross_model_review_passes",
            ),
            (
                {"schema_version": 1, "max_cross_model_review_passes": "3"},
                "max_cross_model_review_passes",
            ),
            ({"schema_version": 1, "max_fix_passes": -1}, "max_fix_passes"),
            ({"schema_version": 1, "max_fix_passes": True}, "max_fix_passes"),
            ({"schema_version": 1, "review": "not-an-object"}, "review"),
            (
                {"schema_version": 1, "review": {"unknown_review_key": 1}},
                "unknown_review_key",
            ),
            (
                {"schema_version": 1, "review": {"provider_priority": []}},
                "provider_priority",
            ),
            (
                {"schema_version": 1, "review": {"provider_priority": "claude"}},
                "provider_priority",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"provider_priority": ["claude", "claude"]},
                },
                "claude",
            ),
            (
                {"schema_version": 1, "review": {"provider_priority": ["ollama"]}},
                "ollama",
            ),
            (
                {"schema_version": 1, "review": {"provider_priority": ["bogus"]}},
                "bogus",
            ),
            (
                {"schema_version": 1, "review": {"provider_priority": [123]}},
                "provider_priority",
            ),
            (
                {"schema_version": 1, "review": {"quota_thresholds": "bad"}},
                "quota_thresholds",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"bogus_key": 0.1}},
                },
                "bogus_key",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"5h_min_fraction": 1.5}},
                },
                "5h_min_fraction",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"5h_min_fraction": -0.1}},
                },
                "5h_min_fraction",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"5h_min_fraction": True}},
                },
                "5h_min_fraction",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"5h_min_fraction": "0.15"}},
                },
                "5h_min_fraction",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"quota_thresholds": {"kiro_min_credits": -1.0}},
                },
                "kiro_min_credits",
            ),
            ({"schema_version": 1, "review": {"providers": "bad"}}, "providers"),
            (
                {
                    "schema_version": 1,
                    "review": {"providers": {"gemini": {"model": "x"}}},
                },
                "gemini",
            ),
            (
                {"schema_version": 1, "review": {"providers": {"claude": "bad"}}},
                "claude",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"providers": {"claude": {"model": "opus", "extra": 1}}},
                },
                "extra",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"providers": {"claude": {"model": ""}}},
                },
                "claude",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {"providers": {"claude": {"model": 123}}},
                },
                "claude",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {"claude": {"model": "opus", "effort": "ultra"}}
                    },
                },
                "effort",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {
                            "claude": {"model": "opus", "thinking_level": "ultra"}
                        }
                    },
                },
                "thinking_level",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {
                            "claude": {"model": "codex-gpt", "effort": "high"}
                        }
                    },
                },
                "codex-gpt",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {
                            "ollama": {"model": "claude-opus", "effort": "high"}
                        }
                    },
                },
                "claude-opus",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {"agy": {"model": "argon", "effort": "xhigh"}}
                    },
                },
                "xhigh",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {
                            "claude": {
                                "model": "opus",
                                "host": "http://localhost:11434",
                            }
                        }
                    },
                },
                "host",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {
                            "ollama": {
                                "model": "gemma4",
                                "host": "ftp://localhost:11434",
                            }
                        }
                    },
                },
                "host",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {"ollama": {"model": "gemma4", "host": "http://"}}
                    },
                },
                "host",
            ),
            (
                {
                    "schema_version": 1,
                    "review": {
                        "providers": {"ollama": {"model": "gemma4", "host": 123}}
                    },
                },
                "host",
            ),
        ],
    )
    def test_urc_fr_01_invalid_review_config_and_limits_raise_persona_config_error(
        self,
        tmp_path: Path,
        layer_payload: dict[str, Any],
        expected_fragment: str,
    ) -> None:
        """URC-FR-01: Invalid limits, priorities, thresholds, and provider configs raise PersonaConfigError."""
        _, resolve_config = _require_review_api()

        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        _write_json(project / ".agents" / "config" / "personas.json", layer_payload)

        with pytest.raises(persona_config.PersonaConfigError, match=expected_fragment):
            persona_config.load_persona_config(project, real_home=real_home)

        with pytest.raises(persona_config.PersonaConfigError, match=expected_fragment):
            resolve_config(project, real_home=real_home)

    def test_urc_fr_01_non_finite_thresholds_and_unknown_review_kind(
        self, tmp_path: Path
    ) -> None:
        """URC-FR-01: Non-finite float thresholds and unknown max_rounds_for_kind raise PersonaConfigError."""
        _, resolve_config = _require_review_api()

        real_home = tmp_path / "home"
        project = tmp_path / "repo"
        real_home.mkdir()
        project.mkdir()

        cfg = resolve_config(project, real_home=real_home)
        with pytest.raises(persona_config.PersonaConfigError, match="bogus-kind"):
            cfg.max_rounds_for_kind("bogus-kind")

        kit_cfg = json.loads(KIT_DEFAULTS_FILE.read_text(encoding="utf-8"))
        for bad_float in (math.nan, math.inf, -math.inf):
            mutated = json.loads(json.dumps(kit_cfg))
            mutated["review"]["quota_thresholds"]["5h_min_fraction"] = bad_float
            with pytest.raises(
                persona_config.PersonaConfigError, match="5h_min_fraction"
            ):
                persona_config.validate_merged_config(mutated)

        missing_model = json.loads(json.dumps(kit_cfg))
        del missing_model["review"]["providers"]["claude"]["model"]
        with pytest.raises(persona_config.PersonaConfigError, match="claude"):
            persona_config.validate_merged_config(missing_model)
