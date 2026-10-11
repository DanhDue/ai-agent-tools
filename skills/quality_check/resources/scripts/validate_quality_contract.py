"""Provider contract validator implementation.

Validates project quality registries, normalized invocations, provider results,
and reconciles provider results against the execution plan according to the
version 1 quality contracts.
"""

from __future__ import annotations

import copy
import re
from typing import Any

VALID_PROFILES = {"pr", "epic", "scheduled", "release"}
VALID_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}
VALID_NOT_APPLICABLE_CODES = {
    "profile_policy",
    "scope_unmodified",
    "capability_not_configured",
    "target_absent",
    "platform_not_applicable",
}
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    f = {"code": code, "message": message}
    f.update(extra)
    return f


def _sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Deduplicate findings with identical representations
    unique: dict[str, dict[str, Any]] = {}
    for f in findings:
        key = (f.get("code", ""), f.get("provider_id", ""), f.get("field", ""), f.get("message", ""))
        if key not in unique:
            unique[key] = f
    return sorted(
        unique.values(),
        key=lambda item: (
            item.get("code", ""),
            item.get("provider_id", ""),
            item.get("field", ""),
            item.get("message", ""),
        ),
    )


def validate_registry(
    registry_data: dict[str, Any],
    requested_profile: str,
    available_skills: set[str] | None = None,
) -> dict[str, Any]:
    """Validate project provider registry and select providers for the requested profile."""
    findings: list[dict[str, Any]] = []

    # Check top-level fields
    allowed_top = {"schema_version", "providers"}
    for k in sorted(registry_data.keys()):
        if k not in allowed_top:
            findings.append(_finding("unknown_field", f"Unknown top-level field '{k}'", field=k))

    for req in ("schema_version", "providers"):
        if req not in registry_data:
            findings.append(_finding("missing_field", f"Missing required top-level field '{req}'", field=req))

    schema_version = registry_data.get("schema_version")
    if schema_version != 1:
        findings.append(
            _finding(
                "unsupported_version",
                f"Unsupported schema_version '{schema_version}', expected 1",
            )
        )

    providers_raw = registry_data.get("providers")
    if not isinstance(providers_raw, list):
        if "providers" in registry_data:
            findings.append(_finding("empty_providers", "Registry providers must be a non-empty list"))
        return {
            "status": "BLOCKED",
            "providers": [],
            "findings": _sort_findings(findings),
        }

    if len(providers_raw) == 0:
        findings.append(_finding("empty_providers", "Registry providers list is empty"))

    allowed_provider_fields = {"id", "skill", "required", "profiles"}
    seen_ids: set[str] = set()
    valid_providers: list[dict[str, Any]] = []

    for idx, p in enumerate(providers_raw):
        if not isinstance(p, dict):
            findings.append(_finding("malformed_provider", f"Provider at index {idx} must be an object"))
            continue

        p_id = p.get("id")
        # Check unknown fields in provider
        for k in sorted(p.keys()):
            if k not in allowed_provider_fields:
                findings.append(
                    _finding(
                        "unknown_field",
                        f"Unknown provider field '{k}'",
                        provider_id=p_id or f"index_{idx}",
                        field=k,
                    )
                )

        # Check missing fields
        for req in ("id", "skill", "required", "profiles"):
            if req not in p:
                findings.append(
                    _finding(
                        "missing_field",
                        f"Missing required provider field '{req}'",
                        provider_id=p_id or f"index_{idx}",
                        field=req,
                    )
                )

        if p_id:
            if p_id in seen_ids:
                findings.append(
                    _finding(
                        "duplicate_id",
                        f"Duplicate provider id '{p_id}'",
                        provider_id=p_id,
                    )
                )
            else:
                seen_ids.add(p_id)

        profiles = p.get("profiles")
        if isinstance(profiles, list):
            for prof in profiles:
                if prof not in VALID_PROFILES:
                    findings.append(
                        _finding(
                            "unsupported_profile",
                            f"Unsupported profile '{prof}' in provider '{p_id}'",
                            provider_id=p_id,
                        )
                    )
        elif "profiles" in p:
            findings.append(
                _finding(
                    "unsupported_profile",
                    f"Profiles for provider '{p_id}' must be a list",
                    provider_id=p_id,
                )
            )

        valid_providers.append(p)

    selected_providers: list[dict[str, Any]] = []
    if requested_profile in VALID_PROFILES:
        for p in valid_providers:
            profs = p.get("profiles", [])
            if isinstance(profs, list) and requested_profile in profs:
                p_id = p.get("id")
                skill = p.get("skill")
                if skill and available_skills is not None:
                    if skill not in available_skills:
                        findings.append(
                            _finding(
                                "unresolved_skill",
                                f"Provider skill '{skill}' could not be resolved",
                                provider_id=p_id,
                            )
                        )
                selected_providers.append(p)
    else:
        findings.append(
            _finding(
                "unsupported_profile",
                f"Requested profile '{requested_profile}' is not supported",
            )
        )

    # Sort selected providers by id for deterministic ordering
    selected_providers.sort(key=lambda item: item.get("id", ""))

    if len(selected_providers) == 0 and len(providers_raw) > 0 and requested_profile in VALID_PROFILES:
        findings.append(
            _finding(
                "empty_selection",
                f"No providers matched the requested profile '{requested_profile}'",
            )
        )

    status = "BLOCKED" if findings else "PASS"
    return {
        "status": status,
        "providers": selected_providers if status == "PASS" else [],
        "findings": _sort_findings(findings),
    }


