#!/usr/bin/env python3
"""Run unittest files and write a JUnit XML report.

Usage:
  run_unittest_junit.py --junitxml <path> <test file> [<test file> ...]

Exit codes: 0 every test and subtest passed or was skipped; 1 otherwise.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import traceback
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class RecordingResult(unittest.TextTestResult):
    """Text result that also keeps each test's outcome and duration."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.records: list[dict] = []
        self._started: dict[str, float] = {}
        self._failed_subtests: dict[str, list[tuple[str, str]]] = {}

    def startTest(self, test) -> None:
        self._started[test.id()] = time.monotonic()
        super().startTest(test)

    def _record(self, test, kind: str | None, detail: str = "") -> None:
        elapsed = time.monotonic() - self._started.pop(test.id(), time.monotonic())
        self.records.append({"test": test, "kind": kind, "detail": detail, "time": elapsed})

    def addSuccess(self, test) -> None:
        super().addSuccess(test)
        self._record(test, None)

    def addFailure(self, test, err) -> None:
        super().addFailure(test, err)
        self._record(test, "failure", self._exc_info_to_string(err, test))

    def addError(self, test, err) -> None:
        super().addError(test, err)
        self._record(test, "error", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason) -> None:
        super().addSkip(test, reason)
        self._record(test, "skipped", reason)

    def addExpectedFailure(self, test, err) -> None:
        super().addExpectedFailure(test, err)
        self._record(test, None)

    def addUnexpectedSuccess(self, test) -> None:
        super().addUnexpectedSuccess(test)
        self._record(test, "failure", "unexpected success")

    def addSubTest(self, test, subtest, err) -> None:
        super().addSubTest(test, subtest, err)
        if err is not None:
            kind = "failure" if issubclass(err[0], test.failureException) else "error"
            detail = f"{subtest}\n{self._exc_info_to_string(err, test)}"
            self._failed_subtests.setdefault(test.id(), []).append((kind, detail))

    def stopTest(self, test) -> None:
        """A test whose subtest failed gets no other outcome from unittest; record it under the test's own name."""
        failed = self._failed_subtests.pop(test.id(), [])
        if failed and test.id() in self._started:
            kind = "error" if any(k == "error" for k, _ in failed) else "failure"
            self._record(test, kind, "\n".join(detail for _, detail in failed))
        super().stopTest(test)


def load_module(path: Path, index: int):
    sys.path.insert(0, str(path.parent))
    name = path.stem if path.stem not in sys.modules else f"{path.stem}_{index}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def suite_element(path: Path, index: int) -> tuple[ET.Element, bool]:
    """Run one file; return its <testsuite> and whether everything passed."""
    suite = ET.Element("testsuite", name=path.stem)
    try:
        module = load_module(path, index)
        loaded = unittest.defaultTestLoader.loadTestsFromModule(module)
    except BaseException:
        case = ET.SubElement(suite, "testcase", classname=path.stem, name="import", time="0")
        ET.SubElement(case, "error", message="import failed").text = traceback.format_exc()
        suite.set("tests", "1"), suite.set("failures", "0"), suite.set("errors", "1"), suite.set("skipped", "0")
        return suite, False
    runner = unittest.TextTestRunner(stream=sys.stderr, resultclass=RecordingResult, verbosity=1)
    result = runner.run(loaded)
    counts = {"failure": 0, "error": 0, "skipped": 0}
    for record in result.records:
        test = record["test"]
        method = getattr(test, "_testMethodName", None)
        classname = f"{type(test).__module__}.{type(test).__name__}" if method else path.stem
        case = ET.SubElement(suite, "testcase", classname=classname,
                             name=method or test.id(), time=f"{record['time']:.6f}")
        if record["kind"]:
            counts[record["kind"]] += 1
            ET.SubElement(case, record["kind"], message=record["detail"].splitlines()[-1:][0]
                          if record["detail"] else "").text = record["detail"]
    suite.set("tests", str(len(result.records)))
    suite.set("failures", str(counts["failure"]))
    suite.set("errors", str(counts["error"]))
    suite.set("skipped", str(counts["skipped"]))
    return suite, result.wasSuccessful()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--junitxml", required=True, type=Path)
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    root = ET.Element("testsuites")
    passed = True
    for index, path in enumerate(args.files):
        suite, ok = suite_element(path.resolve(), index)
        root.append(suite)
        passed = passed and ok
    args.junitxml.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(args.junitxml, encoding="utf-8", xml_declaration=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
