"""End-to-end acceptance tests for the four_persona_governance epic.

Covers BDD scenarios:
- FPG-HP-08: End-to-end English-only epic flows from readiness to dashboard with persona stubs
- FPG-HP-16: The dev-config quick guide documents only commands the real CLI accepts and keeps both language variants in step
"""

from __future__ import annotations

import ast
from collections.abc import Iterator, Sequence
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any
import unittest
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
LIFECYCLE_SCRIPTS = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"
CHECK_TASKS_SCRIPTS = REPO_ROOT / "skills" / "check-tasks" / "resources" / "scripts"

EXPECTED_FPG_SUITES: tuple[tuple[str, bool], ...] = (
    ("tests/test_fpg_persona_config.py", False),
    ("tests/test_fpg_dispatch_and_quota.py", False),
    ("tests/test_fpg_provider_shortcut.py", False),
    ("tests/test_fpg_agy_profile_pool.py", False),
    ("tests/test_fpg_agy_dispatch.py", False),
    ("tests/test_fpg_set_provider_model_profile.py", False),
    ("tests/test_fpg_checkpoint_and_briefs.py", False),
    ("tests/test_fpg_runner_personas.py", False),
    ("tests/test_fpg_english_only_and_ownership.py", False),
    ("tests/test_fpg_dashboard_sync.py", False),
    ("tests/test_fpg_governance_text.py", True),
    ("tests/test_fpg_english_only_text.py", True),
    ("tests/test_fpg_acceptance.py", False),
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PASSWORD_RE = re.compile(r"\bpassword\b", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"<[^>\s]+>")


def _load_module(
    name: str,
    path: Path,
    *,
    extra_sys_path: Path | None = None,
) -> ModuleType:
    """Load a kit Python module by path and register it in sys.modules."""
    existing = sys.modules.get(name)
    if existing is not None and getattr(existing, "__file__", None):
        if Path(str(existing.__file__)).resolve() == path.resolve():
            return existing
    if extra_sys_path is not None and str(extra_sys_path) not in sys.path:
        sys.path.insert(0, str(extra_sys_path))
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None, f"Cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return mod


@contextlib.contextmanager
def _isolated_host_env(*, extra_bin: Path | None = None) -> Iterator[Path]:
    """Isolate HOME, REAL_HOME, PATH, profile env vars, and quota fetchers from host stores."""
    with (
        tempfile.TemporaryDirectory(
            prefix="fpg_accept_home_", ignore_cleanup_errors=True
        ) as tmp,
        contextlib.ExitStack() as stack,
    ):
        fake_home = Path(tmp) / "_isolated_home"
        fake_home.mkdir(parents=True, exist_ok=True)
        clean_path = [
            entry
            for entry in os.environ.get("PATH", "").split(os.pathsep)
            if entry and "/antigravity_homes" not in entry
        ]
        if extra_bin is not None:
            clean_path.insert(0, str(extra_bin))
        env_patch = {
            "HOME": str(fake_home),
            "REAL_HOME": str(fake_home),
            "USER": "fpg_tester",
            "PATH": os.pathsep.join(clean_path),
        }
        stack.enter_context(patch.dict(os.environ, env_patch))
        for var in (
            "AGY_PROFILE",
            "ANTIGRAVITY_PROFILE",
            "AGY_PROGRAMMER_MODEL",
            "AGY_PROGRAMMER_EFFORT",
            "AGY_ASSISTANT_MODEL",
        ):
            os.environ.pop(var, None)

        rer_mod = _load_module(
            "run_external_review",
            DEV_IMPL_SCRIPTS / "run_external_review.py",
            extra_sys_path=DEV_IMPL_SCRIPTS,
        )
        if hasattr(rer_mod, "_default_quota_fetcher"):
            stack.enter_context(
                patch.object(rer_mod, "_default_quota_fetcher", lambda _cli: {})
            )
        pool_mod = _load_module(
            "agy_profile_pool",
            SCRIPTS_DIR / "agy_profile_pool.py",
            extra_sys_path=SCRIPTS_DIR,
        )
        if hasattr(pool_mod, "default_fetcher"):
            stack.enter_context(
                patch.object(pool_mod, "default_fetcher", lambda _prof: {})
            )
        ct_mod = _load_module(
            "check_tasks",
            CHECK_TASKS_SCRIPTS / "check_tasks.py",
            extra_sys_path=CHECK_TASKS_SCRIPTS,
        )
        if hasattr(ct_mod, "discover_antigravity_profiles"):
            stack.enter_context(
                patch.object(
                    ct_mod, "discover_antigravity_profiles", lambda *a, **k: []
                )
            )
        yield fake_home


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed in {cwd}: {res.stderr.strip() or res.stdout.strip()}"
        )
    return res.stdout.strip()


