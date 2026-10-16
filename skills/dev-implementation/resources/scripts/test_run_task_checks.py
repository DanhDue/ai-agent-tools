#!/usr/bin/env python3
"""Tests for task_contract.py and run_task_checks.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py
"""
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import task_contract as tc
from run_task_checks import main

TABLE_HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
EPIC = ".devtool/epic/demo"
TASK = f"{EPIC}/task_1_demo.md"
EVIDENCE = f"{EPIC}/evidence/task_1_demo.json"
TICKS = "`" * 3


def task_text(rows: str, allowed: str = "- `feature.txt` (new)", after_table: str = "",
              head: str = TABLE_HEAD) -> str:
    return (f"# Task 1\n\n## Files\n\nAllowed files:\n{allowed}\n\nRead-only context:\n- `x` - note\n\n"
            f"## Verification\n\n{head}{rows}\n{after_table}\n## Definition of Done\n\n- done (V1)\n")


def hld_text(protected: str = "") -> str:
    line = f"Protected paths: {protected}\n" if protected else ""
    return f"# Epic\n\n## Integration Test Plan\n\n{line}Integration test roots: tests\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout


class RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        git(self.root, "init", "-q")
        git(self.root, "config", "user.email", "demo@example.com")
        git(self.root, "config", "user.name", "Demo")

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def commit(self) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "base")

    def epic(self, rows: str, protected: str = "", **kwargs) -> Path:
        self.write(f"{EPIC}/demo.en.md", hld_text(protected))
        self.write(f"{EPIC}/bdd_scenarios.en.md", "# Scenarios\n")
        task = self.write(TASK, task_text(rows, **kwargs))
        self.commit()
        return task

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main([str(arg) for arg in argv])
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue()

    def evidence(self) -> dict:
        return json.loads((self.root / EVIDENCE).read_text(encoding="utf-8"))

    def run_rows(self) -> dict:
        return {row["id"]: row for row in self.evidence()["runs"]["verify"]["rows"]}


