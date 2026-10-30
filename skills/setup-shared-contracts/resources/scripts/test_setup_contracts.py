"""Unit and integration tests for setup-shared-contracts skill and CLI engine."""

from __future__ import annotations

import concurrent.futures
import os
import string
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Enable direct import of setup_contracts module
sys.path.insert(0, str(Path(__file__).resolve().parent))
import setup_contracts

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
        """[SSC-HP-01] Validates production Hub initialization and contract generation."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "init-hub",
                    "--domain",
                    "lyrics-sync",
                    "--repo-root",
                    str(tmp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"init-hub failed: {proc.stderr}")

            # 1. Physical shared-contracts/ directory exists
            shared_contracts_dir = tmp_path / "shared-contracts"
            self.assertTrue(shared_contracts_dir.is_dir())
            self.assertFalse(shared_contracts_dir.is_symlink())

            # 2. README.md contains Star Topology layout and outbound mappings
            readme_file = shared_contracts_dir / "README.md"
            self.assertTrue(readme_file.is_file())
            readme_text = readme_file.read_text(encoding="utf-8")
            self.assertIn("# Shared Contracts Repository", readme_text)
            self.assertIn("lyrics-sync", readme_text)
            self.assertIn("flowchart TD", readme_text)
            self.assertIn("Outbound Symlink Mappings", readme_text)

            # 3. Domain folder contains all 3 canonical files
            domain_dir = shared_contracts_dir / "lyrics-sync"
            self.assertTrue(domain_dir.is_dir())
            for canonical in ("api_contract.md", "architecture_and_flow.md", "gaps_and_rfcs.md"):
                c_file = domain_dir / canonical
                self.assertTrue(c_file.is_file(), f"Missing canonical file: {canonical}")
                self.assertGreater(len(c_file.read_text(encoding="utf-8")), 50)

            # 4. Hub rule exists with SSOT ownership instructions
            hub_rule = tmp_path / ".agents" / "rules" / "contract_rules.md"
            self.assertTrue(hub_rule.is_file())
            hub_rule_text = hub_rule.read_text(encoding="utf-8")
            self.assertIn("Single Source of Truth", hub_rule_text)
            self.assertIn("task_01", hub_rule_text)

    def test_ssc_ec_01(self) -> None:
        """[SSC-EC-01] Validates idempotent execution preserves custom edits without --force."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # 1. Fresh initialization
            proc1 = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "init-hub",
                    "--domain",
                    "lyrics-sync",
                    "--repo-root",
                    str(tmp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc1.returncode, 0, f"Init failed: {proc1.stderr}")

            # 2. Apply custom edits to api_contract.md
            api_contract_file = tmp_path / "shared-contracts" / "lyrics-sync" / "api_contract.md"
            custom_content = (
                "# API Contract: lyrics-sync\n\n"
                "## Custom Endpoint\n\n`POST /api/v1/lyrics-sync/special`\n"
            )
            api_contract_file.write_text(custom_content, encoding="utf-8")

            # 3. Rerun init-hub without --force
            proc2 = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "init-hub",
                    "--domain",
                    "lyrics-sync",
                    "--repo-root",
                    str(tmp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc2.returncode, 0, f"Rerun init-hub failed: {proc2.stderr}")

            # Custom edits must be strictly preserved
            self.assertEqual(api_contract_file.read_text(encoding="utf-8"), custom_content)

            # 4. Verify --force overwrites existing custom edits
            proc3 = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "init-hub",
                    "--domain",
                    "lyrics-sync",
                    "--repo-root",
                    str(tmp_path),
                    "--force",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc3.returncode, 0, f"Force init-hub failed: {proc3.stderr}")
            self.assertNotEqual(api_contract_file.read_text(encoding="utf-8"), custom_content)


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


