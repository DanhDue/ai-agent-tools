"""Deterministic result aggregation engine for the provider-based quality gate.

Aggregates validated provider results into a unified decision payload and renders
standard executive reports according to the reduction precedence FAIL > BLOCKED > PASS.
"""

from __future__ import annotations

import copy
import json
from typing import Any


def aggregate_results(
    plan: list[dict[str, Any]],
    results: list[dict[str, Any]],
    invocation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministically aggregate provider results according to plan and status precedence."""
    plan_by_id = {item.get("id"): item for item in plan}
    normalized_providers: list[dict[str, Any]] = []

    for r in results:
        p = copy.deepcopy(r)
        p_id = p.get("provider_id", "")
        plan_item = plan_by_id.get(p_id, {})
        is_required = plan_item.get("required", p.get("required", True))
        p["required"] = is_required

        # Sort checks by check id for determinism
        checks = p.get("checks", [])
        if isinstance(checks, list):
            p["checks"] = sorted(checks, key=lambda c: c.get("id", ""))

        # Sort blockers and warnings
        p["blockers"] = sorted(p.get("blockers", []))
        p["warnings"] = sorted(p.get("warnings", []))

        # Check for all-NOT_APPLICABLE checks on a required provider
        all_checks_na = len(checks) > 0 and all(c.get("status") == "NOT_APPLICABLE" for c in checks)
        if (p.get("status") == "NOT_APPLICABLE" or all_checks_na) and is_required:
            p["status"] = "BLOCKED"
            blocker_msg = f"Required provider '{p_id}' has only NOT_APPLICABLE checks"
            if blocker_msg not in p["blockers"]:
                p["blockers"].append(blocker_msg)
                p["blockers"].sort()

        # Check for contradictory result (e.g. status PASS with failing check or sub-threshold coverage)
        if p.get("status") == "PASS":
            for c in checks:
                if c.get("status") in {"FAIL", "BLOCKED"}:
                    p["status"] = "BLOCKED"
                    blocker_msg = f"Contradictory result: provider reported PASS but check '{c.get('id')}' has status '{c.get('status')}'"
                    if blocker_msg not in p["blockers"]:
                        p["blockers"].append(blocker_msg)
            cov = p.get("coverage", {})
            if isinstance(cov, dict):
                for k, v in cov.items():
                    if isinstance(v, dict):
                        meas = v.get("measured")
                        thresh = v.get("threshold")
                        if thresh is not None and isinstance(meas, (int, float)) and isinstance(thresh, (int, float)):
                            if meas < thresh:
                                p["status"] = "BLOCKED"
                                blocker_msg = f"Contradictory result: provider reported PASS but coverage '{k}' is below threshold ({meas} < {thresh})"
                                if blocker_msg not in p["blockers"]:
                                    p["blockers"].append(blocker_msg)
            p["blockers"].sort()

        normalized_providers.append(p)

    # Synthesize missing providers declared in plan
    seen_result_ids = {r.get("provider_id") for r in results if r.get("provider_id")}
    for plan_item in plan:
        plan_id = plan_item.get("id")
        if plan_id and plan_id not in seen_result_ids:
            is_req = plan_item.get("required", True)
            synthetic = {
                "provider_id": plan_id,
                "contract_version": 1,
                "profile": invocation.get("profile") if invocation else (results[0].get("profile") if results else "pr"),
                "repository_sha": invocation.get("repository_sha") if invocation else (results[0].get("repository_sha") if results else ""),
                "status": "BLOCKED",
                "required": is_req,
                "checks": [],
                "coverage": {},
                "evidence": [],
                "started_head": "",
                "finished_head": "",
                "duration": 0.0,
                "blockers": [f"Missing result for provider '{plan_id}'"],
                "warnings": [],
            }
            normalized_providers.append(synthetic)

    # Sort providers by provider_id
    normalized_providers.sort(key=lambda item: item.get("provider_id", ""))

    # Evaluate precedence: FAIL > BLOCKED > PASS
    failing_providers = [p for p in normalized_providers if p.get("status") == "FAIL"]
    blocked_required = [p for p in normalized_providers if p.get("status") == "BLOCKED" and p.get("required", True)]
    all_required = [p for p in normalized_providers if p.get("required", True)]
    passed_required = [p for p in all_required if p.get("status") == "PASS"]

    all_blockers: list[str] = []
    all_warnings: list[str] = []
    coverage_summary: dict[str, Any] = {}

    for p in normalized_providers:
        for b in p.get("blockers", []):
            formatted_b = f"[{p.get('provider_id')}] {b}" if isinstance(b, str) else str(b)
            if formatted_b not in all_blockers:
                all_blockers.append(formatted_b)

        for w in p.get("warnings", []):
            formatted_w = f"[{p.get('provider_id')}] {w}" if isinstance(w, str) else str(w)
            if formatted_w not in all_warnings:
                all_warnings.append(formatted_w)

        cov = p.get("coverage", {})
        if isinstance(cov, dict):
            for k, v in cov.items():
                coverage_summary[f"{p.get('provider_id')}.{k}"] = v

    all_blockers.sort()
    all_warnings.sort()

    profile = invocation.get("profile") if invocation else (normalized_providers[0].get("profile") if normalized_providers else "pr")
    repo_sha = invocation.get("repository_sha") if invocation else (normalized_providers[0].get("repository_sha") if normalized_providers else "")

    status = "PASS"
    decision_trace = ""

    if failing_providers:
        status = "FAIL"
        fail_ids = ", ".join(f"'{p.get('provider_id')}'" for p in failing_providers)
        if blocked_required:
            blocked_ids = ", ".join(f"'{p.get('provider_id')}'" for p in blocked_required)
            decision_trace = f"FAIL outranks BLOCKED: provider(s) {fail_ids} failed while {blocked_ids} was blocked"
        else:
            decision_trace = f"Provider(s) {fail_ids} reported FAIL"
    elif blocked_required:
        status = "BLOCKED"
        reasons = []
        for p in blocked_required:
            p_id = p.get("provider_id", "")
            first_b = p.get("blockers", ["blocked"])[0]
            reasons.append(f"Required provider '{p_id}' has {first_b}")
        decision_trace = "; ".join(reasons)
    elif all_required and len(passed_required) == len(all_required):
        status = "PASS"
        decision_trace = f"All required providers passed ({len(passed_required)}/{len(all_required)})"
    else:
        status = "BLOCKED"
        decision_trace = "No required providers passed or empty execution plan"

    return {
        "status": status,
        "profile": profile,
        "repository_sha": repo_sha,
        "decision_trace": decision_trace,
        "providers": normalized_providers,
        "blockers": all_blockers,
        "warnings": all_warnings,
        "coverage_summary": coverage_summary,
    }


def render_executive_report(payload: dict[str, Any]) -> str:
    """Render a GitHub-flavored Markdown executive quality report from an aggregated payload."""
    status = payload.get("status", "UNKNOWN")
    profile = payload.get("profile", "unknown")
    sha = payload.get("repository_sha", "unknown")
    trace = payload.get("decision_trace", "")
    providers = payload.get("providers", [])
    blockers = payload.get("blockers", [])
    warnings = payload.get("warnings", [])
    coverage = payload.get("coverage_summary", {})

    lines: list[str] = [
        "# Executive Quality Report",
        "",
        "## Invocation Metadata",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| Overall Status | **{status}** |",
        f"| Profile | `{profile}` |",
        f"| Target SHA | `{sha}` |",
        f"| Decision Trace | {trace} |",
        "",
        "## Providers Summary",
        "",
        "| Provider ID | Required | Status | Duration (s) | Checks |",
        "|-------------|----------|--------|--------------|--------|",
    ]

    for p in providers:
        p_id = p.get("provider_id", "")
        req = "Yes" if p.get("required", True) else "No"
        p_status = p.get("status", "")
        dur = f"{p.get('duration', 0.0):.2f}"
        chk_cnt = len(p.get("checks", []))
        lines.append(f"| `{p_id}` | {req} | **{p_status}** | {dur} | {chk_cnt} |")

    lines.append("")
    lines.append("## Coverage Matrix")
    lines.append("")
    if coverage:
        lines.extend([
            "| Metric | Measured | Threshold | Status |",
            "|--------|----------|-----------|--------|",
        ])
        for k, v in sorted(coverage.items()):
            m = v.get("measured", 0.0)
            t = v.get("threshold", 0.0)
            cov_status = "PASS" if m >= t else "FAIL"
            lines.append(f"| `{k}` | {m:.1%} | {t:.1%} | **{cov_status}** |")
    else:
        lines.append("No coverage metrics reported.")

    lines.append("")
    lines.append("## Blockers")
    lines.append("")
    if blockers:
        for b in blockers:
            lines.append(f"- 🔴 {b}")
    else:
        lines.append("Zero blockers reported.")

    lines.append("")
    lines.append("## Warnings")
    lines.append("")
    if warnings:
        for w in warnings:
            lines.append(f"- 🟡 {w}")
    else:
        lines.append("Zero warnings reported.")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Aggregate validated provider results into executive quality report.")
    parser.add_argument("plan_file", help="Path to execution plan JSON")
    parser.add_argument("result_files", nargs="+", help="Paths to provider result JSON files")
    parser.add_argument("--markdown", action="store_true", help="Output markdown report instead of JSON")

    args = parser.parse_args()

    plan_data = json.loads(Path(args.plan_file).read_text())
    results_data = [json.loads(Path(f).read_text()) for f in args.result_files]

    payload = aggregate_results(plan_data, results_data)

    if args.markdown:
        print(render_executive_report(payload))
    else:
        print(json.dumps(payload, indent=2))

    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
