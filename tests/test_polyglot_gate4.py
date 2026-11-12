"""Unit and Integration Tests for Polyglot Gate 4 Registry and Multi-Provider Fan-Out (Task 04)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QC_SCRIPTS = REPO_ROOT / "skills" / "quality_check" / "resources" / "scripts"
SETUP_SCRIPTS = REPO_ROOT / "skills" / "setup_quality_check" / "resources" / "scripts"

if str(QC_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(QC_SCRIPTS))
if str(SETUP_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SETUP_SCRIPTS))

from scaffold_quality_manifest import build_registry_data, detect_platforms
from verify_polyglot_registry import fanout_and_aggregate, verify_polyglot_execution

SAMPLE_SHA = "b1c2d3e4f5a60718293a4b5c6d7e8f9012345679"


def polyglot_d3nexus_registry() -> dict:
    return {
        "schema_version": 1,
        "providers": [
            {
                "id": "rust-core",
                "skill": "d3nexus:rust-quality-check",
                "required": True,
                "profiles": ["pr", "epic", "release", "scheduled"],
            },
            {
                "id": "learning-web",
                "skill": "d3nexus:web-quality-check",
                "required": True,
                "profiles": ["pr", "epic", "release", "scheduled"],
            },
        ],
    }


def sample_provider_result(provider_id: str, status: str) -> dict:
    return {
        "provider_id": provider_id,
        "contract_version": 1,
        "profile": "epic",
        "repository_sha": SAMPLE_SHA,
        "status": status,
        "checks": [
            {
                "id": f"{provider_id}-check-1",
                "category": "compile",
                "status": status,
                "source": "check command",
                "duration": 1.2,
                "summary": f"{provider_id} test check",
                "evidence_refs": ["ev-1"],
            }
        ],
        "coverage": {},
        "evidence": [
            {
                "id": "ev-1",
                "type": "command",
                "source": "check command",
                "location": f"artifacts/{provider_id}.log",
            }
        ],
        "started_head": SAMPLE_SHA,
        "finished_head": SAMPLE_SHA,
        "duration": 5.4,
        "blockers": [] if status == "PASS" else [f"{provider_id} encountered failure"],
        "warnings": [],
    }


def test_polyglot_fanout():
    """GREEN phase assertion for Task 04: Polyglot registry fanout and aggregation precedence."""
    registry = polyglot_d3nexus_registry()

    # 1. Both providers PASS -> Aggregated PASS
    res_both_pass = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "PASS"),
        ],
    )
    assert res_both_pass["status"] == "PASS"
    assert len(res_both_pass["plan"]) == 2

    # 2. Reduction precedence: FAIL > BLOCKED > PASS
    res_one_fail = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "FAIL"),
        ],
    )
    assert res_one_fail["status"] == "FAIL"

    res_one_blocked = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=SAMPLE_SHA,
        provider_results=[
            sample_provider_result("rust-core", "PASS"),
            sample_provider_result("learning-web", "BLOCKED"),
        ],
    )
    assert res_one_blocked["status"] == "BLOCKED"


def test_WQG_AR_01_concurrent_multiprovider_fanout():
    """Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4."""
    import subprocess

    fixture_dir = REPO_ROOT / "tests" / "fixtures" / "astro_repo"
    registry_file = fixture_dir / ".agents" / "quality" / "check_quality.json"
    registry = json.loads(registry_file.read_text(encoding="utf-8"))

    fixture_sha = SAMPLE_SHA
    try:
        head_proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(fixture_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if head_proc.returncode == 0 and head_proc.stdout.strip():
            fixture_sha = head_proc.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    # Execute concurrent live fanout across declared providers in fixture repo
    exec_result = verify_polyglot_execution(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=fixture_sha,
        repo_root=fixture_dir,
        execute=True,
    )

    assert exec_result["status"] == "PASS"
    assert exec_result["aggregated"]["status"] == "PASS"
    assert len(exec_result["aggregated"]["providers"]) == 2
    ids = [p["provider_id"] for p in exec_result["aggregated"]["providers"]]
    assert "learning-web" in ids
    assert "agent-tools-python" in ids
    # Verify outputs are isolated and both succeeded
    for p in exec_result["aggregated"]["providers"]:
        assert p["status"] == "PASS"
        assert len(p["checks"]) > 0


def test_scaffolding_detects_web_and_generates_manifest():
    """Verify scaffold_quality_manifest detects web projects and generates web-quality config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        (tmp_path / "package.json").write_text(json.dumps({"name": "test-web-app"}))
        (tmp_path / "playwright.config.ts").write_text("// config")

        detected = detect_platforms(tmp_path)
        assert "web" in detected

        reg = build_registry_data(detected)
        providers = reg.get("providers", [])
        web_provider = next((p for p in providers if p["id"] == "web-quality"), None)
        assert web_provider is not None
        assert web_provider["skill"] == "d3nexus:web-quality-check"


