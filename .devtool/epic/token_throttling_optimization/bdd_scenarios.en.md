# Token Throttling Optimization BDD Scenarios

## Table of Contents

- [Meta Data](#meta-data)
- [Happy Paths](#happy-paths)
- [Edge Cases and Boundaries](#edge-cases-and-boundaries)
- [State Transitions and Invariants](#state-transitions-and-invariants)
- [Async and Concurrency](#async-and-concurrency)
- [Failure and Resilience](#failure-and-resilience)

## Meta Data

- **Epic**: `token_throttling_optimization`
- **Canonical language**: English
- **Scenario prefix**: `TTO`
- **Automation roots**: `tests`
- **Rule**: Every scenario ID is assigned to exactly one task and appears in an automated test.
- **Mocking**: Subprocess CLIs (`claude`, `codex`, `kiro`, `agy`, `pytest`, `git`) and filesystem mutations are isolated inside temporary directories (`tmp_path` / `tempfile.TemporaryDirectory`) with fake binaries on `PATH`.

## Happy Paths

```gherkin
Scenario: [TTO-HP-01] [Tier C - Integration] Diff-only external review uses -U5 in Round 1 and omits full base diff in Round 2

Given an isolated git repository with an epic having multiple committed source changes and a .vi.md companion document
And an existing Round 1 entry already recorded in review_results.md for an earlier SHA
When run_external_review.py builds the Round 1 prompt and then builds the Round 2 prompt after an incremental fix commit
Then the Round 1 diff section is generated with -U5 context and excludes all *.vi.md artifact paths
And the Round 2 prompt includes delta_round_context for prev_sha..curr_sha with a one-line cumulative diff --stat reference
And the Round 2 prompt omits the full base...curr_sha diff block unless --full is explicitly passed

Scenario: [TTO-HP-02] [Tier C - Integration] Compact Gate 4 runner prints single-line GATE_PASS and stores full logs under build/quality

Given a project with a valid .agents/quality/check_quality.json registry whose providers exit with status 0
When verify_polyglot_registry.py runs with --compact
Then standard output contains single-line "GATE_PASS: <provider_or_cap>" entries instead of verbose JSON blobs
And full per-capability execution logs are written to build/quality/<provider>/<cap>.log
And the overall aggregated verdict equals PASS

Scenario: [TTO-HP-03] [Tier C - Integration] Option A default readiness tolerates in-flight .vi.md drift and deferred bdd_scenarios.vi.md

Given an epic directory containing current *.en.md design docs and bdd_scenarios.en.md
And bdd_scenarios.vi.md is absent while an existing .vi.md companion has un-synced sections during active Principal Review
When check_epic_readiness.py runs without --strict-bilingual
Then the readiness gate succeeds with status PASS on R1, R3, and R7 without failing on .vi.md drift or missing bdd_scenarios.vi.md
And check_bdd_traceability.py validates task coverage solely against bdd_scenarios.en.md

Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig resolves Role 2.3 programmer model and effort using config precedence

Given a .devtool/review_config.json defining providers.programmer.model as "gemini-4-hydrogen-xhigh" and thinking_level as "extra" (or legacy "gemini-3.8-flash-high" on disk)
And AGY_PROGRAMMER_MODEL environment override is unset
When lifecycle_runner.RunnerConfig resolves the programmer model and effort or dispatches agy with no CLI flag supplied
Then resolve_programmer_model returns "gemini-4-hydrogen-xhigh", resolve_programmer_effort returns "xhigh", and dispatched commands receive "--model gemini-4-hydrogen-xhigh --effort xhigh" via the shared legacy alias map
And supplying --programmer-model "gemini-4-pro-high" via CLI overrides both .devtool/review_config.json and environment variables

Scenario: [TTO-HP-05] [Tier C - Integration] Slimmed rules and dev-designer skill satisfy byte caps and release contract checks

Given the updated rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, skills/dev-lifecycle/SKILL.md, skills/dev-implementation/SKILL.md, and skills/task-observer/SKILL.md in the repository
When scripts/test_lifecycle_document_contract.py executes and file byte/word sizes are measured on disk
Then rules/CRITICAL_RULES.md measures at most 8192 bytes retaining §9 Shell Configuration and adding §10 Zero-Fluff Output Cap
And skills/dev-designer/SKILL.md measures at most 22528 bytes, skills/dev-lifecycle/SKILL.md stays <= 2500 words, and skills/dev-implementation/SKILL.md stays <= 4500 words while preserving every required section and Extracted reference link
And skills/task-observer/SKILL.md places <SUBAGENT-STOP> immediately after valid YAML frontmatter and amends its description trigger to exclude subagents and headless workers
And scripts/test_lifecycle_document_contract.py exits with status 0 and zero assertion failures

Scenario: [TTO-HP-06] [Tier C - Integration] Compact context restoration caps output at 4096 bytes and reads programmer config dynamically

Given a multi-repo workspace directory with active epic metadata, tasks, and open RFC entries
And .devtool/review_config.json configures providers.programmer to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
When scripts/resume_context.py runs with --compact --epic token_throttling_optimization and --emit-prompt implement
Then the compact context payload measures at most 4096 bytes and includes active epic snapshot, current repo git status, matching tasks, and relevant open RFCs
And the emitted handoff prompt specifies "gemini-4-hydrogen-xhigh" and "xhigh" read dynamically from .devtool/review_config.json

Scenario: [TTO-HP-07] [Tier C - Integration] Streamlined cross-model review fast-tracks clean code fixes and renders actual Executive Report findings

Given a cross-model review Round 1 verdict of CHANGES_REQUIRED containing only verified code bugs with zero shared-contracts conflicts
When lifecycle_runner.step_cross_model_review executes one remediation iteration followed by convergence
Then unambiguous code fixes bypass _draft_fix_plan and evaluate_programmer_fix_plan and route directly to _apply_code_fixes
And render_final_executive_report populates the Top 3 Highest-Risk Findings table directly from parsed review_results.md and principal_review.md entries rather than placeholder strings

Scenario: [TTO-HP-08] [Tier C - Integration] End-to-end token-throttling pipeline enforces compact prompts, review isolation, and programmer config

Given an isolated epic workspace bootstrapped with .devtool/review_config.json, task files containing target line ranges, and fake review/agy CLIs
When the lifecycle pipeline executes readiness, external review, worker dispatch, compact Gate 4, and executive summary generation
Then every review prompt respects the diff-only -U5 budget and writes raw output outside markdown files
And every worker prompt omits inlined source files while invoking gemini-4-hydrogen-xhigh with --effort xhigh
And compact Gate 4 emits single-line GATE_PASS statuses upon green verification
```

## Edge Cases and Boundaries

```gherkin
Scenario: [TTO-EC-01] [Tier A - Unit] Over-budget diff truncates to --stat summary and @@ hunk headers per changed file

Given a synthetic git diff exceeding MAX_DIFF_LINES (1500 lines) or MAX_DIFF_BYTES (60000 bytes)
When build_diff_section builds the diff payload for external review
Then the output falls back cleanly within the byte budget without dropping structural file boundaries
And the truncated section explicitly contains the git diff --stat summary alongside the file headers and @@ hunk headers for changed files

Scenario: [TTO-EC-02] [Tier A - Unit] Task runner enforces 25-line tail and Python quality manifests inject quiet pytest flags

Given a failing task check output with 120 stdout/stderr lines
And .agents/quality/python-quality.json alongside a scaffolded manifest from scaffold_quality_manifest.py
When run_task_checks.py formats failure evidence and the Python test command is inspected
Then run_task_checks.TAIL_LINES equals 25 and the emitted snippet retains only the last 25 non-empty lines
And both .agents/quality/python-quality.json and newly scaffolded Python quality manifests invoke pytest with "-q", "--tb=short", and "--maxfail=3"

Scenario: [TTO-EC-03] [Tier C - Integration] Design contract checker rejects large >200-line modified files lacking target symbol or line-range anchors

Given a task file referencing a non-new tracked Python source file exceeding 200 lines in Allowed files
And the task's Files and Impact Analysis sections omit any target symbol name or (L<start>-L<end>) line range for that file
When check_task_contract.py executes with --design against that task file
Then check_task_contract.py exits non-zero and reports the missing symbol or line-range anchor for that >200-line file
And adding a valid "path :: Symbol (L10-L85)" anchor clears the violation and exits with status 0

Scenario: [TTO-EC-04] [Tier A - Unit] Programmer effort normalization maps "extra" aliases to xhigh

Given raw effort values "extra", "EXTRA", "extra-high", "extra_high", and "xhigh"
When lifecycle_runner.normalize_agy_effort normalizes each configured thinking level
Then every variant returns the canonical flag value "xhigh"
And invoking the agy command builder passes "--effort", "xhigh" on the command line

Scenario: [TTO-EC-05] [Tier C - Integration] Selective task-reviewer gating skips trivial tasks and activates on high-risk or multi-module tasks

Given a trivial single-file documentation or utility task without high-risk labels and review_tier unset
And a complex task carrying review_tier: "full" or labels ["security", "concurrency"] or touching 3 non-test modules
When the selective task-reviewer criteria documented across dev-designer, dev-implementation, and subagent-driven-development are evaluated
Then the trivial single-file task skips the redundant task-reviewer subagent pass
And the complex or high-risk task triggers the dedicated task-reviewer pass before task sign-off

Scenario: [TTO-EC-06] [Tier C - Integration] Compact verify.sh --quiet prints concise section lines while --full executes all 17 suites

Given the repository tooling scripts and markdown skills under scripts/verify.sh
When bash scripts/verify.sh --quiet runs and when bash scripts/verify.sh --full runs
Then --quiet prints a single concise status line per passing section without verbose suite noise
And --full executes all registered verification sections §1 through §17 and exits with status 0
```

## State Transitions and Invariants

```gherkin
Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config migrates legacy gemini-3.8-flash defaults while preserving custom models

Given an existing .devtool/review_config.json with providers.programmer.model set to "gemini-3.8-flash-high"
And a second config file where providers.programmer.model is customized to "claude-sonnet-4-6"
When run_external_review.load_review_config loads each configuration file
Then the legacy "gemini-3.8-flash-high" entry is upgraded in-memory to "gemini-4-hydrogen-xhigh" with thinking_level "xhigh"
And the user-customized "claude-sonnet-4-6" entry remains untouched without being overwritten

Scenario: [TTO-ST-02] [Tier C - Integration] Handoff package and template exclude .vi.md files from AI coder Read First list

Given an epic directory containing spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md, and bdd_scenarios.vi.md
When package_epic.py generates handoff.md from skills/dev-lifecycle/references/handoff-template.md
Then the generated Read First section references only *.en.md documents and zero *.vi.md paths
And handoff-template.md contains no static legacy model hardcodes conflicting with config-driven Role 2.3 selection

Scenario: [TTO-ST-03] [Tier C - Integration] Stage 4 --strict-bilingual readiness gate enforces full .en.md and .vi.md parity

Given an epic directory whose .vi.md HLD retains identical heading levels but drifted out of sync with edited .en.md prose, or lacks bdd_scenarios.vi.md
When check_epic_readiness.py runs with --strict-bilingual and check_bdd_traceability.py plan --scenarios bdd_scenarios.en.md --tasks task_*.md runs with --strict-bilingual
Then check_epic_readiness.py --strict-bilingual exits non-zero detecting stale Spec/HLD sync provenance and missing bdd_scenarios.vi.md while check_bdd_traceability.py --strict-bilingual validates scenario ID parity
And after delta-syncing .vi.md provenance digests and adding bdd_scenarios.vi.md with matching IDs and ToC headings, both --strict-bilingual checks exit with status 0

Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review escalates to Role 2.2 when shared-contracts or architecture ambiguity arises

Given a cross-model review finding in Round 1 referencing shared-contracts/api_contract.md or an ambiguous architectural state transition
When lifecycle_runner.step_cross_model_review triages the round findings
Then fast-path auto-fix is NOT taken and either CRITICAL_CONFLICT halts immediately or fix_plan_round1.md is routed through Role 2.2 evaluation before any edit occurs

Scenario: [TTO-ST-05] [Tier C - Integration] Finishing-a-development-branch Stage 4 Pre-Finish hook synchronizes .vi.md before merge

Given skills/finishing-a-development-branch/SKILL.md in the updated agent kit
When the Stage 4 finishing workflow specification is inspected and checked by verify.sh §3 and §8
Then an explicit Stage 4 Pre-Finish bilingual sync step delta-syncs Spec and HLD .vi.md companions, generates bdd_scenarios.vi.md, and runs check_epic_readiness.py --strict-bilingual before merge
And all cross-references and doc contract invariants remain unbroken under verify.sh
```

## Async and Concurrency

```gherkin
Scenario: [TTO-AR-01] [Tier C - Integration] Parallel wave dispatch executes independent tasks concurrently with path-only Zero-Fluff prompts

Given an epic DAG containing two disjoint Wave 1 tasks (no mutual blocker dependency) and one Wave 2 task blocked by both
And an isolated worker pool initialized by manage_worker_pool.py
When lifecycle_runner.step_implementation executes the implementation phase using a thread-safe recording mock dispatcher
Then both Wave 1 tasks run concurrently inside distinct pool slots with status sync and git commits running inside cwd=slot_path so each slot commit contains only its owning task paths before serialized merge_slot integration
And each task prompt omits inlined task markdown bodies, forbids d3nexus:task-observer, injects only target file paths and line ranges, and includes the Zero-Fluff output cap

Scenario: [TTO-AR-02] [Tier C - Integration] Per-task clean context and per-round raw logs prevent cross-session transcript contamination

Given sequential Principal Review and Cross-Model Review rounds alongside consecutive task dispatches within a single epic run
When run_external_review.render_round writes logs and lifecycle_runner invokes Task N+1 after Task N commits
Then each review round writes its isolated raw transcript to a distinct build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log path without colliding across principal and code reviews or appending into adjacent round logs
And the Task N+1 invocation prompt contains no accumulated tool output or stderr from Task N
```

## Failure and Resilience

```gherkin
Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts emits one line per passing command and caps failing output + raw transcripts

Given a passing command returning 180 stdout lines with exit code 0 and a failing command returning 90 stderr lines with exit code 1
When run_external_review.fact builds prompt evidence and render_round persists the round artifact
Then the passing command produces a single "PASS: <label>" line omitting stdout
And the failing command includes the command label plus at most 25 trailing non-empty output lines
And unfiltered CLI body and stderr payloads route into build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log while Raw output: preserves pass headers, Verdict lines, and first error line so round_passes(round_output(lines)) still yields the true verdict

Scenario: [TTO-FR-02] [Tier C - Integration] Compact Gate 4 surfaces failing provider header and 25-line log tail on error

Given a quality registry containing one passing capability and one failing capability printing 80 diagnostic lines to stderr
When verify_polyglot_registry.py runs with --compact
Then the process exits non-zero reporting FAIL
And standard output prints "GATE_PASS:" for the passing capability plus the failing capability header and strictly at most 25 trailing log lines from build/quality/
And all 80 raw diagnostic lines remain preserved on disk inside build/quality/<provider>/<cap>.log

Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines bounds Gate 4 and intermediate check failure summaries to 25 lines

Given a subprocess failure from run_gate4 or run_intermediate_check emitting 120 traceback lines
When lifecycle_runner formats the failure message via _tail_lines(output, 25)
Then the returned failure excerpt contains at most 25 lines terminating at the final failing assertion summary
And the exception or state message propagated to the next step never exceeds 25 lines of traceback

Scenario: [TTO-FR-04] [Tier C - Integration] Quantitative regression tests fail loudly if rule, skill, context, or prompt sizes exceed caps

Given the live kit files and mock epic harness inside tests/test_token_throttling_acceptance.py
When the quantitative token-throttling acceptance suite executes under pytest
Then assertions explicitly check byte ceilings (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) and review/prompt budgets
And exceeding any ceiling fails with concrete byte-count diagnostics rather than generic boolean checks
```
