#!/usr/bin/env python3
"""Standalone script to ping Claude Code and Codex CLIs to refresh 5-hour rolling session windows.

Enforces zero skill initialization, zero workspace context, and minimum token consumption
by executing strictly inside an ephemeral isolated temporary directory.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

SUPPORTED_TARGETS = ("claude", "codex", "all")


def build_claude_command(prompt: str = "1", model: str = "haiku") -> list[str]:
    """Construct minimal sandboxed Claude Code CLI command.

    Disables CLAUDE.md, skills, plugins, tools, and hooks while preserving OAuth auth.
    """
    return [
        "claude",
        "--safe-mode",
        "--disable-slash-commands",
        "--tools",
        "",
        "--model",
        model,
        "-p",
        prompt,
    ]


def build_codex_command(prompt: str = "1", reasoning_effort: str = "low") -> list[str]:
    """Construct minimal sandboxed Codex CLI command.

    Bypasses git repository checks, user configs, plugins, and custom rules.
    """
    return [
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
        f"model_reasoning_effort={reasoning_effort}",
        prompt,
    ]


def extract_tokens(output: str) -> int | None:
    """Extract token count from CLI output if reported."""
    patterns = [
        r"tokens used\s*\n\s*([0-9,]+)",
        r"(?:Tokens|tokens):\s*([0-9,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            clean_str = match.group(1).replace(",", "")
            try:
                return int(clean_str)
            except ValueError:
                pass
    return None


def ping_cli(cli_name: str, timeout: int = 60) -> dict[str, Any]:
    """Execute sandboxed minimal ping against the specified CLI inside an ephemeral directory.

    Returns a standardized dictionary matching:
    {"cli": str, "status": "PASS" | "SKIPPED" | "FAIL", "latency_ms": float, "tokens": int | None, "error": str | None}
    """
    result: dict[str, Any] = {
        "cli": cli_name,
        "status": "FAIL",
        "latency_ms": 0.0,
        "tokens": None,
        "error": None,
    }

    executable = shutil.which(cli_name)
    if not executable:
        result["status"] = "SKIPPED"
        result["error"] = f"Executable '{cli_name}' not found in PATH."
        return result

    if cli_name == "claude":
        cmd = build_claude_command(prompt="1", model="haiku")
    elif cli_name == "codex":
        cmd = build_codex_command(prompt="1", reasoning_effort="low")
    else:
        result["error"] = f"Unsupported CLI '{cli_name}'."
        return result

    start_time = time.perf_counter()
    with tempfile.TemporaryDirectory() as sandbox_dir:
        try:
            proc = subprocess.run(
                cmd,
                cwd=sandbox_dir,
                capture_output=True,
                check=False,
                text=True,
                timeout=timeout,
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)

            combined_output = (proc.stdout or "") + "\n" + (proc.stderr or "")
            tokens = extract_tokens(combined_output)
            result["tokens"] = tokens

            if proc.returncode == 0:
                result["status"] = "PASS"
            else:
                err_msg = (proc.stderr or proc.stdout or "").strip()
                result["error"] = err_msg or f"Exited with return code {proc.returncode}"

        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)
            result["status"] = "FAIL"
            result["error"] = f"Timed out after {timeout} seconds"
        except OSError as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result["latency_ms"] = round(elapsed_ms, 2)
            result["status"] = "FAIL"
            result["error"] = str(exc)

    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Ping Claude Code or Codex CLI with minimal token consumption to refresh 5-hour rolling session windows.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=SUPPORTED_TARGETS,
        help="Target CLI to ping: 'claude', 'codex', or 'all' (default: 'all')",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout in seconds per CLI call (default: 60)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    args = parse_args(argv)

    targets = ["claude", "codex"] if args.target == "all" else [args.target]
    results: list[dict[str, Any]] = []

    for target in targets:
        if not args.json:
            print(f"Pinging {target.title()} CLI in isolated sandbox...")
        res = ping_cli(target, timeout=args.timeout)
        results.append(res)

    has_fail = any(r["status"] == "FAIL" for r in results)
    overall_status = "FAIL" if has_fail else "PASS"

    if args.json:
        report = {
            "overall_status": overall_status,
            "results": results,
        }
        print(json.dumps(report, indent=2))
    else:
        print("\nSession Refresh Summary:")
        for r in results:
            cli_name = r["cli"].title()
            status = r["status"]
            latency = f"{r['latency_ms']:.1f}ms"
            tokens = f"{r['tokens']} tokens" if r["tokens"] is not None else "minimal tokens"

            if status == "PASS":
                print(f"  • {cli_name}: PASS ({latency}, {tokens})")
            elif status == "SKIPPED":
                print(f"  • {cli_name}: SKIPPED ({r.get('error')})")
            else:
                print(f"  • {cli_name}: FAIL ({r.get('error')})")

        if not has_fail:
            print("\nSession refresh complete. 5-hour rolling quota window is active.")

    return 1 if has_fail else 0


if __name__ == "__main__":
    sys.exit(main())
