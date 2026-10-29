# Principal Review: setup_shared_contracts

## Round 1

- **Date**: 2026-10-29T23:08:06Z
- **SHA**: fc3733a701ac3a7f2d58f91464fe780cdcc6e72f
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | 2026-10-30-setup-shared-contracts-design.en.md:§4/§6 (Directory Structure / Canonical Template Bundles) | template filenames and placeholder syntax (`{{VAR}}`) contradict Task 1-3's frozen `*.tmpl` names and `string.Template` `$var` syntax. Proposed: align the design spec's template names and placeholder syntax with the task files' Decisions Already Made. | fixed in 783e1b8 |
| 2 | Important | task_5_skill_definition_and_harness_integration.md:Decisions Already Made | freezes `scripts/verify.sh` Section 11 as the wiring point, but that section (scripts/verify.sh:245-261) is scoped to unrelated lifecycle-document-contract tests and would trigger the task's own Stop-and-Report condition. Proposed: wire the new suite into a new Section 14 instead, and update the "13 verification sections" Stop-condition line. | fixed in 783e1b8 |
| 3 | Important | 2026-10-30-setup-shared-contracts-design.en.md:§5 (CLI Engine Specifications) | root-override flag is named `--root` here but `--repo-root`/`--satellite-root` in Tasks 2-4's Decisions Already Made. Proposed: update §5.1-§5.3 to use `--repo-root` (init-hub, verify) and `--satellite-root` (link-satellite). | fixed in 783e1b8 |
| 4 | Minor | 2026-10-30-setup-shared-contracts-design.en.md:4,6 (header) | `Status: In Review` and the Stage-2 `Next step` are stale; Gates 1-2 have already passed per handoff.md. Proposed: set `Status: Approved` and update or remove the `Next step` line. | fixed in 783e1b8 |

Raw output:

```text
## Principal Review — `setup_shared_contracts` (candidate `fc3733a`)

**Scope reviewed:** design spec (EN/VI), HLD, BDD scenarios, handoff, and all 5 task files, cross-checked against `scripts/verify.sh`, `scripts/run_unittest_junit.py`, `skills/doc_quality_check/resources/scripts/check_document.py`, and existing `.agents/rules/` / BDD-prefix conventions in the live tree at `fc3733a`.

### What's solid

- The Hub/Satellite topology, relative-symlink standard, and three-canonical-file contract are consistent across the design spec, HLD, BDD, and all five tasks.
- `## Shared Contract Impact` is present in the HLD (`setup_shared_contracts.en.md:123-125`) and correctly states "None" — this epic builds the tool, it doesn't touch a live `shared-contracts/` tree, so P7's task_01-reservation rule doesn't apply.
- BDD scenario prefix `SSC` doesn't collide with any other epic's prefix (checked against all `.devtool/epic/*/bdd_scenarios.en.md`), and scenario-ID-before-tier-tag formatting matches `dev-designer/SKILL.md`'s convention.
- EN/VI parity is real, not cosmetic: identical heading counts (17/17, 16/16) and identical scenario counts (13/13) — including the VI file reproducing the same filename drift described below, which confirms it's a genuine spec defect and not a translation slip.
- `.agents/rules/contract_rules.md` as the generated-rule path matches the existing convention (`README.md:138`, `templates/AGENTS.md:11-20` — Antigravity natively discovers `.agents/rules/*.md`).
- The `check_document.py <SKILL.md>` verification pattern in Task 5's V3 has direct precedent (`lifecycle_followups/task_2`, `verifiable_task_handoff/task_7`), and its "0 findings" expectation matches the script's actual output format (`check_document.py:259`: `f"  checked {len(args.files)} documents, {len(findings)} findings"`).
- `handoff.md`'s Design commit (`c37225bb...`) is correctly HEAD-before-packaging, matching the convention used by every other epic's handoff.

### Findings

