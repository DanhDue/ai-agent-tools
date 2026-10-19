# Mechanical Verification and Lifecycle Slimming Design

- **Date**: 2026-10-19
- **Status**: Approved at Gate 1
- **Scope**: Mechanical verification in `dev-implementation`, runtime-skill slimming,
  human-facing lifecycle documentation, and regression coverage
- **Next step after approval**: `dev-designer` (epic-scale task breakdown)

## Table of Contents

- [1. Background](#1-background)
- [2. Goals and Non-Goals](#2-goals-and-non-goals)
- [3. Scope](#3-scope)
- [4. Design Decisions](#4-design-decisions)
- [5. Pytest RED Integrity](#5-pytest-red-integrity)
- [6. Python TIER-B Integrity](#6-python-tier-b-integrity)
- [7. Test Integrity Policy Boundary](#7-test-integrity-policy-boundary)
- [8. Lifecycle Skill Slimming](#8-lifecycle-skill-slimming)
- [9. Human Lifecycle Documentation](#9-human-lifecycle-documentation)
- [10. Validation and Testing](#10-validation-and-testing)
- [11. Error Handling](#11-error-handling)
- [12. Risks and Dependencies](#12-risks-and-dependencies)
- [13. Delivery Structure](#13-delivery-structure)

## 1. Background

The `dev-implementation` workflow records a task's RED and verification commands as committed
evidence and later audits that evidence at Gate 4. Two gaps let an agent satisfy the shape of the
contract without proving the intended behavior:

- A pytest RED row with `expect: exit non-zero` can point to a missing file (pytest exit 4) or select
  no tests (pytest exit 5).
- A Python task can claim lint and type safety in its Definition of Done while its `TIER-B` rows run
  only `ruff check`.

The prose that surrounds these checks has also accumulated. `dev-implementation/SKILL.md` is
currently about 7,744 words and `dev-lifecycle/SKILL.md` about 3,990 words. Both contain diagrams or
platform detail that already exists in lifecycle documentation, delegated implementation skills,
or registered quality providers. Adding more prohibitions to these runtime skills increases the
attention burden on smaller models without making the rules mechanically binding.

This design therefore treats hardening and slimming as one reliability change: scripts own
deterministic invariants, providers own platform-specific verification, runtime skills retain only
orchestration and human decisions, and human-facing diagrams live in durable documentation.

## 2. Goals and Non-Goals

**Goals:**

- Reject fake pytest RED runs both when evidence is recorded and when committed evidence is audited.
- Require Python `TIER-B` verification to prove both linting and type checking.
- Make the audit recompute RED validity rather than trusting a recorded `PASS` outcome.
- State the production-code and real-artifact test-integrity rules without claiming unsupported
  cross-language mechanical enforcement.
- Reduce the runtime skills' cognitive load without removing entry-point recovery, approval gates,
  exact validator commands, or fail-closed behavior.
- Keep lifecycle diagrams and developer explanation in the existing synchronized English and
  Vietnamese lifecycle documents.
- Add durable regression coverage for every new mechanical rule and for the skill/document split.

**Non-Goals:**

- Building one generic AST analyzer for Python, Dart, Kotlin, Swift, Rust, and TypeScript.
- Adding a new `test_integrity` provider capability or changing quality-provider schemas in this
  epic. That requires a separate provider-focused design.
- Cryptographically signing task evidence. An agent able to edit both evidence and verifier code
  cannot be defeated by an in-repository signature without an external trust boundary.
- Rewriting the lifecycle sequence, changing gate ownership, or weakening any user approval.
- Creating another lifecycle overview document when `docs/lifecycles.en.md` and `.vi.md` already
  serve that purpose.

## 3. Scope

The developer explicitly expanded the original four-file scope during Gate 1 analysis. The approved
design scope is:

**Mechanical verification:**

- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- The three adjacent regression test files for those scripts

**Runtime skill slimming and policy:**

- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`

**Human documentation and anti-drift checks:**

- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`

No provider skill, provider schema, general quality orchestrator, or unrelated lifecycle document is
modified by this epic.

## 4. Design Decisions

| # | Decision | Reason |
|---|----------|--------|
| D1 | Use an allowlist for pytest RED exit codes: only 1 or 2 can qualify | A denylist of only 4 and 5 leaves internal errors, command-not-found wrappers, and other non-behavioral failures available |
| D2 | Apply negative output markers and require positive pytest failure evidence | A wrapper can rewrite an exit code; output semantics supply a second independent signal |
| D3 | Gate 4 recomputes pytest RED validity from the task row and evidence record | Old or edited evidence must not pass merely because it says `outcome: PASS` |
| D4 | Read Python lint and type-check commands from the registered capability manifest when present, with recognized-tool fallback | The provider manifest is the project's source of truth; fallback supports projects not yet registered without accepting `ruff` alone |
| D5 | Detect Python from task-local evidence, not merely a repository-level `pyproject.toml` | A polyglot repository must not turn every task into a Python task |
| D6 | Keep cross-language test integrity as a mandatory Gate 4 review rule, but do not call it mechanically complete | Reliable import/call and artifact-provenance analysis is language-specific and belongs in providers |
| D7 | Remove diagrams and duplicated platform procedures from runtime skills | These are human explanation or provider-owned detail, not executable agent contracts |
| D8 | Reuse the bilingual `docs/lifecycles.*.md` pair as the human-facing home | Avoids a third source of lifecycle diagrams and preserves English/Vietnamese parity |
| D9 | Preserve gates and recovery rules by positive contract tests, not by retaining duplicate prose | A shorter skill is safe only when mandatory invariants remain mechanically asserted |

## 5. Pytest RED Integrity

### 5.1 Pytest command recognition

A RED row invokes pytest when shell tokenization identifies any of these forms, including executable
paths whose basename matches:

- `pytest`
- `python -m pytest` or `python3 -m pytest`
- common environment wrappers such as `uv run pytest`, `poetry run pytest`, or `pipenv run pytest`

Token-aware recognition avoids counting unrelated text such as `echo pytest`. Invalid shell syntax is
already a command failure and cannot qualify as a valid pytest RED run.

### 5.2 Recording-time verdict

After a pytest RED command finishes, `run_task_checks.py` evaluates the full merged stdout/stderr.
The record is `FAIL` when any of the following is true:

- The exit code is not 1 or 2, including exits 4 and 5.
- Output matches `ERROR: file or directory not found`.
- Output matches `collected 0 items`.
- Output matches `/ 0 selected` with flexible whitespace and case-insensitive comparison.
- Output contains no positive failure summary, such as a non-zero number of failed tests or errors.

The fail-closed `collected 0 items` rule deliberately rejects some collection-time import errors.
When an import failure is the behavior under test, the test must collect and perform that import
inside the test body, producing an assertion or test error rather than relying on zero collection.
This removes the ambiguity between a genuine import contract and an empty test selection.

Every rejection uses the required reason verbatim:

```text
Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), not missing file (exit 4) or zero selected tests (exit 5).
```

The reason is recorded in evidence, printed in the row result, and makes the recorder exit 1.

### 5.3 Gate 4 audit verdict

`audit_epic.py` locates the evidence record for every pytest RED row and reruns the same semantic
validation over the committed fields:

- recorded command and phase;
- recorded exit code;
- recorded output tail;
- recorded outcome.

An invalid semantic result adds the required reason to the Evidence section and makes Gate 4 fail,
even when the JSON outcome says `PASS`. The pytest summary is expected at the end of output, so the
existing evidence tail contains the positive and negative markers needed by the audit.

The recorder and audit use one pure validator to prevent rule drift. The audit still owns the final
Gate 4 finding and failure status; it does not merely repeat the recorded outcome.

## 6. Python TIER-B Integrity

### 6.1 Python task detection

A task is Python-related when its own contract contains at least one local signal:

- An Allowed file with a Python source or Python project filename, such as `.py`, `pyproject.toml`,
  `setup.py`, or `requirements.txt`.
- A verification row invokes pytest, ruff, mypy, pyright, or ty.
- A `TIER-B` row invokes a command registered in `.agents/quality/python-quality.json`.

The presence of a Python file at repository root alone is insufficient.

### 6.2 Required TIER-B capabilities

For a Python task, all `TIER-B` rows are considered together and must directly invoke:

- one linter; and
- one type checker.

Recognized fallback tools are `ruff` for linting and `mypy`, `pyright`, or `ty` for type checking.
Wrapper forms and `python -m <tool>` are recognized through shell tokens rather than substring
matching.

When `.agents/quality/python-quality.json` exists, the validator reads
`capabilities.lint` and `capabilities.type_check`. A row satisfies a registered capability only when
its normalized command directly invokes the registered argument sequence. A generic shell script is
not assumed to call a type checker internally.

Independently of other Python signals, any `TIER-B` row that invokes ruff activates the type-checker
requirement. Missing lint or type-check coverage is a contract problem and makes
`check_task_contract.py` exit 1 before Gate 2 or Gate 3 can pass.

Malformed registered capability JSON is reported as a contract problem rather than silently falling
back. A missing manifest uses recognized-tool fallback because registration is not a prerequisite of
task design in every consuming repository.

## 7. Test Integrity Policy Boundary

`dev-implementation/SKILL.md` retains two concise Gate 4 rules:

- **No Reconstructed Logic in Tests**: unit and integration tests import and invoke the real
  production functions or classes from the task's Allowed files. Reimplementing retry wrappers,
  progress math, or configuration resolution inside tests is a Gate 4 failure.
- **Immutable Real Artifacts**: a test that verifies a real repository artifact copies its input to
  the test's temporary directory before execution and preserves the scenario's anchor values unless
  the scenario explicitly permits synthetic substitution.

These are semantic review requirements. The platform provider and specialist audits must report a
detected violation as `FAIL`, which makes the aggregated quality verdict fail. This epic does not add
a required provider-result field proving that the check ran, so the documentation must not describe
the two rules as complete mechanical enforcement.

A follow-up provider epic may introduce a required `test_integrity` capability with language-specific
implementations. Until then, the universal scripts enforce only what can be derived reliably from
commands, exits, output, evidence, and task contracts.

## 8. Lifecycle Skill Slimming

### 8.1 `dev-lifecycle/SKILL.md`

The runtime orchestrator keeps:

- Stage ownership and routing.
- The five gates and their approvers.
- Handoff Choice and its packaging commands.
- Gate 4 acceptance and Review Choice loop.
- Resume routing, failure routing, and user STOP points.
- The bilingual document contract at the level needed to route work.

It removes:

- The Mermaid lifecycle diagram already present in `docs/lifecycles.*.md`.
- The detailed Mermaid and Graphviz authoring tutorial; durable documents instead must pass the
  existing `doc_quality_check` contract.
- Repeated explanatory prose and red flags that restate an existing hard gate without adding a
  distinct stop condition.

The target is at most 2,500 words, subject to preserving every mechanically asserted lifecycle
invariant.

### 8.2 `dev-implementation/SKILL.md`

The implementation orchestrator keeps:

- Epic resolution, Entry-Point Detection, and Resume Procedure.
- Gate 3 and exact preflight commands.
- Per-task status, RED/verify/status evidence commands, commit, and integration sequence.
- Gate 4, Review Choice, Gate 5, and branch-finishing handoff.
- Non-mechanical STOP conditions such as semantic merge conflicts and user decisions.

It removes:

- The Mermaid process diagram.
- Repeated Flutter, Android, iOS, Web, and Rust Tri-Persona prompt blocks.
- The platform-specific Quick Reference table that omits Python, Rust, and Web.
- Duplicate Common Mistakes and Red Flags after unique stop conditions are consolidated.
- Platform commands already owned by registered providers or required sub-skills.

The Tri-Persona block is replaced by a platform-neutral dispatch contract that supplies the task,
Allowed files, HLD, Covers identifiers, integration roots, TDD requirement, and registered provider
context. The target is at most 4,500 words, again subordinate to preserving asserted behavior.

Both runtime skills link passively to the human lifecycle overview; the link does not instruct an
agent to load the document during normal execution.

## 9. Human Lifecycle Documentation

The existing English and Vietnamese lifecycle documents become the only home for lifecycle diagrams.
English remains canonical; Vietnamese preserves the same structure and facts.

The `dev-lifecycle` section contains:

- The end-to-end Stage 1 through Stage 4 diagram.
- A concise five-gate matrix.
- The Handoff Choice branches.
- The Gate 4 → Review Choice → Gate 5 or cross-model-review loop.
- An interrupted/resume state diagram explaining fresh, packaged, interrupted, completed, and
  inconsistent states.
- The artifact produced at each stage.

Provider internals are not duplicated. The documents link to the existing bilingual quality-provider
architecture pages for that detail.

The documents explicitly say that they describe the lifecycle for humans, while runtime skills and
scripts are the operational source of truth.

## 10. Validation and Testing

### 10.1 Mechanical regression tests

The adjacent unit tests add cases for:

- pytest exits 4 and 5;
- each forbidden output marker;
- a wrapper that rewrites pytest failure to exit 1;
- exit 1 with no positive failure evidence;
- legitimate exit 1 and permitted exit 2 evidence;
- audit rejection of committed evidence whose outcome was changed to `PASS`;
- ruff-only Python `TIER-B` rejection;
- recognized mypy, pyright, and ty commands;
- registered custom lint and type-check commands;
- malformed manifests and polyglot tasks without local Python signals.

Tests create throwaway repositories and commands; they do not depend on pytest being installed in the
kit checkout.

### 10.2 Lifecycle document contract

`scripts/test_lifecycle_document_contract.py` additionally verifies:

- Runtime lifecycle skills contain no Mermaid or DOT fenced blocks.
- Both lifecycle documents contain their expected diagrams.
- English and Vietnamese documents retain the Gate 4, Review Choice, Gate 5, and cross-model rerun
  invariants.
- Runtime skills retain required gate, evidence, resume, and approval tokens after slimming.

The document quality checker validates both lifecycle documents and the new design pair for table of
contents, bilingual structure, links, Markdown, and diagram syntax.

### 10.3 Skill behavior tests

Before and after slimming, the same pressure scenarios cover:

- fresh versus interrupted epic entry;
- refusal to create a worktree before Gate 3;
- a fake pytest RED command;
- Gate 4 PASS followed by Review Choice;
- cross-model review returning to a full Gate 4 run;
- Gate 5 refusal to archive before user approval.

The shortened skill passes only if behavior is preserved or improved. Mechanical repository tests are
the durable regression gate; model samples are supplementary evidence, not a replacement.

Final verification runs targeted unit suites followed by `scripts/verify.sh` and the registered
quality gate appropriate to code and skill changes.

## 11. Error Handling

| Failure | Verdict and action |
|---------|--------------------|
| Pytest RED exits outside 1 or 2 | Recorder `FAIL`; audit `FAIL` with the required reason |
| Pytest RED contains a forbidden zero-test or missing-file marker | Recorder `FAIL`; audit `FAIL` with the required reason |
| Pytest RED has no positive failure summary | Recorder and audit fail closed |
| Python task has no `TIER-B` linter | Task contract `FAIL` |
| Python task has no `TIER-B` type checker | Task contract `FAIL` |
| Registered Python manifest is malformed | Task contract `FAIL`, naming the manifest problem |
| Runtime skill loses a lifecycle invariant during slimming | Lifecycle contract regression test `FAIL` |
| Human diagram loses a required edge or one language drifts | Lifecycle/document contract `FAIL` |
| Provider detects reconstructed test logic or artifact substitution | Provider `FAIL`; aggregate Gate 4 `FAIL` |
| Provider has no mechanical test-integrity capability | This epic makes no mechanical-completeness claim; follow-up remains explicit |

## 12. Risks and Dependencies

- **Pytest output diversity**: plugins can change summaries. The positive patterns must cover standard
  concise and verbose pytest output without accepting an empty run. Unknown output fails closed and
  tells the task author to use a supported reporting form.
- **Shell complexity**: arbitrary shell programs cannot be fully interpreted statically. Token-aware
  recognition plus runtime output validation covers supported direct invocations; intentionally
  opaque wrapper scripts do not count as direct proof.
- **Evidence tampering**: semantic recomputation catches inconsistent fields but cannot provide
  cryptographic provenance without an external trust boundary.
- **Over-slimming**: deleting unique recovery or approval instructions could weaken the lifecycle.
  Positive contract tests and before/after pressure scenarios guard the retained invariants.
- **Documentation drift**: moving diagrams creates a second representation of runtime behavior.
  English-canonical bilingual checks and semantic invariant tests contain that risk.
- **Provider follow-up**: full cross-language test-integrity enforcement depends on a later provider
  contract and language-specific analyzers.

## 13. Delivery Structure

This is one epic with two ordered work packages:

1. **Mechanical verification hardening**: tests first, then recorder, audit, task-contract validation,
   and concise test-integrity policy.
2. **Lifecycle slimming and documentation deduplication**: contract tests first, then runtime-skill
   reduction and synchronized human documentation.

Mechanical hardening lands first so later prose reduction can point to executable enforcement. The
two packages remain separate task groups and commits. Gate 4 runs only after both are complete and
verifies the final candidate SHA in full.
