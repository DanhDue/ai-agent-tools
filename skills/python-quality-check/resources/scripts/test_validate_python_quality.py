"""Unit tests for the Python quality capability configuration validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from validate_python_quality import validate_python_config
except ImportError:
    validate_python_config = None  # type: ignore[assignment]


def valid_config() -> dict:
    return {
        "schema_version": 1,
        "capabilities": {
            "format": ["uv", "run", "ruff", "format", "--check", "."],
            "lint": ["uv", "run", "ruff", "check", "."],
            "type_check": ["uv", "run", "mypy", "--strict", "src"],
            "test": ["uv", "run", "pytest", "-m", "not slow and not acceptance and not live_llm"],
            "coverage": {
                "command": ["uv", "run", "pytest", "--cov=src", "--cov-report=json:coverage.json"],
                "threshold": 0.8,
            },
            "architecture": ["uv", "run", "lint-imports"],
            "schema": ["uv", "run", "python", "-m", "lyrics_sync.model", "--check-schema"],
            "acceptance": ["./scripts/run_e2e_acceptance.sh"],
        },
        "profiles": {
            "pr": ["format", "lint", "type_check", "test"],
            "epic": ["format", "lint", "type_check", "test", "coverage", "architecture", "acceptance"],
        },
    }


class PythonQualityConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        if validate_python_config is None:
            self.fail("validate_python_quality module not yet implemented (RED phase)")

    def test_valid_config_passes_validation(self) -> None:
        res = validate_python_config(valid_config(), "epic")
        self.assertEqual("PASS", res["status"])
        self.assertEqual([], res["findings"])

    def test_valid_config_pr_profile(self) -> None:
        res = validate_python_config(valid_config(), "pr")
        self.assertEqual("PASS", res["status"])
        self.assertEqual([], res["findings"])

    def test_shell_string_command_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["lint"] = "uv run ruff check ."  # string instead of array
        res = validate_python_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_command_format", [f["code"] for f in res["findings"]])

    def test_empty_command_array_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["lint"] = []
        res = validate_python_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("command_array_empty", [f["code"] for f in res["findings"]])

    def test_missing_architecture_command_blocks_epic_profile(self) -> None:
        cfg = valid_config()
        del cfg["capabilities"]["architecture"]
        res = validate_python_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("missing_architecture_authority", [f["code"] for f in res["findings"]])

    def test_invalid_coverage_threshold_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["coverage"]["threshold"] = 1.5
        res = validate_python_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_coverage_threshold", [f["code"] for f in res["findings"]])

    def test_profile_not_configured_is_rejected(self) -> None:
        res = validate_python_config(valid_config(), "non_existent_profile")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("profile_not_configured", [f["code"] for f in res["findings"]])

    def test_missing_capability_definition_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["profiles"]["pr"].append("missing_tool")
        res = validate_python_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("missing_capability_definition", [f["code"] for f in res["findings"]])

    def test_schema_file_is_valid_json_schema(self) -> None:
        schema_path = SCRIPT_DIR.parent / "schemas/python-quality.schema.json"
        self.assertTrue(schema_path.exists(), f"Schema file not found at {schema_path}")
        schema = json.loads(schema_path.read_text())
        self.assertEqual("object", schema["type"])
        self.assertEqual(False, schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])


if __name__ == "__main__":
    unittest.main()
