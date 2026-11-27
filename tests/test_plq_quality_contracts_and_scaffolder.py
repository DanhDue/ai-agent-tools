"""Integration and unit tests for Task 03: Unified Quality Schemas, Validators, and Scaffolder.

Covers BDD Scenarios:
- PLQ-HP-03: Scaffolder generates 4-profile unified manifests and validators emit compact 1-line PASS
- PLQ-EC-05: Legacy v1 manifests without scheduled/release or new additive fields still pass validation
- PLQ-ST-01: Scaffolder does not overwrite existing standards_catalog.json and validates all 4 profiles
- PLQ-AR-02: Web provider schema matches draft 2020-12 parity with the other 5 provider schemas
- PLQ-FR-03: Validators reject invalid pool_mounts, standards_catalog traversal, non-object triage_surfaces, and bad regexes
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
QC_SCRIPTS_DIR = SKILLS_DIR / "quality_check" / "resources" / "scripts"
SCAFFOLD_SCRIPTS_DIR = SKILLS_DIR / "setup_quality_check" / "resources" / "scripts"

ALL_STACKS = ("flutter", "rust", "web", "python", "android", "ios")
ALL_PROFILES = ("pr", "epic", "scheduled", "release")
UNIFIED_CAPABILITIES = (
    "anti_stub",
    "security",
    "security_deps",
    "pr_diff_audit",
    "workspace_audit",
    "pr_impact",
    "workspace_impact",
    "license",
)
DUAL_FLOOR_COVERAGE_KEYS = (
    "command",
    "threshold",
    "min_package_coverage",
    "exclude_package_floor",
    "min_diff_coverage",
    "diff_base",
    "lcov_path",
    "report_path",
    "profdata_path",
)
TRIAGE_SURFACE_CATEGORIES = (
    "signature",
    "api_wire",
    "persistence",
    "concurrency",
    "test_weakening",
)
TASK_TIER_B_KEYS = (
    "format_prefixes",
    "lint_prefixes",
    "typecheck_prefixes",
    "boundary_prefixes",
    "boundary_triggers",
    "require_all_allowed_files_in_format",
)


def _run_cli(
    args: list[str], cwd: Path | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _validator_script(stack: str) -> Path:
    return (
        SKILLS_DIR
        / f"{stack}-quality-check"
        / "resources"
        / "scripts"
        / f"validate_{stack}_quality.py"
    )


def _schema_file(stack: str) -> Path:
    return (
        SKILLS_DIR
        / f"{stack}-quality-check"
        / "resources"
        / "schemas"
        / f"{stack}-quality.schema.json"
    )


def test_plq_ar_02_all_six_schemas_have_unified_parity() -> None:
    """[PLQ-AR-02] Web provider schema matches draft 2020-12 parity with the other 5 provider schemas."""
    # Check registry schema supports optional pool_mounts
    reg_schema_path = (
        SKILLS_DIR
        / "quality_check"
        / "resources"
        / "schemas"
        / "check-quality.schema.json"
    )
    reg_schema = json.loads(reg_schema_path.read_text(encoding="utf-8"))
    assert reg_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert reg_schema["additionalProperties"] is False
    assert reg_schema["properties"]["schema_version"]["const"] == 1
    assert "pool_mounts" in reg_schema["properties"]
    pool_mounts_schema = reg_schema["properties"]["pool_mounts"]
    assert pool_mounts_schema["type"] == "array"
    item_schema = pool_mounts_schema["items"]
    assert item_schema["additionalProperties"] is False
    assert set(item_schema["required"]) == {"path", "mode"}
    assert set(item_schema["properties"]["mode"]["enum"]) == {"symlink", "cow_copy"}

    # Check all 6 stack provider schemas for unified draft 2020-12 parity
    for stack in ALL_STACKS:
        schema_path = _schema_file(stack)
        assert schema_path.is_file(), (
            f"Missing schema for stack '{stack}': {schema_path}"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", (
            stack
        )
        assert schema["type"] == "object", stack
        assert schema["additionalProperties"] is False, stack
        assert schema["required"] == ["schema_version", "capabilities", "profiles"], (
            stack
        )

        props = schema["properties"]
        assert props["schema_version"]["const"] == 1, stack

        # Top-level additive v1 keys
        assert props["standards_catalog"]["type"] == "string", stack
        assert props["extensions"]["type"] == "array", stack
        assert props["extensions"]["items"]["pattern"] == r"^\.[a-z0-9]+$", stack

        task_tier_b = props["task_tier_b"]
        assert task_tier_b["type"] == "object", stack
        assert task_tier_b["additionalProperties"] is False, stack
        for key in TASK_TIER_B_KEYS:
            assert key in task_tier_b["properties"], (
                f"{stack}: missing task_tier_b.{key}"
            )

        triage_surfaces = props["triage_surfaces"]
        assert triage_surfaces["type"] == "object", stack
        assert triage_surfaces["additionalProperties"] is False, stack
        assert set(triage_surfaces["properties"].keys()) == set(
            TRIAGE_SURFACE_CATEGORIES
        ), stack

        # Profiles parity
        profiles = props["profiles"]
        assert profiles["type"] == "object", stack
        assert profiles["additionalProperties"] is False, stack
        assert profiles["required"] == ["pr", "epic"], stack
        assert set(profiles["properties"].keys()) == set(ALL_PROFILES), stack

        # Capabilities & dual-floor coverage parity
        caps = props["capabilities"]
        assert caps["type"] == "object", stack
        assert caps["additionalProperties"] is False, stack
        assert "^contracts_[a-z0-9_]+$" in caps.get("patternProperties", {}), stack

        cap_props = caps["properties"]
        for cap_name in UNIFIED_CAPABILITIES:
            assert cap_name in cap_props, (
                f"{stack}: missing unified capability '{cap_name}'"
            )
        assert "diff_coverage" in cap_props, (
            f"{stack}: missing 'diff_coverage' capability in schema"
        )

        cov = cap_props["coverage"]
        assert cov["type"] == "object", stack
        assert cov["additionalProperties"] is False, stack
        assert cov["required"] == ["command", "threshold"], stack
        for cov_key in DUAL_FLOOR_COVERAGE_KEYS:
            assert cov_key in cov["properties"], f"{stack}: missing coverage.{cov_key}"

    # Android schema keeps cleanup optional for legacy consumer compatibility
    android_schema = json.loads(_schema_file("android").read_text(encoding="utf-8"))
    assert "cleanup" in android_schema["properties"]["capabilities"]["properties"]

    # Android fixture must omit cleanup / pkill -9 java
    android_fixture = json.loads(
        (
            SKILLS_DIR
            / "android-quality-check"
            / "resources"
            / "fixtures"
            / "valid_android_quality.json"
        ).read_text(encoding="utf-8")
    )
    assert "cleanup" not in android_fixture["capabilities"]
    assert "pkill" not in json.dumps(android_fixture)


def test_plq_hp_03_scaffolder_generates_4_profile_manifests_and_compact_validators(
    tmp_path: Path,
) -> None:
    """[PLQ-HP-03] Scaffolder generates 4-profile unified manifests and validators emit compact 1-line PASS."""
    # Polyglot repository markers for all 6 stacks
    (tmp_path / "Cargo.toml").write_text(
        '[package]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (tmp_path / "pubspec.yaml").write_text("name: app\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name": "web-app"}\n', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "py-svc"\n', encoding="utf-8"
    )
    (tmp_path / "build.gradle.kts").write_text("// gradle\n", encoding="utf-8")
    (tmp_path / "Package.swift").write_text("// swift\n", encoding="utf-8")

    scaffold_script = SCAFFOLD_SCRIPTS_DIR / "scaffold_quality_manifest.py"
    scaff_proc = _run_cli([str(scaffold_script), "--root", str(tmp_path)])
    assert scaff_proc.returncode == 0, (
        f"Scaffolder failed: {scaff_proc.stderr}\n{scaff_proc.stdout}"
    )

    quality_dir = tmp_path / ".agents" / "quality"
    registry_path = quality_dir / "check_quality.json"
    catalog_path = quality_dir / "standards_catalog.json"
    assert registry_path.is_file()
    assert catalog_path.is_file()

    # Check starter standards catalog skeleton
    catalog_text = catalog_path.read_text(encoding="utf-8")
    catalog_data = json.loads(catalog_text)
    assert catalog_data["schema_version"] == 1
    for standard_token in ("25010", "27001", "OWASP", "CWE"):
        assert standard_token in catalog_text

    # Check check_quality.json registry and pool_mounts
    reg_data = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(reg_data["providers"]) == 6
    for prov in reg_data["providers"]:
        assert set(prov["profiles"]) == set(ALL_PROFILES)
    assert "pool_mounts" in reg_data and len(reg_data["pool_mounts"]) >= 4
    mount_map = {m["path"]: m["mode"] for m in reg_data["pool_mounts"]}
    assert mount_map.get(".dart_tool") == "cow_copy"
    assert mount_map.get("packages/*/.dart_tool") == "cow_copy"
    assert mount_map.get("target") == "symlink"
    assert mount_map.get("node_modules") == "symlink"

    # Validate each generated stack manifest contents
    for stack in ALL_STACKS:
        manifest_path = quality_dir / f"{stack}-quality.json"
        assert manifest_path.is_file(), f"Missing generated manifest for {stack}"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["schema_version"] == 1
        assert (
            manifest.get("standards_catalog")
            == ".agents/quality/standards_catalog.json"
        )
        assert set(manifest["profiles"].keys()) == set(ALL_PROFILES)

        caps = manifest["capabilities"]
        for unified_cap in UNIFIED_CAPABILITIES:
            assert unified_cap in caps, (
                f"{stack} missing unified capability {unified_cap}"
            )

        cov = caps["coverage"]
        assert isinstance(cov, dict)
        assert any("check_diff_coverage.py" in tok for tok in cov["command"]), stack
        assert "min_package_coverage" in cov
        assert "min_diff_coverage" in cov
        assert "diff_base" in cov

        # pr profile must include a diff-coverage capability invoking check_diff_coverage.py
        assert "diff_coverage" in caps, f"{stack}: missing diff_coverage capability"
        diff_cov_cmd = caps["diff_coverage"]
        assert isinstance(diff_cov_cmd, list), stack
        assert any("check_diff_coverage.py" in tok for tok in diff_cov_cmd), stack
        assert "--min-coverage" in diff_cov_cmd and "0" in diff_cov_cmd, stack
        assert "--min-diff-coverage" in diff_cov_cmd, stack
        assert "diff_coverage" in manifest["profiles"]["pr"], (
            f"{stack}: pr profile missing diff_coverage"
        )

        # release profile must be a true superset of epic (including pr_diff_audit and pr_impact)
        epic_caps = set(manifest["profiles"]["epic"])
        release_caps = set(manifest["profiles"]["release"])
        assert epic_caps.issubset(release_caps), (
            f"{stack}: release profile missing epic capabilities: {sorted(epic_caps - release_caps)}"
        )
        for release_extra in ("security_deps", "workspace_audit", "workspace_impact"):
            assert release_extra in release_caps, (
                f"{stack}: release profile missing {release_extra}"
            )

        # Every scaffolded capability key must be permitted by the stack's JSON Schema
        schema = json.loads(_schema_file(stack).read_text(encoding="utf-8"))
        allowed_schema_caps = set(schema["properties"]["capabilities"]["properties"])
        assert set(caps.keys()).issubset(allowed_schema_caps), (
            f"{stack}: scaffolded capabilities not in schema: {sorted(set(caps.keys()) - allowed_schema_caps)}"
        )

        if stack == "android":
            assert "cleanup" not in caps
            assert "pkill" not in json.dumps(manifest)

    # 1. validate_quality_contract.py registry keeps JSON default stdout + supports --compact
    qc_script = QC_SCRIPTS_DIR / "validate_quality_contract.py"
    reg_default = _run_cli(
        [str(qc_script), "registry", str(registry_path), "--profile", "epic"]
    )
    assert reg_default.returncode == 0, reg_default.stdout + reg_default.stderr
    reg_json = json.loads(reg_default.stdout)
    assert reg_json["status"] == "PASS"
    assert len(reg_json["providers"]) == 6

    reg_compact = _run_cli(
        [
            str(qc_script),
            "registry",
            str(registry_path),
            "--profile",
            "epic",
            "--compact",
        ]
    )
    assert reg_compact.returncode == 0
    compact_lines = [ln for ln in reg_compact.stdout.splitlines() if ln.strip()]
    assert len(compact_lines) == 1
    assert compact_lines[0].startswith("PASS:")

    # Also verify invocation & reconcile keep JSON default stdout + --compact
    sha = "a" * 40
    inv_payload = json.dumps(
        {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": sha,
            "provider_id": "rust-core",
            "required": True,
        }
    )
    inv_default = _run_cli([str(qc_script), "invocation", inv_payload])
    assert inv_default.returncode == 0
    inv_parsed = json.loads(inv_default.stdout)
    assert inv_parsed["status"] == "PASS"
    assert inv_parsed["invocation"]["profile"] == "epic"

    inv_compact = _run_cli([str(qc_script), "invocation", inv_payload, "--compact"])
    assert inv_compact.returncode == 0
    assert len(inv_compact.stdout.strip().splitlines()) == 1
    assert inv_compact.stdout.strip().startswith("PASS:")

    res_fixture = (
        SKILLS_DIR / "quality_check" / "resources" / "fixtures" / "valid_result.json"
    )
    res_inv = json.dumps(
        {
            "contract_version": 1,
            "profile": "epic",
            "base_ref": "main",
            "repository_sha": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
            "provider_id": "rust-core",
            "required": True,
        }
    )
    res_default = _run_cli(
        [str(qc_script), "result", str(res_fixture), "--invocation", res_inv]
    )
    assert res_default.returncode == 0, res_default.stdout + res_default.stderr
    assert len(res_default.stdout.strip().splitlines()) == 1
    assert res_default.stdout.strip().startswith("PASS:")

    res_json_proc = _run_cli(
        [str(qc_script), "result", str(res_fixture), "--invocation", res_inv, "--json"]
    )
    assert res_json_proc.returncode == 0
    assert json.loads(res_json_proc.stdout)["status"] == "PASS"

    plan_payload = json.dumps([{"id": "rust-core", "required": True}])
    rec_default = _run_cli(
        [str(qc_script), "reconcile", plan_payload, "--results", str(res_fixture)]
    )
    assert rec_default.returncode == 0
    rec_parsed = json.loads(rec_default.stdout)
    assert rec_parsed["status"] == "PASS"
    assert len(rec_parsed["results"]) == 1

    rec_compact = _run_cli(
        [
            str(qc_script),
            "reconcile",
            plan_payload,
            "--results",
            str(res_fixture),
            "--compact",
        ]
    )
    assert rec_compact.returncode == 0
    assert len(rec_compact.stdout.strip().splitlines()) == 1
    assert rec_compact.stdout.strip().startswith("PASS:")

    # 2. validate_quality_contract.py capability & all 6 validate_<stack>_quality.py default to 1-line PASS:
    for stack in ALL_STACKS:
        manifest_path = quality_dir / f"{stack}-quality.json"
        for profile in ALL_PROFILES:
            cap_proc = _run_cli(
                [str(qc_script), "capability", str(manifest_path), "--profile", profile]
            )
            assert cap_proc.returncode == 0, (
                f"capability failed for {stack}/{profile}: {cap_proc.stdout}"
            )
            cap_lines = [ln for ln in cap_proc.stdout.splitlines() if ln.strip()]
            assert len(cap_lines) == 1
            assert cap_lines[0].startswith("PASS:")

            val_proc = _run_cli(
                [
                    str(_validator_script(stack)),
                    str(manifest_path),
                    "--profile",
                    profile,
                ]
            )
            assert val_proc.returncode == 0, (
                f"{stack}/{profile} validator failed: {val_proc.stdout}"
            )
            val_lines = [ln for ln in val_proc.stdout.splitlines() if ln.strip()]
            assert len(val_lines) == 1, (
                f"{stack}/{profile} expected 1 line, got: {val_proc.stdout!r}"
            )
            assert val_lines[0].startswith(f"PASS: {stack}-quality"), val_lines[0]
            assert f"profile={profile}" in val_lines[0]

        # Also check --json and --verbose opt-in flags on each stack validator
        json_proc = _run_cli(
            [
                str(_validator_script(stack)),
                str(manifest_path),
                "--profile",
                "pr",
                "--json",
            ]
        )
        assert json_proc.returncode == 0
        parsed_json = json.loads(json_proc.stdout)
        assert parsed_json == {"status": "PASS", "findings": []}

        verbose_proc = _run_cli(
            [
                str(_validator_script(stack)),
                str(manifest_path),
                "--profile",
                "pr",
                "--verbose",
            ]
        )
        assert verbose_proc.returncode == 0
        verbose_lines = [ln for ln in verbose_proc.stdout.splitlines() if ln.strip()]
        assert len(verbose_lines) > 1
        assert verbose_lines[0].startswith(f"PASS: {stack}-quality")

    # Templates also validate cleanly across all 4 profiles
    templates_dir = SKILLS_DIR / "setup_quality_check" / "resources" / "templates"
    polyglot_tpl = templates_dir / "polyglot-check-quality.template.json"
    web_tpl = templates_dir / "web-quality.template.json"
    web_tpl_data = json.loads(web_tpl.read_text(encoding="utf-8"))
    assert "diff_coverage" in web_tpl_data["capabilities"]
    assert any(
        "check_diff_coverage.py" in tok
        for tok in web_tpl_data["capabilities"]["diff_coverage"]
    )
    assert "diff_coverage" in web_tpl_data["profiles"]["pr"]
    assert set(web_tpl_data["profiles"]["epic"]).issubset(
        set(web_tpl_data["profiles"]["release"])
    )
    for profile in ALL_PROFILES:
        tpl_reg = _run_cli(
            [
                str(qc_script),
                "registry",
                str(polyglot_tpl),
                "--profile",
                profile,
                "--compact",
            ]
        )
        assert tpl_reg.returncode == 0, tpl_reg.stdout
        tpl_web = _run_cli(
            [str(_validator_script("web")), str(web_tpl), "--profile", profile]
        )
        assert tpl_web.returncode == 0, tpl_web.stdout


def test_plq_ec_05_legacy_v1_manifests_still_pass() -> None:
    """[PLQ-EC-05] Legacy v1 manifests without scheduled/release or new additive fields still pass validation."""
    if str(QC_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(QC_SCRIPTS_DIR))
    from validate_quality_contract import (
        validate_capability_manifest,
        validate_registry,
    )

    legacy_reg = json.loads(
        (
            SKILLS_DIR
            / "quality_check"
            / "resources"
            / "fixtures"
            / "valid_registry.json"
        ).read_text(encoding="utf-8")
    )
    for profile in ("pr", "epic"):
        res_reg = validate_registry(
            legacy_reg,
            profile,
            available_skills={
                "d3nexus:rust-quality-check",
                "d3nexus:doc_quality_check",
            },
        )
        assert res_reg["status"] == "PASS", res_reg
        assert res_reg["findings"] == []
        assert len(res_reg["providers"]) == 2

    legacy_manifests: dict[str, dict[str, Any]] = {}
    for stack in ("flutter", "rust", "python", "android", "ios"):
        fixture_path = (
            SKILLS_DIR
            / f"{stack}-quality-check"
            / "resources"
            / "fixtures"
            / f"valid_{stack}_quality.json"
        )
        legacy_manifests[stack] = json.loads(fixture_path.read_text(encoding="utf-8"))

    # Legacy Android manifest WITH optional cleanup field must still pass
    legacy_android_with_cleanup = json.loads(json.dumps(legacy_manifests["android"]))
    legacy_android_with_cleanup["capabilities"]["cleanup"] = ["pkill", "-9", "java"]
    legacy_android_with_cleanup["profiles"]["epic"].append("cleanup")

    # Legacy Web manifest with only pr/epic and original capability keys
    legacy_manifests["web"] = {
        "schema_version": 1,
        "capabilities": {
            "type_check": ["npm", "run", "check"],
            "lint": ["npm", "run", "lint"],
            "test_unit": ["npm", "run", "test:unit"],
            "test_e2e": ["npx", "playwright", "test"],
        },
        "profiles": {
            "pr": ["type_check", "lint", "test_unit"],
            "epic": ["type_check", "lint", "test_unit", "test_e2e"],
        },
    }

    validator_fns = {}
    for stack in ALL_STACKS:
        sdir = SKILLS_DIR / f"{stack}-quality-check" / "resources" / "scripts"
        if str(sdir) not in sys.path:
            sys.path.insert(0, str(sdir))
    from validate_android_quality import validate_android_config
    from validate_flutter_quality import validate_flutter_config
    from validate_ios_quality import validate_ios_config
    from validate_python_quality import validate_python_config
    from validate_rust_quality import validate_rust_config
    from validate_web_quality import validate_manifest

    validator_fns = {
        "flutter": validate_flutter_config,
        "rust": validate_rust_config,
        "web": validate_manifest,
        "python": validate_python_config,
        "android": validate_android_config,
        "ios": validate_ios_config,
    }

    for stack, manifest in legacy_manifests.items():
        for profile in ("pr", "epic"):
            cap_res = validate_capability_manifest(manifest, profile)
            assert cap_res == {"status": "PASS", "findings": []}, (
                f"capability {stack}/{profile}: {cap_res}"
            )
            stack_res = validator_fns[stack](manifest, profile)
            assert stack_res == {"status": "PASS", "findings": []}, (
                f"{stack}/{profile}: {stack_res}"
            )

    # Verify legacy Android cleanup still passes
    assert validate_android_config(legacy_android_with_cleanup, "epic") == {
        "status": "PASS",
        "findings": [],
    }


def test_plq_st_01_scaffolder_preserves_existing_standards_catalog_and_validates_4_profiles(
    tmp_path: Path,
) -> None:
    """[PLQ-ST-01] Scaffolder does not overwrite existing standards_catalog.json and validates all 4 profiles."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n', encoding="utf-8"
    )
    (tmp_path / "pubspec.yaml").write_text("name: demo_flutter\n", encoding="utf-8")

    quality_dir = tmp_path / ".agents" / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    catalog_path = quality_dir / "standards_catalog.json"
    sentinel_bytes = b'{\n  "schema_version": 1,\n  "rules": ["CUSTOM-RULE-01"]\n}\n'
    catalog_path.write_bytes(sentinel_bytes)

    scaffold_script = SCAFFOLD_SCRIPTS_DIR / "scaffold_quality_manifest.py"
    # First run without --force must succeed (not fail on pre-existing standards_catalog.json)
    proc1 = _run_cli([str(scaffold_script), "--root", str(tmp_path)])
    assert proc1.returncode == 0, proc1.stdout + proc1.stderr
    assert catalog_path.read_bytes() == sentinel_bytes

    # Second run WITH --force must ALSO preserve standards_catalog.json byte-for-byte
    proc2 = _run_cli([str(scaffold_script), "--root", str(tmp_path), "--force"])
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    assert catalog_path.read_bytes() == sentinel_bytes

    for stack in ("python", "flutter"):
        manifest_path = quality_dir / f"{stack}-quality.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["standards_catalog"] == ".agents/quality/standards_catalog.json"
        for profile in ALL_PROFILES:
            val = _run_cli(
                [
                    str(_validator_script(stack)),
                    str(manifest_path),
                    "--profile",
                    profile,
                ]
            )
            assert val.returncode == 0, f"{stack}/{profile}: {val.stdout}"
            assert val.stdout.strip().startswith(f"PASS: {stack}-quality")


