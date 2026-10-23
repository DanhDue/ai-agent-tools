#!/usr/bin/env python3
"""Check epic readiness before implementation or review.

Usage:
    check_epic_readiness.py <epic_dir> [--baseline] [--row-timeout 600]
"""
from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

# Sibling modules
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import check_bdd_traceability as cb
import run_task_checks as rtc
import sync_task_status as sts
import task_contract as tc

LINTER_PATH = SCRIPTS_DIR.parents[2] / "doc_quality_check" / "resources" / "scripts" / "check_document.py"


@dataclass(frozen=True)
class Finding:
    check: str     # "R1" ... "R8", "R5b", "R7b"
    severity: str  # "FAIL" or "WARN"
    message: str


@dataclass(frozen=True)
class Context:
    root: Path
    epic_dir: str
    epic_slug: str
    hld_text: str
    tasks: dict[Path, str]
    results: list[str]
    roots: list[str]
    baseline: bool = False
    row_timeout: int = 600


def parse_integration_test_roots(hld_text: str) -> list[str]:
    for line in hld_text.splitlines():
        if line.startswith("Integration test roots:"):
            _, rest = line.split(":", 1)
            return [part.strip() for part in rest.split(",") if part.strip()]
    return []


def load_context(
    root: Path,
    epic_dir: str,
    *,
    baseline: bool = False,
    row_timeout: int = 600,
) -> Context:
    epic_path = root / ".devtool" / "epic" / epic_dir
    hld_path = epic_path / f"{epic_dir}.en.md"
    hld_text = hld_path.read_text(encoding="utf-8")

    task_paths = sorted(epic_path.glob("task_*.md"))
    tasks: dict[Path, str] = {p: p.read_text(encoding="utf-8") for p in task_paths}

    epic_slug = epic_dir
    for text in tasks.values():
        m = re.search(r'^epic:\s*"?([^"\n]+)"?', text, re.MULTILINE)
        if m:
            epic_slug = m.group(1).strip()
            break

    results = tc.parse_integration_results(hld_text)
    roots = parse_integration_test_roots(hld_text)

    return Context(
        root=root,
        epic_dir=epic_dir,
        epic_slug=epic_slug,
        hld_text=hld_text,
        tasks=tasks,
        results=results,
        roots=roots,
        baseline=baseline,
        row_timeout=row_timeout,
    )


