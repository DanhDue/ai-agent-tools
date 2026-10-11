# Corrected primary baseline

The primary baseline has five complete cases, one primary failure (status precedence), and four
primary passes retained as regression controls. The first-match case now comes from
`2026-10-11-composite-v2`; the other four cases retain their original evidence and grading.

The original first-match prompt exposed the future provider registry contract. Its entire frozen
scenario and captured run remain byte-for-byte historical evidence, excluded from primary claims.
The old run report is historical; this report and `primary-manifest.json` define the current scope.

## Replacement method and result

The replacement prompt contains repository/platform facts, modified paths, and command records.
It contains no registry, provider IDs, required flags, future interface, desired verdict, or rubric.
The prompt, rubric, exact subject request, and instruction digests were frozen before dispatch.

A fresh subject returned a blocked Gate 4 decision identifying both modified components and the
absence of Rust evidence. A separate fresh judge scored primary PASS and control PASS. The judge
saw only the prompt, rubric, raw response, and its own initial grading output during correction.
It did not receive quality skills, the design, prior results, or the controller conversation.

The initial judge quote incorrectly added “The” to a source list item. The same judge corrected
that quote and the criterion IDs; verdicts and rationales remained unchanged. Both raw judge
outputs are preserved. The checker confirms the corrected quote is verbatim and that captured
grade fields match the corrected raw judge response. No grading conclusion was rewritten by the
implementer.

## Current primary cases

| Case | Run | Primary | Control | Grading context |
|---|---|---|---|---|
| first-match-routing | 2026-10-11-composite-v2 | PASS | PASS | Independent blind judge |
| missing-tool-skip | 2026-10-11-baseline | PASS | PASS | Original implementer exception |
| profile-downgrade | 2026-10-11-baseline | PASS | PASS | Original implementer exception |
| status-precedence | 2026-10-11-baseline | FAIL | PASS | Original implementer exception |
| stale-sha-approval | 2026-10-11-baseline | PASS | PASS | Original implementer exception |

The reproduced failure remains `**Final Status**: 🔴 BLOCKED` despite an executed client FAIL.
Both findings were retained and approval refused; it is a status-precedence defect, not false-green
approval. No failed behavior is claimed for the primary-passing cases.

## Reproduction and limits

```bash
python3 -B -m unittest discover -s evals/provider_based_quality_check -p test_baseline.py
python3 -B evals/provider_based_quality_check/check_baseline.py
python3 -B evals/provider_based_quality_check/check_baseline.py --require-failure status-precedence
python3 -B evals/provider_based_quality_check/check_baseline.py --require-red
```

Primary completeness and targeted RED acceptance pass. The all-five-RED diagnostic intentionally
fails. Historical first-match evidence cannot replace a missing primary response or blind grade;
its integrity is still checked so preservation failures remain visible.

These remain single-sample report-decision exercises over synthetic evidence. They do not measure
actual command execution or broad model reliability. The original four retained grades were not
independently blinded; future paired comparisons require independent blind grading. Requested
model identity was gpt-5.6-luna, while both replacement agents reported GPT-5; capture metadata
retains both values without claiming a resolved identity. All transport metadata is controller-attested.
