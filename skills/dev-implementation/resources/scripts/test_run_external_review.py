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
  fail) echo "credit balance is too low"; exit 1 ;;
  silent) echo "I looked at everything." ;;
  slow) sleep 30 ;;
  modify) echo changed > DEMO-created.txt; echo "Verdict: PASS" ;;
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
