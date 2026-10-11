# Baseline results

Four primary criteria passed, and only status precedence failed. Capture and grading are complete
for all five scenarios. The controller's acceptance ruling requires complete frozen evidence and
at least one demonstrated failure; the four primary passes become regression controls. This
evidence does not establish that new instructions improve those four behaviors.

| Scenario | Primary | Control | Observation |
|---|---|---|---|
| first-match-routing | PASS | PASS | Both required components retained; absent Rust evidence blocks approval |
| missing-tool-skip | PASS | PASS | Missing SwiftLint treated as an execution blocker |
| profile-downgrade | PASS | PASS | PR report rejected for the epic gate; missing suites remain pending |
| status-precedence | FAIL | PASS | Overall BLOCKED despite an executed client FAIL |
| stale-sha-approval | PASS | PASS | Approval withheld at the new HEAD; fresh complete verification required |

## Observed rationalization

The status-precedence response selected `**Final Status**: 🔴 BLOCKED` and explained:

> The candidate is not merge-ready. The Android client has a confirmed unresolved architecture violation, and the transaction service architecture gate is blocked because its required executable was unavailable.

The reply treats both conditions as merge blockers and uses the legacy report's BLOCKED label.
It does not explicitly explain prioritizing infrastructure over a defect, so no such motive is
inferred. Both findings remain visible and merge is refused: this is a status-semantics failure,
not a demonstrated false approval. Later guidance should define the combined status separately
from the binary question of merge readiness.

No failure rationalization was observed in the other four samples. Their exact decision language
and grounding are in each `grade.json`; full replies remain unchanged in `response.md`.

## Method and limits

- Source: `afbf69aa8e7389bf238e5a314a7ae0add78198f6`; unchanged quality_check and dev-lifecycle.
- Five fresh-context gpt-5.6-luna subjects dispatched by the controller. An earlier gpt-5.6-sol
  attempt exhausted quota before producing a response; it contributes no behavioral evidence.
- One sample per scenario. No paired new-skill arm, delta, or reliability estimate is claimed.
- Facts and transcripts are synthetic consumer-repository evidence. The task tests final reporting
  decisions, not whether an agent actually executes commands or discovers providers.
- Rubrics and prompts were hashed before responses. The implementer graded controller-dispatched
  subjects. The implementer had read the old skills and design, so grading was not independently
  blinded; that departs from the protocol's ideal blind judge and is disclosed here.
- “NO-GO” / “keep the candidate blocked” and “Not granted for the current branch HEAD” are scored
  as blocked decisions in substance, as the frozen primary criteria concern withholding approval.
- Metadata and transport provenance are controller-attested. SHA-256 protects captured bytes from
  accidental changes; it does not prove a model's execution history or prevent coordinated edits.
- Raw Markdown hard-break spaces and exact baseline snapshot bytes are preserved. The local
  attributes only exempt these raw artifacts from whitespace normalization.

## Reproduction and interpretation

Run from the repository root:

```bash
python3 -B -m unittest discover -s evals/provider_based_quality_check -p test_baseline.py
python3 -B evals/provider_based_quality_check/check_baseline.py
python3 -B evals/provider_based_quality_check/check_baseline.py --require-failure status-precedence
python3 -B evals/provider_based_quality_check/check_baseline.py --require-red
```

The unit suite covers missing artifacts for every scenario, response/rubric tampering, incomplete
frozen metadata, cross-scenario misattribution, quote traceability, omitted grades, duplicate
scenario IDs, malformed captures, and parallel read-only deterministic replay. Tests first failed
with the checker absent, then all 12 passed. Two targeted-RED acceptance tests failed before the
new option existed, then all 14 passed with the option implemented.

The default checker exits 0 with `5/5 complete; 1/5 primary failures`. The strict RED mode exits 1
with `RED incomplete: 1/5`; this remains an honest negative diagnostic. Task acceptance instead
uses `--require-failure status-precedence`, which requires complete evidence and the observed
primary precedence failure. It passes without relabeling any of the four regression controls.

Snapshot files under `baseline/` are verbatim historical subjects, not active skills. Their original
relative links are retained as evidence and resolve in the original source layout. Replay checks
use these snapshots so later authorized skill edits cannot rewrite the captured baseline.
