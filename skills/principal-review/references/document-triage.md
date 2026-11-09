# Document Review Triage Protocol

Every architectural and design document review round — whether executed via Claude CLI, Codex CLI, or Antigravity CLI — is triaged with the developer before anyone modifies documents or code. Review findings are claims to verify, not direct instructions.

## Triage Procedure

1. **Obtain Triage Table**:
   - For an epic:
     ```bash
     python3 skills/dev-implementation/resources/scripts/run_external_review.py triage --kind principal --epic-dir <epic_dir>
     ```
   - For ad-hoc review of a standalone document (`--doc`): the triage table is streamed directly to stdout.

2. **Verify Every Finding Against Code**:
   - Follow the discipline of `d3nexus:receiving-code-review`.
   - Open the exact file and line number cited by the reviewer.
   - Never accept or dismiss a finding on the reviewer's claim alone without verifying active source code.

3. **Assess Validity & Strict Source-of-Truth Hierarchy (Forward Alignment vs Legacy Reversion)**:
   - **Source-of-Truth Hierarchy**:
     1. **Tier 1 (Approved Design Intent)**: User-approved Spec (`*-design.en.md`) and HLD (`<epic_dir>.en.md`).
     2. **Tier 2 (Cross-Repo Contract Baseline)**: `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
     3. **Tier 3 (Current Code Baseline)**: Legacy code in `src/` and task `Allowed files`.
   - **Forward Alignment Rule (Never Revert User-Approved Design to Match Stale Contracts/Code)**:
     - If a finding points out a mismatch between Tier 1 (e.g., User approved changing 7 pipeline steps to 5 steps in Spec/HLD) and Tier 2 (`shared-contracts/` not yet updated) or Tier 3 (`worker/bridge.py`, `preview/jobs.py` still using 7 steps), **NEVER propose reverting Tier 1 back to the old 7 steps**!
     - Instead, diagnose the root cause as a **Missed Contract Sync / Incomplete Blast-Radius in Tasks**, and write the **Proposed Action** as **Forward Alignment**:
       1. Keep the user-approved 5-step design in the Spec/HLD.
       2. Update `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`) and run `sync_contracts.py ack` to reflect the approved 5 steps.
       3. Add the legacy code files (`worker/bridge.py`, `preview/jobs.py`) to the task's `Allowed files` and `Decisions Already Made` so they are migrated to the 5 steps.
   - **Valid**: The architectural, contract-sync, or blast-radius gap genuinely exists.
   - **Debatable**: Technically true according to literal phrasing, but intent or conventions may differ.
   - **False Positive**: The code or configuration already accounts for the scenario, the reviewer hallucinated non-existent code, OR the reviewer asks to revert an intentional Tier 1 design decision back to legacy behavior (`dismissed: contradicts approved design intent`).
   - **Top 3 Highest-Risk Findings (Executive Report)**: Fill the `Design Anchor (HLD / BDD / Decisions Already Made)` and `Proposed action` columns in the `## Top 3 Highest-Risk Findings (Executive Report)` table emitted by `run_external_review.py triage` so the 3 highest-risk findings are highlighted at the top of the report.

