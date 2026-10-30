# Cross-Model Review: context_memory_management

## Round 1

- **Date**: 2026-10-30T17:59:36Z
- **SHA**: 50f33c1e32166f8d19353846006a88eecfe4d490
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: PASS

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | scripts/test_resume_context.py:411 | test_cmm_fr_02_missing_contracts_and_git_fallback creates its non-git directory at `self.workspace/"lyrics-sync"`, but the harvest's scan root is `self.repo_dir` (which has its own `.git`), so `scan_git_status` takes the single-repo branch and never visits that directory — the scenario's "repo lacking a .git folder is skipped cleanly" clause isn't actually exercised, only the shared-contracts fallback clause is. | fixed in 5b1f43f |
| 2 | Minor | scripts/test_resume_context.py:248 | test_cmm_ar_01_concurrent_flock asserts only activity-log line counts after concurrent writes and never checks `.devtool/assistant_state.md`, despite CMM-AR-01's explicit "And .devtool/assistant_state.md contains valid snapshots for both epics" clause. | fixed in 5b1f43f |

Raw output:

```text
## Review: context_memory_management (candidate `50f33c1`)

**Scope confirmed.** The epic is fully implemented across 4 tasks (all `done`), with Gate 4 evidence (`evidence/task_0{1,4}.json`) showing every RED→GREEN transition, Ruff/Mypy clean, and a final `scripts/verify.sh` run ending `PASS — safe to publish`. The independent facts supplied (12/12 unit tests, 12/12 BDD traceability) are consistent with what the evidence JSON records.

**Spec → HLD → BDD → Tasks consistency.** All issues raised in Principal Review Round 1 (the Rule 7/8 collision, the 2476/2500-word risk in `dev-lifecycle/SKILL.md`, the inconsistent illustrative slugs, the combined-vs-split test function disagreement, the undeclared `test_lifecycle_signals.py` read, and the two Minor doc-consistency items) are genuinely fixed in the current tree, not just marked fixed:
- `rules/CRITICAL_RULES.md` has exactly one `## 7.` (untouched, from the prior `sync_shared_contracts` epic) and the new section is `## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline`, appended cleanly after it. A repo-wide grep found no stray "Rule 7" references for this epic outside `principal_review.md`'s own historical log (which correctly preserves the original finding text verbatim).
- `skills/dev-lifecycle/SKILL.md` is 2485/2500 words, `skills/dev-implementation/SKILL.md` is 3663/4500 words — both within ceiling, and neither contains a Mermaid or DOT fence (checked by grep, not just claimed).
- `bdd_scenarios.en.md` uses the real canonical slug `context_memory_management` (plus clearly-distinct `epic-alpha`/`epic-beta` placeholders) consistently; no leftover near-miss spellings.
- HLD Goals now says "6 CLI capabilities" and enumerates 6.

**Code grounding.** `scripts/resume_context.py` and `docs/architecture/resume_context.py` are byte-identical (`git diff` shows both ending at blob `c1abf15`), satisfying Task 1's Stop-and-Report condition against divergence. Every baseline symbol Task 1 claims to preserve (`print_section`, `ensure_ledger`, `read_tail`, `scan_project_ledger`, `scan_assistant_state`, `scan_activity_stream`, `scan_git_status`, `scan_open_rfcs`, `scan_active_tasks`, `complete_feature_and_rotate`) is present and extended, not replaced. `MAX_STATE_LINES = 20` and `enforce_state_line_limit` correctly keep all 4 mandatory fields under a hand-traced 20/25-line overflow case. Worktree routing (`resolve_primary_repo_root` via `git rev-parse --git-common-dir`) and epic-slug auto-detection (`resolve_current_epic_slug` via `epic/<slug>` branch prefix) both resolve correctly by trace-through against `test_cmm_ec_02_worktree_routing`, which uses a real `git worktree add`, not a mock.

**Test quality (no reconstructed logic, no synthetic substitution).** `scripts/test_resume_context.py` invokes the production CLI exclusively via `subprocess.run` against the real `scripts/resume_context.py`, inside real `tempfile.TemporaryDirectory()` git repos — it does not reimplement any retry/rollup/progress logic locally, satisfying the "no reconstructed logic" and "immutable real artifacts" rules.

Two tests, however, under-exercise the Gherkin clause they claim to cover (see findings below) — both are test-rigor gaps, not production defects; the underlying file-lock and full-overwrite design makes the unverified clauses correct by construction.

**Lifecycle hooks (Task 4).** Grepped every file in Task 4's `Allowed files` for the `resume_context.py` hook: present and correctly scoped in `dev-brainstorming`, `dev-designer`, `dev-lifecycle`, `handoff-template.md`, `principal-review.md`, `principal-review/SKILL.md`, `dev-implementation` (Phase 0/2/4), `cross-model-review`, and `finishing-a-development-branch`'s Pre-Finish Hook (`--complete "<epic_slug>" "<milestone_summary>"`, matching the Decisions Already Made exactly).

