"""Unit and integration tests for Task 5: Slimming rules/skills, deduplicating references, and selective task-reviewer gating."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _word_count(text: str) -> int:
    return len(text.split())


def _parse_frontmatter(text: str) -> tuple[list[str], str]:
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, flags=re.DOTALL)
    assert match is not None, "Expected YAML frontmatter delimited by --- lines"
    fm_body, rest = match.group(1), match.group(2)
    keys = [
        line.split(":", 1)[0].strip()
        for line in fm_body.splitlines()
        if re.match(r"^[A-Za-z0-9_-]+:", line)
    ]
    return keys, rest


def test_tto_hp_05_slimmed_rules_and_skills_caps() -> None:
    """[TTO-HP-05] Rules and dev-designer stay within UTF-8 byte caps, task-observer blocks subagents, and checklists offload."""
    critical_rules = _read("rules/CRITICAL_RULES.md")
    assert critical_rules.startswith("---\ntrigger: always_on\n---")
    assert len(critical_rules.encode("utf-8")) <= 8192, (
        f"CRITICAL_RULES.md too large: {len(critical_rules.encode('utf-8'))} bytes > 8192"
    )
    assert (
        "## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline"
        in critical_rules
    )
    assert "## 9. Shell Configuration" in critical_rules
    assert "## 10. Zero-Fluff Output Cap" in critical_rules
    for required_preserved in ("Verdict", "Findings", "Gate"):
        assert required_preserved in critical_rules
    assert ".devtool/review_config.json" in critical_rules
    assert "gemini-4-hydrogen-xhigh" in critical_rules
    assert "governance-checklists.md" in critical_rules
    assert (
        REPO_ROOT
        / "skills"
        / "dev-lifecycle"
        / "references"
        / "governance-checklists.md"
    ).is_file()
    assert "Gemini Flash 3.8" not in critical_rules
    assert "gemini-3.8-flash" not in critical_rules

    dev_designer = _read("skills/dev-designer/SKILL.md")
    assert len(dev_designer.encode("utf-8")) <= 22528, (
        f"skills/dev-designer/SKILL.md too large: {len(dev_designer.encode('utf-8'))} bytes > 22528"
    )
    assert "references/task-template-examples.md" in dev_designer
    assert (
        REPO_ROOT
        / "skills"
        / "dev-designer"
        / "references"
        / "task-template-examples.md"
    ).is_file()
    assert "Stage 4" in dev_designer and "bdd_scenarios.en.md" in dev_designer
    assert "target_files" in dev_designer and "200" in dev_designer
    assert 'review_tier: "full"' in dev_designer or "review_tier" in dev_designer

    verification_rows = _read("skills/dev-designer/references/verification-rows.md")
    assert "-q --tb=short --maxfail=3" in verification_rows

    task_observer = _read("skills/task-observer/SKILL.md")
    keys, after_fm = _parse_frontmatter(task_observer)
    assert keys == ["name", "description"]
    fm_block = task_observer.split("---", 2)[1]
    assert "subagent" in fm_block.lower() or "headless" in fm_block.lower()
    stripped_after = after_fm.lstrip()
    assert stripped_after.startswith("<SUBAGENT-STOP>"), (
        "Expected <SUBAGENT-STOP> immediately after frontmatter"
    )


def test_tto_hp_05_lifecycle_word_caps() -> None:
    """[TTO-HP-05] dev-lifecycle and dev-implementation meet word caps and use config-driven Role 2.3 defaults."""
    dev_lifecycle = _read("skills/dev-lifecycle/SKILL.md")
    lc_words = _word_count(dev_lifecycle)
    assert lc_words <= 2500, f"dev-lifecycle/SKILL.md word count {lc_words} > 2500"
    assert ".devtool/review_config.json" in dev_lifecycle
    assert "gemini-4-hydrogen-xhigh" in dev_lifecycle
    assert "references/governance-checklists.md" in dev_lifecycle
    assert "Rule 3" in dev_lifecycle or "StartLine" in dev_lifecycle
    assert "Zero-Fluff" in dev_lifecycle

    dev_impl = _read("skills/dev-implementation/SKILL.md")
    impl_words = _word_count(dev_impl)
    assert impl_words <= 4500, (
        f"dev-implementation/SKILL.md word count {impl_words} > 4500"
    )
    assert ".devtool/review_config.json" in dev_impl
    assert "gemini-4-hydrogen-xhigh" in dev_impl
    assert 'review_tier: "full"' in dev_impl or "review_tier" in dev_impl
    assert "StartLine" in dev_impl or "EndLine" in dev_impl
    assert "Zero-Fluff" in dev_impl

    config_checked_paths = (
        "skills/dev-lifecycle/SKILL.md",
        "skills/dev-implementation/SKILL.md",
        "skills/dev-lifecycle/references/autonomous-mode.md",
        "skills/principal-review/SKILL.md",
        "docs/lifecycles.en.md",
        "docs/lifecycles.vi.md",
    )
    for rel_path in config_checked_paths:
        content = _read(rel_path)
        for stale in ("Gemini Flash 3.8", "gemini-3.8-flash", "Gemini 3.8 Flash High"):
            assert stale not in content, (
                f"Found stale programmer model reference {stale!r} in {rel_path}"
            )
        assert (
            ".devtool/review_config.json" in content
            or "gemini-4-hydrogen-xhigh" in content
        ), f"Missing config-driven Role 2.3 default in {rel_path}"

    skill_paths = (
        "skills/task-observer/SKILL.md",
        "skills/dev-designer/SKILL.md",
        "skills/dev-implementation/SKILL.md",
        "skills/dev-lifecycle/SKILL.md",
        "skills/principal-review/SKILL.md",
        "skills/subagent-driven-development/SKILL.md",
        "skills/finishing-a-development-branch/SKILL.md",
    )
    for skill_rel in skill_paths:
        keys, _ = _parse_frontmatter(_read(skill_rel))
        assert keys == ["name", "description"], (
            f"Invalid frontmatter keys {keys} in {skill_rel}"
        )


def test_tto_ec_05_selective_task_reviewer_and_prompt_rules() -> None:
    """[TTO-EC-05] Selective task-reviewer gating, implementer prompt constraints, and thin reference pointers align."""
    for rel_path in (
        "skills/dev-designer/SKILL.md",
        "skills/dev-implementation/SKILL.md",
        "skills/subagent-driven-development/SKILL.md",
    ):
        text = _read(rel_path)
        lowered = text.lower()
        assert "review_tier" in text
        for label in ("security", "architecture", "concurrency", "contract"):
            assert label in lowered, (
                f"Missing high-risk trigger label {label!r} in {rel_path}"
            )
        assert "> 2" in text or "more than 2" in lowered, (
            f"Missing > 2 non-test modules trigger in {rel_path}"
        )
        assert "skip" in lowered, (
            f"Missing skip rule for trivial single-file tasks in {rel_path}"
        )

    sdd = _read("skills/subagent-driven-development/SKILL.md")
    assert "-U5" in sdd
    assert "-U10" not in sdd
    assert "Zero-Fluff" in sdd
    assert "StartLine" in sdd or "EndLine" in sdd

    impl_prompt = _read("skills/subagent-driven-development/implementer-prompt.md")
    assert "d3nexus:task-observer" in impl_prompt
    assert (
        "not" in impl_prompt.lower()
        or "never" in impl_prompt.lower()
        or "do not" in impl_prompt.lower()
    )
    assert "StartLine" in impl_prompt or "sed -n" in impl_prompt
    assert "Zero-Fluff" in impl_prompt
    assert "run_task_checks.py red" in impl_prompt
    assert "run_task_checks.py verify" in impl_prompt
    assert "the evidence file is the test evidence" in impl_prompt

    pointer_pairs = (
        (
            "skills/dev-implementation/references/principal-review-prompt.md",
            "../../principal-review/references/principal-review-prompt.md",
        ),
        (
            "skills/dev-implementation/references/principal-review-rules.md",
            "../../principal-review/references/principal-review-rules.md",
        ),
        (
            "skills/dev-implementation/references/review-triage.md",
            "../../cross-model-review/references/review-triage.md",
        ),
        (
            "skills/dev-implementation/references/local-review-setup.md",
            "../../cross-model-review/references/local-review-setup.md",
        ),
    )
    for pointer_rel, expected_target in pointer_pairs:
        pointer_text = _read(pointer_rel)
        assert expected_target in pointer_text, (
            f"Expected pointer {expected_target} in {pointer_rel}"
        )
        assert len(pointer_text.encode("utf-8")) <= 1024, (
            f"Pointer {pointer_rel} should stay thin (<= 1024 bytes)"
        )

    assert "No Reconstructed Logic" in _read(
        "skills/dev-implementation/references/review-rules.md"
    )
    assert "5-Layer Deep Verification Checklist" in _read(
        "skills/principal-review/references/principal-review-rules.md"
    )
    assert "Auto-Triage Gate" in _read(
        "skills/cross-model-review/references/review-triage.md"
    )


def test_tto_st_05_pre_finish_bilingual_sync_hook() -> None:
    """[TTO-ST-05] Stage 4 Pre-Finish Hook delta-syncs .vi.md, stamps sha256, and enforces strict bilingual gates."""
    finishing = _read("skills/finishing-a-development-branch/SKILL.md")
    assert "sync-en-sha256" in finishing
    assert "bdd_scenarios.vi.md" in finishing
    assert "check_document.py --require-toc --require-bilingual" in finishing
    assert "check_epic_readiness.py <epic_slug> --strict-bilingual" in finishing
    assert (
        "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md "
        "--tasks .devtool/epic/<epic_dir>/task_*.md --strict-bilingual" in finishing
    )
    assert "resume_context.py" in finishing and "--complete" in finishing
    assert "../../rules/CRITICAL_RULES.md#commit-message-format" in finishing


class TestTTODocsAndSlimming_Integration:
    """Integration provenance wrapper for Tier C scenarios in Task 5."""

    def test_tto_hp_05_integration(self) -> None:
        """[TTO-HP-05] Integration check for slimmed rules/skills, task-observer guard, and word caps."""
        test_tto_hp_05_slimmed_rules_and_skills_caps()
        test_tto_hp_05_lifecycle_word_caps()

    def test_tto_ec_05_integration(self) -> None:
        """[TTO-EC-05] Integration check for selective task-reviewer gating, implementer prompt rules, and dedup."""
        test_tto_ec_05_selective_task_reviewer_and_prompt_rules()

    def test_tto_st_05_integration(self) -> None:
        """[TTO-ST-05] Integration check for Stage 4 Pre-Finish bilingual sync hook."""
        test_tto_st_05_pre_finish_bilingual_sync_hook()
