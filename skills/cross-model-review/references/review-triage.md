# Review Triage

Every review round — Claude CLI, Codex CLI, Antigravity CLI or a local Ollama model — is triaged with the developer before anyone acts on it. A reviewer's finding is a claim to check, not an instruction: some are real, some are false positives, and some only say that a file was not shown.

## Steps

1. Print the skeleton for the latest round:
   - For an epic:
     ```bash
     python3 skills/dev-implementation/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>
     ```
   - For an ad-hoc review, the triage skeleton is streamed directly to stdout upon completion.

2. Read `## Passes`. A pass with verdict `none` or an error never reviewed its slice; say so in Next Steps rather than reading its silence as approval.

3. Verify every row of `## Top 3 Highest-Risk Findings (Executive Report)` and `## Findings` against the code at the round's SHA AND against the approved design documents (`.devtool/epic/<epic_dir>/<epic_dir>.en.md` HLD, `bdd_scenarios.en.md`, and `Decisions Already Made` in `task_*.md`), with the discipline of `d3nexus:receiving-code-review`: open the file and line it names, check the claim, and never accept or reject it on the reviewer's word alone.

4. Fill the empty columns of `## Top 3 Highest-Risk Findings (Executive Report)` (`Design Anchor`, `Proposed action`) and the three empty columns of each row in `## Findings`:
   - **Assessment** — `Valid` (the claim holds and adheres to the approved design), `Debatable` (it holds by the letter, not clearly by intent), `False positive` (it does not hold, or it contradicts frozen choices in the approved HLD / `Decisions Already Made`), or `Not shown` (the reviewer could not see what it needed).
   - **Evidence** — the file and line (plus HLD/Task contract section when applicable) you checked, with a short quote.
   - **Proposed action** — `fix` (strictly anchored to the approved design), `dismiss: <reason>`, or `none` for a Minor finding that needs no change.

5. Read `## Round Comparison` and `## Since Round <n>`. Fewer Critical and Important findings, and fixed findings that are not re-reported, show the fixes worked. A fixed finding re-reported at the same path says `check the fix`: look at it again before deciding.

6. Replace the Next Steps line with numbered actions: the Fix commits, the decisions to record, and, when blocking findings will be fixed, a confirmation round whose triage measures the improvement.

7. Evaluate the `## Auto-Triage Gate` section emitted by `run_external_review.py triage` and present the filled triage beginning with the standardized 4-bullet header block:
   ```markdown
   Cross-Model Review Triage: Round <N> (<CLI>)

   • Candidate SHA: <commit_sha>
   • Reviewer: <CLI> ( <model> )
   • Thinking Level: <Light | Low | Medium | High | Extra High | None>
   • Verdict: <VERDICT> (<count> <Severity> findings)
   ```
   - **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor` findings)**: Fix any valid `Minor` items in a single sweep, run Gate 4 green, and complete the review stage without calling the external CLI again.
   - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important` findings, no `shared-contracts/` conflict, and no Fix Loop)**: In autonomous `/dev-lifecycle` mode, when all blocking findings are verified as `Valid` in source and do not conflict with `shared-contracts/`, apply the fixes, record `fixed in <sha>`, run Gate 4 in full, and proceed to the next convergence round (up to max 3 rounds). In interactive mode (or when any finding is `Debatable` / `False positive`), wait until the developer decides each finding.
   - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`**: Triggered immediately in **any round** if a `Critical`/`Important` finding conflicts with `shared-contracts/`. Stop calling tools immediately and report to the Human Architect (never auto-fix or revert the user-approved HLD design).
   - **`CIRCUIT_BREAKER_HALT (FIX_LOOP)`**: Triggered if a file marked `fixed in <sha>` in Round $N-1$ is re-reported with a `Critical`/`Important` finding in Round $N$. Stop calling tools immediately and report to the Human Architect.
   - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`**: Triggered if after **3 rounds (`Round >= 3`) any `Critical` finding still remains**. Stop calling tools immediately and report the `Top 3 Highest-Risk Findings` to the Human Architect.
   - **`AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical` findings, no `shared-contracts/` conflict, and no Fix Loop)**: Apply one final fix pass for remaining valid `Important`/`Minor` items, run Gate 4 green, and complete the stage without a 4th round.

## 4 Anti-Fix-Loop Prompt Strategies (Enforced in `run_external_review.py`)

To prevent false or repetitive Fix Loops across rounds, `delta_round_context()` and `external-review-prompt.md` enforce four guardrails:

1. **Strategy 1 — Exhaustive Per-File Pass in Round 1 (Anti-Drip-Feed)**:
   - Round 1 (Full Scope Audit) instructs the reviewer to report **all** `Critical` and `Important` defects within each inspected file in Round 1, prohibiting piecemeal drip-feeding on untouched lines in later rounds.
2. **Strategy 2 — Universal Anti-Ping-Pong & Solution-Stability Guardrail (All Round $\ge 2$)**:
   - Because every CLI invocation is a stateless subprocess, `delta_round_context()` injects `### Cross-Provider Handoff & Anti-Ping-Pong Guardrail` in **all** Round $\ge 2$ runs (both single-model and mixed-model). Reviewers must honor prior `fixed in <sha>` and `dismissed: <rationale>` decisions and must never demand reversing an accepted fix unless it introduces an objective runtime bug or violates the approved HLD.
3. **Strategy 3 — Previously Fixed Locations Registry (`Verify-Then-Close`)**:
   - `delta_round_context()` extracts all prior `fixed in <sha>` rows into `### Previously Fixed Locations Registry (Verify-Then-Close)`. If the revision resolves the original defect at `$sha`, the reviewer must **close it silently (`PASS`)** without proposing alternative refactors.
4. **Strategy 4 — Diff-Hunk Isolation on Fixed Files**:
   - On any file in `Previously Fixed Locations Registry`, the reviewer is forbidden from reporting pre-existing issues on untouched functions/lines outside the `prev_sha..sha` diff hunks. Re-reporting a fixed file is allowed only for `(a) [INCOMPLETE_FIX]` (original defect unresolved) or `(b) [NEW_REGRESSION]` (new defect directly introduced by the modified lines in `prev_sha..sha`).

## After the developer decides

- Make each fix as its own commit titled `[<EPIC_NAME>] Fix <what>`.
- Write each Decision cell in `review_results.md`: `fixed in <sha>`, or `dismissed: <reason>` in the developer's own words. Never write a dismissal the developer did not give.
- Commit the decisions: `[<EPIC_NAME>] Record review decisions for round <n>`.
- Re-run Phase 4 / Gate 4 in full on the new SHA.
- Present Review Choice again only after Gate 4 returns PASS on the new candidate SHA.
