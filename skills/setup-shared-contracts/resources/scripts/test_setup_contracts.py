"""Unit and integration tests for setup-shared-contracts skill and CLI engine."""

from __future__ import annotations

import os
import string
import subprocess
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


class TestHubInitialization(unittest.TestCase):
    """[SSC-ST-01] and [SSC-FR-01] tests for setup_contracts.py init-hub."""

    def test_ssc_st_01(self) -> None:
        """[SSC-ST-01] Adding subsequent domains updates topology README and preserves existing."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 1. Initialize hub with first domain lyrics-sync
            proc1 = subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "lyrics-sync", "--repo-root", str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc1.returncode, 0, f"Init-hub 1 failed: {proc1.stderr}")

            # 2. Add second domain nexus
            proc2 = subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "nexus", "--repo-root", str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc2.returncode, 0, f"Init-hub 2 failed: {proc2.stderr}")

            # 3. Assert directory structures
            readme_file = tmp_path / "shared-contracts" / "README.md"
            self.assertTrue(readme_file.is_file())
            readme_text = readme_file.read_text(encoding="utf-8")
            self.assertIn("lyrics-sync", readme_text)
            self.assertIn("nexus", readme_text)

            nexus_dir = tmp_path / "shared-contracts" / "nexus"
            for canonical in ("api_contract.md", "architecture_and_flow.md", "gaps_and_rfcs.md"):
                self.assertTrue((nexus_dir / canonical).is_file(), f"Missing {canonical} in nexus domain")

    def test_ssc_fr_01(self) -> None:
        """[SSC-FR-01] Refusing Hub initialization on existing symlink."""
        import os

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            target_dummy = tmp_path / "dummy_target"
            target_dummy.mkdir()

            symlink_path = tmp_path / "shared-contracts"
            os.symlink(target_dummy, symlink_path)

            proc = subprocess.run(
                ["python3", str(cli_path), "init-hub", "--repo-root", str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("symlink", (proc.stdout + proc.stderr).lower())


class TestSatelliteLinking(unittest.TestCase):
    """[SSC-HP-02], [SSC-EC-02], [SSC-ST-02], [SSC-FR-02], [SSC-FR-03] tests for link-satellite."""

    def test_ssc_hp_02(self) -> None:
        """[SSC-HP-02] Fresh satellite repository relative symlinking."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "D3Nexus"
            sat_dir = tmp_path / "lyrics-sync"
            hub_dir.mkdir()
            sat_dir.mkdir()

            # Initialize hub first
            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "lyrics-sync", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            # Link satellite
            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "lyrics-sync",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"Link satellite failed: {proc.stderr}")

            # Check symlink
            symlink_path = sat_dir / "shared-contracts"
            self.assertTrue(symlink_path.is_symlink())
            link_target = os.readlink(symlink_path)
            self.assertFalse(os.path.isabs(link_target), f"Symlink target must be relative, got: {link_target}")

            # Check files resolve across symlink
            self.assertTrue((symlink_path / "api_contract.md").is_file())
            self.assertTrue((symlink_path / "architecture_and_flow.md").is_file())
            self.assertTrue((symlink_path / "gaps_and_rfcs.md").is_file())

            # Check satellite rule installed
            rule_path = sat_dir / ".agents" / "rules" / "contract_rules.md"
            self.assertTrue(rule_path.is_file())

    def test_ssc_ec_02(self) -> None:
        """[SSC-EC-02] Deep sibling hierarchy relative path calculation."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "control-plane" / "hub"
            sat_dir = tmp_path / "services" / "workers" / "audio" / "satellite"
            hub_dir.mkdir(parents=True)
            sat_dir.mkdir(parents=True)

            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "audio-core", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "audio-core",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"Deep link failed: {proc.stderr}")

            symlink_path = sat_dir / "shared-contracts"
            self.assertTrue(symlink_path.is_symlink())
            link_target = os.readlink(symlink_path)
            self.assertFalse(os.path.isabs(link_target))
            self.assertTrue((symlink_path / "api_contract.md").is_file())

    def test_ssc_st_02(self) -> None:
        """[SSC-ST-02] Switching linked domain on satellite with force."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "Hub"
            sat_dir = tmp_path / "Satellite"
            hub_dir.mkdir()
            sat_dir.mkdir()

            # Initialize hub with alpha and beta
            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "alpha", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "beta", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            # Link to alpha
            subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "alpha",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=True,
                capture_output=True,
            )
            symlink_path = sat_dir / "shared-contracts"
            self.assertIn("alpha", os.readlink(symlink_path))

            # Re-link to beta with force
            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "beta",
                    "--satellite-root",
                    str(sat_dir),
                    "--force",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"Force relink failed: {proc.stderr}")
            self.assertIn("beta", os.readlink(symlink_path))

    def test_ssc_fr_02(self) -> None:
        """[SSC-FR-02] Refusing satellite linking when target domain is missing."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "Hub"
            sat_dir = tmp_path / "Satellite"
            hub_dir.mkdir()
            sat_dir.mkdir()

            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "existing-domain", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "missing-domain",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("missing-domain", (proc.stdout + proc.stderr).lower())

    def test_ssc_fr_03(self) -> None:
        """[SSC-FR-03] Refusing overwrite of existing non-empty physical directory without force."""

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "Hub"
            sat_dir = tmp_path / "Satellite"
            hub_dir.mkdir()
            sat_dir.mkdir()

            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "target-domain", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            # Create non-empty physical shared-contracts in satellite
            physical_dir = sat_dir / "shared-contracts"
            physical_dir.mkdir()
            (physical_dir / "uncommitted_work.txt").write_text("precious data", encoding="utf-8")

            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "target-domain",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 1)
            self.assertTrue(physical_dir.is_dir())
            self.assertFalse(physical_dir.is_symlink())


if __name__ == "__main__":
    unittest.main()
