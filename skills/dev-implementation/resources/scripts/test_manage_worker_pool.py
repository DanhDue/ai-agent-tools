#!/usr/bin/env python3
"""Tests for manage_worker_pool.py.

Run: python3 skills/dev-implementation/resources/scripts/test_manage_worker_pool.py -v
"""
from __future__ import annotations
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from manage_worker_pool import (
    finalize_slot,
    get_slot_branch,
    get_slot_path,
    link_shared_caches,
    init_slots,
    sync_slot,
    merge_slot,
    cleanup_slots,
    get_pool_status,
)


class WorkerPoolNamingTests(unittest.TestCase):
    def test_slot_path_and_branch_generation(self):
        root = Path("/fake/repo")
        epic_dir = "logging_refactor"
        epic_slug = "logging-refactor"

        path_1 = get_slot_path(root, epic_dir, slot=1)
        path_2 = get_slot_path(root, epic_dir, slot=2)
        self.assertEqual(path_1, root / ".worktrees" / "logging_refactor-slot-1")
        self.assertEqual(path_2, root / ".worktrees" / "logging_refactor-slot-2")

        branch_1 = get_slot_branch(epic_slug, slot=1)
        branch_2 = get_slot_branch(epic_slug, slot=2)
        self.assertEqual(branch_1, "epic/logging-refactor-slot-1")
        self.assertEqual(branch_2, "epic/logging-refactor-slot-2")


class SharedCacheLinkTests(unittest.TestCase):
    def test_links_heavy_cache_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            main_wt = Path(tmp) / "main_wt"
            slot_wt = Path(tmp) / "slot_wt"
            main_wt.mkdir()
            slot_wt.mkdir()

            # Create mock node_modules and .venv
            (main_wt / "node_modules").mkdir()
            (main_wt / "node_modules" / "test_pkg.txt").write_text("pkg")
            (main_wt / ".venv").mkdir()
            (main_wt / ".venv" / "bin").mkdir()

            linked = link_shared_caches(main_wt, slot_wt)
            self.assertIn("node_modules", linked)
            self.assertIn(".venv", linked)

            # Slot should now have access to those directories
            self.assertTrue((slot_wt / "node_modules" / "test_pkg.txt").exists())
            self.assertTrue((slot_wt / ".venv" / "bin").exists())


class GitWorkerPoolLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.repo = Path(self.tmp_dir) / "test_repo"
        self.repo.mkdir()
        # Initialize bare repo and working clone
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo, check=True)

        # Initial commit on main
        (self.repo / "README.md").write_text("# Test Repo\n")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo, check=True)

        # Create epic branch worktree from main
        self.epic_dir = "sample_epic"
        self.epic_slug = "sample-epic"
        self.epic_branch = f"epic/{self.epic_slug}"

        # Main worktree
        self.main_wt = self.repo / ".worktrees" / self.epic_dir
        self.main_wt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "worktree", "add", str(self.main_wt), "-b", self.epic_branch, "main"],
            cwd=self.repo,
            check=True,
            capture_output=True,
        )

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_init_sync_merge_cleanup_pool(self):
        # 1. Init 2 slots
        res = init_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=2)
        self.assertEqual(len(res), 2)
        slot1_path = get_slot_path(self.repo, self.epic_dir, 1)
        slot2_path = get_slot_path(self.repo, self.epic_dir, 2)
        self.assertTrue(slot1_path.is_dir())
        self.assertTrue(slot2_path.is_dir())

        # Check status
        status = get_pool_status(self.repo, self.epic_dir, pool_size=2)
        self.assertEqual(len(status), 2)
        self.assertTrue(status[1]["exists"])
        self.assertTrue(status[2]["exists"])

        # 2. Simulate task execution in slot 1
        (slot1_path / "task1_file.txt").write_text("Task 1 Done\n")
        subprocess.run(["git", "add", "task1_file.txt"], cwd=slot1_path, check=True)
        subprocess.run(["git", "commit", "-m", f"[{self.epic_slug.upper()}] Task 1"], cwd=slot1_path, check=True)

        # 3. Merge slot 1 into main worktree
        merge_ok = merge_slot(self.repo, self.epic_dir, self.epic_slug, slot=1)
        self.assertTrue(merge_ok)
        self.assertTrue((self.main_wt / "task1_file.txt").exists())

        # 4. Sync slot 2 with updated epic branch
        sync_ok = sync_slot(self.repo, self.epic_dir, self.epic_slug, slot=2)
        self.assertTrue(sync_ok)
        self.assertTrue((slot2_path / "task1_file.txt").exists())

        # 5. Cleanup pool
        cleanup_res = cleanup_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=2)
        self.assertTrue(cleanup_res)
        self.assertFalse(slot1_path.exists())
        self.assertFalse(slot2_path.exists())

    def test_cli_interface_invocation(self):
        from manage_worker_pool import main
        # Test init via CLI
        cwd = os.getcwd()
        try:
            os.chdir(self.repo)
            exit_code = main(["init", "--epic-dir", self.epic_dir, "--epic-slug", self.epic_slug, "--pool-size", "2"])
            self.assertEqual(exit_code, 0)

            # Test status via CLI
            exit_code = main(["status", "--epic-dir", self.epic_dir, "--pool-size", "2"])
            self.assertEqual(exit_code, 0)

            # Test cleanup via CLI
            exit_code = main(["cleanup", "--epic-dir", self.epic_dir, "--epic-slug", self.epic_slug, "--pool-size", "2"])
            self.assertEqual(exit_code, 0)
        finally:
            os.chdir(cwd)

    def test_sync_slot_working_and_review_statuses_preserve_uncommitted_changes(self):
        import json
        from manage_worker_pool import main

        init_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=2)
        slot1_path = get_slot_path(self.repo, self.epic_dir, 1)
        hb_path = self.repo / ".devtool" / "state" / f"{self.epic_slug}.heartbeat.json"

        # 1. Start slot 1 on task_01 with default status='working'
        cwd = os.getcwd()
        try:
            os.chdir(self.main_wt)
            rc = main([
                "sync",
                "--epic-dir",
                self.epic_dir,
                "--epic-slug",
                self.epic_slug,
                "--slot",
                "1",
                "--task",
                "task_01_alpha",
                "--wave",
                "1",
            ])
            self.assertEqual(rc, 0)
            rc2 = main([
                "sync",
                "--epic-dir",
                self.epic_dir,
                "--epic-slug",
                self.epic_slug,
                "--slot",
                "2",
                "--task",
                "task_02_beta",
                "--wave",
                "1",
                "--status",
                "working",
            ])
            self.assertEqual(rc2, 0)
        finally:
            os.chdir(cwd)

        hb = json.loads(hb_path.read_text(encoding="utf-8"))
        self.assertEqual(hb["slots"]["slot-1"]["status"], "working")
        self.assertEqual(hb["slots"]["slot-1"]["task_id"], "task_01_alpha")
        self.assertEqual(hb["slots"]["slot-2"]["status"], "working")
        self.assertEqual(sorted(hb["active_tasks"]), ["task_01_alpha", "task_02_beta"])

        # 2. Simulate uncommitted edits + untracked evidence inside slot 1
        (slot1_path / "README.md").write_text("# Uncommitted Edit\n", encoding="utf-8")
        (slot1_path / "untracked_impl.py").write_text("x = 1\n", encoding="utf-8")

        # Transition slot 1 to 'review' WITHOUT --task (should inherit task_01_alpha and NOT wipe files)
        try:
            os.chdir(self.main_wt)
            rc_rev = main([
                "sync",
                "--epic-dir",
                self.epic_dir,
                "--epic-slug",
                self.epic_slug,
                "--slot",
                "1",
                "--status",
                "review",
                "--wave",
                "1",
            ])
            self.assertEqual(rc_rev, 0)
        finally:
            os.chdir(cwd)

        self.assertEqual(
            (slot1_path / "README.md").read_text(encoding="utf-8"),
            "# Uncommitted Edit\n",
        )
        self.assertTrue((slot1_path / "untracked_impl.py").is_file())

        hb_rev = json.loads(hb_path.read_text(encoding="utf-8"))
        self.assertEqual(hb_rev["slots"]["slot-1"]["status"], "review")
        self.assertEqual(hb_rev["slots"]["slot-1"]["task_id"], "task_01_alpha")
        self.assertEqual(sorted(hb_rev["active_tasks"]), ["task_01_alpha", "task_02_beta"])

        # 3. Merging slot 2 must retain slot 1 (status='review') in active_tasks
        slot2_path = get_slot_path(self.repo, self.epic_dir, 2)
        (slot2_path / "slot2_file.txt").write_text("done\n", encoding="utf-8")
        subprocess.run(["git", "add", "slot2_file.txt"], cwd=slot2_path, check=True)
        subprocess.run(["git", "commit", "-m", "Slot 2 done"], cwd=slot2_path, check=True)
        self.assertTrue(merge_slot(self.repo, self.epic_dir, self.epic_slug, slot=2, task_id="task_02_beta"))

        hb_after_merge = json.loads(hb_path.read_text(encoding="utf-8"))
        self.assertEqual(hb_after_merge["slots"]["slot-1"]["status"], "review")
        self.assertEqual(hb_after_merge["slots"]["slot-2"]["status"], "idle")
        self.assertEqual(hb_after_merge["active_tasks"], ["task_01_alpha"])

        # 4. --no-reset allows returning slot 1 from review -> working without wiping uncommitted fixes
        self.assertTrue(
            sync_slot(
                self.repo,
                self.epic_dir,
                self.epic_slug,
                slot=1,
                status="working",
                reset_worktree=False,
            )
        )
        self.assertTrue((slot1_path / "untracked_impl.py").is_file())
        hb_back = json.loads(hb_path.read_text(encoding="utf-8"))
        self.assertEqual(hb_back["slots"]["slot-1"]["status"], "working")
        self.assertEqual(hb_back["slots"]["slot-1"]["task_id"], "task_01_alpha")

        # 5. status='idle' with --no-reset clears task_id and preserves uncommitted worktree files
        try:
            os.chdir(self.main_wt)
            rc_idle_preserve = main([
                "sync",
                "--epic-dir",
                self.epic_dir,
                "--epic-slug",
                self.epic_slug,
                "--slot",
                "1",
                "--status",
                "idle",
                "--no-reset",
            ])
            self.assertEqual(rc_idle_preserve, 0)
        finally:
            os.chdir(cwd)
        self.assertTrue((slot1_path / "untracked_impl.py").is_file())
        hb_idle = json.loads(hb_path.read_text(encoding="utf-8"))
        self.assertEqual(hb_idle["slots"]["slot-1"]["status"], "idle")
        self.assertIsNone(hb_idle["slots"]["slot-1"]["task_id"])
        self.assertEqual(hb_idle["active_tasks"], [])

        # 6. status='idle' with default reset cleans slot worktree back to epic branch
        self.assertTrue(
            sync_slot(
                self.repo,
                self.epic_dir,
                self.epic_slug,
                slot=1,
                status="idle",
            )
        )
        self.assertFalse((slot1_path / "untracked_impl.py").exists())

        with self.assertRaises(ValueError):
            sync_slot(self.repo, self.epic_dir, self.epic_slug, slot=1, status="invalid")

    def test_finalize_slot_handles_cache_symlinks_and_preserves_tracked_audit_and_contracts(
        self,
    ) -> None:
        # Track shared-contracts symlink and an existing review_audit_notes.jsonl;
        # gitignore .venv while keeping node_modules unignored to cover both symlink paths.
        (self.main_wt / ".gitignore").write_text(
            ".venv\n.venv/\n.worktrees/\n.devtool/state/\n.devtool/logs/\n",
            encoding="utf-8",
        )
        contracts_target = Path(self.tmp_dir) / "contracts_hub"
        contracts_target.mkdir()
        (contracts_target / "api_contract.md").write_text("# Contract\n", encoding="utf-8")
        (self.main_wt / "shared-contracts").symlink_to(contracts_target)

        epic_root = self.main_wt / ".devtool" / "epic" / self.epic_dir
        features_dir = self.main_wt / ".devtool" / "features"
        epic_root.mkdir(parents=True, exist_ok=True)
        features_dir.mkdir(parents=True, exist_ok=True)
        tracked_audit = epic_root / "review_audit_notes.jsonl"
        tracked_audit.write_text('{"task_id": "task_00_prior"}\n', encoding="utf-8")
        (epic_root / f"{self.epic_dir}.md").write_text(
            f"# {self.epic_dir}\n\nIntegration test roots: tests\n", encoding="utf-8"
        )
        (epic_root / "bdd_scenarios.md").write_text(
            "```gherkin\nScenario: [SC-01] Demo\n```\n", encoding="utf-8"
        )
        task_id = "task_01_stage"
        task_md = (
            f'---\nid: "{task_id}"\nstatus: "in-progress"\nepic: "{self.epic_slug}"\n'
            'completedAt: null\nmodified: "2026-11-26T00:00:00Z"\n---\n\n'
            f"# {task_id}\n\nCovers: SC-01\n\n## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n|---|---|---|---|---|\n"
            "| V1 | GREEN | `true` | exit 0 | — |\n"
        )
        (epic_root / f"{task_id}.md").write_text(task_md, encoding="utf-8")
        (features_dir / f"{task_id}.md").write_text(task_md, encoding="utf-8")
        (self.main_wt / "tests").mkdir(exist_ok=True)
        (self.main_wt / "tests" / f"test_{task_id}.py").write_text(
            "# Covers SC-01\ndef test_ok():\n    assert True\n", encoding="utf-8"
        )
        scripts_stub = self.main_wt / "skills" / "dev-implementation" / "resources" / "scripts"
        scripts_stub.mkdir(parents=True, exist_ok=True)
        (scripts_stub / "run_task_checks.py").write_text(
            "import sys\nprint('done gate: PASS')\nsys.exit(0)\n", encoding="utf-8"
        )
        (scripts_stub / "check_bdd_traceability.py").write_text(
            "import sys\nprint('PASS')\nsys.exit(0)\n", encoding="utf-8"
        )
        (scripts_stub / "sync_task_status.py").write_text(
            "import sys\nsys.exit(0)\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.main_wt, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "Seed tracked symlinks and audit log"],
            cwd=self.main_wt,
            check=True,
        )

        # Create cache directories in main_wt so init_slots symlinks both into slot 1
        (self.main_wt / ".venv" / "bin").mkdir(parents=True)
        (self.main_wt / "node_modules" / "pkg").mkdir(parents=True)
        init_slots(self.repo, self.epic_dir, self.epic_slug, pool_size=1)

        slot1 = get_slot_path(self.repo, self.epic_dir, 1)
        self.assertTrue((slot1 / ".venv").is_symlink())
        self.assertTrue((slot1 / "node_modules").is_symlink())
        self.assertTrue((slot1 / "shared-contracts").is_symlink())

        # Make a code edit, mutate tracked audit log, and add an untracked audit file
        (slot1 / "feature.py").write_text("RESULT = 1\n", encoding="utf-8")
        (slot1 / ".devtool" / "epic" / self.epic_dir / "review_audit_notes.jsonl").write_text(
            '{"stale": true}\n', encoding="utf-8"
        )
        (
            slot1 / ".devtool" / "epic" / self.epic_dir / "review_audit_notes_extra.jsonl"
        ).write_text('{"extra": true}\n', encoding="utf-8")

        report = finalize_slot(
            self.repo,
            self.epic_dir,
            self.epic_slug,
            1,
            task_id,
            mode="pass1-approved",
        )
        self.assertTrue(report.get("ok"), report)
        self.assertTrue(report.get("merged"), report)

        committed = subprocess.run(
            ["git", "show", "--pretty=format:", "--name-only", "HEAD"],
            cwd=self.main_wt,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        self.assertIn("feature.py", committed)
        self.assertNotIn(".venv", committed)
        self.assertNotIn("node_modules", committed)
        self.assertFalse(any("review_audit_notes" in item for item in committed))

        # Tracked review_audit_notes.jsonl is preserved unmodified, not deleted
        self.assertEqual(
            tracked_audit.read_text(encoding="utf-8"),
            '{"task_id": "task_00_prior"}\n',
        )
        sc_tree = subprocess.run(
            ["git", "ls-tree", "HEAD", "shared-contracts"],
            cwd=self.main_wt,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertTrue(sc_tree.startswith("120000 "), sc_tree)
        self.assertTrue((slot1 / ".venv").is_symlink())
        self.assertTrue((slot1 / "node_modules").is_symlink())
        self.assertTrue((slot1 / "shared-contracts").is_symlink())


if __name__ == "__main__":
    unittest.main()
