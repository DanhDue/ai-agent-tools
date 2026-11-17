#!/usr/bin/env python3
"""Tests for Autonomous Lifecycle Runner state machine, persistence, and probing."""

import fcntl
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Add skills/dev-lifecycle/resources/scripts to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = (
    REPO_ROOT
    / "skills"
    / "dev-lifecycle"
    / "resources"
    / "scripts"
)
DEV_IMPL_SCRIPTS = (
    REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
)
for _dir in (str(SCRIPTS_DIR), str(DEV_IMPL_SCRIPTS)):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import lifecycle_runner
from lifecycle_runner import (
    HALT_CRITERIA,
    LifecycleRunner,
    ModelDispatcher,
    PipelineState,
    RunnerConfig,
    StageName,
)


@pytest.fixture(autouse=True)
def _isolate_host_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate HOME, REAL_HOME, profile env vars, and quota fetching from host stores."""
    fake_home = tmp_path / "_isolated_home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("REAL_HOME", str(fake_home))
    for var in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
        "AGY_ASSISTANT_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)

    rer_path = DEV_IMPL_SCRIPTS / "run_external_review.py"
    if rer_path.is_file():
        rer_mod = sys.modules.get("run_external_review")
        if rer_mod is None:
            spec = importlib.util.spec_from_file_location("run_external_review", rer_path)
            if spec is not None and spec.loader is not None:
                rer_mod = importlib.util.module_from_spec(spec)
                sys.modules["run_external_review"] = rer_mod
                spec.loader.exec_module(rer_mod)
        if rer_mod is not None and hasattr(rer_mod, "_default_quota_fetcher"):
            monkeypatch.setattr(rer_mod, "_default_quota_fetcher", lambda _cli: {})
    return fake_home


class TestLifecycleRunner_Integration(unittest.TestCase):
    """Test suite covering ALR-ST-03, ALR-AR-02, and Task 1 requirements."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.root = Path(self.temp_dir)
        self.epic_slug = "autonomous_lifecycle_runner"
        self.state_dir = self.root / ".devtool" / "state"
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_alr_st_03(self) -> None:
        """[ALR-ST-03] Probing verifies model capabilities before state initialization."""
        dispatcher = ModelDispatcher(worktree_dir=self.root)

        # 1. Invalid or deprecated model returns failure and halts without initializing state
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 1
            mock_proc.stderr = "Error: Model 'deprecated-model-v0' is not supported."
            mock_proc.stdout = ""
            mock_run.return_value = mock_proc

            ok, err = dispatcher.probe_model("agy", "deprecated-model-v0")
            self.assertFalse(ok)
            self.assertIn("not supported", err)

        # 2. Valid model returns success
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stderr = ""
            mock_proc.stdout = "Model probe successful"
            mock_run.return_value = mock_proc

            ok, msg = dispatcher.probe_model("agy", "gemini-3.8-flash")
            self.assertTrue(ok)
            self.assertEqual(msg, "OK")

        # 3. Model absent from agy models listing returns failure
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stderr = ""
            mock_proc.stdout = "gemini-4-argon-medium     Gemini 4 Argon (Medium)\nclaude-opus-5-5-high       Claude Opus 5.5 (High)\n"
            mock_run.return_value = mock_proc

            ok, err = dispatcher.probe_model("agy", "unknown-future-model")
            self.assertFalse(ok)
            self.assertIn("not supported by agy", err)

    def test_alr_ar_02(self) -> None:
        """[ALR-AR-02] Pipeline state atomic writes prevent file corruption and race conditions."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        runner.state.active_stage = StageName.PRINCIPAL_REVIEW.value
        runner.state.principal_round = 2
        runner.save_state()

        state_path = runner.state_file()
        self.assertTrue(state_path.is_file())

        # Verify atomic write produced valid JSON
        data = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(data["epic_slug"], self.epic_slug)
        self.assertEqual(data["active_stage"], StageName.PRINCIPAL_REVIEW.value)
        self.assertEqual(data["principal_round"], 2)

        # Verify no .tmp file left behind
        tmp_files = list(self.state_dir.glob("*.tmp"))
        self.assertEqual(tmp_files, [])

    def test_state_load_or_init_and_crash_resumption(self) -> None:
        """Loading state restores existing stage, completed tasks, and round counters."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        runner.state.active_stage = StageName.IMPLEMENTATION.value
        runner.state.task_order = ["task_1", "task_2", "task_3"]
        runner.state.completed_tasks = ["task_1"]
        runner.state.principal_round = 3
        runner.save_state()

        # Create a fresh runner instance pointing to the same workspace
        new_runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        loaded = new_runner.load_or_init_state()

        self.assertEqual(loaded.active_stage, StageName.IMPLEMENTATION.value)
        self.assertEqual(loaded.task_order, ["task_1", "task_2", "task_3"])
        self.assertEqual(loaded.completed_tasks, ["task_1"])
        self.assertEqual(loaded.principal_round, 3)

    def test_runner_config_assistant_model_precedence(self) -> None:
        """AI Architect & Reviewer model resolution follows CLI > --config > persona_config (ignoring legacy files)."""
        # 1. Kit fallback via persona_config (argon high -> gemini-4-argon-high)
        cfg = RunnerConfig()
        self.assertEqual(
            cfg.resolve_assistant_model(self.root), "gemini-4-argon-high"
        )

        # 2. Legacy review_config.json and AGY_ASSISTANT_MODEL are ignored
        review_config_file = self.root / ".devtool" / "review_config.json"
        review_config_file.parent.mkdir(parents=True, exist_ok=True)
        review_config_file.write_text(
            json.dumps({"providers": {"assistant": {"model": "Opus 5.5"}}}),
            encoding="utf-8",
        )
        with patch.dict(os.environ, {"AGY_ASSISTANT_MODEL": "legacy-env-model"}):
            self.assertEqual(
                cfg.resolve_assistant_model(self.root), "gemini-4-argon-high"
            )

        # 3. Project persona_config overrides kit default
        personas_file = self.root / ".agents" / "config" / "personas.json"
        personas_file.parent.mkdir(parents=True, exist_ok=True)
        personas_file.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "overrides": {
                        "ai_architect_reviewer": {"model": "claude-opus", "effort": "high"}
                    },
                }
            ),
            encoding="utf-8",
        )
        self.assertEqual(cfg.resolve_assistant_model(self.root), "opus")

        # 4. --config architect_model beats persona_config; CLI beats --config
        cfg_file = RunnerConfig(config_architect_model="codex-gpt")
        self.assertEqual(cfg_file.resolve_assistant_model(self.root), "gpt-6.1-sol")
        cfg_cli = RunnerConfig(
            architect_model="claude-sonnet", config_architect_model="codex-gpt"
        )
        self.assertEqual(cfg_cli.resolve_assistant_model(self.root), "sonnet")
        cfg_alias = RunnerConfig(assistant_model="gpt-6.1-sol")
        self.assertEqual(cfg_alias.resolve_assistant_model(self.root), "gpt-6.1-sol")

    def test_alr_hp_02(self) -> None:
        """[ALR-HP-02] Headless dispatch of AI Programmer with Gemini 3.8 Flash High."""
        dispatcher = ModelDispatcher(worktree_dir=self.root)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 9999
            mock_proc.communicate.return_value = ("Task implementation completed", "")
            mock_proc.returncode = 0
            mock_popen.return_value = mock_proc

            exit_code, stdout, _ = dispatcher.dispatch(
                cli="agy",
                args=[
                    "--model",
                    "gemini-3.8-flash",
                    "--effort",
                    "high",
                    "--mode",
                    "auto",
                ],
                prompt="Implement task 1",
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("Task implementation completed", stdout)
            mock_popen.assert_called_once()
            called_args, called_kwargs = mock_popen.call_args
            self.assertEqual(
                called_args[0][:6],
                ["agy", "--model", "gemini-3.8-flash", "--effort", "high", "--mode"],
            )
            self.assertTrue(called_kwargs.get("start_new_session"))

    def test_alr_ec_04(self) -> None:
        """[ALR-EC-04] Gate 3 execution order auto-confirmed via compute_execution_order."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_output = (
            "Execution plan for epic 'autonomous_lifecycle_runner' (2 tasks):\n"
            "Flattened sequential order:\n"
            "  1. task_1_setup - Setup\n"
            "  2. task_2_impl - Impl\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_output
            mock_run.return_value = mock_proc

            with patch.object(
                runner, "sync_gate_ledger", return_value=True
            ) as mock_sync:
                order = runner.resolve_gate3_order()
                self.assertEqual(order, ["task_1_setup", "task_2_impl"])
                self.assertEqual(
                    runner.state.task_order, ["task_1_setup", "task_2_impl"]
                )
                mock_sync.assert_called_once()

    def test_alr_ar_01(self) -> None:
        """[ALR-AR-01] Subprocess group process isolation and clean SIGTERM termination on timeout."""
        import signal

        dispatcher = ModelDispatcher(worktree_dir=self.root, timeout_seconds=1)
        with patch("subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_proc.pid = 12345
            # Simulate subprocess.TimeoutExpired
            import subprocess

            mock_proc.communicate.side_effect = subprocess.TimeoutExpired(
                cmd=["agy"], timeout=1
            )
            mock_proc.poll.side_effect = [
                None,
                0,
            ]  # First poll None (alive), second poll 0 (terminated)
            mock_popen.return_value = mock_proc

            with patch("os.killpg") as mock_killpg:
                exit_code, _, stderr = dispatcher.dispatch(
                    cli="agy",
                    args=["--model", "gemini-3.8-flash"],
                    prompt="Long running task",
                )
                self.assertEqual(exit_code, 124)  # Standard timeout exit code
                self.assertIn("timeout", stderr.lower())
                mock_killpg.assert_any_call(12345, signal.SIGTERM)

    def test_alr_st_01(self) -> None:
        """[ALR-ST-01] State persistence and resumption from crash in intermediate stage."""
        # 1. Simulate state after task 1 is completed
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        runner.state.active_stage = StageName.IMPLEMENTATION.value
        runner.state.task_order = ["task_1_setup", "task_2_impl"]
        runner.state.completed_tasks = ["task_1_setup"]
        runner.save_state()

        # 2. Resumed runner should pick up and execute only task_2_impl
        resumed_runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        resumed_runner.load_or_init_state()

        dispatched_tasks: list[str] = []

        def fake_dispatch_task(task_slug: str) -> bool:
            dispatched_tasks.append(task_slug)
            return True

        with patch.object(
            resumed_runner, "_execute_single_task", side_effect=fake_dispatch_task
        ):
            ok = resumed_runner.step_implementation()
            self.assertTrue(ok)
            # task_1_setup is skipped, only task_2_impl is dispatched
            self.assertEqual(dispatched_tasks, ["task_2_impl"])
            self.assertIn("task_2_impl", resumed_runner.state.completed_tasks)

    def test_alr_ec_01(self) -> None:
        """[ALR-EC-01] Zero findings in Principal Review bypasses Human confirmation."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_triage
            mock_run.return_value = mock_proc

            with patch.object(runner, "prompt_human_principal_fixes") as mock_prompt:
                ok = runner.step_principal_review()
                self.assertTrue(ok)
                self.assertEqual(
                    runner.state.active_stage, StageName.IMPLEMENTATION.value
                )
                mock_prompt.assert_not_called()

    def test_alr_ec_02(self) -> None:
        """[ALR-EC-02] Minor-only findings in Principal Review swept in single pass without Human halt."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_FINAL_MINOR_SWEEP\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 0 Critical and 0 Important findings (2 Minor).\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_triage
            mock_run.return_value = mock_proc

            with (
                patch.object(runner, "prompt_human_principal_fixes") as mock_prompt,
                patch.object(runner, "_apply_minor_fixes") as mock_minor,
            ):
                ok = runner.step_principal_review()
                self.assertTrue(ok)
                self.assertEqual(
                    runner.state.active_stage, StageName.IMPLEMENTATION.value
                )
                mock_prompt.assert_not_called()
                mock_minor.assert_called_once()

    def test_alr_fr_01(self) -> None:
        """[ALR-FR-01] Circuit Breaker halts immediately on Shared Contract conflict."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: Shared-contract conflict detected in finding(s) #1\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_triage
            mock_run.return_value = mock_proc

            ok = runner.step_principal_review()
            self.assertFalse(ok)
            self.assertEqual(runner.state.active_stage, StageName.HALTED.value)
            self.assertEqual(
                runner.state.halt_reason,
                "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)",
            )

    def test_alr_hp_03(self) -> None:
        """[ALR-HP-03] AI Assistant auto-applies aligned Principal Review fixes and prompts Human confirmation only on critical or domain conflicts."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: Domain Conflict: Critical business requirement conflict detected.\n"
        )
        mock_triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )

        with patch("subprocess.run") as mock_run:
            mock_proc_r1 = MagicMock()
            mock_proc_r1.returncode = 0
            mock_proc_r1.stdout = mock_triage_r1

            mock_proc_r2 = MagicMock()
            mock_proc_r2.returncode = 0
            mock_proc_r2.stdout = mock_triage_r2

            # Return r1 on first calls, r2 on subsequent calls
            mock_run.side_effect = [
                mock_proc_r1,
                mock_proc_r1,
                mock_proc_r2,
                mock_proc_r2,
            ]

            prompt_called = False

            def fake_prompt(triage_summary: str) -> bool:
                nonlocal prompt_called
                prompt_called = True
                self.assertEqual(
                    runner.state.active_stage,
                    StageName.AWAITING_PRINCIPAL_CONFIRMATION.value,
                )
                return True

            with (
                patch.object(
                    runner, "prompt_human_principal_fixes", side_effect=fake_prompt
                ),
                patch.object(runner, "_apply_aligned_fixes") as mock_aligned,
                patch.object(
                    runner, "_run_package_epic_revise", return_value=True
                ) as mock_pkg,
            ):
                ok = runner.step_principal_review()
                self.assertTrue(ok)
                self.assertTrue(prompt_called)
                self.assertEqual(
                    runner.state.active_stage, StageName.IMPLEMENTATION.value
                )
                mock_aligned.assert_called_once()
                mock_pkg.assert_called_once()
                proposal = (
                    self.root
                    / ".devtool"
                    / "epic"
                    / self.epic_slug
                    / "principal_fix_proposal_round1.md"
                )
                self.assertTrue(proposal.is_file())

    def test_alr_fr_02(self) -> None:
        """[ALR-FR-02] Circuit Breaker halts immediately on repeated fix loop."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: CIRCUIT_BREAKER_HALT (FIX_LOOP)\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: Fix Loop detected across consecutive rounds on src/app.py\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_triage
            mock_run.return_value = mock_proc

            ok = runner.step_cross_model_review()
            self.assertFalse(ok)
            self.assertEqual(runner.state.active_stage, StageName.HALTED.value)
            self.assertEqual(
                runner.state.halt_reason, "CIRCUIT_BREAKER_HALT (FIX_LOOP)"
            )

    def test_alr_fr_04(self) -> None:
        """[ALR-FR-04] Role 2.1 fix-planner escalates on CRITICAL_CONFLICT / halt criteria and fails closed."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Critical finding.\n"
        )
        with patch("subprocess.run") as mock_run:
            mock_proc = MagicMock()
            mock_proc.returncode = 0
            mock_proc.stdout = mock_triage
            mock_run.return_value = mock_proc

            with patch.object(
                runner,
                "_draft_fix_plan",
                return_value=("ESCALATE", ["CRITICAL_CONFLICT"], ""),
            ):
                ok = runner.step_cross_model_review()
                self.assertFalse(ok)
                self.assertEqual(runner.state.active_stage, StageName.HALTED.value)
                self.assertEqual(runner.state.halt_reason, "FIX_PLAN_ESCALATE")
                pd_file = self.state_dir / "pending_decision.json"
                pd_data = json.loads(pd_file.read_text(encoding="utf-8"))
                self.assertEqual(pd_data["decisions"][self.epic_slug]["kind"], "blocker")
                self.assertIn(
                    "CRITICAL_CONFLICT", pd_data["decisions"][self.epic_slug]["reason"]
                )

        # Direct fix-planner fail-closed checks
        runner_direct = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        runner_direct.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
        with patch.object(
            runner_direct.dispatcher,
            "dispatch",
            return_value=(124, "", "Process timed out"),
        ):
            status, criteria, _ = runner_direct._draft_fix_plan(1, mock_triage)
            self.assertEqual(status, "ESCALATE")
            self.assertEqual(criteria, ["UNPARSEABLE"])

        with patch.object(
            runner_direct.dispatcher,
            "dispatch",
            return_value=(0, "Unrecognized rambling reply", ""),
        ):
            status, criteria, _ = runner_direct._draft_fix_plan(1, mock_triage)
            self.assertEqual(status, "ESCALATE")
            self.assertEqual(criteria, ["UNPARSEABLE"])
        self.assertIn("CRITICAL_CONFLICT", HALT_CRITERIA)

    def test_alr_ec_03(self) -> None:
        """[ALR-EC-03] Role 2.1 fix-planner plans fix_plan_round1.md and review-fixer applies it."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Important finding.\n"
        )
        mock_triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )

        with patch("subprocess.run") as mock_run:
            mock_proc_r1 = MagicMock()
            mock_proc_r1.returncode = 0
            mock_proc_r1.stdout = mock_triage_r1

            mock_proc_r2 = MagicMock()
            mock_proc_r2.returncode = 0
            mock_proc_r2.stdout = mock_triage_r2

            mock_run.side_effect = [
                mock_proc_r1,
                mock_proc_r1,
                mock_proc_r2,
                mock_proc_r2,
            ]

            with (
                patch.object(
                    runner,
                    "_draft_fix_plan",
                    return_value=(
                        "PLANNED",
                        [],
                        "Add edge-case assertion for null payload",
                    ),
                ),
                patch.object(runner, "_apply_code_fixes") as mock_apply,
                patch.object(runner, "_record_review_decisions"),
                patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")),
            ):
                ok = runner.step_cross_model_review()
                self.assertTrue(ok)
                self.assertEqual(runner.state.last_verdict, "PLANNED")
                mock_apply.assert_called_once()
                self.assertIn(
                    "Add edge-case assertion",
                    mock_apply.call_args[1].get("plan_text", ""),
                )
                self.assertEqual(mock_apply.call_args[1].get("mode"), "apply-plan")

    def test_alr_hp_04(self) -> None:
        """[ALR-HP-04] Role 2.1 fix-planner outputs PLANNED and review-fixer applies without Human stop."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Critical finding.\n"
        )
        mock_triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )

        with patch("subprocess.run") as mock_run:
            mock_proc_r1 = MagicMock()
            mock_proc_r1.returncode = 0
            mock_proc_r1.stdout = mock_triage_r1

            mock_proc_r2 = MagicMock()
            mock_proc_r2.returncode = 0
            mock_proc_r2.stdout = mock_triage_r2

            mock_run.side_effect = [
                mock_proc_r1,
                mock_proc_r1,
                mock_proc_r2,
                mock_proc_r2,
            ]

            with (
                patch.object(
                    runner,
                    "_draft_fix_plan",
                    return_value=("PLANNED", [], "Fix plan adheres to HLD"),
                ),
                patch.object(runner, "_apply_code_fixes") as mock_apply,
                patch.object(runner, "_record_review_decisions"),
                patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")),
            ):
                ok = runner.step_cross_model_review()
                self.assertTrue(ok)
                self.assertEqual(
                    runner.state.active_stage, StageName.AWAITING_FINISH.value
                )
                self.assertEqual(runner.state.last_verdict, "PLANNED")
                mock_apply.assert_called_once()

    def test_alr_fr_03(self) -> None:
        """[ALR-FR-03] Circuit Breaker halts on max rounds exhaustion with Critical remaining."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
        runner.state.cross_model_round = 3

        cb = runner.evaluate_circuit_breakers(
            "code",
            3,
            triage_stdout="- **Action**: CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)\n",
        )
        self.assertEqual(cb, "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)")

    def test_alr_st_02(self) -> None:
        """[ALR-ST-02] Gate Ledger synchronization on autonomous state transitions."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)
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
            patch.object(runner, "sync_gate_ledger", return_value=True) as mock_sync,
            patch.object(
                runner.dispatcher,
                "dispatch",
                return_value=(0, f"```json\n{pass_payload}\n```\n", ""),
            ),
        ):
            ok, msg = runner.run_gate4()
            self.assertTrue(ok)
            self.assertIn("PASS", msg)
            mock_sync.assert_called_with(4, unittest.mock.ANY)

        # Gate 4 fails deterministically when verifier reports audit failure
        fail_payload = json.dumps(
            {
                "candidate_sha": "HEAD",
                "verdict": "FAIL",
                "audit_exit": 2,
                "quality_check_report": "fail",
                "failures": ["Audit failure: missing task evidence"],
            }
        )
        with (
            patch.object(runner, "sync_gate_ledger", return_value=True) as mock_sync,
            patch.object(
                runner.dispatcher,
                "dispatch",
                return_value=(0, f"```json\n{fail_payload}\n```\n", ""),
            ),
            patch.object(
                runner, "_apply_code_fixes", return_value=False
            ),
        ):
            ok, err = runner.run_gate4()
            self.assertFalse(ok)
            self.assertIn("failed", err.lower())
            self.assertIn("missing task evidence", err)
            mock_sync.assert_not_called()

    def test_alr_hp_01(self) -> None:
        """[ALR-HP-01] Complete autonomous pipeline executes from handoff to final executive report."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        def fake_step_principal() -> bool:
            runner.state.active_stage = StageName.IMPLEMENTATION.value
            return True

        def fake_step_implementation() -> bool:
            runner.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
            return True

        def fake_step_cross_model() -> bool:
            runner.state.active_stage = StageName.AWAITING_FINISH.value
            return True

        with (
            patch.object(runner.dispatcher, "probe_model", return_value=(True, "OK")),
            patch.object(
                runner, "step_principal_review", side_effect=fake_step_principal
            ),
            patch.object(
                runner, "step_implementation", side_effect=fake_step_implementation
            ),
            patch.object(
                runner, "step_cross_model_review", side_effect=fake_step_cross_model
            ),
            patch.object(
                runner,
                "render_final_executive_report",
                return_value="# Executive Review Report",
            ),
        ):
            exit_code = runner.run()
            self.assertEqual(exit_code, 0)
            self.assertEqual(runner.state.active_stage, StageName.AWAITING_FINISH.value)

    def test_scoped_tests_protocol_intermediate_rounds(self) -> None:
        """[ALR-ST-03] Intermediate fix rounds run scoped tests only; full Gate 4 runs at final convergence."""
        runner = LifecycleRunner(root=self.root, epic_slug=self.epic_slug)

        mock_triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Important finding.\n"
        )
        mock_triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )

        with patch("subprocess.run") as mock_run:
            mock_proc_r1 = MagicMock()
            mock_proc_r1.returncode = 0
            mock_proc_r1.stdout = mock_triage_r1

            mock_proc_r2 = MagicMock()
            mock_proc_r2.returncode = 0
            mock_proc_r2.stdout = mock_triage_r2

            mock_run.side_effect = [
                mock_proc_r1,
                mock_proc_r1,
                mock_proc_r2,
                mock_proc_r2,
            ]

            with (
                patch.object(
                    runner,
                    "_draft_fix_plan",
                    return_value=("PLANNED", [], "Fix plan adheres to HLD"),
                ),
                patch.object(runner, "_apply_code_fixes"),
                patch.object(runner, "_record_review_decisions"),
                patch.object(
                    runner, "run_intermediate_check", return_value=(True, "Scoped OK")
                ) as mock_scoped,
                patch.object(
                    runner, "run_gate4", return_value=(True, "Gate 4 PASS")
                ) as mock_gate4,
            ):
                ok = runner.step_cross_model_review()
                self.assertTrue(ok)
                # Intermediate round 1 must call run_intermediate_check exactly once
                mock_scoped.assert_called_once()
                # Full Gate 4 must NOT be called in round 1, but called once on final convergence (round 2)
                mock_gate4.assert_called_once()
                self.assertEqual(
                    runner.state.active_stage, StageName.AWAITING_FINISH.value
                )

    def test_tto_hp_04_integration(self) -> None:
        """[TTO-HP-04] Integration check for Runner programmer config precedence."""
        test_tto_hp_04_runner_config_precedence()

    def test_tto_hp_07_integration(self) -> None:
        """[TTO-HP-07] Integration check for cross-model fast-track fixes and real executive report."""
        test_tto_hp_07_streamlined_code_fix_and_real_executive_report()

    def test_tto_ec_04_integration(self) -> None:
        """[TTO-EC-04] Integration check for effort alias normalization to xhigh."""
        test_tto_ec_04_effort_normalization_and_cli_args()

    def test_tto_st_04_integration(self) -> None:
        """[TTO-ST-04] Integration check for escalation on contract or ambiguity findings."""
        test_tto_st_04_cross_model_escalation_on_contract_or_ambiguity()

    def test_tto_ar_01_integration(self) -> None:
        """[TTO-AR-01] Integration check for parallel pool isolation and path-only prompts."""
        test_tto_ar_01_parallel_pool_dispatch_and_path_only_prompts()

    def test_tto_fr_03_integration(self) -> None:
        """[TTO-FR-03] Integration check for Gate 4 quiet verification and _tail_lines capping."""
        test_tto_fr_03_tail_lines_caps_gate4_and_intermediate_errors()


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Execute a git command inside cwd and assert success."""
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed in {cwd}: {res.stderr.strip() or res.stdout.strip()}"
        )
    return res


def _init_git_repo(repo_dir: Path) -> None:
    """Initialize a temporary git repository on branch main with user identity."""
    _git(repo_dir, "init", "-q", "-b", "main")
    _git(repo_dir, "config", "user.name", "Test Architect")
    _git(repo_dir, "config", "user.email", "architect@example.com")


def _load_pool_module() -> Any:
    """Dynamically load manage_worker_pool.py for direct integration checks."""
    pool_path = (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "dev-implementation"
        / "resources"
        / "scripts"
        / "manage_worker_pool.py"
    )
    spec = importlib.util.spec_from_file_location("manage_worker_pool", pool_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tto_hp_04_runner_config_precedence() -> None:
    """[TTO-HP-04] Verify programmer model/effort precedence CLI -> --config -> persona_config (project > global > kit)."""
    with tempfile.TemporaryDirectory() as tmp:
        fake_home = Path(tmp) / "real_home"
        fake_home.mkdir(parents=True, exist_ok=True)
        root = Path(tmp) / "repo"
        (root / ".devtool").mkdir(parents=True, exist_ok=True)
        review_cfg_path = root / ".devtool" / "review_config.json"

        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"AGY_PROGRAMMER_MODEL", "AGY_PROGRAMMER_EFFORT", "AGY_PROFILE", "ANTIGRAVITY_PROFILE"}
        }
        clean_env["HOME"] = str(fake_home)
        clean_env["REAL_HOME"] = str(fake_home)

        # 1. Pure kit fallback via persona_config
        with patch.dict(os.environ, clean_env, clear=True):
            cfg = RunnerConfig()
            assert cfg.resolve_programmer_model(root) == "gemini-4-hydrogen-xhigh"
            assert cfg.resolve_programmer_effort(root) == "xhigh"

        # 2. Legacy AGY_PROGRAMMER_* env vars and .devtool/review_config.json are ignored
        legacy_cfg_text = json.dumps(
            {
                "providers": {
                    "programmer": {
                        "cli": "agy",
                        "model": "custom-prog-v2",
                        "effort": "low",
                    }
                }
            },
            indent=2,
        )
        review_cfg_path.write_text(legacy_cfg_text, encoding="utf-8")
        legacy_env = dict(clean_env)
        legacy_env["AGY_PROGRAMMER_MODEL"] = "env-legacy-model"
        legacy_env["AGY_PROGRAMMER_EFFORT"] = "low"
        with patch.dict(os.environ, legacy_env, clear=True):
            cfg = RunnerConfig()
            assert cfg.resolve_programmer_model(root) == "gemini-4-hydrogen-xhigh"
            assert cfg.resolve_programmer_effort(root) == "xhigh"
            assert review_cfg_path.read_text(encoding="utf-8") == legacy_cfg_text

        # 3. Global persona_config overrides kit; project persona_config overrides global
        global_personas = fake_home / ".d3nexus" / "personas.json"
        global_personas.parent.mkdir(parents=True, exist_ok=True)
        global_personas.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "overrides": {
                        "programmer": {"model": "hydrogen", "effort": "high"}
                    },
                }
            ),
            encoding="utf-8",
        )
        with patch.dict(os.environ, legacy_env, clear=True):
            cfg = RunnerConfig()
            assert cfg.resolve_programmer_model(root) == "gemini-4-hydrogen-high"
            assert cfg.resolve_programmer_effort(root) == "high"

        project_personas = root / ".agents" / "config" / "personas.json"
        project_personas.parent.mkdir(parents=True, exist_ok=True)
        project_personas.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "overrides": {
                        "programmer": {"model": "codex-gpt", "effort": "medium"}
                    },
                }
            ),
            encoding="utf-8",
        )
        with patch.dict(os.environ, legacy_env, clear=True):
            cfg = RunnerConfig()
            assert cfg.resolve_programmer_model(root) == "gpt-6.1-sol"
            assert cfg.resolve_programmer_effort(root) == "medium"

            # 4. --config JSON beats persona_config via main()
            runner_cfg_file = root / "runner_cfg.json"
            runner_cfg_file.write_text(
                json.dumps(
                    {
                        "programmer_model": "runner-cfg-model",
                        "programmer_effort": "extra-high",
                    }
                ),
                encoding="utf-8",
            )
            captured_configs: list[RunnerConfig] = []

            def fake_run(self_runner: LifecycleRunner, **kwargs: Any) -> int:
                captured_configs.append(self_runner.config)
                return 0

            with (
                patch.object(
                    LifecycleRunner, "run", autospec=True, side_effect=fake_run
                ),
                patch.object(
                    sys,
                    "argv",
                    [
                        "lifecycle_runner.py",
                        "--root",
                        str(root),
                        "--epic",
                        "demo",
                        "--config",
                        str(runner_cfg_file),
                        "--dry-run",
                    ],
                ),
            ):
                rc = lifecycle_runner.main()
                assert rc == 0

            assert len(captured_configs) == 1
            assert captured_configs[0].programmer_model is None
            assert captured_configs[0].programmer_effort is None
            assert (
                captured_configs[0].resolve_programmer_model(root) == "runner-cfg-model"
            )
            assert captured_configs[0].resolve_programmer_effort(root) == "xhigh"

            # 5. CLI beats --config, persona_config, review_config.json, and env
            captured_configs.clear()
            with (
                patch.object(
                    LifecycleRunner, "run", autospec=True, side_effect=fake_run
                ),
                patch.object(
                    sys,
                    "argv",
                    [
                        "lifecycle_runner.py",
                        "--root",
                        str(root),
                        "--epic",
                        "demo",
                        "--config",
                        str(runner_cfg_file),
                        "--programmer-model",
                        "cli-override-model",
                        "--programmer-effort",
                        "low",
                        "--dry-run",
                    ],
                ),
            ):
                rc = lifecycle_runner.main()
                assert rc == 0

            assert len(captured_configs) == 1
            assert (
                captured_configs[0].resolve_programmer_model(root)
                == "cli-override-model"
            )
            assert captured_configs[0].resolve_programmer_effort(root) == "low"

            # 6. Default run() probes the persona_config-resolved binding
            runner = LifecycleRunner(root=root, epic_slug="demo", config=RunnerConfig())
            runner.state.active_stage = StageName.INITIALIZED.value
            runner.save_state()
            with patch.object(
                runner.dispatcher, "probe_model", return_value=(False, "stop")
            ) as mock_probe:
                rc = runner.run(dry_run=False)
                assert rc == 1
                mock_probe.assert_called_once_with("codex", "gpt-6.1-sol")


def test_tto_ec_04_effort_normalization_and_cli_args() -> None:
    """[TTO-EC-04] Normalize effort aliases ('extra', 'extra-high', 'xhigh') to 'xhigh' across CLI dispatch."""
    assert lifecycle_runner.normalize_agy_effort("extra") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort("EXTRA") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort("extra-high") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort("extra_high") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort(" XHIGH ") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort("") == "xhigh"
    assert lifecycle_runner.normalize_agy_effort("High") == "high"
    assert lifecycle_runner.normalize_agy_effort(" medium ") == "medium"

    cmd = lifecycle_runner.build_agy_command(
        "gemini-4-hydrogen-xhigh", "extra", mode="auto"
    )
    assert cmd == [
        "agy",
        "--model",
        "gemini-4-hydrogen-xhigh",
        "--effort",
        "xhigh",
        "--mode",
        "auto",
    ]
    assert "extra" not in cmd

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        runner = LifecycleRunner(
            root=root,
            epic_slug="demo",
            config=RunnerConfig(programmer_effort="extra-high"),
        )
        recorded: list[tuple[str, list[str]]] = []

        def fake_dispatch(
            cli: str, args: list[str], prompt: str
        ) -> tuple[int, str, str]:
            recorded.append((cli, list(args)))
            if "fix-planner" in prompt:
                return 0, '```json\n{"round": 1, "status": "PLANNED", "halt_criteria": [], "plan_markdown": "# Plan\\n"}\n```\n', ""
            if "task-implementer" in prompt:
                return 0, '```json\n{"task_id": "task_01_demo", "slot": 1, "status": "DONE", "head_sha": "abc", "verify": "PASS", "changed_files": ["src/a.py"], "non_test_modules_changed": 1, "review_tier": "standard", "labels": [], "finalized": false}\n```\n', ""
            return 0, "ok", ""

        with (
            patch.object(runner.dispatcher, "dispatch", side_effect=fake_dispatch),
            patch.object(runner, "_run_scoped_tests", return_value=(True, "ok")),
        ):
            assert runner._execute_single_task("task_01_demo")
            status, _, _ = runner._draft_fix_plan(1, "find")
            assert status == "PLANNED"
            assert runner._apply_code_fixes(1, plan_text="plan")

        assert len(recorded) == 3
        for idx_call in (0, 2):
            _, args = recorded[idx_call]
            assert "--effort" in args
            idx = args.index("--effort")
            assert args[idx + 1] == "xhigh"
            assert "--model" in args
            m_idx = args.index("--model")
            assert args[m_idx + 1] == "gemini-4-hydrogen-xhigh"
        # _draft_fix_plan uses ai_architect_reviewer (argon high) in read-only mode
        _, plan_args = recorded[1]
        assert "--sandbox" in plan_args
        assert "--model" in plan_args
        assert plan_args[plan_args.index("--model") + 1] == "gemini-4-argon-high"
        assert plan_args[plan_args.index("--effort") + 1] == "high"


def test_tto_fr_03_tail_lines_caps_gate4_and_intermediate_errors() -> None:
    """[TTO-FR-03] Cap verbose test/gate failures to trailing 25 non-empty lines and pass --quiet to verify.sh."""
    lines = [f"line_{i:03d}" if i % 3 else "" for i in range(1, 76)]
    raw = "\n".join(lines)

    tailed_fn = lifecycle_runner._tail_lines(raw, 25)
    tailed_method = LifecycleRunner._tail_lines(raw, 25)
    assert tailed_fn == tailed_method
    tailed_lines = tailed_fn.splitlines()
    assert len(tailed_lines) <= 25
    assert "line_001" not in tailed_fn
    assert tailed_lines[-1] == "line_074"
    assert lifecycle_runner._tail_lines("   \n\n  ", 25) == ""

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".devtool" / "epic" / "demo").mkdir(parents=True, exist_ok=True)
        (root / ".devtool" / "features").mkdir(parents=True, exist_ok=True)
        (root / ".devtool" / "epic" / "demo" / "demo.md").write_text(
            "# Demo HLD\nIntegration results: echo ok -> PASS\n",
            encoding="utf-8",
        )
        (root / ".devtool" / "epic" / "demo" / "bdd_scenarios.md").write_text(
            "# BDD\n", encoding="utf-8"
        )
        (root / "skills" / "dev-implementation" / "resources" / "scripts").mkdir(
            parents=True, exist_ok=True
        )
        (
            root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_external_review.py"
        ).write_text("# stub\n", encoding="utf-8")

        runner = LifecycleRunner(root=root, epic_slug="demo")
        verbose_err = (
            "\n".join(f"line_{i:03d}" for i in range(1, 60))
            + "\nFAIL: final_summary_error"
        )

        # gate4-verifier brief must carry verify.sh --quiet and cap verifier failures to <= 25 trailing lines
        captured_prompts: list[str] = []

        def fail_verifier(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
            captured_prompts.append(prompt)
            return 1, "", verbose_err

        with (
            patch.object(runner.dispatcher, "dispatch", side_effect=fail_verifier),
            patch.object(runner, "_apply_code_fixes", return_value=False),
        ):
            ok, msg = runner.run_gate4()
            assert not ok
            assert "final_summary_error" in msg
            assert "line_001" not in msg
            assert len(msg.splitlines()) <= 26
            assert "--quiet" in captured_prompts[0]
            assert "echo ok" in captured_prompts[0]

        # Run intermediate check failure cap
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout=verbose_err, stderr=""
            )
            ok, msg = runner.run_intermediate_check()
            assert not ok
            assert "final_summary_error" in msg
            assert "line_001" not in msg
            assert len(msg.splitlines()) <= 26


def test_tto_hp_07_streamlined_code_fix_and_real_executive_report() -> None:
    """[TTO-HP-07] Fast-track verified non-Critical bug in Cross-Model Review, refuse Critical, and render real report."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        epic_dir = root / ".devtool" / "epic" / "demo_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / "app.py").write_text(
            "\n".join(f"line_{i} = {i}" for i in range(1, 20)) + "\n",
            encoding="utf-8",
        )

        (epic_dir / "principal_review.md").write_text(
            "# Principal Review\n\n"
            "## Round 1\n"
            "- Candidate SHA: `111aaaa`\n\n"
            "| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| PR-01 | Critical | `hld.md:12` | Missing lease fencing spec | fixed in 111aaaa |\n\n"
            "```text\n"
            "Raw output:\n"
            "| DECOY-99 | Critical | `fake.py:1` | FAKE_DECOY_FINDING_IN_RAW_BLOCK | Open |\n"
            "```\n",
            encoding="utf-8",
        )
        (epic_dir / "review_results.md").write_text(
            "# Cross-Model Review\n\n"
            "## Round 1\n"
            "- Candidate SHA: `222bbbb`\n\n"
            "| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| CR-01 | Important | `src/app.py:4` | Null token causes crash in parse_token | Open |\n"
            "| CR-02 | Important | `src/app.py:10` | Missing timeout bound on retry loop | fixed in 333cccc |\n\n"
            "```text\n"
            "Raw output:\n"
            "| DECOY-88 | Critical | `raw.py:2` | FAKE_DECOY_FINDING_IN_RAW_BLOCK | Open |\n"
            "```\n",
            encoding="utf-8",
        )

        runner = LifecycleRunner(root=root, epic_slug="demo_epic")
        assert not runner._can_fast_track_code_findings(
            [{"severity": "Critical", "target": "src/app.py:4", "problem": "Crash", "status": "Open"}],
            "## Auto-Triage Gate\n- **Action**: AUTO_FIX_ELIGIBLE\n",
        )
        triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Important finding.\n"
        )
        triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings. Stage review passed cleanly.\n"
        )

        with patch("subprocess.run") as mock_run:
            p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
            p2 = MagicMock(returncode=0, stdout=triage_r2, stderr="")
            mock_run.side_effect = [p1, p1, p2, p2]

            with (
                patch.object(runner, "_draft_fix_plan") as mock_draft,
                patch.object(
                    runner, "_apply_code_fixes", return_value=True
                ) as mock_apply,
                patch.object(runner, "_record_review_decisions") as mock_rec,
                patch.object(
                    runner, "run_intermediate_check", return_value=(True, "OK")
                ) as mock_scoped,
                patch.object(
                    runner, "run_gate4", return_value=(True, "Gate 4 PASS")
                ) as mock_gate4,
            ):
                ok = runner.step_cross_model_review()
                assert ok
                mock_draft.assert_not_called()
                mock_apply.assert_called_once()
                mock_rec.assert_called_once()
                mock_scoped.assert_called_once()
                mock_gate4.assert_called_once()

        # Negative contract: non-zero dispatch in _apply_code_fixes halts cleanly without marking fixed
        runner.state_file().unlink(missing_ok=True)
        runner_fail = LifecycleRunner(root=root, epic_slug="demo_epic")
        with patch("subprocess.run") as mock_run:
            p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
            non_review_proc = MagicMock(returncode=1, stdout="", stderr="")
            mock_run.side_effect = lambda cmd, **_kw: (
                p1
                if any("run_external_review.py" in str(part) for part in cmd)
                else non_review_proc
            )
            with (
                patch.object(
                    runner_fail.dispatcher, "dispatch", return_value=(1, "", "boom")
                ),
                patch.object(runner_fail, "_record_review_decisions") as mock_rec,
            ):
                ok = runner_fail.step_cross_model_review()
                assert not ok
                mock_rec.assert_not_called()
                assert runner_fail.state.cross_model_round == 1

        # Negative contract: scoped test failure prevents commit and returns False
        with (
            patch.object(
                runner_fail.dispatcher, "dispatch", return_value=(0, "edited", "")
            ),
            patch.object(
                runner_fail, "_run_scoped_tests", return_value=(False, "pytest failed")
            ),
        ):
            assert not runner_fail._apply_code_fixes(1, plan_text="fix")

        # Executive report renders real Top 3 findings & SHAs with zero placeholders or raw-block decoys
        report = runner.render_final_executive_report()
        assert "CR-01" in report or "Null token causes crash in parse_token" in report
        assert "Missing lease fencing spec" in report
        assert "111aaaa" in report
        assert "222bbbb" in report
        assert "State Machine & Process Supervision" not in report
        assert "Gate 4 Candidate Certification" not in report
        assert "Assistant Model Config Precedence" not in report
        assert "FAKE_DECOY_FINDING_IN_RAW_BLOCK" not in report


