"""Doc-contract tests for Observer Hardening Batch 2 (#18 browser gate & #20 verification-rows)."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

OBS_18_DOCS: tuple[str, ...] = (
    "skills/writing-plans/SKILL.md",
    "skills/dev-designer/SKILL.md",
    "skills/dev-designer/references/task-template-examples.md",
    "skills/subagent-driven-development/SKILL.md",
)

PERSONAL_LEAK_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"/Users/[A-Za-z0-9._-]+"),
    re.compile(r"antigravity_homes/[A-Za-z0-9._-]+"),
    re.compile(r"\bdanhdue", re.IGNORECASE),
)


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


def test_obs18_skills_require_hermetic_playwright_primary_and_devtools_preflight() -> (
    None
):
    """#18: Open-source skills make hermetic Playwright E2E primary and pre-flight DevToolsActivePort."""
    writing_plans = _read("skills/writing-plans/SKILL.md")
    assert "Playwright" in writing_plans
    assert "hermetic" in writing_plans.lower()
    assert "DevToolsActivePort" in writing_plans
    assert "fallback" in writing_plans.lower()

    dev_designer = _read("skills/dev-designer/SKILL.md")
    assert "Playwright" in dev_designer
    assert "DevToolsActivePort" in dev_designer

    task_examples = _read("skills/dev-designer/references/task-template-examples.md")
    assert "Playwright" in task_examples
    assert "DevToolsActivePort" in task_examples

    sdd = _read("skills/subagent-driven-development/SKILL.md")
    assert "DevToolsActivePort" in sdd
    assert "Playwright" in sdd
    assert "Ruling:" in sdd


def test_obs18_docs_contain_zero_personal_paths_and_preserve_skill_contract() -> None:
    """#18 confidentiality & CLAUDE.md contract: no personal paths, no superpowers:, exact SKILL.md frontmatter."""
    for rel in OBS_18_DOCS:
        text = _read(rel)
        assert "superpowers:" not in text, (
            f"{rel} contains stale superpowers: reference"
        )
        for pat in PERSONAL_LEAK_PATTERNS:
            assert pat.search(text) is None, (
                f"{rel} leaked personal pattern {pat.pattern!r}"
            )

    for rel in (
        "skills/writing-plans/SKILL.md",
        "skills/dev-designer/SKILL.md",
        "skills/subagent-driven-development/SKILL.md",
    ):
        text = _read(rel)
        fm = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert fm is not None, f"{rel}: missing YAML frontmatter"
        keys = re.findall(r"^([A-Za-z_][\w-]*):", fm.group(1), flags=re.MULTILINE)
        assert set(keys) == {"name", "description"}, (
            f"{rel}: invalid frontmatter keys {keys!r}"
        )