def get_last_non_empty_line(*outputs: str) -> str:
    combined = "\n".join(outputs)
    lines = [ln.strip() for ln in combined.splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def check_preflight(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    task_paths_str = [str(p) for p in ctx.tasks]
    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir

    # 1. compute_execution_order.py <epic_slug>
    cmd1 = [sys.executable, str(SCRIPTS_DIR / "compute_execution_order.py"), ctx.epic_slug]
    res1 = subprocess.run(cmd1, check=False, cwd=ctx.root, capture_output=True, text=True)
    if res1.returncode != 0:
        last_line = get_last_non_empty_line(res1.stdout, res1.stderr)
        findings.append(Finding("R1", "FAIL", f"compute_execution_order.py: {last_line}"))
    else:
        m_match = re.search(r"(\d+)\s+matched", res1.stdout)
        if m_match:
            m = int(m_match.group(1))
            if m != len(ctx.tasks):
                findings.append(
                    Finding(
                        "R1",
                        "FAIL",
                        f"task mirror count: {m} matched, {len(ctx.tasks)} in the epic directory",
                    )
                )

    # 2. check_bdd_traceability.py plan
    cmd2 = [
        sys.executable,
        str(SCRIPTS_DIR / "check_bdd_traceability.py"),
        "plan",
        "--scenarios",
        str(epic_path / "bdd_scenarios.en.md"),
        "--tasks",
        *task_paths_str,
    ]
    res2 = subprocess.run(cmd2, check=False, cwd=ctx.root, capture_output=True, text=True)
    if res2.returncode != 0:
        last_line = get_last_non_empty_line(res2.stdout, res2.stderr)
        findings.append(Finding("R1", "FAIL", f"check_bdd_traceability.py plan: {last_line}"))

    # 3. check_task_contract.py --design
    cmd3 = [
        sys.executable,
        str(SCRIPTS_DIR / "check_task_contract.py"),
        "--design",
        "--hld",
        str(epic_path / f"{ctx.epic_dir}.en.md"),
        "--tasks",
        *task_paths_str,
    ]
    res3 = subprocess.run(cmd3, check=False, cwd=ctx.root, capture_output=True, text=True)
    if res3.returncode != 0:
        last_line = get_last_non_empty_line(res3.stdout, res3.stderr)
        findings.append(Finding("R1", "FAIL", f"check_task_contract.py --design: {last_line}"))

    # 4. check_document.py
    bilingual_files = sorted(set(epic_path.glob("*.en.md")) | set(epic_path.glob("*.vi.md")))
    if bilingual_files:
        cmd_doc1 = [
            sys.executable,
            str(LINTER_PATH),
            "--require-toc",
            "--require-bilingual",
            *[str(f) for f in bilingual_files],
        ]
        res_doc1 = subprocess.run(cmd_doc1, check=False, cwd=ctx.root, capture_output=True, text=True)
        if res_doc1.returncode != 0:
            last_line = get_last_non_empty_line(res_doc1.stdout, res_doc1.stderr)
            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))

    handoff_file = epic_path / "handoff.md"
    if handoff_file.is_file():
        cmd_handoff = [
            sys.executable,
            str(LINTER_PATH),
            "--require-toc",
            str(handoff_file),
        ]
        res_handoff = subprocess.run(cmd_handoff, check=False, cwd=ctx.root, capture_output=True, text=True)
        if res_handoff.returncode != 0:
            last_line = get_last_non_empty_line(res_handoff.stdout, res_handoff.stderr)
            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))

    if task_paths_str:
        cmd_tasks = [
            sys.executable,
            str(LINTER_PATH),
            *task_paths_str,
        ]
        res_tasks = subprocess.run(cmd_tasks, check=False, cwd=ctx.root, capture_output=True, text=True)
        if res_tasks.returncode != 0:
            last_line = get_last_non_empty_line(res_tasks.stdout, res_tasks.stderr)
            findings.append(Finding("R1", "FAIL", f"check_document.py: {last_line}"))

    return findings


