# Autonomous Lifecycle Runner BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions](#state-transitions)
- [Async and Race Conditions](#async-and-race-conditions)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `autonomous_lifecycle_runner`
- **Canonical language**: English
- **Scenario prefix**: `ALR`
- **Automation roots**: `tests/`, `skills/dev-lifecycle/resources/scripts/`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.
- **Mocking**: `agy` subprocess invocations and external review CLI calls are mocked via executable stubs or test fixtures in unit/integration tests.

## Happy Paths

```gherkin
Scenario: [ALR-HP-01] [Tier C - Integration] Complete autonomous pipeline executes from handoff to final executive report

Given an epic with approved Gate 1 spec and Gate 2 task breakdown in a git worktree
And configured runner models in .devtool/review_config.json
When lifecycle_runner.py runs with --epic autonomous_lifecycle_runner
Then the runner executes Principal Review, advances through Stage 3 implementation, and completes Cross-Model Review without intermediate menu pauses
And only at the final round after convergence and Gate 4 PASS, the runner renders the executive summary report synthesizing the Top 3 Highest-Risk Findings across all review rounds
And the runner halts cleanly, presenting the prompt for /finishing-a-development-branch (merge to base branch or other actions) to the Human Architect

Scenario: [ALR-HP-02] [Tier C - Integration] Headless dispatch of AI Programmer with Gemini 3.8 Flash High

Given a pending implementation task file in .devtool/features/task_1_pipeline_state_machine_and_probing.md
When lifecycle_runner.py dispatches the AI Programmer for task execution
Then the dispatched command executes "agy" with "--model gemini-3.8-flash"
And the command specifies "--effort high" and "--mode auto"
And the execution runs inside the isolated git worktree with dedicated process group supervision

Scenario: [ALR-HP-03] [Tier C - Integration] AI Assistant proposes fixes and prompts Human confirmation in Principal Review

Given Principal Review returns two Important findings on candidate HLD specifications
When the AI Assistant triages the findings in step_principal_review
Then the Assistant verifies findings against HLD source documents and drafts a structured fix table
And lifecycle_runner.py halts execution to prompt Human confirmation
And upon Human confirmation, the Assistant applies the revisions, runs package_epic.py --revise, and proceeds to the next round

Scenario: [ALR-HP-04] [Tier C - Integration] AI Assistant approves AI Programmer fix plan in Cross-Model Review without Human stop

Given Cross-Model Review returns review findings requiring code adjustments in Round 1
When the AI Programmer drafts a proposed fix plan in fix_plan_round1.md
Then the AI Assistant evaluates the fix plan against the approved HLD and emits verdict "APPROVED"
And the AI Programmer applies the approved code changes and re-runs Phase 4 Gate 4
And the cycle proceeds to Round 2 without prompting the Human Architect for intermediate confirmation
```

## Edge Cases and Boundaries

```gherkin
Scenario: [ALR-EC-01] [Tier C - Integration] Zero findings in Principal Review bypasses Human confirmation

Given Principal Review completes Round 1 with verdict PASS and 0 findings
When step_principal_review processes the review results
Then the runner logs "AUTO_PASS_CLEAN: 0 findings"
And the runner bypasses the Human confirmation prompt completely
And the pipeline state advances directly to Stage 3 Implementation

Scenario: [ALR-EC-02] [Tier C - Integration] Minor-only findings in Principal Review batched into single confirmation

Given Principal Review Round 1 returns 0 Critical, 0 Important, and 2 Minor formatting findings
When step_principal_review evaluates the triage report
Then the 2 Minor findings are batched into a single unified fix confirmation prompt for the Human Architect
And once confirmed, the fixes are applied in one pass and package_epic.py --revise executes cleanly

Scenario: [ALR-EC-03] [Tier C - Integration] AI Assistant adjusts AI Programmer fix plan without rejecting

Given the AI Programmer proposes a fix plan that omits a required edge-case assertion
When the AI Assistant reviews the fix plan in Cross-Model Review
Then the Assistant returns verdict "ADJUSTED" along with the amended fix plan text
And the AI Programmer receives the adjusted plan, applies the combined patch, and triggers Gate 4 re-verification

Scenario: [ALR-EC-04] [Tier C - Integration] Gate 3 execution order auto-confirmed via compute_execution_order

Given multiple task files with explicit dependency links in .devtool/features/
When the runner enters Stage 3 Implementation
Then compute_execution_order.py is executed to resolve the topological execution sequence
And the resulting task sequence is auto-confirmed and recorded in .devtool/GATE_LEDGER.md under Gate 3
And task execution begins immediately without presenting an interactive prompt
```

## State Transitions

```gherkin
Scenario: [ALR-ST-01] [Tier C - Integration] State persistence and resumption from crash in intermediate stage

Given the runner is interrupted by SIGINT during Stage 3 task execution
When lifecycle_runner.py is invoked again with --resume
Then the runner reads .devtool/state/<epic>.pipeline.json
And the runner recovers the active stage "implementation", completed task list, and current round
And execution resumes from the exact interrupted task without re-running completed tasks

Scenario: [ALR-ST-02] [Tier C - Integration] Gate Ledger synchronization on autonomous state transitions

Given the pipeline progresses autonomously through Stage 2 and Stage 3
When each gate milestone (Gate 3, Gate 4, Gate 5 candidate) is achieved
Then .devtool/GATE_LEDGER.md is updated with the timestamp, candidate SHA, and auto-approval metadata
And the ledger status remains strictly in sync with .devtool/state/<epic>.pipeline.json

Scenario: [ALR-ST-03] [Tier C - Integration] Probing verifies model capabilities before state initialization

Given an invalid or deprecated model string specified in configuration
When lifecycle_runner.py initiates the startup capability probe
Then ModelDispatcher.probe_model executes a minimal headless agy call
And upon non-zero exit or error, the runner aborts before writing pipeline state or modifying files
And a descriptive error message indicating the rejected model is printed to stderr
```

## Async and Race Conditions

```gherkin
Scenario: [ALR-AR-01] [Tier C - Integration] Subprocess group process isolation and clean SIGTERM termination on timeout

Given a headless agy programmer process exceeds the configured timeout limit
When the supervisor timer expires in ModelDispatcher
Then SIGTERM is broadcast to the entire subprocess group via os.killpg
And after a 1.0s grace period, SIGKILL is escalated if the child processes remain alive
And the runner records a timeout failure in the pipeline state without leaving orphaned processes

Scenario: [ALR-AR-02] [Tier C - Integration] File locking during state updates prevents concurrency corruption

Given concurrent processes or rapid consecutive state transitions
When LifecycleRunner writes updates to .devtool/state/<epic>.pipeline.json
Then state updates are serialized using file locking and atomic temporary file replacement (.tmp rename)
And the pipeline state file remains valid and uncorrupted JSON at all times
```

## Failure and Resilience

```gherkin
Scenario: [ALR-FR-01] [Tier C - Integration] Circuit Breaker halts immediately on Shared Contract conflict

Given an external review round reports a finding conflicting with shared-contracts/
When evaluate_circuit_breakers inspects the triage report
Then the runner triggers CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)
And the pipeline halts immediately, preserving all logs and state
And the console displays the executive warning banner instructing the developer to consult the Human Architect

Scenario: [ALR-FR-02] [Tier C - Integration] Circuit Breaker halts immediately on repeated fix loop

Given a finding in Round N touches the identical file path previously marked as fixed in Round N-1
When evaluate_circuit_breakers evaluates the round comparison
Then the runner triggers CIRCUIT_BREAKER_HALT (FIX_LOOP)
And the pipeline stops calling tools and presents the recurrent finding to the Human Architect

Scenario: [ALR-FR-03] [Tier C - Integration] Circuit Breaker halts on max rounds exhaustion with Critical remaining

Given Cross-Model Review reaches Round 3 with at least 1 unresolved Critical finding
When evaluate_circuit_breakers checks the round counter and severity counts
Then the runner triggers CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)
And the runner halts without launching a 4th round, outputting the Top 3 Highest-Risk Findings

Scenario: [ALR-FR-04] [Tier C - Integration] AI Assistant rejects fix plan with CRITICAL_CONFLICT and halts pipeline

Given the AI Programmer drafts a fix plan that attempts to unilaterally revert an approved architectural decision
When the AI Assistant evaluates the fix plan
Then the Assistant returns verdict "CRITICAL_CONFLICT" with detailed rationale
And lifecycle_runner.py halts immediately, preventing the Programmer from modifying source code
And an alert is displayed to the Human Architect highlighting the architectural conflict
```

