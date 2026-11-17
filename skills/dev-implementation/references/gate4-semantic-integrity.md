# Gate 4 Semantic Test Integrity

Read when: you run Gate 4, dispatch the `gate4-verifier`, or judge whether a test fakes production behaviour.

## Semantic Test Integrity Governance (Gate 4 Rules)

Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
1. **No Reconstructed Logic**: Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses. If a test reconstructs production logic instead of invoking production symbols, the review reports FAIL.
2. **Immutable Real Artifacts**: Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants. If a test substitutes synthetic artifacts that alter scenario anchors, the review reports FAIL.

*(Note: These are Gate 4 semantic integrity requirements evaluated by specialist providers and audits; no universal cross-language mechanical coverage claim is made.)*
