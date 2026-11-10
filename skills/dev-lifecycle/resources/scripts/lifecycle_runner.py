#!/usr/bin/env python3
"""Autonomous Lifecycle Runner: Headless state machine orchestrator for multi-actor development lifecycles."""
from __future__ import annotations

import argparse
import copy
import fcntl
import json
import os
import shutil
import subprocess
import sys
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
        # Task 2 implements full process group isolation and supervisor timers.
        return 0, "", ""


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
                    return PipelineState.from_dict(data)
            except (json.JSONDecodeError, OSError):
                pass
        return PipelineState(epic_slug=self.epic_slug)

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
        return []

    def step_principal_review(self) -> bool:
        """Execute Stage 2 Principal Review automation with selective human stop."""
        return True

    def step_implementation(self) -> bool:
        """Execute Stage 3 autonomous task execution loop."""
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
