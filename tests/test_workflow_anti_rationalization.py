"""Tests for Anti-Rationalization Tables and Doubt-Driven Verification Workflow (Task 05)."""

from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"

if str(DEV_IMPL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(DEV_IMPL_SCRIPTS))

from result_reports import Case, load_reports, verdicts  # type: ignore[import-not-found]


def test_anti_rationalization_content():
    """GREEN phase: verify anti-rationalization tables and doubt protocol across skills."""
    skills_to_check = [
        REPO_ROOT / "skills" / "dev-designer" / "SKILL.md",
        REPO_ROOT / "skills" / "dev-implementation" / "SKILL.md",
        REPO_ROOT / "skills" / "test-driven-development" / "SKILL.md",
    ]

    for skill_path in skills_to_check:
        assert skill_path.is_file(), f"Skill file not found at {skill_path}"
        content = skill_path.read_text(encoding="utf-8")

        # 1. 5th Anti-Rationalization rule regarding Visual Companion and computed CSS
        assert "Visual Companion" in content, (
            f"Missing Visual Companion rule in {skill_path.name}"
        )
        assert "getComputedStyle" in content, (
            f"Missing getComputedStyle rule in {skill_path.name}"
        )
        assert "getBoundingClientRect" in content, (
            f"Missing getBoundingClientRect rule in {skill_path.name}"
        )

        # 2. Subcutaneous testing & Headless Playwright
        assert "Subcutaneous" in content, (
            f"Missing Subcutaneous testing requirement in {skill_path.name}"
        )
        assert "Playwright" in content, (
            f"Missing Playwright requirement in {skill_path.name}"
        )

        # 3. Doubt-driven verification protocol
        assert "Doubt-Driven" in content or "Doubt" in content, (
            f"Missing Doubt protocol in {skill_path.name}"
        )


def test_WQG_ST_02_task_status_progression_under_anti_rationalization_audit(tmp_path: Path):
    """Scenario: [WQG-ST-02] Task status progression under Anti-Rationalization audit."""
    # 1. When only pure unit test mock report file on disk is loaded for Tier C scenario [WQG-HP-01]
    unit_report_file = tmp_path / "unit_results.xml"
    unit_report_file.write_text(
        """<testsuites>
  <testsuite name="unit_tests" tests="1">
    <testcase classname="tests.unit.test_web.UnitTest" name="test_WQG_HP_01_feature"/>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )
    unit_cases = load_reports([str(unit_report_file)], tmp_path)
    res_unit = verdicts(["WQG-HP-01"], unit_cases)

    # Must reject with condition 6 failure naming integration runner provenance
    passed_unit, detail_unit = res_unit["WQG-HP-01"]
    assert not passed_unit, "Expected pure unit mock to be rejected for Tier C scenario"
    assert "lacks integration runner provenance" in detail_unit

    # 2. When real Playwright headless integration report file on disk is loaded
    int_report_file = tmp_path / "playwright_results.xml"
    int_report_file.write_text(
        """<testsuites>
  <testsuite name="playwright" tests="1">
    <testcase classname="tests.test_playwright_e2e" name="test_WQG_HP_01_feature"/>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )
    int_cases = load_reports([str(int_report_file)], tmp_path)
    res_int = verdicts(["WQG-HP-01"], int_cases)

    passed_int, detail_int = res_int["WQG-HP-01"]
    assert passed_int, (
        f"Expected integration test runner evidence to pass: {detail_int}"
    )
    assert detail_int == "test_WQG_HP_01_feature"

    # 3. Empty classname report lacks integration runner provenance for Tier C
    empty_report_file = tmp_path / "empty_results.xml"
    empty_report_file.write_text(
        """<testsuites>
  <testsuite name="unattributed" tests="1">
    <testcase classname="" name="test_WQG_HP_01_feature"/>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )
    empty_cases = load_reports([str(empty_report_file)], tmp_path)
    res_empty = verdicts(["WQG-HP-01"], empty_cases)
    passed_empty, detail_empty = res_empty["WQG-HP-01"]
    assert not passed_empty, (
        "Expected empty classname to be rejected for Tier C scenario"
    )
    assert "lacks integration runner provenance" in detail_empty

    # 4. Tier A scenario (WQG-HP-04) accepts unit test classname from report without rejection
    smoke_report_file = tmp_path / "smoke_results.xml"
    smoke_report_file.write_text(
        """<testsuites>
  <testsuite name="smoke" tests="1">
    <testcase classname="tests.unit.test_smoke.UnitTest" name="test_WQG_HP_04_checklist"/>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )
    smoke_cases = load_reports([str(smoke_report_file)], tmp_path)
    res_hp04 = verdicts(["WQG-HP-04"], smoke_cases)
    passed_hp04, detail_hp04 = res_hp04["WQG-HP-04"]
    assert passed_hp04, (
        f"Expected Tier A scenario to accept unit test evidence: {detail_hp04}"
    )
