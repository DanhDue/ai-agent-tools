"""Polyglot registry verification and multi-provider fanout engine.

Validates multi-provider quality manifests and simulates or executes concurrent provider
fan-out with deterministic aggregation (FAIL > BLOCKED > PASS), live zero-token stderr
heartbeats, atomic namespaced quality_active.json telemetry, and signal-safe child reaping.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
import concurrent.futures
from datetime import datetime, timezone
import fcntl
import importlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import uuid

SCRIPT_DIR = Path(__file__).resolve().parent
KIT_ROOT = Path(__file__).resolve().parents[4]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

_IN_PROCESS_STATE_LOCK = threading.Lock()


class _SignalAbort(BaseException):
    """Internal BaseException raised on SIGINT/SIGTERM to trigger child reaping."""

    def __init__(self, signum: int) -> None:
        self.signum = signum
        super().__init__(f"Aborted by signal {signum}")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _generate_run_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{ts}-{os.getpid()}-{uuid.uuid4().hex[:6]}"


def _load_state_envelope() -> Any | None:
    """Import scripts/_state_envelope lazily when present in KIT_ROOT."""
    scripts_dir = KIT_ROOT / "scripts"
    if not (scripts_dir / "_state_envelope.py").is_file():
        return None
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    try:
        return importlib.import_module("_state_envelope")
    except ImportError:
        return None


def _estimate_ttl_sec(profile: str, has_e2e: bool = False) -> int:
    """Derive lease TTL max(120, estimated_sec * 2) via estimate_heartbeat if present."""
    scripts_dir = KIT_ROOT / "scripts"
    if (scripts_dir / "estimate_heartbeat.py").is_file():
        if str(scripts_dir) not in sys.path:
            sys.path.insert(0, str(scripts_dir))
        try:
            eh = importlib.import_module("estimate_heartbeat")
            valid_profiles = {"fast", "pr", "epic", "release", "full"}
            mapped = (
                profile
                if profile in valid_profiles
                else ("epic" if profile == "scheduled" else None)
            )
            est = eh.estimate_workload(quality_profile=mapped, has_e2e=has_e2e)
            return max(120, int(est["estimated_sec"]) * 2)
        except (ImportError, ValueError, KeyError, TypeError):
            pass
    return 480


def _read_json_safe(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return dict(default)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return dict(default)


def _atomic_write_bytes(target: Path, data: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp"
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
    except BaseException:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _atomic_write_json(target: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, indent=2) + "\n").encode("utf-8")
    _atomic_write_bytes(target, encoded)


def _copy_file_atomic(src: Path, dest: Path) -> None:
    if not src.is_file() or src.resolve() == dest.resolve():
        return
    try:
        _atomic_write_bytes(dest, src.read_bytes())
    except OSError:
        pass


def _resolve_shared_devtool_dirs(start_path: Path) -> list[Path]:
    """Resolve primary repo .devtool/ first, followed by active worktree .devtool/."""
    env_mod = _load_state_envelope()
    if env_mod is not None and hasattr(env_mod, "resolve_shared_devtool_dirs"):
        try:
            resolved = env_mod.resolve_shared_devtool_dirs(start_path)
            if isinstance(resolved, list) and resolved:
                return [Path(p) for p in resolved]
        except (OSError, ValueError, TypeError) as exc:
            sys.stderr.write(f"[quality_check] state envelope path fallback: {exc}\n")

    resolved_start = start_path.resolve()
    dirs: list[Path] = []
    try:
        common_proc = subprocess.run(
            ["git", "-C", str(resolved_start), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            check=False,
        )
        top_proc = subprocess.run(
            ["git", "-C", str(resolved_start), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
        if common_proc.returncode == 0 and common_proc.stdout.strip():
            common_raw = Path(common_proc.stdout.strip())
            common_abs = (
                common_raw.resolve()
                if common_raw.is_absolute()
                else (resolved_start / common_raw).resolve()
            )
            primary_root = (
                common_abs.parent if common_abs.name == ".git" else common_abs
            )
            dirs.append(primary_root / ".devtool")
        if top_proc.returncode == 0 and top_proc.stdout.strip():
            wt_devtool = Path(top_proc.stdout.strip()).resolve() / ".devtool"
            if wt_devtool not in dirs:
                dirs.append(wt_devtool)
    except (subprocess.SubprocessError, OSError):
        pass

    if not dirs:
        dirs.append(resolved_start / ".devtool")
    return dirs


def _run_quality_state_transaction(
    start_path: Path,
    mutator: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Run locked read-modify-write update on quality_active.json across shared devtool dirs."""
    default: dict[str, Any] = {"schema_version": 1, "generation": 0, "runs": {}}
    env_mod = _load_state_envelope()
    if env_mod is not None and hasattr(env_mod, "run_state_transaction"):
        try:
            with _IN_PROCESS_STATE_LOCK:
                res = env_mod.run_state_transaction(
                    start_path, "quality_active.json", mutator, default
                )
            if isinstance(res, dict):
                return res
        except (TypeError, OSError):
            pass

    devtool_dirs = _resolve_shared_devtool_dirs(start_path)
    primary_state = devtool_dirs[0] / "state"
    primary_state.mkdir(parents=True, exist_ok=True)
    lock_path = primary_state / ".state_envelope.lock"
    target_name = "quality_active.json"

    with _IN_PROCESS_STATE_LOCK, lock_path.open("a+", encoding="utf-8") as lock_fh:
        fcntl.flock(lock_fh.fileno(), fcntl.LOCK_EX)
        try:
            primary_file = primary_state / target_name
            current = _read_json_safe(primary_file, default)
            prev_gen = int(current.get("generation", 0) or 0)
            updated = dict(mutator(current))
            updated["schema_version"] = 1
            next_gen = max(prev_gen + 1, int(updated.get("generation", 0) or 0))
            updated["generation"] = next_gen
            _atomic_write_json(primary_file, updated)
            for mirror_dir in devtool_dirs[1:]:
                mirror_file = mirror_dir / "state" / target_name
                existing_mirror = _read_json_safe(mirror_file, default)
                mirror_gen = int(existing_mirror.get("generation", 0) or 0)
                if mirror_gen < next_gen:
                    _atomic_write_json(mirror_file, updated)
            return updated
        finally:
            fcntl.flock(lock_fh.fileno(), fcntl.LOCK_UN)


