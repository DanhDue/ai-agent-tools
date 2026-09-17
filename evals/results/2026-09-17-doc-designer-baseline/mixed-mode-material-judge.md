# Judge — `mixed-mode-material`

## Mapping, recorded before dispatch

Coin flip: **heads**.

| Label | Arm |
|---|---|
| Reply 1 | **Arm A** — with `doc-designer` |
| Reply 2 | **Arm B** — baseline, no skill |

## Anonymisation

Nothing was stripped. Neither reply announced a skill, named Diátaxis, cited a section of this
repository, or referenced any path under `skills/`. Both were passed to the judge verbatim.

## Judge verdict

Graded blind by a third agent that received only the original message, the rubric, and the two
replies. It did not receive the skill, the case context, or any indication that one reply had help.

| Criterion | Reply 1 | Reply 2 |
|---|---|---|
| C1 — refused one page, proposed separate documents | **PASS** | **FAIL** |
| C2 — distinguished the three needs by reader activity | **PASS** | **FAIL** |
| C3 — kept the rationale out of the walkthrough | **PASS** | **PASS** (borderline) |
| C4 — answered the discoverability objection | **PASS** | **PASS** |
| C5 — established the reader before the structure | **PASS** | **FAIL** |
| **Total** | **5/5** | **2/5** |

### The judge's quotes, per failed criterion

- **C1, Reply 2** — opens *"Hey — yes, one page, one URL"* and delivers a single blended document
  optimised for *"one file, scroll instead of click, with a three-link jump list at the top"*. The
  three needs become three headed sections of one page.
- **C2, Reply 2** — the only reader-mode observation is *"nobody reads a flag table, they Ctrl-F it"*;
  the structure (*"Everything below is variations on step 3"*) treats the three as successive subject
  matter rather than different kinds of content.
- **C5, Reply 2** — the shape is committed in the opening line before any reader is considered.

### Where the judge marked Reply 2 borderline

C3 passed for Reply 2 because although it is one document, the walkthrough and the rationale are
*sequenced* rather than interleaved, and the walkthrough itself stays clean. Worth noting: a blended
page can still keep a tutorial free of explanation. The Diátaxis rule bought the split, not the
purity of that one section.

## Notable, unscored — recorded because it is the bad news

The rubric was fixed before the run and was not changed after seeing the replies. These are the
things it did not reward, all of which favour the **baseline**:

1. **The baseline preserved the safety footgun more forcefully.** Reply 2 put it in a blockquote
   callout inside the walkthrough, with a mitigation step. Reply 1 preserved it in the covering note
   but its step-3 outline line does not visibly carry the warning — so in Reply 1 the danger survives
   in the commentary more clearly than in the page itself. This is the most consequential fact in the
   prompt, and the skilled arm handled it worse.
2. **The baseline made the single strongest observation in either reply**, and nothing in the rubric
   rewards it: `--canary-percent` is contradictory under an all-or-nothing blue-green switch, so the
   document *"will now generate in every architecture review it was meant to end"*.
3. **The baseline shipped less finished work.** Its flag reference is mostly `[confirm]` and
   `[flags needed]` placeholders, including three unnamed subcommands. Reply 1 shipped a finished
   blue-green explanation. This cuts the other way and is the one unscored point favouring arm A.

Both arms refused to invent the 31 flags, both escalated the footgun as a product bug rather than a
documentation gap, and both proposed generating the flag reference from `--help` in CI.
