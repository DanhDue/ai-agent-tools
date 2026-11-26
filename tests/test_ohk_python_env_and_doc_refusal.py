"""Tier C integration and unit tests for Task 03: Python uv extras bootstrap, UV_NO_SYNC, and doc refusal."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
BOOTSTRAP_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "dev-implementation"
    / "resources"
    / "scripts"
    / "bootstrap_worktree.sh"
)
CHECK_DOCUMENT_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "doc_quality_check"
    / "resources"
    / "scripts"
    / "check_document.py"
)
VERIFY_POLYGLOT_SCRIPT = (
    REPO_ROOT
    / "skills"
    / "quality_check"
    / "resources"
    / "scripts"
    / "verify_polyglot_registry.py"
)


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "ohk@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "OHK Test"], cwd=repo, check=True)


def _commit_all(repo: Path, message: str = "init") -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return head.stdout.strip()


def _create_recording_fake_uv(bin_dir: Path, record_file: Path) -> Path:
    """Create a fake `uv` executable recording argv and UV_NO_SYNC to JSON."""
    bin_dir.mkdir(parents=True, exist_ok=True)
    fake_uv = bin_dir / "uv"
    fake_uv.write_text(
        f"#!{sys.executable}\n"
        "import json, os, sys\n"
        "from pathlib import Path\n"
        f"record_path = Path({str(record_file)!r})\n"
        "payload = {\n"
        "    'argv': sys.argv[1:],\n"
        "    'uv_no_sync': os.environ.get('UV_NO_SYNC'),\n"
        "    'has_uv_no_sync': 'UV_NO_SYNC' in os.environ,\n"
        "}\n"
        "record_path.write_text(json.dumps(payload), encoding='utf-8')\n"
        "sys.exit(0)\n",
        encoding="utf-8",
    )
    fake_uv.chmod(0o755)
    return fake_uv


def _init_gate4_uv_repo(repo: Path, capability_cmd: list[str]) -> Path:
    _init_git_repo(repo)
    agents_dir = repo / ".agents" / "quality"
    agents_dir.mkdir(parents=True, exist_ok=True)
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
            "lint": capability_cmd,
            "architecture": [sys.executable, "-c", "pass"],
        },
        "profiles": {
            "pr": ["lint"],
            "epic": ["lint", "architecture"],
        },
    }
    reg_file = agents_dir / "check_quality.json"
    reg_file.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    (agents_dir / "python-quality.json").write_text(
        json.dumps(py_manifest, indent=2) + "\n", encoding="utf-8"
    )
    _commit_all(repo, "Init Gate 4 uv repo")
    return reg_file


def test_ohk_hp_03_bootstrap_extras_and_uv_no_sync(tmp_path: Path) -> None:
    """Scenario: [OHK-HP-03] [Tier C - Integration] Bootstrap Python worktree with optional extras and preserve them with UV_NO_SYNC."""
    # 1. Worktree with [project.optional-dependencies] and [dependency-groups].dev
    repo_both = tmp_path / "repo_extras_and_dev"
    _init_git_repo(repo_both)
    (repo_both / "pyproject.toml").write_text(
        "[project]\n"
        'name = "demo-extras"\n'
        'version = "0.1.0"\n\n'
        "[project.optional-dependencies]\n"
        'asr = ["huggingface_hub>=0.20"]\n\n'
        "[dependency-groups]\n"
        'dev = ["pytest>=8.0"]\n',
        encoding="utf-8",
    )
    # Manifest exists without custom "bootstrap" key
    (repo_both / ".agents" / "quality").mkdir(parents=True, exist_ok=True)
    (repo_both / ".agents" / "quality" / "python-quality.json").write_text(
        json.dumps(
            {"schema_version": 1, "capabilities": {}, "profiles": {"pr": []}},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _commit_all(repo_both)

    record_both = tmp_path / "uv_both.json"
    fake_bin = tmp_path / "fake_bin_both"
    _create_recording_fake_uv(fake_bin, record_both)

    env_both = dict(os.environ)
    env_both["PATH"] = f"{fake_bin}{os.pathsep}{env_both.get('PATH', '')}"

    res_both = subprocess.run(
        ["bash", str(BOOTSTRAP_SCRIPT), str(repo_both)],
        cwd=repo_both,
        env=env_both,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_both.returncode == 0, (
        f"stderr={res_both.stderr}\nstdout={res_both.stdout}"
    )
    recorded_both = json.loads(record_both.read_text(encoding="utf-8"))
    assert recorded_both["argv"] == ["sync", "--all-extras", "--group", "dev"]

    # 1b. Worktree with [project.optional-dependencies] only (no [dependency-groups].dev)
    repo_extras_only = tmp_path / "repo_extras_only"
    _init_git_repo(repo_extras_only)
    (repo_extras_only / "pyproject.toml").write_text(
        "[project]\n"
        'name = "demo-extras-only"\n'
        'version = "0.1.0"\n\n'
        "[project.optional-dependencies]\n"
        'ml = ["numpy>=2.0"]\n',
        encoding="utf-8",
    )
    _commit_all(repo_extras_only)

    record_only = tmp_path / "uv_extras_only.json"
    fake_bin_only = tmp_path / "fake_bin_only"
    _create_recording_fake_uv(fake_bin_only, record_only)

    env_only = dict(os.environ)
    env_only["PATH"] = f"{fake_bin_only}{os.pathsep}{env_only.get('PATH', '')}"

    res_only = subprocess.run(
        ["bash", str(BOOTSTRAP_SCRIPT), str(repo_extras_only)],
        cwd=repo_extras_only,
        env=env_only,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_only.returncode == 0, (
        f"stderr={res_only.stderr}\nstdout={res_only.stdout}"
    )
    recorded_only = json.loads(record_only.read_text(encoding="utf-8"))
    assert recorded_only["argv"] == ["sync", "--all-extras"]

    # 2. verify_polyglot_registry.py injects UV_NO_SYNC=1 for `uv run` capability
    gate4_repo = tmp_path / "gate4_uv_run"
    reg_file = _init_gate4_uv_repo(gate4_repo, ["uv", "run", "ruff", "check"])
    record_gate4 = tmp_path / "uv_gate4.json"
    fake_bin_g4 = tmp_path / "fake_bin_g4"
    _create_recording_fake_uv(fake_bin_g4, record_gate4)

    env_g4 = dict(os.environ)
    env_g4.pop("UV_NO_SYNC", None)
    env_g4["PATH"] = f"{fake_bin_g4}{os.pathsep}{env_g4.get('PATH', '')}"

    res_g4 = subprocess.run(
        [
            sys.executable,
            str(VERIFY_POLYGLOT_SCRIPT),
            str(reg_file),
            "--profile",
            "epic",
            "--execute",
            "--compact",
        ],
        cwd=gate4_repo,
        env=env_g4,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_g4.returncode == 0, f"stderr={res_g4.stderr}\nstdout={res_g4.stdout}"
    recorded_g4 = json.loads(record_gate4.read_text(encoding="utf-8"))
    assert recorded_g4["argv"] == ["run", "ruff", "check"]
    assert recorded_g4["has_uv_no_sync"] is True
    assert recorded_g4["uv_no_sync"] == "1"


def test_ohk_ec_03_newline_joined_refusal(tmp_path: Path) -> None:
    """Scenario: [OHK-EC-03] [Tier C - Integration] Document refusal gate catches build-shipping file hidden inside newline-joined zsh argument."""
    _ = tmp_path

    # 1. Single newline-joined argument hiding src/app.py before docs/guide.en.md
    res_offender = subprocess.run(
        [
            sys.executable,
            str(CHECK_DOCUMENT_SCRIPT),
            "--changed-files",
            "src/app.py\ndocs/guide.en.md\n",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_offender.returncode == 1, (
        f"Expected exit 1, got {res_offender.returncode}\n"
        f"stdout={res_offender.stdout}\nstderr={res_offender.stderr}"
    )
    assert "ships in the build: src/app.py" in res_offender.stdout

    # 2. CRLF + blank lines with a build-shipping file
    res_crlf = subprocess.run(
        [
            sys.executable,
            str(CHECK_DOCUMENT_SCRIPT),
            "--changed-files",
            "\r\nsrc/core.rs\r\n\r\ndocs/guide.en.md\r\n",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_crlf.returncode == 1
    assert "ships in the build: src/core.rs" in res_crlf.stdout

    # 3. Single newline-joined string of three documentation files -> accurate count of 3
    res_docs = subprocess.run(
        [
            sys.executable,
            str(CHECK_DOCUMENT_SCRIPT),
            "--changed-files",
            "docs/a.md\ndocs/b.md\nCHANGELOG.md",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_docs.returncode == 0, (
        f"Expected exit 0, got {res_docs.returncode}\n"
        f"stdout={res_docs.stdout}\nstderr={res_docs.stderr}"
    )
    assert "none of 3 changed files ship in the build" in res_docs.stdout

    # 4. Direct module-level check on _flatten_changed and refusal
    doc_scripts = str(CHECK_DOCUMENT_SCRIPT.parent)
    if doc_scripts not in sys.path:
        sys.path.insert(0, doc_scripts)
    check_doc = importlib.import_module("check_document")
    assert check_doc._flatten_changed(
        ["docs/a.md\r\n\n  docs/b.md  \n", "CHANGELOG.md"]
    ) == ["docs/a.md", "docs/b.md", "CHANGELOG.md"]
    assert check_doc.refusal(["src/app.py\ndocs/guide.en.md\n"]) == ["src/app.py"]


def test_ohk_fr_02_uv_no_sync_override_and_malformed_pyproject(
    tmp_path: Path,
) -> None:
    """Scenario: [OHK-FR-02] [Tier C - Integration] Respect explicit caller UV_NO_SYNC override and fallback cleanly on malformed pyproject.toml."""
    # 1. Plain pyproject.toml without [project.optional-dependencies] -> bare `uv sync`
    repo_plain = tmp_path / "repo_plain"
    _init_git_repo(repo_plain)
    (repo_plain / "pyproject.toml").write_text(
        '[project]\nname = "plain-app"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    _commit_all(repo_plain)

    record_plain = tmp_path / "uv_plain.json"
    fake_bin_plain = tmp_path / "fake_bin_plain"
    _create_recording_fake_uv(fake_bin_plain, record_plain)

    env_plain = dict(os.environ)
    env_plain["PATH"] = f"{fake_bin_plain}{os.pathsep}{env_plain.get('PATH', '')}"

    res_plain = subprocess.run(
        ["bash", str(BOOTSTRAP_SCRIPT), str(repo_plain)],
        cwd=repo_plain,
        env=env_plain,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_plain.returncode == 0, (
        f"stderr={res_plain.stderr}\nstdout={res_plain.stdout}"
    )
    recorded_plain = json.loads(record_plain.read_text(encoding="utf-8"))
    assert recorded_plain["argv"] == ["sync"]
    assert "--all-extras" not in recorded_plain["argv"]

    # 2. Empty [project.optional-dependencies] table -> bare `uv sync`
    repo_empty_opt = tmp_path / "repo_empty_opt"
    _init_git_repo(repo_empty_opt)
    (repo_empty_opt / "pyproject.toml").write_text(
        '[project]\nname = "empty-opt"\nversion = "0.1.0"\n\n[project.optional-dependencies]\n',
        encoding="utf-8",
    )
    _commit_all(repo_empty_opt)

    record_empty = tmp_path / "uv_empty_opt.json"
    fake_bin_empty = tmp_path / "fake_bin_empty"
    _create_recording_fake_uv(fake_bin_empty, record_empty)

    env_empty = dict(os.environ)
    env_empty["PATH"] = f"{fake_bin_empty}{os.pathsep}{env_empty.get('PATH', '')}"

    res_empty = subprocess.run(
        ["bash", str(BOOTSTRAP_SCRIPT), str(repo_empty_opt)],
        cwd=repo_empty_opt,
        env=env_empty,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_empty.returncode == 0, (
        f"stderr={res_empty.stderr}\nstdout={res_empty.stdout}"
    )
    assert json.loads(record_empty.read_text(encoding="utf-8"))["argv"] == ["sync"]

    # 3. Malformed pyproject.toml -> graceful fallback to bare `uv sync`
    repo_bad = tmp_path / "repo_malformed"
    _init_git_repo(repo_bad)
    (repo_bad / "pyproject.toml").write_text(
        "[project\nname = broken = [\n",
        encoding="utf-8",
    )
    _commit_all(repo_bad)

    record_bad = tmp_path / "uv_bad.json"
    fake_bin_bad = tmp_path / "fake_bin_bad"
    _create_recording_fake_uv(fake_bin_bad, record_bad)

    env_bad = dict(os.environ)
    env_bad["PATH"] = f"{fake_bin_bad}{os.pathsep}{env_bad.get('PATH', '')}"

    res_bad = subprocess.run(
        ["bash", str(BOOTSTRAP_SCRIPT), str(repo_bad)],
        cwd=repo_bad,
        env=env_bad,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_bad.returncode == 0, f"stderr={res_bad.stderr}\nstdout={res_bad.stdout}"
    assert json.loads(record_bad.read_text(encoding="utf-8"))["argv"] == ["sync"]

    # 4. verify_polyglot_registry.py preserves explicit caller UV_NO_SYNC=0 override
    gate4_repo = tmp_path / "gate4_uv_override"
    reg_file = _init_gate4_uv_repo(gate4_repo, ["uv", "run", "pytest", "-q"])
    record_override = tmp_path / "uv_override.json"
    fake_bin_ovr = tmp_path / "fake_bin_ovr"
    _create_recording_fake_uv(fake_bin_ovr, record_override)

    env_ovr = dict(os.environ)
    env_ovr["UV_NO_SYNC"] = "0"
    env_ovr["PATH"] = f"{fake_bin_ovr}{os.pathsep}{env_ovr.get('PATH', '')}"

    res_ovr = subprocess.run(
        [
            sys.executable,
            str(VERIFY_POLYGLOT_SCRIPT),
            str(reg_file),
            "--profile",
            "epic",
            "--execute",
            "--compact",
        ],
        cwd=gate4_repo,
        env=env_ovr,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_ovr.returncode == 0, f"stderr={res_ovr.stderr}\nstdout={res_ovr.stdout}"
    recorded_ovr = json.loads(record_override.read_text(encoding="utf-8"))
    assert recorded_ovr["has_uv_no_sync"] is True
    assert recorded_ovr["uv_no_sync"] == "0"

    # 5. Direct unit assertions on _build_capability_env helper
    qc_scripts = str(VERIFY_POLYGLOT_SCRIPT.parent)
    if qc_scripts not in sys.path:
        sys.path.insert(0, qc_scripts)
    vpr = importlib.import_module("verify_polyglot_registry")

    built_default = vpr._build_capability_env(
        ["/opt/homebrew/bin/uv", "run", "pytest"],
        base_env={"PATH": "/usr/bin"},
    )
    assert built_default == {"PATH": "/usr/bin", "UV_NO_SYNC": "1"}

    built_override = vpr._build_capability_env(
        ["uv", "run", "mypy", "src"],
        base_env={"PATH": "/usr/bin", "UV_NO_SYNC": "0"},
    )
    assert built_override == {"PATH": "/usr/bin", "UV_NO_SYNC": "0"}

    assert (
        vpr._build_capability_env(["uv", "sync"], base_env={"PATH": "/usr/bin"}) is None
    )
    assert (
        vpr._build_capability_env(
            ["python3", "-m", "pytest"], base_env={"PATH": "/usr/bin"}
        )
        is None
    )


class Test_Ohk_Python_Env_And_Doc_Refusal_Integration:
    """[Tier C - Integration] Integration runner provenance for OHK-HP-03, OHK-EC-03, and OHK-FR-02."""

    def test_ohk_hp_03_integration(self, tmp_path: Path) -> None:
        """[OHK-HP-03] [Tier C - Integration] Bootstrap Python worktree with optional extras and UV_NO_SYNC."""
        test_ohk_hp_03_bootstrap_extras_and_uv_no_sync(tmp_path)

    def test_ohk_ec_03_integration(self, tmp_path: Path) -> None:
        """[OHK-EC-03] [Tier C - Integration] Document refusal gate splits newline-joined arguments."""
        test_ohk_ec_03_newline_joined_refusal(tmp_path)

    def test_ohk_fr_02_integration(self, tmp_path: Path) -> None:
        """[OHK-FR-02] [Tier C - Integration] Respect UV_NO_SYNC override and fallback on malformed pyproject.toml."""
        test_ohk_fr_02_uv_no_sync_override_and_malformed_pyproject(tmp_path)
