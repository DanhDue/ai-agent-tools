# Manual Smoke Walkthrough Checklist: Observer Hardening 2026 11

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `git repository` | "sync_task_status.py promote iso_epic" executes inside ".worktrees/iso_epic" | the command exits 0 and prints "Promoted" |
| 2 | CLI / Workspace Root | "package_epic.py <epic_dir> --revise --reason 'Rebased onto base'" executes | check_epic_readiness.py runs with "--reanchoring" and exits 0 |
| 3 | `Python repository` | "bootstrap_worktree.sh" runs against the worktree with a recording fake "uv" binary on PATH verify_polyglot_registry.py executes a capability command starting with ["uv", "run", ...] | the invoked uv command includes "sync", "--all-extras", and "--group", "dev" the child process receives "UV_NO_SYNC=1" in its environment |
| 4 | `git repository` | "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" executes ".well-known/portal.html" is modified without bumping "?v=1" | "_get_base_file_content" resolves both "main:./static/search.html" and "main:./.well-known/portal.html" cleanly without stripping leading dots and rejects "../outside.html" "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" returns status "FAIL" with a "cache_bust" finding on ".well-known/portal.html" |
| 5 | http://127.0.0.1:8000 | "run_external_review.py triage --epic-dir <epic_dir>" executes "generate_smoke_checklist.py" parses a Playwright browser BDD scenario without an explicit CLI command | Proposed action pre-fills "deferred: out-of-scope epic doc (§4.4)" for both Minor rows the generated checklist target is the inferred web URL or "Web Preview UI" rather than "CLI / Workspace Root" |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
