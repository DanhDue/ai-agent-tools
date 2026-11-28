# Shift-Left Quality Layer Resolver and Mechanical Contract Enforcement — Adversarial BDD Scenarios

- **Epic**: `shift_left_quality_resolver`
- **Prefix**: `SLQR`
- **Dimensions**: Happy Path (`HP`), Edge Cases (`EC`), State Transitions (`ST`), Architecture and Isolation (`AR`), Fault Resilience (`FR`)

## Table of Contents

- [Dimension 1 Happy Path Scenarios](#dimension-1-happy-path-scenarios)
- [Dimension 2 Edge Cases and Boundary Conditions](#dimension-2-edge-cases-and-boundary-conditions)
- [Dimension 3 State Transitions and Idempotency](#dimension-3-state-transitions-and-idempotency)
- [Dimension 4 Architecture Isolation and Zero-Bloat Boundaries](#dimension-4-architecture-isolation-and-zero-bloat-boundaries)
- [Dimension 5 Fault Resilience and Fail-Closed Contract Guards](#dimension-5-fault-resilience-and-fail-closed-contract-guards)

## Dimension 1 Happy Path Scenarios

```gherkin
Scenario: [SLQR-HP-01] [Tier C - Integration] Provider schemas and runtime validators accept additive test_routing, package_floors, architecture, and cache capabilities
Given all 6 stack JSON Schemas ("*-quality.schema.json") and runtime validators ("validate_*_quality.py")
When manifests declaring optional "test_routing", "coverage.package_floors", Flutter "architecture", and Rust/Web/Python "cache_enable" and "cache_purge" are validated across profiles ("pr", "epic", "scheduled", "release")
Then all 6 runtime validators return status "PASS" with 0 findings
And every capability key emitted by scaffold_quality_manifest.py, present in repository/template manifests, or added for Flutter ("architecture") and Rust/Web/Python ("cache_enable", "cache_purge") exists in the corresponding JSON Schema "capabilities.properties" alongside top-level "test_routing" and "coverage.properties.package_floors"

Scenario: [SLQR-HP-02] [Tier C - Integration] Scaffolder and web template generate deduplicated offline-safe 4-profile manifests and check_diff_coverage enforces package_floors ratchets
Given a polyglot temporary repository containing markers for all 6 stacks, "skills/setup_quality_check/resources/templates/web-quality.template.json", and a ".agents/quality/coverage_floors.json" defining adapter floor "src/pkg/align": 0.88 and module floor "src/web/studio.js": 0.50
When scaffold_quality_manifest.py runs and check_diff_coverage.py evaluates LCOV/Cobertura reports with "--package-floors .agents/quality/coverage_floors.json"
Then every generated stack manifest and "web-quality.template.json" has 0 duplicate audit or impact invocations per profile ("pr_diff_audit" and "pr_impact" in "pr" only; "workspace_audit" and "workspace_impact" in "epic", "scheduled", and "release")
And generated Web capabilities and "web-quality.template.json" use "npx --no-install" and omit "test_e2e" from "scheduled", generated Rust "pr" and "epic" profiles omit "cargo audit", and generated Python "type_check" targets ["uv", "run", "mypy", "--strict", "src", "tests"]
And check_diff_coverage.py returns exit code 0 when "src/pkg/align" is at 90.0% and "src/web/studio.js" is at 55.0%, and returns exit code 1 naming the breached ratchet when either drops below its floor

Scenario: [SLQR-HP-03] [Tier C - Integration] d3nexus resolve-quality emits compact file-scoped guidance within latency budgets
Given a polyglot repository configuring ".agents/quality/python-quality.json", ".agents/quality/web-quality.json" (with V8 LCOV diff_coverage on ".js,.mjs" and ui_review), ".agents/quality/coverage_floors.json", and "src/preview/static/index.html" referencing "align-studio.js?v=20261128"
When resolve_quality_plan() executes in-process and "bin/d3nexus resolve-quality --files src/lyrics_sync/align/ctc.py src/preview/static/align-studio.js --base-ref develop" executes via CLI
Then in-process resolve_quality_plan() completes in under 0.10 seconds (best of 3 runs) and the CLI subprocess exits 0 in under 1.0 second printing between 5 and 10 non-empty lines
And the output specifies canonical test roots for Python and dual Web test requirements (V8 LCOV unit test in "tests/js/*.test.mjs" plus Playwright "# tier: C2")
And the output lists matched adapter/module floors from "coverage_floors.json", names "src/preview/static/index.html" for "?v=" cache-busting, and emits "$D3NEXUS_KIT/skills"-interpolated scoped TIER-B commands

Scenario: [SLQR-HP-04] [Tier C - Integration] check_task_contract validates multi-target mypy and skills_dir commands in both --design and --check-plan modes
Given a repository whose "python-quality.json" sets type_check to ["uv", "run", "mypy", "--strict", "src", "tests"] and lint to ["uv", "run", "ruff", "check", "--extend-select", "F821,B904", "."] and whose "web-quality.json" sets type_check to ["python3", "{skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py", "--target-dir", "src/preview"] without a manual task_tier_b override
When check_task_contract.py runs "--design" on epic tasks and "--check-plan" on a standalone plan whose commands scope ruff and mypy to Allowed ".py" files, expand "$D3NEXUS_KIT/skills/.../check_vanilla_js.py", include a "tests/js/*.test.mjs" unit test, and include referencing "?v=" HTML templates
Then both "--design" and "--check-plan" exit 0 with "Result: 0 problems — PASS"

Scenario: [SLQR-HP-05] [Tier C - Integration] Updated skills pass byte/word caps, clean-shell Pre-Flight execution, and multi-stack ecosystem profile validations
Given the updated skill files ("dev-designer/SKILL.md", "dev-designer/references/verification-rows.md", "writing-plans/SKILL.md", "writing-plans/plan-document-reviewer-prompt.md", "finishing-a-development-branch/SKILL.md") and "scripts/verify.sh"
When clean-shell Pre-Flight commands, check_document.py --require-toc, UTF-8 byte/word cap checks, and 5-repo ecosystem manifest validations (via optional SLQR_ECOSYSTEM_ROOT or synthetic 5-repo polyglot fixtures) execute
Then "skills/dev-designer/SKILL.md" stays <= 22528 UTF-8 bytes, retired script names ("verify_importlinter_coverage.py", "pre_review_self_probe.py", "verify_bdd_coverage.py") do not appear in "dev-designer", all discovered ecosystem profiles return "PASS" with zero personal-path leaks in tracked files, and embedded CLI commands exit 0 in a clean env shell
```

## Dimension 2 Edge Cases and Boundary Conditions

```gherkin
Scenario: [SLQR-EC-01] [Tier C - Integration] Registry prefix matcher and TierBContractAdapter unwrap monorepo directory flags, mise exec prefixes, and relocated script paths while rejecting mismatched directories
Given stack manifests declaring "uv --directory apps/align-worker run ruff check .", "mise exec -- swiftlint lint --config quality/.swiftlint.yml --strict", and "python3 {skills_dir}/web-quality-check/resources/scripts/check_vanilla_js.py --target-dir src/preview"
When _subcommand_matches_prefix evaluates Python subcommands "uv --directory apps/align-worker run ruff check src/mod.py" and "uv --directory apps/other-worker run ruff check src/mod.py" against the Python manifest prefixes, and TierBContractAdapter.validate_tier_b evaluates iOS and Web task TIER-B rows using "swiftlint lint --config quality/.swiftlint.yml --strict Packages/Core/Sources/Foo.swift" and "python3 \"$D3NEXUS_KIT/skills/web-quality-check/resources/scripts/check_vanilla_js.py\" --target-dir src/preview"
Then the matching Python "--directory apps/align-worker" subcommand and both iOS and Web TIER-B rows match with 0 problems, while the mismatched "--directory apps/other-worker" subcommand fails to match any prefix (including wrapper-less built-in defaults)

Scenario: [SLQR-EC-02] [Tier C - Integration] check_diff_coverage handles missing or malformed package_floors file as exit 2 BLOCKED and exempts unmeasured files cleanly
Given a valid LCOV report covering "src/core/service.py" at 95.0%
When check_diff_coverage.py runs with "--package-floors missing_floors.json" or a corrupt JSON file
Then check_diff_coverage.py exits with code 2 and status "BLOCKED" without an unhandled Python traceback

Scenario: [SLQR-EC-03] [Tier C - Integration] Bundled ES module imports without src/href template attributes do not trigger false-positive cache-bust template requirements
Given a Web repository with "ui_review" enabled where "apps/web/src/store.ts" and "apps/web/src/helper.js" are imported via ES "import" statements and never referenced in "<script src=...>" or "<link href=...>" attributes inside ".astro" or ".html" templates
When resolve_task_quality_plan.py and check_task_contract.py evaluate a task modifying "apps/web/src/helper.js" (with a paired ".test.mjs" unit test)
Then cache_bust_templates is empty and check_task_contract.py exits 0 without demanding unrelated ".astro" or ".html" templates

Scenario: [SLQR-EC-04] [Tier C - Integration] Final epic task (Task N) and pyproject.toml edits are permitted to run workspace-wide Python static checks
Given a 2-task Python epic where Task 1 modifies only "src/pkg/a.py" and Task 2 (the final task) or a task modifying "pyproject.toml" runs "uv run mypy --strict src tests"
When check_task_contract.py --design validates the epic
Then Task 2 (final task) and any task listing "pyproject.toml" in Allowed files pass without a full-repo TIER-B scope error, whereas Task 1 fails if it uses bare "src tests" instead of Allowed files
```

## Dimension 3 State Transitions and Idempotency

```gherkin
Scenario: [SLQR-ST-01] [Tier C - Integration] Non-passing epic or release quality run unlinks stale gate4_receipt.json while pr run preserves isolation
Given a repository where a prior "verify_polyglot_registry.py --profile epic --execute" run succeeded and wrote "build/quality/gate4_receipt.json" with status "PASS"
When a subsequent "--profile epic --execute" (or "--profile release --execute") run finishes with status "FAIL" or "BLOCKED"
Then "build/quality/gate4_receipt.json" is immediately unlinked and no longer exists on disk

Scenario: [SLQR-ST-02] [Tier C - Integration] integrate_branch verify-tier surfaces dirty working tree warning when uncommitted edits exist on a noop branch
Given a feature branch whose HEAD matches its backup ref ("tier == noop") but contains uncommitted modifications to a tracked source file
When "integrate_branch.py verify-tier --base main --format json" executes
Then the JSON report includes a non-empty warning stating that the worktree has uncommitted changes so callers do not blindly reuse a clean-SHA receipt

Scenario: [SLQR-ST-03] [Tier C - Integration] Fixing violations in a standalone Markdown plan transitions check_task_contract --check-plan from exit 1 FAIL to exit 0 PASS idempotently
Given a standalone Markdown plan in "docs/superpowers/plans/2026-11-28-demo.md" initially containing literal "{skills_dir}", bare "npx playwright test", and a modified ".js" asset missing both its ".test.mjs" LCOV test and referencing "index.html"
When check_task_contract.py --check-plan runs before and after remediating those four defects
Then the initial run exits 1 reporting all four distinct contract problems and repeated post-fix runs exit 0 idempotently with "Result: 0 problems — PASS"
```

## Dimension 4 Architecture Isolation and Zero-Bloat Boundaries

```gherkin
Scenario: [SLQR-AR-01] [Tier C - Integration] Stack lifecycle registry and quality plan resolver maintain zero circular imports and Python 3 stdlib purity
Given "skills/dev-implementation/resources/scripts/_stack_lifecycle_registry.py" and "skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py"
When AST imports are inspected and both modules are imported in a clean Python 3 stdlib environment without third-party packages
Then neither module imports "check_task_contract" or "manage_worker_pool", and 100% of imported modules belong to the Python 3 standard library or "_stack_lifecycle_registry"

Scenario: [SLQR-AR-02] [Tier C - Integration] Single-stack Python invocation of resolve-quality emits zero lines mentioning Web, Flutter, Android, iOS, or Rust
Given a polyglot repository containing manifests for all 6 stacks ("python", "web", "flutter", "android", "ios", "rust")
When "d3nexus resolve-quality --files src/worker/pipeline.py tests/unit/worker/test_pipeline.py" executes
Then stdout contains Python test roots, floors, and scoped TIER-B commands, and contains 0 occurrences of "playwright", "lcov", "flutter", "gradlew", "swiftlint", or "clippy"

Scenario: [SLQR-AR-03] [Tier C - Integration] Repositories without .agents/quality manifests bypass manifest-only Shift-Left guards without false positives
Given a minimal Git repository without a ".agents/quality/" directory containing an epic HLD and Python task file with valid scoped ruff and mypy TIER-B rows
When check_task_contract.py --design executes against that repository
Then manifest-specific LCOV, test_routing, and cache-bust guards self-skip cleanly and check_task_contract.py exits 0

Scenario: [SLQR-AR-04] [Tier C - Integration] Authoring skills integrate CLI resolver in 2-3 lines without embedding multi-stack prose matrices
Given "skills/dev-designer/SKILL.md" and "skills/writing-plans/SKILL.md"
When their diff and content are audited
Then both files reference "resolve-quality" (or "resolve_task_quality_plan.py"), "writing-plans/SKILL.md" and "plan-document-reviewer-prompt.md" reference "--check-plan", and neither skill embeds a multi-stack coverage floor table
```

## Dimension 5 Fault Resilience and Fail-Closed Contract Guards

```gherkin
Scenario: [SLQR-FR-01] [Tier C - Integration] Provider manifest validators fail closed on invalid test_routing keys or path traversal globs
Given a provider manifest containing unknown key "test_routing.rogue_key" or traversal glob "test_routing.canonical_test_globs": ["../outside/test_*.py"]
When validate_additive_provider_fields runs via any stack validator
Then validation fails closed with status "BLOCKED" and finding code "invalid_test_routing"

Scenario: [SLQR-FR-02] [Tier C - Integration] verify_polyglot_registry handles missing or read-only receipt cleanup gracefully without masking FAIL verdict
Given a repository with no pre-existing "build/quality/gate4_receipt.json"
When "verify_polyglot_registry.py --profile epic --execute" finishes with a provider "FAIL"
Then verify_polyglot_registry returns overall status "FAIL" cleanly without raising FileNotFoundError during receipt cleanup

Scenario: [SLQR-FR-03] [Tier C - Integration] resolve_task_quality_plan exits 2 with clear diagnostic on malformed quality manifest JSON
Given a repository whose ".agents/quality/web-quality.json" contains truncated invalid JSON
When "d3nexus resolve-quality --files src/web/app.js" executes
Then the CLI exits with code 2 and prints a descriptive error message to stderr naming "web-quality.json"

Scenario: [SLQR-FR-04] [Tier C - Integration] check_task_contract --design fails closed on each independent Shift-Left violation with distinct guard diagnostics
Given a polyglot repository with LCOV Web diff_coverage, "ui_review", and Python/Web "test_routing" rules ("forbidden_test_globs": ["tests/test_*.py", "scripts/test_*.py"], "paired_source_globs": ["src/api/**/*.py"])
When check_task_contract.py --design evaluates negative task fixtures separately testing: (1) Playwright-only Web task touching "src/static/app.js" without a JS unit test, (2) new test placed at forbidden "tests/test_rogue.py", (3) new "src/api/routes.py" missing a paired unit test, (4) modified "src/static/app.js" omitting referencing "src/static/index.html" ("?v="), and (5) unexpanded "{skills_dir}" in TIER-B
Then each of the five negative fixtures exits 1 and reports the exact diagnostic corresponding to that specific guard mechanism
```
