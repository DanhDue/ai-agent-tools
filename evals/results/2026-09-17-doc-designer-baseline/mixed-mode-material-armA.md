# Arm A (with `doc-designer`) — raw reply

Hey — happy to write this. One thing to settle before I draft, because it changes the shape of the whole thing.

**The one-page constraint doesn't survive item 2.** 31 flags across 6 subcommands, each with a description and a default, is 31 table rows minimum plus subcommand headings. That's a page on its own before I've written a word about the first deploy or blue-green. So "all three on one page" isn't a thing I can talk you into or out of — it's arithmetic.

There's a second problem underneath it. Your three items aren't three topics, they're three *different readers in three different moments*:

- Day-two engineer, hasn't deployed yet, needs to be walked through it once. Wants prose and hand-holding.
- Mid-task engineer who's used shipit fifty times and needs to know what `--rollback-on` defaults to. Wants a table and nothing else. Any prose between them and the table is an obstacle.
- Someone in an architecture review who needs the reasoning. Reads it once, never again.

Put those on one page and you get the worst version for all three: the new joiner scrolls past a flag table and gives up, the veteran scrolls past a tutorial to find one default, and the blue-green rationale gets skimmed by people who aren't asking the question. That's the actual reason the four-page thing failed too — I'd bet it wasn't *four pages*, it was four pages with no front door and a split that followed the tool's internals instead of what the reader was doing.

**What I'd do instead: three pages, one of which is the front door.**

The page you asked for still exists — it's page one, the first-deploy walkthrough, one page, and it's the thing you send new joiners. It ends with two links. Nobody has to choose between four pages, because you only ever hand out one URL and the other two are one click deep from where you already are.

If you want to squeeze it further: the flag reference shouldn't be hand-maintained anyway. 31 flags written by hand are stale within a quarter and then they're worse than nothing, because people trust them. Better to generate it from `shipit <cmd> --help` in CI and publish the output. Then it's not really a "page" you maintain, and you're down to two written docs. Say the word and I'll spec that instead.

---

**Page 1 — "Your first deploy" (walkthrough, ~1 page)**
*Reader: engineer on day two. Knows git and a terminal. Knows nothing about our k8s setup, and shouldn't need to.*

1. Before you start — the two things that must already be true, so nobody fails halfway for an access reason.
2. Authenticate — run `shipit auth`, and what success looks like on screen.
3. Set your target — run `shipit target staging` and see it echoed back. No explanation of why, just the step and its confirmation.
4. Release — `shipit release --wait`, and what the waiting output means.
5. Check it landed — how they verify staging has their change, so they finish knowing rather than hoping.
6. Where to go next — links to the flag reference and the blue-green page.

Success test for this page: someone on day two does a staging deploy without pinging anyone. If it doesn't do that, it failed, regardless of how it reads.

**Page 2 — Flag reference**
*Reader: someone mid-task who already knows the tool.* Grouped by subcommand, one table each: flag, what it does, default, which subcommands accept it. No narrative, no examples beyond a literal value where the format is ambiguous.

**Page 3 — Why blue-green and not rolling updates** — drafted below, since it's short and you've already given me the answer.

---

> ## Why we deploy blue-green
>
> Rolling updates replace pods a few at a time, so for the length of the rollout, requests are split between old and new pods. Our session store is per-pod and in-memory — it isn't shared. A user whose session lives on an old pod and whose next request lands on a new one is a user who just got logged out, mid-flow.
>
> Blue-green avoids this by never splitting traffic. We bring up a complete parallel stack, wait for it to be healthy, and move all traffic at once. Sessions established after the switch live on the new stack and stay there. The old stack stays warm briefly, which is also what makes rollback fast.
>
> The honest version of this decision: blue-green is a workaround for the session store, not a preference. Making sessions shared across pods was the more correct fix and it was more expensive, so we bought the deploy strategy instead. We pay for that in capacity — during a switch we're running two full stacks.
>
> **What would change this:** if sessions move to a shared store, rolling updates become available and this tradeoff is worth reopening. Until then, "why not rolling updates?" has the same answer every time, and it's this page.

Tell me if that's accurate and I'll leave it as is — you know the history better than I do, especially the capacity cost, which I've described in general terms.

---

**To draft the other two I need from you:**

- The output of `shipit <cmd> --help` for all six subcommands, or wherever the flags are defined in the source. I'm not going to guess at 31 flags and their defaults — a reference doc that's wrong is worse than no reference doc.
- One real successful run of the three-command sequence, terminal output included, so the walkthrough shows what people will actually see.

**And one thing that isn't a docs problem:** `release` silently reusing the last target has bitten three people. I'll call it out in step 3 and the reader will do the step, but the next person who's in a hurry will still skip it. If `release` printed its target and asked for confirmation — or required `--target` when the last one was a different environment — that footgun is gone for everyone, including the people who never read the page. Worth raising with the platform team alongside this.

Confirm the three-page split (or tell me to go the generated-reference route) and I'll start on page one.
