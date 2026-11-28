---
name: dev-config
description: Configures layered AI persona model bindings, presets, model catalogue aliases, turn budgets, pass limits, external review settings, profile-scoped low-quota mode, the pre-dispatch quota gate, the global agy profile pool, and pooled dispatch via dev_config.py. Use when inspecting or switching persona models, configuring pass limits or external review priority/providers/thresholds, toggling low-quota mode, managing agy profile pools, dispatching pooled tasks, or checking provider quota before lifecycle waves.
---

# dev-config

Manages four-persona bindings, independent pass limits, and external review settings across five precedence tiers (`scripts/personas.default.json` -> read-only `.devtool/review_config.json` legacy fallback -> `$REAL_HOME/.d3nexus/personas.json` -> `.agents/config/personas.json` -> CLI flags), plus the global `agy` profile pool (`$REAL_HOME/.d3nexus/agy_profiles.json` and `agy_profile_leases.json`) and isolated review runtime state (`.devtool/state/review_runtime.json`). See the human quick-guide at [dev-config-quick-guide.en.md](../../docs/dev-config-quick-guide.en.md).

## Invocation Mapping

Translate `/d3nexus:dev-config <args>` directly to:

```bash
python3 scripts/dev_config.py <args>
```

| Subcommand | Purpose |
|---|---|
| `status [--json]` | Print active preset, persona bindings with source layers, turn budget, pass limits (`review_limits` and `task_review_limits`), external review config (`review`), low-quota expiry, missing-CLI alerts, and legacy-setting warnings |
| `models [--persona P] [--json]` (alias `--models`) | List the merged model catalogue, allowed efforts, resolved IDs, `PATH` availability, and current persona users |
| `models add ALIAS --cli CLI --id ID [--efforts E1,E2\|none] [--quota-pool POOL] [--scope global\|project]` | Add or replace a catalogue alias without editing JSON (`cli` in `agy`, `claude`, `codex`, `kiro`; `--efforts` defaults to `none` for fixed-effort models; optional `quota_pool` in `argonWeekly`, `gemini5h`, `provider`) |
| `models remove ALIAS [--scope global\|project]` | Remove an alias from that layer (refused while any merged persona binding, fallback, or `review.providers.*` entry references it) |
| `preset NAME [--scope global\|project]` | Set `active_preset` (`default`, `gemini-saver`, `claude-hybrid`, `all-hydrogen`, `codex-kiro`, `all-claude`, `all-codex`); warns when project settings mask a global change |
| `--provider agy\|claude\|codex [--scope global\|project]` | One-command quick-setup that sets `active_preset` to the provider's mapped preset and prints the resulting bindings; warns per persona if an override or higher layer masks it |
| `set PERSONA MODEL [EFFORT] [--fallback MODEL] [--scope global\|project]` | Override `ai_architect_reviewer`, `orchestrator`, or `programmer` (positional form; `EFFORT` may be omitted for fixed-effort models with `efforts: ["none"]`) |
| `set PERSONA [--provider agy\|claude\|codex\|kiro] --model M [--effort E] [--fallback MODEL] [--scope global\|project]` | Flag form of `set`: `--model` is a catalogue alias or a model id, `--effort` may be omitted for fixed-effort models (`efforts: ["none"]`), and `--provider` checks that the model belongs to that CLI. Do not mix it with positional `MODEL EFFORT` |
| `reset [PERSONA] [--scope global\|project]` | Clear one or all persona overrides in the target layer |
| `low-quota on\|off [--for HOURS] [--profile NAME]` (alias `--low-quota`) | Toggle profile-scoped low-quota mode in the global layer (default 5 hours; halves the turn budget) |
| `checkpoint --turns N [--scope global\|project]` | Set `checkpoint_policy.max_orchestrator_turns_before_checkpoint` (default `8`) |
| `limits [--json]` | Display resolved pass limits (`max_task_review_passes`, `max_fix_passes`, `max_principal_review_passes`, `max_cross_model_review_passes`) and source layers |
| `limits [--task-review N] [--fix N] [--principal-review N] [--cross-model-review N] [--scope global\|project]` | Independently update one or more pass limits in the target layer (warns on `stderr` if project overrides mask a global write) |
| `limits reset [task\|fix\|principal\|cross-model\|all] [--scope global\|project]` | Clear one or all pass limit overrides in the target layer |
| `review status [--json]` (or `review`) | Show resolved external review `provider_priority`, provider model/effort/host bindings, `quota_thresholds`, runtime `last_used_provider`, and legacy warnings |
| `review priority PROVIDER_LIST [--scope global\|project]` | Set shared `review.provider_priority` across `/principal-review` and `/cross-model-review` (comma- or space-separated subset of `claude`, `codex`, `kiro`, `agy`) |
| `review set PROVIDER --model M [--effort E] [--host URL] [--scope global\|project]` | Configure an external review provider (`claude`, `codex`, `kiro`, `agy`, `ollama`); `--model` accepts a catalogue alias (validated & `{effort}`-expanded) or raw model ID; `--host` applies only to `ollama` |
| `review thresholds [--5h F] [--7d F] [--kiro-frac F] [--kiro-credits N] [--argon F] [--scope global\|project]` | Update `review.quota_thresholds` used by external review selection, `quota-check`, and `agy` pooled dispatch |
| `review reset [priority\|providers\|PROVIDER\|thresholds\|all] [--scope global\|project]` | Clear targeted external review overrides in the target layer and prune empty `review` objects |
| `quota-check [--personas P1,P2] [--json]` | Evaluate each persona's consumed quota pool against resolved `review.quota_thresholds` (both 5-hour and weekly Gemini windows for `agy`, and dry-run pool check when a pool is configured); exits `0` when sufficient or `quota_unknown`, `2` when insufficient |
| `resolve PERSONA [--format json\|argv] [--mode read-only\|write]` | Print the resolved binding JSON or headless dispatch argv |
| `profiles list [--json]` | Show configured `agy` pool profiles, live leases, exhaustion resets, and cached quota |
| `profiles add NAME [--priority N] [--max-concurrent N] [--allow-concurrent-ag-run]` | Add an existing non-symlink `$REAL_HOME/antigravity_homes/NAME` directory to the pool |
| `profiles set (NAME\|--all) [--priority N] [--max-concurrent N] [--allow-concurrent-ag-run\|--exclusive]` | Update priority, concurrency (`0` disables the profile without removing it), or cross-host `ag_run` sharing (`--shared` alias) without disturbing live leases |
| `profiles remove NAME` | Remove a profile from the pool (refused while any live lease exists; release first) |
| `profiles release NAME [--force]` | Release leases on a profile (requires `--force` when a live lease is held) |
| `profiles clear [NAME]` | Clear exhaustion timestamps and cached quota for one or all profiles without modifying leases |
| `profiles probe [NAME]` | Probe quota for one or all pool profiles and refresh the sanitized cache |
| `profiles discover [--json]` | List the Antigravity profiles you could add to the pool (read-only; fetches no quota and writes nothing) |
| `dispatch --persona P [--mode write\|read-only] --prompt-file F --cwd D --log L [--epic E] [--task T] [--slot N] [--role orchestrator\|runner] [--wait SECONDS]` | Dispatch a persona task through the `agy` profile pool (or directly for `claude`/`codex`/`kiro`) and print JSON `DispatchResult` |

