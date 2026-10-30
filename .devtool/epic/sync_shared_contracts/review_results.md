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
