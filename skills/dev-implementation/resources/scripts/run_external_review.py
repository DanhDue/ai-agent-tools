#!/usr/bin/env python3
"""Review of a finished epic through the Claude CLI, the Codex CLI, the Antigravity CLI (agy), the Kiro CLI (kiro-cli/kiro), or a model served by a local Ollama.

Usage:
  run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli claude|codex|agy|kiro [--model <name>] [--timeout 1800] [--facts-timeout 300] [--diff-limit 1500]
  run_external_review.py run --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <name> [--host <url>] [--num-ctx <tokens>] [--timeout 1800]
  run_external_review.py check --epic-dir <epic_dir>
  run_external_review.py triage --epic-dir <epic_dir>

`run` exit codes: 0 a completed round without a Critical or Important finding; 1 a completed round with
one; 2 every other outcome, including CHANGES REQUIRED with no finding line (the round is recorded whenever
the reviewer ran). `check` exit codes: 0 nothing undecided; 1 a Critical or Important finding of the latest
completed round has no decision, or a findings row cannot be read. `triage` prints the latest round as a
skeleton to fill before acting on it, with a comparison of every round; exit 0, or 2 with no round.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc  # type: ignore[attr-defined]
from pathlib import Path
from string import Template
from typing import Any

import local_review
from check_bdd_traceability import load_scenarios
from task_contract import ContractError, git_run, parse_integration_results, parse_integration_result_specs

SCRIPTS = Path(__file__).resolve().parent
PROMPT = SCRIPTS.parent.parent / "references" / "external-review-prompt.md"
RULES = SCRIPTS.parent.parent / "references" / "review-rules.md"
KINDS = ("code", "principal", "epic")
REVIEW_CONFIG_FILE = ".devtool/review_config.json"
THINKING_LEVELS = ("none", "light", "low", "medium", "high", "extra-high")
PROVIDER_PRIORITY: tuple[str, ...] = ("claude", "codex", "kiro", "agy")
MAX_REVIEW_ROUNDS = 3
QUOTA_THRESHOLDS: dict[str, float] = {
    "5h_min_fraction": 0.15,
    "7d_min_fraction": 0.02,
    "kiro_min_fraction": 0.03,
    "kiro_min_credits": 15.0,
    "agy_argon_min_fraction": 0.10,
}
DEFAULT_REVIEW_CONFIG: dict[str, Any] = {
    "last_used_provider": "claude",
    "provider_priority": list(PROVIDER_PRIORITY),
    "max_rounds": MAX_REVIEW_ROUNDS,
    "quota_thresholds": dict(QUOTA_THRESHOLDS),
    "providers": {
        "claude": {
            "model": "Opus 5.5",
            "thinking_level": "high",
        },
        "codex": {
            "model": "gpt-6.1-sol",
            "thinking_level": "high",
        },
        "kiro": {
            "model": "claude-opus-5.5",
            "thinking_level": "high",
        },
        "agy": {
            "model": "Gemini 4 Argon (Medium)",
            "thinking_level": "medium",
        },
        "ollama": {
            "model": "qwen38-fast:latest",
            "thinking_level": "high",
            "host": "http://localhost:11434",
        },
    },
}


def _is_git_tracked(root: Path, rel_path: str) -> bool:
    try:
        res = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel_path],
            cwd=root,
            capture_output=True,
            check=False,
        )
        return res.returncode == 0
    except OSError:
        return False


def load_review_config(root: Path) -> dict[str, Any]:
    path = root / REVIEW_CONFIG_FILE
    if not path.is_file():
        return copy.deepcopy(DEFAULT_REVIEW_CONFIG)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return copy.deepcopy(DEFAULT_REVIEW_CONFIG)
        cfg: dict[str, Any] = copy.deepcopy(DEFAULT_REVIEW_CONFIG)
        if "last_used_provider" in data and isinstance(data["last_used_provider"], str):
            cfg["last_used_provider"] = data["last_used_provider"]
        if "provider_priority" in data and isinstance(data["provider_priority"], list):
            cfg["provider_priority"] = [str(x) for x in data["provider_priority"] if isinstance(x, str)]
        existing_providers = data.get("providers")
        missing_default_provider = not isinstance(existing_providers, dict) or any(
            p not in existing_providers for p in DEFAULT_REVIEW_CONFIG["providers"]
        )
        if isinstance(existing_providers, dict):
            for p, pdata in existing_providers.items():
                if isinstance(pdata, dict):
                    cfg["providers"].setdefault(p, {})
                    cfg["providers"][p].update(pdata)
        if missing_default_provider and not _is_git_tracked(root, REVIEW_CONFIG_FILE):
            save_review_config(root, cfg)
        return cfg
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return copy.deepcopy(DEFAULT_REVIEW_CONFIG)


def save_review_config(root: Path, config: dict[str, Any]) -> None:
    path = root / REVIEW_CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp")
    tmp_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def update_sticky_review_config(root: Path, cli: str, model: str | None, thinking_level: str | None) -> None:
    try:
        cfg = load_review_config(root)
        cfg["last_used_provider"] = cli
        if cli not in cfg.get("providers", {}):
            cfg.setdefault("providers", {})[cli] = {}
        if model:
            cfg["providers"][cli]["model"] = model
        if thinking_level:
            cfg["providers"][cli]["thinking_level"] = thinking_level
        save_review_config(root, cfg)
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        pass


def evaluate_provider_quota(cli: str, quota_data: dict[str, Any]) -> tuple[bool, str]:
    """Evaluate check-quota payload against 5H/7D/Monthly thresholds for Claude -> Codex -> Kiro -> Argon."""
    status = str(quota_data.get("status", ""))
    if cli in ("claude", "codex"):
        frac_5h = float((quota_data.get("gemini5h") or {}).get("fraction", 0.0))
        frac_7d = float((quota_data.get("geminiWeekly") or {}).get("fraction", 0.0))
        ok = (
            status == "ACTIVE"
            and frac_5h >= QUOTA_THRESHOLDS["5h_min_fraction"]
            and frac_7d > QUOTA_THRESHOLDS["7d_min_fraction"]
        )
        return ok, f"5H={frac_5h * 100:.1f}%, 7D={frac_7d * 100:.1f}%, status={status}"
    if cli == "kiro":
        cp = quota_data.get("creditsPool") or quota_data.get("gemini5h") or {}
        frac = float(cp.get("fraction", 0.0))
        limit = float(cp.get("limit", 1000.0))
        remaining = float(cp.get("remaining", frac * limit))
        ok = (
            status.startswith("ACTIVE")
            and frac >= QUOTA_THRESHOLDS["kiro_min_fraction"]
            and remaining >= QUOTA_THRESHOLDS["kiro_min_credits"]
        )
        return ok, f"monthly={frac * 100:.1f}% ({remaining:.1f} credits), status={status}"
    if cli == "agy":
        argon = quota_data.get("argonWeekly") or {}
        g5h = quota_data.get("gemini5h") or {}
        frac_argon = float(argon.get("fraction", 0.0))
        frac_5h = float(g5h.get("fraction", 0.0))
        ok = (status == "ACTIVE" or bool(quota_data.get("success"))) and (
            frac_argon >= QUOTA_THRESHOLDS["agy_argon_min_fraction"]
            or frac_5h >= QUOTA_THRESHOLDS["5h_min_fraction"]
        )
        return ok, f"5H={frac_5h * 100:.1f}%, Argon={frac_argon * 100:.1f}%, status={status}"
    return False, f"unsupported provider {cli}"


def _default_quota_fetcher(cli: str) -> dict[str, Any]:
    quota_script = SCRIPTS.parents[3] / "scripts" / "agy_quota.py"
    if not quota_script.is_file():
        return {}
    import importlib.util

    spec = importlib.util.spec_from_file_location("agy_quota", quota_script)
    if spec is None or spec.loader is None:
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if cli == "claude":
        return dict(mod.fetch_claude_quota())
    if cli == "codex":
        return dict(mod.fetch_codex_quota())
    if cli == "kiro":
        return dict(mod.fetch_kiro_quota())
    if cli == "agy":
        profile = os.environ.get("AGY_PROFILE") or os.path.basename(os.environ.get("HOME", "danhdue"))
        raw = mod.fetch_quota_for_profile(profile)
        return dict(mod.format_profile_for_dashboard(profile, raw) if raw.get("success") else raw)
    return {}


def select_provider_by_quota(
    quota_fetcher: Any = None,
    binary_resolver: Any = None,
    priority: list[str] | None = None,
) -> tuple[str | None, list[str]]:
    """Select the highest-priority eligible provider via check-quota."""
    fetcher = quota_fetcher or _default_quota_fetcher
    resolver = binary_resolver or resolve_cli_binary
    diagnostics: list[str] = []
    order = priority if priority is not None else PROVIDER_PRIORITY
    for candidate in order:
        if not resolver(candidate):
            diagnostics.append(f"{candidate}: binary not found on PATH")
            continue
        try:
            data = fetcher(candidate)
        except Exception as exc:
            diagnostics.append(f"{candidate}: quota check error ({exc})")
            continue
        ok, detail = evaluate_provider_quota(candidate, data)
        diagnostics.append(f"{candidate}: {'ELIGIBLE' if ok else 'SKIPPED'} ({detail})")
        if ok:
            return candidate, diagnostics
    return None, diagnostics


def resolve_review_settings(
    root: Path,
    epic_dir: str | None,
    kind: str,
    cli_arg: str | None,
    model_arg: str | None,
    thinking_arg: str | None,
    auto_quota: bool = False,
) -> tuple[str, str | None, str]:
    config = load_review_config(root)
    prev_cli = None
    prev_model = None
    prev_thinking = None
    if epic_dir:
        name, _ = review_file(kind)
        path = root / ".devtool" / "epic" / epic_dir / name
        if path.exists():
            rounds = rounds_in(path.read_text(encoding="utf-8"))
            if rounds:
                last_meta = round_meta(rounds[-1][1])
                prev_cli = last_meta.get("CLI")
                prev_model = last_meta.get("Model")
                prev_thinking = last_meta.get("Thinking")

    if cli_arg is None and auto_quota:
        selected, diag = select_provider_by_quota(priority=config.get("provider_priority"))
        if selected:
            print(f"{CYAN}⚡ [check-quota]{RESET} Selected provider: {selected} ({'; '.join(diag)})", file=sys.stderr)
            cli = selected
        else:
            cli = prev_cli or config.get("last_used_provider") or "claude"
    else:
        cli = cli_arg or prev_cli or config.get("last_used_provider") or "claude"

    if prev_cli != cli:
        prev_model = None
        prev_thinking = None

    provider_cfg = config.get("providers", {}).get(cli, {})
    default_model = DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("model", "default")
    if cli == "ollama" and not model_arg and not prev_model:
        model = None
    else:
        model = model_arg or prev_model or provider_cfg.get("model") or default_model

    default_thinking = DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("thinking_level", "high")
    thinking_level = thinking_arg or prev_thinking or provider_cfg.get("thinking_level") or default_thinking
    if thinking_level not in THINKING_LEVELS:
        thinking_level = default_thinking if default_thinking in THINKING_LEVELS else "high"

    return cli, model, thinking_level


def principal_prompt_path() -> Path:
    standalone = SCRIPTS.parent.parent.parent / "principal-review" / "references" / "principal-review-prompt.md"
    if standalone.is_file():
        return standalone
    return SCRIPTS.parent.parent / "references" / "principal-review-prompt.md"


def principal_rules_path() -> Path:
    standalone = SCRIPTS.parent.parent.parent / "principal-review" / "references" / "principal-review-rules.md"
    if standalone.is_file():
        return standalone
    return SCRIPTS.parent.parent / "references" / "principal-review-rules.md"



def review_file(kind: str) -> tuple[str, str]:
    if kind == "principal":
        return ("principal_review.md", "Principal Review")
    return ("review_results.md", "Cross-Model Review")


def principal_artefact_lines(root: Path, epic_dir: str) -> str:
    epic_path = root / ".devtool" / "epic" / epic_dir
    lines: list[str] = []

    # 1. *-design.en.md and *-design.vi.md
    for f in sorted(epic_path.glob("*-design.en.md")):
        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")
    for f in sorted(epic_path.glob("*-design.vi.md")):
        lines.append(f"- `.devtool/epic/{epic_dir}/{f.name}`")

    # 2. <epic_dir>.en.md and <epic_dir>.vi.md
    for ext in (".en.md", ".vi.md"):
        doc = epic_path / f"{epic_dir}{ext}"
        if doc.is_file():
            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
            if line not in lines:
                lines.append(line)

    # 3. bdd_scenarios.en.md and bdd_scenarios.vi.md
    for ext in (".en.md", ".vi.md"):
        doc = epic_path / f"bdd_scenarios{ext}"
        if doc.is_file():
            line = f"- `.devtool/epic/{epic_dir}/{doc.name}`"
            if line not in lines:
                lines.append(line)

    # 4. every task_*.md, sorted
    for t in sorted(epic_path.glob("task_*.md")):
        lines.append(f"- `.devtool/epic/{epic_dir}/{t.name}`")

    # 5. handoff.md when present
    handoff = epic_path / "handoff.md"
    if handoff.is_file():
        lines.append(f"- `.devtool/epic/{epic_dir}/handoff.md`")

    return "\n".join(lines)

# Tolerates optional markdown headings, bullet prefixes, and bold markers around Verdict.
VERDICT = re.compile(
    r"^\s*(?:#+\s*|[-*+]\s*)?\*{0,2}Verdict(?:(?:\*{0,2}:)|(?::\*{0,2}))\s*\*{0,2}(PASS|CHANGES REQUIRED)\*{0,2}\s*$",
    re.IGNORECASE,
)
# Tolerates list numbering, bullets and ** around the severity, and —, –, - or : between location and problem.
FINDING = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important|Minor)\*{0,2}\]\*{0,2}\s*"
    r"(\S.*?)(?:\s+[—–-]|\s*:)\s+(\S.*)$",
    re.IGNORECASE,
)
# Only catch unparsed blocking tags when they appear on a list-like or tag-leading line to avoid prose false positives.
UNPARSED_BLOCKING = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])?\s*\*{0,2}\[\*{0,2}(Critical|Important)\*{0,2}\]",
    re.IGNORECASE,
)
FINDING_ROW = re.compile(r"^\|\s*\d+\s*\|")
META_LINE = re.compile(r"^- \*\*(.+?)\*\*: (.*)$")
PASS_HEADER = re.compile(r"^### Pass (\d+): (.+)$")
NEXT_STEPS = ("To be written after verifying every finding: Fix commits, decisions, a confirmation round, "
              "then Gate 4 in full.")
BLOCKING = ("Critical", "Important")
FENCE = re.compile(r"^(`{3,})")

MAX_DIFF_LINES = 1500
MAX_DIFF_BYTES = 60_000

RED = "\033[1;31m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
CYAN = "\033[1;36m"
RESET = "\033[0m"

EXCLUDES = (
    # 1. Common Locks, Build & Devtool
    ":(exclude)*.lock",
    ":(exclude)*-lock.*",
    ":(exclude)*.lockfile",
    ":(exclude)**/Package.resolved",
    ":(exclude)build/**",
    ":(exclude).devtool/**",
    # 2. Flutter / Dart Codegen & FFI Bridge
    ":(exclude)*.g.dart",
    ":(exclude)*.freezed.dart",
    ":(exclude)*.gr.dart",
    ":(exclude)*.config.dart",
    ":(exclude)*.mocks.dart",
    ":(exclude)*.chopper.dart",
    ":(exclude)*.pigeon.*",
    ":(exclude)*frb_generated*",
    ":(exclude)**/l10n/app_localizations*.dart",
    # 3. iOS Native (Xcode metadata, assets & UI layout XML)
    ":(exclude)*.pbxproj",
    ":(exclude)*.xcworkspacedata",
    ":(exclude)*.xcscheme",
    ":(exclude)*.storyboard",
    ":(exclude)*.xib",
    ":(exclude)**/*.xcassets/**",
    ":(exclude)*.xcstrings",
    # 4. Android Native (Gradle wrapper & Baseline profiles)
    ":(exclude)gradlew",
    ":(exclude)gradlew.bat",
    ":(exclude)**/gradle/wrapper/**",
    ":(exclude)**/baseline-prof.txt",
    # 5. Rust & Python Generated / Snapshots
    ":(exclude)*.generated.*",
    ":(exclude)*_pb2.py",
    ":(exclude)*_pb2_grpc.py",
    ":(exclude)*_pb2.pyi",
    ":(exclude)**/.sqlx/**",
    ":(exclude)**/__snapshots__/**",
    ":(exclude)*.snap",
    ":(exclude)*.ambr",
    # 6. Minified Web Assets & Source Maps
    ":(exclude)*.min.js",
    ":(exclude)*.min.css",
    ":(exclude)*.map",
)


class PreconditionFailedError(Exception):
    """Raised when fact collection fails, preventing AI CLI invocation."""

    def __init__(self, gate: str, reason: str, details: str = "") -> None:
        super().__init__(f"{gate}: {reason}")
        self.gate = gate
        self.reason = reason
        self.details = details.strip()


def print_gate_banner(error: PreconditionFailedError, cli: str) -> None:
    """Print an unmistakable highlighted banner when a pre-check blocks AI invocation."""
    bar = "=" * 74
    lines = [
        f"\n{RED}{bar}{RESET}",
        f"{RED}🚨 [PRECONDITION BLOCKED] — {cli.upper()} CLI WAS NOT INVOKED (0 CREDITS USED){RESET}",
        f"{RED}{bar}{RESET}",
        f"{YELLOW}Failed Gate :{RESET} {error.gate}",
        f"{YELLOW}Reason      :{RESET} {error.reason}",
    ]
    if error.details:
        indented = "\n".join(f"  {line}" for line in error.details.splitlines()[-25:])
        lines.append(f"{YELLOW}Details (last 25 lines):{RESET}\n{indented}")
    lines.append(f"{RED}{bar}{RESET}\n")
    print("\n".join(lines), file=sys.stderr, flush=True)


def status_lines(root: Path) -> list[str]:
    return git_run(root, "status", "--porcelain").decode("utf-8", "replace").splitlines()


def head_of(root: Path) -> str:
    return git_run(root, "rev-parse", "HEAD").decode().strip()


def execute(command: list[str] | str, root: Path, timeout: int, prompt: str | None = None,
            shell: bool = False) -> tuple[int | None, str, str]:
    """Run to completion in its own process group, so a timeout also ends the CLI's children."""
    env = None
    if isinstance(command, list) and command and Path(command[0]).name in ("kiro-cli", "kiro"):
        home = os.environ.get("HOME", "")
        if "/antigravity_homes/" in home:
            real_home = Path(home).parents[1]
            if (real_home / "Library" / "Application Support" / "kiro-cli").exists() or (real_home / ".kiro").exists():
                env = dict(os.environ, HOME=str(real_home))
    process = subprocess.Popen(command, cwd=root, shell=shell, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True, env=env)
    try:
        out, err = process.communicate((prompt or "").encode(), timeout=timeout)
        code: int | None = process.returncode
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        out, err = process.communicate()
        code = None
    return code, out.decode("utf-8", "replace"), err.decode("utf-8", "replace")


