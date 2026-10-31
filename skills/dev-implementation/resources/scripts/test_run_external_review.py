#!/usr/bin/env python3
"""Tests for run_external_review.py, on throwaway git repositories with fake claude and codex executables.

The fakes are the only claude and codex on PATH, so no test reaches a real CLI.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
import test_check_epic_readiness as tcer
from run_external_review import format_triage_header, load_review_config, main, save_review_config

EPIC = ".devtool/epic/demo"
TICKS = "`" * 3
FAKE = """#!/bin/bash
if [ -n "$FAKE_COUNTER" ]; then echo 1 >> "$FAKE_COUNTER"; fi
cat > "$FAKE_STDIN"
echo "$@" > "$FAKE_ARGS"
case "$FAKE_MODE" in
  pass) echo "Verdict: PASS" ;;
  minor) echo "Verdict: CHANGES REQUIRED"; echo "- [Minor] README.md:1 — wording | unclear" ;;
  blocking) echo "Verdict: CHANGES REQUIRED"
            echo "[Critical] demo.en.md:3 — evidence missing"
            echo "[Important] task_1_demo.md:9 — row too weak" ;;
  principal_changes) echo "Verdict: CHANGES REQUIRED"
                     echo "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult." ;;
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
            tool_path = shutil.which(tool)
            if tool_path is not None:
                (self.bin / tool).symlink_to(tool_path)
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
        self.assertEqual(self.args.read_text().split(), ["exec", "--sandbox", "read-only", "-c", "model_reasoning_effort=high", "--model", "gpt-test", "-"])
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
        self.assertEqual(self.args.read_text().split(), ["-p", "--dangerously-skip-permissions", "--effort", "high", "--model", "Opus", "5.5"])
        text = self.text()
        self.assertIn("- **Model**: Opus 5.5", text)
        self.assertIn("- **Thinking**: high", text)
        self.assertIn("| 1 | Minor | README.md:1 | wording \\| unclear |  |", text)
        self.assertEqual(self.check()[0], 0)

    def test_agy_review_round_is_recorded(self) -> None:
        self.install("agy")
        code, _, _ = self.run_review(cli="agy", mode="pass")
        self.assertEqual(code, 0)
        self.assertEqual(self.args.read_text().strip(), "--sandbox --mode plan --model Gemini 4 Argon (Medium)")
        text = self.text()
        self.assertIn("- **CLI**: agy", text)
        self.assertIn("- **Model**: Gemini 4 Argon (Medium)", text)
        self.assertEqual(self.check()[0], 0)

    def test_agy_review_custom_model(self) -> None:
        self.install("agy")
        code, _, _ = self.run_review("--model", "gemini-4-argon-high", cli="agy", mode="pass")
        self.assertEqual(code, 0)
        self.assertEqual(self.args.read_text().split(), ["--sandbox", "--mode", "plan", "--model", "gemini-4-argon-high"])
        text = self.text()
        self.assertIn("- **CLI**: agy", text)
        self.assertIn("- **Model**: gemini-4-argon-high", text)

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
        code, _out, err = self.run_review(cli="claude", mode="pass")
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
            code, _out, _err = self.run_review("--facts-timeout", "45", "--timeout", "1200", cli="codex", mode="pass")
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
        code, _out, err = self.run_review(cli="claude", mode="pass")
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
        code, _out, err = self.run_review(cli="claude", mode="pass")
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
        code, _out, err = self.run_review("--facts-timeout", "1", cli="claude", mode="pass")
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
        code, _out, _err = self.run_review(cli="claude", mode="pass")
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
        code, _out, _err = self.run_review("--diff-limit", "3", cli="codex", mode="pass")
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
        code, _out, _err = self.run_review(cli="claude", mode="pass")
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
        code, _out, err = self.run_review(cli="claude", mode="pass")
        self.assertEqual(code, 2)
        self.assertIn("[PRECONDITION BLOCKED]", err)
        self.assertIn("Failed Gate", err)
        self.assertIn("check_bdd_traceability.py", err)
        self.assertIn("failed with exit code 2", err)
        self.assertFalse(self.results.exists())

