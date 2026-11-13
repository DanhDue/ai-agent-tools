To avoid false-positive findings, evaluate evidence against these architectural principles:

1. **Task-Level vs. Gate 4 Workspace Scope**: Task `Verification` tables stay scoped to each task's deliverables; full workspace quality/acceptance belongs solely to **Gate 4 Quality Orchestrator (`@quality_check`)** on the final candidate SHA. Never flag a task for omitting workspace-wide checks.
2. **Compiled Language TDD RED Semantics**: In compiled languages (Rust, Go, C++), a compilation error or missing test target before implementation satisfies RED.
3. **Artifact Budget Assertions**: Tests asserting generated build artifact budgets must first prove the artifact exists (no vacuous passes).
4. **Contract Drift Inspection**: Constants, defaults, and enums must align with published contracts; where `shared-contracts/` is touched (including symlinks), `task_01` must maintain Non-Breaking Schema Guarantees without wire breaks.
5. **No Reconstructed Logic**: Tests must import and invoke production symbols from `Allowed files`, never reimplementing production logic inside helpers or mocks — otherwise Gate 4 reports FAIL.
6. **Immutable Real Artifacts**: Tests must run against genuine repository schemas and fixtures, never synthetic substitutes that alter scenario anchors or weaken invariants — otherwise Gate 4 reports FAIL.
7. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Variables referenced in `except` blocks must be bound before `try`.
   - **Part-of-Speech Ambiguity**: Token normalizers/lemmatizers must disambiguate noun/adjective vs gerund/participle forms.
   - **ORM Flush Semantics**: Enforce Insert -> Update -> Delete ordering before mutating entities sharing unique constraints.
   - **Interactive Contract Boundary**: UI interactive token/span coverage must align strictly with `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: RED test fixtures must satisfy DB check constraints before reaching domain assertions.