def run_gate(label: str, command: list[str] | str, root: Path, timeout: int,
             shell: bool = False) -> tuple[int, str, str]:
    """Execute a pre-check gate with real-time terminal feedback."""
    print(f"{CYAN}⏳ [Pre-check]{RESET} {label} ... ", end="", file=sys.stderr, flush=True)
    code, out, err = execute(command, root, timeout, shell=shell)
    combined = (out + err).rstrip()
    if code is None:
        print(f"{RED}❌ TIMEOUT ({timeout}s){RESET}", file=sys.stderr, flush=True)
        raise PreconditionFailedError(label, f"timed out after {timeout} seconds", combined)
    if code != 0:
        print(f"{RED}❌ FAILED (exit {code}){RESET}", file=sys.stderr, flush=True)
        raise PreconditionFailedError(label, f"failed with exit code {code}", combined)
    print(f"{GREEN}✅ PASS{RESET}", file=sys.stderr, flush=True)
    return code, out, err


def fact(label: str, code: int | None, out: str, err: str) -> str:
    return f"$ {label}\nexit {code if code is not None else 'timeout'}\n{(out + err).rstrip()}\n"


def collect_facts(root: Path, epic_dir: str, base: str, hld_text: str, timeout: int) -> tuple[str, str]:
    audit = [sys.executable, str(SCRIPTS / "audit_epic.py"), "--epic-dir", epic_dir, "--base", base]
    audit_code, audit_out, audit_err = run_gate("audit_epic.py", audit, root, timeout)
    audit_output = fact("audit_epic.py", audit_code, audit_out, audit_err)
    results, reports = [], []
    skipped_live_commands: list[str] = []

    specs = parse_integration_result_specs(hld_text)
    for spec in specs:
        if spec.live:
            missing = [v for v in spec.needs if not os.environ.get(v)]
            if missing:
                results.append(f"$ {spec.command}\nSKIPPED (missing env: {', '.join(missing)})\n")
                skipped_live_commands.append(spec.command)
                continue
        cmd_code, cmd_out, cmd_err = run_gate(f"Integration: {spec.command}", spec.command, root, timeout, shell=True)
        results.append(fact(spec.command, cmd_code, cmd_out, cmd_err))
        if spec.report:
            reports.extend(spec.report.split())

    roots = re.search(r"^Integration test roots:\s*(.+)$", hld_text, re.MULTILINE)
    if roots:
        roots_list = [r.strip("`") for r in roots.group(1).strip().split()]
        scenarios_file = root / ".devtool" / "epic" / epic_dir / "bdd_scenarios.en.md"

        if skipped_live_commands:
            # 1. Static check across 100% of scenarios without --results
            check_static = [
                sys.executable,
                str(SCRIPTS / "check_bdd_traceability.py"),
                "tests",
                "--scenarios",
                str(scenarios_file),
                "--roots",
                *roots_list,
            ]
            chk_code, chk_out, chk_err = run_gate("check_bdd_traceability.py tests (static)", check_static, root, timeout)
            results.append(fact(shlex.join(check_static[1:]), chk_code, chk_out, chk_err))

            # 2. Results check across executed reports
            results_paths = [r.strip("`") for r in reports]
            if results_paths:
                all_ids: list[str] = []
                if scenarios_file.is_file():
                    try:
                        all_ids, _ = load_scenarios(scenarios_file)
                    except Exception:
                        all_ids = []

                skipped_test_files: set[str] = set()
                for cmd in skipped_live_commands:
                    for token in shlex.split(cmd):
                        if any(token.endswith(ext) for ext in (".py", ".js", ".ts", ".mjs", ".dart", ".kt", ".swift")):
                            skipped_test_files.add(Path(token).name)
                            skipped_test_files.add(token)

                files_in_roots: list[Path] = []
                for r in roots_list:
                    r_path = root / r
                    if r_path.is_dir():
                        for p in r_path.rglob("*"):
                            if p.is_file() and any(p.name.endswith(ext) for ext in (".py", ".js", ".ts", ".mjs", ".dart", ".kt", ".swift")):
                                files_in_roots.append(p)

                non_skipped_ids: list[str] = []
                for identifier in all_ids:
                    pattern = re.compile(r"\b" + re.escape(identifier) + r"\b")
                    mentioning_files: list[Path] = []
                    for f in files_in_roots:
                        try:
                            content = f.read_text(encoding="utf-8", errors="ignore")
                            if pattern.search(content):
                                mentioning_files.append(f)
                        except OSError:
                            pass

                    if mentioning_files and all(
                        f.name in skipped_test_files or str(f.relative_to(root)) in skipped_test_files
                        for f in mentioning_files
                    ):
                        continue
                    non_skipped_ids.append(identifier)

                if non_skipped_ids:
                    check_results = [
                        sys.executable,
                        str(SCRIPTS / "check_bdd_traceability.py"),
                        "tests",
                        "--scenarios",
                        str(scenarios_file),
                        "--roots",
                        *roots_list,
                        "--ids",
                        *non_skipped_ids,
                        "--results",
                        *results_paths,
                    ]
                    res_code, res_out, res_err = run_gate("check_bdd_traceability.py tests (results)", check_results, root, timeout)
                    results.append(fact(shlex.join(check_results[1:]), res_code, res_out, res_err))
        elif reports:
            results_paths = [r.strip("`") for r in reports]
            check = [
                sys.executable,
                str(SCRIPTS / "check_bdd_traceability.py"),
                "tests",
                "--scenarios",
                str(scenarios_file),
                "--roots",
                *roots_list,
                "--results",
                *results_paths,
            ]
            chk_code, chk_out, chk_err = run_gate("check_bdd_traceability.py", check, root, timeout)
            results.append(fact(shlex.join(check[1:]), chk_code, chk_out, chk_err))

    py_quality_path = root / ".agents" / "quality" / "python-quality.json"
    if py_quality_path.is_file():
        try:
            q_cfg = json.loads(py_quality_path.read_text(encoding="utf-8"))
            caps = q_cfg.get("capabilities", {}) if isinstance(q_cfg, dict) else {}
            for cap_name in ("anti_stub", "importlinter_coverage", "self_probe"):
                cap = caps.get(cap_name)
                if isinstance(cap, dict) and isinstance(cap.get("command"), str) and cap["command"].strip():
                    c_cmd = cap["command"].strip()
                    c_code, c_out, c_err = run_gate(f"Quality pre-check ({cap_name})", c_cmd, root, timeout, shell=True)
                    audit_output += "\n" + fact(c_cmd, c_code, c_out, c_err)
        except (json.JSONDecodeError, OSError):
            pass

    return audit_output, "\n".join(results) or "No Integration results declared.\n"