class PrincipalReviewTest(ReviewCase):
    def setUp(self) -> None:
        super().setUp()
        tcer.build_ready_epic(self.root)
        self.commit("Ready epic")
        self.principal_results = self.root / ".devtool" / "epic" / "demo_epic" / "principal_review.md"

    def run_principal(self, *extra: str, cli: str = "claude", mode: str = "pass") -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_MODE": mode}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--kind", "principal", "--epic-dir", "demo_epic", "--base", "main", "--cli", cli, *extra])
        return code, out.getvalue(), err.getvalue()

    def test_srs_hp_01_principal_round_recorded_in_principal_review_md(self) -> None:
        """[SRS-HP-01] A principal round is recorded in principal_review.md."""
        self.install("claude")
        code, out, err = self.run_principal()
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nOut:\n{out}\nErr:\n{err}")
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("Principal Reviewer", prompt)
        self.assertIn("Result: 0 FAIL, 0 WARN — PASS", prompt)
        self.assertIn(".devtool/epic/demo_epic/demo_epic.en.md", prompt)
        main_sha = git(self.root, "rev-parse", "main")
        self.assertIn(main_sha, prompt)
        self.assertNotIn("audit_epic.py", prompt)

        self.assertTrue(self.principal_results.is_file(), "principal_review.md should exist")
        text = self.principal_results.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Principal Review: demo_epic\n"))
        self.assertIn("## Round 1", text)
        self.assertIn("- **Kind**: principal", text)
        self.assertIn("- **CLI**: claude", text)
        self.assertIn("- **Status**: completed", text)
        self.assertIn("- **Verdict**: PASS", text)
        self.assertFalse((self.root / ".devtool" / "epic" / "demo_epic" / "review_results.md").exists())

    def test_prv_hp_03_findings_with_proposed_edits_become_table_rows(self) -> None:
        """PRV-HP-03: Findings with proposed edits become table rows and set exit code."""
        self.install("codex")
        code, out, err = self.run_principal(cli="codex", mode="principal_changes")
        self.assertEqual(code, 1, f"Expected 1, got {code}.\nOut:\n{out}\nErr:\n{err}")
        text = self.principal_results.read_text(encoding="utf-8")
        self.assertIn("- **Verdict**: CHANGES REQUIRED", text)
        self.assertIn("| Important |", text)
        self.assertIn("task_2:Decisions Already Made", text)
        self.assertIn("Proposed: keep TrackPersistResult.", text)

    def test_agy_principal_review_recorded(self) -> None:
        self.install("agy")
        code, out, err = self.run_principal(cli="agy", mode="pass")
        self.assertEqual(code, 0, f"Expected 0, got {code}.\nOut:\n{out}\nErr:\n{err}")
        self.assertEqual(self.args.read_text().strip(), "--sandbox --mode plan --model Gemini 4 Argon (Medium)")
        text = self.principal_results.read_text(encoding="utf-8")
        self.assertIn("- **CLI**: agy", text)
        self.assertIn("- **Model**: Gemini 4 Argon (Medium)", text)
        self.assertIn("- **Verdict**: PASS", text)

    def test_srs_st_01_decisions_move_check_from_1_to_0(self) -> None:
        """[SRS-ST-01] Decisions move check --kind principal from 1 to 0, independent of code rounds."""
        self.install("claude")
        code, _, _ = self.run_principal(mode="principal_changes")
        self.assertEqual(code, 1)

        # Code review results with no findings (clean round)
        code_rev_path = self.root / ".devtool" / "epic" / "demo_epic" / "review_results.md"
        code_rev_path.write_text(
            "# Cross-Model Review: demo_epic\n\n## Round 1\n\n- **Status**: completed\n- **Verdict**: PASS\n\n"
            "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n\n"
            "Raw output:\n\n```text\nVerdict: PASS\n```\n",
            encoding="utf-8",
        )

        # check --kind principal exits 1
        out1 = io.StringIO()
        with contextlib.redirect_stdout(out1):
            c1 = main(["check", "--kind", "principal", "--epic-dir", "demo_epic"])
        self.assertEqual(c1, 1)
        self.assertIn("undecided: #1 Important", out1.getvalue())

        # check without --kind exits 0
        out_code = io.StringIO()
        with contextlib.redirect_stdout(out_code):
            c_code = main(["check", "--epic-dir", "demo_epic"])
        self.assertEqual(c_code, 0)

        # Update decision cell
        pr_text = self.principal_results.read_text(encoding="utf-8")
        pr_text = pr_text.replace("|  |\n", "| fixed in abc1234 |\n")
        self.principal_results.write_text(pr_text, encoding="utf-8")

        # check --kind principal now exits 0
        out2 = io.StringIO()
        with contextlib.redirect_stdout(out2):
            c2 = main(["check", "--kind", "principal", "--epic-dir", "demo_epic"])
        self.assertEqual(c2, 0)

    def test_prv_st_02_triage_reads_selected_file(self) -> None:
        """PRV-ST-02: triage reads the file --kind selects."""
        # principal_review.md with 2 rounds
        self.principal_results.write_text(
            "# Principal Review: demo_epic\n\n"
            "## Round 1\n\n- **Status**: completed\n- **Verdict**: PASS\n\n"
            "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n\n"
            "Raw output:\n\n```text\nVerdict: PASS\n```\n\n"
            "## Round 2\n\n- **Status**: completed\n- **Verdict**: PASS\n\n"
            "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n\n"
            "Raw output:\n\n```text\nVerdict: PASS\n```\n",
            encoding="utf-8",
        )
        # review_results.md with 1 round
        code_rev_path = self.root / ".devtool" / "epic" / "demo_epic" / "review_results.md"
        code_rev_path.write_text(
            "# Cross-Model Review: demo_epic\n\n"
            "## Round 1\n\n- **Status**: completed\n- **Verdict**: PASS\n\n"
            "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n\n"
            "Raw output:\n\n```text\nVerdict: PASS\n```\n",
            encoding="utf-8",
        )

        out_pr = io.StringIO()
        with contextlib.redirect_stdout(out_pr):
            c_pr = main(["triage", "--kind", "principal", "--epic-dir", "demo_epic"])
        self.assertEqual(c_pr, 0)
        self.assertTrue(out_pr.getvalue().startswith("# Review Triage: demo_epic, Round 2"))

        out_code = io.StringIO()
        with contextlib.redirect_stdout(out_code):
            c_code = main(["triage", "--epic-dir", "demo_epic"])
        self.assertEqual(c_code, 0)
        self.assertIn("Round 1", out_code.getvalue())

        err_missing = io.StringIO()
        with contextlib.redirect_stderr(err_missing):
            c_missing = main(["triage", "--kind", "principal", "--epic-dir", "nonexistent"])
        self.assertEqual(c_missing, 2)
        self.assertIn("no review round recorded for nonexistent", err_missing.getvalue())

    def test_prv_ar_01_second_round_before_commit_refused(self) -> None:
        """PRV-AR-01: A second round before the first is committed is refused and rounds number in order."""
        self.install("claude")
        counter = self.bin.parent / "fake_counter.txt"
        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
            code1, _, _ = self.run_principal()
            self.assertEqual(code1, 0)
            self.assertEqual(len(counter.read_text().splitlines()), 1)

            # Round 1 is written but uncommitted
            code2, _, err2 = self.run_principal()
            self.assertEqual(code2, 2)
            self.assertIn("commit or stash your changes before a review", err2)
            self.assertEqual(len(counter.read_text().splitlines()), 1)

            # Commit round 1
            self.commit("Record round 1")

            # Run again
            code3, _, _ = self.run_principal()
            self.assertEqual(code3, 0)
            self.assertEqual(len(counter.read_text().splitlines()), 2)

            text = self.principal_results.read_text(encoding="utf-8")
            self.assertIn("## Round 1", text)
            self.assertIn("## Round 2", text)
            self.assertTrue(text.index("## Round 1") < text.index("## Round 2"))

    def test_srs_fr_01_readiness_fail_blocks_cli(self) -> None:
        """[SRS-FR-01] A readiness FAIL blocks the CLI and records nothing."""
        # Break readiness: make task_2 fail R5 by adding a missing symbol
        (self.root / "src").mkdir(parents=True, exist_ok=True)
        (self.root / "src" / "app.py").write_text("def other(): pass\n", encoding="utf-8")
        task_2_path = self.root / ".devtool" / "epic" / "demo_epic" / "task_2.md"
        t2_text = task_2_path.read_text(encoding="utf-8").replace(
            "- **Target Files & Symbols**:\n  - `tool.py`: `run`",
            "- **Target Files & Symbols**:\n  - `tool.py`: `run`\n  - `src/app.py`: `build_payload()`",
        )
        task_2_path.write_text(t2_text, encoding="utf-8")
        (self.root / ".devtool" / "features" / "task_2.md").write_text(
            t2_text.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)"),
            encoding="utf-8",
        )
        self.commit("Break R5 readiness")

        self.install("claude")
        counter = self.bin.parent / "fake_counter.txt"
        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
            code, _out, err = self.run_principal()
            self.assertEqual(code, 2)
            self.assertIn("WAS NOT INVOKED", err)
            self.assertIn("check_epic_readiness.py", err)
            self.assertIn("R5 FAIL", err)
            self.assertFalse(counter.exists())
            self.assertFalse(self.principal_results.exists())

    def test_prv_fr_04_ollama_rejected_before_precheck(self) -> None:
        """PRV-FR-04: --kind principal --cli ollama is rejected before any work."""
        (self.root / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--kind", "principal", "--epic-dir", "demo_epic", "--base", "main", "--cli", "ollama", "--model", "m"])
        self.assertEqual(code, 2)
        self.assertIn("--kind principal supports --cli claude, codex, or agy", err.getvalue())
        self.assertNotIn("[Pre-check]", err.getvalue())
        self.assertFalse(self.principal_results.exists())


class TestPrincipalReviewDocMode(ReviewCase):
    def setUp(self) -> None:
        super().setUp()
        self.doc_path = self.root / "docs" / "rfc" / "feature-architecture.md"
        self.doc_path.parent.mkdir(parents=True, exist_ok=True)
        self.doc_path.write_text(
            "# RFC: Feature Architecture\n\n## Overview\nThis is a sample design document.\n\n"
            "## Architecture\nDetails here.\n",
            encoding="utf-8",
        )
        self.commit("Add RFC document")

    def test_srs_ec_01_doc_mode_missing_document_refuses(self) -> None:
        """[SRS-EC-01] Missing standalone document refuses without calling CLI."""
        self.install("claude")
        counter = self.bin.parent / "fake_counter.txt"
        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(["run", "--kind", "principal", "--doc", "docs/rfc/missing-doc.md", "--base", "main", "--cli", "claude"])
            self.assertEqual(code, 2)
            self.assertIn("docs/rfc/missing-doc.md", err.getvalue())
            self.assertFalse(counter.exists())

    def test_srs_ec_04_doc_mode_broken_structure_refuses(self) -> None:
        """[SRS-EC-04] Broken standalone document formatting refuses before CLI invocation."""
        broken = self.root / "docs" / "rfc" / "broken.md"
        broken.write_text("   \n\n", encoding="utf-8")
        self.commit("Add broken document")

        self.install("claude")
        counter = self.bin.parent / "fake_counter.txt"
        with mock.patch.dict(os.environ, {"FAKE_COUNTER": str(counter)}):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(["run", "--kind", "principal", "--doc", "docs/rfc/broken.md", "--base", "main", "--cli", "claude"])
            self.assertEqual(code, 2)
            self.assertIn("docs/rfc/broken.md", err.getvalue())
            self.assertFalse(counter.exists())

    def test_srs_hp_02_doc_mode_successful_run_streams_triage_table(self) -> None:
        """[SRS-HP-02] Ad-hoc principal review validates and streams triage table to stdout."""
        self.install("claude")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_MODE": "pass"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--kind", "principal", "--doc", "docs/rfc/feature-architecture.md", "--base", "main", "--cli", "claude"])
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("Review Triage", output)
        self.assertIn("Verdict", output)
        self.assertIn("PASS", output)
        prompt = self.stdin.read_text(encoding="utf-8")
        self.assertIn("docs/rfc/feature-architecture.md", prompt)
        self.assertIn("RFC: Feature Architecture", prompt)
        # Verify no principal_review.md was created
        self.assertFalse((self.root / ".devtool" / "epic" / "demo" / "principal_review.md").exists())
        self.assertFalse((self.root / "principal_review.md").exists())


