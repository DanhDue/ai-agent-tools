# Context — `mixed-mode-material`

**Skill under test**: `doc-designer`
**Rule at stake**: material spanning more than one Diátaxis type is split into more than one
document, one per type, linked to each other — never blended into one
**Expected delta**: High

---

## Why this case

The three needs in the prompt map cleanly onto three different Diátaxis types, and the requester has
no idea that is true:

| What they asked for | Type | Procida's axes |
|---|---|---|
| Day-two engineer completes a staging deploy unaided | **tutorial** | informs action · acquisition of skill |
| The complete list of 31 flags with defaults | **reference** | informs cognition · application of skill |
| Why blue-green rather than rolling | **explanation** | informs cognition · acquisition of skill |

**The objection to splitting is correct, not a strawman.** Splitting documentation really does hurt
discoverability, and the requester has lived through a bad split that nobody could navigate. A reply
that splits the material has to answer that objection rather than ignore it — Procida's own remedy is
to *link*, which is exactly what the failed four-page split presumably lacked.

It is also socially loaded: *"Please keep it to one page… I'm serious"*, followed by a reason that
sounds like hard-won experience. Complying is the friendly answer. A rule that only holds when it is
convenient is not a rule.

## Domain novelty

Kubernetes deploy tooling appears nowhere in `skills/`. This repository's own documentation subject
matter is mobile app development, so an agent cannot pattern-match the answer from a nearby example.

## The quieter trap

Need 1 contains a **safety footgun** — skipping `shipit target` silently deploys to the previous
target, which has already bitten three people. A tutorial is not the place to document a hazard
exhaustively, but a reply that drops it entirely has lost the most important thing in the prompt.
Scored as "notable, unscored" rather than as a criterion, because Procida does not settle it.

---

## Arm A — with skill

Role framing:

> You are a technical writer helping an engineering team document an internal tool.

Files to read first, in this order:

- `skills/doc-designer/SKILL.md`
- `skills/doc-designer/references/diataxis-source.md`

Then deliver `prompt.md` verbatim.

## Arm B — baseline

Role framing — **identical**:

> You are a technical writer helping an engineering team document an internal tool.

No files. No mention that documentation frameworks, types or methodologies exist. Then deliver
`prompt.md` verbatim.

## Both arms

Ask for the **actual reply** they would send, not a description of what they would do. Do not tell
either arm it is being evaluated or compared.

## Fixture state

None. The prompt supplies everything; no files need to exist on disk.
