---
id: "task_04_english_only_resolution_and_ownership_check"
status: "done"
completedAt: "2026-11-17T08:47:31Z"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T08:47:31Z"
labels: ["english-only", "contract", "readiness"]
order: "a4"
review_tier: "full"
---

# Task 4: English-Only Document Resolution and Exclusive Ownership Check

Epic: [four_persona_governance](four_persona_governance.en.md)

## Requirement Analysis

Make the dev-implementation scripts English-only (spec §6.2–§6.3, [SE-02]) and add the ownership rule
(spec §7).

1. **Helper (`_epic_docs.py`, new)**: `resolve_epic_doc(directory, stem)` → `<stem>.md`, else
   `<stem>.en.md`, else `None`; never a `.vi.md`. Also `resolve_design_specs(directory)` returning
   `*-design.md` then `*-design.en.md` files, never `.vi.md`. Readers of git history use
   `resolve_epic_doc_at(root, rev, epic_rel, stem)`, which applies the same order to the tree at `rev`.
2. **Callers**: `check_epic_readiness.py` (`load_context` L77-L115, `check_preflight` L124-L229,
   `check_bdd_scenarios` L340-L374, `check_metadata` L744-L826), `package_epic.py`
   (`resolve_base_branch` L68-L82, `_sanitize_read_first_english_only` L92-L123,
   `update_epic_status_to_packaged` L287-L309), `sync_task_status.py` (`is_task_file` L79-L83,
   `find_epic_slug` L666-L685, `archive_epic_tasks` L759-L839, `sync_epic` L842-L922,
   `check_epic_prerequisites` L1199-L1239, `render_epic_tasks` L1326), `check_bdd_traceability.py`
   (`load_scenarios` L83, `main` L231-L299), `run_external_review.py` (`collect_facts` L658 and the
   epic-document listing at L393-L413 and L851-L868) resolve documents through the helper.
2a. **Remaining readers**: `audit_epic.py` (`audit_protected` L171-L190, `audit_amendments` L211-L227,
   `hld_amendments` L230-L241), `generate_smoke_checklist.py` (`generate_smoke_checklist` L174-L210, `main`
   L213-L256), `local_review.py` (`task_slice` L234-L249, `epic_slice` L252-L276), `run_task_checks.py`
   (`epic_scenario_ids` L282-L288), `task_contract.py` (`epic_layout` L403-L415, `_visit` L616-L651) and
   `integrate_branch.py` (`upstream_epics` L266-L276) resolve epic documents through the helper.
   `audit_epic.py::hld_amendments` and `integrate_branch.py::upstream_epics` read git revisions, not the
   working tree, so they use `resolve_epic_doc_at`: `upstream_epics` resolves `bdd_scenarios` at `until`;
   `hld_amendments` resolves the HLD at `base` and at `HEAD` independently.
3. **Status writes**: `sync_task_status.py epic` and `package_epic.py` update the Status line only in the
   resolved English file; `.vi.md` is neither read nor written.
4. **`--strict-bilingual`**: accepted by `check_epic_readiness.py` and `check_bdd_traceability.py` as a
   no-op that prints `warning: --strict-bilingual is deprecated and ignored` once to stderr. `_check_vi_sync_metadata`
   (`L676-L741`) and every `.vi.md` branch are removed.
5. **Ownership (`check_task_contract.py`)**: new `check_exclusive_ownership(check, tasks)` called from `main`
   (`L828-L893`) under `--design`, using `Blocked by` links (same parsing as
   `compute_execution_order.parse_blockers`) to build reachability; finding id `R-OWN`.
