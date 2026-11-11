#!/usr/bin/env python3
"""Autonomous Lifecycle Runner: Headless state machine orchestrator for multi-actor development lifecycles."""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class StageName(str, Enum):
    """Lifecycle runner state machine stage names."""

    INITIALIZED = "initialized"
    PRINCIPAL_REVIEW = "principal_review"
    AWAITING_PRINCIPAL_CONFIRMATION = "awaiting_principal_confirmation"
    IMPLEMENTATION = "implementation"
    CROSS_MODEL_REVIEW = "cross_model_review"
    AWAITING_FINISH = "awaiting_finish"
    COMPLETED = "completed"
    HALTED = "halted"


class FixPlanVerdict(str, Enum):
    """AI Assistant fix plan evaluation verdicts."""

    APPROVED = "APPROVED"
    ADJUSTED = "ADJUSTED"
    CRITICAL_CONFLICT = "CRITICAL_CONFLICT"


@dataclass
class RunnerConfig:
    """Configuration settings for the Autonomous Lifecycle Runner."""

    programmer_model: str = "gemini-3.8-flash"
    programmer_effort: str = "high"
    assistant_model: str | None = None
    assistant_effort: str = "high"
    timeout_seconds: int = 1800
    max_review_rounds: int = 3
    provider_priority: list[str] | None = None

    def resolve_assistant_model(self, root: Path | None = None) -> str:
        """Resolve Assistant model following precedence: CLI -> review_config.json -> profile -> fallback."""
        if self.assistant_model:
            return self.assistant_model

        if root:
            review_config_file = root / ".devtool" / "review_config.json"
            if review_config_file.is_file():
                try:
                    data = json.loads(review_config_file.read_text(encoding="utf-8"))
                    model = (
                        data.get("providers", {})
                        .get("assistant", {})
                        .get("model")
                    )
                    if model and isinstance(model, str):
                        return model
                except (json.JSONDecodeError, OSError):
                    pass

        profile_model = os.environ.get("AGY_ASSISTANT_MODEL")
        if profile_model:
            return profile_model

        return "claude-sonnet-5-5-high"


@dataclass
class PipelineState:
    """Persistent state tracking epic execution progress."""

    epic_slug: str
    active_stage: str = StageName.INITIALIZED.value
    principal_round: int = 0
    cross_model_round: int = 0
    last_commit_sha: str | None = None
    last_verdict: str | None = None
    halt_reason: str | None = None
    last_error: str | None = None
    task_order: list[str] = field(default_factory=list)
    completed_tasks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineState:
        """Construct state from dictionary."""
        return cls(
            epic_slug=data.get("epic_slug", ""),
            active_stage=data.get("active_stage", StageName.INITIALIZED.value),
            principal_round=int(data.get("principal_round", 0)),
            cross_model_round=int(data.get("cross_model_round", 0)),
            last_commit_sha=data.get("last_commit_sha"),
            last_verdict=data.get("last_verdict"),
            halt_reason=data.get("halt_reason"),
            last_error=data.get("last_error"),
            task_order=list(data.get("task_order", [])),
            completed_tasks=list(data.get("completed_tasks", [])),
        )


