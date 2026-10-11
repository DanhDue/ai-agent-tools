"""Artifact-integrity tests; no model replies are regenerated or fabricated."""

import concurrent.futures
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SUITE = Path(__file__).resolve().parent


class CompletenessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.suite = self.repo / "evals/provider_based_quality_check"
        shutil.copytree(SUITE, self.suite, ignore=shutil.ignore_patterns("__pycache__"))
        self.run = self.suite / "runs/2026-10-11-baseline"

    def check(self, *args):
        return subprocess.run(
            [sys.executable, str(self.suite / "check_baseline.py"), *args],
            capture_output=True, text=True, check=False,
        )

    def mutate_json(self, path, change):
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def test_complete_capture_reports_actual_red_count(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("5/5 complete; 1/5 primary failures", result.stdout)

    def test_missing_replacement_blocks_primary_completeness(self):
        replacement = self.suite / "runs/2026-10-11-composite-v2/first-match-routing/response.md"
        replacement.unlink(missing_ok=True)
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("4/5 complete", result.stdout)

    def test_historical_capture_cannot_satisfy_targeted_acceptance(self):
        replacement = self.suite / "runs/2026-10-11-composite-v2/first-match-routing/response.md"
        replacement.unlink(missing_ok=True)
        result = self.check("--require-failure", "status-precedence")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("2026-10-11-composite-v2", result.stdout)

    def test_historical_outcome_is_excluded_from_primary_failure_count(self):
        path = self.run / "first-match-routing/grade.json"
        def change(value):
            value["criteria"][0]["outcome"] = "FAIL"
            value["failure_rationalization"] = value["criteria"][0]["quote"]
        self.mutate_json(path, change)
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("5/5 complete; 1/5 primary failures", result.stdout)

    def test_missing_primary_manifest_cannot_fall_back_to_contaminated_run(self):
        (self.suite / "primary-manifest.json").unlink(missing_ok=True)
        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("primary-manifest.json", result.stdout)

    def test_replacement_requires_all_independent_grade_artifacts(self):
        folder = self.suite / "runs/2026-10-11-composite-v2/first-match-routing"
        for name in ("capture.json", "grade.json", "judge-response.md", "judge-capture.json"):
            with self.subTest(artifact=name):
                path = folder / name
                original = path.read_bytes()
                path.unlink()
                result = self.check()
                path.write_bytes(original)
                self.assertEqual(result.returncode, 1)
                self.assertIn(name, result.stdout)

    def test_changed_independent_grade_cannot_override_judge(self):
        path = self.suite / "runs/2026-10-11-composite-v2/first-match-routing/grade.json"
        self.mutate_json(path, lambda value: value["criteria"][0].update(rationale="Rewritten grade"))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("grade differs from blind judge", result.stdout)

    def test_replacement_rubric_must_remain_frozen(self):
        path = self.suite / "scenarios/composite-workspace-v2/graders/criteria.md"
        path.write_text(path.read_text() + "\nAltered rubric.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("replacement frozen digest", result.stdout)

    def test_judge_must_be_independently_blind(self):
        path = self.suite / "runs/2026-10-11-composite-v2/first-match-routing/judge-capture.json"
        self.mutate_json(path, lambda value: value.update(independent_blind=False))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not independently blind", result.stdout)

    def test_require_red_rejects_four_primary_passes(self):
        result = self.check("--require-red")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("RED incomplete: 1/5", result.stdout)

    def test_targeted_failure_accepts_observed_precedence_red(self):
        result = self.check("--require-failure", "status-precedence")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("5/5 complete; 1/5 primary failures", result.stdout)

    def test_targeted_failure_rejects_passing_regression_control(self):
        result = self.check("--require-failure", "first-match-routing")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("RED not demonstrated: first-match-routing", result.stdout)

    def test_every_missing_artifact_blocks_completeness(self):
        for scenario in sorted(path for path in self.run.iterdir() if path.is_dir()):
            for name in ("response.md", "capture.json", "grade.json"):
                with self.subTest(scenario=scenario.name, artifact=name):
                    path = scenario / name
                    data = path.read_bytes()
                    path.unlink()
                    result = self.check()
                    path.write_bytes(data)
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn(name, result.stdout)

    def test_changed_response_is_rejected(self):
        path = self.run / "first-match-routing/response.md"
        path.write_text(path.read_text() + "\nAltered reply.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("response digest", result.stdout)

    def test_unfrozen_rubric_is_rejected(self):
        path = self.suite / "scenarios/status-precedence/graders/criteria.md"
        path.write_text(path.read_text() + "\nNew criterion.\n")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("frozen digest", result.stdout)

    def test_missing_frozen_entry_is_rejected(self):
        path = self.suite / "manifest.json"
        key = "evals/provider_based_quality_check/scenarios/status-precedence/prompt.md"
        self.mutate_json(path, lambda value: value["frozen_sha256"].pop(key))
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("frozen artifact set", result.stdout)

    def test_cross_scenario_capture_is_rejected(self):
        self.mutate_json(
            self.run / "first-match-routing/capture.json",
            lambda value: value.update(scenario_id="missing-tool-skip"),
        )
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("scenario identity", result.stdout)

    def test_untraceable_grade_quote_is_rejected(self):
        self.mutate_json(
            self.run / "first-match-routing/grade.json",
            lambda value: value["criteria"][0].update(quote="Invented answer text."),
        )
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("quote absent", result.stdout)

    def test_grade_omission_is_rejected(self):
        self.mutate_json(
            self.run / "first-match-routing/grade.json",
            lambda value: value.update(criteria=[]),
        )
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("primary and control", result.stdout)

    def test_duplicate_scenario_is_rejected(self):
        self.mutate_json(
            self.suite / "manifest.json",
            lambda value: value["scenarios"].append("first-match-routing"),
        )
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("scenario set", result.stdout)

    def test_malformed_capture_is_rejected(self):
        (self.run / "first-match-routing/capture.json").write_text("{")
        result = self.check()
        self.assertEqual(result.returncode, 1)
        self.assertIn("capture.json", result.stdout)

    def test_parallel_checks_are_deterministic_and_read_only(self):
        def snapshot():
            return {
                str(path.relative_to(self.repo)): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in self.repo.rglob("*") if path.is_file()
            }

        before = snapshot()
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: self.check(), range(3)))
        self.assertTrue(all(result.returncode == 0 for result in results))
        self.assertEqual(len({result.stdout for result in results}), 1)
        self.assertEqual(snapshot(), before)


if __name__ == "__main__":
    unittest.main()
