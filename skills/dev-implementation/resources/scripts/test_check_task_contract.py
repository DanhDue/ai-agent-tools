#!/usr/bin/env python3
"""Tests for check_task_contract.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py
"""
from __future__ import annotations
import contextlib
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from check_task_contract import main

EPIC = ".devtool/epic/demo"
HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
RED = "| V1 | RED | `python3 tool.py red` | exit 1 | — |\n"
GREEN = "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |\n"
TIER_B = ("| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
          "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n")
TIER_C = "| V5 | TIER-C | `python3 tool.py int --out=build/out.xml` | exit 0; results build/out.xml | — |\n"
DEFAULT_ROWS = RED + GREEN + TIER_B + TIER_C
VERIFICATION_ENV = "## 6. Verification Environment\n\nTests run in temporary directories. Variable: DEMO_TOKEN.\n"
HLD = ("# Epic\n\n## Integration Test Plan\n\nProtected paths: scripts/verify.sh\n\n"
       "Integration results: python3 tool.py all -> build/all.xml\n\n" + VERIFICATION_ENV)
DONE_LINE = "- done (V1)\n"


def task_text(rows: str = DEFAULT_ROWS, allowed: str = "- `tool.py`", dod: str | None = None,
              covers: str = "", status: str = "todo", read_only: str = "- `README.md` — note",
              after_table: str = "", skip: str = "", decisions: str = "- Grounded design decision.\n",
              evidence: str = "") -> str:
    if dod is None:
        row_ids = [m.group(1) for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*[^|]+\s*\|", rows, re.MULTILINE)
                   if m.group(1) not in ("ID", "") and not m.group(1).startswith("-")]
        non_v1 = [r for r in row_ids if r != "V1"]
        dod = f"- done ({', '.join(non_v1)})\n" if non_v1 else "- done (Gate 5)\n"
    ev_part = f"\nEvidence files:\n{evidence}\n" if evidence else ""
    sections = {
        "Files": f"Allowed files:\n{allowed}\n{ev_part}\nRead-only context:\n{read_only}\n",
        "Verification": f"{HEAD}{rows}\n{after_table}",
        "Definition of Done": dod,
        "Stop and Report If": "- A command does not match.\n",
        "Decisions Already Made": decisions,
    }
    body = "".join(f"## {title}\n\n{text}\n" for title, text in sections.items() if title != skip)
    return f'---\nstatus: "{status}"\n---\n# Task\n\n{covers}\n{body}'


def git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)


class ContractCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "demo@example.com")
        git(self.root, "config", "user.name", "Demo")
        self.write(".gitignore", "build/\n")
        self.write("tool.py", "print('x')\n")
        self.write("README.md", "demo\n")
        self.write(f"{EPIC}/demo.en.md", HLD)
        self.previous = Path.cwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.previous)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")

    def task(self, name: str, **kwargs: Any) -> Path:
        return self.write(f"{EPIC}/task_{name}.md", task_text(**kwargs))

    def run_cli(self, *argv: str | Path) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main([str(arg) for arg in argv])
            except SystemExit as exit_:
                code = int(exit_.code) if exit_.code is not None else 0
        return code, out.getvalue(), err.getvalue()

    def check(self, *tasks: Path, design: bool = False) -> tuple[int, str, str]:
        self.commit()
        flags = ["--design"] if design else []
        return self.run_cli(*flags, "--hld", f"{EPIC}/demo.en.md", "--tasks", *tasks)


