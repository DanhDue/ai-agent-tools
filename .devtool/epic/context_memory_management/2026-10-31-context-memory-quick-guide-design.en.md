# Context Memory and Tri-Role Workflow Quick-Guide Content Specification

## Table of Contents

- [1. Purpose and Core Claim](#1-purpose-and-core-claim)
- [2. Scope and Required Content](#2-scope-and-required-content)
- [3. Deliberate Non-Goals](#3-deliberate-non-goals)
- [4. Reader Acceptance Criterion](#4-reader-acceptance-criterion)
- [5. Dependencies and Maintenance Triggers](#5-dependencies-and-maintenance-triggers)

## 1. Purpose and Core Claim

Developers and AI agents operating across multi-repository workspaces (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) and multiple Antigravity account profiles (`antigravity_homes/<profile>`) need a single, actionable operational playbook (`docs/context-memory-quick-guide.en.md` and `docs/context-memory-quick-guide.vi.md`).

Without a scenario-driven quick-guide, switching accounts or transitioning between design, review, and implementation forces the developer to reconstruct prompts from memory or risk invoking an agent in the wrong persona (for example, allowing an advisory agent to edit production source code or losing active state across parallel epics).

This document claims that every workflow transition in a project with Two-Tier Project Memory maps deterministically to one of three governance roles (**Human Architect**, **AI Assistant**, **AI Programmer**) and five operational scenarios backed by `resume` / `save-context` (`scripts/resume_context.py`).

## 2. Scope and Required Content

The quick-guide pair (`docs/context-memory-quick-guide.en.md` and `docs/context-memory-quick-guide.vi.md`) must cover:

1. **Tri-Role Governance Matrix & 10-Second Command Cheat-Sheet**:
   - Clear boundaries between **2.1 Human Architect**, **2.2 AI Assistant (`--role assistant`)**, and **2.3 AI Programmer (`--role programmer`)**.
   - Quick lookup table of shell aliases (`resume`, `save-context`), slash skills (`/resume-context`, `/save-context`), and `--emit-prompt` modes (`principal-review`, `implement`, `cross-review`, `finish`, `assistant`).
2. **End-to-End Workflow Diagram**:
   - A Mermaid `flowchart TD` and `sequenceDiagram` illustrating how Tier 1 (`.devtool/PROJECT_LEDGER.md`) and Tier 2 (`.devtool/state/<epic_slug>.md` and `.devtool/logs/activity_<epic_slug>.log`) connect the three roles across all lifecycle gates.
3. **Scenario 1: Post-Package Principal Review (AI Assistant)**:
   - Trigger: Epic is packaged (`handoff.md` committed at Stage 2).
   - Exact commands to harvest context as **AI Assistant**, run `d3nexus:principal-review`, triage findings with the Human Architect, save state (`--state`), and emit the **AI Programmer Prompt** (`--emit-prompt implement`).
4. **Scenario 2: Post-Review Task Implementation in Worktree (AI Programmer)**:
   - Trigger: Principal Review is `PASS` and the developer dispatches the **AI Programmer Prompt** (`/dev-implementation`).
   - How the **AI Programmer** loads context inside `.worktrees/<epic_dir>` (`--role programmer`), executes tasks with TDD, logs each task (`--log` + `--state`), and emits the **Cross-Model Review Prompt** (`--emit-prompt cross-review`) after Gate 4 `PASS`.
5. **Scenario 3: Post-Implementation Cross-Model Review (AI Assistant)**:
   - Trigger: Gate 4 passes and the developer selects Cross-Model or Local Model Review.
   - How the **AI Assistant** loads context (`--role assistant`), runs `d3nexus:cross-model-review`, presents the verified triage table, and emits either a **Fix Prompt for AI Programmer** (`--emit-prompt implement`) or a **Finish Prompt** (`--emit-prompt finish`).
6. **Scenario 4: Ad-Hoc Technical Discussion, Architecture Q&A & Debugging Analysis (AI Assistant — Read-Only Code)**:
   - Trigger: The developer opens a session or switches accounts only to discuss technical problems, evaluate solution trade-offs, or inspect architecture without modifying code.
   - How to summon **AI Assistant** (`resume --role assistant` or `/resume-context`), enforce the hard ban on editing production code, and save discussion takeaways or custom notes anytime via `/save-context` (`save-context --checkpoint <epic_slug> "<custom_note>"` or `--state --prompt "<note>"`).
7. **Scenario 5: Multi-Epic Concurrency, Account Rotation & Stage 4 Branch Finishing (`/finish`)**:
   - How multiple agents work on `epic-a` and `epic-b` simultaneously without overwriting state or truncating logs.
   - How switching Antigravity accounts preserves shared terminal history (`~/.zsh_history`) and restores context in one command (`resume`).
   - How `/finish` executes `resume_context.py --complete <epic_slug> "<milestone_summary>"` to append the permanent milestone to `PROJECT_LEDGER.md` and archive only that epic's state and logs into `.devtool/archive/`.

## 3. Deliberate Non-Goals

- Internal Python implementation details of `scripts/resume_context.py` or `fcntl.flock` lock mechanics (already covered in `docs/architecture/save_resume_rules.md`).
- Platform-specific TDD/BDD coding tutorials for Flutter, Android, iOS, Python, or Rust.
- Product discovery and market validation workflows (covered in `d3nexus:lean-product-lifecycle`).

## 4. Reader Acceptance Criterion

After reading the quick-guide, a developer can, within 30 seconds at any point in a project (switching Antigravity accounts, finishing Stage 2 packaging, passing Gate 4, or starting an ad-hoc technical discussion), select the matching scenario, run the exact CLI command or copy-paste prompt to summon the right persona (**AI Assistant** or **AI Programmer**), and persist or restore context without role violations or multi-epic state collisions.

## 5. Dependencies and Maintenance Triggers

- **Dependencies**: `scripts/resume_context.py`, `skills/resume-context/SKILL.md`, `skills/save-context/SKILL.md`, `rules/CRITICAL_RULES.md` (Rule 8), and `/Users/danhdueexoictif/.zshrc` aliases (`resume`, `save-context`).
- **Out-of-Date Triggers**: Any change to `--emit-prompt` mode names, CLI flags in `scripts/resume_context.py`, or gate numbering in `d3nexus:dev-lifecycle`.
