# Manual Smoke Walkthrough Checklist: Unified Review Config

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | persona_config.resolve_review_limits and persona_config.resolve_review_config are called | max_task_review_passes equals 2, max_fix_passes equals 1, max_principal_review_passes equals 3, and max_cross_model_review_passes equals 3 with source "kit" |
| 2 | `limits --principal-review 2 --cross-model-review 4 --scope global` | dev_config.py runs "limits --principal-review 2 --cross-model-review 4 --scope global" followed by "limits --task-review 3 --fix 0 --scope project" | "$REAL_HOME/.d3nexus/personas.json" persists max_principal_review_passes=2 and max_cross_model_review_passes=4 without writing max_task_review_passes or max_fix_passes |
| 3 | http://127.0.0.1:11434 | dev_config.py runs "review priority codex,claude,kiro,agy --scope global", "review set agy --model gemini-4-carbon-high --effort high --scope global", "review set ollama --model qwen2.5-coder:32b --host http://127.0.0.1:11434 --scope project", and "review thresholds --5h 0.25 --kiro-credits 25.0 --scope global" | "dev_config.py review status --json" reports provider_priority ["codex", "claude", "kiro", "agy"] with source "global" |
| 4 | CLI / Workspace Root | run_external_review.resolve_effective_max_rounds runs for kind "principal" and kind "code" with cli_max_rounds=None | kind "principal" resolves to 2 rounds and kind "code" resolves to 4 rounds |
| 5 | CLI / Workspace Root | LifecycleRunner initializes with RunnerConfig leaving max_review_rounds, max_principal_review_rounds, max_cross_model_review_rounds, and provider_priority unset | _resolve_external_review_bounds("principal") returns 2 and _resolve_external_review_bounds("code") returns 4 |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