def check_task_mirrors(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    features_dir = ctx.root / ".devtool" / "features"
    done_dir = features_dir / "done"
    link_pattern = f"](../epic/{ctx.epic_dir}/"

    for task_path, epic_text in ctx.tasks.items():
        name = task_path.name
        mirror_path = features_dir / name
        if not mirror_path.is_file():
            mirror_path = done_dir / name
        if not mirror_path.is_file():
            findings.append(Finding("R2", "FAIL", f"{name}: no mirror in .devtool/features/"))
            continue

        mirror_text = mirror_path.read_text(encoding="utf-8")
        norm_mirror = mirror_text.replace(link_pattern, "](")

        if norm_mirror != epic_text:
            epic_lines = epic_text.splitlines()
            mirror_lines = norm_mirror.splitlines()
            max_len = max(len(epic_lines), len(mirror_lines))
            diff_line_idx = -1
            epic_line_content = ""
            mirror_line_content = ""
            for i in range(max_len):
                el = epic_lines[i] if i < len(epic_lines) else ""
                ml = mirror_lines[i] if i < len(mirror_lines) else ""
                if el != ml:
                    diff_line_idx = i + 1
                    epic_line_content = el
                    mirror_line_content = ml
                    break
            diff_msg = (
                f"{name}: line {diff_line_idx}: {epic_line_content}"
                if not mirror_line_content
                else (
                    f"{name}: line {diff_line_idx}: {epic_line_content} != {mirror_line_content}"
                    if epic_line_content
                    else f"{name}: line {diff_line_idx}: {mirror_line_content}"
                )
            )
            findings.append(Finding("R2", "FAIL", diff_msg))

    return findings


def extract_scenario_blocks(text: str) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    in_gherkin = False
    fence_marker: str | None = None
    current_id: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        fence_match = cb.FENCE.match(line)
        if fence_match and fence_marker is None:
            fence_marker = fence_match.group(1)
            in_gherkin = fence_match.group(2).lower() == "gherkin"
            if not in_gherkin and current_id is not None:
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
            continue
        if (
            fence_match
            and fence_marker
            and fence_match.group(1)[0] == fence_marker[0]
            and len(fence_match.group(1)) >= len(fence_marker)
            and not fence_match.group(2)
        ):
            fence_marker = None
            in_gherkin = False
            if current_id is not None:
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
            continue

        if not in_gherkin:
            continue

        sc_match = cb.SCENARIO_LINE.match(line)
        if sc_match:
            if current_id is not None:
                blocks[current_id] = current_lines
                current_lines = []
            rest = sc_match.group(1).strip()
            id_match = cb.ID_SHAPE.search(rest)
            if id_match:
                current_id = id_match.group(0)
                current_lines = [line.rstrip()]
            else:
                current_id = None
        elif current_id is not None:
            if not line.strip():
                blocks[current_id] = current_lines
                current_id = None
                current_lines = []
            else:
                current_lines.append(line.rstrip())

    if current_id is not None:
        blocks[current_id] = current_lines

    return blocks


def check_bdd_scenarios(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
    bdd_en_path = epic_path / "bdd_scenarios.en.md"
    if not bdd_en_path.is_file():
        return findings

    canonical_blocks = extract_scenario_blocks(bdd_en_path.read_text(encoding="utf-8"))

    for task_path, task_text in ctx.tasks.items():
        task_blocks = extract_scenario_blocks(task_text)
        for sc_id, t_lines in task_blocks.items():
            if sc_id in canonical_blocks and t_lines != canonical_blocks[sc_id]:
                findings.append(
                    Finding("R3", "FAIL", f"{task_path.name}: {sc_id} differs from bdd_scenarios.en.md")
                )

    bdd_vi_path = epic_path / "bdd_scenarios.vi.md"
    if bdd_vi_path.is_file():
        en_ids, _ = cb.scenario_ids(bdd_en_path)
        vi_ids, _ = cb.scenario_ids(bdd_vi_path)
        en_set = set(en_ids)
        vi_set = set(vi_ids)
        if en_set != vi_set:
            for missing_or_extra in sorted(en_set ^ vi_set):
                findings.append(
                    Finding("R3", "FAIL", f"bdd_scenarios.vi.md: {missing_or_extra} missing or extra")
                )

    return findings


def check_tier_tags(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    bdd_en_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir / "bdd_scenarios.en.md"
    if not bdd_en_path.is_file():
        return findings

    in_gherkin = False
    fence_marker: str | None = None
    for line in bdd_en_path.read_text(encoding="utf-8").splitlines():
        fence_match = cb.FENCE.match(line)
        if fence_match and fence_marker is None:
            fence_marker = fence_match.group(1)
            in_gherkin = fence_match.group(2).lower() == "gherkin"
            continue
        if (
            fence_match
            and fence_marker
            and fence_match.group(1)[0] == fence_marker[0]
            and len(fence_match.group(1)) >= len(fence_marker)
            and not fence_match.group(2)
        ):
            fence_marker = None
            in_gherkin = False
            continue

        if not in_gherkin:
            continue

        sc_match = cb.SCENARIO_LINE.match(line)
        if not sc_match:
            continue

        rest = sc_match.group(1).strip()
        tags = re.findall(r"\[([^\]]+)\]", rest)
        if not tags:
            continue
        sc_id = tags[0].strip()
        tier_tag = tags[1].strip() if len(tags) > 1 else "none"

        if tier_tag not in ("Tier A - Unit", "Tier C - Integration"):
            findings.append(Finding("R4", "FAIL", f'{sc_id}: tier tag "{tier_tag}"'))

    return findings


def check_grounding(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []

    # --- R5: Symbol Grounding ---
    target_header_re = re.compile(
        r"^\s*-\s*\*\*(?:Target Files & Symbols|Target files and symbols)\*\*:\s*(.*)$",
        re.IGNORECASE,
    )
    sub_bullet_re = re.compile(r"^\s*-\s+`([^`]+)`:\s*(.*)$")
    token_re = re.compile(r"`([^`]+)`")
    ident_re = re.compile(r"^[A-Za-z_][\w.]*(?:\(\))?$")

    for task_path, task_text in ctx.tasks.items():
        impact_body = tc.section(task_text, "Impact Analysis & Blast Radius")
        if not impact_body:
            for heading in (
                "Impact Analysis & Blast Radius",
                "Impact analysis & blast radius",
                "Impact Analysis and Blast Radius",
            ):
                impact_body = tc.section(task_text, heading)
                if impact_body:
                    break
        if not impact_body:
            continue

        allowed_files = tc.parse_allowed_files(task_text)
        new_patterns = {ap.pattern for ap in allowed_files if ap.new}

        in_target_symbols = False
        target_lines: list[str] = []
        for line in impact_body.splitlines():
            if target_header_re.match(line):
                in_target_symbols = True
                continue
            if in_target_symbols:
                if re.match(r"^\s*-\s+\*\*", line) or (line.startswith("- ") and not line.startswith("  - ")):
                    break
                target_lines.append(line)

        for line in target_lines:
            sub_m = sub_bullet_re.match(line)
            if not sub_m:
                continue
            path_str = sub_m.group(1).strip()
            rest = sub_m.group(2)

            full_path = ctx.root / path_str
            if not full_path.is_file() or path_str in new_patterns:
                continue

            try:
                file_text = full_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            for span_m in token_re.finditer(rest):
                token_raw = span_m.group(1).strip()
                if not ident_re.match(token_raw):
                    continue
                prefix = rest[:span_m.start()]
                if re.search(r"\bnew\s+$", prefix):
                    continue

                clean_name = token_raw.removesuffix("()")
                name = clean_name.split(".")[-1]
                if name not in file_text:
                    findings.append(Finding("R5", "FAIL", f"{task_path.name}: {name} not in {path_str}"))

    # --- R5b: Route Grounding (WARN) ---
    route_re = re.compile(r"(?<![\w/])/api/[\w\-/{}.:]*[\w}]")
    routes_to_check: list[str] = []
    texts_to_scan = list(ctx.tasks.values()) + [ctx.hld_text]

    for text in texts_to_scan:
        for match in route_re.finditer(text):
            r = match.group(0)
            if "{" in r:
                r = r.split("{", 1)[0]
            r = r.rstrip("/")
            if r and r not in routes_to_check:
                routes_to_check.append(r)

    if routes_to_check:
        try:
            ls_proc = subprocess.run(
                ["git", "ls-files"],
                check=False,
                cwd=ctx.root,
                capture_output=True,
                text=True,
            )
            files_list = [
                ctx.root / p
                for p in ls_proc.stdout.splitlines()
                if not p.startswith((".devtool/", "docs/")) and not p.endswith(".md")
            ]
        except OSError:
            files_list = []

        tracked_contents: list[str] = []
        for f in files_list:
            if f.is_file():
                try:
                    tracked_contents.append(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass

        for route in routes_to_check:
            if not any(route in content for content in tracked_contents):
                findings.append(Finding("R5b", "WARN", f"{route}: not found in tracked source"))

    return findings


def check_gate4_coverage(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []

    results_tokens_list: list[list[str]] = []
    for cmd in ctx.results:
        try:
            results_tokens_list.append(shlex.split(cmd))
        except ValueError:
            results_tokens_list.append(cmd.split())

    for task_path, task_text in ctx.tasks.items():
        covers = cb.covers_of(task_path)
        try:
            rows, _ = tc.parse_verification(task_text)
        except tc.ContractError:
            continue

        tier_c_rows = [r for r in rows if r.phase == "TIER-C"]
        if covers and not tier_c_rows:
            findings.append(Finding("R6", "FAIL", f"{task_path.name}: Covers without a TIER-C row"))
            continue

        for r in tier_c_rows:
            try:
                tokens = shlex.split(r.command)
            except ValueError:
                tokens = r.command.split()

            for t in tokens:
                if not any(t.startswith(root) for root in ctx.roots):
                    continue

                covered = False
                for res_toks in results_tokens_list:
                    if t in res_toks:
                        covered = True
                        break
                    if any(rt.endswith("/") and t.startswith(rt) for rt in res_toks):
                        covered = True
                        break

                if not covered:
                    findings.append(
                        Finding(
                            "R6",
                            "FAIL",
                            f"{task_path.name}:{r.id}: {t} is in no Integration results command",
                        )
                    )

    return findings


def check_metadata(ctx: Context) -> list[Finding]:
    findings: list[Finding] = []
    epic_path = ctx.root / ".devtool" / "epic" / ctx.epic_dir
    handoff_file = epic_path / "handoff.md"
    has_handoff = handoff_file.is_file()

    status_match = re.search(r"^- \*\*Status\*\*:\s*(.*)$", ctx.hld_text, re.MULTILINE)
    hld_status = status_match.group(1).strip() if status_match else ""

    if hld_status.startswith("Packaged") and not has_handoff:
        findings.append(Finding("R7", "FAIL", "Status starts with Packaged but handoff.md is missing"))

    if has_handoff:
        valid_prefixes = ("Packaged", "In Progress", "Done")
        if not any(hld_status.startswith(prefix) for prefix in valid_prefixes):
            findings.append(Finding("R7", "FAIL", f"handoff.md exists but Status is '{hld_status}'"))

        handoff_text = handoff_file.read_text(encoding="utf-8")
        design_commit_match = re.search(
            r"^- \*\*Design commit\*\*:\s*`?([^`\n]+)`?", handoff_text, re.MULTILINE
        )
        if design_commit_match:
            design_commit = design_commit_match.group(1).strip()
            if design_commit != "uncommitted":
                check_ancestor = subprocess.run(
                    ["git", "merge-base", "--is-ancestor", design_commit, "HEAD"],
                    check=False,
                    cwd=ctx.root,
                    capture_output=True,
                )
                if check_ancestor.returncode != 0:
                    findings.append(
                        Finding(
                            "R7",
                            "FAIL",
                            f"handoff.md Design commit `{design_commit}` is not an ancestor of HEAD",
                        )
                    )
        else:
            findings.append(Finding("R7", "FAIL", "handoff.md is missing 'Design commit' line"))

    for task_path, task_text in ctx.tasks.items():
        epic_m = re.search(r'^epic:\s*"?([^"\n]+)"?', task_text, re.MULTILINE)
        t_epic = epic_m.group(1).strip() if epic_m else ""
        if t_epic != ctx.epic_slug:
            findings.append(
                Finding("R7", "FAIL", f"{task_path.name}: epic '{t_epic}' differs from '{ctx.epic_slug}'")
            )

        status_m = re.search(r'^status:\s*"?([^"\n]+)"?', task_text, re.MULTILINE)
        t_status = status_m.group(1).strip() if status_m else ""
        if t_status not in sts.TASK_STATUSES:
            findings.append(
                Finding("R7", "FAIL", f"{task_path.name}: status '{t_status}' not in TASK_STATUSES")
            )

    spec_files = list(epic_path.glob("*-design.en.md"))
    if spec_files:
        spec_text = spec_files[0].read_text(encoding="utf-8")
        spec_status_m = re.search(r"^- \*\*Status\*\*:\s*(.*)$", spec_text, re.MULTILINE)
        if spec_status_m:
            spec_status = spec_status_m.group(1).strip()
            draft_pattern = re.compile(r"draft|awaiting|under .*review|bản nháp|chờ duyệt", re.IGNORECASE)
            if draft_pattern.search(spec_status):
                findings.append(Finding("R7b", "WARN", f"spec status: {spec_status}"))

    return findings


def check_baseline(ctx: Context) -> list[Finding]:
    if not ctx.baseline:
        return []

    status_proc = subprocess.run(
        ["git", "status", "--porcelain"],
        check=False,
        cwd=ctx.root,
        capture_output=True,
        text=True,
    )
    if status_proc.stdout.strip():
        return [Finding("R8", "WARN", "baseline skipped: dirty tree")]

    findings: list[Finding] = []

    new_paths: set[str] = set()
    for t_text in ctx.tasks.values():
        for ap in tc.parse_allowed_files(t_text):
            if ap.new:
                new_paths.add(ap.pattern)

    for task_path, task_text in ctx.tasks.items():
        try:
            rows, _ = tc.parse_verification(task_text)
        except tc.ContractError:
            continue

        for row in rows:
            if row.phase not in ("GREEN", "TIER-B"):
                continue

            if any(np in row.command for np in new_paths):
                continue

            code, raw_output = rtc.run_command(row.command, ctx.root, ctx.row_timeout)
            if code is None:
                findings.append(
                    Finding(
                        "R8",
                        "WARN",
                        f"{task_path.stem}:{row.id} timeout after {ctx.row_timeout}s",
                    )
                )
            else:
                out_text = raw_output.decode("utf-8", errors="replace")
                mis = rtc.mismatch(row, code, out_text)
                if mis is not None:
                    findings.append(Finding("R8", "WARN", f"{task_path.stem}:{row.id} {mis}"))

    return findings


CHECKS: tuple[tuple[str, Callable[[Context], list[Finding]]], ...] = (
    ("R1", check_preflight),
    ("R2", check_task_mirrors),
    ("R3", check_bdd_scenarios),
    ("R4", check_tier_tags),
    ("R5", check_grounding),
    ("R6", check_gate4_coverage),
    ("R7", check_metadata),
    ("R8", check_baseline),
)


def run_checks(
    ctx: Context,
    *,
    baseline: bool = False,
    row_timeout: int = 600,
) -> list[Finding]:
    active_ctx = Context(
        root=ctx.root,
        epic_dir=ctx.epic_dir,
        epic_slug=ctx.epic_slug,
        hld_text=ctx.hld_text,
        tasks=ctx.tasks,
        results=ctx.results,
        roots=ctx.roots,
        baseline=baseline,
        row_timeout=row_timeout,
    )
    findings: list[Finding] = []
    for _check_id, check_fn in CHECKS:
        findings.extend(check_fn(active_ctx))
    return findings


def render_report(ctx: Context, findings: list[Finding]) -> str:
    lines: list[str] = [f"Epic: {ctx.epic_dir} ({ctx.epic_slug}), {len(ctx.tasks)} tasks"]

    by_check: dict[str, list[Finding]] = {}
    for f in findings:
        by_check.setdefault(f.check, []).append(f)

    for check_id in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        check_findings = by_check.get(check_id, [])
        has_fail = any(f.severity == "FAIL" for f in check_findings)
        if not has_fail:
            lines.append(f"{check_id} PASS")
        for f in check_findings:
            lines.append(f"{f.check} {f.severity} {f.message}")

        if check_id == "R5":
            for f in by_check.get("R5b", []):
                lines.append(f"{f.check} {f.severity} {f.message}")
        elif check_id == "R7":
            for f in by_check.get("R7b", []):
                lines.append(f"{f.check} {f.severity} {f.message}")

    if not ctx.baseline:
        lines.append("R8 SKIP")
    else:
        r8_findings = by_check.get("R8", [])
        has_fail = any(f.severity == "FAIL" for f in r8_findings)
        if not has_fail and not any(f.severity == "WARN" for f in r8_findings):
            lines.append("R8 PASS")
        for f in r8_findings:
            lines.append(f"{f.check} {f.severity} {f.message}")

    fail_count = sum(1 for f in findings if f.severity == "FAIL")
    warn_count = sum(1 for f in findings if f.severity == "WARN")
    verdict = "PASS" if fail_count == 0 else "FAIL"
    lines.append(f"Result: {fail_count} FAIL, {warn_count} WARN — {verdict}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check epic readiness before implementation or review.")
    parser.add_argument("epic_dir", help="Epic directory name under .devtool/epic/")
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Run baseline GREEN and TIER-B verification rows",
    )
    parser.add_argument(
        "--row-timeout",
        type=int,
        default=600,
        help="Timeout in seconds for each baseline row",
    )

    args = parser.parse_args(argv)

    try:
        root_str = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        root = Path(root_str).resolve()
    except (subprocess.CalledProcessError, OSError):
        sys.stderr.write("error: not in a git repository\n")
        return 2

    epic_path = root / ".devtool" / "epic" / args.epic_dir
    if not epic_path.is_dir():
        sys.stderr.write(f"error: {epic_path} does not exist\n")
        return 2

    hld_path = epic_path / f"{args.epic_dir}.en.md"
    if not hld_path.is_file():
        sys.stderr.write(f"error: {hld_path} does not exist\n")
        return 2

    ctx = load_context(root, args.epic_dir, baseline=args.baseline, row_timeout=args.row_timeout)
    findings = run_checks(ctx, baseline=args.baseline, row_timeout=args.row_timeout)
    report = render_report(ctx, findings)
    print(report)

    return 1 if any(f.severity == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
