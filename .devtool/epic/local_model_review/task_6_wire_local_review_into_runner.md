---
id: "task_6_wire_local_review_into_runner"
status: "todo"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:10:00Z"
completedAt: null
labels: ["review", "ollama", "cli"]
order: "a6"
---

# Task 6: Wire Local Model Review Into the Runner

Epic: [local_model_review](local_model_review.en.md)

## Requirement Analysis

Make `run_external_review.py run --cli ollama --model <model>` work end to end on top of Tasks 2
to 5: new arguments, the order of checks, probing before facts, building and fitting every slice
before the first model call, sequential passes with a live progress line, stopping at the first
failed pass, and handing all passes to `record_round`. End-to-end tests run the real `main()` in a
throwaway epic repository against the fake Ollama server.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/local_review.py` (new) — transport, slices and prompt base
- `skills/dev-implementation/resources/scripts/test_run_external_review.py` — the guard that must pass unchanged
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts and Sequence Diagram

## Design Rationale

Every cheap check runs before any expensive one: missing `--model`, then a dirty tree, then the
probe, then the facts, then the budget for every slice, and only then the model. A run that cannot
succeed never spends model time. Passes are sequential because a local GPU serialises them anyway,
and a failed pass ends the run because the round would be `no verdict` regardless.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `run_external_review.main` (arguments), `run` (the ollama branch).
- **Downstream callers**: dev-implementation Review Choice option 3 (Task 7).
- **Cross-platform bridges**: HTTP to a local Ollama server, faked in tests.
- **Target test coverage threshold**: every exit path of the ollama branch has a named test.

### BDD SCENARIOS

Covers: LMR-HP-03, LMR-EC-01, LMR-AR-01, LMR-AR-02, LMR-FR-02, LMR-FR-04, LMR-FR-07

```gherkin
Scenario: [LMR-HP-03] [Tier C - Integration] A local review of a two-task epic records one round
  Given a throwaway epic with two task commits and a fake Ollama server that answers every chat with "Verdict: PASS"
  When run --cli ollama --model qwen38-reviewer --host <fake server> runs
  Then the server receives exactly 3 chat requests
  And review_results.md gains "## Round 1" with "- **CLI**: ollama", "- **Model**: qwen38-reviewer", "- **Passes**: 3", "- **Status**: completed" and "- **Verdict**: PASS"
  And the run exits 0

Scenario: [LMR-EC-01] [Tier C - Integration] Local review without a model stops first
  Given a throwaway epic repository
  When run --cli ollama runs without --model
  Then it exits 2 with "--cli ollama needs --model" on stderr
  And stderr never shows "[Pre-check] audit_epic.py"
  And no review_results.md exists

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

Scenario: [LMR-FR-02] [Tier C - Integration] An unreachable server stops the run before facts
  Given a throwaway epic repository and no server on the --host port
  When run --cli ollama --model m runs
  Then stderr shows "WAS NOT INVOKED" and "Ollama server not reachable"
  And stderr never shows "[Pre-check] audit_epic.py"
  And the run exits 2 and no review_results.md exists

Scenario: [LMR-FR-04] [Tier C - Integration] A failing pass stops the run and records what it has
  Given a fake server that answers the first chat with "Verdict: PASS" and the second with HTTP 500
  When run --cli ollama runs over three slices
  Then the server receives exactly 2 chat requests
  And the round has "- **Status**: no verdict", raw output with "### Pass 1" and the text "HTTP 500"
  And the run exits 2

Scenario: [LMR-FR-07] [Tier C - Integration] A slice that cannot fit stops the run before any chat
  Given --num-ctx 1000 and a task file larger than 1800 bytes
  When run --cli ollama runs
  Then it exits 2 with a message naming the task id and "raise --num-ctx"
  And the fake server receives 0 chat requests
  And no review_results.md exists
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k RunnerTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k RunnerTest` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_6.xml skills/dev-implementation/resources/scripts/test_local_review.py skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; results build/test-results/task_6.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Wiring needs a change to a `local_review.py` signature frozen in the HLD.

## Decisions Already Made

- Arguments of `run`: `--cli` choices `("claude", "codex", "ollama")`; `--host` with default
  `local_review.host_from_env()`; `--num-ctx` (`type=int`, default `None`). `--timeout` keeps its
  default 1800 and applies per pass for `ollama`. `run_external_review.py` imports `local_review`.
- Order for `--cli ollama`, each failure exiting 2 with no round:
  1. no `--model`: print `--cli ollama needs --model` to stderr;
  2. dirty tree: today's message;
  3. `local_review.probe(args.host, args.model)`; a `LocalReviewError` goes through
     `print_gate_banner(PreconditionFailedError("Ollama probe", str(error)), "ollama")`;
  4. `collect_facts` unchanged;
  5. `local_review.build_slices(root, args.epic_dir, args.base, sha, audit_output, results_output, EXCLUDES)`,
     then for every slice `system = render_system(s)` and
     `fit(s, int(ctx * PROMPT_SHARE) - estimate_tokens(system))` with
     `ctx = args.num_ctx or model_ctx or DEFAULT_NUM_CTX`; a `LocalReviewError` goes through
     `print_gate_banner(PreconditionFailedError("Context budget", str(error)), "ollama")`.
- Then, per fitted slice in order: `user = render_user(s)`;
  `options = chat_options(model_ctx, args.num_ctx, estimate_tokens(system) + estimate_tokens(user))`;
  `reply = chat(args.host, args.model, system, user, options, args.timeout)`;
  `Pass(s.label, code, reply.content, reply.error or "", user, s.omitted, reply.done_reason)` with
  `code = 0` when `reply.error is None`, `None` when it starts with `timed out`, else 1.
- Progress on stderr, flushed: `⏳ [Pass <i>/<n>] <label> ... ` then `✅ <seconds>s` or
  `❌ <error>`. The first pass whose error is set, or whose `done_reason` is not `stop`, ends the
  loop.
- `record_round(root, args, sha, passes, changed, {"Passes": str(n), "Context": str(ctx)})`, where
  `Passes` is the number of slices planned and `changed` is computed around the loop as today.
- The Claude CLI and Codex CLI branch is untouched apart from what Task 5 already changed.

## Definition of Done

- All seven covered scenarios have a `test_lmr_*` method in `RunnerTest` and pass in the JUnit
  report. (V2, V6)
- The existing runner suite passes unchanged. (V3, V6)
- Lint and strict type checking report zero issues on the touched Python files. (V4, V5)

## Dependencies & Blockers

Blocked by [Task 2](task_2_ollama_transport.md)
Blocked by [Task 3](task_3_review_slices_and_budget.md)
Blocked by [Task 4](task_4_local_review_prompt_base.md)
Blocked by [Task 5](task_5_record_round_from_passes.md)

Blocks [Task 7](task_7_review_choice_workflow_and_acceptance.md).

## References & Rollback

- [Epic HLD](local_model_review.en.md), Sequence Diagram and Module Contracts.
- **Rollback**: revert the commit; `--cli ollama` disappears and options 1 and 2 are unaffected.
