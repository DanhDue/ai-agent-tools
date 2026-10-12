"""Table-driven unit tests for the quality result aggregation engine."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from aggregate_quality_results import (  # noqa: E402
    aggregate_results,
    render_executive_report,
)

SHA = "a" * 40


def make_check(check_id: str, status: str = "PASS", **extra: object) -> dict:
    val = {
        "id": check_id,
        "category": "lint",
        "status": status,
        "source": "tool",
        "duration": 1.0,
        "summary": f"Check {check_id} {status}",
        "evidence_refs": ["ev-1"],
    }
    val.update(extra)
    return val


def make_provider_result(
    provider_id: str,
    status: str = "PASS",
    required: bool = True,
    checks: list[dict] | None = None,
    blockers: list[str] | None = None,
    warnings: list[str] | None = None,
    **extra: object,
) -> dict:
    val = {
        "provider_id": provider_id,
        "contract_version": 1,
        "profile": "epic",
        "repository_sha": SHA,
        "status": status,
        "required": required,
        "checks": checks if checks is not None else [make_check(f"{provider_id}-chk-1", status)],
        "coverage": {"lines": {"measured": 0.9, "threshold": 0.8}},
        "evidence": [{"id": "ev-1", "type": "command", "source": "tool", "location": "log.txt"}],
        "started_head": SHA,
        "finished_head": SHA,
        "duration": 5.0,
        "blockers": blockers or [],
        "warnings": warnings or [],
    }
    val.update(extra)
    return val


class AggregationEngineTests(unittest.TestCase):
    def test_all_required_providers_pass_produces_pass(self) -> None:
        p1 = make_provider_result("alpha", "PASS", required=True)
        p2 = make_provider_result("beta", "PASS", required=True)
        plan = [{"id": "alpha", "required": True}, {"id": "beta", "required": True}]

        res = aggregate_results(plan, [p1, p2])
        self.assertEqual("PASS", res["status"])
        self.assertIn("All required providers passed", res["decision_trace"])
        self.assertEqual(["alpha", "beta"], [p["provider_id"] for p in res["providers"]])

    def test_failure_outranks_infrastructure_blockage(self) -> None:
        p1 = make_provider_result("alpha", "FAIL", required=True, blockers=["Lint failure"])
        p2 = make_provider_result("beta", "BLOCKED", required=True, blockers=["Missing cargo tool"])
        plan = [{"id": "alpha", "required": True}, {"id": "beta", "required": True}]

        res = aggregate_results(plan, [p1, p2])
        self.assertEqual("FAIL", res["status"])
        self.assertIn("FAIL outranks BLOCKED", res["decision_trace"])
        self.assertEqual(2, len(res["blockers"]))

    def test_required_not_applicable_state_is_converted_to_blocked(self) -> None:
        na_check = make_check(
            "wasm",
            "NOT_APPLICABLE",
            not_applicable_reason={"code": "profile_policy", "detail": "wasm omitted"},
        )
        p1 = make_provider_result("alpha", "NOT_APPLICABLE", required=True, checks=[na_check])
        plan = [{"id": "alpha", "required": True}]

        res = aggregate_results(plan, [p1])
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("Required provider 'alpha' has only NOT_APPLICABLE checks", res["decision_trace"])

    def test_optional_not_applicable_is_neutral(self) -> None:
        p1 = make_provider_result("alpha", "PASS", required=True)
        na_check = make_check(
            "wasm",
            "NOT_APPLICABLE",
            not_applicable_reason={"code": "profile_policy", "detail": "wasm omitted"},
        )
        p2 = make_provider_result("beta-optional", "NOT_APPLICABLE", required=False, checks=[na_check])
        plan = [{"id": "alpha", "required": True}, {"id": "beta-optional", "required": False}]

        res = aggregate_results(plan, [p1, p2])
        self.assertEqual("PASS", res["status"])
        self.assertIn("All required providers passed", res["decision_trace"])

    def test_completion_order_cannot_alter_output_or_verdict(self) -> None:
        p1 = make_provider_result("alpha", "PASS")
        p2 = make_provider_result("zeta", "FAIL")
        plan = [{"id": "alpha", "required": True}, {"id": "zeta", "required": True}]

        res_forward = aggregate_results(plan, [p1, p2])
        res_reverse = aggregate_results(plan, [p2, p1])

        self.assertEqual(json.dumps(res_forward, sort_keys=True), json.dumps(res_reverse, sort_keys=True))
        self.assertEqual("FAIL", res_forward["status"])

    def test_warnings_do_not_alter_verdict(self) -> None:
        p1 = make_provider_result("alpha", "PASS", warnings=["Deprecation warning"])
        plan = [{"id": "alpha", "required": True}]

        res = aggregate_results(plan, [p1])
        self.assertEqual("PASS", res["status"])
        self.assertEqual(1, len(res["warnings"]))

    def test_render_executive_report_produces_structured_markdown(self) -> None:
        p1 = make_provider_result("alpha", "PASS")
        plan = [{"id": "alpha", "required": True}]
        payload = aggregate_results(plan, [p1])

        markdown = render_executive_report(payload)
        self.assertIn("# Executive Quality Report", markdown)
        self.assertIn("alpha", markdown)
        self.assertIn("PASS", markdown)
        self.assertIn("Decision Trace", markdown)

    def test_missing_required_provider_synthesizes_blocked_entry(self) -> None:
        plan = [{"id": "android-core", "required": True}, {"id": "alpha", "required": True}]
        p1 = make_provider_result("alpha", "PASS")
        res = aggregate_results(plan, [p1])
        self.assertEqual("BLOCKED", res["status"])
        self.assertEqual(["alpha", "android-core"], [p["provider_id"] for p in res["providers"]])
        android_p = [p for p in res["providers"] if p["provider_id"] == "android-core"][0]
        self.assertEqual("BLOCKED", android_p["status"])
        self.assertTrue(any("Missing result for provider 'android-core'" in b for b in res["blockers"]))

    def test_contradictory_provider_result_demoted_to_blocked(self) -> None:
        bad_pass = make_provider_result("alpha", "PASS", checks=[make_check("unit", "FAIL")])
        plan = [{"id": "alpha", "required": True}]
        res = aggregate_results(plan, [bad_pass])
        self.assertEqual("BLOCKED", res["status"])
        alpha_p = res["providers"][0]
        self.assertEqual("BLOCKED", alpha_p["status"])
        self.assertTrue(any("Contradictory result" in b for b in res["blockers"]))


if __name__ == "__main__":
    unittest.main()
