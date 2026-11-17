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


SE01_INSTRUCTION_FILES = (
    "skills/dev-implementation/SKILL.md",
    "skills/dev-implementation/references/entry-point-and-resume.md",
    "skills/dev-implementation/references/external-review-prompt.md",
    "skills/principal-review/references/principal-review-prompt.md",
    "skills/principal-review/references/principal-review-rules.md",
    "skills/principal-review/references/document-triage.md",
    "skills/cross-model-review/SKILL.md",
    "skills/cross-model-review/references/review-triage.md",
    "skills/dev-lifecycle/references/orchestration-roles.md",
    "skills/dev-lifecycle/references/handoff-template.md",
    "skills/dev-implementation/resources/scripts/run_external_review.py",
)

BARE_CLI_EN_MD_FLAG = re.compile(r"--(?:scenarios|hld)\s+[^\s`\"']+\.en\.md\b")
STEM_PAIRS: tuple[tuple[re.Pattern[str], re.Pattern[str]], ...] = (
    (re.compile(r"<epic_dir>\.en\.md\b"), re.compile(r"<epic_dir>\.md\b")),
    (re.compile(r"\bbdd_scenarios\.en\.md\b"), re.compile(r"\bbdd_scenarios\.md\b")),
    (re.compile(r"-design\.en\.md\b"), re.compile(r"-design\.md\b")),
    (re.compile(r"<source spec>\.en\.md\b"), re.compile(r"<source spec>\.md\b")),
    (
        re.compile(r"(?<![A-Za-z0-9_-])\*\.en\.md\b"),
        re.compile(r"(?<![A-Za-z0-9_-])\*\.md\b"),
    ),
    (re.compile(r"\.en\.md\s+HLD\b"), re.compile(r"<epic_dir>\.md\b")),
)


def _bare_en_md_instruction_lines(text: str) -> list[tuple[int, str]]:
    """Return lines that hardcode an epic `.en.md` instruction without its canonical `.md` name."""
    offenders: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if "docs/" in line:
            continue
        if BARE_CLI_EN_MD_FLAG.search(line):
            offenders.append((number, line.strip()))
            continue
        if any(
            en_pat.search(line) and not md_pat.search(line)
            for en_pat, md_pat in STEM_PAIRS
        ):
            offenders.append((number, line.strip()))
    return offenders


def test_fpg_dev_skills_do_not_require_en_md_exclusively() -> None:
    """[SE-01] Dev-lifecycle skills, prompts, and triage instructions resolve .md first (legacy .en.md)."""
    scanned = [REPO_ROOT / rel for rel in SE01_INSTRUCTION_FILES]
    assert len(scanned) > 0, "Expected SE-01 instruction files to scan"
    for path in scanned:
        assert path.is_file(), f"Missing SE-01 instruction file: {path}"

    # Verify the scanner detects bare flags and exclusive .en.md instructions while allowing SE-01 style.
    assert _bare_en_md_instruction_lines(
        "--scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md"
    )
    assert _bare_en_md_instruction_lines(
        "--hld .devtool/epic/<epic_dir>/<epic_dir>.en.md"
    )
    assert _bare_en_md_instruction_lines(
        "Read `*.en.md`, `<epic_dir>.en.md`, and `task_*.md`."
    )
    assert not _bare_en_md_instruction_lines(
        "Read `*.md` (legacy `*.en.md`) and `<epic_dir>.md` (legacy `<epic_dir>.en.md`)."
    )

    offenders: list[str] = []
    for path in scanned:
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for number, line in _bare_en_md_instruction_lines(text):
            offenders.append(f"{rel}:{number}: {line}")

    assert not offenders, "Exclusive `.en.md` epic instructions remain:\n" + "\n".join(
        offenders
    )

    entry_text = (
        REPO_ROOT / "skills/dev-implementation/references/entry-point-and-resume.md"
    ).read_text(encoding="utf-8")
    assert "both `bdd_scenarios`, both HLD variants" not in entry_text
