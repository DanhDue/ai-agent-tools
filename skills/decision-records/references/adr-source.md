# Architecture Decision Records — the author's own wording

Source: **Michael Nygard, *Documenting Architecture Decisions*, 2011.**

This file holds the **evidence**. The rules it supports live in [`../SKILL.md`](../SKILL.md) — a rule
kept only here is a rule that may not be read.

Sourcing, and the three errors found in this kit's own drafts before the source was read:
[`source_fidelity_review.md`](../../../.devtool/epic/document_lifecycle_suite/source_fidelity_review.md).

## The sections

| Section | Nygard's wording |
|---|---|
| **Title** | "short noun phrases" |
| **Context** | "describes the forces at play", in language that is "value-neutral" |
| **Decision** | "our response to these forces. It is stated in full sentences, with active voice" |
| **Status** | "proposed", "accepted", "deprecated" or "superseded" |
| **Consequences** | "describes the resulting context, after applying the decision" |

Status is **fourth**, after Decision.

## Immutability

> "If a decision is reversed, we will keep the old one around, but mark it as superseded."

> "It's still relevant to know that it *was* the decision, but is *no longer* the decision."

## Consequences

> "All consequences should be listed here, not just the 'positive' ones. A particular decision may
> have positive, negative, and neutral consequences, but all of them affect the team and project in
> the future."

Three categories, not two.

## What this source does **not** say

> [!CAUTION]
> Nygard's article contains **no statement about recording rejected alternatives.** That practice is
> real and worth keeping, but it comes from later ADR templates. This kit requires it as its own
> addition and must never cite Nygard for it.
>
> An earlier draft of this kit listed it as one of three rules attributed to him. It read as
> authoritative and was simply not in the source — which is the failure mode this file exists to
> prevent.
