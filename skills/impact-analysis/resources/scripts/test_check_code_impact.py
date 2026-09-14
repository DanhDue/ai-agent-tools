#!/usr/bin/env python3
"""Tests for check_code_impact.py.

Run: python3 skills/impact-analysis/resources/scripts/test_check_code_impact.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_code_impact import (
    ImpactReport,
    check_bridge_contracts,
    check_downstream_callers,
    check_test_coverage,
    check_upstream_divergence,
    format_markdown_report,
    run_impact_analysis,
)


class TestUpstreamDivergence(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp_dir.name)
        # Initialize test git repo
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test Dev"], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, capture_output=True, check=True)

        # Initial commit on main
        self.file_path = self.repo / "PaymentRepository.kt"
        self.file_path.write_text("class PaymentRepository { fun pay() = true }\n")
        subprocess.run(["git", "add", "PaymentRepository.kt"], cwd=self.repo, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo, capture_output=True, check=True)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_no_divergence_when_up_to_date(self):
        # Branch off main
        subprocess.run(["git", "checkout", "-b", "feature/payment"], cwd=self.repo, capture_output=True, check=True)
        result = check_upstream_divergence(self.repo, ["PaymentRepository.kt"], base_ref="main")
        self.assertFalse(result.has_divergence)
        self.assertEqual(len(result.divergent_commits), 0)

    def test_detects_unmerged_upstream_commits(self):
        # Branch off main
        subprocess.run(["git", "checkout", "-b", "feature/payment"], cwd=self.repo, capture_output=True, check=True)
        
        # Switch back to main and make a commit touching PaymentRepository.kt
        subprocess.run(["git", "checkout", "main"], cwd=self.repo, capture_output=True, check=True)
        self.file_path.write_text("class PaymentRepository { fun pay() = true; fun refund() = false }\n")
        subprocess.run(["git", "commit", "-am", "Add refund function upstream"], cwd=self.repo, capture_output=True, check=True)

        # Switch back to feature branch
        subprocess.run(["git", "checkout", "feature/payment"], cwd=self.repo, capture_output=True, check=True)

        result = check_upstream_divergence(self.repo, ["PaymentRepository.kt"], base_ref="main")
        self.assertTrue(result.has_divergence)
        self.assertEqual(len(result.divergent_commits), 1)
        self.assertIn("Add refund function upstream", result.divergent_commits[0]["subject"])


class TestBlastRadius(unittest.TestCase):
    def test_finds_callers_and_imports(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_dir = root / "lib"
            lib_dir.mkdir(parents=True)
            
            repo_file = lib_dir / "payment_repo.dart"
            repo_file.write_text("class PaymentRepository {\n  void execute() {}\n}\n")
            
            vm_file = lib_dir / "payment_view_model.dart"
            vm_file.write_text("import 'payment_repo.dart';\n\nclass PaymentViewModel {\n  final PaymentRepository repo;\n}\n")

            callers = check_downstream_callers(root, symbols=["PaymentRepository"], search_files=[repo_file])
            self.assertIn(str(vm_file.relative_to(root)), callers)
            self.assertEqual(len(callers[str(vm_file.relative_to(root))]), 1)  # line 4

    def test_returns_empty_when_no_callers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lib_dir = root / "lib"
            lib_dir.mkdir(parents=True)
            unused_file = lib_dir / "unused.dart"
            unused_file.write_text("class UnusedSecret {}\n")
            callers = check_downstream_callers(root, symbols=["UnusedSecret"], search_files=[unused_file])
            self.assertEqual(len(callers), 0)


class TestBridgeMatcher(unittest.TestCase):
    def test_matches_flutter_to_android_and_ios(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Flutter file
            flutter_dir = root / "lib"
            flutter_dir.mkdir(parents=True)
            (flutter_dir / "biometrics.dart").write_text(
                "import 'package:flutter/services.dart';\n"
                "final channel = MethodChannel('com.example.app/biometrics');\n"
            )
            # Android file
            android_dir = root / "android/src/main/kotlin"
            android_dir.mkdir(parents=True)
            (android_dir / "BiometricsPlugin.kt").write_text(
                'val channel = MethodChannel(flutterEngine.dartExecutor, "com.example.app/biometrics")\n'
            )
            # iOS file
            ios_dir = root / "ios/Classes"
            ios_dir.mkdir(parents=True)
            (ios_dir / "BiometricsPlugin.swift").write_text(
                'let channel = FlutterMethodChannel(name: "com.example.app/biometrics", binaryMessenger: messenger)\n'
            )

            bridges = check_bridge_contracts(root, [flutter_dir / "biometrics.dart"])
            self.assertEqual(len(bridges), 1)
            channel_name = "com.example.app/biometrics"
            self.assertIn(channel_name, bridges)
            self.assertIn("android/src/main/kotlin/BiometricsPlugin.kt", bridges[channel_name]["android"])
            self.assertIn("ios/Classes/BiometricsPlugin.swift", bridges[channel_name]["ios"])


class TestTestImpactAnalysis(unittest.TestCase):
    def test_flags_unprotected_code_when_no_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_file = root / "features/payment/PaymentService.kt"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("class PaymentService { fun processRefund() {} }\n")

            coverage_res = check_test_coverage(root, [src_file])
            self.assertFalse(coverage_res[str(src_file.relative_to(root))]["has_test_file"])
            self.assertEqual(coverage_res[str(src_file.relative_to(root))]["coverage_percent"], 0.0)

    def test_finds_paired_test_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_file = root / "lib/payment/service.dart"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("class Service {}\n")

            test_file = root / "test/payment/service_test.dart"
            test_file.parent.mkdir(parents=True)
            test_file.write_text("void main() {}\n")

            coverage_res = check_test_coverage(root, [src_file])
            self.assertTrue(coverage_res[str(src_file.relative_to(root))]["has_test_file"])
            self.assertEqual(coverage_res[str(src_file.relative_to(root))]["test_file"], "test/payment/service_test.dart")

    def test_parses_lcov_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src_file = root / "lib/math.dart"
            src_file.parent.mkdir(parents=True)
            src_file.write_text("int add(int a, int b) => a + b;\n")

            cov_dir = root / "coverage"
            cov_dir.mkdir(parents=True)
            lcov = cov_dir / "lcov.info"
            lcov.write_text(
                f"SF:{src_file}\n"
                "DA:1,1\n"
                "LF:1\n"
                "LH:1\n"
                "end_of_record\n"
            )

            coverage_res = check_test_coverage(root, [src_file])
            self.assertEqual(coverage_res[str(src_file.relative_to(root))]["coverage_percent"], 100.0)


class TestCliFormatting(unittest.TestCase):
    def test_markdown_formatting_contains_key_sections(self):
        report = ImpactReport(
            files=["PaymentRepository.kt"],
            symbols=["PaymentRepository"],
            divergence=None,
            callers={"CheckoutFlow.kt": [12]},
            bridges={"com.example.app/biometrics": {"android": ["Plugin.kt"], "ios": ["Plugin.swift"]}},
            coverage={"PaymentRepository.kt": {"has_test_file": False, "test_file": None, "coverage_percent": 0.0, "untested_error_paths": []}},
        )
        md = format_markdown_report(report)
        self.assertIn("# Impact Analysis Diagnostic Report", md)
        self.assertIn("Downstream Callers", md)
        self.assertIn("Cross-Platform Bridge Contracts", md)
        self.assertIn("Coverage Safety Net", md)


if __name__ == "__main__":
    unittest.main()
