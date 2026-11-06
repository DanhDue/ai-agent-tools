---
id: "task_04_gate_approval_ledger"
status: "done"
priority: "high"
assignee: null
epic: "multi-epic-orchestration-and-governance"
dueDate: null
created: "2026-11-06T04:25:00Z"
modified: "2026-11-06T20:41:13Z"
completedAt: "2026-11-06T20:41:13Z"
labels: ["governance", "memory", "gates"]
order: "c4"
---

# Task 04: Structured Gate Approval Ledger in Project Memory

Epic: [multi_epic_orchestration_and_governance](multi_epic_orchestration_and_governance.en.md)

## Requirement Analysis

Resolve Observation #0020: developer gate approvals (`Gate 1`–`Gate 5`) and their exact scope or approved deviations (`Spec Errata`, parallel epic execution, or `--force` promotion) were previously recorded only in free-text prose inside `.devtool/state/<epic>.md`, which is subject to a 20-line truncation limit. Extending `scripts/resume_context.py` with a concurrency-safe Gate Approval Ledger (`--gate <1..5> --epic <slug> --approved "<scope>" [--deviations "<text>"]` and `--check-gate <1..5> --epic <slug>`) provides a permanent, queryable record in `.devtool/state/gate_ledger.jsonl` and `.devtool/GATE_LEDGER.md`.

## Files

Allowed files:
- `scripts/resume_context.py`
- `.gitignore`
- `tests/test_gate_approval_ledger.py` (new)

Read-only context:
- `.devtool/epic/multi_epic_orchestration_and_governance/multi_epic_orchestration_and_governance.en.md` (HLD specification)

## Design Rationale

Applicable skills: `python-quality-check`, `test-driven-development`.
1. `record_gate_approval(root: Path, epic_slug: str, gate: int, approved: str, *, deviations: str = "", by: str = "developer", repo: str | None = None) -> dict[str, object]` acquires `file_lock(devtool_dir)` (`fcntl.flock`), resolves the current short git commit SHA (`HEAD`) with `cwd=root`, appends a JSON line to `.devtool/state/gate_ledger.jsonl`, and calls `render_gate_ledger_markdown(devtool_dir)` to write `.devtool/GATE_LEDGER.md` (the tracked permanent Tier-1 record alongside `.devtool/PROJECT_LEDGER.md`, while `.devtool/state/gate_ledger.jsonl` stays ephemeral).
2. `check_gate_approval(root: Path, epic_slug: str, gate: int, *, repo: str | None = None) -> dict[str, object] | None` reads recorded gate approvals via `scan_gate_ledger` (reading `.devtool/state/gate_ledger.jsonl` when present and falling back to `.devtool/GATE_LEDGER.md` on fresh clones or worktrees) and returns the most recent approval record matching `(epic_slug, gate)` (or `None` if unapproved), allowing `--check-gate <1..5>` to exit `0` when approved and `1` when missing.
3. Default context harvesting (`main()`, `collect_harvest_data()`, and `harvest_json()`) includes recorded gate approvals for the active epic so restored sessions immediately see which gates (`Gate 1`–`Gate 5`) have passed and with what scope/deviations.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/resume_context.py`: `parse_args`, `main`, `collect_harvest_data`, `harvest_json`, new `record_gate_approval`, new `check_gate_approval`, new `render_gate_ledger_markdown`, and new `scan_gate_ledger`.
- **Downstream Callers**: `dev-lifecycle`, `dev-designer`, `dev-implementation`, and `save-context`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on new gate ledger functions in `scripts/resume_context.py`.

### BDD SCENARIOS

Covers: MEO-HP-04, MEO-AR-01, MEO-FR-03

```gherkin
  Scenario: [MEO-HP-04] [Tier C - Integration] Gate approval ledger records structured Gate 1-5 approvals and answers --check-gate queries
    Given a repository with ".devtool/" project memory
    When "scripts/resume_context.py --gate 2 --epic sample-epic --approved 'HLD and 5 Kanban tasks' --deviations 'SE-01'" is executed
    Then ".devtool/state/gate_ledger.jsonl" records a JSON entry with "epic": "sample-epic", "gate": 2, "approved": "HLD and 5 Kanban tasks", "deviations": "SE-01", and the current commit SHA
    And ".devtool/GATE_LEDGER.md" is rendered with the Gate 2 approval row
    And "scripts/resume_context.py --check-gate 2 --epic sample-epic" outputs the approval record and exits with code 0

  Scenario: [MEO-AR-01] [Tier A - Unit] Concurrent resume_context.py --gate invocations serialize under fcntl.flock without losing approval records
    Given 4 parallel subprocesses invoking "scripts/resume_context.py --gate <n> --epic concurrent-epic --approved 'Gate <n> scope'" simultaneously
    When all 4 subprocesses complete
    Then ".devtool/state/gate_ledger.jsonl" contains 4 valid JSON lines with 0 interleaved or truncated records
    And ".devtool/GATE_LEDGER.md" contains all 4 gate approval rows

  Scenario: [MEO-FR-03] [Tier A - Unit] resume_context.py rejects --gate with empty --approved text and exits 1 on --check-gate for unapproved gates
    Given a repository where Gate 3 has not been approved for "sample-epic"
    When "scripts/resume_context.py --check-gate 3 --epic sample-epic" is executed
    Then it exits with code 1 and reports that Gate 3 is not yet recorded for "sample-epic"
    And when "scripts/resume_context.py --gate 3 --epic sample-epic --approved ''" is executed with an empty approval scope
    Then it exits with code 2 without modifying ".devtool/state/gate_ledger.jsonl"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest tests/test_gate_approval_ledger.py::test_MEO_HP_04_record_and_check_gate_approval` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest tests/test_gate_approval_ledger.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/resume_context.py tests/test_gate_approval_ledger.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent scripts/resume_context.py tests/test_gate_approval_ledger.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest tests/test_gate_approval_ledger.py --junitxml=build/test-results/task_04_gate_ledger.xml` | exit 0; results build/test-results/task_04_gate_ledger.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- In `.gitignore`:
  - `.devtool/GATE_LEDGER.md` is the tracked permanent Tier-1 record alongside `.devtool/PROJECT_LEDGER.md` while `.devtool/state/gate_ledger.jsonl` stays ephemeral in `.devtool/state/`. Add an explicit `!.devtool/GATE_LEDGER.md` entry in `.gitignore`.
