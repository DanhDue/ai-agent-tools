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

Scenario: [FPG-HP-03] [Tier A - Unit] Dispatch argv per CLI and mode
Given bindings for "programmer" on "hydrogen" effort "xhigh", "ai_architect_reviewer" on "codex-gpt" effort "high" and "programmer" on "kiro-opus" effort "high"
When "build_dispatch_argv" runs for (hydrogen, "write"), (codex-gpt, "read-only") and (kiro-opus, "write")
Then the agy argv equals ["agy", "--model", "gemini-4-hydrogen-xhigh", "--effort", "xhigh", "--mode", "auto"]
And the codex argv starts with ["codex", "exec", "--sandbox", "read-only"] and contains "gpt-6.1-sol"
And the kiro argv contains "--trust-all-tools" and "claude-opus-5.5"

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
```

---

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [FPG-EC-01] [Tier A - Unit] Invalid writes are rejected and leave the configuration file unchanged
Given a project configuration file whose SHA-256 is recorded
When "dev_config.py set programmer argon xhigh", "dev_config.py set programmer nosuchmodel high", "dev_config.py set reviewer argon high" and "dev_config.py models add ollama-x --cli ollama --id gemma --efforts high" run with "--scope project"
Then each exits 1 with a message naming the rejected value ("xhigh", "nosuchmodel", "reviewer", "ollama")
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
When the fix-planner stub returns status "PLANNED"
Then the first dispatch is persona "ai_architect_reviewer" in mode "read-only" and the second is persona "programmer" with review-fixer mode "apply-plan"
When, for each of "CRITICAL_CONFLICT", "Debatable", "SHARED_CONTRACT_CONFLICT", "FIX_LOOP" and "MAX_ROUNDS_CRITICAL_REMAINING", the fix-planner stub returns status "ESCALATE" with that criterion
Then each run halts with halt_reason "FIX_PLAN_ESCALATE", records a pending decision naming the criterion, and dispatches no programmer

Scenario: [FPG-ST-03] [Tier A - Unit] Turn budget and low-quota stop at the next safe point
Given a runner with three waves of two tasks each and stub dispatchers that succeed
When max_orchestrator_turns_before_checkpoint is 4 and low-quota mode is off
Then a "turn_budget" checkpoint is written after dispatches 4 and 8
When low-quota mode is on before wave 2 starts
Then wave 2 completes, a "low_quota_stop" checkpoint is written, no wave 3 task is dispatched, and halt_reason is "LOW_QUOTA_STOP"

Scenario: [FPG-ST-04] [Tier C - Integration] Quota, model and escalation stops render as human action on the dashboard
Given repositories whose pending decisions are kind "quota" (with quota lines "programmer agy 5H=12.0%"), kind "blocker" titled "programmer model hydrogen unavailable", and a heartbeat halt "FIX_PLAN_ESCALATE"
And a fourth repository whose latest checkpoint carries warning "quota_unknown"
When "scan_repo" runs for each repository
Then the first three have is_human_action_required true and an action_blockers entry whose text contains "5H=12.0%", "unavailable" and "FIX_PLAN_ESCALATE" respectively
And the fourth has is_human_action_required false and a "notices" entry containing "quota_unknown"
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
When the governance contract test scans them
Then no file contains "Tri-Role" or "Role 2.1 Human Architect" or "Role 2.3 AI Programmer"
And "rules/CRITICAL_RULES.md" contains "Role 1.0 Human Architect", "Role 2.1 AI Architect & Reviewer", "Role 2.2 Orchestrator" and "Role 2.3 Programmer"
And "skills/dev-lifecycle/references/orchestration-roles.md" contains the old-to-new role mapping table and the brief role "fix-planner"

Scenario: [FPG-AR-04] [Tier A - Unit] Dev-lifecycle skills are English-only and isolate Vietnamese mirrors
Given the SKILL.md and references of "dev-lifecycle", "dev-brainstorming", "dev-designer", "dev-implementation", "writing-plans", "finishing-a-development-branch", "principal-review" and "cross-model-review"
When the English-only contract test scans them
Then none instructs creating a ".vi.md" file or passing "--require-bilingual" or "--strict-bilingual"
And none instructs reading a ".vi.md" file
And "rules/CRITICAL_RULES.md" contains a section titled "English SSOT and Vietnamese Mirror Isolation"
And the doc-lifecycle skills "doc-brainstorming", "doc-designer" and "doc-implementation" still contain "--require-bilingual"
```

---

## 5. Fault Resilience Scenarios (FR)

```gherkin
Scenario: [FPG-FR-01] [Tier A - Unit] The quota gate stops on insufficient quota and tolerates unknown quota
Given bindings "programmer" on "agy" and "ai_architect_reviewer" on "claude", and a stub quota fetcher
When the fetcher returns agy {"status": "ACTIVE", "gemini5h": {"fraction": 0.12}, "argonWeekly": {"fraction": 0.05}} and a healthy claude payload
Then "dev_config.py quota-check --json" exits 2 and lists "programmer" with "sufficient": false and quota line "5H=12.0%, Argon=5.0%"
When the fetcher returns {} for every CLI
Then "dev_config.py quota-check --json" exits 0 and every persona carries "warning": "quota_unknown"

Scenario: [FPG-FR-02] [Tier A - Unit] Dispatch failures are classified as model failures only for quota, auth and missing CLI
Given dispatch results (exit 1, stderr "HTTP 429 Too Many Requests"), (exit 1, stderr "RESOURCE_EXHAUSTED"), (exit 127, stderr "agy: command not found"), (exit 1, stderr "401 Unauthorized") and (exit 1, stdout "3 failed, 10 passed")
When "classify_dispatch_failure" runs on each
Then the first four return "model_unavailable" and the fifth returns "task_failure"

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
