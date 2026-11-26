"""Tier C acceptance tests for Task 06: Kit skill docs, merge hygiene, and verify.sh gate.

Covers BDD Scenarios:
- OHK-HP-06: Updated kit skills preserve metadata contracts and observation rules
- OHK-AR-02: Non-overlapping watchdog timer guidance preserves merge hygiene in subagent-driven-development
- OHK-AR-03: Kit verification gate verify.sh passes cleanly across all registered suites and contracts
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

OHK_SUITES: tuple[str, ...] = (
    "tests/test_ohk_worktree_and_pool.py",
    "tests/test_ohk_revise_and_replay.py",
    "tests/test_ohk_python_env_and_doc_refusal.py",
    "tests/test_ohk_web_ui_audit.py",
    "tests/test_ohk_cmr_and_contracts.py",
    "tests/test_ohk_docs_and_acceptance.py",
)

TASK_06_DOC_FILES: tuple[str, ...] = (
    "skills/dev-brainstorming/SKILL.md",
    "skills/dev-brainstorming/visual-companion.md",
    "skills/dev-designer/SKILL.md",
    "skills/dev-designer/references/task-template-examples.md",
    "skills/dev-designer/references/verification-rows.md",
    "skills/doc-designer/SKILL.md",
    "skills/doc_quality_check/SKILL.md",
    "skills/using-git-worktrees/SKILL.md",
    "skills/subagent-driven-development/SKILL.md",
    "skills/dev-implementation/SKILL.md",
    "skills/python-quality-check/SKILL.md",
    "skills/python-quality-check/references/python-capability-contract.md",
    "skills/cross-model-review/SKILL.md",
    "skills/cross-model-review/references/review-triage.md",
    "skills/dev-lifecycle/references/orchestration-roles.md",
    "skills/sync-shared-contracts/SKILL.md",
    "skills/writing-plans/SKILL.md",
)

EXPECTED_ORIGINAL_WAITING_PARAGRAPH = (
    "**Waiting on dispatched subagents:** never poll a wait interface with\n"
    "short timeouts, and never sit in one silent, open-ended wait either.\n"
    "While you have local work — ledger updates, packaging the next review,\n"
    "reading reports — keep working; child results arrive on their own.\n"
    "When you are genuinely idle, wait in bounded stretches (five to ten\n"
    "minutes, where your platform allows), and between stretches post one\n"
    "line of status and reconcile your live children: list them, and chase\n"
    "any that finished without reporting. A bounded stretch keeps nearly\n"
    "all of a long wait's efficiency while guaranteeing a stuck or lost\n"
    "child is noticed within minutes, not at the end of the session."
)


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _strip_fences_and_inline_code(text: str) -> str:
    no_fences = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", no_fences)


def _heading_anchor(heading: str) -> str:
    lowered = heading.lower()
    cleaned = re.sub(r"[^\w\s-]", "", lowered)
    return "#" + cleaned.replace(" ", "-")


def _assert_all_skill_frontmatter_links_and_anchors() -> None:
    skill_files = sorted((REPO_ROOT / "skills").glob("*/SKILL.md"))
    assert skill_files, "Expected skills/*/SKILL.md files to exist"

    for skill_path in skill_files:
        text = skill_path.read_text(encoding="utf-8")
        fm = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert fm is not None, f"{skill_path}: missing YAML frontmatter"
        keys = re.findall(r"^([A-Za-z_][\w-]*):", fm.group(1), flags=re.MULTILINE)
        assert set(keys) == {"name", "description"}, (
            f"{skill_path}: frontmatter keys {keys!r} must be exclusively name and description"
        )

        # Verify ToC anchors match headings (mirrors verify.sh section 4).
        in_fence = False
        anchors: set[str] = set()
        for line in text.splitlines():
            if line.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence and re.match(r"^#{2,6} ", line):
                anchors.add(_heading_anchor(re.sub(r"^#+ ", "", line).rstrip()))
        for link in re.findall(r"\]\((#[^)]+)\)", text):
            assert link.lower() in anchors, (
                f"{skill_path}: broken internal anchor {link!r}"
            )

    # Verify relative links resolve across all Task 06 touched docs + all SKILL.md files.
    checked_docs = sorted(set(skill_files) | {REPO_ROOT / p for p in TASK_06_DOC_FILES})
    for doc_path in checked_docs:
        stripped = _strip_fences_and_inline_code(doc_path.read_text(encoding="utf-8"))
        for link in re.findall(r"\]\(([^)#][^)]*)\)", stripped):
            if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
                continue
            target = doc_path.parent / link.split("#", 1)[0]
            assert target.exists(), f"{doc_path}: broken relative link {link!r}"

    # Verify zero stale superpowers: cross-namespace references in touched docs.
    for rel_path in TASK_06_DOC_FILES:
        assert "superpowers:" not in _read(rel_path), (
            f"{rel_path}: must not reference stale 'superpowers:' namespace"
        )


def test_ohk_hp_06_skill_contracts_and_directives() -> None:
    """[OHK-HP-06] [Tier C - Integration] Updated kit skills preserve metadata contracts and observation rules."""
    _assert_all_skill_frontmatter_links_and_anchors()

    # #4: Visual Companion Asset Persistence
    dev_brainstorm = _read("skills/dev-brainstorming/SKILL.md")
    assert ".superpowers/brainstorm/" in dev_brainstorm
    assert "/assets/" in dev_brainstorm
    assert "Approved Visual Companions" in dev_brainstorm

    visual_companion = _read("skills/dev-brainstorming/visual-companion.md")
    assert ".superpowers/brainstorm/" in visual_companion
    assert ".devtool/epic/" in visual_companion and "/assets/" in visual_companion
    assert "Approved Visual Companions" in visual_companion

    dev_designer = _read("skills/dev-designer/SKILL.md")
    assert "Approved Visual Companions" in dev_designer
    assert "assets/" in dev_designer

    task_templates = _read("skills/dev-designer/references/task-template-examples.md")
    assert "Approved Visual Companions" in task_templates
    assert "assets/" in task_templates

    # #5: Deferred Step 1 Task Links (inline code spans -> relative links in Step 2)
    assert "inline code span" in dev_designer.lower()
    assert "`task_01_" in dev_designer
    assert "[Task 01](task_01_" in dev_designer

    assert "inline code span" in task_templates.lower()
    assert "`task_01_" in task_templates
    assert "[Task 01](task_01_" in task_templates

    doc_designer = _read("skills/doc-designer/SKILL.md")
    assert "inline code span" in doc_designer.lower()
    assert "`task_01_" in doc_designer
    assert "[Task 01](task_01_" in doc_designer

    # #6: Scoped R8 --replay Guidance
    assert "check_epic_readiness.py <epic_name>" in dev_designer
    assert "--replay" in dev_designer
    assert "Replace in" in dev_designer and "Insert in" in dev_designer
    assert "self-skip" in dev_designer.lower() or "r8 skip" in dev_designer.lower()

    # #8: Multi-Template Cache-Bust Scope
    for rel_path, text in (
        ("skills/dev-designer/SKILL.md", dev_designer),
        ("skills/dev-designer/references/task-template-examples.md", task_templates),
    ):
        assert "*.html" in text and "*.astro" in text, (
            f"{rel_path}: missing multi-template glob guidance"
        )
        assert "*.jinja" in text, f"{rel_path}: missing jinja template glob guidance"
        assert "?v=" in text, f"{rel_path}: missing ?v= cache-bust guidance"

    # #9: Zsh-Safe Check 0 Snippet
    doc_qc = _read("skills/doc_quality_check/SKILL.md")
    expected_check0 = (
        "git diff --name-only -z <base_ref>...HEAD | xargs -0 "
        "python3 skills/doc_quality_check/resources/scripts/check_document.py --changed-files"
    )
    assert expected_check0 in doc_qc, "doc_quality_check Check 0 must use -z | xargs -0"
    assert "$(git diff --name-only <base_ref>...HEAD)" not in doc_qc, (
        "doc_quality_check Check 0 must not use unquoted command substitution"
    )

    # #11: Python uv Optional Extras & UV_NO_SYNC=1 Docs
    py_qc = _read("skills/python-quality-check/SKILL.md")
    py_contract = _read(
        "skills/python-quality-check/references/python-capability-contract.md"
    )
    dev_impl = _read("skills/dev-implementation/SKILL.md")
    for rel_path, text in (
        ("skills/python-quality-check/SKILL.md", py_qc),
        (
            "skills/python-quality-check/references/python-capability-contract.md",
            py_contract,
        ),
        ("skills/dev-implementation/SKILL.md", dev_impl),
    ):
        assert "--all-extras" in text, f"{rel_path}: missing --all-extras guidance"
        assert "UV_NO_SYNC=1" in text, f"{rel_path}: missing UV_NO_SYNC=1 guidance"

    # #12: deferred: out-of-scope epic doc (§4.4) Docs
    cmr_skill = _read("skills/cross-model-review/SKILL.md")
    cmr_triage = _read("skills/cross-model-review/references/review-triage.md")
    roles_doc = _read("skills/dev-lifecycle/references/orchestration-roles.md")
    token_12 = "deferred: out-of-scope epic doc (§4.4)"
    for rel_path, text in (
        ("skills/cross-model-review/SKILL.md", cmr_skill),
        ("skills/cross-model-review/references/review-triage.md", cmr_triage),
        ("skills/dev-lifecycle/references/orchestration-roles.md", roles_doc),
    ):
        assert token_12 in text, f"{rel_path}: missing {token_12!r}"
    assert "deferred:" in cmr_triage and "dismissed:" in cmr_triage

    # #13: sync_contracts.py diff-check --allow-dirty Docs
    sync_skill = _read("skills/sync-shared-contracts/SKILL.md")
    for rel_path, text in (
        ("skills/sync-shared-contracts/SKILL.md", sync_skill),
        ("skills/dev-designer/SKILL.md", dev_designer),
    ):
        assert "--allow-dirty" in text, f"{rel_path}: missing --allow-dirty docs"
        for protected in (
            "shared-contracts",
            ".agents/contract_map.json",
            ".agents/contract_sync.json",
        ):
            assert protected in text, (
                f"{rel_path}: missing protected path {protected!r} for --allow-dirty"
            )
    assert "Gate 4" in sync_skill

    # #15: Shared .venv Symlink PYTHONPATH + UV_NO_SYNC=1 Guidance
    worktrees_skill = _read("skills/using-git-worktrees/SKILL.md")
    sdd_skill = _read("skills/subagent-driven-development/SKILL.md")
    for rel_path, text in (
        ("skills/using-git-worktrees/SKILL.md", worktrees_skill),
        ("skills/subagent-driven-development/SKILL.md", sdd_skill),
        ("skills/dev-implementation/SKILL.md", dev_impl),
    ):
        assert 'UV_NO_SYNC=1 PYTHONPATH="$WORKTREE_ROOT/src"' in text, (
            f"{rel_path}: missing shared .venv UV_NO_SYNC=1 PYTHONPATH guidance"
        )
        assert ".venv" in text

    # #16: Quality-Manifest Commands & Ban Bare npx
    writing_plans = _read("skills/writing-plans/SKILL.md")
    verification_rows = _read("skills/dev-designer/references/verification-rows.md")
    for rel_path, text in (
        ("skills/writing-plans/SKILL.md", writing_plans),
        ("skills/dev-designer/SKILL.md", dev_designer),
        ("skills/dev-designer/references/verification-rows.md", verification_rows),
    ):
        assert ".agents/quality/*-quality.json" in text, (
            f"{rel_path}: missing .agents/quality/*-quality.json reference"
        )
        assert "--no-install" in text, f"{rel_path}: missing npx --no-install rule"
        assert "--yes --package" in text, (
            f"{rel_path}: missing explicit --yes --package alternative"
        )
    # Concrete Web examples must not teach bare npx.
    web_section = verification_rows.split("## Web", 1)[1].split("## iOS", 1)[0]
    assert "npx --no-install vitest" in web_section
    assert "npx --no-install eslint" in web_section
    assert "npx --no-install tsc --noEmit" in web_section
    assert "npx --no-install playwright" in web_section
    assert "npx astro preview" not in writing_plans


def test_ohk_ar_02_subagent_waiting_merge_hygiene() -> None:
    """[OHK-AR-02] [Tier C - Integration] Non-overlapping watchdog timer guidance preserves merge hygiene in subagent-driven-development."""
    sdd_text = _read("skills/subagent-driven-development/SKILL.md")

    assert EXPECTED_ORIGINAL_WAITING_PARAGRAPH in sdd_text, (
        "Original '**Waiting on dispatched subagents:**' paragraph from main must remain byte-identical"
    )

    # Confirm the expected paragraph still matches git main when main ref is present.
    main_show = subprocess.run(
        ["git", "show", "main:skills/subagent-driven-development/SKILL.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if main_show.returncode == 0:
        assert EXPECTED_ORIGINAL_WAITING_PARAGRAPH in main_show.stdout

    after_waiting = sdd_text.split(EXPECTED_ORIGINAL_WAITING_PARAGRAPH, 1)[1]
    between_waiting_and_step1 = after_waiting.split(
        "### 1. Dispatch the implementer", 1
    )[0]
    bullet_lines = [
        line.strip()
        for line in between_waiting_and_step1.splitlines()
        if line.lstrip().startswith("- ")
    ]
    assert bullet_lines, (
        "Expected a standalone follow-on bullet immediately below the Waiting paragraph"
    )
    joined_bullets = " ".join(bullet_lines)
    assert "invoke_subagent" in joined_bullets
    assert 'schedule(DurationSeconds=180, TimerCondition="any")' in joined_bullets


def _run_non_recursive_static_checks() -> None:
    """Validate verify.sh static sections (1-10) safely when already nested under VERIFY_SH_ACTIVE=1."""
    for manifest_rel in (
        "plugin.json",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
    ):
        json.loads(_read(manifest_rel))

    _assert_all_skill_frontmatter_links_and_anchors()

    fidelity = subprocess.run(
        [sys.executable, "scripts/check_source_fidelity.py"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert fidelity.returncode == 0, (
        f"check_source_fidelity.py failed:\n{fidelity.stdout}\n{fidelity.stderr}"
    )

    hook = subprocess.run(
        ["bash", "hooks/session-start"],
        input="{}",
        cwd=REPO_ROOT,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(REPO_ROOT)},
        capture_output=True,
        text=True,
        check=False,
    )
    assert hook.returncode == 0, f"hooks/session-start failed: {hook.stderr}"
    payload = json.loads(hook.stdout)
    assert "hookSpecificOutput" in payload or "injectSteps" in payload


@pytest.fixture(scope="module")
def verify_sh_full_result() -> subprocess.CompletedProcess[str] | None:
    """Run bash scripts/verify.sh --full at most once per pytest invocation of this module."""
    if os.environ.get("VERIFY_SH_ACTIVE") == "1":
        return None
    return subprocess.run(
        ["bash", "scripts/verify.sh", "--full"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _assert_verify_sh_passes(proc: subprocess.CompletedProcess[str] | None) -> None:
    """Validate verify.sh registrations and either nested static checks or full run output."""
    verify_text = _read("scripts/verify.sh")
    assert "export VERIFY_SH_ACTIVE=1" in verify_text

    suites_block = verify_text.split("SUITES = [", 1)[1].split("]\n", 1)[0]
    for suite_rel in OHK_SUITES:
        assert (REPO_ROOT / suite_rel).is_file(), f"Missing OHK test suite: {suite_rel}"
        assert f'"{suite_rel}"' in suites_block, (
            f"scripts/verify.sh SUITES is missing registration for {suite_rel}"
        )

    if os.environ.get("VERIFY_SH_ACTIVE") == "1":
        _run_non_recursive_static_checks()
        return

    assert proc is not None
    tail_out = "\n".join(proc.stdout.splitlines()[-40:])
    assert proc.returncode == 0, (
        f"bash scripts/verify.sh --full exited {proc.returncode}:\n"
        f"{tail_out}\nSTDERR:\n{proc.stderr[-1000:]}"
    )
    assert "PASS — safe to publish" in proc.stdout, (
        f"Missing 'PASS — safe to publish' in verify.sh output:\n{tail_out}"
    )
    for sec_num in range(1, 11):
        assert f"== {sec_num}." in proc.stdout, (
            f"verify.sh --full output missing static section {sec_num}"
        )
    for suite_rel in OHK_SUITES:
        assert f"ok   [§23] {suite_rel}" in proc.stdout, (
            f"verify.sh --full output did not report passing suite {suite_rel}"
        )


def test_ohk_ar_03_verify_sh_passes(
    verify_sh_full_result: subprocess.CompletedProcess[str] | None,
) -> None:
    """[OHK-AR-03] [Tier C - Integration] Kit verification gate verify.sh passes cleanly across all registered suites and contracts."""
    _assert_verify_sh_passes(verify_sh_full_result)


class Test_Ohk_Docs_And_Acceptance_Integration:
    """Tier C integration provenance wrapper for Task 06 BDD scenarios."""

    def test_ohk_hp_06_integration(self) -> None:
        """[OHK-HP-06] [Tier C - Integration] Updated kit skills preserve metadata contracts and observation rules."""
        test_ohk_hp_06_skill_contracts_and_directives()

    def test_ohk_ar_02_integration(self) -> None:
        """[OHK-AR-02] [Tier C - Integration] Non-overlapping watchdog timer guidance preserves merge hygiene in subagent-driven-development."""
        test_ohk_ar_02_subagent_waiting_merge_hygiene()

    def test_ohk_ar_03_integration(
        self,
        verify_sh_full_result: subprocess.CompletedProcess[str] | None,
    ) -> None:
        """[OHK-AR-03] [Tier C - Integration] Kit verification gate verify.sh passes cleanly across all registered suites and contracts."""
        _assert_verify_sh_passes(verify_sh_full_result)
