# {{PROJECT_NAME}} — Agent Entry Point

{{ONE_LINE_DESCRIPTION}}

Agent skills and rules come from the **d3nexus** plugin
(https://github.com/DanhDue/ai-agent-tools) — installed per machine, not vendored here.
See that repo's README for installation.

## Rules

@.agents/rules/CRITICAL_RULES.md
@.agents/rules/coding-guidelines.md

Before starting work, read `CRITICAL_RULES.md` and `coding-guidelines.md`. Use this project's
`.agents/rules/` files if present; otherwise locate the installed `d3nexus` plugin from one of
its skill paths and read `rules/CRITICAL_RULES.md` and `rules/coding-guidelines.md` at that plugin's
root. If the plugin cannot be found, report the missing installation rather than assuming the
rules loaded.

The `@` lines above are Claude Code imports. Antigravity discovers `.agents/rules/*.md` natively.
Codex must follow the explicit reading instruction above. If this project does not vendor
`.agents/rules/`, delete the two import lines and use the installed plugin's files.

When using Codex, select the installed d3nexus skill and read its `SKILL.md`; instructions that
mention Claude's `Skill` tool mean loading that skill through the available Codex tools.

## Orchestration

| Situation | Start here |
|---|---|
| Epic-scale work (multiple components, needs HLD + task breakdown) | `dev-lifecycle` skill — owns the 4 stages and 4 approval gates |
| Any new feature, component, or behaviour change | `dev-brainstorming` skill |
| A bug, test failure, or unexpected behaviour | `systematic-debugging` skill |
| Finished a workflow or skill | `quality_check` skill (mandatory — see CRITICAL_RULES) |

## Build Environment

{{BUILD_INSTRUCTIONS}}

## CLI

{{CLI_COMMANDS}}

## Architecture

{{ARCHITECTURE_NOTES}}
