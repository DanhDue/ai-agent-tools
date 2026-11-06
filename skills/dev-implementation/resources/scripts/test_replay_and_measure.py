"""Tests for task text replay engine, static anchor verification, and MEASURE phase."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import check_epic_readiness
import replay_task_text
import run_task_checks
import task_contract


def _setup_git_repo(root: Path) -> None:
    subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Tester"], check=True)


def test_EVI_HP_04_replay_and_measure_phase(tmp_path: Path) -> None:
    """[EVI-HP-04] [Tier C - Integration] Task text replay engine applies fenced directives and MEASURE phase executes."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_git_repo(repo)

    src_dir = repo / "src"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").write_text("def compute():\n    return 10\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "src/main.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init", "-q"], check=True)

    epic_dir = repo / ".devtool" / "epic" / "sample_epic"
    epic_dir.mkdir(parents=True)
    features_dir = repo / ".devtool" / "features"
    features_dir.mkdir(parents=True)

    task_content = """---
id: "task_01_sample"
status: "in-progress"
priority: "high"
assignee: null
epic: "sample-epic"
dueDate: null
created: "2026-11-06T00:00:00Z"
modified: "2026-11-06T00:00:00Z"
completedAt: null
labels: ["sample"]
order: "b1"
---

# Task 01: Sample

## Files

Allowed files:
- `src/main.py`
- `tests/test_compute.py` (new)

Evidence files:
- `.devtool/epic/sample_epic/evidence/bench.json`

## Changes

Create tests/test_compute.py:
```python
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from src.main import compute

def test_compute():
    assert compute() == 42
```

Replace in src/main.py:
```python
    return 10
```
With:
```python
    return 42
```

Insert in src/main.py (after):
```python
    return 42
```
With:
```python


def extra():
    return True
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_compute.py` | exit 1; contains "FAILED" | — |
| V2 | MEASURE | `python3 -c "import pathlib, json; p = pathlib.Path('.devtool/epic/sample_epic/evidence/bench.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'score': 100}))"` | exit 0 | — |
| V3 | GREEN | `python3 -m pytest tests/test_compute.py` | exit 0; contains "passed" | — |

## Definition of Done

- Done (V3)
"""
    task_file = epic_dir / "task_01_sample.md"
    task_file.write_text(task_content, encoding="utf-8")
    (features_dir / "task_01_sample.md").write_text(task_content, encoding="utf-8")

    # 1. Test replay_task engine
    code, msgs = replay_task_text.replay_task(repo, task_file, task_content, run_rows=True, timeout=60)
    assert code == 0, f"replay_task failed: {msgs}"
    assert (repo / "tests" / "test_compute.py").is_file()
    assert "extra()" in (repo / "src" / "main.py").read_text(encoding="utf-8")

    # 2. Test run_task_checks.py measure
    args = argparse.Namespace(
        mode="measure",
        task=task_file,
        timeout=60,
        resume=False,
    )
    measure_code = run_task_checks.run(args)
    assert measure_code == 0

    evidence_file = epic_dir / "evidence" / "task_01_sample.json"
    assert evidence_file.is_file()
    ev_data = json.loads(evidence_file.read_text(encoding="utf-8"))
    assert "measure" in ev_data["runs"]
    m_run = ev_data["runs"]["measure"]
    assert m_run["passed"] is True
    assert ".devtool/epic/sample_epic/evidence/bench.json" in m_run.get("evidence_digests", {})


def test_EVI_ST_02_measure_resume_and_invalidation(tmp_path: Path) -> None:
    """[EVI-ST-02] [Tier C - Integration] run_task_checks.py measure --resume reuses cached MEASURE runs only when tree and digests match."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_git_repo(repo)

    epic_dir = repo / ".devtool" / "epic" / "sample_epic"
    epic_dir.mkdir(parents=True)
    features_dir = repo / ".devtool" / "features"
    features_dir.mkdir(parents=True)

    task_content = """---
id: "task_01_bench"
status: "in-progress"
priority: "high"
assignee: null
epic: "sample-epic"
dueDate: null
created: "2026-11-06T00:00:00Z"
modified: "2026-11-06T00:00:00Z"
completedAt: null
labels: ["sample"]
order: "b1"
---

# Task 01: Bench