Default `--scope` is `global` for `preset`, `--provider`, `set`, `reset`, `models add`, `models remove`, `checkpoint`, mutating `limits`, and mutating `review` subcommands. Exit codes are `0` (success / sufficient or unknown quota), `1` (validation, usage, `task_failure`, `model_unavailable`, or `preflight_failed`), and `2` (insufficient quota, `no_profile`, or `quota_midrun`).

## Interactive `--models` Flow

When the user invokes `/d3nexus:dev-config --models` (or `/d3nexus:dev-config --models --persona <persona>`) with no write subcommand:

1. Run `python3 scripts/dev_config.py models --json` (adding `--persona <persona>` if supplied) and present the catalogue table.
2. Ask the user one multiple-choice question per target persona (`ai_architect_reviewer`, `orchestrator`, `programmer`, or only `<persona>` when `--persona` is set) listing valid `model` + `effort` pairs with the current binding listed first.
3. Ask whether to apply changes to `global` (default) or `project` scope.
4. Run `python3 scripts/dev_config.py set <persona> <model> <effort> --scope <scope>` for each selected persona.
5. Finish by running `python3 scripts/dev_config.py status` and showing the updated table.

## Setting a Provider, Model, and Effort

Flag form of `set` names the provider, the model, and the effort in one command:

```bash
python3 scripts/dev_config.py set programmer --provider kiro --model claude-sonnet-5.5 --effort high
python3 scripts/dev_config.py set programmer --provider agy --model hydrogen --effort xhigh
python3 scripts/dev_config.py set orchestrator orchestrator-argon
python3 scripts/dev_config.py set orchestrator --provider agy --model gemini-pro-orchestrator-g1-pro
python3 scripts/dev_config.py set programmer codex-gpt xhigh        # positional form, unchanged
```

- `--model` is resolved as a catalogue alias first, then as the `id` of a catalogue entry (with `{effort}` replaced by `--effort`). `--provider` must match the model's CLI. `--effort` / `EFFORT` is required for selectable-effort models (`hydrogen`, `argon`, `neon`, etc.) and defaults to `none` (omitting `--effort` on headless CLI dispatch) only when the model defines `efforts` as `["none"]`; mixing flag options with positional `MODEL EFFORT` exits `1`.
- `--provider` on `set` is an option of `set`. The top-level `--provider` quick-setup below still cannot be combined with a subcommand.
- **Pool-driven `agy` routing**: `agy` account selection is controlled exclusively by pool `priority` and `max_concurrent` (`profiles set` or the Task Dashboard `🔑 Agy Profile Pool` panel), while legacy `overrides.<persona>.profile` entries in `personas.json` are ignored with a warning in `status`.
- **Kiro Sonnet**: the catalogue ships `kiro-sonnet` (`claude-sonnet-5.5`, effort `high`). When every `agy` profile is out of quota, the exhaustion report offers `/d3nexus:dev-config set programmer kiro-sonnet high` next to the Codex option.
- To find profiles to add, run `profiles discover`, then `profiles probe NAME` and `profiles add NAME`. Discover reuses the profile discovery of `d3nexus:check-quota`, marks the host profile, and never fetches quota or unlocks a keychain.

## Provider Quick-Setup (`--provider`)

| `--provider` | Preset | `ai_architect_reviewer` (Role 2.1) | `orchestrator` (Role 2.2) | `programmer` (Role 2.3) |
|---|---|---|---|---|
| `agy` | `default` | `argon` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `claude` | `all-claude` | `claude-opus` `high` | `claude-sonnet` `high` | `claude-sonnet` `high` |
| `codex` | `all-codex` | `codex-gpt` `high` | `codex-terra` `medium` | `codex-terra` `medium` |

`--provider` writes only `active_preset` at the selected `--scope` (default `global`) without modifying `overrides`, `models`, `checkpoint_policy`, or `low_quota`.

## Presets and Quota Pools

| Preset | `ai_architect_reviewer` (Role 2.1) | `orchestrator` (Role 2.2) | `programmer` (Role 2.3) |
|---|---|---|---|
| `default` | `argon` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `gemini-saver` | `argon` `medium` | `hydrogen` `medium` | `hydrogen` `high` |
| `claude-hybrid` | `claude-opus` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `all-hydrogen` | `hydrogen` `xhigh` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `codex-kiro` | `kiro-opus` `high` | `codex-gpt` `medium` | `codex-gpt` `xhigh` |
| `all-claude` | `claude-opus` `high` | `claude-sonnet` `high` | `claude-sonnet` `high` |
| `all-codex` | `codex-gpt` `high` | `codex-terra` `medium` | `codex-terra` `medium` |