def _auto_resolve_epic_slug(repo_root: Path | None) -> str | None:
    """Resolve epic slug from active branch, state heartbeat, or feature frontmatter."""
    if repo_root is None:
        return None
    try:
        branch_proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if branch_proc.returncode == 0:
            branch = branch_proc.stdout.strip()
            if branch.startswith("epic/"):
                slug = branch[len("epic/") :]
                if "-slot-" in slug:
                    slug = slug.rsplit("-slot-", 1)[0]
                if slug:
                    return slug
    except (subprocess.SubprocessError, OSError):
        pass

    features_dir = repo_root / ".devtool" / "features"
    if features_dir.is_dir():
        for task_file in sorted(features_dir.glob("task_*.md")):
            try:
                for line in task_file.read_text(encoding="utf-8").splitlines()[:20]:
                    if line.startswith("epic:"):
                        val = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
            except OSError:
                continue
    return None


def _terminate_process_group(
    proc: subprocess.Popen[Any], grace_sec: float = 1.0
) -> None:
    """Send SIGTERM to process group, wait briefly, escalate to SIGKILL, and reap."""
    if proc.poll() is not None:
        try:
            proc.wait(timeout=1.0)
        except subprocess.SubprocessError:
            pass
        return

    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        pass

    deadline = time.monotonic() + max(0.1, grace_sec)
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            break
        time.sleep(0.02)

    if proc.poll() is None:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    try:
        proc.wait(timeout=2.0)
    except subprocess.SubprocessError:
        pass


class _QualityRunCoordinator:
    """Tracks run_id ownership, stderr heartbeat ticks, quality_active.json, and child PGs."""

    def __init__(
        self,
        *,
        run_id: str,
        repo_root: Path | None,
        profile: str,
        epic_slug: str | None,
        heartbeat_interval: float,
        step_total: int,
        ttl_sec: int,
    ) -> None:
        self.run_id = run_id
        self.repo_root = repo_root
        self.profile = profile
        self.epic_slug = epic_slug
        self.heartbeat_interval = max(0.01, float(heartbeat_interval))
        self.step_total = max(1, int(step_total))
        self.ttl_sec = ttl_sec
        self.pid = os.getpid()
        self.host = socket.gethostname()
        self.started_at = _utc_now_iso()
        self.start_monotonic = time.monotonic()
        self.aborted = False
        self.abort_signal: int | None = None
        self._lock = threading.Lock()
        self._next_step = 0
        self._active_procs: dict[int, subprocess.Popen[Any]] = {}
        self._last_provider = ""
        self._last_capability = ""
        self._last_step_index = 0

    def register_proc(self, proc: subprocess.Popen[Any]) -> bool:
        with self._lock:
            if self.aborted:
                return False
            self._active_procs[proc.pid] = proc
            return True

    def unregister_proc(self, proc: subprocess.Popen[Any]) -> None:
        with self._lock:
            self._active_procs.pop(proc.pid, None)

    def abort_and_reap_children(self, grace_sec: float = 1.0) -> None:
        self.aborted = True
        with self._lock:
            procs = list(self._active_procs.values())
        for proc in procs:
            _terminate_process_group(proc, grace_sec=grace_sec)

    def start_step(self, provider: str, capability: str) -> int:
        with self._lock:
            self._next_step += 1
            step_index = self._next_step
            self.step_total = max(self.step_total, step_index)
            self._last_provider = provider
            self._last_capability = capability
            self._last_step_index = step_index
        self._write_run_state(
            status="running",
            provider=provider,
            capability=capability,
            step_index=step_index,
            finished_at=None,
        )
        return step_index

    def mark_running(self, provider: str = "", capability: str = "") -> None:
        self._write_run_state(
            status="running",
            provider=provider or self._last_provider,
            capability=capability or self._last_capability,
            step_index=self._last_step_index,
            finished_at=None,
        )

    def emit_heartbeat(self, provider: str, capability: str, step_index: int) -> None:
        elapsed = max(0.0, time.monotonic() - self.start_monotonic)
        elapsed_str = (
            f"{round(elapsed)}" if self.heartbeat_interval >= 1.0 else f"{elapsed:.1f}"
        )
        sys.stderr.write(
            f"[quality_check] {step_index}/{self.step_total} "
            f"{provider}:{capability} ({elapsed_str}s elapsed)\n"
        )
        sys.stderr.flush()
        self._write_run_state(
            status="running",
            provider=provider,
            capability=capability,
            step_index=step_index,
            finished_at=None,
        )

    def finalize(self, status: str) -> None:
        finished_at = _utc_now_iso()
        self._write_run_state(
            status=status,
            provider=self._last_provider,
            capability=self._last_capability,
            step_index=self._last_step_index,
            finished_at=finished_at,
        )

    def _write_run_state(
        self,
        *,
        status: str,
        provider: str,
        capability: str,
        step_index: int,
        finished_at: str | None,
    ) -> None:
        if self.repo_root is None:
            return
        now_iso = _utc_now_iso()
        elapsed = round(max(0.0, time.monotonic() - self.start_monotonic), 3)
        entry: dict[str, Any] = {
            "run_id": self.run_id,
            "epic_slug": self.epic_slug,
            "profile": self.profile,
            "status": status,
            "provider": provider,
            "capability": capability,
            "step_index": step_index,
            "step_total": self.step_total,
            "pid": self.pid,
            "host": self.host,
            "ttl_sec": self.ttl_sec,
            "started_at": self.started_at,
            "updated_at": now_iso,
            "finished_at": finished_at,
            "elapsed_sec": elapsed,
        }

        def _mutate(current: dict[str, Any]) -> dict[str, Any]:
            runs_raw = current.get("runs")
            runs: dict[str, Any] = dict(runs_raw) if isinstance(runs_raw, dict) else {}
            runs[self.run_id] = entry

            summary_run_id = self.run_id
            summary_profile = self.profile
            summary_status = status
            if status != "running":
                active_sibling = next(
                    (
                        r
                        for rid, r in runs.items()
                        if rid != self.run_id
                        and isinstance(r, dict)
                        and r.get("status") == "running"
                    ),
                    None,
                )
                if active_sibling is not None:
                    summary_run_id = str(active_sibling.get("run_id", self.run_id))
                    summary_profile = str(active_sibling.get("profile", self.profile))
                    summary_status = "running"

            return {
                "schema_version": 1,
                "run_id": summary_run_id,
                "profile": summary_profile,
                "status": summary_status,
                "runs": runs,
            }

        try:
            _run_quality_state_transaction(self.repo_root, _mutate)
        except OSError:
            pass


