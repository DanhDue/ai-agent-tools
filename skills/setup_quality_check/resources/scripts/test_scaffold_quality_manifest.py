#!/usr/bin/env python3
"""
Unit and integration tests for scaffold_quality_manifest.py.
Verifies platform detection, idempotent scaffolding, schema compliance,
and polyglot multi-provider manifest generation.
"""

import json
import tempfile
import unittest
from pathlib import Path
import sys

# Import under test
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

try:
    from scaffold_quality_manifest import (
        detect_platforms,
        scaffold_quality_manifests,
        ScaffoldError,
        PLATFORM_CONFIGS,
    )
except ImportError:
    # Stub for RED test phase before scaffold_quality_manifest.py is created
    detect_platforms = None
    scaffold_quality_manifests = None
    ScaffoldError = Exception
    PLATFORM_CONFIGS = {}

# Schema validators for validation assertions
SKILLS_DIR = SCRIPT_DIR.parent.parent.parent
sys.path.insert(0, str(SKILLS_DIR / "quality_check" / "resources" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "flutter-quality-check" / "resources" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "android-quality-check" / "resources" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "ios-quality-check" / "resources" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "rust-quality-check" / "resources" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "python-quality-check" / "resources" / "scripts"))

try:
    from validate_quality_contract import validate_registry_dict
except ImportError:
    validate_registry_dict = None

try:
    from validate_flutter_quality import validate_flutter_manifest
except ImportError:
    validate_flutter_manifest = None

try:
    from validate_android_quality import validate_android_manifest
except ImportError:
    validate_android_manifest = None

try:
    from validate_ios_quality import validate_ios_manifest
except ImportError:
    validate_ios_manifest = None

try:
    from validate_rust_quality import validate_rust_manifest
except ImportError:
    validate_rust_manifest = None

try:
    from validate_python_quality import validate_python_config
except ImportError:
    validate_python_config = None


class TestDetectPlatforms(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_detect_platforms_single_rust(self):
        (self.root / "Cargo.toml").write_text("[package]\nname = 'test'\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["rust"])

    def test_detect_platforms_single_flutter(self):
        (self.root / "pubspec.yaml").write_text("name: test_flutter\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["flutter"])

    def test_detect_platforms_single_android(self):
        (self.root / "build.gradle.kts").write_text("// gradle config\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["android"])

    def test_detect_platforms_single_ios(self):
        (self.root / "Project.swift").write_text("// tuist project\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["ios"])

    def test_detect_platforms_single_python_pyproject(self):
        (self.root / "pyproject.toml").write_text("[project]\nname = 'test_py'\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["python"])

    def test_detect_platforms_single_python_requirements(self):
        (self.root / "requirements.txt").write_text("pytest>=8.0.0\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["python"])

    def test_detect_platforms_polyglot(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        (self.root / "settings.gradle.kts").write_text("// settings\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(sorted(platforms), ["android", "rust"])

    def test_detect_platforms_none(self):
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, [])


class TestScaffoldQualityManifests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out_dir = self.root / ".agents" / "quality"

    def tearDown(self):
        self.tmp.cleanup()

    def test_scaffold_flutter_generates_valid_files(self):
        (self.root / "pubspec.yaml").write_text("name: flutter_app\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("flutter", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("flutter-core", provider_ids)
        if validate_registry_dict:
            val_errs = validate_registry_dict(reg_data)
            self.assertEqual(val_errs, [])

        manifest_path = self.out_dir / "flutter-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        if validate_flutter_manifest:
            m_errs = validate_flutter_manifest(manifest_data)
            self.assertEqual(m_errs, [])

    def test_scaffold_android_generates_valid_files(self):
        (self.root / "build.gradle.kts").write_text("// build gradle\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("android", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("android-core", provider_ids)
        if validate_registry_dict:
            val_errs = validate_registry_dict(reg_data)
            self.assertEqual(val_errs, [])

        manifest_path = self.out_dir / "android-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        if validate_android_manifest:
            m_errs = validate_android_manifest(manifest_data)
            self.assertEqual(m_errs, [])

    def test_scaffold_ios_generates_valid_files(self):
        (self.root / "Project.swift").write_text("// tuist\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("ios", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("ios-core", provider_ids)
        if validate_registry_dict:
            val_errs = validate_registry_dict(reg_data)
            self.assertEqual(val_errs, [])

        manifest_path = self.out_dir / "ios-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        if validate_ios_manifest:
            m_errs = validate_ios_manifest(manifest_data)
            self.assertEqual(m_errs, [])

    def test_scaffold_rust_generates_valid_files(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("rust", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("rust-core", provider_ids)
        if validate_registry_dict:
            val_errs = validate_registry_dict(reg_data)
            self.assertEqual(val_errs, [])

        manifest_path = self.out_dir / "rust-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        if validate_rust_manifest:
            m_errs = validate_rust_manifest(manifest_data)
            self.assertEqual(m_errs, [])

    def test_scaffold_python_generates_valid_files(self):
        (self.root / "pyproject.toml").write_text("[project]\nname = 'py_app'\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("python", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("python-core", provider_ids)
        if validate_registry_dict:
            val_errs = validate_registry_dict(reg_data)
            self.assertEqual(val_errs, [])

        manifest_path = self.out_dir / "python-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        if validate_python_config:
            res = validate_python_config(manifest_data, "epic")
            self.assertEqual("PASS", res["status"])
            self.assertEqual([], res["findings"])

    def test_scaffold_polyglot_all_platforms(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        (self.root / "pubspec.yaml").write_text("name: f\n")
        (self.root / "settings.gradle.kts").write_text("// gradle\n")
        (self.root / "Package.swift").write_text("// spm\n")
        (self.root / "pyproject.toml").write_text("[project]\n")

        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertEqual(len(result["detected_platforms"]), 5)

        reg_path = self.out_dir / "check_quality.json"
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertCountEqual(provider_ids, ["rust-core", "flutter-core", "android-core", "ios-core", "python-core"])

        for p in ["rust", "flutter", "android", "ios", "python"]:
            self.assertTrue((self.out_dir / f"{p}-quality.json").exists())

    def test_idempotence_protects_existing_without_force(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        reg_path = self.out_dir / "check_quality.json"
        reg_path.write_text('{"custom": true}')

        with self.assertRaises(ScaffoldError) as ctx:
            scaffold_quality_manifests(self.root, self.out_dir, force=False)
        self.assertIn("already exists", str(ctx.exception))
        # Ensure file was not overwritten
        self.assertEqual(reg_path.read_text(), '{"custom": true}')

    def test_force_overwrites_existing(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        reg_path = self.out_dir / "check_quality.json"
        reg_path.write_text('{"custom": true}')

        result = scaffold_quality_manifests(self.root, self.out_dir, force=True)
        reg_data = json.loads(reg_path.read_text())
        self.assertEqual(reg_data["schema_version"], 1)

    def test_dry_run_does_not_create_files(self):
        (self.root / "Cargo.toml").write_text("[package]\n")
        result = scaffold_quality_manifests(self.root, self.out_dir, dry_run=True)
        self.assertIn("rust", result["detected_platforms"])
        self.assertFalse(self.out_dir.exists())

    def test_no_platform_detected_raises_error(self):
        with self.assertRaises(ScaffoldError) as ctx:
            scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("No supported platform detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
