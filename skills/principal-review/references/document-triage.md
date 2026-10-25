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

3. **Assess Validity**:
   - **Valid**: The architectural or contract mismatch genuinely exists.
   - **Debatable**: Technically true according to literal phrasing, but intent or conventions may differ.
   - **False Positive**: The code or configuration already accounts for the scenario, or the reviewer hallucinated non-existent code.

4. **Present Triage & Wait for Developer Decision**:
   - Present the filled triage table with Assessment, Evidence, and Proposed Action to the developer.
   - Stop calling tools and wait for the developer to confirm or reject each finding.

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