def artefact_lines(root: Path, epic_dir: str) -> str:
    folder = root / ".devtool" / "epic" / epic_dir
    names = sorted(p.name for p in folder.glob("*.md"))
    spec = [n for n in names if not n.startswith(("task_", "bdd_", epic_dir, "review_results"))]
    paths = (spec + [f"{epic_dir}.en.md", "bdd_scenarios.en.md"]
             + [n for n in names if n.startswith("task_")] + ["evidence/"])
    return "\n".join(f"- `.devtool/epic/{epic_dir}/{p}`" for p in paths)


def build_diff_section(root: Path, base: str, sha: str, max_lines: int = MAX_DIFF_LINES, max_bytes: int = MAX_DIFF_BYTES) -> str:
    """Hybrid inlining: always show full --stat; inline filtered diff if within size budget."""
    full_stat = git_run(
        root, "diff", "--stat", f"{base}...{sha}", "--", ".", ":(exclude).devtool/**"
    ).decode("utf-8", "replace").strip()
    filtered_diff = git_run(
        root, "diff", f"{base}...{sha}", "--", ".", *EXCLUDES
    ).decode("utf-8", "replace").strip()

    stat_fence = fence_for(full_stat)
    stat_block = f"Full file change summary (`git diff --stat`, including locks/codegen):\n\n{stat_fence}text\n{full_stat or '(no changes outside .devtool/)'}\n{stat_fence}\n\n"

    if not filtered_diff:
        return stat_block + "No non-excluded source code changes to inline."

    line_count = len(filtered_diff.splitlines())
    byte_size = len(filtered_diff.encode("utf-8"))

    if line_count <= max_lines and byte_size <= max_bytes:
        diff_fence = fence_for(filtered_diff)
        return (
            stat_block
            + f"The complete source diff ({line_count} lines, {byte_size // 1024} KB, lock, generated, and noisy metadata/asset files excluded) "
            f"is inlined below. Do NOT run `git diff` again unless you need to inspect an excluded file:\n\n"
            f"{diff_fence}diff\n{filtered_diff}\n{diff_fence}"
        )

    return (
        stat_block
        + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
        f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {base}...{sha} -- <path>` as needed."
    )


def diff_range(root: Path, base: str, commits: str | None = None) -> tuple[str, str]:
    """Extract commit log and diff section for an arbitrary base and commit range."""
    commit_spec = commits if commits else f"{base}...HEAD"
    log = git_run(root, "log", "--oneline", commit_spec).decode("utf-8", "replace").strip()
    full_stat = git_run(
        root, "diff", "--stat", commit_spec, "--", "."
    ).decode("utf-8", "replace").strip()
    filtered_diff = git_run(
        root, "diff", commit_spec, "--", ".", *EXCLUDES
    ).decode("utf-8", "replace").strip()

    stat_fence = fence_for(full_stat)
    stat_block = f"Full file change summary (`git diff --stat`, including locks/codegen):\n\n{stat_fence}text\n{full_stat or '(no changes)'}\n{stat_fence}\n\n"

    if not filtered_diff:
        diff_section = stat_block + "No non-excluded source code changes to inline."
    else:
        line_count = len(filtered_diff.splitlines())
        byte_size = len(filtered_diff.encode("utf-8"))
        if line_count <= MAX_DIFF_LINES and byte_size <= MAX_DIFF_BYTES:
            diff_fence = fence_for(filtered_diff)
            diff_section = (
                stat_block
                + f"The complete source diff ({line_count} lines, {byte_size // 1024} KB, lock, generated, and noisy metadata/asset files excluded) "
                f"is inlined below. Do NOT run `git diff` again unless you need to inspect an excluded file:\n\n"
                f"{diff_fence}diff\n{filtered_diff}\n{diff_fence}"
            )
        else:
            diff_section = (
                stat_block
                + f"The source diff is large ({line_count} lines, {byte_size // 1024} KB > inline budget). "
                f"Do NOT run an unfiltered `git diff`; inspect specific target files via `git diff {commit_spec} -- <path>` as needed."
            )
    return log, diff_section


def effective_model(cli: str, model: str | None) -> str:
    if model:
        return model
    return str(DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("model", "default"))


def effective_thinking_level(cli: str, thinking_level: str | None) -> str:
    if thinking_level and thinking_level in THINKING_LEVELS:
        return thinking_level
    return str(DEFAULT_REVIEW_CONFIG["providers"].get(cli, {}).get("thinking_level", "high"))


def resolve_cli_binary(cli: str) -> str | None:
    if cli == "kiro":
        return shutil.which("kiro-cli") or shutil.which("kiro")
    return shutil.which(cli)


def cli_command(cli: str, model: str | None, thinking_level: str | None = None) -> list[str]:
    extra = ["--model", model] if model else []
    if cli == "claude":
        claude_model = model
        if claude_model:
            low = claude_model.lower()
            if "opus" in low:
                claude_model = "opus"
            elif "sonnet" in low:
                claude_model = "sonnet"
            elif "haiku" in low:
                claude_model = "haiku"
        extra = ["--model", claude_model] if claude_model else []
        cmd = ["claude", "-p", "--dangerously-skip-permissions"]
        if thinking_level and thinking_level != "none":
            effort_map = {
                "light": "low",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "extra-high": "xhigh",
            }
            effort = effort_map.get(thinking_level.lower(), "high")
            cmd.extend(["--effort", effort])
        cmd.extend(extra)
        return cmd
    if cli == "kiro":
        binary = "kiro-cli" if shutil.which("kiro-cli") or not shutil.which("kiro") else "kiro"
        cmd = [binary, "chat", "--no-interactive", "--trust-all-tools", "--wrap", "never"]
        if thinking_level and thinking_level != "none":
            effort_map = {
                "light": "low",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "extra-high": "xhigh",
            }
            effort = effort_map.get(thinking_level.lower(), "high")
            cmd.extend(["--effort", effort])
        cmd.extend(extra)
        return cmd
    if cli == "agy":
        model_name = effective_model(cli, model)
        return ["agy", "--sandbox", "--mode", "plan", "--model", model_name]
    # codex
    cmd = ["codex", "exec", "--sandbox", "read-only"]
    if thinking_level:
        effort_map = {
            "light": "low",
            "low": "low",
            "medium": "medium",
            "high": "high",
            "extra-high": "extra-high",
            "none": "none",
        }
        effort = effort_map.get(thinking_level.lower(), thinking_level)
        cmd.extend(["-c", f"model_reasoning_effort={effort}"])
    cmd.extend([*extra, "-"])
    return cmd


def format_findings_summary(findings: list[tuple[str, str, str]] | list[list[str]]) -> str:
    crits = sum(1 for f in findings if (f[0] if len(f) == 3 else f[1]) == "Critical")
    importants = sum(1 for f in findings if (f[0] if len(f) == 3 else f[1]) == "Important")
    minors = sum(1 for f in findings if (f[0] if len(f) == 3 else f[1]) == "Minor")
    parts = []
    if crits > 0:
        parts.append(f"{crits} Critical")
    if importants > 0:
        parts.append(f"{importants} Important")
    if not parts and minors > 0:
        parts.append(f"{minors} Minor")
    if not parts:
        return "0 findings"
    total = crits + importants + minors
    return ", ".join(parts) + (" finding" if total == 1 else " findings")


def format_triage_header(
    title: str,
    sha: str,
    cli: str,
    model: str,
    thinking_level: str,
    verdict: str,
    findings: list[tuple[str, str, str]] | list[list[str]],
) -> list[str]:
    cli_display = {"claude": "Claude", "codex": "Codex", "agy": "agy", "kiro": "Kiro", "ollama": "Ollama"}.get(cli, cli.capitalize())
    thinking_display = thinking_level.replace("-", " ").title() if thinking_level else "High"
    summary = format_findings_summary(findings)
    verdict_display = verdict.upper() if verdict else "NONE"
    return [
        title,
        "",
        f"• Candidate SHA: {sha}",
        f"• Reviewer: {cli_display} ( {model} )",
        f"• Thinking Level: {thinking_display}",
        f"• Verdict: {verdict_display} ({summary})",
    ]


def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\r", "").replace("\n", " ").strip()


def fence_for(text: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    return "`" * max(3, longest + 1)


def rounds_in(text: str) -> list[tuple[int, list[str]]]:
    """Split review_results.md into (number, lines) rounds, ignoring headings inside fenced raw output."""
    rounds: list[tuple[int, list[str]]] = []
    fence = ""
    for line in text.splitlines():
        match = FENCE.match(line)
        if fence:
            fence = "" if line.rstrip() == fence else fence
        elif match:
            fence = match.group(1)
        elif (heading := re.fullmatch(r"## Round (\d+)", line)):
            rounds.append((int(heading.group(1)), []))
            continue
        if rounds:
            rounds[-1][1].append(line)
    return rounds


def split_row(line: str) -> list[str]:
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def metadata(lines: list[str]) -> list[str]:
    """A round's own lines: its fields and findings table, never its raw output."""
    return lines[:lines.index("Raw output:")] if "Raw output:" in lines else lines


def table_findings(lines: list[str]) -> list[tuple[str, list[str]]]:
    """(line, cells) for every findings row, `| <number> |` onwards, well formed or not."""
    return [(line, split_row(line)) for line in metadata(lines) if FINDING_ROW.match(line)]


def parse_findings(out: str, verdict: str | None = None) -> list[tuple[str, str, str]]:
    """Each finding line as (severity, location, problem); a blocking line in list format keeps its raw text."""
    findings = []
    for line in out.splitlines():
        if (match := FINDING.match(line)):
            sev, loc, problem = match.groups()
            findings.append((sev.capitalize(), loc, problem))
        elif (blocking := UNPARSED_BLOCKING.search(line)):
            if verdict == "PASS" and not findings:
                continue
            findings.append((blocking.group(1).capitalize(), "unparsed", line.strip()))
    return findings


def render_round(number: int, meta: dict[str, str], findings: list[tuple[str, str, str]], output: str) -> str:
    head = "".join(f"- **{key}**: {value}\n" for key, value in meta.items())
    table = "| # | Severity | Location | Problem | Decision |\n|---|----------|----------|---------|----------|\n"
    table += "".join(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} |  |\n"
                     for i, (sev, loc, problem) in enumerate(findings, 1))
    fence = fence_for(output)
    return f"## Round {number}\n\n{head}\n{table}\nRaw output:\n\n{fence}text\n{output.rstrip()}\n{fence}\n"


