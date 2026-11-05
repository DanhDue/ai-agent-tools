"""Integration and Unit Tests for Web Quality Assurance Provider (Task 01)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SCRIPTS_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"
QC_SCRIPTS_DIR = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"

if str(WEB_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_SCRIPTS_DIR))
if str(QC_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(QC_SCRIPTS_DIR))

from validate_quality_contract import validate_provider_result
from validate_web_quality import (
    run_capabilities,
    validate_manifest,
)

SAMPLE_SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"


def valid_web_manifest() -> dict:
    return {
        "schema_version": 1,
        "capabilities": {
            "type_check": ["npm", "run", "check"],
            "lint": ["npm", "run", "lint"],
            "test_unit": ["npm", "run", "test:unit"],
            "test_e2e": ["npx", "playwright", "test"],
            "contracts": [
                "python3",
                "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py",
                "diff-check",
                "--base-ref",
                "{base_ref}",
            ],
        },
        "profiles": {
            "pr": ["type_check", "lint", "test_unit"],
            "epic": ["type_check", "lint", "test_unit", "test_e2e"],
            "release": ["type_check", "lint", "test_unit", "test_e2e"],
        },
    }


def test_contract_validation():
    """GREEN Phase assertion for Task 01: Web Quality Check Provider Contract."""
    manifest = valid_web_manifest()
    val = validate_manifest(manifest, requested_profile="pr")
    assert val["status"] == "PASS"
    assert val["findings"] == []

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        # Create execution manifest with commands that succeed
        exec_manifest = {
            "schema_version": 1,
            "capabilities": {
                "type_check": ["python3", "-c", "import sys; sys.exit(0)"],
                "lint": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_unit": ["python3", "-c", "import sys; sys.exit(0)"],
            },
            "profiles": {
                "pr": ["type_check", "lint", "test_unit"],
            },
        }
        res = run_capabilities(
            config=exec_manifest,
            profile="pr",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            provider_id="web-quality",
        )

        invocation = {
            "contract_version": 1,
            "profile": "pr",
            "repository_sha": SAMPLE_SHA,
            "provider_id": "web-quality",
            "base_ref": "main",
        }
        contract_check = validate_provider_result(res, invocation)
        assert contract_check["status"] == "PASS", (
            f"Provider result contract validation failed: {contract_check['findings']}"
        )
        assert res["status"] == "PASS"
        assert len(res["checks"]) == 3


def test_WQG_HP_01_astro_provider_certification():
    """Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results_dir = tmp_path / "build" / "test-results"
        results_dir.mkdir(parents=True, exist_ok=True)
        # Write valid Playwright JUnit XML evidence with executed testcase and watchdog trace
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='playwright' tests='1' failures='0'><testcase classname='playwright.watchdog' name='test_zero_console_error'/></testsuite></testsuites>"
        )

        manifest = {
            "schema_version": 1,
            "capabilities": {
                "type_check": ["python3", "-c", "import sys; sys.exit(0)"],
                "lint": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_unit": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_e2e": ["python3", "-c", "import sys; sys.exit(0)"],
            },
            "profiles": {
                "epic": ["type_check", "lint", "test_unit", "test_e2e"],
            },
        }

        res = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            provider_id="learning-web",
            check_watchdog_evidence=True,
        )

        invocation = {
            "contract_version": 1,
            "profile": "epic",
            "repository_sha": SAMPLE_SHA,
            "provider_id": "learning-web",
            "base_ref": "main",
        }
        contract_check = validate_provider_result(res, invocation)
        assert contract_check["status"] == "PASS"
        assert res["status"] == "PASS"
        assert res["repository_sha"] == SAMPLE_SHA
        assert len(res["checks"]) == 4


def test_WQG_EC_01_optional_capabilities():
    """Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities."""
    manifest = {
        "schema_version": 1,
        "capabilities": {
            "type_check": ["npm", "run", "check"],
            "lint": ["npm", "run", "lint"],
            "test_unit": ["npm", "test"],
            "custom_audit": ["echo", "audit"],
        },
        "profiles": {
            "pr": ["type_check", "lint", "test_unit"],
        },
    }
    res = validate_manifest(manifest, requested_profile="pr")
    assert res["status"] == "PASS"
    assert res["findings"] == []


