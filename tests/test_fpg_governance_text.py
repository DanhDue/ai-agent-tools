"""Governance text contract tests for the four-persona model.

Covers BDD Scenarios:
- FPG-AR-03: Governance text uses the four-persona model everywhere
- FPG-AR-07: Governance text routes agy dispatch through the pool and keeps ag_run out of agent shells
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import re
import shlex
import subprocess
import sys

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
    scanned_files = _tracked_governance_files()
    assert len(scanned_files) > 0, "Expected governance files to scan"
    offenders: list[str] = []
    for rel in scanned_files:
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


class _CapturedParser(Exception):
    """Sentinel raised from patched parse_args to capture the live ArgumentParser."""

    def __init__(self, parser: argparse.ArgumentParser) -> None:
        super().__init__("captured parser")
        self.parser = parser


def _load_external_review_parser() -> argparse.ArgumentParser:
    """Load run_external_review.py by path and return its live ArgumentParser."""
    scripts_dir = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
    script_path = scripts_dir / "run_external_review.py"
    added_sys_path = False
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
        added_sys_path = True
    mod_name = "_fpg_run_external_review_probe"
    spec = importlib.util.spec_from_file_location(mod_name, script_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    orig_parse_args = argparse.ArgumentParser.parse_args

    def _capture(
        self: argparse.ArgumentParser, *args: object, **kwargs: object
    ) -> object:
        raise _CapturedParser(self)

    try:
        spec.loader.exec_module(mod)
        argparse.ArgumentParser.parse_args = _capture  # type: ignore[method-assign]
        try:
            mod.main([])
        except _CapturedParser as captured:
            return captured.parser
    finally:
        argparse.ArgumentParser.parse_args = orig_parse_args  # type: ignore[method-assign]
        sys.modules.pop(mod_name, None)
        if added_sys_path and str(scripts_dir) in sys.path:
            sys.path.remove(str(scripts_dir))
    raise AssertionError("run_external_review.main() did not invoke parse_args")


def _extract_external_review_commands(text: str) -> list[tuple[int, str, str]]:
    """Extract inline run_external_review.py <sub> ... commands with 1-based line numbers."""
    results: list[tuple[int, str, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in re.finditer(r"`(run_external_review\.py\s+(\S+)[^`\n]*)`", line):
            results.append((line_no, match.group(2), match.group(1)))
    return results


def _strip_optional_brackets(command: str) -> str:
    """Remove bracketed optional synopsis groups from innermost to outermost."""
    stripped = command
    while True:
        updated = re.sub(r"\[[^\[\]]*\]", "", stripped)
        if updated == stripped:
            return updated
        stripped = updated


def _unwrap_continuations(lines: list[str]) -> list[tuple[int, str]]:
    """Join trailing-backslash line continuations, preserving 1-based start offsets."""
    joined: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        start_offset = index + 1
        buf = lines[index]
        while buf.rstrip().endswith("\\") and index + 1 < len(lines):
            buf = buf.rstrip()[:-1].rstrip() + " " + lines[index + 1].lstrip()
            index += 1
        joined.append((start_offset, buf))
        index += 1
    return joined


def _collect_run_option_commands(
    line_no: int, text: str, pattern: str
) -> list[tuple[int, str]]:
    """Return (line_no, cmd) entries for `run_external_review.py run` snippets that show options."""
    hits: list[tuple[int, str]] = []
    for match in re.finditer(pattern, text):
        cmd = match.group(1).strip()
        tokens = shlex.split(cmd)
        if any(tok.lstrip("[").startswith("-") for tok in tokens[2:]):
            hits.append((line_no, cmd))
    return hits


def _extract_quoted_run_commands_with_options(text: str) -> list[tuple[int, str]]:
    """Extract quoted `run_external_review.py run` commands that show at least one option."""
    results: list[tuple[int, str]] = []
    in_fence = False
    fence_lines: list[str] = []
    fence_start = 1
    outside_lines: list[tuple[int, str]] = []
    run_pat = r"(?:^|(?<=[\s/`\"'$(]))(run_external_review\.py\s+run\b[^\n`]*)"

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if raw_line.lstrip(" >").startswith("```"):
            if not in_fence:
                in_fence = True
                fence_start = line_no + 1
                fence_lines = []
            else:
                in_fence = False
                for offset, joined_line in _unwrap_continuations(fence_lines):
                    results.extend(
                        _collect_run_option_commands(
                            fence_start + offset - 1, joined_line, run_pat
                        )
                    )
            continue
        if in_fence:
            fence_lines.append(raw_line)
        else:
            outside_lines.append((line_no, raw_line))

    for line_no, raw_line in outside_lines:
        for span in re.finditer(r"`([^`\n]+)`", raw_line):
            results.extend(
                _collect_run_option_commands(line_no, span.group(1), run_pat)
            )
    return results


def _external_review_scan_targets() -> list[Path]:
    """Return skills SKILL.md, skills references/*.md, and English docs/architecture/* files."""
    return [
        *sorted((REPO_ROOT / "skills").glob("*/SKILL.md")),
        *sorted((REPO_ROOT / "skills").glob("*/references/*.md")),
        *sorted(
            path
            for path in (REPO_ROOT / "docs" / "architecture").glob("*")
            if path.is_file()
            and not path.name.endswith(".vi.md")
            and path.suffix in TEXT_SUFFIXES
        ),
    ]


