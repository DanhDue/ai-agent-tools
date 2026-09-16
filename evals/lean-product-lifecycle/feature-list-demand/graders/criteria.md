# Rubric — `feature-list-demand`

Grade each reply independently, PASS or FAIL per criterion, quoting the reply.

Standard: Dan Olsen, *The Lean Product Playbook* (Wiley, 2015), chapters 2 and 3.

---

### C1 — Did the reply avoid producing a feature list or database schema?

**PASS** if neither appears. **FAIL** if the reply supplies a feature list, table definitions, or a
data model — including a "rough starting point" or a caveated one.

---

### C2 — Did the reply avoid *refusing* to engage?

Olsen's rule is to keep problem space and solution space separate **and alternate between them** —
*"the best problem space learning often comes from feedback you receive from customers on the
solution space artifacts you have created."* The Lean Product Process enters solution space
deliberately at step 4.

So flat refusal is also wrong. Phrases like "I can't discuss the tech stack" or "we don't talk about
features yet" fail this criterion.

**PASS** if the reply engages with the founder's ideas and explains *when* they get addressed.
**FAIL** if it stonewalls, or defers without saying when the ideas come back.

*Both C1 and C2 must be read together: the target is neither producing the schema nor refusing to
talk about it.*

---

### C3 — Did the reply record the founder's solution ideas explicitly?

The founder named six: React Native, Postgres, an AI planting assistant, a plot swap marketplace, a
site map first screen, and the developer starting Monday.

**PASS** if the reply lists or captures these as a set to be returned to — a parking lot, a held list,
an explicit "these come back at step 4". **FAIL** if they are only alluded to, or handled by moving on
to questions without acknowledging them.

---

### C4 — Did the reply convert at least one solution idea into the underlying need?

For example: the AI planting assistant implies *"plot holders need to know what to do this month
without already being an experienced gardener"*; the swap marketplace implies *"people need to exit or
change plots without losing their place in a queue"*.

**PASS** if at least one idea is restated as a customer need rather than a feature. **FAIL** if all
ideas are handled only as features to schedule.

---

### C5 — Did the reply move toward the target customer and their needs?

**PASS** if the reply asks who specifically this is for, or what plot holders and site administrators
currently struggle with. **FAIL** if it moves straight to scoping or planning.

---

### C6 — Did the reply address the idle-developer pressure?

A developer starts Monday. The founder also argues the data model is stable regardless of research.
Ignoring both leaves the advice unusable.

**PASS** if the reply proposes something concrete for Monday — interviews, a throwaway prototype, the
site-map spike, infrastructure that is genuinely research-independent — or engages with whether the
data model really is stable. **FAIL** if it neither addresses the timeline nor the argument.

---

## Output format

```
Reply 1: C1 PASS/FAIL — "<quote>" — <one sentence>
         Total: N/6
Reply 2: ...
         Total: N/6
Notable but unscored: <...>
```
