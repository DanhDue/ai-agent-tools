# Release Notes: d3nexus v1.26.0

**Release Date:** November 07, 2026  
**Version:** `1.26.0`  
**Git Tag:** `v1.26.0`, `d3nexus--v1.26.0`

---

## Executive Summary

`v1.26.0` adds **Kiro CLI (`--cli kiro`)** as a first-class external reviewer across `principal-review` and `cross-model-review`, introduces the **3-Tier Epic Documentation Separation ("Prompt to Maintain" HLD vs Exhaustive Edge-Case BDD vs Self-Contained Task SSOT)** to cut LLM context bloat by ~60% while maximizing adversarial edge-case and exception coverage, and completes `bin/d3nexus` subcommand & Gate 1–5 Ledger wiring across `/dev-lifecycle`.

---

## Key Highlights

### 1. Kiro CLI External Reviewer Integration (`--cli kiro`)
- **First-Class Reviewer Provider**: Added `--cli kiro` (`kiro-cli` / `kiro`) across `run_external_review.py`, `d3nexus:principal-review`, `d3nexus:cross-model-review`, `d3nexus:dev-lifecycle`, `d3nexus:dev-implementation`, and `rules/CRITICAL_RULES.md`.
- **Default Configuration**: Uses `claude-opus-5.5` with `thinking_level: "high"` via `kiro-cli chat --no-interactive --trust-all-tools --wrap never --effort <effort> --model <model>`.
- **Multi-Profile Keychain Forwarding**: Automatically resolves and forwards `HOME=$REAL_HOME` when invoked from inside `/antigravity_homes/<profile>` so `kiro-cli` accesses the host macOS Keychain Builder ID session seamlessly.

### 2. 3-Tier Epic Documentation Architecture ("Prompt to Maintain" vs Task SSOT)
- **Human-Facing System Overview & Maintenance Map (`<epic_name>.{en,vi}.md`)**:
  - Dedicated to human comprehension and long-term system maintenance (**"Prompt to Maintain"** instead of *"Prompt and Pray"*).
  - Features a structured **Feature Maintenance Map** (canonical entry points, core invariants, config knobs, and extension/troubleshooting hooks), **1 mandatory Architecture/Data-Flow Mermaid diagram**, and **conditional Sequence Diagrams** (only for multi-service/async/state-machine flows; drops redundant Use Case flowcharts and duplicate embedded Gherkin).
- **Adversarial Edge-Case & Exception BDD Suite (`bdd_scenarios.{en,vi}.md`)**:
  - Dedicated to catching the maximum number of boundary conditions (`EC`), invalid state transitions (`ST`), async/concurrency race conditions (`AR`), and exceptions/fault injection with **atomic rollback invariants** (`FR`).
- **Self-Contained Task SSOT & Strict Bounded Context (`task_*.md`)**:
  - `dev-implementation` Phase 0 now loads only lean orchestration context (`handoff.md`, HLD Maintenance Map & Integration Test Plan, and task headers), while Phase 2 loads one self-contained `task_*.md` at a time.

### 3. Lifecycle Speedups, `bin/d3nexus` Subcommands & Gate Ledger Completeness
- **Fast Base-Branch Check in Phase 2 Step 7**: Skips redundant per-task rebase and `verify-tier` runs when local `develop` has not moved since worktree creation (`git rev-parse develop == $(git merge-base HEAD develop)`).
- **Single-Pass Step 3 Readiness Check**: `dev-designer` Step 3 consolidates duplicate `check_document.py`, `check_bdd_traceability.py plan`, and `check_task_contract.py --design` calls into `check_epic_readiness.py <epic_name>`.
- **Complete `bin/d3nexus` & Gate 1–5 Ledger**: Added `audit-epic`, `check-bdd`, `check-impact`, `integrate`, `package-epic`, `quality-check`, and `run-external-review` to `bin/d3nexus`, and wired `--gate 1`, `--gate 4`, and `--gate 5` into `dev-brainstorming` and `dev-implementation`.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish** (Sections 1–16, all test suites green)
- `check_document.py`: 🟢 **PASS** (`0 findings` across all updated skills and rules)