def run_principal_doc(root: Path, args: argparse.Namespace, sha: str) -> int:
    doc_path = root / args.doc if not Path(args.doc).is_absolute() else Path(args.doc)
    if not doc_path.is_file():
        print(f"error: document path not found: {args.doc}", file=sys.stderr)
        return 2

    content = doc_path.read_text(encoding="utf-8")
    if not content.strip() or not re.search(r"^#+\s+\S+", content, re.MULTILINE):
        print(f"error: document has invalid structure or missing headings: {args.doc}", file=sys.stderr)
        return 2

    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
    artefacts = f"- `{args.doc}`\n\nDocument content:\n\n```markdown\n{content}\n```"
    readiness_output = "N/A (Ad-hoc review of standalone document)"

    prompt = Template(principal_prompt_path().read_text(encoding="utf-8")).safe_substitute(
        rules=principal_rules_path().read_text(encoding="utf-8").strip(),
        sha=sha,
        base=args.base,
        base_sha=base_sha,
        epic_dir=args.doc,
        artefacts=artefacts,
        readiness_output=readiness_output,
    )

    before = status_lines(root)
    code, out, _err = execute(cli_command(args.cli, args.model, getattr(args, "thinking_level", None)), root, args.timeout, prompt)
    changed = tree_changes(root, before, sha)
    if changed:
        print(f"error: tree modified during review: {', '.join(changed)}", file=sys.stderr)
        return 2

    lines = out.splitlines()
    marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
    verdict = marks[-1][1] if marks else None
    findings = parse_findings(out, verdict)

    cli_display = {"claude": "Claude", "codex": "Codex", "agy": "agy", "kiro": "Kiro", "ollama": "Ollama"}.get(args.cli, args.cli.capitalize())
    triage_out = format_triage_header(
        f"Principal Review Triage: {args.doc} ({cli_display})",
        sha,
        args.cli,
        effective_model(args.cli, args.model),
        effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
        verdict or "none",
        findings,
    )
    if findings:
        triage_out += [
            "",
            "## Findings",
            "",
            "| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
            "|---|----------|----------|---------|------------|----------|-----------------|",
            *(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} | ? | ? | ? |" for i, (sev, loc, problem) in enumerate(findings, 1)),
        ]
    else:
        triage_out += ["", "## Findings", "", "None."]
    triage_out += ["", "## Next Steps", "", NEXT_STEPS]
    print("\n".join(triage_out))
    update_sticky_review_config(root, args.cli, args.model, getattr(args, "thinking_level", None))

    if code != 0 or verdict is None:
        return 2
    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0


