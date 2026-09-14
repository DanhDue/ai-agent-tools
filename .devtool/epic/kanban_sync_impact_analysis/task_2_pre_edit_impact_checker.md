---
id: "task_2_pre_edit_impact_checker"
status: "todo"
priority: "high"
assignee: null
epic: "kanban-sync-impact-analysis"
dueDate: null
created: "2026-09-15T02:30:00Z"
modified: "2026-09-15T02:30:00Z"
completedAt: null
labels: ["tooling", "impact-analysis", "git", "blast-radius"]
order: "a2"
---

# Task 2: Build Pre-Edit Impact and Conflict Checker Engine

Epic: [kanban-sync-impact-analysis](kanban_sync_impact_analysis.en.md)

## Requirement Analysis
In mobile multi-module architectures (Flutter, Android Clean Architecture + MVI, iOS SwiftPM/Tuist), modifying core or shared files without pre-edit visibility causes:
1. Painful upstream git merge conflicts if the target file has evolved on `<base_ref>`.
2. Silent compilation or behavior breakage in downstream consumer modules (BLoCs, ViewModels, Route Providers).
3. Untracked regressions in native platform channels (`MethodChannel` strings mismatching between Flutter Dart and Kotlin/Swift).
4. Breaking legacy code that lacks unit test protection (blind spots).

This task implements the core analysis engine `check_code_impact.py` and its test suite `test_check_code_impact.py` covering the 4-layer impact pipeline:
- **Layer 1: Upstream Divergence Detection**: Determines the merge base with `<base_ref>` dynamically, inspecting `git log <merge_base>..<base_ref> -- <target_file>`. Halts with an alert if upstream unmerged commits exist.
- **Layer 2: Blast Radius & Downstream Callers**: Uses regex/AST search to discover all downstream callers, imports, and DI registrations referencing modified classes or functions across feature and core packages.
- **Layer 3: Cross-Platform Bridge Matcher**: Scans Flutter Dart source for `MethodChannel("channel_name")`, querying Android (`MethodChannel(..., "channel_name")`) and iOS (`FlutterMethodChannel(name: "channel_name", ...)`) to flag native bridges.
- **Layer 4: Test Impact Analysis (TIA) & Safety Net**: Identifies corresponding test files and checks existing coverage reports (`lcov.info`, JaCoCo, `xccov`), warning if modified functions have 0% coverage or untested error branches.

## Relevant Files & Context Pointers
- `skills/impact-analysis/resources/scripts/check_code_impact.py`: Core impact analysis script.
- `skills/impact-analysis/resources/scripts/test_check_code_impact.py`: Unit and integration tests for the impact engine.
- `.devtool/epic/kanban_sync_impact_analysis/bdd_scenarios.md`: BDD Scenarios 3.1, 3.2, 3.3, 4.1, 4.2.
- `skills/epic-implementation/resources/scripts/detect_project_type.sh`: Project type detector helper.

## Design Rationale
- **Dynamic Base Ref**: The script dynamically detects the upstream base reference (`develop`, `main`, or `origin/develop`) using `git rev-parse --verify`, avoiding hardcoded branch names.
- **Zero Modification / Read-Only**: `check_code_impact.py` is strictly passive and diagnostic; it never modifies source files.
- **Graceful Fallback**: If coverage report files do not exist, Layer 4 gracefully falls back to static test file pairing (`*_test.dart`, `*Test.kt`, `*Tests.swift`) without raising exceptions.

### BDD SCENARIOS

#### Scenario 3.1: Upstream Git Divergence Detection
- **Tag**: `[Tier A - Unit]`
- **Given** an epic branch is working on `features/payment/PaymentRepository.kt`
- **And** the base branch `<base_ref>` (`develop`) has received new commits touching `PaymentRepository.kt` that are unmerged into the current branch
- **When** `check_code_impact.py --files features/payment/PaymentRepository.kt --base-ref develop` is run
- **Then** the report must flag `Git Conflict: 🔴 DIVERGENCE DETECTED`
- **And** list the upstream unmerged commits
- **And** recommend rebasing before making edits.

#### Scenario 3.2: Blast Radius & Downstream Callers Identification
- **Tag**: `[Tier A - Unit]`
- **Given** class `PaymentRepository` in module `:features:payment` is imported by `PaymentViewModel.kt` and `CheckoutFlow.kt`
- **When** `check_code_impact.py --files features/payment/PaymentRepository.kt --symbols PaymentRepository` is executed
- **Then** the tool must list both dependent files with exact line numbers
- **And** calculate the blast radius across module boundaries.

#### Scenario 3.3: Cross-Platform MethodChannel String Detection
- **Tag**: `[Tier A - Unit]`
- **Given** a Flutter file invokes `MethodChannel('com.example.app/biometrics')`
- **And** Native Android Kotlin implements `MethodChannel(..., "com.example.app/biometrics")`
- **And** Native iOS Swift implements `FlutterMethodChannel(name: "com.example.app/biometrics", ...)`
- **When** `check_code_impact.py` runs on the Flutter file
- **Then** it must identify the native Android and iOS plugin files
- **And** flag `Cross-Platform Bridge: ⚠️ NATIVE BRIDGE DETECTED` with exact file paths.

#### Scenario 4.1: Unprotected Code & Coverage Blind-Spot Warning
- **Tag**: `[Tier A - Unit]`
- **Given** a function `processRefund()` in `PaymentService.kt` has no associated unit test file or 0% coverage in reports
- **When** `check_code_impact.py` inspects the function
- **Then** the report must display `Coverage Safety Net: ⚠️ UNPROTECTED CODE (0% Coverage)`
- **And** prompt the developer/agent to write baseline characterization tests before altering code.

#### Scenario 4.2: Missing Logic Cases Detection against 5 BDD Dimensions
- **Tag**: `[Tier A - Unit]`
- **Given** a method handles network requests with a catch block for timeout
- **And** existing test suite only asserts the happy path 200 OK
- **When** impact analysis analyzes test scenario coverage
- **Then** it must warn `Missing Logic Alert: Timeout / Failure handling is untested`
- **And** require adding an edge scenario to the task's BDD specification.

## Test & Verification Checklist
- [ ] **RED**: Create `test_check_code_impact.py` covering git divergence detection, caller symbol search, MethodChannel extraction, and coverage report parsing. Confirm tests fail against empty stub.
- [ ] **GREEN**: Implement `check_code_impact.py` with CLI arguments (`--files`, `--symbols`, `--base-ref`, `--format [json|markdown]`), passing all unit tests.
- [ ] **REFACTOR**: Ensure clean code standards (PEP 8, type annotations, modular analyzers for each layer).
- [ ] **Tier C (Integration)**: Run `check_code_impact.py` on real repository files across simulated git branches, asserting accurate Markdown and JSON diagnostic reports.

## Definition of Done (DoD)
- `check_code_impact.py` successfully detects git divergence, callers, bridge contracts, and missing tests.
- All test cases in `test_check_code_impact.py` pass 100%.
- CLI returns clear exit code: `0` for safe/clean, `1` for divergence/unprotected warning, `2` for syntax error.

## Dependencies & Blockers
- **Blocked by**: None (Engine can be built in parallel with Task 1).
- **Blocks**: [Task 3](../../features/task_3_impact_analysis_skill.md), [Task 4](../../features/task_4_workflow_integration.md).

## References & Rollback
- Reference: [HLD Section 3: High-Level Architecture & 4-Layer Impact Pipeline](kanban_sync_impact_analysis.en.md#3-high-level-architecture)
- Rollback Strategy: Remove created script and test files.
