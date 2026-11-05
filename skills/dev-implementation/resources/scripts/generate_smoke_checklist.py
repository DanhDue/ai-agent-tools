"""Automated manual smoke walkthrough checklist generator from canonical BDD Happy Path scenarios."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

URL_REGEX = re.compile(r"https?://[^\s)`'\"]+")
COMMAND_REGEX = re.compile(r"`([^`]+)`")
CLI_ENTRYPOINT_REGEX = re.compile(
    r"\b(?:python3?|npx|npm|cargo|pytest|mypy|ruff|git)\s+[^\s,;`]+|\bd3nexus:[a-zA-Z0-9_-]+|\b[a-zA-Z0-9_-]+-quality-check\b",
    re.IGNORECASE,
)


def parse_bdd_scenarios(content: str) -> list[dict[str, Any]]:
    """Parse scenario blocks and steps from bdd_scenarios markdown content."""
    scenarios: list[dict[str, Any]] = []
    current_scenario: dict[str, Any] | None = None

    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        header_match = re.match(r"^(?:#{1,4}\s+)?Scenario:\s*(?:\[([^\]]+)\])?\s*(.*)$", stripped)
        if header_match:
            if current_scenario:
                scenarios.append(current_scenario)
            scenario_id = header_match.group(1) or ""
            scenario_title = header_match.group(2).strip()
            current_scenario = {
                "id": scenario_id,
                "title": scenario_title,
                "given": [],
                "when": [],
                "then": [],
                "and": [],
            }
            continue

        if current_scenario is not None:
            stripped = line.strip()
            if stripped.startswith("Given "):
                current_scenario["given"].append(stripped[6:].strip())
            elif stripped.startswith("When "):
                current_scenario["when"].append(stripped[5:].strip())
            elif stripped.startswith("Then "):
                current_scenario["then"].append(stripped[5:].strip())
            elif stripped.startswith("And "):
                current_scenario["and"].append(stripped[4:].strip())

    if current_scenario:
        scenarios.append(current_scenario)

    return scenarios


def extract_target_from_text(text: str) -> str:
    """Extract a URL, backticked command, or bare CLI tooling entrypoint from text."""
    url_match = URL_REGEX.search(text)
    if url_match:
        return url_match.group(0)

    cmd_match = COMMAND_REGEX.search(text)
    if cmd_match:
        return f"`{cmd_match.group(1)}`"

    cli_match = CLI_ENTRYPOINT_REGEX.search(text)
    if cli_match:
        return f"`{cli_match.group(0)}`"

    return "CLI / Workspace Root"


def extract_smoke_steps(
    scenarios: list[dict[str, Any]],
    min_steps: int = 3,
    max_steps: int = 5,
) -> list[dict[str, str]]:
    """Extract 3-5 concise, actionable manual smoke steps from primary BDD Happy Paths."""
    happy_paths = [s for s in scenarios if "-HP-" in s.get("id", "") or "Happy Path" in s.get("title", "")]

    if not happy_paths:
        # Fall back to any scenarios if no explicit HP exists
        happy_paths = scenarios

    raw_steps: list[dict[str, str]] = []

    for sc in happy_paths:
        whens = sc.get("when", [])
        thens = sc.get("then", [])
        ands = sc.get("and", [])

        action = " ".join(whens) if whens else sc.get("title", "Execute scenario workflow")
        outcome = " ".join(thens) if thens else (" ".join(ands) if ands else "Succeeds without errors")

        # Determine target
        combined = f"{' '.join(sc.get('given', []))} {action}"
        target = extract_target_from_text(combined)

        raw_steps.append(
            {
                "scenario_id": sc.get("id", ""),
                "target": target,
                "action": action,
                "outcome": outcome,
            }
        )

    # Ensure step count is clamped between min_steps and max_steps
    steps = raw_steps[:max_steps]

    # If fewer than min_steps, split multi-actions or expand with additional details
    while len(steps) < min_steps and len(raw_steps) > 0:
        idx = len(steps)
        orig = raw_steps[idx % len(raw_steps)]
        steps.append(
            {
                "scenario_id": f"{orig['scenario_id']}-verify",
                "target": orig["target"],
                "action": f"Verify state after {orig['action']}",
                "outcome": f"Confirm outcome: {orig['outcome']}",
            }
        )

    return steps


def render_smoke_checklist_markdown(epic_slug: str, steps: list[dict[str, str]]) -> str:
    """Format extracted smoke steps into a clean GitHub Flavored Markdown checklist."""
    clean_title = epic_slug.replace("_", " ").replace("-", " ").title()
    lines = [
        f"# Manual Smoke Walkthrough Checklist: {clean_title}",
        "",
        "> [!NOTE]",
        "> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.",
        "> Run through these 3–5 high-leverage user journeys before final sign-off.",
        "",
        "| Step | Target (URL / CLI) | Action | Observable Outcome |",
        "| :---: | :--- | :--- | :--- |",
    ]

    for idx, step in enumerate(steps, 1):
        target = step["target"].replace("|", "\\|")
        action = step["action"].replace("|", "\\|")
        outcome = step["outcome"].replace("|", "\\|")
        lines.append(f"| {idx} | {target} | {action} | {outcome} |")

    lines.append("")
    lines.append("## Sign-off")
    lines.append("- [ ] All steps completed manually with expected outcomes verified.")
    lines.append("- **Reviewer / Date:** __________________")
    lines.append("")

    return "\n".join(lines)


def generate_smoke_checklist(
    epic_dir: str | Path,
    workspace_root: Path | str | None = None,
    output_path: Path | str | None = None,
    bdd_file: Path | str | None = None,
) -> Path:
    """Generate manual_smoke_checklist.md from BDD scenarios for the specified epic."""
    ws = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
    epic_path = Path(epic_dir)
    resolved_epic_dir = epic_path if epic_path.is_absolute() else (ws / ".devtool" / "epic" / epic_path)

    if not resolved_epic_dir.is_dir():
        raise FileNotFoundError(f"Epic directory not found at {resolved_epic_dir}")

    source_bdd = Path(bdd_file) if bdd_file else (resolved_epic_dir / "bdd_scenarios.en.md")
    if not source_bdd.is_file():
        raise FileNotFoundError(f"BDD scenarios file not found at {source_bdd}")

    content = source_bdd.read_text(encoding="utf-8")
    scenarios = parse_bdd_scenarios(content)
    steps = extract_smoke_steps(scenarios)

    rendered = render_smoke_checklist_markdown(resolved_epic_dir.name, steps)

    dest = Path(output_path) if output_path else (resolved_epic_dir / "manual_smoke_checklist.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered, encoding="utf-8")

    return dest


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for generate_smoke_checklist."""
    parser = argparse.ArgumentParser(
        description="Generate 3-5 step manual smoke walkthrough checklist from BDD Happy Path scenarios."
    )
    parser.add_argument(
        "--epic-dir",
        required=True,
        type=str,
        help="Epic directory name or path (e.g. web_quality_check_and_integration_gate).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional explicit output markdown path.",
    )
    parser.add_argument(
        "--bdd-file",
        type=str,
        default=None,
        help="Optional explicit path to bdd_scenarios.en.md file.",
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=".",
        help="Workspace root path.",
    )

    args = parser.parse_args(argv)

    try:
        out = generate_smoke_checklist(
            epic_dir=args.epic_dir,
            workspace_root=args.workspace_root,
            output_path=args.output,
            bdd_file=args.bdd_file,
        )
        print(f"Generated manual smoke checklist at {out}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Error generating smoke checklist: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