class CompliantEpicTest(ContractCase):
    def test_vth_hp_01_a_compliant_epic_passes_and_prints_implicit_protected_paths(self) -> None:
        first = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
        second = self.task("2_b", allowed="- `README.md`", covers="Covers: DEMO-HP-01",
                           rows=RED + GREEN + TIER_B + TIER_C.replace("tool.py int", "tool.py src/made.py"))
        code, out, _ = self.check(first, second, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Implicit protected paths: tool.py", out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_no_tracked_program_prints_none(self) -> None:
        task = self.task("1_a", allowed="- `README.md`",
                         rows=RED.replace("python3 tool.py red", "echo red") + GREEN.replace(
            "python3 tool.py green", "echo green") + TIER_C.replace("python3 tool.py", "echo"))
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)
        self.assertIn("Implicit protected paths: none", out)

    def test_wrapped_dod_bullet_and_trailing_period_pass(self) -> None:
        task = self.task("1_a", dod="- done and\n  wrapped (V1, V2).\n- by hand (Gate 5)\n")
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)

    def test_missing_executable_warns_without_failing(self) -> None:
        task = self.task("1_a", rows=RED + GREEN.replace("python3 tool.py green", "nosuch-demo-tool run") + TIER_B + TIER_C)
        code, out, err = self.check(task)
        self.assertEqual(code, 0, out)
        self.assertIn("task_1_a:V2", err)
        self.assertIn("nosuch-demo-tool", err)


class GroundingTest(ContractCase):
    def broken_task(self, status: str = "todo") -> Path:
        self.write("loose.py", "x = 1\n")
        return self.task(
            "1_a", status=status, allowed="- `loose.py`\n- `README.md` (new)\n- `docs/*.md`\n- `src/`\n"
                                          "- `deep/er/est/x.py` (new)",
            read_only="- `docs/nope.md` — gone",
            dod="- done (V2, V5)\n",
            rows=RED + GREEN.replace("tool.py green", "tool.py src/nowhere.py --out=src/also_gone.txt") + TIER_C)

    def test_vth_ec_01_paths_that_do_not_match_the_repository_are_named(self) -> None:
        self.commit()
        task = self.broken_task()
        code, out, _ = self.run_cli("--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", task)
        self.assertEqual(code, 1)
        for expected in ("task_1_a:Files: loose.py is not tracked by git",
                         "task_1_a:Files: README.md is marked (new) but already exists",
                         "task_1_a:Files: docs/*.md matches no tracked file",
                         "task_1_a:Files: src/ is a directory; list files or a glob",
                         "task_1_a:Files: deep/er/est/x.py (new) has no parent or grandparent directory",
                         "task_1_a:Files: Read-only context docs/nope.md does not exist",
                         "task_1_a:V2: src/nowhere.py does not exist, is not ignored by git and is not (new) in any task",
                         "task_1_a:V2: src/also_gone.txt does not exist"):
            self.assertIn(expected, out)

    def test_vth_ec_01_without_design_a_done_task_is_not_grounded_and_new_is_not_checked(self) -> None:
        done = self.broken_task(status="done")
        self.commit()
        code, out, _ = self.run_cli("--hld", f"{EPIC}/demo.en.md", "--tasks", done)
        self.assertEqual(code, 0, out)
        live = self.task("2_b", allowed="- `README.md` (new)\n- `tool.py`")
        code, out, _ = self.check(live)
        self.assertEqual(code, 0, out)
        self.assertNotIn("already exists", out)

    def test_read_only_context_may_name_a_path_another_task_creates(self) -> None:
        owner = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
        reader = self.task("2_b", read_only="- `src/made.py` — built by task 1\n- `README.md` — note")
        code, out, _ = self.check(owner, reader)
        self.assertEqual(code, 0, out)

    def test_command_token_is_new_in_another_task(self) -> None:
        owner = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
        user = self.task("2_b", rows=DEFAULT_ROWS.replace("tool.py green", "tool.py src/made.py"))
        code, out, _ = self.check(owner, user, design=True)
        self.assertEqual(code, 0, out)