def test_plq_fr_03_validators_reject_invalid_pool_mounts_traversal_and_triage_surfaces(
    tmp_path: Path,
) -> None:
    """[PLQ-FR-03] Validators reject invalid pool_mounts, standards_catalog traversal, non-object triage_surfaces, and bad regexes."""
    if str(QC_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(QC_SCRIPTS_DIR))
    py_scripts = SKILLS_DIR / "python-quality-check" / "resources" / "scripts"
    if str(py_scripts) not in sys.path:
        sys.path.insert(0, str(py_scripts))

    from validate_python_quality import validate_python_config
    from validate_quality_contract import (
        validate_capability_manifest,
        validate_registry,
    )

    # 1. Invalid pool_mounts in check_quality.json
    bad_registry = {
        "schema_version": 1,
        "providers": [
            {
                "id": "python-core",
                "skill": "d3nexus:python-quality-check",
                "required": True,
                "profiles": ["pr", "epic"],
            }
        ],
        "pool_mounts": [
            {"path": "/etc/passwd", "mode": "hardlink"},
            {"path": "../outside_secret", "mode": "symlink"},
            {"path": "", "mode": "cow_copy"},
        ],
    }
    reg_res = validate_registry(bad_registry, "pr")
    assert reg_res["status"] == "BLOCKED"
    assert reg_res["providers"] == []
    reg_codes = {f["code"] for f in reg_res["findings"]}
    assert "invalid_pool_mount_path" in reg_codes
    assert "invalid_pool_mount_mode" in reg_codes

    reg_file = tmp_path / "check_quality.json"
    reg_file.write_text(json.dumps(bad_registry), encoding="utf-8")
    qc_script = QC_SCRIPTS_DIR / "validate_quality_contract.py"
    reg_cli = _run_cli([str(qc_script), "registry", str(reg_file), "--profile", "pr"])
    assert reg_cli.returncode == 1
    assert json.loads(reg_cli.stdout)["status"] == "BLOCKED"

    reg_cli_compact = _run_cli(
        [str(qc_script), "registry", str(reg_file), "--profile", "pr", "--compact"]
    )
    assert reg_cli_compact.returncode == 1
    assert reg_cli_compact.stdout.startswith("BLOCKED:")
    assert "invalid_pool_mount_path" in reg_cli_compact.stdout
    assert "invalid_pool_mount_mode" in reg_cli_compact.stdout

    # 2. Invalid standards_catalog traversal + non-object triage_surfaces + invalid regex in python-quality.json
    bad_python_array_ts: dict[str, Any] = {
        "schema_version": 1,
        "standards_catalog": "../escape.json",
        "extensions": ["py", ".OK_BAD"],
        "task_tier_b": {
            "unknown_option": ["x"],
            "format_prefixes": "ruff",
            "require_all_allowed_files_in_format": "true",
        },
        "triage_surfaces": ["not_an_object"],
        "capabilities": {
            "lint": ["ruff", "check", "."],
            "coverage": {
                "command": ["pytest", "--cov"],
                "threshold": 0.8,
                "min_package_coverage": 1.5,
                "min_diff_coverage": -0.1,
                "exclude_package_floor": "legacy",
                "diff_base": "",
            },
        },
        "profiles": {
            "pr": ["lint"],
        },
    }
    py_res_1 = validate_python_config(bad_python_array_ts, "pr")
    assert py_res_1["status"] == "BLOCKED"
    codes_1 = {f["code"] for f in py_res_1["findings"]}
    assert "invalid_standards_catalog_path" in codes_1
    assert "invalid_extensions" in codes_1
    assert "invalid_task_tier_b" in codes_1
    assert "invalid_triage_surfaces_format" in codes_1
    assert "invalid_coverage_threshold" in codes_1
    assert "invalid_coverage_config" in codes_1

    # Also test unknown category + bad regex in object-shaped triage_surfaces
    bad_python_regex_ts: dict[str, Any] = {
        "schema_version": 1,
        "standards_catalog": "/etc/passwd",
        "triage_surfaces": {
            "api_wire": ["[unclosed-regex"],
            "unknown_category": ["foo"],
        },
        "capabilities": {
            "lint": ["ruff", "check", "."],
        },
        "profiles": {
            "pr": ["lint"],
        },
    }
    py_res_2 = validate_python_config(bad_python_regex_ts, "pr")
    assert py_res_2["status"] == "BLOCKED"
    codes_2 = {f["code"] for f in py_res_2["findings"]}
    assert "invalid_standards_catalog_path" in codes_2
    assert "unknown_triage_surface_category" in codes_2
    assert "invalid_triage_surface_regex" in codes_2

    # Same additive checks work through validate_capability_manifest
    cap_res_2 = validate_capability_manifest(bad_python_regex_ts, "pr")
    assert cap_res_2["status"] == "BLOCKED"
    assert {
        "invalid_standards_catalog_path",
        "unknown_triage_surface_category",
        "invalid_triage_surface_regex",
    } <= {f["code"] for f in cap_res_2["findings"]}

    # CLI exits 1 with expanded diagnostics by default and JSON with --json
    py_file = tmp_path / "python-quality.json"
    py_file.write_text(json.dumps(bad_python_regex_ts), encoding="utf-8")
    py_cli = _run_cli(
        [str(_validator_script("python")), str(py_file), "--profile", "pr"]
    )
    assert py_cli.returncode == 1
    assert py_cli.stdout.startswith("BLOCKED: python-quality")
    assert "invalid_triage_surface_regex" in py_cli.stdout
    assert "unknown_triage_surface_category" in py_cli.stdout

    py_cli_json = _run_cli(
        [str(_validator_script("python")), str(py_file), "--profile", "pr", "--json"]
    )
    assert py_cli_json.returncode == 1
    parsed_py = json.loads(py_cli_json.stdout)
    assert parsed_py["status"] == "BLOCKED"
    assert "invalid_triage_surface_regex" in {f["code"] for f in parsed_py["findings"]}


