---
id: "task_01_persona_config_and_dev_config_cli"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["config", "cli", "dispatch", "quota", "architecture", "security"]
order: "a1"
review_tier: "full"
---

# Task 1: Persona Config, Dispatch, Quota Gate and the dev-config Skill

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Create the `dev-config` skill end to end: layered persona configuration, dispatch argv, failure
classification and the quota gate (spec §5, §8.3–§8.5; layout per [SE-03]).

1. **Kit defaults (`scripts/personas.default.json`)**: `schema_version` 1, `active_preset` `"default"`, the
   `models` catalogue (`argon`, `hydrogen`, `claude-opus`, `claude-sonnet`, `codex-gpt`, `kiro-opus`), the
   five presets of spec §5.2 (`default`, `gemini-saver`, `claude-hybrid`, `all-hydrogen`, `codex-kiro`) with
   all three personas bound in each, `overrides` `{}`, `checkpoint_policy`
   `{"max_orchestrator_turns_before_checkpoint": 8}`, `low_quota` `{}`.
2. **Resolver (`scripts/persona_config.py`)**: `load_persona_config`, `resolve_persona`, `low_quota_state`,
   `effective_turn_budget`, `build_dispatch_argv`, `classify_dispatch_failure`, `PersonaBinding`,
   `PersonaConfigError` per the HLD Module Contracts. Deep-merge kit → global
   (`$REAL_HOME/.d3nexus/personas.json`) → project (`.agents/config/personas.json`); select `active_preset`;
   apply `overrides`; apply CLI overrides; record the source layer of every field; substitute `{effort}`;
   validate.
3. **CLI (`scripts/dev_config.py`)**: `status`, `models` (list, `add`, `remove`), `preset`, `set`, `reset`,
   `low-quota on|off [--for HOURS]` with the `--low-quota` alias, `checkpoint --turns`, `quota-check`,
   `resolve [--format json|argv] [--mode read-only|write]`. Writes are validated first and applied atomically
   (temp file plus `os.replace`).
4. **Quota gate**: `quota-check` fetches through `run_external_review.py::_default_quota_fetcher`
   (`L234-L261`) and judges with `evaluate_provider_quota` (`L192-L231`), both loaded by path; exit `2` when
   any persona is insufficient; an empty payload yields `"warning": "quota_unknown"` and does not block.
5. **Skill (`skills/dev-config/SKILL.md`)**: frontmatter `name` + `description` only; maps
   `/d3nexus:dev-config <args>` to `python3 scripts/dev_config.py <args>` and describes the interactive
   `--models` flow (spec §5.3).
6. **Tests**: `tests/test_fpg_persona_config.py` (FPG-HP-01, FPG-HP-02, FPG-EC-01, FPG-EC-02, FPG-ST-01) and
   `tests/test_fpg_dispatch_and_quota.py` (FPG-HP-03, FPG-FR-01, FPG-FR-02), parametrised, with a temporary
   `REAL_HOME`, project, `PATH` and an injected quota fetcher.

## Files

Allowed files:
- `skills/dev-config/SKILL.md` (new)
- `scripts/personas.default.json` (new)
- `scripts/persona_config.py` (new)
- `scripts/dev_config.py` (new)
- `tests/test_fpg_persona_config.py` (new)
- `tests/test_fpg_dispatch_and_quota.py` (new)

Read-only context:
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — HLD Module Contracts, [SE-03]
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — spec §5, §8.3–§8.5
- `skills/dev-implementation/resources/scripts/run_external_review.py` — `evaluate_provider_quota` (L192-L231), `_default_quota_fetcher` (L234-L261), `cli_command` (L1049-L1123)
- `skills/check-tasks/resources/scripts/tasks_server.py` — `get_real_home` (L87-L95)
- `scripts/resume_context.py` — `detect_current_profile` (L465-L557)
- `.devtool/review_config.json` — `quota_thresholds`

## Design Rationale

One resolver with per-field source tracking lets `status`, the runner, the prompts and the dashboard
explain where every binding came from; reusing the review CLI builders and the `--auto-quota` judgement
keeps one implementation of per-CLI flags and one set of thresholds. Applicable skills:
`d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: all new; `run_external_review.py` is imported read-only: `cli_command` (L1049-L1123), `evaluate_provider_quota` (L192-L231), `_default_quota_fetcher` (L234-L261).
- **Downstream Callers**: Task 2 (`resume_context.py` prompts), Task 3 (`lifecycle_runner.py`), Task 5 (`check_tasks.py`).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: every validation branch, every CLI subcommand, every CLI × mode pair and every failure signature.

### BDD SCENARIOS

Covers: FPG-HP-01, FPG-HP-02, FPG-HP-03, FPG-EC-01, FPG-EC-02, FPG-ST-01, FPG-FR-01, FPG-FR-02


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

Scenario: [FPG-ST-01] [Tier A - Unit] Low-quota mode is per profile, expires, and halves the turn budget
Given a temporary REAL_HOME, profile "danhdue" and checkpoint_policy.max_orchestrator_turns_before_checkpoint 8
When "dev_config.py low-quota on --for 2" runs at 10:00 UTC
Then "low_quota_state(root, 'danhdue', now=11:59 UTC)" returns enabled true and the effective turn budget is 4
And "low_quota_state(root, 'danhdue', now=12:01 UTC)" returns None and the effective turn budget is 8
And "low_quota_state(root, 'other_profile', now=11:00 UTC)" returns None
When "dev_config.py low-quota off" runs at 11:00 UTC
Then "low_quota_state(root, 'danhdue', now=11:00 UTC)" returns None

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
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_persona_config.py::test_fpg_hp_01_layered_resolution_reports_sources` | exit 1; contains "failed" | — |
| V2 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_dispatch_and_quota.py::test_fpg_hp_03_dispatch_argv_per_cli_and_mode` | exit 1; contains "failed" | — |
| V3 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_01.xml tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py` | exit 0; results build/test-results/fpg_task_01.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- New contract: `PERSONAS = ("ai_architect_reviewer", "orchestrator", "programmer")`;
  `ALLOWED_CLIS = frozenset({"agy", "claude", "codex", "kiro"})`; `SCHEMA_VERSION = 1`.
