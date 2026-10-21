---
id: "task_4_local_review_prompt_base"
status: "done"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:35:17Z"
completedAt: "2026-10-21T09:35:17Z"
labels: ["review", "prompt", "ollama"]
order: "a4"
---

# Task 4: Write the Local Review Prompt Base

Epic: [local_model_review](local_model_review.en.md)

## Requirement Analysis

Write the prompt base that teaches a tool-less local model the d3nexus workflow, and the code that
assembles it per slice. Three reference files: `local-review-prompt.md` (the system-message
template), `local-review-checklists.md` (`## Task pass` and `## Epic pass`) and
`local-review-platforms.md` (`## Flutter`, `## Android`, `## iOS`, `## Rust`, `## Python`). Two
functions in `local_review.py`: `platform_sections` picks sections by the extensions of a slice's
paths, and `render_system` fills the template. The platform file quotes only rules the kit already
defines, and a test proves it against the source skills.

## Files

Allowed files:
- `skills/dev-implementation/references/local-review-prompt.md` (new)
- `skills/dev-implementation/references/local-review-checklists.md` (new)
- `skills/dev-implementation/references/local-review-platforms.md` (new)
- `skills/dev-implementation/resources/scripts/local_review.py` (new)
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `skills/dev-implementation/references/review-rules.md` (new) — inserted as `$rules`
- `skills/dev-implementation/references/external-review-prompt.md` — verdict grammar to keep identical
- `skills/architecture-audit/SKILL.md` — ARCH Blocker rules
- `skills/code-health-audit/SKILL.md` — HLT Blocker rules
- `skills/security-audit/SKILL.md` — SEC Blocker rules
- `skills/rust-quality-check/references/rust-architecture-governance.md` — five named Rust policies
- `skills/python-quality-check/references/python-architecture-governance.md` — four named Python policies
- `.devtool/epic/local_model_review/2026-10-21-local-model-review-design.en.md` — Prompt Base section

## Design Rationale

A local model knows nothing of gates, task files or evidence, and cannot look them up, so the
primer states them. Loading platform sections per slice from file extensions handles polyglot
repositories that `detect_project_type.sh` reports as one type (spec D9). Only Blocker-level rules
are quoted, because Warning-level rules only add noise on a small model (spec D10). The analysis
comes before the verdict block, because a model with thinking off reasons only in visible text (spec D7).
Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`,
`d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `local_review.EXTENSIONS`, `platform_sections`, `render_system`,
  and the three reference files.
- **Downstream callers**: the runner (Task 6) calls `render_system` once per slice.
- **Cross-platform bridges**: None.
- **Target test coverage threshold**: every quoted rule ID and policy name is checked against its source.

### BDD SCENARIOS

Covers: LMR-HP-05, LMR-HP-07, LMR-EC-05

```gherkin
Scenario: [LMR-HP-05] [Tier C - Integration] The system message fits its pass type
  Given a task slice whose diff touches "lib/a.dart"
  When render_system runs
  Then the message contains "Decisions Already Made", "No Reconstructed Logic", the "## Flutter" section text, the "## Task pass" checklist and "Verdict: PASS"
  And it contains none of "$rules", "$platform_rules" and "$checklist"
  And an epic slice receives the "## Epic pass" checklist instead of the task one

Scenario: [LMR-HP-07] [Tier C - Integration] Every quoted platform rule exists in the kit
  Given references/local-review-platforms.md
  When the test collects the rule IDs of the Flutter, Android and iOS sections and the bold rule names of the Rust and Python sections
  Then each ID occurs in a row marked "Blocker" of architecture-audit, code-health-audit or security-audit SKILL.md
  And each Rust name occurs in rust-architecture-governance.md and each Python name in python-architecture-governance.md

Scenario: [LMR-EC-05] [Tier C - Integration] Platform sections follow the touched extensions
  Given the paths "app/lib/a.dart" and "native/src/b.rs"
  When platform_sections runs
  Then it returns exactly the Flutter section followed by the Rust section
  And for the paths "README.md" and "web/x.ts" it returns an empty list
  And render_system for that slice contains "No platform rules apply to this slice."
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k PromptBaseTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k PromptBaseTest` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- A rule the prompt needs is not defined in any kit skill: report it instead of inventing it.

