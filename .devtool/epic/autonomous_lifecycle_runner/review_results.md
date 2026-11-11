# Cross-Model Review: autonomous_lifecycle_runner

## Round 1

- **Date**: 2026-11-11T00:40:29Z
- **SHA**: f17e25d8a31792291001ba20da91d3015915b99c
- **Base**: main
- **CLI**: claude
- **Model**: sonnet
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:127 | ModelDispatcher.probe_model sends agy an undefined --probe flag; live agy --help/invocation confirms "flags provided but not defined: -probe" (exit 2), so every real (non-mocked) run aborts at INITIALIZED before reaching Principal Review. | fixed in 5d143c2 |
| 2 | Critical | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:819-868,507-545 | _draft_fix_plan/_apply_code_fixes/_apply_aligned_fixes/_apply_minor_fixes/_record_review_decisions never dispatch the Programmer or Assistant and never write decision cells into principal_review.md/review_results.md; they only commit whatever is already dirty, so review findings are never actually fixed despite Tasks 3 and 4's frozen contracts requiring it. | fixed in 5d143c2 |
| 3 | Critical | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:769-817 | run_gate4() omits audit_epic.py, the unit test suite, check_bdd_traceability.py, and the headless quality_check workflow mandated by Task 5's Decisions Already Made and the HLD's Method Execution Contract, and unconditionally returns PASS once the smoke checklist (exit code ignored) and review-decision check run. | fixed in 5d143c2 |
| 4 | Important | skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:870-895 | evaluate_programmer_fix_plan discards the dispatch exit code and defaults to FixPlanVerdict.APPROVED whenever the Assistant call fails or returns unparseable output, violating Task 4's "Stop and Report If: Fix plan verdict cannot be parsed" and creating a fail-open path around the CRITICAL_CONFLICT safety check. | fixed in 5d143c2 |

Raw output:

````text
## Review: autonomous_lifecycle_runner (candidate f17e25d)

### Task evidence vs. Verification tables

All five tasks show `done` status with Verification tables V1–V6 executed and the aggregate suite green (19/19, exit 0) and BDD traceability 17/17. Scenario-to-task mapping is 1:1 and each scenario ID appears in exactly one automated test (`test_alr_*`). Mechanically, the Gate 4 audit and the result-based traceability check both report PASS. However, every V1–V6 row for every task is a *process* check (tests run, lint/type clean) — none of them exercise the runner against a real `agy` binary or a real review-finding cycle end to end. That gap matters here because the defects below are precisely the kind that fully-mocked unit tests cannot surface, and they strike at the epic's stated goal ("fix-and-verify loop," "AI Assistant auto-applies aligned revisions," Gate 4 "in full").

### Dynamic probing results (per the Mandatory Dynamic Probing Rule)

I ran the real `agy` CLI (read-only, no prompts submitted) to check the exact invocation `ModelDispatcher.probe_model` builds in `lifecycle_runner.py:127`: `[cli, "--model", model, "--probe"]`.

```
$ agy --model nonexistent-test-model-xyz --probe
flags provided but not defined: -probe
AGY_EXIT:2
```

`agy --help` confirms there is no `--probe` flag anywhere in the CLI's surface (`--print`, `--mode`, `--model`, `--effort`, etc., but nothing resembling a probe/dry-run flag). The design doc only ever verified `agy --print "<prompt>" --model <model> --effort high --mode plan`. So `--probe` is an invented flag, never verified against the real binary, and the dynamic probe shows it is rejected deterministically with exit 2. Since `LifecycleRunner.run()` calls this probe unconditionally at `INITIALIZED` and aborts on any non-zero exit (`lifecycle_runner.py:284-292`), a real (non-dry-run, non-mocked) invocation of the runner can never advance past the very first state transition.

### Core "autonomous fix" pipeline does not apply fixes

Tracing every call site of `self.dispatcher.dispatch(...)` in `lifecycle_runner.py` (lines 438 and 880 only), the Programmer/Assistant subprocess is dispatched in exactly two places: once to implement a Kanban task (`_execute_single_task`), and once to get the Assistant's fix-plan verdict (`evaluate_programmer_fix_plan`). Nothing dispatches a model to:
- draft the fix plan in `_draft_fix_plan` (`lifecycle_runner.py:819-828`) — it just writes the raw triage text into the file, not a plan authored by the Programmer as Task 4 requires ("dispatches the AI Programmer ... to draft `fix_plan_round<N>.md`");
- apply the approved/adjusted fix in `_apply_code_fixes` (`lifecycle_runner.py:830-848`) — it only runs `git status --porcelain` and commits if something happens to already be dirty;
- apply aligned/minor Principal Review revisions in `_apply_aligned_fixes` / `_apply_minor_fixes` (`lifecycle_runner.py:507-545`) — same commit-if-dirty stub, no Assistant dispatch to actually revise the HLD;
- record `fixed in <sha>` decision cells into `principal_review.md` / `review_results.md` in `_record_review_decisions` (`lifecycle_runner.py:850-868`) — there is no write to either file anywhere in this module (confirmed by grep: `review_results.md` and `principal_review.md` never appear as write targets).

This is a direct contradiction of the frozen "Decisions Already Made" in both Task 3 and Task 4, and of the HLD sequence diagram ("Programmer applies fixes" → "Assistant auto-applies aligned revisions"). In real operation the working tree is unchanged after a finding is triaged, so the same finding(s) would simply reappear every round until the 3-round cap trips `MAX_ROUNDS_CRITICAL_REMAINING` — the autonomous loop cannot actually converge on a real review finding. The unit tests never catch this because every test that reaches these methods mocks them directly (`test_alr_hp_03`, `test_alr_ec_03`, `test_alr_hp_04` all `patch.object(runner, "_apply_code_fixes"/"_apply_aligned_fixes", ...)`), so the stub bodies are never exercised.

