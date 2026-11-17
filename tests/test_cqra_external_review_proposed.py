"""Unit tests for review prompt `. Proposed:` alignment and triage pre-fill (Task 03)."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest  # type: ignore[import-not-found]

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_PROMPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "references"
    / "external-review-prompt.md"
)
LOCAL_PROMPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "references"
    / "local-review-prompt.md"
)
PRINCIPAL_PROMPT = (
    REPO_ROOT
    / "skills"
    / "principal-review"
    / "references"
    / "principal-review-prompt.md"
)
REVIEW_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "run_external_review.py"
)
REQUIRED_FINDING_LINE = (
    "[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>"
)
LEGACY_FINDING_LINE = "[Critical|Important|Minor] <artefact>:<location> — <problem>"


@pytest.fixture(scope="module")
def review_mod() -> ModuleType:
    """Load real run_external_review production module once per module."""
    spec = importlib.util.spec_from_file_location("run_external_review", REVIEW_SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def prompt_texts() -> dict[str, str]:
    """Read external, local, and principal review prompt templates once per module."""
    return {
        "external": EXTERNAL_PROMPT.read_text(encoding="utf-8"),
        "local": LOCAL_PROMPT.read_text(encoding="utf-8"),
        "principal": PRINCIPAL_PROMPT.read_text(encoding="utf-8"),
    }


def _init_git_repo(workspace: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    return workspace


def _section_row_lines(markdown_text: str, heading: str) -> list[str]:
    lines = markdown_text.splitlines()
    assert heading in lines, f"Missing heading {heading!r}"
    start = lines.index(heading) + 1
    rows: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.startswith("|") and not line.startswith(
            ("| # |", "| Rank |", "|---")
        ):
            rows.append(line)
    return rows


def test_cqra_hp_04_prompts_and_triage_prefill(
    review_mod: ModuleType,
    prompt_texts: dict[str, str],
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    """[CQRA-HP-04] Prompts require `. Proposed: <edit>`, 5-col check() passes, and triage pre-fills proposals."""
    assert len(prompt_texts) == 3
    assert REQUIRED_FINDING_LINE in prompt_texts["principal"].splitlines()
    assert REQUIRED_FINDING_LINE in prompt_texts["external"].splitlines()
    assert REQUIRED_FINDING_LINE in prompt_texts["local"].splitlines()
    assert LEGACY_FINDING_LINE not in prompt_texts["external"].splitlines()
    assert LEGACY_FINDING_LINE not in prompt_texts["local"].splitlines()

    repo = _init_git_repo(tmp_path)
    monkeypatch.chdir(repo)

    raw_output = (
        "Verdict: CHANGES REQUIRED\n"
        "- [Important] scripts/app.py:42 — Stale cache key omits round id. "
        "Proposed: include round_num in cache key\n"
    )
    findings = review_mod.parse_findings(raw_output, verdict="CHANGES REQUIRED")
    assert findings == [
        (
            "Important",
            "scripts/app.py:42",
            "Stale cache key omits round id. Proposed: include round_num in cache key",
        )
    ]

    meta = {
        "SHA": "a1b2c3d4e5f6",
        "CLI": "claude",
        "Model": "Opus 5.5",
        "Thinking": "high",
        "Status": "completed",
        "Verdict": "CHANGES REQUIRED",
    }
    rendered = review_mod.render_round(
        1,
        meta,
        findings,
        raw_output,
        root=repo,
        epic_dir="cqra_hp04",
        sha="a1b2c3d4e5f6",
    )
    epic_dir = repo / ".devtool" / "epic" / "cqra_hp04"
    epic_dir.mkdir(parents=True, exist_ok=True)
    review_path = epic_dir / "review_results.md"
    review_path.write_text(rendered, encoding="utf-8")

    rounds = review_mod.rounds_in(review_path.read_text(encoding="utf-8"))
    assert len(rounds) == 1
    table_rows = review_mod.table_findings(rounds[0][1])
    assert len(table_rows) == 1
    for _raw_line, cells in table_rows:
        assert len(cells) == 5
    assert (
        table_rows[0][1][3]
        == "Stale cache key omits round id. Proposed: include round_num in cache key"
    )

    latest = review_mod.finding_rows(rounds[0][1])
    assert len(latest) == 1
    top_md = "\n".join(review_mod.top_risk_findings_section(latest, limit=3))
    top_rows = [
        review_mod.split_row(ln)
        for ln in _section_row_lines(
            top_md, "## Top 3 Highest-Risk Findings (Executive Report)"
        )
    ]
    assert len(top_rows) == 1
    assert len(top_rows[0]) == 7
    assert top_rows[0][4] == "Stale cache key omits round id"
    assert top_rows[0][6] == "include round_num in cache key"

    args = argparse.Namespace(epic_dir="cqra_hp04", kind="code", max_rounds=3)
    assert review_mod.triage(args) == 0
    triage_stdout = capsys.readouterr().out
    assert not (epic_dir / "fix_plan_round1.md").exists()

    triage_rows = [
        review_mod.split_row(ln)
        for ln in _section_row_lines(triage_stdout, "## Findings")
    ]
    assert len(triage_rows) == 1
    assert len(triage_rows[0]) == 7
    assert triage_rows[0][3] == "Stale cache key omits round id"
    assert triage_rows[0][6] == "include round_num in cache key"

    triage_top_rows = [
        review_mod.split_row(ln)
        for ln in _section_row_lines(
            triage_stdout, "## Top 3 Highest-Risk Findings (Executive Report)"
        )
    ]
    assert len(triage_top_rows) == 1
    assert triage_top_rows[0][6] == "include round_num in cache key"

    assert review_mod.check(args) == 1
    undecided_out = capsys.readouterr().out
    assert "unreadable findings row" not in undecided_out

    decided_text = rendered.replace(" |  |\n", " | fixed in 9876543 |\n")
    review_path.write_text(decided_text, encoding="utf-8")
    decided_rows = review_mod.table_findings(review_mod.rounds_in(decided_text)[0][1])
    assert len(decided_rows) == 1 and len(decided_rows[0][1]) == 5
    assert review_mod.check(args) == 0


def test_cqra_ec_04_triage_question_mark_fallback(
    review_mod: ModuleType,
    tmp_path: Path,
    monkeypatch: Any,
    capsys: Any,
) -> None:
    """[CQRA-EC-04] Triage pre-fills Proposed action when present and emits `?` only when omitted."""
    repo = _init_git_repo(tmp_path)
    monkeypatch.chdir(repo)

    raw_output = (
        "Verdict: CHANGES REQUIRED\n"
        "- [Important] scripts/agy_quota.py:88 — Negative fraction breaks width. "
        "Proposed: clamp negative fraction\n"
        "- [Minor] scripts/agy_quota.py:120 — Unused local alias in helper\n"
    )
    findings = review_mod.parse_findings(raw_output, verdict="CHANGES REQUIRED")
    assert len(findings) == 2

    meta = {
        "SHA": "112233445566",
        "CLI": "codex",
        "Model": "gpt-6.1-sol",
        "Thinking": "high",
        "Status": "completed",
        "Verdict": "CHANGES REQUIRED",
    }
    rendered = review_mod.render_round(
        1,
        meta,
        findings,
        raw_output,
        root=repo,
        epic_dir="cqra_ec04",
        sha="112233445566",
    )
    epic_dir = repo / ".devtool" / "epic" / "cqra_ec04"
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "review_results.md").write_text(rendered, encoding="utf-8")

    args = argparse.Namespace(epic_dir="cqra_ec04", kind="code", max_rounds=3)
    assert review_mod.triage(args) == 0
    triage_stdout = capsys.readouterr().out
    assert not (epic_dir / "fix_plan_round1.md").exists()

    finding_rows = [
        review_mod.split_row(ln)
        for ln in _section_row_lines(triage_stdout, "## Findings")
    ]
    assert len(finding_rows) == 2
    by_num = {row[0]: row for row in finding_rows}
    assert by_num["1"][3] == "Negative fraction breaks width"
    assert by_num["1"][6] == "clamp negative fraction"
    assert by_num["2"][3] == "Unused local alias in helper"
    assert by_num["2"][6] == "?"

    top_rows = [
        review_mod.split_row(ln)
        for ln in _section_row_lines(
            triage_stdout, "## Top 3 Highest-Risk Findings (Executive Report)"
        )
    ]
    assert len(top_rows) == 2
    top_by_num = {row[1]: row for row in top_rows}
    assert top_by_num["1"][6] == "clamp negative fraction"
    assert top_by_num["2"][6] == "?"


@pytest.mark.parametrize(
    ("raw_problem", "expected_problem", "expected_action"),
    [
        (
            "Stale cache key omits round id. Proposed: include round_num in cache key",
            "Stale cache key omits round id",
            "include round_num in cache key",
        ),
        (
            "Repeated stat calls; Suggestion: cache mtime per round file",
            "Repeated stat calls",
            "cache mtime per round file",
        ),
        (
            "Null pointer risk — Fix: guard None before strip",
            "Null pointer risk",
            "guard None before strip",
        ),
        (
            "Missing timeout. proposed action: pass timeout=30",
            "Missing timeout",
            "pass timeout=30",
        ),
        (
            "Thiếu kiểm tra rỗng. Đề xuất: thêm điều kiện if not items",
            "Thiếu kiểm tra rỗng",
            "thêm điều kiện if not items",
        ),
        (
            "Docstring mentions `Proposed: example` inline without real suffix",
            "Docstring mentions `Proposed: example` inline without real suffix",
            "",
        ),
        (
            "Regex fails on `Fix: inner` token. Proposed: mask backtick spans first",
            "Regex fails on `Fix: inner` token",
            "mask backtick spans first",
        ),
        (
            "Old note. Fix: first draft; Proposed: final surgical edit",
            "Old note. Fix: first draft",
            "final surgical edit",
        ),
        (
            "Flag edge case: null id; Unproposed: keep as-is",
            "Flag edge case: null id; Unproposed: keep as-is",
            "",
        ),
        (
            "Dangling marker. Proposed:   ",
            "Dangling marker. Proposed:",
            "",
        ),
    ],
)
def test_cqra_ec_04_extract_proposed_action_variants(
    review_mod: ModuleType,
    raw_problem: str,
    expected_problem: str,
    expected_action: str,
) -> None:
    """[CQRA-EC-04] _extract_proposed_action masks backtick spans and takes the last valid marker."""
    problem_text, proposed_action = review_mod._extract_proposed_action(raw_problem)
    assert problem_text == expected_problem
    assert proposed_action == expected_action
