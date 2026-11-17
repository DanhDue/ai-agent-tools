# Four-Persona Governance, Persona Model Config, and English-Only Dev Artefacts

- **Date**: 2026-11-17
- **PIC**: danhdue
- **Status**: Approved
- **Epic**: `four_persona_governance`
- **Next step**: `dev-designer` (epic-scale: rules, five skills, a new skill, lifecycle scripts, kit docs)

## Table of Contents

- [1. Problem Statement](#1-problem-statement)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Persona Model](#3-persona-model)
  - [3.1. The Four Personas](#31-the-four-personas)
  - [3.2. Role Renumbering](#32-role-renumbering)
  - [3.3. Session Map](#33-session-map)
  - [3.4. Subagent Brief Roles](#34-subagent-brief-roles)
- [4. Stage Flows](#4-stage-flows)
  - [4.1. Stage 2 to Stage 3 Handoff](#41-stage-2-to-stage-3-handoff)
  - [4.2. Per-Task Flow](#42-per-task-flow)
  - [4.3. Gate 4 and Risk Escalation](#43-gate-4-and-risk-escalation)
- [5. Persona Model Configuration](#5-persona-model-configuration)
  - [5.1. Files and Precedence](#51-files-and-precedence)
  - [5.2. Schema](#52-schema)
  - [5.3. The dev-config Skill](#53-the-dev-config-skill)
  - [5.4. Dispatch](#54-dispatch)
  - [5.5. Unavailable Models](#55-unavailable-models)
- [6. English-Only Dev Artefacts](#6-english-only-dev-artefacts)
  - [6.1. Language Rule](#61-language-rule)
  - [6.2. File Naming and Legacy Compatibility](#62-file-naming-and-legacy-compatibility)
  - [6.3. Vietnamese Mirrors and Context Loading](#63-vietnamese-mirrors-and-context-loading)
  - [6.4. What Stays Bilingual](#64-what-stays-bilingual)
- [7. Exclusive File Ownership Check](#7-exclusive-file-ownership-check)
- [8. Proactive Checkpoints and Low-Quota Mode](#8-proactive-checkpoints-and-low-quota-mode)
  - [8.1. Checkpoint Record](#81-checkpoint-record)
  - [8.2. Mandatory Checkpoint Events](#82-mandatory-checkpoint-events)
  - [8.3. Turn Budget](#83-turn-budget)
  - [8.4. Low-Quota Mode](#84-low-quota-mode)
  - [8.5. Automatic Quota Gate](#85-automatic-quota-gate)
- [9. check-tasks Dashboard Sync](#9-check-tasks-dashboard-sync)
- [10. Testing Strategy](#10-testing-strategy)
- [11. Dependencies, Assumptions, and Risks](#11-dependencies-assumptions-and-risks)
- [12. Open Items](#12-open-items)
- [13. Shared Contract Warnings](#13-shared-contract-warnings)

## 1. Problem Statement

The Tri-Role model (Human Architect, AI Assistant, AI Programmer) makes the Stage 3 main session do two
jobs: it is both the design authority (fix-plan rulings, revisions) and the mechanical orchestrator
(worker pool, dispatch, SHA checks). Both jobs therefore run on one model, even though design judgement
benefits from a strong reasoning model (Argon) and orchestration only needs a dependable, cheaper one
(Hydrogen at `high`). The `task-reviewer` subagent runs on the Programmer model, so the code that a
model writes is reviewed by the same model family that wrote it.

Model selection is scattered: `.devtool/review_config.json["providers"]["programmer"|"assistant"]`, the
`AGY_PROGRAMMER_*` and `AGY_ASSISTANT_MODEL` environment variables, `lifecycle_runner.py` constants and
CLI flags. Switching models when credits run out means editing JSON by hand in every repository.

Every dev-lifecycle design artefact (spec, HLD, BDD scenarios, non-epic plan) is produced as a
synchronised `.en.md` / `.vi.md` pair. The Vietnamese variant doubles authoring and review tokens, is
loaded into agent context alongside the English one, and is rarely read by the Human Architect.

Agents cannot see the provider's quota bar. State is saved only when an agent decides to call
`/save-context`, which it tends to do late; a session that hits its 5-hour limit mid-wave loses the
in-flight picture, and the next session has to reconstruct it from git and task files.

## 2. Goals and Non-Goals

Goals:

1. Replace Tri-Role with four personas whose boundaries separate design judgement from orchestration.
2. Bind each AI persona to a model through one layered configuration file, editable through a new
   `/d3nexus:dev-config` skill, with presets for switching when credits change.
3. Make dev-lifecycle artefacts English-only, keep chat with the Human Architect free to use
   Vietnamese, and stop agents loading `.vi.md` files.
4. Enforce exclusive file ownership between tasks that may run in parallel.
5. Never lose lifecycle state to a sudden quota cut-off: checkpoint proactively at fixed events and on a
   turn budget, and let the user switch the kit into a low-quota mode that stops at the next safe point.

Non-goals:

- The doc-lifecycle (`doc-brainstorming`, `doc-designer`, `doc-implementation`, `doc_quality_check`)
  is unchanged and stays bilingual.
- No automatic model fallback (see [5.5](#55-unavailable-models)).
- No local Ollama persona binding (see [12. Open Items](#12-open-items)).
- No change to the external review provider priority (`/principal-review`, `/cross-model-review`) or
  its `.devtool/review_config.json` keys other than `providers.assistant` and `providers.programmer`.
- No migration of existing `.vi.md` files in consuming repositories; they are left in place.

## 3. Persona Model

### 3.1. The Four Personas

| Role | Config key | Default | Owns | Forbidden |
|------|-----------|---------|------|-----------|
| **1.0 Human Architect** | — | the user | Product vision, brainstorming, architectural trade-offs, Gates 1, 2 and 5, every escalation | — |
| **2.1 AI Architect & Reviewer** | `ai_architect_reviewer` | Argon, `high` | Stage 1–2: brainstorming with 1.0, spec, HLD, BDD scenarios, TDD test plans (task Verification tables), task decomposition into disjoint packages, non-epic plans, `/principal-review` and its revisions, packaging. Stage 3: `task-reviewer` (semantic and architectural review), `fix-planner` (solutions for high-risk findings) | Editing `src/` or `tests/`; running test suites, linters or type checkers; dispatching subagents or managing the worker pool |
| **2.2 Orchestrator** | `orchestrator` | Hydrogen, `high` | Receiving the packaged handoff; Gate 3; worker pool; dispatching 2.1 and 2.3 subagents; tracking progress; independent verification of subagent claims (SHA, clean tree, report binding, diff scope); marking tasks `done`; consolidated execution and Gate 5 reports | Reading or editing `src/` or `tests/`; editing HLD, BDD, task Verification tables, DoD or `Allowed files`; running tests, linters, type checkers, `run_task_checks.py` or `verify-tier` |
| **2.3 Programmer** | `programmer` | Hydrogen, `xhigh` | `task-implementer` (TDD inside `Allowed files`), `review-fixer`, `gate4-verifier` | Unchanged from today: no edits to HLD, BDD, `shared-contracts/`, Verification tables, DoD or `Allowed files`; no worker-pool calls |

Role 2.1 may run lifecycle scripts that call an external review CLI synchronously (`/principal-review`),
but it never spawns or waits on subagents. The read-only checks it runs as `task-reviewer` are listed in
[3.4](#34-subagent-brief-roles).

### 3.2. Role Renumbering

| Tri-Role (old) | Four-persona (new) |
|----------------|--------------------|
| Role 2.1 Human Architect | Role 1.0 Human Architect |
| Role 2.2 AI Assistant (design work, reviser, fix-plan ruling) | Role 2.1 AI Architect & Reviewer |
| Role 2.2 Orchestrator (Stage 3 main session) | Role 2.2 Orchestrator |
| Role 2.3 AI Programmer | Role 2.3 Programmer |

`orchestration-roles.md` carries this table once; other files reference the new numbers only. The
`--role` values accepted by `resume_context.py` become `architect`, `orchestrator` and `programmer`;
`assistant` remains accepted as an alias of `architect` for existing state files.

### 3.3. Session Map

The kit cannot choose the model of a main session; the user picks it when opening the IDE or CLI. It
can only choose the model of a subagent it dispatches. Personas therefore map to sessions by stage:

- **Stages 1–2** run in a main session the user opens on the `ai_architect_reviewer` model.
- **Stage 3** runs in a main session the user opens on the `orchestrator` model, started from the
  prompt that `resume_context.py --emit-prompt implement` prints. That prompt names the persona and its
  resolved model and effort so the user opens the right session.
- Inside Stage 3, Role 2.1 work runs as subagents dispatched on the `ai_architect_reviewer` binding.
- In autonomous mode, `lifecycle_runner.py` is the Orchestrator and dispatches 2.1 and 2.3 through the
  same bindings.

### 3.4. Subagent Brief Roles

`resume_context.py --emit-prompt brief --brief-role <role>` emits these:

| Brief role | Persona | Change | Summary contract |
|-----------|---------|--------|------------------|
| `task-implementer` | 2.3 | unchanged | unchanged |
| `task-reviewer` | **2.1** (was 2.3) | Reads the slot diff, `src/`/`tests/`, task file and evidence; runs only `run_task_checks.py status` and `check_bdd_traceability.py`; never edits, commits or runs test suites. The Orchestrator marks the task `done` on `PASS`. | `task_id`, `verdict`, `head_sha`, `done_gate`, `findings` |
| `review-fixer` | 2.3 | Modes become `fast-track` and `apply-plan`; `plan-first` moves to `fix-planner` | `round`, `mode`, `status` (`FIXED`/`BLOCKED`), `fix_shas`, `decision_sha`, `changed_files`, `tier1` |
| `gate4-verifier` | 2.3 | unchanged | unchanged |
| `principal-reviser` | 2.1 | Runs inline in the Stage 2 main session or as a same-model subagent | unchanged |
| `fix-planner` | **2.1** (new) | Writes `fix_plan_round<N>.md` for high-risk findings, classifies each against the halt criteria | `round`, `status` (`PLANNED`/`ESCALATE`), `plan_path`, `halt_criteria` (list), `decision_sha` |

Selective review gating is kept: the Orchestrator dispatches `task-reviewer` only when
`review_tier == "full"`, the labels intersect {`security`, `architecture`, `concurrency`, `contract`}, or
`git diff --name-only` shows more than two non-test modules changed.

## 4. Stage Flows

### 4.1. Stage 2 to Stage 3 Handoff

Role 2.1 runs Gate 2, `/principal-review` (max three rounds) and `package_epic.py`, then prints the
implement prompt. Role 2.2 is the receiver of `handoff.md`:

- **Dừng lại** — the user opens a new main session on the `orchestrator` binding with the printed prompt.
  This is the path that honours the session map.
- **Triển khai (tự động)** — Stage 3 continues in the current session, so Role 2.2 runs on the Stage 2
  session's model. The Gate 2 prompt states this and names the configured `orchestrator` binding, so the
  user can choose **Dừng lại** instead when the two differ.

### 4.2. Per-Task Flow

```mermaid
flowchart TD
    A["2.2 Orchestrator: sync working, dispatch task-implementer"] --> B["2.3 Programmer: RED, GREEN, run_task_checks.py verify"]
    B --> C{"2.2 recomputes gating from git diff"}
    C -->|"no review needed"| D["2.3 finalizes task (done + commit)"]
    C -->|"review needed"| E["2.1 task-reviewer: semantic review, status + traceability checks"]
    E -->|"PASS"| F["2.2 marks task done and commits"]
    E -->|"FAIL"| A
    D --> G["2.2 merge slot, next wave"]
    F --> G
```

### 4.3. Gate 4 and Risk Escalation

After `cleanup`, the Orchestrator dispatches a fresh `gate4-verifier` (2.3). On `PASS` it records Gate 4
and runs `/cross-model-review`. Findings from either source are routed by risk:

- **Low risk** — every open finding is `Valid` and the triage contains no escalation marker (today's
  fast-track test), or a Gate 4 failure is the first failure of that check: a 2.3 `review-fixer` runs in
  `fast-track` mode.
- **High risk** — any `Critical` finding, any escalation marker, or the same Gate 4 check failing twice
  in a row: the Orchestrator dispatches a 2.1 `fix-planner`, which writes `fix_plan_round<N>.md`.
  - The plan touches none of the five halt criteria → status `PLANNED`; a 2.3 `review-fixer` applies it
    in `apply-plan` mode.
  - The plan touches any halt criterion → status `ESCALATE`; the Orchestrator records
    `--pending-decision`, renders the Top 3 Highest-Risk Findings, and stops for Role 1.0.

The five halt criteria (from `governance-checklists.md`):

1. `CRITICAL_CONFLICT` — the solution contradicts the approved HLD or `Decisions Already Made`.
2. `Debatable` / `Not shown` — the finding cannot be verified against live source.
3. `SHARED_CONTRACT_CONFLICT` — the finding or solution touches `shared-contracts/`.
4. `FIX_LOOP` — a location fixed in round N−1 fails again with `[INCOMPLETE_FIX]` or `[NEW_REGRESSION]`.
5. `MAX_ROUNDS_CRITICAL_REMAINING` — a `Critical` finding survives round 3.

After every fix, a fresh `gate4-verifier` reruns Gate 4 in full. The Orchestrator no longer rules
`APPROVED`/`ADJUSTED` on fix plans: the plan's author is now the design authority, and the halt criteria
replace the ruling. `lifecycle_runner.py` changes accordingly: `_draft_fix_plan` dispatches the
`ai_architect_reviewer` binding and `evaluate_programmer_fix_plan` is removed.

## 5. Persona Model Configuration

### 5.1. Files and Precedence

| Layer | Path | Purpose |
|-------|------|---------|
| Kit defaults | `skills/dev-config/resources/personas.default.json` | Model catalogue, shipped presets, default bindings |
| Global | `$REAL_HOME/.d3nexus/personas.json` | Per-user choice that follows credits across every repository |
| Project | `.agents/config/personas.json` | Per-repository override |
| Invocation | CLI flags (`lifecycle_runner.py --programmer-model`, etc.) | One-off override |

Layers are deep-merged in that order, later layers winning per key. The effective `active_preset` is
selected from the merged result, then the merged `overrides` are applied per persona, then CLI flags.
`$REAL_HOME` is resolved the way `run_external_review.py` already resolves it for Antigravity profiles,
so every profile shares one global file.

The resolver ignores `.devtool/review_config.json["providers"]["assistant"|"programmer"]` and the
`AGY_PROGRAMMER_MODEL`, `AGY_PROGRAMMER_EFFORT` and `AGY_ASSISTANT_MODEL` environment variables.
`dev-config status` warns when any of them is set.

### 5.2. Schema

```json
{
  "schema_version": 1,
  "active_preset": "default",
  "models": {
    "argon": {"cli": "agy", "id": "gemini-4-argon-{effort}", "efforts": ["low", "medium", "high"]},
    "hydrogen": {"cli": "agy", "id": "gemini-4-hydrogen-{effort}", "efforts": ["low", "medium", "high", "xhigh"]},
    "claude-opus": {"cli": "claude", "id": "opus", "efforts": ["medium", "high", "xhigh"]},
    "claude-sonnet": {"cli": "claude", "id": "sonnet", "efforts": ["medium", "high"]},
    "codex-gpt": {"cli": "codex", "id": "gpt-6.1-sol", "efforts": ["medium", "high", "xhigh"]},
    "kiro-opus": {"cli": "kiro", "id": "claude-opus-5.5", "efforts": ["high"]}
  },
  "presets": {
    "default": {
      "ai_architect_reviewer": {"model": "argon", "effort": "high", "fallback_model": "claude-opus"},
      "orchestrator": {"model": "hydrogen", "effort": "high", "fallback_model": "claude-sonnet"},
      "programmer": {"model": "hydrogen", "effort": "xhigh", "fallback_model": "claude-sonnet"}
    },
    "gemini-saver": {},
    "claude-hybrid": {},
    "all-hydrogen": {},
    "codex-kiro": {}
  },
  "overrides": {},
  "checkpoint_policy": {"max_orchestrator_turns_before_checkpoint": 8},
  "low_quota": {}
}
```

The four non-default presets are abbreviated above; each binds all three personas. Their bindings:

| Preset | `ai_architect_reviewer` | `orchestrator` | `programmer` |
|--------|------------------------|----------------|--------------|
| `gemini-saver` | `argon` `medium` | `hydrogen` `medium` | `hydrogen` `high` |
| `claude-hybrid` | `claude-opus` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `all-hydrogen` | `hydrogen` `xhigh` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `codex-kiro` | `kiro-opus` `high` | `codex-gpt` `medium` | `codex-gpt` `xhigh` |

Rules:

- `{effort}` in an `id` is substituted with the binding's effort; that is how `agy` names its model
  variants today (`gemini-4-hydrogen-xhigh`). The `efforts` list of every `agy` alias is checked against
  the live `agy` model list during implementation; aliases or efforts it does not offer are removed.
- `cli` is one of `agy`, `claude`, `codex`, `kiro`.
- `fallback_model` is advisory only: it is printed when the bound model is unavailable and is never used
  automatically.
- `checkpoint_policy` and `low_quota` are described in [8](#8-proactive-checkpoints-and-low-quota-mode).
- Validation fails on an unknown alias, an effort outside the alias's `efforts`, an unknown persona key, or
  an unknown `schema_version`.

### 5.3. The dev-config Skill

New skill `skills/dev-config/` with `SKILL.md` and `resources/scripts/dev_config.py`. The skill body
maps `/d3nexus:dev-config <args>` to the script.

| Command | Effect |
|---------|--------|
| `status` | Table of persona → CLI, resolved model ID, effort, fallback, and the layer each value came from; lists presets; shows the turn budget and low-quota state with its expiry; prints validation and legacy-key warnings; flags a CLI missing from `PATH` |
| `models [--persona <persona>]` (alias `--models`) | Lists the merged model catalogue: alias, CLI, resolved model IDs per effort, allowed efforts, whether the CLI is on `PATH`, the current quota line when readable, and which personas use it now |
| `models add <alias> --cli <cli> --id <id> --efforts <list> [--scope global\|project]` | Adds or replaces a catalogue alias, so a newly released model is usable without editing JSON |
| `models remove <alias> [--scope global\|project]` | Removes an alias from that layer; refused while a binding in the merged config still uses it |
| `preset <name> [--scope global\|project]` | Sets `active_preset` (default scope `global`); warns when a project layer masks the change |
| `set <persona> <model> <effort> [--fallback <model>] [--scope global\|project]` | Writes `overrides.<persona>` |
| `reset [<persona>] [--scope global\|project]` | Clears one or all overrides |
| `low-quota on\|off [--for <hours>]` (alias `--low-quota`) | Toggles low-quota mode for the current profile, see [8.4](#84-low-quota-mode) |
| `checkpoint --turns <n> [--scope global\|project]` | Sets `max_orchestrator_turns_before_checkpoint` |
| `quota-check [--personas <list>]` | Runs the automatic quota gate ([8.5](#85-automatic-quota-gate)); exit 0 sufficient, 2 insufficient |
| `resolve <persona> [--format json\|argv] [--mode read-only\|write]` | Machine interface used by every dispatch site |

**Choosing models interactively.** `/d3nexus:dev-config --models` with no further arguments runs
`models`, shows the table, then asks the user one question per persona to pick a model and effort among
the valid options (current binding first). It applies each answer with `set` (scope `global` unless the
user picks `project`) and finishes with `status`. With `--persona <persona>` it asks about that persona only.

Writes are atomic (temp file plus rename) and validated before replacing the file. The resolver lives in
`resources/scripts/persona_config.py` and is loaded by path (`importlib.util`) from
`lifecycle_runner.py`, `resume_context.py` and `run_external_review.py`, the same way `lifecycle_runner.py`
already loads sibling modules.

### 5.4. Dispatch

`persona_config.py` builds the headless argv for a binding and a mode. It reuses the per-CLI command
builders in `run_external_review.py` (which already handle `claude`, `codex`, `kiro` and `agy`, including
the Kiro `HOME` workaround) and adds a write mode:

- `read-only` for `task-reviewer` and `fix-planner` (2.1 must not edit code; `fix-planner` writes only
  `fix_plan_round<N>.md`, which the Orchestrator scope-checks).
- `write` for `task-implementer`, `review-fixer` and `gate4-verifier`.

Every dispatch site resolves through `dev_config.py resolve`: `lifecycle_runner.py` (replacing
`resolve_programmer_model`, `resolve_programmer_effort` and `resolve_assistant_model`), the
`--emit-prompt` and `brief` output of `resume_context.py`, and the dispatch instructions in
`dev-implementation`, `subagent-driven-development`, `cross-model-review` and `principal-review`.
The rule that an in-runtime subagent tool may stand in only if it pins the exact model and effort stays.

### 5.5. Unavailable Models

There is no automatic fallback and no retry. On the first dispatch failure caused by a missing CLI, failed
authentication, or exhausted quota (`HTTP 429`, `RESOURCE_EXHAUSTED`, `ResourceExhausted`, or the
CLI's own quota message), the Orchestrator (or `lifecycle_runner.py`, with halt state
`MODEL_UNAVAILABLE`):

1. Writes a `model_unavailable` checkpoint ([8.2](#82-mandatory-checkpoint-events)).
2. Records `resume_context.py --pending-decision "<persona> model <alias> unavailable" --decision-kind blocker --epic <slug>`.
3. Prints the advisory fallback as a ready command, for example
   `/d3nexus:dev-config set programmer claude-sonnet high`, and suggests switching profile.
4. Stops calling tools.

A task failure (red tests, failing checks) is not a model failure and never triggers this path.

## 6. English-Only Dev Artefacts

### 6.1. Language Rule

Added to `CRITICAL_RULES.md` §8 and to `governance-checklists.md`:

- English is the single source of truth for every role.
- Every persisted dev-lifecycle artefact is English-only: specs, HLDs, BDD scenarios, task files and
  their TDD Verification tables, non-epic plans, `handoff.md`, review and fix-plan files, execution and
  Gate 5 reports, code comments, and commit messages.
- Chat with Role 1.0 may use Vietnamese, matching the user. A Vietnamese explanation or mirror is
  produced only when Role 1.0 asks for it.

### 6.2. File Naming and Legacy Compatibility

New artefacts drop the language suffix:

| Artefact | New name | Old pair |
|----------|----------|----------|
| Spec | `YYYY-MM-DD-<topic>-design.md` | `.en.md` + `.vi.md` |
| Non-epic plan | `docs/superpowers/plans/YYYY-MM-DD-<topic>.md` | `.en.md` + `.vi.md` |
| HLD | `.devtool/epic/<epic_dir>/<epic_dir>.md` | `.en.md` + `.vi.md` |
| BDD scenarios | `.devtool/epic/<epic_dir>/bdd_scenarios.md` | `.en.md` + `.vi.md` |

A shared helper `resolve_epic_doc(directory, stem)` returns `<stem>.md`, else `<stem>.en.md`, and never a
`.vi.md`. Every script that locates these files uses it: `check_epic_readiness.py`, `package_epic.py`,
`sync_task_status.py`, `check_bdd_traceability.py`, `run_external_review.py`, `check_tasks.py` and
`tasks_server.py`. In-flight epics with `.en.md` + `.vi.md` pairs keep working; `sync_task_status.py`
updates only the English file, and the status grep matches `Status` only.

### 6.3. Vietnamese Mirrors and Context Loading

- A `.vi.md` file is a mirror of its English original, not a source of truth. No gate checks it and
  nothing keeps it in sync.
- Agents do not load `.vi.md` files unless Role 1.0 names the file.
- Tooling enforces this: prompt and bundle builders (`run_external_review.py`, the principal-review
  bundle, `resume_context.py --emit-prompt` and `brief`, `check_tasks.py`) exclude `*.vi.md` from every
  file list given to an agent, and dev-lifecycle checks ignore `.vi.md`.
- A mirror produced on request starts with
  `> Mirror of <name>.md — not SSOT; agents do not load this file.`

### 6.4. What Stays Bilingual

- The doc-lifecycle skills and `check_document.py --require-bilingual`.
- The kit's human-facing guides under `docs/` (`lifecycles`, `context-memory-quick-guide`,
  `shared-contracts-quick-guide`, `choosing-a-lifecycle`). They are documents; both variants are updated
  for the four-persona model.
- Historical specs and plans in `docs/superpowers/` are left untouched.

## 7. Exclusive File Ownership Check

`check_task_contract.py --design` (run by `check_epic_readiness.py`) gains a rule: for every pair of
tasks with no path between them in the `Blocked by` graph, their `Allowed files` sets, normalised to
repository paths without symbol or line anchors, must be disjoint. A violation fails readiness and names
the pair and the shared paths; Role 2.1 fixes it by adding a `Blocked by` edge or by reassigning the file.

## 8. Proactive Checkpoints and Low-Quota Mode

### 8.1. Checkpoint Record

A checkpoint extends the existing per-epic heartbeat, `.devtool/state/<slug>.heartbeat.json`, which is
already written atomically under a lock, mirrored between the root and worktrees, and read by
`resume_context.py` and check-tasks. No second state file is introduced. A new command writes it:

```bash
python3 scripts/resume_context.py --checkpoint <event> --epic <slug> [--next "<next step>"]
```

It sets a `checkpoint` block in the heartbeat — `event`, `at`, `persona`, `head_sha`, `wave`,
`tasks_done`, `tasks_in_flight`, `next_step`, `turns_since_checkpoint` (reset to 0), `low_quota` — updates
`Next Immediate Step` in `.devtool/state/<slug>.md`, and appends a `checkpoint` event to
`events_<slug>.jsonl`. Plain `resume_context.py` prints the latest checkpoint first, so a fresh session
resumes from it.

### 8.2. Mandatory Checkpoint Events

| Event | Written by | When |
|-------|-----------|------|
| `gate2_tasks_locked` | 2.1 | Immediately after the HLD and `task_01..task_0N` are confirmed and Gate 2 is recorded |
| `subagent_returned` | 2.2 | After reading each subagent's summary contract, before the next dispatch |
| `wave_merged` | 2.2 | After every wave's slots are merged, whatever the wave size |
| `model_unavailable` | 2.2 or runner | On the first quota, auth or missing-CLI failure, before halting ([5.5](#55-unavailable-models)) |
| `turn_budget` | 2.2 | When the turn budget in [8.3](#83-turn-budget) is reached |
| `low_quota_stop` | 2.2 | At the safe point where low-quota mode stops ([8.4](#84-low-quota-mode)) |
| `quota_low` | 2.2 or runner | When the automatic quota gate finds a persona's quota insufficient ([8.5](#85-automatic-quota-gate)) |

These are written into the relevant SKILL.md steps (`dev-designer`, `dev-implementation`,
`subagent-driven-development`, `cross-model-review`) and into `lifecycle_runner.py`.

### 8.3. Turn Budget

`checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default 8) bounds the number of tool calls a
Stage 3 main session makes between checkpoints. `lifecycle_runner.py` enforces it exactly. An interactive
session cannot count its own calls reliably, so the rule is best-effort there; the event checkpoints in
[8.2](#82-mandatory-checkpoint-events) are the guarantee, because every subagent return already forces one.

### 8.4. Low-Quota Mode

`/d3nexus:dev-config low-quota on` (or `--low-quota`) is for the moment the user sees the 5-hour bar at
roughly 15–20 %.

- **Scope.** Quota belongs to an account, so the flag is stored in the global layer keyed by the profile
  from `resume_context.py --detect-profile`: `"low_quota": {"<profile>": {"enabled": true, "expires_at": "<ts>"}}`.
  It expires after 5 hours by default (`--for <hours>`), so a forgotten flag does not throttle the next
  window. `off` clears it.
- **Effects.**
  - The turn budget is halved (8 becomes 4).
  - Reports are reduced to the structured outputs Rule 10 protects (verdicts, findings tables, gate
    results, summary contracts); narration and recaps are dropped.
  - Optional work is skipped: `task-observer` logging and narrative Doc Sync prose.
  - The Orchestrator finishes the task or wave in flight, writes a `low_quota_stop` checkpoint, prints the
    resume prompt (`--emit-prompt implement`), records a `--pending-decision`, and stops. It does not start
    a new wave.
- **Never skipped.** Gates, `gate4-verifier`, reviews required by selective gating, `/cross-model-review`
  rounds, and every halt criterion.

### 8.5. Automatic Quota Gate

Low-quota mode depends on the user noticing the bar. The quota gate does not: it reuses the quota
machinery that `/cross-model-review --auto-quota` already has — `scripts/agy_quota.py` to fetch, and
`evaluate_provider_quota()` with `.devtool/review_config.json["quota_thresholds"]` to judge — and applies it to
persona bindings.

- **When.** The Orchestrator (or the runner) runs `dev_config.py quota-check` before entering Stage 3,
  before dispatching each wave, and before each `/cross-model-review` fix round. It checks the CLIs bound
  to the personas the next step needs, plus the `orchestrator` binding, since that account runs the main
  session.
- **Insufficient.** Any checked persona below its threshold: the Orchestrator writes a `quota_low`
  checkpoint, records `--pending-decision` with `decision_kind: quota` listing each persona's CLI, quota
  line (for example `5H=12.0%, 7D=40.0%`) and the ready commands to recover (switch profile,
  `/d3nexus:dev-config preset <name>` or `set …`), and stops calling tools. It starts no new wave; work
  already dispatched is allowed to return and is checkpointed.
- **Unknown.** When quota cannot be read (no fetcher data, unsupported CLI), the gate does not block; it
  records a `quota_unknown` warning in the checkpoint, which the dashboard shows.
- **Thresholds.** One source of truth: the existing `quota_thresholds`; no second threshold set is added.

## 9. check-tasks Dashboard Sync

`/d3nexus:check-tasks` harvests lifecycle state into its CLI and web dashboard, so every new script and
state introduced here must surface there:

- **Document resolution.** `check_tasks.py` (HLD status scan, epic history) and `tasks_server.py` (epic
  file listing, packaged HLD promotion) use `resolve_epic_doc`. Today `check_tasks.py` scans `.vi.md`
  before `.en.md` in one path; after the change no `.vi.md` is read.
- **Role labels.** `assistant_state.md` `Role:` values `architect`, `orchestrator`, `programmer` (and
  the `assistant` alias) render with the four-persona names; the dashboard's Tri-Role invariant text is
  replaced.
- **Persona bindings.** The repository panel shows the active preset and each persona's resolved model
  and effort with its source layer, read through `persona_config.py`; a validation error renders as a
  warning, not a crash.
- **New halts.** `MODEL_UNAVAILABLE` and `fix-planner` `ESCALATE` arrive through `pending_decision.json`
  (`decision_kind: blocker`) and the runner's halt state, and render as human-action-required alongside the
  existing circuit-breaker halts.
- **Checkpoints.** The epic card shows the latest checkpoint event, its age and `next_step` from the
  heartbeat; the repository panel shows a low-quota badge with its expiry for the current profile; a
  `low_quota_stop` renders as human action.
- **Quota stop.** A `decision_kind: quota` pending decision renders as a human-action alert on the repository
  tab, the approval card and the epic card, showing each insufficient persona's quota line and the recovery
  commands; a `quota_unknown` warning renders as a non-blocking notice.
- **Telemetry.** Each dispatch appends an event to `events_<slug>.jsonl` carrying `persona`, `brief_role`,
  `model` and `effort`, so the epic history modal shows which persona and model did each step.

## 10. Testing Strategy

Tests are parametrised per the kit's anti-test-bloat rules.

- `persona_config.py`: layer precedence (kit, global, project, CLI), preset selection, overrides,
  `{effort}` substitution, every validation failure, legacy-key warnings.
- `dev_config.py`: each command against a temporary `REAL_HOME` and project; atomic write leaves the old
  file intact on a validation failure.
- Dispatch: argv per CLI × mode; `MODEL_UNAVAILABLE` halt with no fallback dispatched.
- `lifecycle_runner.py`: high-risk routing to `fix-planner`, `ESCALATE` on each halt criterion,
  `apply-plan` on `PLANNED`.
- `resolve_epic_doc`: `.md` preferred, `.en.md` fallback, `.vi.md` never returned.
- Context exclusion: no `.vi.md` path appears in any emitted prompt or review bundle.
- Ownership check: disjoint pass, shared-file fail, dependency-ordered pair pass.
- Checkpoints: each event writes the heartbeat block, the state `.md` and one jsonl event under the lock;
  root and worktree mirrors agree; `resume_context.py` prints the latest checkpoint first.
- Runner: turn budget triggers a checkpoint at exactly N calls (N/2 in low-quota mode); `model_unavailable`
  checkpoint precedes the halt and no retry is dispatched; low-quota mode completes the in-flight wave,
  starts no new one, and stops.
- `dev-config low-quota`: per-profile storage, expiry, `off`.
- `dev-config models`: listing marks missing CLIs and current users of an alias; `add` validates CLI and
  efforts; `remove` is refused while the alias is bound.
- Quota gate: parametrised over CLI × (sufficient, insufficient, unreadable) with a stub fetcher;
  insufficient writes `quota_low` and a `quota` pending decision and dispatches nothing; unreadable warns and
  continues.
- check-tasks: HLD resolution never returns `.vi.md`; new role labels; persona panel with a valid and an
  invalid config; `MODEL_UNAVAILABLE`, `ESCALATE`, `low_quota_stop` and `quota` decisions render as human
  action; checkpoint
  and low-quota badge render; dispatch events carry persona fields.
- Contract tests (`test_lifecycle_document_contract.py`, `test_resume_context.py` and others asserting
  role strings) updated to the new numbering.
- `scripts/verify.sh` passes, including link and ToC checks on every edited skill.

## 11. Dependencies, Assumptions, and Risks

- **Role renumbering is wide.** Old "Role 2.1" meant the human; now it means the AI Architect. Every
  reference across about 25 files and several string-asserting tests must move in one epic, or the kit
  contradicts itself. Mitigation: one mapping table, and a test asserting no `Tri-Role` term or old
  numbering remains in `skills/` and `rules/`.
- **Interactive turn counting is best-effort.** Only the runner counts exactly; event checkpoints carry the
  guarantee in interactive sessions.
- **A main session that is itself cut off cannot checkpoint.** The quota gate, low-quota mode and the
  per-subagent checkpoints bound the loss to the work since the last subagent return.
- **Quota data freshness.** The gate is only as current as `agy_quota.py`; a wave can still exhaust quota
  mid-flight, which the `model_unavailable` path then catches.
- **Main-session model is not enforceable.** The handoff prompt names the expected model; the kit cannot
  verify it.
- **`agy` model naming.** The `{effort}` template assumes the current `agy` naming; a change in `agy`
  breaks resolution. `dev-config status` surfaces it as a validation error rather than a silent miss.
- **Plugin versus repository skills.** This epic is built with the installed, older plugin; agents must
  read `skills/` from the working tree (known friction, see the 2026-10-15 dogfood findings).
- **Consuming repositories.** D3Nexus has in-flight epics with `.en.md` + `.vi.md` pairs; legacy
  resolution in [6.2](#62-file-naming-and-legacy-compatibility) keeps them working, including on the check-tasks
  dashboard.
- No dependency on another epic or on a third-party release.

## 12. Open Items

- Local Ollama as a persona binding — a future option, deliberately excluded from the catalogue now.
- Choosing the best preset automatically from live quota; the quota gate only stops and lists commands.
- A hard `Read(**/*.vi.md)` permission deny; not adopted, because it would also block reading a file the
  user names.

## 13. Shared Contract Warnings

This repository has no `shared-contracts/` directory, so no contract check applies and no warnings were
raised.
