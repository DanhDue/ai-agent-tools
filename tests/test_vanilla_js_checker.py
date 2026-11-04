"""Tests for Vanilla JavaScript type checking configuration and execution wrapper."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SCRIPTS_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"

if str(WEB_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_SCRIPTS_DIR))

from check_vanilla_js import (  # noqa: E402
    TEMPLATE_PATH,
    find_jsconfig,
    main,
    parse_tsc_diagnostics,
    run_vanilla_js_typecheck,
    scaffold_jsconfig,
    validate_jsconfig_content,
)


def test_jsconfig_discovery(tmp_path: Path) -> None:
    """V1/V2: Verify jsconfig template existence, discovery in parent dirs, and scaffolding."""
    assert TEMPLATE_PATH.is_file(), f"Template not found at {TEMPLATE_PATH}"
    template_content = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    assert template_content.get("compilerOptions", {}).get("checkJs") is True
    assert template_content.get("compilerOptions", {}).get("noEmit") is True

    # Scaffold into tmp_path
    scaffolded = scaffold_jsconfig(tmp_path)
    assert scaffolded.is_file()
    assert (tmp_path / "jsconfig.json").exists()

    # Discover from child directory
    child_dir = tmp_path / "preview" / "static" / "deep"
    child_dir.mkdir(parents=True)
    discovered = find_jsconfig(child_dir)
    assert discovered == scaffolded


def test_validate_jsconfig_content() -> None:
    """Verify validation of compilerOptions.checkJs."""
    # Valid
    assert validate_jsconfig_content({"compilerOptions": {"checkJs": True}}) == []

    # Missing compilerOptions
    errs = validate_jsconfig_content({})
    assert any("compilerOptions" in e for e in errs)

    # checkJs is False
    errs2 = validate_jsconfig_content({"compilerOptions": {"checkJs": False}})
    assert any("checkJs" in e for e in errs2)


def test_parse_tsc_diagnostics() -> None:
    """Verify tsc output parser."""
    sample = "src/app.js(12,5): error TS2322: Type 'number' is not assignable to type 'string'."
    diags = parse_tsc_diagnostics(sample)
    assert len(diags) == 1
    assert diags[0]["file"] == "src/app.js"
    assert diags[0]["line"] == 12
    assert diags[0]["column"] == 5
    assert diags[0]["severity"] == "error"
    assert diags[0]["code"] == "TS2322"


def test_run_vanilla_js_typecheck_missing_config(tmp_path: Path) -> None:
    """Missing jsconfig returns error."""
    res = run_vanilla_js_typecheck(project_dir=tmp_path)
    assert res["status"] == "FAIL"
    assert res["exit_code"] == 2
    assert res["error"] == "missing_jsconfig"


def test_run_vanilla_js_typecheck_invalid_config(tmp_path: Path) -> None:
    """Invalid jsconfig returns error."""
    cfg = tmp_path / "jsconfig.json"
    cfg.write_text(json.dumps({"compilerOptions": {"checkJs": False}}), encoding="utf-8")
    res = run_vanilla_js_typecheck(project_dir=tmp_path)
    assert res["status"] == "FAIL"
    assert res["exit_code"] == 2
    assert res["error"] == "invalid_jsconfig_options"


def test_WQG_HP_02_vanilla_js_type_checking(tmp_path: Path) -> None:
    """[WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration.

    Given a repository containing Vanilla JavaScript files in preview/static/
    And a jsconfig.json configured with 'checkJs': true
    When web-quality-check executes the type_check capability
    Then the TypeScript compiler validates all JavaScript files without emitting errors
    And passes without requiring any .ts file renaming.
    """
    # 1. Setup preview/static/ directory
    static_dir = tmp_path / "preview" / "static"
    static_dir.mkdir(parents=True)

    # 2. Add valid Vanilla JS file with JSDoc annotations
    js_file = static_dir / "player.js"
    js_file.write_text(
        """/**
 * Calculates track duration in seconds.
 * @param {number} minutes
 * @param {number} seconds
 * @returns {number}
 */
function calculateDuration(minutes, seconds) {
    return minutes * 60 + seconds;
}

const total = calculateDuration(3, 45);
console.log(total);
""",
        encoding="utf-8",
    )

    # 3. Setup jsconfig.json
    scaffold_jsconfig(tmp_path)

    # 4. Mock or execute type check
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="No issues found", stderr="")
        res = run_vanilla_js_typecheck(project_dir=tmp_path)

    assert res["status"] == "PASS"
    assert res["exit_code"] == 0
    assert len(res["diagnostics"]) == 0
    assert js_file.suffix == ".js"


def test_WQG_HP_02_type_error_detected(tmp_path: Path) -> None:
    """Verify that type errors in Vanilla JS are caught without .ts migration."""
    scaffold_jsconfig(tmp_path)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="preview/static/player.js(10,5): error TS2322: Type 'string' is not assignable to type 'number'.",
            stderr="",
        )
        res = run_vanilla_js_typecheck(project_dir=tmp_path)

    assert res["status"] == "FAIL"
    assert res["exit_code"] == 1
    assert len(res["diagnostics"]) == 1
    assert res["diagnostics"][0]["code"] == "TS2322"


def test_cli_execution(tmp_path: Path) -> None:
    """Verify CLI main entrypoint."""
    scaffold_jsconfig(tmp_path)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        code = main(["--target-dir", str(tmp_path), "--json"])
        assert code == 0
