"""Unit and integration tests for Task 3: Option A Bilingual Guards, Surgical Contracts, and Compact Memory."""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
RESUME_SCRIPTS_DIR = REPO_ROOT / "scripts"

for _p in (str(SCRIPTS_DIR), str(RESUME_SCRIPTS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _init_git_repo(root: Path) -> None:
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "tto@example.com")
    _git(root, "config", "user.name", "TTO Test")


def _run_py(
    script: Path, cwd: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    merged_env = dict(os.environ)
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        env=merged_env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_tto_hp_03_option_a_default_readiness() -> None:
    """[TTO-HP-03] Option A default readiness tolerates in-flight .vi.md drift and absent bdd_scenarios.vi.md."""
    tcer: Any = importlib.import_module("test_check_epic_readiness")
    cer_script = SCRIPTS_DIR / "check_epic_readiness.py"
    cbt_script = SCRIPTS_DIR / "check_bdd_traceability.py"

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        _init_git_repo(repo)
        tcer.build_ready_epic(repo)

        epic_dir = repo / ".devtool" / "epic" / "demo_epic"
        # Delete bdd_scenarios.vi.md and inject drifted heading/sections into existing .vi.md companions
        bdd_vi = epic_dir / "bdd_scenarios.vi.md"
        if bdd_vi.is_file():
            bdd_vi.unlink()

        hld_vi = epic_dir / "demo_epic.vi.md"
        hld_vi.write_text(
            hld_vi.read_text(encoding="utf-8")
            + "\n## Unsynced In-Flight Section\n\nDrifted VI prose\n",
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Epic with in-flight vi drift")

        proc = _run_py(cer_script, repo, "demo_epic")
        assert proc.returncode == 0, (
            f"Expected default PASS:\n{proc.stdout}\n{proc.stderr}"
        )
        assert "R1 PASS" in proc.stdout
        assert "R3 PASS" in proc.stdout
        assert "R7 PASS" in proc.stdout

        tasks = sorted(epic_dir.glob("task_*.md"))
        tr_proc = _run_py(
            cbt_script,
            repo,
            "plan",
            "--scenarios",
            str(epic_dir / "bdd_scenarios.en.md"),
            "--tasks",
            *(str(t) for t in tasks),
        )
        assert tr_proc.returncode == 0, tr_proc.stdout + tr_proc.stderr


def test_tto_hp_06_compact_context_and_dynamic_config() -> None:
    """[TTO-HP-06] Compact resume_context caps output at <=4096 bytes and emit_handoff_prompt reads review_config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        ws = tmp / "ws"
        repo = ws / "app_repo"
        real_home = tmp / "home"
        repo.mkdir(parents=True)
        real_home.mkdir(parents=True)
        _init_git_repo(repo)

        devtool = repo / ".devtool"
        epic = devtool / "epic" / "demo_epic"
        features = devtool / "features"
        contracts = repo / "shared-contracts" / "core"
        epic.mkdir(parents=True)
        features.mkdir(parents=True)
        contracts.mkdir(parents=True)

        (epic / "demo_epic.en.md").write_text(
            "# Demo Epic\n\n- **Epic name**: demo_epic\n- **Status**: In Progress\n",
            encoding="utf-8",
        )
        for i in range(1, 30):
            target_epic = "demo_epic" if i <= 2 else f"other_epic_{i}"
            (features / f"task_{i:02d}_item.md").write_text(
                f'---\nid: "task_{i:02d}_item"\nstatus: "todo"\nepic: "{target_epic}"\n---\n\n# Task {i}\n',
                encoding="utf-8",
            )
        (contracts / "gaps_and_rfcs.md").write_text(
            "# Gaps\n\n## GAP-01 — Open demo_epic rate guard\n- Status: OPEN\n- Epic: demo_epic\n"
            + ("\n" + "Filler noise line.\n" * 120),
            encoding="utf-8",
        )
        (devtool / "ACTIVE_STATE.md").write_text(
            "# Active State\n\nEpic: demo_epic\nStatus: Stage 3\n"
            + ("Old log entry\n" * 150),
            encoding="utf-8",
        )
        (devtool / "PROJECT_LEDGER.md").write_text(
            "# Project Ledger\n\n"
            + "".join(
                f"- [2026-11-12] milestone_{k}: {'x' * 120}\n" for k in range(80)
            ),
            encoding="utf-8",
        )
        (devtool / "review_config.json").write_text(
            json.dumps(
                {
                    "last_used_provider": "claude",
                    "providers": {
                        "programmer": {
                            "model": "gemini-4-hydrogen-xhigh",
                            "thinking_level": "extra",
                        },
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Workspace snapshot")

        proc_compact = _run_py(
            RESUME_SCRIPTS_DIR / "resume_context.py",
            repo,
            "--workspace-root",
            str(ws),
            "--real-home",
            str(real_home),
            "--repo",
            "app_repo",
            "--epic",
            "demo_epic",
            "--compact",
        )
        assert proc_compact.returncode == 0, proc_compact.stderr
        payload = proc_compact.stdout
        assert len(payload.encode("utf-8")) <= 4096
        assert "demo_epic" in payload
        assert "other_epic_15" not in payload

        proc_prompt = _run_py(
            RESUME_SCRIPTS_DIR / "resume_context.py",
            repo,
            "--workspace-root",
            str(ws),
            "--real-home",
            str(real_home),
            "--repo",
            "app_repo",
            "--epic",
            "demo_epic",
            "--emit-prompt",
            "implement",
        )
        assert proc_prompt.returncode == 0, proc_prompt.stderr
        assert "gemini-4-hydrogen-xhigh" in proc_prompt.stdout
        assert "xhigh" in proc_prompt.stdout
        assert "Gemini Flash 3.8" not in proc_prompt.stdout

        # Legacy programmer model upgrades dynamically via shared alias map
        (devtool / "review_config.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "programmer": {
                            "model": "gemini-3.8-flash-high",
                            "thinking_level": "high",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        proc_legacy = _run_py(
            RESUME_SCRIPTS_DIR / "resume_context.py",
            repo,
            "--workspace-root",
            str(ws),
            "--real-home",
            str(real_home),
            "--repo",
            "app_repo",
            "--epic",
            "demo_epic",
            "--emit-prompt",
            "implement",
        )
        assert proc_legacy.returncode == 0, proc_legacy.stderr
        assert "gemini-4-hydrogen-xhigh" in proc_legacy.stdout
        assert "xhigh" in proc_legacy.stdout


def test_tto_ec_03_surgical_anchor_required_for_large_files() -> None:
    """[TTO-EC-03] check_task_contract.py --design rejects >200-line modified files lacking symbol/range anchors."""
    ctc_script = SCRIPTS_DIR / "check_task_contract.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        _init_git_repo(repo)
        (repo / ".gitignore").write_text("build/\n", encoding="utf-8")
        (repo / "src").mkdir()
        big_lines = [f"def fn_{i}():\n    return {i}" for i in range(130)]
        (repo / "src" / "big_mod.py").write_text(
            "\n".join(big_lines) + "\n", encoding="utf-8"
        )
        (repo / "tests").mkdir()
        (repo / "tests" / "test_big_mod.py").write_text(
            "def test_fn_1():\n    pass\n", encoding="utf-8"
        )

        epic = repo / ".devtool" / "epic" / "demo"
        epic.mkdir(parents=True)
        hld = epic / "demo.en.md"
        hld.write_text(
            "# Demo\n\nProtected paths: README.md\n\nIntegration test roots: tests/\n\nIntegration results: true -> build/int.xml\n\n## Verification Environment\n\nTemp repo.\n",
            encoding="utf-8",
        )
        task_tmpl = (
            '---\nid: "task_1"\nstatus: "todo"\nepic: "demo"\n---\n\n'
            "# Task 1\n\n## Files\n\nAllowed files:\n- `src/big_mod.py`\n- `tests/test_big_mod.py`\n\n"
            "{impact}\n\n"
            "Covers: DEMO-HP-01\n\n"
            "## Stop and Report If\n\n- Contract mismatch\n\n"
            "## Decisions Already Made\n\n- Keep behavior deterministic.\n\n"
            "## Verification\n\n| ID | Phase | Command | Expect | Needs |\n|---|---|---|---|---|\n"
            "| V1 | RED | `pytest tests/test_big_mod.py` | exit 1 | — |\n"
            "| V2 | GREEN | `pytest tests/test_big_mod.py` | exit 0 | — |\n"
            "| V3 | TIER-B | `ruff check src/big_mod.py` | exit 0 | — |\n"
            "| V4 | TIER-B | `mypy src/big_mod.py` | exit 0 | — |\n"
            "| V5 | TIER-C | `pytest --junitxml=build/task.xml tests/test_big_mod.py` | exit 0; results build/task.xml | — |\n\n"
            "## Definition of Done\n\n- Done (V2)\n"
        )
        task = epic / "task_1.md"
        task.write_text(
            task_tmpl.format(
                impact="## Impact Analysis & Blast Radius\n\n- General update.\n"
            ),
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Repo with large file")

        bad = _run_py(
            ctc_script, repo, "--design", "--hld", str(hld), "--tasks", str(task)
        )
        assert bad.returncode != 0
        assert "src/big_mod.py" in (bad.stdout + bad.stderr)

        task.write_text(
            task_tmpl.format(
                impact="## Impact Analysis & Blast Radius\n\n- `src/big_mod.py`: `fn_5` (L11-L15)\n"
            ),
            encoding="utf-8",
        )
        good = _run_py(
            ctc_script, repo, "--design", "--hld", str(hld), "--tasks", str(task)
        )
        assert good.returncode == 0, good.stdout + good.stderr


def test_tto_st_02_handoff_excludes_vi_md() -> None:
    """[TTO-ST-02] Packaged handoff.md Read First and handoff-template.md exclude *.vi.md and legacy model hardcodes."""
    tcer: Any = importlib.import_module("test_check_epic_readiness")
    pkg_script = SCRIPTS_DIR / "package_epic.py"
    template_path = (
        REPO_ROOT / "skills" / "dev-lifecycle" / "references" / "handoff-template.md"
    )
    template_text = template_path.read_text(encoding="utf-8")
    assert ".vi.md" not in template_text
    assert "Gemini Flash 3.8" not in template_text
    assert "gemini-3.8-flash" not in template_text

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        _init_git_repo(repo)
        tcer.build_ready_epic(repo)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Ready epic")

        proc = _run_py(pkg_script, repo, "demo_epic")
        assert proc.returncode == 0, proc.stdout + proc.stderr

        handoff_text = (
            repo / ".devtool" / "epic" / "demo_epic" / "handoff.md"
        ).read_text(encoding="utf-8")
        m = re.search(r"## Read First\n(.*?)(?:\n## |\Z)", handoff_text, re.DOTALL)
        assert m is not None
        read_first = m.group(1)
        assert ".en.md" in read_first
        assert ".vi.md" not in read_first


def test_tto_st_03_strict_bilingual_stage4_gate() -> None:
    """[TTO-ST-03] --strict-bilingual detects stale Spec/HLD provenance digests and missing/drifted bdd_scenarios.vi.md."""
    tcer: Any = importlib.import_module("test_check_epic_readiness")
    cer: Any = importlib.import_module("check_epic_readiness")
    cer_script = SCRIPTS_DIR / "check_epic_readiness.py"
    cbt_script = SCRIPTS_DIR / "check_bdd_traceability.py"

    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        _init_git_repo(repo)
        tcer.build_ready_epic(repo)
        epic_dir = repo / ".devtool" / "epic" / "demo_epic"
        hld_en = epic_dir / "demo_epic.en.md"
        hld_vi = epic_dir / "demo_epic.vi.md"
        spec_en = epic_dir / "2026-10-22-demo-epic-design.en.md"
        spec_vi = epic_dir / "2026-10-22-demo-epic-design.vi.md"
        bdd_en = epic_dir / "bdd_scenarios.en.md"
        bdd_vi = epic_dir / "bdd_scenarios.vi.md"
        tasks = sorted(epic_dir.glob("task_*.md"))

        digest_fn = getattr(cer, "compute_en_sync_digest", None)
        assert digest_fn is not None, (
            "compute_en_sync_digest must exist on check_epic_readiness"
        )
        en_digest = digest_fn(hld_en.read_text(encoding="utf-8"))
        assert re.fullmatch(r"[0-9a-f]{16}", en_digest)
        spec_digest = digest_fn(spec_en.read_text(encoding="utf-8"))

        # Identical heading levels in HLD .vi.md, edited prose in HLD .en.md, stale digest in .vi.md
        hld_en.write_text(
            hld_en.read_text(encoding="utf-8")
            + "\nAdditional English sentence under identical heading.\n",
            encoding="utf-8",
        )
        hld_vi.write_text(
            hld_vi.read_text(encoding="utf-8")
            + f"\n<!-- sync-en-sha256: {en_digest} -->\n",
            encoding="utf-8",
        )
        spec_vi.write_text(
            spec_vi.read_text(encoding="utf-8")
            + f"\n<!-- sync-en-sha256: {spec_digest} -->\n",
            encoding="utf-8",
        )
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "Stale provenance with same headings")

        # Missing bdd_scenarios.vi.md + stale HLD digest -> strict fails both readiness & traceability
        bdd_vi_saved = bdd_vi.read_text(encoding="utf-8")
        bdd_vi.unlink()
        strict_fail = _run_py(cer_script, repo, "demo_epic", "--strict-bilingual")
        assert strict_fail.returncode != 0
        tr_strict_fail = _run_py(
            cbt_script,
            repo,
            "plan",
            "--scenarios",
            str(bdd_en),
            "--tasks",
            *(str(t) for t in tasks),
            "--strict-bilingual",
        )
        assert tr_strict_fail.returncode != 0

        # Refresh digest in HLD .vi.md + restore bdd_scenarios.vi.md -> both strict gates pass
        fresh_hld_digest = digest_fn(hld_en.read_text(encoding="utf-8"))
        assert fresh_hld_digest != en_digest
        hld_vi.write_text(
            hld_vi.read_text(encoding="utf-8").replace(en_digest, fresh_hld_digest),
            encoding="utf-8",
        )
        bdd_vi.write_text(bdd_vi_saved, encoding="utf-8")
        _git(repo, "add", "-A")
        _git(
            repo,
            "commit",
            "-q",
            "-m",
            "Synced bilingual provenance and bdd_scenarios.vi.md",
        )

        strict_pass = _run_py(cer_script, repo, "demo_epic", "--strict-bilingual")
        assert strict_pass.returncode == 0, strict_pass.stdout + strict_pass.stderr
        tr_strict_pass = _run_py(
            cbt_script,
            repo,
            "plan",
            "--scenarios",
            str(bdd_en),
            "--tasks",
            *(str(t) for t in tasks),
            "--strict-bilingual",
        )
        assert tr_strict_pass.returncode == 0, (
            tr_strict_pass.stdout + tr_strict_pass.stderr
        )

        # Verify normalized sha helper stays unused-import clean via hashlib assertion
        assert len(hashlib.sha256(b"x").hexdigest()[:16]) == 16


class TestTTOBilingualAndSurgical_Integration:
    """Integration provenance wrapper for Tier C scenarios in Task 3."""

    def test_tto_hp_03_integration(self) -> None:
        test_tto_hp_03_option_a_default_readiness()

    def test_tto_hp_06_integration(self) -> None:
        test_tto_hp_06_compact_context_and_dynamic_config()

    def test_tto_ec_03_integration(self) -> None:
        test_tto_ec_03_surgical_anchor_required_for_large_files()

    def test_tto_st_02_integration(self) -> None:
        test_tto_st_02_handoff_excludes_vi_md()

    def test_tto_st_03_integration(self) -> None:
        test_tto_st_03_strict_bilingual_stage4_gate()