def test_verify_polyglot_registry_cli_execution():
    """Verify verify_polyglot_registry CLI accepts result files and execute flag."""
    from verify_polyglot_registry import main

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        reg_file = tmp_path / "check_quality.json"
        res_file = tmp_path / "result.json"

        registry = {
            "schema_version": 1,
            "providers": [
                {
                    "id": "learning-web",
                    "skill": "d3nexus:web-quality-check",
                    "required": True,
                    "profiles": ["epic"],
                }
            ],
        }
        reg_file.write_text(json.dumps(registry))

        res_data = sample_provider_result("learning-web", "PASS")
        res_file.write_text(json.dumps(res_data))

        code = main(
            [
                str(reg_file),
                "--profile",
                "epic",
                "--results",
                str(res_file),
                "--sha",
                SAMPLE_SHA,
            ]
        )
        assert code == 0


def test_polyglot_sha_mismatch_and_drift_rejection():
    """Verify that verify_polyglot_registry rejects mismatched requested SHA and Git HEAD drift."""
    fixture_dir = REPO_ROOT / "tests" / "fixtures" / "astro_repo"
    registry_file = fixture_dir / ".agents" / "quality" / "check_quality.json"
    registry = json.loads(registry_file.read_text(encoding="utf-8"))

    # 1. Executing live provider with incorrect all-a SHA against committed git repository fails
    mismatch_sha = "a" * 40
    exec_res = verify_polyglot_execution(
        registry_data=registry,
        requested_profile="epic",
        repository_sha=mismatch_sha,
        repo_root=fixture_dir,
        execute=True,
    )
    assert exec_res["status"] == "FAIL"
    assert any("mismatch" in str(b).lower() for b in exec_res["aggregated"]["blockers"])

    # 2. Aggregating provider result where started_head != finished_head (drift) fails
    drift_result = sample_provider_result("learning-web", "PASS")
    drift_result["started_head"] = "1" * 40
    drift_result["finished_head"] = "2" * 40
    python_result = sample_provider_result("agent-tools-python", "PASS")
    python_result["started_head"] = "1" * 40
    python_result["finished_head"] = "1" * 40
    agg_res = fanout_and_aggregate(
        registry_data=registry,
        requested_profile="epic",
        repository_sha="1" * 40,
        provider_results=[drift_result, python_result],
    )
    assert agg_res["status"] == "FAIL"
    assert any("drift" in str(b).lower() for b in agg_res["aggregated"]["blockers"])


