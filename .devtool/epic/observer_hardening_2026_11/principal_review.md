# Principal Review: observer_hardening_2026_11

## Round 1

- **Date**: 2026-11-26T15:27:16Z
- **SHA**: 9883d69311b76088cb49be4a7f66702cde4799ca
- **Base**: main
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/observer_hardening_2026_11_principal_round1_9883d69.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/observer_hardening_2026_11/task_01_ohk_worktree_status_and_pool_isolation.md:120 (Decisions Already Made) | Directory presence does not establish checkout ownership. Epic B can inherit Epic A’s directory, so preferring `current_root` still permits cross-epic writes. `skills/dev-implementation/resources/scripts/sync_task_status.py:289` retains the current checkout unconditionally; line 1430 synchronizes across returned roots. Proposed: filter every candidate, including `current_root`, by branch ownership and slot exclusion before selecting authority; add a regression invoking Epic A commands from Epic B with inherited Epic A files. |  |
| 2 | Important | .devtool/epic/observer_hardening_2026_11/task_04_ohk_web_ui_audit_subdir_and_hotfix.md:109 (Decisions Already Made) | Restricting Invariant 2 to `ui_modified` misses regressions in unchanged dependent templates. An in-memory probe removing a CSS class produced one orphan finding with full template coverage and zero with `target_files=["style.css"]`. The dependency exists at `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py:294`; candidate selection narrows at line 328. Proposed: include templates affected by changed stylesheets, and evaluate baseline findings against baseline stylesheet definitions before suppression; add a CSS-only class-removal scenario. |  |
| 3 | Important | .devtool/epic/observer_hardening_2026_11/task_04_ohk_web_ui_audit_subdir_and_hotfix.md:105 (Decisions Already Made) | `.lstrip("./")` removes meaningful path characters: the probe transformed `.well-known/index.html` into `well-known/index.html`. Failed baseline lookup can bypass version comparison when the template also appears in modified files (`skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py:249`–280). Proposed: remove only an exact `./` prefix, preserve dot-prefixed components, reject parent traversal, and test an unchanged cache version in a modified dot-directory template. |  |
| 4 | Important | .devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md:223 (§4.3) | The protected set omits `.agents/contract_sync.json`, although `skills/sync-shared-contracts/resources/scripts/sync_contracts.py:1582` reads acknowledgement proof from the working tree and line 1625 accepts it. A mocked read-only probe returned `PASS` with `proof=ack` using an uncommitted acknowledgement after the proposed guard admitted it. Proposed: protect acknowledgement changes too, or read acknowledgement proof from `HEAD`; extend Task 5 and BDD coverage so an uncommitted acknowledgement cannot satisfy a committed source delta. |  |
| 5 | Important | .devtool/epic/observer_hardening_2026_11/task_05_ohk_cmr_deferred_smoke_and_contracts_dirty.md:134 (Decisions Already Made) | The unrestricted `startswith("deferred:")` alternative lets an ordinary source finding carrying `deferred: arbitrary` produce `AUTO_PASS_CLEAN`, contradicting the immutable-epic-document boundary. This bypasses the Minor sweep currently selected by `skills/dev-implementation/resources/scripts/run_external_review.py:2520`. Proposed: require the exact canonical token and an eligible immutable epic-document location; keep other rows actionable and add a negative test for a source finding with an arbitrary deferred marker. |  |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
