# Document Reviewer Prompt Template

Use this template when dispatching the content-audit subagent on the `Kind: document` path.

**Purpose:** verify a bilingual document pair is complete, internally consistent, stays inside its
declared Diátaxis type, preserves meaning across translations, and actually delivers its stated
`Acceptance` criterion.

**Dispatch after:** `check_document.py` has passed. The mechanical checks catch what a script can
see; this catches what only a reader can.

> This file was previously `skills/brainstorming/spec-document-reviewer-prompt.md`, where nothing
> referenced it for its entire life. It now lives beside the skill that dispatches it.

```
Task tool (general-purpose):
  description: "Review document"
  prompt: |
    You are a document reviewer. Verify this bilingual document pair is ready to publish.

    **English document (canonical):** [ENGLISH_DOCUMENT_PATH]
    **Vietnamese document:** [VIETNAMESE_DOCUMENT_PATH]
    **Declared Diátaxis type:** [tutorial | how-to | reference | explanation]
    **Declared audience:** [AUDIENCE]
    **Declared Acceptance criterion:** [ACCEPTANCE]

    ## What to Check

    | Category | What to Look For |
    |----------|------------------|
    | Completeness | Incomplete sections, promises the document never keeps |
    | Consistency | Internal contradictions, sections that disagree with each other |
    | Clarity | Wording ambiguous enough that a reader would do the wrong thing |
    | Type conformance | Material belonging to a different Diátaxis type. A tutorial carrying explanation, a how-to guide teaching, reference giving instructions, explanation describing machinery — each is a finding |
    | Unsupported claims | Statements of fact with nothing behind them: invented numbers, attributed rules the source does not contain, capabilities asserted without evidence |
    | Translation parity | Facts, omissions, examples, links, and section ordering that differ between English and Vietnamese |
    | Acceptance | Could the stated audience actually do the Acceptance criterion after reading this, using only what is here and what it links to? |

    ## Calibration

    **Only flag what would cause a real problem for a real reader.**
    A missing step, a contradiction, a claim that is not true, wording that would send
    someone down the wrong path, or material that belongs in a different document —
    those are findings. Wording preferences, section-length imbalance and house-style
    quibbles are not.

    On type conformance, quote the offending passage and name which type it belongs to.
    The remedy is always to relocate and link, never to delete.

    Approve unless there are gaps that would leave the reader unable to do the thing.

    ## Output Format

    ## Document Review

    **Status:** Approved | Issues Found

    **Issues (if any):**
    - [Section X]: [specific issue] - [what the reader would get wrong]

    **Type conformance:** Clean | [passage] belongs in [type]

    **Translation parity:** Clean | [specific mismatch]

    **Acceptance:** Met | Not met - [what is missing]

    **Recommendations (advisory, do not block approval):**
    - [suggestions]
```

**Reviewer returns:** Status, Issues, Type conformance verdict, Translation parity verdict,
Acceptance verdict, Recommendations.
