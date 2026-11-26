# Observer Hardening Batch 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve `task-observer` observations `#17`–`#20` inside `.worktrees/observer_hardening_batch2` (`feat/observer-hardening-batch2`): skip `duplicate_text` prose checks on stylesheets in `audit_ui_state_and_styles.py`, promote hermetic Playwright E2E + `DevToolsActivePort` pre-flight/fallback across browser-verification skills, add standalone plan discovery and a top-10 `Done` (Recently Completed) Kanban tab to `check-tasks`, and support sequential `&&`/`;` command chains in `check_task_contract.py` `TIER-B` capability matching.

**Architecture:** Each observation maps cleanly to one self-contained module boundary — `web-quality-check`, browser-verification skill documentation, `check-tasks` backend + dashboard UI, and `dev-implementation` / `dev-designer` contract validation. Backend changes reuse existing constants and lexers (`STYLESHEET_EXTENSIONS`, `_normalize_slug`, `shlex.shlex(..., punctuation_chars=True)`), while UI updates isolate completed tasks in a new `TaskProgress.completed_tasks` field so active `Doing` metrics remain untouched.

**Tech Stack:** Python 3.11+ (stdlib + `pytest`, `ruff`, `mypy`), HTML5 / Vanilla JS (`tasks_dashboard.html` verified via Node.js `vm` harness + hermetic Playwright/CDP), Markdown skills (`d3nexus:` namespace), `bash scripts/verify.sh`.

