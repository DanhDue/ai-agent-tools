# Cross-Model Review: sync_shared_contracts

## Round 1

- **Date**: 2026-10-30T14:18:15Z
- **SHA**: 38857a00e179fd8261d87725e5d3ccf78e9ca06b
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:782 | `check`'s global drift report reads the stale `pending_rfcs` persisted at last `ack` instead of recomputing it from the freshly-parsed `gaps_and_rfcs.md`, and `compute_semantic_delta` never diffs RFCs at all, so a newly-added unacknowledged RFC is not surfaced in `check --strict`'s output even though exit code 1 still fires — contradicting BDD SYC-ST-01's explicit "surfaces... RFC-002" clause, uncaught because `test_syc_st_01` only asserts exit codes. | fixed in 7de1ada |
| 2 | Important | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:849 | `cmd_brief` never loads `.agents/contract_sync.json` (confirmed `load_sync_state` is only called from `cmd_ack`), so every `brief` invocation hardcodes `sync_status="INITIAL_SYNC"`, `previous_version="none"`, and `hub_commit_range="HEAD"` regardless of real prior sync state, contradicting HLD §5.2's "Version transition (previous -> current)" promise; no test exercises the CLI path with a pre-existing watermark to catch this. | fixed in 7de1ada |
| 3 | Minor | .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§3 | Hub-mode "iterates over domain subdirectories" is not implemented (`--domain` is always a single fixed value); not covered by any BDD scenario, so it is a documentation overclaim rather than a tested regression. | dismissed: Hub multi-domain scan is non-blocking roadmap item; CLI operates per --domain as specified in BDD. |

Raw output:

```text
## Review: sync_shared_contracts (candidate `38857a0`)

**Scope confirmed**: this epic ships a self-contained developer-tooling skill (`sync-shared-contracts`) — the HLD's Shared Contract Impact is explicitly "None," so there is no `task_01` contract-mutation commit to check against the Non-Breaking Schema Guarantee; that governance path doesn't apply here.

**Process trail**: Both design-spec language and BDD IDs are in full parity between `en`/`vi` (15/15 identical scenario IDs, identical heading structure). `principal_review.md` recorded two rounds (both `CHANGES REQUIRED`), and all eight findings across the two rounds are marked "fixed in `68f6d63`" / "fixed in `bc6406c`" respectively — I traced several of these fixes into the current HLD/task text (snapshot-bound `ack`, scope-bound `--rfc` tracking, worktree-aware symlink resolution, `baseline_snapshot.payload_fields`) and they are genuinely present in the code, not just prose. No Round 3 is recorded after the Round 2 fix commit, which is a process gap worth noting to the developer, but since `handoff.md` records Gate 2 as passed and the fixes are independently verifiable in code, I'm not treating it as blocking.

**Audit / traceability evidence**: `audit_epic.py` is PASS for all four tasks, the only protected-path touch (`scripts/verify.sh`) is explicitly authorized by Task 4's `Allowed files` and the diff is the single expected line, and the three grader amendments to task docs are all consistent with the Round 1/2 Principal Review fixes (verified task_1/2/3 diffs against actual code behavior). `check_bdd_traceability.py` reports 15/15 scenario IDs mapped 1:1 to test methods, and the unit suite is green (16/16 tests, including the one non-BDD helper test `test_to_camel_case`).

**Gate 5 items** (task execution verified & recorded in evidence) — present and satisfied for all four tasks: `task_1_brief_template_and_contract_parser`, `task_2_heuristic_scanner_and_check_engine`, `task_3_watermark_ack_and_brief_cli`, `task_4_skill_definition_and_verify_integration`, each with an evidence JSON under `.devtool/epic/sync_shared_contracts/evidence/`.

**Where the implementation falls short of its own spec**, despite the green test suite:

1. `cmd_check`'s global drift report never recomputes which RFCs are actually pending — it just echoes `dom_data.get("pending_rfcs", [])`, the list persisted at the *last* `ack` (`sync_contracts.py:782`, reused at `794-807`). `compute_semantic_delta` (`503-541`) only diffs `endpoints`/`payload_keys`/`payload_fields`/`pipeline_steps` — it never diffs `rfcs`, despite the HLD §5.1 step 4 explicitly promising "endpoints, pipeline steps, and RFCs" in the semantic baseline comparison. Concretely: if a Hub domain is `IN_SYNC` (`pending_rfcs: []`) and a new `OPEN` RFC is added to `gaps_and_rfcs.md` without running `ack`, `check --strict --json` still correctly exits `1` (because the file hash changed), but its `pending_rfcs` field still prints `[]` and nothing in `deltas` names the new RFC — contradicting BDD `SYC-ST-01`'s explicit acceptance clause that `check --strict` "surfaces... RFC-002" before acknowledging. `test_syc_st_01_ack_snapshot_and_incremental_drift` only asserts the exit code transition (1 then 0), never inspecting `check`'s output content, so this gap passes CI silently.

2. `cmd_brief` (`812-871`) never calls `load_sync_state` (that function is used only inside `cmd_ack`, confirmed by grep) — every invocation hardcodes `sync_status="INITIAL_SYNC"`, `previous_version="none"`, and `hub_commit_range="HEAD"`, regardless of real prior watermark state. This contradicts HLD §5.2's explicit "Version transition (`previous -> current`)" / "Sync Status" promise for the rendered Contract Requirements Brief, and means every *repeat* `brief` on an already-synced domain still reports it as a first-time initial sync. `test_syc_hp_01` only exercises `render_brief()` directly with manually-supplied correct values, then separately checks `main(["brief", ...])` only for exit code 0 and file existence — it never checks that the CLI path actually computes these fields. Relatedly, `test_syc_st_01` — whose BDD text says the engineer "refreshes the snapshot_id via `sync_contracts.py brief`" — never actually invokes the `brief` subcommand; it recomputes the hash directly via `compute_file_hash`/`compute_snapshot_id`, so the documented refresh path through `brief` is untested end-to-end.

Both gaps are real behavioral divergences from the HLD/BDD, not just prose overstatement, and both happen to be invisible to the existing test suite because the tests assert exit codes / isolated helper functions rather than the actual CLI output content the scenarios describe. Neither breaks the primary safety property (drift still forces a non-zero exit), which is why I'm rating them Important rather than Critical.

One Minor item for completeness: the HLD's Hub-mode description ("iterates over domain subdirectories") isn't implemented — `--domain` always defaults to a single fixed value (`lyrics-sync`) with no multi-domain enumeration — but no BDD scenario requires this, so it's a documentation overclaim rather than a tested-and-broken contract.

Verdict: CHANGES REQUIRED
[Important] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:782 — `check`'s global drift report reads the stale `pending_rfcs` persisted at last `ack` instead of recomputing it from the freshly-parsed `gaps_and_rfcs.md`, and `compute_semantic_delta` never diffs RFCs at all, so a newly-added unacknowledged RFC is not surfaced in `check --strict`'s output even though exit code 1 still fires — contradicting BDD SYC-ST-01's explicit "surfaces... RFC-002" clause, uncaught because `test_syc_st_01` only asserts exit codes.
[Important] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:849 — `cmd_brief` never loads `.agents/contract_sync.json` (confirmed `load_sync_state` is only called from `cmd_ack`), so every `brief` invocation hardcodes `sync_status="INITIAL_SYNC"`, `previous_version="none"`, and `hub_commit_range="HEAD"` regardless of real prior sync state, contradicting HLD §5.2's "Version transition (previous -> current)" promise; no test exercises the CLI path with a pre-existing watermark to catch this.
[Minor] .devtool/epic/sync_shared_contracts/2026-10-30-sync-shared-contracts-design.en.md:§3 — Hub-mode "iterates over domain subdirectories" is not implemented (`--domain` is always a single fixed value); not covered by any BDD scenario, so it is a documentation overclaim rather than a tested regression.
```

## Round 2

- **Date**: 2026-10-30T14:55:48Z
- **SHA**: 0378a4dcd9444048ef25aef4d331a7addd0fe6af
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: PASS

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | principal_review.md:Round 2 | no Round 3 entry records a PASS verdict confirming the bc6406c fixes; Gate 2 sign-off is evidenced only by handoff.md's "Gates passed: 1, 2" line rather than a closing review round in this file. | dismissed: Gate 2 sign-off is recorded in handoff.md before Gate 3 execution began. |
| 2 | Minor | .devtool/epic/sync_shared_contracts/evidence/task_3_watermark_ack_and_brief_cli.json | timestamped before commit 7de1ada, so this Gate 5 record does not reflect the fixed dynamic-pending-RFC/brief-watermark behavior, even though the final full-suite run at the candidate SHA does exercise it. | dismissed: Gate 5 records initial task completion; candidate SHA integration suite verifies 7de1ada fix. |
| 3 | Minor | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:cmd_check | duplicates load_sync_state's corrupted-watermark fallback inline instead of calling it; a cosmetic DRY issue with no behavioral difference, both paths are independently tested. | dismissed: Cosmetic DRY observation; behavior verified by test suite. |
| 4 | Minor | skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:test_syc_ar_01_atomic_watermark_update | only asserts the absence of stray temp files rather than simulating a crash mid-write, so it is a weak proxy for the atomicity claim its name makes. | dismissed: Non-blocking test observation; atomic rename guaranteed by POSIX os.replace. |

