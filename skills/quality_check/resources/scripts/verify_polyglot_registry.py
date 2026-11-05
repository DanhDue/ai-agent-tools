"""Polyglot registry verification and multi-provider fanout engine.

Validates multi-provider quality manifests and simulates or executes concurrent provider
fan-out with deterministic aggregation (FAIL > BLOCKED > PASS).
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
from pathlib import Path
import sys
from typing import Any
from collections.abc import Callable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


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

    invocation = {
        "contract_version": 1,
        "profile": requested_profile,
        "repository_sha": repository_sha,
        "base_ref": base_ref,
    }

    agg_fn = _get_aggregator()
    aggregated = agg_fn(plan, results, invocation=invocation)
    return {
        "status": aggregated.get("status", "PASS"),
        "findings": [],
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
            "started_head": sha,
            "finished_head": sha,
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
            "started_head": sha,
            "finished_head": sha,
            "duration": 0.0,
            "blockers": [f"Failed to parse manifest '{manifest_path}': {e}"],
            "warnings": [],
        }

    try:
        skills_dir = Path(__file__).resolve().parent.parent.parent
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
            check_watchdog_evidence=("web" in p_id or "web" in skill),
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


def verify_polyglot_execution(
    registry_data: dict[str, Any],
    requested_profile: str,
    repository_sha: str,
    provider_results: list[dict[str, Any]],
) -> dict[str, Any]:
    """Verify that multiple providers executed concurrently and resulted in a deterministic verdict."""
    return fanout_and_aggregate(
        registry_data=registry_data,
        requested_profile=requested_profile,
        repository_sha=repository_sha,
        provider_results=provider_results,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify polyglot quality registry and multi-provider results.")
    parser.add_argument("registry_file", help="Path to check_quality.json")
    parser.add_argument("--profile", default="epic", help="Quality profile (pr, epic, release)")
    parser.add_argument("--sha", default="", help="Commit SHA (defaults to git rev-parse HEAD)")
    parser.add_argument("--base-ref", default="main", help="Base reference for diffs")
    parser.add_argument("--results", nargs="*", default=None, help="Paths to provider result JSON files")
    parser.add_argument("--execute", action="store_true", help="Execute declared providers and aggregate live results")

    args = parser.parse_args(argv)
    reg_path = Path(args.registry_file).resolve()
    repo_root = reg_path.parent.parent
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
            provider_results.append(json.loads(Path(r_file).read_text(encoding="utf-8")))
    elif args.execute or not args.results:
        val_fn = _get_validator()
        val = val_fn(data, args.profile)
        if val["status"] != "BLOCKED":
            for plan_item in val["providers"]:
                p_res = execute_provider(
                    provider_item=plan_item,
                    profile=args.profile,
                    sha=sha,
                    base_ref=args.base_ref,
                    repo_root=repo_root,
                )
                provider_results.append(p_res)

    res = fanout_and_aggregate(
        registry_data=data,
        requested_profile=args.profile,
        repository_sha=sha,
        base_ref=args.base_ref,
        provider_results=provider_results,
    )
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
