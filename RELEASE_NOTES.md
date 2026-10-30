# Release Notes: d3nexus v1.16.0

**Release Date:** October 31, 2026  
**Version:** `1.16.0`  
**Git Tag:** `v1.16.0`, `d3nexus--v1.16.0`

---

## Executive Summary

`v1.16.0` introduces **Two-Tier Project Memory** (`scripts/resume_context.py`), the **Tri-Role Persona Governance Model**, **Multi-Profile Shell Environment & Shared History Synchronization**, new standalone skills (`resume-context`, `save-context`), **Rule 8 in Critical Rules**, automated lifecycle context hooks across all 9 `dev-lifecycle` skills, and machine-readable JSON context exports.

This release fundamentally solves the context degradation, multi-epic cross-talk, and role confusion challenges in long-running autonomous and human-in-the-loop AI coding workflows.

---

## Key Highlights

### 1. Two-Tier Project Memory & Concurrency Locking (`scripts/resume_context.py`)
- **Tier 1 (Permanent Architectural Ledger)**: Stored in `.devtool/PROJECT_LEDGER.md`, tracking system invariants, topology, and permanent milestones across the life of the repository.
- **Tier 2 (Per-Epic Active State & Logs)**: Stored in `.devtool/state/<epic_slug>.md` (strictly capped at $\le 20$ lines) and `.devtool/logs/activity_<epic_slug>.log`.
- **Exclusive Advisory Locking**: All reads and writes are protected by POSIX `fcntl.flock` on `.devtool/.memory.lock`, completely eliminating race conditions and interleaved corruption when multiple AI agents run in parallel.
- **Worktree Routing**: Seamlessly resolves the primary repository root from isolated git worktrees (`.worktrees/<epic_slug>`) via `git rev-parse --git-common-dir`.
- **Automatic Legacy Migration**: Transparently migrates legacy flat `.devtool/assistant_state.md` and `.devtool/activity_stream.log` files into the partitioned directory structure.

### 2. Tri-Role Persona Governance Discipline
Formalizes three distinct roles with unambiguous operating boundaries:
- **Role 2.1 — Human Architect (Developer)**: Owns system vision, approves Gate 3 (spec handoff) and Gate 5 (Kanban completion), makes strategic decisions at Gate 4 Review Choice, and authorizes remote operations.
- **Role 2.2 — AI Assistant (Technical Advisor & Reviewer)**: Specializes in Stage 1 brainstorming, Stage 2 design, and Stage 3 independent code review. **Strictly prohibited** from editing production application code or tests.
- **Role 2.3 — AI Programmer (Senior TDD Software Engineer)**: Specializes in Stage 3 implementation. Executes Kanban tasks strictly following Test-Driven Development (Red-Green-Refactor), clean code standards, bounded context rules, and zero test fakery.
- **Role-Bound Handoff Prompts**: Deterministic prompt emission (`--emit-prompt <mode>`) generating standardized English startup instructions for 5 lifecycle stages: `principal-review`, `implement`, `cross-review`, `finish`, and `assistant`.

### 3. Multi-Profile Shell Environment & History Sync (`--sync-zshrc`)
- Synchronizes `/Users/danhdueexoictif/.zshrc` and all Antigravity profile directories (`~/antigravity_homes/*`).
- Establishes a shared, real-time command history:
  ```zsh
  export HISTFILE="$REAL_HOME/.zsh_history"
  setopt INC_APPEND_HISTORY SHARE_HISTORY EXTENDED_HISTORY
  ```
- Creates symlinks (`$HOME/Projects -> $REAL_HOME/AllProjects`) across profiles.
- Configures universal aliases: `alias resume='python3 .../resume_context.py'` and `alias save-context='python3 .../resume_context.py --complete'`.

### 4. New Skills & Critical Rules
- **`resume-context` (`d3nexus:resume-context`)**: Restores complete project memory on session startup, checks environment health, and enforces Tri-Role persona discipline.
- **`save-context` (`d3nexus:save-context`)**: Persists conversational decisions, active feature states, and programmer activity logs to disk, and executes non-destructive checkpoints without premature archiving.
- **Critical Rule 8 (`rules/CRITICAL_RULES.md`)**: Mandates two-tier project memory hygiene, strict 20-line state ceiling, advisory file locking, and Tri-Role persona discipline across all agent plugins and runtime environments.

### 5. Automated Dev-Lifecycle Context Hooks & Release Verification
- Context saving and handoff prompt emission hooks integrated across all 9 `dev-lifecycle` skills and templates (`dev-brainstorming`, `dev-designer`, `dev-lifecycle`, `dev-implementation`, `principal-review`, `cross-model-review`, `finishing-a-development-branch`, `handoff-template.md`, and `principal-review.md`).
- Pre-Finish Hook in `finishing-a-development-branch` automatically archives completed feature states and records permanent ledger milestones upon branch landing.
- Section 15 added to `scripts/verify.sh` to mechanically enforce all context engine capabilities and Tri-Role rules before any release.

### 6. JSON Harvest Export (`--json`)
- Adds `--json` capability to export comprehensive context telemetry in structured machine-readable JSON format:
  ```bash
  python3 scripts/resume_context.py --json
  ```
- Emits structured payloads containing ledger, state snapshots, activity logs, git status across repos, open contract RFCs, and active Kanban tasks.

---

## Verifications & Quality Gates Passed

- `audit_epic.py`: 🟢 **PASS** (100% evidence verified)
- `check_bdd_traceability.py`: 🟢 **PASS** (12/12 scenarios covered, 13/13 unit tests pass)
- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (15/15 sections green)
- Cross-Model Review (Claude CLI): 🟢 **PASS** (All findings resolved across 3 rounds)

