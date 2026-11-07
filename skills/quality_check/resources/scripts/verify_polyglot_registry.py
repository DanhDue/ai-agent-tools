"""Polyglot registry verification and multi-provider fanout engine.

Validates multi-provider quality manifests and simulates or executes concurrent provider
fan-out with deterministic aggregation (FAIL > BLOCKED > PASS).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import os
import subprocess
import time
from pathlib import Path
import sys
from typing import Any
from collections.abc import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


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


def execute_provider(
    provider_item: dict[str, Any],
    profile: str,
    sha: str,
    base_ref: str = "main",
    repo_root: Path | None = None,
) -> dict[str, Any]:
    root = repo_root or Path.cwd()
    p_id = provider_item.get("id", "")
    skill = provider_item.get("skill", "")

    actual_started_head = _get_git_head(root)
    head_recorded = actual_started_head or sha

    candidates = [
        root / ".agents" / "quality" / f"{p_id}.json",
    ]
    platform = p_id.split("-")[0]
    if platform:
        candidates.append(root / ".agents" / "quality" / f"{platform}-quality.json")
    for part in skill.split(":")[-1].split("-"):
        if part and part not in ("quality", "check"):
            candidates.append(root / ".agents" / "quality" / f"{part}-quality.json")

    manifest_path = next((c for c in candidates if c and c.is_file()), None)
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

    # Web provider execution: dispatch to web-quality runner
    if "web" in p_id or "web" in skill:
        try:
            web_scripts = skills_dir / "web-quality-check" / "resources" / "scripts"
            if str(web_scripts) not in sys.path:
                sys.path.insert(0, str(web_scripts))
            from validate_web_quality import run_capabilities

            return run_capabilities(
                config=manifest_data,
                profile=profile,
                repository_sha=sha,
                repo_root=root,
                provider_id=p_id,
                base_ref=base_ref,
                skills_dir=skills_dir,
                check_watchdog_evidence=True,
            )
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

    # Non-web provider execution: validate using platform validator if available
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
                        "warnings": [],
                    }
        except Exception:
            pass

    # Execute configured profile capabilities for non-web provider
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
            "warnings": [],
        }

    capabilities = manifest_data.get("capabilities", {})
    checks: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    overall_status = "PASS"
    log_dir = root / "build" / "quality" / p_id
    log_dir.mkdir(parents=True, exist_ok=True)

    if actual_started_head and sha and sha != actual_started_head:
        overall_status = "FAIL"
        blockers.append(
            {
                "code": "repository_sha_mismatch",
                "message": f"Requested repository SHA '{sha}' does not match actual Git HEAD '{actual_started_head}'",
            }
        )

    for cap_name in caps_to_run:
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
            arg.replace("{base_ref}", base_ref).replace("{skills_dir}", str(skills_dir))
            for arg in cmd
        ]
        cap_start = time.time()
        try:
            proc = subprocess.run(
                substituted_cmd,
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
            )
            cap_duration = round(time.time() - cap_start, 3)
            log_file = log_dir / f"{cap_name}.log"
            log_file.write_text(
                f"$ {' '.join(substituted_cmd)}\n\n--- STDOUT ---\n{proc.stdout}\n--- STDERR ---\n{proc.stderr}\n",
                encoding="utf-8",
            )
            c_status = "PASS" if proc.returncode == 0 else "FAIL"
            summary = (
                f"{cap_name}: passed"
                if c_status == "PASS"
                else f"{cap_name}: failed with return code {proc.returncode}"
            )
        except OSError as exc:
            cap_duration = round(time.time() - cap_start, 3)
            c_status = "BLOCKED"
            summary = f"{cap_name}: failed to execute: {exc}"

        evidence_id = f"{cap_name}-evidence"
        log_file = log_dir / f"{cap_name}.log"
        rel_log_path = str(log_file.relative_to(root)) if log_file.is_file() else ""
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
        "warnings": [],
    }


def verify_polyglot_execution(
    registry_data: dict[str, Any],
    requested_profile: str,
    repository_sha: str,
    provider_results: list[dict[str, Any]] | None = None,
    repo_root: Path | None = None,
    base_ref: str = "main",
    execute: bool = False,
) -> dict[str, Any]:
    """Verify that multiple providers executed concurrently and resulted in a deterministic verdict."""
    results = list(provider_results) if provider_results is not None else []
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
                            "profile": requested_profile,
                            "repository_sha": repository_sha,
                            "started_at": time.time(),
                        }
                    ),
                    encoding="utf-8",
                )
            except OSError:
                pass
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        execute_provider,
                        provider_item=plan_item,
                        profile=requested_profile,
                        sha=repository_sha,
                        base_ref=base_ref,
                        repo_root=repo_root,
                    )
                    for plan_item in plan_providers
                ]
                results = [f.result() for f in futures]
        finally:
            if lease_file is not None and lease_file.exists():
                try:
                    lease_file.unlink()
                except OSError:
                    pass

    out_res = fanout_and_aggregate(
        registry_data=registry_data,
        requested_profile=requested_profile,
        repository_sha=repository_sha,
        base_ref=base_ref,
        provider_results=results,
        repo_root=repo_root,
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


def main(argv: list[str] | None = None) -> int:
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
    provider_results: list[dict[str, Any]] = []

    if args.results:
        for r_file in args.results:
            provider_results.append(
                json.loads(Path(r_file).read_text(encoding="utf-8"))
            )
    elif args.execute or not args.results:
        val_fn = _get_validator()
        val = val_fn(data, args.profile)
        if val["status"] != "BLOCKED":
            workers = max(1, len(val["providers"]))
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [
                    executor.submit(
                        execute_provider,
                        provider_item=plan_item,
                        profile=args.profile,
                        sha=sha,
                        base_ref=args.base_ref,
                        repo_root=repo_root,
                    )
                    for plan_item in val["providers"]
                ]
                provider_results = [f.result() for f in futures]

    git_root = repo_root if (repo_root / ".git").exists() else None
    res = fanout_and_aggregate(
        registry_data=data,
        requested_profile=args.profile,
        repository_sha=sha,
        base_ref=args.base_ref,
        provider_results=provider_results,
        repo_root=git_root,
    )
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
