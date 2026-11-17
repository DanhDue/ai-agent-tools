---
name: dev-config
description: Configures layered AI persona model bindings, presets, model catalogue aliases, turn budgets, profile-scoped low-quota mode, and the pre-dispatch quota gate via dev_config.py. Use when inspecting or switching persona models, toggling low-quota mode, or checking provider quota before lifecycle waves.
---

# dev-config

Manages the four-persona model configuration across kit defaults (`scripts/personas.default.json`), global user settings (`$REAL_HOME/.d3nexus/personas.json`), project overrides (`.agents/config/personas.json`), and one-off CLI flags.

## Invocation Mapping

Translate `/d3nexus:dev-config <args>` directly to:

```bash
python3 scripts/dev_config.py <args>
```

| Subcommand | Purpose |
|---|---|
| `status [--json]` | Print active preset, persona bindings with source layers, turn budget, low-quota expiry, missing-CLI alerts, and legacy-setting warnings |
| `models [--persona P] [--json]` (alias `--models`) | List the merged model catalogue, allowed efforts, resolved IDs, `PATH` availability, and current persona users |
| `models add ALIAS --cli CLI --id ID --efforts E1,E2 [--quota-pool POOL] [--scope global\|project]` | Add or replace a catalogue alias without editing JSON (`cli` in `agy`, `claude`, `codex`, `kiro`; optional `quota_pool` in `argonWeekly`, `gemini5h`, `provider`) |
| `models remove ALIAS [--scope global\|project]` | Remove an alias from that layer (refused while any merged binding or fallback references it) |
| `preset NAME [--scope global\|project]` | Set `active_preset` (`default`, `gemini-saver`, `claude-hybrid`, `all-hydrogen`, `codex-kiro`); warns when project settings mask a global change |
| `set PERSONA MODEL EFFORT [--fallback MODEL] [--scope global\|project]` | Override `ai_architect_reviewer`, `orchestrator`, or `programmer` |
| `reset [PERSONA] [--scope global\|project]` | Clear one or all persona overrides in the target layer |
| `low-quota on\|off [--for HOURS] [--profile NAME]` (alias `--low-quota`) | Toggle profile-scoped low-quota mode in the global layer (default 5 hours; halves the turn budget) |
| `checkpoint --turns N [--scope global\|project]` | Set `checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default `8`) |
| `quota-check [--personas P1,P2] [--json]` | Evaluate each persona's consumed quota pool against `quota_thresholds`; exits `0` when sufficient or `quota_unknown`, `2` when insufficient |
| `resolve PERSONA [--format json\|argv] [--mode read-only\|write]` | Print the resolved binding JSON or headless dispatch argv |

Default `--scope` is `global` for `preset`, `set`, `reset`, `models add`, `models remove`, and `checkpoint`. Exit codes are `0` (success / sufficient or unknown quota), `1` (validation or usage error), and `2` (insufficient quota).

## Interactive `--models` Flow

When the user invokes `/d3nexus:dev-config --models` (or `/d3nexus:dev-config --models --persona <persona>`) with no write subcommand:

1. Run `python3 scripts/dev_config.py models --json` (adding `--persona <persona>` if supplied) and present the catalogue table.
2. Ask the user one multiple-choice question per target persona (`ai_architect_reviewer`, `orchestrator`, `programmer`, or only `<persona>` when `--persona` is set) listing valid `model` + `effort` pairs with the current binding listed first.
3. Ask whether to apply changes to `global` (default) or `project` scope.
4. Run `python3 scripts/dev_config.py set <persona> <model> <effort> --scope <scope>` for each selected persona.
5. Finish by running `python3 scripts/dev_config.py status` and showing the updated table.

## Presets and Quota Pools

| Preset | `ai_architect_reviewer` (Role 2.1) | `orchestrator` (Role 2.2) | `programmer` (Role 2.3) |
|---|---|---|---|
| `default` | `argon` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `gemini-saver` | `argon` `medium` | `hydrogen` `medium` | `hydrogen` `high` |
| `claude-hybrid` | `claude-opus` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `all-hydrogen` | `hydrogen` `xhigh` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `codex-kiro` | `kiro-opus` `high` | `codex-gpt` `medium` | `codex-gpt` `xhigh` |

- `agy` models with `argon` in the `id` template consume `argonWeekly`; other `agy` models consume `gemini5h`; `claude`, `codex`, and `kiro` consume `provider`.
- When quota data is unreadable (`quota_unknown`), `quota-check` exits `0` and surfaces the warning without blocking; use `d3nexus:check-quota` for full multi-profile inspection.