def _init_tto_quality_repo(tmp_path: Path, test_script: str) -> tuple[Path, Path]:
    import subprocess

    repo = tmp_path / "py_quality_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "tto@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "TTO Test"], cwd=repo, check=True)

    (repo / "lint_check.py").write_text(
        "for i in range(60):\n    print(f'lint_ok_line_{i:02d}')\n",
        encoding="utf-8",
    )
    (repo / "test_check.py").write_text(test_script, encoding="utf-8")

    agents_dir = repo / ".agents" / "quality"
    agents_dir.mkdir(parents=True)
    registry = {
        "schema_version": 1,
        "providers": [
            {
                "id": "python-core",
                "skill": "d3nexus:python-quality-check",
                "required": True,
                "profiles": ["pr", "epic"],
            }
        ],
    }
    py_manifest = {
        "schema_version": 1,
        "capabilities": {
            "lint": [sys.executable, "lint_check.py"],
            "test": [sys.executable, "test_check.py"],
        },
        "profiles": {
            "pr": ["lint", "test"],
            "epic": ["lint", "test"],
        },
    }
    reg_file = agents_dir / "check_quality.json"
    reg_file.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (agents_dir / "python-quality.json").write_text(
        json.dumps(py_manifest, indent=2) + "\n", encoding="utf-8"
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "Init quality repo"], cwd=repo, check=True
    )
    return repo, reg_file


def test_tto_hp_02_compact_gate4_single_line_pass():
    """[TTO-HP-02] Compact Gate 4 prints single-line GATE_PASS entries and stores full raw logs."""
    import subprocess

    script = (
        REPO_ROOT
        / "skills"
        / "quality_check"
        / "resources"
        / "scripts"
        / "verify_polyglot_registry.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        repo, reg_file = _init_tto_quality_repo(
            Path(tmpdir),
            "for i in range(60):\n    print(f'test_ok_line_{i:02d}')\n",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                str(reg_file),
                "--profile",
                "pr",
                "--execute",
                "--compact",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0
        out = proc.stdout
        assert "GATE_PASS:" in out
        assert "GATE_PASS: python-core:lint" in out
        assert "GATE_PASS: python-core:test" in out
        assert '"provider_id"' not in out
        assert "lint_ok_line_00" not in out
        lint_log = repo / "build" / "quality" / "python-core" / "lint.log"
        test_log = repo / "build" / "quality" / "python-core" / "test.log"
        assert lint_log.is_file() and "lint_ok_line_59" in lint_log.read_text(
            encoding="utf-8"
        )
        assert test_log.is_file() and "test_ok_line_59" in test_log.read_text(
            encoding="utf-8"
        )


def test_tto_ec_02_tail_lines_25_and_python_quiet_flags():
    """[TTO-EC-02] Task runner enforces 25-line non-empty tail and Python manifests inject quiet pytest flags."""
    import importlib
    import subprocess

    dev_scripts = REPO_ROOT / "skills" / "dev-implementation" / "resources" / "scripts"
    if str(dev_scripts) not in sys.path:
        sys.path.insert(0, str(dev_scripts))
    rtc = importlib.import_module("run_task_checks")
    assert rtc.TAIL_LINES == 25

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_repo = Path(tmpdir)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_repo, check=True)
        cmd = (
            f'{sys.executable} -c "import sys; '
            "[print(f'out_{i:03d}\\n') for i in range(60)]; "
            "sys.stdout.flush(); "
            "[print(f'err_{i:03d}\\n', file=sys.stderr) for i in range(60)]; "
            'sys.exit(1)"'
        )
        row = rtc.Row(
            id="V1",
            phase="GREEN",
            command=cmd,
            expect=rtc._tc.parse_expect("exit 0"),
            expect_text="exit 0",
            needs=[],
        )
        rec = rtc.run_row(row, tmp_repo, timeout=30, scenario_ids=[])
        tail = rec["output_tail"]
        assert len(tail) == 25
        assert all(line.strip() for line in tail)
        assert tail[-1] == "err_059"
        assert tail[0] == "err_035"

    py_manifest = json.loads(
        (REPO_ROOT / ".agents" / "quality" / "python-quality.json").read_text(
            encoding="utf-8"
        )
    )
    for cmd_tokens in (
        py_manifest["capabilities"]["test"],
        __import__("scaffold_quality_manifest").PLATFORM_CONFIGS["python"]["manifest"][
            "capabilities"
        ]["test"],
    ):
        for flag in ("-q", "--tb=short", "--maxfail=3"):
            assert flag in cmd_tokens


