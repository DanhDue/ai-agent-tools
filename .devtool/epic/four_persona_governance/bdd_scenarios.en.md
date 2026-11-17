# BDD Scenarios: Four-Persona Governance, Persona Model Config, and English-Only Dev Artefacts

## Table of Contents

- [1. Happy Path Scenarios (HP)](#1-happy-path-scenarios-hp)
- [2. Edge Case Scenarios (EC)](#2-edge-case-scenarios-ec)
- [3. State Transition Scenarios (ST)](#3-state-transition-scenarios-st)
- [4. Architecture and Concurrency Scenarios (AR)](#4-architecture-and-concurrency-scenarios-ar)
- [5. Fault Resilience Scenarios (FR)](#5-fault-resilience-scenarios-fr)

---

## 1. Happy Path Scenarios (HP)

```gherkin
Scenario: [FPG-HP-01] [Tier A - Unit] Layered persona resolution reports value and source layer per field
Given a temporary REAL_HOME whose ".d3nexus/personas.json" sets "active_preset" to "claude-hybrid"
And a project ".agents/config/personas.json" whose "overrides.programmer" is {"model": "hydrogen", "effort": "high"}
When "resolve_persona" runs for "ai_architect_reviewer", "orchestrator" and "programmer" with no CLI overrides
Then "ai_architect_reviewer" resolves to alias "claude-opus", cli "claude", model_id "opus", effort "high" with sources["model"] == "global"
And "orchestrator" resolves to alias "hydrogen", cli "agy", model_id "gemini-4-hydrogen-high", effort "high"
And "programmer" resolves to model_id "gemini-4-hydrogen-high", effort "high" with sources["effort"] == "project"
And resolving "programmer" with cli_overrides {"effort": "xhigh"} yields model_id "gemini-4-hydrogen-xhigh" with sources["effort"] == "cli"

Scenario: [FPG-HP-02] [Tier C - Integration] dev-config models lists the catalogue and a newly added alias becomes bindable
Given a temporary project and REAL_HOME with the kit default configuration and stub executables "agy" and "claude" on PATH only
When "dev_config.py models --json" runs
Then the JSON lists aliases "argon", "hydrogen", "claude-opus", "claude-sonnet", "codex-gpt" and "kiro-opus"
And "codex-gpt" and "kiro-opus" carry "cli_on_path": false while "argon" carries "used_by": ["ai_architect_reviewer"]
When "dev_config.py models add gpt-next --cli codex --id gpt-7 --efforts medium,high --scope global" and "dev_config.py set programmer gpt-next high" run
Then both exit 0 and "dev_config.py resolve programmer --format json" prints "model_id": "gpt-7" and "cli": "codex"

Scenario: [FPG-HP-03] [Tier A - Unit] Dispatch argv and environment preserve the bound model and effort per CLI and mode
Given bindings "programmer" on "hydrogen" effort "xhigh", "ai_architect_reviewer" on "argon" effort "high", a catalogue alias "claude-custom" with id "claude-opus-4-custom" bound effort "medium", "programmer" on "codex-gpt" effort "xhigh" and "programmer" on "kiro-opus" effort "high"
When "build_dispatch_argv" runs for (hydrogen, "write"), (argon, "read-only"), (claude-custom, "read-only"), (codex-gpt, "write") and (kiro-opus, "write")
Then the hydrogen argv equals ["agy", "--model", "gemini-4-hydrogen-xhigh", "--effort", "xhigh", "--mode", "auto"]
And the argon argv equals ["agy", "--sandbox", "--mode", "plan", "--model", "gemini-4-argon-high", "--effort", "high"]
And the claude argv contains "--model", "claude-opus-4-custom", "--effort", "medium" and "--permission-mode", "plan" and does not contain "--dangerously-skip-permissions"
And the codex argv contains "--sandbox", "workspace-write", "--model", "gpt-6.1-sol" and "model_reasoning_effort=extra-high"
And the kiro argv contains "--trust-all-tools", "--model", "claude-opus-5.5", "--effort" and "high"
And "build_dispatch_env" for the kiro argv with HOME "/Users/x/antigravity_homes/p1" and an existing "/Users/x/.kiro" returns HOME "/Users/x", while for the agy argv it returns the input environment unchanged

Scenario: [FPG-HP-04] [Tier A - Unit] A checkpoint writes the heartbeat block, the state file and one event
Given an isolated git repository with epic "fpg_epic" and an existing heartbeat
When "resume_context.py --checkpoint subagent_returned --epic fpg_epic --next 'dispatch task_03 reviewer'" runs
Then ".devtool/state/fpg-epic.heartbeat.json" has checkpoint["event"] == "subagent_returned", checkpoint["next_step"] == "dispatch task_03 reviewer" and checkpoint["turns_since_checkpoint"] == 0
And ".devtool/state/fpg_epic.md" contains "dispatch task_03 reviewer" under "Next Immediate Step"
And ".devtool/logs/events_fpg-epic.jsonl" gains exactly one line whose "category" is "checkpoint"
And running "resume_context.py" with no arguments prints the "subagent_returned" checkpoint before the activity stream

Scenario: [FPG-HP-05] [Tier A - Unit] Briefs and the implement prompt name the persona binding and never a Vietnamese file
Given a project whose persona config binds "ai_architect_reviewer" to "argon" "high" and "orchestrator" to "hydrogen" "high"
And epic "fpg_epic" whose directory holds "fpg_epic.en.md", "fpg_epic.vi.md", "bdd_scenarios.en.md" and "bdd_scenarios.vi.md"
When "--emit-prompt brief --brief-role task-reviewer", "--emit-prompt brief --brief-role fix-planner" and "--emit-prompt implement" run for "fpg_epic"
Then the task-reviewer and fix-planner briefs name "Role 2.1 AI Architect & Reviewer" and the argv "agy --model gemini-4-argon-high --effort high"
And the implement prompt names "Role 2.2 Orchestrator" with model "gemini-4-hydrogen-high" and effort "high"
And none of the three outputs contains the substring ".vi.md"

Scenario: [FPG-HP-06] [Tier C - Integration] A new English-only epic passes readiness and packaging with single files
Given epic "solo_epic" containing "solo_epic.md", "bdd_scenarios.md" and two valid task files, and no ".en.md" or ".vi.md" file
When "check_epic_readiness.py solo_epic" and "package_epic.py solo_epic" run
Then both exit 0
And "solo_epic.md" Meta Data reads "- **Status**: Packaged"
And no file matching "*.vi.md" or "*.en.md" exists under ".devtool/epic/solo_epic/"

Scenario: [FPG-HP-07] [Tier C - Integration] The dashboard payload carries persona bindings, the latest checkpoint and low-quota state
Given a temporary workspace with repository "demo_repo", a project persona config, a heartbeat with checkpoint event "wave_merged" and next_step "start wave 3", and low-quota enabled for the current profile
When "scan_repo" runs and "GET /api/tasks" is requested from a running TasksServer
Then the repository JSON has "persona_bindings" with three entries carrying "alias", "model_id", "effort" and "sources"
And "checkpoint" has "event" == "wave_merged" and "next_step" == "start wave 3"
And "low_quota" has "enabled" == true and an "expires_at" timestamp
And "tasks_dashboard.html" contains the render hooks "renderPersonaBindings" and "renderCheckpointStatus"

Scenario: [FPG-HP-08] [Tier C - Integration] End-to-end English-only epic flows from readiness to dashboard with persona stubs
Given a temporary repository with an English-only epic of two tasks, a project persona config and stub "agy" executables that return valid summary contracts
When readiness, packaging, "--emit-prompt implement", the runner's implementation step and "scan_repo" run in sequence
Then every dispatch argv was built from the configured bindings
And the heartbeat holds checkpoints "gate2_tasks_locked", "subagent_returned" and "wave_merged" in that order
And the dashboard payload shows both tasks done, the latest checkpoint "wave_merged" and no human-action alert

Scenario: [FPG-HP-09] [Tier C - Integration] Downstream verifiers read English-only epic documents
Given epic "solo_epic" with "solo_epic.md" carrying an "Integration results" line and an amended "## Spec Errata" entry, "bdd_scenarios.md" with scenario "[SOLO-HP-01]", and no ".en.md" or ".vi.md" file
When "generate_smoke_checklist.py --epic-dir solo_epic", "run_task_checks.py status" for a task covering "SOLO-HP-01", "audit_epic.py solo_epic", the local review epic slice and "integrate_branch.py" upstream epic detection run
Then the smoke checklist lists "SOLO-HP-01"
And the task status reports scenario "SOLO-HP-01" as covered
And the audit reports the HLD amendment from "solo_epic.md"
And the review slice includes "solo_epic.md" and "bdd_scenarios.md"
And upstream epic detection names "solo_epic"
And upstream epic detection reports "bdd_scenarios.md" for "solo_epic" when that file exists only at the upstream revision and not in the working tree
And when the base revision holds "solo_epic.en.md" and HEAD holds the renamed "solo_epic.md" with a changed "Integration results" line, the audit reports exactly that line change
```

---

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [FPG-EC-01] [Tier A - Unit] Invalid writes are rejected and leave the configuration file unchanged
Given a project configuration file whose SHA-256 is recorded
When "dev_config.py set programmer argon xhigh", "dev_config.py set programmer nosuchmodel high", "dev_config.py set reviewer argon high", "dev_config.py models add ollama-x --cli ollama --id gemma --efforts high" and "dev_config.py models add fast --cli agy --id gemini-4-flash --efforts high --quota-pool provider" run with "--scope project"
Then each exits 1 with a message naming the rejected value ("xhigh", "nosuchmodel", "reviewer", "ollama", "provider")
And the project configuration file SHA-256 is unchanged

Scenario: [FPG-EC-02] [Tier A - Unit] Legacy model settings are ignored and reported
Given ".devtool/review_config.json" with providers.programmer.model "gemini-3.8-flash" and environment AGY_PROGRAMMER_MODEL="legacy-x"
When "resolve_persona('programmer', root)" runs and "dev_config.py status --json" runs
Then the programmer model_id is "gemini-4-hydrogen-xhigh"
And the status JSON "warnings" list contains entries mentioning "providers.programmer" and "AGY_PROGRAMMER_MODEL"

Scenario: [FPG-EC-03] [Tier A - Unit] The legacy role name maps to the AI Architect
Given an isolated repository with epic "fpg_epic"
When "resume_context.py --state --epic fpg_epic --role assistant --status 'Stage 2'" runs
Then ".devtool/state/fpg_epic.md" records "Role: architect"
And "resume_context.py --role reviewer" exits non-zero with an argparse "invalid choice" message

Scenario: [FPG-EC-04] [Tier C - Integration] A legacy bilingual epic resolves the English file and never reads the mirror
Given epic "legacy_epic" with "legacy_epic.en.md", a stale "legacy_epic.vi.md", "bdd_scenarios.en.md" and "bdd_scenarios.vi.md"
And a file-open spy recording every path the scripts read
When "check_epic_readiness.py legacy_epic --strict-bilingual", "sync_task_status.py epic legacy_epic Packaged" and "check_bdd_traceability.py plan" run
Then all exit 0 and readiness prints one warning containing "--strict-bilingual is deprecated"
And "legacy_epic.en.md" reads "- **Status**: Packaged" while "legacy_epic.vi.md" bytes are unchanged
And the spy recorded no path ending in ".vi.md"

Scenario: [FPG-EC-05] [Tier A - Unit] An invalid persona configuration degrades to a dashboard warning
Given repository "demo_repo" whose ".agents/config/personas.json" contains {"schema_version": 99}
When "scan_repo" runs
Then it returns without raising
And "persona_bindings" is empty and "persona_config_error" contains "schema_version"
```

---

## 3. State Transition Scenarios (ST)

```gherkin
Scenario: [FPG-ST-01] [Tier A - Unit] Low-quota mode is per profile, expires, and halves the turn budget
Given a temporary REAL_HOME, profile "danhdue" and checkpoint_policy.max_orchestrator_turns_before_checkpoint 8
When "dev_config.py low-quota on --for 2" runs at 10:00 UTC
Then "low_quota_state(root, 'danhdue', now=11:59 UTC)" returns enabled true and the effective turn budget is 4
And "low_quota_state(root, 'danhdue', now=12:01 UTC)" returns None and the effective turn budget is 8
And "low_quota_state(root, 'other_profile', now=11:00 UTC)" returns None
When "dev_config.py low-quota off" runs at 11:00 UTC
Then "low_quota_state(root, 'danhdue', now=11:00 UTC)" returns None

Scenario: [FPG-ST-02] [Tier A - Unit] High-risk findings go to the fix-planner and halt criteria escalate
Given a runner whose cross-model triage contains one Critical finding and stub dispatchers recording persona and mode
When the fix-planner stub returns a JSON summary with status "PLANNED", "halt_criteria": [] and a "plan_markdown" body
Then the first dispatch is persona "ai_architect_reviewer" in mode "read-only", the runner writes "plan_markdown" to "fix_plan_round1.md" and commits it, and the second dispatch is persona "programmer" with review-fixer mode "apply-plan"
When, for each of "CRITICAL_CONFLICT", "Debatable", "SHARED_CONTRACT_CONFLICT", "FIX_LOOP" and "MAX_ROUNDS_CRITICAL_REMAINING", the fix-planner stub returns status "ESCALATE" with "halt_criteria" [that criterion]
Then each run halts with halt_reason "FIX_PLAN_ESCALATE", records a pending decision naming the criterion, and dispatches no programmer

Scenario: [FPG-ST-03] [Tier A - Unit] Turn budget and low-quota stop at the next safe point
Given a runner with three waves of two tasks each and stub dispatchers that succeed
When max_orchestrator_turns_before_checkpoint is 4 and low-quota mode is off
Then a "turn_budget" checkpoint is written after dispatches 4 and 8
When low-quota mode is switched on after wave 1 merges and before wave 2 starts
Then no wave 2 task is dispatched, a "low_quota_stop" checkpoint is written, and halt_reason is "LOW_QUOTA_STOP"
When low-quota mode is switched on while wave 2 is executing
Then wave 2's in-flight tasks complete and merge, no wave 3 task is dispatched, and halt_reason is "LOW_QUOTA_STOP"

Scenario: [FPG-ST-04] [Tier C - Integration] Quota, model and escalation stops render as human action on the dashboard
Given repositories whose pending decisions are kind "quota" (with quota lines "programmer agy 5H=12.0%"), kind "blocker" titled "programmer model hydrogen unavailable", and a heartbeat halt "FIX_PLAN_ESCALATE"
And a fourth repository whose latest checkpoint carries warning "quota_unknown"
When "scan_repo" runs for each repository
Then the first three have is_human_action_required true and an action_blockers entry whose text contains "5H=12.0%", "unavailable" and "FIX_PLAN_ESCALATE" respectively
And the fourth has is_human_action_required false and a "notices" entry containing "quota_unknown"

Scenario: [FPG-ST-05] [Tier A - Unit] The runner dispatches the Architect task-reviewer when gating requires it and finalizes only on a SHA-bound PASS
Given a runner with task "t_full" (review_tier "full") and task "t_small" (no review_tier, one non-test module) and stub dispatchers recording persona, brief role and mode
When the programmer stub returns DONE with head_sha "abc123" for both tasks
Then "t_small" is marked done without a reviewer dispatch
And "t_full" triggers one dispatch of persona "ai_architect_reviewer", brief role "task-reviewer", mode "read-only"
When the reviewer stub returns verdict "PASS" with head_sha "abc123"
Then the runner marks "t_full" done and commits the status change
When the reviewer stub instead returns verdict "PASS" with head_sha "zzz999" or verdict "FAIL"
Then "t_full" is not marked done and the programmer is dispatched again for "t_full"

Scenario: [FPG-ST-06] [Tier A - Unit] Gate 4 runs in a fresh Programmer gate4-verifier on every attempt
Given a runner whose slots are merged and cleaned and stub dispatchers recording brief roles
When Gate 4 starts, the first gate4-verifier stub returns verdict "FAIL", a review-fixer runs, and a second gate4-verifier stub returns verdict "PASS" with candidate_sha equal to HEAD
Then two distinct "gate4-verifier" dispatches on persona "programmer" in mode "write" were made and the runner executed no Gate 4 command itself
And Gate 4 is recorded as passed only after the second report
When a gate4-verifier stub returns verdict "PASS" with a candidate_sha different from HEAD
Then Gate 4 is not recorded and the runner dispatches a new gate4-verifier
```

---

## 4. Architecture and Concurrency Scenarios (AR)

```gherkin
Scenario: [FPG-AR-01] [Tier A - Unit] Concurrent checkpoints from root and worktree stay consistent under the lock
Given an isolated repository with epic "conc_epic" mirrored in the root and one worktree ".devtool"
When 6 threads each write 5 checkpoints with distinct "next_step" values through "update_epic_checkpoint"
Then both mirrored heartbeat files parse with json.loads and carry identical "checkpoint" blocks
And "events_conc-epic.jsonl" in each mirror holds exactly 30 "checkpoint" lines that all parse

Scenario: [FPG-AR-02] [Tier A - Unit] Parallel tasks must own disjoint files
Given tasks "task_01" and "task_02" with no Blocked by path between them, both listing "scripts/foo.py (L10-L20)" and "scripts/foo.py" respectively in Allowed files
When "check_task_contract.py --design" runs over both
Then it exits 1 with a finding "R-OWN" naming "task_01", "task_02" and "scripts/foo.py"
When "task_02" declares "Blocked by [Task 01]"
Then the same command exits 0

Scenario: [FPG-AR-03] [Tier A - Unit] Governance text uses the four-persona model everywhere
Given the tracked files under "rules/" and "skills/" excluding historical ".devtool" content
When the governance contract test scans them, excluding only the "Old-to-New Role Mapping" table in "skills/dev-lifecycle/references/orchestration-roles.md"
Then no scanned line contains "Tri-Role" or "Role 2.1 Human Architect" or "Role 2.3 AI Programmer"
And "rules/CRITICAL_RULES.md" contains "Role 1.0 Human Architect", "Role 2.1 AI Architect & Reviewer", "Role 2.2 Orchestrator" and "Role 2.3 Programmer"
And "skills/dev-lifecycle/references/orchestration-roles.md" contains a table under the heading "Old-to-New Role Mapping" and the brief role "fix-planner"

Scenario: [FPG-AR-04] [Tier A - Unit] Dev-lifecycle skills are English-only and isolate Vietnamese mirrors
Given the SKILL.md and references of "dev-lifecycle", "dev-brainstorming", "dev-designer", "dev-implementation", "writing-plans", "finishing-a-development-branch", "principal-review" and "cross-model-review"
When the English-only contract test scans them
Then none instructs creating a ".vi.md" file or passing "--require-bilingual" or "--strict-bilingual"
And none instructs reading a ".vi.md" file
And "rules/CRITICAL_RULES.md" contains a section titled "English SSOT and Vietnamese Mirror Isolation"
And the doc-lifecycle skills "doc-brainstorming", "doc-designer" and "doc-implementation" still contain "--require-bilingual"

Scenario: [FPG-AR-05] [Tier A - Unit] Concurrent writers to the global persona file never lose updates
Given a temporary REAL_HOME with the kit default configuration
When 4 processes run concurrently "dev_config.py set programmer hydrogen high", "dev_config.py set ai_architect_reviewer argon medium", "dev_config.py low-quota on" for profile "p1" and "dev_config.py low-quota on" for profile "p2"
Then all four exit 0
And the global file holds overrides for both "programmer" and "ai_architect_reviewer" and low_quota entries for both "p1" and "p2"
```

---

## 5. Fault Resilience Scenarios (FR)

```gherkin
Scenario: [FPG-FR-01] [Tier A - Unit] The quota gate stops on insufficient quota and tolerates unknown quota
Given bindings "programmer" on "agy" and "ai_architect_reviewer" on "claude", and a stub quota fetcher
When the fetcher returns agy {"status": "ACTIVE", "gemini5h": {"fraction": 0.12}, "argonWeekly": {"fraction": 0.05}} and a healthy claude payload
Then "dev_config.py quota-check --json" exits 2 and lists "programmer" with "sufficient": false and quota line "5H=12.0%"
When the fetcher returns agy {"status": "ACTIVE", "gemini5h": {"fraction": 0.0}, "argonWeekly": {"fraction": 0.9}} with "programmer" bound to "hydrogen" and "ai_architect_reviewer" bound to "argon"
Then "programmer" is "sufficient": false with quota line "5H=0.0%" and "ai_architect_reviewer" is "sufficient": true with quota line "Argon=90.0%"
When the same payload is judged with "programmer" bound to a custom catalogue alias "my-argon" {"cli": "agy", "id": "gemini-4-argon-{effort}", "efforts": ["high"]} that declares no "quota_pool"
Then "programmer" is "sufficient": true with quota line "Argon=90.0%"
When the project layer replaces built-in "hydrogen" with {"cli": "agy", "id": "gemini-4-hydrogen-{effort}", "efforts": ["high", "xhigh"], "quota_pool": "argonWeekly"} and "programmer" stays bound to "hydrogen"
Then "programmer" is "sufficient": true with quota line "Argon=90.0%"
When the fetcher returns {} for every CLI
Then "dev_config.py quota-check --json" exits 0 and every persona carries "warning": "quota_unknown"

Scenario: [FPG-FR-02] [Tier A - Unit] Dispatch failures are classified as model failures only for quota, auth and missing CLI
Given dispatch results (exit 1, stderr "HTTP 429 Too Many Requests"), (exit 1, stderr "RESOURCE_EXHAUSTED: quota exceeded"), (exit 1, stderr "CLI binary 'agy' not found on PATH"), (exit 127, stderr "agy: command not found") and (exit 1, stderr "401 Unauthorized: please log in")
And dispatch results (exit 1, stdout "3 failed, 10 passed"), (exit 1, stdout "401 failed, 403 passed"), (exit 1, stdout "FAILED tests/test_x.py::test_quota_check") and (exit 0, stdout "rate limit handled")
When "classify_dispatch_failure" runs on each
Then the first five return "model_unavailable"
And the next three return "task_failure" and the exit-0 result returns None

Scenario: [FPG-FR-03] [Tier A - Unit] An unavailable model halts with a checkpoint and a fallback command, never a retry
Given a runner whose programmer stub fails with stderr "RESOURCE_EXHAUSTED" and whose binding fallback is "claude-sonnet"
When the implementation step dispatches the first task
Then exactly one dispatch was attempted
And a "model_unavailable" checkpoint precedes a pending decision of kind "blocker" containing "/d3nexus:dev-config set programmer claude-sonnet"
And halt_reason is "MODEL_UNAVAILABLE"

Scenario: [FPG-FR-04] [Tier A - Unit] The runner checks quota before each wave
Given a runner with two waves and a quota gate stub that returns sufficient before wave 1 and insufficient before wave 2
When the implementation step runs
Then wave 1 tasks are dispatched and wave 2 tasks are not
And a "quota_low" checkpoint and a pending decision of kind "quota" are recorded, and halt_reason is "QUOTA_LOW"
```
