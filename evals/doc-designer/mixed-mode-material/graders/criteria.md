# Rubric — `mixed-mode-material`

You are grading two replies to the requester's message. You have not seen either author's reference
material, and you should not assume either had any.

Grade **each reply independently**, **each criterion PASS or FAIL**, and **quote the reply** in your
one-sentence justification. If a reply is ambiguous on a criterion, mark FAIL and quote the ambiguity
— someone acting on the reply has to be able to tell what was decided.

The standard below is **Daniele Procida's Diátaxis framework** (diataxis.fr). The criteria test
whether each reply is *right*, not whether it echoes any particular vocabulary. **A reply that never
uses the words "tutorial", "reference" or "explanation" can still pass every criterion.**

---

### C1 — Did the reply refuse the one-page request and propose separate documents?

The three needs serve three different reader situations: learning to do a first deploy, looking up a
flag mid-task, and understanding a past architectural choice. Procida's framework holds that these
belong in separate documents.

> "It can be tempting to introduce instruction and explanation, simply because description can seem
> too inadequate to be useful… Instead, **link to** how-to guides, explanation and introductory
> tutorials."

**PASS** if the reply proposes more than one document, each covering one of the three needs.
**FAIL** if it delivers or outlines a single blended page, or if it splits merely into headed
sections of one document while still calling it one page.

*A reply that proposes two documents rather than three passes if the grouping is justified — the
criterion is that it did not blend everything.*

---

### C2 — Did the reply distinguish the three needs by what the reader is doing?

Procida separates content that **informs action** from content that **informs cognition**, and
content serving **acquisition of skill** from content serving **application of skill**.

**PASS** if the reply explicitly distinguishes the first-deploy walkthrough (someone learning by
doing) from the flag list (someone looking something up mid-task) from the blue-green rationale
(someone wanting to understand a decision), and this distinction visibly drives its structure.
**FAIL** if the three are treated as three topics of equal kind, differing only in subject matter.

---

### C3 — Did the reply keep the blue-green rationale out of the step-by-step walkthrough?

> "*A tutorial is not the place for explanation.*" · "Ruthlessly minimise explanation."
> "Explanation distracts their attention from [doing], and blocks their learning."

**PASS** if the walkthrough for a new joiner's first deploy contains no discussion of why blue-green
was chosen, and the reply either links to it or places it elsewhere. **FAIL** if the rationale is
woven into the walkthrough, or if a proposed single document interleaves them.

---

### C4 — Did the reply answer the discoverability objection?

The requester's objection is specific and based on experience: a previous four-way split left people
unable to find anything. Procida's remedy for out-of-type material is to **link** to it, which
presupposes the documents reference each other.

**PASS** if the reply addresses findability — cross-links, a single entry point, an index, naming
conventions, or an equivalent concrete mechanism. **FAIL** if it proposes a split and says nothing
about how anyone will navigate it, or if it dismisses the objection.

---

### C5 — Did the reply establish who the reader is before proposing a structure?

**PASS** if the reply identifies the different readers — a day-two joiner, an engineer mid-deploy, an
architecture-review participant — or asks about them, before committing to a shape. **FAIL** if it
proposes a structure with no reference to who reads what.

*This criterion is one a competent writer may well pass without any framework. It is included
deliberately: a rubric the baseline scores zero on measures the rubric's difficulty, not the skill's
value.*

---

## Notable, unscored

Record but do not score:

- Whether the reply preserves the **silent-wrong-target footgun** (skipping `shipit target` deploys
  to the previous target; it has already bitten three people). Procida does not settle where a hazard
  belongs, so this is not a criterion — but a reply that loses it entirely has dropped the most
  consequential fact in the prompt.
- Any reply that asks clarifying questions instead of answering. Note it; grade the substance of
  whatever it did commit to.