**1. Task 5 freezes a `scripts/verify.sh` wiring point that doesn't match its content.** Task 5's Decisions Already Made states "`scripts/verify.sh` Section 11 executes `python3 -m unittest .../test_setup_contracts.py`." At `fc3733a`, Section 11 (`scripts/verify.sh:245-261`, `== 11. Lifecycle document contracts are enforced ==`) is a fixed, thematically-scoped block of 15 existing unittest invocations — all epic-lifecycle/document-contract tooling (`check_document`, `test_lifecycle_signals`, `audit_epic`, `check_bdd_traceability`, `check_epic_readiness`, `run_external_review`, `verifiable_handoff`, etc.). None of it concerns CLI/symlink tooling, and the setup-shared-contracts suite doesn't belong under that heading. This is exactly the condition Task 5's own "Stop and Report If" flags: "A command, path, symbol or anchor named in this task does not match the repository." As written, an implementer either violates the frozen decision or stops and reports — guaranteed friction Gate 3 should resolve now instead of mid-implementation.
Proposed: Change Task 5 to add a new section (e.g. `== 14. Shared contracts CLI engine is enforced ==`) rather than append to Section 11, and update the "across the 13 verification sections" Stop-condition line to 14.

**2. Design Spec and Task 1 disagree on the template file set — names and substitution syntax both.** Design Spec §4/§6 (`2026-10-30-setup-shared-contracts-design.en.md:66-78,123-141`, mirrored in `.vi.md:73-78,127-140`) names the templates `shared_contracts_readme.md.tmpl`, `hub_contract_rules.md.tmpl`, `satellite_contract_rules.md.tmpl` with Mustache-style placeholders `{{DOMAIN_NAME}}`/`{{HUB_NAME}}`/`{{DATE}}`. Task 1's Allowed files and Decisions Already Made (`task_1_canonical_template_bundles.md:38-40,106`), reused verbatim as Read-only context in Tasks 2 and 3, instead freeze `hub_readme.md.tmpl`, `hub_rule.md.tmpl`, `satellite_rule.md.tmpl` with `string.Template` `$domain`/`$hub_repo`/`$timestamp`. These aren't equivalent: `string.Template.substitute()` only recognizes `$identifier`/`${identifier}`, so a template written in `{{DOMAIN_NAME}}` syntax would render with the placeholder left completely untouched — not an error, a silently broken file shipped into every Hub repo. Since every task's "References" section still points back to the design spec as "Spec," the two approved artifacts actively disagree on the shape of the thing being built.
Proposed: Update design spec §4 and §6 (both languages) to the task-frozen filenames and `string.Template` `$var` syntax, since the tasks are what guardrail 2 in `handoff.md` makes binding.

**3. Design Spec and Tasks disagree on the root-override flag name for all three subcommands.** Design Spec §5.1–§5.3 (`2026-10-30-setup-shared-contracts-design.en.md:87,101,115`) specifies `--root` uniformly for `init-hub`, `link-satellite`, and `verify`. Task 2 and Task 4's Decisions Already Made instead freeze `--repo-root` for `init-hub`/`verify` (`task_2_cli_engine_hub_init.md:106`, `task_4_cli_engine_verification.md:115`), and Task 3 freezes a third name, `--satellite-root`, for `link-satellite` (`task_3_cli_engine_satellite_linking.md:128`). Three names for the same concept across two Gate-approved documents is exactly the "field names" drift P1 calls out, and it's a public CLI surface, not internal wiring.
Proposed: Update design spec §5.1–§5.3 (both languages) to `--repo-root` (init-hub, verify) and `--satellite-root` (link-satellite) to match the tasks' frozen contract.

**4. Design Spec header metadata is stale relative to the epic's actual Gate state.** `2026-10-30-setup-shared-contracts-design.en.md:4,6` still reads `**Status**: In Review` and `**Next step**: d3nexus:dev-designer (Stage 2 — Architecture & Kanban Task Breakdown)`, even though the HLD header (`setup_shared_contracts.en.md:19`) says `**Status**: Packaged` and `handoff.md:18-19` confirms Gates 1 and 2 have both already passed, with the epic sitting at Gate 3. A reader opening the design spec on its own would believe Stage 2 hasn't started.
Proposed: Update the design spec header (both languages) to `Status: Approved` and either drop the `Next step` line or point it at Stage 3 (`dev-implementation`).

