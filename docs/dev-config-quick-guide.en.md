# dev-config Quick-Guide

> Vietnamese translation: [dev-config-quick-guide.vi.md](dev-config-quick-guide.vi.md).

## Table of Contents

- [Meta Data](#meta-data)
- [1. Ten-Second Cheat Sheet](#1-ten-second-cheat-sheet)
- [2. Where Settings Live and Which Layer Wins](#2-where-settings-live-and-which-layer-wins)
- [3. Choosing a Provider, Model, and Effort](#3-choosing-a-provider-model-and-effort)
- [4. Using Several agy Profiles](#4-using-several-agy-profiles)
- [5. When Quota Runs Out](#5-when-quota-runs-out)
- [6. Troubleshooting](#6-troubleshooting)
- [7. Command Reference and Exit Codes](#7-command-reference-and-exit-codes)

## Meta Data

- **Kind**: `document`
- **Audience**: Human Architect (Role 1.0)
- **Diátaxis mode**: `how-to`
- **Non-goals**: Internal Python implementation of `scripts/persona_config.py`, `scripts/agy_profile_pool.py`, `scripts/agy_dispatch.py`, or `scripts/dev_config.py`
- **Acceptance**: Within 30 seconds, the Human Architect selects and runs an exact `/d3nexus:dev-config` command to inspect persona bindings, change provider/model/effort, configure the `agy` profile pool, recover from quota exhaustion, or resolve a layer override without CLI usage errors
- **Source Spec**: [2026-11-17-four-persona-governance-design.en.md](../.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md)

## 1. Ten-Second Cheat Sheet

| Goal | Exact Command |
| :--- | :--- |
| Inspect active bindings, layers, turn budget, and warnings | `/d3nexus:dev-config status` |
| Bind all three personas to Claude (global) | `/d3nexus:dev-config --provider claude` |
| Bind all three personas to Codex (project) | `/d3nexus:dev-config --provider codex --scope project` |
| Switch Programmer to Kiro Sonnet (`claude-sonnet-5.5`, `high`) | `/d3nexus:dev-config set programmer kiro-sonnet high` |
| Switch Programmer to Codex in project scope | `/d3nexus:dev-config set programmer codex-gpt xhigh --scope project` |
| Discover unpooled Antigravity profiles on this host | `/d3nexus:dev-config profiles discover` |
| Add your profile to the global `agy` pool | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| Prefer `profile_a` for `agy` Programmer and rotate if busy/empty | `/d3nexus:dev-config set programmer --provider agy --profile profile_a --model hydrogen --effort xhigh` |
| Inspect pool leases, exhaustion timers, and cached quota | `/d3nexus:dev-config profiles list` |
| Enable profile-scoped low-quota mode (5h default, halves turns) | `/d3nexus:dev-config low-quota on` |
| Run the pre-wave quota gate for all personas | `/d3nexus:dev-config quota-check` |
| Inspect all four pass limits and source layers | `/d3nexus:dev-config limits` |
| Set independent Principal (2) and Cross-Model (4) round caps globally | `/d3nexus:dev-config limits --principal-review 2 --cross-model-review 4 --scope global` |
| Set project task-review cap (3) and disable fix passes (0) | `/d3nexus:dev-config limits --task-review 3 --fix 0 --scope project` |
| Inspect external review priority, provider models, and thresholds | `/d3nexus:dev-config review status` |
| Set shared external review priority globally | `/d3nexus:dev-config review priority codex,claude,kiro,agy --scope global` |
| Set an external review provider model (alias or raw ID) | `/d3nexus:dev-config review set agy --model argon --effort medium --scope global` |
| Tune quota thresholds for external review, `quota-check`, and `agy` dispatch | `/d3nexus:dev-config review thresholds --5h 0.25 --kiro-credits 25.0 --scope global` |

## 2. Where Settings Live and Which Layer Wins

`/d3nexus:dev-config` resolves bindings for the three AI personas (`ai_architect_reviewer` Role 2.1, `orchestrator` Role 2.2, and `programmer` Role 2.3), all four pass limits (`max_task_review_passes`, `max_fix_passes`, `max_principal_review_passes`, `max_cross_model_review_passes`), and external review settings (`review.provider_priority`, `review.providers`, `review.quota_thresholds`) across five precedence tiers, merged per key so higher tiers win:

| Layer | Path | Scope Flag | Purpose |
| :--- | :--- | :--- | :--- |
| 1. Kit defaults | `scripts/personas.default.json` | — | Shipped model catalogue, seven presets, turn budget (`8`), default pass limits (`2`, `1`, `3`, `3`), and default review config |
| 2. Legacy fallback | `.devtool/review_config.json` | — | Read-only fallback for external review keys absent from global and project layers (never auto-seeded or overwritten) |
| 3. Global | `$REAL_HOME/.d3nexus/personas.json` | `--scope global` *(default)* | Per-user persona bindings, pass limits, and external review settings shared across repositories |
| 4. Project | `.agents/config/personas.json` | `--scope project` | Repository-specific overrides (including worktrees) |
| 5. Invocation | CLI flags (`--programmer-model`, `--provider-priority`, `--max-rounds`, etc.) | — | One-off autonomous run or review override |

Resolution order: deep-merge layers (`CLI > project > global > legacy > kit`) -> select effective `active_preset` -> apply merged `overrides.<persona>` and `review` / pass limits -> apply invocation CLI flags. External review runtime state (`last_used_provider`) is isolated in `.devtool/state/review_runtime.json` so `.devtool/review_config.json` stays untouched on disk. Legacy `.devtool/review_config.json["providers"]["programmer"|"assistant"]` keys, legacy review keys in `.devtool/review_config.json`, and `AGY_PROGRAMMER_MODEL`, `AGY_PROGRAMMER_EFFORT`, and `AGY_ASSISTANT_MODEL` environment variables surface non-blocking warnings in `status`.

Inspect the resolved table and source layer for every field with `status`:

```bash
/d3nexus:dev-config status
/d3nexus:dev-config status --json
```

## 3. Choosing a Provider, Model, and Effort

### Positional `set`, Flag `set`, and `--provider` Shortcut

Use `set` to override one persona (`ai_architect_reviewer`, `orchestrator`, or `programmer`) or `--provider` to switch all three personas to a provider preset at once:

```bash
/d3nexus:dev-config --provider agy
/d3nexus:dev-config --provider claude
/d3nexus:dev-config --provider codex --scope project
/d3nexus:dev-config preset gemini-saver --scope global
/d3nexus:dev-config set programmer kiro-sonnet high
/d3nexus:dev-config set programmer codex-gpt xhigh --scope project
/d3nexus:dev-config set programmer --provider kiro --model claude-sonnet-5.5 --effort high
/d3nexus:dev-config set programmer hydrogen xhigh --fallback claude-sonnet --scope global
/d3nexus:dev-config reset programmer --scope project
/d3nexus:dev-config reset --scope global
/d3nexus:dev-config preset default --scope project
```

- **Positional vs. flag form**: `set PERSONA MODEL EFFORT` accepts a catalogue alias (`kiro-sonnet`, `codex-gpt`, `hydrogen`). The flag form accepts `--provider` (`agy`, `claude`, `codex`, `kiro`), `--model` (a catalogue alias or a catalogue entry's `id`, such as `claude-sonnet-5.5`), `--effort`, and `--profile`. Both `--model` and `--effort` are required in flag form, and mixing positional arguments with `--model` or `--effort` exits `1`.
- **`--provider` shortcut**: Top-level `--provider agy|claude|codex` writes `active_preset` (`default`, `all-claude`, or `all-codex`) without clearing existing `overrides`, and warns on `stderr` if an override or project layer masks a persona. `kiro` is not a top-level `--provider` shortcut; use `set` or `preset codex-kiro`.
- **Returning a project preset to `default`**: `reset` clears only `overrides` and leaves `active_preset` active for the other personas, so after `--provider codex --scope project` and `reset programmer --scope project`, run `/d3nexus:dev-config preset default --scope project` to return the project layer's preset to `default`.
- **Interactive picker**: In chat, `/d3nexus:dev-config --models` (or `--models --persona programmer`) presents the catalogue table and walks through picking a model and effort per persona.

### Shipped Presets, Effort Rules, and `--profile` Inheritance

| Preset | `ai_architect_reviewer` (2.1) | `orchestrator` (2.2) | `programmer` (2.3) |
| :--- | :--- | :--- | :--- |
| `default` (`--provider agy`) | `argon` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `gemini-saver` | `argon` `medium` | `hydrogen` `medium` | `hydrogen` `high` |
| `claude-hybrid` | `claude-opus` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `all-hydrogen` | `hydrogen` `xhigh` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `codex-kiro` | `kiro-opus` `high` | `codex-gpt` `medium` | `codex-gpt` `xhigh` |
| `all-claude` (`--provider claude`) | `claude-opus` `high` | `claude-sonnet` `high` | `claude-sonnet` `high` |
| `all-codex` (`--provider codex`) | `codex-gpt` `high` | `codex-terra` `medium` | `codex-terra` `medium` |

- **Effort validation & `{effort}` expansion**: Each catalogue alias declares its allowed `efforts` (`argon`: `low|medium|high`; `hydrogen`: `low|medium|high|xhigh`; `claude-opus`/`codex-gpt`/`codex-terra`: `medium|high|xhigh`; `claude-sonnet`: `medium|high`; `kiro-sonnet`/`kiro-opus`: `high`). For `agy` models, `{effort}` in the template `id` expands to the bound effort (for example `gemini-4-hydrogen-xhigh`).
- **Managing catalogue aliases**: Inspect or extend the catalogue at runtime without editing JSON:

```bash
/d3nexus:dev-config models
/d3nexus:dev-config models --persona programmer --json
/d3nexus:dev-config models add custom-sonnet --cli claude --id sonnet-custom --efforts medium,high --quota-pool provider --scope global
/d3nexus:dev-config models remove custom-sonnet --scope global
```

- **Preferred `--profile` and lower-layer inheritance**: `--profile` works only with `agy` models and must name a profile already added to the pool (`--profile auto` clears the preference). Every `set` replaces that persona's override object in the target layer. When a lower layer (for example `global`) sets an `agy` override with `--profile` and a higher layer (for example `project` or CLI) binds a non-`agy` model (`set programmer codex-gpt xhigh --scope project`), the inherited lower-layer `profile` is automatically ignored and dropped from the resolved binding and `sources`. A `profile` in the **same** layer as a non-`agy` model, or passing `--profile` together with a non-`agy` model in one command, still fails with exit `1`.

## 4. Using Several agy Profiles

Configure an explicit priority-ordered pool in `$REAL_HOME/.d3nexus/agy_profiles.json` so concurrent orchestrators share Antigravity accounts safely through `$REAL_HOME/.d3nexus/agy_profile_leases.json`:

```bash
/d3nexus:dev-config profiles discover
/d3nexus:dev-config profiles discover --json
/d3nexus:dev-config profiles probe profile_a
/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1
/d3nexus:dev-config profiles add profile_b --priority 2 --max-concurrent 1
/d3nexus:dev-config set programmer --provider agy --profile profile_a --model hydrogen --effort xhigh
/d3nexus:dev-config set programmer --provider agy --model hydrogen --effort xhigh --profile auto
/d3nexus:dev-config profiles list
/d3nexus:dev-config profiles list --json
/d3nexus:dev-config profiles probe
/d3nexus:dev-config profiles release profile_a --force
/d3nexus:dev-config profiles remove profile_b
/d3nexus:dev-config profiles clear profile_a
/d3nexus:dev-config profiles clear
```

- **Discover, probe before adding, and add only profiles you own**: `profiles discover` lists existing non-symlink Antigravity candidates from `check-quota` (`agy_quota.get_all_profiles()`) not yet in the pool without fetching quota or unlocking keychains, and prints next-step hints (`profiles probe <name>` then `profiles add <name>`). `profiles probe NAME` works **before** a profile is added: it fetches the quota of **only** that one profile, prints the 5-hour and weekly windows with their verdict against `quota_thresholds`, checks whether a resident process holds it, suggests `/d3nexus:dev-config profiles add NAME` when usable, and writes nothing to `agy_profiles.json` or `agy_profile_leases.json`. `probe` uses the login of only the profile you name, never of the others. For a usable non-pool profile, it prints:

```text
Probed 'profile_a' (not in the pool): status=ACTIVE
  Quota: 5H=85.0% (>= 15.0%), 7D=65.0% (> 2.0%) -> pass
  Resident process: no
  Verdict: usable
  Next step: /d3nexus:dev-config profiles add profile_a
```

  If a window fails, it prints `-> fail (5h ... vs 15.0%)` or `-> fail (weekly ... vs 2.0%)` and `Verdict: not usable (5h below floor)` / `Verdict: not usable (weekly below floor)`. A profile with a resident process (an open IDE or CLI of that profile) reports `Resident process: yes (held by a running process)` and `Verdict: not usable (held by resident process)` *(or `yes (host profile)` for the active host profile)* — it is not launched on by non-host dispatch and must be closed first. Add **only profiles you own** (`profile_a`, `profile_b`), and keep every command that requires pool state (`set --profile`, `release`, `remove`, `clear`, `dispatch`) after `profiles add`. Calling `profiles probe` on a pool profile or without a name refreshes the cached quota in `agy_profile_leases.json` and prints `Probed '<name>': status=<status>`.
- **Prefer-then-rotate**: Setting `--profile profile_a` on an `agy` persona tells `dispatch` to try `profile_a` first and rotate across remaining pool profiles in `--priority` order if `profile_a` is leased, busy, or exhausted.
- **Leases and isolation**: Non-host profiles allow one `ag_run` lease at a time (`zsh -ic 'ag_run ...'`, verified by preflight); the profile hosting the active session allows up to `--max-concurrent` (default `2`) direct leases. Stale leases expire automatically when their heartbeat passes `lease_ttl_seconds` (`180s`) or their local PID exits.
- **5-hour and weekly quota windows**: For `gemini5h` models (`hydrogen`), `acquire` and `quota-check` require **both** `5h >= 15%` (`5h_min_fraction = 0.15`) **and** `weekly > 2%` (`7d_min_fraction = 0.02`). For `argonWeekly` models (`argon`), they check `argonWeekly >= 10%` (`agy_argon_min_fraction = 0.10`). A profile failing either window during `acquire` (dispatch) is marked exhausted until its reset time (and fails `quota-check` with exit `2`).

## 5. When Quota Runs Out

Use profile-scoped low-quota mode (`low-quota`, alias `--low-quota`) when you spot a profile approaching its 5-hour limit, and rely on `quota-check` before waves and fix rounds:

```bash
/d3nexus:dev-config low-quota on
/d3nexus:dev-config low-quota on --for 3 --profile profile_a
/d3nexus:dev-config low-quota off --profile profile_a
/d3nexus:dev-config checkpoint --turns 6 --scope global
/d3nexus:dev-config quota-check
/d3nexus:dev-config quota-check --personas orchestrator,programmer --json
```

- **Low-quota mode**: Stored per profile under `low_quota` in the global layer with a 5-hour default expiry (`--for HOURS`). It halves `max_orchestrator_turns_before_checkpoint` (default `8` -> `4`), trims non-essential narrative prose, completes the wave already in flight, writes `--checkpoint low_quota_stop`, prints the resume prompt, records a pending decision, and stops cleanly.
- **`quota-check` & `review thresholds`**: `quota-check` evaluates each target persona's consumed pool (`argonWeekly`, `gemini5h` + `geminiWeekly`, or provider quota for `claude`/`codex`/`kiro`) against resolved `review.quota_thresholds` (customizable via `/d3nexus:dev-config review thresholds --5h 0.25 --7d 0.05 --kiro-frac 0.03 --kiro-credits 25.0 --argon 0.10 --scope global`). Exits `0` when sufficient or when quota cannot be read (`quota_unknown` warning, non-blocking); exits `2` when insufficient.
- **Stop report & no automatic model switching**: When every `agy` profile is exhausted (`no_profile`, exit `2`) or `quota-check` fails, the Orchestrator/runner checkpoints `quota_low`, records a `quota` pending decision visible in `/d3nexus:check-tasks`, prints each profile's failing window and earliest reset, and offers exact recovery commands (`/d3nexus:dev-config profiles clear`, `/d3nexus:dev-config set programmer codex-gpt xhigh`, `/d3nexus:dev-config set programmer kiro-sonnet high`). **The kit never switches models by itself** — Role 1.0 decides when to clear, wait, or switch.

## 6. Troubleshooting

| Symptom | Cause | Fix / Command |
| :--- | :--- | :--- |
| Ran `set programmer codex-gpt xhigh --scope project` after a global `--profile` | Higher-layer non-`agy` model inherits a lower-layer `profile`: the lower-layer `profile` is ignored automatically (SE-15); errors happen only if `--profile` is in the **same** layer or command as a non-`agy` model | `/d3nexus:dev-config set programmer codex-gpt xhigh --scope project` *(works directly; or clear global with `/d3nexus:dev-config reset programmer --scope global`)* |
| `Error: --profile applies only to agy models` | Passed `--profile` in the same command/layer as a `claude`, `codex`, or `kiro` model | `/d3nexus:dev-config set programmer kiro-sonnet high` |
| `warning: programmer is still bound to ... by the project layer` after `--provider` or `preset` | A higher-precedence override or `project` preset masks your global change | `/d3nexus:dev-config reset programmer --scope project` |
| `Error: Profile 'profile_a' is not in the agy pool` (or `is not in the pool`) | `--profile` or `profiles remove`/`release`/`clear` must reference a profile already registered in `$REAL_HOME/.d3nexus/agy_profiles.json` | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| `profiles probe profile_a` fails with `neither in the pool (...) nor in discovered profiles (...)` | `profile_a` is not in the pool and is not a profile folder that `check-quota` lists | `/d3nexus:dev-config profiles discover` |
| `profiles remove` refused because of live leases | Active or recently started orchestrator holds a lease in `agy_profile_leases.json` | `/d3nexus:dev-config profiles release profile_a --force` |
| `Stopped: all agy profiles are out of quota.` (`no_profile`, exit `2`) | Every pool profile failed the 5-hour or weekly threshold | Wait/top up then `/d3nexus:dev-config profiles clear`, or `/d3nexus:dev-config set programmer kiro-sonnet high` |
| `MODEL_UNAVAILABLE` halt or `(!)` next to CLI in `status` | Bound CLI binary is missing from `PATH` or unauthenticated | Install/authenticate CLI or switch with `/d3nexus:dev-config set programmer claude-sonnet high` |
| `Cannot remove model alias ... referenced by ...` | Active preset, override, fallback, or `review.providers.<cli>.model` still points to the alias | `/d3nexus:dev-config reset --scope global` or `/d3nexus:dev-config review reset <provider> --scope global`, then remove the alias |
| `Warning: project override in .agents/config/personas.json masks global ...` | Global `limits` or `review` write succeeded, but `.agents/config/personas.json` overrides the same key in this repo | `/d3nexus:dev-config limits reset <target> --scope project` or `/d3nexus:dev-config review reset <target> --scope project` |
| Legacy `.devtool/review_config.json` warning in `status` | Repository still holds a legacy `.devtool/review_config.json` (read-only fallback only; runtime `last_used_provider` now lives in `.devtool/state/review_runtime.json`) | Migrate keys with `/d3nexus:dev-config review` and `/d3nexus:dev-config limits` |
| `quota_unknown` warning on `quota-check` (exit `0`) | Quota fetcher returned no data or CLI does not expose a quota API | Non-blocking warning; verify live accounts with `/d3nexus:check-quota` |

## 7. Command Reference and Exit Codes

All subcommands also run directly via `python3 scripts/dev_config.py ...` (`dispatch` requires an existing `--prompt-file` and `--cwd` directory):

```bash
python3 scripts/dev_config.py status
python3 scripts/dev_config.py models
python3 scripts/dev_config.py profiles discover
python3 scripts/dev_config.py profiles probe profile_a
python3 scripts/dev_config.py profiles probe
python3 scripts/dev_config.py resolve programmer --format json --mode write
python3 scripts/dev_config.py resolve ai_architect_reviewer --format argv --mode read-only
python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file .devtool/prompt.md --cwd . --log .devtool/dispatch.log --epic demo --task task_01 --slot 1 --role orchestrator --wait 30
```

- **Pass limits (`dev-config limits`)**: Four independent caps are supported (`max_task_review_passes` default `2`, `max_fix_passes` default `1` with `0` allowed, `max_principal_review_passes` default `3`, `max_cross_model_review_passes` default `3`):
  - Inspect: `/d3nexus:dev-config limits` or `/d3nexus:dev-config limits --json`
  - Update: `/d3nexus:dev-config limits [--task-review N] [--fix N] [--principal-review N] [--cross-model-review N] [--scope global|project]`
  - Reset: `/d3nexus:dev-config limits reset [task|fix|principal|cross-model|all] [--scope global|project]`
- **External review (`dev-config review`)**: Shared `provider_priority` across `/principal-review` and `/cross-model-review`, alias-or-raw provider models (catalogue aliases validate CLI ownership, expand `{effort}`, and default fixed-effort aliases such as `orchestrator-argon` to `effort: "none"`; raw model IDs and Ollama tags pass through verbatim; `--host` applies only to `ollama`), shared `quota_thresholds`, and runtime `last_used_provider` isolated in `.devtool/state/review_runtime.json`:
  - Inspect: `/d3nexus:dev-config review status` or `/d3nexus:dev-config review status --json`
  - Priority: `/d3nexus:dev-config review priority codex,claude,kiro,agy [--scope global|project]`
  - Provider model: `/d3nexus:dev-config review set <claude|codex|kiro|agy|ollama> --model <alias-or-id> [--effort <level>] [--host <http(s)://url>] [--scope global|project]`
  - Thresholds: `/d3nexus:dev-config review thresholds [--5h F] [--7d F] [--kiro-frac F] [--kiro-credits N] [--argon F] [--scope global|project]`
  - Reset: `/d3nexus:dev-config review reset [priority|providers|claude|codex|kiro|agy|ollama|thresholds|all] [--scope global|project]`
- **`profiles probe [NAME]`**: When `NAME` is a non-pool profile returned by `profiles discover`, fetches only `NAME`'s quota, prints the 5H/7D threshold check, resident-process check, and `Verdict: usable` / `not usable (...)` without writing `agy_profiles.json` or `agy_profile_leases.json` (exits `0`); when `NAME` is in the pool or omitted, refreshes cached quota in `agy_profile_leases.json` and prints `Probed '<name>': status=<status>`; exits `1` when `NAME` is neither in the pool nor discoverable.

| Exit Code | Meaning |
| :--- | :--- |
| `0` | Success (including `profiles probe NAME` even when verdict is `not usable`); or `quota-check` is sufficient / `quota_unknown` |
| `1` | Validation error, CLI usage error, unknown `profiles probe` name, `task_failure`, `model_unavailable`, or `preflight_failed` |
| `2` | Quota gate insufficient (`quota-check`), `no_profile` (pool exhausted/busy), or `quota_midrun` |
