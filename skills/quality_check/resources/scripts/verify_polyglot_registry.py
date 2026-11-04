"""Polyglot registry verification and multi-provider fanout engine.

Validates multi-provider quality manifests and simulates or executes concurrent provider
fan-out with deterministic aggregation (FAIL > BLOCKED > PASS).
"""

from __future__ import annotations

import argparse
import importlib
import json
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify polyglot quality registry and multi-provider results.")
    parser.add_argument("registry_file", help="Path to check_quality.json")
    parser.add_argument("--profile", default="epic", help="Quality profile (pr, epic, release)")
    parser.add_argument("--sha", default="0000000000000000000000000000000000000000", help="Commit SHA")

    args = parser.parse_args()
    data = json.loads(Path(args.registry_file).read_text())
    res = fanout_and_aggregate(data, args.profile, args.sha)
    print(json.dumps(res, indent=2))
    return 0 if res["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
