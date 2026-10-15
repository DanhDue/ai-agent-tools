---
name: dev-lifecycle
description: Use this skill to orchestrate epic-scale work from idea to merged branch. It owns the sequence and the five approval gates connecting dev-brainstorming, dev-designer, dev-implementation, and quality_check — which skill runs next, what each stage must hand over, and what to do when a gate fails. Activate it when a request spans multiple components or needs an HLD plus a Kanban task breakdown, when routing an approved spec, or whenever it is unclear which epic stage the work is currently in.
---

# Development Lifecycle

The orchestrator for epic-scale work. It owns **sequence and gates only** — each stage's *how*
stays in that stage's own skill. If you need to know how to run a stage, open its skill; if you
need to know what runs next or what must be true before it does, stay here.

**Announce at start:** "I'm using the dev-lifecycle skill to orchestrate the `<epic_slug>` epic."

**Every stage is entered by invoking its skill.** This file names what runs next; it does not
replace it. Reading a stage's description here and then doing that stage's work yourself skips the
gate the stage owns.

## When NOT to use this

- Single-component feature, bugfix, or anything one implementation plan covers → `dev-brainstorming`
  then `writing-plans`. Do not open an epic for it.
- You are already mid-stage and know exactly which stage → go straight to that stage's skill.

## The Sequence

```mermaid
flowchart TD
    S1["Stage 1 — Inception &amp; Spec<br/>(dev-brainstorming)"]
    G1{"Gate 1<br/>Spec approved?"}
    ROUTE{"Epic-scale?"}
    PLANS(["writing-plans<br/>(leaves this workflow)"])
    S2["Stage 2 — Architecture &amp; Tasks<br/>(dev-designer)"]
    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
    HC{"Handoff choice<br/>package or continue?"}
    PKG(["Package epic<br/>handoff.md, status Packaged, stop"])
    S3["Stage 3 — Isolated Execution<br/>(dev-implementation)"]
    G3{"Gate 3<br/>Execution order confirmed?"}
    EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence,<br/>integrate with develop after each task"]
    G4{"Gate 4<br/>BDD traceability + quality_check 🟢 LGTM?"}
    REVIEW["Phase 4.1: Developer Kanban Review<br/>(All tasks held in DONE column for visual inspection)"]
    G5{"Gate 5<br/>User sign-off &amp; finish approved?"}
    S4["Stage 4 — Finish Branch &amp; Archival<br/>(finishing-a-development-branch)"]

    S1 --> G1
    G1 -->|no, revise| S1
    G1 -->|yes| ROUTE
    ROUTE -->|no| PLANS
    ROUTE -->|yes| S2
    S2 --> G2
    G2 -->|no, adjust breakdown| S2
    G2 -->|yes| HC
    HC -->|"1. package"| PKG
    HC -->|"2. continue"| S3
    PKG -.->|"later session or another LLM"| S3
    S3 --> G3
    G3 -->|no, reorder| G3
    G3 -->|yes| EXEC
    EXEC --> G4
    G4 -->|no, fix findings| EXEC
    G4 -->|yes| REVIEW
    REVIEW --> G5
    G5 -->|no, request changes/fixes| EXEC
    G5 -->|yes| S4

```

<HARD-GATE>
Do NOT create `implementation_plan.md` or any Antigravity planning-mode artifact.
The d3nexus workflow replaces the native planning mode entirely.
Specs go to `docs/superpowers/specs/` (Stage 1) or `.devtool/epic/<epic_dir>/` (Stage 2+).
Plans go through `writing-plans` skill (non-epic) or `dev-designer` task files (epic).
If you find yourself about to write `implementation_plan.md`, STOP — you are bypassing a gate.
</HARD-GATE>

## Document Contract

Every durable design document produced by this lifecycle MUST be emitted as a synchronized English
`.en.md` and Vietnamese `.vi.md` pair. English is canonical; Vietnamese matches its structure and
facts. Every variant MUST contain a linked table of contents covering every `##` section, regardless
of document length. This applies to specs, HLD/overview documents, BDD scenario documents, and
non-epic implementation plans. `task_*.md` files and an epic's `handoff.md` are the only exceptions and remain English-only;
`handoff.md` still carries a complete table of contents.

### Markdown Formatting & Lint Standards

