#!/usr/bin/env python3
"""
Automated Scaffolding Engine for Quality Providers.
Inspects project repository roots, detects project platforms (Flutter, Android, iOS, Rust),
and generates standardized .agents/quality/ configurations adhering to canonical templates.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


class ScaffoldError(Exception):
    """Raised when scaffolding fails due to safety or detection violations."""
    pass


PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    "flutter": {
        "provider_id": "flutter-core",
        "skill": "d3nexus:flutter-quality-check",
        "filename": "flutter-quality.json",
        "manifest": {
            "schema_version": 1,
            "capabilities": {
                "format": ["./scripts/dartfmt.sh"],
                "analyze": ["fvm", "flutter", "analyze"],
                "boundaries": ["./scripts/check_module_boundaries.sh"],
                "license": ["./scripts/check_license_header.sh"],
                "test": ["melos", "run", "test"],
                "coverage": {
                    "command": ["./scripts/testWithCoverage.sh"],
                    "lcov_path": "coverage_report/lcov.info",
                    "threshold": 0.85
                },
                "acceptance": ["./scripts/acceptance_check.sh"]
            },
            "profiles": {
                "pr": ["format", "analyze", "test"],
                "epic": ["format", "analyze", "boundaries", "license", "test", "coverage"]
            }
        }
    },
    "android": {
        "provider_id": "android-core",
        "skill": "d3nexus:android-quality-check",
        "filename": "android-quality.json",
        "manifest": {
            "schema_version": 1,
            "capabilities": {
                "format": ["./gradlew", "spotlessCheck"],
                "lint": ["./gradlew", "detekt"],
                "bcv": ["./gradlew", "apiCheck"],
                "architecture": ["./gradlew", ":konsist-test:test"],
                "test": ["./gradlew", "testDebugUnitTest"],
                "coverage": {
                    "command": ["./gradlew", "jacocoTestReport"],
                    "report_path": "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
                    "threshold": 0.85
                },
                "acceptance": ["./scripts/acceptance_check.sh"],
                "cleanup": ["pkill", "-9", "java"]
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "bcv", "architecture", "test", "coverage", "cleanup"]
            }
        }
    },
    "ios": {
        "provider_id": "ios-core",
        "skill": "d3nexus:ios-quality-check",
        "filename": "ios-quality.json",
        "manifest": {
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
                    "threshold": 0.85
                },
                "acceptance": ["./scripts/acceptance_check.sh"]
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "architecture", "boundaries", "test", "coverage"]
            }
        }
    },
    "rust": {
        "provider_id": "rust-core",
        "skill": "d3nexus:rust-quality-check",
        "filename": "rust-quality.json",
        "manifest": {
            "schema_version": 1,
            "capabilities": {
                "format": ["cargo", "fmt", "--all", "--", "--check"],
                "check": ["cargo", "check", "--all-targets"],
                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                "test": ["cargo", "test", "--workspace"],
                "coverage": {
                    "command": ["cargo", "llvm-cov", "--workspace", "--fail-under-lines", "80"],
                    "threshold": 0.8
                },
                "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"]
            },
            "profiles": {
                "pr": ["format", "check", "clippy", "test", "architecture"],
                "epic": ["format", "check", "clippy", "test", "coverage", "architecture"]
            }
        }
    }
}


def detect_platforms(repo_root: Path) -> List[str]:
    """
    Inspects repository root directory and returns detected platform names.
    Supports Flutter, Android, iOS, and Rust heuristics.
    """
    detected = []

    # Flutter detection
    if (repo_root / "pubspec.yaml").is_file() or (repo_root / "melos.yaml").is_file():
        detected.append("flutter")

    # Android detection
    android_markers = [
        "build.gradle.kts",
        "build.gradle",
        "settings.gradle.kts",
        "settings.gradle",
    ]
    if any((repo_root / marker).is_file() for marker in android_markers):
        detected.append("android")

    # iOS detection
    ios_markers = [
        "Project.swift",
        "Tuist.swift",
        "Package.swift",
    ]
    if any((repo_root / marker).is_file() for marker in ios_markers):
        detected.append("ios")

    # Rust detection
    if (repo_root / "Cargo.toml").is_file():
        detected.append("rust")

    return sorted(list(set(detected)))


def build_registry_data(platforms: List[str]) -> Dict[str, Any]:
    """Builds standard check_quality.json structure for given platforms."""
    providers = []
    for p in platforms:
        cfg = PLATFORM_CONFIGS[p]
        providers.append({
            "id": cfg["provider_id"],
            "skill": cfg["skill"],
            "required": True,
            "profiles": ["pr", "epic"]
        })

    return {
        "schema_version": 1,
        "providers": providers
    }


def scaffold_quality_manifests(
    repo_root: Path,
    output_dir: Optional[Path] = None,
    platforms: Optional[List[str]] = None,
    force: bool = False,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Scaffolds quality check registry and provider manifests into output_dir.
    Raises ScaffoldError on detection failures or overwrite conflicts.
    """
    repo_root = repo_root.resolve()
    if output_dir is None:
        target_dir = repo_root / ".agents" / "quality"
    else:
        target_dir = output_dir.resolve()

    if platforms is None:
        detected = detect_platforms(repo_root)
    else:
        detected = sorted(list(set(platforms)))
        for p in detected:
            if p not in PLATFORM_CONFIGS:
                raise ScaffoldError(f"Unsupported platform specified: '{p}'. Allowed: {list(PLATFORM_CONFIGS.keys())}")

    if not detected:
        raise ScaffoldError(
            f"No supported platform detected in repository root: {repo_root}. "
            f"Supported platforms: {list(PLATFORM_CONFIGS.keys())}"
        )

    # Prepare file mappings
    target_files: Dict[Path, Dict[str, Any]] = {}
    reg_path = target_dir / "check_quality.json"
    target_files[reg_path] = build_registry_data(detected)

    for p in detected:
        cfg = PLATFORM_CONFIGS[p]
        p_path = target_dir / cfg["filename"]
        target_files[p_path] = cfg["manifest"]

    # Check for existing files if not force
    if not force:
        for fpath in target_files:
            if fpath.exists():
                raise ScaffoldError(
                    f"Configuration file already exists: {fpath}. Use --force to overwrite."
                )

    if dry_run:
        return {
            "detected_platforms": detected,
            "output_directory": str(target_dir),
            "planned_files": [str(p) for p in target_files.keys()],
            "files": {str(p): data for p, data in target_files.items()},
        }

    # Write files atomically
    target_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for fpath, data in target_files.items():
        fpath.write_text(json.dumps(data, indent=2) + "\n")
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
        help="Comma-separated platform override (e.g. flutter,android,ios,rust).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing configuration files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned scaffolding without writing files to disk.",
    )

    args = parser.parse_args()

    platforms = None
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
        print(f"Scaffolding completed successfully for platforms: {result['detected_platforms']}")
        if args.dry_run:
            print(f"Dry-run planned {len(result['planned_files'])} file(s):")
            for f in result["planned_files"]:
                print(f"  - {f}")
        else:
            print(f"Written {len(result['written_files'])} file(s) into {result['output_directory']}:")
            for f in result["written_files"]:
                print(f"  - {f}")
        return 0
    except ScaffoldError as err:
        print(f"Scaffolding error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
