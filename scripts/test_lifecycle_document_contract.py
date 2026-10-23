#!/usr/bin/env python3
"""Verify that every lifecycle document producer exposes the shared contract."""

from __future__ import annotations

import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

EXPECTED: dict[str, tuple[str, ...]] = {
    "skills/dev-brainstorming/SKILL.md": (
        "YYYY-MM-DD-<topic>-design.en.md",
        "YYYY-MM-DD-<topic>-design.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-brainstorming/SKILL.md": (
        "YYYY-MM-DD-<topic>-design.en.md",
        "YYYY-MM-DD-<topic>-design.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/dev-designer/SKILL.md": (
        "<epic_name>.en.md",
        "<epic_name>.vi.md",
        "bdd_scenarios.en.md",
        "bdd_scenarios.vi.md",
        "--require-toc",
        "--require-bilingual",
        "Task files are English-only",
        "check_bdd_traceability.py plan",
        "Covers:",
        "Integration test roots:",
        "at least one automated integration test",
        "Handoff Choice",
        "`tests/integration/` and `tests/e2e/` (Python)",  # LF-HP-03
        "exact node ID",
        "should be truthy",
        "returns non-empty",
        "must not be empty or write `None`",
    ),
    "skills/writing-plans/SKILL.md": (
        "YYYY-MM-DD-<feature-name>.en.md",
        "YYYY-MM-DD-<feature-name>.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-designer/SKILL.md": (
        "<doc_dir>.en.md",
        "<doc_dir>.vi.md",
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc-implementation/SKILL.md": (
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc_quality_check/SKILL.md": (
        "--require-toc",
        "--require-bilingual",
    ),
    "skills/doc_quality_check/references/document-reviewer-prompt.md": (
        "English document",
        "Vietnamese document",
        "Translation parity",
    ),
    "skills/dev-implementation/SKILL.md": (
        '`profile`: `"epic"`',
        '`repository_sha`',
        "aggregated verdict of **PASS**",
        "check_bdd_traceability.py tests",
        "--ids",
        "Entry-Point Detection",
        "Resume Procedure",
        "handoff.md",
        "space- or comma-separated values",  # LF-HP-04
        "re-enters at Phase 2 step 2",  # LF-ST-04
        "may ride along in that commit",  # LF-ST-06
    ),
    "skills/dev-lifecycle/SKILL.md": (
        'profile `epic`',
        "`repository_sha`",
        "FAIL > BLOCKED > PASS",
        "check_bdd_traceability.py tests",
        "Granting Gate 4 without a passing traceability check",
        "Handoff Choice",
        "handoff-template.md",
        "Resuming an Epic",
        "Packaged",
        "a fresh traceability check and epic quality run",  # LF-ST-05
        "`<N>` is the task count the preflight printed",  # LF-HP-05
        "check_epic_readiness.py <epic_dir>",
        "Principal Review Choice",
        "references/principal-review.md",
    ),
    "skills/dev-lifecycle/references/handoff-template.md": (
        "or `uncommitted` when `auto_commit` is false",  # LF-FR-04
        "Execution Guardrails for Receiving LLM",
        "Bounded context protocol",
        "Strict spec fidelity",
        "Zero test fakery",
        "No contract repair by the executor",
        "Apply the Execution Guardrails for Receiving LLM before presenting Gate 3",
    ),
    "skills/pr_review/SKILL.md": (
        '"profile": "pr"',
        '"base_ref"',
        "Executive Report Format",
    ),
    "skills/principal-review/SKILL.md": (
        "name: principal-review",
        "Two Modes of Operation",
        "In-Lifecycle Mode",
        "Ad-Hoc Mode",
        "--kind principal",
        "references/principal-review-prompt.md",
        "references/principal-review-rules.md",
        "references/document-triage.md",
    ),
    "skills/cross-model-review/SKILL.md": (
        "name: cross-model-review",
        "Two Modes of Operation",
        "In-Lifecycle Mode",
        "Ad-Hoc Mode",
        "Clean Working Tree",
        "references/review-triage.md",
        "references/local-review-setup.md",
    ),
}

FORBIDDEN: dict[str, tuple[str, ...]] = {
    "skills/pr_review/SKILL.md": (
        "melos test",
        "./gradlew check",
        "swift test",
        "cleanup-java",
    ),
}


class LifecycleDocumentContractTest(unittest.TestCase):
    def test_mvls_hp_06_dev_designer_and_handoff_guardrails(self) -> None:
        """[MVLS-HP-06] dev-designer retains Decisions Already Made contracts, exact node IDs, weak assertion ban, and handoff-template retains 4 guardrails."""
        designer_path = ROOT / "skills/dev-designer/SKILL.md"
        designer_text = designer_path.read_text(encoding="utf-8")
        self.assertIn("exact node ID", designer_text)
        self.assertIn("Decisions Already Made", designer_text)
        self.assertIn("should be truthy", designer_text)
        self.assertIn("returns non-empty", designer_text)

        handoff_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
        handoff_text = handoff_path.read_text(encoding="utf-8")
        self.assertIn("Execution Guardrails for Receiving LLM", handoff_text)
        self.assertIn("bounded context", handoff_text.lower())
        self.assertIn("strict spec fidelity", handoff_text.lower())
        self.assertIn("zero test fakery", handoff_text.lower())
        self.assertIn("no contract repair", handoff_text.lower())
        self.assertIn("Apply the Execution Guardrails for Receiving LLM before presenting Gate 3", handoff_text)

    def test_mvls_ec_06_reject_missing_guardrails_or_designer_anchors(self) -> None:
        """[MVLS-EC-06] Reject missing receiving-LLM guardrails or dev-designer anchors in lifecycle contract."""
        designer_path = ROOT / "skills/dev-designer/SKILL.md"
        designer_text = designer_path.read_text(encoding="utf-8")
        self.assertTrue(bool(re.search(r"exact node ID.*path/test_file\.py::test_name", designer_text)))
        self.assertTrue(bool(re.search(r"Decisions Already Made.*must not be empty or write `?None`?", designer_text)))

        handoff_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
        handoff_text = handoff_path.read_text(encoding="utf-8")
        for guardrail in ("bounded context", "strict spec fidelity", "zero test fakery", "no contract repair"):
            self.assertIn(guardrail, handoff_text.lower())

    def test_mvls_hp_05_lifecycle_docs_and_skill_word_limit(self) -> None:
        """[MVLS-HP-05] dev-lifecycle is <= 2500 words and human docs contain lifecycle and resume diagrams."""
        skill_path = ROOT / "skills/dev-lifecycle/SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        words = len(skill_text.split())
        self.assertLessEqual(words, 2500, f"SKILL.md exceeds word limit: {words} > 2500")

        for doc_name in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
            doc_path = ROOT / doc_name
            doc_text = doc_path.read_text(encoding="utf-8")
            self.assertIn("```mermaid", doc_text)
            self.assertIn("Gate 4" if "en" in doc_name else "Cổng 4", doc_text)
            self.assertIn("Review Choice", doc_text)
            self.assertIn("Gate 5" if "en" in doc_name else "Cổng 5", doc_text)
            self.assertIn("Cross-model review", doc_text)
            self.assertIn("Interrupted" if "en" in doc_name else "ngắt quãng", doc_text)

    def test_mvls_ec_05_keep_diagrams_outside_runtime_skills(self) -> None:
        """[MVLS-EC-05] Neither runtime skill contains diagrams; both human docs contain Mermaid diagrams."""
        for skill_rel in ("skills/dev-lifecycle/SKILL.md", "skills/dev-implementation/SKILL.md"):
            text = (ROOT / skill_rel).read_text(encoding="utf-8")
            self.assertNotIn("```mermaid", text, f"{skill_rel} must not contain Mermaid diagram fences")
            self.assertNotIn("```dot", text, f"{skill_rel} must not contain Graphviz DOT diagram fences")

        for doc_rel in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
            text = (ROOT / doc_rel).read_text(encoding="utf-8")
            self.assertIn("```mermaid", text, f"{doc_rel} must contain Mermaid diagrams")

    def test_mvls_st_03_lifecycle_invariants(self) -> None:
        """[MVLS-ST-03] Skill slimming keeps document contracts synchronized and preserves runtime invariants."""
        skill_text = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
        for token in EXPECTED["skills/dev-lifecycle/SKILL.md"]:
            self.assertIn(token, skill_text, f"dev-lifecycle/SKILL.md missing invariant: {token}")

        self.assertIn("fast executor model", skill_text.lower())
        self.assertIn("strongly recommended", skill_text.lower())

    def test_mvls_fr_05_fail_when_lifecycle_invariants_drift(self) -> None:
        """[MVLS-FR-05] Fail when lifecycle invariants drift or diagram rules are violated."""
        skill_text = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Mandatory Review Choice loop", skill_text)
        self.assertIn("Gate 4 grants `🟢 LGTM`", skill_text)

    def test_mvls_hp_04_implementation_skill_concise_and_orchestrated(self) -> None:
        """[MVLS-HP-04] dev-implementation is <= 4500 words, has no diagram fences, and preserves orchestration."""
        impl_path = ROOT / "skills/dev-implementation/SKILL.md"
        text = impl_path.read_text(encoding="utf-8")
        words = len(text.split())
        self.assertLessEqual(words, 4500, f"SKILL.md exceeds word limit: {words} > 4500")
        self.assertNotIn("```mermaid", text, "SKILL.md must not contain Mermaid diagram fences")
        self.assertNotIn("```dot", text, "SKILL.md must not contain Graphviz DOT diagram fences")

        for token in EXPECTED["skills/dev-implementation/SKILL.md"]:
            self.assertIn(token, text, f"Missing required token: {token}")

        self.assertIn("Bounded Context Injection", text)
        self.assertIn("Decisions Already Made", text)
        self.assertIn("strict spec fidelity", text.lower())

        self.assertIn("No Reconstructed Logic", text)
        self.assertIn("Immutable Real Artifacts", text)

    def test_mvls_fr_04_gate_4_semantic_test_fakery_rejected(self) -> None:
        """[MVLS-FR-04] Gate 4 rejects semantic test fakery without claiming universal mechanical coverage."""
        impl_path = ROOT / "skills/dev-implementation/SKILL.md"
        text = impl_path.read_text(encoding="utf-8")
        self.assertIn("No Reconstructed Logic", text)
        self.assertIn("Immutable Real Artifacts", text)
        self.assertTrue(bool(re.search(r"reconstructed\s+logic.*FAIL", text, re.IGNORECASE | re.DOTALL)))
        self.assertTrue(bool(re.search(r"synthetic.*artifact.*FAIL", text, re.IGNORECASE | re.DOTALL)))

    def test_lmr_hp_01_review_choice_presents_three_options(self) -> None:
        """[LMR-HP-01] Review Choice offers Finish, Cross-model review and Local model review everywhere it is stated."""
        for relative in ("skills/dev-implementation/SKILL.md", "skills/dev-lifecycle/SKILL.md",
                         "rules/CRITICAL_RULES.md", "docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            for option in ("Finish", "Cross-model review", "Local model review"):
                self.assertIn(option, text, f"{relative} does not name {option}")
        implementation = (ROOT / "skills/dev-implementation/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("--cli ollama --model <model>", implementation)
        self.assertIn("ollama list", implementation)
        lifecycle = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
        red_flags = lifecycle.split("## Red Flags", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Picking the Ollama model for the developer", red_flags)

    def test_lmr_st_03_local_model_review_returns_to_gate_4(self) -> None:
        """[LMR-ST-03] Local model review returns through its round-recorded edge to Gate 4 in full, never to Gate 5."""
        implementation = (ROOT / "skills/dev-implementation/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('choice -- "Local model review" --> localreview', implementation)
        self.assertIn('localreview -- "round recorded" --> phase4', implementation)
        self.assertNotRegex(implementation, r"localreview -- [^\n]*--> checkpoint4")
        lifecycle = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
        for text in (implementation, lifecycle):
            self.assertIn("Local model review → Gate 4 in full", text)
        for relative, label in (("skills/dev-lifecycle/SKILL.md", "round recorded"),
                                ("docs/lifecycles.en.md", "round recorded"),
                                ("docs/lifecycles.vi.md", "đã ghi nhận round")):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn('RC -->|"3. Local model review"| LR', text, relative)
            self.assertIn(f'LR -->|"{label}"| G4', text, relative)
            self.assertNotRegex(text, r"LR -->\|[^|]*\| (REVIEW|G5)", relative)

    def test_lmr_hp_09_the_workflow_requires_triage_before_acting_on_findings(self) -> None:
        """[LMR-HP-09] Every review round is triaged with the developer before any fix or decision."""
        for relative in ("skills/dev-implementation/SKILL.md", "skills/dev-lifecycle/SKILL.md", "rules/CRITICAL_RULES.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("run_external_review.py triage", text, relative)
        implementation = (ROOT / "skills/dev-implementation/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/review-triage.md", implementation)
        self.assertIn("wait for the developer's decisions before any Fix commit", implementation)
        lifecycle = (ROOT / "skills/dev-lifecycle/SKILL.md").read_text(encoding="utf-8")
        red_flags = lifecycle.split("## Red Flags", 1)[1].split("\n## ", 1)[0]
        self.assertIn("Acting on review findings before presenting the triage", red_flags)

    def test_document_contract_expected_tokens(self) -> None:
        for relative_path, required_tokens in EXPECTED.items():
            path = ROOT / relative_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for token in required_tokens:
                self.assertIn(token, text, f"{relative_path}: missing {token}")

    def test_document_contract_forbidden_tokens(self) -> None:
        for relative_path, forbidden_tokens in FORBIDDEN.items():
            path = ROOT / relative_path
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                self.assertNotIn(token, text, f"{relative_path}: contains forbidden {token}")


class PrincipalReviewWorkflowTest(unittest.TestCase):
    def test_prv_hp_04_packaging_readiness_and_principal_review_choice(self) -> None:
        """[PRV-HP-04] Packaging runs one readiness command and offers Principal Review Choice."""
        skill_path = ROOT / "skills/dev-lifecycle/SKILL.md"
        skill_text = skill_path.read_text(encoding="utf-8")
        self.assertIn("check_epic_readiness.py <epic_dir>", skill_text)
        self.assertIn("Principal Review Choice", skill_text)
        self.assertIn("references/principal-review.md", skill_text)
        self.assertNotIn(
            "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks",
            skill_text,
        )
        words = len(skill_text.split())
        self.assertLessEqual(words, 2500, f"dev-lifecycle/SKILL.md exceeds word limit: {words} > 2500")
        for token in EXPECTED["skills/dev-lifecycle/SKILL.md"]:
            self.assertIn(token, skill_text)

        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
        self.assertTrue(ref_path.is_file(), f"{ref_path} must exist")
        ref_text = ref_path.read_text(encoding="utf-8")
        self.assertIn("1. **Done**", ref_text)
        self.assertIn("2. **Principal Review**", ref_text)
        self.assertIn("Claude CLI", ref_text)
        self.assertIn("Codex CLI", ref_text)
        self.assertIn("Never choose for the developer", ref_text)
        self.assertIn("strongly recommended", ref_text)

    def test_prv_ec_07_handoff_template_reads_first_principal_review(self) -> None:
        """[PRV-EC-07] Read First lists principal_review.md."""
        template_path = ROOT / "skills/dev-lifecycle/references/handoff-template.md"
        text = template_path.read_text(encoding="utf-8")
        read_first = text.split("## Read First", 1)[1].split("## ", 1)[0]
        self.assertIn("`.devtool/epic/<epic_dir>/principal_review.md`, when present", read_first)
        self.assertIn("`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`", text)

    def test_prv_st_03_diagram_loop_returns_to_package_and_done_repackages(self) -> None:
        """[PRV-ST-03] The loop returns to Package and Done re-packages after a round."""
        for doc_name in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
            doc_text = (ROOT / doc_name).read_text(encoding="utf-8")
            self.assertIn("PKG --> PRC", doc_text)
            self.assertIn('PRC -->|"2. Principal Review"| PR', doc_text)
            self.assertIn('PR -->|"revised and re-packaged"| PKG', doc_text)
            self.assertNotRegex(doc_text, r"PR\s*[-.=]+>[^\n]*(S3|G3)")

        ref_path = ROOT / "skills/dev-lifecycle/references/principal-review.md"
        ref_text = ref_path.read_text(encoding="utf-8")
        self.assertIn("Record Principal Review round <n>", ref_text)
        self.assertIn("Revise epic after Principal Review round <n>", ref_text)
        self.assertIn("Package epic for handoff", ref_text)
        self.assertIn("check --kind principal", ref_text)
        self.assertIn("git log -1 --format=%s -- .devtool/epic/<epic_dir>", ref_text)

    def test_prv_st_04_gate_3_stops_while_principal_finding_undecided(self) -> None:
        """[PRV-ST-04] Gate 3 stops while a blocking principal finding is undecided."""
        impl_path = ROOT / "skills/dev-implementation/SKILL.md"
        text = impl_path.read_text(encoding="utf-8")
        self.assertIn("run_external_review.py check --kind principal --epic-dir <epic_dir>", text)

        phase1_section = text.split("### Phase 1", 1)[1].split("#### Phase 1 (continued)", 1)[0]
        self.assertIn("Principal Review", phase1_section)
        self.assertIn("not run", phase1_section)
        self.assertIn("round <n>: PASS", phase1_section)
        self.assertIn("round <n>: decided", phase1_section)

        resume_section = text.split("#### Resume Procedure", 1)[1].split("### Phase 1", 1)[0]
        self.assertIn("Principal Review", resume_section)
        self.assertIn("not run", resume_section)
        self.assertIn("round <n>: PASS", resume_section)
        self.assertIn("round <n>: decided", resume_section)

        words = len(text.split())
        self.assertLessEqual(words, 4500, f"dev-implementation/SKILL.md exceeds word limit: {words} > 4500")


class TestReviewSkillContracts(unittest.TestCase):
    def test_srs_hp_06_review_skills_expose_contract_and_frontmatter(self) -> None:
        """[SRS-HP-06] Document contracts enforce new review skills exposure."""
        for skill_rel in ("skills/principal-review/SKILL.md", "skills/cross-model-review/SKILL.md"):
            skill_path = ROOT / skill_rel
            self.assertTrue(skill_path.is_file(), f"{skill_rel} must exist")
            text = skill_path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), f"{skill_rel} must have YAML frontmatter")
            for token in EXPECTED[skill_rel]:
                self.assertIn(token, text, f"{skill_rel} missing expected contract token: {token}")

    def test_srs_hp_07_lifecycle_diagrams_reflect_two_standalone_review_stages(self) -> None:
        """[SRS-HP-07] Lifecycle diagrams reflect two standalone review stages."""
        for doc_name in ("docs/lifecycles.en.md", "docs/lifecycles.vi.md"):
            doc_text = (ROOT / doc_name).read_text(encoding="utf-8")
            self.assertIn("principal-review", doc_text)
            self.assertIn("cross-model-review", doc_text)


if __name__ == "__main__":
    unittest.main()

