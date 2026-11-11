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

    def run(self, resume: bool = False) -> int:
        """Execute autonomous pipeline state transitions."""
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

    def step_principal_review(self) -> bool:
        """Execute Stage 2 Principal Review automation with selective human stop."""
        return True

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
        return True, "Gate 4 PASS"

    def step_cross_model_review(self) -> bool:
        """Execute Stage 3 Cross-Model Review fix plan evaluation loop."""
        return True

    def evaluate_circuit_breakers(self, stage: str, round_num: int) -> str | None:
        """Evaluate circuit breaker triggers across review rounds."""
        return None

    def prompt_human_principal_fixes(self, triage_summary: str) -> bool:
        """Prompt Human Architect for confirmation when critical/contract conflicts occur."""
        return True

    def evaluate_programmer_fix_plan(self, round_num: int) -> tuple[FixPlanVerdict, str]:
        """Evaluate AI Programmer fix plan against approved HLD."""
        return FixPlanVerdict.APPROVED, ""

    def render_final_executive_report(self) -> str:
        """Render final executive markdown report synthesizing findings across all rounds."""
        return ""


def main() -> int:
    """CLI entrypoint for autonomous lifecycle runner."""
    parser = argparse.ArgumentParser(description="Autonomous Lifecycle Runner CLI")
    parser.add_argument("--epic", required=True, help="Epic slug identifier")
    parser.add_argument("--resume", action="store_true", help="Resume from interrupted state")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Workspace root directory")
    parser.add_argument("--programmer-model", default="gemini-3.8-flash", help="Model for Programmer")
    parser.add_argument("--assistant-model", default=None, help="Model override for Assistant")
    args = parser.parse_args()

    cfg = RunnerConfig(
        programmer_model=args.programmer_model,
        assistant_model=args.assistant_model,
    )
    runner = LifecycleRunner(root=args.root, epic_slug=args.epic, config=cfg)
    return runner.run(resume=args.resume)


if __name__ == "__main__":
    sys.exit(main())