def normalize_invocation(invocation_data: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize an orchestrator invocation request."""
    findings: list[dict[str, Any]] = []
    allowed_fields = {"contract_version", "profile", "base_ref", "repository_sha", "provider_id", "required"}

    for k in sorted(invocation_data.keys()):
        if k not in allowed_fields:
            findings.append(_finding("unknown_field", f"Unknown invocation field '{k}'", field=k))

    contract_version = invocation_data.get("contract_version", 1)
    if contract_version != 1:
        findings.append(
            _finding(
                "unsupported_version",
                f"Unsupported contract_version '{contract_version}', expected 1",
            )
        )

    profile = invocation_data.get("profile", "pr")
    if profile not in VALID_PROFILES:
        findings.append(_finding("unsupported_profile", f"Unsupported profile '{profile}'"))

    sha = invocation_data.get("repository_sha")
    if not isinstance(sha, str) or not SHA_PATTERN.match(sha):
        findings.append(_finding("invalid_repository_sha", f"Invalid repository_sha '{sha}'"))

    norm = copy.deepcopy(invocation_data)
    norm["contract_version"] = 1
    norm["profile"] = profile

    status = "BLOCKED" if findings else "PASS"
    return {
        "status": status,
        "invocation": norm if status == "PASS" else None,
        "findings": _sort_findings(findings),
    }


def validate_provider_result(
    result_data: dict[str, Any],
    invocation_data: dict[str, Any],
) -> dict[str, Any]:
    """Validate a provider result document against contract and invocation identity."""
    findings: list[dict[str, Any]] = []

    contract_version = result_data.get("contract_version")
    if contract_version != 1:
        findings.append(
            _finding(
                "unsupported_version",
                f"Unsupported contract_version '{contract_version}', expected 1",
            )
        )

    # Identity matching against invocation
    exp_provider_id = invocation_data.get("provider_id")
    if exp_provider_id and result_data.get("provider_id") != exp_provider_id:
        findings.append(
            _finding(
                "provider_id_mismatch",
                f"Result provider_id '{result_data.get('provider_id')}' != invocation '{exp_provider_id}'",
            )
        )

    exp_profile = invocation_data.get("profile")
    if exp_profile and result_data.get("profile") != exp_profile:
        findings.append(
            _finding(
                "profile_mismatch",
                f"Result profile '{result_data.get('profile')}' != invocation '{exp_profile}'",
            )
        )

    exp_sha = invocation_data.get("repository_sha")
    if exp_sha:
        if result_data.get("repository_sha") != exp_sha:
            findings.append(
                _finding(
                    "repository_sha_mismatch",
                    f"Result repository_sha '{result_data.get('repository_sha')}' != invocation '{exp_sha}'",
                )
            )
        if result_data.get("started_head") != exp_sha or result_data.get("finished_head") != exp_sha:
            findings.append(
                _finding(
                    "sha_drift",
                    "Started head or finished head does not match repository_sha",
                )
            )

    duration = result_data.get("duration")
    if duration is not None:
        if not isinstance(duration, (int, float)) or duration < 0:
            findings.append(_finding("invalid_duration", f"Invalid duration '{duration}'"))
    else:
        findings.append(_finding("missing_field", "Missing duration in result", field="duration"))

    status = result_data.get("status")
    if status not in VALID_STATUSES:
        findings.append(_finding("invalid_status", f"Invalid status '{status}'"))

    # Validate coverage
    coverage = result_data.get("coverage")
    if isinstance(coverage, dict):
        for metric, cov in coverage.items():
            if not isinstance(cov, dict):
                findings.append(_finding("invalid_coverage", f"Coverage for '{metric}' must be object"))
                continue
            measured = cov.get("measured")
            threshold = cov.get("threshold")
            if not isinstance(measured, (int, float)) or measured < 0 or measured > 1.0:
                findings.append(_finding("invalid_coverage", f"Invalid measured coverage '{measured}' in '{metric}'"))
            if threshold is not None and (not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1.0):
                findings.append(_finding("invalid_coverage", f"Invalid threshold coverage '{threshold}' in '{metric}'"))
    elif coverage is not None:
        findings.append(_finding("invalid_coverage", "Coverage must be an object"))

    # Validate evidence
    evidence = result_data.get("evidence")
    evidence_ids: set[str] = set()
    has_applicability_evidence = False

    if isinstance(evidence, list):
        for idx, ev in enumerate(evidence):
            if not isinstance(ev, dict):
                findings.append(_finding("malformed_evidence", f"Evidence at index {idx} must be an object"))
                continue
            ev_id = ev.get("id")
            if ev_id:
                evidence_ids.add(ev_id)
            for req in ("id", "type", "source"):
                if req not in ev:
                    findings.append(_finding("malformed_evidence", f"Missing field '{req}' in evidence {ev_id or idx}"))
            if "location" not in ev and "digest" not in ev:
                findings.append(_finding("malformed_evidence", f"Evidence '{ev_id or idx}' missing location or digest"))
            if ev.get("type") == "applicability":
                has_applicability_evidence = True
    elif evidence is not None:
        findings.append(_finding("malformed_evidence", "Evidence must be a list"))

    # Validate checks
    checks = result_data.get("checks")
    if isinstance(checks, list):
        for idx, chk in enumerate(checks):
            if not isinstance(chk, dict):
                findings.append(_finding("malformed_check", f"Check at index {idx} must be an object"))
                continue
            chk_id = chk.get("id") or f"check_{idx}"
            req_check_fields = ("id", "category", "status", "source", "duration", "summary", "evidence_refs")
            for req in req_check_fields:
                if req not in chk:
                    findings.append(
                        _finding(
                            "missing_field",
                            f"Missing required field '{req}' in check '{chk_id}'",
                            field=req,
                        )
                    )

            chk_dur = chk.get("duration")
            if chk_dur is not None and (not isinstance(chk_dur, (int, float)) or chk_dur < 0):
                findings.append(_finding("invalid_duration", f"Invalid duration in check '{chk_id}'"))

            chk_status = chk.get("status")
            if chk_status == "NOT_APPLICABLE":
                reason = chk.get("not_applicable_reason")
                if not isinstance(reason, dict) or "code" not in reason or "detail" not in reason:
                    findings.append(
                        _finding(
                            "missing_not_applicable_reason",
                            f"Check '{chk_id}' missing structured not_applicable_reason",
                        )
                    )
                else:
                    code = reason.get("code")
                    if code not in VALID_NOT_APPLICABLE_CODES:
                        findings.append(
                            _finding(
                                "invalid_not_applicable_reason",
                                f"Invalid not_applicable_reason code '{code}' in check '{chk_id}'",
                            )
                        )

            refs = chk.get("evidence_refs")
            if isinstance(refs, list):
                for ref in refs:
                    if ref not in evidence_ids:
                        findings.append(
                            _finding(
                                "unresolved_evidence_reference",
                                f"Evidence reference '{ref}' in check '{chk_id}' not found in evidence",
                            )
                        )
    elif checks is not None:
        findings.append(_finding("malformed_check", "Checks must be a list"))

    if status == "NOT_APPLICABLE" and not has_applicability_evidence:
        findings.append(
            _finding(
                "missing_applicability_evidence",
                "Result status is NOT_APPLICABLE but no applicability evidence was provided",
            )
        )

    out_status = "BLOCKED" if findings else "PASS"
    return {
        "status": out_status,
        "findings": _sort_findings(findings),
    }


def reconcile_results(
    execution_plan: list[dict[str, Any]],
    provider_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Reconcile collected provider results against the execution plan."""
    findings: list[dict[str, Any]] = []
    results_by_id: dict[str, list[dict[str, Any]]] = {}

    for res in provider_results:
        p_id = res.get("provider_id", "")
        results_by_id.setdefault(p_id, []).append(res)

    reconciled_results: list[dict[str, Any]] = []

    for plan_entry in execution_plan:
        p_id = plan_entry.get("id", "")
        is_required = plan_entry.get("required", True)
        matching = results_by_id.get(p_id, [])

        if len(matching) == 0:
            findings.append(
                _finding(
                    "missing_result",
                    f"Missing result for provider '{p_id}'",
                    provider_id=p_id,
                )
            )
            reconciled_results.append(
                {
                    "provider_id": p_id,
                    "status": "BLOCKED",
                    "required": is_required,
                    "blockers": [f"Missing result for provider '{p_id}'"],
                }
            )
        elif len(matching) > 1:
            findings.append(
                _finding(
                    "duplicate_result",
                    f"Duplicate results ({len(matching)}) received for provider '{p_id}'",
                    provider_id=p_id,
                )
            )
            reconciled_results.append(
                {
                    "provider_id": p_id,
                    "status": "BLOCKED",
                    "required": is_required,
                    "blockers": [f"Duplicate results received for provider '{p_id}'"],
                }
            )
        else:
            reconciled_results.append(matching[0])

    reconciled_results.sort(key=lambda item: item.get("provider_id", ""))

    status = "PASS"
    if findings:
        status = "BLOCKED"
    elif any(r.get("status") == "FAIL" for r in reconciled_results):
        status = "FAIL"
    elif any(r.get("status") == "BLOCKED" for r in reconciled_results):
        status = "BLOCKED"

    return {
        "status": status,
        "results": reconciled_results,
        "findings": _sort_findings(findings),
    }


def _load_json_arg(arg: str) -> Any:
    import json
    from pathlib import Path

    p = Path(arg)
    if p.exists() and p.is_file():
        return json.loads(p.read_text())
    return json.loads(arg)


def main() -> int:
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Validate quality contracts and project manifests.")
    subparsers = parser.add_subparsers(dest="command")

    reg_parser = subparsers.add_parser("registry", help="Validate project registry")
    reg_parser.add_argument("registry_path", help="Path to registry JSON or JSON string")
    reg_parser.add_argument("--profile", default="pr", help="Requested profile (pr, epic, scheduled, release)")

    inv_parser = subparsers.add_parser("invocation", help="Validate and normalize invocation")
    inv_parser.add_argument("invocation_path", help="Path to invocation JSON or JSON string")

    res_parser = subparsers.add_parser("result", help="Validate provider result against invocation")
    res_parser.add_argument("result_path", help="Path to result JSON or JSON string")
    res_parser.add_argument("--invocation", required=True, help="Path to invocation JSON or JSON string")

    rec_parser = subparsers.add_parser("reconcile", help="Reconcile provider results with execution plan")
    rec_parser.add_argument("plan_path", help="Path to execution plan JSON or JSON string")
    rec_parser.add_argument("--results", nargs="+", required=True, help="Paths to provider result JSONs")

    args = parser.parse_args()

    if args.command == "registry":
        data = _load_json_arg(args.registry_path)
        res = validate_registry(data, args.profile)
        print(json.dumps(res, indent=2))
        return 0 if res["status"] == "PASS" else 1

    if args.command == "invocation":
        data = _load_json_arg(args.invocation_path)
        res = normalize_invocation(data)
        print(json.dumps(res, indent=2))
        return 0 if res["status"] == "PASS" else 1

    if args.command == "result":
        res_data = _load_json_arg(args.result_path)
        inv_data = _load_json_arg(args.invocation)
        res = validate_provider_result(res_data, inv_data)
        print(json.dumps(res, indent=2))
        return 0 if res["status"] == "PASS" else 1

    if args.command == "reconcile":
        plan_data = _load_json_arg(args.plan_path)
        results = [_load_json_arg(r) for r in args.results]
        res = reconcile_results(plan_data, results)
        print(json.dumps(res, indent=2))
        return 0 if res["status"] == "PASS" else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())