def _resolve_repo_root(path: Path) -> Path:
    p = path.resolve()
    for parent in [p] + list(p.parents):
        if parent.name == ".agents":
            return parent.parent
    for parent in [p] + list(p.parents):
        if (parent / ".git").exists():
            return parent
    return p.parents[2] if len(p.parents) >= 3 else p.parent


def _get_git_head(repo_path: Path) -> str:
    """Retrieve actual Git HEAD commit hash if repo_path is inside a git working tree."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return ""


def _get_validator() -> Callable[..., dict[str, Any]]:
    mod = importlib.import_module("validate_quality_contract")
    val_fn: Callable[..., dict[str, Any]] = mod.validate_registry
    return val_fn


def _get_aggregator() -> Callable[..., dict[str, Any]]:
    mod = importlib.import_module("aggregate_quality_results")
    agg_fn: Callable[..., dict[str, Any]] = mod.aggregate_results
    return agg_fn


def _find_manifest_path(root: Path, provider_item: dict[str, Any]) -> Path | None:
    p_id = provider_item.get("id", "")
    skill = provider_item.get("skill", "")
    candidates = [root / ".agents" / "quality" / f"{p_id}.json"]
    platform = p_id.split("-")[0]
    if platform:
        candidates.append(root / ".agents" / "quality" / f"{platform}-quality.json")
    for part in skill.split(":")[-1].split("-"):
        if part and part not in ("quality", "check"):
            candidates.append(root / ".agents" / "quality" / f"{part}-quality.json")
    return next((c for c in candidates if c and c.is_file()), None)


def _plan_step_stats(
    plan_providers: list[dict[str, Any]], profile: str, repo_root: Path | None
) -> tuple[int, bool]:
    """Count total planned capabilities across providers and detect E2E workloads."""
    if repo_root is None:
        return max(1, len(plan_providers)), False
    total = 0
    has_e2e = False
    for item in plan_providers:
        manifest_path = _find_manifest_path(repo_root, item)
        if manifest_path is None:
            total += 1
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            total += 1
            continue
        caps = manifest.get("profiles", {}).get(profile)
        if isinstance(caps, list) and caps:
            total += len(caps)
            if any(
                "e2e" in str(c).lower() or "playwright" in str(c).lower() for c in caps
            ):
                has_e2e = True
        else:
            total += 1
    return max(1, total), has_e2e


def fanout_and_aggregate(
    registry_data: dict[str, Any],
    requested_profile: str,
    repository_sha: str,
    base_ref: str = "main",
    provider_results: list[dict[str, Any]] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Validate polyglot registry, select profile providers, and aggregate provider results."""
    val_fn = _get_validator()
    val = val_fn(registry_data, requested_profile)
    if val["status"] == "BLOCKED":
        return {
            "status": "BLOCKED",
            "findings": val["findings"],
            "aggregated": None,
        }

    plan = val["providers"]
    results = provider_results or []
    findings: list[dict[str, Any]] = []

    if repo_root is not None:
        actual_head = _get_git_head(repo_root)
        if actual_head and repository_sha and repository_sha != actual_head:
            findings.append(
                {
                    "code": "repository_sha_mismatch",
                    "message": f"Requested repository SHA '{repository_sha}' does not match actual Git HEAD '{actual_head}'",
                }
            )

    for p in results:
        p_sha = p.get("repository_sha", "")
        p_started = p.get("started_head", "")
        p_finished = p.get("finished_head", "")
        if p_started and p_finished and p_started != p_finished:
            findings.append(
                {
                    "code": "git_head_drift",
                    "message": f"[{p.get('provider_id')}] Git HEAD drifted during execution from '{p_started}' to '{p_finished}'",
                }
            )
        if repository_sha and p_sha and p_sha != repository_sha:
            findings.append(
                {
                    "code": "repository_sha_mismatch",
                    "message": f"[{p.get('provider_id')}] Provider SHA '{p_sha}' does not match requested repository SHA '{repository_sha}'",
                }
            )

    invocation = {
        "contract_version": 1,
        "profile": requested_profile,
        "repository_sha": repository_sha,
        "base_ref": base_ref,
    }

    agg_fn = _get_aggregator()
    aggregated = agg_fn(plan, results, invocation=invocation)

    overall_status = aggregated.get("status", "PASS")
    if findings:
        overall_status = "FAIL"
        for f in findings:
            aggregated["status"] = "FAIL"
            aggregated.setdefault("blockers", []).append(f["message"])

    return {
        "status": overall_status,
        "findings": findings,
        "plan": plan,
        "aggregated": aggregated,
    }