**Shared Contract Impact.** HLD states `None — self-contained`; no `shared-contracts/` directory exists in this repo (Workflows repo), and `scan_open_rfcs`'s existing graceful fallback is unchanged in spirit. No breaking-change or symlink concern applies here.

**Audit disclosures.** The task_03 grader amendment is the Principal-Review-driven Rule 7→8 fix plus two mechanical newline/link-sync commits — justified, not a post-hoc defect cover-up. `scripts/verify.sh` is the only protected-path change, and it is explicitly pre-authorized by the HLD's Verification Environment section and listed in Task 4's own `Allowed files`. No commits outside tasks.

**Gate 5 items**, restated: Task 1 (Two-Tier Multi-Epic CLI Engine), Task 2 (Shell Environment Sync), Task 3 (resume-context/save-context skills + Rule 8), and Task 4 (Lifecycle Integration & Verification Harness) each have their execution independently verified and recorded in `evidence/*.json` — confirmed by reading all four evidence files directly (RED failure → GREEN pass → final verify sequences, each with real command output and exit codes, not just assertions).

Verdict: PASS
[Minor] scripts/test_resume_context.py:411 — test_cmm_fr_02_missing_contracts_and_git_fallback creates its non-git directory at `self.workspace/"lyrics-sync"`, but the harvest's scan root is `self.repo_dir` (which has its own `.git`), so `scan_git_status` takes the single-repo branch and never visits that directory — the scenario's "repo lacking a .git folder is skipped cleanly" clause isn't actually exercised, only the shared-contracts fallback clause is.
[Minor] scripts/test_resume_context.py:248 — test_cmm_ar_01_concurrent_flock asserts only activity-log line counts after concurrent writes and never checks `.devtool/assistant_state.md`, despite CMM-AR-01's explicit "And .devtool/assistant_state.md contains valid snapshots for both epics" clause.
```

## Round 2

- **Date**: 2026-10-30T18:28:11Z
- **SHA**: c3b5eafdbf55daeb2da18891744ac2ee999a1da4
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/save-context/SKILL.md:56 | the documented `save-context --checkpoint <epic_slug> "<note>"` command (and the identical form in bdd_scenarios.en.md/.vi.md CMM-ST-02, context_memory_management.en.md/.vi.md, the source spec, and task_03's frozen Decisions Already Made) expands via the `save-context` alias to `resume_context.py --complete --checkpoint <slug> <note>`, which argparse rejects with exit 2 ("expected at least one argument") because `--checkpoint` immediately follows `--complete`'s nargs="+" with no value; the only working orders are `--checkpoint --complete <slug> <note>` or `--complete <slug> <note> --checkpoint` (the latter already correctly documented in docs/architecture/save_resume_rules.md:59), and the shipped test for CMM-ST-02 silently uses the working order instead of the documented one, so the breakage passed every gate. | fixed in 4734183 |
| 2 | Minor | scripts/resume_context.py:670 | `--json` is declared as part of the HLD's "6 CLI capabilities" Goals contract but `args.json` is never read anywhere in the implementation, so passing `--json` silently produces unchanged human-readable text instead of JSON; no task Verification row or BDD scenario exercises it. | fixed in 4734183 |

Raw output:

```text
Plan mode's exit tools (`ExitPlanMode`, `AskUserQuestion`) aren't available in this session, so I'll deliver the review directly as my response instead, per the actual review task's output contract.

## Principal/External Review — context_memory_management (candidate `c3b5eaf`)

**Scope checked:** all listed artefacts (spec EN/VI, handoff, principal_review rounds 1–2, HLD, BDD scenarios, all 4 task files, all 4 evidence JSON files), diffs of `scripts/resume_context.py`, `docs/architecture/resume_context.py`, `scripts/test_resume_context.py`, `rules/CRITICAL_RULES.md`, `scripts/verify.sh`, and all 9 lifecycle skill/reference files touched by Task 4, plus the disclosed out-of-task commit `5b1f43f`.

**Task evidence vs Verification/DoD.** All four tasks' RED rows show genuine `AssertionError`/`FAILED` failures (not collection errors), GREEN/ruff/mypy/JUnit rows all pass at exit 0. `scripts/resume_context.py` and `docs/architecture/resume_context.py` are byte-identical (confirmed via direct diff), satisfying Task 1's hard "must not diverge" Stop condition. Task 4's 9 target lifecycle files each gained exactly one `resume_context.py` hook line; `skills/dev-lifecycle/SKILL.md` sits at 2485/2500 words (the ceiling Principal Review round 1 flagged as nearly exhausted) with no Mermaid/DOT fences in either lifecycle skill; `scripts/verify.sh` Section 15 matches Task 4's Decisions exactly; Rule 8 was appended to `rules/CRITICAL_RULES.md` without colliding with the existing Section 7.

