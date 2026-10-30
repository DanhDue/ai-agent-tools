#!/usr/bin/env python3
"""
Unit and integration tests for scripts/resume_context.py.
Covers BDD scenarios:
- CMM-HP-01: Two-Tier Context Harvesting, Multi-Epic Isolation, and Feature Compaction
- CMM-EC-01: Enforcing the 20-Line Ceiling on Per-Epic State Snapshots
- CMM-EC-02: Worktree-Aware Routing From Nested .worktrees/<epic_dir> Checkout
- CMM-EC-03: Kanban Task Progress Calculation Across Active and Done Directories
- CMM-ST-01: Tri-Role Persona Governance Banners and 4-Scenario Handoff Prompt Emission
- CMM-AR-01: Exclusive File Locking Prevents Interleaved Writes Across Parallel Agents
- CMM-FR-01: Automatic Migration of Legacy Flat assistant_state.md and activity_stream.log
"""

import concurrent.futures
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Target script under test
REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "resume_context.py"


class TestResumeContext(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)
        # Create a sample primary repo inside workspace
        self.repo_dir = self.workspace / "ai-agent-tools"
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        # Initial git init in repo
        subprocess.run(["git", "init", "-b", "main"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_dir, capture_output=True, check=True)
        (self.repo_dir / "README.md").write_text("# Test Repo\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.repo_dir, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_dir, capture_output=True, check=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cli(self, args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        target_cwd = cwd or self.repo_dir
        cmd = [sys.executable, str(SCRIPT_PATH)] + args
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace)
        return subprocess.run(cmd, cwd=target_cwd, capture_output=True, text=True, env=env, check=False)

    def test_cmm_hp_01_multi_epic_state_log_and_complete_isolation(self) -> None:
        """[CMM-HP-01] Two-Tier Context Harvesting, Multi-Epic Isolation, and Feature Compaction."""
        # 1. Record state and logs for epic-alpha and epic-beta
        res = self.run_cli([
            "--state", "--epic", "epic-alpha",
            "--decisions", "Alpha decision 1",
            "--status", "in-progress",
            "--next", "Next alpha step",
        ])
        self.assertEqual(res.returncode, 0, f"stdout: {res.stdout}, stderr: {res.stderr}")

        res = self.run_cli([
            "--log", "--epic", "epic-alpha",
            "--task", "task_01",
            "--request", "Implement alpha engine",
            "--action", "Created alpha.py",
            "--note", "None",
        ])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        res = self.run_cli([
            "--state", "--epic", "epic-beta",
            "--decisions", "Beta decision 1",
            "--status", "todo",
            "--next", "Next beta step",
        ])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        res = self.run_cli([
            "--log", "--epic", "epic-beta",
            "--task", "task_02",
            "--request", "Implement beta feature",
            "--action", "Created beta.py",
            "--note", "None",
        ])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        # 2. Harvest context - should print 6 canonical sections and include both epics
        harvest = self.run_cli([])
        self.assertEqual(harvest.returncode, 0)
        out = harvest.stdout
        self.assertIn("0. PROJECT ARCHITECTURAL LEDGER", out)
        self.assertIn("1. ACTIVE EPIC STATE", out)
        self.assertIn("2. RECENT PROGRAMMER ACTIVITY", out)
        self.assertIn("3. GIT WORKING TREE", out)
        self.assertIn("4. OPEN CONTRACT GAPS & RFCS", out)
        self.assertIn("5. ACTIVE TASKS", out)
        self.assertIn("epic-alpha", out)
        self.assertIn("epic-beta", out)

        # 3. Complete epic-alpha
        complete_res = self.run_cli(["--complete", "epic-alpha", "Delivered alpha engine"])
        self.assertEqual(complete_res.returncode, 0, f"stderr: {complete_res.stderr}")

        # Verify PROJECT_LEDGER.md has milestone
        ledger_file = self.repo_dir / ".devtool" / "PROJECT_LEDGER.md"
        self.assertTrue(ledger_file.exists())
        ledger_text = ledger_file.read_text(encoding="utf-8")
        self.assertIn("`epic-alpha`**: Delivered alpha engine", ledger_text)

        # Verify epic-alpha state and log are archived
        archive_dir = self.repo_dir / ".devtool" / "archive"
        self.assertTrue(archive_dir.exists())
        archived_states = list(archive_dir.glob("*epic-alpha*"))
        self.assertGreater(len(archived_states), 0)

        # epic-alpha should no longer be active in state/ or logs/
        self.assertFalse((self.repo_dir / ".devtool" / "state" / "epic-alpha.md").exists())
        self.assertFalse((self.repo_dir / ".devtool" / "logs" / "activity_epic-alpha.log").exists())

        # epic-beta state and log MUST remain active
        self.assertTrue((self.repo_dir / ".devtool" / "state" / "epic-beta.md").exists())
        self.assertTrue((self.repo_dir / ".devtool" / "logs" / "activity_epic-beta.log").exists())

        # Rollup files should still contain epic-beta but not active epic-alpha
        assistant_state = (self.repo_dir / ".devtool" / "assistant_state.md").read_text(encoding="utf-8")
        self.assertIn("epic-beta", assistant_state)
        self.assertNotIn("Active Epic: epic-alpha", assistant_state)

    def test_cmm_ec_01_snapshot_20_line_cap(self) -> None:
        """[CMM-EC-01] Enforcing the 20-Line Ceiling on Per-Epic State Snapshots."""
        long_decisions = "\n".join([f"- Decision {i}: Detailed architectural rationale and boundary constraint" for i in range(20)])
        long_prompt = "Custom developer instruction note line 1\nCustom line 2\nCustom line 3\nCustom line 4\nCustom line 5"
        res = self.run_cli([
            "--state", "--epic", "context_memory_management",
            "--decisions", long_decisions,
            "--status", "Stage 3 dev-implementation (in-progress)",
            "--next", "Execute task_01 with strict TDD",
            "--prompt", long_prompt,
        ])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        state_file = self.repo_dir / ".devtool" / "state" / "context_memory_management.md"
        self.assertTrue(state_file.exists())
        lines = state_file.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), 20, f"State file exceeded 20 lines (has {len(lines)} lines):\n" + "\n".join(lines))

        content = state_file.read_text(encoding="utf-8")
        self.assertIn("Active Epic:", content)
        self.assertIn("Recent Decisions Locked:", content)
        self.assertIn("Repo/Task Status:", content)
        self.assertIn("Next Immediate Step:", content)

    def test_cmm_ec_02_worktree_routing(self) -> None:
        """[CMM-EC-02] Worktree-Aware Routing From Nested .worktrees/<epic_dir> Checkout."""
        wt_dir = self.repo_dir / ".worktrees" / "context_memory_management"
        subprocess.run(
            ["git", "worktree", "add", str(wt_dir), "-b", "epic/context_memory_management", "main"],
            cwd=self.repo_dir,
            capture_output=True,
            check=True,
        )

        # Run --state and --log from inside worktree without --repo and without --epic
        res_state = self.run_cli(
            ["--state", "--decisions", "Worktree decision", "--next", "Implement task"],
            cwd=wt_dir,
        )
        self.assertEqual(res_state.returncode, 0, f"stderr: {res_state.stderr}")

        res_log = self.run_cli(
            ["--log", "--task", "task_01", "--request", "Worktree task", "--action", "Code in WT", "--note", "None"],
            cwd=wt_dir,
        )
        self.assertEqual(res_log.returncode, 0, f"stderr: {res_log.stderr}")

        # The files must be written in primary repo's .devtool/, NOT in the ephemeral worktree .devtool/
        primary_state = self.repo_dir / ".devtool" / "state" / "context_memory_management.md"
        primary_log = self.repo_dir / ".devtool" / "logs" / "activity_context_memory_management.log"
        self.assertTrue(primary_state.exists(), "State file was not routed to primary repo root")
        self.assertTrue(primary_log.exists(), "Log file was not routed to primary repo root")
        self.assertFalse((wt_dir / ".devtool" / "state").exists(), "State directory was incorrectly created in worktree")

    def test_cmm_ec_03_kanban_task_progress(self) -> None:
        """[CMM-EC-03] Kanban Task Progress Calculation Across Active and Done Directories."""
        features_dir = self.repo_dir / ".devtool" / "features"
        done_dir = features_dir / "done"
        features_dir.mkdir(parents=True, exist_ok=True)
        done_dir.mkdir(parents=True, exist_ok=True)

        # Create 2 active tasks
        (features_dir / "task_01_todo.md").write_text(
            "---\nid: task_01\nstatus: todo\nepic: context_memory_management\n---\n# Task 1\n",
            encoding="utf-8",
        )
        (features_dir / "task_02_inp.md").write_text(
            "---\nid: task_02\nstatus: in-progress\nepic: context_memory_management\n---\n# Task 2\n",
            encoding="utf-8",
        )

        # Create 3 done tasks
        for i in (3, 4, 5):
            (done_dir / f"task_{i:02d}_done.md").write_text(
                f"---\nid: task_{i:02d}\nstatus: done\nepic: context_memory_management\n---\n# Task {i}\n",
                encoding="utf-8",
            )

        harvest = self.run_cli(["--epic", "context_memory_management"])
        self.assertEqual(harvest.returncode, 0)
        out = harvest.stdout
        self.assertIn("3/5 done", out)

    def test_cmm_st_01_tri_role_banners_and_emit_prompts(self) -> None:
        """[CMM-ST-01] Tri-Role Persona Governance Banners and 4-Scenario Handoff Prompt Emission."""
        # 1. --role assistant banner
        res_asst = self.run_cli(["--role", "assistant"])
        self.assertEqual(res_asst.returncode, 0)
        self.assertIn("[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]", res_asst.stdout)
        self.assertIn("NO IMPLEMENTATION", res_asst.stdout)

        # 2. --role programmer banner
        res_prog = self.run_cli(["--role", "programmer"])
        self.assertEqual(res_prog.returncode, 0)
        self.assertIn("[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]", res_prog.stdout)
        self.assertIn("TDD", res_prog.stdout)

        # 3. Aliases --role implementer and --role worker
        res_impl = self.run_cli(["--role", "implementer"])
        self.assertEqual(res_impl.returncode, 0)
        self.assertIn("[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]", res_impl.stdout)

        res_work = self.run_cli(["--role", "worker"])
        self.assertEqual(res_work.returncode, 0)
        self.assertIn("[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]", res_work.stdout)

        # 4. --emit-prompt modes
        modes = ["principal-review", "implement", "cross-review", "finish", "assistant"]
        for mode in modes:
            res_mode = self.run_cli(["--emit-prompt", mode, "--epic", "context_memory_management"])
            self.assertEqual(res_mode.returncode, 0, f"Mode {mode} failed with: {res_mode.stderr}")
            self.assertIn("context_memory_management", res_mode.stdout)
            self.assertTrue(
                "[PERSONA: AI ASSISTANT" in res_mode.stdout or "[PERSONA: AI PROGRAMMER" in res_mode.stdout,
                f"Mode {mode} output missing persona banner: {res_mode.stdout}",
            )

    def test_cmm_ar_01_concurrent_flock(self) -> None:
        """[CMM-AR-01] Exclusive File Locking Prevents Interleaved Writes Across Parallel Agents."""
        iterations = 10

        def worker_log(idx: int, epic: str) -> int:
            proc = self.run_cli([
                "--log", "--epic", epic,
                "--task", f"task_{idx}",
                "--request", f"Concurrent request {idx}",
                "--action", f"Concurrent action {idx}",
                "--note", f"Note {idx}",
            ])
            return proc.returncode

        def worker_state(idx: int, epic: str) -> int:
            proc = self.run_cli([
                "--state", "--epic", epic,
                "--decisions", f"Concurrent decision {idx}",
                "--status", "in-progress",
                "--next", f"Next {idx}",
            ])
            return proc.returncode

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i in range(iterations):
                epic = "epic-alpha" if i % 2 == 0 else "epic-beta"
                futures.append(executor.submit(worker_log, i, epic))
                futures.append(executor.submit(worker_state, i, epic))

            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        self.assertTrue(all(r == 0 for r in results), f"Some concurrent workers failed: {results}")

        # Check log lines count
        alpha_log = self.repo_dir / ".devtool" / "logs" / "activity_epic-alpha.log"
        beta_log = self.repo_dir / ".devtool" / "logs" / "activity_epic-beta.log"
        self.assertTrue(alpha_log.exists())
        self.assertTrue(beta_log.exists())

        alpha_lines = [l for l in alpha_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        beta_lines = [l for l in beta_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(alpha_lines), iterations // 2)
        self.assertEqual(len(beta_lines), iterations // 2)

    def test_cmm_fr_01_legacy_migration(self) -> None:
        """[CMM-FR-01] Automatic Migration of Legacy Flat assistant_state.md and activity_stream.log."""
        devtool_dir = self.repo_dir / ".devtool"
        devtool_dir.mkdir(parents=True, exist_ok=True)
        legacy_state = devtool_dir / "assistant_state.md"
        legacy_log = devtool_dir / "activity_stream.log"
        legacy_state.write_text("Legacy state info before partitioning\n", encoding="utf-8")
        legacy_log.write_text("[2026-10-29 10:00] [ai-agent-tools/legacy] Legacy log line 1\n", encoding="utf-8")

        # Running harvest should trigger migration to state/general.md and logs/activity_general.log
        harvest = self.run_cli([])
        self.assertEqual(harvest.returncode, 0, f"stderr: {harvest.stderr}")

        migrated_state = devtool_dir / "state" / "general.md"
        migrated_log = devtool_dir / "logs" / "activity_general.log"
        self.assertTrue(migrated_state.exists())
        self.assertTrue(migrated_log.exists())
        self.assertIn("Legacy state info", migrated_state.read_text(encoding="utf-8"))
        self.assertIn("Legacy log line 1", migrated_log.read_text(encoding="utf-8"))

    def test_cmm_hp_02_zshrc_symlinks_history_and_aliases(self) -> None:
        """[CMM-HP-02] Multi-Profile Zshrc Environment, Shared Terminal History, and Alias Synchronization."""
        simulated_home = self.workspace / "fake_home"
        simulated_home.mkdir(parents=True, exist_ok=True)
        zshrc_file = simulated_home / ".zshrc"
        initial_zshrc = """# Sample .zshrc
export ZSH="$HOME/.oh-my-zsh"
source $ZSH/oh-my-zsh.sh

ag_run() {
    sync_items=(Documents Desktop)
    echo "Running ag"
}
"""
        zshrc_file.write_text(initial_zshrc, encoding="utf-8")
        sim_ws_root = simulated_home / "AllProjects"
        sim_ws_root.mkdir(parents=True, exist_ok=True)

        # Create two profile directories
        profiles_dir = simulated_home / "antigravity_homes"
        p1 = profiles_dir / "profile_one"
        p2 = profiles_dir / "profile_two"
        p1.mkdir(parents=True, exist_ok=True)
        p2.mkdir(parents=True, exist_ok=True)
        (p1 / ".zsh_history").write_text("cmd_p1_1\ncmd_p1_2\n", encoding="utf-8")

        # Run CLI --sync-zshrc
        res = self.run_cli([
            "--sync-zshrc",
            "--real-home", str(simulated_home),
            "--workspace-root", str(sim_ws_root),
        ])
        self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        zshrc_content = zshrc_file.read_text(encoding="utf-8")
        self.assertIn("REAL_HOME", zshrc_content)
        self.assertIn("WORKSPACE_ROOT", zshrc_content)
        self.assertIn('HISTFILE="$REAL_HOME/.zsh_history"', zshrc_content)
        self.assertIn("SHARE_HISTORY", zshrc_content)
        self.assertIn("INC_APPEND_HISTORY", zshrc_content)
        self.assertIn("alias resume=", zshrc_content)
        self.assertIn("alias save-context=", zshrc_content)
        self.assertIn("AllProjects", zshrc_content)
        self.assertIn("Projects", zshrc_content)
        self.assertIn(".zsh_history", zshrc_content)

        # Check symlinks
        projects_link = simulated_home / "Projects"
        self.assertTrue(projects_link.is_symlink())
        self.assertEqual(projects_link.resolve(), sim_ws_root.resolve())

        self.assertTrue((p1 / "Projects").is_symlink())
        self.assertTrue((p1 / "AllProjects").is_symlink())
        self.assertTrue((p1 / ".zsh_history").is_symlink())
        self.assertEqual((p1 / ".zsh_history").resolve(), (simulated_home / ".zsh_history").resolve())

        # Check history merged
        shared_history = (simulated_home / ".zsh_history").read_text(encoding="utf-8")
        self.assertIn("cmd_p1_1", shared_history)
        self.assertIn("cmd_p1_2", shared_history)

    def test_cmm_ar_02_idempotent_zsh_history_merge(self) -> None:
        """[CMM-AR-02] Idempotent Zsh History Merge Preserves Chronological Commands Without Duplicating Symlinks."""
        simulated_home = self.workspace / "fake_home_idempotent"
        simulated_home.mkdir(parents=True, exist_ok=True)
        zshrc_file = simulated_home / ".zshrc"
        zshrc_file.write_text("# basic zshrc\n", encoding="utf-8")
        sim_ws_root = simulated_home / "AllProjects"
        sim_ws_root.mkdir(parents=True, exist_ok=True)

        profiles_dir = simulated_home / "antigravity_homes"
        p1 = profiles_dir / "p1"
        p2 = profiles_dir / "p2"
        p1.mkdir(parents=True, exist_ok=True)
        p2.mkdir(parents=True, exist_ok=True)

        # Setup real history and profile history with 3 unique commands
        (simulated_home / ".zsh_history").write_text("cmd_existing_1\ncmd_existing_2\n", encoding="utf-8")
        (p1 / ".zsh_history").symlink_to(simulated_home / ".zsh_history")
        (p2 / ".zsh_history").write_text("cmd_p2_1\ncmd_p2_2\ncmd_p2_3\n", encoding="utf-8")

        # Run sync_shell_env twice
        for _ in range(2):
            res = self.run_cli([
                "--sync-zshrc",
                "--real-home", str(simulated_home),
                "--workspace-root", str(sim_ws_root),
            ])
            self.assertEqual(res.returncode, 0, f"stderr: {res.stderr}")

        # The 3 unique commands must appear exactly once
        shared_hist = (simulated_home / ".zsh_history").read_text(encoding="utf-8")
        self.assertEqual(shared_hist.count("cmd_p2_1"), 1)
        self.assertEqual(shared_hist.count("cmd_p2_2"), 1)
        self.assertEqual(shared_hist.count("cmd_p2_3"), 1)
        self.assertTrue((p1 / ".zsh_history").is_symlink())
        self.assertTrue((p2 / ".zsh_history").is_symlink())

    def test_cmm_fr_02_missing_contracts_and_git_fallback(self) -> None:
        """[CMM-FR-02] Graceful Fallback When D3Nexus Shared Contracts or Repo Git Directory Is Absent."""
        # Non-git directory in workspace
        non_git_repo = self.workspace / "lyrics-sync"
        non_git_repo.mkdir(parents=True, exist_ok=True)

        harvest = self.run_cli([])
        self.assertEqual(harvest.returncode, 0, f"stderr: {harvest.stderr}")
        out = harvest.stdout
        self.assertIn("(D3Nexus/shared-contracts not initialized yet.)", out)
        # Verify all 6 sections printed
        self.assertIn("0. PROJECT ARCHITECTURAL LEDGER", out)
        self.assertIn("1. ACTIVE EPIC STATE", out)
        self.assertIn("2. RECENT PROGRAMMER ACTIVITY", out)
        self.assertIn("3. GIT WORKING TREE", out)
        self.assertIn("4. OPEN CONTRACT GAPS & RFCS", out)
        self.assertIn("5. ACTIVE TASKS", out)

    def test_cmm_st_02_checkpoint_non_destructive_save(self) -> None:
        """[CMM-ST-02] Non-Destructive Checkpoint Save via --complete --checkpoint With Custom Prompt."""
        # 1. Existing entry in activity log
        res_log = self.run_cli([
            "--log", "--epic", "context_memory_management",
            "--task", "task_01",
            "--request", "Initial task",
            "--action", "Initial code",
            "--note", "Initial note",
        ])
        self.assertEqual(res_log.returncode, 0, f"stderr: {res_log.stderr}")

        # 2. Run --complete --checkpoint
        custom_prompt = "Locked multi-epic storage model; next write task_01"
        res_cp = self.run_cli([
            "--complete", "context_memory_management", custom_prompt,
            "--checkpoint",
        ])
        self.assertEqual(res_cp.returncode, 0, f"stderr: {res_cp.stderr}")

        # 3. State and log must be updated with custom prompt
        state_file = self.repo_dir / ".devtool" / "state" / "context_memory_management.md"
        log_file = self.repo_dir / ".devtool" / "logs" / "activity_context_memory_management.log"
        self.assertTrue(state_file.exists())
        self.assertTrue(log_file.exists())

        state_content = state_file.read_text(encoding="utf-8")
        log_content = log_file.read_text(encoding="utf-8")
        self.assertIn(custom_prompt, state_content)
        self.assertIn(custom_prompt, log_content)

        # 4. PROJECT_LEDGER.md must NOT have milestone appended
        ledger_file = self.repo_dir / ".devtool" / "PROJECT_LEDGER.md"
        if ledger_file.exists():
            self.assertNotIn("`context_memory_management`**: Locked", ledger_file.read_text(encoding="utf-8"))

        # 5. Archive must NOT contain context_memory_management
        archive_dir = self.repo_dir / ".devtool" / "archive"
        if archive_dir.exists():
            self.assertEqual(len(list(archive_dir.glob("*context_memory_management*"))), 0)

        # 6. Validate skill and rule files
        resume_skill = REPO_ROOT / "skills" / "resume-context" / "SKILL.md"
        save_skill = REPO_ROOT / "skills" / "save-context" / "SKILL.md"
        critical_rules = REPO_ROOT / "rules" / "CRITICAL_RULES.md"

        self.assertTrue(resume_skill.exists(), "skills/resume-context/SKILL.md does not exist")
        self.assertTrue(save_skill.exists(), "skills/save-context/SKILL.md does not exist")
        self.assertTrue(critical_rules.exists(), "rules/CRITICAL_RULES.md does not exist")

        self.assertIn("name: resume-context", resume_skill.read_text(encoding="utf-8"))
        self.assertIn("name: save-context", save_skill.read_text(encoding="utf-8"))
        self.assertIn("## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline", critical_rules.read_text(encoding="utf-8"))

    def test_cmm_hp_03_skills_lifecycle_hooks_and_verify_harness(self) -> None:
        """[CMM-HP-03] End-to-End Skill Definitions, Dev-Lifecycle Hooks, and Release Verification Harness."""
        # 1. Frontmatter check on new skills
        for skill_name in ["resume-context", "save-context"]:
            skill_file = REPO_ROOT / "skills" / skill_name / "SKILL.md"
            self.assertTrue(skill_file.exists())
            content = skill_file.read_text(encoding="utf-8")
            self.assertTrue(content.startswith("---\nname: " + skill_name + "\ndescription: "))

        # 2. Check resume_context.py hooks in lifecycle skills
        hooks_to_check = [
            REPO_ROOT / "skills" / "dev-brainstorming" / "SKILL.md",
            REPO_ROOT / "skills" / "dev-designer" / "SKILL.md",
            REPO_ROOT / "skills" / "dev-lifecycle" / "SKILL.md",
            REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md",
            REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "principal-review.md",
            REPO_ROOT / "skills" / "principal-review" / "SKILL.md",
            REPO_ROOT / "skills" / "dev-implementation" / "SKILL.md",
            REPO_ROOT / "skills" / "cross-model-review" / "SKILL.md",
            REPO_ROOT / "skills" / "finishing-a-development-branch" / "SKILL.md",
        ]
        for h_file in hooks_to_check:
            self.assertTrue(h_file.exists(), f"File {h_file} does not exist")
            self.assertIn("resume_context.py", h_file.read_text(encoding="utf-8"), f"Hook missing in {h_file.name}")

        # 3. Check persona in handoff-template.md
        handoff_tmpl = REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
        self.assertIn("[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]", handoff_tmpl.read_text(encoding="utf-8"))

        # 4. Check Section 15 in verify.sh
        verify_sh = REPO_ROOT / "scripts" / "verify.sh"
        self.assertTrue(verify_sh.exists())
        verify_content = verify_sh.read_text(encoding="utf-8")
        self.assertIn("15. Context memory management", verify_content)
        self.assertIn("test_resume_context.py", verify_content)


if __name__ == "__main__":
    unittest.main()
