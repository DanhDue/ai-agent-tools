# Lifecycle Follow-ups Design

- **Date**: 2026-10-15
- **Status**: Approved
- **Scope**: `check_bdd_traceability.py` and its tests, `dev-designer`, `dev-implementation`,
  `dev-lifecycle`, `dev-lifecycle/references/handoff-template.md`,
  `scripts/test_lifecycle_document_contract.py`
- **Next step**: `writing-plans` (one implementation plan, no HLD)

## Table of Contents

- [1. Background](#1-background)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Items](#3-items)
- [4. Script Changes](#4-script-changes)
- [5. Skill and Template Changes](#5-skill-and-template-changes)
- [6. Amendments to Earlier Specs](#6-amendments-to-earlier-specs)
- [7. Testing](#7-testing)
- [8. Risks](#8-risks)
- [9. Out of Scope](#9-out-of-scope)

## 1. Background

Two branches landed on `main` on 2026-10-15: BDD integration traceability (merge `bde3493`) and
the epic handoff choice (merge `5b37dcc`). Their final reviews deferred eleven minor items, recorded
in project memory. Each item was re-checked against `main` before this spec; three were reproduced
against the real script, and one turned out worse than recorded:

- **B4** — `check_bdd_traceability.py tests` walks its roots with `rglob`, so ignored, vendored and
  generated files count as coverage. A single file under `node_modules/` produced
  `Result: 2/2 covered — PASS`. A stale Playwright report under `tests/e2e/` would keep a deleted
  test's identifiers "covered" and turn Gate 4 green falsely.
- **H1** — without a fetch, `git branch -r` showed nothing for an epic branch another clone had
  pushed, while `git ls-remote --heads` found it.
- **H3** — inside the epic worktree, `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` listed the
  epic's own task commit, so every receiver was told its handoff might be stale; against the base
  branch only the packaging commit appeared.

The developer approved fixing every proposed item in one patch.

## 2. Goals and Non-Goals

**Goals:**

- Remove the false PASS (B4) and the false "stale" warning (H3).
- Stop a resumed epic from duplicating a branch that exists only on a remote (H1).
- Remove avoidable friction: prose in `Covers:` lines (B1), the Python e2e root (B2), input errors
  reported as traceability failures (B3).
- Close the small text gaps B5, B6, H2, H4a, H4b and H5.

**Non-Goals:**

- New scripts, new gates, or changes to `quality_check` and its providers.
- Re-wrapping existing long lines; `dev-lifecycle` already has 54 lines over 100 columns.
- The pre-existing `validate_quality_contract.py` crash on a missing registry.
- Retrofitting epics already archived.

## 3. Items

| ID | Change | Where |
|----|--------|-------|
| B1 | Read `Covers:` identifiers by shape, ignoring prose and trailing punctuation | script |
| B2 | Python default integration roots become `tests/integration/` and `tests/e2e/` | dev-designer |
| B3 | A scenario or task file that is not valid UTF-8 is a usage error, exit 2 | script |
| B4 | List integration test files with `git ls-files`, skipping ignored files; fall back to a directory walk outside git | script |
| B5 | Say that `--roots` and `--ids` take space- or comma-separated values | dev-implementation |
| B6 | Gate 4 condition 4 names the traceability re-run | dev-lifecycle |
| H1 | Detect remote epic branches with `git ls-remote --heads` | dev-implementation |
| H2 | A queued epic is packaged as `Packaged (queued behind <epic>)` | dev-lifecycle, dev-implementation |
| H3 | The staleness check compares against the base branch; `uncommitted` when `auto_commit` is false | template |
| H4a | The retrofit commit may carry the interrupted task's status fields; say that is expected | dev-implementation |
| H4b | Re-entering Phase 2 at a task in `review` resumes its review, not its implementation | dev-implementation |
| H5 | `<N>` in the template is the task count from the preflight | dev-lifecycle |

## 4. Script Changes

All in `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`.

**B1.** `covers_of` extracts identifiers from the text after `Covers:` with the identifier shape
— `[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+`, not preceded by a letter, digit or `-`, not followed by a
letter or digit — instead of splitting on commas and whitespace. `Covers: PY-HP-01 (happy path),
PY-EC-02.` yields `PY-HP-01` and `PY-EC-02`. A well-shaped identifier that is not in the document
is still reported as unknown.

**B3.** Reading a scenario document, its Vietnamese sibling, or a task file catches
`UnicodeDecodeError` and raises the usage error with the file's path, so the run exits 2 with
`error: <path> is not valid UTF-8`. Integration test files keep their current behaviour: an
undecodable file is skipped.

**B4.** For each existing root, `integration_files` runs
`git -C <root> ls-files --cached --others --exclude-standard -z`. It keeps every listed path that
is a file and does not end in `.md`, joined to the root. When git is missing or the root is not
inside a repository, it falls back to the current `rglob` walk for that root. Tracked files and
new, unignored test files count; anything matched by `.gitignore` does not.

## 5. Skill and Template Changes

**B2 — dev-designer, Integration Test Roots bullet.** The Python default reads
`tests/integration/` and `tests/e2e/` (Python). Python's own Tier C already runs both suites, and a
root that does not exist yet only produces a warning.

**B5 — dev-implementation, Phase 4.** After the paragraph that follows the full traceability check,
add: `--roots` and `--ids` take space- or comma-separated values, so the HLD's roots line and a
task's `Covers:` line can be pasted as written.

**B6 — dev-lifecycle, Gate 4 condition 4.** "a fresh epic quality run is required before landing"
becomes "a fresh traceability check and epic quality run are required before landing".

**H1 — dev-implementation, Entry-Point Detection.** The signal
`git branch -r --list '*/epic/<epic_slug>'` becomes
`for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done`. The
explanatory sentence becomes: `git ls-remote` asks each remote directly, so an epic branch pushed
from another clone shows before any fetch; if a remote cannot be reached, say so in the
announcement and fall back to `git branch -r --list '*/epic/<epic_slug>'`.

**H2 — dev-lifecycle packaging step 4, and dev-implementation.** If the overview Status read
`Queued (backlog) — behind <epic>` before packaging, the status script is run with
`"Packaged (queued behind <epic>)"` and that line is copied into Open Notes; the `grep` still
matches because it anchors on `: Packaged`. The Handoff Choice question mentions the queue when
there is one. In dev-implementation, the two checks "if the overview Status is `Packaged`"
(Resume Procedure step 5 and Phase 1 step 4) become "if the overview Status begins with
`Packaged`". Entry-point rows are unchanged: a queued epic's `backlog` tasks still stop at row 2.

**H3 — handoff template.** The Status section's design-commit line adds "or `uncommitted` when
`auto_commit` is false". The staleness rule becomes: unless the design commit is `uncommitted`, if
`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` lists any commit besides the
`Package epic for handoff` commit, the documents changed after packaging; the documents win and
this file may be stale. Comparing against the base branch keeps the epic branch's own task commits
out of the check, and the command works from any checkout.

**H4a — dev-implementation, Resume Procedure step 4.** After the by-path staging rule, add: the
interrupted task's own status fields may ride along in that commit; that is expected.

**H4b — dev-implementation, Resume Procedure step 6.** "Enter Phase 2 at the interrupted task, or
at the first remaining task." becomes: enter Phase 2 at the interrupted task — a task at `review`
re-enters at Phase 2 step 2 and is reviewed on its existing changes; a task at `in-progress`
resumes implementation with the changes kept at Gate 3 (resume) — or at the first remaining task.

**H5 — dev-lifecycle packaging step 2.** After "fill every placeholder", add that `<N>` is the task
count the preflight printed.

**Contract test.** `scripts/test_lifecycle_document_contract.py` locks
`git ls-remote --heads` for dev-implementation and
`a fresh traceability check and epic quality run` for dev-lifecycle.

## 6. Amendments to Earlier Specs

This spec supersedes, without editing them, these parts of the earlier dated specs:

| Earlier spec | Section | Superseded by |
|--------------|---------|---------------|
| `2026-10-15-bdd-integration-traceability-design` | §5 file scanning, §6 Python default root, §7 `Covers:` parsing and exit codes | B4, B2, B1 and B3 |
| `2026-10-15-epic-handoff-choice-design` | §6 Status row and staleness rule | H3 |
| `2026-10-15-epic-handoff-choice-design` | §7 step 4, §8.2 remote-branch signal, §8.4 steps 3 and 5 | H2, H1, H4a and H4b |

## 7. Testing

1. New unit tests in `test_check_bdd_traceability.py`, written first and seen failing:
   - B1: prose and trailing punctuation on a `Covers:` line still give 2/2 covered;
   - B3: a non-UTF-8 task file and a non-UTF-8 scenario document each exit 2;
   - B4, inside a temporary git repository: a test file matched by `.gitignore` does not cover;
     an untracked, unignored test file does; a tracked test file does.

   The existing 26 tests keep passing; their temporary directories are not git repositories, so
   they exercise the fallback walk.
2. Dry runs in throwaway repositories, never in this one:
   - H1: a bare remote with an epic branch pushed from a second clone — `git branch -r` prints
     nothing and the `git ls-remote` loop prints the branch;
   - H3: after packaging, a task commit in the epic worktree — `git log <sha>..HEAD` lists it,
     `git log <sha>..<base_branch>` lists only the packaging commit.
3. Behaviour tests with fresh subagents, before and after the edits: a resume where the epic branch
   exists only on `origin` (expected: the `ls-remote` signal and row 7, not row 3), a resume of a
   task at `review` (expected: Phase 2 step 2), and packaging a queued epic (expected:
   `Packaged (queued behind <epic>)` and a note in Open Notes).
4. `scripts/verify.sh` passes. The quality gate is `scripts/verify.sh`; `@quality_check` is
   `BLOCKED` in this repository, which has no quality registry.

## 8. Risks

- **`git ls-files` changes what counts.** Tests that are ignored by `.gitignore` stop counting. That
  is the intent, but a project that ignores a real test directory by mistake will see new
  uncovered identifiers. The failure is loud and names the identifiers.
- **Network at resume.** `git ls-remote` contacts each remote. Offline, the skill says so and falls
  back to the local refs, which is no worse than today.
- **Status prefix.** Checks move from "is `Packaged`" to "begins with `Packaged`"; no other status
  value starts with that word.

## 9. Out of Scope

- Re-wrapping long lines in `dev-lifecycle` and the other skills.
- The `validate_quality_contract.py` crash on a missing registry (kit tooling defect 6).
- Deferred cosmetic items not recorded in memory: the placement of the Tier C BDD Automation
  heading, the unlinked "below" reference, and the script listed in the Stage Skills table.
