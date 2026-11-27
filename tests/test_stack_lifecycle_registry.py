"""Unit and integration tests for _stack_lifecycle_registry.py.

Covers BDD Scenarios:
- PLQ-HP-01: Registry resolves all 6 built-in stacks and custom manifest overrides
- PLQ-EC-01: Untouched stack manifests incur zero Tier B checks
- PLQ-EC-02: Flutter and Python (new) files require explicit format coverage before git add
- PLQ-AR-01: Suffix-scoped TriageSurfaceRegistry isolates stack rules while preserving language-neutral baselines
- PLQ-FR-01: Path traversal in pool_mounts or malformed regex in triage_surfaces is rejected safely
"""

from __future__ import annotations

import importlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


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


def _load_registry() -> Any:
    """Import _stack_lifecycle_registry or fail deterministically during TDD RED."""
    try:
        return importlib.import_module("_stack_lifecycle_registry")
    except ImportError as exc:
        pytest.fail(f"_stack_lifecycle_registry module is not implemented yet: {exc}")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_git_repo(repo_dir: Path, gitignore_text: str = "") -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "init", "-q", "-b", "main")
    _git(repo_dir, "config", "user.name", "Test User")
    _git(repo_dir, "config", "user.email", "test@example.com")
    if gitignore_text:
        (repo_dir / ".gitignore").write_text(gitignore_text, encoding="utf-8")
    (repo_dir / "README.md").write_text("# Demo\n", encoding="utf-8")
    _git(repo_dir, "add", ".")
    _git(repo_dir, "commit", "-q", "-m", "Initial commit")


def _write_six_stack_manifests(repo_root: Path) -> None:
    quality_dir = repo_root / ".agents" / "quality"
    manifests: dict[str, dict[str, Any]] = {
        "python-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "format": ["ruff", "format", "--check", "."],
                "lint": ["ruff", "check", "."],
                "type_check": ["mypy", "src"],
                "test": ["python3", "-m", "pytest"],
            },
            "profiles": {
                "pr": ["lint", "test"],
                "epic": ["format", "lint", "type_check", "test"],
            },
        },
        "flutter-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "format": [
                    "dart",
                    "format",
                    "--output=none",
                    "--set-exit-if-changed",
                    ".",
                ],
                "analyze": ["dart", "analyze"],
                "boundaries": ["melos", "run", "boundaries"],
                "test": ["flutter", "test"],
            },
            "profiles": {
                "pr": ["format", "analyze", "test"],
                "epic": ["format", "analyze", "boundaries", "test"],
            },
        },
        "rust-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "format": ["cargo", "fmt", "--all", "--", "--check"],
                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
                "architecture": ["cargo", "xtask", "check-arch"],
                "test": ["cargo", "test"],
            },
            "profiles": {
                "pr": ["format", "clippy", "test"],
                "epic": ["format", "clippy", "architecture", "test"],
            },
        },
        "web-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "lint": ["eslint", "."],
                "type_check": ["tsc", "--noEmit"],
                "test": ["vitest", "run"],
            },
            "profiles": {
                "pr": ["lint", "type_check", "test"],
                "epic": ["lint", "type_check", "test"],
            },
        },
        "android-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "format": ["./gradlew", "spotlessCheck"],
                "lint": ["./gradlew", "detekt"],
                "architecture": ["./gradlew", ":konsist-test:test"],
                "test": ["./gradlew", "testDebugUnitTest"],
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "architecture", "test"],
            },
        },
        "ios-quality.json": {
            "schema_version": 1,
            "capabilities": {
                "format": ["swiftformat", "--lint", "."],
                "lint": ["swiftlint", "lint", "--strict"],
                "architecture": ["swift", "test", "--filter", "ArchTests"],
                "test": ["swift", "test"],
            },
            "profiles": {
                "pr": ["format", "lint", "test"],
                "epic": ["format", "lint", "architecture", "test"],
            },
        },
    }
    for filename, payload in manifests.items():
        _write_json(quality_dir / filename, payload)


def test_plq_hp_01_registry_resolves_six_stacks_and_custom_override(
    tmp_path: Path,
) -> None:
    """[PLQ-HP-01] Registry resolves all 6 built-in stacks and custom manifest overrides."""
    reg = _load_registry()

    _write_six_stack_manifests(tmp_path)
    _write_json(
        tmp_path / ".agents" / "quality" / "go-quality.json",
        {
            "schema_version": 1,
            "extensions": [".go"],
            "task_tier_b": {
                "format_prefixes": ["gofmt -l"],
                "lint_prefixes": ["golangci-lint run"],
            },
            "triage_surfaces": {
                "signature": [r"^func\s+[A-Z]"],
                "concurrency": [r"\bgo\s+func\b"],
            },
        },
    )

    assert reg.TierBContractAdapter.has_provider_manifests(tmp_path) is True

    expected_extensions: dict[str, tuple[str, ...]] = {
        "python": (".py",),
        "flutter": (".dart",),
        "rust": (".rs",),
        "web": (".ts", ".tsx", ".js", ".mjs", ".astro"),
        "android": (".kt", ".kts"),
        "ios": (".swift",),
    }

    assert set(reg.BUILTIN_STACKS.keys()) == set(expected_extensions.keys())
    for stack_id, exts in expected_extensions.items():
        descriptor = reg.BUILTIN_STACKS[stack_id]
        assert descriptor.stack_id == stack_id
        assert descriptor.extensions == exts
        assert isinstance(descriptor.default_tier_b, reg.TierBPolicy)
        assert isinstance(descriptor.default_surfaces, reg.SurfaceRuleSet)
        assert isinstance(descriptor.tier_c_policy, reg.TierCPolicy)

    # Initialize all four open contracts from repo root
    tier_b = reg.TierBContractAdapter.from_repo(tmp_path)
    pool_strategy = reg.PoolWorkspaceStrategy.from_repo(tmp_path)
    triage_registry = reg.TriageSurfaceRegistry.from_repo(tmp_path)
    tier_c = reg.TierCTaxonomy.from_repo(tmp_path)

    assert set(expected_extensions.keys()).issubset(set(tier_b.descriptors.keys()))
    assert "go" in tier_b.descriptors
    assert tier_b.descriptors["go"].extensions == (".go",)
    assert tier_b.descriptors["go"].default_tier_b.format_prefixes == ("gofmt -l",)
    assert len(pool_strategy.resolve_mounts(tmp_path)) > 0
    assert tier_c is not None

    # Custom 7th stack (.go) activates without modifying Python kit code
    active_go = reg.TierBContractAdapter.resolve_active_stacks(
        tmp_path, ["cmd/server/main.go"]
    )
    assert [d.stack_id for d in active_go] == ["go"]

    missing_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_go",
        [_FakeAllowedEntry("cmd/server/main.go")],
        [_FakeRow("V4", "TIER-B", "echo ok")],
    )
    assert len(missing_problems) == 2
    assert any("gofmt -l" in msg for _, msg in missing_problems)
    assert any("golangci-lint run" in msg for _, msg in missing_problems)

    passing_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_go",
        [_FakeAllowedEntry("cmd/server/main.go")],
        [
            _FakeRow(
                "V4", "TIER-B", "gofmt -l cmd/server/main.go && golangci-lint run ./..."
            )
        ],
    )
    assert passing_problems == []

    # Custom stack triage surface rules also load for .go suffix
    assert triage_registry.rules_for_path("cmd/server/main.go") is not None
    assert "PUBLIC_SIGNATURE_CHANGED" in triage_registry.match_line(
        "cmd/server/main.go", "+", "func ServeHTTP(w ResponseWriter) {"
    )
    assert "CONCURRENCY_OR_LOCKING_CHANGED" in triage_registry.match_line(
        "cmd/server/main.go", "+", "    go func() { work() }()"
    )

    # All 6 built-in stacks resolve via allowed_paths
    all_paths = [
        "src/app.py",
        "lib/main.dart",
        "crates/core/src/lib.rs",
        "apps/web/src/app.ts",
        "feature/wallet/Main.kt",
        "Sources/Wallet.swift",
    ]
    resolved_ids = {
        d.stack_id
        for d in reg.TierBContractAdapter.resolve_active_stacks(tmp_path, all_paths)
    }
    assert resolved_ids == set(expected_extensions.keys())