def delta_round_context(root: Path, args: argparse.Namespace, sha: str, kind: str = "principal") -> tuple[str, dict[str, str]]:
    """Round >= 2 prompt block: the previous round's findings and decisions plus the revision diff since it.

    Round 1 (or --full) returns ("", {}) so a full-modules/full-scope audit runs first.
    Round 2 narrows scope to Delta Verification (prev_sha..sha) and prohibits new Minor findings on untouched files.
    Round 3+ enters Convergence Mode (Blocker-Only: incomplete fixes or new Critical/Important regressions in prev_sha..sha).
    """
    if getattr(args, "full", False):
        return "", {}
    name, _ = review_file(kind)
    path = root / ".devtool" / "epic" / args.epic_dir / name
    if not path.exists():
        return "", {}
    all_rounds = rounds_in(path.read_text(encoding="utf-8"))
    completed = [(n, lines) for n, lines in all_rounds if "- **Status**: completed" in metadata(lines)]
    if not completed:
        return "", {}
    number, lines = completed[-1]
    prev_sha = round_meta(lines).get("SHA", "")
    if not prev_sha or prev_sha == sha:
        return "", {}
    epic = f".devtool/epic/{args.epic_dir}"
    records = [f":(exclude){epic}/{n}" for n in ("principal_review.md", "review_results.md")]
    try:
        if kind == "principal":
            outside = re.findall(r"`([^`]+)`", principal_artefact_lines(root, args.epic_dir))
            paths = [epic, *dict.fromkeys(p for p in outside if not p.startswith(epic))]
            diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", *paths, *records).decode("utf-8", "replace").strip()
        else:
            diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", ".", *EXCLUDES, *records).decode("utf-8", "replace").strip()
            if not diff:
                diff = git_run(root, "diff", f"{prev_sha}..{sha}", "--", ".", *records).decode("utf-8", "replace").strip()
        source = git_run(root, "diff", "--stat", f"{prev_sha}..{sha}", "--", ".",
                         ":(exclude).devtool/**").decode("utf-8", "replace").strip()
    except ContractError:
        return "", {}
    if not diff or len(diff.splitlines()) > getattr(args, "diff_limit", MAX_DIFF_LINES):
        return "", {}

    next_round = len(all_rounds) + 1
    prev_meta = round_meta(lines)
    prev_cli = prev_meta.get("CLI", "claude")
    prev_model = prev_meta.get("Model", "default")
    curr_cli = getattr(args, "cli", None) or prev_cli
    curr_model = effective_model(curr_cli, getattr(args, "model", None))

    table = ["| # | Severity | Location | Problem | Decision |", "|---|---|---|---|---|"]
    table += ["| " + " | ".join(cell(c)[:400] for c in row) + " |" for row in finding_rows(lines)]

    earlier_ledger_blocks: list[str] = []
    fixed_registry_lines: list[str] = []
    for r_num, r_lines in completed:
        for row in finding_rows(r_lines):
            if len(row) >= 5 and row[4].strip().lower().startswith("fixed in"):
                fixed_registry_lines.append(
                    f"- `{row[2].strip()}` (Round {r_num} #{row[0].strip()}, `{row[1].strip()}`): "
                    f"{cell(row[3])[:180]} -> `{row[4].strip()}`"
                )
    if len(completed) > 1:
        for r_num, r_lines in completed[:-1]:
            r_meta = round_meta(r_lines)
            r_rows = finding_rows(r_lines)
            if not r_rows:
                continue
            r_table = ["| # | Severity | Location | Problem | Decision |", "|---|---|---|---|---|"]
            r_table += ["| " + " | ".join(cell(c)[:300] for c in row) + " |" for row in r_rows]
            earlier_ledger_blocks.append(
                f"#### Round {r_num} ({r_meta.get('CLI', '?')} / {r_meta.get('Model', '?')} at `{r_meta.get('SHA', '?')[:7]}`)\n\n"
                + "\n".join(r_table)
            )

    provider_note = (
        "You are taking over from a different model family. "
        if curr_cli != prev_cli
        else "You are running in a new stateless session following a prior review round. "
    )
    handoff_block = (
        "### Cross-Provider Handoff & Anti-Ping-Pong Guardrail\n\n"
        f"- **Previous Reviewer**: `{prev_cli}` (`{prev_model}`) at `{prev_sha[:7]}`\n"
        f"- **Current Reviewer**: `{curr_cli}` (`{curr_model}`) at `{sha[:7]}`\n"
        f"- **Shared Context Continuity & Anti-Ping-Pong Rule**: {provider_note}"
        "Strictly honor all `dismissed: <rationale>` decisions and `fixed in <sha>` resolutions recorded in the "
        "Shared Context Ledger below. Do NOT ask to revert or rewrite a prior round's accepted fix (zero solution ping-pong) "
        "unless it introduces an objective runtime defect or violates a frozen contract in the approved HLD / "
        "`bdd_scenarios.en.md` / `Decisions Already Made`.\n\n"
    )
    fixed_registry_block = (
        "### Previously Fixed Locations Registry (Verify-Then-Close)\n\n"
        + "\n".join(fixed_registry_lines)
        + "\n\n"
        if fixed_registry_lines
        else ""
    )

    fence, stat_fence = fence_for(diff), fence_for(source)
    if next_round >= 3:
        header_block = (
            f"## Round Scope: Convergence Mode (Round {next_round})\n\n"
            f"You are in Round 3+ Convergence Mode. ONLY report (a) incomplete fixes from previous rounds, or "
            f"(b) NEW Critical/Important regressions directly introduced by the latest fix commit "
            f"(`{prev_sha[:12]}..{sha[:12]}`). DO NOT report new Minor/stylistic findings on untouched code.\n\n"
        )
        scope_meta = {"Scope": f"convergence from round {number} ({prev_sha[:7]})"}
    else:
        header_block = (
            f"## Round Scope: Delta Review (Round {next_round})\n\n"
            f"Round {number} reviewed `{prev_sha}`. The developer triaged it and revised the code/artefacts since. "
            "Do NOT re-derive the whole design or re-audit untouched modules from scratch. "
            "DO NOT report new Minor/stylistic findings on untouched code or artefacts.\n\n"
        )
        scope_meta = {"Scope": f"delta from round {number} ({prev_sha[:7]})"}

    earlier_section = (
        "### Earlier Rounds Shared Context Ledger (Cumulative Memory)\n\n"
        + "\n\n".join(earlier_ledger_blocks)
        + "\n\n"
        if earlier_ledger_blocks
        else ""
    )

    block = (
        header_block
        + handoff_block
        + fixed_registry_block
        + "1. **Approved-Design Anchoring**: Every verification and finding MUST be anchored strictly to the approved HLD "
        "(`.devtool/epic/<epic_dir>/<epic_dir>.en.md`), `bdd_scenarios.en.md`, and `Decisions Already Made` in `task_*.md`.\n"
        "2. **Verify-Then-Close on Fixed Locations**: For each finding below marked `fixed in <sha>`, verify whether the revision "
        f"resolves the original defect at `{sha}`. If resolved, **close it silently (PASS)** — do NOT propose alternative "
        "implementations or secondary refactors on that fix.\n"
        "3. **Diff-Hunk Isolation on Fixed Files (No Late Drip-Feed)**: On any file listed in `Previously Fixed Locations Registry`, "
        "do NOT report pre-existing issues on untouched functions or lines outside the `prev_sha..sha` diff hunks. You may only "
        "report a finding on a previously fixed file if (a) `[INCOMPLETE_FIX]` the original defect remains unresolved, or "
        "(b) `[NEW_REGRESSION]` the modified lines in `prev_sha..sha` directly introduce a new Critical/Important bug.\n"
        "4. Do not re-raise a finding marked `dismissed:` unless the source contradicts its rationale.\n"
        "5. The revision diff below is the primary scope: review the new and edited text/code, and every artefact "
        "or source symbol that text/code references or must stay consistent with (P1, P2, P5, P7). Read an "
        "unchanged file only to verify such a reference.\n"
        "6. Everything else was reviewed in round "
        f"{number}. Skip it, and DO NOT report new Minor findings on untouched code.\n\n"
        + earlier_section
        + f"### Round {number} findings and decisions ({prev_cli} / {prev_model})\n\n" + "\n".join(table) + "\n\n"
        f"### Revision diff since round {number} (`{prev_sha[:12]}..{sha[:12]}`)\n\n"
        f"{fence}diff\n{diff}\n{fence}\n\n"
        f"Source files changed since round {number} (stat only):\n\n"
        f"{stat_fence}text\n{source or '(none outside .devtool/)'}\n{stat_fence}\n"
    )
    return block, scope_meta


def _completed_rounds_count(root: Path, epic_dir: str | None, kind: str) -> int:
    if not epic_dir:
        return 0
    name, _ = review_file(kind)
    path = root / ".devtool" / "epic" / epic_dir / name
    if not path.exists():
        return 0
    return sum(1 for _n, lines in rounds_in(path.read_text(encoding="utf-8")) if "- **Status**: completed" in metadata(lines))


def run_principal(root: Path, args: argparse.Namespace, sha: str) -> int:
    if getattr(args, "doc", None):
        return run_principal_doc(root, args, sha)

    facts_timeout = getattr(args, "facts_timeout", 300)
    check_cmd = [sys.executable, str(SCRIPTS / "check_epic_readiness.py"), args.epic_dir]
    try:
        _code, out, _err = run_gate("check_epic_readiness.py", check_cmd, root, facts_timeout)
    except PreconditionFailedError as error:
        print_gate_banner(error, args.cli)
        return 2

    base_sha = git_run(root, "rev-parse", "--verify", args.base).decode().strip()
    readiness_output = out.rstrip()
    round_context, scope = delta_round_context(root, args, sha, kind="principal")
    if scope:
        print(f"{scope['Scope']}: reviewing the revision, not the whole epic (--full to review everything)",
              file=sys.stderr)

    prompt = Template(principal_prompt_path().read_text(encoding="utf-8")).safe_substitute(
        rules=principal_rules_path().read_text(encoding="utf-8").strip(),
        sha=sha,
        base=args.base,
        base_sha=base_sha,
        epic_dir=f".devtool/epic/{args.epic_dir}",
        artefacts=principal_artefact_lines(root, args.epic_dir),
        readiness_output=readiness_output,
        round_context=round_context,
    )

    if getattr(args, "developer_note", None):
        prompt += f"\n\n## Developer Special Instructions\n\n{args.developer_note}\n"

    before = status_lines(root)
    code, out, err = execute(cli_command(args.cli, args.model, getattr(args, "thinking_level", None)), root, args.timeout, prompt)
    changed = tree_changes(root, before, sha)
    return record_round(root, args, sha, [Pass("principal", code, out, err, prompt)], changed,
                        {"Kind": "principal", **scope})