**Audit disclosures.** The task_03 grader amendment (Rule 7→8) traces directly to Principal Review round 1 finding #1, fixed in `988cacf` — justified. The protected-path change to `scripts/verify.sh` (`50f33c1`) is explicitly authorized by Task 4's Allowed files — justified. The out-of-task commit `5b1f43f` is a post-completion i18n fix (Vietnamese→English handoff prompt bodies, kept in sync across both `resume_context.py` mirrors) plus two test-assertion *additions* (strengthening, not weakening) — transparently disclosed, no scope creep. Shared Contract Impact is correctly declared `None` — no `shared-contracts/` path appears anywhere in the diff.

**Finding 1 — the documented checkpoint-save command is broken.** The source spec, both HLD language variants, both BDD scenario language variants, task_03's own frozen "Decisions Already Made", and the shipped `skills/save-context/SKILL.md` all document the same invocation for CMM-ST-02: `save-context --checkpoint <epic_slug> "<note>"`. Since `save-context` is aliased (task_02's frozen contract) to `resume_context.py --complete`, this expands to `resume_context.py --complete --checkpoint <epic_slug> "<note>"`. I reproduced the exact `argparse` configuration (`--complete` with `nargs="+"`, `--checkpoint` as `store_true`) in isolation with no filesystem side effects: this token order makes argparse exit 2 ("expected at least one argument"), because `--checkpoint` is itself a recognized flag and stops `--complete`'s collection before any value is consumed. Only `--checkpoint --complete <slug> <note>` or `--complete <slug> <note> --checkpoint` work — and `docs/architecture/save_resume_rules.md:59` already documents the second, working order correctly, so the fix was known elsewhere in the same change but never propagated to the skill, BDD scenario, HLD, or spec. The shipped test `test_cmm_st_02_checkpoint_non_destructive_save` doesn't reproduce the scenario's own "When" clause — it calls the args in the working order instead of the documented one — so this breakage passed every gate undetected.

**Finding 2 — `--json` is a dead flag.** The HLD's Goals section lists `--json` as part of its "6 CLI capabilities" contract. `argparse` declares it (`scripts/resume_context.py:670`) but `args.json` is never read anywhere in the implementation (confirmed by grep) — passing `--json` silently produces unchanged text output. No task's Verification row or BDD scenario references it, so no gate could have caught it; this is a gap against the HLD's aspirational list, not a frozen task contract.

**Gate 5 items:** all four tasks — execution verified and recorded in evidence — PASS.

