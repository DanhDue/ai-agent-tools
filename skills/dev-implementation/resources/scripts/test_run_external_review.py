#!/usr/bin/env python3
"""Tests for run_external_review.py, on throwaway git repositories with fake claude and codex executables.

The fakes are the only claude and codex on PATH, so no test reaches a real CLI.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from run_external_review import main

EPIC = ".devtool/epic/demo"
TICKS = "`" * 3
FAKE = """#!/bin/bash
cat > "$FAKE_STDIN"
echo "$@" > "$FAKE_ARGS"
case "$FAKE_MODE" in
  pass) echo "Verdict: PASS" ;;
  minor) echo "Verdict: CHANGES REQUIRED"; echo "- [Minor] README.md:1 — wording | unclear" ;;
  blocking) echo "Verdict: CHANGES REQUIRED"
            echo "[Critical] demo.en.md:3 — evidence missing"
            echo "[Important] task_1_demo.md:9 — row too weak" ;;
  formats) echo "Verdict: CHANGES REQUIRED"
           echo "1. **[Critical]** demo.en.md:3 – evidence missing"
           echo "* [Important] task_1_demo.md:9: row too weak"
           echo "[Important] the audit output was never read" ;;
  bare) echo "Verdict: CHANGES REQUIRED"; echo "Several things look wrong." ;;
  fail) echo "credit balance is too low"; exit 1 ;;
  silent) echo "I looked at everything." ;;
  slow) sleep 30 ;;
  modify) echo changed > DEMO-created.txt; echo "Verdict: PASS" ;;
  bold_verdict) echo "**Verdict:** PASS" ;;
  heading_verdict) echo "### Verdict: CHANGES REQUIRED"; echo "- [Critical] demo.en.md:1 — broken" ;;
  case_verdict) echo "   verdict:   pass   " ;;
  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;
  list_findings) echo "Verdict: CHANGES REQUIRED"
                 echo "- [Critical] demo.en.md:1 — list bullet dash"
                 echo "* [Important] demo.en.md:2 — list bullet star"
                 echo "1. [Minor] demo.en.md:3 — numbered list" ;;

  bold_verdict) echo "**Verdict:** PASS" ;;
  heading_verdict) echo "### Verdict: CHANGES REQUIRED"; echo "- [Critical] demo.en.md:1 — broken" ;;
  case_verdict) echo "   verdict:   pass   " ;;
  prose_summary) echo "I reviewed everything and found 0 [Critical] or [Important] issues."; echo "Verdict: PASS" ;;

