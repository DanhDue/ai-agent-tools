"""Unit tests for the Rust quality capability configuration validator."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_rust_quality import validate_rust_config


def valid_config() -> dict:
    return {
        "schema_version": 1,
        "capabilities": {
            "format": ["cargo", "fmt", "--all", "--", "--check"],
            "check": ["cargo", "check", "--all-targets"],
            "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
            "test": ["cargo", "test", "--workspace"],
            "coverage": {
                "command": ["cargo", "llvm-cov", "--workspace", "--fail-under-lines", "80"],
                "threshold": 0.8,
            },
            "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"],
        },
        "profiles": {
            "pr": ["format", "check", "clippy", "test"],
            "epic": ["format", "check", "clippy", "test", "coverage", "architecture"],
        },
    }


class RustQualityConfigTests(unittest.TestCase):
    def test_valid_config_passes_validation(self) -> None:
        res = validate_rust_config(valid_config(), "epic")
        self.assertEqual("PASS", res["status"])
        self.assertEqual([], res["findings"])

    def test_shell_string_command_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["check"] = "cargo check --all-targets"  # string instead of array
        res = validate_rust_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("invalid_command_format", [f["code"] for f in res["findings"]])

    def test_missing_architecture_command_blocks_epic_profile(self) -> None:
        cfg = valid_config()
        del cfg["capabilities"]["architecture"]
        res = validate_rust_config(cfg, "epic")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("missing_architecture_authority", [f["code"] for f in res["findings"]])

    def test_empty_command_array_is_rejected(self) -> None:
        cfg = valid_config()
        cfg["capabilities"]["check"] = []
        res = validate_rust_config(cfg, "pr")
        self.assertEqual("BLOCKED", res["status"])
        self.assertIn("command_array_empty", [f["code"] for f in res["findings"]])

    def test_schema_file_is_valid_json_schema(self) -> None:
        schema_path = SCRIPT_DIR.parent / "schemas/rust-quality.schema.json"
        schema = json.loads(schema_path.read_text())
        self.assertEqual("object", schema["type"])
        self.assertEqual(False, schema["additionalProperties"])
        self.assertEqual(1, schema["properties"]["schema_version"]["const"])

    def test_cdg_hp_03_capabilities_and_schema_support(self) -> None:
        """[CDG-HP-03] Verify schema permits contracts, contract_diff, db_hygiene, and patternProperties."""
        schema_path = SCRIPT_DIR.parent / "schemas/rust-quality.schema.json"
        schema = json.loads(schema_path.read_text())
        cap_props = schema["properties"]["capabilities"]["properties"]
        self.assertIn("contracts", cap_props)
        self.assertIn("contract_diff", cap_props)
        self.assertIn("db_hygiene", cap_props)
        pattern_props = schema["properties"]["capabilities"].get("patternProperties", {})
        self.assertIn("^contracts_[a-z0-9_]+$", pattern_props)

        cfg = valid_config()
        cfg["capabilities"]["contracts"] = ["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "check"]
        cfg["capabilities"]["contracts_lyrics_sync"] = ["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "check", "--domain", "lyrics-sync"]
        cfg["capabilities"]["contract_diff"] = ["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "diff-check", "--base-ref", "{base_ref}"]
        cfg["capabilities"]["db_hygiene"] = ["cargo", "run", "-p", "xtask", "--", "db-hygiene"]
        res = validate_rust_config(cfg, "epic")
        self.assertEqual("PASS", res["status"])


if __name__ == "__main__":
    unittest.main()