Every markdown document produced by this lifecycle MUST pass markdown lint standards:
- **Heading Hierarchy**: Exactly one top-level `# Title` (H1) at the start of the file. Heading levels MUST increment by one (no skipping levels from `#` to `###`). Space after `#` (`# Title`, not `#Title`). No trailing punctuation in headings (`.`, `:`, `,`, `;`).
- **Fenced Code Blocks**: Fenced code blocks MUST specify a language tag (e.g. ````bash`, ````markdown`, ````python`, ````mermaid`, ````dot`, ````json`). Bare fences without a language are prohibited.
- **Lists**: Consistent list markers (`-` for unordered lists), 2-space or 4-space nested indentation, and blank lines separating list blocks from surrounding paragraphs.
- **Links & Anchors**: Relative file links must resolve on disk; heading anchor fragments (`#anchor`) must match existing headings.
- **Formatting Hygiene**: No trailing whitespace at line ends, no hard tabs (use spaces), maximum 1 consecutive blank line, and ensure the file ends with a trailing newline.

### Diagram Standards & Lint Rules (Mermaid & Graphviz DOT)

All diagrams included in any durable document (spec, HLD, BDD scenarios, implementation plan, or doc sync) MUST adhere strictly to the latest modern linting rules:

1. **Mermaid Standards & Lint Rules**:
   - **`flowchart` over `graph`**: ALWAYS use `flowchart` syntax (e.g. `flowchart TD`, `flowchart LR`). NEVER use legacy `graph` syntax (e.g. `graph TD`, `graph LR`). `graph` is legacy Mermaid syntax; `flowchart` is the current keyword and enables per-subgraph `direction` control (e.g. `direction LR` inside a subgraph), richer node shapes, better rendering engines, and styling.
   - **Quote Node Labels**: Enclose any node label containing special characters, parentheses `()`, brackets `[]`, braces `{}`, colons `:`, slashes `/`, ampersands `&`, or punctuation in double quotes (e.g. `node1["Component (Core Logic)"]`, `gate1{"Gate 1: Spec Approved?"}`, `db[("Storage (PostgreSQL)")]`). Unquoted parentheses or colons break parser AST and trigger linter warnings.
   - **Alphanumeric Node IDs**: Use clean alphanumeric IDs with underscores (e.g. `AUTH_SVC`), never spaces, dashes, or dots in the ID itself. Avoid reserved keywords (`end`, `subgraph`, `graph`, `flowchart`).
   - **Edge Syntax & Quotes**: Use standard edges (`-->`, `-.->`, `==>`). Quote edge labels containing parentheses or punctuation (`A -->|"yes (verified)"| B`). Do not append trailing semicolons `;` on flowchart lines.
   - **Subgraphs**: Always specify explicit closing `end`, unique alphanumeric subgraph ID, and a quoted label: `subgraph ID ["Label"]` ... `end`.
   - **Sequence Diagrams**: Use modern `sequenceDiagram` with explicit participants (`actor U as User`, `participant S as Service`), valid arrows (`->>`, `-->>`, `-)`, `--))`), closed blocks (`alt`, `opt`, `loop`, `par`), and optional `autonumber`.
   - **State Diagrams**: Use `stateDiagram-v2` instead of legacy `stateDiagram`.

2. **Graphviz (DOT) Standards & Lint Rules**:
   - Follow semantic node shapes (see `writing-skills/graphviz-conventions.dot`):
     - `[shape=diamond]` for decisions (questions ending in `?`).
     - `[shape=box]` for actions (imperative verbs: "Write test", "Commit changes").
     - `[shape=plaintext]` for shell commands or literal code (`git status`, `npm test`).
     - `[shape=ellipse]` for states or situations ("Test failing", "Build complete").
     - `[shape=octagon, style=filled, fillcolor=red, fontcolor=white]` for critical warnings (`STOP: ...`).
     - `[shape=doublecircle]` for entry/exit points (`Process starts`, `Process complete`).
   - **Statement Semicolons**: Every statement inside DOT must terminate with a semicolon `;`.
   - **Quotes**: Double-quote all multi-word or punctuation-containing node IDs and labels (`"Process starts"`, `label="Is test passing?"`).
   - **Edges**: In `digraph`, edge operator MUST be `->` (NEVER `--`). Label branches explicitly (`[label="yes"]`, `[label="no"]`).
   - **Clusters**: Subgraphs intended to have a visual border MUST begin with `cluster_` (e.g. `subgraph cluster_phase1 { label="Phase 1"; ... }`).

## The Five Gates

Every gate is a **human approval** except Gate 4, which is a machine verdict. Never cross one
on your own judgement.