class StructureTest(ContractCase):
    def test_vth_ec_02_a_definition_of_done_item_with_no_command_is_rejected(self) -> None:
        task = self.task("1_a", dod="- Works for users.\n- Names a missing row (V9)\n- Fine (V2)\n")
        code, out, _ = self.check(task)
        self.assertEqual(code, 1)
        self.assertIn("task_1_a:Definition of Done: Works for users. ends with no (V<n>) or (Gate 5) reference", out)
        self.assertIn("task_1_a:Definition of Done: Names a missing row (V9) references V9, which the table lacks", out)
        self.assertNotIn("Fine", out)

    def test_vth_ec_03_a_malformed_verification_table_is_rejected_row_by_row(self) -> None:
        rows = (RED + "| V1 | GREEN | `python3 tool.py a` | exit 0 | — |\n"
                "| V2 | LATER | `python3 tool.py b` | exit 0 | — |\n"
                "| V3 | GREEN | `python3 tool.py c` | passes | — |\n"
                "| V4 | GREEN | `python3 tool.py d` | exit 0; results build/d.xml | — |\n")
        bad = self.task("1_bad", rows=rows)
        no_red = self.task("2_nored", rows=GREEN + TIER_C)
        no_reason = self.task("3_noreason", rows=GREEN + TIER_C, after_table="RED: n/a —\n")
        uncovered = self.task("4_cov", covers="Covers: DEMO-HP-01", rows=RED + GREEN)
        code, out, _ = self.check(bad, no_red, no_reason, uncovered)
        self.assertEqual(code, 1)
        for expected in ("task_1_bad:V1: duplicate ID",
                         "task_1_bad:V2: Phase must be one of",
                         "task_1_bad:V3: Expect must start with",
                         "task_1_bad:V4: results is allowed only on TIER-C rows",
                         "task_2_nored:Verification: no RED row and no RED: n/a line with a reason",
                         "task_3_noreason:Verification: no RED row and no RED: n/a line with a reason",
                         "task_4_cov:Verification: Covers line but no TIER-C row with results"):
            self.assertIn(expected, out)

    def test_red_n_a_with_a_reason_replaces_the_red_row(self) -> None:
        task = self.task("1_a", rows=GREEN + TIER_B + TIER_C, after_table="RED: n/a — no new behaviour\n")
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)

    def test_missing_sections_header_and_allowed_files_are_named(self) -> None:
        no_sections = self.write(f"{EPIC}/task_1_a.md", "# Task\n\n## Files\n\nAllowed files:\n\n")
        bad_header = self.write(f"{EPIC}/task_2_b.md", task_text().replace("| Needs |", "| Wants |", 1))
        code, out, _ = self.check(no_sections, bad_header)
        self.assertEqual(code, 1)
        for title in ("Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made"):
            self.assertIn(f"task_1_a:{title}: section is missing", out)
        self.assertIn("task_1_a:Files: Allowed files lists no entry", out)
        self.assertIn("task_2_b:Verification: Verification header must be exactly", out)


class DeclarationTest(ContractCase):
    def test_vth_ec_04_missing_hld_declarations_are_rejected(self) -> None:
        self.write(f"{EPIC}/demo.en.md", "# Epic\n\n## 6. Verification Environment\n\n## 7. Next\n")
        task = self.task("1_a", rows=RED + "| V2 | TIER-C | `python3 tool.py x` | exit 0; results out/report.xml |"
                                          " DEMO_TOKEN |\n")
        code, out, _ = self.check(task)
        self.assertEqual(code, 1)
        for expected in ("demo.en.md: no Protected paths: line",
                         "demo.en.md: no Integration results: line",
                         "demo.en.md: ## Verification Environment section is missing or empty",
                         "task_1_a:V2: results path out/report.xml is not ignored by git"):
            self.assertIn(expected, out)

    def test_vth_ec_04_needs_name_and_integration_report_path_are_checked(self) -> None:
        self.write(f"{EPIC}/demo.en.md", HLD.replace("-> build/all.xml", "-> out/all.xml")
                   + "Integration results: no arrow here\n")
        task = self.task("1_a", rows=RED + GREEN + TIER_B + TIER_C.replace("| — |", "| UNNAMED_VAR |"))
        code, out, _ = self.check(task)
        self.assertEqual(code, 1)
        self.assertIn("task_1_a:V5: Needs UNNAMED_VAR is not named in the Verification Environment section", out)
        self.assertIn("demo.en.md: Integration results path out/all.xml is not ignored by git", out)
        self.assertIn("demo.en.md: Integration results line is not <command> -> <path>: no arrow here", out)

    def test_unnumbered_verification_environment_heading_is_accepted(self) -> None:
        self.write(f"{EPIC}/demo.en.md", HLD.replace("## 6. Verification", "## Verification"))
        code, out, _ = self.check(self.task("1_a"))
        self.assertEqual(code, 0, out)


