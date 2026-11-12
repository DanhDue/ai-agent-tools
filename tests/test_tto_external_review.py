"""Unit and integration tests for Task 1: Diff-Only External Review & Transcript Isolation."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
REVIEW_PACKAGE_BIN = REPO_ROOT / "skills" / "subagent-driven-development" / "scripts" / "review-package"
EXT_PROMPT = REPO_ROOT / "skills" / "dev-implementation" / "references" / "external-review-prompt.md"
PR_PROMPT = REPO_ROOT / "skills" / "principal-review" / "references" / "principal-review-prompt.md"


def _load_external_review_module() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("run_external_review", SCRIPTS_DIR / "run_external_review.py")
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_external_review"] = mod
    spec.loader.exec_module(mod)
    return mod


rer: Any = _load_external_review_module()

FAKE_CLI_SCRIPT = """#!/bin/bash
set -euo pipefail
count=0
if [ -f "$FAKE_COUNT_FILE" ]; then
  count=$(cat "$FAKE_COUNT_FILE")
fi
count=$((count + 1))
echo "$count" > "$FAKE_COUNT_FILE"
cat > "${FAKE_PROMPT_DIR}/prompt_${count}.txt"
mode="${FAKE_MODE:-pass}"
if [ -n "${FAKE_MODE_FILE:-}" ] && [ -f "$FAKE_MODE_FILE" ]; then
  mode=$(sed -n "${count}p" "$FAKE_MODE_FILE" || echo "pass")
fi
case "$mode" in
  pass)
    echo "Verdict: PASS"
    ;;
  blocking)
    echo "Verdict: CHANGES REQUIRED"
    echo "[Important] src/core.py:8 — verify boundary"
    ;;
  noisy_pass)
    for i in $(seq 1 120); do
      echo "bulk analysis prose line ${i}"
    done
    echo "Verdict: PASS"
    for j in $(seq 1 40); do
      echo "noisy stderr warning ${j}" >&2
    done
    ;;
