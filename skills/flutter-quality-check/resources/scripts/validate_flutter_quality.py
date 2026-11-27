"""Validator for the Flutter quality capability configuration (.agents/quality/flutter-quality.json)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_QC_SCRIPTS_DIR = (
    Path(__file__).resolve().parents[3] / "quality_check" / "resources" / "scripts"
)
if str(_QC_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_QC_SCRIPTS_DIR))

from _provider_manifest_common import (  # type: ignore[import-not-found]  # noqa: E402
    format_validator_cli_output,
    validate_additive_provider_fields,
    validate_dual_floor_coverage,
)


def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    f = {"code": code, "message": message}
    f.update(extra)
    return f


def validate_flutter_config(
    config: dict[str, Any],
    requested_profile: str = "pr",
) -> dict[str, Any]:
    """Validate Flutter project capability manifest and check readiness for the requested profile."""
    findings: list[dict[str, Any]] = []

    if config.get("schema_version") != 1:
        findings.append(
            _finding(
                "unsupported_version",
                f"Unsupported schema_version '{config.get('schema_version')}', expected 1",
            )
        )

    findings.extend(validate_additive_provider_fields(config))

    capabilities = config.get("capabilities", {})
    if not isinstance(capabilities, dict):
        findings.append(
            _finding("missing_capabilities", "Missing or invalid 'capabilities' object")
        )
        return {"status": "BLOCKED", "findings": findings}

    if len(capabilities) == 0:
        findings.append(_finding("empty_capabilities", "Capabilities object is empty"))

    for cap_name, cap_val in capabilities.items():
        if cap_name == "coverage":
            if not isinstance(cap_val, dict):
                findings.append(
                    _finding(
                        "invalid_coverage_config",
                        "Coverage capability must be an object",
                        capability=cap_name,
                    )
                )
                continue
            cmd = cap_val.get("command")
            if not isinstance(cmd, list) or not all(
                isinstance(arg, str) for arg in cmd
            ):
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
            if (
                isinstance(threshold, bool)
                or not isinstance(threshold, (int, float))
                or threshold < 0
                or threshold > 1.0
            ):
                findings.append(
                    _finding(
                        "invalid_coverage_threshold",
                        "Coverage threshold must be between 0.0 and 1.0",
                        capability=cap_name,
                    )
                )
            findings.extend(validate_dual_floor_coverage(cap_val, capability=cap_name))
        else:
            if not isinstance(cap_val, list) or not all(
                isinstance(arg, str) for arg in cap_val
            ):
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
        findings.append(
            _finding("missing_profiles", "Missing or invalid 'profiles' object")
        )
        return {"status": "BLOCKED", "findings": findings}

    profile_caps = profiles.get(requested_profile)
    if profile_caps is None:
        findings.append(
            _finding(
                "profile_not_configured",
                f"Requested profile '{requested_profile}' is not configured in profiles",
                profile=requested_profile,
            )
        )
    elif not isinstance(profile_caps, list):
        findings.append(
            _finding(
                "invalid_profile_format",
                f"Profile '{requested_profile}' must be an array of capability names",
                profile=requested_profile,
            )
        )
    else:
        if len(profile_caps) == 0:
            findings.append(
                _finding(
                    "empty_profile_selection",
                    f"Profile '{requested_profile}' has empty capability selection",
                    profile=requested_profile,
                )
            )
        for cap in profile_caps:
            if cap not in capabilities:
                findings.append(
                    _finding(
                        "missing_capability_definition",
                        f"Profile '{requested_profile}' requires capability '{cap}', which is not defined in capabilities",
                        capability=cap,
                    )
                )

        if requested_profile == "epic":
            for req_cap in ("boundaries", "test", "coverage"):
                if req_cap not in profile_caps:
                    findings.append(
                        _finding(
                            "missing_epic_capability",
                            f"Epic profile requires '{req_cap}' capability in profile selection",
                            capability=req_cap,
                        )
                    )

    return {
        "status": "BLOCKED" if findings else "PASS",
        "findings": sorted(
            findings,
            key=lambda f: (
                f.get("code", ""),
                f.get("capability", ""),
                f.get("field", ""),
                f.get("message", ""),
            ),
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Flutter quality capability manifest."
    )
    parser.add_argument(
        "config_file", help="Path to .agents/quality/flutter-quality.json"
    )
    parser.add_argument(
        "--profile",
        default="pr",
        help="Requested profile (pr, epic, scheduled, release)",
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Expand capability breakdown on PASS"
    )
    parser.add_argument(
        "--json", dest="as_json", action="store_true", help="Emit full JSON output"
    )

    args = parser.parse_args()
    config_path = Path(args.config_file)
    data: dict[str, Any] = {}
    if not config_path.is_file():
        res: dict[str, Any] = {
            "status": "BLOCKED",
            "findings": [
                _finding(
                    "config_file_not_found",
                    f"Capability manifest '{args.config_file}' not found",
                )
            ],
        }
    else:
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            res = validate_flutter_config(data, args.profile)
        except json.JSONDecodeError as err:
            res = {
                "status": "BLOCKED",
                "findings": [_finding("invalid_json", f"JSON parsing failed: {err}")],
            }

    profiles_obj = data.get("profiles") if isinstance(data, dict) else None
    profile_caps = (
        profiles_obj.get(args.profile) if isinstance(profiles_obj, dict) else None
    )
    details = [str(c) for c in profile_caps] if isinstance(profile_caps, list) else None
    item_count = (
        len(profile_caps)
        if isinstance(profile_caps, list)
        else (
            len(data.get("capabilities", {}))
            if isinstance(data.get("capabilities"), dict)
            else 0
        )
    )
    print(
        format_validator_cli_output(
            "flutter-quality",
            args.profile,
            res,
            verbose=bool(args.verbose),
            as_json=bool(args.as_json),
            item_count=item_count,
            item_label="caps",
            details=details,
        )
    )
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
