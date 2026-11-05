"""Integration tests for Web Quality Gate against genuine repository fixtures (Task 01 / Finding 1)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SCRIPTS = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"

if str(WEB_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(WEB_SCRIPTS))
if str(QC_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(QC_SCRIPTS))

from validate_quality_contract import validate_provider_result
from validate_web_quality import run_capabilities

FIXTURE_REPO = REPO_ROOT / "tests" / "fixtures" / "astro_repo"


def _get_fixture_sha() -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(FIXTURE_REPO),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return "0" * 40


def test_WQG_HP_01_web_quality_provider_certification_on_astro_repo():
    """Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository."""
    manifest_path = FIXTURE_REPO / ".agents" / "quality" / "web-quality.json"
    assert manifest_path.is_file(), f"Fixture manifest not found at {manifest_path}"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_sha = _get_fixture_sha()

    # Execute genuine capabilities against the Astro repository fixture
    res = run_capabilities(
        config=manifest,
        profile="epic",
        repository_sha=fixture_sha,
        repo_root=FIXTURE_REPO,
        provider_id="learning-web",
        check_watchdog_evidence=True,
    )

    # 1. Overall status and contract verification
    invocation = {
        "contract_version": 1,
        "profile": "epic",
        "repository_sha": fixture_sha,
        "provider_id": "learning-web",
        "base_ref": "main",
    }
    contract_check = validate_provider_result(res, invocation)
    assert contract_check["status"] == "PASS", (
        f"Contract validation failed: {contract_check}"
    )
    assert res["status"] == "PASS"
    assert res["repository_sha"] == fixture_sha

    # 2. Verify all five epic capabilities ran and recorded evidence
    checks_by_id = {c["id"]: c for c in res["checks"]}
    assert len(checks_by_id) == 5
    for cap in ("type_check", "lint", "test_unit", "test_e2e", "ui_review"):
        assert cap in checks_by_id
        assert checks_by_id[cap]["status"] == "PASS"

    # 3. Verify real logs were generated in build/quality/web/
    log_dir = FIXTURE_REPO / "build" / "quality" / "web"
    assert log_dir.is_dir()
    assert (log_dir / "type_check.log").is_file()
    assert "ASTRO TypeScript checks completed" in (
        log_dir / "type_check.log"
    ).read_text(encoding="utf-8")
    assert (log_dir / "test_e2e.log").is_file()
    assert "Playwright watchdog executed" in (log_dir / "test_e2e.log").read_text(
        encoding="utf-8"
    )

    # 4. Verify watchdog evidence artifact was generated and validated
    evidence_xml = FIXTURE_REPO / "build" / "test-results" / "playwright.xml"
    assert evidence_xml.is_file()
    assert "playwright.watchdog" in evidence_xml.read_text(encoding="utf-8")
