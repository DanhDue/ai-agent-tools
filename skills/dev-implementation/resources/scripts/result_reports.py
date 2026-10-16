#!/usr/bin/env python3
"""Read JUnit XML and Dart JSON test reports, and decide which identifiers they prove.

Imported by check_bdd_traceability.py and run_task_checks.py; it has no command line.
"""
from __future__ import annotations

import glob
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


class ReportError(Exception):
    """A report path that is missing, or a file in neither format."""


@dataclass(frozen=True)
class Case:
    name: str
    classname: str
    status: str  # "passed", "failed" or "skipped"


def reference_pattern(identifier: str) -> re.Pattern[str]:
    """Match an identifier in any case, with - and _ interchangeable, not inside a longer token."""
    body = "[-_]".join(re.escape(part) for part in identifier.split("-"))
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)


def parse_junit(text: str) -> list[Case]:
    cases = []
    for element in ET.fromstring(text).iter("testcase"):
        tags = {child.tag for child in element}
        status = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
        cases.append(Case(element.get("name", ""), element.get("classname", ""), status))
    return cases


def parse_dart(text: str) -> list[Case]:
    names: dict[object, str] = {}
    cases = []
    for line in text.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "testStart":
            names[event["test"]["id"]] = event["test"]["name"]
        elif event.get("type") == "testDone" and event.get("testID") in names:
            name = names.pop(event["testID"])
            if event.get("hidden"):
                continue
            status = ("skipped" if event.get("skipped")
                      else "passed" if event.get("result") == "success" else "failed")
            cases.append(Case(name, "", status))
    return cases


def report_files(path: str, root: Path) -> list[Path]:
    target = root / path
    if target.is_dir():
        return sorted(p for pattern in ("*.xml", "*.json") for p in target.rglob(pattern))
    if target.is_file():
        return [target]
    matches = sorted(Path(match) for match in glob.glob(str(target), recursive=True))
    if not matches:
        raise ReportError(f"results path not found: {path}")
    return [p for match in matches for p in report_files(str(match), root)]


def load_reports(paths: list[str], root: Path) -> list[Case]:
    cases: list[Case] = []
    for path in paths:
        for file in report_files(path, root):
            text = file.read_text(encoding="utf-8", errors="replace")
            lead = text.lstrip()[:1]
            try:
                if lead == "<":
                    cases.extend(parse_junit(text))
                elif lead == "{":
                    cases.extend(parse_dart(text))
                else:
                    raise ReportError(f"{file} is neither JUnit XML nor Dart JSON")
            except (ET.ParseError, ValueError, KeyError) as error:
                raise ReportError(f"{file} is not a valid report: {error}") from None
    return cases


def belongs(case: Case, identifier: str) -> bool:
    pattern = reference_pattern(identifier)
    return bool(pattern.search(case.name) or pattern.search(case.classname))


def verdicts(ids: list[str], cases: list[Case]) -> dict[str, tuple[bool, str]]:
    result: dict[str, tuple[bool, str]] = {}
    for identifier in ids:
        own = [case for case in cases if belongs(case, identifier)]
        failed = next((c for c in own if c.status == "failed"), None)
        passed = next((c for c in own if c.status == "passed"), None)
        if failed:
            result[identifier] = (False, f"failed in {failed.name}")
        elif passed:
            result[identifier] = (True, passed.name)
        elif own:
            result[identifier] = (False, "skipped")
        else:
            result[identifier] = (False, "no test case in results")
    return result


def digest(cases: list[Case], ids: list[str]) -> dict:
    own = [case for case in cases if any(belongs(case, identifier) for identifier in ids)]
    totals = {status: sum(1 for c in own if c.status == status) for status in ("passed", "failed", "skipped")}
    return {"totals": totals,
            "cases": [{"name": c.name, "classname": c.classname, "status": c.status} for c in own]}
