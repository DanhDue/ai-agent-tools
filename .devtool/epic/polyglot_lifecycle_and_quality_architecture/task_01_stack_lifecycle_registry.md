---
id: "task_01_stack_lifecycle_registry"
status: "todo"
priority: "high"
assignee: null
epic: "polyglot_lifecycle_and_quality_architecture"
dueDate: null
created: "2026-11-27T09:18:00+07:00"
modified: "2026-11-27T09:18:00+07:00"
completedAt: null
labels: ["architecture", "polyglot", "registry", "dev-implementation"]
order: "a01"
review_tier: "full"
---

# Task 01: Declarative 6-Stack Lifecycle Registry and Four Open Contracts

Epic: [polyglot_lifecycle_and_quality_architecture](polyglot_lifecycle_and_quality_architecture.md)

## Requirement Analysis

Create the pure Python 3 stdlib module `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` implementing all four Open-Closed contracts defined in the HLD (`TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`) across 6 built-in stack families (`python`, `flutter`, `rust`, `web`, `android`, `ios`) plus user-extensible manifest overlays from `.agents/quality/<stack>-quality.json` and `.agents/quality/check_quality.json`. Guarantee zero cross-stack coupling, zero third-party dependencies, safe path-traversal rejection, and safe invalid-regex handling.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (new)
- `tests/test_stack_lifecycle_registry.py` (new)

Read-only context:
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/polyglot_lifecycle_and_quality_architecture.md`
- `.devtool/epic/polyglot_lifecycle_and_quality_architecture/bdd_scenarios.md`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/manage_worker_pool.py`

## Design Rationale & Applicable Skills

- Apply `d3nexus:test-driven-development` and `d3nexus:python-quality-check` conventions (Python 3 stdlib only, full type annotations for `mypy`).
- Use frozen dataclasses (`TierBPolicy`, `SurfaceRuleSet`, `TierCPolicy`, `PoolMountRule`, `StackDescriptor`) so descriptors are immutable and safe to cache across parallel calls.
- Reuse sequential `&&`/`;` subcommand splitting outside quotes so compound `TIER-B` verification commands match cleanly across all 6 stacks.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (new): `StackDescriptor`, `TierBPolicy`, `SurfaceRuleSet`, `TierCPolicy`, `PoolMountRule`, `BUILTIN_STACKS`, `TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`.
  - `tests/test_stack_lifecycle_registry.py` (new): Unit + integration tests covering all 6 built-in stacks, manifest overrides, custom 7th stack (`extensions`), suffix isolation, and security guards.
- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_task_contract.py`, `skills/dev-implementation/resources/scripts/manage_worker_pool.py`, `skills/dev-implementation/resources/scripts/test_check_task_contract.py`, `skills/dev-implementation/resources/scripts/test_manage_worker_pool.py`.
- **Cross-Platform Bridges**: None (kit Python module).
- **Target Coverage Threshold**: >= 90% on `_stack_lifecycle_registry.py`, 100% on path traversal and regex error handling branches.

### BDD SCENARIOS

Covers: PLQ-HP-01, PLQ-EC-01, PLQ-EC-02, PLQ-AR-01, PLQ-FR-01

```gherkin
Scenario: [PLQ-HP-01] [Tier C - Integration] Registry resolves all 6 built-in stacks and custom manifest overrides
Given a repository containing active quality manifests for python, flutter, rust, web, android, and ios
When TierBContractAdapter, PoolWorkspaceStrategy, TriageSurfaceRegistry, and TierCTaxonomy are initialized from the repository root
Then each of the 6 stack families resolves its exact file extensions, default Tier B policy, suffix-scoped SurfaceRuleSet, and Tier C policy
And an optional custom manifest declaring extensions [".go"] and task_tier_b format_prefixes ["gofmt -l"] is activated for ".go" Allowed files without modifying Python kit code

Scenario: [PLQ-EC-01] [Tier C - Integration] Untouched stack manifests incur zero Tier B checks
Given a polyglot repository with active flutter-quality.json, rust-quality.json, and python-quality.json manifests
When TierBContractAdapter validates a task whose Allowed files only modify "crates/core/src/calc.rs"
Then only the rust adapter is dispatched
And zero flutter (dart format / dart analyze) or python (ruff / mypy) problems are emitted

Scenario: [PLQ-EC-02] [Tier C - Integration] Flutter and Python (new) files require explicit format coverage before git add
Given a repository with flutter-quality.json and a task whose Allowed files include "lib/new_widget.dart (new)" and "lib/existing.dart"
When the TIER-B dart format row only names "lib/existing.dart" and omits "lib/new_widget.dart"
Then TierBContractAdapter reports a missing format coverage problem naming "lib/new_widget.dart"

