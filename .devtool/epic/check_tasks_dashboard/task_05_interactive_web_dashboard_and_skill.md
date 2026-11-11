---
id: "task_05_interactive_web_dashboard_and_skill"
status: "todo"
priority: "high"
assignee: null
epic: "check_tasks_dashboard"
dueDate: null
created: "2026-11-11T08:30:00Z"
modified: "2026-11-11T08:30:00Z"
completedAt: null
labels: ["frontend", "skill", "integration"]
order: "a5"
---

# Task 5: Interactive Dark Mode Web Dashboard UI, Skill Definition, and End-to-End Acceptance

Epic: [check_tasks_dashboard](check_tasks_dashboard.en.md)

## Requirement Analysis

Implement the web companion frontend, Antigravity skill metadata, and end-to-end integration:
1. Web Companion UI in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`:
   - Single-file HTML5, modern CSS3 (Dark Theme inspired by Antigravity visual companion), and Vanilla ES6 JavaScript.
   - Zero external CDN dependencies (uses local SVG icons and CSS variables).
   - Real-time polling (`fetch('/api/tasks')` every 5 seconds) or SSE support.
   - Project cards displaying:
     - Header badge with repository signature color (`ai-agent-tools`, `lyrics-sync`, `nexus`, `D3Nexus`).
     - Window title, active branch, active epic name, and lifecycle stage pill.
     - Worktree chips showing branch name, detached commit SHA, and dirty working tree counters.
     - Kanban progress meter with task counts (`done`, `in_progress`, `todo`) and percent bar.
     - Two-Tier Memory snapshot: permanent milestones and recent assistant role.
     - "⚡ Next Immediate Step / Human Decision" callout with color-coded severity.
     - Action buttons: `[ 🔬 Review ]`, `[ 💻 Mở CLI ]`, `[ 🚀 Mở IDE ]`.
   - Cross-Model Review Modal:
     - Header metadata: Candidate SHA, Reviewer Model, Thinking Level, Verdict.
     - Round Selector: Tabs for Round 1, Round 2, Round 3.
     - 7-Column Triage Table: `#`, `Severity`, `Location`, `Problem`, `Assessment`, `Evidence`, `Proposed action`.
2. Antigravity Skill Definition in `skills/check-tasks/SKILL.md`:
   - Frontmatter metadata: `name: check-tasks`, `description: Real-time Cross-Repo Tasks & Context Dashboard and CLI monitor`.
   - Detailed documentation on slash command `/check-tasks`, CLI usage, and architecture.
3. Registration & Verification:
   - Register skill in `.agents/quality/python-quality.json` capabilities list.
   - Integration acceptance test suite in `tests/test_check_tasks_e2e.py` validating the full cycle from scanning to dashboard HTML rendering.

## Files

Allowed files:
- `skills/check-tasks/resources/dashboard/tasks_dashboard.html` (new)
- `skills/check-tasks/SKILL.md` (new)
- `tests/test_check_tasks_e2e.py` (new)
- `.agents/quality/python-quality.json`

Read-only context:
- `skills/check-quota/resources/dashboard/quota_dashboard.html` — dark theme tokens, modal styles, and layout patterns
- `.devtool/epic/check_tasks_dashboard/check_tasks_dashboard.en.md` — UI Specification

## Design Rationale

Self-contained vanilla HTML/CSS/JS eliminates compilation steps, web server complex routing, and bundle size bloat, making the dashboard instantly accessible via browser or embedded iframe. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `skills/check-tasks/SKILL.md`, `tests/test_check_tasks_e2e.py`.
- **Downstream callers**: End users, Antigravity chat embeddings, and browser companion users.
- **Cross-platform bridges**: HTML / CSS / JavaScript UI.
- **Target test coverage threshold**: 100% of DOM structures and API bindings.

### BDD SCENARIOS

Covers: CTD-HP-05

```gherkin
Scenario: [CTD-HP-05] [Tier C - Integration] Interactive web dashboard displays project cards and review modal

Given the web server is running and serving tasks_dashboard.html
When the user accesses the dashboard in a browser
Then the interface renders dark mode cards for all repositories
And clicking a review button opens a modal displaying the candidate SHA, reviewer model, and the 7-column triage table
And clicking an IDE launch button triggers a POST request to /api/launch/ide without throwing errors
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest tests/test_check_tasks_e2e.py -k test_ctd_hp_05` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest tests/test_check_tasks_e2e.py -k test_ctd_hp_05` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest tests/test_check_tasks_e2e.py` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_check_tasks_e2e.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py tests/test_check_tasks_e2e.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_5.xml tests/test_check_tasks_e2e.py` | exit 0; results build/test-results/task_5.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
- A variable named in the Needs column is unset.
- Dashboard HTML requires external internet or CDN resources to render.

## Decisions Already Made

- The web companion uses purely vanilla JavaScript, CSS variables, and HTML5.
- Modal dialogs use `<dialog>` HTML element with backdrop blur and dark background.
- Review triage tables are rendered client-side from the JSON response of `/api/review`.
- The dashboard is registered in `.agents/quality/python-quality.json` and supported by `/check-tasks`.

## Definition of Done

- Scenario CTD-HP-05 is covered and passes in the test suite. (V2, V3, V6)
- Python quality checks (lint and type check) pass cleanly. (V4, V5)
- Dashboard HTML passes validation and renders properly in dark mode. (Gate 5)

## Dependencies & Blockers

Requires [Task 1](task_01_harvester_engine_and_data_models.md), [Task 2](task_02_deterministic_lifecycle_fsm_engine.md), [Task 3](task_03_terminal_cli_and_ansi_reporter.md), and [Task 4](task_04_http_daemon_server_and_rest_api.md).

## References & Rollback

- [Epic HLD](check_tasks_dashboard.en.md), Web Dashboard & Skill Specification.
- **Rollback**: Revert task commit; deletes `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `skills/check-tasks/SKILL.md`, and `tests/test_check_tasks_e2e.py`.
