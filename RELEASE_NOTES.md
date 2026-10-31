# Release Notes: d3nexus v1.17.0

**Release Date:** October 31, 2026  
**Version:** `1.17.0`  
**Git Tag:** `v1.17.0`, `d3nexus--v1.17.0`

---

## Executive Summary

`v1.17.0` introduces the **Tri-Role Context Memory Quick-Guide** (`docs/context-memory-quick-guide.{en,vi}.md`), robust multi-line array parsing and non-UTF-8 metafied byte decoding for `--sync-zshrc`, automatic sibling workspace repository context harvesting in `resume_context.py`, and review runner hardening across Antigravity and Claude CLIs.

---

## Key Highlights

### 1. Tri-Role Context Memory Quick-Guide (`docs/context-memory-quick-guide.*`)
- **Tri-Role Operating Model**: Unifies and clarifies the boundaries among **Human Architect** (Role 2.1 — Strategic decisions & Gate 1–5 approvals), **AI Assistant** (Role 2.2 — Technical Advisor & Reviewer, strictly prohibited from editing production code), and **AI Programmer** (Role 2.3 — Senior TDD Software Engineer bound to approved specs and `Allowed files`).
- **10-Second Command Cheat-Sheet**: Quick reference for session initialization, decision checkpoints, activity logging, handoff prompts, and feature completion.
- **5 Scenario Playbooks**: Step-by-step interactive playbooks covering:
  1. Handing off packaged specs to Principal Review.
  2. Bounded context handoff to AI Programmer for `/dev-implementation`.
  3. Gate 4 PASS handoff to AI Assistant for Cross-Model Review.
  4. Independent technical brainstorming without code mutation.
  5. Multi-account / interrupted session resumption.
- **Updated Lifecycle Diagrams**: Synchronized bilingual Mermaid state and resume diagrams in `docs/lifecycles.{en,vi}.md` annotated with Tri-Role governance personas.

### 2. Multi-Profile Shell Environment & History Sync (`--sync-zshrc`)
- **Multi-Line Array Parsing**: Hardens `update_zshrc_sync_items` with `re.DOTALL` to parse multi-line `sync_items=(...)` declarations containing inline comment lines (`# ...`) without comment corruption.
- **Metafied Byte History Decoding**: Reads `.zsh_history` using `errors="replace"` to smoothly decode macOS zsh extended history metafied byte sequences (`0x83`).
- **Live Host Execution**: Successfully applied and synchronized across `/Users/danhdueexoictif/.zshrc` and all 14 Antigravity profiles (`~/antigravity_homes/*`).

### 3. Sibling Workspace Repository Auto-Harvest
- **Multi-Repo Auto-Discovery**: Automatically discovers sibling workspace repositories (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) when executed from within any individual repository directory.
- **Cross-Repo Telemetry**: Aggregates Git working tree status across all 4 repositories, surfaces open contract RFCs from `D3Nexus/shared-contracts/*/gaps_and_rfcs.md`, and calculates active Kanban task progress across active and done directories.

### 4. Review Runner Hardening & Tooling Resilience
- **`run_external_review.py`**: Trims backtick wrappers from integration results and roots in HLD files, and supports an optional `--developer-note` in Principal Review prompts.
- **`compute_execution_order.py`**: Supports both `&` and `and` in dependency headers, and includes completed tasks from `features/done/`.
- **`check_bdd_traceability.py`**: Normalizes whitespace and comma separation in Covers declarations.
- **`result_reports.py`**: Robustly parses Dart test event JSON stream lines when opening braces appear after newlines.
- **`server.cjs`**: Extends brainstorming server idle timeout to 4 hours via `BRAINSTORM_IDLE_TIMEOUT_MS`.

---

## Verifications & Quality Gates Passed

- `scripts/test_resume_context.py`: 🟢 **PASS** (13/13 tests green)
- `test_run_external_review.py`: 🟢 **PASS** (53/53 tests green)
- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (15/15 sections green)