4. **Evaluate Auto-Triage Gate & Developer Decision**:
   - Present the filled triage table with Assessment, Evidence, and Proposed Action. The presentation MUST begin with the standardized 4-bullet header block:
     ```markdown
     Principal Review Triage: Round <N> (<CLI>)
     *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

     • Candidate SHA: <commit_sha>
     • Reviewer: <CLI> ( <model> )
     • Thinking Level: <Light | Low | Medium | High | Extra High | None>
     • Verdict: <VERDICT> (<count> <Severity> findings)
     ```
   - Follow the `## Auto-Triage Gate` classification printed by `run_external_review.py triage`:
     - **`AUTO_PASS_CLEAN` (`0 findings`)** or **`AUTO_PASS_FINAL_MINOR_SWEEP` (`0 Critical`, `0 Important`, only `Minor` findings)**: Fix any valid `Minor` items in a single pass, re-package via `package_epic.py <epic_dir> --revise`, and complete Principal Review immediately without re-invoking the external reviewer.
     - **`AUTO_FIX_ELIGIBLE` (Round 1..2 with `Critical`/`Important` findings, no `shared-contracts/` conflict, and no Fix Loop)**: In autonomous `/dev-lifecycle` mode, when all blocking findings verify as `Valid` in source and do not conflict with `shared-contracts/`, apply the document revisions, record `fixed in <sha>`, re-package, and proceed to the next convergence round (up to max 3 rounds). In interactive mode (or when any finding is `Debatable` / `False Positive`), stop calling tools and wait for the developer to confirm or reject each finding.
     - **`CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`**: Triggered immediately in **any round** if a `Critical`/`Important` finding conflicts with `shared-contracts/`. Stop calling tools immediately and report to the Human Architect (never auto-fix or revert the user-approved HLD design).
     - **`CIRCUIT_BREAKER_HALT (FIX_LOOP)`**: Triggered if a file marked `fixed in <sha>` in Round $N-1$ is re-reported with a `Critical`/`Important` finding in Round $N$. Stop calling tools immediately and report to the Human Architect.
     - **`CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`**: Triggered if after **3 rounds (`Round >= 3`) any `Critical` finding still remains**. Stop calling tools immediately and report the `Top 3 Highest-Risk Findings` to the Human Architect.
     - **`AUTO_PASS_FINAL_SWEEP` (Round 3 with `0 Critical` findings, no `shared-contracts/` conflict, and no Fix Loop)**: Apply one final revision sweep for remaining valid `Important`/`Minor` items, re-package green, and advance without a 4th round.

## 4 Anti-Fix-Loop Prompt Strategies (Enforced in `run_external_review.py`)

To prevent false or repetitive Fix Loops across rounds, `delta_round_context()` and the review prompt templates enforce four structural guardrails:

1. **Strategy 1 — Exhaustive Per-File Pass in Round 1 (Anti-Drip-Feed)**:
   - Round 1 (Full Scope Audit) instructs the reviewer to report **all** `Critical` and `Important` issues within each inspected artefact in Round 1, prohibiting piecemeal drip-feeding on untouched sections in later rounds.
2. **Strategy 2 — Universal Anti-Ping-Pong & Solution-Stability Guardrail (All Round $\ge 2$)**:
   - Because every CLI invocation is a new stateless subprocess, `delta_round_context()` injects `### Cross-Provider Handoff & Anti-Ping-Pong Guardrail` in **all** Round $\ge 2$ runs (both single-model and mixed-model). Reviewers must honor prior `fixed in <sha>` and `dismissed: <rationale>` decisions and must never demand reversing an accepted fix unless it introduces an objective defect or violates the approved HLD.
3. **Strategy 3 — Previously Fixed Locations Registry (`Verify-Then-Close`)**:
   - `delta_round_context()` automatically extracts all prior `fixed in <sha>` rows into `### Previously Fixed Locations Registry (Verify-Then-Close)`. If the revision resolves the original defect at `$sha`, the reviewer must **close it silently (`PASS`)** without proposing alternative rewrites.
4. **Strategy 4 — Diff-Hunk Isolation on Fixed Files**:
   - On any file in `Previously Fixed Locations Registry`, the reviewer is forbidden from reporting pre-existing issues on untouched lines outside the `prev_sha..sha` diff hunks. Re-reporting a fixed file is allowed only for `(a) [INCOMPLETE_FIX]` (original defect unresolved) or `(b) [NEW_REGRESSION]` (new defect directly introduced by the modified lines in `prev_sha..sha`).

## Post-Triage Revision Loop

When findings are accepted by the developer:

1. **Apply Document Revisions First**:
   - Edit the relevant design documents (HLD, BDD, tasks, RFCs).
   - Commit the document edits:
     ```bash
     git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"
     ```

2. **Record Decisions**:
   - In `.devtool/epic/<epic_dir>/principal_review.md`, fill the Decision column for each finding:
     `fixed in <revision_commit_sha>` or `dismissed: <developer's rationale>`.
   - Commit decisions:
     ```bash
     git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"
     ```

3. **Re-Run Packaging & Preflight**:
   - Execute `check_epic_readiness.py <epic_dir>`.
   - Refresh `handoff.md` with the new design commit SHA.
   - Sync epic status to `Packaged`.
   - Commit: `[<EPIC_NAME>] Package epic for handoff`.
   - Re-present the Principal Review Choice to the developer.
