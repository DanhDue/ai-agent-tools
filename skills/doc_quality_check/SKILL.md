---
name: doc_quality_check
description: Quality gate for documentation. Runs mechanical checks, Diátaxis type conformance and a content audit, and refuses outright if the change touches files that ship in the build. Use it in place of quality_check whenever the deliverable is prose.
---

# Document Quality Check

> [!IMPORTANT]
> **Role**: You are the quality gate for documentation work. Your mandate is to verify a document
> mechanically and semantically without pretending it can be tested, and to refuse the job outright
> when the work is not documentation at all.

The development-side counterpart is `quality_check`. **The two share no tier, no audit and no
tooling**, and neither invokes the other — which is why they are separate skills rather than two
branches of one. Routing between them belongs to the lifecycle that owns the work, or to
`rules/CRITICAL_RULES.md`.

**Announce at start:** "I'm using the doc_quality_check skill to verify `<document>`."

## When to Use

- Gate 3 of `doc-lifecycle`.
- Any time a document is finished and someone else will rely on it.
- Before merging a branch whose changes are entirely documentation.

## When NOT to Use

**If the change touches any file that ships in the build, this is the wrong skill.** Run
`quality_check` instead. Check 0 below enforces this mechanically — do not decide it by judgement.

This matters more than it looks. The document path skips the 3-tier suite, the four semantic audits
and the native build smoke gate; the development path does not. That makes mislabelling code as
documentation a cheap and legitimate-looking shortcut. The defence cannot be a more emphatic rule,
because the problem is incentive, not comprehension. It has to be mechanical.

## The Four Checks

Run them in this order. Check 0 is first because it is the cheapest and it prevents the whole
misuse.

### Check 0 — Refusal rule

```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py \
  --changed-files $(git diff --name-only <base_ref>...HEAD)
```

Any changed file whose extension ships in a build aborts the run and names the offending paths.
Documentation directories (`docs/`, `.devtool/`, `.github/`) and `CHANGELOG.md` are exempt.

🔴 **Blocker.** On abort, stop. Do not run the remaining checks, and do not report a verdict — the
work belongs in `dev-lifecycle`.

### Check 1 — Mechanical

```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py \
  --require-toc --require-bilingual <document>.en.md <document>.vi.md
```

Catches placeholders (`TBD`, `TODO`, `FIXME`, `XXX`) in prose, relative links that do not resolve,
anchors with no matching heading, unbalanced code fences, a missing `.en.md`/`.vi.md` counterpart,
heading-structure drift between the pair, and a missing or incomplete table of contents. Every `##`
section and every `### Task` heading in an implementation plan must be linked from that variant's
contents; document length does not waive the rule.

**Pass both `--require-toc` and `--require-bilingual` for lifecycle deliverables, and omit them
otherwise.** Pass the English and Vietnamese paths in the same invocation. `task_*.md` files, epic
records and `SKILL.md` files are not deliverables and were never meant to carry this contract;
requiring it of them would fail files that are correct as they stand.

It strips fenced blocks and inline code spans before scanning, so a document that *documents* these
checks does not fail them. That is not hypothetical — it was observed while building this skill,
and `scripts/verify.sh` step 3 strips the same way for the same reason.

🔴 **Blocker.**

### Check 2 — Diátaxis type conformance

Read the document's declared `Diátaxis mode` from its Meta Data, then check it stays inside that
type:

| Declared type | A finding is… |
|---|---|
| tutorial | explanation, or reference-style description |
| how-to guide | teaching, digression, or explanation |
| reference | instruction, or explanation |
| explanation | instruction, or technical description |

The remedy is always to **relocate and link**, never to delete — the material belongs elsewhere,
not nowhere.

**When no type is declared, check which case you are in.** A `doc-lifecycle` deliverable with no
declared mode never passed `doc-designer`'s Step 2, and that is a 🔴 finding. A file that was never a
lifecycle deliverable — a README, a `SKILL.md`, a one-word correction to either — has no Meta Data to
read and never should have; record Check 2 as **not applicable** and move on. Returning 🔴 on a typo
fix because a README has no `Diátaxis mode` teaches people to stop running the gate.

🟡 **Warning**, unless the document declares one type and is substantially another — then 🔴.

### Check 3 — Content audit

Dispatch a subagent using
[`references/document-reviewer-prompt.md`](references/document-reviewer-prompt.md), passing the
English and Vietnamese document paths, their declared type, audience and `Acceptance` criterion.
Review English as canonical, then verify that Vietnamese preserves the same facts, omissions,
examples, links, and section ordering rather than merely having the same heading shape.

It checks what a script cannot see: internal contradictions, ambiguity that would send a reader the
wrong way, **unsupported claims** — invented numbers, rules attributed to a source that does not
contain them — and whether the stated audience could actually perform the `Acceptance` criterion
after reading.

🔴 **Blocker** on unsupported claims or an unmet `Acceptance`; 🟡 otherwise.

## Verdict

```
## Document Quality Report — <document>

| Check | Result | Notes |
|---|---|---|
| 0. Refusal rule | ✅ PASSED / ❌ ABORTED | <offending files, if any> |
| 1. Mechanical | ✅ PASSED / ❌ FAILED | <n findings> |
| 2. Type conformance | ✅ PASSED / ⚠️ WARNING / ❌ FAILED | declared <type> |
| 3. Content audit | ✅ PASSED / ⚠️ WARNING / ❌ FAILED | acceptance met / not met |

**Verdict:** 🟢 LGTM / 🔴 BLOCKED
```

🟢 requires **all four clean**. A verdict assembled from a partial re-run is not a verdict: after
fixing findings, run all four again.

## Red Flags

- Reporting a verdict after Check 0 aborted.
- Re-running only the check that failed and calling the result 🟢.
- Treating a missing `Diátaxis mode` as "not applicable" rather than as a finding.
- Deleting out-of-type material instead of relocating and linking it.
- Running the 3-tier test suite, the four semantic audits, or a native build here. None of them
  apply to prose, and a green light from a check that does not apply is worse than no check.
- Accepting a claim because it sounds like expert advice. Attributed rules that the source does not
  contain are the single most common defect in methodology documentation.