class TestVerificationEngine(unittest.TestCase):
    """[SSC-EC-03], [SSC-AR-01], [SSC-AR-02] tests for setup_contracts.py verify and robust IO."""

    def test_ssc_ec_03(self) -> None:
        """[SSC-EC-03] Domain name normalization and whitespace stripping."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            proc = subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "init-hub",
                    "--domain",
                    "  Lyrics-Sync  ",
                    "--repo-root",
                    str(tmp_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 0, f"Init failed: {proc.stderr}")

            # Normalized domain directory must be lowercase and stripped
            normalized_dir = tmp_path / "shared-contracts" / "lyrics-sync"
            self.assertTrue(normalized_dir.is_dir(), f"Normalized directory missing: {normalized_dir}")
            readme_text = (tmp_path / "shared-contracts" / "README.md").read_text(encoding="utf-8")
            self.assertIn("lyrics-sync", readme_text)

    def test_ssc_ar_01(self) -> None:
        """[SSC-AR-01] Atomic file creation prevents partial or torn writes under concurrency."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            target_file = tmp_path / "concurrent_atomic.txt"

            errors: list[str] = []

            def worker_writer(worker_id: int) -> int:
                payload = f"WORKER_{worker_id}_PAYLOAD:" + ("X" * 1024) + f":END_{worker_id}\n"
                writes = 0
                for _ in range(40):
                    setup_contracts.atomic_write_text(target_file, payload)
                    writes += 1
                return writes

            def worker_reader() -> int:
                reads = 0
                for _ in range(80):
                    if target_file.exists():
                        try:
                            text = target_file.read_text(encoding="utf-8")
                            if not text:
                                errors.append("Observed zero-byte file during concurrent read")
                            elif not (text.startswith("WORKER_") and text.endswith("\n")):
                                errors.append(f"Observed torn or partial content: {text[:50]}")
                            else:
                                reads += 1
                        except FileNotFoundError:
                            pass
                return reads

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                writers = [executor.submit(worker_writer, i) for i in range(4)]
                readers = [executor.submit(worker_reader) for _ in range(4)]
                # Explicitly collect future results so any worker exceptions are raised
                write_results = [f.result() for f in writers]
                read_results = [f.result() for f in readers]

            self.assertEqual(errors, [], f"Atomic write concurrency violations: {errors}")
            self.assertEqual(sum(write_results), 160, "All writes must complete successfully")
            self.assertGreater(sum(read_results), 0, "Concurrent reads must succeed")

            # Check final file content integrity
            final_text = target_file.read_text(encoding="utf-8")
            self.assertTrue(final_text.startswith("WORKER_") and final_text.endswith("\n"))

            # No temporary swap files (.tmp_*) should linger
            temp_swap_files = list(tmp_path.glob(".tmp_*"))
            self.assertEqual(temp_swap_files, [], f"Lingering swap files found: {temp_swap_files}")

    def test_ssc_ar_02(self) -> None:
        """[SSC-AR-02] Circular symlink and max depth (>10 hops) loop protection halts cleanly."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"

        # 1. Circular symlink detection (A -> B -> A)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            link_a = tmp_path / "shared-contracts"
            link_b = tmp_path / "loop_target"

            os.symlink("loop_target", link_a)
            os.symlink("shared-contracts", link_b)

            proc = subprocess.run(
                ["python3", str(cli_path), "verify", "--repo-root", str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("exceeds max depth (10 hops)", proc.stderr)
            self.assertNotIn("RecursionError", proc.stderr)

        # 2. Excessive hop chain (> 10 hops)
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_target = tmp_path / "hub_contracts"
            hub_target.mkdir()

            # Create 12 hops: hop_0 (shared-contracts) -> hop_1 -> ... -> hop_11 -> hub_target
            prev_target = "hub_contracts"
            for hop_idx in range(11, -1, -1):
                hop_name = f"hop_{hop_idx}" if hop_idx > 0 else "shared-contracts"
                os.symlink(prev_target, tmp_path / hop_name)
                prev_target = hop_name

            proc_chain = subprocess.run(
                ["python3", str(cli_path), "verify", "--repo-root", str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc_chain.returncode, 0)
            self.assertIn("exceeds max depth (10 hops)", proc_chain.stderr)

    def test_ssc_hp_03(self) -> None:
        """[SSC-HP-03] Comprehensive health verification pass across Hub and Satellite."""
        skill_md = Path(__file__).resolve().parent.parent.parent / "SKILL.md"
        self.assertTrue(skill_md.is_file(), f"Skill definition missing: {skill_md}")

        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "Hub"
            sat_dir = tmp_path / "Satellite"
            hub_dir.mkdir()
            sat_dir.mkdir()

            # 1. Initialize Hub with domain lyrics-sync
            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "lyrics-sync", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )

            # 2. Link Satellite to Hub
            subprocess.run(
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
                check=True,
                capture_output=True,
            )

            # 3. Verify Hub
            proc_hub = subprocess.run(
                ["python3", str(cli_path), "verify", "--repo-root", str(hub_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_hub.returncode, 0, f"Hub verify failed: {proc_hub.stderr}")
            self.assertIn("Hub mode", proc_hub.stdout)
            self.assertIn("PASS", proc_hub.stdout)

            # 4. Verify Satellite
            proc_sat = subprocess.run(
                ["python3", str(cli_path), "verify", "--repo-root", str(sat_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc_sat.returncode, 0, f"Satellite verify failed: {proc_sat.stderr}")
            self.assertIn("Satellite mode", proc_sat.stdout)
            self.assertIn("PASS", proc_sat.stdout)


class TestGovernanceAndDefectFixes(unittest.TestCase):
    """Tests covering security containment, governance rule constraints, and runtime compatibility."""

    def test_domain_containment_and_validation_guards(self) -> None:
        """Domain input must reject path traversal, slashes, and outside containment."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            invalid_domains = ["../escaped", "/absolute", "inv@lid", "sub/dir", "", "   "]
            for bad_domain in invalid_domains:
                proc = subprocess.run(
                    [
                        "python3",
                        str(cli_path),
                        "init-hub",
                        "--domain",
                        bad_domain,
                        "--repo-root",
                        str(tmp_path),
                    ],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(proc.returncode, 0, f"Domain '{bad_domain}' should be rejected")

    def test_satellite_rule_governance_content(self) -> None:
        """Satellite verification rejects empty rules or rules missing Git read-only restrictions."""
        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            hub_dir = tmp_path / "Hub"
            sat_dir = tmp_path / "Satellite"
            hub_dir.mkdir()
            sat_dir.mkdir()

            # Initialize Hub & link Satellite
            subprocess.run(
                ["python3", str(cli_path), "init-hub", "--domain", "test-dom", "--repo-root", str(hub_dir)],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    "python3",
                    str(cli_path),
                    "link-satellite",
                    "--hub",
                    str(hub_dir),
                    "--domain",
                    "test-dom",
                    "--satellite-root",
                    str(sat_dir),
                ],
                check=True,
                capture_output=True,
            )

            # Corrupt satellite rule to be empty
            sat_rule = sat_dir / ".agents" / "rules" / "contract_rules.md"
            sat_rule.write_text("# Empty Rule\n", encoding="utf-8")

            proc = subprocess.run(
                ["python3", str(cli_path), "verify", "--repo-root", str(sat_dir)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("missing required Git read-only boundary constraints", proc.stderr)

    def test_satellite_template_rfc_path(self) -> None:
        """Satellite rule template must reference shared-contracts/gaps_and_rfcs.md."""
        sat_tmpl = TEMPLATES_DIR / "satellite_rule.md.tmpl"
        content = sat_tmpl.read_text(encoding="utf-8")
        self.assertIn("shared-contracts/gaps_and_rfcs.md", content)
        self.assertNotIn("shared-contracts/$domain/gaps_and_rfcs.md", content)

    def test_python310_utc_timestamp(self) -> None:
        """_get_timestamp returns ISO-8601 UTC timestamp compatible with Python 3.10+."""
        ts = setup_contracts._get_timestamp()
        self.assertTrue(ts.endswith("Z"))
        self.assertIn("T", ts)


if __name__ == "__main__":
    unittest.main()
