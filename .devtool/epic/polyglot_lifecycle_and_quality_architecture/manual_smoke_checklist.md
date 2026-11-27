# Manual Smoke Walkthrough Checklist: Polyglot Lifecycle And Quality Architecture

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | TierBContractAdapter, PoolWorkspaceStrategy, TriageSurfaceRegistry, and TierCTaxonomy are initialized from the repository root | each of the 6 stack families resolves its exact file extensions, default Tier B policy, suffix-scoped SurfaceRuleSet, and Tier C policy |
| 2 | CLI / Workspace Root | check_diff_coverage.py is executed with --format auto, --min-coverage 75, --min-package-coverage 60, --diff-files, and --min-diff-coverage 80 | each invocation exits with code 0 |
| 3 | CLI / Workspace Root | scaffold_quality_manifest.py scaffolds check_quality.json, all 6 <stack>-quality.json manifests, and standards_catalog.json | every generated manifest defines all 4 profiles ("pr", "epic", "scheduled", "release"), unified capabilities ("anti_stub", "security", "security_deps", "pr_diff_audit", "workspace_audit", "pr_impact", "workspace_impact", "license"), "standards_catalog", dual-floor coverage referencing check_diff_coverage.py, and Android omits "cleanup" ("pkill -9 java") |
| 4 | `cargo fmt` | check_task_contract.py --design validates the task containing chained TIER-B commands covering cargo fmt --check, cargo clippy -D warnings, eslint, and tsc --noEmit | check_task_contract.py exits with code 0 |
| 5 | CLI / Workspace Root | manage_worker_pool.py creates and syncs slot 1 | target and node_modules in slot 1 are symlinks pointing to the main worktree |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
