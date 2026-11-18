"""End-to-end acceptance tests for lifecycle_runner parity and verify.sh registration.

Covers BDD scenarios:
- TRC-HP-04: End-to-end runner parity and verify.sh registration enforce Pass 1 non-blocking approval and Pass 2 cap
- TRC-ST-04: Headless lifecycle_runner caps review passes at 2 and finalizes on Pass 2 completion when done_gate is PASS
- TRC-FR-03: Unparseable or missing task-reviewer JSON output fails closed without triggering Coercion Guard
"""

from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from types import ModuleType
from typing import Any
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
LIFECYCLE_SCRIPTS = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"

for _path in (str(LIFECYCLE_SCRIPTS), str(DEV_IMPL_SCRIPTS), str(SCRIPTS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)


def _load_module(name: str, path: Path) -> ModuleType:
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
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


manage_worker_pool = _load_module(
    "manage_worker_pool", DEV_IMPL_SCRIPTS / "manage_worker_pool.py"
)
lifecycle_runner = _load_module(
    "lifecycle_runner", LIFECYCLE_SCRIPTS / "lifecycle_runner.py"
)

EXPECTED_TRC_SUITES: tuple[tuple[str, bool], ...] = (
    ("tests/test_trc_persona_limits.py", False),
    ("tests/test_trc_reviewer_briefs_and_governance.py", True),
    ("tests/test_trc_worker_pool_triage.py", False),
    ("tests/test_trc_runner_and_acceptance.py", False),
)


@pytest.fixture(autouse=True)
def _isolate_host_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate HOME, REAL_HOME, and persona env vars from host configuration."""
    fake_home = tmp_path / "_isolated_home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("REAL_HOME", str(fake_home))
    for var in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
        "AGY_ASSISTANT_MODEL",
    ):
        monkeypatch.delenv(var, raising=False)
    return fake_home


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
    _git(repo_dir, "config", "user.name", "TRC Tester")
    _git(repo_dir, "config", "user.email", "trc@example.invalid")
    (repo_dir / ".gitignore").write_text(
        ".devtool/state/\n.devtool/logs/\n.devtool/.memory.lock\n.worktrees/\nbuild/\n__pycache__/\n*.pyc\n",
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


def _make_task_md(
    task_id: str,
    epic: str,
    *,
    allowed: list[str],
    blocked_by: list[str] | None = None,
    review_tier: str = "full",
) -> str:
    deps = (
        "Blocked by " + ", ".join(f"[{dep}]({dep}.md)" for dep in blocked_by) + "."
        if blocked_by
        else "None."
    )
    allowed_lines = "\n".join(f"- `{p}`" for p in allowed)
    return (
        f'---\nid: "{task_id}"\nstatus: "todo"\npriority: "high"\n'
        f'epic: "{epic}"\nlabels: []\nreview_tier: "{review_tier}"\n---\n\n'
        f"# Task {task_id}\n\n"
        f"## Dependencies & Blockers\n\n{deps}\n\n"
        f"## Files\n\nAllowed files:\n{allowed_lines}\n"
    )


def _persona_from_cli_args(cli: str, args: list[str]) -> tuple[str, str]:
    """Infer persona/mode from argv constructed by persona_config.build_dispatch_argv."""
    _ = cli
    mode = (
        "read-only"
        if ("--sandbox" in args or "plan" in args or "read-only" in args)
        else "write"
    )
    model_val = args[args.index("--model") + 1] if "--model" in args else ""
    persona = (
        "ai_architect_reviewer"
        if "argon" in model_val or mode == "read-only"
        else "programmer"
    )
    return persona, mode


def _parse_verify_suites(verify_text: str) -> list[tuple[str, str, str, int, bool]]:
    search_from = 0
    marker = "<<'PY'"
    while True:
        marker_idx = verify_text.find(marker, search_from)
        if marker_idx == -1:
            break
        start = verify_text.find("\n", marker_idx)
        end = verify_text.find("\nPY\n", start)
        if start == -1 or end == -1:
            break
        py_src = verify_text[start + 1 : end]
        search_from = end + 4
        tree = ast.parse(py_src)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "SUITES":
                        raw = ast.literal_eval(node.value)
                        return [
                            (str(sec), str(mode), str(path), int(prio), bool(doc))
                            for sec, mode, path, prio, doc in raw
                        ]
    raise AssertionError("SUITES assignment not found in scripts/verify.sh")


def _read_audit_notes(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _seed_epic_repo(
    tmp_path: Path,
    name: str,
    epic: str,
    *,
    tasks: dict[str, list[str]],
    with_epic_worktree: bool = False,
) -> tuple[Path, Path]:
    repo = tmp_path / name
    _init_git_repo(repo)
    _copy_dev_impl_scripts(repo)
    epic_dir = repo / ".devtool" / "epic" / epic
    features = repo / ".devtool" / "features"
    epic_dir.mkdir(parents=True, exist_ok=True)
    features.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{epic}.md").write_text("# Epic HLD\n", encoding="utf-8")
    (epic_dir / "bdd_scenarios.md").write_text("# BDD Scenarios\n", encoding="utf-8")
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    for task_slug, allowed in tasks.items():
        for rel in allowed:
            target = repo / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_text(f"# seed for {task_slug}\n", encoding="utf-8")
        task_md = _make_task_md(task_slug, epic, allowed=allowed, review_tier="full")
        (features / f"{task_slug}.md").write_text(task_md, encoding="utf-8")
        (epic_dir / f"{task_slug}.md").write_text(task_md, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", f"[{epic.upper()}] Seed epic")

    if with_epic_worktree:
        epic_wt = repo / ".worktrees" / epic
        epic_wt.parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "worktree", "add", "-b", f"epic/{epic}", str(epic_wt), "main")
        return repo, epic_wt
    return repo, repo


def test_trc_hp_04_end_to_end_runner_and_verify_registration(tmp_path: Path) -> None:
    """[TRC-HP-04] End-to-end runner parity and verify.sh registration enforce Pass 1 approval and Pass 2 cap."""
    epic = "trc_hp04"
    repo, epic_wt = _seed_epic_repo(
        tmp_path,
        "repo_hp04",
        epic,
        tasks={"task_01": ["src/a.py"], "task_02": ["src/b.py"]},
        with_epic_worktree=True,
    )
    main_head_before = _git(repo, "rev-parse", "main")

    runner = lifecycle_runner.LifecycleRunner(root=epic_wt, epic_slug=epic)
    runner.quota_gate = lambda *a, **kw: (True, "")

    lock = threading.Lock()
    task_calls: dict[str, dict[str, list[str]]] = {
        "task_01": {"implementer": [], "reviewer": []},
        "task_02": {"implementer": [], "reviewer": []},
    }
    task_shas: dict[str, list[str]] = {"task_01": [], "task_02": []}

    def stub_dispatch(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        wt = Path(self_disp.worktree_dir)
        persona, mode = _persona_from_cli_args(cli, args)
        task_slug = "task_01" if "task_01" in prompt else "task_02"
        role_key = "reviewer" if persona == "ai_architect_reviewer" else "implementer"

        with lock:
            call_idx = len(task_calls[task_slug][role_key]) + 1
            task_calls[task_slug][role_key].append(prompt)

        if persona == "programmer":
            assert mode == "write"
            if task_slug == "task_01":
                (wt / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
                _git(wt, "add", "src/a.py")
                _git(wt, "commit", "-q", "-m", "[TRC_HP04] Implement task_01")
            else:
                val = "1" if call_idx == 1 else "0"
                (wt / "src" / "b.py").write_text(f"B = {val}\n", encoding="utf-8")
                _git(wt, "add", "src/b.py")
                _git(
                    wt,
                    "commit",
                    "-q",
                    "-m",
                    f"[TRC_HP04] Implement task_02 pass {call_idx}",
                )
            head_sha = _git(wt, "rev-parse", "HEAD")
            with lock:
                task_shas[task_slug].append(head_sha)
            impl_out = {
                "task_id": task_slug,
                "slot": 1 if task_slug == "task_01" else 2,
                "status": "DONE",
                "head_sha": head_sha,
                "verify": "PASS",
                "changed_files": ["src/a.py"]
                if task_slug == "task_01"
                else ["src/b.py"],
                "non_test_modules_changed": 1,
                "review_tier": "full",
                "labels": [],
                "finalized": False,
            }
            return 0, f"```json\n{json.dumps(impl_out)}\n```\n", ""

        assert mode == "read-only"
        # Audit notes must never be created inside ephemeral pool slots.
        assert not (
            wt / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
        ).exists()
        current_head = _git(wt, "rev-parse", "HEAD")
        if task_slug == "task_01":
            rev_out = {
                "task_id": "task_01",
                "pass": 1,
                "verdict": "APPROVED",
                "head_sha": current_head,
                "done_gate": "PASS",
                "blockers": [],
                "observations": [
                    {"id": "OBS-1", "file": "src/a.py", "summary": "Style nit"}
                ],
            }
        elif call_idx == 1:
            rev_out = {
                "task_id": "task_02",
                "pass": 1,
                "verdict": "CHANGES_REQUESTED",
                "head_sha": current_head,
                "done_gate": "PASS",
                "blockers": [
                    {
                        "id": "BLK-1",
                        "category": "BDD_VIOLATION",
                        "file": "src/b.py",
                        "summary": "Fix return code",
                        "remediation": "Return 0",
                    }
                ],
                "observations": [],
            }
        else:
            rev_out = {
                "task_id": "task_02",
                "pass": 2,
                "verdict": "APPROVED",
                "head_sha": current_head,
                "done_gate": "PASS",
                "blockers": [],
                "observations": [],
            }
        return 0, f"```json\n{json.dumps(rev_out)}\n```\n", ""

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=stub_dispatch,
    ):
        ok = runner.step_implementation()

    assert ok, f"step_implementation failed: {runner.state.last_error}"

    # Task 1 finalized after 1 review pass and 0 fix passes.
    assert len(task_calls["task_01"]["implementer"]) == 1
    assert len(task_calls["task_01"]["reviewer"]) == 1
    p1_t1_prompt = task_calls["task_01"]["reviewer"][0]
    assert "APPROVED|CHANGES_REQUESTED" in p1_t1_prompt
    assert "BLOCKER" in p1_t1_prompt
    assert "NON_BLOCKING_OBSERVATION" in p1_t1_prompt

    # Task 2 finalized after 2 review passes and 1 fix pass with Delta-Only Pass 2 prompt.
    assert len(task_calls["task_02"]["implementer"]) == 2
    assert len(task_calls["task_02"]["reviewer"]) == 2
    assert len(task_shas["task_02"]) == 2
    assert task_shas["task_02"][0] != task_shas["task_02"][1]
    assert "BLK-1" in task_calls["task_02"]["implementer"][1]
    pass2_prompt = task_calls["task_02"]["reviewer"][1]
    assert "Delta-Only" in pass2_prompt
    assert re.search(r"git diff [0-9a-f]{40}\b", pass2_prompt), pass2_prompt
    assert "BLK-1" in pass2_prompt

    # Both tasks are marked done on the epic branch, and OBS-1 is committed in review_audit_notes.jsonl.
    assert (epic_wt / ".devtool" / "features" / "done" / "task_01.md").is_file()
    assert (epic_wt / ".devtool" / "features" / "done" / "task_02.md").is_file()
    assert _git(epic_wt, "status", "--porcelain") == ""

    audit_path = epic_wt / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
    notes = _read_audit_notes(audit_path)
    assert any(
        note.get("task_id") == "task_01"
        and any(obs.get("id") == "OBS-1" for obs in note.get("observations", []))
        for note in notes
    ), f"Expected OBS-1 audit note for task_01, got: {notes}"
    assert (
        _git(
            epic_wt,
            "ls-files",
            "--error-unmatch",
            f".devtool/epic/{epic}/review_audit_notes.jsonl",
        )
        == f".devtool/epic/{epic}/review_audit_notes.jsonl"
    )
    assert _git(repo, "rev-parse", "main") == main_head_before
    assert not (repo / ".devtool" / "epic" / epic / "review_audit_notes.jsonl").exists()

    # Verify scripts/verify.sh SUITES registration for all four test_trc_*.py suites.
    verify_text = (REPO_ROOT / "scripts" / "verify.sh").read_text(encoding="utf-8")
    suites = _parse_verify_suites(verify_text)
    counts: dict[str, int] = {}
    by_path: dict[str, tuple[str, str, int, bool]] = {}
    for sec, mode, rel_path, prio, doc_only in suites:
        counts[rel_path] = counts.get(rel_path, 0) + 1
        by_path[rel_path] = (sec, mode, prio, doc_only)

    disk_trc = sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in (REPO_ROOT / "tests").glob("test_trc_*.py")
    )
    expected_paths = sorted(path for path, _ in EXPECTED_TRC_SUITES)
    assert disk_trc == expected_paths
    for rel_path, expected_doc_only in EXPECTED_TRC_SUITES:
        assert (REPO_ROOT / rel_path).is_file()
        assert counts.get(rel_path, 0) == 1, (
            f"Expected {rel_path} once in scripts/verify.sh SUITES, got {counts.get(rel_path, 0)}"
        )
        sec, mode, _prio, doc_only = by_path[rel_path]
        assert sec == "11"
        assert mode == "pytest"
        assert doc_only is expected_doc_only


def test_trc_hp_04_coercion_guard_approves_zero_blocker_changes_requested(
    tmp_path: Path,
) -> None:
    """[TRC-HP-04] Zero-blocker CHANGES_REQUESTED with done_gate PASS coerces to APPROVED and logs observations."""
    epic = "trc_coercion"
    repo, _ = _seed_epic_repo(
        tmp_path, "repo_coerce", epic, tasks={"task_01": ["src/a.py"]}
    )
    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    calls: list[str] = []

    def stub_dispatch(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        _ = prompt
        persona, _ = _persona_from_cli_args(cli, args)
        calls.append(persona)
        if persona == "programmer":
            (repo / "src" / "a.py").write_text("A = 42\n", encoding="utf-8")
            _git(repo, "add", "src/a.py")
            _git(repo, "commit", "-q", "-m", "[TRC_COERCION] Impl task_01")
            head = _git(repo, "rev-parse", "HEAD")
            return (
                0,
                f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                "",
            )
        head = _git(repo, "rev-parse", "HEAD")
        rev = {
            "task_id": "task_01",
            "pass": 1,
            "verdict": "CHANGES_REQUESTED",
            "head_sha": head,
            "done_gate": "PASS",
            "blockers": [],
            "observations": [{"id": "OBS-1", "file": "src/a.py", "summary": "Nit"}],
        }
        return 0, f"```json\n{json.dumps(rev)}\n```\n", ""

    with patch.object(runner.dispatcher, "dispatch", side_effect=stub_dispatch):
        assert runner._execute_single_task("task_01")

    assert calls == ["programmer", "ai_architect_reviewer"]
    assert (repo / ".devtool" / "features" / "done" / "task_01.md").is_file()
    notes = _read_audit_notes(
        repo / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
    )
    assert len(notes) == 1
    assert notes[0]["coerced_from_non_blocking"] is True
    assert notes[0]["observations"][0]["id"] == "OBS-1"


def test_trc_st_04_headless_runner_caps_passes_and_finalizes_on_pass2_residual(
    tmp_path: Path,
) -> None:
    """[TRC-ST-04] Headless runner caps passes at 2 and finalizes on Pass 2 completion when done_gate is PASS."""
    epic = "trc_st04"
    repo, _ = _seed_epic_repo(
        tmp_path, "repo_st04", epic, tasks={"task_01": ["src/a.py"]}
    )
    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    impl_prompts: list[str] = []
    rev_prompts: list[str] = []

    def stub_dispatch(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        persona, _ = _persona_from_cli_args(cli, args)
        if persona == "programmer":
            impl_prompts.append(prompt)
            pass_num = len(impl_prompts)
            (repo / "src" / "a.py").write_text(f"VAL = {pass_num}\n", encoding="utf-8")
            _git(repo, "add", "src/a.py")
            _git(repo, "commit", "-q", "-m", f"[TRC_ST04] Impl attempt {pass_num}")
            head = _git(repo, "rev-parse", "HEAD")
            out = {
                "task_id": "task_01",
                "status": "DONE",
                "head_sha": head,
                "verify": "PASS",
                "finalized": False,
            }
            return 0, f"```json\n{json.dumps(out)}\n```\n", ""

        rev_prompts.append(prompt)
        pass_num = len(rev_prompts)
        head = _git(repo, "rev-parse", "HEAD")
        blocker_id = f"BLK-{pass_num}"
        rev_out = {
            "task_id": "task_01",
            "pass": pass_num,
            "verdict": "CHANGES_REQUESTED",
            "head_sha": head,
            "done_gate": "PASS",
            "blockers": [
                {
                    "id": blocker_id,
                    "category": "BDD_VIOLATION",
                    "file": "src/a.py",
                    "summary": f"Finding {blocker_id}",
                }
            ],
            "observations": [],
        }
        return 0, f"```json\n{json.dumps(rev_out)}\n```\n", ""

    with patch.object(runner.dispatcher, "dispatch", side_effect=stub_dispatch):
        assert runner._execute_single_task("task_01"), runner.state.last_error

    assert len(impl_prompts) == 2
    assert len(rev_prompts) == 2
    assert "Delta-Only" in rev_prompts[1]
    assert "BLK-1" in rev_prompts[1]
    assert (repo / ".devtool" / "features" / "done" / "task_01.md").is_file()
    assert _git(repo, "status", "--porcelain") == ""

    notes = _read_audit_notes(
        repo / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
    )
    assert len(notes) == 1
    assert notes[0]["event"] == "pass2_residual_logged_on_cap"
    assert notes[0]["task_id"] == "task_01"
    assert notes[0]["blockers"][0]["id"] == "BLK-2"

    # Reject A1 finalization if Pass 2 has done_gate="FAIL", mismatched head_sha, or wrong task_id.
    for bad_override in (
        {"done_gate": "FAIL"},
        {"head_sha": "zzz999"},
        {"task_id": "other_task"},
    ):
        label = next(iter(bad_override))
        bad_repo, _ = _seed_epic_repo(
            tmp_path, f"repo_st04_bad_{label}", epic, tasks={"task_01": ["src/a.py"]}
        )
        bad_runner = lifecycle_runner.LifecycleRunner(root=bad_repo, epic_slug=epic)
        bad_rev_count = 0

        def bad_dispatch(
            cli: str,
            args: list[str],
            prompt: str,
            _repo: Path = bad_repo,
            _ov: dict[str, str] = bad_override,
        ) -> tuple[int, str, str]:
            nonlocal bad_rev_count
            _ = prompt
            persona, _ = _persona_from_cli_args(cli, args)
            if persona == "programmer":
                head = _git(_repo, "rev-parse", "HEAD")
                return (
                    0,
                    f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                    "",
                )
            bad_rev_count += 1
            head = _git(_repo, "rev-parse", "HEAD")
            payload: dict[str, Any] = {
                "task_id": "task_01",
                "pass": bad_rev_count,
                "verdict": "CHANGES_REQUESTED",
                "head_sha": head,
                "done_gate": "PASS",
                "blockers": [{"id": "BLK-1", "summary": "Fix it"}],
                "observations": [],
            }
            if bad_rev_count == 2:
                payload.update(_ov)
            return 0, f"```json\n{json.dumps(payload)}\n```\n", ""

        with patch.object(bad_runner.dispatcher, "dispatch", side_effect=bad_dispatch):
            assert not bad_runner._execute_single_task("task_01")
        assert not (bad_repo / ".devtool" / "features" / "done" / "task_01.md").exists()
        assert not (
            bad_repo / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
        ).exists()


def test_trc_fr_03_unparseable_reviewer_output_fails_closed(tmp_path: Path) -> None:
    """[TRC-FR-03] Unparseable or missing task-reviewer JSON fails closed without coercion."""
    normalized_bad = manage_worker_pool.normalize_task_review_payload(
        {
            "task_id": "task_01",
            "verdict": "MAYBE",
            "done_gate": "PASS",
            "blockers": [],
            "observations": [],
        }
    )
    assert normalized_bad["valid"] is False
    assert normalized_bad["verdict"] == "UNPARSEABLE"
    assert normalized_bad["coerced_from_non_blocking"] is False

    epic = "trc_fr03"
    for case_name, raw_stdout in (
        ("no_json", "Looks fine overall, no fenced JSON block provided.\n"),
        ("malformed_json", "Review output:\n```json\n{not valid json}\n```\n"),
    ):
        repo, _ = _seed_epic_repo(
            tmp_path, f"repo_fr03_{case_name}", epic, tasks={"task_01": ["src/a.py"]}
        )
        runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
        impl_prompts: list[str] = []
        rev_prompts: list[str] = []

        def stub_dispatch(
            cli: str,
            args: list[str],
            prompt: str,
            _repo: Path = repo,
            _raw: str = raw_stdout,
            _impl_prompts: list[str] = impl_prompts,
            _rev_prompts: list[str] = rev_prompts,
        ) -> tuple[int, str, str]:
            persona, _ = _persona_from_cli_args(cli, args)
            if persona == "programmer":
                _impl_prompts.append(prompt)
                head = _git(_repo, "rev-parse", "HEAD")
                return (
                    0,
                    f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                    "",
                )
            _rev_prompts.append(prompt)
            return 0, _raw, ""

        with patch.object(runner.dispatcher, "dispatch", side_effect=stub_dispatch):
            ok = runner._execute_single_task("task_01")

        assert not ok
        assert len(impl_prompts) == 2
        assert len(rev_prompts) == 2
        assert "verdict=UNPARSEABLE" in impl_prompts[1]
        assert (
            runner.state.last_error and "verdict=UNPARSEABLE" in runner.state.last_error
        )
        assert not (repo / ".devtool" / "features" / "done" / "task_01.md").exists()
        assert not (
            repo / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
        ).exists()


def test_trc_st_04_pool_batch_flushes_pass2_residual_audit_note_onto_epic_wt(
    tmp_path: Path,
) -> None:
    """[TRC-ST-04] Pool mode queues pass2_residual_logged_on_cap and commits it onto epic_wt after merge_slot."""
    epic = "trc_pool_res"
    repo, epic_wt = _seed_epic_repo(
        tmp_path,
        "repo_pool_res",
        epic,
        tasks={"task_01": ["src/a.py"]},
        with_epic_worktree=True,
    )
    main_head_before = _git(repo, "rev-parse", "main")
    runner = lifecycle_runner.LifecycleRunner(root=epic_wt, epic_slug=epic)
    runner.quota_gate = lambda *a, **kw: (True, "")
    impl_count = 0
    rev_count = 0

    def stub_dispatch(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        nonlocal impl_count, rev_count
        _ = prompt
        wt = Path(self_disp.worktree_dir)
        persona, _ = _persona_from_cli_args(cli, args)
        if persona == "programmer":
            impl_count += 1
            (wt / "src" / "a.py").write_text(f"A = {impl_count}\n", encoding="utf-8")
            _git(wt, "add", "src/a.py")
            _git(
                wt,
                "commit",
                "-q",
                "-m",
                f"[TRC_POOL_RES] Impl task_01 pass {impl_count}",
            )
            head = _git(wt, "rev-parse", "HEAD")
            return (
                0,
                f"```json\n{json.dumps({'task_id': 'task_01', 'slot': 1, 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                "",
            )
        rev_count += 1
        assert not (
            wt / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
        ).exists()
        head = _git(wt, "rev-parse", "HEAD")
        payload = {
            "task_id": "task_01",
            "pass": rev_count,
            "verdict": "CHANGES_REQUESTED",
            "head_sha": head,
            "done_gate": "PASS",
            "blockers": [{"id": f"BLK-{rev_count}", "summary": "Residual"}],
            "observations": [],
        }
        return 0, f"```json\n{json.dumps(payload)}\n```\n", ""

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=stub_dispatch,
    ):
        assert runner.step_implementation(), runner.state.last_error

    assert rev_count == 2
    assert (epic_wt / ".devtool" / "features" / "done" / "task_01.md").is_file()
    notes = _read_audit_notes(
        epic_wt / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
    )
    assert len(notes) == 1
    assert notes[0]["event"] == "pass2_residual_logged_on_cap"
    assert _git(epic_wt, "status", "--porcelain") == ""
    assert _git(repo, "rev-parse", "main") == main_head_before


def test_trc_st_04_custom_persona_limits_control_runner_attempts(
    tmp_path: Path,
) -> None:
    """[TRC-ST-04] Layered max_task_review_passes and max_fix_passes bound headless runner loops."""
    epic = "trc_custom"
    # Case 1: (1, 0) stops after 1 review pass when done_gate fails.
    repo1, _ = _seed_epic_repo(
        tmp_path, "repo_custom_1_0", epic, tasks={"task_01": ["src/a.py"]}
    )
    cfg1 = repo1 / ".agents" / "config" / "personas.json"
    cfg1.parent.mkdir(parents=True, exist_ok=True)
    cfg1.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "max_task_review_passes": 1,
                "max_fix_passes": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r1 = lifecycle_runner.LifecycleRunner(root=repo1, epic_slug=epic)
    calls1: list[str] = []

    def disp1(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        _ = prompt
        persona, _ = _persona_from_cli_args(cli, args)
        calls1.append(persona)
        head = _git(repo1, "rev-parse", "HEAD")
        if persona == "programmer":
            return (
                0,
                f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                "",
            )
        return (
            0,
            f"```json\n{json.dumps({'task_id': 'task_01', 'pass': 1, 'verdict': 'CHANGES_REQUESTED', 'head_sha': head, 'done_gate': 'FAIL', 'blockers': [{'id': 'BLK-1', 'summary': 'Gate failed'}], 'observations': []})}\n```\n",
            "",
        )

    with patch.object(r1.dispatcher, "dispatch", side_effect=disp1):
        assert not r1._execute_single_task("task_01")
    assert calls1 == ["programmer", "ai_architect_reviewer"]

    # Case 2: (3, 2) allows 2 fix passes and 3 review passes before finalizing.
    repo3, _ = _seed_epic_repo(
        tmp_path, "repo_custom_3_2", epic, tasks={"task_01": ["src/a.py"]}
    )
    cfg3 = repo3 / ".agents" / "config" / "personas.json"
    cfg3.parent.mkdir(parents=True, exist_ok=True)
    cfg3.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "max_task_review_passes": 3,
                "max_fix_passes": 2,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r3 = lifecycle_runner.LifecycleRunner(root=repo3, epic_slug=epic)
    calls3: list[str] = []
    rev_pass = 0

    def disp3(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        nonlocal rev_pass
        _ = prompt
        persona, _ = _persona_from_cli_args(cli, args)
        calls3.append(persona)
        if persona == "programmer":
            (repo3 / "src" / "a.py").write_text(
                f"V = {len(calls3)}\n", encoding="utf-8"
            )
            _git(repo3, "add", "src/a.py")
            _git(repo3, "commit", "-q", "-m", f"[TRC_CUSTOM] Step {len(calls3)}")
            head = _git(repo3, "rev-parse", "HEAD")
            return (
                0,
                f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                "",
            )
        rev_pass += 1
        head = _git(repo3, "rev-parse", "HEAD")
        if rev_pass < 3:
            rep: dict[str, Any] = {
                "task_id": "task_01",
                "pass": rev_pass,
                "verdict": "CHANGES_REQUESTED",
                "head_sha": head,
                "done_gate": "PASS",
                "blockers": [{"id": f"BLK-{rev_pass}", "summary": "Needs fix"}],
                "observations": [],
            }
        else:
            rep = {
                "task_id": "task_01",
                "pass": 3,
                "verdict": "APPROVED",
                "head_sha": head,
                "done_gate": "PASS",
                "blockers": [],
                "observations": [],
            }
        return 0, f"```json\n{json.dumps(rep)}\n```\n", ""

    with patch.object(r3.dispatcher, "dispatch", side_effect=disp3):
        assert r3._execute_single_task("task_01")
    assert calls3 == [
        "programmer",
        "ai_architect_reviewer",
        "programmer",
        "ai_architect_reviewer",
        "programmer",
        "ai_architect_reviewer",
    ]
    assert (repo3 / ".devtool" / "features" / "done" / "task_01.md").is_file()

    # Case 3: (2, 0) fails closed on Pass 1 CHANGES_REQUESTED with real blocker (no pass2_residual_logged_on_cap).
    repo0, _ = _seed_epic_repo(
        tmp_path, "repo_custom_2_0", epic, tasks={"task_01": ["src/a.py"]}
    )
    cfg0 = repo0 / ".agents" / "config" / "personas.json"
    cfg0.parent.mkdir(parents=True, exist_ok=True)
    cfg0.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "max_task_review_passes": 2,
                "max_fix_passes": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    r0 = lifecycle_runner.LifecycleRunner(root=repo0, epic_slug=epic)
    calls0: list[str] = []

    def disp0(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        _ = prompt
        persona, _ = _persona_from_cli_args(cli, args)
        calls0.append(persona)
        head = _git(repo0, "rev-parse", "HEAD")
        if persona == "programmer":
            return (
                0,
                f"```json\n{json.dumps({'task_id': 'task_01', 'status': 'DONE', 'head_sha': head, 'verify': 'PASS', 'finalized': False})}\n```\n",
                "",
            )
        return (
            0,
            f"```json\n{json.dumps({'task_id': 'task_01', 'pass': 1, 'verdict': 'CHANGES_REQUESTED', 'head_sha': head, 'done_gate': 'PASS', 'blockers': [{'id': 'BLK-1', 'summary': 'Real blocker'}], 'observations': []})}\n```\n",
            "",
        )

    with patch.object(r0.dispatcher, "dispatch", side_effect=disp0):
        assert not r0._execute_single_task("task_01")
    assert calls0 == ["programmer", "ai_architect_reviewer"]
    assert not (repo0 / ".devtool" / "features" / "done" / "task_01.md").exists()
    audit0 = repo0 / ".devtool" / "epic" / epic / "review_audit_notes.jsonl"
    assert (
        not audit0.exists()
        or "pass2_residual_logged_on_cap" not in audit0.read_text(encoding="utf-8")
    )


class TestTrcRunnerAcceptance_Integration:
    """Tier C integration provenance wrappers for TRC-HP-04 and TRC-ST-04."""

    def test_trc_hp_04_integration(self, tmp_path: Path) -> None:
        """[TRC-HP-04] Integration provenance wrapper for end-to-end runner parity."""
        test_trc_hp_04_end_to_end_runner_and_verify_registration(tmp_path)

    def test_trc_st_04_integration(self, tmp_path: Path) -> None:
        """[TRC-ST-04] Integration provenance wrapper for runner pass cap and pool audit flush."""
        test_trc_st_04_headless_runner_caps_passes_and_finalizes_on_pass2_residual(
            tmp_path / "headless"
        )
        test_trc_st_04_pool_batch_flushes_pass2_residual_audit_note_onto_epic_wt(
            tmp_path / "pool"
        )
