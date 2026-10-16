#!/usr/bin/env python3
"""Tests for result_reports.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from result_reports import (Case, ReportError, digest, load_reports, parse_dart, parse_junit,
                            reference_pattern, verdicts)

JUNIT = """<testsuites><testsuite name="a">
<testcase classname="x.Y" name="passes"/>
<testcase classname="x.Y" name="fails"><failure message="m"/></testcase>
<testcase classname="x.Y" name="errors"><error message="m"/></testcase>
<testcase classname="x.Y" name="skips"><skipped/></testcase>
<testsuite name="nested"><testcase classname="z" name="deep"/></testsuite>
</testsuite></testsuites>"""

DART = "\n".join([
    '{"type":"start"}',
    '{"type":"testStart","test":{"id":1,"name":"loading /tmp/x.dart"}}',
    '{"type":"testDone","testID":1,"result":"success","skipped":false,"hidden":true}',
    '{"type":"testStart","test":{"id":2,"name":"g ok"}}',
    '{"type":"testDone","testID":2,"result":"success","skipped":false,"hidden":false}',
    '{"type":"testStart","test":{"id":3,"name":"g bad"}}',
    '{"type":"testDone","testID":3,"result":"failure","skipped":false,"hidden":false}',
    '{"type":"testStart","test":{"id":4,"name":"g skip"}}',
    '{"type":"testDone","testID":4,"result":"success","skipped":true,"hidden":false}',
    '{"type":"done","success":false}',
])


def case(name: str, status: str = "passed", classname: str = "") -> Case:
    return Case(name, classname, status)


class ParserTest(unittest.TestCase):
    def test_junit_statuses_at_any_depth(self) -> None:
        got = {c.name: c.status for c in parse_junit(JUNIT)}
        self.assertEqual(got, {"passes": "passed", "fails": "failed", "errors": "failed",
                               "skips": "skipped", "deep": "passed"})
        self.assertEqual(parse_junit(JUNIT)[0].classname, "x.Y")

    def test_dart_statuses_and_hidden_tests(self) -> None:
        got = {c.name: (c.status, c.classname) for c in parse_dart(DART)}
        self.assertEqual(got, {"g ok": ("passed", ""), "g bad": ("failed", ""), "g skip": ("skipped", "")})

    def test_reference_pattern_matches_case_and_separators(self) -> None:
        pattern = reference_pattern("DEMO-HP-01")
        self.assertTrue(pattern.search("test_demo_hp_01_x"))
        self.assertFalse(pattern.search("demo_hp_011"))


class LoadTest(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def test_file_directory_and_glob(self) -> None:
        self.write("one.xml", '<testsuite><testcase name="a"/></testsuite>')
        self.write("dir/sub/two.xml", '<testsuite><testcase name="b"/></testsuite>')
        self.write("dir/three.json", '{"type":"testStart","test":{"id":1,"name":"c"}}\n'
                   '{"type":"testDone","testID":1,"result":"success","skipped":false,"hidden":false}')
        self.write("dir/ignored.txt", "not a report")
        self.write("g/x1.xml", '<testsuite><testcase name="d"/></testsuite>')
        names = lambda paths: sorted(c.name for c in load_reports(paths, self.root))
        self.assertEqual(names(["one.xml"]), ["a"])
        self.assertEqual(names(["dir"]), ["b", "c"])
        self.assertEqual(names(["g/x*.xml"]), ["d"])

    def test_missing_path_and_unknown_format_raise_naming_the_path(self) -> None:
        self.write("bad.xml", "  plain text")
        with self.assertRaisesRegex(ReportError, "nowhere"):
            load_reports(["nowhere.xml"], self.root)
        with self.assertRaisesRegex(ReportError, "bad.xml"):
            load_reports(["bad.xml"], self.root)


class VerdictTest(unittest.TestCase):
    def test_every_branch(self) -> None:
        cases = [case("demo_hp_01"), case("demo_hp_01_b", "failed"),
                 case("demo_ec_01", "skipped"), case("demo_st_01"), case("demo_st_01_b", "skipped"),
                 case("t", classname="DEMO-FR-01")]
        got = verdicts(["DEMO-HP-01", "DEMO-EC-01", "DEMO-ST-01", "DEMO-FR-01", "DEMO-LF-01"], cases)
        self.assertEqual(got["DEMO-HP-01"], (False, "failed in demo_hp_01_b"))
        self.assertEqual(got["DEMO-EC-01"], (False, "skipped"))
        self.assertEqual(got["DEMO-ST-01"], (True, "demo_st_01"))
        self.assertEqual(got["DEMO-FR-01"], (True, "t"))
        self.assertEqual(got["DEMO-LF-01"], (False, "no test case in results"))

    def test_digest_lists_only_cases_of_the_identifiers(self) -> None:
        cases = [case("demo_hp_01"), case("demo_hp_01_b", "failed"), case("demo_ec_01", "skipped"),
                 case("other")]
        self.assertEqual(digest(cases, ["DEMO-HP-01", "DEMO-EC-01"]), {
            "totals": {"passed": 1, "failed": 1, "skipped": 1},
            "cases": [{"name": "demo_hp_01", "classname": "", "status": "passed"},
                      {"name": "demo_hp_01_b", "classname": "", "status": "failed"},
                      {"name": "demo_ec_01", "classname": "", "status": "skipped"}]})


if __name__ == "__main__":
    unittest.main()
