# ai-agent-tools — working on the kit itself

This repository is the shared agent kit for mobile projects. It is consumed as a plugin by
Antigravity and Claude Code; see [README.md](README.md) for installation.

## Rules

@rules/CRITICAL_RULES.md
@rules/coding-guidelines.md

## When editing skills

- `skills/<name>/SKILL.md` frontmatter is exactly `name` + `description`. No other keys —
  an unrecognised key risks a silent frontmatter parse failure.
- `description` drives activation in both runtimes. State *what* the skill does and *when*
  to use it, in third person.
- Keep `SKILL.md` concise; both runtimes load skills by progressive disclosure. Bulk material
  belongs in the skill's `references/`, `scripts/`, `resources/` or `examples/`.
- Cross-references between skills in this kit use the `d3nexus:` namespace.
- Changing a skill affects every project on every machine that has the plugin installed.
  Verify before publishing: internal links resolve, ToC anchors match headings, and any
  mermaid diagram renders.

## Verifying before a release

```bash
scripts/verify.sh
```
