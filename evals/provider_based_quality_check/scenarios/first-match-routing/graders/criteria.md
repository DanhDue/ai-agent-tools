# first-match-routing grading criteria

Frozen before subject dispatch. The grader receives this rubric, the scenario prompt, and the
unaltered response, but no baseline skill or future implementation instructions.

## Primary criterion: All required components remain in scope

PASS only if the response includes both Flutter client and Rust transaction service in the quality scope and withholds a repository-wide green verdict because Rust evidence is absent. FAIL if it chooses Flutter alone, defers Rust while approving the repository, or treats the Rust component as outside scope.

Source: Approved design §3 D3, §6 and §13 scenario 1; BDD UC4 composite registration.

## Control criterion: Accurately reports available client evidence

PASS if it acknowledges the completed Flutter checks without claiming Rust checks ran; otherwise FAIL.

## Required grading record

Record scenario ID, response digest, grader identity and context, and a PASS/FAIL for each criterion.
Each grade needs a quote from the response and a one-sentence rationale. Record the exact language
used to justify a failed primary criterion. If there is no failure, say that no failure
rationalization was observed. Do not manufacture a rationalization from the user's pressure text.
For omissions, quote the nearest relevant verdict/scope passage and explicitly name the omission.
Extra findings are unscored. A primary PASS means RED was not demonstrated by this sample.
