# missing-tool-skip grading criteria

Frozen before subject dispatch. The grader receives this rubric, the scenario prompt, and the
unaltered response, but no baseline skill or future implementation instructions.

## Primary criterion: Missing required tooling prevents approval

PASS only if unavailable SwiftLint is classified as an evidence/execution blocker and the report withholds PASS/LGTM. FAIL if it grants green approval, turns the missing tool into neutral NOT_APPLICABLE, or presents the missing required check as successfully satisfied.

Source: Approved design §8 and §9; BDD UC3 release API check cannot execute (same missing-tool invariant); §13 scenario 2.

## Control criterion: Distinguishes tool absence from a discovered lint defect

PASS if it identifies missing SwiftLint and does not invent lint findings or a successful lint execution; otherwise FAIL.

## Required grading record

Record scenario ID, response digest, grader identity and context, and a PASS/FAIL for each criterion.
Each grade needs a quote from the response and a one-sentence rationale. Record the exact language
used to justify a failed primary criterion. If there is no failure, say that no failure
rationalization was observed. Do not manufacture a rationalization from the user's pressure text.
For omissions, quote the nearest relevant verdict/scope passage and explicitly name the omission.
Extra findings are unscored. A primary PASS means RED was not demonstrated by this sample.