## Files

Allowed files:
- `app.py` (new)

Evidence files:
- `.devtool/epic/sample_epic/evidence/bench.json`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | MEASURE | `python3 -c "import pathlib, json; p = pathlib.Path('.devtool/epic/sample_epic/evidence/bench.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'score': 42}))"` | exit 0 | — |

## Definition of Done

- Done (V1)
"""
    task_file = epic_dir / "task_01_bench.md"
    task_file.write_text(task_content, encoding="utf-8")
    (features_dir / "task_01_bench.md").write_text(task_content, encoding="utf-8")

    (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "app.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init app", "-q"], check=True)

    # Initial run
    args = argparse.Namespace(mode="measure", task=task_file, timeout=60, resume=False)
    assert run_task_checks.run(args) == 0

    # Resume without modification -> cached PASS (assert row execution was skipped)
    args_resume = argparse.Namespace(mode="measure", task=task_file, timeout=60, resume=True)
    with mock.patch("run_task_checks.run_command") as mock_run_cmd:
        assert run_task_checks.run(args_resume) == 0
        mock_run_cmd.assert_not_called()

    # Invalidate by altering evidence file content
    bench_file = epic_dir / "evidence" / "bench.json"
    bench_file.write_text(json.dumps({"score": 999}), encoding="utf-8")

    # Resume detects digest mismatch -> re-executes MEASURE
    assert run_task_checks.run(args_resume) == 0
    # Verified it re-wrote the original score 42
    assert json.loads(bench_file.read_text(encoding="utf-8")) == {"score": 42}


def test_EVI_FR_02_anchor_verification_missing_or_ambiguous(tmp_path: Path) -> None:
    """[EVI-FR-02] [Tier A - Unit] R5 static anchor verification fails when an anchor is missing or ambiguous."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_git_repo(repo)

    lib_file = repo / "lib.py"
    lib_file.write_text("item = 1\nitem = 1\nother = 2\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "lib.py"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init lib", "-q"], check=True)

    task_ambiguous = """---
id: "task_01"
status: "todo"
---
# Task 01
Replace in lib.py:
```python
item = 1
```
With:
```python
item = 10
```
"""
    task_path = repo / "task_01.md"
    errors = replay_task_text.verify_task_edit_anchors(repo, task_path, task_ambiguous)
    assert len(errors) == 1
    assert "ambiguous edit anchor (2 matches) in lib.py" in errors[0]

    task_missing = """---
id: "task_02"
status: "todo"
---
# Task 02
Insert in lib.py (after):
```python
nonexistent = 999
```
With:
```python
extra = True
```
"""
    task_path_2 = repo / "task_02.md"
    errors_2 = replay_task_text.verify_task_edit_anchors(repo, task_path_2, task_missing)
    assert len(errors_2) == 1
    assert "missing edit anchor in lib.py" in errors_2[0]


def test_EVI_FR_03_evaluate_done_gate_measure_enforcement(tmp_path: Path) -> None:
    """[EVI-FR-03] [Tier A - Unit] evaluate_done_gate fails when MEASURE rows are missing, failed, or stale."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _setup_git_repo(repo)

    epic_dir = repo / ".devtool" / "epic" / "demo"
    epic_dir.mkdir(parents=True)
    features_dir = repo / ".devtool" / "features"
    features_dir.mkdir(parents=True)

    task_content = """---
id: "task_01"
status: "in-progress"
priority: "high"
assignee: null
epic: "demo"
dueDate: null
created: "2026-11-06T00:00:00Z"
modified: "2026-11-06T00:00:00Z"
completedAt: null
labels: ["sample"]
order: "b1"
---

# Task 01

## Files

Allowed files:
- `dummy.txt` (new)

Evidence files:
- `.devtool/epic/demo/evidence/bench.json`

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | MEASURE | `python3 -c "import pathlib, json; p = pathlib.Path('.devtool/epic/demo/evidence/bench.json'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({'ok': True}))"` | exit 0 | — |
| V2 | GREEN | `true` | exit 0 | — |

## Definition of Done

