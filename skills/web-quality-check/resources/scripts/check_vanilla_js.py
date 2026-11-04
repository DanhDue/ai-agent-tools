"""Execution wrapper for type checking static Vanilla JavaScript codebases using jsconfig.json and JSDoc."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "jsconfig.template.json"


def find_jsconfig(start_dir: Path | str = ".") -> Path | None:
    """Search for jsconfig.json starting from start_dir and traversing parent directories."""
    current = Path(start_dir).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "jsconfig.json"
        if candidate.is_file():
            return candidate
    return None


def validate_jsconfig_content(config_data: dict[str, Any]) -> list[str]:
    """Validate that jsconfig.json contains mandatory compilerOptions for Vanilla JS typechecking."""
    errors: list[str] = []
    compiler_options = config_data.get("compilerOptions")
    if not isinstance(compiler_options, dict):
        errors.append("Missing or invalid 'compilerOptions' object in jsconfig.json")
        return errors

    if compiler_options.get("checkJs") is not True:
        errors.append("compilerOptions.checkJs must be set to true for Vanilla JavaScript type checking")

    return errors


def scaffold_jsconfig(
    target_dir: Path | str,
    template_path: Path | str | None = None,
    overwrite: bool = False,
) -> Path:
    """Scaffold a canonical jsconfig.json into target_dir."""
    dest_dir = Path(target_dir).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_file = dest_dir / "jsconfig.json"

    if target_file.exists() and not overwrite:
        raise FileExistsError(f"jsconfig.json already exists at {target_file}")

    tpl = Path(template_path).resolve() if template_path else TEMPLATE_PATH
    if not tpl.is_file():
        raise FileNotFoundError(f"Template jsconfig not found at {tpl}")

    shutil.copyfile(tpl, target_file)
    return target_file


def parse_tsc_diagnostics(output: str) -> list[dict[str, Any]]:
    """Parse TypeScript compiler diagnostic output lines into structured findings."""
    diagnostics: list[dict[str, Any]] = []
    # Pattern: path/file.js(line,col): error TSXXXX: message
    pattern = re.compile(r"^(.*?)\((\d+),(\d+)\):\s+(error|warning)\s+(TS\d+):\s+(.*)$")

    for line in output.splitlines():
        match = pattern.match(line.strip())
        if match:
            diagnostics.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "column": int(match.group(3)),
                    "severity": match.group(4),
                    "code": match.group(5),
                    "message": match.group(6),
                }
            )
    return diagnostics


def run_vanilla_js_typecheck(
    project_dir: Path | str = ".",
    jsconfig_path: Path | str | None = None,
    command_override: list[str] | None = None,
) -> dict[str, Any]:
    """Execute TypeScript compiler against jsconfig.json in project_dir."""
    pdir = Path(project_dir).resolve()
    config_file: Path | None = None

    if jsconfig_path is not None:
        explicit = Path(jsconfig_path)
        config_file = explicit if explicit.is_absolute() else (pdir / explicit).resolve()
    else:
        config_file = find_jsconfig(pdir)

    if config_file is None or not config_file.is_file():
        return {
            "status": "FAIL",
            "exit_code": 2,
            "jsconfig": None,
            "stdout": "",
            "stderr": "No jsconfig.json found in project tree",
            "diagnostics": [],
            "error": "missing_jsconfig",
        }

    try:
        raw_config = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "status": "FAIL",
            "exit_code": 2,
            "jsconfig": str(config_file),
            "stdout": "",
            "stderr": f"Failed to parse jsconfig.json: {exc}",
            "diagnostics": [],
            "error": "invalid_json",
        }

    validation_errors = validate_jsconfig_content(raw_config)
    if validation_errors:
        return {
            "status": "FAIL",
            "exit_code": 2,
            "jsconfig": str(config_file),
            "stdout": "",
            "stderr": "\n".join(validation_errors),
            "diagnostics": [],
            "error": "invalid_jsconfig_options",
        }

    # Resolve executable command
    if command_override:
        cmd = list(command_override)
    elif shutil.which("tsc"):
        cmd = ["tsc", "--project", str(config_file)]
    elif shutil.which("npx"):
        cmd = ["npx", "--yes", "typescript", "tsc", "--project", str(config_file)]
    else:
        return {
            "status": "FAIL",
            "exit_code": 2,
            "jsconfig": str(config_file),
            "stdout": "",
            "stderr": "Neither 'tsc' nor 'npx' executable found in PATH",
            "diagnostics": [],
            "error": "missing_compiler",
        }

    try:
        result = subprocess.run(
            cmd,
            cwd=pdir,
            capture_output=True,
            text=True,
            check=False,
        )
    except (subprocess.SubprocessError, OSError) as exc:
        return {
            "status": "FAIL",
            "exit_code": 2,
            "jsconfig": str(config_file),
            "stdout": "",
            "stderr": f"Failed to execute compiler command {cmd}: {exc}",
            "diagnostics": [],
            "error": "execution_failed",
        }

    combined_output = f"{result.stdout}\n{result.stderr}"
    diagnostics = parse_tsc_diagnostics(combined_output)

    return {
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "exit_code": result.returncode,
        "jsconfig": str(config_file),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "diagnostics": diagnostics,
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for check_vanilla_js."""
    parser = argparse.ArgumentParser(
        description="Vanilla JavaScript type-checking wrapper using jsconfig.json and JSDoc."
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="Path to jsconfig.json file or directory containing it.",
    )
    parser.add_argument(
        "--target-dir",
        type=str,
        default=".",
        help="Project target directory (default: current directory).",
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Scaffold canonical jsconfig.template.json into target directory if missing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON summary output.",
    )

    args = parser.parse_args(argv)

    if args.scaffold:
        target = Path(args.target_dir).resolve()
        jsconfig_dest = target / "jsconfig.json"
        if not jsconfig_dest.exists():
            scaffold_jsconfig(target)
            print(f"Scaffolded jsconfig.json at {jsconfig_dest}")

    res = run_vanilla_js_typecheck(
        project_dir=args.target_dir,
        jsconfig_path=args.project,
    )

    if args.json:
        print(json.dumps(res, indent=2))
    else:
        if res["status"] == "PASS":
            print(f"Vanilla JS typecheck PASSED (jsconfig: {res.get('jsconfig')})")
        else:
            print(f"Vanilla JS typecheck FAILED (exit {res.get('exit_code')}):", file=sys.stderr)
            if res.get("stderr"):
                print(res["stderr"], file=sys.stderr)
            if res.get("stdout"):
                print(res["stdout"], file=sys.stderr)

    return int(res["exit_code"])


if __name__ == "__main__":
    sys.exit(main())
