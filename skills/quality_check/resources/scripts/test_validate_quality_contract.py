"""Red-first contract tests for the provider quality boundary."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_quality_contract import (  # noqa: E402
    normalize_invocation,
    reconcile_results,
    validate_capability_manifest,
    validate_provider_result,
    validate_registry,
)


SHA = "a" * 40


def registry(*providers: dict, schema_version: int = 1) -> dict:
    return {"schema_version": schema_version, "providers": list(providers)}


def provider(provider_id: str, profiles: list[str] | None = None, **extra: object) -> dict:
    value = {
        "id": provider_id,
        "skill": f"d3nexus:{provider_id}",
        "required": True,
        "profiles": profiles or ["pr", "epic"],
    }
    value.update(extra)
    return value


def invocation(profile: str = "epic", **extra: object) -> dict:
    value = {
        "contract_version": 1,
        "profile": profile,
        "base_ref": "main",
        "repository_sha": SHA,
        "provider_id": "alpha",
        "required": True,
    }
    value.update(extra)
    return value


def result(status: str = "PASS", **extra: object) -> dict:
    value = {
        "provider_id": "alpha",
        "contract_version": 1,
        "profile": "epic",
        "repository_sha": SHA,
        "status": status,
        "checks": [],
        "coverage": {},
        "evidence": [],
        "started_head": SHA,
        "finished_head": SHA,
        "duration": 0.25,
        "blockers": [],
        "warnings": [],
    }
    value.update(extra)
    return value


class RegistryContractTests(unittest.TestCase):
    def test_valid_registry_selects_all_matching_providers_in_id_order(self) -> None:
        checked = validate_registry(
            registry(provider("zeta"), provider("alpha"), provider("pr-only", ["pr"])),
            "epic",
            available_skills={"d3nexus:alpha", "d3nexus:zeta"},
        )
        self.assertEqual("PASS", checked["status"])
        self.assertEqual(["alpha", "zeta"], [p["id"] for p in checked["providers"]])
        self.assertEqual([], checked["findings"])

    def test_unknown_and_missing_fields_fail_closed_without_selection(self) -> None:
        bad = registry({"id": "alpha", "skill": "d3nexus:alpha", "profiles": ["epic"], "profles": []})
        checked = validate_registry(bad, "epic", available_skills={"d3nexus:alpha"})
        self.assertEqual("BLOCKED", checked["status"])
        self.assertEqual([], checked["providers"])
        self.assertEqual(
            ["missing_field", "unknown_field"],
            [finding["code"] for finding in checked["findings"]],
        )

    def test_rejects_unsupported_version_duplicate_id_invalid_profile_and_empty_registry(self) -> None:
        cases = [
            (registry(provider("alpha"), schema_version=2), "unsupported_version"),
            (registry(provider("alpha"), provider("alpha")), "duplicate_id"),
            (registry(provider("alpha", ["quick"])), "unsupported_profile"),
            ({"schema_version": 1, "providers": []}, "empty_providers"),
        ]
        for manifest, expected in cases:
            with self.subTest(expected=expected):
                checked = validate_registry(
                    manifest,
                    "epic",
                    available_skills={"d3nexus:alpha"},
                )
                self.assertEqual("BLOCKED", checked["status"])
                self.assertIn(expected, [finding["code"] for finding in checked["findings"]])

    def test_rejects_unresolved_skill_and_empty_selection(self) -> None:
        unresolved = validate_registry(
            registry(provider("alpha")),
            "epic",
            available_skills=set(),
        )
        self.assertIn("unresolved_skill", [finding["code"] for finding in unresolved["findings"]])

        empty = validate_registry(
            registry(provider("alpha", ["pr"])),
            "epic",
            available_skills={"d3nexus:alpha"},
        )
        self.assertIn("empty_selection", [finding["code"] for finding in empty["findings"]])

    def test_findings_and_plan_are_deterministic_for_input_order(self) -> None:
        first = validate_registry(
            registry(provider("zeta"), provider("alpha"), provider("alpha")),
            "epic",
            available_skills={"d3nexus:alpha", "d3nexus:zeta"},
        )
        second = validate_registry(
            registry(provider("alpha"), provider("zeta"), provider("alpha")),
            "epic",
            available_skills={"d3nexus:alpha", "d3nexus:zeta"},
        )
        self.assertEqual(first, second)


class InvocationContractTests(unittest.TestCase):
    def test_missing_profile_defaults_to_pr(self) -> None:
        value = invocation()
        del value["profile"]
        checked = normalize_invocation(value)
        self.assertEqual("PASS", checked["status"])
        self.assertEqual("pr", checked["invocation"]["profile"])

    def test_unknown_fields_unsupported_profile_and_bad_identity_block(self) -> None:
        value = invocation(profile="quick", typo=True)
        checked = normalize_invocation(value)
        self.assertEqual("BLOCKED", checked["status"])
        codes = [finding["code"] for finding in checked["findings"]]
        self.assertIn("unknown_field", codes)
        self.assertIn("unsupported_profile", codes)

        bad_sha = normalize_invocation(invocation(repository_sha="not-a-sha"))
        self.assertIn("invalid_repository_sha", [f["code"] for f in bad_sha["findings"]])


class ResultContractTests(unittest.TestCase):
    def test_valid_result_is_accepted_and_identity_is_preserved(self) -> None:
        checked = validate_provider_result(result(), invocation())
        self.assertEqual("PASS", checked["status"])
        self.assertEqual([], checked["findings"])

    def test_result_identity_sha_and_profile_mismatches_are_blocked(self) -> None:
        for change, code in [
            ({"profile": "pr"}, "profile_mismatch"),
            ({"repository_sha": "b" * 40}, "repository_sha_mismatch"),
            ({"provider_id": "beta"}, "provider_id_mismatch"),
            ({"contract_version": 2}, "unsupported_version"),
        ]:
            value = result(**change)
            checked = validate_provider_result(value, invocation())
            with self.subTest(code=code):
                self.assertEqual("BLOCKED", checked["status"])
                self.assertIn(code, [finding["code"] for finding in checked["findings"]])

    def test_malformed_checks_coverage_evidence_duration_and_status_are_blocked(self) -> None:
        malformed = result(
            checks=[{"id": "lint", "status": "PASS"}],
            coverage={"lines": {"measured": 1.1, "threshold": 0.8}},
            evidence=[{"id": "run", "type": "command", "source": "pytest"}],
            duration=-1,
        )
        checked = validate_provider_result(malformed, invocation())
        self.assertEqual("BLOCKED", checked["status"])
        codes = [finding["code"] for finding in checked["findings"]]
        for expected in ("missing_field", "invalid_coverage", "malformed_evidence", "invalid_duration"):
            self.assertIn(expected, codes)

    def test_evidence_references_must_resolve(self) -> None:
        malformed = result(
            checks=[
                {
                    "id": "lint",
                    "category": "lint",
                    "status": "PASS",
                    "source": "pytest",
                    "duration": 0.1,
                    "summary": "ok",
                    "evidence_refs": ["missing"],
                }
            ],
            evidence=[
                {
                    "id": "run",
                    "type": "command",
                    "source": "pytest",
                    "location": "artifacts/pytest.log",
                }
            ],
        )
        checked = validate_provider_result(malformed, invocation())
        self.assertIn("unresolved_evidence_reference", [f["code"] for f in checked["findings"]])

    def test_not_applicable_requires_reason_and_applicability_evidence(self) -> None:
        check = {
            "id": "wasm",
            "category": "wasm",
            "status": "NOT_APPLICABLE",
            "source": "profile policy",
            "duration": 0,
            "summary": "not applicable",
            "evidence_refs": ["applicability"],
        }
        missing_reason = result(
            status="NOT_APPLICABLE",
            checks=[check],
            evidence=[
                {
                    "id": "applicability",
                    "type": "applicability",
                    "source": "profile policy",
                    "location": "policy.json",
                }
            ],
        )
        checked = validate_provider_result(missing_reason, invocation())
        self.assertIn("missing_not_applicable_reason", [f["code"] for f in checked["findings"]])

        invalid_reason = copy.deepcopy(check)
        invalid_reason["not_applicable_reason"] = {"code": "missing_tool", "detail": "no"}
        invalid = result(
            status="NOT_APPLICABLE",
            checks=[invalid_reason],
            evidence=missing_reason["evidence"],
        )
        checked = validate_provider_result(invalid, invocation())
        self.assertIn("invalid_not_applicable_reason", [f["code"] for f in checked["findings"]])

    def test_provider_pass_with_check_fail_or_blocked_is_contract_violation(self) -> None:
        chk_fail = {
            "id": "unit_tests",
            "category": "unit",
            "status": "FAIL",
            "source": "pytest",
            "duration": 0.1,
            "summary": "1 test failed",
            "evidence_refs": [],
        }
        res = result(status="PASS", checks=[chk_fail])
        checked = validate_provider_result(res, invocation())
        self.assertEqual("BLOCKED", checked["status"])
        self.assertIn("contract_violation", [f["code"] for f in checked["findings"]])

    def test_provider_pass_with_sub_threshold_coverage_is_coverage_deficit(self) -> None:
        cov = {
            "lines": {
                "measured": 0.10,
                "threshold": 0.85,
            }
        }
        res = result(status="PASS", coverage=cov)
        checked = validate_provider_result(res, invocation())
        self.assertEqual("BLOCKED", checked["status"])
        self.assertIn("coverage_deficit", [f["code"] for f in checked["findings"]])


class ReconciliationTests(unittest.TestCase):
    def test_missing_result_gets_synthetic_blocked_and_valid_result_remains(self) -> None:
        plan = [
            {"id": "alpha", "required": True},
            {"id": "beta", "required": True},
        ]
        checked = reconcile_results(plan, [result()])
        self.assertEqual("BLOCKED", checked["status"])
        self.assertEqual(["alpha", "beta"], [item["provider_id"] for item in checked["results"]])
        self.assertEqual("PASS", checked["results"][0]["status"])
        self.assertEqual("BLOCKED", checked["results"][1]["status"])
        self.assertIn("missing_result", [finding["code"] for finding in checked["findings"]])

    def test_duplicate_results_never_choose_arbitrarily(self) -> None:
        first = reconcile_results([{"id": "alpha", "required": True}], [result(), result()])
        second = reconcile_results([{"id": "alpha", "required": True}], [result(), result()])
        self.assertEqual(first, second)
        self.assertEqual("BLOCKED", first["status"])
        self.assertIn("duplicate_result", [finding["code"] for finding in first["findings"]])

    def test_reconcile_rejects_stale_commit_sha(self) -> None:
        plan = [{"id": "alpha", "required": True, "repository_sha": SHA}]
        stale_result = result(repository_sha="b" * 40, started_head="b" * 40, finished_head="b" * 40)
        checked = reconcile_results(plan, [stale_result], expected_sha=SHA)
        self.assertEqual("BLOCKED", checked["status"])
        self.assertIn("sha_mismatch", [f["code"] for f in checked["findings"]])


class CapabilityContractTests(unittest.TestCase):
    def test_capability_manifest_rejects_empty_command_array(self) -> None:
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "test": [],
            },
            "profiles": {
                "pr": ["test"],
            },
        }
        checked = validate_capability_manifest(manifest, "pr")
        self.assertEqual("BLOCKED", checked["status"])
        self.assertIn("command_array_empty", [f["code"] for f in checked["findings"]])

    def test_capability_manifest_valid_passes(self) -> None:
        manifest = {
            "schema_version": 1,
            "capabilities": {
                "test": ["pytest"],
            },
            "profiles": {
                "pr": ["test"],
            },
        }
        checked = validate_capability_manifest(manifest, "pr")
        self.assertEqual("PASS", checked["status"])



class SchemaContractTests(unittest.TestCase):
    def test_checked_in_schemas_describe_version_one_and_reject_unknown_fields(self) -> None:
        root = Path(__file__).resolve().parents[1] / "schemas"
        for name in ("check-quality.schema.json", "provider-result.schema.json"):
            with self.subTest(name=name):
                schema = json.loads((root / name).read_text())
                self.assertEqual("object", schema["type"])
                self.assertEqual(False, schema["additionalProperties"])
                self.assertEqual(1, schema["properties"]["schema_version"]["const"])


class FixtureContractTests(unittest.TestCase):
    def test_fixture_files_are_valid(self) -> None:
        fixtures_dir = Path(__file__).resolve().parents[1] / "fixtures"
        valid_reg = json.loads((fixtures_dir / "valid_registry.json").read_text())
        checked_reg = validate_registry(
            valid_reg,
            "pr",
            available_skills={"d3nexus:rust-quality-check", "d3nexus:doc_quality_check"},
        )
        self.assertEqual("PASS", checked_reg["status"])
        self.assertEqual(2, len(checked_reg["providers"]))

        valid_res = json.loads((fixtures_dir / "valid_result.json").read_text())
        inv = invocation(
            profile="epic",
            provider_id="rust-core",
            repository_sha="5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
        )
        checked_res = validate_provider_result(valid_res, inv)
        self.assertEqual("PASS", checked_res["status"])


class DocumentationExamplesTests(unittest.TestCase):
    def test_embedded_documentation_json_examples_are_valid(self) -> None:
        import re
        root = Path(__file__).resolve().parents[4]
        for doc_rel in (
            "docs/architecture/quality-provider-system.en.md",
            "docs/architecture/quality-provider-system.vi.md",
        ):
            doc_path = root / doc_rel
            if not doc_path.exists():
                continue
            text = doc_path.read_text()
            json_blocks = re.findall(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
            self.assertEqual(4, len(json_blocks), f"Expected 4 JSON blocks in {doc_rel}")

            # 1. Single provider registry
            reg_single = json.loads(json_blocks[0])
            res_reg_single = validate_registry(reg_single, "epic", {"d3nexus:rust-quality-check"})
            self.assertEqual("PASS", res_reg_single["status"], res_reg_single["findings"])

            # 2. Normalized invocation
            inv_req = json.loads(json_blocks[1])
            res_inv = normalize_invocation(inv_req)
            self.assertEqual("PASS", res_inv["status"], res_inv["findings"])

            # 3. Provider result
            result_doc = json.loads(json_blocks[2])
            res_result = validate_provider_result(result_doc, res_inv["invocation"])
            self.assertEqual("PASS", res_result["status"], res_result["findings"])

            # 4. Composite registry
            reg_composite = json.loads(json_blocks[3])
            res_reg_composite = validate_registry(
                reg_composite,
                "epic",
                {"d3nexus:rust-quality-check", "d3nexus:android-quality-check"},
            )
            self.assertEqual("PASS", res_reg_composite["status"], res_reg_composite["findings"])


if __name__ == "__main__":
    unittest.main()


