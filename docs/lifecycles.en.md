# The three lifecycles

Reference for what each lifecycle in this kit is for, what it produces, and how it runs.

This page **describes**.
To decide which one a specific piece of work belongs to, see [choosing-a-lifecycle.en.md](choosing-a-lifecycle.en.md).

## Contents

1. [At a glance](#at-a-glance)
2. [dev-lifecycle](#dev-lifecycle)
3. [doc-lifecycle](#doc-lifecycle)
4. [lean-product-lifecycle](#lean-product-lifecycle)
5. [What is not a lifecycle](#what-is-not-a-lifecycle)
6. [How they connect](#how-they-connect)

## At a glance

Each lifecycle is defined by what exists when it ends.

| | `dev-lifecycle` | `doc-lifecycle` | `lean-product-lifecycle` |
|---|---|---|---|
| **Purpose** | Build code that ships | Produce a document someone reads | Decide what to build, and for whom |
| **Produces** | A merged branch | A published document | A validated MVP backlog |
| **Gates** | 5 | 4 | 3 |
| **Gate approvers** | 4 human, 1 machine | 3 human, 1 machine | 3 human |
| **Artefacts live in** | `.devtool/epic/<slug>/` | `.devtool/epic/<slug>/`, deliverable in `docs/` | `.devtool/product/<slug>/` |
| **Verified by** | `quality_check` | `doc_quality_check` | human judgement only |

The two quality gates share no tier, no audit and no tooling, and neither invokes the other.

## dev-lifecycle

**Purpose.** Orchestrate epic-scale code work from an idea to a merged branch.
It owns sequence and gates only; each stage's method lives in that stage's own skill.

**What it produces.** A merged branch, plus a High-Level Design in English and Vietnamese,
a Gherkin BDD suite, and one task file per unit of work
— all archived into `.devtool/epic/<slug>/` when the epic closes.

**When it does not apply.** A single component that one implementation plan covers.
That work uses `dev-brainstorming` then `writing-plans`, which leaves this lifecycle and its remaining gates behind.

```mermaid
flowchart TD
    S1["Stage 1 — Inception &amp; Spec<br/>(dev-brainstorming)"]
    G1{"Gate 1<br/>Spec approved?"}
    ROUTE{"Epic-scale?"}
    PLANS(["writing-plans<br/>(leaves this workflow)"])
    S2["Stage 2 — Architecture &amp; Tasks<br/>(dev-designer)"]
    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
    HC{"Handoff choice<br/>package or continue?"}
    PKG["Package epic<br/>handoff.md, status Packaged"]
    PRC{"Principal Review Choice<br/>Done or Principal Review?"}
    PR["run_external_review.py run --kind principal<br/>triage, decisions, revision"]
    PKGSTOP(["Stop: handoff.md and Resume Prompt"])
    S3["Stage 3 — Isolated Execution<br/>(dev-implementation)"]
    G3{"Gate 3<br/>Execution order confirmed?"}
    EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence,<br/>integrate with develop after each task"]
    RC{"Review Choice<br/>Finish, Cross-model review or Local model review?"}
    XR["run_external_review.py run<br/>(review_results.md committed per round)"]
    LR["run_external_review.py run --cli ollama<br/>(review_results.md committed per round)"]
    G4{"Gate 4<br/>audit + result-based traceability + quality_check 🟢 LGTM?"}
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
    PKG --> PRC
    PRC -->|"1. Done"| PKGSTOP
    PRC -->|"2. Principal Review"| PR
    PR -->|"revised and re-packaged"| PKG
    PKGSTOP -.->|"later session or another LLM"| S3
    S3 --> G3
    G3 -->|no, reorder| G3
    G3 -->|yes| EXEC
    EXEC --> G4
    G4 -->|"no, fix findings as Fix commits"| EXEC
    G4 -->|"yes"| RC
    RC -->|"1. Finish"| REVIEW
    RC -->|"2. Cross-model review"| XR
    XR -->|"round recorded"| G4
    RC -->|"3. Local model review"| LR
    LR -->|"round recorded"| G4
    REVIEW --> G5
    G5 -->|"no, changes as Fix commits"| EXEC
    G5 -->|yes| S4
```

The lifecycle proceeds through four stages and five approval gates, with two explicit human choice points:
- **Routing & Handoff Choice**: Once Gate 1 passes, epic-scale work routes to Stage 2 (`dev-designer`). Between Gate 2 and Stage 3, the developer chooses whether to **Package** (`handoff.md`, status `Packaged`, stop for later session or another LLM) or **Continue** into Stage 3 immediately.

When an epic is packaged, the developer faces **Principal Review Choice**: either conclude packaging (**Done**) or run **Principal Review** (a cross-model review of design documents and readiness against the source code via Claude CLI or Codex CLI). Rounds are recorded in `principal_review.md`, triaged with the developer, revised in place, and re-packaged before returning to the choice.
- **Isolated Execution**: Stage 3 executes each task independently in an isolated worktree with TDD and continuous integration into `develop`. Once all tasks are complete, the agent runs Gate 4 on the candidate SHA.
- **Gate 4 and Review Choice loop**: Gate 4 is the only machine verdict in this kit's development path. It grants 🟢 only when `audit_epic.py` exits 0, `check_bdd_traceability.py tests --results` exits 0, and `@quality_check` profile `epic` returns PASS on the exact candidate commit SHA. Every PASS presents **Review Choice**: **Finish** advances to Gate 5; **Cross-model review** (Claude CLI or Codex CLI) records the round and returns to a full Gate 4 run, and so does **Local model review** (a model served by a local Ollama, reviewed task by task). Every review round is triaged with the developer (`run_external_review.py triage`) before any fix. The loop repeats until the developer selects Finish.
- **Gate 5 Developer Kanban Review**: Completed tasks are retained in `.devtool/features/done/` for visual developer sign-off before Stage 4 rebases, verifies by tier, lands the branch with a `--no-ff` merge, and archives tasks into `.devtool/epic/<slug>/`.

### Interrupted and resume states

When work stops or an epic is packaged, the lifecycle resumes deterministically across five operational states:

```mermaid
flowchart TD
    FRESH["Fresh Epic<br/>(Stage 1 or Stage 2, no task files)"]
    PKG["Packaged Epic<br/>(handoff.md present, status Packaged)"]
    INTR["Interrupted Epic<br/>(task files exist, mid-Stage 3)"]
    DONE_EPIC["Completed Epic<br/>(all tasks done, Gate 4 PASS)"]
    INCON["Inconsistent State<br/>(documents modified after packaging)"]

    FRESH -->|"Stage 1-2 completion"| PKG
    FRESH -->|"Continue at Handoff Choice"| INTR
    PKG -->|"Check git log since packaging"| INCON
    PKG -->|"Resume at Stage 3 Gate 3"| INTR
    INCON -->|"Documents win, reconcile staleness"| INTR
    INTR -->|"Task-by-task TDD execution"| DONE_EPIC
    DONE_EPIC -->|"Review Choice + Gate 5 sign-off"| MERGED["Stage 4: Landed Branch & Archival"]
```

These diagrams and explanations describe the lifecycle for humans; runtime skills (`dev-lifecycle`, `dev-implementation`) and scripts are the operational source of truth.

## doc-lifecycle

**Purpose.** Orchestrate work whose deliverable is a document rather than code
— a runbook, a handbook, an onboarding guide, a set of reference pages.

**What it produces.** The finished document, in the place it belongs: `docs/`, a README, a skill's `references/`.
Its working artefacts — the brief, the outline, one task per section — stay in `.devtool/epic/<slug>/`.
A deliverable left inside `.devtool/` has not shipped.

**Why four gates and not five.** Code and prose differ in four ways that change what verification can mean:
the unit of work is a section rather than an independently testable deliverable;
verification is mechanical checks plus human judgement rather than a machine running tests;
the governing constraint is the **audience** rather than the architecture;
and the cost of being wrong is low.
Because the cost of being wrong is low, the gate count stays below the development side's five.

The first of the four is inception, and it is **not optional**.
It was once, and its skip condition asked whether the content was already known
— a question an agent answers yes to essentially always.
What makes a mandatory stage affordable is that its *depth* scales while its *existence* does not:
a runbook still passes through Stage 0, and its spec is three sentences.
A runbook that costs five approvals does not get written through the lifecycle
— it gets written around it.

**When it does not apply.** A typo, a broken link, a single Architecture Decision Record,
or any change a reviewer would not meaningfully gate.

```mermaid
flowchart TD
    S0["Stage 0 — Inception<br/>(doc-brainstorming)"]
    G1{"Gate 1 — spec approved"}
    S1["Stage 1 — Brief &amp; Outline<br/>(doc-designer)"]
    G2{"Gate 2 — brief &amp; outline"}
    S2["Stage 2 — Drafting<br/>(doc-implementation)"]
    G3{"Gate 3 — doc_quality_check 🟢"}
    G4{"Gate 4 — sign-off"}
    S3["Stage 3 — Finish branch<br/>(finishing-a-development-branch)"]

    S0 --> G1 --> S1 --> G2 --> S2 --> G3 --> G4 --> S3
```

Stage 0 is mandatory — its depth scales, its existence does not.
Stage 1 establishes the audience, classifies the document into exactly one Diátaxis type,
and turns the outline into one task per section.

## lean-product-lifecycle

**Purpose.** Decide what to build and for whom, before any engineering begins.
It implements Dan Olsen's Lean Product Process and enforces problem-space discipline:
needs are described as needs, not as the features someone already has in mind.

**What it produces.** Three signed-off specifications in `.devtool/product/<slug>/` — `01_problem_space_spec.md`, `02_value_proposition_spec.md`, `03_mvp_feature_backlog.md`.
The backlog is what engineering receives.

**What it does not cover.** Steps 5 and 6 of Olsen's process
— building an MVP prototype and testing it with customers — are not implemented in this release.
The orchestrator says so at Gate 3 rather than implying the journey is complete.

```mermaid
flowchart TD
    IN(["A raw idea, or either brainstorming variant's step-2 escape"])
    S1["Stage 1 — Problem Space<br/>(lean-market-discovery)"]
    G1{"Gate 1 — problem space"}
    S2["Stage 2 — Value Proposition<br/>(lean-value-strategy)"]
    G2{"Gate 2 — value proposition"}
    S3["Stage 3 — MVP Feature Set<br/>(lean-mvp-scoping)"]
    G3{"Gate 3 — MVP backlog"}
    OUT(["Handoff to dev-designer"])

    IN --> S1 --> G1 --> S2 --> G2 --> S3 --> G3 --> OUT
    G1 -.->|"re-segment"| S1
    G2 -.->|"needs were wrong"| S1
    G3 -.->|"scope bloated"| S3
```

The dotted edges are the Tectonic Plates protocol: when a gate fails,
the failing hypothesis is located on the five-layer Product-Market Fit Pyramid and re-validated from there upward,
rather than patched at the layer the work is standing on.

## What is not a lifecycle

Five things route work without being lifecycles themselves.

| | What it is | Gates |
|---|---|---|
| `brainstorming` | The router. Asks whether the work is idea development, a document, or coding, then invokes the matching variant. Holds no process of its own | None — it routes and is finished |
| `dev-brainstorming` | Turns an idea for code work into an approved design spec. Exits to `dev-designer`, `writing-plans` or `lean-product-lifecycle` | A design approval and a spec review, both human |
| `doc-brainstorming` | Turns an idea or a document request into an approved content spec. Exits to `doc-designer`, `decision-records` or `lean-product-lifecycle` | A design approval and a spec review, both human |
| `writing-plans` + an executor | The small-code path. `writing-plans` produces the plan; `subagent-driven-development` or `executing-plans` carries it out | None of its own |
| `decision-records` | A single Architecture Decision Record or spike report, written and committed directly | None |

## How they connect

```mermaid
flowchart LR
    BS["brainstorming<br/>(router)"]
    DEVB["dev-brainstorming"]
    DOCB["doc-brainstorming"]
    LEAN["lean-product-lifecycle"]
    DEV["dev-lifecycle"]
    DOC["doc-lifecycle"]
    PLANS["writing-plans + executor"]

    BS -->|"coding"| DEVB
    BS -->|"idea or document"| DOCB
    DEVB -->|"epic-scale"| DEV
    DEVB -->|"one plan"| PLANS
    DOCB --> DOC
    DEVB -.->|"problem space unvalidated"| LEAN
    DOCB -.->|"unevidenced product argument"| LEAN
    LEAN -->|"Gate 3 backlog"| DEV
```

Two rules hold across every connection.
**The deliverable decides, not the amount of writing involved**
— if the work changes a file that ships in the build, it is development work.
And **two specs are never merged into one epic**:
each keeps its own spec → design → implementation lineage.
