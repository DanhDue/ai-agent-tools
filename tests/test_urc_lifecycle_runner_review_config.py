"""Integration tests for LifecycleRunner layered external review caps and provider_priority.

Covers BDD scenarios:
- URC-HP-05: LifecycleRunner honors separate principal and cross-model round caps and layered provider_priority
- URC-ST-04: Explicit RunnerConfig overrides take precedence over global and project persona_config limits
- URC-AR-03: LifecycleRunner isolates Principal Review cap from Cross-Model Review cap during execution
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"
if str(RUNNER_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_SCRIPTS_DIR))

import lifecycle_runner  # noqa: E402
from lifecycle_runner import LifecycleRunner, RunnerConfig, StageName  # noqa: E402


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _setup_workspace(tmp_path: Path) -> tuple[Path, Path]:
    fake_home = tmp_path / "home"
    repo = tmp_path / "repo"
    fake_home.mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "epic" / "demo").mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "state").mkdir(parents=True, exist_ok=True)
    return repo, fake_home


def _assert_runner_resolves_separate_caps_and_priority(tmp_path: Path) -> None:
    repo, fake_home = _setup_workspace(tmp_path)
    _write_json(
        fake_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "max_principal_review_passes": 2,
            "max_cross_model_review_passes": 4,
            "review": {
                "provider_priority": ["codex", "claude", "kiro", "agy"],
            },
        },
    )

    cfg = RunnerConfig(real_home=fake_home)
    assert cfg.max_review_rounds is None
    assert cfg.max_principal_review_rounds is None
    assert cfg.max_cross_model_review_rounds is None
    assert cfg.provider_priority is None

    runner = LifecycleRunner(root=repo, epic_slug="demo", config=cfg)

    assert runner._resolve_external_review_bounds("principal") == 2
    assert runner._resolve_external_review_bounds("code") == 4
    assert runner._resolve_external_review_bounds("cross_model") == 4
    assert runner._resolve_external_review_bounds("epic") == 4
    assert runner._resolve_review_provider_priority() == [
        "codex",
        "claude",
        "kiro",
        "agy",
    ]


def test_urc_hp_05_runner_resolves_separate_caps_and_priority(tmp_path: Path) -> None:
    """[URC-HP-05] Top-level entry point for V1 RED and separate external review cap resolution."""
    _assert_runner_resolves_separate_caps_and_priority(tmp_path)


class Test_Integration:
    """[Tier C - Integration] Layered filesystem and subprocess integration tests for LifecycleRunner."""

    def test_urc_hp_05_runner_resolves_separate_caps_and_priority(
        self, tmp_path: Path
    ) -> None:
        """[URC-HP-05] LifecycleRunner resolves separate principal/cross-model caps and layered provider_priority."""
        _assert_runner_resolves_separate_caps_and_priority(tmp_path)

    def test_urc_hp_05_kit_defaults_and_step_subprocess_arguments(
        self, tmp_path: Path
    ) -> None:
        """[URC-HP-05] step_principal_review and step_cross_model_review pass resolved per-kind caps and provider priority."""
        repo, fake_home = _setup_workspace(tmp_path)

        # Clean workspace falls back to kit defaults (3, 3, ["claude", "codex", "kiro", "agy"])
        clean_runner = LifecycleRunner(
            root=repo, epic_slug="demo", config=RunnerConfig(real_home=fake_home)
        )
        assert clean_runner._resolve_external_review_bounds("principal") == 3
        assert clean_runner._resolve_external_review_bounds("code") == 3
        assert clean_runner._resolve_review_provider_priority() == [
            "claude",
            "codex",
            "kiro",
            "agy",
        ]

        # Configure distinct global caps and custom provider priority
        _write_json(
            fake_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 2,
                "max_cross_model_review_passes": 4,
                "review": {
                    "provider_priority": ["codex", "claude", "kiro", "agy"],
                },
            },
        )

        runner = LifecycleRunner(
            root=repo, epic_slug="demo", config=RunnerConfig(real_home=fake_home)
        )
        runner.quota_gate = lambda *_args, **_kwargs: True
        recorded_cmds: list[list[str]] = []

        def fake_subprocess_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
            recorded_cmds.append([str(part) for part in cmd])
            return MagicMock(
                returncode=0,
                stdout="## Auto-Triage Gate\n\n- **Action**: AUTO_PASS_CLEAN\n",
                stderr="",
            )

        with (
            patch("subprocess.run", side_effect=fake_subprocess_run),
            patch.object(runner, "_run_package_epic_revise", return_value=True),
            patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")),
        ):
            assert runner.step_principal_review() is True
            assert runner.step_cross_model_review() is True

        principal_run = next(
            cmd for cmd in recorded_cmds if "run" in cmd and "principal" in cmd
        )
        principal_triage = next(
            cmd for cmd in recorded_cmds if "triage" in cmd and "principal" in cmd
        )
        code_run = next(cmd for cmd in recorded_cmds if "run" in cmd and "code" in cmd)
        code_triage = next(
            cmd for cmd in recorded_cmds if "triage" in cmd and "code" in cmd
        )

        assert principal_run[principal_run.index("--max-rounds") + 1] == "2"
        assert (
            principal_run[principal_run.index("--provider-priority") + 1]
            == "codex,claude,kiro,agy"
        )
        assert principal_triage[principal_triage.index("--max-rounds") + 1] == "2"

        assert code_run[code_run.index("--max-rounds") + 1] == "4"
        assert (
            code_run[code_run.index("--provider-priority") + 1]
            == "codex,claude,kiro,agy"
        )
        assert code_triage[code_triage.index("--max-rounds") + 1] == "4"

        # Executive report reflects separate per-stage round caps instead of None
        report = runner.render_final_executive_report()
        assert "- **Principal Review Rounds**: 1 / 2" in report
        assert "- **Cross-Model Review Rounds**: 1 / 4" in report

        # run_gate4 works cleanly when RunnerConfig.max_review_rounds is None
        pass_payload = json.dumps(
            {
                "candidate_sha": "HEAD",
                "verdict": "PASS",
                "audit_exit": 0,
                "quality_check_report": "ok",
                "failures": [],
            }
        )
        with (
            patch.object(runner, "sync_gate_ledger", return_value=True),
            patch.object(
                runner.dispatcher,
                "dispatch",
                return_value=(0, f"```json\n{pass_payload}\n```\n", ""),
            ),
        ):
            gate4_ok, gate4_msg = runner.run_gate4()
            assert gate4_ok is True
            assert "PASS" in gate4_msg

    def test_urc_st_04_explicit_runner_config_overrides_persona_limits_and_priority(
        self, tmp_path: Path
    ) -> None:
        """[URC-ST-04] Explicit RunnerConfig overrides beat global/project persona_config and preserve max_review_rounds legacy compat."""
        repo, fake_home = _setup_workspace(tmp_path)
        _write_json(
            fake_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 3,
                "max_cross_model_review_passes": 3,
                "review": {
                    "provider_priority": ["claude", "codex"],
                },
            },
        )
        _write_json(
            repo / ".agents" / "config" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 2,
                "max_cross_model_review_passes": 4,
                "review": {
                    "provider_priority": ["codex", "claude"],
                },
            },
        )

        # Project overrides global when RunnerConfig leaves fields unset
        project_runner = LifecycleRunner(
            root=repo, epic_slug="demo", config=RunnerConfig(real_home=fake_home)
        )
        assert project_runner._resolve_external_review_bounds("principal") == 2
        assert project_runner._resolve_external_review_bounds("code") == 4
        assert project_runner._resolve_review_provider_priority() == ["codex", "claude"]

        # Per-stage overrides and explicit provider_priority take precedence over project & global
        explicit_runner = LifecycleRunner(
            root=repo,
            epic_slug="demo",
            config=RunnerConfig(
                real_home=fake_home,
                max_principal_review_rounds=1,
                max_cross_model_review_rounds=5,
                provider_priority=["kiro", "agy"],
            ),
        )
        assert explicit_runner._resolve_external_review_bounds("principal") == 1
        assert explicit_runner._resolve_external_review_bounds("code") == 5
        assert explicit_runner._resolve_review_provider_priority() == ["kiro", "agy"]

        # Legacy max_review_rounds overrides both principal and code bounds when per-stage fields are None
        legacy_runner = LifecycleRunner(
            root=repo,
            epic_slug="demo",
            config=RunnerConfig(real_home=fake_home, max_review_rounds=6),
        )
        assert legacy_runner._resolve_external_review_bounds("principal") == 6
        assert legacy_runner._resolve_external_review_bounds("code") == 6
        assert legacy_runner._resolve_review_provider_priority() == ["codex", "claude"]

        # Specific per-stage override takes precedence over generic max_review_rounds
        mixed_runner = LifecycleRunner(
            root=repo,
            epic_slug="demo",
            config=RunnerConfig(
                real_home=fake_home,
                max_review_rounds=6,
                max_principal_review_rounds=2,
            ),
        )
        assert mixed_runner._resolve_external_review_bounds("principal") == 2
        assert mixed_runner._resolve_external_review_bounds("code") == 6

    def test_urc_st_04_cli_max_rounds_and_config_wiring(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[URC-ST-04] CLI --max-rounds defaults to None and overrides --config/persona_config only when explicitly passed."""
        repo, fake_home = _setup_workspace(tmp_path)
        monkeypatch.setenv("HOME", str(fake_home))
        monkeypatch.setenv("REAL_HOME", str(fake_home))

        captured_configs: list[RunnerConfig] = []

        def fake_run(self: LifecycleRunner, **_kwargs: Any) -> int:
            captured_configs.append(self.config)
            return 0

        with patch.object(LifecycleRunner, "run", fake_run):
            # Default invocation without --max-rounds leaves max_review_rounds=None
            rc = lifecycle_runner.main(["--epic", "demo", "--root", str(repo)])
            assert rc == 0
            assert captured_configs[-1].max_review_rounds is None
            assert captured_configs[-1].max_principal_review_rounds is None
            assert captured_configs[-1].max_cross_model_review_rounds is None

            # Explicit --max-rounds CLI flag sets max_review_rounds override
            rc = lifecycle_runner.main(
                ["--epic", "demo", "--root", str(repo), "--max-rounds", "5"]
            )
            assert rc == 0
            assert captured_configs[-1].max_review_rounds == 5

            # --config JSON sets per-stage and legacy fields when CLI --max-rounds is omitted
            cfg_file = tmp_path / "runner_cfg.json"
            _write_json(
                cfg_file,
                {
                    "max_review_rounds": 4,
                    "max_principal_review_rounds": 2,
                    "max_cross_model_review_rounds": 6,
                    "provider_priority": ["kiro", "claude"],
                },
            )
            rc = lifecycle_runner.main(
                ["--epic", "demo", "--root", str(repo), "--config", str(cfg_file)]
            )
            assert rc == 0
            assert captured_configs[-1].max_review_rounds == 4
            assert captured_configs[-1].max_principal_review_rounds == 2
            assert captured_configs[-1].max_cross_model_review_rounds == 6
            assert captured_configs[-1].provider_priority == ["kiro", "claude"]

            # Explicit CLI --max-rounds takes precedence over --config review round settings
            rc = lifecycle_runner.main(
                [
                    "--epic",
                    "demo",
                    "--root",
                    str(repo),
                    "--config",
                    str(cfg_file),
                    "--max-rounds",
                    "7",
                ]
            )
            assert rc == 0
            assert captured_configs[-1].max_review_rounds == 7
            assert captured_configs[-1].max_principal_review_rounds is None
            assert captured_configs[-1].max_cross_model_review_rounds is None

    def test_urc_ar_03_runner_isolates_principal_and_cross_model_circuit_breaker_caps(
        self, tmp_path: Path
    ) -> None:
        """[URC-AR-03] LifecycleRunner isolates Principal Review cap from Cross-Model Review cap in circuit breakers and loops."""
        repo, fake_home = _setup_workspace(tmp_path)
        _write_json(
            fake_home / ".d3nexus" / "personas.json",
            {
                "schema_version": 1,
                "max_principal_review_passes": 1,
                "max_cross_model_review_passes": 3,
            },
        )

        runner = LifecycleRunner(
            root=repo, epic_slug="demo", config=RunnerConfig(real_home=fake_home)
        )
        critical_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Directive**: 1 Critical finding remaining.\n"
        )

        # Round 1 hits principal cap (1), but NOT code cap (3)
        assert (
            runner.evaluate_circuit_breakers(
                "principal", 1, triage_stdout=critical_triage
            )
            == "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        )
        assert (
            runner.evaluate_circuit_breakers("code", 1, triage_stdout=critical_triage)
            is None
        )
        assert (
            runner.evaluate_circuit_breakers("code", 2, triage_stdout=critical_triage)
            is None
        )
        assert (
            runner.evaluate_circuit_breakers("code", 3, triage_stdout=critical_triage)
            == "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        )

        # When triage_stdout is empty, fallback subprocess invokes triage with stage-specific --max-rounds
        review_script = (
            repo
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_external_review.py"
        )
        review_script.parent.mkdir(parents=True, exist_ok=True)
        review_script.write_text("# stub\n", encoding="utf-8")

        fallback_cmds: list[list[str]] = []

        def fake_triage_run(cmd: list[str], **_kwargs: Any) -> MagicMock:
            fallback_cmds.append([str(part) for part in cmd])
            return MagicMock(returncode=0, stdout=critical_triage, stderr="")

        with patch("subprocess.run", side_effect=fake_triage_run):
            assert (
                runner.evaluate_circuit_breakers("principal", 1)
                == "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
            )
            assert runner.evaluate_circuit_breakers("code", 1) is None

        assert fallback_cmds[0][fallback_cmds[0].index("--max-rounds") + 1] == "1"
        assert fallback_cmds[1][fallback_cmds[1].index("--max-rounds") + 1] == "3"

        # Execution loop isolation: principal halts after 1 round while cross-model can converge in round 2
        loop_runner = LifecycleRunner(
            root=repo,
            epic_slug="demo_principal",
            config=RunnerConfig(real_home=fake_home),
        )
        loop_runner.quota_gate = lambda *_args, **_kwargs: True
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout=critical_triage, stderr=""
            )
            assert loop_runner.step_principal_review() is False
            assert loop_runner.state.principal_round == 1
            assert loop_runner.state.active_stage == StageName.HALTED.value
            assert (
                loop_runner.state.halt_reason
                == "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
            )

        code_runner = LifecycleRunner(
            root=repo, epic_slug="demo_code", config=RunnerConfig(real_home=fake_home)
        )
        code_runner.quota_gate = lambda *_args, **_kwargs: True
        triage_r1 = MagicMock(
            returncode=0,
            stdout="## Auto-Triage Gate\n\n- **Action**: AUTO_FIX_ELIGIBLE\n- **Directive**: 1 Critical finding.\n",
            stderr="",
        )
        triage_r2 = MagicMock(
            returncode=0,
            stdout="## Auto-Triage Gate\n\n- **Action**: AUTO_PASS_CLEAN\n",
            stderr="",
        )
        with (
            patch(
                "subprocess.run",
                side_effect=[triage_r1, triage_r1, triage_r2, triage_r2],
            ),
            patch.object(
                code_runner,
                "_draft_fix_plan",
                return_value=("PLANNED", [], "Fix plan"),
            ),
            patch.object(code_runner, "_apply_code_fixes", return_value=True),
            patch.object(code_runner, "_record_review_decisions"),
            patch.object(
                code_runner, "run_intermediate_check", return_value=(True, "Scoped OK")
            ),
            patch.object(code_runner, "run_gate4", return_value=(True, "Gate 4 PASS")),
        ):
            assert code_runner.step_cross_model_review() is True
            assert code_runner.state.cross_model_round == 2
            assert code_runner.state.active_stage == StageName.AWAITING_FINISH.value
