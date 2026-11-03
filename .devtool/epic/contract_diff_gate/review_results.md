# Cross-Model Review: contract_diff_gate

## Round 1

- **Date**: 2026-11-02T13:19:34Z
- **SHA**: ce1cc65b2f84cb8db653cdfcda14339bd48c9303
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1429 | `normalize_rfc_status()` is applied to the already-normalized `rfcs[gap]["status"]`; the literal `"INACTIVE"` is unrecognized and defaults back to `"ACTIONABLE_PENDING"`, so a newly added waiver citing a `REJECTED`/`SUPERSEDED` gap exits `0` instead of `1`, fails the gate open, and contradicts the design's FAIL table, HLD Goals, and the `INACTIVE` clause of CDG-ST-03. Compare `info.get("status")` directly (as lines 821/1140 do) or normalize `raw_status`. | fixed in f27f008 |
| 2 | Important | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1274 | topology is resolved only for `next(iter(head_domains))`, but Hub Rules step 1 requires resolving `shared-contracts/<D>/` for every HEAD domain; probed on a two-domain Hub with `shared-contracts/nexus/` absent, the same repository returns `PASS` when `lyrics-sync` is listed first and `BLOCKED` when `nexus` is, making the fail-closed guarantee depend on JSON key order — and D3Nexus is the named multi-domain Hub target. | fixed in f27f008 |
| 3 | Important | skills/sync-shared-contracts/SKILL.md:133 | the shipped "Contract Map Schema" example contradicts `validate_contract_map`: it uses `"version": 1` instead of `"schema_version": 1`, omits the mandatory `base_ref`, and nests `waivers` inside the domain object without the required `domain` field, so a repository configured from this documentation is rejected with exit `2` (`Expected schema_version 1, got None`) rather than gated; it also disagrees with the `contract_map.json.tmpl` shipped in the same epic. | fixed in d2ea5e9 |
| 4 | Minor | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1644 | `violations` entries use keys `{"file", "domain", "message"}` while the approved design froze `{"domain", "path", "reason"}` for the `--json` schema; the type still matches and nothing consumes it yet, but the only written schema for the gate's machine interface now diverges from its output. | fixed in f27f008 |
| 5 | Minor | skills/sync-shared-contracts/SKILL.md:112 | documents `--base-ref` as defaulting to "`develop` if present, else `main`", whereas the implementation falls back to `contract_map.json`'s own `base_ref` field; line 120 likewise omits `--no-ext-diff` and `--name-only` from the diff command, and the exit-`2` list omits the dirty-tracked-tree blocker. | fixed in d2ea5e9 |
| 6 | Minor | skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:816 | `test_cdg_ec_05_*` builds only a Hub repository, but CDG-EC-05 and its Covers assignment claim rename-out and C-quoted-filename detection "Across Hub and Satellite"; the Satellite half of the scenario is never executed. | fixed in d51dfeb |
| 7 | Minor | skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:757 | in `test_cdg_ec_03_*` the fixture creates `develop` directly off `main` with no intervening commit, so `merge-base(develop, HEAD)` equals `merge-base(main, HEAD)`; the test would pass unchanged if `--base-ref` were ignored entirely, leaving the override-precedence clause of CDG-EC-03 unverified. | fixed in d51dfeb |
| 8 | Minor | skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:1050 | the `GAP-999` sub-case of `test_cdg_st_03_*` runs on a branch freshly cut from `develop`, so `src/api/dto/worker.py` is not in `M..HEAD` and the scenario's "Given ... mapped changes in domain lyrics-sync" is not realized; it asserts only `exit == 1` with no message check, so it cannot distinguish the gap violation from an unrelated failure. | fixed in d51dfeb |
| 9 | Minor | skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:1340 | the duplicate-waiver-id sub-case of `test_cdg_fr_01_*` writes the malformed map without committing, leaving the tree dirty; since both the schema defect and the dirty tree yield `BLOCKED`, the bare `status == "BLOCKED"` assertion would still pass if duplicate-id validation were removed, and CDG-FR-01's "naming the schema defect" clause is not asserted. | fixed in d51dfeb |
| 10 | Minor | skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1630 | a domain is reported as `proof: "waiver"` whenever path coverage matches, even when that waiver's `gap` citation produced a violation, so the per-domain discharge proof surfaced for Gate 4 and Gate 5 audit can read `waiver` on a run whose overall status is `FAIL`. | fixed in f27f008 |

