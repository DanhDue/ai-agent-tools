---
id: "task_09_provider_quick_setup"
status: "todo"
priority: "high"
assignee: null
epic: "four_persona_governance"
dueDate: null
created: "2026-11-17T10:00:00Z"
modified: "2026-11-17T10:00:00Z"
labels: ["config", "cli"]
order: "a9"
review_tier: "full"
---

# Task 9: Provider Quick-Setup Shortcut (`dev-config --provider`)

Epic: [four_persona_governance](../epic/four_persona_governance/four_persona_governance.en.md)

## Requirement Analysis

Add the one-command provider shortcut Role 1.0 requested on 2026-11-17 ([SE-07](../epic/four_persona_governance/four_persona_governance.en.md#spec-errata)):
`/d3nexus:dev-config --provider <agy|claude|codex>` binds all three personas to that provider's models.

1. **Catalogue and presets (`scripts/personas.default.json`)**: add the catalogue alias `codex-terra`
   `{"cli": "codex", "id": "gpt-6.1-terra", "efforts": ["medium", "high", "xhigh"]}` and two presets that each
   bind all three personas:

   | Preset | `ai_architect_reviewer` | `orchestrator` | `programmer` |
   |--------|------------------------|----------------|--------------|
   | `all-claude` | `claude-opus` `high` | `claude-sonnet` `high` | `claude-sonnet` `high` |
   | `all-codex` | `codex-gpt` `high` | `codex-terra` `medium` | `codex-terra` `medium` |

   The `agy` provider reuses the existing `default` preset unchanged. The new presets carry no `fallback_model`.
2. **CLI (`scripts/dev_config.py`)**: `dev_config.py --provider PROVIDER [--scope global|project]` performs the
   `preset` write for the mapped preset, then prints the resulting bindings. It uses the same scope default,
   lock and atomic replace as `preset`, and writes only `active_preset`. It never edits `overrides`; when an
   override, or a higher-precedence layer's `active_preset`, keeps any persona off the new preset's binding, it
   prints one warning per such persona naming the layer, and still exits `0`. A value outside `agy|claude|codex`,
   or `--provider` combined with a subcommand, exits `1` with a message naming the rejected value and leaves every
   configuration file unchanged.
3. **Skill (`skills/dev-config/SKILL.md`)**: document `--provider` and the three-row mapping above; the
   frontmatter stays `name` + `description` only.
4. **Tests (`tests/test_fpg_provider_shortcut.py`)**: FPG-HP-10 and FPG-EC-06, parametrised over the providers,
   with a temporary `REAL_HOME`, project and `PATH`. Assertions in `tests/test_fpg_persona_config.py` that compare the
   kit catalogue aliases or preset names for exact equality become superset checks, so every alias and preset the
   existing scenarios list is still asserted.

## Files

Allowed files:
- `scripts/dev_config.py`
- `scripts/personas.default.json`
- `skills/dev-config/SKILL.md`
- `tests/test_fpg_provider_shortcut.py` (new)
- `tests/test_fpg_persona_config.py`

Read-only context:
- `.devtool/epic/four_persona_governance/four_persona_governance.en.md` — HLD Module Contracts, [SE-07]
- `.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md` — spec §5.2, §5.3
- `scripts/persona_config.py` — layer loading, resolution and the locked atomic layer update that `preset` uses
- `.devtool/epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md` — the contracts this task extends

## Design Rationale

The shortcut is a thin alias over `preset`: one write path, one validation path and one lock, so `status`,
`resolve` and the dashboard keep showing an ordinary `active_preset`. Naming the presets after the provider
keeps the mapping data-driven. Applicable skills: `d3nexus:test-driven-development`,
`d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**: `scripts/dev_config.py` argument parsing and the `preset` write path;
  `scripts/personas.default.json` `models` and `presets`; `skills/dev-config/SKILL.md`;
  `tests/test_fpg_persona_config.py`: `test_fpg_hp_02_dev_config_models_and_bindable_alias`,
  `test_fpg_hp_02_cli_subcommands_aliases_and_fallback_guard` (both in `Test_Integration`) and
  `test_fpg_hp_01_all_five_presets_resolve`, plus any other assertion in that file that compares the kit catalogue
  aliases or preset names for exact equality.
- **Downstream Callers**: Task 8 documents the shortcut and registers the new suite in `scripts/verify.sh`;
  Tasks 3 and 5 read the same presets through `resolve_persona` and are unaffected.
- **Cross-Platform Bridges**: None.
- **Target Test Coverage Threshold**: every provider, both `--scope` values, both rejection branches and the
  masked-persona warning.

### BDD SCENARIOS

Covers: FPG-HP-10, FPG-EC-06


```gherkin
Scenario: [FPG-HP-10] [Tier C - Integration] dev-config --provider binds all three personas to one provider's models
Given a temporary REAL_HOME and project with the kit default configuration and stub executables "agy", "claude" and "codex" on PATH
When "dev_config.py --provider claude" runs
Then it exits 0 and the global file holds "active_preset" "all-claude"
And "dev_config.py resolve ai_architect_reviewer --format json" prints cli "claude", model_id "opus" and effort "high"
And "dev_config.py resolve orchestrator --format json" and "dev_config.py resolve programmer --format json" print cli "claude", model_id "sonnet" and effort "high"
When "dev_config.py --provider codex" runs
Then "ai_architect_reviewer" resolves to cli "codex", model_id "gpt-6.1-sol" and effort "high"
And "orchestrator" and "programmer" resolve to cli "codex", model_id "gpt-6.1-terra" and effort "medium"
When "dev_config.py --provider agy" runs
Then "ai_architect_reviewer" resolves to model_id "gemini-4-argon-high", "orchestrator" to "gemini-4-hydrogen-high" and "programmer" to "gemini-4-hydrogen-xhigh", the same bindings as the "default" preset
When "dev_config.py --provider claude --scope project" runs
Then the project file holds "active_preset" "all-claude" and the global file still holds "active_preset" "default"

Scenario: [FPG-EC-06] [Tier A - Unit] Invalid --provider use is rejected and an override that masks the provider is reported
Given a global configuration file whose SHA-256 is recorded and a project file whose "overrides.programmer" is {"model": "hydrogen", "effort": "high"}
When "dev_config.py --provider gemini" and "dev_config.py --provider claude status" run
Then each exits 1 with a message naming the rejected value ("gemini" and "status")
And the global configuration file SHA-256 is unchanged
When "dev_config.py --provider claude" runs
Then it exits 0 and prints a warning that names "programmer" and the "project" layer
And "resolve_persona('programmer', root)" still returns model_id "gemini-4-hydrogen-high" with sources["effort"] == "project"
And "ai_architect_reviewer" resolves to model_id "opus"
```

```gherkin
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_provider_shortcut.py::test_fpg_hp_10_provider_shortcut_binds_all_personas` | exit 1; contains "failed" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_fpg_provider_shortcut.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py` | exit 0; contains "passed" | — |
| V3 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py` | exit 0 | — |
| V4 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py scripts/persona_config.py scripts/dev_config.py` | exit 0 | — |
| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/test-results/fpg_task_09.xml tests/test_fpg_provider_shortcut.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py` | exit 0; results build/test-results/fpg_task_09.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- Making an existing Task 1 assertion pass would require changing an expected value for an alias or preset
  that Task 1 already defines, rather than relaxing exact equality to a superset check.

## Decisions Already Made

- Source: the catalogue, the `default` preset and the `preset` subcommand come from Task 1 and stay as they
  are; the `agy` provider is the `default` preset (`argon` `high`, `hydrogen` `high`, `hydrogen` `xhigh`).
- New contract: catalogue entry `codex-terra` is `{"cli": "codex", "id": "gpt-6.1-terra", "efforts": ["medium",
  "high", "xhigh"]}`. Its id is derived from the `gpt-6.1-sol` naming and its efforts mirror `codex-gpt`; neither
  can be checked offline because no test calls a real CLI. [SE-07] records both as pending Role 1.0's
  confirmation against the live `codex` CLI.
- New contract: presets `all-claude` and `all-codex` bind the personas exactly as in Requirement 1, with no
  `fallback_model`. `dev_config.py` holds `PROVIDER_PRESETS = {"agy": "default", "claude": "all-claude",
  "codex": "all-codex"}`.
- New contract: `--provider` is a top-level option of `dev_config.py`, not a subcommand, so
  `/d3nexus:dev-config --provider claude` maps to `python3 scripts/dev_config.py --provider claude`. Do not use
  argparse `choices=` for it: argparse exits `2` on an invalid choice, and exit `2` means "quota insufficient" in
  this CLI. Validate the value by hand and exit `1`.
- Exit codes follow Task 1: `0` success, `1` validation or usage error. A rejected value is named in a one-line
  message, as for the other validation errors.
- `--scope` defaults to `global`. `--provider` writes only `active_preset` at that scope; it never touches
  `overrides`, `models`, `checkpoint_policy` or `low_quota`.
- Masked-persona warning: after the write, resolve all three personas. For each persona whose resolved alias or
  effort differs from the mapped preset's binding, print
  `warning: <persona> is still bound to <alias> <effort> by the <layer> layer; run "dev_config.py reset <persona> --scope <layer>"`
  with `<layer>` taken from the binding's `sources`. The exit code stays `0`.
- Output on success: first line `active_preset: <preset> (<scope>)`, then one line per persona in the order
  `ai_architect_reviewer`, `orchestrator`, `programmer`: `<persona>: <cli> <model_id> <effort>`.
- Test function names: `test_fpg_hp_10_provider_shortcut_binds_all_personas` and
  `test_fpg_ec_06_invalid_provider_use_and_masked_override_warning`. Tests load `persona_config.py` and
  `dev_config.py` through `importlib.util.spec_from_file_location` inside fixtures, as Task 1's do, so the RED row
  fails as a test failure (exit `1`) and not as a collection error.

## Definition of Done

- FPG-HP-10 and FPG-EC-06 pass, and Task 1's suites still pass. (V2, V5)
- Ruff and mypy pass on the changed modules. (V3, V4)
- `skills/dev-config/SKILL.md` frontmatter holds exactly `name` and `description`, and the skill documents
  `--provider` with the mapping. (Gate 5)

## Dependencies & Blockers

Blocked by [Task 1](../epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md).

Downstream dependents (blocked by Task 9): `task_08`.

## References & Rollback

- [Epic HLD](../epic/four_persona_governance/four_persona_governance.en.md)
- **Rollback**: Revert the task commit.
