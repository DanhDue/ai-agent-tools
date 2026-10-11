"""Check frozen baseline evidence without regenerating or grading model replies."""

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys

SCENARIOS = {
    "first-match-routing", "missing-tool-skip", "profile-downgrade",
    "status-precedence", "stale-sha-approval",
}
SKILLS = {"skills/quality_check/SKILL.md", "skills/dev-lifecycle/SKILL.md"}
PREFIX = "evals/provider_based_quality_check/"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as error:
        raise ValueError(f"{path.name}: {error}") from error


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def subject_inputs(manifest, scenario):
    paths = manifest.get("subject_input_paths") or (
        SKILLS | {PREFIX + "context.md", PREFIX + f"scenarios/{scenario}/prompt.md"})
    return {path: manifest["frozen_sha256"][path] for path in paths}


def validate_manifest(suite):
    manifest = read_json(suite / "manifest.json")
    require(manifest["version"] == 1, "unsupported manifest version")
    ids = manifest["scenarios"]
    require(len(ids) == 5 and set(ids) == SCENARIOS, "scenario set must contain five unique cases")
    require(set(manifest["baseline_skills"]) == SKILLS, "baseline skill set mismatch")
    require(re.fullmatch(r"[a-f0-9]{40}", manifest["source_revision"]), "invalid source revision")
    require(re.fullmatch(r"[a-z0-9-]+", manifest["run_id"]), "invalid run ID")
    require(manifest["context"] == "context.md", "context path mismatch")
    expected = SKILLS | {PREFIX + "context.md"}
    for scenario in ids:
        expected |= {PREFIX + f"scenarios/{scenario}/prompt.md",
                     PREFIX + f"scenarios/{scenario}/graders/criteria.md"}
    require(set(manifest["frozen_sha256"]) == expected, "frozen artifact set mismatch")
    for path, sha in sorted(manifest["frozen_sha256"].items()):
        if path in SKILLS:
            source = suite / "baseline" / (path.split("/")[1] + ".md")
        else:
            source = suite / path.removeprefix(PREFIX)
        require(digest(source) == sha, f"frozen digest mismatch: {path}")
    return manifest


def validate_grade(grade, response, scenario, sha, capture):
    require(grade["scenario_id"] == scenario, "grade scenario identity mismatch")
    require(grade["response_sha256"] == sha, "grade response digest mismatch")
    grader = grade["grader"]
    require(nonempty(grader["agent_id"]) and nonempty(grader["context"]), "grader context missing")
    require(grader["agent_id"] != capture["agent_id"], "subject cannot grade itself")
    require(grader["dispatched_subject"] is False, "grader dispatched its own subject")
    criteria = grade["criteria"]
    require(len(criteria) == 2 and {item["id"] for item in criteria} == {"primary", "control"},
            "grade must include primary and control")
    for item in criteria:
        require(item["outcome"] in {"PASS", "FAIL"}, "invalid criterion outcome")
        require(nonempty(item["rationale"]), "criterion rationale missing")
        quote = item.get("quote", item.get("exact_quote"))
        require(nonempty(quote) and quote in response, "grade quote absent from response")
    primary = next(item["outcome"] for item in criteria if item["id"] == "primary")
    rationalization = grade["failure_rationalization"]
    require(nonempty(rationalization), "failure rationalization record missing")
    if primary == "FAIL":
        require(rationalization in response, "failure rationalization quote absent from response")
    unscored = grade["unscored"]
    require(nonempty(unscored) or (isinstance(unscored, list) and bool(unscored)),
            "unscored findings record missing")
    return primary


def validate_primary_selection(suite, historical):
    selection = read_json(suite / "primary-manifest.json")
    require(selection["version"] == 1 and selection["historical_manifest"] == "manifest.json",
            "invalid primary manifest version or historical reference")
    ids = selection["primary_scenarios"]
    require(len(ids) == 5 and set(ids) == SCENARIOS, "invalid primary scenario set")
    exclusions = selection["excluded_historical"]
    require(len(exclusions) == 1 and exclusions[0]["run_id"] == historical["run_id"]
            and exclusions[0]["scenario_id"] == "first-match-routing"
            and nonempty(exclusions[0]["reason"]), "contaminated historical exclusion missing")
    replacement = selection["replacement"]
    expected = {
        "prompt": "scenarios/composite-workspace-v2/prompt.md",
        "rubric": "scenarios/composite-workspace-v2/graders/criteria.md",
        "context": "context.md",
        "subject_request": "scenarios/composite-workspace-v2/request.md",
    }
    require(replacement["scenario_id"] == "first-match-routing"
            and replacement["run_id"] == "2026-10-11-composite-v2",
            "uncontaminated replacement identity missing")
    require(replacement["source_revision"] == historical["source_revision"],
            "replacement source revision mismatch")
    require(replacement["independent_blind_grader_required"] is True,
            "independent blind grader requirement missing")
    require(all(replacement[key] == path for key, path in expected.items()),
            "replacement input paths mismatch")
    baseline = {"baseline/quality_check.md", "baseline/dev-lifecycle.md"}
    require(set(replacement["frozen_sha256"]) == set(expected.values()) | baseline,
            "replacement frozen artifact set mismatch")
    for path, sha in replacement["frozen_sha256"].items():
        require(digest(suite / path) == sha, f"replacement frozen digest mismatch: {path}")
    replacement["subject_input_paths"] = baseline | {replacement["subject_request"]}
    return replacement


