# Principal Review: sync_shared_contracts

## Round 1

- **Date**: 2026-10-30T12:13:03Z
- **SHA**: 6a2e64df2140c316a46ab0c9a584ea3b1b196c7c
- **Base**: main
- **CLI**: codex
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md:Requirement Analysis §2 | The parser contract supports setup-template tables but does not cover the existing pilot contracts. The live lyrics-sync API declares endpoints through Method/Path sections (`../D3Nexus/shared-contracts/lyrics-sync/api_contract.md:37–42`), and its ledger uses narrative GAP entries with OPEN/PROPOSED/ACCEPTED statuses (`../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:18–29`, `:55–63`, `:79–84`). Template-only fixtures can therefore pass while real requirements remain unparsed. Proposed: specify support for both existing narrative contracts and generated tables, normalize their statuses explicitly, reject unsupported formats instead of reporting empty success, and add hermetic representative fixtures and bilingual BDD coverage. | fixed in 68f6d63 |
| 2 | Important | .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§5.3 and §7 Steps 2–3 | Scope confirmation permits selecting only some deltas/RFCs, but ack automatically acknowledges every Approved/Implemented RFC and records all current file hashes. Completing RFC-001 can consequently acknowledge an unimplemented RFC-002; an upstream edit arriving during implementation is also silently included. The subsequent strict check proves acknowledgement of current files, without preserving outstanding implementation scope. Proposed: bind acknowledgement to the reviewed contract snapshot and explicitly completed scope; reject snapshot changes and retain outstanding requirements, or require complete domain implementation before advancing its watermark. Align Task 3, both language pairs, and BDD tests. | fixed in 68f6d63 |
| 3 | Important | .devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md:Requirement Analysis, lifecycle bridge | The bridge requires isolated worktree execution without defining how relative satellite links remain resolvable there. Existing setup computes the link relative to the original satellite root (`skills/setup-shared-contracts/resources/scripts/setup_contracts.py:326–331`), while implementation creates nested `.worktrees/<epic_dir>` checkouts (`skills/dev-implementation/SKILL.md:144–151`). The unchanged link bytes then resolve from a different directory, making the required check/ack fail despite valid original topology. Proposed: define worktree-aware contract-root resolution that preserves the tracked link, scans and writes state in the execution worktree, and reads the intended Hub snapshot; add a hermetic nested-worktree acceptance scenario and corresponding Task 2 requirements. | fixed in 68f6d63 |
| 4 | Important | .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§4.2, §5.2 and §9 | The brief promises added or modified payload requirements, including Git-less operation, but the watermark retains hashes and endpoint/RFC identifiers without previous payload or invariant content. After a Git-less contract changes an existing field’s type/default, its old hash cannot recover the previous definition. The same problem occurs when acknowledged content was uncommitted and the recorded Git commit does not represent it. Proposed: persist a normalized baseline sufficient for semantic comparison, or explicitly report that historical comparison is unavailable and emit the entire current contract for review; cover same-key semantic changes and uncommitted baselines in Task 3 and bilingual BDD. | fixed in 68f6d63 |

Raw output:

````text
Four issues need resolution before implementation. Candidate source was inspected at `6a2e64df2140c316a46ab0c9a584ea3b1b196c7c`; sibling Hub contracts were inspected as live filesystem evidence, independently of that commit.

Verdict: CHANGES REQUIRED
[Important] .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md:Requirement Analysis §2 — The parser contract supports setup-template tables but does not cover the existing pilot contracts. The live lyrics-sync API declares endpoints through Method/Path sections (`../D3Nexus/shared-contracts/lyrics-sync/api_contract.md:37–42`), and its ledger uses narrative GAP entries with OPEN/PROPOSED/ACCEPTED statuses (`../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:18–29`, `:55–63`, `:79–84`). Template-only fixtures can therefore pass while real requirements remain unparsed. Proposed: specify support for both existing narrative contracts and generated tables, normalize their statuses explicitly, reject unsupported formats instead of reporting empty success, and add hermetic representative fixtures and bilingual BDD coverage.
[Important] .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§5.3 and §7 Steps 2–3 — Scope confirmation permits selecting only some deltas/RFCs, but ack automatically acknowledges every Approved/Implemented RFC and records all current file hashes. Completing RFC-001 can consequently acknowledge an unimplemented RFC-002; an upstream edit arriving during implementation is also silently included. The subsequent strict check proves acknowledgement of current files, without preserving outstanding implementation scope. Proposed: bind acknowledgement to the reviewed contract snapshot and explicitly completed scope; reject snapshot changes and retain outstanding requirements, or require complete domain implementation before advancing its watermark. Align Task 3, both language pairs, and BDD tests.
[Important] .devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md:Requirement Analysis, lifecycle bridge — The bridge requires isolated worktree execution without defining how relative satellite links remain resolvable there. Existing setup computes the link relative to the original satellite root (`skills/setup-shared-contracts/resources/scripts/setup_contracts.py:326–331`), while implementation creates nested `.worktrees/<epic_dir>` checkouts (`skills/dev-implementation/SKILL.md:144–151`). The unchanged link bytes then resolve from a different directory, making the required check/ack fail despite valid original topology. Proposed: define worktree-aware contract-root resolution that preserves the tracked link, scans and writes state in the execution worktree, and reads the intended Hub snapshot; add a hermetic nested-worktree acceptance scenario and corresponding Task 2 requirements.
[Important] .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§4.2, §5.2 and §9 — The brief promises added or modified payload requirements, including Git-less operation, but the watermark retains hashes and endpoint/RFC identifiers without previous payload or invariant content. After a Git-less contract changes an existing field’s type/default, its old hash cannot recover the previous definition. The same problem occurs when acknowledged content was uncommitted and the recorded Git commit does not represent it. Proposed: persist a normalized baseline sufficient for semantic comparison, or explicitly report that historical comparison is unavailable and emit the entire current contract for review; cover same-key semantic changes and uncommitted baselines in Task 3 and bilingual BDD.


--- stderr ---
OpenAI Codex v0.162.1
--------
workdir: /Users/danhdueexoictif/AllProjects/ai-agent-tools
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: medium
reasoning summaries: none
session id: 01a18cb8-9a91-7bd2-9d54-e08f91ccf0a9
--------
user
# Principal Review Prompt

You are the Principal Reviewer who signs off this architectural design before implementation. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the source at `6a2e64df2140c316a46ab0c9a584ea3b1b196c7c`, and report.

## Candidate

- Commit under review: `6a2e64df2140c316a46ab0c9a584ea3b1b196c7c`
- Base the branch diverged from: `main`
- Base commit: `6a2e64df2140c316a46ab0c9a584ea3b1b196c7c`
- Target path / Epic directory: `.devtool/epic/sync_shared_contracts`

## Artefacts

Read these paths, relative to the repository root:

- `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.vi.md`
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.vi.md`
- `.devtool/epic/sync_shared_contracts/bdd_scenarios.en.md`
- `.devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md`
- `.devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md`
- `.devtool/epic/sync_shared_contracts/task_2_heuristic_scanner_and_check_engine.md`
- `.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md`
- `.devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md`
- `.devtool/epic/sync_shared_contracts/handoff.md`

## Readiness facts

Epic: sync_shared_contracts (sync_shared_contracts), 4 tasks
R1 PASS
R2 PASS
R3 PASS
R4 PASS
R5 PASS
R5b WARN /api/v1/lyrics-sync/tasks: not found in tracked source
R5b WARN /api/v1/lyrics-sync/status: not found in tracked source
R6 PASS
R7 PASS
R8 SKIP
Result: 0 FAIL, 2 WARN — PASS

The readiness report is already proven: all facts above have passed their mechanical checks; do not restate them, spend your review on judgement, architecture, and source grounding.

## Rules

# Principal Review Rules

To avoid false-positive findings, evaluate design documents and epic artefacts against these principles:

1. **Severities**:
   - **Critical**: The epic or architecture cannot reach its goal or pass execution gates as designed (e.g. fatal architectural flaw, missing core contract).
   - **Important**: A task or component would hit Stop-and-Report, ship incorrect behavior, or break module isolation during implementation.
   - **Minor**: Wording, formatting, typo, and minor consistency adjustments.

2. **Readiness Report Is Proven Fact**:
   - The mechanical checks (R1–R8) in `check_epic_readiness.py` are already validated prior to review.
   - Do not re-verify mechanically checked facts or restate them as findings; spend your review effort on judgement, architecture, and source grounding.

3. **Grounding in Active Source**:
   - Every claim about the repository source code must name the specific file and line number read.
   - Grounding verifies that referenced symbols, functions, methods, and configurations actually exist at the candidate commit.

4. **Actionable Findings**:
   - Each finding must name the specific artefact (file path) and location (heading or section) to change.
   - Each finding must conclude with a concrete `Proposed: <edit>` recommendation.

5. **Shared Contracts & Symlink Resolution**:
   - When reviewing design documents impacting inter-service or cross-repo communication, verify that `shared-contracts/` paths resolve on disk (following symlinks to target repositories if applicable).
   - Flag any breaking schema change without backward-compatibility shims or transition windows as **Critical**.
   - Flag any missing `## Shared Contract Impact` section or failure to prioritize contract updates in `task_01` as **Important**.

## Checklist

- **P1 (Consistency)**: Consistency across spec, HLD, BDD, tasks, and documentation: decisions, field names, numbers, titles, statuses.
- **P2 (Grounding)**: Grounding: every path, symbol, signature, return type, route, and constant in `Decisions Already Made` and `Impact Analysis` exists in source code as described.
- **P3 (Pinned behaviour)**: Pinned behaviour: existing tests that pin a behaviour a task changes, especially when outside Allowed files.
- **P4 (Blast radius)**: Blast radius: other writers and readers of changed data, background jobs, callers outside Allowed files, migrations and backfill.
- **P5 (Task split and Verification)**: Task split and Verification: dependency order, RED rows that can fail before implementation, GREEN rows that pass at baseline, DoD references, Stop conditions.
- **P6 (BDD quality)**: BDD quality: valid Gherkin, dimensions that match scenarios, grounded assertions, tier tags.
- **P7 (Shared Contracts & Feasibility)**: Verification Environment, integration test feasibility, and cross-repo contract audit. When `shared-contracts/` (or an external service/FFI boundary) is touched, inspect `shared-contracts/<domain>/` canonical files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`) on disk (including resolving symlinks to target repositories if applicable). Verify that the HLD contains a dedicated `## Shared Contract Impact` section, guarantees backward compatibility (optional fields, safe defaults, no breaking wire changes), reserves `task_01` for contract synchronization, and outputs the Parallel Handoff Summary for satellite repos.
- **P8 (Risks, rollout and rollback)**: Risks, rollout and rollback.

## Required output

Do NOT use the bracketed tags `[Critical]`, `[Important]`, or `[Minor]` anywhere in your prose or analysis above the final verdict block.

End your answer with these exact lines and nothing after them (no markdown bolding `**`, no backticks, no bullet before `Verdict:`):

Verdict: PASS
(or `Verdict: CHANGES REQUIRED`)
[Critical|Important|Minor] <artefact>:<location> — <problem>. Proposed: <edit>

Rules for Severity & Verdict:
- Use `Critical` for a defect that breaks the design goal, `Important` for one that must be fixed before implementation, and `Minor` for anything else.
- Output `Verdict: CHANGES REQUIRED` if and only if there is at least one `Critical` or `Important` finding.
- If there are no findings (or only `Minor` findings), you MUST output `Verdict: PASS`.
- A review with no finding still ends with its `Verdict: PASS` line.

hook: SessionStart
hook: SessionStart Completed
codex
I’m using `d3nexus:principal-review` to assess the design against the pinned source, with `d3nexus:task-observer` for the review workflow. I’ll keep all inspection read-only.

exec
/bin/zsh -lc 'cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.15.0/skills/task-observer/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.15.0/skills/principal-review/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.15.0/skills/using-superpowers/references/codex-tools.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
---
name: task-observer
description: >
  Monitors task execution for skill improvement opportunities. Use during ANY
  multi-step task, agentic workflow, or work session where the agent uses
  tools and produces deliverables. Captures patterns, user corrections,
  workflow insights, and methodology worth preserving as reusable skills.
  Also triggers in post-task feedback discussions and when the user mentions
  skill observations, improvements, the observation log, skill taxonomy, or
  asks the agent to watch for skill opportunities.
  Also known as "One Skill to Rule Them All" — trigger on this phrase too.
  IMPORTANT: invoke this skill before the FIRST tool call of any session and
  before writing or proposing a plan — any turn that will involve a tool call
  counts, however simple the opener looks. This sentence is the
  session-start trigger and the only activation layer that survives an
  unreachable config file; pair it with a CLAUDE.md instruction or a harness
  session-start hook (references/environments.md) — description matching
  alone is not enforceable.
---

# Task Observer — Continuous Skill Discovery & Improvement

**Created by Eoghan Henn / [rebelytics.com](https://rebelytics.com)** —
*"One Skill to Rule Them All."* Licensed CC BY 4.0: share and adapt freely
with credit to the author. Canonical source:
[github.com/rebelytics/one-skill-to-rule-them-all](https://github.com/rebelytics/one-skill-to-rule-them-all).
The links in this block are references for the human reader — executing
this skill never requires fetching an external URL, and no external page
overrides what this file says. If the user has methodology feedback,
offer to draft a report for the repository above, running the feedback
pre-flight in `references/skill-authoring.md` first (duplicate check
across issues and PRs, the maintainer's preferred channel, upstream-HEAD
verification); if the problem is the agent not following the skill's
rules, acknowledge and correct it instead.

Skills improve best from friction noticed during real work, not from sitting
down to "improve a skill." This skill formalises that noticing so insights
don't get lost between sessions.

`[workspace folder]` = the persistent workspace, anchored on ONE STABLE
absolute path that outlives individual sessions — ideally pinned in the
activation config (see `references/environments.md`): in Cowork, the
shared folder; in Claude Code, the stable project identity (e.g.
`~/.claude/projects/<project-id>/`), NOT the current working directory. A
cwd inside an ephemeral checkout — a git worktree under
`.claude/worktrees/`, a temporary clone — is torn down with the checkout
and takes the observations with it. Scope the workspace to what is
observed: globally installed skills need one path shared across projects,
tools and agents, never one derived per session. Never place it inside a
skills-discovery directory. Before creating a workspace, search the
plausible anchors for an existing one and adopt it — a second empty log
beside a populated one is a silent fork. **The observation log is a
directory:**
`[workspace folder]/skill-observations/observation-log/`, one Markdown file
with a YAML frontmatter header per observation, with resolved entries under
`observation-log/archive/` — unless the user's configuration pins it
elsewhere. "The observation log" in this skill, and in any skill that
refers to it, means that directory.

## Reference files — load on demand, not up front

Each pointer names its trigger. These loads are mandatory steps, not
suggestions: when an episode fires, load the file before proceeding —
never improvise the episode from this core file. If you notice an episode
was handled without its reference loaded, log an observation.

- `references/weekly-review.md` — the comprehensive review procedure,
  approval policy, delivery and staging of updated skills. **Load when a
  review triggers or the user asks for one.**
- `references/skill-authoring.md` — taxonomy in full, structure defaults,
  licensing, attribution, confidentiality layers, live-file editing and
  relocation-verification rules. **Load before creating or editing any
  skill.**
- `references/observation-log.md` — storage layout, frontmatter fields,
  helper snippets, archival details, and the reasoning behind the rules.
  **Load when setting up the log for the first time, when archiving, when
  an id or frontmatter looks wrong, or before changing how anything reads
  the log.**
- `references/signals.md` — the full catalogue of what is and isn't worth
  logging. **Load when unsure whether something is an observation, or when
  sorting many candidates.**
- `references/environments.md` — activation and config setup, compaction
  behaviour, bundle manifest, handoff-doc mode for storage-less
  environments. **Load for setup questions, after compaction, or when
  there is no filesystem.**
- `references/migration.md` — the one-time scripted conversion of a
  pre-3.0 single-file `log.md`. **Load only when the Session Start
  Protocol detects a legacy log.** Fresh installs never read it.

## Session Start Protocol

1. **Storage.** If `skill-observations/observation-log/` (with its
   `archive/` subdirectory) or
   `skill-observations/cross-cutting-principles.md` don't exist,
   create them (principles template: `references/skill-authoring.md`).
   Create `skill-observations/last-review-date.txt` containing the literal
   value `never` if it doesn't exist — never write a date into it at setup;
   a date means a review actually ran. If a legacy single-file
   `skill-observations/log.md` exists and `observation-log/` does not, this
   is an upgrade from a pre-3.0 install: load `references/migration.md` and
   run the scripted conversion before writing anything else. Before
   creating or writing anything: if the resolved workspace folder sits
   under an ephemeral path (e.g. `.claude/worktrees/`, a temporary clone),
   warn the user and re-anchor on the stable project path first — state
   written to an ephemeral checkout is lost at teardown.
2. **Scan.** Read only the frontmatter of each file in `observation-log/`
   — the header block between the first two `---` lines, never the bodies
   — and build awareness from `status`, `skill`, `proposes_skill` and
   `title`; also read the active principles. Hold them in awareness, don't
   surface unprompted. Frontmatter-only is the whole point of the per-file
   format: the scan stays cheap once hundreds of observations exist.

   **An empty scan in a log known to be non-empty is a broken command
   until proven otherwise**, never the finding "no relevant observations".
   Count the files independently of the parse — a literal path, not the
   variable the loop uses — and halt if files exist but nothing parsed.
   Re-derive every path inside the same tool call: shell state does not
   carry between calls in most harnesses, and a path variable that
   silently resolves to empty turns a filter into a match-nothing glob
   rather than an error.

   ```bash
   d=skill-observations/observation-log                                # re-derive in EVERY call
   n=$(ls skill-observations/observation-log/*.md 2>/dev/null | wc -l) # literal path: independent of $d
   parsed=0
   for f in "$d"/*.md; do
     [ -e "$f" ] || continue
     hdr=$(awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
                fm && /^---[[:space:]]*$/ {exit}
                fm' "$f")
     [ -n "$hdr" ] && parsed=$(( parsed + 1 ))
     printf '%s\n---\n' "$hdr"
   done
   [ "$n" -gt 0 ] && [ "$parsed" -eq 0 ] && \
     { echo "SCAN COMMAND BROKEN — $n files present, 0 headers parsed"; exit 1; }
   ```
3. **Review trigger.** Read `skill-observations/last-review-date.txt`. The
   value carries the truth: a date = when the last review actually ran;
   `never` = no review has run yet. A missing file is abnormal (step 1
   creates it) — recreate it with `never`, don't invent a date. If the
   value is `never` or older than 7 days AND there are OPEN observations:
   in an interactive session, offer the review in one line ("the
   observation backlog hasn't been reviewed [in N days / yet] — run it now,
   or carry on with your task?") and proceed with the user's task unless
   they opt in; never gate their work on the review. Only a
   scheduled/autonomous run loads `references/weekly-review.md` and runs
   the review unprompted.
4. **Activation.** Once per session: if no CLAUDE.md (or equivalent)
   activation instruction for this skill exists, briefly suggest adding one
   (see `references/environments.md`). Skip if already configured.
5. **Concurrency.** There is no shared log file to guard: each observation
   is its own file, so creating one never collides with or overwrites
   another session's entry. Before changing the *status* of an existing
   observation, re-read that one file first (a parallel review may have
   resolved it).
6. **Targets and staged work.** Resolve each distinct `skill:` value in
   the scanned frontmatter against the installed skill set and mention, in
   one line, any that no longer resolve — a deleted skill can accumulate
   dozens of observations before a review discovers the target is gone.
   If `skill-updates/PENDING.md` lists staged updates, say "N staged
   updates awaiting review" in one line.
7. **First run.** If the log is empty and the project has history
   (handover or decision docs, commit history, test scripts, an existing
   CLAUDE.md — which is largely a record of corrections nobody logged),
   offer a one-off backfill pass over those artefacts. Backfilled entries
   cite the durable artefact (file and section) in `session_context`
   instead of a session, and the same-turn immediacy rule is satisfied by
   one batched write. The pass is one-off; the scheduled review takes
   over afterwards.

## When to Observe

Active for the entire task session — execution, post-task feedback, review
discussion, meta-discussion about skills or methodology, and strategy
conversations about how work should be done. **The observation mindset
does not deactivate when the conversation shifts from doing the work to
discussing it**; review-phase feedback is often the highest-signal input.
Inactive only for casual conversation and quick factual questions with no
tools or deliverables involved.

## What to Watch For

**New skill:** a reusable multi-step workflow, a methodology the user
explains that no skill captures, a recurring task type, a process the user
describes as "I always do it this way". **Improve a skill:** the agent
violates a documented rule (the skill needs enforcement, not louder rules);
a user correction reveals a missing rule or edge case; a better workflow or
technique emerges than the skill recommends; a wrong assumption; new
tooling obsoletes a step; a principle that applies to other skills too.
**Simplify a skill:** a section never relevant across many sessions, a rule
from a single unvalidated observation, contradictory rules, a rule the
agent consistently fails to follow — convert to structural enforcement or
remove. Full catalogue with examples: `references/signals.md`.

**Do NOT log:** one-off corrections that don't generalise; preferences
already captured in a skill; tool bugs unrelated to methodology;
observations that would need proprietary client information to be useful
in an open-source skill (unless an internal skill is the right home). The
generalisability test, when unsure: would this still make sense in another
project, and for another task using the same skill? Does it name a missing
rule, step or principle rather than fix this task? Is it likely to recur?
Mostly no → task context, not an observation. Before minting a
`proposes_skill` name, check the existing candidates and reuse a fitting
one — independently logged proposals for one skill rarely share a name.

**Validate the target at write time.** A name in `skill:` must be a skill
that exists now; if it doesn't, the observation proposes a skill instead.
Checking is cheap at write time and expensive forty entries later.

**Check the target's siblings at write time, and record that you did.**
Libraries accumulate *families* — several skills implementing one
methodology for different tools, one structure for different subjects, one
companion pattern for different base skills. An insight found while using
one member usually applies to the rest, but nothing in the workflow asks,
so `skill:` collapses to a single entry and the family silently diverges.
Before writing, resolve the target against the family registry
(`skill-observations/skill-families.md`; spec, coherence models and the
no-registry fallback in `references/observation-log.md`), and for each
sibling either add it to `skill:` or state in the body why it does not
apply. Fast test: **could this sentence survive having the tool's or
subject's name removed?** If yes it belongs to every sibling — and a rule
that declares itself generic inside one artefact ("this applies to any
file-writing script, not just X") is the cheapest possible propagation
signal, so treat that phrasing as an automatic multi-skill flag. Then
record the outcome in the mandatory `siblings_checked:` frontmatter field,
including the verdict "checked — instance-specific, no propagation": a
one-entry `skill:` list is byte-identical whether the siblings were
evaluated or never considered, and only the recorded field makes the
*absence* of the judgement visible to a review or a drift audit.

## How to Log

Write the observation file **silently, within the same turn or the next** —
never batch mentally for later; the act of writing is the enforcement
mechanism.

**Mandatory checkpoint after every 3rd completed todo item.** After marking
the 3rd, 6th, 9th (etc.) item complete, you must **write to disk** — not
merely ask yourself whether anything is pending. Either write any pending
observation files, or, if genuinely none have accumulated, append a
one-line `no observations` acknowledgement to
`skill-observations/checkpoints.log`. The required action is a concrete
write; a remembered "ask whether" is not enforcement. The count need not be
precise; roughly every third completion is the rule. (Exception: where the
workspace is a shared hosted document store in which every write is priced
and invalidates other sessions' context, suppress the empty marker and
keep only the check — see `references/environments.md`.)

**A denied or failed write is not a read-only log.** Retry once before
concluding the workspace is unwritable, and try a second tool that reaches
the same path — a permission classifier can deny one interface while
allowing another, and consecutive denials from a probabilistic gatekeeper
are noise, not a wall. Report "failed N times", never "cannot be done",
unless retries and alternate interfaces are actually exhausted; otherwise
observations are silently lost for the rest of the session.

**Deliverable-event flush.** Whenever you present or render a major
deliverable — a file handed to the user, a deck or PDF render, a staged
skill file — or complete a task/todo batch, write any pending observation
files at that moment, before moving on. These checkpoints already involve a
tool call; piggy-backing the flush onto them makes the write a side effect
of work you were doing anyway. (Why both checkpoints are writes rather than
questions: `references/observation-log.md`.)

**Two gaps this pairing still leaves — both observed across full working days
in which nothing was logged at all.**

1. *A session can contain no todo items whatsoever.* The 3rd-completion
   checkpoint is bound to ONE tool; work driven entirely through direct tool
   calls and shell commands never trips it. It is armed only in sessions that
   happen to use todos, so it is not a safety net that is always present. When
   a session runs without them, the deliverable flush is the only enforcement
   left and must be applied deliberately.
2. *"Is this a major deliverable?" is a self-assessment, and self-assessment is
   what fails under load.* Prefer triggers unmistakable in the tool record over
   ones needing a judgement call. In particular, treat any **project-completing
   command** — a deploy, release, publish, or push — as a flush point: it is a
   concrete tool call, as hard a trigger as a completed todo, and it reliably
   marks the end of a unit of work where insights have accumulated.

The rule behind both: an enforcement trigger must hang on an event objectively
visible in the tool record, never on the agent noticing that a moment qualifies.
And a counter bound to a single tool is silently inert in every session that does
not use it — such triggers always need a second, independent path.

**Id and filename.** Each observation is `NNNN-short-slug.md` (zero-padded
id + a kebab-case slug from the title). The id is the highest of three
values, plus one: the highest numeric prefix in `observation-log/`, the
highest in `observation-log/archive/`, and the number in
`observation-log/archive/.id-floor` (the highest id ever issued — update it
whenever you issue an id above it, so the counter can never restart from 1
when the active directory is empty):

```bash
d=skill-observations/observation-log
hi=$( { ls "$d" "$d/archive" 2>/dev/null | grep -oE '^[0-9]+'; cat "$d/archive/.id-floor" 2>/dev/null; } \
     | sort -n | tail -1); : "${hi:=0}"
[ "$hi" -eq 0 ] && [ -n "$(ls "$d"/*.md 2>/dev/null)" ] && { echo "ID COMMAND BROKEN — log is non-empty but no ids extracted"; exit 1; }
next_id=$(( hi + 1 )); echo "$next_id" > "$d/archive/.id-floor"
```

The guard line distinguishes "the log says zero" from "I could not read
the log": a command that fails to empty rather than to error would
otherwise propose id 1 in a populated log. A new file never touches another entry's bytes, so it cannot truncate,
overwrite or renumber anyone else's work. If two parallel sessions pick the
same id, two files share a number — harmless; the next review renumbers one
and logs a meta-observation.

**Batch writes: resolve each id at its own write time.** When logging more
than one observation in a session that may overlap a scheduled review or
another writer, run the id snippet before EACH file — never pre-compute a
range and hardcode sequential numbers into a batch. A batch append is N
separate races, not one; pre-baked numbers collapse N independent
max-checks into a single stale read (observed: a hardcoded id collided
with one a parallel review issued between the check and the write).

**A structural probe that comes back empty where content existed before is
a stop signal, not a create.** If the directory or file you logged to
earlier in the session is suddenly missing, or the id check returns empty
in a log you know is populated, HALT and re-probe the structure (is there
an `observation-log/`? a `log.md.migrated`?) — a parallel session may have
migrated or reorganised the storage. Never let an append silently recreate
a missing target: that converts a migration signal into corruption
(observed: a stale session recreated the retired `log.md` with a fresh
"Observation 1" after the per-file migration renamed it).

**File format.** YAML frontmatter (the metadata every scan reads) followed
by the Issue → Improvement → Principle body. **The frontmatter is mandatory;
always write `status: open` and a non-empty `siblings_checked:` at creation
time** — an observation without a `status` field is treated as OPEN by
reviews, never as nonexistent, and one without `siblings_checked:` counts
as logged without a sibling check.

```markdown
---
id: [N]
title: [Short descriptive title]
status: open            # open | actioned | declined | superseded | parked
type: open-source       # open-source | internal
skill: [list of existing skills this improves — always a list, even with
       one entry; first entry is primary; may be empty]
proposes_skill: [list of new skills this argues for, by working name;
       may be empty — an observation can fill either list or both]
siblings_checked: [MANDATORY, never blank: the family name and the members
       evaluated, plus the verdict — e.g. "family-name: a, b — shared, both
       added" or "family-name: a, b — instance-specific, no propagation";
       the literal `none` only where the target belongs to no family]
area: [which part of the skill or workflow]
date: [YYYY-MM-DD]
session_context: [what task was being worked on]
parked_until:           # MANDATORY when status is parked, empty otherwise:
                        #   one line naming the condition that unparks it
resolved:               # date resolved; leave empty while OPEN
resolution:             # what was done — set only when actioned/declined
reference:              # optional: path to saved session-local evidence
---

**Issue:** [What happened — specific enough to understand weeks later
without the original conversation.]

**Suggested improvement:** [Concrete change. For existing skills, name the
section or rule; for new skills, scope and key components.]

**Principle:** [The generalisable takeaway — the most important field.]
```

**`parked` means decided, not pending.** Use it when an observation is sound
but cannot be acted on until an external precondition is met — the scheduled
task that produced it is disabled, the tool it describes is out of use, a
dependency has not landed. A parked entry is OUT of the work queue: reviews
must not re-escalate it, and the decision belongs in `status:`, not in a
free-text note beside a `status: open` (a note nothing classifies on leaves
the entry in the queue and it gets re-raised at every review). It is not
resolved either, so it never archives — archival needs a resolved status plus
a `resolved:` date. It stays in `observation-log/` indefinitely until either
its `parked_until:` condition is met — set it back to `open` and queue it — or
it is genuinely resolved. `parked_until:` is mandatory whenever status is
`parked`: one line stating the condition, phrased so a later session can
actually answer whether it has happened.

**Context preservation:** if an observation depends on session-local data
(uploads, API output), save that context into the workspace first and set
`reference:` to its path — an observation whose evidence dies with the
session is incomplete.

**Confidentiality at logging time:** for `type: open-source` observations,
the Issue/Improvement fields may reference specifics for context, but the
Principle must be fully generalised — no client names, domains, or details
traceable to a real project. Full confidentiality layers:
`references/skill-authoring.md`.

**Changing an existing observation:** re-read that one file, edit only the
frontmatter fields you are changing (`status`, `parked_until`, `resolved`,
`resolution`),
never batch-rewrite the directory. Archival is a plain `mv` (below).

## Referencing Observations

Cite an observation by the `id` field in its frontmatter (= the `NNNN-`
filename prefix). Never cite a `grep -n` line number as if it were the id —
search-tool line numbers are positional metadata, not identifiers. A cited
id must fall within the range that exists across `observation-log/`,
`archive/` and `.id-floor`; a number far outside it is almost certainly a
line number misread as an id.

## Taxonomy (quick version)

**Open-source** — client-agnostic, methodology-driven, useful to other
practitioners. **Internal** — contains user/client/project specifics or
personal preferences. Default to open-source when it could go either way,
stripping specifics. The boundary is also a confidentiality boundary, and
the two errors are not symmetric: over-classifying as internal costs only
reach, under-classifying can leak — when genuinely uncertain, prefer
internal and promote later. Full requirements (attribution, licensing,
structure): `references/skill-authoring.md`.

## Archival on Write

On every write, first `mv` already-resolved files from `observation-log/`
to `observation-log/archive/`. "Already resolved" is read from the file's
own frontmatter: `status: actioned`, `declined` or `superseded` AND a
`resolved:` date **before today**. Files resolved today stay until the next
day, whichever session resolved them — the grace period lives in the file,
never in session memory. A resolved file with no readable `resolved:` date
gets today's date written to that field instead of being archived. One
file per `mv`; no rewrite of anything else. Helper and rationale:
`references/observation-log.md`.

## Surfacing Protocol

Default: at end of session, as a grouped summary — improvements grouped by
skill, new-skill candidates listed separately; for each, one sentence plus
suggested type; ask which to act on. Surface earlier when an observation
needs user input to be complete, when a skill is actively producing wrong
output, or when observations cluster on one skill.

**Deferral wears a second disguise: not a promise, but an argument.** "Let's
wait until this has seen a few days of real use", "we should gather more data
first" — this reads as diligence, which is exactly why it goes unchallenged,
including by the person saying it. It is not an announcement, so a rule about
executing rather than announcing does not catch it. So before writing *any*
"later" into a recommendation, name two things: **which specific observation
would change the decision, and when it could realistically arrive.** If you
cannot name one, the evidence is either already conclusive (act now) or waiting
adds nothing (act now). Then ask what the delay costs — if a known-defective
state stays live meanwhile, the burden of proof is on deferring, not on acting.
A deferral is a decision and needs the same justification as acting; "more
evidence would be better" is not one, because the question is whether more
evidence could change the OUTCOME.

**Default to log-and-defer.** Surfacing an observation is not an invitation
to act on it: state that it is logged for the next review, and stop.
Reserve in-session application strictly for the triggers under "Acting on
Observations". Do NOT routinely offer a binary "apply now vs leave for next
review" choice; for users who run regular reviews that offer is unwanted
friction, and if a user has said they always defer, suppress it entirely.

**Self-check before surfacing:** observations were logged throughout the
whole session (including discussion phases); logged silently; each follows
Issue → Improvement → Principle; each is typed; existing-skill items name
the section; no open-source Principle contains client-identifying info;
every observation file carries `status:` (`status: open` at write time) and
a non-empty `siblings_checked:` — if any lacks one, do the sibling check
now and record it rather than back-filling the field with `none`.

## Acting on Observations

Act only in three contexts: (1) the comprehensive review (load
`references/weekly-review.md`); (2) an explicit user request ("update X
skill", "act on observation #N"); (3) in-session correction when a skill is
producing wrong output the user should know about. Otherwise: log, don't
act.

**Read the full body before resolving, dismissing, fixing, or citing.** A
tracked item's title (observation, GitHub issue, ticket) is an index entry,
not its content — it compresses away the failure story, the reporter's
context, and often the proposed fix. Dismissal is the path with no
downstream checkpoint: a resolved or cited item gets reviewed later, a
dismissed one silently disappears. Harvest fix designs from issue bodies —
reporters frequently include the correct solution, which also settles
attribution. When a parallel agent logs a finding that appears to duplicate
your own, diff the two bodies, not the titles: two entries about the same
mechanism can carry opposite operational conclusions, and the second is
often the refinement, not the echo. Apparent agreement suppresses
verification more effectively than disagreement does, so this rule binds
hardest exactly where it feels least necessary.

When acting: small, clearly-additive, low-risk changes (a new rule, a
clarification, a factual fix) may be applied without waiting for the next
review — "directly" means *now*, not *in place*: the edit is still made on
a staged copy based on a fresh read of the live file and handed to the user
to install, in every environment and every context. Staging-only has no
interactive exception; an exception the user has to remember is a gate
that eventually gets left open. Substantial changes (restructuring, new
capabilities, changed methodology) and all new-skill creation: load
`references/skill-authoring.md` first and follow its editing and staging
rules. A principle that applies to skills generally goes to the
cross-cutting principles file (same reference).

**Set the status in the same turn you act.** An observation acted on
in-session must have its frontmatter updated — `status: actioned`,
`resolved: YYYY-MM-DD`, `resolution: what was done` — before the turn
ends. The work and the bookkeeping are two acts, and the second is the one
that gets dropped; a stale `open` entry then invites redoing finished work
over a section that has since moved on. The write is the enforcement,
exactly as it is for logging.

## Quick Reference

| Question | Answer |
|----------|--------|
| When do I observe? | The whole session, including feedback and reflection phases |
| How do I log? | Silently, immediately, as one file per observation named `NNNN-slug.md`; id = max(active, archive, `.id-floor`) + 1 |
| When do I surface? | End of session, or earlier if needed |
| Status field? | Mandatory `status: open` frontmatter on every new observation; reviews treat a missing status as OPEN, never as nonexistent. Five values: `open`, `actioned`, `declined`, `superseded`, `parked` — `parked` = decided but blocked on an external precondition, so it leaves the queue, requires `parked_until:`, and never archives |
| Does the target skill have siblings? | Resolve it against `skill-observations/skill-families.md` BEFORE writing; add every sibling the insight applies to to `skill:`, and record the verdict in the mandatory `siblings_checked:` field — including "checked, no propagation" |
| A scan or query came back empty? | Two possibilities, only one is a finding: guard every retrieval meant to prevent duplicate work with an independent existence check, and treat empty output over known content as a broken command |
| Citing an observation number? | From the `id:` frontmatter field (= the `NNNN-` filename prefix); never a `grep -n` line number; sanity-check against the known id range |
| Open-source or internal? | Default open-source; the boundary is confidential |
| Small fix or substantial? | Additive → apply directly; restructuring/new skill → `references/skill-authoring.md` |
| Changing an observation (status/archival)? | Re-read that one file, edit only its frontmatter, or `mv` it to `observation-log/archive/` — no shared-file rewrite |
| Upgrading from a single-file `log.md`? | Scripted, once — `references/migration.md` |
| Weekly review? | Trigger check at session start; procedure in `references/weekly-review.md` |
| No filesystem? | Handoff-doc mode — `references/environments.md` |
---
name: principal-review
description: Performs Shift-Left architectural and task design document reviews (HLD, BDD, Tasks, RFC) against source code before implementation begins.
---

# Principal Review

## Overview

Principal Review provides rigorous, cross-model architectural inspection of High-Level Designs (HLDs), BDD scenarios, Kanban task breakdowns, and standalone RFC documents against the active source codebase.

Operating on the principle of **Shift-Left Quality Assurance**, it catches misunderstandings, missing contracts, scope regressions, and symbol drift before implementation starts, when resolving them in documents is an order of magnitude faster and cheaper than debugging in code.

**Announce at start:** "I'm using the principal-review skill to conduct an architectural review."

## Two Modes of Operation

### 1. In-Lifecycle Mode (Stage 2 Handoff Choice)

Invoked during the packaging phase of `dev-lifecycle` after all epic artefacts pass Gate 2 and mechanical readiness checks.

- **Trigger**: Developer selects option 2 ("Principal Review") at the Handoff Choice prompt.
- **Scope**: Evaluates all epic artefacts in `.devtool/epic/<epic_dir>/`:
  - Architecture spec (`*-design.en.md`, `*-design.vi.md`)
  - Canonical HLD (`<epic_dir>.en.md`, `<epic_dir>.vi.md`)
  - BDD scenarios (`bdd_scenarios.en.md`, `bdd_scenarios.vi.md`)
  - All Kanban tasks (`task_*.md`)
  - Packaging record (`handoff.md`)
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --kind principal --epic-dir <epic_dir> --base <base_branch> --cli <claude|codex|agy>
  ```
- **Persistence**: Results recorded in `.devtool/epic/<epic_dir>/principal_review.md`.

### 2. Ad-Hoc Mode (Standalone Documents)

Invoked on-demand to review standalone design documents, architecture proposals, or RFCs without requiring an epic directory.

- **Trigger**: Developer invokes `/principal-review <path>` (e.g. `/principal-review docs/rfc/payment-service.md`).
- **Scope**: Target markdown document and the active git repository context at `HEAD`.
- **Pre-validation**:
  1. The target file path must exist on disk.
  2. The document must contain structural headings (e.g. `# Title`, `## Overview`).
- **Execution**:
  ```bash
  python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
    --kind principal --doc <path> --base <base_branch> --cli <claude|codex|agy>
  ```
- **Streaming & Visibility**:
  - The review output and triage table stream directly to stdout.
  - Ephemeral review logs are saved under `build/` (git-ignored) for inspection.
  - No epic directory is created or required.

## The Review & Triage Loop

1. **Pre-Check**:
   - For epics, `check_epic_readiness.py` runs first. If any check fails (R1–R8), review halts immediately with a precondition banner without calling external model CLIs.
   - For standalone docs, structural validation checks that the file exists and has valid headings.

2. **External Model Review**:
   - Executes with a read-only permissions profile (`claude -p --permission-mode plan`, `codex exec --sandbox read-only`, or `agy --sandbox --mode plan`).
   - The reviewer inspects active code at candidate SHA to verify groundedness (P1–P8 checklists).

3. **Triage Findings**:
   - Follow [document-triage.md](references/document-triage.md).
   - Verify every finding against the codebase.
   - Present the triage table to the developer and wait for decisions.

4. **Revision Loop & Commit Ordering**:
   - Apply document edits first and commit:
     `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
   - Record decisions with revision commit SHA in `principal_review.md`, then commit:
     `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
   - Re-run packaging to refresh handoff metadata and present the Principal Review Choice again.

## Guidelines & Reference Documents

- [Prompt Template](references/principal-review-prompt.md): The read-only instruction template sent to reviewer CLIs.
- [Review Rules](references/principal-review-rules.md): Severity definitions (Critical, Important, Minor) and source grounding standards.
- [Document Triage Protocol](references/document-triage.md): Step-by-step decision verification and revision loop enforcement.
# Using d3nexus in Codex

The plugin ships the same skills in all runtimes. When a skill uses a Claude Code tool name,
perform the equivalent action using the tools exposed by the current Codex session.

| Skill instruction | Codex action |
|---|---|
| Invoke `Skill` or `d3nexus:<name>` | Select the installed d3nexus skill, then read its `SKILL.md` and follow it. Resolve supporting paths relative to that skill's directory. |
| `Read`, `Grep`, `Glob` | Use file tools or shell reads; prefer `rg` and `rg --files` for searches. |
| `Edit`, `Write` | Use the available patch or file editing tool. |
| `Bash` | Use the session's shell execution tool, respecting its permission boundaries. |
| `TodoWrite` | Use an available plan/task tool, or maintain a short progress checklist if none exists. |
| `Agent`, `Task`, parallel reviewers | Use subagents only when available and authorized. Otherwise perform independent steps sequentially and report the limitation. |

Codex reads the consuming project's `AGENTS.md`. Claude's `@file` import syntax and Antigravity's
Markdown `trigger: always_on` frontmatter are not substitutes for explicit reading instructions.
Read the project's rule files when present; otherwise read the plugin's
[critical rules](../../../rules/CRITICAL_RULES.md) and
[coding guidelines](../../../rules/coding-guidelines.md).

Keep `d3nexus:` cross-references in shared skill text. They identify the owning plugin; they do
not imply that Codex has Claude's slash-command or `Skill` API. Use the skill picker or name the
plugin and skill in a prompt when invocation syntax differs across Codex surfaces.

Follow the current host's instruction hierarchy and honor the user's authorized scope. References
to Antigravity's native planning artifact apply to that environment; do not invent unavailable
tools or configuration in Codex. Platform build tools, credentials, and devices requested by a
skill still need to exist in the consuming project.

After reinstalling or upgrading the plugin, start a new thread to load the updated skill inventory.

exec
/bin/zsh -lc "rg -n 'shared_contracts|shared-contracts|principal' /Users/danhdueexoictif/antigravity_homes/duedd/.codex/memories/MEMORY.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
1:# Task Group: ai-agent-tools setup_shared_contracts principal contract review
6:## Task 1: Review initial setup_shared_contracts architecture, partial
10:- rollout_summaries/2026-10-30T06-59-12-Elg4-principal_review_setup_shared_contracts_contract_drift.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08.jsonl, updated_at=2026-10-29T23:08:05+00:00, thread_id=01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08, `CHANGES REQUIRED`; later review verified these four findings were fixed)
14:- setup_shared_contracts, principal-review, shared_contracts_readme.md.tmpl, string.Template, `{{DOMAIN_NAME}}`, --root, --repo-root, --satellite-root, scripts/verify.sh, Section 11, Section 14, contract drift
16:## Task 2: Re-review setup_shared_contracts after corrections, partial
20:- rollout_summaries/2026-10-30T06-59-12-zvna-principal_review_setup_shared_contracts_contract_contradicti.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa8-72e0-8192-3dd403258730.jsonl, updated_at=2026-10-29T23:26:36+00:00, thread_id=01a18b9a-faa8-72e0-8192-3dd403258730, `CHANGES REQUIRED`; current implementation-blocking finding)
24:- setup_shared_contracts, principal-review, SSC-FR-03, shared-contracts, non-empty, symlink, Rule 7, `Covers:`, traceability, `python3 -m unittest`, CHANGES REQUIRED
28:- When requesting a principal review, the user required a “strictly read-only review” with exact source file/line grounding, artefact-specific actionable findings, and an exact final verdict block -> do not edit files or Git state; cite concrete locations for each source claim. [Task 1][Task 2]
32:- Related skill: skills/principal-contract-review/SKILL.md. [Task 1][Task 2]
35:- For Hub/Satellite shared contracts, Rule 7 makes the Hub physical directory the SSOT; satellites consume it through relative `shared-contracts/` symlinks and treat the linked tree as read-only for Git tracking. [Task 2]
41:- Do not approve implementation because readiness checks pass: compare cross-document semantics and every frozen hard contract. In the current candidate, design spec line 105 and SSC-FR-03 allow an existing physical `shared-contracts/` directory when it is empty, while Task 3 rejects every physical directory. Align the “non-empty” qualifier across design, BDD Given clause, task requirement, Decisions Already Made, and handoff guardrails before implementation; otherwise strict-fidelity execution must Stop-and-Report. [Task 2]

exec
/bin/zsh -lc 'cat rules/CRITICAL_RULES.md rules/coding-guidelines.md; git rev-parse HEAD; git status --short; git ls-tree 6a2e64df2140c316a46ab0c9a584ea3b1b196c7c shared-contracts; ls -ld shared-contracts; rg --files .devtool/epic/sync_shared_contracts' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 5151ms:
---
trigger: always_on
---

# Critical Rules

> [!CRITICAL]
> These rules are MANDATORY and MUST be strictly applied by ALL AI Agent Plugins, runtimes, orchestrators, and subagents (including Claude Code, Antigravity IDE, Cursor, Codex, Windsurf, OpenCode, and any custom/third-party plugins) in every interaction across this project and downstream repositories. Failure to follow these rules is a direct violation of the engineering standard.

## Universal Scope & Plugin Applicability

> [!IMPORTANT]
> **Every AI Agent plugin operating in this environment MUST inherit and execute these rules.**
> Regardless of which plugin, tool, extension, or agent framework initiated the session:
> - Built-in or third-party plugins must NEVER override, circumvent, or weaken these rules.
> - Subagents, background runners, and multi-agent teams spawned by any plugin inherit these exact constraints.
> - If an AI agent or plugin has conflicting built-in behaviors (e.g. auto-pushing, autonomous planning artifacts, skipping human checkpoints), these Critical Rules take absolute precedence.

## 1. Mandatory Quality Gates

> [!IMPORTANT]
> After completing any workflow or skill — regardless of which plugin or tool executed it — you **MUST** run the quality gate for the **kind of work you did**, and fix any issues it raises. This is critical to maintain the quality of the project.
>
> | Kind of work | Gate |
> |---|---|
> | Anything that changes a file shipping in the build | `@quality_check` |
> | Anything whose deliverable is prose | `@doc_quality_check` |
>
> The two share no tier, no audit and no tooling. Running the wrong one produces a green light that means nothing — and `@doc_quality_check` refuses outright if the change touches shipped files.
>
> See: [Quality Check Skill](../skills/quality_check/SKILL.md) · [Document Quality Check Skill](../skills/doc_quality_check/SKILL.md)

## 2. Commit Message Format (Universal Standard)

Every commit — written by a skill, a plugin, an agent, or by hand — uses a bracketed scope, a one-line title, and a bullet list of the subtasks actually done:

```text
[EPIC_NAME] Task title

- subtask title 01
- subtask title 02
```

- **`[SCOPE]`** is the epic name for epic work (`[LOGGING_REFACTOR]`), otherwise the area touched (`[TOOLS]`, `[SETTINGS]`). Uppercase, in brackets, always present.
- **Title** is one line, imperative, no trailing period.
- **Body** lists the subtasks or changes this commit actually contains, one bullet each. Omit the body entirely when the commit does exactly one thing.

Write it with two `-m` flags — the first becomes the title, the second the body:

```bash
git commit -m "[EPIC_NAME] Task title" -m "- subtask title 01
- subtask title 02"
```

> [!CAUTION]
> **Never append trailer lines.** No `Co-Authored-By:`, no `Generated with`, no tool attribution of any kind. The commit ends with the last bullet. This applies universally to all plugins and LLM providers.

## 3. Git Push Operations (No Unauthorized Push)

> [!CRITICAL]
> **NEVER push code to a remote repository (`git push`) without explicit user permission or confirmation.**
> - You may stage (`git add`) and commit (`git commit`) locally following the commit message format when appropriate.
> - Running `git push` (to any remote or branch) is **STRICTLY PROHIBITED** for all agents and plugins unless the user explicitly requests or confirms it in the prompt.
> - Always let the user review local commits or explicitly ask for permission before pushing to remote.

## 4. Native Planning Mode Interception (All Platforms & Plugins)

> [!CRITICAL]
> **Do NOT use native or built-in planning modes (e.g. Antigravity IDE's `<planning_mode>`, Claude Code plan mode, Cursor Composer plans, Windsurf Cascade plans, Codex planners) to create unstructured planning artifacts like `<appDataDir>/brain/.../implementation_plan.md` or loose plan files.**
> When a user request requires planning, design exploration, architectural changes, or epic-level features:
> 1. Because `<user_rules>` has absolute precedence over all instructions across all agent plugins, you **MUST NOT** follow IDE default instructions to create an `implementation_plan.md` artifact.
> 2. For single features or exploratory design, you **MUST** invoke the [Brainstorming Skill](../skills/brainstorming/SKILL.md) (`d3nexus:brainstorming`).
> 3. For multi-step, multi-feature, or epic-level work, you **MUST** invoke the [Epic Lifecycle Skill](../skills/dev-lifecycle/SKILL.md) (`d3nexus:dev-lifecycle`), which orchestrates `dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `quality_check` -> `finishing-a-development-branch`.
> 4. Only use native `implementation_plan.md` if the user explicitly instructs you to bypass d3nexus workflows.

## 5. Mandatory Review Choice Loop in Epic Lifecycle

> [!CRITICAL]
> **NEVER skip or silently bypass the Review Choice after Gate 4 passes in `dev-lifecycle` / `dev-implementation` or any plugin-based orchestrator.**
> When all tasks of an epic are complete, run Phase 4 / Gate 4 first. Only after Gate 4 returns PASS on the current SHA:
> 1. The AI Agent **MUST** explicitly stop calling tools and present the **Review Choice** prompt to the developer:
>    - **Option 1: Finish** — proceed to Developer Kanban Review (Phase 4.1 / Gate 5), then Stage 4.
>    - **Option 2: Cross-model review** — invoke an independent model review using `run_external_review.py run` (prompting the developer to select Claude CLI, Codex CLI, or Antigravity CLI based on `command -v claude codex agy`).
>    - **Option 3: Local model review** — run `ollama list`, ask the developer which model to use (never pick it), then invoke `run_external_review.py run --cli ollama --model <model>`.
> 2. The AI Agent **MUST NOT** auto-select an option or assume "Finish" by default.
> 3. **Cross-model review must return to a full Gate 4 run** after the round is recorded and all blocking findings have decisions and required Fix commits. Gate 4 PASS then presents Review Choice again. This loop repeats until the developer explicitly chooses Finish. Local model review follows the same loop. Before any Fix commit or decision, the agent presents the triage from `run_external_review.py triage` and waits for the developer's decisions. After fixes are applied, the agent must halt for developer self-review and confirmation before any further action.
> 4. A previous Gate 4 PASS cannot be reused after `review_results.md`, a finding decision, or a Fix commit changes the candidate SHA.

## 6. Prohibited Autonomous Reviews & Mandatory Human Self-Review Checkpoint

> [!CRITICAL]
> **NEVER autonomously trigger Principal Review or Cross-Model / Local Model Review, and NEVER enter autonomous or infinite re-review loops after fixing findings.**
> Every review invocation and every cycle after fixing findings requires explicit developer confirmation and human checkpointing:
>
> 1. **No Autonomous Review Triggering**:
>    - The AI Agent is **STRICTLY PROHIBITED** from autonomously triggering Principal Review (`d3nexus:principal-review`) or Cross-Model / Local Model Review (`d3nexus:cross-model-review`).
>    - External review tools (`run_external_review.py run`, `claude`, `codex`, `agy`, `ollama`) must **ONLY** be invoked when explicitly chosen, requested, or confirmed by the developer (e.g. at Gate 2 Principal Review checkpoint or Gate 4 Review Choice). The agent must never initiate external AI review on its own initiative.
> 2. **Mandatory Human Checkpoint After Fixing Review Findings**:
>    - After addressing or fixing findings from **any** review (Principal Review in Stage 2, or Cross-Model / Local Model Review in Stage 3):
>    - The AI Agent **MUST IMMEDIATELY STOP CALLING TOOLS**.
>    - The AI Agent is **STRICTLY PROHIBITED** from automatically re-triggering another review round with Cross AI Agents or external models (no autonomous chaining: Review -> Fix -> Auto Re-review -> Auto Fix).
>    - The AI Agent **MUST** present the fixes, file diffs, and updated triage/finding decisions to the developer for **Human Self-Review**.
>    - The AI Agent **MUST wait for explicit developer confirmation** before proceeding with any subsequent action (such as re-running quality gates, re-packaging, invoking another review round, or advancing to the next stage).

## 7. Multi-Repo Boundaries, Symlink Isolation & Contract Governance

> [!CRITICAL]
> **AI Agents MUST strictly respect repository boundaries, symbolic link isolation, and contract-first governance across multi-repo ecosystems (Hub and Satellite repositories).**
>
> 1. **Multi-Repo Git Boundary Isolation**:
>    - An AI Agent running in any repository MUST NOT stage (`git add`) or commit (`git commit`) files residing outside the current git working tree.
>    - In a Satellite repository where `shared-contracts/` is a symbolic link pointing to a Hub repository (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`):
>      - Agents MUST treat `shared-contracts/` as **strictly read-only** for git tracking within the satellite workspace.
>      - Agents **MUST NOT** include `shared-contracts/...` in `Files Allowed` for local git tasks (preventing `fatal: pathspec is beyond a symbolic link`).
>      - Agents **MUST NOT** autonomously execute git commit commands in adjacent repositories (e.g. `git -C <target_repo>`) without explicit developer confirmation.
>
> 2. **Contract-First Triad & Canonical SSOT**:
>    - The Hub repository containing the physical `shared-contracts/` directory is the sole canonical authority (Single Source of Truth) for contract commits.
>    - Before modifying endpoints, database models, worker bridges, offline sync logic, or DTOs, agents MUST inspect the 3 canonical contract files in the relevant domain folder (`shared-contracts/<domain>/`):
>      1. `api_contract.md`: Endpoints, wire format, headers, telemetry, and payload schemas.
>      2. `architecture_and_flow.md`: Pipeline states, state machines, lifecycle fencing, and failure handling.
>      3. `gaps_and_rfcs.md`: Asynchronous change proposals, gap ledger, and cross-repo alignments.
>
> 3. **No Unilateral Breaking Changes & Non-Breaking Schema Guarantee**:
>    - Never rename API fields, mutate JSON request/response structures, or alter pipeline state enums in backend or client implementations without prior documentation and alignment in `shared-contracts/`.
>    - All schema and payload modifications MUST guarantee backward compatibility across all consumers (optional fields with safe defaults, non-breaking enum additions). Breaking changes without backward-compatible transition windows or fallback shims are strictly forbidden.
>
> 4. **Asynchronous RFC Workflow (Gaps & RFCs Ledger)**:
>    - If an agent in a satellite repo detects a payload mismatch, missing field, or new requirement, it **MUST NOT** invent ad-hoc fields or silently diverge.
>    - The agent MUST log a formal `GAP-XX` or `RFC-XXX` entry in `gaps_and_rfcs.md` (or emit an Upstream Contract Handoff Summary via `d3nexus:dev-designer`) and wait for upstream alignment before implementing breaking changes.
>
> 5. **Stateless Compute & Architectural Isolation**:
>    - Satellite worker nodes (e.g. `lyrics-sync`) must act strictly as stateless compute nodes. Direct connection to the control plane database (`DATABASE_URL`, PostgreSQL/SQLite) is **STRICTLY FORBIDDEN**. All state transitions, lease acquisitions, and result deliveries occur strictly via documented HTTP REST/SSE endpoints using worker authentication tokens.
---
trigger: always_on
---

# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

> **TL;DR — 4 rules to always follow:**
> 1. **Think first** — State assumptions, ask when unclear, present tradeoffs before acting.
> 2. **Simplicity** — Minimum code that solves the problem. If it could be 50 lines, don't write 200.
> 3. **Surgical** — Touch only what the request requires. Don't improve adjacent code.
> 4. **Verify** — Define success criteria upfront. Don't claim done without running the check.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-rEHHGIVZ' (errno=Operation not permitted)
2026-10-30 19:11:23.897 xcodebuild[12085:4198333]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:24.056 xcodebuild[12085:4198332] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-EK89PIMy' (errno=Operation not permitted)
2026-10-30 19:11:24.538 xcodebuild[12087:4198343]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:24.655 xcodebuild[12087:4198342] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
6a2e64df2140c316a46ab0c9a584ea3b1b196c7c
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-C0Qp5TL9' (errno=Operation not permitted)
2026-10-30 19:11:25.690 xcodebuild[12104:4198384]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:25.808 xcodebuild[12104:4198383] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-N9RhnNcz' (errno=Operation not permitted)
2026-10-30 19:11:26.256 xcodebuild[12107:4198398]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:26.379 xcodebuild[12107:4198396] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-ID9W6ibM' (errno=Operation not permitted)
2026-10-30 19:11:27.411 xcodebuild[12112:4198425]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:27.536 xcodebuild[12112:4198424] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Gl8NmFm9' (errno=Operation not permitted)
2026-10-30 19:11:27.987 xcodebuild[12114:4198440]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-30 19:11:28.106 xcodebuild[12114:4198438] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
ls: shared-contracts: No such file or directory
.devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md
.devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md
.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md
.devtool/epic/sync_shared_contracts/bdd_scenarios.en.md
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md
.devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md
.devtool/epic/sync_shared_contracts/sync_shared_contracts.vi.md
.devtool/epic/sync_shared_contracts/task_2_heuristic_scanner_and_check_engine.md
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.vi.md
.devtool/epic/sync_shared_contracts/handoff.md

exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md .devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Sync Shared Contracts Design

- **Date**: 2026-10-30
- **Status**: Approved
- **Scope**: New skill `skills/sync-shared-contracts/`, CLI engine `sync_contracts.py`, canonical delta brief template, hermetic test suite `test_sync_contracts.py`, integration with `scripts/verify.sh`
- **Next step**: `d3nexus:dev-designer` (Stage 2 — High-Level Design, BDD Scenarios, and Kanban Breakdown)

## Table of Contents

- [1. Background and Motivation](#1-background-and-motivation)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Architecture and Dual-Mode Detection](#3-architecture-and-dual-mode-detection)
- [4. Directory Structure and Sync Watermark Schema](#4-directory-structure-and-sync-watermark-schema)
- [5. CLI Engine Specifications](#5-cli-engine-specifications)
- [6. Target Codebase Heuristic Scanner](#6-target-codebase-heuristic-scanner)
- [7. Orchestrated Lifecycle Bridge](#7-orchestrated-lifecycle-bridge)
- [8. Verification and Test Strategy](#8-verification-and-test-strategy)
- [9. Error Handling and Edge Cases](#9-error-handling-and-edge-cases)
- [10. Risks and Mitigations](#10-risks-and-mitigations)

## 1. Background and Motivation

With the introduction of `setup-shared-contracts`, multi-repository ecosystems (such as the control plane `D3Nexus` paired with worker satellites like `lyrics-sync` and mobile clients like `nexus`) have a standardized way to initialize physical `shared-contracts/` directories, relative symbolic links, and governance rules.

However, after initial setup (Day-0), teams face continuous synchronization challenges (Day-2 operations):
- When the Hub repository updates `api_contract.md` or `architecture_and_flow.md` (or approves an RFC in `gaps_and_rfcs.md`), satellite repositories lack an automated tool to detect what changed since their last implementation cycle.
- When a satellite repository logs a new `Draft` or `In Review` proposal in `gaps_and_rfcs.md`, the Hub repository needs a deterministic check to discover actionable RFCs and incorporate them into backend implementation plans.
- Transitioning from detected contract deltas into `d3nexus:dev-lifecycle` (Spec -> HLD & BDD -> Worktree TDD Implementation -> Branch Finishing) currently requires manual inspection and copy-pasting of endpoints, schemas, and governance constraints.

To bridge contract changes directly into target repository execution, we are introducing the `sync-shared-contracts` skill and its companion CLI engine `sync_contracts.py`.

## 2. Goals and Non-Goals

### Goals
- Provide a zero-dependency standard-library Python CLI (`sync_contracts.py`) supporting `check`, `brief`, and `ack` subcommands.
- Implement a **3-Layer Hybrid Delta Engine**:
  1. **Git & SHA-256 Watermark Diff**: Compare Hub git history and canonical file hashes against `.agents/contract_sync.json`.
  2. **Structured Markdown Contract Parser**: Parse endpoints, headers, JSON payload keys, pipeline steps, and active RFC tables from the 3 canonical contract files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
  3. **Target Codebase Heuristic Scanner**: Scan target repository source files to classify contract endpoints, headers, and payload keys as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
- Support **Dual-Mode Execution** (auto-detecting Satellite symlink mode vs Hub physical directory mode).
- Generate a structured **Contract Requirements Brief** (`brief`) that feeds directly into `d3nexus:dev-lifecycle` across all 4 stages (`dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `finishing-a-development-branch`).
- Provide an atomic watermark update command (`ack`) that records the synced contract version, Hub commit SHA, file hashes, and acknowledged RFCs/endpoints in `.agents/contract_sync.json`.

### Non-Goals
- Modifying or replacing `setup-shared-contracts` topology initialization (`init-hub`, `link-satellite`).
- Autonomously committing across git symlink boundaries in violation of Rule 7 of `CRITICAL_RULES.md`.
- Pushing git commits to remote repositories without explicit user confirmation (prohibited by Rule 3).

## 3. Architecture and Dual-Mode Detection

The skill operates across both sides of the Star Topology by inspecting `<repo_root>/shared-contracts`:

1. **Satellite Mode (`shared-contracts` is a relative symbolic link)**:
   - Resolves the symlink target to identify the `<domain>` folder and parent `<hub_root>`.
   - Detects upstream changes made in the Hub repository (new endpoints, updated payload fields, pipeline rules, and `Approved` RFCs) that need to be implemented in the satellite consumer/worker codebase.
   - Enforces the strict Git read-only symlink boundary (never staging `shared-contracts/` inside the satellite repository; tracking sync state exclusively in `.agents/contract_sync.json`).
2. **Hub Mode (`shared-contracts/` is a physical directory)**:
   - Iterates over domain subdirectories `shared-contracts/<domain>/` (or targets a specific `--domain`).
   - Detects `Draft`, `In Review`, or `Approved` RFCs and gaps proposed by satellites in `gaps_and_rfcs.md`, as well as contract changes not yet reflected in the Hub backend source code or `.agents/contract_sync.json`.
   - Enforces the `task_01` Contract-First synchronization rule during `dev-designer` task breakdown.

```mermaid
flowchart TD
    subgraph TARGET ["Target Repository (Satellite or Hub)"]
        CLI["sync_contracts.py<br/>(check / brief / ack)"]
        STATE[".agents/contract_sync.json<br/>(Sync Watermark State)"]
        SRC["Target Source Code<br/>(Heuristic Endpoint & Field Scan)"]
    end

    subgraph CONTRACT ["Shared Contracts (Physical or via Symlink)"]
        API["api_contract.md"]
        ARCH["architecture_and_flow.md"]
        RFC["gaps_and_rfcs.md"]
        GIT["Hub Git History (git log / diff)"]
    end

    subgraph LIFECYCLE ["Orchestrated /dev-lifecycle"]
        S1["Stage 1: dev-brainstorming<br/>(Bilingual Design Spec)"]
        S2["Stage 2: dev-designer<br/>(HLD + BDD + Kanban Tasks)"]
        S3["Stage 3: dev-implementation<br/>(Worktree TDD + sync_contracts.py ack)"]
        S4["Stage 4: finishing-a-development-branch"]
    end

    CLI -->|"1. Read previous watermark"| STATE
    CLI -->|"2. Git diff + Parse Markdown"| CONTRACT
    CLI -->|"3. Scan Endpoint/DTO tokens"| SRC
    CLI -->|"4. Emit Contract Delta Brief"| S1
    S1 --> S2 --> S3 --> S4
    S3 -->|"5. Update sync watermark"| STATE
```

## 4. Directory Structure and Sync Watermark Schema

### 4.1 Skill Directory Structure

```text
skills/sync-shared-contracts/
├── SKILL.md
└── resources/
    ├── scripts/
    │   ├── sync_contracts.py
    │   └── test_sync_contracts.py
    └── templates/
        └── contract_delta_brief.md.tmpl
```

### 4.2 Sync Watermark Schema (`.agents/contract_sync.json`)

The watermark file is stored inside the target repository at `.agents/contract_sync.json`:

```json
{
  "schema_version": 1,
  "mode": "satellite",
  "domains": {
    "lyrics-sync": {
      "hub_commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      "contract_version": "1.1.0",
      "last_synced_at": "2026-10-30T18:30:00Z",
      "file_hashes": {
        "api_contract.md": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "architecture_and_flow.md": "sha256:...",
        "gaps_and_rfcs.md": "sha256:..."
      },
      "acknowledged_rfcs": ["RFC-001", "RFC-002"],
      "acknowledged_endpoints": [
        "POST /api/v1/lyrics-sync/tasks/claim",
        "POST /api/v1/lyrics-sync/tasks/{id}/progress",
        "POST /api/v1/lyrics-sync/tasks/{id}/complete",
        "GET /api/v1/lyrics-sync/status"
      ]
    }
  }
}
```

## 5. CLI Engine Specifications

The script `sync_contracts.py` provides three subcommands:

### 5.1 Command: `check`
```bash
python3 sync_contracts.py check [--repo-root <path>] [--domain <domain_name>] [--json] [--strict]
```
- **Validation**:
  - Verifies `shared-contracts` exists and resolves cleanly (no dangling symlinks, all 3 canonical files present).
- **Actions**:
  1. Loads `.agents/contract_sync.json` if present; otherwise marks the domain status as `INITIAL_SYNC`.
  2. Computes current `sha256` hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, and queries the latest git commit SHA affecting the domain folder in the Hub repository (falling back gracefully if git history is unavailable).
  3. Parses the 3 canonical Markdown files to extract version metadata, required headers, endpoints matrix rows, JSON schema keys, pipeline steps, and RFC ledger entries.
  4. Runs the Target Codebase Heuristic Scanner across `<repo_root>` to check whether extracted endpoints, headers, and payload keys appear in source code.
  5. Determines overall sync status: `IN_SYNC`, `INITIAL_SYNC`, or `DRIFT_DETECTED`.
- **Exit Codes**:
  - `0` when `IN_SYNC` (or when `DRIFT_DETECTED` / `INITIAL_SYNC` without `--strict`).
  - `1` when topology/symlink errors occur, or when `--strict` is passed and status is not `IN_SYNC`.

### 5.2 Command: `brief`
```bash
python3 sync_contracts.py brief [--repo-root <path>] [--domain <domain_name>] [--output <path>]
```
- **Actions**:
  - Executes the full 3-layer delta analysis from `check`.
  - Renders `contract_delta_brief.md.tmpl` into a structured Markdown report containing:
    1. **Topology & Sync Metadata**: Mode (`hub` / `satellite`), Domain, Version transition (`previous -> current`), Hub commit range, and Changed files list.
    2. **API & Schema Requirements**: Endpoints and JSON payload fields added or modified, annotated with heuristic scan status (`FOUND_IN_CODE` vs `MISSING_IN_CODE`).
    3. **Architecture & Pipeline Invariants**: Canonical pipeline steps, state machine transitions, and cancellation/isolation constraints.
    4. **Actionable RFCs & Gaps**: Pending or newly approved entries from `gaps_and_rfcs.md` requiring action in the current repository mode.
    5. **Lifecycle Execution Rules**: Mandatory instructions for `dev-brainstorming`, `dev-designer` (`task_01` rule and symlink boundary rules), and `dev-implementation` (`sync_contracts.py ack` verification step).

### 5.3 Command: `ack`
```bash
python3 sync_contracts.py ack [--repo-root <path>] [--domain <domain_name>] [--rfc <RFC-ID> ...]
```
- **Actions**:
  - Computes the current file hashes, contract version, Hub git commit SHA, endpoints list, and RFC IDs (all `Approved` / `Implemented` RFCs plus any explicitly passed via `--rfc`).
  - Writes or updates `.agents/contract_sync.json` atomically using a temporary file and `os.replace()`.

## 6. Target Codebase Heuristic Scanner

To provide immediate visibility into whether contract items are already implemented in the target repository (especially during `INITIAL_SYNC` or partial implementations):
- **Scanned Directories**: Walks `<repo_root>` recursively while excluding `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
- **Supported Source Extensions**: `.py`, `.rs`, `.dart`, `.kt`, `.kts`, `.swift`, `.ts`, `.tsx`, `.js`, `.go`, `.java`, `.yaml`, `.yml`, `.json`.
- **Token Normalization**:
  - For endpoints like `/api/v1/lyrics-sync/tasks/{id}/progress`, extracts static path segments (e.g., `/api/v1/lyrics-sync/tasks` and `/progress` or `tasks/claim`) and checks whether those route fragments exist in source files.
  - For headers (`X-Worker-Token`, `X-Correlation-ID`) and top-level JSON schema keys (`task_id`, `lease_duration_ms`, `output_data`), checks identifier presence (both `snake_case` and `camelCase` equivalents for mobile/frontend clients like Dart/Swift/TypeScript).

## 7. Orchestrated Lifecycle Bridge

When a developer invokes `/sync-shared-contracts` (or asks to check contract changes and execute on a target repo), the skill orchestrates the following 5-step workflow:

1. **Step 1 — Contract Audit & Brief Generation**:
   - Run `sync_contracts.py check` and `sync_contracts.py brief`.
   - If `shared-contracts` is missing or broken, direct the user to `d3nexus:setup-shared-contracts`.
   - If `IN_SYNC` and no `MISSING_IN_CODE` items or pending RFCs exist, report that the repository is fully synchronized and stop.
2. **Step 2 — Scope Confirmation**:
   - Present the generated **Contract Requirements Brief** to the developer and confirm which deltas/RFCs to target and the `<epic_slug>`.
3. **Step 3 — Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`)**:
   - Enter `d3nexus:dev-lifecycle` using the confirmed Contract Requirements Brief as grounding context:
     - **Stage 1 (`dev-brainstorming`)**: Produce the bilingual spec pair (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.en.md` and `.vi.md`) anchored on the contract delta without re-asking questions already settled by the contract, then obtain Gate 1 approval.
     - **Stage 2 (`dev-designer`)**: Generate the bilingual HLD, 5-dimension BDD scenarios (`bdd_scenarios.en.md` / `.vi.md`), and Kanban task breakdown (`task_*.md`) for Gate 2:
       - In **Hub Mode**: `task_01` updates the physical `shared-contracts/<domain>/` files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
       - In **Satellite Mode**: `task_01` updates internal consumer DTOs, API clients, and mock fixtures (never including `shared-contracts/` in `Files Allowed`).
       - In **Both Modes**: The final task (or `task_01` verification hook) includes `.agents/contract_sync.json` in `Files Allowed` and runs `sync_contracts.py ack` + `sync_contracts.py check --strict` so the sync watermark is committed alongside the implementation.
4. **Step 4 — Stage 3 (`dev-implementation`)**:
   - Execute tasks in an isolated worktree via TDD, verify `sync_contracts.py check --strict` passes, run Gate 4 (`quality_check` + `check_bdd_traceability.py` + `audit_epic.py`), and pass the Review Choice loop and Gate 5.
5. **Step 5 — Stage 4 (`finishing-a-development-branch`)**:
   - Rebase, verify, merge `--no-ff`, and archive epic artifacts into `.devtool/epic/<epic_slug>/`.

## 8. Verification and Test Strategy

The hermetic test suite in `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` uses Python's standard `unittest` framework and `tempfile.TemporaryDirectory`:
- **Test Initial Sync & Dual-Mode Detection**: Verifies `check` accurately detects Hub physical mode and Satellite symlink mode on fresh repositories without `.agents/contract_sync.json`.
- **Test Markdown Contract Parser**: Verifies extraction of `Version`, headers, `Endpoints Matrix` rows, JSON schema keys, pipeline steps, and `Active RFC Ledger` statuses.
- **Test Target Codebase Heuristic Scanner**: Verifies detection of implemented vs missing endpoints and `snake_case` / `camelCase` DTO fields across mock source files.
- **Test Watermark Ack & Incremental Drift**: Verifies that running `ack` transitions `check --strict` to exit `0` (`IN_SYNC`), and subsequent edits to `api_contract.md` or `gaps_and_rfcs.md` in the Hub trigger `DRIFT_DETECTED` (exit `1` under `--strict`) with accurate git commit log and file hash deltas.
- **Test Brief Rendering & Error Handling**: Verifies `brief` output structure and graceful error codes for missing or dangling `shared-contracts` links.
- **Harness Integration**: Registered in `scripts/verify.sh` alongside `test_setup_contracts.py`.

## 9. Error Handling and Edge Cases

| Scenario | Handled By | Behavior |
|---|---|---|
| `shared-contracts` does not exist | `check` / `brief` / `ack` | Exits `1` with remediation prompt pointing to `setup_contracts.py`. |
| Satellite `shared-contracts` is a dangling symlink | `check` / `brief` / `ack` | Detects broken target, exits `1` with instructions to re-run `link-satellite --force`. |
| `.agents/contract_sync.json` does not exist yet | `check` / `brief` | Reports status `INITIAL_SYNC`, parses full contract baseline, and classifies items via codebase heuristic scan. |
| `.agents/contract_sync.json` contains malformed JSON | `check` / `ack` | Logs warning, treats state as unsynced during `check`, and overwrites cleanly on `ack`. |
| Hub directory is not a Git repository | `check` / `brief` / `ack` | Skips `git log` / `git rev-parse` gracefully and relies on `sha256` file hashes and `Version` metadata. |

## 10. Risks and Mitigations

- **Risk: False negatives in Heuristic Codebase Scanner when target repos use camelCase or segmented route constants.**
  *Mitigation*: The scanner checks normalized route suffixes (stripping `{param}` placeholders) and checks both `snake_case` and `camelCase` field tokens, while treating heuristic results as advisory indicators alongside the authoritative `.agents/contract_sync.json` watermark.
- **Risk: Satellite agents accidentally staging `shared-contracts/` when updating sync state.**
  *Mitigation*: Sync state is stored strictly inside `<repo_root>/.agents/contract_sync.json`, completely outside the `shared-contracts` symlink, and `brief` explicitly injects the `Files Allowed` prohibition reminder for `dev-designer`.

# Sync Shared Contracts High-Level Design

## Table of Contents

- [Meta Data](#meta-data)
- [Background](#background)
- [Goals and Non-Goals](#goals-and-non-goals)
- [Architecture and Technical Design](#architecture-and-technical-design)
- [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
- [Verification Environment](#verification-environment)
- [Shared Contract Impact](#shared-contract-impact)
- [Comprehensive BDD Scenario Coverage](#comprehensive-bdd-scenario-coverage)
- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)

## Meta Data

- **Epic name**: `sync_shared_contracts`
- **Status**: Packaged
- **Target release**: Next plugin release (1.16.0)
- **Platform**: Python tooling / agent skill kit
- **Source Spec**: [Approved Sync Shared Contracts design](2026-10-30-sync-shared-contracts-design.en.md)

## Background

While `setup-shared-contracts` automates Day-0 topology initialization (creating physical `shared-contracts/` in the Hub repository and relative mode `120000` symbolic links in Satellite repositories), engineering teams and AI agents require a deterministic Day-2 workflow to continuously detect contract changes, audit actionable RFCs, check target codebase readiness, and drive implementation through `d3nexus:dev-lifecycle`.

Without an automated synchronization engine:
1. Satellite repositories cannot easily tell which endpoints, payload fields, or pipeline rules changed in the Hub since their last implementation cycle.
2. Hub repositories lack an automated scanner to surface newly proposed `Draft` or `In Review` RFCs logged by satellites in `gaps_and_rfcs.md`.
3. Translating contract deltas into `dev-brainstorming` specs, `dev-designer` HLDs/tasks, and `dev-implementation` verification gates requires error-prone manual inspection.

This epic delivers the `sync-shared-contracts` skill and its standard-library Python CLI engine `sync_contracts.py` (`check`, `brief`, `ack`) to automate contract delta detection and orchestrate target repository execution via `d3nexus:dev-lifecycle`.

## Goals and Non-Goals

### Goals

- Build `skills/sync-shared-contracts/SKILL.md` to orchestrate contract delta auditing and the 4-stage `d3nexus:dev-lifecycle` bridge on target repositories.
- Build `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` implementing `check`, `brief`, and `ack` using Python's standard library.
- Implement a 3-layer Hybrid Delta Engine:
  1. Git commit history and SHA-256 file hash comparison against `.agents/contract_sync.json`.
  2. Structured Markdown parsing of `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`.
  3. Target Codebase Heuristic Scanner classifying endpoints, headers, and DTO fields (`snake_case` and `camelCase`) as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
- Bundle `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` to render actionable **Contract Requirements Briefs**.
- Implement hermetic unit and integration tests in `test_sync_contracts.py` and register them in `scripts/verify.sh`.

### Non-Goals

- Replacing `setup-shared-contracts` (`init-hub`, `link-satellite`).
- Autonomously staging or committing files across symbolic link boundaries.
- Pushing git commits to remote repositories without explicit user approval.

## Architecture and Technical Design

### High-Level Architecture

```mermaid
flowchart TD
    subgraph TARGET ["Target Repository (Satellite or Hub)"]
        CLI["sync_contracts.py<br/>(check / brief / ack)"]
        STATE[".agents/contract_sync.json<br/>(Watermark State)"]
        SCAN["Heuristic Codebase Scanner<br/>(Routes, Headers, DTO Keys)"]
    end

    subgraph CONTRACT ["Shared Contracts (Physical or Relative Symlink)"]
        C_API["api_contract.md"]
        C_ARCH["architecture_and_flow.md"]
        C_RFC["gaps_and_rfcs.md"]
        H_GIT["Hub Git Log & Diff"]
    end

    subgraph LIFECYCLE ["Orchestrated d3nexus:dev-lifecycle"]
        L_S1["Stage 1: dev-brainstorming<br/>(Gate 1 Bilingual Spec)"]
        L_S2["Stage 2: dev-designer<br/>(Gate 2 HLD, BDD & Tasks)"]
        L_S3["Stage 3: dev-implementation<br/>(Worktree TDD + ack + Gate 4/5)"]
        L_S4["Stage 4: finishing-a-development-branch"]
    end

    CLI -->|"Read/Write Watermark"| STATE
    CLI -->|"Parse & Hash"| C_API
    CLI -->|"Parse & Hash"| C_ARCH
    CLI -->|"Parse & Hash"| C_RFC
    CLI -->|"Query Commit Delta"| H_GIT
    CLI -->|"Classify Tokens"| SCAN
    CLI -->|"Render Brief"| L_S1
    L_S1 --> L_S2 --> L_S3 --> L_S4
```

### Use Cases

```mermaid
flowchart LR
    DEV["Developer / AI Agent"]
    UC1["Run sync_contracts.py check<br/>(Detect Drift & Code Coverage)"]
    UC2["Run sync_contracts.py brief<br/>(Generate Requirements Brief)"]
    UC3["Execute /dev-lifecycle on Target Repo<br/>(Spec -> HLD -> TDD -> Finish)"]
    UC4["Run sync_contracts.py ack<br/>(Record Watermark in .agents/contract_sync.json)"]

    DEV --> UC1
    DEV --> UC2
    UC2 --> UC3
    UC3 --> UC4
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant Dev as Developer / Agent
    participant CLI as sync_contracts.py
    participant Hub as Shared Contracts (Hub / Symlink)
    participant Code as Target Repo Source & .agents/
    participant Life as d3nexus:dev-lifecycle

    Dev->>CLI: check / brief [--domain <name>]
    CLI->>Hub: Verify topology & compute SHA-256 + git log
    CLI->>Hub: Parse api_contract, architecture_and_flow, gaps_and_rfcs
    CLI->>Code: Read .agents/contract_sync.json & scan source tokens
    CLI-->>Dev: Emit Contract Requirements Brief (INITIAL_SYNC / DRIFT_DETECTED)
    Dev->>Life: Stage 1 (dev-brainstorming) -> Approve Gate 1 Spec
    Life->>Life: Stage 2 (dev-designer) -> Approve Gate 2 HLD & Tasks
    Life->>CLI: Stage 3 final task runs sync_contracts.py ack
    CLI->>Code: Atomically write .agents/contract_sync.json
    Life->>CLI: Verify sync_contracts.py check --strict exits 0
    Life-->>Dev: Pass Gate 4 & Gate 5 -> Stage 4 Finish Branch
```

## Integration Test Plan and Boundary Matrix

Integration test roots: skills/sync-shared-contracts/resources/scripts/, scripts/

Protected paths: .agents/quality/**, .devtool/epic/sync_shared_contracts/bdd_scenarios.en.md, .devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md, scripts/verify.sh

Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/sync-shared-contracts.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -> build/test-results/sync-shared-contracts.xml

| Component | Test File | Test Case | Target Boundary |
|---|---|---|---|
| Markdown Parser & Template | `test_sync_contracts.py` | `test_syc_hp_01_parse_and_render_brief` | Parses 3 canonical files and renders `contract_delta_brief.md.tmpl` |
| Dual-Mode & Watermark Check | `test_sync_contracts.py` | `test_syc_hp_02_satellite_and_hub_check` | Detects `INITIAL_SYNC`, `DRIFT_DETECTED`, and `IN_SYNC` across Hub and Satellite |
| Heuristic Codebase Scanner | `test_sync_contracts.py` | `test_syc_ec_02_heuristic_snake_and_camel_scan` | Matches static route prefixes, headers, and `snake_case`/`camelCase` keys |
| Watermark Ack & Strict Gate | `test_sync_contracts.py` | `test_syc_st_01_ack_and_incremental_drift` | Writes `.agents/contract_sync.json` atomically and verifies `--strict` exit codes |
| Skill & Harness Verification | `test_sync_contracts.py` | `test_syc_hp_03_skill_and_verify_harness` | Validates `SKILL.md` frontmatter, links, and `scripts/verify.sh` integration |

## Verification Environment

- **Runtime**: Python 3.10+ (Standard Library only: `pathlib`, `os`, `sys`, `json`, `hashlib`, `re`, `subprocess`, `argparse`, `unittest`, `tempfile`).
- **Isolation**: All tests execute inside isolated `tempfile.TemporaryDirectory()` workspaces with zero network access or live external repositories.
- **Environment Variables (`Needs`)**: None (`—`).
- **Test Command**: `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`
- **Release Gate**: `scripts/verify.sh` executes the test suite on every release verification run.

## Shared Contract Impact

`None — self-contained developer tooling skill (audits and synchronizes shared contracts for target repositories)`.

## Comprehensive BDD Scenario Coverage

Full Gherkin scenarios covering all 5 dimensions live in `bdd_scenarios.en.md` and `bdd_scenarios.vi.md`.

- **Happy Paths**:
  - `[SYC-HP-01]`: Structured parsing of the 3 canonical contract files and rendering of the Contract Requirements Brief.
  - `[SYC-HP-02]`: End-to-end Satellite and Hub drift detection, acknowledgement (`ack`), and `--strict` verification pass.
  - `[SYC-HP-03]`: Skill definition validation and `scripts/verify.sh` harness execution.
- **Edge Cases & Boundaries**:
  - `[SYC-EC-01]`: Initial sync (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet.
  - `[SYC-EC-02]`: Heuristic codebase scanner matching parameterized routes (`/tasks/{id}/progress`) and `camelCase` DTO properties (`leaseDurationMs`).
  - `[SYC-EC-03]`: Graceful fallback when the Hub directory is not a Git repository (no `.git` folder).
- **State Transitions**:
  - `[SYC-ST-01]`: Transitioning from `INITIAL_SYNC` to `IN_SYNC` via `ack`, then to `DRIFT_DETECTED` when `api_contract.md` or `gaps_and_rfcs.md` is updated in the Hub.
  - `[SYC-ST-02]`: Recording newly acknowledged RFC IDs via `ack --rfc RFC-002` while preserving other domain entries in `.agents/contract_sync.json`.
- **Async & Concurrency**:
  - `[SYC-AR-01]`: Atomic watermark file updates via temporary swap file (`os.replace`) leaving zero partial JSON files.
  - `[SYC-AR-02]`: Circular symbolic link protection when resolving `shared-contracts` targets.
- **Failures & Resilience**:
  - `[SYC-FR-01]`: Refusing execution with exit code `1` when `shared-contracts` is missing.
  - `[SYC-FR-02]`: Refusing execution with exit code `1` when `shared-contracts` is a dangling symlink or missing canonical files.
  - `[SYC-FR-03]`: Recovering gracefully from a corrupted `.agents/contract_sync.json` file during `check` and overwriting cleanly on `ack`.

## Rollout Strategy and Mitigation

- **Deployment**: Shipped as a core skill in `skills/sync-shared-contracts/` within the `d3nexus` plugin.
- **Phased Rollout**:
  1. Unit and integration verification in `ai-agent-tools` via `scripts/verify.sh`.
  2. Pilot usage across `D3Nexus` (Hub) and `lyrics-sync` / `nexus` (Satellites).
  3. Bundled in plugin release 1.16.0.
- **Rollback**: Removing `skills/sync-shared-contracts/` and reverting `scripts/verify.sh` cleanly restores the prior state.

## Kanban Tasks Breakdown

- [Task 1: Canonical Brief Template and Markdown Contract Parser](task_1_brief_template_and_contract_parser.md) — Covers: `[SYC-HP-01]`, `[SYC-EC-01]`
- [Task 2: Target Codebase Heuristic Scanner and Dual-Mode Check Engine](task_2_heuristic_scanner_and_check_engine.md) — Covers: `[SYC-EC-02]`, `[SYC-EC-03]`, `[SYC-AR-02]`, `[SYC-FR-01]`, `[SYC-FR-02]`
- [Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands](task_3_watermark_ack_and_brief_cli.md) — Covers: `[SYC-HP-02]`, `[SYC-ST-01]`, `[SYC-ST-02]`, `[SYC-AR-01]`, `[SYC-FR-03]`
- [Task 4: Skill Definition, Lifecycle Bridge Instructions, and Verify Harness Integration](task_4_skill_definition_and_verify_integration.md) — Covers: `[SYC-HP-03]`

exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md .devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md .devtool/epic/sync_shared_contracts/handoff.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md .devtool/epic/sync_shared_contracts/task_2_heuristic_scanner_and_check_engine.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
---
id: "task_3_watermark_ack_and_brief_cli"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "watermark", "cli"]
order: "a3"
---

# Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Implement the `ack` subcommand, incremental drift detection (`IN_SYNC` vs `DRIFT_DETECTED`), multi-domain watermark preservation, atomic JSON writing, and corrupted watermark recovery in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Watermark Ack Command (`[SYC-HP-02]`, `[SYC-ST-02]`, `[SYC-AR-01]`)**:
   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, query the Hub git commit SHA, and collect acknowledged endpoints and RFC IDs (including `--rfc <RFC-ID>` arguments).
   - Write `.agents/contract_sync.json` atomically using a temporary file in `.agents/` and `os.replace()`, preserving existing entries for other domains (`[SYC-ST-02]`, `[SYC-AR-01]`).
2. **Incremental Drift Detection (`[SYC-ST-01]`)**:
   - After `ack` is run, `check --strict` must report `IN_SYNC` and exit `0` (`[SYC-HP-02]`).
   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, `check` must transition to `DRIFT_DETECTED`, surface modified files, new endpoints, and new RFCs, and exit `1` when `--strict` is passed (`[SYC-ST-01]`).
3. **Corrupted Watermark Recovery (`[SYC-FR-03]`)**:
   - If `.agents/contract_sync.json` contains malformed JSON, `check` logs a warning to stderr and falls back to `INITIAL_SYNC` without crashing, while `ack` overwrites it with valid `schema_version: 1` JSON.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Atomic file replacement (`tempfile.NamedTemporaryFile` in `.agents/` + `os.replace`) guarantees concurrent readers never observe truncated JSON.
- Preserving sibling domain keys in `.agents/contract_sync.json` allows a multi-domain Hub or multi-service consumer to track each domain independently.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`cmd_ack`, `cmd_brief`, `load_sync_state`, `save_sync_state_atomic`, `evaluate_domain_drift`) and `test_sync_contracts.py`.
- **Downstream Callers**: Task 4 (`SKILL.md` workflow and `scripts/verify.sh`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `ack`, `brief --output`, drift transitions, and malformed JSON recovery.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-02, SYC-ST-01, SYC-ST-02, SYC-AR-01, SYC-FR-03

```gherkin
Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
  Then the file .agents/contract_sync.json is created in the Satellite repository with mode "satellite" and domain "lyrics-sync"
  And the recorded sha256 hashes match all 3 canonical files in the Hub
  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0

Scenario: [SYC-ST-01] [Tier C - Integration] Incremental Drift Detection After Upstream Hub Contract Update
  Given a Satellite repository that previously ran sync_contracts.py ack and is in state "IN_SYNC"
  When the Hub repository updates api_contract.md to version "1.1.0" with a new endpoint POST /api/v1/lyrics-sync/tasks/{id}/cancel and logs RFC-002 in gaps_and_rfcs.md
  And the engineer runs sync_contracts.py check --strict in the Satellite repository
  Then the status transitions from "IN_SYNC" to "DRIFT_DETECTED"
  And the delta report identifies api_contract.md and gaps_and_rfcs.md as modified, surfaces the new cancel endpoint as "MISSING_IN_CODE", and lists RFC-002
  And sync_contracts.py check --strict exits with code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Multi-Domain Watermark Preservation and Explicit RFC Acknowledgement
  Given a Hub repository with domains lyrics-sync and nexus where lyrics-sync is already recorded in .agents/contract_sync.json
  When the engineer invokes sync_contracts.py ack --domain nexus --rfc RFC-005
  Then .agents/contract_sync.json retains the existing "lyrics-sync" entry unchanged
  And records the new "nexus" entry containing "RFC-005" in acknowledged_rfcs

Scenario: [SYC-AR-01] [Tier A - Unit] Atomic Watermark File Update Prevents Partial JSON Reads
  Given an existing .agents/contract_sync.json file in the target repository
  When sync_contracts.py ack writes updated synchronization metadata
  Then the engine writes to a temporary file in .agents/ and atomically replaces .agents/contract_sync.json
  And no leftover temporary files remain in .agents/ after completion

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_st_01` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_st_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_01` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_03` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_3.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_3.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `ack` writes any file inside `shared-contracts/` instead of `.agents/contract_sync.json`.

## Decisions Already Made

- Watermark state is persisted at `<repo_root>/.agents/contract_sync.json` with `schema_version: 1`, `mode`, and per-domain objects containing `hub_commit_sha`, `contract_version`, `last_synced_at`, `file_hashes`, `acknowledged_rfcs`, and `acknowledged_endpoints`.
- `ack` uses atomic file replacement (`os.replace`) inside `.agents/`.

## Definition of Done

- `sync_contracts.py ack` writes `.agents/contract_sync.json` atomically and `check --strict` passes with `IN_SYNC` (V2, V5).
- Upstream contract edits transition status to `DRIFT_DETECTED` and fail `check --strict` with exit code `1` (V3).
- Multi-domain watermark entries and explicit `--rfc` flags are preserved and recorded (V4).
- Corrupted `.agents/contract_sync.json` files are handled gracefully by `check` and repaired by `ack` (V6).
- Ruff and Mypy strict checks pass (V7, V8).
- JUnit report is generated and all covered scenarios pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 2](task_2_heuristic_scanner_and_check_engine.md) — requires topology resolution and heuristic scanner in `sync_contracts.py`.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 3 additions in `sync_contracts.py` and `test_sync_contracts.py`.
---
id: "task_4_skill_definition_and_verify_integration"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["skill", "docs", "harness", "integration"]
order: "a4"
---

# Task 4: Skill Definition, Lifecycle Bridge Instructions, and Verify Harness Integration

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Create the skill definition `skills/sync-shared-contracts/SKILL.md` and wire the test suite into the repository verification script `scripts/verify.sh`.
1. Author `skills/sync-shared-contracts/SKILL.md`:
   - YAML frontmatter strictly containing only `name: sync-shared-contracts` and `description`.
   - Complete documentation of the 3-layer Hybrid Delta Engine (`check`, `brief`, `ack`) and `.agents/contract_sync.json` watermark schema.
   - Detailed 5-step Orchestrated Bridge into `d3nexus:dev-lifecycle`:
     - Step 1: Preflight & Contract Delta Audit (`sync_contracts.py check` & `brief`).
     - Step 2: Scope Confirmation with developer.
     - Step 3: Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`) rules (Hub `task_01` canonical contract update vs Satellite `task_01` consumer DTO/adapter update, Satellite Git read-only symlink rule, and final task running `sync_contracts.py ack`).
     - Step 4: Stage 3 (`dev-implementation`) TDD execution and `sync_contracts.py check --strict` verification.
     - Step 5: Stage 4 (`finishing-a-development-branch`).
2. Wire `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` into `scripts/verify.sh` in Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) alongside `test_setup_contracts.py`.
3. Add final integration test `test_syc_hp_03_skill_and_verify_harness` in `test_sync_contracts.py` verifying `SKILL.md` frontmatter, links, and end-to-end CLI execution (`[SYC-HP-03]`).

## Files

Allowed files:
- `skills/sync-shared-contracts/SKILL.md` (new)
- `scripts/verify.sh`
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
- `skills/setup-shared-contracts/SKILL.md` — companion skill reference

## Design Rationale

- Frontmatter adheres strictly to the two-key contract (`name` + `description`) required by Claude Code and Antigravity.
- Registering `test_sync_contracts.py` in `scripts/verify.sh` ensures every future plugin release validates both `setup-shared-contracts` and `sync-shared-contracts`.
- Applicable skills: `d3nexus:writing-skills`, `d3nexus:verification-before-completion`, `d3nexus:test-driven-development`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `skills/sync-shared-contracts/SKILL.md`, `scripts/verify.sh`, and `test_sync_contracts.py`.
- **Downstream Callers**: All AI agents discovering `sync-shared-contracts` and CI/CD running `scripts/verify.sh`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% full suite integration coverage and `scripts/verify.sh` green gate.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-03

```gherkin
Scenario: [SYC-HP-03] [Tier C - Integration] Skill Definition and Release Verify Harness Execution
  Given the completed sync-shared-contracts skill directory and scripts/verify.sh registration
  When the engineer runs the verification suite for sync-shared-contracts
  Then skills/sync-shared-contracts/SKILL.md passes frontmatter and link validation
  And all unit and integration tests in test_sync_contracts.py pass with exit code 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_03` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_03` | exit 0; contains "OK" | — |
| V3 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py skills/sync-shared-contracts/SKILL.md` | exit 0; contains "0 findings" | — |
| V4 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V6 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "PASS — safe to publish" | — |
| V7 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/sync-shared-contracts.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/sync-shared-contracts.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- `scripts/verify.sh` reports any failure across the verification sections.

## Decisions Already Made

- Skill frontmatter in `skills/sync-shared-contracts/SKILL.md` has exactly `name` and `description` keys.
- `scripts/verify.sh` Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) executes both `test_setup_contracts.py` and `test_sync_contracts.py`.

## Definition of Done

- `skills/sync-shared-contracts/SKILL.md` is complete with valid frontmatter and 5-step `d3nexus:dev-lifecycle` bridge documentation (V3).
- End-to-end integration test `test_syc_hp_03` passes (V2).
- Linting and typing checks pass cleanly (V4, V5).
- `scripts/verify.sh` runs `test_sync_contracts.py` and outputs "PASS — safe to publish" (V6).
- JUnit report is produced and integration tests pass (V7).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 3](task_3_watermark_ack_and_brief_cli.md) — requires all `sync_contracts.py` subcommands (`check`, `brief`, `ack`) to be complete.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert `skills/sync-shared-contracts/SKILL.md` and `scripts/verify.sh`.
# Handoff: sync_shared_contracts

## Table of Contents

- [Status](#status)
- [Identifiers](#identifiers)
- [Read First](#read-first)
- [Resume Prompt](#resume-prompt)
- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
- [Open Notes](#open-notes)
- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

## Status

- **Packaged**: 2026-10-30
- **Design commit**: `822567269819c2269e884ad8e433c274831a7583` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
- **Base branch**: `main`
- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

## Identifiers

| Placeholder | Value |
|-------------|-------|
| `<epic_dir>` | `sync_shared_contracts` |
| `<epic_slug>` | `sync_shared_contracts` |

These are usually different strings. Never derive one from the other.

## Read First

1. `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 4 tasks.
2. `.devtool/epic/sync_shared_contracts/bdd_scenarios.en.md` — the behavioural contract.
3. `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md` — the approved source spec.
4. `.devtool/epic/sync_shared_contracts/principal_review.md`, when present — Principal Review rounds and decisions.

## Resume Prompt

```text
Use the d3nexus:dev-implementation skill for the `sync_shared_contracts` epic.
Read .devtool/epic/sync_shared_contracts/handoff.md first.
Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
Gates 1 and 2 are passed; do not re-run brainstorming or design.
Gate 3 is pending: present the execution order to me and wait for my confirmation.
```

## Execution Guardrails for Receiving LLM

Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:

1. **Bounded context protocol**:
   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
3. **Zero test fakery**: Tests import or invoke real production symbols and do not reconstruct retry loops, progress math, callback behavior, or configuration resolution.
4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.

## Open Notes

- **Dual-Mode Architecture**: `sync-shared-contracts` complements `setup-shared-contracts` by handling Day-2 continuous contract delta detection (`check`), requirements brief generation (`brief`), and atomic watermark acknowledgement (`ack`) in `.agents/contract_sync.json` across both Satellite (relative symlink) and Hub (physical directory) repositories.
- **3-Layer Hybrid Delta Engine**: Combines Git commit/SHA-256 file hash comparison, structured Markdown parsing of the 3 canonical contract files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`), and a lightweight Target Codebase Heuristic Scanner classifying endpoints, headers, and `snake_case`/`camelCase` DTO keys as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
- **Orchestrated `/dev-lifecycle` Bridge**: `SKILL.md` guides agents through a 5-step workflow feeding the `brief` report into Stage 1 (`dev-brainstorming`), Stage 2 (`dev-designer` — enforcing Hub `task_01` contract update vs Satellite `task_01` consumer DTO update and Satellite read-only symlink rule), Stage 3 (`dev-implementation` with `sync_contracts.py ack` + `check --strict`), and Stage 4 (`finishing-a-development-branch`).

## Rules for the Receiving Agent

- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
- This handoff does not pass Gate 3. The developer confirms the execution order.
- Unless the design commit is `uncommitted`: if `git log 822567269819c2269e884ad8e433c274831a7583..main -- .devtool/epic/sync_shared_contracts` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
- This file is a dated record. It is never updated after packaging.
- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.


 succeeded in 0ms:
---
id: "task_1_brief_template_and_contract_parser"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "templates", "parser"]
order: "a1"
---

# Task 1: Canonical Brief Template and Markdown Contract Parser

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Create the canonical delta brief template `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` and implement the structured Markdown contract parser and initial sync baseline logic in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. Author `contract_delta_brief.md.tmpl` using standard library `string.Template` placeholders (`$domain`, `$mode`, `$sync_status`, `$previous_version`, `$current_version`, `$hub_commit_range`, `$changed_files_summary`, `$endpoints_section`, `$payload_keys_section`, `$pipeline_steps_section`, `$rfcs_section`, `$lifecycle_rules_section`).
2. Implement structured Markdown parsing in `sync_contracts.py` for the 3 canonical contract files:
   - `api_contract.md`: Extract `Version`, required authentication headers table, `Endpoints Matrix` rows (`Method`, `Endpoint`, `Auth`, `Purpose`), JSON payload schema top-level and nested keys, and `Version Changelog` entries.
   - `architecture_and_flow.md`: Extract numbered canonical pipeline steps and state machine transitions.
   - `gaps_and_rfcs.md`: Extract `Active RFC Ledger` rows (`RFC ID`, `Title`, `Proposing Repo`, `Status`, `Target Release`, `Breaking?`).
3. Implement initial baseline detection (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet (`[SYC-EC-01]`) and brief rendering (`[SYC-HP-01]`).
4. Initialize `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` covering `[SYC-HP-01]` and `[SYC-EC-01]`.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new)
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` — canonical API contract structure
- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` — canonical architecture structure
- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` — canonical RFC ledger structure

## Design Rationale

- Standard library `string.Template` and regex/line-based table parsers keep `sync_contracts.py` 100% dependency-free and portable across Python 3.10+ environments.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `contract_delta_brief.md.tmpl`, `sync_contracts.py` (`parse_api_contract`, `parse_architecture_and_flow`, `parse_gaps_and_rfcs`, `render_brief`), and `test_sync_contracts.py`.
- **Downstream Callers**: Tasks 2, 3, and 4 build upon `sync_contracts.py` and `test_sync_contracts.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of Markdown table/schema extraction and template substitution.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-01, SYC-EC-01

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_01` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any canonical template placeholder in `contract_delta_brief.md.tmpl` fails substitution under `string.Template`.

## Decisions Already Made

- New frozen contract `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` uses `string.Template` placeholders and emits the 5 canonical brief sections (`Topology & Sync Metadata`, `API & Schema Requirements`, `Architecture & Pipeline Invariants`, `Actionable RFCs & Gaps`, `Lifecycle Execution Rules`).
- Grounded canonical contract files from `skills/setup-shared-contracts/resources/templates/` are `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`.
- When `.agents/contract_sync.json` is absent, `check` reports `status: "INITIAL_SYNC"`, exits `0` by default, and exits `1` when `--strict` is passed.

## Definition of Done

- `contract_delta_brief.md.tmpl` and Markdown contract parsers in `sync_contracts.py` are implemented and render the full brief (V2).
- `INITIAL_SYNC` status detection and `--strict` exit code behavior pass unit tests (V3).
- Ruff linting and Mypy strict type checks pass with zero errors (V4, V5).
- JUnit XML report is generated and integration tests for `SYC-HP-01` and `SYC-EC-01` pass (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Remove `skills/sync-shared-contracts/resources/` to restore clean state.
---
id: "task_2_heuristic_scanner_and_check_engine"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "scanner", "cli"]
order: "a2"
---

# Task 2: Target Codebase Heuristic Scanner and Dual-Mode Check Engine

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Implement the Target Codebase Heuristic Scanner, Dual-Mode topology resolver (Hub physical mode vs Satellite relative symlink mode), circular symlink protection, git-less Hub fallback, and error validation in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Heuristic Codebase Scanner (`[SYC-EC-02]`)**:
   - Recursively scan source files in `<repo_root>` while skipping `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
   - Normalize parameterized endpoints (e.g., `/api/v1/lyrics-sync/tasks/{id}/progress` -> static route segments `/api/v1/lyrics-sync/tasks` and `/progress`) and check both `snake_case` and `camelCase` DTO field names (`lease_duration_ms` / `leaseDurationMs`) to classify each item as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
2. **Git-less Hub Fallback (`[SYC-EC-03]`)**:
   - When the Hub directory is not a Git repository, skip `git rev-parse` / `git log` cleanly without raising subprocess errors and rely on SHA-256 file hashes and `Version` metadata.
3. **Symlink Cycle Protection & Topology Validation (`[SYC-AR-02]`, `[SYC-FR-01]`, `[SYC-FR-02]`)**:
   - Enforce a 10-hop maximum when traversing symbolic links (`[SYC-AR-02]`).
   - Exit with code `1` and remediation instructions if `shared-contracts` is missing (`[SYC-FR-01]`), is a dangling symlink, or lacks any of the 3 canonical contract files (`[SYC-FR-02]`).

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Static route prefix extraction and `snake_case` -> `camelCase` conversion enable language-agnostic heuristic detection across Python, Rust, Dart/Flutter, Kotlin, Swift, and TypeScript repositories without heavy AST dependencies.
- Hop-bounded symlink resolution mirrors `setup_contracts.py` safety invariants.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`scan_target_codebase`, `resolve_topology`, `to_camel_case`, `cmd_check`) and tests in `test_sync_contracts.py`.
- **Downstream Callers**: `cmd_brief` and `cmd_ack` in Task 3.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage on heuristic token matching, symlink loop detection, and missing/dangling path errors.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-EC-02, SYC-EC-03, SYC-AR-02, SYC-FR-01, SYC-FR-02

```gherkin
Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Graceful Fallback When Hub Directory Has No Git History
  Given a Hub directory that was created on disk without a .git repository
  When the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And computes drift status accurately using sha256 file hashes and contract Version metadata

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop

Scenario: [SYC-FR-01] [Tier A - Unit] Refusing Execution When Shared Contracts Directory Is Missing
  Given a target repository that has no shared-contracts directory or symlink
  When the engineer invokes sync_contracts.py check, brief, or ack
  Then the command aborts with exit code 1
  And prints an error instructing the user to initialize or link contracts with setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink or Missing Canonical Files
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path or a domain missing architecture_and_flow.md
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target or missing canonical file
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_03` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_01` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_02` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Symlink traversal follows unbounded loops without enforcing the 10-hop limit.

## Decisions Already Made

- Excluded directories during codebase scanning are `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
- Symlink resolution halts at `MAX_SYMLINK_HOPS = 10`.
- Missing `shared-contracts`, dangling symlinks, or missing canonical files exit with code `1`.

## Definition of Done

- Heuristic codebase scanner accurately classifies parameterized endpoints and `snake_case`/`camelCase` fields (V2).
- Git-less Hub directories are handled cleanly without subprocess errors (V3).
- Circular symlink chains (`> 10` hops), missing `shared-contracts`, and dangling symlinks exit with code `1` and clear diagnostics (V4, V5, V6).
- Ruff and Mypy strict checks pass (V7, V8).
- JUnit report is generated and all covered scenarios pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_brief_template_and_contract_parser.md) — requires initial `sync_contracts.py` parser and test suite scaffold.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 2 additions in `sync_contracts.py` and `test_sync_contracts.py`.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md; cat .devtool/epic/sync_shared_contracts/bdd_scenarios.en.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Sync Shared Contracts Design
     2	
     3	- **Date**: 2026-10-30
     4	- **Status**: Approved
     5	- **Scope**: New skill `skills/sync-shared-contracts/`, CLI engine `sync_contracts.py`, canonical delta brief template, hermetic test suite `test_sync_contracts.py`, integration with `scripts/verify.sh`
     6	- **Next step**: `d3nexus:dev-designer` (Stage 2 — High-Level Design, BDD Scenarios, and Kanban Breakdown)
     7	
     8	## Table of Contents
     9	
    10	- [1. Background and Motivation](#1-background-and-motivation)
    11	- [2. Goals and Non-Goals](#2-goals-and-non-goals)
    12	- [3. Architecture and Dual-Mode Detection](#3-architecture-and-dual-mode-detection)
    13	- [4. Directory Structure and Sync Watermark Schema](#4-directory-structure-and-sync-watermark-schema)
    14	- [5. CLI Engine Specifications](#5-cli-engine-specifications)
    15	- [6. Target Codebase Heuristic Scanner](#6-target-codebase-heuristic-scanner)
    16	- [7. Orchestrated Lifecycle Bridge](#7-orchestrated-lifecycle-bridge)
    17	- [8. Verification and Test Strategy](#8-verification-and-test-strategy)
    18	- [9. Error Handling and Edge Cases](#9-error-handling-and-edge-cases)
    19	- [10. Risks and Mitigations](#10-risks-and-mitigations)
    20	
    21	## 1. Background and Motivation
    22	
    23	With the introduction of `setup-shared-contracts`, multi-repository ecosystems (such as the control plane `D3Nexus` paired with worker satellites like `lyrics-sync` and mobile clients like `nexus`) have a standardized way to initialize physical `shared-contracts/` directories, relative symbolic links, and governance rules.
    24	
    25	However, after initial setup (Day-0), teams face continuous synchronization challenges (Day-2 operations):
    26	- When the Hub repository updates `api_contract.md` or `architecture_and_flow.md` (or approves an RFC in `gaps_and_rfcs.md`), satellite repositories lack an automated tool to detect what changed since their last implementation cycle.
    27	- When a satellite repository logs a new `Draft` or `In Review` proposal in `gaps_and_rfcs.md`, the Hub repository needs a deterministic check to discover actionable RFCs and incorporate them into backend implementation plans.
    28	- Transitioning from detected contract deltas into `d3nexus:dev-lifecycle` (Spec -> HLD & BDD -> Worktree TDD Implementation -> Branch Finishing) currently requires manual inspection and copy-pasting of endpoints, schemas, and governance constraints.
    29	
    30	To bridge contract changes directly into target repository execution, we are introducing the `sync-shared-contracts` skill and its companion CLI engine `sync_contracts.py`.
    31	
    32	## 2. Goals and Non-Goals
    33	
    34	### Goals
    35	- Provide a zero-dependency standard-library Python CLI (`sync_contracts.py`) supporting `check`, `brief`, and `ack` subcommands.
    36	- Implement a **3-Layer Hybrid Delta Engine**:
    37	  1. **Git & SHA-256 Watermark Diff**: Compare Hub git history and canonical file hashes against `.agents/contract_sync.json`.
    38	  2. **Structured Markdown Contract Parser**: Parse endpoints, headers, JSON payload keys, pipeline steps, and active RFC tables from the 3 canonical contract files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
    39	  3. **Target Codebase Heuristic Scanner**: Scan target repository source files to classify contract endpoints, headers, and payload keys as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
    40	- Support **Dual-Mode Execution** (auto-detecting Satellite symlink mode vs Hub physical directory mode).
    41	- Generate a structured **Contract Requirements Brief** (`brief`) that feeds directly into `d3nexus:dev-lifecycle` across all 4 stages (`dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `finishing-a-development-branch`).
    42	- Provide an atomic watermark update command (`ack`) that records the synced contract version, Hub commit SHA, file hashes, and acknowledged RFCs/endpoints in `.agents/contract_sync.json`.
    43	
    44	### Non-Goals
    45	- Modifying or replacing `setup-shared-contracts` topology initialization (`init-hub`, `link-satellite`).
    46	- Autonomously committing across git symlink boundaries in violation of Rule 7 of `CRITICAL_RULES.md`.
    47	- Pushing git commits to remote repositories without explicit user confirmation (prohibited by Rule 3).
    48	
    49	## 3. Architecture and Dual-Mode Detection
    50	
    51	The skill operates across both sides of the Star Topology by inspecting `<repo_root>/shared-contracts`:
    52	
    53	1. **Satellite Mode (`shared-contracts` is a relative symbolic link)**:
    54	   - Resolves the symlink target to identify the `<domain>` folder and parent `<hub_root>`.
    55	   - Detects upstream changes made in the Hub repository (new endpoints, updated payload fields, pipeline rules, and `Approved` RFCs) that need to be implemented in the satellite consumer/worker codebase.
    56	   - Enforces the strict Git read-only symlink boundary (never staging `shared-contracts/` inside the satellite repository; tracking sync state exclusively in `.agents/contract_sync.json`).
    57	2. **Hub Mode (`shared-contracts/` is a physical directory)**:
    58	   - Iterates over domain subdirectories `shared-contracts/<domain>/` (or targets a specific `--domain`).
    59	   - Detects `Draft`, `In Review`, or `Approved` RFCs and gaps proposed by satellites in `gaps_and_rfcs.md`, as well as contract changes not yet reflected in the Hub backend source code or `.agents/contract_sync.json`.
    60	   - Enforces the `task_01` Contract-First synchronization rule during `dev-designer` task breakdown.
    61	
    62	```mermaid
    63	flowchart TD
    64	    subgraph TARGET ["Target Repository (Satellite or Hub)"]
    65	        CLI["sync_contracts.py<br/>(check / brief / ack)"]
    66	        STATE[".agents/contract_sync.json<br/>(Sync Watermark State)"]
    67	        SRC["Target Source Code<br/>(Heuristic Endpoint & Field Scan)"]
    68	    end
    69	
    70	    subgraph CONTRACT ["Shared Contracts (Physical or via Symlink)"]
    71	        API["api_contract.md"]
    72	        ARCH["architecture_and_flow.md"]
    73	        RFC["gaps_and_rfcs.md"]
    74	        GIT["Hub Git History (git log / diff)"]
    75	    end
    76	
    77	    subgraph LIFECYCLE ["Orchestrated /dev-lifecycle"]
    78	        S1["Stage 1: dev-brainstorming<br/>(Bilingual Design Spec)"]
    79	        S2["Stage 2: dev-designer<br/>(HLD + BDD + Kanban Tasks)"]
    80	        S3["Stage 3: dev-implementation<br/>(Worktree TDD + sync_contracts.py ack)"]
    81	        S4["Stage 4: finishing-a-development-branch"]
    82	    end
    83	
    84	    CLI -->|"1. Read previous watermark"| STATE
    85	    CLI -->|"2. Git diff + Parse Markdown"| CONTRACT
    86	    CLI -->|"3. Scan Endpoint/DTO tokens"| SRC
    87	    CLI -->|"4. Emit Contract Delta Brief"| S1
    88	    S1 --> S2 --> S3 --> S4
    89	    S3 -->|"5. Update sync watermark"| STATE
    90	```
    91	
    92	## 4. Directory Structure and Sync Watermark Schema
    93	
    94	### 4.1 Skill Directory Structure
    95	
    96	```text
    97	skills/sync-shared-contracts/
    98	├── SKILL.md
    99	└── resources/
   100	    ├── scripts/
   101	    │   ├── sync_contracts.py
   102	    │   └── test_sync_contracts.py
   103	    └── templates/
   104	        └── contract_delta_brief.md.tmpl
   105	```
   106	
   107	### 4.2 Sync Watermark Schema (`.agents/contract_sync.json`)
   108	
   109	The watermark file is stored inside the target repository at `.agents/contract_sync.json`:
   110	
   111	```json
   112	{
   113	  "schema_version": 1,
   114	  "mode": "satellite",
   115	  "domains": {
   116	    "lyrics-sync": {
   117	      "hub_commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
   118	      "contract_version": "1.1.0",
   119	      "last_synced_at": "2026-10-30T18:30:00Z",
   120	      "file_hashes": {
   121	        "api_contract.md": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
   122	        "architecture_and_flow.md": "sha256:...",
   123	        "gaps_and_rfcs.md": "sha256:..."
   124	      },
   125	      "acknowledged_rfcs": ["RFC-001", "RFC-002"],
   126	      "acknowledged_endpoints": [
   127	        "POST /api/v1/lyrics-sync/tasks/claim",
   128	        "POST /api/v1/lyrics-sync/tasks/{id}/progress",
   129	        "POST /api/v1/lyrics-sync/tasks/{id}/complete",
   130	        "GET /api/v1/lyrics-sync/status"
   131	      ]
   132	    }
   133	  }
   134	}
   135	```
   136	
   137	## 5. CLI Engine Specifications
   138	
   139	The script `sync_contracts.py` provides three subcommands:
   140	
   141	### 5.1 Command: `check`
   142	```bash
   143	python3 sync_contracts.py check [--repo-root <path>] [--domain <domain_name>] [--json] [--strict]
   144	```
   145	- **Validation**:
   146	  - Verifies `shared-contracts` exists and resolves cleanly (no dangling symlinks, all 3 canonical files present).
   147	- **Actions**:
   148	  1. Loads `.agents/contract_sync.json` if present; otherwise marks the domain status as `INITIAL_SYNC`.
   149	  2. Computes current `sha256` hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, and queries the latest git commit SHA affecting the domain folder in the Hub repository (falling back gracefully if git history is unavailable).
   150	  3. Parses the 3 canonical Markdown files to extract version metadata, required headers, endpoints matrix rows, JSON schema keys, pipeline steps, and RFC ledger entries.
   151	  4. Runs the Target Codebase Heuristic Scanner across `<repo_root>` to check whether extracted endpoints, headers, and payload keys appear in source code.
   152	  5. Determines overall sync status: `IN_SYNC`, `INITIAL_SYNC`, or `DRIFT_DETECTED`.
   153	- **Exit Codes**:
   154	  - `0` when `IN_SYNC` (or when `DRIFT_DETECTED` / `INITIAL_SYNC` without `--strict`).
   155	  - `1` when topology/symlink errors occur, or when `--strict` is passed and status is not `IN_SYNC`.
   156	
   157	### 5.2 Command: `brief`
   158	```bash
   159	python3 sync_contracts.py brief [--repo-root <path>] [--domain <domain_name>] [--output <path>]
   160	```
   161	- **Actions**:
   162	  - Executes the full 3-layer delta analysis from `check`.
   163	  - Renders `contract_delta_brief.md.tmpl` into a structured Markdown report containing:
   164	    1. **Topology & Sync Metadata**: Mode (`hub` / `satellite`), Domain, Version transition (`previous -> current`), Hub commit range, and Changed files list.
   165	    2. **API & Schema Requirements**: Endpoints and JSON payload fields added or modified, annotated with heuristic scan status (`FOUND_IN_CODE` vs `MISSING_IN_CODE`).
   166	    3. **Architecture & Pipeline Invariants**: Canonical pipeline steps, state machine transitions, and cancellation/isolation constraints.
   167	    4. **Actionable RFCs & Gaps**: Pending or newly approved entries from `gaps_and_rfcs.md` requiring action in the current repository mode.
   168	    5. **Lifecycle Execution Rules**: Mandatory instructions for `dev-brainstorming`, `dev-designer` (`task_01` rule and symlink boundary rules), and `dev-implementation` (`sync_contracts.py ack` verification step).
   169	
   170	### 5.3 Command: `ack`
   171	```bash
   172	python3 sync_contracts.py ack [--repo-root <path>] [--domain <domain_name>] [--rfc <RFC-ID> ...]
   173	```
   174	- **Actions**:
   175	  - Computes the current file hashes, contract version, Hub git commit SHA, endpoints list, and RFC IDs (all `Approved` / `Implemented` RFCs plus any explicitly passed via `--rfc`).
   176	  - Writes or updates `.agents/contract_sync.json` atomically using a temporary file and `os.replace()`.
   177	
   178	## 6. Target Codebase Heuristic Scanner
   179	
   180	To provide immediate visibility into whether contract items are already implemented in the target repository (especially during `INITIAL_SYNC` or partial implementations):
   181	- **Scanned Directories**: Walks `<repo_root>` recursively while excluding `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
   182	- **Supported Source Extensions**: `.py`, `.rs`, `.dart`, `.kt`, `.kts`, `.swift`, `.ts`, `.tsx`, `.js`, `.go`, `.java`, `.yaml`, `.yml`, `.json`.
   183	- **Token Normalization**:
   184	  - For endpoints like `/api/v1/lyrics-sync/tasks/{id}/progress`, extracts static path segments (e.g., `/api/v1/lyrics-sync/tasks` and `/progress` or `tasks/claim`) and checks whether those route fragments exist in source files.
   185	  - For headers (`X-Worker-Token`, `X-Correlation-ID`) and top-level JSON schema keys (`task_id`, `lease_duration_ms`, `output_data`), checks identifier presence (both `snake_case` and `camelCase` equivalents for mobile/frontend clients like Dart/Swift/TypeScript).
   186	
   187	## 7. Orchestrated Lifecycle Bridge
   188	
   189	When a developer invokes `/sync-shared-contracts` (or asks to check contract changes and execute on a target repo), the skill orchestrates the following 5-step workflow:
   190	
   191	1. **Step 1 — Contract Audit & Brief Generation**:
   192	   - Run `sync_contracts.py check` and `sync_contracts.py brief`.
   193	   - If `shared-contracts` is missing or broken, direct the user to `d3nexus:setup-shared-contracts`.
   194	   - If `IN_SYNC` and no `MISSING_IN_CODE` items or pending RFCs exist, report that the repository is fully synchronized and stop.
   195	2. **Step 2 — Scope Confirmation**:
   196	   - Present the generated **Contract Requirements Brief** to the developer and confirm which deltas/RFCs to target and the `<epic_slug>`.
   197	3. **Step 3 — Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`)**:
   198	   - Enter `d3nexus:dev-lifecycle` using the confirmed Contract Requirements Brief as grounding context:
   199	     - **Stage 1 (`dev-brainstorming`)**: Produce the bilingual spec pair (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.en.md` and `.vi.md`) anchored on the contract delta without re-asking questions already settled by the contract, then obtain Gate 1 approval.
   200	     - **Stage 2 (`dev-designer`)**: Generate the bilingual HLD, 5-dimension BDD scenarios (`bdd_scenarios.en.md` / `.vi.md`), and Kanban task breakdown (`task_*.md`) for Gate 2:
   201	       - In **Hub Mode**: `task_01` updates the physical `shared-contracts/<domain>/` files (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
   202	       - In **Satellite Mode**: `task_01` updates internal consumer DTOs, API clients, and mock fixtures (never including `shared-contracts/` in `Files Allowed`).
   203	       - In **Both Modes**: The final task (or `task_01` verification hook) includes `.agents/contract_sync.json` in `Files Allowed` and runs `sync_contracts.py ack` + `sync_contracts.py check --strict` so the sync watermark is committed alongside the implementation.
   204	4. **Step 4 — Stage 3 (`dev-implementation`)**:
   205	   - Execute tasks in an isolated worktree via TDD, verify `sync_contracts.py check --strict` passes, run Gate 4 (`quality_check` + `check_bdd_traceability.py` + `audit_epic.py`), and pass the Review Choice loop and Gate 5.
   206	5. **Step 5 — Stage 4 (`finishing-a-development-branch`)**:
   207	   - Rebase, verify, merge `--no-ff`, and archive epic artifacts into `.devtool/epic/<epic_slug>/`.
   208	
   209	## 8. Verification and Test Strategy
   210	
   211	The hermetic test suite in `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` uses Python's standard `unittest` framework and `tempfile.TemporaryDirectory`:
   212	- **Test Initial Sync & Dual-Mode Detection**: Verifies `check` accurately detects Hub physical mode and Satellite symlink mode on fresh repositories without `.agents/contract_sync.json`.
   213	- **Test Markdown Contract Parser**: Verifies extraction of `Version`, headers, `Endpoints Matrix` rows, JSON schema keys, pipeline steps, and `Active RFC Ledger` statuses.
   214	- **Test Target Codebase Heuristic Scanner**: Verifies detection of implemented vs missing endpoints and `snake_case` / `camelCase` DTO fields across mock source files.
   215	- **Test Watermark Ack & Incremental Drift**: Verifies that running `ack` transitions `check --strict` to exit `0` (`IN_SYNC`), and subsequent edits to `api_contract.md` or `gaps_and_rfcs.md` in the Hub trigger `DRIFT_DETECTED` (exit `1` under `--strict`) with accurate git commit log and file hash deltas.
   216	- **Test Brief Rendering & Error Handling**: Verifies `brief` output structure and graceful error codes for missing or dangling `shared-contracts` links.
   217	- **Harness Integration**: Registered in `scripts/verify.sh` alongside `test_setup_contracts.py`.
   218	
   219	## 9. Error Handling and Edge Cases
   220	
   221	| Scenario | Handled By | Behavior |
   222	|---|---|---|
   223	| `shared-contracts` does not exist | `check` / `brief` / `ack` | Exits `1` with remediation prompt pointing to `setup_contracts.py`. |
   224	| Satellite `shared-contracts` is a dangling symlink | `check` / `brief` / `ack` | Detects broken target, exits `1` with instructions to re-run `link-satellite --force`. |
   225	| `.agents/contract_sync.json` does not exist yet | `check` / `brief` | Reports status `INITIAL_SYNC`, parses full contract baseline, and classifies items via codebase heuristic scan. |
   226	| `.agents/contract_sync.json` contains malformed JSON | `check` / `ack` | Logs warning, treats state as unsynced during `check`, and overwrites cleanly on `ack`. |
   227	| Hub directory is not a Git repository | `check` / `brief` / `ack` | Skips `git log` / `git rev-parse` gracefully and relies on `sha256` file hashes and `Version` metadata. |
   228	
   229	## 10. Risks and Mitigations
   230	
   231	- **Risk: False negatives in Heuristic Codebase Scanner when target repos use camelCase or segmented route constants.**
   232	  *Mitigation*: The scanner checks normalized route suffixes (stripping `{param}` placeholders) and checks both `snake_case` and `camelCase` field tokens, while treating heuristic results as advisory indicators alongside the authoritative `.agents/contract_sync.json` watermark.
   233	- **Risk: Satellite agents accidentally staging `shared-contracts/` when updating sync state.**
   234	  *Mitigation*: Sync state is stored strictly inside `<repo_root>/.agents/contract_sync.json`, completely outside the `shared-contracts` symlink, and `brief` explicitly injects the `Files Allowed` prohibition reminder for `dev-designer`.
   235	
# Sync Shared Contracts BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
  Then the file .agents/contract_sync.json is created in the Satellite repository with mode "satellite" and domain "lyrics-sync"
  And the recorded sha256 hashes match all 3 canonical files in the Hub
  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0

Scenario: [SYC-HP-03] [Tier C - Integration] Skill Definition and Release Verify Harness Execution
  Given the completed sync-shared-contracts skill directory and scripts/verify.sh registration
  When the engineer runs the verification suite for sync-shared-contracts
  Then skills/sync-shared-contracts/SKILL.md passes frontmatter and link validation
  And all unit and integration tests in test_sync_contracts.py pass with exit code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided

Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Graceful Fallback When Hub Directory Has No Git History
  Given a Hub directory that was created on disk without a .git repository
  When the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And computes drift status accurately using sha256 file hashes and contract Version metadata
```

## Dimension 3: State Transitions

```gherkin
Scenario: [SYC-ST-01] [Tier C - Integration] Incremental Drift Detection After Upstream Hub Contract Update
  Given a Satellite repository that previously ran sync_contracts.py ack and is in state "IN_SYNC"
  When the Hub repository updates api_contract.md to version "1.1.0" with a new endpoint POST /api/v1/lyrics-sync/tasks/{id}/cancel and logs RFC-002 in gaps_and_rfcs.md
  And the engineer runs sync_contracts.py check --strict in the Satellite repository
  Then the status transitions from "IN_SYNC" to "DRIFT_DETECTED"
  And the delta report identifies api_contract.md and gaps_and_rfcs.md as modified, surfaces the new cancel endpoint as "MISSING_IN_CODE", and lists RFC-002
  And sync_contracts.py check --strict exits with code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Multi-Domain Watermark Preservation and Explicit RFC Acknowledgement
  Given a Hub repository with domains lyrics-sync and nexus where lyrics-sync is already recorded in .agents/contract_sync.json
  When the engineer invokes sync_contracts.py ack --domain nexus --rfc RFC-005
  Then .agents/contract_sync.json retains the existing "lyrics-sync" entry unchanged
  And records the new "nexus" entry containing "RFC-005" in acknowledged_rfcs
```

## Dimension 4: Async and Multi-Repo Concurrency

```gherkin
Scenario: [SYC-AR-01] [Tier A - Unit] Atomic Watermark File Update Prevents Partial JSON Reads
  Given an existing .agents/contract_sync.json file in the target repository
  When sync_contracts.py ack writes updated synchronization metadata
  Then the engine writes to a temporary file in .agents/ and atomically replaces .agents/contract_sync.json
  And no leftover temporary files remain in .agents/ after completion

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop
```

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [SYC-FR-01] [Tier A - Unit] Refusing Execution When Shared Contracts Directory Is Missing
  Given a target repository that has no shared-contracts directory or symlink
  When the engineer invokes sync_contracts.py check, brief, or ack
  Then the command aborts with exit code 1
  And prints an error instructing the user to initialize or link contracts with setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink or Missing Canonical Files
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path or a domain missing architecture_and_flow.md
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target or missing canonical file

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```


exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md .devtool/epic/sync_shared_contracts/task_2_heuristic_scanner_and_check_engine.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
---
id: "task_1_brief_template_and_contract_parser"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "templates", "parser"]
order: "a1"
---

# Task 1: Canonical Brief Template and Markdown Contract Parser

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Create the canonical delta brief template `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` and implement the structured Markdown contract parser and initial sync baseline logic in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. Author `contract_delta_brief.md.tmpl` using standard library `string.Template` placeholders (`$domain`, `$mode`, `$sync_status`, `$previous_version`, `$current_version`, `$hub_commit_range`, `$changed_files_summary`, `$endpoints_section`, `$payload_keys_section`, `$pipeline_steps_section`, `$rfcs_section`, `$lifecycle_rules_section`).
2. Implement structured Markdown parsing in `sync_contracts.py` for the 3 canonical contract files:
   - `api_contract.md`: Extract `Version`, required authentication headers table, `Endpoints Matrix` rows (`Method`, `Endpoint`, `Auth`, `Purpose`), JSON payload schema top-level and nested keys, and `Version Changelog` entries.
   - `architecture_and_flow.md`: Extract numbered canonical pipeline steps and state machine transitions.
   - `gaps_and_rfcs.md`: Extract `Active RFC Ledger` rows (`RFC ID`, `Title`, `Proposing Repo`, `Status`, `Target Release`, `Breaking?`).
3. Implement initial baseline detection (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet (`[SYC-EC-01]`) and brief rendering (`[SYC-HP-01]`).
4. Initialize `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` covering `[SYC-HP-01]` and `[SYC-EC-01]`.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new)
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` — canonical API contract structure
- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` — canonical architecture structure
- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` — canonical RFC ledger structure

## Design Rationale

- Standard library `string.Template` and regex/line-based table parsers keep `sync_contracts.py` 100% dependency-free and portable across Python 3.10+ environments.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `contract_delta_brief.md.tmpl`, `sync_contracts.py` (`parse_api_contract`, `parse_architecture_and_flow`, `parse_gaps_and_rfcs`, `render_brief`), and `test_sync_contracts.py`.
- **Downstream Callers**: Tasks 2, 3, and 4 build upon `sync_contracts.py` and `test_sync_contracts.py`.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of Markdown table/schema extraction and template substitution.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-01, SYC-EC-01

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_hp_01` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_01` | exit 0; contains "OK" | — |
| V4 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V5 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V6 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_1.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_1.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Any canonical template placeholder in `contract_delta_brief.md.tmpl` fails substitution under `string.Template`.

## Decisions Already Made

- New frozen contract `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` uses `string.Template` placeholders and emits the 5 canonical brief sections (`Topology & Sync Metadata`, `API & Schema Requirements`, `Architecture & Pipeline Invariants`, `Actionable RFCs & Gaps`, `Lifecycle Execution Rules`).
- Grounded canonical contract files from `skills/setup-shared-contracts/resources/templates/` are `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`.
- When `.agents/contract_sync.json` is absent, `check` reports `status: "INITIAL_SYNC"`, exits `0` by default, and exits `1` when `--strict` is passed.

## Definition of Done

- `contract_delta_brief.md.tmpl` and Markdown contract parsers in `sync_contracts.py` are implemented and render the full brief (V2).
- `INITIAL_SYNC` status detection and `--strict` exit code behavior pass unit tests (V3).
- Ruff linting and Mypy strict type checks pass with zero errors (V4, V5).
- JUnit XML report is generated and integration tests for `SYC-HP-01` and `SYC-EC-01` pass (V6).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- None.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Remove `skills/sync-shared-contracts/resources/` to restore clean state.
---
id: "task_2_heuristic_scanner_and_check_engine"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "scanner", "cli"]
order: "a2"
---

# Task 2: Target Codebase Heuristic Scanner and Dual-Mode Check Engine

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Implement the Target Codebase Heuristic Scanner, Dual-Mode topology resolver (Hub physical mode vs Satellite relative symlink mode), circular symlink protection, git-less Hub fallback, and error validation in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Heuristic Codebase Scanner (`[SYC-EC-02]`)**:
   - Recursively scan source files in `<repo_root>` while skipping `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
   - Normalize parameterized endpoints (e.g., `/api/v1/lyrics-sync/tasks/{id}/progress` -> static route segments `/api/v1/lyrics-sync/tasks` and `/progress`) and check both `snake_case` and `camelCase` DTO field names (`lease_duration_ms` / `leaseDurationMs`) to classify each item as `FOUND_IN_CODE` or `MISSING_IN_CODE`.
2. **Git-less Hub Fallback (`[SYC-EC-03]`)**:
   - When the Hub directory is not a Git repository, skip `git rev-parse` / `git log` cleanly without raising subprocess errors and rely on SHA-256 file hashes and `Version` metadata.
3. **Symlink Cycle Protection & Topology Validation (`[SYC-AR-02]`, `[SYC-FR-01]`, `[SYC-FR-02]`)**:
   - Enforce a 10-hop maximum when traversing symbolic links (`[SYC-AR-02]`).
   - Exit with code `1` and remediation instructions if `shared-contracts` is missing (`[SYC-FR-01]`), is a dangling symlink, or lacks any of the 3 canonical contract files (`[SYC-FR-02]`).

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Static route prefix extraction and `snake_case` -> `camelCase` conversion enable language-agnostic heuristic detection across Python, Rust, Dart/Flutter, Kotlin, Swift, and TypeScript repositories without heavy AST dependencies.
- Hop-bounded symlink resolution mirrors `setup_contracts.py` safety invariants.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`scan_target_codebase`, `resolve_topology`, `to_camel_case`, `cmd_check`) and tests in `test_sync_contracts.py`.
- **Downstream Callers**: `cmd_brief` and `cmd_ack` in Task 3.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% branch coverage on heuristic token matching, symlink loop detection, and missing/dangling path errors.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-EC-02, SYC-EC-03, SYC-AR-02, SYC-FR-01, SYC-FR-02

```gherkin
Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Graceful Fallback When Hub Directory Has No Git History
  Given a Hub directory that was created on disk without a .git repository
  When the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And computes drift status accurately using sha256 file hashes and contract Version metadata

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop

Scenario: [SYC-FR-01] [Tier A - Unit] Refusing Execution When Shared Contracts Directory Is Missing
  Given a target repository that has no shared-contracts directory or symlink
  When the engineer invokes sync_contracts.py check, brief, or ack
  Then the command aborts with exit code 1
  And prints an error instructing the user to initialize or link contracts with setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink or Missing Canonical Files
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path or a domain missing architecture_and_flow.md
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target or missing canonical file
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_02` | exit 0; contains "OK" | — |
| V3 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ec_03` | exit 0; contains "OK" | — |
| V4 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_ar_02` | exit 0; contains "OK" | — |
| V5 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_01` | exit 0; contains "OK" | — |
| V6 | GREEN | `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -k test_syc_fr_02` | exit 0; contains "OK" | — |
| V7 | TIER-B | `ruff check skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
| V9 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Symlink traversal follows unbounded loops without enforcing the 10-hop limit.

## Decisions Already Made

- Excluded directories during codebase scanning are `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, and `__pycache__`.
- Symlink resolution halts at `MAX_SYMLINK_HOPS = 10`.
- Missing `shared-contracts`, dangling symlinks, or missing canonical files exit with code `1`.

## Definition of Done

- Heuristic codebase scanner accurately classifies parameterized endpoints and `snake_case`/`camelCase` fields (V2).
- Git-less Hub directories are handled cleanly without subprocess errors (V3).
- Circular symlink chains (`> 10` hops), missing `shared-contracts`, and dangling symlinks exit with code `1` and clear diagnostics (V4, V5, V6).
- Ruff and Mypy strict checks pass (V7, V8).
- JUnit report is generated and all covered scenarios pass (V9).
- Task execution is verified and recorded in evidence (Gate 5).

## Dependencies & Blockers

- Blocked by [Task 1](task_1_brief_template_and_contract_parser.md) — requires initial `sync_contracts.py` parser and test suite scaffold.

## References & Rollback

- Spec: `.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md`
- HLD: `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md`
- Rollback: Revert Task 2 additions in `sync_contracts.py` and `test_sync_contracts.py`.

codex
The design distinguishes contract drift from advisory code scanning. I’m checking whether acknowledgement preserves unimplemented scope, and whether the task order can pass its acceptance checks without requiring later tasks early.

exec
/bin/zsh -lc "nl -ba skills/setup-shared-contracts/resources/scripts/setup_contracts.py | sed -n '1,260p'; nl -ba skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl; nl -ba skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl; nl -ba skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""CLI Engine for managing multi-repo shared contracts across Hub and Satellite repositories."""
     3	
     4	from __future__ import annotations
     5	
     6	import argparse
     7	import datetime
     8	import os
     9	import re
    10	import shutil
    11	import string
    12	import sys
    13	import uuid
    14	from pathlib import Path
    15	
    16	TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
    17	MAX_SYMLINK_DEPTH = 10
    18	DOMAIN_REGEX = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
    19	CANONICAL_CONTRACT_FILES = (
    20	    "api_contract.md",
    21	    "architecture_and_flow.md",
    22	    "gaps_and_rfcs.md",
    23	)
    24	
    25	
    26	def normalize_domain(domain: str) -> str:
    27	    """Normalize domain name by stripping whitespace and lowercasing."""
    28	    return domain.strip().lower()
    29	
    30	
    31	def validate_domain(domain: str) -> str:
    32	    """Normalize and validate domain name for safe single-component path containment."""
    33	    normalized = normalize_domain(domain)
    34	    if not normalized:
    35	        raise ValueError("Domain name cannot be empty.")
    36	    if "/" in normalized or "\\" in normalized or ".." in normalized or normalized == ".":
    37	        raise ValueError(
    38	            f"Domain name '{domain}' cannot contain path separators or directory traversal."
    39	        )
    40	    if not DOMAIN_REGEX.match(normalized):
    41	        raise ValueError(
    42	            f"Domain name '{domain}' is invalid: must start with alphanumeric and contain only [a-z0-9_-]."
    43	        )
    44	    return normalized
    45	
    46	
    47	def atomic_write_text(target_path: Path, content: str) -> None:
    48	    """Write content to target_path atomically using a temporary swap file."""
    49	    target_path.parent.mkdir(parents=True, exist_ok=True)
    50	    tmp_path = target_path.parent / f".tmp_{target_path.name}_{uuid.uuid4().hex}"
    51	    try:
    52	        tmp_path.write_text(content, encoding="utf-8")
    53	        os.replace(tmp_path, target_path)
    54	    except Exception:
    55	        if tmp_path.exists():
    56	            try:
    57	                tmp_path.unlink()
    58	            except OSError:
    59	                pass
    60	        raise
    61	
    62	
    63	def resolve_symlink_safe(path: Path) -> tuple[Path, bool]:
    64	    """Resolve a path and all intermediate symlink components with depth and cycle limits."""
    65	    try:
    66	        current = path.absolute() if not path.is_absolute() else path
    67	    except (OSError, RuntimeError):
    68	        return path, False
    69	
    70	    visited: set[tuple[int, int] | str] = set()
    71	    depth = 0
    72	
    73	    while True:
    74	        parts = current.parts
    75	        if not parts:
    76	            break
    77	
    78	        accum = Path(parts[0])
    79	        symlink_found = False
    80	
    81	        for i in range(1, len(parts)):
    82	            accum = accum / parts[i]
    83	            if accum.is_symlink() or os.path.islink(accum):
    84	                depth += 1
    85	                if depth > MAX_SYMLINK_DEPTH:
    86	                    return accum, False
    87	
    88	                try:
    89	                    st = os.lstat(accum)
    90	                    node_key: tuple[int, int] | str = (
    91	                        (st.st_dev, st.st_ino) if st.st_ino != 0 else str(accum)
    92	                    )
    93	                except (OSError, RuntimeError):
    94	                    return accum, False
    95	
    96	                if node_key in visited:
    97	                    return accum, False
    98	                visited.add(node_key)
    99	
   100	                try:
   101	                    raw_target = os.readlink(accum)
   102	                except (OSError, RuntimeError):
   103	                    return accum, False
   104	
   105	                remaining = parts[i + 1:]
   106	                if os.path.isabs(raw_target):
   107	                    new_path = Path(raw_target, *remaining)
   108	                else:
   109	                    new_path = Path(accum.parent, raw_target, *remaining)
   110	
   111	                current = Path(os.path.normpath(new_path))
   112	                symlink_found = True
   113	                break
   114	
   115	        if not symlink_found:
   116	            break
   117	
   118	    try:
   119	        return current, current.exists()
   120	    except (OSError, RuntimeError):
   121	        return current, False
   122	
   123	
   124	def _get_timestamp() -> str:
   125	    """Return ISO-8601 UTC timestamp."""
   126	    utc_tz = getattr(datetime, "UTC", datetime.timezone.utc)  # noqa: UP017
   127	    return datetime.datetime.now(utc_tz).strftime("%Y-%m-%dT%H:%M:%SZ")
   128	
   129	
   130	def _load_template(name: str) -> string.Template:
   131	    """Load a template file and return string.Template instance."""
   132	    path = TEMPLATES_DIR / name
   133	    if not path.is_file():
   134	        raise FileNotFoundError(f"Canonical template not found: {path}")
   135	    return string.Template(path.read_text(encoding="utf-8"))
   136	
   137	
   138	def _update_readme_table(readme_path: Path, domain: str) -> None:
   139	    """Ensure domain is registered in the Outbound Symlink Mappings table."""
   140	    normalized = normalize_domain(domain)
   141	    content = readme_path.read_text(encoding="utf-8")
   142	    if f"| {normalized} " in content or f"|{normalized}|" in content:
   143	        return
   144	
   145	    table_header = "| Domain | Target Path | Target Satellites | Status |"
   146	    table_separator = "|---|---|---|---|"
   147	    new_row = f"| {normalized} | shared-contracts/{normalized} | {normalized} | Active |"
   148	
   149	    if table_separator in content:
   150	        parts = content.split(table_separator, 1)
   151	        updated = f"{parts[0]}{table_separator}\n{new_row}{parts[1]}"
   152	        atomic_write_text(readme_path, updated)
   153	    elif table_header in content:
   154	        parts = content.split(table_header, 1)
   155	        updated = f"{parts[0]}{table_header}\n{table_separator}\n{new_row}{parts[1]}"
   156	        atomic_write_text(readme_path, updated)
   157	    else:
   158	        table_block = (
   159	            f"\n## Outbound Symlink Mappings\n\n"
   160	            f"{table_header}\n{table_separator}\n{new_row}\n"
   161	        )
   162	        atomic_write_text(readme_path, content + table_block)
   163	
   164	
   165	def cmd_init_hub(repo_root: Path, domain: str | None = None, force: bool = False) -> int:
   166	    """Initialize a physical Hub repository with canonical contract files and rules."""
   167	    shared_contracts_dir = repo_root / "shared-contracts"
   168	
   169	    # 1. Validation: Hub must NEVER be a symlink
   170	    if shared_contracts_dir.is_symlink() or os.path.islink(shared_contracts_dir):
   171	        sys.stderr.write(
   172	            "ERROR [SSC-FR-01]: Target 'shared-contracts' is an existing symbolic link (symlink).\n"
   173	            "Hub repositories must maintain a physical directory as the Single Source of Truth (SSOT).\n"
   174	        )
   175	        return 1
   176	
   177	    shared_contracts_dir.mkdir(parents=True, exist_ok=True)
   178	    hub_repo_name = repo_root.resolve().name or "D3Nexus"
   179	    timestamp = _get_timestamp()
   180	    norm_domain = None
   181	    if domain is not None:
   182	        try:
   183	            norm_domain = validate_domain(domain)
   184	        except ValueError as exc:
   185	            sys.stderr.write(f"ERROR: {exc}\n")
   186	            return 1
   187	    primary_domain = norm_domain if norm_domain else "general"
   188	
   189	    template_vars = {
   190	        "hub_repo": hub_repo_name,
   191	        "domain": primary_domain,
   192	        "timestamp": timestamp,
   193	    }
   194	
   195	    # 2. Render shared-contracts/README.md
   196	    readme_path = shared_contracts_dir / "README.md"
   197	    if not readme_path.exists() or force:
   198	        tmpl = _load_template("hub_readme.md.tmpl")
   199	        atomic_write_text(readme_path, tmpl.substitute(template_vars))
   200	    elif norm_domain:
   201	        _update_readme_table(readme_path, norm_domain)
   202	
   203	    # 3. Create domain subfolder with 3 canonical files
   204	    if norm_domain:
   205	        domain_dir = shared_contracts_dir / norm_domain
   206	        if domain_dir.is_symlink() or os.path.islink(domain_dir):
   207	            sys.stderr.write(
   208	                f"ERROR: Domain directory '{domain_dir}' is an existing symbolic link; "
   209	                "Hub domains must be physical directories.\n"
   210	            )
   211	            return 1
   212	
   213	        shared_contracts_resolved = shared_contracts_dir.resolve()
   214	        if domain_dir.exists() and not domain_dir.resolve().is_relative_to(shared_contracts_resolved):
   215	            sys.stderr.write(
   216	                f"ERROR: Domain directory '{domain_dir}' resolves outside '{shared_contracts_resolved}'.\n"
   217	            )
   218	            return 1
   219	
   220	        domain_dir.mkdir(parents=True, exist_ok=True)
   221	
   222	        canonical_files = (
   223	            ("api_contract.md", "api_contract.md.tmpl"),
   224	            ("architecture_and_flow.md", "architecture_and_flow.md.tmpl"),
   225	            ("gaps_and_rfcs.md", "gaps_and_rfcs.md.tmpl"),
   226	        )
   227	        for filename, tmpl_name in canonical_files:
   228	            target_file = domain_dir / filename
   229	            if not target_file.exists() or force:
   230	                tmpl = _load_template(tmpl_name)
   231	                atomic_write_text(target_file, tmpl.substitute(template_vars))
   232	
   233	    # 4. Install Hub local rule .agents/rules/contract_rules.md
   234	    rules_dir = repo_root / ".agents" / "rules"
   235	    rules_dir.mkdir(parents=True, exist_ok=True)
   236	    contract_rules_path = rules_dir / "contract_rules.md"
   237	    if not contract_rules_path.exists() or force:
   238	        rule_tmpl = _load_template("hub_rule.md.tmpl")
   239	        atomic_write_text(contract_rules_path, rule_tmpl.substitute(template_vars))
   240	
   241	    sys.stdout.write(
   242	        f"SUCCESS: Hub repository initialized at '{shared_contracts_dir}'\n"
   243	        f"SSOT Local Rule: '{contract_rules_path}'\n"
   244	    )
   245	    return 0
   246	
   247	
   248	def cmd_link_satellite(
   249	    hub: Path,
   250	    domain: str,
   251	    satellite_root: Path,
   252	    force: bool = False,
   253	) -> int:
   254	    """Link a satellite repository to a Hub domain contracts directory via relative symlink."""
   255	    try:
   256	        norm_domain = validate_domain(domain)
   257	    except ValueError as exc:
   258	        sys.stderr.write(f"ERROR: {exc}\n")
   259	        return 1
   260	
     1	# API Contract: $domain
     2	
     3	- **Domain**: `$domain`
     4	- **Hub Repository**: `$hub_repo`
     5	- **Version**: `1.0.0`
     6	- **Last Updated**: `$timestamp`
     7	
     8	## 1. Overview and Transports
     9	
    10	This document defines the wire-level API contract for the `$domain` service interface. All communicating services and clients MUST conform strictly to these schemas and invariants.
    11	
    12	- **Primary Transport**: HTTPS REST / SSE
    13	- **Content Type**: `application/json; charset=utf-8`
    14	- **Time Encoding**: ISO-8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`)
    15	
    16	## 2. Authentication and Headers
    17	
    18	All requests across the service boundary MUST include standard authentication headers:
    19	
    20	| Header | Type | Required | Description |
    21	|---|---|---|---|
    22	| `Authorization` | String | Yes (Client) | Bearer token for client authentication |
    23	| `X-Worker-Token` | String | Yes (Worker) | Shared secret token for stateless compute worker tasks |
    24	| `X-Correlation-ID` | String | Yes | UUID tracking distributed request traces |
    25	| `X-Client-Timestamp` | String | No | ISO-8601 timestamp emitted by caller |
    26	
    27	## 3. Endpoints Matrix
    28	
    29	| Method | Endpoint | Auth | Purpose |
    30	|---|---|---|---|
    31	| `POST` | `/api/v1/$domain/tasks/claim` | `X-Worker-Token` | Worker acquires compute lease |
    32	| `POST` | `/api/v1/$domain/tasks/{id}/progress` | `X-Worker-Token` | Worker heartbeats and reports progress |
    33	| `POST` | `/api/v1/$domain/tasks/{id}/complete` | `X-Worker-Token` | Worker submits terminal result payload |
    34	| `GET` | `/api/v1/$domain/status` | Public / Token | Health check and schema capability discovery |
    35	
    36	## 4. Payload Schemas
    37	
    38	### 4.1 Task Claim Response Payload
    39	
    40	```json
    41	{
    42	  "task_id": "tsk_01HXYZ123456",
    43	  "domain": "$domain",
    44	  "lease_duration_ms": 30000,
    45	  "payload": {
    46	    "parameters": {},
    47	    "config": {}
    48	  }
    49	}
    50	```
    51	
    52	### 4.2 Terminal Result Delivery Payload
    53	
    54	```json
    55	{
    56	  "status": "COMPLETED",
    57	  "output_data": {},
    58	  "metrics": {
    59	    "execution_time_ms": 1250,
    60	    "memory_peak_mb": 45
    61	  }
    62	}
    63	```
    64	
    65	## 5. Non-Breaking Schema Guarantees
    66	
    67	1. **Safe Defaults**: All newly introduced request/response fields must be optional or provide explicit fallback defaults.
    68	2. **Permissive Parsing**: Clients and workers MUST ignore unknown keys in JSON payloads.
    69	3. **No Unilateral Renames**: Field names must never be changed without a documented transition phase logged in `gaps_and_rfcs.md`.
    70	
    71	## 6. Error Invariants
    72	
    73	All error responses adhere to the standard envelope:
    74	
    75	```json
    76	{
    77	  "error": {
    78	    "code": "TASK_LEASE_EXPIRED",
    79	    "message": "The compute lease for this task expired prior to completion.",
    80	    "retryable": true,
    81	    "details": {}
    82	  }
    83	}
    84	```
    85	
    86	## 7. Version Changelog
    87	
    88	| Version | Date | Author / Repo | Description |
    89	|---|---|---|---|
    90	| 1.0.0 | $timestamp | $hub_repo | Initial canonical API contract for $domain |
     1	# Architecture and Flow: $domain
     2	
     3	- **Domain**: `$domain`
     4	- **Hub Repository**: `$hub_repo`
     5	- **Version**: `1.0.0`
     6	- **Last Updated**: `$timestamp`
     7	
     8	## 1. System Overview
     9	
    10	This document specifies the architectural topology, pipeline lifecycles, and state machine transitions for the `$domain` service domain.
    11	
    12	```mermaid
    13	flowchart TD
    14	    HUB["Hub Control Plane ($hub_repo)<br/>Database & State Authority"]
    15	    WORKER["Stateless Worker Satellite<br/>(e.g. lyrics-sync)"]
    16	    CLIENT["Client Applications<br/>(e.g. nexus)"]
    17	
    18	    HUB -->|1. Lease Acquisition| WORKER
    19	    WORKER -->|2. Heartbeat & Progress| HUB
    20	    WORKER -->|3. Terminal Delivery| HUB
    21	    CLIENT -->|Query State / SSE| HUB
    22	```
    23	
    24	## 2. Seven Canonical Pipeline Steps
    25	
    26	All compute workloads executed under `$domain` MUST implement the seven canonical lifecycle steps:
    27	
    28	1. **Lease Acquisition**: Worker claims task lease from Hub via authenticated HTTP endpoint.
    29	2. **Input Validation**: Worker verifies input payload schema, preconditions, and parameter sanity.
    30	3. **Scratch Isolation**: Worker allocates dedicated temporary workspace (e.g. `tmp/<task_id>/`).
    31	4. **Core Compute**: Worker executes primary algorithmic or transformation pipeline.
    32	5. **Heartbeat and Progress**: Worker emits periodic progress updates to prevent lease timeout.
    33	6. **Terminal Result Delivery**: Worker submits final artifact or status payload to Hub.
    34	7. **Scratch Teardown**: Worker unconditionally purges local temporary directory in `finally` block.
    35	
    36	## 3. State Machine Transitions
    37	
    38	```mermaid
    39	stateDiagram-v2
    40	    [*] --> Idle
    41	    Idle --> Leased: Claim Task
    42	    Leased --> Executing: Start Pipeline
    43	    Executing --> Executing: Heartbeat (< 5s)
    44	    Executing --> Delivering: Task Complete
    45	    Delivering --> Completed: ACK from Hub
    46	    Executing --> Cancelled: Cancel Signal (< 50ms)
    47	    Executing --> Failed: Unhandled Error
    48	    Completed --> [*]
    49	    Cancelled --> [*]
    50	    Failed --> [*]
    51	```
    52	
    53	## 4. Cancellation Fencing and Resource Cleanup
    54	
    55	- **Latency Guarantee**: When Hub issues a cancellation signal, worker compute MUST abort execution and release resources within **50 milliseconds**.
    56	- **Scratch Purge**: Temporary files, scratch memory, and child subprocesses must be terminated cleanly. No orphan files may persist across runs.
    57	
    58	## 5. Stateless Compute Boundary Discipline
    59	
    60	> [!CRITICAL]
    61	> **Satellite worker nodes operate as strictly stateless compute engines.**
    62	> - Direct database connections (`DATABASE_URL`, PostgreSQL, SQLite) to Hub databases are **STRICTLY PROHIBITED**.
    63	> - All state persistence, task queueing, and lease reconciliation are managed exclusively by the Hub Control Plane.
     1	# Gaps and RFCs Ledger: $domain
     2	
     3	- **Domain**: `$domain`
     4	- **Hub Repository**: `$hub_repo`
     5	- **Version**: `1.0.0`
     6	- **Last Updated**: `$timestamp`
     7	
     8	## 1. Overview and Governance
     9	
    10	This document records architectural gaps, schema change proposals, and Request for Comments (RFCs) for the `$domain` service contracts.
    11	
    12	Cross-repository changes MUST be proposed, reviewed, and approved within this ledger before breaking implementation changes are made in any codebase.
    13	
    14	### Core Principles
    15	- **No Unilateral Drift**: Satellite nodes must never invent ad-hoc fields or diverging schemas.
    16	- **Backward Compatibility**: Every proposal must preserve compatibility with existing consumers.
    17	- **Asynchronous Alignment**: Use this ledger to coordinate between backend, worker, and frontend teams.
    18	
    19	## 2. Active RFC Ledger
    20	
    21	| RFC ID | Title | Proposing Repo | Status | Target Release | Breaking? |
    22	|---|---|---|---|---|---|
    23	| RFC-001 | Initial canonical contract baseline | $hub_repo | Approved | 1.0.0 | No |
    24	
    25	*Status values: `Draft` | `In Review` | `Approved` | `Implemented` | `Superseded` | `Rejected`*
    26	
    27	## 3. RFC Proposal Template
    28	
    29	When proposing a new contract enhancement, append a new section below using this structure:
    30	
    31	```markdown
    32	### RFC-XXX: [Descriptive Title]
    33	
    34	- **Date**: YYYY-MM-DD
    35	- **Author / Repo**: [Name / Repository]
    36	- **Status**: Draft
    37	- **Target Release**: [e.g. 1.1.0]
    38	
    39	#### Problem Statement
    40	Describe the missing capability, contract gap, or payload bottleneck.
    41	
    42	#### Proposed Schema Changes
    43	Detail new endpoints, headers, or JSON payload keys. State explicit defaults.
    44	
    45	#### Backward Compatibility Analysis
    46	Explain why this change will not break existing consumers or satellite nodes.
    47	```

exec
/bin/zsh -lc "cat .devtool/epic/sync_shared_contracts/bdd_scenarios.en.md; sed -n '1,62p' .devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md; nl -ba scripts/verify.sh | tail -110; nl -ba scripts/run_unittest_junit.py | sed -n '1,160p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Sync Shared Contracts BDD Scenarios

## Table of Contents

- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
- [Dimension 3: State Transitions](#dimension-3-state-transitions)
- [Dimension 4: Async and Multi-Repo Concurrency](#dimension-4-async-and-multi-repo-concurrency)
- [Dimension 5: Failures and Storage Resilience](#dimension-5-failures-and-storage-resilience)

## Dimension 1: Happy Paths

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
  And the command exits with code 0

Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
  Then the file .agents/contract_sync.json is created in the Satellite repository with mode "satellite" and domain "lyrics-sync"
  And the recorded sha256 hashes match all 3 canonical files in the Hub
  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0

Scenario: [SYC-HP-03] [Tier C - Integration] Skill Definition and Release Verify Harness Execution
  Given the completed sync-shared-contracts skill directory and scripts/verify.sh registration
  When the engineer runs the verification suite for sync-shared-contracts
  Then skills/sync-shared-contracts/SKILL.md passes frontmatter and link validation
  And all unit and integration tests in test_sync_contracts.py pass with exit code 0
```

## Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
  Given a valid Satellite repository where .agents/contract_sync.json does not exist
  When the engineer invokes sync_contracts.py check --json
  Then the JSON report identifies the domain status as "INITIAL_SYNC"
  And lists all 3 canonical contract files as unsynced baseline deltas
  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided

Scenario: [SYC-EC-02] [Tier A - Unit] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields
  Given a target repository containing source file src/worker_client.ts with route "/api/v1/lyrics-sync/tasks" and "/progress" and field "leaseDurationMs"
  When the heuristic scanner evaluates endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" and "/api/v1/lyrics-sync/status" and payload key "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" and key "lease_duration_ms" are classified as "FOUND_IN_CODE"
  And unimplemented endpoint "/api/v1/lyrics-sync/status" is classified as "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Graceful Fallback When Hub Directory Has No Git History
  Given a Hub directory that was created on disk without a .git repository
  When the engineer invokes sync_contracts.py check or brief
  Then the engine skips git rev-parse and git log without raising a subprocess error
  And computes drift status accurately using sha256 file hashes and contract Version metadata
```

## Dimension 3: State Transitions

```gherkin
Scenario: [SYC-ST-01] [Tier C - Integration] Incremental Drift Detection After Upstream Hub Contract Update
  Given a Satellite repository that previously ran sync_contracts.py ack and is in state "IN_SYNC"
  When the Hub repository updates api_contract.md to version "1.1.0" with a new endpoint POST /api/v1/lyrics-sync/tasks/{id}/cancel and logs RFC-002 in gaps_and_rfcs.md
  And the engineer runs sync_contracts.py check --strict in the Satellite repository
  Then the status transitions from "IN_SYNC" to "DRIFT_DETECTED"
  And the delta report identifies api_contract.md and gaps_and_rfcs.md as modified, surfaces the new cancel endpoint as "MISSING_IN_CODE", and lists RFC-002
  And sync_contracts.py check --strict exits with code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Multi-Domain Watermark Preservation and Explicit RFC Acknowledgement
  Given a Hub repository with domains lyrics-sync and nexus where lyrics-sync is already recorded in .agents/contract_sync.json
  When the engineer invokes sync_contracts.py ack --domain nexus --rfc RFC-005
  Then .agents/contract_sync.json retains the existing "lyrics-sync" entry unchanged
  And records the new "nexus" entry containing "RFC-005" in acknowledged_rfcs
```

## Dimension 4: Async and Multi-Repo Concurrency

```gherkin
Scenario: [SYC-AR-01] [Tier A - Unit] Atomic Watermark File Update Prevents Partial JSON Reads
  Given an existing .agents/contract_sync.json file in the target repository
  When sync_contracts.py ack writes updated synchronization metadata
  Then the engine writes to a temporary file in .agents/ and atomically replaces .agents/contract_sync.json
  And no leftover temporary files remain in .agents/ after completion

Scenario: [SYC-AR-02] [Tier A - Unit] Circular Symlink Loop Protection During Topology Resolution
  Given a repository where shared-contracts is part of a circular symbolic link chain exceeding 10 hops
  When the engineer invokes sync_contracts.py check
  Then symlink traversal halts deterministically at the 10-hop boundary
  And exits with code 1 and an error message reporting a symbolic link loop
```

## Dimension 5: Failures and Storage Resilience

```gherkin
Scenario: [SYC-FR-01] [Tier A - Unit] Refusing Execution When Shared Contracts Directory Is Missing
  Given a target repository that has no shared-contracts directory or symlink
  When the engineer invokes sync_contracts.py check, brief, or ack
  Then the command aborts with exit code 1
  And prints an error instructing the user to initialize or link contracts with setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Refusing Execution on Dangling Symlink or Missing Canonical Files
  Given a Satellite repository whose shared-contracts symlink points to a non-existent Hub path or a domain missing architecture_and_flow.md
  When the engineer invokes sync_contracts.py check
  Then the command aborts with exit code 1
  And prints a diagnostic message naming the broken target or missing canonical file

Scenario: [SYC-FR-03] [Tier A - Unit] Resilience Against Corrupted Watermark JSON File
  Given a target repository where .agents/contract_sync.json contains truncated invalid JSON "{corrupt"
  When the engineer runs sync_contracts.py check followed by sync_contracts.py ack
  Then sync_contracts.py check logs a warning about invalid JSON and falls back to "INITIAL_SYNC" without crashing
  And sync_contracts.py ack cleanly overwrites .agents/contract_sync.json with valid schema_version 1 JSON
```

---
id: "task_3_watermark_ack_and_brief_cli"
status: "todo"
priority: "high"
assignee: null
epic: "sync_shared_contracts"
dueDate: null
created: "2026-10-30T11:58:00Z"
modified: "2026-10-30T11:58:00Z"
completedAt: null
labels: ["contracts", "watermark", "cli"]
order: "a3"
---

# Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands

Epic: [sync_shared_contracts](sync_shared_contracts.en.md)

## Requirement Analysis

Implement the `ack` subcommand, incremental drift detection (`IN_SYNC` vs `DRIFT_DETECTED`), multi-domain watermark preservation, atomic JSON writing, and corrupted watermark recovery in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
1. **Watermark Ack Command (`[SYC-HP-02]`, `[SYC-ST-02]`, `[SYC-AR-01]`)**:
   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, query the Hub git commit SHA, and collect acknowledged endpoints and RFC IDs (including `--rfc <RFC-ID>` arguments).
   - Write `.agents/contract_sync.json` atomically using a temporary file in `.agents/` and `os.replace()`, preserving existing entries for other domains (`[SYC-ST-02]`, `[SYC-AR-01]`).
2. **Incremental Drift Detection (`[SYC-ST-01]`)**:
   - After `ack` is run, `check --strict` must report `IN_SYNC` and exit `0` (`[SYC-HP-02]`).
   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, `check` must transition to `DRIFT_DETECTED`, surface modified files, new endpoints, and new RFCs, and exit `1` when `--strict` is passed (`[SYC-ST-01]`).
3. **Corrupted Watermark Recovery (`[SYC-FR-03]`)**:
   - If `.agents/contract_sync.json` contains malformed JSON, `check` logs a warning to stderr and falls back to `INITIAL_SYNC` without crashing, while `ack` overwrites it with valid `schema_version: 1` JSON.

## Files

Allowed files:
- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)

Read-only context:
- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

## Design Rationale

- Atomic file replacement (`tempfile.NamedTemporaryFile` in `.agents/` + `os.replace`) guarantees concurrent readers never observe truncated JSON.
- Preserving sibling domain keys in `.agents/contract_sync.json` allows a multi-domain Hub or multi-service consumer to track each domain independently.
- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `sync_contracts.py` (`cmd_ack`, `cmd_brief`, `load_sync_state`, `save_sync_state_atomic`, `evaluate_domain_drift`) and `test_sync_contracts.py`.
- **Downstream Callers**: Task 4 (`SKILL.md` workflow and `scripts/verify.sh`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: 100% coverage of `ack`, `brief --output`, drift transitions, and malformed JSON recovery.

## BDD Scenarios and Acceptance Criteria

### BDD SCENARIOS

Covers: SYC-HP-02, SYC-ST-01, SYC-ST-02, SYC-AR-01, SYC-FR-03

```gherkin
Scenario: [SYC-HP-02] [Tier C - Integration] End-to-End Satellite Synchronization and Strict Check Pass
  Given a Satellite repository linked via relative symlink shared-contracts to ../Hub/shared-contracts/lyrics-sync
   180	    return not any(part.startswith(".") for part in p.parts)
   181	
   182	supporting = [p for p in root.glob("skills/*/**/*") if p.is_file() and is_skill_content(p)]
   183	corpus = [p for p in root.rglob("*")
   184	          if p.is_file() and ".git/" not in str(p) and "__pycache__" not in p.parts
   185	          and p.suffix in {".md", ".py", ".sh", ".json", ".yaml", ".yml", ""}]
   186	texts = {}
   187	for c in corpus:
   188	    try:
   189	        texts[c] = c.read_text(errors="ignore")
   190	    except OSError:
   191	        pass
   192	bad = 0
   193	for f in sorted(supporting):
   194	    name = f.name
   195	    if any(other != f and name in body for other, body in texts.items()):
   196	        continue
   197	    print(f"  FAIL {f} is referenced by nothing")
   198	    bad = 1
   199	print(f"  checked {len(supporting)} supporting files")
   200	sys.exit(bad)
   201	PY
   202	
   203	note "== 9. The dev-* rename is complete =="
   204	# The old names must survive only where they are history: archived epic records under .devtool/
   205	# and the CHANGELOG entries that describe the rename itself.
   206	# Driven from `git ls-files`, not a filesystem walk: a walk also reads gitignored scratch such as
   207	# .superpowers/, which exists in a normal checkout and not in a worktree — so the same tree passed
   208	# in one and failed in the other. The repository's own file list is the only deterministic input.
   209	# This file is excluded because the check's pattern necessarily contains the names it looks for.
   210	if hits=$(git ls-files \
   211	          | grep -v -e '^\.devtool/' -e '^CHANGELOG\.md$' -e '^scripts/verify\.sh$' \
   212	          | tr '\n' '\0' \
   213	          | xargs -0 grep -n "epic-lifecycle\|epic-designer\|epic-implementation" 2>/dev/null) \
   214	   && [ -n "$hits" ]; then
   215	  printf '%s\n' "$hits" | head -5
   216	  fail "live files still reference the pre-rename skill names"
   217	else
   218	  note "  ok   no live file names epic-lifecycle, epic-designer or epic-implementation"
   219	fi
   220	
   221	echo
   222	note "== 10. Orchestrators route to a variant, never the router =="
   223	# Step 9's repo-wide sweep cannot be reused for this rename. `brainstorming` is an ordinary English
   224	# word: it appears legitimately as "during brainstorming" in writing-plans, "not a full brainstorming
   225	# dialogue" in dev-designer, as a deliberately preserved pre-1.2.0 path in
   226	# doc_quality_check/references/document-reviewer-prompt.md, and in this file's own comments. A bare
   227	# sweep would fail on all four. Scope it instead to the two orchestrators, and only to the two forms
   228	# that actually denote the skill rather than the activity.
   229	#
   230	# What this guards: `brainstorming` is a router that resolves an ambiguous entry. A lifecycle stage
   231	# naming it has not routed — it has moved the ambiguity one hop downstream. The precedent is real:
   232	# epic-lifecycle never contained the word "invoke", so agents read a stage description and did that
   233	# stage's work themselves, skipping the gate the stage owned.
   234	if hits=$(git ls-files 'skills/dev-lifecycle/*' 'skills/doc-lifecycle/*' \
   235	          | tr '\n' '\0' \
   236	          | xargs -0 grep -n 'd3nexus:brainstorming\|`brainstorming`' 2>/dev/null) \
   237	   && [ -n "$hits" ]; then
   238	  printf '%s\n' "$hits" | head -5
   239	  fail "an orchestrator stage names the brainstorming router instead of a variant"
   240	else
   241	  note "  ok   both orchestrators name a concrete brainstorming variant"
   242	fi
   243	
   244	echo
   245	note "== 11. Lifecycle document contracts are enforced =="
   246	python3 -m unittest skills/doc_quality_check/resources/scripts/test_check_document.py || FAILED=1
   247	python3 scripts/test_lifecycle_document_contract.py || FAILED=1
   248	python3 -m unittest scripts/test_lifecycle_signals.py || FAILED=1
   249	python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py || FAILED=1
   250	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py || FAILED=1
   251	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py || FAILED=1
   252	python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py || FAILED=1
   253	python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py || FAILED=1
   254	python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py || FAILED=1
   255	python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py || FAILED=1
   256	python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py || FAILED=1
   257	python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py || FAILED=1
   258	python3 -m unittest scripts/test_run_unittest_junit.py || FAILED=1
   259	python3 -m unittest scripts/test_verifiable_handoff_text.py || FAILED=1
   260	python3 -m unittest scripts/test_verifiable_handoff.py || FAILED=1
   261	
   262	echo
   263	note "== 12. Branch integration script behaves =="
   264	python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py || FAILED=1
   265	
   266	echo
   267	note "== 13. Quality provider contracts, schemas, aggregation, and platform capabilities are enforced =="
   268	python3 -m unittest skills/quality_check/resources/scripts/test_validate_quality_contract.py || FAILED=1
   269	python3 -m unittest skills/quality_check/resources/scripts/test_aggregate_quality_results.py || FAILED=1
   270	python3 -m unittest skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py || FAILED=1
   271	python3 -m unittest skills/python-quality-check/resources/scripts/test_validate_python_quality.py || FAILED=1
   272	python3 -m unittest skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py || FAILED=1
   273	python3 -m unittest skills/android-quality-check/resources/scripts/test_validate_android_quality.py || FAILED=1
   274	python3 -m unittest skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py || FAILED=1
   275	python3 -m unittest skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py || FAILED=1
   276	python3 -m unittest skills/quality_check/resources/scripts/test_quality_provider_acceptance.py || FAILED=1
   277	
   278	echo
   279	note "== 14. Shared contracts CLI engine is enforced =="
   280	python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py || FAILED=1
   281	
   282	echo
   283	if [ "$FAILED" -eq 0 ]; then
   284	  echo "PASS — safe to publish"
   285	else
   286	  echo "FAILED — fix the above before publishing"
   287	fi
   288	exit "$FAILED"
   289	
     1	#!/usr/bin/env python3
     2	"""Run unittest files and write a JUnit XML report.
     3	
     4	Usage:
     5	  run_unittest_junit.py --junitxml <path> <test file> [<test file> ...]
     6	
     7	Exit codes: 0 every test and subtest passed or was skipped; 1 otherwise.
     8	"""
     9	from __future__ import annotations
    10	
    11	import argparse
    12	import importlib.util
    13	import sys
    14	import time
    15	import traceback
    16	import unittest
    17	import xml.etree.ElementTree as ET
    18	from pathlib import Path
    19	
    20	
    21	class RecordingResult(unittest.TextTestResult):
    22	    """Text result that also keeps each test's outcome and duration."""
    23	
    24	    def __init__(self, *args, **kwargs) -> None:
    25	        super().__init__(*args, **kwargs)
    26	        self.records: list[dict] = []
    27	        self._started: dict[str, float] = {}
    28	        self._failed_subtests: dict[str, list[tuple[str, str]]] = {}
    29	
    30	    def startTest(self, test) -> None:
    31	        self._started[test.id()] = time.monotonic()
    32	        super().startTest(test)
    33	
    34	    def _record(self, test, kind: str | None, detail: str = "") -> None:
    35	        elapsed = time.monotonic() - self._started.pop(test.id(), time.monotonic())
    36	        self.records.append({"test": test, "kind": kind, "detail": detail, "time": elapsed})
    37	
    38	    def addSuccess(self, test) -> None:
    39	        super().addSuccess(test)
    40	        self._record(test, None)
    41	
    42	    def addFailure(self, test, err) -> None:
    43	        super().addFailure(test, err)
    44	        self._record(test, "failure", self._exc_info_to_string(err, test))
    45	
    46	    def addError(self, test, err) -> None:
    47	        super().addError(test, err)
    48	        self._record(test, "error", self._exc_info_to_string(err, test))
    49	
    50	    def addSkip(self, test, reason) -> None:
    51	        super().addSkip(test, reason)
    52	        self._record(test, "skipped", reason)
    53	
    54	    def addExpectedFailure(self, test, err) -> None:
    55	        super().addExpectedFailure(test, err)
    56	        self._record(test, None)
    57	
    58	    def addUnexpectedSuccess(self, test) -> None:
    59	        super().addUnexpectedSuccess(test)
    60	        self._record(test, "failure", "unexpected success")
    61	
    62	    def addSubTest(self, test, subtest, err) -> None:
    63	        super().addSubTest(test, subtest, err)
    64	        if err is not None:
    65	            kind = "failure" if issubclass(err[0], test.failureException) else "error"
    66	            detail = f"{subtest}\n{self._exc_info_to_string(err, test)}"
    67	            self._failed_subtests.setdefault(test.id(), []).append((kind, detail))
    68	
    69	    def stopTest(self, test) -> None:
    70	        """A test whose subtest failed gets no other outcome from unittest; record it under the test's own name."""
    71	        failed = self._failed_subtests.pop(test.id(), [])
    72	        if failed and test.id() in self._started:
    73	            kind = "error" if any(k == "error" for k, _ in failed) else "failure"
    74	            self._record(test, kind, "\n".join(detail for _, detail in failed))
    75	        super().stopTest(test)
    76	
    77	
    78	def load_module(path: Path, index: int):
    79	    sys.path.insert(0, str(path.parent))
    80	    name = path.stem if path.stem not in sys.modules else f"{path.stem}_{index}"
    81	    spec = importlib.util.spec_from_file_location(name, path)
    82	    module = importlib.util.module_from_spec(spec)
    83	    sys.modules[name] = module
    84	    spec.loader.exec_module(module)
    85	    return module
    86	
    87	
    88	def suite_element(path: Path, index: int) -> tuple[ET.Element, bool]:
    89	    """Run one file; return its <testsuite> and whether everything passed."""
    90	    suite = ET.Element("testsuite", name=path.stem)
    91	    try:
    92	        module = load_module(path, index)
    93	        loaded = unittest.defaultTestLoader.loadTestsFromModule(module)
    94	    except BaseException:
    95	        case = ET.SubElement(suite, "testcase", classname=path.stem, name="import", time="0")
    96	        ET.SubElement(case, "error", message="import failed").text = traceback.format_exc()
    97	        suite.set("tests", "1"), suite.set("failures", "0"), suite.set("errors", "1"), suite.set("skipped", "0")
    98	        return suite, False
    99	    runner = unittest.TextTestRunner(stream=sys.stderr, resultclass=RecordingResult, verbosity=1)
   100	    result = runner.run(loaded)
   101	    counts = {"failure": 0, "error": 0, "skipped": 0}
   102	    for record in result.records:
   103	        test = record["test"]
   104	        method = getattr(test, "_testMethodName", None)
   105	        classname = f"{type(test).__module__}.{type(test).__name__}" if method else path.stem
   106	        case = ET.SubElement(suite, "testcase", classname=classname,
   107	                             name=method or test.id(), time=f"{record['time']:.6f}")
   108	        if record["kind"]:
   109	            counts[record["kind"]] += 1
   110	            ET.SubElement(case, record["kind"], message=record["detail"].splitlines()[-1:][0]
   111	                          if record["detail"] else "").text = record["detail"]
   112	    suite.set("tests", str(len(result.records)))
   113	    suite.set("failures", str(counts["failure"]))
   114	    suite.set("errors", str(counts["error"]))
   115	    suite.set("skipped", str(counts["skipped"]))
   116	    return suite, result.wasSuccessful()
   117	
   118	
   119	def main(argv: list[str] | None = None) -> int:
   120	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   121	    parser.add_argument("--junitxml", required=True, type=Path)
   122	    parser.add_argument("files", nargs="+", type=Path)
   123	    args = parser.parse_args(argv)
   124	    root = ET.Element("testsuites")
   125	    passed = True
   126	    for index, path in enumerate(args.files):
   127	        suite, ok = suite_element(path.resolve(), index)
   128	        root.append(suite)
   129	        passed = passed and ok
   130	    args.junitxml.parent.mkdir(parents=True, exist_ok=True)
   131	    ET.indent(root)
   132	    ET.ElementTree(root).write(args.junitxml, encoding="utf-8", xml_declaration=True)
   133	    return 0 if passed else 1
   134	
   135	
   136	if __name__ == "__main__":
   137	    sys.exit(main())

exec
/bin/zsh -lc "ls -ld ../D3Nexus/shared-contracts ../lyrics-sync/shared-contracts ../nexus/shared-contracts; rg --files ../D3Nexus/shared-contracts; rg -n 'worktree|symlink|Review Choice|Gate 4|ack' skills/dev-implementation/SKILL.md skills/dev-lifecycle/SKILL.md skills/using-git-worktrees/SKILL.md; nl -ba /Users/danhdueexoictif/antigravity_homes/duedd/.codex/memories/MEMORY.md | sed -n '26,43p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
drwxr-xr-x@ 5 danhdueexoictif  staff  160 Oct 29 18:22 ../D3Nexus/shared-contracts
lrwxr-xr-x@ 1 danhdueexoictif  staff   71 Oct 29 18:18 ../lyrics-sync/shared-contracts -> /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync
lrwxr-xr-x@ 1 danhdueexoictif  staff   33 Oct 29 20:12 ../nexus/shared-contracts -> ../D3Nexus/shared-contracts/nexus
../D3Nexus/shared-contracts/nexus/architecture_and_flow.md
../D3Nexus/shared-contracts/nexus/api_contract.md
../D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md
../D3Nexus/shared-contracts/README.md
../D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md
../D3Nexus/shared-contracts/lyrics-sync/api_contract.md
../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md
skills/using-git-worktrees/SKILL.md:2:name: using-git-worktrees
skills/using-git-worktrees/SKILL.md:3:description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an isolated workspace exists via native tools or git worktree fallback
skills/using-git-worktrees/SKILL.md:10:Ensure work happens in an isolated workspace. Prefer your platform's native worktree tools. Fall back to manual git worktrees only when no native tool is available.
skills/using-git-worktrees/SKILL.md:12:**Core principle:** Detect existing isolation first. Then use native tools. Then fall back to git. Never fight the harness.
skills/using-git-worktrees/SKILL.md:14:**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."
skills/using-git-worktrees/SKILL.md:26:**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:
skills/using-git-worktrees/SKILL.md:29:# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
skills/using-git-worktrees/SKILL.md:33:**If `GIT_DIR != GIT_COMMON` (and not a submodule):** You are already in a linked worktree. Skip to Step 2 (Project Setup). Do NOT create another worktree.
skills/using-git-worktrees/SKILL.md:41:Has the user already indicated their worktree preference in your instructions? If not, ask for consent before creating a worktree:
skills/using-git-worktrees/SKILL.md:43:> "Would you like me to set up an isolated worktree? It protects your current branch from changes."
skills/using-git-worktrees/SKILL.md:53:The user has asked for an isolated workspace (Step 0 consent). Do you already have a way to create a worktree? It might be a tool with a name like `EnterWorktree`, `WorktreeCreate`, a `/worktree` command, or a `--worktree` flag. If you do, use it and skip to Step 2.
skills/using-git-worktrees/SKILL.md:55:Native tools handle directory placement, branch creation, and cleanup automatically. Using `git worktree add` when you have a native tool creates phantom state your harness can't see or manage.
skills/using-git-worktrees/SKILL.md:57:Only proceed to Step 1b if you have no native worktree tool available.
skills/using-git-worktrees/SKILL.md:59:### 1b. Git Worktree Fallback
skills/using-git-worktrees/SKILL.md:61:**Only use this if Step 1a does not apply** — you have no native worktree tool available. Create a worktree manually using git.
skills/using-git-worktrees/SKILL.md:67:1. **Check your instructions for a declared worktree directory preference.** If the user has already specified one, use it without asking.
skills/using-git-worktrees/SKILL.md:69:2. **Check for an existing project-local worktree directory:**
skills/using-git-worktrees/SKILL.md:71:   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
skills/using-git-worktrees/SKILL.md:72:   ls -d worktrees 2>/dev/null      # Alternative
skills/using-git-worktrees/SKILL.md:74:   If found, use it. If both exist, `.worktrees` wins.
skills/using-git-worktrees/SKILL.md:76:3. **If there is no other guidance available**, default to `.worktrees/` at the project root.
skills/using-git-worktrees/SKILL.md:80:**MUST verify directory is ignored before creating worktree:**
skills/using-git-worktrees/SKILL.md:83:git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
skills/using-git-worktrees/SKILL.md:88:**Why critical:** Prevents accidentally committing worktree contents to repository.
skills/using-git-worktrees/SKILL.md:96:git worktree add "$path" -b "$BRANCH_NAME"
skills/using-git-worktrees/SKILL.md:100:**Sandbox fallback:** If `git worktree add` fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.
skills/using-git-worktrees/SKILL.md:108:if [ -f package.json ]; then npm install; fi
skills/using-git-worktrees/SKILL.md:146:| Already in linked worktree | Skip creation (Step 0) |
skills/using-git-worktrees/SKILL.md:148:| Native worktree tool available | Use it (Step 1a) |
skills/using-git-worktrees/SKILL.md:149:| No native tool | Git worktree fallback (Step 1b) |
skills/using-git-worktrees/SKILL.md:150:| `.worktrees/` exists | Use it (verify ignored) |
skills/using-git-worktrees/SKILL.md:151:| `worktrees/` exists | Use it (verify ignored) |
skills/using-git-worktrees/SKILL.md:152:| Both exist | Use `.worktrees/` |
skills/using-git-worktrees/SKILL.md:153:| Neither exists | Check instruction file, then default `.worktrees/` |
skills/using-git-worktrees/SKILL.md:155:| Permission error on create | Sandbox fallback, work in place |
skills/using-git-worktrees/SKILL.md:157:| No package.json/Cargo.toml | Skip dependency install |
skills/using-git-worktrees/SKILL.md:163:| "I'm obviously not in a worktree — no need to check" | Run Step 0. Harness-created isolation and submodules both fool eyeballing; the detection commands settle it. |
skills/using-git-worktrees/SKILL.md:164:| "`git worktree add` is quicker than hunting for a native tool" | A native tool (e.g. `EnterWorktree`) owns placement, branching, and cleanup. Bypassing it is the #1 mistake — it creates phantom state your harness can't see or manage. |
skills/using-git-worktrees/SKILL.md:165:| "The worktree directory is surely ignored already" | Run `git check-ignore`. An unignored worktree directory commits the whole tree into the repo. |
skills/using-git-worktrees/SKILL.md:166:| "Any directory name works" | Explicit instructions beat an existing project-local directory, which beats the `.worktrees/` default. |
skills/dev-lifecycle/SKILL.md:26:2. **Stage 2 (Architecture & Tasks)**: `dev-designer` -> Gate 2 approval -> Handoff Choice (Package or Continue).
skills/dev-lifecycle/SKILL.md:27:3. **Stage 3 (Isolated Execution)**: `dev-implementation` -> Gate 3 (order confirmation) -> Task-by-task TDD in worktree -> Gate 4 machine acceptance -> Review Choice loop (Finish, Cross-model review or Local model review) -> Gate 5 Kanban review.
skills/dev-lifecycle/SKILL.md:37:Do NOT skip or auto-decide the Review Choice after Gate 4 passes.
skills/dev-lifecycle/SKILL.md:38:You MUST present the choice between "Finish", "Cross-model review" and "Local model review" on every Gate 4 PASS.
skills/dev-lifecycle/SKILL.md:39:Cross-model review returns to a full Gate 4 run, which presents the choice again until the developer selects Finish. Local model review does the same.
skills/dev-lifecycle/SKILL.md:58:Every gate is a **human approval** except Gate 4, which is a machine verdict. Never cross one on your own judgement.
skills/dev-lifecycle/SKILL.md:64:| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint, or Gate 3 (resume) in its Resume Procedure | confirmed order + bootstrapped worktree |
skills/dev-lifecycle/SKILL.md:72:A request to implement, continue or resume an epic whose `.devtool/epic/<epic_dir>/` already holds `task_*.md` files is past Gate 2 — whether the epic was packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Announce "Gates 1 and 2 already passed; resuming at Stage 3", invoke `dev-implementation` with that epic name, and let its Entry-Point Detection choose where to start. Never redo Stage 1 or Stage 2 for it. New requirements for such an epic are not a resume: they go to dev-designer's Updating an Existing Epic.
skills/dev-lifecycle/SKILL.md:97:> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop.
skills/dev-lifecycle/SKILL.md:101:**Package** → run packaging procedure:
skills/dev-lifecycle/SKILL.md:105:4. Mark the epic packaged, then confirm both overview variants changed:
skills/dev-lifecycle/SKILL.md:107:   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
skills/dev-lifecycle/SKILL.md:108:   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
skills/dev-lifecycle/SKILL.md:111:   Two matching lines are required; with fewer, set the Status line by hand in both variants. If the Status read `Queued (backlog) — behind <epic>` before packaging, run the script with `"Packaged (queued behind <epic>)"` instead and copy that line into Open Notes; the `grep` still matches.
skills/dev-lifecycle/SKILL.md:112:5. Commit if `auto_commit: true`: `git commit -m "[<EPIC_NAME>] Package epic for handoff"`.
skills/dev-lifecycle/SKILL.md:115:8. Present **Principal Review Choice** — follow [references/principal-review.md](references/principal-review.md). When Option 2 ("Principal Review") is selected, invoke `d3nexus:principal-review`.
skills/dev-lifecycle/SKILL.md:119:**Entry:** Gate 2 passed, HLD and `task_*.md` exist, and Continue chosen (or resuming packaged/interrupted epic).
skills/dev-lifecycle/SKILL.md:120:**Exit (Gate 5):** Gate 4 is 🟢 LGTM and user approves Kanban completion.
skills/dev-lifecycle/SKILL.md:122:- **Gate 3 (Execution Order)**: Present computed execution order and get user confirmation **before** creating worktrees or dispatching subagents.
skills/dev-lifecycle/SKILL.md:123:- **Execution**: One worktree, one task at a time, one commit per task, docs kept truthful. Rebase and integrate with `develop` after each task.
skills/dev-lifecycle/SKILL.md:125:**Review Choice loop**:
skills/dev-lifecycle/SKILL.md:126:After all tasks are complete, run Gate 4. On every PASS, present Review Choice:
skills/dev-lifecycle/SKILL.md:128:- **Option 2: Cross-model review** -> Invoke `d3nexus:cross-model-review` via `run_external_review.py run` (prompting for Claude CLI, Codex CLI, or Antigravity CLI). Record round in `.devtool/epic/<epic_dir>/review_results.md`. Check unresolved findings with `run_external_review.py check --epic-dir <epic_dir>`. Any dismissed finding requires explicit developer instruction. Return to a full Gate 4 run on the new commit.
skills/dev-lifecycle/SKILL.md:129:- **Option 3: Local model review** -> Invoke `d3nexus:cross-model-review` (run `ollama list`, ask which model, then invoke `run_external_review.py run --cli ollama --model <model>`). A model served by the local Ollama reviews each task commit, then the epic, and one round is recorded in the same `review_results.md` under the same `check` rules. Return to a full Gate 4 run on the new commit.
skills/dev-lifecycle/SKILL.md:133:When an epic's tasks were executed by a fast executor model (e.g. Gemini Flash, Claude Haiku, GPT-4o-mini), the agent presents a strong recommendation in the Review Choice prompt:
skills/dev-lifecycle/SKILL.md:136:The invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**. Loop repeats until developer selects Finish.
skills/dev-lifecycle/SKILL.md:140:> **Mandatory Review Choice loop**: Once every task is `done`, run Gate 4. On PASS, the agent MUST stop calling tools and present Review Choice. Silently skipping the choice or assuming Finish is strictly prohibited. Cross-model review and Local model review always return to a full Gate 4 run before Review Choice is presented again.
skills/dev-lifecycle/SKILL.md:142:**Gate 4 Machine Acceptance Criteria:**
skills/dev-lifecycle/SKILL.md:143:Gate 4 grants `🟢 LGTM` only when:
skills/dev-lifecycle/SKILL.md:148:Gate 4 conditions:
skills/dev-lifecycle/SKILL.md:152:4. **Candidate Immutability**: A 🟢 verdict belongs strictly to the tested SHA. If commits change after Gate 4, a fresh traceability check and epic quality run are required before landing.
skills/dev-lifecycle/SKILL.md:154:On failure, route back to `dev-implementation` with defect report; land fixes as `[EPIC_NAME] Fix <what>` commits and re-run Gate 4 in full.
skills/dev-lifecycle/SKILL.md:157:Completed tasks remain in `.devtool/features/done/`. Stop calling tools and present final report for visual inspection. On user approval, advance to Stage 4. Any requested adjustments land as Fix commits and return to full Gate 4.
skills/dev-lifecycle/SKILL.md:172:| 5 | Stage 3 — apply user adjustments as Fix commits, re-run Gate 4 in full |
skills/dev-lifecycle/SKILL.md:182:- Creating a worktree or dispatching subagents before Gate 3. Recreating the worktree of an existing epic branch (dev-implementation Resume Procedure) is not creating one.
skills/dev-lifecycle/SKILL.md:184:- Packaging an epic without preflight, or pushing without explicit permission.
skills/dev-lifecycle/SKILL.md:185:- Treating packaged Gate 3 as passed.
skills/dev-lifecycle/SKILL.md:187:- Merging to `develop` without Gate 4 🟢.
skills/dev-lifecycle/SKILL.md:188:- Granting Gate 4 without a passing traceability check on the same SHA, or without a passing `audit_epic.py`.
skills/dev-lifecycle/SKILL.md:191:- Skipping Review Choice after Gate 4 PASS or auto-selecting Finish.
skills/dev-lifecycle/SKILL.md:192:- Reusing a Gate 4 PASS after review rounds, finding decisions, or Fix commits change SHA.
skills/dev-implementation/SKILL.md:3:description: Use when an epic already has an approved HLD and Kanban task files (`.devtool/epic/<epic_dir>/` + `.devtool/features/task_*.md`) and you need to actually execute those tasks against the codebase, in the right order, inside an isolated worktree across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects.
skills/dev-implementation/SKILL.md:10:Runs an already-approved epic's Kanban tasks end-to-end: reload the epic's own docs for context, detect the platform (Flutter, Android Native, iOS Native, Web, Python, or Rust), compute a dependency-safe execution order, bootstrap one worktree that can actually build this project, then drive each task sequentially through `d3nexus:subagent-driven-development` with exactly one commit per task.
skills/dev-implementation/SKILL.md:12:**Core principle:** One worktree, one task at a time, one commit per task, docs stay truthful.
skills/dev-implementation/SKILL.md:22:| `<epic_dir>` | The epic's directory name on disk | `.devtool/epic/<epic_dir>/<epic_dir>.en.md`, the worktree directory name | `logging_refactor` (underscores) |
skills/dev-implementation/SKILL.md:31:- You are resuming an epic — packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Invoke this skill with the epic's directory name or slug; Entry-Point Detection in Phase 0 decides where to start.
skills/dev-implementation/SKILL.md:50:   - `.devtool/epic/<epic_dir>/handoff.md`, when present — the packaging record. Use its Open Notes as context; it is never updated after packaging.
skills/dev-implementation/SKILL.md:61:**Symlink & Multi-Repo Boundary Invariant**: In Satellite repositories where `shared-contracts/` is a symbolic link (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`), the implementer MUST treat `shared-contracts/` as strictly read-only for git operations. Never attempt to stage files through the symlink (`git add shared-contracts/...`), which triggers `fatal: pathspec is beyond a symbolic link`. If an upstream contract modification is needed, stop and report `BLOCKED` with an Upstream Contract Handoff Summary rather than attempting cross-repo edits.
skills/dev-implementation/SKILL.md:82:test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
skills/dev-implementation/SKILL.md:87:git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
skills/dev-implementation/SKILL.md:92:`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."
skills/dev-implementation/SKILL.md:97:| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is developer's call |
skills/dev-implementation/SKILL.md:98:| 3 | No epic branch locally or on remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then new worktree |
skills/dev-implementation/SKILL.md:99:| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
skills/dev-implementation/SKILL.md:101:| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS presents Review Choice |
skills/dev-implementation/SKILL.md:106:For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.
skills/dev-implementation/SKILL.md:108:1. Row 4 only: recreate worktree from existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. For rows 4 and 5, check bootstrap with Phase 1 step 5's platform checks and re-run if needed.
skills/dev-implementation/SKILL.md:109:2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or diverged base, is handled per Phase 2 step 7 before anything else.
skills/dev-implementation/SKILL.md:110:3. Find the interrupted task: one at `in-progress` or `review`. If worktree has uncommitted changes, collect `git status --short`.
skills/dev-implementation/SKILL.md:112:5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
skills/dev-implementation/SKILL.md:132:   If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.
skills/dev-implementation/SKILL.md:140:   Do not create worktree until both checks exit 0 and developer has confirmed the order.
skills/dev-implementation/SKILL.md:144:4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
skills/dev-implementation/SKILL.md:147:   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
skills/dev-implementation/SKILL.md:150:   If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
skills/dev-implementation/SKILL.md:151:5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
skills/dev-implementation/SKILL.md:152:6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
skills/dev-implementation/SKILL.md:178:   2. **Principal Engineer (TDD Master Persona — Tier A)**: Implements unit logic, state emissions, and hermetic tests using platform tools (Dart/Flutter, Kotlin/Compose, Swift/SwiftUI, TypeScript/Web, Python/pytest, Rust/cargo). Enforces RED failing test first -> minimal GREEN code -> REFACTOR formatting, linter, strict types. In Satellite Mode, adapts consumer models, DTOs, and adapters within satellite-internal files without staging symlinked paths.
skills/dev-implementation/SKILL.md:221:7. **Integrate with develop.** Run in orchestrator from epic worktree after step 5 commit:
skills/dev-implementation/SKILL.md:248:Once every task is `done`, a fix is never made by reopening a task. Make it as its own commit on the epic branch, titled `[EPIC_NAME] Fix <what>`. Do not move a done task back, and do not re-record its evidence. `audit_epic.py` lists these commits under "Commits outside tasks". After fixes, run Phase 4 again in full on the new SHA.
skills/dev-implementation/SKILL.md:259:2. **Gate 4 audit**:
skills/dev-implementation/SKILL.md:278:   - Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.
skills/dev-implementation/SKILL.md:280:#### Semantic Test Integrity Governance (Gate 4 Rules)
skills/dev-implementation/SKILL.md:282:Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
skills/dev-implementation/SKILL.md:283:1. **No Reconstructed Logic**: Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses. If a test reconstructs production logic instead of invoking production symbols, the review reports FAIL.
skills/dev-implementation/SKILL.md:286:*(Note: These are Gate 4 semantic integrity requirements evaluated by specialist providers and audits; no universal cross-language mechanical coverage claim is made.)*
skills/dev-implementation/SKILL.md:288:### Review Choice — after every Gate 4 PASS
skills/dev-implementation/SKILL.md:291:You MUST NOT skip or auto-decide Review Choice after Gate 4 passes.
skills/dev-implementation/SKILL.md:293:Cross-model review and Local model review must return to Phase 4 in full; only the next Gate 4 PASS may present Review Choice again.
skills/dev-implementation/SKILL.md:296:The loop invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**.
skills/dev-implementation/SKILL.md:307:> Gate 4 is 🟢 LGTM for `<candidate_sha>`. How do you want to proceed?
skills/dev-implementation/SKILL.md:313:Option 1 goes to Phase 4.1 / Gate 5. Option 2 invokes `d3nexus:cross-model-review` in epic worktree with clean tree:
skills/dev-implementation/SKILL.md:318:Commit `review_results.md` after every round (`[EPIC_NAME] Record cross-model review round N`). After every round of option 2 or 3, run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, fill it as [review-triage.md](references/review-triage.md) says, present it, and wait for the developer's decisions before any Fix commit or Decision cell. Then make the Fix commits, record the decisions, commit, and rerun Phase 4 / Gate 4 in full.
skills/dev-implementation/SKILL.md:320:Option 3 invokes `d3nexus:cross-model-review` for local models (run `ollama list` first and ask the developer which model to use; never pick it). Then, in the epic worktree with a clean tree:
skills/dev-implementation/SKILL.md:329:Once `@quality_check` reports 🟢 LGTM, all tasks completed, and developer selects **Finish** at Review Choice:
skills/dev-implementation/SKILL.md:331:2. **Present Executive Summary**: Output summary containing epic slug, worktree path, completed tasks, `@quality_check` verdict, BDD matrix, and audit disclosure sections (Evidence, Protected paths, Commits outside tasks, Gate 5 items).
skills/dev-implementation/SKILL.md:351:- **d3nexus:using-git-worktrees** — creates epic worktree (`develop` as base ref).
    26	## User preferences
    27	
    28	- When requesting a principal review, the user required a “strictly read-only review” with exact source file/line grounding, artefact-specific actionable findings, and an exact final verdict block -> do not edit files or Git state; cite concrete locations for each source claim. [Task 1][Task 2]
    29	
    30	## Reusable knowledge
    31	
    32	- Related skill: skills/principal-contract-review/SKILL.md. [Task 1][Task 2]
    33	- Treat frozen design/task differences as public implementation contracts, not harmless wording: template filenames/substitution syntax and CLI root flags must agree before an executor starts. In the first review, Mustache `{{DOMAIN_NAME}}` templates conflicted with Python `string.Template` `$domain`/`$hub_repo`/`$timestamp`, which would leave placeholders unresolved; `--root`, `--repo-root`, and `--satellite-root` likewise needed a single contract. The later review verified those findings were fixed. [Task 1][Task 2]
    34	- Check requested `scripts/verify.sh` integration against the surrounding responsibility, not its stated number. Section 11 was lifecycle/document tooling; with Sections 1–13 present, a dedicated Section 14 was the valid shared-contract test location, and the later review verified the wiring correction. [Task 1][Task 2]
    35	- For Hub/Satellite shared contracts, Rule 7 makes the Hub physical directory the SSOT; satellites consume it through relative `shared-contracts/` symlinks and treat the linked tree as read-only for Git tracking. [Task 2]
    36	- Task-local `Covers:` lines are the authoritative traceability source when an HLD Kanban summary diverges. Current correction target: Task 2 -> `SSC-ST-01`, `SSC-FR-01`; Task 4 -> `SSC-EC-03`, `SSC-AR-01`, `SSC-AR-02`; Task 5 -> `SSC-HP-03`. [Task 2]
    37	- `python3 -m unittest <file> -k <name>` exits 1 and prints `FAILED` when the named test fails or the file is absent, so it supports specified RED rows. [Task 2]
    38	
    39	## Failures and how to do differently
    40	
    41	- Do not approve implementation because readiness checks pass: compare cross-document semantics and every frozen hard contract. In the current candidate, design spec line 105 and SSC-FR-03 allow an existing physical `shared-contracts/` directory when it is empty, while Task 3 rejects every physical directory. Align the “non-empty” qualifier across design, BDD Given clause, task requirement, Decisions Already Made, and handoff guardrails before implementation; otherwise strict-fidelity execution must Stop-and-Report. [Task 2]
    42	- Do not let a summary overstate traceability. Reconcile HLD Kanban rows in both EN and VI to task-local `Covers:` lines before calling the package ready. [Task 2]
    43	

exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Thiết Kế Skill Đồng Bộ Và Thực Thi Shared Contracts

- **Ngày**: 2026-10-30
- **Trạng thái**: Đã phê duyệt
- **Phạm vi**: Skill mới `skills/sync-shared-contracts/`, CLI engine `sync_contracts.py`, template báo cáo delta chuẩn hóa, bộ test hermetic `test_sync_contracts.py`, tích hợp vào `scripts/verify.sh`
- **Bước tiếp theo**: `d3nexus:dev-designer` (Stage 2 — Thiết kế Mức cao HLD, Kịch bản BDD, và Phân rã Kanban Tasks)

## Mục lục

- [1. Bối cảnh và Động lực](#1-bối-cảnh-và-động-lực)
- [2. Mục tiêu và Ngoài phạm vi](#2-mục-tiêu-và-ngoài-phạm-vi)
- [3. Kiến trúc và Cơ chế Tự động Nhận diện Dual-Mode](#3-kiến-trúc-và-cơ-chế-tự-động-nhận-diện-dual-mode)
- [4. Cấu trúc Thư mục và Schema Mốc Đồng bộ](#4-cấu-trúc-thư-mục-và-schema-mốc-đồng-bộ)
- [5. Đặc tả Kỹ thuật CLI Engine](#5-đặc-tả-kỹ-thuật-cli-engine)
- [6. Bộ Quét Heuristic trên Source Code Đích](#6-bộ-quét-heuristic-trên-source-code-đích)
- [7. Cầu nối Điều phối sang Vòng đời Phát triển](#7-cầu-nối-điều-phối-sang-vòng-đời-phát-triển)
- [8. Chiến lược Kiểm thử và Xác minh](#8-chiến-lược-kiểm-thử-và-xác-minh)
- [9. Xử lý Lỗi và các Trường hợp Biên](#9-xử-lý-lỗi-và-các-trường-hợp-biên)
- [10. Rủi ro và Biện pháp Giảm thiểu](#10-rủi-ro-và-biện-pháp-giảm-thiểu)

## 1. Bối cảnh và Động lực

Sau khi có skill `setup-shared-contracts`, các hệ sinh thái đa repository (chẳng hạn như control plane `D3Nexus` kết nối với các worker node như `lyrics-sync` và ứng dụng di động như `nexus`) đã có công cụ chuẩn hóa để khởi tạo thư mục vật lý `shared-contracts/`, tạo relative symlink và cài đặt các quy tắc quản trị.

Tuy nhiên, sau bước thiết lập ban đầu (Day-0), các đội phát triển đối mặt với bài toán đồng bộ và thực thi liên tục (Day-2 operations):
- Khi Hub repository cập nhật `api_contract.md` hoặc `architecture_and_flow.md` (hoặc phê duyệt một RFC trong `gaps_and_rfcs.md`), các satellite repository thiếu công cụ tự động để phát hiện chính xác những gì đã thay đổi kể từ lần đồng bộ gần nhất.
- Khi một satellite repository ghi nhận đề xuất `Draft` hoặc `In Review` mới vào `gaps_and_rfcs.md`, Hub repository cần cơ chế tự động rà soát các RFC đang chờ xử lý để đưa vào kế hoạch triển khai ở phía backend.
- Việc chuyển tiếp từ các thay đổi trong contract sang quy trình `d3nexus:dev-lifecycle` (Spec -> HLD & BDD -> Worktree TDD Implementation -> Branch Finishing) trên target repo hiện vẫn phải đối chiếu thủ công.

Để tự động hóa toàn diện quy trình kiểm tra sự thay đổi, trích xuất requirements từ contracts và kích hoạt `/dev-lifecycle` trên target repo, chúng tôi xây dựng skill `sync-shared-contracts` cùng CLI engine `sync_contracts.py`.

## 2. Mục tiêu và Ngoài phạm vi

### Mục tiêu
- Cung cấp CLI Python tiêu chuẩn không phụ thuộc thư viện ngoài (`sync_contracts.py`) hỗ trợ 3 lệnh `check`, `brief`, và `ack`.
- Triển khai **Cơ chế Phát hiện Thay đổi Lai 3 Tầng (3-Layer Hybrid Delta Engine)**:
  1. **Git & SHA-256 Watermark Diff**: So sánh lịch sử commit trên Hub và mã băm SHA-256 của 3 file canonical với mốc lưu tại `.agents/contract_sync.json`.
  2. **Structured Markdown Contract Parser**: Phân tích cú pháp bảng endpoints, headers, các trường JSON payload, các bước pipeline, và bảng RFC từ 3 file canonical (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
  3. **Target Codebase Heuristic Scanner**: Quét nhanh source code của target repo để phân loại từng endpoint, header, và trường dữ liệu theo trạng thái `FOUND_IN_CODE` (đã xuất hiện trong code) hoặc `MISSING_IN_CODE` (chưa có trong code).
- Hỗ trợ **Chế độ Kép (Dual-Mode Execution)** tự động nhận diện Satellite symlink mode và Hub physical directory mode.
- Sinh bản **Contract Requirements Brief** (`brief`) làm đầu vào chuẩn hóa để dẫn dắt AI Agent thực thi trọn vẹn 4 giai đoạn của `d3nexus:dev-lifecycle` (`dev-brainstorming` -> `dev-designer` -> `dev-implementation` -> `finishing-a-development-branch`).
- Cung cấp lệnh cập nhật mốc đồng bộ nguyên tử (`ack`) ghi nhận phiên bản contract, Hub commit SHA, mã băm file, và danh sách RFC/endpoints đã xử lý vào `.agents/contract_sync.json`.

### Ngoài phạm vi
- Không thay thế chức năng khởi tạo hạ tầng ban đầu (`init-hub`, `link-satellite`) của `setup-shared-contracts`.
- Không tự ý thực hiện git commit xuyên qua ranh giới symlink trái với Rule 7 của `CRITICAL_RULES.md`.
- Không tự động đẩy code (`git push`) lên remote repository khi chưa có sự đồng ý rõ ràng từ người dùng (bị nghiêm cấm theo Rule 3).

## 3. Kiến trúc và Cơ chế Tự động Nhận diện Dual-Mode

Skill hoạt động trên cả hai phía của mô hình Star Topology bằng cách kiểm tra `<repo_root>/shared-contracts`:

1. **Satellite Mode (`shared-contracts` là một relative symbolic link)**:
   - Phân giải đích của symlink để xác định thư mục `<domain>` và thư mục gốc `<hub_root>` của Hub.
   - Phát hiện các thay đổi từ phía Hub (endpoints mới, trường payload mới, quy tắc pipeline, và các RFC đã `Approved`) cần được implement tại codebase của satellite consumer/worker.
   - Thực thi nghiêm ngặt ranh giới chỉ đọc đối với symlink trong Git (không bao giờ đưa `shared-contracts/` vào git staging của satellite; trạng thái đồng bộ chỉ được lưu tại `.agents/contract_sync.json`).
2. **Hub Mode (`shared-contracts/` là một thư mục vật lý)**:
   - Duyệt qua các thư mục con `shared-contracts/<domain>/` (hoặc lọc theo tham số `--domain`).
   - Phát hiện các RFC/Gaps ở trạng thái `Draft`, `In Review`, hoặc `Approved` do các satellite đề xuất trong `gaps_and_rfcs.md`, cũng như các thay đổi trong contract chưa được đồng bộ vào source code backend của Hub hoặc `.agents/contract_sync.json`.
   - Áp dụng quy tắc ưu tiên `task_01` (Contract-First synchronization) khi phân rã task trong `dev-designer`.

```mermaid
flowchart TD
    subgraph TARGET ["Target Repository (Satellite hoặc Hub)"]
        CLI["sync_contracts.py<br/>(check / brief / ack)"]
        STATE[".agents/contract_sync.json<br/>(Sync Watermark State)"]
        SRC["Target Source Code<br/>(Heuristic Endpoint & Field Scan)"]
    end

    subgraph CONTRACT ["Shared Contracts (Physical hoặc qua Symlink)"]
        API["api_contract.md"]
        ARCH["architecture_and_flow.md"]
        RFC["gaps_and_rfcs.md"]
        GIT["Hub Git History (git log / diff)"]
    end

    subgraph LIFECYCLE ["Orchestrated /dev-lifecycle"]
        S1["Stage 1: dev-brainstorming<br/>(Bilingual Design Spec)"]
        S2["Stage 2: dev-designer<br/>(HLD + BDD + Kanban Tasks)"]
        S3["Stage 3: dev-implementation<br/>(Worktree TDD + sync_contracts.py ack)"]
        S4["Stage 4: finishing-a-development-branch"]
    end

    CLI -->|"1. Đọc mốc sync cũ"| STATE
    CLI -->|"2. Git diff + Parse Markdown"| CONTRACT
    CLI -->|"3. Quét Endpoint/DTO tokens"| SRC
    CLI -->|"4. Xuất Contract Delta Brief"| S1
    S1 --> S2 --> S3 --> S4
    S3 -->|"5. Cập nhật mốc sync mới"| STATE
```

## 4. Cấu trúc Thư mục và Schema Mốc Đồng bộ

### 4.1 Cấu trúc Thư mục của Skill

```text
skills/sync-shared-contracts/
├── SKILL.md
└── resources/
    ├── scripts/
    │   ├── sync_contracts.py
    │   └── test_sync_contracts.py
    └── templates/
        └── contract_delta_brief.md.tmpl
```

### 4.2 Schema Mốc Đồng bộ (`.agents/contract_sync.json`)

File trạng thái đồng bộ được lưu trực tiếp trong target repository tại đường dẫn `.agents/contract_sync.json`:

```json
{
  "schema_version": 1,
  "mode": "satellite",
  "domains": {
    "lyrics-sync": {
      "hub_commit_sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
      "contract_version": "1.1.0",
      "last_synced_at": "2026-10-30T18:30:00Z",
      "file_hashes": {
        "api_contract.md": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "architecture_and_flow.md": "sha256:...",
        "gaps_and_rfcs.md": "sha256:..."
      },
      "acknowledged_rfcs": ["RFC-001", "RFC-002"],
      "acknowledged_endpoints": [
        "POST /api/v1/lyrics-sync/tasks/claim",
        "POST /api/v1/lyrics-sync/tasks/{id}/progress",
        "POST /api/v1/lyrics-sync/tasks/{id}/complete",
        "GET /api/v1/lyrics-sync/status"
      ]
    }
  }
}
```

## 5. Đặc tả Kỹ thuật CLI Engine

Script `sync_contracts.py` cung cấp 3 lệnh con (subcommands):

### 5.1 Lệnh: `check`
```bash
python3 sync_contracts.py check [--repo-root <path>] [--domain <domain_name>] [--json] [--strict]
```
- **Xác thực**:
  - Kiểm tra `shared-contracts` tồn tại và phân giải hợp lệ (không bị dangling symlink, có đủ 3 file canonical).
- **Hành động**:
  1. Đọc `.agents/contract_sync.json` nếu có; nếu chưa tồn tại thì đánh dấu trạng thái domain là `INITIAL_SYNC`.
  2. Tính toán mã băm `sha256` hiện tại của `api_contract.md`, `architecture_and_flow.md`, và `gaps_and_rfcs.md`, đồng thời truy vấn commit SHA mới nhất của thư mục domain trên Hub repository (tự động fallback an toàn nếu không có git history).
  3. Phân tích cú pháp 3 file Markdown canonical để trích xuất thông tin phiên bản, bảng headers, bảng `Endpoints Matrix`, các khóa JSON schema, các bước pipeline, và danh mục RFC trong `Active RFC Ledger`.
  4. Chạy bộ quét Target Codebase Heuristic Scanner trên `<repo_root>` để kiểm tra sự hiện diện của các endpoints, headers, và trường dữ liệu trong source code.
  5. Kết luận trạng thái đồng bộ: `IN_SYNC`, `INITIAL_SYNC`, hoặc `DRIFT_DETECTED`.
- **Mã thoát (Exit Codes)**:
  - `0` khi ở trạng thái `IN_SYNC` (hoặc khi `DRIFT_DETECTED` / `INITIAL_SYNC` ở chế độ thông tin không có cờ `--strict`).
  - `1` khi cấu trúc thư mục/symlink bị lỗi, hoặc khi truyền cờ `--strict` mà trạng thái khác `IN_SYNC`.

### 5.2 Lệnh: `brief`
```bash
python3 sync_contracts.py brief [--repo-root <path>] [--domain <domain_name>] [--output <path>]
```
- **Hành động**:
  - Thực thi toàn bộ phân tích delta 3 tầng tương tự lệnh `check`.
  - Kết xuất từ template `contract_delta_brief.md.tmpl` ra báo cáo Markdown có cấu trúc gồm:
    1. **Topology & Sync Metadata**: Chế độ (`hub` / `satellite`), Domain, Chuyển đổi phiên bản (`cũ -> mới`), dải commit trên Hub, và danh sách các file thay đổi.
    2. **API & Schema Requirements**: Các endpoints và trường JSON payload mới hoặc thay đổi, kèm nhãn kết quả quét code (`FOUND_IN_CODE` vs `MISSING_IN_CODE`).
    3. **Architecture & Pipeline Invariants**: Các bước pipeline bắt buộc, chuyển đổi state machine, và ràng buộc cô lập/cancellation.
    4. **Actionable RFCs & Gaps**: Các mục RFC/Gap đang chờ xử lý hoặc vừa được phê duyệt trong `gaps_and_rfcs.md` tương ứng với vai trò của repo hiện tại.
    5. **Lifecycle Execution Rules**: Chỉ dẫn bắt buộc cho `dev-brainstorming`, `dev-designer` (quy tắc `task_01` và ranh giới symlink), cùng `dev-implementation` (bước xác minh bằng `sync_contracts.py ack`).

### 5.3 Lệnh: `ack`
```bash
python3 sync_contracts.py ack [--repo-root <path>] [--domain <domain_name>] [--rfc <RFC-ID> ...]
```
- **Hành động**:
  - Thu thập mã băm 3 file hiện tại, phiên bản contract, Hub git commit SHA, danh sách endpoints, và danh sách mã RFC (toàn bộ các RFC có trạng thái `Approved` / `Implemented` cộng với các mã được chỉ định qua `--rfc`).
  - Ghi hoặc cập nhật file `.agents/contract_sync.json` một cách nguyên tử (atomic write) thông qua file tạm và `os.replace()`.

## 6. Bộ Quét Heuristic trên Source Code Đích

Nhằm cung cấp góc nhìn tức thì về việc các thành phần trong contract đã được hiện thực hóa trong target repository hay chưa (đặc biệt hữu ích trong lần chạy `INITIAL_SYNC` hoặc khi repo đã code sẵn một phần):
- **Phạm vi Thư mục Quét**: Duyệt đệ quy `<repo_root>` và loại trừ `.git`, `shared-contracts`, `.devtool`, `.agents`, `node_modules`, `build`, `dist`, `target`, `.dart_tool`, cùng `__pycache__`.
- **Định dạng File Hỗ trợ**: `.py`, `.rs`, `.dart`, `.kt`, `.kts`, `.swift`, `.ts`, `.tsx`, `.js`, `.go`, `.java`, `.yaml`, `.yml`, `.json`.
- **Chuẩn hóa Token khi Đối chiếu**:
  - Đối với các endpoint có tham số động như `/api/v1/lyrics-sync/tasks/{id}/progress`, bộ quét tách các đoạn đường dẫn tĩnh (như `/api/v1/lyrics-sync/tasks` và `/progress` hoặc `tasks/claim`) để kiểm tra sự xuất hiện trong source code.
  - Đối với các header (`X-Worker-Token`, `X-Correlation-ID`) và khóa JSON payload (`task_id`, `lease_duration_ms`, `output_data`), bộ quét kiểm tra cả dạng `snake_case` lẫn biến thể `camelCase` tương ứng (phục vụ các client viết bằng Dart, Swift, Kotlin, TypeScript).

## 7. Cầu nối Điều phối sang Vòng đời Phát triển

Khi lập trình viên gọi `/sync-shared-contracts` (hoặc yêu cầu kiểm tra thay đổi từ contract và triển khai trên target repo), skill sẽ điều phối quy trình 5 bước khép kín:

1. **Bước 1 — Kiểm toán Contract & Sinh Bản Tổng hợp (Brief)**:
   - Chạy `sync_contracts.py check` và `sync_contracts.py brief`.
   - Nếu thiếu `shared-contracts` hoặc symlink bị đứt, hướng dẫn chạy `d3nexus:setup-shared-contracts`.
   - Nếu kết quả là `IN_SYNC` và không có mục nào `MISSING_IN_CODE` hay RFC chờ xử lý, thông báo repo đã đồng bộ hoàn toàn và kết thúc.
2. **Bước 2 — Xác nhận Phạm vi (Scope Confirmation)**:
   - Trình bày bản **Contract Requirements Brief** cho lập trình viên để xác nhận các thay đổi/RFC sẽ thực hiện trong đợt này và thống nhất tên `<epic_slug>`.
3. **Bước 3 — Chuyển giao vào Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`)**:
   - Kích hoạt `d3nexus:dev-lifecycle` với đầu vào là bản **Contract Requirements Brief**:
     - **Stage 1 (`dev-brainstorming`)**: Soạn thảo cặp Design Spec song ngữ (`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.en.md` và `.vi.md`) bám sát các thông số đã định nghĩa trong contract (không hỏi lại các thông tin đã được chốt trong contract), và xin phê duyệt Gate 1.
     - **Stage 2 (`dev-designer`)**: Tạo tài liệu HLD song ngữ, kịch bản BDD 5 chiều (`bdd_scenarios.en.md` / `.vi.md`), và tách các Kanban tasks (`task_*.md`) trình duyệt ở Gate 2:
       - Ở **Hub Mode**: `task_01` cập nhật các file vật lý trong `shared-contracts/<domain>/` (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
       - Ở **Satellite Mode**: `task_01` cập nhật các DTO nội bộ, API client, và mock fixtures (tuyệt đối không đưa `shared-contracts/` vào `Files Allowed`).
       - Ở **Cả Hai Mode**: Task cuối cùng (hoặc bước kiểm tra của `task_01`) khai báo `.agents/contract_sync.json` trong `Files Allowed` và chạy lệnh `sync_contracts.py ack` + `sync_contracts.py check --strict` để mốc đồng bộ được commit cùng với code.
4. **Bước 4 — Thực thi tại Stage 3 (`dev-implementation`)**:
   - Thực thi từng task theo TDD trong git worktree cô lập, xác minh `sync_contracts.py check --strict` trả về mã thoát `0`, vượt qua Gate 4 (`quality_check` + `check_bdd_traceability.py` + `audit_epic.py`), thực hiện vòng lặp Review Choice và duyệt Gate 5.
5. **Bước 5 — Hoàn tất Nhánh tại Stage 4 (`finishing-a-development-branch`)**:
   - Rebase, kiểm tra theo tier, merge `--no-ff`, và lưu trữ toàn bộ hồ sơ epic vào `.devtool/epic/<epic_slug>/`.

## 8. Chiến lược Kiểm thử và Xác minh

Bộ kiểm thử cô lập (hermetic) trong `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` sử dụng `unittest` và `tempfile.TemporaryDirectory`:
- **Kiểm thử Initial Sync & Nhận diện Dual-Mode**: Xác minh lệnh `check` nhận diện đúng Hub physical mode và Satellite symlink mode trên các repo mới chưa có `.agents/contract_sync.json`.
- **Kiểm thử Bộ Phân tích Markdown Contract**: Xác minh trích xuất chính xác `Version`, headers, các dòng trong bảng `Endpoints Matrix`, các khóa JSON schema, các bước pipeline, và trạng thái trong bảng `Active RFC Ledger`.
- **Kiểm thử Bộ Quét Heuristic trên Source Code**: Xác minh khả năng phân loại đúng các endpoints và trường DTO (`snake_case` / `camelCase`) đã có hoặc còn thiếu trên các file code giả lập.
- **Kiểm thử Lệnh Ack & Phát hiện Thay đổi Tăng dần (Incremental Drift)**: Xác minh sau khi chạy `ack`, lệnh `check --strict` trả về mã `0` (`IN_SYNC`); khi chỉnh sửa `api_contract.md` hoặc thêm RFC mới trên Hub, lệnh `check --strict` từ Satellite trả về mã `1` (`DRIFT_DETECTED`) kèm lịch sử git commit và file hash delta chính xác.
- **Kiểm thử Kết xuất Brief & Xử lý Lỗi**: Xác minh cấu trúc báo cáo Markdown của lệnh `brief` và mã thoát lỗi khi thiếu thư mục hoặc đứt symlink `shared-contracts`.
- **Tích hợp vào Bộ Kiểm tra Phát hành**: Đăng ký chạy tự động trong `scripts/verify.sh` cùng với `test_setup_contracts.py`.

## 9. Xử lý Lỗi và các Trường hợp Biên

| Kịch bản | Được xử lý bởi | Hành vi |
|---|---|---|
| Chưa tồn tại `shared-contracts` | `check` / `brief` / `ack` | Thoát mã `1` kèm hướng dẫn chạy `setup_contracts.py`. |
| Symlink `shared-contracts` ở Satellite bị đứt | `check` / `brief` / `ack` | Phát hiện đích không tồn tại, thoát mã `1` và hướng dẫn chạy lại `link-satellite --force`. |
| Chưa có file `.agents/contract_sync.json` | `check` / `brief` | Báo trạng thái `INITIAL_SYNC`, phân tích toàn bộ contract hiện tại và phân loại qua bộ quét code heuristic. |
| File `.agents/contract_sync.json` bị lỗi cú pháp JSON | `check` / `ack` | Ghi nhận cảnh báo, coi như chưa đồng bộ khi chạy `check`, và ghi đè lại file chuẩn khi chạy `ack`. |
| Thư mục Hub không phải là Git repository | `check` / `brief` / `ack` | Bỏ qua `git log` / `git rev-parse` an toàn và dựa trên mã băm `sha256` cùng trường `Version`. |

## 10. Rủi ro và Biện pháp Giảm thiểu

- **Rủi ro: Bộ quét Heuristic báo thiếu nhầm (false negative) khi target repo đặt tên biến theo camelCase hoặc ghép nối chuỗi URL.**
  *Biện pháp*: Bộ quét chuẩn hóa các đoạn đường dẫn tĩnh (loại bỏ `{param}`) và kiểm tra cả hai biến thể `snake_case` lẫn `camelCase`, đồng thời kết quả heuristic đóng vai trò chỉ báo bổ trợ bên cạnh mốc đồng bộ chính thức trong `.agents/contract_sync.json`.
- **Rủi ro: Agent trên Satellite vô tình đưa `shared-contracts/` vào git staging khi lưu trạng thái đồng bộ.**
  *Biện pháp*: Trạng thái đồng bộ được lưu hoàn toàn tại `<repo_root>/.agents/contract_sync.json` (nằm ngoài symlink `shared-contracts`), và báo cáo `brief` luôn đính kèm quy tắc cấm đưa `shared-contracts/` vào `Files Allowed` cho `dev-designer`.


exec
/bin/zsh -lc 'cat .devtool/epic/sync_shared_contracts/sync_shared_contracts.vi.md .devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Thiết Kế Chi Tiết Skill Đồng Bộ Và Thực Thi Shared Contracts

## Mục lục

- [Meta Data](#meta-data)
- [Bối cảnh](#bối-cảnh)
- [Mục tiêu và Ngoài phạm vi](#mục-tiêu-và-ngoài-phạm-vi)
- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
- [Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-ranh-giới)
- [Môi trường Xác minh](#môi-trường-xác-minh)
- [Tác động Hợp đồng Dùng chung](#tác-động-hợp-đồng-dùng-chung)
- [Độ bao phủ Kịch bản BDD Toàn diện](#độ-bao-phủ-kịch-bản-bdd-toàn-diện)
- [Chiến lược Triển khai và Giảm thiểu Rủi ro](#chiến-lược-triển-khai-và-giảm-thiểu-rủi-ro)
- [Phân rã Công việc Kanban](#phân-rã-công-việc-kanban)

## Meta Data

- **Tên Epic**: `sync_shared_contracts`
- **Trạng thái**: Packaged
- **Phiên bản đích**: Bản phát hành plugin tiếp theo (1.16.0)
- **Nền tảng**: Python tooling / agent skill kit
- **Spec gốc**: [Approved Sync Shared Contracts design](2026-10-30-sync-shared-contracts-design.vi.md)

## Bối cảnh

Trong khi `setup-shared-contracts` giải quyết bài toán khởi tạo hạ tầng ngày đầu (Day-0: tạo thư mục vật lý `shared-contracts/` tại Hub và relative symlink mode `120000` tại các Satellite), các đội phát triển và AI agent cần một quy trình tự động cho vận hành liên tục (Day-2) để kiểm tra sự thay đổi trong contract, rà soát các RFC cần xử lý, đối chiếu mức độ đáp ứng trong source code của target repo, và kích hoạt quy trình `d3nexus:dev-lifecycle`.

Nếu thiếu công cụ đồng bộ tự động:
1. Các Satellite repository không thể biết chính xác những endpoints, trường dữ liệu hay quy tắc pipeline nào vừa thay đổi trên Hub kể từ lần đồng bộ trước.
2. Hub repository thiếu công cụ quét tự động để phát hiện các đề xuất `Draft` hoặc `In Review` mới do Satellite ghi vào `gaps_and_rfcs.md`.
3. Việc chuyển đổi từ contract delta sang `dev-brainstorming` spec, `dev-designer` HLD/tasks, và `dev-implementation` phải làm thủ công và dễ bỏ sót quy tắc ranh giới Git.

Epic này xây dựng skill `sync-shared-contracts` cùng công cụ CLI `sync_contracts.py` (`check`, `brief`, `ack`) để tự động hóa việc phát hiện thay đổi từ contract và điều phối thực thi trên target repo qua `d3nexus:dev-lifecycle`.

## Mục tiêu và Ngoài phạm vi

### Mục tiêu

- Xây dựng `skills/sync-shared-contracts/SKILL.md` hướng dẫn kiểm toán contract delta và điều phối cầu nối 4 giai đoạn của `d3nexus:dev-lifecycle` trên target repository.
- Xây dựng `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` thực thi 3 lệnh `check`, `brief`, và `ack` bằng thư viện chuẩn Python.
- Triển khai Cơ chế Phát hiện Thay đổi Lai 3 Tầng (3-Layer Hybrid Delta Engine):
  1. Đối chiếu lịch sử commit Git và mã băm SHA-256 của 3 file canonical với `.agents/contract_sync.json`.
  2. Phân tích cú pháp Markdown có cấu trúc cho `api_contract.md`, `architecture_and_flow.md`, và `gaps_and_rfcs.md`.
  3. Quét Heuristic trên source code của target repo để phân loại endpoints, headers, và trường DTO (`snake_case` lẫn `camelCase`) thành `FOUND_IN_CODE` hoặc `MISSING_IN_CODE`.
- Đóng gói template `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` để kết xuất báo cáo **Contract Requirements Brief**.
- Xây dựng bộ kiểm thử cô lập `test_sync_contracts.py` và tích hợp vào `scripts/verify.sh`.

### Ngoài phạm vi

- Không thay thế chức năng khởi tạo topology (`init-hub`, `link-satellite`) của `setup-shared-contracts`.
- Không tự ý git stage hoặc commit xuyên qua ranh giới symbolic link.
- Không đẩy code (`git push`) lên remote repository khi chưa có sự cho phép rõ ràng của người dùng.

## Kiến trúc và Thiết kế Kỹ thuật

### Kiến trúc Tổng thể

```mermaid
flowchart TD
    subgraph TARGET ["Target Repository (Satellite hoặc Hub)"]
        CLI["sync_contracts.py<br/>(check / brief / ack)"]
        STATE[".agents/contract_sync.json<br/>(Watermark State)"]
        SCAN["Heuristic Codebase Scanner<br/>(Routes, Headers, DTO Keys)"]
    end

    subgraph CONTRACT ["Shared Contracts (Physical hoặc Relative Symlink)"]
        C_API["api_contract.md"]
        C_ARCH["architecture_and_flow.md"]
        C_RFC["gaps_and_rfcs.md"]
        H_GIT["Hub Git Log & Diff"]
    end

    subgraph LIFECYCLE ["Orchestrated d3nexus:dev-lifecycle"]
        L_S1["Stage 1: dev-brainstorming<br/>(Gate 1 Bilingual Spec)"]
        L_S2["Stage 2: dev-designer<br/>(Gate 2 HLD, BDD & Tasks)"]
        L_S3["Stage 3: dev-implementation<br/>(Worktree TDD + ack + Gate 4/5)"]
        L_S4["Stage 4: finishing-a-development-branch"]
    end

    CLI -->|"Đọc/Ghi Watermark"| STATE
    CLI -->|"Parse & Hash"| C_API
    CLI -->|"Parse & Hash"| C_ARCH
    CLI -->|"Parse & Hash"| C_RFC
    CLI -->|"Truy vấn Commit Delta"| H_GIT
    CLI -->|"Phân loại Tokens"| SCAN
    CLI -->|"Kết xuất Brief"| L_S1
    L_S1 --> L_S2 --> L_S3 --> L_S4
```

### Sơ đồ Use Cases

```mermaid
flowchart LR
    DEV["Lập trình viên / AI Agent"]
    UC1["Chạy sync_contracts.py check<br/>(Phát hiện Drift & Độ phủ Code)"]
    UC2["Chạy sync_contracts.py brief<br/>(Sinh Bản Tổng hợp Requirements)"]
    UC3["Thực thi /dev-lifecycle trên Target Repo<br/>(Spec -> HLD -> TDD -> Finish)"]
    UC4["Chạy sync_contracts.py ack<br/>(Lưu Watermark vào .agents/contract_sync.json)"]

    DEV --> UC1
    DEV --> UC2
    UC2 --> UC3
    UC3 --> UC4
```

### Sơ đồ Tuần tự (Sequence Diagram)

```mermaid
sequenceDiagram
    participant Dev as Developer / Agent
    participant CLI as sync_contracts.py
    participant Hub as Shared Contracts (Hub / Symlink)
    participant Code as Target Repo Source & .agents/
    participant Life as d3nexus:dev-lifecycle

    Dev->>CLI: check / brief [--domain <name>]
    CLI->>Hub: Kiểm tra topology & tính SHA-256 + git log
    CLI->>Hub: Parse api_contract, architecture_and_flow, gaps_and_rfcs
    CLI->>Code: Đọc .agents/contract_sync.json & quét tokens trong code
    CLI-->>Dev: Xuất Contract Requirements Brief (INITIAL_SYNC / DRIFT_DETECTED)
    Dev->>Life: Stage 1 (dev-brainstorming) -> Duyệt Gate 1 Spec
    Life->>Life: Stage 2 (dev-designer) -> Duyệt Gate 2 HLD & Tasks
    Life->>CLI: Task cuối ở Stage 3 chạy sync_contracts.py ack
    CLI->>Code: Ghi nguyên tử .agents/contract_sync.json
    Life->>CLI: Xác minh sync_contracts.py check --strict trả về exit 0
    Life-->>Dev: Vượt qua Gate 4 & Gate 5 -> Stage 4 Finish Branch
```

## Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới

Integration test roots: skills/sync-shared-contracts/resources/scripts/, scripts/

Protected paths: .agents/quality/**, .devtool/epic/sync_shared_contracts/bdd_scenarios.en.md, .devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md, scripts/verify.sh

Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/sync-shared-contracts.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -> build/test-results/sync-shared-contracts.xml

| Thành phần | File Kiểm thử | Kịch bản Kiểm thử | Ranh giới Mục tiêu |
|---|---|---|---|
| Bộ Phân tích Markdown & Template | `test_sync_contracts.py` | `test_syc_hp_01_parse_and_render_brief` | Phân tích 3 file canonical và kết xuất `contract_delta_brief.md.tmpl` |
| Kiểm tra Dual-Mode & Watermark | `test_sync_contracts.py` | `test_syc_hp_02_satellite_and_hub_check` | Phát hiện `INITIAL_SYNC`, `DRIFT_DETECTED`, và `IN_SYNC` trên cả Hub lẫn Satellite |
| Bộ Quét Codebase Heuristic | `test_sync_contracts.py` | `test_syc_ec_02_heuristic_snake_and_camel_scan` | Đối chiếu đường dẫn tĩnh, headers, và các trường `snake_case`/`camelCase` |
| Lệnh Ack & Cổng Kiểm tra Strict | `test_sync_contracts.py` | `test_syc_st_01_ack_and_incremental_drift` | Ghi nguyên tử `.agents/contract_sync.json` và xác minh mã thoát `--strict` |
| Xác minh Skill & Harness | `test_sync_contracts.py` | `test_syc_hp_03_skill_and_verify_harness` | Xác thực frontmatter của `SKILL.md`, các liên kết và tích hợp `scripts/verify.sh` |

## Môi trường Xác minh

- **Môi trường chạy**: Python 3.10+ (Chỉ dùng Thư viện Tiêu chuẩn: `pathlib`, `os`, `sys`, `json`, `hashlib`, `re`, `subprocess`, `argparse`, `unittest`, `tempfile`).
- **Cô lập**: Toàn bộ kiểm thử chạy trong thư mục tạm `tempfile.TemporaryDirectory()` cô lập hoàn toàn, không kết nối mạng hay chạm tới các repository bên ngoài.
- **Biến môi trường (`Needs`)**: Không yêu cầu (`—`).
- **Lệnh kiểm thử**: `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`
- **Cổng phát hành**: `scripts/verify.sh` thực thi bộ kiểm thử trong mọi lượt xác minh phát hành.

## Tác động Hợp đồng Dùng chung

`None — self-contained developer tooling skill (audits and synchronizes shared contracts for target repositories)`.

## Độ bao phủ Kịch bản BDD Toàn diện

Các kịch bản Gherkin hoàn chỉnh bao phủ cả 5 chiều nằm trong `bdd_scenarios.en.md` và `bdd_scenarios.vi.md`.

- **Happy Paths**:
  - `[SYC-HP-01]`: Phân tích có cấu trúc 3 file hợp đồng canonical và kết xuất báo cáo Contract Requirements Brief.
  - `[SYC-HP-02]`: Phát hiện thay đổi toàn trình trên Satellite và Hub, xác nhận đồng bộ (`ack`), và vượt qua kiểm tra `--strict`.
  - `[SYC-HP-03]`: Xác thực định nghĩa skill và tích hợp vào bộ kiểm tra `scripts/verify.sh`.
- **Edge Cases & Boundaries**:
  - `[SYC-EC-01]`: Phát hiện trạng thái `INITIAL_SYNC` khi chưa tồn tại file `.agents/contract_sync.json`.
  - `[SYC-EC-02]`: Bộ quét heuristic khớp chính xác các route có tham số (`/tasks/{id}/progress`) và trường DTO dạng `camelCase` (`leaseDurationMs`).
  - `[SYC-EC-03]`: Tự động fallback an toàn khi thư mục Hub không phải là một Git repository (không có thư mục `.git`).
- **State Transitions**:
  - `[SYC-ST-01]`: Chuyển trạng thái từ `INITIAL_SYNC` sang `IN_SYNC` sau khi chạy `ack`, và chuyển sang `DRIFT_DETECTED` khi `api_contract.md` hoặc `gaps_and_rfcs.md` trên Hub được cập nhật.
  - `[SYC-ST-02]`: Ghi nhận bổ sung mã RFC mới qua `ack --rfc RFC-002` đồng thời bảo toàn dữ liệu của các domain khác trong `.agents/contract_sync.json`.
- **Async & Concurrency**:
  - `[SYC-AR-01]`: Cập nhật nguyên tử file `.agents/contract_sync.json` qua file tạm (`os.replace`) không để lại file JSON dở dang.
  - `[SYC-AR-02]`: Chống vòng lặp đệ quy vô hạn khi phân giải symbolic link `shared-contracts` bị tạo vòng tròn.
- **Failures & Resilience**:
  - `[SYC-FR-01]`: Từ chối thực thi với mã thoát `1` khi thiếu thư mục hoặc symlink `shared-contracts`.
  - `[SYC-FR-02]`: Từ chối thực thi với mã thoát `1` khi `shared-contracts` là một symlink bị đứt (dangling) hoặc thiếu file canonical.
  - `[SYC-FR-03]`: Phục hồi an toàn khi file `.agents/contract_sync.json` bị hỏng cú pháp JSON trong lúc chạy `check` và ghi đè sạch sẽ khi chạy `ack`.

## Chiến lược Triển khai và Giảm thiểu Rủi ro

- **Triển khai**: Đóng gói thành một skill tiêu chuẩn tại `skills/sync-shared-contracts/` trong plugin `d3nexus`.
- **Triển khai theo giai đoạn**:
  1. Kiểm thử đơn vị và tích hợp trong `ai-agent-tools` thông qua `scripts/verify.sh`.
  2. Thử nghiệm thực tế trên `D3Nexus` (Hub) và `lyrics-sync` / `nexus` (Satellites).
  3. Phát hành chính thức trong phiên bản plugin 1.16.0.
- **Khôi phục (Rollback)**: Xóa thư mục `skills/sync-shared-contracts/` và hoàn tác dòng gọi trong `scripts/verify.sh` sẽ đưa hệ thống về trạng thái ban đầu mà không gây ảnh hưởng phụ.

## Phân rã Công việc Kanban

- [Task 1: Canonical Brief Template and Markdown Contract Parser](task_1_brief_template_and_contract_parser.md) — Covers: `[SYC-HP-01]`, `[SYC-EC-01]`
- [Task 2: Target Codebase Heuristic Scanner and Dual-Mode Check Engine](task_2_heuristic_scanner_and_check_engine.md) — Covers: `[SYC-EC-02]`, `[SYC-EC-03]`, `[SYC-AR-02]`, `[SYC-FR-01]`, `[SYC-FR-02]`
- [Task 3: Watermark Ack Command, Drift Detection, and Brief CLI Subcommands](task_3_watermark_ack_and_brief_cli.md) — Covers: `[SYC-HP-02]`, `[SYC-ST-01]`, `[SYC-ST-02]`, `[SYC-AR-01]`, `[SYC-FR-03]`
- [Task 4: Skill Definition, Lifecycle Bridge Instructions, and Verify Harness Integration](task_4_skill_definition_and_verify_integration.md) — Covers: `[SYC-HP-03]`
# Kịch Bản BDD Cho Sync Shared Contracts

## Mục lục

- [Chiều 1: Tuyến thực thi thành công](#chiều-1-tuyến-thực-thi-thành-công)
- [Chiều 2: Trường hợp biên và ranh giới](#chiều-2-trường-hợp-biên-và-ranh-giới)
- [Chiều 3: Chuyển đổi trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và đồng thời đa repo](#chiều-4-bất-đồng-bộ-và-đồng-thời-đa-repo)
- [Chiều 5: Lỗi và khả năng phục hồi lưu trữ](#chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

## Chiều 1: Tuyến thực thi thành công

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Phân tích cú pháp Contract có cấu trúc và kết xuất báo cáo Requirements Brief
  Given một Hub repository đã khởi tạo với domain lyrics-sync chứa api_contract.md, architecture_and_flow.md, và gaps_and_rfcs.md
  When kỹ sư thực thi lệnh sync_contracts.py brief --domain lyrics-sync
  Then bộ phân tích trích xuất đúng phiên bản "1.0.0", 4 endpoints chuẩn, các authentication headers, các khóa JSON payload, 7 bước pipeline, và RFC-001
  And báo cáo Markdown đầu ra chứa đầy đủ các phần Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, và Lifecycle Execution Rules
  And lệnh kết thúc với exit code 0

Scenario: [SYC-HP-02] [Tier C - Integration] Đồng bộ Satellite toàn trình và vượt qua kiểm tra Strict
  Given một Satellite repository được liên kết qua relative symlink shared-contracts tới ../Hub/shared-contracts/lyrics-sync
  When kỹ sư thực thi sync_contracts.py ack sau đó chạy sync_contracts.py check --strict
  Then file .agents/contract_sync.json được tạo trong Satellite repository với mode "satellite" và domain "lyrics-sync"
  And các mã băm sha256 được ghi nhận khớp với cả 3 file canonical trong Hub
  And lệnh sync_contracts.py check --strict xuất trạng thái "IN_SYNC" và kết thúc với exit code 0

Scenario: [SYC-HP-03] [Tier C - Integration] Xác thực định nghĩa Skill và thực thi bộ kiểm tra phát hành
  Given thư mục skill sync-shared-contracts đã hoàn thiện và được đăng ký trong scripts/verify.sh
  When kỹ sư chạy bộ kiểm tra xác minh cho sync-shared-contracts
  Then file skills/sync-shared-contracts/SKILL.md vượt qua kiểm tra frontmatter và liên kết nội bộ
  And toàn bộ các bài kiểm thử đơn vị và tích hợp trong test_sync_contracts.py đều đạt với exit code 0
```

## Chiều 2: Trường hợp biên và ranh giới

```gherkin
Scenario: [SYC-EC-01] [Tier A - Unit] Phát hiện trạng thái Initial Sync khi chưa có file Watermark
  Given một Satellite repository hợp lệ nhưng chưa có file .agents/contract_sync.json
  When kỹ sư thực thi sync_contracts.py check --json
  Then báo cáo JSON xác định trạng thái của domain là "INITIAL_SYNC"
  And liệt kê cả 3 file hợp đồng canonical là các thay đổi nền tảng cần đồng bộ
  And lệnh kết thúc với exit code 0 khi không truyền --strict và exit code 1 khi truyền --strict

Scenario: [SYC-EC-02] [Tier A - Unit] Bộ quét Heuristic khớp các route có tham số và trường DTO dạng CamelCase
  Given một target repository chứa file mã nguồn src/worker_client.ts có đường dẫn "/api/v1/lyrics-sync/tasks" cùng "/progress" và trường "leaseDurationMs"
  When bộ quét heuristic đánh giá các endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" và "/api/v1/lyrics-sync/status" cùng khóa payload "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" và khóa "lease_duration_ms" được phân loại là "FOUND_IN_CODE"
  And endpoint chưa được hiện thực hóa "/api/v1/lyrics-sync/status" được phân loại là "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Tự động fallback an toàn khi thư mục Hub không có lịch sử Git
  Given một thư mục Hub được tạo trên đĩa mà không có kho chứa .git
  When kỹ sư thực thi sync_contracts.py check hoặc brief
  Then engine bỏ qua lệnh git rev-parse và git log mà không phát sinh lỗi tiến trình con
  And tính toán chính xác trạng thái đồng bộ dựa trên mã băm sha256 của file và trường Version trong contract
```

## Chiều 3: Chuyển đổi trạng thái

```gherkin
Scenario: [SYC-ST-01] [Tier C - Integration] Phát hiện thay đổi tăng dần sau khi cập nhật Contract trên Hub
  Given một Satellite repository đã chạy sync_contracts.py ack trước đó và đang ở trạng thái "IN_SYNC"
  When Hub repository cập nhật api_contract.md lên phiên bản "1.1.0" với endpoint mới POST /api/v1/lyrics-sync/tasks/{id}/cancel và thêm RFC-002 vào gaps_and_rfcs.md
  And kỹ sư chạy lệnh sync_contracts.py check --strict trong Satellite repository
  Then trạng thái chuyển từ "IN_SYNC" sang "DRIFT_DETECTED"
  And báo cáo delta chỉ rõ api_contract.md và gaps_and_rfcs.md đã thay đổi, đánh dấu endpoint cancel mới là "MISSING_IN_CODE", và liệt kê RFC-002
  And lệnh sync_contracts.py check --strict kết thúc với exit code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Bảo toàn Watermark đa domain và ghi nhận mã RFC chỉ định
  Given một Hub repository có hai domain lyrics-sync và nexus trong đó lyrics-sync đã được lưu trong .agents/contract_sync.json
  When kỹ sư thực thi sync_contracts.py ack --domain nexus --rfc RFC-005
  Then file .agents/contract_sync.json giữ nguyên vẹn mục "lyrics-sync" hiện có
  And ghi nhận thêm mục "nexus" mới có chứa "RFC-005" trong danh sách acknowledged_rfcs
```

## Chiều 4: Bất đồng bộ và đồng thời đa repo

```gherkin
Scenario: [SYC-AR-01] [Tier A - Unit] Cập nhật file Watermark nguyên tử ngăn chặn đọc phải JSON dở dang
  Given một file .agents/contract_sync.json đang tồn tại trong target repository
  When lệnh sync_contracts.py ack ghi dữ liệu đồng bộ mới
  Then engine ghi vào một file tạm trong thư mục .agents/ và thay thế nguyên tử file .agents/contract_sync.json
  And không để sót lại bất kỳ file tạm nào trong .agents/ sau khi hoàn tất

Scenario: [SYC-AR-02] [Tier A - Unit] Bảo vệ chống vòng lặp Symlink khi phân giải Topology
  Given một repository nơi đường dẫn shared-contracts nằm trong một chuỗi symbolic link trỏ vòng tròn vượt quá 10 bước nhảy
  When kỹ sư thực thi sync_contracts.py check
  Then quá trình duyệt symlink dừng lại một cách xác định tại giới hạn 10 bước nhảy
  And thoát với exit code 1 kèm thông báo lỗi phát hiện vòng lặp symbolic link
```

## Chiều 5: Lỗi và khả năng phục hồi lưu trữ

```gherkin
Scenario: [SYC-FR-01] [Tier A - Unit] Từ chối thực thi khi thiếu thư mục hoặc symlink Shared Contracts
  Given một target repository không có thư mục hay symlink shared-contracts
  When kỹ sư thực thi lệnh sync_contracts.py check, brief, hoặc ack
  Then lệnh dừng ngay với exit code 1
  And in ra thông báo lỗi hướng dẫn người dùng khởi tạo hoặc liên kết contracts bằng setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Từ chối thực thi khi Symlink bị đứt hoặc thiếu file Canonical
  Given một Satellite repository có symlink shared-contracts trỏ tới đường dẫn Hub không tồn tại hoặc thiếu file architecture_and_flow.md
  When kỹ sư thực thi lệnh sync_contracts.py check
  Then lệnh dừng ngay với exit code 1
  And in ra thông báo chẩn đoán nêu rõ đường dẫn đích bị đứt hoặc tên file canonical bị thiếu

Scenario: [SYC-FR-03] [Tier A - Unit] Khả năng phục hồi khi file Watermark JSON bị hỏng
  Given một target repository có file .agents/contract_sync.json chứa nội dung JSON không hợp lệ "{corrupt"
  When kỹ sư chạy lệnh sync_contracts.py check sau đó chạy sync_contracts.py ack
  Then lệnh sync_contracts.py check ghi nhận cảnh báo JSON lỗi và chuyển về trạng thái "INITIAL_SYNC" mà không bị văng lỗi
  And lệnh sync_contracts.py ack ghi đè sạch sẽ .agents/contract_sync.json bằng cấu trúc JSON schema_version 1 hợp lệ
```


exec
/bin/zsh -lc "nl -ba ../D3Nexus/shared-contracts/lyrics-sync/api_contract.md | sed -n '1,190p'; nl -ba ../D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md | sed -n '1,190p'; nl -ba ../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md | sed -n '1,160p'; nl -ba ../D3Nexus/shared-contracts/nexus/api_contract.md | sed -n '1,160p'; nl -ba ../D3Nexus/shared-contracts/nexus/architecture_and_flow.md | sed -n '1,150p'; nl -ba ../D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md | sed -n '1,160p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# API & Protocol Data Contract: D3Nexus ⇄ lyrics-sync
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference
     7	Audience: D3Nexus Control Plane & lyrics-sync Worker Fleet Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 3.0.0
    10	-->
    11	
    12	## 1. Authentication & Protocol Headers
    13	
    14	All worker endpoints require the shared bearer authentication token header:
    15	
    16	```http
    17	X-Worker-Token: <D3N_WORKER_SECRET_TOKEN>
    18	Content-Type: application/json
    19	Accept: application/json
    20	```
    21	
    22	Alternatively, standard Authorization header is accepted:
    23	```http
    24	Authorization: Bearer <D3N_WORKER_SECRET_TOKEN>
    25	```
    26	
    27	For Server-Sent Events (SSE) streaming:
    28	```http
    29	X-Worker-Token: <D3N_WORKER_SECRET_TOKEN>
    30	Accept: text/event-stream
    31	```
    32	
    33	---
    34	
    35	## 2. Align Studio Worker Endpoints (`/api/v1/align/...`)
    36	
    37	### 2.1. Claim Task (`POST /api/v1/align/worker/claim`)
    38	Worker requests the next available task from the queue based on its hardware capabilities.
    39	
    40	* **Method**: `POST`
    41	* **Path**: `/api/v1/align/worker/claim`
    42	* **Request Payload**:
    43	  ```json
    44	  {
    45	    "worker_id": "DanhDues-Mac-mini.local",
    46	    "capabilities": ["mps", "demucs_v4", "whisper_large_v3", "lexical_enrichment"]
    47	  }
    48	  ```
    49	  * `worker_id` (`string`, required): Unique hostname or identifier of the claiming worker node.
    50	  * `capabilities` (`list[string]`, required): List of supported features and acceleration tiers.
    51	* **Responses**:
    52	  * **`200 OK`**: Task claimed successfully. Returns task descriptor:
    53	    ```json
    54	    {
    55	      "id": "521420f6-4c7a-4a82-b1b6-fa12233b45a2",
    56	      "source_type": "youtube",
    57	      "media_url": "https://www.youtube.com/watch?v=0kDXKTYKBEM",
    58	      "media_file_path": null,
    59	      "audio_url": null,
    60	      "language": "en",
    61	      "target_lang": "vi",
    62	      "lyrics_text": "Hello world\nThis is an aligned sentence\n",
    63	      "cefr_level": "B2",
    64	      "domains": ["song", "pop"],
    65	      "pronoun_style": "informal",
    66	      "translation_style": "natural",
    67	      "content_type": "music_video"
    68	    }
    69	    ```
    70	    * `id` (`string`, UUID): Unique task identifier.
    71	    * `source_type` (`string`): `"youtube"` or `"file"`.
    72	    * `media_url` (`string | null`): Remote URL (YouTube / HTTP media stream).
    73	    * `media_file_path` (`string | null`): Local filesystem absolute path if co-located.
    74	    * `audio_url` (`string | null`): Direct audio stream URL.
    75	    * `language` (`string`): Source spoken language code (e.g. `"en"`).
    76	    * `target_lang` (`string`): Target translation language code (e.g. `"vi"`).
    77	    * `lyrics_text` (`string | null`): Raw lyric text if provided upfront; null triggers ASR.
    78	    * `cefr_level` (`string`): Target learner proficiency level (`"A1"` to `"C2"`).
    79	    * `domains` (`list[string]`): Content domains (`["song"]`, `["news"]`, etc.).
    80	    * `pronoun_style` (`string | null`): Localized translation pronoun preference.
    81	    * `translation_style` (`string | null`): Translation tone (`"natural"`, `"literal"`).
    82	    * `content_type` (`string | null`): Taxonomy content category.
    83	  * **`204 No Content`**: Queue is empty. Worker sleeps for `poll_interval` seconds (default 5.0s).
    84	
    85	---
    86	
    87	### 2.2. Telemetry Heartbeat (`POST /api/v1/align/worker/tasks/{id}/heartbeat`)
    88	Worker renews task lease and reports hardware telemetry metrics.
    89	
    90	* **Frequency**: Sent every `10.0 seconds`.
    91	* **Method**: `POST`
    92	* **Path**: `/api/v1/align/worker/tasks/{id}/heartbeat`
    93	* **Request Payload**:
    94	  ```json
    95	  {
    96	    "worker_id": "DanhDues-Mac-mini.local",
    97	    "extend_secs": 60,
    98	    "metrics": {
    99	      "cpu_pct": 21.4,
   100	      "ram_used_mb": 29030,
   101	      "ram_total_mb": 65536,
   102	      "mps_allocated_mb": 64,
   103	      "mps_driver_allocated_mb": 0,
   104	      "thermal_state": "nominal"
   105	    }
   106	  }
   107	  ```
   108	* **Telemetry Fields Contract**:
   109	  * `cpu_pct` (`float`, `f64`): Total host CPU utilization percentage (`0.0` - `100.0`).
   110	  * `ram_used_mb` (`u64` via flexible deserializer): Host RAM used in megabytes. Worker SHOULD send integer megabytes (`round(used_mb)`).
   111	  * `ram_total_mb` (`u64` via flexible deserializer): Total system RAM in megabytes. Worker SHOULD send integer megabytes (`round(total_mb)`).
   112	  * `mps_allocated_mb` (`Option<f64>`): PyTorch Apple Silicon MPS VRAM actively allocated in megabytes (`0` or `0.0` if CPU/CUDA). Accepts both floating-point numbers (`0.0`, `64.01`) and integers (`4096`).
   113	  * `mps_driver_allocated_mb` (`Option<f64>`, optional): Driver-allocated MPS VRAM in megabytes.
   114	  * `thermal_state` (`string`): macOS thermal pressure (`"nominal"`, `"fair"`, `"serious"`, `"critical"`).
   115	
   116	* **Postel's Law Adherence (Defense-in-depth)**:
   117	  * **Worker (`lyrics-sync`) — Conservative Sender**: Always rounds memory values to integer megabytes using `round(...)` before JSON dispatch.
   118	  * **Control Plane (`D3Nexus`) — Liberal Receiver**: Uses `Option<f64>` for MPS fields and `deserialize_flexible_u64` for RAM fields in `models.rs` to guarantee HTTP 200 without 422 schema rejections.
   119	* **Responses**:
   120	  * **`200 OK`**:
   121	    ```json
   122	    {
   123	      "status": "extended",
   124	      "should_abort": false,
   125	      "lease_expires_at": 1793129999000
   126	    }
   127	    ```
   128	    * `should_abort` (`bool`): If `true`, worker must immediately terminate execution.
   129	  * **`404 Not Found` / `409 Conflict`**: Lease lost or reassigned. Worker triggers Heartbeat Fencing.
   130	
   131	---
   132	
   133	### 2.3. Progressive Step Logging (`POST /api/v1/align/worker/tasks/{id}/step`)
   134	Worker reports transition into and completion of canonical pipeline steps.
   135	
   136	* **Method**: `POST`
   137	* **Path**: `/api/v1/align/worker/tasks/{id}/step`
   138	* **Request Payload**:
   139	  ```json
   140	  {
   141	    "worker_id": "DanhDues-Mac-mini.local",
   142	    "step_name": "vocal_separation",
   143	    "status": "success",
   144	    "spent_time_ms": 4422,
   145	    "log_message": "Completed vocal_separation via Demucs v4 on MPS"
   146	  }
   147	  ```
   148	  * `step_name` (`string`, required): One of the 7 canonical steps:
   149	    `"media_ingest"`, `"vocal_separation"`, `"alignment_asr"`, `"semantic_resegment"`, `"translation"`, `"lexical_enrichment"`, `"artifact_export"`.
   150	  * `status` (`string`, required): `"running"`, `"success"`, `"skipped"`, or `"failed"`.
   151	  * `spent_time_ms` (`integer | null`): Execution time in milliseconds (null when `status: "running"`, `0` when `status: "skipped"`).
   152	  * `log_message` (`string | null`): Optional descriptive execution detail.
   153	* **Responses**:
   154	  * **`200 OK`**: `{"status": "recorded"}`
   155	
   156	---
   157	
   158	### 2.4. Deliver Complete Align Result (`POST /api/v1/align/worker/tasks/{id}/complete`)
   159	Worker submits the final synchronized lyric document, bilingual translations, and 10-field lexical chunks/flashcards.
   160	
   161	* **Method**: `POST`
   162	* **Path**: `/api/v1/align/worker/tasks/{id}/complete`
   163	* **Request Payload**:
   164	  ```json
   165	  {
   166	    "worker_id": "DanhDues-Mac-mini.local",
   167	    "spent_time_ms": 24899,
   168	    "output_uri": "/tmp/lyrics_sync_scratch/521420f6-4c7a-4a82-b1b6-fa12233b45a2/out/lyrics.json",
   169	    "payload": {
   170	      "schema": "lyrics-sync/v1",
   171	      "meta": {
   172	        "source": {
   173	          "type": "youtube",
   174	          "id": "0kDXKTYKBEM"
   175	        },
   176	        "title": "Qwen Calling Home",
   177	        "language": "en",
   178	        "durationMs": 184500,
   179	        "offsetMs": 0,
   180	        "difficulty": "intermediate",
   181	        "domain": "song",
   182	        "domains": ["song", "pop"],
   183	        "content_type": "music_video",
   184	        "translation_style": "natural",
   185	        "generator": {
   186	          "name": "lyrics-sync",
   187	          "version": "1.0.0",
   188	          "mode": "ml",
   189	          "aligner": "wav2vec2+whisper"
   190	        }
     1	# Architecture and System Flow Contract: D3Nexus ⇄ lyrics-sync
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference & architectural explanation
     7	Audience: D3Nexus Control Plane & lyrics-sync Worker Fleet Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 3.0.0
    10	-->
    11	
    12	## 1. System Roles & Responsibilities
    13	
    14	The system is partitioned into two decoupled, specialized sub-systems operating in a Producer-Consumer / Orchestrator-Worker relationship:
    15	
    16	```text
    17	┌────────────────────────────────────────────────────────────────────────┐
    18	│                        D3Nexus Control Plane                           │
    19	│  - Task Queue & Lease Scheduling (SQLite / PostgreSQL)                 │
    20	│  - Real-time State & SSE Broadcasting Hub (< 50ms)                     │
    21	│  - Dual-Pipeline Dispatcher: Align Studio & TTS Studio Engine          │
    22	│  - Cloud Quota Fallback Interceptor (HTTP 429 -> Local Worker Queue)   │
    23	│  - End-User Interactive Web UI & Mobile API Hub                        │
    24	│  - SOLE OWNER OF DATABASE PERSISTENCE                                  │
    25	│    (Atomic transaction: tracks, lyrics catalog, flashcards, speech)    │
    26	└───────────────────────────────────┬────────────────────────────────────┘
    27	                                    │ HTTP REST (X-Worker-Token)
    28	                                    │ + SSE Stream (< 50ms)
    29	                                    ▼
    30	┌────────────────────────────────────────────────────────────────────────┐
    31	│                        lyrics-sync Worker Fleet                        │
    32	│  - Pure Stateless Compute Node (macOS Apple Silicon MPS / Linux CUDA)  │
    33	│                                                                        │
    34	│  [Capability 1: Align Studio Pipeline]                                 │
    35	│  - Demucs v4 Vocal Stem Isolation & Audio Resampling                   │
    36	│  - Wav2Vec2 CTC Forced Alignment + Whisper ASR Fallback                │
    37	│  - LLM Boundary Alignment, Contextual Translation & Lexical Mining     │
    38	│                                                                        │
    39	│  [Capability 2: TTS Studio Pipeline]                                   │
    40	│  - High-Fidelity Neural Speech Synthesis (Kokoro-82M on MPS/CUDA)      │
    41	│  - Cloud Quota Fallback Task Execution (Offline Mac Mini Worker)       │
    42	│  - Multi-Speaker Dialogue Stitching & Word-Level Timing Extraction     │
    43	│  - Bilingual Script Generation & CEFR Lexical Filtering                │
    44	│                                                                        │
    45	│  - Strictly FORBIDDEN from direct database connections                 │
    46	│  - Automatic process-group fencing, memory purging & scratch cleanup   │
    47	└────────────────────────────────────────────────────────────────────────┘
    48	```
    49	
    50	### 1.1. Core Invariants
    51	1. **Stateless Compute Boundary**: `lyrics-sync` workers operate strictly as compute daemons. Workers **MUST NOT** possess direct database credentials (`DATABASE_URL`, PostgreSQL connection strings) and **MUST NOT** execute direct writes to the D3Nexus database.
    52	2. **Domain Ownership Boundary**: `D3Nexus` is the sole owner of persistent storage. Upon receiving completion payloads, D3Nexus atomically persists tracks, synchronized lyrics, vocabulary flashcards, and synthesized speech audio records.
    53	3. **Dual-Layer Control Plane**:
    54	   - **Primary Fast Channel**: Long-lived Server-Sent Events (SSE) connection (`GET /api/v1/align/tasks/{id}/stream` and `GET /api/v1/speech/jobs/{id}/events`) for sub-50ms operator cancellation and real-time telemetry.
    55	   - **Heartbeat & Telemetry Channel**: Periodic bidirectional heartbeats sent every `10.0 seconds` for lease renewal, hardware telemetry reporting, and fencing.
    56	
    57	---
    58	
    59	## 2. Pipeline 1: Align Studio Architecture & State Machine
    60	
    61	Task processing for music, speech, and podcast alignment progresses through **3 Phases** encompassing **7 Canonical Steps**. This sequence is authoritative across both codebases (`src/lyrics_sync/worker/bridge.py::CANONICAL_STEPS` and D3Nexus backend/frontend).
    62	
    63	### 2.1. Canonical Step Definitions & Progress Mapping
    64	
    65	```text
    66	[Phase 1: Audio Processing & Text Structuring]
    67	  1. media_ingest         (Progress: ~15%) - Download / load audio, resample to 16kHz mono WAV
    68	         │
    69	         ▼
    70	  2. vocal_separation     (Progress: ~30%) - Isolate clean vocal stem via Demucs v4 (MPS/CUDA)
    71	         │
    72	         ▼
    73	  3. alignment_asr        (Progress: ~45%) - Word-level CTC forced alignment + Whisper ASR fallback
    74	         │
    75	         ▼
    76	[Phase 2: Linguistic Structuring & Translation]
    77	  4. semantic_resegment   (Progress: ~60%) - LLM acoustic & grammatical boundary re-segmentation
    78	         │
    79	         ▼
    80	  5. translation          (Progress: ~75%) - Context-aware bilingual sentence translation
    81	         │
    82	         ▼
    83	[Phase 3: Lexical Mining & Artifact Assembly]
    84	  6. lexical_enrichment   (Progress: ~90%) - Extract 10-field collocations, CEFR, IPA & grammar notes
    85	         │
    86	         ▼
    87	  7. artifact_export      (Progress: 100%) - LyricsDoc schema validation & payload packaging
    88	```
    89	
    90	| Step Index | Step Name | Typical Weight / Progress | Description | UI Display Label |
    91	| :---: | :--- | :---: | :--- | :--- |
    92	| **1** | `media_ingest` | 15% | Download source audio/video or resolve local file, convert to 16kHz mono WAV | Ingest Audio |
    93	| **2** | `vocal_separation` | 30% | Separate instrumental and vocal stems using Demucs v4 HTDemucs on GPU/MPS | Vocal Separation |
    94	| **3** | `alignment_asr` | 45% | Align lyrics with audio at word level via Wav2Vec2 CTC; fallback to local Whisper | Forced Alignment & ASR |
    95	| **4** | `semantic_resegment` | 60% | Align sentence boundaries based on acoustics and LLM syntax rules (skippable) | Semantic Resegment |
    96	| **5** | `translation` | 75% | Translate sentences into Vietnamese with style/pronoun adaptation | Bilingual Translation |
    97	| **6** | `lexical_enrichment` | 90% | Mine formulaic sequences, collocations, CEFR tiers, IPA, and cloze highlight masks | Lexical Enrichment |
    98	| **7** | `artifact_export` | 100% | Validate `lyrics-sync/v1` schema, write local artifacts, assemble completion payload | Artifact Export |
    99	
   100	### 2.2. Step State Lifecycle
   101	Each step in `media_align_step_logs` follows a strict state transition:
   102	
   103	```text
   104	               ┌──────────┐
   105	               │ pending  │
   106	               └────┬─────┘
   107	                    │
   108	         ┌──────────┴──────────┐
   109	         │ (start_step)        │ (bypass / skip)
   110	         ▼                     ▼
   111	   ┌───────────┐         ┌───────────┐
   112	   │  running  │         │  skipped  │ (spent_time_ms = 0)
   113	   └─────┬─────┘         └───────────┘
   114	         │
   115	   ┌─────┴─────┐
   116	   │           │
   117	   ▼           ▼
   118	┌─────────┐ ┌────────┐
   119	│ success │ │ failed │
   120	└─────────┘ └────────┘
   121	```
   122	
   123	- **`pending`**: Step is queued, waiting for previous steps to complete.
   124	- **`running`**: Worker is actively processing this step. Emits `POST /step` with `status: "running"`, `spent_time_ms: null`.
   125	- **`success`**: Step completed normally. Emits `POST /step` with `status: "success"` and measured `spent_time_ms`.
   126	- **`skipped`**: Step was deliberately bypassed by runtime policy (e.g. `skip_llm == True`). Emits `POST /step` with `status: "skipped"` và `spent_time_ms: 0`.
   127	- **`failed`**: Step aborted due to an unrecoverable exception.
   128	
   129	> [!IMPORTANT]
   130	> **No Fake 1 ms Backfills**:
   131	> Bypassed steps must **never** be backfilled with `spent_time_ms = 1`. D3Nexus UI displays skipped steps cleanly as `SKIPPED (0 ms)`.
   132	
   133	### 2.3. Overall Align Task State Machine
   134	
   135	```text
   136	    ┌──────────┐
   137	    │  QUEUED  │ (Created by User / Ingestion Job)
   138	    └────┬─────┘
   139	         │ Worker claims task (POST /api/v1/align/worker/claim -> 200 OK)
   140	         ▼
   141	   ┌───────────┐
   142	   │  CLAIMED  │ (Lease granted, default 900s)
   143	   └─────┬─────┘
   144	         │ Worker starts executing Phase 1
   145	         ▼
   146	 ┌───────────────┐
   147	 │  PROCESSING   │ ◄─── (Periodic Telemetry Heartbeats every 10.0s)
   148	 └───┬───┬───┬───┘
   149	     │   │   │
   150	     │   │   └─► Operator cancels (SSE / UI / CLI) ───────────► ┌───────────┐
   151	     │   │                                                      │ CANCELLED │
   152	     │   └─────► Lease expires / 3 failed heartbeats (Fencing) ─► └───────────┘
   153	     │           (Worker terminates child procs; DB reaper reclaims)
   154	     │
   155	     ├─► Fatal pipeline failure ──────────────────────────────► ┌───────────┐
   156	     │                                                          │  FAILED   │
   157	     │                                                          └───────────┘
   158	     ▼ All 7 steps succeed & POST /complete succeeds
   159	┌─────────────┐
   160	│  COMPLETED  │ (Atomic DB transaction commits lyrics & flashcards)
   161	└─────────────┘
   162	```
   163	
   164	### 2.4. Lexical Mining & Dual Highlighting Presentation Contract
   165	
   166	During canonical step 6 (`lexical_enrichment`), `UnifiedLinguisticAnalyzer` extracts collocations, phrasal verbs, idioms, and sentence frames. To balance acoustic reading fluency during song playback with focused memorization during vocabulary study, the system partitions presentation responsibilities according to the **Dual Highlighting Paradigm**:
   167	
   168	1. **Active Lyric Karaoke Line (Client Playback)**:
   169	   - **Scope**: Highlights the entire constituent verb-object phrase chunk (`usage_text`, e.g. `"set off a dream"` or `"let this moment end"`).
   170	   - **Interaction**: Clicking any constituent token within the chunk opens the popover HUD for the corresponding collocation headword.
   171	2. **Popover HUD & FSRS Review Flashcard (Vocabulary Study)**:
   172	   - **Scope**: Highlights ONLY the core dictionary tokens via `highlight_mask` (`<mark class="d3-target lexical-core">`), leaving variable syntactic arguments unhighlighted (`<span class="lexical-context">`).
   173	     - Example Continuous (`set off sth`): `You <mark class="d3-target lexical-core">set off</mark> <span class="lexical-context">a dream</span> in me`.
   174	     - Example Discontinuous (`let sth end`): `Can't <mark class="d3-target lexical-core">let</mark> <span class="lexical-context">this moment</span> <mark class="d3-target lexical-core">end</mark>`.
   175	   - **Contextual Meaning Row (`A => B`)**:
   176	     - Format: Section label `💡 Ý nghĩa câu:` rendered on its own line.
   177	     - On a dedicated new line below the label, Column A (`usage_text`, full sample in sentence, Studio Orange text `#ff6b00`) and Column B (`meaning_vi`, contextual translation, Vivid Green text `#22c55e`) are displayed with equal line height, separated by a centered `=>`.
   178	
   179	---
   180	
   181	## 3. Pipeline 2: TTS Studio Architecture & Worker Lifecycle
   182	
   183	TTS Studio supports multi-modal speech generation for language learning (dialogue lessons, pronunciation practice, vocabulary shadowing).
   184	
   185	### 3.1. Hybrid Execution Architecture (Cloud + Worker Fallback)
   186	D3Nexus operates an intelligent hybrid dispatch model:
   187	
   188	1. **Client Direct / Edge**: Lightweight synthesis via EdgeTTS directly from client or proxy.
   189	2. **Server Cloud Proxy**: High-tier synthesis via ElevenLabs.
   190	3. **Local Compute Worker (Kokoro-82M)**: Deep neural synthesis executed by the `lyrics-sync` Mac mini/GPU worker fleet.
     1	# Gaps, Open Inquiries & RFCs: D3Nexus ⇄ lyrics-sync
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference & collaboration log
     7	Audience: D3Nexus Control Plane & lyrics-sync Worker Fleet Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.0.0
    10	-->
    11	
    12	This document serves as the formal asynchronous Request For Change (RFC) and communication ledger between the AI Agents and engineers developing `lyrics-sync` and `D3Nexus`.
    13	
    14	---
    15	
    16	## 1. Open Gaps & Alignment Questions (For D3Nexus Confirmation)
    17	
    18	### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
    19	* **Observation**:
    20	  Full alignment payloads containing word-level timestamps (`Word`), bilingual sentence translations, and comprehensive 10-field lexical chunks (`all_collocations`) can range from `500 KB` to `5 MB` for long videos (e.g. 10-15 minute speeches or audio tracks). Axum's default `DefaultBodyLimit` is `2 MB`.
    21	* **Current Behavior**:
    22	  For standard 3-5 minute songs, payloads remain under 1MB. However, long-form content may be rejected with `HTTP 413 Payload Too Large`.
    23	* **Proposed Action for D3Nexus**:
    24	  Ensure the Axum router configures an explicit body limit for the completion endpoint in `apps/server/src/align/routes.rs`:
    25	  ```rust
    26	  .route("/api/v1/align/worker/tasks/:id/complete", post(complete_task))
    27	  .layer(axum::extract::DefaultBodyLimit::max(10 * 1024 * 1024)) // 10 MB limit
    28	  ```
    29	* **Status**: `OPEN` (Awaiting D3Nexus confirmation).
    30	
    31	---
    32	
    33	### GAP-02: Mixed Timestamp Key Formats (`startMs` vs `start_ms`)
    34	* **Observation**:
    35	  In `lyrics-sync/v1`, line and word timestamps use camelCase (`startMs`, `endMs`, `durationMs`) adhering to the committed JSON schema (`schema/lyrics-sync.v1.schema.json`). However, inside `all_collocations[].occurrences`, timestamps use snake_case (`start_ms`, `end_ms`).
    36	* **Current Behavior**:
    37	  Both are supported by Python Pydantic models via `populate_by_name = True` and validation aliases.
    38	* **Proposed Action for D3Nexus**:
    39	  In Rust Serde structs (`learning_domain::align::models`), ensure fields support both naming variants using Serde aliases:
    40	  ```rust
    41	  #[derive(Debug, Deserialize, Serialize)]
    42	  pub struct WordTimestamp {
    43	      pub text: String,
    44	      #[serde(alias = "start_ms", alias = "startMs")]
    45	      pub start_ms: u64,
    46	      #[serde(alias = "end_ms", alias = "endMs")]
    47	      pub end_ms: u64,
    48	      pub score: Option<f64>,
    49	  }
    50	  ```
    51	* **Status**: `OPEN` (Documented in API Contract; recommend Serde alias in D3Nexus).
    52	
    53	---
    54	
    55	### GAP-03: Co-Located Media Path vs Remote Media URL Resolution
    56	* **Observation**:
    57	  `POST /claim` returns both `media_url` (remote web/YouTube URL) and `media_file_path` (local filesystem path).
    58	  When worker and server run on the same physical host (e.g. developer Mac Mini), the worker can directly process `media_file_path`, completely skipping network download and rate-limits.
    59	* **Current Behavior**:
    60	  `lyrics_sync.worker.bridge` prefers `media_file_path` if the file exists on the local filesystem; otherwise, it falls back to `media_url`.
    61	* **Proposed Action for D3Nexus**:
    62	  When creating alignment tasks on D3Nexus, if the source media was uploaded by the user to local disk storage, populate `media_file_path` with the absolute local path.
    63	* **Status**: `ACCEPTED` (Implemented in Worker; D3Nexus should preserve `media_file_path`).
    64	
    65	---
    66	
    67	### GAP-04: Worker Token Authentication for Fleet Monitoring (`GET /api/v1/align/fleet`)
    68	* **Observation**:
    69	  Currently, `GET /api/v1/align/fleet` requires an authenticated web user cookie/session in D3Nexus, returning `HTTP 401 Unauthorized` when queried using `X-Worker-Token`.
    70	  As a result, CLI inspection commands (`lyrics-sync worker top`) running on worker nodes cannot query cluster-wide fleet status using their worker token.
    71	* **Proposed Action for D3Nexus**:
    72	  Update the authentication middleware in D3Nexus for `/api/v1/align/fleet` to accept either:
    73	  1. An authenticated user session, OR
    74	  2. A valid `X-Worker-Token` matching `D3N_WORKER_SECRET_TOKEN`.
    75	* **Status**: `OPEN` (Requested for worker fleet CLI management).
    76	
    77	---
    78	
    79	### GAP-05: Server Restart Orphaned Task Reclaim Hook
    80	* **Observation**:
    81	  When D3Nexus restarts while tasks are in `claimed` state, those tasks remain locked until the 900-second lease expires via the background `lease_reaper`.
    82	* **Proposed Action for D3Nexus**:
    83	  On startup of the D3Nexus server, execute an initial pass of `lease_reaper` or check if the worker heartbeat has timed out, allowing quicker reclamation of interrupted tasks.
    84	* **Status**: `PROPOSED`.
    85	
    86	---
    87	
    88	### GAP-06: Fleet Status Missing Active Pipeline Step (`current_step` in `GET /api/v1/align/fleet`)
    89	* **Observation**:
    90	  `lyrics-sync worker top` displays a dedicated `STEP` column to show the active canonical step (e.g. `media_ingest`, `vocal_separation`, `alignment_asr`, `semantic_resegment`, etc.).
    91	  However, `GET /api/v1/align/fleet` returns `WorkerInfo` records sourced from `media_align_workers`, which does not contain `current_step` or query the active step.
    92	  As a result, `worker top` on the Terminal displays `-` in the `STEP` column for busy nodes.
    93	* **Resolution / Proposed Action**:
    94	  1. **`lyrics-sync` Client**: Enriched `worker top` to load `~/.lyrics_sync/worker_status.json` and merge `current_step` for matching local worker daemon instances.
    95	  2. **`D3Nexus` Server Proposal**: In `features/learning/data/src/align/repository.rs` (`list_workers`), enrich `WorkerInfo` by querying the latest step for `current_task_id`:
    96	     ```sql
    97	     SELECT worker_id, host_name, ip_address, hardware,
    98	            status, current_task_id, metrics_json, last_heartbeat_at, registered_at,
    99	            (SELECT step_name FROM media_align_step_logs WHERE task_id = media_align_workers.current_task_id ORDER BY created_at DESC LIMIT 1) AS current_step
   100	     FROM media_align_workers
   101	     ORDER BY registered_at ASC
   102	     ```
   103	     and add `pub current_step: Option<String>` to `WorkerInfo` in `features/learning/domain/src/align/models.rs`.
   104	* **Status**: `PROPOSED` (Implemented local enrichment in Worker CLI; awaiting D3Nexus contract approval).
   105	
   106	---
   107	
   108	### GAP-07: Unified Multi-Pipeline Worker Capability Negotiation (Align Studio vs TTS Studio)
   109	* **Observation**:
   110	  Currently, `lyrics-sync` claims align tasks via `POST /api/v1/align/worker/claim` with `capabilities: ["mps", "demucs_v4", "whisper_large_v3", ...]` and claims speech jobs via `POST /api/v1/speech/worker/claim`.
   111	  As the worker fleet handles both workloads simultaneously, the worker daemon requires a deterministic capability tag for Kokoro neural synthesis (`tts_kokoro_82m`) and multi-chunk audio stitching (`audio_stitcher`).
   112	* **Proposed Action**:
   113	  In `POST /api/v1/speech/worker/claim`, align the request payload schema with `POST /api/v1/align/worker/claim` by accepting an optional `capabilities: list[string]` field so the scheduler only routes Kokoro-targeted tasks to nodes with Apple Silicon MPS or CUDA acceleration enabled.
   114	* **Status**: `PROPOSED`.
   115	
   116	
   117	
   118	---
   119	
   120	## 2. Accepted RFCs & Architectural Decisions
   121	
   122	### RFC-001: 7-Step Canonical Pipeline & Subprocess Group Isolation
   123	* **Author**: `lyrics-sync` & `D3Nexus` Teams
   124	* **Date**: 2026-10-27
   125	* **Summary**:
   126	  Consolidated pipeline into 7 canonical sequential steps:
   127	  1. `media_ingest`
   128	  2. `vocal_separation`
   129	  3. `alignment_asr`
   130	  4. `semantic_resegment`
   131	  5. `translation`
   132	  6. `lexical_enrichment`
   133	  7. `artifact_export`
   134	  Pipeline runs in an isolated child process with its own process group (`os.setpgrp()`), enabling immediate SIGTERM -> SIGKILL cancellation in `< 50ms` upon operator abort.
   135	* **Status**: `IMPLEMENTED & VERIFIED`.
   136	
   137	---
   138	
   139	### RFC-002: Postel's Law Telemetry Deserialization (Defense-in-depth)
   140	* **Author**: `D3Nexus` & `lyrics-sync` Teams
   141	* **Date**: 2026-10-28
   142	* **Summary**:
   143	  To prevent HTTP 422 schema deserialization rejections during heartbeat dispatch:
   144	  - Worker standardizes all RAM and MPS memory metrics to integer megabytes using `round(...)`.
   145	  - D3Nexus control plane (`features/learning/domain/src/align/models.rs`) configures `mps_allocated_mb` and `mps_driver_allocated_mb` as `Option<f64>` and attaches `deserialize_flexible_u64` to `ram_used_mb` and `ram_total_mb`.
   146	* **Status**: `IMPLEMENTED & VERIFIED`.
   147	
   148	
   149	---
   150	
   151	## 3. D3Nexus Review & Feedback
   152	
   153	* **Review Date**: 2026-10-28
   154	* **Reviewer**: D3Nexus Engineering & AI Agent Team
   155	* **Referenced Commit**: `2a4e2ed0` (`develop`)
   156	
   157	### 3.1. Feedback on Open Gaps (GAP-01 to GAP-05)
   158	
   159	#### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
   160	* **D3Nexus Finding**: **CONFIRMED DEFECT / RISK**.
     1	# API & Protocol Data Contract: D3Nexus ⇄ nexus (Mobile App)
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference
     7	Audience: D3Nexus Control Plane & nexus Mobile Application Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.1.0
    10	-->
    11	
    12	## 1. Authentication & Protocol Headers
    13	
    14	The `nexus` mobile client communicates with the `D3Nexus` backend over HTTPS and Server-Sent Events (SSE).
    15	
    16	### 1.1. Common Client Request Headers
    17	Every request issued by the mobile application MUST include standard telemetry and client-identification headers:
    18	
    19	```http
    20	Authorization: Bearer <JWT_ACCESS_TOKEN>
    21	X-Device-Id: <UUID_V4_DEVICE_ID>
    22	X-Platform: <ios | android>
    23	X-App-Version: <SEMVER_STRING>
    24	Content-Type: application/json
    25	Accept: application/json
    26	```
    27	
    28	* `Authorization`: Standard OAuth2 Bearer token holding the short-lived access JWT (omitted only for unauthenticated guest session bootstrapping and login/registration).
    29	* `X-Device-Id` (`string`, required): Persistent unique client device identifier stored in secure hardware enclave (`flutter_secure_storage` backed by iOS Keychain / Android KeyStore).
    30	* `X-Platform` (`string`, required): Client operating system (`"ios"` or `"android"`).
    31	* `X-App-Version` (`string`, required): Application semantic release version (e.g. `"1.2.0"`).
    32	* `X-Guest-Session-Id` (`string`, optional): Transient guest session identifier for unauthenticated learners.
    33	
    34	---
    35	
    36	## 2. Authentication, Session & Device Security (`/api/v1/auth/...`)
    37	
    38	### 2.1. Account Registration (`POST /api/v1/auth/register`)
    39	Registers a new user account with credentials.
    40	
    41	* **Method**: `POST`
    42	* **Path**: `/api/v1/auth/register`
    43	* **Request Payload**:
    44	  ```json
    45	  {
    46	    "email": "learner@example.com",
    47	    "password": "SecurePassword123!",
    48	    "display_name": "Nguyen Van A"
    49	  }
    50	  ```
    51	* **Responses**:
    52	  * **`201 Created`**:
    53	    ```json
    54	    {
    55	      "account": {
    56	        "id": "c1f7a0b2-3e28-4e89-8d19-21b93f10111a",
    57	        "email": "learner@example.com",
    58	        "display_name": "Nguyen Van A",
    59	        "role": "Learner",
    60	        "created_at": 1793130000000
    61	      },
    62	      "access_token": "eyJhbGciOi...",
    63	      "refresh_token": "r_9983fa01...",
    64	      "token_type": "Bearer",
    65	      "expires_in": 3600
    66	    }
    67	    ```
    68	
    69	---
    70	
    71	### 2.2. Mobile Login (`POST /api/v1/auth/login`)
    72	Authenticates credentials and returns mobile JWT token pair.
    73	
    74	* **Method**: `POST`
    75	* **Path**: `/api/v1/auth/login`
    76	* **Request Payload**:
    77	  ```json
    78	  {
    79	    "email": "learner@example.com",
    80	    "password": "SecurePassword123!"
    81	  }
    82	  ```
    83	* **Responses**:
    84	  * **`200 OK`**: Returns token pair and user profile (same structure as 2.1).
    85	  * **`401 Unauthorized`**: `{"error": "invalid_credentials", "message": "Email or password incorrect"}`
    86	
    87	---
    88	
    89	### 2.3. Token Refresh (`POST /api/v1/auth/refresh`)
    90	Renews an expired access token using the rotating refresh token.
    91	
    92	* **Method**: `POST`
    93	* **Path**: `/api/v1/auth/refresh`
    94	* **Request Payload**:
    95	  ```json
    96	  {
    97	    "refresh_token": "r_9983fa01..."
    98	  }
    99	  ```
   100	* **Responses**:
   101	  * **`200 OK`**:
   102	    ```json
   103	    {
   104	      "access_token": "eyJhbGciOi...",
   105	      "refresh_token": "r_new_7721ab...",
   106	      "token_type": "Bearer",
   107	      "expires_in": 3600
   108	    }
   109	    ```
   110	  * **`401 Unauthorized`**: Refresh token revoked or expired. Mobile app redirects to login.
   111	
   112	---
   113	
   114	### 2.4. Current User Profile (`GET /api/v1/auth/me`)
   115	Retrieves the authenticated user's current account profile and settings.
   116	
   117	* **Method**: `GET`
   118	* **Path**: `/api/v1/auth/me`
   119	* **Headers**: `Authorization: Bearer <JWT>`
   120	* **Responses**:
   121	  * **`200 OK`**:
   122	    ```json
   123	    {
   124	      "account": {
   125	        "id": "c1f7a0b2-3e28-4e89-8d19-21b93f10111a",
   126	        "email": "learner@example.com",
   127	        "display_name": "Nguyen Van A",
   128	        "role": "Learner",
   129	        "created_at": 1793130000000
   130	      }
   131	    }
   132	    ```
   133	
   134	---
   135	
   136	### 2.5. Device Handshake & E2EE Public Key Registration (`POST /api/v1/auth/device/handshake`)
   137	Registers or updates device hardware enclave public keys for end-to-end encryption (Olm/Megolm) and encrypted push notification routing.
   138	
   139	* **Method**: `POST`
   140	* **Path**: `/api/v1/auth/device/handshake`
   141	* **Headers**: `Authorization: Bearer <JWT>`
   142	* **Request Payload**:
   143	  ```json
   144	  {
   145	    "device_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
   146	    "platform": "ios",
   147	    "app_version": "1.2.0",
   148	    "device_name": "iPhone 15 Pro",
   149	    "identity_key": "curve25519_pub_base64...",
   150	    "signing_key": "ed25519_pub_base64...",
   151	    "one_time_prekeys": [
   152	      {"key_id": 1, "public_key": "otpk_base64_001..."},
   153	      {"key_id": 2, "public_key": "otpk_base64_002..."}
   154	    ],
   155	    "push_token": "apns_or_fcm_token_sample"
   156	  }
   157	  ```
   158	* **Responses**:
   159	  * **`200 OK`**:
   160	    ```json
     1	# Architecture and System Flow Contract: D3Nexus ⇄ nexus (Mobile App)
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference & architectural explanation
     7	Audience: D3Nexus Control Plane & nexus Mobile Application Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.1.0
    10	-->
    11	
    12	## 1. System Roles & Responsibilities
    13	
    14	The ecosystem separates concerns between the central Control Plane and the edge-optimized Mobile Application:
    15	
    16	```text
    17	┌────────────────────────────────────────────────────────────────────────┐
    18	│                        D3Nexus Control Plane                           │
    19	│  - Axum / Tokio Rust High-Performance HTTP Engine                      │
    20	│  - Authoritative PostgreSQL Database (Catalog, Entitlements, FSRS)    │
    21	│  - Real-Time Server-Sent Events (SSE) Hub & AI Intent Execution        │
    22	│  - Audio Transcoding & Byte-Range HTTP 206 Streaming                   │
    23	│  - Multi-Device Vector Clock / HLC Conflict Resolution Gateway         │
    24	└───────────────────────────────────┬────────────────────────────────────┘
    25	                                    │ HTTPS REST + SSE Streaming
    26	                                    │ (Bearer JWT / Offline Delta Sync)
    27	                                    ▼
    28	┌────────────────────────────────────────────────────────────────────────┐
    29	│                      nexus Mobile Application                          │
    30	│  - Flutter Cross-Platform Client (iOS & Android)                       │
    31	│  - MVI (Model-View-Intent) Presentation Architecture                   │
    32	│  - Package-First Modular Monorepo (Melos)                              │
    33	│  - Offline-First Local Store (SQLite + Drift + Hive, < 16ms reads)     │
    34	│  - High-Precision 60fps Audio/Lyric Synchronization Canvas            │
    35	│  - Native Mobile Plugins: Low-Power Wake-Word & Low-Latency Audio Ring │
    36	│  - Rust Core FFI: Spaced Repetition (FSRS-4.5), E2EE Olm/Megolm Crypto │
    37	└────────────────────────────────────────────────────────────────────────┘
    38	```
    39	
    40	### 1.1. Core Architectural Invariants
    41	1. **Offline Autonomy & Local-First Authority**: The `nexus` mobile app is fully functional without network connectivity. All UI reads (Today tasks, cached tracks, flashcard queues) query local storage first for `< 16ms` zero-latency rendering.
    42	2. **Deterministic Synchronization via HLC**: All local database mutations are recorded in a persistent `Outbox` stamped with Hybrid Logical Clock (HLC) timestamps (`physicalMillis + logicalCounter + deviceId`), guaranteeing causal order without wall-clock skew.
    43	3. **Smooth 60fps Canvas Rendering**: Lyric animation engines decouple audio clock ticks from UI rendering loops, utilizing lerp interpolation between millisecond word bounds (`startMs` / `endMs`).
    44	4. **Single Source of Schema Truth**: The `lyrics-sync/v1` document schema authored by the worker and stored in `D3Nexus` is directly consumed by Flutter `LyricsApiClient` and deserialized without intermediate reshaping.
    45	5. **Rust Core for Heavy Invariants**: FSRS scheduling algorithms, Olm/Megolm double-ratchet state, and sensitive cryptography execute strictly in the shared Rust core via FFI, guaranteeing identical math and security semantics across platforms.
    46	
    47	---
    48	
    49	## 2. Package-First Modular Structure (`nexus`)
    50	
    51	The `nexus` codebase enforces strict layer boundaries across decoupled packages:
    52	
    53	```text
    54	packages/
    55	├── core/                  # Pure utilities, extensions, functional primitives
    56	├── framework/             # Base MVI classes (MviBloc, BaseAction, BaseState, BaseEvent)
    57	├── network/               # Dio HTTP client, Auth token interceptor, SSL pinning
    58	├── ui_kit/                # Living design system tokens, typography, colors
    59	├── learning_store/        # Local SQLite cache, HLC clock, Outbox sync gateway
    60	├── learning_client/       # FSRS spaced-repetition scheduler & review reducer
    61	├── media_player/          # Just_audio wrapper with HTTP 206 range buffer
    62	└── native_security/       # Secure enclave storage & biometric key storage
    63	
    64	features/
    65	├── authentication/        # Mobile login, biometric prompt, token lifecycle
    66	├── lyrics_player/         # Dual-stage player, 60fps karaoke canvas, catalog
    67	├── cards/                 # Kho flashcard deck management & collocation editor
    68	└── vocab/                 # Spaced repetition review runner & quiz session
    69	```
    70	
    71	---
    72	
    73	## 3. Offline-First Synchronization & Conflict Resolution
    74	
    75	### 3.1. Local Outbox Mutation Pipeline
    76	
    77	```text
    78	 User Action (e.g. Save Card / Toggle Task / Submit Review)
    79	                     │
    80	                     ▼
    81	  1. Generate UUIDv7 + Current HLC Timestamp
    82	     hlc = HLC.now(nodeId: device_id)
    83	                     │
    84	                     ▼
    85	  2. Write to Local SQLite Cache (Immediate UI State Update < 16ms)
    86	                     │
    87	                     ▼
    88	  3. Append to Outbox Table (Transactional Atomicity)
    89	     INSERT INTO outbox_entries (id, hlc, action, entity_type, payload)
    90	                     │
    91	         [Network Connected?]
    92	            /             \
    93	        [Yes]             [No]
    94	          │                 │
    95	          ▼                 ▼
    96	  Dispatch Sync Request   Retain in Outbox
    97	  POST /learning/sync/outbox (Retried via Connectivity Observer)
    98	```
    99	
   100	### 3.2. Conflict Resolution Policy (Last-Write-Wins via HLC)
   101	When mutations from multiple devices collide on the server:
   102	
   103	1. **Card & Task Edits**: The server compares the mutation `HLC` strings. Because HLC is monotonically increasing and incorporates node identity, the strictly greater HLC wins (`last-write-wins`).
   104	2. **Deletions (Tombstones)**: Deletion is recorded as an `OutboxAction::delete` mutation with a tombstone marker. A tombstone with a higher HLC overrides previous saves or edits.
   105	3. **Flashcard Reviews**: Reviews are **append-only logs**. Multiple reviews from different devices are merged and re-fed into the FSRS scheduler, computing an updated stability and interval without data loss.
   106	
   107	---
   108	
   109	## 4. Audio-Lyric 60fps Synchronization & 1-Tap Mining Flow
   110	
   111	### 4.1. High-Performance Playback & Highlighting Loop
   112	
   113	```text
   114	 Native Audio Engine (just_audio / CoreAudio / AAudio)
   115	                     │
   116	                     ▼ Stream position tick (~10-20ms jitter)
   117	   Interpolated Frame Clock (TickerProvider / SchedulerBinding)
   118	                     │
   119	                     ▼ Smoothed target timestamp: t_current
   120	        Binary Search Active Line (lines[].startMs <= t <= lines[].endMs)
   121	                     │
   122	                     ▼ Find Active Word (words[].startMs <= t <= words[].endMs)
   123	  Render Smooth Progress Gradient on Karaoke Canvas (60 - 120 fps)
   124	```
   125	
   126	### 4.2. 1-Tap Collocation Mining Flow
   127	
   128	```text
   129	 User Taps Word / Collocation Chip in Lyrics View
   130	                     │
   131	                     ▼
   132	  Query Local Memory Map for `all_collocations` Match
   133	  (Matches occurrence by line_id and character spans)
   134	                     │
   135	                     ▼
   136	  Display Glassmorphic Bottom Popover / Sheet
   137	  - Canonical phrase & spoken title
   138	  - CEFR Badge & IPA pronunciation
   139	  - Bilingual definition & grammatical pattern
   140	  - Sentence context with {{highlight_mask}}
   141	                     │
   142	                     ▼ User Taps "Save to Kho" (1-Tap Action)
   143	  Construct CardDraft -> Validate Bounds (Phrase <= 80, Sentence <= 500)
   144	                     │
   145	                     ▼
   146	  Commit to Local Cache & Queue Outbox Entry
   147	                     │
   148	                     ▼
   149	  Haptic Feedback (Light Impact) + Toast Confirmation
   150	```
     1	# Gaps, Open Inquiries & RFCs: D3Nexus ⇄ nexus (Mobile App)
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference & collaboration log
     7	Audience: D3Nexus Control Plane & nexus Mobile Application Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.1.0
    10	-->
    11	
    12	This document serves as the formal asynchronous Request For Change (RFC) and communication ledger between the AI Agents and engineers developing `nexus` (Mobile Client) and `D3Nexus` (Control Plane).
    13	
    14	---
    15	
    16	## 1. Identified Gaps & Alignment Inquiries
    17	
    18	### GAP-NEX-01: HTTP 206 Partial Content (Byte-Range) Support for Audio Seeking
    19	* **Observation**:
    20	  Mobile audio playback engines (iOS `AVPlayer` and Android `ExoPlayer` / `Media3` used by `just_audio` in `packages/media_player`) require strict HTTP 206 byte-range handling. When scrubbing the playback timeline or resuming playback from a word index, the player dispatches `Range: bytes=START-END` or `Range: bytes=START-`.
    21	* **Current Behavior**:
    22	  `D3Nexus` serves media via `learning_media::media_streaming_router`. If the server returns HTTP 200 with the full file stream instead of HTTP 206 with `Content-Range: bytes START-END/TOTAL`, mobile players on iOS will fail seeking or buffer the entire file repeatedly.
    23	* **Proposed Action for D3Nexus**:
    24	  Verify and ensure that `apps/server` media streaming handlers explicitly handle `Range` headers, return `HTTP 206 Partial Content`, `Accept-Ranges: bytes`, and the accurate `Content-Range` header.
    25	* **Status**: `OPEN` (Requires verification against `learning_media` router).
    26	
    27	---
    28	
    29	### GAP-NEX-02: Mixed Timestamp Serialization (`i64` Epoch ms vs ISO-8601 Strings)
    30	* **Observation**:
    31	  `nexus` client models (e.g. `outbox_entry.dart`) serialize mutation timestamps as ISO-8601 UTC strings (`2026-10-29T10:15:30.120Z`). Conversely, `D3Nexus` backend models in PostgreSQL and Axum handlers often serialize timestamps as `i64` integer epoch milliseconds (`1793130000000`).
    32	* **Current Behavior**:
    33	  Deserialization errors (`invalid type: string, expected i64`) can occur if contracts do not define a dual-mode parser.
    34	* **Proposed Action**:
    35	  - D3Nexus backend should use a Serde helper (`deserialize_flexible_timestamp`) that accepts both integer milliseconds and ISO-8601 UTC strings.
    36	  - In `nexus` Dart DTOs, deserialize timestamps using a utility that checks `if (val is int) DateTime.fromMillisecondsSinceEpoch(val) else DateTime.parse(val)`.
    37	* **Status**: `OPEN` (Recommended for implementation across both sides).
    38	
    39	---
    40	
    41	### GAP-NEX-03: Client-Generated UUIDv7 Acceptance for Offline Entity Creation
    42	* **Observation**:
    43	  When a user creates a new flashcard or records an outbox mutation offline, `nexus` generates a UUIDv7 on device (`018f921a-7b3c-7411-921a-883a992b1001`) to ensure chronological index ordering in SQLite.
    44	* **Proposed Action for D3Nexus**:
    45	  `POST /api/v1/learning/cards` and `POST /api/v1/learning/sync/outbox` must preserve and persist the client-provided `id` if valid UUID, rather than unconditionally generating a new `Uuid::new_v4()` on the server. If an ID already exists with the same natural key, perform idempotent upsert.
    46	* **Status**: `PROPOSED`.
    47	
    48	---
    49	
    50	### GAP-NEX-04: Concurrent Request Token Refresh Grace Window
    51	* **Observation**:
    52	  When an access token expires while the mobile client initiates multiple parallel queries (e.g. fetching `/today/overview`, `/lyrics/shelves`, and `/cards/due` simultaneously), all three requests fail with HTTP 401.
    53	  The Dio interceptor initiates token rotation (`POST /api/v1/auth/refresh`). If a second request hits the refresh endpoint before the first completes, standard single-use refresh token rotation can invalidate the session and force an abrupt logout.
    54	* **Proposed Action for D3Nexus**:
    55	  In `identity_domain::usecase::refresh`, implement a brief **10-second grace window** where an old refresh token remains temporarily valid to complete concurrent requests from the same `device_id`.
    56	* **Status**: `PROPOSED`.
    57	
    58	---
    59	
    60	### GAP-NEX-05: CORS & Custom Mobile Telemetry Headers
    61	* **Observation**:
    62	  The mobile client includes custom headers (`X-Device-Id`, `X-Platform`, `X-App-Version`, `X-Guest-Session-Id`). While native iOS/Android HTTP bypasses browser CORS, web builds and Flutter Web integration tests enforce strict CORS pre-flight (`OPTIONS`).
    63	* **Proposed Action for D3Nexus**:
    64	  Ensure `build_cors_layer` in `apps/server/src/wiring.rs` includes these four custom headers in `allowed_headers`.
    65	* **Status**: `ACCEPTED & READY`.
    66	
    67	---
    68	
    69	### GAP-NEX-06: Response Envelope Discrepancy (`BaseResponseObject` vs Raw Payload)
    70	* **Observation**:
    71	  In `features/authentication/lib/data/datasources/remote/auth_client.dart`, endpoints expect responses wrapped in `BaseResponseObject<T>` with `{ "code": "0000", "message": "...", "data": T }`. However, `D3Nexus` server endpoints return raw JSON payloads (e.g. `{"account": {...}, "access_token": "..."}`).
    72	* **Current Behavior**:
    73	  If `D3Nexus` returns a raw JSON payload, `BaseResponseObject.fromJson` fails because `code` and `data` fields are null.
    74	* **Proposed Action**:
    75	  Standardize on REST best practice: `D3Nexus` continues returning standard HTTP status codes (`200 OK`, `201 Created`) with raw body. The mobile `Dio` layer or Retrofit converter must detect whether the response has a `data` envelope or is raw, and deserialize seamlessly via an adapter.
    76	* **Status**: `OPEN` (Action required in mobile networking layer).
    77	
    78	---
    79	
    80	### GAP-NEX-07: Token Pair Response Key Mappings
    81	* **Observation**:
    82	  Mobile DTO `TokenPairResponse` in `features/authentication` declares fields:
    83	  - `access`
    84	  - `refresh`
    85	  - `access_expires_in`
    86	  - `token_type`
    87	  While `D3Nexus` contract in `api_contract.md` specifies:
    88	  - `access_token`
    89	  - `refresh_token`
    90	  - `expires_in`
    91	  - `token_type`
    92	* **Current Behavior**:
    93	  JsonSerializable throws `MissingRequiredKeysException` if server keys do not match mobile DTO annotations.
    94	* **Proposed Action**:
    95	  Update `TokenPairResponse` in `features/authentication` to support fallback/alias annotations:
    96	  `@JsonKey(readValue: _readAccessToken)` or support both `access_token` and `access`.
    97	* **Status**: `OPEN`.
    98	
    99	---
   100	
   101	### GAP-NEX-08: E2EE Olm/Megolm Key Exchange & Push Encrypted Payload Format
   102	* **Observation**:
   103	  When D3Nexus dispatches background sync or notification events to `nexus`, sensitive content (personal tasks, private flashcard reviews) should be end-to-end encrypted for the user's registered devices.
   104	* **Proposed Action**:
   105	  Establish the encrypted push payload schema:
   106	  ```json
   107	  {
   108	    "type": "e2ee_event",
   109	    "sender_device_id": "...",
   110	    "session_id": "...",
   111	    "ciphertext": "base64_encoded_megolm_message...",
   112	    "mac": "base64_hmac..."
   113	  }
   114	  ```
   115	  Native mobile extensions (`UNNotificationServiceExtension` / `FirebaseMessagingService`) call Rust FFI directly to decrypt and insert into local SQLite before notifying the OS.
   116	* **Status**: `PROPOSED`.
   117	
   118	---
   119	
   120	### GAP-NEX-09: Task & Habit Sync Schema Alignment
   121	* **Observation**:
   122	  `nexus` local task tracking includes offline-first attributes (`is_dirty`, `version`, `client_hlc`, `priority`, `due_at_ms`). `D3Nexus` needs to accept task mutations through `POST /api/v1/learning/sync/outbox` with `entity_type: "task"`.
   123	* **Proposed Action**:
   124	  Ensure D3Nexus sync service routes `task` and `habit_log` mutation entities into the PostgreSQL user task table.
   125	* **Status**: `PROPOSED`.
   126	
   127	---
   128	
   129	### GAP-NEX-10: SSE Assistant Intent Action Protocol & Reconnection with `Last-Event-ID`
   130	* **Observation**:
   131	  Mobile network handoffs (Wi-Fi to 5G) drop SSE streams mid-sentence.
   132	* **Proposed Action**:
   133	  - `POST /api/v1/assistant/stream` must emit `id: <monotonic_counter>` with each event.
   134	  - The mobile client must include `Last-Event-ID: <last_seen_id>` when reconnecting to resume the stream without repeating tokens or dropping actions.
   135	* **Status**: `ACCEPTED`.
   136	
   137	---
   138	
   139	## 2. Accepted RFCs & Architectural Standards
   140	
   141	### RFC-NEX-001: Hybrid Logical Clock (HLC) Causal Ordering
   142	* **Author**: `D3Nexus` & `nexus` Architecture Teams
   143	* **Date**: 2026-10-29
   144	* **Summary**:
   145	  Adopted the Hybrid Logical Clock algorithm for offline-first delta synchronization. HLC strings formatted as `<iso_timestamp>-<logical_counter>-<node_id>` provide strictly monotonic causal order across offline devices and eliminate wall-clock drift issues.
   146	* **Status**: `ACCEPTED`.
   147	
   148	---
   149	
   150	### RFC-NEX-002: Postel's Law for 60fps Lyrics Timings
   151	* **Author**: `D3Nexus` & `nexus` Teams
   152	* **Date**: 2026-10-29
   153	* **Summary**:
   154	  The `lyrics-sync/v1` document schema delivers word and line timing properties using camelCase (`startMs`, `endMs`, `durationMs`). Flutter mobile client directly parses these fields into high-speed primitive integer arrays to maximize 60fps-120fps canvas rendering performance.
   155	* **Status**: `ACCEPTED`.
   156	
   157	---
   158	
   159	### RFC-NEX-003: 10-Field Lexical Chunk Canonical Model in `all_collocations`
   160	* **Author**: `nexus` Mobile Team

exec
/bin/zsh -lc "rg -n 'protected|Protected' skills/dev-implementation/resources/scripts/check_epic_readiness.py skills/dev-implementation/resources/scripts/audit_epic.py skills/dev-implementation/SKILL.md; nl -ba skills/setup-shared-contracts/resources/scripts/setup_contracts.py | sed -n '260,365p'; nl -ba skills/using-git-worktrees/SKILL.md | sed -n '64,100p'; nl -ba skills/dev-implementation/SKILL.md | sed -n '130,169p'; nl -ba ../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md | sed -n '1,105p'; nl -ba ../D3Nexus/shared-contracts/nexus/api_contract.md | sed -n '1,75p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
skills/dev-implementation/SKILL.md:200:   > 5. **Stop and Report**: A `Stop and Report If` condition in task is reported as `BLOCKED`. Never edit Verification table, Definition of Done, Allowed files or Covers line, or protected path, to force a pass. In Satellite Mode, report `BLOCKED` if an unmerged upstream contract change prevents local tests from passing.
skills/dev-implementation/SKILL.md:331:2. **Present Executive Summary**: Output summary containing epic slug, worktree path, completed tasks, `@quality_check` verdict, BDD matrix, and audit disclosure sections (Evidence, Protected paths, Commits outside tasks, Gate 5 items).
skills/dev-implementation/resources/scripts/audit_epic.py:8:PASS, or an unauthorised protected change outside .devtool/; 2 usage error (unknown base, no epic).
skills/dev-implementation/resources/scripts/audit_epic.py:39:parse_protected_paths: Any = tc.parse_protected_paths
skills/dev-implementation/resources/scripts/audit_epic.py:49:GRADER_LINES = ("Protected paths:", "Integration results:")
skills/dev-implementation/resources/scripts/audit_epic.py:151:def audit_protected(root: Path, epic_path: str, commits: list[Commit], texts: dict[str, str]) -> tuple[list[str], bool]:
skills/dev-implementation/resources/scripts/audit_epic.py:152:    explicit = parse_protected_paths(show(root, "HEAD", f"{epic_path}/{Path(epic_path).name}.en.md") or "")
skills/dev-implementation/resources/scripts/audit_epic.py:211:    """The HLD's Protected paths: and Integration results: lines, diffed between <base> and HEAD."""
skills/dev-implementation/resources/scripts/audit_epic.py:220:    return ["\n  ".join([f"{Path(hld).name}: Protected paths or Integration results changed since base", *diff,
skills/dev-implementation/resources/scripts/audit_epic.py:245:    protected, bad = audit_protected(root, epic_path, commits, texts)
skills/dev-implementation/resources/scripts/audit_epic.py:250:    sections = [("Evidence", evidence), ("Legacy tasks", legacy), ("Protected paths", protected),
   260	
   261	    # 1. Validate Hub directory and domain presence
   262	    hub_resolved = hub.resolve()
   263	    shared_contracts_hub = (hub_resolved / "shared-contracts").resolve()
   264	    hub_domain_dir = shared_contracts_hub / norm_domain
   265	
   266	    if not hub_domain_dir.is_dir():
   267	        sys.stderr.write(
   268	            f"ERROR [SSC-FR-02]: Target domain '{norm_domain}' not found in Hub at '{hub_resolved}'.\n"
   269	            f"Expected directory: '{hub_domain_dir}'\n"
   270	        )
   271	        return 1
   272	
   273	    hub_domain_resolved = hub_domain_dir.resolve()
   274	    if not hub_domain_resolved.is_relative_to(shared_contracts_hub):
   275	        sys.stderr.write(
   276	            f"ERROR: Target domain '{norm_domain}' resolves outside Hub shared-contracts: '{hub_domain_resolved}'.\n"
   277	        )
   278	        return 1
   279	
   280	    satellite_root_resolved = satellite_root.resolve()
   281	    shared_contracts_link = satellite_root_resolved / "shared-contracts"
   282	
   283	    # 2. Pre-flight guard: prevent self-referential linking and Hub erasure
   284	    if satellite_root_resolved == hub_resolved:
   285	        sys.stderr.write(
   286	            f"ERROR: Satellite root and Hub root must be distinct repositories: '{satellite_root_resolved}'.\n"
   287	        )
   288	        return 1
   289	
   290	    if shared_contracts_link.exists() and not (
   291	        shared_contracts_link.is_symlink() or os.path.islink(shared_contracts_link)
   292	    ):
   293	        link_resolved = shared_contracts_link.resolve()
   294	        if (
   295	            link_resolved == shared_contracts_hub
   296	            or hub_domain_resolved == link_resolved
   297	            or hub_domain_resolved.is_relative_to(link_resolved)
   298	        ):
   299	            sys.stderr.write(
   300	                "ERROR: Target Satellite contracts path conflicts with or contains Hub contracts; "
   301	                "refusing overwrite to prevent Hub repository erasure.\n"
   302	            )
   303	            return 1
   304	
   305	    # 3. Check existing path at target
   306	    if shared_contracts_link.is_symlink() or os.path.islink(shared_contracts_link):
   307	        pass  # Will be atomically replaced via temporary sibling symlink
   308	    elif shared_contracts_link.is_dir():
   309	        has_entries = any(shared_contracts_link.iterdir())
   310	        if has_entries and not force:
   311	            sys.stderr.write(
   312	                "ERROR [SSC-FR-03]: Target 'shared-contracts' is an existing non-empty physical directory.\n"
   313	                "Refusing overwrite without --force to prevent uncommitted file loss.\n"
   314	            )
   315	            return 1
   316	        shutil.rmtree(shared_contracts_link)
   317	    elif shared_contracts_link.exists():
   318	        if not force:
   319	            sys.stderr.write(
   320	                "ERROR [SSC-FR-03]: Target 'shared-contracts' exists and is not a symlink.\n"
   321	                "Refusing overwrite without --force.\n"
   322	            )
   323	            return 1
   324	        shared_contracts_link.unlink()
   325	
   326	    # 3. Compute relative target and create symlink atomically
   327	    rel_target = os.path.relpath(hub_domain_dir, satellite_root_resolved)
   328	    tmp_link = satellite_root_resolved / f".tmp_link_{uuid.uuid4().hex}"
   329	    try:
   330	        os.symlink(rel_target, tmp_link)
   331	        os.replace(tmp_link, shared_contracts_link)
   332	    except Exception:
   333	        if tmp_link.is_symlink() or os.path.islink(tmp_link) or tmp_link.exists():
   334	            try:
   335	                tmp_link.unlink()
   336	            except OSError:
   337	                pass
   338	        raise
   339	
   340	    if not shared_contracts_link.exists():
   341	        sys.stderr.write(
   342	            f"ERROR: Created symbolic link is dangling: '{shared_contracts_link}' -> '{rel_target}'.\n"
   343	        )
   344	        return 1
   345	
   346	    # 4. Install Satellite local rule .agents/rules/contract_rules.md
   347	    rules_dir = satellite_root_resolved / ".agents" / "rules"
   348	    rules_dir.mkdir(parents=True, exist_ok=True)
   349	    contract_rules_path = rules_dir / "contract_rules.md"
   350	    template_vars = {
   351	        "hub_repo": hub_resolved.name or "D3Nexus",
   352	        "domain": norm_domain,
   353	        "timestamp": _get_timestamp(),
   354	    }
   355	    rule_tmpl = _load_template("satellite_rule.md.tmpl")
   356	    atomic_write_text(contract_rules_path, rule_tmpl.substitute(template_vars))
   357	
   358	    # 5. Check if AGENTS.md exists and append reference if needed
   359	    agents_md_path = satellite_root_resolved / "AGENTS.md"
   360	    if agents_md_path.is_file():
   361	        agents_content = agents_md_path.read_text(encoding="utf-8")
   362	        rule_reference = "@.agents/rules/contract_rules.md"
   363	        if rule_reference not in agents_content:
   364	            updated_content = agents_content.rstrip() + f"\n\n{rule_reference}\n"
   365	            atomic_write_text(agents_md_path, updated_content)
    64	
    65	Follow this priority order. Explicit user preference always beats observed filesystem state.
    66	
    67	1. **Check your instructions for a declared worktree directory preference.** If the user has already specified one, use it without asking.
    68	
    69	2. **Check for an existing project-local worktree directory:**
    70	   ```bash
    71	   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
    72	   ls -d worktrees 2>/dev/null      # Alternative
    73	   ```
    74	   If found, use it. If both exist, `.worktrees` wins.
    75	
    76	3. **If there is no other guidance available**, default to `.worktrees/` at the project root.
    77	
    78	#### Safety Verification (project-local directories only)
    79	
    80	**MUST verify directory is ignored before creating worktree:**
    81	
    82	```bash
    83	git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
    84	```
    85	
    86	**If NOT ignored:** Add to .gitignore, commit the change, then proceed.
    87	
    88	**Why critical:** Prevents accidentally committing worktree contents to repository.
    89	
    90	#### Create the Worktree
    91	
    92	```bash
    93	# Determine path based on chosen location
    94	path="$LOCATION/$BRANCH_NAME"
    95	
    96	git worktree add "$path" -b "$BRANCH_NAME"
    97	cd "$path"
    98	```
    99	
   100	**Sandbox fallback:** If `git worktree add` fails with a permission error (sandbox denial), tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.
   130	     --tasks .devtool/epic/<epic_dir>/task_*.md
   131	   ```
   132	   If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.
   133	
   134	   Then check task contract:
   135	   ```bash
   136	   python3 "$SKILL_DIR"/resources/scripts/check_task_contract.py \
   137	     --hld .devtool/epic/<epic_dir>/<epic_dir>.en.md \
   138	     --tasks .devtool/epic/<epic_dir>/task_*.md
   139	   ```
   140	   Do not create worktree until both checks exit 0 and developer has confirmed the order.
   141	
   142	#### Phase 1 (continued) — Worktree Bootstrap, once the order is confirmed
   143	
   144	4. Bring local `develop` up to date with upstream, then create one worktree for whole epic (`d3nexus:using-git-worktrees`):
   145	   ```bash
   146	   python3 "$INTEGRATE" sync-base --base develop
   147	   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   148	   ```
   149	   If `sync-base` exits 3 (diverged or dirty file), stop and ask.
   150	   If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
   151	5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
   152	6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
   153	
   154	### Phase 2 — Sequential Task Execution
   155	
   156	For each task in confirmed order, follow `d3nexus:subagent-driven-development`.
   157	
   158	0. **Pre-Edit Verification (Impact & Conflict Check)**:
   159	   ```bash
   160	   python3 skills/impact-analysis/resources/scripts/check_code_impact.py \
   161	     --files <target_files> \
   162	     --symbols <target_symbols> \
   163	     --base-ref <base_ref>
   164	   ```
   165	   - If `🔴 DIVERGENCE DETECTED`: **HALT IMMEDIATELY**. Run step 7 (Integrate with develop) now, then rerun check.
   166	   - If `⚠️ UNPROTECTED CODE (0% Coverage)`: Author baseline characterization unit tests first.
   167	
   168	1. **Live Dual-Workspace Kanban Status (In-Progress)**:
   169	   ```bash
     1	# Gaps, Open Inquiries & RFCs: D3Nexus ⇄ lyrics-sync
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference & collaboration log
     7	Audience: D3Nexus Control Plane & lyrics-sync Worker Fleet Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.0.0
    10	-->
    11	
    12	This document serves as the formal asynchronous Request For Change (RFC) and communication ledger between the AI Agents and engineers developing `lyrics-sync` and `D3Nexus`.
    13	
    14	---
    15	
    16	## 1. Open Gaps & Alignment Questions (For D3Nexus Confirmation)
    17	
    18	### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
    19	* **Observation**:
    20	  Full alignment payloads containing word-level timestamps (`Word`), bilingual sentence translations, and comprehensive 10-field lexical chunks (`all_collocations`) can range from `500 KB` to `5 MB` for long videos (e.g. 10-15 minute speeches or audio tracks). Axum's default `DefaultBodyLimit` is `2 MB`.
    21	* **Current Behavior**:
    22	  For standard 3-5 minute songs, payloads remain under 1MB. However, long-form content may be rejected with `HTTP 413 Payload Too Large`.
    23	* **Proposed Action for D3Nexus**:
    24	  Ensure the Axum router configures an explicit body limit for the completion endpoint in `apps/server/src/align/routes.rs`:
    25	  ```rust
    26	  .route("/api/v1/align/worker/tasks/:id/complete", post(complete_task))
    27	  .layer(axum::extract::DefaultBodyLimit::max(10 * 1024 * 1024)) // 10 MB limit
    28	  ```
    29	* **Status**: `OPEN` (Awaiting D3Nexus confirmation).
    30	
    31	---
    32	
    33	### GAP-02: Mixed Timestamp Key Formats (`startMs` vs `start_ms`)
    34	* **Observation**:
    35	  In `lyrics-sync/v1`, line and word timestamps use camelCase (`startMs`, `endMs`, `durationMs`) adhering to the committed JSON schema (`schema/lyrics-sync.v1.schema.json`). However, inside `all_collocations[].occurrences`, timestamps use snake_case (`start_ms`, `end_ms`).
    36	* **Current Behavior**:
    37	  Both are supported by Python Pydantic models via `populate_by_name = True` and validation aliases.
    38	* **Proposed Action for D3Nexus**:
    39	  In Rust Serde structs (`learning_domain::align::models`), ensure fields support both naming variants using Serde aliases:
    40	  ```rust
    41	  #[derive(Debug, Deserialize, Serialize)]
    42	  pub struct WordTimestamp {
    43	      pub text: String,
    44	      #[serde(alias = "start_ms", alias = "startMs")]
    45	      pub start_ms: u64,
    46	      #[serde(alias = "end_ms", alias = "endMs")]
    47	      pub end_ms: u64,
    48	      pub score: Option<f64>,
    49	  }
    50	  ```
    51	* **Status**: `OPEN` (Documented in API Contract; recommend Serde alias in D3Nexus).
    52	
    53	---
    54	
    55	### GAP-03: Co-Located Media Path vs Remote Media URL Resolution
    56	* **Observation**:
    57	  `POST /claim` returns both `media_url` (remote web/YouTube URL) and `media_file_path` (local filesystem path).
    58	  When worker and server run on the same physical host (e.g. developer Mac Mini), the worker can directly process `media_file_path`, completely skipping network download and rate-limits.
    59	* **Current Behavior**:
    60	  `lyrics_sync.worker.bridge` prefers `media_file_path` if the file exists on the local filesystem; otherwise, it falls back to `media_url`.
    61	* **Proposed Action for D3Nexus**:
    62	  When creating alignment tasks on D3Nexus, if the source media was uploaded by the user to local disk storage, populate `media_file_path` with the absolute local path.
    63	* **Status**: `ACCEPTED` (Implemented in Worker; D3Nexus should preserve `media_file_path`).
    64	
    65	---
    66	
    67	### GAP-04: Worker Token Authentication for Fleet Monitoring (`GET /api/v1/align/fleet`)
    68	* **Observation**:
    69	  Currently, `GET /api/v1/align/fleet` requires an authenticated web user cookie/session in D3Nexus, returning `HTTP 401 Unauthorized` when queried using `X-Worker-Token`.
    70	  As a result, CLI inspection commands (`lyrics-sync worker top`) running on worker nodes cannot query cluster-wide fleet status using their worker token.
    71	* **Proposed Action for D3Nexus**:
    72	  Update the authentication middleware in D3Nexus for `/api/v1/align/fleet` to accept either:
    73	  1. An authenticated user session, OR
    74	  2. A valid `X-Worker-Token` matching `D3N_WORKER_SECRET_TOKEN`.
    75	* **Status**: `OPEN` (Requested for worker fleet CLI management).
    76	
    77	---
    78	
    79	### GAP-05: Server Restart Orphaned Task Reclaim Hook
    80	* **Observation**:
    81	  When D3Nexus restarts while tasks are in `claimed` state, those tasks remain locked until the 900-second lease expires via the background `lease_reaper`.
    82	* **Proposed Action for D3Nexus**:
    83	  On startup of the D3Nexus server, execute an initial pass of `lease_reaper` or check if the worker heartbeat has timed out, allowing quicker reclamation of interrupted tasks.
    84	* **Status**: `PROPOSED`.
    85	
    86	---
    87	
    88	### GAP-06: Fleet Status Missing Active Pipeline Step (`current_step` in `GET /api/v1/align/fleet`)
    89	* **Observation**:
    90	  `lyrics-sync worker top` displays a dedicated `STEP` column to show the active canonical step (e.g. `media_ingest`, `vocal_separation`, `alignment_asr`, `semantic_resegment`, etc.).
    91	  However, `GET /api/v1/align/fleet` returns `WorkerInfo` records sourced from `media_align_workers`, which does not contain `current_step` or query the active step.
    92	  As a result, `worker top` on the Terminal displays `-` in the `STEP` column for busy nodes.
    93	* **Resolution / Proposed Action**:
    94	  1. **`lyrics-sync` Client**: Enriched `worker top` to load `~/.lyrics_sync/worker_status.json` and merge `current_step` for matching local worker daemon instances.
    95	  2. **`D3Nexus` Server Proposal**: In `features/learning/data/src/align/repository.rs` (`list_workers`), enrich `WorkerInfo` by querying the latest step for `current_task_id`:
    96	     ```sql
    97	     SELECT worker_id, host_name, ip_address, hardware,
    98	            status, current_task_id, metrics_json, last_heartbeat_at, registered_at,
    99	            (SELECT step_name FROM media_align_step_logs WHERE task_id = media_align_workers.current_task_id ORDER BY created_at DESC LIMIT 1) AS current_step
   100	     FROM media_align_workers
   101	     ORDER BY registered_at ASC
   102	     ```
   103	     and add `pub current_step: Option<String>` to `WorkerInfo` in `features/learning/domain/src/align/models.rs`.
   104	* **Status**: `PROPOSED` (Implemented local enrichment in Worker CLI; awaiting D3Nexus contract approval).
   105	
     1	# API & Protocol Data Contract: D3Nexus ⇄ nexus (Mobile App)
     2	
     3	<!--
     4	Meta Data:
     5	Kind: document
     6	Diátaxis mode: reference
     7	Audience: D3Nexus Control Plane & nexus Mobile Application Engineers and AI Agents
     8	Status: Canonical Single Source of Truth (SSOT)
     9	Version: 1.1.0
    10	-->
    11	
    12	## 1. Authentication & Protocol Headers
    13	
    14	The `nexus` mobile client communicates with the `D3Nexus` backend over HTTPS and Server-Sent Events (SSE).
    15	
    16	### 1.1. Common Client Request Headers
    17	Every request issued by the mobile application MUST include standard telemetry and client-identification headers:
    18	
    19	```http
    20	Authorization: Bearer <JWT_ACCESS_TOKEN>
    21	X-Device-Id: <UUID_V4_DEVICE_ID>
    22	X-Platform: <ios | android>
    23	X-App-Version: <SEMVER_STRING>
    24	Content-Type: application/json
    25	Accept: application/json
    26	```
    27	
    28	* `Authorization`: Standard OAuth2 Bearer token holding the short-lived access JWT (omitted only for unauthenticated guest session bootstrapping and login/registration).
    29	* `X-Device-Id` (`string`, required): Persistent unique client device identifier stored in secure hardware enclave (`flutter_secure_storage` backed by iOS Keychain / Android KeyStore).
    30	* `X-Platform` (`string`, required): Client operating system (`"ios"` or `"android"`).
    31	* `X-App-Version` (`string`, required): Application semantic release version (e.g. `"1.2.0"`).
    32	* `X-Guest-Session-Id` (`string`, optional): Transient guest session identifier for unauthenticated learners.
    33	
    34	---
    35	
    36	## 2. Authentication, Session & Device Security (`/api/v1/auth/...`)
    37	
    38	### 2.1. Account Registration (`POST /api/v1/auth/register`)
    39	Registers a new user account with credentials.
    40	
    41	* **Method**: `POST`
    42	* **Path**: `/api/v1/auth/register`
    43	* **Request Payload**:
    44	  ```json
    45	  {
    46	    "email": "learner@example.com",
    47	    "password": "SecurePassword123!",
    48	    "display_name": "Nguyen Van A"
    49	  }
    50	  ```
    51	* **Responses**:
    52	  * **`201 Created`**:
    53	    ```json
    54	    {
    55	      "account": {
    56	        "id": "c1f7a0b2-3e28-4e89-8d19-21b93f10111a",
    57	        "email": "learner@example.com",
    58	        "display_name": "Nguyen Van A",
    59	        "role": "Learner",
    60	        "created_at": 1793130000000
    61	      },
    62	      "access_token": "eyJhbGciOi...",
    63	      "refresh_token": "r_9983fa01...",
    64	      "token_type": "Bearer",
    65	      "expires_in": 3600
    66	    }
    67	    ```
    68	
    69	---
    70	
    71	### 2.2. Mobile Login (`POST /api/v1/auth/login`)
    72	Authenticates credentials and returns mobile JWT token pair.
    73	
    74	* **Method**: `POST`
    75	* **Path**: `/api/v1/auth/login`

codex
The live Hub contracts use endpoint sections and narrative GAP/RFC entries, while Task 1 specifies the setup templates’ table format. I also found that the lifecycle’s worktree location would break a tracked relative satellite link. I’m checking those findings against the task boundaries before finalizing.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/audit_epic.py | sed -n '145,185p'; rg -n 'protected|R[1-8]|def check' skills/dev-implementation/resources/scripts/check_epic_readiness.py; nl -ba .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md | sed -n '19,80p'; nl -ba .devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md | sed -n '19,60p'; nl -ba .devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md | sed -n '140,172p'; nl -ba .devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md | sed -n '19,43p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   145	    commit = next(iter(git_lines(root, "log", "-1", "--format=%H", f"{base}..HEAD", "--", evidence_path)), None)
   146	    if commit and patch_id(root, commit) != runs["verify"].get("patch_id"):
   147	        return problems + [f"{stem}: patch changed after verify"], bool(problems)
   148	    return problems or [f"{stem}: PASS"], bool(problems)
   149	
   150	
   151	def audit_protected(root: Path, epic_path: str, commits: list[Commit], texts: dict[str, str]) -> tuple[list[str], bool]:
   152	    explicit = parse_protected_paths(show(root, "HEAD", f"{epic_path}/{Path(epic_path).name}.en.md") or "")
   153	    programs: set[str] = set()
   154	    allowed: set[str] = set()
   155	    for text in texts.values():
   156	        allowed.update(entry.pattern for entry in parse_allowed_files(text))
   157	        try:
   158	            programs.update(p for p in (program_of(row.command, root) for row in parse_verification(text)[0]) if p)
   159	        except ContractError:
   160	            continue
   161	    items: list[str] = []
   162	    failed = False
   163	    for commit in commits:
   164	        for path in commit.paths:
   165	            if path not in programs and not any(path_matches(pattern, path) for pattern in explicit):
   166	                continue
   167	            unauthorised = not path.startswith(".devtool/") and path not in allowed
   168	            items.append(f"{commit.short} {path}" + (" — unauthorised" if unauthorised else ""))
   169	            failed = failed or unauthorised
   170	    return items, failed
   171	
   172	
   173	def grader_text(text: str) -> list[str]:
   174	    covers = [line for line in text.splitlines() if COVERS_LINE.match(line)]
   175	    allowed = [f"`{entry.pattern}`" + (" (new)" if entry.new else "") for entry in parse_allowed_files(text)]
   176	    return (["# Verification"] + (section(text, "Verification") or "").splitlines()
   177	            + ["# Definition of Done"] + (section(text, "Definition of Done") or "").splitlines()
   178	            + ["# Allowed files"] + allowed + ["# Covers"] + covers)
   179	
   180	
   181	def scenario_ids_at(root: Path, rev: str, path: str) -> set[str]:
   182	    text = show(root, rev, path)
   183	    if text is None:
   184	        return set()
   185	    with tempfile.TemporaryDirectory() as scratch:
33:    check: str     # "R1" ... "R8", "R5b", "R7b"
102:def check_preflight(ctx: Context) -> list[Finding]:
112:        findings.append(Finding("R1", "FAIL", f"compute_execution_order.py: {last_line}"))
120:                        "R1",
139:        findings.append(Finding("R1", "FAIL", f"check_bdd_traceability.py plan: {last_line}"))
154:        findings.append(Finding("R1", "FAIL", f"check_task_contract.py --design: {last_line}"))
169:            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
182:            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
193:            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
198:def check_task_mirrors(ctx: Context) -> list[Finding]:
210:            findings.append(Finding("R2", "FAIL", f"{name}: no mirror in .devtool/features/"))
240:            findings.append(Finding("R2", "FAIL", diff_msg))
306:def check_bdd_scenarios(ctx: Context) -> list[Finding]:
320:                    Finding("R3", "FAIL", f"{task_path.name}: {sc_id} differs from bdd_scenarios.en.md")
332:                    Finding("R3", "FAIL", f"bdd_scenarios.vi.md: {missing_or_extra} missing or extra")
338:def check_tier_tags(ctx: Context) -> list[Finding]:
378:            findings.append(Finding("R4", "FAIL", f'{sc_id}: tier tag "{tier_tag}"'))
383:def check_grounding(ctx: Context) -> list[Finding]:
386:    # --- R5: Symbol Grounding ---
450:                    findings.append(Finding("R5", "FAIL", f"{task_path.name}: {name} not in {path_str}"))
452:    # --- R5b: Route Grounding (WARN) ---
493:                findings.append(Finding("R5b", "WARN", f"{route}: not found in tracked source"))
498:def check_gate4_coverage(ctx: Context) -> list[Finding]:
517:            findings.append(Finding("R6", "FAIL", f"{task_path.name}: Covers without a TIER-C row"))
542:                            "R6",
551:def check_metadata(ctx: Context) -> list[Finding]:
561:        findings.append(Finding("R7", "FAIL", "Status starts with Packaged but handoff.md is missing"))
566:            findings.append(Finding("R7", "FAIL", f"handoff.md exists but Status is '{hld_status}'"))
584:                            "R7",
590:            findings.append(Finding("R7", "FAIL", "handoff.md is missing 'Design commit' line"))
597:                Finding("R7", "FAIL", f"{task_path.name}: epic '{t_epic}' differs from '{ctx.epic_slug}'")
604:                Finding("R7", "FAIL", f"{task_path.name}: status '{t_status}' not in TASK_STATUSES")
615:                findings.append(Finding("R7b", "WARN", f"spec status: {spec_status}"))
620:def check_baseline(ctx: Context) -> list[Finding]:
632:        return [Finding("R8", "WARN", "baseline skipped: dirty tree")]
659:                        "R8",
668:                    findings.append(Finding("R8", "WARN", f"{task_path.stem}:{row.id} {mis}"))
674:    ("R1", check_preflight),
675:    ("R2", check_task_mirrors),
676:    ("R3", check_bdd_scenarios),
677:    ("R4", check_tier_tags),
678:    ("R5", check_grounding),
679:    ("R6", check_gate4_coverage),
680:    ("R7", check_metadata),
681:    ("R8", check_baseline),
715:    for check_id in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
723:        if check_id == "R5":
724:            for f in by_check.get("R5b", []):
726:        elif check_id == "R7":
727:            for f in by_check.get("R7b", []):
731:        lines.append("R8 SKIP")
733:        r8_findings = by_check.get("R8", [])
736:            lines.append("R8 PASS")
    19	## Requirement Analysis
    20	
    21	Create the canonical delta brief template `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` and implement the structured Markdown contract parser and initial sync baseline logic in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
    22	1. Author `contract_delta_brief.md.tmpl` using standard library `string.Template` placeholders (`$domain`, `$mode`, `$sync_status`, `$previous_version`, `$current_version`, `$hub_commit_range`, `$changed_files_summary`, `$endpoints_section`, `$payload_keys_section`, `$pipeline_steps_section`, `$rfcs_section`, `$lifecycle_rules_section`).
    23	2. Implement structured Markdown parsing in `sync_contracts.py` for the 3 canonical contract files:
    24	   - `api_contract.md`: Extract `Version`, required authentication headers table, `Endpoints Matrix` rows (`Method`, `Endpoint`, `Auth`, `Purpose`), JSON payload schema top-level and nested keys, and `Version Changelog` entries.
    25	   - `architecture_and_flow.md`: Extract numbered canonical pipeline steps and state machine transitions.
    26	   - `gaps_and_rfcs.md`: Extract `Active RFC Ledger` rows (`RFC ID`, `Title`, `Proposing Repo`, `Status`, `Target Release`, `Breaking?`).
    27	3. Implement initial baseline detection (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet (`[SYC-EC-01]`) and brief rendering (`[SYC-HP-01]`).
    28	4. Initialize `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` covering `[SYC-HP-01]` and `[SYC-EC-01]`.
    29	
    30	## Files
    31	
    32	Allowed files:
    33	- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new)
    34	- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
    35	- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)
    36	
    37	Read-only context:
    38	- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
    39	- `skills/setup-shared-contracts/resources/templates/api_contract.md.tmpl` — canonical API contract structure
    40	- `skills/setup-shared-contracts/resources/templates/architecture_and_flow.md.tmpl` — canonical architecture structure
    41	- `skills/setup-shared-contracts/resources/templates/gaps_and_rfcs.md.tmpl` — canonical RFC ledger structure
    42	
    43	## Design Rationale
    44	
    45	- Standard library `string.Template` and regex/line-based table parsers keep `sync_contracts.py` 100% dependency-free and portable across Python 3.10+ environments.
    46	- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.
    47	
    48	## Impact Analysis & Blast Radius
    49	
    50	- **Target Files & Symbols**: `contract_delta_brief.md.tmpl`, `sync_contracts.py` (`parse_api_contract`, `parse_architecture_and_flow`, `parse_gaps_and_rfcs`, `render_brief`), and `test_sync_contracts.py`.
    51	- **Downstream Callers**: Tasks 2, 3, and 4 build upon `sync_contracts.py` and `test_sync_contracts.py`.
    52	- **Cross-Platform Bridges**: None.
    53	- **Target Test Coverage Threshold**: 100% coverage of Markdown table/schema extraction and template substitution.
    54	
    55	## BDD Scenarios and Acceptance Criteria
    56	
    57	### BDD SCENARIOS
    58	
    59	Covers: SYC-HP-01, SYC-EC-01
    60	
    61	```gherkin
    62	Scenario: [SYC-HP-01] [Tier C - Integration] Structured Contract Parsing and Requirements Brief Rendering
    63	  Given an initialized Hub repository with domain lyrics-sync containing api_contract.md, architecture_and_flow.md, and gaps_and_rfcs.md
    64	  When the engineer invokes sync_contracts.py brief --domain lyrics-sync
    65	  Then the parser extracts version "1.0.0", the 4 canonical endpoints, authentication headers, JSON payload keys, 7 pipeline steps, and RFC-001
    66	  And the output Markdown report contains sections for Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, and Lifecycle Execution Rules
    67	  And the command exits with code 0
    68	
    69	Scenario: [SYC-EC-01] [Tier A - Unit] Initial Sync Detection When Watermark File Is Absent
    70	  Given a valid Satellite repository where .agents/contract_sync.json does not exist
    71	  When the engineer invokes sync_contracts.py check --json
    72	  Then the JSON report identifies the domain status as "INITIAL_SYNC"
    73	  And lists all 3 canonical contract files as unsynced baseline deltas
    74	  And the command exits with code 0 when --strict is omitted and code 1 when --strict is provided
    75	```
    76	
    77	## Verification
    78	
    79	| ID | Phase | Command | Expect | Needs |
    80	|----|-------|---------|--------|-------|
    19	## Requirement Analysis
    20	
    21	Implement the `ack` subcommand, incremental drift detection (`IN_SYNC` vs `DRIFT_DETECTED`), multi-domain watermark preservation, atomic JSON writing, and corrupted watermark recovery in `skills/sync-shared-contracts/resources/scripts/sync_contracts.py`.
    22	1. **Watermark Ack Command (`[SYC-HP-02]`, `[SYC-ST-02]`, `[SYC-AR-01]`)**:
    23	   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, query the Hub git commit SHA, and collect acknowledged endpoints and RFC IDs (including `--rfc <RFC-ID>` arguments).
    24	   - Write `.agents/contract_sync.json` atomically using a temporary file in `.agents/` and `os.replace()`, preserving existing entries for other domains (`[SYC-ST-02]`, `[SYC-AR-01]`).
    25	2. **Incremental Drift Detection (`[SYC-ST-01]`)**:
    26	   - After `ack` is run, `check --strict` must report `IN_SYNC` and exit `0` (`[SYC-HP-02]`).
    27	   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, `check` must transition to `DRIFT_DETECTED`, surface modified files, new endpoints, and new RFCs, and exit `1` when `--strict` is passed (`[SYC-ST-01]`).
    28	3. **Corrupted Watermark Recovery (`[SYC-FR-03]`)**:
    29	   - If `.agents/contract_sync.json` contains malformed JSON, `check` logs a warning to stderr and falls back to `INITIAL_SYNC` without crashing, while `ack` overwrites it with valid `schema_version: 1` JSON.
    30	
    31	## Files
    32	
    33	Allowed files:
    34	- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
    35	- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)
    36	
    37	Read-only context:
    38	- `skills/sync-shared-contracts/resources/templates/contract_delta_brief.md.tmpl` (new) — brief template from Task 1
    39	- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications
    40	
    41	## Design Rationale
    42	
    43	- Atomic file replacement (`tempfile.NamedTemporaryFile` in `.agents/` + `os.replace`) guarantees concurrent readers never observe truncated JSON.
    44	- Preserving sibling domain keys in `.agents/contract_sync.json` allows a multi-domain Hub or multi-service consumer to track each domain independently.
    45	- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:verification-before-completion`.
    46	
    47	## Impact Analysis & Blast Radius
    48	
    49	- **Target Files & Symbols**: `sync_contracts.py` (`cmd_ack`, `cmd_brief`, `load_sync_state`, `save_sync_state_atomic`, `evaluate_domain_drift`) and `test_sync_contracts.py`.
    50	- **Downstream Callers**: Task 4 (`SKILL.md` workflow and `scripts/verify.sh`).
    51	- **Cross-Platform Bridges**: None.
    52	- **Target Test Coverage Threshold**: 100% coverage of `ack`, `brief --output`, drift transitions, and malformed JSON recovery.
    53	
    54	## BDD Scenarios and Acceptance Criteria
    55	
    56	### BDD SCENARIOS
    57	
    58	Covers: SYC-HP-02, SYC-ST-01, SYC-ST-02, SYC-AR-01, SYC-FR-03
    59	
    60	```gherkin
   140	| Dual-Mode & Watermark Check | `test_sync_contracts.py` | `test_syc_hp_02_satellite_and_hub_check` | Detects `INITIAL_SYNC`, `DRIFT_DETECTED`, and `IN_SYNC` across Hub and Satellite |
   141	| Heuristic Codebase Scanner | `test_sync_contracts.py` | `test_syc_ec_02_heuristic_snake_and_camel_scan` | Matches static route prefixes, headers, and `snake_case`/`camelCase` keys |
   142	| Watermark Ack & Strict Gate | `test_sync_contracts.py` | `test_syc_st_01_ack_and_incremental_drift` | Writes `.agents/contract_sync.json` atomically and verifies `--strict` exit codes |
   143	| Skill & Harness Verification | `test_sync_contracts.py` | `test_syc_hp_03_skill_and_verify_harness` | Validates `SKILL.md` frontmatter, links, and `scripts/verify.sh` integration |
   144	
   145	## Verification Environment
   146	
   147	- **Runtime**: Python 3.10+ (Standard Library only: `pathlib`, `os`, `sys`, `json`, `hashlib`, `re`, `subprocess`, `argparse`, `unittest`, `tempfile`).
   148	- **Isolation**: All tests execute inside isolated `tempfile.TemporaryDirectory()` workspaces with zero network access or live external repositories.
   149	- **Environment Variables (`Needs`)**: None (`—`).
   150	- **Test Command**: `python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py`
   151	- **Release Gate**: `scripts/verify.sh` executes the test suite on every release verification run.
   152	
   153	## Shared Contract Impact
   154	
   155	`None — self-contained developer tooling skill (audits and synchronizes shared contracts for target repositories)`.
   156	
   157	## Comprehensive BDD Scenario Coverage
   158	
   159	Full Gherkin scenarios covering all 5 dimensions live in `bdd_scenarios.en.md` and `bdd_scenarios.vi.md`.
   160	
   161	- **Happy Paths**:
   162	  - `[SYC-HP-01]`: Structured parsing of the 3 canonical contract files and rendering of the Contract Requirements Brief.
   163	  - `[SYC-HP-02]`: End-to-end Satellite and Hub drift detection, acknowledgement (`ack`), and `--strict` verification pass.
   164	  - `[SYC-HP-03]`: Skill definition validation and `scripts/verify.sh` harness execution.
   165	- **Edge Cases & Boundaries**:
   166	  - `[SYC-EC-01]`: Initial sync (`INITIAL_SYNC`) when `.agents/contract_sync.json` does not exist yet.
   167	  - `[SYC-EC-02]`: Heuristic codebase scanner matching parameterized routes (`/tasks/{id}/progress`) and `camelCase` DTO properties (`leaseDurationMs`).
   168	  - `[SYC-EC-03]`: Graceful fallback when the Hub directory is not a Git repository (no `.git` folder).
   169	- **State Transitions**:
   170	  - `[SYC-ST-01]`: Transitioning from `INITIAL_SYNC` to `IN_SYNC` via `ack`, then to `DRIFT_DETECTED` when `api_contract.md` or `gaps_and_rfcs.md` is updated in the Hub.
   171	  - `[SYC-ST-02]`: Recording newly acknowledged RFC IDs via `ack --rfc RFC-002` while preserving other domain entries in `.agents/contract_sync.json`.
   172	- **Async & Concurrency**:
    19	## Requirement Analysis
    20	
    21	Create the skill definition `skills/sync-shared-contracts/SKILL.md` and wire the test suite into the repository verification script `scripts/verify.sh`.
    22	1. Author `skills/sync-shared-contracts/SKILL.md`:
    23	   - YAML frontmatter strictly containing only `name: sync-shared-contracts` and `description`.
    24	   - Complete documentation of the 3-layer Hybrid Delta Engine (`check`, `brief`, `ack`) and `.agents/contract_sync.json` watermark schema.
    25	   - Detailed 5-step Orchestrated Bridge into `d3nexus:dev-lifecycle`:
    26	     - Step 1: Preflight & Contract Delta Audit (`sync_contracts.py check` & `brief`).
    27	     - Step 2: Scope Confirmation with developer.
    28	     - Step 3: Stage 1 (`dev-brainstorming`) & Stage 2 (`dev-designer`) rules (Hub `task_01` canonical contract update vs Satellite `task_01` consumer DTO/adapter update, Satellite Git read-only symlink rule, and final task running `sync_contracts.py ack`).
    29	     - Step 4: Stage 3 (`dev-implementation`) TDD execution and `sync_contracts.py check --strict` verification.
    30	     - Step 5: Stage 4 (`finishing-a-development-branch`).
    31	2. Wire `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` into `scripts/verify.sh` in Section 14 (`== 14. Shared contracts CLI engine is enforced ==`) alongside `test_setup_contracts.py`.
    32	3. Add final integration test `test_syc_hp_03_skill_and_verify_harness` in `test_sync_contracts.py` verifying `SKILL.md` frontmatter, links, and end-to-end CLI execution (`[SYC-HP-03]`).
    33	
    34	## Files
    35	
    36	Allowed files:
    37	- `skills/sync-shared-contracts/SKILL.md` (new)
    38	- `scripts/verify.sh`
    39	- `skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` (new)
    40	
    41	Read-only context:
    42	- `skills/sync-shared-contracts/resources/scripts/sync_contracts.py` (new)
    43	- `.devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md` — HLD specifications

exec
/bin/zsh -lc "rg -n 'diff|snapshot|baseline|modified|added|removed|acknowledged|Approved|Implemented|--rfc|strict' .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md .devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md; nl -ba skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py | sed -n '1,90p'; rg -n 'relpath|readlink|relative|symlink' skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py; nl -ba .devtool/epic/sync_shared_contracts/sync_shared_contracts.en.md | sed -n '124,138p'; ls -l /opt/homebrew/bin/git /usr/local/bin/git" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 exited 1 in 0ms:
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:9:modified: "2026-10-30T11:58:00Z"
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:23:   - Compute SHA-256 hashes for `api_contract.md`, `architecture_and_flow.md`, and `gaps_and_rfcs.md`, query the Hub git commit SHA, and collect acknowledged endpoints and RFC IDs (including `--rfc <RFC-ID>` arguments).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:26:   - After `ack` is run, `check --strict` must report `IN_SYNC` and exit `0` (`[SYC-HP-02]`).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:27:   - When `api_contract.md`, `architecture_and_flow.md`, or `gaps_and_rfcs.md` changes in the Hub, `check` must transition to `DRIFT_DETECTED`, surface modified files, new endpoints, and new RFCs, and exit `1` when `--strict` is passed (`[SYC-ST-01]`).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:63:  When the engineer invokes sync_contracts.py ack followed by sync_contracts.py check --strict
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:66:  And sync_contracts.py check --strict outputs status "IN_SYNC" and exits with code 0
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:71:  And the engineer runs sync_contracts.py check --strict in the Satellite repository
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:73:  And the delta report identifies api_contract.md and gaps_and_rfcs.md as modified, surfaces the new cancel endpoint as "MISSING_IN_CODE", and lists RFC-002
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:74:  And sync_contracts.py check --strict exits with code 1
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:78:  When the engineer invokes sync_contracts.py ack --domain nexus --rfc RFC-005
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:80:  And records the new "nexus" entry containing "RFC-005" in acknowledged_rfcs
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:106:| V8 | TIER-B | `mypy --strict --follow-imports=silent skills/sync-shared-contracts/resources/scripts/sync_contracts.py skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py` | exit 0 | — |
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:121:- Watermark state is persisted at `<repo_root>/.agents/contract_sync.json` with `schema_version: 1`, `mode`, and per-domain objects containing `hub_commit_sha`, `contract_version`, `last_synced_at`, `file_hashes`, `acknowledged_rfcs`, and `acknowledged_endpoints`.
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:126:- `sync_contracts.py ack` writes `.agents/contract_sync.json` atomically and `check --strict` passes with `IN_SYNC` (V2, V5).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:127:- Upstream contract edits transition status to `DRIFT_DETECTED` and fail `check --strict` with exit code `1` (V3).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:128:- Multi-domain watermark entries and explicit `--rfc` flags are preserved and recorded (V4).
.devtool/epic/sync_shared_contracts/task_3_watermark_ack_and_brief_cli.md:130:- Ruff and Mypy strict checks pass (V7, V8).
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:4:- **Status**: Approved
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:42:- Provide an atomic watermark update command (`ack`) that records the synced contract version, Hub commit SHA, file hashes, and acknowledged RFCs/endpoints in `.agents/contract_sync.json`.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:55:   - Detects upstream changes made in the Hub repository (new endpoints, updated payload fields, pipeline rules, and `Approved` RFCs) that need to be implemented in the satellite consumer/worker codebase.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:56:   - Enforces the strict Git read-only symlink boundary (never staging `shared-contracts/` inside the satellite repository; tracking sync state exclusively in `.agents/contract_sync.json`).
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:59:   - Detects `Draft`, `In Review`, or `Approved` RFCs and gaps proposed by satellites in `gaps_and_rfcs.md`, as well as contract changes not yet reflected in the Hub backend source code or `.agents/contract_sync.json`.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:74:        GIT["Hub Git History (git log / diff)"]
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:85:    CLI -->|"2. Git diff + Parse Markdown"| CONTRACT
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:125:      "acknowledged_rfcs": ["RFC-001", "RFC-002"],
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:126:      "acknowledged_endpoints": [
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:143:python3 sync_contracts.py check [--repo-root <path>] [--domain <domain_name>] [--json] [--strict]
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:154:  - `0` when `IN_SYNC` (or when `DRIFT_DETECTED` / `INITIAL_SYNC` without `--strict`).
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:155:  - `1` when topology/symlink errors occur, or when `--strict` is passed and status is not `IN_SYNC`.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:165:    2. **API & Schema Requirements**: Endpoints and JSON payload fields added or modified, annotated with heuristic scan status (`FOUND_IN_CODE` vs `MISSING_IN_CODE`).
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:172:python3 sync_contracts.py ack [--repo-root <path>] [--domain <domain_name>] [--rfc <RFC-ID> ...]
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:175:  - Computes the current file hashes, contract version, Hub git commit SHA, endpoints list, and RFC IDs (all `Approved` / `Implemented` RFCs plus any explicitly passed via `--rfc`).
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:203:       - In **Both Modes**: The final task (or `task_01` verification hook) includes `.agents/contract_sync.json` in `Files Allowed` and runs `sync_contracts.py ack` + `sync_contracts.py check --strict` so the sync watermark is committed alongside the implementation.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:205:   - Execute tasks in an isolated worktree via TDD, verify `sync_contracts.py check --strict` passes, run Gate 4 (`quality_check` + `check_bdd_traceability.py` + `audit_epic.py`), and pass the Review Choice loop and Gate 5.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:215:- **Test Watermark Ack & Incremental Drift**: Verifies that running `ack` transitions `check --strict` to exit `0` (`IN_SYNC`), and subsequent edits to `api_contract.md` or `gaps_and_rfcs.md` in the Hub trigger `DRIFT_DETECTED` (exit `1` under `--strict`) with accurate git commit log and file hash deltas.
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:225:| `.agents/contract_sync.json` does not exist yet | `check` / `brief` | Reports status `INITIAL_SYNC`, parses full contract baseline, and classifies items via codebase heuristic scan. |
.devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:234:  *Mitigation*: Sync state is stored strictly inside `<repo_root>/.agents/contract_sync.json`, completely outside the `shared-contracts` symlink, and `brief` explicitly injects the `Files Allowed` prohibition reminder for `dev-designer`.
     1	"""Unit and integration tests for setup-shared-contracts skill and CLI engine."""
     2	
     3	from __future__ import annotations
     4	
     5	import concurrent.futures
     6	import os
     7	import string
     8	import subprocess
     9	import sys
    10	import tempfile
    11	import unittest
    12	from pathlib import Path
    13	
    14	# Enable direct import of setup_contracts module
    15	sys.path.insert(0, str(Path(__file__).resolve().parent))
    16	import setup_contracts
    17	
    18	TEMPLATES_DIR = (
    19	    Path(__file__).resolve().parent.parent / "templates"
    20	)
    21	CANONICAL_TEMPLATE_NAMES = (
    22	    "api_contract.md.tmpl",
    23	    "architecture_and_flow.md.tmpl",
    24	    "gaps_and_rfcs.md.tmpl",
    25	    "hub_readme.md.tmpl",
    26	    "hub_rule.md.tmpl",
    27	    "satellite_rule.md.tmpl",
    28	)
    29	
    30	
    31	class TestCanonicalTemplates(unittest.TestCase):
    32	    """Verifies template existence, schema validity, and string.Template hygiene."""
    33	
    34	    def test_canonical_templates_exist(self) -> None:
    35	        """All 6 canonical template files must exist and be non-empty."""
    36	        self.assertTrue(
    37	            TEMPLATES_DIR.is_dir(),
    38	            f"Templates directory not found: {TEMPLATES_DIR}",
    39	        )
    40	        for tmpl_name in CANONICAL_TEMPLATE_NAMES:
    41	            tmpl_path = TEMPLATES_DIR / tmpl_name
    42	            self.assertTrue(
    43	                tmpl_path.is_file(),
    44	                f"Missing canonical template: {tmpl_name}",
    45	            )
    46	            content = tmpl_path.read_text(encoding="utf-8")
    47	            self.assertGreater(
    48	                len(content.strip()),
    49	                0,
    50	                f"Template is empty: {tmpl_name}",
    51	            )
    52	
    53	    def test_string_template_substitution_hygiene(self) -> None:
    54	        """Every template must be valid string.Template without legacy mustache syntax."""
    55	        mapping = {
    56	            "domain": "test-domain",
    57	            "hub_repo": "TestHub",
    58	            "timestamp": "2026-10-30T00:00:00Z",
    59	        }
    60	        for tmpl_name in CANONICAL_TEMPLATE_NAMES:
    61	            tmpl_path = TEMPLATES_DIR / tmpl_name
    62	            raw_content = tmpl_path.read_text(encoding="utf-8")
    63	
    64	            # Must not contain legacy mustache markers
    65	            self.assertNotIn("{{", raw_content, f"Mustache token '{{' in {tmpl_name}")
    66	            self.assertNotIn("}}", raw_content, f"Mustache token '}}' in {tmpl_name}")
    67	
    68	            # Must successfully substitute defined variables
    69	            tmpl = string.Template(raw_content)
    70	            rendered = tmpl.safe_substitute(mapping)
    71	
    72	            # Assert substitutions took place
    73	            self.assertIn("TestHub", rendered)
    74	            self.assertIn("2026-10-30T00:00:00Z", rendered)
    75	
    76	    def test_ssc_hp_01(self) -> None:
    77	        """[SSC-HP-01] Validates production Hub initialization and contract generation."""
    78	        cli_path = Path(__file__).resolve().parent / "setup_contracts.py"
    79	        with tempfile.TemporaryDirectory() as tmp_dir:
    80	            tmp_path = Path(tmp_dir)
    81	            proc = subprocess.run(
    82	                [
    83	                    "python3",
    84	                    str(cli_path),
    85	                    "init-hub",
    86	                    "--domain",
    87	                    "lyrics-sync",
    88	                    "--repo-root",
    89	                    str(tmp_path),
    90	                ],
100:            self.assertFalse(shared_contracts_dir.is_symlink())
237:        """[SSC-FR-01] Refusing Hub initialization on existing symlink."""
246:            symlink_path = tmp_path / "shared-contracts"
247:            os.symlink(target_dummy, symlink_path)
256:            self.assertIn("symlink", (proc.stdout + proc.stderr).lower())
263:        """[SSC-HP-02] Fresh satellite repository relative symlinking."""
299:            # Check symlink
300:            symlink_path = sat_dir / "shared-contracts"
301:            self.assertTrue(symlink_path.is_symlink())
302:            link_target = os.readlink(symlink_path)
303:            self.assertFalse(os.path.isabs(link_target), f"Symlink target must be relative, got: {link_target}")
305:            # Check files resolve across symlink
306:            self.assertTrue((symlink_path / "api_contract.md").is_file())
307:            self.assertTrue((symlink_path / "architecture_and_flow.md").is_file())
308:            self.assertTrue((symlink_path / "gaps_and_rfcs.md").is_file())
315:        """[SSC-EC-02] Deep sibling hierarchy relative path calculation."""
349:            symlink_path = sat_dir / "shared-contracts"
350:            self.assertTrue(symlink_path.is_symlink())
351:            link_target = os.readlink(symlink_path)
353:            self.assertTrue((symlink_path / "api_contract.md").is_file())
394:            symlink_path = sat_dir / "shared-contracts"
395:            self.assertIn("alpha", os.readlink(symlink_path))
416:            self.assertIn("beta", os.readlink(symlink_path))
494:            self.assertFalse(physical_dir.is_symlink())
579:        """[SSC-AR-02] Circular symlink and max depth (>10 hops) loop protection halts cleanly."""
582:        # 1. Circular symlink detection (A -> B -> A)
588:            os.symlink("loop_target", link_a)
589:            os.symlink("shared-contracts", link_b)
611:                os.symlink(prev_target, tmp_path / hop_name)
623:        # 3. Intermediate directory symlink chain (> 10 hops)
633:                os.symlink(prev_dir, tmp_path / hop_name)
637:            os.symlink("alias_hub/shared-contracts/domain", tmp_path / "shared-contracts")
   124	    CLI->>Code: Atomically write .agents/contract_sync.json
   125	    Life->>CLI: Verify sync_contracts.py check --strict exits 0
   126	    Life-->>Dev: Pass Gate 4 & Gate 5 -> Stage 4 Finish Branch
   127	```
   128	
   129	## Integration Test Plan and Boundary Matrix
   130	
   131	Integration test roots: skills/sync-shared-contracts/resources/scripts/, scripts/
   132	
   133	Protected paths: .agents/quality/**, .devtool/epic/sync_shared_contracts/bdd_scenarios.en.md, .devtool/epic/sync_shared_contracts/bdd_scenarios.vi.md, scripts/verify.sh
   134	
   135	Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/sync-shared-contracts.xml skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py -> build/test-results/sync-shared-contracts.xml
   136	
   137	| Component | Test File | Test Case | Target Boundary |
   138	|---|---|---|---|
ls: /opt/homebrew/bin/git: No such file or directory
ls: /usr/local/bin/git: No such file or directory

codex
Four issues need resolution before implementation. Candidate source was inspected at `6a2e64df2140c316a46ab0c9a584ea3b1b196c7c`; sibling Hub contracts were inspected as live filesystem evidence, independently of that commit.

Verdict: CHANGES REQUIRED
[Important] .devtool/epic/sync_shared_contracts/task_1_brief_template_and_contract_parser.md:Requirement Analysis §2 — The parser contract supports setup-template tables but does not cover the existing pilot contracts. The live lyrics-sync API declares endpoints through Method/Path sections (`../D3Nexus/shared-contracts/lyrics-sync/api_contract.md:37–42`), and its ledger uses narrative GAP entries with OPEN/PROPOSED/ACCEPTED statuses (`../D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:18–29`, `:55–63`, `:79–84`). Template-only fixtures can therefore pass while real requirements remain unparsed. Proposed: specify support for both existing narrative contracts and generated tables, normalize their statuses explicitly, reject unsupported formats instead of reporting empty success, and add hermetic representative fixtures and bilingual BDD coverage.
[Important] .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§5.3 and §7 Steps 2–3 — Scope confirmation permits selecting only some deltas/RFCs, but ack automatically acknowledges every Approved/Implemented RFC and records all current file hashes. Completing RFC-001 can consequently acknowledge an unimplemented RFC-002; an upstream edit arriving during implementation is also silently included. The subsequent strict check proves acknowledgement of current files, without preserving outstanding implementation scope. Proposed: bind acknowledgement to the reviewed contract snapshot and explicitly completed scope; reject snapshot changes and retain outstanding requirements, or require complete domain implementation before advancing its watermark. Align Task 3, both language pairs, and BDD tests.
[Important] .devtool/epic/sync_shared_contracts/task_4_skill_definition_and_verify_integration.md:Requirement Analysis, lifecycle bridge — The bridge requires isolated worktree execution without defining how relative satellite links remain resolvable there. Existing setup computes the link relative to the original satellite root (`skills/setup-shared-contracts/resources/scripts/setup_contracts.py:326–331`), while implementation creates nested `.worktrees/<epic_dir>` checkouts (`skills/dev-implementation/SKILL.md:144–151`). The unchanged link bytes then resolve from a different directory, making the required check/ack fail despite valid original topology. Proposed: define worktree-aware contract-root resolution that preserves the tracked link, scans and writes state in the execution worktree, and reads the intended Hub snapshot; add a hermetic nested-worktree acceptance scenario and corresponding Task 2 requirements.
[Important] .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§4.2, §5.2 and §9 — The brief promises added or modified payload requirements, including Git-less operation, but the watermark retains hashes and endpoint/RFC identifiers without previous payload or invariant content. After a Git-less contract changes an existing field’s type/default, its old hash cannot recover the previous definition. The same problem occurs when acknowledged content was uncommitted and the recorded Git commit does not represent it. Proposed: persist a normalized baseline sufficient for semantic comparison, or explicitly report that historical comparison is unavailable and emit the entire current contract for review; cover same-key semantic changes and uncommitted baselines in Task 3 and bilingual BDD.

tokens used
113,302
````
