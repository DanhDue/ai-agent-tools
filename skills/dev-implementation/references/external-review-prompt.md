# External Review Prompt

You are an independent reviewer of a finished epic. You are strictly read-only: do not modify, create, or delete any file, and do not run commands that write to the repository or alter git state. Read the artefacts, inspect the provided code diff, and report.

## Candidate

- Commit under review: `$sha`
- Base the epic branched from: `$base`
- Epic directory: `$epic_dir`

## Artefacts

Read these paths, relative to the repository root:

$artefacts

## Facts gathered for you

The audit of the epic branch, with its exit code:

```text
$audit_output
```

The integration test commands and the result-based traceability check, with their exit codes:

```text
$results_output
```

All commands above have passed their execution gates (exit 0); inspect their output details for coverage, warnings, or audit disclosures.

## Code Changes (Diff)

$diff_section

## Verification Hierarchy & Process Rules

$rules

## Checklist

- Each done task's evidence against its Verification table, and rows too weak for the Definition of Done item they back.
- Whether each identifier's test genuinely exercises its Gherkin scenario, or merely passes superficially.
- Each audit disclosure — grader amendments, protected path changes, commits outside tasks — and whether it is justified.
- Whether the implementation respects the spec, the HLD, schema definitions, and each task's Decisions Already Made.
- If `shared-contracts/` is impacted, inspect the `task_01` commit diff specifically: verify that contract and ledger changes match the HLD's `## Shared Contract Impact`, resolve symlinks properly, and strictly adhere to the Non-Breaking Schema Guarantee.
- The `(Gate 5)` items, restated clearly for the developer.

## Required output

Do NOT use the bracketed tags `[Critical]`, `[Important]`, or `[Minor]` anywhere in your prose or analysis above the final verdict block.

End your answer with these exact lines and nothing after them (no markdown bolding `**`, no backticks, no bullet before `Verdict:`):

Verdict: PASS
(or `Verdict: CHANGES REQUIRED`)
[Critical|Important|Minor] <artefact>:<location> — <problem>

Rules for Severity & Verdict:
- Use `Critical` for a defect that breaks the epic's goal, `Important` for one that must be fixed before merge, and `Minor` for anything else.
- Output `Verdict: CHANGES REQUIRED` if and only if there is at least one `Critical` or `Important` finding.
- If there are no findings (or only `Minor` findings), you MUST output `Verdict: PASS`.
- A review with no finding still ends with its `Verdict: PASS` line.