6. **Baseline lint**: `package_epic.py` `L440` `except Exception: pass` (ruff S110) logs the exception to stderr.
7. **Tests**: new `tests/test_fpg_english_only_and_ownership.py` (FPG-HP-06, FPG-HP-09, FPG-EC-04, FPG-AR-02); update
   existing tests that assert `.vi.md` writes or strict-bilingual failures.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/_epic_docs.py` (new)
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/package_epic.py`
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py`
- `skills/dev-implementation/resources/scripts/local_review.py`
- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/task_contract.py`
- `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`
- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
- `tests/test_tto_bilingual_and_surgical.py`
- `tests/test_multi_epic_governance_acceptance.py`
- `tests/test_rsdh_orchestration.py`
- `tests/test_fpg_english_only_and_ownership.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/compute_execution_order.py` — `parse_blockers` (L78-L84)
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — Key Design Mechanics 6 and 7, [SE-02]

## Design Rationale

One resolver keeps legacy epics working while new epics drop the suffix, and removing every `.vi.md` branch
from tooling is what makes the context-loading rule enforceable. Applicable skills:
`d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/check_epic_readiness.py`: `Context` (L45-L57), `load_context` (L77-L115), `check_preflight` (L124-L229), `check_bdd_scenarios` (L340-L374), `_check_vi_sync_metadata` (L676-L741), `check_metadata` (L744-L826), `main` (L1030-L1118)
  - `skills/dev-implementation/resources/scripts/package_epic.py`: `resolve_base_branch` (L68-L82), `_sanitize_read_first_english_only` (L92-L123), `update_epic_status_to_packaged` (L287-L309), S110 at (L436-L442)
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `is_task_file` (L79-L83), `find_epic_slug` (L666-L685), `archive_epic_tasks` (L759-L839), `sync_epic` (L842-L922), `check_epic_prerequisites` (L1199-L1239), `render_epic_tasks` (L1326-L1400)
  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `load_scenarios` (L83-L120), `main` (L231-L299)
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `collect_facts` (L658-L700), epic document listing (L393-L413), (L851-L868)
  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_duplicate_new_claims` (L231-L253), `main` (L828-L893)
  - `skills/dev-implementation/resources/scripts/audit_epic.py`: `audit_protected` (L171-L190), `audit_amendments` (L211-L227), `hld_amendments` (L230-L241)
  - `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py`: `generate_smoke_checklist` (L174-L210), `main` (L213-L256)
  - `skills/dev-implementation/resources/scripts/local_review.py`: `task_slice` (L234-L249), `epic_slice` (L252-L276)
  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `epic_scenario_ids` (L282-L288)
  - `skills/dev-implementation/resources/scripts/task_contract.py`: `epic_layout` (L403-L415), `_visit` (L616-L651)
  - `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`: `upstream_epics` (L266-L276)
  - `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py`: `test_prv_fr_02_failing_preflight_subcheck_and_missing_dir` (L536-L577), `test_tto_same_heading_prose_drift_and_strict_bilingual_provenance` (L887-L944)
  - `skills/dev-implementation/resources/scripts/test_sync_task_status.py`: `test_updates_both_en_and_vi_docs` (L417-L435), `test_updates_a_status_line_with_the_colon_inside_the_bold` (L437-L455), `test_handles_vietnamese_meta_data_label` (L457-L470), `test_updates_table_blockquote_unbulleted_yaml_and_case_variants` (L479-L532), `test_prv_hp_05_own_worktree_updated` (L1082-L1095), `test_TCAE_EC_01_legacy_task_backward_compatible` (L1123-L1206), `test_TCAE_ST_01_orphan_mirrors_and_location_aware_links` (L1307-L1429), `test_TCAE_HP_02_render_single_source` (L1432-L1555)
  - `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`: `test_vietnamese_sibling_with_same_identifiers_passes` (L78-L87), `test_vietnamese_sibling_missing_identifier_fails` (L89-L100), `test_absent_vietnamese_sibling_tolerated_by_default_fails_strict` (L102-L122)
  - `skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py`: `test_MEO_FR_02_spec_errata_asymmetry_and_missing_reason` (L198-L244), `test_tto_handoff_and_revise_exclude_vi_md_from_read_first` (L287-L332)
  - `skills/dev-implementation/resources/scripts/test_check_task_contract.py`: `test_cross_category_new_claim_collision_rejected` (L741-L751)
  - `tests/test_tto_bilingual_and_surgical.py`: `test_tto_hp_03_option_a_default_readiness` (L56-L100), `test_tto_st_03_strict_bilingual_stage4_gate` (L338-L436)
  - `tests/test_multi_epic_governance_acceptance.py`: `test_MEO_HP_01_to_04_end_to_end_multi_epic_governance` (L89-L312)
  - `tests/test_rsdh_orchestration.py`: `test_rsdh_ec_03_stage3_revise_vs_stage2_strict` (L411-L669)
- **Downstream Callers**: `audit_epic.py`, `run_task_checks.py`, `manage_worker_pool.py`, `check_tasks.py` (Task 5 imports `_epic_docs.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: `.md`, `.en.md` and absent cases for every caller; ownership pass, fail and ordered-pass.

