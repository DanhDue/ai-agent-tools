# Principal Review: shift_left_quality_resolver

## Round 1

- **Date**: 2026-11-28T03:35:00Z
- **SHA**: 3faa8b2adc39a4771efdc9a378f6ad61ed119a72
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/shift_left_quality_resolver_principal_round1_3faa8b2.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_04_fail_closed_task_and_plan_contract_guards.md:Decisions Already Made / shift_left_quality_resolver.md:Module Contracts and CLI Interfaces §5 | Making `_cap_tool_prefix()` matching unconditional turns the pinned test `test_todo_task_still_rejected_when_omitting_newly_registered_targets` (skills/dev-implementation/resources/scripts/test_check_task_contract.py:1036-1056; expects exit 1 and "missing registered") into exit 0. That test file is outside Allowed files, but Task 04's V3 runs it. The spec also says it relies on `_check_python_tier_b_allowed_coverage()`, which does not run for single-file tasks (check_task_contract.py:1186-1191). As a result, a task can run `mypy unrelated.py` and pass. Proposed: when only the prefix path matches, require every positional target to be in Allowed files or among the manifest targets, without depending on the coverage check's conditions; add `skills/dev-implementation/resources/scripts/test_check_task_contract.py` to Allowed files and record a decision to rewrite that pinned test. | fixed in f4deb43 |
| 2 | Important | task_01_registry_prefix_wrappers_and_provider_schemas.md:Decisions Already Made / shift_left_quality_resolver.md:Module Contracts and CLI Interfaces §2 | Extending `_strip_command_wrappers()` cannot satisfy SLQR-EC-01 case 2 (`mise exec --` in the manifest, bare `swiftlint` in the task). `_subcommand_matches_prefix()` (_stack_lifecycle_registry.py:1066-1094) only unwraps the candidate, and the probe returns `(False, [])`. Rule 2 also treats `--directory` as a required flag and ignores its value, so any `uv --directory <other>` command matches. Proposed: in `_subcommand_matches_prefix`, unwrap the prefix tokens too and compare the unwrapped forms on both sides; strip value-taking wrapper flags (`--directory`, `--project`, `--prefix`) before Rule 2; add a negative EC-01 assertion that a different `--directory` value does not match. | fixed in f4deb43 |
| 3 | Important | task_01_registry_prefix_wrappers_and_provider_schemas.md:Files / shift_left_quality_resolver.md:Module Contracts and CLI Interfaces §1 | The HLD says `validate_{flutter,rust,web,python}_quality.py` are synced, but they are not in Allowed files. These validators have no capability allow-list; they only call the shared helpers (e.g. validate_python_quality.py:45,115). So SLQR-HP-01's "every capability key accepted by each runtime validator" has no defined set to test. Proposed: either add the four validators to Allowed files, or record that they need no change and define parity as "scaffolder capabilities ∪ fixture capabilities ⊆ schema `capabilities.properties`, plus top-level `test_routing` and `coverage.properties.package_floors` in all 6 schemas". | fixed in f4deb43 |
| 4 | Important | task_02_receipt_hygiene_diff_coverage_and_scaffolder.md:Files / 2026-11-28-shift-left-quality-resolver-design.md:§8.1 | `skills/setup_quality_check/resources/templates/web-quality.template.json` still has bare `npx` (L5, L9) and duplicate `pr_diff_audit`/`pr_impact` in `epic`/`release`. The spec says to fix "the Web template", but this file is outside Allowed files, so the task either triggers Stop-and-Report or ships a template that contradicts the scaffolder (it is pinned by tests/test_plq_quality_contracts_and_scaffolder.py:470-480). Proposed: add the template to Task 02 Allowed files and extend the HP-02 assertions to cover it, or explicitly list it as out of scope in the spec. | fixed in f4deb43 |
| 5 | Important | shift_left_quality_resolver.md:Module Contracts and CLI Interfaces §5(b) and Spec Errata | The HLD and spec §6.1(2) reject any bare top-level `src`/`tests` in Task 1..N-1. Task 04 narrows this to manifest caps ending in `.` or `src tests`, and only when both are present. This repo's own lint cap (.agents/quality/python-quality.json) includes bare `tests`. Under the HLD wording, every intermediate task here would fail, including this epic's Tasks 01–04 V4 rows. Despite this, Spec Errata says "None". Proposed: rewrite HLD §5(b) to Task 04's narrower rule and add a Spec Errata entry correcting spec §6.1(2). | fixed in f4deb43 |
| 6 | Important | task_03_on_demand_quality_plan_resolver_cli.md:BDD SCENARIOS (Covers) | SLQR-EC-03 and SLQR-EC-04 require `check_task_contract.py --design` to pass or reject, but those guards only arrive in Task 04 (Wave 3). Task 03 can only test resolver helpers, and Task 04 does not cover these scenarios. Proposed: move `SLQR-EC-03, SLQR-EC-04` to Task 04's `Covers:` and keep only helper unit tests in Task 03 without claiming the scenarios. | fixed in f4deb43 |
| 7 | Important | bdd_scenarios.md:SLQR-HP-03 / task_03_on_demand_quality_plan_resolver_cli.md:Definition of Done | The `< 0.10s` wall-clock limit for a cold subprocess run will be flaky. Measured startup alone is about 0.073–0.080s (median, idle machine) before manifest parsing and the repository template walk, and it will be slower while `verify.sh` is running. Proposed: assert the in-process `resolve_quality_plan()` time `< 0.1s` (best of N runs), bound the subprocess CLI at `< 1.0s`, and update the wording in the spec §1/§5.1, HLD Goals and BDD to match. | fixed in f4deb43 |
| 8 | Minor | 2026-11-28-shift-left-quality-resolver-design.md:§4.1 | Unknown `test_routing` keys map to `unknown_field`, while task_01 and SLQR-FR-01 use `invalid_test_routing`. Proposed: change the spec to `invalid_test_routing`. | fixed in f4deb43 |
| 9 | Minor | 2026-11-28-shift-left-quality-resolver-design.md:§6.1 item 5 | The item contains leftover deliberation text ("unless claimed in an explicit downstream integration task…? No — …!"). Proposed: replace it with "every referencing template MUST appear in the same task's Allowed files." | fixed in f4deb43 |
| 10 | Minor | 2026-11-28-shift-left-quality-resolver-design.md:§7.2 | The spec requires a clean tracked and untracked working tree, but the HLD and task_02 use `dirty_files(untracked=False)`. Proposed: change §7.2 to "tracked changes only", matching `cmd_preflight` (integrate_branch.py:338-339). | fixed in f4deb43 |
| 11 | Minor | 2026-11-28-shift-left-quality-resolver-design.md:§8.1 | `workspace_impact` is described as `--all-files --base-ref {base_ref}`, but the scaffolder emits only `--all-files` (scaffold_quality_manifest.py:585-588). Proposed: drop `--base-ref {base_ref}` from the spec text. | fixed in f4deb43 |
| 12 | Minor | task_03_on_demand_quality_plan_resolver_cli.md:Impact Analysis & Blast Radius | `tests/test_fpg_agy_profile_pool.py` does not use `bin/d3nexus`; the real consumer is `tests/test_task_contract_ergonomics_e2e.py:16`. Proposed: replace it in Downstream Callers and in V3. | fixed in f4deb43 |
| 13 | Minor | task_05_lean_skills_verify_registry_and_acceptance.md:Decisions Already Made | A tracked test would hard-code `/Users/danhdueexoictif/...` sibling paths and a fixed `44/44` count. That conflicts with the kit's personal-path leak checks (tests/test_plq_end_to_end_acceptance.py:115-118) and makes the release gate depend on sibling worktrees that change over time. Proposed: read sibling roots from an env var (e.g. `SLQR_ECOSYSTEM_ROOT`), skip when it is unset, and assert "all discovered profiles PASS" instead of a fixed count. | fixed in f4deb43 |
| 14 | Minor | task_01_registry_prefix_wrappers_and_provider_schemas.md:BDD SCENARIOS | SLQR-AR-01 names `resolve_task_quality_plan.py`, which does not exist until Task 03, and Task 03 re-verifies it without covering it. Proposed: move `SLQR-AR-01` to Task 03's Covers, or split the registry half into a Task 01 unit test. | fixed in f4deb43 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-28T03:48:18Z
- **SHA**: 02908bd813d6a414fa66a30b4048a050fe1eb969
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Scope**: delta from round 1 (3faa8b2)
- **Raw log**: `build/reviews/shift_left_quality_resolver_principal_round2_02908bd.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_01_registry_prefix_wrappers_and_provider_schemas.md:BDD SCENARIOS SLQR-EC-01 / shift_left_quality_resolver.md:Module Contracts and CLI Interfaces §2 | The Python positive/negative `uv --directory` pair cannot be checked through `validate_tier_b`, which skips Python (`_stack_lifecycle_registry.py:1196,1211`). Through `_subcommand_matches_prefix()`, the unwrapped mismatched row matches the built-in `ruff check` default (`:198`), and the positive row cannot match the capability prefix because `_cap_command_str()` (`:739-751`) keeps the trailing `.`. Proposed: in HLD §2 and task_01 Decisions, (a) assert the Python pair directly through `_subcommand_matches_prefix(sub, <manifest-derived prefix>)`, not `validate_tier_b`, (b) make `_cap_command_str()` strip trailing positional targets (`.`, `src`, `tests`) from capability-derived prefixes, and (c) make a sub carrying `--directory/--project/--prefix <d>` match only prefixes that declare the same `<d>`, not wrapper-less defaults; change the EC-01 `When` line to name `_subcommand_matches_prefix` for the Python rows. | fixed in 0c0a73a |
| 2 | Minor | bdd_scenarios.md:SLQR-EC-01 / task_01_registry_prefix_wrappers_and_provider_schemas.md:SLQR-EC-01 | `uv --directory apps/align-worker run ruff check apps/align-worker/src/mod.py` uses a repo-root-relative path, but uv resolves it from `apps/align-worker/`, so the real command would fail (`apps/align-worker/apps/align-worker/src/mod.py`). The negative row has the same flaw. Proposed: use `src/mod.py` in same-wrapper rows (relative to `<dir>`), and state in task_03 that resolver-synthesised scoped targets are rewritten relative to the wrapper directory. | fixed in 0c0a73a |
| 3 | Minor | task_05_lean_skills_verify_registry_and_acceptance.md:Impact Analysis & Blast Radius L57 / shift_left_quality_resolver.md:L168 / 2026-11-28-shift-left-quality-resolver-design.md:§11 L249 | `live 5-repo (44/44 profile)` and `44/44` remain, which contradicts the revised Decision (synthetic fixtures plus optional `SLQR_ECOSYSTEM_ROOT`). Proposed: replace each with "synthetic 5-repo fixtures plus optional `SLQR_ECOSYSTEM_ROOT` profiles (all discovered profiles PASS)". | fixed in 0c0a73a |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 3

- **Date**: 2026-11-28T04:01:45Z
- **SHA**: 80ae793037955d26a48ed3ce6a4e45f84676832f
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: discarded: tree modified (.vscode/settings.json)
- **Verdict**: PASS
- **Kind**: principal
- **Scope**: convergence from round 2 (02908bd)
- **Raw log**: `build/reviews/shift_left_quality_resolver_principal_round3_80ae793.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|

Raw output:

```text
Verdict: PASS
```
