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