- Done (V2)
"""
    task_file = epic_dir / "task_01.md"
    task_file.write_text(task_content, encoding="utf-8")
    (features_dir / "task_01.md").write_text(task_content, encoding="utf-8")

    (repo / "dummy.txt").write_text("ok\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "dummy.txt"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-m", "init dummy", "-q"], check=True)

    # 1. No evidence file -> fails condition 1
    failures = task_contract.evaluate_done_gate(task_file)
    assert any("condition 1" in f for f in failures)

    # 2. Run verify only (missing measure run) -> fails condition 1 for measure
    evidence_path = epic_dir / "evidence" / "task_01.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    tree, patch_id = task_contract.fingerprint(repo)
    head = "HEAD"
    ev_data = {
        "schema": 1,
        "task": "task_01",
        "runs": {
            "verify": {
                "head": head,
                "tree": tree,
                "patch_id": patch_id,
                "started": "2026-11-06T00:00:00Z",
                "finished": "2026-11-06T00:00:01Z",
                "rows": [
                    {"id": "V2", "phase": "GREEN", "command": "true", "expect": "exit 0", "outcome": "PASS"},
                    {"id": "SCOPE", "phase": "SCOPE", "command": "scope", "expect": "scope", "outcome": "PASS"},
                ],
            }
        },
    }
    evidence_path.write_text(json.dumps(ev_data), encoding="utf-8")
    failures_2 = task_contract.evaluate_done_gate(task_file)
    assert any("has no measure run" in f for f in failures_2)

    # 3. Measure run passed=False
    ev_data["runs"]["measure"] = {
        "head": head,
        "tree": tree,
        "patch_id": patch_id,
        "started": "2026-11-06T00:00:00Z",
        "finished": "2026-11-06T00:00:01Z",
        "passed": False,
        "rows": [{"id": "V1", "phase": "MEASURE", "command": "python3 -c ...", "expect": "exit 0", "outcome": "FAIL"}],
    }
    evidence_path.write_text(json.dumps(ev_data), encoding="utf-8")
    failures_3 = task_contract.evaluate_done_gate(task_file)
    assert any("measure run did not pass" in f for f in failures_3)

    # 4. Evidence file digest mismatch
    bench_file = epic_dir / "evidence" / "bench.json"
    bench_file.write_text(json.dumps({"ok": True}), encoding="utf-8")
    ev_data["runs"]["measure"]["passed"] = True
    ev_data["runs"]["measure"]["rows"][0]["outcome"] = "PASS"
    ev_data["runs"]["measure"]["rows"][0]["command"] = 'python3 -c "import pathlib, json; p = pathlib.Path(\'.devtool/epic/demo/evidence/bench.json\'); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps({\'ok\': True}))"'
    ev_data["runs"]["measure"]["evidence_digests"] = {
        ".devtool/epic/demo/evidence/bench.json": "mismatched_sha256_hash",
    }
    evidence_path.write_text(json.dumps(ev_data), encoding="utf-8")
    failures_4 = task_contract.evaluate_done_gate(task_file)
    assert any("digest does not match measure run" in f for f in failures_4)


def test_directive_file_aliases() -> None:
    """Verify parse_task_directives parses 'File: <path>' and '<!-- @@FILE:...@@ -->' aliases."""
    from replay_task_text import parse_task_directives

    task_prose = (
        "Some description\n\n"
        "File: src/first.py:\n"
        "```python\n"
        "a = 1\n"
        "```\n\n"
        "<!-- @@FILE:src/second.py@@ -->\n"
        "```python\n"
        "b = 2\n"
        "```\n"
    )
    directives = parse_task_directives(task_prose)
    assert len(directives) == 2
    assert directives[0].path == "src/first.py"
    assert directives[0].content == "a = 1\n"
    assert directives[1].path == "src/second.py"
    assert directives[1].content == "b = 2\n"


class Test_Replay_And_Measure_Integration:
    def test_EVI_HP_04_integration_runner(self, tmp_path: Path) -> None:
        """[EVI-HP-04] [Tier C - Integration] Task text replay engine integration runner."""
        test_EVI_HP_04_replay_and_measure_phase(tmp_path)

    def test_EVI_ST_02_integration_runner(self, tmp_path: Path) -> None:
        """[EVI-ST-02] [Tier C - Integration] MEASURE resume integration runner."""
        test_EVI_ST_02_measure_resume_and_invalidation(tmp_path)