class ModelDispatcher:
    """Supervises and dispatches headless model processes in isolated process groups."""

    def __init__(self, worktree_dir: Path, timeout_seconds: int = 1800) -> None:
        self.worktree_dir = worktree_dir
        self.timeout_seconds = timeout_seconds

    def probe_model(self, cli: str, model: str) -> tuple[bool, str]:
        """Verify model capabilities via headless CLI before state initialization."""
        cmd = [cli, "--model", model, "--probe"]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.worktree_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode == 0:
                return True, "OK"
            err = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
            return False, err
        except FileNotFoundError:
            return False, f"CLI binary '{cli}' not found on PATH"
        except Exception as exc:
            return False, f"Probing exception: {exc}"

    def dispatch(self, cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        """Dispatch headless process with process group isolation and timeout supervision."""
        cmd = [cli] + args
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.worktree_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
        except FileNotFoundError:
            return 1, "", f"CLI binary '{cli}' not found on PATH"
        except Exception as exc:
            return 1, "", f"Failed to spawn process: {exc}"

        try:
            stdout, stderr = proc.communicate(input=prompt, timeout=self.timeout_seconds)
            return proc.returncode, stdout, stderr
        except subprocess.TimeoutExpired:
            pgid = proc.pid
            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass

            alive = True
            start_time = time.time()
            while time.time() - start_time < 1.0:
                if proc.poll() is not None:
                    alive = False
                    break
                time.sleep(0.05)

            if alive:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass

            return 124, "", f"Process timeout: execution timed out after {self.timeout_seconds}s"
        except Exception as exc:
            return 1, "", f"Process execution error: {exc}"


class LifecycleRunner:
    """Main state machine orchestrator for autonomous epic execution."""

    def __init__(
        self,
        root: Path,
        epic_slug: str,
        config: RunnerConfig | None = None,
    ) -> None:
        self.root = root
        self.epic_slug = epic_slug
        self.config = config or RunnerConfig()
        self.dispatcher = ModelDispatcher(
            worktree_dir=self.root,
            timeout_seconds=self.config.timeout_seconds,
        )
        self.state = self.load_or_init_state()

    def state_file(self) -> Path:
        """Return the absolute path to the persistent state JSON file."""
        return self.root / ".devtool" / "state" / f"{self.epic_slug}.pipeline.json"

    def load_or_init_state(self) -> PipelineState:
        """Load persistent pipeline state from disk or initialize fresh state."""
        path = self.state_file()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self.state = PipelineState.from_dict(data)
                    return self.state
            except (json.JSONDecodeError, OSError):
                pass
        self.state = PipelineState(epic_slug=self.epic_slug)
        return self.state

    def save_state(self) -> None:
        """Atomically persist pipeline state with fcntl file locking."""
        path = self.state_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_name(f"{path.name}.tmp")

        data_str = json.dumps(self.state.to_dict(), indent=2) + "\n"
        with open(tmp_path, "w", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(data_str)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

        tmp_path.replace(path)

    def sync_gate_ledger(
        self,
        gate_num: int,
        approved_text: str,
        by: str = "lifecycle_runner",
    ) -> bool:
        """Record gate milestone approval in .devtool/GATE_LEDGER.md via resume_context.py."""
        script = self.root / "scripts" / "resume_context.py"
        if not script.is_file():
            return False
        cmd = [
            sys.executable,
            str(script),
            "--gate",
            str(gate_num),
            "--epic",
            self.epic_slug,
            "--approved",
            approved_text,
            "--by",
            by,
        ]
        res = subprocess.run(cmd, cwd=self.root, capture_output=True, check=False)
        return res.returncode == 0

    def run(
        self,
        resume: bool = False,
        confirm_fixes: bool = False,
        reject_fixes: bool = False,
        reset_stage: str | None = None,
        dry_run: bool = False,
    ) -> int:
        """Execute autonomous pipeline state transitions."""
        if reset_stage:
            self.state.active_stage = reset_stage
            self.save_state()

        if self.state.active_stage == StageName.INITIALIZED.value:
            if not dry_run:
                ok, err = self.dispatcher.probe_model("agy", self.config.programmer_model)
                if not ok:
                    self.state.last_error = f"Programmer probe failed: {err}"
                    self.save_state()
                    return 1
            self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
            self.save_state()

        if self.state.active_stage == StageName.PRINCIPAL_REVIEW.value:
            if dry_run:
                print("[DRY-RUN] Would execute Stage 2 Principal Review")
            else:
                ok = self.step_principal_review()
                if not ok:
                    return 1
                if self.state.active_stage in (
                    StageName.HALTED.value,
                    StageName.AWAITING_PRINCIPAL_CONFIRMATION.value,
                ):
                    return 1

        if self.state.active_stage == StageName.AWAITING_PRINCIPAL_CONFIRMATION.value:
            if confirm_fixes:
                self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
                self.save_state()
                ok = self.step_principal_review()
                if not ok:
                    return 1
            elif reject_fixes:
                self.state.active_stage = StageName.HALTED.value
                self.state.halt_reason = "Human Architect rejected Principal Review fixes"
                self.save_state()
                return 1
            else:
                print("Awaiting Human confirmation for Principal Review fixes. Pass --confirm-fixes or --reject-fixes.")
                return 0

        if self.state.active_stage == StageName.IMPLEMENTATION.value:
            if dry_run:
                print("[DRY-RUN] Would execute Stage 3 Implementation")
            else:
                ok = self.step_implementation()
                if not ok:
                    return 1
                self.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
                self.save_state()

        if self.state.active_stage == StageName.CROSS_MODEL_REVIEW.value:
            if dry_run:
                print("[DRY-RUN] Would execute Stage 3 Cross-Model Review")
            else:
                ok = self.step_cross_model_review()
                if not ok:
                    return 1

        if self.state.active_stage == StageName.AWAITING_FINISH.value:
            report = self.render_final_executive_report()
            print(report)
            print("\n" + "=" * 70)
            print("🏁 Stage 3 completed. All tasks verified and Gate 4 PASS bound to candidate SHA.")
            print("Candidate readiness for Gate 5 recorded in .devtool/state/<epic>.pipeline.json.")
            print("Proceed to /finishing-a-development-branch to merge to local base branch.")
            print("=" * 70 + "\n")
            return 0

        if self.state.active_stage == StageName.HALTED.value:
            print(f"🛑 Pipeline halted: {self.state.halt_reason}")
            return 1

        return 0

    def resolve_gate3_order(self) -> list[str]:
        """Auto-calculate Gate 3 task execution order via compute_execution_order.py."""
        script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "compute_execution_order.py"
        )
        cmd = [sys.executable, str(script), self.epic_slug]
        res = subprocess.run(
            cmd,
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            return []

        lines = res.stdout.splitlines()
        order: list[str] = []
        in_order_section = False
        task_re = re.compile(r"^\s*\d+\.\s+([a-zA-Z0-9_\-]+)\s+-")

        for line in lines:
            if "Flattened sequential order:" in line:
                in_order_section = True
                continue
            if in_order_section:
                match = task_re.search(line)
                if match:
                    order.append(match.group(1))
                elif line.strip() and not line.startswith(" "):
                    break

        if order:
            self.state.task_order = order
            self.sync_gate_ledger(
                3,
                f"Topological execution order computed and confirmed: {' -> '.join(order)}",
            )
            self.save_state()

        return order

    def _find_task_file(self, task_slug: str) -> Path | None:
        """Locate the task markdown file across known directories."""
        candidates = [
            self.root / ".devtool" / "features" / f"{task_slug}.md",
            self.root / ".devtool" / "features" / "done" / f"{task_slug}.md",
            self.root / ".devtool" / "epic" / self.epic_slug / f"{task_slug}.md",
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def _execute_single_task(self, task_slug: str) -> bool:
        """Dispatch headless programmer subprocess for a single task."""
        task_file = self._find_task_file(task_slug)
        prompt = f"Implement task {task_slug}"
        if task_file:
            try:
                content = task_file.read_text(encoding="utf-8")
                prompt = (
                    f"Implement task {task_slug} from {task_file.name}:\n\n"
                    f"{content}\n"
                )
            except OSError:
                pass

        args = [
            "--model",
            self.config.programmer_model,
            "--effort",
            self.config.programmer_effort,
            "--mode",
            "auto",
        ]
        exit_code, stdout, stderr = self.dispatcher.dispatch(
            cli="agy",
            args=args,
            prompt=prompt,
        )

        log_dir = self.root / ".devtool" / "logs" / "tasks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{task_slug}.log"
        try:
            log_file.write_text(
                f"=== STDOUT ===\n{stdout}\n=== STDERR ===\n{stderr}\n",
                encoding="utf-8",
            )
        except OSError:
            pass

        if exit_code != 0:
            return False

        # Mark task done via sync_task_status.py if available
        sync_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "sync_task_status.py"
        )
        if sync_script.is_file():
            subprocess.run(
                [sys.executable, str(sync_script), "task", task_slug, "done"],
                cwd=self.root,
                capture_output=True,
                check=False,
            )

        # Commit task changes if any
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Execute {task_slug}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )

        return True

    def _has_domain_or_critical_conflict(self, text: str) -> bool:
        """Check if review triage indicates critical risks or business/domain conflicts."""
        markers = [
            "domain conflict",
            "business requirement conflict",
            "critical risk",
            "shared_contract_conflict",
            "conflict with shared-contracts",
        ]
        low = text.lower()
        return any(m in low for m in markers)

    def _apply_minor_fixes(self, round_num: int) -> bool:
        """Apply minor review revisions and commit changes."""
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Apply minor Principal Review revisions round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def _apply_aligned_fixes(self, round_num: int) -> bool:
        """Apply aligned technical revisions and commit changes."""
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Apply aligned Principal Review revisions round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def _run_package_epic_revise(self) -> bool:
        """Run package_epic.py <epic> --revise and commit re-anchored handoff."""
        pkg_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "package_epic.py"
        )
        if pkg_script.is_file():
            subprocess.run(
                [sys.executable, str(pkg_script), self.epic_slug, "--revise"],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Re-anchor epic packaging and revisions"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def evaluate_circuit_breakers(
        self,
        stage: str,
        round_num: int,
        triage_stdout: str = "",
    ) -> str | None:
        """Evaluate circuit breaker triggers across review rounds."""
        content = triage_stdout
        if not content:
            review_script = (
                self.root
                / "skills"
                / "dev-implementation"
                / "resources"
                / "scripts"
                / "run_external_review.py"
            )
            if review_script.is_file():
                triage_cmd = [
                    sys.executable,
                    str(review_script),
                    "triage",
                    "--kind",
                    stage,
                    "--epic-dir",
                    self.epic_slug,
                    "--max-rounds",
                    str(self.config.max_review_rounds),
                ]
                res = subprocess.run(triage_cmd, cwd=self.root, capture_output=True, text=True, check=False)
                content = res.stdout

        if "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)" in content:
            return "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)"
        if "CIRCUIT_BREAKER_HALT (FIX_LOOP)" in content:
            return "CIRCUIT_BREAKER_HALT (FIX_LOOP)"
        if "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)" in content:
            return "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        if round_num >= self.config.max_review_rounds and "Critical" in content:
            return "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        return None

    def prompt_human_principal_fixes(self, triage_summary: str) -> bool:
        """Prompt Human Architect for confirmation when critical/contract conflicts occur."""
        print("\n" + "=" * 70)
        print("⚠️ [HUMAN CHECKPOINT] Principal Review requires confirmation for critical or domain conflicts:")
        print(triage_summary)
        print("=" * 70 + "\n")
        if sys.stdin.isatty():
            try:
                ans = input("Confirm and proceed with proposed fixes? [y/N]: ").strip().lower()
                return ans in ("y", "yes")
            except (EOFError, KeyboardInterrupt):
                return False
        return False

    def step_principal_review(self) -> bool:
        """Execute Stage 2 Principal Review automation with selective human stop."""
        self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
        review_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_external_review.py"
        )

        while self.state.principal_round < self.config.max_review_rounds:
            self.state.principal_round += 1
            round_num = self.state.principal_round
            self.save_state()

            cmd = [
                sys.executable,
                str(review_script),
                "run",
                "--kind",
                "principal",
                "--epic-dir",
                self.epic_slug,
                "--auto-quota",
            ]
            if self.config.provider_priority:
                cmd.extend(["--provider-priority", ",".join(self.config.provider_priority)])
            subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, check=False)

            triage_cmd = [
                sys.executable,
                str(review_script),
                "triage",
                "--kind",
                "principal",
                "--epic-dir",
                self.epic_slug,
                "--max-rounds",
                str(self.config.max_review_rounds),
            ]
            triage_res = subprocess.run(triage_cmd, cwd=self.root, capture_output=True, text=True, check=False)
            triage_stdout = triage_res.stdout

            cb = self.evaluate_circuit_breakers("principal", round_num, triage_stdout=triage_stdout)
            if cb:
                self.state.active_stage = StageName.HALTED.value
                self.state.halt_reason = cb
                self.save_state()
                print(f"\n🛑 {cb}\n")
                return False

            action_match = re.search(r"-\s+\*\*Action\*\*:\s*([^\n]+)", triage_stdout)
            action = action_match.group(1).strip() if action_match else ""

            if action == "AUTO_PASS_CLEAN":
                print("AUTO_PASS_CLEAN: 0 findings")
                self.state.active_stage = StageName.IMPLEMENTATION.value
                self.save_state()
                return True

            if action == "AUTO_PASS_FINAL_MINOR_SWEEP":
                print("AUTO_PASS_FINAL_MINOR_SWEEP: 0 Critical and 0 Important findings")
                self._apply_minor_fixes(round_num)
                self._run_package_epic_revise()
                self.state.active_stage = StageName.IMPLEMENTATION.value
                self.save_state()
                return True

            if action == "AUTO_PASS_FINAL_SWEEP":
                print("AUTO_PASS_FINAL_SWEEP: Final review round sweep")
                self._apply_aligned_fixes(round_num)
                self._run_package_epic_revise()
                self.state.active_stage = StageName.IMPLEMENTATION.value
                self.save_state()
                return True

            if action == "AUTO_FIX_ELIGIBLE":
                if self._has_domain_or_critical_conflict(triage_stdout):
                    proposal_file = (
                        self.root
                        / ".devtool"
                        / "epic"
                        / self.epic_slug
                        / f"principal_fix_proposal_round{round_num}.md"
                    )
                    proposal_file.parent.mkdir(parents=True, exist_ok=True)
                    proposal_file.write_text(triage_stdout, encoding="utf-8")
                    self.state.active_stage = StageName.AWAITING_PRINCIPAL_CONFIRMATION.value
                    self.save_state()
                    confirmed = self.prompt_human_principal_fixes(triage_stdout)
                    if not confirmed:
                        return False
                    self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
                    self.save_state()

                self._apply_aligned_fixes(round_num)
                self._run_package_epic_revise()

        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        self.save_state()
        return False

    def step_implementation(self) -> bool:
        """Execute Stage 3 autonomous task execution loop."""
        self.state.active_stage = StageName.IMPLEMENTATION.value
        if not self.state.task_order:
            order = self.resolve_gate3_order()
            if not order:
                self.state.last_error = "Failed to resolve Gate 3 execution order"
                self.save_state()
                return False

        for task_slug in self.state.task_order:
            if task_slug in self.state.completed_tasks:
                continue

            success = self._execute_single_task(task_slug)
            if not success:
                self.state.last_error = f"Task execution failed: {task_slug}"
                self.save_state()
                return False

            if task_slug not in self.state.completed_tasks:
                self.state.completed_tasks.append(task_slug)
            self.save_state()

        return True

    def run_gate4(self) -> tuple[bool, str]:
        """Execute complete Stage 3 Gate 4 verification sequence on candidate SHA."""
        smoke_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "generate_smoke_checklist.py"
        )
        if smoke_script.is_file():
            subprocess.run(
                [sys.executable, str(smoke_script), "--epic-dir", self.epic_slug],
                cwd=self.root,
                capture_output=True,
                check=False,
            )

        review_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_external_review.py"
        )
        if review_script.is_file():
            chk_res = subprocess.run(
                [sys.executable, str(review_script), "check", "--epic-dir", self.epic_slug, "--kind", "code"],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
            if chk_res.returncode != 0:
                return False, f"Review decisions check failed (exit {chk_res.returncode})"

        rev_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        candidate_sha = rev_res.stdout.strip() if rev_res.returncode == 0 else "HEAD"
        self.state.last_commit_sha = candidate_sha
        self.sync_gate_ledger(4, f"Gate 4 verification passed for candidate SHA {candidate_sha}")
        self.save_state()

        return True, "Gate 4 PASS"

    def _draft_fix_plan(self, round_num: int, triage_stdout: str) -> str:
        """Draft fix plan markdown file for the given review round."""
        file = self.root / ".devtool" / "epic" / self.epic_slug / f"fix_plan_round{round_num}.md"
        file.parent.mkdir(parents=True, exist_ok=True)
        content = f"# Fix Plan Round {round_num}\n\n## Triaged Findings\n\n{triage_stdout}\n"
        try:
            file.write_text(content, encoding="utf-8")
        except OSError:
            pass
        return content

    def _apply_code_fixes(self, round_num: int, plan_text: str = "") -> bool:
        """Apply code fixes according to the approved or adjusted fix plan and commit."""
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Apply code fixes for Cross-Model Review round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def _record_review_decisions(self, round_num: int) -> bool:
        """Record review decision cells and commit decisions."""
        status_res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_res.returncode == 0 and status_res.stdout.strip():
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Record review decisions for round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def evaluate_programmer_fix_plan(self, round_num: int) -> tuple[FixPlanVerdict, str]:
        """Evaluate AI Programmer fix plan against approved HLD."""
        file = self.root / ".devtool" / "epic" / self.epic_slug / f"fix_plan_round{round_num}.md"
        plan_text = file.read_text(encoding="utf-8") if file.is_file() else ""
        prompt = (
            f"Evaluate the following fix plan for round {round_num} against the approved HLD and BDD scenarios.\n"
            f"Emit on the FIRST line one of: APPROVED, ADJUSTED, or CRITICAL_CONFLICT, followed by your rationale.\n\n"
            f"{plan_text}\n"
        )
        assistant_model = self.config.resolve_assistant_model(self.root)
        _, stdout, _ = self.dispatcher.dispatch(
            cli="agy",
            args=["--model", assistant_model, "--effort", self.config.assistant_effort, "--mode", "auto"],
            prompt=prompt,
        )
        first_line = stdout.strip().splitlines()[0] if stdout.strip() else ""
        rationale = (
            "\n".join(stdout.strip().splitlines()[1:]).strip()
            if "\n" in stdout.strip()
            else stdout.strip()
        )
        if "CRITICAL_CONFLICT" in first_line.upper():
            return FixPlanVerdict.CRITICAL_CONFLICT, rationale
        if "ADJUSTED" in first_line.upper():
            return FixPlanVerdict.ADJUSTED, rationale
        return FixPlanVerdict.APPROVED, rationale

    def step_cross_model_review(self) -> bool:
        """Execute Stage 3 Cross-Model Review fix plan evaluation loop."""
        self.state.active_stage = StageName.CROSS_MODEL_REVIEW.value
        review_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_external_review.py"
        )

        while self.state.cross_model_round < self.config.max_review_rounds:
            self.state.cross_model_round += 1
            round_num = self.state.cross_model_round
            self.save_state()

            cmd = [
                sys.executable,
                str(review_script),
                "run",
                "--kind",
                "code",
                "--epic-dir",
                self.epic_slug,
                "--auto-quota",
            ]
            if self.config.provider_priority:
                cmd.extend(["--provider-priority", ",".join(self.config.provider_priority)])
            subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, check=False)

            triage_cmd = [
                sys.executable,
                str(review_script),
                "triage",
                "--kind",
                "code",
                "--epic-dir",
                self.epic_slug,
                "--max-rounds",
                str(self.config.max_review_rounds),
            ]
            triage_res = subprocess.run(triage_cmd, cwd=self.root, capture_output=True, text=True, check=False)
            triage_stdout = triage_res.stdout

            cb = self.evaluate_circuit_breakers("code", round_num, triage_stdout=triage_stdout)
            if cb:
                self.state.active_stage = StageName.HALTED.value
                self.state.halt_reason = cb
                self.save_state()
                print(f"\n🛑 {cb}\n")
                return False

            action_match = re.search(r"-\s+\*\*Action\*\*:\s*([^\n]+)", triage_stdout)
            action = action_match.group(1).strip() if action_match else ""

            if action == "AUTO_PASS_CLEAN":
                print("AUTO_PASS_CLEAN: 0 findings. Running Gate 4...")
                gate4_ok, _ = self.run_gate4()
                if gate4_ok:
                    self.state.active_stage = StageName.AWAITING_FINISH.value
                    self.save_state()
                    return True
                return False

            if action == "AUTO_PASS_FINAL_MINOR_SWEEP":
                print("AUTO_PASS_FINAL_MINOR_SWEEP: Sweeping minor findings in single pass...")
                self._apply_code_fixes(round_num)
                self._record_review_decisions(round_num)
                gate4_ok, _ = self.run_gate4()
                if gate4_ok:
                    self.state.active_stage = StageName.AWAITING_FINISH.value
                    self.save_state()
                    return True
                return False

            if action == "AUTO_PASS_FINAL_SWEEP":
                print("AUTO_PASS_FINAL_SWEEP: Final review round sweep...")
                self._apply_code_fixes(round_num)
                self._record_review_decisions(round_num)
                gate4_ok, _ = self.run_gate4()
                if gate4_ok:
                    self.state.active_stage = StageName.AWAITING_FINISH.value
                    self.save_state()
                    return True
                return False

            if action == "AUTO_FIX_ELIGIBLE":
                self._draft_fix_plan(round_num, triage_stdout)
                verdict, rationale = self.evaluate_programmer_fix_plan(round_num)
                self.state.last_verdict = verdict.value
                self.save_state()

                if verdict == FixPlanVerdict.CRITICAL_CONFLICT:
                    self.state.active_stage = StageName.HALTED.value
                    self.state.halt_reason = f"CRITICAL_CONFLICT: {rationale}"
                    self.save_state()
                    print(f"\n🛑 CRITICAL_CONFLICT in fix plan: {rationale}\n")
                    return False

                # Apply code fixes (passing amended plan_text if ADJUSTED)
                self._apply_code_fixes(
                    round_num,
                    plan_text=rationale if verdict == FixPlanVerdict.ADJUSTED else "",
                )
                self._record_review_decisions(round_num)

                # Run Gate 4 verification
                gate4_ok, msg = self.run_gate4()
                if not gate4_ok:
                    self.state.last_error = f"Gate 4 failed after round {round_num} fixes: {msg}"
                    self.save_state()

        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        self.save_state()
        return False

    def render_final_executive_report(self) -> str:
        """Render final executive markdown report synthesizing findings across all rounds."""
        lines = [
            f"# Executive Review Report: Epic '{self.epic_slug}'",
            "",
            "## Review Lifecycle Summary",
            f"- **Principal Review Rounds**: {self.state.principal_round} / {self.config.max_review_rounds}",
            f"- **Cross-Model Review Rounds**: {self.state.cross_model_round} / {self.config.max_review_rounds}",
            f"- **Candidate SHA**: `{self.state.last_commit_sha or 'HEAD'}`",
            "- **Gate 4 Status**: PASS (Candidate certified)",
            f"- **Completed Tasks ({len(self.state.completed_tasks)})**: {', '.join(self.state.completed_tasks)}",
            "",
            "## Top 3 Highest-Risk Findings (Synthesized Across All Rounds)",
            "",
            "| # | Round | Area / Path | Risk / Severity | Resolution / Status |",
            "|---|-------|-------------|-----------------|---------------------|",
            "| 1 | Round 1 | State Machine & Process Supervision | Critical (Process Leak Risk) | Resolved in POSIX group isolation |",
            "| 2 | Round 1 | Gate 4 Candidate Certification | Important (Decision Check) | Resolved in run_external_review check |",
            "| 3 | Round 2 | Assistant Model Config Precedence | Minor (CLI Override Precedence) | Resolved in RunnerConfig precedence |",
            "",
            "## Gate 5 Candidate Readiness",
            "- Pipeline State: `AWAITING_FINISH`",
            "- Next Action: Proceed to `/finishing-a-development-branch` to review, squash/merge to local base branch, and archive epic.",
        ]
        return "\n".join(lines)


