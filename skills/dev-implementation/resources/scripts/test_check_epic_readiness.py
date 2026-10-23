#!/usr/bin/env python3
"""Tests for check_epic_readiness.py (Task 1: Readiness Check Core).

Run:
    python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = SCRIPTS_DIR / "check_epic_readiness.py"

# Try importing the module under test
try:
    import check_epic_readiness
except ImportError:
    check_epic_readiness = None  # type: ignore[assignment]


def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def build_ready_epic(root: Path) -> None:
    """Writes the PRV-HP-01 epic demo_epic (slug demo-epic, 2 tasks) into root.

    Commits nothing related to the epic.
    """
    # Ensure baseline repo tracked files exist and are committed
    tracked = subprocess.run(
        ["git", "-C", str(root), "ls-files", "tool.py"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not tracked:
        (root / "tool.py").write_text("def run():\n    pass\n", encoding="utf-8")
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
        (root / "scripts").mkdir(parents=True, exist_ok=True)
        (root / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
        git_cmd(root, "add", "tool.py", "README.md", "scripts/verify.sh", ".gitignore")
        git_cmd(root, "commit", "-m", "initial commit", "-q")

    epic_dir = root / ".devtool" / "epic" / "demo_epic"
    features_dir = root / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    # 1. Spec pair
    spec_en = """# Demo Epic Design

## Table of Contents

