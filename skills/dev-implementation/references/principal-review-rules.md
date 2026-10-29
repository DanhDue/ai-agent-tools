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

5. **Shared Contracts & Symlink Resolution**:
   - When reviewing design documents impacting inter-service or cross-repo communication, verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable).
   - Flag any breaking schema change without backward-compatibility shims or transition windows as **Critical**.
   - Flag any missing `## Shared Contract Impact` section or failure to prioritize contract updates in `task_01` as **Important**.