### BDD SCENARIOS

Covers: FPG-HP-06, FPG-HP-09, FPG-EC-04, FPG-AR-02


```gherkin
Scenario: [FPG-HP-06] [Tier C - Integration] A new English-only epic passes readiness and packaging with single files
Given epic "solo_epic" containing "solo_epic.md", "bdd_scenarios.md" and two valid task files, and no ".en.md" or ".vi.md" file
When "check_epic_readiness.py solo_epic" and "package_epic.py solo_epic" run
Then both exit 0
And "solo_epic.md" Meta Data reads "- **Status**: Packaged"
And no file matching "*.vi.md" or "*.en.md" exists under ".devtool/epic/solo_epic/"

Scenario: [FPG-HP-09] [Tier C - Integration] Downstream verifiers read English-only epic documents
Given epic "solo_epic" with "solo_epic.md" carrying an "Integration results" line and an amended "## Spec Errata" entry, "bdd_scenarios.md" with scenario "[SOLO-HP-01]", and no ".en.md" or ".vi.md" file
When "generate_smoke_checklist.py --epic-dir solo_epic", "run_task_checks.py status" for a task covering "SOLO-HP-01", "audit_epic.py solo_epic", the local review epic slice and "integrate_branch.py" upstream epic detection run
Then the smoke checklist lists "SOLO-HP-01"
And the task status reports scenario "SOLO-HP-01" as covered
And the audit reports the HLD amendment from "solo_epic.md"
And the review slice includes "solo_epic.md" and "bdd_scenarios.md"
And upstream epic detection names "solo_epic"
And upstream epic detection reports "bdd_scenarios.md" for "solo_epic" when that file exists only at the upstream revision and not in the working tree
And when the base revision holds "solo_epic.en.md" and HEAD holds the renamed "solo_epic.md" with a changed "Integration results" line, the audit reports exactly that line change

Scenario: [FPG-EC-04] [Tier C - Integration] A legacy bilingual epic resolves the English file and never reads the mirror
Given epic "legacy_epic" with "legacy_epic.en.md", a stale "legacy_epic.vi.md", "bdd_scenarios.en.md" and "bdd_scenarios.vi.md"
And a file-open spy recording every path the scripts read
When "check_epic_readiness.py legacy_epic --strict-bilingual", "sync_task_status.py epic legacy_epic Packaged" and "check_bdd_traceability.py plan" run
Then all exit 0 and readiness prints one warning containing "--strict-bilingual is deprecated"
And "legacy_epic.en.md" reads "- **Status**: Packaged" while "legacy_epic.vi.md" bytes are unchanged
And the spy recorded no path ending in ".vi.md"

Scenario: [FPG-AR-02] [Tier A - Unit] Parallel tasks must own disjoint files
Given tasks "task_01" and "task_02" with no Blocked by path between them, both listing "scripts/foo.py (L10-L20)" and "scripts/foo.py" respectively in Allowed files
When "check_task_contract.py --design" runs over both
Then it exits 1 with a finding "R-OWN" naming "task_01", "task_02" and "scripts/foo.py"
When "task_02" declares "Blocked by [Task 01]"
Then the same command exits 0
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_english_only_and_ownership.py::test_fpg_ar_02_parallel_tasks_must_own_disjoint_files` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_english_only_and_ownership.py tests/test_tto_bilingual_and_surgical.py tests/test_multi_epic_governance_acceptance.py tests/test_rsdh_orchestration.py` | exit 0; contains "passed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_check_epic_readiness.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
| V7 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 skills/dev-implementation/resources/scripts/test_audit_epic.py skills/dev-implementation/resources/scripts/test_local_review.py skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py tests/test_smoke_checklist_generator.py` | exit 0 | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_epic_docs.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/task_contract.py skills/finishing-a-development-branch/resources/scripts/integrate_branch.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py skills/dev-implementation/resources/scripts/_epic_docs.py skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/package_epic.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/task_contract.py skills/finishing-a-development-branch/resources/scripts/integrate_branch.py --ignore-missing-imports --follow-imports=silent` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_04.xml tests/test_fpg_english_only_and_ownership.py` | exit 0; results build/test-results/fpg_task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- New contract: `resolve_epic_doc(directory: Path, stem: str) -> Path | None` and
  `resolve_design_specs(directory: Path) -> list[Path]` in `_epic_docs.py`; callers import it via the same
  `sys.path` pattern the dev-implementation scripts already use for siblings.
