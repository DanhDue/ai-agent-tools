# Principal Review: autonomous_lifecycle_runner

## Round 1

- **Date**: 2026-11-10T14:57:35Z
- **SHA**: bd893c79a49a028c57558b6ee709d4e58d2fb471
- **Base**: main
- **CLI**: kiro
- **Model**: claude-opus-5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:High-Level Architecture and Sequence Diagram (and task_3 Requirement Analysis item 1) | `run_external_review.py run --stage principal` does not exist; the CLI takes `--kind {code,principal,epic}` with `--epic-dir` and a required `--base` (run_external_review.py:1760-1763), so the first Stage 2 dispatch exits 2 with an argparse error. Proposed: replace every `--stage principal` with `run --kind principal --epic-dir <epic_dir> --base <base> --auto-quota` and spell the cross-model call as `run --kind code --epic-dir <epic_dir> --base <base> --auto-quota`, in both HLD variants and task_3. | fixed in 04b1ad8 |
| 2 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts (`evaluate_circuit_breakers`) and Feature Maintenance Map, task_3/task_4 Requirement Analysis | the runner re-derives the Circuit Breakers from fixtures instead of using `run_external_review.py triage`, whose `## Auto-Triage Gate` already emits AUTO_PASS_CLEAN, AUTO_PASS_FINAL_MINOR_SWEEP, AUTO_FIX_ELIGIBLE, AUTO_PASS_FINAL_SWEEP and the three CIRCUIT_BREAKER_HALT actions (run_external_review.py:1614-1687). No artefact says what the runner does on AUTO_PASS_FINAL_MINOR_SWEEP (CRITICAL_RULES §6 says finish without another review round; task_3 says start the next round) or on AUTO_PASS_FINAL_SWEEP (Round 3 with Important findings left). No task writes `fixed in <sha>` / `dismissed: …` decision cells, yet FIX_LOOP only fires on those cells (line 1630) and `check` blocks Phase 4 while they are missing (lines 1470-1474). BDD ALR-FR-02 also says "identical file and issue" where the source compares the file path only. Proposed: add a Decisions Already Made rule that the runner parses `- **Action**:` from `triage --kind <principal\|code> --epic-dir <dir>`; add a per-stage table mapping each Action to a runner transition (including the Tier 1 rule that Minor-only Principal rounds go to the Human batch); make task_3 and task_4 own writing decision cells into `principal_review.md` / `review_results.md` after each fix; reword ALR-FR-02 to "same file path". | fixed in 04b1ad8 |
| 3 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Architecture and Technical Design (no commit policy), task_3/task_4 Decisions Already Made | `run_external_review.py run` refuses any dirty tree (lines 1241-1243). The runner leaves untracked or modified files between rounds: `.devtool/GATE_LEDGER.md` (not ignored, `.gitignore:13`), `fix_plan_round<N>.md`, the review ledgers, and the Assistant's revisions. The second review invocation in either stage therefore exits 2. Proposed: add a "Commit sequencing" decision listing which runner step commits which file and with which message (fix plan, Fix commits, review-ledger decisions, gate ledger, `package_epic.py --revise`), and require a `git status --porcelain` empty check before every `run`. | fixed in 04b1ad8 |
| 4 | Important | .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:Requirement Analysis item 4 (and task_2 Decisions Already Made "records `Gate 3 | CONFIRMED (autonomous)`") — `GATE_LEDGER.md` is a rendered view of `.devtool/state/gate_ledger.jsonl` (resume_context.py:813-854, 363). On re-render, `hydrate_gate_ledger_jsonl_if_needed` imports only rows with 7 or more cells (line 285), so a free-text ledger line written by the runner is silently dropped. That breaks ALR-ST-02 and ALR-EC-04. Proposed: require gate writes through `resume_context.py --gate <n> --epic <slug> --approved "<text>" --by lifecycle_runner` (or by importing `record_gate_approval`), and add `scripts/resume_context.py` to Read-only context in task_1 and task_2. | fixed in 04b1ad8 |
| 5 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `RunnerConfig` (and task_1 Decisions Already Made) | the default `assistant_model="claude-3-7-sonnet"` is not in `agy models` on this machine (only `claude-sonnet-5-5-*` / `claude-opus-5-5-*`), so the startup probe always fails without an override. The spec's model source, an `assistant` entry in `.devtool/review_config.json`, is deleted by every review round: `load_review_config` keeps only `last_used_provider` and `providers` (lines 111-121), and the probe confirmed the key is gone after `update_sticky_review_config`. Proposed: store the Assistant settings under `providers.assistant` (which survives the merge) or in a runner-owned file such as `.devtool/lifecycle_runner.json`; set a default the CLI actually lists (e.g. `claude-sonnet-5-5-high`); state the Assistant's `--mode` (plan for verdicts, auto only for `.devtool/` doc revisions). | fixed in 04b1ad8 |
| 6 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `StageName` / `prompt_human_principal_fixes` (and task_3 Decisions Already Made `[Y/N]`) | the Human checkpoint is a blocking stdin prompt with no saved state. When an agent launches the runner from `/dev-lifecycle --autonomous` through a bash tool (no TTY, tool timeout), `input()` raises EOFError (probed). A crash or exit while waiting has no stage to resume into. Proposed: add `StageName.AWAITING_PRINCIPAL_CONFIRMATION`; make the runner write the fix table to `.devtool/epic/<epic>/principal_fix_proposal_round<N>.md`, save state and exit with a dedicated code; resume with `--resume --confirm-fixes` / `--reject-fixes`. Also state that the Human launches the long-running runner in a terminal rather than inside an agent tool call. | fixed in 04b1ad8 |
| 7 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts and Kanban Tasks Breakdown | "Execute Gate 4 in full" has no contract or owner. Gate 4 is a multi-step procedure (smoke checklist commit, `run_external_review.py check`, `audit_epic.py`, the Integration results commands, `check_bdd_traceability.py --results`, and the agent skill `@quality_check`; dev-implementation/SKILL.md:317-358). No task owns `step_implementation`'s per-task protocol (`run_task_checks.py red/verify`, `sync_task_status.py`, one commit per task). Task_4 says the Programmer runs Gate 4, while the HLD sequence diagram says the Runner does. Proposed: add `run_gate4(self) -> Tuple[bool, str]` to Module Contracts with the exact command list (naming the script that replaces `@quality_check`), name who runs it, and assign `step_implementation` with that per-task protocol to task_2 (or a new task) via Covers and Decisions Already Made. | fixed in 04b1ad8 |
| 8 | Important | .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:BDD SCENARIOS Covers line | ALR-ST-01 ("resumes from the exact interrupted task") needs the `step_implementation` dispatch loop, and ALR-ST-02 (Gate 3/4/5 ledger sync) needs Gate 3 auto-order (task_2) and Gate 4 (task_4/task_5). Neither can pass at task_1, so V2, V3 and V6 cannot go green within task_1's scope. Proposed: move ALR-ST-02 to task_5 and either move ALR-ST-01 to the task that owns `step_implementation` or reword it to state-level resume (`load_or_init_state` returns the saved stage, `completed_tasks` and round). | fixed in 04b1ad8 |
| 9 | Important | .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:Verification V4/V5 (identical rows in task_2..task_5) | V4 already fails today with 12 SIM117 errors in `tests/test_agy_quota.py` and `tests/test_claude_quota.py`, which are outside Allowed files (ruff falls back to `~/.config/ruff/ruff.toml` because the repo has no config). V5 fails with `import-not-found` on a test that imports from the hyphenated scripts folder via `sys.path` (probed on `tests/test_agy_quota.py:18`). Neither row checks `lifecycle_runner.py` itself. Every task would hit "Verification row fails for a reason other than its Expect". Proposed: replace V4 with `ruff check --isolated skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` and V5 with `env MYPYPATH=skills/dev-lifecycle/resources/scripts mypy --ignore-missing-imports skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py`, in all five tasks. | fixed in 04b1ad8 |
| 10 | Important | .devtool/epic/autonomous_lifecycle_runner/task_2_subprocess_dispatcher_and_headless_agy.md:Decisions Already Made | `os.getpgid(p.pid)` raises ProcessLookupError once the group leader has exited, even while its children still run in the group (probed), so the timeout or cleanup path can crash and leave orphans, failing the "zero orphan" DoD. The HLD Feature Maintenance Map says `subprocess.run(timeout=...)`, which kills only the child and cannot do SIGTERM, grace, then SIGKILL. The same row requires a "JSON/text mode" of `compute_execution_order.py` that does not exist (text only; line 183 prints "Flattened sequential order:"). Proposed: decide `pgid = p.pid` captured at spawn (guaranteed by `start_new_session=True`), call `killpg` and treat ProcessLookupError as already exited, and also `killpg` after a normal exit; change the HLD map row to `subprocess.Popen`; specify parsing the "Flattened sequential order:" block (or importing `load_tasks`), and fail on a non-zero exit or any "Manual review advised" notes. | fixed in 04b1ad8 |
| 11 | Important | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts vs Feature Maintenance Map | the frozen contract names `step_principal_review` / `step_cross_model_review` and has no `resolve_gate3_order`, while the Maintenance Map, BDD ALR-HP-03 / ALR-EC-01 / ALR-EC-02 and task_2 name `stage_principal_review`, `stage_cross_model_review` and `LifecycleRunner.resolve_gate3_order`. With the strict-spec-fidelity guardrail in place, the Programmer stops on this mismatch. Proposed: choose one set of names, add `resolve_gate3_order(self) -> List[str]` to Module Contracts, and align the Maintenance Map, both BDD files and task_2/task_3. | fixed in 04b1ad8 |
| 12 | Important | .devtool/epic/autonomous_lifecycle_runner/task_5_orchestrator_cli_and_governance_rules.md:Files and Requirement Analysis item 2 | the spec's Testing section requires `scripts/verify.sh` to run the new test, but the script runs a fixed list of suites (lines 303-353) and is only read-only context here. The spec's Rule Changes require SKILL.md files to point to a reference file for the detail, and no such file is in Allowed files. `rules/CRITICAL_RULES.md` §8.2 (line 151, "Sole authority for … Gate approvals (Gate 1–5), and Review Choice decisions") would contradict auto Gate 3 and auto cross-model review, but only §5 and §6 are in scope. Proposed: add `scripts/verify.sh` (with a SUITES row for `tests/test_lifecycle_runner.py`) and `skills/dev-lifecycle/references/autonomous-mode.md` (new) to Allowed files, and extend item 2 to amend §8.2 with the autonomous-mode exception. | fixed in 04b1ad8 |
| 13 | Minor | .devtool/epic/autonomous_lifecycle_runner/bdd_scenarios.en.md:ALR-HP-02 | `.devtool/features/task_01.md` does not match the repository's `task_<n>_<slug>.md` naming. Proposed: use `.devtool/features/task_1_<slug>.md` in both BDD variants and task_2. | fixed in 04b1ad8 |
| 14 | Minor | .devtool/epic/autonomous_lifecycle_runner/handoff.md:Read First and Identifiers | the placeholders `<N>` and `<source spec>` were never filled in, and the Identifiers table repeats the same row. Proposed: re-run `package_epic.py --revise` after fixing the template fill-in, or write "5 tasks" and the spec filename. | fixed in 04b1ad8 |
| 15 | Minor | .devtool/epic/autonomous_lifecycle_runner/task_2_subprocess_dispatcher_and_headless_agy.md:Files | tasks 2-5 mark `lifecycle_runner.py` and `tests/test_lifecycle_runner.py` as `(new)` although task_1 creates them. Proposed: drop `(new)` in task_2..task_5. | fixed in 04b1ad8 |
| 16 | Minor | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Feature Maintenance Map (Model Prober & Dispatcher) | `agy models` lists effort-suffixed IDs (`gemini-3.8-flash-high`), so `--model gemini-3.8-flash --effort high` relies on alias resolution. Passing the prompt as an argv value also differs from the existing stdin pattern (run_external_review.py:473-476) and can hit Linux's 128 KiB per-argument limit. Proposed: have the probe log the resolved model, and send prompts on stdin as `execute()` does. | fixed in 04b1ad8 |
| 17 | Minor | .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `PipelineState` | ALR-AR-01 says the runner records a timeout failure in pipeline state, but `PipelineState` has no field for it. Proposed: state that timeouts set `halt_reason="DISPATCH_TIMEOUT:<task>"`, or add a `last_error: Optional[str]` field. | fixed in 04b1ad8 |

