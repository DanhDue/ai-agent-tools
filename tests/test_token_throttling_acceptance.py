"""End-to-end token-throttling acceptance and quantitative regression suite (Task 6)."""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
LIFECYCLE_SCRIPTS = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
RESUME_SCRIPT = REPO_ROOT / "scripts" / "resume_context.py"

for _script_dir in (str(DEV_IMPL_SCRIPTS), str(LIFECYCLE_SCRIPTS), str(QC_SCRIPTS)):
    if _script_dir not in sys.path:
        sys.path.insert(0, _script_dir)


def _load_module(name: str, file_path: Path) -> ModuleType:
    """Dynamically load a repository Python script by path."""
    spec = importlib.util.spec_from_file_location(name, file_path)
    assert spec is not None and spec.loader is not None, (
        f"Unable to load module from {file_path}"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _assert_byte_cap(
    path: Path | str, max_bytes: int, content: bytes | None = None
) -> int:
    """Fail loudly with actual vs limit byte counts when a UTF-8 byte ceiling is exceeded."""
    target = Path(path)
    raw = content if content is not None else target.read_bytes()
    actual = len(raw)
    assert actual <= max_bytes, (
        f"Byte ceiling exceeded for {path}: actual {actual} bytes > limit {max_bytes} bytes "
        f"(over by {actual - max_bytes} bytes)"
    )
    return actual


def _assert_word_cap(
    path: Path | str, max_words: int, content: str | None = None
) -> int:
    """Fail loudly with actual vs limit word counts when a word ceiling is exceeded."""
    target = Path(path)
    text = content if content is not None else target.read_text(encoding="utf-8")
    actual = len(text.split())
    assert actual <= max_words, (
        f"Word ceiling exceeded for {path}: actual {actual} words > limit {max_words} words "
        f"(over by {actual - max_words} words)"
    )
    return actual


def _git(cwd: Path, *args: str) -> str:
    """Execute a git command inside cwd and return stripped stdout."""
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
    """Initialize an isolated git repository on branch main."""
    _git(repo_dir, "init", "-q", "-b", "main")
    _git(repo_dir, "config", "user.email", "tto@example.com")
    _git(repo_dir, "config", "user.name", "TTO Acceptance")


def _build_env_with_bin(
    bin_dir: Path, extra: dict[str, str] | None = None
) -> dict[str, str]:
    """Return process environment with fake CLI bin_dir prepended to PATH."""
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env.get('PATH', '')}"
    if extra:
        env.update(extra)
    return env


def _parse_verify_suites(verify_text: str) -> list[tuple[str, str, str, int, bool]]:
    """Extract and parse the SUITES list literal from scripts/verify.sh."""
    match = re.search(
        r"^SUITES\s*=\s*(\[.*?\n\])", verify_text, flags=re.MULTILINE | re.DOTALL
    )
    assert match is not None, (
        "Could not locate SUITES = [...] list in scripts/verify.sh"
    )
    parsed = ast.literal_eval(match.group(1))
    assert isinstance(parsed, list), (
        "SUITES in scripts/verify.sh must evaluate to a list"
    )
    return [
        (str(item[0]), str(item[1]), str(item[2]), int(item[3]), bool(item[4]))
        for item in parsed
    ]


