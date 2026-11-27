# Principal Review: polyglot_lifecycle_and_quality_architecture

## Round 1

- **Date**: 2026-11-27T02:33:59Z
- **SHA**: 26c1504c4ac11cfb1179d3fd47a20088b31ce710
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Raw log**: `build/reviews/polyglot_lifecycle_and_quality_architecture_principal_round1_26c1504.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_01_stack_lifecycle_registry.md:Decisions Already Made | The registry contract leaves out symbols that later tasks call: Task 04 calls `TierBContractAdapter.has_provider_manifests(check.root)` and Task 05 calls `TriageSurfaceRegistry.default()`, but neither appears in Task 01 or HLD §Module Contracts 1. The contract also tells the module to reuse `_split_sequential_subcommands` (check_task_contract.py:826) and to invoke `check_python_tier_b` (check_task_contract.py:861, which mutates `Checker`). The registry cannot import either without a circular import, because check_task_contract.py will import the registry. Finally, `validate_tier_b -> list[str]` drops the `where` argument that `Checker.problem(where, text)` needs (check_task_contract.py:80). Proposed: add `has_provider_manifests(repo_root) -> bool` and `TriageSurfaceRegistry.default()` to Task 01 Decisions and HLD §Module Contracts 1; make `validate_tier_b` return `list[tuple[str, str]]` and cover non-Python stacks only; keep the Python path inside check_task_contract.py; have Task 01 own a private stdlib `&&`/`;` splitter, or move the splitter into task_contract.py within Task 04. | fixed in 70b432b |
| 2 | Important | task_04_polyglot_task_contract_and_tier_c_gate.md:Decisions Already Made (Tier B dispatch) | When any `*-quality.json` exists but `python-quality.json` does not (for example a repo with only flutter-quality.json), a `.py` task silently loses the ruff + mypy enforcement that applies today (check_task_contract.py:916-934, reached via check_task_contract.py:1237-1238). Matching on file extensions alone also drops the existing `pyproject.toml`/ruff-row detection in `is_python_task` (check_task_contract.py:625-639). Proposed: always call `check_python_tier_b` when `is_python_task(...)` is true, since it already chooses between the manifest and the fallback itself; route only non-Python stacks through `TierBContractAdapter`; add a test where a repo with only flutter-quality.json and a `.py` task missing its mypy row exits 1. | fixed in 70b432b |
| 3 | Important | task_04_polyglot_task_contract_and_tier_c_gate.md:Decisions Already Made (TierCTaxonomy) | The explicit `Tier C2` hard-fail has no authoring form the row grammar accepts: Phase is a closed set (task_contract.py:162), Expect rejects unknown clauses (task_contract.py:135), and the 5-column row has no annotation cell. PLQ-ST-02 therefore cannot be written deterministically. Proposed: pin one canonical marker, either a trailing `# tier: C2` shell comment in the Command cell (harmless because rows run under `bash -c`, run_task_checks.py:263) or a new `tier C2` Expect clause added to task_contract.py; document it in the Task 06 update to verification-row-grammar.md and use it verbatim in PLQ-ST-02. | fixed in 70b432b |
| 4 | Important | task_04_polyglot_task_contract_and_tier_c_gate.md:Decisions Already Made (check_hld) and Verification V3 | The rule for matching `Integration test roots:` is not specified, and the existing glob helper does not match a bare directory (`_glob_matches("tests", …)` is False, task_contract.py:316-324). Reusing it would hard-fail this epic's own HLD (`Integration test roots: tests`) and `tests/test_token_throttling_acceptance.py:375`, which asserts readiness `R1 PASS` at L540. Several suites drive check_task_contract.py with such fixtures and are missing from V3: tests/test_token_throttling_acceptance.py, tests/test_tto_bilingual_and_surgical.py, tests/test_fpg_english_only_and_ownership.py, scripts/test_verifiable_handoff.py, tests/test_rsdh_orchestration.py, tests/test_ohk2_skill_docs.py, test_sync_task_status.py and test_inter_epic_dependencies.py. Proposed: state that a root matches when any tracked or created path equals it or starts with `root.rstrip('/') + '/'`; add these suites to Task 04 V3. | fixed in 70b432b |
| 5 | Important | task_01_stack_lifecycle_registry.md:Decisions Already Made (PoolWorkspaceStrategy defaults) | The `cow_copy` defaults include `*.xcconfig`, `ios/Flutter/*.xcconfig` and `macos/Flutter/*.xcconfig`, which match the tracked `Debug.xcconfig`/`Release.xcconfig` in a standard Flutter project. Task 01 does not carry the spec's "ignored by git" condition (spec L163). Task 05 then excludes every resolved mount from snapshots and triage and unstages it in `finalize_slot`, so a legitimate edit to a tracked xcconfig or `local.properties` is silently dropped from the slot commit. Proposed: require each `cow_copy` candidate to pass `git check-ignore` and be absent from `git ls-files`; have `get_excluded_relpaths` return only paths that were actually materialized; add a PLQ-ST-04 variant proving an edited tracked `ios/Flutter/Debug.xcconfig` gets committed. | fixed in 70b432b |
| 6 | Important | 2026-11-27-polyglot-lifecycle-and-quality-architecture-design.md:Component 1 §3 TriageSurfaceRegistry (and task_01 Decisions) | Strict suffix scoping removes Tier 1 detections the current global rules provide (manage_worker_pool.py:79-109): Dart/Kotlin `class` declarations, raw SQL inside Dart/Swift, Dart `Lock()`, and any suffix outside the 6 stacks such as `.sql` migrations. A high-risk fix under 30 lines would then return `ELIGIBLE_FOR_SHORT_CIRCUIT`. Proposed: keep a language-neutral baseline (SQL DDL/DML, `class` declarations, lock constructors) applied to every suffix, unknown ones included, and layer the stack rules on top; add BDD rows proving that a `.sql` `ALTER TABLE` and a Dart `class` change still fire. AR-01's cross-language strings stay unaffected. | fixed in 70b432b |
| 7 | Important | task_03_quality_schemas_validators_and_scaffolder.md:Decisions Already Made (Compact CLI output) | With a compact default, `PASS` output from `validate_quality_contract.py registry` no longer includes the selected `providers` (validate_quality_contract.py:195-199), which quality_check Step 1 (skills/quality_check/SKILL.md:74) needs for its Step 2 fan-out. The `reconcile` payload used at SKILL.md:109 is lost the same way, and no task adds `--json` to those commands. Proposed: keep JSON as the default stdout for the payload-producing subcommands `registry`, `invocation` and `reconcile`, and apply the compact form only to `capability`, `result` and the 6 provider validators; otherwise have Task 06 Decisions add `--json` to SKILL.md:74 and SKILL.md:109. | fixed in 70b432b |
| 8 | Minor | polyglot_lifecycle_and_quality_architecture.md:Meta Data | Status still reads "Pending Task Breakdown Confirmation & Gate 2", but 26c1504 records Gate 2. Proposed: update Status to Gate 2 Approved. | fixed in 70b432b |
| 9 | Minor | 2026-11-27-polyglot-lifecycle-and-quality-architecture-design.md:Component 1 §2 | Spec L166 has `get_excluded_relpaths(slot_path, main_wt)`, but HLD L125 and Task 05 use `(main_wt, slot_path)`. Proposed: align the spec to `(main_wt, slot_path)`. | fixed in 70b432b |
| 10 | Minor | 2026-11-27-polyglot-lifecycle-and-quality-architecture-design.md:Component 3 §2 | "4 Profiles across all 6 schemas" reads as a new addition, but the flutter, rust, python, android and ios schemas already declare pr/epic/scheduled/release with `required: ["pr","epic"]`. Proposed: reword it as a web-only addition that keeps existing parity. | fixed in 70b432b |
| 11 | Minor | task_06_lifecycle_docs_provider_skills_and_acceptance.md:Impact Analysis & Blast Radius | Cites `SUITES` at L475-L490, but the list spans scripts/verify.sh:362-482. Proposed: correct the anchor. | fixed in 70b432b |
| 12 | Minor | task_01_stack_lifecycle_registry.md:Decisions Already Made (.kt signature) | `(?:suspend\s+)?fun\s+` fires on `private fun` (probe), so nearly every Kotlin fix routes to HIGH_RISK. Proposed: exclude `private` declarations or narrow the pattern to public/internal API. | fixed in 70b432b |
| 13 | Minor | task_06_lifecycle_docs_provider_skills_and_acceptance.md:Decisions Already Made | skills/setup_quality_check/SKILL.md:26 still lists `pkill -9 java` but is not named as a removal target. Proposed: name it explicitly beside android-quality-check/SKILL.md:59. | fixed in 70b432b |