Raw output:

```text
I'm using the principal-review skill to conduct an architectural review. As the reviewer I stay read-only.
Only link paths differ. Now the artefacts themselves.
Now the BDD, handoff, and the source the design leans on.
Probing whether `review_config.json` preserves an unknown top-level `assistant` key across a review run's sticky-config rewrite:
Probing the Task 2 process-group decision (`os.getpgid(p.pid)`) for the case where the group leader exits but leaves children running:
I reviewed the epic at `bd893c79` against the scripts it reuses. The spec's direction holds up: the runner is opt-in, interactive mode stays as it is, Gates 1, 2 and 5 stay with the Human, and the three Circuit Breakers stay. `shared-contracts/` is absent (`ls` confirms), so "None" for shared contract impact is correct. The problems are in how the runner talks to the existing scripts. As written, several task contracts would hit Stop-and-Report or ship wrong behaviour.

**What I checked against source**

- **Review commands.** `run_external_review.py` has no `--stage` flag. It takes `--kind {code,principal,epic}`, and `--base` is required (lines 1760–1763).
- **Clean tree.** A review run refuses to start if `git status --porcelain` shows anything (lines 1241–1243). `.devtool/GATE_LEDGER.md` is excluded from the ignore rules (`.gitignore:13`), so once the ledger is written it shows up as untracked. `fix_plan_round<N>.md` is also tracked.
- **Triage.** `auto_triage_section` (lines 1614–1687) already computes all the triage outcomes, including the three Circuit Breakers. It detects FIX_LOOP only from rows whose decision cell starts with `fixed in ` (line 1630). `check` treats a blocking finding with no decision as undecided (lines 1470–1474).
- **Gate Ledger.** `GATE_LEDGER.md` is regenerated from `.devtool/state/gate_ledger.jsonl` by `record_gate_approval` (`scripts/resume_context.py:813–854`) and `render_gate_ledger_markdown` (line 363). Only rows with 7 or more cells are kept (line 285).
- **Execution order.** `compute_execution_order.py` prints text only (lines 146–193). It has no JSON mode.
- **Test registration.** `scripts/verify.sh` runs a fixed list of suites (lines 303–353); it does not discover new test files.
- **Assistant model.** `agy models` lists `gemini-3.8-flash-{low,medium,high}`, `claude-sonnet-5-5-*` and `claude-opus-5-5-*`. There is no `claude-3-7-sonnet`.

**Probes I ran (read-only, in temp directories)**

1. **Config key erasure.** After `update_sticky_review_config`, a top-level `assistant` key in `review_config.json` is gone. `load_review_config` copies only `last_used_provider` and `providers` (lines 111–121).
2. **Process group lookup.** `os.getpgid(p.pid)` raises `ProcessLookupError` once the group leader has exited, even while its child is still running in the group. `os.killpg(p.pid, SIGTERM)` still kills that child.
3. **Non-interactive prompt.** `input()` with stdin at `/dev/null` raises `EOFError`.
4. **mypy (V5).** mypy fails on a test that adds the script folder to `sys.path` at runtime, which is how existing tests import scripts (`tests/test_agy_quota.py:18`, `import-not-found`).
5. **ruff (V4).** The V4 target set already fails today with 12 SIM117 errors in `tests/test_agy_quota.py` and `tests/test_claude_quota.py`. The repo has no ruff config, so ruff falls back to `~/.config/ruff/ruff.toml`.
6. **RED rows.** `python3 -m unittest <path> -k test_alr_…` fails as the RED rows expect: exit 1 with "FAILED (errors=1)". `run_task_checks.py` merges stderr into stdout (line 245), so the "FAILED" match works.

The protected path `tests/test_lifecycle_runner.py` also appearing in Allowed files is not a defect. `audit_epic.py:184–186` treats a protected path listed in Allowed files as authorised, and other epics use the same pattern. Every task-file finding below also applies to its copy in `.devtool/features/`; the two copies differ only in link paths.

Verdict: CHANGES REQUIRED
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:High-Level Architecture and Sequence Diagram (and task_3 Requirement Analysis item 1) — `run_external_review.py run --stage principal` does not exist; the CLI takes `--kind {code,principal,epic}` with `--epic-dir` and a required `--base` (run_external_review.py:1760-1763), so the first Stage 2 dispatch exits 2 with an argparse error. Proposed: replace every `--stage principal` with `run --kind principal --epic-dir <epic_dir> --base <base> --auto-quota` and spell the cross-model call as `run --kind code --epic-dir <epic_dir> --base <base> --auto-quota`, in both HLD variants and task_3.
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts (`evaluate_circuit_breakers`) and Feature Maintenance Map, task_3/task_4 Requirement Analysis — the runner re-derives the Circuit Breakers from fixtures instead of using `run_external_review.py triage`, whose `## Auto-Triage Gate` already emits AUTO_PASS_CLEAN, AUTO_PASS_FINAL_MINOR_SWEEP, AUTO_FIX_ELIGIBLE, AUTO_PASS_FINAL_SWEEP and the three CIRCUIT_BREAKER_HALT actions (run_external_review.py:1614-1687). No artefact says what the runner does on AUTO_PASS_FINAL_MINOR_SWEEP (CRITICAL_RULES §6 says finish without another review round; task_3 says start the next round) or on AUTO_PASS_FINAL_SWEEP (Round 3 with Important findings left). No task writes `fixed in <sha>` / `dismissed: …` decision cells, yet FIX_LOOP only fires on those cells (line 1630) and `check` blocks Phase 4 while they are missing (lines 1470-1474). BDD ALR-FR-02 also says "identical file and issue" where the source compares the file path only. Proposed: add a Decisions Already Made rule that the runner parses `- **Action**:` from `triage --kind <principal|code> --epic-dir <dir>`; add a per-stage table mapping each Action to a runner transition (including the Tier 1 rule that Minor-only Principal rounds go to the Human batch); make task_3 and task_4 own writing decision cells into `principal_review.md` / `review_results.md` after each fix; reword ALR-FR-02 to "same file path".
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Architecture and Technical Design (no commit policy), task_3/task_4 Decisions Already Made — `run_external_review.py run` refuses any dirty tree (lines 1241-1243). The runner leaves untracked or modified files between rounds: `.devtool/GATE_LEDGER.md` (not ignored, `.gitignore:13`), `fix_plan_round<N>.md`, the review ledgers, and the Assistant's revisions. The second review invocation in either stage therefore exits 2. Proposed: add a "Commit sequencing" decision listing which runner step commits which file and with which message (fix plan, Fix commits, review-ledger decisions, gate ledger, `package_epic.py --revise`), and require a `git status --porcelain` empty check before every `run`.
[Important] .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:Requirement Analysis item 4 (and task_2 Decisions Already Made "records `Gate 3: CONFIRMED (autonomous)`") — `GATE_LEDGER.md` is a rendered view of `.devtool/state/gate_ledger.jsonl` (resume_context.py:813-854, 363). On re-render, `hydrate_gate_ledger_jsonl_if_needed` imports only rows with 7 or more cells (line 285), so a free-text ledger line written by the runner is silently dropped. That breaks ALR-ST-02 and ALR-EC-04. Proposed: require gate writes through `resume_context.py --gate <n> --epic <slug> --approved "<text>" --by lifecycle_runner` (or by importing `record_gate_approval`), and add `scripts/resume_context.py` to Read-only context in task_1 and task_2.
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `RunnerConfig` (and task_1 Decisions Already Made) — the default `assistant_model="claude-3-7-sonnet"` is not in `agy models` on this machine (only `claude-sonnet-5-5-*` / `claude-opus-5-5-*`), so the startup probe always fails without an override. The spec's model source, an `assistant` entry in `.devtool/review_config.json`, is deleted by every review round: `load_review_config` keeps only `last_used_provider` and `providers` (lines 111-121), and the probe confirmed the key is gone after `update_sticky_review_config`. Proposed: store the Assistant settings under `providers.assistant` (which survives the merge) or in a runner-owned file such as `.devtool/lifecycle_runner.json`; set a default the CLI actually lists (e.g. `claude-sonnet-5-5-high`); state the Assistant's `--mode` (plan for verdicts, auto only for `.devtool/` doc revisions).
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `StageName` / `prompt_human_principal_fixes` (and task_3 Decisions Already Made `[Y/N]`) — the Human checkpoint is a blocking stdin prompt with no saved state. When an agent launches the runner from `/dev-lifecycle --autonomous` through a bash tool (no TTY, tool timeout), `input()` raises EOFError (probed). A crash or exit while waiting has no stage to resume into. Proposed: add `StageName.AWAITING_PRINCIPAL_CONFIRMATION`; make the runner write the fix table to `.devtool/epic/<epic>/principal_fix_proposal_round<N>.md`, save state and exit with a dedicated code; resume with `--resume --confirm-fixes` / `--reject-fixes`. Also state that the Human launches the long-running runner in a terminal rather than inside an agent tool call.
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts and Kanban Tasks Breakdown — "Execute Gate 4 in full" has no contract or owner. Gate 4 is a multi-step procedure (smoke checklist commit, `run_external_review.py check`, `audit_epic.py`, the Integration results commands, `check_bdd_traceability.py --results`, and the agent skill `@quality_check`; dev-implementation/SKILL.md:317-358). No task owns `step_implementation`'s per-task protocol (`run_task_checks.py red/verify`, `sync_task_status.py`, one commit per task). Task_4 says the Programmer runs Gate 4, while the HLD sequence diagram says the Runner does. Proposed: add `run_gate4(self) -> Tuple[bool, str]` to Module Contracts with the exact command list (naming the script that replaces `@quality_check`), name who runs it, and assign `step_implementation` with that per-task protocol to task_2 (or a new task) via Covers and Decisions Already Made.
[Important] .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:BDD SCENARIOS Covers line — ALR-ST-01 ("resumes from the exact interrupted task") needs the `step_implementation` dispatch loop, and ALR-ST-02 (Gate 3/4/5 ledger sync) needs Gate 3 auto-order (task_2) and Gate 4 (task_4/task_5). Neither can pass at task_1, so V2, V3 and V6 cannot go green within task_1's scope. Proposed: move ALR-ST-02 to task_5 and either move ALR-ST-01 to the task that owns `step_implementation` or reword it to state-level resume (`load_or_init_state` returns the saved stage, `completed_tasks` and round).
[Important] .devtool/epic/autonomous_lifecycle_runner/task_1_pipeline_state_machine_and_probing.md:Verification V4/V5 (identical rows in task_2..task_5) — V4 already fails today with 12 SIM117 errors in `tests/test_agy_quota.py` and `tests/test_claude_quota.py`, which are outside Allowed files (ruff falls back to `~/.config/ruff/ruff.toml` because the repo has no config). V5 fails with `import-not-found` on a test that imports from the hyphenated scripts folder via `sys.path` (probed on `tests/test_agy_quota.py:18`). Neither row checks `lifecycle_runner.py` itself. Every task would hit "Verification row fails for a reason other than its Expect". Proposed: replace V4 with `ruff check --isolated skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py` and V5 with `env MYPYPATH=skills/dev-lifecycle/resources/scripts mypy --ignore-missing-imports skills/dev-lifecycle/resources/scripts/lifecycle_runner.py tests/test_lifecycle_runner.py`, in all five tasks.
[Important] .devtool/epic/autonomous_lifecycle_runner/task_2_subprocess_dispatcher_and_headless_agy.md:Decisions Already Made — `os.getpgid(p.pid)` raises ProcessLookupError once the group leader has exited, even while its children still run in the group (probed), so the timeout or cleanup path can crash and leave orphans, failing the "zero orphan" DoD. The HLD Feature Maintenance Map says `subprocess.run(timeout=...)`, which kills only the child and cannot do SIGTERM, grace, then SIGKILL. The same row requires a "JSON/text mode" of `compute_execution_order.py` that does not exist (text only; line 183 prints "Flattened sequential order:"). Proposed: decide `pgid = p.pid` captured at spawn (guaranteed by `start_new_session=True`), call `killpg` and treat ProcessLookupError as already exited, and also `killpg` after a normal exit; change the HLD map row to `subprocess.Popen`; specify parsing the "Flattened sequential order:" block (or importing `load_tasks`), and fail on a non-zero exit or any "Manual review advised" notes.
[Important] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts vs Feature Maintenance Map — the frozen contract names `step_principal_review` / `step_cross_model_review` and has no `resolve_gate3_order`, while the Maintenance Map, BDD ALR-HP-03 / ALR-EC-01 / ALR-EC-02 and task_2 name `stage_principal_review`, `stage_cross_model_review` and `LifecycleRunner.resolve_gate3_order`. With the strict-spec-fidelity guardrail in place, the Programmer stops on this mismatch. Proposed: choose one set of names, add `resolve_gate3_order(self) -> List[str]` to Module Contracts, and align the Maintenance Map, both BDD files and task_2/task_3.
[Important] .devtool/epic/autonomous_lifecycle_runner/task_5_orchestrator_cli_and_governance_rules.md:Files and Requirement Analysis item 2 — the spec's Testing section requires `scripts/verify.sh` to run the new test, but the script runs a fixed list of suites (lines 303-353) and is only read-only context here. The spec's Rule Changes require SKILL.md files to point to a reference file for the detail, and no such file is in Allowed files. `rules/CRITICAL_RULES.md` §8.2 (line 151, "Sole authority for … Gate approvals (Gate 1–5), and Review Choice decisions") would contradict auto Gate 3 and auto cross-model review, but only §5 and §6 are in scope. Proposed: add `scripts/verify.sh` (with a SUITES row for `tests/test_lifecycle_runner.py`) and `skills/dev-lifecycle/references/autonomous-mode.md` (new) to Allowed files, and extend item 2 to amend §8.2 with the autonomous-mode exception.
[Minor] .devtool/epic/autonomous_lifecycle_runner/bdd_scenarios.en.md:ALR-HP-02 — `.devtool/features/task_01.md` does not match the repository's `task_<n>_<slug>.md` naming. Proposed: use `.devtool/features/task_1_<slug>.md` in both BDD variants and task_2.
[Minor] .devtool/epic/autonomous_lifecycle_runner/handoff.md:Read First and Identifiers — the placeholders `<N>` and `<source spec>` were never filled in, and the Identifiers table repeats the same row. Proposed: re-run `package_epic.py --revise` after fixing the template fill-in, or write "5 tasks" and the spec filename.
[Minor] .devtool/epic/autonomous_lifecycle_runner/task_2_subprocess_dispatcher_and_headless_agy.md:Files — tasks 2-5 mark `lifecycle_runner.py` and `tests/test_lifecycle_runner.py` as `(new)` although task_1 creates them. Proposed: drop `(new)` in task_2..task_5.
[Minor] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Feature Maintenance Map (Model Prober & Dispatcher) — `agy models` lists effort-suffixed IDs (`gemini-3.8-flash-high`), so `--model gemini-3.8-flash --effort high` relies on alias resolution. Passing the prompt as an argv value also differs from the existing stdin pattern (run_external_review.py:473-476) and can hit Linux's 128 KiB per-argument limit. Proposed: have the probe log the resolved model, and send prompts on stdin as `execute()` does.
[Minor] .devtool/epic/autonomous_lifecycle_runner/autonomous_lifecycle_runner.en.md:Module Contracts `PipelineState` — ALR-AR-01 says the runner records a timeout failure in pipeline state, but `PipelineState` has no field for it. Proposed: state that timeouts set `halt_reason="DISPATCH_TIMEOUT:<task>"`, or add a `last_error: Optional[str]` field.

