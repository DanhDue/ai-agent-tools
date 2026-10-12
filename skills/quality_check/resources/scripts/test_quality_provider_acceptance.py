#!/usr/bin/env python3
"""End-to-end acceptance tests for the provider-based quality system.

Tests composite consumer repositories, multiple providers, Rust capability execution,
formal lifecycle inputs, deterministic concurrency, status precedence (FAIL > BLOCKED > PASS),
missing registration, missing tools, corrupt results, SHA drift, and read-only invariants.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from skills.quality_check.resources.scripts.validate_quality_contract import (
    validate_registry,
    normalize_invocation,
    validate_provider_result,
    reconcile_results,
    validate_capability_manifest,
)
from skills.quality_check.resources.scripts.aggregate_quality_results import (
    aggregate_results,
    render_executive_report,
)


def _init_git_repo(path: Path) -> str:
    """Initialize a git repo with a commit and return its HEAD SHA."""
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agent@example.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Agent Tools"], cwd=path, check=True, capture_output=True)
    (path / "README.md").write_text("# Test Repo\n")
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=path, check=True, capture_output=True)
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=path).decode().strip()


def _make_provider_result(
    provider_id: str,
    sha: str,
    profile: str = "epic",
    status: str = "PASS",
    check_status: str = "PASS",
    check_id: str = "main-check",
    blockers: list[str] | None = None,
    coverage_measured: float = 0.88,
    coverage_threshold: float = 0.80,
    extra_checks: list[dict] | None = None,
) -> dict:
    """Construct a schema-valid provider result dict."""
    check_entry = {
        "id": check_id,
        "category": "tests",
        "status": check_status,
        "source": "cargo test" if "rust" in provider_id else "gradle check",
        "duration": 12.5,
        "summary": f"{check_id} completed with status {check_status}",
        "evidence_refs": [f"ev-{check_id}"],
    }
    if check_status == "NOT_APPLICABLE":
        check_entry["not_applicable_reason"] = {
            "code": "scope_unmodified",
            "detail": "No touched files in this module",
        }

    checks = [check_entry]
    if extra_checks:
        checks.extend(extra_checks)

    evidence_items = [
        {
            "id": f"ev-{check_id}",
            "type": "log",
            "source": "stdout",
            "location": f"target/quality/{provider_id}/{check_id}.log",
        }
    ]
    if extra_checks:
        for ec in extra_checks:
            for ref in ec.get("evidence_refs", []):
                evidence_items.append(
                    {
                        "id": ref,
                        "type": "log",
                        "source": "stdout",
                        "location": f"target/quality/{provider_id}/{ref}.log",
                    }
                )

    return {
        "provider_id": provider_id,
        "contract_version": 1,
        "profile": profile,
        "repository_sha": sha,
        "status": status,
        "checks": checks,
        "coverage": {
            "line": {
                "measured": coverage_measured,
                "threshold": coverage_threshold,
            }
        },
        "evidence": evidence_items,
        "started_head": sha,
        "finished_head": sha,
        "duration": 25.0,
        "blockers": blockers or [],
        "warnings": [],
    }


def execute_quality_pipeline(
    repo_path: Path,
    raw_invocation: dict,
    provider_results: list[dict],
    available_skills: set[str],
) -> dict:
    """Simulate the complete quality_check orchestration kernel end-to-end."""
    registry_file = repo_path / ".agents" / "quality" / "check_quality.json"
    if not registry_file.exists():
        plan = [{"id": "unregistered", "required": True}]
        results = [
            {
                "provider_id": "unregistered",
                "status": "BLOCKED",
                "required": True,
                "blockers": ["Missing required project quality registry .agents/quality/check_quality.json"],
            }
        ]
        agg = aggregate_results(plan, results, raw_invocation)
        return {
            "status": "BLOCKED",
            "aggregation": agg,
            "report": render_executive_report(agg),
        }

    # 1. Normalize invocation
    inv_res = normalize_invocation(raw_invocation)
    if inv_res["status"] != "PASS":
        plan = [{"id": "invocation", "required": True}]
        results = [
            {
                "provider_id": "invocation",
                "status": "BLOCKED",
                "required": True,
                "blockers": [f["message"] for f in inv_res["findings"]],
            }
        ]
        agg = aggregate_results(plan, results, raw_invocation)
        return {
            "status": "BLOCKED",
            "aggregation": agg,
            "report": render_executive_report(agg),
        }
    inv = inv_res["invocation"]

    # 2. Validate registry
    reg_data = json.loads(registry_file.read_text())
    reg_res = validate_registry(reg_data, inv["profile"], available_skills)
    if reg_res["status"] != "PASS":
        plan = [{"id": "registry", "required": True}]
        results = [
            {
                "provider_id": "registry",
                "status": "BLOCKED",
                "required": True,
                "blockers": [f["message"] for f in reg_res["findings"]],
            }
        ]
        agg = aggregate_results(plan, results, inv)
        return {
            "status": "BLOCKED",
            "aggregation": agg,
            "report": render_executive_report(agg),
        }

    # 3. Check for SHA drift or workspace mutation
    current_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_path).decode().strip()
    if current_sha != inv["repository_sha"]:
        plan = [{"id": "repository", "required": True}]
        results = [
            {
                "provider_id": "repository",
                "status": "BLOCKED",
                "required": True,
                "blockers": [f"Candidate SHA drifted from {inv['repository_sha']} to {current_sha}"],
            }
        ]
        agg = aggregate_results(plan, results, inv)
        return {
            "status": "BLOCKED",
            "aggregation": agg,
            "report": render_executive_report(agg),
        }

    porcelain = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo_path).decode().strip()
    if porcelain:
        plan = [{"id": "repository", "required": True}]
        results = [
            {
                "provider_id": "repository",
                "status": "BLOCKED",
                "required": True,
                "blockers": [f"Working tree mutated during execution:\n{porcelain}"],
            }
        ]
        agg = aggregate_results(plan, results, inv)
        return {
            "status": "BLOCKED",
            "aggregation": agg,
            "report": render_executive_report(agg),
        }

    # 4. Validate each returned result
    validated_results = []
    for res in provider_results:
        target_inv = copy.deepcopy(inv)
        target_inv["provider_id"] = res.get("provider_id")
        val_res = validate_provider_result(res, target_inv)
        if val_res["status"] == "PASS":
            validated_results.append(res)
        else:
            synthetic_blocked = copy.deepcopy(res)
            synthetic_blocked["status"] = "BLOCKED"
            synthetic_blocked.setdefault("blockers", []).append(
                f"Validation failed: {[f['code'] for f in val_res['findings']]}"
            )
            validated_results.append(synthetic_blocked)

    # 5. Reconcile against plan
    reconciled = reconcile_results(reg_res["providers"], validated_results)

    # 6. Aggregate
    agg = aggregate_results(reg_res["providers"], reconciled["results"], inv)

    # 7. Render report
    report = render_executive_report(agg)

    return {
        "status": agg["status"],
        "aggregation": agg,
        "report": report,
    }


class EndToEndQualityAcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        self.sha = _init_git_repo(self.repo_path)
        self.skills = {
            "d3nexus:rust-quality-check",
            "d3nexus:mobile-quality-check",
            "d3nexus:flutter-quality-check",
            "d3nexus:android-quality-check",
            "d3nexus:ios-quality-check",
            "d3nexus:setup_quality_check",
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_composite_consumer_passes_end_to_end(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "rust-core",
                    "skill": "d3nexus:rust-quality-check",
                    "required": True,
                    "profiles": ["epic", "pr"],
                },
                {
                    "id": "mobile-client",
                    "skill": "d3nexus:mobile-quality-check",
                    "required": True,
                    "profiles": ["epic", "pr"],
                },
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        res_rust = _make_provider_result("rust-core", active_sha, "epic", "PASS")
        res_mobile = _make_provider_result("mobile-client", active_sha, "epic", "PASS", check_id="app-test")

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(
            self.repo_path,
            inv,
            [res_rust, res_mobile],
            self.skills,
        )

        self.assertEqual("PASS", pipeline_out["status"])
        self.assertIn("rust-core", pipeline_out["report"])
        self.assertIn("mobile-client", pipeline_out["report"])
        self.assertIn("**PASS**", pipeline_out["report"])

    def test_failure_precedence_survives_a_blocked_peer(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
                {"id": "mobile-client", "skill": "d3nexus:mobile-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        res_rust = _make_provider_result("rust-core", active_sha, "epic", "FAIL", check_status="FAIL")
        res_mobile = _make_provider_result(
            "mobile-client",
            active_sha,
            "epic",
            "BLOCKED",
            check_status="BLOCKED",
            blockers=["Missing Android SDK"],
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(
            self.repo_path,
            inv,
            [res_rust, res_mobile],
            self.skills,
        )

        self.assertEqual("FAIL", pipeline_out["status"])
        self.assertIn("**FAIL**", pipeline_out["report"])
        self.assertIn("Missing Android SDK", pipeline_out["report"])

    def test_missing_registry_has_no_compatibility_fallback(self) -> None:
        (self.repo_path / "Cargo.toml").write_text("[package]\nname = 'test'\nversion = '0.1.0'\n")
        (self.repo_path / "pubspec.yaml").write_text("name: flutter_app\n")
        (self.repo_path / "build.gradle.kts").write_text("// gradle\n")
        (self.repo_path / "Package.swift").write_text("// swift\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add markers"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(
            self.repo_path,
            inv,
            [],
            self.skills,
        )

        self.assertEqual("BLOCKED", pipeline_out["status"])
        self.assertIn("Missing required project quality registry", pipeline_out["report"])

    def test_concurrent_completion_is_reproducible_and_deterministic(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "provider-b", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
                {"id": "provider-a", "skill": "d3nexus:mobile-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        res_a = _make_provider_result("provider-a", active_sha, "epic", "PASS", check_id="check-1")
        res_b = _make_provider_result("provider-b", active_sha, "epic", "PASS", check_id="check-2")

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        out1 = execute_quality_pipeline(self.repo_path, inv, [res_a, res_b], self.skills)
        out2 = execute_quality_pipeline(self.repo_path, inv, [res_b, res_a], self.skills)

        self.assertEqual("PASS", out1["status"])
        self.assertEqual("PASS", out2["status"])
        self.assertEqual(out1["report"], out2["report"])

    def test_sha_drift_and_source_mutation_cannot_pass(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        initial_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": initial_sha,
        }

        # Case 1: Drift - a new commit occurs during/before pipeline completion
        (self.repo_path / "README.md").write_text("# New commit\n")
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Drift commit"], cwd=self.repo_path, check=True, capture_output=True)

        res_rust = _make_provider_result("rust-core", initial_sha, "epic", "PASS")
        pipeline_drift = execute_quality_pipeline(self.repo_path, inv, [res_rust], self.skills)

        self.assertEqual("BLOCKED", pipeline_drift["status"])
        self.assertIn("Candidate SHA drifted", pipeline_drift["report"])

        # Case 2: Tracked file mutation (dirty working tree)
        new_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()
        (self.repo_path / "README.md").write_text("# Uncommitted modification\n")
        inv2 = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": new_sha,
        }
        res_rust2 = _make_provider_result("rust-core", new_sha, "epic", "PASS")
        pipeline_mutated = execute_quality_pipeline(self.repo_path, inv2, [res_rust2], self.skills)

        self.assertEqual("BLOCKED", pipeline_mutated["status"])
        self.assertIn("Working tree mutated during execution", pipeline_mutated["report"])

    def test_profile_isolation_and_downgrade_rejection(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        res_pr = _make_provider_result("rust-core", active_sha, profile="pr", status="PASS")
        inv_epic = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv_epic, [res_pr], self.skills)
        self.assertEqual("BLOCKED", pipeline_out["status"])
        self.assertIn("**BLOCKED**", pipeline_out["report"])

    def test_pure_flutter_workspace_passes_end_to_end(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "flutter-core",
                    "skill": "d3nexus:flutter-quality-check",
                    "required": True,
                    "profiles": ["epic", "pr"],
                },
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add flutter registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        flutter_checks = [
            {"id": "dartfmt", "category": "formatting", "status": "PASS", "source": "./scripts/dartfmt.sh", "duration": 2.1, "summary": "Format clean", "evidence_refs": ["ev-1"]},
            {"id": "analyze", "category": "analysis", "status": "PASS", "source": "fvm flutter analyze", "duration": 5.4, "summary": "Zero issues", "evidence_refs": ["ev-2"]},
            {"id": "boundaries", "category": "architecture", "status": "PASS", "source": "./scripts/check_module_boundaries.sh", "duration": 1.2, "summary": "Boundaries valid", "evidence_refs": ["ev-3"]},
            {"id": "license", "category": "compliance", "status": "PASS", "source": "./scripts/check_license_header.sh", "duration": 0.8, "summary": "Headers clean", "evidence_refs": ["ev-4"]},
            {"id": "test", "category": "tests", "status": "PASS", "source": "melos run test", "duration": 14.2, "summary": "Tests passed", "evidence_refs": ["ev-5"]},
        ]
        res_flutter = _make_provider_result(
            "flutter-core",
            active_sha,
            "epic",
            "PASS",
            check_id="coverage",
            extra_checks=flutter_checks,
            coverage_measured=0.88,
            coverage_threshold=0.80,
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_flutter], self.skills)
        self.assertEqual("PASS", pipeline_out["status"])
        self.assertIn("flutter-core", pipeline_out["report"])
        self.assertIn("**PASS**", pipeline_out["report"])

    def test_pure_android_workspace_passes_end_to_end(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "android-core",
                    "skill": "d3nexus:android-quality-check",
                    "required": True,
                    "profiles": ["epic", "pr"],
                },
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add android registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        android_checks = [
            {"id": "spotless", "category": "formatting", "status": "PASS", "source": "./gradlew spotlessCheck", "duration": 3.0, "summary": "Spotless clean", "evidence_refs": ["ev-1"]},
            {"id": "detekt", "category": "analysis", "status": "PASS", "source": "./gradlew detekt", "duration": 7.2, "summary": "Detekt clean", "evidence_refs": ["ev-2"]},
            {"id": "bcv", "category": "compatibility", "status": "PASS", "source": "./gradlew apiCheck", "duration": 2.5, "summary": "BCV verified", "evidence_refs": ["ev-3"]},
            {"id": "konsist", "category": "architecture", "status": "PASS", "source": "./gradlew :konsist-test:test", "duration": 4.1, "summary": "Konsist verified", "evidence_refs": ["ev-4"]},
            {"id": "unit_test", "category": "tests", "status": "PASS", "source": "./gradlew testDebugUnitTest", "duration": 15.0, "summary": "Unit tests passed", "evidence_refs": ["ev-5"]},
        ]
        res_android = _make_provider_result(
            "android-core",
            active_sha,
            "epic",
            "PASS",
            check_id="coverage",
            extra_checks=android_checks,
            coverage_measured=0.86,
            coverage_threshold=0.80,
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_android], self.skills)
        self.assertEqual("PASS", pipeline_out["status"])
        self.assertIn("android-core", pipeline_out["report"])
        self.assertIn("**PASS**", pipeline_out["report"])

    def test_pure_ios_workspace_passes_end_to_end(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "ios-core",
                    "skill": "d3nexus:ios-quality-check",
                    "required": True,
                    "profiles": ["epic", "pr"],
                },
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add ios registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        ios_checks = [
            {"id": "swiftformat", "category": "formatting", "status": "PASS", "source": "swiftformat", "duration": 2.0, "summary": "Format clean", "evidence_refs": ["ev-1"]},
            {"id": "swiftlint", "category": "analysis", "status": "PASS", "source": "swiftlint", "duration": 4.5, "summary": "Lint strict pass", "evidence_refs": ["ev-2"]},
            {"id": "arch_tests", "category": "architecture", "status": "PASS", "source": "swift test --package-path ArchTests", "duration": 3.2, "summary": "K1-K10 clean", "evidence_refs": ["ev-3"]},
            {"id": "boundaries", "category": "architecture", "status": "PASS", "source": "./scripts/check_module_boundaries.sh", "duration": 1.1, "summary": "Boundaries valid", "evidence_refs": ["ev-4"]},
            {"id": "unit_test", "category": "tests", "status": "PASS", "source": "swift test", "duration": 8.0, "summary": "Tests passed", "evidence_refs": ["ev-5"]},
        ]
        res_ios = _make_provider_result(
            "ios-core",
            active_sha,
            "epic",
            "PASS",
            check_id="coverage",
            extra_checks=ios_checks,
            coverage_measured=0.87,
            coverage_threshold=0.80,
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_ios], self.skills)
        self.assertEqual("PASS", pipeline_out["status"])
        self.assertIn("ios-core", pipeline_out["report"])
        self.assertIn("**PASS**", pipeline_out["report"])

    def test_polyglot_rust_android_flutter_passes_end_to_end(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic", "pr"]},
                {"id": "android-core", "skill": "d3nexus:android-quality-check", "required": True, "profiles": ["epic", "pr"]},
                {"id": "flutter-core", "skill": "d3nexus:flutter-quality-check", "required": True, "profiles": ["epic", "pr"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add polyglot registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        res_rust = _make_provider_result("rust-core", active_sha, "epic", "PASS", check_id="cargo-test")
        res_android = _make_provider_result("android-core", active_sha, "epic", "PASS", check_id="gradle-test")
        res_flutter = _make_provider_result("flutter-core", active_sha, "epic", "PASS", check_id="melos-test")

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_rust, res_android, res_flutter], self.skills)
        self.assertEqual("PASS", pipeline_out["status"])
        self.assertIn("rust-core", pipeline_out["report"])
        self.assertIn("android-core", pipeline_out["report"])
        self.assertIn("flutter-core", pipeline_out["report"])
        self.assertIn("**PASS**", pipeline_out["report"])

    def test_false_pass_f1_failing_check_demoted_to_blocked(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "flutter-core", "skill": "d3nexus:flutter-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        # Vulnerability F1: top-level status is PASS, but an individual check is FAIL
        res_f1 = _make_provider_result(
            "flutter-core",
            active_sha,
            "epic",
            status="PASS",
            check_status="FAIL",
            check_id="failing-test",
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_f1], self.skills)
        self.assertEqual("BLOCKED", pipeline_out["status"])
        self.assertIn("contract_violation", str(pipeline_out["aggregation"]))

    def test_false_pass_f2_sub_threshold_coverage_demoted_to_blocked(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "android-core", "skill": "d3nexus:android-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        # Vulnerability F2: top-level status is PASS, but line coverage is below threshold (0.65 < 0.80)
        res_f2 = _make_provider_result(
            "android-core",
            active_sha,
            "epic",
            status="PASS",
            check_status="PASS",
            check_id="coverage",
            coverage_measured=0.65,
            coverage_threshold=0.80,
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_f2], self.skills)
        self.assertEqual("BLOCKED", pipeline_out["status"])
        self.assertIn("coverage_deficit", str(pipeline_out["aggregation"]))

    def test_false_pass_f3_stale_sha_rejected(self) -> None:
        agents_dir = self.repo_path / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        registry = {
            "schema_version": 1,
            "providers": [
                {"id": "ios-core", "skill": "d3nexus:ios-quality-check", "required": True, "profiles": ["epic"]},
            ],
        }
        (agents_dir / "check_quality.json").write_text(json.dumps(registry, indent=2))
        subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add registry"], cwd=self.repo_path, check=True, capture_output=True)
        active_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo_path).decode().strip()

        # Vulnerability F3: provider result bound to stale SHA
        res_f3 = _make_provider_result(
            "ios-core",
            sha="0000000000000000000000000000000000000000",
            profile="epic",
            status="PASS",
        )

        inv = {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": active_sha,
        }

        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_f3], self.skills)
        self.assertEqual("BLOCKED", pipeline_out["status"])
        self.assertIn("repository_sha_mismatch", str(pipeline_out["aggregation"]))

    def test_empty_command_array_capability_rejected(self) -> None:
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "empty_check": [],
            },
            "profiles": {
                "pr": ["empty_check"],
            },
        }
        res = validate_capability_manifest(manifest)
        findings = res["findings"]
        self.assertTrue(any(f["code"] == "command_array_empty" for f in findings))


if __name__ == "__main__":
    unittest.main()

