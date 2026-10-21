#!/usr/bin/env python3
"""Local model review through Ollama: transport, review slices, and the prompt base.

The model behind Ollama has no tools, so every pass is self-contained. This module never imports
run_external_review.py; the runner imports it.
"""
from __future__ import annotations

import json
import math
import os
import re
import urllib.error
import urllib.request
from collections.abc import Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from string import Template
from typing import Any

from check_bdd_traceability import FENCE, LEADING_TAG, SCENARIO_LINE, covers_of
from task_contract import git_run, section

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_NUM_CTX = 32768
PROMPT_SHARE = 0.6
BYTES_PER_TOKEN = 3
TAIL_LINES = 15
EXTENSIONS = {".dart": "Flutter", ".kt": "Android", ".kts": "Android",
              ".swift": "iOS", ".rs": "Rust", ".py": "Python"}
PLATFORM_ORDER = ("Flutter", "Android", "iOS", "Rust", "Python")
DIFF_HEADER = re.compile(r"^diff --git a/.* b/(.*)$")

REFERENCES = Path(__file__).resolve().parent.parent.parent / "references"
PROMPT = REFERENCES / "local-review-prompt.md"
CHECKLISTS = REFERENCES / "local-review-checklists.md"
PLATFORMS = REFERENCES / "local-review-platforms.md"
RULES = REFERENCES / "review-rules.md"


class LocalReviewError(Exception):
    """A probe, budget or transport failure; str(error) is the reason shown to the developer."""


@dataclass(frozen=True)
class Reply:
    content: str  # answer_text of message.content; "" on failure
    done_reason: str | None
    error: str | None  # None on HTTP 200


def host_from_env() -> str:
    host = os.environ.get("OLLAMA_HOST") or DEFAULT_HOST
    return (host if "://" in host else f"http://{host}").rstrip("/")


def post(url: str, payload: dict[str, Any], timeout: int) -> Any:
    request = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def probe(host: str, model: str, timeout: int = 10) -> int | None:
    """Check the server and the model; return the Modelfile's num_ctx, or None when it sets none."""
    try:
        urllib.request.urlopen(f"{host}/api/version", timeout=timeout).close()
    except OSError as error:  # URLError is an OSError
        raise LocalReviewError(f"Ollama server not reachable at {host}") from error
    try:
        shown = post(f"{host}/api/show", {"model": model}, timeout)
    except urllib.error.HTTPError as error:
        error.close()
        if error.code == 404:
            raise LocalReviewError(f"model {model} is not installed (ollama list)") from error
        raise LocalReviewError(f"HTTP {error.code} from {host}/api/show") from error
    except OSError as error:
        raise LocalReviewError(f"Ollama server not reachable at {host}") from error
    for line in str(shown.get("parameters") or "").splitlines():
        name, _, value = line.strip().partition(" ")
        if name == "num_ctx":
            return int(value.strip())
    return None


def chat_options(model_ctx: int | None, flag_ctx: int | None, prompt_tokens: int) -> dict[str, int]:
    """Leave sampling to the Modelfile; send num_ctx only when it is not the Modelfile's own."""
    effective = flag_ctx or model_ctx or DEFAULT_NUM_CTX
    options = {"num_predict": effective - prompt_tokens}
    if flag_ctx is not None or model_ctx is None:
        options["num_ctx"] = effective
    return options


def answer_text(content: str) -> str:
    """The answer after any inline thinking: the text after the last </think>, stripped."""
    return content.rpartition("</think>")[2].strip()


def chat(host: str, model: str, system: str, user: str, options: dict[str, int], timeout: int) -> Reply:
    """One non-streaming /api/chat call; failures become a Reply with its error set, never an exception."""
    payload = {"model": model,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
               "stream": False, "options": options}
    try:
        data = post(f"{host}/api/chat", payload, timeout)
    except urllib.error.HTTPError as error:
        with error:
            body = error.read().decode("utf-8", "replace")
        return Reply("", None, f"HTTP {error.code}: {body[:500]}")
    except TimeoutError:
        return Reply("", None, f"timed out after {timeout} seconds")
    except urllib.error.URLError as error:
        if isinstance(error.reason, TimeoutError):
            return Reply("", None, f"timed out after {timeout} seconds")
        return Reply("", None, str(error))
    except (OSError, ValueError) as error:
        return Reply("", None, str(error))
    message = data.get("message") or {}
    return Reply(answer_text(str(message.get("content") or "")), data.get("done_reason"), None)


@dataclass(frozen=True)
class Part:
    section: str  # the heading it renders under
    name: str  # what Not shown lists once it is dropped
    body: str
    rank: int | None  # drop order, lowest first; None is never cut