| Gate | Name | Approver | Enforced in | Handoff artefact |
|------|------|----------|-------------|------------------|
| **1** | Spec Approved | User | end of `dev-brainstorming` | `YYYY-MM-DD-<topic>-design.en.md` + `.vi.md` |
| **2** | HLD & Task Breakdown | User | `dev-designer` task-breakdown checkpoint | `<epic_dir>.en.md` + `.vi.md` + `bdd_scenarios.en.md` + `.vi.md` + `task_*.md` |
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint, or Gate 3 (resume) in its Resume Procedure | confirmed order + bootstrapped worktree |
| **4** | Quality LGTM & Check 2 | `check_bdd_traceability.py` + `quality_check` | `dev-implementation` Phase 4 | 🟢 report + coverage matrix + BDD traceability matrix + merge-ready branch |
| **5** | Developer Kanban Sign-Off | User | `dev-implementation` Phase 4.1 checkpoint | User confirmation to proceed with branch finishing and archival |

## Stages

### Resuming an Epic

A request to implement, continue or resume an epic whose `.devtool/epic/<epic_dir>/` already holds
`task_*.md` files is past Gate 2 — whether the epic was packaged (`handoff.md` present, Status
`Packaged`) or interrupted midway through Stage 3. Announce "Gates 1 and 2 already passed; resuming
at Stage 3", invoke `dev-implementation` with that epic name, and let its Entry-Point Detection
choose where to start. Never redo Stage 1 or Stage 2 for it. New requirements for such an epic are
not a resume: they go to dev-designer's Updating an Existing Epic.

### Stage 1 — Inception & Spec → `dev-brainstorming`

**Invoke `d3nexus:dev-brainstorming`.** Do not write the spec yourself: Gate 1 is *its* user-approval
step, and a spec that never passed through it has not cleared the gate.

**Entry:** a raw idea or requirement.
**Exit (Gate 1):** the user has approved a written spec that passed self-review.

**Routing decision, made here and nowhere else.** Once the spec is approved, choose:

- **Epic-scale code** → `dev-designer`, which is Stage 2 of this lifecycle — multiple independent
  components/services, needs Kanban breakdown plus architecture/use-case/sequence diagrams, or the
  user called it an epic or large feature.
  → relocate both spec variants from `docs/superpowers/specs/` into
  `.devtool/epic/<epic_dir>/` (create the directory if needed), fix relative links inside both
  moved files, then go to Stage 2 passing the canonical `.en.md` path.
- **Everything else** → `writing-plans`. This leaves the epic lifecycle; the remaining gates do
  not apply. `writing-plans` still emits the required `.en.md`/`.vi.md` plan pair with complete
  tables of contents.

When in doubt, ask the user rather than guessing.

If dev-brainstorming decomposed the request into several sub-project specs, **route each one
independently**. Each spec keeps its own spec → design → implementation lineage and gets its own
epic directory. Never merge multiple specs into one epic.

### Stage 2 — Architecture & Tasks → `dev-designer`

**Entry:** a Gate 1 spec, already sitting in `.devtool/epic/<epic_dir>/`.
**Exit (Gate 2):** the user has confirmed the proposed task list and granularity.

Treat the approved spec as the source of truth for scope and decisions already made — formalize
it, do not re-litigate it. Gate 2 is a lightweight confirmation of the *task split* only; the
architecture was already approved at Gate 1.

### Handoff Choice

Between Gate 2 and Stage 3 the developer decides when, and by whom, the epic is implemented. This
is a routing decision like Stage 1's, not a sixth gate. Ask it once `dev-designer` Step 3 has
committed the task files of a new epic — or, with `auto_commit: false`, once they are written.
After dev-designer's Updating an Existing Epic, ask it only when the epic has neither `handoff.md`
nor an epic branch; otherwise leave any `handoff.md` untouched — its staleness rule flags the
update — and continue through Resuming an Epic:

> Gate 2 passed: the HLD, BDD scenarios and N task files for `<epic_slug>` are written. How do you
> want to proceed?
>
> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop, so the work can be
>    picked up later or by another LLM.
> 2. **Continue** — enter Stage 3 now (`dev-implementation`, starting with Gate 3: execution order).

When the overview Status says the epic is queued behind another epic, say so in the question.

**Continue** → invoke `dev-implementation`. **Package** → run the packaging procedure below, then
stop: no worktree and no Stage 3 in this session. Resolve the paths from this skill's directory:

```bash
SKILL_DIR=<absolute path of the directory containing this SKILL.md>
SCRIPTS="$SKILL_DIR/../dev-implementation/resources/scripts"
CHECK_DOC="$SKILL_DIR/../doc_quality_check/resources/scripts/check_document.py"
```

