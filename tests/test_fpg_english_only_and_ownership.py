"""BDD & TDD tests for English-only document resolution and exclusive file ownership.

Covers: FPG-HP-06, FPG-HP-09, FPG-EC-04, FPG-AR-02
"""

from __future__ import annotations

import builtins
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
FINISH_SCRIPTS = (
    REPO_ROOT / "skills" / "finishing-a-development-branch" / "resources" / "scripts"
)

ISOLATED_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "FPG Tester",
    "GIT_AUTHOR_EMAIL": "fpg@example.com",
    "GIT_COMMITTER_NAME": "FPG Tester",
    "GIT_COMMITTER_EMAIL": "fpg@example.com",
}


def _load_script(module_name: str, path: Path) -> Any:
    script_dir = str(path.parent)
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None, f"Cannot load {path}"
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    merged = {**os.environ, **ISOLATED_GIT_ENV}
    if extra:
        merged.update(extra)
    return merged


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args],
        env=_env(),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "fpg@example.com")
    _git(root, "config", "user.name", "FPG Tester")
    (root / ".gitignore").write_text(
        "build/\n.devtool/state/\n__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (root / "README.md").write_text("# Demo Repo\n", encoding="utf-8")
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "verify.sh").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (root / "scripts" / "foo.py").write_text(
        "\n".join(f"def fn_{i}():\n    return {i}" for i in range(15)) + "\n",
        encoding="utf-8",
    )
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "src" / "beta.py").write_text("VALUE = 2\n", encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_alpha.py").write_text(
        "def test_alpha():\n    assert True\n", encoding="utf-8"
    )
    (root / "tool.py").write_text(
        "import pathlib, sys\n"
        "mode = sys.argv[1] if len(sys.argv) > 1 else 'green'\n"
        "if mode == 'red':\n"
        "    raise SystemExit(1)\n"
        "if mode == 'int':\n"
        "    out = pathlib.Path('build/test-results/int.xml')\n"
        "    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_text('<testsuite tests=\"1\"><testcase classname=\"tests.Solo_Integration\" name=\"SOLO-HP-01\"/></testsuite>')\n",
        encoding="utf-8",
    )
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "Initial repo")


def _run_py(
    script: Path, cwd: Path, *args: str, extra_env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        env=_env(extra_env),
        capture_output=True,
        text=True,
        check=False,
    )


def _task_markdown(
    task_id: str,
    epic_slug: str,
    epic_doc_name: str,
    *,
    allowed: str,
    covers: str = "",
    gherkin: str = "",
    dependencies: str = "- None.",
    impact: str = "- `tool.py`: `mode`",
    rows: str | None = None,
    dod: str | None = None,
) -> str:
    default_rows = (
        "| V1 | RED | `python3 tool.py red` | exit 1 | — |\n"
        "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |\n"
        "| V3 | TIER-B | `ruff check tool.py` | exit 0 | — |\n"
        "| V4 | TIER-B | `mypy tool.py` | exit 0 | — |\n"
        "| V5 | TIER-C | `python3 tool.py int` | exit 0; results build/test-results/int.xml | — |"
    )
    used_rows = rows if rows is not None else default_rows
    used_dod = dod if dod is not None else "- Verified cleanly (V2, V3, V4, V5)."
    covers_block = f"\n{covers}\n" if covers else "\n"
    bdd_block = f"\n### BDD SCENARIOS\n\n{covers}\n\n{gherkin}\n" if gherkin else ""
    return (
        f"---\n"
        f'id: "{task_id}"\n'
        f'status: "todo"\n'
        f'priority: "high"\n'
        f'assignee: null\n'
        f'epic: "{epic_slug}"\n'
        f"dueDate: null\n"
        f'created: "2026-11-17T10:00:00Z"\n'
        f'modified: "2026-11-17T10:00:00Z"\n'
        f"completedAt: null\n"
        f'labels: ["demo"]\n'
        f'order: "a1"\n'
        f"---\n\n"
        f"# Task {task_id}: Work Item\n\n"
        f"Epic: [{epic_slug}]({epic_doc_name})\n"
        f"{covers_block}"
        f"## Requirement Analysis\n\nImplement {task_id}.\n\n"
        f"## Files\n\n"
        f"Allowed files:\n{allowed}\n\n"
        f"Read-only context:\n- `README.md` — repository overview\n\n"
        f"## Design Rationale\n\nKeep changes surgical.\n\n"
        f"## Impact Analysis & Blast Radius\n\n"
        f"- **Target Files & Symbols**:\n  {impact}\n"
        f"{bdd_block}\n"
        f"## Verification\n\n"
        f"| ID | Phase | Command | Expect | Needs |\n"
        f"|----|-------|---------|--------|-------|\n"
        f"{used_rows}\n\n"
        f"## Stop and Report If\n\n- A verification row fails unexpectedly.\n\n"
        f"## Decisions Already Made\n\n- Grounded architectural decision.\n\n"
        f"## Definition of Done\n\n{used_dod}\n\n"
        f"## Dependencies & Blockers\n\n{dependencies}\n"
    )