def _all_external_review_command_cases() -> list[tuple[str, str, str]]:
    """Collect (source_label, subcommand, command) cases from rules, skills, and docs/architecture."""
    cases = [
        (f"{RULES_REL}:{line_no}", subcommand, command)
        for line_no, subcommand, command in _extract_external_review_commands(
            _read(RULES_REL)
        )
    ]
    for path in _external_review_scan_targets():
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for line_no, command in _extract_quoted_run_commands_with_options(text):
            cases.append((f"{rel}:{line_no}", "run", command))
    return cases


_EXTERNAL_REVIEW_COMMAND_CASES = _all_external_review_command_cases()


def _required_subparser_option_groups(
    parser: argparse.ArgumentParser, subcommand: str
) -> list[tuple[str, ...]]:
    """Return required option-string tuples from the real subparser for subcommand."""
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparser = action.choices[subcommand]
            return [
                tuple(sub_action.option_strings)
                for sub_action in subparser._actions
                if sub_action.required and sub_action.option_strings
            ]
    raise AssertionError(f"No subparsers found on {parser!r}")


@pytest.fixture(scope="module")
def external_review_parser() -> argparse.ArgumentParser:
    """Module-scoped live ArgumentParser loaded from run_external_review.py."""
    return _load_external_review_parser()


def test_external_review_command_scanner_coverage() -> None:
    """Scanner covers CRITICAL_RULES, skills, and docs/architecture while ignoring bare mentions."""
    rules_subs = {
        sub for _, sub, _ in _extract_external_review_commands(_read(RULES_REL))
    }
    assert {"run", "triage"} <= rules_subs

    scanned = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in _external_review_scan_targets()
    }
    assert {
        "skills/dev-implementation/SKILL.md",
        "skills/principal-review/SKILL.md",
        "skills/cross-model-review/SKILL.md",
        "skills/dev-lifecycle/references/principal-review.md",
        "docs/architecture/resume_context.py",
    } <= scanned
    assert not any(rel.endswith(".vi.md") for rel in scanned)

    assert (
        _extract_quoted_run_commands_with_options(
            "Run `run_external_review.py run` and `triage`."
        )
        == []
    )
    assert _extract_quoted_run_commands_with_options(
        "Runs `run_external_review.py run --kind principal` synchronously."
    ) == [(1, "run_external_review.py run --kind principal")]


