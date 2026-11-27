# Open-Closed Polyglot Lifecycle and Quality Architecture Design

- **Date**: 2026-11-27
- **Epic Slug**: `polyglot_lifecycle_and_quality_architecture`
- **Status**: Approved (Gate 1 Approved at `ac6f972`)
- **PIC**: duvthinh403
- **Selected Approach**: Approach A — Typed Python Registry with Manifest Overlays and Shared Additive Validator Helper
- **Reference Inputs (Read-Only)**: `nexus` commit `49a6ee7a` (`polyglot-quality-lifecycle-handoff.md` and `scripts/check_lcov_threshold.py`)

## Table of Contents

- [Problem Statement and Goals](#problem-statement-and-goals)
- [Shared Contract Warnings](#shared-contract-warnings)
- [System Architecture Overview](#system-architecture-overview)
- [CLI Output Contract and Token-Budget Invariant](#cli-output-contract-and-token-budget-invariant)
- [Component 1 Declarative Stack Lifecycle Registry](#component-1-declarative-stack-lifecycle-registry)
- [Component 2 Portable Multi-Format Diff-Coverage Engine](#component-2-portable-multi-format-diff-coverage-engine)
- [Component 3 Unified Quality Schemas Validators and Scaffolder](#component-3-unified-quality-schemas-validators-and-scaffolder)
- [Component 4 Lifecycle Documentation and Tier C1 vs Tier C2 Standardization](#component-4-lifecycle-documentation-and-tier-c1-vs-tier-c2-standardization)
- [Failure Modes and Risk Mitigations](#failure-modes-and-risk-mitigations)
- [Verification and Testing Strategy](#verification-and-testing-strategy)
- [Non-Goals and Boundaries](#non-goals-and-boundaries)

## Problem Statement and Goals

The `d3nexus` toolkit in `ai-agent-tools` orchestrates `dev-lifecycle`, `dev-designer`, `dev-implementation`, `setup_quality_check`, and `quality_check` across polyglot mobile, web, systems, and backend repositories (`python`, `flutter`, `rust`, `web`, `android`, `ios`). Production hardening on the `nexus` repository (`49a6ee7a`) exposed five structural gaps where lifecycle automation remained Python-centric or brittle across stacks:

1. **Python-only Tier B enforcement**: `skills/dev-implementation/resources/scripts/check_task_contract.py` only inspects Python tasks (`check_python_tier_b`) and misses Flutter/Dart, Rust, Web, Android, and iOS static-gate coverage as well as polyglot tasks touching multiple languages.
2. **Destructive cache symlinking in worker pools**: `skills/dev-implementation/resources/scripts/manage_worker_pool.py` symlinks `.dart_tool` as a directory symlink, which breaks `.gitignore` directory rules (`.dart_tool/`) in Flutter/Melos workspaces and fails to copy nested package `.dart_tool/` trees or gitignored secrets (`secureFiles/`, `local.properties`, `*.xcconfig`).
3. **Unsuffix-scoped Tier 1 risk triage**: `manage_worker_pool.py` applies a single global Python-biased regex set during `triage-fix` regardless of file extension, missing Dart/Rust/Web/Kotlin/Swift surfaces and risking cross-stack false positives, while `_is_test_file()` omits Dart, Rust, Kotlin, and Swift test patterns.
4. **Missing portable diff-coverage, verbose validator stdout, and uneven provider contracts**: Hunk-level diff-coverage enforcement only exists as a repo-local script in `nexus`; `validate_quality_contract.py` and the 6 `validate_*_quality.py` CLIs print multi-line pretty JSON even on `PASS`; `web-quality-check` lacks a formal JSON schema; `check-quality.schema.json` and provider validators reject additive hooks (`pool_mounts`, `task_tier_b`, `triage_surfaces`, `standards_catalog`, dual-floor coverage, unified audit/security/license capabilities); and `scaffold_quality_manifest.py` still emits destructive Android `"cleanup": ["pkill", "-9", "java"]`.
5. **Python-hardcoded lifecycle docs and unenforced Tier C1 vs Tier C2 boundary**: `dev-designer` and `dev-implementation` docs hardcode `uv run pytest`, conflate fast host/VM subcutaneous integration (`Tier C1`, `< 5s`) with `Needs:`-gated device/simulator/browser E2E (`Tier C2`), and lack lightweight contract checks for ungated `Tier C2` rows or invalid HLD `Integration test roots:`.

### Design Goals

- **Zero cross-project breakage (Strict Open-Closed extensibility)**: Support all 6 built-in stack families (`python`, `flutter`, `rust`, `web`, `android`, `ios`) out of the box keyed strictly by `.agents/quality/<stack>-quality.json` presence AND `Path.suffix`, with zero cross-stack coupling and full manifest override support via `.agents/quality/<stack>-quality.json` and `.agents/quality/check_quality.json`.
- **Zero LLM token overhead**: Enforce compact one-line `PASS` stdout across deterministic local CLI validators (`check_diff_coverage.py`, `check_task_contract.py`, `validate_quality_contract.py`, and all 6 `validate_*_quality.py` scripts), expanding diagnostics only on `FAIL`/`BLOCKED` or opt-in `--verbose` / `--json`.
- **Sub-15-second per-task speed**: Keep `Task 1..N-1` scoped to unit/regression tests, scoped `TIER-B` checks on `Allowed files`, and fast `Tier C1` headless subcutaneous integration (`< 5s`), reserving full workspace test + dual-floor coverage + `--all-files` ratchets for Gate 4 (`--profile epic`).
- **Zero third-party dependencies**: All kit runtime scripts remain Python 3 stdlib only.
- **Additive v1 backwards compatibility**: Existing consumer manifests (`D3Nexus`, `lyrics-sync`, `nexus`, `ai-agent-tools`) continue to validate with `PASS` without forced migration; `setup_quality_check` scaffolds the complete upgraded contract by default.

## Shared Contract Warnings

- `ai-agent-tools` is a self-contained plugin kit repository and has **no `shared-contracts/` directory or symlink**.
- No Hub (`D3Nexus`) or Satellite (`lyrics-sync`, `nexus`) wire contracts, API payloads, or adjacent repository files are modified by this epic.
- Read-only reference files from `nexus` (`polyglot-quality-lifecycle-handoff.md` and `scripts/check_lcov_threshold.py`) were inspected strictly as design inputs; no writes occur outside `ai-agent-tools`.

## System Architecture Overview

```mermaid
flowchart TD
    CQ[".agents/quality/check_quality.json (pool_mounts & providers)"] --> REG["_stack_lifecycle_registry.py (6 Built-in Stacks + 4 Open Contracts)"]
    PM[".agents/quality/<stack>-quality.json (task_tier_b, triage_surfaces, capabilities)"] --> REG

    REG --> TIERB["TierBContractAdapter"]
    REG --> TIERC["TierCTaxonomy"]
    REG --> POOL["PoolWorkspaceStrategy"]
    REG --> TRIAGE["TriageSurfaceRegistry"]

    TIERB --> CTC["check_task_contract.py (Polyglot Tier B + Tier C2 Gate)"]
    TIERC --> CTC
    POOL --> MWP1["manage_worker_pool.py (symlink & apfs_cow_tree Mounts)"]
    TRIAGE --> MWP2["manage_worker_pool.py (Suffix-Scoped triage-fix)"]

    COMMON["_provider_manifest_common.py (Shared Additive v1 Rules + Compact CLI Formatter)"] --> VALS["6 Provider Validators + validate_quality_contract.py"]
    DIFFCOV["check_diff_coverage.py (LCOV, Cobertura XML, JaCoCo XML)"] --> SCAFF["scaffold_quality_manifest.py & Provider Templates"]
```

### Module Ownership and Dependency Boundaries

| Component | Path | Responsibility | Depends On |
| :--- | :--- | :--- | :--- |
| Stack Lifecycle Registry | `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` | Frozen 6-stack descriptors, manifest overlay loading, `TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy` | Python 3 stdlib only |
| Task Contract Checker | `skills/dev-implementation/resources/scripts/check_task_contract.py` | Task/HLD validation; delegates Tier B checks to `TierBContractAdapter` and Tier C2 / `Integration test roots:` checks to `TierCTaxonomy`; compact 1-line `PASS` stdout | `_stack_lifecycle_registry.py` |
| Worker Pool Manager | `skills/dev-implementation/resources/scripts/manage_worker_pool.py` | Slot lifecycle, cache mounts, clean/staging exclusions, suffix-scoped Tier 1 diff triage | `_stack_lifecycle_registry.py` |
| Portable Diff-Coverage CLI | `skills/quality_check/resources/scripts/check_diff_coverage.py` | Multi-format coverage parser (`lcov`, `cobertura`, `jacoco`) + hunk-level git diff-coverage & dual-floor evaluator; compact 1-line `PASS` stdout | Python 3 stdlib + `git` |
| Shared Provider Validator Helper | `skills/quality_check/resources/scripts/_provider_manifest_common.py` | Additive v1 validation (`standards_catalog`, `task_tier_b`, `triage_surfaces`, `extensions`, dual-floor `coverage`, unified capabilities, 4 profiles) + shared compact/verbose/JSON CLI formatter | Python 3 stdlib only |
| Registry & Provider Validators | `skills/quality_check/resources/scripts/validate_quality_contract.py` + 6 `validate_*_quality.py` | Validate `check_quality.json` (`pool_mounts`) and each stack manifest; compact 1-line `PASS` stdout with opt-in `--verbose` / `--json` | `_provider_manifest_common.py` |
| Scaffolder & Schemas | `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py` + 7 JSON schemas | Auto-detect stacks and scaffold full 4-profile unified manifests with portable diff-coverage | Python 3 stdlib only |

## CLI Output Contract and Token-Budget Invariant

Per `polyglot-quality-lifecycle-handoff.md` Section 1 (Invariant 2: **Zero LLM Token Overhead**), every deterministic local CLI validator upgraded or introduced by this epic follows one uniform stdout contract:

- **Default on `PASS` (exit code `0`)**: Emit **exactly one compact single-line summary** to stdout and zero extra chatter, keeping token cost near zero during automated task and Gate 4 loops.
- **Default on `FAIL` / `BLOCKED` (exit code `1` or `2`)**: Emit the summary line plus actionable per-file / per-hunk / per-rule diagnostics so the agent can fix root causes in one pass without re-running.
- **Opt-in flags across all CLIs**:
  - `--verbose`: Expand full per-package / per-file / implicit-protected-path / capability breakdown even on `PASS`.
  - `--json`: Emit structured JSON output for machine-to-machine consumers and CI scripts.

| CLI Script | Default `PASS` Single-Line Output | Expanded on `FAIL` / `BLOCKED` or `--verbose` | Machine Output |
| :--- | :--- | :--- | :--- |
| `check_diff_coverage.py` | `PASS: coverage=84.2% (floor>=75.0%), diff=91.5% (floor>=80.0%, files=4, lines=65)` (or diff-only variant when `--min-coverage 0`) | Per-package floor breaches, per-file coverage table, and uncovered diff line ranges | `--json` |
| `validate_<stack>_quality.py` (all 6 stacks) | `PASS: <stack>-quality (profile=<profile>, caps=<n>)` | Each finding (`<code>: <message> [capability=...]`) + summary line | `--json` (returns `{"status", "findings"}`) |
| `validate_quality_contract.py` (`registry`, `capability`, `invocation`, `result`, `reconcile`) | `PASS: <subcommand> (profile=<profile>, items=<n>)` | Each finding (`<code>: <message>`) + summary line | `--json` (returns full structured dict, required when piping normalized payloads) |
| `check_task_contract.py` | `Result: 0 problems — PASS` | All problem lines + `Implicit protected paths: ...` + `Result: <n> problems — FAIL` (with `--verbose` also printing `Implicit protected paths: ...` on `PASS`) | `--json` (returns `{"status", "problems", "warnings", "implicit_protected_paths"}`) |

Python library entry points (`validate_registry()`, `validate_*_config()`, `normalize_invocation()`, `reconcile_results()`) remain completely unchanged in their returned dict structures, preserving 100% backwards compatibility with `verify_polyglot_registry.py` and existing unit tests. Existing CLI tests asserting `Implicit protected paths:` on `PASS` will pass `--verbose` alongside new regression tests locking the default 1-line `PASS` contract.

## Component 1 Declarative Stack Lifecycle Registry

Location: `skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py` (Python 3 stdlib only). Defines the **four open contracts** specified in `polyglot-quality-lifecycle-handoff.md` Section 2: `TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, and `TierCTaxonomy`.

### Core Data Model

- `StackDescriptor` (frozen dataclass):
  - `stack_id: str` (`python`, `flutter`, `rust`, `web`, `android`, `ios`, or custom manifest id)
  - `extensions: tuple[str, ...]` (normalized lowercase with leading dot)
  - `test_path_patterns: tuple[str, ...]` (suffix/path test classifiers for `_is_test_file`)
  - `default_tier_b: TierBPolicy`
  - `default_surfaces: SurfaceRuleSet`
  - `tier_c_policy: TierCPolicy`
- `PoolMountRule` (frozen dataclass):
  - `path: str` (relative path or glob pattern from repo root)
  - `mode: Literal["symlink", "cow_copy"]`
  - `optional: bool = True`
- `SurfaceRuleSet` (frozen dataclass):
  - `signature: tuple[re.Pattern[str], ...]`
  - `api_wire: tuple[re.Pattern[str], ...]`
  - `persistence: tuple[re.Pattern[str], ...]`
  - `concurrency: tuple[re.Pattern[str], ...]`
  - `test_weakening: tuple[re.Pattern[str], ...]`
  - `test_assertion: tuple[re.Pattern[str], ...]`
- `TierCPolicy` (frozen dataclass):
  - `tier_c1_examples: tuple[str, ...]`
  - `tier_c2_command_patterns: tuple[re.Pattern[str], ...]`
  - `default_needs_hint: str`

### Built-In 6-Stack Matrix

#### 1. `TierBContractAdapter` (consumed by `check_task_contract.py`)

Dispatch algorithm:
1. Extract all paths from `Allowed files` (stripping `(new)` / `(existing)` annotations while recording whether new files exist) and derive the unique lowercase file suffix set.
2. Scan `.agents/quality/*-quality.json` in `repo_root` (if `repo_root` is available):
   - If one or more provider manifests exist, resolve active stacks by intersecting the task's `Allowed files` extensions against active manifests (matching built-in stack ids from `<stack>-quality.json` plus any custom manifest declaring `"extensions"`).
   - If **no** `.agents/quality/*-quality.json` manifests exist at all (e.g., standalone unit test fixtures or legacy Python repos), preserve the existing legacy `check_python_tier_b` fallback when `.py` files are touched.
3. Evaluate every matched stack independently (supporting polyglot single tasks touching `.rs` + `.ts`, `.py` + `.js`, or `.dart` + `.rs`/`.kt`/`.swift`) while guaranteeing **0% invocation on untouched stacks**.
4. Reuse `_split_sequential_subcommands()` (splitting `&&` and `;` outside quotes) so compound verification commands match capability prefixes cleanly across all 6 stacks.
5. Honor optional `"task_tier_b"` overrides in `.agents/quality/<stack>-quality.json`:
   - `format_prefixes: list[str]`, `lint_prefixes: list[str]`, `typecheck_prefixes: list[str]`, `boundary_prefixes: list[str]`, `boundary_triggers: list[str]` (path substrings/filenames), `require_all_allowed_files_in_format: bool`.

Built-in default Tier B contracts per stack:

| Stack | Extensions | Mandatory Format / Lint / Typecheck Rows | Conditional Boundary Check Triggers |
| :--- | :--- | :--- | :--- |
| `flutter` | `.dart` | `dart format` covering all `.dart` `Allowed files` (including `(new)` files before `git add`) or workspace `dart format --output=none --set-exit-if-changed`; `dart analyze` or `flutter analyze` | When `domain/` or `pubspec.yaml` is in `Allowed files`: require configured boundary/hygiene check (`boundaries`, `architecture`, or `melos run` boundary script) |
| `rust` | `.rs` | `cargo fmt --check` (or `cargo fmt --all -- --check`); `cargo clippy` with `-D warnings` | When `Cargo.toml` or `domain` crate paths are in `Allowed files`: require `xtask` / configured `architecture` boundary check |
| `web` | `.ts`, `.tsx`, `.js`, `.mjs`, `.astro` | Configured linter/guard (`eslint`, `biome`, `npm run lint`, `check_vanilla_js.py`, or manifest `lint` capability) and type-checker (`tsc --noEmit`, `astro check`, `npm run check`, or manifest `type_check` capability) | Optional via manifest `task_tier_b.boundary_triggers` |
| `python` | `.py` | Full `Allowed files` coverage in `ruff check`, `ruff format --check`, and `mypy`/`pyright`/`ty` | When cross-module/package changes touch `pyproject.toml` or multiple top-level packages and `architecture`/`lint-imports` is configured: require `lint-imports` / `architecture` check |
| `android` | `.kt`, `.kts` | `spotlessCheck` and `detekt` (via `./gradlew` or `gradle`) | When `domain/` or public ABI (`*.api` / `public` API modules) change: require `:konsist-test:test` / `apiCheck` (or configured `architecture`/`bcv` capability) |
| `ios` | `.swift` | `swiftformat --lint` and `swiftlint lint --strict` | When `domain/` or `Project.swift`/`Package.swift` change: require `ArchTests` or `check_module_boundaries.sh` (or configured `architecture`/`boundaries` capability) |

#### 2. `PoolWorkspaceStrategy` (consumed by `manage_worker_pool.py`)

Replaces the flat `CACHE_DIR_CANDIDATES` symlink loop with a declarative two-mode strategy:

- **`symlink` mode** (O(1) shared binary/package caches at slot root):
  - `target`, `node_modules`, `.astro`, `.venv`, `.gradle`, `.build`, `Pods`
- **`cow_copy` (`apfs_cow_tree`) mode** (copy-on-write directory/file tree clone via `cp -c -R` on macOS Darwin with automatic fallback to `shutil.copytree` / `shutil.copy2` on Linux or cross-volume APFS failure — **never a symlink** so `.gitignore` directory rules like `.dart_tool/` remain intact):
  - Root `.dart_tool`
  - Nested Melos/Flutter `.dart_tool` directories discovered dynamically in `main_wt`: `packages/*/.dart_tool`, `features/*/.dart_tool`, `bricks/*/hooks/.dart_tool`
  - Gitignored local secrets/configs when present in `main_wt` and ignored by git: `secureFiles`, `local.properties`, `android/local.properties`, `*.xcconfig`, `ios/Flutter/*.xcconfig`, `macos/Flutter/*.xcconfig`
- **Manifest extensibility**: Reads optional `"pool_mounts"` array from `.agents/quality/check_quality.json` where each entry is `{"path": "<rel-path-or-glob>", "mode": "symlink" | "cow_copy"}`. Security invariant: reject any path containing `..` or absolute paths escaping the repository root.
- **Git clean, snapshot, triage, and staging isolation**:
  - `PoolWorkspaceStrategy.get_excluded_relpaths(slot_path, main_wt)` returns every active mounted path (both symlinked and `cow_copy` materialized paths) so:
    1. `sync_slot()` passes `-e <path>` to `git clean -fd` for every active mount.
    2. `capture_slot_tree_sha()` excludes every active mount from the temporary `GIT_INDEX_FILE`.
    3. `triage_fix_slot()` passes `:(exclude)<path>` to `git diff`.
    4. `finalize_slot()` unstages any mounted path (whether symlink or `cow_copy`) before committing, preventing accidental secret or `.dart_tool` commits.

#### 3. `TriageSurfaceRegistry` (consumed by `manage_worker_pool.py` `triage-fix`)

Scopes every `SurfaceRuleSet` strictly by `Path(changed_file).suffix.lower()` (zero cross-firing across stacks):

| Suffixes | `signature` | `api_wire` | `persistence` | `concurrency` | `test_weakening` (added lines in test files) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `.dart` | `MethodChannel\|EventChannel\|@HostApi\|@FlutterApi\|ffi\.` | `@RestApi\|@GET\|@POST\|fromJson` | `DriftDatabase\|outbox_entries` | `Isolate\.\|Completer<` | `skip:\s*(?:true\|['"])` |
| `.rs` | `pub\s+(?:async\s+)?(?:fn\|struct\|enum\|trait)` | `unsafe\b\|extern\s+"C"` | `sqlx::query\|SELECT\|INSERT\s+INTO` | `tokio::spawn\|Mutex\|RwLock` | `#\[ignore\b` |
| `.ts`, `.tsx`, `.js`, `.mjs`, `.astro` | `export\s+(?:async\s+)?(?:function\|class\|interface\|type)` | `fetch\(\|WebSocket\|EventSource` | `indexedDB\|localStorage` | `Worker\(\|SharedArrayBuffer` | `\.(?:skip\|fixme)\(` |
| `.kt`, `.kts` | `(?:suspend\s+)?fun\s+\|interface\s+` | `@(?:GET\|POST\|PUT\|DELETE\|Entity\|Dao)\b\|MethodChannel` | `RoomDatabase\|SQLiteDatabase` | `Mutex\|CoroutineScope\|Dispatchers\.` | `@(?:Ignore\|Disabled)\b` |
| `.swift` | `public\s+(?:func\|struct\|class\|protocol\|enum\|actor)` | `Codable\|URLSession\|FlutterMethodChannel` | `@Model\|NSManagedObject\|sqlite3` | `\bactor\s+\|Task\.detached\|NSLock` | `XCTSkip\|@Test\([^)]*\.disabled` |
| `.py` | Existing Python `def`/`class` public signature rules | Existing FastAPI/router/Pydantic rules | Existing SQLAlchemy/SQL/Alembic rules | Existing `asyncio`/lock/thread rules | Existing `pytest.mark.skip`/`xfail`/`unittest.skip` rules |

Additional polyglot test-file classification (`_is_test_file`):
- Directory markers: `/tests/`, `/test/`, `/__tests__/`, `/integration_test/`, `/androidTest/`, `/UnitTests/`, `/UITests/`.
- Filename markers: `test_*.py`, `*_test.py`, `*_test.dart`, `*_test.rs`, `*.test.*`, `*.spec.*`, `*Test.kt`, `*Tests.kt`, `*Spec.kt`, `*Test.swift`, `*Tests.swift`.
- Assertion regexes extended per suffix so test assertion weakening counts `expect(`, `assert_eq!`, `assert!`, `assertEquals`, `assertTrue`, `XCTAssert`, `#expect(`, `verify(` alongside Python `assert`.

**Intentional Schema Refinement (`triage_surfaces`: `array` -> `object`)**:
- `polyglot-quality-lifecycle-handoff.md` Section 2 mentions `"triage_surfaces"` informally as an array. This architecture intentionally refines `"triage_surfaces"` in v1 provider schemas and `_stack_lifecycle_registry.py` to an **object keyed by canonical risk category**:
  ```json
  {
    "triage_surfaces": {
      "signature": ["MyPublicMacro\\("],
      "api_wire": ["MyBridgeChannel"],
      "persistence": ["CustomBoxStore"],
      "concurrency": ["CustomMutex"],
      "test_weakening": ["@SkipCustom"]
    }
  }
  ```
- Rationale: (1) maps 1:1 to `SurfaceRuleSet`'s five fields and `TIER1_TRIGGER_ORDER` codes, (2) allows deterministic per-category additive merging onto built-in suffix rules without repeating category tags on every pattern object, and (3) enables strict JSON Schema (`additionalProperties: false`) validation of category keys plus regex compilation checks inside `_provider_manifest_common.py`.

#### 4. `TierCTaxonomy` (consumed by `check_task_contract.py` and Component 4 Docs)

Provides lightweight, zero-false-positive mechanical enforcement alongside the Component 4 documentation so `Tier C1` (fast host/VM subcutaneous integration, `< 5s`) and `Tier C2` (`Needs:`-gated device/simulator/browser E2E) stay cleanly separated before Gate 2 closes:

- **Hard Contract Errors (`check.problem`, exit code `1`)** — triggered strictly on unambiguous declarations:
  1. **Explicit `Tier C2` row missing `Needs:`**: Any `TIER-C` verification row whose command, expect clause, or row comment/annotation explicitly declares `Tier C2` / `TIER-C2` (case-insensitive `\bTIER[- ]?C2\b`) while its `Needs` cell is empty (`—` or `-`) fails contract validation.
  2. **Invalid HLD `Integration test roots:` line**: When an Epic HLD declares an optional `Integration test roots:` directive (per handoff Section 2), every listed root path/glob must be a safe repo-relative path (no `..`, no absolute path) matching at least one tracked file or task `(new)` file.
- **Non-Blocking Diagnostic Warnings (`check.warnings`, emitted to stderr and in `--json`, never failing exit code `0`)** — zero false positives on legacy epics:
  1. **Ungated heavy-runtime `TIER-C` heuristic**: If a `TIER-C` row with empty `Needs` (`—`) matches a stack's conservative Tier C2 runtime pattern (`flutter test.*integration_test`, `connected\w*AndroidTest`, `xcodebuild\b.*\btest\b`, or `playwright test`) without explicitly tagging `Tier C2`, emit a structured warning suggesting a `Needs:` token (e.g., `FLUTTER_DEVICE`, `ANDROID_DEVICE`, `IOS_SIMULATOR`, `PLAYWRIGHT_BROWSER`) so designers catch accidentally ungated heavy suites without breaking legacy epics or repos that legitimately run local headless Playwright in a task.

## Component 2 Portable Multi-Format Diff-Coverage Engine

Location: `skills/quality_check/resources/scripts/check_diff_coverage.py` (Python 3 stdlib only; referenced via `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py`).

### Capabilities and CLI Contract

Ported and generalized from `nexus/scripts/check_lcov_threshold.py` with modular format adapters feeding a unified `CoverageDataset` (`da_by_file: dict[str, dict[int, int]]`, `fallback_by_file: dict[str, tuple[int, int]]`):

- **Supported Formats** (`--format auto|lcov|cobertura|jacoco`, default `auto`):
  - **LCOV**: `SF:` / `DA:` / `LF:` / `LH:` (Flutter `lcov.info`, Rust `cargo llvm-cov --lcov`, Web Vitest/V8/Istanbul LCOV, Swift `llvm-cov export -format=lcov`).
  - **Cobertura XML**: `<packages>/<package>/<classes>/<class filename="...">/<lines>/<line number="..." hits="..."/>` (Python `pytest --cov --cov-report=xml`, JS/TS Cobertura).
  - **JaCoCo XML**: `<report>/<package name="...">/<sourcefile name="...">/<line nr="..." ci="..." mi="..."/>` (Android/Kotlin `./gradlew jacocoTestReport`, where covered hits = `1 if ci > 0 else 0`).
- **Auto-detection**: Inspects XML root tag (`<coverage>` -> `cobertura`, `<report>` -> `jacoco`) or LCOV markers (`SF:` / `end_of_record` -> `lcov`), emitting a clear error exit code `2` on unreadable/unknown formats.
- **CLI Flags**:
  - `report_files...` (one or more coverage report paths, merged cleanly with `max` hit count per `(file, line)`)
  - `--format {auto,lcov,cobertura,jacoco}`
  - `--repo-root <path>` (default `.`)
  - `--source-root <prefix>` (repeatable prefix for resolving relative `<class filename>` / JaCoCo package paths)
  - `--min-coverage <float>` (workspace overall line coverage floor, `0..100` or `0..1` normalized cleanly; default `0.0` when running diff-only)
  - `--min-package-coverage <float>` (optional per-package floor)
  - `--exclude-package-floor <pkg>` (repeatable package name excluded from per-package floor)
  - `--package-group <dir>` (repeatable workspace subpackage root prefix; defaults include `packages`, `features`, `crates`, `apps`, `services`, `modules`, `libs`, `src`)
  - `--diff-base <git-ref>` (computes `git merge-base <diff-base> HEAD` + `git diff -U0` + untracked source files)
  - `--diff-files <path>` (repeatable explicit file override for deterministic unit testing without git)
  - `--min-diff-coverage <float>` (hunk-level diff coverage floor, e.g., `80.0` or `0.80`)
  - `--source-ext <.ext>` (repeatable extension filter for diff-coverage; defaults to all 6 stacks' source extensions when omitted)
  - `--exclude-suffix <suffix>` (repeatable generated-code exclusion; sensible multi-stack defaults including `.g.dart`, `.freezed.dart`, `.gen.dart`, `.pb.dart`, `.pb.rs`, `.pb.swift`, `.d.ts`, `GeneratedPluginRegistrant.swift`)
  - `--verbose` (opt-in expanded per-package and per-file table even on `PASS`)
  - `--json` (opt-in machine-readable JSON summary output for provider ingestion)
- **Output Contract**: Default stdout on `PASS` is a **single compact one-line summary** (`PASS: ...`); on `FAIL` or `BLOCKED`, expands per-package floor breaches, failing files, and uncovered hunk line numbers.
- **Untested New-File Fallback**: Retains `nexus`'s conservative heuristic counting executable non-comment/non-brace lines when a newly added source file is completely absent from coverage reports, generalized for `#` (Python), `//` / `/* */` (Dart/Rust/TS/JS/Kotlin/Swift), and brace-only/annotation-only lines so adding uncovered production files cannot bypass diff coverage.
- **Exit Codes**: `0` = PASS, `1` = FAIL (threshold breach), `2` = BLOCKED/usage error (missing file, malformed report, invalid git ref).

## Component 3 Unified Quality Schemas Validators and Scaffolder

### 1. Registry Contract (`check-quality.schema.json` and `validate_quality_contract.py`)

- Allow optional top-level `"pool_mounts"` in `.agents/quality/check_quality.json`:
  ```json
  {
    "pool_mounts": [
      { "path": "packages/*/.dart_tool", "mode": "cow_copy" },
      { "path": "target", "mode": "symlink" }
    ]
  }
  ```
- Validate each `pool_mounts` entry: `path` must be a non-empty relative string without `..` path traversal or leading `/`; `mode` must be `"symlink"` or `"cow_copy"`.
- Preserve `schema_version: 1` and all existing `providers` validation behavior.
- Add `--verbose` and `--json` flags to `validate_quality_contract.py` CLI, defaulting to a single compact `PASS:` line on success and expanding findings on `FAIL`/`BLOCKED`.

### 2. Shared Additive v1 Provider Contract (`_provider_manifest_common.py` + 6 Provider Schemas & Validators)

Create `skills/quality_check/resources/scripts/_provider_manifest_common.py` and update all 6 provider skills (`flutter`, `rust`, `web`, `python`, `android`, `ios`):

- **Add missing schema**: Create `skills/web-quality-check/resources/schemas/web-quality.schema.json` matching the draft `2020-12` conventions of the other 5 providers.
- **4 Profiles across all 6 schemas**: `pr`, `epic`, `scheduled`, `release` (keep `required: ["pr", "epic"]` so existing repos remain valid; `scheduled` and `release` are optional in validation and always generated by `setup_quality_check`).
- **Unified Additive Capabilities across all 6 schemas**:
  - `anti_stub`, `security`, `security_deps`, `pr_diff_audit`, `workspace_audit` (invoked with `--all-files`), `pr_impact`, `workspace_impact` (invoked with `--all-files`), and `license` (license header verification across Flutter, Rust, Android, iOS, Python, and Web), plus existing stack-native capabilities (`format`, `lint`, `clippy`, `check`, `type_check`, `analyze`, `architecture`, `boundaries`, `bcv`, `db_hygiene`, `test`, `test_unit`, `test_e2e`, `ui_review`, `coverage`, `acceptance`, `contracts`, `contract_diff`, `^contracts_[a-z0-9_]+$`).
  - Keep Android `cleanup` optional in `android-quality.schema.json` strictly for backwards compatibility with existing consumer repositories, while removing `"cleanup": ["pkill", "-9", "java"]` from `scaffold_quality_manifest.py`, `valid_android_quality.json`, and `android-quality-check/SKILL.md`.
- **Dual-Floor `coverage` Object**:
  - Required: `command` (`string[]`), `threshold` (`0..1`).
  - Optional additive fields: `min_package_coverage` (`0..1`), `exclude_package_floor` (`string[]`), `min_diff_coverage` (`0..1`), `diff_base` (`string`), `lcov_path` / `report_path` / `profdata_path` (`string`).
- **Optional Top-Level Additive Keys across all 6 Provider Schemas & Validators**:
  - `standards_catalog` (`string`, relative path e.g. `.agents/quality/standards_catalog.json` — validated as non-empty relative path without `..`).
  - `extensions` (`string[]`, each matching `^\.[a-z0-9]+$`).
  - `task_tier_b` (object with optional `format_prefixes`, `lint_prefixes`, `typecheck_prefixes`, `boundary_prefixes`, `boundary_triggers`, `require_all_allowed_files_in_format`).
  - `triage_surfaces` (**object** mapping `signature | api_wire | persistence | concurrency | test_weakening` to `string[]` of valid regex patterns, compiled and verified during validation; intentionally refined from handoff Section 2's array mention for deterministic per-category merging and strict key validation).
- **Compact CLI Output across all 6 `validate_*_quality.py` CLIs**:
  - Use a shared formatter in `_provider_manifest_common.py` supporting default one-line `PASS` stdout, expanded findings on `BLOCKED`/`FAIL`, plus opt-in `--verbose` and `--json`.
- **Provider SKILL.md & Reference Updates**:
  - Update each of the 6 `*-quality-check/SKILL.md` files (keeping strictly `name` + `description` frontmatter) to document the 4 profiles, unified capabilities, dual-floor coverage / `check_diff_coverage.py`, `standards_catalog.json`, optional `task_tier_b`/`triage_surfaces` hooks, and `--json`/`--verbose` validator CLI flags.
  - Ensure every new file under `skills/` (`_provider_manifest_common.py`, `check_diff_coverage.py`, `web-quality.schema.json`, `_stack_lifecycle_registry.py`) is referenced by a skill `SKILL.md` or tracked script so `scripts/verify.sh` §8 passes.

### 3. `setup_quality_check` Scaffolder and Templates

Update `skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py`, `skills/setup_quality_check/SKILL.md`, and templates (`polyglot-check-quality.template.json`, `web-quality.template.json`):

- Scaffold all **4 profiles** (`pr`, `epic`, `scheduled`, `release`) for every detected stack (`flutter`, `rust`, `web`, `python`, `android`, `ios`) and in `check_quality.json`.
- Scaffold unified capability placeholders/commands:
  - `pr`: fast static + unit + `pr_diff_audit` + `pr_impact` + `anti_stub` + `security` + diff-coverage command (using `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py`).
  - `epic`: full static + boundaries/architecture + test + dual-floor `coverage` + `anti_stub` + `security` + `pr_diff_audit` + `pr_impact`.
  - `scheduled`: full workspace sweep adding `security_deps`, `workspace_audit` (`--all-files`), `workspace_impact` (`--all-files`).
  - `release`: strict release gate combining `epic` + `security_deps` + `workspace_audit` + `workspace_impact`.
- Scaffold `"standards_catalog": ".agents/quality/standards_catalog.json"` and a starter `.agents/quality/standards_catalog.json` when absent (without overwriting existing files).
- Scaffold stack-appropriate `"pool_mounts"` in `check_quality.json` when Flutter (`packages/*/.dart_tool`, `.dart_tool` with `cow_copy`) or mobile secret configs are detected.
- **Remove** `"cleanup": ["pkill", "-9", "java"]` from Android scaffolding completely.

## Component 4 Lifecycle Documentation and Tier C1 vs Tier C2 Standardization

Update five lifecycle instruction files (preserving frontmatter rules and `d3nexus:` namespace):

1. `skills/dev-designer/SKILL.md`
2. `skills/dev-designer/references/verification-rows.md`
3. `skills/dev-designer/references/verification-row-grammar.md`
4. `skills/dev-implementation/SKILL.md`
5. `skills/dev-implementation/references/worker-execution-rules.md`

### Required Documentation Updates

- Replace hardcoded Python-only fixer/tier examples (`uv run pytest ...`) with a concise 6-stack platform-mapped command table (`python`, `flutter`, `rust`, `web`, `android`, `ios`).
- Explicitly standardize the **Tier C1 vs Tier C2** split (`TierCTaxonomy`):
  - **`Tier C1` (Mandatory Subcutaneous / Host-VM Integration, `< 5s`)**: Runs in every task/epic without hardware or browser infrastructure — e.g., `flutter test test/integration/*_integration_test.dart` (Flutter in-memory Drift/BLoC/widget integration), `cargo nextest run --test '*'` (Rust integration tests), Vitest/Node wire & DOM contract tests (Web), `uv run pytest tests/integration/` (Python), JVM/Robolectric `*FlowTest` via `./gradlew :<module>:testDebugUnitTest` (Android), `swift test --filter *FlowTests` (iOS host integration).
  - **`Tier C2` (`Needs:`-Gated Live E2E / Device / Browser)**: Requires external runtime declared via `Needs:` (`FLUTTER_DEVICE`, `ANDROID_DEVICE`, `IOS_SIMULATOR`, `PLAYWRIGHT_BROWSER`, `DOCKER_LIVE`) — e.g., Flutter `integration_test/` on simulator/emulator, Playwright headless Chromium E2E, Android `connectedDebugAndroidTest`, iOS `xcodebuild test` on Simulator, live DB/network E2E.
- Document `TierBContractAdapter` polyglot verification row requirements, `TierCTaxonomy` (`Integration test roots:` + `Needs:` gating for Tier C2), `PoolWorkspaceStrategy` (`symlink` vs `apfs_cow_tree`), `TriageSurfaceRegistry` suffix isolation, compact one-line `PASS` validator output (`--verbose` / `--json`), and `{skills_dir}/quality_check/resources/scripts/check_diff_coverage.py` invocation.

## Failure Modes and Risk Mitigations

| Risk / Failure Mode | Root Cause | Mitigation |
| :--- | :--- | :--- |
| APFS clone failure (`cp -c -R`) on Linux or cross-filesystem mounts | `cp -c` is macOS APFS-only and fails on ext4/tmpfs or cross-volume copies | Detect `sys.platform == "darwin"`, probe `cp -c -R` and gracefully fall back to `shutil.copytree(..., symlinks=False, dirs_exist_ok=True)` on non-zero returncode |
| Accidental staging/commit of `cow_copy` secrets (`secureFiles/`, `local.properties`, `*.xcconfig`) or `.dart_tool` | Unlike symlinks, real copied files inside a slot can be swept by `git add -A` if not gitignored or explicitly excluded | Exclude every active mount path across all 4 pool operations (`sync_slot` `git clean -fd -e`, `capture_slot_tree_sha`, `triage_fix_slot`, and `finalize_slot` unstage) and never copy tracked files |
| Path traversal via malicious `"pool_mounts"`, `"standards_catalog"`, or HLD `Integration test roots:` | User-edited JSON/HLD containing `../` or `/etc/...` | Validate all relative paths with `Path.resolve().is_relative_to(repo_root)` and reject `..` or absolute paths in validators, `PoolWorkspaceStrategy`, and `TierCTaxonomy` |
| Breaking existing consumer manifests or existing kit tests | Tightening schema `required` arrays or changing default CLI stdout without checking existing test assertions | Strict additive v1 compatibility for schemas/validators; update the 3 `test_check_task_contract.py` implicit-protected-path tests to pass `--verbose` while adding dedicated tests for default 1-line `PASS` stdout across all CLIs |
| Cross-stack false positives in `TierBContractAdapter`, `TierCTaxonomy`, or `TriageSurfaceRegistry` | Matching global regexes, activating untouched stacks, or hard-failing heuristic Playwright rows | Strict suffix scoping in `TriageSurfaceRegistry`, exact intersection of `Allowed files` suffixes with active manifests in `TierBContractAdapter`, and hard-fail only on explicit `Tier C2` / `TIER-C2` rows missing `Needs:` (warning-only on heuristic heavy-runtime commands) |
| `scripts/verify.sh` §8 orphan file check or §5 forbidden prefix check | New scripts/schemas unreferenced in `SKILL.md` or accidental forbidden namespace strings | Reference every new script/schema in its owning `SKILL.md`, run `check_document.py`, and run `bash scripts/verify.sh --full` |

## Verification and Testing Strategy

All new and modified code will be covered by automated pytest suites registered in `scripts/verify.sh`:

1. **`tests/test_stack_lifecycle_registry.py`**:
   - Unit tests for all 6 built-in stacks across all 4 contracts (`TierBContractAdapter`, `PoolWorkspaceStrategy`, `TriageSurfaceRegistry`, `TierCTaxonomy`).
   - Manifest overlay tests (`task_tier_b`, `triage_surfaces` object merging + invalid regex rejection, `pool_mounts`, custom 7th stack via `extensions`, path traversal rejection).
2. **`skills/dev-implementation/resources/scripts/test_check_task_contract.py` (extended)**:
   - Polyglot single-task dispatch (`.rs` + `.ts`, `.py` + `.js`, `.dart` + `.rs`/`.kt`/`.swift`), 0% invocation on untouched stacks, `(new)` `.dart`/`.py` coverage, chained `&&`/`;` subcommand matching, conditional boundary triggers, and legacy Python fallback when no `.agents/quality/*-quality.json` exists.
   - `TierCTaxonomy` checks: explicit `Tier C2` row missing `Needs:` fails (`exit 1`); explicit `Tier C2` row with `Needs:` passes; heuristic heavy-runtime `TIER-C` command without `Needs:` emits warning without breaking exit code `0`; valid/invalid HLD `Integration test roots:`.
   - Compact 1-line `PASS` output contract (`Result: 0 problems — PASS` by default; `--verbose` prints `Implicit protected paths:`; `--json` returns structured payload).
3. **`tests/test_manage_worker_pool.py` (extended)**:
   - `apfs_cow_tree` / fallback copy for `.dart_tool`, `packages/*/.dart_tool`, `features/*/.dart_tool`, `bricks/*/hooks/.dart_tool`, `secureFiles/`, `local.properties`, `*.xcconfig`, and custom `pool_mounts`; symlink preservation for `target`/`node_modules`/`.venv`/etc.; verifying none are deleted by `sync_slot` or staged/committed by `finalize_slot`.
   - Suffix-scoped `triage-fix` verifying every stack's 5 surface categories trigger on matching suffixes and never cross-fire on other suffixes, plus polyglot `_is_test_file` and assertion weakening checks.
4. **`tests/test_check_diff_coverage.py`**:
   - Fixture tests for **LCOV**, **Cobertura XML**, and **JaCoCo XML** (auto-detection + explicit `--format`), hunk-level `--diff-base` / `--diff-files`, `--min-diff-coverage`, dual-floor (`--min-coverage`, `--min-package-coverage`, `--exclude-package-floor`), `--source-ext`, generated-code exclusions, untracked new-file fallback detection, and compact 1-line `PASS` vs expanded `FAIL` / `--verbose` / `--json` output.
5. **Schema, Validator & Scaffolder tests** (extended across `validate_quality_contract`, all 6 `test_validate_*_quality.py`, and `test_scaffold_quality_manifest.py`):
   - Validate additive v1 fields (`pool_mounts`, `standards_catalog`, `task_tier_b`, `triage_surfaces` object shape, dual-floor `coverage`, unified capabilities + `license`, 4 profiles), verify legacy manifests still pass, verify `web-quality.schema.json` matches fixtures, verify Android scaffolder omits `pkill -9 java`, and verify compact 1-line `PASS` vs `--verbose` / `--json` CLI output across all 7 validator CLIs.
6. **Full Quality Gate**:
   - `bash scripts/verify.sh --full`
   - `@quality_check` (`profile: epic` — `ruff format --check`, `ruff check`, `mypy`, `pytest tests`, `verify.sh`) with `PASS` and 0 findings.

## Non-Goals and Boundaries

- **No changes outside `ai-agent-tools`**: Consumer repositories (`nexus`, `D3Nexus`, `lyrics-sync`, `android_digital_wallet`, `ios_digital_wallet`) are not modified in this epic.
- **No `git push` or automated release**: `scripts/release.sh` and `git push` are strictly excluded; handoff will output the exact local sync command for `/Users/danhdueexoictif/.gemini/config/plugins/d3nexus` after merge.
- **No third-party Python packages**: Keep zero external runtime dependencies (`jsonschema` is not required at runtime; validators use Python stdlib).
- **No destructive live tool invocations in unit tests**: All tests run hermetic against temporary directories/git repos without requiring Dart, Cargo, Gradle, Xcode, or Playwright binaries on the test host.
