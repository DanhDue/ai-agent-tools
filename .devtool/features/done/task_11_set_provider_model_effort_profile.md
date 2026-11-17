---
id: "task_11_set_provider_model_effort_profile"
status: "done"
completedAt: "2026-11-17T11:28:49Z"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T11:28:49Z"
labels: ["config", "cli", "dispatch"]
order: "a11"
review_tier: "full"
---

# Task 11: dev-config set with Provider, Model, Effort and Preferred agy Profile; Kiro Sonnet

Epic: [four_persona_governance](../../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Let the Human name the provider (Claude, Codex, Kiro or agy), the model, the effort and, for agy, a preferred profile
in one `dev-config set` command, and offer Kiro `claude-sonnet-5.5` at `high` as a ready option when every agy
profile is out of quota ([SE-10](../../epic/four_persona_governance/four_persona_governance.en.md#spec-errata)).

1. **`set` flags (`scripts/dev_config.py`)**: `set PERSONA [MODEL EFFORT] [--provider P] [--model M] [--effort E]
   [--profile NAME|auto] [--fallback MODEL] [--scope S]`. The positional form `set PERSONA MODEL EFFORT` stays valid
   and unchanged. `--model` accepts a catalogue alias or the model id of a catalogue entry; `--provider` checks that
   the resolved entry belongs to that CLI; `--profile` names a profile of the agy pool.
2. **Preferred profile**: `PersonaBinding` gains `profile`, stored in the persona override. `acquire` takes it as
   `preferred_profile`: the preferred profile is tried first, then the pool rotates by priority when it is leased,
   exhausted, in use or out of quota. `run_on_pool` passes it on every attempt.
3. **Catalogue (`scripts/personas.default.json`)**: add `kiro-sonnet` (`claude-sonnet-5.5`, efforts `["high"]`) just
   before `kiro-opus`. The exhaustion report of Task 10 then suggests
   `/d3nexus:dev-config set programmer kiro-sonnet high` for Kiro, with no change to the report code.
4. **Skill (`skills/dev-config/SKILL.md`)**: documents the flag form of `set`, `--profile`, `profiles discover` and the Kiro Sonnet example;
   frontmatter stays `name` + `description` only.
4a. **Discover (`dev_config.py profiles discover`)**: a read-only list of the profiles you could add to the pool, taken from
   the same discovery the `check-quota` skill uses, so nothing is parsed twice ([SE-12](../../epic/four_persona_governance/four_persona_governance.en.md#spec-errata)).
5. **Tests**: `tests/test_fpg_set_provider_model_profile.py` (FPG-HP-14, FPG-HP-15, FPG-EC-08, FPG-FR-08; FPG-HP-17 goes in `tests/test_fpg_agy_profile_pool.py`), with a
   temporary `REAL_HOME`, project, `PATH` and pool; plus any existing assertion that enumerates the kit catalogue
   or `PersonaBinding` fields exactly.

## Files

Allowed files:
- `scripts/persona_config.py`
- `scripts/dev_config.py`
- `scripts/agy_profile_pool.py`
- `scripts/agy_dispatch.py`
- `scripts/personas.default.json`
- `skills/dev-config/SKILL.md`
- `tests/test_fpg_set_provider_model_profile.py` (new)
- `tests/test_fpg_persona_config.py`
- `tests/test_fpg_agy_profile_pool.py`
- `tests/test_fpg_agy_dispatch.py`

Read-only context:
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — HLD Module Contracts, [SE-10]
- `.devtool/epic/four_persona_governance/task_10_agy_profile_pool_and_leases.md` — the pool, lease and report contracts this task extends
- `.devtool/epic/four_persona_governance/task_09_provider_quick_setup.md` — the `--provider` shortcut that must keep working
- `.agents/rules/profile_isolation_rules.md` — profile isolation rules

## Design Rationale

The alias already carries the CLI and the model id, so the flags are a checked way to name an alias, not a second
source of truth. A preferred profile is a preference and not a pin, so a persona never stops while another pool
profile still has quota. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `scripts/persona_config.py`: `PersonaBinding`, `resolve_persona`, `validate_merged_config`
  - `scripts/dev_config.py`: `cmd_set`, `cmd_models`, `_build_parser`, `main`
  - `scripts/agy_profile_pool.py`: `acquire`
  - `scripts/agy_dispatch.py`: `run_on_pool`
  - `scripts/personas.default.json`: `models`
  - `skills/dev-config/SKILL.md`: the `set` section
  - `tests/test_fpg_persona_config.py`: `test_fpg_hp_02_dev_config_models_and_bindable_alias`, `test_fpg_hp_01_all_five_presets_resolve`
  - `tests/test_fpg_agy_profile_pool.py`: `test_fpg_hp_11_pool_selection_priority_and_skip_reasons`
  - `tests/test_fpg_agy_dispatch.py`: `test_fpg_fr_05_dispatch_rotates_only_before_work_starts`
- **Downstream Callers**: Task 3 (the runner dispatches through `run_on_pool` and so honours the preferred profile with
  no change), Task 5 (the persona panel may show `profile`), Task 8 (guides and suite registration).
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: every flag, every rejection branch, both orders of the pool and the new alias.

### BDD SCENARIOS

Covers: FPG-HP-14, FPG-HP-15, FPG-HP-17, FPG-EC-08, FPG-FR-08


```gherkin
Scenario: [FPG-HP-14] [Tier C - Integration] dev-config set accepts a provider, a model, an effort and a preferred agy profile
Given a temporary REAL_HOME and project with the kit default configuration, "antigravity_homes/p1" and "antigravity_homes/p2" as directories, a pool listing "p1" and "p2", and stub executables "agy", "claude", "codex" and "kiro-cli" on PATH
When "dev_config.py set programmer --provider kiro --model claude-sonnet-5.5 --effort high" runs
Then it exits 0 and "dev_config.py resolve programmer --format json" prints cli "kiro", alias "kiro-sonnet", model_id "claude-sonnet-5.5", effort "high" and profile null
When "dev_config.py set programmer --provider agy --profile p2 --model hydrogen --effort xhigh" runs
Then "dev_config.py resolve programmer --format json" prints cli "agy", model_id "gemini-4-hydrogen-xhigh", effort "xhigh" and profile "p2"
When "dev_config.py set programmer codex-gpt xhigh" runs
Then "dev_config.py resolve programmer --format json" prints cli "codex" and profile null
And "dev_config.py models --json" lists "kiro-sonnet" with cli "kiro", id "claude-sonnet-5.5" and efforts ["high"] before "kiro-opus"

Scenario: [FPG-HP-15] [Tier A - Unit] A preferred agy profile is tried first and the pool rotates when it is unusable
Given a pool of "p1", "p2" and "p3" with priorities 1 to 3 and sufficient quota for all of them, and "programmer" bound to agy with profile "p3"
When "acquire" runs with preferred_profile "p3"
Then it returns profile "p3"
When "p3" is leased by another orchestrator and "acquire" runs again with preferred_profile "p3"
Then it returns profile "p1" and the skipped map is {"p3": "leased"}
When "p3" instead has "exhausted_until" in the future and "acquire" runs with preferred_profile "p3"
Then it returns profile "p1" and the skipped map is {"p3": "exhausted"}
And "run_on_pool" for that binding attempts "p3" first and then "p1" and "p2" in priority order

Scenario: [FPG-HP-17] [Tier A - Unit] profiles discover lists the profiles that could be added and fetches no quota
Given an injected discoverer returning "profile_a", "profile_b", "profile_c" and "profile_d", a pool listing "profile_b", a host profile "profile_c", and an injected quota fetcher that records every call
When "dev_config.py profiles discover --json" runs
Then it exits 0 and lists "profile_a", "profile_c" and "profile_d" as candidates in that order, with "host" true for "profile_c", and "in_pool" lists "profile_b"
And the quota fetcher was never called
And "dev_config.py profiles discover" without "--json" prints one line per candidate followed by the hints "profiles probe <name>" and "profiles add <name>"
And the pool file and the lease file are unchanged

Scenario: [FPG-EC-08] [Tier A - Unit] Invalid provider, model, effort and profile combinations are rejected and change nothing
Given a project configuration file whose SHA-256 is recorded, a pool listing "p1", and the kit default catalogue
When these seven commands run with "--scope project": "set programmer --provider kiro --model hydrogen --effort high", "set programmer --provider kiro --effort high", "set programmer --provider kiro --model claude-sonnet-5.5 --effort xhigh", "set programmer --model no-such-model --effort high", "set programmer --provider codex --model codex-gpt --effort xhigh --profile p1", "set programmer --provider agy --model hydrogen --effort xhigh --profile nope" and "set programmer codex-gpt xhigh --model codex-gpt"
Then each exits 1 with a message naming the rejected value: "hydrogen" as not a kiro model, "--model", "xhigh", "no-such-model" with "models add", "profile" with "agy", "nope" with "profiles add", and "positional"
And the project configuration file SHA-256 is unchanged
And "dev_config.py --provider claude set programmer claude-sonnet high" still exits 1 because the all-personas shortcut cannot be combined with a subcommand

Scenario: [FPG-FR-08] [Tier A - Unit] The exhaustion report offers Kiro claude-sonnet-5.5 at high effort with the default catalogue
Given the kit default catalogue, "programmer" bound to "hydrogen" with effort "xhigh", a PATH holding "kiro-cli" and "codex" but not "kiro", and a pool whose profiles are all exhausted
When "exhaustion_report" runs
Then the report contains the line "- switch the programmer: /d3nexus:dev-config set programmer kiro-sonnet high" with no "not on PATH" note
And it contains "/d3nexus:dev-config set programmer codex-gpt xhigh"
And it does not suggest "kiro-opus"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_set_provider_model_profile.py::test_fpg_hp_14_set_with_provider_model_effort_and_profile` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_set_provider_model_profile.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py tests/test_fpg_provider_shortcut.py tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py scripts/agy_profile_pool.py scripts/agy_dispatch.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py scripts/agy_profile_pool.py scripts/agy_dispatch.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_11.xml tests/test_fpg_set_provider_model_profile.py` | exit 0; results build/test-results/fpg_task_11.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Making an existing Task 1, 9 or 10 assertion pass would need a changed expected value for an alias, preset,
  quota rule or report line those tasks already define, rather than a superset check or an added field.

## Decisions Already Made

**CLI**
- New contract: `dev_config.py set PERSONA [MODEL EFFORT] [--provider P] [--model M] [--effort E] [--profile NAME|auto]
  [--fallback MODEL] [--scope S]`. `P` is one of `agy`, `claude`, `codex`, `kiro`. The positional form is unchanged.
  Mixing a positional `MODEL` or `EFFORT` with `--model` or `--effort` exits `1` with a message containing
  `positional`. With flags, `--model` and `--effort` are both required; `--provider` alone, or `--effort` without
  `--model`, exits `1` with a message naming `--model`.
- New contract: `--model` is resolved first as a catalogue alias, otherwise as the entry whose `id`, with `{effort}`
  replaced by `--effort`, equals the value. With `--provider`, only entries whose `cli` equals it are considered. No
  match exits `1` naming the value and containing `models add`; several matches exit `1` naming them. A resolved
  entry whose `cli` differs from `--provider` exits `1` with `<value> is not a <provider> model`.
- New contract: `--effort` is validated against the entry's `efforts` exactly as before, exit `1` naming the effort.
- New contract: `--profile NAME` is accepted only when the resolved `cli` is `agy`, else exit `1` naming `profile` and
  `agy`. `NAME` matches `^[a-zA-Z0-9_-]+$` and appears in the pool of `agy_profiles.json`, else exit `1` naming
  `NAME` and `profiles add`; a persona can never name a profile outside the Human's allow-list. `--profile auto`
  removes the preference.
- New contract: `set` replaces the persona's whole override entry (`model`, `effort`, `fallback_model`, `profile`), so
  a `set` without `--profile` clears a stored preference. Exit codes, the exclusive lock and the atomic replace are
  those of Task 1; a rejected request leaves every configuration file unchanged.
- The subcommand option `--provider` of `set` MUST use its own argparse `dest`, so that it cannot collide with the
  top-level `--provider` shortcut of Task 9. That shortcut keeps exiting `1` when combined with a subcommand.

**Persona configuration**
- New contract: `PersonaBinding` gains `profile: str | None = None` as its last field, and `sources` gains the key
  `"profile"` (`"kit" | "global" | "project" | "cli"`) when a profile is set. `resolve_persona` reads
  `overrides.<persona>.profile`, and a CLI override mapping may carry `profile`. Validation: `profile` is a string
  matching the profile-name pattern and is allowed only when the bound alias has `cli == "agy"`, else
  `PersonaConfigError` naming `profile`. `profile` is never read from a preset or from the kit default.
- `status` and `resolve --format json` print `profile` (null when unset).
- New contract: the catalogue entry `kiro-sonnet` is `{"cli": "kiro", "id": "claude-sonnet-5.5", "efforts":
  ["high"]}` and is inserted immediately before `kiro-opus` in `scripts/personas.default.json`. No preset changes.
  The id and the effort were confirmed against the live Kiro CLI on 2026-11-17.

**Pool and dispatch**
- New contract: `acquire(..., preferred_profile: str | None = None)`. When it names a pool entry, that entry is
  tried first and the others follow in `(priority, profile)` order. It faces the same leased, exhausted,
  resident-process and quota checks, so an unusable preferred profile is skipped with its normal reason and the pool
  rotates. A name that is not in the pool is ignored.
- New contract: `run_on_pool` passes `binding.profile` as `preferred_profile` on every attempt, so attempts go to the
  preferred profile first and then to the rest in priority order.
- `exhaustion_report` is unchanged: its Kiro suggestion is the first catalogue alias of the Kiro CLI, now
  `kiro-sonnet`, and its PATH check already accepts `kiro-cli` or `kiro`.

**Discover**
- New contract: `dev_config.py profiles discover [--json]` lists the profiles you could add. Candidates come from
  `agy_quota.get_all_profiles()`, the function behind `check-quota` (the `antigravity_homes/` folders validated by
  `is_valid_antigravity_profile`, with a `~/.zshrc` fallback), loaded by path and injectable as `discoverer` for tests. This
  task never parses `~/.zshrc` itself. A candidate is a discovered profile that is not in the pool; the host profile stays
  a candidate and is marked `host: true`. Candidates are sorted by name.
- New contract: the command fetches no quota and unlocks no keychain, because that would use the logins of every profile on
  the machine, including other people's. It prints one line per candidate, then the hints `profiles probe <name>` and
  `profiles add <name>`. JSON: `{"candidates": [{"profile", "host"}], "in_pool": [names], "source":
  "agy_quota.get_all_profiles"}`. Exit `0`. The pool file and the lease file are never written.
- New contract: the test is `test_fpg_hp_17_profiles_discover_lists_candidates_not_in_the_pool` in
  `tests/test_fpg_agy_profile_pool.py`; it injects the discoverer and a recording fetcher and never reads the host.

**Tests**
- Test names in `tests/test_fpg_set_provider_model_profile.py`: `test_fpg_hp_14_set_with_provider_model_effort_and_profile`,
  `test_fpg_hp_15_preferred_profile_first_then_rotate`, `test_fpg_ec_08_invalid_set_combinations_change_nothing`
  and `test_fpg_fr_08_exhaustion_report_offers_kiro_sonnet`. Tests load the modules through
  `importlib.util.spec_from_file_location` inside fixtures so the RED row fails as a test failure (exit `1`).
- Every test in the new file runs with `HOME` and `REAL_HOME` pointing at a temporary directory and with
  `AGY_PROFILE` and `ANTIGRAVITY_PROFILE` removed (one autouse fixture), and never reads the host `~/.d3nexus`,
  `~/antigravity_homes`, `~/.zshrc` or `~/.gemini`, never runs `ag_run` or the real `zsh -ic`, and never calls a real
  model CLI.

## Definition of Done

- FPG-HP-14, FPG-HP-15, FPG-HP-17, FPG-EC-08 and FPG-FR-08 pass, and Tasks 1, 9 and 10 suites still pass. (V2, V5)
- Ruff and mypy pass on the changed modules. (V3, V4)
- `skills/dev-config/SKILL.md` frontmatter holds exactly `name` and `description`, and the skill documents the flag
  form of `set`, `--profile` and the Kiro Sonnet example. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 9](../../epic/four_persona_governance/task_09_provider_quick_setup.md) and [Task 10](../../epic/four_persona_governance/task_10_agy_profile_pool_and_leases.md).

Downstream dependents (blocked by Task 11): `task_08`.

## References & Rollback

- [Epic HLD](../../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit.
