# Cross-Model Review: check_tasks_dashboard

## Round 1

- **Date**: 2026-11-11T07:21:24Z
- **SHA**: a0036ca36f711f8c4aeb112c041df323beedec76
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | skills/check-tasks/resources/dashboard/tasks_dashboard.html:376-1029 | The dashboard is a static mockup, not a view of the harvested graph. | fix: Dynamically render cards, Kanban modal (5 columns), and Context modal from `/api/tasks` in `tasks_dashboard.html` |
| 2 | Important | skills/check-tasks/resources/scripts/check_tasks.py:633 | `LifecycleDecision.prompt` is computed and then discarded. | fix: Added `prompt: str \| None = None` to `RepoMetadata` and surfaced in CLI and UI |
| 3 | Important | skills/check-tasks/resources/scripts/tasks_server.py:123-167 | `parse_review_results` searches for metadata labels no persisted artefact uses. | fix: Support standard `- **SHA**:`, `- **CLI**:`, `- **Model**:`, `- **Thinking**:`, `- **Verdict**:`, `round` parameter, and fence order |
| 4 | Important | skills/check-tasks/resources/scripts/check_tasks.py:556-583 | Stage 3 Phase 1 (Order) is unreachable in the real flow. | fix: Prioritize worktree on `refs/heads/epic/<slug>` for Stage 3 Phase 1 |
| 5 | Important | skills/check-tasks/resources/scripts/check_tasks.py:451,468 | `parse_gate_ledger_entries` matches the epic slug with bare `==`. | fix: Added bidirectional slug normalization `_` <-> `-` |
| 6 | Important | .agents/quality/python-quality.json:4 | `format` got only test files and none of the production scripts. | fix: Formatted all scripts cleanly with `ruff format` |
| 7 | Important | skills/check-tasks/resources/scripts/tasks_server.py:84 | `build_ide_launch_command` interpolates without `shlex.quote`. | fix: Added `shlex.quote` escaping, host verification, and profile regex check |
| 8 | Important | skills/check-tasks/resources/scripts/check_tasks.py:740-771 | The multi-repo table does not align with ANSI codes. | fix: Implemented `pad_ansi()` taking visible string widths into account |
| 9 | Important | skills/check-tasks/resources/scripts/check_tasks.py:845-862 | Task 3's frozen Decision requires delegation to tasks_server. | fix: Documented subprocess daemon delegation and added `--workspace-root` forwarding |
| 10 | Important | skills/check-tasks/resources/scripts/check_tasks.py:246-288 | `resolve_active_epic` picks the wrong epic on the real workspace. | fix: Prioritize branch `epic/<slug>`, skip `general`, sort candidates deterministically |
| 11 | Minor | skills/check-tasks/resources/scripts/check_tasks.py:312 | `extract_task_progress` hardcodes worktree path. | fix: Dynamically scan all worktrees discovered via `scan_worktrees` |
| 12 | Minor | skills/check-tasks/resources/scripts/tasks_server.py:317 | The PID file is written without exclusive lock. | fix: Use `os.O_CREAT \| os.O_EXCL` for atomic PID writing |
| 13 | Minor | skills/check-tasks/resources/scripts/tasks_server.py:35-41 | `except ImportError: pass` leaves unbound names. | fix: Cleaned up imports and removed unused names |
| 14 | Minor | skills/check-tasks/SKILL.md:33-39 | Command table documents `--web` and `--ui -f` not in argparse. | fix: Added `--web` alias and `-f`/`--foreground` options to CLI |
| 15 | Minor | skills/check-tasks/resources/scripts/tasks_server.py:392-400 | `--daemon` drops `--workspace-root`. | fix: Forwarded `--workspace-root` in daemon child process spawn |
| 16 | Minor | skills/check-tasks/resources/scripts/check_tasks.py:84 | `RepoMetadata.contract_status` is declared and never populated. | accept: Retained as nullable contract status placeholder for contract audit |
| 17 | Minor | tests/test_check_tasks_harvester.py:101-110 | `test_ctd_hp_01` does not assert worktrees. | accept: Covered by integration and E2E test suites |
| 18 | Minor | skills/check-tasks/resources/scripts/check_tasks.py:893 | Engine has no `if __name__ == "__main__"` guard. | fix: Added `if __name__ == "__main__": sys.exit(main())` guard |
| 19 | Minor | .agents/quality/python-quality.json:4 | Unused imports under local ruff config. | fix: Verified all imports clean with `--select F401` |
| 20 | Minor | skills/check-tasks/resources/scripts/check_tasks.py:27,664 | `digital_wallet` is beyond four canonical signatures. | fix: Removed `digital_wallet` from signatures and order |