class UsageTest(ContractCase):
    def test_vth_fr_04_an_unreadable_task_exits_2_with_the_reason_on_stderr(self) -> None:
        self.commit()
        code, out, err = self.run_cli("--hld", f"{EPIC}/demo.en.md", "--tasks", f"{EPIC}/task_9_gone.md")
        self.assertEqual(code, 2)
        self.assertIn("task_9_gone.md", err)
        self.assertEqual(out, "")

    def test_vth_fr_04_a_missing_argument_exits_2(self) -> None:
        code, _, err = self.run_cli("--hld", f"{EPIC}/demo.en.md")
        self.assertEqual(code, 2)
        self.assertIn("--tasks", err)

    def test_vth_fr_04_a_directory_outside_any_git_repository_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as outside:
            os.chdir(Path(outside).resolve())
            code, _, err = self.run_cli("--hld", "hld.md", "--tasks", "task.md")
        self.assertEqual(code, 2)
        self.assertIn("git repository", err)


class PythonTierBAndFastModelTest(ContractCase):
    def test_mvls_hp_03_python_task_with_lint_and_type_check_passes(self) -> None:
        """[MVLS-HP-03] Python task with ruff and mypy TIER-B rows passes."""
        task = self.task("1_py", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Use standard tooling.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_mvls_hp_03_registered_provider_commands_accepted(self) -> None:
        """[MVLS-HP-03] Registered python-quality.json lint and type_check commands pass."""
        manifest = json.dumps({
            "schema_version": 1,
            "capabilities": {
                "lint": ["uv", "run", "ruff", "check", "."],
                "type_check": ["uv", "run", "mypy", "--strict", "src"]
            }
        })
        self.write(".agents/quality/python-quality.json", manifest)
        task = self.task("1_py", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `uv run ruff check .` | exit 0 | — |\n"
                              "| V4 | TIER-B | `uv run mypy --strict src` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Use uv runner.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_mvls_ec_03_polyglot_repo_non_python_task_skips_python_tier_b(self) -> None:
        """[MVLS-EC-03] Non-Python task in repo with python quality manifest skips Python TIER-B."""
        manifest = json.dumps({
            "schema_version": 1,
            "capabilities": {
                "lint": ["uv", "run", "ruff", "check", "."],
                "type_check": ["uv", "run", "mypy", "--strict", "src"]
            }
        })
        self.write(".agents/quality/python-quality.json", manifest)
        self.write("app/main.dart", "void main() {}\n")
        self.commit()
        task = self.task("1_dart", allowed="- `app/main.dart`",
                         rows=RED.replace("python3 tool.py red", "dart test red") +
                              GREEN.replace("python3 tool.py green", "dart test green") +
                              TIER_C.replace("python3 tool.py int", "dart test int"),
                         decisions="- Dart task decisions.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertNotIn("Python", out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_mvls_ec_07_rejects_pytest_k_without_node_id(self) -> None:
        """[MVLS-EC-07] Generic pytest -k expression without exact node ID is rejected."""
        self.write("tests/test_a.py", "# test\n")
        self.commit()
        task = self.task("1_k", allowed="- `tool.py`",
                         rows="| V1 | RED | `pytest -k unknown tests/test_a.py` | exit 1 | — |\n" +
                              GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Testing -k rejection.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("pytest -k expression must use an exact node ID", out)

    def test_mvls_ec_07_accepts_pytest_k_with_exact_node_id(self) -> None:
        """[MVLS-EC-07] Pytest -k with exact node ID (path/file.py::test_name) is accepted."""
        self.write("tests/test_a.py", "# test\n")
        self.commit()
        task = self.task("1_k", allowed="- `tool.py`",
                         rows="| V1 | RED | `pytest -k tests/test_a.py::test_feature tests/test_a.py` | exit 1 | — |\n" +
                              GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Exact node ID used.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_mvls_ec_07_rejects_weak_bdd_assertions(self) -> None:
        """[MVLS-EC-07] Weak BDD assertions in scenarios are rejected."""
        self.write(f"{EPIC}/bdd_scenarios.en.md",
                   "# Scenarios\n\nScenario: Demo\n  Then the output should be truthy\n")
        self.commit()
        task = self.task("1_weak", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Weak assertions test.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("weak BDD assertion", out)

    def test_mvls_ec_07_rejects_executable_task_with_empty_or_none_decisions(self) -> None:
        """[MVLS-EC-07] Executable tasks must have grounded Decisions Already Made, not 'None.'."""
        task = self.task("1_none", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="None.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("task_1_none:Decisions Already Made: executable task requires grounded facts, cannot be empty or 'None'", out)

    def test_mvls_ec_07_accepts_executable_task_with_grounded_decisions(self) -> None:
        """[MVLS-EC-07] Executable tasks with non-empty grounded decisions pass."""
        task = self.task("1_grounded", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Grounded facts and architectural choices recorded.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_mvls_fr_03_malformed_python_quality_manifest_fails(self) -> None:
        """[MVLS-FR-03] Malformed python-quality.json reports manifest error and does not silently fall back."""
        self.write(".agents/quality/python-quality.json", "{ malformed json content")
        self.commit()
        task = self.task("1_py", allowed="- `tool.py`",
                         rows=RED + GREEN +
                              "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                              "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
                         dod="- done (V2, V3, V4, V5)\n",
                         decisions="- Testing malformed manifest.\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("python-quality.json", out)

    def test_wqg_st_02_pure_unit_mock_rejected_for_tier_c_scenario(self) -> None:
        """[WQG-ST-02] Pure unit mock claiming Tier C scenario fails condition 6."""
        from result_reports import Case, verdicts
        cases = [Case("test_demo_WQG_HP_01", "tests.unit.test_app.UnitTest", "passed")]
        res = verdicts(["WQG-HP-01"], cases)
        self.assertFalse(res["WQG-HP-01"][0])
        self.assertIn("lacks integration runner provenance", res["WQG-HP-01"][1])


class Evidence_Integration_Test(ContractCase):
    def test_TCAE_HP_01_evidence_files_grounding(self) -> None:
        """Integration class version of TCAE-HP-01 for Tier C provenance."""
        test_TCAE_HP_01_evidence_files_grounding()

    def test_TCAE_FR_01_reject_invalid_evidence_files(self) -> None:
        """[TCAE-FR-01] Reject Evidence files with traversal, outside directory, or reserved runner record."""
        # 1. Path traversal
        t1 = self.task("1_trav", evidence="- `.devtool/epic/demo/../secret.txt` (new)")
        code, out, _ = self.check(t1, design=True)
        self.assertEqual(code, 1)
        self.assertIn("must reside under .devtool/epic/<epic_dir>/evidence/ without '..' segments", out)

        # 2. Outside epic evidence
        t2 = self.task("2_out", evidence="- `src/output.json` (new)")
        code, out, _ = self.check(t2, design=True)
        self.assertEqual(code, 1)
        self.assertIn("must reside under .devtool/epic/<epic_dir>/evidence/ without '..' segments", out)

        # 3. Collides with reserved runner task record
        t3 = self.task("3_coll", evidence="- `.devtool/epic/demo/evidence/task_01_setup.json` (new)")
        code, out, _ = self.check(t3, design=True)
        self.assertEqual(code, 1)
        self.assertIn("collides with reserved 'task_*.json' runner records", out)

        # 4. Marked (new) but already exists at design time
        self.write(f"{EPIC}/evidence/existing.txt", "pre-existing")
        t4 = self.task("4_exist", evidence=f"- `{EPIC}/evidence/existing.txt` (new)")
        code, out, _ = self.check(t4, design=True)
        self.assertEqual(code, 1)
        self.assertIn("marked (new) but already exists", out)

    def test_TCAE_HP_02_r3_verbatim_bdd_parity_check(self) -> None:
        """[TCAE-HP-02] check_task_contract --design reports R3 when task BDD differs from bdd_scenarios.en.md."""
        bdd_content = "# Scenarios\n\n```gherkin\nScenario: [DEMO-HP-01] Valid scenario\n  Given a state\n  When action occurs\n  Then result happens\n```\n"
        self.write(f"{EPIC}/bdd_scenarios.en.md", bdd_content)
        self.commit()

        # Task with mismatched BDD scenario
        task = self.task(
            "1_mismatch",
            allowed="- `tool.py`",
            covers="Covers: DEMO-HP-01\n\n```gherkin\nScenario: [DEMO-HP-01] Mismatched scenario\n  Given bad state\n```\n",
            rows=RED + GREEN +
                 "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
                 "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n" + TIER_C,
            dod="- done (V2, V3, V4, V5)\n",
            decisions="- Testing R3 mismatch.\n",
        )
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("scenario DEMO-HP-01 differs from bdd_scenarios.en.md (R3)", out)

    def test_TCAE_HP_02_r2_mirror_parity_check(self) -> None:
        """[TCAE-HP-02] check_task_contract --design reports R2 when mirror differs from epic task."""
        task = self.task("1_parity", allowed="- `tool.py`")
        # Create a modified mirror in .devtool/features/
        self.write(f".devtool/features/{task.name}", "# Different mirror content\n")
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn("features mirror content differs from epic task (R2)", out)


def test_TCAE_HP_01_evidence_files_grounding() -> None:
    """[TCAE-HP-01] Evidence files declaration grounds new evidence paths in design mode."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        git(root, "init", "-q")
        git(root, "config", "user.email", "demo@example.com")
        git(root, "config", "user.name", "Demo")
        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
        (root / "tool.py").write_text("print('x')\n", encoding="utf-8")
        (root / "README.md").write_text("demo\n", encoding="utf-8")
        epic_dir = root / EPIC
        epic_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "demo.en.md").write_text(HLD, encoding="utf-8")
        evidence_file = ".devtool/epic/demo/evidence/baseline.txt"
        task_content = task_text(
            allowed="- `tool.py`",
            rows=RED
            + GREEN
            + "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
            + "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n"
            + f"| V5 | TIER-C | `python3 tool.py int --evidence={evidence_file} --out=build/out.xml` | exit 0; results build/out.xml | — |\n",
            dod="- done (V2, V3, V4, V5)\n",
            decisions="- Testing evidence files contract.\n",
        )
        task_body = (
            "Allowed files:\n- `tool.py`\n\n"
            f"Evidence files:\n- `{evidence_file}` (new)\n\n"
            "Read-only context:\n- `README.md` — note\n"
        )
        task_content = task_content.replace(
            "Allowed files:\n- `tool.py`\n\nRead-only context:\n- `README.md` — note\n",
            task_body,
        )
        task_path = epic_dir / "task_1_evidence.md"
        task_path.write_text(task_content, encoding="utf-8")
        git(root, "add", "-A")
        git(root, "commit", "-q", "-m", "base")

        import task_contract as tc
        ev_entries = tc.parse_evidence_files(task_content)
        assert len(ev_entries) == 1
        assert ev_entries[0].pattern == evidence_file
        assert ev_entries[0].new is True

        cur = os.getcwd()
        os.chdir(root)
        try:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(["--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", str(task_path)])
            assert code == 0, out.getvalue()
            assert "Result: 0 problems — PASS" in out.getvalue()
        finally:
            os.chdir(cur)


class PortableD3NexusCliTest(ContractCase):
    def test_non_portable_path_rejected(self) -> None:
        """Reject hardcoded user home or plugin cache paths in Verification rows."""
        for bad_path, expected_match in [
            ("/Users/alice/tools/check.py", "/Users/"),
            ("/home/bob/scripts/check.sh", "/home/"),
            ("~/my_tools/lint.py", "~/"),
            (".claude/plugins/cache/check.py", ".claude/plugins/cache/"),
            (".gemini/config/plugins/check.py", ".gemini/config/plugins/"),
        ]:
            task = self.task(
                f"non_portable_{expected_match.strip('/.~')}",
                allowed="- `tool.py`",
                rows=f"| V1 | GREEN | `python3 {bad_path}` | exit 0 | — |\n",
                dod="- done (V1)\n",
            )
            code, out, _ = self.check(task)
            self.assertEqual(code, 1)
            self.assertIn(
                f"non-portable path '{expected_match}' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'",
                out,
            )

    def test_d3nexus_executable_recognized_without_warning(self) -> None:
        """d3nexus is recognized as a built-in kit executable without PATH warnings."""
        task = self.task(
            "d3nexus_ok",
            allowed="- `tool.py`",
            rows="| V1 | GREEN | `d3nexus check-doc --require-toc README.md` | exit 0 | — |\n",
            dod="- done (V1)\n",
        )
        code, out, _ = self.check(task)
        self.assertNotIn("executable d3nexus not found on PATH", out)

    def test_d3nexus_subcommand_resolves_implicit_checker(self) -> None:
        """d3nexus <subcommand> resolves to tracked script preserving implicit checker protection."""
        self.write("skills/doc_quality_check/resources/scripts/check_document.py", "# linter\n")
        self.commit()
        import task_contract as tc
        resolved = tc.program_of("d3nexus check-doc --require-toc README.md", self.root)
        self.assertEqual(resolved, "skills/doc_quality_check/resources/scripts/check_document.py")


class SearchPatternGrepTest(ContractCase):
    def test_TCAE_EC_03_grep_slash_pattern_excluded(self) -> None:
        """[TCAE-EC-03] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths."""
        task = self.task(
            "grep_slash",
            allowed="- `tool.py`",
            rows=RED
            + "| V2 | GREEN | `grep -E 'foo/bar/baz' README.md` | exit 0 | — |\n"
            + TIER_B
            + TIER_C,
        )
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)
        self.assertNotIn("foo/bar/baz does not exist", out)

    def test_TCAE_HP_04_escaped_pipe_and_implicit_protected_provenance(self) -> None:
        """[TCAE-HP-04] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance."""
        self.write("scripts/tool.py", "print('ok')\n")
        self.commit()
        task = self.task(
            "01_pipe",
            allowed="- `tool.py`",
            rows="| V1 | RED | `env MODE=strict python3 scripts/tool.py \\| grep -c ok` | exit 1; contains \"FAILED\" | — |\n"
            + GREEN
            + TIER_B
            + TIER_C,
        )
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Implicit protected paths: scripts/tool.py (task_01_pipe:V1), tool.py", out)

    def test_TCAE_FR_02_reject_non_portable_and_bare_env(self) -> None:
        """[TCAE-FR-02] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows."""
        task = self.task(
            "02_grammar_violations",
            allowed="- `tool.py`",
            rows="| V1 | RED | `python3 /Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py` | exit 1; contains \"FAILED\" | — |\n"
            + "| V2 | GREEN | `FOO=bar pytest tests/unit/test_sample.py::test_ok` | exit 0 | — |\n"
            + TIER_B
            + TIER_C,
        )
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1)
        self.assertIn(
            "task_02_grammar_violations:V1: non-portable path '/Users/' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'",
            out,
        )
        self.assertIn(
            "task_02_grammar_violations:V2: inline environment assignment 'FOO=bar' must be prefixed with 'env' (e.g. 'env FOO=bar ...')",
            out,
        )


def test_TCAE_EC_03_grep_slash_pattern_excluded() -> None:
    test = SearchPatternGrepTest()
    test.setUp()
    try:
        test.test_TCAE_EC_03_grep_slash_pattern_excluded()
    finally:
        test.doCleanups()


class SurgicalAnchorTest(ContractCase):
    def _big_py_content(self, num_lines: int) -> str:
        lines: list[str] = []
        idx = 0
        while len(lines) < num_lines:
            lines.append(f"def fn_{idx}() -> int:")
            if len(lines) < num_lines:
                lines.append(f"    return {idx}")
            idx += 1
        return "\n".join(lines[:num_lines]) + "\n"

    def _task_with_sections(self, allowed: str, extra_sections: str, status: str = "todo") -> Path:
        body = (
            f"---\nstatus: \"{status}\"\n---\n# Task\n\n"
            f"## Files\n\nAllowed files:\n{allowed}\n\nRead-only context:\n- `README.md` — note\n\n"
            f"{extra_sections}\n"
            f"## Verification\n\n{HEAD}{DEFAULT_ROWS}\n\n"
            f"## Definition of Done\n\n- done (V2, V3, V4, V5)\n\n"
            f"## Stop and Report If\n\n- A command does not match.\n\n"
            f"## Decisions Already Made\n\n- Grounded design decision.\n"
        )
        return self.write(f"{EPIC}/task_1_surgical.md", body)

    def test_tto_ec_03_rejects_large_file_without_symbol_or_line_range(self) -> None:
        """[TTO-EC-03] --design rejects >200-line tracked Allowed file lacking symbol or (L<start>-L<end>) anchor."""
        self.write("src/big_mod.py", self._big_py_content(202))
        task = self._task_with_sections(
            allowed="- `src/big_mod.py`",
            extra_sections="## Impact Analysis & Blast Radius\n\n- General refactor in `src/big_mod.py`.\n",
        )
        code, out, _ = self.check(task, design=True)
        self.assertEqual(code, 1, out)
        self.assertIn("src/big_mod.py", out)
        self.assertIn("> 200", out)

    def test_tto_ec_03_rejects_out_of_bounds_range_and_unknown_symbol(self) -> None:
        """[TTO-EC-03] Out-of-bounds line range or nonexistent symbol does not satisfy anchor check."""
        self.write("src/big_mod.py", self._big_py_content(210))
        bad_range = self._task_with_sections(
            allowed="- `src/big_mod.py`",
            extra_sections="## Impact Analysis & Blast Radius\n\n- `src/big_mod.py`: (L900-L950)\n",
        )
        code, out, _ = self.check(bad_range, design=True)
        self.assertEqual(code, 1, out)
        self.assertIn("src/big_mod.py", out)

        bad_sym = self._task_with_sections(
            allowed="- `src/big_mod.py`",
            extra_sections="## Impact Analysis & Blast Radius\n\n- `src/big_mod.py`: `missing_symbol`\n",
        )
        code2, out2, _ = self.check(bad_sym, design=True)
        self.assertEqual(code2, 1, out2)
        self.assertIn("src/big_mod.py", out2)

    def test_tto_ec_03_accepts_valid_symbol_or_line_range_anchor(self) -> None:
        """[TTO-EC-03] Valid symbol or (L<start>-L<end>) anchor across supported sections passes."""
        self.write("src/big_mod.py", self._big_py_content(220))
        variants = [
            "## Impact Analysis & Blast Radius\n\n- `src/big_mod.py`: `fn_5` (L11-L15)\n",
            "## Impact Analysis & Blast Radius\n\n- `src/big_mod.py`: (L10-L25)\n",
            "## Impact Analysis & Blast Radius\n\n- `src/big_mod.py` :: fn_5\n",
            "## File Anchor Map\n\n- `src/big_mod.py` :: `fn_5` (L11-L12)\n",
            "## Impact & Design\n\n- `src/big_mod.py`: (L1-L20)\n",
        ]
        for idx, sec in enumerate(variants):
            task = self._task_with_sections(allowed="- `src/big_mod.py`", extra_sections=sec)
            code, out, _ = self.check(task, design=True)
            self.assertEqual(code, 0, f"Variant {idx} failed:\n{out}")

    def test_tto_ec_03_boundary_200_lines_and_new_files_skip_anchor_check(self) -> None:
        """[TTO-EC-03] Files <= 200 lines, (new) files, and non-design runs pass without anchors."""
        self.write("src/exact_200.py", self._big_py_content(200))
        self.write("src/big_unanchored.py", self._big_py_content(250))
        task_200 = self._task_with_sections(
            allowed="- `src/exact_200.py`\n- `src/created.py` (new)",
            extra_sections="## Impact Analysis & Blast Radius\n\n- Boundary check.\n",
        )
        code, out, _ = self.check(task_200, design=True)
        self.assertEqual(code, 0, out)

        task_big = self._task_with_sections(
            allowed="- `src/big_unanchored.py`",
            extra_sections="## Impact Analysis & Blast Radius\n\n- No anchors.\n",
        )
        code_non_design, out_nd, _ = self.check(task_big, design=False)
        self.assertEqual(code_non_design, 0, out_nd)


if __name__ == "__main__":
    unittest.main()

