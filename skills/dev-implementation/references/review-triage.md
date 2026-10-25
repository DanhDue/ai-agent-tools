# Review Triage

Every review round — Claude CLI, Codex CLI, Antigravity CLI or a local Ollama model — is triaged with the developer
before anyone acts on it. A reviewer's finding is a claim to check, not an instruction: some are
real, some are false positives, and some only say that a file was not shown.

## Steps

1. Print the skeleton for the latest round:

   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>
   ```

2. Read `## Passes`. A pass with verdict `none` or an error never reviewed its slice; say so in Next
   Steps rather than reading its silence as approval.
3. Verify every row of `## Findings` against the code at the round's SHA, with the discipline of
   `d3nexus:receiving-code-review`: open the file and line it names, check the claim, and never accept
   or reject it on the reviewer's word alone.
4. Fill the three empty columns of each row:
   - **Assessment** — `Valid` (the claim holds), `Debatable` (it holds by the letter, not clearly by
     intent), `False positive` (it does not hold), or `Not shown` (the reviewer could not see what it
     needed).
   - **Evidence** — the file and line you checked, with a short quote.
   - **Proposed action** — `fix`, `dismiss: <reason>`, or `none` for a Minor finding that needs no
     change.
5. Read `## Round Comparison` and `## Since Round <n>`. Fewer Critical and Important findings, and
   fixed findings that are not re-reported, show the fixes worked. A fixed finding re-reported at the
   same path says `check the fix`: look at it again before deciding.
6. Replace the Next Steps line with numbered actions: the Fix commits, the decisions to record, and,
   when blocking findings will be fixed, a confirmation round whose triage measures the improvement.
7. Present the filled triage and stop. Wait until the developer decides each finding.

## After the developer decides

- Make each fix as its own commit titled `[EPIC_NAME] Fix <what>`.
- Write each Decision cell in `review_results.md`: `fixed in <sha>`, or `dismissed: <reason>` in the
  developer's own words. Never write a dismissal the developer did not give.
- Commit the decisions, then run Phase 4 / Gate 4 in full on the new SHA.
