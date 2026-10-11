# Unified Executive Report Format

## Overview

The quality gate synthesizes all provider findings, coverage metrics, blockers, and warnings into a single
unified executive quality report. The format is designed for both human review in pull requests and automated
certification in Gate 4.

The report renderer is implemented in [aggregate_quality_results.py](../resources/scripts/aggregate_quality_results.py).

## Report Structure

Every report follows a structured layout:

1. **Invocation Metadata**:
   - `Overall Status`: `PASS`, `FAIL`, or `BLOCKED`.
   - `Profile`: The requested profile (`pr`, `epic`, `scheduled`, `release`).
   - `Target SHA`: The immutable 40-character commit SHA certified by this run.
   - `Decision Trace`: Explanatory rationale for the overall verdict.
2. **Providers Summary Table**:
   - Lists every invoked provider, its requirement status (`Yes` / `No`), verdict, duration, and check count.
   - Sorted alphabetically by provider ID.
3. **Coverage Matrix**:
   - Consolidated table of measured coverage versus required thresholds across all providers.
   - Clear `PASS` or `FAIL` indication per dimension.
4. **Blockers Section**:
   - Bulleted list of all critical issues preventing gate approval, tagged with originating provider ID.
5. **Warnings Section**:
   - Bulleted list of non-blocking advisory findings, tagged with originating provider ID.

## Format Stability and Determinism

Provider execution may complete in any order during parallel fan-out. The executive report guarantees
byte-stable output by sorting providers by `provider_id` and checks by check `id`. Permutations in completion
order cannot alter report formatting, findings order, or the final verdict.