@pytest.mark.parametrize(
    ("source_label", "subcommand", "command"),
    _EXTERNAL_REVIEW_COMMAND_CASES,
    ids=[f"{src}:{sub}" for src, sub, _ in _EXTERNAL_REVIEW_COMMAND_CASES],
)
def test_critical_rules_external_review_commands_include_required_options(
    external_review_parser: argparse.ArgumentParser,
    source_label: str,
    subcommand: str,
    command: str,
) -> None:
    """Quoted run_external_review.py commands in rules, skills, and docs/architecture include required options."""
    tokens = shlex.split(_strip_optional_brackets(command))[1:]
    required_groups = _required_subparser_option_groups(
        external_review_parser, subcommand
    )
    missing = [
        "/".join(group)
        for group in required_groups
        if not any(
            opt in tokens or any(tok.startswith(f"{opt}=") for tok in tokens)
            for opt in group
        )
    ]
    assert not missing, (
        f"{source_label} command {command!r} is missing required option(s) {missing} "
        f"for subcommand {subcommand!r}"
    )
    parsed = external_review_parser.parse_args(tokens)
    assert parsed.mode == subcommand


DEV_IMPL_MANDATORY_POINTERS: tuple[tuple[str, str], ...] = (
    (
        "references/entry-point-and-resume.md",
        r"MANDATORY:\s*read\s+\[[^\]]+\]\(references/entry-point-and-resume\.md(?:#[^)]+)?\)\s+before\s+Phase\s+1",
    ),
    (
        "references/worker-execution-rules.md",
        r"MANDATORY:\s*read\s+\[[^\]]+\]\(references/worker-execution-rules\.md\)\s+before\s+(?:dispatching|acting)",
    ),
    (
        "references/gate4-semantic-integrity.md",
        r"MANDATORY:\s*read\s+\[[^\]]+\]\(references/gate4-semantic-integrity\.md\)\s+before\s+running\b",
    ),
)


def _missing_mandatory_dev_impl_pointers(text: str) -> list[str]:
    """Return reference paths lacking a matching MANDATORY: read ... before ... pointer."""
    return [
        ref_path
        for ref_path, pattern in DEV_IMPL_MANDATORY_POINTERS
        if not re.search(pattern, text)
    ]


@pytest.mark.parametrize(
    ("ref_path", "pattern"),
    DEV_IMPL_MANDATORY_POINTERS,
    ids=[ref for ref, _ in DEV_IMPL_MANDATORY_POINTERS],
)
def test_dev_implementation_marks_reference_pointers_mandatory(
    ref_path: str,
    pattern: str,
) -> None:
    """dev-implementation/SKILL.md links all three references with MANDATORY: read ... before ... pointers."""
    text = _read("skills/dev-implementation/SKILL.md")
    assert f"({ref_path})" in text, (
        f"dev-implementation/SKILL.md does not link {ref_path}"
    )
    assert ref_path not in _missing_mandatory_dev_impl_pointers(text), (
        f"dev-implementation/SKILL.md does not mark {ref_path} as MANDATORY before its step"
    )
    # Verify check fails if the pointer is dropped from a copy of SKILL.md.
    stripped = re.sub(pattern, "", text)
    assert ref_path in _missing_mandatory_dev_impl_pointers(stripped)


def test_dev_implementation_worker_rules_pointer_at_phase2_step1() -> None:
    """Worker execution rules pointer appears in Phase 2 step 1 before task-implementer dispatch."""
    text = _read("skills/dev-implementation/SKILL.md")
    phase2 = text.split("### Phase 2", 1)[1].split("### Phase 3", 1)[0]
    step1 = phase2.split("1. **Wave Setup (Orchestrator)**", 1)[1].split(
        "2. **`task-implementer`", 1
    )[0]
    assert "references/worker-execution-rules.md" in step1
    assert "MANDATORY: read [references/worker-execution-rules.md]" in step1
    assert step1.index("references/worker-execution-rules.md") < step1.index(
        "dispatch the slot's `task-implementer`"
    )