Raw output:

````text
I've completed the review. Here is my report.

## Scope verified

I read all six epic artefacts plus the three task files and evidence JSONs, inspected the full source diff file-by-file, and ran read-only dynamic probes against `diff-check` in throwaway git repositories (Hub, multi-domain Hub, Satellite, bootstrap, baseline-union) plus direct probes of the glob compiler and the RFC status normalizer.

**What holds up.** The glob compiler is anchored and matches `task_contract.py` semantics (I probed 18 patterns, including `**/` at zero and multiple depths, `*`/`?` not crossing `/`, exclude precedence, and regex metacharacters in path literals). The tests are genuine: they build real git repositories, invoke `main()` on the real production entrypoint, and reconstruct no production logic. Evidence files record real RED runs — Task 1's RED is an authentic `argparse.ArgumentError: invalid choice: 'diff-check'`. `ruff` and `mypy --strict` both still pass at `ce1cc65`. Task 2's five schemas all carry `contracts`, `contract_diff`, `patternProperties["^contracts_[a-z0-9_]+$"]` with `additionalProperties: false` retained, plus `db_hygiene` on Rust only — exactly as frozen. Bilingual parity across the four `.en`/`.vi` artefact pairs is intact (all 17 identifiers and all `##` sections match). The two CDG-ST-04 variants the test skips (path narrowing, domain deletion) both behave correctly under probe. The audit disclosures are justified: the DoD/`Covers` amendments trace to `4ed9835` and `5f03dc0`, the two pre-implementation Principal Review revision commits; the implementation commits `6484241`/`d9653b3`/`ce1cc65` touched only frontmatter `status`/`completedAt` and the HLD's `Status:` line, so the executor did not repair its own contract. Shared Contract Impact is correctly declared `None` — this repository has no `shared-contracts/` directory.

**The blocking defect.** A waiver citing a `REJECTED` or `SUPERSEDED` gap passes the gate. `parse_gaps_and_rfcs` already stores the *normalized* status (`"INACTIVE"`), but `cmd_diff_check` re-feeds it through `normalize_rfc_status`, which does not recognize the literal `"INACTIVE"` and so returns its default `"ACTIONABLE_PENDING"`. Probed directly:

```
GAP-09 (Rejected)   -> PASS, no violations     (spec: FAIL / exit 1)
GAP-10 (Superseded) -> PASS, no violations     (spec: FAIL / exit 1)
GAP-404 (absent)    -> FAIL, "non-existent gap"
GAP-09 stored status = INACTIVE | re-normalized = ACTIONABLE_PENDING
```

The rest of the file reads these statuses correctly (`sync_contracts.py:821`, `:1140` compare `info.get("status")` against the normalized set directly). This escaped the suite because `test_cdg_st_03` only exercises the *missing*-gap variant, even though its scenario names both.

**The Gate 5 items, restated for you:**
- Task 1 — review the active-waiver output format and code cleanliness. Note while doing this that a domain whose only waiver is invalid is still reported as `proof: "waiver"` (finding below).
- Task 2 — confirm provider parity across all five platforms. I verified the five schemas and five `SKILL.md` files are byte-equivalent in intent; Rust alone adds `db_hygiene`, and only Rust/Python carry the `references/` rule 6 and 7 additions, per the Decisions.
- Task 3 — review skill clarity and scope boundaries. `skills/principal-review/` and `skills/cross-model-review/` were correctly left untouched.

