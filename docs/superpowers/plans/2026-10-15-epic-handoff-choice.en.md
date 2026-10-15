# Epic Handoff Choice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After Gate 2, let the developer package an epic for later or for another LLM, and let `dev-implementation` work out from disk where any epic stands and resume it at the right point.

**Architecture:** Skill-text changes plus one template. `dev-lifecycle` gains the Handoff Choice, the packaging procedure and a Resuming an Epic rule; `dev-designer` hands control back to the choice; `dev-implementation` gains epic-name resolution, Entry-Point Detection and a Resume Procedure. The kit's existing scripts do every mechanical step.

**Tech Stack:** Markdown skill files; the existing `compute_execution_order.py`, `check_bdd_traceability.py`, `sync_task_status.py` and `check_document.py`; git; bash.

**Spec:** [2026-10-15-epic-handoff-choice-design.en.md](../specs/2026-10-15-epic-handoff-choice-design.en.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Tasks](#tasks)
  - [Task 1: Handoff Choice and Packaging](#task-1-handoff-choice-and-packaging)
  - [Task 2: Entry-Point Detection and Resume](#task-2-entry-point-detection-and-resume)
- [Final Verification](#final-verification)

## Global Constraints

- The five gates stay unchanged. The Handoff Choice is a routing decision, not a sixth gate.
- `handoff.md` is English-only with a complete table of contents, and is never updated after packaging.
- Packaging leaves task statuses unchanged and sets the overview Status to `Packaged`.
- Never push without the developer's explicit permission.
- No new scripts; reuse the kit's existing ones.
- Entry-point state comes from disk: `handoff.md`, the overview Status, task statuses, the epic branch and the worktree.
- A resumed epic re-confirms Gate 3 for its remaining tasks, and `git worktree add -b` never runs for an existing branch.
- `SKILL.md` frontmatter stays exactly `name` + `description`.
- Commits: `[SKILLS] <title>` plus a bullet body; never any trailer line.
- Steps 1 and 8 of Task 1 and Steps 1 and 6 of Task 2 dispatch fresh subagents to test the skill text. An implementer that cannot dispatch subagents reports back, and the controller runs those steps. `<ROOT>` in their prompts is the output of `git rev-parse --show-toplevel` in the executing checkout.
- Dry runs happen in a throwaway repository under `mktemp -d`, never in this repository.

## File Structure

| File | Responsibility |
|------|----------------|
| `skills/dev-lifecycle/references/handoff-template.md` | Create. The `handoff.md` template |
| `skills/dev-lifecycle/SKILL.md` | Modify. Handoff Choice, packaging procedure, Resuming an Epic, diagram, Document Contract, red flags |
| `skills/dev-designer/SKILL.md` | Modify. Step 3 returns to the Handoff Choice |
| `skills/dev-implementation/SKILL.md` | Modify. Epic resolution, Entry-Point Detection, Resume Procedure, status change, diagram, red flags |
| `scripts/test_lifecycle_document_contract.py` | Modify. Locks the new phrases |

## Tasks

### Task 1: Handoff Choice and Packaging

**Files:**

- Create: `skills/dev-lifecycle/references/handoff-template.md`
- Modify: `skills/dev-lifecycle/SKILL.md`
- Modify: `skills/dev-designer/SKILL.md`
- Modify: `scripts/test_lifecycle_document_contract.py`

**Interfaces:**

- Consumes: `compute_execution_order.py`, `check_bdd_traceability.py plan`, `sync_task_status.py epic` and `check_document.py --require-toc`, all already on `main`.
- Produces: the template `skills/dev-lifecycle/references/handoff-template.md`, the headings `### Resuming an Epic` (anchor `#resuming-an-epic`) and `### Handoff Choice` (anchor `#handoff-choice`), and the overview Status value `Packaged` that Task 2 detects.

- [ ] **Step 1: Baseline scenario (RED)**

Before editing anything, dispatch a fresh general-purpose subagent with this prompt and keep its reply:

```text
You are in the repository <ROOT>. Read skills/dev-lifecycle/SKILL.md and
skills/dev-designer/SKILL.md. You are orchestrating epic slug todo-export, epic directory
todo_export. dev-designer has just written and committed the HLD, the BDD scenarios and two task
files, and the developer confirmed the task breakdown. Do not run anything. Reply with exactly two
parts:
(1) what you do next, quoting any message you would send the developer;
(2) the developer answers "1" to your question, or, if you asked none, says "Stop here; another
LLM will implement this later". List, in order, every command you would run and every file you
would write, then the last message you would send.
```

Expected baseline: part (1) moves straight on to Stage 3 or `dev-implementation` without asking; part (2) has no `handoff.md` built from a template, no `Packaged` status and no preflight. Record the reply — Step 8 re-runs the same prompt.

- [ ] **Step 2: Lock the new contract (failing test)**

Contract test — in `scripts/test_lifecycle_document_contract.py`, replace:

```python
        "Granting Gate 4 without a passing traceability check",
    ),
```

with:

```python
        "Granting Gate 4 without a passing traceability check",
        "Handoff Choice",
        "handoff-template.md",
        "Resuming an Epic",
        "Packaged",
    ),
```

Contract test — in `scripts/test_lifecycle_document_contract.py`, replace:

```python
        "at least one automated integration test",
    ),
```

with:

```python
        "at least one automated integration test",
        "Handoff Choice",
    ),
```

Run: `python3 scripts/test_lifecycle_document_contract.py`

Expected: exit 1 with these lines:

```text
  FAIL skills/dev-designer/SKILL.md: missing Handoff Choice
  FAIL skills/dev-lifecycle/SKILL.md: missing Handoff Choice
  FAIL skills/dev-lifecycle/SKILL.md: missing handoff-template.md
  FAIL skills/dev-lifecycle/SKILL.md: missing Resuming an Epic
  FAIL skills/dev-lifecycle/SKILL.md: missing Packaged
```

- [ ] **Step 3: Create the handoff template**

Run from the repository root. The heredoc is indented two spaces so that this plan's own table-of-contents check does not read the template's headings; `sed` removes the indent:

````bash
mkdir -p skills/dev-lifecycle/references
sed 's/^  //' > skills/dev-lifecycle/references/handoff-template.md <<'EOF'
  # Handoff: <epic_slug>

  ## Table of Contents

  - [Status](#status)
  - [Identifiers](#identifiers)
  - [Read First](#read-first)
  - [Resume Prompt](#resume-prompt)
  - [Open Notes](#open-notes)
  - [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

  ## Status

  - **Packaged**: <YYYY-MM-DD>
  - **Design commit**: `<sha>` — `HEAD` before the packaging commit
  - **Base branch**: `<base_branch>`
  - **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
  - **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

  ## Identifiers

  | Placeholder | Value |
  |-------------|-------|
  | `<epic_dir>` | `<epic_dir value>` |
  | `<epic_slug>` | `<epic_slug value>` |

  These are usually different strings. Never derive one from the other.

  ## Read First

  1. `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
  2. `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` — the behavioural contract.
  3. `.devtool/epic/<epic_dir>/<source spec>.en.md` — the approved source spec.

  ## Resume Prompt

  ```text
  Use the d3nexus:dev-implementation skill for the `<epic_slug>` epic.
  Read .devtool/epic/<epic_dir>/handoff.md first.
  Gates 1 and 2 are passed; do not re-run brainstorming or design.
  Gate 3 is pending: present the execution order to me and wait for my confirmation.
  ```

  ## Open Notes

  <What the design session knows that the documents do not say — decisions taken in conversation, risks, doubts. Write `None` when there is nothing.>

  ## Rules for the Receiving Agent

  - Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
  - This handoff does not pass Gate 3. The developer confirms the execution order.
  - If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
  - This file is a dated record. It is never updated after packaging.
EOF
````

Check: `head -1 skills/dev-lifecycle/references/handoff-template.md` prints `# Handoff: <epic_slug>`.

- [ ] **Step 4: Edit skills/dev-lifecycle/SKILL.md**

Apply these nine edits. Every anchor occurs exactly once.

A — in the mermaid diagram under The Sequence, insert directly after this line:

```markdown
    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
```

The new text:

```markdown
    HC{"Handoff choice<br/>package or continue?"}
    PKG(["Package epic<br/>handoff.md, status Packaged, stop"])
```

B — in the same diagram, replace:

```markdown
    G2 -->|yes| S3
```

with:

```markdown
    G2 -->|yes| HC
    HC -->|"1. package"| PKG
    HC -->|"2. continue"| S3
    PKG -.->|"later session or another LLM"| S3
```

C — at the start of `## Stages`, insert directly before this line:

```markdown
### Stage 1 — Inception & Spec → `dev-brainstorming`
```

The new text, preceded by a blank line:

```markdown
### Resuming an Epic

A request to implement, continue or resume an epic whose `.devtool/epic/<epic_dir>/` already holds
`task_*.md` files is past Gate 2 — whether the epic was packaged (`handoff.md` present, Status
`Packaged`) or interrupted midway through Stage 3. Announce "Gates 1 and 2 already passed; resuming
at Stage 3", invoke `dev-implementation` with that epic name, and let its Entry-Point Detection
choose where to start. Never redo Stage 1 or Stage 2 for it. New requirements for such an epic are
not a resume: they go to dev-designer's Updating an Existing Epic.
```

D — in the Document Contract, replace:

```markdown
`task_*.md` files are the only exception and remain English-only.
```

with:

```markdown
`task_*.md` files and an epic's `handoff.md` are the only exceptions and remain English-only;
`handoff.md` still carries a complete table of contents.
```

E — between the Stage 2 and Stage 3 sections, insert directly before this line:

```markdown
### Stage 3 — Isolated Execution → `dev-implementation`
```

The new text, preceded by a blank line:

~~~~markdown
### Handoff Choice

Between Gate 2 and Stage 3 the developer decides when, and by whom, the epic is implemented. This
is a routing decision like Stage 1's, not a sixth gate. Ask it once `dev-designer` Step 3 has
committed the task files — or, with `auto_commit: false`, once they are written:

> Gate 2 passed: the HLD, BDD scenarios and N task files for `<epic_slug>` are written. How do you
> want to proceed?
>
> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop, so the work can be
>    picked up later or by another LLM.
> 2. **Continue** — enter Stage 3 now (`dev-implementation`, starting with Gate 3: execution order).

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
   and fill every placeholder. The first column of its Identifiers table names the placeholders and
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

   Two matching lines are required; with fewer, set the Status line by hand in both variants. Task
   statuses stay as they are, so a packaged epic still counts as active under dev-designer's
   Concurrent-Epic Backlog Rule.
5. Commit, when `auto_commit` is `true` or absent: stage `handoff.md`, the overview pair and any task files fixed at step 1, then
   `git commit -m "[<EPIC_NAME>] Package epic for handoff"`, with no trailer. When `auto_commit` is
   `false`, skip it and warn that an agent in another clone will not see the package.
6. Offer to push, and push only on the developer's explicit permission. Say that a receiver in
   another clone or on another machine needs the push.
7. Print the `handoff.md` path and its rendered Resume Prompt, then stop.
~~~~

F — in the Stage 3 section, replace:

```markdown
**Entry:** Gate 2 passed; HLD and `task_*.md` files exist.
```

with:

```markdown
**Entry:** Gate 2 passed, HLD and `task_*.md` files exist, and the developer chose Continue at
the Handoff Choice — or a packaged or interrupted epic is being resumed (see
[Resuming an Epic](#resuming-an-epic)).
```

G — in the Red Flags section, replace:

```markdown
- Creating a worktree or dispatching a subagent before Gate 3.
```

with:

```markdown
- Creating a worktree or dispatching a subagent before Gate 3. Recreating the worktree of an epic branch that already exists (dev-implementation's Resume Procedure) is not creating one.
- Invoking `dev-implementation` straight after `dev-designer` without asking the Handoff Choice.
- Packaging an epic without the preflight, or pushing the package without explicit permission.
- Treating a packaged epic's Gate 3 as already passed.
- Redoing the design of an epic whose task files already exist; new requirements go to dev-designer's Updating an Existing Epic.
```

H — at the end of the Rationalizations table, insert directly after this line:

```markdown
| "I can combine research + spec into one step" | Stage 1 is `dev-brainstorming`'s job. Invoke the skill. |
```

The new text:

```markdown
| "The developer obviously wants to continue" | The Handoff Choice is theirs. Ask it every time Gate 2 passes. |
```

I — in The Five Gates table, replace:

```markdown
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint | confirmed order + bootstrapped worktree |
```

with:

```markdown
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint, or Gate 3 (resume) in its Resume Procedure | confirmed order + bootstrapped worktree |
```

- [ ] **Step 5: Edit skills/dev-designer/SKILL.md**

Apply these two edits.

J — at the end of Step 3: Finalize & Commit, insert directly after this line:

```markdown
- If `auto_commit: false`: skip staging and committing entirely.
```

The new text, preceded by a blank line:

```markdown
Then stop and return to the [Handoff Choice](../dev-lifecycle/SKILL.md#handoff-choice) in
`dev-lifecycle`: ask the developer whether to package the epic or continue to Stage 3. This skill
never invokes `dev-implementation` itself.
```

K — in the Red Flags section, insert directly after this line:

```markdown
- Committing the epic before `check_bdd_traceability.py plan` exits 0.
```

The new text:

```markdown
- Invoking `dev-implementation` after Step 3 instead of returning to the Handoff Choice.
```

- [ ] **Step 6: Run the contract test and the lint**

```bash
python3 scripts/test_lifecycle_document_contract.py
python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-designer/SKILL.md
python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-lifecycle/references/handoff-template.md
```

Expected: `checked 11 lifecycle document contract surfaces`, then `checked 2 documents, 0 findings`, then `checked 1 documents, 0 findings`.

- [ ] **Step 7: Dry-run the packaging procedure on a throwaway epic**

This is the integration test. It runs every command the Handoff Choice prescribes against a real two-task epic, then the three failure modes the preflight and the status check exist to catch. Build the fixture:

````bash
KIT=$(git rev-parse --show-toplevel)
FIXDIR=$(mktemp -d)
cat > "$FIXDIR/make_fixture.sh" <<'EOF'
#!/usr/bin/env bash
# Build a throwaway git repository holding one two-task epic (dir todo_export, slug todo-export),
# for dry-running the epic handoff skill text. Usage: make_fixture.sh <empty-or-new-directory>
set -euo pipefail
FIX="$1"
mkdir -p "$FIX"
cd "$FIX"
git init -q -b main
printf '.worktrees/\n' > .gitignore
EPIC=.devtool/epic/todo_export
mkdir -p "$EPIC" .devtool/features/done
touch .devtool/features/done/.gitkeep
T='```'

printf '%s\n' "# Epic: Todo Export" "" "## Meta Data" "" "- **Status**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.en.md"
printf '%s\n' "# Epic: Xuất danh sách todo" "" "## Meta Data" "" "- **Trạng thái**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.vi.md"

printf '%s\n' "# BDD Scenarios: Todo Export" "" "## Export" "" "${T}gherkin" "Feature: Export" \
  "  Scenario: [TE-HP-01] [Tier C - Integration] Export todos as CSV" "    Given two todos" \
  "  Scenario: [TE-EC-02] Unknown format exits 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.en.md"
printf '%s\n' "# Kịch bản BDD: Xuất todo" "" "## Xuất" "" "${T}gherkin" "Feature: Export" \
  "  Kịch bản: [TE-HP-01] [Tier C - Integration] Xuất todo dạng CSV" "    Given two todos" \
  "  Kịch bản: [TE-EC-02] Định dạng lạ thoát mã 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.vi.md"

task() {  # task <file-stem> <number> <title> <covers> <dependency-line>
  printf '%s\n' "---" "id: \"$1\"" "status: \"todo\"" "priority: \"high\"" "epic: \"todo-export\"" \
    "---" "# Task $2: $3" "" "### BDD SCENARIOS" "" "Covers: $4" "" "## Dependencies & Blockers" "" "$5"
}
task task_1_export_core 1 "Export core" "TE-HP-01" "- None" > "$EPIC/task_1_export_core.md"
task task_2_cli_integration 2 "CLI integration" "TE-EC-02" \
  "- Blocked by [Task 1](task_1_export_core.md)" > "$EPIC/task_2_cli_integration.md"
cp "$EPIC"/task_*.md .devtool/features/

git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: todo_export epic"
echo "fixture ready: $FIX"
EOF
bash "$FIXDIR/make_fixture.sh" "$FIXDIR/repo"
````

Then run, in the same shell so that `KIT` and `FIXDIR` are still set:

```bash
cd "$FIXDIR/repo"
SCRIPTS="$KIT/skills/dev-implementation/resources/scripts"
CHECK_DOC="$KIT/skills/doc_quality_check/resources/scripts/check_document.py"
python3 "$SCRIPTS"/compute_execution_order.py todo-export > "$FIXDIR/order.txt"; echo "order exit=$?"
head -1 "$FIXDIR/order.txt"
ls .devtool/epic/todo_export/task_*.md | wc -l | tr -d ' '
python3 "$SCRIPTS"/check_bdd_traceability.py plan \
  --scenarios .devtool/epic/todo_export/bdd_scenarios.en.md \
  --tasks .devtool/epic/todo_export/task_*.md; echo "plan exit=$?"
cp "$KIT/skills/dev-lifecycle/references/handoff-template.md" .devtool/epic/todo_export/handoff.md
python3 "$CHECK_DOC" --require-toc .devtool/epic/todo_export/handoff.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged
grep -c -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
  .devtool/epic/todo_export/todo_export.en.md .devtool/epic/todo_export/todo_export.vi.md
```

Expected:

```text
order exit=0
Scanned 2 task_*.md files; 2 matched epic 'todo-export'; 0 had no parseable frontmatter or a different epic.
2
TE-HP-01    task_1_export_core.md
TE-EC-02    task_2_cli_integration.md
Result: 2/2 covered — PASS
plan exit=0
  checked 1 documents, 0 findings
Synchronized 2 epic docs for 'todo_export' -> 'Packaged'
.devtool/epic/todo_export/todo_export.en.md:1
.devtool/epic/todo_export/todo_export.vi.md:1
```

Now the failure modes — broken frontmatter, a scenario no task covers, and an overview without a Status line:

```bash
git checkout -q -- . && rm -f .devtool/epic/todo_export/handoff.md
sed -i.bak 's/epic: "todo-export"/epic: "todo-exprot"/' .devtool/features/task_2_cli_integration.md
python3 "$SCRIPTS"/compute_execution_order.py todo-export | head -1
git checkout -q -- . && rm -f .devtool/features/*.bak
sed -i.bak '/^Covers:/d' .devtool/epic/todo_export/task_2_cli_integration.md
python3 "$SCRIPTS"/check_bdd_traceability.py plan \
  --scenarios .devtool/epic/todo_export/bdd_scenarios.en.md \
  --tasks .devtool/epic/todo_export/task_*.md; echo "plan exit=$?"
git checkout -q -- . && rm -f .devtool/epic/todo_export/*.bak
sed -i.bak '/Status/d;/Trạng thái/d' .devtool/epic/todo_export/todo_export.en.md .devtool/epic/todo_export/todo_export.vi.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged; echo "sync exit=$?"
grep -c -E '^- \*\*Status\*\*: Packaged' .devtool/epic/todo_export/todo_export.en.md
cd "$KIT" && rm -rf "$FIXDIR"
```

Expected:

```text
Scanned 2 task_*.md files; 1 matched epic 'todo-export'; 1 had no parseable frontmatter or a different epic.
TE-HP-01    task_1_export_core.md
TE-EC-02    (none)
Result: 1/2 covered — FAIL
plan exit=1
Synchronized 2 epic docs for 'todo_export' -> 'Packaged'
sync exit=0
0
```

The first line shows `1 matched` against 2 task mirrors with exit 0: the count comparison, not the exit code, catches broken frontmatter. The last lines show the status script reporting success while writing nothing, which is why the procedure requires the `grep`.

- [ ] **Step 8: Re-run the scenario (GREEN)**

Dispatch a new fresh subagent with the Step 1 prompt, unchanged. Expected: (1) asks the two-option Handoff Choice and waits; (2) runs `compute_execution_order.py`, the task-mirror count and `check_bdd_traceability.py plan`; writes `handoff.md` from `references/handoff-template.md` and lints it with `--require-toc`; runs `sync_task_status.py epic todo_export Packaged` and the `grep`; commits with a `Package epic for handoff` title and no trailer; asks before any push; ends by printing the path and the Resume Prompt. If a part is missing, tighten the matching edit and re-run.

- [ ] **Step 9: Run verify.sh**

Run: `scripts/verify.sh`
Expected: `PASS — safe to publish`. Its link check also proves that the `#handoff-choice` link from dev-designer resolves.

- [ ] **Step 10: Commit**

```bash
git add skills/dev-lifecycle/SKILL.md skills/dev-lifecycle/references/handoff-template.md \
  skills/dev-designer/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Add the Handoff Choice and epic packaging" -m "- ask package-or-continue between Gate 2 and Stage 3
- add the packaging procedure and the handoff.md template
- add Resuming an Epic and point dev-designer at the Handoff Choice
- lock the new phrases in the lifecycle contract test"
```

### Task 2: Entry-Point Detection and Resume

**Files:**

- Modify: `skills/dev-implementation/SKILL.md`
- Modify: `scripts/test_lifecycle_document_contract.py`

**Interfaces:**

- Consumes: from Task 1, `.devtool/epic/<epic_dir>/handoff.md`, the Status value `Packaged`, and the template `skills/dev-lifecycle/references/handoff-template.md` (used by the dry run); from `main`, Phase 1 step 3's BDD mapping check and `$INTEGRATE` from Phase 0 step 2.
- Produces: Entry-Point Detection rows 1 to 7 and the Resume Procedure, which dev-lifecycle's Resuming an Epic rule hands over to.

- [ ] **Step 1: Baseline scenario (RED)**

Before editing, dispatch a fresh general-purpose subagent with this prompt and keep its reply:

```text
You are in the repository <ROOT>. Read skills/dev-implementation/SKILL.md. You were
invoked as "dev-implementation todo_export" (epic slug todo-export). Do not run anything. For each
situation, name the entry-point row and list, in order, what you do before any task code is written:
(A) .devtool/epic/todo_export/handoff.md exists; the overview Status is Packaged; there is no
epic/todo-export branch and no worktree; both tasks are todo.
(B) The branch epic/todo-export and the worktree .worktrees/todo_export exist; task_1 is done;
task_2 is in-progress and the worktree has uncommitted changes in src/export.py.
```

Expected baseline: no entry-point rows; for (B) it either restarts Phase 1 — including `git worktree add -b`, which fails on the existing branch — or resumes without asking whether to keep the uncommitted changes. Record the reply.

- [ ] **Step 2: Lock the new contract (failing test)**

Contract test — in `scripts/test_lifecycle_document_contract.py`, replace:

```python
        "--ids",
    ),
```

with:

```python
        "--ids",
        "Entry-Point Detection",
        "Resume Procedure",
        "handoff.md",
    ),
```

Run: `python3 scripts/test_lifecycle_document_contract.py`

Expected: exit 1 with these lines:

```text
  FAIL skills/dev-implementation/SKILL.md: missing Entry-Point Detection
  FAIL skills/dev-implementation/SKILL.md: missing Resume Procedure
  FAIL skills/dev-implementation/SKILL.md: missing handoff.md
```

- [ ] **Step 3: Edit skills/dev-implementation/SKILL.md**

Apply these nine edits. Every anchor occurs exactly once.

A — in When to Use, insert directly after this line:

```markdown
- You are about to implement more than one task from that epic in this session.
```

The new text:

```markdown
- You are resuming an epic — packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Invoke this skill with the epic's directory name or slug; Entry-Point Detection in Phase 0 decides where to start.
```

B — in the Process diagram, insert directly after this line:

```markdown
    phase0["Phase 0: Context Reload & Platform Detection\n(detect_project_type.sh)"]
```

The new text:

```markdown
    entry{"Entry-Point Detection\n(rows 1-7)"}
    resume["Resume Procedure\nGate 3 (resume), reuse the worktree"]
```

C — in the same diagram, replace:

```markdown
    phase0 --> phase1a
```

with:

```markdown
    phase0 --> entry
    entry -- "row 3: fresh start" --> phase1a
    entry -- "rows 4-5: interrupted" --> resume
    entry -- "row 6: tasks done" --> phase4
    resume --> phase2
```

D — at the start of Phase 0, insert directly before this line:

```markdown
1. Read, in full:
```

The new text:

```markdown
0. **Resolve the epic.** This skill takes one epic name, in either form:
   - If `.devtool/epic/<name>/` exists, `<epic_dir>` is `<name>`, and `<epic_slug>` is the `epic:` value of its task mirrors: `grep -h -m1 '^epic:' .devtool/epic/<name>/task_*.md`.
   - Otherwise `<name>` is a slug, and `<epic_dir>` is the directory holding the files `grep -l -F 'epic: "<name>"' .devtool/epic/*/task_*.md` lists.
   - With no name, or no match, list the epic directories whose overview Status is not `Done` and ask which one. Never guess, even when only one is listed.
```

E — in Phase 0 step 1's reading list, insert directly after this line:

```markdown
   - Any spec file(s) linked from the HLD's Meta Data section.
```

The new text:

```markdown
   - `.devtool/epic/<epic_dir>/handoff.md`, when present — the packaging record. Use its Open Notes as context; it is never updated after packaging.
```

F — after Phase 0 step 3's platform list, insert directly after this line:

```markdown
   - **`rust`**: Rust workspace (`Cargo.toml`, `xtask`, Clean Architecture + MVI, FFI/WASM).
```

The new text:

~~~~markdown
4. Run **Entry-Point Detection** (below) before Phase 1. It decides whether Phase 1 starts fresh or the Resume Procedure takes over.

#### Entry-Point Detection

Read these signals, all read-only, from the main checkout:

```bash
test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/<epic_dir>/<epic_dir>.en.md
git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
git branch -r --list '*/epic/<epic_slug>'
git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug>
```

`git branch -r` reveals an epic branch pushed from another clone. The last command's flattened order prints each task's status as `[priority, status]`; task files stay in `.devtool/features/` while `done` until Stage 4 archives them. Evaluate the rows top-down — the first match wins — and announce it: "Entry point: row N — <state>."

| # | Signals | State | Entry point |
|---|---------|-------|-------------|
| 1 | Overview Status is `Done` | Finished | Report it and stop |
| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is the developer's call |
| 3 | No epic branch locally or on a remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then a new worktree |
| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
| 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate the worktree if it is missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap it (Phase 1 step 5), then Phase 4 with a full run — a verdict from another session cannot be tied to this SHA |
| 7 | Anything else — for example the epic branch only on a remote (work done in another clone), or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report the signals, ask |

#### Resume Procedure

For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.

1. Row 4 only: recreate the worktree from the existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. This restores an epic already under way; it is not the new worktree that Gate 3 guards. For rows 4 and 5, check the bootstrap with Phase 1 step 5's platform checks and re-run it if they fail.
2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or a base that diverged, is handled the way Phase 2 step 7 prescribes before anything else.
3. Find the interrupted task: one at `in-progress` or `review`. If the worktree has uncommitted changes, collect `git status --short`; uncommitted changes with no interrupted task are presented the same way.
4. **Gate 3 (resume).** Run Phase 1 step 3's BDD mapping check first, including its retrofit for an epic designed before scenario identifiers, and commit any retrofit on the epic branch, staging only the files it touched by path — both `bdd_scenarios` variants, both HLD variants and the task files — never `git add -A`, so the interrupted task's uncommitted work stays out of that commit. Then, in one message, present the tasks already `done` with their commits (`git log --oneline develop..epic/<epic_slug>`); the remaining order — the flattened order with `done` tasks removed, which keeps every dependency satisfied; for uncommitted changes, a choice between keeping them and continuing the task or discarding them and restarting it, discarding only on that explicit answer; and the request for permission to fast-forward `develop`, asked again because it does not carry across sessions. Wait for confirmation.
5. If the overview Status is `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
6. Enter Phase 2 at the interrupted task, or at the first remaining task.
~~~~

G — in Phase 1 step 4, insert directly after this line:

```markdown
   If `sync-base` exits 3 — `develop` diverged from its upstream, or a dirty file blocks the
   fast-forward — stop and ask.
```

The new text:

```markdown
   Once the worktree exists, if the overview Status is `Packaged` (a packaged epic starting fresh, row 3), run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`; the change travels with the first task commit.
```

H — in the Quick Reference table, insert directly before this line:

```markdown
| Create epic worktree |
```

The new text:

```markdown
| Resume an epic | Entry-Point Detection, then the Resume Procedure (no `-b`) | Same | Same |
```

I — in the Red Flags section, insert directly after this line:

```markdown
- Running `@quality_check` for Gate 4 before the full traceability check exits 0, or on a commit that check did not see.
```

The new text:

```markdown
- Starting Phase 1 without running Entry-Point Detection.
- Running `git worktree add -b` for an epic whose branch already exists.
- Re-implementing a task already `done`.
- Discarding an interrupted session's uncommitted changes without an explicit answer.
```

- [ ] **Step 4: Run the contract test and the lint**

```bash
python3 scripts/test_lifecycle_document_contract.py
python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/SKILL.md
```

Expected: `checked 11 lifecycle document contract surfaces`, then `checked 1 documents, 0 findings`.

- [ ] **Step 5: Dry-run Entry-Point Detection on a throwaway epic**

This is the integration test. It walks one epic through rows 3, 5, 4 and 6, printing exactly the signals the new section reads, then checks both forms of epic-name resolution. Build the fixture:

````bash
KIT=$(git rev-parse --show-toplevel)
FIXDIR=$(mktemp -d)
cat > "$FIXDIR/make_fixture.sh" <<'EOF'
#!/usr/bin/env bash
# Build a throwaway git repository holding one two-task epic (dir todo_export, slug todo-export),
# for dry-running the epic handoff skill text. Usage: make_fixture.sh <empty-or-new-directory>
set -euo pipefail
FIX="$1"
mkdir -p "$FIX"
cd "$FIX"
git init -q -b main
printf '.worktrees/\n' > .gitignore
EPIC=.devtool/epic/todo_export
mkdir -p "$EPIC" .devtool/features/done
touch .devtool/features/done/.gitkeep
T='```'

printf '%s\n' "# Epic: Todo Export" "" "## Meta Data" "" "- **Status**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.en.md"
printf '%s\n' "# Epic: Xuất danh sách todo" "" "## Meta Data" "" "- **Trạng thái**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.vi.md"

printf '%s\n' "# BDD Scenarios: Todo Export" "" "## Export" "" "${T}gherkin" "Feature: Export" \
  "  Scenario: [TE-HP-01] [Tier C - Integration] Export todos as CSV" "    Given two todos" \
  "  Scenario: [TE-EC-02] Unknown format exits 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.en.md"
printf '%s\n' "# Kịch bản BDD: Xuất todo" "" "## Xuất" "" "${T}gherkin" "Feature: Export" \
  "  Kịch bản: [TE-HP-01] [Tier C - Integration] Xuất todo dạng CSV" "    Given two todos" \
  "  Kịch bản: [TE-EC-02] Định dạng lạ thoát mã 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.vi.md"

task() {  # task <file-stem> <number> <title> <covers> <dependency-line>
  printf '%s\n' "---" "id: \"$1\"" "status: \"todo\"" "priority: \"high\"" "epic: \"todo-export\"" \
    "---" "# Task $2: $3" "" "### BDD SCENARIOS" "" "Covers: $4" "" "## Dependencies & Blockers" "" "$5"
}
task task_1_export_core 1 "Export core" "TE-HP-01" "- None" > "$EPIC/task_1_export_core.md"
task task_2_cli_integration 2 "CLI integration" "TE-EC-02" \
  "- Blocked by [Task 1](task_1_export_core.md)" > "$EPIC/task_2_cli_integration.md"
cp "$EPIC"/task_*.md .devtool/features/

git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: todo_export epic"
echo "fixture ready: $FIX"
EOF
bash "$FIXDIR/make_fixture.sh" "$FIXDIR/repo"
````

Then run, in the same shell so that `KIT` and `FIXDIR` are still set:

```bash
cd "$FIXDIR/repo"
SCRIPTS="$KIT/skills/dev-implementation/resources/scripts"
signals() {
  test -f .devtool/epic/todo_export/handoff.md && echo "handoff: yes" || echo "handoff: no"
  grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/todo_export/todo_export.en.md
  git rev-parse --verify --quiet refs/heads/epic/todo-export > /dev/null && echo "branch: yes" || echo "branch: no"
  git branch -r --list '*/epic/todo-export' | grep -q . && echo "remote branch: yes" || echo "remote branch: no"
  git worktree list --porcelain | grep -q -E '^worktree .*/\.worktrees/todo_export$' && echo "worktree: yes" || echo "worktree: no"
  python3 "$SCRIPTS"/compute_execution_order.py todo-export | grep -E '^  [0-9]+\.'
}
cp "$KIT/skills/dev-lifecycle/references/handoff-template.md" .devtool/epic/todo_export/handoff.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged > /dev/null
git add -A && git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "package"
echo "== row 3"; signals
git worktree add -q .worktrees/todo_export -b epic/todo-export main
python3 "$SCRIPTS"/sync_task_status.py task task_1_export_core done > /dev/null
echo "== row 5"; signals
git worktree remove --force .worktrees/todo_export
echo "== row 4"; signals
git worktree add -q .worktrees/todo_export epic/todo-export; echo "add without -b exit=$?"
python3 "$SCRIPTS"/sync_task_status.py task task_2_cli_integration done > /dev/null
echo "== row 6"; signals
echo "== name resolution"
grep -h -m1 '^epic:' .devtool/epic/todo_export/task_*.md | sort -u
grep -l -F 'epic: "todo-export"' .devtool/epic/*/task_*.md | xargs -n1 dirname | sort -u
cd "$KIT" && rm -rf "$FIXDIR"
```

Expected:

```text
== row 3
handoff: yes
- **Status**: Packaged
branch: no
remote branch: no
worktree: no
  1. task_1_export_core - Export core [high, todo]
  2. task_2_cli_integration - CLI integration [high, todo]
== row 5
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: yes
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, todo]
== row 4
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: no
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, todo]
add without -b exit=0
== row 6
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: yes
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, done]
== name resolution
epic: "todo-export"
.devtool/epic/todo_export
```

Each block of signals must select the row its header names in the Entry-Point Detection table, and `add without -b exit=0` proves that row 4's recreation works on the existing branch.

- [ ] **Step 6: Re-run the scenario (GREEN)**

Dispatch a new fresh subagent with the Step 1 prompt, unchanged. Expected: (A) row 3 — Phase 1, Gate 3, the new worktree with `-b`, then the Status moved from `Packaged` to `In Progress`; (B) row 5 — the Resume Procedure: bootstrap check, `integrate_branch.py preflight`, task_2 found as interrupted with `git status --short`, Gate 3 (resume) running the BDD mapping check, listing the done tasks with their commits and the remaining order, and asking keep-or-discard for `src/export.py` and the `develop` fast-forward permission — never `git worktree add -b`. If a part is missing, tighten the matching edit and re-run.

- [ ] **Step 7: Run verify.sh**

Run: `scripts/verify.sh`
Expected: `PASS — safe to publish`.

- [ ] **Step 8: Commit**

```bash
git add skills/dev-implementation/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Add entry-point detection and resume to dev-implementation" -m "- resolve the epic from its directory name or slug
- pick the entry point from handoff.md, status, branch, worktree and task states
- add the Resume Procedure and move a packaged epic to In Progress
- lock the new phrases in the lifecycle contract test"
```

## Final Verification

- [ ] Run `scripts/verify.sh` on the final commit. Expected: `PASS — safe to publish`.
- [ ] Check every spec section against the diff: §4 flow and question (Task 1 Edits A, B and E), §5 components (both tasks), §6 template (Task 1 Step 3), §7 packaging procedure (Task 1 Edit E), §8.1 epic resolution (Task 2 Edit D), §8.2 and §8.3 signals and rows (Task 2 Edit F), §8.4 Resume Procedure (Task 2 Edit F), §8.5 status change on a fresh start (Task 2 Edit G), §9 red flags (Task 1 Edits G and K, Task 2 Edit I), and the Gate 3 row (Task 1 Edit I).
- [ ] Quality gate: invoke `@quality_check` as `CRITICAL_RULES` requires. This repository has no `.agents/quality/check_quality.json`, so expect `BLOCKED`; report it as such. The kit's release gate is `scripts/verify.sh`.
- [ ] Do not push. Report the two commits and wait for the developer.
