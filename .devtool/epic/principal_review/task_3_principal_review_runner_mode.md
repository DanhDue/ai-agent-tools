---
id: "task_3_principal_review_runner_mode"
status: "done"
priority: "high"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T10:03:37Z"
completedAt: "2026-10-23T10:03:37Z"
labels: ["review", "cli", "principal-review"]
order: "a3"
---

# Task 3: Principal Review Mode in the Runner

Epic: [principal_review](principal_review.en.md)

## Requirement Analysis

Teach `run_external_review.py` a second kind of review.
- `run --kind principal` sends the epic's design documents, not a code diff, to the Claude CLI or
  the Codex CLI, with the Principal Reviewer prompt and the `check_epic_readiness.py` report as
  facts.
- It records the round in `principal_review.md`.
- `check --kind principal` and `triage --kind principal` read that file.

Readiness is a precondition: a FAIL prints the existing banner and never invokes the CLI. With the
default `--kind code`, every behaviour of today's code review stays byte-identical. The two new
reference files hold the prompt and the rules.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/dev-implementation/references/principal-review-prompt.md` (new)
- `skills/dev-implementation/references/principal-review-rules.md` (new)

Read-only context:
- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (new) — the precondition (Tasks 1–2)
- `skills/dev-implementation/resources/scripts/test_check_epic_readiness.py` (new) — `build_ready_epic(root)`
- `skills/dev-implementation/resources/scripts/test_local_review.py` — the Ollama suite that must pass unchanged
- `skills/dev-implementation/references/external-review-prompt.md` — the output contract the principal prompt reuses
- `skills/dev-implementation/references/review-triage.md` — the triage discipline the prompt and rules defer to
- `.devtool/epic/principal_review/2026-10-22-principal-review-design.en.md` — §5.3 checklist P1–P8
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, `run_external_review.py`

## Design Rationale

One engine, two kinds: CLI invocation, the precondition banner, round recording, `check`, `triage`
and the tree-change guard are shared. That way the design review inherits years of hardening
instead of duplicating it. The selector is the only branch inside the shared functions, and `code`
reproduces today's file name and title exactly. The existing suite guards that.
`test_run_external_review.py` already carries 14 ruff and 1 mypy findings on `main`, so the Tier B
rows cover `run_external_review.py`, which is clean, rather than the test file.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`,
`d3nexus:receiving-code-review`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/run_external_review.py`: `run()`, `record_round()`, `check()`, `triage()`, `main()`, new `review_file()`, new `principal_artefact_lines()`, new `run_principal()`
- **Downstream Callers**: Gate 4's Review Choice options 2 and 3 in `dev-implementation` (unchanged, `--kind code`), the Principal Review loop and the Gate 3 check (Task 5).
- **Cross-Platform Bridges**: the Claude CLI and the Codex CLI, faked in tests.
- **Target Test Coverage Threshold**: every new branch of `run`, `check` and `triage` under `--kind principal` has a named test.

### BDD SCENARIOS

Covers: PRV-HP-02, PRV-HP-03, PRV-ST-01, PRV-ST-02, PRV-AR-01, PRV-FR-03, PRV-FR-04

```gherkin
Scenario: [PRV-HP-02] [Tier C - Integration] A principal round is recorded in principal_review.md
  Given the PRV-HP-01 epic committed in a clean tree and a fake "claude" on PATH that saves its stdin and prints "Verdict: PASS"
  When run_external_review.py run --kind principal --epic-dir demo_epic --base main --cli claude runs
  Then the saved prompt contains "Principal Reviewer", "Result: 0 FAIL, 0 WARN — PASS", ".devtool/epic/demo_epic/demo_epic.en.md" and the SHA of main
  And the saved prompt does not contain "audit_epic.py"
  And principal_review.md starts with "# Principal Review: demo_epic" and has "## Round 1" with "- **Kind**: principal", "- **CLI**: claude", "- **Status**: completed" and "- **Verdict**: PASS"
  And review_results.md does not exist
  And the exit code is 0