1. **Preflight, read-only.** All of it must pass before anything is written:

   ```bash
   python3 "$SCRIPTS"/compute_execution_order.py <epic_slug>
   ls .devtool/epic/<epic_dir>/task_*.md | wc -l
   python3 "$SCRIPTS"/check_bdd_traceability.py plan \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```

   The scan summary's matched count must equal the number of task mirrors, and both scripts must
   exit 0. A smaller count means broken frontmatter or a wrong `epic:` value; exit 1 means a
   dependency cycle or a scenario no `Covers:` line names. Fix it now — the receiving agent has no
   context to diagnose it.
2. Copy this skill's `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md`
   and fill every placeholder; `<N>` is the task count the preflight printed. The first column of its Identifiers table names the placeholders and
   stays as written; drop the source-spec line when the epic has no source spec. Write Open Notes from this
   session's conversation: decisions, risks and doubts the documents do not record.
3. Lint it: `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
4. Mark the epic packaged, then confirm both overview variants changed — the script reports the
   documents it found, not the documents it wrote:

   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   ```

   Two matching lines are required; with fewer, set the Status line by hand in both variants. If the
   Status read `Queued (backlog) — behind <epic>` before packaging, run the script with
   `"Packaged (queued behind <epic>)"` instead and copy that line into Open Notes; the `grep` still
   matches. Task
   statuses stay as they are, so a packaged epic still counts as active under dev-designer's
   Concurrent-Epic Backlog Rule.
5. Commit, when `auto_commit` is `true` or absent: stage `handoff.md`, the overview pair and any task files fixed at step 1, then
   `git commit -m "[<EPIC_NAME>] Package epic for handoff"`, with no trailer. When `auto_commit` is
   `false`, skip it and warn that an agent in another clone will not see the package.
6. Offer to push, and push only on the developer's explicit permission. Say that a receiver in
   another clone or on another machine needs the push.
7. Print the `handoff.md` path and its rendered Resume Prompt, then stop.

### Stage 3 — Isolated Execution → `dev-implementation`

