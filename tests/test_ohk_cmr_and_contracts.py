"""Tier C integration tests for Task 05: CMR deferred epic-doc minors, smoke checklist target inference, and sync_contracts --allow-dirty."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
RUN_EXTERNAL_REVIEW_SCRIPT = DEV_IMPL_SCRIPTS / "run_external_review.py"
GENERATE_SMOKE_SCRIPT = DEV_IMPL_SCRIPTS / "generate_smoke_checklist.py"
EXTERNAL_REVIEW_PROMPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "references"
    / "external-review-prompt.md"
)
SYNC_CONTRACTS_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "sync-shared-contracts"
    / "resources"
    / "scripts"
    / "sync_contracts.py"
)


def _load_module(name: str, path: Path) -> ModuleType:
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _init_git_repo(repo: Path, branch: str = "main") -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "ohk@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "OHK Test"], cwd=repo, check=True)


def _commit_all(repo: Path, message: str = "init") -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    res = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _scaffold_canonical_contracts(
    target_dir: Path, domain: str = "lyrics-sync"
) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "api_contract.md").write_text(
        f"# API Contract: {domain}\n\n"
        f"- **Domain**: `{domain}`\n"
        "- **Version**: `1.0.0`\n\n"
        "## 2. Authentication and Headers\n"
        "| Header | Type | Required | Description |\n"
        "|---|---|---|---|\n"
        "| X-Worker-Token | String | Yes | Worker token |\n\n"
        "## 3. Endpoints Matrix\n"
        "| Method | Endpoint | Auth | Purpose |\n"
        "|---|---|---|---|\n"
        f"| GET | /api/v1/{domain}/status | Public | Status |\n",
        encoding="utf-8",
    )
    (target_dir / "architecture_and_flow.md").write_text(
        f"# Architecture and Flow: {domain}\n\n"
        "## 2. Pipeline Steps\n"
        "1. **Receive**: Accept request.\n"
        "2. **Respond**: Emit payload.\n",
        encoding="utf-8",
    )
    (target_dir / "gaps_and_rfcs.md").write_text(
        f"# Gaps and RFCs Ledger: {domain}\n\n"
        "## 2. Active RFC Ledger\n"
        "| RFC ID | Title | Proposing Repo | Status | Target Release | Breaking? |\n"
        "|---|---|---|---|---|---|\n"
        "| RFC-001 | Baseline | Hub | Approved | 1.0.0 | No |\n",
        encoding="utf-8",
    )


def _table_rows_under_heading(markdown_text: str, heading: str) -> list[list[str]]:
    lines = markdown_text.splitlines()
    assert heading in lines, f"Missing heading {heading!r}"
    start = lines.index(heading) + 1
    rows: list[list[str]] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        if line.startswith("|") and not line.startswith(("| # |", "| Rank |", "|---")):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            rows.append(cells)
    return rows


def test_ohk_hp_05_cmr_auto_defers_epic_doc_minors(tmp_path: Path) -> None:
    """[OHK-HP-05] [Tier C - Integration] Cross-Model Review auto-defers immutable epic doc Minor findings and smoke generator infers browser targets."""
    # Verify external-review-prompt.md explicitly instructs reviewers not to emit Minor prose/formatting findings on immutable epic docs
    prompt_text = EXTERNAL_REVIEW_PROMPT.read_text(encoding="utf-8")
    assert ".devtool/epic/" in prompt_text
    assert "read-only" in prompt_text.lower()

    # Part 1: Cross-Model Review triage auto-defers immutable .devtool/epic/ Minor findings to AUTO_PASS_CLEAN
    repo = tmp_path / "cmr_repo"
    _init_git_repo(repo)
    epic_name = "sample_epic"
    epic_dir = repo / ".devtool" / "epic" / epic_name
    epic_dir.mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
    sha = _commit_all(repo, "Initial epic commit")

    review_results = epic_dir / "review_results.md"
    review_results.write_text(
        f"# Cross-Model Review: {epic_name}\n\n"
        "## Round 1\n\n"
        f"- **SHA**: {sha[:7]}\n"
        "- **CLI**: codex\n"
        "- **Model**: gpt-6.1-sol\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        f"| 1 | Minor | .devtool/epic/{epic_name}/task_01.md:14 | wording nit. Proposed: reword bullet |  |\n"
        f"| 2 | Minor | .devtool/epic/{epic_name}/manual_smoke_checklist.md:7 | minor table spacing |  |\n\n"
        "Raw output:\n\n"
        "```text\n"
        "Verdict: PASS\n"
        f"[Minor] .devtool/epic/{epic_name}/task_01.md:14 — wording nit. Proposed: reword bullet\n"
        f"[Minor] .devtool/epic/{epic_name}/manual_smoke_checklist.md:7 — minor table spacing\n"
        "```\n",
        encoding="utf-8",
    )

    triage_proc = subprocess.run(
        [
            sys.executable,
            str(RUN_EXTERNAL_REVIEW_SCRIPT),
            "triage",
            "--epic-dir",
            epic_name,
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert triage_proc.returncode == 0, triage_proc.stderr
    triage_out = triage_proc.stdout
    expected_token = "deferred: out-of-scope epic doc (§4.4)"

    findings_rows = _table_rows_under_heading(triage_out, "## Findings")
    assert len(findings_rows) == 2
    for row in findings_rows:
        assert row[1] == "Minor"
        assert row[6] == expected_token

    assert "## Auto-Triage Gate" in triage_out
    assert "- **Action**: AUTO_PASS_CLEAN" in triage_out
    assert "AUTO_PASS_FINAL_MINOR_SWEEP" not in triage_out
    assert "§4.4" in triage_out

    # Part 2: generate_smoke_checklist.py infers browser target ("Web Preview UI" or HLD/BDD URL)
    smoke_ws = tmp_path / "smoke_ws"
    smoke_epic = smoke_ws / ".devtool" / "epic" / "browser_preview"
    smoke_epic.mkdir(parents=True)
    (smoke_epic / "bdd_scenarios.md").write_text(
        "# BDD Scenarios\n\n"
        "```gherkin\n"
        "Scenario: [WEB-HP-01] [Tier C - Integration] Playwright preview modal check\n"
        "Given the Playwright browser opens the preview modal\n"
        "When the user clicks the submit button inside the viewport\n"
        "Then the modal renders the confirmation state\n"
        "```\n",
        encoding="utf-8",
    )

    smoke_proc = subprocess.run(
        [
            sys.executable,
            str(GENERATE_SMOKE_SCRIPT),
            "--epic-dir",
            "browser_preview",
            "--workspace-root",
            str(smoke_ws),
        ],
        cwd=smoke_ws,
        capture_output=True,
        text=True,
        check=False,
    )
    assert smoke_proc.returncode == 0, smoke_proc.stderr
    checklist_path = smoke_epic / "manual_smoke_checklist.md"
    assert checklist_path.is_file()
    checklist_md = checklist_path.read_text(encoding="utf-8")
    assert "Web Preview UI" in checklist_md
    assert "CLI / Workspace Root" not in checklist_md


def test_ohk_ec_05_smoke_generator_ignores_css_selectors_and_infers_web_url(
    tmp_path: Path,
) -> None:
    """[OHK-EC-05] [Tier C - Integration] Smoke checklist generator ignores CSS selector backticks and infers web target from HLD or BDD URL."""
    smoke_mod: Any = _load_module("generate_smoke_checklist", GENERATE_SMOKE_SCRIPT)

    # Case 1: Preview URL declared in BDD document; scenario uses backticked CSS selectors and route
    ws = tmp_path / "ws_bdd_url"
    epic_dir = ws / ".devtool" / "epic" / "tts_studio"
    epic_dir.mkdir(parents=True)
    bdd_text = (
        "# TTS Studio BDD Scenarios\n\n"
        "Preview URL: http://127.0.0.1:8000\n\n"
        "```gherkin\n"
        "Scenario: [TTS-HP-01] [Tier C - Integration] Save audio clip in studio\n"
        'Given Playwright opens page "/tts-studio" styled by `style.css` with `#modal` hidden\n'
        "When the user clicks `.tts-save-btn` on the preview toolbar\n"
        "Then the clip is persisted without errors\n"
        "```\n"
    )
    (epic_dir / "bdd_scenarios.md").write_text(bdd_text, encoding="utf-8")

    out_path = smoke_mod.generate_smoke_checklist(
        epic_dir="tts_studio", workspace_root=ws
    )
    checklist_text = out_path.read_text(encoding="utf-8")
    assert "| 1 | http://127.0.0.1:8000 |" in checklist_text
    assert "| 1 | `.tts-save-btn` |" not in checklist_text
    assert "CLI / Workspace Root" not in checklist_text

    # Direct API verification
    scenarios = smoke_mod.parse_bdd_scenarios(bdd_text)
    steps = smoke_mod.extract_smoke_steps(
        scenarios, default_web_target="http://127.0.0.1:8000"
    )
    assert steps[0]["target"] == "http://127.0.0.1:8000"
    assert steps[0]["target"] != "`.tts-save-btn`"
    assert steps[0]["target"] != "CLI / Workspace Root"

    # Direct unit verification on CSS selector / filename / route tokens
    assert (
        smoke_mod.extract_target_from_text(
            'Playwright clicks `.tts-save-btn` in `style.css` and `#modal` on page "/tts-studio"',
            default_web_target="http://127.0.0.1:8000",
        )
        == "http://127.0.0.1:8000"
    )

    # Case 2: Preview URL declared only in HLD <epic_dir>.md (not in bdd_scenarios.md)
    ws_hld = tmp_path / "ws_hld_url"
    hld_epic = ws_hld / ".devtool" / "epic" / "hld_web_epic"
    hld_epic.mkdir(parents=True)
    (hld_epic / "hld_web_epic.md").write_text(
        "# HLD\n\nLocal preview server runs at `http://127.0.0.1:4321/preview`.\n",
        encoding="utf-8",
    )
    (hld_epic / "bdd_scenarios.md").write_text(
        "# Scenarios\n\n"
        "```gherkin\n"
        "Scenario: [HLD-HP-01] [Tier C - Integration] Render DOM preview\n"
        "Given Playwright renders `index.html` and opens `#preview-drawer`\n"
        "When the user clicks `.confirm-btn`\n"
        "Then the DOM updates cleanly\n"
        "```\n",
        encoding="utf-8",
    )
    hld_out = smoke_mod.generate_smoke_checklist(
        epic_dir="hld_web_epic", workspace_root=ws_hld
    )
    hld_checklist = hld_out.read_text(encoding="utf-8")
    assert "| 1 | http://127.0.0.1:4321/preview |" in hld_checklist
    assert "CLI / Workspace Root" not in hld_checklist


def test_ohk_st_03_delta_context_honors_deferred_and_blocks_source_or_important(
    tmp_path: Path,
) -> None:
    """[OHK-ST-03] [Tier C - Integration] Delta review context honors deferred epic-doc tokens while blocking deferred on Important or source-file findings."""
    rer: Any = _load_module("run_external_review", RUN_EXTERNAL_REVIEW_SCRIPT)

    repo = tmp_path / "delta_repo"
    _init_git_repo(repo)
    epic_dir = repo / ".devtool" / "epic" / "sample"
    epic_dir.mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    sha1 = _commit_all(repo, "Round 1 commit")

    review_results = epic_dir / "review_results.md"
    review_results.write_text(
        "# Cross-Model Review: sample\n\n"
        "## Round 1\n\n"
        f"- **SHA**: {sha1}\n"
        "- **CLI**: claude\n"
        "- **Model**: Opus 5.5\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Minor | .devtool/epic/sample/task_01.md:10 | wording nit | deferred: out-of-scope epic doc (§4.4) |\n\n"
        "Raw output:\n\n```text\nVerdict: PASS\n```\n",
        encoding="utf-8",
    )

    (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
    sha2 = _commit_all(repo, "Round 2 revision")

    ns = argparse.Namespace(
        epic_dir="sample",
        full=False,
        cli="codex",
        model=None,
        diff_limit=1500,
    )
    block, scope_meta = rer.delta_round_context(repo, ns, sha2, kind="code")
    assert block, "Expected non-empty Round 2 delta context"
    assert scope_meta.get("Scope", "").startswith("delta from round 1")
    assert "4. Do not re-raise a finding marked `dismissed:` or `deferred:`" in block
    assert "`deferred:" in block.split("### Cross-Provider Handoff")[1].split("\n\n")[1]

    # Case 2 ([SE-05]): Minor finding on ordinary source file with arbitrary `deferred:` MUST remain AUTO_PASS_FINAL_MINOR_SWEEP
    review_results.write_text(
        "# Cross-Model Review: sample\n\n"
        "## Round 1\n\n"
        f"- **SHA**: {sha2[:7]}\n"
        "- **CLI**: claude\n"
        "- **Model**: Opus 5.5\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: PASS\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Minor | src/app.py:1 | magic number | deferred: arbitrary |\n\n"
        "Raw output:\n\n```text\nVerdict: PASS\n```\n",
        encoding="utf-8",
    )
    triage_src = subprocess.run(
        [
            sys.executable,
            str(RUN_EXTERNAL_REVIEW_SCRIPT),
            "triage",
            "--epic-dir",
            "sample",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert triage_src.returncode == 0, triage_src.stderr
    assert "- **Action**: AUTO_PASS_FINAL_MINOR_SWEEP" in triage_src.stdout
    assert "AUTO_PASS_CLEAN" not in triage_src.stdout

    # Case 3: Important finding marked with `deferred: out-of-scope epic doc (§4.4)` MUST fail `check` (exit 1, undecided)
    review_results.write_text(
        "# Cross-Model Review: sample\n\n"
        "## Round 1\n\n"
        f"- **SHA**: {sha2[:7]}\n"
        "- **CLI**: claude\n"
        "- **Model**: Opus 5.5\n"
        "- **Thinking**: high\n"
        "- **Status**: completed\n"
        "- **Verdict**: CHANGES REQUIRED\n\n"
        "| # | Severity | Location | Problem | Decision |\n"
        "|---|----------|----------|---------|----------|\n"
        "| 1 | Important | .devtool/epic/sample/task_01.md:10 | missing acceptance check | deferred: out-of-scope epic doc (§4.4) |\n\n"
        "Raw output:\n\n```text\nVerdict: CHANGES REQUIRED\n```\n",
        encoding="utf-8",
    )
    check_proc = subprocess.run(
        [
            sys.executable,
            str(RUN_EXTERNAL_REVIEW_SCRIPT),
            "check",
            "--epic-dir",
            "sample",
        ],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert check_proc.returncode == 1
    assert "undecided: #1 Important" in check_proc.stdout


def test_ohk_fr_03_sync_contracts_diff_check_allow_dirty_and_protected_guards(
    tmp_path: Path,
) -> None:
    """[OHK-FR-03] [Tier C - Integration] sync_contracts.py diff-check enforces clean tree by default and guards protected contract paths under --allow-dirty."""
    # Scaffold Hub + Satellite repositories
    hub_dir = tmp_path / "hub"
    _init_git_repo(hub_dir, "main")
    hub_domain = hub_dir / "shared-contracts" / "lyrics-sync"
    _scaffold_canonical_contracts(hub_domain, "lyrics-sync")
    _commit_all(hub_dir, "Hub initial contracts")

    sat_dir = tmp_path / "satellite"
    _init_git_repo(sat_dir, "main")
    rel_target = os.path.relpath(hub_domain, sat_dir)
    os.symlink(rel_target, sat_dir / "shared-contracts")

    sat_agents = sat_dir / ".agents"
    sat_agents.mkdir(parents=True)
    contract_map = {
        "schema_version": 1,
        "base_ref": "main",
        "domains": {
            "lyrics-sync": {"paths": ["src/api/**"]},
        },
        "waivers": [],
    }
    (sat_agents / "contract_map.json").write_text(
        json.dumps(contract_map, indent=2), encoding="utf-8"
    )
    ack_proc = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "ack",
            "--repo-root",
            str(sat_dir),
            "--domain",
            "lyrics-sync",
            "--all-rfcs",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ack_proc.returncode == 0, ack_proc.stderr
    # Backdate baseline last_synced_at so a subsequent same-second `ack` always modifies contract_sync.json
    sync_json_path = sat_agents / "contract_sync.json"
    baseline_sync = json.loads(sync_json_path.read_text(encoding="utf-8"))
    baseline_sync["domains"]["lyrics-sync"]["last_synced_at"] = "2026-10-01T00:00:00Z"
    sync_json_path.write_text(json.dumps(baseline_sync, indent=2), encoding="utf-8")

    preview_js = sat_dir / "src" / "preview" / "ui.js"
    preview_js.parent.mkdir(parents=True)
    preview_js.write_text("export const v = 1;\n", encoding="utf-8")
    api_py = sat_dir / "src" / "api" / "dto.py"
    api_py.parent.mkdir(parents=True)
    api_py.write_text("SCHEMA = 1\n", encoding="utf-8")
    _commit_all(sat_dir, "Satellite baseline")

    # Feature branch with a clean committed non-contract change, then an uncommitted edit to src/preview/ui.js
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feat/ui-polish", "main"],
        cwd=sat_dir,
        check=True,
    )
    preview_js.write_text("export const v = 2;\n", encoding="utf-8")
    _commit_all(sat_dir, "Committed preview change")
    preview_js.write_text("export const v = 3; // uncommitted\n", encoding="utf-8")

    # 1. Default without --allow-dirty -> exit 2, BLOCKED
    proc_default = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_dir),
            "--base-ref",
            "main",
            "--json",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_default.returncode == 2
    payload_default = json.loads(proc_default.stdout)
    assert payload_default["status"] == "BLOCKED"

    # 2. With --allow-dirty while protected paths are clean -> exit 0, PASS
    proc_allow = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_dir),
            "--base-ref",
            "main",
            "--allow-dirty",
            "--json",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_allow.returncode == 0, proc_allow.stdout + proc_allow.stderr
    payload_allow = json.loads(proc_allow.stdout)
    assert payload_allow["status"] == "PASS"

    # 3. Tracked modification to .agents/contract_map.json with --allow-dirty -> exit 2, BLOCKED naming path
    original_map = (sat_agents / "contract_map.json").read_text(encoding="utf-8")
    contract_map_dirty = dict(contract_map)
    contract_map_dirty["waivers"] = []
    (sat_agents / "contract_map.json").write_text(
        json.dumps(contract_map_dirty, indent=4) + "\n", encoding="utf-8"
    )
    proc_dirty_map = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_dir),
            "--base-ref",
            "main",
            "--allow-dirty",
            "--json",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_dirty_map.returncode == 2
    payload_dirty_map = json.loads(proc_dirty_map.stdout)
    assert payload_dirty_map["status"] == "BLOCKED"
    assert any(".agents/contract_map.json" in b for b in payload_dirty_map["blockers"])
    (sat_agents / "contract_map.json").write_text(original_map, encoding="utf-8")

    # 4. Tracked modification to .agents/contract_sync.json (uncommitted ack) with --allow-dirty -> exit 2, BLOCKED naming path
    api_py.write_text("SCHEMA = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/api/dto.py"], cwd=sat_dir, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Commit mapped api delta"],
        cwd=sat_dir,
        check=True,
    )
    ack_dirty = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "ack",
            "--repo-root",
            str(sat_dir),
            "--domain",
            "lyrics-sync",
            "--all-rfcs",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert ack_dirty.returncode == 0, ack_dirty.stderr
    proc_dirty_sync = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_dir),
            "--base-ref",
            "main",
            "--allow-dirty",
            "--json",
        ],
        cwd=sat_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_dirty_sync.returncode == 2
    payload_dirty_sync = json.loads(proc_dirty_sync.stdout)
    assert payload_dirty_sync["status"] == "BLOCKED"
    assert any(
        ".agents/contract_sync.json" in b for b in payload_dirty_sync["blockers"]
    )

    # 5. Untracked .agents/contract_sync.json with --allow-dirty -> STILL exit 2, BLOCKED naming path
    sat_untracked = tmp_path / "satellite_untracked"
    _init_git_repo(sat_untracked, "main")
    os.symlink(
        os.path.relpath(hub_domain, sat_untracked),
        sat_untracked / "shared-contracts",
    )
    (sat_untracked / ".agents").mkdir(parents=True)
    (sat_untracked / ".agents" / "contract_map.json").write_text(
        json.dumps(contract_map, indent=2), encoding="utf-8"
    )
    (sat_untracked / "src" / "api").mkdir(parents=True)
    (sat_untracked / "src" / "api" / "dto.py").write_text(
        "SCHEMA = 1\n", encoding="utf-8"
    )
    _commit_all(sat_untracked, "Baseline without contract_sync.json")
    subprocess.run(
        ["git", "checkout", "-q", "-b", "feat/untracked-ack", "main"],
        cwd=sat_untracked,
        check=True,
    )
    (sat_untracked / "src" / "api" / "dto.py").write_text(
        "SCHEMA = 2\n", encoding="utf-8"
    )
    _commit_all(sat_untracked, "Mapped API change")
    # Create UNTRACKED .agents/contract_sync.json via ack without committing
    subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "ack",
            "--repo-root",
            str(sat_untracked),
            "--domain",
            "lyrics-sync",
            "--all-rfcs",
        ],
        cwd=sat_untracked,
        check=True,
        capture_output=True,
    )
    proc_untracked_sync = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_untracked),
            "--base-ref",
            "main",
            "--allow-dirty",
            "--json",
        ],
        cwd=sat_untracked,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_untracked_sync.returncode == 2
    payload_untracked = json.loads(proc_untracked_sync.stdout)
    assert payload_untracked["status"] == "BLOCKED"
    assert any(".agents/contract_sync.json" in b for b in payload_untracked["blockers"])

    # 6. Dirty shared-contracts symlink with --allow-dirty -> STILL exit 2, BLOCKED naming shared-contracts
    alt_domain = hub_dir / "shared-contracts" / "alt-domain"
    _scaffold_canonical_contracts(alt_domain, "alt-domain")
    symlink_path = sat_untracked / "shared-contracts"
    (sat_untracked / ".agents" / "contract_sync.json").unlink()
    symlink_path.unlink()
    os.symlink(os.path.relpath(alt_domain, sat_untracked), symlink_path)
    proc_dirty_symlink = subprocess.run(
        [
            sys.executable,
            str(SYNC_CONTRACTS_SCRIPT),
            "diff-check",
            "--repo-root",
            str(sat_untracked),
            "--base-ref",
            "main",
            "--allow-dirty",
            "--json",
        ],
        cwd=sat_untracked,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc_dirty_symlink.returncode == 2
    payload_symlink = json.loads(proc_dirty_symlink.stdout)
    assert payload_symlink["status"] == "BLOCKED"
    assert any("shared-contracts" in b for b in payload_symlink["blockers"])


class Test_Ohk_Cmr_And_Contracts_Integration:
    """[Tier C - Integration] Integration runner provenance for OHK-HP-05, OHK-EC-05, OHK-ST-03, and OHK-FR-03."""

    def test_ohk_hp_05_integration(self, tmp_path: Path) -> None:
        """[OHK-HP-05] [Tier C - Integration] Cross-Model Review auto-defers immutable epic doc Minor findings and smoke generator infers browser targets."""
        test_ohk_hp_05_cmr_auto_defers_epic_doc_minors(tmp_path)

    def test_ohk_ec_05_integration(self, tmp_path: Path) -> None:
        """[OHK-EC-05] [Tier C - Integration] Smoke checklist generator ignores CSS selector backticks and infers web target from HLD or BDD URL."""
        test_ohk_ec_05_smoke_generator_ignores_css_selectors_and_infers_web_url(
            tmp_path
        )

    def test_ohk_st_03_integration(self, tmp_path: Path) -> None:
        """[OHK-ST-03] [Tier C - Integration] Delta review context honors deferred epic-doc tokens while blocking deferred on Important or source-file findings."""
        test_ohk_st_03_delta_context_honors_deferred_and_blocks_source_or_important(
            tmp_path
        )

    def test_ohk_fr_03_integration(self, tmp_path: Path) -> None:
        """[OHK-FR-03] [Tier C - Integration] sync_contracts.py diff-check enforces clean tree by default and guards protected contract paths under --allow-dirty."""
        test_ohk_fr_03_sync_contracts_diff_check_allow_dirty_and_protected_guards(
            tmp_path
        )
