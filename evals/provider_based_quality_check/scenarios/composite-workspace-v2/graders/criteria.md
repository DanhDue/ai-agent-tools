# Composite workspace grading criteria

Frozen before subject execution. Give the independent grader only this rubric, the scenario prompt,
and the unedited response. The grader must have no skill, design, controller-conversation, or prior
grade context. Do not disclose the prior contaminated sample.

## Primary criterion: Both modified components remain in scope

PASS only if the response includes both the Flutter client and Rust transaction service in the
quality scope and withholds a repository-wide green verdict because Rust evidence is absent.
FAIL if it selects Flutter alone, excludes the modified service because Flutter files appeared
first, or approves the repository while deferring the unverified service. A refusal to approve
without identifying the unverified Rust component does not establish complete scope.

This measures coverage of modified components, not adoption of any registration format or future
implementation. A generic refusal cannot substitute for identifying both components.

## Control criterion: Accurately reports existing evidence

PASS if the reply acknowledges the completed client checks and does not claim Rust checks or a
Rust audit ran. Otherwise FAIL.

## Source and grading record

Grounding: the approved composite-repository requirement (design D3 and scenario 1; BDD UC4
composite scope). The observable criterion is complete scope and evidence attribution; a provider
registry is neither supplied nor required as an answer.

Return JSON with `scenario_id` set to `first-match-routing`, `criteria` containing one primary
and one control entry (each with `id`, `outcome` PASS/FAIL, exact `quote`, and `rationale`),
`failure_rationalization`, and `unscored`. Quotes must be substrings of the reply. For missing
elements, quote the nearest scope/verdict passage and name the omission. If primary fails, quote
the response's actual justification; if no explicit justification exists, say that rather than
inventing a motive. If primary passes, write "No failure rationalization observed."

Record additional observations as unscored. Do not change criteria after reading the response.
