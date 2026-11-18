# Manual Smoke Walkthrough Checklist: Review Cap And Risk Triage

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | "resolve_task_review_limits" and "dev_config.py status --json" run against the project root global ".d3nexus/personas.json" sets {"schema_version": 1, "max_task_review_passes": 3, "max_fix_passes": 2} and project ".agents/config/personas.json" sets {"schema_version": 1, "max_fix_passes": 1} | "resolve_task_review_limits" returns "(2, 1)" matching "scripts/personas.default.json" and ".agents/config/personas.json" "resolve_task_review_limits" returns "(3, 1)" reflecting kit -> global -> project precedence |
| 2 | `git repository` | "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic" runs for Pass 1 "resume_context.py --emit-prompt brief --brief-role task-reviewer --epic trc_epic --review-pass 2 --pass1-tree-sha 4b825dc642cb --blockers-file pass1_blockers.json" runs | stdout exits 0, names "Role 2.1 AI Architect & Reviewer", includes '"verdict": "APPROVED\|CHANGES_REQUESTED"', defines "BLOCKER" versus "NON_BLOCKING_OBSERVATION", and omits ".vi.md" stdout exits 0, includes "git diff 4b825dc642cb", embeds "BLK-1", forbids introducing new non-regression findings in Pass 2, and omits ".vi.md" |
| 3 | CLI / Workspace Root | "manage_worker_pool.py triage-fix trc_demo --slot 1 --task task_01" runs "manage_worker_pool.py finalize-slot trc_demo --slot 1 --task task_01 --mode tier2-short-circuit --risk-level LOW --rationale 'Directly resolves BLK-1 with zero side effects'" runs | exit code is 0 and stdout JSON has "tier1_status" == "ELIGIBLE_FOR_SHORT_CIRCUIT", "triggers" == [], "non_test_changed_lines" == 8, and a non-empty "bounded_diff" exit code is 0, "task_01" status in ".devtool/features/" is synced to "done", the slot commit is merged into "epic/trc-demo", ".devtool/epic/trc_demo/review_audit_notes.jsonl" in the main epic worktree contains one entry with "mode": "tier2-short-circuit" and "risk_level": "LOW", and slot 1 heartbeat resets to "status": "idle" with "review_passes_used": 0 and "fix_passes_used": 0 |
| 4 | `git repository` | Task 1's Pass 1 reviewer returns {"task_id": "task_01", "pass": 1, "verdict": "APPROVED", "head_sha": "<sha1>", "done_gate": "PASS", "blockers": [], "observations": [{"id": "OBS-1", "file": "src/a.py", "summary": "Style nit"}]} | Task 1 finalizes after exactly 1 review pass and 0 fix passes with "OBS-1" recorded and committed on the epic branch in "review_audit_notes.jsonl" |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