**Spec:** [2026-11-27-observer-hardening-batch2-design.md](../specs/2026-11-27-observer-hardening-batch2-design.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Implementation Tasks](#implementation-tasks)
  - [Task 1: Skip duplicate_text on Stylesheets in audit_ui_state_and_styles.py](#task-1-skip-duplicate_text-on-stylesheets-in-audit_ui_state_and_stylespy)
  - [Task 2: Hermetic Playwright Primary Browser Gate and DevToolsActivePort Pre-Flight in Skills](#task-2-hermetic-playwright-primary-browser-gate-and-devtoolsactiveport-pre-flight-in-skills)
  - [Task 3: Standalone Plans Discovery and Top-10 Done Kanban Tab in check-tasks](#task-3-standalone-plans-discovery-and-top-10-done-kanban-tab-in-check-tasks)
  - [Task 4: Sequential TIER-B Compound Command Matching in check_task_contract.py](#task-4-sequential-tier-b-compound-command-matching-in-check_task_contractpy)

## Global Constraints

- **Worktree-only writes**: Work strictly inside `/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/observer_hardening_batch2` on branch `feat/observer-hardening-batch2`. NEVER modify the `main` checkout, `lyrics-sync`, `D3Nexus`, `nexus`, `~/.gemini/config/plugins/d3nexus`, `~/.claude/plugins/`, or `~/.codex/`. NEVER run `scripts/release.sh`, `git push`, or `git pull` into live plugins.
- **Skill contract (`CLAUDE.md`)**: Every `skills/<name>/SKILL.md` frontmatter must contain exclusively `name` and `description`. All cross-references between skills in this kit must use `d3nexus:` (zero `superpowers:` namespace strings under `skills/` or `rules/`). Open-source skill docs must contain zero personal paths (`/Users/...`) or profile names.
- **Rule 11 (English SSOT)**: Never open, grep, glob, or list `*.vi.md` files into context; standalone plan discovery in `check_tasks.py` must strictly ignore `*.vi.md`.
- **Canonical quality commands** (from `.agents/quality/python-quality.json`):
  - Format check: `ruff format --check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py`
  - Lint: `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py`
  - Type check: `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py`
  - Tests: `python3 -m pytest -q --tb=short --maxfail=3 tests`
  - Architecture: `bash scripts/verify.sh`
- **Commit format**: `[OBSERVER_HARDENING_BATCH2] <Imperative title>` with `- <bullet>` lines and zero `Co-Authored-By:` or tool trailers. Never run `git push`.

---

## File Structure

- Modify: `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py` — guard `DUPLICATE_PHRASE_PATTERN` in `audit_text_truncation_and_overflow()` to skip `STYLESHEET_EXTENSIONS` (`.css`, `.scss`) while preserving `LEFT_CLIP_PATTERN`.
- Modify: `tests/test_audit_ui_state_and_styles.py` — add parametrized unit and git-backed regression tests for `#17`.
- Modify: `skills/writing-plans/SKILL.md` — promote hermetic Playwright E2E + screenshot assertions as primary automated browser gate and require `DevToolsActivePort` pre-flight + fallback for `browser` subagent.
- Modify: `skills/dev-designer/SKILL.md` — align Web Tier C anti-rationalization and browser verification guidance with `#18`.
- Modify: `skills/dev-designer/references/task-template-examples.md` — update Web 3-tier matrix and Mermaid `BROWSER_VERIFY` node for hermetic Playwright primary gate + `DevToolsActivePort` pre-flight.
- Modify: `skills/subagent-driven-development/SKILL.md` — document isolated-profile `DevToolsActivePort` `ENOENT` fallback ruling into the SDD ledger.
- Create: `tests/test_ohk2_skill_docs.py` — verify `#18` and `#20` doc contracts, frontmatter keys, `d3nexus:` namespace, and zero personal paths.
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py` — add `TaskProgress.completed_tasks`, `_parse_project_ledger_milestones()`, `_discover_standalone_plans()`, standalone plan & ledger milestone discovery in `harvest_epics_overview()`, and active-plan + top-10 completed task extraction in `extract_task_progress()`.
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html` — add 4th Kanban `EPIC STATUS` tab (`Done`), top-10 `RECENTLY COMPLETED` sidebar list, `Plan` / `Epic` / `Ledger` badges in Kanban and Roadmap, and milestone summary card rendering.
- Create: `tests/test_check_tasks_standalone_plans.py` — Python harvester + Node.js `vm` DOM/JS verification tests for `#19`.
- Modify: `skills/dev-implementation/resources/scripts/check_task_contract.py` — add `_split_sequential_subcommands()` and update `matches_cap()` + fallback branch in `check_python_tier_b()`.
- Modify: `skills/dev-designer/references/verification-rows.md` — document sequential `&&` / `;` chaining and separate `V4`/`V5` parity for Python `TIER-B` rows.
- Modify: `skills/dev-implementation/resources/scripts/test_check_task_contract.py` — add `#20` unit and CLI regression tests.
- Modify: `scripts/verify.sh` — register `tests/test_ohk2_skill_docs.py` and `tests/test_check_tasks_standalone_plans.py` in `SUITES`.

## Implementation Tasks

### Task 1: Skip duplicate_text on Stylesheets in audit_ui_state_and_styles.py

**Files:**
- Modify: `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py:831-904`
- Modify: `tests/test_audit_ui_state_and_styles.py:250-280`

**Interfaces:**
- Consumes: `STYLESHEET_EXTENSIONS`, `LEFT_CLIP_PATTERN`, `DUPLICATE_PHRASE_PATTERN`, `audit_text_truncation_and_overflow(repo_root: Path, target_files: list[str] | None = None)`, and `run_all_ui_reviews(repo_root: Path | str = ".", base_ref: str = "main")` in `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py`.
- Produces: `audit_text_truncation_and_overflow()` skipping `DUPLICATE_PHRASE_PATTERN` for any file whose lowercased suffix is in `STYLESHEET_EXTENSIONS` (`.css`, `.scss`) while still evaluating `LEFT_CLIP_PATTERN` on stylesheets and evaluating both patterns on templates/scripts.

- [ ] **Step 1: Write the failing unit and git-backed integration tests**

In `tests/test_audit_ui_state_and_styles.py`, add `import subprocess` and `import pytest` to the top import block (lines 5–7, before `REPO_ROOT`), and append the following test functions at the end of the file (after line 280):

```python
@pytest.mark.parametrize(
    ("filename", "css_body"),
    [
        (
            "static/style.css",
            ".icon { background-size: 14px 14px; }\n"
            ".panel { border-radius: 10px 10px 0 0; }\n"
            ".arrow { border-color: #fff transparent transparent; }\n"
            ".grid { grid-template-columns: 1fr 1fr; }\n",
        ),
        (
            "styles/theme.scss",
            "$pad: 12px;\n.box { margin: 12px 12px; padding: 8px 8px 4px 4px; }\n",
        ),
        (
            "styles/UPPER.CSS",
            ".btn { border-radius: 10px 10px 0 0; background-size: 16px 16px; }\n",
        ),
    ],
)
def test_stylesheet_shorthands_skip_duplicate_text_when_target_files_passed(
    tmp_path: Path, filename: str, css_body: str
) -> None:
    """#17: Multi-axis CSS/SCSS shorthands must not trigger duplicate_text false positives."""
    css_file = tmp_path / filename
    css_file.parent.mkdir(parents=True, exist_ok=True)
    css_file.write_text(css_body, encoding="utf-8")

    findings = audit_text_truncation_and_overflow(
        tmp_path, target_files=[filename]
    )
    dup_findings = [f for f in findings if f["category"] == "duplicate_text"]
    assert dup_findings == [], f"Unexpected CSS duplicate_text findings: {dup_findings}"


def test_stylesheet_still_checks_left_clip_while_html_checks_duplicate_text(
    tmp_path: Path,
) -> None:
    """#17: Stylesheets retain LEFT_CLIP_PATTERN; templates retain DUPLICATE_PHRASE_PATTERN."""
    css_file = tmp_path / "static" / "layout.css"
    css_file.parent.mkdir(parents=True, exist_ok=True)
    css_file.write_text(
        ".row { display: flex; justify-content: flex-end; text-overflow: ellipsis; "
        "border-radius: 10px 10px 0 0; }\n",
        encoding="utf-8",
    )
    html_file = tmp_path / "templates" / "view.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    html_file.write_text("<h2>Status Status</h2>\n", encoding="utf-8")

    findings = audit_text_truncation_and_overflow(
        tmp_path, target_files=["static/layout.css", "templates/view.html"]
    )
    css_findings = [f for f in findings if f["file"] == "static/layout.css"]
    html_findings = [f for f in findings if f["file"] == "templates/view.html"]

    assert [f["category"] for f in css_findings] == ["text_clipping"]
    assert [f["category"] for f in html_findings] == ["duplicate_text"]


def test_run_all_ui_reviews_modified_css_shorthand_passes_end_to_end(
    tmp_path: Path,
) -> None:
    """#17 integration: Modifying a .css file with multi-axis shorthands passes run_all_ui_reviews()."""
    repo = tmp_path / "web_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo, check=True)

    (repo / "static").mkdir()
    (repo / "static" / "style.css").write_text(".box { color: #fff; }\n", encoding="utf-8")
    (repo / "index.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="static/style.css?v=1"></head>'
        '<body><div class="box">Hello</div></body></html>\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)

    subprocess.run(["git", "checkout", "-q", "-b", "feat"], cwd=repo, check=True)
    (repo / "static" / "style.css").write_text(
        ".box { color: #fff; background-size: 14px 14px; border-radius: 10px 10px 0 0; }\n",
        encoding="utf-8",
    )
    (repo / "index.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="static/style.css?v=2"></head>'
        '<body><div class="box">Hello</div></body></html>\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "css shorthand"], cwd=repo, check=True)

    res = run_all_ui_reviews(repo_root=repo, base_ref="main")
    assert res["status"] == "PASS", f"Expected PASS, got {res}"
    assert res["findings"] == []
```

- [ ] **Step 2: Run tests to verify RED failure**

Run: `python3 -m pytest -q tests/test_audit_ui_state_and_styles.py -k "stylesheet_shorthands or modified_css_shorthand"`
Expected: FAIL with `[duplicate_text]` findings (`14px`, `10px`, `transparent`, `12px`).

- [ ] **Step 3: Implement the stylesheet guard in `audit_text_truncation_and_overflow()`**

In `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py` (around line 880, right after the `LEFT_CLIP_PATTERN` block and before `# Check headings and titles for consecutive duplicate words/phrases`):

```python
        # Skip prose duplicate-phrase checks on stylesheets (multi-axis CSS shorthands like 14px 14px)
        if cf.suffix.lower() in STYLESHEET_EXTENSIONS:
            continue
```

- [ ] **Step 4: Run targeted tests, downstream regression, and static checks**

Run:
```bash
python3 -m pytest -q tests/test_audit_ui_state_and_styles.py tests/test_ohk_web_ui_audit.py && \
ruff format --check skills/web-quality-check tests/test_audit_ui_state_and_styles.py && \
ruff check skills/web-quality-check tests/test_audit_ui_state_and_styles.py
```
Expected: All tests PASS, 0 ruff format/lint errors.

- [ ] **Step 5: Commit Task 1**

```bash
git add skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py tests/test_audit_ui_state_and_styles.py
git commit -m "[OBSERVER_HARDENING_BATCH2] Skip duplicate_text prose regex on CSS and SCSS stylesheets" -m "- guard DUPLICATE_PHRASE_PATTERN with STYLESHEET_EXTENSIONS in audit_text_truncation_and_overflow while retaining LEFT_CLIP_PATTERN" -m "- add parametrized unit and git-backed integration regression tests in tests/test_audit_ui_state_and_styles.py"
```

---

### Task 2: Hermetic Playwright Primary Browser Gate and DevToolsActivePort Pre-Flight in Skills

**Files:**
- Modify: `skills/writing-plans/SKILL.md:10-56,180-190,217-222`
- Modify: `skills/dev-designer/SKILL.md:87-98`
- Modify: `skills/dev-designer/references/task-template-examples.md:33-38,105-112,137-145`
- Modify: `skills/subagent-driven-development/SKILL.md:120-135`
- Create: `tests/test_ohk2_skill_docs.py`
- Modify: `scripts/verify.sh:470-480`

**Interfaces:**
- Consumes: Existing `SKILL.md` frontmatter and `d3nexus:` cross-reference rules verified by `scripts/verify.sh` and `tests/test_ohk_docs_and_acceptance.py`.
- Produces: Generalized open-source browser verification rules (hermetic Playwright E2E + screenshots primary; interactive Chrome DevTools / `browser` subagent pre-flight checked for `DevToolsActivePort` with documented Playwright ruling fallback) + automated doc-contract test suite `tests/test_ohk2_skill_docs.py` registered in `scripts/verify.sh`.

- [ ] **Step 1: Write the failing doc-contract test suite**

Create `tests/test_ohk2_skill_docs.py`:

```python
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


def test_obs18_skills_require_hermetic_playwright_primary_and_devtools_preflight() -> None:
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
        assert "superpowers:" not in text, f"{rel} contains stale superpowers: reference"
        for pat in PERSONAL_LEAK_PATTERNS:
            assert pat.search(text) is None, f"{rel} leaked personal pattern {pat.pattern!r}"

    for rel in (
        "skills/writing-plans/SKILL.md",
        "skills/dev-designer/SKILL.md",
        "skills/subagent-driven-development/SKILL.md",
    ):
        text = _read(rel)
        fm = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
        assert fm is not None, f"{rel}: missing YAML frontmatter"
        keys = re.findall(r"^([A-Za-z_][\w-]*):", fm.group(1), flags=re.MULTILINE)
        assert set(keys) == {"name", "description"}, f"{rel}: invalid frontmatter keys {keys!r}"
```

- [ ] **Step 2: Run test to verify RED failure**

Run: `python3 -m pytest -q tests/test_ohk2_skill_docs.py`
Expected: FAIL because `DevToolsActivePort` and hermetic Playwright primary gate rules are not yet present in the 4 skill documents.

- [ ] **Step 3: Update the 4 skill documents (strictly generalized open-source wording)**

1. **`skills/writing-plans/SKILL.md`**:
   - Overview (L12): Replace mandatory `browser_subagent`-only phrasing with:
     `For any Web or UI deliverables, the plan MUST include a dedicated **Browser Verification** step using **hermetic Playwright E2E assertions and screenshot capture** as the primary automated gate (with optional interactive Chrome DevTools via \`browser_subagent\` pre-flight checked for \`DevToolsActivePort\` and falling back to Playwright in isolated multi-profile \`HOME\` environments).`
   - Section `3. Live Web Browser Verification (For Web / UI Deliverables)` (L45–53):
     - Specify hermetic Playwright E2E assertions + screenshot capture (running against project-local bundled Chromium independent of host `HOME`) as the primary automated browser gate.
     - State that interactive Chrome DevTools (`browser_subagent`) is an optional visual pass that MUST run a pre-flight check for `DevToolsActivePort` in the active Chrome user data directory and fall back cleanly to hermetic Playwright E2E + screenshots whenever `DevToolsActivePort` is absent in isolated multi-profile `HOME` environments.
   - `Step 6` template (L181–188):
     - Primary step: run hermetic Playwright E2E suite against the preview/dev server asserting interactive DOM states, layout geometry, zero console errors, and saving screenshot artifacts.
     - Optional interactive supplement: pre-flight check `DevToolsActivePort`; if present, dispatch `browser_subagent`; if absent (`ENOENT` in isolated `HOME`), record the fallback to Playwright and proceed without stalling.
   - Self-Review `#5` (L219): Update to verify hermetic Playwright E2E + screenshot gate and `DevToolsActivePort` pre-flight/fallback for interactive `browser_subagent` steps.
2. **`skills/dev-designer/SKILL.md`**:
   - Update Anti-Rationalization table (L91–95): clarify Web Tier C uses **hermetic Playwright E2E + screenshot/layout (`getComputedStyle`, `getBoundingClientRect`) + Zero-Console-Error checks** as the primary automated browser gate (independent of host `HOME`), and add a concise note/row that interactive Chrome DevTools (`browser_subagent`) requires a `DevToolsActivePort` pre-flight check with Playwright fallback in isolated multi-profile `HOME` setups.
3. **`skills/dev-designer/references/task-template-examples.md`**:
   - L35 (`Design Rationale & Applicable Skills` Web bullet): list `Playwright` (primary hermetic browser gate), Node.js `--test` / Vitest, Astro check, optional `browser_subagent` (with `DevToolsActivePort` pre-flight + Playwright fallback).
   - L108 (Platform 3-Tier Testing Matrix Web Tier C): `Hermetic Playwright E2E + screenshots/DOM/CSS assertions (primary); optional interactive browser_subagent with DevToolsActivePort pre-flight + Playwright fallback`.
   - L141 (Mermaid `BROWSER_VERIFY` node — keep double-quoted label): `BROWSER_VERIFY["Web: Hermetic Playwright E2E + Screenshots<br/>(optional browser_subagent after DevToolsActivePort pre-flight)"]`.
4. **`skills/subagent-driven-development/SKILL.md`**:
   - Under `## Setup` (right after the Python linked worktree `UV_NO_SYNC=1` guidance around L130): add a concise bullet on **Isolated Multi-Profile Browser Verification Fallback**: when a plan step requests interactive Chrome DevTools (`browser_subagent`) in an isolated multi-profile `HOME` environment, pre-flight check `DevToolsActivePort` first; if absent (`ENOENT`), execute the hermetic Playwright E2E + screenshot gate instead, record `Ruling: Fell back from interactive Chrome DevTools (DevToolsActivePort ENOENT in isolated HOME) to hermetic Playwright E2E + screenshots — <why> — <cost if wrong>` in `<workspace>/progress.md`, and continue without stalling.
5. **`scripts/verify.sh`**:
   - Add section `# 24. Observer Hardening Batch 2 suites` registering `("24", "pytest", "tests/test_ohk2_skill_docs.py", 10, True)` right after section 23.

- [ ] **Step 4: Run doc tests, existing doc regression tests, and ruff**

Run:
```bash
python3 -m pytest -q tests/test_ohk2_skill_docs.py tests/test_ohk_docs_and_acceptance.py && \
ruff format --check tests/test_ohk2_skill_docs.py && \
ruff check tests/test_ohk2_skill_docs.py
```
Expected: All tests PASS, 0 ruff issues.

- [ ] **Step 5: Commit Task 2**

```bash
git add skills/writing-plans/SKILL.md skills/dev-designer/SKILL.md skills/dev-designer/references/task-template-examples.md skills/subagent-driven-development/SKILL.md tests/test_ohk2_skill_docs.py scripts/verify.sh
git commit -m "[OBSERVER_HARDENING_BATCH2] Standardize hermetic Playwright browser gate and DevToolsActivePort pre-flight" -m "- promote hermetic Playwright E2E + screenshots as primary automated browser gate in writing-plans and dev-designer" -m "- add isolated-HOME DevToolsActivePort pre-flight and ledgered Playwright fallback ruling in subagent-driven-development" -m "- add tests/test_ohk2_skill_docs.py and register it in scripts/verify.sh"
```

---

### Task 3: Standalone Plans Discovery and Top-10 Done Kanban Tab in check-tasks

**Files:**
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py:290-330,1259-1420,1540-1808,4888-5065`
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html:3062-3081,3579-3992,4163-4315`
- Create: `tests/test_check_tasks_standalone_plans.py`
- Modify: `scripts/verify.sh:476-482`

**Interfaces:**
- Consumes: `get_completed_epic_slugs()`, `get_abandoned_epic_slugs()`, `_normalize_slug()`, `_is_completed_epic()`, `_collect_matching_worktrees()`, `scan_worktrees()`, `format_relative_time()`, `natural_sort_key()`, `EpicsSummary`, `TaskProgress`, `harvest_epics_overview()`, `extract_task_progress()` in `skills/check-tasks/resources/scripts/check_tasks.py`; `renderKanbanDashboard()`, `setKanbanExecutionFilter()`, `buildKanbanSig()`, `renderEpicsOverviewAndApprovalGate()`, `renderRoadmapTableRows()` in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`.
- Produces:
  - `TaskProgress.completed_tasks: list[dict[str, Any]] = field(default_factory=list)`
  - `_parse_project_ledger_milestones(repo_path: Path) -> dict[str, dict[str, Any]]`
  - `_discover_standalone_plans(repo_path: Path) -> list[dict[str, Any]]`
  - `source_kind` (`"epic"` | `"plan"` | `"ledger"`), optional `completed_date`, `milestone_summary`, `plan_path` on items in `EpicsSummary.epics`
  - Active standalone plan tasks emitted into `TaskProgress.tasks` (`source: "plan"` / `"worktree"`, `labels: ["plan"]`), and top-10 recently completed epic/plan tasks emitted into `TaskProgress.completed_tasks`
  - 4-tab Kanban `EPIC STATUS` filter bar (`Doing | Pending | Cancelled | Done`) with top-10 `RECENTLY COMPLETED` sidebar list, `Plan`/`Epic`/`Ledger` badges, and milestone summary cards in `tasks_dashboard.html`.

- [ ] **Step 1: Write the failing backend + Node.js `vm` UI test suite**

Create `tests/test_check_tasks_standalone_plans.py` covering:
1. `test_harvest_discovers_standalone_plans_sdd_progress_ledger_and_excludes_vi_mirrors`:
   - Seeds a temp repo with:
     - 1 real `.devtool/epic/core_epic/` (done) + a same-slug `docs/superpowers/plans/2026-11-20-core-epic.md` (must deduplicate and keep `source_kind == "epic"`).
     - 1 active standalone plan `docs/superpowers/plans/2026-11-26-live-feature.md` with 3 `### Task N:` headings + `.superpowers/sdd/2026-11-26-live-feature/progress.md` marking `Task 1: complete (commits abc..def)` and `Task 2: fix round 1/1 (...)` → status `in_progress`, `source_kind == "plan"`, `task_count == 3`; `extract_task_progress().tasks` contains 3 tasks with statuses `done`, `in-progress`, `todo`.
     - 1 completed standalone plan `docs/superpowers/plans/2026-11-25-preview-subheader.md` with 2 `### Task N:` headings recorded in `.devtool/PROJECT_LEDGER.md` (`- **[2026-11-25] \`preview-subheader\`**: Completed preview subheader`) → `harvest_epics_overview()` lists it with `status == "done"`, `source_kind == "plan"`, `task_count == 2`, `completed_date == "2026-11-25"`; `extract_task_progress().tasks` excludes it (active counts stay 3, not 5), while `extract_task_progress().completed_tasks` contains its 2 `done` tasks!
     - 1 Vietnamese mirror `docs/superpowers/plans/2026-11-26-vi-only-secret.vi.md` → strictly ignored (never present in `epics_summary` or `tasks`).
     - 1 ledger-only milestone (`- **[2026-11-24] \`ledger-only-hotfix\`**: Shipped direct hotfix`) with no `.devtool/epic/` and no plan file → present in `harvest_epics_overview()` with `status == "done"`, `source_kind == "ledger"`, `completed_date == "2026-11-24"`, `milestone_summary == "Shipped direct hotfix"`.
2. `test_harvest_discovers_worktree_only_standalone_plan`:
   - Plan file exists only inside `.worktrees/wt_plan_feature/docs/superpowers/plans/2026-11-27-wt-plan-feature.md` → discovered as `in_progress` with `source_kind == "plan"` and tasks emitted into `extract_task_progress().tasks`.
3. `test_completed_tasks_caps_to_top_10_newest_and_preserves_active_metrics`:
   - Seeds 12 completed standalone plans in `PROJECT_LEDGER.md` across distinct dates (`2026-11-01`..`2026-11-12`) plus 1 active epic with 2 tasks (`1 done, 1 todo`).
   - Verifies `harvest_epics_overview().completed == 12`, `task_progress.total_tasks == 2`, `task_progress.done_tasks == 1`, and `task_progress.completed_tasks` only includes tasks from the 10 newest completed plans (`2026-11-03`..`2026-11-12`), omitting `2026-11-01` and `2026-11-02`.
4. `test_kanban_dashboard_done_tab_top_10_cap_badges_and_plan_tasks_vm`:
   - Evaluates `tasks_dashboard.html` in Node.js `vm` by importing `_eval_dashboard_js` from `tests.test_ltsp_dashboard_ui` (the same helper used by `tests/test_check_tasks_kanban_and_telemetry_fixes.py`). To exercise `ctx.setKanbanExecutionFilter(repo.name, 'done')` and tab-switch filter resets, populate `ctx.currentReposData = [repo]` and register a mock element for `'kanban-dashboard-wrapper-' + repo.name`.
   - Verifies:
     - `data-kanban-exec-filter="done"` button exists alongside `doing`, `pending`, `cancelled`.
     - Switching `setKanbanExecutionFilter(repo.name, 'done')` renders `RECENTLY COMPLETED`, caps sidebar items to 10 when 12 done items exist in newest-first (`mtime` descending) order (not re-sorted by `done/total`), shows `10/12`, renders `Plan`, `Epic`, and `Ledger` badges, renders `Milestone` + completed date instead of `0/0 Tasks` for 0-task ledger entries, shows `completed_tasks` cards in the `Done` column when selecting a completed standalone plan, and renders a synthesized milestone card when selecting a `ledger`-only milestone.
     - Selecting a completed item on the `Done` tab and switching back to `Doing` resets `currentKanbanFilter[repo.name]` to `'all'` (using `epicMatchesKanbanTab`), while re-clicking `Done` preserves the selected completed slug.
     - Roadmap rows render `Plan` and `Ledger` pills for non-epic entries while preserving epic rows unchanged, and `buildRoadmapSig()` changes when `source_kind` changes.
     - `buildKanbanSig()` changes when `completed_tasks` changes.

- [ ] **Step 2: Run test suite to verify RED failure**

Run: `python3 -m pytest -q tests/test_check_tasks_standalone_plans.py`
Expected: FAIL (`TaskProgress` lacks `completed_tasks`, standalone plans not discovered, `done` tab missing in `tasks_dashboard.html`).

- [ ] **Step 3: Implement backend standalone plan & ledger discovery in `check_tasks.py`**

Key implementation details in `skills/check-tasks/resources/scripts/check_tasks.py`:
1. Add `completed_tasks: list[dict[str, Any]] = field(default_factory=list)` to `TaskProgress`.
2. Add module-level constants:
   - `_RECENTLY_COMPLETED_LIMIT = 10`
   - `_LEDGER_MILESTONE_RE = re.compile(r"^\s*-\s+\*\*\[(\d{4}-\d{2}-\d{2})\]\s+`?([a-zA-Z0-9_\-]+)`?\*\*:\s*(.+?)\s*$")`
   - `_PLAN_DATE_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)$")`
   - `_PLAN_TASK_HEADING_RE = re.compile(r"^###\s+Task\s+(\d+)\s*:\s*(.+?)\s*$")`
   - `_SDD_TASK_COMPLETE_RE = re.compile(r"^Task\s+(\d+)\s*:\s*complete\b", re.IGNORECASE)`
   - `_SDD_TASK_FIX_RE = re.compile(r"^Task\s+(\d+)\s*:\s*fix\s+round\b", re.IGNORECASE)`
3. Implement `_parse_project_ledger_milestones(repo_path: Path) -> dict[str, dict[str, Any]]`:
   - Parses `.devtool/PROJECT_LEDGER.md` line-by-line; derives UTC epoch from `YYYY-MM-DD` plus `idx * 0.001` tie-breaker so later lines on the same date sort newer.
4. Implement `_parse_sdd_progress(repo_path: Path, plan_stem: str, extra_roots: list[Path]) -> tuple[bool, dict[int, str]]`:
   - Looks for `.superpowers/sdd/<plan_stem>/progress.md` in `extra_roots` and `repo_path` (returning `(found, {task_num: status})`).
5. Implement `_discover_standalone_plans(repo_path: Path) -> list[dict[str, Any]]`:
   - Collects roots `[repo_path]` plus non-root worktrees (from `_collect_matching_worktrees(repo_path, None)`).
   - Scans `root / "docs" / "superpowers" / "plans"` for `*.md`, skipping dotfiles and **strictly skipping `*.vi.md`**.
   - Normalizes plan stems (stripping `.en` when `.en.md`, preferring plain `.md` over legacy `.en.md`, preferring worktree copy over root when newer).
   - Extracts `slug` (stripping `YYYY-MM-DD-` prefix), `title` (first `# ` heading minus optional ` Implementation Plan`), `tasks` list from `_PLAN_TASK_HEADING_RE`, `mtime` (max of plan file mtime, `progress.md` mtime, and ledger date epoch if completed), and per-task statuses from `_parse_sdd_progress()`.
6. Update `harvest_epics_overview(repo_path)`:
   - Set `"source_kind": "epic"` (plus `"completed_date"` / `"milestone_summary"` from ledger if matching) on each `.devtool/epic/` entry, tracking seen normalized slugs in `seen_norm_slugs`.
   - Iterate `_discover_standalone_plans(repo_path)`: skip if `_normalize_slug(slug) in seen_norm_slugs`; determine status (`done` if completed in ledger/archive; `in_progress` if matching worktree/branch, `progress.md`, or `.devtool/state/<slug>.md` exists; else `unstarted`); append entry with `"source_kind": "plan"`, `"plan_path"`, `"task_count"`, `"completed_date"`, `"milestone_summary"`.
   - Iterate `_parse_project_ledger_milestones(repo_path)`: for any entry not in `seen_norm_slugs`, append `"source_kind": "ledger"`, `"status": "done"`, `"task_count": 0`, `"completed_date"`, `"milestone_summary"`, `"mtime"`, `"last_updated"`, `"last_updated_human"`.
   - Preserve existing sort key and recompute totals cleanly.
7. Update `extract_task_progress(repo_path, active_epic)`:
   - After harvesting `.devtool/epic/` & `.devtool/features/` tasks, append active standalone plan tasks (for non-completed, non-abandoned plans not duplicated by `.devtool/epic/` tasks in `seen_tasks`), respecting `seen_tasks` keyed by `(_normalize_slug(slug), task_id)`.
   - Collect `completed_tasks` for the top `_RECENTLY_COMPLETED_LIMIT` (10) newest completed entries from `harvest_epics_overview(repo_path)` (sorted by `mtime` descending):
     - For `source_kind == "plan"`: emit each `### Task N:` item with `status: "done"`, `source: "plan"`, `labels: ["plan"]`.
     - For `source_kind == "epic"`: scan `.devtool/epic/<slug>/task_*.md` in natural sort order and emit with `status: "done"`, `source: "root"`.
   - Return `TaskProgress(..., completed_tasks=completed_tasks)`.
8. Verify `_scan_repo_impl()` L4897 properly leaves `"done"` items (`source_kind` in `epic`, `plan`, `ledger`) untouched and doesn't break `doing_count` / `pending_count` / `cancelled_count` / `in_progress`! (Notice L4897 already checks `if ep.get("status") == "done" ...: continue`, and active `"plan"` items with `status == "in_progress"` naturally participate in `doing_count`!)

- [ ] **Step 4: Implement 4-tab Kanban `Done` (Recently Completed) & badges in `tasks_dashboard.html`**

In `skills/check-tasks/resources/dashboard/tasks_dashboard.html`:
1. Add `const RECENTLY_COMPLETED_LIMIT = 10;`, helper `buildSourceKindBadgeHtml(sourceKind)` returning compact pills for `'plan'` (`Plan`, `#38bdf8`), `'epic'` (`Epic`, `#a855f7`), and `'ledger'` (`Ledger`, `#94a3b8`), and tab-membership helper `epicMatchesKanbanTab(repo, slug, tab)`:
   - For `tab === 'done'`: returns `true` iff the matching entry in `repo.epics_summary.epics` has `String(ep.status || '').toLowerCase() === 'done'`.
   - For non-`'done'` tabs (`'doing'`, `'pending'`, `'cancelled'`): returns `true` iff the matching entry is NOT `'done'` and `getEpicExecutionState(repo, slug) === tab`.
2. Update `setKanbanExecutionFilter(repoName, tab)` (lines 3062–3080) to accept `'done'` alongside `'doing'`, `'pending'`, `'cancelled'`, and replace the `getEpicExecutionState(repo, currentFilter) !== normTab` reset guard at BOTH line 3069 (`setKanbanExecutionFilter`) AND line 3189 (`updateEpicExecutionState`) with `!epicMatchesKanbanTab(repo, currentFilter, normTab)`.
3. Update `renderKanbanDashboard(repo, selectedEpicFilter)`:
   - Add 4th tab `{ key: 'done', label: 'Done', accent: '#10b981' }` in `data-kanban-exec-filter-bar` with `grid-template-columns: repeat(4, minmax(0, 1fr))`.
   - When `activeExecFilter === 'done'`:
     - Filter `repo.epics_summary.epics` where `String(e.status || '').toLowerCase() === 'done'`, sorted by `Number(e.mtime || 0)` descending (`totalDone = allDoneEpics.length`), and slice top `RECENTLY_COMPLETED_LIMIT` (10) into `recentDoneEpics`.
     - Build `allTasks` **before** `filteredTasks` and `columns` populate: start from `(repo.task_progress?.completed_tasks || [])` whose `epic` matches a slug in `recentDoneEpics`, and for any `recentDoneEpics` entry with zero matching entries in `completed_tasks` (e.g., `ledger`-only milestone or taskless archived epic), append one synthesized `done` milestone summary card (`id: 'milestone-' + ep.slug`, `title: ep.milestone_summary || ep.title || ep.slug`, `status: 'done'`, `priority: 'low'`, `epic: ep.slug`, `labels: [ep.source_kind || 'ledger']`, `time: ep.completed_date || ep.last_updated_human || ''`, `source: ep.source_kind || 'ledger'`).
     - Build `epicsList` directly in `recentDoneEpics` newest-first order (do **not** apply the active-tab `(in_progress + review, done/total, total)` re-sort when `activeExecFilter === 'done'`), carrying `source_kind`, `completed_date`, `milestone_summary`, `last_updated_human`, `done: taskCount`, `total: taskCount`, `status: 'done'`.
     - Render sidebar heading `RECENTLY COMPLETED` with `${recentDoneEpics.length}${totalDone > recentDoneEpics.length ? '/' + totalDone : ''}`, render `buildSourceKindBadgeHtml(ep.source_kind)` inside each completed sidebar card, and when `ep.total === 0` render `Milestone${ep.completed_date ? ' · ' + escapeHtml(ep.completed_date) : (ep.last_updated_human ? ' · ' + escapeHtml(ep.last_updated_human) : '')}` instead of `0/0 Tasks`.
   - When `activeExecFilter !== 'done'`, keep existing active-tab behavior (filtering tasks via `epicMatchesKanbanTab(repo, t.epic || '', activeExecFilter)` and rendering active standalone plan tasks seamlessly).
   - For task card source footer (`L3831`) and epic link row (`L3816`): render `📄 Plan` when `t.source === 'plan'` and `📜 Ledger` when `t.source === 'ledger'`, avoiding bogus `.en.md` suffix on standalone plan/ledger cards.
4. Update `buildKanbanSig(repo, selectedEpicFilter)` to include `e.source_kind`, `e.completed_date`, and `ct: (repo.task_progress?.completed_tasks || []).map(t => [t.id, t.status, t.epic, t.title])`, and update `buildRoadmapSig(repo)` (`tasks_dashboard.html:4043-4058`) to include `e.source_kind || 'epic'`.
5. Update `renderEpicsOverviewAndApprovalGate()` header hint from `.devtool/epic/` to `.devtool/epic/ · plans/`.
6. Update `renderRoadmapTableRows()` to render a compact `Plan` or `Ledger` badge next to `e.slug` when `e.source_kind === 'plan' || e.source_kind === 'ledger'`.
7. Register `("24", "pytest", "tests/test_check_tasks_standalone_plans.py", 20, False)` in `scripts/verify.sh`.

- [ ] **Step 5: Run backend, VM UI, and downstream check-tasks regression suites + ruff**

Run:
```bash
python3 -m pytest -q tests/test_check_tasks_standalone_plans.py tests/test_check_tasks_harvester.py tests/test_check_tasks_kanban_and_telemetry_fixes.py tests/test_tasks_ui_epic_execution_tabs.py tests/test_rsdh_tasks_dashboard_ui.py && \
ruff format --check tests/test_check_tasks_standalone_plans.py && \
ruff check tests/test_check_tasks_standalone_plans.py
```
Expected: All tests PASS, 0 ruff errors.

- [ ] **Step 6: Commit Task 3**

```bash
git add skills/check-tasks/resources/scripts/check_tasks.py skills/check-tasks/resources/dashboard/tasks_dashboard.html tests/test_check_tasks_standalone_plans.py scripts/verify.sh
git commit -m "[OBSERVER_HARDENING_BATCH2] Discover standalone plans and add top-10 Done Kanban tab in check-tasks" -m "- extend harvest_epics_overview and extract_task_progress for docs/superpowers/plans, SDD progress.md, and PROJECT_LEDGER milestones while excluding *.vi.md" -m "- add completed_tasks field on TaskProgress and 4th Done (Recently Completed) Kanban tab with Plan/Epic/Ledger badges" -m "- add Python harvester and Node.js vm UI regression tests in tests/test_check_tasks_standalone_plans.py"
```

---

### Task 4: Sequential TIER-B Compound Command Matching in check_task_contract.py

**Files:**
- Modify: `skills/dev-implementation/resources/scripts/check_task_contract.py:822-960`
- Modify: `skills/dev-designer/references/verification-rows.md:35-58`
- Modify: `skills/dev-implementation/resources/scripts/test_check_task_contract.py:1005-1015`
- Modify: `tests/test_ohk2_skill_docs.py`

**Interfaces:**
- Consumes: `check_python_tier_b()`, `_check_python_tier_b_allowed_coverage()`, `_cap_tool_prefix()`, `tc.strip_wrappers()`, `tc.CONTROL_TOKENS` in `skills/dev-implementation/resources/scripts/check_task_contract.py`.
- Produces: `_split_sequential_subcommands(command: str) -> list[list[str]]`, compound-chain-aware `matches_cap()`, fallback branch, and `_check_python_tier_b_allowed_coverage()` in `check_task_contract.py`, plus updated grammar documentation in `skills/dev-designer/references/verification-rows.md`.

- [ ] **Step 1: Write the failing unit and CLI tests**

Add a new `CompoundTierBMatchingTest(ContractCase)` class just before `if __name__ == "__main__":` in `skills/dev-implementation/resources/scripts/test_check_task_contract.py` (note: `TIER_C` uses row ID `V5`, so `dod` references `(V2, V3, V5)`, and pipes inside Markdown table cells are escaped as `\|\|` / `\|` so `tc.split_cells()` passes cleanly and `_split_sequential_subcommands()` is actually exercised):

```python
class CompoundTierBMatchingTest(ContractCase):
    """#20: Verify TIER-B capability matching across && / ; sequential chains while rejecting || / | bypasses."""

    def _uv_manifest(self) -> None:
        manifest = json.dumps({
            "schema_version": 1,
            "capabilities": {
                "lint": ["uv", "run", "ruff", "check", "."],
                "type_check": ["uv", "run", "mypy", "--strict", "src"],
            },
        })
        self.write(".agents/quality/python-quality.json", manifest)
        self.write("src/mod.py", "def f() -> int:\n    return 1\n")
        self.commit()

    def test_chained_and_tier_b_row_matches_both_lint_and_type_check(self) -> None:
        self._uv_manifest()
        rows = (
            RED + GREEN
            + "| V3 | TIER-B | `uv run ruff check src/mod.py && uv run ruff format --check src/mod.py && uv run mypy --strict src/mod.py && uv run lint-imports` | exit 0 | — |\n"
            + TIER_C
        )
        t = self.task("1_chain_and", allowed="- `src/mod.py`", rows=rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Chained TIER-B.\n")
        code, out, _ = self.check(t, design=True)
        self.assertEqual(code, 0, out)

    def test_semicolon_chained_tier_b_row_with_and_without_spaces_passes(self) -> None:
        self._uv_manifest()
        for suffix, cmd in (
            ("unspaced", "uv run ruff check src/mod.py;uv run mypy --strict src/mod.py"),
            ("spaced", "uv run ruff check src/mod.py ; uv run mypy --strict src/mod.py"),
        ):
            rows = RED + GREEN + f"| V3 | TIER-B | `{cmd}` | exit 0 | — |\n" + TIER_C
            t = self.task(f"1_chain_{suffix}", allowed="- `src/mod.py`", rows=rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Semicolon chain.\n")
            code, out, _ = self.check(t, design=True)
            self.assertEqual(code, 0, out)

    def test_or_and_pipe_chains_do_not_satisfy_registered_type_check(self) -> None:
        self._uv_manifest()
        for suffix, cmd in (
            ("or", r"uv run ruff check src/mod.py \|\| uv run mypy --strict src/mod.py"),
            ("pipe", r"uv run ruff check src/mod.py \| uv run mypy --strict src/mod.py"),
        ):
            rows = RED + GREEN + f"| V3 | TIER-B | `{cmd}` | exit 0 | — |\n" + TIER_C
            t = self.task(f"1_bypass_{suffix}", allowed="- `src/mod.py`", rows=rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Bypass guard.\n")
            code, out, _ = self.check(t, design=True)
            self.assertEqual(code, 1, out)
            self.assertNotIn("expected 5 cells", out)
            self.assertNotIn("missing registered lint capability", out)
            self.assertIn("missing registered type_check capability", out)

    def test_chained_wrong_runner_still_rejected(self) -> None:
        self._uv_manifest()
        rows = (
            RED + GREEN
            + "| V3 | TIER-B | `uv run ruff check src/mod.py && mypy --strict src/mod.py` | exit 0 | — |\n"
            + TIER_C
        )
        t = self.task("1_wrong_runner", allowed="- `src/mod.py`", rows=rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Wrong runner.\n")
        code, out, _ = self.check(t, design=True)
        self.assertEqual(code, 1, out)
        self.assertNotIn("missing registered lint capability", out)
        self.assertIn("missing registered type_check capability", out)

    def test_chained_historical_prefix_with_expanded_manifest_passes_for_done_task(self) -> None:
        self.write("pkg/a.py", "x = 1\n")
        self.write("scripts/b.py", "y = 2\n")
        manifest = json.dumps({
            "schema_version": 1,
            "capabilities": {
                "lint": ["ruff", "check", "pkg", "tests", "scripts/b.py"],
                "type_check": ["mypy", "pkg/a.py", "scripts/b.py"],
            },
        })
        self.write(".agents/quality/python-quality.json", manifest)
        self.commit()
        rows = RED + GREEN + "| V3 | TIER-B | `ruff check pkg && mypy pkg/a.py` | exit 0 | — |\n" + TIER_C
        t = self.task("1_hist_chain", status="done", allowed="- `tool.py`", rows=rows, dod="- done (V2, V3, V5)\n")
        code, out, _ = self.check(t, design=True)
        self.assertEqual(code, 0, out)

    def test_fallback_without_manifest_accepts_and_rejects_or(self) -> None:
        self.write("src/mod.py", "def f() -> int:\n    return 1\n")
        self.commit()
        good_rows = RED + GREEN + "| V3 | TIER-B | `ruff check src/mod.py && mypy --strict src/mod.py` | exit 0 | — |\n" + TIER_C
        t_good = self.task("1_fb_ok", allowed="- `src/mod.py`", rows=good_rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Fallback ok.\n")
        code, out, _ = self.check(t_good, design=True)
        self.assertEqual(code, 0, out)

        bad_rows = RED + GREEN + r"| V3 | TIER-B | `ruff check src/mod.py \|\| mypy --strict src/mod.py` | exit 0 | — |" + "\n" + TIER_C
        t_bad = self.task("1_fb_bad", allowed="- `src/mod.py`", rows=bad_rows, dod="- [ ] done (V2, V3, V5)\n", decisions="- Fallback reject.\n")
        code2, out2, _ = self.check(t_bad, design=True)
        self.assertEqual(code2, 1, out2)
        self.assertNotIn("expected 5 cells", out2)
        self.assertNotIn("lint (ruff)", out2)
        self.assertIn("type-check", out2)
```

Also add a doc assertion in `tests/test_ohk2_skill_docs.py` confirming `skills/dev-designer/references/verification-rows.md` documents `&&` / `;` sequential chaining and `||` / `|` exclusion for Python `TIER-B` rows.

- [ ] **Step 2: Run tests to verify RED failure**

Run: `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py -k CompoundTierBMatchingTest`
Expected: FAIL (`test_chained_and_tier_b_row_matches_both_lint_and_type_check`, `test_semicolon_chained_tier_b_row_with_and_without_spaces_passes`, and `test_fallback_without_manifest_accepts_and_rejects_or` fail).

- [ ] **Step 3: Implement `_split_sequential_subcommands()` and update `check_python_tier_b()` + `verification-rows.md`**

In `skills/dev-implementation/resources/scripts/check_task_contract.py` (just above `check_python_tier_b`):

```python
_SEQUENTIAL_CHAIN_TOKENS = frozenset({"&&", ";"})
_CONDITIONAL_OR_PIPE_TOKENS = frozenset({"||", "|"})


def _split_sequential_subcommands(command: str) -> list[list[str]]:
    """Split a shell command into unconditionally sequenced subcommands (`&&` / `;`).

    Subcommands following `||` (failure-only fallback) or `|` (pipe consumer) are
    excluded until the next `&&` or `;` so conditional/piped tails cannot satisfy
    required static verification gates.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()

    subcommands: list[list[str]] = []
    current: list[str] = []
    skip_until_seq = False
    for token in tokens:
        if token in _SEQUENTIAL_CHAIN_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = False
        elif token in _CONDITIONAL_OR_PIPE_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = True
        elif not skip_until_seq:
            current.append(token)
    if current and not skip_until_seq:
        subcommands.append(current)
    return subcommands
```

Update `matches_cap(cap: list[str], command: str) -> bool` inside `check_python_tier_b()`:

```python
        def matches_cap(cap: list[str], command: str) -> bool:
            for sub in _split_sequential_subcommands(command):
                if sub == cap:
                    return True
                if len(cap) > 1 and sub[: len(cap) - 1] == cap[:-1]:
                    return True
                if len(sub) >= len(cap) and sub[: len(cap)] == cap:
                    return True
                if allow_historical_prefix:
                    prefix = _cap_tool_prefix(cap)
                    if prefix and len(sub) > len(prefix) and sub[: len(prefix)] == prefix:
                        return True
            return False
```

And update the fallback branch (when `python-quality.json` is absent) in `check_python_tier_b()`:

```python
    # Fallback tooling: ruff + (mypy / pyright / ty) across sequential subcommands
    has_ruff = False
    has_type_checker = False
    for r in tier_b_rows:
        for sub in _split_sequential_subcommands(r.command):
            prog = tc.strip_wrappers(list(sub))
            first = Path(prog[0]).name if prog else ""
            if first == "ruff":
                has_ruff = True
            if first in ("mypy", "pyright", "ty"):
                has_type_checker = True
```

And update `_check_python_tier_b_allowed_coverage()` (around line 940) to iterate `_split_sequential_subcommands(r.command)` instead of `shlex.split(r.command)` + `_split_subcommands(tokens)` so unspaced `;` and `||`/`|` handling is consistent across both checks.

In `skills/dev-designer/references/verification-rows.md` (immediately after line 57 `Report: pytest --junitxml=<path>.`):
Add a concise note:
> **Chained vs. split `TIER-B` rows:** `check_task_contract.py` splits unconditional sequential shell chains (`&&` and `;`) when matching registered `lint` and `type_check` capabilities (tails after `||` or `|` are excluded). Both a single chained `V4 | TIER-B` row and separate `V4`/`V5` `TIER-B` rows are valid.

- [ ] **Step 4: Run contract tests, doc tests, and ruff**

Run:
```bash
python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py && \
python3 -m pytest -q tests/test_ohk2_skill_docs.py && \
ruff format --check tests/test_ohk2_skill_docs.py && \
ruff check tests/test_ohk2_skill_docs.py
```
Expected: All tests PASS, 0 ruff errors.

- [ ] **Step 5: Commit Task 4**

```bash
git add skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-designer/references/verification-rows.md skills/dev-implementation/resources/scripts/test_check_task_contract.py tests/test_ohk2_skill_docs.py
git commit -m "[OBSERVER_HARDENING_BATCH2] Support sequential && and ; chains in TIER-B capability matching" -m "- add _split_sequential_subcommands rejecting || and | tails and apply it in check_python_tier_b matches_cap, fallback, and allowed-coverage checks" -m "- document chained vs split Python TIER-B grammar in verification-rows.md" -m "- add CompoundTierBMatchingTest regression coverage in test_check_task_contract.py"
```

- [ ] **Step 6: Full Repository Verification Gates (Post-Batch Acceptance)**

Run all five canonical quality gates from `.agents/quality/python-quality.json` inside `.worktrees/observer_hardening_batch2`:

```bash
ruff format --check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
python3 -m pytest -q --tb=short --maxfail=3 tests && \
bash scripts/verify.sh --full
```
Expected: All five gates PASS (exit 0) and `git -C /Users/danhdueexoictif/AllProjects/ai-agent-tools status --short` confirms `main` checkout is completely untouched.
