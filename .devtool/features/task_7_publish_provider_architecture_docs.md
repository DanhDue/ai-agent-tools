---
id: "task_7_publish_provider_architecture_docs"
status: "done"
priority: "medium"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T18:22:27Z"
completedAt: "2026-10-11T18:22:27Z"
labels: ["quality", "documentation", "architecture", "migration"]
order: "a7"
---

# Task 7: Publish Provider Architecture Documentation

Epic: [provider_based_quality_check](../epic/provider_based_quality_check/provider_based_quality_check.en.md)

## Requirement Analysis

Publish synchronized English and Vietnamese durable documentation explaining the provider system to
consumer-project maintainers and provider authors. Cover registry setup, provider invocation and
result contracts, status semantics, profile selection, Rust capabilities, the Konsist-equivalent
architecture mechanism, multi-provider composition, evidence, troubleshooting, and the fail-closed
migration.

The documents must clearly state that Android, iOS, and Flutter templates will register their
providers in later platform-owned work. They must not imply a legacy platform fallback exists.

## Relevant Files & Context Pointers

- `docs/architecture/quality-provider-system.en.md`
- `docs/architecture/quality-provider-system.vi.md`
- `README.md` — link to the architecture documents if its structure supports it
- `skills/quality_check/references/`
- `skills/rust-quality-check/references/`
- `skills/doc_quality_check/resources/scripts/check_document.py`
- `scripts/verify.sh`

## Design Rationale

Skill files should remain operational and compact. Durable documents carry conceptual architecture,
consumer examples, provider-authoring rules, and migration guidance. The English document is
canonical for tooling; the Vietnamese document stays structurally and factually synchronized.

Applicable skills: `d3nexus:doc_quality_check`, `d3nexus:writing-skills`, and
`d3nexus:verification-before-completion`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: bilingual architecture documents and repository navigation links.
- **Downstream callers**: consumer project owners, future Android/iOS/Flutter provider authors, and
  agents remediating BLOCKED registration.
- **Cross-platform bridges**: documents define the common bridge contract but do not implement any
  platform provider.
- **Target test coverage threshold**: 100% linked ToC coverage, matching EN/VI heading structures,
  all examples schema-valid, and every local link resolvable.

## BDD SCENARIOS

```gherkin
Scenario: [Tier A - Unit] Consumer registers a Rust provider from the guide
  Given a maintainer follows the English registry example
  When the example is validated by the contract validator
  Then it is schema-valid
  And it selects rust-quality-check for the documented profiles

Scenario: [Tier A - Unit] Vietnamese documentation stays structurally synchronized
  Given the English and Vietnamese architecture documents
  When bilingual document validation runs
  Then their heading structures match
  And both linked tables of contents are complete

Scenario: [Tier A - Unit] Migration state is unambiguous
  Given a project has not added check_quality.json
  When a maintainer reads the migration section
  Then the documented outcome is BLOCKED
  And no fallback or skip-as-pass path is promised

Scenario: [Tier C - Integration] Multi-provider example validates end to end
  Given the guide contains a composite registry and provider result examples
  When the acceptance harness loads those examples
  Then every provider is selected and validated
  And the documented aggregate verdict matches the engine

Scenario: [Tier C - Integration] Missing required tool troubleshooting stays fail closed
  Given a Rust required executable is missing
  When a maintainer follows the troubleshooting decision tree
  Then the expected status remains BLOCKED
  And the guide does not recommend disabling or bypassing the check
```

## Test & Verification Checklist

**TDD adaptation**: documentation behavior is proven with executable examples and document gates
rather than production unit code.

- [x] **RED**: identify current repository guidance that cannot explain Rust registration or
      multi-provider execution.
- [x] Draft the English document from the implemented contract, then translate it to Vietnamese.
- [x] Include schema-valid single-provider and composite-provider examples.
- [x] Include profile, evidence, status, SHA, troubleshooting, migration, and provider-authoring
      sections.
- [x] Explain Cargo metadata plus project `xtask` as the architecture authority and label optional
      Rust tools accurately.
- [x] Run bilingual ToC, link, placeholder, Markdown, and Mermaid checks.
- [x] **Tier B**: validate embedded JSON examples and cross-reference consistency from
      `scripts/verify.sh`.
- [x] **Tier C**: load the documented examples through validator and aggregator acceptance tests.

## Definition of Done

- EN/VI architecture documents are complete, synchronized, navigable, and discoverable.
- Registration and provider-authoring examples pass executable validation.
- Breaking migration and future mobile-template responsibility are explicit.
- No documentation recommends bypassing a BLOCKED quality prerequisite.
- Document quality checks and full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 4](task_4_refactor_quality_check_orchestrator.md),
  [Task 5](task_5_add_rust_quality_provider.md), and
  [Task 6](task_6_integrate_lifecycle_consumers.md).
- Blocks [Task 8](task_8_run_end_to_end_acceptance.md).

## References & Rollback

- [Approved migration design](../epic/provider_based_quality_check/2026-10-11-provider-based-quality-check-design.en.md#migration-and-compatibility)
- [HLD rollout strategy](../epic/provider_based_quality_check/provider_based_quality_check.en.md#rollout-strategy-and-mitigation)
- **Rollback**: remove documents only if the provider system is also reverted. Documentation must
  never describe a contract unavailable in the released skills.

