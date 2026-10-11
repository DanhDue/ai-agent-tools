# Result Aggregation Contract

## Overview

The result aggregation engine reduces validated provider results into a single deterministic gate verdict.
The engine consumes normalized data from the contract validator and applies explicit precedence rules
without human or heuristic interpretation.

The implementation is encapsulated in [aggregate_quality_results.py](../resources/scripts/aggregate_quality_results.py)
and verified with [test_aggregate_quality_results.py](../resources/scripts/test_aggregate_quality_results.py).

## Status Precedence Rules

The aggregation engine applies a strict three-state precedence:

$$\text{FAIL} > \text{BLOCKED} > \text{PASS}$$

1. **FAIL Precedence**: If any registered provider reports `FAIL`, the overall run is `FAIL`. Infrastructure blockers are retained and visible in the report, but product defects always outrank them.
2. **BLOCKED Precedence**: If no provider failed, but any required provider reported `BLOCKED` (or was omitted/unreconciled), the overall run is `BLOCKED`.
3. **PASS Requirement**: The overall verdict is `PASS` if and only if every required provider selected for the profile reports `PASS`.
4. **NOT_APPLICABLE Constraints**:
   - An optional provider may be `NOT_APPLICABLE` with valid applicability evidence; it is neutral during reduction.
   - A required provider whose checks are all `NOT_APPLICABLE` is converted to `BLOCKED`. A required provider cannot satisfy Gate 4 with empty or omitted execution.
5. **Warnings**: Warnings never upgrade or downgrade the gate status, but remain visible in the executive report.

## Decision Trace and Auditability

Every aggregated payload includes a `decision_trace` explaining the reduction outcome:

- `FAIL outranks BLOCKED: provider(s) '...' failed while '...' was blocked`
- `Required provider '...' has ...`
- `All required providers passed (N/N)`

The decision trace guarantees that the final verdict is reproducible and understandable weeks after execution.
