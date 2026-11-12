#!/usr/bin/env python3
"""Standalone runner for check-tasks HTTP daemon server.

Delegates execution to skills/check-tasks/resources/scripts/tasks_server.py
via dynamic importlib spec loading.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


def _delegate_main() -> int:
    target_path = (
        Path(__file__).resolve().parent.parent
        / "skills"
        / "check-tasks"
        / "resources"
        / "scripts"
        / "tasks_server.py"
    )
    if not target_path.is_file():
        sys.stderr.write(
            f"Error: Target tasks_server script not found at {target_path}\n"
        )
        return 1

    spec = importlib.util.spec_from_file_location(
        "_check_tasks_server_engine", target_path
    )
    if spec is None or spec.loader is None:
        sys.stderr.write("Error: Could not load spec for tasks_server module\n")
        return 1

    module = importlib.util.module_from_spec(spec)
    sys.modules["_check_tasks_server_engine"] = module
    spec.loader.exec_module(module)
    return int(module.main(sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(_delegate_main())
