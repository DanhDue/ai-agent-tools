#!/usr/bin/env python3
"""End-to-end integration and acceptance tests for Task Contract Ergonomics (Task 05)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"

if str(DEV_IMPL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DEV_IMPL_SCRIPTS))

import sync_task_status as sts
import task_contract as tc
from run_task_checks import main as run_task_checks_main


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


class TaskContractErgonomics_Integration_E2E_Test(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name).resolve()
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "e2e@example.com")
        _git(self.root, "config", "user.name", "E2ETest")

    def test_TCAE_ST_02_done_gate_evidence_transition(self) -> None:
        """[TCAE-ST-02] Done Gate transitions from FAIL to PASS once declared Evidence file is written."""
        epic_dir = self.root / ".devtool" / "epic" / "sample_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        hld = (
            "# Sample Epic\n\n"
            "## Integration Test Plan\n\n"
            "Protected paths: scripts/verify.sh\n"
        )
        (epic_dir / "sample_epic.en.md").write_text(hld, encoding="utf-8")
        (epic_dir / "bdd_scenarios.en.md").write_text("# Scenarios\n", encoding="utf-8")

        ev_rel = ".devtool/epic/sample_epic/evidence/summary.json"
        task_text = (
            "# Task 1\n\n"
            "## Files\n\n"
            "Allowed files:\n- `feature.txt` (new)\n\n"
            f"Evidence files:\n- `{ev_rel}` (new)\n\n"
            "Read-only context:\n- `README.md` — note\n\n"
            "## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n"
            "|----|-------|---------|--------|-------|\n"
            "| V1 | GREEN | `true` | exit 0 | — |\n\n"
            "## Definition of Done\n\n- done (V1)\n"
        )
        task_path = epic_dir / "task_01_feature.md"
        task_path.write_text(task_text, encoding="utf-8")
        (self.root / "README.md").write_text("readme\n", encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "base")

        # 1. Evaluate before evidence file is written: done gate fails condition 8
        (self.root / "feature.txt").write_text("feature content\n", encoding="utf-8")
        ret = run_task_checks_main(["verify", str(task_path)])
        self.assertEqual(ret, 0)

        failures = tc.evaluate_done_gate(task_path)
        self.assertTrue(len(failures) > 0)
        self.assertTrue(
            any(ev_rel in f and "condition 8" in f for f in failures),
            f"Expected condition 8 failure for {ev_rel}, got: {failures}",
        )

        # 2. Write non-empty JSON to evidence file: done gate transitions to PASS
        ev_file = self.root / ev_rel
        ev_file.parent.mkdir(parents=True, exist_ok=True)
        ev_file.write_text(
            json.dumps({"status": "PASS", "records": 42}) + "\n", encoding="utf-8"
        )

        failures_after = tc.evaluate_done_gate(task_path)
        self.assertEqual(failures_after, [])

    def test_TCAE_AR_02_idempotent_render(self) -> None:
        """[TCAE-AR-02] Deterministic idempotent re-rendering across repeated render calls."""
        epic_dir = self.root / ".devtool" / "epic" / "sample_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        embed_file = self.root / "docs" / "snippet.py"
        embed_file.parent.mkdir(parents=True, exist_ok=True)
        embed_file.write_text(
            "def hello() -> str:\n    return 'world'\n", encoding="utf-8"
        )

        scenarios_text = (
            "# Scenarios\n\n"
            "```gherkin\n"
            "Scenario: [TCAE-01] First scenario\n"
            "  Given something\n\n"
            "Scenario: [TCAE-02] Second scenario\n"
            "  Given another thing\n"
            "```\n"
        )
        (epic_dir / "bdd_scenarios.en.md").write_text(scenarios_text, encoding="utf-8")

        task1_canonical = (
            '---\nstatus: "todo"\n---\n'
            "# Task 01\n\n"
            "Covers: TCAE-01\n\n"
            "## Requirement Analysis\n\n"
            "Check [task_02](task_02_b.md).\n\n"
            "## Embedded Snippet\n\n"
            "<!-- @@FILE:docs/snippet.py@@ -->\n"
            "```python\n"
            "placeholder\n"
            "```\n\n"
            "## Files\n\nAllowed files:\n- `feature.txt`\n\n"
            "## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n"
            "|----|-------|---------|--------|-------|\n"
            "| V1 | GREEN | `true` | exit 0 | — |\n\n"
            "## Definition of Done\n\n- done (V1)\n"
        )
        task2_canonical = (
            '---\nstatus: "todo"\n---\n'
            "# Task 02\n\n"
            "Covers: TCAE-02\n\n"
            "## Requirement Analysis\n\n"
            "Check [task_01](task_01_a.md).\n\n"
            "## Files\n\nAllowed files:\n- `feature.txt`\n\n"
            "## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n"
            "|----|-------|---------|--------|-------|\n"
            "| V1 | GREEN | `true` | exit 0 | — |\n\n"
            "## Definition of Done\n\n- done (V1)\n"
        )
        (epic_dir / "task_01_a.md").write_text(task1_canonical, encoding="utf-8")
        (epic_dir / "task_02_b.md").write_text(task2_canonical, encoding="utf-8")

        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "base")

        # First render
        sts.render_epic_tasks(self.root, "sample_epic")

        features_dir = self.root / ".devtool" / "features"
        t1_first = (features_dir / "task_01_a.md").read_text(encoding="utf-8")
        t2_first = (features_dir / "task_02_b.md").read_text(encoding="utf-8")
        epic_t1_first = (epic_dir / "task_01_a.md").read_text(encoding="utf-8")
        epic_t2_first = (epic_dir / "task_02_b.md").read_text(encoding="utf-8")

        # Verify embedded file was expanded and BDD scenario injected
        self.assertIn("def hello() -> str:", t1_first)
        self.assertIn("Scenario: [TCAE-01] First scenario", t1_first)
        self.assertIn("Scenario: [TCAE-02] Second scenario", t2_first)

        # Second render without edits
        sts.render_epic_tasks(self.root, "sample_epic")

        t1_second = (features_dir / "task_01_a.md").read_text(encoding="utf-8")
        t2_second = (features_dir / "task_02_b.md").read_text(encoding="utf-8")
        epic_t1_second = (epic_dir / "task_01_a.md").read_text(encoding="utf-8")
        epic_t2_second = (epic_dir / "task_02_b.md").read_text(encoding="utf-8")

        # Idempotence: byte-for-byte identical
        self.assertEqual(t1_first, t1_second)
        self.assertEqual(t2_first, t2_second)
        self.assertEqual(epic_t1_first, epic_t1_second)
        self.assertEqual(epic_t2_first, epic_t2_second)

    def test_TCAE_FR_03_render_unknown_covers_aborts(self) -> None:
        """[TCAE-FR-03] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file."""
        epic_dir = self.root / ".devtool" / "epic" / "sample_epic"
        epic_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "bdd_scenarios.en.md").write_text(
            "# Scenarios\n\n```gherkin\nScenario: [TCAE-HP-01] Known\n  Given a\n```\n",
            encoding="utf-8",
        )

        unknown_id = "TCAE" + "-HP-99"
        task_canonical = (
            '---\nstatus: "todo"\n---\n'
            "# Task 01\n\n"
            f"Covers: {unknown_id}\n\n"
            "## Files\n\nAllowed files:\n- `feature.txt`\n\n"
            "## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n"
            "|----|-------|---------|--------|-------|\n"
            "| V1 | GREEN | `true` | exit 0 | — |\n\n"
            "## Definition of Done\n\n- done (V1)\n"
        )
        (epic_dir / "task_01_a.md").write_text(task_canonical, encoding="utf-8")

        features_dir = self.root / ".devtool" / "features"
        features_dir.mkdir(parents=True, exist_ok=True)
        existing_feature_task = features_dir / "task_01_a.md"
        existing_feature_task.write_text("PREEXISTING_CONTENT\n", encoding="utf-8")

        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-q", "-m", "base")

        # When executed via CLI or subprocess
        res = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "sync_task_status.py"),
                "render",
                "sample_epic",
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 1)
        self.assertIn(unknown_id, res.stderr)

        # Existing features task remains untouched
        self.assertEqual(
            existing_feature_task.read_text(encoding="utf-8"), "PREEXISTING_CONTENT\n"
        )


if __name__ == "__main__":
    unittest.main()
