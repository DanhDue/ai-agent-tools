---
name: brainstorming
description: "Asks which kind of work a request is for, then routes to the matching inception skill. Use it whenever someone asks to brainstorm, explore or design something without making clear whether the deliverable is code or a document. When the deliverable is already known, invoke dev-brainstorming or doc-brainstorming directly and skip this skill."
---

# Brainstorming Router

This skill holds one question and two destinations. It does no exploring, asks no clarifying
questions, and produces no design — those belong to the variant it routes to.

## Ask first

Ask this before reading files, exploring the codebase, or anything else. Ask it in the user's own
language:

> Bạn muốn brainstorming để phát triển ý tưởng, làm tài liệu, hay thực hiện phát triển tính năng
> (coding) luôn?

> Do you want to brainstorm to develop an idea, to produce a document, or to build a feature
> (coding)?

## Then route

| Answer | Invoke |
|---|---|
| Develop an idea — *phát triển ý tưởng* | `d3nexus:doc-brainstorming` |
| Produce a document — *làm tài liệu* | `d3nexus:doc-brainstorming` |
| Build a feature, coding — *phát triển tính năng* | `d3nexus:dev-brainstorming` |

Three answers, two destinations. Developing an idea in this kit produces a document, so it takes
the same path.

## Do not guess

**There is no default.** If the answer is unclear, missing, or maps to none of the three, ask again.

Do not infer the branch from how the request is worded. A vague request is more often unclear *code*
work than it is document work, so guessing fails in the direction that costs most: a feature sent
down the document path never meets the test suite.

The question is about **what will exist when the work is finished**, not about how specific the
request was.

## When to skip this skill

Skip it whenever the branch is already known:

- `dev-lifecycle` Stage 1 invokes `dev-brainstorming` directly.
- `doc-lifecycle` Stage 0 invokes `doc-brainstorming` directly.
- A user who names a variant gets that variant, with no question asked.

Once you have routed, this skill is finished. Do not re-enter it later in the session; if a variant
turns out to be the wrong one, its own correction exit handles that.

## Downstream Document Standards

Both downstream destinations (`dev-brainstorming` and `doc-brainstorming`) enforce strict **Markdown & Diagram Lint Standards** on all generated deliverables:
- **Markdown Lint**: Single H1 title, sequential headings, language-tagged code blocks, formatting hygiene.
- **Mermaid Standards**: Modern `flowchart TD/LR` (NEVER legacy `graph TD/LR`), double-quoted node labels with special characters/parentheses/colons, clean alphanumeric IDs, and no trailing semicolons.
- **Graphviz (DOT) Standards**: Semantic node shapes, statement semicolons, and double-quoted labels.