Scenario: [PLQ-AR-01] [Tier C - Integration] Suffix-scoped TriageSurfaceRegistry never cross-fires patterns across languages
Given a Dart file containing the text "unsafe fn" and "tokio::spawn", a Rust file containing "MethodChannel" and "DriftDatabase", and a Kotlin file containing "XCTSkip" and "Codable"
When TriageSurfaceRegistry evaluates each added line by its file suffix
Then zero surface triggers fire on those cross-language strings
And matching native-stack edits (Dart MethodChannel, Rust unsafe/sqlx::query, TS fetch(/Worker(, Kotlin RoomDatabase/@Ignore, Swift actor/XCTSkip, Python FastAPI/pytest.mark.skip) each fire their exact corresponding trigger code

Scenario: [PLQ-FR-01] [Tier C - Integration] Path traversal in pool_mounts or malformed regex in triage_surfaces is rejected safely
Given a check_quality.json containing pool_mounts path "../outside_secret" and a flutter-quality.json containing triage_surfaces signature pattern "[unclosed-regex"
When PoolWorkspaceStrategy and TriageSurfaceRegistry load these manifests
Then PoolWorkspaceStrategy rejects "../outside_secret" without accessing any path outside repo_root
And TriageSurfaceRegistry skips or surfaces a clear validation error for "[unclosed-regex" without raising an unhandled re.error crash
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_stack_lifecycle_registry.py::test_plq_hp_01_registry_resolves_six_stacks_and_custom_override` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_stack_lifecycle_registry.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_manage_worker_pool.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py tests/test_stack_lifecycle_registry.py && ruff format --check skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py tests/test_stack_lifecycle_registry.py && mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py tests/test_stack_lifecycle_registry.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_stack_lifecycle_registry.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **New contract (`_stack_lifecycle_registry.py`)**:
  - 6 built-in stack ids & extensions:
    - `python`: `(".py",)`
    - `flutter`: `(".dart",)`
    - `rust`: `(".rs",)`
    - `web`: `(".ts", ".tsx", ".js", ".mjs", ".astro")`
    - `android`: `(".kt", ".kts")`
    - `ios`: `(".swift",)`
  - `TriageSurfaceRegistry` suffix regexes (from approved Gate 1 spec):
    - `.dart`: signature `MethodChannel|EventChannel|@HostApi|@FlutterApi|ffi\.`, api_wire `@RestApi|@GET|@POST|fromJson`, persistence `DriftDatabase|outbox_entries`, concurrency `Isolate\.|Completer<`, test_weakening `skip:\s*(?:true|['"])`.
    - `.rs`: signature `pub\s+(?:async\s+)?(?:fn|struct|enum|trait)`, api_wire `unsafe\b|extern\s+"C"`, persistence `sqlx::query|SELECT|INSERT\s+INTO`, concurrency `tokio::spawn|Mutex|RwLock`, test_weakening `#\[ignore\b`.
    - `.ts/.tsx/.js/.mjs/.astro`: signature `export\s+(?:async\s+)?(?:function|class|interface|type)`, api_wire `fetch\(|WebSocket|EventSource`, persistence `indexedDB|localStorage`, concurrency `Worker\(|SharedArrayBuffer`, test_weakening `\.(?:skip|fixme)\(`.
    - `.kt/.kts`: signature `(?:suspend\s+)?fun\s+|interface\s+`, api_wire `@(?:GET|POST|PUT|DELETE|Entity|Dao)\b|MethodChannel`, persistence `RoomDatabase|SQLiteDatabase`, concurrency `Mutex|CoroutineScope|Dispatchers\.`, test_weakening `@(?:Ignore|Disabled)\b`.
    - `.swift`: signature `public\s+(?:func|struct|class|protocol|enum|actor)`, api_wire `Codable|URLSession|FlutterMethodChannel`, persistence `@Model|NSManagedObject|sqlite3`, concurrency `\bactor\s+|Task\.detached|NSLock`, test_weakening `XCTSkip|@Test\([^)]*\.disabled`.
    - `.py`: preserves exact existing `_PUBLIC_SIGNATURE_RES`, `_API_SURFACE_RES`, `_DB_SURFACE_RES`, `_CONCURRENCY_RES`, `_TEST_SKIP_RE` from `manage_worker_pool.py` (`L79-L108`).
  - `triage_surfaces` manifest override is strictly a category-keyed JSON object (`signature | api_wire | persistence | concurrency | test_weakening -> list[str]`) per `[SE-01]`.
  - `PoolWorkspaceStrategy` defaults: `symlink` = `("target", "node_modules", ".astro", ".venv", ".gradle", ".build", "Pods")`; `cow_copy` = `(".dart_tool", "packages/*/.dart_tool", "features/*/.dart_tool", "bricks/*/hooks/.dart_tool", "secureFiles", "local.properties", "android/local.properties", "*.xcconfig", "ios/Flutter/*.xcconfig", "macos/Flutter/*.xcconfig")`; merges validated `"pool_mounts"` from `.agents/quality/check_quality.json` rejecting `..` or absolute paths escaping `repo_root`.
  - `TierCTaxonomy` exposes `check_tier_c_rows(rows, active_stacks) -> tuple[list[tuple[str, str]], list[str]]` and `validate_integration_test_roots(repo_root, roots, tracked_files, created_files) -> list[str]`.
  - In TDD `RED` (`V1`), `test_plq_hp_01_registry_resolves_six_stacks_and_custom_override` catches `ImportError` and calls `pytest.fail(...)` so `V1` deterministically exits `1` with `FAILED` before `_stack_lifecycle_registry.py` exists.

## Definition of Done

- [ ] `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` implements all 6 built-in stacks and 4 open contracts using Python 3 stdlib only (V2, V5)
- [ ] All unit tests in `tests/test_stack_lifecycle_registry.py` pass covering `PLQ-HP-01`, `PLQ-EC-01`, `PLQ-EC-02`, `PLQ-AR-01`, `PLQ-FR-01` (V2, V5)
- [ ] Downstream task contract and worker pool regression suites pass without regressions (V3)
- [ ] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4)
- [ ] Fresh JUnit XML report written to `build/test-results/task_01.xml` containing all 5 assigned scenario IDs (V5)

## Dependencies & Blockers

- None (Wave 1 — runs in parallel with Task 02 and Task 03).

## References & Rollback

- Reference HLD: [polyglot_lifecycle_and_quality_architecture.md](polyglot_lifecycle_and_quality_architecture.md)
- Rollback: Delete `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` and `tests/test_stack_lifecycle_registry.py`.
