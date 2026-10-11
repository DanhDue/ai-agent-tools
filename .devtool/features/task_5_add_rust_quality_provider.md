---
id: "task_5_add_rust_quality_provider"
status: "todo"
priority: "high"
assignee: null
epic: "provider_based_quality_check"
dueDate: null
created: "2026-10-11T14:22:20+07:00"
modified: "2026-10-11T14:22:20+07:00"
completedAt: null
labels: ["quality", "rust", "skill", "architecture"]
order: "a5"
---

# Task 5: Add the Rust Quality Provider

Epic: [provider_based_quality_check](../epic/provider_based_quality_check/provider_based_quality_check.en.md)

## Requirement Analysis

Create `d3nexus:rust-quality-check` as a read-only provider implementing the common contract. Define
the version-one `.agents/quality/rust-quality.json` capability model and map the four common
profiles to project-declared commands and thresholds. The provider must distinguish completed
quality failures from inability to execute or prove a check.

Document the Rust equivalent of Android quality tooling and define Cargo metadata plus a
project-owned `xtask` architecture command as the authoritative Konsist-equivalent boundary.
`cargo-modules`, ArchUnitRust, and `syn` remain optional supplements, not silent substitutes.

## Relevant Files & Context Pointers

- `skills/rust-quality-check/SKILL.md`
- `skills/rust-quality-check/references/rust-capability-contract.md`
- `skills/rust-quality-check/references/rust-architecture-governance.md`
- `skills/rust-quality-check/references/rust-tool-mapping.md`
- `skills/rust-quality-check/resources/schemas/rust-quality.schema.json`
- `skills/rust-quality-check/resources/fixtures/`
- `evals/provider_based_quality_check/`
- `scripts/verify.sh`

## Design Rationale

Rust workspaces differ too much for a central command list. A capability file lets each project
declare its actual format, lint, test, coverage, security, architecture, WASM, FFI, acceptance, and
compatibility commands while the provider preserves common status semantics. Cargo metadata exposes
the workspace dependency graph; the project's `xtask` owns semantic rules for feature-first Clean
Architecture, MVI, dependency injection, navigation, and service boundaries.

Applicable skills: `d3nexus:writing-skills`, `d3nexus:test-driven-development`,
`d3nexus:architecture-audit`, `d3nexus:security-audit`, and
`d3nexus:code-health-audit`.

## Impact Analysis & Blast Radius

- **Target files & symbols**: new Rust skill, capability schema, profile planner, outcome
  classification, architecture guidance, and evidence mapping.
- **Downstream callers**: Rust consumer registries and the platform-neutral orchestrator.
- **Cross-platform bridges**: FFI and WASM checks are declared capabilities; their contracts remain
  owned by the consumer repository.
- **Target test coverage threshold**: 100% scenario coverage for required capability and outcome
  classification; 100% for security-related required-tool failure paths.

## BDD SCENARIOS

```gherkin
Scenario: [Tier C - Integration] Epic profile passes complete Rust capabilities
  Given valid Rust configuration declares every capability required by epic
  And each read-only command succeeds with valid evidence
  When rust-quality-check executes the profile
  Then the provider result is PASS
  And started_head, finished_head, and repository_sha match

Scenario: [Tier A - Unit] Shell-string commands are rejected
  Given a capability command is not a structured argument array
  When configuration validation runs
  Then the provider is BLOCKED
  And no implicit shell interpolation occurs

Scenario: [Tier A - Unit] Completed lint defect is FAIL
  Given a configured Clippy process runs and reports denied warnings
  When the outcome is classified
  Then the check is FAIL
  And the failure is not mislabeled as missing infrastructure

Scenario: [Tier C - Integration] Independent Rust checks may run concurrently
  Given format, lint, tests, and architecture checks do not mutate shared state
  When the provider schedules them concurrently
  Then every required check returns one record
  And check ordering in the result remains deterministic

Scenario: [Tier C - Integration] Missing architecture authority blocks the epic profile
  Given architecture enforcement is required
  But no project xtask architecture command is configured
  When the provider builds the epic plan
  Then the provider returns BLOCKED
  And no diagnostic-only tool is promoted to authority
```

## Test & Verification Checklist

- [ ] **RED**: rerun Rust-related Task 1 pressure cases before authoring provider instructions.
- [ ] **RED**: add failing schema/fixture tests for every capability and profile-completeness rule.
- [ ] **GREEN**: add the minimal skill, references, schema, and planner required by the contract.
- [ ] **REFACTOR**: keep `SKILL.md` operational and place tool matrices and architecture detail in
      references.
- [ ] Verify format, check, Clippy, tests, coverage, dependency policy, vulnerability audit,
      architecture, WASM, FFI, acceptance, docs, and semver capabilities.
- [ ] Verify required missing tool/config/evidence is BLOCKED and completed defect is FAIL.
- [ ] Verify commands are read-only structured arrays and HEAD/worktree identity is recorded.
- [ ] Verify semantic audits cover security, architecture, presentation, and code health when
      declared by the profile.
- [ ] **Tier B**: verify exact skill frontmatter, namespaced references, schemas, and no auto-fix
      instruction.
- [ ] **Tier C**: run valid, missing-tool, failing-check, missing-architecture, and SHA-drift Rust
      fixture repositories.

## Definition of Done

- The Rust provider implements the shared invocation and result contracts.
- All four profiles are capability-driven and fail closed.
- The Konsist-equivalent architecture boundary is explicit and project-owned.
- Tool mappings distinguish authoritative gates from optional diagnostics.
- Provider evaluation, schema tests, fixtures, and full repository verification pass.

## Dependencies & Blockers

- Blocked by [Task 1](task_1_capture_red_behavioral_baseline.md),
  [Task 2](task_2_build_provider_contract_validator.md), and
  [Task 3](task_3_build_result_aggregation_engine.md).
- May run in parallel with Task 4 after Task 3 because their authored file sets are disjoint.
- Blocks [Task 6](task_6_integrate_lifecycle_consumers.md),
  [Task 7](task_7_publish_provider_architecture_docs.md), and
  [Task 8](task_8_run_end_to_end_acceptance.md).

## References & Rollback

- [HLD Rust architecture](../epic/provider_based_quality_check/provider_based_quality_check.en.md#contracts-and-state-model)
- [Rust BDD scenarios](../epic/provider_based_quality_check/bdd_scenarios.en.md#uc5-rust-quality-execution)
- **Rollback**: remove the Rust provider registration capability from the kit. Consumer projects
  must remain BLOCKED rather than silently falling back if they still name the removed provider.