def _verify_plq_ec_01_untouched_stack_manifests_incur_zero_tier_b_checks(
    tmp_path: Path,
) -> None:
    """[PLQ-EC-01] Untouched stack manifests incur zero Tier B checks."""
    reg = _load_registry()
    _write_six_stack_manifests(tmp_path)

    allowed = [_FakeAllowedEntry("crates/core/src/calc.rs")]
    active = reg.TierBContractAdapter.resolve_active_stacks(
        tmp_path, ["crates/core/src/calc.rs"]
    )
    assert [d.stack_id for d in active] == ["rust"]

    rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "cargo fmt --check && cargo clippy --all-targets -- -D warnings",
        )
    ]
    problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path, "task_rust", allowed, rows
    )
    assert problems == []

    # Even when Rust row is missing, zero flutter or python problems are emitted
    bad_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_rust",
        allowed,
        [_FakeRow("V4", "TIER-B", "cargo test")],
    )
    assert bad_problems
    combined = "\n".join(msg for _, msg in bad_problems).lower()
    assert "rust" in combined
    assert "flutter" not in combined
    assert "dart" not in combined
    assert "python" not in combined
    assert "ruff" not in combined
    assert "mypy" not in combined


def _verify_plq_ec_02_flutter_new_files_require_explicit_format_coverage(
    tmp_path: Path,
) -> None:
    """[PLQ-EC-02] Flutter (new) files require explicit format coverage before git add."""
    reg = _load_registry()
    _write_json(
        tmp_path / ".agents" / "quality" / "flutter-quality.json",
        {
            "schema_version": 1,
            "capabilities": {
                "format": [
                    "dart",
                    "format",
                    "--output=none",
                    "--set-exit-if-changed",
                    ".",
                ],
                "analyze": ["dart", "analyze"],
                "test": ["flutter", "test"],
            },
            "profiles": {
                "pr": ["format", "analyze", "test"],
                "epic": ["format", "analyze", "test"],
            },
        },
    )

    allowed = [
        _FakeAllowedEntry("lib/new_widget.dart", new=True),
        _FakeAllowedEntry("lib/existing.dart", new=False),
    ]

    # Omitting lib/new_widget.dart from explicit dart format args must fail naming it
    missing_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "dart format --output=none --set-exit-if-changed lib/existing.dart && dart analyze lib/",
        )
    ]
    problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path, "task_flutter", allowed, missing_rows
    )
    assert len(problems) == 1
    where, message = problems[0]
    assert where == "task_flutter:Verification"
    assert "lib/new_widget.dart" in message

    # Naming both files passes
    explicit_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "dart format --output=none --set-exit-if-changed lib/existing.dart lib/new_widget.dart && dart analyze lib/",
        )
    ]
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path, "task_flutter", allowed, explicit_rows
        )
        == []
    )

    # Workspace-wide directory coverage (`.`) also covers both files including (new)
    workspace_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "dart format --output=none --set-exit-if-changed . && flutter analyze",
        )
    ]
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path, "task_flutter", allowed, workspace_rows
        )
        == []
    )

    # Also ensure string-encoded "(new)" entries are parsed properly
    string_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_flutter",
        ["lib/new_widget.dart (new)", "lib/existing.dart"],
        missing_rows,
    )
    assert len(string_problems) == 1
    assert "lib/new_widget.dart" in string_problems[0][1]

    # Conditional `||` or piped `|` tails must never satisfy Tier B gates
    conditional_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "dart format --output=none --set-exit-if-changed . || dart analyze",
        )
    ]
    cond_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path, "task_flutter", allowed, conditional_rows
    )
    assert len(cond_problems) == 1
    assert (
        "lint" in cond_problems[0][1].lower()
        or "analyze" in cond_problems[0][1].lower()
    )