def test_provider_manifest_common_edge_cases() -> None:
    """Exercise additional rejection and acceptance branches in _provider_manifest_common."""
    if str(QC_SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(QC_SCRIPTS_DIR))
    from _provider_manifest_common import (
        format_validator_cli_output,
        validate_additive_provider_fields,
        validate_dual_floor_coverage,
        validate_pool_mounts,
    )

    # pool_mounts malformed container & entries
    assert validate_pool_mounts("not-a-list")[0]["code"] == "invalid_pool_mounts_format"
    entry_findings = validate_pool_mounts(
        ["bad-entry", {"path": "cache", "mode": "symlink", "extra": 1}]
    )
    entry_codes = {f["code"] for f in entry_findings}
    assert "invalid_pool_mounts_format" in entry_codes
    assert "unknown_field" in entry_codes
    assert (
        validate_pool_mounts([{"path": "packages/*/.dart_tool", "mode": "cow_copy"}])
        == []
    )

    # Valid additive fields produce zero findings
    valid_cfg: dict[str, Any] = {
        "standards_catalog": ".agents/quality/standards_catalog.json",
        "extensions": [".py", ".pyi"],
        "task_tier_b": {
            "format_prefixes": ["ruff format --check"],
            "lint_prefixes": ["ruff check"],
            "typecheck_prefixes": ["mypy"],
            "boundary_prefixes": ["lint-imports"],
            "boundary_triggers": ["pyproject.toml"],
            "require_all_allowed_files_in_format": True,
        },
        "triage_surfaces": {
            "signature": [r"def\s+[a-z]"],
            "api_wire": [r"@router\."],
            "persistence": [r"alembic"],
            "concurrency": [r"asyncio\.Lock"],
            "test_weakening": [r"pytest\.mark\.skip"],
        },
    }
    assert validate_additive_provider_fields(valid_cfg) == []

    # Boolean thresholds and bad triage_surfaces pattern container are rejected
    cov_findings = validate_dual_floor_coverage(
        {
            "command": ["pytest"],
            "threshold": 0.8,
            "min_package_coverage": True,
            "min_diff_coverage": False,
            "lcov_path": "",
            "report_path": 123,
            "profdata_path": "  ",
        }
    )
    cov_codes = {f["code"] for f in cov_findings}
    assert "invalid_coverage_threshold" in cov_codes
    assert "invalid_coverage_config" in cov_codes

    ts_bad_list = validate_additive_provider_fields(
        {
            "task_tier_b": "not-a-dict",
            "triage_surfaces": {"signature": "not-a-list", "concurrency": [""]},
        }
    )
    ts_codes = {f["code"] for f in ts_bad_list}
    assert "invalid_task_tier_b" in ts_codes
    assert "invalid_triage_surfaces_format" in ts_codes
    assert "invalid_triage_surface_regex" in ts_codes

    # Formatter outputs compact PASS, verbose PASS (with & without details), expanded BLOCKED, and JSON
    assert validate_dual_floor_coverage("not-a-dict") == []
    assert (
        validate_pool_mounts([{"path": 123, "mode": "symlink"}])[0]["code"]
        == "invalid_pool_mount_path"
    )
    pass_res: dict[str, Any] = {"status": "PASS", "findings": []}
    assert format_validator_cli_output(
        "python-quality", "pr", pass_res, item_count=4
    ) == ("PASS: python-quality (profile=pr, caps=4)")
    assert "findings: 0" in format_validator_cli_output(
        "python-quality", "pr", pass_res, verbose=True, item_count=4
    )
    assert "  - lint" in format_validator_cli_output(
        "python-quality",
        "pr",
        pass_res,
        verbose=True,
        item_count=2,
        details=["lint", "test"],
    )
    assert (
        json.loads(
            format_validator_cli_output("python-quality", "pr", pass_res, as_json=True)
        )
        == pass_res
    )
    blocked_out = format_validator_cli_output(
        "python-quality",
        "pr",
        {
            "status": "BLOCKED",
            "findings": [{"code": "c1", "message": "m1", "field": "f1"}],
        },
        item_count=1,
    )
    assert blocked_out.startswith("BLOCKED: python-quality")
    assert "  - c1: m1 [field=f1]" in blocked_out