Scenario: [PRV-HP-03] [Tier C - Integration] Findings with proposed edits become table rows and set the exit code
  Given a fake "codex" that prints "Verdict: CHANGES REQUIRED" and "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult."
  When run --kind principal --cli codex runs
  Then principal_review.md has a findings row with "Important", "task_2:Decisions Already Made" and "Proposed: keep TrackPersistResult."
  And the round's "- **Verdict**: CHANGES REQUIRED"
  And the exit code is 1

Scenario: [PRV-ST-01] [Tier C - Integration] Decisions move check --kind principal from 1 to 0, independent of code rounds
  Given principal_review.md whose latest completed round has one Important finding with an empty Decision cell
  And review_results.md whose latest round has no finding
  When run_external_review.py check --kind principal --epic-dir demo_epic runs
  Then it prints "undecided: #1 Important" and exits 1
  And check --epic-dir demo_epic without --kind exits 0
  When the Decision cell becomes "fixed in abc1234"
  Then check --kind principal exits 0

Scenario: [PRV-ST-02] [Tier C - Integration] triage reads the file --kind selects
  Given principal_review.md with 2 rounds and review_results.md with 1 round
  When run_external_review.py triage --kind principal --epic-dir demo_epic runs
  Then the output starts "# Review Triage: demo_epic, Round 2"
  And triage without --kind prints "Round 1"
  When principal_review.md does not exist
  Then triage --kind principal prints "no review round recorded for demo_epic" and exits 2

Scenario: [PRV-AR-01] [Tier C - Integration] A second round before the first is committed is refused and rounds number in order
  Given a completed principal round 1 written but not committed
  When run --kind principal runs again
  Then it prints "commit or stash your changes before a review" and exits 2
  And the fake CLI is called exactly once in total
  When round 1 is committed and run --kind principal runs again
  Then principal_review.md has "## Round 1" followed by "## Round 2"

Scenario: [PRV-FR-03] [Tier C - Integration] A readiness FAIL blocks the CLI and records nothing
  Given the PRV-EC-01 epic committed in a clean tree and a fake "claude" that records every call
  When run --kind principal --cli claude runs
  Then stderr shows "WAS NOT INVOKED" and "check_epic_readiness.py"
  And stderr shows the line containing "R5 FAIL"
  And the fake CLI was never called
  And principal_review.md does not exist and the exit code is 2

Scenario: [PRV-FR-04] [Tier C - Integration] --kind principal --cli ollama is rejected before any work
  Given a throwaway epic repository with an uncommitted change
  When run --kind principal --cli ollama --model m runs
  Then stderr shows "--kind principal supports --cli claude or codex"
  And stderr never shows "[Pre-check]"
  And the exit code is 2 and no principal_review.md exists
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py -k PrincipalReviewTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/run_external_review.py` | exit 0 | — |
| V6 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/references/principal-review-prompt.md skills/dev-implementation/references/principal-review-rules.md` | exit 0 | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/dev-implementation/resources/scripts/test_run_external_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- An existing test in `test_run_external_review.py` or `test_local_review.py` needs a changed assertion: `--kind code` must stay byte-identical.

## Decisions Already Made

- **New frozen symbols** (HLD, Module Contracts):
  ```python
  KINDS = ("code", "principal")
  PRINCIPAL_PROMPT = SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"
  PRINCIPAL_RULES = SCRIPTS.parent.parent / "references" / "principal-review-rules.md"

  def review_file(kind: str) -> tuple[str, str]
  def principal_artefact_lines(root: Path, epic_dir: str) -> str
  def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int
  ```
  `review_file("code") == ("review_results.md", "Cross-Model Review")` and
  `review_file("principal") == ("principal_review.md", "Principal Review")`.
- **Arguments**: `run`, `check` and `triage` each gain `--kind` with `choices=KINDS`, `default="code"`.
- **Shared functions**:
  - `record_round` builds `path = root / ".devtool" / "epic" / args.epic_dir / name`, and starts a new file with `f"# {title}: {args.epic_dir}\n"`, where `name, title = review_file(getattr(args, "kind", "code"))`;
  - `check` and `triage` resolve `path` the same way;
  - no other line of those functions changes.
