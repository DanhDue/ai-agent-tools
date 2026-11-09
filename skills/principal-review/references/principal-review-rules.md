# Principal Review Rules

To avoid false-positive findings, evaluate design documents and epic artefacts against these principles:

1. **Severities**:
   - **Critical**: The epic or architecture cannot reach its goal or pass execution gates as designed (e.g. fatal architectural flaw, missing core contract).
   - **Important**: A task or component would hit Stop-and-Report, ship incorrect behavior, or break module isolation during implementation.
   - **Minor**: Wording, formatting, typo, and minor consistency adjustments.

2. **Readiness Report Is Proven Fact**:
   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated prior to review.
   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.

3. **Grounding in Active Source**:
   - Every claim about the repository source code must name the specific file and line number read.
   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at the candidate commit.

4. **Actionable Findings**:
   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.

5. **Shared Contracts, Symlink Resolution & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
   - **Source-of-Truth Hierarchy**:
     1. **Tier 1 (Highest Authority — Approved Design Intent)**: User-approved Spec (`*-design.en.md`) and HLD (`<epic_dir>.en.md` Goals & Architecture).
     2. **Tier 2 (Cross-Repo Contract Baseline)**: `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
     3. **Tier 3 (Legacy Code Baseline)**: Existing source files in `src/` and task `Allowed files`.
   - **Forward Alignment Rule (Never Revert Approved Design Intent)**: When Tier 1 intentionally introduces a new pipeline structure, step count, enum, or schema (e.g., consolidating 7 legacy steps into 5 steps) that differs from Tier 2 (`shared-contracts/`) or Tier 3 (`src/`), **DO NOT propose reverting the HLD/Spec back to the legacy Tier 2/Tier 3 design**. Instead, report a **Forward Contract-Sync / Blast-Radius Gap** and propose:
     1. Updating `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md` + `sync_contracts.py ack`) and `## Shared Contract Impact` to match the approved Tier 1 design (with backward-compatibility shims if needed).
     2. Adding the affected legacy callers (e.g., `worker/bridge.py`, `preview/jobs.py`) into the appropriate task's `Allowed files` so implementation migrates them forward to the new design.
   - When reviewing design documents impacting inter-service or cross-repo communication, verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable).
   - Flag any unacknowledged contract drift or missing `task_01` contract/adapter synchronization as **Critical** or **Important** with a **forward-migration** `Proposed:` action.

6. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.