class ParserTest(unittest.TestCase):
    def test_section_stops_at_next_heading_and_ignores_fenced_headings(self) -> None:
        text = f"# T\n\n## A\n\none\n{TICKS}\n## not a heading\n{TICKS}\n\n## B\n\ntwo\n"
        self.assertIn("one", tc.section(text, "A"))
        self.assertIn("not a heading", tc.section(text, "A"))
        self.assertNotIn("two", tc.section(text, "A"))
        self.assertIsNone(tc.section(text, "Missing"))

    def test_parse_expect_accepts_the_grammar(self) -> None:
        expect = tc.parse_expect('exit 0; contains "passed"; contains "ok"; results build/a.xml')
        self.assertEqual(expect, tc.Expect(0, False, ("passed", "ok"), "build/a.xml"))
        self.assertEqual(tc.parse_expect("exit non-zero"), tc.Expect(None, True, (), None))

    def test_parse_expect_rejects_everything_else(self) -> None:
        for bad in ("", "exit", "exit 0;contains \"x\"", "contains \"x\"", "exit 0; results a; results b",
                    "exit 0; contains x", "exit 0; unknown", 'exit 0; contains "a"b"'):
            with self.subTest(bad=bad), self.assertRaises(tc.ContractError):
                tc.parse_expect(bad)

    def test_parse_verification_rows_and_red_na(self) -> None:
        rows = ("| V1 | RED | `a \\| b` | exit non-zero | — |\n"
                "| V2 | TIER-C | `echo hi` | exit 0; results out.xml | DEMO_ONE, DEMO_TWO |\n")
        parsed, reason = tc.parse_verification(task_text(rows, after_table="RED: n/a - nothing new\n"))
        self.assertEqual([row.id for row in parsed], ["V1", "V2"])
        self.assertEqual(parsed[0].command, "a | b")
        self.assertEqual(parsed[1].needs, ("DEMO_ONE", "DEMO_TWO"))
        self.assertEqual(parsed[0].needs, ())
        self.assertEqual(parsed[1].expect.results, "out.xml")
        self.assertEqual(parsed[1].expect_text, "exit 0; results out.xml")
        self.assertEqual(reason, "nothing new")
        self.assertIsNone(tc.parse_verification(task_text(rows))[1])

    def test_parse_verification_rejects_malformed_tables(self) -> None:
        good = "| V1 | GREEN | `true` | exit 0 | — |\n"
        cases = {
            "missing section": "# T\n",
            "no expect column": task_text("| V1 | GREEN | `true` | — |\n",
                                          head="| ID | Phase | Command | Needs |\n|--|--|--|--|\n"),
            "duplicate id": task_text(good + good),
            "bad phase": task_text("| V1 | BLUE | `true` | exit 0 | — |\n"),
            "two code spans": task_text("| V1 | GREEN | `a` `b` | exit 0 | — |\n"),
            "no code span": task_text("| V1 | GREEN | true | exit 0 | — |\n"),
            "bad needs": task_text("| V1 | GREEN | `true` | exit 0 | lower |\n"),
            "bad expect": task_text("| V1 | GREEN | `true` | passes | — |\n"),
        }
        for name, text in cases.items():
            with self.subTest(name), self.assertRaises(tc.ContractError):
                tc.parse_verification(text)

    def test_contract_error_names_the_row(self) -> None:
        with self.assertRaisesRegex(tc.ContractError, "V7"):
            tc.parse_verification(task_text("| V7 | BLUE | `true` | exit 0 | — |\n"))

    def test_parse_allowed_files_and_protected_paths(self) -> None:
        text = task_text("", allowed="- `a/b.py` (new)\n- `c/**`")
        self.assertEqual(tc.parse_allowed_files(text),
                         [tc.AllowedPath("a/b.py", True), tc.AllowedPath("c/**", False)])
        self.assertEqual(tc.parse_protected_paths(hld_text(".agents/**, x/y.md")), [".agents/**", "x/y.md"])
        self.assertEqual(tc.parse_protected_paths(hld_text()), [])

    def test_path_matches(self) -> None:
        self.assertTrue(tc.path_matches("scripts/**", "scripts/a/b.py"))
        self.assertTrue(tc.path_matches("scripts/*.py", "scripts/a.py"))
        self.assertFalse(tc.path_matches("scripts/*.py", "scripts/a/b.py"))
        self.assertTrue(tc.path_matches("a?.py", "ab.py"))
        self.assertFalse(tc.path_matches("a?.py", "a/.py"))
        self.assertTrue(tc.path_matches("a.py", "a.py"))
        self.assertFalse(tc.path_matches("a.py", "ab.py"))
        self.assertTrue(tc.path_matches("a/**/b.py", "a/b.py"))
        self.assertTrue(tc.path_matches("a/**/b.py", "a/x/y/b.py"))
        self.assertFalse(tc.path_matches("a.b", "aXb"))