- Built-in `agy` aliases added alongside `argon` and `hydrogen`: `neon` (`gemini-4-neon-{effort}`, selectable efforts `low`/`medium`/`high`/`xhigh`, pool `gemini5h`), `orchestrator-neon` (`gemini-pro-orchestrator-neon`, `efforts: ["none"]`, pool `gemini5h`), and `orchestrator-argon` (`gemini-pro-orchestrator-g1-pro`, `efforts: ["none"]`, pool `argonWeekly`).
- `agy` models with `argon` or `orchestrator` + `g1-pro` in the `id` template consume `argonWeekly`; other `agy` models consume `gemini5h`; `claude`, `codex`, and `kiro` consume `provider`.
- When quota data is unreadable (`quota_unknown`), `quota-check` exits `0` and surfaces the warning without blocking; use `d3nexus:check-quota` for full multi-profile inspection.

## Agy Profile Pool and Pooled Dispatch

- **Allow-list (`$REAL_HOME/.d3nexus/agy_profiles.json`)**: An explicit priority-ordered list of `agy` profiles (empty by default). An empty pool dispatches once on the host profile with no lease, leaving non-pool workflows unchanged.
- **Exclusive & Shared Leases (`$REAL_HOME/.d3nexus/agy_profile_leases.json`)**: By default, `ag_run` launches allow one exclusive lease per non-host profile and skip profiles with a resident IDE/CLI process, while `direct` launches on the host profile allow up to `max_concurrent` (default `2`) leases. Setting `allow_concurrent_ag_run: true` (per profile or top-level via `profiles set ... --allow-concurrent-ag-run`) applies `max_concurrent` across all host profiles and allows `ag_run cli` alongside a resident IDE. Stale leases expire by heartbeat age (`lease_ttl_seconds`, default `180`) or dead local owner PID.
- **Launch Safety**: Non-host profiles run via `zsh -ic 'ag_run "$0" cli "$@"'` only after preflight verifies `_ag_link_ok`, `_ag_rel_link`, and `ag_run` are defined; `HOME`, `AGY_PROFILE`, and `TMPDIR` are never exported in the calling process.
- **Quota Windows & Rotation**: Both Gemini 5-hour (`>= 5h_min_fraction`) and weekly (`> 7d_min_fraction`) windows are checked. On a pre-work quota error (`HEAD` and `git status --porcelain` unchanged, ignoring `.vscode/settings.json`), `dispatch` rotates to the next pool profile; mid-work quota errors return `quota_midrun` (exit `2`) without retrying.
- **Exhaustion Recovery**: When every profile is exhausted, `dispatch` returns `no_profile` (exit `2`) with an actionable report listing reset times, `/d3nexus:dev-config profiles clear`, and explicit `/d3nexus:dev-config set programmer ...` commands without ever switching models automatically.

## External Review Settings and Pass Limits

- **5-Tier Precedence (per key)**: `CLI flags > project (.agents/config/personas.json) > global ($REAL_HOME/.d3nexus/personas.json) > legacy (.devtool/review_config.json, read-only fallback) > kit defaults (scripts/personas.default.json)`.
- **Four Independent Pass Limits (`limits`)**: `max_task_review_passes` (default `2`, `>= 1`), `max_fix_passes` (default `1`, `>= 0` so `0` disables fix passes), `max_principal_review_passes` (default `3`, `>= 1`), and `max_cross_model_review_passes` (default `3`, `>= 1`).
- **Shared Priority & Provider Models (`review`)**: `review.provider_priority` (default `["claude", "codex", "kiro", "agy"]`) is shared by `/principal-review` and `/cross-model-review`. Each `review.providers.<cli>.model` resolves catalogue aliases (enforcing CLI ownership, expanding `{effort}`, and defaulting fixed-effort aliases such as `orchestrator-argon` to `effort: "none"`) or passes raw model IDs and Ollama tags through verbatim (`--host` applies only to `ollama`).
- **Runtime Isolation & Masking Warnings**: Writing to `--scope global` warns on `stderr` when `.agents/config/personas.json` masks the same limit or review key. Runtime `last_used_provider` state is written atomically to `.devtool/state/review_runtime.json`; `.devtool/review_config.json` is never auto-seeded or overwritten.
