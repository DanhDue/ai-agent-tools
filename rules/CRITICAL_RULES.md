# Critical Rules

> [!CRITICAL]
> These rules are MANDATORY and must be applied by all AI Agents in every interaction. Failure to follow these rules is a violation of the coding standard.


> [!IMPORTANT]
> After completing any workflow or skill, you **MUST** use the `@quality_check` skill to run quality checks and fix any issues that arise. This is critical to maintain the quality of the project.
> 
> See: [Quality Check Skill](../skills/quality_check/SKILL.md)

## Commit Message Format

Every commit — written by a skill or by hand — uses a bracketed scope, a one-line title, and a
bullet list of the subtasks actually done:

```
[EPIC_NAME] Task title

- subtask title 01
- subtask title 02
```

- **`[SCOPE]`** is the epic name for epic work (`[LOGGING_REFACTOR]`), otherwise the area touched
  (`[TOOLS]`, `[SETTINGS]`). Uppercase, in brackets, always present.
- **Title** is one line, imperative, no trailing period.
- **Body** lists the subtasks or changes this commit actually contains, one bullet each. Omit the
  body entirely when the commit does exactly one thing.

Write it with two `-m` flags — the first becomes the title, the second the body:

```bash
git commit -m "[EPIC_NAME] Task title" -m "- subtask title 01
- subtask title 02"
```

> [!CAUTION]
> **Never append trailer lines.** No `Co-Authored-By:`, no `Generated with`, no tool attribution
> of any kind. The commit ends with the last bullet.
