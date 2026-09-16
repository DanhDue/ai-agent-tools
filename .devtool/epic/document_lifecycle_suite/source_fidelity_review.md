# Source Fidelity Review — Document Lifecycle Suite

> [!WARNING]
> This document deliberately quotes errors in order to name them as errors. Do not lift a
> sentence out of it without the surrounding verdict.

Two external methodologies enter the kit in this epic. Neither was in `docs/books/`, so both were
fetched from their primary sources before any skill text was written. This document records the
authors' own wording for every rule the skills will encode, and every point where this epic's own
drafts already diverged from it.

**Three divergences were found in drafts written before the sources were read.** All three read as
plausible. That is the whole argument for this gate.

---

## Source A — Diátaxis

**Author:** Daniele Procida. **Cited as:** [diataxis.fr](https://diataxis.fr/). The colophon asks
that the website itself be cited; APA and BibTeX metadata are available from the project's
repository.

### A1. The four types — the author's own orientations

> "Diátaxis identifies four distinct needs, and four corresponding forms of documentation —
> *tutorials*, *how-to guides*, *technical reference* and *explanation*."

| Type | Author's orientation | Author's wording |
|---|---|---|
| Tutorial | **learning-oriented** | "An *experience* that takes place under the guidance of a tutor." · "serves the user's *acquisition* of skills and knowledge — their study" |
| How-to guide | **goal-oriented** | "directions that guide the reader through a problem or towards a result" · "guides the user's *action*" |
| Reference | **information-oriented** | "technical descriptions of the machinery and how to operate it" · "propositional or theoretical knowledge that a user looks to in their work" |
| Explanation | **understanding-oriented** | "a discursive treatment of a subject, that permits *reflection*" |

### A2. The two axes — verbatim

The compass has exactly two axes, and the author's names for them are:

1. **action** ⟷ **cognition** — "informs action" / "informs cognition"
2. **acquisition** ⟷ **application** — "acquisition of skill" / "application of skill"

The decision table, verbatim:

| If the content… | …and serves the user's… | …then it must belong to… |
|---|---|---|
| informs action | acquisition of skill | a tutorial |
| informs action | application of skill | a how-to guide |
| informs cognition | application of skill | reference |
| informs cognition | acquisition of skill | explanation |

> [!CAUTION]
> **Divergence 1 — the axes were misnamed in this epic's design discussion.** They were described
> as "theory/practice × study/work". Those are **not** the author's axes; they are a common summary
> paraphrase. The author's axes are **action/cognition** and **acquisition/application**. The
> paraphrase loses the decision table above, which is the only part that actually sorts a document.

### A3. The anti-mixing rule is stated by the author for all four types

This is the rule the `doc-designer` skill exists to enforce, and it is not an inference — the author
states it separately for each type:

- **Tutorial:** "*A tutorial is not the place for explanation.*" · "Ruthlessly minimise explanation."
  · "Explanation distracts their attention from [doing], and blocks their learning."
- **How-to guide:** "no digression, explanation, teaching." · how-to guides "are wholly distinct
  from tutorials"; adding explanatory material "distracts both you and the user and dilutes the
  useful power of the guide." · "It's not the responsibility of a recipe to *teach* you how to make
  something."
- **Reference:** "It can be tempting to introduce instruction and explanation, simply because
  description can seem too inadequate to be useful… Instead, **link to** how-to guides, explanation
  and introductory tutorials." · "You will certainly not expect to find for example recipes or
  marketing claims mixed up with this information; that could be literally dangerous."
- **Explanation:** resist letting instruction or technical description "creep in"; their inclusion
  "interferes with the explanation itself, and removes them from view in the correct place."

**Note on how `doc-designer` must phrase the remedy.** The author's remedy is to **link** to the
other types, which presupposes they are separate documents. "Split into one document per mode, and
link between them" is faithful. "Delete the other material" is not — the author says it belongs
elsewhere, not that it is unwanted.

---

## Source B — Documenting Architecture Decisions

**Author:** Michael Nygard, 2011.

### B1. The sections, in the author's order

> **Title** — "short noun phrases"
> **Context** — "describes the forces at play", in language that is "value-neutral"
> **Decision** — "our response to these forces. It is stated in full sentences, with active voice"
> **Status** — "proposed", "accepted", "deprecated" or "superseded"
> **Consequences** — "describes the resulting context, after applying the decision"

> [!CAUTION]
> **Divergence 2 — the section order was wrong in this epic's drafts.** They gave
> "Title / Status / Context / Decision / Consequences". Nygard's order places **Status fourth**,
> after Decision. Minor, but there is no reason to restate an author's template in a different order
> while citing him for it.

### B2. Immutability — verbatim

> "If a decision is reversed, we will keep the old one around, but mark it as superseded."

> "It's still relevant to know that it *was* the decision, but is *no longer* the decision."

This confirms the rule as drafted: an accepted record is never edited; it is superseded.

### B3. Consequences — verbatim

> "All consequences should be listed here, not just the 'positive' ones. A particular decision may
> have positive, negative, and neutral consequences, but all of them affect the team and project in
> the future."

This confirms the rule as drafted, and sharpens it: the author names **three** categories —
positive, negative and **neutral** — not two.

### B4. Rejected alternatives — the author says nothing

> [!CAUTION]
> **Divergence 3 — and the serious one.** This epic's drafts listed "record the rejected
> alternatives and why they were rejected" as one of three rules **attributed to Nygard**. His 2011
> article contains no such statement. The practice is real and valuable, but it comes from later ADR
> templates — not from this source.
>
> The skill may still require it. What the skill may **not** do is attribute it to Nygard. Either
> cite the template it actually comes from, or present it as this kit's own addition and say so.

This is the failure mode the gate is built for: a rule that is good advice, plausibly attributed,
and simply not in the source. Nothing downstream could have caught it, because nothing downstream
reads the source.

---

## Regression guards

Each divergence above is now a pattern in `scripts/check_source_fidelity.py`, which
`scripts/verify.sh` runs at step 7. A guard that has never failed is unproven, so each was verified
by reintroducing the error and confirming the build breaks.

---

## Known limitation of the guard

`DISCLAIMER` excuses a match when a nearby line reads as a warning rather than a claim. That list is
deliberately loose, and one of its entries is the bare word **`wrong`** — which any sentence may use
for an unrelated reason, silencing a real check.

This was observed, not theorised. The section-order check
(`Title / Status / Context …`) did **not** fire on the ADR drafts, because the sentence immediately
after the wrong order happened to contain "…a way teams routinely get ADRs wrong". The error was
caught by reading the source, not by the guard.

**The obvious remedy does not work.** Removing `wrong` from `DISCLAIMER` was tried and rejected: two
legitimate warnings in `skills/lean-mvp-scoping/SKILL.md` rely on exactly that word, and dropping it
turns the Lean suite's own corrections into false failures.

So the limitation stands, and whoever adds the next source should know it:

- A check can be silenced by an unrelated nearby word. The guard catches **regressions**, not
  **first-time errors** — reading the source remains the only thing that finds those.
- When adding a check, verify it fires by reintroducing its error **in the file it is meant to
  protect**, not in a scratch file. A check proven only in isolation may be dead in place.
