#!/usr/bin/env python3
"""Tests for integrate_branch.py, run as a CLI against real temporary git repositories.

Run: python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent / "integrate_branch.py"
# Isolate every git call from the developer's own configuration (signing, hooks, aliases).
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test Dev",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test Dev",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
LINES = "".join(f"line {n}\n" for n in range(1, 11))


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def commit(cwd: Path, path: str, content: str, message: str) -> str:
    target = cwd / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    git(cwd, "add", path)
    git(cwd, "commit", "-q", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


def edit_line(content: str, number: int, text: str) -> str:
    lines = content.splitlines(keepends=True)
    lines[number - 1] = text + "\n"
    return "".join(lines)


def integrate(cwd: Path, *args: str) -> tuple[int, dict | None, str]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args, "--format", "json"], cwd=cwd,
                            capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, data, result.stderr


class RepoTestCase(unittest.TestCase):
    """A main checkout on `develop`, optionally an `origin` bare remote, and epic worktrees."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, GIT_ENV)
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.main = self.root / "main"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "develop")
        commit(self.main, "lib/app.dart", LINES, "Initial commit")

    def add_remote(self) -> None:
        self.remote = self.root / "remote.git"
        git(self.root, "clone", "-q", "--bare", str(self.main), str(self.remote))
        git(self.main, "remote", "add", "origin", str(self.remote))
        git(self.main, "fetch", "-q", "origin")
        git(self.main, "branch", "-q", "--set-upstream-to", "origin/develop", "develop")

    def push_from_elsewhere(self, path: str, content: str, message: str) -> str:
        other = self.root / "other"
        if not other.exists():
            git(self.root, "clone", "-q", "-b", "develop", str(self.remote), str(other))
        git(other, "pull", "-q", "--ff-only")
        sha = commit(other, path, content, message)
        git(other, "push", "-q", "origin", "develop")
        return sha

    def add_epic(self, name: str = "demo") -> Path:
        worktree = self.root / f"wt-{name}"
        git(self.main, "worktree", "add", "-q", str(worktree), "-b", f"epic/{name}", "develop")
        return worktree

    def conflicting_epic(self) -> tuple[Path, str]:
        epic = self.add_epic()
        head = commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 3, "upstream line 3"), "Upstream edit")
        return epic, head


class TestSyncBase(RepoTestCase):
    def test_no_upstream_uses_local_base(self):
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual(code, 0)
        self.assertEqual(data["relation"], "local-only")

    def test_local_ahead_is_kept(self):
        self.add_remote()
        local = commit(self.main, "lib/local.dart", "local\n", "Local merge")
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual((code, data["relation"]), (0, "ahead"))
        self.assertEqual(git(self.main, "rev-parse", "develop"), local)

    def test_local_behind_fast_forwards_the_base_checkout(self):
        self.add_remote()
        pushed = self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual((code, data["relation"], data["fast_forwarded"]), (0, "behind", True))
        self.assertEqual(git(self.main, "rev-parse", "develop"), pushed)
        self.assertTrue((self.main / "lib/remote.dart").exists())

    def test_diverged_base_stops(self):
        self.add_remote()
        self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        commit(self.main, "lib/local.dart", "local\n", "Local merge")
        code, _, stderr = integrate(self.main, "sync-base")
        self.assertEqual(code, 3)
        self.assertIn("diverged", stderr)

    def test_fetch_failure_warns_and_continues(self):
        self.add_remote()
        git(self.main, "remote", "set-url", "origin", str(self.root / "missing.git"))
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual(code, 0)
        self.assertIn("fetch from origin failed", data["warnings"][0])