def _setup_solo_epic(root: Path, *, with_errata: bool = False) -> Path:
    epic_dir = root / ".devtool" / "epic" / "solo_epic"
    features_dir = root / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    (epic_dir / "2026-11-17-solo-design.md").write_text(
        "# Solo Design Spec\n\n## Table of Contents\n\n- [Meta Data](#meta-data)\n- [Overview](#overview)\n\n"
        "## Meta Data\n\n- **Status**: Approved (Gate 1)\n\n## Overview\n\nDesign approved.\n",
        encoding="utf-8",
    )
    errata_toc = "- [Spec Errata](#spec-errata)\n" if with_errata else ""
    errata_sec = (
        "\n## Spec Errata\n\n- **[SE-01] Verification**: Clarify solo runner output\n"
        if with_errata
        else ""
    )
    (epic_dir / "solo_epic.md").write_text(
        "# Solo Epic HLD\n\n## Table of Contents\n\n"
        "- [Meta Data](#meta-data)\n"
        "- [Integration Test Plan](#integration-test-plan)\n"
        "- [Verification Environment](#verification-environment)\n"
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n"
        f"{errata_toc}\n"
        "## Meta Data\n\n- **Epic**: `solo-epic`\n- **Status**: Planned\n\n"
        "## Integration Test Plan\n\n"
        "Protected paths: scripts/verify.sh\n\n"
        "Integration test roots: tests/\n\n"
        "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
        "## Verification Environment\n\nTemp git repositories.\n\n"
        "## Kanban Tasks Breakdown\n\n1. [Task 01](task_01_alpha.md)\n2. [Task 02](task_02_beta.md)\n"
        f"{errata_sec}",
        encoding="utf-8",
    )

    sc_1 = (
        "```gherkin\n"
        "Scenario: [SOLO-HP-01] [Tier C - Integration] SOLO-HP-01 runs solo verification\n"
        "  Given solo_epic has English-only documents\n"
        "  When SOLO-HP-01 runs downstream verifiers\n"
        "  Then SOLO-HP-01 passes cleanly\n"
        "```"
    )
    sc_2 = (
        "```gherkin\n"
        "Scenario: [SOLO-EC-01] [Tier A - Unit] Solo edge path\n"
        "  Given beta unit check\n"
        "  When beta runs\n"
        "  Then beta passes\n"
        "```"
    )
    (epic_dir / "bdd_scenarios.md").write_text(
        "# Solo BDD Scenarios\n\n## Table of Contents\n\n- [Scenarios](#scenarios)\n\n"
        f"## Scenarios\n\n### SOLO-HP-01\n\n{sc_1}\n\n### SOLO-EC-01\n\n{sc_2}\n",
        encoding="utf-8",
    )

    t1 = _task_markdown(
        "task_01_alpha",
        "solo-epic",
        "solo_epic.md",
        allowed="- `src/alpha.py`",
        covers="Covers: SOLO-HP-01",
        gherkin=sc_1,
        impact="- `src/alpha.py`: `VALUE`",
    )
    t2 = _task_markdown(
        "task_02_beta",
        "solo-epic",
        "solo_epic.md",
        allowed="- `src/beta.py`",
        covers="Covers: SOLO-EC-01",
        gherkin=sc_2,
        impact="- `src/beta.py`: `VALUE`",
    )
    for name, content in (("task_01_alpha.md", t1), ("task_02_beta.md", t2)):
        (epic_dir / name).write_text(content, encoding="utf-8")
        (features_dir / name).write_text(
            content.replace("](solo_epic.md)", "](../epic/solo_epic/solo_epic.md)"),
            encoding="utf-8",
        )
    return epic_dir


def _install_md_open_spy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Callable[[], list[str]]:
    """Record every opened/read markdown path across this process and spawned Python children."""
    spy_log = tmp_path / "opened_paths.log"
    site_dir = tmp_path / "spy_site"
    site_dir.mkdir(exist_ok=True)
    (site_dir / "sitecustomize.py").write_text(
        "import builtins, os, pathlib\n"
        f"LOG = pathlib.Path({str(spy_log)!r})\n"
        "def _record(p):\n"
        "    s = str(p)\n"
        "    if s.endswith('.md'):\n"
        "        with builtins.open(LOG, 'a', encoding='utf-8') as f:\n"
        "            f.write(s + '\\n')\n"
        "_orig_open = builtins.open\n"
        "def _spy_open(file, *a, **kw):\n"
        "    _record(file)\n"
        "    return _orig_open(file, *a, **kw)\n"
        "builtins.open = _spy_open\n"
        "_orig_read_text = pathlib.Path.read_text\n"
        "def _spy_read_text(self, *a, **kw):\n"
        "    _record(self)\n"
        "    return _orig_read_text(self, *a, **kw)\n"
        "pathlib.Path.read_text = _spy_read_text\n",
        encoding="utf-8",
    )

    recorded_in_proc: list[str] = []
    orig_open = builtins.open
    orig_read_text = Path.read_text

    def spy_open(file: Any, *args: Any, **kwargs: Any) -> Any:
        if isinstance(file, (str, os.PathLike)):
            recorded_in_proc.append(os.fspath(file))
        return orig_open(file, *args, **kwargs)

    def spy_read_text(self: Path, *args: Any, **kwargs: Any) -> str:
        recorded_in_proc.append(str(self))
        return orig_read_text(self, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(Path, "read_text", spy_read_text)
    monkeypatch.setenv(
        "PYTHONPATH",
        f"{site_dir}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(
            os.pathsep
        ),
    )

    def collect_vi_reads() -> list[str]:
        subproc_paths = (
            spy_log.read_text(encoding="utf-8").splitlines() if spy_log.is_file() else []
        )
        return [p for p in (recorded_in_proc + subproc_paths) if p.endswith(".vi.md")]

    return collect_vi_reads


