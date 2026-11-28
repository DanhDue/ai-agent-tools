"""Unit and integration tests for Task 01: Registry wrappers, test_routing, and 6-stack schemas.

Covers BDD Scenarios:
- SLQR-HP-01: Provider schemas and runtime validators accept additive test_routing,
  package_floors, architecture, and cache capabilities
- SLQR-EC-01: Registry prefix matcher and TierBContractAdapter unwrap monorepo
  directory flags, mise exec prefixes, and relocated script paths while rejecting
  mismatched directories
- SLQR-FR-01: Provider manifest validators fail closed on invalid test_routing keys
  or path traversal globs
"""

from __future__ import annotations

import ast
import importlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = REPO_ROOT / "skills"
IMPL_SCRIPTS_DIR = SKILLS_DIR / "dev-implementation" / "resources" / "scripts"
QC_SCRIPTS_DIR = SKILLS_DIR / "quality_check" / "resources" / "scripts"
SCAFFOLD_SCRIPT = (
    SKILLS_DIR
    / "setup_quality_check"
    / "resources"
    / "scripts"
    / "scaffold_quality_manifest.py"
)

ALL_STACKS: tuple[str, ...] = (
    "flutter",
    "rust",
    "web",
    "python",
    "android",
    "ios",
)
ALL_PROFILES: tuple[str, ...] = ("pr", "epic", "scheduled", "release")
EXPECTED_TEST_ROUTING_KEYS: tuple[str, ...] = (
    "canonical_test_globs",
    "forbidden_test_globs",
    "paired_source_globs",
    "lcov_unit_test_globs",
    "cache_bust_extensions",
)
CONTRACTS_PATTERN_RE = re.compile(r"^contracts_[a-z0-9_]+$")

for _scripts_dir in (IMPL_SCRIPTS_DIR, QC_SCRIPTS_DIR):
    if str(_scripts_dir) not in sys.path:
        sys.path.insert(0, str(_scripts_dir))
for _stack in ALL_STACKS:
    _stack_scripts = SKILLS_DIR / f"{_stack}-quality-check" / "resources" / "scripts"
    if str(_stack_scripts) not in sys.path:
        sys.path.insert(0, str(_stack_scripts))


@dataclass(frozen=True)
class _FakeAllowedEntry:
    pattern: str
    new: bool = False


@dataclass(frozen=True)
class _FakeRow:
    id: str
    phase: str
    command: str
    needs: tuple[str, ...] = ()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _schema_path(stack: str) -> Path:
    return (
        SKILLS_DIR
        / f"{stack}-quality-check"
        / "resources"
        / "schemas"
        / f"{stack}-quality.schema.json"
    )


@pytest.fixture(scope="module")
def registry_mod() -> Any:
    return importlib.import_module("_stack_lifecycle_registry")


@pytest.fixture(scope="module")
def provider_common_mod() -> Any:
    return importlib.import_module("_provider_manifest_common")


@pytest.fixture(scope="module")
def stack_schemas() -> dict[str, dict[str, Any]]:
    return {
        stack: json.loads(_schema_path(stack).read_text(encoding="utf-8"))
        for stack in ALL_STACKS
    }


@pytest.fixture(scope="module")
def stack_validators() -> dict[str, Callable[[dict[str, Any], str], dict[str, Any]]]:
    from validate_android_quality import validate_android_config
    from validate_flutter_quality import validate_flutter_config
    from validate_ios_quality import validate_ios_config
    from validate_python_quality import validate_python_config
    from validate_rust_quality import validate_rust_config
    from validate_web_quality import validate_manifest

    return {
        "flutter": validate_flutter_config,
        "rust": validate_rust_config,
        "web": validate_manifest,
        "python": validate_python_config,
        "android": validate_android_config,
        "ios": validate_ios_config,
    }


