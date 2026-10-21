#!/usr/bin/env python3
"""Tests for local model review: shared rules, the Ollama transport, slices, the prompt base and rounds.

Every Ollama call goes to a fake server on 127.0.0.1 inside the test; no test reaches a real model.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_run_external_review import ReviewCase


class SharedRulesTest(ReviewCase):
    def test_lmr_hp_02_shared_rules_reach_the_external_prompt(self) -> None:
        self.install("claude")
        code, _, _ = self.run_review(cli="claude")
        self.assertEqual(code, 0)
        prompt = self.stdin.read_text(encoding="utf-8")
        for title in ("Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic",
                      "Immutable Real Artifacts"):
            self.assertIn(title, prompt)
        self.assertNotIn("$rules", prompt)


if __name__ == "__main__":
    unittest.main()
