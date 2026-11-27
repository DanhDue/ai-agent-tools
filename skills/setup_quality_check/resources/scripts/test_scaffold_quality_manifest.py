#!/usr/bin/env python3
"""Unit and integration tests for scaffold_quality_manifest.py.

Verifies platform detection, idempotent scaffolding, schema compliance,
non-overwriting standards_catalog.json, 4-profile unified capabilities,
and polyglot multi-provider manifest generation.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from scaffold_quality_manifest import (  # noqa: E402
    ScaffoldError,
    detect_platforms,
    scaffold_quality_manifests,
)

SKILLS_DIR = SCRIPT_DIR.parent.parent.parent
for _sub in (
    "quality_check",
    "flutter-quality-check",
    "android-quality-check",
    "ios-quality-check",
    "rust-quality-check",
    "python-quality-check",
    "web-quality-check",
):
    _path = str(SKILLS_DIR / _sub / "resources" / "scripts")
    if _path not in sys.path:
        sys.path.insert(0, _path)

from validate_android_quality import validate_android_config  # noqa: E402
from validate_flutter_quality import validate_flutter_config  # noqa: E402
from validate_ios_quality import validate_ios_config  # noqa: E402
from validate_python_quality import validate_python_config  # noqa: E402
from validate_quality_contract import validate_registry  # noqa: E402
from validate_rust_quality import validate_rust_config  # noqa: E402
from validate_web_quality import validate_manifest as validate_web_config  # noqa: E402

ALL_PROFILES = ("pr", "epic", "scheduled", "release")


class TestDetectPlatforms(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_detect_platforms_single_rust(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\nname = 'test'\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["rust"])

    def test_detect_platforms_single_flutter(self) -> None:
        (self.root / "pubspec.yaml").write_text("name: test_flutter\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["flutter"])

    def test_detect_platforms_single_android(self) -> None:
        (self.root / "build.gradle.kts").write_text("// gradle config\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["android"])

    def test_detect_platforms_single_ios(self) -> None:
        (self.root / "Project.swift").write_text("// tuist project\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["ios"])

    def test_detect_platforms_single_python_pyproject(self) -> None:
        (self.root / "pyproject.toml").write_text("[project]\nname = 'test_py'\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["python"])

    def test_detect_platforms_single_python_requirements(self) -> None:
        (self.root / "requirements.txt").write_text("pytest>=8.0.0\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, ["python"])

    def test_detect_platforms_polyglot(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\n")
        (self.root / "settings.gradle.kts").write_text("// settings\n")
        platforms = detect_platforms(self.root)
        self.assertEqual(sorted(platforms), ["android", "rust"])

    def test_detect_platforms_none(self) -> None:
        platforms = detect_platforms(self.root)
        self.assertEqual(platforms, [])


class TestScaffoldQualityManifests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.out_dir = self.root / ".agents" / "quality"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_scaffold_flutter_generates_valid_files(self) -> None:
        (self.root / "pubspec.yaml").write_text("name: flutter_app\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("flutter", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("flutter-core", provider_ids)
        for profile in ALL_PROFILES:
            self.assertEqual("PASS", validate_registry(reg_data, profile)["status"])

        manifest_path = self.out_dir / "flutter-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        for profile in ALL_PROFILES:
            res = validate_flutter_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_android_generates_valid_files(self) -> None:
        (self.root / "build.gradle.kts").write_text("// build gradle\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("android", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("android-core", provider_ids)
        for profile in ALL_PROFILES:
            self.assertEqual("PASS", validate_registry(reg_data, profile)["status"])

        manifest_path = self.out_dir / "android-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        self.assertNotIn("cleanup", manifest_data["capabilities"])
        self.assertNotIn("pkill", json.dumps(manifest_data))
        for profile in ALL_PROFILES:
            res = validate_android_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_ios_generates_valid_files(self) -> None:
        (self.root / "Project.swift").write_text("// tuist\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("ios", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("ios-core", provider_ids)
        for profile in ALL_PROFILES:
            self.assertEqual("PASS", validate_registry(reg_data, profile)["status"])

        manifest_path = self.out_dir / "ios-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        for profile in ALL_PROFILES:
            res = validate_ios_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_rust_generates_valid_files(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("rust", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("rust-core", provider_ids)
        for profile in ALL_PROFILES:
            self.assertEqual("PASS", validate_registry(reg_data, profile)["status"])

        manifest_path = self.out_dir / "rust-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        for profile in ALL_PROFILES:
            res = validate_rust_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_python_generates_valid_files(self) -> None:
        (self.root / "pyproject.toml").write_text("[project]\nname = 'py_app'\n")
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("python", result["detected_platforms"])

        reg_path = self.out_dir / "check_quality.json"
        self.assertTrue(reg_path.exists())
        reg_data = json.loads(reg_path.read_text())
        provider_ids = [p["id"] for p in reg_data["providers"]]
        self.assertIn("python-core", provider_ids)
        for profile in ALL_PROFILES:
            self.assertEqual("PASS", validate_registry(reg_data, profile)["status"])

        manifest_path = self.out_dir / "python-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        for flag in ("-q", "--tb=short", "--maxfail=3"):
            self.assertIn(flag, manifest_data["capabilities"]["test"])
        for profile in ALL_PROFILES:
            res = validate_python_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_web_generates_valid_files(self) -> None:
        (self.root / "package.json").write_text('{"name": "web-app"}\n')
        result = scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("web", result["detected_platforms"])

        manifest_path = self.out_dir / "web-quality.json"
        self.assertTrue(manifest_path.exists())
        manifest_data = json.loads(manifest_path.read_text())
        for profile in ALL_PROFILES:
            res = validate_web_config(manifest_data, profile)
            self.assertEqual("PASS", res["status"], res["findings"])

    def test_scaffold_polyglot_all_platforms(self) -> None:
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
        self.assertCountEqual(
            provider_ids,
            ["rust-core", "flutter-core", "android-core", "ios-core", "python-core"],
        )

        for p in ["rust", "flutter", "android", "ios", "python"]:
            self.assertTrue((self.out_dir / f"{p}-quality.json").exists())
        self.assertTrue((self.out_dir / "standards_catalog.json").exists())

    def test_idempotence_protects_existing_without_force(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\n")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        reg_path = self.out_dir / "check_quality.json"
        reg_path.write_text('{"custom": true}')

        with self.assertRaises(ScaffoldError) as ctx:
            scaffold_quality_manifests(self.root, self.out_dir, force=False)
        self.assertIn("already exists", str(ctx.exception))
        self.assertEqual(reg_path.read_text(), '{"custom": true}')

    def test_force_overwrites_existing_but_preserves_standards_catalog(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\n")
        self.out_dir.mkdir(parents=True, exist_ok=True)
        reg_path = self.out_dir / "check_quality.json"
        reg_path.write_text('{"custom": true}')
        catalog_path = self.out_dir / "standards_catalog.json"
        sentinel = '{"sentinel": "KEEP-ME"}\n'
        catalog_path.write_text(sentinel)

        scaffold_quality_manifests(self.root, self.out_dir, force=True)
        reg_data = json.loads(reg_path.read_text())
        self.assertEqual(reg_data["schema_version"], 1)
        self.assertEqual(catalog_path.read_text(), sentinel)

    def test_dry_run_does_not_create_files(self) -> None:
        (self.root / "Cargo.toml").write_text("[package]\n")
        result = scaffold_quality_manifests(self.root, self.out_dir, dry_run=True)
        self.assertIn("rust", result["detected_platforms"])
        self.assertFalse(self.out_dir.exists())

    def test_no_platform_detected_raises_error(self) -> None:
        with self.assertRaises(ScaffoldError) as ctx:
            scaffold_quality_manifests(self.root, self.out_dir)
        self.assertIn("No supported platform detected", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
