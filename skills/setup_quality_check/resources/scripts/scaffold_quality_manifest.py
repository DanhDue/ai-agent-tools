#!/usr/bin/env python3
"""Automated Scaffolding Engine for Quality Providers.

Inspects project repository roots, detects project platforms (Flutter, Android,
iOS, Rust, Python, Web), and generates standardized .agents/quality/
configurations adhering to the additive v1 unified quality contract.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any


class ScaffoldError(Exception):
    """Raised when scaffolding fails due to safety or detection violations."""


ALL_PROFILES: list[str] = ["pr", "epic", "scheduled", "release"]
STANDARDS_CATALOG_REL_PATH = ".agents/quality/standards_catalog.json"

DEFAULT_STANDARDS_CATALOG: dict[str, Any] = {
    "schema_version": 1,
    "standards": [
        {
            "id": "ISO-25010-2023",
            "name": "ISO/IEC 25010:2023 Software Product Quality",
            "categories": [
                "functional_suitability",
                "reliability",
                "maintainability",
                "security",
                "performance_efficiency",
            ],
        },
        {
            "id": "ISO-27001-27002-2022",
            "name": "ISO/IEC 27001/27002:2022 Information Security Controls",
            "categories": [
                "access_control",
                "cryptography",
                "secure_development",
                "logging_monitoring",
            ],
        },
        {
            "id": "OWASP-TOP-10",
            "name": "OWASP Top 10 & Mobile Top 10",
            "categories": [
                "A01-Broken-Access-Control",
                "A02-Cryptographic-Failures",
                "A03-Injection",
                "M1-Improper-Credential-Usage",
            ],
        },
        {
            "id": "CWE-TOP-25",
            "name": "MITRE CWE Top 25 Most Dangerous Software Weaknesses",
            "categories": [
                "CWE-22-Path-Traversal",
                "CWE-78-OS-Command-Injection",
                "CWE-89-SQL-Injection",
                "CWE-798-Hardcoded-Credentials",
            ],
        },
    ],
    "rules": [],
}

_STACK_POOL_MOUNTS: dict[str, list[dict[str, str]]] = {
    "flutter": [
        {"path": ".dart_tool", "mode": "cow_copy"},
        {"path": "packages/*/.dart_tool", "mode": "cow_copy"},
        {"path": "features/*/.dart_tool", "mode": "cow_copy"},
        {"path": "secureFiles", "mode": "cow_copy"},
    ],
    "android": [
        {"path": ".gradle", "mode": "symlink"},
        {"path": "local.properties", "mode": "cow_copy"},
        {"path": "android/local.properties", "mode": "cow_copy"},
    ],
    "ios": [
        {"path": "Pods", "mode": "symlink"},
        {"path": ".build", "mode": "symlink"},
    ],
    "rust": [
        {"path": "target", "mode": "symlink"},
    ],
    "web": [
        {"path": "node_modules", "mode": "symlink"},
    ],
    "python": [
        {"path": ".venv", "mode": "symlink"},
    ],
}

PLATFORM_CONFIGS: dict[str, dict[str, Any]] = {
    "flutter": {
        "provider_id": "flutter-core",
        "skill": "d3nexus:flutter-quality-check",
        "filename": "flutter-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": ["./scripts/dartfmt.sh"],
                "analyze": ["fvm", "flutter", "analyze"],
                "boundaries": ["./scripts/check_module_boundaries.sh"],
                "license": ["./scripts/check_license_header.sh"],
                "test": ["melos", "run", "test"],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "coverage_report/lcov.info",
                        "--format",
                        "lcov",
                        "--min-coverage",
                        "0.85",
                        "--min-package-coverage",
                        "0.75",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".dart",
                    ],
                    "lcov_path": "coverage_report/lcov.info",
                    "threshold": 0.85,
                    "min_package_coverage": 0.75,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.80,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "coverage_report/lcov.info",
                    "--format",
                    "lcov",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".dart",
                ],
                "acceptance": ["./scripts/acceptance_check.sh"],
                "anti_stub": ["./scripts/check_anti_stub.sh"],
                "security": ["./scripts/check_security.sh"],
                "security_deps": ["./scripts/check_security_deps.sh"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
            },
            "profiles": {
                "pr": [
                    "format",
                    "analyze",
                    "test",
                    "diff_coverage",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "format",
                    "analyze",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "scheduled": [
                    "format",
                    "analyze",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "release": [
                    "format",
                    "analyze",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
            },
        },
    },
    "android": {
        "provider_id": "android-core",
        "skill": "d3nexus:android-quality-check",
        "filename": "android-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": ["./gradlew", "spotlessCheck"],
                "lint": ["./gradlew", "detekt"],
                "bcv": ["./gradlew", "apiCheck"],
                "architecture": ["./gradlew", ":konsist-test:test"],
                "test": ["./gradlew", "testDebugUnitTest"],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
                        "--format",
                        "jacoco",
                        "--min-coverage",
                        "0.85",
                        "--min-package-coverage",
                        "0.75",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".kt",
                    ],
                    "report_path": "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
                    "threshold": 0.85,
                    "min_package_coverage": 0.75,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.80,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
                    "--format",
                    "jacoco",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".kt",
                ],
                "acceptance": ["./scripts/acceptance_check.sh"],
                "anti_stub": ["./scripts/check_anti_stub.sh"],
                "security": ["./scripts/check_security.sh"],
                "security_deps": ["./gradlew", "dependencyCheckAnalyze"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
                "license": ["./scripts/check_license_header.sh"],
            },
            "profiles": {
                "pr": [
                    "format",
                    "lint",
                    "test",
                    "diff_coverage",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "format",
                    "lint",
                    "bcv",
                    "architecture",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "scheduled": [
                    "format",
                    "lint",
                    "bcv",
                    "architecture",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "release": [
                    "format",
                    "lint",
                    "bcv",
                    "architecture",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
            },
        },
    },
    "ios": {
        "provider_id": "ios-core",
        "skill": "d3nexus:ios-quality-check",
        "filename": "ios-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": [
                    "swiftformat",
                    "--config",
                    "quality/.swiftformat",
                    "--lint",
                    ".",
                ],
                "lint": [
                    "swiftlint",
                    "lint",
                    "--config",
                    "quality/.swiftlint.yml",
                    "--strict",
                ],
                "architecture": ["swift", "test", "--package-path", "ArchTests"],
                "boundaries": ["./scripts/check_module_boundaries.sh"],
                "test": ["swift", "test"],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "build/coverage/lcov.info",
                        "--format",
                        "lcov",
                        "--min-coverage",
                        "0.85",
                        "--min-package-coverage",
                        "0.75",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".swift",
                    ],
                    "lcov_path": "build/coverage/lcov.info",
                    "profdata_path": "default.profdata",
                    "threshold": 0.85,
                    "min_package_coverage": 0.75,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.80,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "build/coverage/lcov.info",
                    "--format",
                    "lcov",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".swift",
                ],
                "acceptance": ["./scripts/acceptance_check.sh"],
                "anti_stub": ["./scripts/check_anti_stub.sh"],
                "security": ["./scripts/check_security.sh"],
                "security_deps": ["./scripts/check_security_deps.sh"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
                "license": ["./scripts/check_license_header.sh"],
            },
            "profiles": {
                "pr": [
                    "format",
                    "lint",
                    "test",
                    "diff_coverage",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "format",
                    "lint",
                    "architecture",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "scheduled": [
                    "format",
                    "lint",
                    "architecture",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "release": [
                    "format",
                    "lint",
                    "architecture",
                    "boundaries",
                    "license",
                    "test",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
            },
        },
    },
    "rust": {
        "provider_id": "rust-core",
        "skill": "d3nexus:rust-quality-check",
        "filename": "rust-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": ["cargo", "fmt", "--all", "--", "--check"],
                "check": ["cargo", "check", "--all-targets"],
                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                "test": ["cargo", "test", "--workspace"],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "target/llvm-cov/lcov.info",
                        "--format",
                        "lcov",
                        "--min-coverage",
                        "0.80",
                        "--min-package-coverage",
                        "0.70",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".rs",
                    ],
                    "lcov_path": "target/llvm-cov/lcov.info",
                    "threshold": 0.8,
                    "min_package_coverage": 0.7,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.8,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "target/llvm-cov/lcov.info",
                    "--format",
                    "lcov",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".rs",
                ],
                "architecture": [
                    "cargo",
                    "run",
                    "-p",
                    "xtask",
                    "--",
                    "check-architecture",
                ],
                "anti_stub": ["./scripts/check_anti_stub.sh"],
                "security": ["./scripts/check_security.sh"],
                "security_deps": ["cargo", "audit"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
                "license": ["./scripts/check_license_header.sh"],
            },
            "profiles": {
                "pr": [
                    "format",
                    "check",
                    "clippy",
                    "test",
                    "diff_coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "format",
                    "check",
                    "clippy",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "scheduled": [
                    "format",
                    "check",
                    "clippy",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "release": [
                    "format",
                    "check",
                    "clippy",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
            },
        },
    },
    "python": {
        "provider_id": "python-core",
        "skill": "d3nexus:python-quality-check",
        "filename": "python-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": ["uv", "run", "ruff", "format", "--check", "."],
                "lint": ["uv", "run", "ruff", "check", "."],
                "type_check": ["uv", "run", "mypy", "--strict", "src", "tests"],
                "test": [
                    "uv",
                    "run",
                    "pytest",
                    "-q",
                    "--tb=short",
                    "--maxfail=3",
                    "-m",
                    "not slow and not acceptance and not live_llm",
                ],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "coverage.xml",
                        "--format",
                        "cobertura",
                        "--min-coverage",
                        "0.80",
                        "--min-package-coverage",
                        "0.70",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".py",
                    ],
                    "report_path": "coverage.xml",
                    "threshold": 0.8,
                    "min_package_coverage": 0.7,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.8,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "coverage.xml",
                    "--format",
                    "cobertura",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".py",
                ],
                "architecture": ["uv", "run", "lint-imports"],
                "anti_stub": ["python3", "scripts/check_anti_stub.py"],
                "security": ["uv", "run", "bandit", "-r", "src"],
                "security_deps": ["uv", "run", "pip-audit"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
                "license": ["./scripts/check_license_header.sh"],
            },
            "profiles": {
                "pr": [
                    "format",
                    "lint",
                    "type_check",
                    "test",
                    "diff_coverage",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "format",
                    "lint",
                    "type_check",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "scheduled": [
                    "format",
                    "lint",
                    "type_check",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
                "release": [
                    "format",
                    "lint",
                    "type_check",
                    "license",
                    "test",
                    "coverage",
                    "architecture",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                ],
            },
        },
    },
    "web": {
        "provider_id": "web-quality",
        "skill": "d3nexus:web-quality-check",
        "filename": "web-quality.json",
        "manifest": {
            "schema_version": 1,
            "standards_catalog": STANDARDS_CATALOG_REL_PATH,
            "capabilities": {
                "format": ["npx", "--no-install", "prettier", "--check", "."],
                "type_check": ["npm", "run", "check"],
                "lint": ["npm", "run", "lint"],
                "test_unit": ["npm", "run", "test:unit"],
                "test_e2e": ["npx", "--no-install", "playwright", "test"],
                "ui_review": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/audit_ui_state_and_styles.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "coverage": {
                    "command": [
                        "python3",
                        "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                        "coverage/lcov.info",
                        "--format",
                        "lcov",
                        "--min-coverage",
                        "0.80",
                        "--min-package-coverage",
                        "0.70",
                        "--diff-base",
                        "{base_ref}",
                        "--min-diff-coverage",
                        "0.80",
                        "--source-ext",
                        ".ts",
                        "--source-ext",
                        ".tsx",
                        "--source-ext",
                        ".js",
                    ],
                    "lcov_path": "coverage/lcov.info",
                    "threshold": 0.8,
                    "min_package_coverage": 0.7,
                    "exclude_package_floor": [],
                    "min_diff_coverage": 0.8,
                    "diff_base": "main",
                },
                "diff_coverage": [
                    "python3",
                    "{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py",
                    "coverage/lcov.info",
                    "--format",
                    "lcov",
                    "--min-coverage",
                    "0",
                    "--diff-base",
                    "{base_ref}",
                    "--min-diff-coverage",
                    "0.80",
                    "--source-ext",
                    ".ts",
                    "--source-ext",
                    ".tsx",
                    "--source-ext",
                    ".js",
                ],
                "anti_stub": ["./scripts/check_anti_stub.sh"],
                "security": ["./scripts/check_security.sh"],
                "security_deps": ["npm", "audit", "--audit-level=high"],
                "pr_diff_audit": [
                    "./scripts/check_quality_audit.sh",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_audit": ["./scripts/check_quality_audit.sh", "--all-files"],
                "pr_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--base-ref",
                    "{base_ref}",
                ],
                "workspace_impact": [
                    "python3",
                    "{skills_dir}/impact-analysis/resources/scripts/check_code_impact.py",
                    "--all-files",
                ],
                "license": ["./scripts/check_license_header.sh"],
                "contracts": [
                    "python3",
                    "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py",
                    "diff-check",
                    "--base-ref",
                    "{base_ref}",
                ],
            },
            "profiles": {
                "pr": [
                    "type_check",
                    "lint",
                    "test_unit",
                    "diff_coverage",
                    "anti_stub",
                    "security",
                    "pr_diff_audit",
                    "pr_impact",
                ],
                "epic": [
                    "type_check",
                    "lint",
                    "license",
                    "test_unit",
                    "test_e2e",
                    "ui_review",
                    "coverage",
                    "anti_stub",
                    "security",
                    "workspace_audit",
                    "workspace_impact",
                    "contracts",
                ],
                "scheduled": [
                    "type_check",
                    "lint",
                    "license",
                    "test_unit",
                    "ui_review",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                    "contracts",
                ],
                "release": [
                    "type_check",
                    "lint",
                    "license",
                    "test_unit",
                    "test_e2e",
                    "ui_review",
                    "coverage",
                    "anti_stub",
                    "security",
                    "security_deps",
                    "workspace_audit",
                    "workspace_impact",
                    "contracts",
                ],
            },
        },
    },
}


def detect_platforms(repo_root: Path) -> list[str]:
    """Inspect repository root directory and return detected platform names."""
    detected: list[str] = []

    if (repo_root / "pubspec.yaml").is_file() or (repo_root / "melos.yaml").is_file():
        detected.append("flutter")

    android_markers = [
        "build.gradle.kts",
        "build.gradle",
        "settings.gradle.kts",
        "settings.gradle",
    ]
    if any((repo_root / marker).is_file() for marker in android_markers):
        detected.append("android")

    ios_markers = [
        "Project.swift",
        "Tuist.swift",
        "Package.swift",
    ]
    if any((repo_root / marker).is_file() for marker in ios_markers):
        detected.append("ios")

    if (repo_root / "Cargo.toml").is_file():
        detected.append("rust")

    python_markers = [
        "pyproject.toml",
        "uv.lock",
        "requirements.txt",
        "setup.py",
        "Pipfile",
    ]
    if any((repo_root / marker).is_file() for marker in python_markers):
        detected.append("python")

    web_markers = [
        "package.json",
        "astro.config.mjs",
        "astro.config.ts",
        "astro.config.js",
        "playwright.config.ts",
        "playwright.config.js",
    ]
    if any((repo_root / marker).is_file() for marker in web_markers):
        detected.append("web")

    return sorted(set(detected))


def build_pool_mounts(
    platforms: list[str],
    repo_root: Path | None = None,
) -> list[dict[str, str]]:
    """Build deterministic stack-appropriate pool_mounts entries for check_quality.json."""
    mounts: list[dict[str, str]] = []
    seen_paths: set[str] = set()

    for platform in platforms:
        for entry in _STACK_POOL_MOUNTS.get(platform, []):
            path = entry["path"]
            if path not in seen_paths:
                seen_paths.add(path)
                mounts.append(dict(entry))

    if (
        repo_root is not None
        and (repo_root / "secureFiles").exists()
        and "secureFiles" not in seen_paths
    ):
        seen_paths.add("secureFiles")
        mounts.append({"path": "secureFiles", "mode": "cow_copy"})

    return mounts


def build_registry_data(
    platforms: list[str],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Build standard check_quality.json structure for given platforms."""
    providers: list[dict[str, Any]] = []
    for p in platforms:
        cfg = PLATFORM_CONFIGS[p]
        providers.append(
            {
                "id": cfg["provider_id"],
                "skill": cfg["skill"],
                "required": True,
                "profiles": list(ALL_PROFILES),
            }
        )

    registry: dict[str, Any] = {
        "schema_version": 1,
        "providers": providers,
    }
    pool_mounts = build_pool_mounts(platforms, repo_root=repo_root)
    if pool_mounts:
        registry["pool_mounts"] = pool_mounts
    return registry