def _init_git_repo(repo_dir: Path) -> None:
    repo_dir.mkdir(parents=True, exist_ok=True)
    _git(repo_dir, "init", "-q", "-b", "main")
    _git(repo_dir, "config", "user.name", "FPG Tester")
    _git(repo_dir, "config", "user.email", "fpg@example.invalid")
    (repo_dir / ".gitignore").write_text(
        ".devtool/state/\n.devtool/logs/\n.worktrees/\nbuild/\n",
        encoding="utf-8",
    )


def _copy_dev_impl_scripts(repo_dir: Path) -> None:
    dst = repo_dir / "skills" / "dev-implementation" / "resources" / "scripts"
    dst.mkdir(parents=True, exist_ok=True)
    for name in (
        "_epic_docs.py",
        "check_bdd_traceability.py",
        "compute_execution_order.py",
        "manage_worker_pool.py",
        "result_reports.py",
        "slug_utils.py",
        "sync_task_status.py",
        "task_contract.py",
    ):
        shutil.copy2(DEV_IMPL_SCRIPTS / name, dst / name)


def _write_agy_stub(bin_dir: Path, spy_log: Path) -> Path:
    """Create a stub `agy` executable that logs argv and returns valid summary JSON."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    run_checks = str(DEV_IMPL_SCRIPTS / "run_task_checks.py")
    stub = bin_dir / "agy"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import fcntl, json, os, pathlib, re, subprocess, sys\n"
        "prompt = sys.stdin.read()\n"
        "args = sys.argv[1:]\n"
        "if args == ['models']:\n"
        "    print('gemini-4-argon-medium\\ngemini-4-hydrogen-medium\\ngemini-4-hydrogen-high')\n"
        "    raise SystemExit(0)\n"
        "log_path = pathlib.Path(os.environ['FPG_AGY_SPY_LOG'])\n"
        "log_path.parent.mkdir(parents=True, exist_ok=True)\n"
        "with open(log_path, 'a', encoding='utf-8') as fh:\n"
        "    fcntl.flock(fh.fileno(), fcntl.LOCK_EX)\n"
        "    fh.write(json.dumps({'args': args, 'cwd': os.getcwd()}) + '\\n')\n"
        "    fh.flush()\n"
        "    fcntl.flock(fh.fileno(), fcntl.LOCK_UN)\n"
        "task_match = re.search(r'`(task_[^`]+)`', prompt)\n"
        "task_id = task_match.group(1) if task_match else 'task_01_alpha'\n"
        "if '--sandbox' in args:\n"
        "    sha_m = re.search(r'head_sha `([0-9a-f]+)`', prompt)\n"
        "    sha = sha_m.group(1) if sha_m else subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()\n"
        "    summary = {'task_id': task_id, 'verdict': 'PASS', 'head_sha': sha, 'done_gate': 'PASS', 'findings': []}\n"
        "    print('Review PASS\\n```json\\n' + json.dumps(summary) + '\\n```')\n"
        "    raise SystemExit(0)\n"
        f"run_checks_path = {run_checks!r}\n"
        "task_mirror = f'.devtool/epic/fpg_demo/{task_id}.md'\n"
        "subprocess.run([sys.executable, run_checks_path, 'red', task_mirror], check=True)\n"
        "target_rel = 'src/alpha.py' if 'alpha' in task_id else 'src/beta.py'\n"
        "target_file = pathlib.Path.cwd() / target_rel\n"
        "target_file.write_text(f'VALUE = \"{task_id}_done\"\\n', encoding='utf-8')\n"
        "subprocess.run([sys.executable, run_checks_path, 'verify', task_mirror], check=True)\n"
        "for rel in (task_mirror, f'.devtool/features/{task_id}.md'):\n"
        "    p = pathlib.Path.cwd() / rel\n"
        "    if p.is_file():\n"
        "        p.write_text(p.read_text(encoding='utf-8').replace('- [ ] ', '- [x] '), encoding='utf-8')\n"
        "subprocess.run(['git', 'add', target_rel, task_mirror, f'.devtool/epic/fpg_demo/evidence/{task_id}.json'], check=True)\n"
        "subprocess.run(['git', 'commit', '-q', '-m', f'[FPG_DEMO] Implement {task_id}'], check=True)\n"
        "head_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()\n"
        "tier = 'full' if 'beta' in task_id else 'standard'\n"
        "summary = {\n"
        "    'task_id': task_id,\n"
        "    'slot': 1,\n"
        "    'status': 'DONE',\n"
        "    'head_sha': head_sha,\n"
        "    'verify': 'PASS',\n"
        "    'changed_files': [target_rel],\n"
        "    'non_test_modules_changed': 1,\n"
        "    'review_tier': tier,\n"
        "    'labels': [],\n"
        "    'finalized': False,\n"
        "}\n"
        "print('Implemented\\n```json\\n' + json.dumps(summary) + '\\n```')\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def _make_task_md(
    task_id: str,
    *,
    allowed_path: str,
    symbol: str,
    covers_id: str,
    gherkin: str,
    review_tier: str,
    hld_rel: str,
) -> str:
    short = "alpha" if "alpha" in task_id else "beta"
    return (
        f"---\n"
        f'id: "{task_id}"\n'
        f'status: "todo"\n'
        f'priority: "high"\n'
        f"assignee: null\n"
        f'epic: "fpg_demo"\n'
        f"dueDate: null\n"
        f'created: "2026-11-17T10:00:00Z"\n'
        f'modified: "2026-11-17T10:00:00Z"\n'
        f"completedAt: null\n"
        f'labels: ["demo"]\n'
        f'order: "a1"\n'
        f'review_tier: "{review_tier}"\n'
        f"---\n\n"
        f"# Task {task_id}: Implement {symbol}\n\n"
        f"Epic: [fpg_demo]({hld_rel})\n\n"
        f"## Requirement Analysis\n\nImplement {task_id}.\n\n"
        f"## Files\n\n"
        f"Allowed files:\n- `{allowed_path}`\n\n"
        f"Read-only context:\n- `README.md` — repo overview\n\n"
        f"## Design Rationale\n\nMinimal task change.\n\n"
        f"## Impact Analysis & Blast Radius\n\n"
        f"- **Target Files & Symbols**:\n  - `{allowed_path}`: `{symbol}`\n\n"
        f"### BDD SCENARIOS\n\nCovers: {covers_id}\n\n{gherkin}\n\n"
        f"## Verification\n\n"
        f"| ID | Phase | Command | Expect | Needs |\n"
        f"|----|-------|---------|--------|-------|\n"
        f"| V1 | RED | `python3 tool.py red {short}` | exit 1 | — |\n"
        f"| V2 | GREEN | `python3 tool.py green {short}` | exit 0 | — |\n"
        f"| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
        f"| V4 | TIER-B | `mypy tool.py` | exit 0 | — |\n"
        f"| V5 | TIER-C | `python3 tool.py int {short}` | exit 0; results build/test-results/int.xml | — |\n\n"
        f"## Stop and Report If\n\n- Unexpected failure.\n\n"
        f"## Decisions Already Made\n\n- Keep change minimal.\n\n"
        f"## Definition of Done\n\n- [ ] Passed all checks (V2, V3, V4, V5).\n\n"
        f"## Dependencies & Blockers\n\nNone.\n"
    )


def _setup_demo_epic_repo(repo: Path) -> None:
    _init_git_repo(repo)
    _copy_dev_impl_scripts(repo)
    (repo / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    (repo / "scripts").mkdir(parents=True, exist_ok=True)
    (repo / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "src" / "beta.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "test_alpha.py").write_text(
        "def test_alpha():\n    assert True\n", encoding="utf-8"
    )
    (repo / "tool.py").write_text(
        "import pathlib\n"
        "import sys\n\n"
        "mode = sys.argv[1] if len(sys.argv) > 1 else 'green'\n"
        "target = sys.argv[2] if len(sys.argv) > 2 else 'alpha'\n"
        "src_text = pathlib.Path(f'src/{target}.py').read_text(encoding='utf-8')\n"
        "is_done = '_done' in src_text\n"
        "if mode == 'red':\n"
        "    raise SystemExit(0 if is_done else 1)\n"
        "if mode == 'green':\n"
        "    raise SystemExit(0 if is_done else 1)\n"
        "if mode == 'int':\n"
        "    if not is_done:\n"
        "        raise SystemExit(1)\n"
        "    tc = 'DEMO-HP-01' if target == 'alpha' else 'DEMO-EC-01'\n"
        "    out = pathlib.Path('build/test-results/int.xml')\n"
        "    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_text(\n"
        '        f\'<testsuite tests="1"><testcase classname="tests.Demo_Integration" name="{tc}"/></testsuite>\',\n'
        "        encoding='utf-8',\n"
        "    )\n",
        encoding="utf-8",
    )
    cfg_dir = repo / ".agents" / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "personas.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "overrides": {
                    "ai_architect_reviewer": {"model": "argon", "effort": "medium"},
                    "orchestrator": {"model": "hydrogen", "effort": "medium"},
                    "programmer": {"model": "hydrogen", "effort": "high"},
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    epic_dir = repo / ".devtool" / "epic" / "fpg_demo"
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / "2026-11-17-fpg-demo-design.md").write_text(
        "# Demo Design Spec\n\n## Table of Contents\n\n- [Meta Data](#meta-data)\n\n"
        "## Meta Data\n\n- **Status**: Approved (Gate 1)\n",
        encoding="utf-8",
    )
    (epic_dir / "fpg_demo.md").write_text(
        "# Demo Epic HLD\n\n## Table of Contents\n\n"
        "- [Meta Data](#meta-data)\n"
        "- [Integration Test Plan](#integration-test-plan)\n"
        "- [Verification Environment](#verification-environment)\n"
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n\n"
        "## Meta Data\n\n- **Epic**: `fpg_demo`\n- **Status**: Planned\n\n"
        "## Integration Test Plan\n\n"
        "Protected paths: scripts/verify.sh\n\n"
        "Integration test roots: tests/\n\n"
        "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
        "## Verification Environment\n\nTemp git repositories.\n\n"
        "## Kanban Tasks Breakdown\n\n"
        "1. [Task 01](task_01_alpha.md)\n"
        "2. [Task 02](task_02_beta.md)\n",
        encoding="utf-8",
    )
    sc_1 = (
        "```gherkin\n"
        "Scenario: [DEMO-HP-01] [Tier C - Integration] Alpha works\n"
        "  Given alpha exists\n"
        "  When alpha runs\n"
        "  Then alpha passes\n"
        "```"
    )
    sc_2 = (
        "```gherkin\n"
        "Scenario: [DEMO-EC-01] [Tier A - Unit] Beta works\n"
        "  Given beta exists\n"
        "  When beta runs\n"
        "  Then beta passes\n"
        "```"
    )
    (epic_dir / "bdd_scenarios.md").write_text(
        "# Demo BDD Scenarios\n\n## Table of Contents\n\n- [Scenarios](#scenarios)\n\n"
        f"## Scenarios\n\n### DEMO-HP-01\n\n{sc_1}\n\n### DEMO-EC-01\n\n{sc_2}\n",
        encoding="utf-8",
    )
    for fname, tid, apath, cov, sc, tier in (
        (
            "task_01_alpha.md",
            "task_01_alpha",
            "src/alpha.py",
            "DEMO-HP-01",
            sc_1,
            "standard",
        ),
        ("task_02_beta.md", "task_02_beta", "src/beta.py", "DEMO-EC-01", sc_2, "full"),
    ):
        (epic_dir / fname).write_text(
            _make_task_md(
                tid,
                allowed_path=apath,
                symbol="VALUE",
                covers_id=cov,
                gherkin=sc,
                review_tier=tier,
                hld_rel="fpg_demo.md",
            ),
            encoding="utf-8",
        )
        (features_dir / fname).write_text(
            _make_task_md(
                tid,
                allowed_path=apath,
                symbol="VALUE",
                covers_id=cov,
                gherkin=sc,
                review_tier=tier,
                hld_rel="../epic/fpg_demo/fpg_demo.md",
            ),
            encoding="utf-8",
        )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[FPG_DEMO] Seed English-only epic")


def _extract_fenced_commands(markdown_text: str) -> list[str]:
    """Extract lines starting with /d3nexus:dev-config or python3 scripts/dev_config.py from fences."""
    commands: list[str] = []
    in_fence = False
    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            continue
        if stripped.startswith(
            ("/d3nexus:dev-config", "python3 scripts/dev_config.py")
        ):
            commands.append(stripped)
    return commands


def _parse_verify_suites(verify_text: str) -> list[tuple[str, str, str, int, bool]]:
    match = re.search(
        r"^SUITES\s*=\s*(\[.*?\n\])", verify_text, flags=re.MULTILINE | re.DOTALL
    )
    assert match is not None, "Could not locate SUITES = [...] in scripts/verify.sh"
    parsed = ast.literal_eval(match.group(1))
    assert isinstance(parsed, list)
    return [
        (str(item[0]), str(item[1]), str(item[2]), int(item[3]), bool(item[4]))
        for item in parsed
    ]


def _run_fpg_hp_08_epic_flow() -> None:
    """Execute end-to-end English-only epic readiness through dashboard scan with stubs."""
    with tempfile.TemporaryDirectory(
        prefix="fpg_hp08_ws_", ignore_cleanup_errors=True
    ) as ws_tmp:
        ws = Path(ws_tmp)
        repo = ws / "repo"
        bin_dir = ws / "bin"
        spy_log = ws / "agy_calls.jsonl"
        _write_agy_stub(bin_dir, spy_log)

        with (
            _isolated_host_env(extra_bin=bin_dir) as fake_home,
            patch.dict(os.environ, {"FPG_AGY_SPY_LOG": str(spy_log)}),
        ):
            _setup_demo_epic_repo(repo)
            pc = _load_module(
                "persona_config",
                SCRIPTS_DIR / "persona_config.py",
                extra_sys_path=SCRIPTS_DIR,
            )
            lc = _load_module(
                "lifecycle_runner",
                LIFECYCLE_SCRIPTS / "lifecycle_runner.py",
                extra_sys_path=LIFECYCLE_SCRIPTS,
            )
            ct = _load_module(
                "check_tasks",
                CHECK_TASKS_SCRIPTS / "check_tasks.py",
                extra_sys_path=CHECK_TASKS_SCRIPTS,
            )

            # 1. Readiness check
            ready_proc = subprocess.run(
                [
                    sys.executable,
                    str(DEV_IMPL_SCRIPTS / "check_epic_readiness.py"),
                    "fpg_demo",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            assert ready_proc.returncode == 0, ready_proc.stdout + ready_proc.stderr

            # 2. Record Gate 2 + gate2_tasks_locked checkpoint
            for cmd in (
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "resume_context.py"),
                    "--gate",
                    "2",
                    "--epic",
                    "fpg_demo",
                    "--approved",
                    "HLD and tasks locked",
                ],
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "resume_context.py"),
                    "--checkpoint",
                    "gate2_tasks_locked",
                    "--epic",
                    "fpg_demo",
                    "--next",
                    "package epic",
                ],
                [
                    sys.executable,
                    str(DEV_IMPL_SCRIPTS / "package_epic.py"),
                    "fpg_demo",
                ],
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "resume_context.py"),
                    "--gate",
                    "3",
                    "--epic",
                    "fpg_demo",
                    "--approved",
                    "Execution order approved",
                ],
            ):
                proc = subprocess.run(
                    cmd, cwd=repo, capture_output=True, text=True, check=False
                )
                assert proc.returncode == 0, proc.stdout + proc.stderr

            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "[FPG_DEMO] Package handoff")

            # 3. Emit implement prompt and check persona binding + English-only docs
            emit_proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_DIR / "resume_context.py"),
                    "--emit-prompt",
                    "implement",
                    "--epic",
                    "fpg_demo",
                    "--epic-dir",
                    "fpg_demo",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
                check=False,
            )
            assert emit_proc.returncode == 0, emit_proc.stdout + emit_proc.stderr
            assert "gemini-4-hydrogen-medium" in emit_proc.stdout
            assert "gemini-4-hydrogen-high" in emit_proc.stdout
            assert "gemini-4-argon-medium" in emit_proc.stdout
            assert ".vi.md" not in emit_proc.stdout

            # 4. Run implementation step through LifecycleRunner with stub agy executable
            cfg = lc.RunnerConfig(real_home=fake_home)
            runner = lc.LifecycleRunner(root=repo, epic_slug="fpg_demo", config=cfg)
            runner.quota_gate = lambda *_a, **_kw: 0
            assert runner.step_implementation() is True, (
                f"step_implementation failed: last_error={runner.state.last_error!r}, "
                f"halt_reason={runner.state.halt_reason!r}"
            )

            # 5. Verify dispatch argv came from configured persona bindings
            calls = [
                json.loads(line)
                for line in spy_log.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            prog_binding = pc.resolve_persona("programmer", repo, real_home=fake_home)
            arch_binding = pc.resolve_persona(
                "ai_architect_reviewer", repo, real_home=fake_home
            )
            expected_prog_args = pc.build_dispatch_argv(prog_binding, "write")[1:]
            expected_arch_args = pc.build_dispatch_argv(arch_binding, "read-only")[1:]
            assert [c["args"] for c in calls].count(expected_prog_args) == 2
            assert [c["args"] for c in calls].count(expected_arch_args) == 1
            assert len(calls) == 3

            # 6. Verify checkpoint sequence in event stream and heartbeat
            env_mod = _load_module(
                "_state_envelope",
                SCRIPTS_DIR / "_state_envelope.py",
                extra_sys_path=SCRIPTS_DIR,
            )
            safe_slug = env_mod._sanitize_epic_slug("fpg_demo")
            events_path = repo / ".devtool" / "logs" / f"events_{safe_slug}.jsonl"
            cp_events = [
                ev.get("event")
                for ev in (
                    json.loads(line)
                    for line in events_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                )
                if ev.get("category") == "checkpoint"
            ]
            assert cp_events == [
                "gate2_tasks_locked",
                "subagent_returned",
                "subagent_returned",
                "subagent_returned",
                "wave_merged",
            ]
            hb_data = json.loads(
                (repo / ".devtool" / "state" / f"{safe_slug}.heartbeat.json").read_text(
                    encoding="utf-8"
                )
            )
            assert hb_data["checkpoint"]["event"] == "wave_merged"

            # 7. Verify dashboard scan_repo payload
            meta = ct.scan_repo(repo)
            assert meta.task_progress.total_tasks == 2
            assert meta.task_progress.done_tasks == 2
            assert meta.checkpoint is not None
            assert meta.checkpoint["event"] == "wave_merged"
            assert meta.is_human_action_required is False
            assert meta.action_blockers == []
            by_persona = {b["persona"]: b for b in meta.persona_bindings}
            assert by_persona["programmer"]["model_id"] == "gemini-4-hydrogen-high"
            assert (
                by_persona["ai_architect_reviewer"]["model_id"]
                == "gemini-4-argon-medium"
            )


def _dev_config_argv(cmd_line: str) -> list[str]:
    """Convert a fenced /d3nexus:dev-config or python3 scripts/dev_config.py line to argv."""
    if cmd_line.startswith("/d3nexus:dev-config"):
        return shlex.split(cmd_line[len("/d3nexus:dev-config") :].strip())
    return shlex.split(cmd_line[len("python3 scripts/dev_config.py") :].strip())


def _extract_quoted_run_external_review_commands(markdown_text: str) -> list[str]:
    """Extract quoted `run_external_review.py run` commands carrying options."""
    candidates: list[str] = []
    in_fence = False
    for raw_line in markdown_text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        candidates.extend(re.findall(r"`([^`\n]+)`", raw_line))
        if in_fence and "`" not in raw_line and stripped:
            candidates.append(stripped)

    extracted: list[str] = []
    pattern = re.compile(
        r"^(?:python3\s+\S*/)?run_external_review\.py\s+(run(?:\s+.*)?)$"
    )
    for snippet in candidates:
        match = pattern.match(snippet.strip())
        if match is None:
            continue
        cmd_tail = match.group(1).strip()
        tokens = shlex.split(cmd_tail)
        if any(tok.startswith("-") for tok in tokens[1:]):
            extracted.append(cmd_tail)
    return extracted


def _run_fpg_hp_16_cli_parse() -> None:
    """Parse every fenced command in both quick-guide languages against the real CLI."""
    with _isolated_host_env():
        dc = _load_module(
            "dev_config",
            SCRIPTS_DIR / "dev_config.py",
            extra_sys_path=SCRIPTS_DIR,
        )
        parser = dc._build_parser()

        en_path = REPO_ROOT / "docs" / "dev-config-quick-guide.en.md"
        vi_path = REPO_ROOT / "docs" / "dev-config-quick-guide.vi.md"
        assert en_path.is_file(), f"Missing English quick guide: {en_path}"
        assert vi_path.is_file(), f"Missing Vietnamese quick guide: {vi_path}"

        en_text = en_path.read_text(encoding="utf-8")
        vi_text = vi_path.read_text(encoding="utf-8")

        for label, text in (("en", en_text), ("vi", vi_text)):
            assert not EMAIL_RE.search(text), f"Email address found in {label} guide"
            assert not PASSWORD_RE.search(text), (
                f"Word 'password' found in {label} guide"
            )

        en_commands = _extract_fenced_commands(en_text)
        vi_commands = _extract_fenced_commands(vi_text)
        assert en_commands, (
            "Expected fenced CLI commands in dev-config-quick-guide.en.md"
        )
        assert en_commands == vi_commands, (
            "English and Vietnamese quick guides must keep the same ordered command list"
        )

        en_headings = re.findall(r"^#{1,6}\s+", en_text, flags=re.MULTILINE)
        vi_headings = re.findall(r"^#{1,6}\s+", vi_text, flags=re.MULTILINE)
        assert len(en_headings) == len(vi_headings), (
            f"Heading count differs: en={len(en_headings)} vs vi={len(vi_headings)}"
        )

        for cmd_line in en_commands:
            assert not PLACEHOLDER_RE.search(cmd_line), (
                f"Placeholder found in quick guide command: {cmd_line}"
            )
            argv = _dev_config_argv(cmd_line)
            try:
                args = parser.parse_args(argv)
            except SystemExit as exc:
                raise AssertionError(
                    f"Command failed real dev_config.py parser ({exc}): {cmd_line}"
                ) from exc
            assert args.provider is not None or args.command is not None, (
                f"Command parsed without subcommand or --provider: {cmd_line}"
            )

        required_subcommands = (
            "status",
            "models",
            "set",
            "preset",
            "reset",
            "low-quota",
            "checkpoint",
            "quota-check",
            "resolve",
            "profiles",
            "dispatch",
        )
        for sub in required_subcommands:
            assert re.search(rf"\b{re.escape(sub)}\b", en_text), (
                f"Quick guide missing subcommand {sub!r}"
            )
        for opt in ("--provider", "--model", "--effort", "--profile"):
            assert opt in en_text, f"Quick guide missing option {opt!r}"
        assert "/d3nexus:dev-config set programmer kiro-sonnet high" in en_commands
        assert (
            "/d3nexus:dev-config set programmer codex-gpt xhigh --scope project"
            in en_commands
        )


def _run_verify_registration_check() -> None:
    """Check every tests/test_fpg_*.py suite exists on disk and is registered once in verify.sh as pytest."""
    verify_text = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    suites = _parse_verify_suites(verify_text)

    counts: dict[str, int] = {}
    by_path: dict[str, tuple[str, str, int, bool]] = {}
    for sec, mode, path, prio, doc_only in suites:
        counts[path] = counts.get(path, 0) + 1
        by_path[path] = (sec, mode, prio, doc_only)

    disk_suites = sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / "tests").glob("test_fpg_*.py")
    )
    expected_paths = sorted(path for path, _ in EXPECTED_FPG_SUITES)
    assert disk_suites == expected_paths, (
        f"Unexpected test_fpg_* set on disk: {disk_suites} vs {expected_paths}"
    )

    for rel_path, expected_doc_only in EXPECTED_FPG_SUITES:
        assert (REPO_ROOT / rel_path).is_file(), f"Missing suite: {rel_path}"
        assert counts.get(rel_path, 0) == 1, (
            f"Suite {rel_path} registered {counts.get(rel_path, 0)} times in verify.sh"
        )
        sec, mode, _prio, doc_only = by_path[rel_path]
        assert sec == "11", f"Suite {rel_path} expected in section '11', got {sec!r}"
        assert mode == "pytest", (
            f"Suite {rel_path} expected mode 'pytest', got {mode!r}"
        )
        assert doc_only is expected_doc_only, (
            f"Suite {rel_path} expected affects_doc_only={expected_doc_only}, got {doc_only}"
        )


class TestFpgAcceptance_Integration(unittest.TestCase):
    """Integration acceptance suite proving real-runner FPG-HP-08 flow under pytest and unittest."""

    def test_fpg_hp_08_end_to_end_english_only_epic_with_persona_stubs(self) -> None:
        """[FPG-HP-08] [Tier C - Integration] End-to-end English-only epic flows from readiness to dashboard with persona stubs."""
        _run_fpg_hp_08_epic_flow()


def _assert_guide_profile_order(
    commands: Sequence[str],
    parser: Any,
    *,
    target_action: str,
    doc_name: str,
) -> None:
    """Enforce SE-16 ordering: remove/release/set --profile follow add; probe follows discover or add."""
    active_pool: set[str] = set()
    discovered_seen = False
    found = 0
    for cmd_line in commands:
        args = parser.parse_args(_dev_config_argv(cmd_line))
        cmd = getattr(args, "command", None)
        if cmd == "profiles":
            p_action = getattr(args, "profiles_action", None)
            p_name = getattr(args, "name", None)
            if p_action == "discover":
                discovered_seen = True
            elif p_action == "add" and p_name:
                active_pool.add(str(p_name))
            if target_action == "probe" and p_action == "probe" and p_name:
                found += 1
                assert discovered_seen or str(p_name) in active_pool, (
                    f"Command {cmd_line!r} runs 'profiles probe {p_name}' "
                    f"before 'profiles discover' or 'profiles add {p_name}' in {doc_name}"
                )
            elif (
                target_action in ("remove", "release")
                and p_action == target_action
                and p_name
            ):
                found += 1
                assert str(p_name) in active_pool, (
                    f"Command {cmd_line!r} runs 'profiles {target_action} {p_name}' "
                    f"before 'profiles add {p_name}' in {doc_name}"
                )
            if p_action == "remove" and p_name:
                active_pool.discard(str(p_name))
        elif cmd == "set" and target_action == "set_profile":
            set_profile = getattr(args, "set_profile", None)
            if set_profile and str(set_profile) != "auto":
                found += 1
                assert str(set_profile) in active_pool, (
                    f"Command {cmd_line!r} runs 'set ... --profile {set_profile}' "
                    f"before 'profiles add {set_profile}' in {doc_name}"
                )
    assert found > 0, (
        f"Expected at least one {target_action!r} profile command in {doc_name}"
    )


class TestFpgAcceptance_GuideAndRegistry(unittest.TestCase):
    """Guide CLI-parsing and verify.sh registration checks runnable under pytest and unittest."""

    def test_fpg_hp_16_quick_guide_commands_parse_with_the_real_cli(self) -> None:
        """[FPG-HP-16] [Tier A - Unit] The dev-config quick guide documents only commands the real CLI accepts and keeps both language variants in step."""
        _run_fpg_hp_16_cli_parse()

    def test_fpg_verify_sh_registers_all_fpg_suites(self) -> None:
        """Every tests/test_fpg_*.py suite exists on disk and is registered once in verify.sh as pytest."""
        _run_verify_registration_check()

    def test_dev_config_guide_profile_actions_follow_add(self) -> None:
        """Every fenced remove/release/set --profile follows add <name>, and probe <name> follows discover or add <name>."""
        en_path = REPO_ROOT / "docs" / "dev-config-quick-guide.en.md"
        en_commands = _extract_fenced_commands(en_path.read_text(encoding="utf-8"))
        with _isolated_host_env():
            dc = _load_module(
                "dev_config",
                SCRIPTS_DIR / "dev_config.py",
                extra_sys_path=SCRIPTS_DIR,
            )
            parser = dc._build_parser()
            for target_action in ("probe", "remove", "release", "set_profile"):
                with self.subTest(action=target_action):
                    _assert_guide_profile_order(
                        en_commands,
                        parser,
                        target_action=target_action,
                        doc_name=en_path.name,
                    )

    def test_docs_run_external_review_commands_carry_required_options(self) -> None:
        """Every quoted `run_external_review.py run` command with options in docs/*.en.md passes the real parser."""
        doc_paths = sorted((REPO_ROOT / "docs").glob("*.en.md"))
        cases: list[tuple[Path, str]] = []
        for doc_path in doc_paths:
            for cmd_tail in _extract_quoted_run_external_review_commands(
                doc_path.read_text(encoding="utf-8")
            ):
                cases.append((doc_path, cmd_tail))

        found = len(cases)
        assert found > 0, (
            "Expected at least one quoted 'run_external_review.py run ...' "
            "command with options in docs/*.en.md"
        )

        with _isolated_host_env():
            rer_mod = _load_module(
                "run_external_review",
                DEV_IMPL_SCRIPTS / "run_external_review.py",
                extra_sys_path=DEV_IMPL_SCRIPTS,
            )
            for doc_path, cmd_tail in cases:
                with self.subTest(doc=doc_path.name, command=cmd_tail):
                    argv = shlex.split(cmd_tail)
                    stderr_buf = io.StringIO()
                    with (
                        patch.object(rer_mod, "run", return_value=0) as mock_run,
                        contextlib.redirect_stderr(stderr_buf),
                    ):
                        try:
                            rc = rer_mod.main(argv)
                        except SystemExit as exc:
                            raise AssertionError(
                                f"Quoted command in {doc_path.name} failed real "
                                f"run_external_review.py parser ({exc}): "
                                f"{cmd_tail!r} | stderr={stderr_buf.getvalue().strip()!r}"
                            ) from exc
                    assert rc == 0, (
                        f"Quoted command in {doc_path.name} failed run validation "
                        f"(rc={rc}): {cmd_tail!r} | stderr={stderr_buf.getvalue().strip()!r}"
                    )
                    assert mock_run.called
                    parsed_args = mock_run.call_args.args[0]
                    assert getattr(parsed_args, "base", None), (
                        f"Missing --base on quoted command in {doc_path.name}: {cmd_tail!r}"
                    )


if __name__ == "__main__":
    unittest.main()
