#!/usr/bin/env python3
"""Pooled agy dispatch with preflight check, heartbeat, quota rotation, and git-work guard."""

from __future__ import annotations

from collections.abc import Callable, Mapping
import contextlib
from dataclasses import dataclass
from datetime import datetime
import importlib.util
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from types import FrameType, ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from persona_config import PersonaBinding

_SCRIPTS_DIR = Path(__file__).resolve().parent


def _load_module_by_path(
    name: str, path: Path, *, extra_sys_path: Path | None = None
) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    if not path.is_file():
        raise RuntimeError(f"Required module file not found: {path}")
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Failed to create module spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    inserted = False
    if extra_sys_path is not None and str(extra_sys_path) not in sys.path:
        sys.path.insert(0, str(extra_sys_path))
        inserted = True
    try:
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    finally:
        if inserted:
            try:
                sys.path.remove(str(extra_sys_path))
            except ValueError:
                pass
    return mod


_pc = _load_module_by_path("persona_config", _SCRIPTS_DIR / "persona_config.py")
_pool = _load_module_by_path("agy_profile_pool", _SCRIPTS_DIR / "agy_profile_pool.py")

_AUTO_HOST = object()

_QUOTA_STDERR_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pat, re.IGNORECASE)
    for pat in (
        r"\b429\b",
        r"resource_?exhausted",
        r"quota\s+(?:exceeded|exhausted)",
        r"usage\s+limit",
        r"rate.?limit(?:ed)?\s+exceeded",
    )
)


@dataclass(frozen=True)
class DispatchResult:
    """Outcome of dispatching a persona task through the pool or directly."""

    status: str
    profile_used: str | None
    attempts: int
    exit_code: int
    reason: str | None
    report: list[str]


def _is_quota_stderr(stderr: str) -> bool:
    return any(pattern.search(stderr) for pattern in _QUOTA_STDERR_PATTERNS)


def _git_snapshot(cwd: Path) -> tuple[str, list[str]] | None:
    try:
        head_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if head_proc.returncode != 0:
            return None
        status_proc = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if status_proc.returncode != 0:
            return None
    except OSError:
        return None

    filtered_lines: list[str] = []
    for line in status_proc.stdout.splitlines():
        if len(line) > 3:
            rel_path = line[3:].strip().strip('"')
            if rel_path == ".vscode/settings.json":
                continue
        filtered_lines.append(line)
    return head_proc.stdout.strip(), filtered_lines


def _load_thresholds(project_root: Path) -> dict[str, float]:
    thresholds = dict(_pool.DEFAULT_QUOTA_THRESHOLDS)
    review_cfg = project_root / ".devtool" / "review_config.json"
    if review_cfg.is_file():
        try:
            import json

            data = json.loads(review_cfg.read_text(encoding="utf-8"))
        except Exception:
            data = None
        if isinstance(data, Mapping) and isinstance(
            data.get("quota_thresholds"), Mapping
        ):
            for key, val in data["quota_thresholds"].items():
                if isinstance(val, (int, float)) and not isinstance(val, bool):
                    thresholds[str(key)] = float(val)
    return thresholds