- **`run` order for `--kind principal`**, each failure exiting 2 with no round:
  1. `--cli ollama`: print `--kind principal supports --cli claude or codex` to stderr, before any other check.
  2. The CLI is not on PATH: today's message.
  3. A dirty tree: today's message, `commit or stash your changes before a review`.
  4. In `run_principal`: `run_gate("check_epic_readiness.py", [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir], root, args.facts_timeout)`. A `PreconditionFailedError` goes through `print_gate_banner(error, args.cli)`.
- **Prompt**: `Template(PRINCIPAL_PROMPT.read_text(encoding="utf-8")).safe_substitute(rules=PRINCIPAL_RULES.read_text(encoding="utf-8").strip(), sha=sha, base=args.base, base_sha=<git rev-parse --verify args.base>, epic_dir=f".devtool/epic/{args.epic_dir}", artefacts=principal_artefact_lines(root, args.epic_dir), readiness_output=<the gate's stdout, rstripped>)`.
- **Execution and record**: `before = status_lines(root)`, then `code, out, err = execute(cli_command(args.cli, args.model), root, args.timeout, prompt)`, then `changed = tree_changes(root, before, sha)`, then `return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed, {"Kind": "principal"})`. `collect_facts`, `audit_epic.py`, the integration commands and `build_diff_section` are never called for `--kind principal`.
- **`principal_artefact_lines`**: one ``- `.devtool/epic/<epic_dir>/<name>` `` line each, in this order:
  1. the `*-design.en.md` and `*-design.vi.md` files;
  2. `<epic_dir>.en.md` and `<epic_dir>.vi.md`;
  3. `bdd_scenarios.en.md` and `bdd_scenarios.vi.md`;
  4. every `task_*.md`, sorted;
  5. `handoff.md` when present.

  It never lists `review_results.md` or `principal_review.md`.
- **`principal-review-prompt.md`**:
  - the reader is "the Principal Reviewer who signs off this epic before implementation";
  - it is strictly read-only, and must read the source at `$sha`;
  - sections: Candidate (`$sha`, `$base`, `$base_sha`, `$epic_dir`), Artefacts (`$artefacts`), Readiness facts (`$readiness_output` in a `text` fence), Rules (`$rules`), and a Checklist with P1–P8 worded as in the spec's §5.3;
  - Required output is the external review prompt's block, with the finding line `[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>`.
- **`principal-review-rules.md`**:
  - severities: Critical, the epic cannot reach its goal or Gate 4 as designed; Important, a task would hit Stop-and-Report or ship wrong behaviour; Minor, wording and consistency;
  - the readiness report is already proven: do not restate it, spend the review on judgement and grounding;
  - every claim about the source names the file and line it read;
  - a finding names the artefact and section to change, and its `Proposed:` edit.
- **Tests**: class `PrincipalReviewTest(ReviewCase)`, one `test_prv_*` method per covered scenario. Fake `claude` and `codex` executables go on `PATH` as the existing cases do, and the fixture epic comes from `test_check_epic_readiness.build_ready_epic`.

## Definition of Done

- All seven covered scenarios have a `test_prv_*` method in `PrincipalReviewTest` and pass in the JUnit report. (V2, V7)
- The existing code-review and Ollama suites pass unchanged. (V2, V3, V7)
- Lint and strict type checking report zero issues on `run_external_review.py`, and the two reference files lint clean. (V4, V5, V6)
- The principal prompt reads as a Principal Reviewer's sign-off brief and covers P1–P8. (Gate 5)

## Dependencies & Blockers

- Blocked by [Task 2](task_2_readiness_grounding_and_baseline.md)
- Blocks [Task 5](task_5_principal_review_choice_and_acceptance.md).

## References & Rollback

- [Epic HLD](principal_review.en.md), Module Contracts and Sequence Diagram.
- Spec: [2026-10-22-principal-review-design.en.md](2026-10-22-principal-review-design.en.md), §5.2 and §5.3.
- **Rollback**: revert the commit; `--kind` disappears and Gate 4's Review Choice is unaffected.