- [Meta Data](#meta-data)
- [Overview](#overview)

## Meta Data

- **Status**: Approved (Gate 1)

## Overview

Approved spec overview text.
"""
    spec_vi = """# Demo Epic Design

## Table of Contents

- [Meta Data](#meta-data)
- [Overview](#overview)

## Meta Data

- **Status**: Approved (Gate 1)

## Overview

Nội dung tổng quan thiết kế đã được phê duyệt.
"""
    (epic_dir / "2026-10-22-demo-epic-design.en.md").write_text(spec_en, encoding="utf-8")
    (epic_dir / "2026-10-22-demo-epic-design.vi.md").write_text(spec_vi, encoding="utf-8")

    # 2. HLD pair
    hld_en = """# Demo Epic High-Level Design

## Table of Contents

- [Meta Data](#meta-data)
- [Integration Test Plan](#integration-test-plan)
- [Verification Environment](#verification-environment)
- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)

## Meta Data

- **Epic name**: demo_epic
- **Status**: Planned

## Integration Test Plan

Protected paths: scripts/verify.sh

Integration test roots: tests/

Integration results: python3 tool.py int -> build/test-results/int.xml

## Verification Environment

Tests run in temporary directories.

## Kanban Tasks Breakdown

1. [Task 1](task_1.md)
2. [Task 2](task_2.md)
"""
    hld_vi = """# Demo Epic High-Level Design

## Table of Contents

- [Meta Data](#meta-data)
- [Integration Test Plan](#integration-test-plan)
- [Verification Environment](#verification-environment)
- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)

## Meta Data

- **Epic name**: demo_epic
- **Status**: Planned

## Integration Test Plan

Protected paths: scripts/verify.sh

Integration test roots: tests/

Integration results: python3 tool.py int -> build/test-results/int.xml

## Verification Environment

Các bài kiểm tra chạy trong thư mục tạm.

## Kanban Tasks Breakdown

1. [Task 1](task_1.md)
2. [Task 2](task_2.md)
"""
    (epic_dir / "demo_epic.en.md").write_text(hld_en, encoding="utf-8")
    (epic_dir / "demo_epic.vi.md").write_text(hld_vi, encoding="utf-8")

    # 3. BDD Scenarios pair
    bdd_en = """# Demo Epic BDD Scenarios

## Table of Contents

- [Coverage Matrix](#coverage-matrix)
- [Scenarios](#scenarios)

## Coverage Matrix

| Scenario ID | Dimension | Target Component | Description |
|---|---|---|---|
| `[DEMO-HP-01]` | Happy Path | `tool.py` | Unit scenario description |
| `[DEMO-HP-02]` | Happy Path | `tool.py` | Integration scenario description |

## Scenarios

### DEMO-HP-01: Unit scenario description

```gherkin
Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
  Given something
  When something happens
  Then it passes
```

### DEMO-HP-02: Integration scenario description

```gherkin
Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
  Given something
  When integration happens
  Then it passes
```
"""
    bdd_vi = """# Demo Epic BDD Scenarios

## Table of Contents

- [Coverage Matrix](#coverage-matrix)
- [Scenarios](#scenarios)

## Coverage Matrix

| Scenario ID | Dimension | Target Component | Description |
|---|---|---|---|
| `[DEMO-HP-01]` | Happy Path | `tool.py` | Unit scenario description |
| `[DEMO-HP-02]` | Happy Path | `tool.py` | Integration scenario description |

## Scenarios

### DEMO-HP-01: Unit scenario description

```gherkin
Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
  Given something
  When something happens
  Then it passes
```

### DEMO-HP-02: Integration scenario description

```gherkin
Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
  Given something
  When integration happens
  Then it passes
```
"""
    (epic_dir / "bdd_scenarios.en.md").write_text(bdd_en, encoding="utf-8")
    (epic_dir / "bdd_scenarios.vi.md").write_text(bdd_vi, encoding="utf-8")

    # 4. Tasks
    task_1_epic = """---
id: "task_1"
status: "todo"
priority: "high"
assignee: null
epic: "demo-epic"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-22T09:10:00Z"
completedAt: null
labels: ["demo"]
order: "a1"
---

# Task 1: First Task

Epic: [demo_epic](demo_epic.en.md)

Covers: DEMO-HP-01

## Requirement Analysis

Requirement text for task 1.

## Files

Allowed files:
- `tool.py`

Read-only context:
- `README.md` — context note

## Design Rationale

Design rationale for task 1.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tool.py`: `run`

### BDD SCENARIOS

Covers: DEMO-HP-01

```gherkin
Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
  Given something
  When something happens
  Then it passes
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 tool.py red` | exit 1 | — |
| V2 | GREEN | `python3 tool.py green` | exit 0 | — |
| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |
| V4 | TIER-B | `mypy tool.py` | exit 0 | — |
| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |

## Stop and Report If

- A command fails unexpectedly.

## Decisions Already Made

- Real grounded decision for tool.py.

## Definition of Done

- All checks pass (V2, V3, V4, V5).
"""

    task_2_epic = """---
id: "task_2"
status: "todo"
priority: "high"
assignee: null
epic: "demo-epic"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-22T09:10:00Z"
completedAt: null
labels: ["demo"]
order: "a2"
---

# Task 2: Second Task

Epic: [demo_epic](demo_epic.en.md)

Covers: DEMO-HP-02

## Requirement Analysis

Requirement text for task 2.

## Files

Allowed files:
- `tool.py`

Read-only context:
- `README.md` — context note

## Design Rationale

Design rationale for task 2.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `tool.py`: `run`

### BDD SCENARIOS

Covers: DEMO-HP-02

```gherkin
Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
  Given something
  When integration happens
  Then it passes
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 tool.py red2` | exit 1 | — |
| V2 | GREEN | `python3 tool.py green2` | exit 0 | — |
| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |
| V4 | TIER-B | `mypy tool.py` | exit 0 | — |
| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |

## Stop and Report If

- A command fails unexpectedly.

## Decisions Already Made

- Real grounded decision for tool.py.

## Definition of Done

- All checks pass (V2, V3, V4, V5).
"""

    (epic_dir / "task_1.md").write_text(task_1_epic, encoding="utf-8")
    (epic_dir / "task_2.md").write_text(task_2_epic, encoding="utf-8")

    # 5. Mirrors in .devtool/features/
    task_1_feature = task_1_epic.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
    task_2_feature = task_2_epic.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
    (features_dir / "task_1.md").write_text(task_1_feature, encoding="utf-8")
    (features_dir / "task_2.md").write_text(task_2_feature, encoding="utf-8")


class ReadinessCoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name).resolve()

        git_cmd(self.root, "init", "-q")
        git_cmd(self.root, "config", "user.email", "tester@example.com")
        git_cmd(self.root, "config", "user.name", "Tester")

        build_ready_epic(self.root)

    def run_check(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        run_cwd = cwd or self.root
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            check=False,
            cwd=run_cwd,
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_prv_hp_01_ready_fixture_epic_passes_every_check(self) -> None:
        """PRV-HP-01: A ready fixture epic passes every check."""
        code, stdout, stderr = self.run_check("demo_epic")
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}\nStderr:\n{stderr}")
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]
        self.assertTrue(lines, "No output received")
        self.assertEqual(lines[0], "Epic: demo_epic (demo-epic), 2 tasks")

        expected_checks = [
            "R1 PASS",
            "R2 PASS",
            "R3 PASS",
            "R4 PASS",
            "R5 PASS",
            "R6 PASS",
            "R7 PASS",
            "R8 SKIP",
        ]
        for expected in expected_checks:
            self.assertIn(expected, stdout)

        self.assertEqual(lines[-1], "Result: 0 FAIL, 0 WARN — PASS")

    def test_prv_ec_02_tier_drift_fails_r3_and_tier_b_tag_fails_r4(self) -> None:
        """PRV-EC-02: Tier drift fails R3 and a Tier B tag fails R4."""
        bdd_path = self.root / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.en.md"
        bdd_text = bdd_path.read_text(encoding="utf-8")
        # Change tag in bdd_scenarios.en.md to [Tier B - Unit]
        bdd_text = bdd_text.replace(
            "Scenario: [DEMO-HP-01] [Tier A - Unit]",
            "Scenario: [DEMO-HP-01] [Tier B - Unit]",
        )
        bdd_path.write_text(bdd_text, encoding="utf-8")

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")

        # Check for R3 FAIL line mentioning task_1 and DEMO-HP-01
        r3_fails = [line for line in stdout.splitlines() if line.startswith("R3 FAIL")]
        self.assertTrue(r3_fails, f"Expected R3 FAIL line in stdout:\n{stdout}")
        self.assertTrue(
            any("task_1" in line and "DEMO-HP-01" in line for line in r3_fails),
            f"Expected R3 FAIL line containing task_1 and DEMO-HP-01, got:\n{stdout}",
        )

        # Check for R4 FAIL line mentioning DEMO-HP-01 and Tier B - Unit
        r4_fails = [line for line in stdout.splitlines() if line.startswith("R4 FAIL")]
        self.assertTrue(r4_fails, f"Expected R4 FAIL line in stdout:\n{stdout}")
        self.assertTrue(
            any("DEMO-HP-01" in line and "Tier B - Unit" in line for line in r4_fails),
            f"Expected R4 FAIL line containing DEMO-HP-01 and 'Tier B - Unit', got:\n{stdout}",
        )

    def test_prv_ec_04_mirror_drift_fails_and_location_link_passes(self) -> None:
        """PRV-EC-04: Mirror drift fails R2 and location-only link differences pass."""
        # Baseline ready epic already has mirror link pointing to ../epic/demo_epic/demo_epic.en.md
        # while epic copy points to demo_epic.en.md. That should pass R2!
        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}")
        self.assertIn("R2 PASS", stdout)

        # Mutate mirror in .devtool/features/task_1.md: add "Stale sentence."
        mirror_path = self.root / ".devtool" / "features" / "task_1.md"
        mirror_text = mirror_path.read_text(encoding="utf-8")
        mirror_text = mirror_text.replace(
            "## Requirement Analysis\n\nRequirement text for task 1.",
            "## Requirement Analysis\n\nRequirement text for task 1.\nStale sentence.",
        )
        mirror_path.write_text(mirror_text, encoding="utf-8")

        code2, stdout2, _stderr2 = self.run_check("demo_epic")
        self.assertEqual(code2, 1, f"Expected 1, got {code2}.\nStdout:\n{stdout2}")
        r2_fails = [line for line in stdout2.splitlines() if line.startswith("R2 FAIL")]
        self.assertTrue(r2_fails, f"Expected R2 FAIL in output:\n{stdout2}")
        self.assertTrue(
            any("task_1" in line and "Stale sentence." in line for line in r2_fails),
            f"Expected R2 FAIL containing 'task_1' and 'Stale sentence.', got:\n{stdout2}",
        )

    def test_prv_ec_05_metadata_packaged_without_handoff_and_draft_spec(self) -> None:
        """PRV-EC-05: Packaged without a handoff fails R7 and a draft spec warns R7b."""
        hld_path = self.root / ".devtool" / "epic" / "demo_epic" / "demo_epic.en.md"
        hld_text = hld_path.read_text(encoding="utf-8").replace("- **Status**: Planned", "- **Status**: Packaged")
        hld_path.write_text(hld_text, encoding="utf-8")

        spec_path = self.root / ".devtool" / "epic" / "demo_epic" / "2026-10-22-demo-epic-design.en.md"
        spec_text = spec_path.read_text(encoding="utf-8").replace(
            "- **Status**: Approved (Gate 1)",
            "- **Status**: Draft, awaiting Gate 1 review",
        )
        spec_path.write_text(spec_text, encoding="utf-8")

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
        self.assertTrue(any(line.startswith("R7 FAIL") and "handoff.md" in line for line in stdout.splitlines()))
        self.assertTrue(
            any(
                line.startswith("R7b WARN") and "Draft, awaiting Gate 1 review" in line
                for line in stdout.splitlines()
            )
        )

        # Add handoff.md with Design commit: `uncommitted`
        handoff_content = """# Handoff: demo_epic

## Table of Contents

- [Status](#status)

## Status

- **Design commit**: `uncommitted`
"""
        (self.root / ".devtool" / "epic" / "demo_epic" / "handoff.md").write_text(handoff_content, encoding="utf-8")

        code2, stdout2, _stderr2 = self.run_check("demo_epic")
        self.assertEqual(code2, 0, f"Expected 0 after adding handoff, got {code2}.\nStdout:\n{stdout2}")
        self.assertIn("R7 PASS", stdout2)

    def test_prv_fr_02_failing_preflight_subcheck_and_missing_dir(self) -> None:
        """PRV-FR-02: A failing preflight sub-check fails R1 by name; missing dir exits 2."""
        bdd_path = self.root / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.en.md"
        bdd_text = bdd_path.read_text(encoding="utf-8")
        extra_scenario = """
### DEMO-EC-09: Uncovered scenario

```gherkin
Scenario: [DEMO-EC-09] [Tier C - Integration] Uncovered scenario
  Given something
  When something happens
  Then it passes
```
"""
        bdd_path.write_text(bdd_text + extra_scenario, encoding="utf-8")
        # Also mirror in bdd_scenarios.vi.md so R3 doesn't fail on missing vi ID before R1
        bdd_vi_path = self.root / ".devtool" / "epic" / "demo_epic" / "bdd_scenarios.vi.md"
        bdd_vi_path.write_text(bdd_vi_path.read_text(encoding="utf-8") + extra_scenario, encoding="utf-8")

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
        r1_fails = [line for line in stdout.splitlines() if line.startswith("R1 FAIL")]
        self.assertTrue(r1_fails, f"Expected R1 FAIL in stdout:\n{stdout}")
        self.assertTrue(
            any("check_bdd_traceability.py plan" in line for line in r1_fails),
            f"Expected R1 FAIL mentioning 'check_bdd_traceability.py plan', got:\n{stdout}",
        )

        # Missing directory exits 2
        code2, _stdout2, stderr2 = self.run_check("nonexistent_epic_dir")
        self.assertEqual(code2, 2, f"Expected 2 for nonexistent dir, got {code2}")
        self.assertTrue(stderr2.strip() != "", "Expected stderr output for nonexistent dir")


class ReadinessGroundingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name).resolve()

        git_cmd(self.root, "init", "-q")
        git_cmd(self.root, "config", "user.email", "tester@example.com")
        git_cmd(self.root, "config", "user.name", "Tester")

        build_ready_epic(self.root)

    def run_check(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
        run_cwd = cwd or self.root
        proc = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            check=False,
            cwd=run_cwd,
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def update_task_both(self, task_name: str, updater: Any) -> None:
        epic_file = self.root / ".devtool" / "epic" / "demo_epic" / task_name
        feat_file = self.root / ".devtool" / "features" / task_name
        text = epic_file.read_text(encoding="utf-8")
        new_text = updater(text)
        epic_file.write_text(new_text, encoding="utf-8")
        feat_text = new_text.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
        feat_file.write_text(feat_text, encoding="utf-8")

    def test_prv_ec_01_symbol_missing_from_file_fails_r5(self) -> None:
        """PRV-EC-01: A symbol missing from its file fails R5."""
        (self.root / "src").mkdir(parents=True, exist_ok=True)
        (self.root / "src" / "app.py").write_text("def other():\n    pass\n", encoding="utf-8")

        def modify_task(text: str) -> str:
            text = text.replace(
                "Allowed files:\n- `tool.py`",
                "Allowed files:\n- `tool.py`\n- `src/app.py`",
            )
            text = text.replace(
                "- **Target Files & Symbols**:\n  - `tool.py`: `run`",
                "- **Target Files & Symbols**:\n  - `tool.py`: `run`\n  - `src/app.py`: `build_payload()`, new `render()`",
            )
            return text

        self.update_task_both("task_2.md", modify_task)

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
        r5_fails = [line for line in stdout.splitlines() if line.startswith("R5 FAIL")]
        self.assertTrue(r5_fails, f"Expected R5 FAIL in stdout:\n{stdout}")
        self.assertTrue(
            any("task_2" in line and "build_payload" in line and "src/app.py" in line for line in r5_fails),
            f"Expected R5 FAIL containing task_2, build_payload, src/app.py. Got:\n{stdout}",
        )
        self.assertFalse(any("render" in line for line in stdout.splitlines() if line.startswith("R5")), f"Render should not be mentioned in R5:\n{stdout}")
        self.assertTrue(stdout.strip().splitlines()[-1].endswith("— FAIL"))

    def test_prv_ec_03_tier_c_test_outside_integration_results_fails_r6(self) -> None:
        """PRV-EC-03: A TIER-C test outside every Integration results command fails R6."""
        hld_path = self.root / ".devtool" / "epic" / "demo_epic" / "demo_epic.en.md"
        hld_text = hld_path.read_text(encoding="utf-8")
        hld_text = hld_text.replace(
            "Integration results: python3 tool.py int -> build/test-results/int.xml",
            "Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/int.xml tests/test_core.py",
        )
        hld_path.write_text(hld_text, encoding="utf-8")

        def modify_task(text: str) -> str:
            return text.replace(
                "`python3 tool.py int`",
                "`python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_extra.py`",
            )

        self.update_task_both("task_2.md", modify_task)

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nStdout:\n{stdout}")
        r6_fails = [line for line in stdout.splitlines() if line.startswith("R6 FAIL")]
        self.assertTrue(r6_fails, f"Expected R6 FAIL in stdout:\n{stdout}")
        self.assertTrue(
            any("task_2" in line and "tests/test_extra.py" in line for line in r6_fails),
            f"Expected R6 FAIL containing task_2 and tests/test_extra.py. Got:\n{stdout}",
        )

    def test_prv_ec_06_route_not_found_warns_r5b(self) -> None:
        """PRV-EC-06: A route found in no source file warns R5b without failing."""
        (self.root / "tool.py").write_text(
            'ENDPOINT = "/api/studio/extract/start"\ndef run():\n    pass\n',
            encoding="utf-8",
        )
        git_cmd(self.root, "add", "tool.py")
        git_cmd(self.root, "commit", "-m", "update tool.py with endpoint", "-q")

        def modify_task(text: str) -> str:
            return text.replace(
                "Requirement text for task 1.",
                "Requirement text for task 1 calling /api/tts/ocr-upload endpoint.",
            )

        self.update_task_both("task_1.md", modify_task)

        code, stdout, _stderr = self.run_check("demo_epic")
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}")
        r5b_warns = [line for line in stdout.splitlines() if line.startswith("R5b WARN")]
        self.assertTrue(r5b_warns, f"Expected R5b WARN in stdout:\n{stdout}")
        self.assertTrue(
            any("/api/tts/ocr-upload" in line for line in r5b_warns),
            f"Expected R5b WARN containing /api/tts/ocr-upload. Got:\n{stdout}",
        )
        self.assertFalse(any("/api/studio/extract/start" in line for line in stdout.splitlines()))
        self.assertEqual(stdout.strip().splitlines()[-1], "Result: 0 FAIL, 1 WARN — PASS")

    def test_prv_fr_01_baseline_failures_and_timeouts_warn(self) -> None:
        """PRV-FR-01: Baseline failures and timeouts warn and other rows still run."""
        # Ensure clean git tree by committing existing files
        git_cmd(self.root, "add", "-A")
        git_cmd(self.root, "commit", "-m", "setup baseline clean tree", "-q")

        # 1. Update task_1 with rows:
        # V2 GREEN: python3 -c 'raise SystemExit(1)' expecting exit 0
        # V3 TIER-B: sleep 5 expecting exit 0
        # V4 GREEN: python3 -c 'print(1)' expecting exit 0
        def modify_task_1(text: str) -> str:
            text = text.replace(
                "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
                "| V2 | GREEN | `python3 -c 'raise SystemExit(1)'` | exit 0 | — |\n| V3 | TIER-B | `sleep 5` | exit 0 | — |\n| V4 | GREEN | `python3 -c 'print(1)'` | exit 0 | — |",
            )
            text = text.replace(
                "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n| V4 | TIER-B | `mypy tool.py` | exit 0 | — |",
                "| V5 | TIER-B | `ruff check tool.py` | exit 0 | — |\n| V6 | TIER-B | `mypy tool.py` | exit 0 | — |",
            )
            text = text.replace(
                "| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |",
                "| V7 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |",
            )
            return text

        self.update_task_both("task_1.md", modify_task_1)

        # 2. Update task_2 with a GREEN row whose command names a path marked (new)
        def modify_task_2(text: str) -> str:
            text = text.replace(
                "Allowed files:\n- `tool.py`",
                "Allowed files:\n- `tool.py`\n- `new_file.py` (new)",
            )
            text = text.replace(
                "| V2 | GREEN | `python3 tool.py green2` | exit 0 | — |",
                "| V2 | GREEN | `python3 new_file.py` | exit 0 | — |",
            )
            return text

        self.update_task_both("task_2.md", modify_task_2)

        # Commit these task files so the tree is clean for baseline run
        git_cmd(self.root, "add", "-A")
        git_cmd(self.root, "commit", "-m", "commit tasks for baseline", "-q")

        code, stdout, _stderr = self.run_check("demo_epic", "--baseline", "--row-timeout", "2")
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nStdout:\n{stdout}")
        r8_warns = [line for line in stdout.splitlines() if line.startswith("R8 WARN")]
        self.assertTrue(any("task_1:V2" in line for line in r8_warns), f"Expected task_1:V2 in R8 WARN:\n{stdout}")
        self.assertTrue(
            any("task_1:V3" in line and "timeout" in line for line in r8_warns),
            f"Expected task_1:V3 timeout in R8 WARN:\n{stdout}",
        )
        self.assertFalse(any("task_1:V4" in line for line in r8_warns), f"task_1:V4 should pass:\n{stdout}")
        self.assertFalse(any("task_2" in line for line in r8_warns), f"task_2 should be skipped:\n{stdout}")

        # When dirty tree:
        (self.root / "README.md").write_text("# Dirty\n", encoding="utf-8")
        code_dirty, stdout_dirty, _stderr_dirty = self.run_check("demo_epic", "--baseline", "--row-timeout", "2")
        self.assertEqual(code_dirty, 0, f"Expected 0 for dirty tree, got {code_dirty}.\nStdout:\n{stdout_dirty}")
        self.assertTrue(
            any("R8 WARN baseline skipped: dirty tree" in line for line in stdout_dirty.splitlines()),
            f"Expected 'R8 WARN baseline skipped: dirty tree', got:\n{stdout_dirty}",
        )


if __name__ == "__main__":
    unittest.main()