### Gate 4 is not the gate the HLD/task specifies

`run_gate4()` (`lifecycle_runner.py:769-817`) only runs the smoke-checklist generator (exit code ignored) and `run_external_review.py check`, then unconditionally returns `True, "Gate 4 PASS"`. Task 5's frozen contract and the HLD's "Method Execution Contracts" (`autonomous_lifecycle_runner.en.md:351-360`) both require `run_gate4` to also run `audit_epic.py`, the full test suite via `run_unittest_junit.py`, `check_bdd_traceability.py`, and the headless `quality_check` workflow with an aggregated PASS bound to the SHA. None of those four steps are invoked. `test_alr_st_02` doesn't catch this either — it mocks `subprocess.run` globally and only asserts `sync_gate_ledger` was called with `(4, ANY)`. As written, a candidate with failing tests, lint/type errors, a failed security audit, or BDD coverage gaps would still be certified "Gate 4 PASS" by this runner, which is exactly the local quality gate every subsequent stage (Cross-Model Review entry, Finish prompt) trusts.

### Fail-open fix-plan verdict parsing

`evaluate_programmer_fix_plan` (`lifecycle_runner.py:870-895`) discards the dispatch's exit code entirely (`_, stdout, _ = self.dispatcher.dispatch(...)`) and falls through to `return FixPlanVerdict.APPROVED, rationale` whenever the first output line doesn't literally contain `"CRITICAL_CONFLICT"` or `"ADJUSTED"`. That includes the case where `dispatch` fails outright (timeout → exit 124, missing binary, quota exhaustion) and `stdout` is empty, since `first_line` becomes `""` and none of the substring checks match. Task 4's "Stop and Report If" explicitly lists "Fix plan verdict cannot be parsed from the Assistant output" as a condition that should halt, not silently resolve to approval. As implemented, any Assistant-side failure is treated as an approval to apply code fixes — the opposite of the safety property the Assistant persona exists to provide (preventing unauthorized reversions, per `ALR-FR-04`).

### Other notes (non-blocking)

- `evaluate_circuit_breakers`'s signature (`stage, round_num, triage_stdout=""`) adds a parameter beyond the HLD's frozen `(self, stage: str, round_num: int) -> Optional[str]`. Harmless (default-valued, backward compatible) but worth reconciling with the "frozen" Module Contracts language.
- The dead branch in `run()` (`lifecycle_runner.py:301-305`) checking `active_stage in (HALTED, AWAITING_PRINCIPAL_CONFIRMATION)` after `step_principal_review()` returns `True` is unreachable given the current control flow in `step_principal_review` (every path to those two states returns `False` first). Not a defect, just redundant.
- The `task_3_principal_review_automation_and_checkpoint: patch changed after verify` audit disclosure is adequately explained by the recorded Principal Review revision commits (c52e7c4, f791c6a) already covered by the grader-amendment log; I don't treat it as a separate finding.

### Gate 5 items (restated for the developer)

- Task 1: "State persistence and recovery work reliably across interrupted sessions" — persistence itself is fine; not implicated by the findings above.
- Task 2: "Process termination leaves zero orphan processes upon timeout" — dispatch/termination logic looks correct from static review; not implicated.
- Task 3: "Human confirmation prompt and circuit breaker halts function deterministically" — the halt/prompt wiring is correct, but the "aligned fixes" it applies after confirmation are no-ops per the finding above.
- Task 4: "Assistant evaluation cleanly prevents unauthorized design reversions" — contradicted by the fail-open verdict parsing finding; an Assistant dispatch failure does not prevent anything, it defaults to proceed.
- Task 5: "Document checks pass across all modified skills and bilingual markdown files" — docs look consistent; not implicated, but the docs (`autonomous-mode.md` §4) describe behavior ("applies fixes, commits code and decisions") that the implementation does not actually perform.

Verdict: CHANGES REQUIRED
[Critical] skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:127 — ModelDispatcher.probe_model sends agy an undefined --probe flag; live agy --help/invocation confirms "flags provided but not defined: -probe" (exit 2), so every real (non-mocked) run aborts at INITIALIZED before reaching Principal Review.
[Critical] skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:819-868,507-545 — _draft_fix_plan/_apply_code_fixes/_apply_aligned_fixes/_apply_minor_fixes/_record_review_decisions never dispatch the Programmer or Assistant and never write decision cells into principal_review.md/review_results.md; they only commit whatever is already dirty, so review findings are never actually fixed despite Tasks 3 and 4's frozen contracts requiring it.
[Critical] skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:769-817 — run_gate4() omits audit_epic.py, the unit test suite, check_bdd_traceability.py, and the headless quality_check workflow mandated by Task 5's Decisions Already Made and the HLD's Method Execution Contract, and unconditionally returns PASS once the smoke checklist (exit code ignored) and review-decision check run.
[Important] skills/dev-lifecycle/resources/scripts/lifecycle_runner.py:870-895 — evaluate_programmer_fix_plan discards the dispatch exit code and defaults to FixPlanVerdict.APPROVED whenever the Assistant call fails or returns unparseable output, violating Task 4's "Stop and Report If: Fix plan verdict cannot be parsed" and creating a fail-open path around the CRITICAL_CONFLICT safety check.
````
