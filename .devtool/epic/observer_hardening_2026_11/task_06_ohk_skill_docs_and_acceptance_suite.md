---
id: "task_06_ohk_skill_docs_and_acceptance_suite"
status: "todo"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T22:10:00Z"
completedAt: null
labels: ["architecture", "documentation", "acceptance"]
order: "a6"
review_tier: "full"
---

# Task 6: Update Kit Skills/References for Observations `#4`, `#5`, `#6`, `#8`, `#9`, `#11`, `#12`, `#13`, `#15`, `#16`, Register Suites in `verify.sh`, and Add Final Tier C Acceptance Suite

Epic: [observer-hardening-2026-11](observer_hardening_2026_11.md)

## Requirement Analysis

Apply all skill and reference documentation updates required by Clusters 1–4, register all new `tests/test_ohk_*.py` suites in `scripts/verify.sh`, and write the final Tier C acceptance suite verifying every skill contract, merge-hygiene invariant, and `bash scripts/verify.sh --full`:

1. **`#4` Visual Companion Asset Persistence**:
   - `skills/dev-brainstorming/SKILL.md` ("Routing After Approval" & "Visual Companion"), `skills/dev-brainstorming/visual-companion.md`, `skills/dev-designer/SKILL.md` (Step 1 Meta Data), `skills/dev-designer/references/task-template-examples.md` (§5): persist approved Visual Companion HTML files from `.superpowers/brainstorm/` into `.devtool/epic/<epic_dir>/assets/` and link under `Approved Visual Companions`.
2. **`#5` Deferred Step 1 Task Links**:
   - `skills/dev-designer/SKILL.md` (Step 1 & Step 2), `skills/dev-designer/references/task-template-examples.md` (§5 item 9), `skills/doc-designer/SKILL.md` (Step 4 & The Overview Document): use inline code spans (`` `task_01_...md` ``) in Step 1 before Gate 2 creates task files, and upgrade to relative Markdown links (`[Task 01](task_01_...md)`) in Step 2 right after writing task files.
3. **`#6` Scoped `R8 --replay` Guidance**:
   - `skills/dev-designer/SKILL.md` (Step 3.1): keep `check_epic_readiness.py <epic_name>` universal and scope `--replay` to epics whose tasks embed literal `Create`/`Replace in`/`Insert in` patch directives (noting contract-based tasks self-skip `R8`).
4. **`#8` Multi-Template Cache-Bust Scope**:
   - `skills/dev-designer/SKILL.md` (Step 2 `Allowed files`) & `skills/dev-designer/references/task-template-examples.md`: require grepping all `*.html`/`*.astro`/`*.jinja*` templates referencing modified `.css`/`.js` assets and adding them to the same task's `Allowed files`.
5. **`#9` Zsh-Safe Check 0 Snippet**:
   - `skills/doc_quality_check/SKILL.md` (Check 0): replace unquoted `$(git diff --name-only <base_ref>...HEAD)` with `git diff --name-only -z <base_ref>...HEAD | xargs -0 python3 skills/doc_quality_check/resources/scripts/check_document.py --changed-files`.
6. **`#11` Python `uv` Optional Extras & `UV_NO_SYNC=1` Docs**:
   - `skills/python-quality-check/SKILL.md`, `skills/python-quality-check/references/python-capability-contract.md`, `skills/dev-implementation/SKILL.md` (Phase 1 Step 5): document `--all-extras` bootstrap and `UV_NO_SYNC=1` preservation.
7. **`#12` `deferred: out-of-scope epic doc (§4.4)` Docs**:
   - `skills/cross-model-review/SKILL.md`, `skills/cross-model-review/references/review-triage.md`, `skills/dev-lifecycle/references/orchestration-roles.md` (§4.4): document the machine-recorded `deferred: out-of-scope epic doc (§4.4)` decision token for `Minor` code-review findings on immutable `.devtool/epic/` files.
8. **`#13` `sync_contracts.py diff-check --allow-dirty` Docs**:
   - `skills/sync-shared-contracts/SKILL.md`, `skills/dev-designer/SKILL.md`: document `--allow-dirty` for uncommitted `review_tier: "full"` Tier C task tests while preserving strict default clean-tree enforcement at Gate 4.
9. **`#15` Shared `.venv` Symlink `PYTHONPATH` + `UV_NO_SYNC=1` Guidance**:
   - `skills/using-git-worktrees/SKILL.md` (Step 2), `skills/subagent-driven-development/SKILL.md`, `skills/dev-implementation/SKILL.md`: require `UV_NO_SYNC=1 PYTHONPATH="$WORKTREE_ROOT/src"` whenever reusing a symlinked parent `.venv`.
