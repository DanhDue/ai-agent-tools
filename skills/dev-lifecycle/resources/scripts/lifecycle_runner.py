#!/usr/bin/env python3
"""Autonomous Lifecycle Runner: Headless state machine orchestrator for multi-actor development lifecycles."""
from __future__ import annotations

import argparse
import copy
import fcntl
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional


DEFAULT_PROGRAMMER_MODEL = "gemini-4-hydrogen-xhigh"
DEFAULT_PROGRAMMER_EFFORT = "xhigh"
LEGACY_PROGRAMMER_MODELS = frozenset({"gemini-3.8-flash", "gemini-3.8-flash-high"})
EXTRA_EFFORT_ALIASES = frozenset({"extra", "extra-high", "extra_high", "xhigh"})


def normalize_agy_effort(raw: str) -> str:
    """Normalize reasoning effort aliases ('extra', 'extra-high', 'xhigh') for agy CLI."""
    cleaned = raw.strip().lower()
    if not cleaned or cleaned in EXTRA_EFFORT_ALIASES:
        return "xhigh"
    return cleaned


def build_agy_command(model: str, effort: str, mode: str = "auto") -> list[str]:
    """Construct canonical agy CLI invocation args with normalized effort."""
    return [
        "agy",
        "--model",
        model,
        "--effort",
        normalize_agy_effort(effort),
        "--mode",
        mode,
    ]


def _upgrade_legacy_programmer_pair(
    model: str | None,
    effort: str | None,
) -> tuple[str | None, str | None]:
    """Upgrade legacy 3.8 programmer aliases in-memory without mutating files."""
    clean_model = model.strip() if isinstance(model, str) and model.strip() else None
    clean_effort = effort.strip() if isinstance(effort, str) and effort.strip() else None

    if clean_model in LEGACY_PROGRAMMER_MODELS:
        clean_model = DEFAULT_PROGRAMMER_MODEL
        if clean_effort is None or clean_effort.lower() in {"high"} | EXTRA_EFFORT_ALIASES:
            clean_effort = DEFAULT_PROGRAMMER_EFFORT
        else:
            clean_effort = normalize_agy_effort(clean_effort)
        return clean_model, clean_effort

    if clean_effort is not None:
        clean_effort = normalize_agy_effort(clean_effort)
    return clean_model, clean_effort


