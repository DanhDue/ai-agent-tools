---
id: "task_7_review_choice_workflow_and_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:10:00Z"
completedAt: null
labels: ["workflow", "documentation", "acceptance"]
order: "a7"
---

# Task 7: Update the Review Choice Workflow and Run Acceptance

Epic: [local_model_review](../epic/local_model_review/local_model_review.en.md)

## Requirement Analysis

Expose option 3 everywhere the Review Choice is stated: the two runtime skills, rule 5 of
`CRITICAL_RULES.md`, and the bilingual lifecycle documents. Add `local-review-setup.md` with an
example reviewer Modelfile and the empty-think-block caveat, add the new suite to
`scripts/verify.sh`, assert the new text in `test_lifecycle_document_contract.py`, then run the
epic's acceptance: the Integration results command, `scripts/verify.sh` and the document checks.
This is the epic's final Tier C task.

## Files

Allowed files:
- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`
- `rules/CRITICAL_RULES.md`
- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `docs/choosing-a-lifecycle.en.md`
- `docs/choosing-a-lifecycle.vi.md`
- `skills/dev-implementation/references/local-review-setup.md` (new)
- `scripts/verify.sh`
- `scripts/test_lifecycle_document_contract.py`

Read-only context:
- `scripts/test_verifiable_handoff_text.py` — existing Review Choice assertions that must keep passing unchanged
- `skills/dev-implementation/resources/scripts/run_external_review.py` — the final command line
- `.devtool/epic/local_model_review/2026-10-21-local-model-review-design.en.md` — Workflow Changes and Risks

## Design Rationale

The runtime skills carry the rule, the human documents carry the diagram, and the contract test
pins both, as the earlier lifecycle epics did. Existing asserted phrases stay verbatim and the
third option is added beside them, so `test_verifiable_handoff_text.py` passes without an edit.
`CHANGELOG.md` is not touched: the release commit writes the dated notes that `scripts/release.sh`
requires. Applicable skills: `d3nexus:writing-skills`, `d3nexus:doc_quality_check`,
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: Review Choice sections of both skills, rule 5, the Gate 4 loop
  diagrams and paragraphs of the lifecycle documents, `verify.sh` step running the runner suite.
- **Downstream callers**: every agent at every Gate 4 PASS in every project using the plugin.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: every new token is asserted in both languages where it appears.

### BDD SCENARIOS

Covers: LMR-HP-01, LMR-ST-03

```gherkin
Scenario: [LMR-HP-01] [Tier C - Integration] Review Choice presents three options
  Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, rules/CRITICAL_RULES.md, docs/lifecycles.en.md and docs/lifecycles.vi.md
  When the lifecycle contract tests read them
  Then each names "Local model review" beside "Finish" and "Cross-model review"
  And dev-implementation shows "--cli ollama --model <model>" and tells the agent to run "ollama list" and ask
  And dev-lifecycle's Red Flags forbid picking the Ollama model for the developer

Scenario: [LMR-ST-03] [Tier C - Integration] Local model review returns to Gate 4 in full
  Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, docs/lifecycles.en.md and docs/lifecycles.vi.md
  When the lifecycle contract tests read them
  Then each routes Local model review through its round-recorded edge ("round recorded", or "đã ghi nhận round" in Vietnamese) back to Phase 4 or Gate 4 in full
  And none routes it straight to Gate 5
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest scripts/test_lifecycle_document_contract.py -k lmr` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest scripts/test_lifecycle_document_contract.py` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff_text.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent scripts/test_lifecycle_document_contract.py` | exit 0 | — |
| V6 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-bilingual docs/lifecycles.en.md docs/lifecycles.vi.md docs/choosing-a-lifecycle.en.md docs/choosing-a-lifecycle.vi.md` | exit 0 | — |
| V7 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/local-review-setup.md` | exit 0 | — |
| V8 | TIER-B | `bash scripts/verify.sh` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/local-model-review.xml skills/dev-implementation/resources/scripts/test_local_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py scripts/test_lifecycle_document_contract.py scripts/test_verifiable_handoff_text.py` | exit 0; results build/test-results/local-model-review.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `skills/dev-lifecycle/SKILL.md` would exceed 2,500 words or `skills/dev-implementation/SKILL.md`
  4,500 words, the limits `test_lifecycle_document_contract.py` enforces.