Verdict: CHANGES REQUIRED
[Important] skills/save-context/SKILL.md:56 — the documented `save-context --checkpoint <epic_slug> "<note>"` command (and the identical form in bdd_scenarios.en.md/.vi.md CMM-ST-02, context_memory_management.en.md/.vi.md, the source spec, and task_03's frozen Decisions Already Made) expands via the `save-context` alias to `resume_context.py --complete --checkpoint <slug> <note>`, which argparse rejects with exit 2 ("expected at least one argument") because `--checkpoint` immediately follows `--complete`'s nargs="+" with no value; the only working orders are `--checkpoint --complete <slug> <note>` or `--complete <slug> <note> --checkpoint` (the latter already correctly documented in docs/architecture/save_resume_rules.md:59), and the shipped test for CMM-ST-02 silently uses the working order instead of the documented one, so the breakage passed every gate.
[Minor] scripts/resume_context.py:670 — `--json` is declared as part of the HLD's "6 CLI capabilities" Goals contract but `args.json` is never read anywhere in the implementation, so passing `--json` silently produces unchanged human-readable text instead of JSON; no task Verification row or BDD scenario exercises it.
```

## Round 3

- **Date**: 2026-10-30T18:49:37Z
- **SHA**: 3fcfd373550e084d5728e140c1b5baba784b3aba
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: PASS

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | scripts/test_resume_context.py:533 | test_cmm_hp_01_json_harvest_output is tagged [CMM-HP-01] even though --json/JSON serialization is not part of that scenario's Gherkin text, causing the BDD traceability report to credit CMM-HP-01 to this test instead of to its correctly-scoped sibling test_cmm_hp_01_multi_epic_state_log_and_complete_isolation (which still exists and passes, so this is a labeling inaccuracy rather than a coverage gap). | fixed in 5d9ef7c |

Raw output:

```text
## External Review — context_memory_management (candidate `3fcfd37`)

**Scope.** This is the review round following Cross-Model Review Round 2, which found one Important defect (the documented `save-context --checkpoint` command crashed argparse) and one Minor gap (`--json` was a dead flag). Both are recorded as `fixed in 4734183` in `review_results.md`. I independently re-derived both defects and verified the fix rather than trusting the decision table's claim.

**Checkpoint-order fix verified.** `parse_args` (`scripts/resume_context.py:772-778`) now detects the exact token sequence `--complete --checkpoint` (produced by the documented `save-context --checkpoint <slug> "<note>"` alias expansion) and rewrites it to `--checkpoint --complete` before argparse sees it — the only way to avoid `--complete`'s `nargs="+"` swallowing zero arguments when `--checkpoint` immediately follows. I traced this against argparse's real behavior rather than taking the commit message at face value. `test_cmm_st_02_checkpoint_non_destructive_save` (`scripts/test_resume_context.py:452-461`) now exercises both the documented alias order and the already-working `--complete <slug> <note> --checkpoint` order, closing exactly the gap the reviewer found: previously the test silently used only the working order. `docs/architecture/save_resume_rules.md` and `skills/save-context/SKILL.md` already documented the correct user-facing command; the fix corrected the implementation to match the contract, not the other way around.

**`--json` fix verified.** `main()` (`scripts/resume_context.py:869-871`) now reads `args.json` and dispatches to `harvest_json`/`collect_harvest_data`, which assembles the same six data categories the human-readable harvest prints. `scripts/resume_context.py` and `docs/architecture/resume_context.py` remain byte-identical (confirmed by direct diff), satisfying Task 1's non-divergence Stop condition.

**No new defects from the fix commits.** I hand-traced the token-reordering logic against both working orders and the previously-broken order; all three behave correctly now, and no other call site depends on the old (broken) token layout. `5b1f43f`'s two test-assertion additions were also checked against their stated purpose: `test_cmm_fr_02_missing_contracts_and_git_fallback` now runs with `cwd=self.workspace` and a real non-git `lyrics-sync` directory inside the `REPOS` iteration path, genuinely exercising the "repo lacking `.git` is skipped cleanly" clause it previously missed; `test_cmm_ar_01_concurrent_flock` now asserts `assistant_state.md` contains both `Active Epic: epic-alpha` and `Active Epic: epic-beta`, closing the previously-unverified clause. Both are strengthening additions, not weakened substitutes.

**Process disclosures re-checked.** Rule 8 in `rules/CRITICAL_RULES.md` is appended cleanly after the pre-existing, untouched Rule 7 — no heading collision. `scripts/verify.sh`'s Section 15 addition is explicitly authorized by Task 4's own Allowed files. The task_03 grader amendment is the Principal-Review-driven Rule 7→8 renumbering, traced to a real finding and a real fix commit, not a post-hoc contract rewrite. I re-ran the two lifecycle test suites Task 4's V5/V6 rows require (`test_lifecycle_document_contract.py`, `test_verifiable_handoff_text.py` + `test_lifecycle_signals.py`) myself: both pass cleanly (19 and 14 tests, exit 0), confirming no regression from the nine lifecycle-skill hook edits. Word ceilings hold (`dev-lifecycle` 2485/2500, `dev-implementation` 3663/4500), no Mermaid/DOT fences introduced. EN/VI scenario-ID sets in `bdd_scenarios.*.md` match exactly. `Shared Contract Impact: None` is accurate — no `shared-contracts/` path appears anywhere in the diff.

**One mislabeling, not a coverage gap.** `scripts/test_resume_context.py:533` tags `test_cmm_hp_01_json_harvest_output` with `[CMM-HP-01]`, but CMM-HP-01's Gherkin text (harvest sections, multi-epic isolation, `--complete` archiving) never mentions `--json`; this is why the BDD traceability tool's report credits CMM-HP-01 to this test rather than to its correctly-scoped sibling `test_cmm_hp_01_multi_epic_state_log_and_complete_isolation`, which still exists, still runs under the same `-k test_cmm_hp_01` filter in Task 1's V1/V2 rows, and still genuinely covers the scenario.

**Gate 5 items**, restated: Task 1 (Two-Tier Multi-Epic CLI Engine), Task 2 (Shell Environment Sync), Task 3 (resume-context/save-context skills + Rule 8), and Task 4 (Lifecycle Integration & Verification Harness) each have execution independently verified and recorded in `evidence/*.json` — confirmed by reading the Task 1 evidence directly (a genuine `FileNotFoundError`-driven RED failure before any GREEN pass, not a vacuous collection error).

No Critical or Important defect survived independent verification.

Verdict: PASS
[Minor] scripts/test_resume_context.py:533 — test_cmm_hp_01_json_harvest_output is tagged [CMM-HP-01] even though --json/JSON serialization is not part of that scenario's Gherkin text, causing the BDD traceability report to credit CMM-HP-01 to this test instead of to its correctly-scoped sibling test_cmm_hp_01_multi_epic_state_log_and_complete_isolation (which still exists and passes, so this is a labeling inaccuracy rather than a coverage gap).
```
