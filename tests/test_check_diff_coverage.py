"""Tests for the portable multi-format hunk-level diff-coverage engine."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "quality_check"
    / "resources"
    / "scripts"
    / "check_diff_coverage.py"
)


def _require_script() -> Path:
    if not SCRIPT.is_file():
        pytest.fail(f"Expected implementation script does not exist yet: {SCRIPT}")
    return SCRIPT


def _load_module() -> ModuleType:
    script_path = _require_script()
    spec = importlib.util.spec_from_file_location("check_diff_coverage", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_diff_coverage"] = module
    spec.loader.exec_module(module)
    return module


def _run_cli(
    args: list[str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    script_path = _require_script()
    return subprocess.run(
        [sys.executable, str(script_path), *args],
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _init_git_repo(repo: Path) -> None:
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")


def _build_lcov_fixture(repo: Path) -> tuple[Path, str]:
    src_rel = "packages/core/lib/service.dart"
    src_file = repo / src_rel
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "\n".join(f"int line{i}() => {i};" for i in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    da_lines = [f"DA:{i},{1 if i <= 9 else 0}" for i in range(1, 11)]
    lcov_text = "\n".join(
        [
            "TN:",
            f"SF:{src_rel}",
            *da_lines,
            "LF:10",
            "LH:9",
            "end_of_record",
            "",
        ]
    )
    report = repo / "coverage" / "lcov.info"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(lcov_text, encoding="utf-8")
    return report, src_rel


def _build_cobertura_fixture(repo: Path) -> tuple[Path, str]:
    src_rel = "src/billing/calculator.py"
    src_file = repo / src_rel
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "\n".join(f"v{i} = {i}" for i in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    line_nodes = "\n".join(
        f'          <line number="{i}" hits="{1 if i <= 9 else 0}"/>'
        for i in range(1, 11)
    )
    xml_text = f"""<?xml version="1.0" ?>
<coverage version="7.6" line-rate="0.9">
  <sources>
    <source>{repo / "src"}</source>
  </sources>
  <packages>
    <package name="billing" line-rate="0.9">
      <classes>
        <class name="calculator.py" filename="billing/calculator.py" line-rate="0.9">
          <lines>
{line_nodes}
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
"""
    report = repo / "coverage.xml"
    report.write_text(xml_text, encoding="utf-8")
    return report, src_rel


def _build_jacoco_fixture(repo: Path) -> tuple[Path, str]:
    src_rel = "modules/wallet/src/main/kotlin/com/example/wallet/WalletService.kt"
    src_file = repo / src_rel
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "\n".join(f"val x{i} = {i}" for i in range(1, 11)) + "\n",
        encoding="utf-8",
    )
    line_nodes = "\n".join(
        f'      <line nr="{i}" mi="{0 if i <= 9 else 3}" ci="{3 if i <= 9 else 0}" mb="0" cb="0"/>'
        for i in range(1, 11)
    )
    xml_text = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<report name="wallet">
  <package name="com/example/wallet">
    <sourcefile name="WalletService.kt">
{line_nodes}
      <counter type="LINE" missed="1" covered="9"/>
    </sourcefile>
  </package>
</report>
"""
    report = repo / "build" / "reports" / "jacoco" / "jacocoTestReport.xml"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(xml_text, encoding="utf-8")
    return report, src_rel