**Entry:** Gate 2 passed, HLD and `task_*.md` files exist, and the developer chose Continue at
the Handoff Choice — or a packaged or interrupted epic is being resumed (see
[Resuming an Epic](#resuming-an-epic)).
**Exit (Gate 5):** Gate 4 is 🟢 LGTM (BDD traceability and `quality_check`) AND the user explicitly reviews the completed tasks on the Kanban dashboard and approves finishing the branch (Gate 5).

Gate 3 sits inside this stage, at the end of Phase 1: present the computed execution order and
get confirmation **before** creating any worktree or dispatching any subagent.

Then one worktree, one task at a time, one commit per task, docs kept truthful. On divergence
from the HLD, sync the epic docs before starting the next task. After every task, integrate the
branch with `develop` — rebase, then re-verify by tier — before the next one starts.

**Gate 4 Machine Acceptance Criteria:**
Gate 4 grants `🟢 LGTM` only when `check_bdd_traceability.py tests` exits 0 — every scenario in `bdd_scenarios.en.md` covered by at least one integration test, no test referencing a removed scenario — **and** the provider-based quality orchestrator (`@quality_check`) returns an aggregated verdict of **PASS**, both bound to the exact candidate commit SHA (`git rev-parse HEAD`), with `@quality_check` evaluating all registered providers declared in `.agents/quality/check_quality.json` with profile `epic` against `<base_ref>`.

Gate 4 conditions:
1. **Normalized Invocation Contract**: Invocation must explicitly pass `profile: "epic"`, target `base_ref`, and candidate `repository_sha`. Direct defaults or unprofiled executions are rejected.
2. **Deterministic Aggregation**: All registered providers supporting `epic` must execute or resolve cleanly. Precedence is strict: `FAIL > BLOCKED > PASS`. If any provider returns `FAIL` or `BLOCKED`, the overall verdict is `FAIL` or `BLOCKED`.
3. **No Partial or In-Progress Approvals**: `BLOCKED` cannot transition Gate 4 to approved. Parallel provider executions remain one lifecycle gate; the lifecycle waits for complete aggregate synthesis and never approves on the first provider to finish.
4. **Candidate Immutability**: A 🟢 verdict belongs strictly to the SHA on which the traceability check and quality check ran. If any subsequent commit or rebase mutates the branch after Gate 4, the prior verdict is stale and a fresh traceability check and epic quality run are required before landing.

If the traceability check exits non-zero, or `@quality_check` reports `FAIL` or `BLOCKED`, Gate 4 routes back to Stage 3 Phase 2 (`dev-implementation`) with the complete actionable defect and blocker report.

A 🟢 verdict belongs to the SHA it ran on. If `develop` moves after Gate 4, Stage 4 rebases the
branch and re-verifies it by tier before landing.

**Gate 5 Developer Kanban Review & Sign-Off:**
Once Gate 4 passes, all completed tasks MUST remain in `.devtool/features/done/`. The agent MUST STOP calling tools and present the final executive report to the user. The user visually reviews the Kanban board and approves proceeding to Stage 4. If the user requests adjustments or fixes, execution routes back to Stage 3 Phase 2.

### Stage 4 — Finish Branch → `finishing-a-development-branch`

**Entry:** Gate 5 passed (user confirmed).
**Exit:** epic branch rebased onto `develop`, re-verified by tier, landed with a `--no-ff` merge, and done tasks archived into `.devtool/epic/<epic_dir>/`.

## When a Gate Fails

| Gate | On failure, return to |
|------|----------------------|
| 1 | Stage 1 — revise the spec, re-run its self-review |
| 2 | Stage 2 — adjust the breakdown; only revisit Stage 1 if scope itself was wrong |
| 3 | Stage 3 Phase 1 — reorder by hand; prose notes in task files outrank the calculator |
| 4 | Stage 3 Phase 2 — fix findings in the worktree, then re-run the traceability check and `quality_check` in full |
| 5 | Stage 3 Phase 2 — implement user-requested changes or fixes |

Never advance on a partial pass, and never re-run only the previously failing check at Gate 4 —
the 🟢 verdict must come from a complete run.

## Red Flags

- Writing to `implementation_plan.md` or any Antigravity native planning artifact.
- Skipping `dev-brainstorming` because "the scope is already clear".
- Routing an approved spec straight to an implementation skill, skipping Stage 2 for epic-scale work.
- Merging several sub-project specs into one epic directory.
- Creating a worktree or dispatching a subagent before Gate 3. Recreating the worktree of an epic branch that already exists (dev-implementation's Resume Procedure) is not creating one.
- Invoking `dev-implementation` straight after `dev-designer` without asking the Handoff Choice.
- Packaging an epic without the preflight, or pushing the package without explicit permission.
- Treating a packaged epic's Gate 3 as already passed.
- Redoing the design of an epic whose task files already exist; new requirements go to dev-designer's Updating an Existing Epic.
- Merging to `develop` without a 🟢 from Gate 4.
- Granting Gate 4 without a passing traceability check on the same SHA.
- Merging to `develop` by hand instead of through `integrate_branch.py land`.
- Starting a task while the previous task's integration with `develop` is red.
- Invoking `finishing-a-development-branch` without passing Gate 5 (explicit user sign-off after Kanban review).
- Archiving tasks from `.devtool/features/done/` prematurely before Gate 5 user review.
- Leaving a spec split across `docs/superpowers/specs/` and `.devtool/epic/<epic_dir>/`.
- Producing a durable design document without both language variants or without a complete table
  of contents.
- Using legacy Mermaid syntax (e.g. `graph TD`, `graph LR` instead of `flowchart TD`, `flowchart LR`), unquoted special characters/parentheses in node labels, or malformed Graphviz (DOT) diagrams.
- Translating `task_*.md`; task files remain English-only.
- Leaving completed `task_*.md` files in `.devtool/features/done/` or draft specs in `docs/superpowers/` after branch integration.

## Rationalizations — STOP and Re-read This Skill

| Excuse | Reality |
|--------|---------|
| "I already have enough context to skip brainstorming" | Context ≠ spec. Gate 1 requires a written, approved spec. |
| "This is too simple for the full lifecycle" | Simple work uses `dev-brainstorming` → `writing-plans`. You still start at Stage 1. |
| "I'll just write the implementation plan directly" | `implementation_plan.md` is an Antigravity artifact. d3nexus uses `docs/superpowers/specs/` and `.devtool/`. |
| "The user confirmed the scope, that's basically Gate 1" | Gate 1 is spec approval through `dev-brainstorming`, not a scope question. |
| "I can combine research + spec into one step" | Stage 1 is `dev-brainstorming`'s job. Invoke the skill. |
| "The developer obviously wants to continue" | The Handoff Choice is theirs. Ask it every time a new epic passes Gate 2. |

## Stage Skills

| Stage | Skill | Gate it enforces |
|-------|-------|------------------|
| 1 | `dev-brainstorming` | 1 |
| 2 | `dev-designer` | 2 |
| 3 | `dev-implementation` | 3, triggers 4, and enforces 5 |
| 3 (verification) | `quality_check` + `check_bdd_traceability.py` | 4 |
| 4 | `finishing-a-development-branch` | — |
