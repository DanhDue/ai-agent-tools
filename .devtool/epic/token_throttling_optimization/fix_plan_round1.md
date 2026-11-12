# Cross-Model Review Round 1 Fix Plan (`token_throttling_optimization`)

- **Candidate SHA**: `76bb5a2`
- **Reviewer**: Claude (Opus 5.5, High) — 0 Critical, 3 Important, 6 Minor

## Verified Findings & Anchored Remediation

| # | Severity | Verification | Design Anchor | Planned Surgical Fix |
|---|----------|--------------|---------------|----------------------|
| 1 | Important | Valid (`run_external_review.py:530,543`, `external-review-prompt.md:31`) | HLD `fact()` contract (`TTO-FR-01`) + Checklist disclosures | Keep `fact()` 1-line `PASS:` for tests; extract concise `audit_epic.py` disclosure sections (`Legacy tasks`, `Protected paths`, `Grader amendments`, `Commits outside tasks`, `Gate 5 items`, summarizing `### Evidence`) in `collect_facts()`. |
| 2 | Important | Valid (`run_external_review.py:672`) | HLD Quadratic Bloat / English SSOT | Exclude `principal_review` (and `fix_plan_round`) from `artefact_lines()` alongside `review_results`. |
| 3 | Important | Valid (`CRITICAL_RULES.md:53`, `governance-checklists.md:25`) | HLD L179 / Spec L93 / BDD `TTO-HP-07` (`lifecycle_runner.py:2170`) | Document the unambiguous non-contract source-defect fast path (`_can_fast_track_code_findings`) and explicit Role 2.2 / Circuit Breaker escalation boundaries in `CRITICAL_RULES.md` §6 and `governance-checklists.md` §1.2. |
| 4 | Minor | Valid (`run_external_review.py:744`) | `TTO-EC-01` byte budget | Gate hunk-header truncation marker on `budget - used` (popping last kept header if needed) so rendered diff never exceeds `max_bytes`. |
| 5 | Minor | Valid (`scripts/resume_context.py:1419`) | `TTO-HP-06` compact context | Track `hld_found` so once an `HLD (...)` line is appended, break out of the outer `roots` loop too. |
| 6 | Minor | Valid (`lifecycle_runner.py:634`) | `TTO-AR-01` path-only targets | Filter `_extract_task_targets` tokens to valid path/extension tokens (`/` or `.<ext>`), skipping symbols/IDs like `RunnerConfig` or `TTO-HP-04`. |
| 7 | Minor | Valid (`tests/test_lifecycle_runner.py:1512`, `sync_task_status.py`) | `TTO-AR-01` slot-local status sync | Skip `*-slot-*` worktrees in `checkout_roots()`, scope `sync_task_status.py task` inside a slot worktree to `[current_root]` so parallel slots commit owning paths cleanly before `merge_slot`, and copy `sync_task_status.py` + helpers into `TTO-AR-01`. |
| 8 | Minor | Valid (`autonomous-mode.md:27`) | `TTO-EC-04` CLI flags | Document `--programmer-effort` in `autonomous-mode.md`. |
| 9 | Minor | Valid (`package_epic.py:167`, `handoff.md:33`) | `TTO-HP-03` packaging template | Heal stale `<N>` and `<source spec>.en.md` placeholders in `revise_handoff_text()` and re-anchor `handoff.md` via `package_epic.py --revise`. |

