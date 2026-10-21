# Local Model Review BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions](#state-transitions)
- [Async and Race Conditions](#async-and-race-conditions)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `local_model_review`
- **Canonical language**: English
- **Scenario prefix**: `LMR`
- **Automation roots**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.
- **Fake server**: every Ollama call goes to an `http.server` on `127.0.0.1` inside the test.

## Happy Paths

```gherkin
Scenario: [LMR-HP-01] [Tier C - Integration] Review Choice presents three options

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, rules/CRITICAL_RULES.md, docs/lifecycles.en.md and docs/lifecycles.vi.md
When the lifecycle contract tests read them
Then each names "Local model review" beside "Finish" and "Cross-model review"
And dev-implementation shows "--cli ollama --model <model>" and tells the agent to run "ollama list" and ask
And dev-lifecycle's Red Flags forbid picking the Ollama model for the developer

Scenario: [LMR-HP-02] [Tier C - Integration] Shared rules reach the Claude and Codex prompt

Given a throwaway epic repository and a fake claude on PATH that saves its stdin
When run_external_review.py run --cli claude records a round
Then the saved prompt contains "Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic" and "Immutable Real Artifacts"
And the saved prompt contains no literal "$rules"

Scenario: [LMR-HP-03] [Tier C - Integration] A local review of a two-task epic records one round

Given a throwaway epic with two task commits and a fake Ollama server that answers every chat with "Verdict: PASS"
When run --cli ollama --model qwen38-reviewer --host <fake server> runs
Then the server receives exactly 3 chat requests
And review_results.md gains "## Round 1" with "- **CLI**: ollama", "- **Model**: qwen38-reviewer", "- **Passes**: 3", "- **Status**: completed" and "- **Verdict**: PASS"
And the run exits 0

Scenario: [LMR-HP-04] [Tier C - Integration] A task slice carries everything the reviewer may judge

Given a task commit whose task file says "Covers: DEMO-HP-01" and whose evidence verify row has 40 output_tail lines
When build_slices and render_user run
Then the user message has "## Task file", "## Scenarios covered", "## Evidence" and "## Diff of <short sha>" in that order
And "## Scenarios covered" holds the Gherkin block of DEMO-HP-01 and no other scenario
And the evidence row shows exactly the last 15 of the 40 output lines
And the diff holds no path under ".devtool/"

Scenario: [LMR-HP-05] [Tier C - Integration] The system message fits its pass type

Given a task slice whose diff touches "lib/a.dart"
When render_system runs
Then the message contains "Decisions Already Made", "No Reconstructed Logic", the "## Flutter" section text, the "## Task pass" checklist and "Verdict: PASS"
And it contains none of "$rules", "$platform_rules" and "$checklist"
And an epic slice receives the "## Epic pass" checklist instead of the task one

Scenario: [LMR-HP-06] [Tier C - Integration] The Modelfile governs the context

Given /api/show reports "num_ctx 65536" in its parameters
When probe runs and chat_options(65536, None, 30000) runs
Then probe returns 65536
And chat_options returns {"num_predict": 35536} with no "num_ctx" key

Scenario: [LMR-HP-07] [Tier C - Integration] Every quoted platform rule exists in the kit

Given references/local-review-platforms.md
When the test collects the rule IDs of the Flutter, Android and iOS sections and the bold rule names of the Rust and Python sections
Then each ID occurs in a row marked "Blocker" of architecture-audit, code-health-audit or security-audit SKILL.md
And each Rust name occurs in rust-architecture-governance.md and each Python name in python-architecture-governance.md

Scenario: [LMR-HP-08] [Tier C - Integration] Triage lists every finding of the latest round

Given a recorded round with "[Important] a.py:3 — missing guard" and "[Minor] b.py:5 — wording"
When run_external_review.py triage --epic-dir demo runs
Then it exits 0 and prints "# Review Triage: demo, Round 1"
And its "## Findings" table has rows 1 and 2 with the round's severity, location and problem, and "?" in Assessment, Evidence and Proposed action
And it ends with a "## Next Steps" section

Scenario: [LMR-HP-09] [Tier C - Integration] The workflow requires triage before acting on findings

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md and rules/CRITICAL_RULES.md
When the lifecycle contract tests read them
Then each names "run_external_review.py triage"
And dev-implementation links references/review-triage.md and waits for the developer's decisions before any Fix commit
And dev-lifecycle's Red Flags forbid acting on review findings before presenting the triage

Scenario: [LMR-HP-10] [Tier C - Integration] Triage compares every round

Given a claude Round 1 whose Important finding is decided "fixed in abc1234" and an ollama Round 2 with one Minor finding
When triage runs
Then the "## Round Comparison" table has one row per round with CLI / Model, Status, Verdict, Critical, Important, Minor, Fixed, Dismissed and Undecided
And Round 1 shows Important 1 and Fixed 1, and Round 2 shows Minor 1
```

## Edge Cases and Boundaries

```gherkin
Scenario: [LMR-EC-01] [Tier C - Integration] Local review without a model stops first

Given a throwaway epic repository
When run --cli ollama runs without --model
Then it exits 2 with "--cli ollama needs --model" on stderr
And stderr never shows "[Pre-check] audit_epic.py"
And no review_results.md exists

Scenario: [LMR-EC-02] [Tier C - Integration] Context defaults and overrides

Given a model whose Modelfile sets no num_ctx
When chat_options(None, None, 1000) runs
Then it returns {"num_ctx": 32768, "num_predict": 31768}
And chat_options(65536, 16384, 1000) returns {"num_ctx": 16384, "num_predict": 15384}

Scenario: [LMR-EC-03] [Tier C - Integration] An oversized task diff drops its largest file first

Given a task commit that adds 9000 bytes to "big.py" and 300 bytes to "small.py"
When fit runs with a budget that fits everything except the big.py diff
Then the user message keeps the small.py diff and drops the big.py diff
And "## Not shown" lists "big.py"
And the fitted slice's omitted is ("big.py",)

Scenario: [LMR-EC-04] [Tier C - Integration] Never-cut content larger than the budget

Given a task slice whose task file alone estimates to more than 1000 tokens
When fit runs with a budget of 1000
Then it raises LocalReviewError naming the task id and "raise --num-ctx"

Scenario: [LMR-EC-05] [Tier C - Integration] Platform sections follow the touched extensions

Given the paths "app/lib/a.dart" and "native/src/b.rs"
When platform_sections runs
Then it returns exactly the Flutter section followed by the Rust section
And for the paths "README.md" and "web/x.ts" it returns an empty list
And render_system for that slice contains "No platform rules apply to this slice."

Scenario: [LMR-EC-06] [Tier C - Integration] A legacy task joins the epic slice

Given one task commit with evidence and one commit that changes "src/legacy.py" without touching any evidence file
When build_slices runs
Then it returns one task slice followed by the epic slice
And the epic slice's "## Commits outside tasks" holds the src/legacy.py diff

Scenario: [LMR-EC-07] [Tier C - Integration] Inline thinking is never parsed

Given the content "draft [Critical] a.py:1 — x\nVerdict: CHANGES REQUIRED\n</think>\n## Analysis\nfine\nVerdict: PASS"
When answer_text runs
Then it returns "## Analysis\nfine\nVerdict: PASS"

Scenario: [LMR-EC-08] [Tier C - Integration] A draft finding in Analysis is not a finding

Given an ollama pass whose out is "## Analysis\n- [Critical] a.py:1 — draft\nVerdict: PASS" with code 0 and done_reason "stop"
When record_round runs
Then the round has no findings row, "- **Status**: completed" and "- **Verdict**: PASS"
And record_round returns 0

Scenario: [LMR-EC-09] [Tier C - Integration] Dropped files reach the round metadata

Given an ollama pass "task_1" with omitted ("big.py",) and an epic pass with nothing omitted
When record_round runs
Then the round shows "- **Omitted**: task_1: big.py"

Scenario: [LMR-EC-10] [Tier C - Integration] Triage marks passes without a verdict

Given an ollama round whose pass 2 has no verdict line and whose pass 3 failed with "HTTP 500: boom"
When triage runs
Then the "## Passes" table shows pass 2 with verdict "none" and pass 3 with error "HTTP 500: boom"

Scenario: [LMR-EC-11] [Tier C - Integration] A fixed finding reported again at the same path is flagged

Given Round 1 with "[Important] src/a.py:3 — missing guard" and "[Important] src/b.py:9 — weak", both decided "fixed in abc1234"
And Round 2 reports "[Minor] src/a.py:40 — still unguarded"
When triage runs
Then "## Since Round 1" lists src/a.py:3 as re-reported at the same path with "check the fix"
And lists src/b.py:9 as not re-reported
```

## State Transitions

```gherkin
Scenario: [LMR-ST-01] [Tier C - Integration] A blocking local finding holds check until decided

Given a recorded ollama round with "[Important] lib/a.py:3 — missing guard" where lib/a.py was shown
When check runs
Then it exits 1 and prints "undecided: #1 Important lib/a.py:3"
And after the Decision cell becomes "dismissed: false positive" check exits 0

Scenario: [LMR-ST-02] [Tier C - Integration] Round numbering is shared across reviewers

Given review_results.md already holds a completed Claude "## Round 1" with an undecided Critical finding
When an ollama round with no finding is recorded
Then it is "## Round 2" with "- **CLI**: ollama"
And check exits 0 because only the latest completed round governs it

Scenario: [LMR-ST-03] [Tier C - Integration] Local model review returns to Gate 4 in full

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, docs/lifecycles.en.md and docs/lifecycles.vi.md
When the lifecycle contract tests read them
Then each routes Local model review through its round-recorded edge ("round recorded", or "đã ghi nhận round" in Vietnamese) back to Phase 4 or Gate 4 in full
And none routes it straight to Gate 5

Scenario: [LMR-ST-04] [Tier C - Integration] Triage reads the latest round, completed or not

Given a completed Round 1 and a "no verdict" Round 2
When triage runs
Then it prints "Round 2" and Round 2's findings only in its Findings table
```

## Async and Race Conditions

```gherkin
Scenario: [LMR-AR-01] [Tier C - Integration] Passes run one at a time in commit order

Given two task commits and a fake server that records when each chat request starts and ends
When run --cli ollama runs
Then no two requests overlap
And the requests carry task_1, then task_2, then the epic slice
And stderr shows "[Pass 1/3]", "[Pass 2/3]" and "[Pass 3/3]" in that order

Scenario: [LMR-AR-02] [Tier C - Integration] The timeout applies to each pass

Given a fake server that answers each chat after 2 seconds with "Verdict: PASS"
When run --cli ollama --timeout 3 runs over three passes
Then all three passes complete
And the round is "- **Status**: completed"
```

## Failure and Resilience

```gherkin
Scenario: [LMR-FR-01] [Tier C - Integration] Probe failures name their cause

Given no server listens on a closed local port
When probe runs against it
Then it raises LocalReviewError "Ollama server not reachable at http://127.0.0.1:<port>"
And against a fake server whose /api/show answers 404 it raises "model ghost is not installed (ollama list)"

Scenario: [LMR-FR-02] [Tier C - Integration] An unreachable server stops the run before facts

Given a throwaway epic repository and no server on the --host port
When run --cli ollama --model m runs
Then stderr shows "WAS NOT INVOKED" and "Ollama server not reachable"
And stderr never shows "[Pre-check] audit_epic.py"
And the run exits 2 and no review_results.md exists

Scenario: [LMR-FR-03] [Tier C - Integration] Transport failures become replies

Given a fake server whose /api/chat answers HTTP 500 with the body "boom"
When chat runs
Then it returns content "" and error "HTTP 500: boom"
And against a server that answers after 3 seconds, chat with timeout 1 returns error "timed out after 1 seconds"

Scenario: [LMR-FR-04] [Tier C - Integration] A failing pass stops the run and records what it has

Given a fake server that answers the first chat with "Verdict: PASS" and the second with HTTP 500
When run --cli ollama runs over three slices
Then the server receives exactly 2 chat requests
And the round has "- **Status**: no verdict", raw output with "### Pass 1" and the text "HTTP 500"
And the run exits 2

Scenario: [LMR-FR-05] [Tier C - Integration] Truncated output is no verdict

Given an ollama pass with code 0, done_reason "length" and out "Verdict: PASS"
When record_round runs
Then the round has "- **Status**: no verdict"
And record_round returns 2

Scenario: [LMR-FR-06] [Tier C - Integration] A blocking finding at an unseen path is annotated

Given an ollama pass whose shown text never contains "ghost.py" and whose out is "Verdict: CHANGES REQUIRED\n[Critical] ghost.py:9 — broken\n[Important] seen.py:2 — weak"
When record_round runs
Then the ghost.py row keeps Severity "Critical" and its Problem ends with "(location not shown to reviewer)"
And the seen.py row, whose path was shown, is not annotated

Scenario: [LMR-FR-07] [Tier C - Integration] A slice that cannot fit stops the run before any chat

Given --num-ctx 1000 and a task file larger than 1800 bytes
When run --cli ollama runs
Then it exits 2 with a message naming the task id and "raise --num-ctx"
And the fake server receives 0 chat requests
And no review_results.md exists

Scenario: [LMR-FR-08] [Tier C - Integration] Triage without a review round stops

Given an epic directory without review_results.md
When triage runs
Then it exits 2 and prints "no review round recorded for demo" on stderr
```