class Test_FPG_English_Only_Integration:
    """[Tier C - Integration] Integration suite for English-only epic resolution."""

    def test_fpg_hp_06_english_only_epic_passes_readiness_and_packaging(
        self, tmp_path: Path
    ) -> None:
        """[FPG-HP-06] [Tier C - Integration] A new English-only epic passes readiness and packaging with single files."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_repo(repo)
        epic_dir = _setup_solo_epic(repo)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add solo_epic")

        res_ready = _run_py(
            DEV_IMPL_SCRIPTS / "check_epic_readiness.py", repo, "solo_epic"
        )
        assert res_ready.returncode == 0, res_ready.stdout + res_ready.stderr
        assert "R1 PASS" in res_ready.stdout
        assert "R3 PASS" in res_ready.stdout
        assert "R7 PASS" in res_ready.stdout

        res_pkg = _run_py(DEV_IMPL_SCRIPTS / "package_epic.py", repo, "solo_epic")
        assert res_pkg.returncode == 0, res_pkg.stdout + res_pkg.stderr

        hld_text = (epic_dir / "solo_epic.md").read_text(encoding="utf-8")
        assert "- **Status**: Packaged" in hld_text

        handoff_text = (epic_dir / "handoff.md").read_text(encoding="utf-8")
        assert "solo_epic.md" in handoff_text
        assert "bdd_scenarios.md" in handoff_text
        assert "2026-11-17-solo-design.md" in handoff_text
        assert ".vi.md" not in handoff_text
        assert ".en.md" not in handoff_text

        assert list(epic_dir.glob("*.vi.md")) == []
        assert list(epic_dir.glob("*.en.md")) == []

    def test_fpg_hp_09_downstream_verifiers_read_english_only_documents(
        self, tmp_path: Path
    ) -> None:
        """[FPG-HP-09] [Tier C - Integration] Downstream verifiers read English-only epic documents."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_repo(repo)
        epic_dir = _setup_solo_epic(repo, with_errata=True)
        # Use a task with real passing RED -> GREEN -> TIER-C evidence for task_01_alpha
        (repo / "src" / "alpha.py").write_text("VALUE = 0\n", encoding="utf-8")
        t1_path = epic_dir / "task_01_alpha.md"
        t1_text = t1_path.read_text(encoding="utf-8").replace(
            "| V1 | RED | `python3 tool.py red` | exit 1 | — |\n"
            "| V2 | GREEN | `python3 tool.py green` | exit 0 | — |",
            '| V1 | RED | `python3 -B -c "import src.alpha; assert src.alpha.VALUE == 1"` | exit 1 | — |\n'
            '| V2 | GREEN | `python3 -B -c "import src.alpha; assert src.alpha.VALUE == 1"` | exit 0 | — |',
        )
        t1_path.write_text(t1_text, encoding="utf-8")
        (repo / ".devtool" / "features" / "task_01_alpha.md").write_text(
            t1_text.replace("](solo_epic.md)", "](../epic/solo_epic/solo_epic.md)"),
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add solo_epic base")
        base_sha = _git(repo, "rev-parse", "HEAD")

        # 1. generate_smoke_checklist.py --epic-dir solo_epic
        res_smoke = _run_py(
            DEV_IMPL_SCRIPTS / "generate_smoke_checklist.py",
            repo,
            "--epic-dir",
            "solo_epic",
            "--workspace-root",
            str(repo),
        )
        assert res_smoke.returncode == 0, res_smoke.stdout + res_smoke.stderr
        checklist_text = (epic_dir / "manual_smoke_checklist.md").read_text(
            encoding="utf-8"
        )
        assert "SOLO-HP-01" in checklist_text

        # 2. run_task_checks.py red -> edit -> verify -> status
        res_red = _run_py(
            DEV_IMPL_SCRIPTS / "run_task_checks.py",
            repo,
            "red",
            ".devtool/epic/solo_epic/task_01_alpha.md",
        )
        assert res_red.returncode == 0, res_red.stdout + res_red.stderr
        (repo / "src" / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
        res_verify = _run_py(
            DEV_IMPL_SCRIPTS / "run_task_checks.py",
            repo,
            "verify",
            ".devtool/epic/solo_epic/task_01_alpha.md",
        )
        assert res_verify.returncode == 0, res_verify.stdout + res_verify.stderr
        res_status = _run_py(
            DEV_IMPL_SCRIPTS / "run_task_checks.py",
            repo,
            "status",
            ".devtool/epic/solo_epic/task_01_alpha.md",
        )
        assert res_status.returncode == 0, res_status.stdout + res_status.stderr
        assert "done gate: PASS" in res_status.stdout

        evidence_data = json.loads(
            (epic_dir / "evidence" / "task_01_alpha.json").read_text(encoding="utf-8")
        )
        tier_c_row = next(
            r for r in evidence_data["runs"]["verify"]["rows"] if r["id"] == "V5"
        )
        assert any(
            c["name"] == "SOLO-HP-01" and c["status"] == "passed"
            for c in tier_c_row["results"]["digest"]["cases"]
        )

        # Commit task_01_alpha deliverables + evidence + done status, and amend solo_epic.md
        t1_done = t1_text.replace('status: "todo"', 'status: "done"')
        t1_path.write_text(t1_done, encoding="utf-8")
        done_dir = repo / ".devtool" / "features" / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        (repo / ".devtool" / "features" / "task_01_alpha.md").unlink()
        (done_dir / "task_01_alpha.md").write_text(
            t1_done.replace("](solo_epic.md)", "](../../epic/solo_epic/solo_epic.md)"),
            encoding="utf-8",
        )
        hld_path = epic_dir / "solo_epic.md"
        hld_text = hld_path.read_text(encoding="utf-8")
        hld_text = hld_text.replace(
            "Integration results: python3 tool.py int -> build/test-results/int.xml",
            "Integration results: python3 tool.py int --all -> build/test-results/int.xml",
        )
        hld_text += "- **[SE-02] Audit**: Amended integration filter\n"
        hld_path.write_text(hld_text, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Deliver task_01_alpha and amend solo_epic.md")
        head_sha = _git(repo, "rev-parse", "HEAD")

        # 3. audit_epic.py reports HLD amendment from solo_epic.md
        res_audit = _run_py(
            DEV_IMPL_SCRIPTS / "audit_epic.py",
            repo,
            "--epic-dir",
            "solo_epic",
            "--base",
            base_sha,
        )
        assert res_audit.returncode == 0, res_audit.stdout + res_audit.stderr
        assert (
            "solo_epic.md: Protected paths or Integration results changed since base"
            in res_audit.stdout
        )
        assert (
            "+Integration results: python3 tool.py int --all -> build/test-results/int.xml"
            in res_audit.stdout
        )

        # 4. local_review.py slices include solo_epic.md and bdd_scenarios.md
        lr = _load_script("local_review", DEV_IMPL_SCRIPTS / "local_review.py")
        t_slice = lr.task_slice(
            repo, ".devtool/epic/solo_epic", "task_01_alpha", head_sha, ()
        )
        t_rendered = lr.render_user(t_slice)
        assert "SOLO-HP-01" in t_rendered
        ep_slice = lr.epic_slice(
            repo,
            ".devtool/epic/solo_epic",
            base_sha,
            head_sha,
            res_audit.stdout,
            "results",
            [],
            (),
        )
        ep_rendered = lr.render_user(ep_slice)
        part_names = {p.name for p in ep_slice._parts}
        assert "solo_epic.md" in part_names
        assert "2026-11-17-solo-design.md" in part_names
        assert "# Solo Epic HLD" in ep_rendered
        assert "# Solo Design Spec" in ep_rendered

        rer = _load_script(
            "run_external_review", DEV_IMPL_SCRIPTS / "run_external_review.py"
        )
        assert "solo_epic.md" in rer.artefact_lines(repo, "solo_epic")
        assert "bdd_scenarios.md" in rer.artefact_lines(repo, "solo_epic")
        assert "solo_epic.md" in rer.principal_artefact_lines(repo, "solo_epic")
        assert "bdd_scenarios.md" in rer.principal_artefact_lines(repo, "solo_epic")

        # 5. integrate_branch.py upstream epic detection reads bdd_scenarios.md at upstream rev
        _git(repo, "checkout", "-q", "-b", "upstream-only")
        _git(repo, "checkout", "-q", base_sha)
        _git(repo, "checkout", "-q", "-b", "other-base")
        _git(repo, "rm", "-rf", "-q", ".devtool/epic/solo_epic")
        _git(repo, "commit", "-q", "-m", "Remove solo_epic from working tree")
        clean_base = _git(repo, "rev-parse", "HEAD")

        _git(repo, "checkout", "-q", "-b", "upstream-with-solo")
        _setup_solo_epic(repo)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add solo_epic upstream only")
        upstream_rev = _git(repo, "rev-parse", "HEAD")

        _git(repo, "checkout", "-q", "other-base")
        assert not (
            repo / ".devtool" / "epic" / "solo_epic" / "bdd_scenarios.md"
        ).exists()

        ib = _load_script("integrate_branch", FINISH_SCRIPTS / "integrate_branch.py")
        prev_cwd = Path.cwd()
        os.chdir(repo)
        try:
            detected = ib.upstream_epics(clean_base, upstream_rev)
        finally:
            os.chdir(prev_cwd)
        assert detected == [
            {"epic_dir": "solo_epic", "bdd": ".devtool/epic/solo_epic/bdd_scenarios.md"}
        ]

        # When an upstream epic has only .vi.md (no .md or .en.md), upstream_epics reports "bdd": None
        _git(repo, "checkout", "-q", "upstream-with-solo")
        (repo / ".devtool" / "epic" / "solo_epic" / "bdd_scenarios.md").unlink()
        (repo / ".devtool" / "epic" / "solo_epic" / "bdd_scenarios.vi.md").write_text(
            "# VI\n", encoding="utf-8"
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Replace bdd_scenarios.md with vi only")
        vi_only_rev = _git(repo, "rev-parse", "HEAD")
        _git(repo, "checkout", "-q", "other-base")
        os.chdir(repo)
        try:
            detected_none = ib.upstream_epics(clean_base, vi_only_rev)
        finally:
            os.chdir(prev_cwd)
        assert detected_none == [{"epic_dir": "solo_epic", "bdd": None}]

        # 6. Base holds solo_epic.en.md and HEAD holds renamed solo_epic.md with changed Integration results
        rename_repo = tmp_path / "rename_repo"
        rename_repo.mkdir()
        _init_repo(rename_repo)
        ren_epic = rename_repo / ".devtool" / "epic" / "solo_epic"
        ren_epic.mkdir(parents=True, exist_ok=True)
        (ren_epic / "solo_epic.en.md").write_text(
            "# Solo\n\nProtected paths: scripts/verify.sh\n"
            "Integration results: python3 tool.py v1 -> build/int.xml\n",
            encoding="utf-8",
        )
        _git(rename_repo, "add", "-A")
        _git(rename_repo, "commit", "-q", "-m", "Base .en.md")
        ren_base = _git(rename_repo, "rev-parse", "HEAD")

        (ren_epic / "solo_epic.en.md").unlink()
        (ren_epic / "solo_epic.md").write_text(
            "# Solo\n\nProtected paths: scripts/verify.sh\n"
            "Integration results: python3 tool.py v2 -> build/int.xml\n",
            encoding="utf-8",
        )
        _git(rename_repo, "add", "-A")
        _git(
            rename_repo,
            "commit",
            "-q",
            "-m",
            "Rename to .md and update Integration results",
        )

        ae = _load_script("audit_epic", DEV_IMPL_SCRIPTS / "audit_epic.py")
        amendments = ae.hld_amendments(rename_repo, ".devtool/epic/solo_epic", ren_base)
        assert len(amendments) == 1
        assert "solo_epic.en.md at base" in amendments[0]
        assert "solo_epic.md at HEAD" in amendments[0]
        assert "-Integration results: python3 tool.py v1 -> build/int.xml" in amendments[0]
        assert "+Integration results: python3 tool.py v2 -> build/int.xml" in amendments[0]

    def test_fpg_ec_04_legacy_bilingual_resolves_english_never_reads_vi(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """[FPG-EC-04] [Tier C - Integration] A legacy bilingual epic resolves the English file and never reads the mirror."""
        repo = tmp_path / "repo"
        repo.mkdir()
        _init_repo(repo)

        epic_dir = repo / ".devtool" / "epic" / "legacy_epic"
        features_dir = repo / ".devtool" / "features"
        epic_dir.mkdir(parents=True, exist_ok=True)
        features_dir.mkdir(parents=True, exist_ok=True)

        (epic_dir / "legacy_epic.en.md").write_text(
            "# Legacy Epic\n\n## Table of Contents\n\n"
            "- [Meta Data](#meta-data)\n"
            "- [Integration Test Plan](#integration-test-plan)\n"
            "- [Verification Environment](#verification-environment)\n\n"
            "## Meta Data\n\n- **Epic**: `legacy-epic`\n- **Status**: Planned\n\n"
            "## Integration Test Plan\n\nProtected paths: scripts/verify.sh\n"
            "Integration test roots: tests/\n"
            "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
            "## Verification Environment\n\nIsolated temp repo.\n",
            encoding="utf-8",
        )
        stale_hld_vi = "# Legacy VI\n\n- **Trạng thái**: Bản nháp cũ\n"
        (epic_dir / "legacy_epic.vi.md").write_text(stale_hld_vi, encoding="utf-8")

        sc_1 = (
            "```gherkin\n"
            "Scenario: [LEG-HP-01] [Tier C - Integration] Legacy English scenario\n"
            "  Given legacy epic\n"
            "  When legacy runs\n"
            "  Then legacy passes\n"
            "```"
        )
        (epic_dir / "bdd_scenarios.en.md").write_text(
            "# Legacy BDD\n\n## Table of Contents\n\n- [Scenarios](#scenarios)\n\n"
            f"## Scenarios\n\n### LEG-HP-01\n\n{sc_1}\n",
            encoding="utf-8",
        )
        stale_bdd_vi = "# Stale VI BDD\n\n```gherkin\nScenario: [LEG-99] Stale\n```\n"
        (epic_dir / "bdd_scenarios.vi.md").write_text(stale_bdd_vi, encoding="utf-8")

        t1 = _task_markdown(
            "task_01_legacy",
            "legacy-epic",
            "legacy_epic.en.md",
            allowed="- `src/alpha.py`",
            covers="Covers: LEG-HP-01",
            gherkin=sc_1,
            impact="- `src/alpha.py`: `VALUE`",
        )
        (epic_dir / "task_01_legacy.md").write_text(t1, encoding="utf-8")
        (features_dir / "task_01_legacy.md").write_text(
            t1.replace(
                "](legacy_epic.en.md)", "](../epic/legacy_epic/legacy_epic.en.md)"
            ),
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add legacy_epic")

        hld_vi_bytes = (epic_dir / "legacy_epic.vi.md").read_bytes()
        bdd_vi_bytes = (epic_dir / "bdd_scenarios.vi.md").read_bytes()

        collect_vi_reads = _install_md_open_spy(tmp_path, monkeypatch)

        cer = _load_script(
            "check_epic_readiness", DEV_IMPL_SCRIPTS / "check_epic_readiness.py"
        )
        sts = _load_script("sync_task_status", DEV_IMPL_SCRIPTS / "sync_task_status.py")
        cbt = _load_script(
            "check_bdd_traceability", DEV_IMPL_SCRIPTS / "check_bdd_traceability.py"
        )

        prev_cwd = Path.cwd()
        os.chdir(repo)
        try:
            # 1. check_epic_readiness.py legacy_epic --strict-bilingual
            cer_out, cer_err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(cer_out), contextlib.redirect_stderr(cer_err):
                cer_rc = cer.main(["legacy_epic", "--strict-bilingual"])
            assert cer_rc == 0, cer_out.getvalue() + cer_err.getvalue()
            assert (
                cer_err.getvalue().count(
                    "warning: --strict-bilingual is deprecated and ignored"
                )
                == 1
            ), cer_err.getvalue()

            # 2. sync_task_status.py epic legacy_epic Packaged
            monkeypatch.setattr(
                sys,
                "argv",
                ["sync_task_status.py", "epic", "legacy_epic", "Packaged"],
            )
            sts_out, sts_err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(sts_out), contextlib.redirect_stderr(sts_err):
                sts.main()

            # 3. check_bdd_traceability.py plan --strict-bilingual
            cbt_out, cbt_err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(cbt_out), contextlib.redirect_stderr(cbt_err):
                cbt_rc = cbt.main(
                    [
                        "plan",
                        "--scenarios",
                        str(epic_dir / "bdd_scenarios.en.md"),
                        "--tasks",
                        str(epic_dir / "task_01_legacy.md"),
                        "--strict-bilingual",
                    ]
                )
            assert cbt_rc == 0, cbt_out.getvalue() + cbt_err.getvalue()
            assert (
                cbt_err.getvalue().count(
                    "warning: --strict-bilingual is deprecated and ignored"
                )
                == 1
            ), cbt_err.getvalue()
        finally:
            os.chdir(prev_cwd)

        assert "- **Status**: Packaged" in (epic_dir / "legacy_epic.en.md").read_text(
            encoding="utf-8"
        )
        assert (epic_dir / "legacy_epic.vi.md").read_bytes() == hld_vi_bytes
        assert (epic_dir / "bdd_scenarios.vi.md").read_bytes() == bdd_vi_bytes

        vi_reads = collect_vi_reads()
        assert vi_reads == [], f"Unexpected .vi.md file reads recorded: {vi_reads}"


def test_fpg_ar_02_parallel_tasks_must_own_disjoint_files(tmp_path: Path) -> None:
    """[FPG-AR-02] [Tier A - Unit] Parallel tasks must own disjoint files."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    epic_dir = repo / ".devtool" / "epic" / "demo"
    epic_dir.mkdir(parents=True, exist_ok=True)
    hld_path = epic_dir / "demo.md"
    hld_path.write_text(
        "# Demo Epic\n\n"
        "Protected paths: scripts/verify.sh\n\n"
        "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
        "## Verification Environment\n\nTemp dir.\n",
        encoding="utf-8",
    )

    t1_path = epic_dir / "task_01.md"
    t2_path = epic_dir / "task_02.md"
    t1_path.write_text(
        _task_markdown(
            "task_01",
            "demo",
            "demo.md",
            allowed="- `scripts/foo.py` (L10-L20)",
            impact="- `scripts/foo.py`: (L10-L20)",
        ),
        encoding="utf-8",
    )
    t2_path.write_text(
        _task_markdown(
            "task_02",
            "demo",
            "demo.md",
            allowed="- `scripts/foo.py`",
            impact="- `scripts/foo.py`: `fn_0`",
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add parallel overlapping tasks")

    ctc_script = DEV_IMPL_SCRIPTS / "check_task_contract.py"
    fail_res = _run_py(
        ctc_script,
        repo,
        "--design",
        "--hld",
        str(hld_path),
        "--tasks",
        str(t1_path),
        str(t2_path),
    )
    assert fail_res.returncode == 1, fail_res.stdout + fail_res.stderr
    assert (
        "R-OWN task_01 and task_02 both own scripts/foo.py with no Blocked by path between them"
        in fail_res.stdout
    ), fail_res.stdout

    # Now task_02 declares Blocked by [Task 01]
    t2_blocked = t2_path.read_text(encoding="utf-8").replace(
        "## Dependencies & Blockers\n\n- None.",
        "## Dependencies & Blockers\n\n- Blocked by [Task 01](task_01.md)",
    )
    t2_path.write_text(t2_blocked, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Block task_02 on task_01")

    pass_res = _run_py(
        ctc_script,
        repo,
        "--design",
        "--hld",
        str(hld_path),
        "--tasks",
        str(t1_path),
        str(t2_path),
    )
    assert pass_res.returncode == 0, pass_res.stdout + pass_res.stderr


def test_epic_docs_resolution_order_and_git_rev(tmp_path: Path) -> None:
    """Verify _epic_docs helper resolution order across working tree and git revisions."""
    ed = _load_script("_epic_docs", DEV_IMPL_SCRIPTS / "_epic_docs.py")
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    d = repo / ".devtool" / "epic" / "demo"
    d.mkdir(parents=True)

    # 1. Absent -> None, []
    assert ed.resolve_epic_doc(d, "demo") is None
    assert ed.resolve_design_specs(d) == []

    # 2. Only .vi.md -> None, []
    (d / "demo.vi.md").write_text("# VI\n", encoding="utf-8")
    (d / "2026-11-17-a-design.vi.md").write_text("# VI spec\n", encoding="utf-8")
    assert ed.resolve_epic_doc(d, "demo") is None
    assert ed.resolve_design_specs(d) == []

    # 3. .en.md fallback
    (d / "demo.en.md").write_text("# EN\n", encoding="utf-8")
    (d / "2026-11-17-a-design.en.md").write_text("# EN spec\n", encoding="utf-8")
    assert ed.resolve_epic_doc(d, "demo") == d / "demo.en.md"
    assert ed.resolve_design_specs(d) == [d / "2026-11-17-a-design.en.md"]

    # 4. Plain .md takes precedence over .en.md; resolve_design_specs returns *-design.md then *-design.en.md
    (d / "demo.md").write_text("# Plain\n", encoding="utf-8")
    (d / "2026-11-17-b-design.md").write_text("# Plain spec\n", encoding="utf-8")
    assert ed.resolve_epic_doc(d, "demo") == d / "demo.md"
    assert ed.resolve_design_specs(d) == [
        d / "2026-11-17-b-design.md",
        d / "2026-11-17-a-design.en.md",
    ]

    # 5. resolve_epic_doc_at reads git revision even when working tree differs
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Commit docs")
    rev_both = _git(repo, "rev-parse", "HEAD")

    (d / "demo.md").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Remove plain .md")
    rev_en_only = _git(repo, "rev-parse", "HEAD")

    (d / "demo.en.md").unlink()
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Leave only .vi.md")
    rev_vi_only = _git(repo, "rev-parse", "HEAD")

    assert (
        ed.resolve_epic_doc_at(repo, rev_both, ".devtool/epic/demo", "demo")
        == ".devtool/epic/demo/demo.md"
    )
    assert (
        ed.resolve_epic_doc_at(repo, rev_en_only, ".devtool/epic/demo", "demo")
        == ".devtool/epic/demo/demo.en.md"
    )
    assert ed.resolve_epic_doc_at(repo, rev_vi_only, ".devtool/epic/demo", "demo") is None


def test_ownership_transitive_blocking_and_path_normalization(tmp_path: Path) -> None:
    """Transitive Blocked by paths allow shared ownership; normalized paths catch disguised overlaps."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    epic_dir = repo / ".devtool" / "epic" / "demo"
    epic_dir.mkdir(parents=True, exist_ok=True)
    hld_path = epic_dir / "demo.md"
    hld_path.write_text(
        "# Demo Epic\n\n"
        "Protected paths: scripts/verify.sh\n\n"
        "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
        "## Verification Environment\n\nTemp dir.\n",
        encoding="utf-8",
    )

    t1 = epic_dir / "task_01.md"
    t2 = epic_dir / "task_02.md"
    t3 = epic_dir / "task_03.md"
    t4 = epic_dir / "task_04.md"

    t1.write_text(
        _task_markdown(
            "task_01",
            "demo",
            "demo.md",
            allowed="- `./scripts/new_shared.py` (new)",
            impact="- `scripts/new_shared.py`: `fn_0`",
        ),
        encoding="utf-8",
    )
    t2.write_text(
        _task_markdown(
            "task_02",
            "demo",
            "demo.md",
            allowed="- `src/alpha.py`",
            dependencies="- Blocked by [Task 01](task_01.md)",
            impact="- `src/alpha.py`: `VALUE`",
        ),
        encoding="utf-8",
    )
    t3.write_text(
        _task_markdown(
            "task_03",
            "demo",
            "demo.md",
            allowed="- `scripts/foo.py` :: `fn_1` (L4-L6)",
            dependencies="- Blocked by [Task 02](task_02.md)",
            impact="- `scripts/foo.py`: `fn_1`",
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add transitive chain")

    ctc_script = DEV_IMPL_SCRIPTS / "check_task_contract.py"
    pass_res = _run_py(
        ctc_script,
        repo,
        "--design",
        "--hld",
        str(hld_path),
        "--tasks",
        str(t1),
        str(t2),
        str(t3),
    )
    assert pass_res.returncode == 0, pass_res.stdout + pass_res.stderr

    # Adding unblocked task_04 sharing scripts/foo.py and scripts/new_shared.py fails R-OWN against both task_01 and task_03
    t4.write_text(
        _task_markdown(
            "task_04",
            "demo",
            "demo.md",
            allowed="- `scripts/foo.py (L10-L20)`\n- `scripts/new_shared.py`",
            impact="- `scripts/foo.py`: (L10-L20)",
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add parallel unblocked task_04")

    fail_res = _run_py(
        ctc_script,
        repo,
        "--design",
        "--hld",
        str(hld_path),
        "--tasks",
        str(t1),
        str(t2),
        str(t3),
        str(t4),
    )
    assert fail_res.returncode == 1, fail_res.stdout + fail_res.stderr
    assert "R-OWN task_01 and task_04 both own scripts/new_shared.py" in fail_res.stdout
    assert "R-OWN task_03 and task_04 both own scripts/foo.py" in fail_res.stdout


def _setup_vi_task_mirror_repo(
    tmp_path: Path, *, commit_vi: bool = True
) -> tuple[Path, Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "src" / "vi_sentinel_only.py").write_text(
        "VI_SENTINEL = True\n", encoding="utf-8"
    )
    _git(repo, "add", "src/vi_sentinel_only.py")
    _git(repo, "commit", "-q", "-m", "Add sentinel module")
    base_sha = _git(repo, "rev-parse", "HEAD")

    epic_dir = repo / ".devtool" / "epic" / "solo_epic"
    features_dir = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    (epic_dir / "2026-11-17-solo-design.md").write_text(
        "# Solo Design Spec\n\n## Table of Contents\n\n- [Meta Data](#meta-data)\n\n"
        "## Meta Data\n\n- **Status**: Approved (Gate 1)\n",
        encoding="utf-8",
    )
    (epic_dir / "solo_epic.md").write_text(
        "# Solo Epic HLD\n\n## Table of Contents\n\n"
        "- [Meta Data](#meta-data)\n"
        "- [Integration Test Plan](#integration-test-plan)\n"
        "- [Verification Environment](#verification-environment)\n"
        "- [Kanban Tasks Breakdown](#kanban-tasks-breakdown)\n\n"
        "## Meta Data\n\n- **Epic**: `solo-epic`\n- **Status**: Planned\n\n"
        "## Integration Test Plan\n\n"
        "Protected paths: scripts/verify.sh\n\n"
        "Integration test roots: tests/\n\n"
        "Integration results: python3 tool.py int -> build/test-results/int.xml\n\n"
        "## Verification Environment\n\nTemp git repositories.\n\n"
        "## Kanban Tasks Breakdown\n\n1. [Task 01](task_01_x.md)\n",
        encoding="utf-8",
    )
    sc_1 = (
        "```gherkin\n"
        "Scenario: [SOLO-HP-01] [Tier C - Integration] SOLO-HP-01 runs solo verification\n"
        "  Given solo_epic has English-only documents\n"
        "  When SOLO-HP-01 runs\n"
        "  Then SOLO-HP-01 passes cleanly\n"
        "```"
    )
    (epic_dir / "bdd_scenarios.md").write_text(
        "# Solo BDD\n\n## Table of Contents\n\n- [Scenarios](#scenarios)\n\n"
        f"## Scenarios\n\n### SOLO-HP-01\n\n{sc_1}\n",
        encoding="utf-8",
    )
    t1 = _task_markdown(
        "task_01_x",
        "solo-epic",
        "solo_epic.md",
        allowed="- `src/alpha.py`",
        covers="Covers: SOLO-HP-01",
        gherkin=sc_1,
        impact="- `src/alpha.py`: `VALUE`",
    )
    (epic_dir / "task_01_x.md").write_text(t1, encoding="utf-8")
    (features_dir / "task_01_x.md").write_text(
        t1.replace("](solo_epic.md)", "](../epic/solo_epic/solo_epic.md)"),
        encoding="utf-8",
    )

    vi_task_text = (
        "---\n"
        'id: "task_01_x"\n'
        'status: "done"\n'
        'priority: "high"\n'
        'epic: "solo-epic"\n'
        'order: "a1"\n'
        "---\n\n"
        "# Nhiem vu 01: VI_TASK_SENTINEL\n\n"
        "Epic: [solo-epic](solo_epic.md)\n\n"
        "## Files\n\nAllowed files:\n- `src/vi_sentinel_only.py`\n\n"
        "## Verification\n\n"
        "| ID | Phase | Command | Expect | Needs |\n"
        "|----|-------|---------|--------|-------|\n"
        "| V1 | GREEN | `python3 src/vi_sentinel_only.py` | exit 0 | — |\n\n"
        "## Definition of Done\n\n- Check VI_TASK_SENTINEL (Gate 5).\n"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "Add English epic docs and task_01_x.md")

    (epic_dir / "task_01_x.vi.md").write_text(vi_task_text, encoding="utf-8")
    if commit_vi:
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Add task_01_x.vi.md mirror")

    return repo, epic_dir, base_sha


@pytest.mark.parametrize(
    "caller",
    [
        "readiness_context_loading",
        "package_epic_task_counting",
        "task_contract_epic_layout",
        "audit_epic_task_discovery",
        "run_task_checks_task_discovery",
    ],
)
def test_task_discovery_never_opens_vi_mirrors(
    caller: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Task discovery across migrated scripts skips *.vi.md mirrors and never opens them."""
    repo, epic_dir, base_sha = _setup_vi_task_mirror_repo(
        tmp_path, commit_vi=(caller != "run_task_checks_task_discovery")
    )
    collect_vi_reads = _install_md_open_spy(tmp_path, monkeypatch)

    prev_cwd = Path.cwd()
    os.chdir(repo)
    try:
        if caller == "readiness_context_loading":
            cer = _load_script(
                "check_epic_readiness", DEV_IMPL_SCRIPTS / "check_epic_readiness.py"
            )
            ctx = cer.load_context(repo, "solo_epic")
            assert all(not p.name.endswith(".vi.md") for p in ctx.tasks)
            assert "VI_TASK_SENTINEL" not in "".join(ctx.tasks.values())
            assert not cer._is_epic_done(repo, "solo_epic")
        elif caller == "package_epic_task_counting":
            pkg = _load_script("package_epic", DEV_IMPL_SCRIPTS / "package_epic.py")
            assert not pkg._is_stage3_active(repo, epic_dir, "solo-epic")
            handoff = pkg.package_epic(repo, "solo_epic")
            assert "lists the 1 tasks." in handoff.read_text(encoding="utf-8")
        elif caller == "task_contract_epic_layout":
            tc = _load_script("task_contract", DEV_IMPL_SCRIPTS / "task_contract.py")
            prereq_files, _ = tc.collect_prerequisite_artifacts(repo, ["solo_epic"])
            assert "src/vi_sentinel_only.py" not in prereq_files
            with pytest.raises(tc.ContractError):
                tc.evaluate_done_gate(epic_dir / "task_01_x.vi.md")
        elif caller == "audit_epic_task_discovery":
            ae = _load_script("audit_epic", DEV_IMPL_SCRIPTS / "audit_epic.py")
            shown_paths: list[str] = []
            orig_show = ae.show

            def spy_show(root: Path, rev: str, path: str) -> str | None:
                shown_paths.append(path)
                return orig_show(root, rev, path)

            monkeypatch.setattr(ae, "show", spy_show)
            sections, failed = ae.build_report(repo, "solo_epic", base_sha)
            assert [p for p in shown_paths if p.endswith(".vi.md")] == []
            rendered = "\n".join(item for _, items in sections for item in items)
            assert "VI_TASK_SENTINEL" not in rendered
            assert "task_01_x.vi" not in rendered
            assert not failed
        elif caller == "run_task_checks_task_discovery":
            tc = _load_script("task_contract", DEV_IMPL_SCRIPTS / "task_contract.py")
            rtc = _load_script("run_task_checks", DEV_IMPL_SCRIPTS / "run_task_checks.py")
            layout = tc.epic_layout(epic_dir / "task_01_x.md")
            _, programs_untracked = rtc.protected_patterns(layout, repo)
            assert "src/vi_sentinel_only.py" not in programs_untracked
            _git(repo, "add", "-A")
            _git(repo, "commit", "-q", "-m", "Commit task_01_x.vi.md")
            _, programs_committed = rtc.protected_patterns(layout, repo)
            assert "src/vi_sentinel_only.py" not in programs_committed
    finally:
        os.chdir(prev_cwd)

    vi_reads = collect_vi_reads()
    assert vi_reads == [], f"Unexpected .vi.md file reads for {caller}: {vi_reads}"