def _verify_plq_ar_01_suffix_scoped_triage_surface_registry_and_baselines() -> None:
    """[PLQ-AR-01] Suffix-scoped TriageSurfaceRegistry isolates stack rules while preserving language-neutral baselines."""
    reg = _load_registry()
    registry = reg.TriageSurfaceRegistry.default()

    # Cross-language isolation: zero triggers must fire on foreign-stack strings
    assert registry.match_line("lib/service.dart", "+", "unsafe fn run() {}") == set()
    assert (
        registry.match_line("lib/service.dart", "+", "tokio::spawn(async {});") == set()
    )
    assert (
        registry.match_line("crates/core/src/lib.rs", "+", 'let ch = "MethodChannel";')
        == set()
    )
    assert (
        registry.match_line("crates/core/src/lib.rs", "+", 'let db = "DriftDatabase";')
        == set()
    )
    assert registry.match_line("feature/wallet/Helper.kt", "+", "// XCTSkip") == set()
    assert registry.match_line("feature/wallet/Helper.kt", "+", "// Codable") == set()
    assert (
        registry.match_line("feature/wallet/Helper.kt", "+", "private fun helper() {}")
        == set()
    )
    assert (
        registry.match_line(
            "feature/wallet/Helper.kt", "+", "protected suspend fun inner() {}"
        )
        == set()
    )

    # Language-neutral baselines fire regardless of suffix (including unknown .sql)
    assert registry.rules_for_path("migrations/001_add_role.sql") is None
    assert registry.match_line(
        "migrations/001_add_role.sql", "+", "ALTER TABLE users ADD COLUMN role TEXT;"
    ) == {"DB_OR_PERSISTENCE_CHANGED"}
    assert registry.match_line("lib/auth_service.dart", "+", "class AuthService {") == {
        "PUBLIC_SIGNATURE_CHANGED"
    }
    assert registry.match_line(
        "scripts/worker.unknown", "+", "lock = Semaphore(4)"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}

    # Native-stack edits fire their exact trigger codes
    # Dart
    assert registry.match_line(
        "lib/bridge.dart", "+", "final ch = MethodChannel('wallet');"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line(
        "lib/api.dart", "+", "@RestApi(baseUrl: 'https://api')"
    ) == {"API_ROUTE_OR_SCHEMA_CHANGED"}
    assert registry.match_line(
        "lib/db.dart", "+", "class AppDb extends DriftDatabase {"
    ) == {
        "PUBLIC_SIGNATURE_CHANGED",
        "DB_OR_PERSISTENCE_CHANGED",
    }
    assert registry.match_line(
        "lib/worker.dart", "+", "Isolate.spawn(entry, msg);"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}
    assert registry.match_test_line(
        "test/bridge_test.dart", "+", "test('a', () {}, skip: true);"
    ) == (False, True)
    assert registry.match_test_line(
        "test/bridge_test.dart", "-", "expect(result, equals(42));"
    ) == (True, False)

    # Rust
    assert registry.match_line(
        "crates/core/src/api.rs", "+", "pub async fn transfer() -> Result<()> {"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line(
        "crates/core/src/ffi.rs", "+", "unsafe { ptr.read() }"
    ) == {"API_ROUTE_OR_SCHEMA_CHANGED"}
    assert registry.match_line(
        "crates/core/src/repo.rs", "+", 'sqlx::query!("SELECT id FROM users")'
    ) == {"DB_OR_PERSISTENCE_CHANGED"}
    assert registry.match_line(
        "crates/core/src/jobs.rs", "+", "tokio::spawn(async move {});"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}
    assert registry.match_test_line(
        "crates/core/tests/api_test.rs", "+", "#[ignore]"
    ) == (False, True)
    assert registry.match_test_line(
        "crates/core/tests/api_test.rs", "-", "assert_eq!(got, want);"
    ) == (True, False)

    # TypeScript / Web
    assert registry.match_line(
        "apps/web/src/api.ts", "+", "export async function fetchUser() {"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line(
        "apps/web/src/client.ts", "+", "const res = await fetch('/api/v1/users');"
    ) == {"API_ROUTE_OR_SCHEMA_CHANGED"}
    assert registry.match_line(
        "apps/web/src/store.ts", "+", "localStorage.setItem('token', val);"
    ) == {"DB_OR_PERSISTENCE_CHANGED"}
    assert registry.match_line(
        "apps/web/src/worker.ts", "+", "const w = new Worker('job.js');"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}
    assert registry.match_test_line(
        "apps/web/src/api.spec.ts", "+", "it.skip('flaky', () => {});"
    ) == (False, True)

    # Kotlin / Android
    assert registry.match_line(
        "feature/wallet/UseCase.kt", "+", "public suspend fun execute() {"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line("feature/wallet/Api.kt", "+", '@GET("/v1/balance")') == {
        "API_ROUTE_OR_SCHEMA_CHANGED"
    }
    assert registry.match_line(
        "feature/wallet/Db.kt", "+", "abstract val db: RoomDatabase"
    ) == {"DB_OR_PERSISTENCE_CHANGED"}
    assert registry.match_line(
        "feature/wallet/Repo.kt", "+", "withContext(Dispatchers.IO) {}"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}
    assert registry.match_test_line(
        "feature/wallet/UseCaseTest.kt", "+", "@Ignore"
    ) == (False, True)
    assert registry.match_line("feature/wallet/UseCaseTest.kt", "+", "@Ignore") == {
        "TEST_ASSERTION_WEAKENED"
    }

    # Swift / iOS
    assert registry.match_line(
        "Sources/Wallet.swift", "+", "public func submitPayment() {}"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line(
        "Sources/Model.swift", "+", "struct Payload: Codable {}"
    ) == {"API_ROUTE_OR_SCHEMA_CHANGED"}
    assert registry.match_line(
        "Sources/Store.swift", "+", "@Model final class Entry {}"
    ) == {"DB_OR_PERSISTENCE_CHANGED"}
    assert registry.match_line("Sources/Store.swift", "+", "final class Entry {}") == {
        "PUBLIC_SIGNATURE_CHANGED"
    }
    assert registry.match_line("Sources/Cache.swift", "+", "actor TokenCache {}") == {
        "CONCURRENCY_OR_LOCKING_CHANGED"
    }
    assert registry.match_test_line(
        "Tests/WalletTests.swift", "+", 'throw XCTSkip("skip")'
    ) == (False, True)
    assert registry.match_line(
        "Tests/WalletTests.swift", "+", 'throw XCTSkip("skip")'
    ) == {"TEST_ASSERTION_WEAKENED"}

    # Python
    assert registry.match_line(
        "src/service.py", "+", "async def handle_event(x: int) -> None:"
    ) == {"PUBLIC_SIGNATURE_CHANGED"}
    assert registry.match_line("src/app.py", "+", "app = FastAPI()") == {
        "API_ROUTE_OR_SCHEMA_CHANGED"
    }
    assert registry.match_line("src/routes.py", "+", '@router.post("/items")') == {
        "API_ROUTE_OR_SCHEMA_CHANGED"
    }
    assert registry.match_line("src/db.py", "+", "session.commit()") == {
        "DB_OR_PERSISTENCE_CHANGED"
    }
    assert registry.match_line(
        "src/lock.py", "+", "fcntl.flock(fd, fcntl.LOCK_EX)"
    ) == {"CONCURRENCY_OR_LOCKING_CHANGED"}
    assert registry.match_test_line(
        "tests/test_service.py", "+", "@pytest.mark.skip(reason='wip')"
    ) == (False, True)
    assert registry.match_line(
        "tests/test_service.py", "+", "@pytest.mark.skip(reason='wip')"
    ) == {"TEST_ASSERTION_WEAKENED"}

    # Polyglot is_test_file classification
    assert (
        reg.TriageSurfaceRegistry.is_test_file("packages/core/test/auth_test.dart")
        is True
    )
    assert (
        reg.TriageSurfaceRegistry.is_test_file("crates/core/src/calc_test.rs") is True
    )
    assert reg.TriageSurfaceRegistry.is_test_file("apps/web/src/app.spec.ts") is True
    assert (
        reg.TriageSurfaceRegistry.is_test_file("feature/wallet/WalletTest.kt") is True
    )
    assert reg.TriageSurfaceRegistry.is_test_file("Tests/WalletTests.swift") is True
    assert (
        reg.TriageSurfaceRegistry.is_test_file("app/src/androidTest/java/Main.kt")
        is True
    )
    assert reg.TriageSurfaceRegistry.is_test_file("src/contest.py") is False
    assert reg.TriageSurfaceRegistry.is_test_file("lib/auth.dart") is False


def _verify_plq_fr_01_path_traversal_and_malformed_regex_rejected_safely(
    tmp_path: Path,
) -> None:
    """[PLQ-FR-01] Path traversal in pool_mounts or malformed regex in triage_surfaces is rejected safely."""
    reg = _load_registry()

    outside_secret = tmp_path / "outside_secret"
    outside_secret.mkdir()
    (outside_secret / "creds.txt").write_text("TOP_SECRET\n", encoding="utf-8")

    repo_root = tmp_path / "repo"
    slot_root = tmp_path / "slot_1"
    _init_git_repo(repo_root, gitignore_text=".dart_tool/\nsecureFiles/\n")
    _init_git_repo(slot_root, gitignore_text=".dart_tool/\nsecureFiles/\n")

    _write_json(
        repo_root / ".agents" / "quality" / "check_quality.json",
        {
            "schema_version": 1,
            "pool_mounts": [
                {"path": "../outside_secret", "mode": "cow_copy"},
                {"path": "/etc/passwd", "mode": "symlink"},
                {"path": "valid_cache", "mode": "hardlink"},
            ],
        },
    )
    _write_json(
        repo_root / ".agents" / "quality" / "flutter-quality.json",
        {
            "schema_version": 1,
            "triage_surfaces": {
                "signature": ["[unclosed-regex", r"CustomBridgeChannel"],
                "unknown_cat": ["foo"],
            },
        },
    )

    # PoolWorkspaceStrategy rejects traversal/absolute/invalid-mode without accessing outside_secret
    strategy = reg.PoolWorkspaceStrategy.from_repo(repo_root)
    resolved_paths = [rule.path for rule in strategy.resolve_mounts(repo_root)]
    assert "../outside_secret" not in resolved_paths
    assert "/etc/passwd" not in resolved_paths
    assert "valid_cache" not in resolved_paths
    assert any("../outside_secret" in err for err in strategy.validation_errors)
    assert any("/etc/passwd" in err for err in strategy.validation_errors)
    assert any("hardlink" in err for err in strategy.validation_errors)

    materialized = reg.PoolWorkspaceStrategy.materialize_mounts(repo_root, slot_root)
    assert "../outside_secret" not in materialized["cow_copy"]
    assert not (slot_root / "outside_secret").exists()

    # TriageSurfaceRegistry skips malformed regex without raising re.error while keeping valid rules
    triage = reg.TriageSurfaceRegistry.from_repo(repo_root)
    assert any("[unclosed-regex" in err for err in triage.validation_errors)
    assert triage.match_line("lib/x.dart", "+", "final b = CustomBridgeChannel();") == {
        "PUBLIC_SIGNATURE_CHANGED"
    }
    assert triage.match_line("lib/x.dart", "+", "final c = MethodChannel('a');") == {
        "PUBLIC_SIGNATURE_CHANGED"
    }

    # Non-object triage_surfaces (array instead of category-keyed dict) is also handled safely
    _write_json(
        repo_root / ".agents" / "quality" / "rust-quality.json",
        {
            "schema_version": 1,
            "triage_surfaces": ["unsafe\\b"],
        },
    )
    triage_non_obj = reg.TriageSurfaceRegistry.from_repo(repo_root)
    assert any("triage_surfaces" in err for err in triage_non_obj.validation_errors)


def test_pool_workspace_strategy_symlink_cow_copy_and_tracked_xcconfig_protection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify symlink vs cow_copy materialization, tracked file protection, exclusions, and APFS fallback."""
    reg = _load_registry()

    gitignore = "\n".join(
        [
            "target/",
            "node_modules/",
            ".dart_tool/",
            "packages/*/.dart_tool/",
            "secureFiles/",
            "android/local.properties",
            "ios/Flutter/Secret.xcconfig",
            "custom_secrets/",
            "",
        ]
    )
    main_wt = tmp_path / "main_wt"
    slot_wt = tmp_path / "slot_wt"
    _init_git_repo(main_wt, gitignore_text=gitignore)

    # Create a git-tracked xcconfig that MUST NOT be copied or excluded
    tracked_xcconfig = main_wt / "ios" / "Flutter" / "Debug.xcconfig"
    tracked_xcconfig.parent.mkdir(parents=True, exist_ok=True)
    tracked_xcconfig.write_text('#include "Generated.xcconfig"\n', encoding="utf-8")
    _git(main_wt, "add", "ios/Flutter/Debug.xcconfig")
    _git(main_wt, "commit", "-q", "-m", "Track Debug.xcconfig")

    # Create a second worktree as slot
    _git(main_wt, "worktree", "add", "-q", str(slot_wt), "-b", "slot-1", "main")

    # Populate untracked+ignored mounts in main_wt
    (main_wt / "target").mkdir()
    (main_wt / "target" / "cache.bin").write_text("rust", encoding="utf-8")
    (main_wt / ".dart_tool").mkdir()
    (main_wt / ".dart_tool" / "package_config.json").write_text("{}", encoding="utf-8")
    (main_wt / "packages" / "core" / ".dart_tool").mkdir(parents=True)
    (main_wt / "packages" / "core" / ".dart_tool" / "pkg.json").write_text(
        "{}", encoding="utf-8"
    )
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "dev.json").write_text('{"k":"v"}', encoding="utf-8")
    (main_wt / "android").mkdir(exist_ok=True)
    (main_wt / "android" / "local.properties").write_text(
        "sdk.dir=/sdk\n", encoding="utf-8"
    )
    (main_wt / "ios" / "Flutter" / "Secret.xcconfig").write_text(
        "SECRET=1\n", encoding="utf-8"
    )
    (main_wt / "custom_secrets").mkdir()
    (main_wt / "custom_secrets" / "api.key").write_text("key", encoding="utf-8")

    _write_json(
        main_wt / ".agents" / "quality" / "check_quality.json",
        {
            "schema_version": 1,
            "pool_mounts": [{"path": "custom_secrets", "mode": "cow_copy"}],
        },
    )

    # Simulate cp -c -R failure to verify shutil fallback works cleanly
    real_run = subprocess.run

    def fake_run(
        cmd: Any, *args: Any, **kwargs: Any
    ) -> subprocess.CompletedProcess[Any]:
        if isinstance(cmd, list) and cmd[:3] == ["cp", "-c", "-R"]:
            return subprocess.CompletedProcess(cmd, 1, b"", b"cp: -c not supported")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(reg.subprocess, "run", fake_run)

    materialized = reg.PoolWorkspaceStrategy.materialize_mounts(main_wt, slot_wt)
    assert "target" in materialized["symlink"]
    assert (slot_wt / "target").is_symlink()

    for expected_cow in (
        ".dart_tool",
        "packages/core/.dart_tool",
        "secureFiles",
        "android/local.properties",
        "ios/Flutter/Secret.xcconfig",
        "custom_secrets",
    ):
        assert expected_cow in materialized["cow_copy"]
        dest = slot_wt / expected_cow
        assert dest.exists()
        assert not dest.is_symlink()

    # Tracked ios/Flutter/Debug.xcconfig is NEVER treated as cow_copy or excluded
    assert "ios/Flutter/Debug.xcconfig" not in materialized["cow_copy"]

    excluded = reg.PoolWorkspaceStrategy.get_excluded_relpaths(main_wt, slot_wt)
    assert "target" in excluded
    assert ".dart_tool" in excluded
    assert "packages/core/.dart_tool" in excluded
    assert "secureFiles" in excluded
    assert "android/local.properties" in excluded
    assert "ios/Flutter/Secret.xcconfig" in excluded
    assert "custom_secrets" in excluded
    assert "ios/Flutter/Debug.xcconfig" not in excluded


def test_tier_b_boundary_triggers_for_flutter_rust_android_ios(tmp_path: Path) -> None:
    """Conditional boundary checks activate only on domain or manifest edits across stacks."""
    reg = _load_registry()
    _write_six_stack_manifests(tmp_path)

    # Flutter domain edit requires boundary check; presentation edit does not
    flutter_base_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "dart format --output=none --set-exit-if-changed . && dart analyze",
        )
    ]
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_fl",
            [_FakeAllowedEntry("packages/core/lib/ui/btn.dart")],
            flutter_base_rows,
        )
        == []
    )
    fl_domain_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_fl",
        [_FakeAllowedEntry("packages/core/lib/domain/entity.dart")],
        flutter_base_rows,
    )
    assert len(fl_domain_problems) == 1
    assert "boundary" in fl_domain_problems[0][1].lower()

    # Rust Cargo.toml edit activates rust and requires boundary check
    rust_base_rows = [
        _FakeRow("V4", "TIER-B", "cargo fmt --check && cargo clippy -D warnings")
    ]
    rs_boundary_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_rs",
        [_FakeAllowedEntry("crates/domain/Cargo.toml")],
        rust_base_rows,
    )
    assert len(rs_boundary_problems) == 1
    assert "boundary" in rs_boundary_problems[0][1].lower()

    # Android domain edit requires konsist/apiCheck boundary check
    android_base_rows = [
        _FakeRow(
            "V4",
            "TIER-B",
            "./gradlew :feature:wallet:spotlessCheck :feature:wallet:detekt",
        )
    ]
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_and",
            [_FakeAllowedEntry("feature/wallet/ui/Screen.kt")],
            android_base_rows,
        )
        == []
    )
    and_domain_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_and",
        [_FakeAllowedEntry("feature/wallet/domain/UseCase.kt")],
        android_base_rows,
    )
    assert len(and_domain_problems) == 1
    assert "boundary" in and_domain_problems[0][1].lower()

    # iOS Package.swift edit requires ArchTests/boundaries check
    ios_base_rows = [
        _FakeRow(
            "V4", "TIER-B", "swiftformat --lint Sources/ && swiftlint lint --strict"
        )
    ]
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_ios",
            [_FakeAllowedEntry("Sources/UI/View.swift")],
            ios_base_rows,
        )
        == []
    )
    ios_pkg_problems = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_ios",
        [_FakeAllowedEntry("Packages/Core/Package.swift")],
        ios_base_rows,
    )
    assert len(ios_pkg_problems) == 1
    assert "boundary" in ios_pkg_problems[0][1].lower()


def test_tier_c_taxonomy_explicit_c2_heuristic_warning_and_roots(
    tmp_path: Path,
) -> None:
    """Verify TierCTaxonomy C2 Needs enforcement, heuristic warnings, and Integration test roots matching."""
    reg = _load_registry()

    # Explicit # tier: C2 without Needs -> hard problem
    explicit_row = _FakeRow(
        "V5",
        "TIER-C",
        "flutter test integration_test/app_test.dart # tier: C2",
        needs=(),
    )
    problems, warnings = reg.TierCTaxonomy.check_tier_c_rows(
        "task_01", [explicit_row], []
    )
    assert len(problems) == 1
    assert "C2" in problems[0][1]
    assert warnings == []

    # Explicit # tier: C2 WITH Needs -> clean
    gated_row = _FakeRow(
        "V5",
        "TIER-C",
        "flutter test integration_test/app_test.dart # tier: C2",
        needs=("FLUTTER_DEVICE",),
    )
    problems_ok, warnings_ok = reg.TierCTaxonomy.check_tier_c_rows(
        "task_01", [gated_row], []
    )
    assert problems_ok == []
    assert warnings_ok == []

    # Heuristic heavy-runtime row without # tier: C2 and empty Needs -> warning only
    heuristic_row = _FakeRow(
        "V5", "TIER-C", "npx --no-install playwright test", needs=()
    )
    problems_h, warnings_h = reg.TierCTaxonomy.check_tier_c_rows(
        "task_01", [heuristic_row], []
    )
    assert problems_h == []
    assert len(warnings_h) == 1
    assert "PLAYWRIGHT_BROWSER" in warnings_h[0]

    # validate_integration_test_roots: bare directory, glob, traversal, and missing targets
    tracked = ["tests/test_alpha.py", "packages/core/test/integration/flow_test.dart"]
    created = ["tests/test_new_feature.py"]
    assert (
        reg.TierCTaxonomy.validate_integration_test_roots(
            tmp_path, ["tests"], tracked, created
        )
        == []
    )
    assert (
        reg.TierCTaxonomy.validate_integration_test_roots(
            tmp_path, ["tests/"], tracked, created
        )
        == []
    )
    assert (
        reg.TierCTaxonomy.validate_integration_test_roots(
            tmp_path, ["packages/*/test/integration"], tracked, created
        )
        == []
    )

    root_problems = reg.TierCTaxonomy.validate_integration_test_roots(
        tmp_path, ["../escape", "/abs/path", "nonexistent_dir/"], tracked, created
    )
    assert len(root_problems) == 3
    assert any("../escape" in p for p in root_problems)
    assert any("/abs/path" in p for p in root_problems)
    assert any("nonexistent_dir/" in p for p in root_problems)


def test_registry_edge_cases_wrappers_malformed_manifests_and_heuristics(
    tmp_path: Path,
) -> None:
    """Cover wrapper stripping, clippy flags, malformed manifests, cow_copy symlink cleanup, and heuristics."""
    reg = _load_registry()

    # Empty repo without .agents/quality
    assert reg.TierBContractAdapter.has_provider_manifests(tmp_path) is False
    assert reg.TierBContractAdapter().descriptors.keys() == reg.BUILTIN_STACKS.keys()
    assert len(reg.PoolWorkspaceStrategy().rules) > 0
    assert "python" in reg.TierCTaxonomy().policies

    # Sequential subcommand splitting excludes || and | tails and handles unclosed quotes
    subs = reg._split_sequential_subcommands(
        "fvm dart format . && dart analyze || echo fail; cargo clippy -D warnings | tee out"
    )
    assert len(subs) == 3
    assert subs[0] == ["fvm", "dart", "format", "."]
    assert subs[1] == ["dart", "analyze"]
    assert subs[2] == ["cargo", "clippy", "-D", "warnings"]
    assert reg._split_sequential_subcommands("echo 'unclosed") == [
        ["echo", "'unclosed"]
    ]

    # Wrapper stripping covers common tool runners
    assert reg._strip_command_wrappers(
        ["FOO=1", "env", "-u", "BAR", "npx", "--no-install", "eslint", "."]
    ) == [
        "eslint",
        ".",
    ]
    assert reg._strip_command_wrappers(
        ["uv", "run", "--extra", "dev", "ruff", "check", "."]
    ) == [
        "ruff",
        "check",
        ".",
    ]
    assert reg._strip_command_wrappers(["melos", "exec", "--", "dart", "analyze"]) == [
        "dart",
        "analyze",
    ]
    assert reg._strip_command_wrappers(["pnpm", "exec", "tsc", "--noEmit"]) == [
        "tsc",
        "--noEmit",
    ]
    assert reg._strip_command_wrappers(["python3", "-m", "mypy", "src"]) == [
        "mypy",
        "src",
    ]
    assert reg._strip_command_wrappers(["poetry", "run", "pytest"]) == ["pytest"]

    # Glob matching supports **, ?, character classes, and negation
    assert reg._glob_matches("tests/**/*.py", "tests/test_a.py") is True
    assert reg._glob_matches("tests/**/*.py", "tests/sub/test_a.py") is True
    assert reg._glob_matches("src/[!z]?.py", "src/ab.py") is True
    assert reg._glob_matches("src/[!z]?.py", "src/zb.py") is False

    # Rust clippy missing -D warnings, Web lint + typecheck, boundary passes, and malformed manifest
    _write_six_stack_manifests(tmp_path)
    rs_no_deny = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_rs",
        [_FakeAllowedEntry("crates/core/src/lib.rs")],
        [_FakeRow("V4", "TIER-B", "cargo fmt --all -- --check && cargo clippy")],
    )
    assert len(rs_no_deny) == 1
    assert "-D warnings" in rs_no_deny[0][1]

    web_missing = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_web",
        [_FakeAllowedEntry("apps/web/src/app.ts")],
        [_FakeRow("V4", "TIER-B", "npx --no-install eslint apps/web/src/app.ts")],
    )
    assert len(web_missing) == 1
    assert "type-check" in web_missing[0][1]

    web_ok = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_web",
        [_FakeAllowedEntry("apps/web/src/app.ts")],
        [
            _FakeRow(
                "V4",
                "TIER-B",
                "npx --no-install eslint apps/web/src/app.ts && tsc -p tsconfig.json --noEmit",
            )
        ],
    )
    assert web_ok == []

    # Boundary checks pass when stack-appropriate commands are supplied
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_fl",
            [_FakeAllowedEntry("packages/core/lib/domain/entity.dart")],
            [
                _FakeRow(
                    "V4",
                    "TIER-B",
                    "dart format -o none --set-exit-if-changed . && dart analyze && melos run boundaries",
                )
            ],
        )
        == []
    )
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_and",
            [_FakeAllowedEntry("feature/wallet/domain/UseCase.kt")],
            [
                _FakeRow(
                    "V4",
                    "TIER-B",
                    "./gradlew spotlessCheck detekt :konsist-test:test",
                )
            ],
        )
        == []
    )
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_ios",
            [_FakeAllowedEntry("Packages/Core/Package.swift")],
            [
                _FakeRow(
                    "V4",
                    "TIER-B",
                    "swiftformat Sources --lint && swiftlint lint --strict && swift test --filter ArchTests",
                )
            ],
        )
        == []
    )
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_rs",
            [_FakeAllowedEntry("crates/domain/Cargo.toml")],
            [
                _FakeRow(
                    "V4",
                    "TIER-B",
                    "cargo fmt --check && cargo clippy -Dwarnings && cargo xtask check-arch",
                )
            ],
        )
        == []
    )

    # Malformed manifest for a touched non-Python stack surfaces a clear problem
    (tmp_path / ".agents" / "quality" / "ios-quality.json").write_text(
        "{broken", encoding="utf-8"
    )
    malformed_probs = reg.TierBContractAdapter.validate_tier_b(
        tmp_path,
        "task_ios",
        [_FakeAllowedEntry("Sources/App.swift")],
        [_FakeRow("V4", "TIER-B", "swiftformat --lint . && swiftlint lint --strict")],
    )
    assert any("ios-quality.json" in msg for _, msg in malformed_probs)

    # TierCTaxonomy heuristic warnings for Flutter, Android, and iOS
    for cmd, expected_hint in (
        ("flutter test integration_test/login_test.dart", "FLUTTER_DEVICE"),
        ("./gradlew connectedDebugAndroidTest", "ANDROID_DEVICE"),
        ("xcodebuild test -scheme App", "IOS_SIMULATOR"),
    ):
        probs, warns = reg.TierCTaxonomy.check_tier_c_rows(
            "task_h", [_FakeRow("V5", "TIER-C", cmd)], []
        )
        assert probs == []
        assert len(warns) == 1
        assert expected_hint in warns[0]

    # TriageSurfaceRegistry context lines and extensionless paths
    triage = reg.TriageSurfaceRegistry.default()
    assert triage.match_line("src/app.py", " ", "def public_fn():") == set()
    assert triage.match_test_line("tests/test_app.py", " ", "assert True") == (
        False,
        False,
    )
    assert triage.rules_for_path("Makefile") is None
    assert reg.TriageSurfaceRegistry.is_test_file("") is False

    # PoolWorkspaceStrategy replaces legacy .dart_tool symlink with real cow_copy directory
    main_wt = tmp_path / "cow_main"
    slot_wt = tmp_path / "cow_slot"
    _init_git_repo(main_wt, gitignore_text=".dart_tool/\nsecureFiles/*\n")
    _git(main_wt, "worktree", "add", "-q", str(slot_wt), "-b", "slot-legacy", "main")
    (main_wt / ".dart_tool").mkdir()
    (main_wt / ".dart_tool" / "cfg.json").write_text("{}", encoding="utf-8")
    (main_wt / "secureFiles").mkdir()
    (main_wt / "secureFiles" / "stg.json").write_text("{}", encoding="utf-8")
    (slot_wt / ".dart_tool").symlink_to(main_wt / ".dart_tool")
    assert (slot_wt / ".dart_tool").is_symlink()

    mat = reg.PoolWorkspaceStrategy.materialize_mounts(main_wt, slot_wt)
    assert ".dart_tool" in mat["cow_copy"]
    assert "secureFiles" in mat["cow_copy"]
    assert not (slot_wt / ".dart_tool").is_symlink()
    assert (slot_wt / ".dart_tool" / "cfg.json").is_file()
    # Second call is idempotent
    mat2 = reg.PoolWorkspaceStrategy.materialize_mounts(main_wt, slot_wt)
    assert mat2 == mat


def test_registry_security_and_override_coverage(tmp_path: Path) -> None:
    """Exercise path-traversal guards, regex error branches, manifest overrides, and idempotency."""
    reg = _load_registry()

    # Path-safety rejection across every traversal / invalid form
    for bad in (
        "",
        "   ",
        "foo\x00bar",
        ".",
        "./",
        "/abs",
        "~user/x",
        "C:drive/x",
        "a/../b",
    ):
        assert reg._is_safe_relative_path(bad, tmp_path) is False
    assert reg._is_safe_relative_path(123, tmp_path) is False  # type: ignore[arg-type]
    assert reg._expand_rule_paths(tmp_path, "../escape") == []

    # Glob unclosed bracket + target coverage edge cases + wrapper flags
    assert reg._glob_matches("src/[unclosed", "src/[unclosed") is True
    assert reg._target_covers_path("--flag", "lib/a.dart") is False
    assert reg._target_covers_path("lib/*.dart", "lib/a.dart") is True
    assert reg._strip_command_wrappers(["fvm", "dart", "analyze"]) == [
        "dart",
        "analyze",
    ]
    assert reg._strip_command_wrappers(
        ["env", "-i", "A=1", "uv", "run", "--frozen", "mypy"]
    ) == ["mypy"]
    assert reg._extract_format_targets([], ["dart", "format", "$(git", "diff)"]) == []
    assert reg._extract_format_targets(["--", "lib/a.dart"], ["dart", "format"]) == [
        "lib/a.dart"
    ]

    # Manifest overrides: task_tier_b, extensions union, triage_surfaces validation errors
    _write_json(
        tmp_path / ".agents" / "quality" / "web-quality.json",
        {
            "schema_version": 1,
            "extensions": [".svelte", "bad-ext", 42],
            "task_tier_b": {
                "lint_prefixes": ["check_vanilla_js.py"],
                "typecheck_prefixes": [],
                "boundary_triggers": ["shared/"],
                "boundary_prefixes": ["check_module_boundaries.sh"],
                "require_all_allowed_files_in_format": False,
            },
            "triage_surfaces": {
                "signature": "not-a-list",
                "api_wire": ["", 123, r"CustomApi"],
            },
        },
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "unknown-quality.json", {"schema_version": 1}
    )
    _write_json(
        tmp_path / ".agents" / "quality" / "list-quality.json", ["not-an-object"]
    )

    triage = reg.TriageSurfaceRegistry.from_repo(tmp_path)
    assert any(
        "not-a-list" in e or "expected list" in e for e in triage.validation_errors
    )
    assert any("non-empty string" in e for e in triage.validation_errors)
    assert any("root must be a JSON object" in e for e in triage.validation_errors)
    assert triage.match_line("src/view.svelte", "+", "CustomApi()") == {
        "API_ROUTE_OR_SCHEMA_CHANGED"
    }

    # Script match, boundary script match, and historical prefix tolerance
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_web",
            [_FakeAllowedEntry("src/shared/view.svelte")],
            [
                _FakeRow(
                    "V4",
                    "TIER-B",
                    "python3 scripts/check_vanilla_js.py && bash scripts/check_module_boundaries.sh",
                )
            ],
        )
        == []
    )
    assert (
        reg.TierBContractAdapter.validate_tier_b(
            tmp_path,
            "task_web",
            [],
            [],
        )
        == []
    )
    assert reg._subcommand_matches_prefix(
        ["eslint", "src/a.ts"], "eslint src", allow_historical_prefix=True
    )[0]
    assert reg._subcommand_matches_prefix(["eslint"], "") == (False, [])

    # PoolWorkspaceStrategy malformed/non-list/non-dict pool_mounts + non-git dir + missing slot
    non_git = tmp_path / "non_git"
    non_git.mkdir()
    assert reg._is_untracked_and_gitignored(non_git, ".dart_tool") is False
    assert reg.PoolWorkspaceStrategy.materialize_mounts(
        tmp_path / "missing", non_git
    ) == {
        "symlink": [],
        "cow_copy": [],
    }
    assert (
        reg.PoolWorkspaceStrategy.get_excluded_relpaths(non_git, tmp_path / "missing")
        == []
    )

    _write_json(
        non_git / ".agents" / "quality" / "check_quality.json", {"pool_mounts": "bad"}
    )
    assert any(
        "JSON array" in e
        for e in reg.PoolWorkspaceStrategy.from_repo(non_git).validation_errors
    )
    _write_json(
        non_git / ".agents" / "quality" / "check_quality.json",
        {"pool_mounts": ["not-obj"]},
    )
    assert any(
        "must be an object" in e
        for e in reg.PoolWorkspaceStrategy.from_repo(non_git).validation_errors
    )
    (non_git / ".agents" / "quality" / "check_quality.json").write_text(
        "{bad", encoding="utf-8"
    )
    assert any(
        "malformed" in e
        for e in reg.PoolWorkspaceStrategy.from_repo(non_git).validation_errors
    )

    # Unignored directory is never treated as gitignored cow_copy
    git_dir = tmp_path / "git_unignored"
    _init_git_repo(git_dir, gitignore_text="")
    (git_dir / "secureFiles").mkdir()
    (git_dir / "secureFiles" / "unignored.json").write_text("{}", encoding="utf-8")
    assert reg._is_untracked_and_gitignored(git_dir, "secureFiles") is False

    # Symlink mount idempotency when symlink already exists
    slot_dir = tmp_path / "git_slot"
    _git(git_dir, "worktree", "add", "-q", str(slot_dir), "-b", "slot-idem", "main")
    (git_dir / "target").mkdir()
    first = reg.PoolWorkspaceStrategy.materialize_mounts(git_dir, slot_dir)
    second = reg.PoolWorkspaceStrategy.materialize_mounts(git_dir, slot_dir)
    assert first["symlink"] == ["target"]
    assert second["symlink"] == ["target"]

    # TierCTaxonomy active_stacks precedence, non-TIER-C row skip, empty root skip
    active_web = [reg.BUILTIN_STACKS["web"]]
    probs, warns = reg.TierCTaxonomy.check_tier_c_rows(
        "task_c",
        [
            _FakeRow("V2", "GREEN", "npx playwright test"),
            _FakeRow("V5", "TIER-C", "npx playwright test"),
        ],
        active_web,
    )
    assert probs == []
    assert len(warns) == 1
    assert "PLAYWRIGHT_BROWSER" in warns[0]
    assert (
        reg.TierCTaxonomy.validate_integration_test_roots(tmp_path, ["", "  "], [], [])
        == []
    )


class TestStackLifecycleRegistry_Integration:
    """Tier C integration suite providing integration provenance for assigned PLQ scenarios."""

    def test_plq_hp_01_registry_resolves_six_stacks_and_custom_override(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-HP-01] Registry resolves all 6 built-in stacks and custom manifest overrides."""
        test_plq_hp_01_registry_resolves_six_stacks_and_custom_override(tmp_path)

    def test_plq_ec_01_untouched_stack_manifests_incur_zero_tier_b_checks(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-EC-01] Untouched stack manifests incur zero Tier B checks."""
        _verify_plq_ec_01_untouched_stack_manifests_incur_zero_tier_b_checks(tmp_path)

    def test_plq_ec_02_flutter_new_files_require_explicit_format_coverage(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-EC-02] Flutter (new) files require explicit format coverage before git add."""
        _verify_plq_ec_02_flutter_new_files_require_explicit_format_coverage(tmp_path)

    def test_plq_ar_01_suffix_scoped_triage_surface_registry_and_baselines(
        self,
    ) -> None:
        """[PLQ-AR-01] Suffix-scoped TriageSurfaceRegistry isolates stack rules while preserving language-neutral baselines."""
        _verify_plq_ar_01_suffix_scoped_triage_surface_registry_and_baselines()

    def test_plq_fr_01_path_traversal_and_malformed_regex_rejected_safely(
        self, tmp_path: Path
    ) -> None:
        """[PLQ-FR-01] Path traversal in pool_mounts or malformed regex in triage_surfaces is rejected safely."""
        _verify_plq_fr_01_path_traversal_and_malformed_regex_rejected_safely(tmp_path)
