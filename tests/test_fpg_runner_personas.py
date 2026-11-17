"""Tests for four-persona lifecycle runner bindings, risk routing, checkpoints, and quota stops.

Covers BDD Scenarios:
- FPG-ST-02: High-risk findings go to the fix-planner and halt criteria escalate
- FPG-ST-03: Turn budget and low-quota stop at the next safe point
- FPG-ST-05: The runner dispatches the Architect task-reviewer when gating requires it and finalizes only on a SHA-bound PASS
- FPG-ST-06: Gate 4 runs in a fresh Programmer gate4-verifier on every attempt
- FPG-FR-03: An unavailable model halts with a checkpoint and a fallback command, never a retry
- FPG-FR-04: The runner checks quota before each wave
- FPG-FR-06: The runner halts and reports to the Human only when the whole agy pool is out of quota
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEV_IMPL_SCRIPTS = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
LIFECYCLE_SCRIPTS = REPO_ROOT / "skills" / "dev-lifecycle" / "resources" / "scripts"

for _p in (str(LIFECYCLE_SCRIPTS), str(SCRIPTS_DIR), str(DEV_IMPL_SCRIPTS)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


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


_state_envelope = _load_module("_state_envelope", SCRIPTS_DIR / "_state_envelope.py")
persona_config = _load_module("persona_config", SCRIPTS_DIR / "persona_config.py")
agy_dispatch = _load_module("agy_dispatch", SCRIPTS_DIR / "agy_dispatch.py")
dev_config = _load_module("dev_config", SCRIPTS_DIR / "dev_config.py")
lifecycle_runner = _load_module(
    "lifecycle_runner", LIFECYCLE_SCRIPTS / "lifecycle_runner.py"
)


@pytest.fixture(autouse=True)
def _isolate_host_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate HOME, REAL_HOME, profile env vars, and legacy env vars from host stores."""
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


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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


def _make_task_md(
    task_id: str,
    epic: str,
    *,
    allowed: list[str],
    blocked_by: list[str] | None = None,
    review_tier: str | None = None,
    labels: list[str] | None = None,
) -> str:
    tier_line = f'review_tier: "{review_tier}"\n' if review_tier else ""
    labels_val = json.dumps(labels or [])
    deps = (
        "Blocked by " + ", ".join(f"[{dep}]({dep}.md)" for dep in blocked_by) + "."
        if blocked_by
        else "None."
    )
    allowed_lines = "\n".join(f"- `{p}`" for p in allowed)
    return (
        f'---\nid: "{task_id}"\nstatus: "todo"\npriority: "high"\n'
        f'epic: "{epic}"\nlabels: {labels_val}\n{tier_line}---\n\n'
        f"# Task {task_id}\n\n"
        f"## Dependencies & Blockers\n\n{deps}\n\n"
        f"## Files\n\nAllowed files:\n{allowed_lines}\n"
    )


def _persona_from_cli_args(cli: str, args: list[str]) -> tuple[str, str]:
    """Infer persona/mode from argv built by persona_config.build_dispatch_argv."""
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


def _read_pending_decision(root: Path, epic_slug: str) -> dict[str, Any]:
    path = root / ".devtool" / "state" / "pending_decision.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data["decisions"][epic_slug])