def _setup_mini_kit_fixture(kit: Path) -> None:
    """Populate a minimal valid agent-kit checkout for isolated verify.sh --quiet/--full checks."""
    for sub in (
        "scripts",
        "skills/demo",
        "rules",
        "hooks",
        ".claude-plugin",
        ".codex-plugin",
        ".agents/plugins",
    ):
        (kit / sub).mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / "scripts" / "verify.sh", kit / "scripts" / "verify.sh")
    (kit / "scripts" / "check_source_fidelity.py").write_text(
        "import sys; sys.exit(0)\n", encoding="utf-8"
    )
    (kit / "hooks" / "session-start").write_text(
        "#!/usr/bin/env bash\nread -r -t 1 input || true\n"
        'if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] || printf \'%s\' "$input" | grep -q \'"invocationNum":0\'; then\n'
        '  echo \'{"hookSpecificOutput":{"hookEventName":"SessionStart"}}\'\n'
        "else\n  echo '{}'\nfi\n",
        encoding="utf-8",
    )
    manifest = {
        "name": "d3nexus",
        "version": "1.0.0",
        "skills": "./skills/",
        "interface": {
            "displayName": "D3Nexus",
            "shortDescription": "S",
            "longDescription": "L",
            "developerName": "D",
            "category": "Developer Tools",
        },
    }
    for rel in (
        "plugin.json",
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
    ):
        (kit / rel).write_text(json.dumps(manifest), encoding="utf-8")
    market = {
        "name": "danhdue-agent-tools",
        "plugins": [
            {
                "name": "d3nexus",
                "version": "1.0.0",
                "source": {"source": "local", "path": "./"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Developer Tools",
            }
        ],
    }
    (kit / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps(market), encoding="utf-8"
    )
    (kit / ".agents" / "plugins" / "marketplace.json").write_text(
        json.dumps(market), encoding="utf-8"
    )
    (kit / "CHANGELOG.md").write_text(
        "## 1.0.0 — 2026-11-13\n\nInitial\n", encoding="utf-8"
    )
    (kit / "README.md").write_text("# Readme\n", encoding="utf-8")
    (kit / "CLAUDE.md").write_text("# Claude\n", encoding="utf-8")
    (kit / "rules" / "r.md").write_text(
        "---\ntrigger: always_on\n---\n\nRule\n", encoding="utf-8"
    )
    (kit / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo skill\n---\n\n# Demo\n",
        encoding="utf-8",
    )
    (kit / "scripts" / "test_lifecycle_signals.py").write_text(
        "import unittest\n\nclass T(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    _init_git_repo(kit)
    _git(kit, "add", "-A")
    _git(kit, "commit", "-q", "-m", "Mini kit fixture")


def test_tto_hp_08_end_to_end_pipeline() -> None:
    """[TTO-HP-08] End-to-end token-throttling pipeline enforces compact prompts, review isolation, and programmer config."""
    rer: Any = _load_module(
        "run_external_review", DEV_IMPL_SCRIPTS / "run_external_review.py"
    )
    lc_mod: Any = _load_module(
        "lifecycle_runner", LIFECYCLE_SCRIPTS / "lifecycle_runner.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        main_repo = tmp / "main_repo"
        bin_dir = tmp / "bin"
        prompt_dir = tmp / "review_prompts"
        agy_dir = tmp / "agy_records"
        for d in (main_repo, bin_dir, prompt_dir, agy_dir):
            d.mkdir(parents=True, exist_ok=True)

        _init_git_repo(main_repo)
        (main_repo / ".gitignore").write_text("build/\n.worktrees/\n", encoding="utf-8")
        (main_repo / "README.md").write_text("# Acceptance Demo\n", encoding="utf-8")
        (main_repo / "scripts").mkdir(parents=True, exist_ok=True)
        verify_stub = main_repo / "scripts" / "verify.sh"
        verify_stub.write_text(
            "#!/usr/bin/env bash\necho 'PASS — safe to publish'\nexit 0\n",
            encoding="utf-8",
        )
        verify_stub.chmod(0o755)

        # >200-line source module with a top-of-file secret marker far from line 110 edit
        src_lines = [f"line_{i:03d} = {i}" for i in range(1, 211)]
        src_lines[4] = (
            'SOURCE_INLINING_FORBIDDEN_MARKER = "must_not_leak_in_u5_or_worker_prompt"'
        )
        (main_repo / "src").mkdir(parents=True, exist_ok=True)
        (main_repo / "src" / "feature.py").write_text(
            "\n".join(src_lines) + "\n", encoding="utf-8"
        )

        (main_repo / "tests").mkdir(parents=True, exist_ok=True)
        (main_repo / "tests" / "test_feature.py").write_text(
            "from pathlib import Path\n\n"
            "class TestDemo_Integration:\n"
            "    def test_demo_hp_01(self) -> None:\n"
            "        src = Path('src/feature.py').read_text(encoding='utf-8')\n"
            "        assert 'updated_by_fake_agy' in src\n",
            encoding="utf-8",
        )

        # Quality registry manifests for compact Gate 4 verification
        agents_dir = main_repo / ".agents" / "quality"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "check_quality.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "providers": [
                        {
                            "id": "python-core",
                            "skill": "d3nexus:python-quality-check",
                            "required": True,
                            "profiles": ["pr", "epic"],
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (agents_dir / "python-quality.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "capabilities": {
                        "lint": ["ruff", "check", "src/feature.py"],
                        "type_check": ["mypy", "src/feature.py"],
                        "test": [
                            sys.executable,
                            "-m",
                            "pytest",
                            "-q",
                            "--tb=short",
                            "--maxfail=3",
                            "tests/test_feature.py",
                        ],
                        "architecture": ["bash", "scripts/verify.sh"],
                    },
                    "profiles": {
                        "pr": ["lint", "test"],
                        "epic": ["lint", "type_check", "test", "architecture"],
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        # Legacy programmer model + "extra" effort alias must upgrade cleanly to gemini-4-hydrogen-xhigh / xhigh
        (main_repo / ".devtool").mkdir(parents=True, exist_ok=True)
        (main_repo / ".devtool" / "review_config.json").write_text(
            json.dumps(
                {
                    "last_used_provider": "codex",
                    "providers": {
                        "codex": {"model": "gpt-6.1-sol", "thinking_level": "high"},
                        "programmer": {
                            "cli": "agy",
                            "model": "gemini-3.8-flash-high",
                            "thinking_level": "extra",
                        },
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        _git(main_repo, "add", "-A")
        _git(main_repo, "commit", "-q", "-m", "[DEMO] Base repo")
        base_sha = _git(main_repo, "rev-parse", "HEAD")

        # Bootstrap epic docs (English SSOT + drifted VI companion + missing bdd_scenarios.vi.md)
        epic_dir = main_repo / ".devtool" / "epic" / "demo_epic"
        features_dir = main_repo / ".devtool" / "features"
        epic_dir.mkdir(parents=True, exist_ok=True)
        features_dir.mkdir(parents=True, exist_ok=True)

        (epic_dir / "2026-11-13-demo-epic-design.en.md").write_text(
            "# Demo Epic Design\n\n## Table of Contents\n\n- [Overview](#overview)\n\n"
            "## Overview\n\nApproved specification.\n",
            encoding="utf-8",
        )
        (epic_dir / "2026-11-13-demo-epic-design.vi.md").write_text(
            "# Demo Epic Design VI\n\n## Muc luc\n\n## Stale VI section\n\nDrifted prose.\n",
            encoding="utf-8",
        )
        (epic_dir / "demo_epic.en.md").write_text(
            "# Demo Epic HLD\n\n## Table of Contents\n\n"
            "- [Integration Test Plan](#integration-test-plan)\n"
            "- [Verification Environment](#verification-environment)\n"
            "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n\n"
            "## Integration Test Plan\n\n"
            "Protected paths: README.md\n\n"
            "Integration test roots: tests\n\n"
            "Integration results: python3 -m pytest -q --tb=short --maxfail=3 "
            "--junitxml=build/demo.xml tests/test_feature.py -> build/demo.xml\n\n"
            "## Verification Environment\n\n"
            "Runs inside isolated temp repository.\n\n"
            "## Kanban Tasks Breakdown\n\n"
            "1. [Task 1](task_01_feature.md)\n",
            encoding="utf-8",
        )
        (epic_dir / "demo_epic.vi.md").write_text(
            "# Demo Epic HLD VI\n\n## Muc luc\n\n- [Ke hoach](#ke-hoach)\n\n"
            "## Ke hoach\n\nBan nhap cu bi troi.\n",
            encoding="utf-8",
        )
        (epic_dir / "bdd_scenarios.en.md").write_text(
            "# Demo BDD Scenarios\n\n## Table of Contents\n\n- [Scenarios](#scenarios)\n\n"
            "## Scenarios\n\n```gherkin\n"
            "Scenario: [DEMO-HP-01] [Tier C - Integration] Feature edit at line 110\n"
            "  Given feature.py exists\n"
            "  When task_01_feature updates line 110\n"
            "  Then pytest passes\n"
            "```\n",
            encoding="utf-8",
        )
        task_body = (
            '---\nid: "task_01_feature"\nstatus: "todo"\npriority: "high"\nepic: "demo_epic"\n---\n\n'
            "# Task 1: Update Feature Line 110\n\n"
            "Epic: [demo_epic](demo_epic.en.md)\n\n"
            "TASK_BODY_PROSE_DO_NOT_INLINE_MARKER\n\n"
            "## Dependencies\n\n- None\n\n"
            "## Files\n\nAllowed files:\n- `src/feature.py`\n\n"
            "## Impact Analysis & Blast Radius\n\n"
            "- `src/feature.py` (L100-L130)\n\n"
            "Covers: DEMO-HP-01\n\n"
            "## Verification\n\n"
            "| ID | Phase | Command | Expect | Needs |\n"
            "|----|-------|---------|--------|-------|\n"
            "| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_feature.py` | exit 1 | — |\n"
            "| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_feature.py` | exit 0 | — |\n"
            "| V3 | TIER-B | `ruff check src/feature.py` | exit 0 | — |\n"
            "| V4 | TIER-B | `mypy src/feature.py` | exit 0 | — |\n"
            "| V5 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 --junitxml=build/demo.xml tests/test_feature.py` | exit 0; results build/demo.xml | — |\n\n"
            "## Stop and Report If\n\n- Unexpected error\n\n"
            "## Decisions Already Made\n\n- Edit only line 110 in src/feature.py.\n\n"
            "## Definition of Done\n\n- Feature test and static checks pass (V2, V3, V4, V5).\n"
        )
        (epic_dir / "task_01_feature.md").write_text(task_body, encoding="utf-8")
        (features_dir / "task_01_feature.md").write_text(
            task_body.replace(
                "](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)"
            ),
            encoding="utf-8",
        )

        _git(main_repo, "add", "-A")
        _git(main_repo, "commit", "-q", "-m", "[DEMO] Add epic artifacts")

        # Create isolated epic worktree matching production Layout (.worktrees/demo_epic)
        epic_wt = main_repo / ".worktrees" / "demo_epic"
        _git(
            main_repo,
            "worktree",
            "add",
            "-q",
            "-b",
            "epic/demo_epic",
            str(epic_wt),
            "HEAD",
        )

        # Record RED baseline evidence inside epic_wt and commit it cleanly
        red_proc = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "run_task_checks.py"),
                "red",
                ".devtool/epic/demo_epic/task_01_feature.md",
            ],
            cwd=epic_wt,
            capture_output=True,
            text=True,
            check=False,
        )
        assert red_proc.returncode == 0, red_proc.stdout + red_proc.stderr
        _git(epic_wt, "add", "-A")
        _git(epic_wt, "commit", "-q", "-m", "[DEMO] Record RED evidence")

        # Fake codex + agy CLIs on PATH
        fake_codex = bin_dir / "codex"
        fake_codex.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "${1:-}" = "--version" ]; then echo "codex 1.0"; exit 0; fi\n'
            'count=0; [ -f "$FAKE_COUNT_FILE" ] && count=$(cat "$FAKE_COUNT_FILE")\n'
            "count=$((count + 1))\n"
            'echo "$count" > "$FAKE_COUNT_FILE"\n'
            'cat > "${FAKE_PROMPT_DIR}/prompt_${count}.txt"\n'
            'for i in $(seq 1 40); do echo "review bulk prose line ${i}"; done\n'
            'echo "Verdict: PASS"\n'
            'echo "review noisy stderr" >&2\n',
            encoding="utf-8",
        )
        fake_codex.chmod(0o755)

        fake_agy = bin_dir / "agy"
        fake_agy.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'if [ "${1:-}" = "models" ]; then\n'
            '  echo "gemini-4-hydrogen-xhigh  Gemini 4 Hydrogen (XHigh)"\n'
            "  exit 0\n"
            "fi\n"
            'printf "%s\\n" "$@" > "${FAKE_AGY_DIR}/argv.txt"\n'
            'cat > "${FAKE_AGY_DIR}/prompt.txt"\n'
            f'"{sys.executable}" -c \'\n'
            "from pathlib import Path\n"
            'p = Path("src/feature.py")\n'
            'lines = p.read_text(encoding="utf-8").splitlines()\n'
            'lines[109] = "line_110 = 999  # updated_by_fake_agy"\n'
            'p.write_text("\\n".join(lines) + "\\n", encoding="utf-8")\n'
            "'\n"
            f'"{sys.executable}" "{DEV_IMPL_SCRIPTS / "run_task_checks.py"}" verify '
            ".devtool/epic/demo_epic/task_01_feature.md >/dev/null\n"
            'echo "Modified: src/feature.py"\n'
            'echo "Tests: 1 passed"\n',
            encoding="utf-8",
        )
        fake_agy.chmod(0o755)

        count_file = tmp / "codex_count.txt"
        env = _build_env_with_bin(
            bin_dir,
            {
                "FAKE_COUNT_FILE": str(count_file),
                "FAKE_PROMPT_DIR": str(prompt_dir),
                "FAKE_AGY_DIR": str(agy_dir),
            },
        )

        # 1. Option A Readiness passes despite drifted .vi.md and absent bdd_scenarios.vi.md
        ready_proc = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "check_epic_readiness.py"),
                "demo_epic",
            ],
            cwd=epic_wt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert ready_proc.returncode == 0, ready_proc.stdout + ready_proc.stderr
        assert "R1 PASS" in ready_proc.stdout

        # 2. Principal Review via fake codex writes isolated raw log outside markdown
        pr_proc = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "run_external_review.py"),
                "run",
                "--kind",
                "principal",
                "--epic-dir",
                "demo_epic",
                "--base",
                base_sha,
                "--cli",
                "codex",
            ],
            cwd=epic_wt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert pr_proc.returncode == 0, pr_proc.stdout + pr_proc.stderr
        pr_sha7 = _git(epic_wt, "rev-parse", "HEAD")[:7]
        pr_raw_log = (
            epic_wt
            / "build"
            / "reviews"
            / f"demo_epic_principal_round1_{pr_sha7}.raw.log"
        )
        assert pr_raw_log.is_file()
        assert "review bulk prose line 40" in pr_raw_log.read_text(encoding="utf-8")
        pr_md = (
            epic_wt / ".devtool" / "epic" / "demo_epic" / "principal_review.md"
        ).read_text(encoding="utf-8")
        assert f"build/reviews/demo_epic_principal_round1_{pr_sha7}.raw.log" in pr_md
        assert "review bulk prose line 1\n" not in pr_md
        prompt1 = (prompt_dir / "prompt_1.txt").read_text(encoding="utf-8")
        assert ".vi.md" not in prompt1.split("## Artefacts", 1)[1]

        # Seed a Principal finding and package handoff.md before worker dispatch
        pr_md_with_finding = pr_md.replace(
            "|---|----------|----------|---------|----------|\n",
            "|---|----------|----------|---------|----------|\n"
            "| 1 | Important | `src/feature.py:110` | Verify line 110 bounds | fixed in deadbeef |\n",
        )
        (
            epic_wt / ".devtool" / "epic" / "demo_epic" / "principal_review.md"
        ).write_text(
            pr_md_with_finding,
            encoding="utf-8",
        )
        pkg_proc = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "package_epic.py"),
                "demo_epic",
                "--base-branch",
                "main",
            ],
            cwd=epic_wt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert pkg_proc.returncode == 0, pkg_proc.stdout + pkg_proc.stderr
        handoff_text = (
            epic_wt / ".devtool" / "epic" / "demo_epic" / "handoff.md"
        ).read_text(encoding="utf-8")
        assert ".vi.md" not in handoff_text
        _git(epic_wt, "add", "-A")
        _git(
            epic_wt,
            "commit",
            "-q",
            "-m",
            "[DEMO] Package epic and record principal review",
        )

        # 3. Worker dispatch via LifecycleRunner + fake agy CLI (real subprocess inside pool slot)
        runner = lc_mod.LifecycleRunner(root=epic_wt, epic_slug="demo_epic")
        assert (
            runner.config.resolve_programmer_model(epic_wt) == "gemini-4-hydrogen-xhigh"
        )
        assert runner.config.resolve_programmer_effort(epic_wt) == "xhigh"

        clean_env = {k: v for k, v in env.items()}
        with patch.dict(os.environ, clean_env, clear=True):
            ok_probe, probe_msg = runner.dispatcher.probe_model(
                "agy", "gemini-4-hydrogen-xhigh"
            )
            assert ok_probe, probe_msg
            ok_impl = runner.step_implementation()
        assert ok_impl, f"step_implementation failed: {runner.state.last_error}"

        # Mark task done cleanly and commit for code review
        (epic_wt / ".devtool" / "epic" / "demo_epic" / "task_01_feature.md").write_text(
            task_body.replace('status: "todo"', 'status: "done"'),
            encoding="utf-8",
        )
        (epic_wt / ".devtool" / "features" / "task_01_feature.md").write_text(
            task_body.replace('status: "todo"', 'status: "done"').replace(
                "](demo_epic.en.md)", "](../epic/demo_epic/demo_epic.en.md)"
            ),
            encoding="utf-8",
        )
        _git(epic_wt, "add", "-A")
        _git(epic_wt, "commit", "-q", "-m", "[DEMO] Sync task_01_feature done")

        agy_argv = (agy_dir / "argv.txt").read_text(encoding="utf-8").splitlines()
        assert (
            "--model" in agy_argv
            and agy_argv[agy_argv.index("--model") + 1] == "gemini-4-hydrogen-xhigh"
        )
        assert (
            "--effort" in agy_argv
            and agy_argv[agy_argv.index("--effort") + 1] == "xhigh"
        )

        worker_prompt = (agy_dir / "prompt.txt").read_text(encoding="utf-8")
        assert "task_01_feature" in worker_prompt
        assert "src/feature.py (L100-L130)" in worker_prompt
        assert "do not invoke d3nexus:task-observer" in worker_prompt.lower()
        assert "Zero-Fluff" in worker_prompt
        assert "TASK_BODY_PROSE_DO_NOT_INLINE_MARKER" not in worker_prompt
        assert "SOURCE_INLINING_FORBIDDEN_MARKER" not in worker_prompt

        # 4. Cross-model code review respects -U5 diff budget and offloads raw output
        code_proc = subprocess.run(
            [
                sys.executable,
                str(DEV_IMPL_SCRIPTS / "run_external_review.py"),
                "run",
                "--kind",
                "code",
                "--epic-dir",
                "demo_epic",
                "--base",
                base_sha,
                "--cli",
                "codex",
            ],
            cwd=epic_wt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert code_proc.returncode == 0, code_proc.stdout + code_proc.stderr
        code_sha7 = _git(epic_wt, "rev-parse", "HEAD")[:7]
        code_raw_log = (
            epic_wt / "build" / "reviews" / f"demo_epic_code_round1_{code_sha7}.raw.log"
        )
        assert code_raw_log.is_file()
        assert code_raw_log != pr_raw_log

        prompt2 = (prompt_dir / "prompt_2.txt").read_text(encoding="utf-8")
        assert "line_105 = 105" in prompt2
        assert "line_115 = 115" in prompt2
        assert "SOURCE_INLINING_FORBIDDEN_MARKER" not in prompt2
        assert "PASS: audit_epic.py" in prompt2

        # 5. Compact Gate 4 emits single-line GATE_PASS statuses upon green verification
        gate4_proc = subprocess.run(
            [
                sys.executable,
                str(QC_SCRIPTS / "verify_polyglot_registry.py"),
                str(epic_wt / ".agents" / "quality" / "check_quality.json"),
                "--profile",
                "epic",
                "--execute",
                "--compact",
            ],
            cwd=epic_wt,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert gate4_proc.returncode == 0, gate4_proc.stdout + gate4_proc.stderr
        assert "GATE_PASS: python-core:lint" in gate4_proc.stdout
        assert "GATE_PASS: python-core:type_check" in gate4_proc.stdout
        assert "GATE_PASS: python-core:test" in gate4_proc.stdout
        assert "GATE_PASS: python-core:architecture" in gate4_proc.stdout
        assert '"provider_id"' not in gate4_proc.stdout
        assert (epic_wt / "build" / "quality" / "python-core" / "lint.log").is_file()
        assert (
            epic_wt / "build" / "quality" / "python-core" / "type_check.log"
        ).is_file()
        assert (epic_wt / "build" / "quality" / "python-core" / "test.log").is_file()
        assert (
            epic_wt / "build" / "quality" / "python-core" / "architecture.log"
        ).is_file()

        # 6. Executive summary renders real candidate SHA and parsed findings
        runner.state.principal_round = 1
        runner.state.cross_model_round = 1
        runner.state.last_commit_sha = code_sha7
        report = runner.render_final_executive_report()
        assert code_sha7 in report
        assert "task_01_feature" in report
        assert "Verify line 110 bounds" in report
        assert "Gate 4 Status" in report and "PASS" in report

        # Confirm real module load check passed too
        assert hasattr(rer, "MAX_DIFF_BYTES")


def test_tto_ec_06_verify_suite_registration() -> None:
    """[TTO-EC-06] verify.sh registers all epic suites, defines §1–§17, and prevents recursive nesting."""
    verify_path = REPO_ROOT / "scripts" / "verify.sh"
    verify_text = verify_path.read_text(encoding="utf-8")

    # Anti-recursion guard MUST be exported inside scripts/verify.sh
    assert "export VERIFY_SH_ACTIVE=1" in verify_text, (
        "scripts/verify.sh must export VERIFY_SH_ACTIVE=1 to prevent recursive test loops"
    )

    # Sections §1 through §10 must be wired via run_sec
    for sec_num in range(1, 11):
        assert f'run_sec "== {sec_num}.' in verify_text, (
            f"scripts/verify.sh missing section §{sec_num} run_sec invocation"
        )
    assert 'run_sec "== 5b.' in verify_text, "scripts/verify.sh missing section §5b"

    # Sections §11 through §17 and all 6 epic/runner suites must be registered in SUITES
    suites = _parse_verify_suites(verify_text)
    suite_map: dict[str, tuple[str, str, int, bool]] = {
        path: (sec, mode, prio, doc_only) for sec, mode, path, prio, doc_only in suites
    }
    registered_sections = {sec for sec, _mode, _path, _prio, _doc in suites}
    for sec_id in ("11", "12", "13", "14", "15", "16", "17"):
        assert sec_id in registered_sections, (
            f"scripts/verify.sh SUITES missing section §{sec_id}"
        )

    required_suites = {
        "tests/test_tto_external_review.py": "pytest",
        "tests/test_polyglot_gate4.py": "pytest",
        "tests/test_tto_bilingual_and_surgical.py": "pytest",
        "tests/test_lifecycle_runner.py": None,
        "tests/test_tto_docs_and_slimming.py": "pytest",
        "tests/test_token_throttling_acceptance.py": "pytest",
    }
    for rel_path, expected_mode in required_suites.items():
        assert (REPO_ROOT / rel_path).is_file(), (
            f"Required test suite missing on disk: {rel_path}"
        )
        assert rel_path in suite_map, (
            f"scripts/verify.sh SUITES missing required suite: {rel_path}"
        )
        if expected_mode is not None:
            actual_mode = suite_map[rel_path][1]
            assert actual_mode == expected_mode, (
                f"Expected mode {expected_mode!r} for {rel_path} in SUITES, got {actual_mode!r}"
            )

    # Verify --quiet vs --full output behavior on an isolated mini-kit fixture (safe even under VERIFY_SH_ACTIVE=1)
    with tempfile.TemporaryDirectory() as tmpdir:
        mini_kit = Path(tmpdir) / "mini_kit"
        _setup_mini_kit_fixture(mini_kit)

        q_mini = subprocess.run(
            ["bash", "scripts/verify.sh", "--quiet"],
            cwd=mini_kit,
            capture_output=True,
            text=True,
            check=False,
        )
        assert q_mini.returncode == 0, q_mini.stdout + q_mini.stderr
        assert "PASS — safe to publish" in q_mini.stdout
        assert "  ok   == 1." in q_mini.stdout
        assert "  ok   plugin.json" not in q_mini.stdout

        f_mini = subprocess.run(
            ["bash", "scripts/verify.sh", "--full"],
            cwd=mini_kit,
            capture_output=True,
            text=True,
            check=False,
        )
        assert f_mini.returncode == 0, f_mini.stdout + f_mini.stderr
        assert "PASS — safe to publish" in f_mini.stdout
        assert "  ok   plugin.json" in f_mini.stdout
        assert "  ok   [§11] scripts/test_lifecycle_signals.py" in f_mini.stdout

    # Only run live repo verify.sh --quiet when NOT already executing inside verify.sh
    if os.environ.get("VERIFY_SH_ACTIVE") != "1":
        live_proc = subprocess.run(
            ["bash", str(verify_path), "--quiet"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert live_proc.returncode == 0, live_proc.stdout + live_proc.stderr
        assert "PASS — safe to publish" in live_proc.stdout
        for sec_num in range(1, 11):
            assert f"  ok   == {sec_num}." in live_proc.stdout, (
                f"Expected single-line ok summary for §{sec_num} in verify.sh --quiet output"
            )
        assert "  ok   == 11–16." in live_proc.stdout
        assert "  ok   plugin.json" not in live_proc.stdout


def test_tto_ar_02_isolated_context_and_round_logs() -> None:
    """[TTO-AR-02] Per-task clean context and per-round raw logs prevent cross-session transcript contamination."""
    rer: Any = _load_module(
        "run_external_review", DEV_IMPL_SCRIPTS / "run_external_review.py"
    )
    lc_mod: Any = _load_module(
        "lifecycle_runner", LIFECYCLE_SCRIPTS / "lifecycle_runner.py"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "repo"
        repo.mkdir(parents=True, exist_ok=True)
        _init_git_repo(repo)
        (repo / ".gitignore").write_text("build/\n.worktrees/\n", encoding="utf-8")
        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "one.py").write_text("ONE = 1\n", encoding="utf-8")
        (repo / "src" / "two.py").write_text("TWO = 1\n", encoding="utf-8")

        epic_dir = repo / ".devtool" / "epic" / "demo_epic"
        features_dir = repo / ".devtool" / "features"
        epic_dir.mkdir(parents=True, exist_ok=True)
        features_dir.mkdir(parents=True, exist_ok=True)
        (epic_dir / "demo_epic.en.md").write_text("# Demo HLD\n", encoding="utf-8")
        (epic_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")

        task1_md = (
            "---\nid: task_01_first\nepic: demo_epic\nstatus: todo\npriority: high\n---\n\n"
            "# Task 1\n\nUNIQUE_TASK1_BODY_DO_NOT_LEAK\n\n"
            "## Dependencies\n- None\n\n"
            "## Files\nAllowed files:\n- `src/one.py`\n\n"
            "## Impact Analysis & Blast Radius\n- `src/one.py` (L1-L10)\n"
        )
        task2_md = (
            "---\nid: task_02_second\nepic: demo_epic\nstatus: todo\npriority: high\n---\n\n"
            "# Task 2\n\nTask 2 body.\n\n"
            "## Dependencies\n- Blocked by: [task_01_first](task_01_first.md)\n\n"
            "## Files\nAllowed files:\n- `src/two.py`\n\n"
            "## Impact Analysis & Blast Radius\n- `src/two.py` (L1-L10)\n"
        )
        (features_dir / "task_01_first.md").write_text(task1_md, encoding="utf-8")
        (features_dir / "task_02_second.md").write_text(task2_md, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "[DEMO] Init AR-02 repo")
        sha1 = _git(repo, "rev-parse", "HEAD")

        (repo / "src" / "one.py").write_text("ONE = 2\n", encoding="utf-8")
        _git(repo, "add", "src/one.py")
        _git(repo, "commit", "-q", "-m", "[DEMO] Second commit")
        sha2 = _git(repo, "rev-parse", "HEAD")

        # 1. Non-colliding raw logs across principal vs code and Round 1 vs Round 2
        rounds = [
            (
                "principal",
                1,
                sha1,
                "PR_R1_TRANSCRIPT_ONLY\nVerdict: CHANGES REQUIRED\n--- stderr ---\nPR_R1_STDERR_ONLY\n",
            ),
            (
                "principal",
                2,
                sha2,
                "PR_R2_TRANSCRIPT_ONLY\nVerdict: PASS\n--- stderr ---\nPR_R2_STDERR_ONLY\n",
            ),
            (
                "code",
                1,
                sha1,
                "CODE_R1_TRANSCRIPT_ONLY\nVerdict: CHANGES REQUIRED\n--- stderr ---\nCODE_R1_STDERR_ONLY\n",
            ),
            (
                "code",
                2,
                sha2,
                "CODE_R2_TRANSCRIPT_ONLY\nVerdict: PASS\n--- stderr ---\nCODE_R2_STDERR_ONLY\n",
            ),
        ]
        rendered_by_kind: dict[str, list[str]] = {"principal": [], "code": []}
        log_paths: list[tuple[Path, str, str]] = []
        for kind, rnum, sha, raw_out in rounds:
            meta = {
                "SHA": sha,
                "CLI": "codex",
                "Kind": kind,
                "Verdict": "PASS" if rnum == 2 else "CHANGES REQUIRED",
            }
            section = rer.render_round(
                rnum,
                meta,
                [],
                raw_out,
                root=repo,
                epic_dir="demo_epic",
                kind=kind,
                sha=sha,
            )
            rendered_by_kind[kind].append(section)
            expected_path = (
                repo
                / "build"
                / "reviews"
                / f"demo_epic_{kind}_round{rnum}_{sha[:7]}.raw.log"
            )
            assert expected_path.is_file(), f"Missing expected raw log: {expected_path}"
            log_paths.append(
                (
                    expected_path,
                    f"{kind.upper()}_R{rnum}_TRANSCRIPT_ONLY".replace(
                        "PRINCIPAL", "PR"
                    ),
                    f"{kind.upper()}_R{rnum}_STDERR_ONLY".replace("PRINCIPAL", "PR"),
                )
            )

        # Every raw log path is unique and strictly isolated from other rounds/kinds
        assert len({p for p, _, _ in log_paths}) == 4
        all_markers = [(m_out, m_err) for _, m_out, m_err in log_paths]
        for log_path, own_out, own_err in log_paths:
            body = log_path.read_text(encoding="utf-8")
            assert own_out in body and own_err in body
            for other_out, other_err in all_markers:
                if other_out != own_out:
                    assert other_out not in body, f"{other_out} leaked into {log_path}"
                if other_err != own_err:
                    assert other_err not in body, f"{other_err} leaked into {log_path}"

        # Markdown round sections reference raw logs without leaking full transcripts
        for kind, sections in rendered_by_kind.items():
            md_doc = "\n".join(sections)
            assert f"build/reviews/demo_epic_{kind}_round1_{sha1[:7]}.raw.log" in md_doc
            assert f"build/reviews/demo_epic_{kind}_round2_{sha2[:7]}.raw.log" in md_doc
            for m_out, m_err in all_markers:
                assert m_out not in md_doc
                assert m_err not in md_doc

        # 2. Sequential task dispatch passes zero accumulated Task N stdout/stderr to Task N+1
        epic_wt = repo / ".worktrees" / "demo_epic"
        _git(
            repo, "worktree", "add", "-q", "-b", "epic/demo_epic", str(epic_wt), "HEAD"
        )
        runner = lc_mod.LifecycleRunner(root=epic_wt, epic_slug="demo_epic")
        recorded_prompts: dict[str, str] = {}

        def fake_dispatch(
            self_disp: Any, cli: str, args: list[str], prompt: str
        ) -> tuple[int, str, str]:
            wt = self_disp.worktree_dir
            assert wt is not None
            if "task_01_first" in prompt:
                recorded_prompts["task_01_first"] = prompt
                (wt / "src" / "one.py").write_text("ONE = 3\n", encoding="utf-8")
                return (
                    0,
                    "TASK1_ACCUMULATED_STDOUT_LEAK\n",
                    "TASK1_ACCUMULATED_STDERR_LEAK\n",
                )
            recorded_prompts["task_02_second"] = prompt
            (wt / "src" / "two.py").write_text("TWO = 2\n", encoding="utf-8")
            return 0, "TASK2_DONE\n", ""

        with patch.object(
            lc_mod.ModelDispatcher, "dispatch", autospec=True, side_effect=fake_dispatch
        ):
            assert runner.step_implementation()

        assert (
            "task_01_first" in recorded_prompts and "task_02_second" in recorded_prompts
        )
        task1_log = (
            epic_wt / ".devtool" / "logs" / "tasks" / "task_01_first.log"
        ).read_text(encoding="utf-8")
        assert "TASK1_ACCUMULATED_STDOUT_LEAK" in task1_log
        assert "TASK1_ACCUMULATED_STDERR_LEAK" in task1_log

        prompt_task2 = recorded_prompts["task_02_second"]
        assert "task_02_second" in prompt_task2
        assert "src/two.py (L1-L10)" in prompt_task2
        assert "TASK1_ACCUMULATED_STDOUT_LEAK" not in prompt_task2
        assert "TASK1_ACCUMULATED_STDERR_LEAK" not in prompt_task2
        assert "UNIQUE_TASK1_BODY_DO_NOT_LEAK" not in prompt_task2


def test_tto_fr_04_quantitative_byte_caps_and_fail_loud() -> None:
    """[TTO-FR-04] Quantitative regression assertions enforce caps and fail loudly with concrete byte diagnostics."""
    rer: Any = _load_module(
        "run_external_review", DEV_IMPL_SCRIPTS / "run_external_review.py"
    )
    lc_mod: Any = _load_module(
        "lifecycle_runner", LIFECYCLE_SCRIPTS / "lifecycle_runner.py"
    )

    # 1. Fail-loud behavior check: exceeding any ceiling produces concrete actual-vs-limit diagnostics
    oversized_bytes = b"x" * 8250
    try:
        _assert_byte_cap("rules/CRITICAL_RULES.md", 8192, content=oversized_bytes)
        raise AssertionError("Expected _assert_byte_cap to fail when 8250 > 8192")
    except AssertionError as exc:
        msg = str(exc)
        assert "8250" in msg and "8192" in msg, (
            f"Expected actual vs limit byte counts in message, got: {msg}"
        )

    oversized_words = " ".join("word" for _ in range(2505))
    try:
        _assert_word_cap("skills/dev-lifecycle/SKILL.md", 2500, content=oversized_words)
        raise AssertionError("Expected _assert_word_cap to fail when 2505 > 2500")
    except AssertionError as exc:
        msg = str(exc)
        assert "2505" in msg and "2500" in msg, (
            f"Expected actual vs limit word counts in message, got: {msg}"
        )

    # 2. Live repository byte and word ceilings
    critical_rules_path = REPO_ROOT / "rules" / "CRITICAL_RULES.md"
    _assert_byte_cap(critical_rules_path, 8192)
    critical_text = critical_rules_path.read_text(encoding="utf-8")
    assert "## 5." in critical_text
    assert "## 10. Zero-Fluff Output Cap" in critical_text

    _assert_byte_cap(REPO_ROOT / "skills" / "dev-designer" / "SKILL.md", 22528)
    _assert_word_cap(REPO_ROOT / "skills" / "dev-lifecycle" / "SKILL.md", 2500)
    _assert_word_cap(REPO_ROOT / "skills" / "dev-implementation" / "SKILL.md", 4500)

    # 3. task-observer places <SUBAGENT-STOP> immediately after frontmatter (L20+) and excludes subagents
    observer_lines = (
        (REPO_ROOT / "skills" / "task-observer" / "SKILL.md")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    fm_end = observer_lines.index("---", 1)
    assert "<SUBAGENT-STOP>" in observer_lines[fm_end + 1 : fm_end + 5], (
        f"Expected <SUBAGENT-STOP> immediately after frontmatter (around L20+), found: "
        f"{observer_lines[fm_end + 1 : fm_end + 5]}"
    )
    fm_text = "\n".join(observer_lines[1:fm_end]).lower()
    assert "subagent" in fm_text and "headless" in fm_text

    # 4. resume_context.py --compact --epic token_throttling_optimization <= 4096 bytes
    compact_proc = subprocess.run(
        [
            sys.executable,
            str(RESUME_SCRIPT),
            "--compact",
            "--epic",
            "token_throttling_optimization",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert compact_proc.returncode == 0, compact_proc.stderr
    _assert_byte_cap(
        "resume_context.py --compact --epic token_throttling_optimization",
        4096,
        content=compact_proc.stdout.encode("utf-8"),
    )

    # 5. Zero stale Gemini Flash 3.8 / gemini-3.8-flash Role 2.3 defaults across exact 9-file path set
    markdown_paths = (
        "rules/CRITICAL_RULES.md",
        "docs/lifecycles.en.md",
        "docs/lifecycles.vi.md",
        "skills/dev-lifecycle/SKILL.md",
        "skills/dev-lifecycle/references/autonomous-mode.md",
        "skills/dev-implementation/SKILL.md",
        "skills/principal-review/SKILL.md",
    )
    for rel_path in markdown_paths:
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for stale in ("Gemini Flash 3.8", "gemini-3.8-flash", "Gemini 3.8 Flash"):
            assert stale not in content, (
                f"Stale Role 2.3 default {stale!r} found in {rel_path}"
            )

    script_paths = (
        "skills/dev-lifecycle/resources/scripts/lifecycle_runner.py",
        "scripts/resume_context.py",
    )
    for rel_path in script_paths:
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert "Gemini Flash 3.8" not in content, f"Stale label found in {rel_path}"
        assert 'DEFAULT_PROGRAMMER_MODEL = "gemini-4-hydrogen-xhigh"' in content
        assert 'DEFAULT_PROGRAMMER_EFFORT = "xhigh"' in content
        non_alias_hits = [
            f"L{idx}: {line.strip()}"
            for idx, line in enumerate(content.splitlines(), 1)
            if "gemini-3.8-flash" in line and "LEGACY_PROGRAMMER_MODELS" not in line
        ]
        assert not non_alias_hits, (
            f"Stale gemini-3.8-flash reference outside LEGACY_PROGRAMMER_MODELS in {rel_path}: {non_alias_hits}"
        )

    # 6. Dynamic resolution including legacy "gemini-3.8-flash-high" upgrade
    assert rer.upgrade_legacy_programmer_provider(
        {"model": "gemini-3.8-flash-high", "thinking_level": "high"}
    ) == (
        "gemini-4-hydrogen-xhigh",
        "xhigh",
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_repo = Path(tmpdir)
        (tmp_repo / ".devtool").mkdir(parents=True, exist_ok=True)
        (tmp_repo / ".devtool" / "review_config.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "programmer": {
                            "model": "gemini-3.8-flash-high",
                            "thinking_level": "high",
                        },
                    }
                }
            ),
            encoding="utf-8",
        )
        cfg = lc_mod.RunnerConfig()
        clean_env = {
            k: v
            for k, v in os.environ.items()
            if k not in {"AGY_PROGRAMMER_MODEL", "AGY_PROGRAMMER_EFFORT"}
        }
        with patch.dict(os.environ, clean_env, clear=True):
            assert cfg.resolve_programmer_model(tmp_repo) == "gemini-4-hydrogen-xhigh"
            assert cfg.resolve_programmer_effort(tmp_repo) == "xhigh"

    # 7. External review diff budget constants stay bounded
    assert rer.MAX_DIFF_LINES <= 1500, (
        f"MAX_DIFF_LINES drifted: {rer.MAX_DIFF_LINES} > 1500"
    )
    assert rer.MAX_DIFF_BYTES <= 60000, (
        f"MAX_DIFF_BYTES drifted: {rer.MAX_DIFF_BYTES} > 60000"
    )


class TestTTOTokenThrottlingAcceptance_Integration:
    """Tier C integration provenance wrappers for Task 6 BDD scenarios."""

    def test_tto_hp_08_integration(self) -> None:
        """[TTO-HP-08] Integration provenance wrapper for end-to-end token-throttling pipeline."""
        test_tto_hp_08_end_to_end_pipeline()

    def test_tto_ec_06_integration(self) -> None:
        """[TTO-EC-06] Integration provenance wrapper for verify.sh suite registry and quiet/full modes."""
        test_tto_ec_06_verify_suite_registration()

    def test_tto_ar_02_integration(self) -> None:
        """[TTO-AR-02] Integration provenance wrapper for per-task and per-round isolation."""
        test_tto_ar_02_isolated_context_and_round_logs()

    def test_tto_fr_04_integration(self) -> None:
        """[TTO-FR-04] Integration provenance wrapper for fail-loud quantitative bounds."""
        test_tto_fr_04_quantitative_byte_caps_and_fail_loud()