def run_adhoc_code(root: Path, args: argparse.Namespace, sha: str) -> int:
    commit_spec = getattr(args, "commits", None) or f"{args.base}...HEAD"
    log, diff_section = diff_range(root, args.base, getattr(args, "commits", None))

    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
        rules=RULES.read_text(encoding="utf-8").strip(),
        sha=sha,
        base=args.base,
        epic_dir=f"Ad-hoc diff review ({commit_spec})",
        artefacts=f"- Commit range: `{commit_spec}`",
        audit_output=f"Commit log ({commit_spec}):\n{log or '(no commits)'}",
        results_output="N/A (Ad-hoc review of branch diff)",
        round_context="",
        diff_section=diff_section,
    )

    before = status_lines(root)
    code, out, _err = execute(cli_command(args.cli, args.model, getattr(args, "thinking_level", None)), root, args.timeout, prompt)
    changed = tree_changes(root, before, sha)
    if changed:
        print(f"error: tree modified during review: {', '.join(changed)}", file=sys.stderr)
        return 2

    lines = out.splitlines()
    marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
    verdict = marks[-1][1] if marks else None
    findings = parse_findings(out, verdict)

    cli_display = {"claude": "Claude", "codex": "Codex", "agy": "agy", "kiro": "Kiro", "ollama": "Ollama"}.get(args.cli, args.cli.capitalize())
    triage_out = format_triage_header(
        f"Cross-Model Review Triage: {commit_spec} ({cli_display})",
        sha,
        args.cli,
        effective_model(args.cli, args.model),
        effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
        verdict or "none",
        findings,
    )
    if findings:
        triage_out += [
            "",
            "## Findings",
            "",
            "| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
            "|---|----------|----------|---------|------------|----------|-----------------|",
            *(f"| {i} | {sev} | {cell(loc)} | {cell(problem)} | ? | ? | ? |" for i, (sev, loc, problem) in enumerate(findings, 1)),
        ]
    else:
        triage_out += ["", "## Findings", "", "None."]
    triage_out += ["", "## Next Steps", "", NEXT_STEPS]
    print("\n".join(triage_out))
    update_sticky_review_config(root, args.cli, args.model, getattr(args, "thinking_level", None))

    if code != 0 or verdict is None:
        return 2
    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0



def run(args: argparse.Namespace) -> int:
    kind = getattr(args, "kind", "code")
    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())

    cli, model, thinking_level = resolve_review_settings(
        root=root,
        epic_dir=getattr(args, "epic_dir", None),
        kind=kind,
        cli_arg=args.cli,
        model_arg=args.model,
        thinking_arg=getattr(args, "thinking_level", None),
        auto_quota=bool(getattr(args, "auto_quota", False)),
    )
    args.cli = cli
    args.model = model
    args.thinking_level = thinking_level

    if kind == "principal" and args.cli == "ollama":
        print("--kind principal supports --cli claude, codex, or agy (and kiro)", file=sys.stderr)
        return 2

    if args.cli == "ollama":
        if not args.model:
            print("--cli ollama needs --model", file=sys.stderr)
            return 2
    elif not resolve_cli_binary(args.cli):
        print(f"{args.cli} not found on PATH", file=sys.stderr)
        return 2
    if status_lines(root):
        print("commit or stash your changes before a review", file=sys.stderr)
        return 2
    max_rounds = getattr(args, "max_rounds", MAX_REVIEW_ROUNDS)
    if getattr(args, "epic_dir", None) and not getattr(args, "force", False):
        completed_count = _completed_rounds_count(root, args.epic_dir, kind)
        if completed_count >= max_rounds:
            print_gate_banner(
                PreconditionFailedError(
                    "Max review rounds",
                    f"Max review rounds ({max_rounds}) reached; Circuit Breaker halted for human architect",
                ),
                args.cli,
            )
            return 2
    sha = head_of(root)

    if kind == "principal":
        return run_principal(root, args, sha)

    if not args.epic_dir:
        return run_adhoc_code(root, args, sha)

    model_ctx = None
    if args.cli == "ollama":
        try:
            model_ctx = local_review.probe(args.host, args.model)
        except local_review.LocalReviewError as error:
            print_gate_banner(PreconditionFailedError("Ollama probe", str(error)), args.cli)
            return 2
    hld_text = (root / ".devtool" / "epic" / args.epic_dir / f"{args.epic_dir}.en.md").read_text(encoding="utf-8")
    try:
        facts_timeout = getattr(args, "facts_timeout", 300)
        audit_output, results_output = collect_facts(root, args.epic_dir, args.base, hld_text, facts_timeout)
    except PreconditionFailedError as error:
        print_gate_banner(error, args.cli)
        return 2
    if args.cli == "ollama":
        return run_local(root, args, sha, audit_output, results_output, model_ctx)
    diff_limit = getattr(args, "diff_limit", MAX_DIFF_LINES)
    round_context, scope = delta_round_context(root, args, sha, kind="code")
    if scope:
        print(f"{scope['Scope']}: reviewing the revision delta, not the full epic diff (--full to review everything)",
              file=sys.stderr)
    diff_section = build_diff_section(root, args.base, sha, max_lines=diff_limit)
    prompt = Template(PROMPT.read_text(encoding="utf-8")).safe_substitute(
        rules=RULES.read_text(encoding="utf-8").strip(),
        sha=sha,
        base=args.base,
        epic_dir=f".devtool/epic/{args.epic_dir}",
        artefacts=artefact_lines(root, args.epic_dir),
        audit_output=audit_output.rstrip(),
        results_output=results_output.rstrip(),
        round_context=round_context,
        diff_section=diff_section,
    )
    before = status_lines(root)  # after the facts: running the test commands may write build output
    code, out, err = execute(cli_command(args.cli, args.model, args.thinking_level), root, args.timeout, prompt)
    changed = tree_changes(root, before, sha)
    return record_round(root, args, sha, [Pass("review", code, out, err, prompt)], changed, scope)


def live_log_dir(root: Path, epic_dir: str) -> Path:
    """Where each pass streams its output: build/local-review/<epic_dir> when Git ignores it, else the Git directory.

    Either place leaves `git status` untouched, so the logs never trip the tree-modified check."""
    visible = root / "build" / "local-review" / epic_dir
    if subprocess.run(["git", "check-ignore", "-q", str(visible)], cwd=root, check=False).returncode == 0:
        return visible
    return root / git_run(root, "rev-parse", "--git-path", f"local-review/{epic_dir}").decode().strip()


def run_local(root: Path, args: argparse.Namespace, sha: str, audit_output: str, results_output: str,
              model_ctx: int | None) -> int:
    """Fit every slice before the first call, then review them one at a time; the first failed pass ends the run."""
    ctx = args.num_ctx or model_ctx or local_review.DEFAULT_NUM_CTX
    planned: list[tuple[local_review.Slice, str]] = []
    try:
        for slice_ in local_review.build_slices(root, args.epic_dir, args.base, sha, audit_output, results_output,
                                                EXCLUDES):
            system = local_review.render_system(slice_)
            budget = int(ctx * local_review.PROMPT_SHARE) - local_review.estimate_tokens(system)
            planned.append((local_review.fit(slice_, budget), system))
    except local_review.LocalReviewError as error:
        print_gate_banner(PreconditionFailedError("Context budget", str(error)), args.cli)
        return 2
    logs = live_log_dir(root, args.epic_dir)
    logs.mkdir(parents=True, exist_ok=True)
    print(f"{CYAN}Live logs:{RESET} {logs}", file=sys.stderr, flush=True)
    before = status_lines(root)
    passes: list[Pass] = []
    for number, (slice_, system) in enumerate(planned, 1):
        user = local_review.render_user(slice_)
        prompt_tokens = local_review.estimate_tokens(system) + local_review.estimate_tokens(user)
        options = local_review.chat_options(model_ctx, args.num_ctx, prompt_tokens)
        print(f"{CYAN}⏳ [Pass {number}/{len(planned)}]{RESET} {slice_.label} ... ", end="", file=sys.stderr, flush=True)
        started = time.monotonic()
        reply = local_review.chat(args.host, args.model, system, user, options, args.timeout,
                                  logs / f"{number}-{slice_.label}.log")
        code = 0 if reply.error is None else None if reply.error.startswith("timed out") else 1
        passes.append(Pass(slice_.label, code, reply.content, reply.error or "", user, slice_.omitted,
                           reply.done_reason))
        if reply.error is not None or reply.done_reason != "stop":
            print(f"{RED}❌ {reply.error or f'done_reason {reply.done_reason}'}{RESET}", file=sys.stderr, flush=True)
            break
        print(f"{GREEN}✅ {round(time.monotonic() - started)}s{RESET}", file=sys.stderr, flush=True)
    changed = tree_changes(root, before, sha)
    return record_round(root, args, sha, passes, changed, {"Passes": str(len(planned)), "Context": str(ctx)})


@dataclass(frozen=True)
class Pass:
    label: str
    code: int | None  # 0 transport success, None timeout, otherwise failure
    out: str  # the text the parser reads
    err: str
    shown: str  # what the reviewer was shown
    omitted: tuple[str, ...] = ()
    done_reason: str | None = None


def tree_changes(root: Path, before: list[str], sha: str) -> list[str]:
    """Status lines that appeared or vanished since `before`, led by HEAD when it moved."""
    changed = sorted(set(status_lines(root)) ^ set(before))
    if head_of(root) != sha:
        changed.insert(0, "HEAD")
    return changed


def path_of(location: str) -> str:
    """The file a finding points at: its location before the first colon, without backticks."""
    return location.split(":", 1)[0].strip().strip("`")


def annotate(finding: tuple[str, str, str], shown: str) -> tuple[str, str, str]:
    """Mark a blocking finding whose location path the reviewer was never shown; its severity stays."""
    sev, loc, problem = finding
    if sev in BLOCKING and loc != "unparsed" and path_of(loc) not in shown:
        problem += " (location not shown to reviewer)"
    return sev, loc, problem


