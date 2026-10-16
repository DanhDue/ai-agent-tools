#!/usr/bin/env python3
"""Tests for run_unittest_junit.py.

Run: python3 -m unittest scripts/test_run_unittest_junit.py
"""
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

RUNNER = Path(__file__).parent / "run_unittest_junit.py"

MIXED = '''import unittest


class Sample(unittest.TestCase):
    def test_passes(self):
        self.assertTrue(True)

    def test_fails(self):
        self.assertEqual(1, 2)

    def test_errors(self):
        raise RuntimeError("boom")

    @unittest.skip("not today")
    def test_skipped(self):
        pass
'''
PASSING = '''import unittest


class Fine(unittest.TestCase):
    def test_ok(self):
        pass
'''
SETUP_ERROR = '''import unittest


class Fragile(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raise RuntimeError("no fixture")

    def test_never_runs(self):
        pass
'''
BROKEN = "import module_that_does_not_exist\n"


class JunitRunnerCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def run_runner(self, *files: Path) -> tuple[int, ET.Element]:
        report = self.root / "out" / "nested" / "report.xml"
        done = subprocess.run([sys.executable, str(RUNNER), "--junitxml", str(report),
                               *map(str, files)], capture_output=True, text=True)
        return done.returncode, ET.parse(report).getroot()

    def test_counts_and_children_per_outcome(self) -> None:
        code, root = self.run_runner(self.write("test_mixed.py", MIXED))
        self.assertEqual(code, 1)
        suite = root.find("testsuite")
        self.assertEqual(root.tag, "testsuites")
        self.assertEqual({key: suite.get(key) for key in ("tests", "failures", "errors", "skipped")},
                         {"tests": "4", "failures": "1", "errors": "1", "skipped": "1"})
        cases = {case.get("name"): case for case in suite.findall("testcase")}
        self.assertEqual(cases["test_passes"].get("classname"), "test_mixed.Sample")
        self.assertIsNotNone(cases["test_passes"].get("time"))
        self.assertIsNotNone(cases["test_fails"].find("failure"))
        self.assertIsNotNone(cases["test_errors"].find("error"))
        self.assertIsNotNone(cases["test_skipped"].find("skipped"))
        self.assertEqual(len(cases["test_passes"]), 0)

    def test_all_passing_exits_zero(self) -> None:
        code, root = self.run_runner(self.write("test_fine.py", PASSING))
        self.assertEqual(code, 0)
        self.assertEqual(root.find("testsuite").get("tests"), "1")

    def test_one_suite_per_file(self) -> None:
        code, root = self.run_runner(self.write("test_a.py", PASSING), self.write("test_b.py", PASSING))
        self.assertEqual(code, 0)
        self.assertEqual(len(root.findall("testsuite")), 2)

    def test_unimportable_file_becomes_import_error(self) -> None:
        code, root = self.run_runner(self.write("test_broken.py", BROKEN))
        self.assertEqual(code, 1)
        suite = root.find("testsuite")
        case = suite.find("testcase")
        self.assertEqual(case.get("name"), "import")
        self.assertIsNotNone(case.find("error"))
        self.assertEqual(suite.get("errors"), "1")

    def test_setup_class_error_is_reported_as_an_error_case(self) -> None:
        code, root = self.run_runner(self.write("test_fragile.py", SETUP_ERROR))
        self.assertEqual(code, 1)
        suite = root.find("testsuite")
        self.assertEqual(suite.get("errors"), "1")
        self.assertEqual(suite.get("tests"), "1")
        case = suite.find("testcase")
        self.assertIn("setUpClass", case.get("name"))
        self.assertIsNotNone(case.find("error"))


if __name__ == "__main__":
    unittest.main()
