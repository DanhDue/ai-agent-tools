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


if __name__ == "__main__":
    unittest.main()