- New contract: `PersonaBinding(persona, alias, cli, model_id, effort, fallback_alias, sources)` frozen
  dataclass; `sources` maps `"model"`, `"effort"`, `"fallback_model"` to `"kit" | "global" | "project" | "cli"`.
- New contract: catalogue entries `argon` `{"cli": "agy", "id": "gemini-4-argon-{effort}", "efforts": ["low",
  "medium", "high"]}`, `hydrogen` `{"cli": "agy", "id": "gemini-4-hydrogen-{effort}", "efforts": ["low",
  "medium", "high", "xhigh"]}`, `claude-opus` `{"cli": "claude", "id": "opus", "efforts": ["medium", "high",
  "xhigh"]}`, `claude-sonnet` `{"cli": "claude", "id": "sonnet", "efforts": ["medium", "high"]}`, `codex-gpt`
  `{"cli": "codex", "id": "gpt-6.1-sol", "efforts": ["medium", "high", "xhigh"]}`, `kiro-opus`
  `{"cli": "kiro", "id": "claude-opus-5.5", "efforts": ["high"]}`.
- New contract: `default` preset binds `ai_architect_reviewer` → `argon`/`high` (fallback `claude-opus`),
  `orchestrator` → `hydrogen`/`high` (fallback `claude-sonnet`), `programmer` → `hydrogen`/`xhigh` (fallback
  `claude-sonnet`); the other four presets follow the spec §5.2 table.
- `$REAL_HOME` resolution copies `tasks_server.py::get_real_home` (`L87-L95`): split at `/antigravity_homes/`,
  else `REAL_HOME` env, else `~`. Public functions accept `real_home` for tests.
- Legacy sources `.devtool/review_config.json["providers"]["programmer"|"assistant"]`, `AGY_PROGRAMMER_MODEL`,
  `AGY_PROGRAMMER_EFFORT`, `AGY_ASSISTANT_MODEL` are never read for resolution; `status` lists each one that is
  set under `warnings`.
- `low-quota` state lives only in the global layer under `low_quota.<profile>` = `{"enabled": true,
  "expires_at": "<ISO-8601 UTC>"}`; default duration 5 hours; the profile comes from
  `resume_context.detect_current_profile()` loaded by path; `effective_turn_budget` returns `max(1, N // 2)`
  while enabled and unexpired, else `N`.
- `--scope` defaults to `global` for `preset`, `set`, `reset`, `models add/remove` and `checkpoint`.
- `models remove ALIAS` exits 1 while any merged binding or fallback references `ALIAS`.
- Source: `run_external_review.py::cli_command(cli: str, model: str | None, thinking_level: str | None = None)
  -> list[str]` (`L1049-L1123`) is the `read-only` builder; it is called, never copied or modified.
- New contract: `write` argv — `agy`: `["agy", "--model", model_id, "--effort", effort, "--mode", "auto"]`
  (matches `lifecycle_runner.build_agy_command`); `claude`: `["claude", "-p", "--model", model_id,
  "--dangerously-skip-permissions"]`; `codex`: `["codex", "exec", "--sandbox", "workspace-write", "--model",
  model_id, "-c", f"model_reasoning_effort={effort}"]`; `kiro`: `["kiro-cli", "chat", "--no-interactive",
  "--trust-all-tools", "--model", model_id]`.
- New contract: `classify_dispatch_failure(exit_code, stdout, stderr)` returns `"model_unavailable"` when the
  exit code is `127`, or the combined output matches (case-insensitive) `429`, `resource_exhausted`,
  `resourceexhausted`, `quota`, `rate limit`, `401`, `403`, `unauthorized`, `not authenticated`,
  `command not found`; otherwise `"task_failure"`.
- New contract: `quota-check --json` prints `{"sufficient": bool, "personas": [{"persona", "cli", "alias",
  "sufficient", "quota_line", "warning"}]}`; exit `2` iff any `sufficient` is false; `quota_unknown` entries
  count as sufficient; `cmd_quota_check` accepts an injectable `fetcher: Callable[[str], dict[str, Any]]`.
- Exit codes: `0` success, `1` validation or usage error, `2` quota insufficient. Errors print one line naming
  the rejected value.
- Tests load `persona_config.py` and `dev_config.py` through `importlib.util.spec_from_file_location` inside
  fixtures, so RED rows fail as test failures (exit 1) rather than collection errors.

## Definition of Done

- FPG-HP-01, FPG-HP-02, FPG-HP-03, FPG-EC-01, FPG-EC-02, FPG-ST-01, FPG-FR-01 and FPG-FR-02 pass. (V3, V6)
- Ruff and mypy pass on the new modules. (V4, V5)
- `skills/dev-config/SKILL.md` frontmatter holds exactly `name` and `description`. (Gate 5)

## Dependencies & Blockers

None.

Downstream dependents (blocked by Task 1): `task_02`, `task_05`.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Delete `skills/dev-config/`, the three new `scripts/` files and the two test files.
