# Principal Review: four_persona_governance

## Round 1

- **Date**: 2026-11-17T02:31:20Z
- **SHA**: e009b621de298900e2ddb4251abddf2bb588ce1a
- **Base**: b7383ec
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/four_persona_governance_principal_round1_e009b62.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Critical | .devtool/epic/four_persona_governance/four_persona_governance.en.md:225 (Impact Analysis) | Leaving downstream readers untouched breaks the new `.md` contract: `generate_smoke_checklist.py:191` requires `bdd_scenarios.en.md`; `run_task_checks.py:285` silently loses scenario IDs; `audit_epic.py:223,232` misses scenario and HLD amendments; `lifecycle_runner.py:1624,1664` retains legacy paths. Proposed: extend task ownership and resolver adoption to these readers, with acceptance coverage through task verification and Gate 4. | fixed in 2767c92 |
| 2 | Important | .devtool/epic/four_persona_governance/task_03_runner_personas_risk_routing_and_quota_stops.md:21 (Requirement Analysis) | No requirement implements the promised per-task Architect review. The current `lifecycle_runner.py:789–817` marks a successful Programmer dispatch done without reviewer dispatch or approval. Proposed: explicitly require selective review gating, Architect dispatch, SHA-bound PASS validation and deferred finalization; test reviewer rejection and required-review success. | fixed in 2767c92 |
| 3 | Important | .devtool/epic/four_persona_governance/task_03_runner_personas_risk_routing_and_quota_stops.md:28 (Requirement Analysis) | The fresh `gate4-verifier` contract has no implementation requirement. `lifecycle_runner.py:1527–1705` executes verification directly in the runner. Proposed: require a fresh Programmer verifier dispatch for initial Gate 4 and every post-fix rerun, validating its report against the candidate SHA. | fixed in 2767c92 |
| 4 | Important | .devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md:310 (§5.4 Dispatch) | A read-only fix-planner must write a plan file, while its summary supplies only `plan_path`. Codex dispatch explicitly uses a read-only sandbox (`run_external_review.py:1109`); Task 03 additionally expects a first-line verdict while Task 02 specifies fenced JSON. Proposed: define one response containing verdict, criteria and plan body; assign persistence to the Orchestrator, and align HLD, briefs, parser and BDD. | fixed in 2767c92 |
| 5 | Important | .devtool/epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md:194 (Decisions Already Made) | The prescribed argv does not consistently preserve bindings: Claude and Kiro write commands omit effort; the reused Claude builder rewrites custom model IDs containing “opus” or “sonnet” (`run_external_review.py:1054–1062`); the reused agy command omits the explicit effort required by FPG-HP-05 (`run_external_review.py:1105–1107`). Proposed: define exact model/effort preservation per CLI and mode, allowing adapter changes and testing custom IDs and nondefault efforts. | fixed in 2767c92 |
| 6 | Important | .devtool/epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md:201 (Decisions Already Made) | The failure matcher misclassifies ordinary output such as `FAILED test_quota_check` and `401 failed, 403 passed`, yet misses the actual missing-CLI result `(1, "", "CLI binary 'agy' not found on PATH")` from `lifecycle_runner.py:324–325`. Read-only probes reproduced these mismatches. Proposed: require unsuccessful dispatch, recognize structured spawn failures, and match provider-specific authentication/quota diagnostics; add these counterexamples to FPG-FR-02. | fixed in 2767c92 |
| 7 | Important | .devtool/epic/four_persona_governance/four_persona_governance.en.md:126 (Key Design Mechanics | Quota gate) — The reused evaluator checks provider availability rather than the bound model’s quota. `run_external_review.py:218–225` accepts either Antigravity pool; probes accepted Hydrogen with 0% Gemini quota and healthy Argon quota, and the reverse. Proposed: evaluate the pool consumed by each binding using the existing thresholds, preserving external-review provider selection separately. | fixed in 2767c92 |
| 8 | Important | .devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md:306 (§5.4 Dispatch) | Reusing the command builder does not inherit the claimed Kiro HOME handling. That handling lives in `run_external_review.py:556–577`, while `ModelDispatcher.dispatch` spawns without an environment override (`lifecycle_runner.py:315–323`). Proposed: include subprocess environment preparation in the shared dispatch contract and test Kiro dispatch from an isolated Antigravity profile. | fixed in 2767c92 |
| 9 | Important | .devtool/epic/four_persona_governance/bdd_scenarios.en.md:142 (State Transition Scenarios | FPG-ST-03) — Enabling low-quota mode before wave 2 starts still requires wave 2 to execute, contradicting spec §8.4’s prohibition on starting another wave. Task 03 repeats this assertion. Proposed: require immediate checkpoint and stop before wave 2; add a separate case enabling the flag during an executing wave and draining only that wave. | fixed in 2767c92 |
| 10 | Important | .devtool/epic/four_persona_governance/task_06_four_persona_governance_text.md:99 (BDD SCENARIOS | FPG-AR-03) — The test forbids every occurrence of the old role labels while requiring the migration table that contains those labels. The approved spec §3.2 table contains all three forbidden strings. Proposed: exempt only the canonical migration table from obsolete-vocabulary assertions and apply the same exception to the canonical BDD scenario. | fixed in 2767c92 |
| 11 | Important | .devtool/epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md:35 (Requirement Analysis | CLI writes) — Atomic replacement prevents partial JSON but permits lost updates between concurrent repositories or profiles sharing the global file; one writer can erase another profile’s low-quota flag. Proposed: lock the complete read-modify-validate-replace transaction and add concurrent writers covering independent persona and profile updates. | fixed in 2767c92 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-17T02:39:56Z
- **SHA**: 60408dba54edccab35e9c17087e9f30f432b2650
- **Base**: b7383ec
- **CLI**: codex
- **Model**: gpt-6.1-sol
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Scope**: delta from round 1 (e009b62)
- **Raw log**: `build/reviews/four_persona_governance_principal_round2_60408db.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | .devtool/epic/four_persona_governance/task_01_persona_config_and_dev_config_cli.md:237 (Decisions Already Made) | [INCOMPLETE_FIX] Quota selection still depends on alias rather than the bound model, contrary to HLD Key Design Mechanics §3. A custom alias targeting `gemini-4-argon-high` selects `gemini5h`; the probe accepted 90% Gemini quota despite exhausted Argon quota. Proposed: derive the pool from model identity or validated catalogue metadata; cover custom aliases and replacement of built-in aliases. || fixed in 22e8fc3 |
| 2 | Important | .devtool/epic/four_persona_governance/task_04_english_only_resolution_and_ownership_check.md:35 (Requirement Analysis, Remaining readers) | The mandated filesystem resolver lacks a revision-aware contract for Git-history readers. `integrate_branch.py:273–275` checks documents at `until`, potentially absent from the checkout; `audit_epic.py:232–234` reads both base and HEAD. Checkout resolution misses upstream-only documents and loses the old filename across `.en.md` → `.md` migration. Proposed: specify resolution against each requested Git revision and add upstream-only and cross-revision rename cases to FPG-HP-09. || fixed in 22e8fc3 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
