# Skill Ablation Evals

Measures whether a skill **changes agent behaviour**, rather than whether an agent that has the
skill can recite it.

Each scenario runs twice — once with the skill, once without — and a third agent grades both
replies blind. The finding is the **delta**.

> [!IMPORTANT]
> `scripts/check_source_fidelity.py` must **never** be extended to scan `evals/`.
>
> These prompts deliberately contain the errors the skills were corrected to prevent — a founder
> arguing to cut a must-have, a founder citing an opportunity score of 11 as a pass. That is the
> input under test, and a fixture that stops containing the error stops testing anything.
>
> Measured 2026-09-16: extending the glob to `evals/` currently produces **zero** failures, because
> today's prompts happen to phrase the errors in prose rather than in the exact forms the regexes
> match. That is luck, not design. A future case written as *"just take cells 1-3 and ship it"* or
> *"the cupcake principle says…"* — both entirely natural things for a founder to say — would fail
> the build on a correct fixture. Keep the directory out of scope.

---

## Why this exists

The four Lean Product skills were first verified with pressure tests that scored 17/17 — all of them
run **with the skill present**. That cannot distinguish "the skill prevented a failure" from "the
model would have been fine anyway."

This repository's own standard, in
[`skills/writing-skills/testing-skills-with-subagents.md`](../skills/writing-skills/testing-skills-with-subagents.md):

> If you didn't watch an agent fail *without* the skill, you don't know if the skill prevents the
> right failures.

---

## Running it

Follow [`protocol.md`](protocol.md). It is written for an agent to execute; a human can drive it too.

In short: for each case, dispatch arm A (with skill) and arm B (without), then a blind judge over
both replies. Write everything to `results/YYYY-MM-DD-<label>/`.

Roughly 3 agent invocations per case, 15 for the full set. This costs real money and is **not** part
of `scripts/verify.sh` — run it at release time, or after editing a skill.

---

## Reading a result

`results/<run>/report.md` holds the delta table:

| Case | Arm A (skill) | Arm B (baseline) | Delta | Reading |
|---|---|---|---|---|
| `must-have-rank-23` | 6/6 | 1/6 | **+5** | Skill is doing the work |
| `feature-list-demand` | 5/5 | 5/5 | **0** | Skill inert here |
| `high-everywhere` | 2/3 | 1/3 | +1 | Partial — one rule not landing |

**Three outcomes, all informative:**

- **High delta** — the skill earns its context on that rule.
- **Zero delta** — a competent agent already does this. The rule is not paying for the tokens it
  occupies, and is a candidate for deletion. *This is a finding, not a failure.*
- **Arm A fails a criterion** — the skill has a hole. Fix the skill, re-run, compare against the
  previous run's directory.

An all-green first run should be treated as suspicious rather than reassuring — it usually means
the scenarios are too easy or the rubric is echoing the skill.

---

## Layout

```
evals/
├── README.md                     you are here
├── protocol.md                   the procedure
├── <skill>/<case>/
│   ├── prompt.md                 INPUT  — the founder's message, verbatim
│   ├── context.md                INPUT  — arm framings, fixtures, files arm A may read
│   └── graders/criteria.md       INPUT  — rubric, fixed before any run
└── results/YYYY-MM-DD-<label>/   OUTPUT — never overwritten
```

Scenario files contain no dates and no run-specific content, so they are re-runnable indefinitely.
Results accumulate so runs can be compared after a skill is edited.

The `evals/**/prompt.md` + `graders/*.md` shape matches what `claude plugin eval` documents it
scans. That command is currently gated behind early access and does nothing when invoked, so the
harness does not depend on it — but the cases should port with little churn if it opens.

---

## Cases

| Case | Skill | Rule at stake | Expected delta |
|---|---|---|---|
| [`must-have-rank-23`](lean-mvp-scoping/must-have-rank-23/) | `lean-mvp-scoping` | All must-haves enter v1 regardless of ROI rank | High |
| [`scales-and-threshold`](lean-market-discovery/scales-and-threshold/) | `lean-market-discovery` | 5-point / 7-point scales; Ulwick `> 15` | High |
| [`no-competitors`](lean-value-strategy/no-competitors/) | `lean-value-strategy` | Workaround is a competitor; demand a delighter | High |
| [`high-everywhere`](lean-value-strategy/high-everywhere/) | `lean-value-strategy` | Win one, hold parity; force a trade-off | Medium |
| [`feature-list-demand`](lean-product-lifecycle/feature-list-demand/) | `lean-product-lifecycle` | Capture / convert / park, not refusal | **Low** |

Every case uses a domain that appears nowhere in the skill documentation. In an earlier round a
scenario reused a worked example almost verbatim, so part of its pass was pattern-matching rather
than reasoning.

---

## Adding a case

1. `mkdir -p evals/<skill>/<case>/graders`
2. Write `prompt.md` — the founder's message only. No meta-commentary, no hints.
3. Write `context.md` — both arm framings, any fixture state, and which files arm A may read.
4. Write `graders/criteria.md` — numbered criteria, each answerable PASS/FAIL from the reply alone.
   **Cite the book, never the skill** (see `protocol.md` for why).
5. Pick a domain that appears nowhere in `skills/`.
6. Add a row to the table above.
