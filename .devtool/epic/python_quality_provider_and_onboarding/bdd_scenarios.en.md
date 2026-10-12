# BDD Scenarios: Python Quality Provider and Onboarding

## Table of Contents

- [1. Overview and Boundary Matrix](#1-overview-and-boundary-matrix)
- [2. Dimension 1: Happy Paths](#2-dimension-1-happy-paths)
- [3. Dimension 2: Edge Cases and Boundaries](#3-dimension-2-edge-cases-and-boundaries)
- [4. Dimension 3: State Transitions and Invariants](#4-dimension-3-state-transitions-and-invariants)
- [5. Dimension 4: Concurrency and Determinism](#5-dimension-4-concurrency-and-determinism)
- [6. Dimension 5: Failures and Storage Resilience](#6-dimension-5-failures-and-storage-resilience)

---

## 1. Overview and Boundary Matrix

This document formalizes the Behavior-Driven Development (BDD) specification for the Python Quality Provider and automated scaffolding system across Dan Olsen's 5-Dimension Boundary Matrix:

| Dimension | Scope Tested | Target Failure Code / Guarantee |
|---|---|---|
| **1. Happy Paths** | Standard discovery, scaffolding, provider execution, aggregation | `status: PASS`, SHA-bound receipt |
| **2. Edge Cases** | Empty command arrays, boundary coverage percentages | `command_array_empty`, `coverage_deficit` |
| **3. State Transitions** | False-PASS demotion, missing check status consistency | `contract_violation` -> `BLOCKED` |
| **4. Concurrency** | Parallel multi-provider execution order invariance | Deterministic report order |
| **5. Failures & Resilience** | SHA drift, dirty working trees, missing CLI tools | `repository_sha_mismatch`, `ALREADY_EXISTS` |

---

## 2. Dimension 1: Happy Paths

```gherkin
Feature: Python Quality Provider Happy Path Verification

  Scenario: [PY-HP-01] Auto-detect Python workspace and scaffold manifest
    Given a repository containing "pyproject.toml" and "uv.lock"
    When scaffold_quality_manifest.py executes against the repository root
    Then .agents/quality/check_quality.json declares provider "python-core"
    And .agents/quality/python-quality.json is generated with schema_version 1
    And all declared capabilities pass validate_python_quality.py validation

  Scenario: [PY-HP-02] Execute complete Python quality suite with clean results
    Given a clean Python repository with valid formatting, clean lint, strict typing, and passing tests
    When python-quality-check executes profile "pr"
    Then ruff format, ruff check, mypy, and pytest execute cleanly
    And provider-result.json is emitted with status "PASS"
    And provider-result.json is cryptographically bound to the current commit SHA

  Scenario: [PY-HP-03] Polyglot multi-provider aggregation with Python and mobile peers
    Given check_quality.json declaring "python-core" and "flutter-core"
    When both providers return schema-valid provider-result.json with status "PASS"
    Then aggregate_quality_results.py yields aggregate status "PASS"
    And the generated executive report contains status and coverage for both providers
```

---

## 3. Dimension 2: Edge Cases and Boundaries

```gherkin
Feature: Edge Case and Boundary Validations

  Scenario: [PY-EDGE-01] Reject capability declared with empty command array
    Given a python-quality.json where capability "lint" is an empty array []
    When validate_python_quality.py validates the configuration
    Then validation fails with code "command_array_empty"
    And the provider execution halts before running any process

  Scenario: [PY-EDGE-02] Enforce exact line coverage threshold boundary
    Given python-quality.json with coverage threshold set to 0.80
    When pytest coverage reports measured line rate of 0.799
    Then python-quality-check returns finding "coverage_deficit"
    And the provider status is demoted to "BLOCKED"
```

---

## 4. Dimension 3: State Transitions and Invariants

```gherkin
Feature: State Transition and False-PASS Invariant Guards

  Scenario: [PY-ST-01] Demote contradictory provider result to BLOCKED (F1 Guard)
    Given a Python provider result with top-level status "PASS"
    And an individual check "unit_test" reporting status "FAIL"
    When validate_provider_result validates the output
    Then finding "contract_violation" is recorded
    And the aggregate result demotes the provider to status "BLOCKED"

  Scenario: [PY-ST-02] Block provider reporting PASS with sub-threshold coverage (F2 Guard)
    Given a Python provider result reporting status "PASS"
    And measured coverage is 0.65 while threshold is 0.80
    When validate_provider_result validates the output
    Then finding "coverage_deficit" is recorded
    And the provider is marked "BLOCKED" in the final executive summary
```

---

## 5. Dimension 4: Concurrency and Determinism

```gherkin
Feature: Concurrency and Deterministic Concurrency

  Scenario: [PY-CONC-01] Concurrency order does not alter executive report output
    Given providers "python-core" and "rust-core" completing in non-deterministic order
    When aggregate_quality_results.py processes [python, rust] versus [rust, python]
    Then the resulting markdown executive report is byte-for-byte identical
    And provider rows follow stable alphabetic sorting by provider ID
```

---

## 6. Dimension 5: Failures and Storage Resilience

```gherkin
Feature: Failures and Storage Resilience

  Scenario: [PY-FAIL-01] Reject candidate commit SHA drift during execution (F3 Guard)
    Given a quality invocation initiated at commit SHA "aaaa1111"
    When python-quality-check emits provider-result.json bound to "bbbb2222"
    Then the result is rejected with code "repository_sha_mismatch"
    And the pipeline returns status "BLOCKED"

  Scenario: [PY-FAIL-02] Idempotent protection against overwriting existing configs
    Given .agents/quality/check_quality.json already exists in target repository
    When scaffold_quality_manifest.py runs without --force
    Then execution exits with error code 1 and message "already exists"
    And no existing configuration files are modified

  Scenario: [PY-FAIL-03] Report BLOCKED when required CLI tool is absent
    Given a system where "uv" is not installed or executable in PATH
    When python-quality-check attempts capability execution
    Then the provider emits status "BLOCKED" with blocker "tool_missing: uv"
```
