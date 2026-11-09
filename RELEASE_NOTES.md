# Release Notes: d3nexus v1.28.0

**Release Date:** November 10, 2026  
**Version:** `1.28.0`  
**Git Tag:** `v1.28.0`, `d3nexus--v1.28.0`

---

## Executive Summary

`v1.28.0` introduces the **3-Round Scope-Narrowing Review Convergence Funnel** (`Full -> Delta -> Blocker-Only`) with **Quota-Aware Provider Selection (`Claude -> Codex -> Kiro -> Argon`)**, **4 Anti-Fix-Loop Prompt Strategies**, **Source-of-Truth Forward Alignment** (preventing reviewers from proposing reversion of user-approved HLD changes back to legacy contracts), **Top 3 Highest-Risk Findings Executive Report**, **3 Hard Circuit Breaker Halts** (`SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`), the **3-Level Test Scope Pyramid** (`Task-Scoped` -> `Blast-Radius Scoped` -> `Test All` once on merge), and **3-Layer Lifecycle Documentation Separation** to eliminate LLM Attention Dilution and Lost-in-the-Middle degradation.

---

## Key Highlights

### 1. 3-Round Scope-Narrowing Convergence Funnel & `check-quota` Priority
- **Provider Priority (`Claude -> Codex -> Kiro -> Argon`)**: Automatically evaluates live quota via `select_provider_by_quota()` (`--auto-quota`):
  - **Claude & Codex**: `ACTIVE`, `5H Session >= 15%`, and `7D Weekly > 2%`.
  - **Kiro (`kiro-cli`)**: `ACTIVE`, `Monthly Credits >= 3%`, and `remaining >= 15.0 credits`.
  - **Argon (`agy`)**: `ACTIVE` and `Argon Weekly >= 10%` or `5H >= 15%`.
- **Max 3 Rounds (`MAX_REVIEW_ROUNDS = 3`)**:
  - **Round 1 (`Scope: full`)**: Exhaustive full-scope audit across all touched artefacts/modules.
  - **Round 2 (`Scope: delta`)**: Delta verification on `prev_sha..curr_sha`; prohibits new `Minor` findings on untouched files.
  - **Round 3 (`Scope: convergence`)**: Strict Blocker-Only Convergence Mode (incomplete fixes or new `Critical`/`Important` regressions in `prev_sha..curr_sha`).

### 2. 4 Anti-Fix-Loop Prompt Strategies & Cross-Round Shared Context
- **Strategy 1 — Exhaustive Per-File Pass in Round 1**: Requires reporting all `Critical` and `Important` issues per file in Round 1 (no drip-feeding).
- **Strategy 2 — Universal Anti-Ping-Pong Guardrail**: Injects `### Cross-Provider Handoff & Anti-Ping-Pong Guardrail` and `### Earlier Rounds Shared Context Ledger (Cumulative Memory)` across all Round $\ge 2$ runs (both single-model and mixed-model sessions).
- **Strategy 3 — Previously Fixed Locations Registry (`Verify-Then-Close`)**: Automatically lists all `fixed in <sha>` locations; resolved items must be closed silently (`PASS`) without proposing alternative rewrites.
- **Strategy 4 — Diff-Hunk Isolation on Fixed Files**: Prohibits reporting untouched lines on previously fixed files; only `[INCOMPLETE_FIX]` or `[NEW_REGRESSION]` in `prev_sha..sha` may be reported.

### 3. Forward Alignment, Top 3 Highest-Risk Findings Report & 3 Circuit Breakers
- **Forward Alignment over Legacy Reversion**: Enforces Tier 1 (Approved Spec/HLD) > Tier 2 (`shared-contracts/`) > Tier 3 (Legacy `src/`). Never reverts approved HLD designs to match stale contracts.
- **Top 3 Highest-Risk Findings (`## Top 3 Highest-Risk Findings (Executive Report)`)**: Automatically ranked at the top of `run_external_review.py triage` with `Design Anchor` and `Proposed action`.
- **3 Hard Circuit Breakers**:
  1. `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`: Immediate halt in any round when a `Critical`/`Important` finding conflicts with `shared-contracts/`.
  2. `CIRCUIT_BREAKER_HALT (FIX_LOOP)`: Immediate halt when a fixed file fails again in Round $N$.
  3. `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`: Immediate halt when any `Critical` finding remains after Round 3 (whereas Round 3 with `0 Critical` findings triggers `AUTO_PASS_FINAL_SWEEP`).

### 4. 3-Level Test Scope Pyramid & 3-Layer Documentation Architecture
- **3-Level Test Scope Pyramid**: Level 1 (`Task-Scoped` `< 5s` per task) -> Level 2 (`Blast-Radius Scoped` `< 30s` at Gate 4) -> Level 3 (`Test All` full workspace suite once in `finishing-a-development-branch` before merging to `develop`).
- **3-Layer Lifecycle Documentation Separation**: Keeps runtime `SKILL.md` files lean and decouples the `/dev-lifecycle` skills catalog and convergence architecture into `docs/lifecycles.{en,vi}.md` and on-demand `references/*.md` files.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish**
- `test_run_external_review.py` & `test_audit_epic.py`: 🟢 **PASS** (89/89 unit tests passing)
- `test_lifecycle_document_contract.py` & `test_verifiable_handoff_text.py`: 🟢 **PASS** (26/26 contract tests passing)
