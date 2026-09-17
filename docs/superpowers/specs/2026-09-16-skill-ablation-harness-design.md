# Skill Ablation Harness — Design Specification

> **Topic**: Measuring whether a skill actually changes agent behaviour **Date**: 2026-09-16
> **Status**: Approved Design Spec **Scope**: `evals/` harness for the four Lean Product skills,
> reusable for any future skill

---

## 1. Problem

The four Lean Product skills were verified with four pressure tests that all scored 17/17.
Every one of those tests ran **with the skill present**. None ran without it.

`skills/writing-skills/testing-skills-with-subagents.md` — this repository's own standard — is explicit that this is half a cycle:

> **Core principle:** If you didn't watch an agent fail *without* the skill, you don't know if the
> skill prevents the right failures.

A GREEN-only result cannot distinguish two very different worlds:

1. The skill prevents a failure the agent would otherwise commit. *The skill earns its context.*
2. A competent agent would have behaved correctly anyway.
   *The skill is inert, and the 17/17 was measuring the model, not the skill.*

The harness exists to tell those apart, per rule, with a number.

A second, separate flaw:
in that round the same party wrote the skills, designed the scenarios, ran them,
and graded the results. Even in good faith that is not a measurement.

---

## 2. Non-goals

- **Not** wired into `scripts/verify.sh`.
  Each run costs real agent invocations; it belongs at release time, not in the verify loop.
- **Not** dependent on `claude plugin eval`.
  That command is gated behind early access on this account and currently does nothing (`"plugin eval" is currently in early access`,
  exit 0, no files written). The layout is chosen to be *compatible* with it, not to require it.
- **Not** a correctness test of the skill's prose.
  `scripts/check_source_fidelity.py` already guards the documented rules.
  This measures **behaviour**.

---

## 3. Design

### 3.1 Two arms plus a blind judge

For each scenario, three agent invocations:

| Arm | Receives | Purpose |
|---|---|---|
| **A** | Role framing + founder prompt + **the skill files** | GREEN |
| **B** | Role framing + founder prompt, **no skill** | RED / baseline |
| **Judge** | Founder prompt + rubric + both replies, anonymised and shuffled | Scoring |

The score for a scenario is the count of rubric criteria passed. The finding is **delta = A − B**.

### 3.2 The baseline must be fair

Arm B receives the **same role framing** as arm A
— *"an experienced product advisor helping an early-stage founder"*
— and differs only in having none of the skill's specific rules.

A baseline with no role framing at all would produce a larger,
flattering delta that conflates two effects:
the value of assigning a role, and the value of the skill's content.
Only the second is being bought with context budget, so only the second is measured.

*(Considered and rejected: a three-arm design isolating both effects. Rejected for cost
— 20 invocations instead of 15 — and because the role-framing delta is not actionable here.)*

### 3.3 The judge is blind, and grades against the book

The judge receives the two replies labelled `Reply 1` / `Reply 2` in **randomised order** and is not told which arm is which.
The label→arm mapping is recorded in the results file and revealed only after the verdict is written.

**The rubric cites *The Lean Product Playbook*, never the skill.** This matters:
a rubric written from the skill would ask *"did the reply echo our wording?"*,
which arm A passes trivially.
A rubric written from the source asks *"did the reply follow Olsen's method?"*
— a question both arms can answer on merit, and one the skill can genuinely lose.

### 3.4 Scenarios use unfamiliar domains

The earlier round's MVP scenario reused the worked example from `skills/lean-mvp-scoping/references/mvp-candidate-grid.md` almost verbatim,
so part of its pass was the subagent recognising a grid it had just read.
Every scenario here uses a domain that appears nowhere in the skill documentation:
veterinary clinics, school bus tracking, forklift maintenance, freelance invoicing,
community gardens.

### 3.5 A low delta is a result, not a failure

Scenario 5 is expected to score near zero delta
— a competent advisor already asks about the target customer before listing features.
That is worth knowing: it says that part of the skill is not paying for the context it occupies,
and is a candidate for deletion.

The harness is built to be able to report that the skills do not work.
A harness that cannot return bad news is not measuring anything.

---

## 4. Layout

```
evals/
├── README.md                          # what this is, how to read results
├── protocol.md                        # the procedure a future agent follows
├── <skill>/<case>/
│   ├── prompt.md                      # INPUT — founder's message, verbatim
│   ├── context.md                     # INPUT — fixtures, arm framings, files arm A may read
│   └── graders/criteria.md            # INPUT — rubric, declared before any run
└── results/YYYY-MM-DD-<label>/
    ├── <case>-armA.md                 # OUTPUT — raw reply
    ├── <case>-armB.md                 # OUTPUT — raw reply
    ├── <case>-judge.md                # OUTPUT — verdict + label mapping
    └── report.md                      # OUTPUT — delta table across all cases
```

The `evals/**/prompt.md` + `graders/*.md` shape matches what `claude plugin eval` documents it scans,
so the scenarios should port with little churn if early access opens.

Scenario files carry no dates or run-specific content, so they are re-runnable indefinitely.
Results go to timestamped directories and are never overwritten
— the point is comparing runs over time, for instance after a skill is edited.

---

## 5. Scenario set

| # | Case | Skill under test | Rule at stake | Expected delta |
|---|---|---|---|---|
| 1 | `must-have-rank-23` | `lean-mvp-scoping` | All must-haves enter v1 regardless of ROI rank | High |
| 2 | `scales-and-threshold` | `lean-market-discovery` | 5-point/7-point scales; Ulwick `> 15` | High |
| 3 | `no-competitors` | `lean-value-strategy` | Workaround is a competitor column; demand a delighter | High |
| 4 | `high-everywhere` | `lean-value-strategy` | Win one, hold parity; require a deliberate trade-off | Medium |
| 5 | `feature-list-demand` | `lean-product-lifecycle` | Capture / convert / park, not refusal | **Low** |

Scenario 1 carries the most weight: it is the rule the epic exists to protect,
the founder's argument for breaking it is numerically correct,
and the pressure to comply is social as well as logical.

---

## 6. Important constraint

`scripts/check_source_fidelity.py` globs `skills/lean-*/**/*.md` and `docs/books/*.md`.
It must **never** be extended to `evals/`. These prompts deliberately contain the corrected errors
— a founder arguing to cut a must-have, a founder citing a score of 11 as passing
— because that is the input under test.

Measured: extending the glob today produces **zero** failures,
since the current prompts phrase those errors in prose rather than in the forms the regexes match.
That is incidental.
A future fixture worded *"just take cells 1-3"* would fail the build while being a perfectly correct test input,
and the fix would be to weaken the fixture rather than the glob. Keep them separate.

---

## 7. Verification

The harness is working if it can produce all three of these outcomes:

- A scenario where arm A passes and arm B fails → the skill works.
- A scenario where both pass → the skill is inert there.
- A scenario where arm A fails → the skill has a hole.

The first run establishes the baseline. It is not expected to be all-green,
and an all-green first run should itself be treated as suspicious.
