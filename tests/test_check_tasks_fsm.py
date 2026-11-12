"""Unit tests for check-tasks deterministic lifecycle FSM engine.

Covers BDD Scenarios:
- CTD-HP-02: Deterministic Lifecycle FSM derives exact human decision prompt
- CTD-ST-01: FSM transitions from Stage 2 Architecture to Stage 2 Exit Handoff
- CTD-ST-02: FSM transitions to Stage 3 Phase 2 TDD when tasks enter in-progress
"""

from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT_DIR = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "check-tasks"
    / "resources"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from check_tasks import (
        LifecycleDecision,
        LifecycleStage,
        derive_lifecycle_state,
    )
except ImportError:
    pass


class TestCheckTasksFSM_Integration(unittest.TestCase):
    """Test suite for deterministic lifecycle FSM engine."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _init_gate_ledger(self, gates: list[dict[str, object]]) -> None:
        devtool = self.repo_path / ".devtool"
        devtool.mkdir(parents=True, exist_ok=True)
        ledger = devtool / "GATE_LEDGER.md"
        lines = [
            "| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations / Notes | Approver |",
            "|---|---|---|---|---|---|---|",
        ]
        for g in gates:
            lines.append(
                f"| {g.get('timestamp', '2026-11-11T00:00:00Z')} | {g.get('epic', 'test_epic')} | "
                f"{g.get('gate', 1)} | {g.get('commit', 'abc1234')} | {g.get('approved', 'Approved')} | "
                f"{g.get('deviations', '')} | {g.get('by', 'developer')} |"
            )
        ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_ctd_hp_02(self) -> None:
        """[CTD-HP-02] [Tier C - Integration] Deterministic Lifecycle FSM derives exact human decision prompt."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
                {"epic": epic_name, "gate": 2, "approved": "HLD approved"},
                {"epic": epic_name, "gate": 3, "approved": "Order confirmed"},
                {"epic": epic_name, "gate": 4, "approved": "Verification PASS"},
            ]
        )
        features_dir = self.repo_path / ".devtool" / "features"
        done_dir = features_dir / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        task_done = done_dir / "task_1.md"
        task_done.write_text(
            "---\nid: task_1\nstatus: done\nepic: test_epic\n---\n# Task 1\n",
            encoding="utf-8",
        )

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_3_PHASE_4_REVIEW)
        self.assertIn("Review Choice (Rule 5)", decision.prompt)
        self.assertTrue(decision.is_human_action_required)

    def test_ctd_st_01(self) -> None:
        """[CTD-ST-01] [Tier A - Unit] FSM transitions from Stage 2 Architecture to Stage 2 Exit Handoff."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
                {"epic": epic_name, "gate": 2, "approved": "HLD approved"},
            ]
        )
        epic_dir = self.repo_path / ".devtool" / "epic" / epic_name
        epic_dir.mkdir(parents=True, exist_ok=True)
        handoff = epic_dir / "handoff.md"
        handoff.write_text("# Handoff\nReady for handoff choice\n", encoding="utf-8")

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_2_EXIT_HANDOFF)
        self.assertIn("principal-review", decision.prompt.lower())
        self.assertTrue(decision.is_human_action_required)

    def test_ctd_st_02(self) -> None:
        """[CTD-ST-02] [Tier A - Unit] FSM transitions to Stage 3 Phase 2 TDD when tasks enter in-progress."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
                {"epic": epic_name, "gate": 2, "approved": "HLD approved"},
                {"epic": epic_name, "gate": 3, "approved": "Order confirmed"},
            ]
        )
        features_dir = self.repo_path / ".devtool" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        task_file = features_dir / "task_1.md"
        task_file.write_text(
            "---\nid: task_1\nstatus: in-progress\nepic: test_epic\n---\n# Task 1\n",
            encoding="utf-8",
        )

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_3_PHASE_2_TDD)
        self.assertFalse(decision.is_human_action_required)
        self.assertIn("TDD", decision.prompt)

    def test_idle_when_no_active_epic(self) -> None:
        """FSM returns Idle when active_epic is None."""
        decision = derive_lifecycle_state(self.repo_path, None)
        self.assertEqual(decision.stage_name, LifecycleStage.IDLE)
        self.assertFalse(decision.is_human_action_required)

    def test_stage_1_inception(self) -> None:
        """FSM returns Stage 1 Inception when no gates are passed but spec exists."""
        epic_name = "new_feature"
        epic_dir = self.repo_path / ".devtool" / "epic" / epic_name
        epic_dir.mkdir(parents=True, exist_ok=True)
        spec = epic_dir / f"{epic_name}.en.md"
        spec.write_text("# Feature Spec\n", encoding="utf-8")

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_1_INCEPTION)
        self.assertTrue(decision.is_human_action_required)
        self.assertIn("Gate 1", decision.prompt)

    def test_stage_2_architecture(self) -> None:
        """FSM returns Stage 2 Architecture when Gate 1 passes but Gate 2 is not yet approved."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
            ]
        )
        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_2_ARCHITECTURE)
        self.assertFalse(decision.is_human_action_required)

    def test_stage_3_phase_1_order(self) -> None:
        """FSM returns Stage 3 Phase 1 Order when Gate 2 passes and worktree exists but no Gate 3."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
                {"epic": epic_name, "gate": 2, "approved": "HLD approved"},
            ]
        )
        worktree_dir = self.repo_path / ".worktrees" / epic_name
        worktree_dir.mkdir(parents=True, exist_ok=True)

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_3_PHASE_1_ORDER)
        self.assertTrue(decision.is_human_action_required)
        self.assertIn("Gate 3", decision.prompt)

    def test_stage_3_phase_4_1_signoff(self) -> None:
        """FSM returns Stage 3 Phase 4.1 Sign-off when Gate 4 PASS and cross-model review converged."""
        epic_name = "test_epic"
        self._init_gate_ledger(
            [
                {"epic": epic_name, "gate": 1, "approved": "Spec approved"},
                {"epic": epic_name, "gate": 2, "approved": "HLD approved"},
                {"epic": epic_name, "gate": 3, "approved": "Order confirmed"},
                {"epic": epic_name, "gate": 4, "approved": "Verification PASS"},
            ]
        )
        devtool = self.repo_path / ".devtool"
        state = devtool / "assistant_state.md"
        state.write_text(
            "# Assistant State\n## Status:\nReview Converged\n## Next Immediate Step:\nApprove Gate 5 (Kanban Sign-off)\n",
            encoding="utf-8",
        )

        decision = derive_lifecycle_state(self.repo_path, epic_name)
        self.assertEqual(decision.stage_name, LifecycleStage.STAGE_3_PHASE_4_1_SIGNOFF)
        self.assertTrue(decision.is_human_action_required)
        self.assertIn("Gate 5", decision.prompt)


if __name__ == "__main__":
    unittest.main()
