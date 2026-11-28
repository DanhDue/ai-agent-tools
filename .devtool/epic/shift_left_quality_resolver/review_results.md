# Cross-Model Review: shift_left_quality_resolver

## Round 1

- **Date**: 2026-11-28T05:45:41Z
- **SHA**: ce86d18bd0efb7c4eb0abcc4b4760dcfd5acf4a8
- **Base**: main
- **CLI**: claude
- **Model**: opus
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Raw log**: `build/reviews/shift_left_quality_resolver_code_round1_ce86d18.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/check_task_contract.py:1158-1217 (_matches_python_cap / allowed_py) | removing the legacy cap[:-1] match and requiring concrete .py Allowed files means a non-final Python task with glob/dir Allowed entries (e.g. src/pkg/*.py) fails both scoped TIER-B ("missing registered lint/type_check capability") and full-repo TIER-B (non-final-task scope rule), so no command can pass; main accepted it. Proposed: treat glob/directory Allowed entries as coverage roots (positional targets covered by or covering an Allowed glob/dir are accepted), or fall back to the legacy cap[:-1] acceptance when allowed_py is empty; add a regression test with `src/pkg/*.py`. | fixed in 9886cd6 |
| 2 | Important | skills/dev-implementation/resources/scripts/check_task_contract.py:2077-2091 (_task_order_key) | the stem regex `\btask[_-]?0*(\d+)\b` never matches `task_NN_<slug>` (underscore is a word char), and the order fallback keeps only trailing digits, so `order: "a9"` outranks `"b1"`; the true final task is treated as non-final (false SLQR-EC-04 FAIL) and an earlier task is exempted. Proposed: match `^task[_-]?0*(\d+)(?=[_-]\|$)` and compare `order` as (letter prefix, numeric suffix) or lexicographic fractional index; add a test with a9/b1 orders. | fixed in 9886cd6 |
| 3 | Minor | skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py:411 | cache-bust regex matches the asset name as a substring (`app.js` matches `/static/webapp.js?v=1`, confirmed), producing fail-closed false positives in --design/--check-plan. Proposed: anchor to a path boundary: `(?:src\|href)=['"](?:[^'"]*/)?{name}(\?[^'"]*)?['"]`. | fixed in 9886cd6 |
| 4 | Minor | skills/dev-implementation/resources/scripts/check_task_contract.py:1710,2070 | malformed web-quality.json / test_routing makes the LCOV, test-routing and cache-bust guards silently self-skip (`_read_optional_manifest_json` returns None; `_load_repo_manifests` errors are discarded), contradicting the fail-closed design and the resolver's exit-2 behaviour. Proposed: report a check.problem naming the malformed manifest. | fixed in 9886cd6 |
| 5 | Minor | skills/dev-implementation/resources/scripts/resolve_task_quality_plan.py:1138 (format_compact_plan) | `unmatched_files` is only printed when no stack matched, so a planned `.js` in a repo without web-quality.json is silently dropped from guidance. Proposed: append `UNMATCHED: ...` whenever unmatched_files is non-empty. | fixed in 9886cd6 |
| 6 | Minor | tests/test_slqr_end_to_end_acceptance.py:436 | ecosystem capability parity ignores schema `patternProperties`, so `SLQR_ECOSYSTEM_ROOT` pointed at the real ecosystem fails on D3Nexus `contracts_lyrics_sync`/`contracts_nexus`, which the rust schema accepts via `^contracts_[a-z0-9_]+$`. Proposed: treat a capability as present if it matches any patternProperties regex. | fixed in 9886cd6 |
| 7 | Minor | skills/finishing-a-development-branch/resources/scripts/integrate_branch.py:1-830, bin/d3nexus:1-50 | whole-file reformatting (about 350 lines) unrelated to the 3-line dirty-tree warning violates the surgical-changes rule and hides the functional diff. Proposed: revert formatting-only hunks, keeping the `cmd_verify_tier` warnings change. | fixed in 9886cd6 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