@pytest.fixture(scope="module")
def scaffolded_six_stack_manifests(
    tmp_path_factory: pytest.TempPathFactory,
) -> dict[str, dict[str, Any]]:
    root = tmp_path_factory.mktemp("slqr_scaffold_six_stacks")
    (root / "Cargo.toml").write_text(
        '[package]\nname = "core"\nversion = "0.1.0"\n', encoding="utf-8"
    )
    (root / "pubspec.yaml").write_text("name: app\n", encoding="utf-8")
    (root / "package.json").write_text('{"name": "web-app"}\n', encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "py-svc"\n', encoding="utf-8"
    )
    (root / "build.gradle.kts").write_text("// gradle\n", encoding="utf-8")
    (root / "Package.swift").write_text("// swift\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(SCAFFOLD_SCRIPT), "--root", str(root)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"Scaffolder failed: {proc.stderr}\n{proc.stdout}"
    quality_dir = root / ".agents" / "quality"
    return {
        stack: json.loads(
            (quality_dir / f"{stack}-quality.json").read_text(encoding="utf-8")
        )
        for stack in ALL_STACKS
    }


def _minimal_manifest(stack: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "capabilities": {
            "lint": ["echo", f"lint-{stack}"],
            "test": ["echo", f"test-{stack}"],
            "coverage": {
                "command": ["echo", f"cov-{stack}"],
                "threshold": 0.8,
                "min_package_coverage": 0.8,
                "min_diff_coverage": 0.85,
                "diff_base": "main",
                "package_floors": ".agents/quality/coverage_floors.json",
            },
        },
        "profiles": {
            "pr": ["lint", "test"],
            "epic": ["lint", "test", "coverage"],
            "scheduled": ["lint", "test", "coverage"],
            "release": ["lint", "test", "coverage"],
        },
    }


def test_slqr_hp_01_provider_schemas_and_validators_accept_additive_contracts(
    stack_schemas: dict[str, dict[str, Any]],
    stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
    scaffolded_six_stack_manifests: dict[str, dict[str, Any]],
    provider_common_mod: Any,
) -> None:
    """[SLQR-HP-01] Provider schemas and runtime validators accept additive test_routing, package_floors, architecture, and cache capabilities."""
    from validate_quality_contract import validate_capability_manifest

    # Explicitly assert Flutter schema has top-level test_routing (TDD RED anchor)
    flutter_props = stack_schemas["flutter"]["properties"]
    assert "test_routing" in flutter_props
    assert provider_common_mod.TEST_ROUTING_KEYS == EXPECTED_TEST_ROUTING_KEYS

    templates_dir = SKILLS_DIR / "setup_quality_check" / "resources" / "templates"
    repo_quality_dir = REPO_ROOT / ".agents" / "quality"

    for stack in ALL_STACKS:
        schema = stack_schemas[stack]
        props = schema["properties"]

        # Top-level test_routing contract across all 6 schemas
        assert "test_routing" in props, f"{stack}: missing top-level test_routing"
        tr_schema = props["test_routing"]
        assert tr_schema["type"] == "object", stack
        assert tr_schema["additionalProperties"] is False, stack
        assert set(tr_schema["properties"].keys()) == set(EXPECTED_TEST_ROUTING_KEYS), (
            stack
        )
        assert (
            tr_schema["properties"]["cache_bust_extensions"]["items"]["pattern"]
            == r"^\.[a-z0-9]+$"
        ), stack

        # coverage.properties.package_floors across all 6 schemas
        cap_props = props["capabilities"]["properties"]
        cov_props = cap_props["coverage"]["properties"]
        assert "package_floors" in cov_props, (
            f"{stack}: missing coverage.package_floors"
        )
        assert cov_props["package_floors"]["type"] == "string", stack

        # Stack-specific additive capabilities
        if stack == "flutter":
            assert "architecture" in cap_props, (
                "flutter: missing capabilities.architecture"
            )
        if stack in ("rust", "web", "python"):
            assert "cache_enable" in cap_props, (
                f"{stack}: missing capabilities.cache_enable"
            )
            assert "cache_purge" in cap_props, (
                f"{stack}: missing capabilities.cache_purge"
            )

        # Parity across scaffolded + repo + template manifests
        observed_caps = set(
            scaffolded_six_stack_manifests[stack]["capabilities"].keys()
        )
        for candidate_path in (
            repo_quality_dir / f"{stack}-quality.json",
            templates_dir / f"{stack}-quality.template.json",
        ):
            if candidate_path.is_file():
                candidate_data = json.loads(candidate_path.read_text(encoding="utf-8"))
                observed_caps.update(candidate_data.get("capabilities", {}).keys())

        schema_cap_keys = set(cap_props.keys())
        missing_caps = sorted(
            cap
            for cap in observed_caps
            if cap not in schema_cap_keys and not CONTRACTS_PATTERN_RE.match(cap)
        )
        assert missing_caps == [], (
            f"{stack}: capabilities missing from schema: {missing_caps}"
        )

        # Runtime validators accept test_routing, package_floors, architecture, and cache caps across all 4 profiles
        manifest = json.loads(json.dumps(scaffolded_six_stack_manifests[stack]))
        manifest["test_routing"] = {
            "canonical_test_globs": ["tests/unit/**/test_*.py"],
            "forbidden_test_globs": ["tests/test_*.py"],
            "paired_source_globs": ["src/api/**/*.py"],
            "lcov_unit_test_globs": ["tests/js/*.test.mjs"],
            "cache_bust_extensions": [".js", ".css"],
        }
        manifest["capabilities"]["coverage"]["package_floors"] = (
            ".agents/quality/coverage_floors.json"
        )
        if stack == "flutter":
            manifest["capabilities"]["architecture"] = ["melos", "run", "architecture"]
            manifest["profiles"]["epic"].append("architecture")
        if stack in ("rust", "web", "python"):
            manifest["capabilities"]["cache_enable"] = ["echo", "cache-enable"]
            manifest["capabilities"]["cache_purge"] = ["echo", "cache-purge"]
            manifest["profiles"]["scheduled"].extend(["cache_enable", "cache_purge"])

        for profile in ALL_PROFILES:
            stack_res = stack_validators[stack](manifest, profile)
            assert stack_res == {"status": "PASS", "findings": []}, (
                f"{stack}/{profile}: {stack_res}"
            )
            cap_res = validate_capability_manifest(manifest, profile)
            assert cap_res == {"status": "PASS", "findings": []}, (
                f"capability {stack}/{profile}: {cap_res}"
            )


def _verify_slqr_ec_01_registry_wrappers_mise_and_relocated_scripts(
    tmp_path: Path,
    registry_mod: Any,
) -> None:
    """[SLQR-EC-01] Registry prefix matcher and TierBContractAdapter unwrap monorepo directory flags, mise exec prefixes, and relocated script paths while rejecting mismatched directories."""
    quality_dir = tmp_path / ".agents" / "quality"
    _write_json(
        quality_dir / "python-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": [
                    "uv",
                    "--directory",
                    "apps/align-worker",
                    "run",
                    "ruff",
                    "check",
                    ".",
                ],
                "test": ["uv", "--directory", "apps/align-worker", "run", "pytest"],
            },
            "profiles": {"pr": ["lint", "test"], "epic": ["lint", "test"]},
        },
    )
    _write_json(
        quality_dir / "ios-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": ["mise", "exec", "--", "swiftformat", "--lint", "."],
                "lint": [
                    "mise",
                    "exec",
                    "--",
                    "swiftlint",
                    "lint",
                    "--config",
                    "quality/.swiftlint.yml",
                    "--strict",
                ],
                "test": ["swift", "test"],
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "test"],
            },
        },
    )
    _write_json(
        quality_dir / "web-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "lint": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                    "--target-dir",
                    "src/preview",
                ],
                "type_check": [
                    "python3",
                    "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                    "--target-dir",
                    "src/preview",
                ],
                "test": ["node", "--test", "tests/js/*.test.mjs"],
            },
            "profiles": {
                "pr": ["lint", "type_check", "test"],
                "epic": ["lint", "type_check", "test"],
            },
        },
    )

    # 1. Python monorepo --directory enforcement via _subcommand_matches_prefix
    adapter = registry_mod.TierBContractAdapter.from_repo(tmp_path)
    py_lint_prefixes = adapter.descriptors["python"].default_tier_b.lint_prefixes
    assert "uv --directory apps/align-worker run ruff check" in py_lint_prefixes

    matching_sub = [
        "uv",
        "--directory",
        "apps/align-worker",
        "run",
        "ruff",
        "check",
        "src/mod.py",
    ]
    mismatched_sub = [
        "uv",
        "--directory",
        "apps/other-worker",
        "run",
        "ruff",
        "check",
        "src/mod.py",
    ]
    assert any(
        registry_mod._subcommand_matches_prefix(matching_sub, p)[0]
        for p in py_lint_prefixes
    )
    assert not any(
        registry_mod._subcommand_matches_prefix(mismatched_sub, p)[0]
        for p in py_lint_prefixes
    )

    # Unwrapped target scoped under <d>/ matches <d> prefix; outside <d>/ does not
    dir_prefix = "uv --directory apps/align-worker run ruff check"
    assert registry_mod._subcommand_matches_prefix(
        ["ruff", "check", "apps/align-worker/src/mod.py"], dir_prefix
    )[0]
    assert not registry_mod._subcommand_matches_prefix(
        ["ruff", "check", "apps/other-worker/src/mod.py"], dir_prefix
    )[0]
    assert not registry_mod._subcommand_matches_prefix(["ruff", "check"], dir_prefix)[0]

    # 2. iOS mise exec -- manifest matches bare swiftlint/swiftformat via validate_tier_b
    ios_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "swiftformat --lint Packages/Core/Sources/Foo.swift && "
            "swiftlint lint --config quality/.swiftlint.yml --strict Packages/Core/Sources/Foo.swift",
        )
    ]
    assert (
        registry_mod.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_ios",
            [_FakeAllowedEntry("Packages/Core/Sources/Foo.swift")],
            ios_rows,
        )
        == []
    )
    assert registry_mod._subcommand_matches_prefix(
        [
            "swiftlint",
            "lint",
            "--config",
            "quality/.swiftlint.yml",
            "--strict",
            "Packages/Core/Sources/Foo.swift",
        ],
        "mise exec -- swiftlint lint --config quality/.swiftlint.yml --strict",
    )[0]

    # 3. Web {skills_dir} normalization & check_vanilla_js.py typecheck default via validate_tier_b
    assert (
        "check_vanilla_js.py"
        in registry_mod.BUILTIN_STACKS["web"].default_tier_b.typecheck_prefixes
    )
    web_tc_prefixes = adapter.descriptors["web"].default_tier_b.typecheck_prefixes
    assert any("$D3NEXUS_KIT/skills" in p for p in web_tc_prefixes)
    assert all("{skills_dir}" not in p for p in web_tc_prefixes)

    web_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            'python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview',
        )
    ]
    assert (
        registry_mod.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_web",
            [_FakeAllowedEntry("src/preview/app.js")],
            web_rows,
        )
        == []
    )

    # Relocated script path with required flags matches multi-token script prefix; missing flag fails
    script_prefix = next(p for p in web_tc_prefixes if "$D3NEXUS_KIT/skills" in p)
    assert registry_mod._subcommand_matches_prefix(
        [
            "python3",
            "/opt/relocated/scripts/check_vanilla_js.py",
            "--target-dir",
            "src/preview",
        ],
        script_prefix,
    )[0]
    assert not registry_mod._subcommand_matches_prefix(
        ["python3", "/opt/relocated/scripts/check_vanilla_js.py"],
        script_prefix,
    )[0]
    # Non-interpreter linter targeting a .py file must NOT match a script prefix
    assert not registry_mod._subcommand_matches_prefix(
        ["ruff", "check", "scripts/check_vanilla_js.py"],
        "check_vanilla_js.py",
    )[0]
    # Shell script (.sh) relocated path + required flag matching & npm --prefix agreement
    assert registry_mod._subcommand_matches_prefix(
        ["bash", "/custom/tools/check_arch.sh", "--strict", "--base-ref", "main"],
        "bash scripts/check_arch.sh --strict --base-ref {base_ref}",
    )[0]
    assert registry_mod._subcommand_matches_prefix(
        ["npm", "--prefix=apps/web", "run", "lint"],
        "npm --prefix apps/web run lint",
    )[0]
    assert not registry_mod._subcommand_matches_prefix(
        ["npm", "--prefix", "apps/other", "run", "lint"],
        "npm --prefix apps/web run lint",
    )[0]
    assert registry_mod._subcommand_matches_prefix(
        [
            "ruff",
            "check",
            "--config",
            "apps/align-worker/pyproject.toml",
            "--",
            "apps/align-worker/src/mod.py",
        ],
        "uv --directory=apps/align-worker run ruff check",
    )[0]


