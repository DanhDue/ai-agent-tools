#!/usr/bin/env python3
"""Tests for audit_epic.py, on epic branches built in throwaway repositories.

Evidence is recorded by the real recorder, so the patch ids the audit compares are the real ones.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
import run_task_checks
from audit_epic import main, status_of

EPIC = ".devtool/epic/demo"
TABLE_HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
TICKS = "`" * 3
SECTIONS = ("Evidence", "Legacy tasks", "Protected paths", "Grader amendments", "Commits outside tasks",
            "Gate 5 items")


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout


def scenarios_text(*ids: str) -> str:
    blocks = "".join(f"Scenario: [{i}] [Tier C - Integration] Demo\n  Given a demo\n" for i in ids)
    return f"# Scenarios\n\n{TICKS}gherkin\n{blocks}{TICKS}\n"


def mirror_text(n: int, status: str, verification: bool = True, gate5: bool = False) -> str:
    text = (f'---\nid: "task_{n}_demo"\nstatus: "{status}"\n---\n\n# Task {n}\n\n'
            f"## Files\n\nAllowed files:\n- `feature_{n}.txt` (new)\n\n")
    if verification:
        text += f"## Verification\n\n{TABLE_HEAD}| V1 | GREEN | `true` | exit 0 | — |\n\n"
    text += "## Definition of Done\n\n- the demo works (V1)\n"
    if gate5:
        text += "- the wording reads well (Gate 5)\n"
    return text + "\n## BDD Scenarios\n\nCovers: DEMO-HP-01\n"


class AuditCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "demo@example.com")
        git(self.root, "config", "user.name", "Demo")
        self.write("README.md", "demo\n")
        self.write("scripts/verify.sh", "echo verify\n")
        self.write(f"{EPIC}/demo.en.md",
                   "# Epic\n\nProtected paths: scripts/verify.sh, "
                   f"{EPIC}/bdd_scenarios.en.md\n")
        self.write(f"{EPIC}/bdd_scenarios.en.md", scenarios_text("DEMO-HP-01"))
        self.commit("base")
        git(self.root, "checkout", "-q", "-b", "epic")
        previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, title: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", title)

    def mirror(self, n: int) -> str:
        return f"{EPIC}/task_{n}_demo.md"

    def start_task(self, n: int, **options: Any) -> None:
        self.write(self.mirror(n), mirror_text(n, "in-progress", **options))
        self.commit(f"[DEMO] Create task {n}")

    def mark_done(self, n: int) -> None:
        path = self.root / self.mirror(n)
        path.write_text(path.read_text(encoding="utf-8").replace('"in-progress"', '"done"'), encoding="utf-8")

    def finish_task(self, n: int, record: bool = True) -> None:
        self.write(f"feature_{n}.txt", f"feature {n}\n")
        if record:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(run_task_checks.main(["verify", str(self.root / self.mirror(n))]), 0)
        self.mark_done(n)
        self.commit(f"[DEMO] Task {n}")

    def audit(self, base: str = "main") -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--epic-dir", "demo", "--base", base])
        return code, out.getvalue(), err.getvalue()

    def section(self, report: str, name: str) -> str:
        return report.split(f"### {name}\n", 1)[1].split("###", 1)[0].split("Result:", 1)[0]


class AuditEpicTest(AuditCase):
    def test_vth_hp_05_a_clean_epic_passes_the_audit(self) -> None:
        for n in (1, 2):
            self.start_task(n)
            self.finish_task(n)
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertIn("Result: PASS", report)
        self.assertEqual([name for name in SECTIONS if f"### {name}\n" not in report], [])
        self.assertIn("task_1_demo: PASS", self.section(report, "Evidence"))
        self.assertIn("task_2_demo: PASS", self.section(report, "Evidence"))
        self.assertNotIn("patch changed", report)
        self.assertNotIn("unauthorised", report)
        for name in SECTIONS[1:]:
            self.assertEqual(self.section(report, name).strip(), "None", name)

    def test_vth_hp_10_disclosures_are_listed_without_failing_the_audit(self) -> None:
        self.start_task(1, gate5=True)
        self.finish_task(1)
        path = self.root / self.mirror(1)
        path.write_text(path.read_text(encoding="utf-8").replace("`true`", "`echo changed`"), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):  # the amended row is re-verified, so the evidence matches
            self.assertEqual(run_task_checks.main(["verify", str(path)]), 0)
        self.commit("Loosen V1 check")
        self.write("extra.txt", "extra\n")
        self.commit("Fix integration with develop")
        self.start_task(2, verification=False)
        self.finish_task(2, record=False)
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertIn("Loosen V1 check", self.section(report, "Grader amendments"))
        self.assertIn("-| V1 | GREEN | `true`", self.section(report, "Grader amendments"))
        self.assertIn("Fix integration with develop", self.section(report, "Commits outside tasks"))
        self.assertIn("task_1_demo: the wording reads well (Gate 5)", self.section(report, "Gate 5 items"))
        self.assertIn("task_2_demo: legacy — no evidence", self.section(report, "Legacy tasks"))

    def test_vth_st_08_a_done_status_written_by_hand_fails_the_audit(self) -> None:
        self.start_task(1)
        self.mark_done(1)
        self.commit("Mark done by hand")
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        self.assertIn("task_1_demo: missing evidence", self.section(report, "Evidence"))
        self.assertIn("Result: FAIL", report)

    def test_status_is_read_whatever_its_quoting(self) -> None:
        for line in ("status: done", 'status: "done"', "status: 'done'", "status: done  # by hand"):
            with self.subTest(line=line):
                self.assertEqual(status_of(f"---\nid: t\n{line}\n---\n"), "done")

    def test_done_written_by_hand_only_in_the_features_copy_fails_the_audit(self) -> None:
        for folder in ("", "done/"):
            with self.subTest(folder=folder):
                self.start_task(1)
                self.write(f".devtool/features/{folder}task_1_demo.md",
                           "---\nid: task_1_demo\nstatus: 'done'\n---\n\n# Task 1\n")
                self.commit("Mark done by hand in the features copy")
                code, report, _ = self.audit()
                self.assertEqual(code, 1, report)
                self.assertIn("task_1_demo: missing evidence", self.section(report, "Evidence"))
                git(self.root, "reset", "-q", "--hard", "main")

    def test_a_gate_5_item_ending_with_a_period_is_listed(self) -> None:
        self.write(self.mirror(1), mirror_text(1, "in-progress", gate5=True).replace("(Gate 5)", "(Gate 5)."))
        self.commit("[DEMO] Create task 1")
        self.finish_task(1)
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertIn("task_1_demo: the wording reads well (Gate 5).", self.section(report, "Gate 5 items"))

    def test_hld_grader_line_changes_are_disclosed_without_failing(self) -> None:
        self.start_task(1)
        self.finish_task(1)
        self.write(f"{EPIC}/demo.en.md", f"# Epic\n\nProtected paths: {EPIC}/bdd_scenarios.en.md\n"
                                         "Integration results: true -> build/r.xml\n")
        self.commit("Loosen the HLD")
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        amendments = self.section(report, "Grader amendments")
        self.assertIn(f"-Protected paths: scripts/verify.sh, {EPIC}/bdd_scenarios.en.md", amendments)
        self.assertIn(f"+Protected paths: {EPIC}/bdd_scenarios.en.md", amendments)
        self.assertIn("+Integration results: true -> build/r.xml", amendments)
        self.assertIn("Loosen the HLD", amendments)

    def test_a_row_that_is_not_pass_fails_the_audit(self) -> None:
        self.start_task(1)
        self.finish_task(1)
        evidence = self.root / f"{EPIC}/evidence/task_1_demo.json"
        evidence.write_text(evidence.read_text(encoding="utf-8").replace('"outcome": "PASS"',
                                                                         '"outcome": "FAIL"', 1), encoding="utf-8")
        self.commit("Tamper with evidence")
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        self.assertIn("task_1_demo: row V1 not PASS", report)

    def tamper(self, edit: Callable[[str], str]) -> None:
        self.start_task(1)
        self.finish_task(1)
        path = self.root / f"{EPIC}/evidence/task_1_demo.json"
        path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")
        self.commit("Hand-edit evidence")

    def test_evidence_omitting_a_table_row_fails_the_audit(self) -> None:
        def drop_v1(text: str) -> str:
            data = json.loads(text)
            data["runs"]["verify"]["rows"] = [r for r in data["runs"]["verify"]["rows"] if r["id"] != "V1"]
            return json.dumps(data)
        self.tamper(drop_v1)
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        self.assertIn("row V1", report)

    def test_evidence_with_no_rows_fails_the_audit(self) -> None:
        self.tamper(lambda text: json.dumps({"runs": {"verify": {"rows": []}}}))
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        self.assertIn("row V1", report)

    def test_malformed_evidence_fails_without_a_traceback(self) -> None:
        def make_bad(b: str) -> Callable[[str], str]:
            return lambda _: b

        for bad in ("[]", '{"runs": {"verify": {}}}', '{"runs": {"verify": {"rows": [{"id": "V1"}]}}}', "{"):
            with self.subTest(bad=bad):
                self.tamper(make_bad(bad))
                code, report, _ = self.audit()
                self.assertEqual(code, 1, report)
                self.assertIn("task_1_demo: malformed evidence", report)
                git(self.root, "reset", "-q", "--hard", "HEAD~1")

    def test_vth_st_09_protected_changes_outside_tasks_fail_outside_devtool_and_are_disclosed_inside(self) -> None:
        self.start_task(1)
        self.finish_task(1)
        self.write("scripts/verify.sh", "echo changed\n")
        self.commit("Fix integration with develop")
        self.write(f"{EPIC}/bdd_scenarios.en.md", scenarios_text("DEMO-HP-01", "DEMO-HP-02"))
        self.commit("Sync scenarios")
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        protected = self.section(report, "Protected paths")
        self.assertRegex(protected, r"scripts/verify\.sh.*unauthorised")
        self.assertIn(f"{EPIC}/bdd_scenarios.en.md", protected)
        self.assertNotRegex(protected, rf"{EPIC}/bdd_scenarios\.en\.md.*unauthorised")
        self.assertIn("DEMO-HP-02 added", self.section(report, "Grader amendments"))

    def test_vth_ar_01_a_moved_base_branch_changes_trees_but_not_the_verdict(self) -> None:
        for n in (1, 2):
            self.start_task(n)
            self.finish_task(n)
        git(self.root, "checkout", "-q", "main")
        self.write("other.txt", "base moved\n")
        self.commit("Base moves")
        git(self.root, "checkout", "-q", "epic")
        git(self.root, "rebase", "-q", "main")
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertNotIn("patch changed", report)
        self.write("feature_2.txt", "feature 2, resolved differently\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "--amend", "--no-edit")
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertIn("task_2_demo: patch changed after verify", report)
        self.assertNotIn("task_1_demo: patch changed", report)

    def test_vth_fr_03_an_unknown_base_reference_is_a_usage_error(self) -> None:
        code, report, error = self.audit("no-such-ref")
        self.assertEqual(code, 2)
        self.assertIn("no-such-ref", error)
        self.assertEqual(report, "")

    def test_mvls_hp_02_audit_genuine_pytest_red_evidence(self) -> None:
        """[MVLS-HP-02] Committed genuine pytest RED evidence passes semantic recomputation."""
        self.write(self.mirror(1),
                   mirror_text(1, "in-progress").replace(
                       "| V1 | GREEN | `true` | exit 0 | — |\n\n",
                       "| V1 | RED | `pytest tests/test_a.py::test_foo` | exit 1 | — |\n"
                       "| V2 | GREEN | `true` | exit 0 | — |\n\n"
                   ).replace("- the demo works (V1)\n", "- the demo works (V2)\n"))
        self.commit("[DEMO] Task 1 with pytest RED")
        self.write("feature_1.txt", "feature 1\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_task_checks.main(["verify", str(self.root / self.mirror(1))]), 0)
        evidence_path = self.root / f"{EPIC}/evidence/task_1_demo.json"
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
        data["runs"]["red"] = {
            "head": git(self.root, "rev-parse", "HEAD").strip(),
            "tree": "some-tree",
            "rows": [{
                "id": "V1",
                "phase": "RED",
                "command": "pytest tests/test_a.py::test_foo",
                "expect": "exit 1",
                "needs": [],
                "exit": 1,
                "outcome": "PASS",
                "reason": None,
                "output_tail": [
                    "FAILED tests/test_a.py::test_foo - AssertionError: expected False",
                    "=== 1 failed in 0.05s ==="
                ]
            }]
        }
        evidence_path.write_text(json.dumps(data), encoding="utf-8")
        self.mark_done(1)
        self.commit("[DEMO] Task 1 done with valid pytest RED")
        code, report, _ = self.audit()
        self.assertEqual(code, 0, report)
        self.assertIn("task_1_demo: PASS", report)
        self.assertNotIn("invalid-pytest-RED", report)

    def test_mvls_st_02_tampered_pytest_red_evidence_fails_gate_4(self) -> None:
        """[MVLS-ST-02] Invalid pytest RED evidence marked outcome PASS fails Gate 4 semantic audit."""
        self.write(self.mirror(1),
                   mirror_text(1, "in-progress").replace(
                       "| V1 | GREEN | `true` | exit 0 | — |\n\n",
                       "| V1 | RED | `pytest tests/test_a.py::test_foo` | exit 1 | — |\n"
                       "| V2 | GREEN | `true` | exit 0 | — |\n\n"
                   ).replace("- the demo works (V1)\n", "- the demo works (V2)\n"))
        self.commit("[DEMO] Task 1 with pytest RED")
        self.write("feature_1.txt", "feature 1\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_task_checks.main(["verify", str(self.root / self.mirror(1))]), 0)
        evidence_path = self.root / f"{EPIC}/evidence/task_1_demo.json"
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
        data["runs"]["red"] = {
            "head": git(self.root, "rev-parse", "HEAD").strip(),
            "tree": "some-tree",
            "rows": [{
                "id": "V1",
                "phase": "RED",
                "command": "pytest tests/test_a.py::test_foo",
                "expect": "exit 1",
                "needs": [],
                "exit": 4,
                "outcome": "PASS",
                "reason": None,
                "output_tail": [
                    "ERROR: file or directory not found: tests/test_a.py::test_foo"
                ]
            }]
        }
        evidence_path.write_text(json.dumps(data), encoding="utf-8")
        self.mark_done(1)
        self.commit("[DEMO] Task 1 done with tampered pytest RED")
        code, report, _ = self.audit()
        self.assertEqual(code, 1, report)
        evidence_sec = self.section(report, "Evidence")
        self.assertIn("task_1_demo: row V1 Invalid pytest RED phase", evidence_sec)
        self.assertIn("Result: FAIL", report)

    def test_mvls_ar_02_multi_task_audit_is_deterministic(self) -> None:
        """[MVLS-AR-02] Multi-task audit associates findings to correct tasks with FAIL precedence."""
        self.write(self.mirror(1), mirror_text(1, "in-progress"))
        self.commit("[DEMO] Task 1 start")
        self.finish_task(1)

        self.write(self.mirror(2),
                   mirror_text(2, "in-progress").replace(
                       "| V1 | GREEN | `true` | exit 0 | — |\n\n",
                       "| V1 | RED | `pytest tests/test_b.py::test_bar` | exit 1 | — |\n"
                       "| V2 | GREEN | `true` | exit 0 | — |\n\n"
                   ).replace("- the demo works (V1)\n", "- the demo works (V2)\n"))
        self.commit("[DEMO] Task 2 start")
        self.write("feature_2.txt", "feature 2\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(run_task_checks.main(["verify", str(self.root / self.mirror(2))]), 0)
        evidence_path = self.root / f"{EPIC}/evidence/task_2_demo.json"
        data = json.loads(evidence_path.read_text(encoding="utf-8"))
        data["runs"]["red"] = {
            "head": git(self.root, "rev-parse", "HEAD").strip(),
            "tree": "some-tree",
            "rows": [{
                "id": "V1",
                "phase": "RED",
                "command": "pytest tests/test_b.py::test_bar",
                "expect": "exit 1",
                "needs": [],
                "exit": 5,
                "outcome": "PASS",
                "reason": None,
                "output_tail": [
                    "collected 0 items"
                ]
            }]
        }
        evidence_path.write_text(json.dumps(data), encoding="utf-8")
        self.mark_done(2)
        self.commit("[DEMO] Task 2 done with tampered evidence")

        for _ in range(2):
            code, report, _ = self.audit()
            self.assertEqual(code, 1, report)
            evidence_sec = self.section(report, "Evidence")
            self.assertIn("task_1_demo: PASS", evidence_sec)
            self.assertIn("task_2_demo: row V1 Invalid pytest RED phase", evidence_sec)
            self.assertIn("Result: FAIL", report)


if __name__ == "__main__":
    unittest.main()
