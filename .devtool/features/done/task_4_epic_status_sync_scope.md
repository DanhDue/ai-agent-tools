---
id: "task_4_epic_status_sync_scope"
status: "done"
priority: "medium"
assignee: null
epic: "principal_review"
dueDate: null
created: "2026-10-22T09:10:00Z"
modified: "2026-10-23T09:33:45Z"
completedAt: "2026-10-23T09:33:45Z"
labels: ["kanban-sync", "worktree", "packaging"]
order: "a4"
---

# Task 4: Scope Epic Status Sync to Its Own Worktrees

Epic: [principal_review](../epic/principal_review/principal_review.en.md)

## Requirement Analysis

`sync_task_status.py epic <epic_dir> <status>` rewrites the overview Status in every checkout of
the repository, including worktrees of other epics. In lyrics-sync, packaging one epic left
uncommitted Status edits inside another epic's worktree, and another session could have committed
them to the wrong epic. The Principal Review loop re-packages after every revision, so it would
repeat that side effect on every round.

The `epic` subcommand must now write only to the current checkout and to worktrees on the
`epic/<epic_slug>` branch. The `task`, `archive-epic` and `archive-done` subcommands keep
mirroring across every checkout, which is their purpose.

The file also carries 8 ruff and 3 strict-mypy findings on `main`, among them a real
`str | None` union access and two `list[str]` / `list[Path]` mix-ups. This task clears them, so its
Tier B rows prove the file clean.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/sync_task_status.py`
- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`

Read-only context:
- `skills/dev-implementation/SKILL.md` — `<epic_slug>` and the `epic/<epic_slug>` branch name
- `scripts/test_lifecycle_signals.py` — `QueuedPackagingTest` runs `sync_task_status.py epic`
- `scripts/test_verifiable_handoff.py` — runs the done gate through `sync_task_status.py`
- `.devtool/epic/principal_review/principal_review.en.md` — Module Contracts, `sync_task_status.py`

## Design Rationale

The branch, not the directory name, says which epic a worktree belongs to: worktree directories
are named after `<epic_dir>`, while branches carry `<epic_slug>`, and the two differ by
underscores and hyphens. Reading `--porcelain` output keeps the change inside the existing
`checkout_roots()` style.
`test_sync_task_status.py` carries 66 strict-mypy findings on `main`, so the Tier B rows cover
`sync_task_status.py` only.
Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `main()`, `checkout_roots()`, `find_epic_slug()`, new `parse_worktree_branches()`, new `epic_checkout_roots()`
- **Downstream Callers**: `dev-lifecycle` packaging step 4, `dev-implementation` status changes, `finishing-a-development-branch` (`Done`), `doc-implementation`, `subagent-driven-development`.
- **Cross-Platform Bridges**: none.
- **Target Test Coverage Threshold**: both new functions and the `epic` dispatch have named tests.

### BDD SCENARIOS

Covers: PRV-HP-05, PRV-FR-05

```gherkin
Scenario: [PRV-HP-05] [Tier C - Integration] epic updates the main checkout and the epic's own worktree
  Given a throwaway repository with epic "demo_epic" (slug "demo-epic") and a worktree on branch "epic/demo-epic"
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then demo_epic.en.md and demo_epic.vi.md read "Packaged" in both checkouts

Scenario: [PRV-FR-05] [Tier C - Integration] Another epic's worktree stays byte-identical and task sync still mirrors everywhere
  Given the PRV-HP-05 repository plus a worktree on branch "epic/other-epic" that also contains .devtool/epic/demo_epic/
  When sync_task_status.py epic demo_epic Packaged runs in the main checkout
  Then git status in the "epic/other-epic" worktree is empty
  When sync_task_status.py task task_1_demo in-progress runs
  Then task_1_demo reads "in-progress" in all three checkouts
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py -k EpicCheckoutRootsTests` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest scripts/test_lifecycle_signals.py` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest scripts/test_verifiable_handoff.py` | exit 0; contains "OK" | — |
| V5 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/sync_task_status.py` | exit 0 | — |
| V6 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py` | exit 0 | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_4.xml skills/dev-implementation/resources/scripts/test_sync_task_status.py scripts/test_lifecycle_signals.py` | exit 0; results build/test-results/task_4.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Clearing a ruff or mypy finding would change behaviour that an existing test asserts.

## Decisions Already Made

- **New frozen symbols** (HLD, Module Contracts):
  ```python
  def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]
  def epic_checkout_roots(epic_dir: str) -> list[Path]
  ```
- **`parse_worktree_branches`**:
  - reads `git worktree list --porcelain` output, in which entries are separated by blank lines;
  - each entry yields `(Path(<worktree>), <branch ref>)`, for example `refs/heads/epic/demo-epic`, or `None` when the entry has `detached` or no `branch` line.
- **`epic_checkout_roots`**:
  - `current = Path(git rev-parse --show-toplevel)`, and `slug = find_epic_slug(current, epic_dir) or epic_dir`;
  - the result is `current` followed by every worktree path whose branch is `f"refs/heads/epic/{slug}"`;
  - paths are compared after `resolve()`, deduplicated and kept in order.
- **`main`**: only the `epic` subcommand changes its roots, from `checkout_roots()` to `epic_checkout_roots(args.epic_dir)`. `sync_epic()`, its return value and its printed `Synchronized <n> epic docs …` line are unchanged.
- **Unchanged subcommands**: `task`, `archive-epic` and `archive-done` keep `checkout_roots()`.
- **Lint and type debt**: clear every finding `ruff check` and `mypy --strict --follow-imports=silent` report on `sync_task_status.py` without changing behaviour. On `main` at `5f91fd7` there are 8 ruff and 3 mypy findings.
- **Tests**: class `EpicCheckoutRootsTests(unittest.TestCase)` builds a throwaway repository with worktrees on `epic/demo-epic` and `epic/other-epic`, and has one `test_prv_*` method per covered scenario plus a parser test.

## Definition of Done

- Both covered scenarios have a `test_prv_*` method in `EpicCheckoutRootsTests` and pass in the JUnit report. (V2, V7)
- The existing sync, lifecycle-signal and verifiable-handoff suites pass unchanged. (V2, V3, V4, V7)
- `sync_task_status.py` reports zero ruff and strict-mypy findings. (V5, V6)

## Dependencies & Blockers

- Blocked by: none.
- Blocks [Task 5](task_5_principal_review_choice_and_acceptance.md).

## References & Rollback

- [Epic HLD](../epic/principal_review/principal_review.en.md), Module Contracts.
- Spec: [2026-10-22-principal-review-design.en.md](../epic/principal_review/2026-10-22-principal-review-design.en.md), D12 and §5.6.
- **Rollback**: revert the commit; `epic` writes to every checkout again.
