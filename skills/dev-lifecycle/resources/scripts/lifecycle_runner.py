#!/usr/bin/env python3
"""Autonomous Lifecycle Runner: Headless state machine orchestrator for multi-actor development lifecycles."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
import contextlib
import copy
import fcntl
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


KIT_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PROGRAMMER_MODEL = "gemini-4-hydrogen-xhigh"
DEFAULT_PROGRAMMER_EFFORT = "xhigh"
LEGACY_PROGRAMMER_MODELS = frozenset({"gemini-3.8-flash", "gemini-3.8-flash-high"})
EXTRA_EFFORT_ALIASES = frozenset({"extra", "extra-high", "extra_high", "xhigh"})
HALT_CRITERIA: tuple[str, ...] = (
    "CRITICAL_CONFLICT",
    "Debatable",
    "SHARED_CONTRACT_CONFLICT",
    "FIX_LOOP",
    "MAX_ROUNDS_CRITICAL_REMAINING",
)
_HIGH_RISK_LABELS: frozenset[str] = frozenset(
    {"security", "architecture", "concurrency", "contract"}
)
_MODULE_LOAD_LOCK = threading.Lock()


def _load_kit_module(name: str, rel_path: str) -> Any:
    """Load a sibling kit Python module by path, reusing sys.modules when present."""
    with _MODULE_LOAD_LOCK:
        existing = sys.modules.get(name)
        if existing is not None:
            return existing
        target = KIT_ROOT / rel_path
        if not target.is_file():
            raise RuntimeError(f"Required kit module not found: {target}")
        spec = importlib.util.spec_from_file_location(name, str(target))
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Failed to create module spec for {target}")
        mod = importlib.util.module_from_spec(spec)
        parent_str = str(target.parent)
        inserted = False
        if parent_str not in sys.path:
            sys.path.insert(0, parent_str)
            inserted = True
        try:
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
        except Exception:
            sys.modules.pop(name, None)
            raise
        finally:
            if inserted:
                with contextlib.suppress(ValueError):
                    sys.path.remove(parent_str)
        return mod


def _persona_config() -> Any:
    return _load_kit_module("persona_config", "scripts/persona_config.py")


def _dev_config() -> Any:
    return _load_kit_module("dev_config", "scripts/dev_config.py")


def _agy_dispatch() -> Any:
    return _load_kit_module("agy_dispatch", "scripts/agy_dispatch.py")


def _agy_pool() -> Any:
    return _load_kit_module("agy_profile_pool", "scripts/agy_profile_pool.py")


def _state_envelope() -> Any:
    return _load_kit_module("_state_envelope", "scripts/_state_envelope.py")


def _resume_context() -> Any:
    return _load_kit_module("resume_context", "scripts/resume_context.py")


def _epic_docs() -> Any:
    return _load_kit_module(
        "_epic_docs", "skills/dev-implementation/resources/scripts/_epic_docs.py"
    )


def _manage_worker_pool() -> Any:
    return _load_kit_module(
        "manage_worker_pool",
        "skills/dev-implementation/resources/scripts/manage_worker_pool.py",
    )


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


def _extract_last_fenced_json(text: str) -> dict[str, Any] | None:
    """Return the parsed JSON object from the last fenced ```json block, or None."""
    if not text:
        return None
    blocks = re.findall(
        r"```json\s*\n?(.*?)\n?```", text, flags=re.DOTALL | re.IGNORECASE
    )
    if not blocks:
        return None
    try:
        parsed = json.loads(blocks[-1].strip())
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _strip_yaml_inline_comment(value: str) -> str:
    """Strip an unquoted trailing `# ...` YAML comment while preserving quoted `#` characters."""
    in_single = False
    in_double = False
    escaped = False
    for idx, ch in enumerate(value):
        if escaped:
            escaped = False
            continue
        if in_double:
            if ch == "\\":
                escaped = True
            elif ch == '"':
                in_double = False
            continue
        if in_single:
            if ch == "'":
                in_single = False
            continue
        if ch == '"':
            in_double = True
        elif ch == "'":
            in_single = True
        elif ch == "#":
            return value[:idx].strip()
    return value.strip()


def _parse_task_frontmatter(task_file: Path | None) -> tuple[str, set[str]]:
    """Extract (review_tier, labels) from task markdown YAML frontmatter."""
    if task_file is None or not task_file.is_file():
        return "", set()
    try:
        lines = task_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return "", set()
    if not lines or lines[0].strip() != "---":
        return "", set()
    fm_lines: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            break
        fm_lines.append(line)

    review_tier = ""
    labels: set[str] = set()
    in_labels = False
    for raw in fm_lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("review_tier:"):
            in_labels = False
            raw_val = _strip_yaml_inline_comment(stripped.split(":", 1)[1])
            review_tier = raw_val.strip("'\"").lower()
            continue
        if stripped.startswith("labels:"):
            val = _strip_yaml_inline_comment(stripped.split(":", 1)[1])
            if val.startswith("[") and val.endswith("]"):
                in_labels = False
                for item in val[1:-1].split(","):
                    tok = item.strip().strip("'\"")
                    if tok:
                        labels.add(tok.lower())
            elif not val:
                in_labels = True
            else:
                in_labels = False
                tok = val.strip("'\"").lower()
                if tok:
                    labels.add(tok)
            continue
        if in_labels and stripped.startswith("- "):
            tok = _strip_yaml_inline_comment(stripped[2:]).strip("'\"").lower()
            if tok:
                labels.add(tok)
            continue
        if not raw.startswith((" ", "\t")):
            in_labels = False
    return review_tier, labels


def _is_non_test_module(rel_path: str) -> bool:
    """Return True when `rel_path` denotes a non-test implementation module."""
    norm = rel_path.strip().strip('"').replace("\\", "/")
    if not norm:
        return False
    if norm.startswith((".devtool/", "build/", ".git/")):
        return False
    parts = [p for p in norm.split("/") if p]
    if any(part in ("tests", "test", "__tests__") for part in parts):
        return False
    name = Path(norm).name.lower()
    return not (name.startswith("test_") or "_test." in name or ".test." in name)


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


@dataclass
class RunnerConfig:
    """Configuration settings for the Autonomous Lifecycle Runner."""

    programmer_model: str | None = None
    programmer_effort: str | None = None
    config_programmer_model: str | None = None
    config_programmer_effort: str | None = None
    architect_model: str | None = None
    architect_effort: str | None = None
    config_architect_model: str | None = None
    config_architect_effort: str | None = None
    assistant_model: str | None = None
    assistant_effort: str | None = None
    real_home: Path | None = None
    timeout_seconds: int = 1800
    max_review_rounds: int = 3
    provider_priority: list[str] | None = None
    base_branch: str = "main"

    def resolve_binding(self, persona: str, root: Path | None = None) -> Any:
        """Resolve PersonaBinding via CLI > --config > persona_config (project > global > kit)."""
        project_root = root if root is not None else Path.cwd()
        pc = _persona_config()

        if persona == "programmer":
            cli_model, cfg_model = self.programmer_model, self.config_programmer_model
            cli_effort, cfg_effort = (
                self.programmer_effort,
                self.config_programmer_effort,
            )
        elif persona == "ai_architect_reviewer":
            cli_model = self.architect_model or self.assistant_model
            cfg_model = self.config_architect_model
            cli_effort = self.architect_effort or self.assistant_effort
            cfg_effort = self.config_architect_effort
        else:
            cli_model = cfg_model = cli_effort = cfg_effort = None

        raw_model = next(
            (m.strip() for m in (cli_model, cfg_model) if isinstance(m, str) and m.strip()),
            None,
        )
        raw_effort = next(
            (
                e.strip()
                for e in (cli_effort, cfg_effort)
                if isinstance(e, str) and e.strip()
            ),
            None,
        )
        norm_effort = normalize_agy_effort(raw_effort) if raw_effort is not None else None

        cfg = pc.load_persona_config(project_root, real_home=self.real_home)
        base_binding = pc.resolve_persona(
            persona, project_root, real_home=self.real_home
        )
        if raw_model is None and norm_effort is None:
            return base_binding

        models: Mapping[str, Any] = cfg["models"]
        if raw_model is None:
            assert norm_effort is not None
            return pc.resolve_persona(
                persona,
                project_root,
                cli_overrides={"effort": norm_effort},
                real_home=self.real_home,
            )

        if raw_model in models:
            allowed = list(models[raw_model]["efforts"])
            chosen_effort = (
                norm_effort
                if norm_effort is not None
                else (
                    base_binding.effort
                    if base_binding.effort in allowed
                    else allowed[-1]
                )
            )
            return pc.resolve_persona(
                persona,
                project_root,
                cli_overrides={"model": raw_model, "effort": chosen_effort},
                real_home=self.real_home,
            )

        # Check if raw_model matches a catalogue model id (exact or template)
        for alias, entry in models.items():
            template = str(entry["id"])
            efforts = list(entry["efforts"])
            if "{effort}" in template:
                pattern = re.escape(template).replace(r"\{effort\}", r"([A-Za-z0-9_-]+)")
                match = re.fullmatch(pattern, raw_model)
                if match is not None:
                    raw_matched = match.group(1)
                    matched_eff = (
                        raw_matched
                        if raw_matched in efforts
                        else normalize_agy_effort(raw_matched)
                    )
                    chosen_effort = (
                        matched_eff
                        if matched_eff not in efforts
                        else (norm_effort or matched_eff)
                    )
                    return pc.resolve_persona(
                        persona,
                        project_root,
                        cli_overrides={"model": alias, "effort": chosen_effort},
                        real_home=self.real_home,
                    )
            elif template == raw_model:
                chosen_effort = norm_effort or (
                    base_binding.effort
                    if base_binding.effort in efforts
                    else efforts[-1]
                )
                return pc.resolve_persona(
                    persona,
                    project_root,
                    cli_overrides={"model": alias, "effort": chosen_effort},
                    real_home=self.real_home,
                )

        # Fallback kept strictly for uncatalogued custom raw model IDs (e.g. legacy/test IDs)

        sources = dict(base_binding.sources)
        sources["model"] = "cli"
        if norm_effort is not None:
            sources["effort"] = "cli"
        return pc.PersonaBinding(
            persona=persona,
            alias=raw_model,
            cli=base_binding.cli,
            model_id=raw_model,
            effort=norm_effort or base_binding.effort,
            quota_pool=base_binding.quota_pool,
            fallback_alias=base_binding.fallback_alias,
            sources=sources,
        )

    def resolve_programmer_model(self, root: Path | None = None) -> str:
        """Resolve Programmer model ID via RunnerConfig -> persona_config precedence."""
        return str(self.resolve_binding("programmer", root).model_id)

    def resolve_programmer_effort(self, root: Path | None = None) -> str:
        """Resolve Programmer reasoning effort via RunnerConfig -> persona_config precedence."""
        return str(self.resolve_binding("programmer", root).effort)

    def resolve_assistant_model(self, root: Path | None = None) -> str:
        """Resolve AI Architect & Reviewer model ID via RunnerConfig -> persona_config precedence."""
        return str(self.resolve_binding("ai_architect_reviewer", root).model_id)


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