def pass_output(item: Pass, number: int, args: argparse.Namespace) -> str:
    if args.cli == "ollama":
        return f"### Pass {number}: {item.label}\n\n{item.out}" + (f"\n--- error ---\n{item.err}" if item.err.strip() else "")
    output = item.out + (f"\n--- stderr ---\n{item.err}" if item.err.strip() else "")
    if item.code is None:
        output += f"\n--- timed out after {args.timeout} seconds ---\n"
    return output


def record_round(root: Path, args: argparse.Namespace, sha: str, passes: list[Pass],
                 changed: list[str], extra: dict[str, str]) -> int:
    """Append one round to review_results.md from every pass of a review; return the run's exit code."""
    local = args.cli == "ollama"
    verdicts: list[str | None] = []
    findings: list[tuple[str, str, str]] = []
    complete = True
    for item in passes:
        lines = item.out.splitlines()
        marks = [(index, m.group(1).upper()) for index, line in enumerate(lines) if (m := VERDICT.match(line))]
        verdict = marks[-1][1] if marks else None
        if local:  # a draft line in the Analysis above the verdict block is never a finding
            block = "\n".join(lines[marks[-1][0]:]) if marks else ""
            found = [annotate(finding, item.shown) for finding in parse_findings(block, verdict)]
        else:
            found = parse_findings(item.out, verdict)
        verdicts.append(verdict)
        findings.extend(found)
        complete = complete and item.code == 0 and verdict is not None \
            and not (verdict == "CHANGES REQUIRED" and not found) and (not local or item.done_reason == "stop")
    if changed:
        status = f"discarded: tree modified ({', '.join(line[3:] if line != 'HEAD' else line for line in changed)})"
    else:
        status = "completed" if complete else "no verdict"
    if "CHANGES REQUIRED" in verdicts:
        verdict_text = "CHANGES REQUIRED"
    else:
        verdict_text = "PASS" if verdicts and None not in verdicts else "none"
    name, title = review_file(getattr(args, "kind", "code"))
    path = root / ".devtool" / "epic" / args.epic_dir / name
    existing = path.read_text(encoding="utf-8") if path.exists() else f"# {title}: {args.epic_dir}\n"
    round_num = len(rounds_in(existing)) + 1
    meta = {
        "Date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "SHA": sha,
        "Base": args.base,
        "CLI": args.cli,
        "Model": effective_model(args.cli, args.model),
        "Thinking": effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
        "Status": status,
        "Verdict": verdict_text,
        **extra,
    }
    if (omitted := "; ".join(f"{item.label}: {', '.join(item.omitted)}" for item in passes if item.omitted)):
        meta["Omitted"] = omitted
    output = "\n\n".join(pass_output(item, number, args) for number, item in enumerate(passes, 1))
    text = existing.rstrip("\n") + "\n\n" + render_round(round_num, meta, findings, output)
    path.write_text(text, encoding="utf-8")
    update_sticky_review_config(root, args.cli, getattr(args, "model", None), getattr(args, "thinking_level", None))
    header = format_triage_header(
        f"Round {round_num}: {status} ({path.relative_to(root)})",
        sha,
        args.cli,
        effective_model(args.cli, getattr(args, "model", None)),
        effective_thinking_level(args.cli, getattr(args, "thinking_level", None)),
        verdict_text,
        findings,
    )
    print("\n".join(header))
    if status != "completed":
        print(f"- **Status**: {status}")
        return 2
    return 1 if any(sev in BLOCKING for sev, _, _ in findings) else 0


def check(args: argparse.Namespace) -> int:
    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    name, _ = review_file(getattr(args, "kind", "code"))
    path = root / ".devtool" / "epic" / args.epic_dir / name
    if not path.exists():
        return 0
    completed = [(n, lines) for n, lines in rounds_in(path.read_text(encoding="utf-8"))
                 if "- **Status**: completed" in metadata(lines)]
    undecided = []
    for line, cells in table_findings(completed[-1][1]) if completed else []:
        if len(cells) != 5:
            undecided.append(f"undecided: unreadable findings row: {line.strip()}")
        elif cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")):
            undecided.append(f"undecided: #{cells[0]} {cells[1]} {cells[2]}")
    if undecided:
        print("\n".join(undecided))
    return 1 if undecided else 0


def round_meta(lines: list[str]) -> dict[str, str]:
    """A round's `- **Key**: value` fields."""
    return {m.group(1): m.group(2) for line in metadata(lines) if (m := META_LINE.match(line))}


def round_output(lines: list[str]) -> str:
    """The fenced raw output of a round, without its fence."""
    body = lines[lines.index("Raw output:") + 1:] if "Raw output:" in lines else []
    fences = [(index, match.group(1)) for index, line in enumerate(body) if (match := FENCE.match(line))]
    if not fences:
        return ""
    start, fence = fences[0]
    end = next((i for i in range(start + 1, len(body)) if body[i].rstrip() == fence), len(body))
    return "\n".join(body[start + 1:end])


def round_passes(output: str) -> list[tuple[str, str, str]]:
    """(pass, verdict, error) for each `### Pass` block, or one `review` pass when there is none."""
    blocks: list[tuple[str, list[str]]] = []
    for line in output.splitlines():
        if (header := PASS_HEADER.match(line)):
            blocks.append((f"{header.group(1)} {header.group(2)}", []))
        elif blocks:
            blocks[-1][1].append(line)
    rows = []
    for name, lines in blocks or [("review", output.splitlines())]:
        verdicts = [m.group(1).upper() for line in lines if (m := VERDICT.match(line))]
        after = lines[lines.index("--- error ---") + 1:] if "--- error ---" in lines else []
        rows.append((name, verdicts[-1] if verdicts else "none", after[0].strip() if after else "—"))
    return rows


def finding_rows(lines: list[str]) -> list[list[str]]:
    return [cells for _, cells in table_findings(lines) if len(cells) == 5]


def comparison_row(number: int, lines: list[str]) -> str:
    meta, rows = round_meta(lines), finding_rows(lines)
    counts = [sum(cells[1] == severity for cells in rows) for severity in ("Critical", "Important", "Minor")]
    fixed = sum(cells[4].startswith("fixed in ") for cells in rows)
    dismissed = sum(cells[4].startswith("dismissed: ") for cells in rows)
    undecided = sum(cells[1] in BLOCKING and not cells[4].startswith(("fixed in ", "dismissed: ")) for cells in rows)
    values = [str(number), f"{meta.get('CLI', '?')} / {meta.get('Model', '?')}", meta.get("SHA", "?")[:7],
              meta.get("Status", "?"), meta.get("Verdict", "?"), *map(str, [*counts, fixed, dismissed, undecided])]
    return "| " + " | ".join(cell(value) for value in values) + " |"


def since_lines(previous: list[list[str]], latest: list[list[str]]) -> list[str]:
    """What became of the previous round's blocking or fixed findings, compared by file path."""
    lines = []
    for cells in previous:
        fixed = cells[4].startswith("fixed in ")
        if cells[1] not in BLOCKING and not fixed:
            continue
        again = [f"#{row[0]}" for row in latest if path_of(row[2]) == path_of(cells[2])]
        if again:
            lines.append(f"- {cells[2]}: re-reported at the same path ({', '.join(again)})"
                         + (" — check the fix" if fixed else ""))
        else:
            lines.append(f"- {cells[2]}: not re-reported")
    return lines or ["No blocking or fixed finding in the previous round."]


HIGH_RISK_KEYWORDS = (
    "security",
    "race",
    "deadlock",
    "corrupt",
    "rollback",
    "contract",
    "shared-contracts",
    "unbound",
    "notimplementederror",
    "_stub",
    "leak",
    "crash",
    "injection",
    "signature",
)


SHARED_CONTRACT_MARKERS = (
    "shared-contracts",
    "api_contract.md",
    "architecture_and_flow.md",
    "gaps_and_rfcs.md",
    "contract_sync.json",
)


def is_shared_contract_conflict(row: list[str]) -> bool:
    """Return True when a finding directly impacts or conflicts with shared-contracts/."""
    combined = f"{row[2]} {row[3]}".lower()
    return any(marker in combined for marker in SHARED_CONTRACT_MARKERS)


def _finding_risk_sort_key(row: list[str]) -> tuple[int, int, int, int, int]:
    """Rank findings by (severity_rank, is_not_shared_contract, is_non_prod_path, missing_high_risk_keyword, original_index)."""
    sev_rank = {"Critical": 0, "Important": 1, "Minor": 2}.get(row[1], 3)
    not_contract = 0 if is_shared_contract_conflict(row) else 1
    loc = row[2].lower()
    prob = row[3].lower()
    is_non_prod = 0 if (loc.startswith("src/") or "shared-contracts" in loc or "bdd_scenarios" in loc) else 1
    has_risk_kw = 0 if any(kw in prob or kw in loc for kw in HIGH_RISK_KEYWORDS) else 1
    try:
        idx = int(row[0])
    except ValueError:
        idx = 999
    return (sev_rank, not_contract, is_non_prod, has_risk_kw, idx)


def top_risk_findings_section(latest: list[list[str]], limit: int = 3) -> list[str]:
    """Filter and rank the Top 3 highest-risk findings for executive reporting and design-anchored fixing."""
    if not latest:
        return [
            f"## Top {limit} Highest-Risk Findings (Executive Report)",
            "",
            "None.",
        ]
    ranked = sorted(latest, key=_finding_risk_sort_key)[:limit]
    lines = [
        f"## Top {limit} Highest-Risk Findings (Executive Report)",
        "",
        "> **Strict Approved-Design Anchoring & Forward-Alignment Rule**: Tier 1 (User-approved Spec `*-design.en.md` & HLD `<epic_dir>.en.md`) "
        "takes precedence over legacy `shared-contracts/` and legacy `src/` code. When Tier 1 intentionally changes steps/enums/schemas "
        "(e.g. 7 steps -> 5 steps) but `shared-contracts/` or `src/` still holds legacy values, NEVER propose reverting Tier 1 to the old design; "
        "always propose **Forward Alignment** (update `shared-contracts/` + `sync_contracts.py ack` and add affected `src/` files to task `Allowed files`).",
        "",
        "| Rank | # | Severity | Location | Problem | Design Anchor (HLD / BDD / Decisions Already Made) | Proposed action |",
        "|------|---|----------|----------|---------|----------------------------------------------------|-----------------|",
    ]
    for rank, cells in enumerate(ranked, 1):
        lines.append(f"| #{rank} | {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? |")
    return lines