def _run_capability_subprocess(
    *,
    substituted_cmd: list[str],
    root: Path,
    run_log_file: Path,
    compat_log_file: Path,
    coordinator: _QualityRunCoordinator,
    provider_id: str,
    cap_name: str,
    step_idx: int,
) -> tuple[str, str, float]:
    """Execute one capability via Popen(start_new_session=True) with heartbeat polling."""
    cap_start = time.time()
    poll_interval = coordinator.heartbeat_interval
    poll_slice = min(poll_interval, 0.25)

    run_log_file.parent.mkdir(parents=True, exist_ok=True)
    proc: subprocess.Popen[Any] | None = None
    try:
        with run_log_file.open("w", encoding="utf-8") as log_fh:
            log_fh.write(f"$ {' '.join(substituted_cmd)}\n\n--- OUTPUT ---\n")
            log_fh.flush()
            proc = subprocess.Popen(
                substituted_cmd,
                cwd=str(root),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            if not coordinator.register_proc(proc):
                _terminate_process_group(proc)
                c_status = "FAIL"
                summary = f"{cap_name}: aborted by signal"
                cap_duration = round(time.time() - cap_start, 3)
                return c_status, summary, cap_duration

            last_tick = time.monotonic()
            while True:
                if coordinator.aborted:
                    _terminate_process_group(proc)
                    returncode = proc.returncode if proc.returncode is not None else -15
                    break
                try:
                    returncode = proc.wait(timeout=poll_slice)
                    break
                except subprocess.TimeoutExpired:
                    now_mono = time.monotonic()
                    if now_mono - last_tick >= poll_interval:
                        last_tick = now_mono
                        coordinator.emit_heartbeat(
                            provider=provider_id,
                            capability=cap_name,
                            step_index=step_idx,
                        )
    except OSError as exc:
        cap_duration = round(time.time() - cap_start, 3)
        run_log_file.write_text(
            f"$ {' '.join(substituted_cmd)}\n\n--- ERROR ---\n{exc}\n",
            encoding="utf-8",
        )
        _copy_file_atomic(run_log_file, compat_log_file)
        return "BLOCKED", f"{cap_name}: failed to execute: {exc}", cap_duration
    finally:
        if proc is not None:
            coordinator.unregister_proc(proc)

    cap_duration = round(time.time() - cap_start, 3)
    _copy_file_atomic(run_log_file, compat_log_file)
    if coordinator.aborted:
        return "FAIL", f"{cap_name}: aborted by signal", cap_duration
    c_status = "PASS" if returncode == 0 else "FAIL"
    summary = (
        f"{cap_name}: passed"
        if c_status == "PASS"
        else f"{cap_name}: failed with return code {returncode}"
    )
    return c_status, summary, cap_duration


def _execute_web_provider(
    *,
    provider_item: dict[str, Any],
    manifest_data: dict[str, Any],
    profile: str,
    sha: str,
    base_ref: str,
    root: Path,
    skills_dir: Path,
    coordinator: _QualityRunCoordinator,
) -> dict[str, Any]:
    """Run web-quality provider with periodic heartbeat thread and run-isolated log copies."""
    p_id = provider_item.get("id", "")
    step_idx = coordinator.start_step(p_id, "web")
    stop_event = threading.Event()

    def _ticker() -> None:
        while not stop_event.wait(timeout=coordinator.heartbeat_interval):
            if coordinator.aborted:
                return
            coordinator.emit_heartbeat(
                provider=p_id, capability="web", step_index=step_idx
            )

    ticker_thread = threading.Thread(target=_ticker, daemon=True)
    ticker_thread.start()
    try:
        web_scripts = skills_dir / "web-quality-check" / "resources" / "scripts"
        if str(web_scripts) not in sys.path:
            sys.path.insert(0, str(web_scripts))
        web_mod = importlib.import_module("validate_web_quality")
        web_res: dict[str, Any] = web_mod.run_capabilities(
            config=manifest_data,
            profile=profile,
            repository_sha=sha,
            repo_root=root,
            provider_id=p_id,
            base_ref=base_ref,
            skills_dir=skills_dir,
            check_watchdog_evidence=True,
        )
        run_log_dir = root / "build" / "quality" / p_id / "runs" / coordinator.run_id
        run_log_dir.mkdir(parents=True, exist_ok=True)
        p_log_dir = root / "build" / "quality" / p_id
        p_log_dir.mkdir(parents=True, exist_ok=True)
        for ev in web_res.get("evidence", []):
            if not isinstance(ev, dict):
                continue
            loc = ev.get("location", "")
            src_log = root / loc if loc else None
            if src_log is not None and src_log.is_file():
                _copy_file_atomic(src_log, run_log_dir / src_log.name)
                if p_id and p_id != "web":
                    _copy_file_atomic(src_log, p_log_dir / src_log.name)
        return web_res
    except Exception as exc:  # noqa: BLE001
        return {
            "provider_id": p_id,
            "contract_version": 1,
            "profile": profile,
            "repository_sha": sha,
            "status": "FAIL",
            "required": provider_item.get("required", True),
            "checks": [],
            "coverage": {},
            "evidence": [],
            "started_head": sha,
            "finished_head": sha,
            "duration": 0.0,
            "blockers": [f"Error executing provider '{p_id}': {exc}"],
            "warnings": [],
        }
    finally:
        stop_event.set()
        ticker_thread.join(timeout=1.0)


def _execute_with_coordinator(
    *,
    repo_root: Path | None,
    profile: str,
    epic_slug: str | None,
    heartbeat_interval: float,
    step_total: int,
    has_e2e: bool,
    run_id: str | None,
    fn: Callable[[_QualityRunCoordinator], dict[str, Any]],
) -> dict[str, Any]:
    """Run fn under signal handlers, child reaping, and finally-safe quality_active cleanup."""
    resolved_epic = (
        epic_slug if epic_slug is not None else _auto_resolve_epic_slug(repo_root)
    )
    coordinator = _QualityRunCoordinator(
        run_id=run_id or _generate_run_id(),
        repo_root=repo_root,
        profile=profile,
        epic_slug=resolved_epic,
        heartbeat_interval=heartbeat_interval,
        step_total=step_total,
        ttl_sec=_estimate_ttl_sec(profile, has_e2e=has_e2e),
    )

    is_main = threading.current_thread() is threading.main_thread()
    prev_sigint: Any = None
    prev_sigterm: Any = None

    def _on_signal(signum: int, _frame: Any) -> None:
        coordinator.aborted = True
        coordinator.abort_signal = signum
        raise _SignalAbort(signum)

    if is_main:
        prev_sigint = signal.getsignal(signal.SIGINT)
        prev_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGINT, _on_signal)
        signal.signal(signal.SIGTERM, _on_signal)

    coordinator.mark_running()
    final_status = "failed"
    try:
        res = fn(coordinator)
        final_status = "passed" if res.get("status") == "PASS" else "failed"
        return res
    except _SignalAbort:
        final_status = "aborted"
        coordinator.abort_and_reap_children()
        raise
    except BaseException:
        coordinator.abort_and_reap_children()
        raise
    finally:
        if is_main:
            signal.signal(signal.SIGINT, prev_sigint)
            signal.signal(signal.SIGTERM, prev_sigterm)
        if coordinator.aborted:
            final_status = "aborted"
        coordinator.finalize(final_status)