def test_plq_hp_02_multiformat_compact_pass_and_json(tmp_path: Path) -> None:
    """[PLQ-HP-02] [Tier C - Integration] Portable diff-coverage engine evaluates LCOV, Cobertura XML, and JaCoCo XML with compact one-line PASS."""
    _require_script()

    builders = [
        ("lcov", _build_lcov_fixture),
        ("cobertura", _build_cobertura_fixture),
        ("jacoco", _build_jacoco_fixture),
    ]
    for name, builder in builders:
        repo = tmp_path / name
        repo.mkdir(parents=True, exist_ok=True)
        report_path, src_rel = builder(repo)

        base_args = [
            str(report_path),
            "--repo-root",
            str(repo),
            "--format",
            "auto",
            "--min-coverage",
            "75",
            "--min-package-coverage",
            "60",
            "--diff-files",
            src_rel,
            "--min-diff-coverage",
            "80",
        ]
        proc = _run_cli(base_args, cwd=repo)
        assert proc.returncode == 0, f"{name} failed: {proc.stdout}\n{proc.stderr}"
        assert proc.stderr == "", f"{name} unexpected stderr: {proc.stderr}"

        lines = proc.stdout.strip().splitlines()
        assert len(lines) == 1, f"{name} expected 1 line, got: {proc.stdout!r}"
        assert lines[0].startswith("PASS:"), lines[0]
        assert "coverage=90.0%" in lines[0], lines[0]
        assert "diff=90.0%" in lines[0], lines[0]

        json_proc = _run_cli([*base_args, "--json"], cwd=repo)
        assert json_proc.returncode == 0, json_proc.stdout
        payload: dict[str, Any] = json.loads(json_proc.stdout)
        assert payload["status"] == "PASS"
        assert payload["coverage_pct"] == pytest.approx(90.0)
        assert payload["min_coverage_pct"] == pytest.approx(75.0)
        assert payload["diff_coverage_pct"] == pytest.approx(90.0)
        assert payload["min_diff_coverage_pct"] == pytest.approx(80.0)
        assert payload["failures"] == []
        assert len(payload["package_results"]) >= 1
        assert len(payload["diff_files"]) == 1
        assert payload["diff_files"][0]["file"] == src_rel

        verbose_proc = _run_cli([*base_args, "--verbose"], cwd=repo)
        assert verbose_proc.returncode == 0
        verbose_lines = verbose_proc.stdout.strip().splitlines()
        assert len(verbose_lines) > 1
        assert verbose_lines[0].startswith("PASS:")
        assert src_rel in verbose_proc.stdout