def _read_events(root: Path, epic_slug: str) -> list[dict[str, Any]]:
    path = root / ".devtool" / "logs" / f"events_{epic_slug}.jsonl"
    if not path.is_file():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_fpg_st_02_high_risk_routes_to_fix_planner_and_escalates(
    tmp_path: Path,
) -> None:
    """[FPG-ST-02] High-risk findings go to the fix-planner and halt criteria escalate."""
    repo = tmp_path / "repo_planned"
    _init_git_repo(repo)
    epic = "demo_epic"
    epic_dir = repo / ".devtool" / "epic" / epic
    epic_dir.mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (epic_dir / f"{epic}.md").write_text("# HLD\n", encoding="utf-8")
    (epic_dir / "review_results.md").write_text(
        "# Cross-Model Review\n\n## Round 1\n\n"
        "| ID | Severity | File / Target | Problem | Status |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| CR-01 | Critical | `src/app.py:1` | Unbounded lock acquisition | Open |\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed repo")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    runner.quota_gate = lambda *_a, **_kw: 0

    triage_r1 = (
        "## Auto-Triage Gate\n\n"
        "- **Action**: AUTO_FIX_ELIGIBLE\n"
        "- **Round**: 1 / 3\n"
        "- **Directive**: 1 Critical finding.\n"
    )
    triage_r2 = (
        "## Auto-Triage Gate\n\n"
        "- **Action**: AUTO_PASS_CLEAN\n"
        "- **Round**: 2 / 3\n"
        "- **Directive**: 0 findings.\n"
    )

    recorded_dispatches: list[dict[str, Any]] = []
    plan_body = "# Fix Plan Round 1\n\n- Guard lock acquisition with timeout.\n"

    def planned_dispatch(
        cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        persona, mode = _persona_from_cli_args(cli, args)
        recorded_dispatches.append(
            {"persona": persona, "mode": mode, "args": list(args), "prompt": prompt}
        )
        if persona == "ai_architect_reviewer":
            summary = {
                "round": 1,
                "status": "PLANNED",
                "halt_criteria": [],
                "plan_markdown": plan_body,
            }
            return 0, f"Analysis\n```json\n{json.dumps(summary)}\n```\n", ""
        if "gate4-verifier" in prompt:
            head_sha = _git(repo, "rev-parse", "HEAD")
            verdict = {
                "candidate_sha": head_sha,
                "verdict": "PASS",
                "audit_exit": 0,
                "quality_check_report": "ok",
                "failures": [],
            }
            return 0, f"```json\n{json.dumps(verdict)}\n```\n", ""
        # review-fixer in apply-plan mode modifies src/app.py
        (repo / "src" / "app.py").write_text("x = 2\n", encoding="utf-8")
        return 0, '{"status": "FIXED"}', ""

    real_run = subprocess.run
    with patch("subprocess.run") as mock_sub:
        p1 = MagicMock(returncode=0, stdout=triage_r1, stderr="")
        p2 = MagicMock(returncode=0, stdout=triage_r2, stderr="")

        def route_run(cmd: Any, **kwargs: Any) -> Any:
            if isinstance(cmd, list) and cmd and cmd[0] in ("git", "ps"):
                return real_run(cmd, **kwargs)
            if isinstance(cmd, list) and any(
                "run_external_review.py" in str(c) for c in cmd
            ):
                if "triage" in cmd:
                    return p1 if runner.state.cross_model_round == 1 else p2
                return MagicMock(returncode=0, stdout="", stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_sub.side_effect = route_run
        with (
            patch.object(runner.dispatcher, "dispatch", side_effect=planned_dispatch),
            patch.object(runner, "_run_scoped_tests", return_value=(True, "ok")),
            patch.object(runner, "run_intermediate_check", return_value=(True, "ok")),
        ):
            ok = runner.step_cross_model_review()

    assert ok
    assert len(recorded_dispatches) >= 2
    assert recorded_dispatches[0]["persona"] == "ai_architect_reviewer"
    assert recorded_dispatches[0]["mode"] == "read-only"
    assert "fix-planner" in recorded_dispatches[0]["prompt"]
    assert recorded_dispatches[1]["persona"] == "programmer"
    assert "apply-plan" in recorded_dispatches[1]["prompt"]
    assert "review-fixer" in recorded_dispatches[1]["prompt"]
    plan_file = epic_dir / "fix_plan_round1.md"
    assert plan_file.is_file()
    assert plan_file.read_text(encoding="utf-8").strip() == plan_body.strip()
    commit_files = _git(repo, "log", "-n", "3", "--name-only", "--format=")
    assert "fix_plan_round1.md" in commit_files

    # Test each of the 5 halt criteria + an out-of-tuple criterion + unparseable output
    criteria = (
        "CRITICAL_CONFLICT",
        "Debatable",
        "SHARED_CONTRACT_CONFLICT",
        "FIX_LOOP",
        "MAX_ROUNDS_CRITICAL_REMAINING",
        "CUSTOM_OUT_OF_TUPLE_REASON",
    )
    for idx, criterion in enumerate(criteria):
        esc_repo = tmp_path / f"repo_esc_{idx}"
        _init_git_repo(esc_repo)
        esc_epic_dir = esc_repo / ".devtool" / "epic" / epic
        esc_epic_dir.mkdir(parents=True, exist_ok=True)
        (esc_repo / "src").mkdir(parents=True, exist_ok=True)
        (esc_repo / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
        (esc_epic_dir / "review_results.md").write_text(
            "## Round 1\n\n| ID | Severity | File / Target | Problem | Status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| CR-01 | Critical | `src/app.py:1` | Escalation case | Open |\n",
            encoding="utf-8",
        )
        _git(esc_repo, "add", "-A")
        _git(esc_repo, "commit", "-q", "-m", "[DEMO] Seed esc repo")

        esc_runner = lifecycle_runner.LifecycleRunner(root=esc_repo, epic_slug=epic)
        esc_runner.quota_gate = lambda *_a, **_kw: 0
        esc_dispatches: list[str] = []

        def esc_dispatch(
            cli: str,
            args: list[str],
            prompt: str,
            _crit: str = criterion,
            _esc: list[str] = esc_dispatches,
        ) -> tuple[int, str, str]:
            persona, _ = _persona_from_cli_args(cli, args)
            _esc.append(persona)
            summary = {
                "round": 1,
                "status": "ESCALATE",
                "halt_criteria": [_crit],
                "plan_markdown": "",
            }
            return 0, f"```json\n{json.dumps(summary)}\n```\n", ""

        real_esc_run = subprocess.run
        with patch("subprocess.run") as mock_sub:
            triage_proc = MagicMock(returncode=0, stdout=triage_r1, stderr="")

            def route_esc_run(
                cmd: Any,
                _real: Any = real_esc_run,
                _tp: Any = triage_proc,
                **kwargs: Any,
            ) -> Any:
                if isinstance(cmd, list) and cmd and cmd[0] in ("git", "ps"):
                    return _real(cmd, **kwargs)
                if isinstance(cmd, list) and any(
                    "run_external_review.py" in str(c) for c in cmd
                ):
                    return _tp
                return MagicMock(returncode=0, stdout="", stderr="")

            mock_sub.side_effect = route_esc_run
            with patch.object(
                esc_runner.dispatcher, "dispatch", side_effect=esc_dispatch
            ):
                esc_ok = esc_runner.step_cross_model_review()

        assert not esc_ok
        assert esc_runner.state.halt_reason == "FIX_PLAN_ESCALATE"
        assert esc_runner.state.active_stage == lifecycle_runner.StageName.HALTED.value
        assert esc_dispatches == ["ai_architect_reviewer"]
        decision = _read_pending_decision(esc_repo, epic)
        assert decision["kind"] == "blocker"
        assert criterion in decision["reason"]

    # Missing/unparseable JSON block from fix-planner escalates with UNPARSEABLE
    unp_repo = tmp_path / "repo_unparseable"
    _init_git_repo(unp_repo)
    unp_runner = lifecycle_runner.LifecycleRunner(root=unp_repo, epic_slug=epic)
    with patch.object(
        unp_runner.dispatcher, "dispatch", return_value=(0, "prose without json", "")
    ):
        status_u, criteria_u, _ = unp_runner._draft_fix_plan(1, "find")
    assert status_u == "ESCALATE"
    assert criteria_u == ["UNPARSEABLE"]


def test_fpg_st_03_turn_budget_and_low_quota_stop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[FPG-ST-03] Turn budget triggers at N dispatches and low-quota stops at the next safe point."""
    real_home = tmp_path / "_isolated_home"
    _write_json(
        real_home / ".d3nexus" / "personas.json",
        {
            "schema_version": 1,
            "checkpoint_policy": {"max_orchestrator_turns_before_checkpoint": 4},
        },
    )

    def _setup_three_wave_repo(name: str) -> Path:
        repo = tmp_path / name
        _init_git_repo(repo)
        _copy_dev_impl_scripts(repo)
        (repo / "src").mkdir(parents=True, exist_ok=True)
        features = repo / ".devtool" / "features"
        features.mkdir(parents=True, exist_ok=True)
        epic = "demo_epic"
        (repo / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
        (repo / ".devtool" / "epic" / epic / f"{epic}.md").write_text(
            "# HLD\n", encoding="utf-8"
        )

        # 3 waves of 2 tasks each; w1_t1 and w2_t1 have review_tier=full -> 8 total dispatches
        tasks = [
            ("task_01_w1a", "src/w1a.py", [], "full"),
            ("task_02_w1b", "src/w1b.py", [], None),
            ("task_03_w2a", "src/w2a.py", ["task_01_w1a", "task_02_w1b"], "full"),
            ("task_04_w2b", "src/w2b.py", ["task_01_w1a", "task_02_w1b"], None),
            ("task_05_w3a", "src/w3a.py", ["task_03_w2a", "task_04_w2b"], None),
            ("task_06_w3b", "src/w3b.py", ["task_03_w2a", "task_04_w2b"], None),
        ]
        for tid, mod, deps, tier in tasks:
            (repo / mod).write_text(f"{tid} = 0\n", encoding="utf-8")
            (features / f"{tid}.md").write_text(
                _make_task_md(
                    tid, epic, allowed=[mod], blocked_by=deps, review_tier=tier
                ),
                encoding="utf-8",
            )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "[DEMO] 3 waves")
        return repo

    # Part 1: turn_budget checkpoint after dispatches 4 and 8 with low-quota OFF
    repo1 = _setup_three_wave_repo("repo_budget")
    runner1 = lifecycle_runner.LifecycleRunner(root=repo1, epic_slug="demo_epic")
    runner1.quota_gate = lambda *_a, **_kw: 0
    events_log_1: list[tuple[int, str]] = []
    dispatch_count_1 = 0
    returned_count_1 = 0
    lock_1 = threading.Lock()
    real_cp_writer = runner1.checkpoint_writer

    def spy_cp_1(root: Path, epic_slug: str, cp: dict[str, Any]) -> dict[str, Any]:
        nonlocal returned_count_1
        ev_name = str(cp.get("event"))
        with lock_1:
            if ev_name == "subagent_returned":
                returned_count_1 += 1
            events_log_1.append((returned_count_1, ev_name))
        return real_cp_writer(root, epic_slug, cp)

    runner1.checkpoint_writer = spy_cp_1

    def ok_dispatch_1(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        nonlocal dispatch_count_1
        with lock_1:
            dispatch_count_1 += 1
        persona, mode = _persona_from_cli_args(cli, args)
        if persona == "ai_architect_reviewer" and mode == "read-only":
            return (
                0,
                '```json\n{"task_id": "t", "verdict": "PASS", "head_sha": "sha_ok", "done_gate": "PASS", "findings": []}\n```\n',
                "",
            )
        wt = self_disp.worktree_dir
        for mod in ("w1a", "w1b", "w2a", "w2b", "w3a", "w3b"):
            if mod in prompt:
                (wt / "src" / f"{mod}.py").write_text(f"{mod} = 1\n", encoding="utf-8")
        return (
            0,
            '```json\n{"task_id": "t", "slot": 1, "status": "DONE", "head_sha": "sha_ok", "verify": "PASS", "changed_files": [], "non_test_modules_changed": 1, "review_tier": "standard", "labels": [], "finalized": false}\n```\n',
            "",
        )

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=ok_dispatch_1,
    ):
        assert runner1.step_implementation()

    assert dispatch_count_1 == 8
    turn_budget_at = [cnt for cnt, ev in events_log_1 if ev == "turn_budget"]
    assert turn_budget_at == [4, 8]
    assert sum(1 for _, ev in events_log_1 if ev == "wave_merged") == 3

    # Part 2: low-quota switched ON after wave 1 merges and before wave 2 starts
    repo2 = _setup_three_wave_repo("repo_lq_before_w2")
    monkeypatch.setenv("AGY_PROFILE", "testprof")
    dev_config.cmd_low_quota(
        repo2, action="off", profile="testprof", real_home=real_home
    )
    runner2 = lifecycle_runner.LifecycleRunner(root=repo2, epic_slug="demo_epic")
    dispatched_2: list[str] = []
    quota_calls_2 = 0

    def gate_enable_before_w2(*_a: Any, **_kw: Any) -> int:
        nonlocal quota_calls_2
        quota_calls_2 += 1
        if quota_calls_2 == 2:
            dev_config.cmd_low_quota(
                repo2, action="on", profile="testprof", real_home=real_home
            )
        return 0

    runner2.quota_gate = gate_enable_before_w2

    def ok_dispatch_2(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        persona, mode = _persona_from_cli_args(cli, args)
        if persona == "programmer":
            for tid in (
                "task_01_w1a",
                "task_02_w1b",
                "task_03_w2a",
                "task_04_w2b",
                "task_05_w3a",
                "task_06_w3b",
            ):
                if tid in prompt:
                    dispatched_2.append(tid)
        if persona == "ai_architect_reviewer" and mode == "read-only":
            return (
                0,
                '```json\n{"task_id": "t", "verdict": "PASS", "head_sha": "sha2", "done_gate": "PASS", "findings": []}\n```\n',
                "",
            )
        return (
            0,
            '```json\n{"task_id": "t", "slot": 1, "status": "DONE", "head_sha": "sha2", "verify": "PASS", "changed_files": [], "non_test_modules_changed": 1, "review_tier": "standard", "labels": [], "finalized": false}\n```\n',
            "",
        )

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=ok_dispatch_2,
    ):
        ok2 = runner2.step_implementation()

    assert not ok2
    assert runner2.state.halt_reason == "LOW_QUOTA_STOP"
    assert set(dispatched_2) == {"task_01_w1a", "task_02_w1b"}
    hb2 = _state_envelope.read_epic_heartbeat(repo2, "demo_epic")
    assert hb2["checkpoint"]["event"] == "low_quota_stop"
    assert _read_pending_decision(repo2, "demo_epic")["kind"] == "blocker"

    # Part 3: low-quota switched ON while wave 2 is executing -> wave 2 completes & merges, no wave 3 dispatched
    repo3 = _setup_three_wave_repo("repo_lq_during_w2")
    dev_config.cmd_low_quota(
        repo3, action="off", profile="testprof", real_home=real_home
    )
    runner3 = lifecycle_runner.LifecycleRunner(root=repo3, epic_slug="demo_epic")
    runner3.quota_gate = lambda *_a, **_kw: 0
    dispatched_3: list[str] = []

    def ok_dispatch_3(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        persona, mode = _persona_from_cli_args(cli, args)
        if persona == "programmer":
            for tid in (
                "task_01_w1a",
                "task_02_w1b",
                "task_03_w2a",
                "task_04_w2b",
                "task_05_w3a",
                "task_06_w3b",
            ):
                if tid in prompt:
                    dispatched_3.append(tid)
                    if tid == "task_03_w2a":
                        dev_config.cmd_low_quota(
                            repo3, action="on", profile="testprof", real_home=real_home
                        )
        if persona == "ai_architect_reviewer" and mode == "read-only":
            return (
                0,
                '```json\n{"task_id": "t", "verdict": "PASS", "head_sha": "sha3", "done_gate": "PASS", "findings": []}\n```\n',
                "",
            )
        return (
            0,
            '```json\n{"task_id": "t", "slot": 1, "status": "DONE", "head_sha": "sha3", "verify": "PASS", "changed_files": [], "non_test_modules_changed": 1, "review_tier": "standard", "labels": [], "finalized": false}\n```\n',
            "",
        )

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=ok_dispatch_3,
    ):
        ok3 = runner3.step_implementation()

    assert not ok3
    assert runner3.state.halt_reason == "LOW_QUOTA_STOP"
    assert set(dispatched_3) == {
        "task_01_w1a",
        "task_02_w1b",
        "task_03_w2a",
        "task_04_w2b",
    }
    assert "task_03_w2a" in runner3.state.completed_tasks
    assert "task_04_w2b" in runner3.state.completed_tasks
    events3 = [
        ev.get("event")
        for ev in _read_events(repo3, "demo_epic")
        if ev.get("category") == "checkpoint"
    ]
    assert events3.count("wave_merged") == 2
    assert events3[-1] == "low_quota_stop"


def test_fpg_st_05_per_task_architect_review_and_sha_binding(
    tmp_path: Path,
) -> None:
    """[FPG-ST-05] Runner dispatches Architect task-reviewer when gated and finalizes only on SHA-bound PASS."""
    repo = tmp_path / "repo_st05"
    _init_git_repo(repo)
    _copy_dev_impl_scripts(repo)
    epic = "demo_epic"
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "epic" / epic / f"{epic}.md").write_text(
        "# HLD\n", encoding="utf-8"
    )
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "small.py").write_text("S = 1\n", encoding="utf-8")
    (repo / "src" / "full.py").write_text("F = 1\n", encoding="utf-8")
    (features / "t_small.md").write_text(
        _make_task_md("t_small", epic, allowed=["src/small.py"]),
        encoding="utf-8",
    )
    (features / "t_full.md").write_text(
        _make_task_md("t_full", epic, allowed=["src/full.py"], review_tier="full"),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed ST-05")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    calls: list[dict[str, Any]] = []

    def pass_dispatch(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        persona, mode = _persona_from_cli_args(cli, args)
        role = (
            "task-reviewer"
            if persona == "ai_architect_reviewer"
            else "task-implementer"
        )
        calls.append({"persona": persona, "role": role, "mode": mode, "prompt": prompt})
        if persona == "ai_architect_reviewer":
            out = {
                "task_id": "t_full",
                "verdict": "PASS",
                "head_sha": "abc123",
                "done_gate": "PASS",
                "findings": [],
            }
            return 0, f"```json\n{json.dumps(out)}\n```\n", ""
        out = {
            "task_id": "t_small" if "t_small" in prompt else "t_full",
            "slot": 1,
            "status": "DONE",
            "head_sha": "abc123",
            "verify": "PASS",
            "changed_files": ["src/small.py"]
            if "t_small" in prompt
            else ["src/full.py"],
            "non_test_modules_changed": 1,
            "review_tier": "standard" if "t_small" in prompt else "full",
            "labels": [],
            "finalized": False,
        }
        return 0, f"```json\n{json.dumps(out)}\n```\n", ""

    with patch.object(runner.dispatcher, "dispatch", side_effect=pass_dispatch):
        assert runner._execute_single_task("t_small")
        assert len(calls) == 1
        assert (features / "done" / "t_small.md").is_file()

        calls.clear()
        assert runner._execute_single_task("t_full")
        assert len(calls) == 2
        assert calls[1]["persona"] == "ai_architect_reviewer"
        assert calls[1]["mode"] == "read-only"
        assert "task-reviewer" in calls[1]["prompt"]
        assert (features / "done" / "t_full.md").is_file()
        assert "t_full" in _git(repo, "log", "-n", "1", "--format=%s")

    # Reviewer returns mismatched SHA zzz999 -> NOT marked done, programmer re-dispatched
    repo_bad = tmp_path / "repo_st05_bad"
    _init_git_repo(repo_bad)
    _copy_dev_impl_scripts(repo_bad)
    features_bad = repo_bad / ".devtool" / "features"
    features_bad.mkdir(parents=True, exist_ok=True)
    (repo_bad / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
    (repo_bad / ".devtool" / "epic" / epic / f"{epic}.md").write_text(
        "# HLD\n", encoding="utf-8"
    )
    (repo_bad / "src").mkdir(parents=True, exist_ok=True)
    (repo_bad / "src" / "full.py").write_text("F = 1\n", encoding="utf-8")
    (features_bad / "t_full.md").write_text(
        _make_task_md("t_full", epic, allowed=["src/full.py"], review_tier="full"),
        encoding="utf-8",
    )
    _git(repo_bad, "add", "-A")
    _git(repo_bad, "commit", "-q", "-m", "[DEMO] Seed bad SHA")

    for bad_reply in (
        {
            "task_id": "t_full",
            "verdict": "PASS",
            "head_sha": "zzz999",
            "done_gate": "PASS",
            "findings": [],
        },
        {
            "task_id": "t_full",
            "verdict": "FAIL",
            "head_sha": "abc123",
            "done_gate": "FAIL",
            "findings": ["bug"],
        },
    ):
        runner_bad = lifecycle_runner.LifecycleRunner(root=repo_bad, epic_slug=epic)
        bad_calls: list[str] = []

        def bad_dispatch(
            cli: str,
            args: list[str],
            prompt: str,
            _reply: dict[str, Any] = bad_reply,
            _calls: list[str] = bad_calls,
        ) -> tuple[int, str, str]:
            persona, _ = _persona_from_cli_args(cli, args)
            _calls.append(persona)
            if persona == "ai_architect_reviewer":
                return 0, f"```json\n{json.dumps(_reply)}\n```\n", ""
            out = {
                "task_id": "t_full",
                "slot": 1,
                "status": "DONE",
                "head_sha": "abc123",
                "verify": "PASS",
                "changed_files": ["src/full.py"],
                "non_test_modules_changed": 1,
                "review_tier": "full",
                "labels": [],
                "finalized": False,
            }
            return 0, f"```json\n{json.dumps(out)}\n```\n", ""

        with patch.object(runner_bad.dispatcher, "dispatch", side_effect=bad_dispatch):
            ok_bad = runner_bad._execute_single_task("t_full")

        assert not ok_bad
        assert not (features_bad / "done" / "t_full.md").exists()
        assert (features_bad / "t_full.md").is_file()
        assert bad_calls.count("programmer") >= 2

    # Standard task touching > 2 non-test modules in git diff triggers task-reviewer
    (features / "t_many.md").write_text(
        _make_task_md("t_many", epic, allowed=["src/m1.py", "src/m2.py", "src/m3.py"]),
        encoding="utf-8",
    )
    _git(repo, "add", str(features / "t_many.md"))
    _git(repo, "commit", "-q", "-m", "[DEMO] Add t_many")
    many_calls: list[str] = []

    def many_dispatch(cli: str, args: list[str], prompt: str) -> tuple[int, str, str]:
        persona, _ = _persona_from_cli_args(cli, args)
        many_calls.append(persona)
        if persona == "ai_architect_reviewer":
            head = _git(repo, "rev-parse", "HEAD")
            return (
                0,
                f'```json\n{{"task_id": "t_many", "verdict": "PASS", "head_sha": "{head}", "done_gate": "PASS", "findings": []}}\n```\n',
                "",
            )
        for idx in (1, 2, 3):
            (repo / "src" / f"m{idx}.py").write_text(f"M{idx} = 1\n", encoding="utf-8")
        _git(repo, "add", "src/m1.py", "src/m2.py", "src/m3.py")
        _git(repo, "commit", "-q", "-m", "[DEMO] Impl 3 modules")
        head = _git(repo, "rev-parse", "HEAD")
        return (
            0,
            f'```json\n{{"task_id": "t_many", "slot": 1, "status": "DONE", "head_sha": "{head}", "verify": "PASS", "changed_files": ["src/m1.py"], "non_test_modules_changed": 1, "review_tier": "standard", "labels": [], "finalized": false}}\n```\n',
            "",
        )

    with patch.object(runner.dispatcher, "dispatch", side_effect=many_dispatch):
        assert runner._execute_single_task("t_many")
    assert many_calls == ["programmer", "ai_architect_reviewer"]
    assert (features / "done" / "t_many.md").is_file()


def test_fpg_st_06_gate4_fresh_verifier_and_sha_binding(tmp_path: Path) -> None:
    """[FPG-ST-06] Gate 4 runs in a fresh Programmer gate4-verifier on every attempt."""
    repo = tmp_path / "repo_st06"
    _init_git_repo(repo)
    epic = "demo_epic"
    epic_dir = repo / ".devtool" / "epic" / epic
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{epic}.md").write_text(
        "# HLD\nIntegration results: pytest -q -> build/res.xml\n",
        encoding="utf-8",
    )
    (epic_dir / "bdd_scenarios.md").write_text("# BDD\n", encoding="utf-8")
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed ST-06")
    head_sha = _git(repo, "rev-parse", "HEAD")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    dispatches: list[dict[str, Any]] = []
    ledger_calls: list[tuple[int, str]] = []
    gate4_commands_run_directly: list[Any] = []
    real_sub_run = subprocess.run

    def spy_sub_run(cmd: Any, **kwargs: Any) -> Any:
        if isinstance(cmd, list) and cmd and cmd[0] in ("git", "ps"):
            return real_sub_run(cmd, **kwargs)
        gate4_commands_run_directly.append(cmd)
        return MagicMock(returncode=0, stdout="", stderr="")

    def verifier_then_fix_then_pass(
        cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        persona, mode = _persona_from_cli_args(cli, args)
        role = (
            "gate4-verifier"
            if "gate4-verifier" in prompt
            else ("review-fixer" if "review-fixer" in prompt else "other")
        )
        dispatches.append(
            {"persona": persona, "mode": mode, "role": role, "prompt": prompt}
        )
        verifier_idx = sum(1 for d in dispatches if d["role"] == "gate4-verifier")
        if role == "gate4-verifier" and verifier_idx == 1:
            rep = {
                "candidate_sha": head_sha,
                "verdict": "FAIL",
                "audit_exit": 1,
                "quality_check_report": "fail",
                "failures": ["lint error"],
            }
            return 0, f"```json\n{json.dumps(rep)}\n```\n", ""
        if role == "review-fixer":
            return 0, '{"status": "FIXED"}', ""
        rep = {
            "candidate_sha": head_sha,
            "verdict": "PASS",
            "audit_exit": 0,
            "quality_check_report": "ok",
            "failures": [],
        }
        return 0, f"```json\n{json.dumps(rep)}\n```\n", ""

    with (
        patch("subprocess.run", side_effect=spy_sub_run),
        patch.object(
            runner.dispatcher, "dispatch", side_effect=verifier_then_fix_then_pass
        ),
        patch.object(
            runner,
            "sync_gate_ledger",
            side_effect=lambda g, msg: ledger_calls.append((g, msg)) or True,
        ),
        patch.object(runner, "_run_scoped_tests", return_value=(True, "ok")),
    ):
        passed, _ = runner.run_gate4()

    assert passed
    verifier_calls = [d for d in dispatches if d["role"] == "gate4-verifier"]
    assert len(verifier_calls) == 2
    assert all(
        d["persona"] == "programmer" and d["mode"] == "write" for d in verifier_calls
    )
    assert "generate_smoke_checklist.py" in verifier_calls[0]["prompt"]
    assert "verify.sh" in verifier_calls[0]["prompt"]
    assert any(d["role"] == "review-fixer" for d in dispatches)
    assert gate4_commands_run_directly == []
    assert len(ledger_calls) == 1
    assert ledger_calls[0][0] == 4

    # Mismatched candidate_sha must NOT record Gate 4 and must dispatch a new gate4-verifier
    dispatches_2: list[str] = []
    ledger_calls_2: list[int] = []

    def bad_sha_then_good_sha(
        cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        dispatches_2.append(prompt)
        sha_to_use = "0000000deadbeef" if len(dispatches_2) == 1 else head_sha
        rep = {
            "candidate_sha": sha_to_use,
            "verdict": "PASS",
            "audit_exit": 0,
            "quality_check_report": "ok",
            "failures": [],
        }
        return 0, f"```json\n{json.dumps(rep)}\n```\n", ""

    with (
        patch.object(runner.dispatcher, "dispatch", side_effect=bad_sha_then_good_sha),
        patch.object(
            runner,
            "sync_gate_ledger",
            side_effect=lambda g, _m: ledger_calls_2.append(g) or True,
        ),
    ):
        passed2, _ = runner.run_gate4()

    assert passed2
    assert len(dispatches_2) == 2
    assert ledger_calls_2 == [4]


def test_fpg_fr_03_unavailable_model_halts_without_retry(tmp_path: Path) -> None:
    """[FPG-FR-03] Unavailable model writes checkpoint, records blocker with fallback command, and halts."""
    repo = tmp_path / "repo_fr03"
    _init_git_repo(repo)
    _copy_dev_impl_scripts(repo)
    epic = "demo_epic"
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
    (repo / "src" / "b.py").write_text("B = 1\n", encoding="utf-8")
    (features / "task_01.md").write_text(
        _make_task_md("task_01", epic, allowed=["src/a.py"]),
        encoding="utf-8",
    )
    (features / "task_02.md").write_text(
        _make_task_md("task_02", epic, allowed=["src/b.py"], blocked_by=["task_01"]),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed FR-03")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    runner.quota_gate = lambda *_a, **_kw: 0
    order_log: list[str] = []
    real_cp = runner.checkpoint_writer
    real_pd = _state_envelope.record_pending_decision

    def spy_cp(root: Path, epic_slug: str, cp: dict[str, Any]) -> dict[str, Any]:
        order_log.append(f"cp:{cp.get('event')}")
        return real_cp(root, epic_slug, cp)

    def spy_pd(*args: Any, **kwargs: Any) -> dict[str, Any]:
        order_log.append(f"pd:{kwargs.get('kind')}")
        return real_pd(*args, **kwargs)

    runner.checkpoint_writer = spy_cp
    dispatch_attempts = 0

    def fail_resource_exhausted(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        nonlocal dispatch_attempts
        dispatch_attempts += 1
        return 1, "", "RESOURCE_EXHAUSTED: quota exceeded"

    with (
        patch.object(
            lifecycle_runner.ModelDispatcher,
            "dispatch",
            autospec=True,
            side_effect=fail_resource_exhausted,
        ),
        patch.object(_state_envelope, "record_pending_decision", side_effect=spy_pd),
    ):
        ok = runner.step_implementation()

    assert not ok
    assert dispatch_attempts == 1
    assert runner.state.halt_reason == "MODEL_UNAVAILABLE"
    assert runner.state.active_stage == lifecycle_runner.StageName.HALTED.value
    assert order_log.index("cp:model_unavailable") < order_log.index("pd:blocker")
    decision = _read_pending_decision(repo, epic)
    assert decision["kind"] == "blocker"
    assert "/d3nexus:dev-config set programmer claude-sonnet" in decision["reason"]


def test_fpg_fr_04_quota_gate_checked_before_each_wave(tmp_path: Path) -> None:
    """[FPG-FR-04] Quota gate runs before each wave and halts with QUOTA_LOW when insufficient."""
    repo = tmp_path / "repo_fr04"
    _init_git_repo(repo)
    _copy_dev_impl_scripts(repo)
    epic = "demo_epic"
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True, exist_ok=True)
    (repo / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "w1.py").write_text("W1 = 1\n", encoding="utf-8")
    (repo / "src" / "w2.py").write_text("W2 = 1\n", encoding="utf-8")
    (features / "task_01_w1.md").write_text(
        _make_task_md("task_01_w1", epic, allowed=["src/w1.py"]),
        encoding="utf-8",
    )
    (features / "task_02_w2.md").write_text(
        _make_task_md(
            "task_02_w2", epic, allowed=["src/w2.py"], blocked_by=["task_01_w1"]
        ),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed FR-04")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    gate_calls = 0

    def quota_gate_stub(*_a: Any, **_kw: Any) -> int:
        nonlocal gate_calls
        gate_calls += 1
        if gate_calls == 1:
            return 0
        print(
            json.dumps(
                {
                    "sufficient": False,
                    "personas": [
                        {
                            "persona": "programmer",
                            "cli": "agy",
                            "alias": "hydrogen",
                            "sufficient": False,
                            "quota_line": "5H=5.0%, 7D=40.0%",
                            "warning": None,
                        }
                    ],
                }
            )
        )
        return 2

    runner.quota_gate = quota_gate_stub
    dispatched: list[str] = []

    def ok_dispatch(
        self_disp: Any, cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        if "task_01_w1" in prompt:
            dispatched.append("task_01_w1")
        if "task_02_w2" in prompt:
            dispatched.append("task_02_w2")
        return 0, "done", ""

    with patch.object(
        lifecycle_runner.ModelDispatcher,
        "dispatch",
        autospec=True,
        side_effect=ok_dispatch,
    ):
        ok = runner.step_implementation()

    assert not ok
    assert gate_calls == 2
    assert dispatched == ["task_01_w1"]
    assert runner.state.halt_reason == "QUOTA_LOW"
    hb = _state_envelope.read_epic_heartbeat(repo, epic)
    assert hb["checkpoint"]["event"] == "quota_low"
    decision = _read_pending_decision(repo, epic)
    assert decision["kind"] == "quota"


def test_fpg_fr_06_agy_pool_dispatch_outcomes(tmp_path: Path) -> None:
    """[FPG-FR-06] Runner maps pooled agy DispatchResult outcomes to halts, checkpoints, and mid-run retries."""
    real_home = tmp_path / "_isolated_home"
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {
            "schema_version": 1,
            "pool": [
                {"profile": "p1", "priority": 1},
                {"profile": "p2", "priority": 2},
            ],
        },
    )

    def _setup_repo(name: str) -> Path:
        repo = tmp_path / name
        _init_git_repo(repo)
        _copy_dev_impl_scripts(repo)
        epic = "demo_epic"
        features = repo / ".devtool" / "features"
        features.mkdir(parents=True, exist_ok=True)
        (repo / ".devtool" / "epic" / epic).mkdir(parents=True, exist_ok=True)
        (repo / "src").mkdir(parents=True, exist_ok=True)
        (repo / "src" / "a.py").write_text("A = 1\n", encoding="utf-8")
        (features / "task_01.md").write_text(
            _make_task_md("task_01", epic, allowed=["src/a.py"]),
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "[DEMO] Seed FR-06")
        return repo

    # 1. no_profile (pool_exhausted) -> quota_low checkpoint, quota pending decision = report, QUOTA_LOW
    report_lines = [
        "Stopped: all agy profiles are out of quota.",
        "- p1: 5-hour limit reached (resets 2026-11-17T14:00:00Z)",
        "- switch the programmer: /d3nexus:dev-config set programmer codex-gpt xhigh",
    ]
    repo1 = _setup_repo("repo_fr06_exhausted")
    r1 = lifecycle_runner.LifecycleRunner(root=repo1, epic_slug="demo_epic")
    r1.quota_gate = lambda *_a, **_kw: 0
    seen_owners: list[Any] = []

    def stub_no_profile(*_a: Any, **kw: Any) -> Any:
        seen_owners.append(kw.get("owner"))
        return agy_dispatch.DispatchResult(
            status="no_profile",
            profile_used=None,
            attempts=2,
            exit_code=2,
            reason="pool_exhausted",
            report=list(report_lines),
        )

    r1.dispatcher.pool_dispatcher = stub_no_profile
    assert not r1.step_implementation()
    assert r1.state.halt_reason == "QUOTA_LOW"
    assert len(seen_owners) == 1
    assert seen_owners[0]["role"] == "runner"
    assert seen_owners[0]["epic"] == "demo_epic"
    hb1 = _state_envelope.read_epic_heartbeat(repo1, "demo_epic")
    assert hb1["checkpoint"]["event"] == "quota_low"
    dec1 = _read_pending_decision(repo1, "demo_epic")
    assert dec1["kind"] == "quota"
    assert dec1["reason"] == "\n".join(report_lines)

    # 2. ok with profile_used "p2" -> continues and subagent_returned checkpoint names "p2"
    repo2 = _setup_repo("repo_fr06_ok")
    r2 = lifecycle_runner.LifecycleRunner(root=repo2, epic_slug="demo_epic")
    r2.quota_gate = lambda *_a, **_kw: 0
    cp_events_2: list[dict[str, Any]] = []
    real_cp2 = r2.checkpoint_writer

    def spy_cp2(root: Path, epic: str, cp: dict[str, Any]) -> dict[str, Any]:
        cp_events_2.append(dict(cp))
        return real_cp2(root, epic, cp)

    r2.checkpoint_writer = spy_cp2
    r2.dispatcher.pool_dispatcher = lambda *_a, **_kw: agy_dispatch.DispatchResult(
        status="ok",
        profile_used="p2",
        attempts=2,
        exit_code=0,
        reason=None,
        report=[],
    )
    assert r2.step_implementation()
    assert r2.state.halt_reason is None
    sub_cps = [c for c in cp_events_2 if c.get("event") == "subagent_returned"]
    assert any("p2" in json.dumps(c) for c in sub_cps)

    # 3. quota_midrun then ok -> re-dispatched once, no halt_reason
    repo3 = _setup_repo("repo_fr06_midrun")
    r3 = lifecycle_runner.LifecycleRunner(root=repo3, epic_slug="demo_epic")
    r3.quota_gate = lambda *_a, **_kw: 0
    calls_3 = 0

    def stub_midrun_then_ok(*_a: Any, **_kw: Any) -> Any:
        nonlocal calls_3
        calls_3 += 1
        if calls_3 == 1:
            return agy_dispatch.DispatchResult(
                status="quota_midrun",
                profile_used="p1",
                attempts=1,
                exit_code=1,
                reason="quota_midrun",
                report=[],
            )
        return agy_dispatch.DispatchResult(
            status="ok",
            profile_used="p2",
            attempts=1,
            exit_code=0,
            reason=None,
            report=[],
        )

    r3.dispatcher.pool_dispatcher = stub_midrun_then_ok
    assert r3.step_implementation()
    assert calls_3 == 2
    assert r3.state.halt_reason is None

    # 4. model_unavailable -> MODEL_UNAVAILABLE + blocker pending decision
    repo4 = _setup_repo("repo_fr06_unavail")
    r4 = lifecycle_runner.LifecycleRunner(root=repo4, epic_slug="demo_epic")
    r4.quota_gate = lambda *_a, **_kw: 0
    r4.dispatcher.pool_dispatcher = lambda *_a, **_kw: agy_dispatch.DispatchResult(
        status="model_unavailable",
        profile_used="p1",
        attempts=1,
        exit_code=1,
        reason="model_unavailable",
        report=[],
    )
    assert not r4.step_implementation()
    assert r4.state.halt_reason == "MODEL_UNAVAILABLE"
    assert _read_pending_decision(repo4, "demo_epic")["kind"] == "blocker"

    # 5. preflight_failed -> MODEL_UNAVAILABLE + blocker pending decision; pool_busy -> QUOTA_LOW
    repo5 = _setup_repo("repo_fr06_preflight")
    r5 = lifecycle_runner.LifecycleRunner(root=repo5, epic_slug="demo_epic")
    r5.quota_gate = lambda *_a, **_kw: 0
    r5.dispatcher.pool_dispatcher = lambda *_a, **_kw: agy_dispatch.DispatchResult(
        status="preflight_failed",
        profile_used=None,
        attempts=0,
        exit_code=1,
        reason="preflight_failed",
        report=["Missing ag_run helper"],
    )
    assert not r5.step_implementation()
    assert r5.state.halt_reason == "MODEL_UNAVAILABLE"
    assert _read_pending_decision(repo5, "demo_epic")["kind"] == "blocker"

    repo6 = _setup_repo("repo_fr06_busy")
    r6 = lifecycle_runner.LifecycleRunner(root=repo6, epic_slug="demo_epic")
    r6.quota_gate = lambda *_a, **_kw: 0
    busy_report = ["Stopped: every agy profile stayed in use for 60 seconds."]
    r6.dispatcher.pool_dispatcher = lambda *_a, **_kw: agy_dispatch.DispatchResult(
        status="no_profile",
        profile_used=None,
        attempts=0,
        exit_code=2,
        reason="pool_busy",
        report=list(busy_report),
    )
    assert not r6.step_implementation()
    assert r6.state.halt_reason == "QUOTA_LOW"
    assert _read_pending_decision(repo6, "demo_epic")["reason"] == "\n".join(
        busy_report
    )

    # 6. Empty pool uses direct subprocess.Popen dispatch without invoking pool_dispatcher
    _write_json(
        real_home / ".d3nexus" / "agy_profiles.json",
        {"schema_version": 1, "pool": []},
    )
    disp = lifecycle_runner.ModelDispatcher(worktree_dir=repo6)
    spy_pool = MagicMock()
    disp.pool_dispatcher = spy_pool
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock(returncode=0)
        proc.communicate.return_value = ("ok", "")
        mock_popen.return_value = proc
        rc, out, _ = disp.dispatch(
            "agy",
            [
                "--model",
                "gemini-4-hydrogen-xhigh",
                "--effort",
                "xhigh",
                "--mode",
                "auto",
            ],
            "hi",
        )
    assert rc == 0
    assert out == "ok"
    spy_pool.assert_not_called()
    mock_popen.assert_called_once()


def test_fpg_runner_bindings_env_docs_and_role_prompts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify --architect-model alias, build_dispatch_env, _epic_docs resolution, and Role 2.1 prompts."""
    repo = tmp_path / "repo_misc"
    _init_git_repo(repo)
    epic = "demo_epic"
    epic_dir = repo / ".devtool" / "epic" / epic
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{epic}.md").write_text("# English HLD\n", encoding="utf-8")
    (epic_dir / f"{epic}.en.md").write_text("# Legacy EN HLD\n", encoding="utf-8")
    (epic_dir / f"{epic}.vi.md").write_text("# Vietnamese Mirror\n", encoding="utf-8")
    (epic_dir / "bdd_scenarios.md").write_text("# English BDD\n", encoding="utf-8")
    (epic_dir / "2026-11-17-topic-design.md").write_text("# Design\n", encoding="utf-8")
    (epic_dir / "2026-11-17-topic-design.vi.md").write_text(
        "# Design VI\n", encoding="utf-8"
    )
    features = repo / ".devtool" / "features"
    features.mkdir(parents=True, exist_ok=True)
    task_path = features / "t1.md"
    task_path.write_text(
        _make_task_md("t1", epic, allowed=["src/a.py"]), encoding="utf-8"
    )

    # 1. --architect-model and --assistant-model alias in main()
    captured: list[Any] = []
    with (
        patch.object(
            lifecycle_runner.LifecycleRunner,
            "run",
            autospec=True,
            side_effect=lambda self, **_kw: captured.append(self.config) or 0,
        ),
        patch.object(
            sys,
            "argv",
            [
                "lifecycle_runner.py",
                "--root",
                str(repo),
                "--epic",
                epic,
                "--architect-model",
                "claude-opus",
                "--dry-run",
            ],
        ),
    ):
        assert lifecycle_runner.main() == 0
    assert captured[-1].resolve_assistant_model(repo) == "opus"

    with (
        patch.object(
            lifecycle_runner.LifecycleRunner,
            "run",
            autospec=True,
            side_effect=lambda self, **_kw: captured.append(self.config) or 0,
        ),
        patch.object(
            sys,
            "argv",
            [
                "lifecycle_runner.py",
                "--root",
                str(repo),
                "--epic",
                epic,
                "--assistant-model",
                "codex-gpt",
                "--dry-run",
            ],
        ),
    ):
        assert lifecycle_runner.main() == 0
    assert captured[-1].resolve_assistant_model(repo) == "gpt-6.1-sol"

    # 2. _build_task_prompt and _apply_code_fixes resolve English-only docs via _epic_docs
    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    task_prompt = runner._build_task_prompt("t1", task_path, repo)
    assert f".devtool/epic/{epic}/{epic}.md" in task_prompt
    assert ".vi.md" not in task_prompt

    fix_prompts: list[str] = []
    with (
        patch.object(
            runner.dispatcher,
            "dispatch",
            side_effect=lambda cli, args, prompt: (
                fix_prompts.append(prompt) or (0, "ok", "")
            ),
        ),
        patch.object(runner, "_run_scoped_tests", return_value=(True, "ok")),
    ):
        assert runner._apply_code_fixes(1, plan_text="plan")
    assert f".devtool/epic/{epic}/{epic}.md" in fix_prompts[0]
    assert "2026-11-17-topic-design.md" in fix_prompts[0]
    assert ".vi.md" not in fix_prompts[0]

    # 3. Role 2.1 prompts in _apply_minor_fixes and _apply_aligned_fixes
    pr_prompts: list[str] = []
    with (
        patch.object(
            runner.dispatcher,
            "dispatch",
            side_effect=lambda cli, args, prompt: (
                pr_prompts.append(prompt) or (0, "ok", "")
            ),
        ),
    ):
        runner._apply_minor_fixes(1)
        runner._apply_aligned_fixes(1)
    assert all("AI Architect & Reviewer (Role 2.1)" in p for p in pr_prompts)
    assert all("AI Assistant (Role 2.2)" not in p for p in pr_prompts)

    # 4. ModelDispatcher.dispatch passes persona_config.build_dispatch_env to Popen (e.g. Kiro HOME)
    kiro_host = tmp_path / "kiro_host"
    (kiro_host / ".kiro").mkdir(parents=True, exist_ok=True)
    isolated_home = kiro_host / "antigravity_homes" / "prof1"
    isolated_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(isolated_home))
    monkeypatch.setenv("REAL_HOME", str(kiro_host))
    disp = lifecycle_runner.ModelDispatcher(worktree_dir=repo)
    with patch("subprocess.Popen") as mock_popen:
        proc = MagicMock(returncode=0)
        proc.communicate.return_value = ("ok", "")
        mock_popen.return_value = proc
        rc, _, _ = disp.dispatch("kiro-cli", ["chat", "--no-interactive"], "hello")
    assert rc == 0
    assert mock_popen.call_args.kwargs["env"]["HOME"] == str(kiro_host)


@pytest.mark.parametrize(
    ("triage_action", "revision_path"),
    [
        ("AUTO_PASS_FINAL_MINOR_SWEEP", "minor-sweep"),
        ("AUTO_PASS_FINAL_SWEEP", "aligned-final"),
        ("AUTO_FIX_ELIGIBLE", "aligned-loop"),
    ],
)
@pytest.mark.parametrize("failure_kind", ["model_unavailable", "quota_low"])
def test_fpg_fr_03_principal_revision_halt_stops_without_overwrite(
    tmp_path: Path,
    triage_action: str,
    revision_path: str,
    failure_kind: str,
) -> None:
    """[FPG-FR-03] [FPG-FR-06] Halting during Principal Review revision preserves HALTED state and dispatches nothing further."""
    real_home = tmp_path / "_isolated_home"
    if failure_kind == "quota_low":
        _write_json(
            real_home / ".d3nexus" / "agy_profiles.json",
            {"schema_version": 1, "pool": [{"profile": "p1", "priority": 1}]},
        )

    repo = tmp_path / f"repo_pr_{revision_path}_{failure_kind}"
    _init_git_repo(repo)
    epic = "demo_epic"
    epic_dir = repo / ".devtool" / "epic" / epic
    epic_dir.mkdir(parents=True, exist_ok=True)
    (epic_dir / f"{epic}.md").write_text("# HLD\n", encoding="utf-8")
    (epic_dir / "principal_review.md").write_text(
        "# Principal Review\n\n## Round 1\n\n| # | Severity | Area | Problem | Decision |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 1 | Important | `hld.md` | Needs revision | pending |\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "[DEMO] Seed PR halt test")

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug=epic)
    dispatch_calls: list[dict[str, Any]] = []
    ext_run_calls: list[int] = []
    ext_triage_calls: list[int] = []

    if failure_kind == "model_unavailable":
        expected_halt = "MODEL_UNAVAILABLE"
        expected_cp = "model_unavailable"
        expected_kind = "blocker"
    else:
        expected_halt = "QUOTA_LOW"
        expected_cp = "quota_low"
        expected_kind = "quota"

    quota_report = [
        "Stopped: all agy profiles are out of quota.",
        "- p1: 5-hour limit reached (resets 2026-11-17T14:00:00Z)",
        "- switch the ai_architect_reviewer: /d3nexus:dev-config set ai_architect_reviewer claude-opus high",
    ]

    def fail_direct_dispatch(
        cli: str, args: list[str], prompt: str
    ) -> tuple[int, str, str]:
        dispatch_calls.append({"cli": cli, "args": list(args), "prompt": prompt})
        return 1, "", "RESOURCE_EXHAUSTED: model quota exhausted"

    def fail_pool_dispatch(*_a: Any, **kw: Any) -> Any:
        dispatch_calls.append(
            {"owner": kw.get("owner"), "mode": _a[1] if len(_a) > 1 else ""}
        )
        return agy_dispatch.DispatchResult(
            status="no_profile",
            profile_used=None,
            attempts=1,
            exit_code=2,
            reason="pool_exhausted",
            report=list(quota_report),
        )

    real_run = subprocess.run
    real_popen = subprocess.Popen

    def guarded_popen(cmd: Any, *p_args: Any, **p_kwargs: Any) -> Any:
        exe = cmd[0] if isinstance(cmd, (list, tuple)) and cmd else str(cmd)
        if exe in ("git", "ps"):
            return real_popen(cmd, *p_args, **p_kwargs)
        raise AssertionError(f"real CLI must not run: {cmd!r}")

    def route_run(cmd: Any, **kwargs: Any) -> Any:
        if isinstance(cmd, list) and cmd and cmd[0] in ("git", "ps"):
            return real_run(cmd, **kwargs)
        if isinstance(cmd, list) and any(
            "run_external_review.py" in str(c) for c in cmd
        ):
            if "run" in cmd:
                ext_run_calls.append(runner.state.principal_round)
                return MagicMock(returncode=0, stdout="", stderr="")
            if "triage" in cmd:
                ext_triage_calls.append(runner.state.principal_round)
                triage_out = (
                    "## Auto-Triage Gate\n\n"
                    f"- **Action**: {triage_action}\n"
                    f"- **Round**: {runner.state.principal_round} / 3\n"
                    "- **Directive**: Revision needed.\n"
                )
                return MagicMock(returncode=0, stdout=triage_out, stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    dispatcher_ctx = (
        patch.object(runner.dispatcher, "dispatch", side_effect=fail_direct_dispatch)
        if failure_kind == "model_unavailable"
        else patch.object(
            runner.dispatcher, "pool_dispatcher", side_effect=fail_pool_dispatch
        )
    )

    with (
        patch("subprocess.run", side_effect=route_run),
        patch("subprocess.Popen", side_effect=guarded_popen),
        dispatcher_ctx,
        patch.object(
            runner, "_run_package_epic_revise", wraps=runner._run_package_epic_revise
        ) as spy_pkg_revise,
    ):
        ok = runner.step_principal_review()

    assert not ok
    assert runner.state.active_stage == lifecycle_runner.StageName.HALTED.value
    assert runner.state.active_stage != lifecycle_runner.StageName.IMPLEMENTATION.value
    assert runner.state.halt_reason == expected_halt
    assert runner.state.principal_round == 1
    assert len(dispatch_calls) == 1
    assert len(ext_run_calls) == 1
    assert len(ext_triage_calls) == 1
    spy_pkg_revise.assert_not_called()

    persisted = lifecycle_runner.PipelineState.from_dict(
        json.loads(runner.state_file().read_text(encoding="utf-8"))
    )
    assert persisted.active_stage == lifecycle_runner.StageName.HALTED.value
    assert persisted.halt_reason == expected_halt
    assert persisted.principal_round == 1

    hb = _state_envelope.read_epic_heartbeat(repo, epic)
    assert hb["checkpoint"]["event"] == expected_cp

    decision = _read_pending_decision(repo, epic)
    assert decision["kind"] == expected_kind
    if failure_kind == "model_unavailable":
        assert "/d3nexus:dev-config set ai_architect_reviewer" in decision["reason"]
    else:
        assert decision["reason"] == "\n".join(quota_report)


@pytest.mark.parametrize(
    ("stubs", "expected_ok"),
    [
        (("kiro-cli",), True),
        (("kiro",), True),
        ((), False),
    ],
)
def test_runner_probe_resolves_kiro_binary_from_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stubs: tuple[str, ...],
    expected_ok: bool,
) -> None:
    """S1: run() must probe the executable resolved by build_dispatch_argv (accepting kiro-cli or kiro)."""
    repo = tmp_path / "repo"
    _init_git_repo(repo)
    _write_json(
        repo / ".agents" / "config" / "personas.json",
        {
            "schema_version": 1,
            "overrides": {"programmer": {"model": "kiro-sonnet", "effort": "high"}},
        },
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(parents=True)
    for name in stubs:
        stub = bin_dir / name
        stub.write_text("#!/bin/sh\necho 'kiro 1.0'\nexit 0\n", encoding="utf-8")
        stub.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))

    runner = lifecycle_runner.LifecycleRunner(root=repo, epic_slug="kiro_probe")
    assert runner.state.active_stage == lifecycle_runner.StageName.INITIALIZED.value

    entered_stage2 = False

    def fake_principal_review() -> bool:
        nonlocal entered_stage2
        entered_stage2 = True
        runner.state.active_stage = lifecycle_runner.StageName.COMPLETED.value
        return True

    with patch.object(
        runner, "step_principal_review", side_effect=fake_principal_review
    ):
        rc = runner.run(dry_run=False)

    if expected_ok:
        assert entered_stage2 is True, (
            f"Probe failed unexpectedly: {runner.state.last_error}"
        )
        assert rc == 0
        assert runner.state.last_error in (None, "")
    else:
        assert entered_stage2 is False
        assert rc == 1
        assert runner.state.active_stage == lifecycle_runner.StageName.INITIALIZED.value
        assert runner.state.last_error is not None
        assert "Programmer probe failed:" in runner.state.last_error
