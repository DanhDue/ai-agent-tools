# Behavior-Driven Development Scenarios: Split Review Skills

## Table of Contents

- [Use Case 1: In-Lifecycle and Ad-Hoc Principal Review](#use-case-1-in-lifecycle-and-ad-hoc-principal-review)
- [Use Case 2: In-Lifecycle and Ad-Hoc Cross-Model Review](#use-case-2-in-lifecycle-and-ad-hoc-cross-model-review)
- [Use Case 3: State Transitions and Gate Invariants](#use-case-3-state-transitions-and-gate-invariants)
- [Use Case 4: Asynchronous Resilience and Tool Fallbacks](#use-case-4-asynchronous-resilience-and-tool-fallbacks)
- [Use Case 5: Failure Handling and Precondition Gates](#use-case-5-failure-handling-and-precondition-gates)
- [Use Case 6: Lifecycle Documentation and Contract Assurance](#use-case-6-lifecycle-documentation-and-contract-assurance)

## Use Case 1: In-Lifecycle and Ad-Hoc Principal Review

### Happy Paths

```gherkin
Scenario: [SRS-HP-01] [Tier C - Integration] In-lifecycle Principal Review invocation from dev-lifecycle
  Given an epic "sample_epic" has passed Gate 2 and packaging preflight passes
  When the developer selects option 2 "Principal Review" with "codex" CLI
  Then the "d3nexus:principal-review" skill is invoked
  And "run_external_review.py run --kind principal" executes against the epic artifacts
  And round 1 is recorded into ".devtool/epic/sample_epic/principal_review.md"

Scenario: [SRS-HP-02] [Tier C - Integration] Ad-hoc Principal Review invocation on standalone design document
  Given a standalone design document "docs/rfc/feature-architecture.md" exists
  When the developer invokes "/principal-review docs/rfc/feature-architecture.md" with base "main" and CLI "claude"
  Then the "principal-review" skill validates the document structure
  And invokes the external reviewer with document text and source context
  And outputs an actionable review triage table without requiring an epic directory
```

### Edge Cases and Boundaries

```gherkin
Scenario: [SRS-EC-01] [Tier A - Unit] Ad-hoc review invocation with non-existent document
  Given a requested target path "docs/rfc/missing-doc.md" does not exist on disk
  When the user runs "/principal-review docs/rfc/missing-doc.md"
  Then the skill immediately refuses with an error naming the missing path
  And no external CLI process is spawned

Scenario: [SRS-EC-04] [Tier A - Unit] Standalone document without required structure
  Given a standalone document "docs/rfc/broken.md" contains syntax errors or missing headings
  When ad-hoc principal review executes pre-validation
  Then the check reports the formatting error
  And prompts the author to fix structure before running external model review
```

## Use Case 2: In-Lifecycle and Ad-Hoc Cross-Model Review

### Happy Paths

```gherkin
Scenario: [SRS-HP-03] [Tier C - Integration] In-lifecycle Cross-Model Review invocation from dev-implementation
  Given all tasks in epic "sample_epic" are marked done and Gate 4 returns PASS
  When the developer selects option 2 "Cross-model review" with "claude" CLI
  Then the "d3nexus:cross-model-review" skill is invoked
  And "run_external_review.py run --kind epic" evaluates task commits and diffs against base
  And round 1 is recorded into ".devtool/epic/sample_epic/review_results.md"

Scenario: [SRS-HP-04] [Tier C - Integration] Ad-hoc Cross-Model Review invocation on git branch
  Given a feature branch "feature/payment-flow" has commits diverging from "main"
  When the developer invokes "/cross-model-review --base main"
  Then the "cross-model-review" skill computes the commit range and diff against "main"
  And executes external model review across the diff
  And emits a formatted triage report with proposed fixes

Scenario: [SRS-HP-05] [Tier C - Integration] Local model review invocation through cross-model-review skill
  Given local Ollama server is running and exposes model "qwen2.5-coder:32b"
  When the developer selects option 3 "Local model review" specifying model "qwen2.5-coder:32b"
  Then the "cross-model-review" skill invokes the runner with "--cli ollama --model qwen2.5-coder:32b"
  And records the evaluation round into "review_results.md"
```

### Edge Cases and Boundaries

```gherkin
Scenario: [SRS-EC-02] [Tier A - Unit] Cross-model review refuses execution on dirty working tree
  Given the repository working tree has unstaged or untracked changes
  When "cross-model-review" initiates runner execution
  Then the runner refuses execution with a clean tree precondition error
  And reminds the user to commit or stash modifications before review

Scenario: [SRS-EC-03] [Tier A - Unit] Missing external CLI tool triggers actionable guidance
  Given neither "claude" nor "codex" binary is installed on the user PATH
  When an external review round is requested
  Then the skill detects missing CLI binaries
  And prints installation instructions for Claude Code CLI and OpenAI Codex CLI without crashing
```

## Use Case 3: State Transitions and Gate Invariants

### State Transitions

```gherkin
Scenario: [SRS-ST-01] [Tier C - Integration] Principal Review revision loop enforces commit ordering
  Given round 1 of principal review reported Important findings
  When the developer approves document edits
  Then the revised documents are committed first as "[EPIC] Revise epic after Principal Review round 1"
  And decisions referencing the revision commit SHA are committed into "principal_review.md"
  And the epic packaging procedure re-runs to refresh handoff metadata

Scenario: [SRS-ST-02] [Tier C - Integration] Cross-Model Review fix loop enforces Gate 4 re-verification
  Given round 1 of cross-model review reported Important findings
  When code fixes are committed and decisions are recorded in "review_results.md"
  Then Gate 4 machine acceptance must be re-run in full on the new candidate SHA
  And Review Choice is presented again only after Gate 4 returns PASS

Scenario: [SRS-ST-03] [Tier A - Unit] Gate 3 execution order enforces zero undecided principal findings
  Given ".devtool/epic/sample_epic/principal_review.md" contains undecided blocking findings
  When "dev-implementation" initiates Gate 3 execution order verification
  Then Gate 3 check exits with code 1 and refuses to proceed to worktree dispatch

Scenario: [SRS-ST-04] [Tier A - Unit] Gate 5 Kanban sign-off enforces zero undecided code findings
  Given ".devtool/epic/sample_epic/review_results.md" contains undecided blocking findings
  When developer chooses "Finish" at Review Choice
  Then the finish preflight check exits with code 1
  And prompts the developer to decide all findings before proceeding to Gate 5
```

## Use Case 4: Asynchronous Resilience and Tool Fallbacks

### Async and Resilience

```gherkin
Scenario: [SRS-AR-01] [Tier A - Unit] Streaming timeout handling during model execution
  Given an external CLI invocation exceeds the configured process timeout
  When the timeout trigger fires
  Then the runner terminates the child process cleanly
  And reports a descriptive timeout finding without leaving orphaned background processes

Scenario: [SRS-AR-02] [Tier A - Unit] Sequential round numbering prevents collision
  Given an epic already has round 1 recorded in its review log
  When a subsequent review round completes
  Then the new round is strictly assigned round number 2
  And previous round history and decisions are immutably preserved
```

## Use Case 5: Failure Handling and Precondition Gates

### Failures and Resilience

```gherkin
Scenario: [SRS-FR-01] [Tier C - Integration] Principal review runner halts on failed readiness preflight
  Given an epic directory has broken document links or missing bilingual pairs
  When "principal-review" executes "check_epic_readiness.py"
  Then the readiness preflight fails with non-zero exit code
  And prints the precondition banner without calling the external CLI model

Scenario: [SRS-FR-02] [Tier A - Unit] Triage parser isolates malformed model responses
  Given an external reviewer outputs text that omits valid verdict or severity anchors
  When "run_external_review.py triage" processes the round output
  Then the parser isolates the parse failure into a visible warning
  And prompts the developer to inspect raw log without crashing the lifecycle
```

## Use Case 6: Lifecycle Documentation and Contract Assurance

### Happy Paths

```gherkin
Scenario: [SRS-HP-06] [Tier C - Integration] Document contracts enforce new review skills exposure
  Given the repository skill directory contains "principal-review" and "cross-model-review"
  When "test_lifecycle_document_contract.py" evaluates all lifecycle producers
  Then both skills expose expected contract keywords and YAML frontmatter
  And "scripts/verify.sh" completes with zero contract regressions

Scenario: [SRS-HP-07] [Tier C - Integration] Lifecycle diagrams reflect two standalone review stages
  Given human-facing lifecycle documentation "docs/lifecycles.en.md" and "docs/lifecycles.vi.md"
  When modern flowchart diagrams are inspected
  Then Stage 2 displays explicit delegation to "principal-review"
  And Stage 3 displays explicit delegation to "cross-model-review"
```
