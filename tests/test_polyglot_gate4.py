"""Unit and Integration Tests for Polyglot Gate 4 Registry and Multi-Provider Fan-Out (Task 04)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
SETUP_SCRIPTS = REPO_ROOT / "skills" / "setup_quality_check" / "resources" / "scripts"

if str(QC_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(QC_SCRIPTS))
if str(SETUP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SETUP_SCRIPTS))

from scaffold_quality_manifest import build_registry_data, detect_platforms
from verify_polyglot_registry import fanout_and_aggregate, verify_polyglot_execution

SAMPLE_SHA = "b1c2d3e4f5a60718293a4b5c6d7e8f9012345679"


def polyglot_d3nexus_registry() -> dict:
    return {
        "schema_version": 1,
        "providers": [
            {
                "id": "rust-core",
                "skill": "d3nexus:rust-quality-check",
                "required": True,
                "profiles": ["pr", "epic", "release", "scheduled"],
            },
            {
                "id": "learning-web",
                "skill": "d3nexus:web-quality-check",
                "required": True,
                "profiles": ["pr", "epic", "release", "scheduled"],
            },
        ],
    }


def sample_provider_result(provider_id: str, status: str) -> dict:
    return {
        "provider_id": provider_id,
        "contract_version": 1,
        "profile": "epic",
        "repository_sha": SAMPLE_SHA,
        "status": status,
        "checks": [
            {
                "id": f"{provider_id}-check-1",
                "category": "compile",
                "status": status,
                "source": "check command",
                "duration": 1.2,
                "summary": f"{provider_id} test check",
                "evidence_refs": ["ev-1"],
            }
        ],
        "coverage": {},
        "evidence": [
            {
                "id": "ev-1",
                "type": "command",
                "source": "check command",
                "location": f"artifacts/{provider_id}.log",
            }
        ],
        "started_head": SAMPLE_SHA,
        "finished_head": SAMPLE_SHA,
        "duration": 5.4,
        "blockers": [] if status == "PASS" else [f"{provider_id} encountered failure"],
        "warnings": [],
    }


def test_polyglot_fanout():
    """GREEN phase assertion for Task 04: Polyglot registry fanout and aggregation precedence."""
    registry = polyglot_d3nexus_registry()

    # 1. Both providers PASS -> Aggregated PASS
    res_both_pass = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "PASS"),
        ],
    )
    assert res_both_pass["status"] == "PASS"
    assert len(res_both_pass["plan"]) == 2

    # 2. Reduction precedence: FAIL > BLOCKED > PASS
    res_one_fail = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "FAIL"),
        ],
    )
    assert res_one_fail["status"] == "FAIL"

    res_one_blocked = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "BLOCKED"),
        ],
    )
    assert res_one_blocked["status"] == "BLOCKED"


def test_WQG_AR_01_concurrent_multiprovider_fanout():
    """Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4."""
    registry = polyglot_d3nexus_registry()
    provider_results = [
        sample_provider_result("rust-core", "PASS"),
        sample_provider_result("learning-web", "PASS"),
    ]

    exec_result = verify_polyglot_execution(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=provider_results,
    )

    assert exec_result["status"] == "PASS"
    assert exec_result["aggregated"]["status"] == "PASS"
    assert len(exec_result["aggregated"]["providers"]) == 2
    ids = [p["provider_id"] for p in exec_result["aggregated"]["providers"]]
    assert "rust-core" in ids
    assert "learning-web" in ids


def test_scaffolding_detects_web_and_generates_manifest():
    """Verify scaffold_quality_manifest detects web projects and generates web-quality config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "package.json").write_text(json.dumps({"name": "test-web-app"}))
        (tmp_path / "playwright.config.ts").write_text("// config")

        detected = detect_platforms(tmp_path)
        assert "web" in detected

        reg = build_registry_data(detected)
        providers = reg.get("providers", [])
        web_provider = next((p for p in providers if p["id"] == "web-quality"), None)
        assert web_provider is not None
        assert web_provider["skill"] == "d3nexus:web-quality-check"


def test_verify_polyglot_registry_cli_execution():
    """Verify verify_polyglot_registry CLI accepts result files and execute flag."""
    from verify_polyglot_registry import main

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        reg_file = tmp_path / "check_quality.json"
        res_file = tmp_path / "result.json"

        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "learning-web",
                    "skill": "d3nexus:web-quality-check",
                    "required": True,
                    "profiles": ["epic"],
                }
            ],
        }
        reg_file.write_text(json.dumps(registry))

        res_data = sample_provider_result("learning-web", "PASS")
        res_file.write_text(json.dumps(res_data))

        code = main([str(reg_file), "--profile", "epic", "--results", str(res_file), "--sha", SAMPLE_SHA])
        assert code == 0
