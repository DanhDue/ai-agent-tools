#!/usr/bin/env python3
"""End-to-end acceptance test for the verifiable task hand-off.

One compliant task travels the whole lifecycle on a throwaway repository, and every script of the kit
runs as a subprocess in the order the skills tell an agent to run it.

Run: python3 -m unittest scripts/test_verifiable_handoff.py
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/dev-implementation/resources/scripts"
JUNIT = ROOT / "scripts/run_unittest_junit.py"
EPIC = ".devtool/epic/demo"
TASK = "task_1_demo"
TICKS = "`" * 3
TABLE_HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"

HLD = f"""# Demo epic

## Integration Test Plan

Integration test roots: tests/

Protected paths: .agents/quality/**

Integration results: python3 {JUNIT} --junitxml build/r.xml tests/test_demo.py -> build/r.xml

## Verification Environment

Tests run in the repository itself and need no variable.
"""

SCENARIOS = f"""# Scenarios

{TICKS}gherkin
Scenario: [DEMO-HP-01] [Tier C - Integration] Demo
  Given a demo
{TICKS}
"""

DEMO_TEST = """import os
import unittest


class DemoTest(unittest.TestCase):
    def test_demo_hp_01_feature_exists(self) -> None:
        self.assertTrue(os.path.exists("feature.txt"))
"""

TASK_TEXT = f"""---
id: "{TASK}"
status: "todo"
priority: "high"
assignee: null
epic: "demo"
dueDate: null
created: "2026-10-16T00:00:00Z"
modified: "2026-10-16T00:00:00Z"
completedAt: null
labels: []
order: "a1"
---

# Task 1: Demo

## Files

Allowed files:
- `feature.txt` (new)

## Verification

{TABLE_HEAD}| V1 | RED | `test -f feature.txt` | exit non-zero | — |
| V2 | GREEN | `test -f feature.txt` | exit 0 | — |
| V3 | TIER-C | `python3 {JUNIT} --junitxml build/r.xml tests/test_demo.py` | exit 0; results build/r.xml | — |

## Definition of Done

- the feature exists (V2)
- the demo scenario passes (V3)

## Stop and Report If

- A command does not match the repository.

## Decisions Already Made

- Feature file is created in root workspace and verified by test harness.

## BDD Scenarios

Covers: DEMO-HP-01
"""


def git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                           "-C", str(root), *args], capture_output=True, text=True, check=True)
    return done.stdout


class DesignToAuditTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        git(self.root, "init", "-q", "-b", "main")
        for relative, text in {
            f"{EPIC}/demo.en.md": HLD,
            f"{EPIC}/bdd_scenarios.en.md": SCENARIOS,
            ".gitignore": "build/\n",
            "tests/test_demo.py": DEMO_TEST,
            f"{EPIC}/{TASK}.md": TASK_TEXT,
            f".devtool/features/{TASK}.md": TASK_TEXT,
        }.items():
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")
        git(self.root, "checkout", "-q", "-b", "epic/demo")

    def step(self, script: str, *args: str) -> str:
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}  # bytecode would be an untracked change outside Allowed files
        done = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=self.root,
                              capture_output=True, text=True, env=env)
        self.assertEqual(done.returncode, 0, f"{script} {' '.join(args)}\n{done.stdout}\n{done.stderr}")
        return done.stdout

    def test_vth_hp_11_design_to_audit_every_step_exits_0(self) -> None:
        mirror = f"{EPIC}/{TASK}.md"
        self.step("check_task_contract.py", "--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", mirror)
        self.step("check_bdd_traceability.py", "plan", "--scenarios", f"{EPIC}/bdd_scenarios.en.md",
                  "--tasks", mirror)
        self.step("run_task_checks.py", "red", mirror)
        (self.root / "feature.txt").write_text("feature\n", encoding="utf-8")
        self.step("run_task_checks.py", "verify", mirror)
        self.step("sync_task_status.py", "task", TASK, "done")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "[DEMO] Task 1")
        report = self.step("audit_epic.py", "--epic-dir", "demo", "--base", "main")
        self.assertIn("Result: PASS", report)


if __name__ == "__main__":
    unittest.main()
