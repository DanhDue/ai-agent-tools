#!/usr/bin/env python3
"""Tests for Autonomous Lifecycle Runner state machine, persistence, and probing."""

import fcntl
import json
import os
import shutil
import tempfile
import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add skills/dev-lifecycle/resources/scripts to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "skills" / "dev-lifecycle" / "resources" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from lifecycle_runner import (
    FixPlanVerdict,
    LifecycleRunner,
    ModelDispatcher,
    PipelineState,
    RunnerConfig,
    StageName,
)


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
        """Assistant model resolution follows CLI -> review_config.json -> fallback precedence."""
        # 1. Fallback default
        cfg = RunnerConfig()
        self.assertEqual(cfg.resolve_assistant_model(self.root), "claude-sonnet-5-5-high")

        # 2. Config file precedence
        review_config_file = self.root / ".devtool" / "review_config.json"
        review_config_file.parent.mkdir(parents=True, exist_ok=True)
        review_config_file.write_text(
            json.dumps({"providers": {"assistant": {"model": "Opus 5.5"}}}),
            encoding="utf-8",
        )
        self.assertEqual(cfg.resolve_assistant_model(self.root), "Opus 5.5")

        # 3. Explicit CLI config override takes top precedence
        cfg_cli = RunnerConfig(assistant_model="gpt-6.1-sol")
        self.assertEqual(cfg_cli.resolve_assistant_model(self.root), "gpt-6.1-sol")

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
                args=["--model", "gemini-3.8-flash", "--effort", "high", "--mode", "auto"],
                prompt="Implement task 1",
            )

            self.assertEqual(exit_code, 0)
            self.assertIn("Task implementation completed", stdout)
            mock_popen.assert_called_once()
            called_args, called_kwargs = mock_popen.call_args
            self.assertEqual(called_args[0][:6], ["agy", "--model", "gemini-3.8-flash", "--effort", "high", "--mode"])
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

            with patch.object(runner, "sync_gate_ledger", return_value=True) as mock_sync:
                order = runner.resolve_gate3_order()
                self.assertEqual(order, ["task_1_setup", "task_2_impl"])
                self.assertEqual(runner.state.task_order, ["task_1_setup", "task_2_impl"])
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

            mock_proc.communicate.side_effect = subprocess.TimeoutExpired(cmd=["agy"], timeout=1)
            mock_proc.poll.side_effect = [None, 0]  # First poll None (alive), second poll 0 (terminated)
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

        with patch.object(resumed_runner, "_execute_single_task", side_effect=fake_dispatch_task):
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
                self.assertEqual(runner.state.active_stage, StageName.IMPLEMENTATION.value)
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

            with patch.object(runner, "prompt_human_principal_fixes") as mock_prompt:
                with patch.object(runner, "_apply_minor_fixes") as mock_minor:
                    ok = runner.step_principal_review()
                    self.assertTrue(ok)
                    self.assertEqual(runner.state.active_stage, StageName.IMPLEMENTATION.value)
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
            self.assertEqual(runner.state.halt_reason, "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)")

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
            mock_run.side_effect = [mock_proc_r1, mock_proc_r1, mock_proc_r2, mock_proc_r2]

            prompt_called = False

            def fake_prompt(triage_summary: str) -> bool:
                nonlocal prompt_called
                prompt_called = True
                self.assertEqual(runner.state.active_stage, StageName.AWAITING_PRINCIPAL_CONFIRMATION.value)
                return True

            with patch.object(runner, "prompt_human_principal_fixes", side_effect=fake_prompt):
                with patch.object(runner, "_apply_aligned_fixes") as mock_aligned:
                    with patch.object(runner, "_run_package_epic_revise", return_value=True) as mock_pkg:
                        ok = runner.step_principal_review()
                        self.assertTrue(ok)
                        self.assertTrue(prompt_called)
                        self.assertEqual(runner.state.active_stage, StageName.IMPLEMENTATION.value)
                        mock_aligned.assert_called_once()
                        mock_pkg.assert_called_once()
                        proposal = self.root / ".devtool" / "epic" / self.epic_slug / "principal_fix_proposal_round1.md"
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
            self.assertEqual(runner.state.halt_reason, "CIRCUIT_BREAKER_HALT (FIX_LOOP)")

    def test_alr_fr_04(self) -> None:
        """[ALR-FR-04] AI Assistant rejects fix plan with CRITICAL_CONFLICT and halts pipeline."""
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

            with patch.object(runner, "_draft_fix_plan", return_value="Draft fix plan"):
                with patch.object(
                    runner,
                    "evaluate_programmer_fix_plan",
                    return_value=(
                        FixPlanVerdict.CRITICAL_CONFLICT,
                        "Attempted unilateral contract modification",
                    ),
                ):
                    ok = runner.step_cross_model_review()
                    self.assertFalse(ok)
                    self.assertEqual(runner.state.active_stage, StageName.HALTED.value)
                    self.assertIn("CRITICAL_CONFLICT", str(runner.state.halt_reason))

    def test_alr_ec_03(self) -> None:
        """[ALR-EC-03] AI Assistant adjusts AI Programmer fix plan without rejecting."""
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

            mock_run.side_effect = [mock_proc_r1, mock_proc_r1, mock_proc_r2, mock_proc_r2]

            with patch.object(runner, "_draft_fix_plan", return_value="Draft fix plan"):
                with patch.object(
                    runner,
                    "evaluate_programmer_fix_plan",
                    return_value=(
                        FixPlanVerdict.ADJUSTED,
                        "Add edge-case assertion for null payload",
                    ),
                ):
                    with patch.object(runner, "_apply_code_fixes") as mock_apply:
                        with patch.object(runner, "_record_review_decisions"):
                            with patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")):
                                ok = runner.step_cross_model_review()
                                self.assertTrue(ok)
                                self.assertEqual(runner.state.last_verdict, FixPlanVerdict.ADJUSTED.value)
                                mock_apply.assert_called_once()
                                self.assertIn("Add edge-case assertion", mock_apply.call_args[1].get("plan_text", ""))

    def test_alr_hp_04(self) -> None:
        """[ALR-HP-04] AI Assistant approves AI Programmer fix plan in Cross-Model Review without Human stop."""
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

            mock_run.side_effect = [mock_proc_r1, mock_proc_r1, mock_proc_r2, mock_proc_r2]

            with patch.object(runner, "_draft_fix_plan", return_value="Draft fix plan"):
                with patch.object(
                    runner,
                    "evaluate_programmer_fix_plan",
                    return_value=(
                        FixPlanVerdict.APPROVED,
                        "Fix plan adheres to HLD",
                    ),
                ):
                    with patch.object(runner, "_apply_code_fixes") as mock_apply:
                        with patch.object(runner, "_record_review_decisions"):
                            with patch.object(runner, "run_gate4", return_value=(True, "Gate 4 PASS")):
                                ok = runner.step_cross_model_review()
                                self.assertTrue(ok)
                                self.assertEqual(runner.state.active_stage, StageName.AWAITING_FINISH.value)
                                self.assertEqual(runner.state.last_verdict, FixPlanVerdict.APPROVED.value)
                                mock_apply.assert_called_once()


if __name__ == "__main__":
    unittest.main()
