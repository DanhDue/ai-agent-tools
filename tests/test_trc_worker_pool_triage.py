"""Unit and integration tests for Task 3: Worker pool hard caps, tree snapshot, triage, and finalization.

Covers BDD Scenarios:
- TRC-HP-03: Clean surgical Fix Pass 1 passes Tier 1 eligibility and short-circuits via Tier 2 LOW finalize-slot
- TRC-EC-02: Parser Coercion Guard converts zero-blocker CHANGES_REQUESTED to APPROVED and blocks Fix Pass 1 without blockers
- TRC-EC-03: Tier 1 heuristic boundary and sensitive-surface triggers classify HIGH_RISK accurately
- TRC-EC-04: Pass 2 residual CHANGES_REQUESTED with green mechanical gates finalizes to done with audit note and zero Fix Pass 2
- TRC-ST-01: Worker pool enforces idempotent re-sync across both review passes and max_task_review_passes = 2 while rejecting a third review transition with exit code 2
- TRC-ST-02: Worker pool enforces max_fix_passes = 1 and rejects a second fix pass with exit code 2
- TRC-ST-03: Temporary GIT_INDEX_FILE snapshot isolates Fix Pass 1 delta from uncommitted Pass 1 changes without touching HEAD or index
- TRC-AR-02: Concurrent slot 1 and slot 2 pool operations preserve independent per-slot review and fix counters
- TRC-AR-03: Slot merge and finalize-slot reconcile tracked epic and features mirrors plus untracked done mirrors and commit main_wt audit notes across parallel slots
- TRC-FR-02: finalize-slot aborts with exit code 1 when mechanical done_gate or BDD traceability fails
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
POOL_SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
POOL_SCRIPT = POOL_SCRIPTS_DIR / "manage_worker_pool.py"

if str(POOL_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(POOL_SCRIPTS_DIR))

import manage_worker_pool  # noqa: E402


def _git(cwd: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout.strip()


def _init_pool_repo(
    tmp_path: Path,
    *,
    epic_dir: str = "trc_demo",
    epic_slug: str = "trc-demo",
    pool_size: int = 2,
) -> tuple[Path, Path, Path]:
    """Create an isolated git repo with an epic worktree and isolated HOME/REAL_HOME."""
    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    repo = tmp_path / "repo"
    repo.mkdir(parents=True, exist_ok=True)

    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.name", "Test User")
    _git(repo, "config", "user.email", "test@example.com")

    (repo / ".gitignore").write_text(
        ".worktrees/\n.devtool/.memory.lock\n.devtool/state/\n.devtool/logs/\n",
        encoding="utf-8",
    )
    (repo / "README.md").write_text("# Test Repo\n", encoding="utf-8")
    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "__init__.py").write_text("", encoding="utf-8")
    (repo / "tests").mkdir(parents=True, exist_ok=True)
    (repo / "tests" / "__init__.py").write_text("", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "Initial commit")

    main_wt = repo / ".worktrees" / epic_dir
    main_wt.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "add", str(main_wt), "-b", f"epic/{epic_slug}", "main")

    return repo, main_wt, home


def _run_pool_cli(
    cwd: Path,
    args: list[str],
    *,
    home: Path,
) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["REAL_HOME"] = str(home)
    env["WORKSPACE_ROOT"] = str(cwd)
    for key in (
        "AGY_PROFILE",
        "ANTIGRAVITY_PROFILE",
        "AGY_PROGRAMMER_MODEL",
        "AGY_PROGRAMMER_EFFORT",
    ):
        env.pop(key, None)
    return subprocess.run(
        [sys.executable, str(POOL_SCRIPT), *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _read_heartbeat(repo: Path, epic_slug: str) -> dict[str, Any]:
    hb_path = repo / ".devtool" / "state" / f"{epic_slug}.heartbeat.json"
    return json.loads(hb_path.read_text(encoding="utf-8"))


def _write_heartbeat(repo: Path, epic_slug: str, data: dict[str, Any]) -> None:
    hb_path = repo / ".devtool" / "state" / f"{epic_slug}.heartbeat.json"
    hb_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _seed_task_stubs(
    repo: Path,
    main_wt: Path,
    epic_dir: str,
    epic_slug: str,
    task_id: str,
    *,
    scenario_id: str,
    done_gate_pass: bool = True,
    with_bdd_root: bool = True,
    commit_in_epic: bool = True,
) -> None:
    """Seed minimal task mirrors, HLD, scenarios, and deterministic stub scripts."""
    epic_root = main_wt / ".devtool" / "epic" / epic_dir
    features_dir = main_wt / ".devtool" / "features"
    epic_root.mkdir(parents=True, exist_ok=True)
    features_dir.mkdir(parents=True, exist_ok=True)

    (epic_root / f"{epic_dir}.md").write_text(
        f"# Epic {epic_dir}\n\nIntegration test roots: tests\n",
        encoding="utf-8",
    )
    (epic_root / "bdd_scenarios.md").write_text(
        "# BDD\n\n```gherkin\n"
        f"Scenario: [{scenario_id}] [Tier C - Integration] Stub scenario\n"
        "Given a repo\nWhen it runs\nThen it passes\n"
        "```\n",
        encoding="utf-8",
    )
    task_md = (
        f'---\nid: "{task_id}"\nstatus: "in-progress"\nepic: "{epic_slug}"\n'
        'completedAt: null\nmodified: "2026-11-18T00:00:00Z"\n---\n\n'
        f"# {task_id}\n\nCovers: {scenario_id}\n\n"
        "## Verification\n\n| ID | Phase | Command | Expect | Needs |\n"
        "|---|---|---|---|---|\n| V1 | GREEN | `true` | exit 0 | — |\n"
    )
    (epic_root / f"{task_id}.md").write_text(task_md, encoding="utf-8")
    (features_dir / f"{task_id}.md").write_text(task_md, encoding="utf-8")

    if with_bdd_root:
        (main_wt / "tests").mkdir(parents=True, exist_ok=True)
        (main_wt / "tests" / f"test_{task_id}.py").write_text(
            f"# Covers {scenario_id}\ndef test_{task_id}():\n    assert True\n",
            encoding="utf-8",
        )

    scripts_dir = main_wt / "skills" / "dev-implementation" / "resources" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    gate_line = "done gate: PASS" if done_gate_pass else "done gate: FAIL"
    gate_exit = 0 if done_gate_pass else 1
    (scripts_dir / "run_task_checks.py").write_text(
        f"import sys\nprint({gate_line!r})\nsys.exit({gate_exit})\n",
        encoding="utf-8",
    )
    (scripts_dir / "check_bdd_traceability.py").write_text(
        "import pathlib, sys\n"
        "args = sys.argv[1:]\n"
        "ids = []\n"
        "if '--ids' in args:\n"
        "    idx = args.index('--ids') + 1\n"
        "    while idx < len(args) and not args[idx].startswith('--'):\n"
        "        ids.append(args[idx]); idx += 1\n"
        "text = '\\n'.join(p.read_text(encoding='utf-8') for p in pathlib.Path('tests').rglob('*.py')) if pathlib.Path('tests').is_dir() else ''\n"
        "missing = [i for i in ids if i not in text]\n"
        "if missing:\n"
        "    print('Missing:', missing)\n"
        "    sys.exit(1)\n"
        "print('PASS')\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    (scripts_dir / "sync_task_status.py").write_text(
        "import pathlib, re, sys\n"
        "task_id, new_status = sys.argv[2], sys.argv[3]\n"
        "root = pathlib.Path.cwd()\n"
        "for p in list(root.glob(f'.devtool/epic/*/{task_id}.md')):\n"
        "    t = re.sub(r'^status:.*$', f'status: \"{new_status}\"', p.read_text(encoding='utf-8'), flags=re.M)\n"
        "    p.write_text(t, encoding='utf-8')\n"
        "feat = root / '.devtool' / 'features' / f'{task_id}.md'\n"
        "if feat.is_file():\n"
        "    t = re.sub(r'^status:.*$', f'status: \"{new_status}\"', feat.read_text(encoding='utf-8'), flags=re.M)\n"
        "    if new_status == 'done':\n"
        "        done_dir = root / '.devtool' / 'features' / 'done'\n"
        "        done_dir.mkdir(parents=True, exist_ok=True)\n"
        "        (done_dir / f'{task_id}.md').write_text(t, encoding='utf-8')\n"
        "        feat.unlink()\n"
        "    else:\n"
        "        feat.write_text(t, encoding='utf-8')\n",
        encoding="utf-8",
    )

    if commit_in_epic:
        _git(main_wt, "add", ".")
        _git(main_wt, "commit", "-q", "-m", f"Seed {task_id} for {epic_dir}")


def test_trc_st_01_and_st_02_hard_review_and_fix_caps(tmp_path: Path) -> None:
    """TRC-ST-01 & TRC-ST-02: Idempotent re-sync and hard review/fix cap enforcement."""
    assert getattr(manage_worker_pool, "HardCapExceededError", None) is not None, (
        "manage_worker_pool.HardCapExceededError must be defined"
    )
    assert getattr(manage_worker_pool, "HARD_CAP_EXIT_CODE", None) == 2

    repo, main_wt, home = _init_pool_repo(tmp_path)
    init_res = _run_pool_cli(
        main_wt, ["init", "trc_demo", "--pool-size", "2"], home=home
    )
    assert init_res.returncode == 0, init_res.stderr

    hb0 = _read_heartbeat(repo, "trc-demo")
    assert hb0["slots"]["slot-1"]["review_passes_used"] == 0
    assert hb0["slots"]["slot-1"]["fix_passes_used"] == 0
    assert hb0["slots"]["slot-1"]["pass1_tree_sha"] is None

    # Pass 1 implementation working sync
    res_w1 = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--task", "task_01", "--status", "working"],
        home=home,
    )
    assert res_w1.returncode == 0, res_w1.stderr

    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    (slot1 / "src" / "app.py").write_text(
        "def run():\n    return 1\n", encoding="utf-8"
    )

    # Pass 1 review sync twice (second call must be idempotent)
    res_r1_a = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--task", "task_01", "--status", "review"],
        home=home,
    )
    assert res_r1_a.returncode == 0, res_r1_a.stderr
    hb_r1_a = _read_heartbeat(repo, "trc-demo")
    assert hb_r1_a["slots"]["slot-1"]["review_passes_used"] == 1
    tree_sha_p1 = hb_r1_a["slots"]["slot-1"]["pass1_tree_sha"]
    assert isinstance(tree_sha_p1, str) and len(tree_sha_p1) >= 7

    res_r1_b = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--task", "task_01", "--status", "review"],
        home=home,
    )
    assert res_r1_b.returncode == 0, res_r1_b.stderr
    hb_r1_b = _read_heartbeat(repo, "trc-demo")
    assert hb_r1_b["slots"]["slot-1"]["review_passes_used"] == 1
    assert hb_r1_b["slots"]["slot-1"]["pass1_tree_sha"] == tree_sha_p1

    # Attempting Pass 2 review from working with fix_passes_used == 0 must fail
    hb_no_fix = _read_heartbeat(repo, "trc-demo")
    hb_no_fix["slots"]["slot-1"]["status"] = "working"
    _write_heartbeat(repo, "trc-demo", hb_no_fix)
    res_no_fix_p2 = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "review"],
        home=home,
    )
    assert res_no_fix_p2.returncode == 2
    assert "NO_FIX_PASS_BEFORE_REVIEW_PASS_2" in res_no_fix_p2.stderr

    # Restore review status for Pass 1 -> Fix Pass 1 transition
    hb_no_fix["slots"]["slot-1"]["status"] = "review"
    _write_heartbeat(repo, "trc-demo", hb_no_fix)

    blocker_file = _write_json(
        tmp_path / "p1_blockers.json",
        [
            {
                "id": "BLK-1",
                "category": "BDD_VIOLATION",
                "file": "src/app.py",
                "summary": "Return 2 instead of 1",
                "remediation": "Return 2",
            }
        ],
    )
    res_fix1 = _run_pool_cli(
        main_wt,
        [
            "sync",
            "trc_demo",
            "--slot",
            "1",
            "--status",
            "working",
            "--no-reset",
            "--blockers-file",
            str(blocker_file),
        ],
        home=home,
    )
    assert res_fix1.returncode == 0, res_fix1.stderr
    hb_fix1 = _read_heartbeat(repo, "trc-demo")
    assert hb_fix1["slots"]["slot-1"]["fix_passes_used"] == 1
    assert hb_fix1["slots"]["slot-1"]["review_passes_used"] == 1
    assert hb_fix1["slots"]["slot-1"]["pass1_blockers"][0]["id"] == "BLK-1"

    # Idempotent re-sync mid-fix preserves counters
    res_fix1_dup = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "working", "--no-reset"],
        home=home,
    )
    assert res_fix1_dup.returncode == 0, res_fix1_dup.stderr
    hb_fix1_dup = _read_heartbeat(repo, "trc-demo")
    assert hb_fix1_dup["slots"]["slot-1"]["fix_passes_used"] == 1
    assert hb_fix1_dup["slots"]["slot-1"]["review_passes_used"] == 1

    # Pass 2 review sync twice (second call must be idempotent)
    res_r2_a = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "review"],
        home=home,
    )
    assert res_r2_a.returncode == 0, res_r2_a.stderr
    hb_r2_a = _read_heartbeat(repo, "trc-demo")
    assert hb_r2_a["slots"]["slot-1"]["review_passes_used"] == 2
    assert hb_r2_a["slots"]["slot-1"]["pass1_tree_sha"] == tree_sha_p1

    res_r2_b = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "review"],
        home=home,
    )
    assert res_r2_b.returncode == 0, res_r2_b.stderr
    hb_r2_b = _read_heartbeat(repo, "trc-demo")
    assert hb_r2_b["slots"]["slot-1"]["review_passes_used"] == 2

    # TRC-ST-02: Second fix pass attempt from Pass 2 review exits 2 with HARD_FIX_CAP_EXCEEDED
    res_fix2 = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "working", "--no-reset"],
        home=home,
    )
    assert res_fix2.returncode == 2
    assert "HARD_FIX_CAP_EXCEEDED" in res_fix2.stderr
    assert _read_heartbeat(repo, "trc-demo")["slots"]["slot-1"]["fix_passes_used"] == 1

    # TRC-ST-01: Attempting a 3rd entry into review from working exits 2 with HARD_REVIEW_CAP_EXCEEDED
    hb_working = _read_heartbeat(repo, "trc-demo")
    hb_working["slots"]["slot-1"]["status"] = "working"
    _write_heartbeat(repo, "trc-demo", hb_working)

    res_r3 = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "review"],
        home=home,
    )
    assert res_r3.returncode == 2
    assert "HARD_REVIEW_CAP_EXCEEDED" in res_r3.stderr
    assert (
        _read_heartbeat(repo, "trc-demo")["slots"]["slot-1"]["review_passes_used"] == 2
    )


def test_trc_ec_02_coercion_guard_and_normalization(tmp_path: Path) -> None:
    """TRC-EC-02: Coercion Guard converts zero-blocker CHANGES_REQUESTED to APPROVED and rejects fix sync."""
    norm_fn = getattr(manage_worker_pool, "normalize_task_review_payload", None)
    assert norm_fn is not None, "normalize_task_review_payload must be exported"

    coerced_payload = {
        "task_id": "task_03",
        "pass": 1,
        "verdict": "CHANGES_REQUESTED",
        "head_sha": "abc1234",
        "done_gate": "PASS",
        "blockers": [],
        "observations": [{"id": "OBS-1", "file": "src/x.py", "summary": "Nitpick"}],
    }
    norm = norm_fn(coerced_payload)
    assert norm["valid"] is True
    assert norm["verdict"] == "APPROVED"
    assert norm["coerced_from_non_blocking"] is True

    # Legacy PASS / FAIL + findings + done_gate FAIL + UNPARSEABLE branches
    assert norm_fn({"verdict": "PASS", "done_gate": "PASS"})["verdict"] == "APPROVED"
    legacy_fail = norm_fn(
        {"verdict": "FAIL", "done_gate": "PASS", "findings": ["Missing check"]}
    )
    assert legacy_fail["verdict"] == "CHANGES_REQUESTED"
    assert legacy_fail["blockers"] == [
        {"id": "BLK-1", "category": "LEGACY_FINDING", "summary": "Missing check"}
    ]

    legacy_obs = norm_fn(
        {
            "verdict": "FAIL",
            "done_gate": "PASS",
            "findings": ["NON_BLOCKING_OBSERVATION: style nit"],
        }
    )
    assert legacy_obs["verdict"] == "APPROVED"
    assert legacy_obs["coerced_from_non_blocking"] is True

    gate_fail = norm_fn(
        {
            "verdict": "CHANGES_REQUESTED",
            "done_gate": "FAIL",
            "blockers": [],
        }
    )
    assert gate_fail["verdict"] == "CHANGES_REQUESTED"
    assert gate_fail["coerced_from_non_blocking"] is False
    assert gate_fail["blockers"][0]["id"] == "BLK-GATE"
    assert gate_fail["blockers"][0]["category"] == "RUNTIME_SAFETY"

    approved_with_blockers = norm_fn(
        {
            "verdict": "APPROVED",
            "done_gate": "PASS",
            "blockers": [{"id": "BLK-1", "summary": "Bug"}],
        }
    )
    assert approved_with_blockers["verdict"] == "CHANGES_REQUESTED"
    assert approved_with_blockers["coerced_from_non_blocking"] is False
    assert len(approved_with_blockers["blockers"]) == 1

    for bad in ("not a mapping", {}, {"verdict": "MAYBE"}):
        unparsed = norm_fn(bad)  # type: ignore[arg-type]
        assert unparsed["valid"] is False
        assert unparsed["verdict"] == "UNPARSEABLE"
        assert unparsed["coerced_from_non_blocking"] is False

    # CLI sync --status working --no-reset --review-file coerced.json exits 2
    repo, main_wt, home = _init_pool_repo(tmp_path)
    assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--status",
                "working",
            ],
            home=home,
        ).returncode
        == 0
    )
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--status",
                "review",
            ],
            home=home,
        ).returncode
        == 0
    )

    coerced_file = _write_json(tmp_path / "coerced.json", coerced_payload)
    res_block = _run_pool_cli(
        main_wt,
        [
            "sync",
            "trc_demo",
            "--slot",
            "1",
            "--status",
            "working",
            "--no-reset",
            "--review-file",
            str(coerced_file),
        ],
        home=home,
    )
    assert res_block.returncode == 2
    assert "NO_BLOCKER_FOR_FIX_PASS" in res_block.stderr


def test_trc_st_03_temporary_index_snapshot_isolates_fix_delta(tmp_path: Path) -> None:
    """TRC-ST-03: pass1_tree_sha snapshot isolates Fix Pass 1 delta without mutating HEAD or slot index."""
    repo, main_wt, home = _init_pool_repo(tmp_path)
    assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--status",
                "working",
            ],
            home=home,
        ).returncode
        == 0
    )

    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    big_lines = [f"VAL_{i} = {i}" for i in range(220)]
    (slot1 / "src" / "feature_big.py").write_text(
        "\n".join(big_lines) + "\n", encoding="utf-8"
    )
    (slot1 / ".devtool" / "epic" / "trc_demo" / "evidence").mkdir(
        parents=True, exist_ok=True
    )
    (slot1 / ".devtool" / "epic" / "trc_demo" / "evidence" / "task_03.json").write_text(
        "{}\n", encoding="utf-8"
    )

    index_rel = _git(slot1, "rev-parse", "--git-path", "index")
    index_path = Path(index_rel)
    if not index_path.is_absolute():
        index_path = slot1 / index_path
    head_before = _git(slot1, "rev-parse", "HEAD")
    index_digest_before = hashlib.sha256(index_path.read_bytes()).hexdigest()

    res_rev = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--task", "task_03", "--status", "review"],
        home=home,
    )
    assert res_rev.returncode == 0, res_rev.stderr

    head_after = _git(slot1, "rev-parse", "HEAD")
    index_digest_after = hashlib.sha256(index_path.read_bytes()).hexdigest()
    assert head_after == head_before
    assert index_digest_after == index_digest_before

    # Enter Fix Pass 1 and insert 6 surgical lines
    blocker_file = _write_json(
        tmp_path / "b.json",
        [
            {
                "id": "BLK-1",
                "category": "RUNTIME_SAFETY",
                "file": "src/feature_big.py",
                "summary": "Add 6 constants",
            }
        ],
    )
    res_fix = _run_pool_cli(
        main_wt,
        [
            "sync",
            "trc_demo",
            "--slot",
            "1",
            "--status",
            "working",
            "--no-reset",
            "--blockers-file",
            str(blocker_file),
        ],
        home=home,
    )
    assert res_fix.returncode == 0, res_fix.stderr

    fix_lines = big_lines + [f"FIX_{j} = {j}" for j in range(6)]
    (slot1 / "src" / "feature_big.py").write_text(
        "\n".join(fix_lines) + "\n", encoding="utf-8"
    )
    (slot1 / ".devtool" / "epic" / "trc_demo" / "evidence" / "task_03.json").write_text(
        '{"updated": true}\n', encoding="utf-8"
    )

    res_triage = _run_pool_cli(
        main_wt,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_03"],
        home=home,
    )
    assert res_triage.returncode == 0, res_triage.stderr
    triage = json.loads(res_triage.stdout)
    assert triage["non_test_changed_lines"] == 6
    assert triage["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT"
    assert triage["triggers"] == []
    assert isinstance(triage["bounded_diff"], str) and "FIX_0" in triage["bounded_diff"]


def _setup_slot_for_triage(
    tmp_path: Path,
    *,
    initial_src: str,
    initial_test: str,
) -> tuple[Path, Path, Path, Path]:
    repo, main_wt, home = _init_pool_repo(tmp_path)
    (main_wt / "src" / "calc.py").write_text(initial_src, encoding="utf-8")
    (main_wt / "tests" / "test_calc.py").write_text(initial_test, encoding="utf-8")
    _git(main_wt, "add", ".")
    _git(main_wt, "commit", "-q", "-m", "Add calc module")

    assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--status",
                "working",
            ],
            home=home,
        ).returncode
        == 0
    )
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--status",
                "review",
            ],
            home=home,
        ).returncode
        == 0
    )
    blocker_file = _write_json(
        tmp_path / "b.json",
        [
            {
                "id": "BLK-1",
                "category": "BDD_VIOLATION",
                "file": "src/calc.py",
                "summary": "Fix calc",
            }
        ],
    )
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--status",
                "working",
                "--no-reset",
                "--blockers-file",
                str(blocker_file),
            ],
            home=home,
        ).returncode
        == 0
    )
    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    return repo, main_wt, home, slot1


def test_trc_ec_03_boundary_30_lines_eligible_and_tier2_record(tmp_path: Path) -> None:
    """TRC-EC-03 boundary: Exactly 30 internal lines + added test assertion is ELIGIBLE_FOR_SHORT_CIRCUIT."""
    initial_src = "def _helper(val: int) -> int:\n    return val\n"
    initial_test = "def test_calc():\n    assert 1 == 1\n"
    _, main_wt, home, slot1 = _setup_slot_for_triage(
        tmp_path, initial_src=initial_src, initial_test=initial_test
    )

    body_lines = "\n".join(f"    val += {i % 3}" for i in range(30))
    (slot1 / "src" / "calc.py").write_text(
        f"def _helper(val: int) -> int:\n{body_lines}\n    return val\n",
        encoding="utf-8",
    )
    (slot1 / "tests" / "test_calc.py").write_text(
        "RAW_TEST_BODY_MARKER = 42\n"
        "def test_calc():\n"
        "    assert 1 == 1\n"
        "    assert 2 == 2\n",
        encoding="utf-8",
    )

    res = _run_pool_cli(
        main_wt,
        [
            "triage-fix",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_03",
            "--format",
            "json",
        ],
        home=home,
    )
    assert res.returncode == 0, res.stderr
    payload = json.loads(res.stdout)
    assert payload["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT"
    assert payload["non_test_changed_lines"] == 30
    assert payload["triggers"] == []
    bounded = payload["bounded_diff"]
    assert isinstance(bounded, str) and bounded
    assert "diff --git a/src/calc.py" in bounded
    assert "diff --git a/tests/" not in bounded
    assert "RAW_TEST_BODY_MARKER" not in bounded
    assert "+    assert 2 == 2" not in bounded
    assert (
        "# test-summary tests/test_calc.py: +1/-0 assertions, skip_added=False"
        in bounded
    )

    # Also test --record-tier2 MEDIUM writes committed audit note in main_wt
    res_rec = _run_pool_cli(
        main_wt,
        [
            "triage-fix",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_03",
            "--record-tier2",
            "--risk-level",
            "MEDIUM",
            "--rationale",
            "Requires Pass 2 delta verification",
        ],
        home=home,
    )
    assert res_rec.returncode == 0, res_rec.stderr
    notes_file = main_wt / ".devtool" / "epic" / "trc_demo" / "review_audit_notes.jsonl"
    assert notes_file.is_file()
    entries = [
        json.loads(line)
        for line in notes_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert entries[-1]["risk_level"] == "MEDIUM"
    assert _git(main_wt, "status", "--porcelain") == ""


@pytest.mark.parametrize(
    ("case_id", "src_override", "test_override", "expected_trigger"),
    [
        (
            "a_over_30_lines",
            "def _helper(val: int) -> int:\n"
            + "\n".join(f"    val += {i % 3}" for i in range(31))
            + "\n    return val\n",
            None,
            "NON_TEST_DIFF_OVER_30_LINES",
        ),
        (
            "b_public_signature",
            "def compute_score(val: int, weight: int = 1) -> int:\n    return val * weight\n",
            None,
            "PUBLIC_SIGNATURE_CHANGED",
        ),
        (
            "c_api_route_or_schema",
            "class Payload(BaseModel):\n    name: str\n\n@router.post('/items')\ndef _h():\n    pass\n",
            None,
            "API_ROUTE_OR_SCHEMA_CHANGED",
        ),
        (
            "d_db_or_persistence",
            "import sqlite3\ndef _helper(val: int) -> int:\n    q = 'UPDATE items SET v = 1'\n    return val\n",
            None,
            "DB_OR_PERSISTENCE_CHANGED",
        ),
        (
            "e_concurrency_or_locking",
            "import threading\n_LOCK = threading.Lock()\ndef _helper(val: int) -> int:\n    return val\n",
            None,
            "CONCURRENCY_OR_LOCKING_CHANGED",
        ),
        (
            "f_test_assertion_removed",
            None,
            "def test_calc():\n    pass\n",
            "TEST_ASSERTION_WEAKENED",
        ),
        (
            "f_test_skip_added",
            None,
            "import pytest\n@pytest.mark.skip(reason='flaky')\ndef test_calc():\n    assert 1 == 1\n",
            "TEST_ASSERTION_WEAKENED",
        ),
    ],
)
def test_trc_ec_03_tier1_sensitive_triggers_classify_high_risk(
    tmp_path: Path,
    case_id: str,
    src_override: str | None,
    test_override: str | None,
    expected_trigger: str,
) -> None:
    """TRC-EC-03 triggers (a)-(f): Classify HIGH_RISK with bounded_diff=None and exact trigger."""
    initial_src = "def compute_score(val: int) -> int:\n    return val\n"
    initial_test = "def test_calc():\n    assert 1 == 1\n"
    _, main_wt, home, slot1 = _setup_slot_for_triage(
        tmp_path, initial_src=initial_src, initial_test=initial_test
    )

    if src_override is not None:
        (slot1 / "src" / "calc.py").write_text(src_override, encoding="utf-8")
    if test_override is not None:
        (slot1 / "tests" / "test_calc.py").write_text(test_override, encoding="utf-8")

    res = _run_pool_cli(
        main_wt,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_03"],
        home=home,
    )
    assert res.returncode == 0, f"{case_id}: {res.stderr}"
    payload = json.loads(res.stdout)
    assert payload["tier1_status"] == "HIGH_RISK", case_id
    assert payload["bounded_diff"] is None, case_id
    assert expected_trigger in payload["triggers"], f"{case_id}: {payload['triggers']}"


class TestTrcWorkerPool_Integration:
    """Tier C integration suite for TRC-HP-03, TRC-EC-04, TRC-ST-01, TRC-ST-02, TRC-AR-02, TRC-AR-03, TRC-FR-02."""

    def test_trc_st_01_idempotent_resync_and_hard_review_cap(
        self, tmp_path: Path
    ) -> None:
        """TRC-ST-01: Duplicate Pass 1/Pass 2 review syncs are idempotent; 3rd review exits 2."""
        test_trc_st_01_and_st_02_hard_review_and_fix_caps(tmp_path)

    def test_trc_st_02_hard_fix_cap_rejects_second_fix_pass(
        self, tmp_path: Path
    ) -> None:
        """TRC-ST-02: Seeded review_passes_used=2, fix_passes_used=1 rejects second fix pass with exit 2."""
        repo, main_wt, home = _init_pool_repo(tmp_path)
        assert (
            _run_pool_cli(
                main_wt, ["init", "trc_demo", "--pool-size", "2"], home=home
            ).returncode
            == 0
        )
        hb = _read_heartbeat(repo, "trc-demo")
        hb["slots"]["slot-1"].update(
            {
                "status": "review",
                "task_id": "task_01",
                "review_passes_used": 2,
                "fix_passes_used": 1,
            }
        )
        _write_heartbeat(repo, "trc-demo", hb)
        res = _run_pool_cli(
            main_wt,
            ["sync", "trc_demo", "--slot", "1", "--status", "working", "--no-reset"],
            home=home,
        )
        assert res.returncode == 2
        assert "HARD_FIX_CAP_EXCEEDED" in res.stderr
        assert (
            _read_heartbeat(repo, "trc-demo")["slots"]["slot-1"]["fix_passes_used"] == 1
        )

    def test_trc_hp_03_surgical_fix_and_tier2_short_circuit_finalize(
        self,
        tmp_path: Path,
    ) -> None:
        """TRC-HP-03: Surgical Fix Pass 1 passes Tier 1 and short-circuits via Tier 2 LOW finalize-slot."""
        repo, main_wt, home = _init_pool_repo(tmp_path)
        (main_wt / "src" / "worker.py").write_text(
            "def _process(x: int) -> int:\n    return x\n",
            encoding="utf-8",
        )
        _seed_task_stubs(
            repo,
            main_wt,
            "trc_demo",
            "trc-demo",
            "task_01",
            scenario_id="TRC-HP-03",
            done_gate_pass=True,
        )

        assert (
            _run_pool_cli(
                main_wt, ["init", "trc_demo", "--pool-size", "2"], home=home
            ).returncode
            == 0
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )

        slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
        (slot1 / "src" / "worker.py").write_text(
            "def _process(x: int) -> int:\n    return x + 1\n",
            encoding="utf-8",
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "review",
                ],
                home=home,
            ).returncode
            == 0
        )

        blocker_file = _write_json(
            tmp_path / "p1.json",
            [
                {
                    "id": "BLK-1",
                    "category": "BDD_VIOLATION",
                    "file": "src/worker.py",
                    "summary": "Add bounds",
                }
            ],
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--status",
                    "working",
                    "--no-reset",
                    "--blockers-file",
                    str(blocker_file),
                ],
                home=home,
            ).returncode
            == 0
        )

        # 8 lines inserted inside internal helper + 4 assertion lines in tests/test_worker.py
        extra = "\n".join(f"    x += {i}" for i in range(8))
        (slot1 / "src" / "worker.py").write_text(
            f"def _process(x: int) -> int:\n{extra}\n    return x + 1\n",
            encoding="utf-8",
        )
        (slot1 / "tests" / "test_worker.py").write_text(
            "# TRC-HP-03\ndef test_worker():\n    assert 1 == 1\n    assert 2 == 2\n    assert 3 == 3\n    assert 4 == 4\n",
            encoding="utf-8",
        )

        res_triage = _run_pool_cli(
            main_wt,
            ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_01"],
            home=home,
        )
        assert res_triage.returncode == 0, res_triage.stderr
        triage = json.loads(res_triage.stdout)
        assert triage["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT"
        assert triage["triggers"] == []
        assert triage["non_test_changed_lines"] == 8
        assert isinstance(triage["bounded_diff"], str) and triage["bounded_diff"]

        res_fin = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--mode",
                "tier2-short-circuit",
                "--risk-level",
                "LOW",
                "--rationale",
                "Directly resolves BLK-1 with zero side effects",
            ],
            home=home,
        )
        assert res_fin.returncode == 0, res_fin.stderr
        fin = json.loads(res_fin.stdout)
        assert fin["ok"] is True

        done_feature = main_wt / ".devtool" / "features" / "done" / "task_01.md"
        assert done_feature.is_file()
        assert 'status: "done"' in done_feature.read_text(encoding="utf-8")
        assert not (main_wt / ".devtool" / "features" / "task_01.md").exists()

        audit_path = (
            main_wt / ".devtool" / "epic" / "trc_demo" / "review_audit_notes.jsonl"
        )
        assert audit_path.is_file()
        entries = [
            json.loads(ln)
            for ln in audit_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert len(entries) == 1
        assert entries[0]["mode"] == "tier2-short-circuit"
        assert entries[0]["risk_level"] == "LOW"
        assert _git(main_wt, "status", "--porcelain") == ""

        hb = _read_heartbeat(repo, "trc-demo")
        assert hb["slots"]["slot-1"]["status"] == "idle"
        assert hb["slots"]["slot-1"]["review_passes_used"] == 0
        assert hb["slots"]["slot-1"]["fix_passes_used"] == 0
        assert hb["slots"]["slot-1"]["pass1_tree_sha"] is None

    def test_trc_ec_04_pass2_residual_changes_requested_finalizes_to_done(
        self,
        tmp_path: Path,
    ) -> None:
        """TRC-EC-04: Pass 2 residual CHANGES_REQUESTED with green gates finalizes to done + audit note."""
        repo, main_wt, home = _init_pool_repo(tmp_path)
        _seed_task_stubs(
            repo,
            main_wt,
            "trc_demo",
            "trc-demo",
            "task_03",
            scenario_id="TRC-EC-04",
            done_gate_pass=True,
        )
        assert (
            _run_pool_cli(
                main_wt, ["init", "trc_demo", "--pool-size", "2"], home=home
            ).returncode
            == 0
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--task",
                    "task_03",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )
        slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
        (slot1 / "src" / "worker.py").write_text("x = 1\n", encoding="utf-8")
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--task",
                    "task_03",
                    "--status",
                    "review",
                ],
                home=home,
            ).returncode
            == 0
        )
        p1_file = _write_json(
            tmp_path / "p1.json",
            [
                {
                    "id": "BLK-1",
                    "category": "BDD_VIOLATION",
                    "file": "src/worker.py",
                    "summary": "Fix x",
                }
            ],
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--status",
                    "working",
                    "--no-reset",
                    "--blockers-file",
                    str(p1_file),
                ],
                home=home,
            ).returncode
            == 0
        )
        (slot1 / "src" / "worker.py").write_text("x = 2\n", encoding="utf-8")
        assert (
            _run_pool_cli(
                main_wt,
                ["sync", "trc_demo", "--slot", "1", "--status", "review"],
                home=home,
            ).returncode
            == 0
        )

        pass2_file = _write_json(
            tmp_path / "pass2.json",
            {
                "task_id": "task_03",
                "pass": 2,
                "verdict": "CHANGES_REQUESTED",
                "head_sha": _git(slot1, "rev-parse", "HEAD"),
                "done_gate": "PASS",
                "blockers": [
                    {
                        "id": "BLK-2",
                        "category": "BDD_VIOLATION",
                        "file": "src/worker.py",
                        "summary": "Residual nit",
                    }
                ],
                "observations": [],
            },
        )
        res_fin = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_03",
                "--mode",
                "pass2-complete",
                "--review-file",
                str(pass2_file),
            ],
            home=home,
        )
        assert res_fin.returncode == 0, res_fin.stderr
        assert (main_wt / ".devtool" / "features" / "done" / "task_03.md").is_file()
        audit_path = (
            main_wt / ".devtool" / "epic" / "trc_demo" / "review_audit_notes.jsonl"
        )
        raw = audit_path.read_text(encoding="utf-8")
        assert "pass2_residual_logged_on_cap" in raw
        assert "BLK-2" in raw
        hb = _read_heartbeat(repo, "trc-demo")
        assert hb["slots"]["slot-1"]["status"] == "idle"
        assert hb["slots"]["slot-1"]["fix_passes_used"] == 0

    def test_trc_ar_02_concurrent_slots_preserve_independent_counters(
        self,
        tmp_path: Path,
    ) -> None:
        """TRC-AR-02: Concurrent slot 1 and slot 2 pool operations preserve independent counters."""
        repo, main_wt, home = _init_pool_repo(
            tmp_path, epic_dir="trc_conc", epic_slug="trc-conc"
        )
        assert (
            _run_pool_cli(
                main_wt, ["init", "trc_conc", "--pool-size", "2"], home=home
            ).returncode
            == 0
        )

        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_conc",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_conc",
                    "--slot",
                    "2",
                    "--task",
                    "task_02",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )

        slot1 = manage_worker_pool.get_slot_path(repo, "trc_conc", 1)
        slot2 = manage_worker_pool.get_slot_path(repo, "trc_conc", 2)
        (slot1 / "src" / "one.py").write_text("one = 1\n", encoding="utf-8")
        (slot2 / "src" / "two.py").write_text("two = 2\n", encoding="utf-8")

        b1 = _write_json(
            tmp_path / "b1.json",
            [
                {
                    "id": "BLK-1",
                    "category": "BDD_VIOLATION",
                    "file": "src/one.py",
                    "summary": "Fix one",
                }
            ],
        )

        def _run_slot1() -> None:
            r1 = _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_conc",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "review",
                ],
                home=home,
            )
            assert r1.returncode == 0, r1.stderr
            r2 = _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_conc",
                    "--slot",
                    "1",
                    "--status",
                    "working",
                    "--no-reset",
                    "--blockers-file",
                    str(b1),
                ],
                home=home,
            )
            assert r2.returncode == 0, r2.stderr

        def _run_slot2() -> None:
            r1 = _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_conc",
                    "--slot",
                    "2",
                    "--task",
                    "task_02",
                    "--status",
                    "review",
                ],
                home=home,
            )
            assert r1.returncode == 0, r1.stderr

        with ThreadPoolExecutor(max_workers=2) as ex:
            f1 = ex.submit(_run_slot1)
            f2 = ex.submit(_run_slot2)
            f1.result()
            f2.result()

        hb = _read_heartbeat(repo, "trc-conc")
        assert hb["slots"]["slot-1"]["review_passes_used"] == 1
        assert hb["slots"]["slot-1"]["fix_passes_used"] == 1
        assert hb["slots"]["slot-2"]["review_passes_used"] == 1
        assert hb["slots"]["slot-2"]["fix_passes_used"] == 0
        assert (
            hb["slots"]["slot-1"]["pass1_tree_sha"]
            != hb["slots"]["slot-2"]["pass1_tree_sha"]
        )
        assert sorted(hb["active_tasks"]) == ["task_01", "task_02"]

    def test_trc_ar_03_mirror_reconciliation_and_parallel_audit_notes(
        self,
        tmp_path: Path,
    ) -> None:
        """TRC-AR-03: Reconcile tracked/untracked .devtool mirrors and commit main_wt audit notes across parallel slots."""
        repo, main_wt, home = _init_pool_repo(
            tmp_path, epic_dir="trc_mirror", epic_slug="trc-mirror"
        )
        _seed_task_stubs(
            repo,
            main_wt,
            "trc_mirror",
            "trc-mirror",
            "task_01",
            scenario_id="TRC-AR-03",
            done_gate_pass=True,
            commit_in_epic=False,
        )
        _seed_task_stubs(
            repo,
            main_wt,
            "trc_mirror",
            "trc-mirror",
            "task_02",
            scenario_id="TRC-AR-03",
            done_gate_pass=True,
            commit_in_epic=True,
        )

        assert (
            _run_pool_cli(
                main_wt, ["init", "trc_mirror", "--pool-size", "2"], home=home
            ).returncode
            == 0
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_mirror",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_mirror",
                    "--slot",
                    "2",
                    "--task",
                    "task_02",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )

        slot1 = manage_worker_pool.get_slot_path(repo, "trc_mirror", 1)
        slot2 = manage_worker_pool.get_slot_path(repo, "trc_mirror", 2)

        for slot_num, task_id in ((1, "task_01"), (2, "task_02")):
            assert (
                _run_pool_cli(
                    main_wt,
                    [
                        "sync",
                        "trc_mirror",
                        "--slot",
                        str(slot_num),
                        "--task",
                        task_id,
                        "--status",
                        "review",
                    ],
                    home=home,
                ).returncode
                == 0
            )
            blocker_file = _write_json(
                tmp_path / f"blk_{task_id}.json",
                [
                    {
                        "id": "BLK-1",
                        "category": "BDD_VIOLATION",
                        "file": f"src/m{slot_num}.py",
                        "summary": f"Surgical fix {task_id}",
                    }
                ],
            )
            assert (
                _run_pool_cli(
                    main_wt,
                    [
                        "sync",
                        "trc_mirror",
                        "--slot",
                        str(slot_num),
                        "--status",
                        "working",
                        "--no-reset",
                        "--blockers-file",
                        str(blocker_file),
                    ],
                    home=home,
                ).returncode
                == 0
            )

        (slot1 / "src" / "m1.py").write_text("m1 = 1\n", encoding="utf-8")
        (slot2 / "src" / "m2.py").write_text("m2 = 2\n", encoding="utf-8")

        for slot_num, task_id in ((1, "task_01"), (2, "task_02")):
            tr_res = _run_pool_cli(
                main_wt,
                [
                    "triage-fix",
                    "trc_mirror",
                    "--slot",
                    str(slot_num),
                    "--task",
                    task_id,
                ],
                home=home,
            )
            assert tr_res.returncode == 0, tr_res.stderr
            assert (
                json.loads(tr_res.stdout)["tier1_status"]
                == "ELIGIBLE_FOR_SHORT_CIRCUIT"
            )

        # Pollute main_wt with unstaged tracked edits + untracked done mirror + non-.devtool file
        (main_wt / ".devtool" / "features" / "task_01.md").write_text(
            '---\nid: "task_01"\nstatus: "review"\n---\n', encoding="utf-8"
        )
        (main_wt / ".devtool" / "epic" / "trc_mirror" / "task_01.md").write_text(
            '---\nid: "task_01"\nstatus: "review"\n---\n', encoding="utf-8"
        )
        done_dir = main_wt / ".devtool" / "features" / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        (done_dir / "task_01.md").write_text(
            '---\nid: "task_01"\nstatus: "done"\n---\n', encoding="utf-8"
        )
        non_devtool_keep = main_wt / "notes_non_devtool.txt"
        non_devtool_keep.write_text("keep me safe\n", encoding="utf-8")

        # Even if slot 1 somehow had a leftover audit file, finalize-slot must exclude it from slot commit
        (
            slot1 / ".devtool" / "epic" / "trc_mirror" / "review_audit_notes.jsonl"
        ).write_text('{"stale": true}\n', encoding="utf-8")

        fin1 = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_mirror",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--mode",
                "tier2-short-circuit",
                "--risk-level",
                "LOW",
                "--rationale",
                "Slot 1 surgical fix",
            ],
            home=home,
        )
        assert fin1.returncode == 0, fin1.stderr

        fin2 = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_mirror",
                "--slot",
                "2",
                "--task",
                "task_02",
                "--mode",
                "tier2-short-circuit",
                "--risk-level",
                "LOW",
                "--rationale",
                "Slot 2 surgical fix",
            ],
            home=home,
        )
        assert fin2.returncode == 0, fin2.stderr

        audit_path = (
            main_wt / ".devtool" / "epic" / "trc_mirror" / "review_audit_notes.jsonl"
        )
        entries = [
            json.loads(ln)
            for ln in audit_path.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
        assert [e["task_id"] for e in entries] == ["task_01", "task_02"]
        assert non_devtool_keep.read_text(encoding="utf-8") == "keep me safe\n"
        # Zero dirty tracked files in main_wt; only the intentional untracked non-.devtool file remains
        assert _git(main_wt, "diff", "--name-only") == ""
        assert _git(main_wt, "diff", "--cached", "--name-only") == ""

        # Verify _reconcile_main_wt_devtool_mirrors never discards dirty tracked non-.devtool files
        (main_wt / "README.md").write_text("# Dirty non-devtool\n", encoding="utf-8")
        manage_worker_pool._reconcile_main_wt_devtool_mirrors(main_wt, "trc_mirror")
        assert (main_wt / "README.md").read_text(
            encoding="utf-8"
        ) == "# Dirty non-devtool\n"

    def test_trc_fr_02_finalize_slot_aborts_on_mechanical_gate_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """TRC-FR-02: finalize-slot exits 1 with MECHANICAL_GATE_FAILED without committing or merging."""
        repo, main_wt, home = _init_pool_repo(tmp_path)
        _seed_task_stubs(
            repo,
            main_wt,
            "trc_demo",
            "trc-demo",
            "task_01",
            scenario_id="TRC-FR-02",
            done_gate_pass=False,
        )
        assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
        assert (
            _run_pool_cli(
                main_wt,
                [
                    "sync",
                    "trc_demo",
                    "--slot",
                    "1",
                    "--task",
                    "task_01",
                    "--status",
                    "working",
                ],
                home=home,
            ).returncode
            == 0
        )

        slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
        uncommitted_file = slot1 / "src" / "broken.py"
        uncommitted_file.write_text("broken = True\n", encoding="utf-8")
        epic_head_before = _git(main_wt, "rev-parse", "HEAD")
        slot_head_before = _git(slot1, "rev-parse", "HEAD")

        res = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--mode",
                "pass1-approved",
            ],
            home=home,
        )
        assert res.returncode == 1
        assert "MECHANICAL_GATE_FAILED" in res.stderr
        assert _git(main_wt, "rev-parse", "HEAD") == epic_head_before
        assert _git(slot1, "rev-parse", "HEAD") == slot_head_before
        assert uncommitted_file.read_text(encoding="utf-8") == "broken = True\n"

        # Also fail when done_gate passes but check_bdd_traceability fails
        (
            slot1
            / "skills"
            / "dev-implementation"
            / "resources"
            / "scripts"
            / "run_task_checks.py"
        ).write_text(
            "import sys\nprint('done gate: PASS')\nsys.exit(0)\n",
            encoding="utf-8",
        )
        (slot1 / "tests" / "test_task_01.py").write_text(
            "def test_task_01():\n    assert True\n", encoding="utf-8"
        )
        res_bdd = _run_pool_cli(
            main_wt,
            [
                "finalize-slot",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--mode",
                "pass1-approved",
            ],
            home=home,
        )
        assert res_bdd.returncode == 1
        assert "MECHANICAL_GATE_FAILED" in res_bdd.stderr
        assert _git(main_wt, "rev-parse", "HEAD") == epic_head_before


def test_trc_fallback_without_state_envelope_and_persona_config(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Direct JSON heartbeat and (2, 1) limit fallbacks work when _state_envelope or persona_config is None."""
    repo, main_wt, _ = _init_pool_repo(tmp_path)
    monkeypatch.setattr(manage_worker_pool, "_STATE_ENVELOPE", None)
    monkeypatch.setattr(manage_worker_pool, "_PERSONA_CONFIG", None)

    manage_worker_pool.init_slots(repo, "trc_demo", "trc-demo", pool_size=2)
    assert manage_worker_pool.sync_slot(
        repo, "trc_demo", "trc-demo", 1, task_id="task_01", status="working"
    )
    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    (slot1 / "src" / "x.py").write_text("x = 1\n", encoding="utf-8")
    assert manage_worker_pool.sync_slot(
        repo, "trc_demo", "trc-demo", 1, task_id="task_01", status="review"
    )

    hb = _read_heartbeat(repo, "trc-demo")
    assert hb["slots"]["slot-1"]["review_passes_used"] == 1
    assert isinstance(hb["slots"]["slot-1"]["pass1_tree_sha"], str)

    assert manage_worker_pool.sync_slot(repo, "trc_demo", "trc-demo", 1, status="idle")
    hb_idle = _read_heartbeat(repo, "trc-demo")
    assert hb_idle["slots"]["slot-1"]["review_passes_used"] == 0
    assert hb_idle["slots"]["slot-1"]["pass1_tree_sha"] is None