def _verify_slqr_fr_01_invalid_test_routing(
    bad_test_routing: Any,
    stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
) -> None:
    """[SLQR-FR-01] Provider manifest validators fail closed on invalid test_routing keys or path traversal globs."""
    for stack in ALL_STACKS:
        manifest = _minimal_manifest(stack)
        manifest["test_routing"] = bad_test_routing
        res = stack_validators[stack](manifest, "epic")
        assert res["status"] == "BLOCKED", f"{stack}: expected BLOCKED, got {res}"
        codes = {f["code"] for f in res["findings"]}
        assert "invalid_test_routing" in codes, f"{stack}: {res}"


def _verify_slqr_fr_01_invalid_package_floors(
    bad_package_floors: Any,
    stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
) -> None:
    """[SLQR-FR-01] Invalid coverage.package_floors paths fail closed with invalid_coverage_config."""
    manifest = _minimal_manifest("python")
    manifest["capabilities"]["coverage"]["package_floors"] = bad_package_floors
    res = stack_validators["python"](manifest, "epic")
    assert res["status"] == "BLOCKED", res
    assert any(f["code"] == "invalid_coverage_config" for f in res["findings"])


class TestSlqrRegistryAndSchemas_Integration:
    """Tier C integration suite providing integration provenance for SLQR Task 01 scenarios."""

    def test_slqr_hp_01_provider_schemas_and_validators_accept_additive_contracts(
        self,
        stack_schemas: dict[str, dict[str, Any]],
        stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
        scaffolded_six_stack_manifests: dict[str, dict[str, Any]],
        provider_common_mod: Any,
    ) -> None:
        """[SLQR-HP-01] Provider schemas and runtime validators accept additive test_routing, package_floors, architecture, and cache capabilities."""
        test_slqr_hp_01_provider_schemas_and_validators_accept_additive_contracts(
            stack_schemas,
            stack_validators,
            scaffolded_six_stack_manifests,
            provider_common_mod,
        )

    def test_slqr_ec_01_registry_wrappers_mise_and_relocated_scripts(
        self,
        tmp_path: Path,
        registry_mod: Any,
    ) -> None:
        """[SLQR-EC-01] Registry prefix matcher and TierBContractAdapter unwrap monorepo directory flags, mise exec prefixes, and relocated script paths while rejecting mismatched directories."""
        _verify_slqr_ec_01_registry_wrappers_mise_and_relocated_scripts(
            tmp_path, registry_mod
        )

    @pytest.mark.parametrize(
        "bad_test_routing",
        [
            pytest.param("not-a-dict", id="non_dict_string"),
            pytest.param(["tests/**"], id="non_dict_list"),
            pytest.param({"rogue_key": ["tests/**"]}, id="unknown_key"),
            pytest.param({"canonical_test_globs": []}, id="empty_glob_list"),
            pytest.param({"canonical_test_globs": "tests/**"}, id="non_list_value"),
            pytest.param(
                {"canonical_test_globs": ["../outside/test_*.py"]},
                id="parent_traversal",
            ),
            pytest.param(
                {"forbidden_test_globs": ["tests/../escape/test_*.py"]},
                id="nested_traversal",
            ),
            pytest.param(
                {"paired_source_globs": ["/abs/src/**/*.py"]},
                id="absolute_glob_path",
            ),
            pytest.param(
                {"lcov_unit_test_globs": [""]},
                id="empty_glob_string",
            ),
            pytest.param(
                {"cache_bust_extensions": []},
                id="empty_extensions_list",
            ),
            pytest.param(
                {"cache_bust_extensions": ["js"]},
                id="extension_missing_dot",
            ),
            pytest.param(
                {"cache_bust_extensions": [".JS"]},
                id="extension_uppercase",
            ),
        ],
    )
    def test_slqr_fr_01_validators_fail_closed_on_invalid_test_routing(
        self,
        bad_test_routing: Any,
        stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
    ) -> None:
        """[SLQR-FR-01] Provider manifest validators fail closed on invalid test_routing keys or path traversal globs."""
        _verify_slqr_fr_01_invalid_test_routing(bad_test_routing, stack_validators)

    @pytest.mark.parametrize(
        "bad_package_floors",
        [
            pytest.param("../outside/floors.json", id="traversal"),
            pytest.param("/etc/floors.json", id="absolute"),
            pytest.param("", id="empty"),
            pytest.param(42, id="non_string"),
        ],
    )
    def test_slqr_fr_01_invalid_package_floors_fails_closed(
        self,
        bad_package_floors: Any,
        stack_validators: dict[str, Callable[[dict[str, Any], str], dict[str, Any]]],
    ) -> None:
        """[SLQR-FR-01] Invalid coverage.package_floors paths fail closed with invalid_coverage_config."""
        _verify_slqr_fr_01_invalid_package_floors(bad_package_floors, stack_validators)


