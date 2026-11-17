"""Governance text contract tests for the four-persona model.

Covers BDD Scenarios:
- FPG-AR-03: Governance text uses the four-persona model everywhere
- FPG-AR-07: Governance text routes agy dispatch through the pool and keeps ag_run out of agent shells
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLES_REL = "skills/dev-lifecycle/references/orchestration-roles.md"
RULES_REL = "rules/CRITICAL_RULES.md"
MAPPING_HEADING = "## Old-to-New Role Mapping"
TEXT_SUFFIXES = {".md", ".py", ".json", ".sh", ".txt", ".yml", ".yaml", ".tmpl"}
OLD_VOCABULARY = (
    "Tri-Role",
    "Role 2.1 Human Architect",
    "Role 2.3 AI Programmer",
    "Role 2.2 AI Assistant",
)
CANONICAL_LABELS = (
    "Role 1.0 Human Architect",
    "Role 2.1 AI Architect & Reviewer",
    "Role 2.2 Orchestrator",
    "Role 2.3 Programmer",
)
QUOTA_STOP_PHRASE = "record a quota pending decision with the printed report and stop"
DISPATCH_FILES = (
    "skills/dev-lifecycle/SKILL.md",
    "skills/dev-lifecycle/references/orchestration-roles.md",
    "skills/dev-lifecycle/references/autonomous-mode.md",
    "skills/dev-lifecycle/references/governance-checklists.md",
    "skills/dev-lifecycle/references/handoff-template.md",
    "skills/dev-lifecycle/references/principal-review.md",
    "skills/dev-implementation/SKILL.md",
    "skills/subagent-driven-development/SKILL.md",
    "skills/cross-model-review/SKILL.md",
    "skills/principal-review/SKILL.md",
)
HAND_BUILT_ENV = re.compile(r"(?<![\w.])(?:HOME|AGY_PROFILE)=[\"'$/\w]")


def _read(rel_path: str) -> str:
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8")


def _tracked_governance_files() -> list[str]:
    proc = subprocess.run(
        ["git", "ls-files", "rules", "skills"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    tracked = [line for line in proc.stdout.splitlines() if line.strip()]
    on_disk = [
        path.relative_to(REPO_ROOT).as_posix()
        for root in ("rules", "skills")
        for path in (REPO_ROOT / root).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    merged = sorted(set(tracked) | set(on_disk))
    return [rel for rel in merged if Path(rel).suffix in TEXT_SUFFIXES]


def _mapping_section_lines(text: str) -> set[int]:
    """Return zero-based line indexes inside the Old-to-New Role Mapping section."""
    skipped: set[int] = set()
    inside = False
    for index, line in enumerate(text.splitlines()):
        if line.strip() == MAPPING_HEADING:
            inside = True
            skipped.add(index)
            continue
        if inside and re.match(r"^##\s", line):
            inside = False
        if inside:
            skipped.add(index)
    return skipped


def _section(text: str, heading_prefix: str) -> str:
    match = re.search(
        rf"^{re.escape(heading_prefix)}.*?(?=^## |\Z)",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )
    assert match is not None, f"Missing section {heading_prefix!r}"
    return match.group(0)


def test_fpg_ar_03_governance_text_uses_four_personas() -> None:
    """[FPG-AR-03] [Tier A - Unit] Governance text uses the four-persona model everywhere."""
    offenders: list[str] = []
    for rel in _tracked_governance_files():
        text = (REPO_ROOT / rel).read_text(encoding="utf-8", errors="ignore")
        skipped = _mapping_section_lines(text) if rel == ROLES_REL else set()
        for index, line in enumerate(text.splitlines()):
            if index in skipped:
                continue
            for token in OLD_VOCABULARY:
                if token in line:
                    offenders.append(f"{rel}:{index + 1}: {token}")
    assert not offenders, "Old Tri-Role vocabulary remains:\n" + "\n".join(offenders)

    rules = _read(RULES_REL)
    for label in CANONICAL_LABELS:
        assert label in rules, f"{RULES_REL} is missing {label!r}"

    roles = _read(ROLES_REL)
    mapping = _section(roles, MAPPING_HEADING)
    assert re.search(r"^\|.*\|\s*$", mapping, flags=re.MULTILINE), (
        "Mapping must be a table"
    )
    assert "fix-planner" in roles


def test_fpg_ar_03_critical_rules_section_8_carries_checkpoint_and_quota_text() -> None:
    """[FPG-AR-03] [Tier A - Unit] Rule 8 holds the persona table, session map, checkpoints and quota gate."""
    rules = _read(RULES_REL)
    assert rules.startswith("---\ntrigger: always_on\n---")
    for number in range(1, 11):
        assert re.search(rf"^## {number}\. ", rules, flags=re.MULTILINE), (
            f"Rule {number} missing"
        )
    rule_8 = _section(rules, "## 8. ")
    for token in (
        "ai_architect_reviewer",
        "orchestrator",
        "programmer",
        "dev-config",
        "--checkpoint",
        "gate2_tasks_locked",
        "subagent_returned",
        "wave_merged",
        "model_unavailable",
        "turn_budget",
        "low_quota_stop",
        "quota_low",
        "low-quota",
        "quota-check",
    ):
        assert token in rule_8, f"Rule 8 is missing {token!r}"
    assert "session map" in rule_8.lower()
    rule_5 = _section(rules, "## 5. ")
    rule_6 = _section(rules, "## 6. ")
    assert "Role 2.2" in rule_5 and "orchestrator" in rule_5
    assert "Role 2.1" in rule_6 and "Role 2.3" in rule_6
    assert "fix-planner" in rule_6
    assert "APPROVED" not in rule_6
    assert "Role 2.2 revisions" not in rules


@pytest.mark.parametrize(
    "rel",
    [
        "skills/dev-lifecycle/SKILL.md",
        "skills/dev-implementation/SKILL.md",
        "skills/subagent-driven-development/SKILL.md",
        "skills/cross-model-review/SKILL.md",
        "skills/principal-review/SKILL.md",
        "skills/resume-context/SKILL.md",
        "skills/save-context/SKILL.md",
        "skills/dev-lifecycle/references/orchestration-roles.md",
    ],
)
def test_fpg_ar_03_skills_name_new_personas_and_commands(rel: str) -> None:
    """[FPG-AR-03] [Tier A - Unit] Edited skills reference the new persona labels and role values."""
    text = _read(rel)
    assert re.search(r"Role 2\.[123]", text), f"{rel} names no four-persona role"
    assert "evaluate_programmer_fix_plan" not in text
    assert "plan-first" not in text or "fix-planner" in text
    if rel.endswith("resume-context/SKILL.md"):
        assert "architect|orchestrator|programmer" in text
    if rel.endswith("save-context/SKILL.md"):
        assert "--checkpoint" in text
    if rel.endswith(("principal-review/SKILL.md", "cross-model-review/SKILL.md")):
        assert "dev_config.py resolve" in text


def test_fpg_ar_07_governance_text_routes_dispatch_through_pool_and_guards_ag_run() -> (
    None
):
    """[FPG-AR-07] [Tier A - Unit] Governance text routes agy dispatch through the pool and keeps ag_run out of agent shells."""
    roles = _read(ROLES_REL)
    impl = _read("skills/dev-implementation/SKILL.md")
    rules = _read(RULES_REL)

    for name, text in (
        ("orchestration-roles.md", roles),
        ("dev-implementation/SKILL.md", impl),
    ):
        assert "dev_config.py dispatch" in text, (
            f"{name} must name dev_config.py dispatch"
        )
        assert "--persona programmer" in text
        assert "--mode write --prompt-file" in text
        assert QUOTA_STOP_PHRASE in text, f"{name} must state the exit code 2 rule"
        assert "agy_profile_leases.json" in text, f"{name} must name the lease file"
    assert "dev_config.py resolve" in roles
    assert "no automatic fallback, no retry" in roles
    assert "pool" in roles and "exhaust" in roles.lower()

    rule_9 = _section(rules, "## 9. ")
    assert "ag_run" in rule_9
    assert "<profile>-cli" in rule_9
    assert "zsh -ic" in rule_9
    assert "never from an agent runtime's own shell" in rule_9
    assert "deletes a profile's symlinks" in rule_9

    offenders = [
        f"{rel}:{index + 1}: {line.strip()}"
        for rel in DISPATCH_FILES
        for index, line in enumerate(_read(rel).splitlines())
        if HAND_BUILT_ENV.search(line)
    ]
    assert not offenders, (
        "Hand-built HOME or AGY_PROFILE in dispatch text:\n" + "\n".join(offenders)
    )
