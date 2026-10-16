#!/usr/bin/env python3
"""Tests for check_bdd_traceability.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py
"""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_bdd_traceability import main

TICKS = "`" * 3
TWO = ("Scenario: [PY-HP-01] [Tier C - Integration] First",
       "Scenario Outline: [PY-EC-02] Second")


def gherkin(*scenario_lines: str) -> str:
    body = "\n".join(f"  {line}\n    Given a precondition\n" for line in scenario_lines)
    return f"# BDD Scenarios\n\n{TICKS}gherkin\nFeature: Sample\n\n{body}{TICKS}\n"


class TraceabilityCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def scenarios(self, *lines: str) -> Path:
        return self.write("epic/bdd_scenarios.en.md", gherkin(*lines))

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main([str(arg) for arg in argv])
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue()

    def plan(self, scenarios: Path, *tasks: Path) -> tuple[int, str, str]:
        return self.run_cli("plan", "--scenarios", scenarios, "--tasks", *tasks)

    def covering_task(self) -> Path:
        return self.write("epic/task_1_all.md", "Covers: PY-HP-01, PY-EC-02\n")


class DocumentValidationTest(TraceabilityCase):
    def test_scenario_without_identifier_fails(self) -> None:
        scenarios = self.scenarios("Scenario: [PY-HP-01] First", "Scenario: Second")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("scenario has no identifier", out)

    def test_tier_tag_in_identifier_position_is_malformed(self) -> None:
        scenarios = self.scenarios("Scenario: [Tier A - Unit] First")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("malformed identifier [Tier A - Unit]", out)

    def test_duplicate_identifier_fails(self) -> None:
        scenarios = self.scenarios("Scenario: [PY-HP-01] First", "Scenario: [PY-HP-01] Again")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("duplicate identifier PY-HP-01", out)

    def test_vietnamese_sibling_with_same_identifiers_passes(self) -> None:
        scenarios = self.scenarios(*TWO)
        self.write("epic/bdd_scenarios.vi.md", gherkin(
            "Kịch bản: [PY-HP-01] Thứ nhất", "Khung tình huống: [PY-EC-02] Thứ hai"))
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 0, out)

    def test_vietnamese_sibling_missing_identifier_fails(self) -> None:
        scenarios = self.scenarios(*TWO)
        self.write("epic/bdd_scenarios.vi.md", gherkin("Kịch bản: [PY-HP-01] Thứ nhất"))
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("missing identifiers PY-EC-02", out)

    def test_scenario_lines_outside_gherkin_fences_are_ignored(self) -> None:
        text = gherkin(*TWO) + "\nScenario: prose without an identifier\n" \
            + f"{TICKS}text\nScenario: also outside gherkin\n{TICKS}\n"
        scenarios = self.write("epic/bdd_scenarios.en.md", text)
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 0, out)

    def test_longer_closing_fence_closes_the_block(self) -> None:
        text = (f"# BDD Scenarios\n\n{TICKS}text\nnot gherkin\n{TICKS}`\n\n"
                f"{TICKS}gherkin\nFeature: Sample\n\n  Scenario: Missing identifier\n{TICKS}\n")
        scenarios = self.write("epic/bdd_scenarios.en.md", text)
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("scenario has no identifier", out)

    def test_lf_fr_02_non_utf8_scenario_document_exits_2(self) -> None:
        scenarios = self.root / "epic/bdd_scenarios.en.md"
        scenarios.parent.mkdir(parents=True, exist_ok=True)
        scenarios.write_bytes(b"\xff\xfe# BDD Scenarios\n")
        code, _, err = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 2)
        self.assertIn("is not valid UTF-8", err)

    def test_document_without_scenarios_fails(self) -> None:
        scenarios = self.write("epic/bdd_scenarios.en.md", "# BDD Scenarios\n")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("no scenarios found", out)

    def test_missing_scenario_document_exits_2(self) -> None:
        code, _, err = self.plan(self.root / "absent.en.md", self.covering_task())
        self.assertEqual(code, 2)
        self.assertIn("scenario document not found", err)