@pytest.mark.parametrize(
    ("raw_tokens", "expected"),
    [
        (
            ["uv", "--directory", "apps/worker", "run", "ruff", "check", "."],
            ["ruff", "check", "."],
        ),
        (
            ["uv", "--project", "apps/worker", "--frozen", "--quiet", "run", "mypy"],
            ["mypy"],
        ),
        (
            ["uv", "-q", "--offline", "--no-sync", "run", "pytest"],
            ["pytest"],
        ),
        (
            ["mise", "exec", "--", "swiftlint", "lint", "--strict"],
            ["swiftlint", "lint", "--strict"],
        ),
        (
            ["mise", "exec", "swift@6.0", "ruby@3.3", "--", "swiftformat", "--lint"],
            ["swiftformat", "--lint"],
        ),
        (
            ["mise", "x", "node@22", "--", "eslint", "."],
            ["eslint", "."],
        ),
        (
            ["npm", "--prefix", "apps/web", "exec", "--", "tsc", "--noEmit"],
            ["tsc", "--noEmit"],
        ),
        (
            ["npm", "exec", "eslint", "."],
            ["eslint", "."],
        ),
        (
            ["uv", "--directory=apps/worker", "run", "--", "ruff", "check", "."],
            ["ruff", "check", "."],
        ),
        (
            ["npm", "--prefix=apps/web", "exec", "--", "eslint", "."],
            ["eslint", "."],
        ),
        (
            ["npm", "run", "lint"],
            ["npm", "run", "lint"],
        ),
    ],
)
def test_strip_command_wrappers_variants(
    raw_tokens: list[str],
    expected: list[str],
    registry_mod: Any,
) -> None:
    """Verify _strip_command_wrappers unwraps uv/mise/npm exec while preserving npm run."""
    assert registry_mod._strip_command_wrappers(raw_tokens) == expected