@dataclass(frozen=True)
class Slice:
    label: str  # the task id, or "epic"
    kind: str  # "task" or "epic"
    paths: tuple[str, ...]  # changed paths shown in this slice's diffs
    omitted: tuple[str, ...]  # names dropped by fit, in drop order
    sections: tuple[str, ...] = ()
    parts: tuple[Part, ...] = ()


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text.encode("utf-8")) / BYTES_PER_TOKEN)


def fenced(text: str, language: str) -> str:
    """A code fence longer than any backtick run inside the text."""
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{fence}{language}\n{text.rstrip()}\n{fence}"


def git_text(root: Path, *args: str) -> str:
    return git_run(root, *args).decode("utf-8", "replace")


def file_diffs(root: Path, commit: str, excludes: tuple[str, ...]) -> list[tuple[str, str]]:
    """(path, diff) for each file a commit changes, with the excluded paths left out."""
    diffs: list[tuple[str, list[str]]] = []
    for line in git_text(root, "diff", f"{commit}^", commit, "--", ".", *excludes).splitlines():
        if (header := DIFF_HEADER.match(line)):
            diffs.append((header.group(1), []))
        if diffs:
            diffs[-1][1].append(line)
    return [(path, "\n".join(lines)) for path, lines in diffs]


def scenario_blocks(text: str, ids: list[str]) -> list[str]:
    """The Gherkin block of each wanted scenario: its Scenario line up to the next one or the fence."""
    blocks: dict[str, list[str]] = {}
    current: list[str] | None = None
    fence: str | None = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if marker and fence is None:
            fence, current = marker.group(1), None
            continue
        if marker and fence and marker.group(1)[0] == fence[0] and not marker.group(2):
            fence, current = None, None
            continue
        scenario = SCENARIO_LINE.match(line) if fence else None
        if scenario:
            tag = LEADING_TAG.match(scenario.group(1).strip())
            current = blocks.setdefault(tag.group(1), []) if tag and tag.group(1) in ids else None
        if current is not None:
            current.append(line)
    return ["\n".join(blocks[identifier]).rstrip() for identifier in ids if identifier in blocks]


def evidence_lines(data: dict[str, Any]) -> str:
    """Each recorded row of the red and verify runs, with the tail of its output."""
    entries: list[str] = []
    for run in ("red", "verify"):
        for row in (data.get("runs", {}).get(run) or {}).get("rows", []):
            tail = "\n".join((row.get("output_tail") or [])[-TAIL_LINES:])
            entries.append(f"- {run} {row.get('id')} {row.get('phase')} `{row.get('command')}`; "
                           f"expect {row.get('expect')}; exit {row.get('exit')}; {row.get('outcome')}\n\n"
                           + fenced(tail or "(no output)", "text"))
    return "\n\n".join(entries)


def task_slice(root: Path, epic_path: str, task: str, commit: str, excludes: tuple[str, ...]) -> Slice:
    """Read from the working tree, which the runner requires to be clean at the candidate SHA."""
    task_path = root / epic_path / f"{task}.md"
    short = git_text(root, "rev-parse", "--short", commit).strip()
    diff_section = f"## Diff of {short}"
    scenarios = (root / epic_path / "bdd_scenarios.en.md").read_text(encoding="utf-8")
    evidence = json.loads((root / epic_path / "evidence" / f"{task}.json").read_text(encoding="utf-8"))
    diffs = file_diffs(root, commit, excludes)
    ranks = {path: rank for rank, (path, _) in enumerate(sorted(diffs, key=lambda item: -len(item[1])))}
    parts = [Part("## Task file", "task file", fenced(task_path.read_text(encoding="utf-8"), "markdown"), None),
             *(Part("## Scenarios covered", "scenarios", fenced(block, "gherkin"), None)
               for block in scenario_blocks(scenarios, covers_of(task_path))),
             Part("## Evidence", "evidence", evidence_lines(evidence) or "None.", None),
             *(Part(diff_section, path, f"### {path}\n\n{fenced(diff, 'diff')}", ranks[path]) for path, diff in diffs)]
    sections = ("## Task file", "## Scenarios covered", "## Evidence", diff_section)
    return Slice(task, "task", tuple(path for path, _ in diffs), (), sections, tuple(parts))


