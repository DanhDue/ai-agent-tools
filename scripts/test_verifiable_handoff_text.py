#!/usr/bin/env python3
"""Lock the verifiable task handoff statements in the skills a receiving agent reads.

Run: python3 -m unittest scripts/test_verifiable_handoff_text.py
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SDD = "skills/subagent-driven-development/"


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class VerifiableHandoffText(unittest.TestCase):
    def assert_present(self, relative, phrases):
        text = read(relative)
        for phrase in phrases:
            self.assertIn(phrase, text, f"{relative} lacks {phrase!r}")

    def assert_absent(self, relative, phrases):
        text = read(relative)
        for phrase in phrases:
            self.assertNotIn(phrase, text, f"{relative} still has {phrase!r}")

    def test_vth_hp_06_dev_designer_states_the_task_contract(self):
        self.assert_present("skills/dev-designer/SKILL.md", (
            "Stop and Report If", "Decisions Already Made", "Allowed files:",
            "RED: n/a", "(Gate 5)", "exactly one task",
            "check_task_contract.py --design", "Protected paths:",
            "Integration results:", "Verification Environment",
            "references/verification-rows.md",
        ))
        self.assert_absent("skills/dev-designer/SKILL.md",
                           ("Test & Verification Checklist",))
        self.assert_present("skills/dev-designer/references/verification-rows.md", (
            "Python", "Android", "Web", "iOS", "Rust", "Flutter",
            "--junitxml", "--file-reporter json:", "--xunit-output", "nextest",
        ))

    def test_vth_hp_07_dev_implementation_states_recorder_and_gate(self):
        path = "skills/dev-implementation/SKILL.md"
        self.assert_present(path, (
            "run_task_checks.py red", "run_task_checks.py verify",
            "run_task_checks.py status", "evidence/<task_id>.json",
            "check_task_contract.py",
        ))
        text = read(path)
        start = text.index("### Phase 4")
        end = text.index("### Phase 4.1")
        phase4 = text[start:end]
        positions = [phase4.index(p) for p in (
            "audit_epic.py", "Integration results", "tests --results",
            "@quality_check")]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(set(positions)), 4)

    def test_vth_hp_08_dev_lifecycle_and_handoff_state_the_rules(self):
        self.assert_present("skills/dev-lifecycle/SKILL.md", (
            "audit_epic.py", "result-based traceability",
            "check_task_contract.py --design",
        ))
        self.assert_present("skills/dev-lifecycle/references/handoff-template.md", (
            "Never edit a task's Verification table",
        ))

    def test_vth_hp_09_sdd_prompts_treat_evidence_as_proof(self):
        self.assert_present(SDD + "implementer-prompt.md", (
            "run_task_checks.py red", "run_task_checks.py verify",
            "the evidence file is the test evidence",
        ))
        self.assert_absent(SDD + "implementer-prompt.md",
                           ("your report is the test evidence",))
        self.assert_present(SDD + "task-reviewer-prompt.md", (
            "run_task_checks.py status", "Critical",
        ))

    def test_vth_hp_13_review_choice_is_stated(self):
        for path in ("skills/dev-implementation/SKILL.md",
                     "skills/dev-lifecycle/SKILL.md"):
            self.assert_present(path, (
                "Review Choice", "Finish", "Cross-model review", "Claude CLI",
                "Codex CLI", "run_external_review.py run",
                "run_external_review.py check", "review_results.md",
            ))
        self.assert_present("skills/dev-lifecycle/SKILL.md",
                            ("picking the review CLI for the developer",))


if __name__ == "__main__":
    unittest.main()