Verdict: CHANGES REQUIRED
[Important] 2026-10-30-setup-shared-contracts-design.en.md:§4/§6 (Directory Structure / Canonical Template Bundles) — template filenames and placeholder syntax (`{{VAR}}`) contradict Task 1-3's frozen `*.tmpl` names and `string.Template` `$var` syntax. Proposed: align the design spec's template names and placeholder syntax with the task files' Decisions Already Made.
[Important] task_5_skill_definition_and_harness_integration.md:Decisions Already Made — freezes `scripts/verify.sh` Section 11 as the wiring point, but that section (scripts/verify.sh:245-261) is scoped to unrelated lifecycle-document-contract tests and would trigger the task's own Stop-and-Report condition. Proposed: wire the new suite into a new Section 14 instead, and update the "13 verification sections" Stop-condition line.
[Important] 2026-10-30-setup-shared-contracts-design.en.md:§5 (CLI Engine Specifications) — root-override flag is named `--root` here but `--repo-root`/`--satellite-root` in Tasks 2-4's Decisions Already Made. Proposed: update §5.1-§5.3 to use `--repo-root` (init-hub, verify) and `--satellite-root` (link-satellite).
[Minor] 2026-10-30-setup-shared-contracts-design.en.md:4,6 (header) — `Status: In Review` and the Stage-2 `Next step` are stale; Gates 1-2 have already passed per handoff.md. Proposed: set `Status: Approved` and update or remove the `Next step` line.
```

## Round 2

- **Date**: 2026-10-29T23:26:36Z
- **SHA**: 83c186e28897c89069f4ff58c2b5a5c0ba5e5825
- **Base**: main
- **CLI**: claude
- **Model**: default
- **Status**: completed
- **Verdict**: CHANGES REQUIRED
- **Kind**: principal

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | task_3_cli_engine_satellite_linking.md:Requirement Analysis item 3 / Decisions Already Made | drops the "non-empty" qualifier that the approved design spec (§5.2) and SSC-FR-03's Given clause both require, creating a hard-contract contradiction that would trigger Stop-and-Report on an empty `shared-contracts/` directory. Proposed: add "non-empty" to Task 3's requirement text and decision line to match the design spec and BDD scenario, or remove it from both of those instead so all three artefacts agree. | fixed in 66beed2 |
| 2 | Minor | setup_shared_contracts.en.md / setup_shared_contracts.vi.md:Kanban Tasks Breakdown | Task 2/4/5 Covers annotations list SSC-HP-01/02/03 scenarios that don't appear in those tasks' own Covers lines or Verification tables. Proposed: trim the HLD table's Covers lists to match each task's own Covers line exactly. | fixed in 66beed2 |

Raw output:

```text
Confirmed, the mismatch mirrors identically in the Vietnamese file. I have what I need to write the review.

## Principal Review — `setup_shared_contracts` (candidate `83c186e`)

### Scope reviewed

Design spec (EN/VI), HLD, BDD scenarios (EN/VI), all 5 task files, and `handoff.md`, cross-checked against the live tree at `83c186e`: `scripts/verify.sh` (confirmed Section 14 is the correct next slot, sections run through 13), `scripts/run_unittest_junit.py` (confirmed `--junitxml`/`files` CLI matches task usage), `skills/doc_quality_check/resources/scripts/check_document.py:261` (confirmed `"0 findings"` output format matches Task 5 V3), and `rules/CRITICAL_RULES.md:109-128` (Rule 7, confirmed the Hub/Satellite/symlink boundary language the templates encode). This epic already completed one Principal Review round (`principal_review.md`); all four round-1 findings (template filename/syntax drift, `verify.sh` Section 11 vs 14, `--root` vs `--repo-root`/`--satellite-root`, stale header) are verifiably fixed at this candidate — I checked each independently rather than trusting the "fixed" label.

### What's solid

- Design spec §5.1-§5.3 now uses `--repo-root`/`--satellite-root` consistently, matching Tasks 2-4's frozen decisions.
- Template names/syntax (`hub_readme.md.tmpl`, `$domain`/`$hub_repo`/`$timestamp`) agree between the design spec and Task 1.
- `scripts/verify.sh` currently ends at `== 13. ... ==`, so Task 5's new `== 14. ... ==` section is the correct next slot, not a collision.
- Verification-table RED rows are grounded: I confirmed empirically that `python3 -m unittest <file> -k <name>` exits 1 and prints "FAILED" both when the named test fails and when the file doesn't exist yet, so the TDD RED/GREEN rows hold either way.
- EN/VI scenario-ID sets are identical (`diff` of `[SSC-*]` tokens is empty).

