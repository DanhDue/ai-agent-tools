---
name: decision-records
description: Writes Architecture Decision Records in Michael Nygard's format, and spike reports that state what would refute them. Use it when a technical decision needs recording, when one is being reversed, or after an investigation that produced a recommendation.
---

# Decision Records

Two artefacts, one purpose: making a decision legible to whoever inherits it.

- **Architecture Decision Record (ADR)** — a decision that has been made.
- **Spike report** — an investigation that produced a recommendation.

**Announce at start:** "I'm using the decision-records skill to record `<decision>`."

## When to Use

- A choice was made that someone will later ask about — a library, a boundary, a protocol, a
  trade-off accepted knowingly.
- A previous decision is being reversed. That needs a **new** record, never an edit to the old one.
- A spike, investigation or comparison has finished.

## When NOT to Use `doc-lifecycle` for This

A single record sits **below** `doc-lifecycle`'s threshold. Invoke this skill directly, write the
record, commit it. Three gates around one file nobody would reject is friction with no benefit.

Reach for `doc-lifecycle` only when a batch of records is being produced or backfilled as a single
piece of work.

## Architecture Decision Records

Grounded in **Michael Nygard, *Documenting Architecture Decisions* (2011)**. His wording for every
rule below: [`references/adr-source.md`](references/adr-source.md).

### The format, in the author's section order

| Section | What it holds |
|---|---|
| **Title** | A short noun phrase |
| **Context** | The forces at play, described in value-neutral language |
| **Decision** | The response to those forces, in full sentences and active voice |
| **Status** | `proposed`, `accepted`, `deprecated` or `superseded` |
| **Consequences** | The resulting context, after applying the decision |

Note where `Status` sits: **fourth, after Decision**. Reordering an author's template while citing
him for it is a small dishonesty that costs nothing to avoid.

### Rule 1 — one decision per record, immutable once accepted

An accepted record is **never edited**. A reversal is a new record that supersedes it by number.
This is the whole difference between an ADR and a wiki page: a wiki page always agrees with the
present, which makes it worthless at exactly the moment someone needs to know what was believed at
the time.

Legal transitions:

| From | To | |
|---|---|---|
| `proposed` | `accepted` | allowed |
| `proposed` | `rejected` | allowed |
| `accepted` | `deprecated` | allowed |
| `accepted` | `superseded` | allowed, by a new record that names it |
| `accepted` | `proposed` | **refused** |
| `superseded` | `accepted` | **refused** — write a new record instead |

### Rule 2 — all consequences, not just the good ones

Three categories — positive, negative **and neutral** — not two. A record whose consequences are all benefits is a sales pitch, and it
will be read as one.

### Rule 3 — the alternatives that lost, and why

> [!IMPORTANT]
> **This rule is this kit's own addition — it is not Nygard's**, and his 2011 article does not
> mention it. It comes from later ADR templates. Never cite him for it.

With that attribution stated, the rule stands: name what was considered and rejected, and why. That
is precisely what nobody remembers six months later, and it is why teams reverse decisions that were
correct — the reasons against the alternative are invisible, so the alternative looks free.

### Location and numbering

`docs/adr/NNNN-kebab-case-title.md`, zero-padded, sequential, **never renumbered**. A number is an
address: other records cite it, and renumbering breaks every citation silently.

## Spike Reports

For an investigation rather than a decision:

| Section | What it holds |
|---|---|
| **Question** | What was being decided, in one sentence |
| **Method** | What was actually done — measured, read, prototyped |
| **Findings** | What was observed, separated from what it implies |
| **Recommendation** | The proposed course of action |
| **Confidence** | High / medium / low, with the reason |
| **What would change this conclusion** | **Mandatory.** Name the observation that would overturn it |

The last field is what separates a report from an opinion. A recommendation that no evidence could
overturn is not a finding — it is a preference, and it should be labelled as one.

## Markdown & Diagram Standards

All ADRs and spike reports MUST adhere to markdown lint and modern diagram standards:
- **Markdown Lint**: Single H1 title, no skipped heading levels, space after `#`, no trailing punctuation in headings, mandatory language tags on all code fences, and clean formatting hygiene.
- **Mermaid Standards**: Use `flowchart TD/LR` (NEVER legacy `graph TD/LR`), double-quote node labels with special characters, parentheses `()`, brackets `[]`, braces `{}`, colons `:`, slashes `/`, ampersands `&`, use alphanumeric IDs, and avoid trailing semicolons.
- **Graphviz (DOT) Standards**: Follow semantic shapes (`diamond` for decisions `?`, `box` for actions, `plaintext` for commands, `ellipse` for states, `octagon` for warnings, `doublecircle` for start/complete) and statement semicolons.

## Red Flags

- Editing a record whose status is `accepted`. Supersede it instead.
- Reusing or renumbering an existing number.
- Consequences that are entirely positive.
- Citing Nygard for the rejected-alternatives rule.
- Restating the section order with `Status` in second place.
- A spike report whose "what would change this conclusion" section is empty or hedged.
- Opening `doc-lifecycle` gates around a single record.
- Violating markdown lint standards or using legacy Mermaid syntax (`graph TD`/`graph LR`).