class GitHelpersTest(RepoCase):
    def test_program_of_unwraps_and_requires_a_tracked_file(self) -> None:
        self.write("tools/check.py", "")
        self.write("run.sh", "")
        self.commit()
        cases = {
            "python3 tools/check.py --x": "tools/check.py",
            "uv run python3 tools/check.py": "tools/check.py",
            "env A=1 B=2 bash ./run.sh && echo hi": "run.sh",
            "./run.sh | cat": "run.sh",
            "python3 -m unittest tools/check.py": None,
            "python3 -c 'print(1)'": None,
            "python3 -u tools/check.py": "tools/check.py",
            "python3 missing.py": None,
            "echo hi": None,
            "": None,
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(tc.program_of(command, self.root), expected)

    def test_epic_layout(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n")
        layout = tc.epic_layout(task)
        self.assertEqual(layout.root, self.root)
        self.assertEqual(layout.epic_dir, self.root / EPIC)
        self.assertEqual(layout.hld, self.root / EPIC / "demo.en.md")
        self.assertEqual(layout.scenarios, self.root / EPIC / "bdd_scenarios.en.md")
        self.assertEqual(layout.evidence, self.root / EVIDENCE)
        features = self.write(".devtool/features/task_1_demo.md", "x")
        with self.assertRaisesRegex(tc.ContractError, "pass the task's mirror under"):
            tc.epic_layout(features)

    def test_fingerprint_sees_untracked_files_and_leaves_the_index_alone(self) -> None:
        self.write("a.txt", "one\n")
        self.commit()
        tree_clean, patch_clean = tc.fingerprint(self.root)
        self.assertIsNone(patch_clean)
        self.write("b.txt", "two\n")
        self.write(f"{EPIC}/ignored.md", "no effect")
        tree_dirty, patch_dirty = tc.fingerprint(self.root)
        self.assertNotEqual(tree_clean, tree_dirty)
        self.assertTrue(patch_dirty)
        self.assertEqual(git(self.root, "status", "--porcelain").count("??"), 2)
        self.assertEqual(git(self.root, "diff", "--cached", "--name-only"), "")

    def test_changed_paths_includes_both_sides_of_a_rename(self) -> None:
        self.write("old.txt", "x\n")
        self.write("keep.txt", "y\n")
        self.commit()
        git(self.root, "mv", "old.txt", "new.txt")
        self.write("untracked/deep.txt", "z")
        self.assertEqual(sorted(tc.changed_paths(self.root)),
                         ["new.txt", "old.txt", "untracked/deep.txt"])

    def test_evidence_round_trip(self) -> None:
        path = self.root / "a" / "b.json"
        self.assertIsNone(tc.load_evidence(path))
        tc.save_evidence(path, {"k": [1]})
        self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "k": [\n    1\n  ]\n}\n')
        self.assertEqual(tc.load_evidence(path), {"k": [1]})


class RecorderTest(RepoCase):
    def test_vth_hp_02_red_then_verify_records_passing_evidence(self) -> None:
        rows = ("| V1 | RED | `test -f feature.txt` | exit non-zero | — |\n"
                "| V2 | GREEN | `test -f feature.txt && echo found` | exit 0; contains \"found\" | — |\n")
        task = self.epic(rows)
        code, out, _ = self.run_cli("red", task)
        self.assertEqual(code, 0, out)
        self.write("feature.txt", "hello\n")
        code, out, _ = self.run_cli("verify", task)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: PASS", out)
        evidence = self.evidence()
        self.assertEqual(evidence["schema"], 1)
        self.assertEqual(evidence["task"], "task_1_demo")
        for kind in ("red", "verify"):
            run = evidence["runs"][kind]
            self.assertEqual(run["head"], git(self.root, "rev-parse", "HEAD").strip())
            self.assertTrue(run["tree"] and run["started"] and run["finished"])
        self.assertIsNone(evidence["runs"]["red"]["patch_id"])
        self.assertTrue(evidence["runs"]["verify"]["patch_id"])
        red_row = evidence["runs"]["red"]["rows"][0]
        self.assertEqual((red_row["outcome"], red_row["exit"]), ("PASS", 1))
        verify_rows = evidence["runs"]["verify"]["rows"]
        self.assertEqual([row["id"] for row in verify_rows], ["V2", "SCOPE"])
        self.assertEqual(verify_rows[0]["outcome"], "PASS")
        self.assertEqual(verify_rows[0]["output_tail"], ["found"])
        self.assertEqual(len(verify_rows[0]["output_sha256"]), 64)
        self.assertEqual(verify_rows[0]["expect"], 'exit 0; contains "found"')
        self.assertEqual((verify_rows[1]["phase"], verify_rows[1]["outcome"]), ("SCOPE", "PASS"))
        self.assertEqual(verify_rows[1]["changed"], ["feature.txt"])

    def test_vth_ec_05_unset_needs_variable_blocks_without_running(self) -> None:
        task = self.epic("| V1 | TIER-C | `touch ran.txt` | exit 0 | DEMO_DATABASE_URL |\n")
        env = {key: value for key, value in os.environ.items() if key != "DEMO_DATABASE_URL"}
        with mock.patch.dict(os.environ, env, clear=True):
            code, out, _ = self.run_cli("verify", task)
        self.assertEqual(code, 1)
        row = self.run_rows()["V1"]
        self.assertEqual((row["outcome"], row["reason"], row["exit"]), ("BLOCKED", "unset: DEMO_DATABASE_URL", None))
        self.assertFalse((self.root / "ran.txt").exists())
        self.assertIn("Result: FAIL", out)

    def test_empty_needs_variable_is_blocked_and_set_one_runs(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | exit 0 | DEMO_FLAG |\n", allowed="- `x` (new)")
        with mock.patch.dict(os.environ, {"DEMO_FLAG": ""}):
            self.assertEqual(self.run_cli("verify", task)[0], 1)
        self.assertEqual(self.run_rows()["V1"]["outcome"], "BLOCKED")
        with mock.patch.dict(os.environ, {"DEMO_FLAG": "1"}):
            self.assertEqual(self.run_cli("verify", task)[0], 0)

    def test_vth_st_02_scope_rejects_outside_and_protected_changes(self) -> None:
        self.write("scripts/verify_coverage.py", "print('ok')\n")
        task = self.epic("| V1 | GREEN | `python3 scripts/verify_coverage.py` | exit 0 | — |\n",
                         allowed="- `scripts/**`")
        self.write("outside.txt", "stray\n")
        self.write("scripts/verify_coverage.py", "print('weakened')\n")
        code, out, _ = self.run_cli("verify", task)
        self.assertEqual(code, 1)
        scope = self.run_rows()["SCOPE"]
        self.assertEqual(scope["outcome"], "FAIL")
        self.assertIn("outside Allowed files: outside.txt", scope["violations"])
        self.assertIn("protected path not named exactly in Allowed files: scripts/verify_coverage.py",
                      scope["violations"])
        self.assertIn("outside.txt", out)

    def test_deleting_a_protected_program_fails_scope(self) -> None:
        self.write("scripts/verify_coverage.py", "print('ok')\n")
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n| V2 | GREEN | `python3 scripts/verify_coverage.py` | exit 0 | — |\n",
                         allowed="- `scripts/**`")
        (self.root / "scripts/verify_coverage.py").unlink()
        self.assertEqual(self.run_cli("verify", task)[0], 1)
        self.assertIn("protected path not named exactly in Allowed files: scripts/verify_coverage.py",
                      self.run_rows()["SCOPE"]["violations"])

    def test_exact_allowed_entry_authorises_a_protected_program(self) -> None:
        self.write("scripts/verify_coverage.py", "print('ok')\n")
        task = self.epic("| V1 | GREEN | `python3 scripts/verify_coverage.py` | exit 0 | — |\n",
                         allowed="- `scripts/verify_coverage.py`")
        self.write("scripts/verify_coverage.py", "print('changed')\n")
        self.assertEqual(self.run_cli("verify", task)[0], 0)

    def test_hld_protected_paths_count_even_under_devtool(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n",
                         protected=f"{EPIC}/bdd_scenarios.en.md", allowed="- `x` (new)")
        self.write(f"{EPIC}/bdd_scenarios.en.md", "# edited\n")
        self.write(f"{EPIC}/notes.md", "ignored under .devtool\n")
        self.assertEqual(self.run_cli("verify", task)[0], 1)
        violations = self.run_rows()["SCOPE"]["violations"]
        self.assertEqual(violations, [f"protected path not named exactly in Allowed files: {EPIC}/bdd_scenarios.en.md"])

    def test_program_of_a_sibling_task_row_is_protected(self) -> None:
        self.write("tools/grade.py", "print(1)\n")
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n", allowed="- `tools/**`")
        self.write(f"{EPIC}/task_2_other.md", task_text("| V1 | GREEN | `python3 tools/grade.py` | exit 0 | — |\n"))
        self.commit()
        self.write("tools/grade.py", "print(2)\n")
        self.assertEqual(self.run_cli("verify", task)[0], 1)
        self.assertIn("protected path not named exactly in Allowed files: tools/grade.py",
                      self.run_rows()["SCOPE"]["violations"])

    def test_vth_fr_01_slow_row_and_stale_report_fail_closed(self) -> None:
        self.write("report.xml", "<testsuites/>")
        os.utime(self.root / "report.xml", (1_000_000, 1_000_000))
        rows = ("| V1 | GREEN | `sleep 20` | exit 0 | — |\n"
                "| V2 | TIER-C | `true` | exit 0; results report.xml | — |\n")
        task = self.epic(rows, allowed="- `x` (new)")
        code, _, _ = self.run_cli("verify", task, "--timeout", "1")
        self.assertEqual(code, 1)
        by_id = self.run_rows()
        self.assertEqual((by_id["V1"]["outcome"], by_id["V1"]["reason"]), ("FAIL", "timeout after 1 s"))
        self.assertEqual((by_id["V2"]["outcome"], by_id["V2"]["reason"]),
                         ("FAIL", "results not produced by this run"))
        self.assertEqual(by_id["V2"]["results"], {"path": "report.xml", "fresh": False})

    def test_fresh_results_file_and_directory_pass(self) -> None:
        rows = ("| V1 | TIER-C | `mkdir -p out && echo '<x/>' > out/a.xml` | exit 0; results out | — |\n"
                "| V2 | TIER-C | `echo '{}' > single.json` | exit 0; results single.json | — |\n")
        task = self.epic(rows, allowed="- `out/**` (new)\n- `single.json` (new)")
        self.assertEqual(self.run_cli("verify", task)[0], 0)
        by_id = self.run_rows()
        self.assertEqual(by_id["V1"]["results"], {"path": "out", "fresh": True})
        self.assertEqual(by_id["V2"]["results"], {"path": "single.json", "fresh": True})

    def test_missing_results_path_is_not_fresh(self) -> None:
        task = self.epic("| V1 | TIER-C | `true` | exit 0; results nowhere.xml | — |\n")
        self.assertEqual(self.run_cli("verify", task)[0], 1)
        self.assertEqual(self.run_rows()["V1"]["reason"], "results not produced by this run")

    def test_mismatches_fail_but_every_row_still_runs(self) -> None:
        rows = ("| V1 | GREEN | `echo hello; exit 3` | exit 0 | — |\n"
                "| V2 | GREEN | `echo hello` | exit 0; contains \"absent\" | — |\n"
                "| V3 | GREEN | `echo hello` | exit 0; contains \"hello\" | — |\n")
        task = self.epic(rows, allowed="- `x` (new)")
        self.assertEqual(self.run_cli("verify", task)[0], 1)
        by_id = self.run_rows()
        self.assertEqual([by_id[name]["outcome"] for name in ("V1", "V2", "V3")], ["FAIL", "FAIL", "PASS"])
        self.assertEqual(by_id["V1"]["exit"], 3)
        self.assertIn("3", by_id["V1"]["reason"])
        self.assertIn("absent", by_id["V2"]["reason"])

    def test_stderr_is_combined_and_tail_keeps_the_last_forty_lines(self) -> None:
        rows = ("| V1 | GREEN | `seq 1 100; echo oops >&2` | exit 0; contains \"oops\" | — |\n")
        task = self.epic(rows, allowed="- `x` (new)")
        self.assertEqual(self.run_cli("verify", task)[0], 0)
        tail = self.run_rows()["V1"]["output_tail"]
        self.assertEqual(len(tail), 40)
        self.assertEqual(tail[-1], "oops")

    def test_pipefail_applies(self) -> None:
        task = self.epic("| V1 | GREEN | `false \\| cat` | exit 1 | — |\n", allowed="- `x` (new)")
        self.assertEqual(self.run_cli("verify", task)[0], 0)

    def test_a_run_replaces_the_previous_run_of_its_kind(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n| V2 | RED | `false` | exit non-zero | — |\n",
                         allowed="- `x` (new)")
        self.run_cli("red", task)
        first = self.evidence()["runs"]["red"]["started"]
        self.run_cli("verify", task)
        self.run_cli("red", task)
        evidence = self.evidence()
        self.assertGreaterEqual(evidence["runs"]["red"]["started"], first)
        self.assertEqual(set(evidence["runs"]), {"red", "verify"})
        self.assertEqual([row["id"] for row in evidence["runs"]["red"]["rows"]], ["V2"])

    def test_red_without_red_rows_or_with_red_na_exits_two(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n", after_table="RED: n/a — bootstrap\n")
        code, _, err = self.run_cli("red", task)
        self.assertEqual(code, 2)
        self.assertIn("RED", err)
        self.assertFalse((self.root / EVIDENCE).exists())
        self.write(TASK, task_text("| V1 | GREEN | `true` | exit 0 | — |\n"))
        self.assertEqual(self.run_cli("red", task)[0], 2)

    def test_vth_fr_05_unparseable_task_exits_two_and_writes_no_evidence(self) -> None:
        task = self.epic("| V1 | GREEN | `true` | — |\n",
                         head="| ID | Phase | Command | Needs |\n|--|--|--|--|\n")
        code, _, err = self.run_cli("verify", task)
        self.assertEqual(code, 2)
        self.assertIn("Expect", err)
        self.assertFalse((self.root / EVIDENCE).exists())

    def test_mirror_outside_the_epic_directory_exits_two(self) -> None:
        self.epic("| V1 | GREEN | `true` | exit 0 | — |\n")
        features = self.write(".devtool/features/task_1_demo.md", task_text("| V1 | GREEN | `true` | exit 0 | — |\n"))
        code, _, err = self.run_cli("verify", features)
        self.assertEqual(code, 2)
        self.assertIn("pass the task's mirror under", err)

    def test_usage_errors_exit_two(self) -> None:
        self.assertEqual(self.run_cli("verify")[0], 2)
        self.assertEqual(self.run_cli("verify", self.root / "nope.md")[0], 2)


if __name__ == "__main__":
    unittest.main()