class TestCrossModelReviewAdhoc(ReviewCase):
    def test_srs_hp_03_in_lifecycle_cross_model_review(self) -> None:
        """[SRS-HP-03] In-lifecycle cross-model review evaluates diff against base and records round."""
        self.install("claude")
        code, _out, _err = self.run_review(cli="claude")
        self.assertEqual(code, 0)
        self.assertTrue(self.results.exists())
        text = self.results.read_text(encoding="utf-8")
        self.assertIn("## Round 1", text)
        self.assertIn("- **CLI**: claude", text)
        self.assertIn("- **Verdict**: PASS", text)

    def test_srs_hp_04_adhoc_branch_diff_streams_triage(self) -> None:
        """[SRS-HP-04] Ad-hoc cross-model review evaluates git branch diff and streams triage to stdout."""
        self.install("claude")
        self.write("src/service.py", "def process(): return True\n")
        self.commit("Add service")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"FAKE_MODE": "pass"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--base", "main", "--cli", "claude"])
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("Review Triage", output)
        self.assertIn("Verdict", output)
        self.assertIn("PASS", output)
        # Ad-hoc does not write review_results.md
        adhoc_results = self.root / "review_results.md"
        self.assertFalse(adhoc_results.exists())

    def test_srs_hp_05_local_model_review_invocation(self) -> None:
        """[SRS-HP-05] Local model review invokes runner with --cli ollama and records round."""
        with mock.patch("local_review.probe", return_value=32768), \
                mock.patch("local_review.chat", return_value=mock.Mock(error=None, content="Verdict: PASS", done_reason="stop")):
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(["run", "--epic-dir", "demo", "--base", self.base, "--cli", "ollama", "--model", "qwen2.5-coder:32b"])
            self.assertEqual(code, 0)
            text = self.results.read_text(encoding="utf-8")
            self.assertIn("## Round 1", text)
            self.assertIn("- **CLI**: ollama", text)
            self.assertIn("- **Model**: qwen2.5-coder:32b", text)

    def test_srs_ec_02_cross_model_refuses_dirty_tree(self) -> None:
        """[SRS-EC-02] Cross-model review refuses execution on dirty working tree."""
        self.install("claude")
        self.write("dirty_file.txt", "untracked content")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--base", "main", "--cli", "claude"])
        self.assertEqual(code, 2)
        self.assertIn("commit or stash your changes before a review", err.getvalue())

    def test_srs_ec_03_missing_external_cli_guidance(self) -> None:
        """[SRS-EC-03] Missing external CLI triggers error guidance without crashing."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--epic-dir", "demo", "--base", self.base, "--cli", "claude"])
        self.assertEqual(code, 2)
        self.assertIn("claude not found on PATH", err.getvalue())

    def test_srs_st_02_fix_loop_enforces_gate_4_reverification(self) -> None:
        """[SRS-ST-02] Cross-model review check reports undecided blocking findings until decisions are recorded."""
        self.install("claude")
        code, _, _ = self.run_review(cli="claude", mode="blocking")
        self.assertEqual(code, 1)
        check_code, check_out = self.check()
        self.assertEqual(check_code, 1)
        self.assertIn("undecided: #1 Critical demo.en.md:3", check_out)

        # Record decision
        text = self.results.read_text(encoding="utf-8")
        fixed = text.replace(
            "| 1 | Critical | demo.en.md:3 | evidence missing |  |",
            "| 1 | Critical | demo.en.md:3 | evidence missing | fixed in abc1234 |",
        ).replace(
            "| 2 | Important | task_1_demo.md:9 | row too weak |  |",
            "| 2 | Important | task_1_demo.md:9 | row too weak | dismissed: not an issue |",
        )
        self.results.write_text(fixed, encoding="utf-8")
        check_code_after, check_out_after = self.check()
        self.assertEqual(check_code_after, 0)
        self.assertEqual(check_out_after.strip(), "")

    def test_srs_ar_01_streaming_timeout_clean_termination(self) -> None:
        """[SRS-AR-01] Slow CLI triggers timeout, terminates process, and records timeout."""
        self.install("claude")
        code, _, _err = self.run_review("--timeout", "1", cli="claude", mode="slow")
        self.assertEqual(code, 2)
        self.assertTrue(self.results.exists())
        text = self.results.read_text(encoding="utf-8")
        self.assertIn("timed out after 1 seconds", text)
        self.assertIn("- **Status**: no verdict", text)

    def test_srs_ar_02_sequential_round_numbering(self) -> None:
        """[SRS-AR-02] Sequential round numbering increments strictly without collision."""
        self.install("claude")
        self.run_review(cli="claude", mode="pass")
        self.commit("Round 1 commit")
        self.run_review(cli="claude", mode="pass")
        text = self.results.read_text(encoding="utf-8")
        self.assertIn("## Round 1", text)
        self.assertIn("## Round 2", text)
        self.assertTrue(text.index("## Round 1") < text.index("## Round 2"))

    def test_srs_fr_02_triage_isolates_malformed_response(self) -> None:
        """[SRS-FR-02] Triage isolates unparsed blocking lines gracefully."""
        self.install("claude")
        self.run_review(cli="claude", mode="formats")
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["triage", "--epic-dir", "demo"])
        self.assertEqual(code, 0)
        self.assertIn("## Findings", out.getvalue())
        self.assertIn("demo.en.md:3", out.getvalue())


class TestReviewConfigAndHeader(ReviewCase):
    def test_rts_hp_01_standardized_4_bullet_header_in_triage(self) -> None:
        """[RTS-HP-01] Triage output strictly includes the 4 standardized bullet lines."""
        self.install("codex")
        self.run_review(cli="codex", mode="pass")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["triage", "--epic-dir", "demo"])
        self.assertEqual(code, 0)
        output = out.getvalue()
        self.assertIn("# Review Triage: demo, Round 1", output)
        self.assertIn("• Candidate SHA:", output)
        self.assertIn("• Reviewer: Codex ( gpt-6.1-sol )", output)
        self.assertIn("• Thinking Level: High", output)
        self.assertIn("• Verdict: PASS (0 findings)", output)

    def test_rts_hp_02_canonical_defaults_auto_seeded(self) -> None:
        """[RTS-HP-02] Canonical provider defaults are automatically seeded when config is missing."""
        config_path = self.root / ".devtool" / "review_config.json"
        if config_path.exists():
            config_path.unlink()
        cfg = load_review_config(self.root)
        self.assertEqual(cfg["last_used_provider"], "codex")
        self.assertEqual(cfg["providers"]["codex"]["model"], "gpt-6.1-sol")
        self.assertEqual(cfg["providers"]["codex"]["thinking_level"], "high")
        self.assertEqual(cfg["providers"]["claude"]["model"], "Opus 5.5")
        self.assertEqual(cfg["providers"]["claude"]["thinking_level"], "high")
        self.assertEqual(cfg["providers"]["agy"]["model"], "Gemini 4 Argon (Medium)")
        self.assertEqual(cfg["providers"]["agy"]["thinking_level"], "medium")
        self.assertEqual(cfg["providers"]["ollama"]["model"], "qwen38-fast:latest")
        self.assertEqual(cfg["providers"]["ollama"]["thinking_level"], "high")

    def test_rts_hp_03_sticky_memory_updates_on_subsequent_runs(self) -> None:
        """[RTS-HP-03] Sticky memory updates provider preferences upon execution."""
        self.install("claude")
        code, _, _ = self.run_review(
            "--thinking-level", "medium",
            "--model", "custom-claude",
            cli="claude",
            mode="pass",
        )
        self.assertEqual(code, 0)
        config_path = self.root / ".devtool" / "review_config.json"
        self.assertTrue(config_path.exists())
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(config["last_used_provider"], "claude")
        self.assertEqual(config["providers"]["claude"]["model"], "custom-claude")
        self.assertEqual(config["providers"]["claude"]["thinking_level"], "medium")
        self.assertEqual(config["providers"]["codex"]["model"], "gpt-6.1-sol")

    def test_rts_hp_04_thinking_level_translates_to_cli_flags(self) -> None:
        """[RTS-HP-04] Thinking level translates to provider-specific CLI flags."""
        self.install("codex")
        self.run_review("--thinking-level", "low", cli="codex", mode="pass")
        self.assertIn("-c model_reasoning_effort=low", self.args.read_text())
        self.commit("Round 1")
        self.install("claude")
        self.run_review("--thinking-level", "extra-high", cli="claude", mode="pass")
        args = self.args.read_text().split()
        self.assertIn("--effort", args)
        self.assertIn("xhigh", args)

    def test_rts_hp_05_claude_dangerously_skip_permissions(self) -> None:
        """[RTS-HP-05] Claude CLI uses --dangerously-skip-permissions."""
        self.install("claude")
        self.run_review(cli="claude", mode="pass")
        args = self.args.read_text().split()
        self.assertIn("--dangerously-skip-permissions", args)
        self.assertNotIn("--permission-mode", args)

    def test_rts_hp_06_dynamic_probing_and_senior_rules_in_prompts(self) -> None:
        """[RTS-HP-06] Prompts contain Mandatory Dynamic Probing Rule and senior reviewer checklist."""
        from run_external_review import PROMPT, RULES, principal_prompt_path, principal_rules_path
        ext_prompt = PROMPT.read_text(encoding="utf-8")
        ext_rules = RULES.read_text(encoding="utf-8")
        pr_prompt = principal_prompt_path().read_text(encoding="utf-8")
        pr_rules = principal_rules_path().read_text(encoding="utf-8")
        for p in (ext_prompt, pr_prompt):
            self.assertIn("Mandatory Dynamic Probing Rule", p)
        for r in (ext_rules, pr_rules):
            self.assertIn("5-Layer Deep Verification Checklist", r)

    def test_rts_ec_01_ollama_requires_model_without_previous_round(self) -> None:
        """[RTS-EC-01] Ollama requires explicit --model if no previous round exists."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["run", "--epic-dir", "demo", "--base", self.base, "--cli", "ollama"])
        self.assertEqual(code, 2)
        self.assertIn("--cli ollama needs --model", err.getvalue())

    def test_rts_ec_02_corrupted_config_falls_back_to_defaults(self) -> None:
        """[RTS-EC-02] Corrupted review_config.json falls back cleanly to defaults."""
        config_path = self.root / ".devtool" / "review_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text("{broken json...", encoding="utf-8")
        cfg = load_review_config(self.root)
        self.assertEqual(cfg["last_used_provider"], "codex")
        self.assertEqual(cfg["providers"]["codex"]["model"], "gpt-6.1-sol")

    def test_rts_ec_03_zero_findings_in_verdict(self) -> None:
        """[RTS-EC-03] Zero findings in review verdict displays 0 findings."""
        lines = format_triage_header("Title", "abc1234", "codex", "gpt-6.1-sol", "high", "PASS", [])
        self.assertIn("• Verdict: PASS (0 findings)", lines)

    def test_rts_st_01_provider_switching_preserves_distinct_memory(self) -> None:
        """[RTS-ST-01] Switching providers preserves each provider's distinct preferences."""
        self.install("claude")
        self.install("codex")
        self.run_review("--model", "custom-claude", "--thinking-level", "low", cli="claude", mode="pass")
        self.commit("Round 1")
        self.run_review("--model", "custom-codex", "--thinking-level", "high", cli="codex", mode="pass")
        self.commit("Round 2")
        cfg = load_review_config(self.root)
        self.assertEqual(cfg["last_used_provider"], "codex")
        self.assertEqual(cfg["providers"]["claude"]["model"], "custom-claude")
        self.assertEqual(cfg["providers"]["claude"]["thinking_level"], "low")
        self.assertEqual(cfg["providers"]["codex"]["model"], "custom-codex")
        self.assertEqual(cfg["providers"]["codex"]["thinking_level"], "high")

    def test_rts_st_02_incomplete_round_reflects_status(self) -> None:
        """[RTS-ST-02] Incomplete review round appends - **Status** in triage."""
        self.install("codex")
        self.run_review(cli="codex", mode="fail")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["triage", "--epic-dir", "demo"])
        self.assertEqual(code, 0)
        self.assertIn("- **Status**:", out.getvalue())

    def test_rts_ar_01_atomic_config_write(self) -> None:
        """[RTS-AR-01] Atomic write replaces .tmp file cleanly."""
        cfg = {"last_used_provider": "codex", "providers": {}}
        save_review_config(self.root, cfg)
        config_path = self.root / ".devtool" / "review_config.json"
        self.assertTrue(config_path.exists())
        self.assertFalse(config_path.with_suffix(".tmp").exists())
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["last_used_provider"], "codex")

    def test_rts_fr_01_tree_changes_aborts_on_mutation(self) -> None:
        """[RTS-FR-01] tree_changes detects modified paths when reviewer mutates repo."""
        from run_external_review import tree_changes, status_lines, head_of
        before = status_lines(self.root)
        sha = head_of(self.root)
        (self.root / "mutated.txt").write_text("mutation", encoding="utf-8")
        changed = tree_changes(self.root, before, sha)
        self.assertTrue(any("mutated.txt" in c for c in changed))

    def test_rts_fr_02_unknown_thinking_level_defaults_to_high(self) -> None:
        """[RTS-FR-02] Unknown or None thinking level defaults safely to high."""
        from run_external_review import effective_thinking_level
        self.assertEqual(effective_thinking_level("codex", None), "high")
        self.assertEqual(effective_thinking_level("codex", "custom"), "custom")


if __name__ == '__main__':
    unittest.main()

