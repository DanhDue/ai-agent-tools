# 0001. A separate quality gate for documentation

## Context

`rules/CRITICAL_RULES.md` mandates `@quality_check` after every workflow. That skill is 512 lines of
platform-specific tooling — Melos, Gradle, Tuist — and release 1.1.1 added Tier C2, which compiles a
native binary. None of it applies to a Markdown deliverable.

The mandate was therefore unsatisfiable for documentation work. An instruction that cannot be obeyed
does not simply fail; it teaches that rules are negotiable, which costs more than the missing check.

Three options were considered:

1. **Branch `quality_check` on a `Kind` field.** One entry point; document work takes a different
   path through the same skill.
2. **A standalone `doc_quality_check` skill**, with `quality_check` carrying a short redirect.
3. **A standalone skill with no redirect**, routing owned by the lifecycles and by the rule file.

## Decision

We adopt option 3. `doc_quality_check` is a standalone skill. `skills/quality_check/SKILL.md` is not
modified at all, and neither skill references the other. Routing lives in `doc-lifecycle`, which
already owns sequence and gates, and in `rules/CRITICAL_RULES.md`, which is amended to make the
mandated gate depend on the kind of work.

The refusal rule is mechanical, not advisory: if a change touches a file that ships in the build,
`doc_quality_check` aborts and names the files.

## Status

`accepted`

## Consequences

**Positive.** `quality_check` gates every merge in every project and changed 57 lines in the release
immediately prior; not touching it puts its regression risk at zero. Both runtimes load skills
lazily, so a document work item no longer loads three platform matrices it will never use. The two
gates can be maintained independently, because they share no file and neither invokes the other.

**Negative.** There are now two doors rather than one, and choosing wrongly is possible. The document
path is cheaper — it skips the 3-tier suite, the four semantic audits and the native build gate —
which makes mislabelling code as documentation an attractive shortcut. That is an incentive problem,
not a comprehension problem, and no wording fixes it; the mechanical refusal rule is the mitigation,
with the human's choice of lifecycle as a second, independent layer.

`rules/CRITICAL_RULES.md` was amended, and it loads into every session on every project. An earlier
draft of the design spec listed not editing that file as a goal. That goal conflicted with the same
spec's own observation that the rule was unsatisfiable for documents; the conflict is resolved here
in favour of making the rule correct.

**Neutral.** The kit gains a skill, taking the count from 50 to 51. `Kind: document` remains in the
document overview's metadata, but as a record of what the work item is rather than as a dispatch key.

## Rejected alternatives

**Option 1 — branch inside `quality_check`.** Rejected because it puts new logic into the single file
that guards every merge in every project, and because it forces a document work item to load 512
lines of mobile build tooling to verify a runbook.

**Option 2 — standalone skill with a redirect in `quality_check`.** Rejected because the redirect is
itself the coupling the split was meant to remove. A pointer from one gate to the other means neither
can be changed without reading both.

> The rejected-alternatives section is this repository's own convention, not part of Nygard's 2011
> format.
