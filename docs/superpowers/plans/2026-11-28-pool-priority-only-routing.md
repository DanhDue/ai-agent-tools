# Priority-Only Agy Pool Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove persona-level `preferred_profile` overrides (`_preferred_first` and `dev-config set --profile`) and clean `$REAL_HOME/.d3nexus/personas.json` so 100% of pooled Antigravity (`agy`) dispatches obey Task Dashboard `priority` and `max_concurrent` settings.

**Architecture:** Delete `_preferred_first()` and the `preferred_profile` argument from `scripts/agy_profile_pool.py`, `scripts/agy_dispatch.py`, and `scripts/dev_config.py` so `_candidate_quota_sort_key()` is the sole candidate ordering function. Retire `--profile` on `dev-config set` while keeping `scripts/persona_config.py` tolerant of legacy `overrides.<persona>.profile` keys on disk (resolving `PersonaBinding.profile` as `None` and surfacing a warning in `dev-config status`), synchronize docs and acceptance tests, and strip `"profile": "khangatuaon248"` from `$REAL_HOME/.d3nexus/personas.json`.

**Tech Stack:** Python 3.10+, `pytest`, `ruff`, `mypy`, `fcntl.flock` atomic JSON config mutation, Markdown documentation contract (`check_document.py`).

**Spec:** [2026-11-28-pool-priority-only-routing-design.md](../specs/2026-11-28-pool-priority-only-routing-design.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Implementation Tasks](#implementation-tasks)
  - [Task 1: Remove Preferred Profile Pre-Sort from Pool and Dispatch Callers](#task-1-remove-preferred-profile-pre-sort-from-pool-and-dispatch-callers)
  - [Task 2: Retire dev-config set Profile Flag and Add Legacy Override Warnings](#task-2-retire-dev-config-set-profile-flag-and-add-legacy-override-warnings)
  - [Task 3: Update Docs and Acceptance Suite and Clean Host Persona Overrides](#task-3-update-docs-and-acceptance-suite-and-clean-host-persona-overrides)

## Global Constraints

- Pool candidate ordering in `scripts/agy_profile_pool.py` MUST follow `(priority, wk_tier, win_tier, edf_ts, -eff_wk, -eff_5h, profile)` for `gemini5h` and `(priority, wk_tier, win_tier, edf_ts, -eff_aw, profile)` for `argonWeekly` with zero per-persona pre-sorting.
- Existing `personas.json` files on disk containing `"profile"` under `overrides.<persona>` MUST load without raising `PersonaConfigError`, resolve `PersonaBinding.profile` as `None`, omit `"profile"` from `PersonaBinding.sources`, and emit a legacy warning in `dev-config status`.
- Passing `--profile` to `dev-config set` MUST fail fast with exit code `1`, whereas `dev-config low-quota --profile <name>` and `resume_context.py --profile <name>` MUST remain unchanged.
- `docs/dev-config-quick-guide.en.md` and `docs/dev-config-quick-guide.vi.md` MUST maintain identical ordered fenced CLI command lists and identical heading counts (`tests/test_fpg_acceptance.py`).
- Commit messages MUST follow `[POOL_PRIORITY_ROUTING] <Imperative title>` with bullet subtasks and zero trailer lines; never run `git push`.
- Never disturb `$REAL_HOME/.d3nexus/agy_profile_leases.json` or modify sibling repositories (`D3Nexus`, `nexus`, `lyrics-sync`, `digital_wallet`).

---

## File Structure

- `scripts/agy_profile_pool.py`: Remove `_preferred_first()` and `preferred_profile` parameters from `_order_pool_candidates()`, `_attempt_acquire_once()`, and `acquire()`.
- `scripts/agy_dispatch.py`: Remove `preferred_profile=binding.profile` from `_pool.acquire(...)` inside `run_on_pool()`.
- `scripts/persona_config.py`: Ignore `overrides.<persona>.profile` during `resolve_persona()`, reject `"profile"` in `cli_overrides`, and report legacy `overrides.<persona>.profile` entries in `detect_legacy_warnings()`.
- `scripts/dev_config.py`: Remove `preferred_profile=binding.profile` in `_check_agy_pool_quota()`, remove `--profile` from `set` subparser and `cmd_set()` / `_resolve_set_request()`, delete `_checked_set_profile()`, pass `real_home=real_home` into `detect_legacy_warnings()` in `cmd_status()`, and drop `b.profile` formatting in `cmd_status()`.
- `skills/dev-config/SKILL.md`: Remove `--profile` from `set` documentation and document Task Dashboard / `profiles set` priority-only routing.
- `docs/dev-config-quick-guide.en.md` & `docs/dev-config-quick-guide.vi.md`: Remove `set ... --profile` commands and prose in lockstep across both language files.
- `tests/test_fpg_agy_profile_pool.py`, `tests/test_fpg_agy_dispatch.py`, `tests/test_fpg_persona_config.py`, `tests/test_fpg_set_provider_model_profile.py`, `tests/test_agy_effortless_models.py`, `tests/test_fpg_acceptance.py`: Update unit, integration, and acceptance suites to enforce priority-only routing and legacy `profile` ignore warnings.
- `$REAL_HOME/.d3nexus/personas.json`: Strip `"profile": "khangatuaon248"` from all three persona overrides under `fcntl.flock` protection.

## Implementation Tasks

### Task 1: Remove Preferred Profile Pre-Sort from Pool and Dispatch Callers

**Files:**
- Modify: `scripts/agy_profile_pool.py:1047-1124` and `scripts/agy_profile_pool.py:1257-1324`
- Modify: `scripts/agy_dispatch.py:710-725`
- Modify: `scripts/dev_config.py:1485-1505`
- Test: `tests/test_fpg_agy_profile_pool.py` and `tests/test_fpg_agy_dispatch.py`

**Interfaces:**
- Consumes: `_candidate_quota_sort_key()` in `scripts/agy_profile_pool.py`
- Produces: `agy_profile_pool.acquire(owner, *, real_home=None, host_profile=None, quota_pool="gemini5h", thresholds=None, fetcher=None, resident_probe=None, wait_seconds=0, poll_seconds=15, now=None, dry_run=False) -> Acquisition` (without `preferred_profile`)

- [ ] **Step 1: Write the failing unit and dispatch tests**

Replace `test_fpg_hp_15_quota_check_dry_run_names_preferred_profile` in `tests/test_fpg_agy_profile_pool.py` with priority-only assertions and signature checks, and add a dispatch priority-order check in `tests/test_fpg_agy_dispatch.py`:

```python
import inspect


def test_acquire_rejects_removed_preferred_profile_kwarg() -> None:
    """acquire() and _order_pool_candidates() no longer accept preferred_profile."""
    pool_mod = _pool_mod()
    assert not hasattr(pool_mod, "_preferred_first")
    assert "preferred_profile" not in inspect.signature(pool_mod.acquire).parameters
    assert (
        "preferred_profile"
        not in inspect.signature(pool_mod._order_pool_candidates).parameters
    )


@pytest.mark.parametrize(
    ("scenario", "expected_prefix", "expected_fetched"),
    [
        ("p1_usable", "profile=p1", ["p1"]),
        ("p1_exhausted_falls_back_to_p2", "profile=p2", ["p1", "p2"]),
        ("p1_leased_falls_back_to_p2", "profile=p2", ["p2"]),
    ],
)
def test_quota_check_dry_run_strictly_follows_pool_priority_ignoring_legacy_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    scenario: str,
    expected_prefix: str,
    expected_fetched: list[str],
) -> None:
    """Even when personas.json has a legacy profile='p3', quota-check probes p1 -> p2 -> p3 strictly by priority."""
    pool_mod = _pool_mod()
    dev_config_mod = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    monkeypatch.delenv("AGY_PROFILE", raising=False)
    monkeypatch.delenv("ANTIGRAVITY_PROFILE", raising=False)
    _make_profile_dirs(real_home, ("p1", "p2", "p3"))
    _write_json(
        project / ".agents" / "config" / "personas.json",
        {
            "overrides": {
                "programmer": {
                    "model": "hydrogen",
                    "effort": "xhigh",
                    "profile": "p3",
                }
            }
        },
    )
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1, "max_concurrent": 1},
                {"profile": "p2", "priority": 2, "max_concurrent": 1},
                {"profile": "p3", "priority": 3, "max_concurrent": 1},
            ],
        },
    )

    if scenario == "p1_leased_falls_back_to_p2":
        leased = pool_mod.acquire(
            {"repo": "other", "epic": "e0", "task": "t0", "role": "runner"},
            real_home=real_home,
            host_profile="px",
            fetcher=lambda _p: {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.90},
                "geminiWeekly": {"fraction": 0.80},
            },
            resident_probe=lambda _p: False,
        )
        assert leased.profile == "p1"

    fetched: list[str] = []

    def recording_fetcher(profile: str) -> dict[str, Any]:
        fetched.append(profile)
        if scenario == "p1_exhausted_falls_back_to_p2" and profile == "p1":
            return {
                "status": "ACTIVE",
                "gemini5h": {"fraction": 0.02, "resetTime": "2026-11-17T14:00:00Z"},
                "geminiWeekly": {"fraction": 0.80, "resetTime": "2026-11-22T00:00:00Z"},
            }
        return {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.90},
            "geminiWeekly": {"fraction": 0.80},
        }

    rc = dev_config_mod.cmd_quota_check(
        project,
        personas=("programmer",),
        json_output=True,
        fetcher=recording_fetcher,
        real_home=real_home,
        resident_probe=lambda _p: False,
    )
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["sufficient"] is True
    entry = out["personas"][0]
    assert entry["sufficient"] is True
    assert entry["quota_line"].startswith(expected_prefix)
    assert fetched == expected_fetched
```

In `tests/test_fpg_agy_dispatch.py`, add `test_run_on_pool_ignores_binding_profile_and_dispatches_p1_first`:

```python
def test_run_on_pool_ignores_binding_profile_and_dispatches_p1_first(
    tmp_path: Path,
) -> None:
    """run_on_pool() always acquires p1 (priority 1) ahead of p2 (priority 2), even if PersonaBinding.profile is set."""
    pc = _persona_mod()
    dispatch_mod = _dispatch_mod()
    real_home = tmp_path / "real_home"
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    for name in ("p1", "p2"):
        (real_home / "antigravity_homes" / name).mkdir(parents=True, exist_ok=True)
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1, "max_concurrent": 2},
                {"profile": "p2", "priority": 2, "max_concurrent": 6},
            ],
            "allow_concurrent_ag_run": True,
        },
    )
    prompt_file = tmp_path / "prompt.md"
    prompt_file.write_text("run task\n", encoding="utf-8")
    binding = pc.PersonaBinding(
        persona="programmer",
        alias="neon",
        cli="agy",
        model_id="gemini-4-neon-xhigh",
        effort="xhigh",
        quota_pool="gemini5h",
        fallback_alias="claude-sonnet",
        sources={"model": "global", "effort": "global"},
        profile="p2",
    )
    launched: list[str | None] = []

    def ok_launcher(
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        stdin_text: str,
        profile: str | None,
        via_ag_run: bool,
    ) -> tuple[int, str, str]:
        _ = (argv, cwd, env, stdin_text, via_ag_run)
        launched.append(profile)
        return (0, "ok\n", "")

    res = dispatch_mod.run_on_pool(
        binding,
        "write",
        prompt_file=prompt_file,
        cwd=repo,
        log=tmp_path / "dispatch.log",
        owner={"repo": "repo", "epic": "e1", "task": "t1", "slot": 1, "role": "orchestrator"},
        real_home=real_home,
        host_profile="p1",
        launcher=ok_launcher,
        fetcher=lambda _p: {
            "status": "ACTIVE",
            "gemini5h": {"fraction": 0.85},
            "geminiWeekly": {"fraction": 0.70},
        },
        resident_probe=lambda _p: False,
        preflight=lambda: 0,
    )
    assert res.status == "ok"
    assert res.profile_used == "p1"
    assert launched == ["p1"]
```

- [ ] **Step 2: Run tests to verify RED failure**

Run: `python3 -m pytest tests/test_fpg_agy_profile_pool.py -k "preferred_profile or strictly_follows_pool_priority" tests/test_fpg_agy_dispatch.py -k "ignores_binding_profile" -v`
Expected: FAIL because `_preferred_first` and `preferred_profile` still exist and route to `p3` / `p2`.

- [ ] **Step 3: Remove `_preferred_first` and `preferred_profile` from pool and callers**

In `scripts/agy_profile_pool.py`, update `_order_pool_candidates`, delete `_preferred_first`, and remove `preferred_profile` from `_attempt_acquire_once` and `acquire`:

```python
def _order_pool_candidates(
    pool: Sequence[dict[str, Any]],
    *,
    snap_profiles: Mapping[str, Any],
    quota_pool: str,
    thresholds: Mapping[str, float],
    now: datetime,
    weekly_soft_guard: float = DEFAULT_WEEKLY_SOFT_GUARD_FRACTION,
) -> list[dict[str, Any]]:
    """Order candidates strictly by priority, then 2-group EDF + weekly soft-guard."""
    return sorted(
        pool,
        key=lambda entry: _candidate_quota_sort_key(
            entry,
            snap_profiles=snap_profiles,
            quota_pool=quota_pool,
            thresholds=thresholds,
            now=now,
            weekly_soft_guard=weekly_soft_guard,
        ),
    )
```

Remove `preferred_profile: str | None = None` and `preferred_profile=preferred_profile` from `_attempt_acquire_once()` and `acquire()` in `scripts/agy_profile_pool.py` (updating `acquire()`'s docstring at lines 1272–1276 to document strict `(priority, wk_tier, win_tier, edf_ts, ...)` ordering instead of `preferred_profile` pre-sorting), remove `preferred_profile=binding.profile` from `scripts/agy_dispatch.py` (`run_on_pool`), and remove `preferred_profile=binding.profile` from `scripts/dev_config.py` (`_check_agy_pool_quota`).

- [ ] **Step 4: Run tests to verify GREEN pass**

Run: `python3 -m pytest tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py -q`
Expected: PASS across all pool and dispatch tests (including concurrency `0x` disabled draining, multi-slot `allow_concurrent_ag_run`, and weekly soft-guard edge cases).

- [ ] **Step 5: Commit Task 1**

```bash
git add scripts/agy_profile_pool.py scripts/agy_dispatch.py scripts/dev_config.py tests/test_fpg_agy_profile_pool.py tests/test_fpg_agy_dispatch.py
git commit -m "[POOL_PRIORITY_ROUTING] Remove preferred_profile override from pool acquisition" -m "- remove _preferred_first and preferred_profile from agy_profile_pool.py" -m "- drop preferred_profile forwarding in agy_dispatch.py and dev_config.py quota-check" -m "- verify strict priority and concurrency ordering in pool and dispatch suites"
```

### Task 2: Retire dev-config set Profile Flag and Add Legacy Override Warnings

**Files:**
- Modify: `scripts/persona_config.py:69-72`, `scripts/persona_config.py:833-904`, `scripts/persona_config.py:1408-1456`
- Modify: `scripts/dev_config.py:398-466`, `scripts/dev_config.py:828-980`, `scripts/dev_config.py:2069-2079`, `scripts/dev_config.py:2319-2332`
- Test: `tests/test_fpg_persona_config.py`, `tests/test_fpg_set_provider_model_profile.py`, `tests/test_agy_effortless_models.py`

**Interfaces:**
- Consumes: `agy_profile_pool.acquire()` (Task 1)
- Produces:
  - `persona_config.detect_legacy_warnings(project_root: Path, env: Mapping[str, str] | None = None, *, real_home: Path | str | None = None) -> list[str]`
  - `dev_config.cmd_set(project_root: Path, *, persona: str, model: str | None = None, effort: str | None = None, fallback: str | None = None, scope: str = "global", real_home: Path | None = None, provider: str | None = None, flag_model: str | None = None, flag_effort: str | None = None) -> int`

- [ ] **Step 1: Write failing tests for retired `--profile`, legacy JSON tolerance, and status warnings**

In `tests/test_fpg_persona_config.py`, add tests covering legacy `"profile"` tolerance across global/project layers (with both `agy` and non-`agy` models!), invalid `"profile"` type rejection vs string tolerance, `cli_overrides={"profile": "p1"}` rejection, and `detect_legacy_warnings`:

```python
def test_legacy_override_profile_is_ignored_and_warns_in_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Legacy overrides.<persona>.profile keys on disk load cleanly, resolve profile=None, and emit status warnings."""
    pc = _persona_mod()
    dc = _dev_config_mod()
    real_home = tmp_path / "real_home"
    project = tmp_path / "project"
    real_home.mkdir()
    project.mkdir()
    monkeypatch.setenv("HOME", str(real_home))
    monkeypatch.setenv("REAL_HOME", str(real_home))
    _write_json(
        real_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "overrides": {
                "orchestrator": {
                    "model": "hydrogen",
                    "effort": "high",
                    "profile": "legacy_acc",
                },
                "programmer": {
                    "model": "codex-gpt",
                    "effort": "xhigh",
                    "profile": "legacy_acc",
                },
            },
        },
    )

    bindings = pc.resolve_all_personas(project, real_home=real_home)
    assert bindings["orchestrator"].profile is None
    assert "profile" not in bindings["orchestrator"].sources
    assert bindings["programmer"].cli == "codex"
    assert bindings["programmer"].profile is None
    assert "profile" not in bindings["programmer"].sources

    warnings = pc.detect_legacy_warnings(project, real_home=real_home)
    assert any(
        "global personas.json overrides.orchestrator.profile" in w for w in warnings
    )
    assert any(
        "global personas.json overrides.programmer.profile" in w for w in warnings
    )

    rc = dc.cmd_status(project, json_output=True, real_home=real_home)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["personas"]["orchestrator"]["profile"] is None
    assert any("overrides.orchestrator.profile" in w for w in payload["warnings"])
```

Update `tests/test_fpg_set_provider_model_profile.py` and `tests/test_agy_effortless_models.py`:
- Remove `--profile` from positive `set` invocations in `test_fpg_hp_14_*` and `tests/test_agy_effortless_models.py` (`test_custom_effortless_alias_set_and_resolve`), asserting `resolved["profile"] is None`.
- Add test asserting `dev_config.py set programmer --provider agy --model hydrogen --effort xhigh --profile p1` and `dev_config.py set programmer hydrogen xhigh --profile p1` both exit `1` without modifying `personas.json` (updating the two `--profile` cases in `test_fpg_ec_08_invalid_set_combinations_change_nothing` at lines 605–634 to expect `["--profile"]` from `_DevConfigParser`'s `unrecognized arguments: --profile`), and that a subsequent `dev_config.py set programmer hydrogen xhigh` overwrites and prunes any pre-existing `"profile"` key in that layer.
- Replace `test_fpg_hp_15_preferred_profile_first_then_rotate`, `test_fpg_se15_inherited_profile_*`, `test_fpg_se15_profile_with_a_non_agy_model_*`, and `test_fpg_se15_set_codex_in_project_after_a_global_profile_exits_zero` with priority-only pool rotation (`calls == ["p1", "p2", "p3"]` even when `personas.json` has `"profile": "p3"`) and legacy multi-layer tolerance tests (`global` or `project` `"profile"` never blocks `codex`/`kiro`/`agy` resolution).

- [ ] **Step 2: Run tests to verify RED failure**

Run: `python3 -m pytest tests/test_fpg_persona_config.py tests/test_fpg_set_provider_model_profile.py tests/test_agy_effortless_models.py -q`
Expected: FAIL because `resolve_persona` still populates `binding.profile`, `set --profile` still exits `0`, and `detect_legacy_warnings` does not report legacy `overrides.<persona>.profile`.

- [ ] **Step 3: Implement legacy tolerance in `persona_config.py` and retire `--profile` in `dev_config.py`**

In `scripts/persona_config.py`:
1. Keep `_ALLOWED_OVERRIDE_FIELDS = frozenset({"model", "effort", "fallback_model", "profile"})` for disk JSON validation, and define `_ALLOWED_CLI_OVERRIDE_FIELDS = frozenset({"model", "effort", "fallback_model"})`.
2. In `_resolve_from_layers()`:
   - Only read `("model", "effort", "fallback_model")` from `ov` and `cli_overrides` (checking `set(cli_overrides) - _ALLOWED_CLI_OVERRIDE_FIELDS` so `cli_overrides={"profile": ...}` raises `PersonaConfigError`).
   - Return `PersonaBinding(..., profile=None)` without setting `"profile"` in `sources`.
3. In `detect_legacy_warnings(project_root: Path, env: Mapping[str, str] | None = None, *, real_home: Path | str | None = None) -> list[str]`:
   - Inspect `("global", global_config_path(real_home))` and `("project", project_config_path(project_root))`:

```python
    for layer_label, cfg_path in (
        ("global", global_config_path(real_home)),
        ("project", project_config_path(project_root)),
    ):
        if not cfg_path.is_file():
            continue
        try:
            layer_doc = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(layer_doc, Mapping):
            continue
        ov_map = layer_doc.get("overrides")
        if not isinstance(ov_map, Mapping):
            continue
        for persona_key in PERSONAS:
            ov_entry = ov_map.get(persona_key)
            if isinstance(ov_entry, Mapping) and "profile" in ov_entry:
                warnings.append(
                    f"Legacy setting '{layer_label} personas.json overrides.{persona_key}.profile' "
                    "is ignored; configure pool priority and concurrency on Task Dashboard "
                    "or via 'dev-config profiles set'."
                )
```

In `scripts/dev_config.py`:
1. In both `cmd_status()` (line 400) and `cmd_review_status()` (line 1191), call `warnings = _pc.detect_legacy_warnings(project_root, real_home=real_home)`, and remove `if b.profile is not None: src_str += ...` from `cmd_status()`.
2. Delete `_checked_set_profile()`.
3. Simplify `_resolve_set_request()` to return `tuple[str, str]` (`(alias, effort)`), removing `profile` parameter and logic.
4. Simplify `cmd_set()` by removing `profile: str | None = None` and writing only `{"model": alias, "effort": resolved_effort}` (plus optional `"fallback_model"`).
5. Remove `p_set.add_argument("--profile", dest="set_profile", default=None)` and `profile=args.set_profile` in `_dispatch_args()`.

- [ ] **Step 4: Run unit, integration, and static quality checks**

Run: `python3 -m pytest tests/test_fpg_persona_config.py tests/test_fpg_set_provider_model_profile.py tests/test_agy_effortless_models.py tests/test_urc_dev_config_cli.py -q && ruff check tests`
Expected: PASS with 0 errors.

- [ ] **Step 5: Commit Task 2**

```bash
git add scripts/persona_config.py scripts/dev_config.py tests/test_fpg_persona_config.py tests/test_fpg_set_provider_model_profile.py tests/test_agy_effortless_models.py
git commit -m "[POOL_PRIORITY_ROUTING] Retire dev-config set --profile and ignore legacy profile keys" -m "- ignore legacy overrides.<persona>.profile in persona_config.py and emit status warnings" -m "- remove --profile flag from dev-config set while keeping low-quota --profile intact" -m "- update persona config, set flag, and effortless model test suites"
```

### Task 3: Update Docs and Acceptance Suite and Clean Host Persona Overrides

**Files:**
- Modify: `skills/dev-config/SKILL.md`
- Modify: `docs/dev-config-quick-guide.en.md` and `docs/dev-config-quick-guide.vi.md`
- Modify: `tests/test_fpg_acceptance.py:750-900`
- Clean host runtime file (untracked outside repo): `$REAL_HOME/.d3nexus/personas.json`

**Interfaces:**
- Consumes: Updated `dev_config._build_parser()` and `persona_config.detect_legacy_warnings()` from Task 2
- Produces: Synchronized `SKILL.md` + bilingual quick guides passing `check_document.py` and `scripts/verify.sh`, plus clean `$REAL_HOME/.d3nexus/personas.json`

- [ ] **Step 1: Update `tests/test_fpg_acceptance.py` to forbid `set ... --profile` in quick guides**

In `tests/test_fpg_acceptance.py`:
- In `test_dev_config_guide_profile_actions_follow_add()`, change `("probe", "remove", "release", "set_profile")` to `("probe", "remove", "release")` and remove the `target_action == "set_profile"` branch in `_assert_guide_profile_order()`.
- In `_run_fpg_hp_16_cli_parse()`, assert that no extracted command uses `set` with `--profile` (note: `--profile` remains present in `low-quota on --for 3 --profile profile_a`):

```python
        for cmd_line in en_commands:
            tokens = _dev_config_argv(cmd_line)
            if tokens and tokens[0] == "set":
                assert "--profile" not in tokens, (
                    f"Retired --profile flag found in quick-guide set command: {cmd_line}"
                )
```

- [ ] **Step 2: Run acceptance test to verify RED failure**

Run: `python3 -m pytest tests/test_fpg_acceptance.py -k "quick_guide or profile_actions" -v`
Expected: FAIL because `docs/dev-config-quick-guide.en.md` (and `.vi.md`) still contain `/d3nexus:dev-config set programmer --provider agy --profile profile_a ...` which now fails `parser.parse_args()`.

- [ ] **Step 3: Synchronize `skills/dev-config/SKILL.md`, `docs/dev-config-quick-guide.en.md`, and `docs/dev-config-quick-guide.vi.md`**

1. In `skills/dev-config/SKILL.md`:
   - Update the `set` row in the Invocation Mapping table to remove `[--profile NAME|auto]`.
   - Rename `## Setting a Provider, Model, Effort and Preferred Profile` to `## Setting a Provider, Model, and Effort`, remove `--profile p2` from the example command, and replace the `--profile` bullets with a bullet stating that `agy` account selection is controlled exclusively by pool `priority` and `max_concurrent` (`profiles set` or the Task Dashboard `🔑 Agy Profile Pool` panel), while legacy `overrides.<persona>.profile` entries in `personas.json` are ignored with a warning in `status`.
2. In `docs/dev-config-quick-guide.en.md` AND `docs/dev-config-quick-guide.vi.md` (keeping exact 1-to-1 ordered fenced CLI commands, exact heading counts, and identical heading levels `heading_structure()` between `.en.md` and `.vi.md`, including renaming `### Shipped Presets, Effort Rules, and \`--profile\` Inheritance` to `### Shipped Presets and Effort Rules` in both variants):
   - Replace the Cheat Sheet `set programmer --provider agy --profile profile_a ...` row with `/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2` (updating priority and concurrency).
   - Remove the two `set programmer --provider agy ... --profile ...` lines from Section 4 (`Using Several agy Profiles`) and add `/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2`.
   - Replace the `Preferred --profile and lower-layer inheritance` / `Prefer-then-rotate` / troubleshooting `--profile` rows with priority-only Task Dashboard & `profiles set` routing notes (and ensure `.vi.md` includes any newly added sections/commands from `.en.md` so `en_commands == vi_commands` and `len(en_headings) == len(vi_headings)` pass cleanly).

- [ ] **Step 4: Clean `"profile": "khangatuaon248"` from host `$REAL_HOME/.d3nexus/personas.json` under lock**

Run an atomic locked cleanup via `persona_config.locked_update_layer`:

```bash
python3 - <<'PY'
import pathlib, sys
sys.path.insert(0, "scripts")
import persona_config as pc

def strip_profiles(layer: dict) -> None:
    overrides = layer.get("overrides")
    if isinstance(overrides, dict):
        for entry in overrides.values():
            if isinstance(entry, dict):
                entry.pop("profile", None)

pc.locked_update_layer(pathlib.Path.cwd(), "global", strip_profiles)
PY
python3 scripts/dev_config.py status
python3 scripts/dev_config.py quota-check
```

Expected: `dev_config.py status` shows `ai_architect_reviewer` (`gemini-4-carbon-medium`), `orchestrator` (`gemini-4-carbon-medium`), and `programmer` (`gemini-4-neon-xhigh`) with **no** `profile=khangatuaon248` and zero legacy `overrides.*.profile` warnings; `quota-check` selects `profile=tess` (`P1`) first!

- [ ] **Step 5: Run full canonical quality gates (`check_document.py`, `.agents/quality/python-quality.json`, and `scripts/verify.sh`)**

Run:
```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc --require-bilingual docs/dev-config-quick-guide.en.md docs/dev-config-quick-guide.vi.md && \
ruff format --check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && \
bash scripts/verify.sh --full
```
Expected: `PASS — safe to publish` with 0 findings and 100% test suites passing.

- [ ] **Step 6: Commit Task 3**

```bash
git add skills/dev-config/SKILL.md docs/dev-config-quick-guide.en.md docs/dev-config-quick-guide.vi.md tests/test_fpg_acceptance.py
git commit -m "[POOL_PRIORITY_ROUTING] Sync dev-config docs and acceptance suite for priority-only pool" -m "- remove retired set --profile flag from dev-config skill and bilingual quick guides" -m "- update test_fpg_acceptance.py to forbid set --profile and verify bilingual CLI parity"
```
