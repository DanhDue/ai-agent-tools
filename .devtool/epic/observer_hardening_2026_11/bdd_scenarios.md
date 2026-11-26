# Observer Hardening 2026-11 BDD Scenarios

## Table of Contents

- [1. Happy Path Scenarios (HP)](#1-happy-path-scenarios-hp)
- [2. Edge Case Scenarios (EC)](#2-edge-case-scenarios-ec)
- [3. State Transition Scenarios (ST)](#3-state-transition-scenarios-st)
- [4. Architectural and Boundary Scenarios (AR)](#4-architectural-and-boundary-scenarios-ar)
- [5. Failure and Recovery Scenarios (FR)](#5-failure-and-recovery-scenarios-fr)

## 1. Happy Path Scenarios (HP)

```gherkin
Scenario: [OHK-HP-01] [Tier C - Integration] Promote epic tasks inside an isolated worktree without mutating primary checkout
Given a git repository with a primary checkout on develop lacking epic "iso_epic"
And a linked worktree ".worktrees/iso_epic" on branch "epic/iso-epic" containing ".devtool/epic/iso_epic" with a "backlog" task
When "sync_task_status.py promote iso_epic" executes inside ".worktrees/iso_epic"
Then the command exits 0 and prints "Promoted"
And the task frontmatter inside ".worktrees/iso_epic" updates from "backlog" to "todo"
And the primary checkout remains clean with zero untracked or modified ".devtool/" files

Scenario: [OHK-HP-02] [Tier C - Integration] Re-anchor handoff after rebasing an active Stage 3 epic branch
Given an epic packaged with handoff.md referencing pre-rebase Design commit SHA "old_sha"
And the epic branch is rebased onto an advanced base branch so "old_sha" is no longer an ancestor of HEAD
When "package_epic.py <epic_dir> --revise --reason 'Rebased onto base'" executes
Then check_epic_readiness.py runs with "--reanchoring" and exits 0
And handoff.md updates Design commit to the new rebased short HEAD SHA
And running "check_epic_readiness.py --post-design <epic_dir>" afterwards exits 0 with "R7 PASS"

Scenario: [OHK-HP-03] [Tier C - Integration] Bootstrap Python worktree with optional extras and preserve them with UV_NO_SYNC
Given a Python repository worktree whose pyproject.toml declares "[project.optional-dependencies]" and "[dependency-groups].dev"
And no custom "bootstrap" command is configured in ".agents/quality/python-quality.json"
When "bootstrap_worktree.sh" runs against the worktree with a recording fake "uv" binary on PATH
Then the invoked uv command includes "sync", "--all-extras", and "--group", "dev"
When verify_polyglot_registry.py executes a capability command starting with ["uv", "run", ...]
Then the child process receives "UV_NO_SYNC=1" in its environment

Scenario: [OHK-HP-04] [Tier C - Integration] Subdirectory UI audit resolves base templates and merges uncommitted template edits
Given a git repository whose web preview lives in subdirectory "src/app/preview"
And commit HEAD modifies "src/app/preview/static/style.css" while base ref "main" holds "static/search.html" with "style.css?v=1" and ".well-known/portal.html" with "style.css?v=1"
And the working tree has an uncommitted edit bumping "src/app/preview/static/search.html" to "style.css?v=2" and ".well-known/portal.html" to "style.css?v=2"
When "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" executes
Then "_get_base_file_content" resolves both "main:./static/search.html" and "main:./.well-known/portal.html" cleanly without stripping leading dots and rejects "../outside.html"
And "get_git_diff_files" includes "static/style.css", uncommitted "static/search.html", and uncommitted ".well-known/portal.html"
And the JSON report returns status "PASS" with 0 cache_bust findings
When ".well-known/portal.html" is modified without bumping "?v=1"
Then "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" returns status "FAIL" with a "cache_bust" finding on ".well-known/portal.html"

Scenario: [OHK-HP-05] [Tier C - Integration] Cross-Model Review auto-defers immutable epic doc Minor findings and smoke generator infers browser targets
Given a completed code-review round in "review_results.md" with 0 Critical, 0 Important, and 2 Minor findings targeting ".devtool/epic/<epic_dir>/task_01.md" and ".devtool/epic/<epic_dir>/manual_smoke_checklist.md"
When "run_external_review.py triage --epic-dir <epic_dir>" executes
Then Proposed action pre-fills "deferred: out-of-scope epic doc (§4.4)" for both Minor rows
And Auto-Triage Gate emits "AUTO_PASS_CLEAN" instead of "AUTO_PASS_FINAL_MINOR_SWEEP"
When "generate_smoke_checklist.py" parses a Playwright browser BDD scenario without an explicit CLI command
Then the generated checklist target is the inferred web URL or "Web Preview UI" rather than "CLI / Workspace Root"

Scenario: [OHK-HP-06] [Tier C - Integration] Updated kit skills preserve metadata contracts and observation rules
Given all skill and reference markdown updates across Clusters 1 through 4 are applied in the worktree
When kit skill contract verification inspects frontmatter, links, ToC anchors, and required policy directives
Then every SKILL.md contains exclusively "name" and "description" frontmatter keys
And skills document Visual Companion epic assets (#4), Step 1 code-span task links (#5), R8 --replay scoping (#6), multi-template Allowed files (#8), zsh-safe Check 0 (#9), uv --all-extras/UV_NO_SYNC (#11), deferred §4.4 token (#12), --allow-dirty (#13), shared .venv PYTHONPATH (#15), and quality-manifest/no-bare-npx/180s timer (#16)
```

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [OHK-EC-01] [Tier C - Integration] Finalize worker slot succeeds with gitignored .venv symlink and preserves tracked shared-contracts symlink
Given a worker pool slot containing a gitignored ".venv" symlink and a tracked "shared-contracts" symlink
And the slot has a valid code edit and completed task verification evidence
When "manage_worker_pool.py finalize-slot" executes on that slot
Then git staging succeeds with exit 0 without triggering ".venv is ignored by .gitignore"
And the created slot commit includes the code edit, excludes ".venv" and "review_audit_notes*", and preserves the tracked "shared-contracts" symlink intact

Scenario: [OHK-EC-02] [Tier C - Integration] Check epic readiness --replay skips R8 when contract-based tasks have zero test-creation directives
Given an epic whose task files declare "(new)" pytest test paths in Allowed files and RED rows targeting those not-yet-created tests
And the task files embed zero "Create", "Replace in", or "Insert in" directives for test files
When "check_epic_readiness.py <epic_dir> --replay" executes
Then check_epic_readiness.py exits 0
And output contains "R8 SKIP" rather than failing with pytest exit 4

Scenario: [OHK-EC-03] [Tier C - Integration] Document refusal gate catches build-shipping file hidden inside newline-joined zsh argument
Given "--changed-files" receives a single newline-joined string "src/app.py\ndocs/guide.en.md\n" simulating zsh unquoted command substitution
When "check_document.py --changed-files" runs refusal evaluation
Then it exits 1 and reports "ships in the build: src/app.py"
When "--changed-files" receives a newline-joined string of three documentation files "docs/a.md\ndocs/b.md\nCHANGELOG.md"
Then it exits 0 and reports "none of 3 changed files ship in the build"

Scenario: [OHK-EC-04] [Tier C - Integration] UI auditor excludes build directories, ignores pre-existing base-ref orphans, and catches CSS-only class removals including layout-inherited templates
Given a web project containing compiled HTML with orphaned classes inside "dist/", ".astro/", ".devtool/", "docs/", "target/", and "tests/"
And "src/layout.html" links "src/style.css" while unchanged child page "src/page.html" inherits "src/layout.html" without a direct stylesheet link and carries pre-existing orphaned class "legacy-unmapped" plus styled class "active-card" defined in "src/style.css" at base ref "main"
And HEAD edits only text on "src/page.html" without touching "src/style.css"
When "audit_ui_state_and_styles.py --base-ref main --json" executes
Then files under "dist/", ".astro/", ".devtool/", "docs/", "target/", and "tests/" produce zero findings
And pre-existing "legacy-unmapped" on "src/page.html" is filtered out so status is "PASS"
When HEAD instead modifies only "src/style.css" to delete ".active-card" while leaving both "src/layout.html" and child "src/page.html" untouched
Then "audit_ui_state_and_styles.py --base-ref main --json" scans all non-excluded templates for Invariant 2 and returns status "FAIL" with an "orphaned_class" finding for "active-card" on "src/page.html" while still suppressing pre-existing "legacy-unmapped"
And adding a brand-new undefined class "new-orphan-cls" on "src/page.html" also returns status "FAIL" with category "orphaned_class"

Scenario: [OHK-EC-05] [Tier C - Integration] Smoke checklist generator ignores CSS selector backticks and infers web target from HLD or BDD URL
Given a BDD Happy Path scenario mentioning Playwright clicking backticked selector "`.tts-save-btn`" on page "/tts-studio" with no CLI command
And the BDD document mentions preview URL "http://127.0.0.1:8000"
When "generate_smoke_checklist.py" extracts smoke steps
Then the step target is not "`.tts-save-btn`" and not "CLI / Workspace Root"
And the step target resolves to "http://127.0.0.1:8000"
```

## 3. State Transition Scenarios (ST)

```gherkin
Scenario: [OHK-ST-01] [Tier C - Integration] Archiving or promoting Epic A never dirties concurrent sibling Epic B worktree even with inherited Epic A files
Given a git repository with primary checkout on develop, worktree ".worktrees/epic_a" on branch "epic/epic-a", and sibling worktree ".worktrees/epic_b" on branch "epic/epic-b" that inherited ".devtool/epic/epic_a/" from develop
And Epic A has completed tasks in ".worktrees/epic_a/.devtool/features/done/" while Epic B has clean tracked ".devtool/" tasks inside ".worktrees/epic_b"
When "sync_task_status.py archive-done" executes inside ".worktrees/epic_a"
Then Epic A tasks archive into ".worktrees/epic_a/.devtool/epic/epic_a/" and Epic A HLD status becomes "Done"
And "git -C .worktrees/epic_b status --porcelain" remains completely empty
When "sync_task_status.py promote epic_a" is invoked from inside ".worktrees/epic_b"
Then "epic_checkout_roots" excludes ".worktrees/epic_b" because its branch is "refs/heads/epic/epic-b" and leaves ".worktrees/epic_b" completely clean

Scenario: [OHK-ST-02] [Tier C - Integration] Replay engine still enforces strict RED and GREEN checks on directive-bearing tasks
Given an epic task embedding literal "Create tests/test_sample_replay.py:" and "Create src_replay_mod.py:" directives
When "check_epic_readiness.py <epic_dir> --replay" executes with valid failing RED and passing GREEN rows
Then R8 reports "R8 PASS" and exits 0
When the embedded implementation directive breaks the GREEN test
Then R8 reports "R8 FAIL" and exits 1

Scenario: [OHK-ST-03] [Tier C - Integration] Delta review context honors deferred epic-doc tokens while blocking deferred on Important or source-file findings
Given Round 1 in "review_results.md" records a Minor finding on ".devtool/epic/sample/task_01.md" with decision "deferred: out-of-scope epic doc (§4.4)"
When "delta_round_context" constructs the Round 2 prompt block
Then rule 4 explicitly instructs the reviewer not to re-raise findings marked "dismissed:" or "deferred:"
When Round 1 instead marks a Minor finding on "src/app.py" with "deferred: arbitrary"
Then "run_external_review.py triage --epic-dir sample" still emits "AUTO_PASS_FINAL_MINOR_SWEEP" rather than "AUTO_PASS_CLEAN"
When Round 1 instead marks an Important finding with "deferred: out-of-scope epic doc (§4.4)"
Then "run_external_review.py check --epic-dir sample" exits 1 reporting that Important finding as undecided
```

## 4. Architectural and Boundary Scenarios (AR)

```gherkin
Scenario: [OHK-AR-01] [Tier C - Integration] Non-UI changes return NOT_APPLICABLE when only excluded paths contain HTML or CSS
Given a git branch diff against "main" that modifies "src/backend.py" and compiled "dist/index.html" with zero non-excluded UI source edits
When "audit_ui_state_and_styles.py --base-ref main --json" executes
Then status is "NOT_APPLICABLE" with reason code "scope_unmodified" and "ui_modified_files_count" equal to 0

Scenario: [OHK-AR-02] [Tier C - Integration] Non-overlapping watchdog timer guidance preserves merge hygiene in subagent-driven-development
Given "skills/subagent-driven-development/SKILL.md" in the epic worktree
When inspecting the "Waiting on dispatched subagents" section
Then the original paragraph wording from main remains intact to minimize conflicts with "feat/bg-task-watchdog-and-stall-detection"
And a dedicated follow-on bullet specifies pairing "invoke_subagent" with "schedule(DurationSeconds=180, TimerCondition=\"any\")"

Scenario: [OHK-AR-03] [Tier C - Integration] Kit verification gate verify.sh passes cleanly across all registered suites and contracts
Given all implementation changes and new test suites are registered in "scripts/verify.sh"
When "bash scripts/verify.sh --full" executes in the epic worktree
Then every static section (1 through 10) and all registered unittest and pytest suites exit 0 with "PASS — safe to publish"
```

## 5. Failure and Recovery Scenarios (FR)

```gherkin
Scenario: [OHK-FR-01] [Tier C - Integration] archive-epic called for Epic A skips unrelated Epic B worktrees even when run from primary checkout
Given a repository where primary checkout on develop has Epic A done tasks while sibling ".worktrees/epic_b" is active on "epic/epic-b"
When "sync_task_status.py archive-epic epic_a" runs from the primary checkout
Then Epic A archives cleanly in the primary checkout
And ".worktrees/epic_b" receives zero file writes or deletions

Scenario: [OHK-FR-02] [Tier C - Integration] Respect explicit caller UV_NO_SYNC override and fallback cleanly on malformed pyproject.toml
Given a Python repository whose pyproject.toml has no "[project.optional-dependencies]" table
When "bootstrap_worktree.sh" runs with a recording fake "uv" binary on PATH
Then it invokes bare "uv sync" without "--all-extras"
When verify_polyglot_registry.py runs a "uv run" capability while caller environment explicitly sets "UV_NO_SYNC=0"
Then the child process inherits "UV_NO_SYNC=0" without being clobbered

Scenario: [OHK-FR-03] [Tier C - Integration] sync_contracts.py diff-check enforces clean tree by default and guards protected contract paths under --allow-dirty
Given a satellite repository with valid ".agents/contract_map.json", ".agents/contract_sync.json", and "shared-contracts" symlink
And an uncommitted tracked modification exists in "src/preview/ui.js"
When "sync_contracts.py diff-check --base-ref main" runs without "--allow-dirty"
Then it exits 2 with status "BLOCKED"
When "sync_contracts.py diff-check --base-ref main --allow-dirty" runs while "shared-contracts", ".agents/contract_map.json", and ".agents/contract_sync.json" are clean
Then it audits committed "merge_base..HEAD" and exits 0 with status "PASS"
When ".agents/contract_map.json" or ".agents/contract_sync.json" has an uncommitted modification (tracked or untracked) and "--allow-dirty" is passed
Then it still exits 2 with status "BLOCKED" naming the dirty protected path so an uncommitted acknowledgement cannot satisfy a committed source delta
```