def _extract_attempt_output_from_log(log_path: Path) -> str:
    """Extract stdout/stderr captured for the latest attempt in an agy_dispatch log."""
    if not log_path.is_file():
        return ""
    try:
        lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return ""
    start_idx: int | None = None
    for idx, line in enumerate(lines):
        if line.startswith("dispatch-profile: "):
            start_idx = idx + 1
    if start_idx is None:
        return "\n".join(lines)
    collected: list[str] = []
    for line in lines[start_idx:]:
        if line.startswith("agy-profile="):
            break
        collected.append(line)
    return "\n".join(collected)


class ModelDispatcher:
    """Supervises and dispatches headless model processes in isolated process groups."""

    def __init__(
        self,
        worktree_dir: Path,
        timeout_seconds: int = 1800,
        *,
        real_home: Path | None = None,
        pool_dispatcher: Any = None,
    ) -> None:
        self.worktree_dir = worktree_dir
        self.timeout_seconds = timeout_seconds
        self.real_home = real_home
        self.pool_dispatcher: Any = (
            pool_dispatcher
            if pool_dispatcher is not None
            else _agy_dispatch().run_on_pool
        )
        self._ctx_local = threading.local()
        self.last_dispatch_result: Any = None

    def set_dispatch_context(
        self,
        *,
        binding: Any,
        mode: str,
        owner: dict[str, Any],
        log_path: Path | None = None,
    ) -> None:
        """Bind persona metadata on the current thread for the next dispatch call."""
        self._ctx_local.context = {
            "binding": binding,
            "mode": mode,
            "owner": dict(owner),
            "log_path": log_path,
        }

    def clear_dispatch_context(self) -> None:
        """Clear thread-local persona dispatch metadata."""
        self._ctx_local.context = None

    def consume_last_dispatch_result(self) -> Any:
        """Return and clear the DispatchResult produced by the last dispatch on this thread."""
        res = getattr(self._ctx_local, "last_result", None)
        self._ctx_local.last_result = None
        return res

    def _resolve_pool_metadata(
        self, cli: str, args: list[str]
    ) -> tuple[Any, str, dict[str, Any], Path | None]:
        ctx = getattr(self._ctx_local, "context", None)
        if isinstance(ctx, dict):
            return (
                ctx["binding"],
                str(ctx["mode"]),
                dict(ctx["owner"]),
                ctx.get("log_path"),
            )
        pc = _persona_config()
        mode = (
            "read-only"
            if ("--sandbox" in args or "plan" in args or "read-only" in args)
            else "write"
        )
        model_id = (
            args[args.index("--model") + 1]
            if "--model" in args and args.index("--model") + 1 < len(args)
            else DEFAULT_PROGRAMMER_MODEL
        )
        effort = (
            args[args.index("--effort") + 1]
            if "--effort" in args and args.index("--effort") + 1 < len(args)
            else DEFAULT_PROGRAMMER_EFFORT
        )
        quota_pool = pc.derive_quota_pool({"cli": cli, "id": model_id}, model_id)
        binding = pc.PersonaBinding(
            persona="programmer",
            alias=model_id,
            cli=cli,
            model_id=model_id,
            effort=effort,
            quota_pool=quota_pool,
            fallback_alias=None,
            sources={"model": "cli", "effort": "cli"},
        )
        owner = {
            "repo": self.worktree_dir.name,
            "epic": "",
            "task": "",
            "slot": None,
            "role": "runner",
        }
        return binding, mode, owner, None

    def probe_model(self, cli: str, model: str) -> tuple[bool, str]:
        """Verify model capabilities via headless CLI before state initialization."""
        resolved_cli = (
            "kiro-cli"
            if cli == "kiro" and (shutil.which("kiro-cli") or not shutil.which("kiro"))
            else cli
        )
        if resolved_cli == "agy":
            cmd = [resolved_cli, "models"]
        else:
            cmd = [resolved_cli, "--version"]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.worktree_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                err = (
                    res.stderr.strip()
                    or res.stdout.strip()
                    or f"Exit code {res.returncode}"
                )
                return False, err

            if resolved_cli == "agy":
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
            return False, f"CLI binary '{resolved_cli}' not found on PATH"
        except Exception as exc:
            return False, f"Probing exception: {exc}"

    def _dispatch_via_pool(
        self, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        pc = _persona_config()
        resolved_home = pc.get_real_home(self.real_home)
        binding, mode, owner, explicit_log = self._resolve_pool_metadata(cli, args)
        with tempfile.TemporaryDirectory(prefix="d3_pool_disp_") as tmp_dir:
            tmp_path = Path(tmp_dir)
            prompt_path = tmp_path / "prompt.txt"
            prompt_path.write_text(prompt, encoding="utf-8")
            log_path = explicit_log if explicit_log is not None else (tmp_path / "dispatch.log")
            log_path.parent.mkdir(parents=True, exist_ok=True)
            res = self.pool_dispatcher(
                binding,
                mode,
                prompt_file=prompt_path,
                cwd=self.worktree_dir,
                log=log_path,
                owner=owner,
                real_home=resolved_home,
                timeout_seconds=self.timeout_seconds,
            )
            self._ctx_local.last_result = res
            self.last_dispatch_result = res
            status = str(getattr(res, "status", ""))
            report = list(getattr(res, "report", []) or [])
            reason = getattr(res, "reason", None)
            rc = int(getattr(res, "exit_code", 0))
            log_output = _extract_attempt_output_from_log(log_path)

        if status == "ok":
            return 0, log_output, ""
        if status == "task_failure":
            if reason == "timeout":
                timeout_err = (
                    "\n".join(report)
                    if report
                    else (
                        log_output.strip()
                        or f"Process timeout: execution timed out after {self.timeout_seconds}s"
                    )
                )
                return (rc or 1), log_output, timeout_err
            return (rc or 1), log_output, ""
        if status == "quota_midrun":
            return (rc or 1), log_output, "quota_midrun"
        if status in ("model_unavailable", "preflight_failed"):
            err_msg = "\n".join(report) if report else str(reason or status)
            return (rc or 1), "", err_msg
        if status == "no_profile":
            err_msg = "\n".join(report) if report else str(reason or "no_profile")
            return (rc or 2), "", err_msg
        return (rc or 1), log_output, "\n".join(report) if report else str(reason or "")

    def dispatch(self, cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        """Dispatch headless process with pool routing, dispatch env, process group isolation, and timeout supervision."""
        self._ctx_local.last_result = None
        self.last_dispatch_result = None

        pc = _persona_config()
        if cli == "agy":
            resolved_home = pc.get_real_home(self.real_home)
            pool_cfg = _agy_pool().load_pool_config(real_home=resolved_home)
            if pool_cfg.get("pool"):
                return self._dispatch_via_pool(cli, args, prompt)

        cmd = [cli] + args
        launch_env = pc.build_dispatch_env(cmd, os.environ)
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=self.worktree_dir,
                env=launch_env,
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
            stdout, stderr = proc.communicate(
                input=prompt, timeout=self.timeout_seconds
            )
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

            return (
                124,
                "",
                f"Process timeout: execution timed out after {self.timeout_seconds}s",
            )
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
            real_home=self.config.real_home,
        )
        self.quota_gate: Any = _dev_config().cmd_quota_check
        self.checkpoint_writer: Any = _state_envelope().update_epic_checkpoint
        self._turns_since_budget_checkpoint: int = 0
        self._checkpoint_lock = threading.Lock()
        self._pending_audit_notes: dict[str, list[dict[str, Any]]] = {}
        self._audit_notes_lock = threading.Lock()
        self._halted_by_stop: bool = False
        self._pending_quota_warning: str | None = None
        self.state = self.load_or_init_state()

    @property
    def pool_dispatcher(self) -> Any:
        """Delegate pool_dispatcher access to the underlying ModelDispatcher."""
        return self.dispatcher.pool_dispatcher

    @pool_dispatcher.setter
    def pool_dispatcher(self, value: Any) -> None:
        self.dispatcher.pool_dispatcher = value

    def _detect_profile(self) -> str:
        resolved_home = _persona_config().get_real_home(self.config.real_home)
        profile = str(
            _resume_context().detect_current_profile(
                self.root, real_home=resolved_home
            )
            or ""
        ).strip()
        return profile or os.environ.get("USER", "").strip() or "default"

    def _is_low_quota_active(self) -> bool:
        profile = self._detect_profile()
        return (
            _persona_config().low_quota_state(
                self.root, profile, real_home=self.config.real_home
            )
            is not None
        )

    def _effective_turn_budget(self) -> int:
        profile = self._detect_profile()
        return int(
            _persona_config().effective_turn_budget(
                self.root, profile, real_home=self.config.real_home
            )
        )

    def _git_head_sha(self, target: Path | None = None) -> str:
        cwd = target or self.root
        if not self._is_git_repo(cwd):
            return ""
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return res.stdout.strip() if res.returncode == 0 else ""

    def _write_checkpoint(
        self,
        event: str,
        *,
        persona: str = "orchestrator",
        wave: int | None = None,
        tasks_in_flight: Sequence[str] | None = None,
        next_step: str = "",
        turns_since_checkpoint: int | None = None,
        warning: str | None = None,
        extra: Mapping[str, Any] | None = None,
    ) -> None:
        turns_val = (
            self._turns_since_budget_checkpoint
            if turns_since_checkpoint is None
            else turns_since_checkpoint
        )
        payload: dict[str, Any] = {
            "event": event,
            "at": _state_envelope()._utc_now_iso(),
            "persona": persona,
            "head_sha": self._git_head_sha(),
            "wave": wave,
            "tasks_done": list(self.state.completed_tasks),
            "tasks_in_flight": list(tasks_in_flight or []),
            "next_step": next_step,
            "turns_since_checkpoint": turns_val,
            "low_quota": self._is_low_quota_active(),
        }
        effective_warning = warning or self._pending_quota_warning
        if effective_warning:
            payload["warning"] = effective_warning
            self._pending_quota_warning = None
        if extra:
            for key in ("brief_role", "model", "effort"):
                val = extra.get(key)
                if isinstance(val, str) and val.strip():
                    payload[key] = val.strip()
        self.checkpoint_writer(self.root, self.epic_slug, payload)

    def _halt_with_decision(
        self,
        *,
        halt_reason: str,
        checkpoint_event: str,
        decision_kind: str,
        decision_reason: str,
        persona: str = "orchestrator",
        wave: int | None = None,
        tasks_in_flight: Sequence[str] | None = None,
    ) -> None:
        self._write_checkpoint(
            checkpoint_event,
            persona=persona,
            wave=wave,
            tasks_in_flight=tasks_in_flight,
            next_step=halt_reason,
        )
        _state_envelope().record_pending_decision(
            self.root,
            self.epic_slug,
            decision_reason,
            kind=decision_kind,
            stage=self.state.active_stage,
            worktree=self.root,
        )
        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = halt_reason
        self.state.last_error = decision_reason
        self._halted_by_stop = True
        self.save_state()
        print(f"\n🛑 {halt_reason}: {decision_reason}\n")

    def _fallback_command_hint(self, persona: str, binding: Any) -> str:
        fallback_alias = getattr(binding, "fallback_alias", None)
        if not fallback_alias:
            return f"/d3nexus:dev-config set {persona} <model> <effort>"
        pc = _persona_config()
        chosen_effort = str(binding.effort)
        try:
            cfg = pc.load_persona_config(self.root, real_home=self.config.real_home)
            meta = cfg.get("models", {}).get(fallback_alias, {})
            efforts = [str(e) for e in meta.get("efforts", []) if isinstance(e, str)]
            if efforts and chosen_effort not in efforts:
                chosen_effort = efforts[-1]
        except (OSError, ValueError, KeyError, TypeError, pc.PersonaConfigError):
            chosen_effort = str(binding.effort)
        return f"/d3nexus:dev-config set {persona} {fallback_alias} {chosen_effort}"

    def _invoke_quota_gate(self, personas: tuple[str, ...]) -> tuple[Any, str]:
        buf = io.StringIO()
        gate_fn = self.quota_gate
        kwargs: dict[str, Any] = {}
        try:
            sig = inspect.signature(gate_fn)
            params = sig.parameters
            accepts_var_kw = any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values()
            )
            if accepts_var_kw or "personas" in params:
                kwargs["personas"] = personas
            if accepts_var_kw or "json_output" in params:
                kwargs["json_output"] = True
            if accepts_var_kw or "real_home" in params:
                kwargs["real_home"] = self.config.real_home
            accepts_pos = any(
                p.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    inspect.Parameter.VAR_POSITIONAL,
                )
                for p in params.values()
            )
        except (TypeError, ValueError):
            accepts_pos = True
            kwargs = {
                "personas": personas,
                "json_output": True,
                "real_home": self.config.real_home,
            }

        with contextlib.redirect_stdout(buf):
            if accepts_pos:
                raw_res = gate_fn(self.root, **kwargs)
            else:
                raw_res = gate_fn(**kwargs)
        return raw_res, buf.getvalue()

    def _run_quota_gate(
        self, personas: tuple[str, ...], *, wave: int | None = None
    ) -> bool:
        raw_res, captured = self._invoke_quota_gate(personas)
        extra_detail = ""
        if type(raw_res) is bool:
            sufficient = raw_res
        elif isinstance(raw_res, int):
            sufficient = raw_res == 0
        elif isinstance(raw_res, tuple):
            sufficient = bool(raw_res[0])
            if len(raw_res) > 1:
                extra_detail = str(raw_res[1])
        elif isinstance(raw_res, Mapping):
            sufficient = bool(raw_res.get("sufficient", True))
        else:
            sufficient = bool(raw_res)

        warnings_list: list[str] = []
        insufficient_lines: list[str] = []
        if captured.strip():
            try:
                payload = json.loads(captured)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, Mapping):
                for item in payload.get("personas", []):
                    if not isinstance(item, Mapping):
                        continue
                    warn = item.get("warning")
                    if isinstance(warn, str) and warn.strip():
                        warnings_list.append(warn.strip())
                    if not item.get("sufficient", True):
                        p_name = str(item.get("persona") or "")
                        cli_name = str(item.get("cli") or "")
                        alias = str(item.get("alias") or "")
                        q_line = str(item.get("quota_line") or "insufficient")
                        insufficient_lines.append(
                            f"{p_name} ({cli_name}/{alias}): {q_line}"
                        )

        if warnings_list:
            self._pending_quota_warning = "; ".join(warnings_list)

        if sufficient:
            return True

        if insufficient_lines:
            reason = (
                "Quota insufficient: "
                + "; ".join(insufficient_lines)
                + ". Recover via profile switch or /d3nexus:dev-config preset <name>."
            )
        elif extra_detail:
            reason = extra_detail
        elif captured.strip():
            reason = captured.strip()
        else:
            reason = f"Quota insufficient for {', '.join(personas)}."

        self._halt_with_decision(
            halt_reason="QUOTA_LOW",
            checkpoint_event="quota_low",
            decision_kind="quota",
            decision_reason=reason,
            wave=wave,
        )
        return False

    def _check_low_quota_stop(
        self, *, wave: int | None = None, context: str = "before wave"
    ) -> bool:
        if not self._is_low_quota_active():
            return False
        self._halt_with_decision(
            halt_reason="LOW_QUOTA_STOP",
            checkpoint_event="low_quota_stop",
            decision_kind="blocker",
            decision_reason=(
                f"Low-quota mode enabled ({context}); stopped safely at checkpoint."
            ),
            wave=wave,
        )
        return True

    def _dispatch_persona(
        self,
        persona: str,
        mode: str,
        prompt: str,
        *,
        brief_role: str = "",
        task_id: str = "",
        slot: int | None = None,
        wave: int | None = None,
        dispatcher: ModelDispatcher | None = None,
        log_path: Path | None = None,
        allow_quota_midrun_retry: bool = True,
    ) -> tuple[int, str, str, bool]:
        """Dispatch a persona binding with pool routing, failure classification, checkpoints, and turn budget."""
        pc = _persona_config()
        binding = self.config.resolve_binding(persona, self.root)
        cmd = pc.build_dispatch_argv(binding, mode)
        active_dispatcher = dispatcher or self.dispatcher
        max_attempts = 2 if allow_quota_midrun_retry else 1

        for attempt_idx in range(max_attempts):
            with self._checkpoint_lock:
                if self._halted_by_stop or self.state.active_stage == StageName.HALTED.value:
                    return 1, "", self.state.halt_reason or "halted", False

            owner = {
                "repo": self.root.name,
                "epic": self.epic_slug,
                "task": task_id or brief_role,
                "slot": slot,
                "role": "runner",
            }
            if isinstance(active_dispatcher, ModelDispatcher):
                active_dispatcher.set_dispatch_context(
                    binding=binding,
                    mode=mode,
                    owner=owner,
                    log_path=log_path,
                )
            try:
                exit_code, stdout, stderr = active_dispatcher.dispatch(
                    cli=cmd[0],
                    args=cmd[1:],
                    prompt=prompt,
                )
            finally:
                if isinstance(active_dispatcher, ModelDispatcher):
                    active_dispatcher.clear_dispatch_context()

            dispatch_res = (
                active_dispatcher.consume_last_dispatch_result()
                if isinstance(active_dispatcher, ModelDispatcher)
                else None
            )

            with self._checkpoint_lock:
                already_halted = (
                    self._halted_by_stop
                    or self.state.active_stage == StageName.HALTED.value
                )
                res_status = (
                    str(getattr(dispatch_res, "status", ""))
                    if dispatch_res is not None
                    else ""
                )
                profile_used = (
                    getattr(dispatch_res, "profile_used", None)
                    if dispatch_res is not None
                    else None
                )
                is_no_profile = dispatch_res is not None and res_status == "no_profile"
                is_model_unavail = (
                    dispatch_res is not None
                    and res_status in ("model_unavailable", "preflight_failed")
                ) or (
                    dispatch_res is None
                    and pc.classify_dispatch_failure(exit_code, stdout, stderr)
                    == "model_unavailable"
                )

                if already_halted and (is_no_profile or is_model_unavail):
                    return exit_code, stdout, stderr, False

                self._turns_since_budget_checkpoint += 1

                if not already_halted and is_no_profile:
                    report_lines = list(getattr(dispatch_res, "report", []) or [])
                    reason_text = (
                        "\n".join(report_lines)
                        if report_lines
                        else str(getattr(dispatch_res, "reason", None) or "no_profile")
                    )
                    print(reason_text)
                    self._halt_with_decision(
                        halt_reason="QUOTA_LOW",
                        checkpoint_event="quota_low",
                        decision_kind="quota",
                        decision_reason=reason_text,
                        persona=persona,
                        wave=wave,
                        tasks_in_flight=[task_id] if task_id else None,
                    )
                    return exit_code, stdout, stderr, False

                if not already_halted and is_model_unavail:
                    hint_cmd = self._fallback_command_hint(persona, binding)
                    detail = _tail_lines(stderr, 10) or f"exit={exit_code}"
                    reason_text = (
                        f"{persona} model '{binding.alias}' unavailable ({detail}). "
                        f"Fallback: {hint_cmd}"
                    )
                    self._halt_with_decision(
                        halt_reason="MODEL_UNAVAILABLE",
                        checkpoint_event="model_unavailable",
                        decision_kind="blocker",
                        decision_reason=reason_text,
                        persona=persona,
                        wave=wave,
                        tasks_in_flight=[task_id] if task_id else None,
                    )
                    return exit_code, stdout, stderr, False

                profile_part = f" profile={profile_used}" if profile_used else ""
                role_label = brief_role or persona
                target_label = task_id or "epic"
                self._write_checkpoint(
                    "subagent_returned",
                    persona=persona,
                    wave=wave,
                    tasks_in_flight=[task_id] if task_id else None,
                    next_step=f"{role_label}:{target_label}{profile_part}",
                    extra={
                        "brief_role": brief_role,
                        "model": str(getattr(binding, "model_id", "") or ""),
                        "effort": str(getattr(binding, "effort", "") or ""),
                    },
                )
                budget = self._effective_turn_budget()
                if self._turns_since_budget_checkpoint >= budget:
                    self._write_checkpoint(
                        "turn_budget",
                        persona="orchestrator",
                        wave=wave,
                        tasks_in_flight=[task_id] if task_id else None,
                        next_step=f"Turn budget ({budget}) reached",
                        turns_since_checkpoint=0,
                    )
                    self._turns_since_budget_checkpoint = 0

                if already_halted:
                    ret_code = (
                        (exit_code or 1)
                        if dispatch_res is not None and res_status == "quota_midrun"
                        else exit_code
                    )
                    return ret_code, stdout, stderr, False

                if dispatch_res is not None and res_status == "quota_midrun":
                    if attempt_idx == 0 and allow_quota_midrun_retry:
                        continue
                    return (exit_code or 1), stdout, stderr, False

                return exit_code, stdout, stderr, True

        return 1, "", "quota_midrun retry exhausted", False

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
                prog_binding = self.config.resolve_binding("programmer", self.root)
                probe_cli = _persona_config().build_dispatch_argv(
                    prog_binding, "write"
                )[0]
                ok, err = self.dispatcher.probe_model(
                    probe_cli, prog_binding.model_id
                )
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
                self.state.halt_reason = (
                    "Human Architect rejected Principal Review fixes"
                )
                self.save_state()
                return 1
            else:
                print(
                    "Awaiting Human confirmation for Principal Review fixes. Pass --confirm-fixes or --reject-fixes."
                )
                return 0

        if self.state.active_stage == StageName.IMPLEMENTATION.value:
            if dry_run:
                print("[DRY-RUN] Would execute Stage 3 Implementation")
            else:
                ok = self.step_implementation()
                if not ok:
                    return 1
                if self.state.active_stage == StageName.IMPLEMENTATION.value:
                    gate4_ok, _ = self.run_gate4()
                    if not gate4_ok:
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
            print(
                "🏁 Stage 3 completed. All tasks verified and Gate 4 PASS bound to candidate SHA."
            )
            print(
                "Candidate readiness for Gate 5 recorded in .devtool/state/<epic>.pipeline.json."
            )
            print(
                "Proceed to /finishing-a-development-branch to merge to local base branch."
            )
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
        pool_path = self._resolve_script(
            "dev-implementation/resources/scripts/manage_worker_pool.py"
        )
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
        script = self._resolve_script(
            "dev-implementation/resources/scripts/compute_execution_order.py"
        )
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
                    key in heading
                    for key in ("files", "impact analysis", "blast radius")
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
                    or not (
                        "/" in path_tok
                        or re.search(r"\.[A-Za-z][A-Za-z0-9]{0,7}$", path_tok)
                    )
                ):
                    continue
                if range_tok and not range_tok.startswith("L"):
                    range_tok = f"L{range_tok}"
                if path_tok not in targets_by_path or range_tok:
                    targets_by_path[path_tok] = (
                        f"{path_tok} ({range_tok})" if range_tok else path_tok
                    )

        return list(targets_by_path.values())

    def _resolve_epic_anchor_rels(self, exec_root: Path) -> list[str]:
        """Resolve English-only epic artefact paths relative to exec_root/self.root."""
        ed = _epic_docs()
        anchors: list[str] = []
        seen: set[str] = set()
        for base in dict.fromkeys([exec_root, self.root]):
            epic_dir = base / ".devtool" / "epic" / self.epic_slug
            if not epic_dir.is_dir():
                continue
            for stem in ("handoff", self.epic_slug, "hld", "bdd_scenarios"):
                doc = ed.resolve_epic_doc(epic_dir, stem)
                if doc is None or doc.name.endswith(".vi.md"):
                    continue
                rel = f".devtool/epic/{self.epic_slug}/{doc.name}"
                if rel not in seen:
                    seen.add(rel)
                    anchors.append(rel)
            for spec_doc in ed.resolve_design_specs(epic_dir):
                if spec_doc.name.endswith(".vi.md"):
                    continue
                rel = f".devtool/epic/{self.epic_slug}/{spec_doc.name}"
                if rel not in seen:
                    seen.add(rel)
                    anchors.append(rel)
        return anchors

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
                target_refs = self._extract_task_targets(
                    task_file.read_text(encoding="utf-8")
                )
            except OSError:
                target_refs = []

        existing_anchors = self._resolve_epic_anchor_rels(exec_root)

        lines = [
            f"Implement task `{task_slug}` inside workspace `{exec_root}` using strict TDD (`task-implementer`).",
            f"- Task spec path (read directly bounded): `{task_rel}`",
        ]
        if existing_anchors:
            lines.append("- Design/BDD anchors (paths only):")
            for anchor in existing_anchors:
                lines.append(f"  - `{anchor}`")
        if target_refs:
            lines.append(
                "- Target files & line ranges (read bounded <=150 lines per call):"
            )
            for ref in target_refs:
                lines.append(f"  - `{ref}`")
        lines.extend(
            [
                "- Constraints: Modify ONLY this task's Allowed files. Do not invoke d3nexus:task-observer.",
                "- Output cap (Zero-Fluff): Reply ONLY with modified file paths, pass/fail test counts, and blocking errors (preserve required Gate/verdict/finding lines).",
            ]
        )
        return "\n".join(lines) + "\n"

    def _changed_files_for_gating(
        self,
        exec_root: Path,
        pre_task_sha: str,
        impl_head_sha: str,
        summary: Mapping[str, Any] | None,
    ) -> list[str]:
        """Collect changed file paths via git diff (or working tree / summary fallback)."""
        if self._is_git_repo(exec_root):
            paths: list[str] = []
            diff_ok = False
            if impl_head_sha:
                valid_res = subprocess.run(
                    ["git", "cat-file", "-e", f"{impl_head_sha}^{{commit}}"],
                    cwd=exec_root,
                    capture_output=True,
                    check=False,
                )
                if valid_res.returncode == 0:
                    base_ref = ""
                    if pre_task_sha:
                        if pre_task_sha != impl_head_sha:
                            base_ref = pre_task_sha
                    else:
                        base_check = subprocess.run(
                            [
                                "git",
                                "rev-parse",
                                "--verify",
                                "--quiet",
                                self.config.base_branch,
                            ],
                            cwd=exec_root,
                            capture_output=True,
                            check=False,
                        )
                        if base_check.returncode == 0:
                            base_ref = self.config.base_branch
                    if base_ref:
                        diff_res = subprocess.run(
                            [
                                "git",
                                "diff",
                                "--name-only",
                                f"{base_ref}..{impl_head_sha}",
                            ],
                            cwd=exec_root,
                            capture_output=True,
                            text=True,
                            check=False,
                        )
                        if diff_res.returncode == 0:
                            paths.extend(
                                ln.strip()
                                for ln in diff_res.stdout.splitlines()
                                if ln.strip()
                            )
                            diff_ok = True
                    elif pre_task_sha == impl_head_sha:
                        diff_ok = True
            st_res = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=exec_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if st_res.returncode == 0:
                for line in st_res.stdout.splitlines():
                    if len(line) >= 4:
                        rel = line[3:].strip().split(" -> ")[-1].strip('"')
                        if rel and rel not in paths:
                            paths.append(rel)
            if diff_ok or paths:
                return paths

        if isinstance(summary, Mapping) and isinstance(
            summary.get("changed_files"), list
        ):
            return [str(p) for p in summary["changed_files"] if str(p).strip()]
        return []

    def _task_requires_architect_review(
        self,
        task_file: Path | None,
        exec_root: Path,
        pre_task_sha: str,
        impl_head_sha: str,
        summary: Mapping[str, Any] | None,
    ) -> bool:
        """Recompute selective review gating from task frontmatter and git diff."""
        review_tier, labels = _parse_task_frontmatter(task_file)
        if review_tier == "full" or bool(labels & _HIGH_RISK_LABELS):
            return True
        changed = self._changed_files_for_gating(
            exec_root, pre_task_sha, impl_head_sha, summary
        )
        non_test = [p for p in changed if _is_non_test_module(p)]
        return len(non_test) > 2

    def _build_task_reviewer_prompt(
        self,
        task_slug: str,
        task_file: Path | None,
        exec_root: Path,
        impl_head_sha: str,
        review_pass: int = 1,
        pass1_tree_sha: str | None = None,
        pass1_blockers: Sequence[Mapping[str, Any]] | None = None,
    ) -> str:
        """Build read-only Role 2.1 task-reviewer brief for Pass 1 or Pass 2 Delta-Only audit."""
        task_rel = f".devtool/features/{task_slug}.md"
        if task_file is not None:
            try:
                task_rel = str(task_file.relative_to(exec_root))
            except ValueError:
                task_rel = str(task_file)
        anchors = self._resolve_epic_anchor_rels(exec_root)
        anchor_text = ", ".join(anchors) if anchors else "(none)"
        common = (
            f"You are Role 2.1 AI Architect & Reviewer (`task-reviewer`, read-only).\n"
            f"Review task `{task_slug}` in `{exec_root}` at candidate head_sha `{impl_head_sha}` "
            f"(Pass {review_pass}).\n"
            f"- Task spec: `{task_rel}`\n"
            f"- English SSOT epic docs: {anchor_text}\n"
            f"- Boundaries: Read-only. Do NOT edit files, mark tasks done, or commit.\n"
        )
        if review_pass >= 2:
            sha_ref = (pass1_tree_sha or "").strip() or "<pass1_tree_sha>"
            blockers_json = json.dumps(
                [dict(item) for item in (pass1_blockers or ())],
                ensure_ascii=False,
            )
            return (
                f"{common}"
                f"- Scope: Delta-Only Verification — inspect ONLY `git diff {sha_ref}`, "
                f"Pass 1 blockers, `run_task_checks.py status`, and `check_bdd_traceability.py`.\n"
                f"- Strict Rule: Do NOT introduce new non-regression findings, new edge cases, "
                f"or style nitpicks in Pass 2. Only unresolved Pass 1 blockers or direct regressions "
                f"introduced by Fix Pass 1 (`DIRECT_REGRESSION`) may appear in `blockers`.\n"
                f"- Pass 1 blockers: {blockers_json}\n"
                f'- End with fenced json: `{{"task_id": "{task_slug}", "pass": {review_pass}, '
                f'"verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "{impl_head_sha}", '
                f'"done_gate": "PASS|FAIL", "blockers": [], "observations": []}}`\n'
            )
        return (
            f"{common}"
            f"- Severity Rubric (Blocker-Only): Report `BLOCKER` defects (`BDD_VIOLATION`, "
            f"`CONTRACT_SCHEMA_VIOLATION`, `RUNTIME_SAFETY`, `OWNERSHIP_ARCHITECTURE_VIOLATION`) "
            f"in `blockers` to return `CHANGES_REQUESTED`. Log minor refinements/style nits as "
            f"`NON_BLOCKING_OBSERVATION` in `observations` with `\"verdict\": \"APPROVED\"` "
            f"(legacy `PASS`/`FAIL` remains accepted).\n"
            f'- End with fenced json: `{{"task_id": "{task_slug}", "pass": 1, '
            f'"verdict": "APPROVED|CHANGES_REQUESTED", "head_sha": "{impl_head_sha}", '
            f'"done_gate": "PASS|FAIL", "blockers": [], "observations": []}}`\n'
        )

    def _resolve_task_review_bounds(self) -> tuple[int, int, int]:
        """Return (max_review_passes, max_fix_passes, max_attempts) from persona_config."""
        pc = _persona_config()
        if self.config.real_home is not None:
            max_review_passes, max_fix_passes = pc.resolve_task_review_limits(
                self.root, real_home=self.config.real_home
            )
        else:
            max_review_passes, max_fix_passes = pc.resolve_task_review_limits(self.root)
        max_attempts = max(1, min(int(max_review_passes), int(max_fix_passes) + 1))
        return int(max_review_passes), int(max_fix_passes), max_attempts

    def _record_or_queue_review_audit_note(
        self,
        task_slug: str,
        exec_root: Path,
        worktree_dir: Path | None,
        entry: dict[str, Any],
    ) -> None:
        """Write and commit an audit note on exec_root directly, or queue for post-merge flush."""
        if worktree_dir is None:
            _manage_worker_pool().append_review_audit_note(
                self.root,
                exec_root,
                self.epic_slug,
                self.epic_slug,
                task_slug,
                entry,
                commit=self._is_git_repo(exec_root),
            )
            return
        with self._audit_notes_lock:
            self._pending_audit_notes.setdefault(task_slug, []).append(entry)

    def _evaluate_task_reviewer_output(
        self,
        task_slug: str,
        impl_head_sha: str,
        rev_code: int,
        rev_out: str,
        rev_err: str,
    ) -> dict[str, Any]:
        """Normalize Role 2.1 task-reviewer stdout and enforce fail-closed mechanical checks."""
        rev_summary = _extract_last_fenced_json(rev_out)
        normalized = (
            _manage_worker_pool().normalize_task_review_payload(rev_summary)
            if rev_summary is not None
            else None
        )
        rev_valid = bool(normalized is not None and normalized.get("valid"))
        rev_verdict = (
            str(normalized.get("verdict") or "").strip().upper()
            if normalized is not None
            else "UNPARSEABLE"
        ) or "UNPARSEABLE"
        rev_sha = str(
            (normalized.get("head_sha") if normalized is not None else None)
            or (rev_summary.get("head_sha") if rev_summary is not None else None)
            or ""
        ).strip()
        rev_done_gate = (
            str(normalized.get("done_gate") or "").strip().upper()
            if normalized is not None
            else ""
        )
        raw_task_id = rev_summary.get("task_id") if rev_summary is not None else None
        rev_task_id_present = raw_task_id is not None
        rev_task_id = str(raw_task_id or "").strip() if rev_task_id_present else ""
        task_id_ok = (not rev_task_id_present) or (rev_task_id == task_slug)

        mechanical_ok = (
            rev_code == 0
            and rev_summary is not None
            and rev_valid
            and rev_done_gate == "PASS"
            and task_id_ok
            and bool(impl_head_sha)
            and rev_sha == impl_head_sha
        )
        blockers: list[dict[str, Any]] = (
            list(normalized.get("blockers") or [])
            if normalized is not None
            else []
        )
        observations: list[Any] = (
            list(normalized.get("observations") or [])
            if normalized is not None
            else []
        )
        coerced = bool(
            normalized is not None and normalized.get("coerced_from_non_blocking")
        )
        findings_payload: Any = None
        if blockers:
            findings_payload = blockers
        elif rev_summary is not None and rev_summary.get("findings") is not None:
            findings_payload = rev_summary.get("findings")
        findings_text = (
            json.dumps(findings_payload, ensure_ascii=False)
            if findings_payload is not None
            else _tail_lines(rev_err or rev_out, 10)
        )
        retry_note = (
            f"Architect task-reviewer did not PASS for head_sha '{impl_head_sha}' "
            f"(verdict={rev_verdict or 'UNPARSEABLE'}, done_gate={rev_done_gate or 'missing'}, "
            f"task_id={rev_task_id or 'none'}, reviewer_sha={rev_sha or 'none'}, "
            f"blockers={findings_text})."
        )
        return {
            "mechanical_ok": mechanical_ok,
            "verdict": rev_verdict,
            "blockers": blockers,
            "observations": observations,
            "coerced": coerced,
            "retry_note": retry_note,
        }

    def _finalize_task_done(
        self,
        task_slug: str,
        exec_root: Path,
        sync_script: Path,
        *,
        commit_title: str,
    ) -> bool:
        """Mark task done via sync_task_status.py and commit changes inside exec_root."""
        if sync_script.is_file():
            sync_res = subprocess.run(
                [sys.executable, "-B", str(sync_script), "task", task_slug, "done"],
                cwd=exec_root,
                capture_output=True,
                text=True,
                check=False,
            )
            if sync_res.returncode != 0:
                raw_err = sync_res.stderr or sync_res.stdout or ""
                if isinstance(raw_err, bytes):
                    raw_err = raw_err.decode("utf-8", errors="replace")
                detail = _tail_lines(str(raw_err), 10) or f"exit={sync_res.returncode}"
                self.state.last_error = (
                    f"sync_task_status failed for {task_slug}: {detail}"
                )
                return False

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

    def _execute_single_task(
        self,
        task_slug: str,
        worktree_dir: Path | None = None,
        dispatcher: ModelDispatcher | None = None,
        *,
        slot: int | None = None,
        wave: int | None = None,
    ) -> bool:
        """Dispatch headless programmer subprocess for a single task inside `worktree_dir`."""
        exec_root = worktree_dir or self.root
        task_file = self._find_task_file(
            task_slug, root=exec_root
        ) or self._find_task_file(task_slug, root=self.root)
        base_prompt = self._build_task_prompt(task_slug, task_file, exec_root)
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
                [
                    sys.executable,
                    "-B",
                    str(sync_script),
                    "task",
                    task_slug,
                    "in-progress",
                ],
                cwd=exec_root,
                capture_output=True,
                check=False,
            )

        pre_task_sha = self._git_head_sha(exec_root)
        log_dir = self.root / ".devtool" / "logs" / "tasks"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{task_slug}.log"
        if worktree_dir is not None:
            with self._audit_notes_lock:
                self._pending_audit_notes.pop(task_slug, None)

        _, _, max_attempts = self._resolve_task_review_bounds()
        retry_note = ""
        pass1_tree_sha: str | None = None
        pass1_blockers: list[dict[str, Any]] = []

        for attempt_idx in range(max_attempts):
            review_pass = attempt_idx + 1
            prompt = (
                base_prompt
                if not retry_note
                else f"{base_prompt}\nReviewer feedback to address:\n{retry_note}\n"
            )
            exit_code, stdout, stderr, disp_ok = self._dispatch_persona(
                "programmer",
                "write",
                prompt,
                brief_role="task-implementer",
                task_id=task_slug,
                slot=slot,
                wave=wave,
                dispatcher=dispatcher,
                log_path=log_dir / f"{task_slug}.pool.log",
            )
            try:
                log_file.write_text(
                    f"=== STDOUT ===\n{stdout}\n=== STDERR ===\n{stderr}\n",
                    encoding="utf-8",
                )
            except OSError:
                pass

            if not disp_ok or exit_code != 0:
                return False

            impl_summary = _extract_last_fenced_json(stdout)
            if impl_summary is not None:
                impl_status = str(impl_summary.get("status") or "").strip().upper()
                if impl_status and impl_status != "DONE":
                    self.state.last_error = (
                        f"Task {task_slug} returned status '{impl_status}'"
                    )
                    return False
                if "verify" in impl_summary:
                    impl_verify = str(impl_summary.get("verify") or "").strip().upper()
                    if impl_verify != "PASS":
                        self.state.last_error = (
                            f"Task {task_slug} returned verify '{impl_verify or 'missing'}'"
                        )
                        return False
                impl_head_sha = str(impl_summary.get("head_sha") or "").strip()
                if self._is_git_repo(exec_root):
                    real_head = self._git_head_sha(exec_root)
                    if real_head and impl_head_sha != real_head:
                        self.state.last_error = (
                            f"Task {task_slug} reported head_sha '{impl_head_sha or 'missing'}' "
                            f"!= HEAD '{real_head}'"
                        )
                        return False
            else:
                impl_head_sha = ""
            if not impl_head_sha and self._is_git_repo(exec_root):
                impl_head_sha = self._git_head_sha(exec_root)

            needs_review = self._task_requires_architect_review(
                task_file, exec_root, pre_task_sha, impl_head_sha, impl_summary
            )
            if not needs_review:
                return self._finalize_task_done(
                    task_slug,
                    exec_root,
                    sync_script,
                    commit_title=f"[{self.epic_slug.upper()}] Execute {task_slug}",
                )

            rev_prompt = self._build_task_reviewer_prompt(
                task_slug,
                task_file,
                exec_root,
                impl_head_sha,
                review_pass=review_pass,
                pass1_tree_sha=pass1_tree_sha,
                pass1_blockers=pass1_blockers,
            )
            rev_code, rev_out, rev_err, rev_disp_ok = self._dispatch_persona(
                "ai_architect_reviewer",
                "read-only",
                rev_prompt,
                brief_role="task-reviewer",
                task_id=task_slug,
                slot=slot,
                wave=wave,
                dispatcher=dispatcher,
                log_path=log_dir / f"{task_slug}.review.log",
            )
            if not rev_disp_ok:
                return False

            eval_res = self._evaluate_task_reviewer_output(
                task_slug, impl_head_sha, rev_code, rev_out, rev_err
            )
            mechanical_ok = bool(eval_res["mechanical_ok"])
            rev_verdict = str(eval_res["verdict"])
            blockers: list[dict[str, Any]] = eval_res["blockers"]
            observations: list[Any] = eval_res["observations"]
            coerced = bool(eval_res["coerced"])

            if mechanical_ok and rev_verdict == "APPROVED":
                if not self._finalize_task_done(
                    task_slug,
                    exec_root,
                    sync_script,
                    commit_title=(
                        f"[{self.epic_slug.upper()}] Mark {task_slug} done after Architect review"
                    ),
                ):
                    return False
                if observations or coerced:
                    event_name = (
                        "coerced_non_blocking_approval"
                        if coerced
                        else f"pass{review_pass}_observations"
                    )
                    self._record_or_queue_review_audit_note(
                        task_slug,
                        exec_root,
                        worktree_dir,
                        {
                            "event": event_name,
                            "task_id": task_slug,
                            "review_pass": review_pass,
                            "head_sha": impl_head_sha,
                            "coerced_from_non_blocking": coerced,
                            "observations": observations,
                        },
                    )
                return True

            if mechanical_ok and review_pass >= max_attempts:
                if not self._finalize_task_done(
                    task_slug,
                    exec_root,
                    sync_script,
                    commit_title=(
                        f"[{self.epic_slug.upper()}] Mark {task_slug} done after Architect review"
                    ),
                ):
                    return False
                residual_entry: dict[str, Any] = {
                    "event": "pass2_residual_logged_on_cap",
                    "task_id": task_slug,
                    "head_sha": impl_head_sha,
                    "blockers": blockers,
                }
                if observations:
                    residual_entry["observations"] = observations
                self._record_or_queue_review_audit_note(
                    task_slug,
                    exec_root,
                    worktree_dir,
                    residual_entry,
                )
                return True

            if review_pass < max_attempts:
                if review_pass == 1 and self._is_git_repo(exec_root):
                    pass1_tree_sha = _manage_worker_pool().capture_slot_tree_sha(
                        exec_root, self.epic_slug
                    )
                if blockers:
                    pass1_blockers = blockers
            retry_note = str(eval_res["retry_note"])

        if not self._halted_by_stop:
            detail = f": {retry_note}" if retry_note else ""
            self.state.last_error = (
                f"Task {task_slug} failed Architect task-reviewer verification{detail}"
            )
        return False

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
            f"You are the AI Architect & Reviewer (Role 2.1). Apply minor revisions for Principal Review round {round_num}.\n"
            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to address all minor review findings.\n"
        )
        _, _, _, disp_ok = self._dispatch_persona(
            "ai_architect_reviewer",
            "write",
            prompt,
            brief_role="principal-reviser",
        )
        if not disp_ok:
            return False
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
            f"You are the AI Architect & Reviewer (Role 2.1). Apply aligned technical revisions for Principal Review round {round_num}.\n"
            f"Update the architectural specifications in .devtool/epic/{self.epic_slug}/ to align with verified findings.\n"
        )
        _, _, _, disp_ok = self._dispatch_persona(
            "ai_architect_reviewer",
            "write",
            prompt,
            brief_role="principal-reviser",
        )
        if not disp_ok:
            return False
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
            handoff_file = (
                self.root / ".devtool" / "epic" / self.epic_slug / "handoff.md"
            )
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
            commit_title = (
                f"[{self.epic_slug.upper()}] Re-anchor epic packaging and revisions"
            )
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
                res = subprocess.run(
                    triage_cmd,
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
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
        print(
            "⚠️ [HUMAN CHECKPOINT] Principal Review requires confirmation for critical or domain conflicts:"
        )
        print(triage_summary)
        print("=" * 70 + "\n")
        if sys.stdin.isatty():
            try:
                ans = (
                    input("Confirm and proceed with proposed fixes? [y/N]: ")
                    .strip()
                    .lower()
                )
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
                cmd.extend(
                    ["--provider-priority", ",".join(self.config.provider_priority)]
                )
            subprocess.run(
                cmd, cwd=self.root, capture_output=True, text=True, check=False
            )

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
            triage_res = subprocess.run(
                triage_cmd, cwd=self.root, capture_output=True, text=True, check=False
            )
            triage_stdout = triage_res.stdout

            cb = self.evaluate_circuit_breakers(
                "principal", round_num, triage_stdout=triage_stdout
            )
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
                print(
                    "AUTO_PASS_FINAL_MINOR_SWEEP: 0 Critical and 0 Important findings"
                )
                if not self._apply_minor_fixes(round_num):
                    self.save_state()
                    return False
                self._run_package_epic_revise()
                self.state.active_stage = StageName.IMPLEMENTATION.value
                self.save_state()
                return True

            if action == "AUTO_PASS_FINAL_SWEEP":
                print("AUTO_PASS_FINAL_SWEEP: Final review round sweep")
                self._emit_review_phase_status("principal", "fixing", round_num)
                if not self._apply_aligned_fixes(round_num):
                    self.save_state()
                    return False
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
                    self.state.active_stage = (
                        StageName.AWAITING_PRINCIPAL_CONFIRMATION.value
                    )
                    self.save_state()
                    confirmed = self.prompt_human_principal_fixes(triage_stdout)
                    if not confirmed:
                        return False
                    self.state.active_stage = StageName.PRINCIPAL_REVIEW.value
                    self.save_state()

                self._emit_review_phase_status("principal", "fixing", round_num)
                if not self._apply_aligned_fixes(round_num):
                    self.save_state()
                    return False
                self._emit_review_phase_status("principal", "verifying", round_num)

        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        self.save_state()
        return False

    def _compute_parallel_batches(self) -> list[list[str]]:
        """Compute DAG wave batches via compute_execution_order.py --parallel --json."""
        script = self._resolve_script(
            "dev-implementation/resources/scripts/compute_execution_order.py"
        )
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
            res = subprocess.run(
                cmd, cwd=self.root, capture_output=True, text=True, check=False
            )
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
        if (
            not isinstance(self.dispatcher, ModelDispatcher)
            or "dispatch" in self.dispatcher.__dict__
        ):
            return self.dispatcher
        return ModelDispatcher(
            worktree_dir=slot_path,
            timeout_seconds=self.config.timeout_seconds,
            real_home=self.dispatcher.real_home,
            pool_dispatcher=self.dispatcher.pool_dispatcher,
        )

    def _wave_personas(self, batch: Sequence[str]) -> tuple[str, ...]:
        """Return persona bindings required before executing a wave."""
        for task_slug in batch:
            task_file = self._find_task_file(task_slug)
            review_tier, labels = _parse_task_frontmatter(task_file)
            if review_tier == "full" or bool(labels & _HIGH_RISK_LABELS):
                return ("orchestrator", "programmer", "ai_architect_reviewer")
        return ("orchestrator", "programmer")

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
                self.state.last_error = (
                    f"Failed to sync pool slot {slot_idx} to {epic_branch}"
                )
                self.save_state()
                return False

        def run_in_slot(slot_idx: int, task_slug: str) -> tuple[int, str, bool]:
            slot_path = pool_mod.get_slot_path(repo_root, self.epic_slug, slot_idx)
            slot_dispatcher = self._make_slot_dispatcher(slot_path)
            ok = self._execute_single_task(
                task_slug,
                worktree_dir=slot_path,
                dispatcher=slot_dispatcher,
                slot=slot_idx,
                wave=wave_num,
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
                with self._audit_notes_lock:
                    self._pending_audit_notes.pop(task_slug, None)
                pool_mod.sync_slot(
                    repo_root,
                    self.epic_slug,
                    self.epic_slug,
                    slot=slot_idx,
                    base_ref=epic_branch,
                    status="idle",
                )
                if (
                    not self._halted_by_stop
                    and self.state.active_stage != StageName.HALTED.value
                ):
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
                with self._audit_notes_lock:
                    pending_notes = self._pending_audit_notes.pop(task_slug, [])
                if merged and pending_notes:
                    append_fn = (
                        getattr(pool_mod, "append_review_audit_note", None)
                        or _manage_worker_pool().append_review_audit_note
                    )
                    for audit_entry in pending_notes:
                        append_fn(
                            repo_root,
                            epic_wt,
                            self.epic_slug,
                            self.epic_slug,
                            task_slug,
                            audit_entry,
                            commit=True,
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
                self.state.last_error = (
                    f"Slot {slot_idx} merge failed for task {task_slug}"
                )
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
            self._is_git_repo(self.root) and "_execute_single_task" not in self.__dict__
        )
        pool_mod = self._load_pool_module() if use_pool else None

        if pool_mod is None:
            if not self.state.task_order:
                order = self.resolve_gate3_order()
                if not order:
                    self.state.last_error = "Failed to resolve Gate 3 execution order"
                    self.save_state()
                    return False

            pending_seq = [
                t for t in self.state.task_order if t not in self.state.completed_tasks
            ]
            for wave_num, task_slug in enumerate(pending_seq, start=1):
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"before task {task_slug}"
                ):
                    return False
                if not self._run_quota_gate(
                    self._wave_personas([task_slug]), wave=wave_num
                ):
                    return False
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"before task {task_slug}"
                ):
                    return False

                success = self._execute_single_task(task_slug)
                if not success:
                    if (
                        not self._halted_by_stop
                        and self.state.active_stage != StageName.HALTED.value
                    ):
                        self.state.last_error = f"Task execution failed: {task_slug}"
                        self.save_state()
                    return False

                if task_slug not in self.state.completed_tasks:
                    self.state.completed_tasks.append(task_slug)
                self.save_state()
                self._write_checkpoint(
                    "wave_merged",
                    persona="orchestrator",
                    wave=wave_num,
                    next_step=f"Wave {wave_num} merged: {task_slug}",
                )
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"after task {task_slug}"
                ):
                    return False

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
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"before wave {wave_num}"
                ):
                    return False
                if not self._run_quota_gate(
                    self._wave_personas(pending_batch), wave=wave_num
                ):
                    return False
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"before wave {wave_num}"
                ):
                    return False

                if not self._run_pool_batch(
                    pool_mod,
                    repo_root,
                    epic_wt,
                    epic_branch,
                    pending_batch,
                    wave_num=wave_num,
                ):
                    return False

                self._write_checkpoint(
                    "wave_merged",
                    persona="orchestrator",
                    wave=wave_num,
                    next_step=f"Wave {wave_num} merged: {', '.join(pending_batch)}",
                )
                if self._check_low_quota_stop(
                    wave=wave_num, context=f"after wave {wave_num} merged"
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

    def _build_gate4_verifier_prompt(self, attempt_num: int) -> str:
        """Build the Role 2.3 gate4-verifier brief carrying Gate 4 commands verbatim."""
        ed = _epic_docs()
        epic_dir = self.root / ".devtool" / "epic" / self.epic_slug
        hld_doc = ed.resolve_epic_doc(epic_dir, self.epic_slug) or ed.resolve_epic_doc(
            epic_dir, "hld"
        )
        scenarios_doc = ed.resolve_epic_doc(epic_dir, "bdd_scenarios")

        hld_integ_cmds: list[str] = []
        hld_report_paths: list[str] = []
        if hld_doc is not None and hld_doc.is_file():
            try:
                for line in hld_doc.read_text(encoding="utf-8").splitlines():
                    if line.startswith("Integration results:"):
                        cmd_part = line[len("Integration results:") :].strip()
                        if "->" in cmd_part:
                            cmd_str, rhs = cmd_part.split("->", 1)
                            cmd_str = cmd_str.strip()
                            for tok in re.split(r"[\s,]+", rhs.strip()):
                                cleaned = tok.strip("`'\"")
                                if not cleaned:
                                    continue
                                low = cleaned.lower()
                                if (
                                    "/" in cleaned
                                    or "*" in cleaned
                                    or low.endswith((".xml", ".json"))
                                ):
                                    if cleaned not in hld_report_paths:
                                        hld_report_paths.append(cleaned)
                        else:
                            cmd_str = cmd_part
                        if cmd_str:
                            hld_integ_cmds.append(cmd_str)
            except OSError:
                pass

        scenarios_rel = (
            f".devtool/epic/{self.epic_slug}/{scenarios_doc.name}"
            if scenarios_doc is not None
            else f".devtool/epic/{self.epic_slug}/bdd_scenarios.md"
        )
        results_opt = (
            f" --results {' '.join(hld_report_paths)}" if hld_report_paths else ""
        )
        bdd_cmd = (
            f"python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py "
            f"tests --roots tests --scenarios {scenarios_rel}{results_opt}"
        )

        lines = [
            f"You are Role 2.3 Programmer (`gate4-verifier`, attempt {attempt_num}) inside `{self.root}`.",
            "Execute the complete Stage 3 Gate 4 verification sequence without modifying source or test files (commit only any generated smoke checklist so the working tree is clean):",
            f"1. `python3 skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --epic-dir {self.epic_slug}`",
            f"2. `python3 skills/dev-implementation/resources/scripts/run_external_review.py check --epic-dir {self.epic_slug} --kind code`",
            f"3. `python3 skills/dev-implementation/resources/scripts/audit_epic.py --epic-dir {self.epic_slug} --base {self.config.base_branch}`",
        ]
        if hld_integ_cmds:
            for icmd in hld_integ_cmds:
                lines.append(f"4a. HLD Integration results command: `{icmd}`")
        else:
            lines.append("4a. Execute any `Integration results:` command declared in the epic HLD.")
        lines.extend(
            [
                f"4b. `{bdd_cmd}`",
                "5. `bash scripts/verify.sh --quiet`",
                "Ensure `git status --porcelain` is empty and report `candidate_sha` equal to `git rev-parse HEAD`.",
                'End your response with one fenced `json` block: `{"candidate_sha": "...", "verdict": "PASS|FAIL", "audit_exit": 0, "quality_check_report": "...", "failures": []}`',
            ]
        )
        return "\n".join(lines) + "\n"

    def _validate_gate4_report(
        self, raw_report: Any, candidate_sha: str
    ) -> tuple[bool, str]:
        """Validate Gate 4 quality_check_report, checking SHA binding when path-like."""
        if not isinstance(raw_report, str) or not raw_report.strip():
            return False, "quality_check_report=missing"
        report_val = raw_report.strip()
        if report_val.lower() == "fail":
            return False, "quality_check_report='fail'"
        looks_like_path = "/" in report_val or report_val.lower().endswith(
            (".json", ".md", ".xml")
        )
        if not looks_like_path:
            return True, ""
        report_path = Path(report_val)
        if not report_path.is_absolute():
            report_path = self.root / report_path
        if not report_path.is_file():
            return False, f"quality_check_report missing: {report_val}"
        try:
            content = report_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return False, f"quality_check_report unreadable: {report_val}"
        if not candidate_sha or candidate_sha not in content:
            return False, f"quality_check_report unbound to SHA {candidate_sha}"
        return True, ""

    def run_gate4(self) -> tuple[bool, str]:
        """Execute Stage 3 Gate 4 via a fresh Role 2.3 gate4-verifier with SHA and clean-tree checks."""
        max_attempts = max(4, self.config.max_review_rounds + 1)
        prev_checks: set[str] = set()
        last_detail = "Gate 4 verification failed"

        for attempt_idx in range(max_attempts):
            prompt = self._build_gate4_verifier_prompt(attempt_idx + 1)
            exit_code, stdout, stderr, disp_ok = self._dispatch_persona(
                "programmer",
                "write",
                prompt,
                brief_role="gate4-verifier",
                task_id="gate4",
            )
            if not disp_ok:
                return False, self.state.halt_reason or last_detail

            summary = _extract_last_fenced_json(stdout)
            verdict = (
                str(summary.get("verdict") or "").strip().upper()
                if summary is not None
                else ("PASS" if exit_code == 0 and not stdout.strip() else "FAIL")
            )
            if exit_code == 0 and summary is not None and verdict == "PASS":
                candidate_sha = str(summary.get("candidate_sha") or "").strip()
                if self._is_git_repo(self.root):
                    head_sha = self._git_head_sha(self.root)
                    st_res = subprocess.run(
                        ["git", "status", "--porcelain"],
                        cwd=self.root,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    clean_tree = (
                        st_res.returncode == 0 and not st_res.stdout.strip()
                    )
                else:
                    head_sha = candidate_sha or "HEAD"
                    clean_tree = True

                reasons: list[str] = []
                if not candidate_sha or candidate_sha != head_sha:
                    reasons.append(
                        f"candidate_sha={candidate_sha or 'missing'} != head={head_sha or 'unknown'}"
                    )
                if not clean_tree:
                    reasons.append("clean_tree=False")
                audit_exit = summary.get("audit_exit")
                if (
                    isinstance(audit_exit, bool)
                    or not isinstance(audit_exit, int)
                    or audit_exit != 0
                ):
                    reasons.append(f"audit_exit={audit_exit!r}")
                raw_failures = summary.get("failures")
                if not isinstance(raw_failures, list) or any(
                    str(item).strip() for item in raw_failures
                ):
                    reasons.append(f"failures={raw_failures!r}")
                report_ok, report_reason = self._validate_gate4_report(
                    summary.get("quality_check_report"), candidate_sha
                )
                if not report_ok:
                    reasons.append(report_reason)

                if not reasons:
                    self.state.last_commit_sha = candidate_sha
                    self.sync_gate_ledger(
                        4, f"Gate 4 verification passed for candidate SHA {candidate_sha}"
                    )
                    self.save_state()
                    return True, "Gate 4 PASS"

                last_detail = (
                    "Gate 4 candidate verification rejected ("
                    + ", ".join(reasons)
                    + ")"
                )
                continue

            raw_failures = summary.get("failures") if summary is not None else None
            failure_lines = (
                [str(item) for item in raw_failures if str(item).strip()]
                if isinstance(raw_failures, list)
                else []
            )
            raw_err = (
                "\n".join(failure_lines)
                or stderr.strip()
                or stdout.strip()
                or f"exit code {exit_code}"
            )
            err = self._tail_lines(raw_err, 25) or raw_err
            last_detail = f"Gate 4 verification failed: {err}"
            if attempt_idx == max_attempts - 1:
                break

            curr_checks = {
                (
                    item.split(":", 1)[0].strip().lower()
                    if ":" in item
                    else item.strip().lower()
                )
                for item in (failure_lines or [err])
                if item.strip()
            }
            repeated = bool(prev_checks & curr_checks)
            prev_checks = curr_checks
            if repeated:
                plan_status, criteria, plan_md = self._draft_fix_plan(
                    attempt_idx + 1, last_detail
                )
                if plan_status == "HALTED":
                    return False, self.state.halt_reason or last_detail
                if plan_status == "ESCALATE":
                    self._escalate_fix_plan(attempt_idx + 1, criteria)
                    return False, self.state.halt_reason or last_detail
                fixer_ok = self._apply_code_fixes(
                    attempt_idx + 1,
                    plan_text=plan_md,
                    mode="apply-plan",
                )
            else:
                fixer_ok = self._apply_code_fixes(
                    attempt_idx + 1,
                    plan_text=last_detail,
                    mode="fast-track",
                )
            if not fixer_ok:
                return False, self.state.last_error or last_detail

        return False, last_detail

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
                [
                    sys.executable,
                    str(review_script),
                    "check",
                    "--epic-dir",
                    self.epic_slug,
                    "--kind",
                    "code",
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if chk_res.returncode != 0:
                raw_err = (
                    chk_res.stderr.strip()
                    or chk_res.stdout.strip()
                    or f"exit code {chk_res.returncode}"
                )
                err = self._tail_lines(raw_err, 25) or raw_err
                return False, f"Review decisions check failed: {err}"
        return True, "Intermediate scoped check PASS"

    def _draft_fix_plan(
        self, round_num: int, triage_stdout: str
    ) -> tuple[str, list[str], str]:
        """Dispatch Role 2.1 fix-planner (read-only) and persist fix_plan_round<N>.md when PLANNED."""
        epic_dir = self.root / ".devtool" / "epic" / self.epic_slug
        plan_file = epic_dir / f"fix_plan_round{round_num}.md"
        anchors = self._resolve_epic_anchor_rels(self.root)
        anchor_text = ", ".join(anchors) if anchors else "(none)"
        criteria_list = ", ".join(HALT_CRITERIA)
        prompt = (
            f"You are Role 2.1 AI Architect & Reviewer (`fix-planner`, read-only) for Cross-Model Review Round {round_num}.\n"
            f"- Epic docs (English SSOT): {anchor_text}\n"
            f"- Halt criteria: {criteria_list}\n"
            f"- Boundaries: Read-only. Do NOT edit files or commit.\n"
            f"Triage Findings:\n\n{triage_stdout}\n\n"
            f"End your response with one fenced `json` block: "
            f'`{{"round": {round_num}, "status": "PLANNED|ESCALATE", "halt_criteria": [], "plan_markdown": "..."}}`\n'
        )
        exit_code, stdout, _stderr, disp_ok = self._dispatch_persona(
            "ai_architect_reviewer",
            "read-only",
            prompt,
            brief_role="fix-planner",
            task_id=f"fix-plan-round-{round_num}",
        )
        if not disp_ok:
            return "HALTED", [], ""

        summary = _extract_last_fenced_json(stdout)
        if exit_code != 0 or summary is None:
            return "ESCALATE", ["UNPARSEABLE"], ""

        raw_round = summary.get("round")
        raw_status = summary.get("status")
        status = raw_status.strip().upper() if isinstance(raw_status, str) else ""
        raw_criteria = summary.get("halt_criteria")
        criteria = (
            [str(c).strip() for c in raw_criteria if str(c).strip()]
            if isinstance(raw_criteria, list)
            else []
        )
        raw_plan = summary.get("plan_markdown")
        plan_markdown = raw_plan if isinstance(raw_plan, str) else ""

        schema_ok = (
            isinstance(raw_round, int)
            and not isinstance(raw_round, bool)
            and status in {"PLANNED", "ESCALATE"}
            and isinstance(raw_criteria, list)
            and isinstance(raw_plan, str)
        )
        if (
            schema_ok
            and status == "PLANNED"
            and not criteria
            and bool(plan_markdown.strip())
        ):
            epic_dir.mkdir(parents=True, exist_ok=True)
            body = plan_markdown if plan_markdown.endswith("\n") else f"{plan_markdown}\n"
            plan_file.write_text(body, encoding="utf-8")
            if self._is_git_repo(self.root):
                subprocess.run(
                    ["git", "add", str(plan_file)],
                    cwd=self.root,
                    capture_output=True,
                    check=False,
                )
                commit_title = (
                    f"[{self.epic_slug.upper()}] Add fix plan for Cross-Model Review round {round_num}"
                )
                subprocess.run(
                    ["git", "commit", "-m", commit_title],
                    cwd=self.root,
                    capture_output=True,
                    check=False,
                )
            return "PLANNED", [], plan_markdown

        if not criteria:
            criteria = ["CRITICAL_CONFLICT"] if status == "ESCALATE" else ["UNPARSEABLE"]
        return "ESCALATE", criteria, ""

    def _escalate_fix_plan(self, round_num: int, criteria: list[str]) -> None:
        """Record FIX_PLAN_ESCALATE blocker pending decision and halt pipeline."""
        criteria_str = ", ".join(criteria) if criteria else "UNPARSEABLE"
        reason = (
            f"FIX_PLAN_ESCALATE ({criteria_str}): high-risk fix plan escalated in round {round_num}."
        )
        _state_envelope().record_pending_decision(
            self.root,
            self.epic_slug,
            reason,
            kind="blocker",
            stage=self.state.active_stage,
            worktree=self.root,
        )
        self.state.active_stage = StageName.HALTED.value
        self.state.halt_reason = "FIX_PLAN_ESCALATE"
        self.state.last_verdict = "ESCALATE"
        self.state.last_error = reason
        self._halted_by_stop = True
        self.save_state()
        print(f"\n🛑 FIX_PLAN_ESCALATE ({criteria_str})\n")

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
                raw_err = (
                    comp_res.stderr.strip()
                    or comp_res.stdout.strip()
                    or "py_compile failed"
                )
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
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "--tb=short",
                    *[str(t) for t in matched_tests],
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=False,
            )
            if test_res.returncode != 0:
                raw_err = (
                    test_res.stderr.strip()
                    or test_res.stdout.strip()
                    or "scoped pytest failed"
                )
                return False, _tail_lines(raw_err, 25) or raw_err

        return True, "Scoped checks PASS"

    def _emit_review_phase_status(self, kind: str, phase: str, round_num: int) -> None:
        """Emit mechanical review phase telemetry via run_external_review._emit_review_heartbeat."""
        try:
            if not (self.root / ".devtool" / "state").is_dir():
                return
            ext_scripts = (
                Path(__file__).resolve().parents[4]
                / "skills"
                / "dev-implementation"
                / "resources"
                / "scripts"
            )
            if str(ext_scripts) not in sys.path:
                sys.path.insert(0, str(ext_scripts))
            import run_external_review  # type: ignore[import-not-found]

            run_external_review._emit_review_heartbeat(
                self.root,
                self.epic_slug,
                kind="principal" if kind == "principal" else "code",
                phase=phase,
                round_num=round_num,
            )
        except Exception:  # noqa: BLE001
            return

    def _apply_code_fixes(
        self,
        round_num: int,
        plan_text: str = "",
        findings: list[dict[str, str]] | None = None,
        review_artifact: Path | None = None,
        mode: str | None = None,
    ) -> bool:
        """Apply verified code fixes aligned to HLD/BDD/specs, run scoped tests, and commit."""
        ed = _epic_docs()
        epic_dir = self.root / ".devtool" / "epic" / self.epic_slug
        anchor_candidates: list[Path] = []
        if epic_dir.is_dir():
            for stem in (self.epic_slug, "hld", "bdd_scenarios"):
                doc = ed.resolve_epic_doc(epic_dir, stem)
                if doc is not None and not doc.name.endswith(".vi.md"):
                    anchor_candidates.append(doc)
            for spec_doc in ed.resolve_design_specs(epic_dir):
                if not spec_doc.name.endswith(".vi.md"):
                    anchor_candidates.append(spec_doc)
        rev_art = review_artifact or (epic_dir / "review_results.md")
        if rev_art.is_file() and rev_art not in anchor_candidates:
            anchor_candidates.append(rev_art)
        fixer_mode = mode or ("apply-plan" if plan_text.strip() else "fast-track")
        plan_path = epic_dir / f"fix_plan_round{round_num}.md"
        if fixer_mode == "apply-plan" and plan_path.is_file() and plan_path not in anchor_candidates:
            anchor_candidates.append(plan_path)

        anchors: list[str] = []
        seen_anchors: set[str] = set()
        for candidate in anchor_candidates:
            if candidate.is_file() and not candidate.name.endswith(".vi.md"):
                try:
                    rel_str = str(candidate.relative_to(self.root))
                except ValueError:
                    rel_str = str(candidate)
                if rel_str not in seen_anchors:
                    seen_anchors.add(rel_str)
                    anchors.append(rel_str)

        prompt_parts = [
            f"You are Role 2.3 Programmer (`review-fixer`, mode `{fixer_mode}`). Implement verified fixes for Round {round_num}.",
        ]
        if anchors:
            prompt_parts.append(
                "Design/BDD/Review anchor paths (read bounded as needed):"
            )
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
        prompt_parts.append(
            "Constraints: Strict TDD. Do not invoke d3nexus:task-observer."
        )
        prompt_parts.append(
            "Output cap (Zero-Fluff): Reply ONLY with modified file paths, pass/fail test counts, and blocking errors."
        )
        prompt = "\n".join(prompt_parts) + "\n"

        self._emit_review_phase_status("code", "fixing", round_num)
        exit_code, stdout, stderr, disp_ok = self._dispatch_persona(
            "programmer",
            "write",
            prompt,
            brief_role="review-fixer",
            task_id=f"review-round-{round_num}",
        )
        if not disp_ok:
            return False
        if exit_code != 0:
            raw_err = stderr.strip() or stdout.strip() or f"exit code {exit_code}"
            self.state.last_error = f"Code fix dispatch failed in round {round_num}: {_tail_lines(raw_err, 25) or raw_err}"
            return False

        self._emit_review_phase_status("code", "verifying", round_num)
        scoped_ok, scoped_msg = self._run_scoped_tests(findings=findings)
        if not scoped_ok:
            self.state.last_error = (
                f"Scoped tests failed after round {round_num} fixes: {scoped_msg}"
            )
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
            sha_short = (
                rev_res.stdout.strip()[:7] if rev_res.returncode == 0 else "unknown"
            )
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
        sha_re = re.compile(
            r"(?:Candidate\s+)?SHA\s*:\s*`?([0-9a-fA-F]{7,40})`?", re.IGNORECASE
        )

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

            if len(cells) >= 5 and cells[1].lower() in {
                "critical",
                "important",
                "minor",
            }:
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

        review_file = (
            self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
        )
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
            if sev not in {"important", "minor"}:
                return False

            combined = " ".join(
                [
                    item.get("target", ""),
                    item.get("problem", ""),
                    item.get("status", ""),
                ]
            ).lower()
            if any(marker in combined for marker in escalation_markers):
                return False

            raw_target = item.get("target", "").strip().strip("`")
            if not raw_target:
                return False
            path_part = re.split(r"[:#]", raw_target, maxsplit=1)[0].strip()
            line_part = (
                raw_target[len(path_part) + 1 :].strip()
                if len(raw_target) > len(path_part)
                else ""
            )

            if (
                not path_part
                or path_part.endswith(".md")
                or path_part.startswith(
                    (".devtool/", "shared-contracts/", "shared_contracts/")
                )
            ):
                return False

            target_path = self.root / path_part
            if not target_path.is_file():
                return False

            line_num_match = re.match(r"^L?(\d+)", line_part)
            if line_num_match:
                line_num = int(line_num_match.group(1))
                try:
                    total_lines = len(
                        target_path.read_text(encoding="utf-8").splitlines()
                    )
                except OSError:
                    return False
                if line_num < 1 or line_num > total_lines:
                    return False

        return True

    def step_cross_model_review(self) -> bool:
        """Execute Stage 3 Cross-Model Review loop with risk-routed fix planning."""
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
                cmd.extend(
                    ["--provider-priority", ",".join(self.config.provider_priority)]
                )
            subprocess.run(
                cmd, cwd=self.root, capture_output=True, text=True, check=False
            )

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
            triage_res = subprocess.run(
                triage_cmd, cwd=self.root, capture_output=True, text=True, check=False
            )
            triage_stdout = triage_res.stdout

            cb = self.evaluate_circuit_breakers(
                "code", round_num, triage_stdout=triage_stdout
            )
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

            review_artifact = (
                self.root / ".devtool" / "epic" / self.epic_slug / "review_results.md"
            )
            findings = self._extract_cross_model_findings(round_num, triage_stdout)

            if action == "AUTO_PASS_FINAL_MINOR_SWEEP":
                print(
                    "AUTO_PASS_FINAL_MINOR_SWEEP: Sweeping minor findings in single pass..."
                )
                if not self._run_quota_gate(("orchestrator", "programmer")):
                    return False
                if not self._apply_code_fixes(
                    round_num,
                    findings=findings or None,
                    review_artifact=review_artifact
                    if review_artifact.is_file()
                    else None,
                    mode="fast-track",
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
                if not self._run_quota_gate(("orchestrator", "programmer")):
                    return False
                if not self._apply_code_fixes(
                    round_num,
                    findings=findings or None,
                    review_artifact=review_artifact
                    if review_artifact.is_file()
                    else None,
                    mode="fast-track",
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
                fast_track = self._can_fast_track_code_findings(
                    findings, triage_stdout
                )
                gate_personas = (
                    ("orchestrator", "programmer")
                    if fast_track
                    else ("orchestrator", "programmer", "ai_architect_reviewer")
                )
                if not self._run_quota_gate(gate_personas):
                    return False

                if fast_track:
                    applied = self._apply_code_fixes(
                        round_num,
                        findings=findings,
                        review_artifact=review_artifact
                        if review_artifact.is_file()
                        else None,
                        mode="fast-track",
                    )
                else:
                    plan_status, criteria, plan_md = self._draft_fix_plan(
                        round_num, triage_stdout
                    )
                    if plan_status == "HALTED":
                        return False
                    if plan_status == "ESCALATE":
                        self._escalate_fix_plan(round_num, criteria)
                        return False

                    self.state.last_verdict = "PLANNED"
                    self.save_state()
                    applied = self._apply_code_fixes(
                        round_num,
                        plan_text=plan_md,
                        findings=findings or None,
                        review_artifact=review_artifact
                        if review_artifact.is_file()
                        else None,
                        mode="apply-plan",
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
            prob_lower = (
                item.get("problem", "") + " " + item.get("target", "")
            ).lower()
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
                r_label = (
                    f"{item.get('stage', 'Review')} {item.get('round', 'Round 1')}"
                )
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
            lines.append(
                "| 1 | All Rounds | Reviewed Epic & Repository Artifacts | 0 Open High-Risk Findings | Gate 4 Verified |"
            )

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
    parser.add_argument(
        "--resume", action="store_true", help="Resume from interrupted state"
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config JSON")
    parser.add_argument(
        "--root", type=Path, default=Path.cwd(), help="Workspace root directory"
    )
    parser.add_argument(
        "--reset-stage",
        choices=[s.value for s in StageName],
        default=None,
        help="Reset to specific stage",
    )
    parser.add_argument(
        "--confirm-fixes", action="store_true", help="Confirm Principal Review fixes"
    )
    parser.add_argument(
        "--reject-fixes", action="store_true", help="Reject Principal Review fixes"
    )
    parser.add_argument(
        "--base", default="main", help="Base branch name (default: main)"
    )
    parser.add_argument(
        "--programmer-model", default=None, help="CLI override model for Programmer"
    )
    parser.add_argument(
        "--programmer-effort",
        default=None,
        help="CLI override reasoning effort for Programmer",
    )
    parser.add_argument(
        "--architect-model",
        "--assistant-model",
        dest="architect_model",
        default=None,
        help="CLI override model for AI Architect & Reviewer (--assistant-model alias)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate execution without running subprocesses",
    )
    args = parser.parse_args()

    cfg = RunnerConfig(
        programmer_model=args.programmer_model,
        programmer_effort=args.programmer_effort,
        architect_model=args.architect_model,
        base_branch=args.base,
    )
    if args.config and args.config.is_file():
        try:
            cdata = json.loads(args.config.read_text(encoding="utf-8"))
            if "programmer_model" in cdata and isinstance(
                cdata["programmer_model"], str
            ):
                cfg.config_programmer_model = cdata["programmer_model"]
            if "programmer_effort" in cdata and isinstance(
                cdata["programmer_effort"], str
            ):
                cfg.config_programmer_effort = cdata["programmer_effort"]
            elif "thinking_level" in cdata and isinstance(cdata["thinking_level"], str):
                cfg.config_programmer_effort = cdata["thinking_level"]
            arch_cfg_model = cdata.get("architect_model", cdata.get("assistant_model"))
            if isinstance(arch_cfg_model, str):
                cfg.config_architect_model = arch_cfg_model
            arch_cfg_effort = cdata.get("architect_effort", cdata.get("assistant_effort"))
            if isinstance(arch_cfg_effort, str):
                cfg.config_architect_effort = arch_cfg_effort
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
