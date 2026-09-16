# The Competitive Value Proposition Grid

Reference for [lean-value-strategy](../SKILL.md), steps 2–4. How to build Olsen's value proposition
grid (Tables 5.4 and 5.5) and read a strategy out of it.

The grid's job is not to show that your product is good. It is to make a **choice** visible — and to
make its absence equally visible.

---

## Table of Contents

1. [Who counts as a competitor](#who-counts-as-a-competitor)
2. [The grid structure](#the-grid-structure)
3. [Scoring conventions](#scoring-conventions)
4. [Win one, hold parity](#win-one-hold-parity)
5. [The search engine case](#the-search-engine-case)
6. [Reading the grid back](#reading-the-grid-back)
7. [Failure signatures](#failure-signatures)

---

## Who counts as a competitor

> "'Competitors' doesn't just mean direct competitors: in the unlikely case that you don't have any
> direct competitors, there should still be **alternative solutions that customers are currently
> using** to meet their needs (remember how pen and paper was an alternative to TurboTax)."

Three kinds of column, in descending order of how obvious they are and ascending order of how often
they are the real answer:

**Direct competitors.** Products in the same category solving the same need the same way. Easy to
name, and usually the least interesting column — you are all fighting over the same customers.

**Indirect alternatives.** Different category, same job. A spreadsheet competes with your project
tool. A phone call competes with your messaging feature.

**The current workaround, including doing nothing.** What the persona actually does today. Pen and
paper. A shared spreadsheet and a weekly call. A junior employee spending Friday afternoon on it.
Tolerating the problem.

**The workaround column is mandatory.** It is already recorded in `01_problem_space_spec.md` as the
persona's `Current workaround`, it is what you measured satisfaction against in Stage 1, and it is
what the customer keeps doing if you do not clearly beat it.

**"We have no competitors" is not an answer.** It means "no direct competitors", which is a fact
about the category, not about the customer. Every customer with the need is doing *something*.

> "No direct competitors is genuinely useful — it means the category is open. But it isn't the same
> as no competition. In Gate 1 we recorded that they handle this today with a shared sheet and a
> Monday call. That's the column we have to beat, and it has some real advantages: it's free,
> everyone already knows how to use it, and nobody has to approve it."

That last point is why the workaround column matters. Workarounds beat products on switching cost,
and a grid without that column hides the strongest competitor in the market.

---

## The grid structure

Rows are benefits grouped by Kano category. Columns are each competitor plus your product.

| Benefit | Competitor A | Competitor B | Current workaround | **My product** |
|---|---|---|---|---|
| **Must-haves** | | | | |
| Must-have 1 | Yes | Yes | Yes | Yes |
| Must-have 2 | Yes | Yes | No | Yes |
| Must-have 3 | Yes | Yes | No | Yes |
| **Performance benefits** | | | | |
| Performance benefit 1 | **High** | Low | Low | Medium |
| Performance benefit 2 | Medium | **High** | Low | Low |
| Performance benefit 3 | Low | Medium | Low | **High** |
| **Delighters** | | | | |
| Delighter 1 | **Yes** | | | |
| Delighter 2 | | | | **Yes** |

This is Olsen's Table 5.5, and it is worth reading as a story. Competitor A wins performance 1.
Competitor B wins performance 2. You are taking performance 3 — perhaps because you found a segment
that values it more, or because you have technology that lets you reach a level others cannot. A
already has a delighter; you have a different one. Key differentiators are in **bold**.

**Row ordering matters.** Must-haves first establishes the floor, so the performance rows are read as
"and on top of that, here is where we compete." Leading with performance invites the founder to
treat table stakes as achievements.

---

## Scoring conventions

**Must-haves — Yes / No.**

> "The entries for must-haves should be 'Yes'."

A serious competitor is Yes on all of them; so must you be. A **No** in your column is not a
trade-off, it is a disqualification — fix it or accept you are not in this category. A No in the
*workaround* column is informative: it is a real gap, and often the cheapest reason to switch.

**Performance benefits — High / Medium / Low, or numbers.**

> "For performance benefits, you should use whatever scale works best for you: a scale of 'High',
> 'Medium', and 'Low' usually works well. For performance benefits that are amenable to numerical
> measurement, you can use the values for higher precision."

Olsen's example: for a restaurant reservation app, *number of restaurants in the system* and *time it
takes to make a reservation* are both measurable — use the numbers. Numbers survive disagreement in
a way that "High" does not; two people can both say "High" and mean different things.

**Delighters — one per row, Yes where present.**

> "Delighters are typically unique, so just list each delighter on a separate row and then mark 'Yes'
> where applicable."

Most cells in the delighter block stay empty. That is correct and it is the point — a delighter that
several columns share has already migrated to a performance benefit.

**Existing product vs planned product.** Score an existing product on what it does. Score a new one
on what you **plan to achieve**, and mark those cells as hypotheses. A planned High is a commitment
to spend, and treating it as a fact is how roadmaps quietly become fiction.

---

## Win one, hold parity

The strategy is in two commitments, and both are required.

**Commitment 1 — designate exactly one performance benefit to win.** Not two. Winning means investing
enough to be visibly, defensibly better, and that budget comes from somewhere.

**Commitment 2 — hold parity on the rest.** Comparable or better, not excellent. This is the half
that gets forgotten, and it is where products die: a team wins spectacularly on one axis and falls so
far behind on another that the win never gets evaluated.

Look again at the "My product" column above: Medium, Low, **High**. The **Low** is the most important
cell in the grid. It is the only direct evidence that a decision was made, and it is what pays for
the High.

**When is Low acceptable?** When the benefit is not what your segment optimizes for, and you can say
which segment that concedes. Low on price sensitivity is fine if you are selling to people who are
not price sensitive — and it explicitly concedes the ones who are. Say so; that concession belongs in
the non-goals.

**When is Low fatal?** When the benefit is drifting toward must-have status. Kano migration means
today's performance benefit is tomorrow's table stake, so a Low on a fast-migrating benefit is a
dated decision with a short life. Note the migration stage next to any Low you accept.

---

## The search engine case

Olsen's worked example, because it shows both halves operating.

Early search engines competed on three performance benefits:

| Benefit | What it meant |
|---|---|
| **Number of results** | How many pages in the index |
| **Freshness** | How quickly new pages were added and existing ones updated |
| **Relevance** | How well the top results matched the query |

Different companies chose differently, because *"at this early stage in the search engine market, the
relative importance of each benefit wasn't clear."*

Then the market resolved it. Everyone's index got large — and *"while users liked knowing that there
were many results, they didn't usually take the time to look beyond the first few pages."* Number of
results had become a must-have and stopped differentiating. Freshness followed. That left relevance
as the benefit that mattered, and the one offering the biggest opening.

> "Google was able to achieve much higher relevance than other search engines due to its unique
> PageRank algorithm. **Because they were best at the benefit that mattered most — and had comparable
> or better performance on the other dimensions** — Google won the search engine wars."

Three things to take from it:

1. **Which benefit matters is a fact about the market at a point in time**, and it moves. Google did
   not pick relevance because it was inherently more important; it became the differentiating axis
   once the others commoditized.
2. **Winning required being best at exactly one thing** — not three.
3. **Parity on the others was a precondition**, not a consolation. A search engine with the best
   relevance and a stale, tiny index would not have won.

---

## Reading the grid back

A completed grid should collapse into one sentence a stranger could repeat:

> "For **\<persona\>** who **\<underserved need from Gate 1\>**, **\<product\>** is the only option
> that **\<winning performance benefit\>** — unlike **\<competitor / workaround\>**, which
> **\<their weakness on that benefit\>**. It also **\<delighter\>**."

If you cannot fill that in from the grid, the grid has not produced a strategy yet. The usual cause
is that no cell in your column is bold.

**Trace every claim back.** The winning benefit should map to an upper-left need from Gate 1 — high
importance, low satisfaction. If it maps to an upper-right need, you are planning to win at something
customers are already satisfied with, which buys no switching.

---

## Failure signatures

**The me-too column.** Your column is identical to a competitor's. No bold cells, no delighter, no
Low. There is no reason for a rational customer to switch, and switching costs are never zero.

**Parity everywhere, including no Low.** Your column matches the competitors on every row — Yes on
the must-haves, Medium on every performance benefit, no delighters. No bold cell, and, just as
telling, **no Low**: nothing was scored down, so nothing paid for anything. This is the quietest
me-too signature because every individual cell looks defensible; only the column read as a whole
shows that no decision was made. Check the competitors' scores for evidence before diagnosing —
whether this is an uncontested opening or a market already won turns on whether those Mediums are
real.

**High everywhere.** The founder has scored themselves best on every performance benefit. This is not
ambition; it is the refusal to choose, and it reliably produces a product that is second-best at
everything.

> "Every performance row says High for us. That reads as 'we haven't decided' rather than 'we're
> excellent'. Winning on one benefit takes real investment and it has to come from somewhere. Which
> of these are you willing to be Medium at — and is there one you'd take Low on, if it bought a
> decisive lead on the one that matters?"

**A No in your must-have row.** Not a trade-off. You are not in the category. Either meet it or
re-open Gate 1, because a segment whose table stakes you cannot afford is the wrong segment.

**An empty workaround column.** Either the founder has not described the persona's current behaviour,
or the grid is dodging the strongest competitor. Go back to `01_problem_space_spec.md`; it is in
there.

**Delighters that everyone has.** Check the migration stage. If two competitors already ship it, it
is a performance benefit and belongs in that block, scored.

**Bold in someone else's column only.** Every competitor has a differentiator and you have none. This
is the me-too signature with extra steps — and it is a Gate 2 failure, not a presentation problem.

---

## Related

- [Kano Model Framework](kano-model-framework.md) — classifying the rows
- [lean-value-strategy](../SKILL.md)