- An existing assertion of `test_verifiable_handoff_text.py` would need to change.

## Decisions Already Made

- Phrases asserted today stay verbatim, including "Cross-model review → Gate 4 in full",
  "Cross-model review must return to a full Gate 4 run", "picking the review CLI for the developer",
  `XR -->|"round recorded"| G4` and `review -- "round recorded" --> phase4`.
- `skills/dev-implementation/SKILL.md` Review Choice: the prompt lists
  `3. **Local model review** — a model served by your local Ollama reviews the epic task by task (`ollama list`).`;
  option 3 runs, after the agent runs `ollama list` and asks which model, never picking it:
  `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>`;
  sampling and context come from the model's Modelfile and `--num-ctx` overrides the context; each
  round is committed as `[EPIC_NAME] Record local model review round N`; the HARD-GATE names the
  three options; the invariant line adds "Local model review → Gate 4 in full"; the transitions
  comment adds `choice -- "Local model review" --> localreview` and
  `localreview -- "round recorded" --> phase4`; the setup reference is linked.
- `skills/dev-lifecycle/SKILL.md`: the Review Choice loop lists **Option 3: Local model review**;
  the invariant adds "Local model review → Gate 4 in full"; the transitions add
  `RC -->|"3. Local model review"| LR` and `LR -->|"round recorded"| G4`; the fast-executor
  recommendation adds "Local model review does not replace it."; Red Flags add
  "Picking the Ollama model for the developer instead of running `ollama list` and asking."
- `rules/CRITICAL_RULES.md` rule 5 lists **Option 3: Local model review** with the same command and
  the `ollama list` rule, and adds "Local model review follows the same loop." after item 3.
- `docs/lifecycles.en.md`: node `LR["run_external_review.py run --cli ollama<br/>(review_results.md committed per round)"]`,
  edges `RC -->|"3. Local model review"| LR` and `LR -->|"round recorded"| G4`, the `RC` label names
  the three options, and the Gate 4 paragraph names Local model review. `docs/lifecycles.vi.md`
  mirrors it with the edge label `"đã ghi nhận round"`, as its `XR` edge does.
- `docs/choosing-a-lifecycle.en.md` and `.vi.md` describe Review Choice as Finish, Cross-model
  review or Local model review.
- `local-review-setup.md` shows the reference Modelfile of `qwen38-reviewer` (Qwen3.8 27B Q8,
  `num_ctx 65536`, temperature 0.2, no `SYSTEM`, a template that opens `<think>` without closing it)
  and explains that a template pre-filling an empty `<think></think>` turns thinking off.
- `scripts/verify.sh` runs `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py || FAILED=1`
  next to the existing runner suite line.
- New tests in `test_lifecycle_document_contract.py`: `test_lmr_hp_01_review_choice_presents_three_options`
  and `test_lmr_st_03_local_model_review_returns_to_gate_4`.

## Definition of Done

- Both covered scenarios pass in the epic's JUnit report. (V2, V9)
- The existing Review Choice assertions pass unchanged. (V3)
- Lint and strict type checking report zero issues on the contract test. (V4, V5)
- The changed bilingual documents and the setup reference pass the document checker. (V6, V7)
- `scripts/verify.sh` passes on the candidate. (V8)
- The Integration results command of the HLD exits 0 and writes its report. (V9)
- The local review round of this epic, taken at Review Choice with `qwen38-reviewer`, reads as
  useful to the developer. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 6](task_6_wire_local_review_into_runner.md)

## References & Rollback

- [Epic HLD](../epic/local_model_review/local_model_review.en.md), Rollout Strategy.
- [Approved spec](../epic/local_model_review/2026-10-21-local-model-review-design.en.md), Workflow Changes.
- **Rollback**: revert the commit; option 3 disappears from the text while the runner keeps working.
