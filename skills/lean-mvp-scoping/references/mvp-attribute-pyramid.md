# The MVP Attribute Pyramid

Reference for [lean-mvp-scoping](../SKILL.md), step 6. Olsen's Figure 7.1, *Building an MVP* — what
"minimum" is allowed to mean, and what it is not.

> [!IMPORTANT]
> **Attribution.** Olsen writes: *"I've adapted this figure from one created by talented UX designer
> **Jussi Pasanen** of Volkside, who gives his acknowledgements to **Aarron Walter, Ben Tollady, and
> Ben Rowe**."*
>
> The **cupcake / birthday cake / wedding cake** metaphor is **Brandon Schauer's** and does **not**
> appear in *The Lean Product Playbook*. It makes a similar point and it is a good mnemonic — but do
> not attribute it to Olsen, and do not name this pyramid after it.

---

## Table of Contents

1. [The misreading this corrects](#the-misreading-this-corrects)
2. [The four attributes](#the-four-attributes)
3. [Vertical versus horizontal cuts](#vertical-versus-horizontal-cuts)
4. [Applying it at step 4](#applying-it-at-step-4)
5. [MVP versus MVP test](#mvp-versus-mvp-test)

---

## The misreading this corrects

> "Many people misinterpret the term MVP by placing too much emphasis on the word **minimum**. They
> use this as an excuse to build a partial MVP that has too little functionality to be considered
> viable by a customer. Others use 'minimum' to rationalize a shoddy user experience or a buggy
> product. While it's true that an MVP is deliberately limited in scope relative to your entire value
> proposition, **what you release to customers has to be above a certain bar in order to create value
> for them**."

Two distinct failures hide behind the same word:

1. **Too little functionality** — so thin that no customer would call it a product.
2. **Shoddy quality** — enough features, but unreliable, unusable, or joyless.

The pyramid addresses the second, and the composition rule in
[The MVP Candidate Grid](mvp-candidate-grid.md) addresses the first. Both have to hold.

---

## The four attributes

Figure 7.1 uses a pyramid of four hierarchical layers describing a product's attributes:

```
          /\
         /  \        DELIGHTFUL   - is any of it worth remarking on?
        /----\
       /      \      USABLE       - can the target persona get through it?
      /--------\
     /          \    RELIABLE     - does it work consistently?
    /------------\
   /              \  FUNCTIONAL   - does it do the job at all?
  ------------------
```

> "The pyramid on the left illustrates the misconception that an MVP is just a product with limited
> functionality, and that reliability, usability, and delight can be ignored. Instead, the pyramid on
> the right shows that while an MVP **has limited functionality, it should be complete** by addressing
> those three higher-level attributes."

The claim is precise: **narrow the base, keep all four layers**.

| Attribute | The question | Failure looks like |
|---|---|---|
| **Functional** | Does it do the job at all? | A demo that cannot complete the task |
| **Reliable** | Does it do it consistently? | Works in the demo, fails on a real account |
| **Usable** | Can the target persona get through it unaided? | Works, if you already know where to click |
| **Delightful** | Is there anything worth remarking on? | Correct, forgettable, and unmentioned to a colleague |

**Delight is not polish.** It is the reason someone tells someone else. A product that is functional,
reliable and usable is *adequate* — and adequate does not displace an incumbent or a workaround that
already has the advantage of being familiar and free.

Note the resemblance to the Kano hierarchy in `d3nexus:lean-value-strategy`: must-haves, then
performance, then delighters. Both put delight at the top, both say it is real value, and both say it
is only collectable once the layers beneath it hold.

---

## Vertical versus horizontal cuts

The pyramid is really a rule about **which direction you cut**.

**Horizontal cut — wrong.** Keep the whole feature scope, lower quality across all of it. Every
feature present, none of them reliable, the UX unfinished. This is what "it's only an MVP" usually
produces, and it tests as *"this is broken"* — which teaches you nothing about your hypotheses,
because you never gave them a fair hearing.

**Vertical cut — right.** Fewer features, each one complete through all four attributes. This tests
as *"this does less than I want, but what it does is good"* — which is real information about whether
the value proposition lands.

```
   HORIZONTAL (wrong)              VERTICAL (right)
   +---+---+---+---+---+           +---+
   | delightful ?      |           | D |
   +-------------------+           +---+
   | usable ?          |           | U |
   +-------------------+           +---+
   | reliable ?        |           | R |
   +---+---+---+---+---+           +---+
   | F | F | F | F | F |           | F |
   +---+---+---+---+---+           +---+
   all features, none finished     one benefit, finished
```

**Why it matters for learning, not just for taste.** A horizontally-cut MVP confounds the experiment.
When it tests badly you cannot tell whether the value proposition is wrong or the build is bad, so
the wave produces no validated learning and you run it again. A vertically-cut MVP gives you an
answer you can act on.

---

## Applying it at step 4

This material lives in Chapter 7 (step 5, creating the prototype), but it **bounds what step 4 may
scope**. A feature set that cannot be delivered complete through all four attributes within your
constraints is too large, and that is discovered at scoping time or expensively at build time.

Check the v1 column against all four:

- **Functional** — does the v1 column let the persona complete the job end to end? A must-have with
  no chunk in v1 usually fails this.
- **Reliable** — is reliability work in the estimates? If the effort numbers assume the happy path
  only, they are wrong, and the ROI ranking built on them is wrong too.
- **Usable** — can the persona get through it without being walked through? If the plan depends on
  onboarding a user personally, that is a Wizard-of-Oz MVP test and should be named as one.
- **Delightful** — the delighter chunk is in v1. This is the same requirement as step 3 of the
  composition rule, arrived at from a different direction — which is a good sign the rule is right.

**When the four attributes will not fit**, the answer is to narrow scope, not to lower the bar: drop
a benefit, chunk the remaining ones smaller, or return to Stage 2 and shorten the value proposition.
Quality is not the adjustable dimension.

---

## MVP versus MVP test

Olsen resolves the long-running argument about whether a landing page is an MVP by changing the noun:

> "Some people argue vehemently that a landing page is a valid MVP. Others say it isn't, insisting
> that an MVP must be a real, working product or at least an interactive prototype. The way I resolve
> this dichotomy is to realize that these are all methods to **test** the hypotheses behind your MVP.
> By using the term **MVP tests** instead of MVP, the debate goes away. This allows more precise
> terminology by reserving the use of MVP for **actual products**."

| Term | Means |
|---|---|
| **MVP** | An actual product you release to customers. Subject to all four attributes. |
| **MVP test** | Any method for testing the hypotheses behind it — wireframes, interactive prototype, Wizard of Oz, concierge, smoke test, fake door, landing page. |

Use his terms. They matter here because the four-attribute bar applies to an **MVP**, not to every
MVP test — nobody expects a fake door to be delightful. Conflating the two produces both errors at
once: over-building a throwaway test, and under-building a real release.

A caution that belongs with this: a landing page or smoke test measures **marketing** — whether the
description is compelling. It does not measure product-market fit, because there is no functionality
the customer can use. Testing fit requires putting something they can interact with in front of them.

> Steps 5 and 6 — building MVP tests and running them with customers — are **not implemented** in
> this skill suite. This section exists so that step 4 scopes something that could be built
> completely, and so the handoff at Gate 3 uses the right words.

---

## Related

- [The MVP Candidate Grid](mvp-candidate-grid.md) — the composition rule
- [ROI Prioritization](roi-prioritization.md) — ordering the work
- [lean-mvp-scoping](../SKILL.md)
