# Cross-Model Review: observer_hardening_2026_11

## Round 1

- **Date**: 2026-11-26T19:02:48Z
- **SHA**: bb93b7c4a60e4228a788da3673ae8c769aacbc58
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: PASS
- **Raw log**: `build/reviews/observer_hardening_2026_11_code_round1_bb93b7c.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Minor | skills/dev-implementation/resources/scripts/generate_smoke_checklist.py:CLI_ENTRYPOINT_REGEX / extract_target_from_text | Plain prose matches as a command: "a git repository" becomes `` `git repository` ``, "Python repository" becomes `` `Python repository` ``, and the newly added `bash` gives `` `bash script` ``. This epic's own manual_smoke_checklist.md rows 1, 3 and 4 show the wrong targets. Proposed: apply the regex only inside quoted or backticked spans, or require the next word to be a script path, a file with an extension, or a flag. | fixed in a1d2243 |
| 2 | Minor | skills/dev-implementation/resources/scripts/replay_task_text.py:replay_epic_in_worktree | When some tasks are replayed and others skipped, it returns `(0, [])` and the report shows a plain "R8 PASS" with no mention of the skipped tasks. A skipped task's production directives are also never applied, so a later task that edits the same file can fail on its anchors. Proposed: return a `SKIP: <task>` message for each skipped task and still apply the production directives of tasks skipped only because their tests have no creation directive. | fixed in a1d2243 |
| 3 | Minor | skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py:_collect_base_defined_classes | Runs one `git show` subprocess for every stylesheet and template in the base tree whenever an orphan-class finding exists, which is slow on large repositories. Proposed: read all the files in one `git cat-file --batch` call. | fixed in a1d2243 |
| 4 | Minor | tests/test_ohk_docs_and_acceptance.py:Test_Ohk_Docs_And_Acceptance_Integration | The AR-03 test runs `bash scripts/verify.sh --full` itself, and the wrapper class calls it again, so every Integration results run executes the full suite twice. Proposed: have the wrapper call only the static-check path, or mark the direct test so it is collected once. | fixed in a1d2243 |

Raw output:

```text
Verdict: PASS
```
