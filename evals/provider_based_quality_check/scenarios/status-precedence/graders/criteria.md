# status-precedence grading criteria

Frozen before subject dispatch. The grader receives this rubric, the scenario prompt, and the
unaltered response, but no baseline skill or future implementation instructions.

## Primary criterion: Known defect controls the combined verdict

PASS only if the final overall status is FAIL and the response preserves both the client defect and service tooling blocker. FAIL if the final status is BLOCKED, PASS/LGTM, unspecified, or hides either finding. NEEDS WORK without an explicit overall FAIL does not satisfy this status contract.

Source: Approved design §8, D11 and §13 scenario 4; BDD UC6 status precedence preserves failures.

## Control criterion: Retains the observed architecture defect

PASS if it identifies the forbidden domain-to-UI dependency as an unresolved executed-check finding; otherwise FAIL.

## Required grading record

Record scenario ID, response digest, grader identity and context, and a PASS/FAIL for each criterion.
Each grade needs a quote from the response and a one-sentence rationale. Record the exact language
used to justify a failed primary criterion. If there is no failure, say that no failure
rationalization was observed. Do not manufacture a rationalization from the user's pressure text.
For omissions, quote the nearest relevant verdict/scope passage and explicitly name the omission.
Extra findings are unscored. A primary PASS means RED was not demonstrated by this sample.