def test_window_title_rule_template_matches_english_only_rule() -> None:
    """templates/.agents/rules/window_title_sync.md stays in sync with .agents/rules/window_title_sync.md."""
    live = _read(".agents/rules/window_title_sync.md").rstrip("\n")
    template = _read("templates/.agents/rules/window_title_sync.md").rstrip("\n")
    assert template == live, (
        "templates/.agents/rules/window_title_sync.md drifted from .agents/rules/window_title_sync.md"
    )
    assert "<Tên Epic Tiếng Việt>" not in template
    assert "<Epic Name>" in template
    assert "No `.vi.md` file is read" in template


def test_fpg_fix_planner_contract_matches_se04() -> None:
    """[SE-04] fix-planner is read-only and returns plan_markdown; Orchestrator writes fix_plan_round<N>.md."""
    roles = _read(ROLES_REL)
    summary_section = _section(roles, "## 3. Summary Contracts")
    planner_rows = [
        line
        for line in summary_section.splitlines()
        if line.lstrip().startswith("| `fix-planner`")
    ]
    assert len(planner_rows) == 1, (
        f"Expected one fix-planner summary row, got {planner_rows!r}"
    )
    planner_row = planner_rows[0]
    for required_key in ("`round`", "`status`", "`halt_criteria`", "`plan_markdown`"):
        assert required_key in planner_row, (
            f"fix-planner summary row missing {required_key!r}: {planner_row}"
        )
    for forbidden_key in ("plan_path", "decision_sha"):
        assert forbidden_key not in planner_row, (
            f"fix-planner summary row must not require {forbidden_key!r}: {planner_row}"
        )

    for rel in (
        ROLES_REL,
        "skills/cross-model-review/SKILL.md",
        RULES_REL,
        "skills/dev-lifecycle/SKILL.md",
        "skills/dev-lifecycle/references/governance-checklists.md",
        "skills/dev-lifecycle/references/autonomous-mode.md",
        "skills/subagent-driven-development/SKILL.md",
    ):
        text = _read(rel)
        for stale_phrase in (
            "writes only `fix_plan_round<N>.md`",
            "may write only `fix_plan_round<N>.md`",
            "`fix-planner` writes `fix_plan_round<N>.md`",
            "`fix-planner` writing `fix_plan_round<N>.md`",
            "`fix-planner` (read-only) writes `fix_plan_round<N>.md`",
            "that writes `fix_plan_round<N>.md`",
            "`fix-planner` writes the plan",
            "Writes `fix_plan_round<N>.md` for high-risk findings",
        ):
            assert stale_phrase not in text, (
                f"{rel} still uses pre-SE-04 wording {stale_phrase!r}"
            )
    assert "plan_markdown" in roles
    assert "plan_markdown" in _read("skills/cross-model-review/SKILL.md")
    boundaries_section = _section(roles, "## 1. Boundaries")
    role_21_rows = [
        line
        for line in boundaries_section.splitlines()
        if line.lstrip().startswith("| **Role 2.1")
    ]
    assert len(role_21_rows) == 1
    assert "fix_plan_round" not in role_21_rows[0]


@pytest.mark.parametrize(
    "rel",
    [
        ROLES_REL,
        "skills/cross-model-review/SKILL.md",
    ],
)
def test_fpg_low_risk_clause_excludes_critical(rel: str) -> None:
    """Low-risk routing clause allows only Important or Minor and keeps Critical in High risk."""
    text = _read(rel)
    assert "**Low risk**" in text and "**High risk**" in text
    after_low = text.split("**Low risk**", 1)[1]
    low_clause, high_rest = after_low.split("**High risk**", 1)
    high_clause = high_rest.split("\n\n", 1)[0]
    expected_phrase = (
        "severity `Important` or `Minor` (a `Critical` finding is always high risk)"
    )
    stripped_low = low_clause.replace("(a `Critical` finding is always high risk)", "")
    assert "`Critical`" not in stripped_low, (
        f"{rel} lists Critical inside the Low risk clause: {low_clause!r}"
    )
    assert expected_phrase in low_clause, (
        f"{rel} missing canonical low-risk severity phrase: {low_clause!r}"
    )
    assert "any `Critical`" in high_clause, (
        f"{rel} missing 'any `Critical`' in High risk clause: {high_clause!r}"
    )