def test_trc_redispatch_private_helper_and_pass1_coerced_finalize(
    tmp_path: Path,
) -> None:
    """Verify Pass 1 re-dispatch, private helper exemption, cache symlink exclusion, and coerced pass1 finalize."""
    repo, main_wt, home = _init_pool_repo(tmp_path)
    _seed_task_stubs(
        repo,
        main_wt,
        "trc_demo",
        "trc-demo",
        "task_01",
        scenario_id="TRC-HP-03",
        done_gate_pass=True,
    )
    (main_wt / "node_modules").mkdir()
    (main_wt / "node_modules" / "pkg.js").write_text("// cached\n", encoding="utf-8")

    assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--status",
                "working",
            ],
            home=home,
        ).returncode
        == 0
    )
    # Re-dispatching working --no-reset before any review preserves counters at (0, 0)
    assert (
        _run_pool_cli(
            main_wt,
            ["sync", "trc_demo", "--slot", "1", "--status", "working", "--no-reset"],
            home=home,
        ).returncode
        == 0
    )
    hb0 = _read_heartbeat(repo, "trc-demo")
    assert hb0["slots"]["slot-1"]["review_passes_used"] == 0
    assert hb0["slots"]["slot-1"]["fix_passes_used"] == 0

    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    assert (slot1 / "node_modules").is_symlink()
    (slot1 / "src" / "priv.py").write_text(
        "def _private_helper(x: int) -> int:\n    return x\n",
        encoding="utf-8",
    )
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--status",
                "review",
            ],
            home=home,
        ).returncode
        == 0
    )

    # Verify private helper def line change does not trigger PUBLIC_SIGNATURE_CHANGED
    blocker_file = _write_json(
        tmp_path / "b.json",
        [
            {
                "id": "BLK-1",
                "category": "BDD_VIOLATION",
                "file": "src/priv.py",
                "summary": "Rename arg",
            }
        ],
    )
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--status",
                "working",
                "--no-reset",
                "--blockers-file",
                str(blocker_file),
            ],
            home=home,
        ).returncode
        == 0
    )
    (slot1 / "src" / "priv.py").write_text(
        "def _private_helper(x: int, scale: int = 2) -> int:\n    return x * scale\n",
        encoding="utf-8",
    )
    triage_res = _run_pool_cli(
        main_wt,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_01"],
        home=home,
    )
    assert triage_res.returncode == 0, triage_res.stderr
    triage = json.loads(triage_res.stdout)
    assert triage["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT"
    assert triage["triggers"] == []

    # Coerced Pass 1 review payload logged during pass1-approved finalize-slot
    coerced_file = _write_json(
        tmp_path / "coerced_p1.json",
        {
            "task_id": "task_01",
            "pass": 1,
            "verdict": "CHANGES_REQUESTED",
            "done_gate": "PASS",
            "blockers": [],
            "observations": [
                {"id": "OBS-1", "file": "src/priv.py", "summary": "Minor nit"}
            ],
        },
    )
    fin_res = _run_pool_cli(
        main_wt,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "pass1-approved",
            "--review-file",
            str(coerced_file),
        ],
        home=home,
    )
    assert fin_res.returncode == 0, fin_res.stderr
    audit_path = main_wt / ".devtool" / "epic" / "trc_demo" / "review_audit_notes.jsonl"
    entries = [
        json.loads(ln)
        for ln in audit_path.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    assert entries[-1]["event"] == "coerced_non_blocking_approval"
    assert entries[-1]["coerced_from_non_blocking"] is True
    assert (
        "node_modules"
        not in _git(main_wt, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    )

    # Seeded working status at (review=2, fix=1) also rejects sync --working --no-reset with HARD_FIX_CAP_EXCEEDED
    hb_cap = _read_heartbeat(repo, "trc-demo")
    hb_cap["slots"]["slot-1"].update(
        {
            "status": "working",
            "task_id": "task_01",
            "review_passes_used": 2,
            "fix_passes_used": 1,
        }
    )
    _write_heartbeat(repo, "trc-demo", hb_cap)
    cap_res = _run_pool_cli(
        main_wt,
        ["sync", "trc_demo", "--slot", "1", "--status", "working", "--no-reset"],
        home=home,
    )
    assert cap_res.returncode == 2
    assert "HARD_FIX_CAP_EXCEEDED" in cap_res.stderr


def test_trc_round1_fail_closed_preconditions_and_prefix_resolution(
    tmp_path: Path,
) -> None:
    """Round 1 fixes: fail-closed task mirror/prefix resolution, triage-fix/short-circuit preconditions, and APPROVED-with-blockers."""
    # 1. Missing task file fails closed without commit/merge; unambiguous short prefix resolves
    repo, main_wt, home = _init_pool_repo(tmp_path / "prefix_case")
    _seed_task_stubs(
        repo,
        main_wt,
        "trc_demo",
        "trc-demo",
        "task_01_alpha",
        scenario_id="TRC-FR-02",
        done_gate_pass=True,
    )
    assert _run_pool_cli(main_wt, ["init", "trc_demo"], home=home).returncode == 0
    assert (
        _run_pool_cli(
            main_wt,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--status",
                "working",
            ],
            home=home,
        ).returncode
        == 0
    )
    slot1 = manage_worker_pool.get_slot_path(repo, "trc_demo", 1)
    (slot1 / "src" / "feat.py").write_text("v = 1\n", encoding="utf-8")
    epic_head_before = _git(main_wt, "rev-parse", "HEAD")
    slot_head_before = _git(slot1, "rev-parse", "HEAD")

    res_missing = _run_pool_cli(
        main_wt,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_99",
            "--mode",
            "pass1-approved",
        ],
        home=home,
    )
    assert res_missing.returncode == 1
    assert "MECHANICAL_GATE_FAILED" in res_missing.stderr
    assert _git(main_wt, "rev-parse", "HEAD") == epic_head_before
    assert _git(slot1, "rev-parse", "HEAD") == slot_head_before

    bad_approved_file = _write_json(
        tmp_path / "bad_approved.json",
        {
            "task_id": "task_01_alpha",
            "pass": 1,
            "verdict": "APPROVED",
            "done_gate": "PASS",
            "blockers": [{"id": "BLK-1", "summary": "Bug"}],
        },
    )
    res_bad_approved = _run_pool_cli(
        main_wt,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "pass1-approved",
            "--review-file",
            str(bad_approved_file),
        ],
        home=home,
    )
    assert res_bad_approved.returncode == 1
    assert "MECHANICAL_GATE_FAILED" in res_bad_approved.stderr
    assert _git(main_wt, "rev-parse", "HEAD") == epic_head_before

    res_prefix = _run_pool_cli(
        main_wt,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "pass1-approved",
        ],
        home=home,
    )
    assert res_prefix.returncode == 0, res_prefix.stderr
    assert (main_wt / ".devtool" / "features" / "done" / "task_01_alpha.md").is_file()

    # 2. triage-fix requires fix_passes_used == 1; tier2-short-circuit requires current ELIGIBLE last_triage
    repo2, main_wt2, home2 = _init_pool_repo(tmp_path / "triage_case")
    _seed_task_stubs(
        repo2,
        main_wt2,
        "trc_demo",
        "trc-demo",
        "task_01",
        scenario_id="TRC-HP-03",
        done_gate_pass=True,
    )
    (main_wt2 / "src" / "calc.py").write_text(
        "def compute_score(x: int) -> int:\n    return x\n", encoding="utf-8"
    )
    _git(main_wt2, "add", ".")
    _git(main_wt2, "commit", "-q", "-m", "Add calc")
    assert _run_pool_cli(main_wt2, ["init", "trc_demo"], home=home2).returncode == 0
    assert (
        _run_pool_cli(
            main_wt2,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--status",
                "working",
            ],
            home=home2,
        ).returncode
        == 0
    )
    assert (
        _run_pool_cli(
            main_wt2,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--task",
                "task_01",
                "--status",
                "review",
            ],
            home=home2,
        ).returncode
        == 0
    )
    res_triage_before_fix = _run_pool_cli(
        main_wt2,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_01"],
        home=home2,
    )
    assert res_triage_before_fix.returncode == 1
    assert "fix_passes_used == 1" in res_triage_before_fix.stderr

    blocker_file = _write_json(
        tmp_path / "blk_triage.json",
        [{"id": "BLK-1", "category": "BDD_VIOLATION", "summary": "Fix calc"}],
    )
    assert (
        _run_pool_cli(
            main_wt2,
            [
                "sync",
                "trc_demo",
                "--slot",
                "1",
                "--status",
                "working",
                "--no-reset",
                "--blockers-file",
                str(blocker_file),
            ],
            home=home2,
        ).returncode
        == 0
    )

    # Missing last_triage
    res_no_triage = _run_pool_cli(
        main_wt2,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "tier2-short-circuit",
            "--risk-level",
            "LOW",
        ],
        home=home2,
    )
    assert res_no_triage.returncode == 1
    assert "MECHANICAL_GATE_FAILED" in res_no_triage.stderr

    # HIGH_RISK last_triage rejected by tier2-short-circuit
    slot2_1 = manage_worker_pool.get_slot_path(repo2, "trc_demo", 1)
    (slot2_1 / "src" / "calc.py").write_text(
        "def compute_score(x: int, factor: int = 2) -> int:\n    return x * factor\n",
        encoding="utf-8",
    )
    res_high = _run_pool_cli(
        main_wt2,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_01"],
        home=home2,
    )
    assert res_high.returncode == 0
    assert json.loads(res_high.stdout)["tier1_status"] == "HIGH_RISK"
    res_fin_high = _run_pool_cli(
        main_wt2,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "tier2-short-circuit",
            "--risk-level",
            "LOW",
        ],
        home=home2,
    )
    assert res_fin_high.returncode == 1
    assert "MECHANICAL_GATE_FAILED" in res_fin_high.stderr

    # Eligible triage becomes stale after subsequent slot edit
    (slot2_1 / "src" / "calc.py").write_text(
        "def compute_score(x: int) -> int:\n    return x\n", encoding="utf-8"
    )
    (slot2_1 / "src" / "patch.py").write_text("p = 1\n", encoding="utf-8")
    res_eligible = _run_pool_cli(
        main_wt2,
        ["triage-fix", "trc_demo", "--slot", "1", "--task", "task_01"],
        home=home2,
    )
    assert res_eligible.returncode == 0
    assert (
        json.loads(res_eligible.stdout)["tier1_status"] == "ELIGIBLE_FOR_SHORT_CIRCUIT"
    )

    (slot2_1 / "src" / "patch.py").write_text("p = 2\n", encoding="utf-8")
    res_stale = _run_pool_cli(
        main_wt2,
        [
            "finalize-slot",
            "trc_demo",
            "--slot",
            "1",
            "--task",
            "task_01",
            "--mode",
            "tier2-short-circuit",
            "--risk-level",
            "LOW",
        ],
        home=home2,
    )
    assert res_stale.returncode == 1
    assert "MECHANICAL_GATE_FAILED" in res_stale.stderr
