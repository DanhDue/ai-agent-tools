---
name: decision-records
description: Use when a technical decision has been made and needs recording, or when a research spike has produced a recommendation. Writes Architecture Decision Records in Michael Nygard's format and spike reports that state what would refute them. Activate it whenever someone asks why a choice was made, when a decision is being reversed, or after any investigation whose output is a recommendation rather than code.
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

Grounded in **Michael Nygard, *Documenting Architecture Decisions* (2011)**. Quotations and their
sourcing:
[`source_fidelity_review.md`](../../.devtool/epic/document_lifecycle_suite/source_fidelity_review.md).

### The format, in the author's section order

| Section | What it holds |
|---|---|
| **Title** | "short noun phrases" |
| **Context** | "describes the forces at play", in language that is "value-neutral" |
| **Decision** | "our response to these forces… stated in full sentences, with active voice" |
| **Status** | `proposed`, `accepted`, `deprecated` or `superseded` |
| **Consequences** | "describes the resulting context, after applying the decision" |

Note where `Status` sits: **fourth, after Decision**. Reordering an author's template while citing
him for it is a small dishonesty that costs nothing to avoid.

### Rule 1 — one decision per record, immutable once accepted

Nygard: *"If a decision is reversed, we will keep the old one around, but mark it as superseded…
It's still relevant to know that it* was *the decision, but is* no longer *the decision."*

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

Nygard: *"All consequences should be listed here, not just the 'positive' ones. A particular decision
may have positive, negative, and neutral consequences, but all of them affect the team and project
in the future."*

Three categories, not two. A record whose consequences are all benefits is a sales pitch, and it
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

## Red Flags

- Editing a record whose status is `accepted`. Supersede it instead.
- Reusing or renumbering an existing number.
- Consequences that are entirely positive.
- Citing Nygard for the rejected-alternatives rule.
- Restating the section order with `Status` in second place.
- A spike report whose "what would change this conclusion" section is empty or hedged.
- Opening `doc-lifecycle` gates around a single record.