def scaffold_quality_manifests(
    repo_root: Path,
    output_dir: Path | None = None,
    platforms: list[str] | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Scaffold quality check registry, provider manifests, and starter standards catalog.

    Raises ScaffoldError on detection failures or overwrite conflicts for
    registry/provider manifests. Existing standards_catalog.json is never
    overwritten (even with force=True).
    """
    repo_root = repo_root.resolve()
    target_dir = (
        (repo_root / ".agents" / "quality")
        if output_dir is None
        else output_dir.resolve()
    )

    if platforms is None:
        detected = detect_platforms(repo_root)
    else:
        detected = sorted(set(platforms))
        for p in detected:
            if p not in PLATFORM_CONFIGS:
                raise ScaffoldError(
                    f"Unsupported platform specified: '{p}'. Allowed: {list(PLATFORM_CONFIGS.keys())}"
                )

    if not detected:
        raise ScaffoldError(
            f"No supported platform detected in repository root: {repo_root}. "
            f"Supported platforms: {list(PLATFORM_CONFIGS.keys())}"
        )

    target_files: dict[Path, dict[str, Any]] = {}
    reg_path = target_dir / "check_quality.json"
    target_files[reg_path] = build_registry_data(detected, repo_root=repo_root)

    for p in detected:
        cfg = PLATFORM_CONFIGS[p]
        p_path = target_dir / cfg["filename"]
        target_files[p_path] = copy.deepcopy(cfg["manifest"])

    # Check for existing registry/provider manifests if not force
    if not force:
        for fpath in target_files:
            if fpath.exists():
                raise ScaffoldError(
                    f"Configuration file already exists: {fpath}. Use --force to overwrite."
                )

    # Starter standards_catalog.json is created ONLY when absent (never overwritten)
    catalog_path = target_dir / "standards_catalog.json"
    if not catalog_path.exists():
        target_files[catalog_path] = copy.deepcopy(DEFAULT_STANDARDS_CATALOG)

    if dry_run:
        return {
            "detected_platforms": detected,
            "output_directory": str(target_dir),
            "planned_files": [str(p) for p in target_files],
            "files": {str(p): data for p, data in target_files.items()},
        }

    target_dir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for fpath, data in target_files.items():
        fpath.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        written.append(str(fpath))

    return {
        "detected_platforms": detected,
        "output_directory": str(target_dir),
        "written_files": written,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold standardized quality check configurations for repository platforms."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root directory to inspect (default: current directory).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Target directory for quality configs (default: <root>/.agents/quality).",
    )
    parser.add_argument(
        "--platform",
        type=str,
        default=None,
        help="Comma-separated platform override (e.g. flutter,android,ios,rust,python,web).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing registry/provider configuration files (never overwrites standards_catalog.json).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned scaffolding without writing files to disk.",
    )

    args = parser.parse_args()

    platforms: list[str] | None = None
    if args.platform:
        platforms = [p.strip().lower() for p in args.platform.split(",") if p.strip()]

    try:
        result = scaffold_quality_manifests(
            repo_root=args.root,
            output_dir=args.output_dir,
            platforms=platforms,
            force=args.force,
            dry_run=args.dry_run,
        )
        print(
            f"Scaffolding completed successfully for platforms: {result['detected_platforms']}"
        )
        if args.dry_run:
            print(f"Dry-run planned {len(result['planned_files'])} file(s):")
            for f in result["planned_files"]:
                print(f"  - {f}")
        else:
            print(
                f"Written {len(result['written_files'])} file(s) into {result['output_directory']}:"
            )
            for f in result["written_files"]:
                print(f"  - {f}")
        return 0
    except ScaffoldError as err:
        print(f"Scaffolding error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
