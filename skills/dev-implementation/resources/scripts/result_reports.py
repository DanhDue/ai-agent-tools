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
        try:
            event = json.loads(line)
        except Exception:
            continue
        if isinstance(event, list):
            if event and isinstance(event[0], dict):
                event = event[0]
            else:
                continue
        if not isinstance(event, dict):
            continue
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


def load_files(files: list[Path]) -> list[Case]:
    cases: list[Case] = []
    for file in files:
        text = file.read_text(encoding="utf-8", errors="replace")
        lead = text.lstrip()[:1]
        try:
            if lead == "<":
                cases.extend(parse_junit(text))
            elif lead == "{" or any(line.startswith("{") for line in text.splitlines()):
                cases.extend(parse_dart(text))
            else:
                raise ReportError(f"{file} is neither JUnit XML nor Dart JSON")
        except (ET.ParseError, ValueError, KeyError) as error:
            raise ReportError(f"{file} is not a valid report: {error}") from None
    return cases


def load_reports(paths: list[str], root: Path) -> list[Case]:
    return load_files([file for path in paths for file in report_files(path, root)])


def belongs(case: Case, identifier: str) -> bool:
    pattern = reference_pattern(identifier)
    return bool(pattern.search(case.name) or pattern.search(case.classname))


UNIT_CLASSNAME_PATTERNS = [
    re.compile(r"^tests?[\./]unit[\./]", re.IGNORECASE),
    re.compile(r"\bUnitTests?\b", re.IGNORECASE),
    re.compile(r"\bMockTest\b", re.IGNORECASE),
    re.compile(r"^unit[\._]", re.IGNORECASE),
]

_SCENARIO_TIER_CACHE: dict[str, str] = {}


def _discover_scenario_tiers() -> dict[str, str]:
    if _SCENARIO_TIER_CACHE:
        return _SCENARIO_TIER_CACHE
    devtool_epic = Path(".devtool/epic")
    if not devtool_epic.is_dir():
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent.parent
            candidate = repo_root / ".devtool" / "epic"
            if candidate.is_dir():
                devtool_epic = candidate
        except (AttributeError, OSError):
            pass
    if devtool_epic.is_dir():
        for bdd_file in devtool_epic.glob("*/*bdd_scenarios*.md"):
            try:
                for line in bdd_file.read_text(encoding="utf-8").splitlines():
                    m = re.search(r"Scenario:\s*\[([^\]]+)\](?:\s*\[([^\]]+)\])?", line)
                    if m:
                        scen_id = m.group(1).strip()
                        tier_info = m.group(2).strip() if m.group(2) else ""
                        _SCENARIO_TIER_CACHE[scen_id] = tier_info
            except (OSError, UnicodeDecodeError):
                pass
    return _SCENARIO_TIER_CACHE


def is_pure_unit_mock(classname: str) -> bool:
    """Detect if classname represents a pure unit mock test rather than an integration runner."""
    if not classname or not classname.strip():
        return True
    return any(p.search(classname) for p in UNIT_CLASSNAME_PATTERNS)


def is_tier_c_scenario(identifier: str, metadata: dict[str, str] | None = None) -> bool:
    """Identify Tier C integration scenarios from metadata, explicit tags, or discovered scenarios."""
    if re.search(r"\bTier\s*C\b", identifier, re.IGNORECASE):
        return True
    if re.search(r"\bTier\s*[AB]\b", identifier, re.IGNORECASE):
        return False

    if metadata and identifier in metadata:
        meta = metadata[identifier]
        if re.search(r"\bTier\s*C\b", meta, re.IGNORECASE):
            return True
        if re.search(r"\bTier\s*[AB]\b", meta, re.IGNORECASE):
            return False

    tiers = _discover_scenario_tiers()
    if identifier in tiers:
        meta = tiers[identifier]
        if re.search(r"\bTier\s*C\b", meta, re.IGNORECASE):
            return True
        if re.search(r"\bTier\s*[AB]\b", meta, re.IGNORECASE):
            return False

    return False


def verdicts(
    ids: list[str],
    cases: list[Case],
    scenario_metadata: dict[str, str] | None = None,
) -> dict[str, tuple[bool, str]]:
    result: dict[str, tuple[bool, str]] = {}
    for identifier in ids:
        own = [case for case in cases if belongs(case, identifier)]
        failed = next((c for c in own if c.status == "failed"), None)
        passed = next((c for c in own if c.status == "passed"), None)
        if failed:
            result[identifier] = (False, f"failed in {failed.name}")
        elif passed:
            if is_tier_c_scenario(identifier, scenario_metadata):
                valid_integration = [
                    c for c in own if c.status == "passed" and not is_pure_unit_mock(c.classname)
                ]
                if not valid_integration:
                    result[identifier] = (
                        False,
                        f"pure unit test class '{passed.classname}' lacks integration runner provenance for Tier C scenario",
                    )
                else:
                    result[identifier] = (True, valid_integration[0].name)
            else:
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