esac
"""
HLD = ("# Demo\n\nIntegration test roots: scripts/\n\nIntegration results: true -> build/demo.xml\n")
SCENARIOS = f"# Scenarios\n\n{TICKS}gherkin\nScenario: [DEMO-HP-01] [Tier C - Integration] Demo\n  Given a demo\n{TICKS}\n"


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=True).stdout.strip()


class ReviewCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        tmp = Path(directory.name).resolve()
        self.root, self.bin = tmp / "repo", tmp / "bin"
        self.root.mkdir()
        self.bin.mkdir()
        for tool in ("git", "bash", "cat", "sleep", "sh"):  # only what the run needs: never a real claude or codex
            (self.bin / tool).symlink_to(shutil.which(tool))
        (self.bin / "python3").symlink_to(sys.executable)
        self.stdin, self.args = tmp / "stdin.txt", tmp / "args.txt"
        env = {"PATH": str(self.bin), "FAKE_STDIN": str(self.stdin), "FAKE_ARGS": str(self.args)}
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "demo@example.com")
        git(self.root, "config", "user.name", "Demo")
        self.write("README.md", "demo\n")
        self.commit("Start")
        self.base = git(self.root, "rev-parse", "HEAD")
        self.write(f"{EPIC}/demo.en.md", HLD)
        self.write(f"{EPIC}/bdd_scenarios.en.md", SCENARIOS)
        self.write(f"{EPIC}/design.en.md", "# Spec\n")
        self.write(f"{EPIC}/task_1_demo.md", '---\nid: "task_1_demo"\nstatus: "done"\n---\n\n# Task 1\n')
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<testsuites>\n  <testsuite name="demo" tests="1">\n    <testcase name="test_demo_hp_01" classname="test_demo"/>\n  </testsuite>\n</testsuites>\n'
        self.write("build/demo.xml", xml)
        self.write("scripts/test_demo.py", "# [DEMO-HP-01]\ndef test_demo_hp_01(): pass\n")
        self.commit("Epic")
        self.results = self.root / EPIC / "review_results.md"
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.cwd)

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, message: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)

    def install(self, name: str) -> None:
        path = self.bin / name
        path.write_text(FAKE, encoding="utf-8")
        path.chmod(0o755)

    def run_review(self, *extra: str, cli: str = "codex", mode: str = "pass") -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_MODE": mode}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--epic-dir", "demo", "--base", self.base, "--cli", cli, *extra])
        return code, out.getvalue(), err.getvalue()

    def check(self) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = main(["check", "--epic-dir", "demo"])
        return code, out.getvalue()

    def text(self) -> str:
        return self.results.read_text(encoding="utf-8")


class RunExternalReviewTest(ReviewCase):
    def test_vth_hp_12_a_clean_review_round_is_recorded(self) -> None:
        self.install("codex")
        code, _, _ = self.run_review("--model", "gpt-test")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        for expected in (git(self.root, "rev-parse", "HEAD"), self.base, f"{EPIC}/evidence",
                         "Each done task's evidence against its Verification table",
                         "The `(Gate 5)` items", "Verdict: PASS"):
            self.assertIn(expected, prompt)
        self.assertEqual(self.args.read_text().split(), ["exec", "--sandbox", "read-only", "--model", "gpt-test", "-"])
        text = self.text()
        self.assertTrue(text.startswith("# Cross-Model Review: demo\n"))
        for expected in ("## Round 1", "- **Status**: completed", "- **CLI**: codex", "- **Model**: gpt-test",
                         "- **Verdict**: PASS", f"- **Base**: {self.base}", f"{TICKS}text\nVerdict: PASS\n{TICKS}"):
            self.assertIn(expected, text)
        self.assertEqual(self.check()[0], 0)

    def test_vth_ec_07_minor_findings_alone_do_not_block(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude", mode="minor")
        self.assertEqual(code, 0)
        self.assertEqual(self.args.read_text().split(), ["-p", "--permission-mode", "plan"])
        text = self.text()
        self.assertIn("- **Model**: default", text)
        self.assertIn("| 1 | Minor | README.md:1 | wording \\| unclear |  |", text)
        self.assertEqual(self.check()[0], 0)

    def test_vth_st_10_blocking_findings_hold_phase_4_until_each_has_a_decision(self) -> None:
        self.install("claude")
        self.assertEqual(self.run_review(cli="claude", mode="blocking")[0], 1)
        text = self.text()
        self.assertIn("| 1 | Critical | demo.en.md:3 | evidence missing |  |", text)
        self.assertIn("| 2 | Important | task_1_demo.md:9 | row too weak |  |", text)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("undecided: #1 Critical demo.en.md:3", out)
        self.assertIn("undecided: #2 Important task_1_demo.md:9", out)
        text = text.replace("evidence missing |  |", "evidence missing | fixed in abc1234 |")
        self.results.write_text(text.replace("row too weak |  |", "row too weak | dismissed: by design |"),
                                encoding="utf-8")
        self.assertEqual(self.check(), (0, ""))

    def test_vth_st_11_the_latest_completed_round_governs_check(self) -> None:
        def round_text(n: int, status: str, findings: str) -> str:
            return (f"## Round {n}\n\n- **Status**: {status}\n- **Verdict**: none\n\n"
                    f"| # | Severity | Location | Problem | Decision |\n|---|---|---|---|---|\n{findings}\n"
                    f"Raw output:\n\n{TICKS}text\n## Round 99\n{TICKS}\n\n")
        body = ("# Cross-Model Review: demo\n\n" + round_text(1, "completed", "| 1 | Critical | a:1 | bad |  |")
                + round_text(2, "completed", "| 1 | Minor | b:2 | nit |  |")
                + round_text(3, "no verdict", "| 1 | Critical | c:3 | worse |  |"))
        self.results.write_text(body, encoding="utf-8")
        self.assertEqual(self.check(), (0, ""))
        self.assertEqual(self.text(), body)

    def test_finding_lines_in_other_shapes_are_parsed_and_unparsed_blocking_lines_kept(self) -> None:
        self.install("codex")
        self.assertEqual(self.run_review(mode="formats")[0], 1)
        text = self.text()
        self.assertIn("| 1 | Critical | demo.en.md:3 | evidence missing |  |", text)
        self.assertIn("| 2 | Important | task_1_demo.md:9 | row too weak |  |", text)
        self.assertIn("| 3 | Important | unparsed | [Important] the audit output was never read |  |", text)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertEqual(out.count("undecided:"), 3)

    def test_changes_required_without_a_finding_line_is_no_verdict(self) -> None:
        self.install("codex")
        self.assertEqual(self.run_review(mode="bare")[0], 2)
        self.assertIn("- **Status**: no verdict", self.text())
        self.assertEqual(self.check(), (0, ""))

    def round_text(self, status: str, findings: str, raw: str) -> str:
        return (f"## Round 1\n\n- **Status**: {status}\n- **Verdict**: none\n\n"
                f"| # | Severity | Location | Problem | Decision |\n|---|---|---|---|---|\n{findings}\n"
                f"Raw output:\n\n{TICKS}text\n{raw}\n{TICKS}\n")

    def test_an_unreadable_findings_row_fails_closed(self) -> None:
        self.results.write_text("# Cross-Model Review: demo\n\n" + self.round_text(
            "completed", "| 1 | Minor | a:1 | split | by | pipes |  |", "Verdict: PASS"), encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("undecided: unreadable findings row: | 1 | Minor | a:1 | split | by | pipes |  |", out)

    def test_a_round_status_is_read_from_its_fields_not_its_raw_output(self) -> None:
        self.results.write_text("# Cross-Model Review: demo\n\n" + self.round_text(
            "no verdict", "| 1 | Critical | c:3 | worse |  |", "- **Status**: completed"), encoding="utf-8")
        self.assertEqual(self.check(), (0, ""))

    def test_vth_fr_06_a_missing_cli_or_a_dirty_tree_stops_the_review_before_it_runs(self) -> None:
        code, _, err = self.run_review(cli="claude")
        self.assertEqual(code, 2)
        self.assertIn("claude not found on PATH", err)
        self.assertFalse(self.results.exists())
        self.install("claude")
        self.write("README.md", "dirty\n")
        code, _, err = self.run_review(cli="claude")
        self.assertEqual(code, 2)
        self.assertIn("commit or stash your changes before a review", err)
        self.assertFalse(self.results.exists())
        self.assertFalse(self.stdin.exists())

    def test_vth_fr_07_a_reviewer_that_modifies_the_tree_is_discarded(self) -> None:
        self.install("codex")
        code, _, _ = self.run_review(mode="modify")
        self.assertEqual(code, 2)
        self.assertIn("- **Status**: discarded: tree modified (DEMO-created.txt)", self.text())
        self.assertTrue((self.root / "DEMO-created.txt").exists())

    def test_vth_fr_08_a_failing_silent_or_slow_cli_records_no_verdict(self) -> None:
        self.install("claude")
        for mode, option in (("fail", []), ("silent", []), ("slow", ["--timeout", "1"])):
            with self.subTest(mode=mode):
                self.assertEqual(self.run_review(*option, cli="claude", mode=mode)[0], 2)
                self.commit(f"Record {mode} round")  # a review needs a clean tree
        text = self.text()
        self.assertEqual(text.count("- **Status**: no verdict"), 3)
        self.assertEqual(text.count("- **Verdict**: none"), 3)
        self.assertIn("credit balance is too low", text)
        self.assertIn("I looked at everything.", text)
        self.assertIn("timed out after 1 seconds", text)
        self.assertEqual(self.check(), (0, ""))

    # [RWE-HP-01] Resilient Verdict Parsing
    def test_rwe_hp_01_resilient_verdict_parsing(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude", mode="bold_verdict")
        self.assertEqual(code, 0)
        self.assertIn("- **Verdict**: PASS", self.text())
        self.assertIn("- **Status**: completed", self.text())

        self.commit("Record round 1")
        code2, _, _ = self.run_review(cli="claude", mode="heading_verdict")
        self.assertEqual(code2, 1)
        self.assertIn("- **Verdict**: CHANGES REQUIRED", self.text())
        self.assertIn("- **Status**: completed", self.text())

    # [RWE-EC-02] Verdict Whitespace and Case
    def test_rwe_ec_02_verdict_whitespace_and_case(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude", mode="case_verdict")
        self.assertEqual(code, 0)
        self.assertIn("- **Verdict**: PASS", self.text())
        self.assertIn("- **Status**: completed", self.text())

    # [RWE-EC-01] Conversational Summary Does Not Trigger Unparsed Blocking
    def test_rwe_ec_01_conversational_summary_does_not_trigger_unparsed_blocking(self) -> None:
        self.install("codex")
        code, _, _ = self.run_review(cli="codex", mode="prose_summary")
        self.assertEqual(code, 0)
        self.assertIn("- **Verdict**: PASS", self.text())
        self.assertIn("- **Status**: completed", self.text())
        self.assertNotIn("unparsed", self.text())

    # [RWE-HP-02] Finding lines match list items
    def test_rwe_hp_02_finding_lines_match_list_items(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude", mode="list_findings")
        self.assertEqual(code, 1)
        text = self.text()
        self.assertIn("| 1 | Critical | demo.en.md:1 | list bullet dash |  |", text)
        self.assertIn("| 2 | Important | demo.en.md:2 | list bullet star |  |", text)
        self.assertIn("| 3 | Minor | demo.en.md:3 | numbered list |  |", text)



    # [RWE-HP-03] Table cell sanitizes control characters
    def test_rwe_hp_03_cell_sanitizes_control_characters(self) -> None:
        from run_external_review import cell
        raw = "line 1\r\nline 2 | line 3\r"
        sanitized = cell(raw)
        self.assertEqual(sanitized, r"line 1 line 2 \| line 3")
        self.assertNotIn("\r", sanitized)
        self.assertNotIn("\n", sanitized)

    # [RWE-EC-03] Table findings row with multiple escaped pipes
    def test_rwe_ec_03_cell_handles_escaped_pipes(self) -> None:
        from run_external_review import render_round, table_findings
        meta = {"Status": "completed", "Verdict": "PASS"}
        findings = [("Minor", "src/file.py:10", "use a | b | c syntax")]
        round_md = render_round(1, meta, findings, "Verdict: PASS\n")
        rows = table_findings(round_md.splitlines())
        self.assertEqual(len(rows), 1)
        cells = rows[0][1]
        self.assertEqual(len(cells), 5)
        self.assertEqual(cells[2], "src/file.py:10")
        self.assertEqual(cells[3], "use a | b | c syntax")


    # [RWE-HP-04] Clean facts collection proceeds to CLI execution
    def test_rwe_hp_04_clean_facts_collection_proceeds_to_cli(self) -> None:
        self.install("claude")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 0)
        self.assertIn("[Pre-check]", err)
        self.assertIn("audit_epic.py", err)
        self.assertIn("Integration: true", err)
        self.assertIn("check_bdd_traceability.py", err)
        self.assertEqual(err.count("PASS"), 3)
        self.assertTrue(self.results.exists())
        self.assertIn("- **Status**: completed", self.text())
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("The audit of the epic branch, with its exit code:", prompt)
        self.assertIn("$ audit_epic.py", prompt)
        self.assertIn("The integration test commands and the result-based traceability check", prompt)
        self.assertIn("$ true", prompt)

    # [RWE-EC-04] Facts timeout separated from CLI timeout
    def test_rwe_ec_04_facts_timeout_separated_from_cli_timeout(self) -> None:
        self.install("codex")
        with mock.patch("run_external_review.execute") as mock_exec:
            mock_exec.side_effect = [
                (0, "audit passed", ""),       # audit_epic.py
                (0, "test passed", ""),        # integration test
                (0, "trace passed", ""),       # check_bdd_traceability.py
                (0, "Verdict: PASS\n", ""),    # codex CLI
            ]
            code, out, err = self.run_review("--facts-timeout", "45", "--timeout", "1200", cli="codex", mode="pass")
            self.assertEqual(code, 0)
            self.assertEqual(mock_exec.call_args_list[0][0][2], 45)
            self.assertEqual(mock_exec.call_args_list[1][0][2], 45)
            self.assertEqual(mock_exec.call_args_list[2][0][2], 45)
            self.assertEqual(mock_exec.call_args_list[3][0][2], 1200)

    # [RWE-FR-01] Fail-fast aborts on non-zero integration test exit
    def test_rwe_fr_01_fail_fast_aborts_on_integration_test_failure(self) -> None:
        self.install("claude")
        self.write(f"{EPIC}/demo.en.md", "# Demo\n\nIntegration test roots: scripts/\n\nIntegration results: false -> build/demo.xml\n")
        self.commit("HLD with failing test")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 2)
        self.assertIn("[PRECONDITION BLOCKED]", err)
        self.assertIn("CLAUDE CLI WAS NOT INVOKED (0 CREDITS USED)", err)
        self.assertIn("Failed Gate", err)
        self.assertIn("Integration: false", err)
        self.assertIn("failed with exit code 1", err)
        self.assertFalse(self.results.exists())

    # [RWE-FR-01] Fail-fast aborts on audit failure
    def test_rwe_fr_01_fail_fast_aborts_on_audit_failure(self) -> None:
        self.install("claude")
        # Mark task_1_demo done with a Verification section but without evidence to make audit_epic fail
        self.write(f"{EPIC}/task_1_demo.md", '---\nid: "task_1_demo"\nstatus: "done"\n---\n\n# Task 1\n\n## Verification\n\n| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n| V1 | GREEN | true | exit 0 | — |\n')
        self.commit("Task 1 done without evidence")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 2)
        self.assertIn("[PRECONDITION BLOCKED]", err)
        self.assertIn("audit_epic.py", err)
        self.assertFalse(self.results.exists())

    # [RWE-FR-02] Fail-fast aborts on test timeout
    def test_rwe_fr_02_fail_fast_aborts_on_test_timeout(self) -> None:
        self.install("claude")
        # Change HLD to have a sleeping integration test
        self.write(f"{EPIC}/demo.en.md", "# Demo\n\nIntegration test roots: scripts/\n\nIntegration results: sleep 5 -> build/demo.xml\n")
        self.commit("HLD with slow test")
        code, out, err = self.run_review("--facts-timeout", "1", cli="claude", mode="pass")
        self.assertEqual(code, 2)
        self.assertIn("[PRECONDITION BLOCKED]", err)
        self.assertIn("TIMEOUT (1s)", err)
        self.assertIn("timed out after 1 seconds", err)
        self.assertFalse(self.results.exists())

    def test_precheck_progress_prints_are_flushed_immediately(self) -> None:
        from run_external_review import run_gate

        with mock.patch("run_external_review.execute", return_value=(0, "ok", "")), \
                mock.patch("builtins.print") as print_mock:
            code, out, err = run_gate("demo gate", ["true"], self.root, 30)

        self.assertEqual((code, out, err), (0, "ok", ""))
        self.assertEqual(print_mock.call_count, 2)
        for call in print_mock.call_args_list:
            self.assertIs(call.kwargs["file"], sys.stderr)
            self.assertTrue(call.kwargs["flush"])
        self.assertEqual(print_mock.call_args_list[0].kwargs["end"], "")


    # [RWE-ST-01] Round transitions to check pass after decisions
    def test_rwe_st_01_round_transitions_to_check_pass_after_decisions(self) -> None:
        self.install("claude")
        self.assertEqual(self.run_review(cli="claude", mode="blocking")[0], 1)
        # Record decisions for both findings
        review_text = self.text()
        review_text = review_text.replace("| 1 | Critical | demo.en.md:3 | evidence missing |  |",
                                  "| 1 | Critical | demo.en.md:3 | evidence missing | fixed in abc1234 |")
        review_text = review_text.replace("| 2 | Important | task_1_demo.md:9 | row too weak |  |",
                                  "| 2 | Important | task_1_demo.md:9 | row too weak | dismissed: verified by V3 |")
        self.results.write_text(review_text, encoding="utf-8")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    # [RWE-ST-02] Undecided findings block check
    def test_rwe_st_02_undecided_findings_block_check(self) -> None:
        self.install("claude")
        self.assertEqual(self.run_review(cli="claude", mode="blocking")[0], 1)
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("undecided: #1 Critical demo.en.md:3", out)
        self.assertIn("undecided: #2 Important task_1_demo.md:9", out)


    # [RWE-HP-05] Full diff inlined when under line limit
    def test_rwe_hp_05_inlined_code_diff(self) -> None:
        self.install("claude")
        self.write("src/core.py", "def greet():\n    return 'hello'\n")
        self.commit("Add greet")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("## Code Changes (Diff)", prompt)
        self.assertIn("The complete source diff", prompt)
        self.assertIn("Do NOT run `git diff` again", prompt)
        self.assertIn("```diff", prompt)
        self.assertIn("+def greet():", prompt)

    # [RWE-EC-05] Fallback to diff stat when exceeding line limit
    def test_rwe_ec_05_diff_stat_fallback_when_exceeding_limit(self) -> None:
        self.install("codex")
        self.write("src/large.py", "\n".join(f"x_{i} = {i}" for i in range(10)) + "\n")
        self.commit("Add large file")
        code, out, err = self.run_review("--diff-limit", "3", cli="codex", mode="pass")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("## Code Changes (Diff)", prompt)
        self.assertIn("The source diff is large", prompt)
        self.assertIn("Full file change summary", prompt)
        self.assertIn("src/large.py", prompt)


    # [RWE-HP-05] Diff with raw dollar variables is safely substituted without Template crash
    def test_rwe_hp_05_diff_with_dollar_variables(self) -> None:
        self.install("claude")
        self.write("src/script.sh", "#!/bin/bash\necho \"$UNDEFINED_VAR\" > \"$OUTPUT_FILE\"\n")
        self.commit("Add bash script with dollars")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("$UNDEFINED_VAR", prompt)


    # Test lowercase severity is capitalized and triggers blocking
    def test_lowercase_severity_is_capitalized_and_blocks_run(self) -> None:
        self.install("claude")
        from run_external_review import parse_findings
        out = "Verdict: CHANGES REQUIRED\n- [critical] demo.en.md:1 — broken\n"
        findings = parse_findings(out)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0][0], "Critical")

    # Test list text with important without brackets does not trigger unparsed blocking
    def test_list_text_without_brackets_does_not_trigger_unparsed_blocking(self) -> None:
        from run_external_review import parse_findings
        out = "Verdict: PASS\n- Important context: this is good documentation\n"
        findings = parse_findings(out, "PASS")
        self.assertEqual(len(findings), 0)

    # Test fail-fast on traceability check failure
    def test_fail_fast_aborts_on_traceability_failure(self) -> None:
        self.install("claude")
        # Point to missing report in HLD
        self.write(f"{EPIC}/demo.en.md", "# Demo\n\nIntegration test roots: scripts/\n\nIntegration results: true -> build/nonexistent.xml\n")
        self.commit("HLD with missing report")
        code, out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 2)
        self.assertIn("[PRECONDITION BLOCKED]", err)
        self.assertIn("Failed Gate", err)
        self.assertIn("check_bdd_traceability.py", err)
        self.assertIn("failed with exit code 2", err)
        self.assertFalse(self.results.exists())

if __name__ == '__main__':
    unittest.main()
