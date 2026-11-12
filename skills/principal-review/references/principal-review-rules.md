# Principal Review Rules

Evaluate design documents and epic artefacts against these standalone principles:

1. **Severities**:
   - **Critical**: Fatal architectural flaw or missing core contract preventing the epic from reaching its goal or passing execution gates.
   - **Important**: Would trigger Stop-and-Report, ship incorrect behavior, or break module isolation during implementation.
   - **Minor**: Wording, formatting, typo, or minor consistency adjustments.
2. **Readiness Report Is Proven Fact**: Mechanical checks (`R1`–`R8` in `check_epic_readiness.py`) already passed prior to review; do not re-verify or re-report them. Focus strictly on judgement, architecture, and source grounding.
3. **Grounding in Active Source**: Every claim about repository code must cite an observed file path and line number proving the symbol/config exists at the candidate commit.
4. **Actionable Findings**: Each finding must name the artefact path, section heading, and a concrete `Proposed: <edit>` recommendation.
5. **Shared Contracts & Source-of-Truth Hierarchy (Forward Alignment over Legacy Reversion)**:
   - **Tier 1 (Highest — Approved Design Intent)**: Approved Spec (`*-design.en.md`) and HLD (`<epic_dir>.en.md`).
   - **Tier 2 (Cross-Repo Contract Baseline)**: `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
   - **Tier 3 (Legacy Code Baseline)**: Existing `src/` files and task `Allowed files`.
   - **Forward Alignment Rule**: When Tier 1 intentionally updates pipeline steps, enums, or schemas beyond Tier 2/Tier 3, **never propose reverting Tier 1 back to legacy Tier 2/Tier 3**. Report a Forward Contract-Sync / Blast-Radius Gap proposing forward updates to `shared-contracts/<domain>/` (`+ sync_contracts.py ack` + `## Shared Contract Impact`) and adding legacy callers to task `Allowed files`. Verify `shared-contracts/` symlink resolution on disk and flag unacknowledged drift or missing `task_01` sync as `Critical`/`Important`.
6. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Variables referenced in `except` blocks must be bound before `try`.
   - **Part-of-Speech Ambiguity**: Token normalizers/lemmatizers must disambiguate noun/adjective vs gerund/participle forms.
   - **ORM Flush Semantics**: Enforce Insert -> Update -> Delete ordering before mutating entities sharing unique constraints.
   - **Interactive Contract Boundary**: UI interactive token/span coverage must match `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: RED test fixtures must satisfy DB check constraints before reaching domain assertions.