Raw output:

```text
# External Review — Epic `sync_shared_contracts` (candidate `0378a4dcd9444048ef25aef4d331a7addd0fe6af`)

## Task evidence vs. Verification tables

**Task 1 — Brief template and contract parser.** The template (`contract_delta_brief.md.tmpl`) and the dual-format Markdown parser are both present and match the grader-amended DoD ("render the full brief for both table and narrative contracts"). `parse_api_contract`/`parse_architecture_and_flow`/`parse_gaps_and_rfcs` each try table-regex extraction first and narrative-regex extraction second, unioning results, and raise `UNSUPPORTED_CONTRACT_FORMAT` when neither matches — this is a real implementation of the amendment, not a doc-only change. V2–V6 all ran GREEN in evidence; `ruff`/`mypy --strict` clean. Evidence is internally consistent with the task's own table.

**Task 2 — Heuristic scanner and dual-mode check engine.** `resolve_topology` implements worktree-aware resolution (parses the `.git` gitdir pointer or walks up to a `.worktrees` parent, then re-resolves the tracked relative symlink against the primary root), a bounded hop counter plus a visited-set cycle guard for circular symlinks, and clear `TopologyError` messages for dangling links/missing directories. `compute_semantic_delta` diffs a `payload_fields` dotted type map, which is exactly the "semantic baseline diffing" the grader amendment added to the DoD (detects a field whose *type* changed, not just added/removed names). `scan_target_codebase` strips `{param}` segments from paths and generates camelCase variants of snake_case keys before matching. All of V1–V10 passed per evidence; the newly added `test_syc_ec_04_worktree_aware_symlink_resolution` was independently re-verified — it builds a real nested `.worktrees/<epic>/` directory with a real relative symlink computed against the outer root and a synthetic `.git` gitdir file, which forces the code through the actual fallback branch rather than exercising it superficially.

**Task 3 — Watermark ack, drift detection, brief CLI.** `save_sync_state_atomic` writes via `tempfile.mkstemp` in the same directory, `fsync`s, then `os.replace`s — a correct atomic-rename pattern with cleanup on failure. The on-disk schema is multi-domain (`{"domains": {...}}}`), and `ack`'s scope logic (`contract_active_rfcs & newly_acked` vs. `- newly_acked`) only acknowledges explicitly selected RFCs unless `--all-rfcs`/no-active-RFCs, matching the grader-amended DoD line about unselected RFCs staying pending. Snapshot-mismatch rejection (`SNAPSHOT_MISMATCH`, exit 1, no write) and corrupted-watermark recovery (`check` warns and falls back; `ack` repairs by unconditionally rewriting) are both implemented and independently confirmed by direct test execution (16/16 pass). One nuance worth surfacing to the developer: this task's own evidence JSON (`evidence/task_3_watermark_ack_and_brief_cli.json`) was captured before commit `7de1ada`, which changed the RFC-pending and brief-watermark logic this task owns — see "Commits outside tasks" below.

**Task 4 — Skill definition, lifecycle bridge, verify integration.** `SKILL.md` frontmatter is exactly `name` + `description`, matching this repo's own authoring rule. `scripts/verify.sh`'s one-line addition wires `test_sync_contracts.py` into section 14 using the identical convention as its neighboring registrations. This is the one task authorized to touch that otherwise-protected file, and the HLD's Verification Environment note explicitly documents the carve-out — the protected-path audit disclosure for `38857a0 scripts/verify.sh` is therefore justified, not a violation.

## Scenario-to-test fidelity

All 15 BDD scenario IDs map 1:1 to dedicated test methods (confirmed by direct traceability tooling and independently by reading every test). None of the 16 test methods reconstruct production logic: every assertion either calls a `sync_contracts` function directly (`parse_api_contract`, `resolve_topology`, `compute_semantic_delta`, `scan_target_codebase`, `to_camel_case`) or drives the real `main()` CLI entrypoint — the same function used by the script's own `__main__` block — with a full `argv` list. `mock.patch` appears only to capture `stdout`/`stderr` for assertions, never to stub a collaborator, hash, or filesystem call. Tests build genuine temp directories with real files and real `os.symlink` calls; nothing substitutes synthetic data that would mask a real defect. `test_syc_ec_04` and `test_syc_hp_02` in particular reproduce a real nested-worktree symlink topology rather than asserting against a mocked one. Two scenario tests are comparatively weak relative to what they claim (flagged below as Minor, not blocking): `test_syc_ar_01` only checks that no stray `.tmp` file is left behind rather than simulating a crash mid-write, and `test_syc_hp_03` validates repo-structure metadata via plain string checks rather than calling into `sync_contracts.py` — appropriate given there's no frontmatter-parsing logic in the module to call, but worth naming as what it actually tests.

## Audit disclosures

The grader amendments to task_1/2/3 (adding dual-format parsing, worktree-aware resolution, semantic baseline diffing, and snapshot/RFC-scope language) are all traceable to specific Principal Review round-1 and round-2 findings and their fix commits (`68f6d63`, `bc6406c`), not silent scope drift — the two Principal Review rounds (both recorded as CHANGES REQUIRED) list eight Important findings, and all eight are annotated "fixed in" a specific commit. The protected-path disclosure (`scripts/verify.sh`) is explicitly authorized for Task 4 only, as documented in both the HLD and `handoff.md`.

The one disclosure needing real scrutiny is the out-of-task commit `7de1ada "Fix dynamic pending RFC detection and brief watermark loading"`. This postdates a separate, later cross-model code review (`review_results.md`, not in the originally supplied artifact list but directly relevant) that found two Important code-level gaps: `cmd_check`'s drift report wasn't recomputing pending RFCs from the live parsed contract, and `cmd_brief` never called `load_sync_state`, so every brief hardcoded `INITIAL_SYNC`/`previous_version="none"` regardless of real prior state. I verified directly in the current code (not just trusting the "fixed in" annotation) that both are genuinely fixed: `evaluate_domain_sync` and `cmd_ack` both recompute `pending_rfcs` from the live parsed `gaps_and_rfcs.md` state rather than reading a stale persisted field, and `cmd_brief` now calls `load_sync_state`. This out-of-task fix commit is therefore justified — it's a real fix for a real, independently-discovered defect, applied and verified at the final SHA, consistent with this repo's fix-then-human-checkpoint review discipline.

## Spec, HLD, and schema fidelity

The implementation matches each task's "Decisions Already Made" section: watermark schema fields (`schema_version`, `baseline_snapshot.payload_fields`, `acknowledged_rfcs`, `pending_rfcs`) line up exactly between the HLD, `SKILL.md`'s documented schema, and what `cmd_ack` actually writes. `MAX_SYMLINK_HOPS = 10` and the excluded-directories list match the task 2 decisions. No test-only special-casing of a domain name leaks into production logic — `"lyrics-sync"` appears only as an argparse default value with zero conditional branching on it anywhere in `sync_contracts.py`, and the second domain used in tests (`"nexus"`) doesn't appear in production code at all, which is the right way to prove multi-domain support is generic rather than hardcoded. The HLD's "## Shared Contract Impact: None — self-contained developer tooling skill" claim holds: this epic builds a tool that *reads* other repositories' `shared-contracts/` trees, it does not modify any Hub's canonical contract content, so the Non-Breaking Schema Guarantee and task_01 synchronization check do not apply to this epic.

## Gate 5 items (restated)

All four tasks carry the same Gate 5 requirement — "Task execution is verified and recorded in evidence" — and all four have a corresponding JSON in `.devtool/epic/sync_shared_contracts/evidence/` showing a RED run followed by a fully GREEN/TIER-B/TIER-C verification run with zero scope violations. These are internally consistent with each task's own Verification table. The one caveat already noted: Task 3's evidence JSON predates the later `7de1ada` fix, so it does not itself demonstrate the fixed RFC/brief behavior — that demonstration instead comes from the final full-suite run captured in this review's own facts, executed at the candidate SHA.

Verdict: PASS
[Minor] principal_review.md:Round 2 — no Round 3 entry records a PASS verdict confirming the bc6406c fixes; Gate 2 sign-off is evidenced only by handoff.md's "Gates passed: 1, 2" line rather than a closing review round in this file.
[Minor] .devtool/epic/sync_shared_contracts/evidence/task_3_watermark_ack_and_brief_cli.json — timestamped before commit 7de1ada, so this Gate 5 record does not reflect the fixed dynamic-pending-RFC/brief-watermark behavior, even though the final full-suite run at the candidate SHA does exercise it.
[Minor] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:cmd_check — duplicates load_sync_state's corrupted-watermark fallback inline instead of calling it; a cosmetic DRY issue with no behavioral difference, both paths are independently tested.
[Minor] skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:test_syc_ar_01_atomic_watermark_update — only asserts the absence of stray temp files rather than simulating a crash mid-write, so it is a weak proxy for the atomicity claim its name makes.
```