Raw output:

```text
Verdict: CHANGES REQUIRED
```

## Round 2

- **Date**: 2026-11-27T02:39:26Z
- **SHA**: 756c6ec0daea1027aaf0a8a795d7274c722d491f
- **Base**: main
- **CLI**: claude
- **Model**: Opus 5.5
- **Thinking**: high
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal
- **Scope**: delta from round 1 (26c1504)
- **Raw log**: `build/reviews/polyglot_lifecycle_and_quality_architecture_principal_round2_756c6ec.raw.log`

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_04_polyglot_task_contract_and_tier_c_gate.md:Requirement Analysis item 1 and DoD | [INCOMPLETE_FIX #2] Still described check_python_tier_b as running only when zero manifests exist instead of always running when is_python_task is true. | fixed in 32affe7 |
| 2 | Important | task_03_quality_schemas_validators_and_scaffolder.md:Requirement Analysis item 2 and DoD | [INCOMPLETE_FIX #7] Still stated all 7 validator CLIs emit 1-line PASS by default instead of preserving JSON default stdout on registry/invocation/reconcile. | fixed in 32affe7 |
| 3 | Minor | task_04_polyglot_task_contract_and_tier_c_gate.md:Requirement Analysis item 2 and DoD | Still named generic Tier C2 instead of canonical `# tier: C2` command comment marker. | fixed in 32affe7 |
| 4 | Minor | 2026-11-27-polyglot-lifecycle-and-quality-architecture-design.md & polyglot_lifecycle_and_quality_architecture.md | Spec Component 1/Risks and HLD Goals still echoed Round 1 Python fallback and Tier C2 phrasing. | fixed in 32affe7 |

Raw output:

```text
Verdict: CHANGES REQUIRED
```
