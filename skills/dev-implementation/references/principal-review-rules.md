# Principal Review Rules

To avoid false-positive findings, evaluate the epic against these principles:

1. **Severities**:
   - **Critical**: The epic cannot reach its goal or Gate 4 as designed.
   - **Important**: A task would hit Stop-and-Report or ship wrong behaviour.
   - **Minor**: Wording, formatting, and minor consistency adjustments.

2. **Readiness Report Is Proven Fact**:
   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated.
   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.

3. **Grounding in Active Source**:
   - Every claim about the repository source code must name the specific file and line number read.
   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at `$sha`.

4. **Actionable Findings**:
   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.

5. **Shared Contracts, Symlink Resolution & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
   - **Source-of-Truth Hierarchy**: Tier 1 (Approved Spec `*-design.en.md` & HLD `<epic_dir>.en.md` Goals/Architecture) > Tier 2 (`shared-contracts/`) > Tier 3 (Legacy `src/` code).
   - **Forward Alignment Rule**: When Tier 1 intentionally changes pipeline steps, enums, or schemas (e.g., replacing 7 legacy steps with 5 new steps) while `shared-contracts/` or `src/` still holds legacy values, **never propose reverting Tier 1 back to the legacy design**. Instead, propose **forward alignment**: (a) synchronize `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md` + `sync_contracts.py ack`) and `## Shared Contract Impact` to the new Tier 1 design, and (b) add legacy callers in `src/` to task `Allowed files` for forward migration.
   - Verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable) and that `task_01` prioritizes contract/adapter synchronization.