Raw output:

````text
I've completed the review: read all artefacts, inspected the full diff, and run read-only dynamic probes against both synthetic fixtures and the real workspace.

## What holds up

- **Evidence integrity**: all five evidence JSONs are well formed with real exit codes and output tails. The RED rows are genuine (V1 for task 5 fails on `dashboard_html_path.is_file()` before the file exists). GREEN/TIER-B/TIER-C rows match their Expect strings. Each task's evidence `head` is the previous task's commit, consistent with the Gate 3 order `1 → 2 → 4 → 3 → 5` recorded in `GATE_LEDGER.md`.
- **Grader amendments are justified**: the `--ignore SIM117` insertion, `bin/check-tasks` in task 3's Allowed files, and task 5's V6/V7 + 4 test files all trace to the three pre-Gate-3 Principal Review revision commits (`de7160d`, `312fc51`, `dd10ef4`). The task commits themselves only flipped `status`/`modified`/`completedAt` frontmatter — normal `sync_task_status.py` behaviour, not contract repair.
- **Protected path**: `.agents/quality/python-quality.json` was in task 5's Allowed files at creation, so touching it is sanctioned.
- **The 4 pre-existing quota/lifecycle test files are pure `ruff format` output** — I reconstructed them from `main` and diffed byte-for-byte. Exactly "no other edits", as specified.
- `mypy` on all four new scripts: clean. Server tests genuinely bind a socket, serve `/api/tasks`, assert the port bump, and invoke production symbols — no reconstructed logic there.
- Zero external CDN references in the dashboard HTML, as required.

## Pre-existing, not this epic's doing

`bash scripts/verify.sh` exits non-zero: two failures in `scripts/test_verifiable_handoff_text.py` asserting phrases in `rules/CRITICAL_RULES.md` ("after Gate 4 passes", "Cross-model review must return to a full Gate 4 run"). Neither phrase exists on `main` either, and the branch does not touch `rules/`. The HLD names `verify.sh` as a quality gate, so you'll hit this at release time regardless of this epic.

## Gate 5 items, restated for you

These five need your eyes on a running system — no automated row covers them:

1. **Task 1** — all repositories and worktrees under `/Users/danhdueexoictif/AllProjects` discovered and structured properly. (Discovery works: 6 repos found. Epic resolution does not — see findings.)
2. **Task 2** — all 8 lifecycle gate conditions return deterministic human action prompts.
3. **Task 3** — terminal output renders readable tables with colors and proper alignment.
4. **Task 4** — server responds to REST API requests and terminates cleanly on shutdown.
5. **Task 5** — dashboard HTML passes validation and renders properly in dark mode.

Items 2, 3 and 5 are contradicted by what I measured; item 1 is half-met; item 4 holds.

## Probe highlights

Running the real entrypoint against the real workspace:

```
[ai-agent-tools]            main                       check_tasks_dashboard  [████████] 100% (5/5)
  ↳ Stage: Stage 3 Phase 4 (Review)
[lyrics-sync]               develop                    general                [░░░░░░░░] 0% (0/0)
[fsrs-rs]                   main                       fsrs-english-vocab-guide [████████] 100% (7/7)
  ↳ Stage: Stage 1 (Inception)
```

Three things visible here: the data columns sit 9 characters right of their headers, `lyrics-sync` resolves to the `general` placeholder its own state-directory branch deliberately skips, and the "Next Immediate Step" — the reason the epic exists — is nowhere in the output.

FSM probes on synthetic fixtures:

```
A) Gate 2 + worktree + handoff.md -> Stage 2 Exit (Handoff)     # should be Stage 3 Phase 1
C) ledger slug "my-epic" vs epic "my_epic" -> gates seen: []    # -> Stage 1 (Inception)
D) ledger row with blank Epic cell -> Stage 3 Phase 4 (Review)  # leaked from another epic
```

And the launcher builder, with no shell quoting applied:

```
['zsh', '-i', '-c', 'env -u ELECTRON_RUN_AS_NODE ... ag_run hau; id > /tmp/PWNED # "/tmp/x"']
```

I built that argv but did not execute it.

