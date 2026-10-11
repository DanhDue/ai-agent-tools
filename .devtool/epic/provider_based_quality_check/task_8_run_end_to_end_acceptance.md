---
id: "task_8_run_end_to_end_acceptance"
status: "todo"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T14:22:20+07:00"
completedAt: null
labels: ["quality", "integration", "acceptance", "verification"]
order: "a8"
---

# Task 8: Run End-to-End Acceptance

Epic: [provider_based_quality_check](provider_based_quality_check.en.md)

## Requirement Analysis

Build and run the mandatory Tier C acceptance harness for the complete provider system. Temporary
consumer repositories must cover multiple providers, Rust capability execution, formal lifecycle
inputs, deterministic concurrency, status precedence, missing registration, missing tools, corrupt
results, and SHA drift. The harness must prove the quality run is read-only.

Complete the behavioral GREEN evaluation against the exact Task 1 prompts, run all unit and
governance tests, verify durable documents, and execute the repository's full verification script.
This task does not release or push the kit.

## Relevant Files & Context Pointers

- `skills/quality_check/resources/scripts/test_quality_provider_acceptance.py`
- `skills/quality_check/resources/fixtures/`
- `skills/rust-quality-check/resources/fixtures/`
- `evals/provider_based_quality_check/`
- `scripts/verify.sh`
- `.devtool/epic/provider_based_quality_check/`
- `.devtool/features/`

## Design Rationale

Unit tests prove functions and schemas; only an end-to-end fixture proves registry discovery,
provider fan-out, evidence reconciliation, lifecycle identity, and final reporting work together.
Temporary repositories isolate destructive cases and let SHA changes be modeled without touching
the agent-kit worktree.

Applicable skills: `d3nexus:verification-before-completion`,
`d3nexus:writing-skills`, `d3nexus:quality_check`, and `d3nexus:impact-analysis`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: acceptance harness, complete evaluation results, verification entry
  points, and epic-wide evidence.
- **Downstream callers**: all future consumers; this is the final proof before Gate 4 and Gate 5.
- **Cross-platform bridges**: fixture providers simulate a composite repository without requiring
  mobile SDKs; the Rust fixture uses harmless deterministic commands.
- **Target test coverage threshold**: 100% of HLD use cases and canonical BDD scenarios mapped to a
  passing automated or behavioral result; zero missing traceability entries.

## BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] Composite consumer passes end to end
  Given a temporary repository registers two required providers for epic
  And both return valid PASS evidence for the same SHA
  When the public quality workflow runs
  Then both providers are invoked
  And the unified verdict is PASS for that SHA

Scenario: [Tier C - Integration] Failure precedence survives a blocked peer
  Given one fixture provider reports a quality defect
  And another cannot execute a required tool
  When the complete workflow aggregates results
  Then the final verdict is FAIL
  And both defect and blocker evidence remain visible

Scenario: [Tier C - Integration] Missing registry has no compatibility fallback
  Given a temporary repository contains recognizable Rust and mobile markers
  But has no provider registry
  When the quality workflow runs
  Then it returns BLOCKED
  And no provider is guessed from those markers

Scenario: [Tier C - Integration] Concurrent completion is reproducible
  Given two fixture providers return in changing orders across repeated runs
  When normalized reports are compared
  Then provider and check ordering is identical
  And verdicts and decision traces match

Scenario: [Tier C - Integration] SHA drift and source mutation cannot pass
  Given provider execution begins at the requested SHA
  When a fixture changes HEAD or a provider mutates tracked files
  Then the run is BLOCKED with stale or mutation evidence
  And LGTM is never emitted
```

## Test & Verification Checklist

- [ ] **RED**: run the acceptance harness before integration is complete and capture the expected
      failing seams.
- [ ] **GREEN**: run all canonical success and failure fixtures through public entry points.
- [ ] Verify composite, missing-registry, duplicate, unresolved-provider, empty-selection,
      profile-mismatch, timeout, corrupt-result, and missing-result cases.
- [ ] Verify PASS, FAIL, BLOCKED, optional NOT_APPLICABLE, and required all-NOT_APPLICABLE cases.
- [ ] Verify Rust complete, missing-tool, command-defect, architecture-missing, and threshold cases.
- [ ] Verify profile `epic` from Gate 4 and `pr` from PR review.
- [ ] Verify HEAD drift, tracked-file mutation, deterministic ordering, and preserved evidence.
- [ ] Rerun Task 1's frozen primary selection, including the uncontaminated replacement for the
      registry-leaking historical prompt, and record the comparison.
- [ ] Run document validation for spec, HLD, BDD, and durable EN/VI architecture pairs.
- [ ] Run all Python tests, `git diff --check`, and `scripts/verify.sh`.
- [ ] Confirm the final worktree contains only intended epic changes and no fixture residue.
- [ ] Record exact commands, exits, scenario traceability, and remaining warnings.

## Definition of Done

- Every HLD use case and canonical BDD scenario has passing evidence.
- The before/after behavioral evaluation demonstrates correction of every observed baseline
  failure and preservation of the passing regression controls.
- Full unit, governance, document, and acceptance verification is green.
- Read-only and immutable-SHA invariants are proven end to end.
- Final evidence is sufficient for the new provider-based Gate 4 to judge the implementation.

## Dependencies & Blockers

- Blocked by Tasks [1](task_1_capture_red_behavioral_baseline.md),
  [2](task_2_build_provider_contract_validator.md),
  [3](task_3_build_result_aggregation_engine.md),
  [4](task_4_refactor_quality_check_orchestrator.md),
  [5](task_5_add_rust_quality_provider.md),
  [6](task_6_integrate_lifecycle_consumers.md), and
  [7](task_7_publish_provider_architecture_docs.md).

## References & Rollback

- [Canonical BDD suite](bdd_scenarios.en.md)
- [HLD verification strategy](provider_based_quality_check.en.md#verification-strategy)
- **Rollback**: if acceptance fails, do not publish or integrate the epic. Route findings to the
  owning task, retain failing evidence, and rerun the complete acceptance suite after correction.
