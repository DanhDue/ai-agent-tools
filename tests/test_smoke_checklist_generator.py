"""Tests for automated manual smoke checklist generator."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_IMPL_SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"

if str(DEV_IMPL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(DEV_IMPL_SCRIPTS_DIR))

from generate_smoke_checklist import (  # noqa: E402
    extract_smoke_steps,
    extract_target_from_text,
    generate_smoke_checklist,
    main,
    parse_bdd_scenarios,
    render_smoke_checklist_markdown,
)

SAMPLE_BDD_CONTENT = """# BDD Scenarios

### Scenario: [DEMO-HP-01] [Tier C - Integration] Studio user starts recording session
Given the user navigates to `http://localhost:3000/studio`
When the user clicks the start recording button
Then the waveform visualization activates within 200ms
And status shows `Recording`.

### Scenario: [DEMO-HP-02] [Tier C - Integration] CLI quality validation execution
Given a clean working tree
When the engineer runs `d3nexus:quality_check` with profile `epic`
Then the quality orchestrator executes all registered providers
And emits an executive report with verdict `PASS`.

### Scenario: [DEMO-HP-03] [Tier B - Component] Settings drawer toggle
Given the settings icon is visible
When the user taps the gear icon
Then the settings drawer slides open from the right.

### Scenario: [DEMO-HP-04] [Tier A - Unit] Offline sync queue processing
Given 3 pending offline actions in queue
When connectivity is restored
Then all 3 actions synchronize sequentially.

### Scenario: [DEMO-EC-01] [Tier B - Edge] Network timeout handling
Given a flaky connection
When requests time out after 5000ms
Then an error toast displays retry action.
"""


def test_smoke_checklist_generation(tmp_path: Path) -> None:
    """V1/V2: Verify parsing and generation of manual smoke checklist."""
    scenarios = parse_bdd_scenarios(SAMPLE_BDD_CONTENT)
    assert len(scenarios) == 5

    happy_paths = [s for s in scenarios if "-HP-" in s["id"]]
    assert len(happy_paths) == 4

    steps = extract_smoke_steps(scenarios)
    assert 3 <= len(steps) <= 5

    # Check extracted targets
    assert "http://localhost:3000/studio" in steps[0]["target"]
    assert "`d3nexus:quality_check`" in steps[1]["target"]

    # Render markdown
    md = render_smoke_checklist_markdown("demo_epic", steps)
    assert "# Manual Smoke Walkthrough Checklist: Demo Epic" in md
    assert "| Step | Target (URL / CLI) | Action | Observable Outcome |" in md
    assert "http://localhost:3000/studio" in md


def test_extract_target_from_text() -> None:
    """Verify URL and command extraction logic."""
    url_text = "Navigate to https://example.com/login and submit"
    assert extract_target_from_text(url_text) == "https://example.com/login"

    cmd_text = "Run `npm run test` in terminal"
    assert extract_target_from_text(cmd_text) == "`npm run test`"

    bare_cli = "When python3 scripts/verify.sh runs"
    assert extract_target_from_text(bare_cli) == "`python3 scripts/verify.sh`"

    bare_skill = "When Gate 4 invokes d3nexus:web-quality-check with profile epic"
    assert extract_target_from_text(bare_skill) == "`d3nexus:web-quality-check`"

    fallback_text = "Click the primary button"
    assert extract_target_from_text(fallback_text) == "CLI / Workspace Root"


def test_step_count_clamping() -> None:
    """Verify that steps are always clamped between 3 and 5."""
    single_scenario = [
        {
            "id": "SOLO-HP-01",
            "title": "Solo action",
            "given": ["start"],
            "when": ["action"],
            "then": ["success"],
            "and": [],
        }
    ]
    clamped_up = extract_smoke_steps(single_scenario, min_steps=3, max_steps=5)
    assert len(clamped_up) == 3

    many_scenarios = [
        {
            "id": f"TEST-HP-0{i}",
            "title": f"Action {i}",
            "given": [f"given {i}"],
            "when": [f"when {i}"],
            "then": [f"then {i}"],
            "and": [],
        }
        for i in range(1, 10)
    ]
    clamped_down = extract_smoke_steps(many_scenarios, min_steps=3, max_steps=5)
    assert len(clamped_down) == 5


def test_WQG_HP_04_automated_manual_smoke_checklist(tmp_path: Path) -> None:
    """[WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist.

    Given all tasks in an epic reach status `done` and Phase 4 executes
    When the smoke generator parses primary BDD Happy Path scenarios
    Then it emits .devtool/epic/<epic_dir>/manual_smoke_checklist.md before Gate 4 validation
    And the checklist contains between 3 and 5 actionable verification steps with Target
    (URL or CLI Command), Action, and Observable Outcome.
    """
    epic_dir = tmp_path / ".devtool" / "epic" / "web_quality_check_and_integration_gate"
    epic_dir.mkdir(parents=True)
    bdd_file = epic_dir / "bdd_scenarios.en.md"
    bdd_file.write_text(SAMPLE_BDD_CONTENT, encoding="utf-8")

    out_file = generate_smoke_checklist(
        epic_dir="web_quality_check_and_integration_gate",
        workspace_root=tmp_path,
    )

    assert out_file.is_file()
    assert out_file == epic_dir / "manual_smoke_checklist.md"

    content = out_file.read_text(encoding="utf-8")
    assert "| Step | Target (URL / CLI) | Action | Observable Outcome |" in content

    # Count table rows
    table_rows = [line for line in content.splitlines() if line.startswith("| ") and not line.startswith("| Step") and not line.startswith("| :---")]
    assert 3 <= len(table_rows) <= 5


def test_main_cli_execution(tmp_path: Path) -> None:
    """Verify CLI entrypoint."""
    epic_dir = tmp_path / ".devtool" / "epic" / "sample_epic"
    epic_dir.mkdir(parents=True)
    (epic_dir / "bdd_scenarios.en.md").write_text(SAMPLE_BDD_CONTENT, encoding="utf-8")

    code = main([
        "--epic-dir", "sample_epic",
        "--workspace-root", str(tmp_path),
    ])
    assert code == 0
    assert (epic_dir / "manual_smoke_checklist.md").is_file()
