# Assumption Mapping — Design Specification

> **Topic**: Closing the Lean Product Process at steps 5-6 — testing ideas before building them
> **Date**: 2026-09-17
> **Status**: Approved Design Spec
> **Scope**: One new skill, `assumption-mapping`, extending the upstream discovery suite

---

## 1. Problem

The README states the gap plainly:

> **Steps 5 (create your MVP prototype) and 6 (test your MVP with customers) are not implemented.**

So `lean-product-lifecycle` currently ends at Gate 3 and hands `03_mvp_feature_backlog.md` straight
to engineering. That backlog is a **stack of untested hypotheses presented as a plan**. Every layer
of the Product-Market Fit Pyramid beneath it — target customer, underserved needs, value proposition
— was reasoned about carefully and validated by nobody.

The orchestrator is honest about this at Gate 3, telling the founder what they still owe themselves:
a low-fidelity prototype and waves of five to eight target customers. But honesty about a gap is not
a way through it. The founder is told to go test, handed no method, and the path of least resistance
runs directly into engineering.

This is the Build Trap arriving one step later than usual, with better paperwork.

### 1.1 Why this is a separate spec

`assumption-mapping` belongs to the **upstream discovery suite**, not to the document lifecycle. It
extends `lean-product-lifecycle`, writes into `.devtool/product/<slug>/`, and draws on a different
methodology and a different author. It ships independently and delivers value with or without
[the document lifecycle suite](2026-09-17-document-lifecycle-suite-design.md).

---

## 2. Goals and non-goals

**Goals**

1. Turn an MVP backlog into a ranked list of the assumptions holding it up.
2. Identify the hypothesis that is most important and least evidenced, and design the cheapest
   experiment capable of refuting it.
3. Force the success Criteria to be committed **before** the experiment runs.
4. Keep a durable record of what was tested, what was learned, and what changed as a result.

**Non-goals**

1. Running the experiments. The skill designs and records them; a human talks to customers.
2. Building prototypes. Step 5 of the Lean Product Process remains partly uncovered, and the skill
   must say so rather than implying completeness.
3. Replacing Gate 3. This adds a stage after it; it does not relitigate the backlog.

---

## 3. Design

### 3.1 Where it sits

```mermaid
flowchart TD
    S3["Stage 3 — MVP Feature Set<br/>(lean-mvp-scoping)"]
    G3{"Gate 3<br/>MVP backlog signed off?"}
    S4["Stage 4 — Assumption Mapping<br/>(assumption-mapping)"]
    G4{"Gate 4<br/>Riskiest assumptions tested?"}
    OUT(["Handoff to dev-designer"])
    BACK["Return to the failing<br/>pyramid layer"]

    S3 --> G3
    G3 -->|yes| S4
    S4 --> G4
    G4 -->|"evidence supports the backlog"| OUT
    G4 -->|"evidence contradicts it"| BACK
```

Gate 4 is a **human approval**, consistent with the other three gates in the suite.

`lean-product-lifecycle` needs three edits: the sequence diagram gains Stage 4, the gates table
gains Gate 4, and the *Handoff to engineering* section stops being the terminus.

### 3.2 The method — grounded in Bland & Osterwalder

Verified against the primary source now held at `docs/books/2. Testing Business Ideas.pdf`. Every
term below is the authors' own; where an earlier draft of this spec used invented names, the book's
names replace them.

**Step 1 — Identify hypotheses.** Read `03_mvp_feature_backlog.md` and the two specs beneath it and
surface what must be true, writing each one in the book's format: **"We believe that…"**. Each
hypothesis is one of three types (adapted in the source from Larry Keeley, Doblin Group and IDEO):

| Type | The book's question | The risk it names |
|---|---|---|
| **Desirable** | "Do they want this?" | The target market is too small; too few customers want the value proposition; the company cannot reach, acquire and retain them |
| **Viable** | "Should we do this?" | The business cannot generate more revenue than costs |
| **Feasible** | "Can we do this?" | The business cannot manage, scale, or get access to key resources, activities or partners |

Agents reliably over-produce **feasible** hypotheses, because feasibility is the type visible from
inside a codebase. The skill must push back toward **desirable**, which is where ideas actually die.

**Step 2 — Prioritize on the Assumptions Map.** The map is adapted in the source from Gothelf &
Seiden, *Lean UX*. Both axis labels below are the book's own wording:

```
                          Important
                              │
      already known           │        TEST FIRST
      (no experiment needed)  │     1. Design Experiment
                              │     2. Run Experiment
   Have Evidence ─────────────┼───────────────── No Evidence
                              │
           noise              │        ignore for now
                              │
                         Unimportant
```

The book is explicit that experiments are drawn from **the top right quadrant** — important, and no
evidence. The discipline lies in what gets left alone: a map on which everything is important has
ranked nothing.

**Step 3 — Turn top-right hypotheses into experiments (Test Card).** The Test Card is a Strategyzer
tool with four components. The skill uses these names, not paraphrases of them:

| Component | Content |
|---|---|
| **1. Hypothesis** | The most critical hypothesis from the top right quadrant of the Assumptions Map |
| **2. Experiment** | What will actually be done |
| **3. Metrics** | The data that will be measured |
| **4. Criteria** | The success criteria for those metrics |

Two rules govern the choice:

