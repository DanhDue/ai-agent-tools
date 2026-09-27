# Using d3nexus in Codex

The plugin ships the same skills in all runtimes. When a skill uses a Claude Code tool name,
perform the equivalent action using the tools exposed by the current Codex session.

| Skill instruction | Codex action |
|---|---|
| Invoke `Skill` or `d3nexus:<name>` | Select the installed d3nexus skill, then read its `SKILL.md` and follow it. Resolve supporting paths relative to that skill's directory. |
| `Read`, `Grep`, `Glob` | Use file tools or shell reads; prefer `rg` and `rg --files` for searches. |
| `Edit`, `Write` | Use the available patch or file editing tool. |
| `Bash` | Use the session's shell execution tool, respecting its permission boundaries. |
| `TodoWrite` | Use an available plan/task tool, or maintain a short progress checklist if none exists. |
| `Agent`, `Task`, parallel reviewers | Use subagents only when available and authorized. Otherwise perform independent steps sequentially and report the limitation. |

Codex reads the consuming project's `AGENTS.md`. Claude's `@file` import syntax and Antigravity's
Markdown `trigger: always_on` frontmatter are not substitutes for explicit reading instructions.
Read the project's rule files when present; otherwise read the plugin's
[critical rules](../../../rules/CRITICAL_RULES.md) and
[coding guidelines](../../../rules/coding-guidelines.md).

Keep `d3nexus:` cross-references in shared skill text. They identify the owning plugin; they do
not imply that Codex has Claude's slash-command or `Skill` API. Use the skill picker or name the
plugin and skill in a prompt when invocation syntax differs across Codex surfaces.

Follow the current host's instruction hierarchy and honor the user's authorized scope. References
to Antigravity's native planning artifact apply to that environment; do not invent unavailable
tools or configuration in Codex. Platform build tools, credentials, and devices requested by a
skill still need to exist in the consuming project.

After reinstalling or upgrading the plugin, start a new thread to load the updated skill inventory.
