"""Unit tests for the iOS quality capability configuration validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_ios_quality import validate_ios_config  # noqa: E402


def valid_config() -> dict:
    return {
        "schema_version": 1,
        "capabilities": {
            "format": ["swiftformat", "--config", "quality/.swiftformat", "--lint", "."],
            "lint": ["swiftlint", "lint", "--config", "quality/.swiftlint.yml", "--strict"],
            "architecture": ["swift", "test", "--package-path", "ArchTests"],
            "boundaries": ["./scripts/check_module_boundaries.sh"],
            "test": ["swift", "test"],
            "coverage": {
                "command": ["./scripts/check_coverage_thresholds.sh"],
                "profdata_path": "default.profdata",
                "threshold": 0.85,
            },
            "acceptance": ["./scripts/acceptance_check.sh"],
        },
        "profiles": {
            "pr": ["format", "lint", "test"],
            "epic": ["format", "lint", "architecture", "boundaries", "test", "coverage"],
        },
    }


class IOSQualityConfigTests(unittest.TestCase):
    def test_valid_config_passes_validation(self) -> None:
        res = validate_ios_config(valid_config(), "epic")
        self.assertEqual("PASS", res["status"])
        self.assertEqual([], res["findings"])

    def test_shell_string_command_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["lint"] = "swiftlint lint --strict"
        res = validate_ios_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_command_format", [f["code"] for f in res["findings"]])

    def test_empty_command_array_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["test"] = []
        res = validate_ios_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("command_array_empty", [f["code"] for f in res["findings"]])

    def test_missing_required_profile_is_rejected(self) -> None:
        cfg = valid_config()
        del cfg["profiles"]["epic"]
        res = validate_ios_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("profile_not_configured", [f["code"] for f in res["findings"]])

    def test_missing_architecture_blocks_epic_profile(self) -> None:
        cfg = valid_config()
        del cfg["capabilities"]["architecture"]
        res = validate_ios_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("missing_capability_definition", [f["code"] for f in res["findings"]])

    def test_schema_file_is_valid_json_schema(self) -> None:
        schema_path = SCRIPT_DIR.parent / "schemas/ios-quality.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertEqual("object", schema["type"])
        self.assertEqual(False, schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])


if __name__ == "__main__":
    unittest.main()
