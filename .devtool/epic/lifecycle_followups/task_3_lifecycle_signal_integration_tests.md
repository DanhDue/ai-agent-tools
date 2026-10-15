---
id: "task_3_lifecycle_signal_integration_tests"
status: "done"
priority: "high"
assignee: null
epic: "lifecycle-followups"
dueDate: null
created: "2026-10-15T15:57:47Z"
modified: "2026-10-15T16:23:37Z"
completedAt: "2026-10-15T16:23:37Z"
labels: ["tests", "integration"]
order: "a3"
---

# Task 3: Lifecycle signal integration tests

Epic: [lifecycle-followups](lifecycle_followups.en.md)

## Requirement Analysis

The final Tier C task. A new `scripts/test_lifecycle_signals.py` builds throwaway git repositories and
runs the exact commands the skills prescribe, read from the skill text itself: the `git ls-remote`
remote-branch loop, its failure on an unreachable remote, the handoff template's staleness command, and
the packaging `grep` on a queued epic's Status. `scripts/verify.sh` runs it.

### Exact changes

Create `scripts/test_lifecycle_signals.py`:

```python
#!/usr/bin/env python3
"""Integration tests for the git signals the lifecycle skills prescribe.

Each test builds throwaway git repositories, reads the command from the skill text itself, and runs it,
so a skill whose command stops working fails here rather than in a user's session.

Run: python3 -m unittest scripts/test_lifecycle_signals.py
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMPLEMENTATION = (ROOT / "skills/dev-implementation/SKILL.md").read_text()
LIFECYCLE = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text()
TEMPLATE = (ROOT / "skills/dev-lifecycle/references/handoff-template.md").read_text()
SYNC = ROOT / "skills/dev-implementation/resources/scripts/sync_task_status.py"


def skill_line(text: str, prefix: str) -> str:
    """The first line of a skill that starts with prefix; the test fails if the skill lost it."""
    for line in text.splitlines():
        if line.startswith(prefix):
            return line
    raise AssertionError(f"no line starting with {prefix!r}")


def run(cwd: Path, script: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", "-c", script], cwd=cwd, capture_output=True, text=True)


def git(cwd: Path, *args: str) -> str:
    done = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", *args],
                          cwd=cwd, capture_output=True, text=True, check=True)
    return done.stdout


class SignalCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.tmp = Path(directory.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "base")


class RemoteBranchSignalTest(SignalCase):
    def loop(self) -> str:
        line = skill_line(IMPLEMENTATION, "for remote in $(git remote); do git ls-remote --heads")
        return line.replace("<epic_slug>", "todo-export")

    def test_lf_st_01_branch_pushed_from_another_clone_is_seen_before_any_fetch(self) -> None:
        origin = self.tmp / "origin.git"
        git(self.tmp, "init", "-q", "--bare", str(origin))
        git(self.repo, "remote", "add", "origin", str(origin))
        git(self.repo, "push", "-q", "origin", "main")
        other = self.tmp / "other"
        git(self.tmp, "clone", "-q", str(origin), str(other))
        git(other, "checkout", "-q", "-b", "epic/todo-export")
        git(other, "commit", "-q", "--allow-empty", "-m", "task on another machine")
        git(other, "push", "-q", "origin", "epic/todo-export")
        self.assertEqual(git(self.repo, "branch", "-r", "--list", "*/epic/todo-export"), "")
        found = run(self.repo, self.loop())
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertIn("refs/heads/epic/todo-export", found.stdout)

    def test_lf_fr_03_unreachable_remote_fails_and_the_skill_names_the_fallback(self) -> None:
        git(self.repo, "remote", "add", "origin", str(self.tmp / "missing.git"))
        found = run(self.repo, self.loop())
        self.assertNotEqual(found.returncode, 0)
        self.assertIn("fall back to `git branch -r --list '*/epic/<epic_slug>'`", IMPLEMENTATION)


class StalenessCheckTest(SignalCase):
    def test_lf_st_02_staleness_check_ignores_the_epic_branchs_task_commits(self) -> None:
        check = re.search(r"`(git log <sha>\.\.<base_branch> -- \.devtool/epic/<epic_dir>)`", TEMPLATE)
        self.assertIsNotNone(check, "the template lost its staleness command")
        epic = self.repo / ".devtool/epic/todo_export"
        epic.mkdir(parents=True)
        (epic / "task_1_export_core.md").write_text('---\nstatus: "todo"\n---\n')
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "[TODO_EXPORT] Generate epic and task breakdown")
        sha = git(self.repo, "rev-parse", "HEAD").strip()
        (epic / "handoff.md").write_text("# Handoff: todo-export\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "[TODO_EXPORT] Package epic for handoff")
        worktree = self.repo / ".worktrees/todo_export"
        git(self.repo, "worktree", "add", "-q", str(worktree), "-b", "epic/todo-export", "main")
        task = worktree / ".devtool/epic/todo_export/task_1_export_core.md"
        task.write_text('---\nstatus: "done"\n---\n')
        git(worktree, "commit", "-q", "-am", "[TODO_EXPORT] Export core")
        command = (check.group(1).replace("<sha>", sha).replace("<base_branch>", "main")
                   .replace("<epic_dir>", "todo_export"))
        listed = run(worktree, command.replace(" -- ", " --format=%s -- ", 1))
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual(listed.stdout.split("\n")[:-1], ["[TODO_EXPORT] Package epic for handoff"])


class QueuedPackagingTest(SignalCase):
    def test_lf_st_03_queued_epic_keeps_its_queue_and_the_grep_still_matches(self) -> None:
        self.assertIn('`"Packaged (queued behind <epic>)"`', LIFECYCLE)
        grep = skill_line(LIFECYCLE, "   grep -n -E '^- ").strip().rstrip("\\").strip()
        epic = self.repo / ".devtool/epic/todo_export"
        epic.mkdir(parents=True)
        (epic / "todo_export.en.md").write_text(
            "# Epic\n\n- **Status**: Queued (backlog) — behind logging-refactor\n")
        (epic / "todo_export.vi.md").write_text(
            "# Epic\n\n- **Trạng thái**: Queued (backlog) — behind logging-refactor\n")
        synced = subprocess.run(["python3", str(SYNC), "epic", "todo_export",
                                 "Packaged (queued behind logging-refactor)"],
                                cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(synced.returncode, 0, synced.stderr)
        paths = " ".join(f".devtool/epic/todo_export/todo_export.{lang}.md" for lang in ("en", "vi"))
        matched = run(self.repo, f"{grep} {paths}")
        self.assertEqual(matched.returncode, 0, matched.stderr)
        self.assertEqual(len(matched.stdout.splitlines()), 2)
        self.assertIn("Packaged (queued behind logging-refactor)", matched.stdout)


if __name__ == "__main__":
    unittest.main()
```