def auto_triage_section(
    number: int,
    rounds: list[tuple[int, list[str]]],
    latest: list[list[str]],
    max_rounds: int = MAX_REVIEW_ROUNDS,
) -> list[str]:
    """Severity-Tiered Auto-Triage Gate & Circuit Breaker evaluation for the latest round."""
    blocking_rows = [cells for cells in latest if cells[1] in BLOCKING]
    critical_rows = [cells for cells in latest if cells[1] == "Critical"]
    important_rows = [cells for cells in latest if cells[1] == "Important"]
    minor_rows = [cells for cells in latest if cells[1] == "Minor"]
    contract_conflict_rows = [cells for cells in blocking_rows if is_shared_contract_conflict(cells)]
    fix_loop_paths: list[str] = []
    if len(rounds) >= 2 and blocking_rows:
        prev_fixed_paths = {
            path_of(prev[2])
            for prev in finding_rows(rounds[-2][1])
            if prev[4].startswith("fixed in ")
        }
        for row in blocking_rows:
            p = path_of(row[2])
            if p and p in prev_fixed_paths and p not in fix_loop_paths:
                fix_loop_paths.append(p)

    if not blocking_rows:
        action = "AUTO_PASS_FINAL_MINOR_SWEEP" if minor_rows else "AUTO_PASS_CLEAN"
        reason = (
            f"0 Critical and 0 Important findings ({len(minor_rows)} Minor). "
            "Fix valid Minor items once (strictly anchored to approved HLD/BDD/Task contracts), run local quality gate green, "
            "and finish stage immediately without calling external reviewer again."
            if minor_rows
            else "0 findings. Stage review passed cleanly."
        )
    elif contract_conflict_rows:
        ids = ", ".join(f"#{r[0]}" for r in contract_conflict_rows)
        action = "CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)"
        reason = (
            f"Shared-contract conflict detected in finding(s) {ids}: directly impacts `shared-contracts/` "
            "(`api_contract.md` / `architecture_and_flow.md` / `gaps_and_rfcs.md`). "
            "STOP IMMEDIATELY — do NOT auto-fix, do NOT revert user-approved HLD steps/schemas to legacy contracts, "
            "and do NOT continue autonomous execution. Report Top 3 Highest-Risk Findings to Human Architect immediately."
        )
    elif fix_loop_paths:
        action = "CIRCUIT_BREAKER_HALT (FIX_LOOP)"
        reason = (
            f"Fix Loop detected across consecutive rounds on {', '.join(fix_loop_paths)}. "
            "STOP IMMEDIATELY — halt auto-pilot and escalate Top 3 Highest-Risk Findings to Human Architect."
        )
    elif number >= max_rounds and critical_rows:
        ids = ", ".join(f"#{r[0]}" for r in critical_rows)
        action = "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)"
        reason = (
            f"After {number}/{max_rounds} review rounds, {len(critical_rows)} Critical finding(s) ({ids}) still remain unresolved. "
            "STOP IMMEDIATELY — do NOT continue autonomous execution; report Top 3 Highest-Risk Findings to Human Architect."
        )
    elif number >= max_rounds:
        action = "AUTO_PASS_FINAL_SWEEP"
        reason = (
            f"Round {number}/{max_rounds} reached max_rounds with 0 Critical findings ({len(important_rows)} Important, {len(minor_rows)} Minor, no Fix Loop or contract conflict). "
            "Apply one final fix sweep anchored to approved design, run local quality gate green, and finish stage without invoking a 4th review round."
        )
    else:
        action = "AUTO_FIX_ELIGIBLE"
        reason = (
            f"Round {number}/{max_rounds} has {len(blocking_rows)} Critical/Important finding(s) and no Fix Loop or shared-contract conflict. "
            "Verify against approved design (HLD, bdd_scenarios.en.md, Decisions Already Made): if Valid, "
            "auto-record decisions, switch to Role 2.3 to fix, run local quality gate, "
            "and advance to next review round."
        )
    return [
        "## Auto-Triage Gate",
        "",
        f"- **Action**: {action}",
        f"- **Round**: {number} / {max_rounds}",
        f"- **Directive**: {reason}",
    ]


def triage(args: argparse.Namespace) -> int:
    """Print the latest round as a skeleton to fill, verify and present before any action on its findings."""
    root = Path(git_run(Path.cwd(), "rev-parse", "--show-toplevel").decode().strip())
    name, _ = review_file(getattr(args, "kind", "code"))
    path = root / ".devtool" / "epic" / args.epic_dir / name
    rounds = rounds_in(path.read_text(encoding="utf-8")) if path.exists() else []
    if not rounds:
        print(f"no review round recorded for {args.epic_dir}", file=sys.stderr)
        return 2
    number, lines = rounds[-1]
    meta = round_meta(lines)
    cli = meta.get("CLI", "claude")
    title = f"# Review Triage: {args.epic_dir}, Round {number}"
    latest = finding_rows(lines)
    header = format_triage_header(
        title,
        meta.get("SHA", "?"),
        cli,
        meta.get("Model", "?"),
        meta.get("Thinking", "high"),
        meta.get("Verdict", "none"),
        latest,
    )
    if meta.get("Status") and meta.get("Status") != "completed":
        header.append(f"- **Status**: {meta.get('Status')}")
    out = [
        *header,
        "",
        *top_risk_findings_section(latest, limit=3),
        "",
        "## Passes",
        "",
        "| Pass | Verdict | Error |",
        "|------|---------|-------|",
        *(f"| {cell(name)} | {verdict} | {cell(error)} |" for name, verdict, error in round_passes(round_output(lines))),
        "",
        "## Findings",
        "",
    ]
    if latest:
        out += [
            "| # | Severity | Location | Problem | Assessment | Evidence | Proposed action |",
            "|---|----------|----------|---------|------------|----------|-----------------|",
            *(f"| {cells[0]} | {cells[1]} | {cell(cells[2])} | {cell(cells[3])} | ? | ? | ? |" for cells in latest),
        ]
    else:
        out.append("None.")
    out += [
        "",
        "## Round Comparison",
        "",
        "| Round | CLI / Model | SHA | Status | Verdict | Critical | Important | Minor | Fixed | Dismissed | Undecided |",
        "|-------|-------------|-----|--------|---------|----------|-----------|-------|-------|-----------|-----------|",
        *(comparison_row(n, round_lines) for n, round_lines in rounds),
        "",
    ]
    if len(rounds) > 1:
        out += [f"## Since Round {rounds[-2][0]}", "", *since_lines(finding_rows(rounds[-2][1]), latest)]
    else:
        out += ["## Since the Previous Round", "", "No earlier round."]
    out += ["", *auto_triage_section(number, rounds, latest, getattr(args, "max_rounds", MAX_REVIEW_ROUNDS))]
    out += ["", "## Next Steps", "", NEXT_STEPS]
    print("\n".join(out))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    runner = modes.add_parser("run", help="have the CLI review the epic and record a round")
    runner.add_argument("--kind", choices=KINDS, default="code")
    runner.add_argument("--epic-dir")
    runner.add_argument("--doc")
    runner.add_argument("--base", required=True)
    runner.add_argument("--cli", choices=("claude", "codex", "ollama", "agy", "kiro"), default=None)
    runner.add_argument("--model")
    runner.add_argument("--thinking-level", choices=THINKING_LEVELS, default=None)
    runner.add_argument("--host", default=local_review.host_from_env())
    runner.add_argument("--num-ctx", type=int, default=None)
    runner.add_argument("--timeout", type=int, default=1800)
    runner.add_argument("--facts-timeout", type=int, default=300)
    runner.add_argument("--diff-limit", type=int, default=MAX_DIFF_LINES)
    runner.add_argument("--commits")
    runner.add_argument("--developer-note")
    runner.add_argument("--max-rounds", type=int, default=MAX_REVIEW_ROUNDS,
                        help="maximum completed review rounds before Circuit Breaker halts (default: 3)")
    runner.add_argument("--force", action="store_true",
                        help="override the max-rounds Circuit Breaker limit when explicitly requested")
    runner.add_argument("--auto-quota", action="store_true",
                        help="auto-select provider in Claude -> Codex -> Kiro -> Argon order using check-quota thresholds")
    runner.add_argument("--full", action="store_true",
                        help="review every artefact/diff even when an earlier round exists (default: delta)")
    checker = modes.add_parser("check", help="list undecided blocking findings of the latest completed round")
    checker.add_argument("--kind", choices=KINDS, default="code")
    checker.add_argument("--epic-dir", required=True)
    triager = modes.add_parser("triage", help="print the latest round as a skeleton to fill before acting on it")
    triager.add_argument("--kind", choices=KINDS, default="code")
    triager.add_argument("--epic-dir", required=True)
    triager.add_argument("--max-rounds", type=int, default=MAX_REVIEW_ROUNDS)
    args = parser.parse_args(argv)

    if args.mode == "run":
        if args.doc:
            if getattr(args, "kind", "code") != "principal":
                print("error: --doc requires --kind principal", file=sys.stderr)
                return 2
            if args.epic_dir:
                print("error: specify either --epic-dir or --doc, not both", file=sys.stderr)
                return 2
        elif not args.epic_dir and getattr(args, "kind", "code") == "principal":
            print("error: one of --epic-dir or --doc is required for principal review", file=sys.stderr)
            return 2

    try:
        return {"run": run, "check": check, "triage": triage}[args.mode](args)
    except (ContractError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
