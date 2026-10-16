#!/usr/bin/env python3
"""Tests for check_task_contract.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py
"""
import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_task_contract import main

EPIC = ".devtool/epic/demo"
HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
RED = "| V1 | RED | `python3 tool.py red` | exit 1 | — |\n"
GREEN = "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |\n"
TIER_C = "| V3 | TIER-C | `python3 tool.py int --out=build/out.xml` | exit 0; results build/out.xml | — |\n"
VERIFICATION_ENV = "## 6. Verification Environment\n\nTests run in temporary directories. Variable: DEMO_TOKEN.\n"
HLD = ("# Epic\n\n## Integration Test Plan\n\nProtected paths: scripts/verify.sh\n\n"
       "Integration results: python3 tool.py all -> build/all.xml\n\n" + VERIFICATION_ENV)
DONE_LINE = "- done (V1)\n"


def task_text(rows: str = RED + GREEN + TIER_C, allowed: str = "- `tool.py`", dod: str = "- done (V2, V3)\n",
              covers: str = "", status: str = "todo", read_only: str = "- `README.md` — note",
              after_table: str = "", skip: str = "") -> str:
    sections = {
        "Files": f"Allowed files:\n{allowed}\n\nRead-only context:\n{read_only}\n",
        "Verification": f"{HEAD}{rows}\n{after_table}",
        "Definition of Done": dod,
        "Stop and Report If": "- A command does not match.\n",
        "Decisions Already Made": "None.\n",
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

    def task(self, name: str, **kwargs) -> Path:
        return self.write(f"{EPIC}/task_{name}.md", task_text(**kwargs))

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main([str(arg) for arg in argv])
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue()

    def check(self, *tasks: Path, design: bool = False) -> tuple[int, str, str]:
        self.commit()
        flags = ["--design"] if design else []
        return self.run_cli(*flags, "--hld", f"{EPIC}/demo.en.md", "--tasks", *tasks)


class CompliantEpicTest(ContractCase):
    def test_vth_hp_01_a_compliant_epic_passes_and_prints_implicit_protected_paths(self) -> None:
        first = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
        second = self.task("2_b", allowed="- `README.md`", covers="Covers: DEMO-HP-01",
                           rows=RED + GREEN + TIER_C.replace("tool.py int", "tool.py src/made.py"))
        code, out, _ = self.check(first, second, design=True)
        self.assertEqual(code, 0, out)
        self.assertIn("Implicit protected paths: tool.py", out)
        self.assertIn("Result: 0 problems — PASS", out)

    def test_no_tracked_program_prints_none(self) -> None:
        task = self.task("1_a", rows=RED.replace("python3 tool.py red", "echo red") + GREEN.replace(
            "python3 tool.py green", "echo green") + TIER_C.replace("python3 tool.py", "echo"))
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)
        self.assertIn("Implicit protected paths: none", out)

    def test_wrapped_dod_bullet_and_trailing_period_pass(self) -> None:
        task = self.task("1_a", dod="- done and\n  wrapped (V1, V2).\n- by hand (Gate 5)\n")
        code, out, _ = self.check(task)
        self.assertEqual(code, 0, out)

    def test_missing_executable_warns_without_failing(self) -> None:
        task = self.task("1_a", rows=RED + GREEN.replace("python3 tool.py green", "nosuch-demo-tool run") + TIER_C)
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
        user = self.task("2_b", rows=RED + GREEN.replace("tool.py green", "tool.py src/made.py") + TIER_C)
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
        task = self.task("1_a", rows=GREEN + TIER_C, after_table="RED: n/a — no new behaviour\n")
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
        task = self.task("1_a", rows=RED + GREEN + TIER_C.replace("| — |", "| UNNAMED_VAR |"))
        code, out, _ = self.check(task)
        self.assertEqual(code, 1)
        self.assertIn("task_1_a:V3: Needs UNNAMED_VAR is not named in the Verification Environment section", out)
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


if __name__ == "__main__":
    unittest.main()