class TestPLQQualityContracts_Integration:
    """Integration provenance suite for Tier C scenarios assigned to Task 03."""

    def test_plq_hp_03_integration(self, tmp_path: Path) -> None:
        """[PLQ-HP-03] Scaffolder generates 4-profile unified manifests and compact 1-line PASS."""
        test_plq_hp_03_scaffolder_generates_4_profile_manifests_and_compact_validators(
            tmp_path
        )

    def test_plq_ec_05_integration(self) -> None:
        """[PLQ-EC-05] Legacy v1 manifests without scheduled/release or additive fields still pass."""
        test_plq_ec_05_legacy_v1_manifests_still_pass()

    def test_plq_st_01_integration(self, tmp_path: Path) -> None:
        """[PLQ-ST-01] Scaffolder preserves existing standards_catalog.json and validates all 4 profiles."""
        test_plq_st_01_scaffolder_preserves_existing_standards_catalog_and_validates_4_profiles(
            tmp_path
        )

    def test_plq_ar_02_integration(self) -> None:
        """[PLQ-AR-02] All 6 provider schemas declare unified draft 2020-12 parity."""
        test_plq_ar_02_all_six_schemas_have_unified_parity()

    def test_plq_fr_03_integration(self, tmp_path: Path) -> None:
        """[PLQ-FR-03] Validators reject invalid pool_mounts, standards_catalog traversal, and triage_surfaces."""
        test_plq_fr_03_validators_reject_invalid_pool_mounts_traversal_and_triage_surfaces(
            tmp_path
        )
