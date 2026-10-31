#!/usr/bin/env python3
"""Unit tests for refresh_session.py engine and CLI commands."""

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path to import refresh_session
sys.path.insert(0, str(Path(__file__).parent))

import refresh_session


class TestRefreshSession(unittest.TestCase):
    def test_parse_arguments_default(self) -> None:
        """Target defaults to 'all', timeout to 60, json to False."""
        args = refresh_session.parse_args([])
        self.assertEqual(args.target, "all")
        self.assertEqual(args.timeout, 60)
        self.assertFalse(args.json)

    def test_parse_arguments_targets(self) -> None:
        """Parses valid target arguments: claude, codex, and all."""
        for target in ("claude", "codex", "all"):
            args = refresh_session.parse_args([target])
            self.assertEqual(args.target, target)

    def test_parse_arguments_options(self) -> None:
        """Parses optional --timeout and --json flags."""
        args = refresh_session.parse_args(["claude", "--timeout", "30", "--json"])
        self.assertEqual(args.target, "claude")
        self.assertEqual(args.timeout, 30)
        self.assertTrue(args.json)

    def test_parse_arguments_invalid_target(self) -> None:
        """Rejects unknown target choices."""
        import io
        from contextlib import redirect_stderr

        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            refresh_session.parse_args(["unknown-cli"])

    def test_build_claude_command(self) -> None:
        """Builds sandboxed Claude command with zero-skill flags and model haiku."""
        cmd = refresh_session.build_claude_command(prompt="1", model="haiku")
        expected = [
            "claude",
            "--safe-mode",
            "--disable-slash-commands",
            "--tools",
            "",
            "--model",
            "haiku",
            "-p",
            "1",
        ]
        self.assertEqual(cmd, expected)

    def test_build_codex_command(self) -> None:
        """Builds sandboxed Codex command disabling plugins, apps, hooks, and rules."""
        cmd = refresh_session.build_codex_command(prompt="1", reasoning_effort="low")
        expected = [
            "codex",
            "exec",
            "--disable",
            "plugins",
            "--disable",
            "apps",
            "--disable",
            "hooks",
            "--ephemeral",
            "--skip-git-repo-check",
            "--ignore-user-config",
            "--ignore-rules",
            "-c",
            "model_reasoning_effort=low",
            "1",
        ]
        self.assertEqual(cmd, expected)

    def test_extract_token_usage(self) -> None:
        """Extracts token usage integer from typical CLI outputs."""
        codex_output = "OpenAI Codex v0.162.1\nuser\n1\ncodex\nHello\ntokens used\n1,695\n"
        self.assertEqual(refresh_session.extract_tokens(codex_output), 1695)

        alt_output = "Summary\nTokens: 42\nDone"
        self.assertEqual(refresh_session.extract_tokens(alt_output), 42)

        no_tokens = "Simple response with no token metadata"
        self.assertIsNone(refresh_session.extract_tokens(no_tokens))

    @patch("shutil.which", return_value=None)
    def test_run_ping_missing_cli(self, mock_which: MagicMock) -> None:
        """Gracefully reports SKIPPED when target executable is missing from PATH."""
        res = refresh_session.ping_cli("claude")
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "SKIPPED")
        self.assertIn("not found in PATH", res.get("error", ""))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run")
    def test_run_ping_claude_success_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Successfully executes Claude in a clean temp directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=0,
            stdout="Hi! Ready to help.\ntokens used\n25\n",
            stderr="",
        )
        res = refresh_session.ping_cli("claude", timeout=10)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["tokens"], 25)
        self.assertGreaterEqual(res["latency_ms"], 0.0)
        self.assertIsNone(res.get("error"))

        # Verify cwd was set to a temporary directory outside current repository
        cwd_arg = mock_run.call_args[1].get("cwd")
        self.assertIsNotNone(cwd_arg)
        self.assertFalse(str(cwd_arg).startswith(str(Path.cwd())))

    @patch("shutil.which", return_value="/opt/homebrew/bin/codex")
    @patch("subprocess.run")
    def test_run_ping_codex_success_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Successfully executes Codex in a clean temp directory."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["codex"],
            returncode=0,
            stdout="codex\nOK\ntokens used\n1,697\n",
            stderr="",
        )
        res = refresh_session.ping_cli("codex", timeout=10)
        self.assertEqual(res["cli"], "codex")
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["tokens"], 1697)
        self.assertIsNone(res.get("error"))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd=["claude"], timeout=5))
    def test_run_ping_timeout_mocked(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Reports TIMEOUT and status FAIL on subprocess timeout."""
        res = refresh_session.ping_cli("claude", timeout=5)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("Timed out", res.get("error", ""))

    @patch("shutil.which", return_value="/opt/homebrew/bin/claude")
    @patch("subprocess.run")
    def test_run_ping_error_exit(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        """Reports FAIL when subprocess exits with non-zero returncode."""
        mock_run.return_value = subprocess.CompletedProcess(
            args=["claude"],
            returncode=1,
            stdout="",
            stderr="Authentication required",
        )
        res = refresh_session.ping_cli("claude", timeout=10)
        self.assertEqual(res["cli"], "claude")
        self.assertEqual(res["status"], "FAIL")
        self.assertIn("Authentication required", res.get("error", ""))

    @patch("refresh_session.ping_cli")
    def test_main_json_output(self, mock_ping: MagicMock) -> None:
        """Formats output as structured JSON on --json flag."""
        mock_ping.return_value = {
            "cli": "claude",
            "status": "PASS",
            "latency_ms": 1250.0,
            "tokens": 25,
            "error": None,
        }
        import io
        from contextlib import redirect_stdout

        out = io.StringIO()
        with redirect_stdout(out):
            code = refresh_session.main(["claude", "--json"])

        self.assertEqual(code, 0)
        data = json.loads(out.getvalue())
        self.assertIn("results", data)
        self.assertEqual(data["overall_status"], "PASS")
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["cli"], "claude")


if __name__ == "__main__":
    unittest.main()