def test_plq_ec_03_untested_new_file_fallback_failure(tmp_path: Path) -> None:
    """[PLQ-EC-03] [Tier C - Integration] Untested new source file triggers fallback executable-line diff-coverage failure."""
    _require_script()
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)

    existing = repo / "src" / "existing.py"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")
    _git(repo, "add", "src/existing.py")
    _git(repo, "commit", "-m", "initial")

    new_service = repo / "src" / "new_service.py"
    new_service.write_text(
        '"""Untested service."""\n\n'
        "# Header comment\n"
        "import os\n\n"
        "def compute_total(a: int, b: int) -> int:\n"
        "    step_one = a + 1\n"
        "    step_two = b + 2\n"
        "    step_three = step_one + step_two\n"
        "    step_four = step_three * 2\n"
        "    step_five = step_four - 1\n"
        "    if step_five > 10:\n"
        "        step_five = step_five - 3\n"
        "    result = step_five + int(bool(os.name))\n"
        "    return result\n",
        encoding="utf-8",
    )

    coverage_xml = repo / "coverage.xml"
    coverage_xml.write_text(
        """<?xml version="1.0" ?>
<coverage version="7.6">
  <packages>
    <package name="src">
      <classes>
        <class name="existing.py" filename="src/existing.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    proc = _run_cli(
        [
            str(coverage_xml),
            "--repo-root",
            str(repo),
            "--diff-base",
            "HEAD",
            "--min-diff-coverage",
            "80",
            "--source-ext",
            ".py",
        ],
        cwd=repo,
    )
    assert proc.returncode == 1, (
        f"Expected exit 1, got {proc.returncode}: {proc.stdout}"
    )
    assert proc.stdout.startswith("FAIL:"), proc.stdout
    assert "src/new_service.py" in proc.stdout, proc.stdout
    assert "10" in proc.stdout, proc.stdout

    json_proc = _run_cli(
        [
            str(coverage_xml),
            "--repo-root",
            str(repo),
            "--diff-base",
            "HEAD",
            "--min-diff-coverage",
            "80",
            "--source-ext",
            ".py",
            "--json",
        ],
        cwd=repo,
    )
    assert json_proc.returncode == 1
    payload = json.loads(json_proc.stdout)
    assert payload["status"] == "FAIL"
    assert payload["diff_coverage_pct"] == pytest.approx(0.0)
    assert payload["diff_files"][0]["file"] == "src/new_service.py"
    assert payload["diff_files"][0]["uncovered"] == 10
    assert payload["diff_files"][0]["fallback"] is True


def test_plq_ec_04_generated_files_and_excluded_package_floor(tmp_path: Path) -> None:
    """[PLQ-EC-04] [Tier C - Integration] Generated files and excluded packages are omitted from dual-floor enforcement."""
    _require_script()
    repo = tmp_path / "dart_workspace"
    repo.mkdir()

    gen_lines = [f"DA:{i},0" for i in range(1, 101)]
    legacy_lines = [f"DA:{i},{1 if i <= 9 else 0}" for i in range(1, 21)]
    core_lines = [f"DA:{i},{1 if i <= 90 else 0}" for i in range(1, 101)]

    lcov_text = "\n".join(
        [
            "SF:packages/core/lib/model.g.dart",
            *gen_lines,
            "LF:100",
            "LH:0",
            "end_of_record",
            "SF:packages/legacy/lib/old.dart",
            *legacy_lines,
            "LF:20",
            "LH:9",
            "end_of_record",
            "SF:packages/core/lib/service.dart",
            *core_lines,
            "LF:100",
            "LH:90",
            "end_of_record",
            "",
        ]
    )
    lcov_file = repo / "lcov.info"
    lcov_file.write_text(lcov_text, encoding="utf-8")

    proc = _run_cli(
        [
            str(lcov_file),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "75",
            "--min-package-coverage",
            "60",
            "--exclude-package-floor",
            "legacy",
        ],
        cwd=repo,
    )
    assert proc.returncode == 0, f"Expected PASS, got: {proc.stdout}\n{proc.stderr}"
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("PASS:")
    # Total without .g.dart = (9 + 90) / (20 + 100) = 99 / 120 = 82.5%
    assert "coverage=82.5%" in lines[0], lines[0]

    json_proc = _run_cli(
        [
            str(lcov_file),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "75",
            "--min-package-coverage",
            "60",
            "--exclude-package-floor",
            "legacy",
            "--json",
        ],
        cwd=repo,
    )
    assert json_proc.returncode == 0
    payload = json.loads(json_proc.stdout)
    assert payload["coverage_pct"] == pytest.approx(82.5)
    by_pkg = {item["package"]: item for item in payload["package_results"]}
    assert by_pkg["packages/core"]["coverage_pct"] == pytest.approx(90.0)
    assert by_pkg["packages/core"]["passed"] is True
    assert by_pkg["packages/legacy"]["coverage_pct"] == pytest.approx(45.0)
    assert by_pkg["packages/legacy"]["excluded_from_floor"] is True

    # Without --exclude-package-floor legacy, per-package floor must FAIL
    fail_proc = _run_cli(
        [
            str(lcov_file),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "75",
            "--min-package-coverage",
            "60",
        ],
        cwd=repo,
    )
    assert fail_proc.returncode == 1
    assert fail_proc.stdout.startswith("FAIL:")
    assert "packages/legacy" in fail_proc.stdout


def test_plq_fr_02_malformed_or_missing_reports_return_blocked_exit_2(
    tmp_path: Path,
) -> None:
    """[PLQ-FR-02] [Tier C - Integration] Malformed or missing coverage reports return exit code 2 BLOCKED cleanly."""
    _require_script()

    missing_path = tmp_path / "does_not_exist.xml"
    proc_missing = _run_cli([str(missing_path)])
    assert proc_missing.returncode == 2
    assert proc_missing.stdout.startswith("BLOCKED:"), proc_missing.stdout
    assert str(missing_path) in proc_missing.stdout
    assert "Traceback" not in proc_missing.stdout
    assert "Traceback" not in proc_missing.stderr

    corrupt_xml = tmp_path / "corrupt.xml"
    corrupt_xml.write_text("<broken", encoding="utf-8")
    proc_corrupt = _run_cli([str(corrupt_xml)])
    assert proc_corrupt.returncode == 2
    assert proc_corrupt.stdout.startswith("BLOCKED:"), proc_corrupt.stdout
    assert str(corrupt_xml) in proc_corrupt.stdout
    assert "Traceback" not in proc_corrupt.stdout
    assert "Traceback" not in proc_corrupt.stderr

    proc_corrupt_json = _run_cli([str(corrupt_xml), "--json"])
    assert proc_corrupt_json.returncode == 2
    payload = json.loads(proc_corrupt_json.stdout)
    assert payload["status"] == "BLOCKED"
    assert any(str(corrupt_xml) in msg for msg in payload["failures"])


def test_multi_report_merging_and_threshold_normalization(tmp_path: Path) -> None:
    """Verify multiple reports merge via max hit count and accept both 0..1 and 0..100 thresholds."""
    mod = _load_module()
    repo = tmp_path / "merge_repo"
    repo.mkdir()

    lcov_a = repo / "part_a.info"
    lcov_a.write_text(
        "SF:packages/core/lib/a.dart\nDA:1,1\nDA:2,0\nDA:3,0\nDA:4,0\nend_of_record\n",
        encoding="utf-8",
    )
    lcov_b = repo / "part_b.info"
    lcov_b.write_text(
        "SF:packages/core/lib/a.dart\nDA:1,0\nDA:2,3\nDA:3,1\nDA:4,0\nend_of_record\n",
        encoding="utf-8",
    )
    cobertura = repo / "py.xml"
    cobertura.write_text(
        """<coverage>
  <packages>
    <package name="svc">
      <classes>
        <class name="svc.py" filename="services/api/svc.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    # Merged: a.dart has 3/4 covered, svc.py has 2/2 covered -> 5/6 = 83.33%
    proc = _run_cli(
        [
            str(lcov_a),
            str(lcov_b),
            str(cobertura),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "0.80",
            "--min-package-coverage",
            "0.75",
            "--json",
        ],
        cwd=repo,
    )
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["status"] == "PASS"
    assert payload["min_coverage_pct"] == pytest.approx(80.0)
    assert payload["coverage_pct"] == pytest.approx(83.33, abs=0.05)

    # Verify exported symbols directly
    assert hasattr(mod, "CoverageDataset")
    assert hasattr(mod, "detect_format")
    assert hasattr(mod, "parse_lcov")
    assert hasattr(mod, "parse_cobertura_xml")
    assert hasattr(mod, "parse_jacoco_xml")
    assert hasattr(mod, "collect_git_diff_lines")
    assert hasattr(mod, "evaluate_coverage")
    assert hasattr(mod, "format_output")
    assert hasattr(mod, "main")


def test_git_hunk_diff_coverage_and_scope_exclusions(tmp_path: Path) -> None:
    """Verify git hunk diff-coverage isolates changed hunks, ignores tests/generated files, and supports diff-only PASS."""
    _require_script()
    repo = tmp_path / "git_hunk_repo"
    repo.mkdir()
    _init_git_repo(repo)

    src_file = repo / "src" / "engine.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text(
        "def f1() -> int:\n"
        "    return 1\n"
        "def f2() -> int:\n"
        "    return 2\n"
        "def f3() -> int:\n"
        "    return 3\n",
        encoding="utf-8",
    )
    _git(repo, "add", "src/engine.py")
    _git(repo, "commit", "-m", "base")

    # Modify only lines 5-6 (f3), add an uncovered test file and an uncovered generated file
    src_file.write_text(
        "def f1() -> int:\n"
        "    return 1\n"
        "def f2() -> int:\n"
        "    return 2\n"
        "def f3() -> int:\n"
        "    val = 30\n"
        "    return val\n",
        encoding="utf-8",
    )
    test_file = repo / "tests" / "test_engine.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("def test_ok() -> None:\n    assert True\n", encoding="utf-8")

    gen_file = repo / "src" / "types.d.ts"
    gen_file.write_text("export declare const x: number;\n", encoding="utf-8")

    # Lines 1-4 are uncovered (workspace 33%), but modified lines 6-7 are 100% covered!
    cov = repo / "cov.xml"
    cov.write_text(
        """<coverage>
  <packages>
    <package name="src">
      <classes>
        <class name="engine.py" filename="src/engine.py">
          <lines>
            <line number="1" hits="0"/>
            <line number="2" hits="0"/>
            <line number="3" hits="0"/>
            <line number="4" hits="0"/>
            <line number="5" hits="1"/>
            <line number="6" hits="1"/>
            <line number="7" hits="1"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )

    # Diff-only mode: --min-coverage omitted -> PASS line omits coverage=...
    proc = _run_cli(
        [
            str(cov),
            "--repo-root",
            str(repo),
            "--diff-base",
            "HEAD",
            "--min-diff-coverage",
            "80",
        ],
        cwd=repo,
    )
    assert proc.returncode == 0, proc.stdout
    out_lines = proc.stdout.strip().splitlines()
    assert len(out_lines) == 1
    assert out_lines[0].startswith("PASS: diff=100.0%"), out_lines[0]
    assert "coverage=" not in out_lines[0]

    # When modified lines 6-7 are uncovered, diff floor fails with exit 1
    cov_miss = repo / "cov_miss.xml"
    cov_miss.write_text(
        """<coverage>
  <packages>
    <package name="src">
      <classes>
        <class name="engine.py" filename="src/engine.py">
          <lines>
            <line number="1" hits="1"/>
            <line number="2" hits="1"/>
            <line number="3" hits="1"/>
            <line number="4" hits="1"/>
            <line number="5" hits="1"/>
            <line number="6" hits="0"/>
            <line number="7" hits="0"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>
""",
        encoding="utf-8",
    )
    fail_proc = _run_cli(
        [
            str(cov_miss),
            "--repo-root",
            str(repo),
            "--diff-base",
            "HEAD",
            "--min-diff-coverage",
            "80",
        ],
        cwd=repo,
    )
    assert fail_proc.returncode == 1
    assert fail_proc.stdout.startswith("FAIL:")
    assert "src/engine.py" in fail_proc.stdout
    assert "L6" in fail_proc.stdout


def test_parser_error_and_invalid_flag_branches_return_blocked(tmp_path: Path) -> None:
    """Verify all parser error, unknown format, bad git ref, and invalid threshold branches return exit 2 BLOCKED."""
    _require_script()

    # Unknown plain text (no LCOV markers)
    garbage = tmp_path / "garbage.txt"
    garbage.write_text("hello world\nno markers here\n", encoding="utf-8")
    p_garbage = _run_cli([str(garbage)])
    assert p_garbage.returncode == 2
    assert p_garbage.stdout.startswith("BLOCKED:")
    assert "Traceback" not in p_garbage.stderr

    # Unknown XML root tag
    unknown_xml = tmp_path / "other.xml"
    unknown_xml.write_text("<project><name>x</name></project>", encoding="utf-8")
    p_unknown_xml = _run_cli([str(unknown_xml)])
    assert p_unknown_xml.returncode == 2
    assert p_unknown_xml.stdout.startswith("BLOCKED:")

    # Explicit format mismatch
    valid_lcov = tmp_path / "ok.info"
    valid_lcov.write_text("SF:src/a.py\nDA:1,1\nend_of_record\n", encoding="utf-8")
    p_mismatch = _run_cli([str(valid_lcov), "--format", "cobertura"])
    assert p_mismatch.returncode == 2
    assert p_mismatch.stdout.startswith("BLOCKED:")

    # Corrupt LCOV DA line
    bad_lcov = tmp_path / "bad.info"
    bad_lcov.write_text("SF:src/a.py\nDA:abc,xyz\nend_of_record\n", encoding="utf-8")
    p_bad_lcov = _run_cli([str(bad_lcov), "--format", "lcov"])
    assert p_bad_lcov.returncode == 2
    assert p_bad_lcov.stdout.startswith("BLOCKED:")

    # Corrupt Cobertura line attribute
    bad_cob = tmp_path / "bad_cob.xml"
    bad_cob.write_text(
        '<coverage><packages><package name="p"><classes>'
        '<class filename="src/a.py"><lines><line number="NaN" hits="1"/></lines></class>'
        "</classes></package></packages></coverage>",
        encoding="utf-8",
    )
    p_bad_cob = _run_cli([str(bad_cob)])
    assert p_bad_cob.returncode == 2
    assert p_bad_cob.stdout.startswith("BLOCKED:")

    # Corrupt JaCoCo line attribute
    bad_jac = tmp_path / "bad_jac.xml"
    bad_jac.write_text(
        '<report name="r"><package name="p"><sourcefile name="A.kt">'
        '<line nr="bad" mi="0" ci="1"/></sourcefile></package></report>',
        encoding="utf-8",
    )
    p_bad_jac = _run_cli([str(bad_jac)])
    assert p_bad_jac.returncode == 2
    assert p_bad_jac.stdout.startswith("BLOCKED:")

    # Invalid thresholds (< 0 and > 100)
    p_neg = _run_cli([str(valid_lcov), "--min-coverage", "-5"])
    assert p_neg.returncode == 2
    assert p_neg.stdout.startswith("BLOCKED:")

    p_over = _run_cli([str(valid_lcov), "--min-coverage", "105"])
    assert p_over.returncode == 2
    assert p_over.stdout.startswith("BLOCKED:")

    # --min-diff-coverage without --diff-base or --diff-files
    p_no_diff_src = _run_cli([str(valid_lcov), "--min-diff-coverage", "80"])
    assert p_no_diff_src.returncode == 2
    assert p_no_diff_src.stdout.startswith("BLOCKED:")

    # Invalid --diff-base git ref
    repo = tmp_path / "bad_ref_repo"
    repo.mkdir()
    _init_git_repo(repo)
    p_bad_ref = _run_cli(
        [
            str(valid_lcov),
            "--repo-root",
            str(repo),
            "--diff-base",
            "refs/heads/nonexistent_branch_xyz",
            "--min-diff-coverage",
            "80",
        ],
        cwd=repo,
    )
    assert p_bad_ref.returncode == 2
    assert p_bad_ref.stdout.startswith("BLOCKED:")

    # Invalid CLI flag
    p_bad_flag = _run_cli([str(valid_lcov), "--totally-unknown-flag"])
    assert p_bad_flag.returncode == 2
    assert p_bad_flag.stdout.startswith("BLOCKED:")


def test_subpackage_lcov_fallback_and_non_python_exec_lines(tmp_path: Path) -> None:
    """Verify subpackage SF:lib/... inference, LCOV LF/LH summary fallback, --source-root, and multi-language fallback executable detection."""
    mod = _load_module()
    repo = tmp_path / "polyglot_repo"
    repo.mkdir()

    # Subpackage LCOV with SF:lib/calc.dart and LF/LH-only fallback record
    pkg_src = repo / "packages" / "math" / "lib" / "calc.dart"
    pkg_src.parent.mkdir(parents=True, exist_ok=True)
    pkg_src.write_text(
        "// file comment\n"
        "/* block\n"
        "   comment */\n"
        "import 'dart:math';\n"
        "@override\n"
        "int add(int a, int b) {\n"
        "  final total = a + b;\n"
        "  return total;\n"
        "}\n",
        encoding="utf-8",
    )
    lcov_path = repo / "packages" / "math" / "coverage" / "lcov.info"
    lcov_path.parent.mkdir(parents=True, exist_ok=True)
    lcov_path.write_text(
        "SF:lib/calc.dart\nLF:4\nLH:4\nend_of_record\n",
        encoding="utf-8",
    )

    proc = _run_cli(
        [
            str(lcov_path),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "80",
            "--min-package-coverage",
            "80",
            "--json",
        ],
        cwd=repo,
    )
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(proc.stdout)
    assert payload["coverage_pct"] == pytest.approx(100.0)
    assert payload["package_results"][0]["package"] == "packages/math"

    # Non-Python fallback executable line detection skips comments, imports, annotations, braces
    detected = mod._fallback_executable_lines(pkg_src, set(range(1, 10)))
    assert detected == [6, 7, 8]

    # Explicit --source-root with JaCoCo summary-only <counter type="LINE">
    jac_path = repo / "jacoco_summary.xml"
    jac_path.write_text(
        '<report name="app"><package name="com/acme">'
        '<sourcefile name="Main.kt">'
        '<counter type="LINE" missed="2" covered="8"/>'
        "</sourcefile></package></report>",
        encoding="utf-8",
    )
    p_jac = _run_cli(
        [
            str(jac_path),
            "--repo-root",
            str(repo),
            "--source-root",
            "modules/app/src/main/kotlin",
            "--min-coverage",
            "80",
            "--min-package-coverage",
            "70",
            "--json",
        ],
        cwd=repo,
    )
    assert p_jac.returncode == 0, p_jac.stdout
    jac_payload = json.loads(p_jac.stdout)
    assert jac_payload["coverage_pct"] == pytest.approx(80.0)
    assert jac_payload["package_results"][0]["package"] == "modules/app"

    # Workspace floor breach returns exit 1
    p_fail = _run_cli(
        [
            str(jac_path),
            "--repo-root",
            str(repo),
            "--min-coverage",
            "90",
        ],
        cwd=repo,
    )
    assert p_fail.returncode == 1
    assert p_fail.stdout.startswith("FAIL:")


def test_inprocess_parsers_edge_cases_and_high_branch_coverage(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Exercise path normalization, parser errors, diff specs, fallbacks, and output truncation in-process."""
    mod = _load_module()
    repo = tmp_path / "unit_repo"
    repo.mkdir()

    # Path normalization edge cases (empty, Windows abs, POSIX abs inside/outside repo)
    assert mod._normalize_source_path("", repo) == ""
    assert (
        mod._normalize_source_path(
            "C:\\work\\packages\\core\\lib\\a.dart",
            Path("C:/other"),
        )
        == "packages/core/lib/a.dart"
    )
    assert (
        mod._normalize_source_path(
            "C:\\repo\\src\\mod.py",
            Path("C:/repo"),
        )
        == "src/mod.py"
    )
    assert (
        mod._normalize_source_path("C:\\other\\lib\\root.dart", Path("D:/x"))
        == "lib/root.dart"
    )
    assert (
        mod._normalize_source_path("C:\\other\\standalone.py", Path("D:/x"))
        == "/other/standalone.py"
    )
    abs_inside = repo / "src" / "inside.py"
    abs_inside.parent.mkdir(parents=True, exist_ok=True)
    abs_inside.write_text("x = 1\n", encoding="utf-8")
    assert mod._normalize_source_path(str(abs_inside), repo) == "src/inside.py"
    assert (
        mod._normalize_source_path("/foreign/packages/net/lib/http.dart", repo)
        == "packages/net/lib/http.dart"
    )
    assert mod._normalize_source_path("/foreign/lib/main.dart", repo) == "lib/main.dart"
    assert mod._normalize_source_path("/foreign/other.py", repo) == "/foreign/other.py"

    # detect_format edge cases (empty, BOM XML, unknown root)
    with pytest.raises(mod.BlockedError):
        mod.detect_format("   \n", "empty.txt")
    assert mod.detect_format("\ufeff<coverage/>", "bom.xml") == "cobertura"
    assert mod.detect_format("<report/>", "j.xml") == "jacoco"

    # LCOV parser errors & partial-DA LF reconciliation
    with pytest.raises(mod.BlockedError):
        mod.parse_lcov("no markers", repo, source_name="bad.info")
    with pytest.raises(mod.BlockedError):
        mod.parse_lcov("SF:src/a.py\nDA:10\nend_of_record\n", repo, source_name="bad")
    with pytest.raises(mod.BlockedError):
        mod.parse_lcov("SF:src/a.py\nLF:oops\nend_of_record\n", repo, source_name="bad")
    partial_ds = mod.parse_lcov(
        "SF:src/a.py\nDA:1,1\nLF:4\nLH:2\nend_of_record\n", repo
    )
    assert partial_ds.da_by_file["src/a.py"] == {1: 1}
    assert partial_ds.fallback_by_file["src/a.py"] == (2, 4)

    # Cobertura parser errors & relative <source> & empty <class>
    with pytest.raises(mod.BlockedError):
        mod.parse_cobertura_xml("<broken", repo, source_name="bad.xml")
    with pytest.raises(mod.BlockedError):
        mod.parse_cobertura_xml("<report/>", repo, source_name="wrong.xml")
    cob_ds = mod.parse_cobertura_xml(
        '<coverage><sources><source>src</source></sources><packages><package name="p">'
        '<classes><class filename=""/><class filename="empty.py"/>'
        '<class filename="inside.py"><lines><line number="1" hits="2"/></lines></class>'
        "</classes></package></packages></coverage>",
        repo,
    )
    assert cob_ds.da_by_file == {"src/inside.py": {1: 2}}

    # JaCoCo parser errors & branch-only line (cb > 0, ci == 0, mi == 0)
    with pytest.raises(mod.BlockedError):
        mod.parse_jacoco_xml("<broken", repo, source_name="bad.xml")
    with pytest.raises(mod.BlockedError):
        mod.parse_jacoco_xml("<coverage/>", repo, source_name="wrong.xml")
    jvm_file = repo / "src" / "main" / "kotlin" / "com" / "acme" / "App.kt"
    jvm_file.parent.mkdir(parents=True, exist_ok=True)
    jvm_file.write_text("val a = 1\nval b = 2\n", encoding="utf-8")
    jac_ds = mod.parse_jacoco_xml(
        '<report name="r"><package name="com/acme"><sourcefile name="App.kt">'
        '<line nr="1" mi="0" ci="0" cb="2"/><line nr="2" mi="1" ci="0" cb="0"/>'
        "</sourcefile></package></report>",
        repo,
    )
    assert jac_ds.da_by_file["src/main/kotlin/com/acme/App.kt"] == {1: 1, 2: 0}

    # Multi-line Python docstring, Rust mod/use/attr, empty comment-only file
    py_doc = repo / "src" / "doc_mod.py"
    py_doc.write_text(
        '"""Line 1\nLine 2\nLine 3"""\n'
        "from pathlib import Path\n"
        "@staticmethod\n"
        "def run() -> int:\n"
        "    try:\n"
        "        return 1\n"
        "    finally:\n"
        "        pass\n",
        encoding="utf-8",
    )
    assert mod._fallback_executable_lines(py_doc, set(range(1, 11))) == [6, 8, 10]

    rs_file = repo / "crates" / "core" / "src" / "lib.rs"
    rs_file.parent.mkdir(parents=True, exist_ok=True)
    rs_file.write_text(
        "use std::fmt;\n"
        "pub mod sub;\n"
        "#[derive(Debug)]\n"
        "pub fn value() -> i32 {\n"
        "    42\n"
        "}\n",
        encoding="utf-8",
    )
    assert mod._fallback_executable_lines(rs_file, set(range(1, 7))) == [4, 5]

    # Explicit --diff-files with :start-end line spec, directory path, and >12 missed lines truncation
    many_lines = "\n".join(f"DA:{i},0" for i in range(1, 16))
    big_lcov = repo / "big.info"
    big_lcov.write_text(
        f"SF:src/inside.py\n{many_lines}\nend_of_record\n", encoding="utf-8"
    )
    rc_big = mod.main(
        [
            str(big_lcov),
            "--repo-root",
            str(repo),
            "--diff-files",
            "src/inside.py:1-15",
            "--min-diff-coverage",
            "80",
        ]
    )
    assert rc_big == 1
    out_big = capsys.readouterr().out
    assert out_big.startswith("FAIL:")
    assert "+3 more" in out_big

    # Directory in --diff-files + custom --package-group and --exclude-suffix
    rc_dir = mod.main(
        [
            str(big_lcov),
            "--repo-root",
            str(repo),
            "--diff-files",
            "src",
            "--package-group",
            "src",
            "--exclude-suffix",
            ".custom.py",
            "--min-diff-coverage",
            "0",
            "--verbose",
        ]
    )
    assert rc_dir == 0
    out_dir = capsys.readouterr().out
    assert out_dir.startswith("PASS:")
    assert "File Coverage:" in out_dir

    # Empty measurable report with min_coverage > 0 fails (exit 1); diff-only 0 changes passes (exit 0)
    empty_cov = repo / "empty.xml"
    empty_cov.write_text("<coverage><packages/></coverage>", encoding="utf-8")
    rc_empty_fail = mod.main([str(empty_cov), "--min-coverage", "75"])
    assert rc_empty_fail == 1
    assert "0 measurable" in capsys.readouterr().out

    # Git repo: deleted file + comment-only diff -> 0 measurable diff lines -> PASS 100.0%
    git_repo = tmp_path / "git_zero_diff"
    git_repo.mkdir()
    _init_git_repo(git_repo)
    f_del = git_repo / "src" / "old.py"
    f_del.parent.mkdir(parents=True, exist_ok=True)
    f_del.write_text("x = 1\n", encoding="utf-8")
    f_keep = git_repo / "src" / "keep.py"
    f_keep.write_text("y = 2\n", encoding="utf-8")
    _git(git_repo, "add", ".")
    _git(git_repo, "commit", "-m", "init")
    f_del.unlink()
    f_keep.write_text("# comment only\ny = 2\n", encoding="utf-8")
    cov_keep = git_repo / "cov.xml"
    cov_keep.write_text(
        '<coverage><packages><package name="src"><classes>'
        '<class filename="src/keep.py"><lines><line number="2" hits="1"/></lines></class>'
        "</classes></package></packages></coverage>",
        encoding="utf-8",
    )
    rc_zero = mod.main(
        [
            str(cov_keep),
            "--repo-root",
            str(git_repo),
            "--diff-base",
            "HEAD",
            "--diff-files",
            "src/keep.py",
            "--min-diff-coverage",
            "80",
        ]
    )
    assert rc_zero == 0
    assert "diff=100.0%" in capsys.readouterr().out

    # In-process BLOCKED path via main()
    rc_blocked = mod.main([str(tmp_path / "missing_inproc.xml")])
    assert rc_blocked == 2
    assert capsys.readouterr().out.startswith("BLOCKED:")


class TestCheckDiffCoverage_Integration:
    """Integration provenance wrapper for Tier C scenarios assigned to Task 02."""

    def test_plq_hp_02_integration(self, tmp_path: Path) -> None:
        """[PLQ-HP-02] Multi-format LCOV, Cobertura XML, and JaCoCo XML compact PASS and JSON."""
        test_plq_hp_02_multiformat_compact_pass_and_json(tmp_path)

    def test_plq_ec_03_integration(self, tmp_path: Path) -> None:
        """[PLQ-EC-03] Untested new source file triggers fallback executable-line diff-coverage failure."""
        test_plq_ec_03_untested_new_file_fallback_failure(tmp_path)

    def test_plq_ec_04_integration(self, tmp_path: Path) -> None:
        """[PLQ-EC-04] Generated files and excluded packages omitted from dual-floor enforcement."""
        test_plq_ec_04_generated_files_and_excluded_package_floor(tmp_path)

    def test_plq_fr_02_integration(self, tmp_path: Path) -> None:
        """[PLQ-FR-02] Malformed or missing coverage reports return exit code 2 BLOCKED cleanly."""
        test_plq_fr_02_malformed_or_missing_reports_return_blocked_exit_2(tmp_path)