Then wire it into `scripts/verify.sh`:

1. `scripts/verify.sh` (T3) — replace the current text:

```bash
python3 scripts/test_lifecycle_document_contract.py || FAILED=1
```

with:

```bash
python3 scripts/test_lifecycle_document_contract.py || FAILED=1
python3 -m unittest scripts/test_lifecycle_signals.py || FAILED=1
```

Run before Task 2's text changes, these four tests fail (`FAILED (failures=4)`); after them, all four
pass and `scripts/verify.sh` prints `PASS — safe to publish`.

## Relevant Files & Context Pointers

- `scripts/test_lifecycle_signals.py` (new)
- `scripts/verify.sh` — step 11
- `skills/dev-implementation/SKILL.md`, `skills/dev-lifecycle/SKILL.md`,
  `skills/dev-lifecycle/references/handoff-template.md` — read by the tests
- `skills/dev-implementation/resources/scripts/sync_task_status.py` — run by `LF-ST-03`

## Design Rationale

- Reading each command from the skill text makes the test fail when the skill's command changes, not
  only when git does.
- Remotes are local bare repositories and the unreachable remote is a missing path: real git, no network.
- Applicable skills: `test-driven-development`, `verification-before-completion`.

## Impact Analysis & Blast Radius

- **New file only**, plus one line in `scripts/verify.sh`.
- **Runtime**: about half a second; four temporary repositories per run.

## BDD Scenarios & Acceptance Criteria

### BDD SCENARIOS

Covers: LF-ST-01, LF-ST-02, LF-ST-03, LF-FR-03

```gherkin
Feature: lifecycle follow-ups

  Scenario: [LF-ST-01] [Tier C - Integration] An epic branch pushed from another clone is visible before any fetch
    Given a remote that holds "epic/todo-export", pushed from another clone
    And a local repository that has not fetched since
    When the remote-branch signal of Entry-Point Detection runs
    Then "git branch -r" shows nothing
    And the "git ls-remote --heads" loop prints "refs/heads/epic/todo-export"

  Scenario: [LF-ST-02] [Tier C - Integration] The staleness check ignores the epic branch's own task commits
    Given an epic packaged at design commit S on the base branch
    And a task commit on the epic branch that changes the epic's task mirror
    When the template's check runs "git log S..<base_branch> -- .devtool/epic/<epic_dir>"
    Then only the "Package epic for handoff" commit is listed

  Scenario: [LF-ST-03] [Tier C - Integration] A queued epic keeps its queue when packaged
    Given an epic whose overview Status reads "Queued (backlog) — behind logging-refactor"
    When it is packaged with the Status "Packaged (queued behind logging-refactor)"
    Then the packaging grep finds that Status in both overview variants

  Scenario: [LF-FR-03] [Tier C - Integration] An unreachable remote falls back to remote-tracking refs
    Given a repository whose remote URL cannot be reached
    When the "git ls-remote --heads" loop runs
    Then it exits non-zero
    And the skill text tells the agent to say so and fall back to "git branch -r"
```

## Test & Verification Checklist

- [ ] **RED/GREEN**: `python3 -W error -m unittest scripts/test_lifecycle_signals.py` prints `Ran 4 tests` and `OK`.
- [ ] **Tier C**: the epic's full check —
  `python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests --scenarios .devtool/epic/lifecycle_followups/bdd_scenarios.en.md --roots skills/dev-implementation/resources/scripts/, scripts/`
  — prints `Result: 17/17 covered — PASS`.
- [ ] `scripts/verify.sh` prints `PASS — safe to publish`.

## Definition of Done

All four identifiers are covered by passing `test_lf_*` tests, the full traceability check reports
17/17, `scripts/verify.sh` passes, and the task lands as one commit
`[LIFECYCLE_FOLLOWUPS] Lifecycle signal integration tests` with no trailer.

## Dependencies & Blockers

- Blocked by [Task 2](task_2_skill_and_template_text.md)

## References & Rollback

- Spec: `.devtool/epic/lifecycle_followups/2026-10-15-lifecycle-followups-design.en.md` §7
- Rollback: revert this task's commit; nothing else depends on the new test file.
