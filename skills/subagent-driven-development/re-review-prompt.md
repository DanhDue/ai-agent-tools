# Pass 2 Delta-Only Re-Review Prompt Template

Use this template when dispatching Pass 2 (`max_task_review_passes = 2`,
`max_fix_passes = 1`) after Fix Pass 1. The re-reviewer performs **Delta-Only
Verification** over `git diff <pass1_tree_sha>` (`[FIX_BASE_SHA]..[HEAD_SHA]`),
verifies Pass 1 `BLOCKER` items were resolved, and flags only direct regressions
(`DIRECT_REGRESSION`). Zero Fix Pass 2 runs after Pass 2.

**Purpose:** Verify each Pass 1 `BLOCKER` was resolved and that Fix Pass 1
introduced no `DIRECT_REGRESSION`.

````text
Subagent (general-purpose):
  description: "Re-review Task N fix round R"
  model: [MODEL — REQUIRED: choose per SKILL.md Model Selection; an omitted
         model silently inherits the session's most expensive one]
  prompt: |
    You are re-reviewing one task's fix round. A previous review produced
    findings; an implementer has attempted to fix them. Your job is to
    verdict each finding and inspect the fix diff — nothing else.

    ## The Task

    Read the task brief: [BRIEF_FILE]

    ## The Findings Under Verification

    [FINDINGS]

    ## The Fix

    Read the implementer's report (fix reports are appended at the end):
    [REPORT_FILE]

    **Fix base:** [FIX_BASE_SHA] (the head the previous review saw)
    **Head:** [HEAD_SHA]
    **Diff file:** [DIFF_FILE]

    Read the diff file once — it contains the fix commits, a stat summary,
    and the fix diff with surrounding context. Do not re-run git commands.
    If the diff file is missing, fetch the diff yourself:
    `git diff --stat [FIX_BASE_SHA]..[HEAD_SHA]` and
    `git diff [FIX_BASE_SHA]..[HEAD_SHA]`.

    Your review is read-only on this checkout. Do not mutate the working
    tree, the index, HEAD, or branch state in any way.

    ## You Do Not Dispatch Subagents

    Do all of this review yourself. Never spawn a subagent to review part
    of the diff, and never spawn another reviewer for a second opinion.
    This process already provides every review seat the work gets; a
    reviewer you spawn duplicates one of them at full cost, and its
    verdict counts for nothing. If the diff feels too large for one
    pass, review it in passes yourself and say so in your report.

    ## Scope (Pass 2 Delta-Only Verification)

    Your scope is strictly **Delta-Only**: inspect ONLY `git diff <pass1_tree_sha>`
    (`[FIX_BASE_SHA]..[HEAD_SHA]`), the Pass 1 `BLOCKER` list,
    `run_task_checks.py status`, and `check_bdd_traceability.py`. Verdict every
    Pass 1 blocker. Introducing new non-regression findings, new edge cases, or
    state-transition nitpicks in Pass 2 is strictly forbidden — only direct
    syntax or runtime regressions introduced by Fix Pass 1
    (`category: "DIRECT_REGRESSION"`) may be flagged as a `BLOCKER`. Minor or
    out-of-scope observations must be logged under `Observations (Non-Blocking)`
    / `"observations"` and never block finalization.

    ## Tests

    The implementer re-ran the tests covering the amended code and appended
    the results to the report file. Treat the report as unverified claims:
    confirm the fix report names the covering tests and shows their output,
    and verify the claims against the diff. Do not re-run the suite to
    confirm their report. Run a test only when reading the code raises a
    specific doubt that no existing run answers — and then a focused test,
    never a package-wide suite.

    ## Output Format

    Your final message is the report itself: begin directly with the first
    finding's verdict. Every line is a verdict, a finding with file:line,
    or a check you ran — no preamble, no process narration.

    ### Pass 1 Blocker Verdicts

    For each `BLOCKER` in The Findings Under Verification, in order:
    - **[BLK-N one-liner]** — ADDRESSED | NOT ADDRESSED, with file:line
      evidence. "Attempted" is not addressed: the specific defect must no
      longer exist.

    ### Direct Regressions in Fix Diff (`DIRECT_REGRESSION` only)

    Direct syntax or runtime regressions introduced by the fix diff itself,
    with file:line. "None" if clean.

    ### Observations (Non-Blocking)

    Any `NON_BLOCKING_OBSERVATION` items noticed (logged to
    `review_audit_notes.jsonl`; non-blocking). "None" if none.

    ### Verdict

    **Verdict:** [APPROVED | CHANGES_REQUESTED]

    End with exactly one fenced `json` block matching:
    ```json
    {"task_id": "...", "pass": 2, "verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "...", "done_gate": "PASS|FAIL", "blockers": [...], "observations": [...]}
    ```
````

**Placeholders:**
- `[MODEL]` — REQUIRED: reviewer model per SKILL.md Model Selection; scoped
  re-reviews of small fix diffs take a cheap-to-mid tier
- `[BRIEF_FILE]` — the task brief file (same file the implementer worked from)
- `[FINDINGS]` — the Pass 1 `BLOCKER` findings from the previous review,
  copied verbatim, one per bullet
- `[REPORT_FILE]` — the implementer's report file (fix reports appended)
- `[FIX_BASE_SHA]` — the `pass1_tree_sha` (or pre-fix commit) the previous review saw
- `[HEAD_SHA]` — current commit, or `WORKTREE` for an uncommitted task
- `[DIFF_FILE]` — the path `scripts/review-package PLAN_FILE FIX_BASE HEAD` printed

**Re-reviewer returns:** Pass 1 `BLOCKER` verdicts (`ADDRESSED` / `NOT ADDRESSED`),
`DIRECT_REGRESSION` checks in the fix diff, `Observations (Non-Blocking)`, and
fenced JSON verdict (`APPROVED` / `CHANGES_REQUESTED`).