def test_tto_st_04_cross_model_escalation_on_contract_or_ambiguity() -> None:
    """[TTO-ST-04] Escalate or route through Role 2.1 fix-planner on shared-contracts, debatable, or unverified findings."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        epic_dir = root / ".devtool" / "epic" / "demo_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        (root / "src").mkdir(parents=True, exist_ok=True)
        (root / "src" / "app.py").write_text(
            "x = 1\ny = 2\nz = 3\nw = 4\n", encoding="utf-8"
        )
        (root / "shared-contracts").mkdir(parents=True, exist_ok=True)
        (root / "shared-contracts" / "api_contract.md").write_text(
            "# Contract\n" * 15, encoding="utf-8"
        )

        triage_r1 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_FIX_ELIGIBLE\n"
            "- **Round**: 1 / 3\n"
            "- **Directive**: 1 Critical finding.\n"
        )
        triage_r2 = (
            "## Auto-Triage Gate\n\n"
            "- **Action**: AUTO_PASS_CLEAN\n"
            "- **Round**: 2 / 3\n"
            "- **Directive**: 0 findings.\n"
        )

        # Case 1: shared-contracts conflict refuses fast-track and halts on FIX_PLAN_ESCALATE
        (epic_dir / "review_results.md").write_text(
            "## Round 1\n\n"
            "| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| CR-01 | Critical | `shared-contracts/api_contract.md:5` | Endpoint enum mismatch | Open |\n",
            encoding="utf-8",
        )
        runner = LifecycleRunner(root=root, epic_slug="demo_epic")
        with patch("subprocess.run") as mock_run:
            p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
            non_review_proc = MagicMock(returncode=1, stdout="", stderr="")
            mock_run.side_effect = lambda cmd, **_kw: (
                p1
                if any("run_external_review.py" in str(part) for part in cmd)
                else non_review_proc
            )
            with (
                patch.object(
                    runner,
                    "_draft_fix_plan",
                    return_value=("ESCALATE", ["SHARED_CONTRACT_CONFLICT"], ""),
                ) as mock_draft,
                patch.object(
                    runner, "_apply_code_fixes", return_value=True
                ) as mock_apply,
            ):
                ok = runner.step_cross_model_review()
                assert not ok
                mock_draft.assert_called_once()
                mock_apply.assert_not_called()
                assert runner.state.active_stage == StageName.HALTED.value
                assert runner.state.halt_reason == "FIX_PLAN_ESCALATE"

        # Case 2: Debatable / ambiguous architectural state transition refuses fast-track
        (epic_dir / "review_results.md").write_text(
            "## Round 1\n\n"
            "| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| CR-02 | Important | `src/app.py:2` | Debatable ambiguous architectural state transition | Open |\n",
            encoding="utf-8",
        )
        runner.state_file().unlink(missing_ok=True)
        runner2 = LifecycleRunner(root=root, epic_slug="demo_epic")
        with patch("subprocess.run") as mock_run:
            p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
            p2 = MagicMock(returncode=0, stdout=triage_r2, stderr="")
            mock_run.side_effect = [p1, p1, p2, p2]
            with (
                patch.object(
                    runner2, "_draft_fix_plan", return_value=("PLANNED", [], "Plan")
                ) as mock_draft,
                patch.object(runner2, "_apply_code_fixes", return_value=True),
                patch.object(runner2, "_record_review_decisions"),
                patch.object(
                    runner2, "run_intermediate_check", return_value=(True, "OK")
                ),
                patch.object(runner2, "run_gate4", return_value=(True, "PASS")),
            ):
                ok = runner2.step_cross_model_review()
                assert ok
                mock_draft.assert_called_once()

        # Case 3: Unverified / missing file target refuses fast-track
        (epic_dir / "review_results.md").write_text(
            "## Round 1\n\n"
            "| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| CR-03 | Critical | `src/missing_file.py:12` | Bug in missing file | Open |\n",
            encoding="utf-8",
        )
        runner2.state_file().unlink(missing_ok=True)
        runner3 = LifecycleRunner(root=root, epic_slug="demo_epic")
        with patch("subprocess.run") as mock_run:
            p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
            p2 = MagicMock(returncode=0, stdout=triage_r2, stderr="")
            mock_run.side_effect = [p1, p1, p2, p2]
            with (
                patch.object(
                    runner3, "_draft_fix_plan", return_value=("PLANNED", [], "Plan")
                ) as mock_draft,
                patch.object(runner3, "_apply_code_fixes", return_value=True),
                patch.object(runner3, "_record_review_decisions"),
                patch.object(
                    runner3, "run_intermediate_check", return_value=(True, "OK")
                ),
                patch.object(runner3, "run_gate4", return_value=(True, "PASS")),
            ):
                ok = runner3.step_cross_model_review()
                assert ok
                mock_draft.assert_called_once()


def test_tto_ar_01_parallel_pool_dispatch_and_path_only_prompts() -> None:
    """[TTO-AR-01] Execute DAG waves across non-nested pool slots with path-only prompts and rollback recovery."""
    pool_mod = _load_pool_module()
    with tempfile.TemporaryDirectory() as tmp:
        main_repo = Path(tmp) / "repo"
        main_repo.mkdir(parents=True, exist_ok=True)
        _init_git_repo(main_repo)

        (main_repo / "src").mkdir(parents=True, exist_ok=True)
        (main_repo / "src" / "mod_a.py").write_text("VAL_A = 1\n", encoding="utf-8")
        (main_repo / "src" / "mod_b.py").write_text("VAL_B = 1\n", encoding="utf-8")
        (main_repo / "src" / "mod_c.py").write_text("VAL_C = 1\n", encoding="utf-8")

        epic_dir = main_repo / ".devtool" / "epic" / "demo_epic"
        features_dir = main_repo / ".devtool" / "features"
        epic_dir.mkdir(parents=True, exist_ok=True)
        features_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "hld.en.md").write_text("# HLD\n", encoding="utf-8")
        (epic_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")

        (features_dir / "task_01_a.md").write_text(
            "---\n"
            "id: task_01_a\n"
            "epic: demo_epic\n"
            "status: todo\n"
            "priority: p1\n"
            "---\n\n"
            "# Task 1\n\n"
            "UNIQUE_LONG_PROSE_BODY_SHOULD_NOT_BE_INLINED\n\n"
            "## Dependencies\n"
            "- None\n\n"
            "## Files\n"
            "Allowed files:\n"
            "- `src/mod_a.py`\n\n"
            "- `src/mod_a.py` (L1-L10)\n\n"
            "## Impact Analysis & Blast Radius\n"
            "- `src/mod_a.py` (L1-L10)\n",
            encoding="utf-8",
        )
        (features_dir / "task_02_b.md").write_text(
            "---\n"
            "id: task_02_b\n"
            "epic: demo_epic\n"
            "status: todo\n"
            "priority: p1\n"
            "---\n\n"
            "# Task 2\n\n"
            "UNIQUE_LONG_PROSE_BODY_SHOULD_NOT_BE_INLINED\n\n"
            "## Dependencies\n"
            "- None\n\n"
            "## Files\n"
            "Allowed files:\n"
            "- `src/mod_b.py`\n\n"
            "- `src/mod_b.py` (L1-L10)\n",
            encoding="utf-8",
        )
        (features_dir / "task_03_c.md").write_text(
            "---\n"
            "id: task_03_c\n"
            "epic: demo_epic\n"
            "status: todo\n"
            "priority: p1\n"
            "---\n\n"
            "# Task 3\n\n"
            "UNIQUE_LONG_PROSE_BODY_SHOULD_NOT_BE_INLINED\n\n"
            "## Dependencies\n"
            "- Blocked by: [task_01_a](task_01_a.md)\n"
            "- Blocked by: [task_02_b](task_02_b.md)\n\n"
            "## Files\n"
            "Allowed files:\n"
            "- `src/mod_c.py`\n\n"
            "- `src/mod_c.py` (L1-L10)\n",
            encoding="utf-8",
        )

        # Copy required dev-implementation scripts so worktree executes real scripts locally
        repo_scripts = (
            main_repo / "skills" / "dev-implementation" / "resources" / "scripts"
        )
        repo_scripts.mkdir(parents=True, exist_ok=True)
        src_scripts_dir = (
            Path(__file__).resolve().parent.parent
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
        )
        for script_name in (
            "_epic_docs.py",
            "compute_execution_order.py",
            "manage_worker_pool.py",
            "slug_utils.py",
            "sync_task_status.py",
            "check_bdd_traceability.py",
            "task_contract.py",
            "result_reports.py",
        ):
            shutil.copy2(src_scripts_dir / script_name, repo_scripts / script_name)

        _git(main_repo, "add", "-A")
        _git(main_repo, "commit", "-q", "-m", "[DEMO] Initial setup")

        # Create epic worktree and run LifecycleRunner FROM INSIDE the epic worktree
        epic_wt = main_repo / ".worktrees" / "demo_epic"
        _git(main_repo, "worktree", "add", "-b", "epic/demo_epic", str(epic_wt), "main")

        # Verify resolve_repo_root works inside epic worktree without nesting .worktrees
        assert pool_mod.resolve_repo_root(epic_wt).resolve() == main_repo.resolve()

        runner = LifecycleRunner(root=epic_wt, epic_slug="demo_epic")
        lock = threading.Lock()
        dispatches: list[dict[str, Any]] = []
        active_wave1 = 0
        max_wave1 = 0

        observed_heartbeats: dict[str, dict[str, Any]] = {}
        hb_path = main_repo / ".devtool" / "state" / "demo_epic.heartbeat.json"

        def fake_dispatch(
            self_disp: ModelDispatcher, cli: str, args: list[str], prompt: str
        ) -> tuple[int, str, str]:
            nonlocal active_wave1, max_wave1
            wt = self_disp.worktree_dir
            assert wt is not None
            if "task_01_a" in prompt:
                task_slug = "task_01_a"
                target = wt / "src" / "mod_a.py"
                new_text = "VAL_A = 2\n"
            elif "task_02_b" in prompt:
                task_slug = "task_02_b"
                target = wt / "src" / "mod_b.py"
                new_text = "VAL_B = 2\n"
            else:
                task_slug = "task_03_c"
                target = wt / "src" / "mod_c.py"
                # Wave 2 must see both Wave 1 merged outputs inside its synced slot
                assert (wt / "src" / "mod_a.py").read_text(
                    encoding="utf-8"
                ) == "VAL_A = 2\n"
                assert (wt / "src" / "mod_b.py").read_text(
                    encoding="utf-8"
                ) == "VAL_B = 2\n"
                new_text = "VAL_C = 2\n"

            with lock:
                if task_slug in {"task_01_a", "task_02_b"}:
                    active_wave1 += 1
                    max_wave1 = max(max_wave1, active_wave1)
                if hb_path.is_file():
                    observed_heartbeats[task_slug] = json.loads(
                        hb_path.read_text(encoding="utf-8")
                    )
                dirty_non_runtime = [
                    ln
                    for ln in _git(
                        epic_wt,
                        "status",
                        "--porcelain",
                        "--",
                        ".devtool/features",
                        "src",
                    ).stdout.splitlines()
                ]
                assert dirty_non_runtime == []
            time.sleep(0.05)
            target.write_text(new_text, encoding="utf-8")
            with lock:
                if task_slug in {"task_01_a", "task_02_b"}:
                    active_wave1 -= 1
                dispatches.append(
                    {
                        "task": task_slug,
                        "worktree_dir": wt.resolve(),
                        "args": list(args),
                        "prompt": prompt,
                    }
                )
            return 0, f"done {task_slug}", ""

        with patch.object(
            ModelDispatcher, "dispatch", autospec=True, side_effect=fake_dispatch
        ):
            ok = runner.step_implementation()
            assert ok

        assert len(dispatches) == 3
        assert set(runner.state.completed_tasks) == {
            "task_01_a",
            "task_02_b",
            "task_03_c",
        }

        # Pool slots must sit under main_repo/.worktrees/, never nested inside epic_wt/.worktrees
        assert not (epic_wt / ".worktrees").exists()
        assert not (main_repo / ".worktrees" / "demo_epic-slot-1").exists()
        assert not (main_repo / ".worktrees" / "demo_epic-slot-2").exists()

        slot1_resolved = (main_repo / ".worktrees" / "demo_epic-slot-1").resolve()
        slot2_resolved = (main_repo / ".worktrees" / "demo_epic-slot-2").resolve()
        wave1_wts = {
            d["worktree_dir"]
            for d in dispatches
            if d["task"] in {"task_01_a", "task_02_b"}
        }
        assert wave1_wts == {slot1_resolved, slot2_resolved}
        assert max_wave1 == 2

        assert set(observed_heartbeats) == {"task_01_a", "task_02_b", "task_03_c"}
        hb_w1 = observed_heartbeats["task_01_a"]
        assert hb_w1.get("active_wave") == 1
        assert hb_w1.get("slots", {}).get("slot-1", {}).get("task_id") == "task_01_a"
        assert hb_w1.get("slots", {}).get("slot-1", {}).get("status") == "working"
        assert hb_w1.get("slots", {}).get("slot-2", {}).get("task_id") == "task_02_b"
        assert hb_w1.get("slots", {}).get("slot-2", {}).get("status") == "working"
        hb_w2 = observed_heartbeats["task_03_c"]
        assert hb_w2.get("active_wave") == 2
        assert hb_w2.get("slots", {}).get("slot-1", {}).get("task_id") == "task_03_c"
        assert hb_w2.get("slots", {}).get("slot-1", {}).get("status") == "working"

        for rec in dispatches:
            prompt_text = rec["prompt"]
            assert "UNIQUE_LONG_PROSE_BODY_SHOULD_NOT_BE_INLINED" not in prompt_text
            assert rec["task"] in prompt_text
            assert "do not invoke d3nexus:task-observer" in prompt_text.lower()
            if rec["task"] == "task_01_a":
                assert "src/mod_a.py" in prompt_text
                assert "L1-L10" in prompt_text

        # Epic worktree must reflect all 3 commits and keep task logs untracked under epic_wt
        assert (epic_wt / "src" / "mod_a.py").read_text(
            encoding="utf-8"
        ) == "VAL_A = 2\n"
        assert (epic_wt / "src" / "mod_b.py").read_text(
            encoding="utf-8"
        ) == "VAL_B = 2\n"
        assert (epic_wt / "src" / "mod_c.py").read_text(
            encoding="utf-8"
        ) == "VAL_C = 2\n"
        assert (epic_wt / ".devtool" / "logs" / "tasks" / "task_01_a.log").is_file()
        changed_files = set(
            _git(epic_wt, "diff", "--name-only", "main..HEAD")
            .stdout.strip()
            .splitlines()
        )
        assert {"src/mod_a.py", "src/mod_b.py", "src/mod_c.py"}.issubset(changed_files)
        for task_slug, mod_file in (
            ("task_01_a", "src/mod_a.py"),
            ("task_02_b", "src/mod_b.py"),
            ("task_03_c", "src/mod_c.py"),
        ):
            assert (
                epic_wt / ".devtool" / "features" / "done" / f"{task_slug}.md"
            ).is_file()
            assert not (epic_wt / ".devtool" / "features" / f"{task_slug}.md").exists()
            task_sha = _git(
                epic_wt,
                "log",
                "-n",
                "1",
                "--format=%H",
                "--grep",
                f"Execute {task_slug}$",
            ).stdout.strip()
            assert task_sha
            commit_files = set(
                _git(
                    epic_wt,
                    "show",
                    "--no-renames",
                    "--name-only",
                    "--format=",
                    task_sha,
                )
                .stdout.strip()
                .splitlines()
            )
            assert commit_files == {
                mod_file,
                f".devtool/features/{task_slug}.md",
                f".devtool/features/done/{task_slug}.md",
            }
            assert (main_repo / ".devtool" / "features" / f"{task_slug}.md").is_file()

        # Merge conflict recovery: merge_slot must run git merge --abort on conflict
        pool_mod.init_slots(
            root=main_repo,
            epic_dir="demo_epic",
            epic_slug="demo_epic",
            pool_size=2,
            epic_worktree_root=epic_wt,
        )
        slot1 = pool_mod.get_slot_path(main_repo, "demo_epic", 1)
        (epic_wt / "src" / "mod_a.py").write_text("EPIC_EDIT = 10\n", encoding="utf-8")
        _git(epic_wt, "add", "src/mod_a.py")
        _git(epic_wt, "commit", "-q", "-m", "[DEMO] Epic edit")

        (slot1 / "src" / "mod_a.py").write_text(
            "SLOT_CONFLICT = 99\n", encoding="utf-8"
        )
        _git(slot1, "add", "src/mod_a.py")
        _git(slot1, "commit", "-q", "-m", "[DEMO] Conflicting slot edit")

        merged = pool_mod.merge_slot(
            root=main_repo,
            epic_dir="demo_epic",
            epic_slug="demo_epic",
            slot=1,
            task_id="task_conflict",
            epic_worktree_root=epic_wt,
        )
        assert not merged
        merge_head = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"],
            cwd=epic_wt,
            capture_output=True,
            text=True,
            check=False,
        )
        assert merge_head.returncode != 0
        assert (epic_wt / "src" / "mod_a.py").read_text(
            encoding="utf-8"
        ) == "EPIC_EDIT = 10\n"
        pool_mod.cleanup_slots(
            root=main_repo, epic_dir="demo_epic", epic_slug="demo_epic", pool_size=2
        )

        # Failed slot dispatch keeps task out of completed_tasks, records last_error, and cleans slots
        (epic_wt / ".devtool" / "features" / "task_04_fail.md").write_text(
            "---\n"
            "id: task_04_fail\n"
            "epic: demo_epic\n"
            "status: todo\n"
            "priority: p1\n"
            "---\n\n"
            "# Task 4\n\n"
            "## Dependencies\n"
            "- Blocked by: [task_03_c](task_03_c.md)\n\n"
            "## Files\n"
            "Allowed files:\n"
            "- `src/mod_c.py`\n",
            encoding="utf-8",
        )
        _git(epic_wt, "add", ".devtool/features/task_04_fail.md")
        _git(epic_wt, "commit", "-q", "-m", "[DEMO] Add failing task 4")

        def fail_dispatch(
            self_disp: ModelDispatcher, cli: str, args: list[str], prompt: str
        ) -> tuple[int, str, str]:
            return 1, "", "simulated programmer error"

        with patch.object(
            ModelDispatcher, "dispatch", autospec=True, side_effect=fail_dispatch
        ):
            ok_fail = runner.step_implementation()
            assert not ok_fail

        assert "task_04_fail" not in runner.state.completed_tasks
        assert runner.state.last_error and "task_04_fail" in runner.state.last_error
        assert not (main_repo / ".worktrees" / "demo_epic-slot-1").exists()
        assert not (main_repo / ".worktrees" / "demo_epic-slot-2").exists()


def test_extract_task_targets_filters_non_path_tokens(tmp_path: Path) -> None:
    """_extract_task_targets emits file paths/ranges and drops non-path identifiers like RunnerConfig or TTO-HP-04."""
    runner = LifecycleRunner(root=tmp_path, epic_slug="demo_epic")
    task_md = (
        "## Files\n"
        "Allowed files:\n"
        "- `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` (L44-L80)\n"
        "- `scripts/verify.sh`\n\n"
        "## Impact Analysis & Blast Radius\n"
        "- Updates `RunnerConfig` and `normalize_agy_effort` covered by `TTO-HP-04` and `--compact`.\n"
        "- See `tests/test_lifecycle_runner.py` (L10-L30).\n"
    )
    targets = runner._extract_task_targets(task_md)
    assert (
        "skills/dev-lifecycle/resources/scripts/lifecycle_runner.py (L44-L80)"
        in targets
    )
    assert "scripts/verify.sh" in targets
    assert "tests/test_lifecycle_runner.py (L10-L30)" in targets
    joined = " | ".join(targets)
    assert "RunnerConfig" not in joined
    assert "normalize_agy_effort" not in joined
    assert "TTO-HP-04" not in joined
    assert "--compact" not in joined


if __name__ == "__main__":
    unittest.main()
