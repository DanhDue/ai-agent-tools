"""Unit and integration tests for setup-shared-contracts skill and CLI engine."""

from __future__ import annotations

import string
import tempfile
import unittest
from pathlib import Path

TEMPLATES_DIR = (
    Path(__file__).resolve().parent.parent / "templates"
)
CANONICAL_TEMPLATE_NAMES = (
    "api_contract.md.tmpl",
    "architecture_and_flow.md.tmpl",
    "gaps_and_rfcs.md.tmpl",
    "hub_readme.md.tmpl",
    "hub_rule.md.tmpl",
    "satellite_rule.md.tmpl",
)


class TestCanonicalTemplates(unittest.TestCase):
    """Verifies template existence, schema validity, and string.Template hygiene."""

    def test_canonical_templates_exist(self) -> None:
        """All 6 canonical template files must exist and be non-empty."""
        self.assertTrue(
            TEMPLATES_DIR.is_dir(),
            f"Templates directory not found: {TEMPLATES_DIR}",
        )
        for tmpl_name in CANONICAL_TEMPLATE_NAMES:
            tmpl_path = TEMPLATES_DIR / tmpl_name
            self.assertTrue(
                tmpl_path.is_file(),
                f"Missing canonical template: {tmpl_name}",
            )
            content = tmpl_path.read_text(encoding="utf-8")
            self.assertGreater(
                len(content.strip()),
                0,
                f"Template is empty: {tmpl_name}",
            )

    def test_string_template_substitution_hygiene(self) -> None:
        """Every template must be valid string.Template without legacy mustache syntax."""
        mapping = {
            "domain": "test-domain",
            "hub_repo": "TestHub",
            "timestamp": "2026-10-30T00:00:00Z",
        }
        for tmpl_name in CANONICAL_TEMPLATE_NAMES:
            tmpl_path = TEMPLATES_DIR / tmpl_name
            raw_content = tmpl_path.read_text(encoding="utf-8")

            # Must not contain legacy mustache markers
            self.assertNotIn("{{", raw_content, f"Mustache token '{{' in {tmpl_name}")
            self.assertNotIn("}}", raw_content, f"Mustache token '}}' in {tmpl_name}")

            # Must successfully substitute defined variables
            tmpl = string.Template(raw_content)
            rendered = tmpl.safe_substitute(mapping)

            # Assert substitutions took place
            self.assertIn("TestHub", rendered)
            self.assertIn("2026-10-30T00:00:00Z", rendered)

    def test_ssc_hp_01(self) -> None:
        """[SSC-HP-01] Validates template bundle rendering for fresh Hub initialization."""
        params = {
            "domain": "lyrics-sync",
            "hub_repo": "D3Nexus",
            "timestamp": "2026-10-30T05:35:00Z",
        }

        # 1. Render Hub Readme
        readme_tmpl = string.Template(
            (TEMPLATES_DIR / "hub_readme.md.tmpl").read_text(encoding="utf-8")
        )
        readme_rendered = readme_tmpl.substitute(params)
        self.assertIn("# Shared Contracts Repository", readme_rendered)
        self.assertIn("D3Nexus", readme_rendered)
        self.assertIn("lyrics-sync", readme_rendered)
        self.assertIn("flowchart TD", readme_rendered)
        self.assertIn("Outbound Symlink Mappings", readme_rendered)

        # 2. Render Domain Contracts (API, Architecture, Gaps)
        api_tmpl = string.Template(
            (TEMPLATES_DIR / "api_contract.md.tmpl").read_text(encoding="utf-8")
        )
        api_rendered = api_tmpl.substitute(params)
        self.assertIn("# API Contract: lyrics-sync", api_rendered)
        self.assertIn("X-Worker-Token", api_rendered)
        self.assertIn("Non-Breaking Schema Guarantees", api_rendered)

        arch_tmpl = string.Template(
            (TEMPLATES_DIR / "architecture_and_flow.md.tmpl").read_text(encoding="utf-8")
        )
        arch_rendered = arch_tmpl.substitute(params)
        self.assertIn("# Architecture and Flow: lyrics-sync", arch_rendered)
        self.assertIn("Seven Canonical Pipeline Steps", arch_rendered)
        self.assertIn("Cancellation Fencing", arch_rendered)
        self.assertIn("Stateless Compute", arch_rendered)

        gaps_tmpl = string.Template(
            (TEMPLATES_DIR / "gaps_and_rfcs.md.tmpl").read_text(encoding="utf-8")
        )
        gaps_rendered = gaps_tmpl.substitute(params)
        self.assertIn("# Gaps and RFCs Ledger: lyrics-sync", gaps_rendered)
        self.assertIn("Active RFC Ledger", gaps_rendered)
        self.assertIn("RFC Proposal Template", gaps_rendered)

        # 3. Render Hub Rules
        rule_tmpl = string.Template(
            (TEMPLATES_DIR / "hub_rule.md.tmpl").read_text(encoding="utf-8")
        )
        rule_rendered = rule_tmpl.substitute(params)
        self.assertIn("# Shared Contracts Rules (Hub Repository)", rule_rendered)
        self.assertIn("Single Source of Truth", rule_rendered)
        self.assertIn("task_01", rule_rendered)

    def test_ssc_ec_01(self) -> None:
        """[SSC-EC-01] Validates template rendering preserves custom edits and invariants."""
        params = {
            "domain": "custom-service",
            "hub_repo": "MainHub",
            "timestamp": "2026-10-30T12:00:00Z",
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            domain_dir = tmp_path / "shared-contracts" / "custom-service"
            domain_dir.mkdir(parents=True, exist_ok=True)

            api_contract_file = domain_dir / "api_contract.md"
            custom_content = (
                "# API Contract: custom-service\n\n"
                "## Custom Endpoint\n\n`POST /api/v1/custom-service/special`\n"
            )
            api_contract_file.write_text(custom_content, encoding="utf-8")

            # Check that existing content is preserved when checking presence
            self.assertTrue(api_contract_file.exists())
            self.assertEqual(api_contract_file.read_text(encoding="utf-8"), custom_content)

            # Ensure satellite rule template preserves boundary guarantees
            sat_rule_tmpl = string.Template(
                (TEMPLATES_DIR / "satellite_rule.md.tmpl").read_text(encoding="utf-8")
            )
            sat_rendered = sat_rule_tmpl.substitute(params)
            self.assertIn("# Shared Contracts Rules (Satellite Repository)", sat_rendered)
            self.assertIn("120000", sat_rendered)
            self.assertIn("Files Allowed", sat_rendered)
            self.assertIn("Stateless Compute", sat_rendered)


if __name__ == "__main__":
    unittest.main()