10. **`#16` Quality-Manifest Commands, Ban Bare `npx`, and Non-Overlapping 180s Timer**:
    - `skills/writing-plans/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/dev-designer/references/verification-rows.md`: require reading `.agents/quality/*-quality.json` for canonical `type_check`/`lint` commands and forbid bare `npx <bin>` without `--no-install` (or explicit `--yes --package <pkg>`).
    - `skills/subagent-driven-development/SKILL.md`: keep the existing `**Waiting on dispatched subagents:**` paragraph unchanged for merge hygiene with `feat/bg-task-watchdog-and-stall-detection`, and add a standalone bullet immediately below it pairing `invoke_subagent` with `schedule(DurationSeconds=180, TimerCondition="any")`.
11. **Registration & Final Acceptance Suite**:
    - Register all six `tests/test_ohk_*.py` suites in `scripts/verify.sh` (`SUITES` list).
    - Author `tests/test_ohk_docs_and_acceptance.py` verifying `OHK-HP-06`, `OHK-AR-02`, and `OHK-AR-03` (including executing `bash scripts/verify.sh --full` when not already nested inside `VERIFY_SH_ACTIVE=1` — wait: assert `bash scripts/verify.sh --full` directly in a non-nested test or check `VERIFY_SH_ACTIVE` safely so running `verify.sh` never recurses infinitely!).

## Files