--- stderr ---
[tool] Load skill: principal-review
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=35
[tool] status: InProgress
[tool] status: Completed
[tool] Confirm candidate commit and branch diff scope
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=63
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] List changed files and compare duplicate task copies
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=88
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Failed: List changed files and compare duplicate task copies
[tool] Show how duplicate task copies differ
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=63
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Failed: Show how duplicate task copies differ
[tool] Read File
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=38
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] Read File
[tool] status: InProgress
[tool] Read File
[tool] status: InProgress
[tool] Read File
[tool] status: InProgress
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=123
[tool] status: Completed
[tool] status: Completed
[tool] status: Completed
[tool] status: Completed
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=518
[tool] status: Completed
[tool] status: Completed
[tool] Inspect external review runner CLI surface
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=64
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Locate triage gate states and result files
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=97
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=23
[tool] status: Completed
[tool] Find decision recording and undecided-finding guards
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=158
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=22
[tool] status: Completed
[tool] Check artefact classification and ignore rules for runner files
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=128
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Inspect gate ledger writer and its CLI
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=125
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] status: Completed
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=32
[tool] Inspect execution order script interface and output
[tool] status: InProgress
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=134
[tool] status: Completed
[tool] Compute this epic's task execution order
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=60
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read Python quality config and verify script test hooks
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=58
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=14
[tool] status: Completed
[tool] Probe unittest path invocation and test import pattern
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=121
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Probe RED-row behaviour with missing module in temp dir
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=88
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Check whether task checks match against stderr
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=53
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Learn how protected paths are enforced
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=61
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=22
[tool] status: Completed
[tool] Compare protected-path conventions in other epics
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=64
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Check agy CLI flags for headless dispatch
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=47
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] List models agy accepts
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=53
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Check review config schema for an assistant entry
[tool] status: InProgress
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=110
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=25
[tool] status: Completed
[tool] Probe whether review runs drop an assistant config key
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=149
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] See how the existing runner invokes agy and supervises it
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=156
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=41
[tool] status: Completed
[tool] Find what Gate 3 and Gate 4 mean in dev-implementation
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=75
[tool] Locate Phase 4 Gate 4 procedure definition
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=31
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] status: Completed
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=20
[tool] Check dev-lifecycle worktree and autonomous mode text
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=117
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read dev-lifecycle runtime sequence and handoff sections
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=39
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Map CRITICAL_RULES section numbering and docs files
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=76
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Read File
[tool] status: InProgress
[tool] status: Completed
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=18
[tool] Check clean-tree guard and whether gate ledger is tracked
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=206
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] See where gate ledger writes resolve in worktrees
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=49
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Probe process-group lookup after leader exits
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=231
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Check lint and type-check tool availability
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=153
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Probe mypy on an existing sys.path-importing test
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=89
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Baseline the V4 and V5 quality commands
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=161
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] List the pre-existing ruff failures
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=39
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Identify which ruff config produces SIM117
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=83
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Failed: Identify which ruff config produces SIM117
[tool] Confirm no shared contracts and non-TTY prompt behaviour
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=454
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Cross-check contract term usage across artefacts
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=92
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[tool] Pin exact line numbers for cited evidence
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=120
[tool] status: InProgress
[tool] status: InProgress
[tool] status: Completed
[INFO] [KRS] <-- GenerateAssistantResponseCommand done totalEvents=1332
```
