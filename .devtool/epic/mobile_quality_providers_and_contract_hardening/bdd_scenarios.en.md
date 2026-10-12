# BDD Behavioral Test Scenarios: Mobile Quality Providers and Contract Hardening

## Table of Contents

- [1. Overview and Boundary Dimension Matrix](#1-overview-and-boundary-dimension-matrix)
- [2. Use Case 1: Repository Onboarding and Scaffolding](#2-use-case-1-repository-onboarding-and-scaffolding)
  - [2.1. Dimension 1: Happy Paths](#21-dimension-1-happy-paths)
  - [2.2. Dimension 2: Edge Cases and Boundaries](#22-dimension-2-edge-cases-and-boundaries)
  - [2.3. Dimension 3: State Transitions](#23-dimension-3-state-transitions)
  - [2.4. Dimension 4: Async and Concurrency](#24-dimension-4-async-and-concurrency)
  - [2.5. Dimension 5: Failures and Environmental Resilience](#25-dimension-5-failures-and-environmental-resilience)
- [3. Use Case 2: End-of-Epic Gate 4 Verification](#3-use-case-2-end-of-epic-gate-4-verification)
  - [3.1. Dimension 1: Happy Paths](#31-dimension-1-happy-paths)
  - [3.2. Dimension 2: Edge Cases and Boundaries](#32-dimension-2-edge-cases-and-boundaries)
  - [3.3. Dimension 3: State Transitions](#33-dimension-3-state-transitions)
  - [3.4. Dimension 4: Async and Concurrency](#34-dimension-4-async-and-concurrency)
  - [3.5. Dimension 5: Failures and Environmental Resilience](#35-dimension-5-failures-and-environmental-resilience)
- [4. Use Case 3: Pull Request Review Profiling](#4-use-case-3-pull-request-review-profiling)
  - [4.1. Dimension 1: Happy Paths](#41-dimension-1-happy-paths)
  - [4.2. Dimension 2: Edge Cases and Boundaries](#42-dimension-2-edge-cases-and-boundaries)
  - [4.3. Dimension 3: State Transitions](#43-dimension-3-state-transitions)
  - [4.4. Dimension 4: Async and Concurrency](#44-dimension-4-async-and-concurrency)
  - [4.5. Dimension 5: Failures and Environmental Resilience](#45-dimension-5-failures-and-environmental-resilience)
- [5. Use Case 4: Engine Contract Hardening and Anti-False-PASS](#5-use-case-4-engine-contract-hardening-and-anti-false-pass)
  - [5.1. Dimension 1: Happy Paths](#51-dimension-1-happy-paths)
  - [5.2. Dimension 2: Edge Cases and Boundaries](#52-dimension-2-edge-cases-and-boundaries)
  - [5.3. Dimension 3: State Transitions](#53-dimension-3-state-transitions)
  - [5.4. Dimension 4: Async and Concurrency](#54-dimension-4-async-and-concurrency)
  - [5.5. Dimension 5: Failures and Environmental Resilience](#55-dimension-5-failures-and-environmental-resilience)

---

## 1. Overview and Boundary Dimension Matrix

This document defines the exhaustive BDD Gherkin test suite for the `mobile_quality_providers_and_contract_hardening` epic. Every scenario adheres strictly to the **Mandatory 5-Dimension Boundary Matrix**:
1. **Happy Paths**: Nominal executions with standard payloads and expected success states.
2. **Edge Cases & Boundaries**: Boundary thresholds, zero/empty structures, and multi-provider compositions.
3. **State Transitions**: Valid and invalid lifecycle transitions across invocation, execution, and aggregation.
4. **Async & Concurrency**: Parallel provider executions, race conditions, and SHA stability guards.
5. **Failures & Environmental Resilience**: Missing executables, malformed schemas, and process timeouts.

---

## 2. Use Case 1: Repository Onboarding and Scaffolding

### 2.1. Dimension 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Auto-scaffold Flutter repository manifests
  Given a clean Flutter repository root containing pubspec.yaml with workspace configuration
  When the developer executes setup_quality_check
  Then .agents/quality/check_quality.json is created with flutter-core provider
  And .agents/quality/flutter-quality.json is generated with format, analyze, boundaries, test, and audits capabilities
  And the initial baseline verification run succeeds with status PASS
```

```gherkin
Scenario: [Tier C - Integration] Auto-scaffold Android repository manifests
  Given a clean Android repository root containing build.gradle.kts and settings.gradle.kts
  When the developer executes setup_quality_check
  Then .agents/quality/check_quality.json is created with android-core provider
  And .agents/quality/android-quality.json is generated declaring Konsist, BCV, Detekt, and test capabilities
  And the initial baseline verification run succeeds with status PASS
```

### 2.2. Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [Tier A - Unit] Scaffolding a polyglot composite repository
  Given a repository containing both Cargo.toml and pubspec.yaml
  When setup_quality_check is executed
  Then .agents/quality/check_quality.json declares both rust-core and flutter-core providers
  And both providers are configured with required=true for the epic profile
```

### 2.3. Dimension 3: State Transitions

```gherkin
Scenario: [Tier C - Integration] Idempotent re-scaffolding without clobbering existing configuration
  Given a repository where .agents/quality/check_quality.json already exists with custom thresholds
  When setup_quality_check is re-executed without --force
  Then the existing manifests remain unmodified
  And a notification informs the user that configuration is already present
```

### 2.4. Dimension 4: Async and Concurrency

```gherkin
Scenario: [Tier A - Unit] Concurrent scaffolding invocation race condition
  Given two parallel agent invocations trigger setup_quality_check simultaneously
  When file writes are executed with atomic write and replace operations
  Then the final manifest files are valid and contain zero corrupted JSON content
```

### 2.5. Dimension 5: Failures and Environmental Resilience

```gherkin
Scenario: [Tier A - Unit] Unknown repository platform detection failure
  Given a repository containing no recognizable platform indicators
  When setup_quality_check is executed
  Then the tool halts with status BLOCKED
  And actionable error output lists the supported platforms (Rust, Flutter, Android, iOS)
```

---

## 3. Use Case 2: End-of-Epic Gate 4 Verification

### 3.1. Dimension 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Successful Gate 4 certification on Flutter repository
  Given a completed epic worktree on a Flutter repository
  And .agents/quality/check_quality.json declares required flutter-core provider
  When @quality_check is invoked with profile="epic" and candidate SHA
  Then flutter-quality-check executes format, analyze, boundaries, unit tests, coverage, and 4 audits
  And all checks return status PASS with coverage exceeding 80%
  And quality_check issues 🟢 LGTM approval bound to the candidate SHA
```

```gherkin
Scenario: [Tier C - Integration] Successful Gate 4 certification on Android repository
  Given a completed epic worktree on an Android repository
  And .agents/quality/check_quality.json declares required android-core provider
  When @quality_check is invoked with profile="epic" and candidate SHA
  Then android-quality-check executes Konsist K1-K10, BCV apiCheck, Detekt, unit tests, and acceptance harness
  And all checks return status PASS
  And cleanup-java terminates all background Gradle daemons
  And quality_check issues 🟢 LGTM approval bound to the candidate SHA
```

### 3.2. Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [Tier A - Unit] Composite repository requires full consensus across all platforms
  Given a composite workspace declaring rust-core and android-core providers
  When @quality_check runs for profile="epic"
  And rust-core returns PASS
  But android-core returns FAIL due to a Konsist architecture boundary violation
  Then the overall aggregated verdict is FAIL
  And Gate 4 approval is rejected
```

### 3.3. Dimension 3: State Transitions

```gherkin
Scenario: [Tier C - Integration] Rejection of un-profiled invocation during formal Gate 4
  Given an automated lifecycle caller invokes @quality_check
  When the profile argument is omitted
  Then the orchestrator rejects the request with status BLOCKED
  And requires explicit profile="epic" for lifecycle verification
```

### 3.4. Dimension 4: Async and Concurrency

```gherkin
Scenario: [Tier A - Unit] Rejection of stale evidence when candidate SHA drifts
  Given a verification run begins on candidate commit SHA "1111111"
  When a background process or agent commits a modification changing HEAD to "2222222" before provider completion
  Then the orchestrator detects SHA drift
  And rejects all collected evidence as stale with status BLOCKED
```

### 3.5. Dimension 5: Failures and Environmental Resilience

```gherkin
Scenario: [Tier A - Unit] Missing required compiler or CLI tool
  Given an iOS project declaring swiftformat capability
  When swiftformat is absent from the host PATH
  Then ios-quality-check returns status BLOCKED
  And the report lists "missing executable: swiftformat" in blockers
```

---

## 4. Use Case 3: Pull Request Review Profiling

### 4.1. Dimension 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Fast PR review execution on touched scope
  Given a feature branch diff targeting develop
  When @pr_review invokes @quality_check with profile="pr"
  Then the selected provider executes fast formatting, compilation, lint, and touched unit tests
  And expensive full workspace integration suites are omitted
  And a concise PR review report is rendered with inline findings
```

### 4.2. Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [Tier A - Unit] Attempting to satisfy Gate 4 using PR profile evidence
  Given evidence collected from a previous profile="pr" run
  When @dev-implementation Gate 4 requests profile="epic"
  Then the orchestrator refuses to reuse the pr evidence
  And requires a complete epic profile execution
```

### 4.3. Dimension 3: State Transitions

```gherkin
Scenario: [Tier C - Integration] PR review transitions from clean PASS to CHANGES REQUESTED on lint defect
  Given a PR with a newly introduced Detekt code smell
  When @pr_review runs with profile="pr"
  Then android-quality-check reports check status FAIL for Detekt
  And pr_review renders 🔴 CHANGES REQUESTED detailing the failing line numbers
```

### 4.4. Dimension 4: Async and Concurrency

```gherkin
Scenario: [Tier A - Unit] Parallel provider dispatch during PR review
  Given a repository with two independent providers selected for profile="pr"
  When @quality_check fans out invocations
  Then both providers execute in parallel
  And output aggregation deterministically sorts findings by provider ID
```

### 4.5. Dimension 5: Failures and Environmental Resilience

```gherkin
Scenario: [Tier A - Unit] Base ref resolution failure
  Given a PR review invoked without explicit base_ref where git cannot determine merge-base
  When @quality_check runs
  Then the orchestrator halts with status BLOCKED
  And prompts the caller to provide an explicit base_ref
```

---

## 5. Use Case 4: Engine Contract Hardening and Anti-False-PASS

### 5.1. Dimension 1: Happy Paths

```gherkin
Scenario: [Tier A - Unit] Valid provider result passes hardened validation
  Given a provider result document matching provider-result.schema.json
  And all checks report status PASS with matching evidence references
  And line coverage is 0.88 with configured threshold 0.80
  When validate_quality_contract.py validates the result
  Then validation passes with exit code 0
```

### 5.2. Dimension 2: Edge Cases and Boundaries

```gherkin
Scenario: [Tier A - Unit] Anti-False-PASS: Provider PASS with contained check FAIL is strictly rejected
  Given a provider result declaring top-level status="PASS"
  But one check inside checks array reports status="FAIL"
  When validate_quality_contract.py validates the result
  Then validation rejects the document with error "CONTRACT_VIOLATION"
  And the result status is converted to BLOCKED
```

```gherkin
Scenario: [Tier A - Unit] Anti-False-PASS: Provider PASS with sub-threshold coverage is strictly rejected
  Given a provider result declaring top-level status="PASS"
  And coverage threshold is configured as 0.85
  But measured coverage is reported as 0.10
  When validate_quality_contract.py validates the result
  Then validation rejects the document with error "COVERAGE_DEFICIT"
  And top-level status cannot remain PASS
```

### 5.3. Dimension 3: State Transitions

```gherkin
Scenario: [Tier A - Unit] Reconcile CLI rejects stale SHA in result documents
  Given an execution plan targeting SHA "aaaaaaa"
  When reconcile is invoked with a result document containing started_head="bbbbbbb"
  Then reconcile halts with error "SHA_MISMATCH" and non-zero exit code
```

### 5.4. Dimension 4: Async and Concurrency

```gherkin
Scenario: [Tier A - Unit] Aggregation handles conflicting provider results deterministically
  Given Provider A reports FAIL on unit tests
  And Provider B reports BLOCKED due to a missing optional tool
  When aggregate_quality_results.py reduces the verdicts
  Then overall status is FAIL because FAIL outranks BLOCKED
  And both the test failure and the missing tool blocker remain visible in the report
```

### 5.5. Dimension 5: Failures and Environmental Resilience

```gherkin
Scenario: [Tier A - Unit] Capability schema rejects empty profile command arrays
  Given a capability JSON declaring capability "test" with an empty command array []
  When validate_quality_contract.py validates the capability manifest
  Then validation halts with schema error "COMMAND_ARRAY_EMPTY"
```
