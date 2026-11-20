# Release Notes: d3nexus v1.34.0

**Release Date:** November 21, 2026  
**Version:** `1.34.0`  
**Git Tag:** `v1.34.0`, `d3nexus--v1.34.0`

---

## Executive Summary

`v1.34.0` hardens task-level mechanical verification and governance across the `/dev-lifecycle` workflow and supporting skills (`dev-designer`, `dev-implementation`, `subagent-driven-development`). It introduces mandatory `REGRESSION` verification rows covering touched modules and downstream callers, mandates full `Allowed files` static analysis (`TIER-B`) including architectural boundary linting, enforces anti-tamper `Definition of Done` checkbox locks before marking tasks done, and clarifies the separation between exhaustive mechanical testing by the Programmer and focused semantic/architectural review.

---

## Key Highlights

### 1. Mandatory `REGRESSION` Verification Row (`skills/dev-lifecycle/`, `skills/dev-designer/`, `check_task_contract.py`)
- Every task must declare at least one `REGRESSION` verification row targeting the test suite of the touched module and all *Downstream Callers* listed in the task's blast radius analysis.
- Validated automatically by `check_task_contract.py` (`check_regression_coverage`), blocking design-phase bypasses while grandfathering completed historical tasks.

### 2. Comprehensive `TIER-B` Static Analysis on All `Allowed files`
- Prohibits partial or single-file linting; linter, formatting, and strict type-checking commands must target **all** files in `Allowed files` (both production and test files).
- Requires architectural boundary validation (`lint-imports` or stack contract check) whenever tasks alter inter-module imports or interface contracts.

### 3. Strict `Definition of Done` Checkbox Locking & Anti-Tamper Enforcement
- `status: "done"` and `completedAt` are strictly blocked if any unchecked `- [ ]` box remains in `Definition of Done`.
- Every checkbox must be marked `[x]` with mechanical evidence notes following the `(Vn)` reference (e.g. `- [x] Criterion (V1) — exit 0, 42 passed`).
- Anti-tamper validation in `check_task_contract.py` detects and rejects tampering attempts, such as deleting checklist items or modifying criteria text.

### 4. Clear Demarcation: Programmer Mechanical Verification vs. Semantic LLM Review
- Role 2.3 Programmer is strictly required to execute and pass the complete mechanical verification suite (RED → GREEN → REGRESSION → TIER-B → TIER-C) for every task before claiming completion.
- LLM and Cross-Model reviews are decoupled from routine mechanical tasks, focusing on architectural boundaries, high-risk items, and comprehensive Gate 4 synthesis to prevent orchestration bottlenecks.

---

## Verifications & Quality Gates Passed

- `ruff check skills/dev-implementation/resources/scripts/ check_task_contract.py sync_task_status.py run_task_checks.py audit_epic.py check_epic_readiness.py replay_task_text.py`
- `uv run pytest skills/dev-implementation/resources/scripts/ tests/test_task_contract_ergonomics_e2e.py tests/test_runtime_sync_and_dashboard_hardening.py tests/test_fpg_acceptance.py tests/test_rsdh_orchestration.py -q --tb=short`
- `bash scripts/verify.sh --quiet` (all structural integrity checks & 89 test suites across 14 parallel workers: PASS)
