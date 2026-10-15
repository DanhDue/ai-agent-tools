#!/usr/bin/env python3
"""Verify that every lifecycle document producer exposes the shared contract."""

import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]

EXPECTED = {
    "skills/dev-brainstorming/SKILL.md": (
        "YYYY-MM-DD-<topic>-design.en.md",
        "YYYY-MM-DD-<topic>-design.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-brainstorming/SKILL.md": (
        "YYYY-MM-DD-<topic>-design.en.md",
        "YYYY-MM-DD-<topic>-design.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/dev-designer/SKILL.md": (
        "<epic_name>.en.md",
        "<epic_name>.vi.md",
        "bdd_scenarios.en.md",
        "bdd_scenarios.vi.md",
        "--require-toc",
        "--require-bilingual",
        "Task files are English-only",
        "check_bdd_traceability.py plan",
        "Covers:",
        "Integration test roots:",
        "at least one automated integration test",
        "Handoff Choice",
    ),
    "skills/writing-plans/SKILL.md": (
        "YYYY-MM-DD-<feature-name>.en.md",
        "YYYY-MM-DD-<feature-name>.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-designer/SKILL.md": (
        "<doc_dir>.en.md",
        "<doc_dir>.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-implementation/SKILL.md": (
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc_quality_check/SKILL.md": (
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc_quality_check/references/document-reviewer-prompt.md": (
        "English document",
        "Vietnamese document",
        "Translation parity",
    ),
    "skills/dev-implementation/SKILL.md": (
        '`profile`: `"epic"`',
        '`repository_sha`',
        "aggregated verdict of **PASS**",
        "check_bdd_traceability.py tests",
        "--ids",
        "Entry-Point Detection",
        "Resume Procedure",
        "handoff.md",
    ),
    "skills/dev-lifecycle/SKILL.md": (
        'profile `epic`',
        "`repository_sha`",
        "FAIL > BLOCKED > PASS",
        "check_bdd_traceability.py tests",
        "Granting Gate 4 without a passing traceability check",
        "Handoff Choice",
        "handoff-template.md",
        "Resuming an Epic",
        "Packaged",
    ),
    "skills/pr_review/SKILL.md": (
        '"profile": "pr"',
        '"base_ref"',
        "Executive Report Format",
    ),
}

FORBIDDEN = {
    "skills/pr_review/SKILL.md": (
        "melos test",
        "./gradlew check",
        "swift test",
        "cleanup-java",
    ),
}


def main() -> int:
    failures = []
    for relative_path, required_tokens in EXPECTED.items():
        text = (ROOT / relative_path).read_text()
        for token in required_tokens:
            if token not in text:
                failures.append(f"{relative_path}: missing {token}")
    for relative_path, forbidden_tokens in FORBIDDEN.items():
        text = (ROOT / relative_path).read_text()
        for token in forbidden_tokens:
            if token in text:
                failures.append(f"{relative_path}: contains forbidden token {token}")
    if failures:
        for failure in failures:
            print(f"  FAIL {failure}")
        return 1
    print(f"  checked {len(EXPECTED)} lifecycle document contract surfaces")
    return 0


if __name__ == "__main__":
    sys.exit(main())
