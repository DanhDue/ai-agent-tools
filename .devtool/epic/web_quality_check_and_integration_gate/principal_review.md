# Principal Review: web_quality_check_and_integration_gate

## Round 1

- **Date**: 2026-11-04T19:46:15Z
- **SHA**: c88539eeb74257e43fa573a3271ea2351931848e
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_01_web_quality_check_skill_and_contract.md:Decisions Already Made | The frozen output includes forbidden top-level `summary` and omits eight required v1 fields. The canonical [schema](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/quality_check/resources/schemas/provider-result.schema.json:5) requires these fields; executing the existing validator with the frozen payload returned BLOCKED with profile, duration, and SHA-drift findings. Proposed: Replace the frozen output definition with the complete canonical result schema and require the contract test to validate and reconcile the actual emitted document. | fixed in fa7db71 |
| 2 | Important | web_quality_check_and_integration_gate.en.md:Integration Test Plan and Boundary Matrix; 2026-11-04-web-quality-check-and-integration-gate-design.en.md:Dev-Designer and Dev-Implementation Enhancements | The HLD command does not request creation of `pytest.xml`, while the spec mandates Playwright JSON, which the current [report reader](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/result_reports.py:83) interprets as Dart events. An active probe returned zero cases for a passing Playwright JSON report. Gate 4 explicitly consumes these reports for [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/SKILL.md:270). Proposed: Add `--junitxml=build/test-results/pytest.xml` to the HLD command and standardize browser evidence on the existing supported Playwright JUnit configuration. | fixed in fa7db71 |
| 3 | Important | task_05_anti_rationalization_and_doubt_driven_workflow.md:BDD SCENARIOS / Files | WQG-ST-02 promises mechanical rejection of mock-only completion, but Allowed files permit only skill text and a new test. Existing [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:157) matches identifiers, and the [done gate](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/task_contract.py:439) judges recorded case statuses. Probes accepted a mock-only test reference and its passing result. Proposed: Define the semantic auditor responsible for rejection, wire its verdict into completion gating, authorize the affected production files, and test that actual rejection path. | fixed in fa7db71 |
| 4 | Important | task_04_polyglot_gate4_registry_and_fanout.md:Requirement Analysis / Files | The promised consumer registration has no executable adoption path. The existing [scaffolder](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py:244) generates configurations from `PLATFORM_CONFIGS`, without loading the proposed template; a read-only dry-run probe rejected platform `web`. Neither scaffolder changes nor consumer adoption handoffs are assigned. Proposed: Authorize and specify web scaffolder integration, capability-manifest generation, and separate repository-owned adoption handoffs covering registry entries, watchdog attachment, and verification commands. | fixed in fa7db71 |
| 5 | Important | task_06_automated_manual_smoke_checklist_generator.md:Requirement Analysis / BDD SCENARIOS | Generating the checklist after Gate 4 PASS creates an unignored file under the tracked epic directory. `git check-ignore` confirmed this path is not ignored, and the [review runner](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:805) rejects dirty trees. Committing afterward changes the certified candidate SHA. Proposed: Generate and commit the checklist before resolving the final candidate SHA, then run full Gate 4 before presenting Review Choice. | fixed in fa7db71 |
| 6 | Important | task_06_automated_manual_smoke_checklist_generator.md:Decisions Already Made / WQG-HP-04 | The generator must extract URLs and visual outcomes from arbitrary Happy Paths, but its supplied canonical BDD contains provider/compiler workflows without target URLs or structured manual-step metadata. The executor must invent information or fail the frozen requirement. Proposed: Define explicit smoke metadata containing a URL or CLI command, action, and observable outcome; specify behavior when metadata is absent; and align the scenario and generator contract accordingly. | fixed in fa7db71 |

Raw output:

````text
Six implementation blockers remain. I reviewed all 13 artefacts against `c88539eeb74257e43fa573a3271ea2351931848e`. Read-only probes confirmed the contract and report incompatibilities below; Git remained clean.

Artefact paths below are relative to `.devtool/epic/web_quality_check_and_integration_gate/`. Apply corresponding changes to EN/VI mirrors.

Verdict: CHANGES REQUIRED
[Important] task_01_web_quality_check_skill_and_contract.md:Decisions Already Made — The frozen output includes forbidden top-level `summary` and omits eight required v1 fields. The canonical [schema](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/quality_check/resources/schemas/provider-result.schema.json:5) requires these fields; executing the existing validator with the frozen payload returned BLOCKED with profile, duration, and SHA-drift findings. Proposed: Replace the frozen output definition with the complete canonical result schema and require the contract test to validate and reconcile the actual emitted document.
[Important] web_quality_check_and_integration_gate.en.md:Integration Test Plan and Boundary Matrix; 2026-11-04-web-quality-check-and-integration-gate-design.en.md:Dev-Designer and Dev-Implementation Enhancements — The HLD command does not request creation of `pytest.xml`, while the spec mandates Playwright JSON, which the current [report reader](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/result_reports.py:83) interprets as Dart events. An active probe returned zero cases for a passing Playwright JSON report. Gate 4 explicitly consumes these reports for [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/SKILL.md:270). Proposed: Add `--junitxml=build/test-results/pytest.xml` to the HLD command and standardize browser evidence on the existing supported Playwright JUnit configuration.
[Important] task_05_anti_rationalization_and_doubt_driven_workflow.md:BDD SCENARIOS / Files — WQG-ST-02 promises mechanical rejection of mock-only completion, but Allowed files permit only skill text and a new test. Existing [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:157) matches identifiers, and the [done gate](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/task_contract.py:439) judges recorded case statuses. Probes accepted a mock-only test reference and its passing result. Proposed: Define the semantic auditor responsible for rejection, wire its verdict into completion gating, authorize the affected production files, and test that actual rejection path.
[Important] task_04_polyglot_gate4_registry_and_fanout.md:Requirement Analysis / Files — The promised consumer registration has no executable adoption path. The existing [scaffolder](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py:244) generates configurations from `PLATFORM_CONFIGS`, without loading the proposed template; a read-only dry-run probe rejected platform `web`. Neither scaffolder changes nor consumer adoption handoffs are assigned. Proposed: Authorize and specify web scaffolder integration, capability-manifest generation, and separate repository-owned adoption handoffs covering registry entries, watchdog attachment, and verification commands.
[Important] task_06_automated_manual_smoke_checklist_generator.md:Requirement Analysis / BDD SCENARIOS — Generating the checklist after Gate 4 PASS creates an unignored file under the tracked epic directory. `git check-ignore` confirmed this path is not ignored, and the [review runner](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:805) rejects dirty trees. Committing afterward changes the certified candidate SHA. Proposed: Generate and commit the checklist before resolving the final candidate SHA, then run full Gate 4 before presenting Review Choice.
[Important] task_06_automated_manual_smoke_checklist_generator.md:Decisions Already Made / WQG-HP-04 — The generator must extract URLs and visual outcomes from arbitrary Happy Paths, but its supplied canonical BDD contains provider/compiler workflows without target URLs or structured manual-step metadata. The executor must invent information or fail the frozen requirement. Proposed: Define explicit smoke metadata containing a URL or CLI command, action, and observable outcome; specify behavior when metadata is absent; and align the scenario and generator contract accordingly.



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
session id: 01a1a815-6968-7a52-b890-8b4f94461a2e
--------
user
# Principal Review Prompt

You are the Principal Reviewer who signs off this architectural design before implementation. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the source at `c88539eeb74257e43fa573a3271ea2351931848e`, and report.

## Candidate

- Commit under review: `c88539eeb74257e43fa573a3271ea2351931848e`
- Base the branch diverged from: `main`
- Base commit: `c88539eeb74257e43fa573a3271ea2351931848e`
- Target path / Epic directory: `.devtool/epic/web_quality_check_and_integration_gate`

## Artefacts

Read these paths, relative to the repository root:

- `.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md`
- `.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.vi.md`
- `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md`
- `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.vi.md`
- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md`
- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_01_web_quality_check_skill_and_contract.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_02_playwright_zero_error_watchdog.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_03_jsconfig_and_vanilla_js_type_checker.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_04_polyglot_gate4_registry_and_fanout.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_05_anti_rationalization_and_doubt_driven_workflow.md`
- `.devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md`
- `.devtool/epic/web_quality_check_and_integration_gate/handoff.md`

## Readiness facts

Epic: web_quality_check_and_integration_gate (web-quality-check-and-integration-gate), 6 tasks
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
Tôi sẽ dùng `d3nexus:principal-review` để đối chiếu bộ thiết kế với mã nguồn tại commit đã chỉ định, cùng `d3nexus:task-observer` để theo dõi quy trình. Mọi thao tác sẽ chỉ đọc; tôi sẽ tập trung vào rủi ro kiến trúc và các probe cần thiết.

exec
/bin/zsh -lc 'cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.23.0/skills/task-observer/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.23.0/skills/principal-review/SKILL.md /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.23.0/skills/using-superpowers/references/codex-tools.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
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
/bin/zsh -lc "rg -n 'web_quality|principal|quality.*contract|Gate 4' /Users/danhdueexoictif/antigravity_homes/peter/.codex/memories/MEMORY.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
1:# Task Group: ai-agent-tools setup_shared_contracts principal contract review
10:- rollout_summaries/2026-10-30T06-59-12-Elg4-principal_review_setup_shared_contracts_contract_drift.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08.jsonl, updated_at=2026-10-29T23:08:05+00:00, thread_id=01a18b9a-faa7-7f50-81b9-b3c8aa8e3a08, `CHANGES REQUIRED`; later review verified these four findings were fixed)
14:- setup_shared_contracts, principal-review, shared_contracts_readme.md.tmpl, string.Template, `{{DOMAIN_NAME}}`, --root, --repo-root, --satellite-root, scripts/verify.sh, Section 11, Section 14, contract drift
20:- rollout_summaries/2026-10-30T06-59-12-zvna-principal_review_setup_shared_contracts_contract_contradicti.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/30/rollout-2026-10-30T13-59-12-01a18b9a-faa8-72e0-8192-3dd403258730.jsonl, updated_at=2026-10-29T23:26:36+00:00, thread_id=01a18b9a-faa8-72e0-8192-3dd403258730, `CHANGES REQUIRED`; current implementation-blocking finding)
24:- setup_shared_contracts, principal-review, SSC-FR-03, shared-contracts, non-empty, symlink, Rule 7, `Covers:`, traceability, `python3 -m unittest`, CHANGES REQUIRED
28:- When requesting a principal review, the user required a “strictly read-only review” with exact source file/line grounding, artefact-specific actionable findings, and an exact final verdict block -> do not edit files or Git state; cite concrete locations for each source claim. [Task 1][Task 2]
32:- Related skill: skills/principal-contract-review/SKILL.md. [Task 1][Task 2]
152:- Keep `Scenario:` entries inside parser-compatible fenced Gherkin blocks; otherwise BDD traceability fails. Record absent `ruff`, `mypy`, and `.agents/quality/check_quality.json` as Stage 3 blockers rather than weakening contracts or claiming a quality PASS. [Task 1]
195:- Corrected execution graph is `521 -> 522 -> 527 -> 523 -> 528 -> 524 -> 529 -> 525 -> 526` (9 tasks, 7 layers, acyclic). Package validation: document quality `0 findings`, BDD `43/43 covered — PASS`, task contract `0 problems — PASS`, task mirrors byte-identical; commit `4cef42e`. Required quality commands remain `cargo run -p xtask -- pre-commit`, `cargo run -p xtask -- check-boundaries`, and `just acceptance`. [Task 2]
203:# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics
208:## Task 1: Reposition Review Choice into a Gate 4 loop, success
216:- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088
230:- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
235:- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
236:- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
242:- A first regression failed because normative files still said Review Choice occurred before Gate 4. Do not make a flowchart-only edit: synchronize rules, both skills, diagrams, English/Vietnamese docs, lifecycle-selection docs, and negative assertions. [Task 1]
347:- Package/preflight success is not production readiness: no implementation tests, live browser evidence, or Gate 4 quality profile ran. Before implementation, read the handoff, present execution order, and wait for explicit Gate 3 confirmation. [Task 2]
349:# Task Group: D3Nexus design_system Gate 4 evidence review and lifecycle concurrency
351:scope: Gate 4 review of a web-heavy epic: evidence completeness, fail-closed verdicts, stable-SHA reruns, and lifecycle race protection.
354:## Task 1: Review design_system Gate 4 readiness, partial
367:- The workflow was expected to stop at Gate 4 and not finish/merge automatically -> preserve strict gate separation; a passing subset is not approval for Gate 5. [Task 1]
371:- Gate 4 requires BDD traceability plus the complete provider profile; precedence is `FAIL > BLOCKED > PASS`, so one `FAIL` prevents LGTM. [Task 1]
373:- The registered quality plan currently contains only `rust-core`; for a web-heavy epic this is a governance coverage gap, though not an independent aggregate failure under the current contract. [Task 1]
374:- Candidate identity can be invalidated while Gate 4 runs if another workflow archives tasks, merges the branch, deletes the worktree, or changes HEAD. A repository-scoped transition lease plus HEAD/worktree revalidation before each provider capability is the needed guard. [Task 1]
381:- Manual web tests cannot establish Gate 4 PASS when the registered provider plan does not reconcile them; record that limitation, retain raw screenshots/video/command outputs before cleanup or merge, then rerun the whole profile. [Task 1]
396:- lyrics_lexical_normalization, Gate 3, Gate 4, handoff.md, BDD traceability, database isolation, Gemini, DeepSeek, backfill, e1f4cfc, c1657ae, Dependencies & Blockers
408:- Task 43 is the safety prerequisite: establish an isolated PostgreSQL namespace and prove the live catalog fingerprint remains unchanged before full pytest or coverage. Gate 4 needs the same immutable candidate SHA, complete registered `epic` profile, raw artifacts, BDD/test traceability, browser evidence at 390x844 and 1440x900, authorized provider provenance/canary evidence, and an independent catalog audit. [Task 1]
535:- rust-quality-check, Gate-4, C1-C7, false-PASS, validate_quality_contract.py, aggregate_quality_results.py, check-boundaries, exit 0/1/75
664:- vocab_learning_app, doc_quality_check, Diataxis, bilingual, Mermaid, contract-map, learner-journeys, 649024e, develop

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
> 1. **Mandatory Context Restoration on Session Startup**:
>    - At the start of any new session or account switch, the AI Agent MUST run `python3 scripts/resume_context.py` (or the `d3nexus:resume-context` skill) to restore architectural memory before answering or proposing solutions.
>    - The agent MUST summarize the restored project context in 5–10 concise bullets for the developer.
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
/bin/zsh -lc "sed -n '203,245p' /Users/danhdueexoictif/antigravity_homes/peter/.codex/memories/MEMORY.md; cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.23.0/skills/principal-review/references/principal-review-rules.md" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
# Task Group: ai-agent-tools Gate 4 Review Choice loop and external-review diagnostics

scope: Verified lifecycle state-machine update and streamed external-review precondition reporting.
applies_to: cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools; reuse_rule=inspect current lifecycle rules/skills and candidate SHA before reuse; flow is repository policy, not a generic shortcut around gates.

## Task 1: Reposition Review Choice into a Gate 4 loop, success

### rollout_summary_files

- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, committed and fully verified)

### keywords

- Gate 4, Review Choice, Cross-model review, Gate 5, SHA-bound, rules/CRITICAL_RULES.md, test_verifiable_handoff_text.py, df9f67af7c1f7fecd3b4a9768c0863d035ed3088

## Task 2: Add realtime ANSI pre-check output to external review, success

### rollout_summary_files

- rollout_summaries/2026-10-18T10-39-52-b3XU-gate4_review_choice_loop_and_external_review_streaming.md (cwd=/Users/danhdueexoictif/AllProjects/ai-agent-tools, rollout_path=/Users/danhdueexoictif/.codex/sessions/2026/10/18/rollout-2026-10-18T17-39-52-01a14e98-b2b9-7043-9d17-65dd8df4be46.jsonl, updated_at=2026-10-18T15:23:36+00:00, thread_id=01a14e98-b2b9-7043-9d17-65dd8df4be46, 31 targeted tests and full verification passed)

### keywords

- run_external_review.py, run_gate, PreconditionFailedError, [PRECONDITION BLOCKED], ANSI, flush=True, audit_epic.py, check_bdd_traceability.py, scripts/verify.sh, android-ui-audit

## User preferences

- The user explicitly corrected the lifecycle sequence: “Gate 4 => Review Choice”, then “Finish” or “Cross model review”, and “Sau bước này chạy lại Gate 4 ... Loop cho tới khi finish.” -> preserve this order for similar ai-agent-tools lifecycle work. [Task 1]
- After verification, the user asked “Commit and finish all tasks.” -> commit locally when requested, but do not push without explicit permission. [Task 1]

## Reusable knowledge

- Enforced invariant: `Gate 4 PASS -> Review Choice; Finish -> Gate 5; Cross-model review -> Gate 4 in full`. A review round, decision, Fix commit, Gate 5-requested change, cross-model CLI failure, or timeout that changes/reassesses the candidate requires full Gate 4 before another Review Choice. Gate 4 is SHA-bound. [Task 1]
- The policy update touched `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, bilingual lifecycle docs, lifecycle-selection docs, and `scripts/test_verifiable_handoff_text.py`; commit `df9f67af7c1f7fecd3b4a9768c0863d035ed3088` is `[REVIEW_WORKFLOW] Loop review choice through Gate 4`. [Task 1]
- `run_gate()` emits `[Pre-check]`, `PASS`, `FAILED`, or `TIMEOUT` to stderr with `flush=True`. `PreconditionFailedError` holds `gate`, `reason`, and `details`; its banner shows the final 25 detail lines and confirms the selected CLI was not invoked. [Task 2]
- Route `audit_epic.py`, declared Integration commands, and `check_bdd_traceability.py` through `run_gate()` while retaining captured output in the facts bundle. `run_external_review.py` does not directly invoke `android-ui-audit`; that is only indirect through the quality-provider registry. Targeted suite passed 31 tests and `scripts/verify.sh` reported `PASS — safe to publish`; worktree was clean on `main`, with no push. [Task 2]

## Failures and how to do differently

- A first regression failed because normative files still said Review Choice occurred before Gate 4. Do not make a flowchart-only edit: synchronize rules, both skills, diagrams, English/Vietnamese docs, lifecycle-selection docs, and negative assertions. [Task 1]

# Task Group: D3Nexus contextual flashcard sharing platform package and nexus mobile handoff

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

exec
/bin/zsh -lc "git rev-parse HEAD; git status --short; git show -s --format='%H %s' c88539eeb74257e43fa573a3271ea2351931848e; rg --files .devtool/epic/web_quality_check_and_integration_gate; rg --files -g AGENTS.md -g '*quality*' skills/quality_check skills/python-quality-check skills/setup_quality_check scripts" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 4635ms:
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-me3Qk59y' (errno=Operation not permitted)
2026-11-05 02:42:32.664 xcodebuild[34500:252126]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:32.889 xcodebuild[34500:252125] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-6H2J0Z8e' (errno=Operation not permitted)
2026-11-05 02:42:33.339 xcodebuild[34502:252143]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:33.445 xcodebuild[34502:252142] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
c88539eeb74257e43fa573a3271ea2351931848e
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-pS4p49Fb' (errno=Operation not permitted)
2026-11-05 02:42:34.321 xcodebuild[34511:252177]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:34.428 xcodebuild[34511:252176] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Yxyo4rGK' (errno=Operation not permitted)
2026-11-05 02:42:34.796 xcodebuild[34513:252185]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:34.901 xcodebuild[34513:252184] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-YDv6LdB3' (errno=Operation not permitted)
2026-11-05 02:42:35.736 xcodebuild[34518:252203]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:35.841 xcodebuild[34518:252202] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-q5wILINA' (errno=Operation not permitted)
2026-11-05 02:42:36.217 xcodebuild[34520:252212]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-11-05 02:42:36.322 xcodebuild[34520:252210] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
c88539eeb74257e43fa573a3271ea2351931848e [SETTINGS] Normalize epic slug resolution and isolate profile test environment
.devtool/epic/web_quality_check_and_integration_gate/task_02_playwright_zero_error_watchdog.md
.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md
.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.vi.md
.devtool/epic/web_quality_check_and_integration_gate/task_03_jsconfig_and_vanilla_js_type_checker.md
.devtool/epic/web_quality_check_and_integration_gate/handoff.md
.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md
.devtool/epic/web_quality_check_and_integration_gate/task_04_polyglot_gate4_registry_and_fanout.md
.devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md
.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.vi.md
.devtool/epic/web_quality_check_and_integration_gate/task_05_anti_rationalization_and_doubt_driven_workflow.md
.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md
.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md
.devtool/epic/web_quality_check_and_integration_gate/task_01_web_quality_check_skill_and_contract.md
skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py
skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py
skills/python-quality-check/resources/fixtures/valid_python_quality.json
skills/python-quality-check/resources/schemas/python-quality.schema.json
skills/python-quality-check/resources/scripts/validate_python_quality.py
skills/python-quality-check/resources/scripts/test_validate_python_quality.py
skills/quality_check/resources/scripts/test_aggregate_quality_results.py
skills/quality_check/resources/schemas/check-quality.schema.json
skills/quality_check/resources/scripts/aggregate_quality_results.py
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py
skills/quality_check/resources/scripts/validate_quality_contract.py
skills/quality_check/resources/scripts/test_validate_quality_contract.py

exec
/bin/zsh -lc 'wc -l .devtool/epic/web_quality_check_and_integration_gate/*.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     144 .devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md
     145 .devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.vi.md
     105 .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md
     106 .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md
      74 .devtool/epic/web_quality_check_and_integration_gate/handoff.md
     115 .devtool/epic/web_quality_check_and_integration_gate/task_01_web_quality_check_skill_and_contract.md
     114 .devtool/epic/web_quality_check_and_integration_gate/task_02_playwright_zero_error_watchdog.md
      94 .devtool/epic/web_quality_check_and_integration_gate/task_03_jsconfig_and_vanilla_js_type_checker.md
      93 .devtool/epic/web_quality_check_and_integration_gate/task_04_polyglot_gate4_registry_and_fanout.md
      95 .devtool/epic/web_quality_check_and_integration_gate/task_05_anti_rationalization_and_doubt_driven_workflow.md
      93 .devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md
     162 .devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md
     162 .devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.vi.md
    1502 total
     1	# Web Quality Check and Integration Gate Design Spec
     2	
     3	## Table of Contents
     4	
     5	- [Metadata](#metadata)
     6	- [Problem Statement and Context](#problem-statement-and-context)
     7	- [Goals and Non-Goals](#goals-and-non-goals)
     8	- [Architecture and 3-Tier Testing Standard](#architecture-and-3-tier-testing-standard)
     9	- [Anti-Rationalization and Doubt-Driven Verification](#anti-rationalization-and-doubt-driven-verification)
    10	- [Web Quality Provider Specification](#web-quality-provider-specification)
    11	- [Multi-Repo Registry and Polyglot Gate 4 Integration](#multi-repo-registry-and-polyglot-gate-4-integration)
    12	- [Dev-Designer and Dev-Implementation Enhancements](#dev-designer-and-dev-implementation-enhancements)
    13	- [Automated Smoke Walkthrough Generation](#automated-smoke-walkthrough-generation)
    14	- [Risks and Mitigations](#risks-and-mitigations)
    15	- [Verification Plan](#verification-plan)
    16	
    17	## Metadata
    18	
    19	- **Epic Name**: `web_quality_check_and_integration_gate`
    20	- **Epic Slug**: `web-quality-check-and-integration-gate`
    21	- **Date**: 2026-11-04
    22	- **Author**: Human Architect & AI Assistant
    23	- **Status**: Approved Spec (Gate 1 Passed)
    24	- **Target Repositories**: `ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`
    25	
    26	## Problem Statement and Context
    27	
    28	In our multi-repository ecosystem (`D3Nexus`, `lyrics-sync`, `nexus`), developers experience a significant gap between theoretical architectural design and real runtime behavior. This gap forces human engineers to conduct extensive manual testing (bấm tay) on devices and browsers for every release:
    29	
    30	1. **The Mocking Fallacy**: Unit tests in `[Tier A - Unit]` achieve 100% green pass rates by isolating components with mock objects (`when(...).thenReturn(...)`). However, the application crashes or breaks when components are wired together at runtime due to DI registration failures, JSON serialization mismatches, lifecycle cancellation, or event-bus stream race conditions.
    31	2. **Missing Web Quality Provider in Gate 4**: The quality orchestration system (`d3nexus:quality_check`) has dedicated providers for Flutter, Android, iOS, Rust, and Python, but completely lacks a `web-quality-check` provider. Consequently:
    32	   - In `D3Nexus`, Gate 4 only verifies `rust-core` (`d3nexus:rust-quality-check`), leaving the Astro + Vanilla TypeScript web application (`apps/learning-web`) completely unverified.
    33	   - In `lyrics-sync`, Gate 4 only verifies `python-core` (`d3nexus:python-quality-check`), leaving the 17 Vanilla JavaScript files (`src/lyrics_sync/preview/static/*.js`) unverified.
    34	3. **Simulated Node-Only E2E Tests**: Many tests located under `tests/e2e/` run in `node:test` without rendering real HTML, without testing Custom Element connections, and without verifying DOM events or browser layout geometries (`getBoundingClientRect`).
    35	4. **AI Rationalization**: AI coding agents routinely rationalize shortcuts: asserting tests in pure Node, ignoring browser console errors, and avoiding headless browser execution.
    36	
    37	## Goals and Non-Goals
    38	
    39	### Goals
    40	- Create a standardized `web-quality-check` provider implementing Provider Result Contract v1 for Astro TypeScript and Vanilla JavaScript projects.
    41	- Eliminate blind spots in Gate 4 by enabling polyglot multi-provider registration in `D3Nexus` (`rust-core` + `learning-web`) and `lyrics-sync` (`python-core` + `preview-ui`).
    42	- Enforce a strict 3-Tier Testing Standard: Tier A (Unit), Tier C1 (Subcutaneous Integration with real DI and in-memory DB), and Tier C2 (Headless Browser Integration with Playwright and Zero-Console-Error).
    43	- Embed Anti-Rationalization Tables and Doubt-Driven Verification (inspired by `addyosmani/agent-skills`) into skill workflows.
    44	- Automate human verification by generating a concise 3-5 step `manual_smoke_checklist.md` at epic completion, reducing manual exploratory testing time from 30 minutes to 2 minutes.
    45	
    46	### Non-Goals
    47	- Migrating Vanilla JavaScript files in `lyrics-sync` to TypeScript (type checking is achieved in-place via JSDoc `// @ts-check` and `jsconfig.json`).
    48	- Replacing existing unit test suites in `D3Nexus` or `lyrics-sync` (existing fast unit tests remain as Tier A).
    49	- Requiring heavy device emulators for local PR/Epic gates (Tier C tests run headless via Playwright and subcutaneous VM harnesses).
    50	
    51	## Architecture and 3-Tier Testing Standard
    52	
    53	The architecture establishes three distinct testing tiers across mobile and web platforms:
    54	
    55	1. **Tier A — Unit Testing**:
    56	   - Scope: Pure algorithms, mathematical state machines, standalone data parsers, and helper functions.
    57	   - Execution: In-process (Node.js, Dart VM, JVM, Python VM).
    58	   - Mocking: External dependencies may be mocked. Speed: <10ms per test.
    59	2. **Tier C1 — Subcutaneous Integration Testing (Mobile & Backend)**:
    60	   - Scope: Presentation controllers (BLoC / ViewModel) down to local database storage, caching, and serialization.
    61	   - Invariant: Zero-Domain-Mock. Mocking domain UseCases or Repositories is strictly prohibited. Real DI containers and in-memory databases (SQLite `:memory:`, Room in-memory) are required.
    62	   - Network Boundary: Network I/O is mocked at the HTTP wire socket using canonical JSON fixtures from `shared-contracts/`.
    63	3. **Tier C2 — Headless Browser Integration Testing (Web)**:
    64	   - Scope: Real DOM rendering, Custom Elements, Vanilla JS/TS controllers, user clicks, navigation, and visual popover placement.
    65	   - Invariant: Zero-Console-Error. Any `console.error` or uncaught page exception immediately fails the test.
    66	   - Network Boundary: Mocked at the browser socket via Playwright `page.route()` returning canonical contract JSON fixtures.
    67	
    68	## Anti-Rationalization and Doubt-Driven Verification
    69	
    70	Drawing from the principles of `addyosmani/agent-skills`, all coding and testing workflows enforce four anti-rationalization rules:
    71	
    72	| Agent Rationalization | Enforced Counter-Rule |
    73	| :--- | :--- |
    74	| "A Node.js test is sufficient to prove this web UI feature works." | **REJECTED**: Node tests prove only pure data logic. 80% of web defects occur in DOM queries, event bubbling, and CSS rendering. Tier C requires headless Playwright execution. |
    75	| "This component is simple; hardcoding mock data in a stub is enough." | **REJECTED**: Method-level stubs bypass JSON deserialization and network interceptors. Wire-level fixtures from `shared-contracts/` are mandatory. |
    76	| "The red errors in the browser console are just harmless warnings." | **REJECTED**: The Zero-Console-Error rule fails Gate 4 on any browser console error or uncaught exception. |
    77	| "I cannot launch a mobile simulator, so I will write a unit test instead." | **REJECTED**: Mobile Tier C requires Subcutaneous Testing with real DI and in-memory persistence. Pure unit tests cannot be tagged as Tier C. |
    78	
    79	Under Doubt-Driven Verification (`CLAIM -> EXTRACT -> DOUBT -> RECONCILE`), Gate 4 audits tests to confirm that Tier C tests actually exercise production code paths without mocking the primary system under test.
    80	
    81	## Web Quality Provider Specification
    82	
    83	A new skill `d3nexus:web-quality-check` is authored in `skills/web-quality-check/`:
    84	
    85	1. **Invocation Contract**: Conforms to Provider Result Contract v1, accepting `{ "profile": "<profile>", "base_ref": "<base_ref>", "repository_sha": "<sha>" }`.
    86	2. **Configuration File**: Reads `.agents/quality/web-quality.json` from the repository root.
    87	3. **Capabilities**:
    88	   - `type_check`: Runs `astro check` or `tsc --noEmit` for TypeScript projects, or `tsc --project jsconfig.json` for Vanilla JavaScript projects.
    89	   - `lint`: Runs project linter (ESLint, Biome, or Astro linter).
    90	   - `test_unit`: Executes fast in-memory unit tests (Tier A).
    91	   - `test_e2e`: Launches headless Playwright suites (Tier C2) with the Zero-Console-Error watchdog.
    92	   - `contracts`: Runs cross-repo contract diff verification.
    93	4. **Validation Tooling**: Provides `validate_web_quality.py` to ensure schema conformance and executable presence before execution.
    94	
    95	## Multi-Repo Registry and Polyglot Gate 4 Integration
    96	
    97	The root Gate 4 orchestrator (`d3nexus:quality_check`) executes multi-provider fan-out across repositories:
    98	
    99	- **`D3Nexus` (`.agents/quality/check_quality.json`)**:
   100	  - Provider 1: `rust-core` (`d3nexus:rust-quality-check`) for Rust core, WASM compilation, and system tests.
   101	  - Provider 2: `learning-web` (`d3nexus:web-quality-check`) for Astro templates, Vanilla TypeScript controllers, and Playwright suites.
   102	- **`lyrics-sync` (`.agents/quality/check_quality.json`)**:
   103	  - Provider 1: `python-core` (`d3nexus:python-quality-check`) for FastAPI endpoints, worker logic, and pytest suites.
   104	  - Provider 2: `preview-ui` (`d3nexus:web-quality-check`) for static Vanilla JS type checking and Chrome Playwright tests.
   105	- **`nexus` (`.agents/quality/check_quality.json`)**:
   106	  - Provider 1: `flutter-core` (`d3nexus:flutter-quality-check`) enforcing Subcutaneous Widget Testing with real DI and WireMock.
   107	
   108	## Dev-Designer and Dev-Implementation Enhancements
   109	
   110	1. **`dev-designer` (Stage 2)**:
   111	   - When detecting a Web project, the HLD `Integration results:` line must target Playwright headless output (`build/test-results/playwright.json`).
   112	   - BDD scenarios for Tier C must include concrete DOM interaction expectations and wiremock assertions.
   113	2. **`dev-implementation` (Stage 3)**:
   114	   - Integrates the Anti-Rationalization Table into task execution.
   115	   - Validates that tasks claiming Tier C scenario coverage execute real headless browser or subcutaneous tests.
   116	   - Halts and reports `BLOCKED` if test code mocks the component under test.
   117	
   118	## Automated Smoke Walkthrough Generation
   119	
   120	Upon successful completion of all tasks and a passing Gate 4 machine verdict, `dev-implementation` automatically generates a human-oriented verification artifact:
   121	- Path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
   122	- Content: 3 to 5 concise, actionable manual steps extracted directly from the primary BDD Happy Path scenarios (e.g. Target URL, user action, observable visual outcome).
   123	- Benefit: Reduces developer exploratory testing from 30 minutes of unstructured wandering to a 2-minute deterministic confirmation.
   124	
   125	## Risks and Mitigations
   126	
   127	| Risk | Impact | Mitigation Strategy |
   128	| :--- | :--- | :--- |
   129	| Playwright installation overhead in CI / local dev | Slow Gate 4 runs | Use headless Chromium only; cache browser binaries; profile `pr` runs unit tests, profile `epic` runs Playwright. |
   130	| Port conflicts when launching preview servers | Test flakiness | Playwright `webServer` configuration binds to dynamic or dedicated ports with healthcheck probes. |
   131	| Existing legacy console warnings triggering Zero-Console-Error | False positive failures | Allow an explicit, documented allowlist of benign vendor warnings in `.agents/quality/web-quality.json`. |
   132	
   133	## Verification Plan
   134	
   135	1. **Provider Contract Verification**:
   136	   - Run `validate_web_quality.py` against `.agents/quality/web-quality.json` sample configurations.
   137	   - Execute `quality_check` with profile `epic` in `D3Nexus` and verify both `rust-core` and `learning-web` produce certified verdicts.
   138	2. **Playwright Zero-Console-Error Verification**:
   139	   - Inject an intentional `console.error` into a test page; confirm that Playwright and Gate 4 correctly report `FAIL`.
   140	   - Resolve the error and confirm Gate 4 transitions to `PASS`.
   141	3. **Vanilla JS Type-Checking Verification**:
   142	   - Run `tsc --project jsconfig.json` against `lyrics-sync/src/lyrics_sync/preview/static/` and verify clean type validation.
   143	4. **Smoke Checklist Generation Verification**:
   144	   - Verify that completing an epic produces `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` containing 3-5 structured steps.
     1	# Epic: Web Quality Check Provider and Integration Quality Gate
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
    21	- **Epic Name**: `web_quality_check_and_integration_gate`
    22	- **Epic Slug**: `web-quality-check-and-integration-gate`
    23	- **Status**: Packaged
    24	- **Target Release**: v1.2.0
    25	- **Platform**: Polyglot / Quality Architecture
    26	- **Source Spec**: [2026-11-04-web-quality-check-and-integration-gate-design.en.md](./2026-11-04-web-quality-check-and-integration-gate-design.en.md)
    27	
    28	## Background
    29	
    30	In our multi-repository ecosystem (`D3Nexus`, `lyrics-sync`, `nexus`), developers experience a significant gap between design specifications and actual runtime behavior. This gap forces human engineers to conduct extensive manual testing on devices and browsers for every release:
    31	- Unit tests pass with 100% green mocks, but fail at runtime due to real DI registration errors, serialization bugs, and DOM event wiring defects.
    32	- Gate 4 (`quality_check`) lacks a web provider, leaving `D3Nexus` (`apps/learning-web`) and `lyrics-sync` (17 Vanilla JS preview files) completely unverified.
    33	- AI coding agents frequently rationalize shortcuts by avoiding headless browser tests and ignoring browser console errors.
    34	
    35	## Goals and Non-Goals
    36	
    37	### Goals
    38	- Deliver the `web-quality-check` provider implementing Provider Result Contract v1 for Astro TypeScript and Vanilla JavaScript projects.
    39	- Enable multi-provider polyglot quality orchestration at Gate 4 across `D3Nexus` and `lyrics-sync`.
    40	- Enforce the 3-Tier Testing Standard (Tier A Unit, Tier C1 Subcutaneous Mobile/Backend, Tier C2 Headless Browser Web).
    41	- Embed Anti-Rationalization Tables and Doubt-Driven Verification from `addyosmani/agent-skills` into skill workflows.
    42	- Automatically generate a concise 3-5 step `manual_smoke_checklist.md` upon epic completion to reduce manual verification time from 30 minutes to 2 minutes.
    43	
    44	### Non-Goals
    45	- Migrating Vanilla JS files in `lyrics-sync` to TypeScript (type checking is done in-place via JSDoc and `jsconfig.json`).
    46	- Rewriting existing fast unit tests.
    47	- Forcing full mobile emulators into local PR/Epic quality check gates.
    48	
    49	## Architecture and Technical Design
    50	
    51	### High-Level Architecture
    52	
    53	```mermaid
    54	flowchart TD
    55	    QC["Gate 4: quality_check (Platform-Neutral Orchestrator)"] --> REG["Load .agents/quality/check_quality.json"]
    56	    REG --> FANOUT{"Fan-Out Selected Providers"}
    57	    FANOUT --> P_RUST["rust-quality-check (D3Nexus Core)"]
    58	    FANOUT --> P_PY["python-quality-check (lyrics-sync Backend)"]
    59	    FANOUT --> P_FLUTTER["flutter-quality-check (nexus Mobile)"]
    60	    FANOUT --> P_WEB["web-quality-check (NEW: Astro TS + Vanilla JS)"]
    61	    
    62	    subgraph WEB_PROVIDER["web-quality-check Capabilities"]
    63	        direction TB
    64	        CAP_TYPE["Type-Check (astro check / tsc --noEmit / jsconfig.json)"]
    65	        CAP_LINT["Lint (ESLint / Biome / Astro linter)"]
    66	        CAP_UNIT["Tier A Unit Tests (Node / Vitest)"]
    67	        CAP_E2E["Tier C2 Headless Playwright + Zero-Console-Error Watchdog"]
    68	    end
    69	    
    70	    P_WEB --> WEB_PROVIDER
    71	    FANOUT --> AGG["Aggregate Provider Results (FAIL > BLOCKED > PASS)"]
    72	    AGG --> SMOKE["Generate manual_smoke_checklist.md (3-5 Steps)"]
    73	    SMOKE --> VERDICT["Gate 4 Certified Verdict"]
    74	```
    75	
    76	### Use Cases
    77	
    78	```mermaid
    79	flowchart LR
    80	    DEV["Human Architect"] --> UC1["Configure Multi-Provider Quality Registry"]
    81	    DEV --> UC2["Run Gate 4 Quality Verification"]
    82	    DEV --> UC3["Review Automated Smoke Checklist (2-min verify)"]
    83	    
    84	    AGENT["AI Programmer"] --> UC4["Execute Task with Anti-Rationalization Guard"]
    85	    AGENT --> UC5["Run Headless Playwright with Zero-Console-Error"]
    86	    AGENT --> UC6["Validate Vanilla JS Types via JSDoc"]
    87	```
    88	
    89	### Sequence Diagram
    90	
    91	```mermaid
    92	sequenceDiagram
    93	    autonumber
    94	    actor Human as Human Architect
    95	    participant Gate as quality_check (Gate 4)
    96	    participant Web as web-quality-check
    97	    participant Playwright as Headless Chromium
    98	    participant Gen as Smoke Generator
    99	
   100	    Human->>Gate: Trigger @quality_check (profile: epic)
   101	    Gate->>Gate: Read .agents/quality/check_quality.json
   102	    Gate->>Web: Fan-out invocation with repository SHA
   103	    Web->>Web: Run type-check & lint
   104	    Web->>Playwright: Launch Playwright headless with wiremock
   105	    Playwright->>Playwright: Verify DOM & assert Zero-Console-Error
   106	    Playwright-->>Web: Test execution trace & evidence
   107	    Web-->>Gate: Emit Provider Result Document (PASS)
   108	    Gate->>Gen: Extract primary BDD happy paths
   109	    Gen-->>Gate: Emit manual_smoke_checklist.md
   110	    Gate-->>Human: Report Gate 4 LGTM + 2-minute Smoke Checklist
   111	```
   112	
   113	### Integration Test Plan and Boundary Matrix
   114	
   115	```text
   116	Integration test roots: tests/, skills/web-quality-check/tests/
   117	Protected paths: .agents/quality/**, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md
   118	Integration results: python3 -m pytest tests/ -> build/test-results/pytest.xml
   119	```
   120	
   121	| Boundary Seam | Testing Strategy | Verification Target |
   122	| :--- | :--- | :--- |
   123	| Provider Contract | Mock `quality_check` invocation payload | Verify status aggregation and schema conformance |
   124	| Astro Web / TypeScript | Headless Playwright + Wiremock fixture | Verify DOM elements, Custom Elements, and zero console errors |
   125	| Vanilla JS Preview | `tsc --project jsconfig.json` + Playwright | Verify type safety without `.ts` migration, and page crash prevention |
   126	| Task Workflow Engine | BDD traceability & Anti-Rationalization audit | Verify tasks rejecting fake Tier C mocks and requiring real integration runs |
   127	
   128	## Verification Environment
   129	
   130	- Execution environment: Local macOS / Linux CLI with Node.js v20+, Python 3.11+, and Playwright Chromium browser installed.
   131	- No live network dependencies: All external network calls in tests are intercepted at the socket boundary.
   132	- File system isolation: Test runs operate in temporary isolated directories without mutating working git trees.
   133	
   134	### Comprehensive BDD Test Scenarios
   135	
   136	The suite covers all 5 dimensions under the `[WQG-]` prefix:
   137	1. **Happy Paths (`WQG-HP-xx`)**: Successful provider execution, Playwright headless pass, clean Vanilla JS type check, and smoke checklist generation.
   138	2. **Edge Cases (`WQG-EC-xx`)**: Missing capabilities, partial web configs, empty test suites, and third-party console warnings.
   139	3. **State Transitions (`WQG-ST-xx`)**: Dynamic transition from `BLOCKED` to `PASS` upon fixing configuration, and task status synchronization.
   140	4. **Async & Concurrency (`WQG-AR-xx`)**: Concurrent provider fan-out in Gate 4, non-blocking Playwright webServer startup.
   141	5. **Failures & Resilience (`WQG-FR-xx`)**: Console error detection triggering immediate failure, uncaught exception traps, and broken contract detection.
   142	
   143	## Shared Contract Impact
   144	
   145	None — self-contained quality provider and workflow enhancement.
   146	
   147	## Rollout Strategy and Mitigation
   148	
   149	- **Phase 1**: Author `web-quality-check` skill and validate its contract with unit and integration tests.
   150	- **Phase 2**: Add Playwright Zero-Console-Error watchdog and Vanilla JS `jsconfig.json` checker.
   151	- **Phase 3**: Update `dev-designer`, `dev-implementation`, and `test-driven-development` with Anti-Rationalization Tables and Subcutaneous Testing guidelines.
   152	- **Phase 4**: Configure polyglot registries in `D3Nexus` and `lyrics-sync`, verifying Gate 4 multi-provider execution.
   153	
   154	## Kanban Tasks Breakdown
   155	
   156	- [Task 01: Web Quality Check Skill and Provider Contract](./task_01_web_quality_check_skill_and_contract.md)
   157	- [Task 02: Playwright Zero-Console-Error Watchdog and Fixtures](./task_02_playwright_zero_error_watchdog.md)
   158	- [Task 03: Vanilla JS JSDoc Type-Checking Configuration](./task_03_jsconfig_and_vanilla_js_type_checker.md)
   159	- [Task 04: Polyglot Gate 4 Registry and Multi-Provider Fan-Out](./task_04_polyglot_gate4_registry_and_fanout.md)
   160	- [Task 05: Anti-Rationalization and Doubt-Driven Workflow Rules](./task_05_anti_rationalization_and_doubt_driven_workflow.md)
   161	- [Task 06: Automated Manual Smoke Checklist Generator](./task_06_automated_manual_smoke_checklist_generator.md)
   162	

exec
/bin/zsh -lc 'nl -ba .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# BDD Test Scenarios: Web Quality Check Provider and Integration Quality Gate
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
    14	Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
    15	  Given a repository containing an Astro project with .agents/quality/web-quality.json
    16	  When Gate 4 invokes d3nexus:web-quality-check with profile epic
    17	  Then the provider executes type_check, lint, and test_e2e via Playwright headless
    18	  And produces a validated Provider Result Document with status PASS bound to the commit SHA
    19	
    20	Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
    21	  Given a repository containing Vanilla JavaScript files in preview/static/
    22	  And a jsconfig.json configured with "checkJs": true
    23	  When web-quality-check executes the type_check capability
    24	  Then the TypeScript compiler validates all JavaScript files without emitting errors
    25	  And passes without requiring any .ts file renaming
    26	
    27	Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
    28	  Given an Astro web page with client-side interactive controllers
    29	  And Playwright configured with the Zero-Console-Error watchdog fixture
    30	  When the test simulates user navigation, button clicks, and network mocking via page.route()
    31	  Then the page renders without emitting any console.error or uncaught exceptions
    32	  And the test suite completes successfully
    33	
    34	Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
    35	  Given all tasks in an epic reach status done and Gate 4 returns PASS
    36	  When the smoke generator parses primary BDD Happy Path scenarios
    37	  Then it emits .devtool/epic/<epic_dir>/manual_smoke_checklist.md
    38	  And the checklist contains between 3 and 5 actionable verification steps with URLs and expected visual outcomes
    39	```
    40	
    41	## Dimension 2: Edge Cases and Boundaries
    42	
    43	```gherkin
    44	Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
    45	  Given a repository where .agents/quality/web-quality.json configures only type_check and test_unit
    46	  When web-quality-check is invoked with profile pr
    47	  Then it resolves only the declared capabilities
    48	  And successfully certifies the repository without erroring on missing optional capabilities
    49	
    50	Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
    51	  Given a web page emitting known third-party library deprecation warnings
    52	  And an allowlist regex configured in .agents/quality/web-quality.json
    53	  When the Playwright test executes
    54	  Then the Zero-Console-Error watchdog filters out matching allowlisted warnings
    55	  And does not falsely fail the test suite
    56	```
    57	
    58	## Dimension 3: State Transitions
    59	
    60	```gherkin
    61	Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
    62	  Given a repository with a malformed .agents/quality/web-quality.json
    63	  When validate_web_quality.py evaluates the manifest
    64	  Then it reports status BLOCKED with validation findings
    65	  And when the developer corrects the JSON schema
    66	  Then the validator transitions to status PASS
    67	
    68	Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
    69	  Given a Kanban task covering scenario [WQG-HP-01]
    70	  When the AI Programmer attempts to mark the task done with only unit mocks
    71	  Then check_bdd_traceability.py and task status sync reject the completion
    72	  And when a real Playwright headless integration test is committed
    73	  Then the task transitions cleanly to status done
    74	```
    75	
    76	## Dimension 4: Async and Concurrency
    77	
    78	```gherkin
    79	Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
    80	  Given a polyglot repository (D3Nexus) with providers rust-core and learning-web
    81	  When Gate 4 quality_check executes profile epic
    82	  Then both providers execute concurrently without interfering with each other's outputs
    83	  And Gate 4 aggregates the final verdict based on FAIL > BLOCKED > PASS priority
    84	
    85	Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
    86	  Given Playwright configured with webServer command npm run preview
    87	  When Playwright starts the test runner
    88	  Then it awaits the server healthcheck port before dispatching browser tests
    89	  And cleanly tears down the webServer process upon completion
    90	```
    91	
    92	## Dimension 5: Failures and Resilience
    93	
    94	```gherkin
    95	Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
    96	  Given a web component with a runtime bug emitting console.error("Uncaught TypeError")
    97	  When Playwright executes the test suite
    98	  Then the Zero-Console-Error watchdog immediately halts and fails the test
    99	  And logs the full console message, stack trace, and target URL as evidence
   100	
   101	Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
   102	  Given an environment where playwright or astro binary is not found in PATH
   103	  When web-quality-check attempts to spawn the process
   104	  Then it catches the spawn failure and emits status BLOCKED with actionable remediation guidance
   105	```
     1	# Kịch bản Kiểm thử BDD: Web Quality Check Provider và Integration Quality Gate
     2	
     3	## Mục lục
     4	
     5	- [Mục lục](#mục-lục)
     6	- [Chiều 1: Happy Paths](#chiều-1-happy-paths)
     7	- [Chiều 2: Edge Cases và Biên Giới hạn](#chiều-2-edge-cases-và-biên-giới-hạn)
     8	- [Chiều 3: Chuyển đổi Trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
     9	- [Chiều 4: Bất đồng bộ và Đồng thời](#chiều-4-bất-đồng-bộ-và-đồng-thời)
    10	- [Chiều 5: Thất bại và Khả năng Phục hồi](#chiều-5-thất-bại-và-khả-năng-phục-hồi)
    11	
    12	## Chiều 1: Happy Paths
    13	
    14	```gherkin
    15	Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
    16	  Given một kho lưu trữ chứa dự án Astro có file .agents/quality/web-quality.json
    17	  When Gate 4 gọi d3nexus:web-quality-check với profile epic
    18	  Then provider thực thi type_check, lint, và test_e2e qua Playwright headless
    19	  And xuất ra Tài liệu Kết quả Provider hợp lệ với trạng thái PASS gắn với commit SHA
    20	
    21	Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
    22	  Given một kho lưu trữ chứa các file Vanilla JavaScript trong preview/static/
    23	  And file jsconfig.json được cấu hình "checkJs": true
    24	  When web-quality-check thực thi capability type_check
    25	  Then trình biên dịch TypeScript kiểm tra toàn bộ file JavaScript mà không phát sinh lỗi
    26	  And vượt qua mà không yêu cầu đổi tên bất kỳ file nào sang .ts
    27	
    28	Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
    29	  Given một trang web Astro có các controller tương tác phía client
    30	  And Playwright được cấu hình với fixture bộ chặn Zero-Console-Error
    31	  When bài test giả lập điều hướng, click nút của người dùng và mock mạng qua page.route()
    32	  Then trang web render mà không phát sinh bất kỳ lỗi console.error hay ngoại lệ chưa xử lý nào
    33	  And bộ test hoàn thành thành công
    34	
    35	Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
    36	  Given tất cả các task trong một epic đạt trạng thái done và Gate 4 trả về PASS
    37	  When bộ sinh checklist phân tích các kịch bản BDD Happy Path chính
    38	  Then nó xuất ra file .devtool/epic/<epic_dir>/manual_smoke_checklist.md
    39	  And checklist chứa từ 3 đến 5 bước kiểm tra thực tế kèm URL và kết quả trực quan mong đợi
    40	```
    41	
    42	## Chiều 2: Edge Cases và Biên Giới hạn
    43	
    44	```gherkin
    45	Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
    46	  Given một kho lưu trữ có .agents/quality/web-quality.json chỉ cấu hình type_check và test_unit
    47	  When web-quality-check được gọi với profile pr
    48	  Then nó chỉ phân giải các capability đã được khai báo
    49	  And chứng thực thành công kho lưu trữ mà không báo lỗi về các capability tùy chọn bị thiếu
    50	
    51	Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
    52	  Given một trang web phát ra cảnh báo deprecation đã biết từ thư viện bên thứ ba
    53	  And một biểu thức chính quy allowlist được cấu hình trong .agents/quality/web-quality.json
    54	  When bài test Playwright thực thi
    55	  Then bộ chặn Zero-Console-Error lọc bỏ các cảnh báo khớp trong danh sách cho phép
    56	  And không đánh trượt nhầm bộ test
    57	```
    58	
    59	## Chiều 3: Chuyển đổi Trạng thái
    60	
    61	```gherkin
    62	Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
    63	  Given một kho lưu trữ có file .agents/quality/web-quality.json sai cú pháp
    64	  When validate_web_quality.py đánh giá manifest
    65	  Then nó báo cáo trạng thái BLOCKED kèm các phát hiện lỗi cấu hình
    66	  And khi lập trình viên sửa đúng schema JSON
    67	  Then validator chuyển đổi trạng thái sang PASS
    68	
    69	Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
    70	  Given một tác vụ Kanban bao phủ kịch bản [WQG-HP-01]
    71	  When Lập trình viên AI cố gắng đánh dấu task done chỉ với mock đơn vị
    72	  Then check_bdd_traceability.py và script đồng bộ trạng thái từ chối hoàn thành
    73	  And khi một bài test tích hợp Playwright headless thật được commit
    74	  Then tác vụ chuyển đổi suôn sẻ sang trạng thái done
    75	```
    76	
    77	## Chiều 4: Bất đồng bộ và Đồng thời
    78	
    79	```gherkin
    80	Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
    81	  Given một kho lưu trữ đa nền tảng (D3Nexus) với 2 provider rust-core và learning-web
    82	  When Gate 4 quality_check thực thi profile epic
    83	  Then cả hai provider chạy đồng thời mà không can thiệp vào output của nhau
    84	  And Gate 4 tổng hợp phán quyết cuối cùng theo độ ưu tiên FAIL > BLOCKED > PASS
    85	
    86	Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
    87	  Given Playwright được cấu hình với lệnh webServer là npm run preview
    88	  When Playwright khởi động test runner
    89	  Then nó chờ đợi port healthcheck của server trước khi phát lệnh chạy trình duyệt
    90	  And dọn dẹp sạch tiến trình webServer khi hoàn tất
    91	```
    92	
    93	## Chiều 5: Thất bại và Khả năng Phục hồi
    94	
    95	```gherkin
    96	Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
    97	  Given một web component có lỗi runtime phát ra console.error("Uncaught TypeError")
    98	  When Playwright thực thi bộ test
    99	  Then bộ chặn Zero-Console-Error lập tức dừng lại và đánh trượt bài test
   100	  And ghi lại toàn bộ thông báo console, stack trace và URL mục tiêu làm bằng chứng
   101	
   102	Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
   103	  Given một môi trường thiếu binary playwright hoặc astro trong PATH
   104	  When web-quality-check cố gắng spawn tiến trình
   105	  Then nó bắt lỗi spawn thất bại và xuất ra trạng thái BLOCKED kèm hướng dẫn khắc phục cụ thể
   106	```

exec
/bin/zsh -lc 'nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_01_web_quality_check_skill_and_contract.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_02_playwright_zero_error_watchdog.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_03_jsconfig_and_vanilla_js_type_checker.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_01_web_quality_check_skill_and_contract"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["quality", "web", "provider"]
    12	order: "a1"
    13	---
    14	
    15	# Task 01: Web Quality Check Skill and Provider Contract
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Author the `d3nexus:web-quality-check` provider skill implementing the canonical Provider Result Contract v1. The provider reads `.agents/quality/web-quality.json` from the repository root, executes configured capability commands without shell interpolation, validates outputs, and produces certified result documents bound to the commit SHA. Include the companion validator script `validate_web_quality.py`.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/web-quality-check/SKILL.md` (new)
    27	- `skills/web-quality-check/resources/scripts/validate_web_quality.py` (new)
    28	- `tests/test_web_quality_provider.py` (new)
    29	
    30	Read-only context:
    31	- `skills/python-quality-check/SKILL.md` (canonical capability provider reference)
    32	- `skills/quality_check/references/provider-result-contract.md` (schema definition for provider results)
    33	
    34	## Design Rationale
    35	
    36	The web quality assurance provider follows the identical architecture as `python-quality-check` and `rust-quality-check`:
    37	1. It avoids hardcoded build commands and instead reads capabilities from `.agents/quality/web-quality.json`.
    38	2. It supports argument placeholders: `{skills_dir}` for referencing sibling scripts and `{base_ref}` for Git diff baselines.
    39	3. It emits deterministic verdicts: `FAIL` (nonzero exit in tests/linter), `BLOCKED` (missing configuration, invalid schema, or executable failure), and `PASS` (all capabilities exit 0).
    40	
    41	## Impact Analysis & Blast Radius
    42	
    43	- **Target Files & Symbols**: `skills/web-quality-check/SKILL.md`, `validate_web_quality.py` (`validate_manifest`, `run_capabilities`).
    44	- **Downstream Callers**: `quality_check` orchestrator via registry invocation.
    45	- **Cross-Platform Bridges**: None (Python CLI tool).
    46	- **Target Test Coverage Threshold**: $\ge 90\%$ line coverage for `validate_web_quality.py`.
    47	
    48	### BDD SCENARIOS
    49	
    50	Covers: [WQG-HP-01], [WQG-EC-01], [WQG-ST-01], [WQG-FR-02]
    51	
    52	#### Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
    53	Given a repository containing an Astro project with `.agents/quality/web-quality.json`
    54	When Gate 4 invokes `d3nexus:web-quality-check` with profile `epic`
    55	Then the provider executes `type_check`, `lint`, and `test_e2e` via Playwright headless
    56	And produces a validated Provider Result Document with status `PASS` bound to the commit SHA.
    57	
    58	#### Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
    59	Given a repository where `.agents/quality/web-quality.json` configures only `type_check` and `test_unit`
    60	When `web-quality-check` is invoked with profile `pr`
    61	Then it resolves only the declared capabilities
    62	And successfully certifies the repository without erroring on missing optional capabilities.
    63	
    64	#### Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
    65	Given a repository with a malformed `.agents/quality/web-quality.json`
    66	When `validate_web_quality.py` evaluates the manifest
    67	Then it reports status `BLOCKED` with validation findings
    68	And when the developer corrects the JSON schema
    69	Then the validator transitions to status `PASS`.
    70	
    71	#### Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
    72	Given an environment where `playwright` or `astro` binary is not found in `PATH`
    73	When `web-quality-check` attempts to spawn the process
    74	Then it catches the spawn failure and emits status `BLOCKED` with actionable remediation guidance.
    75	
    76	## Verification
    77	
    78	| ID | Phase | Command | Expect | Needs |
    79	|----|-------|---------|--------|-------|
    80	| V1 | RED | `python3 -m pytest tests/test_web_quality_provider.py::test_contract_validation` | exit 1; contains "FAILED" | — |
    81	| V2 | GREEN | `python3 -m pytest tests/test_web_quality_provider.py::test_contract_validation` | exit 0; contains "passed" | — |
    82	| V3 | TIER-B | `ruff check skills/web-quality-check tests` | exit 0 | — |
    83	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py` | exit 0 | — |
    84	| V5 | TIER-C | `python3 -m pytest tests/test_web_quality_provider.py -k "test_WQG_HP_01 or test_WQG_EC_01 or test_WQG_ST_01 or test_WQG_FR_02" --junitxml=build/test-results/task_01.xml` | exit 0; results build/test-results/task_01.xml | — |
    85	
    86	## Stop and Report If
    87	
    88	- A command, path, symbol or anchor named in this task does not match the repository.
    89	- A Verification row fails for a reason other than its Expect.
    90	- The work needs a change to a file outside Allowed files, or to a protected path.
    91	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    92	- A variable named in the Needs column is unset.
    93	
    94	## Decisions Already Made
    95	
    96	- Manifest file path: `.agents/quality/web-quality.json`.
    97	- Schema Version: `1`.
    98	- Standard profiles supported: `pr`, `epic`, `release`, `scheduled`.
    99	- Output structure: Standard Provider Result Contract v1 format with keys `provider_id`, `contract_version`, `status`, `summary`, `checks`, `repository_sha`.
   100	
   101	## Definition of Done
   102	
   103	- `SKILL.md` documents provider execution, profile resolution, and capabilities. (V2)
   104	- `validate_web_quality.py` passes ruff linting and mypy strict typing. (V3, V4)
   105	- 100% BDD scenarios ([WQG-HP-01], [WQG-EC-01], [WQG-ST-01], [WQG-FR-02]) automated and passing. (V5)
   106	- Clean git status with changes restricted to Allowed files. (Gate 5)
   107	
   108	## Dependencies & Blockers
   109	
   110	- Blocked by: None (First task in execution order).
   111	
   112	## References & Rollback
   113	
   114	- Reference: `skills/quality_check/references/provider-result-contract.md`.
   115	- Rollback: Revert changes in `skills/web-quality-check/` and `tests/test_web_quality_provider.py`.
     1	---
     2	id: "task_02_playwright_zero_error_watchdog"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["web", "playwright", "integration"]
    12	order: "a2"
    13	---
    14	
    15	# Task 02: Playwright Zero-Console-Error Watchdog and Fixtures
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Implement the Playwright Zero-Console-Error watchdog fixture and helper harness. The fixture intercepts all browser `console.error` and `pageerror` events, halting tests on uncaught runtime errors, while supporting a regex allowlist for benign vendor deprecation warnings. It also provides wire-level network mocking patterns using `page.route()` to consume canonical contract fixtures.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/web-quality-check/resources/templates/playwright-zero-error.fixture.ts` (new)
    27	- `skills/web-quality-check/resources/scripts/run_playwright_harness.py` (new)
    28	- `tests/test_playwright_watchdog.py` (new)
    29	
    30	Read-only context:
    31	- `skills/web-quality-check/SKILL.md` (new in Task 01)
    32	- `docs/refresh-session-quick-guide.en.md` (documentation guide)
    33	
    34	## Design Rationale
    35	
    36	Browser testing often produces silent failures where a missing DOM node or failed network request logs an uncaught exception to the DevTools console while the test runner completes without error. By enforcing Zero-Console-Error at the test fixture root, any unhandled JavaScript exception immediately fails the test suite. An explicit allowlist ensures known vendor warnings (e.g. deprecation notices from third-party analytics) do not cause false positives.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `playwright-zero-error.fixture.ts`, `run_playwright_harness.py`.
    41	- **Downstream Callers**: Web test suites across `D3Nexus` (`apps/learning-web`) and `lyrics-sync` (`tests/e2e_full_screens_chrome_test.py`).
    42	- **Cross-Platform Bridges**: Browser DevTools Protocol (CDP) via Playwright.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for watchdog harness.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-HP-03], [WQG-EC-02], [WQG-AR-02], [WQG-FR-01]
    48	
    49	#### Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
    50	Given an Astro web page with client-side interactive controllers
    51	And Playwright configured with the Zero-Console-Error watchdog fixture
    52	When the test simulates user navigation, button clicks, and network mocking via `page.route()`
    53	Then the page renders without emitting any `console.error` or uncaught exceptions
    54	And the test suite completes successfully.
    55	
    56	#### Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
    57	Given a web page emitting known third-party library deprecation warnings
    58	And an allowlist regex configured in `.agents/quality/web-quality.json`
    59	When the Playwright test executes
    60	Then the Zero-Console-Error watchdog filters out matching allowlisted warnings
    61	And does not falsely fail the test suite.
    62	
    63	#### Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
    64	Given Playwright configured with `webServer` command `npm run preview`
    65	When Playwright starts the test runner
    66	Then it awaits the server healthcheck port before dispatching browser tests
    67	And cleanly tears down the webServer process upon completion.
    68	
    69	#### Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
    70	Given a web component with a runtime bug emitting `console.error("Uncaught TypeError")`
    71	When Playwright executes the test suite
    72	Then the Zero-Console-Error watchdog immediately halts and fails the test
    73	And logs the full console message, stack trace, and target URL as evidence.
    74	
    75	## Verification
    76	
    77	| ID | Phase | Command | Expect | Needs |
    78	|----|-------|---------|--------|-------|
    79	| V1 | RED | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 1; contains "FAILED" | — |
    80	| V2 | GREEN | `python3 -m pytest tests/test_playwright_watchdog.py::test_watchdog_filters` | exit 0; contains "passed" | — |
    81	| V3 | TIER-B | `ruff check tests/test_playwright_watchdog.py skills/web-quality-check` | exit 0 | — |
    82	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/run_playwright_harness.py` | exit 0 | — |
    83	| V5 | TIER-C | `python3 -m pytest tests/test_playwright_watchdog.py -k "test_WQG_HP_03 or test_WQG_EC_02 or test_WQG_AR_02 or test_WQG_FR_01" --junitxml=build/test-results/task_02.xml` | exit 0; results build/test-results/task_02.xml | — |
    84	
    85	## Stop and Report If
    86	
    87	- A command, path, symbol or anchor named in this task does not match the repository.
    88	- A Verification row fails for a reason other than its Expect.
    89	- The work needs a change to a file outside Allowed files, or to a protected path.
    90	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    91	- A variable named in the Needs column is unset.
    92	
    93	## Decisions Already Made
    94	
    95	- Target browser for Tier C runs: Chromium headless.
    96	- Console listener syntax: `page.on('console', msg => ...)` and `page.on('pageerror', err => ...)`.
    97	- Wire mocking pattern: `await page.route('**/api/**', route => route.fulfill({ json: fixture }))`.
    98	- Allowlist pattern: Array of regex strings in manifest config under `console_error_allowlist`.
    99	
   100	## Definition of Done
   101	
   102	- `playwright-zero-error.fixture.ts` template provides reusable test extension. (V2)
   103	- Zero-Console-Error watchdog passes ruff and mypy. (V3, V4)
   104	- Scenarios [WQG-HP-03], [WQG-EC-02], [WQG-AR-02], [WQG-FR-01] fully tested and passing. (V5)
   105	- Clean git status with changes restricted to Allowed files. (Gate 5)
   106	
   107	## Dependencies & Blockers
   108	
   109	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
   110	
   111	## References & Rollback
   112	
   113	- Reference: [Playwright Network Mocking Guide](https://playwright.dev/docs/mock).
   114	- Rollback: Revert `playwright-zero-error.fixture.ts` and test additions.
     1	---
     2	id: "task_03_jsconfig_and_vanilla_js_type_checker"
     3	status: "todo"
     4	priority: "medium"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["vanilla-js", "typecheck", "tooling"]
    12	order: "a3"
    13	---
    14	
    15	# Task 03: Vanilla JS JSDoc Type-Checking Configuration
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Provide in-place type checking tooling for static Vanilla JavaScript codebases (such as `lyrics-sync/src/lyrics_sync/preview/static/`) without migrating files to `.ts`. Supply a canonical `jsconfig.json` template enabling `checkJs` and strict type analysis via JSDoc annotations, accompanied by the `check_vanilla_js.py` execution wrapper for the `type_check` capability.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/web-quality-check/resources/templates/jsconfig.template.json` (new)
    27	- `skills/web-quality-check/resources/scripts/check_vanilla_js.py` (new)
    28	- `tests/test_vanilla_js_checker.py` (new)
    29	
    30	Read-only context:
    31	- `skills/web-quality-check/SKILL.md` (new in Task 01)
    32	- `docs/refresh-session-quick-guide.en.md` (documentation guide)
    33	
    34	## Design Rationale
    35	
    36	Vanilla JavaScript codebases often suffer from silent runtime bugs due to misspelled variable names, missing function parameters, or null reference errors on DOM nodes. Migrating these files to TypeScript involves substantial build overhead. Using TypeScript's built-in `checkJs` mode via `jsconfig.json` provides compile-time safety and catches nullability bugs without changing runtime deployment semantics.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `jsconfig.template.json`, `check_vanilla_js.py`.
    41	- **Downstream Callers**: `web-quality-check` provider running `type_check` on static JavaScript files.
    42	- **Cross-Platform Bridges**: None.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `check_vanilla_js.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-HP-02]
    48	
    49	#### Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
    50	Given a repository containing Vanilla JavaScript files in `preview/static/`
    51	And a `jsconfig.json` configured with `"checkJs": true`
    52	When `web-quality-check` executes the `type_check` capability
    53	Then the TypeScript compiler validates all JavaScript files without emitting errors
    54	And passes without requiring any `.ts` file renaming.
    55	
    56	## Verification
    57	
    58	| ID | Phase | Command | Expect | Needs |
    59	|----|-------|---------|--------|-------|
    60	| V1 | RED | `python3 -m pytest tests/test_vanilla_js_checker.py::test_jsconfig_discovery` | exit 1; contains "FAILED" | — |
    61	| V2 | GREEN | `python3 -m pytest tests/test_vanilla_js_checker.py::test_jsconfig_discovery` | exit 0; contains "passed" | — |
    62	| V3 | TIER-B | `ruff check tests/test_vanilla_js_checker.py skills/web-quality-check` | exit 0 | — |
    63	| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/check_vanilla_js.py` | exit 0 | — |
    64	| V5 | TIER-C | `python3 -m pytest tests/test_vanilla_js_checker.py -k "test_WQG_HP_02" --junitxml=build/test-results/task_03.xml` | exit 0; results build/test-results/task_03.xml | — |
    65	
    66	## Stop and Report If
    67	
    68	- A command, path, symbol or anchor named in this task does not match the repository.
    69	- A Verification row fails for a reason other than its Expect.
    70	- The work needs a change to a file outside Allowed files, or to a protected path.
    71	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    72	- A variable named in the Needs column is unset.
    73	
    74	## Decisions Already Made
    75	
    76	- Compiler configuration: `compilerOptions: { "checkJs": true, "noEmit": true, "target": "ES2022", "moduleResolution": "node" }`.
    77	- Target files: `src/**/*.js` or configured include glob.
    78	- Execution binary: `npx tsc --project <path_to_jsconfig>`.
    79	
    80	## Definition of Done
    81	
    82	- `jsconfig.template.json` provides a turn-key configuration for Vanilla JS type checking. (V2)
    83	- `check_vanilla_js.py` passes ruff linting and mypy typing. (V3, V4)
    84	- Scenario [WQG-HP-02] fully verified and passing. (V5)
    85	- Clean git status with changes restricted to Allowed files. (Gate 5)
    86	
    87	## Dependencies & Blockers
    88	
    89	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
    90	
    91	## References & Rollback
    92	
    93	- Reference: [TypeScript JSDoc Reference](https://www.typescriptlang.org/docs/handbook/jsdoc-supported-types.html).
    94	- Rollback: Revert `jsconfig.template.json` and checker script.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_04_polyglot_gate4_registry_and_fanout.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_05_anti_rationalization_and_doubt_driven_workflow.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/handoff.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_04_polyglot_gate4_registry_and_fanout"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["orchestration", "quality-gate", "polyglot"]
    12	order: "a4"
    13	---
    14	
    15	# Task 04: Polyglot Gate 4 Registry and Multi-Provider Fan-Out
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Extend project quality templates and verification tooling to support multi-provider polyglot registries in `.agents/quality/check_quality.json`. Enable concurrent fan-out and deterministic aggregation across disparate stacks: `rust-core` + `learning-web` for `D3Nexus`, and `python-core` + `preview-ui` for `lyrics-sync`.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/setup_quality_check/resources/templates/polyglot-check-quality.template.json` (new)
    27	- `skills/quality_check/resources/scripts/verify_polyglot_registry.py` (new)
    28	- `tests/test_polyglot_gate4.py` (new)
    29	
    30	Read-only context:
    31	- `skills/quality_check/SKILL.md` (Gate 4 orchestrator)
    32	- `skills/quality_check/resources/scripts/validate_quality_contract.py` (registry validator)
    33	
    34	## Design Rationale
    35	
    36	Modern systems are increasingly polyglot: a single repository may house a Rust/WASM core alongside an Astro frontend (`D3Nexus`), or a Python worker service alongside a Vanilla JavaScript player (`lyrics-sync`). Gate 4 must not be constrained to a single provider. It must concurrently dispatch checks across all registered providers, aggregate verdicts under `FAIL > BLOCKED > PASS`, and report a unified executive summary.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `polyglot-check-quality.template.json`, `verify_polyglot_registry.py`.
    41	- **Downstream Callers**: All polyglot repositories consuming `quality_check`.
    42	- **Cross-Platform Bridges**: Multi-process fan-out.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `verify_polyglot_registry.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-AR-01]
    48	
    49	#### Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
    50	Given a polyglot repository (`D3Nexus`) with providers `rust-core` and `learning-web`
    51	When Gate 4 `quality_check` executes profile `epic`
    52	Then both providers execute concurrently without interfering with each other's outputs
    53	And Gate 4 aggregates the final verdict based on `FAIL > BLOCKED > PASS` priority.
    54	
    55	## Verification
    56	
    57	| ID | Phase | Command | Expect | Needs |
    58	|----|-------|---------|--------|-------|
    59	| V1 | RED | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 1; contains "FAILED" | — |
    60	| V2 | GREEN | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 0; contains "passed" | — |
    61	| V3 | TIER-B | `ruff check tests/test_polyglot_gate4.py skills/quality_check` | exit 0 | — |
    62	| V4 | TIER-B | `mypy skills/quality_check/resources/scripts/verify_polyglot_registry.py` | exit 0 | — |
    63	| V5 | TIER-C | `python3 -m pytest tests/test_polyglot_gate4.py -k "test_WQG_AR_01" --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |
    64	
    65	## Stop and Report If
    66	
    67	- A command, path, symbol or anchor named in this task does not match the repository.
    68	- A Verification row fails for a reason other than its Expect.
    69	- The work needs a change to a file outside Allowed files, or to a protected path.
    70	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    71	- A variable named in the Needs column is unset.
    72	
    73	## Decisions Already Made
    74	
    75	- Aggregation precedence: `FAIL` trumps `BLOCKED`, which trumps `PASS`.
    76	- Output format: Unified executive markdown report listing every provider's status, executed checks, and SHA binding.
    77	- Manifest schema version: `1` with multiple objects in the `providers` array.
    78	
    79	## Definition of Done
    80	
    81	- `polyglot-check-quality.template.json` provides working configuration models for multi-provider repos. (V2)
    82	- Multi-provider concurrency and verdict reduction verified with ruff and mypy. (V3, V4)
    83	- Scenario [WQG-AR-01] fully tested and passing. (V5)
    84	- Clean git status with changes restricted to Allowed files. (Gate 5)
    85	
    86	## Dependencies & Blockers
    87	
    88	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
    89	
    90	## References & Rollback
    91	
    92	- Reference: `skills/quality_check/SKILL.md`.
    93	- Rollback: Revert `polyglot-check-quality.template.json` and verification test.
     1	---
     2	id: "task_05_anti_rationalization_and_doubt_driven_workflow"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["governance", "workflow", "anti-rationalization"]
    12	order: "a5"
    13	---
    14	
    15	# Task 05: Anti-Rationalization and Doubt-Driven Workflow Rules
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Incorporate Anti-Rationalization Tables and Doubt-Driven Verification principles (inspired by `addyosmani/agent-skills`) into core lifecycle and implementation skills: `dev-designer`, `dev-implementation`, and `test-driven-development`. Enforce Subcutaneous Testing for mobile, require real Playwright execution for web Tier C scenarios, and reject mock-substitution shortcuts during task execution.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/dev-designer/SKILL.md`
    27	- `skills/dev-implementation/SKILL.md`
    28	- `skills/test-driven-development/SKILL.md`
    29	- `tests/test_workflow_anti_rationalization.py` (new)
    30	
    31	Read-only context:
    32	- `rules/CRITICAL_RULES.md` (mandatory quality gates)
    33	- `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md` (parent HLD)
    34	
    35	## Design Rationale
    36	
    37	AI coding agents naturally seek the path of least resistance, often writing Unit mocks while tagging them as Integration tests or skipping browser validation. Codifying explicit Anti-Rationalization Tables directly in the skill prompts provides an active behavioral counter-force, preventing agents from cutting corners before task completion.
    38	
    39	## Impact Analysis & Blast Radius
    40	
    41	- **Target Files & Symbols**: `dev-designer`, `dev-implementation`, `test-driven-development`.
    42	- **Downstream Callers**: All developers and agents running epic lifecycles across mobile and web.
    43	- **Cross-Platform Bridges**: None.
    44	- **Target Test Coverage Threshold**: Document syntax and skill lint validation (0 errors).
    45	
    46	### BDD SCENARIOS
    47	
    48	Covers: [WQG-ST-02]
    49	
    50	#### Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
    51	Given a Kanban task covering scenario `[WQG-HP-01]`
    52	When the AI Programmer attempts to mark the task `done` with only unit mocks
    53	Then `check_bdd_traceability.py` and task status sync reject the completion
    54	And when a real Playwright headless integration test is committed
    55	Then the task transitions cleanly to status `done`.
    56	
    57	## Verification
    58	
    59	| ID | Phase | Command | Expect | Needs |
    60	|----|-------|---------|--------|-------|
    61	| V1 | RED | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 1; contains "FAILED" | — |
    62	| V2 | GREEN | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 0; contains "passed" | — |
    63	| V3 | TIER-B | `ruff check tests/test_workflow_anti_rationalization.py` | exit 0 | — |
    64	| V4 | TIER-B | `mypy tests/test_workflow_anti_rationalization.py` | exit 0 | — |
    65	| V5 | TIER-C | `python3 -m pytest tests/test_workflow_anti_rationalization.py -k "test_WQG_ST_02" --junitxml=build/test-results/task_05.xml` | exit 0; results build/test-results/task_05.xml | — |
    66	
    67	## Stop and Report If
    68	
    69	- A command, path, symbol or anchor named in this task does not match the repository.
    70	- A Verification row fails for a reason other than its Expect.
    71	- The work needs a change to a file outside Allowed files, or to a protected path.
    72	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    73	- A variable named in the Needs column is unset.
    74	
    75	## Decisions Already Made
    76	
    77	- Frontmatter of `SKILL.md` files must remain strictly `name` and `description` only.
    78	- Anti-Rationalization tables placed in dedicated sections within each skill.
    79	- Subcutaneous testing guidelines formalized for Flutter and native mobile.
    80	
    81	## Definition of Done
    82	
    83	- `dev-designer/SKILL.md` requires Playwright for Web and Subcutaneous tests for Mobile. (V2)
    84	- Test suite passes ruff linting and mypy typing. (V3, V4)
    85	- Scenario [WQG-ST-02] fully verified and passing. (V5)
    86	- Clean git status with changes restricted to Allowed files. (Gate 5)
    87	
    88	## Dependencies & Blockers
    89	
    90	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
    91	
    92	## References & Rollback
    93	
    94	- Reference: `addyosmani/agent-skills` Anti-Rationalization patterns.
    95	- Rollback: Revert modifications to `skills/` files via git restore.
     1	---
     2	id: "task_06_automated_manual_smoke_checklist_generator"
     3	status: "todo"
     4	priority: "medium"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["automation", "smoke-test", "workflow"]
    12	order: "a6"
    13	---
    14	
    15	# Task 06: Automated Manual Smoke Checklist Generator
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Build the automated smoke checklist generator script `generate_smoke_checklist.py` and hook it into Phase 4 of `dev-implementation`. The script parses the canonical BDD Happy Path scenarios (`bdd_scenarios.en.md`), extracts 3 to 5 core user journey steps, and formats them into a clean markdown document at `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`. This gives the human engineer an instant 2-minute manual sanity check checklist upon Gate 4 completion.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` (new)
    27	- `skills/dev-implementation/SKILL.md`
    28	- `tests/test_smoke_checklist_generator.py` (new)
    29	
    30	Read-only context:
    31	- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` (source BDD contract)
    32	- `skills/dev-implementation/SKILL.md` (Phase 4 integration point)
    33	
    34	## Design Rationale
    35	
    36	Even with 100% automated testing, human developers naturally want to perform a quick sanity check before release. Without structured guidance, this exploratory testing often takes 20-30 minutes of aimless clicking. Automatically generating a focused 3-5 step walkthrough directly from the approved BDD Happy Paths concentrates human verification into a rapid 2-minute validation loop.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `generate_smoke_checklist.py`, `dev-implementation/SKILL.md`.
    41	- **Downstream Callers**: `dev-implementation` Phase 4 upon Gate 4 pass.
    42	- **Cross-Platform Bridges**: None.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `generate_smoke_checklist.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-HP-04]
    48	
    49	#### Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
    50	Given all tasks in an epic reach status `done` and Gate 4 returns `PASS`
    51	When the smoke generator parses primary BDD Happy Path scenarios
    52	Then it emits `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
    53	And the checklist contains between 3 and 5 actionable verification steps with URLs and expected visual outcomes.
    54	
    55	## Verification
    56	
    57	| ID | Phase | Command | Expect | Needs |
    58	|----|-------|---------|--------|-------|
    59	| V1 | RED | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 1; contains "FAILED" | — |
    60	| V2 | GREEN | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 0; contains "passed" | — |
    61	| V3 | TIER-B | `ruff check tests/test_smoke_checklist_generator.py skills/dev-implementation` | exit 0 | — |
    62	| V4 | TIER-B | `mypy skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
    63	| V5 | TIER-C | `python3 -m pytest tests/test_smoke_checklist_generator.py -k "test_WQG_HP_04" --junitxml=build/test-results/task_06.xml` | exit 0; results build/test-results/task_06.xml | — |
    64	
    65	## Stop and Report If
    66	
    67	- A command, path, symbol or anchor named in this task does not match the repository.
    68	- A Verification row fails for a reason other than its Expect.
    69	- The work needs a change to a file outside Allowed files, or to a protected path.
    70	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    71	- A variable named in the Needs column is unset.
    72	
    73	## Decisions Already Made
    74	
    75	- Output path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`.
    76	- Maximum checklist length: 5 items.
    77	- Structure: Checklist table containing Step Number, Target Screen/URL, Action, and Observable Outcome.
    78	
    79	## Definition of Done
    80	
    81	- `generate_smoke_checklist.py` extracts Happy Path steps and outputs valid markdown. (V2)
    82	- Script passes ruff linting and mypy typing. (V3, V4)
    83	- Scenario [WQG-HP-04] fully verified and passing. (V5)
    84	- Clean git status with changes restricted to Allowed files. (Gate 5)
    85	
    86	## Dependencies & Blockers
    87	
    88	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md), [Task 05](task_05_anti_rationalization_and_doubt_driven_workflow.md).
    89	
    90	## References & Rollback
    91	
    92	- Reference: `dev-implementation/SKILL.md` Phase 4 verification flow.
    93	- Rollback: Revert `generate_smoke_checklist.py` and test file.
     1	# Handoff: web_quality_check_and_integration_gate
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
    15	- **Packaged**: 2026-11-04
    16	- **Design commit**: `19eb54a`
    17	- **Base branch**: `main`
    18	- **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
    19	- **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.
    20	
    21	## Identifiers
    22	
    23	| Placeholder | Value |
    24	|-------------|-------|
    25	| `<epic_dir>` | `web_quality_check_and_integration_gate` |
    26	| `<epic_slug>` | `web-quality-check-and-integration-gate` |
    27	
    28	These are two distinct strings (underscores for directory, hyphens for slug). Never derive one from the other.
    29	
    30	## Read First
    31	
    32	1. `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md` — the HLD. Its Kanban Tasks Breakdown lists the 6 tasks.
    33	2. `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` — the behavioural contract covering all 12 scenarios.
    34	3. `.devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md` — the approved source spec.
    35	
    36	## Resume Prompt
    37	
    38	```text
    39	[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]
    40	Use the d3nexus:dev-implementation skill for the `web-quality-check-and-integration-gate` epic.
    41	Read .devtool/epic/web_quality_check_and_integration_gate/handoff.md first.
    42	Apply the Execution Guardrails for Receiving LLM before presenting Gate 3.
    43	Gates 1 and 2 are passed; do not re-run brainstorming or design.
    44	Gate 3 is pending: present the execution order to me and wait for my confirmation.
    45	```
    46	
    47	## Execution Guardrails for Receiving LLM
    48	
    49	Fast executor models and receiving agents MUST adhere to these four hard guardrails throughout implementation:
    50	
    51	1. **Bounded context protocol**:
    52	   - Step 1: Read only the active task file (`.devtool/features/task_*.md`).
    53	   - Step 2: Read only the exact files declared in `Allowed files` and `Read-only context`.
    54	   - Step 3: Look up exact symbol definitions identified under `## Decisions Already Made`.
    55	   Undirected whole-repository searches (`grep`, `find`, `list_dir`) are forbidden unless an unresolved import explicitly requires symbol lookup.
    56	2. **Strict spec fidelity**: Frozen constants, defaults, retry counts, fallback conditions, signatures, and call paths under `## Decisions Already Made` and the HLD are hard contracts. Any mismatch causes STOP and report rather than an executor-side simplification.
    57	3. **Zero test fakery & Anti-Rationalization**: Tests must exercise real production symbols. In Tier C tests, mocking domain use cases or repositories is strictly forbidden. Web Tier C tests must run in headless Playwright with Zero-Console-Error assertion.
    58	4. **No contract repair by the executor**: The receiver never edits Verification tables, Allowed files, Definition of Done, Covers lines, protected paths, or frozen contract facts.
    59	
    60	## Open Notes
    61	
    62	- **Polyglot Ecosystem Scope**: This epic implements the `web-quality-check` provider in `ai-agent-tools`, which unblocks full Gate 4 multi-provider verification across `D3Nexus` (`rust-core` + `learning-web`) and `lyrics-sync` (`python-core` + `preview-ui`), as well as formalizing Subcutaneous Testing guidelines for `nexus` (`flutter-core`).
    63	- **Anti-Rationalization Integration**: Inspired by `addyosmani/agent-skills`, Anti-Rationalization tables and Doubt-Driven Verification rules are codified into `dev-designer`, `dev-implementation`, and `test-driven-development`.
    64	- **Zero-Console-Error Watchdog**: Playwright fixtures intercept all `console.error` and `pageerror` events, halting tests on unhandled runtime exceptions while supporting an allowlist regex for benign third-party library deprecation warnings.
    65	- **In-Place Vanilla JS Type-Checking**: Static JavaScript files in `lyrics-sync` are type-checked via `jsconfig.json` with JSDoc `// @ts-check` without requiring `.ts` file renaming.
    66	- **Automated Smoke Walkthrough**: Task 06 provides `generate_smoke_checklist.py`, hooked into `dev-implementation` Phase 4, generating `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` (3-5 steps, 2-minute sanity check) upon Gate 4 pass.
    67	
    68	## Rules for the Receiving Agent
    69	
    70	- Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
    71	- This handoff does not pass Gate 3. The developer confirms the execution order.
    72	- Unless the design commit is `uncommitted`: if `git log 19eb54a..main -- .devtool/epic/web_quality_check_and_integration_gate` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale. Comparing against the base branch keeps the epic branch's own task commits out of the check.
    73	- This file is a dated record. It is never updated after packaging.
    74	- Never edit a task's Verification table, Definition of Done, Allowed files or a protected path; stop and report.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_04_polyglot_gate4_registry_and_fanout.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_05_anti_rationalization_and_doubt_driven_workflow.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	id: "task_04_polyglot_gate4_registry_and_fanout"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["orchestration", "quality-gate", "polyglot"]
    12	order: "a4"
    13	---
    14	
    15	# Task 04: Polyglot Gate 4 Registry and Multi-Provider Fan-Out
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Extend project quality templates and verification tooling to support multi-provider polyglot registries in `.agents/quality/check_quality.json`. Enable concurrent fan-out and deterministic aggregation across disparate stacks: `rust-core` + `learning-web` for `D3Nexus`, and `python-core` + `preview-ui` for `lyrics-sync`.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/setup_quality_check/resources/templates/polyglot-check-quality.template.json` (new)
    27	- `skills/quality_check/resources/scripts/verify_polyglot_registry.py` (new)
    28	- `tests/test_polyglot_gate4.py` (new)
    29	
    30	Read-only context:
    31	- `skills/quality_check/SKILL.md` (Gate 4 orchestrator)
    32	- `skills/quality_check/resources/scripts/validate_quality_contract.py` (registry validator)
    33	
    34	## Design Rationale
    35	
    36	Modern systems are increasingly polyglot: a single repository may house a Rust/WASM core alongside an Astro frontend (`D3Nexus`), or a Python worker service alongside a Vanilla JavaScript player (`lyrics-sync`). Gate 4 must not be constrained to a single provider. It must concurrently dispatch checks across all registered providers, aggregate verdicts under `FAIL > BLOCKED > PASS`, and report a unified executive summary.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `polyglot-check-quality.template.json`, `verify_polyglot_registry.py`.
    41	- **Downstream Callers**: All polyglot repositories consuming `quality_check`.
    42	- **Cross-Platform Bridges**: Multi-process fan-out.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `verify_polyglot_registry.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-AR-01]
    48	
    49	#### Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
    50	Given a polyglot repository (`D3Nexus`) with providers `rust-core` and `learning-web`
    51	When Gate 4 `quality_check` executes profile `epic`
    52	Then both providers execute concurrently without interfering with each other's outputs
    53	And Gate 4 aggregates the final verdict based on `FAIL > BLOCKED > PASS` priority.
    54	
    55	## Verification
    56	
    57	| ID | Phase | Command | Expect | Needs |
    58	|----|-------|---------|--------|-------|
    59	| V1 | RED | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 1; contains "FAILED" | — |
    60	| V2 | GREEN | `python3 -m pytest tests/test_polyglot_gate4.py::test_polyglot_fanout` | exit 0; contains "passed" | — |
    61	| V3 | TIER-B | `ruff check tests/test_polyglot_gate4.py skills/quality_check` | exit 0 | — |
    62	| V4 | TIER-B | `mypy skills/quality_check/resources/scripts/verify_polyglot_registry.py` | exit 0 | — |
    63	| V5 | TIER-C | `python3 -m pytest tests/test_polyglot_gate4.py -k "test_WQG_AR_01" --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |
    64	
    65	## Stop and Report If
    66	
    67	- A command, path, symbol or anchor named in this task does not match the repository.
    68	- A Verification row fails for a reason other than its Expect.
    69	- The work needs a change to a file outside Allowed files, or to a protected path.
    70	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    71	- A variable named in the Needs column is unset.
    72	
    73	## Decisions Already Made
    74	
    75	- Aggregation precedence: `FAIL` trumps `BLOCKED`, which trumps `PASS`.
    76	- Output format: Unified executive markdown report listing every provider's status, executed checks, and SHA binding.
    77	- Manifest schema version: `1` with multiple objects in the `providers` array.
    78	
    79	## Definition of Done
    80	
    81	- `polyglot-check-quality.template.json` provides working configuration models for multi-provider repos. (V2)
    82	- Multi-provider concurrency and verdict reduction verified with ruff and mypy. (V3, V4)
    83	- Scenario [WQG-AR-01] fully tested and passing. (V5)
    84	- Clean git status with changes restricted to Allowed files. (Gate 5)
    85	
    86	## Dependencies & Blockers
    87	
    88	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
    89	
    90	## References & Rollback
    91	
    92	- Reference: `skills/quality_check/SKILL.md`.
    93	- Rollback: Revert `polyglot-check-quality.template.json` and verification test.
     1	---
     2	id: "task_05_anti_rationalization_and_doubt_driven_workflow"
     3	status: "todo"
     4	priority: "high"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["governance", "workflow", "anti-rationalization"]
    12	order: "a5"
    13	---
    14	
    15	# Task 05: Anti-Rationalization and Doubt-Driven Workflow Rules
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Incorporate Anti-Rationalization Tables and Doubt-Driven Verification principles (inspired by `addyosmani/agent-skills`) into core lifecycle and implementation skills: `dev-designer`, `dev-implementation`, and `test-driven-development`. Enforce Subcutaneous Testing for mobile, require real Playwright execution for web Tier C scenarios, and reject mock-substitution shortcuts during task execution.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/dev-designer/SKILL.md`
    27	- `skills/dev-implementation/SKILL.md`
    28	- `skills/test-driven-development/SKILL.md`
    29	- `tests/test_workflow_anti_rationalization.py` (new)
    30	
    31	Read-only context:
    32	- `rules/CRITICAL_RULES.md` (mandatory quality gates)
    33	- `.devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md` (parent HLD)
    34	
    35	## Design Rationale
    36	
    37	AI coding agents naturally seek the path of least resistance, often writing Unit mocks while tagging them as Integration tests or skipping browser validation. Codifying explicit Anti-Rationalization Tables directly in the skill prompts provides an active behavioral counter-force, preventing agents from cutting corners before task completion.
    38	
    39	## Impact Analysis & Blast Radius
    40	
    41	- **Target Files & Symbols**: `dev-designer`, `dev-implementation`, `test-driven-development`.
    42	- **Downstream Callers**: All developers and agents running epic lifecycles across mobile and web.
    43	- **Cross-Platform Bridges**: None.
    44	- **Target Test Coverage Threshold**: Document syntax and skill lint validation (0 errors).
    45	
    46	### BDD SCENARIOS
    47	
    48	Covers: [WQG-ST-02]
    49	
    50	#### Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
    51	Given a Kanban task covering scenario `[WQG-HP-01]`
    52	When the AI Programmer attempts to mark the task `done` with only unit mocks
    53	Then `check_bdd_traceability.py` and task status sync reject the completion
    54	And when a real Playwright headless integration test is committed
    55	Then the task transitions cleanly to status `done`.
    56	
    57	## Verification
    58	
    59	| ID | Phase | Command | Expect | Needs |
    60	|----|-------|---------|--------|-------|
    61	| V1 | RED | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 1; contains "FAILED" | — |
    62	| V2 | GREEN | `python3 -m pytest tests/test_workflow_anti_rationalization.py::test_anti_rationalization_content` | exit 0; contains "passed" | — |
    63	| V3 | TIER-B | `ruff check tests/test_workflow_anti_rationalization.py` | exit 0 | — |
    64	| V4 | TIER-B | `mypy tests/test_workflow_anti_rationalization.py` | exit 0 | — |
    65	| V5 | TIER-C | `python3 -m pytest tests/test_workflow_anti_rationalization.py -k "test_WQG_ST_02" --junitxml=build/test-results/task_05.xml` | exit 0; results build/test-results/task_05.xml | — |
    66	
    67	## Stop and Report If
    68	
    69	- A command, path, symbol or anchor named in this task does not match the repository.
    70	- A Verification row fails for a reason other than its Expect.
    71	- The work needs a change to a file outside Allowed files, or to a protected path.
    72	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    73	- A variable named in the Needs column is unset.
    74	
    75	## Decisions Already Made
    76	
    77	- Frontmatter of `SKILL.md` files must remain strictly `name` and `description` only.
    78	- Anti-Rationalization tables placed in dedicated sections within each skill.
    79	- Subcutaneous testing guidelines formalized for Flutter and native mobile.
    80	
    81	## Definition of Done
    82	
    83	- `dev-designer/SKILL.md` requires Playwright for Web and Subcutaneous tests for Mobile. (V2)
    84	- Test suite passes ruff linting and mypy typing. (V3, V4)
    85	- Scenario [WQG-ST-02] fully verified and passing. (V5)
    86	- Clean git status with changes restricted to Allowed files. (Gate 5)
    87	
    88	## Dependencies & Blockers
    89	
    90	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md).
    91	
    92	## References & Rollback
    93	
    94	- Reference: `addyosmani/agent-skills` Anti-Rationalization patterns.
    95	- Rollback: Revert modifications to `skills/` files via git restore.
     1	---
     2	id: "task_06_automated_manual_smoke_checklist_generator"
     3	status: "todo"
     4	priority: "medium"
     5	assignee: null
     6	epic: "web-quality-check-and-integration-gate"
     7	dueDate: null
     8	created: "2026-11-04T22:52:00Z"
     9	modified: "2026-11-04T22:52:00Z"
    10	completedAt: null
    11	labels: ["automation", "smoke-test", "workflow"]
    12	order: "a6"
    13	---
    14	
    15	# Task 06: Automated Manual Smoke Checklist Generator
    16	
    17	Epic: [web_quality_check_and_integration_gate](web_quality_check_and_integration_gate.en.md)
    18	
    19	## Requirement Analysis
    20	
    21	Build the automated smoke checklist generator script `generate_smoke_checklist.py` and hook it into Phase 4 of `dev-implementation`. The script parses the canonical BDD Happy Path scenarios (`bdd_scenarios.en.md`), extracts 3 to 5 core user journey steps, and formats them into a clean markdown document at `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`. This gives the human engineer an instant 2-minute manual sanity check checklist upon Gate 4 completion.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` (new)
    27	- `skills/dev-implementation/SKILL.md`
    28	- `tests/test_smoke_checklist_generator.py` (new)
    29	
    30	Read-only context:
    31	- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` (source BDD contract)
    32	- `skills/dev-implementation/SKILL.md` (Phase 4 integration point)
    33	
    34	## Design Rationale
    35	
    36	Even with 100% automated testing, human developers naturally want to perform a quick sanity check before release. Without structured guidance, this exploratory testing often takes 20-30 minutes of aimless clicking. Automatically generating a focused 3-5 step walkthrough directly from the approved BDD Happy Paths concentrates human verification into a rapid 2-minute validation loop.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `generate_smoke_checklist.py`, `dev-implementation/SKILL.md`.
    41	- **Downstream Callers**: `dev-implementation` Phase 4 upon Gate 4 pass.
    42	- **Cross-Platform Bridges**: None.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `generate_smoke_checklist.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-HP-04]
    48	
    49	#### Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
    50	Given all tasks in an epic reach status `done` and Gate 4 returns `PASS`
    51	When the smoke generator parses primary BDD Happy Path scenarios
    52	Then it emits `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
    53	And the checklist contains between 3 and 5 actionable verification steps with URLs and expected visual outcomes.
    54	
    55	## Verification
    56	
    57	| ID | Phase | Command | Expect | Needs |
    58	|----|-------|---------|--------|-------|
    59	| V1 | RED | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 1; contains "FAILED" | — |
    60	| V2 | GREEN | `python3 -m pytest tests/test_smoke_checklist_generator.py::test_smoke_checklist_generation` | exit 0; contains "passed" | — |
    61	| V3 | TIER-B | `ruff check tests/test_smoke_checklist_generator.py skills/dev-implementation` | exit 0 | — |
    62	| V4 | TIER-B | `mypy skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` | exit 0 | — |
    63	| V5 | TIER-C | `python3 -m pytest tests/test_smoke_checklist_generator.py -k "test_WQG_HP_04" --junitxml=build/test-results/task_06.xml` | exit 0; results build/test-results/task_06.xml | — |
    64	
    65	## Stop and Report If
    66	
    67	- A command, path, symbol or anchor named in this task does not match the repository.
    68	- A Verification row fails for a reason other than its Expect.
    69	- The work needs a change to a file outside Allowed files, or to a protected path.
    70	- The work needs a change to this task's Verification table, Definition of Done, Allowed files or Covers line.
    71	- A variable named in the Needs column is unset.
    72	
    73	## Decisions Already Made
    74	
    75	- Output path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`.
    76	- Maximum checklist length: 5 items.
    77	- Structure: Checklist table containing Step Number, Target Screen/URL, Action, and Observable Outcome.
    78	
    79	## Definition of Done
    80	
    81	- `generate_smoke_checklist.py` extracts Happy Path steps and outputs valid markdown. (V2)
    82	- Script passes ruff linting and mypy typing. (V3, V4)
    83	- Scenario [WQG-HP-04] fully verified and passing. (V5)
    84	- Clean git status with changes restricted to Allowed files. (Gate 5)
    85	
    86	## Dependencies & Blockers
    87	
    88	- Blocked by: [Task 01](task_01_web_quality_check_skill_and_contract.md), [Task 05](task_05_anti_rationalization_and_doubt_driven_workflow.md).
    89	
    90	## References & Rollback
    91	
    92	- Reference: `dev-implementation/SKILL.md` Phase 4 verification flow.
    93	- Rollback: Revert `generate_smoke_checklist.py` and test file.

exec
/bin/zsh -lc 'nl -ba .devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.vi.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.vi.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Đặc tả Thiết kế Web Quality Check và Integration Gate
     2	
     3	## Mục lục
     4	
     5	- [Mục lục](#mục-lục)
     6	- [Metadata](#metadata)
     7	- [Bối cảnh và Vấn đề](#bối-cảnh-và-vấn-đề)
     8	- [Mục tiêu và Giới hạn](#mục-tiêu-và-giới-hạn)
     9	- [Kiến trúc và Chuẩn Kiểm thử 3 Lớp](#kiến-trúc-và-chuẩn-kiểm-thử-3-lớp)
    10	- [Chống Ngụy biện và Cơ chế Phản biện Nghi vấn](#chống-ngụy-biện-và-cơ-chế-phản-biện-nghi-vấn)
    11	- [Đặc tả Kỹ thuật Provider Web Quality](#đặc-tả-kỹ-thuật-provider-web-quality)
    12	- [Tích hợp Registry Đa Repo và Gate 4 Đa Nền tảng](#tích-hợp-registry-đa-repo-và-gate-4-đa-nền-tảng)
    13	- [Nâng cấp Dev-Designer và Dev-Implementation](#nâng-cấp-dev-designer-và-dev-implementation)
    14	- [Tự động Sinh Kịch bản Smoke Test Bấm tay](#tự-động-sinh-kịch-bản-smoke-test-bấm-tay)
    15	- [Rủi ro và Giải pháp Giảm thiểu](#rủi-ro-và-giải-pháp-giảm-thiểu)
    16	- [Kế hoạch Kiểm chứng](#kế-hoạch-kiểm-chứng)
    17	
    18	## Metadata
    19	
    20	- **Tên Epic**: `web_quality_check_and_integration_gate`
    21	- **Slug Epic**: `web-quality-check-and-integration-gate`
    22	- **Ngày**: 2026-11-04
    23	- **Tác giả**: Kiến trúc sư Con người & Trợ lý AI
    24	- **Trạng thái**: Đã phê duyệt (Đã qua Gate 1)
    25	- **Kho lưu trữ Mục tiêu**: `ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`
    26	
    27	## Bối cảnh và Vấn đề
    28	
    29	Trong hệ sinh thái đa repo (`D3Nexus`, `lyrics-sync`, `nexus`), các kỹ sư thường xuyên đối mặt với khoảng cách lớn giữa thiết kế kiến trúc lý thuyết và hành vi thực tế khi chạy. Khoảng cách này buộc lập trình viên phải thực hiện quá nhiều thao tác kiểm thử thủ công (bấm tay) trên thiết bị và trình duyệt trước mỗi đợt release:
    30	
    31	1. **Cái bẫy của Mock (Mocking Fallacy)**: Các bài kiểm thử đơn vị `[Tier A - Unit]` đạt tỷ lệ pass 100% bằng cách cô lập các thành phần bằng đối tượng mock (`when(...).thenReturn(...)`). Tuy nhiên, ứng dụng bị crash hoặc vỡ khi các thành phần được ghép nối với nhau trong runtime thật do lỗi đăng ký DI, lệch chuẩn parse JSON, hủy vòng đời component, hoặc xung đột timing trên stream event-bus.
    32	2. **Thiếu Provider Web Quality ở Gate 4**: Hệ thống điều phối chất lượng (`d3nexus:quality_check`) đã có sẵn provider chuyên biệt cho Flutter, Android, iOS, Rust và Python, nhưng hoàn toàn thiếu provider `web-quality-check`. Dẫn đến:
    33	   - Tại `D3Nexus`, Gate 4 chỉ xác thực `rust-core` (`d3nexus:rust-quality-check`), bỏ quên hoàn toàn ứng dụng web Astro + Vanilla TypeScript (`apps/learning-web`).
    34	   - Tại `lyrics-sync`, Gate 4 chỉ xác thực `python-core` (`d3nexus:python-quality-check`), bỏ quên hoàn toàn 17 file Vanilla JavaScript (`src/lyrics_sync/preview/static/*.js`).
    35	3. **Bài kiểm thử E2E giả lập chỉ chạy trong Node**: Nhiều bài test nằm dưới thư mục `tests/e2e/` thực chất chỉ chạy bằng `node:test` mà không hề render HTML thật, không kiểm tra kết nối Custom Elements, và không xác thực sự kiện DOM hay tọa độ hiển thị thực tế (`getBoundingClientRect`).
    36	4. **Sự ngụy biện của AI (AI Rationalization)**: Các AI coding agent thường xuyên tự tìm đường tắt: khẳng định test Node là đủ, bỏ qua lỗi console trình duyệt, và né tránh việc chạy trình duyệt headless.
    37	
    38	## Mục tiêu và Giới hạn
    39	
    40	### Mục tiêu
    41	- Xây dựng provider chuẩn hóa `web-quality-check` tuân thủ Hợp đồng Kết quả Provider v1 cho các dự án Astro TypeScript và Vanilla JavaScript.
    42	- Xóa bỏ điểm mù tại Gate 4 bằng cách kích hoạt đăng ký đa provider đồng thời trong `D3Nexus` (`rust-core` + `learning-web`) và `lyrics-sync` (`python-core` + `preview-ui`).
    43	- Thực thi nghiêm ngặt Chuẩn Kiểm thử 3 Lớp: Tier A (Unit), Tier C1 (Tích hợp Dưới da với DI thật và In-memory DB), và Tier C2 (Tích hợp Trình duyệt Headless với Playwright và Zero-Console-Error).
    44	- Đưa Bảng Chống Ngụy biện và Cơ chế Phản biện Nghi vấn (lấy cảm hứng từ `addyosmani/agent-skills`) vào các quy trình kỹ năng.
    45	- Tự động hóa quá trình xác nhận của con người bằng cách tự sinh tài liệu hướng dẫn 3–5 bước `manual_smoke_checklist.md` sau khi hoàn tất epic, giảm thời gian bấm tay từ 30 phút xuống còn 2 phút.
    46	
    47	### Giới hạn
    48	- Không migrate 17 file Vanilla JavaScript trong `lyrics-sync` sang TypeScript (việc kiểm tra kiểu dữ liệu được thực hiện tại chỗ thông qua JSDoc `// @ts-check` và `jsconfig.json`).
    49	- Không thay thế bộ unit test hiện có trong `D3Nexus` hay `lyrics-sync` (các bài test nhanh này vẫn được giữ lại làm Tier A).
    50	- Không yêu cầu bật emulator thiết bị nặng nề cho các cổng duyệt cục bộ PR/Epic (các bài test Tier C chạy headless qua Playwright và môi trường harness VM).
    51	
    52	## Kiến trúc và Chuẩn Kiểm thử 3 Lớp
    53	
    54	Kiến trúc thiết lập 3 phân tầng kiểm thử rõ ràng trên cả mobile và web:
    55	
    56	1. **Tier A — Kiểm thử Đơn vị (Unit Testing)**:
    57	   - Phạm vi: Thuật toán thuần, state machine toán học, bộ parse dữ liệu độc lập, và hàm tiện ích.
    58	   - Thực thi: Trong tiến trình (Node.js, Dart VM, JVM, Python VM).
    59	   - Mock: Cho phép mock các dependency bên ngoài. Tốc độ: <10ms mỗi test.
    60	2. **Tier C1 — Kiểm thử Tích hợp Dưới da (Mobile & Backend)**:
    61	   - Phạm vi: Controller giao diện (BLoC / ViewModel) xuyên suốt xuống kho lưu trữ cục bộ, bộ nhớ đệm và tuần tự hóa dữ liệu.
    62	   - Bất biến: Zero-Domain-Mock. Nghiêm cấm mock UseCase hoặc Repository của domain. Bắt buộc dùng DI container thật và cơ sở dữ liệu in-memory (SQLite `:memory:`, Room in-memory).
    63	   - Ranh giới mạng: Mock tại socket HTTP bằng các fixture JSON chuẩn từ `shared-contracts/`.
    64	3. **Tier C2 — Kiểm thử Tích hợp Trình duyệt Headless (Web)**:
    65	   - Phạm vi: Render DOM thật, Custom Elements, controller Vanilla JS/TS, thao tác click của người dùng, chuyển trang và định vị popover trực quan.
    66	   - Bất biến: Zero-Console-Error. Bất kỳ lỗi `console.error` hoặc ngoại lệ trang chưa xử lý nào đều khiến bài test trượt ngay lập tức.
    67	   - Ranh giới mạng: Chặn tại tầng socket trình duyệt thông qua `page.route()` của Playwright và trả về fixture JSON chuẩn từ hợp đồng.
    68	
    69	## Chống Ngụy biện và Cơ chế Phản biện Nghi vấn
    70	
    71	Học hỏi từ các nguyên tắc của `addyosmani/agent-skills`, tất cả quy trình lập trình và kiểm thử đều thực thi 4 quy tắc chống ngụy biện:
    72	
    73	| Lời bào chữa của Agent | Quy tắc Phản biện Bắt buộc |
    74	| :--- | :--- |
    75	| "Một bài test Node.js là đủ để chứng minh tính năng web UI hoạt động." | **BỊ TỪ CHỐI**: Test Node chỉ chứng minh logic dữ liệu thuần. 80% lỗi web xảy ra ở truy vấn DOM, nổi bọt sự kiện và render CSS. Tier C bắt buộc phải chạy qua Playwright headless. |
    76	| "Component này đơn giản; mock cứng dữ liệu trong stub là đủ." | **BỊ TỪ CHỐI**: Stub cấp method bỏ qua việc kiểm tra giải mã JSON và interceptor mạng. Bắt buộc phải dùng fixture cấp mạng (wire-level) từ `shared-contracts/`. |
    77	| "Các lỗi đỏ trong console trình duyệt chỉ là cảnh báo vô hại." | **BỊ TỪ CHỐI**: Quy tắc Zero-Console-Error đánh trượt Gate 4 đối với bất kỳ lỗi console hoặc ngoại lệ chưa xử lý nào trong trình duyệt. |
    78	| "Tôi không bật được simulator điện thoại nên tôi sẽ viết unit test thay thế." | **BỊ TỪ CHỐI**: Tier C mobile bắt buộc phải dùng Kiểm thử Dưới da với DI thật và lưu trữ in-memory. Unit test thuần túy không được gắn mác Tier C. |
    79	
    80	Dưới Cơ chế Phản biện Nghi vấn (`CLAIM -> EXTRACT -> DOUBT -> RECONCILE`), Gate 4 sẽ rà soát để đảm bảo bài test Tier C thực sự kích hoạt luồng code production mà không mock hệ thống chính đang được kiểm thử.
    81	
    82	## Đặc tả Kỹ thuật Provider Web Quality
    83	
    84	Một kỹ năng mới `d3nexus:web-quality-check` được xây dựng tại thư mục `skills/web-quality-check/`:
    85	
    86	1. **Hợp đồng Gọi thực thi**: Tuân thủ Hợp đồng Kết quả Provider v1, nhận `{ "profile": "<profile>", "base_ref": "<base_ref>", "repository_sha": "<sha>" }`.
    87	2. **File Cấu hình**: Đọc file `.agents/quality/web-quality.json` từ thư mục gốc của repository.
    88	3. **Các Khả năng (Capabilities)**:
    89	   - `type_check`: Chạy `astro check` hoặc `tsc --noEmit` cho dự án TypeScript, hoặc `tsc --project jsconfig.json` cho dự án Vanilla JavaScript.
    90	   - `lint`: Chạy linter của dự án (ESLint, Biome, hoặc Astro linter).
    91	   - `test_unit`: Thực thi bộ unit test in-memory nhanh (Tier A).
    92	   - `test_e2e`: Khởi chạy bộ Playwright headless (Tier C2) tích hợp bộ giám sát Zero-Console-Error.
    93	   - `contracts`: Thực hiện kiểm tra chênh lệch hợp đồng đa repo.
    94	4. **Công cụ Xác thực**: Cung cấp script `validate_web_quality.py` để đảm bảo tính hợp lệ của schema và sự hiện diện của các binary thực thi trước khi chạy.
    95	
    96	## Tích hợp Registry Đa Repo và Gate 4 Đa Nền tảng
    97	
    98	Nhạc trưởng Gate 4 gốc (`d3nexus:quality_check`) thực hiện kích hoạt đa provider song song trên các kho lưu trữ:
    99	
   100	- **`D3Nexus` (`.agents/quality/check_quality.json`)**:
   101	  - Provider 1: `rust-core` (`d3nexus:rust-quality-check`) cho nhân Rust, biên dịch WASM và test hệ thống.
   102	  - Provider 2: `learning-web` (`d3nexus:web-quality-check`) cho template Astro, controller Vanilla TypeScript và bộ test Playwright.
   103	- **`lyrics-sync` (`.agents/quality/check_quality.json`)**:
   104	  - Provider 1: `python-core` (`d3nexus:python-quality-check`) cho endpoint FastAPI, logic worker và test pytest.
   105	  - Provider 2: `preview-ui` (`d3nexus:web-quality-check`) cho kiểm tra kiểu Vanilla JS tĩnh và test Playwright trên Chrome.
   106	- **`nexus` (`.agents/quality/check_quality.json`)**:
   107	  - Provider 1: `flutter-core` (`d3nexus:flutter-quality-check`) thực thi Kiểm thử Widget Dưới da với DI thật và WireMock.
   108	
   109	## Nâng cấp Dev-Designer và Dev-Implementation
   110	
   111	1. **`dev-designer` (Stage 2)**:
   112	   - Khi phát hiện dự án Web, dòng `Integration results:` trong HLD bắt buộc phải trỏ tới kết quả của Playwright headless (`build/test-results/playwright.json`).
   113	   - Các kịch bản BDD cho Tier C phải bao gồm kỳ vọng tương tác DOM cụ thể và xác nhận qua wiremock.
   114	2. **`dev-implementation` (Stage 3)**:
   115	   - Nhúng Bảng Chống Ngụy biện trực tiếp vào quá trình thực thi tác vụ.
   116	   - Xác thực rằng các tác vụ tuyên bố bao phủ kịch bản Tier C thực sự chạy test trình duyệt headless hoặc test dưới da thật.
   117	   - Tạm dừng và báo cáo `BLOCKED` nếu code test mock chính component đang được kiểm thử.
   118	
   119	## Tự động Sinh Kịch bản Smoke Test Bấm tay
   120	
   121	Sau khi hoàn thành thành công tất cả tác vụ và Gate 4 trả về kết quả máy PASS, `dev-implementation` sẽ tự động sinh ra một tài liệu hỗ trợ con người:
   122	- Đường dẫn: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
   123	- Nội dung: 3 đến 5 bước thủ công ngắn gọn, rõ ràng được trích xuất trực tiếp từ các kịch bản BDD Happy Path chính (gồm URL mục tiêu, hành động của người dùng, kết quả trực quan quan sát được).
   124	- Lợi ích: Rút ngắn thời gian kiểm thử tự do của lập trình viên từ 30 phút mò mẫm xuống còn đúng 2 phút xác nhận có định hướng.
   125	
   126	## Rủi ro và Giải pháp Giảm thiểu
   127	
   128	| Rủi ro | Tác động | Chiến lược Giảm thiểu |
   129	| :--- | :--- | :--- |
   130	| Chi phí cài đặt Playwright trong CI / máy cục bộ | Gate 4 chạy chậm | Chỉ sử dụng Chromium headless; cache binary trình duyệt; profile `pr` chỉ chạy unit test, profile `epic` mới chạy Playwright. |
   131	| Xung đột port khi khởi chạy preview server | Test không ổn định (flaky) | Cấu hình `webServer` của Playwright bind vào port động hoặc cổng chuyên dụng có probe kiểm tra healthcheck. |
   132	| Cảnh báo console cũ của thư viện kích hoạt Zero-Console-Error | Đánh trượt nhầm (false positive) | Cho phép cấu hình danh sách loại trừ (allowlist) cho các cảnh báo bên thứ ba vô hại đã biết trong `.agents/quality/web-quality.json`. |
   133	
   134	## Kế hoạch Kiểm chứng
   135	
   136	1. **Kiểm chứng Hợp đồng Provider**:
   137	   - Chạy `validate_web_quality.py` đối với file cấu hình mẫu `.agents/quality/web-quality.json`.
   138	   - Chạy `quality_check` với profile `epic` tại `D3Nexus` và kiểm tra cả `rust-core` lẫn `learning-web` đều xuất ra phán quyết được chứng thực.
   139	2. **Kiểm chứng Zero-Console-Error của Playwright**:
   140	   - Cố tình chèn 1 dòng `console.error` vào trang test; xác nhận Playwright và Gate 4 báo cáo chính xác trạng thái `FAIL`.
   141	   - Sửa lỗi và xác nhận Gate 4 chuyển sang `PASS`.
   142	3. **Kiểm chứng Type-Checking cho Vanilla JS**:
   143	   - Chạy `tsc --project jsconfig.json` trên thư mục `lyrics-sync/src/lyrics_sync/preview/static/` và xác nhận kết quả kiểm tra kiểu dữ liệu sạch sẽ.
   144	4. **Kiểm chứng Tự sinh Checklist Bấm tay**:
   145	   - Xác nhận rằng việc hoàn tất epic sẽ tạo ra file `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` chứa 3–5 bước rõ ràng.
     1	# Epic: Web Quality Check Provider và Integration Quality Gate
     2	
     3	## Mục lục
     4	
     5	- [Mục lục](#mục-lục)
     6	- [Meta Data](#meta-data)
     7	- [Bối cảnh](#bối-cảnh)
     8	- [Mục tiêu và Giới hạn](#mục-tiêu-và-giới-hạn)
     9	- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
    10	  - [Kiến trúc Tổng thể](#kiến-trúc-tổng-thể)
    11	  - [Use Cases](#use-cases)
    12	  - [Sequence Diagram](#sequence-diagram)
    13	  - [Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-ranh-giới)
    14	  - [Các Kịch bản BDD Toàn diện](#các-kịch-bản-bdd-toàn-diện)
    15	- [Môi trường Kiểm chứng](#môi-trường-kiểm-chứng)
    16	- [Tác động Hợp đồng Dùng chung](#tác-động-hợp-đồng-dùng-chung)
    17	- [Chiến lược Triển khai và Giảm thiểu Rủi ro](#chiến-lược-triển-khai-và-giảm-thiểu-rủi-ro)
    18	- [Phân rã Tác vụ Kanban](#phân-rã-tác-vụ-kanban)
    19	
    20	## Meta Data
    21	
    22	- **Tên Epic**: `web_quality_check_and_integration_gate`
    23	- **Slug Epic**: `web-quality-check-and-integration-gate`
    24	- **Trạng thái**: Packaged
    25	- **Phiên bản Mục tiêu**: v1.2.0
    26	- **Nền tảng**: Polyglot / Quality Architecture
    27	- **Tài liệu Đặc tả Gốc**: [2026-11-04-web-quality-check-and-integration-gate-design.vi.md](./2026-11-04-web-quality-check-and-integration-gate-design.vi.md)
    28	
    29	## Bối cảnh
    30	
    31	Trong hệ sinh thái đa repo (`D3Nexus`, `lyrics-sync`, `nexus`), các kỹ sư đối mặt với khoảng cách lớn giữa thiết kế kiến trúc và hành vi thực tế khi chạy. Khoảng cách này buộc lập trình viên phải kiểm thử thủ công (bấm tay) rất nhiều trên thiết bị và trình duyệt trước mỗi đợt release:
    32	- Unit test pass 100% xanh bằng mock, nhưng gãy khi chạy thật do lỗi đăng ký DI, lỗi giải mã JSON, và lỗi gắn sự kiện DOM.
    33	- Gate 4 (`quality_check`) thiếu provider cho Web, bỏ quên hoàn toàn `D3Nexus` (`apps/learning-web`) và `lyrics-sync` (17 file Vanilla JS).
    34	- AI coding agent thường xuyên tự tìm đường tắt, né tránh chạy trình duyệt headless và bỏ qua lỗi console.
    35	
    36	## Mục tiêu và Giới hạn
    37	
    38	### Mục tiêu
    39	- Xây dựng provider `web-quality-check` tuân thủ Hợp đồng Kết quả Provider v1 cho các dự án Astro TypeScript và Vanilla JavaScript.
    40	- Kích hoạt điều phối chất lượng đa nền tảng (polyglot) tại Gate 4 trên cả `D3Nexus` và `lyrics-sync`.
    41	- Thực thi Chuẩn Kiểm thử 3 Lớp (Tier A Unit, Tier C1 Dưới da Mobile/Backend, Tier C2 Trình duyệt Headless Web).
    42	- Đưa Bảng Chống Ngụy biện và Cơ chế Phản biện Nghi vấn từ `addyosmani/agent-skills` vào quy trình kỹ năng.
    43	- Tự động sinh tài liệu 3–5 bước `manual_smoke_checklist.md` sau khi hoàn thành epic để rút ngắn thời gian bấm tay từ 30 phút xuống còn 2 phút.
    44	
    45	### Giới hạn
    46	- Không chuyển đổi 17 file Vanilla JS trong `lyrics-sync` sang TypeScript (kiểm tra kiểu dữ liệu tại chỗ qua JSDoc và `jsconfig.json`).
    47	- Không viết lại các unit test nhanh hiện có.
    48	- Không ép buộc bật emulator thiết bị cho các cổng duyệt cục bộ PR/Epic.
    49	
    50	## Kiến trúc và Thiết kế Kỹ thuật
    51	
    52	### Kiến trúc Tổng thể
    53	
    54	```mermaid
    55	flowchart TD
    56	    QC["Gate 4: quality_check (Nhạc trưởng Trung lập)"] --> REG["Đọc .agents/quality/check_quality.json"]
    57	    REG --> FANOUT{"Kích hoạt Song song các Provider"}
    58	    FANOUT --> P_RUST["rust-quality-check (Nhân D3Nexus)"]
    59	    FANOUT --> P_PY["python-quality-check (Backend lyrics-sync)"]
    60	    FANOUT --> P_FLUTTER["flutter-quality-check (Mobile nexus)"]
    61	    FANOUT --> P_WEB["web-quality-check (MỚI: Astro TS + Vanilla JS)"]
    62	    
    63	    subgraph WEB_PROVIDER["Các Khả năng của web-quality-check"]
    64	        direction TB
    65	        CAP_TYPE["Kiểm tra Kiểu (astro check / tsc --noEmit / jsconfig.json)"]
    66	        CAP_LINT["Linter (ESLint / Biome / Astro linter)"]
    67	        CAP_UNIT["Tier A Unit Tests (Node / Vitest)"]
    68	        CAP_E2E["Tier C2 Headless Playwright + Bộ Chặn Zero-Console-Error"]
    69	    end
    70	    
    71	    P_WEB --> WEB_PROVIDER
    72	    FANOUT --> AGG["Tổng hợp Kết quả (FAIL > BLOCKED > PASS)"]
    73	    AGG --> SMOKE["Tự sinh manual_smoke_checklist.md (3-5 Bước)"]
    74	    SMOKE --> VERDICT["Chứng nhận Gate 4 Hợp lệ"]
    75	```
    76	
    77	### Use Cases
    78	
    79	```mermaid
    80	flowchart LR
    81	    DEV["Kiến trúc sư Con người"] --> UC1["Cấu hình Registry Đa Provider"]
    82	    DEV --> UC2["Kích hoạt Kiểm chuẩn Gate 4"]
    83	    DEV --> UC3["Duyệt Checklist Bấm tay (2 phút xác nhận)"]
    84	    
    85	    AGENT["Lập trình viên AI"] --> UC4["Thực thi Task có Chặn Ngụy biện"]
    86	    AGENT --> UC5["Chạy Playwright Headless Zero-Console-Error"]
    87	    AGENT --> UC6["Kiểm tra Kiểu Vanilla JS qua JSDoc"]
    88	```
    89	
    90	### Sequence Diagram
    91	
    92	```mermaid
    93	sequenceDiagram
    94	    autonumber
    95	    actor Human as Kiến trúc sư Con người
    96	    participant Gate as quality_check (Gate 4)
    97	    participant Web as web-quality-check
    98	    participant Playwright as Chromium Headless
    99	    participant Gen as Bộ Sinh Checklist
   100	
   101	    Human->>Gate: Kích hoạt @quality_check (profile: epic)
   102	    Gate->>Gate: Đọc .agents/quality/check_quality.json
   103	    Gate->>Web: Gọi provider kèm commit SHA
   104	    Web->>Web: Chạy kiểm tra kiểu & linter
   105	    Web->>Playwright: Khởi chạy Playwright headless kèm wiremock
   106	    Playwright->>Playwright: Render DOM & xác thực Zero-Console-Error
   107	    Playwright-->>Web: Trả về trace & bằng chứng thực thi
   108	    Web-->>Gate: Xuất Tài liệu Kết quả Provider (PASS)
   109	    Gate->>Gen: Trích xuất các luồng Happy Path chính
   110	    Gen-->>Gate: Xuất file manual_smoke_checklist.md
   111	    Gate-->>Human: Báo cáo Gate 4 LGTM + Checklist Bấm tay 2 phút
   112	```
   113	
   114	### Kế hoạch Kiểm thử Tích hợp và Ma trận Ranh giới
   115	
   116	```text
   117	Integration test roots: tests/, skills/web-quality-check/tests/
   118	Protected paths: .agents/quality/**, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md
   119	Integration results: python3 -m pytest tests/ -> build/test-results/pytest.xml
   120	```
   121	
   122	| Mối ghép Ranh giới | Chiến lược Kiểm thử | Mục tiêu Kiểm chứng |
   123	| :--- | :--- | :--- |
   124	| Hợp đồng Provider | Payload giả lập gọi `quality_check` | Xác thực tổng hợp trạng thái và tuân thủ schema |
   125	| Astro Web / TypeScript | Playwright Headless + Fixture wiremock | Xác thực phần tử DOM, Custom Elements, và zero console error |
   126	| Vanilla JS Preview | `tsc --project jsconfig.json` + Playwright | Xác thực an toàn kiểu dữ liệu không cần đuôi `.ts`, ngăn ngừa crash |
   127	| Luồng Workflow Tác vụ | Rà soát BDD traceability & Anti-Rationalization | Xác thực tác vụ từ chối mock ảo Tier C và yêu cầu chạy test tích hợp thật |
   128	
   129	## Môi trường Kiểm chứng
   130	
   131	- Môi trường thực thi: CLI cục bộ macOS / Linux có cài sẵn Node.js v20+, Python 3.11+, và trình duyệt Chromium Playwright.
   132	- Không phụ thuộc mạng ngoài: Mọi lệnh gọi mạng bên ngoài trong test đều bị chặn tại socket.
   133	- Cách ly hệ thống tệp: Các lượt chạy test diễn ra trong thư mục tạm độc lập, không làm biến đổi git working tree.
   134	
   135	### Các Kịch bản BDD Toàn diện
   136	
   137	Bộ test bao phủ đủ 5 chiều với tiền tố `[WQG-]`:
   138	1. **Happy Paths (`WQG-HP-xx`)**: Thực thi provider thành công, Playwright headless pass, type check Vanilla JS sạch, và tự sinh checklist bấm tay.
   139	2. **Edge Cases (`WQG-EC-xx`)**: Thiếu capability, cấu hình web bị khuyết, bộ test rỗng, và cảnh báo console bên thứ ba.
   140	3. **Chuyển đổi Trạng thái (`WQG-ST-xx`)**: Chuyển trạng thái linh hoạt từ `BLOCKED` sang `PASS` khi sửa cấu hình, và đồng bộ trạng thái task.
   141	4. **Bất đồng bộ & Đồng thời (`WQG-AR-xx`)**: Kích hoạt đa provider đồng thời trong Gate 4, khởi động webServer Playwright không gây nghẽn.
   142	5. **Thất bại & Khả năng Phục hồi (`WQG-FR-xx`)**: Bắt lỗi console error gây fail ngay lập tức, bẫy ngoại lệ chưa xử lý, và phát hiện hợp đồng bị gãy.
   143	
   144	## Tác động Hợp đồng Dùng chung
   145	
   146	Không có — đây là bộ kỹ năng provider chất lượng và cải tiến quy trình độc lập.
   147	
   148	## Chiến lược Triển khai và Giảm thiểu Rủi ro
   149	
   150	- **Giai đoạn 1**: Xây dựng skill `web-quality-check` và kiểm chứng hợp đồng bằng unit và integration test.
   151	- **Giai đoạn 2**: Bổ sung bộ giám sát Zero-Console-Error cho Playwright và bộ kiểm tra `jsconfig.json` cho Vanilla JS.
   152	- **Giai đoạn 3**: Cập nhật `dev-designer`, `dev-implementation` và `test-driven-development` với Bảng Chống Ngụy biện và hướng dẫn Kiểm thử Dưới da.
   153	- **Giai đoạn 4**: Cấu hình registry đa provider tại `D3Nexus` và `lyrics-sync`, kiểm chứng Gate 4 chạy đa nền tảng.
   154	
   155	## Phân rã Tác vụ Kanban
   156	
   157	- [Task 01: Web Quality Check Skill và Hợp đồng Provider](./task_01_web_quality_check_skill_and_contract.md)
   158	- [Task 02: Bộ Giám sát Playwright Zero-Console-Error và Fixtures](./task_02_playwright_zero_error_watchdog.md)
   159	- [Task 03: Cấu hình Kiểm tra Kiểu Vanilla JS qua JSDoc](./task_03_jsconfig_and_vanilla_js_type_checker.md)
   160	- [Task 04: Registry Gate 4 Đa Nền tảng và Kích hoạt Song song](./task_04_polyglot_gate4_registry_and_fanout.md)
   161	- [Task 05: Quy tắc Quy trình Chống Ngụy biện và Phản biện Nghi vấn](./task_05_anti_rationalization_and_doubt_driven_workflow.md)
   162	- [Task 06: Bộ Tự động Sinh Kịch bản Smoke Test Bấm tay](./task_06_automated_manual_smoke_checklist_generator.md)

codex
Tôi đã đọc đủ các artefact EN/VI. Các điểm cần đối chiếu kỹ với nguồn là hợp đồng kết quả provider, nơi thực sự điều phối fan-out, và khả năng công cụ hiện tại từ chối Tier C dùng mock như BDD yêu cầu.

exec
/bin/zsh -lc 'nl -ba skills/quality_check/references/provider-result-contract.md; nl -ba skills/quality_check/SKILL.md' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	# Provider Result Contract
     2	
     3	## Overview
     4	
     5	Quality providers communicate findings and verification evidence through machine-readable result documents.
     6	Each provider produces one structured result document bound to the immutable repository commit SHA being verified.
     7	
     8	The contract is validated mechanically using [provider-result.schema.json](../resources/schemas/provider-result.schema.json)
     9	and the contract validator script [validate_quality_contract.py](../resources/scripts/validate_quality_contract.py).
    10	
    11	## Result Structure
    12	
    13	```json
    14	{
    15	  "provider_id": "rust-core",
    16	  "contract_version": 1,
    17	  "profile": "epic",
    18	  "repository_sha": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
    19	  "status": "PASS",
    20	  "checks": [
    21	    {
    22	      "id": "cargo-check",
    23	      "category": "compile",
    24	      "status": "PASS",
    25	      "source": "cargo check --all-targets",
    26	      "duration": 12.4,
    27	      "summary": "Compilation check succeeded with 0 warnings",
    28	      "evidence_refs": ["check-log"]
    29	    }
    30	  ],
    31	  "coverage": {
    32	    "lines": {
    33	      "measured": 0.88,
    34	      "threshold": 0.85
    35	    }
    36	  },
    37	  "evidence": [
    38	    {
    39	      "id": "check-log",
    40	      "type": "command",
    41	      "source": "cargo check",
    42	      "location": "artifacts/cargo-check.log"
    43	    }
    44	  ],
    45	  "started_head": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
    46	  "finished_head": "5d8b7b0f1b7a9c6f7c8f6498e69c3d6f1e0a4123",
    47	  "duration": 45.2,
    48	  "blockers": [],
    49	  "warnings": []
    50	}
    51	```
    52	
    53	## Schema Specification
    54	
    55	### Top-Level Fields
    56	
    57	- `provider_id` (string, required): Identifier matching the provider registration.
    58	- `contract_version` (integer, required): Must be integer `1`.
    59	- `profile` (string, required): Quality profile matching the invocation (`pr`, `epic`, `scheduled`, `release`).
    60	- `repository_sha` (string, required): 40-character hexadecimal git commit SHA.
    61	- `status` (string, required): Overall provider verdict: `PASS`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`.
    62	- `checks` (array of objects, required): Structured breakdown of individual checks performed.
    63	- `coverage` (object, required): Measured code coverage and required thresholds.
    64	- `evidence` (array of objects, required): Verifiable evidence records confirming executed checks.
    65	- `started_head` (string, required): Git HEAD SHA at the start of provider execution.
    66	- `finished_head` (string, required): Git HEAD SHA at the conclusion of provider execution.
    67	- `duration` (number, required): Execution duration in seconds (must be non-negative).
    68	- `blockers` (array, required): Actionable blocking issues requiring resolution.
    69	- `warnings` (array, required): Non-blocking advisory findings.
    70	
    71	### Check Object Fields
    72	
    73	- `id` (string, required): Unique check identifier within the provider.
    74	- `category` (string, required): Category classification (e.g. `lint`, `compile`, `unit-test`, `security`, `architecture`).
    75	- `status` (string, required): Individual check verdict (`PASS`, `FAIL`, `BLOCKED`, `NOT_APPLICABLE`).
    76	- `source` (string, required): Executed command or audit tool source.
    77	- `duration` (number, required): Check duration in seconds.
    78	- `summary` (string, required): Human-readable summary of the check result.
    79	- `evidence_refs` (array of strings, required): List of evidence identifiers referenced by this check.
    80	- `not_applicable_reason` (object, optional): Mandatory when status is `NOT_APPLICABLE`. Contains `code` and `detail`.
    81	
    82	### Evidence Object Fields
    83	
    84	- `id` (string, required): Evidence identifier referenced by checks.
    85	- `type` (string, required): Evidence type (`command`, `applicability`, `audit`, `log`, `report`).
    86	- `source` (string, required): Producing tool or command.
    87	- `location` (string, required): File path or URL to evidence output.
    88	- `digest` (string, optional): SHA256 cryptographic digest of the evidence content.
    89	
    90	## Contract Rules and Verification Boundaries
    91	
    92	1. **Identity and SHA Integrity**: `started_head`, `finished_head`, and `repository_sha` must match the requested SHA. Any divergence invalidates evidence as stale and produces `BLOCKED`.
    93	2. **Evidence Resolution**: Every reference in `evidence_refs` must resolve to a valid entry in `evidence`.
    94	3. **NOT_APPLICABLE Constraints**: `NOT_APPLICABLE` requires a structured reason (`profile_policy`, `scope_unmodified`, `capability_not_configured`, `target_absent`, `platform_not_applicable`) and evidence of type `applicability`. Missing tools, timeouts, or command errors produce `BLOCKED` or `FAIL`, never `NOT_APPLICABLE`.
    95	4. **Deterministic Precedence**: `FAIL` > `BLOCKED` > `PASS`. Product defects outrank infrastructure blockage.
     1	---
     2	name: quality_check
     3	description: Platform-neutral quality gatekeeper and orchestrator that discovers project-registered providers from .agents/quality/check_quality.json, validates versioned contracts, aggregates verdicts (FAIL > BLOCKED > PASS), and renders immutable SHA-bound executive reports.
     4	---
     5	
     6	# Platform-Neutral Quality Check Orchestrator
     7	
     8	## Overview
     9	
    10	You are the Master Quality Orchestrator and Governance Gatekeeper. Your role is platform-neutral: you do not embed
    11	ecosystem-specific compilers, testing tools, or heuristics. Instead, you act as the composition root for project quality,
    12	discovering registered capability providers via dependency injection, fanning out execution across all selected providers,
    13	validating versioned contracts, and synthesizing a single deterministic Gate 4 verdict bound to an immutable commit SHA.
    14	
    15	Execution is strictly read-only: quality certification verifies existing code and never mutates source files or applies
    16	auto-fix scripts during verification.
    17	
    18	## Architecture and Execution Sequence
    19	
    20	```mermaid
    21	flowchart TD
    22	    CALLER["Caller supplies profile, base ref, and target SHA"] --> NORMALIZE["Step 0: Normalize request and verify repository SHA"]
    23	    NORMALIZE --> REGISTRY["Step 1: Load .agents/quality/check_quality.json"]
    24	    REGISTRY --> VALIDATE["Step 2: Validate registry and select providers"]
    25	    VALIDATE --> FANOUT["Step 3: Fan out invocation across all selected providers"]
    26	    FANOUT --> HEAD_CHECK["Step 4: Verify finished repository HEAD matches initial SHA"]
    27	    HEAD_CHECK --> CONTRACT_CHECK["Step 5: Validate provider results and reconcile plan"]
    28	    CONTRACT_CHECK --> REDUCE["Step 6: Aggregate statuses and render executive report"]
    29	    REDUCE --> VERDICT{"Overall status"}
    30	    VERDICT -->|"PASS"| LGTM["Render Gate 4 LGTM for verified SHA"]
    31	    VERDICT -->|"FAIL"| REJECT_FAIL["Report product defects"]
    32	    VERDICT -->|"BLOCKED"| REJECT_BLOCKED["Report infrastructure blockers"]
    33	```
    34	
    35	## Step-by-Step Orchestration Workflow
    36	
    37	### Step 0: Input Normalization and Invocation Contract
    38	
    39	Normalize caller parameters:
    40	- `profile`: Defaults to `pr` for direct interactive invocations. Formal lifecycle callers (`dev-implementation`, `dev-lifecycle`) must pass explicit profile (`epic`, `scheduled`, `release`).
    41	- `base_ref`: Branch or ref used for blast radius, changed-file scope, and impact analysis (e.g. `main`, `develop`).
    42	- `repository_sha`: The 40-character commit SHA to certify. If omitted, resolve immediately using `git rev-parse HEAD`.
    43	
    44	Construct the immutable invocation payload:
    45	
    46	```json
    47	{
    48	  "contract_version": 1,
    49	  "profile": "<profile>",
    50	  "base_ref": "<base_ref>",
    51	  "repository_sha": "<sha>"
    52	}
    53	```
    54	
    55	Validate the invocation using [validate_quality_contract.py](resources/scripts/validate_quality_contract.py). If invocation parameters are invalid, halt immediately with status `BLOCKED`.
    56	
    57	### Step 1: Project Registry Loading
    58	
    59	Load the project quality manifest located at `.agents/quality/check_quality.json` from the repository root:
    60	
    61	```bash
    62	python3 skills/quality_check/resources/scripts/validate_quality_contract.py registry .agents/quality/check_quality.json --profile "<profile>"
    63	```
    64	
    65	Fail-closed rules:
    66	- If `.agents/quality/check_quality.json` is missing or unreadable: halt with status `BLOCKED`. Never attempt fallback platform detection.
    67	- If the registry contains unknown fields, unsupported schema versions, duplicate provider IDs, or empty provider lists: halt with status `BLOCKED`.
    68	- If no provider matches the requested profile: return `BLOCKED` with finding `empty_selection`.
    69	- If a selected provider's skill is unresolvable in the active environment: halt with status `BLOCKED`.
    70	
    71	### Step 2: Provider Invocation Fan-Out
    72	
    73	For every provider selected by the registry for the requested profile:
    74	1. Provide the identical immutable invocation payload, adding the provider's `provider_id` and `required` flag.
    75	2. Invoke the provider skill (e.g. `d3nexus:rust-quality-check`).
    76	3. Providers execute read-only checks matching their declared profile capabilities.
    77	4. Collect one structured result document per provider.
    78	
    79	Independent providers may run concurrently. Output ordering is never dependent on execution order.
    80	
    81	### Step 3: Stale-Evidence and Final HEAD Verification
    82	
    83	Before accepting provider evidence, verify current repository HEAD:
    84	
    85	```bash
    86	git rev-parse HEAD
    87	```
    88	
    89	If current HEAD differs from `repository_sha`, repository state drifted during execution. All collected evidence is rejected as stale, and the overall run returns `BLOCKED`.
    90	
    91	### Step 4: Result Contract Validation and Plan Reconciliation
    92	
    93	Reconcile collected provider results against the execution plan:
    94	
    95	```bash
    96	python3 skills/quality_check/resources/scripts/validate_quality_contract.py reconcile "<plan_json>" --results "<result_files...>"
    97	```
    98	
    99	Validation guarantees:
   100	- Every result document matches [provider-result.schema.json](resources/schemas/provider-result.schema.json).
   101	- Identity fields (`provider_id`, `profile`, `repository_sha`, `started_head`, `finished_head`) match the invocation.
   102	- Missing results or duplicate results for a provider generate synthetic `BLOCKED` findings.
   103	- Evidence references resolve cleanly to recorded evidence artifacts.
   104	
   105	### Step 5: Deterministic Aggregation and Executive Report
   106	
   107	Reduce validated results into a unified verdict:
   108	
   109	```bash
   110	python3 skills/quality_check/resources/scripts/aggregate_quality_results.py "<plan_json>" "<result_files...>" --markdown
   111	```
   112	
   113	Precedence policy:
   114	$$\text{FAIL} > \text{BLOCKED} > \text{PASS}$$
   115	
   116	1. **FAIL**: If any provider reported `FAIL`, the overall verdict is `FAIL`. All defects and blockers remain visible.
   117	2. **BLOCKED**: If no failure occurred, but any required provider reported `BLOCKED` or failed reconciliation, the overall verdict is `BLOCKED`.
   118	3. **PASS**: Granted if and only if every required provider passed.
   119	4. **NOT_APPLICABLE**: An optional provider may be neutral if supported by applicability evidence. A required provider with only `NOT_APPLICABLE` checks is converted to `BLOCKED`.
   120	
   121	### Step 6: Gate 4 Certification
   122	
   123	Only an aggregated verdict of **PASS** bound to the candidate commit SHA qualifies for Gate 4 `🟢 LGTM`. If the verdict is `FAIL` or `BLOCKED`, render the complete executive report detailing all blockers and warnings, and stop.
   124	
   125	## Reference Contracts and Resources
   126	
   127	- [Provider Registry Contract](references/provider-registry-contract.md): Format and rules for `.agents/quality/check_quality.json`.
   128	- [Provider Result Contract](references/provider-result-contract.md): Schema and constraints for provider result documents.
   129	- [Result Aggregation Contract](references/aggregation-contract.md): Deterministic precedence and status reduction model.
   130	- [Executive Report Format](references/executive-report-format.md): Layout specification for pull request and Gate 4 reports.
   131	- [Registry Schema](resources/schemas/check-quality.schema.json): Machine-readable JSON Schema for project registries.
   132	- [Result Schema](resources/schemas/provider-result.schema.json): Machine-readable JSON Schema for provider results.
   133	- [Contract Validator](resources/scripts/validate_quality_contract.py): Standard-library validator script and CLI.
   134	- [Aggregation Engine](resources/scripts/aggregate_quality_results.py): Result aggregation and markdown report engine.
   135	- [Acceptance Suite](resources/scripts/test_quality_provider_acceptance.py): End-to-end multi-provider acceptance test suite.

exec
/bin/zsh -lc 'nl -ba skills/python-quality-check/SKILL.md; nl -ba skills/python-quality-check/resources/schemas/python-quality.schema.json; nl -ba skills/python-quality-check/resources/scripts/validate_python_quality.py' in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	name: python-quality-check
     3	description: Read-only Python quality assurance provider implementing the common quality contract. Executes project-configured capabilities from .agents/quality/python-quality.json, enforces architecture policies via import-linter, and outputs structured results bound to repository SHA.
     4	---
     5	
     6	# Python Quality Assurance Provider
     7	
     8	## Overview
     9	
    10	You are the Python Quality Provider (`d3nexus:python-quality-check`). When invoked by `quality_check`, you execute
    11	read-only quality verification against the active repository according to the requested quality profile.
    12	
    13	You do not guess commands from file layouts. You load capabilities from `.agents/quality/python-quality.json`, execute
    14	the project-declared command arrays, collect evidence, and output a validated result document adhering to the shared
    15	[Provider Result Contract](../quality_check/references/provider-result-contract.md).
    16	
    17	## Workflow
    18	
    19	```mermaid
    20	flowchart TD
    21	    INVOKE["Invoked with normalized request payload"] --> LOAD["Step 1: Load .agents/quality/python-quality.json"]
    22	    LOAD --> VALIDATE["Step 2: Validate capability configuration and profile completeness"]
    23	    VALIDATE --> PLAN["Step 3: Resolve execution plan for requested profile"]
    24	    PLAN --> EXEC["Step 4: Execute read-only commands without shell interpolation"]
    25	    EXEC --> COLLECT["Step 5: Collect check records, coverage, and evidence files"]
    26	    COLLECT --> RESULT["Step 6: Emit validated result document bound to repository SHA"]
    27	```
    28	
    29	### Step 1: Configuration Loading and Validation
    30	
    31	Load the project capability manifest `.agents/quality/python-quality.json` from the repository root:
    32	
    33	```bash
    34	python3 skills/python-quality-check/resources/scripts/validate_python_quality.py .agents/quality/python-quality.json --profile "<profile>"
    35	```
    36	
    37	- If `.agents/quality/python-quality.json` is missing or invalid: emit status `BLOCKED`.
    38	- If the requested profile is not configured: emit status `BLOCKED`.
    39	- For profile `epic`: if the `architecture` (or `boundaries`) capability is missing: emit status `BLOCKED`.
    40	
    41	### Step 2: Read-Only Command Execution
    42	
    43	Execute commands declared in `capabilities` for the target profile:
    44	1. Commands are executed as structured argument arrays (no shell interpolation).
    45	   - An argument beginning with `{skills_dir}` is resolved to the directory containing this plugin's `skills/` folders (the parent of `python-quality-check/`), so manifests can call sibling skill scripts without machine-specific paths (e.g. `["python3", "{skills_dir}/sync-shared-contracts/resources/scripts/sync_contracts.py", "diff-check", "--base-ref", "{base_ref}"]`).
    46	   - An argument containing `{base_ref}` is substituted with the normalized `base_ref` invocation parameter from `quality_check` (falling back to `develop` or the repository default only when `base_ref` was not supplied).
    47	2. All commands run from the resolved repository root.
    48	3. If an executable is missing or cannot be spawned: record check status as `BLOCKED`.
    49	4. If a command runs and reports defects (nonzero exit code):
    50	   - For governance and contract capabilities (`contracts`, `contracts_<domain>`, and `contract_diff`): exit code `0` records `PASS`, exit code `2` (or JSON `"status": "BLOCKED"`) records `BLOCKED`, and any other nonzero exit code (such as `1`) records `FAIL`.
    51	   - For all other capabilities: nonzero exit code records `FAIL`.
    52	5. If a command succeeds (zero exit code): record check status as `PASS`.
    53	
    54	Independent commands (e.g. `format`, `lint`, `type_check`, `test`) may run concurrently.
    55	
    56	### Step 3: Semantic Audits
    57	
    58	Execute specialist audits as configured:
    59	- **Architecture Gate**: Authoritative `lint-imports` or AST-based check evaluates package boundaries, Clean Architecture layer inversion, and forbidden imports.
    60	- **Coverage Gate**: Evaluates `pytest-cov` or project coverage wrapper against configured threshold.
    61	- **Security Policy**: Evaluates `bandit` or `pip-audit` for scheduled and release profiles.
    62	
    63	### Step 4: Result Assembly and Contract Emission
    64	
    65	Assemble the result document matching [provider-result.schema.json](../quality_check/resources/schemas/provider-result.schema.json):
    66	
    67	- `provider_id`: `"python-core"` (or matching invocation identifier)
    68	- `contract_version`: `1`
    69	- `profile`: `<profile>`
    70	- `repository_sha`: Verified commit SHA matching invocation
    71	- `status`: Aggregated provider status (`FAIL` if any check failed, `BLOCKED` if any check blocked, else `PASS`)
    72	- `started_head` and `finished_head`: Git SHA recorded before and after execution
    73	- `checks`, `coverage`, `evidence`, `blockers`, `warnings`
    74	
    75	Return the result document to the orchestrator.
    76	
    77	## References & Resources
    78	
    79	- [Python Capability Contract](references/python-capability-contract.md): Format and rules for `.agents/quality/python-quality.json`.
    80	- [Python Architecture Governance](references/python-architecture-governance.md): Architecture policies via `import-linter` and Clean Architecture boundaries.
    81	- [Python Tool Mapping](references/python-tool-mapping.md): Mapping mobile quality concepts to Python ecosystem equivalents.
    82	- [Capability Schema](resources/schemas/python-quality.schema.json): Machine-readable JSON Schema for Python capability manifests.
    83	- [Capability Validator](resources/scripts/validate_python_quality.py): Script and CLI validator for Python capability files.
    84	- [Valid Fixture](resources/fixtures/valid_python_quality.json): Reference valid capability configuration fixture.
     1	{
     2	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     3	  "title": "Python Quality Capability Configuration Schema",
     4	  "type": "object",
     5	  "additionalProperties": false,
     6	  "required": [
     7	    "schema_version",
     8	    "capabilities",
     9	    "profiles"
    10	  ],
    11	  "properties": {
    12	    "schema_version": {
    13	      "type": "integer",
    14	      "const": 1
    15	    },
    16	    "capabilities": {
    17	      "type": "object",
    18	      "additionalProperties": false,
    19	      "properties": {
    20	        "format": {
    21	          "type": "array",
    22	          "minItems": 1,
    23	          "items": { "type": "string" }
    24	        },
    25	        "lint": {
    26	          "type": "array",
    27	          "minItems": 1,
    28	          "items": { "type": "string" }
    29	        },
    30	        "type_check": {
    31	          "type": "array",
    32	          "minItems": 1,
    33	          "items": { "type": "string" }
    34	        },
    35	        "check": {
    36	          "type": "array",
    37	          "minItems": 1,
    38	          "items": { "type": "string" }
    39	        },
    40	        "test": {
    41	          "type": "array",
    42	          "minItems": 1,
    43	          "items": { "type": "string" }
    44	        },
    45	        "coverage": {
    46	          "type": "object",
    47	          "additionalProperties": false,
    48	          "required": ["command", "threshold"],
    49	          "properties": {
    50	            "command": {
    51	              "type": "array",
    52	              "minItems": 1,
    53	              "items": { "type": "string" }
    54	            },
    55	            "threshold": {
    56	              "type": "number",
    57	              "minimum": 0,
    58	              "maximum": 1
    59	            }
    60	          }
    61	        },
    62	        "architecture": {
    63	          "type": "array",
    64	          "minItems": 1,
    65	          "items": { "type": "string" }
    66	        },
    67	        "boundaries": {
    68	          "type": "array",
    69	          "minItems": 1,
    70	          "items": { "type": "string" }
    71	        },
    72	        "schema": {
    73	          "type": "array",
    74	          "minItems": 1,
    75	          "items": { "type": "string" }
    76	        },
    77	        "acceptance": {
    78	          "type": "array",
    79	          "minItems": 1,
    80	          "items": { "type": "string" }
    81	        },
    82	        "security": {
    83	          "type": "array",
    84	          "minItems": 1,
    85	          "items": { "type": "string" }
    86	        },
    87	        "docs": {
    88	          "type": "array",
    89	          "minItems": 1,
    90	          "items": { "type": "string" }
    91	        },
    92	        "contracts": {
    93	          "type": "array",
    94	          "minItems": 1,
    95	          "items": { "type": "string" }
    96	        },
    97	        "contract_diff": {
    98	          "type": "array",
    99	          "minItems": 1,
   100	          "items": { "type": "string" }
   101	        }
   102	      },
   103	      "patternProperties": {
   104	        "^contracts_[a-z0-9_]+$": {
   105	          "type": "array",
   106	          "minItems": 1,
   107	          "items": { "type": "string" }
   108	        }
   109	      }
   110	    },
   111	    "profiles": {
   112	      "type": "object",
   113	      "additionalProperties": false,
   114	      "required": ["pr", "epic"],
   115	      "properties": {
   116	        "pr": {
   117	          "type": "array",
   118	          "minItems": 1,
   119	          "items": { "type": "string" }
   120	        },
   121	        "epic": {
   122	          "type": "array",
   123	          "minItems": 1,
   124	          "items": { "type": "string" }
   125	        },
   126	        "scheduled": {
   127	          "type": "array",
   128	          "minItems": 1,
   129	          "items": { "type": "string" }
   130	        },
   131	        "release": {
   132	          "type": "array",
   133	          "minItems": 1,
   134	          "items": { "type": "string" }
   135	        }
   136	      }
   137	    }
   138	  }
   139	}
     1	"""Validator for Python quality capability configuration (.agents/quality/python-quality.json)."""
     2	
     3	from __future__ import annotations
     4	
     5	import json
     6	from typing import Any
     7	
     8	
     9	def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    10	    f = {"code": code, "message": message}
    11	    f.update(extra)
    12	    return f
    13	
    14	
    15	def validate_python_config(
    16	    config: dict[str, Any],
    17	    requested_profile: str = "pr",
    18	) -> dict[str, Any]:
    19	    """Validate Python project capability manifest and check readiness for requested profile."""
    20	    findings: list[dict[str, Any]] = []
    21	
    22	    if config.get("schema_version") != 1:
    23	        findings.append(
    24	            _finding("unsupported_version", f"Unsupported schema_version '{config.get('schema_version')}', expected 1")
    25	        )
    26	
    27	    capabilities = config.get("capabilities", {})
    28	    if not isinstance(capabilities, dict):
    29	        findings.append(_finding("missing_capabilities", "Missing or invalid 'capabilities' object"))
    30	        return {"status": "BLOCKED", "findings": findings}
    31	
    32	    for cap_name, cap_val in capabilities.items():
    33	        if cap_name == "coverage":
    34	            if not isinstance(cap_val, dict):
    35	                findings.append(_finding("invalid_coverage_config", "Coverage capability must be an object"))
    36	                continue
    37	            cmd = cap_val.get("command")
    38	            if not isinstance(cmd, list) or not all(isinstance(arg, str) for arg in cmd):
    39	                findings.append(
    40	                    _finding(
    41	                        "invalid_command_format",
    42	                        f"Coverage command for '{cap_name}' must be an array of string arguments",
    43	                        capability=cap_name,
    44	                    )
    45	                )
    46	            elif len(cmd) == 0:
    47	                findings.append(
    48	                    _finding(
    49	                        "command_array_empty",
    50	                        f"Coverage command for '{cap_name}' is empty []",
    51	                        capability=cap_name,
    52	                    )
    53	                )
    54	            threshold = cap_val.get("threshold")
    55	            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1.0:
    56	                findings.append(_finding("invalid_coverage_threshold", "Coverage threshold must be between 0.0 and 1.0"))
    57	        else:
    58	            if not isinstance(cap_val, list) or not all(isinstance(arg, str) for arg in cap_val):
    59	                findings.append(
    60	                    _finding(
    61	                        "invalid_command_format",
    62	                        f"Capability command for '{cap_name}' must be an array of string arguments, not a string or shell command",
    63	                        capability=cap_name,
    64	                    )
    65	                )
    66	            elif len(cap_val) == 0:
    67	                findings.append(
    68	                    _finding(
    69	                        "command_array_empty",
    70	                        f"Capability command for '{cap_name}' is empty []",
    71	                        capability=cap_name,
    72	                    )
    73	                )
    74	
    75	    profiles = config.get("profiles", {})
    76	    if not isinstance(profiles, dict):
    77	        findings.append(_finding("missing_profiles", "Missing or invalid 'profiles' object"))
    78	        return {"status": "BLOCKED", "findings": findings}
    79	
    80	    profile_caps = profiles.get(requested_profile)
    81	    if profile_caps is None:
    82	        findings.append(
    83	            _finding(
    84	                "profile_not_configured",
    85	                f"Requested profile '{requested_profile}' is not configured in profiles",
    86	            )
    87	        )
    88	    elif not isinstance(profile_caps, list):
    89	        findings.append(_finding("invalid_profile_format", f"Profile '{requested_profile}' must be an array of capability names"))
    90	    else:
    91	        for cap in profile_caps:
    92	            if cap not in capabilities:
    93	                findings.append(
    94	                    _finding(
    95	                        "missing_capability_definition",
    96	                        f"Profile '{requested_profile}' requires capability '{cap}', which is not defined in capabilities",
    97	                        capability=cap,
    98	                    )
    99	                )
   100	
   101	        if requested_profile == "epic" and "architecture" not in capabilities and "boundaries" not in capabilities:
   102	            findings.append(
   103	                _finding(
   104	                    "missing_architecture_authority",
   105	                    "Epic profile requires an authoritative architecture or boundaries command in capabilities",
   106	                    capability="architecture",
   107	                )
   108	            )
   109	
   110	    return {
   111	        "status": "BLOCKED" if findings else "PASS",
   112	        "findings": sorted(findings, key=lambda f: (f.get("code", ""), f.get("capability", ""))),
   113	    }
   114	
   115	
   116	def main() -> int:
   117	    import argparse
   118	    from pathlib import Path
   119	
   120	    parser = argparse.ArgumentParser(description="Validate Python quality capability manifest.")
   121	    parser.add_argument("config_file", help="Path to .agents/quality/python-quality.json")
   122	    parser.add_argument("--profile", default="pr", help="Requested profile (pr, epic, scheduled, release)")
   123	
   124	    args = parser.parse_args()
   125	    data = json.loads(Path(args.config_file).read_text())
   126	    res = validate_python_config(data, args.profile)
   127	    print(json.dumps(res, indent=2))
   128	    return 0 if res["status"] == "PASS" else 1
   129	
   130	
   131	if __name__ == "__main__":
   132	    import sys
   133	
   134	    sys.exit(main())

exec
/bin/zsh -lc "rg -n 'Tier|Integration|check_bdd|sync|Phase 4|Gate 4|provider|smoke' skills/dev-implementation/SKILL.md skills/dev-designer/SKILL.md skills/dev-implementation/resources/scripts/check_bdd_traceability.py; rg --files skills/dev-implementation/resources/scripts skills/setup_quality_check .agents tests | head -100; command -v git python3 node npm npx tsc ruff mypy pytest; ls -ld shared-contracts /opt/homebrew/bin/git /usr/local/bin/git" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 exited 1 in 0ms:
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:5:  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
skills/dev-implementation/resources/scripts/check_bdd_traceability.py:6:  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
skills/dev-designer/SKILL.md:3:description: Use when analyzing high-level requirements to design a complete software Epic across Web Applications, Flutter, Android Native, iOS Native, Python, or Rust projects, including High-Level Design (HLD), Mermaid diagrams, Integration Test Plans, and Kanban task breakdowns with BDD & TDD specifications.
skills/dev-designer/SKILL.md:9:This skill transforms high-level product or technical requirements into a structured, developer-ready Epic for **Web Applications**, **Flutter**, **Android Native**, **iOS Native**, **Python**, and **Rust Core / Polyglot** projects. It creates a centralized High-Level Design (HLD) document, formalizes an **Integration Test Plan** covering analyzed use cases and boundary edge cases, and breaks the work down into granular Kanban tasks enforcing Behavior-Driven Development (BDD), Test-Driven Development (TDD), and strict Definition of Done (DoD), fully aligned with `dev-implementation`'s Tri-Persona workflow (QA Red Team + TDD Master + System Integration Engineer).
skills/dev-designer/SKILL.md:87:   - **Integration Test Plan & Boundary Matrix**: Map every Use Case and Sequence Diagram interaction into an explicit Integration Test Plan. Detail the end-to-end integration boundaries, mock/live services, data stores, and multi-component seams. For Web/UI applications, explicitly specify the **Visual & Browser Verification Matrix** (target viewports, URL routes/query parameters, interactive states, audio/video playback, and DOM verification).
skills/dev-designer/SKILL.md:88:   - **Integration Test Roots**: The Integration Test Plan MUST contain the line `Integration test roots: <dir>, <dir>` naming every directory that holds integration tests. Defaults: `tests/e2e/` (Web), `integration_test/` (Flutter), `app/src/test/` and `shell/src/test/` (Android), `App/Tests/` and `Shell/Tests/` (iOS), `tests/integration/` and `tests/e2e/` (Python), `tests/` (Rust). `check_bdd_traceability.py` scans exactly these directories.
skills/dev-designer/SKILL.md:89:   - **Protected Paths & Integration Results**: Beside `Integration test roots:`, the Integration Test Plan MUST carry these lines, which the recorder, the done gate and Gate 4 read:
skills/dev-designer/SKILL.md:92:     Integration results: uv run pytest tests/integration tests/e2e --junitxml=build/test-results/py.xml -> build/test-results/py.xml
skills/dev-designer/SKILL.md:94:     `Protected paths:` lists explicit paths and globs; the three shown are the minimum, and a tracked program that a Verification row runs is protected implicitly. Write one `Integration results:` line per platform, at least one: the command Gate 4 runs, then ` -> `, then the report it writes.
skills/dev-designer/SKILL.md:100:     4. **Async / Race Conditions**: Rapid consecutive user interactions (debouncing, stream transformers, cancellation).
skills/dev-designer/SKILL.md:103:   In multi-repo ecosystems (e.g. `D3Nexus` hub with `lyrics-sync` and `nexus` satellite repos connected via `shared-contracts/` symlinks), waiting until local implementation finishes to update inter-service contracts creates bottlenecks. When deriving tasks from an approved spec, **read `## Shared Contract Warnings`** to discover all human-approved contract decisions, pending drifts, and waivers planned during Stage 1.
skills/dev-designer/SKILL.md:107:     - **Satellite Mode (`shared-contracts/` is a symbolic link)**: The current workspace is a Satellite Consumer or Producer (e.g. `lyrics-sync`, `nexus`). The Lead acts under the **Satellite Consumer Architect Persona**, responsible for specifying upstream contract requirements and ensuring internal adapters gracefully tolerate contract evolution without violating Git symlink boundaries.
skills/dev-designer/SKILL.md:112:   - In addition to embedding scenarios in the Epic Overview, generate a synchronized pair:
skills/dev-designer/SKILL.md:117:   - **Scenario IDs**: Every `Scenario:` or `Scenario Outline:` line starts with a unique identifier in brackets, before any tier tag: `Scenario: [PY-HP-01] [Tier C - Integration] ...`. Shape: uppercase segments joined by `-`, ending in digits; convention `<EPIC>-<DIM>-<NN>` with `HP`, `EC`, `ST`, `AR`, `FR` for the five dimensions. The `.vi.md` file carries exactly the same identifiers, untranslated. The first segment is this epic's prefix and MUST NOT be used by any other epic in the project, because integration test roots hold every epic's tests; list the prefixes already taken with `grep -ho '\[[A-Z][A-Z0-9]*-' .devtool/epic/*/bdd_scenarios.en.md | sort -u`.
skills/dev-designer/SKILL.md:126:`.vi.md` variant is a translation for local team communication and MUST be kept in sync whenever
skills/dev-designer/SKILL.md:143:Beside each proposed task, list the epic scenario identifiers it will cover (its future `Covers:` line, see Tier C — BDD Automation below), so the user approves the scenario-to-task mapping together with the split.
skills/dev-designer/SKILL.md:151:  - **Parallel Handoff Summary**: Once `task_01` is drafted and confirmed at Gate 2, output a concise handoff prompt so the developer can immediately trigger AI Agents in satellite repos (e.g. `lyrics-sync`, `nexus`) to work in parallel while local implementation proceeds. The handoff summary MUST include:
skills/dev-designer/SKILL.md:156:- **Satellite Mode (`shared-contracts/` is a symbolic link, e.g. `lyrics-sync`)**:
skills/dev-designer/SKILL.md:166:      5. Run `python3 skills/sync-shared-contracts/resources/scripts/sync_contracts.py ack --domain <domain> --snapshot <new_snapshot_id>` in the Satellite workspace to immediately record the new baseline in `.agents/contract_sync.json`, seamlessly unblocking Stage 3 `dev-implementation` without cross-repo stalls.
skills/dev-designer/SKILL.md:178:Break the Epic down into granular implementation tasks. **Crucially, each task must be structured around Behavior-Driven Development (BDD), Test-Driven Development (TDD), and Integration Flow Testing** to feed directly into the Tri-Persona (QA Red Team + TDD Master + System Integration Engineer) execution workflow in `dev-implementation`. Wherever the task produces testable behavior, generate Markdown task files located at `.devtool/features/task_<number>_<name>.md` (and mirrored in `.devtool/epic/<epic_name>/task_<number>_<name>.md` as permanent epic outputs).
skills/dev-designer/SKILL.md:182:- **In-Flight**: As tasks complete during `dev-implementation`, `sync_task_status.py` moves them from `.devtool/features/` into `.devtool/features/done/`.
skills/dev-designer/SKILL.md:183:- **Epic Completion Archival**: When all tasks of an epic finish and the epic status transitions to `Done` (`sync_task_status.py epic <epic_dir> Done`), all completed tasks and draft superpowers documents are archived permanently into `.devtool/epic/<epic_dir>/`. Relative markdown links are rewritten to point locally, and `.devtool/features/done/` is left clean with zero lingering task files.
skills/dev-designer/SKILL.md:186:When `shared-contracts/` is affected, `task_01` is reserved strictly for contract synchronization before local feature tasks begin, structured per the active mode and persona:
skills/dev-designer/SKILL.md:197:- **Persona**: **TDD Master (Dev Persona — Tier A)** + **QA Red Team (QA Persona)**.
skills/dev-designer/SKILL.md:204:#### Mandatory 3-Tier Testing Standard in Task Breakdown
skills/dev-designer/SKILL.md:208:- **Tier A (Unit / Package Tests)**: Tasks covering module/feature logic, BLoCs, UseCases, Repositories, Parsers with isolated unit tests (`fvm flutter test` or `melos test` using `bloc_test`, Mocktail). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:209:- **Tier B (Tooling & Governance Tests)**: Tasks that touch feature packages or public APIs MUST verify module boundaries (`./scripts/check_module_boundaries.sh`), license headers (`./scripts/check_license_header.sh`), code formatting (`melos format`), and static analysis (`melos analyze`).
skills/dev-designer/SKILL.md:210:- **Tier C (Acceptance & App Tests)**: Every Epic MUST include an explicit final integration task (e.g. `Task N: Host App Integration & Acceptance Tests`) verifying the Host composition root (`lib/` composition, `AppRoutes`, `AppEventBus`), full end-to-end user navigation flows, and running the automated acceptance/integration harness (`fvm flutter test integration_test` or `./scripts/testWithCoverage.sh`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:213:- **Tier A (Unit / Package Tests)**: Tasks covering module/feature logic, MVI ViewModels, UseCases, Repositories, Parsers with isolated unit tests (`./gradlew testDebugUnitTest` using JUnit, MockK, Turbine). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:214:- **Tier B (Tooling & Governance Tests)**: Tasks that touch architectural rules, convention plugins, or public API signatures MUST include verification with Konsist rules K1–K10 (`./gradlew :konsist-test:test`) and BCV public ABI checks (`./gradlew apiCheck`), Detekt, and Spotless (`./gradlew check`).
skills/dev-designer/SKILL.md:215:- **Tier C (Acceptance & App Tests)**: Every Epic MUST include an explicit final integration task verifying Host composition root (`:app` + `:shell`), full end-to-end user navigation flows, DFM on-demand splits, and running the automated acceptance harness (`./scripts/acceptance_check.sh`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:218:- **Tier A (Unit / Package Tests)**: Tasks covering module/feature logic, MVI ViewModels, UseCases, Repositories, Parsers with isolated unit tests (`swift test --package-path <PackagePath>` using Swift Testing `@Test` or XCTest). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:219:- **Tier B (Tooling & Governance Tests)**: Tasks that touch feature packages or public API contracts MUST verify module boundaries (`bash scripts/check_module_boundaries.sh`), AST architecture governance rules K1–K10 (`swift test --package-path ArchTests`), static analysis (`swiftlint lint --strict --config quality/.swiftlint.yml`), and code formatting (`swiftformat --config quality/.swiftformat . --lint`).
skills/dev-designer/SKILL.md:220:- **Tier C (Acceptance & App Tests)**: Every Epic MUST include an explicit final integration task verifying Host composition root (`App/` + `Shell/`), `AppRoutes`, RouteProvider registration, end-to-end user navigation flows, and running the automated acceptance harness (`tuist generate --no-open && xcodebuild test ...`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:223:- **Tier A (Unit & State Tests)**: Tasks covering component logic, domain utilities, reactive stores, state machines, parsers, and reducers with isolated unit tests (`node --test`, Vitest, Jest). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:224:- **Tier B (Tooling, Types & Governance Tests)**: Tasks touching components, pages, or shared modules MUST verify type soundness (`tsc --noEmit`), framework diagnostics (`astro check` or framework linter), code style/formatting (`prettier --check` / `eslint`), and module boundaries.
skills/dev-designer/SKILL.md:225:- **Tier C (Acceptance, E2E & Live Browser Verification)**: Every Web Epic MUST include an explicit final integration task (e.g. `Task N: Integration & Live Browser Verification`) verifying application composition roots, router navigation flows, running the automated integration harness (`tests/e2e/*.test.ts`, Playwright, Cypress) **AND executing Live Web Browser Verification**. The agent MUST launch the local dev/preview server, navigate using `browser_subagent`, record a video session (`.webp`), capture screenshot artifacts, and assert real DOM states, user interactions, audio/video playback, and visual layout against analyzed use cases and edge cases. Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:228:- **Tier A (Unit Tests)**: Tasks covering module/domain logic, services, models, and parsers with isolated unit tests (`pytest tests/unit/` using `pytest-mock`, `unittest.mock`). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:229:- **Tier B (Tooling & Governance Tests)**: Tasks touching modules or public APIs MUST verify code formatting and linting (`ruff check .`, `ruff format --check .`), strict type checking (`mypy --strict src`), and architectural layer boundaries (`lint-imports` or `import-linter` via `.importlinter`).
skills/dev-designer/SKILL.md:230:- **Tier C (Acceptance & Integration Tests)**: Every Epic MUST include an explicit final integration task verifying service composition roots, API integrations, database workflows, and running automated integration/acceptance tests (`pytest tests/integration/` and `pytest tests/e2e/`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:233:- **Tier A (Unit Tests)**: Tasks covering module/domain logic, services, models, and parsers with isolated unit tests (`pytest tests/unit/` using `pytest-mock`, `unittest.mock`). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:234:- **Tier B (Tooling & Governance Tests)**: Tasks touching modules or public APIs MUST verify code formatting and linting (`ruff check .`, `ruff format --check .`), strict type checking (`mypy --strict src`), and architectural layer boundaries (`lint-imports` or `import-linter` via `.importlinter`).
skills/dev-designer/SKILL.md:235:- **Tier C (Acceptance & Integration Tests)**: Every Epic MUST include an explicit final integration task verifying service composition roots, API integrations, database workflows, and running automated integration/acceptance tests (`pytest tests/integration/` and `pytest tests/e2e/`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:238:- **Tier A (Unit / Crate Tests)**: Tasks covering core domain models, business logic, parsers, algorithms, and state machines with isolated unit tests (`cargo test --lib`). Executed by the **TDD Master (Dev Persona)**.
skills/dev-designer/SKILL.md:239:- **Tier B (Tooling & Governance Tests)**: Tasks touching shared crates or public APIs MUST verify formatting (`just fmt` or `cargo fmt --check`), clippy warnings denied (`just lint` or `cargo clippy -D warnings`), dependency licensing/security (`cargo deny check`), and architecture boundaries (`cargo run -p xtask -- check-boundaries`).
skills/dev-designer/SKILL.md:240:- **Tier C (Acceptance & App Tests)**: Every Epic MUST include an explicit final integration task verifying composition roots, WASM bindings (`just wasm-test`), FFI exports, and running end-to-end acceptance tests (`cargo test --test '*'` or `just acceptance`). Executed by the **System Integration Engineer (Integration Persona)**.
skills/dev-designer/SKILL.md:242:##### 🔗 Tier C — BDD Automation (All Platforms)
skills/dev-designer/SKILL.md:244:- The test carries the scenario identifier in its name, description or tag (`test_py_hp_01_...`, `func test_PY_HP_01_...()`, `testWidgets('[PY-HP-01] ...')`, ``@Test fun `PY-HP-01 ...`()``) and lives under one of the HLD's `Integration test roots`.
skills/dev-designer/SKILL.md:245:- Each identifier is assigned to exactly one task through that task's `Covers:` line; two tasks never share an identifier. The final Tier C task takes every identifier no earlier task covers.
skills/dev-designer/SKILL.md:246:- **Final Task Governance & Immutability (`Allowed files`)**: The final task of every epic (the Tier C integration/acceptance task running immediately before Phase 4 / Gate 4) MUST include `.agents/contract_sync.json` in its `Allowed files` (for recording `sync_contracts.py ack` watermark acknowledgements on Satellites) and, when path-scoped waivers are planned, `.agents/contract_map.json` in `Allowed files`. Updating these manifests inside the final task ensures that the repository commit SHA certified by Gate 4 remains completely immutable and reproducible.
skills/dev-designer/SKILL.md:251:        HLD["High-Level Design<br/>(Use Cases, Sequence & Integration Plan)"]
skills/dev-designer/SKILL.md:261:        subgraph TIER_A["Tier A: TDD Master (Dev Persona)"]
skills/dev-designer/SKILL.md:262:            UNIT_SCENARIOS["[Tier A - Unit] Scenarios"]
skills/dev-designer/SKILL.md:269:        subgraph TIER_C["Tier C: System Integration & E2E Engineer"]
skills/dev-designer/SKILL.md:270:            FLOW_SCENARIOS["[Tier C - Integration] Scenarios"]
skills/dev-designer/SKILL.md:271:            FLOW_TESTS["Host Integration Flow & E2E Tests<br/>(integration_test, *FlowTest.kt, tests/e2e)"]
skills/dev-designer/SKILL.md:278:    subgraph TIER_B["Tier B: Automated Governance Gates"]
skills/dev-designer/SKILL.md:303:> When executing via `dispatching-parallel-agents`, the Lead Agent may dispatch **Subagent 1 (Dev Persona — Tier A)** and **Subagent 2 (SDET Persona — Tier C)** concurrently, provided these 3 inviolable rules are satisfied:
skills/dev-designer/SKILL.md:307:>    - Neither agent is permitted to rename, alter types, or mutate public contract signatures during parallel execution without a synchronized pause.
skills/dev-designer/SKILL.md:316:>    - Once both subagents report completion, the Lead Agent performs the **Sync Checkpoint**: merges the branches, validates that the integration tests turn **GREEN**, and runs the Tier C acceptance check.
skills/dev-designer/SKILL.md:361:   Directly under that heading, write the line `Covers: <ID>, <ID>` naming the epic scenario identifiers from `bdd_scenarios.en.md` whose integration tests this task writes. Omit the line only when the task covers no epic scenario, for example a Tier B tooling task.
skills/dev-designer/SKILL.md:374:   - **Async / Race Conditions**: Rapid consecutive user interactions (debouncing, stream transformers, cancellation).
skills/dev-designer/SKILL.md:377:   **Tier Categorization Tagging & 100% Traceability Mandate**:
skills/dev-designer/SKILL.md:378:   - `[Tier A - Unit]`: Scenarios covering class/function level logic, BLoCs/ViewModels, UseCases, Repositories, Parsers, and Guards. Must be covered 100% by unit tests.
skills/dev-designer/SKILL.md:379:   - `[Tier C - Integration]`: Scenarios covering end-to-end user navigation, Host App lifecycle, Tab switching, Auth Gating & Replay, and multi-component seams (including media playback synchronization, live database states, and web route transitions). Must be covered 100% by integration tests.
skills/dev-designer/SKILL.md:380:   - **Zero Uncovered Scenarios Rule**: Every authored BDD scenario across all 5 dimensions MUST map to at least one automated test case. Unit tests with mocks do NOT substitute for Tier C integration tests.
skills/dev-designer/SKILL.md:408:   - For pytest specifically, the command must use an exact node ID such as `path/test_file.py::test_name`, expect exit 1, and require positive collected-test failure output. Generic `-k` expressions without an exact node ID are rejected by `check_task_contract.py`. Other platforms use the repository's registered runner/provider command without imposing Python syntax on non-Python platforms.
skills/dev-designer/SKILL.md:410:   - The Tier A/B/C testing standard above decides which rows a task needs; the rows are the proof, not a checklist.
skills/dev-designer/SKILL.md:426:10. **Definition of Done (DoD)**: Acceptance criteria (100% BDD scenario coverage across Tier A unit and Tier C integration tests with zero uncovered scenarios, passes Tier A/B/C verification, clean git status; for Web/UI deliverables: automated integration tests pass AND live browser verification artifacts are captured via `browser_subagent`). Every bullet ends with a parenthesised reference: the Verification rows that prove it, such as `(V2, V4)`, or `(Gate 5)` for an item only the developer can judge at Kanban review. The Gate 4 report lists `(Gate 5)` items; no script marks one met.
skills/dev-designer/SKILL.md:434:python3 "$SKILL_DIR"/../dev-implementation/resources/scripts/check_bdd_traceability.py plan \
skills/dev-designer/SKILL.md:466:When new requirements arrive for an epic already in progress, append new task files continuing the sequence, and append links to the Epic Overview's Kanban Tasks Breakdown section (in both `.en.md` and `.vi.md`). Update the Mermaid diagrams if architecture changes. If the epic's `bdd_scenarios.en.md` predates scenario identifiers, retrofit the whole epic first — identifiers, `Covers:` lines and the `Integration test roots:` line, as dev-implementation Phase 1 step 3 describes — before running the Step 3 `plan` check.
skills/dev-designer/SKILL.md:474:- Omitting the final Tier C (Acceptance & App Tests) task from the Epic breakdown.
skills/dev-designer/SKILL.md:475:- Omitting Tier C integration tests that exercise analyzed use cases, edge cases, and boundary conditions.
skills/dev-designer/SKILL.md:484:- Committing the epic before `check_bdd_traceability.py plan` and `check_task_contract.py --design` both exit 0.
skills/dev-implementation/SKILL.md:46:   - `.devtool/epic/<epic_dir>/<epic_dir>.en.md` (the canonical HLD — never `.vi.md` for decisions, that's a synced translation).
skills/dev-implementation/SKILL.md:47:   - `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` (the canonical behavioral contract across the 5 dimensions, if present; `.vi.md` is its synchronized translation).
skills/dev-implementation/SKILL.md:51:   - Restore architectural context and synchronize window title: `python3 scripts/resume_context.py --role programmer --epic <epic_slug>`.
skills/dev-implementation/SKILL.md:62:**Symlink & Multi-Repo Boundary Invariant**: In Satellite repositories where `shared-contracts/` is a symbolic link (e.g. `lyrics-sync` or `nexus` linking to `D3Nexus`), the implementer MUST treat `shared-contracts/` as strictly read-only for git operations. Never attempt to stage files through the symlink (`git add shared-contracts/...`), which triggers `fatal: pathspec is beyond a symbolic link`. If an upstream contract modification is needed, stop and report `BLOCKED` with an Upstream Contract Handoff Summary rather than attempting cross-repo edits.
skills/dev-implementation/SKILL.md:93:`git ls-remote` asks each remote directly, so an epic branch pushed from another clone shows before any fetch; if a remote cannot be reached, fall back to `git branch -r --list '*/epic/<epic_slug>'`. The last command reads the epic's task mirrors (`sync_task_status.py` keeps them in step with `.devtool/features/` and `.devtool/features/done/`); its flattened order prints each task's status as `[priority, status]`. Evaluate the rows top-down — first match wins — and announce it: "Entry point: row N — <state>."
skills/dev-implementation/SKILL.md:102:| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate worktree if missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap (Phase 1 step 5), run Resume Procedure preflight (step 2), then Phase 4 in full; its PASS presents Review Choice |
skills/dev-implementation/SKILL.md:113:5. If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
skills/dev-implementation/SKILL.md:129:   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
skills/dev-implementation/SKILL.md:133:   If needed, add bracketed identifiers to `bdd_scenarios.*.md`, `Covers:` lines to task files, and `Integration test roots:` to HLD. Commit as `[EPIC_NAME] Add BDD scenario identifiers`.
skills/dev-implementation/SKILL.md:147:   python3 "$INTEGRATE" sync-base --base develop
skills/dev-implementation/SKILL.md:150:   If `sync-base` exits 3 (diverged or dirty file), stop and ask.
skills/dev-implementation/SKILL.md:151:   If overview Status begins with `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
skills/dev-implementation/SKILL.md:152:5. Bootstrap worktree using platform tooling (`bootstrap_worktree.sh`, Gradle sync, Tuist, npm/pnpm, uv sync, cargo check).
skills/dev-implementation/SKILL.md:171:   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> in-progress
skills/dev-implementation/SKILL.md:177:   When dispatching implementer subagent, operate across the 3-Tier Testing Standard:
skills/dev-implementation/SKILL.md:178:   1. **Expert QA (Red Team Persona)**: Authors BDD Scenarios in complete isolation from coding, purely from HLD and `bdd_scenarios.en.md`, applying 5 dimensions: Happy Paths, Edge Cases & Boundaries, State Transitions, Async / Race Conditions, Failures & Resilience. Categorizes scenarios into `[Tier A - Unit]` vs `[Tier C - Integration]`. In Satellite Mode, authors verification scenarios validating that local deserializers parse both legacy and updated upstream payloads safely.
skills/dev-implementation/SKILL.md:179:   2. **Principal Engineer (TDD Master Persona — Tier A)**: Implements unit logic, state emissions, and hermetic tests using platform tools (Dart/Flutter, Kotlin/Compose, Swift/SwiftUI, TypeScript/Web, Python/pytest, Rust/cargo). Enforces RED failing test first -> minimal GREEN code -> REFACTOR formatting, linter, strict types. In Satellite Mode, adapts consumer models, DTOs, and adapters within satellite-internal files without staging symlinked paths.
skills/dev-implementation/SKILL.md:180:   3. **System Integration & E2E Engineer (Tier C Persona)**: Implements host integration flow tests (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) connecting DI, navigation, and persistence contracts.
skills/dev-implementation/SKILL.md:185:   > 2. **Tier Separation**: `[Tier A - Unit]` covered 100% by unit tests; `[Tier C - Integration]` covered 100% by host integration flow tests. Mocks do NOT substitute for Tier C integration tests.
skills/dev-implementation/SKILL.md:186:   > 3. **BDD Automation (Tier C, all platforms)**: For every identifier on task's `Covers:` line, author at least one integration test under HLD's `Integration test roots`, carrying the identifier in test name, description, or tag.
skills/dev-implementation/SKILL.md:193:   >    Never edit `.devtool/epic/<epic_dir>/evidence/<task_id>.json` by hand. `sync_task_status.py task <id> done` refuses unless evidence matches tree and table.
skills/dev-implementation/SKILL.md:196:   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
skills/dev-implementation/SKILL.md:198:   >      --roots <Integration test roots from the HLD> \
skills/dev-implementation/SKILL.md:203:2. When implementer reports `DONE`, synchronize review status:
skills/dev-implementation/SKILL.md:205:   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> review
skills/dev-implementation/SKILL.md:208:4. When both reviews pass, `run_task_checks.py status <task mirror>` prints `done gate: PASS` and `check_bdd_traceability.py tests --ids` exits 0, update status to `done`:
skills/dev-implementation/SKILL.md:210:   python3 skills/dev-implementation/resources/scripts/sync_task_status.py task <task_id> done
skills/dev-implementation/SKILL.md:221:   Log programmer activity and update state (which synchronizes `window.title` to the latest completed task):
skills/dev-implementation/SKILL.md:254:Once every task is `done`, a fix is never made by reopening a task. Make it as its own commit on the epic branch, titled `[EPIC_NAME] Fix <what>`. Do not move a done task back, and do not re-record its evidence. `audit_epic.py` lists these commits under "Commits outside tasks". After fixes, run Phase 4 again in full on the new SHA.
skills/dev-implementation/SKILL.md:256:### Phase 4 — End of Epic Verification
skills/dev-implementation/SKILL.md:264:   Exit 1 means unresolved finding: record decision or make Fix commit, then restart Phase 4 in full.
skills/dev-implementation/SKILL.md:265:2. **Gate 4 audit**:
skills/dev-implementation/SKILL.md:269:   Must exit 0. Keep output for Phase 4.1.
skills/dev-implementation/SKILL.md:270:3. **HLD Integration results commands.** Run every `Integration results:` line of HLD Integration Test Plan.
skills/dev-implementation/SKILL.md:271:4. **Result-based traceability**: run `check_bdd_traceability.py tests --results` over those reports:
skills/dev-implementation/SKILL.md:273:   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
skills/dev-implementation/SKILL.md:275:     --roots <Integration test roots from the HLD> \
skills/dev-implementation/SKILL.md:276:     --results <reports written by Integration results commands>
skills/dev-implementation/SKILL.md:284:   - Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.
skills/dev-implementation/SKILL.md:286:#### Semantic Test Integrity Governance (Gate 4 Rules)
skills/dev-implementation/SKILL.md:288:Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
skills/dev-implementation/SKILL.md:292:*(Note: These are Gate 4 semantic integrity requirements evaluated by specialist providers and audits; no universal cross-language mechanical coverage claim is made.)*
skills/dev-implementation/SKILL.md:294:### Review Choice — after every Gate 4 PASS
skills/dev-implementation/SKILL.md:297:You MUST NOT skip or auto-decide Review Choice after Gate 4 passes.
skills/dev-implementation/SKILL.md:299:Cross-model review and Local model review must return to Phase 4 in full; only the next Gate 4 PASS may present Review Choice again.
skills/dev-implementation/SKILL.md:302:The loop invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**.
skills/dev-implementation/SKILL.md:311:On Gate 4 PASS, run `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 4.1: Review Choice"` (which synchronizes `window.title` to Review Choice) and emit the prompt via `python3 scripts/resume_context.py --emit-prompt cross-review --epic <epic_slug>`.
skills/dev-implementation/SKILL.md:314:> Gate 4 is 🟢 LGTM for `<candidate_sha>`. How do you want to proceed?
skills/dev-implementation/SKILL.md:320:Option 1 goes to Phase 4.1 / Gate 5. Option 2 invokes `d3nexus:cross-model-review` in epic worktree with clean tree:
skills/dev-implementation/SKILL.md:325:Commit `review_results.md` after every round (`[EPIC_NAME] Record cross-model review round N`). After every round of option 2 or 3, run `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>`, fill it as [review-triage.md](references/review-triage.md) says, present it, and wait for the developer's decisions before any Fix commit or Decision cell. Then make the Fix commits, record the decisions, commit, and rerun Phase 4 / Gate 4 in full.
skills/dev-implementation/SKILL.md:334:### Phase 4.1 — Developer Kanban Review Checkpoint (🛑 MANDATORY STOP & WAIT — Gate 5)
skills/dev-implementation/SKILL.md:351:   python3 skills/dev-implementation/resources/scripts/sync_task_status.py archive-done
skills/dev-implementation/SKILL.md:355:## Integration
rg: tests: No such file or directory (os error 2)
.agents/rules/window_title_sync.md
skills/setup_quality_check/SKILL.md
.agents/plugins/marketplace.json
skills/dev-implementation/resources/scripts/slug_utils.py
skills/dev-implementation/resources/scripts/test_sync_task_status.py
skills/dev-implementation/resources/scripts/test_local_review.py
skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py
skills/dev-implementation/resources/scripts/compute_execution_order.py
skills/dev-implementation/resources/scripts/check_task_contract.py
skills/dev-implementation/resources/scripts/local_review.py
skills/dev-implementation/resources/scripts/test_bootstrap_worktree_validation.sh
skills/dev-implementation/resources/scripts/test_slug_utils.py
skills/dev-implementation/resources/scripts/sync_task_status.py
skills/dev-implementation/resources/scripts/test_run_task_checks.py
skills/dev-implementation/resources/scripts/test_run_external_review.py
skills/dev-implementation/resources/scripts/test_check_task_contract.py
skills/dev-implementation/resources/scripts/run_external_review.py
skills/dev-implementation/resources/scripts/test_result_reports.py
skills/dev-implementation/resources/scripts/task_contract.py
skills/dev-implementation/resources/scripts/test_check_epic_readiness.py
skills/dev-implementation/resources/scripts/test_audit_epic.py
skills/dev-implementation/resources/scripts/test_compute_execution_order.py
skills/dev-implementation/resources/scripts/bootstrap_worktree.sh
skills/dev-implementation/resources/scripts/run_task_checks.py
skills/dev-implementation/resources/scripts/detect_project_type.sh
skills/dev-implementation/resources/scripts/check_bdd_traceability.py
skills/dev-implementation/resources/scripts/audit_epic.py
skills/dev-implementation/resources/scripts/result_reports.py
skills/dev-implementation/resources/scripts/check_epic_readiness.py
skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py
skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py
/usr/bin/git
/opt/homebrew/bin/python3
/opt/homebrew/bin/node
/opt/homebrew/bin/npm
/opt/homebrew/bin/npx
/Users/danhdueexoictif/.local/bin/ruff
/Users/danhdueexoictif/.local/bin/mypy
ls: /opt/homebrew/bin/git: No such file or directory
ls: /usr/local/bin/git: No such file or directory
ls: shared-contracts: No such file or directory

exec
/bin/zsh -lc "nl -ba skills/quality_check/resources/schemas/provider-result.schema.json; nl -ba skills/quality_check/resources/scripts/validate_quality_contract.py | sed -n '1,280p'; nl -ba skills/quality_check/resources/scripts/validate_quality_contract.py | sed -n '280,580p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py; nl -ba skills/dev-implementation/resources/scripts/result_reports.py; rg -n 'bdd|trace|mock|done|evidence' skills/dev-implementation/resources/scripts/sync_task_status.py skills/dev-implementation/resources/scripts/run_task_checks.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	{
     2	  "$schema": "https://json-schema.org/draft/2020-12/schema",
     3	  "title": "Provider Result Schema",
     4	  "type": "object",
     5	  "additionalProperties": false,
     6	  "required": [
     7	    "provider_id",
     8	    "contract_version",
     9	    "profile",
    10	    "repository_sha",
    11	    "status",
    12	    "checks",
    13	    "coverage",
    14	    "evidence",
    15	    "started_head",
    16	    "finished_head",
    17	    "duration",
    18	    "blockers",
    19	    "warnings"
    20	  ],
    21	  "properties": {
    22	    "schema_version": {
    23	      "type": "integer",
    24	      "const": 1
    25	    },
    26	    "contract_version": {
    27	      "type": "integer",
    28	      "const": 1
    29	    },
    30	    "provider_id": {
    31	      "type": "string",
    32	      "pattern": "^[a-z0-9_-]+$"
    33	    },
    34	    "profile": {
    35	      "type": "string",
    36	      "enum": [
    37	        "pr",
    38	        "epic",
    39	        "scheduled",
    40	        "release"
    41	      ]
    42	    },
    43	    "repository_sha": {
    44	      "type": "string",
    45	      "pattern": "^[0-9a-f]{40}$"
    46	    },
    47	    "status": {
    48	      "type": "string",
    49	      "enum": [
    50	        "PASS",
    51	        "FAIL",
    52	        "BLOCKED",
    53	        "NOT_APPLICABLE"
    54	      ]
    55	    },
    56	    "started_head": {
    57	      "type": "string",
    58	      "pattern": "^[0-9a-f]{40}$"
    59	    },
    60	    "finished_head": {
    61	      "type": "string",
    62	      "pattern": "^[0-9a-f]{40}$"
    63	    },
    64	    "duration": {
    65	      "type": "number",
    66	      "minimum": 0
    67	    },
    68	    "checks": {
    69	      "type": "array",
    70	      "items": {
    71	        "type": "object",
    72	        "additionalProperties": false,
    73	        "required": [
    74	          "id",
    75	          "category",
    76	          "status",
    77	          "source",
    78	          "duration",
    79	          "summary",
    80	          "evidence_refs"
    81	        ],
    82	        "properties": {
    83	          "id": {
    84	            "type": "string"
    85	          },
    86	          "category": {
    87	            "type": "string"
    88	          },
    89	          "status": {
    90	            "type": "string",
    91	            "enum": [
    92	              "PASS",
    93	              "FAIL",
    94	              "BLOCKED",
    95	              "NOT_APPLICABLE"
    96	            ]
    97	          },
    98	          "source": {
    99	            "type": "string"
   100	          },
   101	          "duration": {
   102	            "type": "number",
   103	            "minimum": 0
   104	          },
   105	          "summary": {
   106	            "type": "string"
   107	          },
   108	          "evidence_refs": {
   109	            "type": "array",
   110	            "items": {
   111	              "type": "string"
   112	            }
   113	          },
   114	          "not_applicable_reason": {
   115	            "type": "object",
   116	            "additionalProperties": false,
   117	            "required": [
   118	              "code",
   119	              "detail"
   120	            ],
   121	            "properties": {
   122	              "code": {
   123	                "type": "string"
   124	              },
   125	              "detail": {
   126	                "type": "string"
   127	              }
   128	            }
   129	          }
   130	        }
   131	      }
   132	    },
   133	    "coverage": {
   134	      "type": "object",
   135	      "additionalProperties": {
   136	        "type": "object",
   137	        "additionalProperties": false,
   138	        "required": [
   139	          "measured",
   140	          "threshold"
   141	        ],
   142	        "properties": {
   143	          "measured": {
   144	            "type": "number",
   145	            "minimum": 0,
   146	            "maximum": 1
   147	          },
   148	          "threshold": {
   149	            "type": "number",
   150	            "minimum": 0,
   151	            "maximum": 1
   152	          }
   153	        }
   154	      }
   155	    },
   156	    "evidence": {
   157	      "type": "array",
   158	      "items": {
   159	        "type": "object",
   160	        "additionalProperties": false,
   161	        "required": [
   162	          "id",
   163	          "type",
   164	          "source",
   165	          "location"
   166	        ],
   167	        "properties": {
   168	          "id": {
   169	            "type": "string"
   170	          },
   171	          "type": {
   172	            "type": "string"
   173	          },
   174	          "source": {
   175	            "type": "string"
   176	          },
   177	          "location": {
   178	            "type": "string"
   179	          },
   180	          "digest": {
   181	            "type": "string"
   182	          }
   183	        }
   184	      }
   185	    },
   186	    "blockers": {
   187	      "type": "array",
   188	      "items": {
   189	        "type": [
   190	          "string",
   191	          "object"
   192	        ]
   193	      }
   194	    },
   195	    "warnings": {
   196	      "type": "array",
   197	      "items": {
   198	        "type": [
   199	          "string",
   200	          "object"
   201	        ]
   202	      }
   203	    }
   204	  }
   205	}
     1	"""Provider contract validator implementation.
     2	
     3	Validates project quality registries, normalized invocations, provider results,
     4	and reconciles provider results against the execution plan according to the
     5	version 1 quality contracts.
     6	"""
     7	
     8	from __future__ import annotations
     9	
    10	import copy
    11	import re
    12	from typing import Any
    13	
    14	VALID_PROFILES = {"pr", "epic", "scheduled", "release"}
    15	VALID_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_APPLICABLE"}
    16	VALID_NOT_APPLICABLE_CODES = {
    17	    "profile_policy",
    18	    "scope_unmodified",
    19	    "capability_not_configured",
    20	    "target_absent",
    21	    "platform_not_applicable",
    22	}
    23	SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
    24	
    25	
    26	def _finding(code: str, message: str, **extra: Any) -> dict[str, Any]:
    27	    f = {"code": code, "message": message}
    28	    f.update(extra)
    29	    return f
    30	
    31	
    32	def _sort_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    33	    # Deduplicate findings with identical representations
    34	    unique: dict[str, dict[str, Any]] = {}
    35	    for f in findings:
    36	        key = (f.get("code", ""), f.get("provider_id", ""), f.get("field", ""), f.get("message", ""))
    37	        if key not in unique:
    38	            unique[key] = f
    39	    return sorted(
    40	        unique.values(),
    41	        key=lambda item: (
    42	            item.get("code", ""),
    43	            item.get("provider_id", ""),
    44	            item.get("field", ""),
    45	            item.get("message", ""),
    46	        ),
    47	    )
    48	
    49	
    50	def validate_registry(
    51	    registry_data: dict[str, Any],
    52	    requested_profile: str,
    53	    available_skills: set[str] | None = None,
    54	) -> dict[str, Any]:
    55	    """Validate project provider registry and select providers for the requested profile."""
    56	    findings: list[dict[str, Any]] = []
    57	
    58	    # Check top-level fields
    59	    allowed_top = {"schema_version", "providers"}
    60	    for k in sorted(registry_data.keys()):
    61	        if k not in allowed_top:
    62	            findings.append(_finding("unknown_field", f"Unknown top-level field '{k}'", field=k))
    63	
    64	    for req in ("schema_version", "providers"):
    65	        if req not in registry_data:
    66	            findings.append(_finding("missing_field", f"Missing required top-level field '{req}'", field=req))
    67	
    68	    schema_version = registry_data.get("schema_version")
    69	    if schema_version != 1:
    70	        findings.append(
    71	            _finding(
    72	                "unsupported_version",
    73	                f"Unsupported schema_version '{schema_version}', expected 1",
    74	            )
    75	        )
    76	
    77	    providers_raw = registry_data.get("providers")
    78	    if not isinstance(providers_raw, list):
    79	        if "providers" in registry_data:
    80	            findings.append(_finding("empty_providers", "Registry providers must be a non-empty list"))
    81	        return {
    82	            "status": "BLOCKED",
    83	            "providers": [],
    84	            "findings": _sort_findings(findings),
    85	        }
    86	
    87	    if len(providers_raw) == 0:
    88	        findings.append(_finding("empty_providers", "Registry providers list is empty"))
    89	
    90	    allowed_provider_fields = {"id", "skill", "required", "profiles"}
    91	    seen_ids: set[str] = set()
    92	    valid_providers: list[dict[str, Any]] = []
    93	
    94	    for idx, p in enumerate(providers_raw):
    95	        if not isinstance(p, dict):
    96	            findings.append(_finding("malformed_provider", f"Provider at index {idx} must be an object"))
    97	            continue
    98	
    99	        p_id = p.get("id")
   100	        # Check unknown fields in provider
   101	        for k in sorted(p.keys()):
   102	            if k not in allowed_provider_fields:
   103	                findings.append(
   104	                    _finding(
   105	                        "unknown_field",
   106	                        f"Unknown provider field '{k}'",
   107	                        provider_id=p_id or f"index_{idx}",
   108	                        field=k,
   109	                    )
   110	                )
   111	
   112	        # Check missing fields
   113	        for req in ("id", "skill", "required", "profiles"):
   114	            if req not in p:
   115	                findings.append(
   116	                    _finding(
   117	                        "missing_field",
   118	                        f"Missing required provider field '{req}'",
   119	                        provider_id=p_id or f"index_{idx}",
   120	                        field=req,
   121	                    )
   122	                )
   123	
   124	        if p_id:
   125	            if p_id in seen_ids:
   126	                findings.append(
   127	                    _finding(
   128	                        "duplicate_id",
   129	                        f"Duplicate provider id '{p_id}'",
   130	                        provider_id=p_id,
   131	                    )
   132	                )
   133	            else:
   134	                seen_ids.add(p_id)
   135	
   136	        profiles = p.get("profiles")
   137	        if isinstance(profiles, list):
   138	            for prof in profiles:
   139	                if prof not in VALID_PROFILES:
   140	                    findings.append(
   141	                        _finding(
   142	                            "unsupported_profile",
   143	                            f"Unsupported profile '{prof}' in provider '{p_id}'",
   144	                            provider_id=p_id,
   145	                        )
   146	                    )
   147	        elif "profiles" in p:
   148	            findings.append(
   149	                _finding(
   150	                    "unsupported_profile",
   151	                    f"Profiles for provider '{p_id}' must be a list",
   152	                    provider_id=p_id,
   153	                )
   154	            )
   155	
   156	        valid_providers.append(p)
   157	
   158	    selected_providers: list[dict[str, Any]] = []
   159	    if requested_profile in VALID_PROFILES:
   160	        for p in valid_providers:
   161	            profs = p.get("profiles", [])
   162	            if isinstance(profs, list) and requested_profile in profs:
   163	                p_id = p.get("id")
   164	                skill = p.get("skill")
   165	                if skill and available_skills is not None:
   166	                    if skill not in available_skills:
   167	                        findings.append(
   168	                            _finding(
   169	                                "unresolved_skill",
   170	                                f"Provider skill '{skill}' could not be resolved",
   171	                                provider_id=p_id,
   172	                            )
   173	                        )
   174	                selected_providers.append(p)
   175	    else:
   176	        findings.append(
   177	            _finding(
   178	                "unsupported_profile",
   179	                f"Requested profile '{requested_profile}' is not supported",
   180	            )
   181	        )
   182	
   183	    # Sort selected providers by id for deterministic ordering
   184	    selected_providers.sort(key=lambda item: item.get("id", ""))
   185	
   186	    if len(selected_providers) == 0 and len(providers_raw) > 0 and requested_profile in VALID_PROFILES:
   187	        findings.append(
   188	            _finding(
   189	                "empty_selection",
   190	                f"No providers matched the requested profile '{requested_profile}'",
   191	            )
   192	        )
   193	
   194	    status = "BLOCKED" if findings else "PASS"
   195	    return {
   196	        "status": status,
   197	        "providers": selected_providers if status == "PASS" else [],
   198	        "findings": _sort_findings(findings),
   199	    }
   200	
   201	
   202	def normalize_invocation(invocation_data: dict[str, Any]) -> dict[str, Any]:
   203	    """Validate and normalize an orchestrator invocation request."""
   204	    findings: list[dict[str, Any]] = []
   205	    allowed_fields = {"contract_version", "profile", "base_ref", "repository_sha", "provider_id", "required"}
   206	
   207	    for k in sorted(invocation_data.keys()):
   208	        if k not in allowed_fields:
   209	            findings.append(_finding("unknown_field", f"Unknown invocation field '{k}'", field=k))
   210	
   211	    contract_version = invocation_data.get("contract_version", 1)
   212	    if contract_version != 1:
   213	        findings.append(
   214	            _finding(
   215	                "unsupported_version",
   216	                f"Unsupported contract_version '{contract_version}', expected 1",
   217	            )
   218	        )
   219	
   220	    profile = invocation_data.get("profile", "pr")
   221	    if profile not in VALID_PROFILES:
   222	        findings.append(_finding("unsupported_profile", f"Unsupported profile '{profile}'"))
   223	
   224	    sha = invocation_data.get("repository_sha")
   225	    if not isinstance(sha, str) or not SHA_PATTERN.match(sha):
   226	        findings.append(_finding("invalid_repository_sha", f"Invalid repository_sha '{sha}'"))
   227	
   228	    norm = copy.deepcopy(invocation_data)
   229	    norm["contract_version"] = 1
   230	    norm["profile"] = profile
   231	
   232	    status = "BLOCKED" if findings else "PASS"
   233	    return {
   234	        "status": status,
   235	        "invocation": norm if status == "PASS" else None,
   236	        "findings": _sort_findings(findings),
   237	    }
   238	
   239	
   240	def validate_provider_result(
   241	    result_data: dict[str, Any],
   242	    invocation_data: dict[str, Any],
   243	) -> dict[str, Any]:
   244	    """Validate a provider result document against contract and invocation identity."""
   245	    findings: list[dict[str, Any]] = []
   246	
   247	    contract_version = result_data.get("contract_version")
   248	    if contract_version != 1:
   249	        findings.append(
   250	            _finding(
   251	                "unsupported_version",
   252	                f"Unsupported contract_version '{contract_version}', expected 1",
   253	            )
   254	        )
   255	
   256	    # Identity matching against invocation
   257	    exp_provider_id = invocation_data.get("provider_id")
   258	    if exp_provider_id and result_data.get("provider_id") != exp_provider_id:
   259	        findings.append(
   260	            _finding(
   261	                "provider_id_mismatch",
   262	                f"Result provider_id '{result_data.get('provider_id')}' != invocation '{exp_provider_id}'",
   263	            )
   264	        )
   265	
   266	    exp_profile = invocation_data.get("profile")
   267	    if exp_profile and result_data.get("profile") != exp_profile:
   268	        findings.append(
   269	            _finding(
   270	                "profile_mismatch",
   271	                f"Result profile '{result_data.get('profile')}' != invocation '{exp_profile}'",
   272	            )
   273	        )
   274	
   275	    exp_sha = invocation_data.get("repository_sha")
   276	    if exp_sha:
   277	        if result_data.get("repository_sha") != exp_sha:
   278	            findings.append(
   279	                _finding(
   280	                    "repository_sha_mismatch",
   280	                    "repository_sha_mismatch",
   281	                    f"Result repository_sha '{result_data.get('repository_sha')}' != invocation '{exp_sha}'",
   282	                )
   283	            )
   284	        if result_data.get("started_head") != exp_sha or result_data.get("finished_head") != exp_sha:
   285	            findings.append(
   286	                _finding(
   287	                    "sha_drift",
   288	                    "Started head or finished head does not match repository_sha",
   289	                )
   290	            )
   291	
   292	    duration = result_data.get("duration")
   293	    if duration is not None:
   294	        if not isinstance(duration, (int, float)) or duration < 0:
   295	            findings.append(_finding("invalid_duration", f"Invalid duration '{duration}'"))
   296	    else:
   297	        findings.append(_finding("missing_field", "Missing duration in result", field="duration"))
   298	
   299	    status = result_data.get("status")
   300	    if status not in VALID_STATUSES:
   301	        findings.append(_finding("invalid_status", f"Invalid status '{status}'"))
   302	
   303	    # Validate coverage
   304	    coverage = result_data.get("coverage")
   305	    if isinstance(coverage, dict):
   306	        for metric, cov in coverage.items():
   307	            if not isinstance(cov, dict):
   308	                findings.append(_finding("invalid_coverage", f"Coverage for '{metric}' must be object"))
   309	                continue
   310	            measured = cov.get("measured")
   311	            threshold = cov.get("threshold")
   312	            if not isinstance(measured, (int, float)) or measured < 0 or measured > 1.0:
   313	                findings.append(_finding("invalid_coverage", f"Invalid measured coverage '{measured}' in '{metric}'"))
   314	            if threshold is not None and (not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1.0):
   315	                findings.append(_finding("invalid_coverage", f"Invalid threshold coverage '{threshold}' in '{metric}'"))
   316	            if status == "PASS" and threshold is not None and isinstance(measured, (int, float)) and isinstance(threshold, (int, float)):
   317	                if measured < threshold:
   318	                    findings.append(
   319	                        _finding(
   320	                            "coverage_deficit",
   321	                            f"Provider reported PASS but measured coverage {measured} is below threshold {threshold} in '{metric}'",
   322	                            provider_id=result_data.get("provider_id"),
   323	                            field=f"coverage.{metric}",
   324	                        )
   325	                    )
   326	    elif coverage is not None:
   327	        findings.append(_finding("invalid_coverage", "Coverage must be an object"))
   328	
   329	    # Validate evidence
   330	    evidence = result_data.get("evidence")
   331	    evidence_ids: set[str] = set()
   332	    has_applicability_evidence = False
   333	
   334	    if isinstance(evidence, list):
   335	        for idx, ev in enumerate(evidence):
   336	            if not isinstance(ev, dict):
   337	                findings.append(_finding("malformed_evidence", f"Evidence at index {idx} must be an object"))
   338	                continue
   339	            ev_id = ev.get("id")
   340	            if ev_id:
   341	                evidence_ids.add(ev_id)
   342	            for req in ("id", "type", "source"):
   343	                if req not in ev:
   344	                    findings.append(_finding("malformed_evidence", f"Missing field '{req}' in evidence {ev_id or idx}"))
   345	            if "location" not in ev and "digest" not in ev:
   346	                findings.append(_finding("malformed_evidence", f"Evidence '{ev_id or idx}' missing location or digest"))
   347	            if ev.get("type") == "applicability":
   348	                has_applicability_evidence = True
   349	    elif evidence is not None:
   350	        findings.append(_finding("malformed_evidence", "Evidence must be a list"))
   351	
   352	    # Validate checks
   353	    checks = result_data.get("checks")
   354	    if isinstance(checks, list):
   355	        for idx, chk in enumerate(checks):
   356	            if not isinstance(chk, dict):
   357	                findings.append(_finding("malformed_check", f"Check at index {idx} must be an object"))
   358	                continue
   359	            chk_id = chk.get("id") or f"check_{idx}"
   360	            req_check_fields = ("id", "category", "status", "source", "duration", "summary", "evidence_refs")
   361	            for req in req_check_fields:
   362	                if req not in chk:
   363	                    findings.append(
   364	                        _finding(
   365	                            "missing_field",
   366	                            f"Missing required field '{req}' in check '{chk_id}'",
   367	                            field=req,
   368	                        )
   369	                    )
   370	
   371	            chk_dur = chk.get("duration")
   372	            if chk_dur is not None and (not isinstance(chk_dur, (int, float)) or chk_dur < 0):
   373	                findings.append(_finding("invalid_duration", f"Invalid duration in check '{chk_id}'"))
   374	
   375	            chk_status = chk.get("status")
   376	            if status == "PASS" and chk_status in {"FAIL", "BLOCKED"}:
   377	                findings.append(
   378	                    _finding(
   379	                        "contract_violation",
   380	                        f"Provider reported PASS but check '{chk_id}' has status '{chk_status}'",
   381	                        provider_id=result_data.get("provider_id"),
   382	                        field="status",
   383	                    )
   384	                )
   385	            if chk_status == "NOT_APPLICABLE":
   386	                reason = chk.get("not_applicable_reason")
   387	                if not isinstance(reason, dict) or "code" not in reason or "detail" not in reason:
   388	                    findings.append(
   389	                        _finding(
   390	                            "missing_not_applicable_reason",
   391	                            f"Check '{chk_id}' missing structured not_applicable_reason",
   392	                        )
   393	                    )
   394	                else:
   395	                    code = reason.get("code")
   396	                    if code not in VALID_NOT_APPLICABLE_CODES:
   397	                        findings.append(
   398	                            _finding(
   399	                                "invalid_not_applicable_reason",
   400	                                f"Invalid not_applicable_reason code '{code}' in check '{chk_id}'",
   401	                            )
   402	                        )
   403	
   404	            refs = chk.get("evidence_refs")
   405	            if isinstance(refs, list):
   406	                for ref in refs:
   407	                    if ref not in evidence_ids:
   408	                        findings.append(
   409	                            _finding(
   410	                                "unresolved_evidence_reference",
   411	                                f"Evidence reference '{ref}' in check '{chk_id}' not found in evidence",
   412	                            )
   413	                        )
   414	    elif checks is not None:
   415	        findings.append(_finding("malformed_check", "Checks must be a list"))
   416	
   417	    if status == "NOT_APPLICABLE" and not has_applicability_evidence:
   418	        findings.append(
   419	            _finding(
   420	                "missing_applicability_evidence",
   421	                "Result status is NOT_APPLICABLE but no applicability evidence was provided",
   422	            )
   423	        )
   424	
   425	    out_status = "BLOCKED" if findings else "PASS"
   426	    return {
   427	        "status": out_status,
   428	        "findings": _sort_findings(findings),
   429	    }
   430	
   431	
   432	def reconcile_results(
   433	    execution_plan: list[dict[str, Any]] | dict[str, Any],
   434	    provider_results: list[dict[str, Any]],
   435	    expected_sha: str | None = None,
   436	) -> dict[str, Any]:
   437	    """Reconcile collected provider results against the execution plan."""
   438	    findings: list[dict[str, Any]] = []
   439	
   440	    if isinstance(execution_plan, dict):
   441	        plan_entries = execution_plan.get("providers", execution_plan.get("plan", []))
   442	        expected_sha = expected_sha or execution_plan.get("repository_sha")
   443	    else:
   444	        plan_entries = execution_plan
   445	
   446	    if expected_sha is None and plan_entries:
   447	        for pe in plan_entries:
   448	            if isinstance(pe, dict) and pe.get("repository_sha"):
   449	                expected_sha = pe.get("repository_sha")
   450	                break
   451	
   452	    results_by_id: dict[str, list[dict[str, Any]]] = {}
   453	
   454	    for res in provider_results:
   455	        p_id = res.get("provider_id", "")
   456	        results_by_id.setdefault(p_id, []).append(res)
   457	
   458	        # Validate commit SHA and drift across all results
   459	        res_sha = res.get("repository_sha")
   460	        start_sha = res.get("started_head")
   461	        fin_sha = res.get("finished_head")
   462	        if start_sha != res_sha or fin_sha != res_sha:
   463	            findings.append(
   464	                _finding(
   465	                    "sha_drift",
   466	                    f"Provider '{p_id}' started_head or finished_head does not match repository_sha",
   467	                    provider_id=p_id,
   468	                )
   469	            )
   470	        if expected_sha and (res_sha != expected_sha or start_sha != expected_sha or fin_sha != expected_sha):
   471	            findings.append(
   472	                _finding(
   473	                    "sha_mismatch",
   474	                    f"Provider '{p_id}' result SHA does not match expected candidate SHA '{expected_sha}'",
   475	                    provider_id=p_id,
   476	                )
   477	            )
   478	
   479	        # Anti-False-PASS internal consistency check for each result
   480	        top_status = res.get("status")
   481	        if top_status == "PASS":
   482	            for chk in res.get("checks", []):
   483	                if isinstance(chk, dict) and chk.get("status") in {"FAIL", "BLOCKED"}:
   484	                    findings.append(
   485	                        _finding(
   486	                            "contract_violation",
   487	                            f"Provider '{p_id}' reported PASS but check '{chk.get('id')}' has status '{chk.get('status')}'",
   488	                            provider_id=p_id,
   489	                        )
   490	                    )
   491	            cov = res.get("coverage", {})
   492	            if isinstance(cov, dict):
   493	                for metric, m_cov in cov.items():
   494	                    if isinstance(m_cov, dict):
   495	                        meas = m_cov.get("measured")
   496	                        thresh = m_cov.get("threshold")
   497	                        if thresh is not None and isinstance(meas, (int, float)) and isinstance(thresh, (int, float)):
   498	                            if meas < thresh:
   499	                                findings.append(
   500	                                    _finding(
   501	                                        "coverage_deficit",
   502	                                        f"Provider '{p_id}' reported PASS but measured coverage {meas} is below threshold {thresh} in '{metric}'",
   503	                                        provider_id=p_id,
   504	                                    )
   505	                                )
   506	
   507	    reconciled_results: list[dict[str, Any]] = []
   508	
   509	    for plan_entry in plan_entries:
   510	        p_id = plan_entry.get("id", "")
   511	        is_required = plan_entry.get("required", True)
   512	        matching = results_by_id.get(p_id, [])
   513	
   514	        if len(matching) == 0:
   515	            findings.append(
   516	                _finding(
   517	                    "missing_result",
   518	                    f"Missing result for provider '{p_id}'",
   519	                    provider_id=p_id,
   520	                )
   521	            )
   522	            reconciled_results.append(
   523	                {
   524	                    "provider_id": p_id,
   525	                    "status": "BLOCKED",
   526	                    "required": is_required,
   527	                    "blockers": [f"Missing result for provider '{p_id}'"],
   528	                }
   529	            )
   530	        elif len(matching) > 1:
   531	            findings.append(
   532	                _finding(
   533	                    "duplicate_result",
   534	                    f"Duplicate results ({len(matching)}) received for provider '{p_id}'",
   535	                    provider_id=p_id,
   536	                )
   537	            )
   538	            reconciled_results.append(
   539	                {
   540	                    "provider_id": p_id,
   541	                    "status": "BLOCKED",
   542	                    "required": is_required,
   543	                    "blockers": [f"Duplicate results received for provider '{p_id}'"],
   544	                }
   545	            )
   546	        else:
   547	            reconciled_results.append(matching[0])
   548	
   549	    reconciled_results.sort(key=lambda item: item.get("provider_id", ""))
   550	
   551	    status = "PASS"
   552	    if findings:
   553	        status = "BLOCKED"
   554	    elif any(r.get("status") == "FAIL" for r in reconciled_results):
   555	        status = "FAIL"
   556	    elif any(r.get("status") == "BLOCKED" for r in reconciled_results):
   557	        status = "BLOCKED"
   558	
   559	    return {
   560	        "status": status,
   561	        "results": reconciled_results,
   562	        "findings": _sort_findings(findings),
   563	    }
   564	
   565	
   566	def validate_capability_manifest(
   567	    manifest_data: dict[str, Any],
   568	    requested_profile: str = "pr",
   569	) -> dict[str, Any]:
   570	    """Validate capability manifest (.agents/quality/*-quality.json) against schema version 1."""
   571	    findings: list[dict[str, Any]] = []
   572	
   573	    if manifest_data.get("schema_version") != 1:
   574	        findings.append(
   575	            _finding("unsupported_version", f"Unsupported schema_version '{manifest_data.get('schema_version')}', expected 1")
   576	        )
   577	
   578	    capabilities = manifest_data.get("capabilities")
   579	    if not isinstance(capabilities, dict):
   580	        findings.append(_finding("missing_capabilities", "Missing or invalid 'capabilities' object"))

 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Check that every epic BDD scenario is assigned to a task and covered by an integration test.
     3	
     4	Usage:
     5	  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
     6	  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
     7	                                  [--results <report file|dir|glob ...>]
     8	
     9	Exit codes: 0 all covered; 1 traceability failure; 2 usage error.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import re
    15	import subprocess
    16	import sys
    17	from pathlib import Path
    18	
    19	from result_reports import ReportError, load_reports, reference_pattern, verdicts
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
   156	
   157	def check_tests(ids: list[str], selected: list[str], roots: list[Path],
   158	                check_stale: bool) -> tuple[dict[str, list[str]], list[str], list[str]]:
   159	    patterns = {identifier: reference_pattern(identifier) for identifier in selected}
   160	    coverage: dict[str, list[str]] = {identifier: [] for identifier in selected}
   161	    stale = stale_pattern(ids)
   162	    known = set(ids)
   163	    problems: list[str] = []
   164	    files, warnings = integration_files(roots)
   165	    for path in files:
   166	        try:
   167	            lines = path.read_text(encoding="utf-8").splitlines()
   168	        except UnicodeDecodeError:
   169	            continue
   170	        for number, line in enumerate(lines, start=1):
   171	            for identifier, pattern in patterns.items():
   172	                if pattern.search(line):
   173	                    coverage[identifier].append(f"{path}:{number}")
   174	            if check_stale:
   175	                problems.extend(f"{path}:{number}: stale reference {token}"
   176	                                for token in stale.findall(line) if token not in known)
   177	    return coverage, problems, warnings
   178	
   179	
   180	def split_values(values: list[str] | None) -> list[str]:
   181	    """Accept space- or comma-separated values, as copied from an HLD or Covers: line."""
   182	    return [item for value in values or [] for part in value.split(",") for item in part.split() if item]
   183	
   184	
   185	def report(coverage: dict[str, list[str]], problems: list[str], warnings: list[str]) -> int:
   186	    width = max((len(identifier) for identifier in coverage), default=0)
   187	    for identifier, places in coverage.items():
   188	        print(f"{identifier.ljust(width)}    {', '.join(places) if places else '(none)'}")
   189	    for warning in warnings:
   190	        print(warning, file=sys.stderr)
   191	    for problem in problems:
   192	        print(problem)
   193	    covered = sum(1 for places in coverage.values() if places)
   194	    failed = bool(problems) or covered < len(coverage)
   195	    print(f"Result: {covered}/{len(coverage)} covered — {'FAIL' if failed else 'PASS'}")
   196	    return 1 if failed else 0
   197	
   198	
   199	def report_results(ids: list[str], selected: list[str], roots: list[Path], results: list[str],
   200	                   check_stale: bool, unknown: list[str]) -> int:
   201	    """Coverage proven by test results: each selected identifier needs a passed case."""
   202	    cases = load_reports(results, Path.cwd())
   203	    _, problems, warnings = check_tests(ids, [], roots, check_stale)
   204	    if check_stale:
   205	        stale, known = stale_pattern(ids), set(ids)
   206	        problems.extend(f"{case.name}: stale reference {token}" for case in cases
   207	                        for token in stale.findall(f"{case.name} {case.classname}") if token not in known)
   208	    judged = verdicts(selected, cases)
   209	    width = max((len(identifier) for identifier in judged), default=0)
   210	    for identifier, (passed, detail) in judged.items():
   211	        print(f"{identifier.ljust(width)}    {'PASS' if passed else 'FAIL'} {detail}")
   212	    for warning in warnings:
   213	        print(warning, file=sys.stderr)
   214	    problems = unknown + problems
   215	    for problem in problems:
   216	        print(problem)
   217	    covered = sum(1 for passed, _ in judged.values() if passed)
   218	    failed = bool(problems) or covered < len(judged)
   219	    print(f"Result: {covered}/{len(judged)} covered — {'FAIL' if failed else 'PASS'}")
   220	    return 1 if failed else 0
   221	
   222	
   223	def main(argv: list[str] | None = None) -> int:
   224	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   225	    modes = parser.add_subparsers(dest="mode", required=True)
   226	    plan = modes.add_parser("plan", help="every scenario is assigned to exactly one task")
   227	    plan.add_argument("--scenarios", required=True, type=Path)
   228	    plan.add_argument("--tasks", required=True, nargs="+", type=Path)
   229	    tests = modes.add_parser("tests", help="every scenario has at least one integration test")
   230	    tests.add_argument("--scenarios", required=True, type=Path)
   231	    tests.add_argument("--roots", required=True, nargs="+")
   232	    tests.add_argument("--ids", nargs="+")
   233	    tests.add_argument("--results", nargs="+")
   234	    args = parser.parse_args(argv)
   235	    try:
   236	        ids, problems = load_scenarios(args.scenarios)
   237	        if problems:
   238	            print("\n".join(problems))
   239	            print("Result: scenario document invalid — FAIL")
   240	            return 1
   241	        if args.mode == "plan":
   242	            coverage, problems = check_plan(ids, args.tasks)
   243	            return report(coverage, problems, [])
   244	        roots = [Path(value) for value in split_values(args.roots)]
   245	        selected = split_values(args.ids) or ids
   246	        unknown = [f"--ids names unknown identifier {identifier}"
   247	                   for identifier in selected if identifier not in ids]
   248	        known_selected = [identifier for identifier in selected if identifier in ids]
   249	        if args.results:
   250	            return report_results(ids, known_selected, roots, split_values(args.results),
   251	                                  not args.ids, unknown)
   252	        coverage, problems, warnings = check_tests(ids, known_selected, roots, not args.ids)
   253	        return report(coverage, unknown + problems, warnings)
   254	    except (UsageError, ReportError) as error:
   255	        print(f"error: {error}", file=sys.stderr)
   256	        return 2
   257	
   258	
   259	if __name__ == "__main__":
   260	    sys.exit(main())
     1	#!/usr/bin/env python3
     2	"""Read JUnit XML and Dart JSON test reports, and decide which identifiers they prove.
     3	
     4	Imported by check_bdd_traceability.py and run_task_checks.py; it has no command line.
     5	"""
     6	from __future__ import annotations
     7	
     8	import glob
     9	import json
    10	import re
    11	import xml.etree.ElementTree as ET
    12	from dataclasses import dataclass
    13	from pathlib import Path
    14	
    15	
    16	class ReportError(Exception):
    17	    """A report path that is missing, or a file in neither format."""
    18	
    19	
    20	@dataclass(frozen=True)
    21	class Case:
    22	    name: str
    23	    classname: str
    24	    status: str  # "passed", "failed" or "skipped"
    25	
    26	
    27	def reference_pattern(identifier: str) -> re.Pattern[str]:
    28	    """Match an identifier in any case, with - and _ interchangeable, not inside a longer token."""
    29	    body = "[-_]".join(re.escape(part) for part in identifier.split("-"))
    30	    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)
    31	
    32	
    33	def parse_junit(text: str) -> list[Case]:
    34	    cases = []
    35	    for element in ET.fromstring(text).iter("testcase"):
    36	        tags = {child.tag for child in element}
    37	        status = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
    38	        cases.append(Case(element.get("name", ""), element.get("classname", ""), status))
    39	    return cases
    40	
    41	
    42	def parse_dart(text: str) -> list[Case]:
    43	    names: dict[object, str] = {}
    44	    cases = []
    45	    for line in text.splitlines():
    46	        if not line.strip():
    47	            continue
    48	        try:
    49	            event = json.loads(line)
    50	        except Exception:
    51	            continue
    52	        if isinstance(event, list):
    53	            if event and isinstance(event[0], dict):
    54	                event = event[0]
    55	            else:
    56	                continue
    57	        if not isinstance(event, dict):
    58	            continue
    59	        if event.get("type") == "testStart":
    60	            names[event["test"]["id"]] = event["test"]["name"]
    61	        elif event.get("type") == "testDone" and event.get("testID") in names:
    62	            name = names.pop(event["testID"])
    63	            if event.get("hidden"):
    64	                continue
    65	            status = ("skipped" if event.get("skipped")
    66	                      else "passed" if event.get("result") == "success" else "failed")
    67	            cases.append(Case(name, "", status))
    68	    return cases
    69	
    70	
    71	def report_files(path: str, root: Path) -> list[Path]:
    72	    target = root / path
    73	    if target.is_dir():
    74	        return sorted(p for pattern in ("*.xml", "*.json") for p in target.rglob(pattern))
    75	    if target.is_file():
    76	        return [target]
    77	    matches = sorted(Path(match) for match in glob.glob(str(target), recursive=True))
    78	    if not matches:
    79	        raise ReportError(f"results path not found: {path}")
    80	    return [p for match in matches for p in report_files(str(match), root)]
    81	
    82	
    83	def load_files(files: list[Path]) -> list[Case]:
    84	    cases: list[Case] = []
    85	    for file in files:
    86	        text = file.read_text(encoding="utf-8", errors="replace")
    87	        lead = text.lstrip()[:1]
    88	        try:
    89	            if lead == "<":
    90	                cases.extend(parse_junit(text))
    91	            elif lead == "{" or any(line.startswith("{") for line in text.splitlines()):
    92	                cases.extend(parse_dart(text))
    93	            else:
    94	                raise ReportError(f"{file} is neither JUnit XML nor Dart JSON")
    95	        except (ET.ParseError, ValueError, KeyError) as error:
    96	            raise ReportError(f"{file} is not a valid report: {error}") from None
    97	    return cases
    98	
    99	
   100	def load_reports(paths: list[str], root: Path) -> list[Case]:
   101	    return load_files([file for path in paths for file in report_files(path, root)])
   102	
   103	
   104	def belongs(case: Case, identifier: str) -> bool:
   105	    pattern = reference_pattern(identifier)
   106	    return bool(pattern.search(case.name) or pattern.search(case.classname))
   107	
   108	
   109	def verdicts(ids: list[str], cases: list[Case]) -> dict[str, tuple[bool, str]]:
   110	    result: dict[str, tuple[bool, str]] = {}
   111	    for identifier in ids:
   112	        own = [case for case in cases if belongs(case, identifier)]
   113	        failed = next((c for c in own if c.status == "failed"), None)
   114	        passed = next((c for c in own if c.status == "passed"), None)
   115	        if failed:
   116	            result[identifier] = (False, f"failed in {failed.name}")
   117	        elif passed:
   118	            result[identifier] = (True, passed.name)
   119	        elif own:
   120	            result[identifier] = (False, "skipped")
   121	        else:
   122	            result[identifier] = (False, "no test case in results")
   123	    return result
   124	
   125	
   126	def digest(cases: list[Case], ids: list[str]) -> dict:
   127	    own = [case for case in cases if any(belongs(case, identifier) for identifier in ids)]
   128	    totals = {status: sum(1 for c in own if c.status == status) for status in ("passed", "failed", "skipped")}
   129	    return {"totals": totals,
   130	            "cases": [{"name": c.name, "classname": c.classname, "status": c.status} for c in own]}
skills/dev-implementation/resources/scripts/run_task_checks.py:2:"""Run a task's Verification rows and record the outcome as evidence.
skills/dev-implementation/resources/scripts/run_task_checks.py:7:  run_task_checks.py status <task mirror>   (read-only: print the recorded runs and the done-gate verdict)
skills/dev-implementation/resources/scripts/run_task_checks.py:9:Exit codes: 0 every row passed (status: the done gate passes); 1 a row failed (evidence still written) or
skills/dev-implementation/resources/scripts/run_task_checks.py:10:the done gate fails; 2 usage error or a task
skills/dev-implementation/resources/scripts/run_task_checks.py:11:file the parser rejects (no evidence written).
skills/dev-implementation/resources/scripts/run_task_checks.py:41:evaluate_done_gate: Any = _tc.evaluate_done_gate
skills/dev-implementation/resources/scripts/run_task_checks.py:44:load_evidence: Any = _tc.load_evidence
skills/dev-implementation/resources/scripts/run_task_checks.py:50:save_evidence: Any = _tc.save_evidence
skills/dev-implementation/resources/scripts/run_task_checks.py:60:_cbt: Any = importlib.import_module("check_bdd_traceability")
skills/dev-implementation/resources/scripts/run_task_checks.py:159:        features_task = layout.root / ".devtool" / "features" / "done" / path.name
skills/dev-implementation/resources/scripts/run_task_checks.py:222:        return cast(list[str], load_scenarios(layout.epic_dir / "bdd_scenarios.en.md")[0])
skills/dev-implementation/resources/scripts/run_task_checks.py:348:    evidence = load_evidence(layout.evidence) or {"schema": 1, "task": Path(args.task).stem, "runs": {}}
skills/dev-implementation/resources/scripts/run_task_checks.py:349:    evidence["runs"][args.mode] = {"head": head, "tree": tree, "patch_id": patch_id, "started": started,
skills/dev-implementation/resources/scripts/run_task_checks.py:351:    save_evidence(layout.evidence, evidence)
skills/dev-implementation/resources/scripts/run_task_checks.py:356:    print(f"Evidence: {layout.evidence}")
skills/dev-implementation/resources/scripts/run_task_checks.py:362:    evidence = load_evidence(layout.evidence) or {}
skills/dev-implementation/resources/scripts/run_task_checks.py:363:    for kind, run in evidence.get("runs", {}).items():
skills/dev-implementation/resources/scripts/run_task_checks.py:367:    failures = evaluate_done_gate(args.task)
skills/dev-implementation/resources/scripts/run_task_checks.py:368:    print("done gate: " + ("FAIL" if failures else "PASS"))
skills/dev-implementation/resources/scripts/sync_task_status.py:16:`task` mode rewrites `status`, `modified`, and -- on `done` -- `completedAt` in
skills/dev-implementation/resources/scripts/sync_task_status.py:39:TASK_STATUSES = ("backlog", "todo", "in-progress", "review", "done")
skills/dev-implementation/resources/scripts/sync_task_status.py:154:    """Every copy of one task inside one checkout: features, features/done, + each epic dir."""
skills/dev-implementation/resources/scripts/sync_task_status.py:157:        root / ".devtool" / "features" / "done" / f"{task_id}.md",
skills/dev-implementation/resources/scripts/sync_task_status.py:177:        for features_dir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
skills/dev-implementation/resources/scripts/sync_task_status.py:204:            if new_status == "done":
skills/dev-implementation/resources/scripts/sync_task_status.py:217:    """Move a features copy into features/done when it becomes done, and back when it leaves done.
skills/dev-implementation/resources/scripts/sync_task_status.py:222:    if status == "done" and path.parent == features:
skills/dev-implementation/resources/scripts/sync_task_status.py:223:        target = features / "done" / path.name
skills/dev-implementation/resources/scripts/sync_task_status.py:224:    elif status != "done" and path.parent == features / "done":
skills/dev-implementation/resources/scripts/sync_task_status.py:240:            root / ".devtool" / "features" / "done",
skills/dev-implementation/resources/scripts/sync_task_status.py:301:    text = re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
skills/dev-implementation/resources/scripts/sync_task_status.py:307:    return re.sub(r"\]\(\.\./\.\./features/(?:done/)?(task_[^)]+\.md)\)", r"](\1)", text)
skills/dev-implementation/resources/scripts/sync_task_status.py:342:    """Move all done tasks of an epic from features/done into .devtool/epic/<epic_dir>/,
skills/dev-implementation/resources/scripts/sync_task_status.py:355:        # 1. Relocate task files from features and features/done
skills/dev-implementation/resources/scripts/sync_task_status.py:356:        for fdir in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
skills/dev-implementation/resources/scripts/sync_task_status.py:394:        # 5. Ensure .gitkeep exists in features/done if directory is empty
skills/dev-implementation/resources/scripts/sync_task_status.py:395:        done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/sync_task_status.py:396:        if done_dir.is_dir():
skills/dev-implementation/resources/scripts/sync_task_status.py:397:            non_keep = [f for f in done_dir.iterdir() if f.name != ".gitkeep"]
skills/dev-implementation/resources/scripts/sync_task_status.py:399:                (done_dir / ".gitkeep").touch()
skills/dev-implementation/resources/scripts/sync_task_status.py:428:    if new_status.strip().lower() in ("done", "hoàn thành"):
skills/dev-implementation/resources/scripts/sync_task_status.py:434:def archive_all_done_epics(roots: list[Path]) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:435:    """Find all completed tasks in .devtool/features/done/ and archive them into their epics.
skills/dev-implementation/resources/scripts/sync_task_status.py:441:        done_dir = root / ".devtool" / "features" / "done"
skills/dev-implementation/resources/scripts/sync_task_status.py:442:        if not done_dir.is_dir():
skills/dev-implementation/resources/scripts/sync_task_status.py:444:        for task_file in sorted(done_dir.glob("task_*.md")):
skills/dev-implementation/resources/scripts/sync_task_status.py:463:    for features in (root / ".devtool" / "features", root / ".devtool" / "features" / "done"):
skills/dev-implementation/resources/scripts/sync_task_status.py:473:def done_gate_failures(task_id: str) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:474:    """Messages refusing `task <id> done` for a code epic's task; empty when the gate does not apply or passes."""
skills/dev-implementation/resources/scripts/sync_task_status.py:475:    from task_contract import ContractError, evaluate_done_gate, section
skills/dev-implementation/resources/scripts/sync_task_status.py:485:            return ["run the done gate in the checkout that holds the task and its evidence (the epic worktree)"]
skills/dev-implementation/resources/scripts/sync_task_status.py:492:        return evaluate_done_gate(mirror)
skills/dev-implementation/resources/scripts/sync_task_status.py:515:        "archive-epic", help="Archive done tasks of an epic into .devtool/epic/<epic_dir>/"
skills/dev-implementation/resources/scripts/sync_task_status.py:520:        "archive-done",
skills/dev-implementation/resources/scripts/sync_task_status.py:521:        help="Find all completed tasks in .devtool/features/done/ and archive them into their respective epic directories",
skills/dev-implementation/resources/scripts/sync_task_status.py:533:        failures = done_gate_failures(args.task_id) if args.status == "done" else []
skills/dev-implementation/resources/scripts/sync_task_status.py:535:            sys.stderr.write(f"refused: {args.task_id} cannot be marked done\n")
skills/dev-implementation/resources/scripts/sync_task_status.py:576:    elif args.command == "archive-done":
skills/dev-implementation/resources/scripts/sync_task_status.py:578:        done_epics = archive_all_done_epics(roots)
skills/dev-implementation/resources/scripts/sync_task_status.py:579:        if done_epics:
skills/dev-implementation/resources/scripts/sync_task_status.py:580:            print(f"Archived {len(done_epics)} epic(s) into .devtool/epic/: {', '.join(done_epics)}")

exec
/bin/zsh -lc "nl -ba skills/setup_quality_check/SKILL.md; nl -ba skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py; nl -ba scripts/verify.sh | sed -n '1,260p'; rg -n 'platform|python|web|rust|schema_version|providers' skills/quality_check/resources/schemas/check-quality.schema.json skills/quality_check/resources/scripts/test_quality_provider_acceptance.py; nl -ba .claude-plugin/plugin.json; nl -ba .agents/plugins/marketplace.json" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	---
     2	name: setup_quality_check
     3	description: Inspects repository structure, auto-detects platforms (Flutter, Android, iOS, Rust, or Polyglot), and scaffolds standardized quality provider configurations adhering to canonical templates.
     4	---
     5	
     6	# Setup Quality Check
     7	
     8	Automated onboarding skill that bootstraps the d3nexus quality governance system for both Greenfield
     9	(new projects) and Brownfield (legacy repositories before active maintenance or AI agent code generation).
    10	
    11	## Overview
    12	
    13	The quality governance model requires deterministic, SHA-bound quality verification before any feature branch
    14	or PR is merged. Setting up quality checking ensures that:
    15	- Every platform present in the repository is discovered and registered in `.agents/quality/check_quality.json`.
    16	- Platform-specific quality manifests (`flutter-quality.json`, `android-quality.json`, `ios-quality.json`, `rust-quality.json`, `python-quality.json`) are populated with canonical, production-tested verification toolchains.
    17	- Code generation agents and developers are constrained by automated quality gates from day one.
    18	
    19	## Platform Detection Heuristics
    20	
    21	The scaffolding engine inspects repository roots against the following marker files:
    22	
    23	| Platform | Markers Detected | Provider ID | Target Manifest | Canonical Toolchain |
    24	|---|---|---|---|---|
    25	| **Flutter** | `pubspec.yaml`, `melos.yaml` | `flutter-core` | `flutter-quality.json` | `dartfmt.sh`, `fvm flutter analyze`, `check_module_boundaries.sh`, `check_license_header.sh`, `melos run test`, `testWithCoverage.sh` |
    26	| **Android** | `build.gradle.kts`, `build.gradle`, `settings.gradle.kts`, `settings.gradle` | `android-core` | `android-quality.json` | `spotlessCheck`, `detekt`, `apiCheck`, `:konsist-test:test`, `testDebugUnitTest`, `jacocoTestReport`, `pkill -9 java` |
    27	| **iOS** | `Project.swift`, `Tuist.swift`, `Package.swift` | `ios-core` | `ios-quality.json` | `swiftformat`, `swiftlint`, `ArchTests` (K1-K10), `check_module_boundaries.sh`, `swift test`, `check_coverage_thresholds.sh` |
    28	| **Rust** | `Cargo.toml` | `rust-core` | `rust-quality.json` | `cargo fmt`, `cargo check`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, `xtask check-architecture` |
    29	| **Python** | `pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, `Pipfile` | `python-core` | `python-quality.json` | `ruff format`, `ruff check`, `mypy --strict`, `pytest`, `pytest-cov`, `lint-imports` |
    30	
    31	In composite repositories (e.g. Flutter mobile host with Rust core, or native Android/iOS bridging modules), all detected platforms are registered in `.agents/quality/check_quality.json`.
    32	
    33	## Operational Workflow
    34	
    35	### Step 1: Dry-Run Inspection
    36	
    37	Inspect what platforms the tool detects and what files will be created:
    38	
    39	```bash
    40	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --dry-run
    41	```
    42	
    43	### Step 2: Scaffold Configuration Files
    44	
    45	Execute scaffolding to generate the `.agents/quality/` directory:
    46	
    47	```bash
    48	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py
    49	```
    50	
    51	If configurations already exist and you want to reset them to canonical defaults:
    52	
    53	```bash
    54	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --force
    55	```
    56	
    57	### Step 3: Run Baseline Quality Verification
    58	
    59	Run an initial check to certify that the repository passes the baseline PR profile:
    60	
    61	```bash
    62	# Invoke quality_check skill
    63	python3 skills/quality_check/resources/scripts/validate_quality_contract.py .agents/quality/check_quality.json
    64	```
    65	
    66	## CLI Reference
    67	
    68	`scaffold_quality_manifest.py` accepts the following arguments:
    69	
    70	- `--root <DIR>`: Path to the target repository root (default: current directory `.`).
    71	- `--output-dir <DIR>`: Explicit output directory for generated manifests (default: `<root>/.agents/quality`).
    72	- `--platform <LIST>`: Override automatic detection with comma-separated platforms (`flutter`, `android`, `ios`, `rust`, `python`).
    73	- `--force`: Overwrite existing quality manifests (fails safely by default to prevent accidental overwrite).
    74	- `--dry-run`: Display detected platforms and planned file list without writing to disk.
    75	
    76	## Related Skills
    77	
    78	- [Quality Check](../quality_check/SKILL.md)
    79	- [Flutter Quality Check](../flutter-quality-check/SKILL.md)
    80	- [Android Quality Check](../android-quality-check/SKILL.md)
    81	- [iOS Quality Check](../ios-quality-check/SKILL.md)
    82	- [Rust Quality Check](../rust-quality-check/SKILL.md)
    83	- [Python Quality Check](../python-quality-check/SKILL.md)
     1	#!/usr/bin/env python3
     2	"""
     3	Automated Scaffolding Engine for Quality Providers.
     4	Inspects project repository roots, detects project platforms (Flutter, Android, iOS, Rust),
     5	and generates standardized .agents/quality/ configurations adhering to canonical templates.
     6	"""
     7	from __future__ import annotations
     8	
     9	import argparse
    10	import json
    11	import sys
    12	from pathlib import Path
    13	from typing import Dict, List, Optional, Any
    14	
    15	
    16	class ScaffoldError(Exception):
    17	    """Raised when scaffolding fails due to safety or detection violations."""
    18	    pass
    19	
    20	
    21	PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    22	    "flutter": {
    23	        "provider_id": "flutter-core",
    24	        "skill": "d3nexus:flutter-quality-check",
    25	        "filename": "flutter-quality.json",
    26	        "manifest": {
    27	            "schema_version": 1,
    28	            "capabilities": {
    29	                "format": ["./scripts/dartfmt.sh"],
    30	                "analyze": ["fvm", "flutter", "analyze"],
    31	                "boundaries": ["./scripts/check_module_boundaries.sh"],
    32	                "license": ["./scripts/check_license_header.sh"],
    33	                "test": ["melos", "run", "test"],
    34	                "coverage": {
    35	                    "command": ["./scripts/testWithCoverage.sh"],
    36	                    "lcov_path": "coverage_report/lcov.info",
    37	                    "threshold": 0.85
    38	                },
    39	                "acceptance": ["./scripts/acceptance_check.sh"]
    40	            },
    41	            "profiles": {
    42	                "pr": ["format", "analyze", "test"],
    43	                "epic": ["format", "analyze", "boundaries", "license", "test", "coverage"]
    44	            }
    45	        }
    46	    },
    47	    "android": {
    48	        "provider_id": "android-core",
    49	        "skill": "d3nexus:android-quality-check",
    50	        "filename": "android-quality.json",
    51	        "manifest": {
    52	            "schema_version": 1,
    53	            "capabilities": {
    54	                "format": ["./gradlew", "spotlessCheck"],
    55	                "lint": ["./gradlew", "detekt"],
    56	                "bcv": ["./gradlew", "apiCheck"],
    57	                "architecture": ["./gradlew", ":konsist-test:test"],
    58	                "test": ["./gradlew", "testDebugUnitTest"],
    59	                "coverage": {
    60	                    "command": ["./gradlew", "jacocoTestReport"],
    61	                    "report_path": "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
    62	                    "threshold": 0.85
    63	                },
    64	                "acceptance": ["./scripts/acceptance_check.sh"],
    65	                "cleanup": ["pkill", "-9", "java"]
    66	            },
    67	            "profiles": {
    68	                "pr": ["format", "lint", "test"],
    69	                "epic": ["format", "lint", "bcv", "architecture", "test", "coverage", "cleanup"]
    70	            }
    71	        }
    72	    },
    73	    "ios": {
    74	        "provider_id": "ios-core",
    75	        "skill": "d3nexus:ios-quality-check",
    76	        "filename": "ios-quality.json",
    77	        "manifest": {
    78	            "schema_version": 1,
    79	            "capabilities": {
    80	                "format": ["swiftformat", "--config", "quality/.swiftformat", "--lint", "."],
    81	                "lint": ["swiftlint", "lint", "--config", "quality/.swiftlint.yml", "--strict"],
    82	                "architecture": ["swift", "test", "--package-path", "ArchTests"],
    83	                "boundaries": ["./scripts/check_module_boundaries.sh"],
    84	                "test": ["swift", "test"],
    85	                "coverage": {
    86	                    "command": ["./scripts/check_coverage_thresholds.sh"],
    87	                    "profdata_path": "default.profdata",
    88	                    "threshold": 0.85
    89	                },
    90	                "acceptance": ["./scripts/acceptance_check.sh"]
    91	            },
    92	            "profiles": {
    93	                "pr": ["format", "lint", "test"],
    94	                "epic": ["format", "lint", "architecture", "boundaries", "test", "coverage"]
    95	            }
    96	        }
    97	    },
    98	    "rust": {
    99	        "provider_id": "rust-core",
   100	        "skill": "d3nexus:rust-quality-check",
   101	        "filename": "rust-quality.json",
   102	        "manifest": {
   103	            "schema_version": 1,
   104	            "capabilities": {
   105	                "format": ["cargo", "fmt", "--all", "--", "--check"],
   106	                "check": ["cargo", "check", "--all-targets"],
   107	                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
   108	                "test": ["cargo", "test", "--workspace"],
   109	                "coverage": {
   110	                    "command": ["cargo", "llvm-cov", "--workspace", "--fail-under-lines", "80"],
   111	                    "threshold": 0.8
   112	                },
   113	                "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"]
   114	            },
   115	            "profiles": {
   116	                "pr": ["format", "check", "clippy", "test", "architecture"],
   117	                "epic": ["format", "check", "clippy", "test", "coverage", "architecture"]
   118	            }
   119	        }
   120	    },
   121	    "python": {
   122	        "provider_id": "python-core",
   123	        "skill": "d3nexus:python-quality-check",
   124	        "filename": "python-quality.json",
   125	        "manifest": {
   126	            "schema_version": 1,
   127	            "capabilities": {
   128	                "format": ["uv", "run", "ruff", "format", "--check", "."],
   129	                "lint": ["uv", "run", "ruff", "check", "."],
   130	                "type_check": ["uv", "run", "mypy", "--strict", "src"],
   131	                "test": ["uv", "run", "pytest", "-m", "not slow and not acceptance and not live_llm"],
   132	                "coverage": {
   133	                    "command": ["uv", "run", "pytest", "--cov=src", "--cov-report=json:coverage.json"],
   134	                    "threshold": 0.8
   135	                },
   136	                "architecture": ["uv", "run", "lint-imports"]
   137	            },
   138	            "profiles": {
   139	                "pr": ["format", "lint", "type_check", "test"],
   140	                "epic": ["format", "lint", "type_check", "test", "coverage", "architecture"]
   141	            }
   142	        }
   143	    }
   144	}
   145	
   146	
   147	def detect_platforms(repo_root: Path) -> List[str]:
   148	    """
   149	    Inspects repository root directory and returns detected platform names.
   150	    Supports Flutter, Android, iOS, Rust, and Python heuristics.
   151	    """
   152	    detected = []
   153	
   154	    # Flutter detection
   155	    if (repo_root / "pubspec.yaml").is_file() or (repo_root / "melos.yaml").is_file():
   156	        detected.append("flutter")
   157	
   158	    # Android detection
   159	    android_markers = [
   160	        "build.gradle.kts",
   161	        "build.gradle",
   162	        "settings.gradle.kts",
   163	        "settings.gradle",
   164	    ]
   165	    if any((repo_root / marker).is_file() for marker in android_markers):
   166	        detected.append("android")
   167	
   168	    # iOS detection
   169	    ios_markers = [
   170	        "Project.swift",
   171	        "Tuist.swift",
   172	        "Package.swift",
   173	    ]
   174	    if any((repo_root / marker).is_file() for marker in ios_markers):
   175	        detected.append("ios")
   176	
   177	    # Rust detection
   178	    if (repo_root / "Cargo.toml").is_file():
   179	        detected.append("rust")
   180	
   181	    # Python detection
   182	    python_markers = [
   183	        "pyproject.toml",
   184	        "uv.lock",
   185	        "requirements.txt",
   186	        "setup.py",
   187	        "Pipfile",
   188	    ]
   189	    if any((repo_root / marker).is_file() for marker in python_markers):
   190	        detected.append("python")
   191	
   192	    return sorted(list(set(detected)))
   193	
   194	
   195	def build_registry_data(platforms: List[str]) -> Dict[str, Any]:
   196	    """Builds standard check_quality.json structure for given platforms."""
   197	    providers = []
   198	    for p in platforms:
   199	        cfg = PLATFORM_CONFIGS[p]
   200	        providers.append({
   201	            "id": cfg["provider_id"],
   202	            "skill": cfg["skill"],
   203	            "required": True,
   204	            "profiles": ["pr", "epic"]
   205	        })
   206	
   207	    return {
   208	        "schema_version": 1,
   209	        "providers": providers
   210	    }
   211	
   212	
   213	def scaffold_quality_manifests(
   214	    repo_root: Path,
   215	    output_dir: Optional[Path] = None,
   216	    platforms: Optional[List[str]] = None,
   217	    force: bool = False,
   218	    dry_run: bool = False,
   219	) -> Dict[str, Any]:
   220	    """
   221	    Scaffolds quality check registry and provider manifests into output_dir.
   222	    Raises ScaffoldError on detection failures or overwrite conflicts.
   223	    """
   224	    repo_root = repo_root.resolve()
   225	    if output_dir is None:
   226	        target_dir = repo_root / ".agents" / "quality"
   227	    else:
   228	        target_dir = output_dir.resolve()
   229	
   230	    if platforms is None:
   231	        detected = detect_platforms(repo_root)
   232	    else:
   233	        detected = sorted(list(set(platforms)))
   234	        for p in detected:
   235	            if p not in PLATFORM_CONFIGS:
   236	                raise ScaffoldError(f"Unsupported platform specified: '{p}'. Allowed: {list(PLATFORM_CONFIGS.keys())}")
   237	
   238	    if not detected:
   239	        raise ScaffoldError(
   240	            f"No supported platform detected in repository root: {repo_root}. "
   241	            f"Supported platforms: {list(PLATFORM_CONFIGS.keys())}"
   242	        )
   243	
   244	    # Prepare file mappings
   245	    target_files: Dict[Path, Dict[str, Any]] = {}
   246	    reg_path = target_dir / "check_quality.json"
   247	    target_files[reg_path] = build_registry_data(detected)
   248	
   249	    for p in detected:
   250	        cfg = PLATFORM_CONFIGS[p]
   251	        p_path = target_dir / cfg["filename"]
   252	        target_files[p_path] = cfg["manifest"]
   253	
   254	    # Check for existing files if not force
   255	    if not force:
   256	        for fpath in target_files:
   257	            if fpath.exists():
   258	                raise ScaffoldError(
   259	                    f"Configuration file already exists: {fpath}. Use --force to overwrite."
   260	                )
   261	
   262	    if dry_run:
   263	        return {
   264	            "detected_platforms": detected,
   265	            "output_directory": str(target_dir),
   266	            "planned_files": [str(p) for p in target_files.keys()],
   267	            "files": {str(p): data for p, data in target_files.items()},
   268	        }
   269	
   270	    # Write files atomically
   271	    target_dir.mkdir(parents=True, exist_ok=True)
   272	    written = []
   273	    for fpath, data in target_files.items():
   274	        fpath.write_text(json.dumps(data, indent=2) + "\n")
   275	        written.append(str(fpath))
   276	
   277	    return {
   278	        "detected_platforms": detected,
   279	        "output_directory": str(target_dir),
   280	        "written_files": written,
   281	    }
   282	
   283	
   284	def main() -> int:
   285	    parser = argparse.ArgumentParser(
   286	        description="Scaffold standardized quality check configurations for repository platforms."
   287	    )
   288	    parser.add_argument(
   289	        "--root",
   290	        type=Path,
   291	        default=Path("."),
   292	        help="Repository root directory to inspect (default: current directory).",
   293	    )
   294	    parser.add_argument(
   295	        "--output-dir",
   296	        type=Path,
   297	        default=None,
   298	        help="Target directory for quality configs (default: <root>/.agents/quality).",
   299	    )
   300	    parser.add_argument(
   301	        "--platform",
   302	        type=str,
   303	        default=None,
   304	        help="Comma-separated platform override (e.g. flutter,android,ios,rust).",
   305	    )
   306	    parser.add_argument(
   307	        "--force",
   308	        action="store_true",
   309	        help="Overwrite existing configuration files.",
   310	    )
   311	    parser.add_argument(
   312	        "--dry-run",
   313	        action="store_true",
   314	        help="Print planned scaffolding without writing files to disk.",
   315	    )
   316	
   317	    args = parser.parse_args()
   318	
   319	    platforms = None
   320	    if args.platform:
   321	        platforms = [p.strip().lower() for p in args.platform.split(",") if p.strip()]
   322	
   323	    try:
   324	        result = scaffold_quality_manifests(
   325	            repo_root=args.root,
   326	            output_dir=args.output_dir,
   327	            platforms=platforms,
   328	            force=args.force,
   329	            dry_run=args.dry_run,
   330	        )
   331	        print(f"Scaffolding completed successfully for platforms: {result['detected_platforms']}")
   332	        if args.dry_run:
   333	            print(f"Dry-run planned {len(result['planned_files'])} file(s):")
   334	            for f in result["planned_files"]:
   335	                print(f"  - {f}")
   336	        else:
   337	            print(f"Written {len(result['written_files'])} file(s) into {result['output_directory']}:")
   338	            for f in result["written_files"]:
   339	                print(f"  - {f}")
   340	        return 0
   341	    except ScaffoldError as err:
   342	        print(f"Scaffolding error: {err}", file=sys.stderr)
   343	        return 1
   344	
   345	
   346	if __name__ == "__main__":
   347	    sys.exit(main())
     1	#!/usr/bin/env bash
     2	# Pre-release checks for the agent kit. Run before publishing — a broken skill
     3	# propagates to every project on every machine that has the plugin installed.
     4	set -uo pipefail
     5	
     6	KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
     7	cd "$KIT_DIR"
     8	FAILED=0
     9	note() { printf '%s\n' "$1"; }
    10	fail() { printf '  FAIL %s\n' "$1"; FAILED=1; }
    11	
    12	note "== 1. JSON manifests parse =="
    13	for f in plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json .claude-plugin/marketplace.json .agents/plugins/marketplace.json; do
    14	  if python3 -c "import json,sys;json.load(open('$f'))" 2>/dev/null; then
    15	    note "  ok   $f"
    16	  else
    17	    fail "$f is not valid JSON"
    18	  fi
    19	done
    20	
    21	note "== 1b. Runtime versions and Codex marketplace agree =="
    22	python3 - <<'PY' || FAILED=1
    23	import json, pathlib, re, sys
    24	try:
    25	    manifests = [json.loads(pathlib.Path(p).read_text()) for p in
    26	                 ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json")]
    27	    claude = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text())
    28	    catalog = json.loads(pathlib.Path(".agents/plugins/marketplace.json").read_text())
    29	    entry, = [p for p in catalog["plugins"] if p["name"] == "d3nexus"]
    30	    claude_entry, = [p for p in claude["plugins"] if p["name"] == "d3nexus"]
    31	    versions = {m["version"] for m in manifests} | {claude_entry["version"]}
    32	    assert all(m["name"] == "d3nexus" for m in manifests), "plugin names must agree"
    33	    assert len(versions) == 1, f"release versions differ: {sorted(versions)}"
    34	    version, = versions
    35	    assert re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version), "invalid release version"
    36	    assert re.search(r'^## ' + re.escape(version) + r' — \d{4}-\d{2}-\d{2}\n\n\S',
    37	                     pathlib.Path("CHANGELOG.md").read_text(), re.M), "missing dated release notes"
    38	    assert catalog["name"] == claude["name"] == "danhdue-agent-tools", "marketplace names differ"
    39	    assert entry["source"] == {"source": "local", "path": "./"}, "marketplace must load the repo root"
    40	    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "invalid policy"
    41	    assert entry["category"] == "Developer Tools", "missing marketplace category"
    42	    codex = manifests[2]
    43	    assert codex["skills"] == "./skills/" and pathlib.Path(codex["skills"]).is_dir(), "missing shared skills"
    44	    assert not ({"apps", "mcpServers", "hooks"} & codex.keys()), "unexpected Codex components"
    45	    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
    46	        assert codex["interface"][field].strip(), f"missing Codex interface.{field}"
    47	    print(f"  ok   d3nexus {version}, shared skills, and repo marketplace")
    48	except (AssertionError, KeyError, ValueError, OSError, TypeError) as error:
    49	    print(f"  FAIL {error}")
    50	    sys.exit(1)
    51	PY
    52	
    53	note "== 2. Skill frontmatter is exactly name + description =="
    54	python3 - <<'PY' || FAILED=1
    55	import pathlib, re, sys
    56	bad = 0
    57	for p in sorted(pathlib.Path("skills").glob("*/SKILL.md")):
    58	    text = p.read_text()
    59	    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    60	    if not m:
    61	        print(f"  FAIL {p}: missing YAML frontmatter"); bad = 1; continue
    62	    keys = re.findall(r'^([A-Za-z_][\w-]*):', m.group(1), re.M)
    63	    if set(keys) != {"name", "description"}:
    64	        print(f"  FAIL {p}: frontmatter keys {keys} (expected exactly name, description)")
    65	        bad = 1
    66	    else:
    67	        name = re.search(r'^name:\s*(.+)$', m.group(1), re.M).group(1).strip().strip('"\'')
    68	        if name != p.parent.name:
    69	            print(f"  WARN {p}: name '{name}' differs from directory '{p.parent.name}'")
    70	print(f"  checked {len(list(pathlib.Path('skills').glob('*/SKILL.md')))} skills")
    71	sys.exit(bad)
    72	PY
    73	
    74	note "== 3. Relative links resolve =="
    75	python3 - <<'PY' || FAILED=1
    76	import pathlib, re, sys
    77	bad = 0
    78	targets = list(pathlib.Path("skills").glob("*/SKILL.md")) \
    79	        + list(pathlib.Path("skills").glob("*/**/*.md")) \
    80	        + list(pathlib.Path("rules").glob("*.md")) \
    81	        + [pathlib.Path("README.md"), pathlib.Path("CLAUDE.md"), pathlib.Path("CHANGELOG.md")]
    82	targets = sorted(set(targets))
    83	def strip_fences(s):
    84	    # Link syntax also occurs inside code samples and inline code spans that document
    85	    # a format. Only links in prose are real links.
    86	    s = re.sub(r'```.*?```', '', s, flags=re.S)
    87	    return re.sub(r'`[^`\n]*`', '', s)
    88	
    89	for p in targets:
    90	    if not p.exists():
    91	        continue
    92	    for link in re.findall(r'\]\(([^)#][^)]*)\)', strip_fences(p.read_text())):
    93	        if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
    94	            continue  # external, or an illustrative placeholder
    95	        if not (p.parent / link.split('#')[0]).exists():
    96	            print(f"  FAIL {p} -> {link}"); bad = 1
    97	print(f"  checked {len(targets)} files")
    98	sys.exit(bad)
    99	PY
   100	
   101	note "== 4. ToC anchors match headings =="
   102	python3 - <<'PY' || FAILED=1
   103	import pathlib, re, sys
   104	def anchor(h):
   105	    h = h.lower(); h = re.sub(r'[^\w\s-]', '', h); return '#' + h.replace(' ', '-')
   106	bad = 0
   107	for p in sorted(pathlib.Path("skills").glob("*/SKILL.md")) + [pathlib.Path("README.md")]:
   108	    s = p.read_text(); fence = False; heads = []
   109	    for ln in s.split("\n"):
   110	        if ln.startswith("```"): fence = not fence; continue
   111	        if not fence and re.match(r'^#{2,6} ', ln):
   112	            heads.append(anchor(re.sub(r'^#+ ', '', ln).rstrip()))
   113	    for link in re.findall(r'\]\((#[^)]+)\)', s):
   114	        if link.lower() not in heads:
   115	            print(f"  FAIL {p} -> {link}"); bad = 1
   116	sys.exit(bad)
   117	PY
   118	
   119	note "== 5. No stale cross-namespace references =="
   120	if grep -rq "superpowers:" skills rules 2>/dev/null; then
   121	  grep -rn "superpowers:" skills rules | head -5
   122	  fail "skills still reference the superpowers namespace"
   123	else
   124	  note "  ok   none"
   125	fi
   126	
   127	note "== 5b. Rule files start with frontmatter =="
   128	# Antigravity rejects a rules/*.md without frontmatter outright:
   129	#   "Failed to parse plugin rule file ...: invalid frontmatter format"
   130	# and the rule then silently never loads.
   131	for f in rules/*.md; do
   132	  if head -1 "$f" | grep -qx -- '---'; then
   133	    note "  ok   $f"
   134	  else
   135	    fail "$f has no frontmatter — Antigravity will refuse to load it"
   136	  fi
   137	done
   138	
   139	note "== 6. Session-start hook emits valid JSON for both runtimes =="
   140	hook_case() {  # <label> <expect: inject|silent> <env> <payload>
   141	  local label="$1" expect="$2" env="$3" payload="$4" out
   142	  out=$(printf '%s' "$payload" | env $env bash hooks/session-start 2>/dev/null) || {
   143	    fail "hook exited non-zero: $label"; return; }
   144	  printf '%s' "$out" | python3 -c "
   145	import json,sys
   146	d=json.load(sys.stdin)
   147	got='inject' if ('hookSpecificOutput' in d or 'injectSteps' in d) else ('silent' if d=={} else 'other')
   148	sys.exit(0 if got=='$expect' else 1)
   149	" 2>/dev/null && note "  ok   $label" || fail "$label — expected $expect"
   150	}
   151	hook_case "Claude Code SessionStart"        inject "CLAUDE_PLUGIN_ROOT=$KIT_DIR" '{}'
   152	hook_case "Antigravity first invocation"    inject "X=1" '{"invocationNum":0}'
   153	hook_case "Antigravity second invocation"   silent "X=1" '{"invocationNum":1}'
   154	hook_case "Antigravity later invocation"    silent "X=1" '{"invocationNum":7}'
   155	hook_case "Antigravity unreadable payload"  silent "X=1" 'not json'
   156	
   157	note "== 7. Methodology skills stay faithful to their sources =="
   158	python3 scripts/check_source_fidelity.py || FAILED=1
   159	
   160	note "== 8. Every supporting skill file is referenced by something =="
   161	# skills/brainstorming/spec-document-reviewer-prompt.md was 49 lines of working reviewer prompt
   162	# that nothing in the repository referenced, for its entire life. Nothing prevented that from
   163	# recurring. SKILL.md is exempt: it is a skill's entry point by definition, and without the
   164	# exemption this check fires on every skill in the kit.
   165	python3 - <<'PY' || FAILED=1
   166	import pathlib, sys
   167	root = pathlib.Path(".")
   168	# The rule is that a skill's own content must be reachable from the skill. Three things are
   169	# not that content: binary assets, legal files, and the repo furniture a vendored skill brings
   170	# with it (CI workflows and other dotfile directories, which their own tooling invokes).
   171	ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
   172	LEGAL_PREFIXES = ("LICENSE", "COPYING", "NOTICE")
   173	def is_skill_content(p):
   174	    if p.name == "SKILL.md" or "__pycache__" in p.parts:
   175	        return False
   176	    if p.suffix.lower() in ASSET_SUFFIXES:
   177	        return False
   178	    if p.name.upper().startswith(LEGAL_PREFIXES):
   179	        return False
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
skills/quality_check/resources/schemas/check-quality.schema.json:7:    "schema_version",
skills/quality_check/resources/schemas/check-quality.schema.json:8:    "providers"
skills/quality_check/resources/schemas/check-quality.schema.json:11:    "schema_version": {
skills/quality_check/resources/schemas/check-quality.schema.json:15:    "providers": {
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:1:#!/usr/bin/env python3
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:4:Tests composite consumer repositories, multiple providers, Rust capability execution,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:59:        "source": "cargo test" if "rust" in provider_id else "gradle check",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:235:    reconciled = reconcile_results(reg_res["providers"], validated_results)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:238:    agg = aggregate_results(reg_res["providers"], reconciled["results"], inv)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:256:            "d3nexus:rust-quality-check",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:257:            "d3nexus:python-quality-check",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:272:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:273:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:275:                    "id": "rust-core",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:276:                    "skill": "d3nexus:rust-quality-check",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:293:        res_rust = _make_provider_result("rust-core", active_sha, "epic", "PASS")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:306:            [res_rust, res_mobile],
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:311:        self.assertIn("rust-core", pipeline_out["report"])
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:319:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:320:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:321:                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:330:        res_rust = _make_provider_result("rust-core", active_sha, "epic", "FAIL", check_status="FAIL")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:350:            [res_rust, res_mobile],
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:388:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:389:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:390:                {"id": "provider-b", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:420:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:421:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:422:                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:442:        res_rust = _make_provider_result("rust-core", initial_sha, "epic", "PASS")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:443:        pipeline_drift = execute_quality_pipeline(self.repo_path, inv, [res_rust], self.skills)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:457:        res_rust2 = _make_provider_result("rust-core", new_sha, "epic", "PASS")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:458:        pipeline_mutated = execute_quality_pipeline(self.repo_path, inv2, [res_rust2], self.skills)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:467:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:468:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:469:                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic"]},
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:477:        res_pr = _make_provider_result("rust-core", active_sha, profile="pr", status="PASS")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:493:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:494:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:542:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:543:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:591:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:592:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:636:    def test_polyglot_rust_android_flutter_passes_end_to_end(self) -> None:
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:640:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:641:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:642:                {"id": "rust-core", "skill": "d3nexus:rust-quality-check", "required": True, "profiles": ["epic", "pr"]},
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:652:        res_rust = _make_provider_result("rust-core", active_sha, "epic", "PASS", check_id="cargo-test")
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:663:        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_rust, res_android, res_flutter], self.skills)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:665:        self.assertIn("rust-core", pipeline_out["report"])
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:674:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:675:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:709:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:710:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:746:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:747:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:777:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:789:    def test_python_provider_passes_end_to_end(self) -> None:
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:793:            "schema_version": 1,
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:794:            "providers": [
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:796:                    "id": "python-core",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:797:                    "skill": "d3nexus:python-quality-check",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:808:        res_python = _make_provider_result(
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:809:            "python-core",
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:834:        pipeline_out = execute_quality_pipeline(self.repo_path, inv, [res_python], self.skills)
skills/quality_check/resources/scripts/test_quality_provider_acceptance.py:837:        self.assertIn("python-core", report)
     1	{
     2	  "name": "d3nexus",
     3	  "description": "Mobile engineering agent kit: epic lifecycle orchestration, 3-tier quality gates, and security/architecture/UI/code-health audits for Flutter, Android Native, and iOS Native.",
     4	  "version": "1.23.0",
     5	  "author": {
     6	    "name": "DanhDue ExOICTIF"
     7	  },
     8	  "homepage": "https://github.com/DanhDue/ai-agent-tools",
     9	  "repository": "https://github.com/DanhDue/ai-agent-tools",
    10	  "license": "MIT",
    11	  "keywords": [
    12	    "skills",
    13	    "flutter",
    14	    "android",
    15	    "ios",
    16	    "clean-architecture",
    17	    "mvi",
    18	    "tdd",
    19	    "quality-gate",
    20	    "fintech"
    21	  ]
    22	}
     1	{
     2	  "name": "danhdue-agent-tools",
     3	  "interface": {
     4	    "displayName": "DanhDue Agent Tools"
     5	  },
     6	  "plugins": [
     7	    {
     8	      "name": "d3nexus",
     9	      "source": {
    10	        "source": "local",
    11	        "path": "./"
    12	      },
    13	      "policy": {
    14	        "installation": "AVAILABLE",
    15	        "authentication": "ON_INSTALL"
    16	      },
    17	      "category": "Developer Tools"
    18	    }
    19	  ]
    20	}

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '1,280p'; nl -ba skills/dev-implementation/resources/scripts/check_bdd_traceability.py | sed -n '280,560p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Check that every epic BDD scenario is assigned to a task and covered by an integration test.
     3	
     4	Usage:
     5	  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
     6	  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
     7	                                  [--results <report file|dir|glob ...>]
     8	
     9	Exit codes: 0 all covered; 1 traceability failure; 2 usage error.
    10	"""
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import re
    15	import subprocess
    16	import sys
    17	from pathlib import Path
    18	
    19	from result_reports import ReportError, load_reports, reference_pattern, verdicts
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
   156	
   157	def check_tests(ids: list[str], selected: list[str], roots: list[Path],
   158	                check_stale: bool) -> tuple[dict[str, list[str]], list[str], list[str]]:
   159	    patterns = {identifier: reference_pattern(identifier) for identifier in selected}
   160	    coverage: dict[str, list[str]] = {identifier: [] for identifier in selected}
   161	    stale = stale_pattern(ids)
   162	    known = set(ids)
   163	    problems: list[str] = []
   164	    files, warnings = integration_files(roots)
   165	    for path in files:
   166	        try:
   167	            lines = path.read_text(encoding="utf-8").splitlines()
   168	        except UnicodeDecodeError:
   169	            continue
   170	        for number, line in enumerate(lines, start=1):
   171	            for identifier, pattern in patterns.items():
   172	                if pattern.search(line):
   173	                    coverage[identifier].append(f"{path}:{number}")
   174	            if check_stale:
   175	                problems.extend(f"{path}:{number}: stale reference {token}"
   176	                                for token in stale.findall(line) if token not in known)
   177	    return coverage, problems, warnings
   178	
   179	
   180	def split_values(values: list[str] | None) -> list[str]:
   181	    """Accept space- or comma-separated values, as copied from an HLD or Covers: line."""
   182	    return [item for value in values or [] for part in value.split(",") for item in part.split() if item]
   183	
   184	
   185	def report(coverage: dict[str, list[str]], problems: list[str], warnings: list[str]) -> int:
   186	    width = max((len(identifier) for identifier in coverage), default=0)
   187	    for identifier, places in coverage.items():
   188	        print(f"{identifier.ljust(width)}    {', '.join(places) if places else '(none)'}")
   189	    for warning in warnings:
   190	        print(warning, file=sys.stderr)
   191	    for problem in problems:
   192	        print(problem)
   193	    covered = sum(1 for places in coverage.values() if places)
   194	    failed = bool(problems) or covered < len(coverage)
   195	    print(f"Result: {covered}/{len(coverage)} covered — {'FAIL' if failed else 'PASS'}")
   196	    return 1 if failed else 0
   197	
   198	
   199	def report_results(ids: list[str], selected: list[str], roots: list[Path], results: list[str],
   200	                   check_stale: bool, unknown: list[str]) -> int:
   201	    """Coverage proven by test results: each selected identifier needs a passed case."""
   202	    cases = load_reports(results, Path.cwd())
   203	    _, problems, warnings = check_tests(ids, [], roots, check_stale)
   204	    if check_stale:
   205	        stale, known = stale_pattern(ids), set(ids)
   206	        problems.extend(f"{case.name}: stale reference {token}" for case in cases
   207	                        for token in stale.findall(f"{case.name} {case.classname}") if token not in known)
   208	    judged = verdicts(selected, cases)
   209	    width = max((len(identifier) for identifier in judged), default=0)
   210	    for identifier, (passed, detail) in judged.items():
   211	        print(f"{identifier.ljust(width)}    {'PASS' if passed else 'FAIL'} {detail}")
   212	    for warning in warnings:
   213	        print(warning, file=sys.stderr)
   214	    problems = unknown + problems
   215	    for problem in problems:
   216	        print(problem)
   217	    covered = sum(1 for passed, _ in judged.values() if passed)
   218	    failed = bool(problems) or covered < len(judged)
   219	    print(f"Result: {covered}/{len(judged)} covered — {'FAIL' if failed else 'PASS'}")
   220	    return 1 if failed else 0
   221	
   222	
   223	def main(argv: list[str] | None = None) -> int:
   224	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
   225	    modes = parser.add_subparsers(dest="mode", required=True)
   226	    plan = modes.add_parser("plan", help="every scenario is assigned to exactly one task")
   227	    plan.add_argument("--scenarios", required=True, type=Path)
   228	    plan.add_argument("--tasks", required=True, nargs="+", type=Path)
   229	    tests = modes.add_parser("tests", help="every scenario has at least one integration test")
   230	    tests.add_argument("--scenarios", required=True, type=Path)
   231	    tests.add_argument("--roots", required=True, nargs="+")
   232	    tests.add_argument("--ids", nargs="+")
   233	    tests.add_argument("--results", nargs="+")
   234	    args = parser.parse_args(argv)
   235	    try:
   236	        ids, problems = load_scenarios(args.scenarios)
   237	        if problems:
   238	            print("\n".join(problems))
   239	            print("Result: scenario document invalid — FAIL")
   240	            return 1
   241	        if args.mode == "plan":
   242	            coverage, problems = check_plan(ids, args.tasks)
   243	            return report(coverage, problems, [])
   244	        roots = [Path(value) for value in split_values(args.roots)]
   245	        selected = split_values(args.ids) or ids
   246	        unknown = [f"--ids names unknown identifier {identifier}"
   247	                   for identifier in selected if identifier not in ids]
   248	        known_selected = [identifier for identifier in selected if identifier in ids]
   249	        if args.results:
   250	            return report_results(ids, known_selected, roots, split_values(args.results),
   251	                                  not args.ids, unknown)
   252	        coverage, problems, warnings = check_tests(ids, known_selected, roots, not args.ids)
   253	        return report(coverage, unknown + problems, warnings)
   254	    except (UsageError, ReportError) as error:
   255	        print(f"error: {error}", file=sys.stderr)
   256	        return 2
   257	
   258	
   259	if __name__ == "__main__":
   260	    sys.exit(main())

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/result_reports.py | sed -n '1,280p'; rg -n 'def |except|traceability|mock|check_done' skills/dev-implementation/resources/scripts/run_task_checks.py skills/dev-implementation/resources/scripts/sync_task_status.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Read JUnit XML and Dart JSON test reports, and decide which identifiers they prove.
     3	
     4	Imported by check_bdd_traceability.py and run_task_checks.py; it has no command line.
     5	"""
     6	from __future__ import annotations
     7	
     8	import glob
     9	import json
    10	import re
    11	import xml.etree.ElementTree as ET
    12	from dataclasses import dataclass
    13	from pathlib import Path
    14	
    15	
    16	class ReportError(Exception):
    17	    """A report path that is missing, or a file in neither format."""
    18	
    19	
    20	@dataclass(frozen=True)
    21	class Case:
    22	    name: str
    23	    classname: str
    24	    status: str  # "passed", "failed" or "skipped"
    25	
    26	
    27	def reference_pattern(identifier: str) -> re.Pattern[str]:
    28	    """Match an identifier in any case, with - and _ interchangeable, not inside a longer token."""
    29	    body = "[-_]".join(re.escape(part) for part in identifier.split("-"))
    30	    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)
    31	
    32	
    33	def parse_junit(text: str) -> list[Case]:
    34	    cases = []
    35	    for element in ET.fromstring(text).iter("testcase"):
    36	        tags = {child.tag for child in element}
    37	        status = "failed" if tags & {"failure", "error"} else "skipped" if "skipped" in tags else "passed"
    38	        cases.append(Case(element.get("name", ""), element.get("classname", ""), status))
    39	    return cases
    40	
    41	
    42	def parse_dart(text: str) -> list[Case]:
    43	    names: dict[object, str] = {}
    44	    cases = []
    45	    for line in text.splitlines():
    46	        if not line.strip():
    47	            continue
    48	        try:
    49	            event = json.loads(line)
    50	        except Exception:
    51	            continue
    52	        if isinstance(event, list):
    53	            if event and isinstance(event[0], dict):
    54	                event = event[0]
    55	            else:
    56	                continue
    57	        if not isinstance(event, dict):
    58	            continue
    59	        if event.get("type") == "testStart":
    60	            names[event["test"]["id"]] = event["test"]["name"]
    61	        elif event.get("type") == "testDone" and event.get("testID") in names:
    62	            name = names.pop(event["testID"])
    63	            if event.get("hidden"):
    64	                continue
    65	            status = ("skipped" if event.get("skipped")
    66	                      else "passed" if event.get("result") == "success" else "failed")
    67	            cases.append(Case(name, "", status))
    68	    return cases
    69	
    70	
    71	def report_files(path: str, root: Path) -> list[Path]:
    72	    target = root / path
    73	    if target.is_dir():
    74	        return sorted(p for pattern in ("*.xml", "*.json") for p in target.rglob(pattern))
    75	    if target.is_file():
    76	        return [target]
    77	    matches = sorted(Path(match) for match in glob.glob(str(target), recursive=True))
    78	    if not matches:
    79	        raise ReportError(f"results path not found: {path}")
    80	    return [p for match in matches for p in report_files(str(match), root)]
    81	
    82	
    83	def load_files(files: list[Path]) -> list[Case]:
    84	    cases: list[Case] = []
    85	    for file in files:
    86	        text = file.read_text(encoding="utf-8", errors="replace")
    87	        lead = text.lstrip()[:1]
    88	        try:
    89	            if lead == "<":
    90	                cases.extend(parse_junit(text))
    91	            elif lead == "{" or any(line.startswith("{") for line in text.splitlines()):
    92	                cases.extend(parse_dart(text))
    93	            else:
    94	                raise ReportError(f"{file} is neither JUnit XML nor Dart JSON")
    95	        except (ET.ParseError, ValueError, KeyError) as error:
    96	            raise ReportError(f"{file} is not a valid report: {error}") from None
    97	    return cases
    98	
    99	
   100	def load_reports(paths: list[str], root: Path) -> list[Case]:
   101	    return load_files([file for path in paths for file in report_files(path, root)])
   102	
   103	
   104	def belongs(case: Case, identifier: str) -> bool:
   105	    pattern = reference_pattern(identifier)
   106	    return bool(pattern.search(case.name) or pattern.search(case.classname))
   107	
   108	
   109	def verdicts(ids: list[str], cases: list[Case]) -> dict[str, tuple[bool, str]]:
   110	    result: dict[str, tuple[bool, str]] = {}
   111	    for identifier in ids:
   112	        own = [case for case in cases if belongs(case, identifier)]
   113	        failed = next((c for c in own if c.status == "failed"), None)
   114	        passed = next((c for c in own if c.status == "passed"), None)
   115	        if failed:
   116	            result[identifier] = (False, f"failed in {failed.name}")
   117	        elif passed:
   118	            result[identifier] = (True, passed.name)
   119	        elif own:
   120	            result[identifier] = (False, "skipped")
   121	        else:
   122	            result[identifier] = (False, "no test case in results")
   123	    return result
   124	
   125	
   126	def digest(cases: list[Case], ids: list[str]) -> dict:
   127	    own = [case for case in cases if any(belongs(case, identifier) for identifier in ids)]
   128	    totals = {status: sum(1 for c in own if c.status == status) for status in ("passed", "failed", "skipped")}
   129	    return {"totals": totals,
   130	            "cases": [{"name": c.name, "classname": c.classname, "status": c.status} for c in own]}
skills/dev-implementation/resources/scripts/run_task_checks.py:29:except ImportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:60:_cbt: Any = importlib.import_module("check_bdd_traceability")
skills/dev-implementation/resources/scripts/run_task_checks.py:83:def is_pytest_command(command: str) -> bool:
skills/dev-implementation/resources/scripts/run_task_checks.py:88:    except ValueError:
skills/dev-implementation/resources/scripts/run_task_checks.py:119:def validate_pytest_red(command: str, exit_code: int | None, output_text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:137:def parse_covers(text: str) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:146:def core_sections(text: str) -> tuple[str | None, str | None, str | None, list[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:155:def check_task_tamper(task_path: Path | str, layout: EpicLayout) -> None:
skills/dev-implementation/resources/scripts/run_task_checks.py:184:def utc_now() -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:188:def fresh_reports(path: str, root: Path, since: float) -> list[Path]:
skills/dev-implementation/resources/scripts/run_task_checks.py:192:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:197:def run_command(command: str, root: Path, timeout: int) -> tuple[int | None, bytes]:
skills/dev-implementation/resources/scripts/run_task_checks.py:204:    except subprocess.TimeoutExpired:
skills/dev-implementation/resources/scripts/run_task_checks.py:210:def mismatch(row: Row, code: int, text: str) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:220:def epic_scenario_ids(layout: EpicLayout) -> list[str]:
skills/dev-implementation/resources/scripts/run_task_checks.py:223:    except UsageError:
skills/dev-implementation/resources/scripts/run_task_checks.py:227:def attach_digest(results: dict[str, Any], files: list[Path], scenario_ids: list[str]) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:231:    except ReportError:
skills/dev-implementation/resources/scripts/run_task_checks.py:236:def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:277:def committed_text(root: Path, path: Path) -> str | None:
skills/dev-implementation/resources/scripts/run_task_checks.py:283:    except (ContractError, ValueError):
skills/dev-implementation/resources/scripts/run_task_checks.py:287:def protected_patterns(layout: EpicLayout, root: Path) -> tuple[list[str], set[str]]:
skills/dev-implementation/resources/scripts/run_task_checks.py:298:        except ContractError:
skills/dev-implementation/resources/scripts/run_task_checks.py:304:def scope_row(layout: EpicLayout, allowed_patterns: list[str]) -> dict[str, Any]:
skills/dev-implementation/resources/scripts/run_task_checks.py:323:def detail_of(record: dict[str, Any]) -> str:
skills/dev-implementation/resources/scripts/run_task_checks.py:329:def run(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:360:def status(args: argparse.Namespace) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:374:def main(argv: list[str] | None = None) -> int:
skills/dev-implementation/resources/scripts/run_task_checks.py:384:    except ContractError as error:
skills/dev-implementation/resources/scripts/sync_task_status.py:32:except ImportError:
skills/dev-implementation/resources/scripts/sync_task_status.py:43:def now_iso() -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:48:def set_frontmatter_field(text: str, key: str, value: str | None) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:75:def parse_worktree_list(output: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:86:def parse_worktree_branches(output: str) -> list[tuple[Path, str | None]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:112:def checkout_roots() -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:123:def epic_checkout_roots(epic_dir: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:153:def task_targets(root: Path, task_id: str) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:163:def epic_of(path: Path) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:168:def expected_epic(roots: list[Path], task_id: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:187:def sync_task(roots: list[Path], task_id: str, new_status: str) -> tuple[list[Path], list[str]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:216:def board_location(root: Path, path: Path, status: str) -> Path:
skills/dev-implementation/resources/scripts/sync_task_status.py:233:def board_tally(roots: list[Path], epic_slug: str) -> dict[str, int]:
skills/dev-implementation/resources/scripts/sync_task_status.py:259:def find_epic_slug(root: Path, epic_dir: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:279:def find_epic_dir_for_slug(root: Path, epic_slug: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:298:def fix_task_markdown_links(text: str, epic_dir: str) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:305:def fix_epic_overview_links(text: str) -> str:
skills/dev-implementation/resources/scripts/sync_task_status.py:310:def archive_superpowers_docs(root: Path, epic_dir: str, epic_slug: str | None) -> list[Path]:
skills/dev-implementation/resources/scripts/sync_task_status.py:341:def archive_epic_tasks(roots: list[Path], epic_dir: str) -> tuple[list[Path], list[Path]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:404:def sync_epic(roots: list[Path], epic_dir: str, new_status: str) -> tuple[list[Path], list[Path]]:
skills/dev-implementation/resources/scripts/sync_task_status.py:434:def archive_all_done_epics(roots: list[Path]) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:459:def code_epic_dir(root: Path, task_id: str) -> str | None:
skills/dev-implementation/resources/scripts/sync_task_status.py:473:def done_gate_failures(task_id: str) -> list[str]:
skills/dev-implementation/resources/scripts/sync_task_status.py:493:    except ContractError as error:
skills/dev-implementation/resources/scripts/sync_task_status.py:497:def main() -> None:

exec
/bin/zsh -lc "nl -ba skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py | sed -n '1,285p'; nl -ba skills/setup_quality_check/SKILL.md | sed -n '1,165p'; nl -ba skills/dev-implementation/SKILL.md | sed -n '256,320p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""
     3	Automated Scaffolding Engine for Quality Providers.
     4	Inspects project repository roots, detects project platforms (Flutter, Android, iOS, Rust),
     5	and generates standardized .agents/quality/ configurations adhering to canonical templates.
     6	"""
     7	from __future__ import annotations
     8	
     9	import argparse
    10	import json
    11	import sys
    12	from pathlib import Path
    13	from typing import Dict, List, Optional, Any
    14	
    15	
    16	class ScaffoldError(Exception):
    17	    """Raised when scaffolding fails due to safety or detection violations."""
    18	    pass
    19	
    20	
    21	PLATFORM_CONFIGS: Dict[str, Dict[str, Any]] = {
    22	    "flutter": {
    23	        "provider_id": "flutter-core",
    24	        "skill": "d3nexus:flutter-quality-check",
    25	        "filename": "flutter-quality.json",
    26	        "manifest": {
    27	            "schema_version": 1,
    28	            "capabilities": {
    29	                "format": ["./scripts/dartfmt.sh"],
    30	                "analyze": ["fvm", "flutter", "analyze"],
    31	                "boundaries": ["./scripts/check_module_boundaries.sh"],
    32	                "license": ["./scripts/check_license_header.sh"],
    33	                "test": ["melos", "run", "test"],
    34	                "coverage": {
    35	                    "command": ["./scripts/testWithCoverage.sh"],
    36	                    "lcov_path": "coverage_report/lcov.info",
    37	                    "threshold": 0.85
    38	                },
    39	                "acceptance": ["./scripts/acceptance_check.sh"]
    40	            },
    41	            "profiles": {
    42	                "pr": ["format", "analyze", "test"],
    43	                "epic": ["format", "analyze", "boundaries", "license", "test", "coverage"]
    44	            }
    45	        }
    46	    },
    47	    "android": {
    48	        "provider_id": "android-core",
    49	        "skill": "d3nexus:android-quality-check",
    50	        "filename": "android-quality.json",
    51	        "manifest": {
    52	            "schema_version": 1,
    53	            "capabilities": {
    54	                "format": ["./gradlew", "spotlessCheck"],
    55	                "lint": ["./gradlew", "detekt"],
    56	                "bcv": ["./gradlew", "apiCheck"],
    57	                "architecture": ["./gradlew", ":konsist-test:test"],
    58	                "test": ["./gradlew", "testDebugUnitTest"],
    59	                "coverage": {
    60	                    "command": ["./gradlew", "jacocoTestReport"],
    61	                    "report_path": "build/reports/jacoco/jacocoTestReport/jacocoTestReport.xml",
    62	                    "threshold": 0.85
    63	                },
    64	                "acceptance": ["./scripts/acceptance_check.sh"],
    65	                "cleanup": ["pkill", "-9", "java"]
    66	            },
    67	            "profiles": {
    68	                "pr": ["format", "lint", "test"],
    69	                "epic": ["format", "lint", "bcv", "architecture", "test", "coverage", "cleanup"]
    70	            }
    71	        }
    72	    },
    73	    "ios": {
    74	        "provider_id": "ios-core",
    75	        "skill": "d3nexus:ios-quality-check",
    76	        "filename": "ios-quality.json",
    77	        "manifest": {
    78	            "schema_version": 1,
    79	            "capabilities": {
    80	                "format": ["swiftformat", "--config", "quality/.swiftformat", "--lint", "."],
    81	                "lint": ["swiftlint", "lint", "--config", "quality/.swiftlint.yml", "--strict"],
    82	                "architecture": ["swift", "test", "--package-path", "ArchTests"],
    83	                "boundaries": ["./scripts/check_module_boundaries.sh"],
    84	                "test": ["swift", "test"],
    85	                "coverage": {
    86	                    "command": ["./scripts/check_coverage_thresholds.sh"],
    87	                    "profdata_path": "default.profdata",
    88	                    "threshold": 0.85
    89	                },
    90	                "acceptance": ["./scripts/acceptance_check.sh"]
    91	            },
    92	            "profiles": {
    93	                "pr": ["format", "lint", "test"],
    94	                "epic": ["format", "lint", "architecture", "boundaries", "test", "coverage"]
    95	            }
    96	        }
    97	    },
    98	    "rust": {
    99	        "provider_id": "rust-core",
   100	        "skill": "d3nexus:rust-quality-check",
   101	        "filename": "rust-quality.json",
   102	        "manifest": {
   103	            "schema_version": 1,
   104	            "capabilities": {
   105	                "format": ["cargo", "fmt", "--all", "--", "--check"],
   106	                "check": ["cargo", "check", "--all-targets"],
   107	                "clippy": ["cargo", "clippy", "--all-targets", "--", "-D", "warnings"],
   108	                "test": ["cargo", "test", "--workspace"],
   109	                "coverage": {
   110	                    "command": ["cargo", "llvm-cov", "--workspace", "--fail-under-lines", "80"],
   111	                    "threshold": 0.8
   112	                },
   113	                "architecture": ["cargo", "run", "-p", "xtask", "--", "check-architecture"]
   114	            },
   115	            "profiles": {
   116	                "pr": ["format", "check", "clippy", "test", "architecture"],
   117	                "epic": ["format", "check", "clippy", "test", "coverage", "architecture"]
   118	            }
   119	        }
   120	    },
   121	    "python": {
   122	        "provider_id": "python-core",
   123	        "skill": "d3nexus:python-quality-check",
   124	        "filename": "python-quality.json",
   125	        "manifest": {
   126	            "schema_version": 1,
   127	            "capabilities": {
   128	                "format": ["uv", "run", "ruff", "format", "--check", "."],
   129	                "lint": ["uv", "run", "ruff", "check", "."],
   130	                "type_check": ["uv", "run", "mypy", "--strict", "src"],
   131	                "test": ["uv", "run", "pytest", "-m", "not slow and not acceptance and not live_llm"],
   132	                "coverage": {
   133	                    "command": ["uv", "run", "pytest", "--cov=src", "--cov-report=json:coverage.json"],
   134	                    "threshold": 0.8
   135	                },
   136	                "architecture": ["uv", "run", "lint-imports"]
   137	            },
   138	            "profiles": {
   139	                "pr": ["format", "lint", "type_check", "test"],
   140	                "epic": ["format", "lint", "type_check", "test", "coverage", "architecture"]
   141	            }
   142	        }
   143	    }
   144	}
   145	
   146	
   147	def detect_platforms(repo_root: Path) -> List[str]:
   148	    """
   149	    Inspects repository root directory and returns detected platform names.
   150	    Supports Flutter, Android, iOS, Rust, and Python heuristics.
   151	    """
   152	    detected = []
   153	
   154	    # Flutter detection
   155	    if (repo_root / "pubspec.yaml").is_file() or (repo_root / "melos.yaml").is_file():
   156	        detected.append("flutter")
   157	
   158	    # Android detection
   159	    android_markers = [
   160	        "build.gradle.kts",
   161	        "build.gradle",
   162	        "settings.gradle.kts",
   163	        "settings.gradle",
   164	    ]
   165	    if any((repo_root / marker).is_file() for marker in android_markers):
   166	        detected.append("android")
   167	
   168	    # iOS detection
   169	    ios_markers = [
   170	        "Project.swift",
   171	        "Tuist.swift",
   172	        "Package.swift",
   173	    ]
   174	    if any((repo_root / marker).is_file() for marker in ios_markers):
   175	        detected.append("ios")
   176	
   177	    # Rust detection
   178	    if (repo_root / "Cargo.toml").is_file():
   179	        detected.append("rust")
   180	
   181	    # Python detection
   182	    python_markers = [
   183	        "pyproject.toml",
   184	        "uv.lock",
   185	        "requirements.txt",
   186	        "setup.py",
   187	        "Pipfile",
   188	    ]
   189	    if any((repo_root / marker).is_file() for marker in python_markers):
   190	        detected.append("python")
   191	
   192	    return sorted(list(set(detected)))
   193	
   194	
   195	def build_registry_data(platforms: List[str]) -> Dict[str, Any]:
   196	    """Builds standard check_quality.json structure for given platforms."""
   197	    providers = []
   198	    for p in platforms:
   199	        cfg = PLATFORM_CONFIGS[p]
   200	        providers.append({
   201	            "id": cfg["provider_id"],
   202	            "skill": cfg["skill"],
   203	            "required": True,
   204	            "profiles": ["pr", "epic"]
   205	        })
   206	
   207	    return {
   208	        "schema_version": 1,
   209	        "providers": providers
   210	    }
   211	
   212	
   213	def scaffold_quality_manifests(
   214	    repo_root: Path,
   215	    output_dir: Optional[Path] = None,
   216	    platforms: Optional[List[str]] = None,
   217	    force: bool = False,
   218	    dry_run: bool = False,
   219	) -> Dict[str, Any]:
   220	    """
   221	    Scaffolds quality check registry and provider manifests into output_dir.
   222	    Raises ScaffoldError on detection failures or overwrite conflicts.
   223	    """
   224	    repo_root = repo_root.resolve()
   225	    if output_dir is None:
   226	        target_dir = repo_root / ".agents" / "quality"
   227	    else:
   228	        target_dir = output_dir.resolve()
   229	
   230	    if platforms is None:
   231	        detected = detect_platforms(repo_root)
   232	    else:
   233	        detected = sorted(list(set(platforms)))
   234	        for p in detected:
   235	            if p not in PLATFORM_CONFIGS:
   236	                raise ScaffoldError(f"Unsupported platform specified: '{p}'. Allowed: {list(PLATFORM_CONFIGS.keys())}")
   237	
   238	    if not detected:
   239	        raise ScaffoldError(
   240	            f"No supported platform detected in repository root: {repo_root}. "
   241	            f"Supported platforms: {list(PLATFORM_CONFIGS.keys())}"
   242	        )
   243	
   244	    # Prepare file mappings
   245	    target_files: Dict[Path, Dict[str, Any]] = {}
   246	    reg_path = target_dir / "check_quality.json"
   247	    target_files[reg_path] = build_registry_data(detected)
   248	
   249	    for p in detected:
   250	        cfg = PLATFORM_CONFIGS[p]
   251	        p_path = target_dir / cfg["filename"]
   252	        target_files[p_path] = cfg["manifest"]
   253	
   254	    # Check for existing files if not force
   255	    if not force:
   256	        for fpath in target_files:
   257	            if fpath.exists():
   258	                raise ScaffoldError(
   259	                    f"Configuration file already exists: {fpath}. Use --force to overwrite."
   260	                )
   261	
   262	    if dry_run:
   263	        return {
   264	            "detected_platforms": detected,
   265	            "output_directory": str(target_dir),
   266	            "planned_files": [str(p) for p in target_files.keys()],
   267	            "files": {str(p): data for p, data in target_files.items()},
   268	        }
   269	
   270	    # Write files atomically
   271	    target_dir.mkdir(parents=True, exist_ok=True)
   272	    written = []
   273	    for fpath, data in target_files.items():
   274	        fpath.write_text(json.dumps(data, indent=2) + "\n")
   275	        written.append(str(fpath))
   276	
   277	    return {
   278	        "detected_platforms": detected,
   279	        "output_directory": str(target_dir),
   280	        "written_files": written,
   281	    }
   282	
   283	
   284	def main() -> int:
   285	    parser = argparse.ArgumentParser(
     1	---
     2	name: setup_quality_check
     3	description: Inspects repository structure, auto-detects platforms (Flutter, Android, iOS, Rust, or Polyglot), and scaffolds standardized quality provider configurations adhering to canonical templates.
     4	---
     5	
     6	# Setup Quality Check
     7	
     8	Automated onboarding skill that bootstraps the d3nexus quality governance system for both Greenfield
     9	(new projects) and Brownfield (legacy repositories before active maintenance or AI agent code generation).
    10	
    11	## Overview
    12	
    13	The quality governance model requires deterministic, SHA-bound quality verification before any feature branch
    14	or PR is merged. Setting up quality checking ensures that:
    15	- Every platform present in the repository is discovered and registered in `.agents/quality/check_quality.json`.
    16	- Platform-specific quality manifests (`flutter-quality.json`, `android-quality.json`, `ios-quality.json`, `rust-quality.json`, `python-quality.json`) are populated with canonical, production-tested verification toolchains.
    17	- Code generation agents and developers are constrained by automated quality gates from day one.
    18	
    19	## Platform Detection Heuristics
    20	
    21	The scaffolding engine inspects repository roots against the following marker files:
    22	
    23	| Platform | Markers Detected | Provider ID | Target Manifest | Canonical Toolchain |
    24	|---|---|---|---|---|
    25	| **Flutter** | `pubspec.yaml`, `melos.yaml` | `flutter-core` | `flutter-quality.json` | `dartfmt.sh`, `fvm flutter analyze`, `check_module_boundaries.sh`, `check_license_header.sh`, `melos run test`, `testWithCoverage.sh` |
    26	| **Android** | `build.gradle.kts`, `build.gradle`, `settings.gradle.kts`, `settings.gradle` | `android-core` | `android-quality.json` | `spotlessCheck`, `detekt`, `apiCheck`, `:konsist-test:test`, `testDebugUnitTest`, `jacocoTestReport`, `pkill -9 java` |
    27	| **iOS** | `Project.swift`, `Tuist.swift`, `Package.swift` | `ios-core` | `ios-quality.json` | `swiftformat`, `swiftlint`, `ArchTests` (K1-K10), `check_module_boundaries.sh`, `swift test`, `check_coverage_thresholds.sh` |
    28	| **Rust** | `Cargo.toml` | `rust-core` | `rust-quality.json` | `cargo fmt`, `cargo check`, `cargo clippy`, `cargo test`, `cargo llvm-cov`, `xtask check-architecture` |
    29	| **Python** | `pyproject.toml`, `uv.lock`, `requirements.txt`, `setup.py`, `Pipfile` | `python-core` | `python-quality.json` | `ruff format`, `ruff check`, `mypy --strict`, `pytest`, `pytest-cov`, `lint-imports` |
    30	
    31	In composite repositories (e.g. Flutter mobile host with Rust core, or native Android/iOS bridging modules), all detected platforms are registered in `.agents/quality/check_quality.json`.
    32	
    33	## Operational Workflow
    34	
    35	### Step 1: Dry-Run Inspection
    36	
    37	Inspect what platforms the tool detects and what files will be created:
    38	
    39	```bash
    40	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --dry-run
    41	```
    42	
    43	### Step 2: Scaffold Configuration Files
    44	
    45	Execute scaffolding to generate the `.agents/quality/` directory:
    46	
    47	```bash
    48	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py
    49	```
    50	
    51	If configurations already exist and you want to reset them to canonical defaults:
    52	
    53	```bash
    54	python3 skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py --force
    55	```
    56	
    57	### Step 3: Run Baseline Quality Verification
    58	
    59	Run an initial check to certify that the repository passes the baseline PR profile:
    60	
    61	```bash
    62	# Invoke quality_check skill
    63	python3 skills/quality_check/resources/scripts/validate_quality_contract.py .agents/quality/check_quality.json
    64	```
    65	
    66	## CLI Reference
    67	
    68	`scaffold_quality_manifest.py` accepts the following arguments:
    69	
    70	- `--root <DIR>`: Path to the target repository root (default: current directory `.`).
    71	- `--output-dir <DIR>`: Explicit output directory for generated manifests (default: `<root>/.agents/quality`).
    72	- `--platform <LIST>`: Override automatic detection with comma-separated platforms (`flutter`, `android`, `ios`, `rust`, `python`).
    73	- `--force`: Overwrite existing quality manifests (fails safely by default to prevent accidental overwrite).
    74	- `--dry-run`: Display detected platforms and planned file list without writing to disk.
    75	
    76	## Related Skills
    77	
    78	- [Quality Check](../quality_check/SKILL.md)
    79	- [Flutter Quality Check](../flutter-quality-check/SKILL.md)
    80	- [Android Quality Check](../android-quality-check/SKILL.md)
    81	- [iOS Quality Check](../ios-quality-check/SKILL.md)
    82	- [Rust Quality Check](../rust-quality-check/SKILL.md)
    83	- [Python Quality Check](../python-quality-check/SKILL.md)
   256	### Phase 4 — End of Epic Verification
   257	
   258	Once every task is `done`, resolve candidate commit SHA (`git rev-parse HEAD`) with a clean tree (`git status --porcelain` prints nothing):
   259	
   260	1. **Review decisions**, only when `.devtool/epic/<epic_dir>/review_results.md` exists:
   261	   ```bash
   262	   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --epic-dir <epic_dir>
   263	   ```
   264	   Exit 1 means unresolved finding: record decision or make Fix commit, then restart Phase 4 in full.
   265	2. **Gate 4 audit**:
   266	   ```bash
   267	   python3 "$SKILL_DIR"/resources/scripts/audit_epic.py --epic-dir <epic_dir> --base <base_ref>
   268	   ```
   269	   Must exit 0. Keep output for Phase 4.1.
   270	3. **HLD Integration results commands.** Run every `Integration results:` line of HLD Integration Test Plan.
   271	4. **Result-based traceability**: run `check_bdd_traceability.py tests --results` over those reports:
   272	   ```bash
   273	   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   274	     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
   275	     --roots <Integration test roots from the HLD> \
   276	     --results <reports written by Integration results commands>
   277	   ```
   278	   Must exit 0: every scenario in `bdd_scenarios.en.md` is covered by at least one passing integration test. `--roots` and `--ids` accept space- or comma-separated values.
   279	5. **Quality check.** Run `@quality_check` on the same SHA:
   280	   - Inputs:
   281	     - `profile`: `"epic"`
   282	     - `base_ref`: `<base_ref>`
   283	     - `repository_sha`: Candidate commit SHA from `git rev-parse HEAD`
   284	   - Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.
   285	
   286	#### Semantic Test Integrity Governance (Gate 4 Rules)
   287	
   288	Gate 4 enforces strict semantic test integrity to prevent false-confidence passes. Registered providers and auditors reject test fakery with **`FAIL`**:
   289	1. **No Reconstructed Logic**: Tests MUST import and invoke production code directly from Allowed files. Tests MUST NOT reconstruct production logic (such as retry loops, progress tracking, mapping transformations, or configuration defaults) locally within test helpers or mock harnesses. If a test reconstructs production logic instead of invoking production symbols, the review reports FAIL.
   290	2. **Immutable Real Artifacts**: Tests MUST execute against genuine, immutable repository artifacts, schemas, and fixtures. Tests MUST NOT substitute synthetic artifacts or mock data that alter scenario anchors or weaken contractual invariants. If a test substitutes synthetic artifacts that alter scenario anchors, the review reports FAIL.
   291	
   292	*(Note: These are Gate 4 semantic integrity requirements evaluated by specialist providers and audits; no universal cross-language mechanical coverage claim is made.)*
   293	
   294	### Review Choice — after every Gate 4 PASS
   295	
   296	<HARD-GATE>
   297	You MUST NOT skip or auto-decide Review Choice after Gate 4 passes.
   298	Present the choice between "Finish", "Cross-model review" and "Local model review" and wait for the developer's explicit instruction.
   299	Cross-model review and Local model review must return to Phase 4 in full; only the next Gate 4 PASS may present Review Choice again.
   300	</HARD-GATE>
   301	
   302	The loop invariant is **Gate 4 PASS → Review Choice; Finish → Gate 5; Cross-model review → Gate 4 in full; Local model review → Gate 4 in full**.
   303	<!-- Workflow transitions:
   304	moretasks -- "no, epic done" --> phase4
   305	phase4 -- "PASS" --> choice
   306	choice -- "Finish" --> checkpoint4
   307	review -- "round recorded" --> phase4
   308	choice -- "Local model review" --> localreview
   309	localreview -- "round recorded" --> phase4
   310	-->
   311	On Gate 4 PASS, run `python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 4.1: Review Choice"` (which synchronizes `window.title` to Review Choice) and emit the prompt via `python3 scripts/resume_context.py --emit-prompt cross-review --epic <epic_slug>`.
   312	Ask developer and wait for answer:
   313	
   314	> Gate 4 is 🟢 LGTM for `<candidate_sha>`. How do you want to proceed?
   315	>
   316	> 1. **Finish** — continue to Gate 5, then `finishing-a-development-branch`.
   317	> 2. **Cross-model review** — an independent model reviews the epic through Claude CLI, Codex CLI, or Antigravity CLI (`command -v claude codex agy`).
   318	> 3. **Local model review** — a model served by your local Ollama reviews the epic task by task (`ollama list`).
   319	
   320	Option 1 goes to Phase 4.1 / Gate 5. Option 2 invokes `d3nexus:cross-model-review` in epic worktree with clean tree:

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_task_checks.py | sed -n '180,276p'; nl -ba skills/dev-implementation/resources/scripts/sync_task_status.py | sed -n '470,540p'; nl -ba skills/dev-implementation/resources/scripts/task_contract.py | sed -n '1,110p'; rg -n 'Integration results|load_reports|integration_results|class.*Layout|clean' skills/dev-implementation/resources/scripts/task_contract.py skills/dev-implementation/resources/scripts/audit_epic.py; nl -ba skills/quality_check/resources/scripts/aggregate_quality_results.py | sed -n '1,180p'; nl -ba scripts/verify.sh | sed -n '260,390p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   180	                f"TASK_TAMPERED_ERROR: task '{path.name}' core sections altered from HEAD"
   181	            )
   182	
   183	
   184	def utc_now() -> str:
   185	    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
   186	
   187	
   188	def fresh_reports(path: str, root: Path, since: float) -> list[Path]:
   189	    """The report files under a results path that were written at or after `since`; older ones never count."""
   190	    try:
   191	        files = report_files(path, root)
   192	    except ReportError:
   193	        return []
   194	    return [file for file in files if file.stat().st_mtime >= since]
   195	
   196	
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
   211	    expect = row.expect
   212	    if expect.nonzero and code == 0:
   213	        return "exit 0, expected non-zero"
   214	    if expect.exit_code is not None and code != expect.exit_code:
   215	        return f"exit {code}, expected {expect.exit_code}"
   216	    missing = next((t for t in expect.contains if t not in text), None)
   217	    return None if missing is None else f'output lacks "{missing}"'
   218	
   219	
   220	def epic_scenario_ids(layout: EpicLayout) -> list[str]:
   221	    try:
   222	        return cast(list[str], load_scenarios(layout.epic_dir / "bdd_scenarios.en.md")[0])
   223	    except UsageError:
   224	        return []
   225	
   226	
   227	def attach_digest(results: dict[str, Any], files: list[Path], scenario_ids: list[str]) -> str | None:
   228	    """Store the digest of the fresh reports; None on success, else the row's failure reason."""
   229	    try:
   230	        results["digest"] = digest(load_files(files), scenario_ids)
   231	    except ReportError:
   232	        return "results in neither format"
   233	    return None
   234	
   235	
   236	def run_row(row: Row, root: Path, timeout: int, scenario_ids: list[str]) -> dict[str, Any]:
   237	    record: dict[str, Any] = {
   238	        "id": row.id,
   239	        "phase": row.phase,
   240	        "command": row.command,
   241	        "expect": row.expect_text,
   242	        "needs": list(row.needs),
   243	        "exit": None,
   244	        "outcome": "PASS",
   245	        "reason": None,
   246	        "started": utc_now(),
   247	        "finished": None,
   248	        "output_tail": [],
   249	        "output_sha256": hashlib.sha256(b"").hexdigest(),
   250	    }
   251	    unset = next((name for name in row.needs if not os.environ.get(name)), None)
   252	    if unset:
   253	        record.update(outcome="BLOCKED", reason=f"unset: {unset}")
   254	    else:
   255	        started = time.time()
   256	        code, output = run_command(row.command, root, timeout)
   257	        text = output.decode("utf-8", "replace")
   258	        record.update(exit=code, output_tail=text.splitlines()[-TAIL_LINES:],
   259	                      output_sha256=hashlib.sha256(output).hexdigest())
   260	        reason = f"timeout after {timeout} s" if code is None else mismatch(row, code, text)
   261	        if row.phase == "RED":
   262	            pytest_err = validate_pytest_red(row.command, code, text)
   263	            if pytest_err:
   264	                reason = pytest_err
   265	        if row.expect.results:
   266	            files = fresh_reports(row.expect.results, root, started)
   267	            record["results"] = {"path": row.expect.results, "fresh": bool(files)}
   268	            reason = reason or (None if files else STALE)
   269	            if files:
   270	                reason = reason or attach_digest(record["results"], files, scenario_ids)
   271	        if reason:
   272	            record.update(outcome="FAIL", reason=reason)
   273	    record["finished"] = utc_now()
   274	    return record
   275	
   276	
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
     1	#!/usr/bin/env python3
     2	"""Parse a task file's Verification contract, and fingerprint the worktree it is checked in.
     3	
     4	Shared by run_task_checks.py and the other scripts that read task files, so every one of them reads a
     5	task identically. Python 3 standard library only.
     6	"""
     7	from __future__ import annotations
     8	
     9	import json
    10	import os
    11	import re
    12	import shlex
    13	import subprocess
    14	import tempfile
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
    41	    """A task file or HLD the parser cannot accept; the message names the row or section."""
    42	
    43	
    44	@dataclass(frozen=True)
    45	class Expect:
    46	    exit_code: int | None
    47	    nonzero: bool
    48	    contains: tuple[str, ...]
    49	    results: str | None
    50	
    51	
    52	@dataclass(frozen=True)
    53	class Row:
    54	    id: str
    55	    phase: str
    56	    command: str
    57	    expect_text: str
    58	    expect: Expect
    59	    needs: tuple[str, ...]
    60	
    61	
    62	@dataclass(frozen=True)
    63	class AllowedPath:
    64	    pattern: str
    65	    new: bool
    66	
    67	
    68	@dataclass(frozen=True)
    69	class EpicLayout:
    70	    root: Path
    71	    epic_dir: Path
    72	    hld: Path
    73	    scenarios: Path
    74	    evidence: Path
    75	
    76	
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
skills/dev-implementation/resources/scripts/audit_epic.py:49:GRADER_LINES = ("Protected paths:", "Integration results:")
skills/dev-implementation/resources/scripts/audit_epic.py:211:    """The HLD's Protected paths: and Integration results: lines, diffed between <base> and HEAD."""
skills/dev-implementation/resources/scripts/audit_epic.py:220:    return ["\n  ".join([f"{Path(hld).name}: Protected paths or Integration results changed since base", *diff,
skills/dev-implementation/resources/scripts/task_contract.py:69:class EpicLayout:
skills/dev-implementation/resources/scripts/task_contract.py:221:def parse_integration_results(hld_text: str) -> list[str]:
skills/dev-implementation/resources/scripts/task_contract.py:222:    """The text after `Integration results:` on each such line, as written."""
skills/dev-implementation/resources/scripts/task_contract.py:224:            if line.startswith("Integration results:")]
     1	"""Deterministic result aggregation engine for the provider-based quality gate.
     2	
     3	Aggregates validated provider results into a unified decision payload and renders
     4	standard executive reports according to the reduction precedence FAIL > BLOCKED > PASS.
     5	"""
     6	
     7	from __future__ import annotations
     8	
     9	import copy
    10	import json
    11	from typing import Any
    12	
    13	
    14	def aggregate_results(
    15	    plan: list[dict[str, Any]],
    16	    results: list[dict[str, Any]],
    17	    invocation: dict[str, Any] | None = None,
    18	) -> dict[str, Any]:
    19	    """Deterministically aggregate provider results according to plan and status precedence."""
    20	    plan_by_id = {item.get("id"): item for item in plan}
    21	    normalized_providers: list[dict[str, Any]] = []
    22	
    23	    for r in results:
    24	        p = copy.deepcopy(r)
    25	        p_id = p.get("provider_id", "")
    26	        plan_item = plan_by_id.get(p_id, {})
    27	        is_required = plan_item.get("required", p.get("required", True))
    28	        p["required"] = is_required
    29	
    30	        # Sort checks by check id for determinism
    31	        checks = p.get("checks", [])
    32	        if isinstance(checks, list):
    33	            p["checks"] = sorted(checks, key=lambda c: c.get("id", ""))
    34	
    35	        # Sort blockers and warnings
    36	        p["blockers"] = sorted(p.get("blockers", []))
    37	        p["warnings"] = sorted(p.get("warnings", []))
    38	
    39	        # Check for all-NOT_APPLICABLE checks on a required provider
    40	        all_checks_na = len(checks) > 0 and all(c.get("status") == "NOT_APPLICABLE" for c in checks)
    41	        if (p.get("status") == "NOT_APPLICABLE" or all_checks_na) and is_required:
    42	            p["status"] = "BLOCKED"
    43	            blocker_msg = f"Required provider '{p_id}' has only NOT_APPLICABLE checks"
    44	            if blocker_msg not in p["blockers"]:
    45	                p["blockers"].append(blocker_msg)
    46	                p["blockers"].sort()
    47	
    48	        # Check for contradictory result (e.g. status PASS with failing check or sub-threshold coverage)
    49	        if p.get("status") == "PASS":
    50	            for c in checks:
    51	                if c.get("status") in {"FAIL", "BLOCKED"}:
    52	                    p["status"] = "BLOCKED"
    53	                    blocker_msg = f"Contradictory result: provider reported PASS but check '{c.get('id')}' has status '{c.get('status')}'"
    54	                    if blocker_msg not in p["blockers"]:
    55	                        p["blockers"].append(blocker_msg)
    56	            cov = p.get("coverage", {})
    57	            if isinstance(cov, dict):
    58	                for k, v in cov.items():
    59	                    if isinstance(v, dict):
    60	                        meas = v.get("measured")
    61	                        thresh = v.get("threshold")
    62	                        if thresh is not None and isinstance(meas, (int, float)) and isinstance(thresh, (int, float)):
    63	                            if meas < thresh:
    64	                                p["status"] = "BLOCKED"
    65	                                blocker_msg = f"Contradictory result: provider reported PASS but coverage '{k}' is below threshold ({meas} < {thresh})"
    66	                                if blocker_msg not in p["blockers"]:
    67	                                    p["blockers"].append(blocker_msg)
    68	            p["blockers"].sort()
    69	
    70	        normalized_providers.append(p)
    71	
    72	    # Synthesize missing providers declared in plan
    73	    seen_result_ids = {r.get("provider_id") for r in results if r.get("provider_id")}
    74	    for plan_item in plan:
    75	        plan_id = plan_item.get("id")
    76	        if plan_id and plan_id not in seen_result_ids:
    77	            is_req = plan_item.get("required", True)
    78	            synthetic = {
    79	                "provider_id": plan_id,
    80	                "contract_version": 1,
    81	                "profile": invocation.get("profile") if invocation else (results[0].get("profile") if results else "pr"),
    82	                "repository_sha": invocation.get("repository_sha") if invocation else (results[0].get("repository_sha") if results else ""),
    83	                "status": "BLOCKED",
    84	                "required": is_req,
    85	                "checks": [],
    86	                "coverage": {},
    87	                "evidence": [],
    88	                "started_head": "",
    89	                "finished_head": "",
    90	                "duration": 0.0,
    91	                "blockers": [f"Missing result for provider '{plan_id}'"],
    92	                "warnings": [],
    93	            }
    94	            normalized_providers.append(synthetic)
    95	
    96	    # Sort providers by provider_id
    97	    normalized_providers.sort(key=lambda item: item.get("provider_id", ""))
    98	
    99	    # Evaluate precedence: FAIL > BLOCKED > PASS
   100	    failing_providers = [p for p in normalized_providers if p.get("status") == "FAIL"]
   101	    blocked_required = [p for p in normalized_providers if p.get("status") == "BLOCKED" and p.get("required", True)]
   102	    all_required = [p for p in normalized_providers if p.get("required", True)]
   103	    passed_required = [p for p in all_required if p.get("status") == "PASS"]
   104	
   105	    all_blockers: list[str] = []
   106	    all_warnings: list[str] = []
   107	    coverage_summary: dict[str, Any] = {}
   108	
   109	    for p in normalized_providers:
   110	        for b in p.get("blockers", []):
   111	            formatted_b = f"[{p.get('provider_id')}] {b}" if isinstance(b, str) else str(b)
   112	            if formatted_b not in all_blockers:
   113	                all_blockers.append(formatted_b)
   114	
   115	        for w in p.get("warnings", []):
   116	            formatted_w = f"[{p.get('provider_id')}] {w}" if isinstance(w, str) else str(w)
   117	            if formatted_w not in all_warnings:
   118	                all_warnings.append(formatted_w)
   119	
   120	        cov = p.get("coverage", {})
   121	        if isinstance(cov, dict):
   122	            for k, v in cov.items():
   123	                coverage_summary[f"{p.get('provider_id')}.{k}"] = v
   124	
   125	    all_blockers.sort()
   126	    all_warnings.sort()
   127	
   128	    profile = invocation.get("profile") if invocation else (normalized_providers[0].get("profile") if normalized_providers else "pr")
   129	    repo_sha = invocation.get("repository_sha") if invocation else (normalized_providers[0].get("repository_sha") if normalized_providers else "")
   130	
   131	    status = "PASS"
   132	    decision_trace = ""
   133	
   134	    if failing_providers:
   135	        status = "FAIL"
   136	        fail_ids = ", ".join(f"'{p.get('provider_id')}'" for p in failing_providers)
   137	        if blocked_required:
   138	            blocked_ids = ", ".join(f"'{p.get('provider_id')}'" for p in blocked_required)
   139	            decision_trace = f"FAIL outranks BLOCKED: provider(s) {fail_ids} failed while {blocked_ids} was blocked"
   140	        else:
   141	            decision_trace = f"Provider(s) {fail_ids} reported FAIL"
   142	    elif blocked_required:
   143	        status = "BLOCKED"
   144	        reasons = []
   145	        for p in blocked_required:
   146	            p_id = p.get("provider_id", "")
   147	            first_b = p.get("blockers", ["blocked"])[0]
   148	            reasons.append(f"Required provider '{p_id}' has {first_b}")
   149	        decision_trace = "; ".join(reasons)
   150	    elif all_required and len(passed_required) == len(all_required):
   151	        status = "PASS"
   152	        decision_trace = f"All required providers passed ({len(passed_required)}/{len(all_required)})"
   153	    else:
   154	        status = "BLOCKED"
   155	        decision_trace = "No required providers passed or empty execution plan"
   156	
   157	    return {
   158	        "status": status,
   159	        "profile": profile,
   160	        "repository_sha": repo_sha,
   161	        "decision_trace": decision_trace,
   162	        "providers": normalized_providers,
   163	        "blockers": all_blockers,
   164	        "warnings": all_warnings,
   165	        "coverage_summary": coverage_summary,
   166	    }
   167	
   168	
   169	def render_executive_report(payload: dict[str, Any]) -> str:
   170	    """Render a GitHub-flavored Markdown executive quality report from an aggregated payload."""
   171	    status = payload.get("status", "UNKNOWN")
   172	    profile = payload.get("profile", "unknown")
   173	    sha = payload.get("repository_sha", "unknown")
   174	    trace = payload.get("decision_trace", "")
   175	    providers = payload.get("providers", [])
   176	    blockers = payload.get("blockers", [])
   177	    warnings = payload.get("warnings", [])
   178	    coverage = payload.get("coverage_summary", {})
   179	
   180	    lines: list[str] = [
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
   281	python3 -m unittest skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py || FAILED=1
   282	
   283	echo
   284	note "== 15. Context memory management CLI and Tri-Role governance are enforced =="
   285	python3 -m unittest scripts/test_resume_context.py || FAILED=1
   286	
   287	echo
   288	note "== 16. Session refresh CLI engine and isolation contracts are enforced =="
   289	python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py || FAILED=1
   290	
   291	echo
   292	if [ "$FAILED" -eq 0 ]; then
   293	  echo "PASS — safe to publish"
   294	else
   295	  echo "FAILED — fix the above before publishing"
   296	fi
   297	exit "$FAILED"
   298	

exec
/bin/zsh -lc "python3 -B -c 'from pathlib import Path
import importlib.util
root=Path(\"/Users/danhdueexoictif/AllProjects\")
for name in (\"D3Nexus\",\"lyrics-sync\",\"nexus\"):
    repo=root/name
    contracts=repo/\"shared-contracts\"
    print(name, \"exists=\",repo.exists(), \"contracts_link=\",contracts.is_symlink(),\"contracts_exists=\",contracts.exists(), \"resolved=\",contracts.resolve())
    if contracts.exists():
        print(\"domains=\",[str(p.relative_to(contracts)) for p in contracts.glob(\"*/api_contract.md\")])
    manifest=repo/\".agents/quality/check_quality.json\"
    print(\"registry=\",manifest.read_text() if manifest.exists() else \"MISSING\")
for mod in (\"pytest\",\"jsonschema\",\"playwright\"):
    print(mod, bool(importlib.util.find_spec(mod)))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
D3Nexus exists= True contracts_link= False contracts_exists= True resolved= /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts
domains= ['lyrics-sync/api_contract.md', 'nexus/api_contract.md']
registry= {
  "schema_version": 1,
  "providers": [
    {
      "id": "rust-core",
      "skill": "d3nexus:rust-quality-check",
      "required": true,
      "profiles": [
        "pr",
        "epic",
        "scheduled",
        "release"
      ]
    }
  ]
}

lyrics-sync exists= True contracts_link= True contracts_exists= True resolved= /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync
domains= []
registry= {
  "schema_version": 1,
  "providers": [
    {
      "id": "python-core",
      "skill": "d3nexus:python-quality-check",
      "required": true,
      "profiles": [
        "pr",
        "epic"
      ]
    }
  ]
}

nexus exists= True contracts_link= True contracts_exists= True resolved= /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus
domains= []
registry= {
  "schema_version": 1,
  "providers": [
    {
      "id": "flutter-core",
      "skill": "d3nexus:flutter-quality-check",
      "required": true,
      "profiles": [
        "pr",
        "epic"
      ]
    }
  ]
}

pytest False
jsonschema False
playwright False

codex
Đã xác nhận hai chỗ lệch quan trọng: danh sách khóa kết quả bị đóng băng trong Task 01 khác schema v1 hiện hành; và BDD yêu cầu traceability/status-sync phát hiện mock, trong khi mã hiện tại chỉ xét ID và kết quả test. Tôi sẽ probe trực tiếp hai hành vi này và kiểm tra đường tạo báo cáo Gate 4.

exec
/bin/zsh -lc "nl -ba /Users/danhdueexoictif/AllProjects/lyrics-sync/tests/e2e_full_screens_chrome_test.py | sed -n '1,210p'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/package.json; rg --files /Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web | rg '(playwright|e2e|tsconfig)' | head -45; rg -n 'fixture|schema|mock|snapshot|stateless|Database|SQLite|HTTP|memory|GAP|RFC' /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/{api_contract.md,architecture_and_flow.md,gaps_and_rfcs.md} /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/{api_contract.md,architecture_and_flow.md,gaps_and_rfcs.md}" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	"""Automated Google Chrome E2E test suite for Preview Player, Flashcards, and Search.
     2	
     3	Validates all 3 requested screens with real user interactions on Google Chrome:
     4	1. Preview Player Screen (playback, lines, speed controls, mute, scrubber, seeking, collocations)
     5	2. Flashcards & Vocabulary Screen (navigation, search filter, CEFR filter, cards grid, drawer edit)
     6	3. Catalog Search Screen (/search, suggestions dropdown, filter chips, sorting, cards grid, preview)
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	import sys
    12	import time
    13	
    14	import pytest
    15	
    16	pytest.importorskip("playwright", reason="playwright is required for browser E2E tests")
    17	from playwright.sync_api import sync_playwright
    18	
    19	CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    20	BASE_URL = "http://localhost:8768"
    21	
    22	
    23	def run_tests() -> None:
    24	    print(f"[Full Chrome E2E] Launching Google Chrome from: {CHROME_PATH}")
    25	    errors: list[str] = []
    26	    failed_requests: list[str] = []
    27	
    28	    with sync_playwright() as p:
    29	        browser = p.chromium.launch(
    30	            executable_path=CHROME_PATH,
    31	            headless=True,
    32	            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
    33	        )
    34	        page = browser.new_page()
    35	
    36	        # Capture browser console errors and failed responses
    37	        page.on("console", lambda msg: print(f"  [Browser {msg.type}] {msg.text}"))
    38	        page.on("pageerror", lambda err: errors.append(f"Uncaught Page Error: {err}"))
    39	        page.on(
    40	            "response",
    41	            lambda r: (
    42	                failed_requests.append(f"{r.status} {r.url}")
    43	                if r.status >= 400 and not r.url.endswith("favicon.ico")
    44	                else None
    45	            ),
    46	        )
    47	
    48	        # =========================================================================
    49	        # 1. PREVIEW PLAYER SCREEN VERIFICATION
    50	        # =========================================================================
    51	        print("\n=======================================================")
    52	        print("STAGE 1: Preview Player Screen Verification")
    53	        print("=======================================================")
    54	        print(f"[Preview Player] Navigating to {BASE_URL}...")
    55	        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
    56	        assert page.title(), "Preview player failed to load"
    57	        print("[Preview Player] Page loaded successfully!")
    58	
    59	        # 1a. Verify Active View is Karaoke/Preview
    60	        tab_preview = page.locator("#tab-preview")
    61	        assert tab_preview.is_visible(), "Tab Preview button not visible"
    62	        karaoke_view = page.locator("#karaoke-view")
    63	        assert karaoke_view.is_visible(), "Karaoke / Preview player view not visible"
    64	
    65	        # 1b. Verify Lines Container and Synced Lyrics
    66	        lines_container = page.locator("#lines")
    67	        assert lines_container.is_visible(), "Lyrics lines container not visible"
    68	        page.wait_for_selector("#lines .line", timeout=6000)
    69	        lines_count = page.locator("#lines .line").count()
    70	        print(f"[Preview Player] Rendered lyrics lines: {lines_count}")
    71	        assert lines_count > 0, "No lyrics lines rendered in preview player"
    72	
    73	        first_line = page.locator("#lines .line").first
    74	        first_line_text = first_line.inner_text().strip()
    75	        print(f"[Preview Player] First line text preview: '{first_line_text[:50]}...'")
    76	
    77	        # 1c. Test Playback Controls (Play / Pause toggle)
    78	        play_pause_btn = page.locator("#play-pause")
    79	        assert play_pause_btn.is_visible(), "Play/Pause button not visible"
    80	        initial_play_icon = play_pause_btn.inner_text().strip()
    81	        print(f"[Preview Player] Initial play button icon: '{initial_play_icon}'")
    82	        play_pause_btn.click()
    83	        time.sleep(0.5)
    84	        after_click_icon = play_pause_btn.inner_text().strip()
    85	        print(f"[Preview Player] Play button icon after click: '{after_click_icon}'")
    86	        # Pause again
    87	        play_pause_btn.click()
    88	        time.sleep(0.3)
    89	
    90	        # 1d. Test Speed Stepper (Speed Up / Down)
    91	        speed_readout = page.locator("#speed-readout")
    92	        speed_up_btn = page.locator("#speed-up")
    93	        speed_down_btn = page.locator("#speed-down")
    94	        assert speed_readout.is_visible(), "Speed readout not visible"
    95	        initial_speed = speed_readout.inner_text().strip()
    96	        print(f"[Preview Player] Initial speed: {initial_speed}")
    97	
    98	        speed_up_btn.click()
    99	        time.sleep(0.2)
   100	        speed_after_up = speed_readout.inner_text().strip()
   101	        print(f"[Preview Player] Speed after increase: {speed_after_up}")
   102	        assert speed_after_up != initial_speed or "1.25" in speed_after_up, "Speed increase failed"
   103	
   104	        speed_down_btn.click()
   105	        time.sleep(0.2)
   106	        print(f"[Preview Player] Speed after decrease: {speed_readout.inner_text().strip()}")
   107	
   108	        # 1e. Test Mute Toggle
   109	        mute_btn = page.locator("#dock-mute-btn")
   110	        assert mute_btn.is_visible(), "Dock mute button not visible"
   111	        mute_btn.click()
   112	        time.sleep(0.2)
   113	        print(f"[Preview Player] Mute button after click: {mute_btn.inner_text().strip()}")
   114	        mute_btn.click()
   115	        time.sleep(0.2)
   116	
   117	        # 1f. Test Sentence Gap Select
   118	        gap_select = page.locator("#sentence-gap-select")
   119	        assert gap_select.is_visible(), "Sentence gap select not visible"
   120	        gap_select.select_option("3")
   121	        time.sleep(0.2)
   122	        assert gap_select.input_value() == "3", "Sentence gap selection failed"
   123	        gap_select.select_option("0")
   124	        print("[Preview Player] Sentence gap option selection verified.")
   125	
   126	        # 1g. Test Clicking a Line to Seek
   127	        if lines_count >= 2:
   128	            second_line = page.locator("#lines .line").nth(1)
   129	            second_line.click()
   130	            time.sleep(0.3)
   131	            print("[Preview Player] Successfully clicked line 2 for playback focus.")
   132	
   133	        # 1h. Test Collocation Click and Popover (if collocations rendered)
   134	        collocations = page.locator(".collocation")
   135	        coll_count = collocations.count()
   136	        print(f"[Preview Player] Highlighted collocations detected: {coll_count}")
   137	        if coll_count > 0:
   138	            first_coll = collocations.first
   139	            print(f"[Preview Player] Clicking collocation: '{first_coll.inner_text()}'...")
   140	            first_coll.click()
   141	            page.wait_for_selector("#collocation-popover:not([hidden])", timeout=4000)
   142	            popover = page.locator("#collocation-popover")
   143	            assert popover.is_visible(), "Collocation popover failed to open"
   144	            phrase_text = page.locator("#collocation-popover-phrase").inner_text()
   145	            print(f"[Preview Player] Popover opened for phrase: '{phrase_text}'")
   146	
   147	            close_btn = page.locator("#collocation-popover-close")
   148	            close_btn.click()
   149	            page.wait_for_selector("#collocation-popover", state="hidden", timeout=4000)
   150	            print("[Preview Player] Popover closed successfully.")
   151	
   152	        assert len(errors) == 0, f"Errors encountered during Preview Player test: {errors}"
   153	        print("[Preview Player] All Preview Player tests PASSED!")
   154	
   155	        # =========================================================================
   156	        # 2. FLASHCARDS & VOCABULARY SCREEN VERIFICATION
   157	        # =========================================================================
   158	        print("\n=======================================================")
   159	        print("STAGE 2: Flashcards & Vocabulary Screen Verification")
   160	        print("=======================================================")
   161	        tab_flashcards = page.locator("#tab-flashcards")
   162	        assert tab_flashcards.is_visible(), "Tab Flashcards button not visible"
   163	        print("[Flashcards] Clicking #tab-flashcards...")
   164	        tab_flashcards.click()
   165	
   166	        page.wait_for_selector("#flashcards-view:not([hidden])", timeout=5000)
   167	        flashcards_view = page.locator("#flashcards-view")
   168	        assert flashcards_view.is_visible(), "Flashcards view failed to display"
   169	        print("[Flashcards] Flashcards view is visible.")
   170	
   171	        # 2a. Verify Header, Filters and Toolbar
   172	        filter_search = page.locator("#flashcards-filter-search")
   173	        filter_cefr = page.locator("#flashcards-filter-cefr")
   174	        assert filter_search.is_visible(), "Vocabulary filter search input not visible"
   175	        assert filter_cefr.is_visible(), "CEFR filter dropdown not visible"
   176	
   177	        # 2b. Verify Action Buttons
   178	        edit_btn = page.locator("#flashcards-open-drawer-btn")
   179	        sync_r2_btn = page.locator("#flashcards-sync-all-btn")
   180	        refresh_btn = page.locator("#flashcards-refresh-btn")
   181	        assert edit_btn.is_visible(), "Edit button not visible"
   182	        assert sync_r2_btn.is_visible(), "Sync R2 button not visible"
   183	        assert refresh_btn.is_visible(), "Refresh button not visible"
   184	
   185	        # 2c. Check Cards Grid & Summary Bar
   186	        time.sleep(1.0)
   187	        summary_text = page.locator("#flashcards-count-label").inner_text()
   188	        print(f"[Flashcards] Summary label: '{summary_text}'")
   189	
   190	        cards = page.locator("#panel-flashcards .flashcard-card, #panel-flashcards .fc-card")
   191	        card_count = cards.count()
   192	        print(f"[Flashcards] Flashcard cards rendered in grid: {card_count}")
   193	
   194	        # 2d. Test Filter Search Interaction
   195	        filter_search.fill("family")
   196	        filter_search.dispatch_event("input")
   197	        time.sleep(0.3)
   198	        filter_search.fill("")
   199	        filter_search.dispatch_event("input")
   200	        time.sleep(0.2)
   201	
   202	        # 2e. Test CEFR Dropdown Interaction
   203	        filter_cefr.select_option("B1")
   204	        time.sleep(0.3)
   205	        filter_cefr.select_option("")
   206	        time.sleep(0.2)
   207	        print("[Flashcards] Filter controls verified successfully.")
   208	
   209	        # 2f. Test Opening Flashcard Review Drawer via Edit Button
   210	        print("[Flashcards] Testing Review Drawer toggle...")
     1	{
     2	  "name": "@d3nexus/learning-web",
     3	  "version": "1.0.0",
     4	  "type": "module",
     5	  "description": "D3Nexus English Learning Web Application (Astro + Vanilla Custom Elements + Screen MVI + Rust WASM)",
     6	  "scripts": {
     7	    "dev": "astro dev",
     8	    "start": "astro dev",
     9	    "build": "astro build",
    10	    "preview": "node preview.mjs",
    11	    "test:guard": "node --experimental-strip-types --test tests/unit/design-system-guard.test.ts",
    12	    "test": "node --experimental-strip-types --test tests/unit/*.test.ts tests/*.test.ts tests/e2e/*.test.ts"
    13	  },
    14	  "dependencies": {
    15	    "@d3nexus/contracts": "file:../../packages/contracts",
    16	    "astro": "^5.0.0"
    17	  },
    18	  "devDependencies": {
    19	    "@playwright/test": "^1.64.1",
    20	    "typescript": "^5.7.0"
    21	  }
    22	}
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/playwright.config.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tsconfig.json
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/studio-align-e2e.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/seamless-history-navigation.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/fcs-acceptance.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lyric-font-size-control.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/apple-music-media-controller.spec.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lvf-implicit-grading-flow.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/live-postgres-catalog.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lyrics-preview-parity-scenarios.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/flashcard-fsrs-security.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/design-docs.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/preview-keyboard-dispatcher.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/tts-studio-fixes.spec.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/design-styleguide.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/fcs-track-options.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/youtube-autoplay-tab-focus.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/auto-replay-composition-root.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/youtube-embed-fallback.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/flashcard-fsrs-entitlement.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/design-auth.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/align-studio-acceptance.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/volume-hud-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/today_dashboard.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/flashcard-fsrs-online-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/today-browser-responsive.spec.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/flashcard-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/flashcard-fsrs-web-runtime.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/design-player-dock.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lvf-binary-review-room.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/design-vocab-flashcards.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/fcs-memory-rating.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lvf-popover-add-card.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/bilingual-animation-modes-acceptance.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/lyrics-display-and-animations.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/tts-studio-acceptance.spec.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/contextual-flashcard-sharing.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/preview-keyboard-shortcuts-bdd.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/fcs-vocab-enroll.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/keyboard-ime-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/catalog-taxonomy-live.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/settings-parity-e2e.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/seamless-persistent-playback.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/sentence-playback-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/collocation-flashcard-integration.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:1:# Gaps, Open Inquiries & RFCs: D3Nexus ⇄ nexus (Mobile App)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:12:This document serves as the formal asynchronous Request For Change (RFC) and communication ledger between the AI Agents and engineers developing `nexus` (Mobile Client) and `D3Nexus` (Control Plane).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:18:### GAP-NEX-01: HTTP 206 Partial Content (Byte-Range) Support for Audio Seeking
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:20:  Mobile audio playback engines (iOS `AVPlayer` and Android `ExoPlayer` / `Media3` used by `just_audio` in `packages/media_player`) require strict HTTP 206 byte-range handling. When scrubbing the playback timeline or resuming playback from a word index, the player dispatches `Range: bytes=START-END` or `Range: bytes=START-`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:22:  `D3Nexus` serves media via `learning_media::media_streaming_router`. If the server returns HTTP 200 with the full file stream instead of HTTP 206 with `Content-Range: bytes START-END/TOTAL`, mobile players on iOS will fail seeking or buffer the entire file repeatedly.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:24:  Verify and ensure that `apps/server` media streaming handlers explicitly handle `Range` headers, return `HTTP 206 Partial Content`, `Accept-Ranges: bytes`, and the accurate `Content-Range` header.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:29:### GAP-NEX-02: Mixed Timestamp Serialization (`i64` Epoch ms vs ISO-8601 Strings)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:41:### GAP-NEX-03: Client-Generated UUIDv7 Acceptance for Offline Entity Creation
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:43:  When a user creates a new flashcard or records an outbox mutation offline, `nexus` generates a UUIDv7 on device (`018f921a-7b3c-7411-921a-883a992b1001`) to ensure chronological index ordering in SQLite.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:50:### GAP-NEX-04: Concurrent Request Token Refresh Grace Window
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:52:  When an access token expires while the mobile client initiates multiple parallel queries (e.g. fetching `/today/overview`, `/lyrics/shelves`, and `/cards/due` simultaneously), all three requests fail with HTTP 401.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:60:### GAP-NEX-05: CORS & Custom Mobile Telemetry Headers
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:62:  The mobile client includes custom headers (`X-Device-Id`, `X-Platform`, `X-App-Version`, `X-Guest-Session-Id`). While native iOS/Android HTTP bypasses browser CORS, web builds and Flutter Web integration tests enforce strict CORS pre-flight (`OPTIONS`).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:69:### GAP-NEX-06: Response Envelope Discrepancy (`BaseResponseObject` vs Raw Payload)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:80:### GAP-NEX-07: Token Pair Response Key Mappings
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:101:### GAP-NEX-08: E2EE Olm/Megolm Key Exchange & Push Encrypted Payload Format
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:105:  Establish the encrypted push payload schema:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:115:  Native mobile extensions (`UNNotificationServiceExtension` / `FirebaseMessagingService`) call Rust FFI directly to decrypt and insert into local SQLite before notifying the OS.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:120:### GAP-NEX-09: Task & Habit Sync Schema Alignment
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:129:### GAP-NEX-10: SSE Assistant Intent Action Protocol & Reconnection with `Last-Event-ID`
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:139:## 2. Accepted RFCs & Architectural Standards
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:141:### RFC-NEX-001: Hybrid Logical Clock (HLC) Causal Ordering
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:150:### RFC-NEX-002: Postel's Law for 60fps Lyrics Timings
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:154:  The `lyrics-sync/v1` document schema delivers word and line timing properties using camelCase (`startMs`, `endMs`, `durationMs`). Flutter mobile client directly parses these fields into high-speed primitive integer arrays to maximize 60fps-120fps canvas rendering performance.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:159:### RFC-NEX-003: 10-Field Lexical Chunk Canonical Model in `all_collocations`
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:163:  Every collocation item in `lyrics_doc.all_collocations` MUST supply the complete 10-field lexical schema:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:178:### RFC-NEX-004: Dual-Alias Deserialization Policy for `startMs` / `start_ms`
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:190:### RFC-NEX-005: Zero-Engine Encrypted Push Notification Architecture
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:194:  On iOS and Android, incoming push notifications carrying E2EE payload must NOT spin up the Flutter engine (which incurs a ~300ms latency and 80MB memory footprint). Instead, native platform extensions link directly to the pre-compiled `learning_core` Rust library via C-ABI, decrypt the payload, commit directly to the encrypted SQLite database via SQLite WAL mode, and present the local notification.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md:199:### RFC-NEX-006: Standardize API Response Envelope Format (`BaseResponseObject<T>`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:14:The `nexus` mobile client communicates with the `D3Nexus` backend over HTTPS and Server-Sent Events (SSE).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:38:Every REST JSON response emitted by `/api/*` endpoints MUST conform to the universal `BaseResponseObject<T>` wire schema:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:50:* `success` (`boolean`, required): `true` for successful operations (HTTP status 2xx), `false` for client or server errors (HTTP status 4xx/5xx).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:53:* `data` (`T | null`, required): The actual payload data (JSON object, array, primitive, or `null`). For HTTP 204 No Content responses mapped to 200 OK or error responses, `data` is `null`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:57:* **Streaming & Binary Bypass**: Server-Sent Events (`text/event-stream`), byte-range audio streaming (`audio/*`, HTTP 206), and non-API documentation or health check routes (`/healthz`, `/docs`, `/swagger-ui`, `/openapi.json`) are completely excluded from envelope wrapping.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:456:        "schema": "lyrics-sync/v1",
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:498:  * **`304 Not Modified`**: ETag matched; mobile client uses local SQLite/Hive cache.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:557:The `nexus` app creates cards, edits tags, modifies tasks, and performs flashcard reviews entirely offline. Mutations are queued in a local SQLite Outbox and synchronized using Hybrid Logical Clocks (HLC).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:574:        "schema_version": 1,
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:591:        "schema_version": 1,
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:607:        "schema_version": 1,
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:732:| **Timestamps (Network & Database)** | Unix Epoch Milliseconds | `i64` milliseconds with `_ms` suffix (`updated_at_ms`, `due_at_ms`, `completed_at_ms`, `created_at`). |
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md:734:| **UUIDs** | UUIDv7 for outbox/entities, UUIDv4 for devices | High-cardinality, time-ordered UUIDv7 prevents SQLite B-tree index fragmentation. |
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:1:# Gaps, Open Inquiries & RFCs: D3Nexus ⇄ lyrics-sync
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:12:This document serves as the formal asynchronous Request For Change (RFC) and communication ledger between the AI Agents and engineers developing `lyrics-sync` and `D3Nexus`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:16:- [2. Accepted RFCs & Architectural Decisions](#2-accepted-rfcs--architectural-decisions)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:19:- [5. Lexical & Collocation RFCs](#5-lexical--collocation-rfcs)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:25:### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:29:  For standard 3-5 minute songs, payloads remain under 1MB. However, long-form content may be rejected with `HTTP 413 Payload Too Large`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:40:### GAP-02: Mixed Timestamp Key Formats (`startMs` vs `start_ms`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:42:  In `lyrics-sync/v1`, line and word timestamps use camelCase (`startMs`, `endMs`, `durationMs`) adhering to the committed JSON schema (`schema/lyrics-sync.v1.schema.json`). However, inside `all_collocations[].occurrences`, timestamps use snake_case (`start_ms`, `end_ms`).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:62:### GAP-03: Co-Located Media Path vs Remote Media URL Resolution
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:74:### GAP-04: Worker Token Authentication for Fleet Monitoring (`GET /api/v1/align/fleet`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:76:  Currently, `GET /api/v1/align/fleet` requires an authenticated web user cookie/session in D3Nexus, returning `HTTP 401 Unauthorized` when queried using `X-Worker-Token`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:86:### GAP-05: Server Restart Orphaned Task Reclaim Hook
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:95:### GAP-06: Fleet Status Missing Active Pipeline Step (`current_step` in `GET /api/v1/align/fleet`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:115:### GAP-07: Unified Multi-Pipeline Worker Capability Negotiation (Align Studio vs TTS Studio)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:120:  In `POST /api/v1/speech/worker/claim`, align the request payload schema with `POST /api/v1/align/worker/claim` by accepting an optional `capabilities: list[string]` field so the scheduler only routes Kokoro-targeted tasks to nodes with Apple Silicon MPS or CUDA acceleration enabled.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:127:## 2. Accepted RFCs & Architectural Decisions
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:129:### RFC-001: 7-Step Canonical Pipeline & Subprocess Group Isolation
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:146:### RFC-002: Postel's Law Telemetry Deserialization (Defense-in-depth)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:150:  To prevent HTTP 422 schema deserialization rejections during heartbeat dispatch:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:151:  - Worker standardizes all RAM and MPS memory metrics to integer megabytes using `round(...)`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:164:### 3.1. Feedback on Open Gaps (GAP-01 to GAP-05)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:166:#### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:168:  In `apps/server/src/wiring.rs` and `apps/server/src/align_api/worker.rs`, no explicit `DefaultBodyLimit` is configured. Axum defaults to 2 MB (`2 * 1024 * 1024` bytes). Large tasks (> 2 MB) with detailed word-level timestamps and 10-field collocations will indeed fail with `HTTP 413 Payload Too Large`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:172:#### GAP-02: Mixed Timestamp Key Formats (`startMs` vs `start_ms`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:180:#### GAP-03: Co-Located Media Path vs Remote Media URL Resolution
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:185:#### GAP-04: Worker Token Authentication for Fleet Monitoring (`GET /api/v1/align/fleet`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:186:* **D3Nexus Finding**: **CONFIRMED GAP**.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:191:#### GAP-05: Server Restart Orphaned Task Reclaim Hook
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:193:  Currently, orphaned tasks remain locked in SQLite until the 900-second lease expires via the periodic background reaper task.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:236:  In D3Nexus, this route is in `client_router` and strictly requires a User or Admin JWT cookie/bearer token. A request from a worker node presenting only `X-Worker-Token` is rejected with HTTP 401/403.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:246:### GAP-08: Explicit Failure Reporting Endpoint for TTS Worker (`POST /api/v1/speech/worker/jobs/{id}/fail`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:264:### GAP-09: Telemetry & Memory Metrics in Speech Worker Heartbeat (`POST /api/v1/speech/worker/heartbeat`)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:268:  Update `POST /api/v1/speech/worker/heartbeat` request schema to accept optional `metrics: { ... }` adhering to Postel's Law (integers via `round(...)`).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:273:### GAP-10: TTS Worker Audio Artifact Delivery Standard (Local Path vs Multipart Upload)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:284:## 5. Lexical & Collocation RFCs
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:286:### RFC-003: Collocation Schema Alignment, IPA Expansion & Lexical Separation
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:325:### RFC-004: Lyrics Report Worker Endpoint Protocol & Audio Slicing
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:329:  Learner-submitted line overrides and transcript edits require isolated forced alignment without re-running full-song Demucs/Whisper pipelines. The worker fleet acts as a stateless compute cluster leasing pending overrides via `/api/v1/lyrics-report/worker/tasks/claim`, pulling audio slices via `/api/v1/lyrics/{slug}/lines/{line_index}/audio-slice`, and reporting word timings via `/complete`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:331:  1. **Short Lease TTL**: 10-second default lease with 10-second heartbeat extension. Expired heartbeats receive HTTP 409 Conflict with `should_abort: true`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:337:### RFC-005: 3-Tier Worker Queue Task Execution Priority Hierarchy & Lease Dispatch
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:351:### RFC-006: Context-First Align Studio Flow — Canonical Step Reorder & Locked Context Profile Payload
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:356:  Align Studio lexical extraction currently runs on 8-line windows while simultaneously translating each chunk into Vietnamese. Splitting model attention across English linguistics and Vietnamese translation produces hallucinated chunks, over-extraction, and isolated chunk translations that clash with sentence-level pronouns and negation. The new flow locks the discourse profile once, extracts pure-English lexical candidates, filters them deterministically in Python, then translates subtitle lines and surviving chunks together in one top-down pass. Because lexical work now completes *before* the chunk translation it feeds, the canonical step sequence must follow the data dependency. `architecture_and_flow.md` §2 declares that sequence authoritative across both codebases, so `lyrics-sync` cannot reorder it unilaterally and raises this RFC instead.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md:363:  6. **Explicitly Unchanged**: The 12-key `meta.domains` set enforced by PostgreSQL `chk_lyrics_domains` and `taxonomy.rs` remains frozen; finer subject nuance is carried in `meta.context_profile.sub_topic`. The 10-field `collocations` and `all_collocations` wire schemas are untouched. Both remain 100% backward compatible.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:19:│  - Axum / Tokio Rust High-Performance HTTP Engine                      │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:20:│  - Authoritative PostgreSQL Database (Catalog, Entitlements, FSRS)    │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:22:│  - Audio Transcoding & Byte-Range HTTP 206 Streaming                   │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:25:                                    │ HTTPS REST + SSE Streaming
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:33:│  - Offline-First Local Store (SQLite + Drift + Hive, < 16ms reads)     │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:44:4. **Single Source of Schema Truth**: The `lyrics-sync/v1` document schema authored by the worker and stored in `D3Nexus` is directly consumed by Flutter `LyricsApiClient` and deserialized without intermediate reshaping.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:57:├── network/               # Dio HTTP client, Auth token interceptor, SSL pinning
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:59:├── learning_store/        # Local SQLite cache, HLC clock, Outbox sync gateway
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:61:├── media_player/          # Just_audio wrapper with HTTP 206 range buffer
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:85:  2. Write to Local SQLite Cache (Immediate UI State Update < 16ms)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:162:   - Sensitive user notes and flashcards stored in local SQLite are encrypted using SQLCipher with a user key derived via Argon2id.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:188:- **Spaced Repetition Scheduler**: Computes memory stability $S$, difficulty $D$, retrievability $R$, and scheduled intervals $I$ according to FSRS-4.5 formula:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/architecture_and_flow.md:197:  - The notification is decrypted, written to local SQLite, and shown to the user immediately.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:79:    * `media_url` (`string | null`): Remote URL (YouTube / HTTP media stream).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:124:  * **Worker (`lyrics-sync`) — Conservative Sender**: Always rounds memory values to integer megabytes using `round(...)` before JSON dispatch.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:125:  * **Control Plane (`D3Nexus`) — Liberal Receiver**: Uses `Option<f64>` for MPS fields and `deserialize_flexible_u64` for RAM fields in `models.rs` to guarantee HTTP 200 without 422 schema rejections.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:177:      "schema": "lyrics-sync/v1",
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:285:* **Document Metadata (`meta`)**: `schema: "lyrics-sync/v1"`, `source` (`{type: "youtube", id: "..."}` or `{type: "file", name: "..."}`), `durationMs` (camelCase i64), `offsetMs` (camelCase i64), `difficulty`, `domains`.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:389:    "error_message": "Audio stream HTTP 403 Forbidden: YouTube download failed"
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:432:TTS Studio worker endpoints power the local neural speech synthesis queue (Kokoro-82M on Apple Silicon MPS / CUDA), multi-speaker dialogue stitching, and handle automated Cloud Quota Fallbacks (HTTP 429 demotions from ElevenLabs/EdgeTTS).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:511:  * Adheres strictly to Postel's Law: Worker rounds RAM and MPS memory fields to integer megabytes (`round(...)`).
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:570:      "schema": "lyrics-sync/v1",
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:639:    "error_message": "Kokoro MPS out of memory during 32-turn dialogue synthesis"
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/api_contract.md:828:| **API Endpoints & HTTP Requests** | `snake_case` | `worker_id`, `step_name`, `spent_time_ms`, `error_message`, `lease_token`, `audio_url` |
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:26:│  - Task Queue & Lease Scheduling (SQLite / PostgreSQL)                 │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:29:│  - Cloud Quota Fallback Interceptor (HTTP 429 -> Local Worker Queue)   │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:34:                                    │ HTTP REST (X-Worker-Token)
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:53:│  - Automatic process-group fencing, memory purging & scratch cleanup   │
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:66:To ensure responsive learner interaction while processing compute-intensive background workloads, compute task execution across the stateless worker fleet adheres to a 3-tier weighted priority hierarchy:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:109:  7. artifact_export      (Progress: 100%) - LyricsDoc schema validation & payload packaging
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:120:| **7** | `artifact_export` | 100% | Validate `lyrics-sync/v1` schema, write local artifacts, assemble completion payload | Artifact Export |
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:213:4. **Cloud Quota Fallback (HTTP 429)**: When ElevenLabs or EdgeTTS hits rate limits (`HTTP 429 Too Many Requests`), D3Nexus automatically catches the error, transitions the job to `QueuedForWorker`, and dispatches it to the `lyrics-sync` worker fleet without user interruption.
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:223:      │              Quota Exceeded (HTTP 429)?
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:279:| **5** | `timestamp_alignment` | 80% | Align word boundaries into canonical lines and words adhering to `lyrics-sync/v1` schema | Align Timings |
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:305:To ensure deterministic cancellation and prevent zombie GPU processes or memory leaks on Apple Silicon / CUDA:
/Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md:335:| `ERR_SCHEMA_VALIDATION` | Both | Contract | No | Fail task immediately. Output violates contract schema invariants. |

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/task_contract.py | sed -n '530,690p'; rg -n 'pytest|junit|playwright|Integration results' skills/dev-implementation/resources/scripts/run_external_review.py; rg --files -g 'pyproject.toml' -g 'pytest.ini' -g 'setup.cfg' -g '*requirements*' -g 'AGENTS.md'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/.agents/quality/check_quality.json; nl -ba /Users/danhdueexoictif/AllProjects/lyrics-sync/.agents/quality/check_quality.json" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
385:    return audit_output, "\n".join(results) or "No Integration results declared.\n"
templates/AGENTS.md
     1	{
     2	  "schema_version": 1,
     3	  "providers": [
     4	    {
     5	      "id": "rust-core",
     6	      "skill": "d3nexus:rust-quality-check",
     7	      "required": true,
     8	      "profiles": [
     9	        "pr",
    10	        "epic",
    11	        "scheduled",
    12	        "release"
    13	      ]
    14	    }
    15	  ]
    16	}
     1	{
     2	  "schema_version": 1,
     3	  "providers": [
     4	    {
     5	      "id": "python-core",
     6	      "skill": "d3nexus:python-quality-check",
     7	      "required": true,
     8	      "profiles": [
     9	        "pr",
    10	        "epic"
    11	      ]
    12	    }
    13	  ]
    14	}

exec
/bin/zsh -lc "python3 -B -c 'import sys, json
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[\"skills/dev-implementation/resources/scripts\",\"skills/quality_check/resources/scripts\",\"skills/setup_quality_check/resources/scripts\"]
import validate_quality_contract as quality
import result_reports as reports
import check_bdd_traceability as trace
import scaffold_quality_manifest as scaffold
sha=\"c88539eeb74257e43fa573a3271ea2351931848e\"
inv={\"provider_id\":\"learning-web\",\"profile\":\"epic\",\"repository_sha\":sha}
frozen={\"provider_id\":\"learning-web\",\"contract_version\":1,\"status\":\"PASS\",\"summary\":\"OK\",\"checks\":[],\"repository_sha\":sha}
schema=json.loads(Path(\"skills/quality_check/resources/schemas/provider-result.schema.json\").read_text())
print(\"Task01 missing required keys:\",sorted(set(schema[\"required\"])-set(frozen)))
print(\"Task01 forbidden keys:\",sorted(set(frozen)-set(schema[\"properties\"])))
print(\"Task01 live validator:\",json.dumps(quality.validate_provider_result(frozen,inv)))
fake_source=\"from unittest.mock import Mock\\ndef test_WQG_HP_01():\\n    assert Mock(return_value=True)()\\n\"
with patch.object(trace,\"integration_files\",return_value=([Path(\"mock_test.py\")],[])),patch.object(Path,\"read_text\",return_value=fake_source):
    coverage, problems, warnings=trace.check_tests([\"WQG-HP-01\"],[\"WQG-HP-01\"],[Path(\".\")],True)
print(\"Mock-only traceability:\",coverage,problems)
fake_junit='\\''<testsuite><testcase name=\"test_WQG_HP_01\" classname=\"mock_test\"/></testsuite>'\\''
print(\"Mock-only result verdict:\",reports.verdicts([\"WQG-HP-01\"],reports.parse_junit(fake_junit)))
playwright_json=json.dumps({\"config\":{},\"suites\":[{\"title\":\"web\",\"specs\":[{\"title\":\"WQG-HP-01\",\"ok\":True,\"tests\":[{\"status\":\"expected\",\"results\":[{\"status\":\"passed\"}]}]}]}],\"errors\":[],\"stats\":{\"expected\":1,\"unexpected\":0}})
with patch.object(Path,\"read_text\",return_value=playwright_json):
    loaded=reports.load_files([Path(\"playwright.json\")])
print(\"Playwright JSON cases:\",loaded,\"verdict:\",reports.verdicts([\"WQG-HP-01\"],loaded))
for text in (\"{bad json\",\"[]\",\"{}\",'\\''{\"type\":\"testDone\",\"testID\":1,\"result\":\"success\"}'\\''):
    print(\"early JSON parse\",repr(text),reports.parse_dart(text))
for text in (\"<bad\",):
    with patch.object(Path,\"read_text\",return_value=text):
        try: reports.load_files([Path(\"bad.xml\")])
        except reports.ReportError as error: print(\"early XML failure:\",type(error).__name__,str(error))
with patch.object(Path,\"read_text\",side_effect=UnicodeDecodeError(\"utf-8\",b\"\\\\xff\",0,1,\"bad\")):
    try: trace.read_text(Path(\"invalid.md\"))
    except trace.UsageError as error: print(\"early text failure:\",type(error).__name__,str(error))
with patch.object(trace.subprocess,\"run\",side_effect=OSError(\"spawn failed\")):
    print(\"early subprocess failure:\",trace.listed_files(Path(\".\")))
for identifier, token in ((\"WQG-HP-01\",\"test_WQG_HP_01\"),(\"WQG-HP-01\",\"test_WQG_HP_010\"),(\"WQG-HP-01\",\"WQG-HP-01extra\"),(\"WQG-HP-01\",\"test_wqg_hp_01\")):
    print(\"ID token\",token,bool(reports.reference_pattern(identifier).search(token)))
print(\"Existing polyglot registry ids:\",[x[\"id\"] for x in scaffold.build_registry_data([\"rust\",\"python\"])[\"providers\"]])
try: scaffold.scaffold_quality_manifests(Path(\".\"),platforms=[\"web\"],dry_run=True)
except scaffold.ScaffoldError as error: print(\"Web onboarding:\",str(error))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
Task01 missing required keys: ['blockers', 'coverage', 'duration', 'evidence', 'finished_head', 'profile', 'started_head', 'warnings']
Task01 forbidden keys: ['summary']
Task01 live validator: {"status": "BLOCKED", "findings": [{"code": "missing_field", "message": "Missing duration in result", "field": "duration"}, {"code": "profile_mismatch", "message": "Result profile 'None' != invocation 'epic'"}, {"code": "sha_drift", "message": "Started head or finished head does not match repository_sha"}]}
Mock-only traceability: {'WQG-HP-01': ['mock_test.py:2']} []
Mock-only result verdict: {'WQG-HP-01': (True, 'test_WQG_HP_01')}
Playwright JSON cases: [] verdict: {'WQG-HP-01': (False, 'no test case in results')}
early JSON parse '{bad json' []
early JSON parse '[]' []
early JSON parse '{}' []
early JSON parse '{"type":"testDone","testID":1,"result":"success"}' []
early XML failure: ReportError bad.xml is not a valid report: unclosed token: line 1, column 0
early text failure: UsageError invalid.md is not valid UTF-8
early subprocess failure: None
ID token test_WQG_HP_01 True
ID token test_WQG_HP_010 False
ID token WQG-HP-01extra False
ID token test_wqg_hp_01 True
Existing polyglot registry ids: ['rust-core', 'python-core']
Web onboarding: Unsupported platform specified: 'web'. Allowed: ['flutter', 'android', 'ios', 'rust', 'python']

exec
/bin/zsh -lc "nl -ba .gitignore; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/playwright.config.ts; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/apps/learning-web/tests/e2e/apple-music-media-controller.spec.ts | sed -n '1,85p'; nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '345,390p'; nl -ba skills/dev-implementation/resources/scripts/task_contract.py | sed -n '400,535p'; rg -n 'clean|porcelain|dirty' skills/dev-implementation/resources/scripts/run_external_review.py" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	.DS_Store
     2	node_modules/
     3	*.log
     4	.superpowers/
     5	__pycache__/
     6	*.pyc
     7	.worktrees/
     8	skill-observations/
     9	build/
    10	
    11	# Devtool Tier-2 ephemeral runtime state, logs, locks, and local review preferences
    12	# (Keep .devtool/PROJECT_LEDGER.md, .devtool/epic/, .devtool/features/, .devtool/product/ tracked)
    13	.devtool/.memory.lock
    14	.devtool/assistant_state.md
    15	.devtool/activity_stream.log
    16	.devtool/state/
    17	.devtool/logs/
    18	.devtool/archive/
    19	.devtool/review_config.json
    20	.devtool/review_config.json.tmp
    21	.devtool/contract_brief_*.md
     1	import { defineConfig, devices } from '@playwright/test';
     2	
     3	const port = process.env.PLAYWRIGHT_PORT || 8385;
     4	
     5	export default defineConfig({
     6	  testDir: './tests/e2e',
     7	  testMatch: '**/*.spec.ts',
     8	  outputDir: '../../build/browser-artifacts',
     9	  fullyParallel: false,
    10	  workers: 1,
    11	  forbidOnly: !!process.env.CI,
    12	  retries: 0,
    13	  use: {
    14	    baseURL: `http://127.0.0.1:${port}`,
    15	    trace: 'on-first-retry',
    16	  },
    17	  projects: [
    18	    {
    19	      name: 'chromium',
    20	      use: { ...devices['Desktop Chrome'] },
    21	    },
    22	  ],
    23	  webServer: {
    24	    command: `npm run build && node preview.mjs --port ${port}`,
    25	    url: `http://127.0.0.1:${port}`,
    26	    reuseExistingServer: !process.env.CI,
    27	    timeout: 120 * 1000,
    28	  },
    29	});
     1	import { test, expect, type Page } from '@playwright/test';
     2	import fs from 'node:fs';
     3	import path from 'node:path';
     4	import { fileURLToPath } from 'node:url';
     5	
     6	const __filename = fileURLToPath(import.meta.url);
     7	const __dirname = path.dirname(__filename);
     8	
     9	const fixturesPath = path.join(__dirname, 'fixtures', 'apple-music-tracks.json');
    10	const fixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf-8'));
    11	
    12	function createSilentWavBuffer(durationSeconds: number): Buffer {
    13	  const sampleRate = 8000;
    14	  const numChannels = 1;
    15	  const bitsPerSample = 16;
    16	  const byteRate = (sampleRate * numChannels * bitsPerSample) / 8;
    17	  const blockAlign = (numChannels * bitsPerSample) / 8;
    18	  const numSamples = Math.floor(sampleRate * durationSeconds);
    19	  const dataSize = numSamples * blockAlign;
    20	  const buffer = Buffer.alloc(44 + dataSize);
    21	
    22	  buffer.write('RIFF', 0);
    23	  buffer.writeUInt32LE(36 + dataSize, 4);
    24	  buffer.write('WAVE', 8);
    25	
    26	  buffer.write('fmt ', 12);
    27	  buffer.writeUInt32LE(16, 16);
    28	  buffer.writeUInt16LE(1, 20); // PCM
    29	  buffer.writeUInt16LE(numChannels, 22);
    30	  buffer.writeUInt32LE(sampleRate, 24);
    31	  buffer.writeUInt32LE(byteRate, 28);
    32	  buffer.writeUInt16LE(blockAlign, 32);
    33	  buffer.writeUInt16LE(bitsPerSample, 34);
    34	
    35	  buffer.write('data', 36);
    36	  buffer.writeUInt32LE(dataSize, 40);
    37	
    38	  return buffer;
    39	}
    40	
    41	const TINY_PNG = Buffer.from(
    42	  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=',
    43	  'base64'
    44	);
    45	
    46	async function setupMockRoutes(
    47	  page: Page,
    48	  fixtureKey: 'standard' | 'longTitle' | 'threeMinutes' = 'standard'
    49	): Promise<void> {
    50	  const fixture = fixtures[fixtureKey];
    51	  await page.route('**/*', async (route) => {
    52	    const req = route.request();
    53	    const url = new URL(req.url());
    54	
    55	    if (url.hostname !== '127.0.0.1' && url.hostname !== 'localhost') {
    56	      return route.abort();
    57	    }
    58	
    59	    if (url.pathname.startsWith('/api/v1/lyrics/')) {
    60	      return route.fulfill({
    61	        status: 200,
    62	        contentType: 'application/json',
    63	        body: JSON.stringify(fixture),
    64	      });
    65	    }
    66	
    67	    if (url.pathname.startsWith('/media/thumbnails/')) {
    68	      return route.fulfill({
    69	        status: 200,
    70	        contentType: 'image/png',
    71	        body: TINY_PNG,
    72	      });
    73	    }
    74	
    75	    if (url.pathname.startsWith('/media/')) {
    76	      const durSec = (fixture.duration_ms || 300000) / 1000;
    77	      const wav = createSilentWavBuffer(durSec);
    78	      const rangeHeader = req.headers()['range'];
    79	      if (rangeHeader) {
    80	        const match = /bytes=(\d+)-(\d*)/.exec(rangeHeader);
    81	        if (match) {
    82	          const start = parseInt(match[1], 10);
    83	          const end = match[2] ? parseInt(match[2], 10) : wav.length - 1;
    84	          const chunk = wav.subarray(start, end + 1);
    85	          return route.fulfill({
   345	             shell: bool = False) -> tuple[int, str, str]:
   346	    """Execute a pre-check gate with real-time terminal feedback."""
   347	    print(f"{CYAN}⏳ [Pre-check]{RESET} {label} ... ", end="", file=sys.stderr, flush=True)
   348	    code, out, err = execute(command, root, timeout, shell=shell)
   349	    combined = (out + err).rstrip()
   350	    if code is None:
   351	        print(f"{RED}❌ TIMEOUT ({timeout}s){RESET}", file=sys.stderr, flush=True)
   352	        raise PreconditionFailedError(label, f"timed out after {timeout} seconds", combined)
   353	    if code != 0:
   354	        print(f"{RED}❌ FAILED (exit {code}){RESET}", file=sys.stderr, flush=True)
   355	        raise PreconditionFailedError(label, f"failed with exit code {code}", combined)
   356	    print(f"{GREEN}✅ PASS{RESET}", file=sys.stderr, flush=True)
   357	    return code, out, err
   358	
   359	
   360	def fact(label: str, code: int | None, out: str, err: str) -> str:
   361	    return f"$ {label}\nexit {code if code is not None else 'timeout'}\n{(out + err).rstrip()}\n"
   362	
   363	
   364	def collect_facts(root: Path, epic_dir: str, base: str, hld_text: str, timeout: int) -> tuple[str, str]:
   365	    audit = [sys.executable, str(SCRIPTS / "audit_epic.py"), "--epic-dir", epic_dir, "--base", base]
   366	    audit_code, audit_out, audit_err = run_gate("audit_epic.py", audit, root, timeout)
   367	    audit_output = fact("audit_epic.py", audit_code, audit_out, audit_err)
   368	    results, reports = [], []
   369	    for line in parse_integration_results(hld_text):
   370	        command, _, report = line.strip().strip("`").partition(" -> ")
   371	        cmd = command.strip().strip("`")
   372	        report = report.strip().strip("`")
   373	        cmd_code, cmd_out, cmd_err = run_gate(f"Integration: {cmd}", cmd, root, timeout, shell=True)
   374	        results.append(fact(cmd, cmd_code, cmd_out, cmd_err))
   375	        reports.extend(report.split())
   376	    roots = re.search(r"^Integration test roots:\s*(.+)$", hld_text, re.MULTILINE)
   377	    if roots and reports:
   378	        results_paths = ["build/test-results"] if (root / "build/test-results").is_dir() else [r.strip("`") for r in reports]
   379	        roots_list = [r.strip("`") for r in roots.group(1).strip().split()]
   380	        check = [sys.executable, str(SCRIPTS / "check_bdd_traceability.py"), "tests", "--scenarios",
   381	                 f".devtool/epic/{epic_dir}/bdd_scenarios.en.md", "--roots", *roots_list,
   382	                 "--results", *results_paths]
   383	        chk_code, chk_out, chk_err = run_gate("check_bdd_traceability.py", check, root, timeout)
   384	        results.append(fact(shlex.join(check[1:]), chk_code, chk_out, chk_err))
   385	    return audit_output, "\n".join(results) or "No Integration results declared.\n"
   386	
   387	
   388	def artefact_lines(root: Path, epic_dir: str) -> str:
   389	    folder = root / ".devtool" / "epic" / epic_dir
   390	    names = sorted(p.name for p in folder.glob("*.md"))
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
322:    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()

exec
/bin/zsh -lc "rg -n 'mock|Tier C|Integration results|Playwright|smoke' scripts/test_verifiable_handoff_text.py scripts/test_verifiable_handoff.py scripts/test_lifecycle_document_contract.py skills/dev-implementation/resources/scripts/test_result_reports.py; nl -ba skills/quality_check/resources/scripts/validate_quality_contract.py | sed -n '430,510p'; nl -ba skills/quality_check/resources/scripts/validate_quality_contract.py | sed -n '580,680p'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/api_contract.md | sed -n '1,70p'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/architecture_and_flow.md | sed -n '1,65p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
scripts/test_verifiable_handoff.py:33:Integration results: python3 {JUNIT} --junitxml build/r.xml tests/test_demo.py -> build/r.xml
scripts/test_verifiable_handoff.py:43:Scenario: [DEMO-HP-01] [Tier C - Integration] Demo
scripts/test_verifiable_handoff_text.py:35:            "Integration results:", "Verification Environment",
scripts/test_verifiable_handoff_text.py:57:            "audit_epic.py", "Integration results", "tests --results",
   430	
   431	
   432	def reconcile_results(
   433	    execution_plan: list[dict[str, Any]] | dict[str, Any],
   434	    provider_results: list[dict[str, Any]],
   435	    expected_sha: str | None = None,
   436	) -> dict[str, Any]:
   437	    """Reconcile collected provider results against the execution plan."""
   438	    findings: list[dict[str, Any]] = []
   439	
   440	    if isinstance(execution_plan, dict):
   441	        plan_entries = execution_plan.get("providers", execution_plan.get("plan", []))
   442	        expected_sha = expected_sha or execution_plan.get("repository_sha")
   443	    else:
   444	        plan_entries = execution_plan
   445	
   446	    if expected_sha is None and plan_entries:
   447	        for pe in plan_entries:
   448	            if isinstance(pe, dict) and pe.get("repository_sha"):
   449	                expected_sha = pe.get("repository_sha")
   450	                break
   451	
   452	    results_by_id: dict[str, list[dict[str, Any]]] = {}
   453	
   454	    for res in provider_results:
   455	        p_id = res.get("provider_id", "")
   456	        results_by_id.setdefault(p_id, []).append(res)
   457	
   458	        # Validate commit SHA and drift across all results
   459	        res_sha = res.get("repository_sha")
   460	        start_sha = res.get("started_head")
   461	        fin_sha = res.get("finished_head")
   462	        if start_sha != res_sha or fin_sha != res_sha:
   463	            findings.append(
   464	                _finding(
   465	                    "sha_drift",
   466	                    f"Provider '{p_id}' started_head or finished_head does not match repository_sha",
   467	                    provider_id=p_id,
   468	                )
   469	            )
   470	        if expected_sha and (res_sha != expected_sha or start_sha != expected_sha or fin_sha != expected_sha):
   471	            findings.append(
   472	                _finding(
   473	                    "sha_mismatch",
   474	                    f"Provider '{p_id}' result SHA does not match expected candidate SHA '{expected_sha}'",
   475	                    provider_id=p_id,
   476	                )
   477	            )
   478	
   479	        # Anti-False-PASS internal consistency check for each result
   480	        top_status = res.get("status")
   481	        if top_status == "PASS":
   482	            for chk in res.get("checks", []):
   483	                if isinstance(chk, dict) and chk.get("status") in {"FAIL", "BLOCKED"}:
   484	                    findings.append(
   485	                        _finding(
   486	                            "contract_violation",
   487	                            f"Provider '{p_id}' reported PASS but check '{chk.get('id')}' has status '{chk.get('status')}'",
   488	                            provider_id=p_id,
   489	                        )
   490	                    )
   491	            cov = res.get("coverage", {})
   492	            if isinstance(cov, dict):
   493	                for metric, m_cov in cov.items():
   494	                    if isinstance(m_cov, dict):
   495	                        meas = m_cov.get("measured")
   496	                        thresh = m_cov.get("threshold")
   497	                        if thresh is not None and isinstance(meas, (int, float)) and isinstance(thresh, (int, float)):
   498	                            if meas < thresh:
   499	                                findings.append(
   500	                                    _finding(
   501	                                        "coverage_deficit",
   502	                                        f"Provider '{p_id}' reported PASS but measured coverage {meas} is below threshold {thresh} in '{metric}'",
   503	                                        provider_id=p_id,
   504	                                    )
   505	                                )
   506	
   507	    reconciled_results: list[dict[str, Any]] = []
   508	
   509	    for plan_entry in plan_entries:
   510	        p_id = plan_entry.get("id", "")
   580	        findings.append(_finding("missing_capabilities", "Missing or invalid 'capabilities' object"))
   581	        return {"status": "BLOCKED", "findings": _sort_findings(findings)}
   582	
   583	    if len(capabilities) == 0:
   584	        findings.append(_finding("empty_capabilities", "Capabilities object is empty"))
   585	
   586	    for cap_name, cap_val in capabilities.items():
   587	        if cap_name == "coverage":
   588	            if not isinstance(cap_val, dict):
   589	                findings.append(_finding("invalid_coverage_config", "Coverage capability must be an object", capability=cap_name))
   590	                continue
   591	            cmd = cap_val.get("command")
   592	            if not isinstance(cmd, list) or not all(isinstance(arg, str) for arg in cmd):
   593	                findings.append(
   594	                    _finding(
   595	                        "invalid_command_format",
   596	                        f"Coverage command for '{cap_name}' must be an array of string arguments",
   597	                        capability=cap_name,
   598	                    )
   599	                )
   600	            elif len(cmd) == 0:
   601	                findings.append(
   602	                    _finding(
   603	                        "command_array_empty",
   604	                        f"Coverage command for '{cap_name}' has an empty command array []",
   605	                        capability=cap_name,
   606	                    )
   607	                )
   608	            threshold = cap_val.get("threshold")
   609	            if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1.0:
   610	                findings.append(_finding("invalid_coverage_threshold", "Coverage threshold must be between 0.0 and 1.0", capability=cap_name))
   611	        else:
   612	            if not isinstance(cap_val, list) or not all(isinstance(arg, str) for arg in cap_val):
   613	                findings.append(
   614	                    _finding(
   615	                        "invalid_command_format",
   616	                        f"Capability command for '{cap_name}' must be an array of string arguments",
   617	                        capability=cap_name,
   618	                    )
   619	                )
   620	            elif len(cap_val) == 0:
   621	                findings.append(
   622	                    _finding(
   623	                        "command_array_empty",
   624	                        f"Capability '{cap_name}' has an empty command array []",
   625	                        capability=cap_name,
   626	                    )
   627	                )
   628	
   629	    profiles = manifest_data.get("profiles")
   630	    if not isinstance(profiles, dict):
   631	        findings.append(_finding("missing_profiles", "Missing or invalid 'profiles' object"))
   632	        return {"status": "BLOCKED", "findings": _sort_findings(findings)}
   633	
   634	    profile_caps = profiles.get(requested_profile)
   635	    if profile_caps is None:
   636	        findings.append(
   637	            _finding(
   638	                "profile_not_configured",
   639	                f"Requested profile '{requested_profile}' is not configured in profiles",
   640	                profile=requested_profile,
   641	            )
   642	        )
   643	    elif not isinstance(profile_caps, list):
   644	        findings.append(_finding("invalid_profile_format", f"Profile '{requested_profile}' must be an array of capability names", profile=requested_profile))
   645	    else:
   646	        if len(profile_caps) == 0:
   647	            findings.append(_finding("empty_profile_selection", f"Profile '{requested_profile}' has empty capability selection", profile=requested_profile))
   648	        for cap in profile_caps:
   649	            if cap not in capabilities:
   650	                findings.append(
   651	                    _finding(
   652	                        "missing_capability_definition",
   653	                        f"Profile '{requested_profile}' requires capability '{cap}', which is not defined in capabilities",
   654	                        capability=cap,
   655	                    )
   656	                )
   657	
   658	    status = "BLOCKED" if findings else "PASS"
   659	    return {
   660	        "status": status,
   661	        "findings": _sort_findings(findings),
   662	    }
   663	
   664	
   665	def _load_json_arg(arg: str) -> Any:
   666	    import json
   667	    from pathlib import Path
   668	
   669	    p = Path(arg)
   670	    if p.exists() and p.is_file():
   671	        return json.loads(p.read_text())
   672	    return json.loads(arg)
   673	
   674	
   675	def main() -> int:
   676	    import argparse
   677	    import json
   678	    import sys
   679	
   680	    parser = argparse.ArgumentParser(description="Validate quality contracts and project manifests.")
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
    36	### 1.2. Universal API Response Envelope (`BaseResponseObject<T>`)
    37	
    38	Every REST JSON response emitted by `/api/*` endpoints MUST conform to the universal `BaseResponseObject<T>` wire schema:
    39	
    40	```json
    41	{
    42	  "success": true,
    43	  "code": "0000",
    44	  "message": "Success",
    45	  "data": { ... }
    46	}
    47	```
    48	
    49	#### Field Specifications
    50	* `success` (`boolean`, required): `true` for successful operations (HTTP status 2xx), `false` for client or server errors (HTTP status 4xx/5xx).
    51	* `code` (`string`, required): Standardized machine-readable status or error code. `"0000"` indicates success; error codes follow UPPER_SNAKE_CASE (e.g. `"NOT_FOUND"`, `"EMPTY_SLUG_LIST"`, `"AUTH_INVALID_CREDENTIALS"`).
    52	* `message` (`string`, required): Human-readable status description. Defaults to `"Success"` for successful operations, or a descriptive error explanation on failures.
    53	* `data` (`T | null`, required): The actual payload data (JSON object, array, primitive, or `null`). For HTTP 204 No Content responses mapped to 200 OK or error responses, `data` is `null`.
    54	
    55	#### Idempotency & Pass-Through Guarantees
    56	* **Idempotent Handling (Zero Double-Wrapping)**: If an outgoing response is already wrapped in `BaseResponseObject<T>` (containing `success`, `code`, and `data` keys), `AutoEnvelopeLayer` passes it through untouched without introducing nested envelopes.
    57	* **Streaming & Binary Bypass**: Server-Sent Events (`text/event-stream`), byte-range audio streaming (`audio/*`, HTTP 206), and non-API documentation or health check routes (`/healthz`, `/docs`, `/swagger-ui`, `/openapi.json`) are completely excluded from envelope wrapping.
    58	
    59	---
    60	
    61	## 2. Authentication, Session & Device Security (`/api/v1/auth/...`)
    62	
    63	### 2.1. Account Registration (`POST /api/v1/auth/register`)
    64	Registers a new user account with credentials.
    65	
    66	* **Method**: `POST`
    67	* **Path**: `/api/v1/auth/register`
    68	* **Request Payload**:
    69	  ```json
    70	  {
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
    12	## Table of Contents
    13	- [1. System Roles & Responsibilities](#1-system-roles--responsibilities)
    14	- [2. Pipeline 1: Align Studio Architecture & State Machine](#2-pipeline-1-align-studio-architecture--state-machine)
    15	- [3. Pipeline 2: TTS Studio Architecture & Worker Lifecycle](#3-pipeline-2-tts-studio-architecture--worker-lifecycle)
    16	- [4. Subprocess Isolation & Cancellation Fencing](#4-subprocess-isolation--cancellation-fencing)
    17	- [5. Error Codes & Retry Conventions](#5-error-codes--retry-conventions)
    18	
    19	## 1. System Roles & Responsibilities
    20	
    21	The system is partitioned into two decoupled, specialized sub-systems operating in a Producer-Consumer / Orchestrator-Worker relationship:
    22	
    23	```text
    24	┌────────────────────────────────────────────────────────────────────────┐
    25	│                        D3Nexus Control Plane                           │
    26	│  - Task Queue & Lease Scheduling (SQLite / PostgreSQL)                 │
    27	│  - Real-time State & SSE Broadcasting Hub (< 50ms)                     │
    28	│  - Dual-Pipeline Dispatcher: Align Studio & TTS Studio Engine          │
    29	│  - Cloud Quota Fallback Interceptor (HTTP 429 -> Local Worker Queue)   │
    30	│  - End-User Interactive Web UI & Mobile API Hub                        │
    31	│  - SOLE OWNER OF DATABASE PERSISTENCE                                  │
    32	│    (Atomic transaction: tracks, lyrics catalog, flashcards, speech)    │
    33	└───────────────────────────────────┬────────────────────────────────────┘
    34	                                    │ HTTP REST (X-Worker-Token)
    35	                                    │ + SSE Stream (< 50ms)
    36	                                    ▼
    37	┌────────────────────────────────────────────────────────────────────────┐
    38	│                        lyrics-sync Worker Fleet                        │
    39	│  - Pure Stateless Compute Node (macOS Apple Silicon MPS / Linux CUDA)  │
    40	│                                                                        │
    41	│  [Capability 1: Align Studio Pipeline]                                 │
    42	│  - Demucs v4 Vocal Stem Isolation & Audio Resampling                   │
    43	│  - Wav2Vec2 CTC Forced Alignment + Whisper ASR Fallback                │
    44	│  - LLM Boundary Alignment, Contextual Translation & Lexical Mining     │
    45	│                                                                        │
    46	│  [Capability 2: TTS Studio Pipeline]                                   │
    47	│  - High-Fidelity Neural Speech Synthesis (Kokoro-82M on MPS/CUDA)      │
    48	│  - Cloud Quota Fallback Task Execution (Offline Mac Mini Worker)       │
    49	│  - Multi-Speaker Dialogue Stitching & Word-Level Timing Extraction     │
    50	│  - Bilingual Script Generation & CEFR Lexical Filtering                │
    51	│                                                                        │
    52	│  - Strictly FORBIDDEN from direct database connections                 │
    53	│  - Automatic process-group fencing, memory purging & scratch cleanup   │
    54	└────────────────────────────────────────────────────────────────────────┘
    55	```
    56	
    57	### 1.1. Core Invariants
    58	1. **Stateless Compute Boundary**: `lyrics-sync` workers operate strictly as compute daemons. Workers **MUST NOT** possess direct database credentials (`DATABASE_URL`, PostgreSQL connection strings) and **MUST NOT** execute direct writes to the D3Nexus database.
    59	2. **Domain Ownership Boundary**: `D3Nexus` is the sole owner of persistent storage. Upon receiving completion payloads, D3Nexus atomically persists tracks, synchronized lyrics, vocabulary flashcards, and synthesized speech audio records.
    60	3. **Dual-Layer Control Plane**:
    61	   - **Primary Fast Channel**: Long-lived Server-Sent Events (SSE) connection (`GET /api/v1/align/tasks/{id}/stream` and `GET /api/v1/speech/jobs/{id}/events`) for sub-50ms operator cancellation and real-time telemetry.
    62	   - **Heartbeat & Telemetry Channel**: Periodic bidirectional heartbeats sent every `10.0 seconds` for lease renewal, hardware telemetry reporting, and fencing.
    63	
    64	### 1.2. Worker Queue Task Execution Priorities
    65	

exec
/bin/zsh -lc "python3 -B -c 'import sys, re
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,\"skills/dev-implementation/resources/scripts\")
import task_contract as contract
import result_reports as reports
epic=Path(\".devtool/epic/web_quality_check_and_integration_gate\")
hld=(epic/\"web_quality_check_and_integration_gate.en.md\").read_text()
line=contract.parse_integration_results(hld)[0]
command,_,report=line.partition(\" -> \")
print(\"HLD command:\",command)
print(\"HLD report:\",report,\"explicit_junit_output=\", \"--junitxml\" in command)
bdd=(epic/\"bdd_scenarios.en.md\").read_text()
happy=bdd.split(\"## Dimension 1: Happy Paths\",1)[1].split(\"## Dimension 2:\",1)[0]
print(\"Smoke source happy-path URLs:\",re.findall(r\"https?://["'^'"\\\\s]+\",happy))
print(\"Smoke source explicit screen/URL metadata:\", [line for line in happy.splitlines() if line.startswith((\"Target URL:\",\"Target Screen:\",\"Manual action:\",\"Observable outcome:\"))])
for event in ('\\''{\"type\":\"testStart\"}'\\'','\\''{\"type\":\"testStart\",\"test\":{\"id\":1,\"name\":\"WQG-HP-01\"}}\\n{\"type\":\"testDone\",\"testID\":1,\"result\":\"success\"}'\\''):
    with patch.object(Path,\"read_text\",return_value=event):
        try: print(\"Report early/malformed event:\",reports.load_files([Path(\"probe.json\")]))
        except reports.ReportError as error: print(\"Report early/malformed event:\",type(error).__name__,str(error))
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
HLD command: python3 -m pytest tests/
HLD report: build/test-results/pytest.xml explicit_junit_output= False
Smoke source happy-path URLs: []
Smoke source explicit screen/URL metadata: []
Report early/malformed event: ReportError probe.json is not a valid report: 'test'
Report early/malformed event: [Case(name='WQG-HP-01', classname='', status='passed')]

exec
/bin/zsh -lc "nl -ba scripts/test_verifiable_handoff_text.py | sed -n '1,160p'; nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '305,330p'; rg -n 'worktree_changes|worktree_status|porcelain|dirty|status_lines' skills/dev-implementation/resources/scripts/run_external_review.py; rg --files /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts /Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts | rg '(fixture|sample|schema)' | head -40" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
     1	#!/usr/bin/env python3
     2	"""Lock the verifiable task handoff statements in the skills a receiving agent reads.
     3	
     4	Run: python3 -m unittest scripts/test_verifiable_handoff_text.py
     5	"""
     6	from __future__ import annotations
     7	import pathlib
     8	import re
     9	import unittest
    10	
    11	ROOT = pathlib.Path(__file__).resolve().parents[1]
    12	SDD = "skills/subagent-driven-development/"
    13	
    14	
    15	def read(relative):
    16	    return (ROOT / relative).read_text(encoding="utf-8")
    17	
    18	
    19	class VerifiableHandoffText(unittest.TestCase):
    20	    def assert_present(self, relative, phrases):
    21	        text = read(relative)
    22	        for phrase in phrases:
    23	            self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")
    24	
    25	    def assert_absent(self, relative, phrases):
    26	        text = read(relative)
    27	        for phrase in phrases:
    28	            self.assertNotIn(phrase, text, f"{relative} still has {phrase!r}")
    29	
    30	    def test_vth_hp_06_dev_designer_states_the_task_contract(self):
    31	        self.assert_present("skills/dev-designer/SKILL.md", (
    32	            "Stop and Report If", "Decisions Already Made", "Allowed files:",
    33	            "RED: n/a", "(Gate 5)", "exactly one task",
    34	            "check_task_contract.py --design", "Protected paths:",
    35	            "Integration results:", "Verification Environment",
    36	            "references/verification-rows.md",
    37	        ))
    38	        self.assert_absent("skills/dev-designer/SKILL.md",
    39	                           ("Test & Verification Checklist",))
    40	        self.assert_present("skills/dev-designer/references/verification-rows.md", (
    41	            "Python", "Android", "Web", "iOS", "Rust", "Flutter",
    42	            "--junitxml", "--file-reporter json:", "--xunit-output", "nextest",
    43	        ))
    44	
    45	    def test_vth_hp_07_dev_implementation_states_recorder_and_gate(self):
    46	        path = "skills/dev-implementation/SKILL.md"
    47	        self.assert_present(path, (
    48	            "run_task_checks.py red", "run_task_checks.py verify",
    49	            "run_task_checks.py status", "evidence/<task_id>.json",
    50	            "check_task_contract.py",
    51	        ))
    52	        text = read(path)
    53	        start = text.index("### Phase 4")
    54	        end = text.index("### Phase 4.1")
    55	        phase4 = text[start:end]
    56	        positions = [phase4.index(p) for p in (
    57	            "audit_epic.py", "Integration results", "tests --results",
    58	            "@quality_check")]
    59	        self.assertEqual(positions, sorted(positions))
    60	        self.assertEqual(len(set(positions)), 4)
    61	
    62	    def test_vth_hp_08_dev_lifecycle_and_handoff_state_the_rules(self):
    63	        self.assert_present("skills/dev-lifecycle/SKILL.md", (
    64	            "audit_epic.py", "result-based traceability",
    65	            "check_task_contract.py --design",
    66	        ))
    67	        self.assert_present("skills/dev-lifecycle/references/handoff-template.md", (
    68	            "Never edit a task's Verification table",
    69	        ))
    70	
    71	    def test_vth_hp_09_sdd_prompts_treat_evidence_as_proof(self):
    72	        self.assert_present(SDD + "implementer-prompt.md", (
    73	            "run_task_checks.py red", "run_task_checks.py verify",
    74	            "the evidence file is the test evidence",
    75	        ))
    76	        self.assert_absent(SDD + "implementer-prompt.md",
    77	                           ("your report is the test evidence",))
    78	        self.assert_present(SDD + "task-reviewer-prompt.md", (
    79	            "run_task_checks.py status", "Critical",
    80	        ))
    81	
    82	    def test_vth_hp_13_review_choice_is_stated(self):
    83	        for path in ("skills/dev-implementation/SKILL.md",
    84	                     "skills/dev-lifecycle/SKILL.md"):
    85	            self.assert_present(path, (
    86	                "Review Choice", "Finish", "Cross-model review", "Claude CLI",
    87	                "Codex CLI", "run_external_review.py run",
    88	                "run_external_review.py check", "review_results.md",
    89	            ))
    90	        self.assert_present("skills/dev-lifecycle/SKILL.md",
    91	                            ("picking the review CLI for the developer",))
    92	
    93	    def test_vth_st_14_review_choice_follows_gate_4_and_loops(self):
    94	        self.assert_present("rules/CRITICAL_RULES.md", (
    95	            "after Gate 4 passes",
    96	            "Cross-model review must return to a full Gate 4 run",
    97	        ))
    98	        for path in ("skills/dev-lifecycle/SKILL.md",
    99	                     "skills/dev-implementation/SKILL.md"):
   100	            self.assert_present(path, (
   101	                "Gate 4 PASS → Review Choice",
   102	                "Finish → Gate 5",
   103	                "Cross-model review → Gate 4 in full",
   104	            ))
   105	
   106	        lifecycle = read("skills/dev-lifecycle/SKILL.md")
   107	        self.assertIn('EXEC --> G4', lifecycle)
   108	        self.assertIn('G4 -->|"yes"| RC', lifecycle)
   109	        self.assertIn('RC -->|"1. Finish"| REVIEW', lifecycle)
   110	        self.assertIn('XR -->|"round recorded"| G4', lifecycle)
   111	
   112	        implementation = read("skills/dev-implementation/SKILL.md")
   113	        self.assertIn('moretasks -- "no, epic done" --> phase4', implementation)
   114	        self.assertIn('phase4 -- "PASS" --> choice', implementation)
   115	        self.assertIn('choice -- "Finish" --> checkpoint4', implementation)
   116	        self.assertIn('review -- "round recorded" --> phase4', implementation)
   117	
   118	        for path in ("rules/CRITICAL_RULES.md",
   119	                     "skills/dev-lifecycle/SKILL.md",
   120	                     "skills/dev-implementation/SKILL.md",
   121	                     "docs/lifecycles.en.md",
   122	                     "docs/choosing-a-lifecycle.en.md"):
   123	            self.assert_absent(path, (
   124	                "Review Choice before Gate 4",
   125	                "Review Choice is mandatory before Gate 4",
   126	                "Review Choice) before Gate 4",
   127	            ))
   128	
   129	        self.assert_present("docs/lifecycles.en.md", (
   130	            "Every PASS presents **Review Choice**",
   131	            "returns to a full Gate 4 run",
   132	        ))
   133	        self.assert_present("docs/lifecycles.vi.md", (
   134	            "Mỗi lần PASS sẽ đưa ra **Review Choice**",
   135	            "quay lại chạy đầy đủ Cổng 4",
   136	        ))
   137	        self.assert_present("docs/choosing-a-lifecycle.en.md", (
   138	            "after every Gate 4 PASS",
   139	            "loop continues until you choose Finish",
   140	        ))
   141	        self.assert_present("docs/choosing-a-lifecycle.vi.md", (
   142	            "sau mỗi lần Cổng 4 PASS",
   143	            "vòng lặp tiếp tục cho tới khi bạn chọn Finish",
   144	        ))
   145	
   146	
   147	if __name__ == "__main__":
   148	    unittest.main()
   305	    """Print an unmistakable highlighted banner when a pre-check blocks AI invocation."""
   306	    bar = "=" * 74
   307	    lines = [
   308	        f"\n{RED}{bar}{RESET}",
   309	        f"{RED}🚨 [PRECONDITION BLOCKED] — {cli.upper()} CLI WAS NOT INVOKED (0 CREDITS USED){RESET}",
   310	        f"{RED}{bar}{RESET}",
   311	        f"{YELLOW}Failed Gate :{RESET} {error.gate}",
   312	        f"{YELLOW}Reason      :{RESET} {error.reason}",
   313	    ]
   314	    if error.details:
   315	        indented = "\n".join(f"  {line}" for line in error.details.splitlines()[-25:])
   316	        lines.append(f"{YELLOW}Details (last 25 lines):{RESET}\n{indented}")
   317	    lines.append(f"{RED}{bar}{RESET}\n")
   318	    print("\n".join(lines), file=sys.stderr, flush=True)
   319	
   320	
   321	def status_lines(root: Path) -> list[str]:
   322	    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()
   323	
   324	
   325	def head_of(root: Path) -> str:
   326	    return git_run(root, "rev-parse", "HEAD").decode().strip()
   327	
   328	
   329	def execute(command: list[str] | str, root: Path, timeout: int, prompt: str | None = None,
   330	            shell: bool = False) -> tuple[int | None, str, str]:
321:def status_lines(root: Path) -> list[str]:
322:    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()
644:    before = status_lines(root)
714:    before = status_lines(root)
735:    before = status_lines(root)
805:    if status_lines(root):
844:    before = status_lines(root)  # after the facts: running the test commands may write build output
877:    before = status_lines(root)
911:    changed = sorted(set(status_lines(root)) ^ set(before))
/Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts/fixtures/catalog-id-vectors.json
/Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts/fixtures/implicit-grading-vectors.json
/Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts/tests/schema-validation.test.ts
/Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts/schemas/track-document.schema.json
/Users/danhdueexoictif/AllProjects/D3Nexus/packages/contracts/schemas/catalog-index.schema.json

codex
Các probe chỉ đọc xác nhận: payload Task 01 hiện bị validator trả `BLOCKED`; test chỉ dùng mock vẫn được traceability chấp nhận; và báo cáo JSON Playwright không tạo ra test case nào trong parser hiện tại. Tôi cũng đang kiểm tra việc sinh smoke checklist sau PASS có làm vướng yêu cầu cây Git sạch ở Review Choice hay không.

exec
/bin/zsh -lc "python3 -B -c 'from pathlib import Path
import subprocess, os
for candidate in (\"/Library/Developer/CommandLineTools/usr/bin/git\",\"/Applications/Xcode.app/Contents/Developer/usr/bin/git\"):
    print(\"native git\",candidate,Path(candidate).is_file())
    if Path(candidate).is_file():
        env={**os.environ,\"GIT_OPTIONAL_LOCKS\":\"0\"}
        for args in ([\"rev-parse\",\"HEAD\"],[\"status\",\"--porcelain\"],[\"check-ignore\",\"-v\",\".devtool/epic/web_quality_check_and_integration_gate/manual_smoke_checklist.md\"]):
            result=subprocess.run([candidate,*args],capture_output=True,text=True,env=env)
            print(\"read-only git\",args,\"exit\",result.returncode,\"out\",result.stdout.strip(),\"err\",result.stderr.strip())
        break
'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
native git /Library/Developer/CommandLineTools/usr/bin/git True
read-only git ['rev-parse', 'HEAD'] exit 0 out c88539eeb74257e43fa573a3271ea2351931848e err 
read-only git ['status', '--porcelain'] exit 0 out  err 
read-only git ['check-ignore', '-v', '.devtool/epic/web_quality_check_and_integration_gate/manual_smoke_checklist.md'] exit 1 out  err 

exec
/bin/zsh -lc "nl -ba skills/dev-implementation/resources/scripts/run_external_review.py | sed -n '787,813p'; nl -ba skills/dev-designer/references/verification-rows.md | sed -n '1,155p'; nl -ba .devtool/epic/web_quality_check_and_integration_gate/task_06_automated_manual_smoke_checklist_generator.md | sed -n '19,54p'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/nexus/gaps_and_rfcs.md | sed -n '1,36p'; nl -ba /Users/danhdueexoictif/AllProjects/D3Nexus/shared-contracts/lyrics-sync/gaps_and_rfcs.md | sed -n '1,28p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
   787	        model_arg=args.model,
   788	        thinking_arg=getattr(args, "thinking_level", None),
   789	    )
   790	    args.cli = cli
   791	    args.model = model
   792	    args.thinking_level = thinking_level
   793	
   794	    if kind == "principal" and args.cli == "ollama":
   795	        print("--kind principal supports --cli claude, codex, or agy", file=sys.stderr)
   796	        return 2
   797	
   798	    if args.cli == "ollama":
   799	        if not args.model:
   800	            print("--cli ollama needs --model", file=sys.stderr)
   801	            return 2
   802	    elif not shutil.which(args.cli):
   803	        print(f"{args.cli} not found on PATH", file=sys.stderr)
   804	        return 2
   805	    if status_lines(root):
   806	        print("commit or stash your changes before a review", file=sys.stderr)
   807	        return 2
   808	    sha = head_of(root)
   809	
   810	    if kind == "principal":
   811	        return run_principal(root, args, sha)
   812	
   813	    if not args.epic_dir:
     1	# Verification Rows by Platform
     2	
     3	Example rows for a task's `## Verification` table, one set per platform, and the command that
     4	produces the test report a `TIER-C` row names after `results`. The table grammar is in
     5	[`SKILL.md`](../SKILL.md); here are only the platform commands.
     6	
     7	## Table of Contents
     8	
     9	- [How to Read the Examples](#how-to-read-the-examples)
    10	- [Python](#python)
    11	- [Android](#android)
    12	- [Web](#web)
    13	- [iOS](#ios)
    14	- [Rust](#rust)
    15	- [Flutter](#flutter)
    16	
    17	## How to Read the Examples
    18	
    19	- `RED` rows run before implementation and must fail for the right reason, so their Expect names
    20	  the failure (`exit 1; contains "ModuleNotFoundError"`). `GREEN` rows run the same command after
    21	  implementation. `TIER-B` rows are tooling and governance checks. `TIER-C` rows run integration
    22	  tests and name the report with `results <path>`.
    23	- Replace the paths, package names and flags with the project's own. The rows show the shape, not
    24	  the project's commands; use the commands the HLD's Integration Test Plan already names.
    25	- The `results` path must be ignored by git (for example `build/` in `.gitignore`), because the
    26	  report is rewritten on every run and is never committed.
    27	- A report that records a test passing is what proves a scenario identifier. The test name, tag or
    28	  description carries the identifier, and the framework writes it into the report.
    29	
    30	## Python
    31	
    32	| ID | Phase | Command | Expect | Needs |
    33	|----|-------|---------|--------|-------|
    34	| V1 | RED | `uv run pytest tests/unit/test_taxonomy.py` | exit 1; contains "ModuleNotFoundError" | — |
    35	| V2 | GREEN | `uv run pytest tests/unit/test_taxonomy.py` | exit 0; contains "passed" | — |
    36	| V3 | TIER-B | `uv run ruff check src tests` | exit 0 | — |
    37	| V4 | TIER-C | `uv run pytest tests/integration/test_taxonomy_bdd.py --junitxml=build/test-results/task_3.xml` | exit 0; results build/test-results/task_3.xml | — |
    38	
    39	Report: `pytest --junitxml=<path>`.
    40	
    41	## Android
    42	
    43	| ID | Phase | Command | Expect | Needs |
    44	|----|-------|---------|--------|-------|
    45	| V1 | RED | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartViewModelTest'` | exit 1; contains "FAILED" | — |
    46	| V2 | GREEN | `./gradlew :feature:cart:testDebugUnitTest --tests '*CartViewModelTest'` | exit 0; contains "BUILD SUCCESSFUL" | — |
    47	| V3 | TIER-B | `./gradlew spotlessCheck detekt :konsist-test:test apiCheck` | exit 0; contains "BUILD SUCCESSFUL" | — |
    48	| V4 | TIER-C | `./gradlew :app:testDebugUnitTest --tests '*CartFlowTest'` | exit 0; results app/build/test-results/testDebugUnitTest | — |
    49	
    50	Report: Gradle writes JUnit XML under `build/test-results/<task>/`. Name that directory after
    51	`results`; every `.xml` file inside it is read.
    52	
    53	## Web
    54	
    55	| ID | Phase | Command | Expect | Needs |
    56	|----|-------|---------|--------|-------|
    57	| V1 | RED | `npx vitest run src/cart/store.test.ts` | exit 1; contains "FAIL" | — |
    58	| V2 | GREEN | `npx vitest run src/cart/store.test.ts` | exit 0; contains "passed" | — |
    59	| V3 | TIER-B | `npx tsc --noEmit` | exit 0 | — |
    60	| V4 | TIER-C | `PLAYWRIGHT_JUNIT_OUTPUT_FILE=build/test-results/e2e.xml npx playwright test tests/e2e/cart.spec.ts --reporter=junit` | exit 0; results build/test-results/e2e.xml | — |
    61	
    62	Report: choose the reporter that writes JUnit XML.
    63	
    64	- `node --test --test-reporter=junit --test-reporter-destination=<path>`
    65	- `vitest --reporter=junit --outputFile=<path>`
    66	- `playwright test --reporter=junit`, with the file set by the `PLAYWRIGHT_JUNIT_OUTPUT_FILE`
    67	  environment variable or the `outputFile` option of the reporter in `playwright.config`.
    68	
    69	## iOS
    70	
    71	| ID | Phase | Command | Expect | Needs |
    72	|----|-------|---------|--------|-------|
    73	| V1 | RED | `swift test --package-path Packages/Cart --filter CartReducerTests` | exit 1; contains "error" | — |
    74	| V2 | GREEN | `swift test --package-path Packages/Cart --filter CartReducerTests` | exit 0; contains "passed" | — |
    75	| V3 | TIER-B | `swiftlint lint --strict --config quality/.swiftlint.yml` | exit 0 | — |
    76	| V4 | TIER-C | `swift test --package-path Packages/Cart --filter CartFlowTests --xunit-output build/test-results/cart.xml` | exit 0; results build/test-results/cart.xml | — |
    77	
    78	Report: `swift test --xunit-output <path>`. XCTest results go to the named file. Swift Testing
    79	writes its results to a second file beside it, so pass the directory after `results` when the
    80	tests use Swift Testing. Converting an `.xcresult` bundle to JUnit is the project's job: add a
    81	script to the repository and run it in the row's command; this kit does not read `.xcresult`.
    82	
    83	## Rust
    84	
    85	| ID | Phase | Command | Expect | Needs |
    86	|----|-------|---------|--------|-------|
    87	| V1 | RED | `cargo test -p cart --lib totals` | exit non-zero; contains "error" | — |
    88	| V2 | GREEN | `cargo test -p cart --lib totals` | exit 0; contains "test result: ok" | — |
    89	| V3 | TIER-B | `cargo clippy --all-targets -- -D warnings` | exit 0 | — |
    90	| V4 | TIER-C | `cargo nextest run -p cart --test '*' --profile ci` | exit 0; results target/nextest/ci/junit.xml | — |
    91	
    92	Report: `cargo nextest` with a JUnit section in `.config/nextest.toml`:
    93	
    94	```toml
    95	[profile.ci.junit]
    96	path = "junit.xml"
    97	```
    98	
    99	nextest writes the file to `target/nextest/<profile>/junit.xml`.
   100	
   101	## Flutter
   102	
   103	| ID | Phase | Command | Expect | Needs |
   104	|----|-------|---------|--------|-------|
   105	| V1 | RED | `fvm flutter test test/cart/cart_bloc_test.dart` | exit 1; contains "Some tests failed" | — |
   106	| V2 | GREEN | `fvm flutter test test/cart/cart_bloc_test.dart` | exit 0; contains "All tests passed" | — |
   107	| V3 | TIER-B | `fvm flutter analyze` | exit 0; contains "No issues found" | — |
   108	| V4 | TIER-C | `fvm flutter test integration_test/cart_flow_test.dart --file-reporter json:build/test-results/cart.json` | exit 0; results build/test-results/cart.json | — |
   109	
   110	Report: `flutter test --file-reporter json:<path>`, which writes the Dart JSON test events that
   111	`results` reads.
    19	## Requirement Analysis
    20	
    21	Build the automated smoke checklist generator script `generate_smoke_checklist.py` and hook it into Phase 4 of `dev-implementation`. The script parses the canonical BDD Happy Path scenarios (`bdd_scenarios.en.md`), extracts 3 to 5 core user journey steps, and formats them into a clean markdown document at `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`. This gives the human engineer an instant 2-minute manual sanity check checklist upon Gate 4 completion.
    22	
    23	## Files
    24	
    25	Allowed files:
    26	- `skills/dev-implementation/resources/scripts/generate_smoke_checklist.py` (new)
    27	- `skills/dev-implementation/SKILL.md`
    28	- `tests/test_smoke_checklist_generator.py` (new)
    29	
    30	Read-only context:
    31	- `.devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md` (source BDD contract)
    32	- `skills/dev-implementation/SKILL.md` (Phase 4 integration point)
    33	
    34	## Design Rationale
    35	
    36	Even with 100% automated testing, human developers naturally want to perform a quick sanity check before release. Without structured guidance, this exploratory testing often takes 20-30 minutes of aimless clicking. Automatically generating a focused 3-5 step walkthrough directly from the approved BDD Happy Paths concentrates human verification into a rapid 2-minute validation loop.
    37	
    38	## Impact Analysis & Blast Radius
    39	
    40	- **Target Files & Symbols**: `generate_smoke_checklist.py`, `dev-implementation/SKILL.md`.
    41	- **Downstream Callers**: `dev-implementation` Phase 4 upon Gate 4 pass.
    42	- **Cross-Platform Bridges**: None.
    43	- **Target Test Coverage Threshold**: $\ge 85\%$ for `generate_smoke_checklist.py`.
    44	
    45	### BDD SCENARIOS
    46	
    47	Covers: [WQG-HP-04]
    48	
    49	#### Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
    50	Given all tasks in an epic reach status `done` and Gate 4 returns `PASS`
    51	When the smoke generator parses primary BDD Happy Path scenarios
    52	Then it emits `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
    53	And the checklist contains between 3 and 5 actionable verification steps with URLs and expected visual outcomes.
    54	
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
    14	## Table of Contents
    15	- [1. Open Gaps & Alignment Questions (For D3Nexus Confirmation)](#1-open-gaps--alignment-questions-for-d3nexus-confirmation)
    16	- [2. Accepted RFCs & Architectural Decisions](#2-accepted-rfcs--architectural-decisions)
    17	- [3. D3Nexus Review & Feedback](#3-d3nexus-review--feedback)
    18	- [4. TTS Studio Gaps & Open Inquiries](#4-tts-studio-gaps--open-inquiries)
    19	- [5. Lexical & Collocation RFCs](#5-lexical--collocation-rfcs)
    20	
    21	---
    22	
    23	## 1. Open Gaps & Alignment Questions (For D3Nexus Confirmation)
    24	
    25	### GAP-01: Axum Request Body Size Limit on Task Completion (`POST /complete`)
    26	* **Observation**:
    27	  Full alignment payloads containing word-level timestamps (`Word`), bilingual sentence translations, and comprehensive 10-field lexical chunks (`all_collocations`) can range from `500 KB` to `5 MB` for long videos (e.g. 10-15 minute speeches or audio tracks). Axum's default `DefaultBodyLimit` is `2 MB`.
    28	* **Current Behavior**:

exec
/bin/zsh -lc "cat /Users/danhdueexoictif/.codex/plugins/cache/danhdue-agent-tools/d3nexus/1.23.0/skills/verification-before-completion/SKILL.md; nl -ba .devtool/epic/web_quality_check_and_integration_gate/2026-11-04-web-quality-check-and-integration-gate-design.en.md | sed -n '108,124p'; nl -ba .devtool/epic/web_quality_check_and_integration_gate/web_quality_check_and_integration_gate.en.md | sed -n '113,153p'" in /Users/danhdueexoictif/AllProjects/ai-agent-tools
 succeeded in 0ms:
---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness
   108	## Dev-Designer and Dev-Implementation Enhancements
   109	
   110	1. **`dev-designer` (Stage 2)**:
   111	   - When detecting a Web project, the HLD `Integration results:` line must target Playwright headless output (`build/test-results/playwright.json`).
   112	   - BDD scenarios for Tier C must include concrete DOM interaction expectations and wiremock assertions.
   113	2. **`dev-implementation` (Stage 3)**:
   114	   - Integrates the Anti-Rationalization Table into task execution.
   115	   - Validates that tasks claiming Tier C scenario coverage execute real headless browser or subcutaneous tests.
   116	   - Halts and reports `BLOCKED` if test code mocks the component under test.
   117	
   118	## Automated Smoke Walkthrough Generation
   119	
   120	Upon successful completion of all tasks and a passing Gate 4 machine verdict, `dev-implementation` automatically generates a human-oriented verification artifact:
   121	- Path: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
   122	- Content: 3 to 5 concise, actionable manual steps extracted directly from the primary BDD Happy Path scenarios (e.g. Target URL, user action, observable visual outcome).
   123	- Benefit: Reduces developer exploratory testing from 30 minutes of unstructured wandering to a 2-minute deterministic confirmation.
   124	
   113	### Integration Test Plan and Boundary Matrix
   114	
   115	```text
   116	Integration test roots: tests/, skills/web-quality-check/tests/
   117	Protected paths: .agents/quality/**, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.en.md, .devtool/epic/web_quality_check_and_integration_gate/bdd_scenarios.vi.md
   118	Integration results: python3 -m pytest tests/ -> build/test-results/pytest.xml
   119	```
   120	
   121	| Boundary Seam | Testing Strategy | Verification Target |
   122	| :--- | :--- | :--- |
   123	| Provider Contract | Mock `quality_check` invocation payload | Verify status aggregation and schema conformance |
   124	| Astro Web / TypeScript | Headless Playwright + Wiremock fixture | Verify DOM elements, Custom Elements, and zero console errors |
   125	| Vanilla JS Preview | `tsc --project jsconfig.json` + Playwright | Verify type safety without `.ts` migration, and page crash prevention |
   126	| Task Workflow Engine | BDD traceability & Anti-Rationalization audit | Verify tasks rejecting fake Tier C mocks and requiring real integration runs |
   127	
   128	## Verification Environment
   129	
   130	- Execution environment: Local macOS / Linux CLI with Node.js v20+, Python 3.11+, and Playwright Chromium browser installed.
   131	- No live network dependencies: All external network calls in tests are intercepted at the socket boundary.
   132	- File system isolation: Test runs operate in temporary isolated directories without mutating working git trees.
   133	
   134	### Comprehensive BDD Test Scenarios
   135	
   136	The suite covers all 5 dimensions under the `[WQG-]` prefix:
   137	1. **Happy Paths (`WQG-HP-xx`)**: Successful provider execution, Playwright headless pass, clean Vanilla JS type check, and smoke checklist generation.
   138	2. **Edge Cases (`WQG-EC-xx`)**: Missing capabilities, partial web configs, empty test suites, and third-party console warnings.
   139	3. **State Transitions (`WQG-ST-xx`)**: Dynamic transition from `BLOCKED` to `PASS` upon fixing configuration, and task status synchronization.
   140	4. **Async & Concurrency (`WQG-AR-xx`)**: Concurrent provider fan-out in Gate 4, non-blocking Playwright webServer startup.
   141	5. **Failures & Resilience (`WQG-FR-xx`)**: Console error detection triggering immediate failure, uncaught exception traps, and broken contract detection.
   142	
   143	## Shared Contract Impact
   144	
   145	None — self-contained quality provider and workflow enhancement.
   146	
   147	## Rollout Strategy and Mitigation
   148	
   149	- **Phase 1**: Author `web-quality-check` skill and validate its contract with unit and integration tests.
   150	- **Phase 2**: Add Playwright Zero-Console-Error watchdog and Vanilla JS `jsconfig.json` checker.
   151	- **Phase 3**: Update `dev-designer`, `dev-implementation`, and `test-driven-development` with Anti-Rationalization Tables and Subcutaneous Testing guidelines.
   152	- **Phase 4**: Configure polyglot registries in `D3Nexus` and `lyrics-sync`, verifying Gate 4 multi-provider execution.
   153	

codex
Six implementation blockers remain. I reviewed all 13 artefacts against `c88539eeb74257e43fa573a3271ea2351931848e`. Read-only probes confirmed the contract and report incompatibilities below; Git remained clean.

Artefact paths below are relative to `.devtool/epic/web_quality_check_and_integration_gate/`. Apply corresponding changes to EN/VI mirrors.

Verdict: CHANGES REQUIRED
[Important] task_01_web_quality_check_skill_and_contract.md:Decisions Already Made — The frozen output includes forbidden top-level `summary` and omits eight required v1 fields. The canonical [schema](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/quality_check/resources/schemas/provider-result.schema.json:5) requires these fields; executing the existing validator with the frozen payload returned BLOCKED with profile, duration, and SHA-drift findings. Proposed: Replace the frozen output definition with the complete canonical result schema and require the contract test to validate and reconcile the actual emitted document.
[Important] web_quality_check_and_integration_gate.en.md:Integration Test Plan and Boundary Matrix; 2026-11-04-web-quality-check-and-integration-gate-design.en.md:Dev-Designer and Dev-Implementation Enhancements — The HLD command does not request creation of `pytest.xml`, while the spec mandates Playwright JSON, which the current [report reader](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/result_reports.py:83) interprets as Dart events. An active probe returned zero cases for a passing Playwright JSON report. Gate 4 explicitly consumes these reports for [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/SKILL.md:270). Proposed: Add `--junitxml=build/test-results/pytest.xml` to the HLD command and standardize browser evidence on the existing supported Playwright JUnit configuration.
[Important] task_05_anti_rationalization_and_doubt_driven_workflow.md:BDD SCENARIOS / Files — WQG-ST-02 promises mechanical rejection of mock-only completion, but Allowed files permit only skill text and a new test. Existing [traceability](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/check_bdd_traceability.py:157) matches identifiers, and the [done gate](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/task_contract.py:439) judges recorded case statuses. Probes accepted a mock-only test reference and its passing result. Proposed: Define the semantic auditor responsible for rejection, wire its verdict into completion gating, authorize the affected production files, and test that actual rejection path.
[Important] task_04_polyglot_gate4_registry_and_fanout.md:Requirement Analysis / Files — The promised consumer registration has no executable adoption path. The existing [scaffolder](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/setup_quality_check/resources/scripts/scaffold_quality_manifest.py:244) generates configurations from `PLATFORM_CONFIGS`, without loading the proposed template; a read-only dry-run probe rejected platform `web`. Neither scaffolder changes nor consumer adoption handoffs are assigned. Proposed: Authorize and specify web scaffolder integration, capability-manifest generation, and separate repository-owned adoption handoffs covering registry entries, watchdog attachment, and verification commands.
[Important] task_06_automated_manual_smoke_checklist_generator.md:Requirement Analysis / BDD SCENARIOS — Generating the checklist after Gate 4 PASS creates an unignored file under the tracked epic directory. `git check-ignore` confirmed this path is not ignored, and the [review runner](/Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/dev-implementation/resources/scripts/run_external_review.py:805) rejects dirty trees. Committing afterward changes the certified candidate SHA. Proposed: Generate and commit the checklist before resolving the final candidate SHA, then run full Gate 4 before presenting Review Choice.
[Important] task_06_automated_manual_smoke_checklist_generator.md:Decisions Already Made / WQG-HP-04 — The generator must extract URLs and visual outcomes from arbitrary Happy Paths, but its supplied canonical BDD contains provider/compiler workflows without target URLs or structured manual-step metadata. The executor must invent information or fail the frozen requirement. Proposed: Define explicit smoke metadata containing a URL or CLI command, action, and observable outcome; specify behavior when metadata is absent; and align the scenario and generator contract accordingly.


tokens used
156,489
````