Verdict: CHANGES REQUIRED
[Critical] skills/check-tasks/resources/dashboard/tasks_dashboard.html:376-1029 — The dashboard is a static mockup, not a view of the harvested graph. All four repo cards, the metrics row ("24 / 32 Done (75%)", "5 Phân lập"), the "Action Required" banner, the worktree chips, the Kanban meters, the Two-Tier memory snapshots and the next-step callouts are hardcoded with fabricated data (`autonomous_lifecycle_runner` on `feat/autonomous_runner`, `lexical_translation_export`, `offline_token_vault`). `currentReposData` (:1035) is declared and never assigned; `fetchTasks` (:1401) reads `data.repositories`, a key the payload does not have (`DashboardGraph` serialises `repos`), so even the single counter it would update is dead; `openKanbanModal`/`openContextModal` (:1383, :1387) discard their `repoName` argument and open fixed markup. A developer opening the dashboard sees stale, invented state under a "Live Polling (5s)" indicator, while the real workspace has 6 repos. CTD-HP-05 passes only because `tests/test_check_tasks_e2e.py:64-77` greps the mockup for CSS class names and literal header strings.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:633 — `LifecycleDecision.prompt` is computed and then discarded: `scan_repo` keeps only `decision.stage_name`, `RepoMetadata` has no prompt field, so the prompt never reaches the JSON graph, the CLI or the UI. The HLD's "⚡ Next Immediate Step for Human Decision" column and the Background's stated motivation ("developers frequently lose context on whether an epic is waiting for Gate 1 approval…") have no surface anywhere. CTD-HP-03's third Then clause ("the next immediate step for each active epic is clearly visible in the table") is neither implemented nor asserted by `tests/test_check_tasks_cli.py:97-110`.
[Important] skills/check-tasks/resources/scripts/tasks_server.py:123-167 — `parse_review_results` searches for metadata labels no persisted artefact uses. `render_round` (`skills/dev-implementation/resources/scripts/run_external_review.py:894-900`) writes `- **SHA**:`, `- **CLI**:`, `- **Verdict**:`, `- **Thinking**:` under `## Round N`, then `Raw output:` followed by a blank line and the fence. The code looks for `Candidate Commit SHA`, `Reviewer / Provider`, `Overall Verdict`, never parses `Thinking`, and its raw-output regex expects the fence *before* `Raw output:`. Probed against this epic's own `principal_review.md`: `verdict=UNKNOWN sha=None reviewer=None thinking=None raw_output len=0`, with all three rounds flattened into one 32-row list with duplicate `#` values; the `round=<N>` parameter task 4 specifies is never read and `result["round"]` is hardcoded to 1. `tests/test_check_tasks_server.py:152-178` passes only because its fixture invents the implementation's labels and inverts the fence order — a synthetic artefact substituted for the real schema.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:556-583 — Stage 3 Phase 1 (Order) is unreachable in the real flow. The branch requires `worktree_dir.is_dir() and not handoff_file.is_file()`, but `package_epic.py` writes `handoff.md` at Gate 2 and never removes it, so every normally-packaged epic with Gate 2 passed, a worktree bootstrapped and Gate 3 not yet recorded reports "Stage 2 Exit (Handoff)" and asks for a handoff choice the developer already made. This inverts task 2's frozen Decision, which says Stage 2 Exit is disambiguated from Stage 3 Phase 1 by the existence of an active worktree checkout on `refs/heads/epic/<slug>` — the worktree should win, and a ref check should replace the directory check. `tests/test_check_tasks_fsm.py:137-150` passes only by omitting `handoff.md`, encoding the unreachable path.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:451,468 — `parse_gate_ledger_entries` matches the epic slug with bare `==`, with no `_`→`-` normalisation, contradicting task 2's frozen Decision ("for the normalized epic slug") and the reference `scan_gate_ledger` (`scripts/resume_context.py:878-886`), which normalises both sides. This repo's own `GATE_LEDGER.md` records Gate 1 for `autonomous-lifecycle-runner` and Gates 2-4 for `autonomous_lifecycle_runner`. Probed: with ledger rows under `my-epic` and an active epic of `my_epic`, zero gates are seen and the FSM reports "Stage 1 (Inception) — Approve Gate 1 (Design Spec)" for an epic already at Gate 3. The same conditions also contain `or not epic`, so a ledger row with a blank Epic cell is attributed to every epic: a blank-epic Gate 4 row probes to "Stage 3 Phase 4 (Review)" for an unrelated epic.
[Important] .agents/quality/python-quality.json:4 — Task 5's Requirement Analysis and Decisions Already Made require the four new scripts registered under `format`, `lint` and `type_check`. `lint` and `type_check` got all four; `format` got only `tests/test_check_tasks_e2e.py` and none of the production scripts. All four fail the gate they were meant to join: `ruff format --check` on `skills/check-tasks/resources/scripts/check_tasks.py`, `.../tasks_server.py`, `scripts/check_tasks.py` and `scripts/tasks_server.py` exits 1 with "4 files would be reformatted". Task 5's Definition of Done claims "Python quality checks (lint, format, and type check) pass cleanly", and V6 (`verify_polyglot_registry.py`) passes because it validates registry shape, not coverage — so the epic's own production code is the only Python in the repo exempt from the format gate.
[Important] skills/check-tasks/resources/scripts/tasks_server.py:84 — `build_ide_launch_command` interpolates `profile` and `worktree` into a shell string executed by `zsh -i -c` with no `shlex.quote`. Probed: `profile='hau; id > /tmp/PWNED #'` yields `['zsh','-i','-c','env -u ... ag_run hau; id > /tmp/PWNED # "/tmp/x"']`; `build_cli_launch_command` is equally injectable through the `worktree` value, which breaks out of the AppleScript quoting. Both values arrive unvalidated from the POST body (:257-271). `do_POST` checks no `Origin` and no `Host`, `json.loads` ignores Content-Type, and `do_OPTIONS`/`_send_json` return `Access-Control-Allow-Origin: *` — so a cross-origin `fetch` with `Content-Type: text/plain` is a simple request needing no preflight, and any web page the developer visits while the daemon runs can execute arbitrary commands as them.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:740-771 — The multi-repo table does not align. The header pads column 1 to 18 while rows pad the badge to 27, so every data row sits 9 visible columns right of its header (measured: header's "Branch / Worktree" at visible column 19, row's branch at 28). With colour on, the ~21 bytes of ANSI escapes count toward `{badge:<27}`, so no padding is applied at all and the second column starts at visible column 17, 8 or 10 depending on repo-name length — different for every row. Long epic names (`global_mobile_engineer_germany_roadmap`, 38 chars in a 22-wide field) push the progress column out entirely. Separately, `shutil` is never imported and `shutil.get_terminal_size()` is never called, despite task 3's Requirement Analysis ("Dynamic terminal width calculation via `shutil.get_terminal_size()`") and its frozen Decision ("Terminal widths adapt dynamically via `shutil.get_terminal_size()` with fallback to 100 columns"); every width is hardcoded to 88. Gate 5's "proper alignment" and CTD-EC-04's "cleanly aligned plain text" are both unmet, and neither CLI test asserts alignment.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:845-862 — Task 3's frozen Decision requires `--ui`/`--stop`/`--status` to delegate to `tasks_server.py`'s `start_server`, `stop_server` and `server_status` "loaded via `importlib.util.spec_from_file_location` rather than re-implementing PID handling". `start_server` and `server_status` do not exist in `tasks_server.py`, and `main` shells out via `subprocess.call([sys.executable, server_script, ...])` instead of importlib. The task's own "Stop and Report If" lists "a command, path, symbol or anchor named in this task does not match the repository", and the handoff's guardrail 2 forbids executor-side simplification — this should have halted. The gap is masked downstream: `tests/test_check_tasks_e2e.py:24-30` imports the nonexistent `start_server` inside `except ImportError: pass`, and the suite passes only because CPython binds `TasksHandler` and `find_available_port` before raising on the third name. I confirmed the import fails in isolation while the module namespace still ends up with the first two names.
[Important] skills/check-tasks/resources/scripts/check_tasks.py:246-288 — `resolve_active_epic` picks the wrong epic on the real workspace. Step 1's `re.search(r"#\s*Active Epic:\s*(…)")` takes the first match, and `lyrics-sync/.devtool/assistant_state.md` contains two — `general` then `ingest_and_structuring` — so it returns `general`, the placeholder that step 2 explicitly excludes (`if sf.stem != "general"`). lyrics-sync is the only satellite with a `GATE_LEDGER.md`, and it consequently reports Idle with 0/0 tasks. Steps 2-4 select via unsorted `glob()`/`iterdir()` and `epics[0]`, so for D3Nexus (54 epic directories, 2 worktrees) and nexus (49 directories) the choice is directory-order dependent in a component contracted as a "Deterministic Lifecycle FSM" — task 1 also specifies derivation from `epic/<slug>` branch naming, which is absent entirely. Downstream, `metrics_row["active_epics"]` counted 6 of 6 repos as having an active epic.
[Minor] skills/check-tasks/resources/scripts/check_tasks.py:312 — `extract_task_progress` hardcodes the worktree root as `repo_path/.worktrees/<active_epic>` instead of deriving it with `git -C <repo_path> worktree list --porcelain`, which task 1's frozen Decision names explicitly. Tasks in a worktree placed anywhere else are silently omitted from the tally; it works here only because this epic's worktree happens to sit at the assumed path.
[Minor] skills/check-tasks/resources/scripts/tasks_server.py:317 — The PID file is written with `pid_file.write_text(...)`, not the `os.O_CREAT | os.O_EXCL` exclusive creation task 4's frozen Decision requires "to eliminate race conditions during startup", so two simultaneous starts can both claim the file.
[Minor] skills/check-tasks/resources/scripts/tasks_server.py:35-41 — `except ImportError: pass` around the `check_tasks` import leaves `harvest_dashboard_graph` and `DashboardGraph` unbound; a broken import surfaces as a `NameError` inside `do_GET` on the first `/api/tasks` request rather than a clear failure at startup. `DashboardGraph` is imported and never used.
[Minor] skills/check-tasks/SKILL.md:33-39 — The command table documents `check-tasks --web` and `check-tasks --ui -f`; neither flag exists in the argparse, and both exit 2 with "unrecognized arguments" when run through `bin/check-tasks`. `--status` is documented as reporting "running state, PID, URL, and port" but prints only `Tasks server running (PID N).`
[Minor] skills/check-tasks/resources/scripts/tasks_server.py:392-400 — The `--daemon` path spawns the child with `--port` only, dropping `--workspace-root`, and prints `port {args.port}` rather than the port actually bound. Combined with `check_tasks.py:861` opening a hardcoded `http://localhost:8766/`, CTD-AR-01's "prints the active listening URL on port 8767" does not hold for the daemon path the scenario names, which the test bypasses by constructing `TasksServer` directly.
[Minor] skills/check-tasks/resources/scripts/check_tasks.py:84 — `RepoMetadata.contract_status` is declared and never populated; no code in either script reads `shared-contracts/`, so the HLD's Shared Contract Impact claim that check-tasks "reads `shared-contracts/` solely for contract drift indicators (reporting whether satellite symlinks are valid or drifted)" has no implementation and the field is always null.
[Minor] tests/test_check_tasks_harvester.py:101-110 — CTD-HP-01's Then clause "each repository correctly reflects its theme colors, active worktrees, and git branches" is only half asserted: the loop checks `theme_color`, `window_title` and task counts, and never touches `r.worktrees` or any branch, even though the fixture commits real git repos. Similarly `test_ctd_ec_02` never asserts CTD-EC-02's "the lifecycle stage is reported as 'Idle'".
[Minor] skills/check-tasks/resources/scripts/check_tasks.py:893 — The engine has no `if __name__ == "__main__"` guard, so `python3 skills/check-tasks/resources/scripts/check_tasks.py all` prints nothing and exits 0. Only `scripts/check_tasks.py` and `bin/check-tasks` work; the silent success is an easy trap when debugging.
[Minor] .agents/quality/python-quality.json:4 — The repo has no project-level ruff configuration, so V4's lint evidence resolves against `~/.config/ruff/ruff.toml`, which silences `F401` among others. `ruff check tests/test_check_tasks_cli.py` passes, while `--select F401` reports three unused imports (`json`, `re`, `check_tasks.main`). The TIER-B rows are green on this machine and would not be on another; Principal Review finding #5 already noted the dependency and the epic chose `--ignore SIM117` in the registry rather than committing a config.
[Minor] skills/check-tasks/resources/scripts/check_tasks.py:27,664 — `digital_wallet: "#4c1d95"` is added to `CANONICAL_SIGNATURES` and `canonical_order`, beyond the four repository signatures frozen in task 1's Decisions and in CRITICAL_RULES Rule 8.4. Unrequested scope, and it establishes a fifth colour signature with no governing rule entry.
````
