"""Tests for failure baseline recording and regression comparison CLI."""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from unittest import mock

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from record_failure_baseline import (
    extract_node_failures,
    extract_pytest_failures,
    main as record_main,
    record_baseline,
)
from compare_failure_sets import (
    compare_failure_sets,
    load_failure_set,
    main as compare_main,
)


def test_EVI_HP_02_record_and_compare_baseline(tmp_path: Path) -> None:
    """[EVI-HP-02] Failure-set baseline recording and regression comparison pass when no new failures appear."""
    pytest_output = (
        "tests/test_a.py .F\n"
        "tests/test_b.py F.\n"
        "=========================== short test summary info ============================\n"
        "FAILED tests/test_a.py::test_one - AssertionError: foo\n"
        "FAILED tests/test_b.py::test_two - AssertionError: bar\n"
        "======================== 2 failed, 2 passed in 0.12s ==========================\n"
    )
    baseline_file = tmp_path / "baseline.txt"
    failures = extract_pytest_failures(pytest_output)
    assert failures == ["tests/test_a.py::test_one", "tests/test_b.py::test_two"]

    record_baseline(output_path=baseline_file, failures=failures)
    assert baseline_file.read_text(encoding="utf-8") == "tests/test_a.py::test_one\ntests/test_b.py::test_two\n"

    current_file = tmp_path / "current.txt"
    current_file.write_text("tests/test_a.py::test_one\n", encoding="utf-8")

    code, new_failures = compare_failure_sets(baseline_path=baseline_file, current_path=current_file)
    assert code == 0
    assert new_failures == []

    # Run CLI compare
    cli_code = compare_main(["--baseline", str(baseline_file), "--current", str(current_file)])
    assert cli_code == 0


class Test_Failure_Baseline_Integration:
    def test_EVI_HP_02_integration_baseline(self, tmp_path: Path) -> None:
        """[EVI-HP-02] [Tier C - Integration] Failure-set baseline recording and regression comparison."""
        test_EVI_HP_02_record_and_compare_baseline(tmp_path)



def test_EVI_EC_01_ignore_captured_logs_and_sentinel_on_zero(tmp_path: Path) -> None:
    """[EVI-EC-01] Failure-set parser ignores captured ERROR log lines and writes sentinel on zero failures."""
    pytest_with_logs = (
        "tests/test_app.py .\n"
        "----------------------------- Captured stderr call -----------------------------\n"
        "ERROR logger:module.py:42 Database connection timeout\n"
        "ERROR app.service:main.py:105 Failed to fetch user profile\n"
        "=== short test summary info ===\n"
        "FAILED tests/test_app.py::test_fail - AssertionError: fail\n"
        "ERROR tests/test_app.py::test_err - RuntimeError: error\n"
        "=== 1 failed, 1 error, 1 passed in 0.25s ===\n"
    )
    failures = extract_pytest_failures(pytest_with_logs)
    assert failures == ["tests/test_app.py::test_err", "tests/test_app.py::test_fail"]
    assert "logger:module.py:42" not in failures
    assert "app.service:main.py:105" not in failures

    # Zero failures in short test summary info
    zero_fail_file = tmp_path / "zero_baseline.txt"
    record_baseline(zero_fail_file, [])
    content = zero_fail_file.read_text(encoding="utf-8")
    assert content == "# 0 failures\n"
    assert len(content) > 0
    assert load_failure_set(zero_fail_file) == set()


def test_EVI_ST_01_rerun_new_classifies_isolated_pass_and_persistent_failure(tmp_path: Path) -> None:
    """[EVI-ST-01] --rerun-new classifies isolated-pass vs persistent failures and requires explicit opt-in."""
    baseline_file = tmp_path / "baseline.txt"
    baseline_file.write_text("# 0 failures\n", encoding="utf-8")

    current_file = tmp_path / "current.txt"
    test_cand_pass = "tests/test_x.py::test_x[hello - world]"
    test_cand_fail = "tests/test_y.py::test_y"
    current_file.write_text(f"{test_cand_pass}\n{test_cand_fail}\n", encoding="utf-8")

    # Mock subprocess.run in rerun_candidate
    def mock_subprocess_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        # Last argument is node_id
        node_id = cmd[-1]
        if node_id == test_cand_pass:
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="1 passed\n", stderr="")
        return subprocess.CompletedProcess(cmd, returncode=1, stdout="1 failed\n", stderr="")

    with mock.patch("subprocess.run", side_effect=mock_subprocess_run):
        # Without --allow-isolated-pass, exits 1 due to persistent failure (and isolated pass)
        code = compare_main([
            "--baseline", str(baseline_file),
            "--current", str(current_file),
            "--rerun-new",
            "--rerun-cmd", "python3 -m pytest",
        ])
        assert code == 1

    # Now test when ALL candidates pass in isolation
    current_pass_only = tmp_path / "current_pass_only.txt"
    current_pass_only.write_text(f"{test_cand_pass}\n", encoding="utf-8")

    def mock_all_pass(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="1 passed\n", stderr="")

    with mock.patch("subprocess.run", side_effect=mock_all_pass):
        # Without --allow-isolated-pass, still exits 1 to flag order-dependent state-pollution
        code_without_flag = compare_main([
            "--baseline", str(baseline_file),
            "--current", str(current_pass_only),
            "--rerun-new",
            "--rerun-cmd", "python3 -m pytest",
        ])
        assert code_without_flag == 1

        # With --allow-isolated-pass, exits 0
        code_with_flag = compare_main([
            "--baseline", str(baseline_file),
            "--current", str(current_pass_only),
            "--rerun-new",
            "--rerun-cmd", "python3 -m pytest",
            "--allow-isolated-pass",
        ])
        assert code_with_flag == 0


