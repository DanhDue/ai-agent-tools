"""Playwright test runner harness with webServer lifecycle and watchdog verification.

Supports launching development or preview web servers, awaiting healthcheck availability,
executing headless Playwright test suites, and guaranteeing clean server teardown.
"""

from __future__ import annotations

import argparse
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    """Poll until a TCP port is open or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.2)
    return False


def wait_for_http(url: str, timeout: float = 15.0) -> bool:
    """Poll until an HTTP URL returns status 200 or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Playwright-Harness-Healthcheck"}
            )
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status < 400:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    return False


def run_playwright_suite(
    test_command: list[str],
    cwd: Path | str,
    web_server_command: list[str] | None = None,
    healthcheck_url: str | None = None,
    healthcheck_port: int | None = None,
    healthcheck_host: str = "127.0.0.1",
    timeout: float = 20.0,
) -> dict[str, Any]:
    """Execute Playwright test suite with webServer lifecycle management."""
    working_dir = Path(cwd).resolve()
    server_proc: subprocess.Popen[str] | None = None
    start_time = time.time()

    try:
        # 1. Start webServer if configured
        if web_server_command:
            server_proc = subprocess.Popen(
                web_server_command,
                cwd=str(working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Await healthcheck port or URL
            healthy = False
            if healthcheck_url:
                healthy = wait_for_http(healthcheck_url, timeout=timeout)
            elif healthcheck_port:
                healthy = wait_for_port(
                    healthcheck_host, healthcheck_port, timeout=timeout
                )
            else:
                # Default quick stabilization delay if no healthcheck specified
                time.sleep(1.0)
                healthy = server_proc.poll() is None

            if not healthy:
                stderr = ""
                if server_proc:
                    try:
                        _stdout, stderr = server_proc.communicate(timeout=2.0)
                    except (subprocess.TimeoutExpired, OSError):
                        pass
                return {
                    "status": "BLOCKED",
                    "returncode": 1,
                    "error": f"webServer failed healthcheck on {healthcheck_url or healthcheck_port}. Stderr: {stderr}",
                    "duration": round(time.time() - start_time, 3),
                }

        # 2. Run Playwright test suite
        test_proc = subprocess.run(
            test_command,
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        duration = round(time.time() - start_time, 3)

        return {
            "status": "PASS" if test_proc.returncode == 0 else "FAIL",
            "returncode": test_proc.returncode,
            "stdout": test_proc.stdout,
            "stderr": test_proc.stderr,
            "duration": duration,
        }

    finally:
        # 3. Clean teardown of webServer process
        if server_proc is not None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Playwright harness with webServer lifecycle."
    )
    parser.add_argument(
        "--test-cmd", nargs="+", required=True, help="Test execution command"
    )
    parser.add_argument(
        "--web-server-cmd", nargs="*", default=None, help="WebServer start command"
    )
    parser.add_argument(
        "--healthcheck-url", default=None, help="URL to wait for before running tests"
    )
    parser.add_argument(
        "--healthcheck-port", type=int, default=None, help="TCP port to wait for"
    )
    parser.add_argument("--cwd", default=".", help="Working directory")

    args = parser.parse_args()
    res = run_playwright_suite(
        test_command=args.test_cmd,
        cwd=args.cwd,
        web_server_command=args.web_server_cmd,
        healthcheck_url=args.healthcheck_url,
        healthcheck_port=args.healthcheck_port,
    )
    print(f"Harness result: {res['status']} in {res['duration']}s")
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