@pytest.mark.parametrize(
    ("cap_cmd", "expected_prefix"),
    [
        (
            ["uv", "--directory", "apps/align-worker", "run", "ruff", "check", "."],
            "uv --directory apps/align-worker run ruff check",
        ),
        (
            ["uv", "run", "mypy", "--strict", "src", "tests"],
            "uv run mypy --strict",
        ),
        (
            [
                "python3",
                "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                "--base-ref",
                "{base_ref}",
                "--target-dir",
                "src",
            ],
            'python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src',
        ),
        (
            [
                "python3",
                "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py",
                "--base-ref={base_ref}",
                "--target-dir",
                "src/preview",
            ],
            'python3 "$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py" --target-dir src/preview',
        ),
    ],
)
def test_cap_command_str_normalization(
    cap_cmd: list[str],
    expected_prefix: str,
    registry_mod: Any,
) -> None:
    """Verify _cap_command_str normalizes {skills_dir}, strips --base-ref {base_ref}, and strips trailing repo targets."""
    result = registry_mod._cap_command_str({"check": cap_cmd}, "check")
    assert result == (expected_prefix,)


def test_stack_descriptor_loads_test_routing_policy(
    tmp_path: Path,
    registry_mod: Any,
) -> None:
    """Verify StackDescriptor exposes optional TestRoutingPolicy populated from manifests."""
    default_desc = registry_mod.BUILTIN_STACKS["python"]
    assert default_desc.test_routing == registry_mod.TestRoutingPolicy()

    _write_json(
        tmp_path / ".agents" / "quality" / "web-quality.json",
        {
            "schema_version": 1,
            "test_routing": {
                "canonical_test_globs": ["tests/js/*.test.mjs"],
                "forbidden_test_globs": ["src/**/*.test.js"],
                "paired_source_globs": ["src/preview/static/*.js"],
                "lcov_unit_test_globs": ["tests/js/*.test.mjs"],
                "cache_bust_extensions": [".js", ".css"],
            },
            "capabilities": {
                "lint": ["eslint", "."],
                "test": ["vitest", "run"],
            },
            "profiles": {"pr": ["lint", "test"], "epic": ["lint", "test"]},
        },
    )
    adapter = registry_mod.TierBContractAdapter.from_repo(tmp_path)
    routing = adapter.descriptors["web"].test_routing
    assert routing == registry_mod.TestRoutingPolicy(
        canonical_test_globs=("tests/js/*.test.mjs",),
        forbidden_test_globs=("src/**/*.test.js",),
        paired_source_globs=("src/preview/static/*.js",),
        lcov_unit_test_globs=("tests/js/*.test.mjs",),
        cache_bust_extensions=(".js", ".css"),
    )


def test_registry_stdlib_and_import_isolation() -> None:
    """Verify _stack_lifecycle_registry.py uses Python 3 stdlib only with zero circular imports."""
    reg_path = IMPL_SCRIPTS_DIR / "_stack_lifecycle_registry.py"
    tree = ast.parse(reg_path.read_text(encoding="utf-8"), filename=str(reg_path))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "check_task_contract" not in imported
    assert "manage_worker_pool" not in imported
    non_stdlib = sorted(mod for mod in imported if mod not in sys.stdlib_module_names)
    assert non_stdlib == [], (
        f"Non-stdlib imports in _stack_lifecycle_registry.py: {non_stdlib}"
    )