def execute_provider(
    provider_item: dict[str, Any],
    profile: str,
    sha: str,
    base_ref: str = "main",
    repo_root: Path | None = None,
    heartbeat_interval: float = 15.0,
    epic_slug: str | None = None,
    run_id: str | None = None,
    _coordinator: _QualityRunCoordinator | None = None,
) -> dict[str, Any]:
    """Execute one provider's profile capabilities with isolated logs and live heartbeats."""
    root = repo_root or Path.cwd()
    p_id = provider_item.get("id", "")
    skill = provider_item.get("skill", "")

    actual_started_head = _get_git_head(root)
    head_recorded = actual_started_head or sha

    manifest_path = _find_manifest_path(root, provider_item)
    if not manifest_path:
        return {
            "provider_id": p_id,
            "contract_version": 1,
            "profile": profile,
            "repository_sha": sha,
            "status": "BLOCKED",
            "required": provider_item.get("required", True),
            "checks": [],
            "coverage": {},
            "evidence": [],
            "started_head": head_recorded,
            "finished_head": head_recorded,
            "duration": 0.0,
            "blockers": [f"Manifest file for provider '{p_id}' not found"],
            "warnings": [],
        }

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return {
            "provider_id": p_id,
            "contract_version": 1,
            "profile": profile,
            "repository_sha": sha,
            "status": "BLOCKED",
            "required": provider_item.get("required", True),
            "checks": [],
            "coverage": {},
            "evidence": [],
            "started_head": head_recorded,
            "finished_head": head_recorded,
            "duration": 0.0,
            "blockers": [f"Failed to parse manifest '{manifest_path}': {e}"],
            "warnings": [],
        }

    skills_dir = Path(__file__).resolve().parents[3]

    def _run_with_coord(coordinator: _QualityRunCoordinator) -> dict[str, Any]:
        if "web" in p_id or "web" in skill:
            return _execute_web_provider(
                provider_item=provider_item,
                manifest_data=manifest_data,
                profile=profile,
                sha=sha,
                base_ref=base_ref,
                root=root,
                skills_dir=skills_dir,
                coordinator=coordinator,
            )

        validator_warnings: list[str] = []
        platform_name = None
        for p in ("python", "android", "flutter", "ios", "rust"):
            if p in p_id or p in skill:
                platform_name = p
                break

        if platform_name:
            p_scripts = (
                skills_dir / f"{platform_name}-quality-check" / "resources" / "scripts"
            )
            if p_scripts.is_dir() and str(p_scripts) not in sys.path:
                sys.path.insert(0, str(p_scripts))
            try:
                mod = importlib.import_module(f"validate_{platform_name}_quality")
                val_fn = getattr(mod, f"validate_{platform_name}_config", None)
                if val_fn:
                    v_res = val_fn(manifest_data, profile)
                    if v_res.get("status") == "BLOCKED":
                        return {
                            "provider_id": p_id,
                            "contract_version": 1,
                            "profile": profile,
                            "repository_sha": sha,
                            "status": "BLOCKED",
                            "required": provider_item.get("required", True),
                            "checks": [],
                            "coverage": {},
                            "evidence": [],
                            "started_head": sha,
                            "finished_head": sha,
                            "duration": 0.0,
                            "blockers": v_res.get("findings", []),
                            "warnings": validator_warnings,
                        }
            except Exception as exc:  # noqa: BLE001
                validator_warnings.append(
                    f"Platform validator check skipped for '{p_id}': {exc}"
                )

        start_time = time.time()
        profiles = manifest_data.get("profiles", {})
        caps_to_run = profiles.get(profile)
        if caps_to_run is None:
            return {
                "provider_id": p_id,
                "contract_version": 1,
                "profile": profile,
                "repository_sha": sha,
                "status": "BLOCKED",
                "required": provider_item.get("required", True),
                "checks": [],
                "coverage": {},
                "evidence": [],
                "started_head": head_recorded,
                "finished_head": head_recorded,
                "duration": 0.0,
                "blockers": [
                    f"Requested profile '{profile}' is not configured in profiles"
                ],
                "warnings": validator_warnings,
            }

        capabilities = manifest_data.get("capabilities", {})
        checks: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []
        blockers: list[dict[str, Any]] = []
        overall_status = "PASS"
        compat_log_dir = root / "build" / "quality" / p_id
        compat_log_dir.mkdir(parents=True, exist_ok=True)
        run_log_dir = compat_log_dir / "runs" / coordinator.run_id
        run_log_dir.mkdir(parents=True, exist_ok=True)

        if actual_started_head and sha and sha != actual_started_head:
            overall_status = "FAIL"
            blockers.append(
                {
                    "code": "repository_sha_mismatch",
                    "message": f"Requested repository SHA '{sha}' does not match actual Git HEAD '{actual_started_head}'",
                }
            )

        for cap_name in caps_to_run:
            if coordinator.aborted:
                overall_status = "FAIL"
                blockers.append(
                    {
                        "code": "aborted_by_signal",
                        "capability": cap_name,
                        "message": f"{cap_name}: aborted by signal",
                    }
                )
                break

            cap_val = capabilities.get(cap_name)
            if isinstance(cap_val, dict):
                cmd = cap_val.get("command", [])
            elif isinstance(cap_val, list):
                cmd = cap_val
            else:
                cmd = []

            if not cmd:
                continue

            substituted_cmd = [
                arg.replace("{base_ref}", base_ref).replace(
                    "{skills_dir}", str(skills_dir)
                )
                for arg in cmd
            ]
            step_idx = coordinator.start_step(p_id, cap_name)
            run_log_file = run_log_dir / f"{cap_name}.log"
            compat_log_file = compat_log_dir / f"{cap_name}.log"
            c_status, summary, cap_duration = _run_capability_subprocess(
                substituted_cmd=substituted_cmd,
                root=root,
                run_log_file=run_log_file,
                compat_log_file=compat_log_file,
                coordinator=coordinator,
                provider_id=p_id,
                cap_name=cap_name,
                step_idx=step_idx,
            )

            evidence_id = f"{cap_name}-evidence"
            rel_log_path = (
                str(run_log_file.relative_to(root)) if run_log_file.is_file() else ""
            )
            checks.append(
                {
                    "id": cap_name,
                    "category": "quality-check",
                    "status": c_status,
                    "source": " ".join(substituted_cmd),
                    "duration": cap_duration,
                    "summary": summary,
                    "evidence_refs": [evidence_id] if rel_log_path else [],
                }
            )
            if rel_log_path:
                evidence.append(
                    {
                        "id": evidence_id,
                        "type": "command",
                        "source": " ".join(substituted_cmd),
                        "location": rel_log_path,
                    }
                )
            if c_status == "FAIL":
                overall_status = "FAIL"
                blockers.append(
                    {
                        "code": "capability_failed",
                        "capability": cap_name,
                        "message": summary,
                    }
                )
            elif c_status == "BLOCKED" and overall_status != "FAIL":
                overall_status = "BLOCKED"
                blockers.append(
                    {
                        "code": "capability_blocked",
                        "capability": cap_name,
                        "message": summary,
                    }
                )

        actual_finished_head = _get_git_head(root)
        if (
            actual_started_head
            and actual_finished_head
            and actual_finished_head != actual_started_head
        ):
            overall_status = "FAIL"
            blockers.append(
                {
                    "code": "git_head_drift",
                    "message": f"Git HEAD changed during execution from '{actual_started_head}' to '{actual_finished_head}'",
                }
            )

        started_head = actual_started_head or head_recorded
        finished_head = actual_finished_head or head_recorded
        total_duration = round(time.time() - start_time, 3)
        return {
            "provider_id": p_id,
            "contract_version": 1,
            "profile": profile,
            "repository_sha": sha,
            "status": overall_status,
            "required": provider_item.get("required", True),
            "checks": checks,
            "coverage": {},
            "evidence": evidence,
            "started_head": started_head,
            "finished_head": finished_head,
            "duration": total_duration,
            "blockers": blockers,
            "warnings": validator_warnings,
        }

    if _coordinator is not None:
        return _run_with_coord(_coordinator)

    step_total, has_e2e = _plan_step_stats([provider_item], profile, root)
    return _execute_with_coordinator(
        repo_root=repo_root,
        profile=profile,
        epic_slug=epic_slug,
        heartbeat_interval=heartbeat_interval,
        step_total=step_total,
        has_e2e=has_e2e,
        run_id=run_id,
        fn=_run_with_coord,
    )