esac
"""


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _init_epic_repo(tmp_path: Path) -> tuple[Path, str, Path, Path]:
    repo = tmp_path / "repo"
    bin_dir = tmp_path / "bin"
    prompt_dir = tmp_path / "prompts"
    repo.mkdir()
    bin_dir.mkdir()
    prompt_dir.mkdir()

    for tool in ("git", "bash", "cat", "seq", "sed", "tr", "wc", "mktemp", "dirname", "rm"):
        found = shutil.which(tool)
        if found is not None:
            (bin_dir / tool).symlink_to(found)
    (bin_dir / "python3").symlink_to(sys.executable)

    for cli_name in ("codex", "claude"):
        cli_path = bin_dir / cli_name
        cli_path.write_text(FAKE_CLI_SCRIPT, encoding="utf-8")
        cli_path.chmod(0o755)

    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "tto@example.com")
    _git(repo, "config", "user.name", "TTO Test")

    (repo / "README.md").write_text("base\n", encoding="utf-8")
    core_lines = [f"line_{i:02d} = {i}" for i in range(1, 16)]
    (repo / "src").mkdir()
    (repo / "src" / "core.py").write_text("\n".join(core_lines) + "\n", encoding="utf-8")
    (repo / "src" / "round1_only.py").write_text("ROUND1_ONLY_MARKER = 'init'\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.vi.md").write_text("# Huong dan\n\nBan dau\n", encoding="utf-8")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Base commit")
    base_sha = _git(repo, "rev-parse", "HEAD")

    epic = repo / ".devtool" / "epic" / "demo"
    epic.mkdir(parents=True)
    hld = (
        "# Demo\n\n"
        "Integration test roots: scripts/\n\n"
        "Integration results: true -> build/demo.xml\n"
    )
    (epic / "demo.en.md").write_text(hld, encoding="utf-8")
    (epic / "demo.vi.md").write_text("# Demo VI\n\nNoi dung cu\n", encoding="utf-8")
    (epic / "2026-11-12-demo-design.en.md").write_text("# Spec EN\n", encoding="utf-8")
    (epic / "2026-11-12-demo-design.vi.md").write_text("# Spec VI\n", encoding="utf-8")
    (epic / "bdd_scenarios.en.md").write_text(
        "# Scenarios\n\n```gherkin\nScenario: [DEMO-HP-01] [Tier C - Integration] Demo\n  Given demo\n```\n",
        encoding="utf-8",
    )
    (epic / "bdd_scenarios.vi.md").write_text(
        "# Kich ban VI\n\n```gherkin\nScenario: [DEMO-HP-01] [Tier C - Integration] Demo VI\n  Given demo\n```\n",
        encoding="utf-8",
    )
    (epic / "task_1_demo.md").write_text(
        '---\nid: "task_1_demo"\nstatus: "done"\nepic: "demo"\n---\n\n# Task 1\n',
        encoding="utf-8",
    )
    (epic / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "test_demo.py").write_text("# [DEMO-HP-01]\ndef test_demo_hp_01() -> None: pass\n", encoding="utf-8")
    (repo / "build").mkdir()
    (repo / "build" / "demo.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<testsuites><testsuite name="demo" tests="1">'
        '<testcase name="test_demo_hp_01" classname="test_demo"/></testsuite></testsuites>\n',
        encoding="utf-8",
    )

    core_r1 = [f"line_{i:02d} = {i if i != 8 else 888}" for i in range(1, 16)]
    (repo / "src" / "core.py").write_text("\n".join(core_r1) + "\n", encoding="utf-8")
    (repo / "src" / "round1_only.py").write_text("ROUND1_ONLY_MARKER = 'round1'\n", encoding="utf-8")
    (repo / "docs" / "guide.vi.md").write_text("# Huong dan\n\nSua lan 1\n", encoding="utf-8")

    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Epic round 1")
    return repo, base_sha, bin_dir, prompt_dir


def test_tto_hp_01_diff_only_round1_and_round2(tmp_path: Path, monkeypatch: Any) -> None:
    """[TTO-HP-01] Diff-only external review uses -U5, excludes *.vi.md, and omits base...sha in Round 2."""
    repo, base_sha, bin_dir, prompt_dir = _init_epic_repo(tmp_path)
    count_file = tmp_path / "count.txt"
    mode_file = tmp_path / "modes.txt"
    mode_file.write_text("blocking\npass\npass\n", encoding="utf-8")

    # Artefact lists exclude all *.vi.md files
    pr_artefacts = rer.principal_artefact_lines(repo, "demo")
    code_artefacts = rer.artefact_lines(repo, "demo")
    for art_text in (pr_artefacts, code_artefacts):
        assert "demo.en.md" in art_text
        assert "bdd_scenarios.en.md" in art_text
        assert "task_1_demo.md" in art_text
        assert ".vi.md" not in art_text

    # review-package uses -U5 context (shows line_03 and line_13, omits line_01)
    pkg_out = tmp_path / "review.diff"
    subprocess.run(
        ["bash", str(REVIEW_PACKAGE_BIN), str(repo / ".devtool" / "epic" / "demo" / "task_1_demo.md"), base_sha, "HEAD", str(pkg_out)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    pkg_text = pkg_out.read_text(encoding="utf-8")
    assert "line_03 = 3" in pkg_text
    assert "line_13 = 13" in pkg_text
    assert "line_01 = 1" not in pkg_text

    # diff_range uses -U5 and excludes *.vi.md
    _log, adhoc_diff = rer.diff_range(repo, base_sha)
    assert "line_03 = 3" in adhoc_diff
    assert "line_13 = 13" in adhoc_diff
    assert "guide.vi.md" not in adhoc_diff

    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("FAKE_COUNT_FILE", str(count_file))
    monkeypatch.setenv("FAKE_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("FAKE_MODE_FILE", str(mode_file))
    monkeypatch.chdir(repo)

    # Round 1
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        code1 = rer.main(["run", "--epic-dir", "demo", "--base", base_sha, "--cli", "codex"])
    assert code1 == 1
    prompt1 = (prompt_dir / "prompt_1.txt").read_text(encoding="utf-8")
    assert "line_03 = 3" in prompt1
    assert "line_13 = 13" in prompt1
    assert "ROUND1_ONLY_MARKER = 'round1'" in prompt1
    assert ".vi.md" not in prompt1.split("## Artefacts", 1)[1]
    assert "Sua lan 1" not in prompt1

    # Record decision and make incremental fix commit (including a .vi.md edit inside & outside epic)
    results_path = repo / ".devtool" / "epic" / "demo" / "review_results.md"
    results_text = results_path.read_text(encoding="utf-8").replace(
        "| 1 | Important | src/core.py:8 | verify boundary |  |",
        "| 1 | Important | src/core.py:8 | verify boundary | fixed in 1234567 |",
    )
    results_path.write_text(results_text, encoding="utf-8")
    core_r2 = [f"line_{i:02d} = {i if i != 8 else 999}" for i in range(1, 16)]
    (repo / "src" / "core.py").write_text("\n".join(core_r2) + "\n", encoding="utf-8")
    (repo / "docs" / "guide.vi.md").write_text("# Huong dan\n\nSua lan 2\n", encoding="utf-8")
    (repo / ".devtool" / "epic" / "demo" / "demo.vi.md").write_text("# Demo VI\n\nNoi dung moi\n", encoding="utf-8")
    (repo / ".devtool" / "epic" / "demo" / "demo.en.md").write_text(
        "# Demo\n\nUpdated EN.\n\nIntegration test roots: scripts/\n\nIntegration results: true -> build/demo.xml\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Round 1 fix")
    r2_sha = _git(repo, "rev-parse", "HEAD")

    # Verify principal delta_round_context also excludes *.vi.md inside .devtool/epic/demo/
    pr_path = repo / ".devtool" / "epic" / "demo" / "principal_review.md"
    pr_path.write_text(
        "# Principal Review: demo\n\n"
        f"## Round 1\n\n- **SHA**: {base_sha}\n- **CLI**: codex\n- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n- **Kind**: principal\n- **Status**: completed\n- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n|---|---|---|---|---|\n"
        "| 1 | Important | demo.en.md:3 | clarify | fixed in 1234567 |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n",
        encoding="utf-8",
    )
    _git(repo, "add", str(pr_path))
    _git(repo, "commit", "-q", "-m", "Seed principal round 1")
    r2_sha = _git(repo, "rev-parse", "HEAD")
    pr_delta, _ = rer.delta_round_context(repo, rer.argparse.Namespace(epic_dir="demo", cli="codex", model=None, full=False), r2_sha, kind="principal")
    assert "Updated EN." in pr_delta
    assert ".vi.md" not in pr_delta
    assert "Noi dung moi" not in pr_delta

    # Round 2 (delta-only: omits full base...curr_sha diff block, emits 1-line cumulative stat reference)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        code2 = rer.main(["run", "--epic-dir", "demo", "--base", base_sha, "--cli", "codex"])
    assert code2 == 0
    prompt2 = (prompt_dir / "prompt_2.txt").read_text(encoding="utf-8")
    assert "Round Scope: Delta Review (Round 2)" in prompt2
    assert "line_03 = 3" in prompt2
    assert "line_13 = 13" in prompt2
    assert "git diff --stat" in prompt2
    assert "The complete source diff" not in prompt2
    assert "ROUND1_ONLY_MARKER" not in prompt2
    assert ".vi.md" not in prompt2.split("## Artefacts", 1)[1]
    assert "Sua lan 2" not in prompt2

    # Round 3 with --full explicitly includes full base...sha diff
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Record round 2")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        code3 = rer.main(["run", "--epic-dir", "demo", "--base", base_sha, "--cli", "codex", "--full"])
    assert code3 == 0
    prompt3 = (prompt_dir / "prompt_3.txt").read_text(encoding="utf-8")
    assert "The complete source diff" in prompt3
    assert "ROUND1_ONLY_MARKER = 'round1'" in prompt3


def test_tto_ec_01_over_budget_diff_stat_and_hunk_headers(tmp_path: Path) -> None:
    """[TTO-EC-01] Over-budget diffs fall back within budget retaining --stat, file headers, and @@ hunks."""
    repo = tmp_path / "big_repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "tto@example.com")
    _git(repo, "config", "user.name", "TTO Test")
    (repo / "src").mkdir()
    (repo / "src" / "alpha.py").write_text("def a():\n    return 0\n", encoding="utf-8")
    (repo / "src" / "beta.py").write_text("def b():\n    return 0\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Base")
    base_sha = _git(repo, "rev-parse", "HEAD")

    alpha_body = "\n".join(f"alpha_{i:04d} = '{'x' * 50}'" for i in range(900))
    beta_body = "\n".join(f"beta_{i:04d} = '{'y' * 50}'" for i in range(900))
    (repo / "src" / "alpha.py").write_text(f"def a():\n    return 1\n{alpha_body}\n", encoding="utf-8")
    (repo / "src" / "beta.py").write_text(f"def b():\n    return 2\n{beta_body}\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Large change")
    head_sha = _git(repo, "rev-parse", "HEAD")

    section = rer.build_diff_section(repo, base_sha, head_sha)
    assert len(section.encode("utf-8")) <= rer.MAX_DIFF_BYTES
    assert "Full file change summary" in section
    assert "src/alpha.py" in section
    assert "src/beta.py" in section
    assert "diff --git a/src/alpha.py b/src/alpha.py" in section
    assert "diff --git a/src/beta.py b/src/beta.py" in section
    assert "@@" in section
    assert "alpha_0800" not in section

    tight = rer.build_diff_section(repo, base_sha, head_sha, max_lines=10, max_bytes=2500)
    assert len(tight.encode("utf-8")) <= 2500
    assert "src/alpha.py" in tight
    assert "@@" in tight

    _log, range_section = rer.diff_range(repo, base_sha)
    assert len(range_section.encode("utf-8")) <= rer.MAX_DIFF_BYTES
    assert "diff --git a/src/alpha.py b/src/alpha.py" in range_section
    assert "@@" in range_section


def test_tto_st_01_load_review_config_migrates_legacy_and_preserves_custom(tmp_path: Path) -> None:
    """[TTO-ST-01] Default providers include assistant/programmer and legacy IDs upgrade in-memory only."""
    defaults = rer.DEFAULT_REVIEW_CONFIG["providers"]
    assert defaults["assistant"] == {"model": "claude-opus-5-5-high", "thinking_level": "high"}
    assert defaults["programmer"] == {"model": "gemini-4-hydrogen-xhigh", "thinking_level": "xhigh"}

    assert rer.upgrade_legacy_programmer_provider({"model": "gemini-3.8-flash", "thinking_level": "high"}) == (
        "gemini-4-hydrogen-xhigh",
        "xhigh",
    )
    assert rer.upgrade_legacy_programmer_provider({"model": "gemini-3.8-flash-high", "thinking_level": "high"}) == (
        "gemini-4-hydrogen-xhigh",
        "xhigh",
    )
    assert rer.upgrade_legacy_programmer_provider({"model": "claude-sonnet-4-6", "thinking_level": "medium"}) == (
        "claude-sonnet-4-6",
        "medium",
    )

    # Repo 1: git-tracked legacy programmer config stays untouched on disk, upgraded in memory
    repo1 = tmp_path / "repo_legacy"
    repo1.mkdir()
    _git(repo1, "init", "-q", "-b", "main")
    _git(repo1, "config", "user.email", "tto@example.com")
    _git(repo1, "config", "user.name", "TTO Test")
    legacy_payload = {
        "last_used_provider": "claude",
        "providers": {
            "programmer": {"model": "gemini-3.8-flash-high", "thinking_level": "high"},
        },
    }
    cfg_path1 = repo1 / ".devtool" / "review_config.json"
    cfg_path1.parent.mkdir(parents=True)
    raw_legacy = json.dumps(legacy_payload, indent=2) + "\n"
    cfg_path1.write_text(raw_legacy, encoding="utf-8")
    _git(repo1, "add", "-A")
    _git(repo1, "commit", "-q", "-m", "Track legacy config")

    loaded1 = rer.load_review_config(repo1)
    assert loaded1["providers"]["programmer"] == {"model": "gemini-4-hydrogen-xhigh", "thinking_level": "xhigh"}
    assert loaded1["providers"]["assistant"] == {"model": "claude-opus-5-5-high", "thinking_level": "high"}
    assert cfg_path1.read_text(encoding="utf-8") == raw_legacy
    assert _git(repo1, "status", "--porcelain") == ""

    # Repo 2: custom programmer model stays untouched in memory and on disk
    repo2 = tmp_path / "repo_custom"
    repo2.mkdir()
    _git(repo2, "init", "-q", "-b", "main")
    _git(repo2, "config", "user.email", "tto@example.com")
    _git(repo2, "config", "user.name", "TTO Test")
    custom_payload = {
        "last_used_provider": "claude",
        "providers": {
            "programmer": {"model": "claude-sonnet-4-6", "thinking_level": "medium"},
        },
    }
    cfg_path2 = repo2 / ".devtool" / "review_config.json"
    cfg_path2.parent.mkdir(parents=True)
    raw_custom = json.dumps(custom_payload, indent=2) + "\n"
    cfg_path2.write_text(raw_custom, encoding="utf-8")
    _git(repo2, "add", "-A")
    _git(repo2, "commit", "-q", "-m", "Track custom config")

    loaded2 = rer.load_review_config(repo2)
    assert loaded2["providers"]["programmer"] == {"model": "claude-sonnet-4-6", "thinking_level": "medium"}
    assert cfg_path2.read_text(encoding="utf-8") == raw_custom

    # Untracked config missing default providers seeds defaults to disk
    repo3 = tmp_path / "repo_untracked"
    repo3.mkdir()
    _git(repo3, "init", "-q", "-b", "main")
    cfg_path3 = repo3 / ".devtool" / "review_config.json"
    cfg_path3.parent.mkdir(parents=True)
    cfg_path3.write_text(json.dumps({"providers": {"claude": {"model": "Opus 5.5"}}}) + "\n", encoding="utf-8")
    rer.load_review_config(repo3)
    persisted3 = json.loads(cfg_path3.read_text(encoding="utf-8"))
    assert persisted3["providers"]["programmer"]["model"] == "gemini-4-hydrogen-xhigh"
    assert persisted3["providers"]["assistant"]["model"] == "claude-opus-5-5-high"


def test_tto_fr_01_quiet_facts_and_raw_log_offloading(tmp_path: Path, monkeypatch: Any) -> None:
    """[TTO-FR-01] Passing facts collapse to 1 line; failing facts cap at 25 lines; raw output offloads to build/reviews."""
    passing_stdout = "\n".join(f"ok_line_{i}" for i in range(180))
    assert rer.fact("audit_epic.py", 0, passing_stdout, "") == "PASS: audit_epic.py\n"

    failing_stderr = "\n".join(["", *[f"err_line_{i:02d}" for i in range(90)], ""])
    fail_fact = rer.fact("pytest_check", 1, "", failing_stderr)
    fail_lines = fail_fact.strip().splitlines()
    assert fail_lines[0] == "$ pytest_check"
    assert fail_lines[1] == "exit 1"
    body_lines = fail_lines[2:]
    assert len(body_lines) == 25
    assert body_lines[0] == "err_line_65"
    assert body_lines[-1] == "err_line_89"

    # Full run offloading bulk prose & stderr into build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log
    repo, base_sha, bin_dir, prompt_dir = _init_epic_repo(tmp_path)
    head_sha = _git(repo, "rev-parse", "HEAD")
    sha7 = head_sha[:7]
    count_file = tmp_path / "count.txt"

    monkeypatch.setenv("PATH", str(bin_dir))
    monkeypatch.setenv("FAKE_COUNT_FILE", str(count_file))
    monkeypatch.setenv("FAKE_PROMPT_DIR", str(prompt_dir))
    monkeypatch.setenv("FAKE_MODE", "noisy_pass")
    monkeypatch.chdir(repo)

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        code_res = rer.main(["run", "--epic-dir", "demo", "--base", base_sha, "--cli", "codex"])
    assert code_res == 0

    code_raw_rel = f"build/reviews/demo_code_round1_{sha7}.raw.log"
    code_raw_path = repo / code_raw_rel
    assert code_raw_path.is_file()
    raw_content = code_raw_path.read_text(encoding="utf-8")
    assert "bulk analysis prose line 120" in raw_content
    assert "noisy stderr warning 40" in raw_content

    rev_md = (repo / ".devtool" / "epic" / "demo" / "review_results.md").read_text(encoding="utf-8")
    assert code_raw_rel in rev_md
    assert "bulk analysis prose line 1" not in rev_md
    assert "noisy stderr warning 1" not in rev_md
    rounds = rer.rounds_in(rev_md)
    assert len(rounds) == 1
    assert rer.round_passes(rer.round_output(rounds[0][1])) == [("review", "PASS", "—")]

    # Verify --kind principal writes a distinct raw log using a valid ready epic
    import importlib

    tcer: Any = importlib.import_module("test_check_epic_readiness")

    pr_repo = tmp_path / "pr_repo"
    pr_repo.mkdir()
    _git(pr_repo, "init", "-q", "-b", "main")
    _git(pr_repo, "config", "user.email", "tto@example.com")
    _git(pr_repo, "config", "user.name", "TTO Test")
    (pr_repo / "README.md").write_text("# Root\n", encoding="utf-8")
    _git(pr_repo, "add", "-A")
    _git(pr_repo, "commit", "-q", "-m", "Base commit")
    pr_base_sha = _git(pr_repo, "rev-parse", "HEAD")
    tcer.build_ready_epic(pr_repo)
    _git(pr_repo, "add", "-A")
    _git(pr_repo, "commit", "-q", "-m", "Ready epic")
    pr_sha7 = _git(pr_repo, "rev-parse", "HEAD")[:7]
    monkeypatch.chdir(pr_repo)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        pr_res = rer.main(["run", "--kind", "principal", "--epic-dir", "demo_epic", "--base", pr_base_sha, "--cli", "codex"])
    assert pr_res == 0
    pr_raw_rel = f"build/reviews/demo_epic_principal_round1_{pr_sha7}.raw.log"
    assert (pr_repo / pr_raw_rel).is_file()
    rer.render_round(1, {"SHA": head_sha}, [], "Verdict: PASS\n", root=repo, epic_dir="demo", kind="principal", sha=head_sha)
    assert (repo / f"build/reviews/demo_principal_round1_{sha7}.raw.log").is_file()
    assert code_raw_path.is_file()

    # Multi-pass ollama-style output preserves Pass header, Verdict, and first --- error --- line
    multipass_raw = (
        "### Pass 1: architecture\n\nDetailed prose 1\nDetailed prose 2\nVerdict: PASS\n\n"
        "### Pass 2: security\n\nMore prose\n--- error ---\ntimed out after 60s\nstack line 2\n"
    )
    rendered = rer.render_round(
        1,
        {"SHA": "abc1234", "Status": "no verdict", "Verdict": "none"},
        [],
        multipass_raw,
        root=repo,
        epic_dir="demo",
        kind="code",
        sha="abc1234",
    )
    parsed_rounds = rer.rounds_in(f"# Review\n\n{rendered}")
    assert rer.round_passes(rer.round_output(parsed_rounds[0][1])) == [
        ("1 architecture", "PASS", "—"),
        ("2 security", "none", "timed out after 60s"),
    ]
    assert "Detailed prose 1" not in rendered
    assert "stack line 2" not in rendered

    # Prompt templates explicitly enforce Diff-Only (-U5), Zero-Fluff, and English SSOT
    for prompt_file in (EXT_PROMPT, PR_PROMPT):
        text = prompt_file.read_text(encoding="utf-8")
        assert "-U5" in text or "Diff-Only" in text
        assert "Zero-Fluff" in text
        assert ".en.md" in text and ".vi.md" in text


class TestTTOExternalReview_Integration:
    """Integration provenance wrapper for Tier C scenarios in Task 1."""

    def test_tto_hp_01_integration(self, tmp_path: Path, monkeypatch: Any) -> None:
        test_tto_hp_01_diff_only_round1_and_round2(tmp_path, monkeypatch)

    def test_tto_fr_01_integration(self, tmp_path: Path, monkeypatch: Any) -> None:
        test_tto_fr_01_quiet_facts_and_raw_log_offloading(tmp_path, monkeypatch)