def test_EVI_AR_02_restore_tracked_files_after_execution(tmp_path: Path) -> None:
    """[EVI-AR-02] record_failure_baseline --restore restores tracked files after execution."""
    # Setup temporary git repo
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    config_file = repo / "config.json"
    config_file.write_text('{"clean": true}', encoding="utf-8")
    subprocess.run(["git", "add", "config.json"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=repo, check=True)

    # Command mutates config.json and prints pytest output
    cmd = (
        'python3 -c "import pathlib; '
        'pathlib.Path(\'config.json\').write_text(\'{\\\"clean\\\": false}\'); '
        'print(\'=== short test summary info ===\\nFAILED test_x.py::test_x - Error\\n=== 1 failed in 0.1s ===\')"'
    )
    baseline_out = repo / "baseline.txt"

    exit_code = record_main([
        "--cmd", cmd,
        "--out", str(baseline_out),
        "--restore", "config.json",
        "--cwd", str(repo),
    ])
    assert exit_code == 0
    assert baseline_out.read_text(encoding="utf-8") == "test_x.py::test_x\n"
    # Verify config.json was restored to its clean HEAD state
    assert config_file.read_text(encoding="utf-8") == '{"clean": true}'


def test_real_pytest_summary_padding_extraction() -> None:
    """Verify extract_pytest_failures on real-world pytest output with 20+ '=' padding."""
    real_out = (
        "=================================== FAILURES ===================================\n"
        "_ test_a _\n"
        ">   assert False\n"
        "E   assert False\n"
        "tests/test_foo.py:10: AssertionError\n"
        "=========================== short test summary info ============================\n"
        "FAILED tests/test_foo.py::test_a - assert False\n"
        "FAILED tests/test_bar.py::test_b[param-1] - assert False\n"
        "======================== 2 failed, 10 passed in 1.23s ==========================\n"
    )
    failures = extract_pytest_failures(real_out)
    assert failures == ["tests/test_bar.py::test_b[param-1]", "tests/test_foo.py::test_a"]


def test_parameterized_ids_with_spaces_and_delimiter() -> None:
    """Verify regex preserves parameterized node IDs containing spaces and ' - ' delimiters."""
    output = (
        "=== short test summary info ===\n"
        "FAILED tests/test_x.py::test_x[hello - world] - AssertionError: value mismatch\n"
        "FAILED tests/test_x.py::test_x[hello - other] - AssertionError: value mismatch\n"
        "=== 2 failed in 0.05s ===\n"
    )
    failures = extract_pytest_failures(output)
    assert failures == [
        "tests/test_x.py::test_x[hello - other]",
        "tests/test_x.py::test_x[hello - world]",
    ]


def test_node_runner_failure_extraction() -> None:
    """Verify node failure extraction preserves file context in spec and TAP modes."""
    # Spec reporter format with duration and suite header
    spec_output = (
        "▶ tests/foo.test.mjs\n"
        "  ✖ test one (0.483083ms)\n"
        "▶ tests/bar.test.mjs\n"
        "  ✖ test two (1.25ms)\n"
        "  ✖ test three (tests/bar.test.mjs:20:5)\n"
        "ℹ tests 3\n"
        "ℹ fail 3\n"
    )
    spec_failures = extract_node_failures(spec_output)
    assert spec_failures == [
        "tests/bar.test.mjs::test three",
        "tests/bar.test.mjs::test two",
        "tests/foo.test.mjs::test one",
    ]

    # TAP format with subtests
    tap_output = (
        "# Subtest: tests/foo.test.mjs\n"
        "    # Subtest: unit test A\n"
        "    not ok 1 - unit test A\n"
        "not ok 1 - tests/foo.test.mjs\n"
        "# tests 1\n"
        "# fail 1\n"
    )
    tap_failures = extract_node_failures(tap_output)
    assert tap_failures == ["tests/foo.test.mjs::unit test A"]


def test_invalid_runner_launch_or_usage_errors(tmp_path: Path) -> None:
    """Verify runner launch/usage errors (exit 4, 5, etc) reject without producing a baseline."""
    baseline_file = tmp_path / "baseline.txt"

    # Command exiting with pytest usage error (exit 4) without summary info
    cmd_usage_error = 'python3 -c "import sys; print(\'pytest: error: unrecognized arguments\'); sys.exit(4)"'
    exit_code = record_main([
        "--cmd", cmd_usage_error,
        "--out", str(baseline_file),
    ])
    assert exit_code == 2
    assert not baseline_file.exists()