def test_WQG_ST_01_blocked_to_pass_transition():
    """Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration."""
    malformed_manifest = {
        "schema_version": 1,
        "capabilities": {
            "type_check": "npm run check",  # invalid: string instead of list
        },
        "profiles": {
            "pr": ["type_check"],
        },
    }
    blocked_res = validate_manifest(malformed_manifest, requested_profile="pr")
    assert blocked_res["status"] == "BLOCKED"
    codes = [f["code"] for f in blocked_res["findings"]]
    assert "invalid_command_format" in codes

    # Correct the manifest
    corrected_manifest = valid_web_manifest()
    pass_res = validate_manifest(corrected_manifest, requested_profile="pr")
    assert pass_res["status"] == "PASS"
    assert pass_res["findings"] == []


def test_WQG_FR_02_missing_binary_execution_blocker():
    """Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "type_check": ["nonexistent_astro_binary_12345", "check"],
                "lint": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_unit": ["python3", "-c", "import sys; sys.exit(0)"],
            },
            "profiles": {
                "pr": ["type_check", "lint", "test_unit"],
            },
        }

        res = run_capabilities(
            config=manifest,
            profile="pr",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            provider_id="web-quality",
        )

        assert res["status"] == "BLOCKED"
        assert len(res["blockers"]) > 0
        blocker = res["blockers"][0]
        assert blocker["code"] == "binary_execution_blocker"
        assert "nonexistent_astro_binary_12345" in blocker["message"]


def test_watchdog_xml_validation_and_real_logs():
    """Verify watchdog XML failure detection and real log persistence."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results_dir = tmp_path / "build" / "test-results"
        results_dir.mkdir(parents=True, exist_ok=True)

        # 1. Failed tests in XML triggers FAIL
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='playwright' tests='2' failures='1'><testcase classname='playwright.watchdog' name='t1'><failure message='err'/></testcase></testsuite></testsuites>"
        )
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "type_check": ["python3", "-c", "import sys; sys.exit(0)"],
                "lint": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_unit": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_e2e": ["python3", "-c", "print('hello e2e')"],
            },
            "profiles": {
                "epic": ["type_check", "lint", "test_unit", "test_e2e"],
            },
        }
        res_fail = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            check_watchdog_evidence=True,
        )
        assert res_fail["status"] == "FAIL"
        codes = [b["code"] for b in res_fail["blockers"]]
        assert "failed_watchdog_tests" in codes

        # Verify real log file was written
        log_file = tmp_path / "build" / "quality" / "web" / "test_e2e.log"
        assert log_file.is_file()
        assert "hello e2e" in log_file.read_text()

        # 2. Empty XML (0 tests) triggers BLOCKED
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='pw' tests='0'/></testsuites>"
        )
        res_empty = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            check_watchdog_evidence=True,
        )
        assert res_empty["status"] == "BLOCKED"
        codes_empty = [b["code"] for b in res_empty["blockers"]]
        assert "empty_watchdog_evidence" in codes_empty


def test_watchdog_evidence_rejections():
    """Verify watchdog rejection of stale, empty, skipped, and non-browser reports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        results_dir = tmp_path / "build" / "test-results"
        results_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "type_check": ["python3", "-c", "import sys; sys.exit(0)"],
                "lint": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_unit": ["python3", "-c", "import sys; sys.exit(0)"],
                "test_e2e": ["python3", "-c", "import sys; sys.exit(0)"],
            },
            "profiles": {
                "epic": ["type_check", "lint", "test_unit", "test_e2e"],
            },
        }

        # 1. Non-browser report (e.g. pytest without watchdog/browser traces)
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='pytest' tests='1'><testcase classname='tests.test_unit' name='test_one'/></testsuite></testsuites>"
        )
        res_non_browser = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            check_watchdog_evidence=True,
        )
        assert res_non_browser["status"] == "BLOCKED"
        codes = [b["code"] for b in res_non_browser["blockers"]]
        assert "missing_watchdog_attachment" in codes

        # 2. Entirely skipped suite
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='playwright' tests='1'><testcase classname='playwright.e2e' name='test_one'><skipped/></testcase></testsuite></testsuites>"
        )
        res_skipped = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            check_watchdog_evidence=True,
        )
        assert res_skipped["status"] == "BLOCKED"
        codes = [b["code"] for b in res_skipped["blockers"]]
        assert "skipped_watchdog_suite" in codes

        # 3. Valid executed browser testcase with watchdog attachment
        (results_dir / "playwright.xml").write_text(
            "<testsuites><testsuite name='playwright' tests='1'><testcase classname='playwright.watchdog' name='test_zero_console_errors'/></testsuite></testsuites>"
        )
        res_valid = run_capabilities(
            config=manifest,
            profile="epic",
            repository_sha=SAMPLE_SHA,
            repo_root=tmp_path,
            check_watchdog_evidence=True,
        )
        assert res_valid["status"] == "PASS"
