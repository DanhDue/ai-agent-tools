# Principal Review Loop Procedure

Principal Review is a cross-model review of an epic's architecture and task designs against the source repository before implementation begins. It catches grounded misunderstandings, missing contracts, and scope regressions while fixing them in documents is cheap.

## Procedure

1. After the packaging procedure prints `handoff.md`, present the Principal Review Choice to the developer:

   > Packaged.
   > 1. **Done** — stop here.
   > 2. **Principal Review** — a cross-model review of the design against the source before implementation (Claude CLI, Codex CLI, or Antigravity CLI).

   Add the recommendation when it applies:
   - When the epic was designed by a different or fast model (judged from the HLD's `Author` line or the developer's word), cross-model review is strongly recommended before committing to implementation. Recommend using each CLI's strongest reasoning model (for Antigravity CLI: `agy --model "Gemini 4 Argon (Medium)"`).
   - Never choose for the developer. Always wait for explicit selection.

2. **Done**:
   If `.devtool/epic/<epic_dir>/principal_review.md` exists, run:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>
   ```
   - If this check exits 1 (undecided blocking findings exist), refusal is enforced: proceed to step 5 (triage).
   - If this check exits 0, check whether the epic documents were revised:
     ```bash
     git log -1 --format=%s -- .devtool/epic/<epic_dir>
     ```
     When the last commit touching the epic directory is not `[<EPIC_NAME>] Package epic for handoff`, re-run the packaging procedure from step 1 (readiness check, regenerated `handoff.md`, lint, status, and package commit).
     Then print the `handoff.md` path and the Resume Prompt, and stop.

3. **Principal Review**:
   Ask the developer which CLI to use — Claude CLI, Codex CLI, or Antigravity CLI (`agy --model "Gemini 4 Argon (Medium)"`) — and optionally which model. Never choose for the developer.
   Invoke `d3nexus:principal-review`.

4. Run the principal review:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex|agy>
   ```
   - A readiness FAIL prints the precondition banner: the CLI is never invoked. Fix the named failures as an epic revision, re-package, and return to step 1.
   - On success, the round is recorded in `.devtool/epic/<epic_dir>/principal_review.md`. Commit the recorded round:
     ```bash
     git commit -m "[<EPIC_NAME>] Record Principal Review round <n>"
     ```

5. Present the review triage for the latest principal round:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --kind principal --epic-dir <epic_dir>
   ```
   Fill the triage by verifying every finding against the source at the round's SHA, following the discipline in [review-triage.md](../../dev-implementation/references/review-triage.md). Stop calling tools and wait for the developer's decision on each finding.

6. Apply each accepted finding as an in-place revision of the epic documents.
   - Commit the document revision first:
     ```bash
     git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"
     ```
   - Record the decisions in `.devtool/epic/<epic_dir>/principal_review.md` using the SHA from the revision commit (e.g. `fixed in <sha>` or `dismissed: <developer's words>`).
   - Commit decisions:
     ```bash
     git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"
     ```

7. Re-run the packaging procedure from step 1:
   - Run `check_epic_readiness.py <epic_dir>`.
   - Update `handoff.md` with the new design commit SHA.
   - Lint `handoff.md`.
   - Sync epic status to `Packaged`.
   - Commit: `[<EPIC_NAME>] Package epic for handoff`.
   - Return to step 1 of this procedure and present the Principal Review Choice again.

## Guidelines and References

For detailed guidelines on how to verify reviewer claims, assess validity, and record decisions, refer to [review-triage.md](../../dev-implementation/references/review-triage.md).