def _append_attempt_log(
    log_path: Path,
    *,
    first_attempt: bool,
    profile_label: str,
    launch_mode: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    quota_exhausted: bool,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "w" if first_attempt else "a"
    lines: list[str] = [f"dispatch-profile: {profile_label} ({launch_mode})\n"]
    if stdout:
        lines.append(stdout if stdout.endswith("\n") else f"{stdout}\n")
    if stderr:
        lines.append(stderr if stderr.endswith("\n") else f"{stderr}\n")
    lines.append(f"agy-profile={profile_label}\n")
    if quota_exhausted:
        lines.append("agy-quota-exhausted=1\n")
    lines.append(f"agy-exit={exit_code}\n")
    with open(log_path, mode, encoding="utf-8") as fh:
        fh.writelines(lines)


def _run_preflight(
    launch_env: Mapping[str, str],
    preflight: Callable[[], int | bool] | None,
) -> tuple[bool, int]:
    if preflight is not None:
        res = preflight()
        if isinstance(res, bool):
            return res, (0 if res else 1)
        rc = int(res)
        return rc == 0, rc
    try:
        proc = subprocess.run(
            ["zsh", "-ic", "typeset -f _ag_link_ok _ag_rel_link ag_run >/dev/null"],
            env=dict(launch_env),
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0, proc.returncode
    except OSError:
        return False, 127


def _coerce_launch_output(raw: Any) -> tuple[int, str, str]:
    if isinstance(raw, subprocess.CompletedProcess):
        return int(raw.returncode), str(raw.stdout or ""), str(raw.stderr or "")
    rc, out, err = raw
    return int(rc), str(out or ""), str(err or "")


def _terminate_process_group(proc: subprocess.Popen[str]) -> None:
    """Send SIGTERM then SIGKILL to a child's process group and drain pipes."""
    pgid = proc.pid
    with contextlib.suppress(ProcessLookupError, OSError):
        os.killpg(pgid, signal.SIGTERM)

    deadline = time.monotonic() + 1.0
    alive = True
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            alive = False
            break
        time.sleep(0.05)

    if alive:
        with contextlib.suppress(ProcessLookupError, OSError):
            os.killpg(pgid, signal.SIGKILL)
    with contextlib.suppress(Exception):
        proc.communicate(timeout=0.5)


def _execute_launch(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdin_text: str,
    profile: str | None,
    via_ag_run: bool,
    launcher: Callable[..., Any] | None,
    active_proc_holder: list[subprocess.Popen[str] | None],
    timeout_seconds: float | None = None,
) -> tuple[int, str, str]:
    if launcher is not None:
        raw = launcher(
            argv,
            cwd=cwd,
            env=env,
            stdin_text=stdin_text,
            profile=profile,
            via_ag_run=via_ag_run,
        )
        return _coerce_launch_output(raw)
    try:
        proc = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
    except FileNotFoundError:
        return 127, "", f"CLI binary '{argv[0]}' not found on PATH"
    except OSError as exc:
        return 1, "", f"Failed to spawn process '{argv[0]}': {exc}"

    active_proc_holder[0] = proc
    try:
        out, err = proc.communicate(input=stdin_text, timeout=timeout_seconds)
        return int(proc.returncode or 0), str(out or ""), str(err or "")
    except subprocess.TimeoutExpired:
        _terminate_process_group(proc)
        return (
            124,
            "",
            f"Process timeout: execution timed out after {timeout_seconds}s",
        )
    finally:
        active_proc_holder[0] = None


def _run_with_heartbeat(
    *,
    owner_id: str | None,
    real_home: Path | str | None,
    heartbeat_seconds: float,
    fn: Callable[[], tuple[int, str, str]],
) -> tuple[int, str, str]:
    if owner_id is None:
        return fn()
    stop_event = threading.Event()
    interval = max(0.05, float(heartbeat_seconds))

    def _loop() -> None:
        while not stop_event.wait(timeout=interval):
            with contextlib.suppress(Exception):
                _pool.heartbeat(owner_id, real_home=real_home)

    hb_thread = threading.Thread(target=_loop, daemon=True)
    hb_thread.start()
    try:
        return fn()
    finally:
        stop_event.set()
        hb_thread.join(timeout=2.0)


def _format_busy_pool_report(
    status: Mapping[str, Any],
    *,
    skipped: Mapping[str, str],
    wait_seconds: float,
) -> list[str]:
    wait_display = (
        int(wait_seconds)
        if isinstance(wait_seconds, (int, float)) and float(wait_seconds).is_integer()
        else wait_seconds
    )
    lines = [f"Stopped: agy profile pool is busy (stayed in use for {wait_display} seconds)."]
    resident_profiles = [
        profile for profile, why in skipped.items() if why == "resident_process"
    ]
    for p_name in resident_profiles:
        lines.append(
            f"- {p_name} is held by a resident agy process (antigravity_homes/{p_name}/)"
        )
    leased_count = 0
    for entry in status.get("profiles") or []:
        p_name = str(entry.get("profile") or "")
        for holder in entry.get("leased_by") or []:
            leased_count += 1
            epic = str(holder.get("epic") or "unknown")
            task = str(holder.get("task") or "unknown")
            slot = holder.get("slot")
            slot_str = str(slot) if slot is not None else "?"
            lines.append(f"- {p_name} is held by {epic}/{task}/slot {slot_str}")
    if not resident_profiles and leased_count == 0:
        lines.append("- one or more pool profiles are currently busy")
    lines.append("Options:")
    lines.append(
        "- wait for the active profile to finish, or retry dispatch with --wait <seconds>"
    )
    if resident_profiles:
        target_pat = (
            f"antigravity_homes/{resident_profiles[0]}/"
            if len(resident_profiles) == 1
            else "antigravity_homes/<profile>/"
        )
        lines.append(
            f"- free the profile by closing its resident agy session (or `pkill -f '{target_pat}'`)"
        )
    if leased_count > 0 or not resident_profiles:
        lines.append(
            '- or run "/d3nexus:dev-config profiles release <name> --force" once stale'
        )
    return lines


def _build_no_profile_report(
    cwd: Path,
    binding: PersonaBinding,
    *,
    real_home: Path | str | None,
    host_profile: str | None,
    wait_seconds: float,
    which: Callable[[str], str | None],
    now: datetime | None,
    acq: Any | None = None,
) -> list[str]:
    status = _pool.pool_status(real_home=real_home, now=now, host_profile=host_profile)
    status["wait_seconds"] = wait_seconds
    acq_reason = getattr(acq, "reason", None) if acq is not None else None
    skipped = getattr(acq, "skipped", None) if acq is not None else None
    skipped_map = dict(skipped) if isinstance(skipped, Mapping) else {}
    if acq_reason == "pool_busy" and (
        status.get("state") != "busy"
        or any(why == "resident_process" for why in skipped_map.values())
    ):
        return _format_busy_pool_report(
            status,
            skipped=skipped_map,
            wait_seconds=wait_seconds,
        )
    cfg = _pc.load_persona_config(cwd, real_home=real_home)
    prog_binding = (
        binding
        if binding.persona == "programmer"
        else _pc.resolve_persona("programmer", cwd, real_home=real_home)
    )
    return list(
        _pool.exhaustion_report(
            status,
            catalogue=cfg["models"],
            programmer_binding=prog_binding,
            which=which,
            wait_seconds=wait_seconds,
        )
    )


def _dispatch_direct_non_pool(
    binding: PersonaBinding,
    mode: str,
    *,
    prompt_text: str,
    cwd_path: Path,
    log_path: Path,
    extra_env: Mapping[str, str] | None,
    extra_agy_args: list[str],
    profile_label: str | None,
    launcher: Callable[..., Any] | None,
    timeout_seconds: float | None = None,
) -> DispatchResult:
    base_argv = _pc.build_dispatch_argv(binding, mode)
    argv = [*base_argv, *extra_agy_args] if binding.cli == "agy" else base_argv
    base_env = dict(os.environ)
    if extra_env:
        base_env.update(extra_env)
    launch_env = _pc.build_dispatch_env(argv, base_env)

    holder: list[subprocess.Popen[str] | None] = [None]
    rc, out, err = _execute_launch(
        argv,
        cwd=cwd_path,
        env=launch_env,
        stdin_text=prompt_text,
        profile=profile_label,
        via_ag_run=False,
        launcher=launcher,
        active_proc_holder=holder,
        timeout_seconds=timeout_seconds,
    )
    failure_kind = _pc.classify_dispatch_failure(rc, out, err)
    _append_attempt_log(
        log_path,
        first_attempt=True,
        profile_label=profile_label or binding.cli,
        launch_mode="direct",
        stdout=out,
        stderr=err,
        exit_code=rc,
        quota_exhausted=(failure_kind == "model_unavailable" and _is_quota_stderr(err)),
    )
    if rc == 0:
        return DispatchResult(
            status="ok",
            profile_used=profile_label,
            attempts=1,
            exit_code=0,
            reason=None,
            report=[],
        )
    status = (
        "model_unavailable" if failure_kind == "model_unavailable" else "task_failure"
    )
    is_timeout = status == "task_failure" and rc == 124 and err.startswith("Process timeout:")
    reason = (
        "model_unavailable"
        if status == "model_unavailable"
        else ("timeout" if is_timeout else None)
    )
    return DispatchResult(
        status=status,
        profile_used=profile_label,
        attempts=1,
        exit_code=rc,
        reason=reason,
        report=[err] if is_timeout else [],
    )


def _run_single_attempt(
    *,
    profile: str,
    via_ag_run: bool,
    owner_id: str,
    attempt_num: int,
    agy_args: list[str],
    prompt_text: str,
    cwd_path: Path,
    log_path: Path,
    resolved_real_home: Path,
    extra_env: Mapping[str, str] | None,
    heartbeat_seconds: float,
    preflight_passed: bool,
    preflight: Callable[[], int | bool] | None,
    launcher: Callable[..., Any] | None,
    now: datetime | None,
    timeout_seconds: float | None = None,
) -> tuple[DispatchResult | None, int, bool]:
    """Execute one leased attempt and return (result_or_none_to_rotate, exit_code, preflight_ok)."""
    active_proc: list[subprocess.Popen[str] | None] = [None]
    prev_sigterm: Any = None
    installed_sigterm = False

    if threading.current_thread() is threading.main_thread():

        def _handle_sigterm(signum: int, _frame: FrameType | None) -> None:
            proc_ref = active_proc[0]
            if proc_ref is not None and proc_ref.poll() is None:
                with contextlib.suppress(ProcessLookupError, OSError):
                    os.killpg(proc_ref.pid, signal.SIGTERM)
                with contextlib.suppress(OSError):
                    proc_ref.terminate()
            raise SystemExit(128 + signum)

        prev_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, _handle_sigterm)
        installed_sigterm = True

    try:
        launch_env = dict(os.environ)
        if extra_env:
            launch_env.update(extra_env)
        if via_ag_run:
            launch_env["REAL_HOME"] = str(resolved_real_home)
            if not preflight_passed:
                pf_ok, pf_rc = _run_preflight(launch_env, preflight)
                if not pf_ok:
                    return (
                        DispatchResult(
                            status="preflight_failed",
                            profile_used=None,
                            attempts=attempt_num - 1,
                            exit_code=pf_rc or 1,
                            reason="preflight_failed",
                            report=[
                                "Preflight failed: zsh -ic missing _ag_link_ok, _ag_rel_link, or ag_run."
                            ],
                        ),
                        pf_rc or 1,
                        False,
                    )
                preflight_passed = True
            argv = ["zsh", "-ic", 'ag_run "$0" cli "$@"', profile, *agy_args]
            launch_mode = "ag_run"
        else:
            argv = ["agy", *agy_args]
            launch_mode = "direct"

        before_snap = _git_snapshot(cwd_path)
        rc, out, err = _run_with_heartbeat(
            owner_id=owner_id,
            real_home=resolved_real_home,
            heartbeat_seconds=heartbeat_seconds,
            fn=lambda: _execute_launch(
                argv,
                cwd=cwd_path,
                env=launch_env,
                stdin_text=prompt_text,
                profile=profile,
                via_ag_run=via_ag_run,
                launcher=launcher,
                active_proc_holder=active_proc,
                timeout_seconds=timeout_seconds,
            ),
        )
        failure_kind = _pc.classify_dispatch_failure(rc, out, err)
        is_quota = failure_kind == "model_unavailable" and _is_quota_stderr(err)
        after_snap = _git_snapshot(cwd_path) if is_quota else None

        _append_attempt_log(
            log_path,
            first_attempt=(attempt_num == 1),
            profile_label=profile,
            launch_mode=launch_mode,
            stdout=out,
            stderr=err,
            exit_code=rc,
            quota_exhausted=is_quota,
        )

        if rc == 0:
            return (
                DispatchResult(
                    status="ok",
                    profile_used=profile,
                    attempts=attempt_num,
                    exit_code=0,
                    reason=None,
                    report=[],
                ),
                0,
                preflight_passed,
            )

        if failure_kind != "model_unavailable":
            is_timeout = rc == 124 and err.startswith("Process timeout:")
            return (
                DispatchResult(
                    status="task_failure",
                    profile_used=profile,
                    attempts=attempt_num,
                    exit_code=rc,
                    reason="timeout" if is_timeout else None,
                    report=[err] if is_timeout else [],
                ),
                rc,
                preflight_passed,
            )

        if not is_quota:
            return (
                DispatchResult(
                    status="model_unavailable",
                    profile_used=profile,
                    attempts=attempt_num,
                    exit_code=rc,
                    reason="model_unavailable",
                    report=[],
                ),
                rc,
                preflight_passed,
            )

        _pool.mark_exhausted(
            profile,
            reason="5h",
            real_home=resolved_real_home,
            now=now,
        )
        work_started = (
            before_snap is None or after_snap is None or before_snap != after_snap
        )
        if work_started:
            return (
                DispatchResult(
                    status="quota_midrun",
                    profile_used=profile,
                    attempts=attempt_num,
                    exit_code=rc,
                    reason="quota_midrun",
                    report=[],
                ),
                rc,
                preflight_passed,
            )
        return None, rc, preflight_passed
    finally:
        if installed_sigterm:
            signal.signal(signal.SIGTERM, prev_sigterm)
        _pool.release(owner_id, real_home=resolved_real_home, now=now)


def run_on_pool(
    binding: PersonaBinding,
    mode: str,
    *,
    prompt_file: Path | str,
    cwd: Path | str,
    log: Path | str,
    owner: Mapping[str, Any] | str,
    real_home: Path | str | None = None,
    extra_env: Mapping[str, str] | None = None,
    wait_seconds: float = 0,
    poll_seconds: float = 15,
    host_profile: str | None | object = _AUTO_HOST,
    thresholds: Mapping[str, float] | None = None,
    launcher: Callable[..., Any] | None = None,
    fetcher: Callable[[str], Mapping[str, Any]] | None = None,
    resident_probe: Callable[[str], bool] | None = None,
    preflight: Callable[[], int | bool] | None = None,
    which: Callable[[str], str | None] = shutil.which,
    now: datetime | None = None,
    timeout_seconds: float | None = None,
) -> DispatchResult:
    """Acquire an agy profile lease, run preflight/launch with heartbeat, and rotate on clean quota errors."""
    prompt_path = Path(prompt_file)
    prompt_text = prompt_path.read_text(encoding="utf-8")
    cwd_path = Path(cwd)
    log_path = Path(log)

    if binding.cli != "agy":
        return _dispatch_direct_non_pool(
            binding,
            mode,
            prompt_text=prompt_text,
            cwd_path=cwd_path,
            log_path=log_path,
            extra_env=extra_env,
            extra_agy_args=[],
            profile_label=None,
            launcher=launcher,
            timeout_seconds=timeout_seconds,
        )

    resolved_real_home = _pc.get_real_home(real_home)
    pool_cfg = _pool.load_pool_config(real_home=resolved_real_home)
    resolved_host: str | None = (
        _pool.detect_host_profile() if host_profile is _AUTO_HOST else host_profile  # type: ignore[assignment]
    )

    extra_agy_args = list(pool_cfg["agy_extra_args"])
    if not pool_cfg["pool"]:
        return _dispatch_direct_non_pool(
            binding,
            mode,
            prompt_text=prompt_text,
            cwd_path=cwd_path,
            log_path=log_path,
            extra_env=extra_env,
            extra_agy_args=extra_agy_args,
            profile_label=resolved_host,
            launcher=launcher,
            timeout_seconds=timeout_seconds,
        )

    active_thresholds = (
        dict(thresholds) if thresholds is not None else _load_thresholds(cwd_path)
    )
    agy_args = [*_pc.build_dispatch_argv(binding, mode)[1:], *extra_agy_args]
    heartbeat_seconds = float(pool_cfg["heartbeat_seconds"])
    quota_pool = _pc.quota_pool_for(binding)

    attempts = 0
    last_rc = 2
    preflight_passed = False
    tried_profiles: set[str] = set()

    while True:
        acq = _pool.acquire(
            owner,
            real_home=resolved_real_home,
            host_profile=resolved_host,
            quota_pool=quota_pool,
            thresholds=active_thresholds,
            fetcher=fetcher,
            resident_probe=resident_probe,
            wait_seconds=wait_seconds if attempts == 0 else 0,
            poll_seconds=poll_seconds,
            now=now,
            preferred_profile=binding.profile,
        )
        if acq.profile is None:
            report = _build_no_profile_report(
                cwd_path,
                binding,
                real_home=resolved_real_home,
                host_profile=resolved_host,
                wait_seconds=wait_seconds,
                which=which,
                now=now,
                acq=acq,
            )
            return DispatchResult(
                status="no_profile",
                profile_used=None,
                attempts=attempts,
                exit_code=last_rc if attempts > 0 else 2,
                reason=acq.reason,
                report=report,
            )

        profile = acq.profile
        if profile in tried_profiles:
            _pool.release(acq.owner_id, real_home=resolved_real_home, now=now)
            report = _build_no_profile_report(
                cwd_path,
                binding,
                real_home=resolved_real_home,
                host_profile=resolved_host,
                wait_seconds=wait_seconds,
                which=which,
                now=now,
            )
            return DispatchResult(
                status="no_profile",
                profile_used=None,
                attempts=attempts,
                exit_code=last_rc if attempts > 0 else 2,
                reason="pool_exhausted",
                report=report,
            )

        attempts += 1
        tried_profiles.add(profile)
        outcome, rc, preflight_passed = _run_single_attempt(
            profile=profile,
            via_ag_run=acq.via_ag_run,
            owner_id=acq.owner_id,
            attempt_num=attempts,
            agy_args=agy_args,
            prompt_text=prompt_text,
            cwd_path=cwd_path,
            log_path=log_path,
            resolved_real_home=resolved_real_home,
            extra_env=extra_env,
            heartbeat_seconds=heartbeat_seconds,
            preflight_passed=preflight_passed,
            preflight=preflight,
            launcher=launcher,
            now=now,
            timeout_seconds=timeout_seconds,
        )
        last_rc = rc
        if outcome is not None:
            if outcome.status == "preflight_failed":
                return DispatchResult(
                    status=outcome.status,
                    profile_used=outcome.profile_used,
                    attempts=attempts - 1,
                    exit_code=outcome.exit_code,
                    reason=outcome.reason,
                    report=outcome.report,
                )
            return outcome
