# Provider-Based Quality Check BDD Scenarios

## Table of Contents

- [Purpose and Test Rules](#purpose-and-test-rules)
- [UC1 Direct PR Quality Run](#uc1-direct-pr-quality-run)
- [UC2 Epic Gate Certification](#uc2-epic-gate-certification)
- [UC3 Scheduled and Release Assurance](#uc3-scheduled-and-release-assurance)
- [UC4 Project Provider Registration](#uc4-project-provider-registration)
- [UC5 Rust Quality Execution](#uc5-rust-quality-execution)
- [UC6 Provider Authoring and Aggregation](#uc6-provider-authoring-and-aggregation)
- [Traceability Matrix](#traceability-matrix)

## Purpose and Test Rules

This is the canonical behavioral contract for the `provider_based_quality_check` epic. Scenarios are
derived from the approved design and HLD, not from implementation convenience. Each use case covers
the mandatory five dimensions: happy path, edges and boundaries, state transitions, concurrency or
races, and failures or resilience.

Tags have these meanings:

- `[Tier A - Unit]` maps to validator, aggregator, schema, and provider unit tests.
- `[Tier C - Integration]` maps to temporary-repository or lifecycle acceptance tests.
- A scenario may carry both tags when the same invariant needs local and end-to-end proof.

## UC1 Direct PR Quality Run

```gherkin
Feature: Run a direct PR quality profile

  Scenario: [Tier C - Integration] Happy path uses the PR profile by default
    Given a direct invocation omits the profile and supplies a valid base reference
    And the registry contains two required providers that support pr
    When quality_check normalizes and executes the request
    Then both providers receive profile pr and the same repository SHA
    And a deterministic unified report contains both results

  Scenario: [Tier A - Unit] Edge case rejects an unknown profile
    Given an invocation requests profile quick
    When the invocation contract is validated
    Then the request is BLOCKED with an unsupported-profile reason
    And no provider is invoked

  Scenario: [Tier A - Unit] State transition does not pass before result validation
    Given provider execution has completed
    But one result has not passed schema and identity validation
    When aggregation is requested
    Then the run remains BLOCKED
    And it cannot transition to PASS

  Scenario: [Tier C - Integration] Concurrent providers finish in different orders
    Given two providers execute independently for profile pr
    When they finish in reverse order across two equivalent runs
    Then both reports order providers by stable provider ID
    And both runs produce the same final verdict

  Scenario: [Tier C - Integration] Failure to resolve the base reference is visible
    Given a direct invocation supplies a base reference that does not exist
    When quality_check normalizes changed-file scope
    Then the run is BLOCKED
    And the report names the unresolved base reference
```

## UC2 Epic Gate Certification

```gherkin
Feature: Certify an epic candidate SHA

  Scenario: [Tier C - Integration] Happy path grants LGTM for the certified SHA
    Given dev-implementation requests profile epic with a base reference and candidate SHA
    And every required selected provider returns PASS for that SHA
    When quality_check validates final HEAD and aggregates results
    Then the overall verdict is PASS
    And Gate 4 may render LGTM only for the candidate SHA

  Scenario: [Tier A - Unit] Boundary rejects cheaper PR evidence
    Given Gate 4 requested profile epic
    And a provider result claims profile pr
    When the result identity is validated
    Then that result is rejected
    And the overall verdict is BLOCKED

  Scenario: [Tier A - Unit] Invalid state transition cannot reuse a prior green SHA
    Given a prior epic result passed for SHA A
    And the current candidate is SHA B
    When the prior result is supplied to the current run
    Then validation marks it stale
    And Gate 4 remains BLOCKED

  Scenario: [Tier C - Integration] Repository HEAD changes during execution
    Given all providers start on the requested candidate SHA
    When another process changes HEAD before final validation
    Then all collected results are rejected as stale
    And no LGTM is emitted

  Scenario: [Tier C - Integration] Provider timeout blocks Gate 4
    Given a required epic provider does not return before its configured timeout
    When the orchestrator closes the run
    Then it creates a BLOCKED result for that provider
    And the report preserves completed findings from other providers
```

## UC3 Scheduled and Release Assurance

```gherkin
Feature: Run deeper scheduled and release profiles

  Scenario: [Tier C - Integration] Happy scheduled run includes expensive configured checks
    Given a provider supports scheduled and declares dependency and vulnerability checks
    When the scheduled profile runs
    Then those checks execute in addition to its epic requirements
    And their evidence appears in the provider result

  Scenario: [Tier A - Unit] Empty release capability set is not a false pass
    Given a required provider is registered for release
    And its configuration declares no release checks
    When the provider validates profile completeness
    Then it returns BLOCKED
    And it identifies the missing release capability

  Scenario: [Tier A - Unit] Profile state cannot be upgraded by evidence reuse
    Given cached evidence satisfies epic but not release
    When a release run considers that evidence
    Then the release-only requirements remain pending
    And the run cannot transition to PASS

  Scenario: [Tier C - Integration] Parallel expensive checks keep deterministic output
    Given scheduled dependency and security checks finish concurrently
    When their check records are combined
    Then records are sorted by stable check ID
    And timing order does not change status precedence

  Scenario: [Tier C - Integration] Release API check cannot execute
    Given API compatibility is required for release
    And the configured executable is unavailable
    When the provider runs
    Then the check and provider are BLOCKED rather than NOT_APPLICABLE
    And the final report names the missing executable
```

## UC4 Project Provider Registration

```gherkin
Feature: Register project quality providers

  Scenario: [Tier A - Unit] Happy registry selects every matching provider
    Given a valid registry contains Rust and service providers for profile epic
    When the registry is validated and filtered
    Then both providers appear exactly once in the execution plan
    And the plan is ordered by provider ID

  Scenario: [Tier A - Unit] Duplicate provider IDs are rejected
    Given two registry entries use the same provider ID
    When schema and semantic validation run
    Then the registry is BLOCKED
    And neither provider is invoked

  Scenario: [Tier A - Unit] Registry state is invalid when selection is empty
    Given a valid registry has no provider supporting the requested profile
    When the execution plan is built
    Then plan construction returns BLOCKED
    And it lists the requested profile

  Scenario: [Tier C - Integration] Composite registration never uses first-match detection
    Given a repository contains recognizable files for two ecosystems
    And its registry explicitly selects two providers
    When quality_check runs
    Then both registered providers are invoked
    And repository file order has no effect

  Scenario: [Tier C - Integration] Missing registry fails closed
    Given a consumer repository has no check_quality registry
    When quality_check starts
    Then the run is BLOCKED
    And no legacy platform fallback is attempted
```

## UC5 Rust Quality Execution

```gherkin
Feature: Execute the Rust quality provider

  Scenario: [Tier C - Integration] Happy epic profile runs declared Rust capabilities
    Given rust-quality configuration declares required format, check, lint, test, architecture, and coverage commands
    And every command succeeds at or above its threshold
    When rust-quality-check runs profile epic
    Then it returns PASS with evidence for every required capability
    And the working tree and HEAD are unchanged

  Scenario: [Tier A - Unit] Malformed command arrays are rejected
    Given a Rust capability is configured as an interpolated shell string instead of an argument array
    When configuration validation runs
    Then the provider returns BLOCKED
    And the command is not executed

  Scenario: [Tier A - Unit] Completed defect transitions to FAIL
    Given Clippy executes successfully as a process and reports denied warnings
    When the provider classifies the outcome
    Then the check status is FAIL
    And it is not classified as an infrastructure blocker

  Scenario: [Tier C - Integration] Repository identity race invalidates Rust evidence
    Given Rust commands start on the requested SHA
    When HEAD changes before the provider records finished_head
    Then the provider returns BLOCKED
    And successful command exits cannot restore PASS

  Scenario: [Tier C - Integration] Required architecture command is missing
    Given the epic profile requires feature-first architecture enforcement
    And no project xtask architecture command is configured
    When rust-quality-check validates capabilities
    Then it returns BLOCKED
    And it does not substitute cargo-modules, ArchUnitRust, or syn as authority
```

## UC6 Provider Authoring and Aggregation

```gherkin
Feature: Author providers and aggregate their results

  Scenario: [Tier A - Unit] Happy provider result satisfies the common contract
    Given a provider returns all required fields for the requested identity
    And every evidence reference is well formed
    When result validation runs
    Then the result is accepted for aggregation
    And its checks are sorted by stable check ID

  Scenario: [Tier A - Unit] Unknown result fields are rejected at contract version one
    Given a provider result contains a misspelled status field and an unknown replacement field
    When schema validation runs
    Then the result becomes BLOCKED
    And the misspelled field cannot be silently ignored

  Scenario: [Tier A - Unit] Status precedence preserves failures
    Given one valid provider returns FAIL
    And another valid provider returns BLOCKED
    When statuses are reduced
    Then the overall verdict is FAIL
    And both provider details remain present

  Scenario: [Tier C - Integration] Duplicate results from concurrent delivery are rejected
    Given one selected provider returns two result documents
    When the result set is reconciled with the execution plan
    Then that provider is BLOCKED for duplicate identity
    And aggregation cannot arbitrarily choose one document

  Scenario: [Tier A - Unit] Required all-not-applicable result is blocked
    Given a required provider returns only NOT_APPLICABLE checks
    When applicability evidence is evaluated
    Then the provider is converted to BLOCKED
    And the final verdict cannot be PASS
```

## Traceability Matrix

| Requirement | Scenarios |
|-------------|-----------|
| Direct invocation defaults to `pr` | UC1 happy path |
| Unknown or downgraded profiles fail closed | UC1 edge, UC2 boundary, UC3 state |
| All matching providers run | UC1 happy path, UC4 happy and composite paths |
| Missing manifest or tool is `BLOCKED` | UC4 failure, UC3 and UC5 failures |
| Verdict binds to immutable SHA | UC2 happy, state, and race; UC5 race |
| Deterministic ordering under concurrency | UC1 concurrency, UC3 concurrency, UC6 happy path |
| `FAIL > BLOCKED > PASS` | UC6 precedence |
| Required `NOT_APPLICABLE` cannot pass | UC6 applicability boundary |
| Rust architecture authority is project-owned | UC5 architecture failure |
| Provider output is versioned and strict | UC6 happy and unknown-field paths |
