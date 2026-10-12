"""Unit tests for the Flutter quality capability configuration validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_flutter_quality import validate_flutter_config  # noqa: E402


def valid_config() -> dict:
    return {
        "schema_version": 1,
        "capabilities": {
            "format": ["./scripts/dartfmt.sh"],
            "analyze": ["fvm", "flutter", "analyze"],
            "boundaries": ["./scripts/check_module_boundaries.sh"],
            "license": ["./scripts/check_license_header.sh"],
            "test": ["melos", "run", "test"],
            "coverage": {
                "command": ["./scripts/testWithCoverage.sh"],
                "lcov_path": "coverage_report/lcov.info",
                "threshold": 0.85,
            },
            "acceptance": ["./scripts/acceptance_check.sh"],
        },
        "profiles": {
            "pr": ["format", "analyze", "test"],
            "epic": ["format", "analyze", "boundaries", "license", "test", "coverage"],
        },
    }


class FlutterQualityConfigTests(unittest.TestCase):
    def test_valid_config_passes_validation(self) -> None:
        res = validate_flutter_config(valid_config(), "epic")
        self.assertEqual("PASS", res["status"])
        self.assertEqual([], res["findings"])

    def test_shell_string_command_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["analyze"] = "fvm flutter analyze"
        res = validate_flutter_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_command_format", [f["code"] for f in res["findings"]])

    def test_empty_command_array_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["test"] = []
        res = validate_flutter_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("command_array_empty", [f["code"] for f in res["findings"]])

    def test_missing_boundaries_command_blocks_epic_profile(self) -> None:
        cfg = valid_config()
        del cfg["capabilities"]["boundaries"]
        res = validate_flutter_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("missing_capability_definition", [f["code"] for f in res["findings"]])

    def test_invalid_coverage_threshold_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["coverage"]["threshold"] = 1.5
        res = validate_flutter_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_coverage_threshold", [f["code"] for f in res["findings"]])

    def test_schema_file_is_valid_json_schema(self) -> None:
        schema_path = SCRIPT_DIR.parent / "schemas/flutter-quality.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertEqual("object", schema["type"])
        self.assertEqual(False, schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])


if __name__ == "__main__":
    unittest.main()