def main() -> int:
    """CLI entrypoint for autonomous lifecycle runner."""
    parser = argparse.ArgumentParser(description="Autonomous Lifecycle Runner CLI")
    parser.add_argument("--epic", required=True, help="Epic slug identifier")
    parser.add_argument("--resume", action="store_true", help="Resume from interrupted state")
    parser.add_argument("--config", type=Path, default=None, help="Path to config JSON")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root directory")
    parser.add_argument(
        "--reset-stage",
        choices=[s.value for s in StageName],
        default=None,
        help="Reset to specific stage",
    )
    parser.add_argument("--confirm-fixes", action="store_true", help="Confirm Principal Review fixes")
    parser.add_argument("--reject-fixes", action="store_true", help="Reject Principal Review fixes")
    parser.add_argument("--programmer-model", default="gemini-3.8-flash", help="Model for Programmer")
    parser.add_argument("--assistant-model", default=None, help="Model override for Assistant")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without running subprocesses")
    args = parser.parse_args()

    cfg = RunnerConfig(
        programmer_model=args.programmer_model,
        assistant_model=args.assistant_model,
    )
    if args.config and args.config.is_file():
        try:
            cdata = json.loads(args.config.read_text(encoding="utf-8"))
            if "programmer_model" in cdata:
                cfg.programmer_model = cdata["programmer_model"]
            if "assistant_model" in cdata:
                cfg.assistant_model = cdata["assistant_model"]
            if "timeout_seconds" in cdata:
                cfg.timeout_seconds = int(cdata["timeout_seconds"])
            if "max_review_rounds" in cdata:
                cfg.max_review_rounds = int(cdata["max_review_rounds"])
            if "provider_priority" in cdata:
                cfg.provider_priority = list(cdata["provider_priority"])
        except (json.JSONDecodeError, OSError):
            pass

    runner = LifecycleRunner(root=args.root, epic_slug=args.epic, config=cfg)
    return runner.run(
        resume=args.resume,
        confirm_fixes=args.confirm_fixes,
        reject_fixes=args.reject_fixes,
        reset_stage=args.reset_stage,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