def verify_polyglot_execution(
    registry_data: dict[str, Any],
    requested_profile: str,
    repository_sha: str,
    provider_results: list[dict[str, Any]] | None = None,
    repo_root: Path | None = None,
    base_ref: str = "main",
    execute: bool = False,
    heartbeat_interval: float = 15.0,
    epic_slug: str | None = None,
    _fanout_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Verify multiple providers concurrently with live heartbeats and signal-safe cleanup."""
    results = list(provider_results) if provider_results is not None else []
    fanout_root = _fanout_repo_root if _fanout_repo_root is not None else repo_root

    if execute or (provider_results is None):
        val_fn = _get_validator()
        val = val_fn(registry_data, requested_profile)
        if val["status"] == "BLOCKED":
            return {
                "status": "BLOCKED",
                "findings": val["findings"],
                "aggregated": None,
            }
        plan_providers = val.get("providers", [])
        workers = max(1, len(plan_providers))
        step_total, has_e2e = _plan_step_stats(
            plan_providers, requested_profile, repo_root
        )

        def _execute_all(coordinator: _QualityRunCoordinator) -> dict[str, Any]:
            lease_file = (
                (repo_root / "build" / "quality" / ".gate4_active.lease")
                if repo_root is not None
                else None
            )
            if lease_file is not None:
                try:
                    lease_file.parent.mkdir(parents=True, exist_ok=True)
                    lease_file.write_text(
                        json.dumps(
                            {
                                "pid": os.getpid(),
                                "run_id": coordinator.run_id,
                                "profile": requested_profile,
                                "repository_sha": repository_sha,
                                "started_at": time.time(),
                            }
                        ),
                        encoding="utf-8",
                    )
                except OSError:
                    pass
            nonlocal results
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
            try:
                futures = [
                    executor.submit(
                        execute_provider,
                        provider_item=plan_item,
                        profile=requested_profile,
                        sha=repository_sha,
                        base_ref=base_ref,
                        repo_root=repo_root,
                        heartbeat_interval=heartbeat_interval,
                        epic_slug=coordinator.epic_slug,
                        run_id=coordinator.run_id,
                        _coordinator=coordinator,
                    )
                    for plan_item in plan_providers
                ]
                results = [f.result() for f in futures]
            except BaseException:
                coordinator.abort_and_reap_children()
                raise
            finally:
                executor.shutdown(wait=True)
                if lease_file is not None and lease_file.exists():
                    try:
                        lease_file.unlink()
                    except OSError:
                        pass

            return fanout_and_aggregate(
                registry_data=registry_data,
                requested_profile=requested_profile,
                repository_sha=repository_sha,
                base_ref=base_ref,
                provider_results=results,
                repo_root=fanout_root,
            )

        out_res = _execute_with_coordinator(
            repo_root=repo_root,
            profile=requested_profile,
            epic_slug=epic_slug,
            heartbeat_interval=heartbeat_interval,
            step_total=step_total,
            has_e2e=has_e2e,
            run_id=None,
            fn=_execute_all,
        )
    else:
        out_res = fanout_and_aggregate(
            registry_data=registry_data,
            requested_profile=requested_profile,
            repository_sha=repository_sha,
            base_ref=base_ref,
            provider_results=results,
            repo_root=fanout_root,
        )

    if (
        repo_root is not None
        and out_res.get("status") == "PASS"
        and requested_profile in ("epic", "release")
    ):
        try:
            receipt_file = repo_root / "build" / "quality" / "gate4_receipt.json"
            receipt_file.parent.mkdir(parents=True, exist_ok=True)
            receipt_file.write_text(
                json.dumps(
                    {
                        "status": "PASS",
                        "profile": requested_profile,
                        "repository_sha": repository_sha,
                        "base_ref": base_ref,
                        "timestamp": time.time(),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass
    return out_res


def _compact_log_tail(log_path: Path, limit: int = 25) -> list[str]:
    try:
        raw_lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    non_empty = [ln for ln in raw_lines if ln.strip()]
    return non_empty[-limit:]


def format_compact_output(res: dict[str, Any], repo_root: Path) -> str:
    """Format compact single-line GATE_PASS summaries and 25-line failure tails."""
    lines: list[str] = []
    overall = str(res.get("status", "FAIL"))
    aggregated = res.get("aggregated")
    if aggregated is None:
        lines.append(f"GATE_{overall}: registry")
        for f in res.get("findings", [])[:25]:
            msg = f.get("message", str(f)) if isinstance(f, dict) else str(f)
            lines.append(f"  {msg}")
        lines.append(f"GATE_VERDICT: {overall}")
        return "\n".join(lines)

    for p in aggregated.get("providers", []):
        p_id = str(p.get("provider_id", "provider"))
        p_status = str(p.get("status", "BLOCKED"))
        ev_map = {
            str(ev.get("id")): str(ev.get("location"))
            for ev in p.get("evidence", [])
            if isinstance(ev, dict) and ev.get("id") and ev.get("location")
        }
        checks = p.get("checks", [])
        shown_failure = False
        if checks:
            for c in checks:
                cid = str(c.get("id", "check"))
                cst = str(c.get("status", p_status))
                if cst in {"PASS", "NOT_APPLICABLE"}:
                    lines.append(f"GATE_PASS: {p_id}:{cid}")
                else:
                    shown_failure = True
                    lines.append(f"GATE_{cst}: {p_id}:{cid}")
                    log_path: Path | None = None
                    for ref in c.get("evidence_refs", []):
                        loc = ev_map.get(str(ref))
                        if loc:
                            cand = repo_root / loc
                            if cand.is_file():
                                log_path = cand
                                break
                    if log_path is None:
                        for folder in (p_id, "web"):
                            cand = (
                                repo_root / "build" / "quality" / folder / f"{cid}.log"
                            )
                            if cand.is_file():
                                log_path = cand
                                break
                    if log_path is not None:
                        lines.extend(_compact_log_tail(log_path, 25))
                    elif c.get("summary"):
                        lines.append(f"  {c['summary']}")
        else:
            if p_status == "PASS":
                lines.append(f"GATE_PASS: {p_id}")
            else:
                shown_failure = True
                lines.append(f"GATE_{p_status}: {p_id}")
        if p_status != "PASS" and not shown_failure:
            for b in p.get("blockers", [])[:25]:
                msg = b.get("message", str(b)) if isinstance(b, dict) else str(b)
                lines.append(f"  {msg}")

    for b in aggregated.get("blockers", []):
        msg = b.get("message", str(b)) if isinstance(b, dict) else str(b)
        if not any(msg in existing for existing in lines):
            lines.append(f"GATE_BLOCKER: {msg}")
    lines.append(f"GATE_VERDICT: {overall}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for polyglot quality verification and live fanout."""
    parser = argparse.ArgumentParser(
        description="Verify polyglot quality registry and multi-provider results."
    )
    parser.add_argument("registry_file", help="Path to check_quality.json")
    parser.add_argument(
        "--profile", default="epic", help="Quality profile (pr, epic, release)"
    )
    parser.add_argument(
        "--sha", default="", help="Commit SHA (defaults to git rev-parse HEAD)"
    )
    parser.add_argument("--base-ref", default="main", help="Base reference for diffs")
    parser.add_argument(
        "--results", nargs="*", default=None, help="Paths to provider result JSON files"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute declared providers and aggregate live results",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print single-line GATE_PASS summaries and 25-line failure tails while keeping full logs under build/quality/",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=float,
        default=15.0,
        help="Seconds between live stderr progress and quality_active.json heartbeat ticks (default: 15.0)",
    )
    parser.add_argument(
        "--epic",
        default=None,
        help="Optional epic slug for quality_active.json telemetry (auto-resolved when omitted)",
    )

    args = parser.parse_args(argv)
    reg_path = Path(args.registry_file).resolve()
    repo_root = _resolve_repo_root(reg_path)
    sha = args.sha
    if not sha or sha == "0" * 40:
        try:
            head_out = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if head_out.returncode == 0:
                sha = head_out.stdout.strip()
        except (subprocess.SubprocessError, OSError):
            pass
    if not sha:
        sha = "0" * 40

    data = json.loads(reg_path.read_text(encoding="utf-8"))
    git_root = repo_root if (repo_root / ".git").exists() else None

    try:
        if args.results:
            provider_results = [
                json.loads(Path(r_file).read_text(encoding="utf-8"))
                for r_file in args.results
            ]
            res = fanout_and_aggregate(
                registry_data=data,
                requested_profile=args.profile,
                repository_sha=sha,
                base_ref=args.base_ref,
                provider_results=provider_results,
                repo_root=git_root,
            )
        else:
            res = verify_polyglot_execution(
                registry_data=data,
                requested_profile=args.profile,
                repository_sha=sha,
                provider_results=None,
                repo_root=repo_root,
                base_ref=args.base_ref,
                execute=bool(args.execute or not args.results),
                heartbeat_interval=args.heartbeat_interval,
                epic_slug=args.epic,
                _fanout_repo_root=git_root,
            )
    except _SignalAbort as exc:
        sys.stderr.write(f"[quality_check] aborted by signal {exc.signum}\n")
        sys.stderr.flush()
        return 128 + exc.signum

    if args.compact:
        print(format_compact_output(res, repo_root))
    else:
        print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