def test_tto_fr_02_compact_gate4_failure_tail_25_and_verify_quiet():
    """[TTO-FR-02] Compact Gate 4 surfaces failing header + <=25 trailing log lines; verify.sh supports --quiet."""
    import shutil
    import subprocess

    script = (
        REPO_ROOT
        / "skills"
        / "quality_check"
        / "resources"
        / "scripts"
        / "verify_polyglot_registry.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        repo, reg_file = _init_tto_quality_repo(
            tmp_path,
            "import sys\nfor i in range(80):\n    print(f'diag_line_{i:02d}', file=sys.stderr)\nsys.exit(1)\n",
        )
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                str(reg_file),
                "--profile",
                "pr",
                "--execute",
                "--compact",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 1
        out = proc.stdout
        assert "GATE_PASS: python-core:lint" in out
        assert "GATE_FAIL: python-core:test" in out
        assert '"provider_id"' not in out
        lines = [ln for ln in out.splitlines() if ln.strip()]
        fail_idx = next(
            i for i, ln in enumerate(lines) if "GATE_FAIL: python-core:test" in ln
        )
        diag_lines = [ln for ln in lines[fail_idx + 1 :] if "diag_line_" in ln]
        assert 1 <= len(diag_lines) <= 25
        assert diag_lines[-1] == "diag_line_79"
        assert "diag_line_00" not in out

        raw_test_log = (
            repo / "build" / "quality" / "python-core" / "test.log"
        ).read_text(encoding="utf-8")
        for i in range(80):
            assert f"diag_line_{i:02d}" in raw_test_log

        # Verify scripts/verify.sh supports --quiet on a minimal kit fixture
        kit = tmp_path / "mini_kit"
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
        for p in (
            "plugin.json",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
        ):
            payload = {
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
            (kit / p).write_text(json.dumps(payload), encoding="utf-8")
        market = {
            "name": "danhdue-agent-tools",
            "plugins": [
                {
                    "name": "d3nexus",
                    "version": "1.0.0",
                    "source": {"source": "local", "path": "./"},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
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
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=kit, check=True)
        subprocess.run(
            ["git", "config", "user.email", "tto@example.com"], cwd=kit, check=True
        )
        subprocess.run(["git", "config", "user.name", "TTO Test"], cwd=kit, check=True)
        subprocess.run(["git", "add", "-A"], cwd=kit, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "Mini kit"], cwd=kit, check=True)

        q_proc = subprocess.run(
            ["bash", "scripts/verify.sh", "--quiet"],
            cwd=kit,
            capture_output=True,
            text=True,
            check=False,
        )
        assert q_proc.returncode == 0
        assert "PASS" in q_proc.stdout
        assert "  ok   plugin.json" not in q_proc.stdout

        (kit / "scripts" / "test_lifecycle_signals.py").write_text(
            "import sys, unittest\n\nclass T(unittest.TestCase):\n    def test_fail(self):\n"
            "        for i in range(60):\n            print(f'verify_fail_line_{i:02d}', file=sys.stderr)\n"
            "        self.fail('boom')\n",
            encoding="utf-8",
        )
        q_fail = subprocess.run(
            ["bash", "scripts/verify.sh", "--quiet", "--full"],
            cwd=kit,
            capture_output=True,
            text=True,
            check=False,
        )
        assert q_fail.returncode == 1
        assert "FAIL [§11] scripts/test_lifecycle_signals.py" in q_fail.stdout
        v_lines = [ln for ln in q_fail.stdout.splitlines() if "verify_fail_line_" in ln]
        assert len(v_lines) <= 25
        assert "verify_fail_line_00" not in q_fail.stdout
