# Open-Closed Polyglot Lifecycle and Quality Architecture — Adversarial BDD Scenarios

- **Epic**: `polyglot_lifecycle_and_quality_architecture`
- **Prefix**: `PLQ`
- **Dimensions**: Happy Path (`HP`), Edge Cases (`EC`), State Transitions (`ST`), Architecture & Concurrency (`AR`), Fault Resilience (`FR`)

## Table of Contents

- [Dimension 1 Happy Path Scenarios](#dimension-1-happy-path-scenarios)
- [Dimension 2 Edge Cases and Boundary Conditions](#dimension-2-edge-cases-and-boundary-conditions)
- [Dimension 3 State Transitions and Idempotency](#dimension-3-state-transitions-and-idempotency)
- [Dimension 4 Architecture Isolation and Cross-Stack Safety](#dimension-4-architecture-isolation-and-cross-stack-safety)
- [Dimension 5 Fault Resilience and Security Hardening](#dimension-5-fault-resilience-and-security-hardening)

## Dimension 1 Happy Path Scenarios

```gherkin
Scenario: [PLQ-HP-01] [Tier C - Integration] Registry resolves all 6 built-in stacks and custom manifest overrides
Given a repository containing active quality manifests for python, flutter, rust, web, android, and ios
When TierBContractAdapter, PoolWorkspaceStrategy, TriageSurfaceRegistry, and TierCTaxonomy are initialized from the repository root
Then each of the 6 stack families resolves its exact file extensions, default Tier B policy, suffix-scoped SurfaceRuleSet, and Tier C policy
And an optional custom manifest declaring extensions [".go"] and task_tier_b format_prefixes ["gofmt -l"] is activated for ".go" Allowed files without modifying Python kit code

Scenario: [PLQ-HP-02] [Tier C - Integration] Portable diff-coverage engine evaluates LCOV, Cobertura XML, and JaCoCo XML with compact one-line PASS
Given temporary repositories containing valid LCOV, Cobertura XML, and JaCoCo XML coverage reports covering >= 85% of modified source hunks and >= 80% workspace lines
When check_diff_coverage.py is executed with --format auto, --min-coverage 75, --min-package-coverage 60, --diff-files, and --min-diff-coverage 80
Then each invocation exits with code 0
And stdout contains exactly one line starting with "PASS:" and reporting both coverage percentage and diff percentage
And re-running with --json prints valid JSON containing status "PASS", coverage_pct, and diff_coverage_pct

Scenario: [PLQ-HP-03] [Tier C - Integration] Scaffolder generates 4-profile unified manifests and validators emit compact one-line PASS
Given a polyglot repository containing Cargo.toml, pubspec.yaml, package.json, pyproject.toml, build.gradle.kts, and Package.swift
When scaffold_quality_manifest.py scaffolds check_quality.json, all 6 <stack>-quality.json manifests, and standards_catalog.json
Then every generated manifest defines all 4 profiles ("pr", "epic", "scheduled", "release"), unified capabilities ("anti_stub", "security", "security_deps", "pr_diff_audit", "workspace_audit", "pr_impact", "workspace_impact", "license"), "standards_catalog", dual-floor coverage referencing check_diff_coverage.py, and Android omits "cleanup" ("pkill -9 java")
And validate_quality_contract.py registry returns valid JSON containing "status": "PASS" and selected "providers" (with --compact emitting a single "PASS:" line), while validate_quality_contract.py capability and all 6 validate_<stack>_quality.py CLIs exit 0 with a single stdout line starting with "PASS:"

Scenario: [PLQ-HP-04] [Tier C - Integration] Polyglot task contract passes when all touched stacks satisfy Tier B and emits one-line PASS
Given a repository with active rust-quality.json and web-quality.json manifests and a task whose Allowed files touch both "crates/core/src/lib.rs" and "apps/web/src/app.ts"
When check_task_contract.py --design validates the task containing chained TIER-B commands covering cargo fmt --check, cargo clippy -D warnings, eslint, and tsc --noEmit
Then check_task_contract.py exits with code 0
And default stdout is exactly one line: "Result: 0 problems — PASS"
And re-running with --verbose appends the "Implicit protected paths:" line before the Result line

Scenario: [PLQ-HP-05] [Tier C - Integration] Worker pool materializes symlink caches and APFS/copytree COW trees without symlinking .dart_tool
Given a main worktree containing target/, node_modules/, .dart_tool/, packages/core/.dart_tool/, features/home/.dart_tool/, bricks/feat/hooks/.dart_tool/, and gitignored secureFiles/dev.json and android/local.properties
When manage_worker_pool.py creates and syncs slot 1
Then target and node_modules in slot 1 are symlinks pointing to the main worktree
And root .dart_tool, packages/core/.dart_tool, features/home/.dart_tool, bricks/feat/hooks/.dart_tool, secureFiles, and android/local.properties in slot 1 are real copied directories or files (is_symlink() is False)
And git status --porcelain inside slot 1 remains clean with zero untracked secret or .dart_tool noise

Scenario: [PLQ-HP-06] [Tier C - Integration] Lifecycle docs, provider skills, and verify.sh registry pass full structural and word-cap checks
Given all updated dev-designer, dev-implementation, quality_check, setup_quality_check, and 6 stack quality-check SKILL.md files plus scripts/verify.sh
When end-to-end documentation, frontmatter, reference-reachability, and Tier C1/Tier C2 contract assertions execute
Then dev-implementation/SKILL.md stays <= 4500 words and dev-designer/SKILL.md stays <= 22528 UTF-8 bytes
And every newly created script and schema under skills/ is referenced by at least one tracked file
And all 6 new polyglot test suites are registered in scripts/verify.sh SUITES
```

## Dimension 2 Edge Cases and Boundary Conditions

```gherkin
Scenario: [PLQ-EC-01] [Tier C - Integration] Untouched stack manifests incur zero Tier B checks
Given a polyglot repository with active flutter-quality.json, rust-quality.json, and python-quality.json manifests
When TierBContractAdapter validates a task whose Allowed files only modify "crates/core/src/calc.rs"
Then only the rust adapter is dispatched
And zero flutter (dart format / dart analyze) or python (ruff / mypy) problems are emitted

Scenario: [PLQ-EC-02] [Tier C - Integration] Flutter and Python (new) files require explicit format coverage before git add
Given a repository with flutter-quality.json and a task whose Allowed files include "lib/new_widget.dart (new)" and "lib/existing.dart"
When the TIER-B dart format row only names "lib/existing.dart" and omits "lib/new_widget.dart"
Then TierBContractAdapter reports a missing format coverage problem naming "lib/new_widget.dart"

Scenario: [PLQ-EC-03] [Tier C - Integration] Untested new source file triggers fallback executable-line diff-coverage failure
Given a git repository with a newly added untracked source file "src/new_service.py" containing 10 executable statements and 0 entries in coverage.xml
When check_diff_coverage.py runs with --diff-base HEAD --min-diff-coverage 80 --source-ext .py
Then check_diff_coverage.py exits with code 1
And stdout reports "FAIL:" along with "src/new_service.py" and its uncovered executable line count

Scenario: [PLQ-EC-04] [Tier C - Integration] Generated files and excluded packages are omitted from dual-floor enforcement
Given an LCOV report containing 0% coverage for "packages/core/lib/model.g.dart" and 45% coverage for "packages/legacy/lib/old.dart" alongside 90% coverage for "packages/core/lib/service.dart"
When check_diff_coverage.py runs with --min-coverage 75 --min-package-coverage 60 --exclude-package-floor legacy
Then generated ".g.dart" lines are excluded from coverage denominators
And "legacy" is skipped for the per-package floor while "core" passes at 90%
And check_diff_coverage.py exits with code 0

Scenario: [PLQ-EC-05] [Tier C - Integration] Legacy v1 manifests without scheduled/release or new additive fields still pass validation
Given legacy check_quality.json and all 6 legacy <stack>-quality.json fixtures containing only schema_version 1, pr/epic profiles, and original capability keys
When validate_quality_contract.py and all 6 validate_<stack>_quality.py validators run for profile "pr" and "epic"
Then every validator returns status "PASS" with 0 findings

Scenario: [PLQ-EC-06] [Tier C - Integration] Python tasks retain check_python_tier_b enforcement without python-quality.json or with only non-Python manifests
Given a temporary git repository with no .agents/quality directory and another temporary git repository with only .agents/quality/flutter-quality.json (no python-quality.json), each having a task whose Allowed files touch "src/app.py"
When check_task_contract.py --design validates each task with a missing mypy row
Then check_python_tier_b reports the missing Python type-check problem and exits with code 1 in both repositories
```

## Dimension 3 State Transitions and Idempotency

```gherkin
Scenario: [PLQ-ST-01] [Tier C - Integration] Scaffolder does not overwrite existing standards_catalog.json and validates all 4 profiles
Given a repository that already contains a customized ".agents/quality/standards_catalog.json" with sentinel content "CUSTOM-RULE-01"
When scaffold_quality_manifest.py runs on that repository
Then ".agents/quality/standards_catalog.json" retains "CUSTOM-RULE-01" byte-for-byte
And generated provider manifests reference ".agents/quality/standards_catalog.json" and validate PASS across profiles "pr", "epic", "scheduled", and "release"

Scenario: [PLQ-ST-02] [Tier C - Integration] TierCTaxonomy distinguishes explicit Tier C2 missing Needs from heuristic heavy-runtime warning
Given an epic with a task having a TIER-C row whose Command ends with "# tier: C2" and empty Needs ("—") and another task having an unlabeled "npx --no-install playwright test" TIER-C row with empty Needs ("—")
When check_task_contract.py --design validates the first task
Then it exits with code 1 and reports an explicit Tier C2 missing Needs problem
When check_task_contract.py --design validates the second task
Then it exits with code 0 and emits a non-blocking Tier C2 warning to stderr suggesting a Needs variable

Scenario: [PLQ-ST-03] [Tier C - Integration] Repeated sync_slot preserves COW mounts and never deletes them during git clean
Given slot 1 with materialized .dart_tool, packages/core/.dart_tool, and gitignored secureFiles/dev.json plus an unrelated stale untracked file "scratch.tmp"
When manage_worker_pool.py runs sync_slot twice consecutively on slot 1
Then "scratch.tmp" is removed by git clean -fd
And .dart_tool, packages/core/.dart_tool, and secureFiles/dev.json remain intact as non-symlink directories/files after both syncs

Scenario: [PLQ-ST-04] [Tier C - Integration] finalize_slot unstages ignored mounts while committing edits to tracked xcconfig files
Given slot 1 containing a legitimate source edit, an edited git-tracked "ios/Flutter/Debug.xcconfig", plus materialized gitignored cow_copy mounts (.dart_tool, secureFiles/dev.json, android/local.properties) and a custom gitignored pool_mounts cow_copy entry
When manage_worker_pool.py runs capture_slot_tree_sha and finalize_slot on slot 1
Then the resulting slot commit contains both the legitimate source edit and the tracked "ios/Flutter/Debug.xcconfig" edit
And git show --stat HEAD contains zero paths from .dart_tool, secureFiles, android/local.properties, or custom gitignored pool_mounts

Scenario: [PLQ-ST-05] [Tier C - Integration] End-to-end polyglot lifecycle pipeline transitions cleanly from scaffold to contract check to pool triage
Given a synthetic polyglot repo (Flutter + Rust + Python) initialized via scaffold_quality_manifest.py
When check_task_contract.py validates a polyglot task, manage_worker_pool.py syncs and triages a low-risk fix in slot 1, and check_diff_coverage.py checks a passing LCOV + Cobertura diff
Then every CLI stage exits with code 0 and emits compact one-line PASS summaries where applicable
```

## Dimension 4 Architecture Isolation and Cross-Stack Safety

```gherkin
Scenario: [PLQ-AR-01] [Tier C - Integration] Suffix-scoped TriageSurfaceRegistry isolates stack rules while preserving language-neutral baselines
Given a Dart file containing "unsafe fn" and "tokio::spawn", a Rust file containing "MethodChannel" and "DriftDatabase", a Kotlin file containing "XCTSkip", "Codable", and "private fun helper()", a ".sql" migration containing "ALTER TABLE users ADD COLUMN role TEXT;", and a Dart file declaring "class AuthService {"
When TriageSurfaceRegistry evaluates each added line by its file suffix
Then zero surface triggers fire on the cross-language strings or Kotlin "private fun helper()"
And the ".sql" "ALTER TABLE" line fires "DB_OR_PERSISTENCE_CHANGED" and the Dart "class AuthService {" line fires "PUBLIC_SIGNATURE_CHANGED"
And matching native-stack edits (Dart MethodChannel, Rust unsafe/sqlx::query, TS fetch(/Worker(, Kotlin public fun/RoomDatabase/@Ignore, Swift actor/XCTSkip, Python FastAPI/pytest.mark.skip) each fire their exact corresponding trigger code

Scenario: [PLQ-AR-02] [Tier C - Integration] Web provider schema matches draft 2020-12 parity with the other 5 provider schemas
Given all 6 provider JSON schemas (flutter, rust, web, python, android, ios) under skills/*-quality-check/resources/schemas/
When the test suite inspects each schema's top-level properties, capabilities properties, coverage properties, and profile keys
Then all 6 schemas declare additionalProperties: false, schema_version const 1, profiles pr/epic/scheduled/release, unified capabilities (anti_stub, security, security_deps, pr_diff_audit, workspace_audit, pr_impact, workspace_impact, license), dual-floor coverage keys, standards_catalog, extensions, task_tier_b, and object-shaped triage_surfaces

Scenario: [PLQ-AR-03] [Tier C - Integration] Conditional boundary checks activate only when domain or manifest boundary files change
Given active manifests for flutter, rust, android, and ios
When check_task_contract.py validates tasks touching "packages/core/lib/domain/entity.dart", "crates/domain/Cargo.toml", "feature/wallet/domain/UseCase.kt", or "Packages/Core/Package.swift" without boundary/architecture TIER-B rows
Then check_task_contract.py reports the missing stack-specific boundary check for each task
And when a task only touches non-domain presentation/utility files without manifest edits, no boundary check problem is emitted

Scenario: [PLQ-AR-04] [Tier C - Integration] Polyglot _is_test_file classifies test files and assertion weakening accurately per language
Given a Fix Pass 1 diff in manage_worker_pool.py triage-fix that removes an expect() call or adds skip: true in a Dart *_test.dart file, #[ignore] in a Rust *_test.rs file, .skip( in a *.spec.ts file, @Ignore in a *Test.kt file, or XCTSkip in a *Tests.swift file
When triage_fix_slot evaluates the diff
Then each case classifies the file as a test file (0 non-test changed lines) and fires "TEST_ASSERTION_WEAKENED" with tier1_status "HIGH_RISK"

Scenario: [PLQ-AR-05] [Tier C - Integration] Documentation cross-references obey d3nexus namespace and exclude forbidden prefixes
Given all modified SKILL.md and references/*.md files in dev-designer, dev-implementation, quality_check, setup_quality_check, and the 6 *-quality-check skills
When frontmatter, markdown lint (check_document.py), and namespace checks run
Then every SKILL.md frontmatter contains exclusively "name" and "description"
And zero files under skills/ contain the forbidden "superpowers:" prefix
And dev-designer/references/verification-rows.md preserves "-q --tb=short --maxfail=3" alongside 6-stack Tier C1/Tier C2 examples
```

## Dimension 5 Fault Resilience and Security Hardening

```gherkin
Scenario: [PLQ-FR-01] [Tier C - Integration] Path traversal in pool_mounts or malformed regex in triage_surfaces is rejected safely
Given a check_quality.json containing pool_mounts path "../outside_secret" and a flutter-quality.json containing triage_surfaces signature pattern "[unclosed-regex"
When PoolWorkspaceStrategy and TriageSurfaceRegistry load these manifests
Then PoolWorkspaceStrategy rejects "../outside_secret" without accessing any path outside repo_root
And TriageSurfaceRegistry skips or surfaces a clear validation error for "[unclosed-regex" without raising an unhandled re.error crash

Scenario: [PLQ-FR-02] [Tier C - Integration] Malformed or missing coverage reports return exit code 2 BLOCKED cleanly
Given a missing report path and a corrupt XML file "<broken"
When check_diff_coverage.py runs against either input
Then check_diff_coverage.py exits with code 2
And output starts with "BLOCKED:" naming the offending report path without a Python traceback

Scenario: [PLQ-FR-03] [Tier C - Integration] Validators reject invalid pool_mounts, standards_catalog traversal, non-object triage_surfaces, and bad regexes
Given a check_quality.json with pool_mounts mode "hardlink" and path "/etc/passwd", and a python-quality.json with standards_catalog "../escape.json", triage_surfaces as a JSON array instead of an object, and an invalid regex in triage_surfaces.api_wire
When validate_quality_contract.py and validate_python_quality.py validate these configs
Then both return status "BLOCKED" with deterministic finding codes and exit code 1 in CLI mode

Scenario: [PLQ-FR-04] [Tier C - Integration] Invalid HLD Integration test roots with path traversal or missing targets fail check_task_contract
Given an Epic HLD declaring "Integration test roots: ../escape, nonexistent_dir/"
When check_task_contract.py --design validates the HLD and tasks
Then check_task_contract.py exits with code 1 and reports explicit problems for both "../escape" (path traversal) and "nonexistent_dir/" (no matching tracked or planned files)

Scenario: [PLQ-FR-05] [Tier C - Integration] APFS copy-on-write failure gracefully falls back to shutil.copytree on non-APFS or Linux hosts
Given a simulated environment where `cp -c -R` returns exit code 1 (e.g., cross-volume or Linux host)
When manage_worker_pool.py materializes .dart_tool and secureFiles/dev.json into slot 1
Then PoolWorkspaceStrategy falls back to shutil.copytree / shutil.copy2 automatically
And slot 1 contains complete, readable, non-symlink copies of .dart_tool and secureFiles/dev.json with zero exceptions
```