Verdict: CHANGES REQUIRED
[Critical] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1429 — `normalize_rfc_status()` is applied to the already-normalized `rfcs[gap]["status"]`; the literal `"INACTIVE"` is unrecognized and defaults back to `"ACTIONABLE_PENDING"`, so a newly added waiver citing a `REJECTED`/`SUPERSEDED` gap exits `0` instead of `1`, fails the gate open, and contradicts the design's FAIL table, HLD Goals, and the `INACTIVE` clause of CDG-ST-03. Compare `info.get("status")` directly (as lines 821/1140 do) or normalize `raw_status`.
[Important] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1274 — topology is resolved only for `next(iter(head_domains))`, but Hub Rules step 1 requires resolving `shared-contracts/<D>/` for every HEAD domain; probed on a two-domain Hub with `shared-contracts/nexus/` absent, the same repository returns `PASS` when `lyrics-sync` is listed first and `BLOCKED` when `nexus` is, making the fail-closed guarantee depend on JSON key order — and D3Nexus is the named multi-domain Hub target.
[Important] skills/sync-shared-contracts/SKILL.md:133 — the shipped "Contract Map Schema" example contradicts `validate_contract_map`: it uses `"version": 1` instead of `"schema_version": 1`, omits the mandatory `base_ref`, and nests `waivers` inside the domain object without the required `domain` field, so a repository configured from this documentation is rejected with exit `2` (`Expected schema_version 1, got None`) rather than gated; it also disagrees with the `contract_map.json.tmpl` shipped in the same epic.
[Minor] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1644 — `violations` entries use keys `{"file", "domain", "message"}` while the approved design froze `{"domain", "path", "reason"}` for the `--json` schema; the type still matches and nothing consumes it yet, but the only written schema for the gate's machine interface now diverges from its output.
[Minor] skills/sync-shared-contracts/SKILL.md:112 — documents `--base-ref` as defaulting to "`develop` if present, else `main`", whereas the implementation falls back to `contract_map.json`'s own `base_ref` field; line 120 likewise omits `--no-ext-diff` and `--name-only` from the diff command, and the exit-`2` list omits the dirty-tracked-tree blocker.
[Minor] skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:816 — `test_cdg_ec_05_*` builds only a Hub repository, but CDG-EC-05 and its Covers assignment claim rename-out and C-quoted-filename detection "Across Hub and Satellite"; the Satellite half of the scenario is never executed.
[Minor] skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:757 — in `test_cdg_ec_03_*` the fixture creates `develop` directly off `main` with no intervening commit, so `merge-base(develop, HEAD)` equals `merge-base(main, HEAD)`; the test would pass unchanged if `--base-ref` were ignored entirely, leaving the override-precedence clause of CDG-EC-03 unverified.
[Minor] skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:1050 — the `GAP-999` sub-case of `test_cdg_st_03_*` runs on a branch freshly cut from `develop`, so `src/api/dto/worker.py` is not in `M..HEAD` and the scenario's "Given ... mapped changes in domain lyrics-sync" is not realized; it asserts only `exit == 1` with no message check, so it cannot distinguish the gap violation from an unrelated failure.
[Minor] skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py:1340 — the duplicate-waiver-id sub-case of `test_cdg_fr_01_*` writes the malformed map without committing, leaving the tree dirty; since both the schema defect and the dirty tree yield `BLOCKED`, the bare `status == "BLOCKED"` assertion would still pass if duplicate-id validation were removed, and CDG-FR-01's "naming the schema defect" clause is not asserted.
[Minor] skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1630 — a domain is reported as `proof: "waiver"` whenever path coverage matches, even when that waiver's `gap` citation produced a violation, so the per-domain discharge proof surfaced for Gate 4 and Gate 5 audit can read `waiver` on a run whose overall status is `FAIL`.
````
