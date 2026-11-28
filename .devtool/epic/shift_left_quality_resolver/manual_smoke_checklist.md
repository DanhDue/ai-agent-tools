# Manual Smoke Walkthrough Checklist: Shift Left Quality Resolver

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | manifests declaring optional "test_routing", "coverage.package_floors", Flutter "architecture", and Rust/Web/Python "cache_enable" and "cache_purge" are validated across profiles ("pr", "epic", "scheduled", "release") | all 6 runtime validators return status "PASS" with 0 findings |
| 2 | CLI / Workspace Root | scaffold_quality_manifest.py runs and check_diff_coverage.py evaluates LCOV/Cobertura reports with "--package-floors .agents/quality/coverage_floors.json" | every generated stack manifest and "web-quality.template.json" has 0 duplicate audit or impact invocations per profile ("pr_diff_audit" and "pr_impact" in "pr" only; "workspace_audit" and "workspace_impact" in "epic", "scheduled", and "release") |
| 3 | `bin/d3nexus resolve-quality --files src/lyrics_sync/align/ctc.py src/preview/static/align-studio.js --base-ref develop` | resolve_quality_plan() executes in-process and "bin/d3nexus resolve-quality --files src/lyrics_sync/align/ctc.py src/preview/static/align-studio.js --base-ref develop" executes via CLI | in-process resolve_quality_plan() completes in under 0.10 seconds (best of 3 runs) and the CLI subprocess exits 0 in under 1.0 second printing between 5 and 10 non-empty lines |
| 4 | `web-quality-check` | check_task_contract.py runs "--design" on epic tasks and "--check-plan" on a standalone plan whose commands scope ruff and mypy to Allowed ".py" files, expand "$D3NEXUS_KIT/skills/.../check_vanilla_js.py", include a "tests/js/*.test.mjs" unit test, and include referencing "?v=" HTML templates | both "--design" and "--check-plan" exit 0 with "Result: 0 problems — PASS" |
| 5 | `scripts/verify.sh` | clean-shell Pre-Flight commands, check_document.py --require-toc, UTF-8 byte/word cap checks, and 5-repo ecosystem manifest validations (via optional SLQR_ECOSYSTEM_ROOT or synthetic 5-repo polyglot fixtures) execute | "skills/dev-designer/SKILL.md" stays <= 22528 UTF-8 bytes, retired script names ("verify_importlinter_coverage.py", "pre_review_self_probe.py", "verify_bdd_coverage.py") do not appear in "dev-designer", all discovered ecosystem profiles return "PASS" with zero personal-path leaks in tracked files, and embedded CLI commands exit 0 in a clean env shell |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
