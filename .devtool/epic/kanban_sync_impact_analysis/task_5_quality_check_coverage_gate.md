---
id: "task_5_quality_check_coverage_gate"
status: "done"
priority: "high"
assignee: null
epic: "kanban-sync-impact-analysis"
dueDate: null
created: "2026-09-15T02:30:00Z"
modified: "2026-09-14T19:58:40Z"
completedAt: "2026-09-14T19:58:40Z"
labels: ["quality-check", "coverage", "reverse-verification", "gate-4"]
order: "a5"
---

# Task 5: Integrate Quality Check Test Coverage and Reverse Verification Gate

Epic: [kanban-sync-impact-analysis](kanban_sync_impact_analysis.en.md)

## Requirement Analysis
A successful epic cannot rely on unit test assertions alone; it must verify that test coverage genuinely exercises the critical code paths identified across the 4 specialized audit dimensions (Security, Architecture, UI, Code Health). Furthermore, Gate 4 must serve as **Check 2 (Shift-Right Bookend Verification)**, auditing the actual cumulative `git diff` against `<base_ref>` before merging.

This task integrates test coverage extraction and reverse verification into `quality_check` and `epic-lifecycle`:
1. **Platform-Aware Test Coverage Generation**:
   - **Flutter**: Execute `./scripts/testWithCoverage.sh` (or `melos run test:coverage`), parsing `coverage/lcov.info`.
   - **Android**: Execute `./gradlew testDebugUnitTest jacocoTestReport` (or Kover), parsing XML/HTML coverage summaries.
   - **iOS**: Execute `xcodebuild test -enableCodeCoverage YES`, extracting line coverage via `xcrun xccov view --report --json`.
2. **Reverse Verification against 4 Audit Categories**:
   - Cross-check files flagged in semantic audits against line coverage metrics:
     - **Security Audit**: High-risk files (crypto, keychain, auth tokens, biometric channels) require **100% line coverage**.
     - **Architecture Audit**: Pure domain logic (UseCases, Repositories, Entities) requires **$\ge 85\%$ line coverage**.
     - **UI Audit**: State hoisting, BLoC state transitions, and ViewModel emissions must be covered by widget/unit tests.
     - **Code Health Audit**: Refactored methods (< 20 lines) must have active test execution paths.
3. **Gate 4 Bookend Acceptance in `epic-lifecycle/SKILL.md`**:
   - Gate 4 grants `🟢 LGTM` only when:
     - 3-Tier test suite passes 100%.
     - 4 Semantic Audits report zero blockers.
     - Reverse Verification Coverage thresholds are satisfied.
   - If any condition fails, Gate 4 routes back to `epic-implementation` with concrete gap reports.

## Relevant Files & Context Pointers
- `skills/quality_check/SKILL.md`: Master quality gatekeeper skill.
- `skills/epic-lifecycle/SKILL.md`: Epic lifecycle orchestration skill (Gate 4).
- `skills/impact-analysis/resources/scripts/check_code_impact.py`: Impact analyzer tool used for merge-time diff inspection.
- `.devtool/epic/kanban_sync_impact_analysis/bdd_scenarios.md`: BDD Scenario 5.1.

## Design Rationale
- **Closed-Loop Verification**: Combining semantic audits with code coverage reports ensures that agents do not write "superficial" tests that pass without exercising conditional branches or error handlers.
- **Fail-Closed Security Invariant**: Zero tolerance for missing test coverage on security-sensitive code (100% threshold).

### BDD SCENARIOS

#### Scenario 5.1: Reverse Verification against 4 Semantic Audits at Gate 4
- **Tag**: `[Tier C - Integration]`
- **Given** all tasks in the epic are marked `done`
- **When** `@quality_check` runs on the worktree
- **Then** platform test suite coverage is computed (`lcov.info` / JaCoCo / `xccov`)
- **And** security-critical files must demonstrate 100% test coverage
- **And** architecture domain use cases must demonstrate $\ge 85\%$ coverage
- **And** Gate 4 grants `🟢 LGTM` only when both 3-Tier tests, 4 semantic audits, and the Coverage Matrix pass.

## Test & Verification Checklist
- [x] **RED**: Verify that `quality_check/SKILL.md` lacks explicit Coverage-by-Audit Category thresholds and reverse verification instructions.
- [x] **GREEN**: Update `skills/quality_check/SKILL.md` and `skills/epic-lifecycle/SKILL.md` with:
  - Platform-specific coverage invocation commands.
  - The Coverage-by-Audit Category Matrix table.
  - Check 2 (Shift-Right) cumulative diff validation instructions.
- [x] **REFACTOR**: Ensure clear terminal reporting templates and unified executive summary formats.
- [x] **Tier C (Integration)**: Perform a dry-run test asserting that a simulated low-coverage security file triggers a Gate 4 rejection.

## Definition of Done (DoD)
- `quality_check/SKILL.md` incorporates platform coverage commands and reverse verification auditing.
- `epic-lifecycle/SKILL.md` Gate 4 incorporates the coverage threshold matrix.
- Executive summary report template in `quality_check` includes coverage breakdowns per audit category.

## Dependencies & Blockers
- **Blocked by**: [Task 3](../../features/task_3_impact_analysis_skill.md), [Task 4](../../features/task_4_workflow_integration.md).
- **Blocks**: None (Final Epic Gate Task).

## References & Rollback
- Reference: [HLD Section 5.3: Quality Check (Gate 4)](kanban_sync_impact_analysis.en.md#53-quality_check-gate-4--end-of-epic-acceptance)
- Rollback Strategy: Revert edits to `quality_check/SKILL.md` and `epic-lifecycle/SKILL.md` via git.