def validate_blind_judge(suite, manifest):
    folder = suite / "runs" / manifest["run_id"] / "first-match-routing"
    capture = read_json(folder / "judge-capture.json")
    grade = read_json(folder / "grade.json")
    require(capture["context_mode"] == "fresh-none"
            and capture["independent_blind"] is True, "judge was not independently blind")
    require(capture["agent_id"] == grade["grader"]["agent_id"]
            and capture["agent_id"] != "/root/task1_implementer", "judge identity mismatch")
    require(capture["raw_sha256"] == digest(folder / "judge-response.md"),
            "judge response digest mismatch")
    require(capture["initial_raw_sha256"] == digest(folder / "judge-initial.md"),
            "initial judge response digest mismatch")
    require(capture["response_sha256"] == digest(folder / "response.md"),
            "judge graded a different response")
    require(capture["inputs_sha256"] == {
        manifest["prompt"]: manifest["frozen_sha256"][manifest["prompt"]],
        manifest["rubric"]: manifest["frozen_sha256"][manifest["rubric"]],
        "response.md": digest(folder / "response.md"),
    }, "blind judge inputs mismatch")
    raw, _ = json.JSONDecoder().raw_decode((folder / "judge-response.md").read_text())
    for field in ("scenario_id", "criteria", "failure_rationalization", "unscored"):
        require(grade[field] == raw[field], f"grade differs from blind judge: {field}")


def validate_scenario(suite, manifest, scenario):
    folder = suite / "runs" / manifest["run_id"] / scenario
    response_path = folder / "response.md"
    response = response_path.read_text()
    require(nonempty(response), "response.md is empty")
    sha = digest(response_path)
    capture = read_json(folder / "capture.json")
    require(capture["scenario_id"] == scenario, "capture scenario identity mismatch")
    require(capture["run_id"] == manifest["run_id"], "capture run identity mismatch")
    require(capture["source_revision"] == manifest["source_revision"], "capture source revision mismatch")
    require(capture["response_sha256"] == sha, "capture response digest mismatch")
    require(capture["subject_inputs_sha256"] == subject_inputs(manifest, scenario),
            "subject input digests mismatch")
    require(capture["frozen_artifacts_sha256"] == manifest["frozen_sha256"],
            "capture frozen digests mismatch")
    for key in ("agent_id", "model", "captured_by", "provenance"):
        require(nonempty(capture[key]), f"capture {key} missing")
    require(capture["context_mode"] == "fresh-none", "subject context was not fresh")
    start = datetime.fromisoformat(capture["started_at"].replace("Z", "+00:00"))
    finish = datetime.fromisoformat(capture["finished_at"].replace("Z", "+00:00"))
    require(start.tzinfo is not None and finish.tzinfo is not None and finish >= start,
            "invalid capture timestamps")
    grade = read_json(folder / "grade.json")
    return validate_grade(grade, response, scenario, sha, capture)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-red", action="store_true",
                        help="also require all five primary behavioral failures")
    parser.add_argument("--require-failure", choices=sorted(SCENARIOS),
                        help="require an observed primary failure for this scenario")
    args = parser.parse_args()
    suite = Path(__file__).resolve().parent
    try:
        manifest = validate_manifest(suite)
        replacement = validate_primary_selection(suite, manifest)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"INCOMPLETE: {error}")
        return 1
    failures, complete, errors, outcomes = 0, 0, [], {}
    try:
        validate_scenario(suite, manifest, "first-match-routing")
    except (OSError, ValueError, KeyError, TypeError) as error:
        errors.append(f"historical first-match-routing integrity: {error}")
    for scenario in sorted(manifest["scenarios"]):
        try:
            selected = replacement if scenario == "first-match-routing" else manifest
            outcome = validate_scenario(suite, selected, scenario)
            if scenario == "first-match-routing":
                validate_blind_judge(suite, selected)
            outcomes[scenario] = outcome
            complete += 1
            failures += outcome == "FAIL"
            print(f"{scenario}: primary {outcome}")
        except (OSError, ValueError, KeyError, TypeError) as error:
            errors.append(f"{scenario}: {error}")
    for error in errors:
        print(f"INCOMPLETE: {error}")
    print(f"{complete}/5 complete; {failures}/5 primary failures")
    if errors:
        return 1
    if args.require_failure and outcomes[args.require_failure] != "FAIL":
        print(f"RED not demonstrated: {args.require_failure}")
        return 1
    if args.require_red and failures != 5:
        print(f"RED incomplete: {failures}/5; strict all-RED diagnostic not satisfied")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