- **Cheapest and fastest first.** The book's framing: start with cheap, fast experiments to learn
  quickly, because every experiment reduces the risk of spending time, energy and money on the wrong
  idea. The book's library of **44 experiments** is the menu — the skill selects from it rather than
  inventing experiments of its own.
- **It must be able to fail.** An experiment with no outcome that would change the backlog is
  theatre. If no result would alter the plan, do not run it, and say why out loud.

**Step 4 — Criteria are written before the run.** This is not an addition to the method; it is what
the Test Card's **Criteria** field is for, and the card is completed at design time. Without it any
result can be read as encouraging, and the experiment measures the founder's hope rather than the
market.

**Step 5 — Capture the learning (Learning Card).** The book's sequence: **analyze the evidence**,
explicitly distinguishing strong evidence from weak, then **gain insights** that support or refute
the hypothesis, then decide. A refuted hypothesis routes back through the existing Tectonic Plates
protocol in `lean-product-lifecycle` — find the failing pyramid layer and re-validate from there
upward, rather than patching the layer you happen to be standing on.

### 3.3 Artefacts

Continuing the suite's existing numbering in `.devtool/product/<slug>/`:

| File | Holds |
|---|---|
| `04_assumptions_map.md` | Every hypothesis in "We believe that…" form, its type, its quadrant, and the test queue drawn from the top right |
| `05_test_and_learning_log.md` | One Test Card per experiment (Hypothesis / Experiment / Metrics / Criteria), each paired with its Learning Card (evidence analyzed, insights, decision) |

`05_test_and_learning_log.md` is **append-only**. A Test Card's Criteria are fixed before the
experiment runs and are never edited afterwards; a superseded conclusion gets a new pair of cards
referencing the old one. An editable record of what you believed is worthless precisely when it
matters most, because it will have been quietly revised to agree with whatever happened.

---

## 4. Failure modes

| Failure | Mitigation |
|---|---|
| Criteria rationalized after the fact | Criteria are committed to the Test Card before the experiment runs; the skill refuses to record a Learning Card against a Test Card whose Criteria field is empty |
| Experiments that cannot fail | Every designed test states, in writing, which result would change the backlog. No such result, no experiment |
| Everything mapped as important | The map is a ranking, not a labelling exercise; the skill names the top 3 hypotheses and explicitly parks the rest |
| Feasible hypotheses crowd out desirable ones | The skill requires at least one **desirable** hypothesis in the top 3, or a written reason why there is none |
| Becomes a stalling device | Cap: three hypotheses per round. Stage 4 has a bottom, and the skill says where it is |

---

## 5. Verification

Subject to `evals/`, per README §3.7. The sharpest scenario: hand an agent a plausible MVP backlog
whose weakest point is a **desirable** hypothesis dressed up as a feasible one, and check whether
the skill causes the agent to name and test the desirable hypothesis instead. Grade blind
against the source, not against the skill.

---

## 6. Dependencies and risks

**Primary source — acquired and verified.**

**David J. Bland & Alex Osterwalder, _Testing Business Ideas: A Field Guide for Rapid
Experimentation_** — John Wiley & Sons, copyright © 2020, ISBN 9781119551447. Held at
`docs/books/2. Testing Business Ideas.pdf`, 368 pages. Reading it requires `poppler`
(`brew install poppler`): the PDF's fonts are subset-encoded, so naive extraction returns glyph
indices rather than characters, and both `Read` and stream decompression come back empty without it.

Implementation is **no longer blocked**. The source has also already paid for itself — checking
§3.2 against the book corrected four errors in this spec's own first draft, which is exactly the
pattern `.devtool/epic/lean_product_suite/source_fidelity_review.md` exists to catch.

| The draft said | The book says |
|---|---|
| Published 2019 | Copyright © 2020 |
| Grid drawn with low evidence on the left | **Have Evidence** on the left, **No Evidence** on the right; the test queue comes from the **top right** quadrant |
| Log fields invented: hypothesis / method / threshold / result / verdict | **Test Card** (Hypothesis / Experiment / Metrics / Criteria) and **Learning Card** — both named Strategyzer tools |
| Items called "assumptions" | The exercise is Assumptions Mapping, but the items are **hypotheses**, written as "We believe that…" |

The third row is the one that mattered. Invented field names produce a skill that reads as
authoritative while teaching something the source never said — and nobody downstream can tell.

**Carried into implementation**: the two attributions the book makes for borrowed material must
survive into the skill — the Assumptions Map is adapted from Gothelf & Seiden, *Lean UX*, and the
three hypothesis types from Larry Keeley, Doblin Group and IDEO.

**Other risks**

| Risk | Mitigation |
|---|---|
| Founders experience Stage 4 as an obstacle before engineering | Frame it by cost: an afternoon of interviews against a sprint. Cap at three assumptions per round |
| Overlaps `lean-market-discovery`'s opportunity scoring | Different objects: discovery scores *needs*, this scores *the beliefs holding up a plan*. Say so explicitly in both skills to keep the boundary visible |
| Step 5 stays partly uncovered | Say so at Gate 4, exactly as the orchestrator already does at Gate 3. Do not imply the process is complete when it is not |

---

## 7. Out of scope

- The document lifecycle suite — separate spec, separate lineage.
- Automated experiment execution, survey tooling, or interview transcription.
- Prototype construction (step 5 proper).
