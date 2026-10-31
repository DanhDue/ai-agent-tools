To avoid false-positive findings, evaluate evidence against these architectural principles:

1. **Task-Level vs. Gate 4 Workspace Scope**:
   - Each task's `Verification` table is strictly scoped to that individual task's deliverables (e.g. documentation, domain models, or specific adapters).
   - Tasks are NOT required to execute workspace-wide profiles. Full workspace capabilities (coverage thresholds, security advisories/deny, FFI/WASM release builds, database hygiene, and end-to-end acceptance) belong exclusively to the platform-neutral **Gate 4 Quality Orchestrator (`@quality_check`)** evaluated on the final candidate SHA. Do not report task evidence as defective solely because it does not run the entire workspace epic profile.
2. **Compiled Language TDD RED Semantics**:
   - In compiled languages (Rust, Go, C++, etc.), the initial TDD RED phase for a new component or function is legitimately satisfied by a compilation failure or missing test target. A non-zero exit code prior to implementation code being written demonstrates a valid RED state.
3. **Artifact Budget Assertions**:
   - Verify that test assertions checking generated build artifacts (such as WASM binary size or exported types) strictly verify that the target artifact actually exists (avoiding vacuous false-PASS loops).
4. **Contract Drift Inspection**:
   - Check whether code constants, default parameters, and enum variants match the published API reference documentation and cross-epic integration contracts without divergence.
   - If `shared-contracts/` is touched (including directories linked via symlinks across repositories), verify that the `task_01` commit synchronizes the canonical contract files, preserves backward compatibility (Non-Breaking Schema Guarantee), and introduces no breaking wire changes for satellite consumers.
5. **No Reconstructed Logic**:
   - Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses.
   - A test that reconstructs production logic instead of invoking production symbols is a blocking finding; Gate 4 reports it as FAIL.
6. **Immutable Real Artifacts**:
   - Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants.
   - A test that substitutes synthetic artifacts altering scenario anchors is a blocking finding; Gate 4 reports it as FAIL.
7. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.
