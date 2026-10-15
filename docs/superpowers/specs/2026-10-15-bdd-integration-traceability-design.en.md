# BDD Integration Traceability Design

- **Date**: 2026-10-15
- **Status**: Approved
- **Scope**: `dev-designer`, `dev-implementation`, `dev-lifecycle`, a new
  `dev-implementation/resources/scripts/check_bdd_traceability.py` with its tests,
  `scripts/verify.sh`
- **Next step**: `writing-plans` (one implementation plan, no HLD)

## Table of Contents

- [1. Background](#1-background)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Decisions](#3-decisions)
- [4. Scenario IDs](#4-scenario-ids)
- [5. Test References](#5-test-references)
- [6. Design Declarations](#6-design-declarations)
- [7. Traceability Script](#7-traceability-script)
- [8. Enforcement Points](#8-enforcement-points)
- [9. Error Handling](#9-error-handling)
- [10. Testing](#10-testing)
- [11. Risks and Dependencies](#11-risks-and-dependencies)
- [12. Out of Scope](#12-out-of-scope)

## 1. Background

The epic lifecycle already promises "100% BDD-to-test traceability".
[dev-designer](../../../skills/dev-designer/SKILL.md) requires every scenario to "map 1-to-1 or
1-to-N to an automated test case", and [dev-implementation](../../../skills/dev-implementation/SKILL.md)
forbids marking a task `done` unless 100% of its scenarios have passing tests. Nothing checks
either promise.

A survey of the epics in `.devtool/epic/` shows what that costs:

- Scenarios live at two levels that are never linked: the epic's `bdd_scenarios.en.md` — the
  behavioural contract — and the BDD SCENARIOS section of each task file, tagged `[Tier A - Unit]` or
  `[Tier C - Integration]`, without identifiers.
- Scenario identifiers appear in one epic of three (11 of 64 scenarios), chosen ad hoc by the agent,
  in two dimension spellings (`PY-HP-01`, `PY-EDGE-01`).
- No test in the repository mentions any scenario identifier.
- The Coverage Matrix in the `quality_check` executive report is code coverage, not scenario
  coverage.
- Epic-level scenarios tagged as unit-level get unit tests with mocks only. Nothing proves the epic's
  behavioural contract holds when the components run together.

The developer asked for an additional part in the BDD/TDD three-tier standard: automated integration
tests mapped to the BDD scenarios, with **every scenario mapped to at least one test**.

## 2. Goals and Non-Goals

**Goals:**

- Every scenario in an epic's `bdd_scenarios.en.md` is covered by at least one automated integration
  test.
- The mapping is checked by a script with an exit code, at design time and at implementation time.
- Gate 4 cannot turn green while any scenario is uncovered.
- Work identically on every platform the kit supports: Web, Flutter, Android, iOS, Python, Rust.

**Non-Goals:**

- Changing `quality_check`, its contracts, its schemas, or any platform provider.
- Executable Gherkin and BDD runner frameworks.
- Non-epic work: `writing-plans` is unchanged.
- Retrofitting identifiers into epics already archived.
- Proving that a test asserts the behaviour its identifier names.

## 3. Decisions

| # | Decision | Reason |
|---|----------|--------|
| D1 | Every scenario in the epic-level `bdd_scenarios.en.md` needs at least one automated integration test. One test may cover several scenarios | The developer's requirement. "At least one" replaces "1-to-1 or 1-to-N" everywhere |
| D2 | Task-level `[Tier A - Unit]` scenarios keep their unit tests, under the same "at least one" wording | Unit and integration coverage answer different questions; this change adds the second without removing the first |
| D3 | No waivers. A scenario that cannot be automated is rewritten at Gate 2 | A waiver list would recreate the honour system this change removes |
| D4 | The new requirement is a mandatory part of Tier C, named BDD Automation, not a Tier D | Tier C is already the integration tier; the three-tier standard keeps its numbering and every reference to it stays valid |
| D5 | Mandatory scenario identifiers, identifiers in test names, and a checking script (Approach A) | A hand-maintained matrix (Approach B) is the honour system that already failed. Executable Gherkin (Approach C) imposes a runner per platform, and Swift has no mature one |
| D6 | The check runs outside `quality_check`. Gate 4 becomes: the traceability script exits 0 **and** `quality_check` returns PASS, both on the same candidate SHA | `dev-implementation` Phase 4 is the only caller of the `epic` profile, so enforcement there is as strong as an orchestrator-level check and changes no contract. Six per-provider copies of identical logic were rejected |
| D7 | The script validates identifier *shape* only, and finds scenarios by any Gherkin scenario keyword, English or Vietnamese | Existing epics already use more than one dimension code, and `.vi.md` files translate keywords (`Kịch bản:`) |
| D8 | A test that references an identifier no longer in the document fails the full check | Forces the document and the tests to stay in step, the same rule as "docs stay truthful" |

## 4. Scenario IDs

Every scenario line inside a `gherkin` fence of `bdd_scenarios.en.md` and `bdd_scenarios.vi.md`
starts with an identifier in brackets. A tier tag, when present, follows it:

```gherkin
Scenario: [PY-HP-01] [Tier C - Integration] Auto-detect Python workspace and scaffold manifest
```

- **Scenario keywords recognised:** `Scenario`, `Scenario Outline`, `Scenario Template`, `Example`,
  `Tình huống`, `Kịch bản`, `Khung tình huống`, `Khung kịch bản`.
- **Shape:** uppercase alphanumeric segments joined by `-`, ending in a digit run —
  `[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+`. Recommended convention: `<EPIC>-<DIM>-<NN>` with `HP`, `EC`,
  `ST`, `AR`, `FR` for the five dimensions. The script does not enforce the convention.
- **Uniqueness:** each identifier appears once in the document.
- **Language parity:** `bdd_scenarios.vi.md` carries exactly the same identifier set. Identifiers are
  never translated.
- **Prefix:** the first segment. All identifiers sharing a prefix belong to this epic, and no other
  epic in the project may use it: integration test roots hold every epic's tests, so a shared prefix
  would let one epic's tests cover — or look stale to — another's. The prefix is what the stale check
  looks for (§7).

## 5. Test References

An integration test covers an identifier when the identifier appears in a test file under one of
the declared integration test roots (§6) — in the test's name, description, or tag. Matching is
case-insensitive, treats `-` and `_` alike, and requires that no letter or digit sits directly
before or after the match. That lets every platform use its idiom:

| Platform | Example |
|----------|---------|
| Python | `def test_py_hp_01_scaffold_manifest():` |
| Rust | `fn py_hp_01_scaffold_manifest()` |
| Flutter | `testWidgets('[PY-HP-01] scaffolds the manifest', ...)` |
| Web | `test('[PY-HP-01] scaffolds the manifest', ...)` |
| iOS | `@Test("[PY-HP-01] scaffolds the manifest")` |
| Android | ``@Test fun `PY-HP-01 scaffolds the manifest`()`` |

- One test may carry several identifiers; each identifier needs at least one test (D1).
- Markdown files under the roots are ignored, and so are files that are not valid UTF-8.
- **Stale references (D8)** are detected in the canonical form only — an uppercase, hyphenated token
  matching `<PREFIX>(-[A-Z0-9]+)*-[0-9]+` that is not an identifier in the document. The snake_case
  and lowercase forms count towards coverage but not towards staleness: in `test_py_hp_01_retry_2`
  the script cannot tell where an identifier ends and a test name begins, and a short prefix such as
  `PY` would flag unrelated lowercase text like `py-3`.

## 6. Design Declarations

`dev-designer` adds three things to the documents it already writes.

1. **Integration test roots.** The HLD's Integration Test Plan gains a mandatory line, in both
   language variants:

   ```text
   Integration test roots: tests/integration/, tests/e2e/
   ```

   Defaults per platform come from the list already in dev-designer's parallel-execution Rule 2:
   `tests/e2e/` for Web, `integration_test/` for Flutter, `app/src/test/` and `shell/src/test/` for
   Android, `App/Tests/` and `Shell/Tests/` for iOS, `tests/integration/` for Python, `tests/` for
   Rust.
2. **`Covers:` in task files.** The BDD SCENARIOS section of each task gains one line naming the
   epic scenario identifiers whose integration tests that task writes:

   ```text
   Covers: PY-HP-01, PY-EDGE-02
   ```

   A task with no epic-level scenario — a Tier B tooling task, for instance — omits the line. Every
   identifier must appear in at least one task's `Covers:`. The final Tier C task usually takes the
   identifiers no earlier task covers.
3. **Gate 2 summary.** The task-breakdown checkpoint lists each proposed task with its `Covers:`
   identifiers, so the developer approves the mapping together with the split.

## 7. Traceability Script

`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, standard library only,
with `test_check_bdd_traceability.py` beside it in the `unittest` style of its sibling scripts.

```bash
check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
```

`--roots` and `--ids` accept space- or comma-separated values, so the HLD's roots line and a task's
`Covers:` line can be copied verbatim.

**Both modes** first validate the scenario document: every scenario line has an identifier, every
identifier has the right shape and appears once, and — when a `.vi.md` sibling exists — the two
identifier sets are equal.

**`plan` mode** reads every `Covers:` line in the given task files, including list-item and bold
variants (`- **Covers**: ...`). It fails when an identifier is in no task, or when a `Covers:` line
names an identifier the document does not have.

**`tests` mode** walks the roots and fails when an identifier has no covering file. With `--ids`, it
checks only those identifiers and skips the stale check, so a per-task run is not blocked by another
task's work. Without `--ids`, it also runs the stale check (§5).

**Output:** a matrix of identifier to covering tasks (`plan`) or to `file:line` (`tests`), with
`(none)` where uncovered, followed by a summary line:

```text
PY-HP-01    tests/integration/test_scaffold.py:12
PY-HP-02    (none)
Result: 10/11 covered — FAIL
```

A root that does not exist yet is reported as a warning and skipped; an uncovered identifier still
fails the run.

**Exit codes:** `0` all covered; `1` a traceability failure — uncovered, stale, unknown, missing,
malformed, duplicated or mismatched identifiers; `2` a usage error, such as a missing scenario or
task file, or no existing root at all.

`dev-designer` and `dev-lifecycle` reach the script through their own skill directory, as
`dev-implementation` already does for `integrate_branch.py`:

```bash
TRACE="$SKILL_DIR/../dev-implementation/resources/scripts/check_bdd_traceability.py"
```

## 8. Enforcement Points

| Where | Check |
|-------|-------|
| `dev-designer`, after Step 2 writes the task files and before the Step 3 commit | `plan` over `.devtool/epic/<epic_dir>/task_*.md` — the epic's own mirrors, never `.devtool/features/`, which can hold other epics' tasks — must exit 0 |
| `dev-designer`, three-tier standard | One platform-neutral paragraph, "Tier C — BDD Automation", after the per-platform tier lists; the per-platform blocks stay as they are |
| `dev-designer`, task template | The BDD SCENARIOS section documents the `Covers:` line; the Zero Uncovered Scenarios Rule says "at least one" |
| `dev-implementation`, the shared traceability rule after the Tri-Persona blocks | The Integration persona writes at least one integration test per identifier in the task's `Covers:`, with the identifier in the test's name or description. Applies to all six platforms without editing each block |
| `dev-implementation`, Gate to Done of each task | `tests --ids <the task's Covers>` exits 0 |
| `dev-implementation`, Phase 4 | Full `tests` exits 0 **before** `quality_check` runs; on failure, return to Phase 2. The matrix is part of the Gate 5 report |
| `dev-lifecycle`, Gate 4 | Approver becomes "`check_bdd_traceability.py` + `quality_check`". Gate 4 is 🟢 only when the script exits 0 and `quality_check` returns PASS on the same SHA. Candidate immutability covers both: a new commit makes both stale |

## 9. Error Handling

| Failure | Guard |
|---------|-------|
| A scenario has no identifier, or a malformed or duplicate one | Both modes fail before checking coverage |
| `.vi.md` identifiers drift from `.en.md` | Language parity check |
| An identifier is assigned to no task | `plan` fails before the design commit |
| A `Covers:` line names a deleted or mistyped identifier | `plan` fails |
| An identifier has no integration test | Per-task `tests --ids` at Gate to Done; full `tests` at Phase 4 and Gate 4 |
| A test still references a scenario removed from the document | Full `tests` stale check |
| A declared root does not exist yet, before any integration test is written | A warning naming the path; exit 2 only when no root exists. The task that creates a root runs its check after creating it |
| An epic designed before this change has no identifiers | Both modes fail on the first scenario line. On resume, identifiers and `Covers:` lines are added at Gate 3, before any task runs |
| Gate 4 is granted on `quality_check` alone | Red Flag in `dev-lifecycle`: "Granting Gate 4 without a passing traceability check on the same SHA" |

## 10. Testing

1. Unit tests in `test_check_bdd_traceability.py`, each with its own fixture in a temporary
   directory:
   - document validation: missing identifier, malformed shape, duplicate, `.vi.md` set mismatch,
     Vietnamese keywords recognised, tier tag after the identifier accepted, scenario lines outside
     `gherkin` fences ignored;
   - `plan`: all covered; an identifier in no task; an unknown identifier in `Covers:`; list-item and
     bold `Covers:` variants;
   - `tests`: hyphenated, snake_case and lowercase references all count; a longer digit run does not
     match (`PY-HP-010` does not cover `PY-HP-01`); `.md` files ignored; `--ids` limits the check and
     skips staleness; a stale hyphenated reference fails the full run; one missing root warns while
     the others are scanned; no existing root exits 2.
2. `scripts/verify.sh` runs the new test file and passes.
3. A smoke run of `tests` against `.devtool/epic/python_quality_provider_and_onboarding/` validates the
   document and reports 11 uncovered identifiers — the gap this change closes.
4. The quality gate is `@quality_check`, because the script and the `SKILL.md` files ship in the
   plugin. The plan follows `writing-skills` for the skill edits and `test-driven-development` for
   the script.

## 11. Risks and Dependencies

- **Name without substance.** A test can carry an identifier without asserting the behaviour. The
  script proves a mapping exists, not that it is meaningful; the spec review in
  `subagent-driven-development` and the developer's review at Gate 5 judge that.
- **Integration test cost.** Async and race scenarios are slower and more fragile as integration
  tests. Accepted: it is the developer's explicit requirement.
- **Substring collisions.** An identifier could appear in an unrelated string. The boundary rules in
  §5 make this unlikely; a false positive under-reports a gap, it never blocks.
- **Interplay with the epic handoff spec.** If
  [2026-10-15-epic-handoff-choice-design.en.md](2026-10-15-epic-handoff-choice-design.en.md) lands too,
  its packaging preflight should also run `plan`. Whichever plan lands second adds that step.

## 12. Out of Scope

- Any change to `quality_check`, its contracts, schemas or executive report, and to platform
  providers.
- Executable Gherkin, BDD runners, and a Tier D.
- `writing-plans` and other non-epic work.
- Retrofitting identifiers into archived epics.
- Verifying that a test's assertions match its scenario.
