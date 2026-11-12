# Review Triage

Every cross-model review round (Claude CLI, Codex CLI, Kiro CLI, Antigravity CLI, or Ollama) is verified before acting. Shared rules: [review-rules.md](../../dev-implementation/references/review-rules.md) and [governance-checklists.md](../../dev-lifecycle/references/governance-checklists.md).

## Steps

1. Print the round triage skeleton:
   - Epic: `python3 skills/dev-implementation/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`
   - Ad-hoc: triage skeleton streams directly to stdout.
2. Check `## Passes` (`none` or error means that slice was unreviewed — note in Next Steps).
3. Verify every row in `## Top 3 Highest-Risk Findings (Executive Report)` and `## Findings` against candidate-SHA source AND approved `.en.md` HLD, `bdd_scenarios.en.md`, and `Decisions Already Made` (`d3nexus:receiving-code-review` discipline).
4. Fill `## Top 3 Highest-Risk Findings (Executive Report)` (`Design Anchor`, `Proposed action`) and each `## Findings` row:
   - **Assessment**: `Valid`, `Debatable`, `False positive`, or `Not shown`.
   - **Evidence**: exact `file:line` and HLD/Task contract reference checked.
   - **Proposed action**: `fix` (anchored to approved design), `dismiss: <reason>`, or `none` (non-blocking `Minor`).
5. Inspect `## Round Comparison` and `## Since Round <n>` (`check the fix` marks re-reported items for re-inspection).
6. Replace Next Steps with concrete Fix commits, recorded decisions, and confirmation round status.
7. Evaluate `## Auto-Triage Gate` and begin output with the standardized 4-bullet header block:
   ```markdown
   Cross-Model Review Triage: Round <N> (<CLI>)

   • Candidate SHA: <commit_sha>
   • Reviewer: <CLI> ( <model> )
   • Thinking Level: <Light | Low | Medium | High | Extra High | None>
   • Verdict: <VERDICT> (<count> <Severity> findings)
   ```
   - **`AUTO_PASS_CLEAN` (`0 findings`)** / **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`)**: Sweep valid `Minor` items once, pass full Gate 4, and finish the stage without another CLI round.
   - **`AUTO_FIX_ELIGIBLE` (Rounds 1–2 with `Critical`/`Important`, no contract conflict/Fix Loop)**: In autonomous mode when all blockers verify `Valid` in source without touching `shared-contracts/`, fix, record `fixed in <sha>`, run **scoped tests only**, and advance to Round `N+1` (max 3 rounds). In interactive mode (or any `Debatable` / `False positive`), wait for developer decision.
   - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`**: Immediate stop if any `Critical`/`Important` finding conflicts with `shared-contracts/` (never auto-fix or revert approved HLD).
   - **`CIRCUIT_BREAKER_HALT (FIX_LOOP)`**: Immediate stop if a file marked `fixed in <sha>` in Round $N-1$ receives a `Critical`/`Important` finding in Round $N$.
   - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`**: Immediate stop if any `Critical` finding survives Round 3; report `Top 3 Highest-Risk Findings`.
   - **`AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical`, no conflict/Fix Loop)**: Fix valid `Important`/`Minor` items once, pass full Gate 4, and complete without Round 4.

## Remediation Loop Protocol

- **Scoped Tests Only in Intermediate Rounds**: Run fast static checks (`ruff`, `mypy`, `lint-imports`) and targeted unit test files (`uv run pytest -q --tb=short --maxfail=3 <file.py>`). Repo-wide `pytest`, `tests/e2e/`, and `| tail` are forbidden until the **Final Convergence Gate**.
- **Anti-Evasion**: Never remove required packages from `pyproject.toml` instead of `uv lock`, never delete stale reports without regenerating them, never synthesize fake test fixtures, and run `uv run playwright install chromium` after Playwright upgrades. See [governance-checklists.md](../../dev-lifecycle/references/governance-checklists.md).

## 4 Anti-Fix-Loop Prompt Strategies (`run_external_review.py`)

1. **Exhaustive Per-File Round 1 Pass**: Report all `Critical`/`Important` defects per inspected file in Round 1 (anti-drip-feed).
2. **Universal Anti-Ping-Pong Guardrail (Round >= 2)**: Injects `### Cross-Provider Handoff & Anti-Ping-Pong Guardrail`; reviewers honor prior `fixed in <sha>` and `dismissed:` rulings unless an objective runtime bug or HLD violation exists.
3. **Previously Fixed Locations Registry (`Verify-Then-Close`)**: Closes verified prior `fixed in <sha>` locations silently (`PASS`) without proposing alternative refactors.
4. **Diff-Hunk Isolation on Fixed Files**: Restricts re-reports on previously fixed files strictly to `[INCOMPLETE_FIX]` or `[NEW_REGRESSION]` within `prev_sha..sha` diff hunks.

## After the developer decides

- Commit each fix as `[<EPIC_NAME>] Fix <what>`.
- Record Decision cells in `review_results.md` verbatim (`fixed in <sha>` or developer-supplied `dismissed: <reason>`) and commit `[<EPIC_NAME>] Record review decisions for round <n>`.
- Validate intermediate rounds with **scoped tests only**; run Phase 4 / Gate 4 in full only at final convergence, then present Stage 4 Finish Decision.
