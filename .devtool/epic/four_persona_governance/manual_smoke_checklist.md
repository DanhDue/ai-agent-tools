# Manual Smoke Walkthrough Checklist: Four Persona Governance

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | CLI / Workspace Root | "resolve_persona" runs for "ai_architect_reviewer", "orchestrator" and "programmer" with no CLI overrides | "ai_architect_reviewer" resolves to alias "claude-opus", cli "claude", model_id "opus", effort "high" with sources["model"] == "global" |
| 2 | CLI / Workspace Root | "dev_config.py models --json" runs "dev_config.py models add gpt-next --cli codex --id gpt-7 --efforts medium,high --scope global" and "dev_config.py set programmer gpt-next high" run | the JSON lists aliases "argon", "hydrogen", "claude-opus", "claude-sonnet", "codex-gpt" and "kiro-opus" both exit 0 and "dev_config.py resolve programmer --format json" prints "model_id": "gpt-7" and "cli": "codex" |
| 3 | CLI / Workspace Root | "build_dispatch_argv" runs for (hydrogen, "write"), (argon, "read-only"), (claude-custom, "read-only"), (codex-gpt, "write") and (kiro-opus, "write") | the hydrogen argv equals ["agy", "--model", "gemini-4-hydrogen-xhigh", "--effort", "xhigh", "--mode", "auto"] |
| 4 | `git repository` | "resume_context.py --checkpoint subagent_returned --epic fpg_epic --next 'dispatch task_03 reviewer'" runs | ".devtool/state/fpg-epic.heartbeat.json" has checkpoint["event"] == "subagent_returned", checkpoint["next_step"] == "dispatch task_03 reviewer" and checkpoint["turns_since_checkpoint"] == 0 |
| 5 | CLI / Workspace Root | "--emit-prompt brief --brief-role task-reviewer", "--emit-prompt brief --brief-role fix-planner" and "--emit-prompt implement" run for "fpg_epic" | the task-reviewer and fix-planner briefs name "Role 2.1 AI Architect & Reviewer" and the argv "agy --model gemini-4-argon-high --effort high" |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
