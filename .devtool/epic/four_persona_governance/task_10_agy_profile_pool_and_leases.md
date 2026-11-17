---
id: "task_10_agy_profile_pool_and_leases"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["config", "cli", "dispatch", "concurrency", "security", "architecture"]
order: "a10"
review_tier: "full"
---

# Task 10: Agy Profile Pool, Lease File and Pooled Dispatch

Epic: [four_persona_governance](four_persona_governance.en.md)

## Requirement Analysis

Let the Orchestrator and the autonomous runner spend `agy` quota across several Antigravity profiles, keep two
orchestrators (other epics, other repositories) from using one profile at the same time, and stop with a clear
report when every profile is out of quota, judging both the 5-hour and the weekly Gemini window ([SE-09](four_persona_governance.en.md#spec-errata)). It applies to
bindings whose CLI is `agy`; bindings on `claude`, `codex` and `kiro` are never touched.

1. **Files (`scripts/agy_profile_pool.py`, new)**: two global files under `$REAL_HOME/.d3nexus/`, with `$REAL_HOME`
   resolved as in Task 1.
   - `agy_profiles.json`: the configuration the Human edits through `dev_config.py profiles`. `schema_version` 1,
     `pool` (an ordered allow-list of `{"profile", "priority", "max_concurrent"}`), `lease_ttl_seconds`,
     `heartbeat_seconds`, `exhausted_recheck_seconds`, `agy_extra_args`. The pool is never derived from
     `antigravity_homes/`; an empty pool leaves dispatch exactly as it is today.
   - `agy_profile_leases.json`: the marker of which profile is in use and by whom, plus each profile's
     `exhausted_until` and a short quota cache.
   Every write holds the exclusive `fcntl` lock and atomic replace that Task 1 uses for persona files.
2. **Acquisition**: `acquire` walks the pool by priority, skips profiles that are leased, exhausted or in use by a
   resident Antigravity process, claims the first free one under the lock, and only then checks its quota (claim,
   then verify), so two orchestrators cannot pick the same profile. Quota is judged on both Gemini windows, the
   5-hour pool and the weekly pool; a profile that fails either is released and recorded as exhausted until the
   later of the failing windows resets, with the window named, because a weekly limit means days of waiting.
3. **Leases**: one lease per `ag_run` profile; a configurable number of `direct` leases on the profile that hosts the
   session. Leases are kept alive by heartbeats and become stale by age or by a dead owner process, so a crashed
   orchestrator never blocks a profile for long.
4. **Pooled dispatch (`scripts/agy_dispatch.py`, new)**: `run_on_pool` acquires a profile, launches `agy` on it,
   heartbeats while it runs, classifies the outcome, rotates to the next profile on a quota failure that happened
   before any work started, and always releases the lease.
5. **CLI (`scripts/dev_config.py`)**: `profiles list|add|remove|release|clear|probe`, `dispatch`, and a pool-aware
   `quota-check` for `agy` bindings.
6. **Exhaustion report**: when every pool profile is out of quota the result carries a report that tells the Human
   when each profile resets and how to continue: wait or top up the quota, or switch the programmer to another CLI
   with an exact `/d3nexus:dev-config set` command. The kit never switches model by itself.
7. **Skill (`skills/dev-config/SKILL.md`)**: documents `profiles` and `dispatch`; frontmatter stays `name` +
   `description` only.
8. **Tests**: `tests/test_fpg_agy_profile_pool.py` and `tests/test_fpg_agy_dispatch.py`, parametrised, with a
   temporary `REAL_HOME`, `PATH`, git repository and injected quota fetcher, resident-process probe and launcher.

## Files

Allowed files:
- `scripts/agy_profile_pool.py` (new)
- `scripts/agy_dispatch.py` (new)
- `scripts/dev_config.py`
- `skills/dev-config/SKILL.md`
- `tests/test_fpg_agy_profile_pool.py` (new)
- `tests/test_fpg_agy_dispatch.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — HLD Module Contracts, [SE-09]
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — spec §5.4, §8.5
- `scripts/persona_config.py` — `resolve_persona`, `build_dispatch_argv`, `classify_dispatch_failure`, the locked atomic file update, `$REAL_HOME` resolution
- `scripts/agy_quota.py` — `fetch_quota_for_profile`, `format_profile_for_dashboard`, `is_valid_antigravity_profile` (read only: never copy its constants or credentials)
- `.agents/rules/profile_isolation_rules.md` — profile isolation rules
- `skills/audit-account-block/references/profile-isolation-and-remediation.md` — isolation protocol

## Design Rationale

Quota belongs to an account, and `ag_run` edits a profile's database at every launch, so two launches of one
profile at the same time break the isolation rule that forbids editing a profile database while its process runs.
A single global lease file is the cheapest thing every orchestrator on the machine already shares. Applicable
skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: new `scripts/agy_profile_pool.py` and `scripts/agy_dispatch.py`;
  `scripts/dev_config.py`: `main` and `cmd_quota_check`; `skills/dev-config/SKILL.md`.
  `scripts/persona_config.py` and `scripts/agy_quota.py` are imported read-only.
- **Downstream Callers**: Task 3 (`lifecycle_runner.py` dispatch and halts), Task 5 (`check_tasks.py` payload and
  alerts), Task 6 (dispatch instructions), Task 8 (guides and `verify.sh` suites).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: every skip reason, every lease state, every dispatch status, every
  `profiles` subcommand and both launch forms.

### BDD SCENARIOS

Covers: FPG-HP-11, FPG-HP-12, FPG-EC-07, FPG-ST-07, FPG-AR-06, FPG-FR-05, FPG-FR-07


```gherkin
Scenario: [FPG-HP-11] [Tier A - Unit] Pool acquisition picks the first usable profile by priority and records why the others were skipped
Given a temporary REAL_HOME whose "agy_profiles.json" lists "p1", "p2", "p3", "p4", "p5" and "p6" with priorities 1 to 6, a 5-hour threshold of 0.15 and a weekly threshold of 0.02
And an injected quota fetcher returning ACTIVE with these gemini5h and geminiWeekly fractions: "p1" 0.10 and 0.50, "p2" 0.50 and 0.50, "p3" 0.60 and 0.50, "p4" 0.70 and 0.50, "p5" 0.90 and 0.01, "p6" 0.90 and 0.50, each pool with its own reset time
And "p2" holds a live lease owned by another orchestrator, "p3" has "exhausted_until" one hour in the future, and an injected resident-process probe returns true for "p4"
When "acquire" runs for an orchestrator whose host profile is "px"
Then it returns profile "p6" with via_ag_run true
And the skipped map equals {"p1": "quota", "p2": "leased", "p3": "exhausted", "p4": "resident_process", "p5": "quota"}
And "p1" now carries "exhausted_until" equal to its 5-hour reset time and exhausted_reason "5h"
And "p5" now carries "exhausted_until" equal to its weekly reset time and exhausted_reason "weekly"
When that orchestrator releases its lease and "acquire" runs again for an orchestrator whose host profile is "p6"
Then it returns profile "p6" with via_ag_run false

Scenario: [FPG-HP-12] [Tier C - Integration] The profiles CLI and dispatch drive stub CLIs through the pool
Given a temporary REAL_HOME with directories "antigravity_homes/p1" and "antigravity_homes/p2", a temporary PATH holding stub "agy" and "zsh" executables that record their argv, HOME and AGY_PROFILE, a temporary git repository as the working directory, and an injected quota fetcher returning sufficient quota
When "dev_config.py profiles add p1 --priority 1", "dev_config.py profiles add p2 --priority 2" and "dev_config.py profiles list --json" run
Then the JSON lists "p1" then "p2" with no lease
When "dev_config.py dispatch --persona programmer --prompt-file prompt.txt --cwd <repo> --log run.log --epic e1 --task t1" runs for host profile "host_x"
Then the stub "zsh" recorded a preflight call and a launch call containing "ag_run", "p1", "--model", "gemini-4-hydrogen-xhigh" and "--effort", "xhigh"
And "run.log" starts with "dispatch-profile: p1" and ends with "agy-exit=0"
And "dev_config.py profiles list --json" shows no lease for "p1" after the command returns
When the host profile is "p1" and the same dispatch runs again
Then the stub "agy" was called directly, the stub "zsh" was not called, and HOME was left unchanged

Scenario: [FPG-EC-07] [Tier A - Unit] Invalid pool changes are rejected and a launch without the ag_run helpers starts nothing
Given a temporary REAL_HOME with "antigravity_homes/real_p" as a directory, "antigravity_homes/link_p" as a symlink and no "antigravity_homes/ghost"
When "dev_config.py profiles add" runs for "ghost", "link_p", "bad name" and "real_p" with "--priority 0", then for "real_p" twice
Then "ghost", "link_p", "bad name" and the priority 0 request each exit 1 with a message naming the rejected value
And the second "real_p" add exits 1 with a message containing "already"
And the pool file holds only "real_p"
When "dev_config.py profiles remove real_p" runs while "real_p" holds a live lease
Then it exits 1 naming the lease owner and the lease file is unchanged
When a dispatch targets a non-host profile and the preflight command "zsh -ic 'typeset -f _ag_link_ok _ag_rel_link ag_run'" exits non-zero
Then nothing is launched, the lease is released and the result status is "preflight_failed"

Scenario: [FPG-ST-07] [Tier A - Unit] A lease is kept alive by heartbeats and reclaimed when it goes stale
Given orchestrator "o1" holding a lease on "p1" acquired at 10:00 UTC with a time-to-live of 180 seconds on a host named "h1"
When "heartbeat" runs at 10:02 UTC and the lease is checked at 10:04:30 UTC
Then the lease is live
When the lease is checked at 10:05:30 UTC with no further heartbeat
Then the lease is stale and "acquire" for orchestrator "o2" returns "p1"
And a lease on host "h1" whose owner pid is not running is stale 5 seconds after its last heartbeat
And a lease held on another host is stale only by heartbeat age
When "release" runs for "o2" twice
Then "p1" has no lease and the second call changes nothing

Scenario: [FPG-AR-06] [Tier A - Unit] Concurrent orchestrators never share a profile and never lose lease-file updates
Given a pool of "p1" and "p2" and a stub quota fetcher returning sufficient quota
When 6 processes call "acquire" at the same time with distinct owners, a host profile "px" and a wait of 0 seconds, and keep their leases
Then exactly 2 processes receive a profile, one "p1" and one "p2", and the other 4 receive profile None with reason "pool_busy"
And the leases file holds exactly two leases with distinct owner ids and schema_version 1

Scenario: [FPG-FR-05] [Tier A - Unit] Dispatch rotates to the next profile only before any work started
Given a pool of "p1" and "p2" with sufficient quota and a stub launcher
When the launcher fails on "p1" with stderr "RESOURCE_EXHAUSTED: quota exceeded" and the working tree and HEAD are unchanged
Then "p1" gets "exhausted_until", its lease is released, the dispatch retries on "p2", and the result is status "ok" with profile_used "p2" after 2 attempts
When the launcher fails on "p1" with the same stderr after it created a commit in the working tree
Then there is no retry, the result is status "quota_midrun" with profile_used "p1", and "p1" is marked exhausted and released
When the launcher fails on every pool profile with the quota stderr and an unchanged tree
Then the result is status "no_profile" with reason "pool_exhausted" after one attempt per profile, and no lease remains
When the launcher exits 1 with stdout "3 failed, 10 passed"
Then the result is status "task_failure", "p1" is not marked exhausted, and its lease is released

Scenario: [FPG-FR-07] [Tier A - Unit] An exhausted pool yields a report that tells the Human how to continue, and a top-up recovers it
Given a pool of "p1" and "p2" whose quota fetcher returns ACTIVE with gemini5h 0.02 and geminiWeekly 0.50 for "p1" (5-hour reset 2026-11-17T11:43:00Z) and gemini5h 0.60 and geminiWeekly 0.01 for "p2" (weekly reset 2026-11-21T00:54:00Z), a catalogue holding "codex-gpt" and "kiro-opus", a PATH holding "codex" but not "kiro", and "programmer" bound to "hydrogen" with effort "xhigh"
When "acquire" runs at 10:00 UTC on 2026-11-17
Then it returns profile None with reason "pool_exhausted"
And "p1" carries exhausted_reason "5h" with "exhausted_until" 2026-11-17T11:43:00Z and "p2" carries exhausted_reason "weekly" with "exhausted_until" 2026-11-21T00:54:00Z
And the report contains the lines "- p1: 5-hour limit reached (resets 2026-11-17T11:43:00Z)" and "- p2: weekly limit reached (resets 2026-11-21T00:54:00Z)"
And the report states "Earliest reset: 2026-11-17T11:43:00Z."
And the report offers "wait for the reset or top up the quota", "/d3nexus:dev-config set programmer codex-gpt xhigh" and "/d3nexus:dev-config set programmer kiro-opus high"
And the "kiro-opus" line says the "kiro" CLI is not on PATH
When the fetcher then returns gemini5h 0.60 and geminiWeekly 0.50 for "p1" and "acquire" runs at 10:11 UTC, more than 600 seconds after the last probe
Then it returns profile "p1"
When "p2" is marked exhausted again and "dev_config.py profiles clear p2" runs
Then "p2" has no "exhausted_until", no exhausted_reason and no cached quota
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_agy_profile_pool.py::test_fpg_hp_11_pool_selection_priority_and_skip_reasons` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py tests/test_fpg_provider_shortcut.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py scripts/agy_profile_pool.py scripts/agy_dispatch.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py scripts/agy_profile_pool.py scripts/agy_dispatch.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_10.xml tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py` | exit 0; results build/test-results/fpg_task_10.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- A decision below names a quota payload key or function behaviour that `agy_quota.py` does not have. Read
  `format_profile_for_dashboard` for the real key names and report `BLOCKED` instead of guessing.

## Decisions Already Made

**Files and schema**
- New contract: `POOL_SCHEMA_VERSION = 1`. Paths: `$REAL_HOME/.d3nexus/agy_profiles.json` and
  `$REAL_HOME/.d3nexus/agy_profile_leases.json`; `$REAL_HOME` is resolved as in `persona_config.py` and every
  public function accepts `real_home` for tests. Neither file is ever created under a repository.
- New contract: `agy_profiles.json` keys are exactly `schema_version`, `pool`, `lease_ttl_seconds` (default 180),
  `heartbeat_seconds` (default 30), `exhausted_recheck_seconds` (default 600), `agy_extra_args` (list of strings,
  default `[]`); any other key, a wrong type or another `schema_version` is rejected with a message naming it. A
  pool entry is `{"profile": str, "priority": int >= 1, "max_concurrent": int >= 1}`; `max_concurrent` defaults
  to 2 and counts only `direct` leases. Order is `(priority, profile)`.
- New contract: `agy_profile_leases.json` is `{"schema_version": 1, "profiles": {"<profile>": {"leases": [...],
  "exhausted_until": ISO-8601 UTC or null, "exhausted_checked_at": ISO-8601 UTC or null, "exhausted_reason":
  `"5h"`, `"weekly"`, `"5h+weekly"`, `"status:<STATUS>"` or null, "quota": {"status", "gemini5h", "geminiWeekly",
  "argonWeekly", "fetched_at"} or null}}}`. A lease is `{"owner_id" (uuid4 hex), "repo", "epic",
  "task", "slot", "role" ("orchestrator" or "runner"), "launch" ("ag_run" or "direct"), "pid", "host",
  "acquired_at", "heartbeat_at"}`. Neither file ever stores an e-mail address, token, password or path inside a
  profile; the quota cache keeps only the fields listed.
- A profile name matches `^[a-zA-Z0-9_-]+$`, names an existing directory `$REAL_HOME/antigravity_homes/<name>`
  that is not a symlink, and appears once. The module only reads that path's existence; it never writes under
  `antigravity_homes/`.

**Capacity, stale leases, skip reasons**
- New contract: the profile that hosts the session is `AGY_PROFILE` when set, else the profile directory name in
  `HOME` when `HOME` contains `/antigravity_homes/`, else `None`. A launch on the host profile is `direct`
  (`agy` is run with the inherited environment); a launch on any other profile is `ag_run`.
- New contract: an `ag_run` lease needs a profile with no live lease at all and is the only lease on it. A
  `direct` lease needs a profile with no live `ag_run` lease and fewer live `direct` leases than `max_concurrent`.
  A refusal for either reason is the skip reason `"leased"`.
- New contract: a lease is stale when `now - heartbeat_at > lease_ttl_seconds`, or when its `host` equals this
  host's name and `os.kill(pid, 0)` reports the process is gone. A lease from another host is stale by age only.
  Stale leases are purged under the lock at the start of every `acquire`, `status` and `release`.
- New contract: `acquire(owner, *, real_home, host_profile, quota_pool="gemini5h", thresholds, fetcher,
  resident_probe, wait_seconds=0, poll_seconds=15, now=None) -> Acquisition`; `thresholds` is the `quota_thresholds`
  mapping. `Acquisition` carries `profile`
  (or `None`), `via_ag_run`, `owner_id`, `skipped` (profile to reason) and `reason`, which is `None` on success
  and otherwise `"pool_empty"`, `"pool_exhausted"` (every pool profile is exhausted) or `"pool_busy"` (at least one
  profile still has quota but none was free for `wait_seconds`). Skip reasons are the exact strings `"exhausted"`,
  `"leased"`, `"resident_process"`, `"quota"` and `"status:<STATUS>"`.
- New contract: for each pool entry in order: (1) skip as `"exhausted"` when `exhausted_until > now` and
  `now - exhausted_checked_at < exhausted_recheck_seconds`; an entry whose recheck interval has passed is probed
  again; (2) skip as `"leased"` on a capacity refusal; (3) skip as `"resident_process"` when the profile is not the
  host profile and `resident_probe(profile)` is true; (4) claim the lease under the lock, re-validating capacity
  inside the lock; (5) outside the lock take the quota from the cache when `fetched_at` is under 120 seconds old,
  else call `fetcher(profile)`; (6) judge it with `evaluate_agy_quota`; a status other than `ACTIVE` releases the
  claim, skips as `"status:<STATUS>"`, sets `exhausted_reason` to `"status:<STATUS>"` and `exhausted_until` to
  `now + exhausted_recheck_seconds`; (7) a failing window releases the claim, skips as `"quota"`, sets
  `exhausted_reason` to `"5h"`, `"weekly"` or `"5h+weekly"`, sets `exhausted_until` to the LATEST reset time among
  the failing windows (else `now + exhausted_recheck_seconds` when none is given) and `exhausted_checked_at = now`;
  (8) otherwise return it.
- New contract: `evaluate_agy_quota(payload, quota_pool, thresholds) -> QuotaVerdict` with `sufficient` and
  `failing`, a list of `{"window", "fraction", "threshold", "reset_at"}`. For `quota_pool == "gemini5h"` (every
  agy model that is not Argon) BOTH windows must pass: the 5-hour window is `payload["gemini5h"]["fraction"] >=
  thresholds["5h_min_fraction"]` and the weekly window is `payload["geminiWeekly"]["fraction"] >
  thresholds["7d_min_fraction"]`, strictly greater, exactly as `evaluate_provider_quota` treats the weekly window of
  Claude and Codex. For `quota_pool == "argonWeekly"` only `payload["argonWeekly"]["fraction"] >=
  thresholds["agy_argon_min_fraction"]` is judged. A pool that is missing from the payload or has no `fraction`
  is unknown and passes (the quota gate's `quota_unknown` rule); an empty payload is sufficient. `unavailable` and
  `countdown` are ignored.
- New contract: `fetcher(profile)` returns the dictionary shape of `agy_quota.format_profile_for_dashboard`: `status`
  and the pools `gemini5h`, `geminiWeekly` and `argonWeekly`, each a dictionary with `fraction` and `resetTime`
  (ISO-8601 UTC). The default fetcher
  loads `scripts/agy_quota.py` by path and calls `fetch_quota_for_profile`; tests inject a stub. `thresholds`
  comes from `quota_thresholds` exactly as `quota-check` reads it; `quota_pool` follows the binding's `quota_pool`.
- New contract: the default `resident_probe(profile)` runs `pgrep -f "antigravity_homes/<profile>/"` and is true
  when it finds a process. `release(owner_id)` is a no-op when the lease is already gone.
  `heartbeat(owner_id)` refreshes `heartbeat_at`. `mark_exhausted(profile, until)` and
  `clear_exhausted(profile=None)` edit only `exhausted_until`, `exhausted_checked_at` and `quota`.
- New contract: `pool_status(real_home, *, now=None) -> dict` returns `{"state", "profiles", "earliest_reset"}`.
  `state` is `"empty"` (no pool), `"exhausted"` (every pool profile has `exhausted_until > now`), `"busy"` (not
  exhausted and every non-exhausted profile is at capacity) or `"ok"`. Each profile entry has `profile`,
  `priority`, `leased_by` (list of `epic`, `task`, `slot`, `role`, `repo`), `exhausted_until`,
  `exhausted_reason` and `quota`; `earliest_reset` is the smallest `exhausted_until`.

**Exhaustion report**
- New contract: `exhaustion_report(status, *, catalogue, programmer_binding, which=shutil.which, fetcher=None) ->
  list[str]` returns, for state `"exhausted"`: the first line `Stopped: all agy profiles are out of quota.`; one
  line per pool profile, `- <profile>: <reason> (resets <ISO UTC>)`, where `<reason>` is `5-hour limit reached` for
  `exhausted_reason` `5h`, `weekly limit reached` for `weekly`, `5-hour and weekly limits reached` for `5h+weekly`
  and `account status <STATUS>` for `status:<STATUS>`, and `<ISO UTC>` is `YYYY-MM-DDTHH:MM:SSZ`;
  `Earliest reset: <ISO UTC>.`; the line
  `Options:`; the line `- wait for the reset or top up the quota of a profile, then run "/d3nexus:dev-config
  profiles clear" and resume`; and one line per non-`agy` CLI in the order `codex`, `kiro`, `claude`:
  `- switch the programmer: /d3nexus:dev-config set programmer <alias> <effort>` followed by
  ` ("<cli>" CLI not on PATH)` when `which(cli)` is `None`. `<alias>` is the first catalogue alias of that CLI;
  `<effort>` is the programmer's current effort when the alias lists it, else the alias's last listed effort. For
  state `"busy"` the first line is `Stopped: every agy profile stayed in use for <wait> seconds.` followed by one
  `- <profile> is held by <epic>/<task>/slot <n>` line per holder.

**Dispatch**
- New contract: `run_on_pool(binding, mode, *, prompt_file, cwd, log, owner, real_home, extra_env=None,
  wait_seconds=0, launcher=None, fetcher=None, resident_probe=None, preflight=None) -> DispatchResult` with
  `status`, `profile_used`, `attempts`, `exit_code`, `reason` and `report`. Statuses are the exact strings `"ok"`,
  `"task_failure"`, `"model_unavailable"`, `"quota_midrun"`, `"no_profile"` and `"preflight_failed"`.
- New contract: the agy arguments are `build_dispatch_argv(binding, mode)[1:]` followed by `agy_extra_args`. A
  `direct` launch runs `["agy", *args]`. An `ag_run` launch runs `["zsh", "-ic", 'ag_run "$0" cli "$@"', profile,
  *args]` with `REAL_HOME` set. The prompt is passed on standard input from `prompt_file`.
- New contract: before the first `ag_run` launch the preflight runs `["zsh", "-ic", "typeset -f _ag_link_ok
  _ag_rel_link ag_run >/dev/null"]`. A non-zero exit releases the lease and returns `"preflight_failed"` with
  nothing launched: `ag_run` deletes a profile's symlinks when its helper functions are missing.
- New contract: while the launched process runs, a heartbeat refreshes the lease every `heartbeat_seconds`. The
  lease is released in a `finally` block on every path, including a signal.
- New contract: `classify_dispatch_failure` decides the status. Exit 0 is `"ok"`; `"task_failure"` is returned as
  is. A `model_unavailable` whose stderr matches a quota signature (`429`, `resource_exhausted`, `quota exceeded`
  or `exhausted`, `usage limit`, `rate limit exceeded`) calls `mark_exhausted` and then: when `git rev-parse HEAD`
  and `git status --porcelain` in `cwd`, ignoring `.vscode/settings.json`, are unchanged from before the launch and
  profiles remain, retry once on the next profile; when they changed, return `"quota_midrun"` without retrying.
  Any other `model_unavailable` returns `"model_unavailable"` without rotating. A `cwd` that is not a git work tree
  counts as changed.
- New contract: for each attempt the log starts with `dispatch-profile: <profile> (<launch>)` and ends with
  `agy-profile=<profile>`, optionally `agy-quota-exhausted=1`, and `agy-exit=<code>`.
- New contract: an empty pool makes `run_on_pool` launch once on the host profile with no lease, exactly as a
  caller does today. Nothing in this task changes behaviour for a user who has not run `profiles add`.

**CLI**
- New contract: `dev_config.py profiles list [--json]`, `add NAME [--priority N] [--max-concurrent N]`,
  `remove NAME`, `release NAME [--force]`, `clear [NAME]`, `probe [NAME]`. `remove` and `release` refuse a
  profile with a live lease unless `--force` (`remove` has no `--force`: release first), and say which owner holds
  it. `probe` calls the fetcher and refreshes the quota cache. Exit `0` success, `1` validation or usage error.
  Writes take the lock described in Requirement 1.
- New contract: `dev_config.py dispatch --persona P [--mode write|read-only] --prompt-file F --cwd D --log L
  [--epic E] [--task T] [--slot N] [--role orchestrator|runner] [--wait SECONDS]` prints one JSON object with the
  `DispatchResult` fields and the `report` as a list of lines. Exit `0` for `"ok"`, `2` for `"no_profile"` and
  `"quota_midrun"`, `1` for every other status and for usage errors. A persona bound to a CLI other than `agy` is
  launched directly with `build_dispatch_argv` and never touches the pool.
- New contract: for a persona bound to `agy`, `cmd_quota_check` judges the quota with `evaluate_agy_quota` whether
  or not a pool is configured, so the weekly window counts as well. A payload without `geminiWeekly` gives exactly
  the Task 1 result and quota line; when the weekly figure is present the line is `5H=<pct>% 7D=<pct>%`. With a
  non-empty pool the persona is sufficient when a dry run of `acquire` (no claim, no wait) finds a profile, and its
  quota line names that profile. Bindings on other CLIs are unchanged.

**Isolation (from the two profile isolation documents; every item is a hard rule)**
- Never export or set `HOME`, `AGY_PROFILE` or `TMPDIR` for the calling process; a profile is entered only through
  `ag_run <profile> cli` inside `zsh -ic`, which sets them for that one command.
- Never call `security`, `pkill` or `kill` on a profile, never touch the default keychain, never open or write
  `state.vscdb`, `storage.json`, `conversation_summaries.db` or a keychain, and never create, remove or edit
  anything under `antigravity_homes/`.
- Nothing in these modules, tests or fixtures contains a keychain password, token or e-mail address.
- Tests never run `ag_run` or the real `zsh -ic`, never read `~/.d3nexus`, `antigravity_homes`, `~/.zshrc` or
  `~/.gemini`, and never call a real model CLI. They use stub executables on a temporary `PATH`.

**Tests**
- Test names: `test_fpg_hp_11_pool_selection_priority_and_skip_reasons`,
  `test_fpg_st_07_lease_lifecycle_heartbeat_and_stale_reclaim`,
  `test_fpg_ar_06_concurrent_acquirers_never_share_a_profile`, `test_fpg_ec_07_invalid_pool_use_is_rejected` and
  `test_fpg_fr_07_exhausted_pool_report_and_recovery` in `tests/test_fpg_agy_profile_pool.py`;
  `test_fpg_fr_05_dispatch_rotates_only_before_work_starts`, `test_fpg_ec_07_preflight_failure_launches_nothing`
  and `test_fpg_hp_12_profiles_cli_and_dispatch_with_stub_clis` in `tests/test_fpg_agy_dispatch.py`. Tests load
  the modules through `importlib.util.spec_from_file_location` inside fixtures so the RED row fails as a test
  failure (exit `1`).

## Definition of Done

- FPG-HP-11, FPG-HP-12, FPG-EC-07, FPG-ST-07, FPG-AR-06, FPG-FR-05 and FPG-FR-07 pass. (V2, V5)
- Ruff and mypy pass on the new and changed modules. (V3, V4)
- `skills/dev-config/SKILL.md` frontmatter holds exactly `name` and `description`, and the skill documents
  `profiles` and `dispatch`. (Gate 5)
- The two global files and the log contain no token, e-mail address or password. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](task_01_persona_config_and_dev_config_cli.md) and [Task 9](task_09_provider_quick_setup.md), because
both edit `scripts/dev_config.py` and `skills/dev-config/SKILL.md`.

Downstream dependents (blocked by Task 10): `task_03`, `task_05`.

## References & Rollback

- [Epic HLD](four_persona_governance.en.md)
- **Rollback**: Revert the task commit. Delete `$REAL_HOME/.d3nexus/agy_profiles.json` and
  `agy_profile_leases.json` if they were created.