Allowed files:
- `skills/dev-brainstorming/SKILL.md`
- `skills/dev-brainstorming/visual-companion.md`
- `skills/dev-designer/SKILL.md`
- `skills/dev-designer/references/task-template-examples.md`
- `skills/dev-designer/references/verification-rows.md`
- `skills/doc-designer/SKILL.md`
- `skills/doc_quality_check/SKILL.md`
- `skills/using-git-worktrees/SKILL.md`
- `skills/subagent-driven-development/SKILL.md`
- `skills/dev-implementation/SKILL.md`
- `skills/python-quality-check/SKILL.md`
- `skills/python-quality-check/references/python-capability-contract.md`
- `skills/cross-model-review/SKILL.md`
- `skills/cross-model-review/references/review-triage.md`
- `skills/dev-lifecycle/references/orchestration-roles.md`
- `skills/sync-shared-contracts/SKILL.md`
- `skills/writing-plans/SKILL.md`
- `scripts/verify.sh`
- `tests/test_ohk_docs_and_acceptance.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`
- `tests/test_ohk_worktree_and_pool.py`
- `tests/test_ohk_revise_and_replay.py`
- `tests/test_ohk_python_env_and_doc_refusal.py`
- `tests/test_ohk_web_ui_audit.py`
- `tests/test_ohk_cmr_and_contracts.py`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.
- Strictly obey `CLAUDE.md` / `AGENTS.md`: `SKILL.md` frontmatter contains ONLY `name` and `description`; cross-references use `d3nexus:`; keep edits concise and surgical.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-brainstorming/SKILL.md` (L90-L115, L249-L266), `skills/dev-brainstorming/visual-companion.md` (L250-L263).
  - `skills/dev-designer/SKILL.md` (L21-L75), `skills/dev-designer/references/task-template-examples.md` (L26-L75, L176-L197), `skills/dev-designer/references/verification-rows.md` (L72-L88).
  - `skills/doc-designer/SKILL.md` (L95-L140).
  - `skills/doc_quality_check/SKILL.md` (L41-L53).
  - `skills/using-git-worktrees/SKILL.md` (L102-L130).
  - `skills/subagent-driven-development/SKILL.md` (L120-L135, L233-L246).
  - `skills/dev-implementation/SKILL.md` (L124-L142).
  - `skills/python-quality-check/SKILL.md` (L41-L55), `skills/python-quality-check/references/python-capability-contract.md` (L39-L47).
  - `skills/cross-model-review/SKILL.md` (L71-L103), `skills/cross-model-review/references/review-triage.md` (L12-L50).
  - `skills/dev-lifecycle/references/orchestration-roles.md` (L78-L97).
  - `skills/sync-shared-contracts/SKILL.md` (L86-L132).
  - `skills/writing-plans/SKILL.md` (L31-L60, L150-L185).
  - `scripts/verify.sh` (`SUITES` list, L450-L472).
- **Downstream Callers**: `tests/test_tto_docs_and_slimming.py`, `tests/test_fpg_governance_text.py`, `tests/test_fpg_english_only_text.py`, `tests/test_trc_reviewer_briefs_and_governance.py`, `scripts/test_lifecycle_document_contract.py`.
- **Target Coverage**: 100% of documentation contracts and `verify.sh` registration verified mechanically.

### BDD SCENARIOS

Covers: OHK-HP-06, OHK-AR-02, OHK-AR-03

```gherkin
Scenario: [OHK-HP-06] [Tier C - Integration] Updated kit skills preserve metadata contracts and observation rules
Given all skill and reference markdown updates across Clusters 1 through 4 are applied in the worktree
When kit skill contract verification inspects frontmatter, links, ToC anchors, and required policy directives
Then every SKILL.md contains exclusively "name" and "description" frontmatter keys
And skills document Visual Companion epic assets (#4), Step 1 code-span task links (#5), R8 --replay scoping (#6), multi-template Allowed files (#8), zsh-safe Check 0 (#9), uv --all-extras/UV_NO_SYNC (#11), deferred §4.4 token (#12), --allow-dirty (#13), shared .venv PYTHONPATH (#15), and quality-manifest/no-bare-npx/180s timer (#16)

Scenario: [OHK-AR-02] [Tier C - Integration] Non-overlapping watchdog timer guidance preserves merge hygiene in subagent-driven-development
Given "skills/subagent-driven-development/SKILL.md" in the epic worktree
When inspecting the "Waiting on dispatched subagents" section
Then the original paragraph wording from main remains intact to minimize conflicts with "feat/bg-task-watchdog-and-stall-detection"
And a dedicated follow-on bullet specifies pairing "invoke_subagent" with "schedule(DurationSeconds=180, TimerCondition=\"any\")"

Scenario: [OHK-AR-03] [Tier C - Integration] Kit verification gate verify.sh passes cleanly across all registered suites and contracts
Given all implementation changes and new test suites are registered in "scripts/verify.sh"
When "bash scripts/verify.sh --full" executes in the epic worktree
Then every static section (1 through 10) and all registered unittest and pytest suites exit 0 with "PASS — safe to publish"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_docs_and_acceptance.py::test_ohk_hp_06_skill_contracts_and_directives` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_docs_and_acceptance.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_tto_docs_and_slimming.py tests/test_fpg_governance_text.py tests/test_fpg_english_only_text.py tests/test_trc_reviewer_briefs_and_governance.py && python3 scripts/test_lifecycle_document_contract.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && ruff format --check tests/test_ohk_docs_and_acceptance.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent tests/test_ohk_docs_and_acceptance.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_worktree_and_pool.py tests/test_ohk_revise_and_replay.py tests/test_ohk_python_env_and_doc_refusal.py tests/test_ohk_web_ui_audit.py tests/test_ohk_cmr_and_contracts.py tests/test_ohk_docs_and_acceptance.py --junitxml=build/test-results/ohk_acceptance.xml` | exit 0; results build/test-results/ohk_acceptance.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Recursion Guard for `OHK-AR-03` inside `verify.sh`**: `scripts/verify.sh` exports `VERIFY_SH_ACTIVE=1` (line 9). Inside `test_ohk_ar_03_verify_sh_passes`, when `os.environ.get("VERIFY_SH_ACTIVE") == "1"` (meaning `verify.sh` itself is already running all static sections and suites), validate that all 6 `tests/test_ohk_*.py` paths are registered in `scripts/verify.sh` and execute sections 1–10 checks without recursively spawning `verify.sh --full`; when invoked standalone (outside `VERIFY_SH_ACTIVE=1`, such as during `V2` / `V5` / `Integration results`), execute `bash scripts/verify.sh --full` directly and assert exit 0 and `"PASS — safe to publish"` in stdout!
- **Merge Hygiene (`OHK-AR-02`)**: Keep lines 233–242 of `skills/subagent-driven-development/SKILL.md` (`**Waiting on dispatched subagents:** ... not at the end of the session.`) byte-identical to `main`, adding a new bullet right after line 242 for `invoke_subagent` + `schedule(DurationSeconds=180, TimerCondition="any")`.
- **Frontmatter & Links**: Never add extra keys to any `SKILL.md` frontmatter (strictly `name` + `description`), use `d3nexus:` cross-references, and preserve every anchor tested by `verify.sh` sections 2, 3, 4, 5, 7, 8, 9, 10 and `test_tto_docs_and_slimming.py`.

## Definition of Done

- [ ] All 10 observation doc updates (`#4`, `#5`, `#6`, `#8`, `#9`, `#11`, `#12`, `#13`, `#15`, `#16`) applied cleanly with valid frontmatter, links, and ToC anchors (V2, V3)
- [ ] `skills/subagent-driven-development/SKILL.md` preserves the original Waiting paragraph verbatim and adds the 180s `invoke_subagent` bullet (V2)
- [ ] All six `tests/test_ohk_*.py` suites registered in `scripts/verify.sh` and `bash scripts/verify.sh --full` exits 0 (`PASS — safe to publish`) (V2, V4, V5, V6)
- [ ] Full 20-scenario Tier C integration suite passes with JUnit XML evidence at `build/test-results/ohk_acceptance.xml` (V6)

## Dependencies & Blockers

Blocked by [Task 1](task_01_ohk_worktree_status_and_pool_isolation.md), [Task 2](task_02_ohk_revise_reanchor_and_replay_skip.md), [Task 3](task_03_ohk_python_uv_bootstrap_and_doc_refusal.md), [Task 4](task_04_ohk_web_ui_audit_subdir_and_hotfix.md), [Task 5](task_05_ohk_cmr_deferred_smoke_and_contracts_dirty.md).

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