class PlanModeTest(TraceabilityCase):
    def test_every_identifier_in_a_task_passes(self) -> None:
        first = self.write("epic/task_1_first.md", "Covers: PY-HP-01\n")
        second = self.write("epic/task_2_second.md", "Covers: PY-EC-02\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first, second)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def test_identifier_in_no_task_fails(self) -> None:
        first = self.write("epic/task_1_first.md", "Covers: PY-HP-01\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first)
        self.assertEqual(code, 1)
        self.assertRegex(out, r"PY-EC-02\s+\(none\)")

    def test_unknown_identifier_in_covers_fails(self) -> None:
        task = self.write("epic/task_1_all.md", "Covers: PY-HP-01, PY-EC-02, PY-HP-99\n")
        code, out, _ = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 1)
        self.assertIn("Covers names unknown identifier PY-HP-99", out)

    def test_list_item_and_bold_covers_variants_are_read(self) -> None:
        first = self.write("epic/task_1_first.md", "- **Covers**: `PY-HP-01`\n")
        second = self.write("epic/task_2_second.md", "**Covers:** PY-EC-02\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first, second)
        self.assertEqual(code, 0, out)

    def test_lf_hp_01_prose_and_trailing_punctuation_in_covers_are_ignored(self) -> None:
        task = self.write("epic/task_1_all.md", "Covers: PY-HP-01 (happy path), PY-EC-02.\n")
        code, out, _ = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def test_lf_fr_01_non_utf8_task_file_exits_2(self) -> None:
        task = self.root / "epic/task_1_all.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_bytes(b"\xff\xfeCovers: PY-HP-01\n")
        code, _, err = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 2)
        self.assertIn("is not valid UTF-8", err)

    def test_missing_task_file_exits_2(self) -> None:
        code, _, err = self.plan(self.scenarios(*TWO), self.root / "epic/task_9_absent.md")
        self.assertEqual(code, 2)
        self.assertIn("task file not found", err)

    def test_vth_st_01_an_identifier_owned_by_two_tasks_fails_the_plan(self) -> None:
        scenarios = self.scenarios("Scenario: [DEMO-HP-01] First")
        first = self.write("epic/task_1_a.md", "Covers: DEMO-HP-01\n")
        second = self.write("epic/task_2_b.md", "Covers: DEMO-HP-01\n")
        code, out, _ = self.plan(scenarios, first, second)
        self.assertEqual(code, 1)
        self.assertIn("DEMO-HP-01 is on the Covers lines of task_1_a.md and task_2_b.md", out)
        self.assertIn("Result: 1/1 covered — FAIL", out)


class TestsModeTest(TraceabilityCase):
    def run_tests_mode(self, *extra: object, roots: tuple[str, ...] = ("tests/integration",)) -> tuple[int, str, str]:
        return self.run_cli("tests", "--scenarios", self.scenarios(*TWO),
                            "--roots", *(self.root / root for root in roots), *extra)

    def test_hyphenated_snake_and_lowercase_references_count(self) -> None:
        self.write("tests/integration/flow_test.dart", "testWidgets('[PY-HP-01] first', () {});\n")
        self.write("tests/integration/test_flow.py", "def test_py_ec_02_second():\n    pass\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)
        self.assertIn("flow_test.dart:1", out)
        self.assertIn("test_flow.py:1", out)

    def test_longer_digit_run_does_not_cover(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-010] other', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-01")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"PY-HP-01\s+\(none\)")

    def test_markdown_files_are_ignored(self) -> None:
        self.write("tests/integration/README.md", "PY-HP-01 and PY-EC-02 are covered elsewhere\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("Result: 0/2 covered — FAIL", out)

    def test_ids_limits_the_check_and_skips_staleness(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-HP-07] first', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-01")
        self.assertEqual(code, 0, out)
        self.assertNotIn("PY-EC-02", out)

    def test_stale_reference_fails_the_full_run(self) -> None:
        self.write("tests/integration/flow_test.ts",
                   "test('[PY-HP-01] [PY-EC-02] [PY-HP-07] all', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("stale reference PY-HP-07", out)

    def test_tokens_shaped_unlike_the_identifiers_are_never_stale(self) -> None:
        self.write("tests/integration/flow_test.ts",
                   "test('[PY-HP-01] [PY-EC-02] all', () => { expect(code).toBe('PY-1001'); });\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_snake_and_lowercase_tokens_are_never_stale(self) -> None:
        self.write("tests/integration/test_flow.py",
                   "def test_py_hp_01_retry_2():\n    pass\n\n"
                   "def test_py_ec_02_second():\n    assert 'py-3' != 'PY-HP'\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_missing_root_warns_while_others_are_scanned(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, err = self.run_tests_mode(roots=("tests/integration", "tests/e2e"))
        self.assertEqual(code, 0, out)
        self.assertIn("integration test root not found", err)

    def test_no_existing_root_exits_2(self) -> None:
        code, _, err = self.run_tests_mode(roots=("tests/e2e",))
        self.assertEqual(code, 2)
        self.assertIn("none of the integration test roots exists", err)

    def test_comma_separated_roots_and_ids_are_accepted(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, _ = self.run_cli("tests", "--scenarios", self.scenarios(*TWO),
                                    "--roots", f"{self.root / 'tests/integration'},", self.root / "tests/e2e",
                                    "--ids", "PY-HP-01,", "PY-EC-02")
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)

    def test_lf_ec_01_gitignored_files_do_not_cover(self) -> None:
        self.git("init", "-q")
        self.write(".gitignore", "playwright-report/\n")
        self.write("tests/integration/playwright-report/index.html", "<li>[PY-HP-01] [PY-EC-02]</li>\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("Result: 0/2 covered — FAIL", out)

    def test_lf_hp_02_tracked_and_untracked_unignored_files_cover(self) -> None:
        self.git("init", "-q")
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] first', () => {});\n")
        self.git("add", "tests/integration/flow_test.ts")
        self.write("tests/integration/new_test.ts", "test('[PY-EC-02] second', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_lf_ec_02_roots_outside_git_fall_back_to_the_directory_walk(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_unknown_identifier_in_ids_fails(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] first', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-99")
        self.assertEqual(code, 1)
        self.assertIn("--ids names unknown identifier PY-HP-99", out)

    def test_undecodable_file_is_skipped(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        (self.root / "tests/integration/fixture.bin").write_bytes(b"\xff\xfe\x00PY-HP-07")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)


DEMO = ("Scenario: [DEMO-HP-01] One", "Scenario: [DEMO-EC-01] Two", "Scenario: [DEMO-ST-01] Three")


def junit(*cases: str) -> str:
    return '<testsuite name="s">' + "".join(cases) + "</testsuite>"


def case(name: str, child: str = "", classname: str = "demo.Suite") -> str:
    return f'<testcase classname="{classname}" name="{name}">{child}</testcase>'


class ResultsModeTest(TraceabilityCase):
    def run_results(self, *results: object, ids: tuple[str, ...] = ()) -> tuple[int, str, str]:
        self.write("tests/placeholder.txt", "nothing\n")
        extra = ("--ids", *ids) if ids else ()
        return self.run_cli("tests", "--scenarios", self.scenarios(*DEMO), "--roots", self.root / "tests",
                            "--results", *results, *extra)

    def test_vth_hp_04_junit_directory_and_dart_reports_prove_every_identifier(self) -> None:
        single = self.write("reports/pytest.xml", junit(case("test_demo_hp_01_compliant_epic")))
        self.write("reports/gradle/TEST-a.xml", junit(case("checks_demo_ec_01", classname="a.B")))
        self.write("reports/gradle/TEST-b.xml", junit(case("unrelated")))
        dart = self.write("reports/dart.json", "\n".join([
            '{"type":"start","protocolVersion":"0.1.1"}',
            '{"type":"group","group":{"id":1,"name":"outer"}}',
            '{"type":"testStart","test":{"id":2,"name":"outer [DEMO-ST-01] plan rejects"}}',
            '{"type":"testDone","testID":2,"result":"success","skipped":false,"hidden":false}',
        ]))
        code, out, err = self.run_results(single, self.root / "reports/gradle", dart)
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("DEMO-HP-01    PASS test_demo_hp_01_compliant_epic", out)
        self.assertIn("DEMO-ST-01    PASS outer [DEMO-ST-01] plan rejects", out)
        self.assertIn("Result: 3/3 covered \u2014 PASS", out)

    def test_vth_ec_06_misleading_coverage_is_rejected_with_its_reason(self) -> None:
        self.write("tests/test_flow.py", "# DEMO-HP-01 is only mentioned in a comment\n")
        report = self.write("reports/r.xml", junit(
            case("test_demo_ec_01_skipped", "<skipped/>"),
            case("test_demo_st_01_good"), case("test_demo_st_01_bad", "<failure>x</failure>")))
        code, out, _ = self.run_results(report)
        self.assertEqual(code, 1)
        self.assertIn("DEMO-HP-01    FAIL no test case in results", out)
        self.assertIn("DEMO-EC-01    FAIL skipped", out)
        self.assertIn("DEMO-ST-01    FAIL failed in test_demo_st_01_bad", out)
        self.assertIn("Result: 0/3 covered \u2014 FAIL", out)

    def test_vth_fr_02_report_in_neither_format_exits_2_naming_the_file(self) -> None:
        report = self.write("reports/bad.txt", "plain text\n")
        code, out, err = self.run_results(report)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("error:", err)
        self.assertIn("bad.txt", err)

    def test_missing_results_path_exits_2(self) -> None:
        code, _, err = self.run_results(self.root / "nowhere.xml")
        self.assertEqual(code, 2)
        self.assertIn("nowhere.xml", err)

    def test_stale_reference_in_a_root_file_fails_a_full_run(self) -> None:
        self.write("tests/test_flow.py", "# DEMO-HP-09 was removed\n")
        report = self.write("reports/r.xml", junit(
            case("demo_hp_01"), case("demo_ec_01"), case("demo_st_01")))
        code, out, _ = self.run_results(report)
        self.assertEqual(code, 1)
        self.assertIn("stale reference DEMO-HP-09", out)

    def test_ids_limits_the_selection(self) -> None:
        report = self.write("reports/r.xml", junit(case("demo_hp_01")))
        code, out, _ = self.run_results(report, ids=("DEMO-HP-01",))
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 1/1 covered \u2014 PASS", out)


if __name__ == "__main__":
    unittest.main()
