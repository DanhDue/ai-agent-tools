# Principal Review: contract_and_authoring_ergonomics

## Round 1

- **Date**: 2026-11-05T19:16:38Z
- **SHA**: e4725dcf21bae83479967b22137325d3a320eb69
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_02_single_source_render_engine.md:Decisions Already Made | Link rewriting breaks ./ link parity and done-directory targets. Proposed: use location-aware rewriting and shared normalization, with readiness changes allowed in Task 02. | fixed in 32fc4b0 |
| 2 | Important | task_01_evidence_files_contract.md:BDD SCENARIOS and Definition of Done | TCAE-EC-01 requires the renderer introduced by dependent Task 02. Proposed: move this scenario and its acceptance coverage to Task 02. | fixed in 32fc4b0 |
| 3 | Important | task_02_single_source_render_engine.md:Decisions Already Made | Fixed four-backtick wrapping breaks embedded files containing four-backtick fences. Proposed: select a delimiter longer than payload fence runs and synchronize specifications and tests. | fixed in 32fc4b0 |
| 4 | Important | task_05_end_to_end_contract_acceptance.md:Verification V1 | Mandatory RED failure conflicts with already-delivered evidence-transition behavior and the permitted changes. Proposed: replace V1 with justified RED: n/a acceptance-task handling. | fixed in 32fc4b0 |

Raw output:

`````text
Four issues need correction before implementation.

1. **Mirror rewriting conflicts with readiness and completed-task locations.** Task 02’s “Decisions Already Made” (line 109) rewrites both `file.md` and `./file.md` to `../epic/<epic>/file.md`. However, [check_epic_readiness.py:202](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_epic_readiness.py:202) normalizes only that prefix, leaving `file.md` unequal to the original `./file.md`. An in-memory probe of the actual R2 function confirmed failure. Additionally, that prefix resolves beneath `.devtool/features/epic/` when used from `features/done/`. Task 02 currently lists the readiness implementation as read-only. Proposed: define location-aware rewriting and common normalization, permit the necessary readiness changes in Task 02, and test both link spellings in both board locations.

2. **Task 01 requires functionality delivered by its dependent task.** Its `Covers:` line and DoD require `TCAE-EC-01`, whose canonical scenario explicitly executes `sync_task_status.py render`. Task 02 introduces that command and depends on Task 01. The candidate’s [sync_task_status.py:504](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/sync_task_status.py:504) registers the existing subcommands without `render`, and Task 01 cannot modify that file. Faithful scenario coverage therefore cannot pass before Task 02. Proposed: move `TCAE-EC-01` ownership and acceptance coverage to Task 02, updating the corresponding task blocks and mirrors.

3. **Fixed four-backtick promotion does not safely embed supported Markdown files.** Task 02 freezes four backticks whenever embedded content contains triple backticks. Existing [writing-plans/SKILL.md:135](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/writing-plans/SKILL.md:135) already contains a four-backtick block. Wrapping that actual file in the prescribed fence and invoking the existing document checker in memory produced an MD040 finding; five backticks passed. The checker closes a fence when an unlabelled delimiter is at least as long as its opener ([check_document.py:104](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/doc_quality_check/resources/scripts/check_document.py:104)). Proposed: choose an outer fence longer than every potentially closing backtick run in the payload, retaining four as the minimum promotion, and update the bilingual specification and acceptance cases.

4. **Task 05 mandates a failing RED test for behavior already required to pass.** V1 expects the evidence-transition test to fail after Tasks 01–04 have delivered that behavior. Task 05 permits only its new test file and an unrelated typing correction, leaving no planned behavioral implementation to turn that failure green. The real [RED validator:119](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_task_checks.py:119) rejects both an already-passing test and a missing test; read-only probes confirmed both outcomes. Proposed: make this an acceptance-only task with a justified `RED: n/a`, retaining GREEN and integration verification.

Early-error probes also exercised parsing, file-read failure, and timeout handlers without exposing an unbound-variable failure.

Verdict: CHANGES REQUIRED
[Important] task_02_single_source_render_engine.md:Decisions Already Made — Link rewriting breaks ./ link parity and done-directory targets. Proposed: use location-aware rewriting and shared normalization, with readiness changes allowed in Task 02.
[Important] task_01_evidence_files_contract.md:BDD SCENARIOS and Definition of Done — TCAE-EC-01 requires the renderer introduced by dependent Task 02. Proposed: move this scenario and its acceptance coverage to Task 02.
[Important] task_02_single_source_render_engine.md:Decisions Already Made — Fixed four-backtick wrapping breaks embedded files containing four-backtick fences. Proposed: select a delimiter longer than payload fence runs and synchronize specifications and tests.
[Important] task_05_end_to_end_contract_acceptance.md:Verification V1 — Mandatory RED failure conflicts with already-delivered evidence-transition behavior and the permitted changes. Proposed: replace V1 with justified RED: n/a acceptance-task handling.

--- stderr ---
OpenAI Codex v0.162.1
--------
workdir: /Users/danhdueexoictif/AllProjects/ai-agent-tools
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: read-only
reasoning effort: high
reasoning summaries: none
session id: 01a1ad20-b7aa-7282-96c6-896d4185956d
--------
user
# Principal Review Prompt

You are the Principal Reviewer who signs off this architectural design before implementation. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the source at `e4725dcf21bae83479967b22137325d3a320eb69`, and report.

## Candidate

- Commit under review: `e4725dcf21bae83479967b22137325d3a320eb69`
- Base the branch diverged from: `main`
- Base commit: `e4725dcf21bae83479967b22137325d3a320eb69`
- Target path / Epic directory: `.devtool/epic/contract_and_authoring_ergonomics`

## Artefacts

Read these paths, relative to the repository root:

- `.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md`
- `.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.vi.md`
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md`
- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.vi.md`
- `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md`
- `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md`
- `.devtool/epic/contract_and_authoring_ergonomics/task_01_evidence_files_contract.md`
- `.devtool/epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md`
- `.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md`
- `.devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md`
- `.devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md`
- `.devtool/epic/contract_and_authoring_ergonomics/handoff.md`

## Readiness facts

Epic: contract_and_authoring_ergonomics (contract-and-authoring-ergonomics), 5 tasks
R1 PASS
R2 PASS
R3 PASS
R4 PASS
R5 PASS
R6 PASS
R7 PASS
R8 SKIP
Result: 0 FAIL, 0 WARN — PASS

The readiness report is already proven: all facts above have passed their mechanical checks; do not restate them, spend your review on judgement, architecture, and source grounding.

## Mandatory Dynamic Probing Rule

Do not rely solely on static diff inspection. For any language processing logic, regex expressions, exception handlers (`try/except`), or ORM persistence code, you MUST execute active read-only terminal probes (e.g. `python3 -c "..."` or interactive read-only REPL commands) to verify:
1. Local variables referenced in exception handlers are not unbound when exceptions occur early in a block.
2. Edge-case lexical tokens and inflections are not deformed by tokenization or lemmatization.
3. Database statement ordering in transaction flushes does not violate foreign keys or unique constraints.

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

6. **5-Layer Deep Verification Checklist**:
   - **Unbound Variable in Fallback**: Verify that all variables referenced in `except` blocks are assigned or imported before the `try` block begins.
   - **Part-of-Speech Ambiguity**: Verify that morphological transformation functions (lemmatizers, stemmers, token normalizers) disambiguate noun/adjective forms from verb-like gerunds and participles.
   - **ORM Flush Semantics**: Verify SQLAlchemy Unit of Work execution ordering (Insert -> Update -> Delete). Forbid mutating ORM entities before flushing deleted records sharing the same unique key or index constraint.
   - **Interactive Contract Boundary**: Verify that interactive token and span coverage on user interfaces conforms strictly to `architecture_and_flow.md`.
   - **Fixture Schema Sanity**: Verify that test fixtures and mock records in RED tests satisfy database check constraints before reaching domain assertions.

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
Tôi sẽ dùng `d3nexus:principal-review` để đối chiếu thiết kế với source tại commit đã chỉ định và chạy các probe chỉ đọc cho những logic liên quan. Tôi cũng dùng `d3nexus:task-observer` theo quy tắc của bộ kit; toàn bộ phiên review sẽ giữ nguyên filesystem và git state.

exec
/bin/zsh -lc 'cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.24.0/skills/task-observer/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.24.0/skills/principal-review/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.24.0/skills/using-superpowers/references/codex-tools.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
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
   n=$(find "$d" -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)         # independent count via find (zsh-safe)
   parsed=0
   if [ "$n" -gt 0 ]; then
     for f in "$d"/*.md; do
       [ -e "$f" ] || continue
       hdr=$(awk 'NR==1 && /^---[[:space:]]*$/ {fm=1; next}
                  fm && /^---[[:space:]]*$/ {exit}
                  fm' "$f")
       [ -n "$hdr" ] && parsed=$(( parsed + 1 ))
       printf '%s\n---\n' "$hdr"
     done
   fi
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
[ "$hi" -eq 0 ] && [ -n "$(find "$d" -maxdepth 1 -name "*.md" 2>/dev/null)" ] && { echo "ID COMMAND BROKEN — log is non-empty but no ids extracted"; exit 1; }
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
   - Executes with a read-only permissions profile (`claude -p --dangerously-skip-permissions`, `codex exec --sandbox read-only`, or `agy --sandbox --mode plan`).
   - The reviewer inspects active code at candidate SHA to verify groundedness (P1–P8 checklists).

3. **Triage Findings**:
   - Follow [document-triage.md](references/document-triage.md).
   - Verify every finding against the codebase.
   - Present the triage table to the developer and wait for decisions. The presentation MUST begin with the standardized 4-bullet header block:
     ```markdown
     Principal Review Triage: Round <N> (<CLI>)
     *(or `Principal Review Triage: <doc_path> (<CLI>)`)*

     • Candidate SHA: <commit_sha>
     • Reviewer: <CLI> ( <model> )
     • Thinking Level: <Light | Low | Medium | High | Extra High | None>
     • Verdict: <VERDICT> (<count> <Severity> findings)
     ```

4. **Revision Loop & Commit Ordering**:
   - Apply document edits first and commit:
     `git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"`
   - Record decisions with revision commit SHA in `principal_review.md`, then commit:
     `git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"`
   - Re-run packaging to refresh handoff metadata, record state via `python3 scripts/resume_context.py --state --epic <epic_slug>`, emit the AI Programmer prompt via `python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>`, and present the Principal Review Choice again.

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
/bin/zsh -lc "rg -n 'contract_and_authoring|evidence_files|render|principal|setup_shared_contracts' /Users/danhdueexoictif/antigravity_homes/phungthuy8901/.codex/memories/MEMORY.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
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

exec
/bin/zsh -lc 'cat rules/CRITICAL_RULES.md rules/coding-guidelines.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
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

## 8. Mandatory Two-Tier Project Memory & Tri-Role Persona Discipline

> [!CRITICAL]
> **AI Agents MUST strictly preserve Two-Tier Project Memory across session rotations and respect Tri-Role Persona boundaries across all stages of development.**
>
> 1. **Mandatory Context Restoration on Session Startup (Scoped to Development Lifecycle)**:
>    - When starting substantive feature engineering, architectural design, or task execution in the development lifecycle (`d3nexus:dev-lifecycle`, `dev-brainstorming`, `dev-designer`, `dev-implementation`) or after an account profile switch for development, the AI Agent MUST run `python3 scripts/resume_context.py` (or the `d3nexus:resume-context` skill) to restore architectural memory before answering or proposing solutions.
>    - The agent MUST summarize the restored project context in 5–10 concise bullets for the developer.
>    - **Zero-Context & Fast-Execution Exemption**: Routine operational prompts, standalone utility skills, and fast-execution commands — specifically `/refresh-session` (pinging quota windows), `/setup_keybindings`, git status/diff inspections, or quick standalone queries — **MUST NOT** invoke `resume_context.py` or `resume-context`. They must execute their requested actions immediately without loading repository context.
>    - **No Redundant Invocation**: Within an already-resumed active working session, the AI Agent MUST NOT repeatedly re-invoke `resume-context` on normal conversation turns.
>
> 2. **Strict Tri-Role Persona Discipline**:
>    - **Role 2.1 — Human Architect (Developer)**: Sole authority for system strategy, Gate approvals (Gate 1–5), and Review Choice decisions.
>    - **Role 2.2 — AI Assistant (`[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]`)**:
>      - Activated for architectural analysis, problem statement exploration, design specifications (`d3nexus:dev-brainstorming`, `d3nexus:dev-designer`), Principal Review (`d3nexus:principal-review`), and Cross-Model Review (`d3nexus:cross-model-review`).
>      - **STRICT PROHIBITION**: The AI Assistant is **STRICTLY PROHIBITED from modifying production source code or application test suites**. Only architectural documentation (`docs/`, `.devtool/`, `shared-contracts/`) may be edited.
>    - **Role 2.3 — AI Programmer (`[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]`)**:
>      - Activated for `/dev-implementation` and task execution inside isolated git worktrees.
>      - **STRICT BOUNDARIES**: Bound strictly to approved specifications, `Decisions Already Made`, and `Allowed files`. Must practice strict TDD (Red-Green-Refactor) and Clean Code standards. Zero test fakery.
>
> 3. **Deterministic State & Log Checkpointing**:
>    - After completing each Kanban task, the AI Programmer MUST log programmer activity (`scripts/resume_context.py --log`) and update Tier 2 snapshot state (`scripts/resume_context.py --state`).
>    - Upon feature completion in Stage 4 (`/finish`), the agent MUST run `scripts/resume_context.py --complete <epic_slug> "<milestone_summary>"` to record the permanent milestone in `.devtool/PROJECT_LEDGER.md` and archive the completed epic's Tier 2 files into `.devtool/archive/`.
>
> 4. **Mandatory Window Title Synchronization & Persistent Top/Bottom Bar Customization**:
>    - To eliminate cross-project window confusion when developers operate multiple IDEs or profile accounts, AI Agents MUST synchronize `window.title` and ensure persistent top/bottom bar colors in `.vscode/settings.json` upon entering an epic, transitioning lifecycle stages, or completing tasks.
>    - **Title Format**: `"<ICON> [<REPO_NAME>] [@<account_id>] <Vietnamese Epic Name> - <Stage / Task>"`.
>    - The `<account_id>` is extracted from the active profile / home environment (`os.path.basename(os.environ["HOME"])` under `antigravity_homes/`, e.g. `[@danhdue]`, `[@tess]`).
>    - The Vietnamese Epic Name MUST be extracted directly from the H1 header of `.devtool/epic/<epic_slug>/<epic_slug>.vi.md` (stripping the `# Epic:` prefix).
>    - **Persistent Inactive Bar Parity**: Both `titleBar` and `statusBar` MUST configure matching inactive background colors (`titleBar.inactiveBackground = titleBar.activeBackground` and `statusBar.inactiveBackground = statusBar.background`) to eliminate IDE dimming when windows lose focus.
>    - **Clean Activity Toolbar**: The left `activityBar.background` remains uncolored in default dark theme to avoid peripheral visual clutter.
>    - **Repository Color Signatures**:
>      - 🔴 `[LYRICS-SYNC]`: `#7f1d1d` (Crimson Red)
>      - 🟢 `[D3NEXUS]`: `#065f46` (Emerald Green)
>      - 🔵 `[NEXUS]`: `#0d47a1` (Royal Blue)
>      - 🟠 `[AGENT-TOOLS]`: `#b45309` (Warm Amber)
>    - Agents MUST preserve all existing `workbench.colorCustomizations` and developer configurations in `.vscode/settings.json`.
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

exec
/bin/zsh -lc 'for f in .devtool/epic/contract_and_authoring_ergonomics/*; do wc -l "$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     200 .devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md
     200 .devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.vi.md
     116 .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md
     116 .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md
     181 .devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md
     181 .devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.vi.md
      75 .devtool/epic/contract_and_authoring_ergonomics/handoff.md
     121 .devtool/epic/contract_and_authoring_ergonomics/task_01_evidence_files_contract.md
     126 .devtool/epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md
     129 .devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md
     115 .devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md
     114 .devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md

exec
/bin/zsh -lc 'git status --short && git rev-parse HEAD && git ls-tree -r --name-only e4725dcf21bae83479967b22137325d3a320eb69 .devtool/epic/contract_and_authoring_ergonomics' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 4178ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-16WEWABV' (errno=Operation not permitted)
2026-11-06 02:12:59.428 xcodebuild[45406:383744]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:12:59.548 xcodebuild[45406:383743] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-0LULEGJ0' (errno=Operation not permitted)
2026-11-06 02:12:59.949 xcodebuild[45408:383754]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:13:00.063 xcodebuild[45408:383753] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YAwMfu6Q' (errno=Operation not permitted)
2026-11-06 02:13:00.884 xcodebuild[45442:383863]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:13:00.985 xcodebuild[45442:383862] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-0lGj9eSd' (errno=Operation not permitted)
2026-11-06 02:13:01.341 xcodebuild[45444:383877]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:13:01.442 xcodebuild[45444:383876] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
e4725dcf21bae83479967b22137325d3a320eb69
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-EijEC2fx' (errno=Operation not permitted)
2026-11-06 02:13:02.266 xcodebuild[45448:383900]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:13:02.365 xcodebuild[45448:383899] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-mMmTpMJC' (errno=Operation not permitted)
2026-11-06 02:13:02.721 xcodebuild[45450:383911]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-06 02:13:02.822 xcodebuild[45450:383909] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md
.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.vi.md
.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md
.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md
.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md
.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.vi.md
.devtool/epic/contract_and_authoring_ergonomics/handoff.md
.devtool/epic/contract_and_authoring_ergonomics/task_01_evidence_files_contract.md
.devtool/epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md
.devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md
.devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md

exec
/bin/zsh -lc 'for f in .devtool/epic/contract_and_authoring_ergonomics/*en.md .devtool/epic/contract_and_authoring_ergonomics/handoff.md; do echo "$f"; nl -ba "$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md
     1	# Task Contract and Authoring Ergonomics Design Specification
     2	
     3	## Table of Contents
     4	
     5	- [Overview and Background](#overview-and-background)
     6	- [Problem Statement and Observations Addressed](#problem-statement-and-observations-addressed)
     7	- [Goals and Non-Goals](#goals-and-non-goals)
     8	- [Architecture and Component Design](#architecture-and-component-design)
     9	  - [Component Topology](#component-topology)
    10	  - [1. Evidence Files Contract](#1-evidence-files-contract)
    11	  - [2. Single-Source Task Authoring and Auto-Render Engine](#2-single-source-task-authoring-and-auto-render-engine)
    12	  - [3. Zero-Setup Portable Kit Entrypoint](#3-zero-setup-portable-kit-entrypoint)
    13	  - [4. Verification Row Grammar Reference and Diagnostics](#4-verification-row-grammar-reference-and-diagnostics)
    14	- [Error Handling and Edge Cases](#error-handling-and-edge-cases)
    15	- [Testing and Verification Strategy](#testing-and-verification-strategy)
    16	- [Shared Contract Warnings](#shared-contract-warnings)
    17	- [Dependency Mapping and Roadmap Context](#dependency-mapping-and-roadmap-context)
    18	
    19	## Overview and Background
    20	
    21	During multi-epic packaging and execution in satellite repositories (`lyrics-sync`), fifteen workflow observations (`#0006` through `#0020`) were recorded in `skill-observations/observation-log/`. To deliver focused, verifiable improvements through `dev-lifecycle`, the 15 observations are structured into a three-epic optimization roadmap:
    22	
    23	1. **Epic 1 (`contract_and_authoring_ergonomics`)**: Resolves observations `#0008`, `#0009`, `#0012`, `#0016`, and `#0019` by eliminating manual duplication in task authoring, allowing evidence path declarations under `.devtool/`, providing a zero-setup portable CLI entrypoint for kit tools, and formalizing Verification row grammar diagnostics.
    24	2. **Epic 2 (`execution_and_verification_infrastructure`)**: Resolves observations `#0006`, `#0007`, `#0010`, `#0011`, `#0017`, and `#0018` (worktree capability extras bootstrap, failure-set baseline scripts, opt-in live integration tests, design-time task replay, `MEASURE` phase pattern, and JS static module cache-bust checks).
    25	3. **Epic 3 (`multi_epic_orchestration_and_governance`)**: Resolves observations `#0013`, `#0014`, `#0015`, and `#0020` (`Depends on epic:` metadata, conflict-aware concurrent epic backlog detection, revising packaged epics with `Spec Errata`, and structured Gate Approval Ledger).
    26	
    27	This specification defines the complete design for **Epic 1 (`contract_and_authoring_ergonomics`)**.
    28	
    29	## Problem Statement and Observations Addressed
    30	
    31	| Observation ID | Core Problem | Root Cause |
    32	| :--- | :--- | :--- |
    33	| **#0008** | Verification rows and `Read-only context:` cannot reference evidence files created by a task under `.devtool/epic/<epic_dir>/evidence/`. | `.devtool/` is excluded from `Allowed files:`, while `check_task_contract.py` rejects any non-existent, unignored path not marked `(new)` in `Allowed files:`. |
    34	| **#0009** | `check_epic_readiness.py` (Rule R3) requires task Gherkin blocks to match `bdd_scenarios.en.md` verbatim, whereas `dev-designer` instructs authors to write task-level scenario summaries and `check_task_contract.py --design` does not check R3. | Disconnected rules between `dev-designer` instructions, `check_task_contract.py --design`, and `check_epic_readiness.py`. |
    35	| **#0012** | Every task file is authored and maintained twice (`.devtool/epic/<epic_dir>/task_*.md` and `.devtool/features/task_*.md`), and embedded code snippets drift from verified source files. | Lack of a single-source rendering step in `sync_task_status.py` to generate `.devtool/features/` mirrors and inject verified code or verbatim BDD blocks. |
    36	| **#0016** | Task Verification rows invoke kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/...`), breaking portability across machines, accounts, and plugin versions. | No auto-injected kit environment variable or `PATH` wrapper inside `run_task_checks.py` and `check_epic_readiness.py`, and no check rejecting hardcoded home/plugin paths. |
    37	| **#0019** | Verification table rows suffer from undocumented grammar traps (`\|` unescaping false positives in `principal-review`, bare `VAR=val` parsed as an executable name, grep patterns containing `/` treated as missing file paths, and opaque implicit protected paths). | Implicit parser rules in `task_contract.py` and `check_task_contract.py` are not explained in diagnostics or consolidated in a reference read by `dev-designer` and `principal-review`. |
    38	
    39	## Goals and Non-Goals
    40	
    41	### Goals
    42	
    43	- Introduce an `Evidence files:` subsection under `## Files` in `task_*.md` supporting `(new)` markers for `.devtool/epic/<epic_dir>/evidence/*` paths, validated at both `--design` time and the task Done Gate (`#0008`).
    44	- Establish `.devtool/epic/<epic_dir>/task_*.md` as the single authoritative source of truth and add `sync_task_status.py render <epic_dir> [--source-root <dir>]` to automatically inject verbatim Gherkin blocks from `bdd_scenarios.en.md` (`#0009`), expand `<!-- @@FILE:path@@ -->` code blocks, and generate `.devtool/features/task_*.md` mirrors with rewritten relative links (`#0012`).
    45	- Run R2 (mirror parity) and R3 (verbatim BDD parity) checks early inside `check_task_contract.py --design` (`#0009`, `#0012`).
    46	- Ship a portable `bin/d3nexus` CLI wrapper and automatically inject `D3NEXUS_KIT=<kit_root>` and `PATH="<kit_root>/bin:$PATH"` at runtime inside `run_task_checks.py` and `check_epic_readiness.py` (`#0016`).
    47	- Reject machine- or profile-specific absolute paths in Verification rows inside `check_task_contract.py` (`#0016`).
    48	- Improve `check_task_contract.py` grammar diagnostics (`env VAR=value`, non-path grep patterns, implicit protected path provenance) and document the canonical grammar in `skills/dev-designer/references/verification-row-grammar.md` and `skills/principal-review/SKILL.md` (`#0019`).
    49	
    50	### Non-Goals
    51	
    52	- Changing the 5-column Markdown table layout (`| ID | Phase | Command | Expect | Needs |`) of `## Verification`.
    53	- Modifying worktree bootstrap, failure-set baseline scripts, or multi-epic dependency scheduling (reserved for Epic 2 and Epic 3).
    54	- Breaking backward compatibility for existing completed or in-flight epics that do not declare `Evidence files:` or `<!-- @@FILE:...@@ -->` directives.
    55	
    56	## Architecture and Component Design
    57	
    58	### Component Topology
    59	
    60	```mermaid
    61	flowchart TD
    62	    subgraph SOURCE["1. Single-Source Epic Directory (.devtool/epic/<epic_dir>/)"]
    63	        HLD["<epic_dir>.en.md (HLD)"]
    64	        BDD["bdd_scenarios.en.md"]
    65	        TASK_SRC["task_N_*.md (Authoritative Source)"]
    66	    end
    67	
    68	    subgraph RENDER["2. Render & Mirror Engine (sync_task_status.py render)"]
    69	        SYNC_BDD["Inject Verbatim Gherkin Blocks from Covers: (#0009)"]
    70	        SYNC_EMBED["Expand @@FILE:path@@ Code Blocks (#0012)"]
    71	        SYNC_MIRROR["Write .devtool/features/task_N_*.md & Rewrite Links (#0012)"]
    72	    end
    73	
    74	    subgraph CHECKER["3. Contract & Grammar Gate (task_contract.py + check_task_contract.py)"]
    75	        PARSE_EV["Parse Evidence files: under .devtool/epic/<epic>/evidence/ (#0008)"]
    76	        CHECK_ABS["Reject Hardcoded Home/Plugin Absolute Paths (#0016)"]
    77	        CHECK_R2R3["Verify R2 Mirror & R3 Verbatim BDD at --design (#0009, #0012)"]
    78	        CHECK_GRAMMAR["Diagnose Bare VAR=val, Grep Patterns & Protected Provenance (#0019)"]
    79	    end
    80	
    81	    subgraph EXEC["4. Zero-Setup Runtime (run_task_checks.py + bin/d3nexus)"]
    82	        AUTO_ENV["Compute KIT_ROOT via Path(__file__) & Inject D3NEXUS_KIT + PATH (#0016)"]
    83	        GATE_EV["Verify Declared Evidence files Exist at Done Gate (#0008)"]
    84	    end
    85	
    86	    BDD --> SYNC_BDD
    87	    TASK_SRC --> SYNC_BDD --> SYNC_EMBED --> SYNC_MIRROR
    88	    SYNC_MIRROR --> CHECKER
    89	    HLD --> CHECKER
    90	    CHECKER --> EXEC
    91	```
    92	
    93	### 1. Evidence Files Contract
    94	
    95	In `task_contract.py` and `check_task_contract.py`:
    96	
    97	- **Syntax**: Under `## Files`, a task may optionally include an `Evidence files:` list between `Allowed files:` and `Read-only context:`:
    98	  ```markdown
    99	  ## Files
   100	
   101	  Allowed files:
   102	  - `src/service.py`
   103	
   104	  Evidence files:
   105	  - `.devtool/epic/my_epic/evidence/baseline_failures.txt` (new)
   106	  - `.devtool/epic/my_epic/evidence/benchmark_summary.json` (new)
   107	
   108	  Read-only context:
   109	  - `src/constants.py`
   110	  ```
   111	- **Parsing (`parse_evidence_files(task_text) -> list[AllowedPath]`)**:
   112	  - Uses the same `- `<path>` (new)` bullet format as `parse_allowed_files()`.
   113	  - Every entry must match `.devtool/epic/<epic_dir>/evidence/<filename>` (no `..` traversal, no directories, no paths outside `.devtool/epic/<epic_dir>/evidence/`).
   114	- **Design-Time Grounding (`check_task_contract.py`)**:
   115	  - Paths marked `(new)` in `Evidence files:` are added to the `created` set across the epic's tasks so `check_grounding()` accepts references to those evidence paths in `Verification` rows and `Read-only context:`.
   116	  - If `--design` is passed and an `Evidence files:` entry is marked `(new)` but already exists on disk, `check_task_contract.py` reports a problem (matching `Allowed files:` behavior).
   117	- **Done-Gate Verification (`evaluate_done_gate()` in `task_contract.py`)**:
   118	  - Adds a check verifying that every path listed in `parse_evidence_files(task_text)` exists on disk (`(layout.root / entry.pattern).is_file()`) and is non-empty after the `verify` run completes.
   119	
   120	### 2. Single-Source Task Authoring and Auto-Render Engine
   121	
   122	In `sync_task_status.py`:
   123	
   124	- **New Subcommand**:
   125	  ```bash
   126	  python3 sync_task_status.py render <epic_dir> [--source-root <worktree_or_repo_dir>]
   127	  ```
   128	- **Step 2.1 — Verbatim BDD Injection (`#0009`)**:
   129	  - Reads `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and extracts canonical scenario blocks keyed by scenario ID (reusing the Gherkin extraction logic from `check_epic_readiness.py`).
   130	  - For each `.devtool/epic/<epic_dir>/task_*.md`, reads the `Covers:` line(s). If `Covers:` lists scenario IDs (`SC-...`), locates the Gherkin block in the task's BDD section (or a `<!-- @@BDD_COVERS@@ -->` placeholder) and replaces it with the exact verbatim Gherkin blocks from `bdd_scenarios.en.md` in the order listed in `Covers:`.
   131	  - Fails with exit code 1 if any ID in `Covers:` does not exist in `bdd_scenarios.en.md`.
   132	- **Step 2.2 — Verified File Embedding (`#0012`)**:
   133	  - Scans the task body for directives of the form `<!-- @@FILE:<relative_path>@@ -->` immediately preceding a fenced code block.
   134	  - Resolves `<relative_path>` against `--source-root` (defaulting to the repository root). Rejects any path with `..` or absolute prefix.
   135	  - Replaces the fenced block's interior with the exact file content, automatically using a 4-backtick outer fence (```` ````<lang> ````) if the embedded file contains triple backticks.
   136	- **Step 2.3 — Mirror Generation and Link Rewriting (`#0012`)**:
   137	  - Writes the rendered task back to `.devtool/epic/<epic_dir>/task_*.md`.
   138	  - Generates the corresponding Kanban board mirror in `.devtool/features/task_*.md` (or `.devtool/features/done/task_*.md` when frontmatter `status` is `"done"`), rewriting relative Markdown links pointing to sibling epic files (`](<file>.md)` or `](./<file>.md)`) to `](../epic/<epic_dir>/<file>.md)`.
   139	  - Removes stale `.devtool/features/task_*.md` files whose frontmatter `epic:` matches `<epic_slug>` but whose source file no longer exists in `.devtool/epic/<epic_dir>/`.
   140	- **Step 2.4 — Shift-Left R2 & R3 Checks in `check_task_contract.py --design`**:
   141	  - When `--design` is active (or whenever `bdd_scenarios.en.md` exists alongside `--hld`), `check_task_contract.py` validates that each task's Gherkin scenario blocks match `bdd_scenarios.en.md` verbatim (R3) and that `.devtool/features/<task>.md` matches the normalized epic task file (R2), printing a remediation hint (`run: d3nexus sync-status render <epic_dir>`).
   142	
   143	### 3. Zero-Setup Portable Kit Entrypoint
   144	
   145	- **New CLI (`bin/d3nexus`)**:
   146	  - A portable Python 3 script (`#!/usr/bin/env python3`, `chmod +x`) at `<kit_root>/bin/d3nexus` that resolves `KIT_ROOT = Path(__file__).resolve().parent.parent` and dispatches subcommands:
   147	    - `d3nexus check-doc [args...]` $\rightarrow$ `skills/doc_quality_check/resources/scripts/check_document.py`
   148	    - `d3nexus check-contract [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/check_task_contract.py`
   149	    - `d3nexus check-readiness [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
   150	    - `d3nexus sync-status [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/sync_task_status.py`
   151	    - `d3nexus run-checks [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/run_task_checks.py`
   152	- **Zero-Setup Runtime Environment Injection (`#0016`)**:
   153	  - In `run_task_checks.py` (`run_command()`) and `check_epic_readiness.py`, compute `KIT_ROOT = Path(__file__).resolve().parents[4]` and inject into the subprocess environment:
   154	    - `D3NEXUS_KIT = str(KIT_ROOT)`
   155	    - `PATH = f"{KIT_ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"`
   156	  - No manual setup is required when switching machines, OS users, or Antigravity account profiles.
   157	  - Additionally, `scripts/resume_context.py --sync-zshrc` exports `D3NEXUS_KIT` and adds `<kit_root>/bin` to `PATH` for interactive user shells.
   158	- **Banning Non-Portable Absolute Paths in `check_task_contract.py` (`#0016`)**:
   159	  - `check_task_contract.py` scans every Verification row command for machine- or profile-specific paths (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`). Any match raises a contract problem instructing the author to use `d3nexus <subcommand>` or `$D3NEXUS_KIT/...`.
   160	  - Recognizes `d3nexus` in `strip_wrappers()` / executable checks so `check_task_contract.py` never emits a false `executable d3nexus not found on PATH` warning even if the caller's interactive shell has not added `bin/` to `PATH`.
   161	
   162	### 4. Verification Row Grammar Reference and Diagnostics
   163	
   164	- **Enhanced Grammar Diagnostics in `check_task_contract.py` (`#0019`)**:
   165	  1. **Bare `VAR=value` detection**: If the first command token (without `env`) matches `^[A-Za-z_][A-Za-z0-9_]*=.*`, emit an explicit problem: `inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')`.
   166	  2. **Search pattern exclusion in `command_paths()`**: When a subcommand invokes `grep`, `egrep`, `fgrep`, `rg`, `sed`, or `awk`, exclude the regex/pattern argument (either the token immediately following `-e` / `--regexp`, or the first non-option positional argument when `-e` / `-f` is absent) from path extraction so patterns containing `/` are not misclassified as missing file paths.
   167	  3. **Implicit Protected Path Provenance**: When `check_task_contract.py` prints `Implicit protected paths:`, include the task and row IDs that triggered each path (e.g., `scripts/verify.sh (task_1:V2)`).
   168	- **Consolidated Grammar Reference (`skills/dev-designer/references/verification-row-grammar.md`)**:
   169	  - Documents cell splitting, `\|` unescaping (`parse_row` turns `\|` into `|` before execution), `env VAR=value`, `d3nexus` / `$D3NEXUS_KIT`, `Evidence files:`, implicit protected paths, and 4-backtick outer code fences for task steps containing nested code blocks.
   170	- **Reviewer Alignment (`skills/principal-review/SKILL.md`)**:
   171	  - Explicitly instructs reviewers that `\|` inside Markdown table cells is unescaped to `|` by `task_contract.py` before shell execution, preventing false-positive review findings.
   172	
   173	## Error Handling and Edge Cases
   174	
   175	- **Missing Scenario ID in `Covers:`**: `sync_task_status.py render` aborts with a clear message naming the task file and the unknown scenario ID without modifying files on disk.
   176	- **Path Traversal in `Evidence files:` or `<!-- @@FILE:...@@ -->`**: Any path containing `..`, starting with `/`, or resolving outside the allowed boundary raises a `ContractError` / `UsageError` and exits non-zero.
   177	- **Tasks without `Covers:` (`Covers: none`)**: `sync_task_status.py render` skips BDD Gherkin injection and still performs `@@FILE:...@@` embedding and `.devtool/features/` mirror generation.
   178	- **Legacy Epics**: Epics without `Evidence files:` or `<!-- @@FILE:...@@ -->` continue to pass all checks unchanged.
   179	
   180	## Testing and Verification Strategy
   181	
   182	- **Tier A (Unit Tests)**:
   183	  - `test_check_task_contract.py`: Tests for `Evidence files:` validation, `(new)` evidence path grounding, rejection of `/Users/...` and `.claude/plugins/cache/...` paths, bare `VAR=val` diagnostic, `grep`/`rg` pattern slash exclusion, and early R2/R3 checks.
   184	  - `test_sync_task_status.py`: Tests for `render` subcommand covering verbatim BDD injection from `bdd_scenarios.en.md`, `<!-- @@FILE:...@@ -->` code embedding (including automatic 4-backtick fence promotion), relative link rewriting in `.devtool/features/`, and orphan mirror cleanup.
   185	  - `test_run_task_checks.py`: Tests verifying `D3NEXUS_KIT` and `PATH` injection during row execution and Done-Gate verification of declared `Evidence files:`.
   186	- **Tier C1 (Subcutaneous End-to-End Integration)**:
   187	  - End-to-end test creating a temporary git repository with an HLD, `bdd_scenarios.en.md`, and a single-source `.devtool/epic/<epic>/task_1.md`, running `bin/d3nexus sync-status render`, `bin/d3nexus check-contract --design`, and `bin/d3nexus run-checks verify` (executing `d3nexus check-doc` inside a Verification row and producing a declared evidence file), asserting a clean Done-Gate pass.
   188	- **Repository Quality Gate**:
   189	  - `scripts/verify.sh` and `python-quality-check` (`ruff check`, `mypy`, `pytest`) must pass with 0 errors.
   190	
   191	## Shared Contract Warnings
   192	
   193	- No `shared-contracts/` directory exists in `ai-agent-tools` (this repository is the workflow plugin kit rather than a `D3Nexus` domain service consumer). No shared API contracts, wire payloads, or database schemas are affected.
   194	
   195	## Dependency Mapping and Roadmap Context
   196	
   197	- **Blocks**:
   198	  - **Epic 2 (`execution_and_verification_infrastructure`)**: Relies on `Evidence files:` (`#0008`), `bin/d3nexus` (`#0016`), and `sync_task_status.py render` (`#0012`) to store failure-set baselines (`.devtool/epic/<epic>/evidence/baseline_failures.txt`) and measurement evidence (`#0007`, `#0017`).
   199	  - **Epic 3 (`multi_epic_orchestration_and_governance`)**: Extends `check_task_contract.py` and `sync_task_status.py` for cross-epic dependencies (`#0013`, `#0014`) and packaged epic revisions (`#0015`).
   200	
.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md
     1	# BDD Test Scenarios: Task Contract and Authoring Ergonomics
     2	
     3	## Table of Contents
     4	
     5	- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
     6	- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
     7	- [Dimension 3: State Transitions](#dimension-3-state-transitions)
     8	- [Dimension 4: Async and Concurrency](#dimension-4-async-and-concurrency)
     9	- [Dimension 5: Failures and Resilience](#dimension-5-failures-and-resilience)
    10	
    11	## Dimension 1: Happy Paths
    12	
    13	```gherkin
    14	Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
    15	  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
    16	  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
    17	  When check_task_contract.py runs with "--design"
    18	  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
    19	  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
    20	  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions
    21	
    22	Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
    23	  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
    24	  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
    25	  When "sync_task_status.py render sample_epic" executes
    26	  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
    27	  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
    28	  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings
    29	
    30	Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
    31	  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    32	  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
    33	  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
    34	  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0
    35	
    36	Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
    37	  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    38	  When "check_task_contract.py --design" evaluates the task
    39	  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
    40	  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
    41	```
    42	
    43	## Dimension 2: Edge Cases and Boundaries
    44	
    45	```gherkin
    46	Scenario: [TCAE-EC-01] [Tier A - Unit] Task without Evidence files or Covers line remains backward-compatible
    47	  Given a legacy task file that omits the "Evidence files:" subsection and omits the "Covers:" line
    48	  When "sync_task_status.py render" and "check_task_contract.py --design" run on the epic
    49	  Then "sync_task_status.py render" generates the ".devtool/features/" mirror without modifying the task's BDD section
    50	  And "check_task_contract.py --design" exits 0 with 0 problems
    51	
    52	Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
    53	  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
    54	  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
    55	  When "sync_task_status.py render sample_epic" executes
    56	  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence
    57	
    58	Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
    59	  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
    60	  When "check_task_contract.py --design" inspects the command tokens
    61	  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
    62	  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
    63	```
    64	
    65	## Dimension 3: State Transitions
    66	
    67	```gherkin
    68	Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
    69	  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
    70	  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then ".devtool/features/task_99_obsolete.md" is removed from disk
    73	  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"
    74	
    75	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    76	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    77	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    78	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    79	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    80	  Then "evaluate_done_gate" returns an empty problem list
    81	```
    82	
    83	## Dimension 4: Async and Concurrency
    84	
    85	```gherkin
    86	Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
    87	  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
    88	  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
    89	  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
    90	
    91	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    92	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    93	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    94	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    95	```
    96	
    97	## Dimension 5: Failures and Resilience
    98	
    99	```gherkin
   100	Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
   101	  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
   102	  When "check_task_contract.py --design" evaluates the task
   103	  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments
   104	
   105	Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
   106	  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
   107	  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
   108	  When "check_task_contract.py --design" evaluates the task
   109	  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2
   110	
   111	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
   112	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
   113	  When "sync_task_status.py render sample_epic" executes
   114	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
   115	```
   116	
.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md
     1	# Epic: Task Contract and Authoring Ergonomics
     2	
     3	## Table of Contents
     4	
     5	- [Meta Data](#meta-data)
     6	- [Background](#background)
     7	- [Goals and Non-Goals](#goals-and-non-goals)
     8	- [Architecture and Technical Design](#architecture-and-technical-design)
     9	  - [High-Level Architecture](#high-level-architecture)
    10	  - [Use Cases](#use-cases)
    11	  - [Sequence Diagram](#sequence-diagram)
    12	  - [Integration Test Plan and Boundary Matrix](#integration-test-plan-and-boundary-matrix)
    13	  - [Comprehensive BDD Test Scenarios](#comprehensive-bdd-test-scenarios)
    14	- [Verification Environment](#verification-environment)
    15	- [Shared Contract Impact](#shared-contract-impact)
    16	- [Rollout Strategy and Mitigation](#rollout-strategy-and-mitigation)
    17	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
    18	
    19	## Meta Data
    20	
    21	- **Epic Name**: `contract_and_authoring_ergonomics`
    22	- **Epic Slug**: `contract-and-authoring-ergonomics`
    23	- **Status**: Packaged
    24	- **Target Release**: v1.25.0
    25	- **Platform**: Python
    26	- **Source Spec**: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](./2026-11-06-contract-and-authoring-ergonomics-design.en.md)
    27	
    28	## Background
    29	
    30	During multi-epic packaging and execution in satellite repositories (`lyrics-sync`), five recurring authoring and contract-checking pain points were recorded in `skill-observations/observation-log/`:
    31	- **Observation #0008**: Verification rows and `Read-only context:` cannot reference evidence files created by a task under `.devtool/epic/<epic_dir>/evidence/` because `.devtool/` is barred from `Allowed files:` while `check_task_contract.py` rejects unignored non-existent paths not marked `(new)`.
    32	- **Observation #0009**: `check_epic_readiness.py` (Rule R3) requires task Gherkin blocks to match `bdd_scenarios.en.md` verbatim, whereas `dev-designer` asks for task-level scenario summaries and `check_task_contract.py --design` does not check R3 early.
    33	- **Observation #0012**: Every task file must be maintained in two places (`.devtool/epic/<epic_dir>/task_*.md` and `.devtool/features/task_*.md`), and embedded code snippets drift from verified source files.
    34	- **Observation #0016**: Task Verification rows call kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/...`), breaking portability across machines, accounts, and plugin versions.
    35	- **Observation #0019**: Verification table rows contain undocumented grammar traps (`\|` unescaping false positives in `principal-review`, bare `VAR=val` parsed as an executable name, grep patterns containing `/` treated as missing file paths, and opaque implicit protected paths).
    36	
    37	## Goals and Non-Goals
    38	
    39	### Goals
    40	
    41	- Introduce an `Evidence files:` subsection under `## Files` in `task_*.md` supporting `(new)` markers for `.devtool/epic/<epic_dir>/evidence/*` paths, validated at both `--design` time and the task Done Gate (`#0008`).
    42	- Establish `.devtool/epic/<epic_dir>/task_*.md` as the single authoritative source of truth and add `sync_task_status.py render <epic_dir> [--source-root <dir>]` to automatically inject verbatim Gherkin blocks from `bdd_scenarios.en.md` (`#0009`), expand `<!-- @@FILE:path@@ -->` code blocks, and generate `.devtool/features/task_*.md` mirrors with rewritten relative links (`#0012`).
    43	- Run R2 (mirror parity) and R3 (verbatim BDD parity) checks early inside `check_task_contract.py --design` (`#0009`, `#0012`).
    44	- Ship a portable `bin/d3nexus` CLI wrapper and automatically inject `D3NEXUS_KIT=<kit_root>` and `PATH="<kit_root>/bin:$PATH"` at runtime inside `run_task_checks.py` and `check_epic_readiness.py` (`#0016`).
    45	- Reject machine- or profile-specific absolute paths in Verification rows inside `check_task_contract.py` (`#0016`).
    46	- Improve `check_task_contract.py` grammar diagnostics (`env VAR=value`, non-path grep patterns, implicit protected path provenance) and document the canonical grammar in `skills/dev-designer/references/verification-row-grammar.md` and `skills/principal-review/SKILL.md` (`#0019`).
    47	
    48	### Non-Goals
    49	
    50	- Changing the 5-column Markdown table layout (`| ID | Phase | Command | Expect | Needs |`) of `## Verification`.
    51	- Modifying worktree capability bootstrap, failure-set baseline scripts, or multi-epic dependency scheduling (scoped for Epic 2 and Epic 3).
    52	- Breaking backward compatibility for existing completed or in-flight epics that do not declare `Evidence files:` or `<!-- @@FILE:...@@ -->` directives.
    53	
    54	## Architecture and Technical Design
    55	
    56	### High-Level Architecture
    57	
    58	```mermaid
    59	flowchart TD
    60	    subgraph SOURCE["1. Single-Source Epic Directory (.devtool/epic/<epic_dir>/)"]
    61	        HLD["<epic_dir>.en.md (HLD)"]
    62	        BDD["bdd_scenarios.en.md"]
    63	        TASK_SRC["task_N_*.md (Authoritative Source)"]
    64	    end
    65	
    66	    subgraph RENDER["2. Render & Mirror Engine (sync_task_status.py render)"]
    67	        SYNC_BDD["Inject Verbatim Gherkin Blocks from Covers: (#0009)"]
    68	        SYNC_EMBED["Expand @@FILE:path@@ Code Blocks (#0012)"]
    69	        SYNC_MIRROR["Write .devtool/features/task_N_*.md & Rewrite Links (#0012)"]
    70	    end
    71	
    72	    subgraph CHECKER["3. Contract & Grammar Gate (task_contract.py + check_task_contract.py)"]
    73	        PARSE_EV["Parse Evidence files: under .devtool/epic/<epic>/evidence/ (#0008)"]
    74	        CHECK_ABS["Reject Hardcoded Home/Plugin Absolute Paths (#0016)"]
    75	        CHECK_R2R3["Verify R2 Mirror & R3 Verbatim BDD at --design (#0009, #0012)"]
    76	        CHECK_GRAMMAR["Diagnose Bare VAR=val, Grep Patterns & Protected Provenance (#0019)"]
    77	    end
    78	
    79	    subgraph EXEC["4. Zero-Setup Runtime (run_task_checks.py + bin/d3nexus)"]
    80	        AUTO_ENV["Compute KIT_ROOT via Path(__file__) & Inject D3NEXUS_KIT + PATH (#0016)"]
    81	        GATE_EV["Verify Declared Evidence files Exist at Done Gate (#0008)"]
    82	    end
    83	
    84	    BDD --> SYNC_BDD
    85	    TASK_SRC --> SYNC_BDD --> SYNC_EMBED --> SYNC_MIRROR
    86	    SYNC_MIRROR --> CHECKER
    87	    HLD --> CHECKER
    88	    CHECKER --> EXEC
    89	```
    90	
    91	### Use Cases
    92	
    93	```mermaid
    94	flowchart LR
    95	    DESIGNER["AI Assistant / Designer"] --> UC1["Author Single-Source Task in .devtool/epic/<epic>/"]
    96	    DESIGNER --> UC2["Run d3nexus sync-status render to Sync BDD & Mirrors"]
    97	    DESIGNER --> UC3["Validate Contract, Evidence Paths & Grammar via check-contract --design"]
    98	
    99	    PROGRAMMER["AI Programmer"] --> UC4["Execute Verification Rows with Zero-Setup d3nexus CLI"]
   100	    PROGRAMMER --> UC5["Produce Evidence Files Verified at Task Done Gate"]
   101	```
   102	
   103	### Sequence Diagram
   104	
   105	```mermaid
   106	sequenceDiagram
   107	    autonumber
   108	    actor Designer as AI Assistant (dev-designer)
   109	    participant Render as sync_task_status.py render
   110	    participant Contract as check_task_contract.py --design
   111	    actor Programmer as AI Programmer (dev-implementation)
   112	    participant Runner as run_task_checks.py
   113	    participant CLI as bin/d3nexus
   114	
   115	    Designer->>Render: Invoke render <epic_dir> [--source-root <dir>]
   116	    Render->>Render: Read bdd_scenarios.en.md & inject verbatim Gherkin via Covers:
   117	    Render->>Render: Expand <!-- @@FILE:path@@ --> code fences
   118	    Render->>Render: Write .devtool/features/task_*.md with rewritten relative links
   119	    Render-->>Designer: Exit 0 (rendered N tasks and mirrors)
   120	    Designer->>Contract: Invoke check_task_contract.py --design
   121	    Contract->>Contract: Validate Evidence files:, R2 mirror parity, R3 verbatim BDD
   122	    Contract->>Contract: Check portable paths (no /Users/...) & grammar rules
   123	    Contract-->>Designer: Result: 0 problems — PASS
   124	    Programmer->>Runner: Invoke run_task_checks.py verify <task_mirror>
   125	    Runner->>Runner: Inject D3NEXUS_KIT & PATH=<kit_root>/bin
   126	    Runner->>CLI: Execute row command `d3nexus check-doc ...`
   127	    CLI-->>Runner: Exit 0
   128	    Runner->>Runner: evaluate_done_gate() checks Evidence files exist on disk
   129	    Runner-->>Programmer: Done gate PASS
   130	```
   131	
   132	### Integration Test Plan and Boundary Matrix
   133	
   134	```text
   135	Integration test roots: tests/, skills/dev-implementation/resources/scripts/
   136	Protected paths: .agents/quality/**, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md
   137	Integration results: python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml -> build/test-results/pytest.xml
   138	```
   139	
   140	| Boundary Seam | Testing Strategy | Verification Target |
   141	| :--- | :--- | :--- |
   142	| `task_contract.py` & `check_task_contract.py` | Subcutaneous CLI & parser unit/integration tests on temporary git repositories | Verify `Evidence files:` parsing, `(new)` grounding, Done-Gate file existence check, bare `VAR=val` errors, grep pattern exclusion, and early R2/R3 enforcement |
   143	| `sync_task_status.py render` | Real filesystem rendering tests across `.devtool/epic/<epic>/` and `.devtool/features/` | Verify verbatim Gherkin injection from `bdd_scenarios.en.md`, `@@FILE:path@@` embedding with 4-backtick promotion, relative link rewriting, and orphan mirror cleanup |
   144	| `bin/d3nexus` & `run_task_checks.py` | Subprocess execution tests in temporary git repositories | Verify zero-setup `D3NEXUS_KIT` and `PATH` injection, `d3nexus` subcommand dispatch, and rejection of hardcoded `/Users/...` or plugin cache paths |
   145	| Reviewer & Authoring Docs | Document lint and contract checks via `check_document.py` | Verify `verification-row-grammar.md`, `dev-designer/SKILL.md`, and `principal-review/SKILL.md` alignment |
   146	
   147	## Verification Environment
   148	
   149	- Execution environment: Local macOS / Linux CLI with Python 3.11+, Git, `pytest`, `ruff`, and `mypy` installed.
   150	- No live network or external database dependencies: All tests execute against temporary local Git repositories created via `tempfile.TemporaryDirectory` / `tmp_path`.
   151	- File system isolation: Test runs never mutate the main repository's `.devtool/` state or working tree.
   152	
   153	### Comprehensive BDD Test Scenarios
   154	
   155	The suite covers all 5 dimensions under the `[TCAE-]` prefix:
   156	1. **Happy Paths (`TCAE-HP-01` .. `TCAE-HP-04`)**: Declaring and verifying `(new)` `Evidence files:`, rendering verbatim BDD and `.devtool/features/` mirrors from single-source epic tasks, executing `d3nexus` commands via zero-setup environment injection, and clean grammar validation with `\|` unescaping and `env VAR=val`.
   157	2. **Edge Cases (`TCAE-EC-01` .. `TCAE-EC-03`)**: Tasks without `Covers:` (`Covers: none`), embedded files containing triple-backtick fences automatically promoted to 4-backtick outer fences, and grep/rg/sed search patterns containing `/` excluded from missing-file path errors.
   158	3. **State Transitions (`TCAE-ST-01` .. `TCAE-ST-02`)**: Orphan mirror cleanup and `done/` board location synchronization during `render`, and Done-Gate transition from FAIL (when a declared `Evidence files:` output is missing) to PASS (once created by verification).
   159	4. **Async & Concurrency (`TCAE-AR-01` .. `TCAE-AR-02`)**: Isolated `D3NEXUS_KIT` / `PATH` injection across parallel worktrees without environment leakage, and deterministic multi-task rendering across worktrees.
   160	5. **Failures & Resilience (`TCAE-FR-01` .. `TCAE-FR-03`)**: Rejecting `Evidence files:` outside `.devtool/epic/<epic>/evidence/` or with `..` traversal, rejecting hardcoded `/Users/...` or `.claude/plugins/cache/...` paths and bare `VAR=val` assignments, and aborting `render` cleanly when `Covers:` references an unknown scenario ID.
   161	
   162	## Shared Contract Impact
   163	
   164	None — self-contained feature in `ai-agent-tools`.
   165	
   166	## Rollout Strategy and Mitigation
   167	
   168	- **Phase 1**: Extend `task_contract.py` and `check_task_contract.py` with `Evidence files:` support and Done-Gate verification (`Task 01`).
   169	- **Phase 2**: Implement `sync_task_status.py render` and shift-left R2/R3 validation in `check_task_contract.py --design` (`Task 02`).
   170	- **Phase 3**: Add `bin/d3nexus`, runtime `D3NEXUS_KIT`/`PATH` injection in `run_task_checks.py` and `check_epic_readiness.py`, and absolute path rejection (`Task 03`).
   171	- **Phase 4**: Add Verification row grammar diagnostics (`env VAR=val`, grep pattern exclusion, implicit protected path provenance) and author `verification-row-grammar.md` + skill updates (`Task 04`).
   172	- **Phase 5**: Execute end-to-end subcutaneous integration tests and repository verification (`Task 05`).
   173	- **Rollback Plan**: All changes are backwards-compatible additions to standard library Python scripts; reverting the epic merge commit cleanly restores previous checker behavior.
   174	
   175	## Kanban Tasks Breakdown
   176	
   177	- [Task 01: Evidence Files Contract and Done-Gate Verification](./task_01_evidence_files_contract.md)
   178	- [Task 02: Single-Source Task Render Engine and Shift-Left R2/R3 Checks](./task_02_single_source_render_engine.md)
   179	- [Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection](./task_03_portable_d3nexus_cli_and_env.md)
   180	- [Task 04: Verification Row Grammar Diagnostics and Reference Documentation](./task_04_verification_grammar_and_docs.md)
   181	- [Task 05: End-to-End Integration and Acceptance Verification](./task_05_end_to_end_contract_acceptance.md)
.devtool/epic/contract_and_authoring_ergonomics/handoff.md
     1	# Handoff: contract-and-authoring-ergonomics
     2	
     3	## Table of Contents
     4	
     5	- [Status](#status)
     6	- [Identifiers](#identifiers)
     7	- [Read First](#read-first)
     8	- [Resume Prompt](#resume-prompt)
     9	- [Execution Guardrails for Receiving LLM](#execution-guardrails-for-receiving-llm)
    10	- [Open Notes](#open-notes)
    11	- [Rules for the Receiving Agent](#rules-for-the-receiving-agent)
    12	
    13	## Status
    14	
    15	- **Packaged**: 2026-11-06
    16	- **Design commit**: `1e5c8be` — `HEAD` before the packaging commit, or `uncommitted` when `auto_commit` is false
    17	- **Base branch**: `main`
    18	- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
    19	- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.
    20	
    21	## Identifiers
    22	
    23	| Placeholder | Value |
    24	|-------------|-------|
    25	| `<epic_dir>` | `contract_and_authoring_ergonomics` |
    26	| `<epic_slug>` | `contract-and-authoring-ergonomics` |
    27	
    28	These are usually different strings. Never derive one from the other.
    29	
    30	## Read First
    31	
    32	1. `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 5 tasks.
    33	2. `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md` — the behavioural contract.
    34	3. `.devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.en.md` — the approved source spec.
    35	4. `.devtool/epic/contract_and_authoring_ergonomics/principal_review.md`, when present — Principal Review rounds and decisions.
    36	
    37	## Resume Prompt
    38	
    39	```text
    40	[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
    41	Use the d3nexus:dev-implementation skill for the `contract-and-authoring-ergonomics` epic.
    42	Read .devtool/epic/contract_and_authoring_ergonomics/handoff.md first.
    43	Run: python3 scripts/resume_context.py --role programmer --epic contract-and-authoring-ergonomics
    44	Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
    45	Gates 1 and 2 are passed; do not re-run brainstorming or design.
    46	Gate 3 is pending: present the execution order to me and wait for my confirmation.
    47	```
    48	
    49	## Execution Guardrails for Receiving LLM
    50	
    51	Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:
    52	
    53	1. **Bounded context protocol**:
    54	   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
    55	   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
    56	   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
    57	   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
    58	2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
    59	3. **Zero test fakery**: Tests import or invoke real production symbols and do not reconstruct retry loops, progress math, callback behavior, or configuration resolution.
    60	4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.
    61	
    62	## Open Notes
    63	
    64	- **Three-Epic Optimization Roadmap**: This epic (`contract_and_authoring_ergonomics`) is Epic 1 of 3 addressing the 15 open observations in `skill-observations/observation-log/` (`#0008, #0009, #0012, #0016, #0019`). Epic 2 (`execution_and_verification_infrastructure` for `#0006, #0007, #0010, #0011, #0017, #0018`) and Epic 3 (`multi_epic_orchestration_and_governance` for `#0013, #0014, #0015, #0020`) follow sequentially.
    65	- **Zero-Setup `D3NEXUS_KIT` & `bin/d3nexus`**: `run_task_checks.py` and `check_epic_readiness.py` compute `KIT_ROOT = Path(__file__).resolve().parents[4]` dynamically at runtime and inject `D3NEXUS_KIT` and `PATH="<kit_root>/bin:$PATH"` into child subprocesses, requiring zero manual setup across machines or profiles.
    66	- **Mypy Import Narrowing**: Tasks 01–04 use `--follow-imports=silent` on `mypy` rows because `check_bdd_traceability.py` has an unnarrowed `Optional[str]` on `fence` in `scenario_ids()`; Task 05 narrows `fence` in `check_bdd_traceability.py` so `mypy` passes cleanly without `--follow-imports=silent`.
    67	- **Observation #0021**: Logged during Stage 2 when an epic directory starting with `task_` collided with `task_*.md` globs; Task 02 (`render_epic_tasks`) should match task files with `re.fullmatch(r"task_[0-9]+_.*\.md", path.name)` (or exclude `*.en.md`/`*.vi.md`).
    68	
    69	## Rules for the Receiving Agent
    70	
    71	- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
    72	- This handoff does not pass Gate 3. The developer confirms the execution order.
    73	- Unless the design commit is `uncommitted`: if `git log 1e5c8be..main -- .devtool/epic/contract_and_authoring_ergonomics` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
    74	- This file is a dated record. It is never updated after packaging.
    75	- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.

exec
/bin/zsh -lc 'for f in .devtool/epic/contract_and_authoring_ergonomics/task_*.md; do echo "$f"; nl -ba "$f"; done' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
.devtool/epic/contract_and_authoring_ergonomics/task_01_evidence_files_contract.md
     1	---
     2	id: "task_01_evidence_files_contract"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "contract", "python"]
    12	order: "a1"
    13	---
    14	
    15	# Task 01: Evidence Files Contract and Done-Gate Verification
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observation #0008: task files cannot list `.devtool/` paths under `Allowed files:`, yet `check_task_contract.py` rejects any `Verification` row or `Read-only context:` path that does not exist on disk, is not git-ignored, and is not marked `(new)` in some task. Consequently, tasks that produce evidence artifacts under `.devtool/epic/<epic_dir>/evidence/` (such as `baseline_failures.txt`, `results.json`, or `summary.json`) cannot reference those files in their own or downstream Verification rows.
    22	
    23	This task introduces an optional `Evidence files:` subsection under `## Files` in `task_contract.py` and `check_task_contract.py`:
    24	1. `parse_evidence_files(task_text: str) -> list[AllowedPath]` parses `- `<path>` (new)` bullets under `Evidence files:` inside `## Files`.
    25	2. `check_evidence(check, stem, text, design)` in `check_task_contract.py` validates that every entry resides strictly under `.devtool/epic/<epic_dir>/evidence/<filename>` without `..` segments or bare directories, and when `--design` is passed, ensures `(new)` entries do not already exist on disk.
    26	3. `Evidence files:` entries marked `(new)` are added to the `created` set in `check_task_contract.py` so `check_grounding()` accepts references to them in `Verification` rows and `Read-only context:`.
    27	4. `evaluate_done_gate(task_file: Path)` in `task_contract.py` verifies that every path declared in `parse_evidence_files(task_text)` exists as a non-empty file on disk after `verify` completes.
    28	
    29	## Files
    30	
    31	Allowed files:
    32	- `skills/dev-implementation/resources/scripts/task_contract.py`
    33	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    34	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    35	- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
    36	
    37	Read-only context:
    38	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    39	- `.devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md` (canonical BDD scenarios)
    40	
    41	## Design Rationale
    42	
    43	Applicable skills: `python-quality-check`, `test-driven-development`.
    44	Separating `Evidence files:` from `Allowed files:` preserves the invariant that `Allowed files:` tracks production/test code outside `.devtool/` (which `fingerprint()` and `SCOPE` evaluate with `:(exclude).devtool`), while giving `.devtool/epic/<epic_dir>/evidence/*` artifacts first-class contract grounding at design time and existence enforcement at the Done Gate.
    45	
    46	## Impact Analysis & Blast Radius
    47	
    48	- **Target Files & Symbols**:
    49	  - `skills/dev-implementation/resources/scripts/task_contract.py`: `parse_allowed_files`, `evaluate_done_gate`, and new `parse_evidence_files`.
    50	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_allowed`, `check_grounding`, `check_task`, `main`, and new `check_evidence`.
    51	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/run_task_checks.py`, `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    52	- **Cross-Platform Bridges**: None.
    53	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage across modified functions in `task_contract.py` and `check_task_contract.py`.
    54	
    55	### BDD SCENARIOS
    56	
    57	Covers: TCAE-HP-01, TCAE-EC-01, TCAE-FR-01
    58	
    59	```gherkin
    60	Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
    61	  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
    62	  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
    63	  When check_task_contract.py runs with "--design"
    64	  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
    65	  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
    66	  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions
    67	
    68	Scenario: [TCAE-EC-01] [Tier A - Unit] Task without Evidence files or Covers line remains backward-compatible
    69	  Given a legacy task file that omits the "Evidence files:" subsection and omits the "Covers:" line
    70	  When "sync_task_status.py render" and "check_task_contract.py --design" run on the epic
    71	  Then "sync_task_status.py render" generates the ".devtool/features/" mirror without modifying the task's BDD section
    72	  And "check_task_contract.py --design" exits 0 with 0 problems
    73	
    74	Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
    75	  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
    76	  When "check_task_contract.py --design" evaluates the task
    77	  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments
    78	```
    79	
    80	## Verification
    81	
    82	| ID | Phase | Command | Expect | Needs |
    83	|----|-------|---------|--------|-------|
    84	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py::test_TCAE_HP_01_evidence_files_grounding` | exit 1; contains "FAILED" | — |
    85	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0; contains "passed" | — |
    86	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py` | exit 0 | — |
    87	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
    88	| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py skills/dev-implementation/resources/scripts/test_run_task_checks.py --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |
    89	
    90	## Stop and Report If
    91	
    92	- A command, path, symbol or anchor named in this task does not match the repository.
    93	- A Verification row fails for a reason other than its Expect.
    94	- The work needs a change to a file outside Allowed files, or to a protected path.
    95	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    96	  Covers line.
    97	- A variable named in the Needs column is unset.
    98	
    99	## Decisions Already Made
   100	
   101	- Grounded existing symbol `parse_allowed_files(task_text: str) -> list[AllowedPath]` in `skills/dev-implementation/resources/scripts/task_contract.py`: add sibling frozen contract `parse_evidence_files(task_text: str) -> list[AllowedPath]` parsing `- `<path>` (new)` bullets under `Evidence files:` inside `## Files`.
   102	- Every `Evidence files:` path must match `^\.devtool/epic/[A-Za-z0-9_-]+/evidence/[A-Za-z0-9_.-]+$` and must not contain `..` or trailing `/`.
   103	- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `main()` unions `{entry.pattern for text in tasks.values() for entry in tc.parse_evidence_files(text) if entry.new}` into `created` so `check_grounding()` accepts those paths in `Verification` rows and `Read-only context:`.
   104	- In `skills/dev-implementation/resources/scripts/task_contract.py`, `evaluate_done_gate(task_file: Path)` checks every entry in `parse_evidence_files(task_text)` and appends `"condition 8: evidence file <path> declared in Evidence files was not created or is empty"` if the file is missing or has size 0.
   105	
   106	## Definition of Done
   107	
   108	- `parse_evidence_files` and `check_evidence` validate `Evidence files:` entries and ground `(new)` evidence paths across tasks. (V2)
   109	- `evaluate_done_gate` enforces that declared `Evidence files:` exist and are non-empty on disk. (V2, V5)
   110	- `ruff` and `mypy` pass with zero errors on all modified files. (V3, V4)
   111	- Automated tests covering `TCAE-HP-01`, `TCAE-EC-01`, and `TCAE-FR-01` pass and write JUnit XML results. (V5)
   112	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   113	
   114	## Dependencies & Blockers
   115	
   116	- Blocked by: None (first task in execution order).
   117	
   118	## References & Rollback
   119	
   120	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   121	- Rollback: `git revert` the task commit to restore `task_contract.py` and `check_task_contract.py`.
.devtool/epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md
     1	---
     2	id: "task_02_single_source_render_engine"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "authoring", "python"]
    12	order: "a2"
    13	---
    14	
    15	# Task 02: Single-Source Task Render Engine and Shift-Left R2/R3 Checks
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observations #0009 and #0012:
    22	1. Authors currently maintain two copies of every task file (`.devtool/epic/<epic_dir>/task_*.md` and `.devtool/features/task_*.md`), and manually copy Gherkin blocks from `bdd_scenarios.en.md` and code blocks from source files.
    23	2. `check_epic_readiness.py` checks R2 (mirror parity) and R3 (verbatim BDD scenario parity), but `check_task_contract.py --design` does not run R2 or R3, so mismatches are discovered late.
    24	
    25	This task adds `sync_task_status.py render <epic_dir> [--source-root <dir>]` and integrates R2/R3 checks into `check_task_contract.py --design`:
    26	1. `render_epic_tasks(root: Path, epic_dir: str, source_root: Path | None = None)` in `sync_task_status.py`:
    27	   - Reads `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and injects the verbatim Gherkin scenario blocks matching each task's `Covers:` line into the task's `### BDD SCENARIOS` section.
    28	   - Expands `<!-- @@FILE:<relative_path>@@ -->` directives by replacing the immediately following fenced code block with the contents of `<source_root>/<relative_path>`, promoting the outer fence to 4 backticks (` ```` `) when the embedded file contains triple backticks.
    29	   - Generates `.devtool/features/task_*.md` (or `.devtool/features/done/task_*.md` when `status: "done"`), rewriting relative links `](< sibling >.md)` / `](./< sibling >.md)` to `](../epic/<epic_dir>/< sibling >.md)` and removing orphan mirrors for the same epic slug.
    30	2. `check_task_contract.py --design` validates R3 (task Gherkin blocks match `bdd_scenarios.en.md` verbatim) and R2 (when a `.devtool/features/` mirror exists, its normalized content matches the epic task).
    31	
    32	## Files
    33	
    34	Allowed files:
    35	- `skills/dev-implementation/resources/scripts/sync_task_status.py`
    36	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    37	- `skills/dev-implementation/resources/scripts/test_sync_task_status.py`
    38	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    39	
    40	Read-only context:
    41	- `skills/dev-implementation/resources/scripts/check_epic_readiness.py` (reference for R2 and R3 extraction and normalization rules)
    42	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    43	
    44	## Design Rationale
    45	
    46	Applicable skills: `python-quality-check`, `test-driven-development`.
    47	Placing `render` inside `sync_task_status.py` keeps all task-mirror and frontmatter synchronization logic in one stdlib-only module while eliminating manual dual-file editing.
    48	
    49	## Impact Analysis & Blast Radius
    50	
    51	- **Target Files & Symbols**:
    52	  - `skills/dev-implementation/resources/scripts/sync_task_status.py`: `main`, `board_location`, and new `render_epic_tasks`.
    53	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `check_task`, `check_hld`, and new `check_r2_r3_parity`.
    54	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    55	- **Cross-Platform Bridges**: None.
    56	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `render_epic_tasks` and `check_r2_r3_parity`.
    57	
    58	### BDD SCENARIOS
    59	
    60	Covers: TCAE-HP-02, TCAE-EC-02, TCAE-ST-01
    61	
    62	```gherkin
    63	Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
    64	  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
    65	  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
    66	  When "sync_task_status.py render sample_epic" executes
    67	  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
    68	  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
    69	  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings
    70	
    71	Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
    72	  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
    73	  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
    74	  When "sync_task_status.py render sample_epic" executes
    75	  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence
    76	
    77	Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
    78	  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
    79	  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
    80	  When "sync_task_status.py render sample_epic" executes
    81	  Then ".devtool/features/task_99_obsolete.md" is removed from disk
    82	  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"
    83	```
    84	
    85	## Verification
    86	
    87	| ID | Phase | Command | Expect | Needs |
    88	|----|-------|---------|--------|-------|
    89	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py::test_TCAE_HP_02_render_single_source` | exit 1; contains "FAILED" | — |
    90	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
    91	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
    92	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
    93	| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_sync_task_status.py skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |
    94	
    95	## Stop and Report If
    96	
    97	- A command, path, symbol or anchor named in this task does not match the repository.
    98	- A Verification row fails for a reason other than its Expect.
    99	- The work needs a change to a file outside Allowed files, or to a protected path.
   100	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
   101	  Covers line.
   102	- A variable named in the Needs column is unset.
   103	
   104	## Decisions Already Made
   105	
   106	- CLI interface in `skills/dev-implementation/resources/scripts/sync_task_status.py`: `sync_task_status.py render <epic_dir> [--source-root <path>]`.
   107	- When rendering BDD scenarios: if a task has a `Covers:` line with scenario IDs, `render_epic_tasks` extracts the matching scenario blocks from `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and replaces the ` ```gherkin ... ``` ` block under `### BDD SCENARIOS` (or inserts one immediately after the `Covers:` line). If any covered ID is missing from `bdd_scenarios.en.md`, `render_epic_tasks` raises ValueError / exits 1 without writing partial mirrors.
   108	- When expanding `<!-- @@FILE:<rel_path>@@ -->`: `<rel_path>` must be relative without `..` segments; if the target file content contains ` ``` `, the outer code fence uses ` ```` ` (4 backticks).
   109	- Mirror link rewriting: links targeting files inside `.devtool/epic/<epic_dir>/` (such as `](<epic_dir>.en.md)` or `](./task_01_foo.md)`) are rewritten to `](../epic/<epic_dir>/<target>)` in `.devtool/features/<task>.md`, matching `check_epic_readiness.py` R2 normalization `mirror_text.replace(f"](../epic/{epic_dir}/", "](") == epic_text`.
   110	
   111	## Definition of Done
   112	
   113	- `sync_task_status.py render <epic_dir>` injects verbatim Gherkin blocks, expands `@@FILE:...@@` fences, writes `.devtool/features/` mirrors, and removes orphan mirrors. (V2)
   114	- `check_task_contract.py --design` checks R3 verbatim scenario parity and R2 mirror parity when mirrors exist. (V2)
   115	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   116	- Automated tests for `TCAE-HP-02`, `TCAE-EC-02`, and `TCAE-ST-01` pass and write JUnit XML results. (V5)
   117	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   118	
   119	## Dependencies & Blockers
   120	
   121	- Blocked by [Task 01](task_01_evidence_files_contract.md)
   122	
   123	## References & Rollback
   124	
   125	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   126	- Rollback: `git revert` the task commit to restore `sync_task_status.py` and `check_task_contract.py`.
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md
     1	---
     2	id: "task_03_portable_d3nexus_cli_and_env"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "portability", "cli"]
    12	order: "a3"
    13	---
    14	
    15	# Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observation #0016: task Verification rows invoke kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/tess/.claude/plugins/cache/...`), which fail when run on another machine, OS user, account profile, or plugin version.
    22	
    23	This task provides a zero-setup portable CLI entrypoint and bans hardcoded user/plugin paths in Verification rows:
    24	1. Create executable `bin/d3nexus` dispatching subcommands (`check-doc`, `check-contract`, `check-readiness`, `sync-status`, `run-checks`) to the kit's scripts relative to `Path(__file__).resolve().parent.parent`.
    25	2. In `run_task_checks.py` (`run_command()`) and `check_epic_readiness.py`, automatically compute `KIT_ROOT = Path(__file__).resolve().parents[4]` and inject `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH="<kit_root>/bin:$PATH"` into the child process environment without mutating `os.environ` of the parent process.
    26	3. Update `scripts/resume_context.py` (`--sync-zshrc`) so interactive terminal shells also export `D3NEXUS_KIT` and prepend `<kit_root>/bin` to `PATH`.
    27	4. In `check_task_contract.py`, reject any Verification row command containing hardcoded user home or plugin cache paths (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`) and recognize `d3nexus` as a built-in kit executable.
    28	
    29	## Files
    30	
    31	Allowed files:
    32	- `bin/d3nexus` (new)
    33	- `skills/dev-implementation/resources/scripts/run_task_checks.py`
    34	- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
    35	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    36	- `skills/dev-implementation/resources/scripts/task_contract.py`
    37	- `scripts/resume_context.py`
    38	- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
    39	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    40	
    41	Read-only context:
    42	- `skills/doc_quality_check/resources/scripts/check_document.py` (target of `d3nexus check-doc`)
    43	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    44	
    45	## Design Rationale
    46	
    47	Applicable skills: `python-quality-check`, `test-driven-development`.
    48	Deriving `KIT_ROOT` dynamically from `Path(__file__).resolve().parents[4]` inside `run_task_checks.py` guarantees zero manual setup when switching machines, accounts, or plugin cache versions.
    49	
    50	## Impact Analysis & Blast Radius
    51	
    52	- **Target Files & Symbols**:
    53	  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_command` and new `kit_env`.
    54	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, and new `check_portable_command`.
    55	  - `skills/dev-implementation/resources/scripts/task_contract.py`: `strip_wrappers`.
    56	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    57	- **Cross-Platform Bridges**: None.
    58	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `bin/d3nexus`, `kit_env`, and `check_portable_command`.
    59	
    60	### BDD SCENARIOS
    61	
    62	Covers: TCAE-HP-03, TCAE-AR-01, TCAE-FR-02
    63	
    64	```gherkin
    65	Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
    66	  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    67	  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
    68	  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
    69	  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0
    70	
    71	Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
    72	  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
    73	  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
    74	  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
    75	
    76	Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
    77	  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
    78	  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
    79	  When "check_task_contract.py --design" evaluates the task
    80	  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2
    81	```
    82	
    83	## Verification
    84	
    85	| ID | Phase | Command | Expect | Needs |
    86	|----|-------|---------|--------|-------|
    87	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py::test_TCAE_HP_03_d3nexus_zero_setup_env` | exit 1; contains "FAILED" | — |
    88	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
    89	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py bin/d3nexus skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py scripts/resume_context.py` | exit 0 | — |
    90	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py` | exit 0 | — |
    91	| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |
    92	
    93	## Stop and Report If
    94	
    95	- A command, path, symbol or anchor named in this task does not match the repository.
    96	- A Verification row fails for a reason other than its Expect.
    97	- The work needs a change to a file outside Allowed files, or to a protected path.
    98	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    99	  Covers line.
   100	- A variable named in the Needs column is unset.
   101	
   102	## Decisions Already Made
   103	
   104	- `KIT_ROOT` in `skills/dev-implementation/resources/scripts/run_task_checks.py` is `Path(__file__).resolve().parents[4]`.
   105	- `kit_env() -> dict[str, str]` returns a copy of `os.environ` with `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH=f"{KIT_ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"`.
   106	- `bin/d3nexus` is an executable Python 3 script (`0o755`) supporting subcommands:
   107	  - `check-doc` -> `skills/doc_quality_check/resources/scripts/check_document.py`
   108	  - `check-contract` -> `skills/dev-implementation/resources/scripts/check_task_contract.py`
   109	  - `check-readiness` -> `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
   110	  - `sync-status` -> `skills/dev-implementation/resources/scripts/sync_task_status.py`
   111	  - `run-checks` -> `skills/dev-implementation/resources/scripts/run_task_checks.py`
   112	- `NON_PORTABLE_PATH_RE` in `check_task_contract.py` matches `(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)` and reports `"non-portable path '<match>' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'"`.
   113	
   114	## Definition of Done
   115	
   116	- `bin/d3nexus` dispatches kit subcommands and is automatically placed on `PATH` with `D3NEXUS_KIT` by `run_task_checks.py` and `check_epic_readiness.py`. (V2, V5)
   117	- `check_task_contract.py` rejects hardcoded user home and plugin cache paths in Verification rows. (V2)
   118	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   119	- Automated tests for `TCAE-HP-03`, `TCAE-AR-01`, and `TCAE-FR-02` pass and write JUnit XML results. (V5)
   120	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   121	
   122	## Dependencies & Blockers
   123	
   124	- Blocked by [Task 02](task_02_single_source_render_engine.md)
   125	
   126	## References & Rollback
   127	
   128	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   129	- Rollback: `git revert` the task commit to remove `bin/d3nexus` and restore runtime scripts.
.devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md
     1	---
     2	id: "task_04_verification_grammar_and_docs"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "grammar", "documentation"]
    12	order: "a4"
    13	---
    14	
    15	# Task 04: Verification Row Grammar Diagnostics and Reference Documentation
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observation #0019: authors and reviewers repeatedly encounter undocumented grammar rules in Verification tables:
    22	1. `task_contract.py` unescapes `\|` to `|` in table cells, which caused a Principal Review round to falsely flag valid rows as broken.
    23	2. Inline `VAR=value cmd` without `env` is parsed as an executable named `VAR=value`.
    24	3. Search patterns in `grep`, `rg`, `sed`, and `awk` containing `/` (such as `grep -E 'foo/bar' file.txt`) are misclassified by `command_paths()` as missing file paths.
    25	4. Tracked scripts executed by a row become implicit protected paths without reporting which task/row triggered them.
    26	
    27	This task improves `check_task_contract.py` diagnostics, creates the canonical `skills/dev-designer/references/verification-row-grammar.md` reference, and updates `skills/dev-designer/SKILL.md` and `skills/principal-review/SKILL.md`.
    28	
    29	## Files
    30	
    31	Allowed files:
    32	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    33	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    34	- `skills/dev-designer/references/verification-row-grammar.md` (new)
    35	- `skills/dev-designer/SKILL.md`
    36	- `skills/principal-review/SKILL.md`
    37	
    38	Read-only context:
    39	- `skills/dev-designer/references/verification-rows.md` (existing per-platform example rows)
    40	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    41	
    42	## Design Rationale
    43	
    44	Applicable skills: `python-quality-check`, `doc_quality_check`, `test-driven-development`.
    45	Centralizing all Verification table grammar rules in `skills/dev-designer/references/verification-row-grammar.md` and aligning `check_task_contract.py` diagnostics with `principal-review` eliminates false positives in both automated checks and AI reviews.
    46	
    47	## Impact Analysis & Blast Radius
    48	
    49	- **Target Files & Symbols**:
    50	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, `main`.
    51	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    52	- **Cross-Platform Bridges**: None.
    53	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `command_paths` and grammar diagnostics in `check_task_contract.py`.
    54	
    55	### BDD SCENARIOS
    56	
    57	Covers: TCAE-HP-04, TCAE-EC-03
    58	
    59	```gherkin
    60	Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
    61	  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    62	  When "check_task_contract.py --design" evaluates the task
    63	  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
    64	  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
    65	
    66	Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
    67	  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
    68	  When "check_task_contract.py --design" inspects the command tokens
    69	  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
    70	  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
    71	```
    72	
    73	## Verification
    74	
    75	| ID | Phase | Command | Expect | Needs |
    76	|----|-------|---------|--------|-------|
    77	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py::test_TCAE_EC_03_grep_slash_pattern_excluded` | exit 1; contains "FAILED" | — |
    78	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
    79	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
    80	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
    81	| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-designer/references/verification-row-grammar.md` | exit 0; contains "0 findings" | — |
    82	| V6 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |
    83	
    84	## Stop and Report If
    85	
    86	- A command, path, symbol or anchor named in this task does not match the repository.
    87	- A Verification row fails for a reason other than its Expect.
    88	- The work needs a change to a file outside Allowed files, or to a protected path.
    89	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    90	  Covers line.
    91	- A variable named in the Needs column is unset.
    92	
    93	## Decisions Already Made
    94	
    95	- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `command_paths(command: str)` splits subcommands on `tc.CONTROL_TOKENS` (`&&`, `||`, `;`, `|`). For any subcommand whose unwrapped program is `grep`, `egrep`, `fgrep`, `rg`, `sed`, or `awk`, the pattern argument (the token after `-e`/`--regexp` or the first non-flag positional argument when no `-e`/`-f` flag is present) is skipped before collecting path tokens.
    96	- When the first token of a subcommand (before `env`) matches `^[A-Za-z_][A-Za-z0-9_]*=.*`, `check_grounding` records a problem: `"inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')"`.
    97	- `Implicit protected paths:` in `check_task_contract.py` formats each entry as `<path> (<task_stem>:<row_id>, ...)`.
    98	- `skills/dev-designer/references/verification-row-grammar.md` includes a `## Table of Contents` and documents all 6 rules (`\|` unescaping, `env VAR=val`, grep pattern rules, `Evidence files:`, `d3nexus` / `$D3NEXUS_KIT`, and 4-backtick outer code fences).
    99	
   100	## Definition of Done
   101	
   102	- `command_paths()` excludes `grep`/`rg`/`sed`/`awk` pattern arguments from missing-path errors and reports bare `VAR=val` assignments and implicit protected path provenance. (V2)
   103	- `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-designer/SKILL.md`, and `skills/principal-review/SKILL.md` are updated and pass document linting. (V5)
   104	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   105	- Automated tests for `TCAE-HP-04` and `TCAE-EC-03` pass and write JUnit XML results. (V6)
   106	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   107	
   108	## Dependencies & Blockers
   109	
   110	- Blocked by [Task 03](task_03_portable_d3nexus_cli_and_env.md)
   111	
   112	## References & Rollback
   113	
   114	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   115	- Rollback: `git revert` the task commit to restore `check_task_contract.py` and skill documentation.
.devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md
     1	---
     2	id: "task_05_end_to_end_contract_acceptance"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["integration", "acceptance", "tier-c"]
    12	order: "a5"
    13	---
    14	
    15	# Task 05: End-to-End Integration and Acceptance Verification
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Every epic requires a final Tier C integration and acceptance task exercising the full end-to-end workflow across all component seams (`bin/d3nexus`, `sync_task_status.py render`, `check_task_contract.py --design`, `run_task_checks.py`, and `task_contract.py` Done-Gate evaluation) and verifying repository-wide quality gates (`scripts/verify.sh`).
    22	
    23	This task creates `tests/test_task_contract_ergonomics_e2e.py` covering the remaining integration scenarios (`TCAE-ST-02`, `TCAE-AR-02`, `TCAE-FR-03`) and running end-to-end subcutaneous workflows in isolated temporary git repositories.
    24	
    25	## Files
    26	
    27	Allowed files:
    28	- `tests/test_task_contract_ergonomics_e2e.py` (new)
    29	- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
    30	
    31	Read-only context:
    32	- `bin/d3nexus` (created in Task 03) (new)
    33	- `skills/dev-implementation/resources/scripts/task_contract.py` (modified in Task 01 and Task 03)
    34	- `skills/dev-implementation/resources/scripts/check_task_contract.py` (modified in Tasks 01–04)
    35	- `skills/dev-implementation/resources/scripts/sync_task_status.py` (modified in Task 02)
    36	- `skills/dev-implementation/resources/scripts/run_task_checks.py` (modified in Task 03)
    37	
    38	## Design Rationale
    39	
    40	Applicable skills: `python-quality-check`, `test-driven-development`.
    41	Placing the end-to-end subcutaneous suite in `tests/test_task_contract_ergonomics_e2e.py` ensures that `python3 -m pytest tests/` exercises the complete lifecycle from single-source authoring to Done-Gate verification on every PR and Epic quality gate run. In addition, fixing the two `Optional[str]` narrowing lines in `check_bdd_traceability.py` ensures clean `mypy` runs across the entire script suite without requiring workarounds.
    42	
    43	## Impact Analysis & Blast Radius
    44	
    45	- **Target Files & Symbols**:
    46	  - `tests/test_task_contract_ergonomics_e2e.py`: new `test_TCAE_ST_02_done_gate_evidence_transition`, new `test_TCAE_AR_02_idempotent_render`, new `test_TCAE_FR_03_render_unknown_covers_aborts`.
    47	  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `scenario_ids`.
    48	- **Downstream Callers**: Gate 4 `quality_check` and `check_bdd_traceability.py tests --results`.
    49	- **Cross-Platform Bridges**: None.
    50	- **Target Test Coverage Threshold**: 100% BDD scenario traceability across all 14 `[TCAE-*]` scenarios.
    51	
    52	### BDD SCENARIOS
    53	
    54	Covers: TCAE-ST-02, TCAE-AR-02, TCAE-FR-03
    55	
    56	```gherkin
    57	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    58	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    59	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    60	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    61	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    62	  Then "evaluate_done_gate" returns an empty problem list
    63	
    64	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    65	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    66	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    67	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    68	
    69	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
    70	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
    73	```
    74	
    75	## Verification
    76	
    77	| ID | Phase | Command | Expect | Needs |
    78	|----|-------|---------|--------|-------|
    79	| V1 | RED | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py::test_TCAE_ST_02_done_gate_evidence_transition` | exit 1; contains "FAILED" | — |
    80	| V2 | GREEN | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py` | exit 0; contains "passed" | — |
    81	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    82	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    83	| V5 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "OK" | — |
    84	| V6 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |
    85	
    86	## Stop and Report If
    87	
    88	- A command, path, symbol or anchor named in this task does not match the repository.
    89	- A Verification row fails for a reason other than its Expect.
    90	- The work needs a change to a file outside Allowed files, or to a protected path.
    91	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    92	  Covers line.
    93	- A variable named in the Needs column is unset.
    94	
    95	## Decisions Already Made
    96	
    97	- `tests/test_task_contract_ergonomics_e2e.py` exercises the end-to-end flow using temporary git repositories (`tmp_path`), invoking `bin/d3nexus` (`sync-status render`, `check-contract --design`, `run-checks verify`) and asserting all 14 `[TCAE-*]` scenarios pass across the test suite.
    98	- In `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, narrow `fence: str | None` before indexing `fence[0]` and `len(fence)` in `scenario_ids()` so `mypy` passes cleanly without `--follow-imports=silent`.
    99	
   100	## Definition of Done
   101	
   102	- End-to-end integration tests in `tests/test_task_contract_ergonomics_e2e.py` pass for `TCAE-ST-02`, `TCAE-AR-02`, and `TCAE-FR-03`. (V2, V6)
   103	- `ruff`, `mypy`, and `bash scripts/verify.sh` pass with zero errors. (V3, V4, V5)
   104	- Full test suite across `tests/` and `skills/dev-implementation/resources/scripts/` passes with 100% `[TCAE-*]` scenario traceability in `build/test-results/pytest.xml`. (V6)
   105	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   106	
   107	## Dependencies & Blockers
   108	
   109	- Blocked by [Task 04](task_04_verification_grammar_and_docs.md)
   110	
   111	## References & Rollback
   112	
   113	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   114	- Rollback: `git revert` the task commit to remove `tests/test_task_contract_ergonomics_e2e.py`.

exec
/bin/zsh -lc "nl -ba .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md; rg -n '"'^(def |class )|except|subprocess|parse_allowed|created|strip_wrappers|command_paths|Evidence files|is_file|protected'"' skills/dev-implementation/resources/scripts/{task_contract,check_task_contract,check_epic_readiness,run_task_checks,sync_task_status}.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# BDD Test Scenarios: Task Contract and Authoring Ergonomics
     2	
     3	## Table of Contents
     4	
     5	- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
     6	- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
     7	- [Dimension 3: State Transitions](#dimension-3-state-transitions)
     8	- [Dimension 4: Async and Concurrency](#dimension-4-async-and-concurrency)
     9	- [Dimension 5: Failures and Resilience](#dimension-5-failures-and-resilience)
    10	
    11	## Dimension 1: Happy Paths
    12	
    13	```gherkin
    14	Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
    15	  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
    16	  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
    17	  When check_task_contract.py runs with "--design"
    18	  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
    19	  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
    20	  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions
    21	
    22	Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
    23	  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
    24	  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
    25	  When "sync_task_status.py render sample_epic" executes
    26	  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
    27	  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
    28	  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings
    29	
    30	Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
    31	  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    32	  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
    33	  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
    34	  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0
    35	
    36	Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
    37	  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    38	  When "check_task_contract.py --design" evaluates the task
    39	  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
    40	  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
    41	```
    42	
    43	## Dimension 2: Edge Cases and Boundaries
    44	
    45	```gherkin
    46	Scenario: [TCAE-EC-01] [Tier A - Unit] Task without Evidence files or Covers line remains backward-compatible
    47	  Given a legacy task file that omits the "Evidence files:" subsection and omits the "Covers:" line
    48	  When "sync_task_status.py render" and "check_task_contract.py --design" run on the epic
    49	  Then "sync_task_status.py render" generates the ".devtool/features/" mirror without modifying the task's BDD section
    50	  And "check_task_contract.py --design" exits 0 with 0 problems
    51	
    52	Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
    53	  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
    54	  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
    55	  When "sync_task_status.py render sample_epic" executes
    56	  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence
    57	
    58	Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
    59	  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
    60	  When "check_task_contract.py --design" inspects the command tokens
    61	  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
    62	  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
    63	```
    64	
    65	## Dimension 3: State Transitions
    66	
    67	```gherkin
    68	Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
    69	  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
    70	  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then ".devtool/features/task_99_obsolete.md" is removed from disk
    73	  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"
    74	
    75	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    76	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    77	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    78	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    79	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    80	  Then "evaluate_done_gate" returns an empty problem list
    81	```
    82	
    83	## Dimension 4: Async and Concurrency
    84	
    85	```gherkin
    86	Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
    87	  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
    88	  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
    89	  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
    90	
    91	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    92	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    93	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    94	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    95	```
    96	
    97	## Dimension 5: Failures and Resilience
    98	
    99	```gherkin
   100	Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
   101	  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
   102	  When "check_task_contract.py --design" evaluates the task
   103	  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments
   104	
   105	Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
   106	  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
   107	  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
   108	  When "check_task_contract.py --design" evaluates the task
   109	  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2
   110	
   111	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
   112	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
   113	  When "sync_task_status.py render sample_epic" executes
   114	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
   115	```
   116	
skills/dev-implementation/resources/scripts/sync_task_status.py:26:import subprocess
skills/dev-implementation/resources/scripts/sync_task_status.py:32:except ImportError:
skills/dev-implementation/resources/scripts/sync_task_status.py:43:def now_iso() -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:48:def set_frontmatter_field(text: str, key: str, value: str | None) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:75:def parse_worktree_list(output: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:86:def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:112:def checkout_roots() -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:115:    The only subprocess boundary in this module -- everything else is pure and
skills/dev-implementation/resources/scripts/sync_task_status.py:118:    result = subprocess.run(["git", "worktree", "list", "--porcelain"],
skills/dev-implementation/resources/scripts/sync_task_status.py:123:def epic_checkout_roots(epic_dir: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:129:    top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
skills/dev-implementation/resources/scripts/sync_task_status.py:133:    wt_result = subprocess.run(["git", "worktree", "list", "--porcelain"],
skills/dev-implementation/resources/scripts/sync_task_status.py:153:def task_targets(root: Path, task_id: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:160:    return [path for path in candidates if path.is_file()]
skills/dev-implementation/resources/scripts/sync_task_status.py:163:def epic_of(path: Path) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:168:def expected_epic(roots: list[Path], task_id: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:179:            if features.is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:182:            if epic_copy.is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:187:def sync_task(roots: list[Path], task_id: str, new_status: str) -> tuple[list[Path], list[str]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:216:def board_location(root: Path, path: Path, status: str) -> Path:
skills/dev-implementation/resources/scripts/sync_task_status.py:233:def board_tally(roots: list[Path], epic_slug: str) -> dict[str, int]:
skills/dev-implementation/resources/scripts/sync_task_status.py:259:def find_epic_slug(root: Path, epic_dir: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:266:        if doc.is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:279:def find_epic_dir_for_slug(root: Path, epic_slug: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:298:def fix_task_markdown_links(text: str, epic_dir: str) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:305:def fix_epic_overview_links(text: str) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:310:def archive_superpowers_docs(root: Path, epic_dir: str, epic_slug: str | None) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:341:def archive_epic_tasks(roots: list[Path], epic_dir: str) -> tuple[list[Path], list[Path]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:385:            if doc.is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:404:def sync_epic(roots: list[Path], epic_dir: str, new_status: str) -> tuple[list[Path], list[Path]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:418:            if not doc.is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:434:def archive_all_done_epics(roots: list[Path]) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:459:def code_epic_dir(root: Path, task_id: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:464:        if (features / f"{task_id}.md").is_file():
skills/dev-implementation/resources/scripts/sync_task_status.py:473:def done_gate_failures(task_id: str) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:477:    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/sync_task_status.py:488:    if not mirror.is_file() or section(mirror.read_text(encoding="utf-8"), "Verification") is None:
skills/dev-implementation/resources/scripts/sync_task_status.py:493:    except ContractError as error:
skills/dev-implementation/resources/scripts/sync_task_status.py:497:def main() -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:8:implicit protected paths, and a Result line. Exit codes: 0 no problem; 1 problems; 2 usage error.
skills/dev-implementation/resources/scripts/check_task_contract.py:19:import subprocess
skills/dev-implementation/resources/scripts/check_task_contract.py:38:class Checker:
skills/dev-implementation/resources/scripts/check_task_contract.py:43:        listed = subprocess.run(["git", "ls-files", "-z"], check=False, cwd=root, capture_output=True, text=True).stdout
skills/dev-implementation/resources/scripts/check_task_contract.py:47:        return subprocess.run(["git", "check-ignore", "-q", "--", path], check=False, cwd=self.root,
skills/dev-implementation/resources/scripts/check_task_contract.py:60:def read_file(path: Path) -> str:
skills/dev-implementation/resources/scripts/check_task_contract.py:63:    except OSError as error:
skills/dev-implementation/resources/scripts/check_task_contract.py:67:def table_rows(check: Checker, stem: str, text: str) -> list[Any]:
skills/dev-implementation/resources/scripts/check_task_contract.py:86:        except tc.ContractError as error:
skills/dev-implementation/resources/scripts/check_task_contract.py:92:def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[Any]) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:96:    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
skills/dev-implementation/resources/scripts/check_task_contract.py:124:def check_allowed(check: Checker, stem: str, text: str, design: bool) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:125:    for entry in tc.parse_allowed_files(text):
skills/dev-implementation/resources/scripts/check_task_contract.py:143:def command_paths(command: str) -> tuple[list[str], str | None]:
skills/dev-implementation/resources/scripts/check_task_contract.py:149:    except ValueError:
skills/dev-implementation/resources/scripts/check_task_contract.py:157:    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
skills/dev-implementation/resources/scripts/check_task_contract.py:162:def check_grounding(check: Checker, stem: str, text: str, rows: list[Any], created: set[str]) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:164:        if not (check.root / context).exists() and context not in created:
skills/dev-implementation/resources/scripts/check_task_contract.py:167:        paths, executable = command_paths(row.command)
skills/dev-implementation/resources/scripts/check_task_contract.py:169:            if not (check.root / path).exists() and not check.ignored(path) and path not in created:
skills/dev-implementation/resources/scripts/check_task_contract.py:176:def check_pytest_k(check: Checker, stem: str, row: Any) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:179:    except ValueError:
skills/dev-implementation/resources/scripts/check_task_contract.py:181:    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
skills/dev-implementation/resources/scripts/check_task_contract.py:197:def is_python_task(text: str, rows: list[Any]) -> bool:
skills/dev-implementation/resources/scripts/check_task_contract.py:198:    entries = tc.parse_allowed_files(text)
skills/dev-implementation/resources/scripts/check_task_contract.py:207:        except ValueError:
skills/dev-implementation/resources/scripts/check_task_contract.py:214:def check_python_tier_b(check: Checker, stem: str, rows: list[Any]) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:220:        except (json.JSONDecodeError, OSError):
skills/dev-implementation/resources/scripts/check_task_contract.py:242:            except ValueError:
skills/dev-implementation/resources/scripts/check_task_contract.py:264:        except ValueError:
skills/dev-implementation/resources/scripts/check_task_contract.py:266:        prog = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
skills/dev-implementation/resources/scripts/check_task_contract.py:282:def check_weak_bdd(check: Checker, source_name: str, text: str) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:289:def check_task(check: Checker, path: Path, text: str, design: bool, created: set[str]) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:303:        check_grounding(check, stem, text, rows, created)
skills/dev-implementation/resources/scripts/check_task_contract.py:306:def check_hld(check: Checker, hld_path: Path, text: str, tasks: dict[Path, str]) -> None:
skills/dev-implementation/resources/scripts/check_task_contract.py:308:    if not tc.parse_protected_paths(text):
skills/dev-implementation/resources/scripts/check_task_contract.py:326:        except tc.ContractError:
skills/dev-implementation/resources/scripts/check_task_contract.py:336:        except UsageError:
skills/dev-implementation/resources/scripts/check_task_contract.py:340:def repository_root() -> Path:
skills/dev-implementation/resources/scripts/check_task_contract.py:341:    done = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_task_contract.py:347:def main(argv: list[str] | None = None) -> int:
skills/dev-implementation/resources/scripts/check_task_contract.py:357:        created = {entry.pattern for text in tasks.values() for entry in tc.parse_allowed_files(text) if entry.new}
skills/dev-implementation/resources/scripts/check_task_contract.py:359:            check_task(check, path, text, args.design, created)
skills/dev-implementation/resources/scripts/check_task_contract.py:361:    except UsageError as error:
skills/dev-implementation/resources/scripts/check_task_contract.py:370:    print(f"Implicit protected paths: {', '.join(programs) if programs else 'none'}")
skills/dev-implementation/resources/scripts/check_task_contract.py:375:def _rows(text: str) -> list[Any]:
skills/dev-implementation/resources/scripts/check_task_contract.py:379:    except tc.ContractError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:12:import subprocess
skills/dev-implementation/resources/scripts/check_epic_readiness.py:32:class Finding:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:39:class Context:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:51:def parse_integration_test_roots(hld_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:59:def load_context(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:96:def get_last_non_empty_line(*outputs: str) -> str:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:102:def check_preflight(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:109:    res1 = subprocess.run(cmd1, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:136:    res2 = subprocess.run(cmd2, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:151:    res3 = subprocess.run(cmd3, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:166:        res_doc1 = subprocess.run(cmd_doc1, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:172:    if handoff_file.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:179:        res_handoff = subprocess.run(cmd_handoff, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:190:        res_tasks = subprocess.run(cmd_tasks, check=False, cwd=ctx.root, capture_output=True, text=True)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:198:def check_task_mirrors(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:207:        if not mirror_path.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:209:        if not mirror_path.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:245:def extract_scenario_blocks(text: str) -> dict[str, list[str]]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:306:def check_bdd_scenarios(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:310:    if not bdd_en_path.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:324:    if bdd_vi_path.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:338:def check_tier_tags(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:341:    if not bdd_en_path.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:383:def check_grounding(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:409:        allowed_files = tc.parse_allowed_files(task_text)
skills/dev-implementation/resources/scripts/check_epic_readiness.py:431:            if not full_path.is_file() or path_str in new_patterns:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:436:            except OSError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:468:            ls_proc = subprocess.run(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:480:        except OSError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:485:            if f.is_file():
skills/dev-implementation/resources/scripts/check_epic_readiness.py:488:                except OSError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:498:def check_gate4_coverage(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:505:        except ValueError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:512:        except tc.ContractError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:523:            except ValueError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:551:def check_metadata(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:555:    has_handoff = handoff_file.is_file()
skills/dev-implementation/resources/scripts/check_epic_readiness.py:575:                check_ancestor = subprocess.run(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:620:def check_baseline(ctx: Context) -> list[Finding]:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:624:    status_proc = subprocess.run(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:638:        for ap in tc.parse_allowed_files(t_text):
skills/dev-implementation/resources/scripts/check_epic_readiness.py:645:        except tc.ContractError:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:685:def run_checks(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:708:def render_report(ctx: Context, findings: list[Finding]) -> str:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:748:def main(argv: list[str] | None = None) -> int:
skills/dev-implementation/resources/scripts/check_epic_readiness.py:766:        root_str = subprocess.run(
skills/dev-implementation/resources/scripts/check_epic_readiness.py:773:    except (subprocess.CalledProcessError, OSError):
skills/dev-implementation/resources/scripts/check_epic_readiness.py:783:    if not hld_path.is_file():
skills/dev-implementation/resources/scripts/run_task_checks.py:22:import subprocess
skills/dev-implementation/resources/scripts/run_task_checks.py:29:except ImportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:45:parse_allowed_files: Any = _tc.parse_allowed_files
skills/dev-implementation/resources/scripts/run_task_checks.py:46:parse_protected_paths: Any = _tc.parse_protected_paths
skills/dev-implementation/resources/scripts/run_task_checks.py:52:strip_wrappers: Any = _tc.strip_wrappers
skills/dev-implementation/resources/scripts/run_task_checks.py:83:def is_pytest_command(command: str) -> bool:
skills/dev-implementation/resources/scripts/run_task_checks.py:88:    except ValueError:
skills/dev-implementation/resources/scripts/run_task_checks.py:103:        sub = strip_wrappers(sub)
skills/dev-implementation/resources/scripts/run_task_checks.py:119:def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:137:def parse_covers(text: str) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:146:def core_sections(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:155:def check_task_tamper(task_path: Path | str, layout: EpicLayout) -> None:
skills/dev-implementation/resources/scripts/run_task_checks.py:158:    if not features_task.is_file():
skills/dev-implementation/resources/scripts/run_task_checks.py:161:    if not features_task.is_file():
skills/dev-implementation/resources/scripts/run_task_checks.py:184:def utc_now() -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:188:def fresh_reports(path: str, root: Path, since: float) -> list[Path]:
skills/dev-implementation/resources/scripts/run_task_checks.py:192:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:197:def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
skills/dev-implementation/resources/scripts/run_task_checks.py:199:    process = subprocess.Popen(["bash", "-o", "pipefail", "-c", command], cwd=root, start_new_session=True,
skills/dev-implementation/resources/scripts/run_task_checks.py:200:                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
skills/dev-implementation/resources/scripts/run_task_checks.py:204:    except subprocess.TimeoutExpired:
skills/dev-implementation/resources/scripts/run_task_checks.py:210:def mismatch(row: Row, code: int, text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:220:def epic_scenario_ids(layout: EpicLayout) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:223:    except UsageError:
skills/dev-implementation/resources/scripts/run_task_checks.py:227:def attach_digest(results: dict[str, Any], files: list[Path], scenario_ids: list[str]) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:231:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:236:def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:277:def committed_text(root: Path, path: Path) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:283:    except (ContractError, ValueError):
skills/dev-implementation/resources/scripts/run_task_checks.py:284:        return path.read_text(encoding="utf-8") if path.is_file() else None
skills/dev-implementation/resources/scripts/run_task_checks.py:287:def protected_patterns(layout: EpicLayout, root: Path) -> tuple[list[str], set[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:290:    explicit = parse_protected_paths(hld) if hld else []
skills/dev-implementation/resources/scripts/run_task_checks.py:298:        except ContractError:
skills/dev-implementation/resources/scripts/run_task_checks.py:304:def scope_row(layout: EpicLayout, allowed_patterns: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:305:    explicit, programs = protected_patterns(layout, layout.root)
skills/dev-implementation/resources/scripts/run_task_checks.py:310:        protected = path in programs or any(path_matches(pattern, path) for pattern in explicit)
skills/dev-implementation/resources/scripts/run_task_checks.py:311:        if path.startswith(".devtool/") and not protected:
skills/dev-implementation/resources/scripts/run_task_checks.py:314:        if protected:
skills/dev-implementation/resources/scripts/run_task_checks.py:316:                violations.append(f"protected path not named exactly in Allowed files: {path}")
skills/dev-implementation/resources/scripts/run_task_checks.py:323:def detail_of(record: dict[str, Any]) -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:329:def run(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:334:    allowed = parse_allowed_files(task_text)
skills/dev-implementation/resources/scripts/run_task_checks.py:360:def status(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:374:def main(argv: list[str] | None = None) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:381:        if not args.task.is_file():
skills/dev-implementation/resources/scripts/run_task_checks.py:384:    except ContractError as error:
skills/dev-implementation/resources/scripts/task_contract.py:13:import subprocess
skills/dev-implementation/resources/scripts/task_contract.py:40:class ContractError(Exception):
skills/dev-implementation/resources/scripts/task_contract.py:45:class Expect:
skills/dev-implementation/resources/scripts/task_contract.py:53:class Row:
skills/dev-implementation/resources/scripts/task_contract.py:63:class AllowedPath:
skills/dev-implementation/resources/scripts/task_contract.py:69:class EpicLayout:
skills/dev-implementation/resources/scripts/task_contract.py:77:def section(text: str, title: str) -> str | None:
skills/dev-implementation/resources/scripts/task_contract.py:99:def parse_expect(text: str) -> Expect:
skills/dev-implementation/resources/scripts/task_contract.py:121:def split_cells(line: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:128:def parse_row(cells: list[str], seen: set[str]) -> Row:
skills/dev-implementation/resources/scripts/task_contract.py:142:    except ContractError as error:
skills/dev-implementation/resources/scripts/task_contract.py:152:def parse_verification(task_text: str) -> tuple[list[Row], str | None]:
skills/dev-implementation/resources/scripts/task_contract.py:172:def parse_allowed_files(task_text: str) -> list[AllowedPath]:
skills/dev-implementation/resources/scripts/task_contract.py:187:def parse_protected_paths(hld_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:194:def parse_read_only_context(task_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:210:def dod_bullets(task_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:221:def parse_integration_results(hld_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:227:def verification_environment(hld_text: str) -> str | None:
skills/dev-implementation/resources/scripts/task_contract.py:246:def path_matches(pattern: str, path: str) -> bool:
skills/dev-implementation/resources/scripts/task_contract.py:262:def git_run(root: Path, *args: str, env: dict[str, str] | None = None, stdin: bytes | None = None) -> bytes:
skills/dev-implementation/resources/scripts/task_contract.py:263:    done = subprocess.run(["git", *args], cwd=root, env=env, input=stdin, capture_output=True)
skills/dev-implementation/resources/scripts/task_contract.py:269:def strip_wrappers(tokens: list[str]) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:284:def program_of(command: str, root: Path) -> str | None:
skills/dev-implementation/resources/scripts/task_contract.py:290:    except ValueError:
skills/dev-implementation/resources/scripts/task_contract.py:296:    tokens = strip_wrappers(tokens)
skills/dev-implementation/resources/scripts/task_contract.py:313:    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", candidate], cwd=root,
skills/dev-implementation/resources/scripts/task_contract.py:318:def epic_layout(task_file: Path) -> EpicLayout:
skills/dev-implementation/resources/scripts/task_contract.py:322:    except (ContractError, OSError):
skills/dev-implementation/resources/scripts/task_contract.py:333:def fingerprint(root: Path) -> tuple[str, str | None]:
skills/dev-implementation/resources/scripts/task_contract.py:346:def changed_paths(root: Path) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:361:def load_evidence(path: Path) -> dict | None:
skills/dev-implementation/resources/scripts/task_contract.py:364:    except FileNotFoundError:
skills/dev-implementation/resources/scripts/task_contract.py:368:def save_evidence(path: Path, data: dict) -> None:
skills/dev-implementation/resources/scripts/task_contract.py:374:def is_code_epic(hld_path: Path) -> bool:
skills/dev-implementation/resources/scripts/task_contract.py:378:    except OSError:
skills/dev-implementation/resources/scripts/task_contract.py:383:def row_problems(rows: list[Row], runs: dict) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:400:def evaluate_done_gate(task_file: Path) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:405:    except ContractError as error:

exec
/bin/zsh -lc 'cat skills/dev-implementation/resources/scripts/check_task_contract.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/task_contract.py | sed -n '77,210p;260,346p;383,470p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc 'nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md; nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc "nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_02_single_source_render_engine.md | sed -n '104,126p'; nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
#!/usr/bin/env python3
"""Check the task files and HLD a designer wrote against the task contract, before Gate 2 closes.

Usage:
  check_task_contract.py [--design] --hld <epic_dir>.en.md --tasks <task_*.md ...>

Prints problems as `<task stem>:<row or section>: <problem>` or `<hld file name>: <problem>`, the
implicit protected paths, and a Result line. Exit codes: 0 no problem; 1 problems; 2 usage error.
Python 3 standard library only.
"""
from __future__ import annotations

import argparse
import importlib
import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
tc: Any = importlib.import_module("task_contract")
cb: Any = importlib.import_module("check_bdd_traceability")
UsageError: type[Exception] = cb.UsageError
covers_of: Any = cb.covers_of
read_text: Any = cb.read_text

SECTIONS = ("Files", "Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made")
ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.MULTILINE)
GLOB_CHARS = re.compile(r"[*?]")
WEAK_ASSERTION_RE = re.compile(r"\b(should be truthy|is valid|should work|returns non-empty)\b", re.IGNORECASE)


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.problems: list[str] = []
        self.warnings: list[str] = []
        listed = subprocess.run(["git", "ls-files", "-z"], check=False, cwd=root, capture_output=True, text=True).stdout
        self.tracked = set(listed.split("\0")) - {""}

    def ignored(self, path: str) -> bool:
        return subprocess.run(["git", "check-ignore", "-q", "--", path], check=False, cwd=self.root,
                              capture_output=True).returncode == 0

    def problem(self, where: str, text: str) -> None:
        self.problems.append(f"{where}: {text}")

    def is_tracked(self, path: str) -> bool:
        return path in self.tracked

    def matches_tracked(self, pattern: str) -> bool:
        return any(tc.path_matches(pattern, name) for name in self.tracked)


def read_file(path: Path) -> str:
    try:
        return str(read_text(path))
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error.strerror or error}") from None


def table_rows(check: Checker, stem: str, text: str) -> list[Any]:
    """Parse the Verification table row by row, reporting every bad row rather than the first."""
    body = tc.section(text, "Verification")
    if body is None:
        return []
    table = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    if not table or tc.split_cells(table[0]) != tc.HEADER:
        check.problem(f"{stem}:Verification", "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |")
        return []
    rows: list[Any] = []
    seen: set[str] = set()
    for line in table[2:]:
        cells = tc.split_cells(line)
        try:
            if len(cells) != len(tc.HEADER):
                raise tc.ContractError(f"Verification row {cells[0]!r}: expected {len(tc.HEADER)} cells, found {len(cells)}")
            rows.append(tc.parse_row(cells, seen))
            if rows[-1].phase != "TIER-C" and rows[-1].expect.results:
                check.problem(f"{stem}:{cells[0]}", "results is allowed only on TIER-C rows")
        except tc.ContractError as error:
            check.problem(f"{stem}:{cells[0]}", ROW_PREFIX.sub("", str(error)))
        seen.add(cells[0])
    return rows


def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[Any]) -> None:
    for title in SECTIONS:
        if tc.section(text, title) is None:
            check.problem(f"{stem}:{title}", "section is missing")
    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
        check.problem(f"{stem}:Files", "Allowed files lists no entry")
    v_sec = tc.section(text, "Verification")
    if v_sec is not None:
        reason = next((m.group(1) for m in map(tc.RED_NA.match, v_sec.splitlines()) if m), None)
        if not any(row.phase == "RED" for row in rows) and not (reason and reason.strip()):
            check.problem(f"{stem}:Verification", "no RED row and no RED: n/a line with a reason")
        if covers_of(path) and not any(row.phase == "TIER-C" and row.expect.results for row in rows):
            check.problem(f"{stem}:Verification", "Covers line but no TIER-C row with results")
    ids = {row.id for row in rows}
    for bullet in tc.dod_bullets(text):
        reference = tc.DOD_REFERENCE.search(bullet)
        if not reference:
            check.problem(f"{stem}:Definition of Done", f"{bullet} ends with no (V<n>) or (Gate 5) reference")
            continue
        missing = [name for name in re.findall(r"V[0-9]+", reference.group(1)) if name not in ids]
        if missing:
            check.problem(f"{stem}:Definition of Done",
                          f"{bullet} references {', '.join(missing)}, which the table lacks")
    has_executable = any(row.phase in ("RED", "GREEN") for row in rows)
    if has_executable:
        decisions = tc.section(text, "Decisions Already Made")
        clean_decisions = decisions.strip().lower() if decisions else ""
        if not decisions or not clean_decisions or clean_decisions in ("none", "none.", "n/a"):
            check.problem(f"{stem}:Decisions Already Made",
                          "executable task requires grounded facts, cannot be empty or 'None'")


def check_allowed(check: Checker, stem: str, text: str, design: bool) -> None:
    for entry in tc.parse_allowed_files(text):
        pattern = entry.pattern
        if entry.new:
            if design:
                parent = (check.root / pattern).parent
                if (check.root / pattern).exists():
                    check.problem(f"{stem}:Files", f"{pattern} is marked (new) but already exists")
                elif not (parent.exists() or parent.parent.exists()):
                    check.problem(f"{stem}:Files", f"{pattern} (new) has no parent or grandparent directory")
        elif pattern.endswith("/") or (not GLOB_CHARS.search(pattern) and (check.root / pattern).is_dir()):
            check.problem(f"{stem}:Files", f"{pattern} is a directory; list files or a glob")
        elif GLOB_CHARS.search(pattern):
            if not check.matches_tracked(pattern):
                check.problem(f"{stem}:Files", f"{pattern} matches no tracked file")
        elif not check.is_tracked(pattern):
            check.problem(f"{stem}:Files", f"{pattern} is not tracked by git")


def command_paths(command: str) -> tuple[list[str], str | None]:
    """Path-like tokens of a command, and its executable when that is a bare name."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return [], None
    paths: list[str] = []
    for token in tokens:
        value = token.split("=", 1)[1] if token.startswith("-") and "=" in token else token
        if "/" in value and not value.startswith("-") and not re.search(r"[*$]|://", value):
            clean_path = value.split("::", 1)[0]
            paths.append(clean_path.removeprefix("./"))
    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    first = program[0] if program else None
    return paths, first if first and "/" not in first else None


def check_grounding(check: Checker, stem: str, text: str, rows: list[Any], created: set[str]) -> None:
    for context in tc.parse_read_only_context(text):
        if not (check.root / context).exists() and context not in created:
            check.problem(f"{stem}:Files", f"Read-only context {context} does not exist and is not (new) in any task")
    for row in rows:
        paths, executable = command_paths(row.command)
        for path in paths:
            if not (check.root / path).exists() and not check.ignored(path) and path not in created:
                check.problem(f"{stem}:{row.id}",
                              f"{path} does not exist, is not ignored by git and is not (new) in any task")
        if executable and shutil.which(executable) is None:
            check.warnings.append(f"warning: {stem}:{row.id}: executable {executable} not found on PATH")


def check_pytest_k(check: Checker, stem: str, row: Any) -> None:
    try:
        tokens = shlex.split(row.command)
    except ValueError:
        tokens = row.command.split()
    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
    if not program or "pytest" not in program[0]:
        return
    for i, token in enumerate(tokens):
        val: str | None = None
        if token == "-k" and i + 1 < len(tokens):
            val = tokens[i + 1]
        elif token.startswith("-k="):
            val = token.split("=", 1)[1]
        elif token.startswith("-k") and len(token) > 2:
            val = token[2:]
        if val is not None and ("::" not in val or not val.split("::", 1)[0].endswith(".py")):
            check.problem(f"{stem}:{row.id}",
                          f"pytest -k expression must use an exact node ID (<file>::<test>), found: {val!r}")


def is_python_task(text: str, rows: list[Any]) -> bool:
    entries = tc.parse_allowed_files(text)
    for entry in entries:
        pat = entry.pattern.lower()
        if pat.endswith(".py") or pat in ("pyproject.toml", "setup.py", "requirements.txt", "pipfile"):
            return True
    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
    for row in tier_b_rows:
        try:
            tokens = shlex.split(row.command)
        except ValueError:
            tokens = row.command.split()
        if "ruff" in tokens or any("ruff" in t for t in tokens):
            return True
    return False


def check_python_tier_b(check: Checker, stem: str, rows: list[Any]) -> None:
    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
    manifest_path = check.root / ".agents" / "quality" / "python-quality.json"
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            check.problem(f"{stem}:Verification", "malformed .agents/quality/python-quality.json manifest")
            return
        if not isinstance(data, dict):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: root must be an object")
            return
        capabilities = data.get("capabilities")
        if not isinstance(capabilities, dict):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: capabilities must be an object")
            return
        lint_cmd = capabilities.get("lint")
        type_check_cmd = capabilities.get("type_check")
        if not isinstance(lint_cmd, list) or not lint_cmd or not all(isinstance(x, str) for x in lint_cmd):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: lint capability missing or invalid")
            return
        if not isinstance(type_check_cmd, list) or not type_check_cmd or not all(isinstance(x, str) for x in type_check_cmd):
            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: type_check capability missing or invalid")
            return

        def matches_cap(cap: list[str], command: str) -> bool:
            try:
                row_toks = shlex.split(command)
            except ValueError:
                row_toks = command.split()
            if row_toks == cap:
                return True
            if len(cap) > 1 and row_toks[:len(cap) - 1] == cap[:-1]:
                return True
            return bool(len(row_toks) >= len(cap) and row_toks[:len(cap)] == cap)

        has_lint = any(matches_cap(lint_cmd, r.command) for r in tier_b_rows)
        has_type = any(matches_cap(type_check_cmd, r.command) for r in tier_b_rows)
        if not has_lint:
            check.problem(f"{stem}:Verification", f"Python task missing registered lint capability ({' '.join(lint_cmd)})")
        if not has_type:
            check.problem(f"{stem}:Verification", f"Python task missing registered type_check capability ({' '.join(type_check_cmd)})")
        return

    # Fallback tooling: ruff + (mypy / pyright / ty)
    has_ruff = False
    has_type_checker = False
    for r in tier_b_rows:
        try:
            tokens = shlex.split(r.command)
        except ValueError:
            tokens = r.command.split()
        prog = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
        first = prog[0] if prog else ""
        if first == "ruff" or "ruff" in tokens:
            has_ruff = True
        if first in ("mypy", "pyright", "ty") or any(t in ("mypy", "pyright", "ty") for t in tokens):
            has_type_checker = True

    if not has_ruff or not has_type_checker:
        missing_tools: list[str] = []
        if not has_ruff:
            missing_tools.append("lint (ruff)")
        if not has_type_checker:
            missing_tools.append("type-check (mypy/pyright/ty)")
        check.problem(f"{stem}:Verification", f"Python task requires TIER-B direct {', '.join(missing_tools)}")


def check_weak_bdd(check: Checker, source_name: str, text: str) -> None:
    for line_num, line in enumerate(text.splitlines(), start=1):
        m = WEAK_ASSERTION_RE.search(line)
        if m:
            check.problem(f"{source_name}:{line_num}", f"weak BDD assertion found: {m.group(0)!r}")


def check_task(check: Checker, path: Path, text: str, design: bool, created: set[str]) -> None:
    stem = path.stem
    rows = table_rows(check, stem, text)
    check_structure(check, stem, path, text, rows)
    for row in rows:
        if row.expect.results and not check.ignored(row.expect.results):
            check.problem(f"{stem}:{row.id}", f"results path {row.expect.results} is not ignored by git")
        check_pytest_k(check, stem, row)
    check_weak_bdd(check, stem, text)
    status = STATUS.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
    if design or not (status and status.group(1) == "done"):
        if is_python_task(text, rows):
            check_python_tier_b(check, stem, rows)
        check_allowed(check, stem, text, design)
        check_grounding(check, stem, text, rows, created)


def check_hld(check: Checker, hld_path: Path, text: str, tasks: dict[Path, str]) -> None:
    name = hld_path.name
    if not tc.parse_protected_paths(text):
        check.problem(name, "no Protected paths: line")
    results = tc.parse_integration_results(text)
    if not results:
        check.problem(name, "no Integration results: line")
    for entry in results:
        command, arrow, report = entry.rpartition(" -> ")
        if not arrow or not command.strip() or not report.strip():
            check.problem(name, f"Integration results line is not <command> -> <path>: {entry}")
        elif not check.ignored(report.strip()):
            check.problem(name, f"Integration results path {report.strip()} is not ignored by git")
    environment = tc.verification_environment(text)
    if environment is None or not environment.strip():
        check.problem(name, "## Verification Environment section is missing or empty")
        return
    for path, task_text in tasks.items():
        try:
            rows, _ = tc.parse_verification(task_text)
        except tc.ContractError:
            continue
        for row in rows:
            for need in row.needs:
                if need not in environment:
                    check.problem(f"{path.stem}:{row.id}", f"Needs {need} is not named in the Verification Environment section")
    for bdd_path in sorted(hld_path.parent.glob("bdd_scenarios*.md")):
        try:
            content = read_file(bdd_path)
            check_weak_bdd(check, bdd_path.name, content)
        except UsageError:
            pass


def repository_root() -> Path:
    done = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
    if done.returncode != 0:
        raise UsageError("not inside a git repository")
    return Path(done.stdout.strip())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--design", action="store_true")
    parser.add_argument("--hld", required=True, type=Path)
    parser.add_argument("--tasks", required=True, nargs="+", type=Path)
    args = parser.parse_args(argv)
    try:
        check = Checker(repository_root())
        hld_text = read_file(args.hld)
        tasks = {path: read_file(path) for path in args.tasks}
        created = {entry.pattern for text in tasks.values() for entry in tc.parse_allowed_files(text) if entry.new}
        for path, text in tasks.items():
            check_task(check, path, text, args.design, created)
        check_hld(check, args.hld, hld_text, tasks)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    programs = sorted({program for text in tasks.values() for row in _rows(text)
                       if (program := tc.program_of(row.command, check.root))})
    for warning in check.warnings:
        print(warning, file=sys.stderr)
    for problem in check.problems:
        print(problem)
    print(f"Implicit protected paths: {', '.join(programs) if programs else 'none'}")
    print(f"Result: {len(check.problems)} problems — {'FAIL' if check.problems else 'PASS'}")
    return 1 if check.problems else 0


def _rows(text: str) -> list[Any]:
    try:
        parsed: tuple[list[Any], Any] = tc.parse_verification(text)
        return list(parsed[0])
    except tc.ContractError:
        return []


if __name__ == "__main__":
    sys.exit(main())

 succeeded in 0ms:
    77	def section(text: str, title: str) -> str | None:
    78	    """Body under `## <title>` up to the next `## ` heading; fenced lines never count as headings."""
    79	    body: list[str] = []
    80	    found = False
    81	    fence: str | None = None
    82	    for line in text.splitlines():
    83	        marker = FENCE.match(line)
    84	        if marker:
    85	            if fence is None:
    86	                fence = marker.group(1)
    87	            elif marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
    88	                fence = None
    89	        elif fence is None and line.startswith("## "):
    90	            if found:
    91	                break
    92	            found = line[3:].strip() == title
    93	            continue
    94	        if found:
    95	            body.append(line)
    96	    return "\n".join(body) if found else None
    97	
    98	
    99	def parse_expect(text: str) -> Expect:
   100	    head = EXIT_CLAUSE.match(text)
   101	    if not head:
   102	        raise ContractError(f'Expect must start with "exit <n>" or "exit non-zero": {text!r}')
   103	    position = head.end()
   104	    contains: list[str] = []
   105	    results: str | None = None
   106	    while position < len(text):
   107	        clause = CLAUSE.match(text, position)
   108	        if not clause:
   109	            raise ContractError(f"Expect has an unknown clause: {text!r}")
   110	        if clause.group(1) is not None:
   111	            contains.append(clause.group(1))
   112	        elif results is not None:
   113	            raise ContractError(f"Expect has more than one results clause: {text!r}")
   114	        else:
   115	            results = clause.group(2)
   116	        position = clause.end()
   117	    exit_code = int(head.group(1)) if head.group(1) is not None else None
   118	    return Expect(exit_code, exit_code is None, tuple(contains), results)
   119	
   120	
   121	def split_cells(line: str) -> list[str]:
   122	    inner = line.strip()
   123	    inner = inner[1:] if inner.startswith("|") else inner
   124	    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
   125	    return [cell.strip() for cell in re.split(r"(?<!\\)\|", inner)]
   126	
   127	
   128	def parse_row(cells: list[str], seen: set[str]) -> Row:
   129	    row_id = cells[0]
   130	    if not ROW_ID.fullmatch(row_id):
   131	        raise ContractError(f"Verification row {row_id!r}: ID must look like V1")
   132	    if row_id in seen:
   133	        raise ContractError(f"Verification row {row_id}: duplicate ID")
   134	    phase, command_cell, expect_text, needs_cell = cells[1:]
   135	    if phase not in PHASES:
   136	        raise ContractError(f"Verification row {row_id}: Phase must be one of {', '.join(PHASES)}")
   137	    span = CODE_SPAN.fullmatch(command_cell)
   138	    if not span:
   139	        raise ContractError(f"Verification row {row_id}: Command must be exactly one inline code span")
   140	    try:
   141	        expect = parse_expect(expect_text)
   142	    except ContractError as error:
   143	        raise ContractError(f"Verification row {row_id}: {error}") from None
   144	    needs: tuple[str, ...] = ()
   145	    if needs_cell not in NONE_CELL:
   146	        needs = tuple(name.strip() for name in needs_cell.split(","))
   147	        if not all(NEEDS_NAME.fullmatch(name) for name in needs):
   148	            raise ContractError(f"Verification row {row_id}: Needs must be — or names like TEST_DATABASE_URL")
   149	    return Row(row_id, phase, span.group(1).replace("\\|", "|"), expect_text, expect, needs)
   150	
   151	
   152	def parse_verification(task_text: str) -> tuple[list[Row], str | None]:
   153	    body = section(task_text, "Verification")
   154	    if body is None:
   155	        raise ContractError("task has no ## Verification section")
   156	    lines = body.splitlines()
   157	    table = [line for line in lines if line.lstrip().startswith("|")]
   158	    if not table or split_cells(table[0]) != HEADER:
   159	        raise ContractError("Verification header must be exactly: " + "| " + " | ".join(HEADER) + " |")
   160	    rows: list[Row] = []
   161	    seen: set[str] = set()
   162	    for line in table[2:]:
   163	        cells = split_cells(line)
   164	        if len(cells) != len(HEADER):
   165	            raise ContractError(f"Verification row {cells[0]!r}: expected {len(HEADER)} cells, found {len(cells)}")
   166	        rows.append(parse_row(cells, seen))
   167	        seen.add(rows[-1].id)
   168	    reason = next((m.group(1) for m in map(RED_NA.match, lines) if m), None)
   169	    return rows, reason
   170	
   171	
   172	def parse_allowed_files(task_text: str) -> list[AllowedPath]:
   173	    body = section(task_text, "Files") or ""
   174	    allowed: list[AllowedPath] = []
   175	    listing = False
   176	    for line in body.splitlines():
   177	        if not listing:
   178	            listing = line.strip() == "Allowed files:"
   179	            continue
   180	        bullet = ALLOWED_BULLET.match(line)
   181	        if not bullet:
   182	            break
   183	        allowed.append(AllowedPath(bullet.group(1), bool(bullet.group(2))))
   184	    return allowed
   185	
   186	
   187	def parse_protected_paths(hld_text: str) -> list[str]:
   188	    for line in hld_text.splitlines():
   189	        if line.startswith("Protected paths:"):
   190	            return [entry.strip() for entry in line.split(":", 1)[1].split(",") if entry.strip()]
   191	    return []
   192	
   193	
   194	def parse_read_only_context(task_text: str) -> list[str]:
   195	    """The first inline code span of each bullet under `Read-only context:` in `## Files`."""
   196	    paths: list[str] = []
   197	    listing = False
   198	    for line in (section(task_text, "Files") or "").splitlines():
   199	        if not listing:
   200	            listing = line.strip() == "Read-only context:"
   201	        elif line.startswith("- "):
   202	            span = CODE_SPAN.search(line)
   203	            if span:
   204	                paths.append(span.group(1))
   205	        elif line.strip():
   206	            break
   207	    return paths
   208	
   209	
   210	def dod_bullets(task_text: str) -> list[str]:
   260	
   261	
   262	def git_run(root: Path, *args: str, env: dict[str, str] | None = None, stdin: bytes | None = None) -> bytes:
   263	    done = subprocess.run(["git", *args], cwd=root, env=env, input=stdin, capture_output=True)
   264	    if done.returncode != 0:
   265	        raise ContractError(f"git {' '.join(args)} failed: {done.stderr.decode(errors='replace').strip()}")
   266	    return done.stdout
   267	
   268	
   269	def strip_wrappers(tokens: list[str]) -> list[str]:
   270	    while tokens:
   271	        if tokens[:2] in (["uv", "run"], ["poetry", "run"]):
   272	            tokens = tokens[2:]
   273	        elif tokens[0] in ("npx", "fvm"):
   274	            tokens = tokens[1:]
   275	        elif tokens[0] == "env":
   276	            tokens = tokens[1:]
   277	            while tokens and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", tokens[0]):
   278	                tokens = tokens[1:]
   279	        else:
   280	            break
   281	    return tokens
   282	
   283	
   284	def program_of(command: str, root: Path) -> str | None:
   285	    """The tracked file a command runs, or None when it runs something else."""
   286	    try:
   287	        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
   288	        lexer.whitespace_split = True
   289	        tokens = list(lexer)
   290	    except ValueError:
   291	        return None
   292	    for index, token in enumerate(tokens):
   293	        if token in CONTROL_TOKENS:
   294	            tokens = tokens[:index]
   295	            break
   296	    tokens = strip_wrappers(tokens)
   297	    if not tokens:
   298	        return None
   299	    candidate: str | None
   300	    if tokens[0] in INTERPRETERS:
   301	        candidate = None
   302	        for argument in tokens[1:]:
   303	            if argument in ("-m", "-c"):
   304	                break
   305	            if not argument.startswith("-"):
   306	                candidate = argument
   307	                break
   308	    else:
   309	        candidate = tokens[0]
   310	    if not candidate:
   311	        return None
   312	    candidate = candidate[2:] if candidate.startswith("./") else candidate
   313	    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", candidate], cwd=root,
   314	                             capture_output=True).returncode == 0
   315	    return candidate if tracked else None
   316	
   317	
   318	def epic_layout(task_file: Path) -> EpicLayout:
   319	    path = Path(task_file).resolve()
   320	    try:
   321	        top = git_run(path.parent, "rev-parse", "--show-toplevel").decode().strip()
   322	    except (ContractError, OSError):
   323	        raise ContractError(f"{task_file} is not inside a git repository") from None
   324	    root = Path(top).resolve()
   325	    parts = path.relative_to(root).parts if path.is_relative_to(root) else ()
   326	    if not (len(parts) == 4 and parts[:2] == (".devtool", "epic") and re.fullmatch(r"task_.*\.md", parts[3])):
   327	        raise ContractError("pass the task's mirror under .devtool/epic/<epic_dir>/")
   328	    epic_dir = path.parent
   329	    return EpicLayout(root, epic_dir, epic_dir / f"{epic_dir.name}.en.md",
   330	                      epic_dir / "bdd_scenarios.en.md", epic_dir / "evidence" / f"{path.stem}.json")
   331	
   332	
   333	def fingerprint(root: Path) -> tuple[str, str | None]:
   334	    """Tree id of the worktree without .devtool/, and its stable patch id against HEAD outside .devtool/."""
   335	    with tempfile.TemporaryDirectory() as scratch:
   336	        env = {**os.environ, "GIT_INDEX_FILE": str(Path(scratch) / "index")}
   337	        git_run(root, "read-tree", "HEAD", env=env)
   338	        git_run(root, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", ".devtool", env=env)
   339	        git_run(root, "add", "-A", "--", ".", EXCLUDE_DEVTOOL, env=env)
   340	        tree = git_run(root, "write-tree", env=env).decode().strip()
   341	        diff = git_run(root, "diff", *DIFF_PLAIN, "--cached", "HEAD", "--", ".", EXCLUDE_DEVTOOL, env=env)
   342	        patch = git_run(root, "patch-id", "--stable", stdin=diff).decode().split() if diff else []
   343	    return tree, patch[0] if patch else None
   344	
   345	
   346	def changed_paths(root: Path) -> list[str]:
   383	def row_problems(rows: list[Row], runs: dict) -> list[str]:
   384	    """Condition 2: each table row needs a PASS record carrying the same command and expect."""
   385	    problems: list[str] = []
   386	    for row in rows:
   387	        run = runs.get("red" if row.phase == "RED" else "verify") or {}
   388	        record = next((r for r in run.get("rows", []) if r["id"] == row.id), None)
   389	        if record is None or (record["outcome"] != "PASS" and record["outcome"] != "BLOCKED"):
   390	            problems.append(f"condition 2: row {row.id}: no PASS result in the evidence")
   391	        elif record["outcome"] == "BLOCKED":
   392	            continue
   393	        elif record["command"] != row.command:
   394	            problems.append(f"condition 2: row {row.id}: recorded command differs from the table")
   395	        elif record["expect"] != row.expect_text:
   396	            problems.append(f"condition 2: row {row.id}: recorded expect differs from the table")
   397	    return problems
   398	
   399	
   400	def evaluate_done_gate(task_file: Path) -> list[str]:
   401	    """One message per failed done-gate condition for a task mirror; empty when the gate passes."""
   402	    layout = epic_layout(task_file)
   403	    try:
   404	        rows, red_na = parse_verification(Path(task_file).read_text(encoding="utf-8"))
   405	    except ContractError as error:
   406	        return [f"condition 2: {error}"]
   407	    evidence = load_evidence(layout.evidence)
   408	    if evidence is None:
   409	        return [f"condition 1: evidence {layout.evidence} not found in this checkout — record it with "
   410	                "run_task_checks.py and run the done gate in the epic worktree"]
   411	    runs = evidence.get("runs", {})
   412	    needs_red = red_na is None and any(row.phase == "RED" for row in rows)
   413	    missing = [kind for kind in (("red",) if needs_red else ()) + ("verify",) if kind not in runs]
   414	    if missing:
   415	        return [f"condition 1: evidence {layout.evidence} has no {kind} run" for kind in missing]
   416	    problems = row_problems(rows, runs)
   417	    ids = {row.id for row in rows} | {"SCOPE"}
   418	    problems += [f"condition 2: {kind} row {r['id']} is {r['outcome']} and no longer in the table"
   419	                 for kind, run in runs.items() for r in run["rows"]
   420	                 if r["id"] not in ids and r["outcome"] not in ("PASS", "BLOCKED")]
   421	    for kind, run in runs.items():
   422	        problems += [f"condition 3: {kind} row {r['id']} is BLOCKED ({r.get('reason')})"
   423	                     for r in run["rows"] if r["outcome"] == "BLOCKED"]
   424	    verify = runs["verify"]
   425	    if verify["tree"] != fingerprint(layout.root)[0]:
   426	        problems.append("condition 4: the verify run's tree differs from the current tree — "
   427	                        "files changed after verification")
   428	    if verify.get("patch_id") is None:
   429	        problems.append("condition 4: verify saw no change outside .devtool — record verify before committing")
   430	    if needs_red:
   431	        red = runs["red"]
   432	        if red.get("head") != verify.get("head"):
   433	            problems.append("condition 5: red and verify were recorded on different commits")
   434	        if red["tree"] == verify["tree"]:
   435	            problems.append("condition 5: the red run's tree equals the verify run's tree — "
   436	                            "RED was not recorded before the change")
   437	        if red["finished"] > verify["started"]:
   438	            problems.append("condition 5: the red run finished after the verify run started")
   439	    cases = [Case(c["name"], c["classname"], c["status"]) for r in verify["rows"] if r["phase"] == "TIER-C"
   440	             for c in r.get("results", {}).get("digest", {}).get("cases", [])]
   441	    problems += [f"condition 6: {identifier}: {detail}"
   442	                 for identifier, (passed, detail) in verdicts(covers_of(Path(task_file)), cases).items()
   443	                 if not passed]
   444	    scope = next((r for r in verify["rows"] if r["id"] == "SCOPE"), None)
   445	    if scope is None or scope["outcome"] != "PASS":
   446	        detail = "; ".join(scope.get("violations", [])) if scope else "no SCOPE row"
   447	        problems.append(f"condition 7: SCOPE row is not PASS ({detail})")
   448	    return problems

 succeeded in 0ms:
     1	---
     2	id: "task_04_verification_grammar_and_docs"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "grammar", "documentation"]
    12	order: "a4"
    13	---
    14	
    15	# Task 04: Verification Row Grammar Diagnostics and Reference Documentation
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observation #0019: authors and reviewers repeatedly encounter undocumented grammar rules in Verification tables:
    22	1. `task_contract.py` unescapes `\|` to `|` in table cells, which caused a Principal Review round to falsely flag valid rows as broken.
    23	2. Inline `VAR=value cmd` without `env` is parsed as an executable named `VAR=value`.
    24	3. Search patterns in `grep`, `rg`, `sed`, and `awk` containing `/` (such as `grep -E 'foo/bar' file.txt`) are misclassified by `command_paths()` as missing file paths.
    25	4. Tracked scripts executed by a row become implicit protected paths without reporting which task/row triggered them.
    26	
    27	This task improves `check_task_contract.py` diagnostics, creates the canonical `skills/dev-designer/references/verification-row-grammar.md` reference, and updates `skills/dev-designer/SKILL.md` and `skills/principal-review/SKILL.md`.
    28	
    29	## Files
    30	
    31	Allowed files:
    32	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    33	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    34	- `skills/dev-designer/references/verification-row-grammar.md` (new)
    35	- `skills/dev-designer/SKILL.md`
    36	- `skills/principal-review/SKILL.md`
    37	
    38	Read-only context:
    39	- `skills/dev-designer/references/verification-rows.md` (existing per-platform example rows)
    40	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    41	
    42	## Design Rationale
    43	
    44	Applicable skills: `python-quality-check`, `doc_quality_check`, `test-driven-development`.
    45	Centralizing all Verification table grammar rules in `skills/dev-designer/references/verification-row-grammar.md` and aligning `check_task_contract.py` diagnostics with `principal-review` eliminates false positives in both automated checks and AI reviews.
    46	
    47	## Impact Analysis & Blast Radius
    48	
    49	- **Target Files & Symbols**:
    50	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, `main`.
    51	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    52	- **Cross-Platform Bridges**: None.
    53	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `command_paths` and grammar diagnostics in `check_task_contract.py`.
    54	
    55	### BDD SCENARIOS
    56	
    57	Covers: TCAE-HP-04, TCAE-EC-03
    58	
    59	```gherkin
    60	Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
    61	  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    62	  When "check_task_contract.py --design" evaluates the task
    63	  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
    64	  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
    65	
    66	Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
    67	  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
    68	  When "check_task_contract.py --design" inspects the command tokens
    69	  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
    70	  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
    71	```
    72	
    73	## Verification
    74	
    75	| ID | Phase | Command | Expect | Needs |
    76	|----|-------|---------|--------|-------|
    77	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py::test_TCAE_EC_03_grep_slash_pattern_excluded` | exit 1; contains "FAILED" | — |
    78	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
    79	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0 | — |
    80	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/check_task_contract.py` | exit 0 | — |
    81	| V5 | TIER-B | `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-designer/references/verification-row-grammar.md` | exit 0; contains "0 findings" | — |
    82	| V6 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |
    83	
    84	## Stop and Report If
    85	
    86	- A command, path, symbol or anchor named in this task does not match the repository.
    87	- A Verification row fails for a reason other than its Expect.
    88	- The work needs a change to a file outside Allowed files, or to a protected path.
    89	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    90	  Covers line.
    91	- A variable named in the Needs column is unset.
    92	
    93	## Decisions Already Made
    94	
    95	- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `command_paths(command: str)` splits subcommands on `tc.CONTROL_TOKENS` (`&&`, `||`, `;`, `|`). For any subcommand whose unwrapped program is `grep`, `egrep`, `fgrep`, `rg`, `sed`, or `awk`, the pattern argument (the token after `-e`/`--regexp` or the first non-flag positional argument when no `-e`/`-f` flag is present) is skipped before collecting path tokens.
    96	- When the first token of a subcommand (before `env`) matches `^[A-Za-z_][A-Za-z0-9_]*=.*`, `check_grounding` records a problem: `"inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')"`.
    97	- `Implicit protected paths:` in `check_task_contract.py` formats each entry as `<path> (<task_stem>:<row_id>, ...)`.
    98	- `skills/dev-designer/references/verification-row-grammar.md` includes a `## Table of Contents` and documents all 6 rules (`\|` unescaping, `env VAR=val`, grep pattern rules, `Evidence files:`, `d3nexus` / `$D3NEXUS_KIT`, and 4-backtick outer code fences).
    99	
   100	## Definition of Done
   101	
   102	- `command_paths()` excludes `grep`/`rg`/`sed`/`awk` pattern arguments from missing-path errors and reports bare `VAR=val` assignments and implicit protected path provenance. (V2)
   103	- `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-designer/SKILL.md`, and `skills/principal-review/SKILL.md` are updated and pass document linting. (V5)
   104	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   105	- Automated tests for `TCAE-HP-04` and `TCAE-EC-03` pass and write JUnit XML results. (V6)
   106	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   107	
   108	## Dependencies & Blockers
   109	
   110	- Blocked by [Task 03](task_03_portable_d3nexus_cli_and_env.md)
   111	
   112	## References & Rollback
   113	
   114	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   115	- Rollback: `git revert` the task commit to restore `check_task_contract.py` and skill documentation.
     1	---
     2	id: "task_05_end_to_end_contract_acceptance"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["integration", "acceptance", "tier-c"]
    12	order: "a5"
    13	---
    14	
    15	# Task 05: End-to-End Integration and Acceptance Verification
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Every epic requires a final Tier C integration and acceptance task exercising the full end-to-end workflow across all component seams (`bin/d3nexus`, `sync_task_status.py render`, `check_task_contract.py --design`, `run_task_checks.py`, and `task_contract.py` Done-Gate evaluation) and verifying repository-wide quality gates (`scripts/verify.sh`).
    22	
    23	This task creates `tests/test_task_contract_ergonomics_e2e.py` covering the remaining integration scenarios (`TCAE-ST-02`, `TCAE-AR-02`, `TCAE-FR-03`) and running end-to-end subcutaneous workflows in isolated temporary git repositories.
    24	
    25	## Files
    26	
    27	Allowed files:
    28	- `tests/test_task_contract_ergonomics_e2e.py` (new)
    29	- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
    30	
    31	Read-only context:
    32	- `bin/d3nexus` (created in Task 03) (new)
    33	- `skills/dev-implementation/resources/scripts/task_contract.py` (modified in Task 01 and Task 03)
    34	- `skills/dev-implementation/resources/scripts/check_task_contract.py` (modified in Tasks 01–04)
    35	- `skills/dev-implementation/resources/scripts/sync_task_status.py` (modified in Task 02)
    36	- `skills/dev-implementation/resources/scripts/run_task_checks.py` (modified in Task 03)
    37	
    38	## Design Rationale
    39	
    40	Applicable skills: `python-quality-check`, `test-driven-development`.
    41	Placing the end-to-end subcutaneous suite in `tests/test_task_contract_ergonomics_e2e.py` ensures that `python3 -m pytest tests/` exercises the complete lifecycle from single-source authoring to Done-Gate verification on every PR and Epic quality gate run. In addition, fixing the two `Optional[str]` narrowing lines in `check_bdd_traceability.py` ensures clean `mypy` runs across the entire script suite without requiring workarounds.
    42	
    43	## Impact Analysis & Blast Radius
    44	
    45	- **Target Files & Symbols**:
    46	  - `tests/test_task_contract_ergonomics_e2e.py`: new `test_TCAE_ST_02_done_gate_evidence_transition`, new `test_TCAE_AR_02_idempotent_render`, new `test_TCAE_FR_03_render_unknown_covers_aborts`.
    47	  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `scenario_ids`.
    48	- **Downstream Callers**: Gate 4 `quality_check` and `check_bdd_traceability.py tests --results`.
    49	- **Cross-Platform Bridges**: None.
    50	- **Target Test Coverage Threshold**: 100% BDD scenario traceability across all 14 `[TCAE-*]` scenarios.
    51	
    52	### BDD SCENARIOS
    53	
    54	Covers: TCAE-ST-02, TCAE-AR-02, TCAE-FR-03
    55	
    56	```gherkin
    57	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    58	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    59	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    60	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    61	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    62	  Then "evaluate_done_gate" returns an empty problem list
    63	
    64	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    65	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    66	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    67	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    68	
    69	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
    70	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
    73	```
    74	
    75	## Verification
    76	
    77	| ID | Phase | Command | Expect | Needs |
    78	|----|-------|---------|--------|-------|
    79	| V1 | RED | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py::test_TCAE_ST_02_done_gate_evidence_transition` | exit 1; contains "FAILED" | — |
    80	| V2 | GREEN | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py` | exit 0; contains "passed" | — |
    81	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    82	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    83	| V5 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "OK" | — |
    84	| V6 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |
    85	
    86	## Stop and Report If
    87	
    88	- A command, path, symbol or anchor named in this task does not match the repository.
    89	- A Verification row fails for a reason other than its Expect.
    90	- The work needs a change to a file outside Allowed files, or to a protected path.
    91	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    92	  Covers line.
    93	- A variable named in the Needs column is unset.
    94	
    95	## Decisions Already Made
    96	
    97	- `tests/test_task_contract_ergonomics_e2e.py` exercises the end-to-end flow using temporary git repositories (`tmp_path`), invoking `bin/d3nexus` (`sync-status render`, `check-contract --design`, `run-checks verify`) and asserting all 14 `[TCAE-*]` scenarios pass across the test suite.
    98	- In `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, narrow `fence: str | None` before indexing `fence[0]` and `len(fence)` in `scenario_ids()` so `mypy` passes cleanly without `--follow-imports=silent`.
    99	
   100	## Definition of Done
   101	
   102	- End-to-end integration tests in `tests/test_task_contract_ergonomics_e2e.py` pass for `TCAE-ST-02`, `TCAE-AR-02`, and `TCAE-FR-03`. (V2, V6)
   103	- `ruff`, `mypy`, and `bash scripts/verify.sh` pass with zero errors. (V3, V4, V5)
   104	- Full test suite across `tests/` and `skills/dev-implementation/resources/scripts/` passes with 100% `[TCAE-*]` scenario traceability in `build/test-results/pytest.xml`. (V6)
   105	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   106	
   107	## Dependencies & Blockers
   108	
   109	- Blocked by [Task 04](task_04_verification_grammar_and_docs.md)
   110	
   111	## References & Rollback
   112	
   113	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   114	- Rollback: `git revert` the task commit to remove `tests/test_task_contract_ergonomics_e2e.py`.

 succeeded in 0ms:
   104	## Decisions Already Made
   105	
   106	- CLI interface in `skills/dev-implementation/resources/scripts/sync_task_status.py`: `sync_task_status.py render <epic_dir> [--source-root <path>]`.
   107	- When rendering BDD scenarios: if a task has a `Covers:` line with scenario IDs, `render_epic_tasks` extracts the matching scenario blocks from `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` and replaces the ` ```gherkin ... ``` ` block under `### BDD SCENARIOS` (or inserts one immediately after the `Covers:` line). If any covered ID is missing from `bdd_scenarios.en.md`, `render_epic_tasks` raises ValueError / exits 1 without writing partial mirrors.
   108	- When expanding `<!-- @@FILE:<rel_path>@@ -->`: `<rel_path>` must be relative without `..` segments; if the target file content contains ` ``` `, the outer code fence uses ` ```` ` (4 backticks).
   109	- Mirror link rewriting: links targeting files inside `.devtool/epic/<epic_dir>/` (such as `](<epic_dir>.en.md)` or `](./task_01_foo.md)`) are rewritten to `](../epic/<epic_dir>/<target>)` in `.devtool/features/<task>.md`, matching `check_epic_readiness.py` R2 normalization `mirror_text.replace(f"](../epic/{epic_dir}/", "](") == epic_text`.
   110	
   111	## Definition of Done
   112	
   113	- `sync_task_status.py render <epic_dir>` injects verbatim Gherkin blocks, expands `@@FILE:...@@` fences, writes `.devtool/features/` mirrors, and removes orphan mirrors. (V2)
   114	- `check_task_contract.py --design` checks R3 verbatim scenario parity and R2 mirror parity when mirrors exist. (V2)
   115	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   116	- Automated tests for `TCAE-HP-02`, `TCAE-EC-02`, and `TCAE-ST-01` pass and write JUnit XML results. (V5)
   117	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   118	
   119	## Dependencies & Blockers
   120	
   121	- Blocked by [Task 01](task_01_evidence_files_contract.md)
   122	
   123	## References & Rollback
   124	
   125	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   126	- Rollback: `git revert` the task commit to restore `sync_task_status.py` and `check_task_contract.py`.
     1	---
     2	id: "task_03_portable_d3nexus_cli_and_env"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["architecture", "portability", "cli"]
    12	order: "a3"
    13	---
    14	
    15	# Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Resolve Observation #0016: task Verification rows invoke kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/tess/.claude/plugins/cache/...`), which fail when run on another machine, OS user, account profile, or plugin version.
    22	
    23	This task provides a zero-setup portable CLI entrypoint and bans hardcoded user/plugin paths in Verification rows:
    24	1. Create executable `bin/d3nexus` dispatching subcommands (`check-doc`, `check-contract`, `check-readiness`, `sync-status`, `run-checks`) to the kit's scripts relative to `Path(__file__).resolve().parent.parent`.
    25	2. In `run_task_checks.py` (`run_command()`) and `check_epic_readiness.py`, automatically compute `KIT_ROOT = Path(__file__).resolve().parents[4]` and inject `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH="<kit_root>/bin:$PATH"` into the child process environment without mutating `os.environ` of the parent process.
    26	3. Update `scripts/resume_context.py` (`--sync-zshrc`) so interactive terminal shells also export `D3NEXUS_KIT` and prepend `<kit_root>/bin` to `PATH`.
    27	4. In `check_task_contract.py`, reject any Verification row command containing hardcoded user home or plugin cache paths (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`) and recognize `d3nexus` as a built-in kit executable.
    28	
    29	## Files
    30	
    31	Allowed files:
    32	- `bin/d3nexus` (new)
    33	- `skills/dev-implementation/resources/scripts/run_task_checks.py`
    34	- `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
    35	- `skills/dev-implementation/resources/scripts/check_task_contract.py`
    36	- `skills/dev-implementation/resources/scripts/task_contract.py`
    37	- `scripts/resume_context.py`
    38	- `skills/dev-implementation/resources/scripts/test_run_task_checks.py`
    39	- `skills/dev-implementation/resources/scripts/test_check_task_contract.py`
    40	
    41	Read-only context:
    42	- `skills/doc_quality_check/resources/scripts/check_document.py` (target of `d3nexus check-doc`)
    43	- `.devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.en.md` (HLD specification)
    44	
    45	## Design Rationale
    46	
    47	Applicable skills: `python-quality-check`, `test-driven-development`.
    48	Deriving `KIT_ROOT` dynamically from `Path(__file__).resolve().parents[4]` inside `run_task_checks.py` guarantees zero manual setup when switching machines, accounts, or plugin cache versions.
    49	
    50	## Impact Analysis & Blast Radius
    51	
    52	- **Target Files & Symbols**:
    53	  - `skills/dev-implementation/resources/scripts/run_task_checks.py`: `run_command` and new `kit_env`.
    54	  - `skills/dev-implementation/resources/scripts/check_task_contract.py`: `command_paths`, `check_grounding`, and new `check_portable_command`.
    55	  - `skills/dev-implementation/resources/scripts/task_contract.py`: `strip_wrappers`.
    56	- **Downstream Callers**: `skills/dev-implementation/resources/scripts/check_epic_readiness.py`.
    57	- **Cross-Platform Bridges**: None.
    58	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage on `bin/d3nexus`, `kit_env`, and `check_portable_command`.
    59	
    60	### BDD SCENARIOS
    61	
    62	Covers: TCAE-HP-03, TCAE-AR-01, TCAE-FR-02
    63	
    64	```gherkin
    65	Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
    66	  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    67	  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
    68	  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
    69	  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0
    70	
    71	Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
    72	  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
    73	  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
    74	  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
    75	
    76	Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
    77	  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
    78	  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
    79	  When "check_task_contract.py --design" evaluates the task
    80	  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2
    81	```
    82	
    83	## Verification
    84	
    85	| ID | Phase | Command | Expect | Needs |
    86	|----|-------|---------|--------|-------|
    87	| V1 | RED | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py::test_TCAE_HP_03_d3nexus_zero_setup_env` | exit 1; contains "FAILED" | — |
    88	| V2 | GREEN | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py` | exit 0; contains "passed" | — |
    89	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py bin/d3nexus skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py scripts/resume_context.py` | exit 0 | — |
    90	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py --follow-imports=silent skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py` | exit 0 | — |
    91	| V5 | TIER-C | `python3 -m pytest skills/dev-implementation/resources/scripts/test_run_task_checks.py skills/dev-implementation/resources/scripts/test_check_task_contract.py --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |
    92	
    93	## Stop and Report If
    94	
    95	- A command, path, symbol or anchor named in this task does not match the repository.
    96	- A Verification row fails for a reason other than its Expect.
    97	- The work needs a change to a file outside Allowed files, or to a protected path.
    98	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    99	  Covers line.
   100	- A variable named in the Needs column is unset.
   101	
   102	## Decisions Already Made
   103	
   104	- `KIT_ROOT` in `skills/dev-implementation/resources/scripts/run_task_checks.py` is `Path(__file__).resolve().parents[4]`.
   105	- `kit_env() -> dict[str, str]` returns a copy of `os.environ` with `D3NEXUS_KIT=str(KIT_ROOT)` and `PATH=f"{KIT_ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"`.
   106	- `bin/d3nexus` is an executable Python 3 script (`0o755`) supporting subcommands:
   107	  - `check-doc` -> `skills/doc_quality_check/resources/scripts/check_document.py`
   108	  - `check-contract` -> `skills/dev-implementation/resources/scripts/check_task_contract.py`
   109	  - `check-readiness` -> `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
   110	  - `sync-status` -> `skills/dev-implementation/resources/scripts/sync_task_status.py`
   111	  - `run-checks` -> `skills/dev-implementation/resources/scripts/run_task_checks.py`
   112	- `NON_PORTABLE_PATH_RE` in `check_task_contract.py` matches `(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)` and reports `"non-portable path '<match>' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'"`.
   113	
   114	## Definition of Done
   115	
   116	- `bin/d3nexus` dispatches kit subcommands and is automatically placed on `PATH` with `D3NEXUS_KIT` by `run_task_checks.py` and `check_epic_readiness.py`. (V2, V5)
   117	- `check_task_contract.py` rejects hardcoded user home and plugin cache paths in Verification rows. (V2)
   118	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   119	- Automated tests for `TCAE-HP-03`, `TCAE-AR-01`, and `TCAE-FR-02` pass and write JUnit XML results. (V5)
   120	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   121	
   122	## Dependencies & Blockers
   123	
   124	- Blocked by [Task 02](task_02_single_source_render_engine.md)
   125	
   126	## References & Rollback
   127	
   128	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   129	- Rollback: `git revert` the task commit to remove `bin/d3nexus` and restore runtime scripts.

codex
Thiết kế tập trung đúng vào ba điểm nối nhạy cảm: grounding của evidence, đồng bộ task/mirror, và cách CLI đi qua parser lệnh hiện có. Tôi đang kiểm tra các hợp đồng này với luồng Done Gate và readiness để tìm những chỗ có thể khiến implementation phải dừng hoặc tạo hành vi sai.

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_task_contract.py | sed -n '1,245p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Check the task files and HLD a designer wrote against the task contract, before Gate 2 closes.
     3	
     4	Usage:
     5	  check_task_contract.py [--design] --hld <epic_dir>.en.md --tasks <task_*.md ...>
     6	
     7	Prints problems as `<task stem>:<row or section>: <problem>` or `<hld file name>: <problem>`, the
     8	implicit protected paths, and a Result line. Exit codes: 0 no problem; 1 problems; 2 usage error.
     9	Python 3 standard library only.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import importlib
    15	import json
    16	import re
    17	import shlex
    18	import shutil
    19	import subprocess
    20	import sys
    21	from pathlib import Path
    22	from typing import Any
    23	
    24	sys.path.insert(0, str(Path(__file__).resolve().parent))
    25	tc: Any = importlib.import_module("task_contract")
    26	cb: Any = importlib.import_module("check_bdd_traceability")
    27	UsageError: type[Exception] = cb.UsageError
    28	covers_of: Any = cb.covers_of
    29	read_text: Any = cb.read_text
    30	
    31	SECTIONS = ("Files", "Verification", "Definition of Done", "Stop and Report If", "Decisions Already Made")
    32	ROW_PREFIX = re.compile(r"^Verification row [^:]+: ")
    33	STATUS = re.compile(r'^status:\s*"?([A-Za-z_-]+)"?\s*$', re.MULTILINE)
    34	GLOB_CHARS = re.compile(r"[*?]")
    35	WEAK_ASSERTION_RE = re.compile(r"\b(should be truthy|is valid|should work|returns non-empty)\b", re.IGNORECASE)
    36	
    37	
    38	class Checker:
    39	    def __init__(self, root: Path) -> None:
    40	        self.root = root
    41	        self.problems: list[str] = []
    42	        self.warnings: list[str] = []
    43	        listed = subprocess.run(["git", "ls-files", "-z"], check=False, cwd=root, capture_output=True, text=True).stdout
    44	        self.tracked = set(listed.split("\0")) - {""}
    45	
    46	    def ignored(self, path: str) -> bool:
    47	        return subprocess.run(["git", "check-ignore", "-q", "--", path], check=False, cwd=self.root,
    48	                              capture_output=True).returncode == 0
    49	
    50	    def problem(self, where: str, text: str) -> None:
    51	        self.problems.append(f"{where}: {text}")
    52	
    53	    def is_tracked(self, path: str) -> bool:
    54	        return path in self.tracked
    55	
    56	    def matches_tracked(self, pattern: str) -> bool:
    57	        return any(tc.path_matches(pattern, name) for name in self.tracked)
    58	
    59	
    60	def read_file(path: Path) -> str:
    61	    try:
    62	        return str(read_text(path))
    63	    except OSError as error:
    64	        raise UsageError(f"cannot read {path}: {error.strerror or error}") from None
    65	
    66	
    67	def table_rows(check: Checker, stem: str, text: str) -> list[Any]:
    68	    """Parse the Verification table row by row, reporting every bad row rather than the first."""
    69	    body = tc.section(text, "Verification")
    70	    if body is None:
    71	        return []
    72	    table = [line for line in body.splitlines() if line.lstrip().startswith("|")]
    73	    if not table or tc.split_cells(table[0]) != tc.HEADER:
    74	        check.problem(f"{stem}:Verification", "Verification header must be exactly: | " + " | ".join(tc.HEADER) + " |")
    75	        return []
    76	    rows: list[Any] = []
    77	    seen: set[str] = set()
    78	    for line in table[2:]:
    79	        cells = tc.split_cells(line)
    80	        try:
    81	            if len(cells) != len(tc.HEADER):
    82	                raise tc.ContractError(f"Verification row {cells[0]!r}: expected {len(tc.HEADER)} cells, found {len(cells)}")
    83	            rows.append(tc.parse_row(cells, seen))
    84	            if rows[-1].phase != "TIER-C" and rows[-1].expect.results:
    85	                check.problem(f"{stem}:{cells[0]}", "results is allowed only on TIER-C rows")
    86	        except tc.ContractError as error:
    87	            check.problem(f"{stem}:{cells[0]}", ROW_PREFIX.sub("", str(error)))
    88	        seen.add(cells[0])
    89	    return rows
    90	
    91	
    92	def check_structure(check: Checker, stem: str, path: Path, text: str, rows: list[Any]) -> None:
    93	    for title in SECTIONS:
    94	        if tc.section(text, title) is None:
    95	            check.problem(f"{stem}:{title}", "section is missing")
    96	    if tc.section(text, "Files") is not None and not tc.parse_allowed_files(text):
    97	        check.problem(f"{stem}:Files", "Allowed files lists no entry")
    98	    v_sec = tc.section(text, "Verification")
    99	    if v_sec is not None:
   100	        reason = next((m.group(1) for m in map(tc.RED_NA.match, v_sec.splitlines()) if m), None)
   101	        if not any(row.phase == "RED" for row in rows) and not (reason and reason.strip()):
   102	            check.problem(f"{stem}:Verification", "no RED row and no RED: n/a line with a reason")
   103	        if covers_of(path) and not any(row.phase == "TIER-C" and row.expect.results for row in rows):
   104	            check.problem(f"{stem}:Verification", "Covers line but no TIER-C row with results")
   105	    ids = {row.id for row in rows}
   106	    for bullet in tc.dod_bullets(text):
   107	        reference = tc.DOD_REFERENCE.search(bullet)
   108	        if not reference:
   109	            check.problem(f"{stem}:Definition of Done", f"{bullet} ends with no (V<n>) or (Gate 5) reference")
   110	            continue
   111	        missing = [name for name in re.findall(r"V[0-9]+", reference.group(1)) if name not in ids]
   112	        if missing:
   113	            check.problem(f"{stem}:Definition of Done",
   114	                          f"{bullet} references {', '.join(missing)}, which the table lacks")
   115	    has_executable = any(row.phase in ("RED", "GREEN") for row in rows)
   116	    if has_executable:
   117	        decisions = tc.section(text, "Decisions Already Made")
   118	        clean_decisions = decisions.strip().lower() if decisions else ""
   119	        if not decisions or not clean_decisions or clean_decisions in ("none", "none.", "n/a"):
   120	            check.problem(f"{stem}:Decisions Already Made",
   121	                          "executable task requires grounded facts, cannot be empty or 'None'")
   122	
   123	
   124	def check_allowed(check: Checker, stem: str, text: str, design: bool) -> None:
   125	    for entry in tc.parse_allowed_files(text):
   126	        pattern = entry.pattern
   127	        if entry.new:
   128	            if design:
   129	                parent = (check.root / pattern).parent
   130	                if (check.root / pattern).exists():
   131	                    check.problem(f"{stem}:Files", f"{pattern} is marked (new) but already exists")
   132	                elif not (parent.exists() or parent.parent.exists()):
   133	                    check.problem(f"{stem}:Files", f"{pattern} (new) has no parent or grandparent directory")
   134	        elif pattern.endswith("/") or (not GLOB_CHARS.search(pattern) and (check.root / pattern).is_dir()):
   135	            check.problem(f"{stem}:Files", f"{pattern} is a directory; list files or a glob")
   136	        elif GLOB_CHARS.search(pattern):
   137	            if not check.matches_tracked(pattern):
   138	                check.problem(f"{stem}:Files", f"{pattern} matches no tracked file")
   139	        elif not check.is_tracked(pattern):
   140	            check.problem(f"{stem}:Files", f"{pattern} is not tracked by git")
   141	
   142	
   143	def command_paths(command: str) -> tuple[list[str], str | None]:
   144	    """Path-like tokens of a command, and its executable when that is a bare name."""
   145	    try:
   146	        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
   147	        lexer.whitespace_split = True
   148	        tokens = list(lexer)
   149	    except ValueError:
   150	        return [], None
   151	    paths: list[str] = []
   152	    for token in tokens:
   153	        value = token.split("=", 1)[1] if token.startswith("-") and "=" in token else token
   154	        if "/" in value and not value.startswith("-") and not re.search(r"[*$]|://", value):
   155	            clean_path = value.split("::", 1)[0]
   156	            paths.append(clean_path.removeprefix("./"))
   157	    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
   158	    first = program[0] if program else None
   159	    return paths, first if first and "/" not in first else None
   160	
   161	
   162	def check_grounding(check: Checker, stem: str, text: str, rows: list[Any], created: set[str]) -> None:
   163	    for context in tc.parse_read_only_context(text):
   164	        if not (check.root / context).exists() and context not in created:
   165	            check.problem(f"{stem}:Files", f"Read-only context {context} does not exist and is not (new) in any task")
   166	    for row in rows:
   167	        paths, executable = command_paths(row.command)
   168	        for path in paths:
   169	            if not (check.root / path).exists() and not check.ignored(path) and path not in created:
   170	                check.problem(f"{stem}:{row.id}",
   171	                              f"{path} does not exist, is not ignored by git and is not (new) in any task")
   172	        if executable and shutil.which(executable) is None:
   173	            check.warnings.append(f"warning: {stem}:{row.id}: executable {executable} not found on PATH")
   174	
   175	
   176	def check_pytest_k(check: Checker, stem: str, row: Any) -> None:
   177	    try:
   178	        tokens = shlex.split(row.command)
   179	    except ValueError:
   180	        tokens = row.command.split()
   181	    program = tc.strip_wrappers([t for t in tokens if t not in tc.CONTROL_TOKENS])
   182	    if not program or "pytest" not in program[0]:
   183	        return
   184	    for i, token in enumerate(tokens):
   185	        val: str | None = None
   186	        if token == "-k" and i + 1 < len(tokens):
   187	            val = tokens[i + 1]
   188	        elif token.startswith("-k="):
   189	            val = token.split("=", 1)[1]
   190	        elif token.startswith("-k") and len(token) > 2:
   191	            val = token[2:]
   192	        if val is not None and ("::" not in val or not val.split("::", 1)[0].endswith(".py")):
   193	            check.problem(f"{stem}:{row.id}",
   194	                          f"pytest -k expression must use an exact node ID (<file>::<test>), found: {val!r}")
   195	
   196	
   197	def is_python_task(text: str, rows: list[Any]) -> bool:
   198	    entries = tc.parse_allowed_files(text)
   199	    for entry in entries:
   200	        pat = entry.pattern.lower()
   201	        if pat.endswith(".py") or pat in ("pyproject.toml", "setup.py", "requirements.txt", "pipfile"):
   202	            return True
   203	    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
   204	    for row in tier_b_rows:
   205	        try:
   206	            tokens = shlex.split(row.command)
   207	        except ValueError:
   208	            tokens = row.command.split()
   209	        if "ruff" in tokens or any("ruff" in t for t in tokens):
   210	            return True
   211	    return False
   212	
   213	
   214	def check_python_tier_b(check: Checker, stem: str, rows: list[Any]) -> None:
   215	    tier_b_rows = [r for r in rows if r.phase == "TIER-B"]
   216	    manifest_path = check.root / ".agents" / "quality" / "python-quality.json"
   217	    if manifest_path.exists():
   218	        try:
   219	            data = json.loads(manifest_path.read_text(encoding="utf-8"))
   220	        except (json.JSONDecodeError, OSError):
   221	            check.problem(f"{stem}:Verification", "malformed .agents/quality/python-quality.json manifest")
   222	            return
   223	        if not isinstance(data, dict):
   224	            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: root must be an object")
   225	            return
   226	        capabilities = data.get("capabilities")
   227	        if not isinstance(capabilities, dict):
   228	            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: capabilities must be an object")
   229	            return
   230	        lint_cmd = capabilities.get("lint")
   231	        type_check_cmd = capabilities.get("type_check")
   232	        if not isinstance(lint_cmd, list) or not lint_cmd or not all(isinstance(x, str) for x in lint_cmd):
   233	            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: lint capability missing or invalid")
   234	            return
   235	        if not isinstance(type_check_cmd, list) or not type_check_cmd or not all(isinstance(x, str) for x in type_check_cmd):
   236	            check.problem(f"{stem}:Verification", "invalid python-quality.json manifest: type_check capability missing or invalid")
   237	            return
   238	
   239	        def matches_cap(cap: list[str], command: str) -> bool:
   240	            try:
   241	                row_toks = shlex.split(command)
   242	            except ValueError:
   243	                row_toks = command.split()
   244	            if row_toks == cap:
   245	                return True

exec
/bin/zsh -lc "nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_05_end_to_end_contract_acceptance.md; nl -ba .devtool/epic/contract_and_authoring_ergonomics/task_04_verification_grammar_and_docs.md | sed -n '93,115p'; nl -ba .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_05_end_to_end_contract_acceptance"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "contract-and-authoring-ergonomics"
     7	dueDate: null
     8	created: "2026-11-06T01:50:00Z"
     9	modified: "2026-11-06T01:50:00Z"
    10	completedAt: null
    11	labels: ["integration", "acceptance", "tier-c"]
    12	order: "a5"
    13	---
    14	
    15	# Task 05: End-to-End Integration and Acceptance Verification
    16	
    17	Epic: [contract_and_authoring_ergonomics](contract_and_authoring_ergonomics.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Every epic requires a final Tier C integration and acceptance task exercising the full end-to-end workflow across all component seams (`bin/d3nexus`, `sync_task_status.py render`, `check_task_contract.py --design`, `run_task_checks.py`, and `task_contract.py` Done-Gate evaluation) and verifying repository-wide quality gates (`scripts/verify.sh`).
    22	
    23	This task creates `tests/test_task_contract_ergonomics_e2e.py` covering the remaining integration scenarios (`TCAE-ST-02`, `TCAE-AR-02`, `TCAE-FR-03`) and running end-to-end subcutaneous workflows in isolated temporary git repositories.
    24	
    25	## Files
    26	
    27	Allowed files:
    28	- `tests/test_task_contract_ergonomics_e2e.py` (new)
    29	- `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
    30	
    31	Read-only context:
    32	- `bin/d3nexus` (created in Task 03) (new)
    33	- `skills/dev-implementation/resources/scripts/task_contract.py` (modified in Task 01 and Task 03)
    34	- `skills/dev-implementation/resources/scripts/check_task_contract.py` (modified in Tasks 01–04)
    35	- `skills/dev-implementation/resources/scripts/sync_task_status.py` (modified in Task 02)
    36	- `skills/dev-implementation/resources/scripts/run_task_checks.py` (modified in Task 03)
    37	
    38	## Design Rationale
    39	
    40	Applicable skills: `python-quality-check`, `test-driven-development`.
    41	Placing the end-to-end subcutaneous suite in `tests/test_task_contract_ergonomics_e2e.py` ensures that `python3 -m pytest tests/` exercises the complete lifecycle from single-source authoring to Done-Gate verification on every PR and Epic quality gate run. In addition, fixing the two `Optional[str]` narrowing lines in `check_bdd_traceability.py` ensures clean `mypy` runs across the entire script suite without requiring workarounds.
    42	
    43	## Impact Analysis & Blast Radius
    44	
    45	- **Target Files & Symbols**:
    46	  - `tests/test_task_contract_ergonomics_e2e.py`: new `test_TCAE_ST_02_done_gate_evidence_transition`, new `test_TCAE_AR_02_idempotent_render`, new `test_TCAE_FR_03_render_unknown_covers_aborts`.
    47	  - `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`: `scenario_ids`.
    48	- **Downstream Callers**: Gate 4 `quality_check` and `check_bdd_traceability.py tests --results`.
    49	- **Cross-Platform Bridges**: None.
    50	- **Target Test Coverage Threshold**: 100% BDD scenario traceability across all 14 `[TCAE-*]` scenarios.
    51	
    52	### BDD SCENARIOS
    53	
    54	Covers: TCAE-ST-02, TCAE-AR-02, TCAE-FR-03
    55	
    56	```gherkin
    57	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    58	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    59	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    60	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    61	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    62	  Then "evaluate_done_gate" returns an empty problem list
    63	
    64	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    65	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    66	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    67	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    68	
    69	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
    70	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
    73	```
    74	
    75	## Verification
    76	
    77	| ID | Phase | Command | Expect | Needs |
    78	|----|-------|---------|--------|-------|
    79	| V1 | RED | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py::test_TCAE_ST_02_done_gate_evidence_transition` | exit 1; contains "FAILED" | — |
    80	| V2 | GREEN | `python3 -m pytest tests/test_task_contract_ergonomics_e2e.py` | exit 0; contains "passed" | — |
    81	| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    82	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | exit 0 | — |
    83	| V5 | TIER-B | `bash scripts/verify.sh` | exit 0; contains "OK" | — |
    84	| V6 | TIER-C | `python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml` | exit 0; results build/test-results/pytest.xml | — |
    85	
    86	## Stop and Report If
    87	
    88	- A command, path, symbol or anchor named in this task does not match the repository.
    89	- A Verification row fails for a reason other than its Expect.
    90	- The work needs a change to a file outside Allowed files, or to a protected path.
    91	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
    92	  Covers line.
    93	- A variable named in the Needs column is unset.
    94	
    95	## Decisions Already Made
    96	
    97	- `tests/test_task_contract_ergonomics_e2e.py` exercises the end-to-end flow using temporary git repositories (`tmp_path`), invoking `bin/d3nexus` (`sync-status render`, `check-contract --design`, `run-checks verify`) and asserting all 14 `[TCAE-*]` scenarios pass across the test suite.
    98	- In `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, narrow `fence: str | None` before indexing `fence[0]` and `len(fence)` in `scenario_ids()` so `mypy` passes cleanly without `--follow-imports=silent`.
    99	
   100	## Definition of Done
   101	
   102	- End-to-end integration tests in `tests/test_task_contract_ergonomics_e2e.py` pass for `TCAE-ST-02`, `TCAE-AR-02`, and `TCAE-FR-03`. (V2, V6)
   103	- `ruff`, `mypy`, and `bash scripts/verify.sh` pass with zero errors. (V3, V4, V5)
   104	- Full test suite across `tests/` and `skills/dev-implementation/resources/scripts/` passes with 100% `[TCAE-*]` scenario traceability in `build/test-results/pytest.xml`. (V6)
   105	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   106	
   107	## Dependencies & Blockers
   108	
   109	- Blocked by [Task 04](task_04_verification_grammar_and_docs.md)
   110	
   111	## References & Rollback
   112	
   113	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   114	- Rollback: `git revert` the task commit to remove `tests/test_task_contract_ergonomics_e2e.py`.
    93	## Decisions Already Made
    94	
    95	- In `skills/dev-implementation/resources/scripts/check_task_contract.py`, `command_paths(command: str)` splits subcommands on `tc.CONTROL_TOKENS` (`&&`, `||`, `;`, `|`). For any subcommand whose unwrapped program is `grep`, `egrep`, `fgrep`, `rg`, `sed`, or `awk`, the pattern argument (the token after `-e`/`--regexp` or the first non-flag positional argument when no `-e`/`-f` flag is present) is skipped before collecting path tokens.
    96	- When the first token of a subcommand (before `env`) matches `^[A-Za-z_][A-Za-z0-9_]*=.*`, `check_grounding` records a problem: `"inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')"`.
    97	- `Implicit protected paths:` in `check_task_contract.py` formats each entry as `<path> (<task_stem>:<row_id>, ...)`.
    98	- `skills/dev-designer/references/verification-row-grammar.md` includes a `## Table of Contents` and documents all 6 rules (`\|` unescaping, `env VAR=val`, grep pattern rules, `Evidence files:`, `d3nexus` / `$D3NEXUS_KIT`, and 4-backtick outer code fences).
    99	
   100	## Definition of Done
   101	
   102	- `command_paths()` excludes `grep`/`rg`/`sed`/`awk` pattern arguments from missing-path errors and reports bare `VAR=val` assignments and implicit protected path provenance. (V2)
   103	- `skills/dev-designer/references/verification-row-grammar.md`, `skills/dev-designer/SKILL.md`, and `skills/principal-review/SKILL.md` are updated and pass document linting. (V5)
   104	- `ruff` and `mypy` pass with zero errors. (V3, V4)
   105	- Automated tests for `TCAE-HP-04` and `TCAE-EC-03` pass and write JUnit XML results. (V6)
   106	- Clean git working tree with changes restricted to Allowed files. (Gate 5)
   107	
   108	## Dependencies & Blockers
   109	
   110	- Blocked by [Task 03](task_03_portable_d3nexus_cli_and_env.md)
   111	
   112	## References & Rollback
   113	
   114	- Reference: [2026-11-06-contract-and-authoring-ergonomics-design.en.md](2026-11-06-contract-and-authoring-ergonomics-design.en.md).
   115	- Rollback: `git revert` the task commit to restore `check_task_contract.py` and skill documentation.
     1	# BDD Test Scenarios: Task Contract and Authoring Ergonomics
     2	
     3	## Table of Contents
     4	
     5	- [Dimension 1: Happy Paths](#dimension-1-happy-paths)
     6	- [Dimension 2: Edge Cases and Boundaries](#dimension-2-edge-cases-and-boundaries)
     7	- [Dimension 3: State Transitions](#dimension-3-state-transitions)
     8	- [Dimension 4: Async and Concurrency](#dimension-4-async-and-concurrency)
     9	- [Dimension 5: Failures and Resilience](#dimension-5-failures-and-resilience)
    10	
    11	## Dimension 1: Happy Paths
    12	
    13	```gherkin
    14	Scenario: [TCAE-HP-01] [Tier C - Integration] Evidence files declaration passes design contract and Done-Gate verification
    15	  Given a task declaring ".devtool/epic/sample_epic/evidence/baseline.txt (new)" under "Evidence files:" in "## Files"
    16	  And a Verification row referencing ".devtool/epic/sample_epic/evidence/baseline.txt"
    17	  When check_task_contract.py runs with "--design"
    18	  Then it exits 0 with 0 problems and grounds the new evidence path across the epic
    19	  And when run_task_checks.py verify executes the row that writes ".devtool/epic/sample_epic/evidence/baseline.txt"
    20	  Then evaluate_done_gate confirms the evidence file exists on disk and passes all Done-Gate conditions
    21	
    22	Scenario: [TCAE-HP-02] [Tier C - Integration] Single-source task rendering injects verbatim BDD, embeds code, and writes mirror
    23	  Given a single-source task ".devtool/epic/sample_epic/task_01_setup.md" with "Covers: TCAE-HP-01" and a "<!-- @@FILE:src/helper.py@@ -->" directive
    24	  And ".devtool/epic/sample_epic/bdd_scenarios.en.md" defining scenario "[TCAE-HP-01]"
    25	  When "sync_task_status.py render sample_epic" executes
    26	  Then ".devtool/epic/sample_epic/task_01_setup.md" contains the exact verbatim Gherkin block for "[TCAE-HP-01]" and the exact contents of "src/helper.py"
    27	  And ".devtool/features/task_01_setup.md" is generated with relative links rewritten to "../epic/sample_epic/"
    28	  And "check_task_contract.py --design" exits 0 with zero R2 or R3 findings
    29	
    30	Scenario: [TCAE-HP-03] [Tier C - Integration] Zero-setup d3nexus CLI execution inside Verification rows
    31	  Given a task Verification row invoking "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    32	  When "run_task_checks.py verify" executes the task in a temporary git repository without pre-configured shell exports
    33	  Then "run_task_checks.py" automatically injects "D3NEXUS_KIT" and prepends "<kit_root>/bin" to "PATH"
    34	  And "d3nexus check-doc" dispatches to "check_document.py" and exits 0
    35	
    36	Scenario: [TCAE-HP-04] [Tier A - Unit] Verification row grammar with escaped pipes, env assignments, and implicit protected path provenance
    37	  Given a Verification row command using "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    38	  When "check_task_contract.py --design" evaluates the task
    39	  Then "task_contract.py" unescapes "\|" to "|" in the parsed command without raising a contract problem
    40	  And "check_task_contract.py" reports "scripts/tool.py (task_01:V1)" in the "Implicit protected paths:" line
    41	```
    42	
    43	## Dimension 2: Edge Cases and Boundaries
    44	
    45	```gherkin
    46	Scenario: [TCAE-EC-01] [Tier A - Unit] Task without Evidence files or Covers line remains backward-compatible
    47	  Given a legacy task file that omits the "Evidence files:" subsection and omits the "Covers:" line
    48	  When "sync_task_status.py render" and "check_task_contract.py --design" run on the epic
    49	  Then "sync_task_status.py render" generates the ".devtool/features/" mirror without modifying the task's BDD section
    50	  And "check_task_contract.py --design" exits 0 with 0 problems
    51	
    52	Scenario: [TCAE-EC-02] [Tier A - Unit] Embedded file containing triple backticks promotes outer fence to four backticks
    53	  Given a source file "docs/snippet.md" containing a fenced code block delimited by three backticks
    54	  And a task containing "<!-- @@FILE:docs/snippet.md@@ -->" immediately above a three-backtick code fence
    55	  When "sync_task_status.py render sample_epic" executes
    56	  Then the rendered code block in both the epic task and the ".devtool/features/" mirror uses a four-backtick outer fence
    57	
    58	Scenario: [TCAE-EC-03] [Tier A - Unit] Search patterns containing slashes in grep, rg, sed, and awk are not flagged as missing paths
    59	  Given a Verification row command "grep -E 'foo/bar/baz' README.md" where "foo/bar/baz" is not a file on disk
    60	  When "check_task_contract.py --design" inspects the command tokens
    61	  Then "command_paths()" excludes the search pattern "foo/bar/baz" from path existence checks
    62	  And "check_task_contract.py" exits 0 without reporting "foo/bar/baz does not exist"
    63	```
    64	
    65	## Dimension 3: State Transitions
    66	
    67	```gherkin
    68	Scenario: [TCAE-ST-01] [Tier A - Unit] Rendering cleans up orphan mirrors and preserves done board location
    69	  Given ".devtool/features/task_99_obsolete.md" with frontmatter "epic: sample-epic" whose source file was deleted from ".devtool/epic/sample_epic/"
    70	  And ".devtool/epic/sample_epic/task_01_done.md" with frontmatter "status: \"done\""
    71	  When "sync_task_status.py render sample_epic" executes
    72	  Then ".devtool/features/task_99_obsolete.md" is removed from disk
    73	  And the mirror for "task_01_done.md" is written at ".devtool/features/done/task_01_done.md"
    74	
    75	Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate transitions from FAIL to PASS once declared Evidence file is written
    76	  Given a task declaring ".devtool/epic/sample_epic/evidence/summary.json (new)" under "Evidence files:"
    77	  When "evaluate_done_gate" runs before ".devtool/epic/sample_epic/evidence/summary.json" is created on disk
    78	  Then "evaluate_done_gate" returns a condition failure naming ".devtool/epic/sample_epic/evidence/summary.json"
    79	  And when the verification run writes non-empty JSON to ".devtool/epic/sample_epic/evidence/summary.json"
    80	  Then "evaluate_done_gate" returns an empty problem list
    81	```
    82	
    83	## Dimension 4: Async and Concurrency
    84	
    85	```gherkin
    86	Scenario: [TCAE-AR-01] [Tier A - Unit] Isolated subprocess environment injection across concurrent row executions
    87	  Given two concurrent invocations of "run_task_checks.py" running in separate temporary git worktrees
    88	  When each invocation executes a Verification row printing "$D3NEXUS_KIT" and "$(which d3nexus)"
    89	  Then both subprocesses resolve the exact kit root path without mutating "os.environ" of the parent Python process
    90	
    91	Scenario: [TCAE-AR-02] [Tier C - Integration] Deterministic idempotent re-rendering across repeated render calls
    92	  Given an epic directory with multiple tasks covering multiple scenarios and file embeds
    93	  When "sync_task_status.py render sample_epic" is executed twice in succession without intermediate edits
    94	  Then the second run produces byte-for-byte identical files in ".devtool/epic/sample_epic/" and ".devtool/features/"
    95	```
    96	
    97	## Dimension 5: Failures and Resilience
    98	
    99	```gherkin
   100	Scenario: [TCAE-FR-01] [Tier A - Unit] Reject invalid Evidence files path outside epic evidence directory or with path traversal
   101	  Given a task listing ".devtool/epic/sample_epic/../secret.txt (new)" or "src/output.json (new)" under "Evidence files:"
   102	  When "check_task_contract.py --design" evaluates the task
   103	  Then it exits 1 and reports that every "Evidence files:" entry must reside under ".devtool/epic/<epic_dir>/evidence/" without ".." segments
   104	
   105	Scenario: [TCAE-FR-02] [Tier A - Unit] Reject hardcoded user home or plugin cache paths and bare VAR=value in Verification rows
   106	  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
   107	  And row V2 calling "FOO=bar pytest tests/unit/test_sample.py::test_ok" without "env"
   108	  When "check_task_contract.py --design" evaluates the task
   109	  Then it exits 1 reporting a non-portable absolute path on V1 and an unprefixed inline environment assignment on V2
   110	
   111	Scenario: [TCAE-FR-03] [Tier C - Integration] Render aborts cleanly when Covers references an unknown scenario ID or missing embed file
   112	  Given a task in ".devtool/epic/sample_epic/" whose "Covers:" line names "TCAE-HP-99" which is absent from "bdd_scenarios.en.md"
   113	  When "sync_task_status.py render sample_epic" executes
   114	  Then it exits 1 naming the unknown scenario ID "TCAE-HP-99" and leaves existing ".devtool/features/" files untouched
   115	```
   116	

exec
/bin/zsh -lc 'cat .devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.vi.md .devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.vi.md .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Đặc tả Thiết kế Hợp đồng Task và Tối ưu Soạn thảo (Task Contract and Authoring Ergonomics)

## Mục lục

- [Tổng quan và Bối cảnh](#tổng-quan-và-bối-cảnh)
- [Phát biểu Bài toán và Các Observations được Giải quyết](#phát-biểu-bài-toán-và-các-observations-được-giải-quyết)
- [Mục tiêu và Phi mục tiêu](#mục-tiêu-và-phi-mục-tiêu)
- [Kiến trúc và Thiết kế Thành phần](#kiến-trúc-và-thiết-kế-thành-phần)
  - [Sơ đồ Cấu trúc Thành phần](#sơ-đồ-cấu-trúc-thành-phần)
  - [1. Hợp đồng Khai báo Evidence Files](#1-hợp-đồng-khai-báo-evidence-files)
  - [2. Soạn thảo Task Một Nguồn Duy nhất và Bộ máy Auto-Render](#2-soạn-thảo-task-một-nguồn-duy-nhất-và-bộ-máy-auto-render)
  - [3. Điểm vào CLI Khả chuyển Không cần Cài đặt (Zero-Setup)](#3-điểm-vào-cli-khả-chuyển-không-cần-cài-đặt-zero-setup)
  - [4. Tài liệu Quy chiếu Ngữ pháp Bảng Verification và Chẩn đoán Lỗi](#4-tài-liệu-quy-chiếu-ngữ-pháp-bảng-verification-và-chẩn-đoán-lỗi)
- [Xử lý Lỗi và Các Trường hợp Biên](#xử-lý-lỗi-và-các-trường-hợp-biên)
- [Chiến lược Kiểm thử và Xác minh](#chiến-lược-kiểm-thử-và-xác-minh)
- [Cảnh báo Shared Contract](#cảnh-báo-shared-contract)
- [Ánh xạ Phụ thuộc và Bối cảnh Lộ trình](#ánh-xạ-phụ-thuộc-và-bối-cảnh-lộ-trình)

## Tổng quan và Bối cảnh

Trong quá trình đóng gói và thực thi nhiều epic trên các kho mã nguồn vệ tinh (`lyrics-sync`), 15 ghi nhận thực tế (`#0006` đến `#0020`) đã được lưu lại trong `skill-observations/observation-log/`. Để triển khai các cải tiến một cách bài bản và kiểm chứng được qua `dev-lifecycle`, 15 observations này được chia thành lộ trình tối ưu hóa gồm 3 Epics độc lập:

1. **Epic 1 (`contract_and_authoring_ergonomics`)**: Giải quyết các observations `#0008`, `#0009`, `#0012`, `#0016` và `#0019` bằng cách loại bỏ việc nhân bản thủ công khi viết task, cho phép khai báo đường dẫn bằng chứng (`Evidence files:`) dưới `.devtool/`, cung cấp CLI khả chuyển tự động cấu hình cho các công cụ của kit, và chuẩn hóa chẩn đoán ngữ pháp bảng Verification.
2. **Epic 2 (`execution_and_verification_infrastructure`)**: Giải quyết các observations `#0006`, `#0007`, `#0010`, `#0011`, `#0017` và `#0018` (khởi tạo extras cho môi trường worktree, bộ công cụ ghi nhận và so sánh baseline hồi quy, kiểm thử tích hợp live opt-in, công cụ replay văn bản task trước khi đóng gói, mẫu thực thi `MEASURE`, và kiểm tra cache-bust cho mô-đun JS tĩnh).
3. **Epic 3 (`multi_epic_orchestration_and_governance`)**: Giải quyết các observations `#0013`, `#0014`, `#0015` và `#0020` (khai báo `Depends on epic:`, xếp hàng `backlog` thông minh theo xung đột file thực tế, quy trình cập nhật epic đã đóng gói kèm `Spec Errata`, và sổ cái lưu vết phê duyệt Gate có cấu trúc).

Tài liệu đặc tả này định nghĩa thiết kế chi tiết cho **Epic 1 (`contract_and_authoring_ergonomics`)**.

## Phát biểu Bài toán và Các Observations được Giải quyết

| Mã Observation | Vấn đề Cốt lõi | Nguyên nhân Gốc rễ |
| :--- | :--- | :--- |
| **#0008** | Các dòng Verification và `Read-only context:` không thể tham chiếu tới file bằng chứng do task tạo ra dưới `.devtool/epic/<epic_dir>/evidence/`. | `.devtool/` bị cấm đưa vào `Allowed files:`, trong khi `check_task_contract.py` từ chối mọi đường dẫn chưa tồn tại và không được đánh dấu `(new)` trong `Allowed files:`. |
| **#0009** | `check_epic_readiness.py` (Rule R3) yêu cầu khối Gherkin trong task phải khớp nguyên văn với `bdd_scenarios.en.md`, nhưng `dev-designer` lại hướng dẫn viết tóm tắt scenario và `check_task_contract.py --design` không kiểm tra R3. | Quy tắc không đồng nhất giữa hướng dẫn trong `dev-designer`, công cụ `check_task_contract.py --design` và `check_epic_readiness.py`. |
| **#0012** | Mỗi file task phải viết và duy trì ở 2 nơi (`.devtool/epic/<epic_dir>/task_*.md` và `.devtool/features/task_*.md`), đồng thời các đoạn code mẫu nhúng trong task bị trôi lệch so với bản đã kiểm chứng. | Thiếu bước render từ một nguồn duy nhất trong `sync_task_status.py` để tự động sinh bản mirror `.devtool/features/` và điền code hoặc khối BDD nguyên văn. |
| **#0016** | Bảng Verification gọi các script của kit (`check_document.py`) bằng đường dẫn tuyệt đối gắn với máy hoặc profile cá nhân (`/Users/.../antigravity_homes/...`), làm hỏng tính khả chuyển khi đổi máy, đổi tài khoản hoặc nâng bản cập nhật plugin. | Chưa tự động tiêm biến môi trường hoặc `PATH` của kit vào `run_task_checks.py` / `check_epic_readiness.py`, và chưa có rule chặn đường dẫn tuyệt đối cá nhân. |
| **#0019** | Bảng Verification có nhiều bẫy ngữ pháp ngầm (unescape `\|` gây báo lỗi giả khi `principal-review`, viết `VAR=val` thiếu `env` bị hiểu nhầm là tên file thực thi, biểu thức grep chứa `/` bị coi là đường dẫn file bị thiếu, và không rõ nguồn gốc của implicit protected paths). | Các quy tắc phân tích ngầm trong `task_contract.py` và `check_task_contract.py` chưa được giải thích rõ trong thông báo lỗi hoặc gom về một tài liệu tham chiếu chung cho `dev-designer` và `principal-review`. |

## Mục tiêu và Phi mục tiêu

### Mục tiêu

- Bổ sung tiểu mục `Evidence files:` dưới `## Files` trong `task_*.md` hỗ trợ đánh dấu `(new)` cho các đường dẫn `.devtool/epic/<epic_dir>/evidence/*`, được kiểm tra ở cả pha `--design` và tại cổng hoàn tất Done Gate (`#0008`).
- Xác lập `.devtool/epic/<epic_dir>/task_*.md` làm nguồn sự thật duy nhất (Single Source of Truth) và thêm lệnh `sync_task_status.py render <epic_dir> [--source-root <dir>]` để tự động chèn khối Gherkin nguyên văn từ `bdd_scenarios.en.md` (`#0009`), bung nội dung file từ chỉ thị `<!-- @@FILE:path@@ -->`, và sinh bản mirror `.devtool/features/task_*.md` với liên kết tương đối được viết lại tự động (`#0012`).
- Đưa kiểm tra R2 (đồng bộ mirror) và R3 (khớp BDD nguyên văn) vào chạy sớm ngay trong `check_task_contract.py --design` (`#0009`, `#0012`).
- Cung cấp CLI khả chuyển `bin/d3nexus` và tự động tiêm `D3NEXUS_KIT=<kit_root>` cùng `PATH="<kit_root>/bin:$PATH"` ngay lúc chạy bên trong `run_task_checks.py` và `check_epic_readiness.py` (`#0016`).
- Chặn mọi đường dẫn tuyệt đối gắn với máy hoặc profile cá nhân trong bảng Verification khi chạy `check_task_contract.py` (`#0016`).
- Nâng cấp thông báo chẩn đoán ngữ pháp của `check_task_contract.py` (`env VAR=value`, loại trừ mẫu tìm kiếm grep khỏi kiểm tra đường dẫn, hiển thị nguồn gốc implicit protected paths) và tài liệu hóa chuẩn mực tại `skills/dev-designer/references/verification-row-grammar.md` cùng `skills/principal-review/SKILL.md` (`#0019`).

### Phi mục tiêu

- Không thay đổi cấu trúc bảng Markdown 5 cột (`| ID | Phase | Command | Expect | Needs |`) của mục `## Verification`.
- Không sửa đổi quy trình khởi tạo worktree, script baseline hồi quy hay lịch trình phụ thuộc liên epic (thuộc phạm vi của Epic 2 và Epic 3).
- Không làm gãy tính tương thích ngược đối với các epic cũ hoặc đang chạy mà không khai báo `Evidence files:` hay `<!-- @@FILE:...@@ -->`.

## Kiến trúc và Thiết kế Thành phần

### Sơ đồ Cấu trúc Thành phần

```mermaid
flowchart TD
    subgraph SOURCE["1. Thư mục Epic Nguồn Duy nhất (.devtool/epic/<epic_dir>/)"]
        HLD["<epic_dir>.en.md (HLD)"]
        BDD["bdd_scenarios.en.md"]
        TASK_SRC["task_N_*.md (File Nguồn Duy nhất)"]
    end

    subgraph RENDER["2. Bộ máy Render & Đồng bộ Mirror (sync_task_status.py render)"]
        SYNC_BDD["Chèn Khối Gherkin Nguyên văn từ Covers: (#0009)"]
        SYNC_EMBED["Bung Khối Code từ @@FILE:path@@ (#0012)"]
        SYNC_MIRROR["Sinh .devtool/features/task_N_*.md & Viết lại Link (#0012)"]
    end

    subgraph CHECKER["3. Cổng Kiểm tra Hợp đồng & Ngữ pháp (task_contract.py + check_task_contract.py)"]
        PARSE_EV["Phân tích Evidence files: dưới .devtool/epic/<epic>/evidence/ (#0008)"]
        CHECK_ABS["Chặn Đường dẫn Tuyệt đối Cá nhân/Plugin (#0016)"]
        CHECK_R2R3["Kiểm tra Sớm R2 Mirror & R3 Verbatim BDD tại --design (#0009, #0012)"]
        CHECK_GRAMMAR["Chẩn đoán Thiếu env, Mẫu Grep & Nguồn gốc Protected Path (#0019)"]
    end

    subgraph EXEC["4. Thực thi Không cần Cài đặt (run_task_checks.py + bin/d3nexus)"]
        AUTO_ENV["Tự tính KIT_ROOT qua Path(__file__) & Tiêm D3NEXUS_KIT + PATH (#0016)"]
        GATE_EV["Xác minh File trong Evidence files Tồn tại ở Done Gate (#0008)"]
    end

    BDD --> SYNC_BDD
    TASK_SRC --> SYNC_BDD --> SYNC_EMBED --> SYNC_MIRROR
    SYNC_MIRROR --> CHECKER
    HLD --> CHECKER
    CHECKER --> EXEC
```

### 1. Hợp đồng Khai báo Evidence Files

Trong `task_contract.py` và `check_task_contract.py`:

- **Cú pháp**: Dưới mục `## Files`, một task có thể tùy chọn khai báo danh sách `Evidence files:` nằm giữa `Allowed files:` và `Read-only context:`:
  ```markdown
  ## Files

  Allowed files:
  - `src/service.py`

  Evidence files:
  - `.devtool/epic/my_epic/evidence/baseline_failures.txt` (new)
  - `.devtool/epic/my_epic/evidence/benchmark_summary.json` (new)

  Read-only context:
  - `src/constants.py`
  ```
- **Phân tích cú pháp (`parse_evidence_files(task_text) -> list[AllowedPath]`)**:
  - Sử dụng cùng định dạng gạch đầu dòng `- `<path>` (new)` như `parse_allowed_files()`.
  - Mọi đường dẫn bắt buộc phải khớp khuôn mẫu `.devtool/epic/<epic_dir>/evidence/<filename>` (cấm chứa `..`, cấm chỉ định thư mục trần, cấm trỏ ra ngoài `.devtool/epic/<epic_dir>/evidence/`).
- **Kiểm tra Grounding lúc Thiết kế (`check_task_contract.py`)**:
  - Các đường dẫn đánh dấu `(new)` trong `Evidence files:` được gộp vào tập `created` trên toàn epic để `check_grounding()` chấp nhận các tham chiếu tới chúng trong bảng `Verification` và `Read-only context:`.
  - Khi chạy với cờ `--design`, nếu một mục trong `Evidence files:` được đánh dấu `(new)` nhưng đã tồn tại sẵn trên đĩa, `check_task_contract.py` sẽ báo lỗi (giống hành vi của `Allowed files:`).
- **Xác minh tại Done Gate (`evaluate_done_gate()` trong `task_contract.py`)**:
  - Bổ sung điều kiện kiểm tra mọi đường dẫn liệt kê trong `parse_evidence_files(task_text)` phải tồn tại thực tế trên đĩa (`(layout.root / entry.pattern).is_file()`) và khác rỗng sau khi lượt chạy `verify` hoàn tất.

### 2. Soạn thảo Task Một Nguồn Duy nhất và Bộ máy Auto-Render

Trong `sync_task_status.py`:

- **Lệnh con Mới**:
  ```bash
  python3 sync_task_status.py render <epic_dir> [--source-root <worktree_or_repo_dir>]
  ```
- **Bước 2.1 — Chèn Khối BDD Nguyên văn (`#0009`)**:
  - Đọc `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` và trích xuất các khối scenario chuẩn theo mã ID (tái sử dụng thuật toán trích xuất Gherkin từ `check_epic_readiness.py`).
  - Với mỗi file `.devtool/epic/<epic_dir>/task_*.md`, đọc dòng `Covers:`. Nếu `Covers:` có liệt kê các mã scenario (`SC-...`), tìm khối Gherkin trong mục BDD của task (hoặc thẻ giữ chỗ `<!-- @@BDD_COVERS@@ -->`) và thay thế bằng đúng các khối Gherkin nguyên văn từ `bdd_scenarios.en.md` theo đúng thứ tự liệt kê trong `Covers:`.
  - Dừng và trả về mã thoát 1 nếu bất kỳ mã ID nào trong `Covers:` không tồn tại trong `bdd_scenarios.en.md`.
- **Bước 2.2 — Nhúng Nội dung File đã Kiểm chứng (`#0012`)**:
  - Quét thân bài task tìm các chỉ thị có dạng `<!-- @@FILE:<relative_path>@@ -->` nằm ngay trước một khối code fence.
  - Phân giải `<relative_path>` tương đối theo `--source-root` (mặc định là thư mục gốc của repo). Từ chối mọi đường dẫn chứa `..` hoặc bắt đầu bằng `/`.
  - Thay thế phần ruột của khối code fence bằng nội dung chính xác của file nguồn, đồng thời tự động nâng rào ngoài lên 4 dấu backtick (```` ````<lang> ````) nếu nội dung file nhúng có chứa 3 dấu backtick.
- **Bước 2.3 — Sinh Bản Mirror và Viết lại Liên kết (`#0012`)**:
  - Ghi nội dung đã render trở lại `.devtool/epic/<epic_dir>/task_*.md`.
  - Sinh bản mirror tương ứng trên bảng Kanban tại `.devtool/features/task_*.md` (hoặc `.devtool/features/done/task_*.md` nếu frontmatter `status` là `"done"`), tự động chuyển đổi các liên kết Markdown tương đối trỏ tới các file cùng thư mục epic (`](<file>.md)` hoặc `](./<file>.md)`) thành `](../epic/<epic_dir>/<file>.md)`.
  - Dọn dẹp các file `.devtool/features/task_*.md` mồ côi có frontmatter `epic:` trùng với `<epic_slug>` nhưng file nguồn không còn tồn tại trong `.devtool/epic/<epic_dir>/`.
- **Bước 2.4 — Dịch chuyển Kiểm tra R2 & R3 sang Trái trong `check_task_contract.py --design`**:
  - Khi bật cờ `--design` (hoặc khi có file `bdd_scenarios.en.md` đi kèm `--hld`), `check_task_contract.py` kiểm tra ngay các khối Gherkin trong task có khớp nguyên văn với `bdd_scenarios.en.md` (R3) và bản mirror `.devtool/features/<task>.md` có đồng nhất với bản gốc (R2) hay không, đồng thời in gợi ý chạy `d3nexus sync-status render <epic_dir>`.

### 3. Điểm vào CLI Khả chuyển Không cần Cài đặt (Zero-Setup)

- **CLI Mới (`bin/d3nexus`)**:
  - Script Python 3 khả chuyển (`#!/usr/bin/env python3`, `chmod +x`) đặt tại `<kit_root>/bin/d3nexus`, tự xác định `KIT_ROOT = Path(__file__).resolve().parent.parent` và điều phối các lệnh con:
    - `d3nexus check-doc [args...]` $\rightarrow$ `skills/doc_quality_check/resources/scripts/check_document.py`
    - `d3nexus check-contract [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/check_task_contract.py`
    - `d3nexus check-readiness [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/check_epic_readiness.py`
    - `d3nexus sync-status [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/sync_task_status.py`
    - `d3nexus run-checks [args...]` $\rightarrow$ `skills/dev-implementation/resources/scripts/run_task_checks.py`
- **Tự động Tiêm Môi trường Lúc Chạy Không cần Cài đặt (`#0016`)**:
  - Trong `run_task_checks.py` (`run_command()`) và `check_epic_readiness.py`, tự động tính `KIT_ROOT = Path(__file__).resolve().parents[4]` và truyền vào môi trường tiến trình con:
    - `D3NEXUS_KIT = str(KIT_ROOT)`
    - `PATH = f"{KIT_ROOT / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"`
  - Hoàn toàn không cần cài đặt thủ công khi đổi máy, đổi user hệ điều hành hay chuyển đổi profile Antigravity.
  - Ngoài ra, `scripts/resume_context.py --sync-zshrc` cũng tự động thêm `D3NEXUS_KIT` và `<kit_root>/bin` vào `~/.zshrc` để tiện gõ trực tiếp ngoài terminal.
- **Chặn Đường dẫn Tuyệt đối Cá nhân trong `check_task_contract.py` (`#0016`)**:
  - `check_task_contract.py` quét mọi dòng lệnh Verification tìm các tiền tố đường dẫn gắn với máy hoặc profile cá nhân (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`). Nếu phát hiện sẽ báo lỗi hợp đồng và hướng dẫn chuyển sang dùng `d3nexus <subcommand>` hoặc `$D3NEXUS_KIT/...`.
  - Nhận diện `d3nexus` trong `strip_wrappers()` và bộ kiểm tra file thực thi để không bao giờ cảnh báo giả `executable d3nexus not found on PATH`.

### 4. Tài liệu Quy chiếu Ngữ pháp Bảng Verification và Chẩn đoán Lỗi

- **Nâng cấp Chẩn đoán Ngữ pháp trong `check_task_contract.py` (`#0019`)**:
  1. **Phát hiện `VAR=value` thiếu `env`**: Nếu token đầu tiên của lệnh (khi chưa có `env`) khớp mẫu `^[A-Za-z_][A-Za-z0-9_]*=.*`, báo lỗi tường minh: `inline environment assignment '<token>' must be prefixed with 'env' (e.g. 'env <token> ...')`.
  2. **Loại trừ biểu thức mẫu tìm kiếm trong `command_paths()`**: Khi câu lệnh gọi `grep`, `egrep`, `fgrep`, `rg`, `sed`, hoặc `awk`, bỏ qua tham số biểu thức tìm kiếm (token đứng ngay sau `-e` / `--regexp`, hoặc tham số vị trí đầu tiên không phải cờ khi không dùng `-e` / `-f`) khỏi bước trích xuất đường dẫn file để các mẫu tìm kiếm có chứa dấu `/` không bị báo lỗi nhầm là thiếu file.
  3. **Hiển thị Nguồn gốc Implicit Protected Paths**: Khi `check_task_contract.py` in dòng `Implicit protected paths:`, hiển thị kèm tên task và mã dòng Verification đã kích hoạt đường dẫn đó (ví dụ: `scripts/verify.sh (task_1:V2)`).
- **Tài liệu Quy chiếu Ngữ pháp Tập trung (`skills/dev-designer/references/verification-row-grammar.md`)**:
  - Tài liệu hóa đầy đủ quy tắc tách ô bảng, quy tắc tự unescape `\|` thành `|` trước khi chạy, cách dùng `env VAR=value`, `d3nexus` / `$D3NEXUS_KIT`, `Evidence files:`, implicit protected paths, và cách dùng rào 4 dấu backtick cho các bước thực thi có chứa khối code lồng bên trong.
- **Đồng bộ Quy tắc với Reviewer (`skills/principal-review/SKILL.md`)**:
  - Ghi rõ trong hướng dẫn của `principal-review` rằng ký tự `\|` trong ô bảng Markdown được `task_contract.py` tự động unescape thành `|` trước khi truyền cho shell, loại bỏ hoàn toàn lỗi bắt nhầm (false positive).

## Xử lý Lỗi và Các Trường hợp Biên

- **Mã Scenario trong `Covers:` Không Tồn tại**: `sync_task_status.py render` dừng ngay với thông báo chỉ rõ tên file task và mã scenario bị thiếu mà không làm hỏng file trên đĩa.
- **Đường dẫn Chứa `..` trong `Evidence files:` hoặc `<!-- @@FILE:...@@ -->`**: Mọi đường dẫn chứa `..`, bắt đầu bằng `/` hoặc trỏ ra ngoài phạm vi cho phép đều bị từ chối với `ContractError` / `UsageError` và mã thoát khác 0.
- **Task Không Có `Covers:` (`Covers: none`)**: `sync_task_status.py render` bỏ qua bước chèn Gherkin BDD nhưng vẫn thực hiện nhúng `@@FILE:...@@` và sinh bản mirror `.devtool/features/`.
- **Các Epic Cũ**: Các epic không khai báo `Evidence files:` hoặc `<!-- @@FILE:...@@ -->` tiếp tục vượt qua mọi bài kiểm tra mà không bị ảnh hưởng.

## Chiến lược Kiểm thử và Xác minh

- **Tier A (Unit Tests)**:
  - `test_check_task_contract.py`: Kiểm thử phân tích `Evidence files:`, grounding cho đường dẫn evidence `(new)`, chặn đường dẫn tuyệt đối `/Users/...` và `.claude/plugins/cache/...`, chẩn đoán `VAR=val` thiếu `env`, bỏ qua mẫu `grep`/`rg` có chứa dấu `/`, và kiểm tra sớm R2/R3.
  - `test_sync_task_status.py`: Kiểm thử lệnh con `render` cho việc chèn BDD nguyên văn từ `bdd_scenarios.en.md`, nhúng code `<!-- @@FILE:...@@ -->` (bao gồm tự động nâng lên 4 dấu backtick), viết lại liên kết tương đối trong `.devtool/features/`, và dọn dẹp mirror mồ côi.
  - `test_run_task_checks.py`: Kiểm thử việc tự động tiêm `D3NEXUS_KIT` và `PATH` khi chạy dòng Verification cũng như kiểm tra sự tồn tại của `Evidence files:` tại Done Gate.
- **Tier C1 (Subcutaneous End-to-End Integration)**:
  - Kiểm thử tích hợp đầu-cuối trên một git repo tạm có đủ HLD, `bdd_scenarios.en.md`, và file nguồn `.devtool/epic/<epic>/task_1.md`; chạy lần lượt `bin/d3nexus sync-status render`, `bin/d3nexus check-contract --design`, và `bin/d3nexus run-checks verify` (bên trong có dòng lệnh gọi `d3nexus check-doc` và sinh file trong `Evidence files:`), xác nhận Done Gate trả về PASS.
- **Cổng Chất lượng Kho mã nguồn**:
  - `scripts/verify.sh` và `python-quality-check` (`ruff check`, `mypy`, `pytest`) phải vượt qua với 0 lỗi.

## Cảnh báo Shared Contract

- Không tồn tại thư mục `shared-contracts/` trong `ai-agent-tools` (kho mã nguồn này là bộ công cụ workflow plugin, không phải dịch vụ tiêu thụ hợp đồng domain của `D3Nexus`). Không có API contract, cấu trúc bản tin hay schema cơ sở dữ liệu dùng chung nào bị ảnh hưởng.

## Ánh xạ Phụ thuộc và Bối cảnh Lộ trình

- **Mở đường cho các Epic tiếp theo**:
  - **Epic 2 (`execution_and_verification_infrastructure`)**: Sử dụng trực tiếp `Evidence files:` (`#0008`), `bin/d3nexus` (`#0016`), và `sync_task_status.py render` (`#0012`) để lưu trữ tập baseline lỗi (`.devtool/epic/<epic>/evidence/baseline_failures.txt`) và bằng chứng đo lường (`#0007`, `#0017`).
  - **Epic 3 (`multi_epic_orchestration_and_governance`)**: Kế thừa và mở rộng `check_task_contract.py` cùng `sync_task_status.py` cho bài toán phụ thuộc liên epic (`#0013`, `#0014`) và đóng gói lại epic (`#0015`).

# Epic: Hợp đồng Task và Tối ưu Soạn thảo (Task Contract and Authoring Ergonomics)

## Mục lục

- [Thông tin Chung](#thông-tin-chung)
- [Bối cảnh](#bối-cảnh)
- [Mục tiêu và Phi mục tiêu](#mục-tiêu-và-phi-mục-tiêu)
- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
  - [Kiến trúc Tổng thể](#kiến-trúc-tổng-thể)
  - [Các Ca Sử dụng (Use Cases)](#các-ca-sử-dụng-use-cases)
  - [Sơ đồ Tuần tự (Sequence Diagram)](#sơ-đồ-tuần-tự-sequence-diagram)
  - [Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-ranh-giới)
  - [Kịch bản Kiểm thử BDD Toàn diện](#kịch-bản-kiểm-thử-bdd-toàn-diện)
- [Môi trường Xác minh](#môi-trường-xác-minh)
- [Tác động Shared Contract](#tác-động-shared-contract)
- [Chiến lược Triển khai và Giảm thiểu Rủi ro](#chiến-lược-triển-khai-và-giảm-thiểu-rủi-ro)
- [Phân rã Kanban Tasks](#phân-rã-kanban-tasks)

## Thông tin Chung

- **Tên Epic**: `contract_and_authoring_ergonomics`
- **Epic Slug**: `contract-and-authoring-ergonomics`
- **Trạng thái**: Packaged
- **Phiên bản Mục tiêu**: v1.25.0
- **Nền tảng**: Python
- **Tài liệu Spec Nguồn**: [2026-11-06-contract-and-authoring-ergonomics-design.vi.md](./2026-11-06-contract-and-authoring-ergonomics-design.vi.md)

## Bối cảnh

Trong quá trình đóng gói và thực thi nhiều epic trên các kho mã nguồn vệ tinh (`lyrics-sync`), 5 điểm nghẽn lặp đi lặp lại trong khâu soạn thảo và kiểm tra hợp đồng task đã được ghi nhận tại `skill-observations/observation-log/`:
- **Observation #0008**: Các dòng Verification và `Read-only context:` không thể tham chiếu tới file bằng chứng do task tạo ra dưới `.devtool/epic/<epic_dir>/evidence/` vì `.devtool/` bị cấm đưa vào `Allowed files:` trong khi `check_task_contract.py` từ chối mọi đường dẫn chưa tồn tại nếu không được đánh dấu `(new)`.
- **Observation #0009**: `check_epic_readiness.py` (Rule R3) yêu cầu khối Gherkin trong task phải khớp nguyên văn với `bdd_scenarios.en.md`, nhưng `dev-designer` lại hướng dẫn viết tóm tắt scenario và `check_task_contract.py --design` không kiểm tra R3 sớm.
- **Observation #0012**: Mỗi file task phải duy trì ở 2 nơi (`.devtool/epic/<epic_dir>/task_*.md` và `.devtool/features/task_*.md`), đồng thời các đoạn code mẫu nhúng trong task bị trôi lệch so với bản đã kiểm chứng.
- **Observation #0016**: Bảng Verification gọi các script của kit (`check_document.py`) bằng đường dẫn tuyệt đối gắn với máy hoặc profile cá nhân (`/Users/.../antigravity_homes/...`), làm hỏng tính khả chuyển khi đổi máy, đổi tài khoản hoặc nâng bản cập nhật plugin.
- **Observation #0019**: Bảng Verification có nhiều bẫy ngữ pháp ngầm (unescape `\|` gây báo lỗi giả khi `principal-review`, viết `VAR=val` thiếu `env` bị hiểu nhầm là tên file thực thi, biểu thức grep chứa `/` bị coi là đường dẫn file bị thiếu, và không rõ nguồn gốc của implicit protected paths).

## Mục tiêu và Phi mục tiêu

### Mục tiêu

- Bổ sung tiểu mục `Evidence files:` dưới `## Files` trong `task_*.md` hỗ trợ đánh dấu `(new)` cho các đường dẫn `.devtool/epic/<epic_dir>/evidence/*`, được kiểm tra ở cả pha `--design` và tại cổng hoàn tất Done Gate (`#0008`).
- Xác lập `.devtool/epic/<epic_dir>/task_*.md` làm nguồn sự thật duy nhất (Single Source of Truth) và thêm lệnh `sync_task_status.py render <epic_dir> [--source-root <dir>]` để tự động chèn khối Gherkin nguyên văn từ `bdd_scenarios.en.md` (`#0009`), bung nội dung file từ chỉ thị `<!-- @@FILE:path@@ -->`, và sinh bản mirror `.devtool/features/task_*.md` với liên kết tương đối được viết lại tự động (`#0012`).
- Đưa kiểm tra R2 (đồng bộ mirror) và R3 (khớp BDD nguyên văn) vào chạy sớm ngay trong `check_task_contract.py --design` (`#0009`, `#0012`).
- Cung cấp CLI khả chuyển `bin/d3nexus` và tự động tiêm `D3NEXUS_KIT=<kit_root>` cùng `PATH="<kit_root>/bin:$PATH"` ngay lúc chạy bên trong `run_task_checks.py` và `check_epic_readiness.py` (`#0016`).
- Chặn mọi đường dẫn tuyệt đối gắn với máy hoặc profile cá nhân trong bảng Verification khi chạy `check_task_contract.py` (`#0016`).
- Nâng cấp thông báo chẩn đoán ngữ pháp của `check_task_contract.py` (`env VAR=value`, loại trừ mẫu tìm kiếm grep khỏi kiểm tra đường dẫn, hiển thị nguồn gốc implicit protected paths) và tài liệu hóa chuẩn mực tại `skills/dev-designer/references/verification-row-grammar.md` cùng `skills/principal-review/SKILL.md` (`#0019`).

### Phi mục tiêu

- Không thay đổi cấu trúc bảng Markdown 5 cột (`| ID | Phase | Command | Expect | Needs |`) của mục `## Verification`.
- Không sửa đổi quy trình khởi tạo extras cho worktree, script baseline hồi quy hay lịch trình phụ thuộc liên epic (thuộc phạm vi của Epic 2 và Epic 3).
- Không làm gãy tính tương thích ngược đối với các epic cũ hoặc đang chạy mà không khai báo `Evidence files:` hay `<!-- @@FILE:...@@ -->`.

## Kiến trúc và Thiết kế Kỹ thuật

### Kiến trúc Tổng thể

```mermaid
flowchart TD
    subgraph SOURCE["1. Thư mục Epic Nguồn Duy nhất (.devtool/epic/<epic_dir>/)"]
        HLD["<epic_dir>.en.md (HLD)"]
        BDD["bdd_scenarios.en.md"]
        TASK_SRC["task_N_*.md (File Nguồn Duy nhất)"]
    end

    subgraph RENDER["2. Bộ máy Render & Đồng bộ Mirror (sync_task_status.py render)"]
        SYNC_BDD["Chèn Khối Gherkin Nguyên văn từ Covers: (#0009)"]
        SYNC_EMBED["Bung Khối Code từ @@FILE:path@@ (#0012)"]
        SYNC_MIRROR["Sinh .devtool/features/task_N_*.md & Viết lại Link (#0012)"]
    end

    subgraph CHECKER["3. Cổng Kiểm tra Hợp đồng & Ngữ pháp (task_contract.py + check_task_contract.py)"]
        PARSE_EV["Phân tích Evidence files: dưới .devtool/epic/<epic>/evidence/ (#0008)"]
        CHECK_ABS["Chặn Đường dẫn Tuyệt đối Cá nhân/Plugin (#0016)"]
        CHECK_R2R3["Kiểm tra Sớm R2 Mirror & R3 Verbatim BDD tại --design (#0009, #0012)"]
        CHECK_GRAMMAR["Chẩn đoán Thiếu env, Mẫu Grep & Nguồn gốc Protected Path (#0019)"]
    end

    subgraph EXEC["4. Thực thi Không cần Cài đặt (run_task_checks.py + bin/d3nexus)"]
        AUTO_ENV["Tự tính KIT_ROOT qua Path(__file__) & Tiêm D3NEXUS_KIT + PATH (#0016)"]
        GATE_EV["Xác minh File trong Evidence files Tồn tại ở Done Gate (#0008)"]
    end

    BDD --> SYNC_BDD
    TASK_SRC --> SYNC_BDD --> SYNC_EMBED --> SYNC_MIRROR
    SYNC_MIRROR --> CHECKER
    HLD --> CHECKER
    CHECKER --> EXEC
```

### Các Ca Sử dụng (Use Cases)

```mermaid
flowchart LR
    DESIGNER["AI Assistant / Designer"] --> UC1["Soạn thảo Task Một Nguồn trong .devtool/epic/<epic>/"]
    DESIGNER --> UC2["Chạy d3nexus sync-status render để Đồng bộ BDD & Mirror"]
    DESIGNER --> UC3["Kiểm tra Hợp đồng, Evidence Paths & Ngữ pháp qua check-contract --design"]

    PROGRAMMER["AI Programmer"] --> UC4["Chạy Bảng Verification với CLI d3nexus Zero-Setup"]
    PROGRAMMER --> UC5["Sinh File Evidence được Xác minh tại Task Done Gate"]
```

### Sơ đồ Tuần tự (Sequence Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Designer as AI Assistant (dev-designer)
    participant Render as sync_task_status.py render
    participant Contract as check_task_contract.py --design
    actor Programmer as AI Programmer (dev-implementation)
    participant Runner as run_task_checks.py
    participant CLI as bin/d3nexus

    Designer->>Render: Gọi render <epic_dir> [--source-root <dir>]
    Render->>Render: Đọc bdd_scenarios.en.md & chèn Gherkin nguyên văn theo Covers:
    Render->>Render: Bung các khối code <!-- @@FILE:path@@ -->
    Render->>Render: Ghi .devtool/features/task_*.md kèm viết lại relative links
    Render-->>Designer: Thoát 0 (đã render N tasks và mirrors)
    Designer->>Contract: Gọi check_task_contract.py --design
    Contract->>Contract: Kiểm tra Evidence files:, R2 mirror parity, R3 verbatim BDD
    Contract->>Contract: Kiểm tra đường dẫn khả chuyển (cấm /Users/...) & ngữ pháp
    Contract-->>Designer: Result: 0 problems — PASS
    Programmer->>Runner: Gọi run_task_checks.py verify <task_mirror>
    Runner->>Runner: Tiêm D3NEXUS_KIT & PATH=<kit_root>/bin
    Runner->>CLI: Thực thi dòng lệnh `d3nexus check-doc ...`
    CLI-->>Runner: Thoát 0
    Runner->>Runner: evaluate_done_gate() kiểm tra Evidence files tồn tại trên đĩa
    Runner-->>Programmer: Done gate PASS
```

### Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới

```text
Integration test roots: tests/, skills/dev-implementation/resources/scripts/
Protected paths: .agents/quality/**, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md
Integration results: python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml -> build/test-results/pytest.xml
```

| Ranh giới Tích hợp | Chiến lược Kiểm thử | Mục tiêu Xác minh |
| :--- | :--- | :--- |
| `task_contract.py` & `check_task_contract.py` | Kiểm thử unit và subcutaneous CLI trên git repo tạm | Xác minh phân tích `Evidence files:`, grounding `(new)`, kiểm tra tồn tại file tại Done Gate, báo lỗi `VAR=val` thiếu `env`, loại trừ mẫu grep, và kiểm tra sớm R2/R3 |
| `sync_task_status.py render` | Kiểm thử render trên hệ thống file thực giữa `.devtool/epic/<epic>/` và `.devtool/features/` | Xác minh chèn Gherkin nguyên văn từ `bdd_scenarios.en.md`, nhúng `@@FILE:path@@` kèm tự nâng lên 4 backticks, viết lại relative link, và xóa mirror mồ côi |
| `bin/d3nexus` & `run_task_checks.py` | Kiểm thử thực thi tiến trình con trên git repo tạm | Xác minh tự động tiêm `D3NEXUS_KIT` và `PATH`, điều phối lệnh con `d3nexus`, và từ chối đường dẫn cứng `/Users/...` hoặc plugin cache |
| Tài liệu Reviewer & Authoring | Kiểm tra lint và hợp đồng tài liệu qua `check_document.py` | Xác minh tính đồng bộ của `verification-row-grammar.md`, `dev-designer/SKILL.md` và `principal-review/SKILL.md` |

## Môi trường Xác minh

- Môi trường thực thi: Máy cục bộ macOS / Linux CLI cài đặt Python 3.11+, Git, `pytest`, `ruff` và `mypy`.
- Không phụ thuộc mạng hay cơ sở dữ liệu bên ngoài: Toàn bộ bài kiểm thử chạy trên các kho Git cục bộ tạm thời tạo bằng `tempfile.TemporaryDirectory` / `tmp_path`.
- Cô lập hệ thống tệp: Các lượt chạy kiểm thử không bao giờ làm thay đổi trạng thái `.devtool/` hoặc cây thư mục làm việc của kho mã nguồn chính.

### Kịch bản Kiểm thử BDD Toàn diện

Bộ kịch bản bao phủ đầy đủ 5 chiều dưới tiền tố `[TCAE-]`:
1. **Happy Paths (`TCAE-HP-01` .. `TCAE-HP-04`)**: Khai báo và xác minh `Evidence files:` đánh dấu `(new)`, render BDD nguyên văn và bản mirror `.devtool/features/` từ một nguồn duy nhất, chạy lệnh `d3nexus` qua cơ chế tự tiêm biến môi trường, và kiểm tra ngữ pháp bảng Verification với `\|` và `env VAR=val`.
2. **Edge Cases (`TCAE-EC-01` .. `TCAE-EC-03`)**: Task không có kịch bản (`Covers: none`), file nhúng có chứa 3 dấu backtick được tự động bọc bằng rào ngoài 4 dấu backtick, và biểu thức tìm kiếm `grep`/`rg`/`sed` chứa dấu `/` không bị báo lỗi nhầm là thiếu file.
3. **State Transitions (`TCAE-ST-01` .. `TCAE-ST-02`)**: Dọn dẹp mirror mồ côi và đồng bộ vị trí `done/` khi chạy `render`, cùng chuyển đổi trạng thái Done Gate từ FAIL (khi thiếu file trong `Evidence files:`) sang PASS (sau khi lệnh verification tạo đủ file).
4. **Async & Concurrency (`TCAE-AR-01` .. `TCAE-AR-02`)**: Cô lập biến môi trường `D3NEXUS_KIT` / `PATH` giữa các worktree song song và đảm bảo tính tất định khi render nhiều task trên nhiều worktree.
5. **Failures & Resilience (`TCAE-FR-01` .. `TCAE-FR-03`)**: Từ chối `Evidence files:` nằm ngoài `.devtool/epic/<epic>/evidence/` hoặc chứa `..`, từ chối đường dẫn cứng `/Users/...` hay `.claude/plugins/cache/...` và phép gán `VAR=val` thiếu `env`, đồng thời dừng `render` an toàn khi `Covers:` chứa mã scenario không tồn tại.

## Tác động Shared Contract

None — tính năng khép kín trong `ai-agent-tools`.

## Chiến lược Triển khai và Giảm thiểu Rủi ro

- **Giai đoạn 1**: Mở rộng `task_contract.py` và `check_task_contract.py` hỗ trợ `Evidence files:` và kiểm tra tại Done Gate (`Task 01`).
- **Giai đoạn 2**: Hiện thực hóa `sync_task_status.py render` và đưa kiểm tra R2/R3 vào `check_task_contract.py --design` (`Task 02`).
- **Giai đoạn 3**: Bổ sung `bin/d3nexus`, tự động tiêm `D3NEXUS_KIT`/`PATH` trong `run_task_checks.py` và `check_epic_readiness.py`, và chặn đường dẫn tuyệt đối (`Task 03`).
- **Giai đoạn 4**: Bổ sung chẩn đoán ngữ pháp bảng Verification (`env VAR=val`, loại trừ mẫu grep, nguồn gốc implicit protected path) và biên soạn `verification-row-grammar.md` + cập nhật skills (`Task 04`).
- **Giai đoạn 5**: Thực thi kiểm thử tích hợp đầu-cuối (Tier C) và xác minh toàn bộ kho mã nguồn (`Task 05`).
- **Kế hoạch Rollback**: Mọi thay đổi đều tương thích ngược trên các script Python stdlib; hoàn tác commit merge của epic sẽ khôi phục nguyên trạng hành vi cũ.

## Phân rã Kanban Tasks

- [Task 01: Evidence Files Contract and Done-Gate Verification](./task_01_evidence_files_contract.md)
- [Task 02: Single-Source Task Render Engine and Shift-Left R2/R3 Checks](./task_02_single_source_render_engine.md)
- [Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection](./task_03_portable_d3nexus_cli_and_env.md)
- [Task 04: Verification Row Grammar Diagnostics and Reference Documentation](./task_04_verification_grammar_and_docs.md)
- [Task 05: End-to-End Integration and Acceptance Verification](./task_05_end_to_end_contract_acceptance.md)
# Kịch bản Kiểm thử BDD: Hợp đồng Task và Tối ưu Soạn thảo (Task Contract and Authoring Ergonomics)

## Mục lục

- [Chiều 1: Luồng Thành công Chuẩn (Happy Paths)](#chiều-1-luồng-thành-công-chuẩn-happy-paths)
- [Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)](#chiều-2-trường-hợp-biên-và-giới-hạn-edge-cases-and-boundaries)
- [Chiều 3: Chuyển đổi Trạng thái (State Transitions)](#chiều-3-chuyển-đổi-trạng-thái-state-transitions)
- [Chiều 4: Bất đồng bộ và Đồng thời (Async and Concurrency)](#chiều-4-bất-đồng-bộ-và-đồng-thời-async-and-concurrency)
- [Chiều 5: Xử lý Lỗi và Phục hồi (Failures and Resilience)](#chiều-5-xử-lý-lỗi-và-phục-hồi-failures-and-resilience)

## Chiều 1: Luồng Thành công Chuẩn (Happy Paths)

```gherkin
Scenario: [TCAE-HP-01] [Tier C - Integration] Khai báo Evidence files vượt qua kiểm tra hợp đồng thiết kế và xác minh tại Done-Gate
  Given một task khai báo ".devtool/epic/sample_epic/evidence/baseline.txt (new)" dưới mục "Evidence files:" trong "## Files"
  And một dòng Verification tham chiếu tới ".devtool/epic/sample_epic/evidence/baseline.txt"
  When check_task_contract.py chạy với cờ "--design"
  Then công cụ thoát mã 0 với 0 lỗi và ghi nhận đường dẫn evidence mới trên toàn epic
  And khi run_task_checks.py verify thực thi dòng lệnh tạo ra file ".devtool/epic/sample_epic/evidence/baseline.txt"
  Then evaluate_done_gate xác nhận file evidence tồn tại trên đĩa và vượt qua mọi điều kiện Done-Gate

Scenario: [TCAE-HP-02] [Tier C - Integration] Render task từ một nguồn duy nhất tự động chèn BDD nguyên văn, nhúng code và sinh bản mirror
  Given một file task nguồn ".devtool/epic/sample_epic/task_01_setup.md" có dòng "Covers: TCAE-HP-01" và chỉ thị "<!-- @@FILE:src/helper.py@@ -->"
  And file ".devtool/epic/sample_epic/bdd_scenarios.en.md" định nghĩa kịch bản "[TCAE-HP-01]"
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then file ".devtool/epic/sample_epic/task_01_setup.md" chứa chính xác khối Gherkin nguyên văn của "[TCAE-HP-01]" và toàn bộ nội dung của "src/helper.py"
  And bản mirror ".devtool/features/task_01_setup.md" được sinh ra với các liên kết tương đối được viết lại thành "../epic/sample_epic/"
  And lệnh "check_task_contract.py --design" thoát mã 0 mà không có bất kỳ lỗi R2 hay R3 nào

Scenario: [TCAE-HP-03] [Tier C - Integration] Thực thi CLI d3nexus không cần cài đặt (Zero-Setup) bên trong dòng Verification
  Given một dòng Verification của task gọi lệnh "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
  When lệnh "run_task_checks.py verify" thực thi task trong một kho git tạm chưa hề cấu hình sẵn biến môi trường shell
  Then "run_task_checks.py" tự động tiêm biến "D3NEXUS_KIT" và gắn "<kit_root>/bin" vào đầu "PATH"
  And lệnh "d3nexus check-doc" điều phối tới "check_document.py" và thoát mã 0

Scenario: [TCAE-HP-04] [Tier A - Unit] Ngữ pháp dòng Verification với ký tự pipe được escape, biến môi trường env và nguồn gốc implicit protected path
  Given một dòng lệnh Verification viết "env MODE=strict python3 scripts/tool.py \| grep -c ok"
  When lệnh "check_task_contract.py --design" đánh giá task
  Then "task_contract.py" tự động unescape "\|" thành "|" trong câu lệnh đã phân tích mà không báo lỗi hợp đồng
  And "check_task_contract.py" hiển thị "scripts/tool.py (task_01:V1)" trong dòng "Implicit protected paths:"
```

## Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)

```gherkin
Scenario: [TCAE-EC-01] [Tier A - Unit] Task không khai báo Evidence files hoặc không có dòng Covers vẫn tương thích ngược hoàn toàn
  Given một file task kiểu cũ không có tiểu mục "Evidence files:" và không có dòng "Covers:"
  When chạy "sync_task_status.py render" và "check_task_contract.py --design" trên epic đó
  Then "sync_task_status.py render" vẫn sinh bản mirror ".devtool/features/" mà không làm thay đổi mục BDD của task
  And "check_task_contract.py --design" thoát mã 0 với 0 lỗi

Scenario: [TCAE-EC-02] [Tier A - Unit] File nhúng chứa 3 dấu backtick tự động nâng rào ngoài lên 4 dấu backtick
  Given một file nguồn "docs/snippet.md" có chứa một khối code fence được bao bởi 3 dấu backtick
  And một file task chứa chỉ thị "<!-- @@FILE:docs/snippet.md@@ -->" ngay phía trên khối code fence 3 dấu backtick
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then khối code sau khi render trong cả file task của epic và bản mirror ".devtool/features/" đều sử dụng rào ngoài gồm 4 dấu backtick

Scenario: [TCAE-EC-03] [Tier A - Unit] Biểu thức tìm kiếm chứa dấu gạch chéo trong grep, rg, sed và awk không bị báo lỗi nhầm là thiếu file
  Given một dòng lệnh Verification viết "grep -E 'foo/bar/baz' README.md" trong đó "foo/bar/baz" không phải là file trên đĩa
  When "check_task_contract.py --design" kiểm tra các token của câu lệnh
  Then hàm "command_paths()" loại trừ biểu thức tìm kiếm "foo/bar/baz" khỏi bước kiểm tra sự tồn tại của file
  And "check_task_contract.py" thoát mã 0 mà không báo lỗi "foo/bar/baz does not exist"
```

## Chiều 3: Chuyển đổi Trạng thái (State Transitions)

```gherkin
Scenario: [TCAE-ST-01] [Tier A - Unit] Lệnh render dọn dẹp mirror mồ côi và bảo toàn vị trí trong thư mục done
  Given file ".devtool/features/task_99_obsolete.md" có frontmatter "epic: sample-epic" nhưng file gốc đã bị xóa khỏi ".devtool/epic/sample_epic/"
  And file ".devtool/epic/sample_epic/task_01_done.md" có frontmatter "status: \"done\""
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then file ".devtool/features/task_99_obsolete.md" bị xóa khỏi đĩa
  And bản mirror của "task_01_done.md" được ghi vào đúng ".devtool/features/done/task_01_done.md"

Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate chuyển từ FAIL sang PASS sau khi file trong Evidence files được tạo ra
  Given một task khai báo ".devtool/epic/sample_epic/evidence/summary.json (new)" dưới mục "Evidence files:"
  When hàm "evaluate_done_gate" chạy trước khi file ".devtool/epic/sample_epic/evidence/summary.json" được tạo trên đĩa
  Then "evaluate_done_gate" trả về lỗi điều kiện chỉ rõ thiếu file ".devtool/epic/sample_epic/evidence/summary.json"
  And khi lượt chạy verification ghi nội dung JSON khác rỗng vào ".devtool/epic/sample_epic/evidence/summary.json"
  Then "evaluate_done_gate" trả về danh sách lỗi rỗng
```

## Chiều 4: Bất đồng bộ và Đồng thời (Async and Concurrency)

```gherkin
Scenario: [TCAE-AR-01] [Tier A - Unit] Cô lập việc tiêm biến môi trường vào tiến trình con giữa các lượt chạy song song
  Given hai lượt gọi "run_task_checks.py" chạy đồng thời trên hai git worktree tạm riêng biệt
  When mỗi lượt gọi thực thi một dòng Verification in ra "$D3NEXUS_KIT" và "$(which d3nexus)"
  Then cả hai tiến trình con đều phân giải đúng đường dẫn gốc của bộ kit mà không làm biến đổi "os.environ" của tiến trình Python cha

Scenario: [TCAE-AR-02] [Tier C - Integration] Đảm bảo tính tất định và lũy đẳng khi chạy render nhiều lần liên tiếp
  Given một thư mục epic có nhiều task bao phủ nhiều kịch bản BDD và chỉ thị nhúng file
  When thực thi lệnh "sync_task_status.py render sample_epic" hai lần liên tiếp mà không có chỉnh sửa trung gian
  Then lần chạy thứ hai tạo ra các file giống hệt từng byte trong cả ".devtool/epic/sample_epic/" và ".devtool/features/"
```

## Chiều 5: Xử lý Lỗi và Phục hồi (Failures and Resilience)

```gherkin
Scenario: [TCAE-FR-01] [Tier A - Unit] Từ chối đường dẫn Evidence files nằm ngoài thư mục evidence của epic hoặc chứa ký tự leo thư mục
  Given một task liệt kê ".devtool/epic/sample_epic/../secret.txt (new)" hoặc "src/output.json (new)" dưới mục "Evidence files:"
  When "check_task_contract.py --design" đánh giá task
  Then công cụ thoát mã 1 và báo lỗi yêu cầu mọi mục trong "Evidence files:" phải nằm dưới ".devtool/epic/<epic_dir>/evidence/" và không chứa ".."

Scenario: [TCAE-FR-02] [Tier A - Unit] Từ chối đường dẫn tuyệt đối chứa thư mục cá nhân hoặc plugin cache và phép gán VAR=value thiếu env
  Given một task có dòng V1 gọi "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
  And dòng V2 gọi "FOO=bar pytest tests/unit/test_sample.py::test_ok" mà không có tiền tố "env"
  When "check_task_contract.py --design" đánh giá task
  Then công cụ thoát mã 1 báo lỗi đường dẫn tuyệt đối không khả chuyển tại V1 và phép gán biến môi trường thiếu "env" tại V2

Scenario: [TCAE-FR-03] [Tier C - Integration] Lệnh render dừng an toàn khi Covers tham chiếu tới mã scenario không tồn tại hoặc thiếu file nhúng
  Given một task trong ".devtool/epic/sample_epic/" có dòng "Covers:" liệt kê "TCAE-HP-99" không tồn tại trong "bdd_scenarios.en.md"
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then công cụ thoát mã 1 chỉ rõ mã scenario không xác định "TCAE-HP-99" và giữ nguyên các file hiện có trong ".devtool/features/"
```


exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '20,50p;112,345p'; nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '137,184p;197,210p;329,359p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
    20	if str(SCRIPTS_DIR) not in sys.path:
    21	    sys.path.insert(0, str(SCRIPTS_DIR))
    22	
    23	import check_bdd_traceability as cb
    24	import run_task_checks as rtc
    25	import sync_task_status as sts
    26	import task_contract as tc
    27	
    28	LINTER_PATH = SCRIPTS_DIR.parents[2] / "doc_quality_check" / "resources" / "scripts" / "check_document.py"
    29	
    30	
    31	@dataclass(frozen=True)
    32	class Finding:
    33	    check: str     # "R1" ... "R8", "R5b", "R7b"
    34	    severity: str  # "FAIL" or "WARN"
    35	    message: str
    36	
    37	
    38	@dataclass(frozen=True)
    39	class Context:
    40	    root: Path
    41	    epic_dir: str
    42	    epic_slug: str
    43	    hld_text: str
    44	    tasks: dict[Path, str]
    45	    results: list[str]
    46	    roots: list[str]
    47	    baseline: bool = False
    48	    row_timeout: int = 600
    49	
    50	
   112	        findings.append(Finding("R1", "FAIL", f"compute_execution_order.py: {last_line}"))
   113	    else:
   114	        m_match = re.search(r"(\d+)\s+matched", res1.stdout)
   115	        if m_match:
   116	            m = int(m_match.group(1))
   117	            if m != len(ctx.tasks):
   118	                findings.append(
   119	                    Finding(
   120	                        "R1",
   121	                        "FAIL",
   122	                        f"task mirror count: {m} matched, {len(ctx.tasks)} in the epic directory",
   123	                    )
   124	                )
   125	
   126	    # 2. check_bdd_traceability.py plan
   127	    cmd2 = [
   128	        sys.executable,
   129	        str(SCRIPTS_DIR / "check_bdd_traceability.py"),
   130	        "plan",
   131	        "--scenarios",
   132	        str(epic_path / "bdd_scenarios.en.md"),
   133	        "--tasks",
   134	        *task_paths_str,
   135	    ]
   136	    res2 = subprocess.run(cmd2, check=False, cwd=ctx.root, capture_output=True, text=True)
   137	    if res2.returncode != 0:
   138	        last_line = get_last_non_empty_line(res2.stdout, res2.stderr)
   139	        findings.append(Finding("R1", "FAIL", f"check_bdd_traceability.py plan: {last_line}"))
   140	
   141	    # 3. check_task_contract.py --design
   142	    cmd3 = [
   143	        sys.executable,
   144	        str(SCRIPTS_DIR / "check_task_contract.py"),
   145	        "--design",
   146	        "--hld",
   147	        str(epic_path / f"{ctx.epic_dir}.en.md"),
   148	        "--tasks",
   149	        *task_paths_str,
   150	    ]
   151	    res3 = subprocess.run(cmd3, check=False, cwd=ctx.root, capture_output=True, text=True)
   152	    if res3.returncode != 0:
   153	        last_line = get_last_non_empty_line(res3.stdout, res3.stderr)
   154	        findings.append(Finding("R1", "FAIL", f"check_task_contract.py --design: {last_line}"))
   155	
   156	    # 4. check_document.py
   157	    bilingual_files = sorted(set(epic_path.glob("*.en.md")) | set(epic_path.glob("*.vi.md")))
   158	    if bilingual_files:
   159	        cmd_doc1 = [
   160	            sys.executable,
   161	            str(LINTER_PATH),
   162	            "--require-toc",
   163	            "--require-bilingual",
   164	            *[str(f) for f in bilingual_files],
   165	        ]
   166	        res_doc1 = subprocess.run(cmd_doc1, check=False, cwd=ctx.root, capture_output=True, text=True)
   167	        if res_doc1.returncode != 0:
   168	            last_line = get_last_non_empty_line(res_doc1.stdout, res_doc1.stderr)
   169	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   170	
   171	    handoff_file = epic_path / "handoff.md"
   172	    if handoff_file.is_file():
   173	        cmd_handoff = [
   174	            sys.executable,
   175	            str(LINTER_PATH),
   176	            "--require-toc",
   177	            str(handoff_file),
   178	        ]
   179	        res_handoff = subprocess.run(cmd_handoff, check=False, cwd=ctx.root, capture_output=True, text=True)
   180	        if res_handoff.returncode != 0:
   181	            last_line = get_last_non_empty_line(res_handoff.stdout, res_handoff.stderr)
   182	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   183	
   184	    if task_paths_str:
   185	        cmd_tasks = [
   186	            sys.executable,
   187	            str(LINTER_PATH),
   188	            *task_paths_str,
   189	        ]
   190	        res_tasks = subprocess.run(cmd_tasks, check=False, cwd=ctx.root, capture_output=True, text=True)
   191	        if res_tasks.returncode != 0:
   192	            last_line = get_last_non_empty_line(res_tasks.stdout, res_tasks.stderr)
   193	            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))
   194	
   195	    return findings
   196	
   197	
   198	def check_task_mirrors(ctx: Context) -> list[Finding]:
   199	    findings: list[Finding] = []
   200	    features_dir = ctx.root / ".devtool" / "features"
   201	    done_dir = features_dir / "done"
   202	    link_pattern = f"](../epic/{ctx.epic_dir}/"
   203	
   204	    for task_path, epic_text in ctx.tasks.items():
   205	        name = task_path.name
   206	        mirror_path = features_dir / name
   207	        if not mirror_path.is_file():
   208	            mirror_path = done_dir / name
   209	        if not mirror_path.is_file():
   210	            findings.append(Finding("R2", "FAIL", f"{name}: no mirror in .devtool/features/"))
   211	            continue
   212	
   213	        mirror_text = mirror_path.read_text(encoding="utf-8")
   214	        norm_mirror = mirror_text.replace(link_pattern, "](")
   215	
   216	        if norm_mirror != epic_text:
   217	            epic_lines = epic_text.splitlines()
   218	            mirror_lines = norm_mirror.splitlines()
   219	            max_len = max(len(epic_lines), len(mirror_lines))
   220	            diff_line_idx = -1
   221	            epic_line_content = ""
   222	            mirror_line_content = ""
   223	            for i in range(max_len):
   224	                el = epic_lines[i] if i < len(epic_lines) else ""
   225	                ml = mirror_lines[i] if i < len(mirror_lines) else ""
   226	                if el != ml:
   227	                    diff_line_idx = i + 1
   228	                    epic_line_content = el
   229	                    mirror_line_content = ml
   230	                    break
   231	            diff_msg = (
   232	                f"{name}: line {diff_line_idx}: {epic_line_content}"
   233	                if not mirror_line_content
   234	                else (
   235	                    f"{name}: line {diff_line_idx}: {epic_line_content} != {mirror_line_content}"
   236	                    if epic_line_content
   237	                    else f"{name}: line {diff_line_idx}: {mirror_line_content}"
   238	                )
   239	            )
   240	            findings.append(Finding("R2", "FAIL", diff_msg))
   241	
   242	    return findings
   243	
   244	
   245	def extract_scenario_blocks(text: str) -> dict[str, list[str]]:
   246	    blocks: dict[str, list[str]] = {}
   247	    in_gherkin = False
   248	    fence_marker: str | None = None
   249	    current_id: str | None = None
   250	    current_lines: list[str] = []
   251	
   252	    for line in text.splitlines():
   253	        fence_match = cb.FENCE.match(line)
   254	        if fence_match and fence_marker is None:
   255	            fence_marker = fence_match.group(1)
   256	            in_gherkin = fence_match.group(2).lower() == "gherkin"
   257	            if not in_gherkin and current_id is not None:
   258	                blocks[current_id] = current_lines
   259	                current_id = None
   260	                current_lines = []
   261	            continue
   262	        if (
   263	            fence_match
   264	            and fence_marker
   265	            and fence_match.group(1)[0] == fence_marker[0]
   266	            and len(fence_match.group(1)) >= len(fence_marker)
   267	            and not fence_match.group(2)
   268	        ):
   269	            fence_marker = None
   270	            in_gherkin = False
   271	            if current_id is not None:
   272	                blocks[current_id] = current_lines
   273	                current_id = None
   274	                current_lines = []
   275	            continue
   276	
   277	        if not in_gherkin:
   278	            continue
   279	
   280	        sc_match = cb.SCENARIO_LINE.match(line)
   281	        if sc_match:
   282	            if current_id is not None:
   283	                blocks[current_id] = current_lines
   284	                current_lines = []
   285	            rest = sc_match.group(1).strip()
   286	            id_match = cb.ID_SHAPE.search(rest)
   287	            if id_match:
   288	                current_id = id_match.group(0)
   289	                current_lines = [line.rstrip()]
   290	            else:
   291	                current_id = None
   292	        elif current_id is not None:
   293	            if not line.strip():
   294	                blocks[current_id] = current_lines
   295	                current_id = None
   296	                current_lines = []
   297	            else:
   298	                current_lines.append(line.rstrip())
   299	
   300	    if current_id is not None:
   301	        blocks[current_id] = current_lines
   302	
   303	    return blocks
   304	
   305	
   306	def check_bdd_scenarios(ctx: Context) -> list[Finding]:
   307	    findings: list[Finding] = []
   308	    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
   309	    bdd_en_path = epic_path / "bdd_scenarios.en.md"
   310	    if not bdd_en_path.is_file():
   311	        return findings
   312	
   313	    canonical_blocks = extract_scenario_blocks(bdd_en_path.read_text(encoding="utf-8"))
   314	
   315	    for task_path, task_text in ctx.tasks.items():
   316	        task_blocks = extract_scenario_blocks(task_text)
   317	        for sc_id, t_lines in task_blocks.items():
   318	            if sc_id in canonical_blocks and t_lines != canonical_blocks[sc_id]:
   319	                findings.append(
   320	                    Finding("R3", "FAIL", f"{task_path.name}: {sc_id} differs from bdd_scenarios.en.md")
   321	                )
   322	
   323	    bdd_vi_path = epic_path / "bdd_scenarios.vi.md"
   324	    if bdd_vi_path.is_file():
   325	        en_ids, _ = cb.scenario_ids(bdd_en_path)
   326	        vi_ids, _ = cb.scenario_ids(bdd_vi_path)
   327	        en_set = set(en_ids)
   328	        vi_set = set(vi_ids)
   329	        if en_set != vi_set:
   330	            for missing_or_extra in sorted(en_set ^ vi_set):
   331	                findings.append(
   332	                    Finding("R3", "FAIL", f"bdd_scenarios.vi.md: {missing_or_extra} missing or extra")
   333	                )
   334	
   335	    return findings
   336	
   337	
   338	def check_tier_tags(ctx: Context) -> list[Finding]:
   339	    findings: list[Finding] = []
   340	    bdd_en_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir / "bdd_scenarios.en.md"
   341	    if not bdd_en_path.is_file():
   342	        return findings
   343	
   344	    in_gherkin = False
   345	    fence_marker: str | None = None
   137	def parse_covers(text: str) -> list[str]:
   138	    found: list[str] = []
   139	    for line in text.splitlines():
   140	        match = COVERS_LINE_RE.match(line)
   141	        if match:
   142	            found.extend(ID_TOKEN_RE.findall(match.group(1)))
   143	    return found
   144	
   145	
   146	def core_sections(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
   147	    return (
   148	        section(text, "Files"),
   149	        section(text, "Verification"),
   150	        section(text, "Definition of Done"),
   151	        parse_covers(text),
   152	    )
   153	
   154	
   155	def check_task_tamper(task_path: Path | str, layout: EpicLayout) -> None:
   156	    path = Path(task_path)
   157	    features_task = layout.root / ".devtool" / "features" / path.name
   158	    if not features_task.is_file():
   159	        features_task = layout.root / ".devtool" / "features" / "done" / path.name
   160	
   161	    if not features_task.is_file():
   162	        return
   163	
   164	    active_text = features_task.read_text(encoding="utf-8")
   165	    active_core = core_sections(active_text)
   166	
   167	    mirror_text = path.read_text(encoding="utf-8")
   168	    mirror_core = core_sections(mirror_text)
   169	
   170	    if active_core != mirror_core:
   171	        raise ContractError(
   172	            f"TASK_TAMPERED_ERROR: active task '{features_task.name}' core sections altered from epic mirror"
   173	        )
   174	
   175	    head_text = committed_text(layout.root, path)
   176	    if head_text is not None:
   177	        head_core = core_sections(head_text)
   178	        if active_core != head_core or mirror_core != head_core:
   179	            raise ContractError(
   180	                f"TASK_TAMPERED_ERROR: task '{path.name}' core sections altered from HEAD"
   181	            )
   182	
   183	
   184	def utc_now() -> str:
   197	def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
   198	    """Run one row; the exit code is None when the process group had to be killed."""
   199	    process = subprocess.Popen(["bash", "-o", "pipefail", "-c", command], cwd=root, start_new_session=True,
   200	                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   201	    try:
   202	        output, _ = process.communicate(timeout=timeout)
   203	        return process.returncode, output
   204	    except subprocess.TimeoutExpired:
   205	        os.killpg(process.pid, signal.SIGKILL)
   206	        output, _ = process.communicate()
   207	        return None, output
   208	
   209	
   210	def mismatch(row: Row, code: int, text: str) -> str | None:
   329	def run(args: argparse.Namespace) -> int:
   330	    layout = epic_layout(args.task)
   331	    check_task_tamper(args.task, layout)
   332	    task_text = Path(args.task).read_text(encoding="utf-8")
   333	    rows, red_na = parse_verification(task_text)
   334	    allowed = parse_allowed_files(task_text)
   335	    if args.mode == "red":
   336	        selected = [row for row in rows if row.phase == "RED"]
   337	        if red_na is not None or not selected:
   338	            raise ContractError("task has no RED rows to run (RED: n/a or no RED row)")
   339	    else:
   340	        selected = [row for row in rows if row.phase in VERIFY_PHASES]
   341	    started = utc_now()
   342	    scenario_ids = epic_scenario_ids(layout)
   343	    records = [run_row(row, layout.root, args.timeout, scenario_ids) for row in selected]
   344	    if args.mode == "verify":
   345	        records.append(scope_row(layout, [entry.pattern for entry in allowed]))
   346	    tree, patch_id = fingerprint(layout.root)
   347	    head = git_run(layout.root, "rev-parse", "HEAD").decode().strip()
   348	    evidence = load_evidence(layout.evidence) or {"schema": 1, "task": Path(args.task).stem, "runs": {}}
   349	    evidence["runs"][args.mode] = {"head": head, "tree": tree, "patch_id": patch_id, "started": started,
   350	                                   "finished": utc_now(), "rows": records}
   351	    save_evidence(layout.evidence, evidence)
   352	    for record in records:
   353	        print(f"{record['id']} {record['phase']} {record['outcome']} {detail_of(record)}")
   354	    passed = all(record["outcome"] == "PASS" for record in records)
   355	    print(f"Result: {'PASS' if passed else 'FAIL'}")
   356	    print(f"Evidence: {layout.evidence}")
   357	    return 0 if passed else 1
   358	
   359	

exec
/bin/zsh -lc "command -v python3; command -v git; ls -l /opt/homebrew/bin/git /usr/local/bin/git /Library/Developer/CommandLineTools/usr/bin/git; nl -ba skills/dev-implementation/resources/scripts/sync_task_status.py | sed -n '18,43p;187,233p;259,310p;459,560p'; rg -n 'sync-zshrc|zshrc|def .*shell|PLUGIN_ROOT|KIT_ROOT' scripts/resume_context.py; rg -n 'render|mirror|BDD|scenario summar|gherkin|task_.*md' skills/dev-designer/SKILL.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
/opt/homebrew/bin/python3
/usr/bin/git
ls: /opt/homebrew/bin/git: No such file or directory
ls: /usr/local/bin/git: No such file or directory
-rwxr-xr-x  1 root  wheel  3838240 Oct 21 07:01 /Library/Developer/CommandLineTools/usr/bin/git
    18	list` reports. `epic` mode rewrites the Meta Data `Status` line of the Epic
    19	Overview's `.en.md` and `.vi.md` together, so the pair can never diverge.
    20	
    21	Only matched lines change; every other key and the whole document body survive
    22	byte-for-byte. Frontmatter is parsed with the same hand-rolled regex idiom as
    23	compute_execution_order.py -- deliberately no PyYAML, so this stays stdlib-only.
    24	"""
    25	import re
    26	import subprocess
    27	import sys
    28	from datetime import datetime, timezone
    29	
    30	try:
    31	    from datetime import UTC
    32	except ImportError:
    33	    UTC = timezone.utc  # type: ignore[attr-defined]
    34	from pathlib import Path
    35	
    36	sys.path.insert(0, str(Path(__file__).parent))
    37	from slug_utils import parse_frontmatter, sanitize_slug
    38	
    39	TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
    40	FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
    41	
    42	
    43	def now_iso() -> str:
   187	def sync_task(roots: list[Path], task_id: str, new_status: str) -> tuple[list[Path], list[str]]:
   188	    """Synchronize a task's status across all checkout roots."""
   189	    exp_epic = expected_epic(roots, task_id)
   190	    written: list[Path] = []
   191	    notes: list[str] = []
   192	    now = now_iso()
   193	
   194	    for root in roots:
   195	        targets = task_targets(root, task_id)
   196	        for path in targets:
   197	            file_epic = epic_of(path)
   198	            if exp_epic and file_epic and file_epic != exp_epic:
   199	                notes.append(f"Skipped {path}: belongs to epic '{file_epic}', expected '{exp_epic}'")
   200	                continue
   201	            text = path.read_text()
   202	            text = set_frontmatter_field(text, "status", new_status)
   203	            text = set_frontmatter_field(text, "modified", now)
   204	            if new_status == "done":
   205	                text = set_frontmatter_field(text, "completedAt", now)
   206	            else:
   207	                fm = parse_frontmatter(text)
   208	                if "completedAt" in fm and fm["completedAt"] != "null":
   209	                    text = set_frontmatter_field(text, "completedAt", "null")
   210	            path.write_text(text)
   211	            written.append(board_location(root, path, new_status))
   212	
   213	    return written, notes
   214	
   215	
   216	def board_location(root: Path, path: Path, status: str) -> Path:
   217	    """Move a features copy into features/done when it becomes done, and back when it leaves done.
   218	
   219	    Epic mirrors stay put. A copy already at the target is replaced by the one just written.
   220	    """
   221	    features = root / ".devtool" / "features"
   222	    if status == "done" and path.parent == features:
   223	        target = features / "done" / path.name
   224	    elif status != "done" and path.parent == features / "done":
   225	        target = features / path.name
   226	    else:
   227	        return path
   228	    target.parent.mkdir(parents=True, exist_ok=True)
   229	    path.replace(target)
   230	    return target
   231	
   232	
   233	def board_tally(roots: list[Path], epic_slug: str) -> dict[str, int]:
   259	def find_epic_slug(root: Path, epic_dir: str) -> str | None:
   260	    """Find the epic slug from the epic's HLD overview or contained tasks."""
   261	    epic_path = root / ".devtool" / "epic" / epic_dir
   262	    if not epic_path.is_dir():
   263	        return None
   264	    for ext in (".en.md", ".vi.md"):
   265	        doc = epic_path / f"{epic_dir}{ext}"
   266	        if doc.is_file():
   267	            match = re.search(r"^-\s*\*\*(?:Epic)\*\*:\s*(.+)$", doc.read_text(), re.MULTILINE)
   268	            if match:
   269	                slug = sanitize_slug(match.group(1))
   270	                if slug:
   271	                    return slug
   272	    for task_file in sorted(epic_path.glob("task_*.md")):
   273	        slug = epic_of(task_file)
   274	        if slug:
   275	            return slug
   276	    return sanitize_slug(epic_dir)
   277	
   278	
   279	def find_epic_dir_for_slug(root: Path, epic_slug: str) -> str | None:
   280	    """Find the epic directory name matching the given epic slug."""
   281	    epics_parent = root / ".devtool" / "epic"
   282	    if not epics_parent.is_dir():
   283	        return None
   284	    for sub in sorted(epics_parent.iterdir()):
   285	        if not sub.is_dir():
   286	            continue
   287	        slug = find_epic_slug(root, sub.name)
   288	        if slug == epic_slug:
   289	            return sub.name
   290	    # Fallback to name heuristic: replace hyphens with underscores
   291	    candidate = epic_slug.replace("-", "_")
   292	    if (epics_parent / candidate).is_dir():
   293	        return candidate
   294	    return None
   295	
   296	
   297	
   298	def fix_task_markdown_links(text: str, epic_dir: str) -> str:
   299	    """Rewrite task links when relocated into .devtool/epic/<epic_dir>/."""
   300	    text = re.sub(rf"\]\(\.\./epic/{re.escape(epic_dir)}/([^)]+)\)", r"](\1)", text)
   301	    text = re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
   302	    return text
   303	
   304	
   305	def fix_epic_overview_links(text: str) -> str:
   306	    """Rewrite Section 8 links in <epic_dir>.en.md / .vi.md to local task_*.md."""
   307	    return re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
   308	
   309	
   310	def archive_superpowers_docs(root: Path, epic_dir: str, epic_slug: str | None) -> list[Path]:
   459	def code_epic_dir(root: Path, task_id: str) -> str | None:
   460	    """The epic directory of this checkout's copy of the task when that epic is a code epic, else None."""
   461	    from task_contract import is_code_epic
   462	
   463	    for features in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
   464	        if (features / f"{task_id}.md").is_file():
   465	            slug = epic_of(features / f"{task_id}.md")
   466	            epic_dir = find_epic_dir_for_slug(root, slug) if slug else None
   467	            if epic_dir and is_code_epic(root / ".devtool" / "epic" / epic_dir / f"{epic_dir}.en.md"):
   468	                return epic_dir
   469	            return None
   470	    return None
   471	
   472	
   473	def done_gate_failures(task_id: str) -> list[str]:
   474	    """Messages refusing `task <id> done` for a code epic's task; empty when the gate does not apply or passes."""
   475	    from task_contract import ContractError, evaluate_done_gate, section
   476	
   477	    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], check=False, capture_output=True, text=True)
   478	    if top.returncode != 0:
   479	        return []
   480	    root = Path(top.stdout.strip())
   481	    epic_dir = code_epic_dir(root, task_id)
   482	    if epic_dir is None:
   483	        if (any(code_epic_dir(other, task_id) for other in checkout_roots() if other.resolve() != root.resolve())
   484	                and not task_targets(root, task_id)):
   485	            return ["run the done gate in the checkout that holds the task and its evidence (the epic worktree)"]
   486	        return []
   487	    mirror = root / ".devtool" / "epic" / epic_dir / f"{task_id}.md"
   488	    if not mirror.is_file() or section(mirror.read_text(encoding="utf-8"), "Verification") is None:
   489	        return [(f"retrofit required: {mirror} has no Verification section — retrofit it through "
   490	                "dev-designer's Updating an Existing Epic")]
   491	    try:
   492	        return evaluate_done_gate(mirror)
   493	    except ContractError as error:
   494	        return [f"condition 1: {error}"]
   495	
   496	
   497	def main() -> None:
   498	    import argparse
   499	    import sys
   500	
   501	    parser = argparse.ArgumentParser(
   502	        description="Mirror one epic task's Kanban status across every checkout of this repo."
   503	    )
   504	    subparsers = parser.add_subparsers(dest="command", required=True)
   505	
   506	    task_parser = subparsers.add_parser("task", help="Sync task status")
   507	    task_parser.add_argument("task_id", help="Task ID (e.g. task_1_setup)")
   508	    task_parser.add_argument("status", help=f"New status ({', '.join(TASK_STATUSES)})")
   509	
   510	    epic_parser = subparsers.add_parser("epic", help="Sync epic overview status")
   511	    epic_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
   512	    epic_parser.add_argument("status", help="New status string (e.g. 'In Progress')")
   513	
   514	    archive_parser = subparsers.add_parser(
   515	        "archive-epic", help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/"
   516	    )
   517	    archive_parser.add_argument("epic_dir", help="Epic directory name (e.g. logging_refactor)")
   518	
   519	    subparsers.add_parser(
   520	        "archive-done",
   521	        help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
   522	    )
   523	
   524	    args = parser.parse_args()
   525	
   526	    if args.command == "task":
   527	        if args.status not in TASK_STATUSES:
   528	            sys.stderr.write(
   529	                f"Invalid status '{args.status}'. Expected one of: {', '.join(TASK_STATUSES)}\n"
   530	            )
   531	            sys.exit(2)
   532	
   533	        failures = done_gate_failures(args.task_id) if args.status == "done" else []
   534	        if failures:
   535	            sys.stderr.write(f"refused: {args.task_id} cannot be marked done\n")
   536	            for failure in failures:
   537	                sys.stderr.write(f"  {failure}\n")
   538	            sys.exit(1)
   539	
   540	        roots = checkout_roots()
   541	        written, notes = sync_task(roots, args.task_id, args.status)
   542	        for note in notes:
   543	            sys.stderr.write(f"Note: {note}\n")
   544	
   545	        if not written:
   546	            sys.stderr.write(f"Warning: No copies of task '{args.task_id}' found in any checkout.\n")
   547	            sys.exit(1)
   548	
   549	        exp_epic = expected_epic(roots, args.task_id)
   550	        if exp_epic:
   551	            tally = board_tally(roots, exp_epic)
   552	            tally_str = ", ".join(f"{k}: {v}" for k, v in tally.items())
   553	            print(
   554	                f"Updated {len(written)} copies of {args.task_id} -> '{args.status}' "
   555	                f"[Epic '{exp_epic}': {tally_str}]"
   556	            )
   557	        else:
   558	            print(f"Updated {len(written)} copies of {args.task_id} -> '{args.status}'")
   559	
   560	    elif args.command == "epic":
936:def update_zshrc_env(zshrc_path: Path, r_home: Path, ws_root: Path) -> None:
937:    if not zshrc_path.exists():
938:        zshrc_path.write_text("", encoding="utf-8")
939:    content = zshrc_path.read_text(encoding="utf-8")
946:        zshrc_path.write_text("\n".join(lines_to_add) + "\n" + content, encoding="utf-8")
949:def update_zshrc_history_and_aliases(zshrc_path: Path) -> None:
950:    content = zshrc_path.read_text(encoding="utf-8")
971:    zshrc_path.write_text(content, encoding="utf-8")
974:def update_zshrc_sync_items(zshrc_path: Path) -> None:
975:    content = zshrc_path.read_text(encoding="utf-8")
986:    zshrc_path.write_text(content[:m.start()] + new_decl + content[m.end():], encoding="utf-8")
1019:def sync_shell_env(
1025:    zshrc_path = r_home / ".zshrc"
1028:    update_zshrc_env(zshrc_path, r_home, ws_root)
1029:    update_zshrc_history_and_aliases(zshrc_path)
1030:    update_zshrc_sync_items(zshrc_path)
1092:    parser.add_argument("--sync-zshrc", action="store_true", help="Synchronize shell environment and history")
1139:    if args.sync_zshrc:
3:description: Use when analyzing high-level requirements to design a complete software Epic across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects, including High-Level Design (HLD), Mermaid diagrams, Integration Test Plans, and Kanban task breakdowns with BDD & TDD specifications.
9:This skill transforms high-level product or technical requirements into a structured, developer-ready Epic for **Web Applications**, **Flutter**, **Android Native**, **iOS Native**, **Python**, and **Rust Core / Polyglot** projects. It creates a centralized High-Level Design (HLD) document, formalizes an **Integration Test Plan** covering analyzed use cases and boundary edge cases, and breaks the work down into granular Kanban tasks enforcing Behavior-Driven Development (BDD), Test-Driven Development (TDD), and strict Definition of Done (DoD), fully aligned with `dev-implementation`'s Tri-Persona workflow (QA Red Team + TDD Master + System Integration Engineer).
72:   - **High-Level Architecture**: Use `mermaid flowchart TD` (or `flowchart LR`) to show component interactions. NEVER use legacy `graph TD` (`graph` is legacy Mermaid syntax; `flowchart` is the modern standard that enables per-subgraph `direction` control, richer node shapes, better rendering engines, and styling).
78:   - **Markdown Lint Standards**: All generated markdown files (`.en.md`, `.vi.md`, `bdd_scenarios.*.md`, `task_*.md`) MUST strictly adhere to markdown lint rules: single H1 top-level title, no skipped heading levels, space after `#`, no trailing punctuation in headings, all code blocks tagged with language identifiers (no bare fences), and clean formatting hygiene (no trailing whitespace, no hard tabs).
96:   - **Comprehensive BDD Test Scenarios**: A detailed Gherkin suite (`Given - When - Then`) covering all Use Cases and Sequence Diagram flows across the **Mandatory 5-Dimension Boundary Matrix**:
111:7. **BDD Output in Epic Directory**:
143:Beside each proposed task, list the epic scenario identifiers it will cover (its future `Covers:` line, see Tier C — BDD Automation below), so the user approves the scenario-to-task mapping together with the split.
150:  - **`task_01` Rule**: **`task_01` MUST always be the Contract & Ledger Update task** (updating `shared-contracts/<domain>/api_contract.md`, `architecture_and_flow.md`, and logging cross-repo requirements in `gaps_and_rfcs.md`). Updating shared contracts FIRST in Stage 3 unblocks satellite repos to develop in parallel rather than serializing work behind local feature implementation.
167:  - **`task_01` Rule**: **`task_01` MUST always be the Consumer DTOs & Adapter Synchronization task** (updating satellite-internal DTOs, serializers, mock fixtures, and BDD test stubs).
178:Break the Epic down into granular implementation tasks. **Crucially, each task must be structured around Behavior-Driven Development (BDD), Test-Driven Development (TDD), and Integration Flow Testing** to feed directly into the Tri-Persona (QA Red Team + TDD Master + System Integration Engineer) execution workflow in `dev-implementation`. Wherever the task produces testable behavior, generate Markdown task files located at `.devtool/features/task_<number>_<name>.md` (and mirrored in `.devtool/epic/<epic_name>/task_<number>_<name>.md` as permanent epic outputs).
181:- **Creation**: Tasks are generated into `.devtool/features/task_<number>_<name>.md` and mirrored into `.devtool/epic/<epic_name>/task_<number>_<name>.md`.
242:##### 🔗 Tier C — BDD Automation (All Platforms)
255:        BDD["BDD Scenarios (Gherkin syntax)<br/>⚠️ Strictly Decoupled from Coding"]
287:    HLD -->|100% Independent Derivation| BDD
288:    BDD --> TAG
306:>    - All public interface contracts (`AppRoutes`, `AppEventBus`, DTOs, State/Action contracts) must be locked during Phase 1 BDD authoring.
318:Task files are English-only — do not generate a `.vi.md` variant for `task_*.md` and do not mix
320:this workflow; the spec, Epic Overview, and BDD scenario documents remain bilingual.
344:   - `Allowed files:` lists the exact paths or globs (`*`, `?`, and `**` across directories) the task may create, change or delete. A path that does not exist yet carries `(new)`. Bare directories are not allowed. Changes under `.devtool/` (task status, mirrors, evidence) are never listed, except changes to a protected path.
359:8. **BDD Scenarios & Acceptance Criteria (The QA Persona)**:
360:   Document this section under the markdown heading `### BDD SCENARIOS`.
365:   - The QA Persona MUST author BDD scenarios **completely decoupled from implementation code**.
380:   - **Zero Uncovered Scenarios Rule**: Every authored BDD scenario across all 5 dimensions MUST map to at least one automated test case. Unit tests with mocks do NOT substitute for Tier C integration tests.
381:   - **Grounded Assertions Mandate**: Under `### BDD SCENARIOS`, pin assertions to production observation points and exact inputs, outputs, boundary indices, attempt counts, timestamps, or canonical fixture anchors. Vague or weak assertions (`should be truthy`, `is valid`, `should work`, `returns non-empty`) are strictly forbidden and rejected by `check_task_contract.py --design`.
383:9. **Verification**: A `## Verification` section holding one table and nothing else to tick. Each row is a command the recorder (`run_task_checks.py`) runs and the done gate checks; nothing is ticked by hand. Per-platform example rows, and the command that produces each platform's test report, are in [`references/verification-rows.md`](references/verification-rows.md).
426:10. **Definition of Done (DoD)**: Acceptance criteria (100% BDD scenario coverage across Tier A unit and Tier C integration tests with zero uncovered scenarios, passes Tier A/B/C verification, clean git status; for Web/UI deliverables: automated integration tests pass AND live browser verification artifacts are captured via `browser_subagent`). Every bullet ends with a parenthesised reference: the Verification rows that prove it, such as `(V2, V4)`, or `(Gate 5)` for an item only the developer can judge at Kanban review. The Gate 4 report lists `(Gate 5)` items; no script marks one met.
427:11. **Dependencies & Blockers**: Link to blocking/blocked task files as markdown links, each `Blocked by` clause on one line (e.g. `Blocked by [Task 1](task_1_create_package.md)`).
436:  --tasks .devtool/epic/<epic_name>/task_*.md
446:  --tasks .devtool/epic/<epic_name>/task_*.md
449:It must exit 0 as well; fix what it names and run both checks again. Both must exit 0 before the commit. Pass the epic directory's task mirrors, never `.devtool/features/task_*.md`, which can hold other epics' tasks.
453:- If `auto_commit: true`: stage exactly the generated/modified paths (the epic's `.devtool/epic/<epic_name>/` directory and each new/modified `.devtool/features/task_*.md` file). Then commit:
472:| "A Node.js test is sufficient to prove this web UI feature works." | **REJECTED**: Node tests prove only pure data logic. 80% of web defects occur in DOM queries, event bubbling, and CSS rendering. Tier C requires headless Playwright execution with Zero-Console-And-Layout-Defect Watchdog. |

exec
/bin/zsh -lc "rg -n 'command_paths|program_of|strip_wrappers|symlink|done|mirror|check_task_tamper|except|render' skills/dev-implementation/resources/scripts/test_{check_task_contract,sync_task_status,run_task_checks,check_epic_readiness}.py | head -140; ls -ld shared-contracts; cat .agents/quality/python-quality.json; rg -n 'test_.*py|pytest|unittest|check_task_contract|check_epic_readiness|sync_task_status' scripts/verify.sh" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:22:except ImportError:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:470:    def test_prv_ec_04_mirror_drift_fails_and_location_link_passes(self) -> None:
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:472:        # Baseline ready epic already has mirror link pointing to ../epic/demo_epic/demo_epic.en.md
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:478:        # Mutate mirror in .devtool/features/task_1.md: add "Stale sentence."
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:479:        mirror_path = self.root / ".devtool" / "features" / "task_1.md"
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:480:        mirror_text = mirror_path.read_text(encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:481:        mirror_text = mirror_text.replace(
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:485:        mirror_path.write_text(mirror_text, encoding="utf-8")
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:550:        # Also mirror in bdd_scenarios.vi.md so R3 doesn't fail on missing vi ID before R1
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:621:                "- **Target Files & Symbols**:\n  - `tool.py`: `run`\n  - `src/app.py`: `build_payload()`, new `render()`",
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py:635:        self.assertFalse(any("render" in line for line in stdout.splitlines() if line.startswith("R5")), f"Render should not be mentioned in R5:\n{stdout}")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:16:    archive_all_done_epics, archive_epic_tasks, archive_superpowers_docs, board_tally, epic_of,
skills/dev-implementation/resources/scripts/test_sync_task_status.py:51:        out = set_frontmatter_field(TASK_TEXT, "status", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:68:        self.assertEqual(set_frontmatter_field(text, "status", "done"), text)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:72:        out = set_frontmatter_field(text, "status", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:188:    def test_done_moves_the_features_copy_into_done_in_every_checkout(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:191:            written, _ = sync_task(roots, "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:194:                moved = features / "done" / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:195:                mirror = root / ".devtool" / "epic" / "logging_refactor" / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:197:                self.assertIn('status: "done"', moved.read_text())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:199:                self.assertIn('status: "done"', mirror.read_text())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:201:    def test_leaving_done_moves_the_features_copy_back(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:204:            sync_task(roots, "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:208:                self.assertFalse((features / "done" / "task_1_setup.md").exists())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:211:    def test_done_replaces_a_stale_copy_already_in_done(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:215:                make_task(root / ".devtool" / "features" / "done" / "task_1_setup.md",
skills/dev-implementation/resources/scripts/test_sync_task_status.py:217:            sync_task(roots, "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:221:                self.assertIn('status: "done"', (features / "done" / "task_1_setup.md").read_text())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:240:    def test_completed_at_only_on_done(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:246:            sync_task(roots, "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:247:            text = (roots[0] / ".devtool/features/done/task_1_setup.md").read_text()
skills/dev-implementation/resources/scripts/test_sync_task_status.py:251:    def test_completed_at_resets_to_null_when_leaving_done(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:254:            sync_task(roots, "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:256:                             (roots[0] / ".devtool/features/done/task_1_setup.md").read_text())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:268:            written, notes = sync_task([root], "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:280:            written, _ = sync_task([main, Path(tmp) / "empty"], "task_1_setup", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:285:            written, notes = sync_task([Path(tmp)], "task_9_absent", "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:295:            make_task(features / "task_1_a.md", epic="logging-refactor", status="done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:296:            make_task(features / "task_2_b.md", epic="logging-refactor", status="done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:301:            self.assertEqual(counts["done"], 2)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:312:                          epic="logging-refactor", status="done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:313:            self.assertEqual(board_tally(roots, "logging-refactor")["done"], 1)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:381:            "- **Blocks**: [Task 2](../../features/task_2_b.md), [Task 3](../../features/done/task_3_c.md).\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:391:            "- [Task 2: Done](../../features/done/task_2_done.md)\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:395:        self.assertIn("- [Task 2: Done](task_2_done.md)", out)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:399:    def test_archive_done_tasks(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:410:            done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:411:            done_dir.mkdir(parents=True, exist_ok=True)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:412:            task_file = done_dir / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:414:                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n\n'
skills/dev-implementation/resources/scripts/test_sync_task_status.py:426:            self.assertTrue((done_dir / ".gitkeep").is_file())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:435:    def test_sync_epic_done_triggers_archival(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:443:                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:446:            done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:447:            done_dir.mkdir(parents=True, exist_ok=True)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:448:            task_file = done_dir / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:450:                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
skills/dev-implementation/resources/scripts/test_sync_task_status.py:457:            self.assertTrue((done_dir / ".gitkeep").is_file())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:482:            make_task(task_file, epic="logging-refactor", status="done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:486:            self.assertEqual(tally["done"], 1)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:488:    def test_archive_all_done_epics(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:496:                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:499:            done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:500:            done_dir.mkdir(parents=True, exist_ok=True)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:501:            task_file = done_dir / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:503:                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
skills/dev-implementation/resources/scripts/test_sync_task_status.py:506:            archived = archive_all_done_epics([root])
skills/dev-implementation/resources/scripts/test_sync_task_status.py:510:            self.assertTrue((done_dir / ".gitkeep").is_file())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:513:    def test_archive_all_done_epics_with_backtick_header(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:521:                "## 8. Tasks\n- [Task 1](../../features/done/task_1_setup.md)\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:524:            done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:525:            done_dir.mkdir(parents=True, exist_ok=True)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:526:            task_file = done_dir / "task_1_setup.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:528:                '---\nid: "task_1_setup"\nstatus: "done"\nepic: "logging-refactor"\n---\n'
skills/dev-implementation/resources/scripts/test_sync_task_status.py:531:            archived = archive_all_done_epics([root])
skills/dev-implementation/resources/scripts/test_sync_task_status.py:535:            self.assertTrue((done_dir / ".gitkeep").is_file())
skills/dev-implementation/resources/scripts/test_sync_task_status.py:538:    def test_archive_all_done_epics_empty(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:541:            done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:542:            done_dir.mkdir(parents=True, exist_ok=True)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:543:            (done_dir / ".gitkeep").touch()
skills/dev-implementation/resources/scripts/test_sync_task_status.py:545:            archived = archive_all_done_epics([root])
skills/dev-implementation/resources/scripts/test_sync_task_status.py:558:DONE_FEATURE = f".devtool/features/done/{TASK_ID}.md"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:579:    return text + "## Definition of Done\n\n- done (V2)\n"
skills/dev-implementation/resources/scripts/test_sync_task_status.py:622:        mirror = self.wt / MIRROR
skills/dev-implementation/resources/scripts/test_sync_task_status.py:623:        self.assertEqual(run_py(RECORDER, self.wt, "red", str(mirror)).returncode, 0)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:624:        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:625:        self.assertEqual(run_py(RECORDER, self.wt, "verify", str(mirror)).returncode, 0)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:641:    def done(self, cwd: Path) -> subprocess.CompletedProcess:
skills/dev-implementation/resources/scripts/test_sync_task_status.py:642:        return run_py(SYNC, cwd, "task", TASK_ID, "done")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:646:        self.assertIn(f"refused: {TASK_ID} cannot be marked done", result.stderr)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:652:        self.assert_refused(self.done(self.wt), *fragments)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:657:    def test_vth_hp_03_matching_evidence_reaches_done(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:662:        self.assertIn("done gate: PASS", status.stdout)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:663:        result = self.done(self.wt)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:669:            self.assertIn('status: "done"', text)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:673:    def test_vth_st_03_done_without_evidence_is_refused(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:676:                                  "run the done gate in the epic worktree")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:683:        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:684:        mirror = self.wt / MIRROR
skills/dev-implementation/resources/scripts/test_sync_task_status.py:685:        mirror.write_text(mirror.read_text(encoding="utf-8").replace(
skills/dev-implementation/resources/scripts/test_sync_task_status.py:702:        result = self.done(self.wt)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:704:        self.assertIn('status: "done"', (self.wt / DONE_FEATURE).read_text(encoding="utf-8"))
skills/dev-implementation/resources/scripts/test_sync_task_status.py:722:        result = self.done(self.main)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:723:        self.assert_refused(result, "condition 1:", "run the done gate in the epic worktree")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:726:    def test_done_from_a_checkout_lacking_the_task_is_refused(self):
skills/dev-implementation/resources/scripts/test_sync_task_status.py:731:        result = self.done(self.main)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:732:        self.assert_refused(result, "run the done gate in the checkout that holds the task and its evidence "
skills/dev-implementation/resources/scripts/test_sync_task_status.py:759:        mirror = self.wt / MIRROR
skills/dev-implementation/resources/scripts/test_sync_task_status.py:760:        self.assertEqual(run_py(RECORDER, self.wt, "red", str(mirror)).returncode, 0)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:763:        (self.wt / "feature.txt").write_text("done\n", encoding="utf-8")
skills/dev-implementation/resources/scripts/test_sync_task_status.py:764:        self.assertEqual(run_py(RECORDER, self.wt, "verify", str(mirror)).returncode, 0)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:765:        result = self.done(self.wt)
skills/dev-implementation/resources/scripts/test_sync_task_status.py:851:        """PRV-FR-05: Another epic's worktree stays byte-identical and task sync still mirrors everywhere."""
skills/dev-implementation/resources/scripts/test_run_task_checks.py:35:            f"## Verification\n\n{head}{rows}\n{after_table}\n## Definition of Done\n\n- done (V1)\n")
skills/dev-implementation/resources/scripts/test_run_task_checks.py:79:            except SystemExit as exit_:
skills/dev-implementation/resources/scripts/test_run_task_checks.py:166:    def test_program_of_unwraps_and_requires_a_tracked_file(self) -> None:
skills/dev-implementation/resources/scripts/test_run_task_checks.py:184:                self.assertEqual(tc.program_of(command, self.root), expected)
skills/dev-implementation/resources/scripts/test_run_task_checks.py:195:        with self.assertRaisesRegex(tc.ContractError, "pass the task's mirror under"):
skills/dev-implementation/resources/scripts/test_run_task_checks.py:329:    def test_program_of_a_sibling_task_row_is_protected(self) -> None:
skills/dev-implementation/resources/scripts/test_run_task_checks.py:475:    def test_mirror_outside_the_epic_directory_exits_two(self) -> None:
skills/dev-implementation/resources/scripts/test_run_task_checks.py:480:        self.assertIn("pass the task's mirror under", err)
skills/dev-implementation/resources/scripts/test_run_task_checks.py:490:        self.assertIn("done gate: FAIL", out)
skills/dev-implementation/resources/scripts/test_run_task_checks.py:497:        self.assertIn("done gate: PASS", out)
skills/dev-implementation/resources/scripts/test_check_task_contract.py:33:DONE_LINE = "- done (V1)\n"
skills/dev-implementation/resources/scripts/test_check_task_contract.py:43:        dod = f"- done ({', '.join(non_v1)})\n" if non_v1 else "- done (Gate 5)\n"
skills/dev-implementation/resources/scripts/test_check_task_contract.py:93:            except SystemExit as exit_:
skills/dev-implementation/resources/scripts/test_check_task_contract.py:122:        task = self.task("1_a", dod="- done and\n  wrapped (V1, V2).\n- by hand (Gate 5)\n")
skills/dev-implementation/resources/scripts/test_check_task_contract.py:141:            dod="- done (V2, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:159:    def test_vth_ec_01_without_design_a_done_task_is_not_grounded_and_new_is_not_checked(self) -> None:
skills/dev-implementation/resources/scripts/test_check_task_contract.py:160:        done = self.broken_task(status="done")
skills/dev-implementation/resources/scripts/test_check_task_contract.py:162:        code, out, _ = self.run_cli("--hld", f"{EPIC}/demo.en.md", "--tasks", done)
skills/dev-implementation/resources/scripts/test_check_task_contract.py:183:    def test_vth_ec_02_a_definition_of_done_item_with_no_command_is_rejected(self) -> None:
skills/dev-implementation/resources/scripts/test_check_task_contract.py:284:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:304:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:341:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:356:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:371:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:383:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:395:                         dod="- done (V2, V3, V4, V5)\n",
skills/dev-implementation/resources/scripts/test_check_task_contract.py:409:                         dod="- done (V2, V3, V4, V5)\n",
ls: shared-contracts: No such file or directory
{
  "schema_version": 1,
  "capabilities": {
    "format": ["ruff", "format", "--check", "skills/web-quality-check", "tests", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
    "lint": ["ruff", "check", "skills/web-quality-check", "tests", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
    "type_check": ["mypy", "skills/web-quality-check/resources/scripts/validate_web_quality.py", "skills/web-quality-check/resources/scripts/run_playwright_harness.py", "skills/quality_check/resources/scripts/verify_polyglot_registry.py", "skills/web-quality-check/resources/scripts/check_vanilla_js.py", "skills/dev-implementation/resources/scripts/generate_smoke_checklist.py"],
    "test": ["python3", "-m", "pytest", "tests"],
    "architecture": ["bash", "scripts/verify.sh"]
  },
  "profiles": {
    "pr": ["lint", "test"],
    "epic": ["format", "lint", "type_check", "test", "architecture"],
    "release": ["format", "lint", "type_check", "test", "architecture"],
    "scheduled": ["format", "lint", "type_check", "test", "architecture"]
  }
}
246:python3 -m unittest skills/doc_quality_check/resources/scripts/test_check_document.py || FAILED=1
247:python3 scripts/test_lifecycle_document_contract.py || FAILED=1
248:python3 -m unittest scripts/test_lifecycle_signals.py || FAILED=1
249:python3 -m unittest skills/dev-implementation/resources/scripts/test_audit_epic.py || FAILED=1
250:python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py || FAILED=1
251:python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py || FAILED=1
252:python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py || FAILED=1
253:python3 -m unittest skills/dev-implementation/resources/scripts/test_result_reports.py || FAILED=1
254:python3 -m unittest skills/dev-implementation/resources/scripts/test_run_external_review.py || FAILED=1
255:python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py || FAILED=1
256:python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py || FAILED=1
257:python3 -m unittest skills/dev-implementation/resources/scripts/test_sync_task_status.py || FAILED=1
258:python3 -m unittest scripts/test_run_unittest_junit.py || FAILED=1
259:python3 -m unittest scripts/test_verifiable_handoff_text.py || FAILED=1
260:python3 -m unittest scripts/test_verifiable_handoff.py || FAILED=1
264:python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py || FAILED=1
268:python3 -m unittest skills/quality_check/resources/scripts/test_validate_quality_contract.py || FAILED=1
269:python3 -m unittest skills/quality_check/resources/scripts/test_aggregate_quality_results.py || FAILED=1
270:python3 -m unittest skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py || FAILED=1
271:python3 -m unittest skills/python-quality-check/resources/scripts/test_validate_python_quality.py || FAILED=1
272:python3 -m unittest skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py || FAILED=1
273:python3 -m unittest skills/android-quality-check/resources/scripts/test_validate_android_quality.py || FAILED=1
274:python3 -m unittest skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py || FAILED=1
275:python3 -m unittest skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py || FAILED=1
276:python3 -m unittest skills/quality_check/resources/scripts/test_quality_provider_acceptance.py || FAILED=1
280:python3 -m unittest skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py || FAILED=1
281:python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py || FAILED=1
285:python3 -m unittest scripts/test_resume_context.py || FAILED=1
289:python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py || FAILED=1

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/test_check_task_contract.py | sed -n '1,210p'; nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '65,200p'; nl -ba skills/dev-implementation/resources/scripts/test_run_task_checks.py | sed -n '1,32p;166,200p;380,420p'; nl -ba scripts/test_lifecycle_document_contract.py | sed -n '1,180p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Tests for check_task_contract.py.
     3	
     4	Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_task_contract.py
     5	"""
     6	from __future__ import annotations
     7	import contextlib
     8	import io
     9	import json
    10	import os
    11	import re
    12	import subprocess
    13	import sys
    14	import tempfile
    15	import unittest
    16	from pathlib import Path
    17	from typing import Any
    18	
    19	sys.path.insert(0, str(Path(__file__).parent))
    20	from check_task_contract import main
    21	
    22	EPIC = ".devtool/epic/demo"
    23	HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
    24	RED = "| V1 | RED | `python3 tool.py red` | exit 1 | — |\n"
    25	GREEN = "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |\n"
    26	TIER_B = ("| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
    27	          "| V4 | TIER-B | `mypy --strict tool.py` | exit 0 | — |\n")
    28	TIER_C = "| V5 | TIER-C | `python3 tool.py int --out=build/out.xml` | exit 0; results build/out.xml | — |\n"
    29	DEFAULT_ROWS = RED + GREEN + TIER_B + TIER_C
    30	VERIFICATION_ENV = "## 6. Verification Environment\n\nTests run in temporary directories. Variable: DEMO_TOKEN.\n"
    31	HLD = ("# Epic\n\n## Integration Test Plan\n\nProtected paths: scripts/verify.sh\n\n"
    32	       "Integration results: python3 tool.py all -> build/all.xml\n\n" + VERIFICATION_ENV)
    33	DONE_LINE = "- done (V1)\n"
    34	
    35	
    36	def task_text(rows: str = DEFAULT_ROWS, allowed: str = "- `tool.py`", dod: str | None = None,
    37	              covers: str = "", status: str = "todo", read_only: str = "- `README.md` — note",
    38	              after_table: str = "", skip: str = "", decisions: str = "- Grounded design decision.\n") -> str:
    39	    if dod is None:
    40	        row_ids = [m.group(1) for m in re.finditer(r"^\|\s*([^|]+?)\s*\|\s*[^|]+\s*\|", rows, re.MULTILINE)
    41	                   if m.group(1) not in ("ID", "") and not m.group(1).startswith("-")]
    42	        non_v1 = [r for r in row_ids if r != "V1"]
    43	        dod = f"- done ({', '.join(non_v1)})\n" if non_v1 else "- done (Gate 5)\n"
    44	    sections = {
    45	        "Files": f"Allowed files:\n{allowed}\n\nRead-only context:\n{read_only}\n",
    46	        "Verification": f"{HEAD}{rows}\n{after_table}",
    47	        "Definition of Done": dod,
    48	        "Stop and Report If": "- A command does not match.\n",
    49	        "Decisions Already Made": decisions,
    50	    }
    51	    body = "".join(f"## {title}\n\n{text}\n" for title, text in sections.items() if title != skip)
    52	    return f'---\nstatus: "{status}"\n---\n# Task\n\n{covers}\n{body}'
    53	
    54	
    55	def git(root: Path, *args: str) -> None:
    56	    subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=True)
    57	
    58	
    59	class ContractCase(unittest.TestCase):
    60	    def setUp(self) -> None:
    61	        directory = tempfile.TemporaryDirectory()
    62	        self.addCleanup(directory.cleanup)
    63	        self.root = Path(directory.name).resolve()
    64	        git(self.root, "init", "-q")
    65	        git(self.root, "config", "user.email", "demo@example.com")
    66	        git(self.root, "config", "user.name", "Demo")
    67	        self.write(".gitignore", "build/\n")
    68	        self.write("tool.py", "print('x')\n")
    69	        self.write("README.md", "demo\n")
    70	        self.write(f"{EPIC}/demo.en.md", HLD)
    71	        self.previous = Path.cwd()
    72	        os.chdir(self.root)
    73	        self.addCleanup(os.chdir, self.previous)
    74	
    75	    def write(self, relative: str, text: str) -> Path:
    76	        path = self.root / relative
    77	        path.parent.mkdir(parents=True, exist_ok=True)
    78	        path.write_text(text, encoding="utf-8")
    79	        return path
    80	
    81	    def commit(self) -> None:
    82	        git(self.root, "add", "-A")
    83	        git(self.root, "commit", "-q", "-m", "base")
    84	
    85	    def task(self, name: str, **kwargs: Any) -> Path:
    86	        return self.write(f"{EPIC}/task_{name}.md", task_text(**kwargs))
    87	
    88	    def run_cli(self, *argv: str | Path) -> tuple[int, str, str]:
    89	        out, err = io.StringIO(), io.StringIO()
    90	        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    91	            try:
    92	                code = main([str(arg) for arg in argv])
    93	            except SystemExit as exit_:
    94	                code = int(exit_.code) if exit_.code is not None else 0
    95	        return code, out.getvalue(), err.getvalue()
    96	
    97	    def check(self, *tasks: Path, design: bool = False) -> tuple[int, str, str]:
    98	        self.commit()
    99	        flags = ["--design"] if design else []
   100	        return self.run_cli(*flags, "--hld", f"{EPIC}/demo.en.md", "--tasks", *tasks)
   101	
   102	
   103	class CompliantEpicTest(ContractCase):
   104	    def test_vth_hp_01_a_compliant_epic_passes_and_prints_implicit_protected_paths(self) -> None:
   105	        first = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
   106	        second = self.task("2_b", allowed="- `README.md`", covers="Covers: DEMO-HP-01",
   107	                           rows=RED + GREEN + TIER_B + TIER_C.replace("tool.py int", "tool.py src/made.py"))
   108	        code, out, _ = self.check(first, second, design=True)
   109	        self.assertEqual(code, 0, out)
   110	        self.assertIn("Implicit protected paths: tool.py", out)
   111	        self.assertIn("Result: 0 problems — PASS", out)
   112	
   113	    def test_no_tracked_program_prints_none(self) -> None:
   114	        task = self.task("1_a", allowed="- `README.md`",
   115	                         rows=RED.replace("python3 tool.py red", "echo red") + GREEN.replace(
   116	            "python3 tool.py green", "echo green") + TIER_C.replace("python3 tool.py", "echo"))
   117	        code, out, _ = self.check(task)
   118	        self.assertEqual(code, 0, out)
   119	        self.assertIn("Implicit protected paths: none", out)
   120	
   121	    def test_wrapped_dod_bullet_and_trailing_period_pass(self) -> None:
   122	        task = self.task("1_a", dod="- done and\n  wrapped (V1, V2).\n- by hand (Gate 5)\n")
   123	        code, out, _ = self.check(task)
   124	        self.assertEqual(code, 0, out)
   125	
   126	    def test_missing_executable_warns_without_failing(self) -> None:
   127	        task = self.task("1_a", rows=RED + GREEN.replace("python3 tool.py green", "nosuch-demo-tool run") + TIER_B + TIER_C)
   128	        code, out, err = self.check(task)
   129	        self.assertEqual(code, 0, out)
   130	        self.assertIn("task_1_a:V2", err)
   131	        self.assertIn("nosuch-demo-tool", err)
   132	
   133	
   134	class GroundingTest(ContractCase):
   135	    def broken_task(self, status: str = "todo") -> Path:
   136	        self.write("loose.py", "x = 1\n")
   137	        return self.task(
   138	            "1_a", status=status, allowed="- `loose.py`\n- `README.md` (new)\n- `docs/*.md`\n- `src/`\n"
   139	                                          "- `deep/er/est/x.py` (new)",
   140	            read_only="- `docs/nope.md` — gone",
   141	            dod="- done (V2, V5)\n",
   142	            rows=RED + GREEN.replace("tool.py green", "tool.py src/nowhere.py --out=src/also_gone.txt") + TIER_C)
   143	
   144	    def test_vth_ec_01_paths_that_do_not_match_the_repository_are_named(self) -> None:
   145	        self.commit()
   146	        task = self.broken_task()
   147	        code, out, _ = self.run_cli("--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", task)
   148	        self.assertEqual(code, 1)
   149	        for expected in ("task_1_a:Files: loose.py is not tracked by git",
   150	                         "task_1_a:Files: README.md is marked (new) but already exists",
   151	                         "task_1_a:Files: docs/*.md matches no tracked file",
   152	                         "task_1_a:Files: src/ is a directory; list files or a glob",
   153	                         "task_1_a:Files: deep/er/est/x.py (new) has no parent or grandparent directory",
   154	                         "task_1_a:Files: Read-only context docs/nope.md does not exist",
   155	                         "task_1_a:V2: src/nowhere.py does not exist, is not ignored by git and is not (new) in any task",
   156	                         "task_1_a:V2: src/also_gone.txt does not exist"):
   157	            self.assertIn(expected, out)
   158	
   159	    def test_vth_ec_01_without_design_a_done_task_is_not_grounded_and_new_is_not_checked(self) -> None:
   160	        done = self.broken_task(status="done")
   161	        self.commit()
   162	        code, out, _ = self.run_cli("--hld", f"{EPIC}/demo.en.md", "--tasks", done)
   163	        self.assertEqual(code, 0, out)
   164	        live = self.task("2_b", allowed="- `README.md` (new)\n- `tool.py`")
   165	        code, out, _ = self.check(live)
   166	        self.assertEqual(code, 0, out)
   167	        self.assertNotIn("already exists", out)
   168	
   169	    def test_read_only_context_may_name_a_path_another_task_creates(self) -> None:
   170	        owner = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
   171	        reader = self.task("2_b", read_only="- `src/made.py` — built by task 1\n- `README.md` — note")
   172	        code, out, _ = self.check(owner, reader)
   173	        self.assertEqual(code, 0, out)
   174	
   175	    def test_command_token_is_new_in_another_task(self) -> None:
   176	        owner = self.task("1_a", allowed="- `tool.py`\n- `src/made.py` (new)")
   177	        user = self.task("2_b", rows=DEFAULT_ROWS.replace("tool.py green", "tool.py src/made.py"))
   178	        code, out, _ = self.check(owner, user, design=True)
   179	        self.assertEqual(code, 0, out)
   180	
   181	
   182	class StructureTest(ContractCase):
   183	    def test_vth_ec_02_a_definition_of_done_item_with_no_command_is_rejected(self) -> None:
   184	        task = self.task("1_a", dod="- Works for users.\n- Names a missing row (V9)\n- Fine (V2)\n")
   185	        code, out, _ = self.check(task)
   186	        self.assertEqual(code, 1)
   187	        self.assertIn("task_1_a:Definition of Done: Works for users. ends with no (V<n>) or (Gate 5) reference", out)
   188	        self.assertIn("task_1_a:Definition of Done: Names a missing row (V9) references V9, which the table lacks", out)
   189	        self.assertNotIn("Fine", out)
   190	
   191	    def test_vth_ec_03_a_malformed_verification_table_is_rejected_row_by_row(self) -> None:
   192	        rows = (RED + "| V1 | GREEN | `python3 tool.py a` | exit 0 | — |\n"
   193	                "| V2 | LATER | `python3 tool.py b` | exit 0 | — |\n"
   194	                "| V3 | GREEN | `python3 tool.py c` | passes | — |\n"
   195	                "| V4 | GREEN | `python3 tool.py d` | exit 0; results build/d.xml | — |\n")
   196	        bad = self.task("1_bad", rows=rows)
   197	        no_red = self.task("2_nored", rows=GREEN + TIER_C)
   198	        no_reason = self.task("3_noreason", rows=GREEN + TIER_C, after_table="RED: n/a —\n")
   199	        uncovered = self.task("4_cov", covers="Covers: DEMO-HP-01", rows=RED + GREEN)
   200	        code, out, _ = self.check(bad, no_red, no_reason, uncovered)
   201	        self.assertEqual(code, 1)
   202	        for expected in ("task_1_bad:V1: duplicate ID",
   203	                         "task_1_bad:V2: Phase must be one of",
   204	                         "task_1_bad:V3: Expect must start with",
   205	                         "task_1_bad:V4: results is allowed only on TIER-C rows",
   206	                         "task_2_nored:Verification: no RED row and no RED: n/a line with a reason",
   207	                         "task_3_noreason:Verification: no RED row and no RED: n/a line with a reason",
   208	                         "task_4_cov:Verification: Covers line but no TIER-C row with results"):
   209	            self.assertIn(expected, out)
   210	
    65	
    66	- [Meta Data](#meta-data)
    67	- [Overview](#overview)
    68	
    69	## Meta Data
    70	
    71	- **Status**: Approved (Gate 1)
    72	
    73	## Overview
    74	
    75	Approved spec overview text.
    76	"""
    77	    spec_vi = """# Demo Epic Design
    78	
    79	## Table of Contents
    80	
    81	- [Meta Data](#meta-data)
    82	- [Overview](#overview)
    83	
    84	## Meta Data
    85	
    86	- **Status**: Approved (Gate 1)
    87	
    88	## Overview
    89	
    90	Nội dung tổng quan thiết kế đã được phê duyệt.
    91	"""
    92	    (epic_dir / "2026-10-22-demo-epic-design.en.md").write_text(spec_en, encoding="utf-8")
    93	    (epic_dir / "2026-10-22-demo-epic-design.vi.md").write_text(spec_vi, encoding="utf-8")
    94	
    95	    # 2. HLD pair
    96	    hld_en = """# Demo Epic High-Level Design
    97	
    98	## Table of Contents
    99	
   100	- [Meta Data](#meta-data)
   101	- [Integration Test Plan](#integration-test-plan)
   102	- [Verification Environment](#verification-environment)
   103	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
   104	
   105	## Meta Data
   106	
   107	- **Epic name**: demo_epic
   108	- **Status**: Planned
   109	
   110	## Integration Test Plan
   111	
   112	Protected paths: scripts/verify.sh
   113	
   114	Integration test roots: tests/
   115	
   116	Integration results: python3 tool.py int -> build/test-results/int.xml
   117	
   118	## Verification Environment
   119	
   120	Tests run in temporary directories.
   121	
   122	## Kanban Tasks Breakdown
   123	
   124	1. [Task 1](task_1.md)
   125	2. [Task 2](task_2.md)
   126	"""
   127	    hld_vi = """# Demo Epic High-Level Design
   128	
   129	## Table of Contents
   130	
   131	- [Meta Data](#meta-data)
   132	- [Integration Test Plan](#integration-test-plan)
   133	- [Verification Environment](#verification-environment)
   134	- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)
   135	
   136	## Meta Data
   137	
   138	- **Epic name**: demo_epic
   139	- **Status**: Planned
   140	
   141	## Integration Test Plan
   142	
   143	Protected paths: scripts/verify.sh
   144	
   145	Integration test roots: tests/
   146	
   147	Integration results: python3 tool.py int -> build/test-results/int.xml
   148	
   149	## Verification Environment
   150	
   151	Các bài kiểm tra chạy trong thư mục tạm.
   152	
   153	## Kanban Tasks Breakdown
   154	
   155	1. [Task 1](task_1.md)
   156	2. [Task 2](task_2.md)
   157	"""
   158	    (epic_dir / "demo_epic.en.md").write_text(hld_en, encoding="utf-8")
   159	    (epic_dir / "demo_epic.vi.md").write_text(hld_vi, encoding="utf-8")
   160	
   161	    # 3. BDD Scenarios pair
   162	    bdd_en = """# Demo Epic BDD Scenarios
   163	
   164	## Table of Contents
   165	
   166	- [Coverage Matrix](#coverage-matrix)
   167	- [Scenarios](#scenarios)
   168	
   169	## Coverage Matrix
   170	
   171	| Scenario ID | Dimension | Target Component | Description |
   172	|---|---|---|---|
   173	| `[DEMO-HP-01]` | Happy Path | `tool.py` | Unit scenario description |
   174	| `[DEMO-HP-02]` | Happy Path | `tool.py` | Integration scenario description |
   175	
   176	## Scenarios
   177	
   178	### DEMO-HP-01: Unit scenario description
   179	
   180	```gherkin
   181	Scenario: [DEMO-HP-01] [Tier A - Unit] Unit scenario description
   182	  Given something
   183	  When something happens
   184	  Then it passes
   185	```
   186	
   187	### DEMO-HP-02: Integration scenario description
   188	
   189	```gherkin
   190	Scenario: [DEMO-HP-02] [Tier C - Integration] Integration scenario description
   191	  Given something
   192	  When integration happens
   193	  Then it passes
   194	```
   195	"""
   196	    bdd_vi = """# Demo Epic BDD Scenarios
   197	
   198	## Table of Contents
   199	
   200	- [Coverage Matrix](#coverage-matrix)
     1	#!/usr/bin/env python3
     2	"""Tests for task_contract.py and run_task_checks.py.
     3	
     4	Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_run_task_checks.py
     5	"""
     6	from __future__ import annotations
     7	import contextlib
     8	import importlib
     9	import io
    10	import json
    11	import os
    12	import subprocess
    13	import sys
    14	import tempfile
    15	import unittest
    16	from pathlib import Path
    17	from typing import Any
    18	from unittest import mock
    19	
    20	sys.path.insert(0, str(Path(__file__).parent))
    21	tc: Any = importlib.import_module("task_contract")
    22	
    23	from run_task_checks import main
    24	
    25	TABLE_HEAD = "| ID | Phase | Command | Expect | Needs |\n|----|-------|---------|--------|-------|\n"
    26	EPIC = ".devtool/epic/demo"
    27	TASK = f"{EPIC}/task_1_demo.md"
    28	EVIDENCE = f"{EPIC}/evidence/task_1_demo.json"
    29	TICKS = "`" * 3
    30	
    31	
    32	def task_text(rows: str, allowed: str = "- `feature.txt` (new)", after_table: str = "",
   166	    def test_program_of_unwraps_and_requires_a_tracked_file(self) -> None:
   167	        self.write("tools/check.py", "")
   168	        self.write("run.sh", "")
   169	        self.commit()
   170	        cases = {
   171	            "python3 tools/check.py --x": "tools/check.py",
   172	            "uv run python3 tools/check.py": "tools/check.py",
   173	            "env A=1 B=2 bash ./run.sh && echo hi": "run.sh",
   174	            "./run.sh | cat": "run.sh",
   175	            "python3 -m unittest tools/check.py": None,
   176	            "python3 -c 'print(1)'": None,
   177	            "python3 -u tools/check.py": "tools/check.py",
   178	            "python3 missing.py": None,
   179	            "echo hi": None,
   180	            "": None,
   181	        }
   182	        for command, expected in cases.items():
   183	            with self.subTest(command=command):
   184	                self.assertEqual(tc.program_of(command, self.root), expected)
   185	
   186	    def test_epic_layout(self) -> None:
   187	        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n")
   188	        layout = tc.epic_layout(task)
   189	        self.assertEqual(layout.root, self.root)
   190	        self.assertEqual(layout.epic_dir, self.root / EPIC)
   191	        self.assertEqual(layout.hld, self.root / EPIC / "demo.en.md")
   192	        self.assertEqual(layout.scenarios, self.root / EPIC / "bdd_scenarios.en.md")
   193	        self.assertEqual(layout.evidence, self.root / EVIDENCE)
   194	        features = self.write(".devtool/features/task_1_demo.md", "x")
   195	        with self.assertRaisesRegex(tc.ContractError, "pass the task's mirror under"):
   196	            tc.epic_layout(features)
   197	
   198	    def test_fingerprint_sees_untracked_files_and_leaves_the_index_alone(self) -> None:
   199	        self.write("a.txt", "one\n")
   200	        self.commit()
   380	        self.write("stale/old.xml", "<testsuite><testcase name='test_demo_hp_01_old'/></testsuite>")
   381	        for old in ("out/old.xml", "stale/old.xml"):
   382	            os.utime(self.root / old, (1_000_000, 1_000_000))
   383	        rows = ("| V1 | TIER-C | `echo \"<testsuite><testcase name='other'/></testsuite>\" > out/new.xml` "
   384	                "| exit 0; results out | — |\n"
   385	                "| V2 | TIER-C | `true` | exit 0; results stale | — |\n")
   386	        task = self.epic(rows, allowed="- `out/**`")
   387	        self.write(f"{EPIC}/bdd_scenarios.en.md", f"{TICKS}gherkin\nScenario: [DEMO-HP-01] One\n{TICKS}\n")
   388	        self.assertEqual(self.run_cli("verify", task)[0], 1)
   389	        by_id = self.run_rows()
   390	        self.assertEqual(by_id["V1"]["outcome"], "PASS")
   391	        self.assertEqual(by_id["V1"]["results"]["digest"]["cases"], [])
   392	        self.assertEqual((by_id["V2"]["outcome"], by_id["V2"]["reason"]), ("FAIL", "results not produced by this run"))
   393	
   394	    def test_scope_reads_hld_protection_from_head(self) -> None:
   395	        self.write("scripts/verify.sh", "echo ok\n")
   396	        task = self.epic("| V1 | GREEN | `true` | exit 0 | — |\n", protected="scripts/verify.sh",
   397	                         allowed="- `scripts/**`")
   398	        self.write(f"{EPIC}/demo.en.md", hld_text())  # the task drops its own protection
   399	        self.write("scripts/verify.sh", "echo weakened\n")
   400	        self.assertEqual(self.run_cli("verify", task)[0], 1)
   401	        self.assertEqual(self.run_rows()["SCOPE"]["violations"],
   402	                         ["protected path not named exactly in Allowed files: scripts/verify.sh"])
   403	
   404	    def test_scope_reads_task_rows_from_head_and_new_task_files_from_the_tree(self) -> None:
   405	        self.write("tools/grade.py", "print(1)\n")
   406	        self.write("tools/other.py", "print(1)\n")
   407	        task = self.epic("| V1 | GREEN | `python3 tools/grade.py` | exit 0 | — |\n", allowed="- `tools/**`")
   408	        self.write(TASK, task_text("| V1 | GREEN | `true` | exit 0 | — |\n", allowed="- `tools/**`"))
   409	        self.write(f"{EPIC}/task_2_new.md", task_text("| V1 | GREEN | `python3 tools/other.py` | exit 0 | — |\n"))
   410	        self.write("tools/grade.py", "print(2)\n")
   411	        self.write("tools/other.py", "print(2)\n")
   412	        self.assertEqual(self.run_cli("verify", task)[0], 1)
   413	        self.assertEqual(self.run_rows()["SCOPE"]["violations"],
   414	                         ["protected path not named exactly in Allowed files: tools/grade.py",
   415	                          "protected path not named exactly in Allowed files: tools/other.py"])
   416	
   417	    def test_missing_results_path_is_not_fresh(self) -> None:
   418	        task = self.epic("| V1 | TIER-C | `true` | exit 0; results nowhere.xml | — |\n")
   419	        self.assertEqual(self.run_cli("verify", task)[0], 1)
   420	        self.assertEqual(self.run_rows()["V1"]["reason"], "results not produced by this run")
     1	#!/usr/bin/env python3
     2	"""Verify that every lifecycle document producer exposes the shared contract."""
     3	
     4	from __future__ import annotations
     5	
     6	import pathlib
     7	import re
     8	import unittest
     9	
    10	ROOT = pathlib.Path(__file__).resolve().parents[1]
    11	
    12	EXPECTED: dict[str, tuple[str, ...]] = {
    13	    "skills/dev-brainstorming/SKILL.md": (
    14	        "YYYY-MM-DD-<topic>-design.en.md",
    15	        "YYYY-MM-DD-<topic>-design.vi.md",
    16	        "--require-toc",
    17	        "--require-bilingual",
    18	        "## Shared Contract Warnings",
    19	        "## Cảnh báo Shared Contract",
    20	        "check and warn only",
    21	        "Silence is never consent",
    22	    ),
    23	    "skills/doc-brainstorming/SKILL.md": (
    24	        "YYYY-MM-DD-<topic>-design.en.md",
    25	        "YYYY-MM-DD-<topic>-design.vi.md",
    26	        "--require-toc",
    27	        "--require-bilingual",
    28	    ),
    29	    "skills/dev-designer/SKILL.md": (
    30	        "<epic_name>.en.md",
    31	        "<epic_name>.vi.md",
    32	        "bdd_scenarios.en.md",
    33	        "bdd_scenarios.vi.md",
    34	        "--require-toc",
    35	        "--require-bilingual",
    36	        "Task files are English-only",
    37	        "check_bdd_traceability.py plan",
    38	        "Covers:",
    39	        "Integration test roots:",
    40	        "at least one automated integration test",
    41	        "Handoff Choice",
    42	        "`tests/integration/` and `tests/e2e/` (Python)",  # LF-HP-03
    43	        "exact node ID",
    44	        "should be truthy",
    45	        "returns non-empty",
    46	        "must not be empty or write `None`",
    47	        "## Shared Contract Warnings",
    48	        "task_01",
    49	        ".agents/contract_sync.json",
    50	        ".agents/contract_map.json",
    51	    ),
    52	    "skills/setup-shared-contracts/SKILL.md": (
    53	        "contract_map.json.tmpl",
    54	    ),
    55	    "skills/sync-shared-contracts/SKILL.md": (
    56	        "diff-check",
    57	    ),
    58	    "skills/writing-plans/SKILL.md": (
    59	        "YYYY-MM-DD-<feature-name>.en.md",
    60	        "YYYY-MM-DD-<feature-name>.vi.md",
    61	        "--require-toc",
    62	        "--require-bilingual",
    63	    ),
    64	    "skills/doc-designer/SKILL.md": (
    65	        "<doc_dir>.en.md",
    66	        "<doc_dir>.vi.md",
    67	        "--require-toc",
    68	        "--require-bilingual",
    69	    ),
    70	    "skills/doc-implementation/SKILL.md": (
    71	        "--require-toc",
    72	        "--require-bilingual",
    73	    ),
    74	    "skills/doc_quality_check/SKILL.md": (
    75	        "--require-toc",
    76	        "--require-bilingual",
    77	    ),
    78	    "skills/doc_quality_check/references/document-reviewer-prompt.md": (
    79	        "English document",
    80	        "Vietnamese document",
    81	        "Translation parity",
    82	    ),
    83	    "skills/dev-implementation/SKILL.md": (
    84	        '`profile`: `"epic"`',
    85	        '`repository_sha`',
    86	        "aggregated verdict of **PASS**",
    87	        "check_bdd_traceability.py tests",
    88	        "--ids",
    89	        "Entry-Point Detection",
    90	        "Resume Procedure",
    91	        "handoff.md",
    92	        "space- or comma-separated values",  # LF-HP-04
    93	        "re-enters at Phase 2 step 2",  # LF-ST-04
    94	        "may ride along in that commit",  # LF-ST-06
    95	    ),
    96	    "skills/dev-lifecycle/SKILL.md": (
    97	        'profile `epic`',
    98	        "`repository_sha`",
    99	        "FAIL > BLOCKED > PASS",
   100	        "check_bdd_traceability.py tests",
   101	        "Granting Gate 4 without a passing traceability check",
   102	        "Handoff Choice",
   103	        "handoff-template.md",
   104	        "Resuming an Epic",
   105	        "Packaged",
   106	        "a fresh traceability check and epic quality run",  # LF-ST-05
   107	        "`<N>` is the task count the preflight printed",  # LF-HP-05
   108	        "check_epic_readiness.py <epic_dir>",
   109	        "Principal Review Choice",
   110	        "references/principal-review.md",
   111	    ),
   112	    "skills/dev-lifecycle/references/handoff-template.md": (
   113	        "or `uncommitted` when `auto_commit` is false",  # LF-FR-04
   114	        "Execution Guardrails for Receiving LLM",
   115	        "Bounded context protocol",
   116	        "Strict spec fidelity",
   117	        "Zero test fakery",
   118	        "No contract repair by the executor",
   119	        "Apply the Execution Guardrails for Receiving LLM before presenting Gate 3",
   120	    ),
   121	    "skills/pr_review/SKILL.md": (
   122	        '"profile": "pr"',
   123	        '"base_ref"',
   124	        "Executive Report Format",
   125	    ),
   126	    "skills/principal-review/SKILL.md": (
   127	        "name: principal-review",
   128	        "Two Modes of Operation",
   129	        "In-Lifecycle Mode",
   130	        "Ad-Hoc Mode",
   131	        "--kind principal",
   132	        "references/principal-review-prompt.md",
   133	        "references/principal-review-rules.md",
   134	        "references/document-triage.md",
   135	    ),
   136	    "skills/cross-model-review/SKILL.md": (
   137	        "name: cross-model-review",
   138	        "Two Modes of Operation",
   139	        "In-Lifecycle Mode",
   140	        "Ad-Hoc Mode",
   141	        "Clean Working Tree",
   142	        "references/review-triage.md",
   143	        "references/local-review-setup.md",
   144	    ),
   145	}
   146	
   147	FORBIDDEN: dict[str, tuple[str, ...]] = {
   148	    "skills/pr_review/SKILL.md": (
   149	        "melos test",
   150	        "./gradlew check",
   151	        "swift test",
   152	        "cleanup-java",
   153	    ),
   154	}
   155	
   156	
   157	class LifecycleDocumentContractTest(unittest.TestCase):
   158	    def test_mvls_hp_06_dev_designer_and_handoff_guardrails(self) -> None:
   159	        """[MVLS-HP-06] dev-designer retains Decisions Already Made contracts, exact node IDs, weak assertion ban, and handoff-template retains 4 guardrails."""
   160	        designer_path = ROOT / "skills/dev-designer/SKILL.md"
   161	        designer_text = designer_path.read_text(encoding="utf-8")
   162	        self.assertIn("exact node ID", designer_text)
   163	        self.assertIn("Decisions Already Made", designer_text)
   164	        self.assertIn("should be truthy", designer_text)
   165	        self.assertIn("returns non-empty", designer_text)
   166	
   167	        handoff_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
   168	        handoff_text = handoff_path.read_text(encoding="utf-8")
   169	        self.assertIn("Execution Guardrails for Receiving LLM", handoff_text)
   170	        self.assertIn("bounded context", handoff_text.lower())
   171	        self.assertIn("strict spec fidelity", handoff_text.lower())
   172	        self.assertIn("zero test fakery", handoff_text.lower())
   173	        self.assertIn("no contract repair", handoff_text.lower())
   174	        self.assertIn("Apply the Execution Guardrails for Receiving LLM before presenting Gate 3", handoff_text)
   175	
   176	    def test_cdg_hp_04_contract_diff_gate_lifecycle_docs(self) -> None:
   177	        """[CDG-HP-04] Lifecycle document contracts enforce read-only brainstorming warnings, designer contract ordering, and diff-check template/CLI references."""
   178	        brainstorming_text = (ROOT / "skills/dev-brainstorming/SKILL.md").read_text(encoding="utf-8")
   179	        self.assertIn("## Shared Contract Warnings", brainstorming_text)
   180	        self.assertIn("## Cảnh báo Shared Contract", brainstorming_text)

exec
/bin/zsh -lc "rg -n 'features/task|epic.*task|scenario|summar|mirror|Covers|render' skills/dev-designer/references/{task-template.md,workflow.md} scripts/test_lifecycle_document_contract.py scripts/test_verifiable_handoff*.py scripts/verifiable_handoff.py 2>/dev/null; nl -ba scripts/resume_context.py | sed -n '936,950p;1019,1045p'; nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '65,155p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
scripts/test_verifiable_handoff.py:87:- the demo scenario passes (V3)
scripts/test_verifiable_handoff.py:99:Covers: DEMO-HP-01
scripts/test_verifiable_handoff.py:117:            f"{EPIC}/bdd_scenarios.en.md": SCENARIOS,
scripts/test_verifiable_handoff.py:138:        mirror = f"{EPIC}/{TASK}.md"
scripts/test_verifiable_handoff.py:139:        self.step("check_task_contract.py", "--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", mirror)
scripts/test_verifiable_handoff.py:140:        self.step("check_bdd_traceability.py", "plan", "--scenarios", f"{EPIC}/bdd_scenarios.en.md",
scripts/test_verifiable_handoff.py:141:                  "--tasks", mirror)
scripts/test_verifiable_handoff.py:142:        self.step("run_task_checks.py", "red", mirror)
scripts/test_verifiable_handoff.py:144:        self.step("run_task_checks.py", "verify", mirror)
scripts/test_lifecycle_document_contract.py:32:        "bdd_scenarios.en.md",
scripts/test_lifecycle_document_contract.py:33:        "bdd_scenarios.vi.md",
scripts/test_lifecycle_document_contract.py:38:        "Covers:",
scripts/test_lifecycle_document_contract.py:354:            "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks",
   936	def update_zshrc_env(zshrc_path: Path, r_home: Path, ws_root: Path) -> None:
   937	    if not zshrc_path.exists():
   938	        zshrc_path.write_text("", encoding="utf-8")
   939	    content = zshrc_path.read_text(encoding="utf-8")
   940	    lines_to_add: list[str] = []
   941	    if "REAL_HOME" not in content:
   942	        lines_to_add.append(f'export REAL_HOME="{r_home}"')
   943	    if "WORKSPACE_ROOT" not in content:
   944	        lines_to_add.append(f'export WORKSPACE_ROOT="{ws_root}"')
   945	    if lines_to_add:
   946	        zshrc_path.write_text("\n".join(lines_to_add) + "\n" + content, encoding="utf-8")
   947	
   948	
   949	def update_zshrc_history_and_aliases(zshrc_path: Path) -> None:
   950	    content = zshrc_path.read_text(encoding="utf-8")
  1019	def sync_shell_env(
  1020	    real_home: Path | None = None,
  1021	    workspace_root: Path | None = None,
  1022	) -> dict[str, object]:
  1023	    r_home = real_home or Path("/Users/danhdueexoictif")
  1024	    ws_root = workspace_root or Path("/Users/danhdueexoictif/AllProjects")
  1025	    zshrc_path = r_home / ".zshrc"
  1026	    main_hist = r_home / ".zsh_history"
  1027	
  1028	    update_zshrc_env(zshrc_path, r_home, ws_root)
  1029	    update_zshrc_history_and_aliases(zshrc_path)
  1030	    update_zshrc_sync_items(zshrc_path)
  1031	
  1032	    projects_link = r_home / "Projects"
  1033	    if not projects_link.exists() and not projects_link.is_symlink():
  1034	        projects_link.symlink_to(ws_root)
  1035	
  1036	    if not main_hist.exists():
  1037	        main_hist.write_text("", encoding="utf-8")
  1038	    main_text = main_hist.read_text(encoding="utf-8", errors="replace")
  1039	    seen_cmds = {l.strip() for l in main_text.splitlines() if l.strip()}
  1040	
  1041	    synced_profiles: list[str] = []
  1042	    profiles_dir = r_home / "antigravity_homes"
  1043	    if profiles_dir.exists():
  1044	        for prof in sorted(profiles_dir.iterdir()):
  1045	            if prof.is_dir():
    65	        tag = LEADING_TAG.match(match.group(1).strip())
    66	        if not tag:
    67	            problems.append(f"{path}:{number}: scenario has no identifier")
    68	        elif not ID_SHAPE.fullmatch(tag.group(1)):
    69	            problems.append(f"{path}:{number}: malformed identifier [{tag.group(1)}]")
    70	        elif tag.group(1) in ids:
    71	            problems.append(f"{path}:{number}: duplicate identifier {tag.group(1)}")
    72	        else:
    73	            ids.append(tag.group(1))
    74	    return ids, problems
    75	
    76	
    77	def load_scenarios(path: Path) -> tuple[list[str], list[str]]:
    78	    """Validate the English document and, when present, its Vietnamese sibling."""
    79	    if not path.is_file():
    80	        raise UsageError(f"scenario document not found: {path}")
    81	    ids, problems = scenario_ids(path)
    82	    if not ids and not problems:
    83	        problems.append(f"{path}: no scenarios found inside gherkin fences")
    84	    if path.name.endswith(".en.md"):
    85	        sibling = path.with_name(path.name[: -len(".en.md")] + ".vi.md")
    86	        if sibling.is_file():
    87	            vi_ids, vi_problems = scenario_ids(sibling)
    88	            problems.extend(vi_problems)
    89	            missing = sorted(set(ids) - set(vi_ids))
    90	            extra = sorted(set(vi_ids) - set(ids))
    91	            if missing:
    92	                problems.append(f"{sibling}: missing identifiers {', '.join(missing)}")
    93	            if extra:
    94	                problems.append(f"{sibling}: identifiers not in {path.name}: {', '.join(extra)}")
    95	    return ids, problems
    96	
    97	
    98	def covers_of(path: Path) -> list[str]:
    99	    """Identifiers named on every Covers: line of one task file."""
   100	    found: list[str] = []
   101	    for line in read_text(path).splitlines():
   102	        match = COVERS_LINE.match(line)
   103	        if match:
   104	            found.extend(ID_TOKEN.findall(match.group(1)))
   105	    return found
   106	
   107	
   108	def check_plan(ids: list[str], task_paths: list[Path]) -> tuple[dict[str, list[str]], list[str]]:
   109	    coverage: dict[str, list[str]] = {identifier: [] for identifier in ids}
   110	    problems: list[str] = []
   111	    for path in task_paths:
   112	        if not path.is_file():
   113	            raise UsageError(f"task file not found: {path}")
   114	        for identifier in covers_of(path):
   115	            if identifier not in coverage:
   116	                problems.append(f"{path}: Covers names unknown identifier {identifier}")
   117	            elif path.name not in coverage[identifier]:
   118	                coverage[identifier].append(path.name)
   119	    for identifier, owners in coverage.items():
   120	        if len(owners) > 1:
   121	            problems.append(f"{identifier} is on the Covers lines of {', '.join(owners[:-1])} and {owners[-1]}")
   122	    return coverage, problems
   123	
   124	
   125	def stale_pattern(ids: list[str]) -> re.Pattern[str]:
   126	    """Uppercase hyphenated tokens shaped like this document's identifiers: same prefix, same segment count."""
   127	    shapes = sorted({(identifier.split("-")[0], identifier.count("-")) for identifier in ids})
   128	    alternatives = "|".join(re.escape(prefix) + "(?:-[A-Z0-9]+)" * (hyphens - 1) + "-[0-9]+"
   129	                            for prefix, hyphens in shapes)
   130	    return re.compile(r"(?<![A-Za-z0-9-])(?:" + alternatives + r")(?![A-Za-z0-9-])")
   131	
   132	
   133	def listed_files(root: Path) -> list[Path] | None:
   134	    """Files git lists under root — tracked, plus untracked but not ignored — or None outside git."""
   135	    try:
   136	        listed = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "--others",
   137	                                 "--exclude-standard", "-z"], capture_output=True, check=True)
   138	    except (OSError, subprocess.CalledProcessError):
   139	        return None
   140	    return [root / name for name in listed.stdout.decode("utf-8", "surrogateescape").split("\0") if name]
   141	
   142	
   143	def integration_files(roots: list[Path]) -> tuple[list[Path], list[str]]:
   144	    existing = [root for root in roots if root.is_dir()]
   145	    warnings = [f"warning: integration test root not found, skipped: {root}"
   146	                for root in roots if not root.is_dir()]
   147	    if not existing:
   148	        raise UsageError("none of the integration test roots exists: " + ", ".join(map(str, roots)))
   149	    files: list[Path] = []
   150	    for root in existing:
   151	        listed = listed_files(root)
   152	        candidates = sorted(listed) if listed is not None else sorted(root.rglob("*"))
   153	        files.extend(path for path in candidates if path.is_file() and path.suffix.lower() != ".md")
   154	    return files, warnings
   155	

exec
/bin/zsh -lc "python3 -B -c 'import sys, re, subprocess
from pathlib import Path
from unittest.mock import patch, Mock
sys.path.insert(0, \"skills/dev-implementation/resources/scripts\")
import task_contract as tc
import check_task_contract as cc
import check_epic_readiness as cr
import run_task_checks as rtc
import check_bdd_traceability as cb
import sync_task_status as sts
for cmd in [\"grep -E '\\''foo/bar/baz'\\'' README.md\", \"rg -g '\\''*.py'\\'' '\\''foo/bar'\\'' src/\", \"sed -f scripts/filter.sed src/input.txt\", \"awk -F / '\\''{print "'$1}'"'\\'' src/input.txt\", \"python3 '\\''unterminated\"]:
    print(\"command_paths\", repr(cmd), \"=>\", cc.command_paths(cmd))
cells = tc.split_cells(r\"| V1 | GREEN | "'`env MODE=strict python3 scripts/tool.py '"\\| grep -c ok"'` | exit 0 | — |")
print("escaped pipe =>", tc.parse_row(cells, set()).command)
try:
    tc.parse_row(["V1","GREEN","`true`","invalid","—"],set())
except tc.ContractError as e:
    print("early invalid Expect =>", type(e).__name__, str(e))
with patch.object(cc, "read_text", side_effect=OSError(5, "probe")):
    try: cc.read_file(Path("not-read"))
    except Exception as e: print("read_file early OSError =>",type(e).__name__,str(e))
proc=Mock(pid=1234)
proc.communicate.side_effect=[subprocess.TimeoutExpired("probe", 1), (b"partial",None)]
with patch.object(rtc.subprocess,"Popen",return_value=proc), patch.object(rtc.os,"killpg") as kill:
    print("run_command timeout =>",rtc.run_command("true", Path.cwd(), 1),"kill=",kill.call_args)
with patch.object(cb.subprocess,"run",side_effect=OSError("probe")):
    print("listed_files early OSError =>", cb.listed_files(Path.cwd()))
pattern=re.compile(r"''^'"\\.devtool/epic/[A-Za-z0-9_-]+/evidence/[A-Za-z0-9_.-]+"'$")
for p in [".devtool/epic/this_epic/evidence/out.json",".devtool/epic/another_epic/evidence/out.json",".devtool/epic/this_epic/evidence/.."]:
    print("frozen evidence regex",p,"=>",bool(pattern.fullmatch(p)), "contains traversal=", ".." in Path(p).parts)
for source in ["[HLD](sample_epic.en.md)", "[HLD](./sample_epic.en.md)"]:
    rendered=re.sub(r"'"\\]\\((?:\\./)?(["'^/)]+'"\\.md)\\)\",r\"](../epic/sample_epic/\\1)\",source)
    normalized=rendered.replace(\"](../epic/sample_epic/\",\"](\")
    for board in [Path(\"/repo/.devtool/features\"),Path(\"/repo/.devtool/features/done\")]:
        print(\"mirror\",source,\"board=\",str(board),\"resolved target=\",str((board/\"../epic/sample_epic/sample_epic.en.md\").resolve()),\"R2 equal=\",normalized==source)
ctx=cr.Context(Path(\"/repo\"),\"sample_epic\",\"sample-epic\",\"\", {Path(\"task_01.md\"):\"[HLD](./sample_epic.en.md)\"}, [], [])
with patch.object(Path,\"is_file\",return_value=True),patch.object(Path,\"read_text\",return_value=\"[HLD](../epic/sample_epic/sample_epic.en.md)\"):
    print(\"actual R2 on prescribed ./ rewrite =>\", [(f.check,f.message) for f in cr.check_task_mirrors(ctx)])
print(\"sync root calculation =>\",Path(rtc.__file__).resolve().parents[4])
print(\"current render symbol =>\",hasattr(sts,\"render_epic_tasks\"))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
command_paths "grep -E 'foo/bar/baz' README.md" => (['foo/bar/baz'], 'grep')
command_paths "rg -g '*.py' 'foo/bar' src/" => (['foo/bar', 'src/'], 'rg')
command_paths 'sed -f scripts/filter.sed src/input.txt' => (['scripts/filter.sed', 'src/input.txt'], 'sed')
command_paths "awk -F / '{print $1}' src/input.txt" => (['/', 'src/input.txt'], 'awk')
command_paths "python3 'unterminated" => ([], None)
escaped pipe => env MODE=strict python3 scripts/tool.py | grep -c ok
early invalid Expect => ContractError Verification row V1: Expect must start with "exit <n>" or "exit non-zero": 'invalid'
read_file early OSError => UsageError cannot read not-read: probe
run_command timeout => (None, b'partial') kill= call(1234, <Signals.SIGKILL: 9>)
listed_files early OSError => None
frozen evidence regex .devtool/epic/this_epic/evidence/out.json => True contains traversal= False
frozen evidence regex .devtool/epic/another_epic/evidence/out.json => True contains traversal= False
frozen evidence regex .devtool/epic/this_epic/evidence/.. => True contains traversal= True
mirror [HLD](sample_epic.en.md) board= /repo/.devtool/features resolved target= /repo/.devtool/epic/sample_epic/sample_epic.en.md R2 equal= True
mirror [HLD](sample_epic.en.md) board= /repo/.devtool/features/done resolved target= /repo/.devtool/features/epic/sample_epic/sample_epic.en.md R2 equal= True
mirror [HLD](./sample_epic.en.md) board= /repo/.devtool/features resolved target= /repo/.devtool/epic/sample_epic/sample_epic.en.md R2 equal= False
mirror [HLD](./sample_epic.en.md) board= /repo/.devtool/features/done resolved target= /repo/.devtool/features/epic/sample_epic/sample_epic.en.md R2 equal= False
actual R2 on prescribed ./ rewrite => [('R2', 'task_01.md: line 1: [HLD](./sample_epic.en.md) != [HLD](sample_epic.en.md)')]
sync root calculation => /Users/danhdueexoictif/AllProjects/ai-agent-tools
current render symbol => False

codex
Probe chỉ đọc đã xác nhận hai lỗi cụ thể trong quy tắc mirror: `./file.md` sau khi rewrite không vượt qua phép so sánh R2 hiện tại, và cùng tiền tố `../epic/` sẽ trỏ sai khi mirror nằm trong `features/done/`. Tôi cũng thấy phân chia task đang yêu cầu kiểm thử hành vi trước task triển khai hành vi đó; tôi đang đối chiếu lại DoD để xác định các điểm cần sửa trước implementation.

exec
/bin/zsh -lc "nl -ba .devtool/epic/contract_and_authoring_ergonomics/contract_and_authoring_ergonomics.vi.md | sed -n '120,181p'; nl -ba .devtool/epic/contract_and_authoring_ergonomics/2026-11-06-contract-and-authoring-ergonomics-design.vi.md | sed -n '173,200p'; nl -ba .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md | sed -n '1,65p'; nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '20,75p'; nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '83,137p;374,390p'; nl -ba skills/dev-implementation/SKILL.md | sed -n '160,255p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   120	    Designer->>Contract: Gọi check_task_contract.py --design
   121	    Contract->>Contract: Kiểm tra Evidence files:, R2 mirror parity, R3 verbatim BDD
   122	    Contract->>Contract: Kiểm tra đường dẫn khả chuyển (cấm /Users/...) & ngữ pháp
   123	    Contract-->>Designer: Result: 0 problems — PASS
   124	    Programmer->>Runner: Gọi run_task_checks.py verify <task_mirror>
   125	    Runner->>Runner: Tiêm D3NEXUS_KIT & PATH=<kit_root>/bin
   126	    Runner->>CLI: Thực thi dòng lệnh `d3nexus check-doc ...`
   127	    CLI-->>Runner: Thoát 0
   128	    Runner->>Runner: evaluate_done_gate() kiểm tra Evidence files tồn tại trên đĩa
   129	    Runner-->>Programmer: Done gate PASS
   130	```
   131	
   132	### Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới
   133	
   134	```text
   135	Integration test roots: tests/, skills/dev-implementation/resources/scripts/
   136	Protected paths: .agents/quality/**, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.en.md, .devtool/epic/contract_and_authoring_ergonomics/bdd_scenarios.vi.md
   137	Integration results: python3 -m pytest tests/ skills/dev-implementation/resources/scripts/ --junitxml=build/test-results/pytest.xml -> build/test-results/pytest.xml
   138	```
   139	
   140	| Ranh giới Tích hợp | Chiến lược Kiểm thử | Mục tiêu Xác minh |
   141	| :--- | :--- | :--- |
   142	| `task_contract.py` & `check_task_contract.py` | Kiểm thử unit và subcutaneous CLI trên git repo tạm | Xác minh phân tích `Evidence files:`, grounding `(new)`, kiểm tra tồn tại file tại Done Gate, báo lỗi `VAR=val` thiếu `env`, loại trừ mẫu grep, và kiểm tra sớm R2/R3 |
   143	| `sync_task_status.py render` | Kiểm thử render trên hệ thống file thực giữa `.devtool/epic/<epic>/` và `.devtool/features/` | Xác minh chèn Gherkin nguyên văn từ `bdd_scenarios.en.md`, nhúng `@@FILE:path@@` kèm tự nâng lên 4 backticks, viết lại relative link, và xóa mirror mồ côi |
   144	| `bin/d3nexus` & `run_task_checks.py` | Kiểm thử thực thi tiến trình con trên git repo tạm | Xác minh tự động tiêm `D3NEXUS_KIT` và `PATH`, điều phối lệnh con `d3nexus`, và từ chối đường dẫn cứng `/Users/...` hoặc plugin cache |
   145	| Tài liệu Reviewer & Authoring | Kiểm tra lint và hợp đồng tài liệu qua `check_document.py` | Xác minh tính đồng bộ của `verification-row-grammar.md`, `dev-designer/SKILL.md` và `principal-review/SKILL.md` |
   146	
   147	## Môi trường Xác minh
   148	
   149	- Môi trường thực thi: Máy cục bộ macOS / Linux CLI cài đặt Python 3.11+, Git, `pytest`, `ruff` và `mypy`.
   150	- Không phụ thuộc mạng hay cơ sở dữ liệu bên ngoài: Toàn bộ bài kiểm thử chạy trên các kho Git cục bộ tạm thời tạo bằng `tempfile.TemporaryDirectory` / `tmp_path`.
   151	- Cô lập hệ thống tệp: Các lượt chạy kiểm thử không bao giờ làm thay đổi trạng thái `.devtool/` hoặc cây thư mục làm việc của kho mã nguồn chính.
   152	
   153	### Kịch bản Kiểm thử BDD Toàn diện
   154	
   155	Bộ kịch bản bao phủ đầy đủ 5 chiều dưới tiền tố `[TCAE-]`:
   156	1. **Happy Paths (`TCAE-HP-01` .. `TCAE-HP-04`)**: Khai báo và xác minh `Evidence files:` đánh dấu `(new)`, render BDD nguyên văn và bản mirror `.devtool/features/` từ một nguồn duy nhất, chạy lệnh `d3nexus` qua cơ chế tự tiêm biến môi trường, và kiểm tra ngữ pháp bảng Verification với `\|` và `env VAR=val`.
   157	2. **Edge Cases (`TCAE-EC-01` .. `TCAE-EC-03`)**: Task không có kịch bản (`Covers: none`), file nhúng có chứa 3 dấu backtick được tự động bọc bằng rào ngoài 4 dấu backtick, và biểu thức tìm kiếm `grep`/`rg`/`sed` chứa dấu `/` không bị báo lỗi nhầm là thiếu file.
   158	3. **State Transitions (`TCAE-ST-01` .. `TCAE-ST-02`)**: Dọn dẹp mirror mồ côi và đồng bộ vị trí `done/` khi chạy `render`, cùng chuyển đổi trạng thái Done Gate từ FAIL (khi thiếu file trong `Evidence files:`) sang PASS (sau khi lệnh verification tạo đủ file).
   159	4. **Async & Concurrency (`TCAE-AR-01` .. `TCAE-AR-02`)**: Cô lập biến môi trường `D3NEXUS_KIT` / `PATH` giữa các worktree song song và đảm bảo tính tất định khi render nhiều task trên nhiều worktree.
   160	5. **Failures & Resilience (`TCAE-FR-01` .. `TCAE-FR-03`)**: Từ chối `Evidence files:` nằm ngoài `.devtool/epic/<epic>/evidence/` hoặc chứa `..`, từ chối đường dẫn cứng `/Users/...` hay `.claude/plugins/cache/...` và phép gán `VAR=val` thiếu `env`, đồng thời dừng `render` an toàn khi `Covers:` chứa mã scenario không tồn tại.
   161	
   162	## Tác động Shared Contract
   163	
   164	None — tính năng khép kín trong `ai-agent-tools`.
   165	
   166	## Chiến lược Triển khai và Giảm thiểu Rủi ro
   167	
   168	- **Giai đoạn 1**: Mở rộng `task_contract.py` và `check_task_contract.py` hỗ trợ `Evidence files:` và kiểm tra tại Done Gate (`Task 01`).
   169	- **Giai đoạn 2**: Hiện thực hóa `sync_task_status.py render` và đưa kiểm tra R2/R3 vào `check_task_contract.py --design` (`Task 02`).
   170	- **Giai đoạn 3**: Bổ sung `bin/d3nexus`, tự động tiêm `D3NEXUS_KIT`/`PATH` trong `run_task_checks.py` và `check_epic_readiness.py`, và chặn đường dẫn tuyệt đối (`Task 03`).
   171	- **Giai đoạn 4**: Bổ sung chẩn đoán ngữ pháp bảng Verification (`env VAR=val`, loại trừ mẫu grep, nguồn gốc implicit protected path) và biên soạn `verification-row-grammar.md` + cập nhật skills (`Task 04`).
   172	- **Giai đoạn 5**: Thực thi kiểm thử tích hợp đầu-cuối (Tier C) và xác minh toàn bộ kho mã nguồn (`Task 05`).
   173	- **Kế hoạch Rollback**: Mọi thay đổi đều tương thích ngược trên các script Python stdlib; hoàn tác commit merge của epic sẽ khôi phục nguyên trạng hành vi cũ.
   174	
   175	## Phân rã Kanban Tasks
   176	
   177	- [Task 01: Evidence Files Contract and Done-Gate Verification](./task_01_evidence_files_contract.md)
   178	- [Task 02: Single-Source Task Render Engine and Shift-Left R2/R3 Checks](./task_02_single_source_render_engine.md)
   179	- [Task 03: Portable d3nexus CLI and Zero-Setup Runtime Environment Injection](./task_03_portable_d3nexus_cli_and_env.md)
   180	- [Task 04: Verification Row Grammar Diagnostics and Reference Documentation](./task_04_verification_grammar_and_docs.md)
   181	- [Task 05: End-to-End Integration and Acceptance Verification](./task_05_end_to_end_contract_acceptance.md)
   173	## Xử lý Lỗi và Các Trường hợp Biên
   174	
   175	- **Mã Scenario trong `Covers:` Không Tồn tại**: `sync_task_status.py render` dừng ngay với thông báo chỉ rõ tên file task và mã scenario bị thiếu mà không làm hỏng file trên đĩa.
   176	- **Đường dẫn Chứa `..` trong `Evidence files:` hoặc `<!-- @@FILE:...@@ -->`**: Mọi đường dẫn chứa `..`, bắt đầu bằng `/` hoặc trỏ ra ngoài phạm vi cho phép đều bị từ chối với `ContractError` / `UsageError` và mã thoát khác 0.
   177	- **Task Không Có `Covers:` (`Covers: none`)**: `sync_task_status.py render` bỏ qua bước chèn Gherkin BDD nhưng vẫn thực hiện nhúng `@@FILE:...@@` và sinh bản mirror `.devtool/features/`.
   178	- **Các Epic Cũ**: Các epic không khai báo `Evidence files:` hoặc `<!-- @@FILE:...@@ -->` tiếp tục vượt qua mọi bài kiểm tra mà không bị ảnh hưởng.
   179	
   180	## Chiến lược Kiểm thử và Xác minh
   181	
   182	- **Tier A (Unit Tests)**:
   183	  - `test_check_task_contract.py`: Kiểm thử phân tích `Evidence files:`, grounding cho đường dẫn evidence `(new)`, chặn đường dẫn tuyệt đối `/Users/...` và `.claude/plugins/cache/...`, chẩn đoán `VAR=val` thiếu `env`, bỏ qua mẫu `grep`/`rg` có chứa dấu `/`, và kiểm tra sớm R2/R3.
   184	  - `test_sync_task_status.py`: Kiểm thử lệnh con `render` cho việc chèn BDD nguyên văn từ `bdd_scenarios.en.md`, nhúng code `<!-- @@FILE:...@@ -->` (bao gồm tự động nâng lên 4 dấu backtick), viết lại liên kết tương đối trong `.devtool/features/`, và dọn dẹp mirror mồ côi.
   185	  - `test_run_task_checks.py`: Kiểm thử việc tự động tiêm `D3NEXUS_KIT` và `PATH` khi chạy dòng Verification cũng như kiểm tra sự tồn tại của `Evidence files:` tại Done Gate.
   186	- **Tier C1 (Subcutaneous End-to-End Integration)**:
   187	  - Kiểm thử tích hợp đầu-cuối trên một git repo tạm có đủ HLD, `bdd_scenarios.en.md`, và file nguồn `.devtool/epic/<epic>/task_1.md`; chạy lần lượt `bin/d3nexus sync-status render`, `bin/d3nexus check-contract --design`, và `bin/d3nexus run-checks verify` (bên trong có dòng lệnh gọi `d3nexus check-doc` và sinh file trong `Evidence files:`), xác nhận Done Gate trả về PASS.
   188	- **Cổng Chất lượng Kho mã nguồn**:
   189	  - `scripts/verify.sh` và `python-quality-check` (`ruff check`, `mypy`, `pytest`) phải vượt qua với 0 lỗi.
   190	
   191	## Cảnh báo Shared Contract
   192	
   193	- Không tồn tại thư mục `shared-contracts/` trong `ai-agent-tools` (kho mã nguồn này là bộ công cụ workflow plugin, không phải dịch vụ tiêu thụ hợp đồng domain của `D3Nexus`). Không có API contract, cấu trúc bản tin hay schema cơ sở dữ liệu dùng chung nào bị ảnh hưởng.
   194	
   195	## Ánh xạ Phụ thuộc và Bối cảnh Lộ trình
   196	
   197	- **Mở đường cho các Epic tiếp theo**:
   198	  - **Epic 2 (`execution_and_verification_infrastructure`)**: Sử dụng trực tiếp `Evidence files:` (`#0008`), `bin/d3nexus` (`#0016`), và `sync_task_status.py render` (`#0012`) để lưu trữ tập baseline lỗi (`.devtool/epic/<epic>/evidence/baseline_failures.txt`) và bằng chứng đo lường (`#0007`, `#0017`).
   199	  - **Epic 3 (`multi_epic_orchestration_and_governance`)**: Kế thừa và mở rộng `check_task_contract.py` cùng `sync_task_status.py` cho bài toán phụ thuộc liên epic (`#0013`, `#0014`) và đóng gói lại epic (`#0015`).
   200	
     1	# Kịch bản Kiểm thử BDD: Hợp đồng Task và Tối ưu Soạn thảo (Task Contract and Authoring Ergonomics)
     2	
     3	## Mục lục
     4	
     5	- [Chiều 1: Luồng Thành công Chuẩn (Happy Paths)](#chiều-1-luồng-thành-công-chuẩn-happy-paths)
     6	- [Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)](#chiều-2-trường-hợp-biên-và-giới-hạn-edge-cases-and-boundaries)
     7	- [Chiều 3: Chuyển đổi Trạng thái (State Transitions)](#chiều-3-chuyển-đổi-trạng-thái-state-transitions)
     8	- [Chiều 4: Bất đồng bộ và Đồng thời (Async and Concurrency)](#chiều-4-bất-đồng-bộ-và-đồng-thời-async-and-concurrency)
     9	- [Chiều 5: Xử lý Lỗi và Phục hồi (Failures and Resilience)](#chiều-5-xử-lý-lỗi-và-phục-hồi-failures-and-resilience)
    10	
    11	## Chiều 1: Luồng Thành công Chuẩn (Happy Paths)
    12	
    13	```gherkin
    14	Scenario: [TCAE-HP-01] [Tier C - Integration] Khai báo Evidence files vượt qua kiểm tra hợp đồng thiết kế và xác minh tại Done-Gate
    15	  Given một task khai báo ".devtool/epic/sample_epic/evidence/baseline.txt (new)" dưới mục "Evidence files:" trong "## Files"
    16	  And một dòng Verification tham chiếu tới ".devtool/epic/sample_epic/evidence/baseline.txt"
    17	  When check_task_contract.py chạy với cờ "--design"
    18	  Then công cụ thoát mã 0 với 0 lỗi và ghi nhận đường dẫn evidence mới trên toàn epic
    19	  And khi run_task_checks.py verify thực thi dòng lệnh tạo ra file ".devtool/epic/sample_epic/evidence/baseline.txt"
    20	  Then evaluate_done_gate xác nhận file evidence tồn tại trên đĩa và vượt qua mọi điều kiện Done-Gate
    21	
    22	Scenario: [TCAE-HP-02] [Tier C - Integration] Render task từ một nguồn duy nhất tự động chèn BDD nguyên văn, nhúng code và sinh bản mirror
    23	  Given một file task nguồn ".devtool/epic/sample_epic/task_01_setup.md" có dòng "Covers: TCAE-HP-01" và chỉ thị "<!-- @@FILE:src/helper.py@@ -->"
    24	  And file ".devtool/epic/sample_epic/bdd_scenarios.en.md" định nghĩa kịch bản "[TCAE-HP-01]"
    25	  When thực thi lệnh "sync_task_status.py render sample_epic"
    26	  Then file ".devtool/epic/sample_epic/task_01_setup.md" chứa chính xác khối Gherkin nguyên văn của "[TCAE-HP-01]" và toàn bộ nội dung của "src/helper.py"
    27	  And bản mirror ".devtool/features/task_01_setup.md" được sinh ra với các liên kết tương đối được viết lại thành "../epic/sample_epic/"
    28	  And lệnh "check_task_contract.py --design" thoát mã 0 mà không có bất kỳ lỗi R2 hay R3 nào
    29	
    30	Scenario: [TCAE-HP-03] [Tier C - Integration] Thực thi CLI d3nexus không cần cài đặt (Zero-Setup) bên trong dòng Verification
    31	  Given một dòng Verification của task gọi lệnh "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
    32	  When lệnh "run_task_checks.py verify" thực thi task trong một kho git tạm chưa hề cấu hình sẵn biến môi trường shell
    33	  Then "run_task_checks.py" tự động tiêm biến "D3NEXUS_KIT" và gắn "<kit_root>/bin" vào đầu "PATH"
    34	  And lệnh "d3nexus check-doc" điều phối tới "check_document.py" và thoát mã 0
    35	
    36	Scenario: [TCAE-HP-04] [Tier A - Unit] Ngữ pháp dòng Verification với ký tự pipe được escape, biến môi trường env và nguồn gốc implicit protected path
    37	  Given một dòng lệnh Verification viết "env MODE=strict python3 scripts/tool.py \| grep -c ok"
    38	  When lệnh "check_task_contract.py --design" đánh giá task
    39	  Then "task_contract.py" tự động unescape "\|" thành "|" trong câu lệnh đã phân tích mà không báo lỗi hợp đồng
    40	  And "check_task_contract.py" hiển thị "scripts/tool.py (task_01:V1)" trong dòng "Implicit protected paths:"
    41	```
    42	
    43	## Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)
    44	
    45	```gherkin
    46	Scenario: [TCAE-EC-01] [Tier A - Unit] Task không khai báo Evidence files hoặc không có dòng Covers vẫn tương thích ngược hoàn toàn
    47	  Given một file task kiểu cũ không có tiểu mục "Evidence files:" và không có dòng "Covers:"
    48	  When chạy "sync_task_status.py render" và "check_task_contract.py --design" trên epic đó
    49	  Then "sync_task_status.py render" vẫn sinh bản mirror ".devtool/features/" mà không làm thay đổi mục BDD của task
    50	  And "check_task_contract.py --design" thoát mã 0 với 0 lỗi
    51	
    52	Scenario: [TCAE-EC-02] [Tier A - Unit] File nhúng chứa 3 dấu backtick tự động nâng rào ngoài lên 4 dấu backtick
    53	  Given một file nguồn "docs/snippet.md" có chứa một khối code fence được bao bởi 3 dấu backtick
    54	  And một file task chứa chỉ thị "<!-- @@FILE:docs/snippet.md@@ -->" ngay phía trên khối code fence 3 dấu backtick
    55	  When thực thi lệnh "sync_task_status.py render sample_epic"
    56	  Then khối code sau khi render trong cả file task của epic và bản mirror ".devtool/features/" đều sử dụng rào ngoài gồm 4 dấu backtick
    57	
    58	Scenario: [TCAE-EC-03] [Tier A - Unit] Biểu thức tìm kiếm chứa dấu gạch chéo trong grep, rg, sed và awk không bị báo lỗi nhầm là thiếu file
    59	  Given một dòng lệnh Verification viết "grep -E 'foo/bar/baz' README.md" trong đó "foo/bar/baz" không phải là file trên đĩa
    60	  When "check_task_contract.py --design" kiểm tra các token của câu lệnh
    61	  Then hàm "command_paths()" loại trừ biểu thức tìm kiếm "foo/bar/baz" khỏi bước kiểm tra sự tồn tại của file
    62	  And "check_task_contract.py" thoát mã 0 mà không báo lỗi "foo/bar/baz does not exist"
    63	```
    64	
    65	## Chiều 3: Chuyển đổi Trạng thái (State Transitions)
    20	
    21	ID_SHAPE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+")
    22	SCENARIO_KEYWORDS = (
    23	    "Scenario Outline", "Scenario Template", "Scenario", "Example",
    24	    "Khung tình huống", "Khung kịch bản", "Tình huống", "Kịch bản",
    25	)
    26	SCENARIO_LINE = re.compile(
    27	    r"^\s*(?:" + "|".join(re.escape(keyword) for keyword in SCENARIO_KEYWORDS) + r")\s*:\s*(.*)$"
    28	)
    29	LEADING_TAG = re.compile(r"^\[([^\]]*)\]")
    30	FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
    31	COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
    32	ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])" + ID_SHAPE.pattern + r"(?![A-Za-z0-9])")
    33	
    34	
    35	class UsageError(Exception):
    36	    """Missing input: exit 2."""
    37	
    38	
    39	def read_text(path: Path) -> str:
    40	    """Read a scenario document or task file; anything but UTF-8 is a usage error."""
    41	    try:
    42	        return path.read_text(encoding="utf-8")
    43	    except UnicodeDecodeError:
    44	        raise UsageError(f"{path} is not valid UTF-8") from None
    45	
    46	
    47	def scenario_ids(path: Path) -> tuple[list[str], list[str]]:
    48	    """Identifiers in document order, and the problems found, for one scenario document."""
    49	    ids: list[str] = []
    50	    problems: list[str] = []
    51	    fence_marker: str | None = None
    52	    in_gherkin = False
    53	    for number, line in enumerate(read_text(path).splitlines(), start=1):
    54	        fence = FENCE.match(line)
    55	        if fence and fence_marker is None:
    56	            fence_marker, in_gherkin = fence.group(1), fence.group(2).lower() == "gherkin"
    57	            continue
    58	        if (fence and fence.group(1)[0] == fence_marker[0]
    59	                and len(fence.group(1)) >= len(fence_marker) and not fence.group(2)):
    60	            fence_marker, in_gherkin = None, False
    61	            continue
    62	        match = SCENARIO_LINE.match(line) if in_gherkin else None
    63	        if not match:
    64	            continue
    65	        tag = LEADING_TAG.match(match.group(1).strip())
    66	        if not tag:
    67	            problems.append(f"{path}:{number}: scenario has no identifier")
    68	        elif not ID_SHAPE.fullmatch(tag.group(1)):
    69	            problems.append(f"{path}:{number}: malformed identifier [{tag.group(1)}]")
    70	        elif tag.group(1) in ids:
    71	            problems.append(f"{path}:{number}: duplicate identifier {tag.group(1)}")
    72	        else:
    73	            ids.append(tag.group(1))
    74	    return ids, problems
    75	
    83	def is_pytest_command(command: str) -> bool:
    84	    try:
    85	        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    86	        lexer.whitespace_split = True
    87	        tokens = list(lexer)
    88	    except ValueError:
    89	        return False
    90	    subcommands: list[list[str]] = []
    91	    current: list[str] = []
    92	    for token in tokens:
    93	        if token in CONTROL_TOKENS:
    94	            if current:
    95	                subcommands.append(current)
    96	                current = []
    97	        else:
    98	            current.append(token)
    99	    if current:
   100	        subcommands.append(current)
   101	
   102	    for sub in subcommands:
   103	        sub = strip_wrappers(sub)
   104	        if not sub:
   105	            continue
   106	        prog = Path(sub[0]).name
   107	        if prog == "pytest":
   108	            return True
   109	        if (
   110	            (prog in ("python", "python3") or prog.startswith("python3."))
   111	            and len(sub) >= 3
   112	            and sub[1] == "-m"
   113	            and sub[2] == "pytest"
   114	        ):
   115	            return True
   116	    return False
   117	
   118	
   119	def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
   120	    """Evaluate whether a pytest RED execution is genuine.
   121	
   122	    Returns None if valid or not a pytest command.
   123	    Returns INVALID_PYTEST_RED_REASON if it is an invalid pytest RED run.
   124	    """
   125	    if not is_pytest_command(command):
   126	        return None
   127	    if exit_code not in (1, 2):
   128	        return INVALID_PYTEST_RED_REASON
   129	    for marker in FORBIDDEN_MARKERS:
   130	        if marker.search(output_text):
   131	            return INVALID_PYTEST_RED_REASON
   132	    if not POSITIVE_FAILURE_SUMMARY.search(output_text):
   133	        return INVALID_PYTEST_RED_REASON
   134	    return None
   135	
   136	
   137	def parse_covers(text: str) -> list[str]:
   374	def main(argv: list[str] | None = None) -> int:
   375	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   376	    parser.add_argument("mode", choices=("red", "verify", "status"))
   377	    parser.add_argument("task", type=Path)
   378	    parser.add_argument("--timeout", type=int, default=1800)
   379	    args = parser.parse_args(argv)
   380	    try:
   381	        if not args.task.is_file():
   382	            raise ContractError(f"task file not found: {args.task}")
   383	        return status(args) if args.mode == "status" else run(args)
   384	    except ContractError as error:
   385	        print(f"error: {error}", file=sys.stderr)
   386	        return 2
   387	
   388	
   389	if __name__ == "__main__":
   390	    sys.exit(main())
   160	5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
   161	6. Never copy build caches (`.dart_tool/`, `/build/`, `.build/`, `android/**/.cxx/`) from another checkout into this worktree.
   162	
   163	### Phase 2 — Sequential Task Execution
   164	
   165	For each task in confirmed order, follow `d3nexus:subagent-driven-development`.
   166	
   167	0. **Pre-Edit Verification (Impact & Conflict Check)**:
   168	   ```bash
   169	   python3 skills/impact-analysis/resources/scripts/check_code_impact.py \
   170	     --files <target_files> \
   171	     --symbols <target_symbols> \
   172	     --base-ref <base_ref>
   173	   ```
   174	   - If `🔴 DIVERGENCE DETECTED`: **HALT IMMEDIATELY**. Run step 7 (Integrate with develop) now, then rerun check.
   175	   - If `⚠️ UNPROTECTED CODE (0% Coverage)`: Author baseline characterization unit tests first.
   176	
   177	1. **Live Dual-Workspace Kanban Status (In-Progress)**:
   178	   ```bash
   179	   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> in-progress
   180	   ```
   181	
   182	   **Test Assertion Health Rule**: When authoring tests verifying build artifacts, never assert conditions only inside `if path.exists()` without asserting evaluated counts. Always assert `found > 0`.
   183	
   184	   **Tri-Persona Subagent Execution Model**:
   185	   When dispatching implementer subagent, operate across the 3-Tier Testing Standard:
   186	   1. **Expert QA (Red Team Persona)**: Authors BDD Scenarios in complete isolation from coding, purely from HLD and `bdd_scenarios.en.md`, applying 5 dimensions: Happy Paths, Edge Cases & Boundaries, State Transitions, Async / Race Conditions, Failures & Resilience. Categorizes scenarios into `[Tier A - Unit]` vs `[Tier C - Integration]`. In Satellite Mode, authors verification scenarios validating that local deserializers parse both legacy and updated upstream payloads safely.
   187	   2. **Principal Engineer (TDD Master Persona — Tier A)**: Implements unit logic, state emissions, and hermetic tests using platform tools (Dart/Flutter, Kotlin/Compose, Swift/SwiftUI, TypeScript/Web, Python/pytest, Rust/cargo). Enforces RED failing test first -> minimal GREEN code -> REFACTOR formatting, linter, strict types. In Satellite Mode, adapts consumer models, DTOs, and adapters within satellite-internal files without staging symlinked paths.
   188	   3. **System Integration & E2E Engineer (Tier C Persona)**: Implements host integration flow tests (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) connecting DI, navigation, and persistence contracts.
   189	
   190	   #### Anti-Rationalization and Doubt-Driven Verification
   191	
   192	   During implementation, coding agents must actively guard against rationalizations that cut testing corners:
   193	
   194	   | Agent Rationalization | Enforced Counter-Rule |
   195	   | :--- | :--- |
   196	   | "A Node.js test is sufficient to prove this web UI feature works." | **REJECTED**: Node tests prove only pure data logic. 80% of web defects occur in DOM queries, event bubbling, and CSS rendering. Tier C requires headless Playwright execution with Zero-Console-And-Layout-Defect Watchdog. |
   197	   | "This component is simple; hardcoding mock data in a stub is enough." | **REJECTED**: Method-level stubs bypass JSON deserialization and network interceptors. Wire-level fixtures from `shared-contracts/` are mandatory. |
   198	   | "The red errors in the browser console are just harmless warnings." | **REJECTED**: The Zero-Console-Error rule fails Gate 4 on any browser console error or uncaught exception. |
   199	   | "I cannot launch a mobile simulator, so I will write a unit test instead." | **REJECTED**: Mobile Tier C requires Subcutaneous Testing with real DI and in-memory persistence. Pure unit tests cannot be tagged as Tier C. |
   200	   | "I ported the HTML structure and JS logic from the Visual Companion mockup, and the DOM selectors match in Playwright." | **REJECTED**: Porting HTML/JS without verifying computed CSS styles results in broken, unstyled layouts. Tier C2 tests for UI components MUST assert `getComputedStyle` and `getBoundingClientRect` properties (non-zero dimensions, layout display mode, and mutually exclusive state visibility, while respecting standard clipped `.sr-only` accessibility patterns) against the Visual Companion design. |
   201	
   202	   **Doubt-Driven Verification Protocol**:
   203	   Before claiming done on any task:
   204	   1. `CLAIM`: Identify the test assertions claiming Tier C coverage.
   205	   2. `EXTRACT`: Inspect test reports and runner provenance.
   206	   3. `DOUBT`: Ask whether mocks hide runtime DI/DOM integration failures.
   207	   4. `RECONCILE`: Run real headless Playwright or subcutaneous integration tests.
   208	
   209	   > [!CRITICAL]
   210	   > ### 🎯 MANDATORY 100% BDD-TO-TEST TRACEABILITY RULE
   211	   > 1. **100% Scenario Traceability**: Every single BDD scenario authored in Phase 1 MUST map directly to at least one concrete automated test function or test block.
   212	   > 2. **Tier Separation**: `[Tier A - Unit]` covered 100% by unit tests; `[Tier C - Integration]` covered 100% by host integration flow tests. Mocks do NOT substitute for Tier C integration tests.
   213	   > 3. **BDD Automation (Tier C, all platforms)**: For every identifier on task's `Covers:` line, author at least one integration test under HLD's `Integration test roots`, carrying the identifier in test name, description, or tag.
   214	   > 4. **Gate to Done**:
   215	   >    ```bash
   216	   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py red <task mirror>     # before implementing (exits 0 on expected fail)
   217	   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py verify <task mirror>  # after last change (exits 0 with all pass)
   218	   >    python3 "$SKILL_DIR"/resources/scripts/run_task_checks.py status <task mirror>  # prints done gate: PASS
   219	   >    ```
   220	   >    Never edit `.devtool/epic/<epic_dir>/evidence/<task_id>.json` by hand. `sync_task_status.py task <id> done` refuses unless evidence matches tree and table.
   221	   >    When task has `Covers:` line, run traceability check (exit 0):
   222	   >    ```bash
   223	   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   224	   >      --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
   225	   >      --roots <Integration test roots from the HLD> \
   226	   >      --ids <identifiers on the task's Covers: line>
   227	   >    ```
   228	   > 5. **Stop and Report**: A `Stop and Report If` condition in task is reported as `BLOCKED`. Never edit Verification table, Definition of Done, Allowed files or Covers line, or protected path, to force a pass. In Satellite Mode, report `BLOCKED` if an unmerged upstream contract change prevents local tests from passing.
   229	
   230	2. When implementer reports `DONE`, synchronize review status:
   231	   ```bash
   232	   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> review
   233	   ```
   234	3. If review finds issues, cycle between `status: "in-progress"` and `status: "review"`.
   235	4. When both reviews pass, `run_task_checks.py status <task mirror>` prints `done gate: PASS` and `check_bdd_traceability.py tests --ids` exits 0, update status to `done`:
   236	   ```bash
   237	   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> done
   238	   ```
   239	   This moves `.devtool/features/<task_id>.md` into `.devtool/features/done/`.
   240	5. Make exactly one commit staging code, task file, and evidence file (`.devtool/epic/<epic_dir>/evidence/<task_id>.json`):
   241	   ```bash
   242	   git status                                    # check nothing unrelated is pending
   243	   git add -A                                    # code changes + .devtool/features/ + evidence
   244	   git commit -m "[EPIC_NAME] <task_title>" -m "- <subtask 1>
   245	   - <subtask 2>"
   246	   ```
   247	   No trailers (no `Co-Authored-By`).
   248	   Log programmer activity and update state (which synchronizes `window.title` to the latest completed task):
   249	   ```bash
   250	   python3 scripts/resume_context.py --log --epic <epic_slug> --task <task_id> --request "<summary>" --action "<tests>"
   251	   python3 scripts/resume_context.py --state --epic <epic_slug>
   252	   ```
   253	6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
   254	7. **Integrate with develop.** Run in orchestrator from epic worktree after step 5 commit:
   255	   ```bash

exec
/bin/zsh -lc "rg -n 'RED|already|test.*first|n/a|test.*pass' skills/dev-implementation/SKILL.md | head -65; rg -n 'evidence|.devtool' skills/dev-implementation/resources/scripts/check_task_contract.py skills/dev-implementation/resources/scripts/task_contract.py | tail -25; /Library/Developer/CommandLineTools/usr/bin/git diff --quiet e4725dcf21bae83479967b22137325d3a320eb69 -- .devtool/epic/contract_and_authoring_ergonomics skills/dev-implementation/resources/scripts scripts/resume_context.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
3:description: Use when an epic already has an approved HLD and Kanban task files (`.devtool/epic/<epic_dir>/` + `.devtool/features/task_*.md`) and you need to actually execute those tasks against the codebase, in the right order, inside an isolated worktree across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects.
10:Runs an already-approved epic's Kanban tasks end-to-end: reload the epic's own docs for context, detect the platform (Flutter, Android Native, iOS Native, Web, Python, or Rust), compute a dependency-safe execution order, bootstrap one worktree that can actually build this project, then drive each task sequentially through `d3nexus:subagent-driven-development` with exactly one commit per task.
29:- The epic has a `.devtool/epic/<epic_dir>/<epic_dir>.en.md` HLD and one or more `.devtool/features/task_*.md` files with `epic: "<epic_slug>"` in frontmatter, and a human has already approved that design.
112:4. **Gate 3 (resume).** Check mirror scan summary against task mirror count and read Manual review advised section. State the Principal Review status (`not run`, `round <n>: PASS`, or `round <n>: decided`), and stop with the triage if that check exits 1. Run Phase 1 step 3's BDD mapping check and task contract check, including retrofit if needed. Commit any retrofit on epic branch staging only touched files (both `bdd_scenarios`, both HLD variants, task files — never `git add -A`). The interrupted task's own status fields may ride along in that commit; that is expected. Present tasks already `done` with commits (`git log --oneline develop..epic/<epic_slug>`), remaining order with `done` tasks removed, choice on uncommitted changes (keep or discard), and request permission to fast-forward `develop`. Wait for confirmation.
175:   - If `⚠️ UNPROTECTED CODE (0% Coverage)`: Author baseline characterization unit tests first.
187:   2. **Principal Engineer (TDD Master Persona — Tier A)**: Implements unit logic, state emissions, and hermetic tests using platform tools (Dart/Flutter, Kotlin/Compose, Swift/SwiftUI, TypeScript/Web, Python/pytest, Rust/cargo). Enforces RED failing test first -> minimal GREEN code -> REFACTOR formatting, linter, strict types. In Satellite Mode, adapts consumer models, DTOs, and adapters within satellite-internal files without staging symlinked paths.
228:   > 5. **Stop and Report**: A `Stop and Report If` condition in task is reported as `BLOCKED`. Never edit Verification table, Definition of Done, Allowed files or Covers line, or protected path, to force a pass. In Satellite Mode, report `BLOCKED` if an unmerged upstream contract change prevents local tests from passing.
326:Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
skills/dev-implementation/resources/scripts/task_contract.py:35:EXCLUDE_DEVTOOL = ":(exclude).devtool"
skills/dev-implementation/resources/scripts/task_contract.py:74:    evidence: Path
skills/dev-implementation/resources/scripts/task_contract.py:326:    if not (len(parts) == 4 and parts[:2] == (".devtool", "epic") and re.fullmatch(r"task_.*\.md", parts[3])):
skills/dev-implementation/resources/scripts/task_contract.py:327:        raise ContractError("pass the task's mirror under .devtool/epic/<epic_dir>/")
skills/dev-implementation/resources/scripts/task_contract.py:330:                      epic_dir / "bdd_scenarios.en.md", epic_dir / "evidence" / f"{path.stem}.json")
skills/dev-implementation/resources/scripts/task_contract.py:334:    """Tree id of the worktree without .devtool/, and its stable patch id against HEAD outside .devtool/."""
skills/dev-implementation/resources/scripts/task_contract.py:338:        git_run(root, "rm", "-r", "-q", "--cached", "--ignore-unmatch", "--", ".devtool", env=env)
skills/dev-implementation/resources/scripts/task_contract.py:361:def load_evidence(path: Path) -> dict | None:
skills/dev-implementation/resources/scripts/task_contract.py:368:def save_evidence(path: Path, data: dict) -> None:
skills/dev-implementation/resources/scripts/task_contract.py:390:            problems.append(f"condition 2: row {row.id}: no PASS result in the evidence")
skills/dev-implementation/resources/scripts/task_contract.py:407:    evidence = load_evidence(layout.evidence)
skills/dev-implementation/resources/scripts/task_contract.py:408:    if evidence is None:
skills/dev-implementation/resources/scripts/task_contract.py:409:        return [f"condition 1: evidence {layout.evidence} not found in this checkout — record it with "
skills/dev-implementation/resources/scripts/task_contract.py:411:    runs = evidence.get("runs", {})
skills/dev-implementation/resources/scripts/task_contract.py:415:        return [f"condition 1: evidence {layout.evidence} has no {kind} run" for kind in missing]
skills/dev-implementation/resources/scripts/task_contract.py:429:        problems.append("condition 4: verify saw no change outside .devtool — record verify before committing")

exec
/bin/zsh -lc "rg -n '/Users/|/home/|~/|\\.claude/plugins/cache/|\\.gemini/config/plugins/' .devtool/epic --glob 'task_[0-9]*.md' | head -45; nl -ba scripts/test_verifiable_handoff.py | sed -n '55,150p'; nl -ba skills/dev-implementation/resources/scripts/task_contract.py | sed -n '15,40p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md:21:Resolve Observation #0016: task Verification rows invoke kit scripts (`check_document.py`) using machine- and profile-specific absolute paths (`/Users/.../antigravity_homes/tess/.claude/plugins/cache/...`), which fail when run on another machine, OS user, account profile, or plugin version.
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md:27:4. In `check_task_contract.py`, reject any Verification row command containing hardcoded user home or plugin cache paths (`/Users/`, `/home/`, `~/`, `.claude/plugins/cache/`, `.gemini/config/plugins/`) and recognize `d3nexus` as a built-in kit executable.
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md:77:  Given a task with row V1 calling "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
.devtool/epic/contract_and_authoring_ergonomics/task_03_portable_d3nexus_cli_and_env.md:112:- `NON_PORTABLE_PATH_RE` in `check_task_contract.py` matches `(?:/Users/|/home/|~/|\.claude/plugins/cache/|\.gemini/config/plugins/)` and reports `"non-portable path '<match>' in command; use 'd3nexus <subcommand>' or '$D3NEXUS_KIT/...'"`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:22:Crucially, this provider is modeled directly on the canonical ground truth established in the [bloc_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/) template:
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:34:- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/pubspec.yaml`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:36:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/dartfmt.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:37:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/check_module_boundaries.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:38:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/check_license_header.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_3_build_flutter_quality_provider.md:39:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/bloc_digital_wallet/scripts/testWithCoverage.sh`.
.devtool/epic/epic_slug_sanitization/task_4_plugin_sync_and_verification.md:18:Synchronize all updated scripts and unit tests from `ai-agent-tools/skills/epic-implementation/resources/scripts/` to `~/.gemini/config/plugins/d3nexus/skills/epic-implementation/resources/scripts/`. Run the full test suite across the entire scripts directory to verify 100% green test execution. Prepare the branch for merge and release.
.devtool/epic/epic_slug_sanitization/task_4_plugin_sync_and_verification.md:25:- `slug_utils.py`, `sync_task_status.py`, `compute_execution_order.py`, and test files are copied to `~/.gemini/config/plugins/d3nexus/`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:22:Crucially, this provider is modeled directly on the canonical ground truth established in the [android_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/) template:
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:35:- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/build.gradle.kts`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:37:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/konsist-test/`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:38:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/scripts/konsist_boundary_whitelist.txt`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:39:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/scripts/acceptance_check.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_4_build_android_quality_provider.md:40:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/android_digital_wallet/buildSrc/src/main/kotlin/codeanalyzetools/`.
.devtool/epic/context_memory_management/task_02_zshrc_and_environment_sync.md:23:   - Ensure `export REAL_HOME="/Users/danhdueexoictif"` (or target `real_home`) and `export WORKSPACE_ROOT="$REAL_HOME/AllProjects"` are declared in `.zshrc`.
.devtool/epic/context_memory_management/task_02_zshrc_and_environment_sync.md:116:- New frozen contract `sync_shell_env(real_home: Path | None = None, workspace_root: Path | None = None) -> dict[str, object]` in `scripts/resume_context.py` accepts explicit paths for hermetic testing in `tempfile.TemporaryDirectory()` and defaults to `Path("/Users/danhdueexoictif")` and `Path("/Users/danhdueexoictif/AllProjects")` when invoked via `--sync-zshrc`.
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:21:Onboard the target consumer repository `/Users/danhdueexoictif/AllProjects/lyrics-sync` into the new Python quality framework and certify a 100% green baseline:
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:23:   - Run the updated `scaffold_quality_manifest.py` against `/Users/danhdueexoictif/AllProjects/lyrics-sync`.
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:44:- Target Consumer Repo: `/Users/danhdueexoictif/AllProjects/lyrics-sync`
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:46:  - `/Users/danhdueexoictif/AllProjects/lyrics-sync/.agents/quality/check_quality.json`
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:47:  - `/Users/danhdueexoictif/AllProjects/lyrics-sync/.agents/quality/python-quality.json`
.devtool/epic/python_quality_provider_and_onboarding/task_4_onboard_lyrics_sync.md:48:- Python Configuration: `/Users/danhdueexoictif/AllProjects/lyrics-sync/pyproject.toml`
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:22:Crucially, this provider is modeled directly on the canonical ground truth established in the [ios_digital_wallet](file:///Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/) template:
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:35:- Template Reference: `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/Project.swift`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:37:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/ArchTests/`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:38:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/quality/.swiftlint.yml`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:39:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/quality/.swiftformat`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:40:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/check_module_boundaries.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:41:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/check_coverage_thresholds.sh`.
.devtool/epic/mobile_quality_providers_and_contract_hardening/task_5_build_ios_quality_provider.md:42:  - `/Users/danhdueexoictif/AllProjects/digital_wallet/ios_digital_wallet/scripts/acceptance_check.sh`.
.devtool/epic/python_quality_provider_and_onboarding/task_1_build_python_quality_provider.md:33:- Template Reference: `/Users/danhdueexoictif/AllProjects/lyrics-sync/pyproject.toml`
.devtool/epic/epic_archival_and_planning_gate/task_4_workspace_verification_and_release.md:25:- `~/.gemini/config/plugins/d3nexus`: Local plugin installation target.
.devtool/epic/epic_archival_and_planning_gate/task_4_workspace_verification_and_release.md:45:- **Scenario 4**: `scripts/release.sh` successfully packages v1.0.15 and updates `~/.gemini/config/plugins/d3nexus`.
.devtool/epic/epic_archival_and_planning_gate/task_4_workspace_verification_and_release.md:56:- v1.0.15 released and synced to `~/.gemini/config/plugins/d3nexus`.
.devtool/epic/lean_product_suite/task_5_suite_integration_and_verification.md:42:> `~/.gemini/config/plugins/d3nexus/` is **a git clone of this repository** on `main`, not a
.devtool/epic/lean_product_suite/task_5_suite_integration_and_verification.md:43:> file-copy target. `scripts/release.sh` syncs it with `git -C "$HOME/.gemini/config/plugins/d3nexus"
    55	"""
    56	
    57	TASK_TEXT = f"""---
    58	id: "{TASK}"
    59	status: "todo"
    60	priority: "high"
    61	assignee: null
    62	epic: "demo"
    63	dueDate: null
    64	created: "2026-10-16T00:00:00Z"
    65	modified: "2026-10-16T00:00:00Z"
    66	completedAt: null
    67	labels: []
    68	order: "a1"
    69	---
    70	
    71	# Task 1: Demo
    72	
    73	## Files
    74	
    75	Allowed files:
    76	- `feature.txt` (new)
    77	
    78	## Verification
    79	
    80	{TABLE_HEAD}| V1 | RED | `test -f feature.txt` | exit non-zero | — |
    81	| V2 | GREEN | `test -f feature.txt` | exit 0 | — |
    82	| V3 | TIER-C | `python3 {JUNIT} --junitxml build/r.xml tests/test_demo.py` | exit 0; results build/r.xml | — |
    83	
    84	## Definition of Done
    85	
    86	- the feature exists (V2)
    87	- the demo scenario passes (V3)
    88	
    89	## Stop and Report If
    90	
    91	- A command does not match the repository.
    92	
    93	## Decisions Already Made
    94	
    95	- Feature file is created in root workspace and verified by test harness.
    96	
    97	## BDD Scenarios
    98	
    99	Covers: DEMO-HP-01
   100	"""
   101	
   102	
   103	def git(root: Path, *args: str) -> str:
   104	    done = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
   105	                           "-C", str(root), *args], capture_output=True, text=True, check=True)
   106	    return done.stdout
   107	
   108	
   109	class DesignToAuditTest(unittest.TestCase):
   110	    def setUp(self) -> None:
   111	        directory = tempfile.TemporaryDirectory()
   112	        self.addCleanup(directory.cleanup)
   113	        self.root = Path(directory.name).resolve()
   114	        git(self.root, "init", "-q", "-b", "main")
   115	        for relative, text in {
   116	            f"{EPIC}/demo.en.md": HLD,
   117	            f"{EPIC}/bdd_scenarios.en.md": SCENARIOS,
   118	            ".gitignore": "build/\n",
   119	            "tests/test_demo.py": DEMO_TEST,
   120	            f"{EPIC}/{TASK}.md": TASK_TEXT,
   121	            f".devtool/features/{TASK}.md": TASK_TEXT,
   122	        }.items():
   123	            path = self.root / relative
   124	            path.parent.mkdir(parents=True, exist_ok=True)
   125	            path.write_text(text, encoding="utf-8")
   126	        git(self.root, "add", "-A")
   127	        git(self.root, "commit", "-q", "-m", "base")
   128	        git(self.root, "checkout", "-q", "-b", "epic/demo")
   129	
   130	    def step(self, script: str, *args: str) -> str:
   131	        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}  # bytecode would be an untracked change outside Allowed files
   132	        done = subprocess.run([sys.executable, str(SCRIPTS / script), *args], cwd=self.root,
   133	                              capture_output=True, text=True, env=env)
   134	        self.assertEqual(done.returncode, 0, f"{script} {' '.join(args)}\n{done.stdout}\n{done.stderr}")
   135	        return done.stdout
   136	
   137	    def test_vth_hp_11_design_to_audit_every_step_exits_0(self) -> None:
   138	        mirror = f"{EPIC}/{TASK}.md"
   139	        self.step("check_task_contract.py", "--design", "--hld", f"{EPIC}/demo.en.md", "--tasks", mirror)
   140	        self.step("check_bdd_traceability.py", "plan", "--scenarios", f"{EPIC}/bdd_scenarios.en.md",
   141	                  "--tasks", mirror)
   142	        self.step("run_task_checks.py", "red", mirror)
   143	        (self.root / "feature.txt").write_text("feature\n", encoding="utf-8")
   144	        self.step("run_task_checks.py", "verify", mirror)
   145	        self.step("sync_task_status.py", "task", TASK, "done")
   146	        git(self.root, "add", "-A")
   147	        git(self.root, "commit", "-q", "-m", "[DEMO] Task 1")
   148	        report = self.step("audit_epic.py", "--epic-dir", "demo", "--base", "main")
   149	        self.assertIn("Result: PASS", report)
   150	
    15	from dataclasses import dataclass
    16	from pathlib import Path
    17	
    18	from check_bdd_traceability import covers_of
    19	from result_reports import Case, verdicts
    20	
    21	PHASES = ("RED", "GREEN", "TIER-B", "TIER-C")
    22	HEADER = ["ID", "Phase", "Command", "Expect", "Needs"]
    23	NONE_CELL = ("—", "-")
    24	FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
    25	EXIT_CLAUSE = re.compile(r"exit (?:(\d+)|non-zero)")
    26	CLAUSE = re.compile(r'; (?:contains "([^"]*)"|results (\S+))')
    27	NEEDS_NAME = re.compile(r"[A-Z_][A-Z0-9_]*")
    28	ROW_ID = re.compile(r"V[0-9]+")
    29	CODE_SPAN = re.compile(r"`([^`]+)`")
    30	RED_NA = re.compile(r"^RED:\s*n/a\s*[—-]\s*(.+?)\s*$")
    31	ALLOWED_BULLET = re.compile(r"^- `([^`]+)`( \(new\))?\s*$")
    32	ENVIRONMENT_HEADING = re.compile(r"^## (?:\d+\.\s*)?Verification Environment\s*$")
    33	INTERPRETERS = {"python", "python3", "bash", "sh", "zsh", "node", "deno", "ruby", "perl"}
    34	CONTROL_TOKENS = {"&&", "||", ";", "|"}
    35	EXCLUDE_DEVTOOL = ":(exclude).devtool"
    36	DIFF_PLAIN = ("--no-ext-diff", "--no-color")  # user diff settings must not change a patch id
    37	DOD_REFERENCE = re.compile(r"\((V[0-9]+(?:,\s*V[0-9]+)*|Gate 5)\)\.?\s*$")
    38	
    39	
    40	class ContractError(Exception):

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_epic_readiness.py | sed -n '383,445p;620,684p'; nl -ba skills/dev-implementation/resources/scripts/check_task_contract.py | sed -n '270,315p'; nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '30,65p'; nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '570,610p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   383	def check_grounding(ctx: Context) -> list[Finding]:
   384	    findings: list[Finding] = []
   385	
   386	    # --- R5: Symbol Grounding ---
   387	    target_header_re = re.compile(
   388	        r"^\s*-\s*\*\*(?:Target Files & Symbols|Target files and symbols)\*\*:\s*(.*)$",
   389	        re.IGNORECASE,
   390	    )
   391	    sub_bullet_re = re.compile(r"^\s*-\s+`([^`]+)`:\s*(.*)$")
   392	    token_re = re.compile(r"`([^`]+)`")
   393	    ident_re = re.compile(r"^[A-Za-z_][\w.]*(?:\(\))?$")
   394	
   395	    for task_path, task_text in ctx.tasks.items():
   396	        impact_body = tc.section(task_text, "Impact Analysis & Blast Radius")
   397	        if not impact_body:
   398	            for heading in (
   399	                "Impact Analysis & Blast Radius",
   400	                "Impact analysis & blast radius",
   401	                "Impact Analysis and Blast Radius",
   402	            ):
   403	                impact_body = tc.section(task_text, heading)
   404	                if impact_body:
   405	                    break
   406	        if not impact_body:
   407	            continue
   408	
   409	        allowed_files = tc.parse_allowed_files(task_text)
   410	        new_patterns = {ap.pattern for ap in allowed_files if ap.new}
   411	
   412	        in_target_symbols = False
   413	        target_lines: list[str] = []
   414	        for line in impact_body.splitlines():
   415	            if target_header_re.match(line):
   416	                in_target_symbols = True
   417	                continue
   418	            if in_target_symbols:
   419	                if re.match(r"^\s*-\s+\*\*", line) or (line.startswith("- ") and not line.startswith("  - ")):
   420	                    break
   421	                target_lines.append(line)
   422	
   423	        for line in target_lines:
   424	            sub_m = sub_bullet_re.match(line)
   425	            if not sub_m:
   426	                continue
   427	            path_str = sub_m.group(1).strip()
   428	            rest = sub_m.group(2)
   429	
   430	            full_path = ctx.root / path_str
   431	            if not full_path.is_file() or path_str in new_patterns:
   432	                continue
   433	
   434	            try:
   435	                file_text = full_path.read_text(encoding="utf-8", errors="ignore")
   436	            except OSError:
   437	                continue
   438	
   439	            for span_m in token_re.finditer(rest):
   440	                token_raw = span_m.group(1).strip()
   441	                if not ident_re.match(token_raw):
   442	                    continue
   443	                prefix = rest[:span_m.start()]
   444	                if re.search(r"\bnew\s+$", prefix):
   445	                    continue
   620	def check_baseline(ctx: Context) -> list[Finding]:
   621	    if not ctx.baseline:
   622	        return []
   623	
   624	    status_proc = subprocess.run(
   625	        ["git", "status", "--porcelain"],
   626	        check=False,
   627	        cwd=ctx.root,
   628	        capture_output=True,
   629	        text=True,
   630	    )
   631	    if status_proc.stdout.strip():
   632	        return [Finding("R8", "WARN", "baseline skipped: dirty tree")]
   633	
   634	    findings: list[Finding] = []
   635	
   636	    new_paths: set[str] = set()
   637	    for t_text in ctx.tasks.values():
   638	        for ap in tc.parse_allowed_files(t_text):
   639	            if ap.new:
   640	                new_paths.add(ap.pattern)
   641	
   642	    for task_path, task_text in ctx.tasks.items():
   643	        try:
   644	            rows, _ = tc.parse_verification(task_text)
   645	        except tc.ContractError:
   646	            continue
   647	
   648	        for row in rows:
   649	            if row.phase not in ("GREEN", "TIER-B"):
   650	                continue
   651	
   652	            if any(np in row.command for np in new_paths):
   653	                continue
   654	
   655	            code, raw_output = rtc.run_command(row.command, ctx.root, ctx.row_timeout)
   656	            if code is None:
   657	                findings.append(
   658	                    Finding(
   659	                        "R8",
   660	                        "WARN",
   661	                        f"{task_path.stem}:{row.id} timeout after {ctx.row_timeout}s",
   662	                    )
   663	                )
   664	            else:
   665	                out_text = raw_output.decode("utf-8", errors="replace")
   666	                mis = rtc.mismatch(row, code, out_text)
   667	                if mis is not None:
   668	                    findings.append(Finding("R8", "WARN", f"{task_path.stem}:{row.id} {mis}"))
   669	
   670	    return findings
   671	
   672	
   673	CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...] = (
   674	    ("R1", check_preflight),
   675	    ("R2", check_task_mirrors),
   676	    ("R3", check_bdd_scenarios),
   677	    ("R4", check_tier_tags),
   678	    ("R5", check_grounding),
   679	    ("R6", check_gate4_coverage),
   680	    ("R7", check_metadata),
   681	    ("R8", check_baseline),
   682	)
   683	
   684	
   270	        if first in ("mypy", "pyright", "ty") or any(t in ("mypy", "pyright", "ty") for t in tokens):
   271	            has_type_checker = True
   272	
   273	    if not has_ruff or not has_type_checker:
   274	        missing_tools: list[str] = []
   275	        if not has_ruff:
   276	            missing_tools.append("lint (ruff)")
   277	        if not has_type_checker:
   278	            missing_tools.append("type-check (mypy/pyright/ty)")
   279	        check.problem(f"{stem}:Verification", f"Python task requires TIER-B direct {', '.join(missing_tools)}")
   280	
   281	
   282	def check_weak_bdd(check: Checker, source_name: str, text: str) -> None:
   283	    for line_num, line in enumerate(text.splitlines(), start=1):
   284	        m = WEAK_ASSERTION_RE.search(line)
   285	        if m:
   286	            check.problem(f"{source_name}:{line_num}", f"weak BDD assertion found: {m.group(0)!r}")
   287	
   288	
   289	def check_task(check: Checker, path: Path, text: str, design: bool, created: set[str]) -> None:
   290	    stem = path.stem
   291	    rows = table_rows(check, stem, text)
   292	    check_structure(check, stem, path, text, rows)
   293	    for row in rows:
   294	        if row.expect.results and not check.ignored(row.expect.results):
   295	            check.problem(f"{stem}:{row.id}", f"results path {row.expect.results} is not ignored by git")
   296	        check_pytest_k(check, stem, row)
   297	    check_weak_bdd(check, stem, text)
   298	    status = STATUS.search(text.split("\n---", 1)[0]) if text.startswith("---") else None
   299	    if design or not (status and status.group(1) == "done"):
   300	        if is_python_task(text, rows):
   301	            check_python_tier_b(check, stem, rows)
   302	        check_allowed(check, stem, text, design)
   303	        check_grounding(check, stem, text, rows, created)
   304	
   305	
   306	def check_hld(check: Checker, hld_path: Path, text: str, tasks: dict[Path, str]) -> None:
   307	    name = hld_path.name
   308	    if not tc.parse_protected_paths(text):
   309	        check.problem(name, "no Protected paths: line")
   310	    results = tc.parse_integration_results(text)
   311	    if not results:
   312	        check.problem(name, "no Integration results: line")
   313	    for entry in results:
   314	        command, arrow, report = entry.rpartition(" -> ")
   315	        if not arrow or not command.strip() or not report.strip():
    30	FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
    31	COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")
    32	ID_TOKEN = re.compile(r"(?<![A-Za-z0-9-])" + ID_SHAPE.pattern + r"(?![A-Za-z0-9])")
    33	
    34	
    35	class UsageError(Exception):
    36	    """Missing input: exit 2."""
    37	
    38	
    39	def read_text(path: Path) -> str:
    40	    """Read a scenario document or task file; anything but UTF-8 is a usage error."""
    41	    try:
    42	        return path.read_text(encoding="utf-8")
    43	    except UnicodeDecodeError:
    44	        raise UsageError(f"{path} is not valid UTF-8") from None
    45	
    46	
    47	def scenario_ids(path: Path) -> tuple[list[str], list[str]]:
    48	    """Identifiers in document order, and the problems found, for one scenario document."""
    49	    ids: list[str] = []
    50	    problems: list[str] = []
    51	    fence_marker: str | None = None
    52	    in_gherkin = False
    53	    for number, line in enumerate(read_text(path).splitlines(), start=1):
    54	        fence = FENCE.match(line)
    55	        if fence and fence_marker is None:
    56	            fence_marker, in_gherkin = fence.group(1), fence.group(2).lower() == "gherkin"
    57	            continue
    58	        if (fence and fence.group(1)[0] == fence_marker[0]
    59	                and len(fence.group(1)) >= len(fence_marker) and not fence.group(2)):
    60	            fence_marker, in_gherkin = None, False
    61	            continue
    62	        match = SCENARIO_LINE.match(line) if in_gherkin else None
    63	        if not match:
    64	            continue
    65	        tag = LEADING_TAG.match(match.group(1).strip())
   570	
   571	        # Missing directory exits 2
   572	        code2, _stdout2, stderr2 = self.run_check("nonexistent_epic_dir")
   573	        self.assertEqual(code2, 2, f"Expected 2 for nonexistent dir, got {code2}")
   574	        self.assertTrue(stderr2.strip() != "", "Expected stderr output for nonexistent dir")
   575	
   576	
   577	class ReadinessGroundingTest(unittest.TestCase):
   578	    def setUp(self) -> None:
   579	        self.temp_dir = tempfile.TemporaryDirectory()
   580	        self.addCleanup(self.temp_dir.cleanup)
   581	        self.root = Path(self.temp_dir.name).resolve()
   582	
   583	        git_cmd(self.root, "init", "-q")
   584	        git_cmd(self.root, "config", "user.email", "tester@example.com")
   585	        git_cmd(self.root, "config", "user.name", "Tester")
   586	
   587	        build_ready_epic(self.root)
   588	
   589	    def run_check(self, *args: str, cwd: Path | None = None) -> tuple[int, str, str]:
   590	        run_cwd = cwd or self.root
   591	        proc = subprocess.run(
   592	            [sys.executable, str(SCRIPT_PATH), *args],
   593	            check=False,
   594	            cwd=run_cwd,
   595	            capture_output=True,
   596	            text=True,
   597	        )
   598	        return proc.returncode, proc.stdout, proc.stderr
   599	
   600	    def update_task_both(self, task_name: str, updater: Any) -> None:
   601	        epic_file = self.root / ".devtool" / "epic" / "demo_epic" / task_name
   602	        feat_file = self.root / ".devtool" / "features" / task_name
   603	        text = epic_file.read_text(encoding="utf-8")
   604	        new_text = updater(text)
   605	        epic_file.write_text(new_text, encoding="utf-8")
   606	        feat_text = new_text.replace("](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)")
   607	        feat_file.write_text(feat_text, encoding="utf-8")
   608	
   609	    def test_prv_ec_01_symbol_missing_from_file_fails_r5(self) -> None:
   610	        """PRV-EC-01: A symbol missing from its file fails R5."""

exec
/bin/zsh -lc "rg -n '"'^`{4,}'"' skills/dev-designer skills/dev-implementation skills/principal-review docs | head -45; rg -n '"'^`{4,}'"' skills | head -55; nl -ba skills/dev-designer/SKILL.md | sed -n '315,345p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:131:````bash
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:188:````
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:424:````bash
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:472:````
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:792:````bash
docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md:840:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1530:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1532:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1536:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1542:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1546:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1548:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1552:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1566:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1570:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1577:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1581:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1589:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1593:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1609:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1613:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1626:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1630:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1632:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1636:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1641:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1645:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1673:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1677:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1759:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1763:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1765:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1769:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1773:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1777:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1783:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1787:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1794:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1798:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1805:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1809:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1816:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1820:````markdown
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1822:````
docs/superpowers/plans/2026-10-09-finishing-branch-rebase.vi.md:1826:````markdown
skills/writing-plans/SKILL.md:135:````markdown
skills/writing-plans/SKILL.md:194:````
skills/writing-skills/anthropic-best-practices.md:32:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:43:````
skills/writing-skills/anthropic-best-practices.md:92:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:103:````
skills/writing-skills/anthropic-best-practices.md:115:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:125:````
skills/writing-skills/anthropic-best-practices.md:271:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:293:````
skills/writing-skills/anthropic-best-practices.md:311:````markdown SKILL.md theme={null}
skills/writing-skills/anthropic-best-practices.md:330:````
skills/writing-skills/anthropic-best-practices.md:418:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:454:````
skills/writing-skills/anthropic-best-practices.md:460:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:499:````
skills/writing-skills/anthropic-best-practices.md:606:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:626:````
skills/writing-skills/anthropic-best-practices.md:630:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:649:````
skills/writing-skills/anthropic-best-practices.md:655:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:689:````
skills/writing-skills/anthropic-best-practices.md:838:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:849:````
skills/writing-skills/anthropic-best-practices.md:932:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:961:````
skills/writing-skills/anthropic-best-practices.md:967:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:977:````
skills/writing-skills/anthropic-best-practices.md:1077:````markdown  theme={null}
skills/writing-skills/anthropic-best-practices.md:1089:````
   315	>    - Subagent 2's integration flow tests initially act as **ATDD Red Tests** (failing while Subagent 1's code is in-flight).
   316	>    - Once both subagents report completion, the Lead Agent performs the **Sync Checkpoint**: merges the branches, validates that the integration tests turn **GREEN**, and runs the Tier C acceptance check.
   317	
   318	Task files are English-only — do not generate a `.vi.md` variant for `task_*.md` and do not mix
   319	Vietnamese prose into their section headers or body. They are the sole language-pair exception in
   320	this workflow; the spec, Epic Overview, and BDD scenario documents remain bilingual.
   321	
   322	Each task file MUST adhere to this exact structure:
   323	
   324	1. **YAML Frontmatter (LachyFS Kanban Markdown compatible)**:
   325	   ```yaml
   326	   ---
   327	   id: "task_<number>_<name>"
   328	   status: "todo"          # one of: backlog | todo | in-progress | review | done — see Concurrent-Epic Backlog Rule above
   329	   priority: "high"        # one of: low | medium | high
   330	   assignee: null
   331	   epic: "<epic_name>"
   332	   dueDate: null
   333	   created: "<ISO-8601 timestamp, set once at creation>"
   334	   modified: "<ISO-8601 timestamp, update on every edit>"
   335	   completedAt: null       # set to an ISO-8601 timestamp only when status becomes "done"
   336	   labels: ["architecture", "feature"]
   337	   order: "a<number>"
   338	   ---
   339	   ```
   340	2. **Title**: `# Task <number>: <Task Name>`
   341	3. **Epic Reference**: A link back to the parent HLD, e.g. `Epic: [<epic_name>](../epic/<epic_name>/<epic_name>.en.md)`. This is the agent's entry point back to architecture/diagram context.
   342	4. **Requirement Analysis**: Context and requirements specific to this task.
   343	5. **Files**: A `## Files` section holding two lists.
   344	   - `Allowed files:` lists the exact paths or globs (`*`, `?`, and `**` across directories) the task may create, change or delete. A path that does not exist yet carries `(new)`. Bare directories are not allowed. Changes under `.devtool/` (task status, mirrors, evidence) are never listed, except changes to a protected path.
   345	   - `Read-only context:` lists the paths the task only reads, each with a note. It restricts nothing, and a path that another task creates may carry `(new)`.

exec
/bin/zsh -lc "nl -ba skills/writing-plans/SKILL.md | sed -n '128,201p'; nl -ba skills/dev-implementation/resources/scripts/test_check_task_contract.py | sed -n '245,280p'; nl -ba skills/dev-implementation/resources/scripts/test_run_task_checks.py | sed -n '465,485p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   128	include this section.]
   129	
   130	---
   131	```
   132	
   133	## Task Structure
   134	
   135	````markdown
   136	### Task N: [Component Name]
   137	
   138	**Files:**
   139	- Create: `exact/path/to/file.py`
   140	- Modify: `exact/path/to/existing.py:123-145`
   141	- Test: `tests/exact/path/to/test.py`
   142	
   143	**Interfaces:**
   144	- Consumes: [what this task uses from earlier tasks — exact signatures]
   145	- Produces: [what later tasks rely on — exact function names, parameter
   146	  and return types. A task's implementer sees only their own task; this
   147	  block is how they learn the names and types neighboring tasks use.]
   148	
   149	- [ ] **Step 1: Write the failing test**
   150	
   151	```python
   152	def test_specific_behavior():
   153	    result = function(input)
   154	    assert result == expected
   155	```
   156	
   157	- [ ] **Step 2: Run test to verify it fails**
   158	
   159	Run: `pytest tests/path/test.py::test_name -v`
   160	Expected: FAIL with "function not defined"
   161	
   162	- [ ] **Step 3: Write minimal implementation**
   163	
   164	```python
   165	def function(input):
   166	    return expected
   167	```
   168	
   169	- [ ] **Step 4: Run test to verify it passes**
   170	
   171	Run: `pytest tests/path/test.py::test_name -v`
   172	Expected: PASS
   173	
   174	- [ ] **Step 5: Integration & Edge Case Test (if touching workflows/data/APIs)**
   175	
   176	Write & run integration test exercising multi-component flow and boundary edge cases (empty payload, timeout, error fallback):
   177	Run: `npm test tests/integration/test_flow.test.ts` (or `pytest tests/integration/...`)
   178	Expected: PASS with 100% boundary coverage
   179	
   180	- [ ] **Step 6: Live Web Browser Verification (for Web / UI Tasks)**
   181	
   182	Launch preview/dev server and dispatch `browser_subagent` to verify live behavior:
   183	1. Open URL `http://localhost:<port>/<route>`
   184	2. Test user interaction flow, click controls, verify state transitions
   185	3. Save video recording (`.webp`) and capture screenshot artifact
   186	4. Assert expected DOM text and zero console exceptions
   187	
   188	- [ ] **Step 7: Commit**
   189	
   190	```bash
   191	git add tests/path/test.py src/path/file.py
   192	git commit -m "[SCOPE] Add specific feature" -m "- <what this step changed>"
   193	```
   194	````
   195	
   196	## No Placeholders
   197	
   198	Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
   199	- `TBD`, `TODO`, "implement later", "fill in details"
   200	- "Add appropriate error handling" / "add validation" / "handle edge cases"
   201	- "Write tests for the above" (without actual test code)
   245	        self.assertEqual(code, 1)
   246	        self.assertIn("task_1_a:V5: Needs UNNAMED_VAR is not named in the Verification Environment section", out)
   247	        self.assertIn("demo.en.md: Integration results path out/all.xml is not ignored by git", out)
   248	        self.assertIn("demo.en.md: Integration results line is not <command> -> <path>: no arrow here", out)
   249	
   250	    def test_unnumbered_verification_environment_heading_is_accepted(self) -> None:
   251	        self.write(f"{EPIC}/demo.en.md", HLD.replace("## 6. Verification", "## Verification"))
   252	        code, out, _ = self.check(self.task("1_a"))
   253	        self.assertEqual(code, 0, out)
   254	
   255	
   256	class UsageTest(ContractCase):
   257	    def test_vth_fr_04_an_unreadable_task_exits_2_with_the_reason_on_stderr(self) -> None:
   258	        self.commit()
   259	        code, out, err = self.run_cli("--hld", f"{EPIC}/demo.en.md", "--tasks", f"{EPIC}/task_9_gone.md")
   260	        self.assertEqual(code, 2)
   261	        self.assertIn("task_9_gone.md", err)
   262	        self.assertEqual(out, "")
   263	
   264	    def test_vth_fr_04_a_missing_argument_exits_2(self) -> None:
   265	        code, _, err = self.run_cli("--hld", f"{EPIC}/demo.en.md")
   266	        self.assertEqual(code, 2)
   267	        self.assertIn("--tasks", err)
   268	
   269	    def test_vth_fr_04_a_directory_outside_any_git_repository_exits_2(self) -> None:
   270	        with tempfile.TemporaryDirectory() as outside:
   271	            os.chdir(Path(outside).resolve())
   272	            code, _, err = self.run_cli("--hld", "hld.md", "--tasks", "task.md")
   273	        self.assertEqual(code, 2)
   274	        self.assertIn("git repository", err)
   275	
   276	
   277	class PythonTierBAndFastModelTest(ContractCase):
   278	    def test_mvls_hp_03_python_task_with_lint_and_type_check_passes(self) -> None:
   279	        """[MVLS-HP-03] Python task with ruff and mypy TIER-B rows passes."""
   280	        task = self.task("1_py", allowed="- `tool.py`",
   465	        self.assertEqual(self.run_cli("red", task)[0], 2)
   466	
   467	    def test_vth_fr_05_unparseable_task_exits_two_and_writes_no_evidence(self) -> None:
   468	        task = self.epic("| V1 | GREEN | `true` | — |\n",
   469	                         head="| ID | Phase | Command | Needs |\n|--|--|--|--|\n")
   470	        code, _, err = self.run_cli("verify", task)
   471	        self.assertEqual(code, 2)
   472	        self.assertIn("Expect", err)
   473	        self.assertFalse((self.root / EVIDENCE).exists())
   474	
   475	    def test_mirror_outside_the_epic_directory_exits_two(self) -> None:
   476	        self.epic("| V1 | GREEN | `true` | exit 0 | — |\n")
   477	        features = self.write(".devtool/features/task_1_demo.md", task_text("| V1 | GREEN | `true` | exit 0 | — |\n"))
   478	        code, _, err = self.run_cli("verify", features)
   479	        self.assertEqual(code, 2)
   480	        self.assertIn("pass the task's mirror under", err)
   481	
   482	    def test_usage_errors_exit_two(self) -> None:
   483	        self.assertEqual(self.run_cli("verify")[0], 2)
   484	        self.assertEqual(self.run_cli("verify", self.root / "nope.md")[0], 2)
   485	

exec
/bin/zsh -lc "python3 -B -c 'import sys,re
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,\"skills/dev-implementation/resources/scripts\")
import task_contract as tc
import run_task_checks as rtc
import check_bdd_traceability as cb
payload=Path(\"skills/writing-plans/SKILL.md\").read_text()
for n in (4,5):
    rendered=\"# Task\\n\\n## Steps\\n\\n\"+\"\\x60\"*n+\"markdown\\n\"+payload+\"\\n\"+\"\\x60\"*n+\"\\n\\n## Verification\\n\\nEXPECTED_VERIFICATION\\n\"
    print(\"embed existing writing-plans with outer fence\",n, \"=> Verification =\",repr(tc.section(rendered,\"Verification\")))
for cmd, code, output in [(\"python3 -m pytest tests/sample.py::test_ok\",0,\"1 passed\"),(\"python3 -m pytest tests/sample.py::missing\",4,\"ERROR: not found\"),(\"python3 -m pytest tests/sample.py::test_ok\",1,\"1 failed\")]:
    print(\"actual pytest RED validation\",code,repr(output),\"=>\",rtc.validate_pytest_red(cmd,code,output))
with patch.object(cb,\"read_text\",side_effect=UnicodeDecodeError(\"utf-8\",b\"\\xff\",0,1,\"probe\")):
    try: cb.read_text(Path(\"not-read\"))
    except UnicodeDecodeError: print(\"patched boundary only; no filesystem read\")
# Probe actual UTF-8 fallback with mocked Path.read_text.
with patch.object(Path,\"read_text\",side_effect=UnicodeDecodeError(\"utf-8\",b\"\\xff\",0,1,\"probe\")):
    try: cb.read_text(Path(\"not-read\"))
    except Exception as e: print(\"UTF-8 early fallback =>\",type(e).__name__,str(e))
# Demonstrate token rules on an actual parsed command; no subprocess execution.
import check_task_contract as cc
p=re.compile(r\"(?:/Users/|/home/|~/|\\.claude/plugins/cache/|\\.gemini/config/plugins/)\")
for cmd in [\"grep -F /Users/ README.md\",\"python3 /Users/alice/tool.py\"]:
    print(\"frozen portability regex\",repr(cmd),\"=>\",p.findall(cmd))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
embed existing writing-plans with outer fence 4 => Verification = '\nEXPECTED_VERIFICATION'
embed existing writing-plans with outer fence 5 => Verification = '\nEXPECTED_VERIFICATION'
actual pytest RED validation 0 '1 passed' => Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), not missing file (exit 4) or zero selected tests (exit 5).
actual pytest RED validation 4 'ERROR: not found' => Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), not missing file (exit 4) or zero selected tests (exit 5).
actual pytest RED validation 1 '1 failed' => None
patched boundary only; no filesystem read
UTF-8 early fallback => UsageError not-read is not valid UTF-8
frozen portability regex 'grep -F /Users/ README.md' => ['/Users/']
frozen portability regex 'python3 /Users/alice/tool.py' => ['/Users/']

exec
/bin/zsh -lc "rg -n '"'^def |fence'"' skills/doc_quality_check/resources/scripts/check_document.py | head -45; nl -ba docs/superpowers/plans/2026-10-15-epic-handoff-choice.en.md | sed -n '182,203p'; nl -ba skills/dev-implementation/resources/scripts/test_check_epic_readiness.py | sed -n '1,65p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
43:def strip_code(text: str) -> str:
44:    """Blank out fenced blocks and inline code spans, preserving line numbering.
49:    out, fenced = [], False
52:            fenced = not fenced
55:        out.append("" if fenced else re.sub(r"`[^`]*`", "", line))
59:def anchor(heading: str) -> str:
65:def check_file(path: pathlib.Path, require_toc: bool = False) -> list:
77:    fences = sum(1 for ln in raw_lines if ln.lstrip().startswith("```"))
78:    if fences % 2:
79:        findings.append((path, 0, f"unbalanced code fences ({fences} found)"))
82:    fence_len = 0
83:    fence_lang = ""
91:        # Check for code fence start/end
92:        m_fence = re.match(r"^(?P<fence>`{3,}|~{3,})(?P<lang>\S*)", lstripped)
93:        if m_fence:
94:            cur_len = len(m_fence.group("fence"))
95:            if fence_len == 0:
96:                # Opening fence
97:                fence_len = cur_len
98:                fence_lang = m_fence.group("lang").lower()
99:                if not fence_lang:
100:                    findings.append((path, i, "fenced code block missing language tag (MD040)"))
104:            elif cur_len >= fence_len and not m_fence.group("lang"):
105:                # Closing fence
106:                fence_len = 0
107:                fence_lang = ""
113:        if fence_len == 0:
119:        # Inside code blocks (fence_len > 0)
120:        if fence_lang == "mermaid":
139:        elif fence_lang in ("dot", "graphviz"):
182:def check_language_pairs(paths: list[pathlib.Path]) -> list:
210:def heading_structure(path: pathlib.Path) -> list[int]:
217:def refusal(changed: list) -> list:
228:def main() -> int:
   182	
   183	  - Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
   184	  - This handoff does not pass Gate 3. The developer confirms the execution order.
   185	  - If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
   186	  - This file is a dated record. It is never updated after packaging.
   187	EOF
   188	````
   189	
   190	Check: `head -1 skills/dev-lifecycle/references/handoff-template.md` prints `# Handoff: <epic_slug>`.
   191	
   192	- [ ] **Step 4: Edit skills/dev-lifecycle/SKILL.md**
   193	
   194	Apply these nine edits. Every anchor occurs exactly once.
   195	
   196	A — in the mermaid diagram under The Sequence, insert directly after this line:
   197	
   198	```markdown
   199	    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
   200	```
   201	
   202	The new text:
   203	
     1	#!/usr/bin/env python3
     2	"""Tests for check_epic_readiness.py (Task 1: Readiness Check Core).
     3	
     4	Run:
     5	    python3 -m unittest skills/dev-implementation/resources/scripts/test_check_epic_readiness.py -k ReadinessCoreTest
     6	"""
     7	from __future__ import annotations
     8	
     9	import subprocess
    10	import sys
    11	import tempfile
    12	import unittest
    13	from pathlib import Path
    14	from typing import Any
    15	
    16	SCRIPTS_DIR = Path(__file__).resolve().parent
    17	SCRIPT_PATH = SCRIPTS_DIR / "check_epic_readiness.py"
    18	
    19	# Try importing the module under test
    20	try:
    21	    import check_epic_readiness
    22	except ImportError:
    23	    check_epic_readiness = None  # type: ignore[assignment]
    24	
    25	
    26	def git_cmd(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    27	    return subprocess.run(
    28	        ["git", "-C", str(root), *args],
    29	        capture_output=True,
    30	        text=True,
    31	        check=True,
    32	    )
    33	
    34	
    35	def build_ready_epic(root: Path) -> None:
    36	    """Writes the PRV-HP-01 epic demo_epic (slug demo-epic, 2 tasks) into root.
    37	
    38	    Commits nothing related to the epic.
    39	    """
    40	    # Ensure baseline repo tracked files exist and are committed
    41	    tracked = subprocess.run(
    42	        ["git", "-C", str(root), "ls-files", "tool.py"],
    43	        check=False,
    44	        capture_output=True,
    45	        text=True,
    46	    ).stdout.strip()
    47	    if not tracked:
    48	        (root / "tool.py").write_text("def run():\n    pass\n", encoding="utf-8")
    49	        (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    50	        (root / "scripts").mkdir(parents=True, exist_ok=True)
    51	        (root / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    52	        (root / ".gitignore").write_text("build/\n", encoding="utf-8")
    53	        git_cmd(root, "add", "tool.py", "README.md", "scripts/verify.sh", ".gitignore")
    54	        git_cmd(root, "commit", "-m", "initial commit", "-q")
    55	
    56	    epic_dir = root / ".devtool" / "epic" / "demo_epic"
    57	    features_dir = root / ".devtool" / "features"
    58	    epic_dir.mkdir(parents=True, exist_ok=True)
    59	    features_dir.mkdir(parents=True, exist_ok=True)
    60	
    61	    # 1. Spec pair
    62	    spec_en = """# Demo Epic Design
    63	
    64	## Table of Contents
    65	

exec
/bin/zsh -lc "python3 -B -c 'import sys,importlib.util
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,\"skills/dev-implementation/resources/scripts\")
import task_contract as tc
# A valid file containing a four-backtick block and an internal heading.
payload=\"\\x60\\x60\\x60\\x60markdown\\n\\x60\\x60\\x60python\\npass\\n\\x60\\x60\\x60\\n\\x60\\x60\\x60\\x60\\n\\n## Reference\\nText\\n\"
# Observe the existing document checker'\\''s fence state on the exact prescribed wrapping.
spec=importlib.util.spec_from_file_location(\"doccheck\",\"skills/doc_quality_check/resources/scripts/check_document.py\")
doccheck=importlib.util.module_from_spec(spec)
spec.loader.exec_module(doccheck)
for width in (4,5):
    wrapped=\"# Task\\n\\n## Steps\\n\\n\"+\"\\x60\"*width+\"markdown\\n\"+payload+\"\\x60\"*width+\"\\n\\n## Verification\\n\\nEXPECTED\\n\"
    with patch.object(Path,\"read_text\",return_value=wrapped):
        findings=doccheck.check_file(Path(\"in-memory.md\"))
    print(\"nested fence width\",width,\"=>\",[(n,msg) for _,n,msg in findings])
# More direct marker-scope probe with legal plain four-backtick code inside Markdown.
payload2=\"\\x60\"*4+\"\\n## Verification\\nEMBEDDED\\n\"+\"\\x60\"*4+\"\\n\"
for width in (4,5):
    wrapped=\"# Task\\n\\n## Steps\\n\\n\"+\"\\x60\"*width+\"markdown\\n\"+payload2+\"\\x60\"*width+\"\\n\\n## Verification\\n\\nEXPECTED\\n\"
    print(\"actual section on nested plain fences\",width,\"=>\",repr(tc.section(wrapped,\"Verification\")))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
nested fence width 4 => [(14, 'fenced code block missing language tag (MD040)')]
nested fence width 5 => []
actual section on nested plain fences 4 => 'EMBEDDED\n````\n````\n'
actual section on nested plain fences 5 => '\nEXPECTED'

exec
/bin/zsh -lc "python3 -B -c 'import sys,importlib.util
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location(\"doccheck\",\"skills/doc_quality_check/resources/scripts/check_document.py\")
dc=importlib.util.module_from_spec(spec);spec.loader.exec_module(dc)
payload=Path(\"skills/writing-plans/SKILL.md\").read_text()
for width in (4,5):
    wrapped=\"# Task\\n\\n## Steps\\n\\n\"+\"\\x60\"*width+\"markdown\\n\"+payload+\"\\n\"+\"\\x60\"*width+\"\\n\\n## Verification\\n\\nEXPECTED\\n\"
    with patch.object(Path,\"read_text\",return_value=wrapped):
        print(\"existing writing-plans embed\",width,\"=>\",[(n,msg) for _,n,msg in dc.check_file(Path(\"in-memory.md\"))][:10])
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
existing writing-plans embed 4 => [(258, 'fenced code block missing language tag (MD040)')]
existing writing-plans embed 5 => []

exec
/bin/zsh -lc "nl -ba skills/doc_quality_check/resources/scripts/check_document.py | sed -n '89,108p'; /Library/Developer/CommandLineTools/usr/bin/git -c core.fsmonitor=false status --short --untracked-files=no" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
    89	        lstripped = rline.lstrip()
    90	
    91	        # Check for code fence start/end
    92	        m_fence = re.match(r"^(?P<fence>`{3,}|~{3,})(?P<lang>\S*)", lstripped)
    93	        if m_fence:
    94	            cur_len = len(m_fence.group("fence"))
    95	            if fence_len == 0:
    96	                # Opening fence
    97	                fence_len = cur_len
    98	                fence_lang = m_fence.group("lang").lower()
    99	                if not fence_lang:
   100	                    findings.append((path, i, "fenced code block missing language tag (MD040)"))
   101	                in_flowchart = False
   102	                in_digraph = False
   103	                continue
   104	            elif cur_len >= fence_len and not m_fence.group("lang"):
   105	                # Closing fence
   106	                fence_len = 0
   107	                fence_lang = ""
   108	                in_flowchart = False

codex
Các probe bổ sung xác nhận quy tắc cố định “nâng fence lên 4 backticks” vẫn làm hỏng nội dung khi file nhúng đã chứa fence 4 backticks; trường hợp này có sẵn trong kit. Tôi đã thu hẹp review còn các vấn đề ảnh hưởng trực tiếp đến tính đúng đắn và khả năng hoàn thành task theo thứ tự đã duyệt.

codex
Four issues need correction before implementation.

1. **Mirror rewriting conflicts with readiness and completed-task locations.** Task 02’s “Decisions Already Made” (line 109) rewrites both `file.md` and `./file.md` to `../epic/<epic>/file.md`. However, [check_epic_readiness.py:202](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_epic_readiness.py:202) normalizes only that prefix, leaving `file.md` unequal to the original `./file.md`. An in-memory probe of the actual R2 function confirmed failure. Additionally, that prefix resolves beneath `.devtool/features/epic/` when used from `features/done/`. Task 02 currently lists the readiness implementation as read-only. Proposed: define location-aware rewriting and common normalization, permit the necessary readiness changes in Task 02, and test both link spellings in both board locations.

2. **Task 01 requires functionality delivered by its dependent task.** Its `Covers:` line and DoD require `TCAE-EC-01`, whose canonical scenario explicitly executes `sync_task_status.py render`. Task 02 introduces that command and depends on Task 01. The candidate’s [sync_task_status.py:504](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/sync_task_status.py:504) registers the existing subcommands without `render`, and Task 01 cannot modify that file. Faithful scenario coverage therefore cannot pass before Task 02. Proposed: move `TCAE-EC-01` ownership and acceptance coverage to Task 02, updating the corresponding task blocks and mirrors.

3. **Fixed four-backtick promotion does not safely embed supported Markdown files.** Task 02 freezes four backticks whenever embedded content contains triple backticks. Existing [writing-plans/SKILL.md:135](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/writing-plans/SKILL.md:135) already contains a four-backtick block. Wrapping that actual file in the prescribed fence and invoking the existing document checker in memory produced an MD040 finding; five backticks passed. The checker closes a fence when an unlabelled delimiter is at least as long as its opener ([check_document.py:104](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/doc_quality_check/resources/scripts/check_document.py:104)). Proposed: choose an outer fence longer than every potentially closing backtick run in the payload, retaining four as the minimum promotion, and update the bilingual specification and acceptance cases.

4. **Task 05 mandates a failing RED test for behavior already required to pass.** V1 expects the evidence-transition test to fail after Tasks 01–04 have delivered that behavior. Task 05 permits only its new test file and an unrelated typing correction, leaving no planned behavioral implementation to turn that failure green. The real [RED validator:119](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_task_checks.py:119) rejects both an already-passing test and a missing test; read-only probes confirmed both outcomes. Proposed: make this an acceptance-only task with a justified `RED: n/a`, retaining GREEN and integration verification.

Early-error probes also exercised parsing, file-read failure, and timeout handlers without exposing an unbound-variable failure.

Verdict: CHANGES REQUIRED
[Important] task_02_single_source_render_engine.md:Decisions Already Made — Link rewriting breaks ./ link parity and done-directory targets. Proposed: use location-aware rewriting and shared normalization, with readiness changes allowed in Task 02.
[Important] task_01_evidence_files_contract.md:BDD SCENARIOS and Definition of Done — TCAE-EC-01 requires the renderer introduced by dependent Task 02. Proposed: move this scenario and its acceptance coverage to Task 02.
[Important] task_02_single_source_render_engine.md:Decisions Already Made — Fixed four-backtick wrapping breaks embedded files containing four-backtick fences. Proposed: select a delimiter longer than payload fence runs and synchronize specifications and tests.
[Important] task_05_end_to_end_contract_acceptance.md:Verification V1 — Mandatory RED failure conflicts with already-delivered evidence-transition behavior and the permitted changes. Proposed: replace V1 with justified RED: n/a acceptance-task handling.
tokens used
139,825
`````
