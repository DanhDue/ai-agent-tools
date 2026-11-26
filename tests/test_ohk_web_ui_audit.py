"""Tier C integration and unit tests for Task 04: Web UI audit subdirectory git show, dirty diff merge, and folded hotfix."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SCRIPTS_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"
AUDIT_SCRIPT = WEB_SCRIPTS_DIR / "audit_ui_state_and_styles.py"

if str(WEB_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_SCRIPTS_DIR))

from unittest import mock

from audit_ui_state_and_styles import (  # noqa: E402
    _collect_base_defined_classes,
    _get_base_file_content,
    _get_base_files_contents,
    _is_excluded,
    get_git_diff_files,
    run_all_ui_reviews,
)


def _init_git_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "ohk@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "OHK Test"], cwd=repo, check=True)


def _commit_all(repo: Path, message: str = "init") -> None:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)


def _run_audit_cli(
    cwd: Path,
    *,
    project_root: str | None = None,
    base_ref: str = "main",
) -> tuple[int, dict[str, Any]]:
    cmd = [sys.executable, str(AUDIT_SCRIPT), "--base-ref", base_ref, "--json"]
    if project_root is not None:
        cmd.extend(["--project-root", project_root])
    proc = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.stdout.strip(), (
        f"Expected JSON stdout from audit script, exit={proc.returncode}, stderr={proc.stderr!r}"
    )
    return proc.returncode, json.loads(proc.stdout)


def test_ohk_hp_04_subdir_base_and_uncommitted_merge(tmp_path: Path) -> None:
    """Scenario: [OHK-HP-04] [Tier C - Integration] Subdirectory UI audit resolves base templates and merges uncommitted template edits."""
    repo = tmp_path / "subdir_web_repo"
    _init_git_repo(repo)

    preview = repo / "src" / "app" / "preview"
    static_dir = preview / "static"
    well_known_dir = preview / ".well-known"
    static_dir.mkdir(parents=True, exist_ok=True)
    well_known_dir.mkdir(parents=True, exist_ok=True)

    (repo / "outside.html").write_text("<div>outside</div>\n", encoding="utf-8")
    (static_dir / "style.css").write_text(
        ".search-box { padding: 8px; }\n.portal-card { border: 1px solid #ccc; }\n",
        encoding="utf-8",
    )
    (static_dir / "search.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css?v=1"></head>'
        '<body><div class="search-box">Search</div></body></html>\n',
        encoding="utf-8",
    )
    (well_known_dir / "portal.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="../static/style.css?v=1"></head>'
        '<body><div class="portal-card">Portal</div></body></html>\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Base main preview templates")

    # Feature branch commits a CSS change only
    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    (static_dir / "style.css").write_text(
        ".search-box { padding: 12px; }\n.portal-card { border: 1px solid #333; }\n",
        encoding="utf-8",
    )
    _commit_all(repo, "Update preview CSS")

    # Working tree holds uncommitted edits bumping ?v=1 -> ?v=2 on both templates
    (static_dir / "search.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css?v=2"></head>'
        '<body><div class="search-box">Search</div></body></html>\n',
        encoding="utf-8",
    )
    (well_known_dir / "portal.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="../static/style.css?v=2"></head>'
        '<body><div class="portal-card">Portal</div></body></html>\n',
        encoding="utf-8",
    )

    # 1. Verify _get_base_file_content resolves normal & dot-prefixed paths and rejects traversal
    base_search = _get_base_file_content(preview, "main", "static/search.html")
    assert base_search is not None
    assert "style.css?v=1" in base_search

    base_search_dot = _get_base_file_content(preview, "main", "./static/search.html")
    assert base_search_dot == base_search

    base_portal = _get_base_file_content(preview, "main", ".well-known/portal.html")
    assert base_portal is not None
    assert "style.css?v=1" in base_portal

    base_portal_dot = _get_base_file_content(
        preview, "main", "./.well-known/portal.html"
    )
    assert base_portal_dot == base_portal

    assert _get_base_file_content(preview, "main", "../outside.html") is None
    assert _get_base_file_content(preview, "main", "../../../outside.html") is None
    assert _get_base_file_content(preview, "main", "/outside.html") is None
    assert _get_base_file_content(preview, "main", "") is None
    assert _get_base_file_content(preview, "main", "./") is None

    # 2. Verify get_git_diff_files unions committed CSS + uncommitted templates
    diff_files = get_git_diff_files(preview, "main")
    assert "static/style.css" in diff_files
    assert "static/search.html" in diff_files
    assert ".well-known/portal.html" in diff_files
    assert len(diff_files) == len(set(diff_files))

    # 3. CLI JSON report returns PASS with 0 cache_bust findings
    rc_pass, payload_pass = _run_audit_cli(
        repo, project_root="src/app/preview", base_ref="main"
    )
    assert rc_pass == 0, f"Expected PASS, got {payload_pass}"
    assert payload_pass["status"] == "PASS"
    cache_bust_pass = [
        f for f in payload_pass["findings"] if f["category"] == "cache_bust"
    ]
    assert cache_bust_pass == []

    # 4. Modify .well-known/portal.html without bumping ?v=1 -> FAIL with cache_bust on .well-known/portal.html
    (well_known_dir / "portal.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="../static/style.css?v=1"></head>'
        '<body><div class="portal-card">Portal updated text</div></body></html>\n',
        encoding="utf-8",
    )
    rc_fail, payload_fail = _run_audit_cli(
        repo, project_root="src/app/preview", base_ref="main"
    )
    assert rc_fail == 1, f"Expected FAIL, got {payload_fail}"
    assert payload_fail["status"] == "FAIL"
    cache_bust_fail = [
        f
        for f in payload_fail["findings"]
        if f["category"] == "cache_bust" and f["file"] == ".well-known/portal.html"
    ]
    assert len(cache_bust_fail) == 1, f"Expected cache_bust finding, got {payload_fail}"


def test_ohk_ec_04_excludes_base_orphans_and_css_removal_on_layout_children(
    tmp_path: Path,
) -> None:
    """Scenario: [OHK-EC-04] [Tier C - Integration] UI auditor excludes build directories, ignores pre-existing base-ref orphans, and catches CSS-only class removals including layout-inherited templates."""
    repo = tmp_path / "layout_inherit_repo"
    _init_git_repo(repo)

    # Compiled HTML with orphaned classes inside all 6 newly excluded directories
    excluded_dirs = ("dist", ".astro", ".devtool", "docs", "target", "tests")
    for dirname in excluded_dirs:
        d = repo / dirname
        d.mkdir(parents=True, exist_ok=True)
        (d / "compiled.html").write_text(
            f'<div class="compiled-{dirname.strip(".")}-orphan">Compiled</div>\n',
            encoding="utf-8",
        )

    src_dir = repo / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "style.css").write_text(
        ".layout-shell { display: block; }\n.active-card { padding: 12px; }\n",
        encoding="utf-8",
    )
    (src_dir / "layout.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="style.css?v=1"></head>'
        '<body class="layout-shell">{% block content %}{% endblock %}</body></html>\n',
        encoding="utf-8",
    )
    (src_dir / "page.html").write_text(
        '{% extends "layout.html" %}\n'
        '<section class="legacy-unmapped active-card">Original text</section>\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Base main with layout, child page, and excluded build dirs")

    # Part 1: HEAD edits only text on src/page.html without touching src/style.css
    subprocess.run(
        ["git", "checkout", "-q", "-b", "text-only-edit"], cwd=repo, check=True
    )
    (src_dir / "page.html").write_text(
        '{% extends "layout.html" %}\n'
        '<section class="legacy-unmapped active-card">Updated copy</section>\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Edit text only on src/page.html")

    rc_pass, payload_pass = _run_audit_cli(repo, base_ref="main")
    assert rc_pass == 0, f"Expected PASS, got {payload_pass}"
    assert payload_pass["status"] == "PASS"
    assert payload_pass["findings"] == []

    # Part 2: HEAD modifies only src/style.css to delete .active-card, leaving layout.html & page.html untouched
    subprocess.run(
        ["git", "checkout", "-q", "-b", "css-only-removal", "main"],
        cwd=repo,
        check=True,
    )
    (src_dir / "style.css").write_text(
        ".layout-shell { display: block; }\n",
        encoding="utf-8",
    )
    _commit_all(repo, "Delete .active-card from src/style.css")

    rc_css_fail, payload_css_fail = _run_audit_cli(repo, base_ref="main")
    assert rc_css_fail == 1, f"Expected FAIL, got {payload_css_fail}"
    assert payload_css_fail["status"] == "FAIL"

    # Zero findings from excluded directories
    for finding in payload_css_fail["findings"]:
        finding_file = str(finding.get("file", ""))
        for dirname in excluded_dirs:
            assert not finding_file.startswith(f"{dirname}/"), (
                f"Excluded directory '{dirname}/' leaked finding: {finding}"
            )

    orphans = [
        f for f in payload_css_fail["findings"] if f["category"] == "orphaned_class"
    ]
    assert any(
        f.get("file") == "src/page.html" and f.get("class") == "active-card"
        for f in orphans
    ), f"Expected orphaned_class for active-card on src/page.html, got {orphans}"
    assert not any(f.get("class") == "legacy-unmapped" for f in orphans), (
        f"Pre-existing legacy-unmapped should stay suppressed, got {orphans}"
    )

    # Part 3: Adding a brand-new undefined class on src/page.html also returns FAIL
    subprocess.run(
        ["git", "checkout", "-q", "-b", "new-orphan-edit", "main"],
        cwd=repo,
        check=True,
    )
    (src_dir / "page.html").write_text(
        '{% extends "layout.html" %}\n'
        '<section class="legacy-unmapped active-card new-orphan-cls">Text</section>\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Add new-orphan-cls on src/page.html")

    rc_new_fail, payload_new_fail = _run_audit_cli(repo, base_ref="main")
    assert rc_new_fail == 1, f"Expected FAIL, got {payload_new_fail}"
    assert payload_new_fail["status"] == "FAIL"
    new_orphans = [
        f for f in payload_new_fail["findings"] if f["category"] == "orphaned_class"
    ]
    assert any(
        f.get("file") == "src/page.html" and f.get("class") == "new-orphan-cls"
        for f in new_orphans
    ), f"Expected orphaned_class for new-orphan-cls, got {new_orphans}"
    assert not any(f.get("class") == "legacy-unmapped" for f in new_orphans)


def test_ohk_ar_01_non_ui_and_excluded_html_return_not_applicable(
    tmp_path: Path,
) -> None:
    """Scenario: [OHK-AR-01] [Tier C - Integration] Non-UI changes return NOT_APPLICABLE when only excluded paths contain HTML or CSS."""
    repo = tmp_path / "non_ui_repo"
    _init_git_repo(repo)

    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "dist").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "backend.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "src" / "style.css").write_text(".ok { color: black; }\n", encoding="utf-8")
    (repo / "src" / "page.html").write_text(
        '<div class="ok">Base</div>\n', encoding="utf-8"
    )
    (repo / "dist" / "index.html").write_text(
        '<div class="dist-built-v1">Built</div>\n', encoding="utf-8"
    )
    _commit_all(repo, "Base main")

    subprocess.run(
        ["git", "checkout", "-q", "-b", "backend-only"], cwd=repo, check=True
    )
    (repo / "src" / "backend.py").write_text("VALUE = 2\n", encoding="utf-8")
    (repo / "dist" / "index.html").write_text(
        '<div class="dist-built-v2">Rebuilt</div>\n', encoding="utf-8"
    )
    _commit_all(repo, "Modify backend.py and compiled dist/index.html only")

    rc, payload = _run_audit_cli(repo, base_ref="main")
    assert rc == 0, f"Expected exit 0 NOT_APPLICABLE, got {payload}"
    assert payload["status"] == "NOT_APPLICABLE"
    assert payload["not_applicable_reason"]["code"] == "scope_unmodified"
    assert payload["ui_modified_files_count"] == 0
    assert payload["modified_files_count"] == 2
    assert payload["total_findings"] == 0


def test_get_git_diff_files_merges_staged_unstaged_untracked_and_ignores_gitignored(
    tmp_path: Path,
) -> None:
    """Verify get_git_diff_files unions committed, unstaged, staged, and non-ignored untracked files inside a subdir."""
    repo = tmp_path / "dirty_union_repo"
    _init_git_repo(repo)

    preview = repo / "web" / "preview"
    preview.mkdir(parents=True, exist_ok=True)
    (repo / ".gitignore").write_text("*.ignored.html\n", encoding="utf-8")
    (preview / "committed.css").write_text(".a { color: red; }\n", encoding="utf-8")
    (preview / "unstaged.html").write_text('<div class="a">1</div>\n', encoding="utf-8")
    (preview / "staged.html").write_text('<div class="a">1</div>\n', encoding="utf-8")
    _commit_all(repo, "Base main")

    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=repo, check=True)
    (preview / "committed.css").write_text(".a { color: blue; }\n", encoding="utf-8")
    _commit_all(repo, "Committed CSS update")

    # Unstaged tracked edit
    (preview / "unstaged.html").write_text('<div class="a">2</div>\n', encoding="utf-8")
    # Staged tracked edit
    (preview / "staged.html").write_text('<div class="a">2</div>\n', encoding="utf-8")
    subprocess.run(["git", "add", "web/preview/staged.html"], cwd=repo, check=True)
    # Untracked non-ignored file + ignored file
    (preview / "untracked.html").write_text(
        '<div class="a">new</div>\n', encoding="utf-8"
    )
    (preview / "skip.ignored.html").write_text(
        '<div class="a">ignored</div>\n', encoding="utf-8"
    )
    # Unrelated file outside preview subdir
    (repo / "outside_untracked.html").write_text("<div>out</div>\n", encoding="utf-8")

    diff_files = get_git_diff_files(preview, "main")
    assert diff_files == [
        "committed.css",
        "staged.html",
        "unstaged.html",
        "untracked.html",
    ]


def test_get_git_diff_files_falls_back_to_2dot_diff_on_unrelated_history(
    tmp_path: Path,
) -> None:
    """When 3-dot base_ref...HEAD fails (no merge base), get_git_diff_files falls back to 2-dot diff."""
    repo = tmp_path / "orphan_repo"
    _init_git_repo(repo)
    (repo / "base.css").write_text(".a { color: red; }\n", encoding="utf-8")
    _commit_all(repo, "Base main")

    subprocess.run(["git", "checkout", "--orphan", "unrelated"], cwd=repo, check=True)
    subprocess.run(["git", "rm", "-rf", "-q", "."], cwd=repo, check=True)
    (repo / "new.css").write_text(".b { color: blue; }\n", encoding="utf-8")
    _commit_all(repo, "Orphan commit")

    diff_files = get_git_diff_files(repo, "main")
    assert "base.css" in diff_files
    assert "new.css" in diff_files


def test_css_deletion_and_jinja2_template_and_component_style_base_resolution(
    tmp_path: Path,
) -> None:
    """Deleting a stylesheet or component style class flags unchanged .jinja2 templates while suppressing base orphans."""
    repo = tmp_path / "jinja2_css_delete_repo"
    _init_git_repo(repo)

    (repo / "src").mkdir(parents=True, exist_ok=True)
    (repo / "src" / "keep.css").write_text(".keep { color: #111; }\n", encoding="utf-8")
    (repo / "src" / "removed.css").write_text(
        ".removed-btn { padding: 4px; }\n", encoding="utf-8"
    )
    (repo / "src" / "view.jinja2").write_text(
        '<button class="keep removed-btn old-orphan">Go</button>\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Base main with removed.css and view.jinja2")

    subprocess.run(["git", "checkout", "-q", "-b", "del-css"], cwd=repo, check=True)
    (repo / "src" / "removed.css").unlink()
    _commit_all(repo, "Delete src/removed.css")

    res = run_all_ui_reviews(repo_root=repo, base_ref="main")
    assert res["status"] == "FAIL", f"Expected FAIL, got {res}"
    orphans = [f for f in res["findings"] if f["category"] == "orphaned_class"]
    assert any(
        f.get("file") == "src/view.jinja2" and f.get("class") == "removed-btn"
        for f in orphans
    ), f"Expected removed-btn orphaned_class on src/view.jinja2, got {orphans}"
    assert not any(f.get("class") == "old-orphan" for f in orphans), (
        f"Expected pre-existing old-orphan suppressed, got {orphans}"
    )


def test_preexisting_base_filtering_for_unstyled_duplicate_clipping_and_state_machine(
    tmp_path: Path,
) -> None:
    """Verify pre-existing Invariant 2/3/4 findings on base_ref are suppressed while newly introduced ones fail."""
    repo = tmp_path / "base_filter_repo"
    _init_git_repo(repo)

    (repo / "style.css").write_text(".card { color: #111; }\n", encoding="utf-8")
    (repo / "panel.html").write_text(
        '<div class="card" style="background: transparent; border: 0; padding: 0">Base card</div>\n'
        '<div style="display: flex; justify-content: flex-end; text-overflow: ellipsis">Base clip</div>\n'
        "<h2>RepeatWord RepeatWord</h2>\n",
        encoding="utf-8",
    )
    (repo / "stream.js").write_text(
        'const label = "Running: FAILED";\n'
        'if (status === "FAILED") { progress = 100; }\n'
        'const sse = new EventSource("/events");\n',
        encoding="utf-8",
    )
    _commit_all(repo, "Base main with pre-existing violations")

    # Benign edits to both files: line shifts, no new violations -> PASS
    subprocess.run(["git", "checkout", "-q", "-b", "benign"], cwd=repo, check=True)
    (repo / "panel.html").write_text(
        "<!-- shifted line -->\n"
        '<div class="card" style="background: transparent; border: 0; padding: 0">Base card</div>\n'
        '<div style="display: flex; justify-content: flex-end; text-overflow: ellipsis">Base clip</div>\n'
        "<h2>RepeatWord RepeatWord</h2>\n",
        encoding="utf-8",
    )
    (repo / "stream.js").write_text(
        "// benign comment\n"
        'const label = "Running: FAILED";\n'
        'if (status === "FAILED") { progress = 100; }\n'
        'const sse = new EventSource("/events");\n',
        encoding="utf-8",
    )
    res_pass = run_all_ui_reviews(repo_root=repo, base_ref="main")
    assert res_pass["status"] == "PASS", f"Expected PASS, got {res_pass}"

    # Introducing a second unstyled card + a new duplicate phrase + a new contradiction -> FAIL
    (repo / "panel.html").write_text(
        '<div class="card" style="background: transparent; border: 0; padding: 0">Base card</div>\n'
        '<div class="card" style="background: transparent; border: 0; padding: 0">Second card</div>\n'
        '<div style="display: flex; justify-content: flex-end; text-overflow: ellipsis">Base clip</div>\n'
        "<h2>RepeatWord RepeatWord</h2>\n"
        "<h3>FreshDup FreshDup</h3>\n",
        encoding="utf-8",
    )
    (repo / "stream.js").write_text(
        'const label = "Running: FAILED";\n'
        'const second = "Processing: COMPLETED";\n'
        'if (status === "FAILED") { progress = 100; }\n'
        'const sse = new EventSource("/events");\n',
        encoding="utf-8",
    )
    res_fail = run_all_ui_reviews(repo_root=repo, base_ref="main")
    assert res_fail["status"] == "FAIL", f"Expected FAIL, got {res_fail}"
    categories = {f["category"] for f in res_fail["findings"]}
    assert "unstyled_default" in categories
    assert "duplicate_text" in categories
    assert "state_machine_contradiction" in categories
    assert "text_clipping" not in categories
    assert "sse_leak" not in categories
    assert "invalid_progress_state" not in categories


def test_is_excluded_covers_all_required_directories(tmp_path: Path) -> None:
    """Verify _is_excluded matches all 10 excluded directories and preserves .well-known."""
    for name in (
        "node_modules",
        "build",
        ".worktrees",
        ".git",
        "dist",
        ".astro",
        ".devtool",
        "docs",
        "target",
        "tests",
    ):
        assert _is_excluded(tmp_path / name / "file.html", tmp_path) is True
    assert _is_excluded(tmp_path / ".well-known" / "portal.html", tmp_path) is False
    assert _is_excluded(tmp_path / "src" / "page.html", tmp_path) is False


def test_collect_base_defined_classes_batches_git_cat_file_in_subdir(
    tmp_path: Path,
) -> None:
    """_collect_base_defined_classes reads multiple base-ref files in a single git cat-file --batch call."""
    import audit_ui_state_and_styles

    repo = tmp_path / "batched_subdir_repo"
    _init_git_repo(repo)

    preview = repo / "src" / "app" / "preview"
    static_dir = preview / "static"
    well_known_dir = preview / ".well-known"
    dist_dir = preview / "dist"
    static_dir.mkdir(parents=True, exist_ok=True)
    well_known_dir.mkdir(parents=True, exist_ok=True)
    dist_dir.mkdir(parents=True, exist_ok=True)

    (repo / "outside.css").write_text(
        ".outside-root-cls { color: red; }\n", encoding="utf-8"
    )
    (static_dir / "main.css").write_text(
        "/* Tiến độ UI */\n.base-btn { padding: 8px; }\n",
        encoding="utf-8",
    )
    (static_dir / "extra.scss").write_text(
        ".extra-badge { border-radius: 4px; }\n",
        encoding="utf-8",
    )
    (static_dir / "Card.astro").write_text(
        "<div class='astro-panel'>Card</div>\n<style>.astro-panel { display: block; }</style>\n",
        encoding="utf-8",
    )
    (well_known_dir / "portal.html").write_text(
        "<style>.portal-shell { margin: 0; }</style>\n<div class='portal-shell'>OK</div>\n",
        encoding="utf-8",
    )
    (dist_dir / "compiled.css").write_text(
        ".excluded-dist-cls { display: none; }\n",
        encoding="utf-8",
    )
    _commit_all(repo, "Base main with multiple stylesheets and components")

    # Verify _get_base_files_contents handles valid, dot-prefixed, missing, and traversal paths in one batch
    batched = _get_base_files_contents(
        preview,
        "main",
        [
            "static/main.css",
            ".well-known/portal.html",
            "missing.css",
            "../outside.css",
            "../../outside.css",
        ],
    )
    assert set(batched.keys()) == {"static/main.css", ".well-known/portal.html"}
    assert "Tiến độ UI" in batched["static/main.css"]
    assert ".portal-shell" in batched[".well-known/portal.html"]

    calls: list[list[str]] = []
    real_run = audit_ui_state_and_styles.subprocess.run

    def _spy_run(cmd: list[str], *args: Any, **kwargs: Any) -> Any:
        calls.append(list(cmd))
        return real_run(cmd, *args, **kwargs)

    with mock.patch.object(
        audit_ui_state_and_styles.subprocess, "run", side_effect=_spy_run
    ):
        defined = _collect_base_defined_classes(preview, "main")

    assert {"base-btn", "extra-badge", "astro-panel", "portal-shell"} <= defined
    assert "excluded-dist-cls" not in defined
    assert "outside-root-cls" not in defined

    cat_file_calls = [c for c in calls if c[:3] == ["git", "cat-file", "--batch"]]
    git_show_calls = [c for c in calls if c[:2] == ["git", "show"]]
    assert len(cat_file_calls) == 1, (
        f"Expected 1 git cat-file --batch call, got {calls}"
    )
    assert git_show_calls == [], f"Expected 0 git show calls, got {git_show_calls}"


class Test_Ohk_Web_Ui_Audit_Integration:
    """[Tier C - Integration] Integration runner provenance for OHK-HP-04, OHK-EC-04, and OHK-AR-01."""

    def test_ohk_hp_04_integration(self, tmp_path: Path) -> None:
        """[OHK-HP-04] [Tier C - Integration] Subdirectory UI audit resolves base templates and merges uncommitted template edits."""
        test_ohk_hp_04_subdir_base_and_uncommitted_merge(tmp_path)

    def test_ohk_ec_04_integration(self, tmp_path: Path) -> None:
        """[OHK-EC-04] [Tier C - Integration] UI auditor excludes build dirs, ignores base orphans, and catches CSS class removals."""
        test_ohk_ec_04_excludes_base_orphans_and_css_removal_on_layout_children(
            tmp_path
        )

    def test_ohk_ar_01_integration(self, tmp_path: Path) -> None:
        """[OHK-AR-01] [Tier C - Integration] Non-UI changes return NOT_APPLICABLE when only excluded paths contain HTML or CSS."""
        test_ohk_ar_01_non_ui_and_excluded_html_return_not_applicable(tmp_path)
