"""Contract test for English-only dev-lifecycle skill text and Vietnamese mirror isolation.

Covers: FPG-AR-04
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_REL = "rules/CRITICAL_RULES.md"
RULE_11_HEADING = "## 11. English SSOT and Vietnamese Mirror Isolation"
RULE_11_REQUIRED_TOKENS = (
    "MUST NOT",
    "*.vi.md",
    "Role 1.0",
    "doc-lifecycle",
    "(a) a file Role 1.0 names explicitly",
    "(b) writing the `.vi.md` variant of a doc-lifecycle document",
)
SCANNED_SKILLS = (
    "dev-lifecycle",
    "dev-brainstorming",
    "dev-designer",
    "dev-implementation",
    "writing-plans",
    "finishing-a-development-branch",
    "principal-review",
    "cross-model-review",
)
BILINGUAL_SKILLS = ("doc-brainstorming", "doc-designer", "doc-implementation")
BILINGUAL_FLAGS = ("--require-bilingual", "--strict-bilingual")
MIRROR_MENTION = re.compile(r"\.vi\.md")
MIRROR_GUARD = re.compile(r"MUST NOT|\b[Nn]ever\b|not SSOT")


def _scan_set() -> list[Path]:
    files: list[Path] = []
    for skill in SCANNED_SKILLS:
        skill_dir = REPO_ROOT / "skills" / skill
        files.append(skill_dir / "SKILL.md")
        files.extend(sorted((skill_dir / "references").glob("**/*.md")))
    return files


def _unguarded_mirror_lines(text: str) -> list[tuple[int, str]]:
    """Return lines that mention a `.vi.md` mirror without a prohibition marker."""
    return [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if MIRROR_MENTION.search(line) and not MIRROR_GUARD.search(line)
    ]


def _missing_rule_11_tokens(section_text: str) -> list[str]:
    """Return required Rule 11 prohibitions or SE-01 exceptions absent from section_text."""
    normalized = " ".join(section_text.split())
    return [token for token in RULE_11_REQUIRED_TOKENS if token not in normalized]


def test_fpg_ar_04_dev_skills_are_english_only_and_isolate_mirrors() -> None:
    """[FPG-AR-04] [Tier A - Unit] Dev-lifecycle skills are English-only and isolate Vietnamese mirrors."""
    scan_set = _scan_set()
    assert len(scan_set) > len(SCANNED_SKILLS), "reference files must be scanned too"

    # The scanner itself must separate an instruction from a prohibition.
    assert _unguarded_mirror_lines("Write `x.vi.md` next to it.") == [
        (1, "Write `x.vi.md` next to it.")
    ]
    assert not _unguarded_mirror_lines("You MUST NOT open `x.vi.md`.")
    assert not _unguarded_mirror_lines("Vietnamese `x.vi.md` is not SSOT.")
    assert not _unguarded_mirror_lines("never read `x.vi.md` mirrors")

    offenders: list[str] = []
    for path in scan_set:
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        offenders.extend(
            f"{rel}:{number}: {line}" for number, line in _unguarded_mirror_lines(text)
        )
        offenders.extend(
            f"{rel}: contains {flag}" for flag in BILINGUAL_FLAGS if flag in text
        )
    assert not offenders, "Bilingual instructions remain:\n" + "\n".join(offenders)

    rules = (REPO_ROOT / RULES_REL).read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(RULE_11_HEADING)}$", rules, flags=re.MULTILINE)
    rule_11 = rules.split(RULE_11_HEADING, 1)[1].split("\n## ", 1)[0]
    missing = _missing_rule_11_tokens(rule_11)
    assert not missing, f"Rule 11 is missing {missing!r}"
    # The Rule 11 check must fail if either SE-01 exception is dropped.
    assert "(a) a file Role 1.0 names explicitly" in _missing_rule_11_tokens(
        rule_11.replace("(a) a file Role 1.0 names explicitly", "")
    )
    assert (
        "(b) writing the `.vi.md` variant of a doc-lifecycle document"
        in _missing_rule_11_tokens(
            rule_11.replace(
                "(b) writing the `.vi.md` variant of a doc-lifecycle document", ""
            )
        )
    )

    for skill in BILINGUAL_SKILLS:
        text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        assert "--require-bilingual" in text, f"{skill} lost its bilingual contract"