- In `scripts/resume_context.py`:
  - Add CLI flags to `parse_args()`:
    - `--gate`: `type=int, choices=[1, 2, 3, 4, 5], help="Record gate approval (1..5)"`
    - `--approved`: `type=str, default="", help="Approved scope description for --gate"`
    - `--deviations`: `type=str, default="", help="Approved deviations or Spec Errata IDs for --gate"`
    - `--by`: `type=str, default="developer", help="Approver identity for --gate"`
    - `--check-gate`: `type=int, choices=[1, 2, 3, 4, 5], help="Check if gate (1..5) is approved for --epic"`
  - When `args.gate is not None`:
    - Validate that `args.approved.strip()` is non-empty; if empty, print `"error: --approved must be non-empty when recording --gate"` to `stderr` and `sys.exit(2)`.
    - Call `record_gate_approval(target_root, active_epic, args.gate, args.approved.strip(), deviations=args.deviations.strip(), by=args.by.strip() or "developer", repo=args.repo)`.
  - `record_gate_approval(...)` acquires `file_lock(devtool_dir)`, ensures `(devtool_dir / "state").mkdir(parents=True, exist_ok=True)`, resolves `commit_sha` via `subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root, check=False, capture_output=True, text=True)` (with `"unknown"` fallback), appends JSON line `{"timestamp": now_utc_iso, "epic": epic_slug, "gate": gate, "commit": commit_sha, "approved": approved, "deviations": deviations, "by": by}` to `devtool_dir / "state" / "gate_ledger.jsonl"`, and calls `render_gate_ledger_markdown(devtool_dir)` to write `devtool_dir / "GATE_LEDGER.md"` with a Markdown table `| Timestamp | Epic | Gate | Commit | Approved Scope | Deviations | By |`.
  - `scan_gate_ledger(root: Path, epic_slug: str | None = None) -> list[dict[str, object]]` reads `devtool_dir / "state" / "gate_ledger.jsonl"` when present and falls back to parsing the Markdown table rows of `devtool_dir / "GATE_LEDGER.md"` when `gate_ledger.jsonl` is absent (e.g. on a fresh clone or worktree). `collect_harvest_data` adds a `"gate_approvals"` key from `scan_gate_ledger(root, epic_slug=epic_filter)`.
  - When `args.check_gate is not None`:
    - Call `rec = check_gate_approval(target_root, active_epic, args.check_gate, repo=args.repo)`: if `rec` is found, print `json.dumps(rec)` and `sys.exit(0)`; if `None`, print `f"Gate {args.check_gate} is not yet recorded for epic '{active_epic}'"` to `stderr` and `sys.exit(1)`.

## Definition of Done

- `scripts/resume_context.py` supports `--gate` and `--check-gate` with `fcntl.flock` protection, writing `.devtool/state/gate_ledger.jsonl` and `.devtool/GATE_LEDGER.md` (`MEO-HP-04`, `MEO-AR-01`, `MEO-FR-03`). (V2, V5)
- `ruff` and `mypy` pass with zero errors. (V3, V4)
- Automated tests pass and write JUnit XML results. (V5)
- Clean git working tree with changes restricted to Allowed files. (Gate 5)

## Dependencies & Blockers

- None (Wave 1).

## References & Rollback

- Reference: [2026-11-06-multi-epic-orchestration-and-governance-design.en.md](2026-11-06-multi-epic-orchestration-and-governance-design.en.md).
- Rollback: `git revert` the task commit to remove Gate Approval Ledger flags from `scripts/resume_context.py`.
