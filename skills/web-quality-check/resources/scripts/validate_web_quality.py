"""Validator and execution runner for Web quality capability configuration (.agents/quality/web-quality.json)."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

VALID_PROFILES = {"pr", "epic", "scheduled", "release"}
MANDATORY_PR_CAPABILITIES = {"type_check", "lint", "test_unit"}
MANDATORY_EPIC_CAPABILITIES = {"type_check", "lint", "test_unit", "test_e2e"}


def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    f = {"code": code, "message": message}
    f.update(extra)
    return f


def validate_manifest(
    config: dict[str, Any],
    requested_profile: str = "pr",
    repo_root: Path | str | None = None,
    require_watchdog_evidence: bool = False,
) -> dict[str, Any]:
    """Validate Web quality capability manifest and check readiness for requested profile."""
    findings: list[dict[str, Any]] = []

    if config.get("schema_version") != 1:
        findings.append(
            _finding(
                "unsupported_version",
                f"Unsupported schema_version '{config.get('schema_version')}', expected 1",
            )
        )

    capabilities = config.get("capabilities", {})
    if not isinstance(capabilities, dict):
        findings.append(_finding("missing_capabilities", "Missing or invalid 'capabilities' object"))
        return {"status": "BLOCKED", "findings": findings}

    for cap_name, cap_val in capabilities.items():
        if cap_name == "coverage":
            if not isinstance(cap_val, dict):
                findings.append(_finding("invalid_coverage_config", "Coverage capability must be an object"))
                continue
            cmd = cap_val.get("command")
            if not isinstance(cmd, list) or not all(isinstance(arg, str) for arg in cmd):
                findings.append(
                    _finding(
                        "invalid_command_format",
                        f"Coverage command for '{cap_name}' must be an array of string arguments",
                        capability=cap_name,
                    )
                )
            elif len(cmd) == 0:
                findings.append(
                    _finding(
                        "command_array_empty",
                        f"Coverage command for '{cap_name}' is empty []",
                        capability=cap_name,
                    )
                )
            threshold = cap_val.get("threshold")
            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1.0:
                findings.append(
                    _finding(
                        "invalid_coverage_threshold",
                        "Coverage threshold must be between 0.0 and 1.0",
                        capability=cap_name,
                    )
                )
        else:
            if not isinstance(cap_val, list) or not all(isinstance(arg, str) for arg in cap_val):
                findings.append(
                    _finding(
                        "invalid_command_format",
                        f"Capability command for '{cap_name}' must be an array of string arguments, not a string or shell command",
                        capability=cap_name,
                    )
                )
            elif len(cap_val) == 0:
                findings.append(
                    _finding(
                        "command_array_empty",
                        f"Capability command for '{cap_name}' is empty []",
                        capability=cap_name,
                    )
                )

    profiles = config.get("profiles", {})
    if not isinstance(profiles, dict):
        findings.append(_finding("missing_profiles", "Missing or invalid 'profiles' object"))
        return {"status": "BLOCKED", "findings": findings}

    profile_caps = profiles.get(requested_profile)
    if profile_caps is None:
        findings.append(
            _finding(
                "profile_not_configured",
                f"Requested profile '{requested_profile}' is not configured in profiles",
            )
        )
    elif not isinstance(profile_caps, list):
        findings.append(
            _finding(
                "invalid_profile_format",
                f"Profile '{requested_profile}' must be an array of capability names",
            )
        )
    else:
        for cap in profile_caps:
            if cap not in capabilities:
                findings.append(
                    _finding(
                        "missing_capability_definition",
                        f"Profile '{requested_profile}' requires capability '{cap}', which is not defined in capabilities",
                        capability=cap,
                    )
                )

        if requested_profile == "pr":
            for mandatory in sorted(MANDATORY_PR_CAPABILITIES):
                if mandatory not in capabilities:
                    findings.append(
                        _finding(
                            "missing_mandatory_capability",
                            f"Profile '{requested_profile}' mandates capability '{mandatory}' in capabilities",
                            capability=mandatory,
                        )
                    )
                elif mandatory not in profile_caps:
                    findings.append(
                        _finding(
                            "missing_profile_capability",
                            f"Profile '{requested_profile}' mandates capability '{mandatory}' in its profile array",
                            capability=mandatory,
                        )
                    )

        if requested_profile in ("epic", "release"):
            for mandatory in sorted(MANDATORY_EPIC_CAPABILITIES):
                if mandatory not in capabilities:
                    findings.append(
                        _finding(
                            "missing_mandatory_capability",
                            f"Profile '{requested_profile}' mandates capability '{mandatory}' in capabilities",
                            capability=mandatory,
                        )
                    )
                elif mandatory not in profile_caps:
                    findings.append(
                        _finding(
                            "missing_profile_capability",
                            f"Profile '{requested_profile}' mandates capability '{mandatory}' in its profile array",
                            capability=mandatory,
                        )
                    )

            if require_watchdog_evidence and repo_root is not None:
                root_path = Path(repo_root)
                evidence_file = root_path / "build" / "test-results" / "playwright.xml"
                if not evidence_file.is_file():
                    findings.append(
                        _finding(
                            "missing_watchdog_evidence",
                            f"Profile '{requested_profile}' requires Playwright watchdog evidence artifact at '{evidence_file}'",
                            location=str(evidence_file),
                        )
                    )

    return {
        "status": "BLOCKED" if findings else "PASS",
        "findings": sorted(findings, key=lambda f: (f.get("code", ""), f.get("capability", ""))),
    }


def validate_web_config(
    config: dict[str, Any],
    requested_profile: str = "pr",
    repo_root: Path | str | None = None,
) -> dict[str, Any]:
    """Compatibility alias for validate_manifest."""
    return validate_manifest(config, requested_profile, repo_root)


def _resolve_category(cap_name: str) -> str:
    if "type" in cap_name:
        return "type-check"
    if "lint" in cap_name:
        return "lint"
    if "unit" in cap_name:
        return "unit-test"
    if "e2e" in cap_name or "playwright" in cap_name:
        return "e2e-test"
    if "contract" in cap_name:
        return "contract"
    if "coverage" in cap_name:
        return "coverage"
    return "quality-check"


def run_capabilities(
    config: dict[str, Any],
    profile: str,
    repository_sha: str,
    repo_root: Path | str,
    base_ref: str = "main",
    provider_id: str = "web-quality",
    skills_dir: Path | str | None = None,
    check_watchdog_evidence: bool = True,
) -> dict[str, Any]:
    """Execute capabilities for the requested profile and return a Provider Result Contract v1 document."""
    start_time = time.time()
    root_path = Path(repo_root).resolve()

    manifest_validation = validate_manifest(
        config,
        requested_profile=profile,
        repo_root=root_path,
        require_watchdog_evidence=False,
    )

    resolved_skills_dir = (
        Path(skills_dir).resolve()
        if skills_dir
        else Path(__file__).resolve().parent.parent.parent.parent
    )

    if manifest_validation["status"] == "BLOCKED":
        duration = round(time.time() - start_time, 3)
        init_blockers: list[dict[str, Any]] = manifest_validation["findings"]
        return {
            "provider_id": provider_id,
            "contract_version": 1,
            "profile": profile,
            "repository_sha": repository_sha,
            "status": "BLOCKED",
            "checks": [],
            "coverage": {},
            "evidence": [],
            "started_head": repository_sha,
            "finished_head": repository_sha,
            "duration": duration,
            "blockers": init_blockers,
            "warnings": [],
        }

    capabilities = config.get("capabilities", {})
    profiles = config.get("profiles", {})
    caps_to_run: list[str] = profiles.get(profile, [])

    checks: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    overall_status = "PASS"

    for cap_name in caps_to_run:
        cap_val = capabilities.get(cap_name)
        if cap_name == "coverage":
            cmd = cap_val.get("command", [])
        else:
            cmd = cap_val

        substituted_cmd: list[str] = []
        for arg in cmd:
            arg_sub = arg.replace("{skills_dir}", str(resolved_skills_dir)).replace(
                "{base_ref}", base_ref
            )
            substituted_cmd.append(arg_sub)

        check_start = time.time()
        check_status = "PASS"
        summary = f"Capability '{cap_name}' passed"

        try:
            res = subprocess.run(
                substituted_cmd,
                cwd=str(root_path),
                capture_output=True,
                text=True,
                check=False,
            )
            check_duration = round(time.time() - check_start, 3)

            if "contract" in cap_name:
                if res.returncode == 0:
                    check_status = "PASS"
                elif res.returncode == 2:
                    check_status = "BLOCKED"
                    summary = f"Capability '{cap_name}' blocked: {res.stderr.strip() or res.stdout.strip()}"
                else:
                    check_status = "FAIL"
                    summary = f"Capability '{cap_name}' failed: {res.stderr.strip() or res.stdout.strip()}"
            else:
                if res.returncode != 0:
                    check_status = "FAIL"
                    summary = f"Capability '{cap_name}' failed with exit code {res.returncode}: {res.stderr.strip() or res.stdout.strip()}"

        except (FileNotFoundError, PermissionError) as e:
            check_duration = round(time.time() - check_start, 3)
            check_status = "BLOCKED"
            summary = (
                f"Binary execution blocker for '{cap_name}': executable not found or inaccessible in PATH. "
                f"Remediation: ensure required tools (e.g. node, npm, astro, playwright) are installed. Details: {e}"
            )
            blockers.append(
                _finding(
                    "binary_execution_blocker",
                    summary,
                    capability=cap_name,
                    command=substituted_cmd,
                )
            )

        evidence_id = f"{cap_name}-evidence"
        checks.append(
            {
                "id": cap_name,
                "category": _resolve_category(cap_name),
                "status": check_status,
                "source": " ".join(substituted_cmd),
                "duration": check_duration,
                "summary": summary,
                "evidence_refs": [evidence_id],
            }
        )
        evidence.append(
            {
                "id": evidence_id,
                "type": "command",
                "source": " ".join(substituted_cmd),
                "location": f"artifacts/{cap_name}.log",
            }
        )

        if check_status == "FAIL":
            overall_status = "FAIL"
        elif check_status == "BLOCKED" and overall_status != "FAIL":
            overall_status = "BLOCKED"

    # For epic and release profiles, check watchdog evidence artifact if requested
    if profile in ("epic", "release") and check_watchdog_evidence:
        evidence_file = root_path / "build" / "test-results" / "playwright.xml"
        if not evidence_file.is_file():
            blockers.append(
                _finding(
                    "missing_watchdog_evidence",
                    f"Profile '{profile}' mandates Playwright watchdog evidence artifact at '{evidence_file}'",
                    location=str(evidence_file),
                )
            )
            if overall_status != "FAIL":
                overall_status = "BLOCKED"

    total_duration = round(time.time() - start_time, 3)
    return {
        "provider_id": provider_id,
        "contract_version": 1,
        "profile": profile,
        "repository_sha": repository_sha,
        "status": overall_status,
        "checks": checks,
        "coverage": {},
        "evidence": evidence,
        "started_head": repository_sha,
        "finished_head": repository_sha,
        "duration": total_duration,
        "blockers": blockers,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Web quality capability manifest.")
    parser.add_argument("config_file", help="Path to .agents/quality/web-quality.json")
    parser.add_argument("--profile", default="pr", help="Requested profile (pr, epic, scheduled, release)")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")

    args = parser.parse_args()
    config_path = Path(args.config_file)
    if not config_path.is_file():
        res = {
            "status": "BLOCKED",
            "findings": [
                _finding("config_file_not_found", f"Capability manifest '{args.config_file}' not found")
            ],
        }
    else:
        try:
            data = json.loads(config_path.read_text())
            res = validate_manifest(data, args.profile, repo_root=args.repo_root)
        except json.JSONDecodeError as err:
            res = {
                "status": "BLOCKED",
                "findings": [_finding("invalid_json", f"JSON parsing failed: {err}")],
            }

    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