def _tail_lines(text: str, limit: int = 25) -> str:
    """Keep at most the trailing `limit` non-empty lines for concise error summaries."""
    if limit <= 0 or not text:
        return ""
    non_empty = [line for line in text.splitlines() if line.strip()]
    if not non_empty:
        return ""
    return "\n".join(non_empty[-limit:])


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

    programmer_model: str | None = None
    programmer_effort: str | None = None
    config_programmer_model: str | None = None
    config_programmer_effort: str | None = None
    assistant_model: str | None = None
    assistant_effort: str = "high"
    timeout_seconds: int = 1800
    max_review_rounds: int = 3
    provider_priority: list[str] | None = None
    base_branch: str = "main"

    def _read_review_config_programmer(self, root: Path | None) -> tuple[str | None, str | None]:
        """Read-only lookup of providers.programmer from .devtool/review_config.json."""
        if not root:
            return None, None
        review_config_file = root / ".devtool" / "review_config.json"
        if not review_config_file.is_file():
            return None, None
        try:
            data = json.loads(review_config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None, None

        if not isinstance(data, dict):
            return None, None
        prog = data.get("providers", {}).get("programmer", {})
        if not isinstance(prog, dict):
            return None, None

        raw_model = prog.get("model") if isinstance(prog.get("model"), str) else None
        raw_effort_val = prog.get("effort") if prog.get("effort") is not None else prog.get("thinking_level")
        raw_effort = raw_effort_val if isinstance(raw_effort_val, str) else None
        return _upgrade_legacy_programmer_pair(raw_model, raw_effort)

    def resolve_programmer_model(self, root: Path | None = None) -> str:
        """Resolve Programmer model: CLI -> --config -> review_config.json -> env -> fallback."""
        if self.programmer_model and self.programmer_model.strip():
            return self.programmer_model.strip()

        if self.config_programmer_model and self.config_programmer_model.strip():
            cfg_model, _ = _upgrade_legacy_programmer_pair(
                self.config_programmer_model, self.config_programmer_effort
            )
            if cfg_model:
                return cfg_model

        rc_model, _ = self._read_review_config_programmer(root)
        if rc_model:
            return rc_model

        env_model_raw = os.environ.get("AGY_PROGRAMMER_MODEL", "")
        env_effort_raw = os.environ.get("AGY_PROGRAMMER_EFFORT", "")
        env_model, _ = _upgrade_legacy_programmer_pair(env_model_raw, env_effort_raw or None)
        if env_model:
            return env_model

        return DEFAULT_PROGRAMMER_MODEL

    def resolve_programmer_effort(self, root: Path | None = None) -> str:
        """Resolve Programmer effort: CLI -> --config -> review_config.json -> env -> fallback."""
        if self.programmer_effort and self.programmer_effort.strip():
            return normalize_agy_effort(self.programmer_effort)

        if self.config_programmer_effort and self.config_programmer_effort.strip():
            _, cfg_effort = _upgrade_legacy_programmer_pair(
                self.config_programmer_model, self.config_programmer_effort
            )
            if cfg_effort:
                return cfg_effort

        _, rc_effort = self._read_review_config_programmer(root)
        if rc_effort:
            return rc_effort

        env_model_raw = os.environ.get("AGY_PROGRAMMER_MODEL", "")
        env_effort_raw = os.environ.get("AGY_PROGRAMMER_EFFORT", "")
        _, env_effort = _upgrade_legacy_programmer_pair(env_model_raw or None, env_effort_raw)
        if env_effort:
            return env_effort

        return DEFAULT_PROGRAMMER_EFFORT

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
        if cli == "agy":
            cmd = [cli, "models"]
        else:
            cmd = [cli, "--version"]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.worktree_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                err = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
                return False, err

            if cli == "agy":
                clean_target = model.strip().lower()
                clean_output = res.stdout.lower()
                if (
                    clean_target in clean_output
                    or "model probe successful" in clean_output
                    or any(clean_target in line for line in clean_output.splitlines())
                ):
                    return True, "OK"
                return False, f"Model '{model}' is not supported by agy."

            return True, "OK"
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
                prog_model = self.config.resolve_programmer_model(self.root)
                ok, err = self.dispatcher.probe_model("agy", prog_model)
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

    @staticmethod
    def _tail_lines(text: str, limit: int = 25) -> str:
        """Keep at most the trailing `limit` non-empty lines for concise error reporting."""
        return _tail_lines(text, limit)

    def _resolve_script(self, rel_under_skills: str) -> Path | None:
        """Resolve a kit helper script from self.root first, falling back to kit tree."""
        local = self.root / "skills" / rel_under_skills
        if local.is_file():
            return local
        kit = Path(__file__).resolve().parents[3] / rel_under_skills
        if kit.is_file():
            return kit
        return None

    def _load_pool_module(self) -> Any:
        """Dynamically load manage_worker_pool.py module."""
        pool_path = self._resolve_script("dev-implementation/resources/scripts/manage_worker_pool.py")
        if pool_path is None:
            return None
        spec = importlib.util.spec_from_file_location("manage_worker_pool", pool_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _is_git_repo(self, path: Path | None = None) -> bool:
        """Return True if path (default self.root) is inside a valid git worktree."""
        target = path or self.root
        if not target.is_dir():
            return False
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=target,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0 and res.stdout.strip().lower() == "true"

    def resolve_gate3_order(self) -> list[str]:
        """Auto-calculate Gate 3 task execution order via compute_execution_order.py."""
        script = self._resolve_script("dev-implementation/resources/scripts/compute_execution_order.py")
        if script is None:
            return []
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

    def _find_task_file(self, task_slug: str, root: Path | None = None) -> Path | None:
        """Locate the task markdown file across known directories."""
        base = root or self.root
        candidates = [
            base / ".devtool" / "features" / f"{task_slug}.md",
            base / ".devtool" / "features" / "done" / f"{task_slug}.md",
            base / ".devtool" / "epic" / self.epic_slug / f"{task_slug}.md",
        ]
        for c in candidates:
            if c.is_file():
                return c
        return None

    def _extract_task_targets(self, task_content: str) -> list[str]:
        """Extract target file paths and optional (Lstart-Lend) line ranges from task markdown."""
        targets_by_path: dict[str, str] = {}
        in_relevant = False
        in_allowed_yaml = False
        line_range_re = re.compile(
            r"`([^`]+)`(?:\s*\((L?\d+(?:\s*[-–]\s*L?\d+)?)\))?|\b([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)\s*\((L?\d+(?:\s*[-–]\s*L?\d+)?)\)"
        )

        for raw_line in task_content.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("## "):
                heading = stripped[3:].strip().lower()
                in_relevant = any(
                    key in heading for key in ("files", "impact analysis", "blast radius")
                )
                in_allowed_yaml = False
                continue

            if stripped == "Allowed files:":
                in_allowed_yaml = True
                continue

            if in_allowed_yaml and not stripped.startswith("-") and stripped:
                in_allowed_yaml = False

            if not (in_relevant or in_allowed_yaml):
                continue

            for match in line_range_re.finditer(raw_line):
                path_tok = (match.group(1) or match.group(3) or "").strip()
                range_tok = (match.group(2) or match.group(4) or "").strip()
                if (
                    not path_tok
                    or " " in path_tok
                    or path_tok.startswith("-")
                    or not ("/" in path_tok or re.search(r"\.[A-Za-z][A-Za-z0-9]{0,7}$", path_tok))
                ):
                    continue
                if range_tok and not range_tok.startswith("L"):
                    range_tok = f"L{range_tok}"
                if path_tok not in targets_by_path or range_tok:
                    targets_by_path[path_tok] = (
                        f"{path_tok} ({range_tok})" if range_tok else path_tok
                    )

        return list(targets_by_path.values())

    def _build_task_prompt(
        self,
        task_slug: str,
        task_file: Path | None,
        exec_root: Path,
    ) -> str:
        """Build a concise path-only Zero-Fluff prompt referencing targeted files and anchors."""
        target_refs: list[str] = []
        task_rel = f".devtool/features/{task_slug}.md"
        if task_file is not None:
            try:
                task_rel = str(task_file.relative_to(exec_root))
            except ValueError:
                try:
                    task_rel = str(task_file.relative_to(self.root))
                except ValueError:
                    task_rel = str(task_file)
            try:
                target_refs = self._extract_task_targets(task_file.read_text(encoding="utf-8"))
            except OSError:
                target_refs = []

        anchor_candidates = [
            f".devtool/epic/{self.epic_slug}/handoff.md",
            f".devtool/epic/{self.epic_slug}/{self.epic_slug}.en.md",
            f".devtool/epic/{self.epic_slug}/hld.en.md",
            f".devtool/epic/{self.epic_slug}/bdd_scenarios.en.md",
        ]
        existing_anchors = [
            rel for rel in anchor_candidates if (exec_root / rel).is_file() or (self.root / rel).is_file()
        ]

        lines = [
            f"Implement task `{task_slug}` inside workspace `{exec_root}` using strict TDD.",
            f"- Task spec path (read directly bounded): `{task_rel}`",
        ]
        if existing_anchors:
            lines.append("- Design/BDD anchors (paths only):")
            for anchor in existing_anchors:
                lines.append(f"  - `{anchor}`")
        if target_refs:
            lines.append("- Target files & line ranges (read bounded <=150 lines per call):")
            for ref in target_refs:
                lines.append(f"  - `{ref}`")
        lines.extend(
            [
                "- Constraints: Modify ONLY this task's Allowed files. Do not invoke d3nexus:task-observer.",
                "- Output cap (Zero-Fluff): Reply ONLY with modified file paths, pass/fail test counts, and blocking errors (preserve required Gate/verdict/finding lines).",
            ]
        )
        return "\n".join(lines) + "\n"

    def _execute_single_task(
        self,
        task_slug: str,
        worktree_dir: Path | None = None,
        dispatcher: ModelDispatcher | None = None,
    ) -> bool:
        """Dispatch headless programmer subprocess for a single task inside `worktree_dir`."""
        exec_root = worktree_dir or self.root
        task_file = self._find_task_file(task_slug, root=exec_root) or self._find_task_file(
            task_slug, root=self.root
        )
        prompt = self._build_task_prompt(task_slug, task_file, exec_root)

        prog_model = self.config.resolve_programmer_model(self.root)
        prog_effort = self.config.resolve_programmer_effort(self.root)
        cmd = build_agy_command(prog_model, prog_effort, mode="auto")
        sync_script = (
            exec_root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "sync_task_status.py"
        )
        if worktree_dir is None and sync_script.is_file():
            subprocess.run(
                [sys.executable, "-B", str(sync_script), "task", task_slug, "in-progress"],
                cwd=exec_root,
                capture_output=True,
                check=False,
            )
        active_dispatcher = dispatcher or self.dispatcher
        exit_code, stdout, stderr = active_dispatcher.dispatch(
            cli=cmd[0],
            args=cmd[1:],
            prompt=prompt,
        )

        # Keep task logs under self.root (epic worktree), never polluting isolated slot commits
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

        # Mark task done via sync_task_status.py if present in exec_root
        if sync_script.is_file():
            subprocess.run(
                [sys.executable, "-B", str(sync_script), "task", task_slug, "done"],
                cwd=exec_root,
                capture_output=True,
                check=False,
            )

        # Commit task changes inside exec_root if git repository
        if self._is_git_repo(exec_root):
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=exec_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if status_res.returncode == 0 and status_res.stdout.strip():
                add_res = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=exec_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if add_res.returncode != 0:
                    return False
                commit_title = f"[{self.epic_slug.upper()}] Execute {task_slug}"
                commit_res = subprocess.run(
                    ["git", "commit", "-m", commit_title],
                    cwd=exec_root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if commit_res.returncode != 0:
                    return False

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
        prompt = (
            f"You are the AI Assistant (Role 2.2). Apply minor revisions for Principal Review round {round_num}.\n"
            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to address all minor review findings.\n"
        )
        self.dispatcher.dispatch(
            cli="agy",
            args=["--model", self.config.resolve_assistant_model(self.root), "--effort", self.config.assistant_effort, "--mode", "accept-edits"],
            prompt=prompt,
        )
        # 1. Commit technical revision edits first
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

        # 2. Record decision cells citing the fix commit SHA
        rev_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"

        file = self.root / ".devtool" / "epic" / self.epic_slug / "principal_review.md"
        if file.is_file():
            content = file.read_text(encoding="utf-8")
            lines = content.splitlines()
            in_target_round = False
            in_raw_output = False
            new_lines = []
            for line in lines:
                if line.startswith(f"## Round {round_num}"):
                    in_target_round = True
                elif line.startswith("## Round "):
                    in_target_round = False
                if in_target_round:
                    if line.startswith("Raw output:"):
                        in_raw_output = True
                    if not in_raw_output and re.match(r"^\|\s*\d+\s*\|", line):
                        parts = line.split("|")
                        if len(parts) >= 6:
                            current_dec = parts[-2].strip()
                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
                                parts[-2] = f" fixed in {sha_short} "
                                line = "|".join(parts)
                new_lines.append(line)
            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # 3. Commit review decisions separately
        dec_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if dec_status.returncode == 0 and dec_status.stdout.strip():
            subprocess.run(["git", "add", str(file)], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Record Principal Review decisions for round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def _apply_aligned_fixes(self, round_num: int) -> bool:
        """Apply aligned technical revisions and commit changes."""
        prompt = (
            f"You are the AI Assistant (Role 2.2). Apply aligned technical revisions for Principal Review round {round_num}.\n"
            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to align with verified findings.\n"
        )
        self.dispatcher.dispatch(
            cli="agy",
            args=["--model", self.config.resolve_assistant_model(self.root), "--effort", self.config.assistant_effort, "--mode", "accept-edits"],
            prompt=prompt,
        )
        # 1. Commit aligned revision edits first
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

        # 2. Record decision cells citing the fix commit SHA
        rev_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"

        file = self.root / ".devtool" / "epic" / self.epic_slug / "principal_review.md"
        if file.is_file():
            content = file.read_text(encoding="utf-8")
            lines = content.splitlines()
            in_target_round = False
            in_raw_output = False
            new_lines = []
            for line in lines:
                if line.startswith(f"## Round {round_num}"):
                    in_target_round = True
                elif line.startswith("## Round "):
                    in_target_round = False
                if in_target_round:
                    if line.startswith("Raw output:"):
                        in_raw_output = True
                    if not in_raw_output and re.match(r"^\|\s*\d+\s*\|", line):
                        parts = line.split("|")
                        if len(parts) >= 6:
                            current_dec = parts[-2].strip()
                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
                                parts[-2] = f" fixed in {sha_short} "
                                line = "|".join(parts)
                new_lines.append(line)
            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        # 3. Commit review decisions separately
        dec_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        if dec_status.returncode == 0 and dec_status.stdout.strip():
            subprocess.run(["git", "add", str(file)], cwd=self.root, check=False)
            commit_title = f"[{self.epic_slug.upper()}] Record Principal Review decisions for round {round_num}"
            subprocess.run(
                ["git", "commit", "-m", commit_title],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        return True

    def _run_package_epic_revise(self) -> bool:
        """Run initial package_epic.py <epic> or --revise when handoff.md exists, and commit."""
        pkg_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "package_epic.py"
        )
        if pkg_script.is_file():
            handoff_file = self.root / ".devtool" / "epic" / self.epic_slug / "handoff.md"
            cmd = [sys.executable, str(pkg_script), self.epic_slug]
            if handoff_file.is_file():
                cmd.extend(["--revise", "--reason", "Revise after Principal Review"])
            subprocess.run(cmd, cwd=self.root, capture_output=True, check=False)
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
                self._run_package_epic_revise()
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
                self._emit_review_phase_status("principal", "fixing", round_num)
                self._apply_aligned_fixes(round_num)
                self._emit_review_phase_status("principal", "verifying", round_num)
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

                self._emit_review_phase_status("principal", "fixing", round_num)
                self._apply_aligned_fixes(round_num)
                self._emit_review_phase_status("principal", "verifying", round_num)

        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        self.save_state()
        return False

    def _compute_parallel_batches(self) -> list[list[str]]:
        """Compute DAG wave batches via compute_execution_order.py --parallel --json."""
        script = self._resolve_script("dev-implementation/resources/scripts/compute_execution_order.py")
        if script is not None:
            cmd = [
                sys.executable,
                str(script),
                self.epic_slug,
                "--parallel",
                "--pool-size",
                "2",
                "--json",
            ]
            res = subprocess.run(cmd, cwd=self.root, capture_output=True, text=True, check=False)
            if res.returncode == 0 and res.stdout.strip():
                try:
                    payload = json.loads(res.stdout)
                    parallel_batches = payload.get("parallel_batches", [])
                    batches: list[list[str]] = []
                    for layer in parallel_batches:
                        if isinstance(layer, list):
                            for batch in layer:
                                if isinstance(batch, list) and batch:
                                    batches.append([str(t) for t in batch])
                    if batches:
                        flat = [t for batch in batches for t in batch]
                        if not self.state.task_order:
                            self.state.task_order = flat
                            self.sync_gate_ledger(
                                3,
                                f"Topological execution order computed and confirmed: {' -> '.join(flat)}",
                            )
                            self.save_state()
                        return batches
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        if not self.state.task_order:
            self.resolve_gate3_order()
        return [[t] for t in self.state.task_order]

    def _resolve_epic_base_ref(self, repo_root: Path, epic_wt: Path) -> str:
        """Resolve git base ref for pool slot creation and wave sync."""
        epic_branch = f"epic/{self.epic_slug}"
        verify_epic = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", epic_branch],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if verify_epic.returncode == 0:
            return epic_branch
        head_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=epic_wt if epic_wt.is_dir() else repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        branch = head_res.stdout.strip() if head_res.returncode == 0 else ""
        if branch and branch != "HEAD":
            return branch
        return "HEAD"

    def _make_slot_dispatcher(self, slot_path: Path) -> ModelDispatcher:
        """Construct a slot-bound ModelDispatcher unless instance dispatcher was monkeypatched."""
        if not isinstance(self.dispatcher, ModelDispatcher) or "dispatch" in self.dispatcher.__dict__:
            return self.dispatcher
        return ModelDispatcher(
            worktree_dir=slot_path,
            timeout_seconds=self.config.timeout_seconds,
        )

    def _run_pool_batch(
        self,
        pool_mod: Any,
        repo_root: Path,
        epic_wt: Path,
        epic_branch: str,
        pending_batch: list[str],
        wave_num: int | None = None,
    ) -> bool:
        """Execute one DAG wave batch across isolated pool slots and serialize merges."""
        for slot_idx, task_slug in enumerate(pending_batch, start=1):
            if not pool_mod.sync_slot(
                repo_root,
                self.epic_slug,
                self.epic_slug,
                slot=slot_idx,
                base_ref=epic_branch,
                task_id=task_slug,
                active_wave=wave_num,
                status="working",
            ):
                self.state.last_error = f"Failed to sync pool slot {slot_idx} to {epic_branch}"
                self.save_state()
                return False

        def run_in_slot(slot_idx: int, task_slug: str) -> tuple[int, str, bool]:
            slot_path = pool_mod.get_slot_path(repo_root, self.epic_slug, slot_idx)
            slot_dispatcher = self._make_slot_dispatcher(slot_path)
            ok = self._execute_single_task(
                task_slug,
                worktree_dir=slot_path,
                dispatcher=slot_dispatcher,
            )
            return slot_idx, task_slug, ok

        results: list[tuple[int, str, bool]] = []
        if len(pending_batch) == 1:
            results.append(run_in_slot(1, pending_batch[0]))
        else:
            with ThreadPoolExecutor(max_workers=len(pending_batch)) as executor:
                futures = [
                    executor.submit(run_in_slot, idx, task_slug)
                    for idx, task_slug in enumerate(pending_batch, start=1)
                ]
                for future in futures:
                    results.append(future.result())

        # Serialize merges into epic_wt under explicit lock; rollback & fail on error
        merge_lock = threading.Lock()
        for slot_idx, task_slug, ok in sorted(results, key=lambda item: item[0]):
            if not ok:
                pool_mod.sync_slot(
                    repo_root,
                    self.epic_slug,
                    self.epic_slug,
                    slot=slot_idx,
                    base_ref=epic_branch,
                    status="idle",
                )
                self.state.last_error = f"Task execution failed: {task_slug}"
                self.save_state()
                return False

            with merge_lock:
                merged = pool_mod.merge_slot(
                    repo_root,
                    self.epic_slug,
                    self.epic_slug,
                    slot=slot_idx,
                    task_id=task_slug,
                    epic_worktree_root=epic_wt,
                    active_wave=wave_num,
                )
            if not merged:
                pool_mod.sync_slot(
                    repo_root,
                    self.epic_slug,
                    self.epic_slug,
                    slot=slot_idx,
                    base_ref=epic_branch,
                    status="idle",
                )
                self.state.last_error = f"Slot {slot_idx} merge failed for task {task_slug}"
                self.save_state()
                return False

            if task_slug not in self.state.completed_tasks:
                self.state.completed_tasks.append(task_slug)
            self.save_state()

        return True

    def step_implementation(self) -> bool:
        """Execute Stage 3 autonomous task execution loop with pool isolation in git repos."""
        self.state.active_stage = StageName.IMPLEMENTATION.value
        use_pool = (
            self._is_git_repo(self.root)
            and "_execute_single_task" not in self.__dict__
        )
        pool_mod = self._load_pool_module() if use_pool else None

        if pool_mod is None:
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

        batches = self._compute_parallel_batches()
        if not batches:
            self.state.last_error = "Failed to resolve Gate 3 execution order"
            self.save_state()
            return False

        pending_batches = [
            (wave_idx, [t for t in batch if t not in self.state.completed_tasks])
            for wave_idx, batch in enumerate(batches, start=1)
        ]
        pending_batches = [(wave_idx, b) for wave_idx, b in pending_batches if b]
        if not pending_batches:
            return True

        repo_root, resolved_wt = pool_mod.resolve_pool_roots(self.root, self.epic_slug)
        epic_wt = resolved_wt if resolved_wt.is_dir() else self.root
        epic_branch = self._resolve_epic_base_ref(repo_root, epic_wt)
        pool_size = max(2, max((len(b) for _, b in pending_batches), default=2))

        pool_mod.init_slots(
            repo_root,
            self.epic_slug,
            self.epic_slug,
            pool_size=pool_size,
            base_ref=epic_branch,
            epic_worktree_root=epic_wt,
        )
        try:
            for wave_num, pending_batch in pending_batches:
                if not self._run_pool_batch(
                    pool_mod,
                    repo_root,
                    epic_wt,
                    epic_branch,
                    pending_batch,
                    wave_num=wave_num,
                ):
                    return False
        finally:
            pool_mod.cleanup_slots(
                repo_root,
                self.epic_slug,
                self.epic_slug,
                pool_size=pool_size,
            )

        return True

    def run_gate4(self) -> tuple[bool, str]:
        """Execute complete Stage 3 Gate 4 verification sequence on candidate SHA."""
        # 1. Smoke checklist generation
        smoke_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "generate_smoke_checklist.py"
        )
        if smoke_script.is_file():
            res = subprocess.run(
                [sys.executable, str(smoke_script), "--epic-dir", self.epic_slug],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                raw_err = res.stderr.strip() or res.stdout.strip() or f"exit code {res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Smoke checklist generation failed: {err}"

        # 2. Review decisions check
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
                text=True,
                check=False,
            )
            if chk_res.returncode != 0:
                raw_err = chk_res.stderr.strip() or chk_res.stdout.strip() or f"exit code {chk_res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Review decisions check failed: {err}"

        # 3. Code and security audit checks via audit_epic.py
        audit_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "audit_epic.py"
        )
        if audit_script.is_file():
            audit_res = subprocess.run(
                [sys.executable, str(audit_script), "--epic-dir", self.epic_slug, "--base", self.config.base_branch],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if audit_res.returncode != 0:
                raw_err = audit_res.stderr.strip() or audit_res.stdout.strip() or f"exit code {audit_res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Epic audit failed: {err}"

        # 4. HLD Integration results and result-based BDD traceability
        hld_file = self.root / ".devtool" / "epic" / self.epic_slug / f"{self.epic_slug}.en.md"
        if hld_file.is_file():
            content = hld_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("Integration results:"):
                    cmd_part = line[len("Integration results:"):].strip()
                    cmd_str = cmd_part.split("->")[0].strip() if "->" in cmd_part else cmd_part
                    if cmd_str:
                        integ_res = subprocess.run(
                            cmd_str,
                            shell=True,
                            cwd=self.root,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if integ_res.returncode != 0:
                            raw_err = integ_res.stderr.strip() or integ_res.stdout.strip() or f"exit code {integ_res.returncode}"
                            err = self._tail_lines(raw_err, 25) or raw_err
                            return False, f"Integration test execution failed: {err}"

        bdd_script = (
            self.root
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "check_bdd_traceability.py"
        )
        if bdd_script.is_file():
            scenarios_file = self.root / ".devtool" / "epic" / self.epic_slug / "bdd_scenarios.en.md"
            bdd_cmd = [sys.executable, str(bdd_script), "tests", "--roots", "tests"]
            if scenarios_file.is_file():
                bdd_cmd.extend(["--scenarios", str(scenarios_file)])
            report_file = self.root / "build" / "test-results" / "autonomous-lifecycle-runner.xml"
            if report_file.is_file():
                bdd_cmd.extend(["--results", str(report_file)])
            bdd_res = subprocess.run(
                bdd_cmd,
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if bdd_res.returncode != 0:
                raw_err = bdd_res.stderr.strip() or bdd_res.stdout.strip() or f"exit code {bdd_res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"BDD traceability check failed: {err}"

        # 5. Quality check verification
        verify_script = self.root / "scripts" / "verify.sh"
        if verify_script.is_file():
            q_res = subprocess.run(
                ["bash", str(verify_script), "--quiet"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if q_res.returncode != 0:
                raw_err = q_res.stderr.strip() or q_res.stdout.strip() or f"exit code {q_res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Quality check verification failed: {err}"

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

    def run_intermediate_check(self) -> tuple[bool, str]:
        """Execute fast scoped checks during intermediate review-remediation rounds.

        Enforces Scoped Tests Protocol:
        - Only fast static checks and review decisions check.
        - Strictly forbids full Gate 4, repo-wide pytest discoveries, and Playwright E2E suites.
        - Full regression and machine acceptance run strictly at Final Convergence Gate.
        """
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
                text=True,
                check=False,
            )
            if chk_res.returncode != 0:
                raw_err = chk_res.stderr.strip() or chk_res.stdout.strip() or f"exit code {chk_res.returncode}"
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Review decisions check failed: {err}"
        return True, "Intermediate scoped check PASS"

    def _draft_fix_plan(self, round_num: int, triage_stdout: str) -> str:
        """Draft fix plan markdown file for the given review round via AI Programmer dispatch."""
        file = self.root / ".devtool" / "epic" / self.epic_slug / f"fix_plan_round{round_num}.md"
        file.parent.mkdir(parents=True, exist_ok=True)
        prompt = (
            f"You are the AI Programmer (Role 2.3). Draft an actionable fix plan for Cross-Model Review Round {round_num}.\n"
            f"Triage Findings:\n\n{triage_stdout}\n\n"
            f"Specify exact file modifications, functions, and unit tests to add/update.\n"
        )
        prog_model = self.config.resolve_programmer_model(self.root)
        prog_effort = self.config.resolve_programmer_effort(self.root)
        cmd = build_agy_command(prog_model, prog_effort, mode="plan")
        code, stdout, _ = self.dispatcher.dispatch(
            cli=cmd[0],
            args=cmd[1:],
            prompt=prompt,
        )
        content = stdout.strip() if (code == 0 and stdout.strip()) else f"# Fix Plan Round {round_num}\n\n## Triaged Findings\n\n{triage_stdout}\n"
        try:
            file.write_text(content, encoding="utf-8")
        except OSError:
            pass
        return content

    def _run_scoped_tests(
        self,
        findings: list[dict[str, str]] | None = None,
    ) -> tuple[bool, str]:
        """Run fast syntax and targeted unit checks covering modified modules."""
        candidate_py: list[Path] = []
        if findings:
            for item in findings:
                raw_target = item.get("target", "").strip().strip("`")
                rel_path = re.split(r"[:#]", raw_target, maxsplit=1)[0].strip()
                if rel_path.endswith(".py"):
                    p = self.root / rel_path
                    if p.is_file() and p not in candidate_py:
                        candidate_py.append(p)

        if self._is_git_repo(self.root):
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if status_res.returncode == 0:
                for line in status_res.stdout.splitlines():
                    if len(line) >= 4:
                        rel = line[3:].strip().split(" -> ")[-1]
                        if rel.endswith(".py"):
                            p = self.root / rel
                            if p.is_file() and p not in candidate_py:
                                candidate_py.append(p)

        if candidate_py:
            comp_res = subprocess.run(
                [sys.executable, "-m", "py_compile", *[str(p) for p in candidate_py]],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if comp_res.returncode != 0:
                raw_err = comp_res.stderr.strip() or comp_res.stdout.strip() or "py_compile failed"
                return False, _tail_lines(raw_err, 25) or raw_err

        matched_tests: list[Path] = []
        tests_dir = self.root / "tests"
        if tests_dir.is_dir() and candidate_py:
            for py_path in candidate_py:
                if py_path.name.startswith("test_"):
                    if py_path not in matched_tests:
                        matched_tests.append(py_path)
                    continue
                t_file = tests_dir / f"test_{py_path.stem}.py"
                if t_file.is_file() and t_file not in matched_tests:
                    matched_tests.append(t_file)

        if matched_tests:
            test_res = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "--tb=short", *[str(t) for t in matched_tests]],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if test_res.returncode != 0:
                raw_err = test_res.stderr.strip() or test_res.stdout.strip() or "scoped pytest failed"
                return False, _tail_lines(raw_err, 25) or raw_err

        return True, "Scoped checks PASS"

    def _emit_review_phase_status(self, kind: str, phase: str, round_num: int) -> None:
        """Emit mechanical review phase telemetry via run_external_review.py status."""
        script = self._resolve_script("dev-implementation/resources/scripts/run_external_review.py")
        if script is None:
            return
        try:
            subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "status",
                    "--kind",
                    kind,
                    "--epic-dir",
                    self.epic_slug,
                    "--phase",
                    phase,
                    "--round",
                    str(round_num),
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception:
            pass

    def _apply_code_fixes(
        self,
        round_num: int,
        plan_text: str = "",
        findings: list[dict[str, str]] | None = None,
        review_artifact: Path | None = None,
    ) -> bool:
        """Apply verified code fixes aligned to HLD/BDD/specs, run scoped tests, and commit."""
        epic_dir = self.root / ".devtool" / "epic" / self.epic_slug
        anchor_candidates = [
            epic_dir / f"{self.epic_slug}.en.md",
            epic_dir / "hld.en.md",
            epic_dir / "bdd_scenarios.en.md",
            review_artifact or (epic_dir / "review_results.md"),
        ]
        if epic_dir.is_dir():
            for extra in sorted(epic_dir.glob("*design*.md")):
                if extra not in anchor_candidates:
                    anchor_candidates.append(extra)

        anchors: list[str] = []
        for candidate in anchor_candidates:
            if candidate.is_file():
                try:
                    anchors.append(str(candidate.relative_to(self.root)))
                except ValueError:
                    anchors.append(str(candidate))

        prompt_parts = [
            f"You are the AI Programmer (Role 2.3). Implement verified fixes for Cross-Model Review Round {round_num}.",
        ]
        if anchors:
            prompt_parts.append("Design/BDD/Review anchor paths (read bounded as needed):")
            prompt_parts.extend(f"- `{a}`" for a in anchors)
        if findings:
            prompt_parts.append("Verified Findings:")
            for item in findings:
                fid = item.get("id", "-")
                sev = item.get("severity", "Unknown")
                tgt = item.get("target", "")
                prob = item.get("problem", "")
                prompt_parts.append(f"- [{fid}] ({sev}) `{tgt}`: {prob}")
        if plan_text.strip():
            prompt_parts.append(f"Approved Fix Plan:\n{plan_text.strip()}")
        prompt_parts.append("Constraints: Strict TDD. Do not invoke d3nexus:task-observer.")
        prompt_parts.append("Output cap (Zero-Fluff): Reply ONLY with modified file paths, pass/fail test counts, and blocking errors.")
        prompt = "\n".join(prompt_parts) + "\n"

        prog_model = self.config.resolve_programmer_model(self.root)
        prog_effort = self.config.resolve_programmer_effort(self.root)
        self._emit_review_phase_status("code", "fixing", round_num)
        cmd = build_agy_command(prog_model, prog_effort, mode="accept-edits")
        exit_code, stdout, stderr = self.dispatcher.dispatch(
            cli=cmd[0],
            args=cmd[1:],
            prompt=prompt,
        )
        if exit_code != 0:
            raw_err = stderr.strip() or stdout.strip() or f"exit code {exit_code}"
            self.state.last_error = f"Code fix dispatch failed in round {round_num}: {_tail_lines(raw_err, 25) or raw_err}"
            return False

        self._emit_review_phase_status("code", "verifying", round_num)
        scoped_ok, scoped_msg = self._run_scoped_tests(findings=findings)
        if not scoped_ok:
            self.state.last_error = f"Scoped tests failed after round {round_num} fixes: {scoped_msg}"
            return False

        if self._is_git_repo(self.root):
            status_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if status_res.returncode == 0 and status_res.stdout.strip():
                add_res = subprocess.run(
                    ["git", "add", "-A"],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if add_res.returncode != 0:
                    return False
                commit_title = f"[{self.epic_slug.upper()}] Apply code fixes for Cross-Model Review round {round_num}"
                commit_res = subprocess.run(
                    ["git", "commit", "-m", commit_title],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if commit_res.returncode != 0:
                    return False
        return True

    def _record_review_decisions(self, round_num: int) -> bool:
        """Record review decision cells and commit decisions."""
        file = self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
        if file.is_file():
            content = file.read_text(encoding="utf-8")
            rev_res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            sha_short = rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"
            lines = content.splitlines()
            in_target_round = False
            in_raw_output = False
            in_fence = False
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("```"):
                    in_fence = not in_fence
                if line.startswith(f"## Round {round_num}"):
                    in_target_round = True
                    in_raw_output = False
                elif line.startswith("## Round "):
                    in_target_round = False
                    in_raw_output = False
                if in_target_round:
                    if stripped.startswith("Raw output:"):
                        in_raw_output = True
                    if (
                        not in_raw_output
                        and not in_fence
                        and re.match(r"^\|\s*(?:\d+|[A-Za-z]+-\d+)\s*\|", line)
                    ):
                        parts = line.split("|")
                        if len(parts) >= 6:
                            current_dec = parts[-2].strip()
                            if not current_dec.startswith(("fixed in ", "dismissed: ")):
                                parts[-2] = f" fixed in {sha_short} "
                                line = "|".join(parts)
                new_lines.append(line)
            file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

        if self._is_git_repo(self.root):
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

    def _parse_finding_rows(
        self,
        markdown_text: str,
        stage_label: str,
        target_round: int | None = None,
    ) -> list[dict[str, str]]:
        """Parse finding rows from review markdown while ignoring fenced Raw output blocks."""
        findings: list[dict[str, str]] = []
        current_round_num: int | None = None
        current_round_label = "Round 1"
        current_sha = ""
        in_fence = False
        in_raw_output = False

        round_re = re.compile(r"^##\s+Round\s+(\d+)\b")
        sha_re = re.compile(r"(?:Candidate\s+)?SHA\s*:\s*`?([0-9a-fA-F]{7,40})`?", re.IGNORECASE)

        for raw_line in markdown_text.splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue

            r_match = round_re.match(stripped)
            if r_match:
                current_round_num = int(r_match.group(1))
                current_round_label = f"Round {current_round_num}"
                current_sha = ""
                in_raw_output = False
                continue

            if stripped.startswith("Raw output:"):
                in_raw_output = True
                continue

            if in_fence or in_raw_output:
                continue

            if target_round is not None and current_round_num != target_round:
                continue

            sha_match = sha_re.search(stripped)
            if sha_match:
                current_sha = sha_match.group(1)[:7]
                continue

            if not (stripped.startswith("|") and stripped.endswith("|")):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 4:
                continue
            if all(re.fullmatch(r"[:\-\s]+", c or "-") for c in cells):
                continue
            if cells[0].lower() in {"id", "#", "finding", "item"}:
                continue

            fid = cells[0]
            sev = "Important"
            target = ""
            problem = ""
            status = cells[-1]

            if len(cells) >= 5 and cells[1].lower() in {"critical", "important", "minor"}:
                sev = cells[1].capitalize()
                target = cells[2].strip("`")
                problem = cells[3]
            elif cells[2].lower() in {"critical", "important", "minor"}:
                sev = cells[2].capitalize()
                target = cells[1].strip("`")
                problem = cells[3] if len(cells) > 4 else cells[1]
            else:
                sev = cells[1] if len(cells) > 1 else "Important"
                target = cells[2].strip("`") if len(cells) > 2 else ""
                problem = cells[3] if len(cells) > 3 else ""

            findings.append(
                {
                    "id": fid,
                    "stage": stage_label,
                    "round": current_round_label,
                    "round_num": str(current_round_num or 1),
                    "sha": current_sha,
                    "severity": sev,
                    "target": target,
                    "problem": problem,
                    "status": status,
                }
            )

        return findings

    def _extract_cross_model_findings(
        self,
        round_num: int,
        triage_stdout: str,
    ) -> list[dict[str, str]]:
        """Extract open Cross-Model findings for `round_num` from review_results.md and triage output."""
        findings: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        review_file = self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
        if review_file.is_file():
            try:
                parsed = self._parse_finding_rows(
                    review_file.read_text(encoding="utf-8"),
                    stage_label="Cross-Model",
                    target_round=round_num,
                )
                for item in parsed:
                    st = item.get("status", "").strip().lower()
                    if st.startswith(("fixed", "dismissed", "resolved", "closed")):
                        continue
                    key = (item.get("target", ""), item.get("problem", ""))
                    if key not in seen:
                        seen.add(key)
                        findings.append(item)
            except OSError:
                pass

        if triage_stdout.strip():
            parsed_triage = self._parse_finding_rows(
                triage_stdout,
                stage_label="Cross-Model",
                target_round=None,
            )
            for item in parsed_triage:
                st = item.get("status", "").strip().lower()
                if st.startswith(("fixed", "dismissed", "resolved", "closed")):
                    continue
                key = (item.get("target", ""), item.get("problem", ""))
                if key not in seen:
                    seen.add(key)
                    findings.append(item)

        return findings

    def _can_fast_track_code_findings(
        self,
        findings: list[dict[str, str]],
        triage_stdout: str,
    ) -> bool:
        """Return True only when all open findings verify cleanly against real non-contract source files."""
        if not findings:
            return False

        escalation_markers = (
            "shared-contracts",
            "shared_contracts",
            "critical_conflict",
            "shared_contract_conflict",
            "debatable",
            "ambiguous",
            "architectural state transition",
            "trade-off",
            "tradeoff",
            "not shown",
            "false positive",
        )
        triage_lower = triage_stdout.lower()
        if any(marker in triage_lower for marker in escalation_markers):
            return False

        for item in findings:
            sev = item.get("severity", "").strip().lower()
            if sev not in {"critical", "important", "minor"}:
                return False

            combined = " ".join(
                [item.get("target", ""), item.get("problem", ""), item.get("status", "")]
            ).lower()
            if any(marker in combined for marker in escalation_markers):
                return False

            raw_target = item.get("target", "").strip().strip("`")
            if not raw_target:
                return False
            path_part = re.split(r"[:#]", raw_target, maxsplit=1)[0].strip()
            line_part = raw_target[len(path_part) + 1:].strip() if len(raw_target) > len(path_part) else ""

            if (
                not path_part
                or path_part.endswith(".md")
                or path_part.startswith((".devtool/", "shared-contracts/", "shared_contracts/"))
            ):
                return False

            target_path = self.root / path_part
            if not target_path.is_file():
                return False

            line_num_match = re.match(r"^L?(\d+)", line_part)
            if line_num_match:
                line_num = int(line_num_match.group(1))
                try:
                    total_lines = len(target_path.read_text(encoding="utf-8").splitlines())
                except OSError:
                    return False
                if line_num < 1 or line_num > total_lines:
                    return False

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
        code, stdout, stderr = self.dispatcher.dispatch(
            cli="agy",
            args=["--model", assistant_model, "--effort", self.config.assistant_effort, "--mode", "auto"],
            prompt=prompt,
        )
        if code != 0 or not stdout.strip():
            err_msg = stderr.strip() or f"Assistant dispatch failed with exit code {code}"
            return FixPlanVerdict.CRITICAL_CONFLICT, f"Fix plan evaluation failed: {err_msg}"

        first_line = stdout.strip().splitlines()[0].strip().upper()
        rationale = (
            "\n".join(stdout.strip().splitlines()[1:]).strip()
            if "\n" in stdout.strip()
            else stdout.strip()
        )
        if "CRITICAL_CONFLICT" in first_line:
            return FixPlanVerdict.CRITICAL_CONFLICT, rationale
        if "ADJUSTED" in first_line:
            return FixPlanVerdict.ADJUSTED, rationale
        if "APPROVED" in first_line:
            return FixPlanVerdict.APPROVED, rationale
        return (
            FixPlanVerdict.CRITICAL_CONFLICT,
            f"Unparseable fix plan verdict from Assistant (expected APPROVED, ADJUSTED, or CRITICAL_CONFLICT): {first_line}\n{rationale}",
        )

    def step_cross_model_review(self) -> bool:
        """Execute Stage 3 Cross-Model Review loop with verified fast-track code fixes."""
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

            review_artifact = self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
            findings = self._extract_cross_model_findings(round_num, triage_stdout)

            if action == "AUTO_PASS_FINAL_MINOR_SWEEP":
                print("AUTO_PASS_FINAL_MINOR_SWEEP: Sweeping minor findings in single pass...")
                if not self._apply_code_fixes(
                    round_num,
                    findings=findings or None,
                    review_artifact=review_artifact if review_artifact.is_file() else None,
                ):
                    self.save_state()
                    return False
                self._record_review_decisions(round_num)
                gate4_ok, _ = self.run_gate4()
                if gate4_ok:
                    self.state.active_stage = StageName.AWAITING_FINISH.value
                    self.save_state()
                    return True
                return False

            if action == "AUTO_PASS_FINAL_SWEEP":
                print("AUTO_PASS_FINAL_SWEEP: Final review round sweep...")
                if not self._apply_code_fixes(
                    round_num,
                    findings=findings or None,
                    review_artifact=review_artifact if review_artifact.is_file() else None,
                ):
                    self.save_state()
                    return False
                self._record_review_decisions(round_num)
                gate4_ok, _ = self.run_gate4()
                if gate4_ok:
                    self.state.active_stage = StageName.AWAITING_FINISH.value
                    self.save_state()
                    return True
                return False

            if action == "AUTO_FIX_ELIGIBLE":
                if self._can_fast_track_code_findings(findings, triage_stdout):
                    applied = self._apply_code_fixes(
                        round_num,
                        findings=findings,
                        review_artifact=review_artifact if review_artifact.is_file() else None,
                    )
                else:
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

                    applied = self._apply_code_fixes(
                        round_num,
                        plan_text=rationale if verdict == FixPlanVerdict.ADJUSTED else "",
                        findings=findings or None,
                        review_artifact=review_artifact if review_artifact.is_file() else None,
                    )

                if not applied:
                    self.save_state()
                    return False

                self._record_review_decisions(round_num)

                # Run intermediate scoped verification (reserve full Gate 4 for final convergence)
                scoped_ok, msg = self.run_intermediate_check()
                if not scoped_ok:
                    self.state.last_error = f"Intermediate scoped check failed after round {round_num} fixes: {msg}"
                    self.save_state()
                    return False

        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        self.save_state()
        return False

    def _collect_report_findings(self) -> list[dict[str, str]]:
        """Collect real findings across principal_review.md and review_results.md ranked by risk."""
        epic_dir = self.root / ".devtool" / "epic" / self.epic_slug
        collected: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()

        for filename, stage_label in (
            ("review_results.md", "Cross-Model"),
            ("principal_review.md", "Principal"),
        ):
            artifact = epic_dir / filename
            if not artifact.is_file():
                continue
            try:
                parsed = self._parse_finding_rows(
                    artifact.read_text(encoding="utf-8"),
                    stage_label=stage_label,
                    target_round=None,
                )
            except OSError:
                continue
            for item in parsed:
                key = (item.get("target", ""), item.get("problem", ""))
                if key not in seen:
                    seen.add(key)
                    collected.append(item)

        sev_rank = {"critical": 0, "important": 1, "minor": 2}
        risk_keywords = (
            "shared-contracts",
            "security",
            "race",
            "concurrency",
            "worktree",
            "crash",
            "null",
            "lease",
            "timeout",
            "corruption",
            "auth",
        )

        def sort_key(item: dict[str, str]) -> tuple[int, int, int, int]:
            sev = item.get("severity", "").strip().lower()
            s_rank = sev_rank.get(sev, 3)
            st = item.get("status", "").strip().lower()
            open_rank = 0 if st in {"", "open", "pending"} else 1
            prob_lower = (item.get("problem", "") + " " + item.get("target", "")).lower()
            kw_rank = 0 if any(kw in prob_lower for kw in risk_keywords) else 1
            r_num = int(item.get("round_num", "1") or "1")
            return (s_rank, open_rank, kw_rank, -r_num)

        return sorted(collected, key=sort_key)

    def render_final_executive_report(self) -> str:
        """Render final executive markdown report synthesizing real findings across all rounds."""
        candidate_sha = self.state.last_commit_sha or ""
        if not candidate_sha and self._is_git_repo(self.root):
            rev_res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if rev_res.returncode == 0 and rev_res.stdout.strip():
                candidate_sha = rev_res.stdout.strip()
        if not candidate_sha:
            candidate_sha = "HEAD"

        lines = [
            f"# Executive Review Report: Epic '{self.epic_slug}'",
            "",
            "## Review Lifecycle Summary",
            f"- **Principal Review Rounds**: {self.state.principal_round} / {self.config.max_review_rounds}",
            f"- **Cross-Model Review Rounds**: {self.state.cross_model_round} / {self.config.max_review_rounds}",
            f"- **Candidate SHA**: `{candidate_sha}`",
            "- **Gate 4 Status**: PASS (Candidate certified)",
            f"- **Completed Tasks ({len(self.state.completed_tasks)})**: {', '.join(self.state.completed_tasks)}",
            "",
            "## Top 3 Highest-Risk Findings (Synthesized Across All Rounds)",
            "",
            "| # | Round | Area / Path | Risk / Severity | Resolution / Status |",
            "|---|-------|-------------|-----------------|---------------------|",
        ]

        top_findings = self._collect_report_findings()[:3]
        if top_findings:
            for idx, item in enumerate(top_findings, start=1):
                r_label = f"{item.get('stage', 'Review')} {item.get('round', 'Round 1')}"
                area = item.get("target") or item.get("id") or "Repository"
                fid = item.get("id", "").strip()
                if fid and fid not in area:
                    area = f"{fid}: {area}"
                sev = item.get("severity", "Important")
                prob = item.get("problem", "").replace("|", "/")
                risk_col = f"{sev} ({prob})" if prob else sev
                status = item.get("status") or "Open"
                sha = item.get("sha", "")
                if sha and sha not in status:
                    status = f"{status} (Candidate `{sha}`)"
                lines.append(f"| {idx} | {r_label} | {area} | {risk_col} | {status} |")
        else:
            lines.append("| 1 | All Rounds | Reviewed Epic & Repository Artifacts | 0 Open High-Risk Findings | Gate 4 Verified |")

        lines.extend(
            [
                "",
                "## Gate 5 Candidate Readiness",
                "- Pipeline State: `AWAITING_FINISH`",
                "- Next Action: Proceed to `/finishing-a-development-branch` to review, squash/merge to local base branch, and archive epic.",
            ]
        )
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
    parser.add_argument("--base", default="main", help="Base branch name (default: main)")
    parser.add_argument("--programmer-model", default=None, help="CLI override model for Programmer")
    parser.add_argument("--programmer-effort", default=None, help="CLI override reasoning effort for Programmer")
    parser.add_argument("--assistant-model", default=None, help="Model override for Assistant")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without running subprocesses")
    args = parser.parse_args()

    cfg = RunnerConfig(
        programmer_model=args.programmer_model,
        programmer_effort=args.programmer_effort,
        assistant_model=args.assistant_model,
        base_branch=args.base,
    )
    if args.config and args.config.is_file():
        try:
            cdata = json.loads(args.config.read_text(encoding="utf-8"))
            if "programmer_model" in cdata and isinstance(cdata["programmer_model"], str):
                cfg.config_programmer_model = cdata["programmer_model"]
            if "programmer_effort" in cdata and isinstance(cdata["programmer_effort"], str):
                cfg.config_programmer_effort = cdata["programmer_effort"]
            elif "thinking_level" in cdata and isinstance(cdata["thinking_level"], str):
                cfg.config_programmer_effort = cdata["thinking_level"]
            if "assistant_model" in cdata and cfg.assistant_model is None:
                cfg.assistant_model = cdata["assistant_model"]
            if "assistant_effort" in cdata and isinstance(cdata["assistant_effort"], str):
                cfg.assistant_effort = cdata["assistant_effort"]
            if "timeout_seconds" in cdata:
                cfg.timeout_seconds = int(cdata["timeout_seconds"])
            if "max_review_rounds" in cdata:
                cfg.max_review_rounds = int(cdata["max_review_rounds"])
            if "provider_priority" in cdata:
                cfg.provider_priority = list(cdata["provider_priority"])
            if "base_branch" in cdata and isinstance(cdata["base_branch"], str):
                cfg.base_branch = cdata["base_branch"]
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