def epic_slice(root: Path, epic_path: str, base: str, sha: str, audit_output: str, results_output: str,
               outside: list[str], excludes: tuple[str, ...]) -> Slice:
    folder = root / epic_path
    hld = folder / f"{Path(epic_path).name}.en.md"
    specs = sorted(folder.glob("*-design.en.md"))
    stat = git_text(root, "diff", "--stat", f"{base}...{sha}", "--", ".", ":(exclude).devtool/**").strip()
    parts: list[Part] = []
    paths: list[str] = []
    for rank, commit in enumerate(outside):
        title = git_text(root, "log", "-1", "--format=%h %s", commit).strip()
        diffs = file_diffs(root, commit, excludes)
        paths.extend(path for path, _ in diffs if path not in paths)
        body = "\n\n".join(fenced(diff, "diff") for _, diff in diffs) or "No change outside excluded paths."
        parts.append(Part("## Commits outside tasks", title, f"### {title}\n\n{body}", rank))
    rank = len(outside)
    parts += [Part("## Spec", spec.name, fenced(spec.read_text(encoding="utf-8"), "markdown"), rank + index)
              for index, spec in enumerate(specs)]
    parts += [Part("## HLD", hld.name, fenced(hld.read_text(encoding="utf-8"), "markdown"), rank + len(specs)),
              Part("## Audit", "audit", fenced(audit_output, "text"), None),
              Part("## Traceability", "traceability", fenced(results_output, "text"), None),
              Part("## Diff stat", "diff stat", fenced(stat or "(no changes outside .devtool/)", "text"), None)]
    if not outside:
        parts.append(Part("## Commits outside tasks", "commits outside tasks", "None.", None))
    sections = ("## Spec", "## HLD", "## Audit", "## Traceability", "## Diff stat", "## Commits outside tasks")
    return Slice("epic", "epic", tuple(paths), (), sections, tuple(parts))


def build_slices(root: Path, epic_dir: str, base: str, sha: str, audit_output: str,
                 results_output: str, excludes: tuple[str, ...]) -> list[Slice]:
    """One slice per task commit, in commit order, then the epic slice."""
    epic_path = f".devtool/epic/{epic_dir}"
    order = git_text(root, "rev-list", "--reverse", f"{base}..{sha}").split()
    task_commits: dict[str, str] = {}
    for evidence in git_text(root, "ls-tree", "--name-only", sha, f"{epic_path}/evidence/").split():
        if evidence.endswith(".json"):
            commit = git_text(root, "log", "-1", "--format=%H", f"{base}..{sha}", "--", evidence).strip()
            if commit:
                task_commits[Path(evidence).stem] = commit
    tasks = sorted(task_commits, key=lambda task: order.index(task_commits[task]))
    outside = [commit for commit in order if commit not in task_commits.values() and any(
        not path.startswith(".devtool/")
        for path in git_text(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit).split())]
    slices = [task_slice(root, epic_path, task, task_commits[task], excludes) for task in tasks]
    return [*slices, epic_slice(root, epic_path, base, sha, audit_output, results_output, outside, excludes)]


def render_user(slice_: Slice) -> str:
    """The user message: every section in order, then the names fit dropped under Not shown."""
    blocks: list[str] = []
    for heading in slice_.sections:
        bodies = [part.body for part in slice_.parts if part.section == heading]
        blocks.append(f"{heading}\n\n" + ("\n\n".join(bodies) or "Dropped to fit the context budget; see Not shown."))
    blocks.append("## Not shown\n\n" + ("\n".join(f"- {name}" for name in slice_.omitted) or "None."))
    return "\n\n".join(blocks) + "\n"


def fit(slice_: Slice, budget_tokens: int) -> Slice:
    """Drop droppable parts, lowest rank first, until the user message fits the budget."""
    droppable = sorted((part for part in slice_.parts if part.rank is not None), key=lambda part: part.rank or 0)
    floor = replace(slice_, parts=tuple(part for part in slice_.parts if part.rank is None),
                    omitted=slice_.omitted + tuple(part.name for part in droppable))
    needed = estimate_tokens(render_user(floor))
    if needed > budget_tokens:
        raise LocalReviewError(f"{slice_.label} needs {needed} tokens of never-cut content but the budget is "
                               f"{budget_tokens}; raise --num-ctx")
    fitted = slice_
    for part in droppable:
        if estimate_tokens(render_user(fitted)) <= budget_tokens:
            break
        fitted = replace(fitted, parts=tuple(kept for kept in fitted.parts if kept is not part),
                         omitted=fitted.omitted + (part.name,))
    return fitted


def platform_sections(paths: Iterable[str]) -> list[str]:
    """The platform rule sections for the file extensions among the paths, each with its heading."""
    present = {EXTENSIONS[suffix] for path in paths if (suffix := Path(path).suffix) in EXTENSIONS}
    text = PLATFORMS.read_text(encoding="utf-8")
    return [f"## {name}\n{section(text, name) or ''}".strip() for name in PLATFORM_ORDER if name in present]


def render_system(slice_: Slice) -> str:
    """The prompt base with the shared rules, this slice's platform rules and its pass checklist."""
    checklist = "Task pass" if slice_.kind == "task" else "Epic pass"
    checklists = CHECKLISTS.read_text(encoding="utf-8")
    return Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
        rules=RULES.read_text(encoding="utf-8").strip(),
        platform_rules="\n\n".join(platform_sections(slice_.paths)) or "No platform rules apply to this slice.",
        checklist=f"## {checklist}\n{section(checklists, checklist) or ''}".strip(),
    )
