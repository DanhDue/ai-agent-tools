# BDD Scenarios: Task Review Cap Blocker-Only Triage and Two-Tier Risk Short-Circuit

## Table of Contents

- [1. Happy Path Scenarios (HP)](#1-happy-path-scenarios-hp)
- [2. Edge Case Scenarios (EC)](#2-edge-case-scenarios-ec)
- [3. State Transition Scenarios (ST)](#3-state-transition-scenarios-st)
- [4. Architecture and Concurrency Scenarios (AR)](#4-architecture-and-concurrency-scenarios-ar)
- [5. Fault Resilience Scenarios (FR)](#5-fault-resilience-scenarios-fr)

---

## 1. Happy Path Scenarios (HP)

```gherkin
Scenario: [TRC-HP-01] [Tier A - Unit] Layered persona configuration resolves default and overridden task review and fix pass limits
Given a temporary REAL_HOME and project root with no custom personas.json files
When "resolve_task_review_limits" and "dev_config.py status --json" run against the project root
Then "resolve_task_review_limits" returns "(2, 1)" matching "scripts/personas.default.json" and ".agents/config/personas.json"
And the status JSON includes "task_review_limits" equal to {"max_task_review_passes": 2, "max_fix_passes": 1}
When global ".d3nexus/personas.json" sets {"schema_version": 1, "max_task_review_passes": 3, "max_fix_passes": 2} and project ".agents/config/personas.json" sets {"schema_version": 1, "max_fix_passes": 1}
Then "resolve_task_review_limits" returns "(3, 1)" reflecting kit -> global -> project precedence

Scenario: [TRC-HP-02] [Tier A - Unit] Task-reviewer brief emitter renders Pass 1 comprehensive rubric and Pass 2 delta-only rubric without Vietnamese mirror paths
Given an isolated git repository with epic "trc_epic" holding "trc_epic.md", "bdd_scenarios.md", and an ignored "trc_epic.vi.md"
And a blockers file "pass1_blockers.json" containing [{"id": "BLK-1", "category": "BDD_VIOLATION", "file": "src/app.py", "summary": "Missing null guard"}]
When "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic" runs for Pass 1
Then stdout exits 0, names "Role 2.1 AI Architect & Reviewer", includes '"verdict": "APPROVED|CHANGES_REQUESTED"', defines "BLOCKER" versus "NON_BLOCKING_OBSERVATION", and omits ".vi.md"
When "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic --review-pass 2 --pass1-tree-sha 4b825dc642cb --blockers-file pass1_blockers.json" runs
Then stdout exits 0, includes "git diff 4b825dc642cb", embeds "BLK-1", forbids introducing new non-regression findings in Pass 2, and omits ".vi.md"

Scenario: [TRC-HP-03] [Tier C - Integration] Clean surgical Fix Pass 1 passes Tier 1 eligibility and short-circuits via Tier 2 LOW finalize-slot
Given an initialized 2-slot worker pool for epic "trc_demo" where slot 1 completed Pass 1 review ("review_passes_used" == 1) and transitioned to Fix Pass 1 ("fix_passes_used" == 1) with blocker "BLK-1"
And Fix Pass 1 inserts 8 lines inside an internal helper of "src/worker.py" and adds 4 assertion lines in "tests/test_worker.py" with passing task checks and BDD traceability
When "manage_worker_pool.py triage-fix trc_demo --slot 1 --task task_01" runs
Then exit code is 0 and stdout JSON has "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT", "triggers" == [], "non_test_changed_lines" == 8, and a non-empty "bounded_diff"
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode tier2-short-circuit --risk-level LOW --rationale 'Directly resolves BLK-1 with zero side effects'" runs
Then exit code is 0, "task_01" status in ".devtool/features/" is synced to "done", the slot commit is merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" in the main epic worktree contains one entry with "mode": "tier2-short-circuit" and "risk_level": "LOW", and slot 1 heartbeat resets to "status": "idle" with "review_passes_used": 0 and "fix_passes_used": 0

Scenario: [TRC-HP-04] [Tier C - Integration] End-to-end runner parity and verify.sh registration enforce Pass 1 non-blocking approval and Pass 2 cap
Given an isolated git repository with an English-only epic of two review-gated tasks and stub persona CLIs
When Task 1's Pass 1 reviewer returns {"task_id": "task_01", "pass": 1, "verdict": "APPROVED", "head_sha": "<sha1>", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/a.py", "summary": "Style nit"}]}
And Task 2's Pass 1 reviewer returns {"task_id": "task_02", "pass": 1, "verdict": "CHANGES_REQUESTED", "head_sha": "<sha2>", "done_gate": "PASS", "blockers": [{"id": "BLK-1", "category": "BDD_VIOLATION", "file": "src/b.py", "summary": "Fix return code", "remediation": "Return 0"}], "observations": []} followed by Fix Pass 1 producing "<sha2_fix>" and Pass 2 Delta-Only {"task_id": "task_02", "pass": 2, "verdict": "APPROVED", "head_sha": "<sha2_fix>", "done_gate": "PASS", "blockers": [], "observations": []}
Then Task 1 finalizes after exactly 1 review pass and 0 fix passes with "OBS-1" recorded in "review_audit_notes.jsonl"
And Task 2 finalizes after exactly 2 review passes and 1 fix pass with Pass 2 prompt containing Delta-Only instructions
And "scripts/verify.sh" lists all four "tests/test_trc_*.py" suites in "SUITES"
```

---

## 2. Edge Case Scenarios (EC)

```gherkin
Scenario: [TRC-EC-01] [Tier A - Unit] Invalid or boolean task review limit values in personas.json raise PersonaConfigError
Given a temporary project root with kit defaults present
When ".agents/config/personas.json" sets any of {"max_task_review_passes": 0}, {"max_task_review_passes": -1}, {"max_task_review_passes": true}, {"max_task_review_passes": "2"}, {"max_fix_passes": -1}, or {"max_fix_passes": false}
Then loading or validating persona config raises "PersonaConfigError" naming the invalid key

Scenario: [TRC-EC-02] [Tier A - Unit] Parser Coercion Guard converts zero-blocker CHANGES_REQUESTED to APPROVED and blocks Fix Pass 1 without blockers
Given a reviewer JSON payload {"task_id": "task_03", "pass": 1, "verdict": "CHANGES_REQUESTED", "head_sha": "abc1234", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/x.py", "summary": "Nitpick"}]}
When "normalize_task_review_payload" evaluates the payload
Then the normalized payload has "verdict" == "APPROVED" and "coerced_from_non_blocking" == True
And running "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset --review-file coerced.json" exits with code 2 and stderr containing "NO_BLOCKER_FOR_FIX_PASS"

Scenario: [TRC-EC-03] [Tier A - Unit] Tier 1 heuristic boundary and sensitive-surface triggers classify HIGH_RISK accurately
Given a slot worktree with a captured "pass1_tree_sha" and "fix_passes_used" == 1
When Fix Pass 1 inserts exactly 30 internal lines in "src/calc.py" with zero signature/API/DB/concurrency hits and adds 1 test assertion
Then "triage-fix" returns "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT" and "non_test_changed_lines" == 30
When Fix Pass 1 instead introduces (a) 31 inserted non-test lines, (b) a modified public "def compute_score(" signature, (c) an "@router.post" or "BaseModel" change, (d) an SQL "UPDATE " or "sqlite3" change, (e) a "threading.Lock(" or "os.killpg(" change, or (f) removes an "assert " line in "tests/test_calc.py" without replacement
Then in every case (a) through (f) "triage-fix" returns "tier1_status" == "HIGH_RISK", "bounded_diff" == None, and the corresponding trigger code in "triggers"

Scenario: [TRC-EC-04] [Tier C - Integration] Pass 2 residual CHANGES_REQUESTED with green mechanical gates finalizes to done with audit note and zero Fix Pass 2
Given slot 1 of epic "trc_demo" has completed Review Pass 2 ("review_passes_used" == 2, "fix_passes_used" == 1)
And "run_task_checks.py status" reports "done gate: PASS" and "check_bdd_traceability.py" exits 0
And Pass 2 reviewer file "pass2.json" contains {"task_id": "task_03", "pass": 2, "verdict": "CHANGES_REQUESTED", "head_sha": "<sha>", "done_gate": "PASS", "blockers": [{"id": "BLK-2", "category": "BDD_VIOLATION", "file": "src/worker.py", "summary": "Residual nit"}], "observations": []}
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_03 --mode pass2-complete --review-file pass2.json" runs
Then exit code is 0, "task_03" is marked "done" and merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" records an entry with "event" == "pass2_residual_logged_on_cap" and "BLK-2", and zero additional fix passes execute
```

---

## 3. State Transition Scenarios (ST)

```gherkin
Scenario: [TRC-ST-01] [Tier C - Integration] Worker pool enforces idempotent re-sync and max_task_review_passes = 2 while rejecting a third review pass with exit code 2
Given an initialized slot 1 for epic "trc_demo" with "max_task_review_passes" == 2 and "max_fix_passes" == 1
When "sync --slot 1 --task task_01 --status review" runs twice in a row for Pass 1, followed by "sync --slot 1 --status working --no-reset" with 1 blocker, followed by "sync --slot 1 --status review" for Pass 2
Then the duplicate Pass 1 review sync is idempotent keeping "review_passes_used" == 1, Fix Pass 1 sets "fix_passes_used" == 1, and Pass 2 sets "review_passes_used" == 2
When a third transition into "review" is attempted after "working" or when "review_passes_used" == 2 with a new review pass request
Then the third review transition exits with code 2, stderr contains "HARD_REVIEW_CAP_EXCEEDED", and "review_passes_used" remains 2

Scenario: [TRC-ST-02] [Tier C - Integration] Worker pool enforces max_fix_passes = 1 and rejects a second fix pass with exit code 2
Given slot 1 of epic "trc_demo" has "review_passes_used" == 2 and "fix_passes_used" == 1 after Review Pass 2
When "manage_worker_pool.py sync trc_demo --slot 1 --status working --no-reset" runs
Then the command exits with code 2, stderr contains "HARD_FIX_CAP_EXCEEDED", and "fix_passes_used" remains 1

Scenario: [TRC-ST-03] [Tier A - Unit] Temporary GIT_INDEX_FILE snapshot isolates Fix Pass 1 delta from uncommitted Pass 1 changes without touching HEAD or index
Given slot 1 has 220 uncommitted lines added in "src/feature_big.py" during Pass 1 implementation
When "manage_worker_pool.py sync trc_demo --slot 1 --task task_03 --status review" captures "pass1_tree_sha"
Then "git rev-parse HEAD" and the SHA-256 digest of ".git/index" (slot git index) before and after "sync --status review" are identical
When Fix Pass 1 inserts 6 lines in "src/feature_big.py" after "sync --status working --no-reset"
Then "triage-fix" reports "non_test_changed_lines" == 6 (not 226) and "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT"

Scenario: [TRC-ST-04] [Tier C - Integration] Headless lifecycle_runner caps review passes at 2 and finalizes on Pass 2 completion when done_gate is PASS
Given an autonomous "LifecycleRunner" configured with default limits ("max_task_review_passes" == 2, "max_fix_passes" == 1) and a review-gated task "task_01"
When Pass 1 "task-reviewer" returns "CHANGES_REQUESTED" with 1 blocker, Fix Pass 1 succeeds, and Pass 2 "task-reviewer" returns residual "CHANGES_REQUESTED" with "done_gate": "PASS" and matching "head_sha"
Then the runner dispatches "task-implementer" exactly twice (initial + Fix Pass 1) and "task-reviewer" exactly twice (Pass 1 + Pass 2), logs "pass2_residual_logged_on_cap" to "review_audit_notes.jsonl", and marks "task_01" done
```

---

## 4. Architecture and Concurrency Scenarios (AR)

```gherkin
Scenario: [TRC-AR-01] [Tier A - Unit] Governance rules and skills document bounded Role 2.2 triage-fix and finalize-slot exceptions within strict byte and word caps
Given the repository governance files "rules/CRITICAL_RULES.md", "skills/dev-lifecycle/references/orchestration-roles.md", "skills/dev-lifecycle/references/governance-checklists.md", "skills/dev-lifecycle/SKILL.md", "skills/dev-lifecycle/references/handoff-template.md", "skills/dev-implementation/SKILL.md", and "skills/subagent-driven-development/SKILL.md"
When governance text contract checks execute
Then UTF-8 byte length of "rules/CRITICAL_RULES.md" is <= 8192 and Rule 6 does not contain "APPROVED"
And word count of "skills/dev-lifecycle/SKILL.md" is <= 2500, word count of "skills/dev-implementation/SKILL.md" is <= 4500, and all three "MANDATORY: read [references/...]" pointers remain intact
And "orchestration-roles.md" and "dev-implementation/SKILL.md" document "triage-fix", "finalize-slot" (including its internal read-only mechanical status gates), "BLOCKER", "NON_BLOCKING_OBSERVATION", and the bounded "<= 30" non-test line Role 2.2 Tier 2 RiskAssessment exception while still forbidding direct reading/editing of "src/" and "tests/"

Scenario: [TRC-AR-02] [Tier C - Integration] Concurrent slot 1 and slot 2 pool operations preserve independent per-slot review and fix counters
Given an initialized 2-slot worker pool for epic "trc_conc" with "task_01" in slot 1 and "task_02" in slot 2
When slot 1 transitions through Pass 1 review ("review_passes_used" == 1) and Fix Pass 1 ("fix_passes_used" == 1) while slot 2 transitions to Pass 1 review ("review_passes_used" == 1, "fix_passes_used" == 0)
Then ".devtool/state/trc-conc.heartbeat.json" preserves distinct "pass1_tree_sha" values, "fix_passes_used" == 1 on "slot-1", "fix_passes_used" == 0 on "slot-2", and "active_tasks" == ["task_01", "task_02"]

Scenario: [TRC-AR-03] [Tier C - Integration] Slot merge and finalize-slot reconcile tracked and untracked .devtool/features mirrors and preserve main_wt audit notes across parallel slots
Given a main epic worktree ".worktrees/trc_mirror" whose ".devtool/features/task_01.md" has unstaged edits and whose ".devtool/features/done/task_01.md" exists untracked from cross-worktree status syncing
And both slot 1 ("task_01") and slot 2 ("task_02") finalize with audit notes written to ".devtool/epic/trc_mirror/review_audit_notes.jsonl" in ".worktrees/trc_mirror"
When "manage_worker_pool.py finalize-slot" merges slot 1 and then slot 2 into ".worktrees/trc_mirror"
Then tracked and untracked ".devtool/features/" mirrors in ".worktrees/trc_mirror" are reconciled before each merge, both merges exit 0 without add/add conflict, ".devtool/epic/trc_mirror/review_audit_notes.jsonl" retains both slots' audit lines, and any non-".devtool/" dirty file in ".worktrees/trc_mirror" is never discarded
```

---

## 5. Fault Resilience Scenarios (FR)

```gherkin
Scenario: [TRC-FR-01] [Tier A - Unit] Missing optional persona config layers fall back to kit defaults while malformed JSON fails closed
Given a temporary project root with no ".agents/config/personas.json" and an empty temporary REAL_HOME
When "resolve_task_review_limits" runs
Then it returns "(2, 1)" without error
When ".agents/config/personas.json" contains truncated invalid JSON "{bad"
Then "resolve_task_review_limits" raises "PersonaConfigError" naming ".agents/config/personas.json"

Scenario: [TRC-FR-02] [Tier C - Integration] finalize-slot aborts with exit code 1 when mechanical done_gate or BDD traceability fails
Given slot 1 of epic "trc_demo" has uncommitted changes for "task_01" where "run_task_checks.py status" outputs "done gate: FAIL"
When "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode pass1-approved" runs
Then the command exits with code 1, stderr contains "MECHANICAL_GATE_FAILED", no commit or merge occurs on "epic/trc-demo", and slot 1 retains its uncommitted working tree for diagnosis

Scenario: [TRC-FR-03] [Tier A - Unit] Unparseable or missing task-reviewer JSON output fails closed without triggering Coercion Guard
Given raw reviewer stdout containing prose with no fenced JSON block or a malformed JSON block "{not valid json}"
When "lifecycle_runner.py" or "normalize_task_review_payload" processes the reviewer output
Then it never coerces the verdict to "APPROVED", records "verdict=UNPARSEABLE", and respects the "max_task_review_passes" bound without infinite retries
```
