# {{PROJECT_NAME}} — Agent Entry Point

{{ONE_LINE_DESCRIPTION}}

Agent skills and rules come from the **d3nexus** plugin
(https://github.com/DanhDue/ai-agent-tools) — installed per machine, not vendored here.
See that repo's README for installation.

## Rules

@.agents/rules/CRITICAL_RULES.md
@.agents/rules/coding-guidelines.md

> The `@` lines are Claude Code imports. Antigravity discovers `.agents/rules/*.md` natively,
> so rules load in both runtimes without being duplicated. If this project does not vendor
> `.agents/rules/`, delete these two lines — the plugin supplies the rules instead.

## Orchestration

| Situation | Start here |
|---|---|
| Epic-scale work (multiple components, needs HLD + task breakdown) | `epic-lifecycle` skill — owns the 4 stages and 4 approval gates |
| Any new feature, component, or behaviour change | `brainstorming` skill |
| A bug, test failure, or unexpected behaviour | `systematic-debugging` skill |
| Finished a workflow or skill | `quality_check` skill (mandatory — see CRITICAL_RULES) |

## Build Environment

{{BUILD_INSTRUCTIONS}}

## CLI

{{CLI_COMMANDS}}

## Architecture

{{ARCHITECTURE_NOTES}}
