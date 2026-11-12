# Cross-Model Review: token_throttling_optimization

## Round 1

- **Date**: 2026-11-12T23:13:07Z
- **SHA**: 76bb5a29e54ae15a55037b042973ba825225e49b
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/token_throttling_optimization_code_round1_76bb5a2.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/run_external_review.py:530 | `fact()` collapses exit-0 commands to `PASS: <label>`, so `audit_epic.py`'s grader-amendment, protected-path, commits-outside-tasks and Gate 5 disclosures never reach the reviewer, while `references/external-review-prompt.md:31` and its Checklist still require the reviewer to judge them. Proposed: exempt `audit_epic.py` from the collapse (or emit only its `###` sections), or drop those Checklist items. | fixed in 9a9877b |
| 2 | Important | skills/dev-implementation/resources/scripts/run_external_review.py:672 | `artefact_lines()` still lists `principal_review.md` (979,111 bytes of raw transcripts on this epic) as a path the code reviewer must read, re-introducing the exact bloat the HLD Background targets, even though `delta_round_context()` already excludes that file. Proposed: filter `principal_review.md` and `review_results.md` out of `artefact_lines()`. | fixed in 9a9877b |
| 3 | Important | rules/CRITICAL_RULES.md:53 | §6 (and `skills/dev-lifecycle/references/governance-checklists.md:25`) still mandate a Role 2.2-reviewed `fix_plan_round<N>.md` for every valid Stage 3 blocker, contradicting the fast-track bypass shipped at `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:2170`; no kit document records the carve-out. Proposed: document the source-grounded unambiguous-code-defect fast path and its halt conditions in §6 and §1.2. | fixed in 9a9877b |
| 4 | Minor | skills/dev-implementation/resources/scripts/run_external_review.py:744 | the hunk-header truncation marker is gated on total `budget` instead of remaining `budget - used`, so the payload can exceed `max_bytes` (probed: 60,033 bytes at `max_bytes=60000`). Proposed: compare against `budget - used`. | fixed in 9a9877b |
| 5 | Minor | scripts/resume_context.py:1419 | the `break` exits only the inner `for ep_dir` loop, so each candidate root appends its own `HLD (...)` line; live output shows the same path twice with conflicting `Status` values ("In Progress" vs "Packaged (2026-11-12)"). Proposed: break out of the outer root loop once an HLD line is emitted. | fixed in 9a9877b |
| 6 | Minor | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:596 | `_extract_task_targets` emits non-path tokens under "Target files & line ranges" (probed on `task_04`: `RunnerConfig (L44-L80)`, `normalize_agy_effort`, `TTO-HP-04`). Proposed: require a path separator or file extension before accepting a token as a target. | fixed in 9a9877b |
| 7 | Minor | tests/test_lifecycle_runner.py:1500 | the `TTO-AR-01` fixture copies only `compute_execution_order.py`, `manage_worker_pool.py` and `slug_utils.py`, so the `sync_task_status.py` call at `cwd=slot_path` named in the scenario is never executed, and the strict `changed_files == {src/mod_a.py, src/mod_b.py, src/mod_c.py}` assertion holds only because of that omission. | fixed in 9a9877b |
| 8 | Minor | skills/dev-lifecycle/references/autonomous-mode.md:27 | the CLI flag list documents `--programmer-model` but omits the new `--programmer-effort` flag added in `lifecycle_runner.main()`. | fixed in 9a9877b |
| 9 | Minor | .devtool/epic/token_throttling_optimization/handoff.md:33 | `## Read First` still carries the unreplaced `<N>` and `<source spec>.en.md` placeholders that `package_epic.py` now substitutes; item 3 points at a path that does not exist. Proposed: re-run `package_epic.py --revise`. | fixed in 9a9877b, 9cd485d |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-12T23:39:51Z
- **SHA**: 562bd335cb93498688d63813ad177ce169050d78
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: PASS
- **Scope**: delta from round 1 (76bb5a2)
- **Raw log**: `build/reviews/token_throttling_optimization_code_round2_562bd33.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|

Raw output:

```text
Verdict: PASS
```
