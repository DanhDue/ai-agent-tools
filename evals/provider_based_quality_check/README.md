# Provider quality behavioral baseline

Review correction: the original first-match prompt exposed the future registry contract. Its
frozen prompt, rubric, response, capture, and grade are retained unchanged as contaminated
historical evidence and excluded from primary behavioral claims. `primary-manifest.json`
selects the independent `2026-10-11-composite-v2` replacement. Its response and independent blind
grade are now captured. Missing replacement evidence reduces primary completeness to 4/5 and
cannot be filled by the historical sample.

These fixtures measure the unchanged quality and lifecycle instructions at source revision
`afbf69aa8e7389bf238e5a314a7ae0add78198f6` before provider implementation. Task 1 is a
baseline-only adaptation of [the evaluation protocol](../protocol.md): the old instructions are
the subject, and there is no new-skill arm yet. A future paired comparison must reuse these
prompts and rubrics. One sample per scenario is exploratory evidence, not a reliability estimate.

## Running subjects

The controller dispatches one fresh-context subject per scenario. Give it only the shared
`context.md`, the baseline skill files listed there, and that scenario's `prompt.md` verbatim.
Do not give subjects this README, scenario labels, manifests, rubrics, design documents, other
responses, task briefs, or grading instructions. Read-only fixture facts stand in for a consumer
repository; subjects produce their actual report without executing simulated commands.

Save the full, unedited reply in `runs/2026-10-11-baseline/<scenario-id>/response.md` and record
agent ID, model (or explicitly unknown), context mode, timestamps, source revision, and prompt /
context / baseline-skill digests in `capture.json`. Independent subjects have separate paths and
no shared conversation. Never overwrite a run; retries need a new run ID and retain earlier data.

## Grading

Criteria in each `graders/criteria.md` are frozen before dispatch. A grader who did not dispatch
the subjects receives only each prompt, rubric, and raw response. Record PASS or FAIL per
criterion with a verbatim quote and rationale. The primary criterion tests the named invariant;
the second is a grounded reporting control the baseline can plausibly pass. Record extra findings
as unscored. A primary PASS means that failure was not demonstrated; never relabel it RED.

The implementer may grade controller-dispatched subjects, satisfying the protocol's prohibition
on grading one's own dispatch. If the implementer dispatches a subject, use an independent grader.
No arm randomization is needed for this one-arm baseline; later paired arms require blind labels.

The initial run's implementer grading was an explicit exception to the stronger no-skill-context
rule: the grader had already read the old skills and design. This disclosure does not make those
grades independently blind. The replacement case and all future paired comparisons require a
fresh independent grader with only the prompt, rubric, and anonymized reply or replies.

## Completion

All five scenarios require a raw response, capture metadata, grade, and quoted rationalization
(or an explicit statement that no failure rationalization was observed). Completeness and RED
demonstration are separate claims. Task 1 requires 5/5 complete frozen evidence and at least one
honestly demonstrated primary failure. Primary passes remain regression controls. This acceptance
ruling does not change the frozen prompts, rubrics, responses, or grades.
Evaluation checks belong in this directory; runtime skills and `scripts/verify.sh` stay unchanged.

Current primary findings and limitations are in
[the corrected primary report](runs/2026-10-11-composite-v2/report.md).
The [original report](runs/2026-10-11-baseline/report.md) remains historical.
Run `python3 -B evals/provider_based_quality_check/check_baseline.py` for evidence completeness;
add `--require-failure status-precedence` for task acceptance. The optional `--require-red` flag
retains the stricter all-five diagnostic, which this run does not satisfy. Baseline snapshot digests are
verified against the frozen source-file digests, independent of future changes to active skills.