## Decisions Already Made

- Frozen constant: `EXTENSIONS = {".dart": "Flutter", ".kt": "Android", ".kts": "Android", ".swift": "iOS", ".rs": "Rust", ".py": "Python"}`.
- `def platform_sections(paths: Iterable[str]) -> list[str]`: the `task_contract.section` bodies of
  `local-review-platforms.md`, each prefixed with its `## <name>` heading, for the platforms whose
  extensions occur, in the order Flutter, Android, iOS, Rust, Python, without duplicates.
- `def render_system(slice_: Slice) -> str`: `string.Template(local-review-prompt.md).safe_substitute(rules=..., platform_rules=..., checklist=...)`.
  `rules` is `review-rules.md` stripped; `platform_rules` is the joined sections, or
  `No platform rules apply to this slice.`; `checklist` is the `## Task pass` or `## Epic pass`
  section of `local-review-checklists.md` with its heading, chosen by `slice_.kind`.
- `local-review-prompt.md` is English and holds, in order: role and hard limits (one slice, no
  tools, judge only what is shown, never invent contents, line numbers, commands or test names,
  report anything missing as `[Minor] <slice>:not-shown — <what>`); a workflow primer of about 40
  lines (Gates 1 to 4 and that Gate 4 already passed; the task file sections Allowed files,
  Read-only context, Decisions Already Made, Verification with `Vn` RED and GREEN rows, Definition
  of Done and `(Gate 5)` items; evidence recorded by `run_task_checks.py`; scenario IDs `HP`, `EC`,
  `ST`, `AR`, `FR` each covered by a passing integration test; `Fix` commits and protected paths);
  `$rules`; `$platform_rules`; `$checklist`; the output format.
- The output format asks for `## Analysis` first, one short paragraph per checklist item quoting
  the shown line it relies on, with no bracketed severity tag; then the verdict block with exactly
  the grammar of `external-review-prompt.md` (`Verdict: PASS` or `Verdict: CHANGES REQUIRED`, then
  `[Critical|Important|Minor] <artefact>:<location> — <problem>` lines) and one worked example.
  Critical or Important requires a quote from the shown content.
- `local-review-checklists.md` items are those of the spec's Pass Checklists section, verbatim in
  meaning.
- `local-review-platforms.md`: the Flutter, Android and iOS sections quote only rules whose row is
  marked Blocker in `architecture-audit`, `code-health-audit` or `security-audit`, as
  `` - `<ID>` **<title>** — <one-line rule> ``; the Rust section quotes the five named policies of
  `rust-architecture-governance.md`, the Python section the four of
  `python-architecture-governance.md`, as `- **<name>** — <one-line rule>`. Each section says the
  rules apply to added lines of production files and that a violation is reported as `Important`
  with the rule ID or name in its Problem.

## Definition of Done

- All three covered scenarios have a `test_lmr_*` method in `PromptBaseTest` and pass in the JUnit
  report. (V2, V5)
- Every quoted platform rule is proven to exist at Blocker level or by name in its source. (V2)
- Lint and strict type checking report zero issues. (V3, V4)
- The prompt base reads as a clear brief for a reviewer who has never seen the kit. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_1_share_verification_rules.md)

Blocks [Task 6](task_6_wire_local_review_into_runner.md).

## References & Rollback

- [Epic HLD](local_model_review.en.md), Module Contracts.
- [Approved spec](2026-10-21-local-model-review-design.en.md), Prompt Base.
- **Rollback**: revert the commit; nothing renders the prompt yet.