- New contract: `resolve_epic_doc_at(root: Path, rev: str, epic_rel: str, stem: str) -> str | None` returns the
  repo-relative path `<epic_rel>/<stem>.md` when `git -C <root> cat-file -e <rev>:<path>` exits 0, else
  `<epic_rel>/<stem>.en.md` under the same test, else `None`; it never returns `.vi.md` and never reads the
  working tree.
- Source: `upstream_epics` (`integrate_branch.py` L266-L276) keeps `"bdd": None` when no candidate exists at
  `until`; `hld_amendments` (`audit_epic.py` L230-L241) treats a revision with no resolved HLD as empty text,
  as `show()` returning `None` does today, and labels the diff with each revision's own file name.
- New contract: ownership finding text `R-OWN <task_a> and <task_b> both own <path>[, <path>...] with no
  Blocked by path between them`; paths normalised by stripping `(new)`, backticks, symbol names and
  `(L<start>-L<end>)` anchors and a leading `./`.
- New contract: `--strict-bilingual` remains a recognised flag (`action="store_true"`) on
  `check_epic_readiness.py` and both `check_bdd_traceability.py` subcommands; when set, print
  `warning: --strict-bilingual is deprecated and ignored` to stderr once and continue.
- Source: status lines are matched by the existing Meta Data regex in `update_epic_status_to_packaged`
  (`L287-L309`); only the English label `Status` is written; the `Trạng thái` alternative is dropped.
- Source: `run_external_review.py` already excludes `*.vi.md` from git diffs (`:(exclude)*.vi.md`); those
  pathspecs stay.
- The baseline mypy `import-not-found` errors for sys.path-injected siblings are why V5 passes
  `--ignore-missing-imports`.
- Source: `integrate_branch.py` has four existing mypy `arg-type` errors (near L253, L325, L328, L342) that V5 reports
  because the file is listed. Fix them with typing-only changes (annotations or narrowing, no behaviour change). A
  type error in a module that V5 does not list, such as `scripts/resume_context.py` (owned by Task 2), is outside
  this task: V5 passes `--follow-imports=silent`, so it is not reported ([SE-08](four_persona_governance.en.md#spec-errata)).
- Tests load script modules via `importlib.util.spec_from_file_location` inside fixtures.

## Definition of Done

- FPG-HP-06, FPG-HP-09, FPG-EC-04 and FPG-AR-02 pass. (V2, V6)
- Updated dev-implementation, bilingual and multi-epic suites pass. (V2, V3)
- Audit, local review, task checks, branch integration and smoke checklist suites pass unchanged on legacy `.en.md` fixtures. (V7)
- Ruff (including S110 in `package_epic.py`) and mypy pass on every touched script. (V4, V5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 4): `task_05`.

## References & Rollback

- [Epic HLD](four_persona_governance.en.md)
- **Rollback**: Revert the task commit; `.en.md` epics behave as before.