class TestPreflight(RepoTestCase):
    def test_noop_when_base_has_not_moved(self):
        epic = self.add_epic()
        commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "noop"))
        self.assertEqual(data["upstream_commits"], [])

    def test_reports_upstream_work_epics_overlap_and_manifests(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 8, "upstream line 8"), "Upstream edit")
        commit(self.main, ".devtool/epic/other_epic/bdd_scenarios.en.md", "# BDD\n", "Other epic")
        commit(self.main, "pubspec.yaml", "name: app\n", "Add dependency")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "clean"))
        self.assertEqual(len(data["upstream_commits"]), 3)
        self.assertEqual(data["upstream_epics"], [
            {"epic_dir": "other_epic", "bdd": ".devtool/epic/other_epic/bdd_scenarios.en.md"}])
        self.assertEqual(data["overlap_files"], ["lib/app.dart"])
        self.assertTrue(data["bootstrap_required"])

    def test_predicts_conflicts_and_tags_generated_files(self):
        epic, _ = self.conflicting_epic()
        commit(epic, "pubspec.lock", "epic: 1\n", "Lock epic")
        commit(self.main, "pubspec.lock", "upstream: 1\n", "Lock upstream")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "conflicts"))
        self.assertEqual(data["conflicts"], [{"path": "lib/app.dart", "tag": "review"},
                                             {"path": "pubspec.lock", "tag": "regenerate"}])

    def test_refuses_to_integrate_the_base_itself(self):
        code, _, stderr = integrate(self.main, "preflight")
        self.assertEqual(code, 3)
        self.assertIn("is the base", stderr)

    def test_does_not_move_a_base_that_is_behind(self):
        self.add_remote()
        epic = self.add_epic()
        before = git(self.main, "rev-parse", "develop")
        self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["relation"], data["target"]), (0, "behind", "origin/develop"))
        self.assertEqual(git(self.main, "rev-parse", "develop"), before)
        self.assertEqual(data["predicted_tier"], "clean")


class TestRebase(RepoTestCase):
    def test_refuses_a_dirty_worktree(self):
        epic = self.add_epic()
        (epic / "lib/app.dart").write_text("dirty\n")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("uncommitted", stderr)

    def test_refuses_a_branch_that_was_pushed(self):
        self.add_remote()
        epic = self.add_epic()
        git(epic, "push", "-q", "-u", "origin", "epic/demo")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("force-push", stderr)

    def test_a_local_upstream_is_not_a_push(self):
        epic = self.add_epic()
        git(epic, "branch", "-q", "--set-upstream-to", "develop")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "noop"))

    def test_refuses_a_detached_head(self):
        epic = self.add_epic()
        git(epic, "checkout", "-q", "--detach")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("detached", stderr)

    def test_noop_records_the_backup(self):
        epic = self.add_epic()
        head = commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "noop"))
        self.assertEqual(git(epic, "rev-parse", "backup/epic/demo"), head)

    def test_clean_rebase_replays_onto_the_base(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 5, "upstream line 5"), "Upstream edit")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "complete"))
        content = (epic / "lib/app.dart").read_text()
        self.assertIn("epic line 3", content)
        self.assertIn("upstream line 5", content)

    def test_conflict_stops_then_continue_completes(self):
        epic, _ = self.conflicting_epic()
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (2, "stopped"))
        self.assertEqual(data["conflicts"], [{"path": "lib/app.dart", "tag": "review"}])
        self.assertIn("Task 1", data["replaying"])
        (epic / "lib/app.dart").write_text(edit_line(LINES, 3, "epic and upstream line 3"))
        git(epic, "add", "lib/app.dart")
        code, data, _ = integrate(epic, "rebase", "--continue")
        self.assertEqual((code, data["result"]), (0, "complete"))

    def test_abort_restores_the_backup(self):
        epic, head = self.conflicting_epic()
        self.assertEqual(integrate(epic, "rebase")[0], 2)
        code, data, _ = integrate(epic, "rebase", "--abort")
        self.assertEqual((code, data["result"], data["restored_to_backup"]), (0, "aborted", True))
        self.assertEqual(git(epic, "rev-parse", "HEAD"), head)


if __name__ == "__main__":
    unittest.main()