### Findings

**1. Task 3 drops the "non-empty" qualifier that the approved design and the BDD scenario it covers both require.** The design spec (`2026-10-30-setup-shared-contracts-design.en.md:105`) specifies: "Aborts if `<sat_root>/shared-contracts` is a physical **non-empty** directory without `--force`." The scenario it implements, `SSC-FR-03` (`bdd_scenarios.en.md:113`, mirrored in `task_3_cli_engine_satellite_linking.md:92`), likewise scopes its Given clause to "an existing **non-empty** physical directory." But Task 3's own Requirement Analysis item 3 (`task_3_cli_engine_satellite_linking.md:26`) and its Decisions Already Made (`task_3_cli_engine_satellite_linking.md:127`, "Existing physical directories must never be overwritten without explicit `--force`") both generalize to *any* existing physical directory, dropping "non-empty." The handoff guardrails (`handoff.md:56`) make `## Decisions Already Made` a hard contract whose mismatch "causes STOP and report rather than an executor-side simplification" — so an implementer who hits an empty `shared-contracts/` directory has two authoritative-looking but contradictory instructions to resolve, exactly the Stop-and-Report condition this gate exists to clear before implementation.
Proposed: Add "non-empty" to Task 3's Requirement Analysis item 3 and Decisions Already Made line so it matches the design spec and `SSC-FR-03`'s Given clause — or, if refusing even empty directories is the intended (stricter) behavior, drop "non-empty" from the design spec §5.2 and from `bdd_scenarios.en.md`/`.vi.md`'s `SSC-FR-03` instead, so all three artefacts agree on one condition.

**2. The HLD's Kanban Tasks Breakdown overstates which scenarios Tasks 2, 4, and 5 cover.** `setup_shared_contracts.en.md:162,164-165` (identically in `.vi.md:162,164-165`) lists Task 2 as covering `[SSC-HP-01]`, Task 4 as covering `[SSC-HP-03]`, and Task 5 as covering `[SSC-HP-01]`, `[SSC-HP-02]`, `[SSC-HP-03]`. None of these HP-prefixed IDs appear in those tasks' own authoritative `Covers:` lines — Task 2's is `SSC-ST-01, SSC-FR-01` (`task_2_cli_engine_hub_init.md:63`), Task 4's is `SSC-EC-03, SSC-AR-01, SSC-AR-02` (`task_4_cli_engine_verification.md:67`), Task 5's is `SSC-HP-03` alone (`task_5_skill_definition_and_harness_integration.md:58`) — nor in any Verification-table row of those tasks. This doesn't change what gets built (each task file is self-consistent and is what an implementer actually follows), but it misrepresents scenario-to-task traceability to anyone reading the HLD summary.
Proposed: Trim the HLD's Kanban Tasks Breakdown lines (both languages) to match each task's own `Covers:` line exactly: Task 2 → `[SSC-ST-01]`, `[SSC-FR-01]`; Task 4 → `[SSC-EC-03]`, `[SSC-AR-01]`, `[SSC-AR-02]`; Task 5 → `[SSC-HP-03]`.

Verdict: CHANGES REQUIRED
[Important] task_3_cli_engine_satellite_linking.md:Requirement Analysis item 3 / Decisions Already Made — drops the "non-empty" qualifier that the approved design spec (§5.2) and SSC-FR-03's Given clause both require, creating a hard-contract contradiction that would trigger Stop-and-Report on an empty `shared-contracts/` directory. Proposed: add "non-empty" to Task 3's requirement text and decision line to match the design spec and BDD scenario, or remove it from both of those instead so all three artefacts agree.
[Minor] setup_shared_contracts.en.md / setup_shared_contracts.vi.md:Kanban Tasks Breakdown — Task 2/4/5 Covers annotations list SSC-HP-01/02/03 scenarios that don't appear in those tasks' own Covers lines or Verification tables. Proposed: trim the HLD table's Covers lists to match each task's own Covers line exactly.
```
