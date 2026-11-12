# Manual Smoke Walkthrough Checklist: Token Throttling Optimization

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `git repository` | run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit | the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths |
| 2 | CLI / Workspace Root | verify_polyglot_registry.py runs with --compact | standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs |
| 3 | CLI / Workspace Root | check_epic_readiness.py runs without --strict-bilingual | the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md |
| 4 | CLI / Workspace Root | lifecycle_runner.RunnerConfig resolves the programmer model and effort or dispatches agy with no CLI flag supplied | resolve_programmer_model returns "gemini-4-hydrogen-xhigh", resolve_programmer_effort returns "xhigh", and dispatched commands receive "--model gemini-4-hydrogen-xhigh --effort xhigh" via the shared legacy alias map |
| 5 | CLI / Workspace Root | scripts/test_lifecycle_document_contract.py executes and file byte/word sizes are measured on disk | rules/CRITICAL_RULES.md measures at most 8192 bytes retaining §9 Shell Configuration and adding §10 Zero-Fluff Output Cap |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
