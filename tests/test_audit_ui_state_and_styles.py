"""Tests for UI state, styling invariants, cache-busting, and state machine consistency audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_SCRIPTS_DIR = REPO_ROOT / "skills" / "web-quality-check" / "resources" / "scripts"

if str(WEB_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(WEB_SCRIPTS_DIR))

from audit_ui_state_and_styles import (  # noqa: E402
    audit_cache_busting,
    audit_orphaned_classes_and_styles,
    audit_text_truncation_and_overflow,
    audit_ui_state_machine_consistency,
    main,
    run_all_ui_reviews,
)


def test_cache_bust_verification(tmp_path: Path) -> None:
    """Invariant 1: Verify cache-bust ?v= query parameter updates when static assets change."""
    # Setup template referencing static asset
    tpl = tmp_path / "index.html"
    tpl.write_text(
        """<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="/static/style.css?v=1.0.0">
    <script src="/static/app.js?v=1.0.0"></script>
    <script src="/static/legacy.js"></script>
</head>
<body></body>
</html>""",
        encoding="utf-8",
    )

    # 1. When static file was modified but template was not touched (or missing ?v=)
    findings = audit_cache_busting(
        tmp_path, modified_files=["static/app.js", "static/legacy.js"]
    )
    assert len(findings) == 2
    categories = [f["category"] for f in findings]
    assert all(c == "cache_bust" for c in categories)

    # 2. When template was also updated in modified_files
    findings_ok = audit_cache_busting(
        tmp_path, modified_files=["static/app.js", "index.html"]
    )
    # static/app.js is satisfied because index.html is in modified_files
    # static/legacy.js is not in modified_files, so only 0 findings for app.js
    assert not any(f.get("asset") == "static/app.js" for f in findings_ok)


def test_orphaned_classes_and_unstyled_styles(tmp_path: Path) -> None:
    """Invariant 2: Verify referenced CSS classes exist and cards/drawers/badges have styled definitions."""
    css_dir = tmp_path / "styles"
    css_dir.mkdir(parents=True)
    css_file = css_dir / "main.css"
    css_file.write_text(
        """.btn-primary { color: blue; }
.card-header { padding: 8px; }
.custom-badge { background: green; }
""",
        encoding="utf-8",
    )

    # Template with valid class and an orphaned class
    tpl = tmp_path / "view.html"
    tpl.write_text(
        """<div class="card-header btn-primary flex">
    <span class="custom-badge">OK</span>
    <div class="missing-nonexistent-class">Test</div>
</div>
<!-- Unstyled default card anti-pattern -->
<div class="card" style="background: transparent; border: 0; padding: 0">
    <span>Ghost Card</span>
</div>
""",
        encoding="utf-8",
    )

    findings = audit_orphaned_classes_and_styles(tmp_path)
    assert len(findings) >= 2

    # Check unstyled default finding
    unstyled = [f for f in findings if f["category"] == "unstyled_default"]
    assert len(unstyled) == 1
    assert "card" in unstyled[0]["message"]

    # Check orphaned class finding
    orphaned = [f for f in findings if f["category"] == "orphaned_class"]
    assert any(f.get("class") == "missing-nonexistent-class" for f in orphaned)


def test_astro_component_scoped_styles_not_orphaned(tmp_path: Path) -> None:
    """Invariant 2: Scoped <style> classes in Astro/HTML components must not be flagged as orphaned."""
    # Global stylesheet with unrelated class
    css_file = tmp_path / "global.css"
    css_file.write_text(".global-header { margin: 0; }", encoding="utf-8")

    # Astro component with scoped style definition
    astro_file = tmp_path / "Card.astro"
    astro_file.write_text(
        """---
// Frontmatter
---
<div class="scoped-card-box">
    <p>Card Content</p>
</div>

<style>
.scoped-card-box {
    border-radius: 8px;
    background: #fff;
}
</style>
""",
        encoding="utf-8",
    )

    findings = audit_orphaned_classes_and_styles(tmp_path)
    orphaned = [f for f in findings if f["category"] == "orphaned_class"]
    assert len(orphaned) == 0, f"Expected 0 orphaned classes, got: {orphaned}"


def test_text_truncation_and_duplicate_phrases(tmp_path: Path) -> None:
    """Invariant 3: Guard against text clipping at start of flex rows and consecutive duplicate text."""
    bad_file = tmp_path / "page.html"
    bad_file.write_text(
        """<div style="display: flex; justify-content: flex-end; text-overflow: ellipsis">
    <h2>Tiến độ Tiến độ</h2>
</div>""",
        encoding="utf-8",
    )

    findings = audit_text_truncation_and_overflow(tmp_path)
    assert len(findings) >= 2

    clipping = [f for f in findings if f["category"] == "text_clipping"]
    assert len(clipping) == 1

    duplicate = [f for f in findings if f["category"] == "duplicate_text"]
    assert len(duplicate) == 1
    assert "Tiến độ" in duplicate[0]["duplicate_phrase"]


def test_ui_state_machine_consistency(tmp_path: Path) -> None:
    """Invariant 4: Validate state machine consistency, progress limits, and EventSource teardown."""
    # 1. Contradictory terminal state string
    bad_ui = tmp_path / "status.js"
    bad_ui.write_text(
        """const label = "Đang chạy: FAILED";
if (status === 'FAILED') {
    progress = 100;
}
const sse = new EventSource("/stream");
// missing sse.close()
""",
        encoding="utf-8",
    )

    findings = audit_ui_state_machine_consistency(tmp_path)
    assert len(findings) == 3

    categories = {f["category"] for f in findings}
    assert "state_machine_contradiction" in categories
    assert "sse_leak" in categories
    assert "invalid_progress_state" in categories


def test_run_all_ui_reviews_clean(tmp_path: Path) -> None:
    """Verify clean project passes all UI review invariants."""
    clean_css = tmp_path / "style.css"
    clean_css.write_text(
        ".container { width: 100%; } .heading { font-size: 16px; }", encoding="utf-8"
    )

    clean_html = tmp_path / "index.html"
    clean_html.write_text(
        """<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="style.css?v=2.0.0">
</head>
<body>
    <div class="container">
        <h1 class="heading">Tiến độ công việc</h1>
    </div>
</body>
</html>""",
        encoding="utf-8",
    )

    res = run_all_ui_reviews(repo_root=tmp_path, base_ref="main")
    assert res["status"] == "PASS"
    assert res["total_findings"] == 0


def test_cli_execution(tmp_path: Path) -> None:
    """Verify CLI entrypoint."""
    code = main(["--project-root", str(tmp_path), "--json"])
    assert code == 0


def test_progress_progression_not_flagged_as_duplicate(tmp_path: Path) -> None:
    """Verify substring overlap like 'Progress Progression' is not false-positived."""
    page = tmp_path / "valid.html"
    page.write_text("<h2>Progress Progression</h2>", encoding="utf-8")
    findings = audit_text_truncation_and_overflow(tmp_path)
    dups = [f for f in findings if f["category"] == "duplicate_text"]
    assert len(dups) == 0


def test_worktree_path_auditing(tmp_path: Path) -> None:
    """Verify that repositories located inside a parent path named .worktrees are not excluded."""
    nested_worktree = tmp_path / ".worktrees" / "feature-branch"
    nested_worktree.mkdir(parents=True)
    (nested_worktree / "style.css").write_text(
        ".existing-class { color: red; }", encoding="utf-8"
    )
    bad_page = nested_worktree / "view.html"
    bad_page.write_text(
        "<div class='missing-orphan-class'>Text</div>", encoding="utf-8"
    )

    findings = audit_orphaned_classes_and_styles(nested_worktree)
    orphans = [f for f in findings if f["category"] == "orphaned_class"]
    assert len(orphans) == 1
    assert orphans[0]["class"] == "missing-orphan-class"


def test_url_containing_sse_source_and_comment_handling(tmp_path: Path) -> None:
    """Verify that EventSource URLs with https:// and inline comments do not strip close() logic."""
    app_js = tmp_path / "app.js"
    app_js.write_text(
        """
        // Global comment at start
        const source = new EventSource("https://example.test/events"); // connection opened
        source.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === "COMPLETED" || data.status === "FAILED") {
                source.close(); // clean terminal closure
            }
        };
        """,
        encoding="utf-8",
    )
    findings = audit_ui_state_machine_consistency(tmp_path)
    assert len(findings) == 0


def test_scope_unmodified_returns_not_applicable_when_only_backend_files_changed(
    tmp_path: Path,
) -> None:
    """When git diff against base_ref only modifies backend (.py) files, run_all_ui_reviews short-circuits with NOT_APPLICABLE (scope_unmodified)."""
    import subprocess

    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    (tmp_path / "backend.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True)

    subprocess.run(["git", "checkout", "-q", "-b", "feature"], cwd=tmp_path, check=True)
    (tmp_path / "backend.py").write_text("x = 2\n", encoding="utf-8")
    subprocess.run(
        ["git", "commit", "-q", "-am", "backend change"], cwd=tmp_path, check=True
    )

    res = run_all_ui_reviews(repo_root=tmp_path, base_ref="main")
    assert res["status"] == "NOT_APPLICABLE"
    assert res["not_applicable_reason"]["code"] == "scope_unmodified"
    assert res["total_findings"] == 0, f"Expected 0 findings, got: {res['findings']}"


@pytest.mark.parametrize(
    ("filename", "css_body"),
    [
        (
            "static/style.css",
            ".icon { background-size: 14px 14px; }\n"
            ".panel { border-radius: 10px 10px 0 0; }\n"
            ".arrow { border-color: #fff transparent transparent; }\n"
            ".grid { grid-template-columns: 1fr 1fr; }\n",
        ),
        (
            "styles/theme.scss",
            "$pad: 12px;\n.box { margin: 12px 12px; padding: 8px 8px 4px 4px; }\n",
        ),
        (
            "styles/UPPER.CSS",
            ".btn { border-radius: 10px 10px 0 0; background-size: 16px 16px; }\n",
        ),
    ],
)
def test_stylesheet_shorthands_skip_duplicate_text_when_target_files_passed(
    tmp_path: Path, filename: str, css_body: str
) -> None:
    """#17: Multi-axis CSS/SCSS shorthands must not trigger duplicate_text false positives."""
    css_file = tmp_path / filename
    css_file.parent.mkdir(parents=True, exist_ok=True)
    css_file.write_text(css_body, encoding="utf-8")

    findings = audit_text_truncation_and_overflow(tmp_path, target_files=[filename])
    dup_findings = [f for f in findings if f["category"] == "duplicate_text"]
    assert dup_findings == [], f"Unexpected CSS duplicate_text findings: {dup_findings}"


def test_stylesheet_still_checks_left_clip_while_html_checks_duplicate_text(
    tmp_path: Path,
) -> None:
    """#17: Stylesheets retain LEFT_CLIP_PATTERN; templates retain DUPLICATE_PHRASE_PATTERN."""
    css_file = tmp_path / "static" / "layout.css"
    css_file.parent.mkdir(parents=True, exist_ok=True)
    css_file.write_text(
        ".row { display: flex; justify-content: flex-end; text-overflow: ellipsis; "
        "border-radius: 10px 10px 0 0; }\n",
        encoding="utf-8",
    )
    html_file = tmp_path / "templates" / "view.html"
    html_file.parent.mkdir(parents=True, exist_ok=True)
    html_file.write_text("<h2>Status Status</h2>\n", encoding="utf-8")

    findings = audit_text_truncation_and_overflow(
        tmp_path, target_files=["static/layout.css", "templates/view.html"]
    )
    css_findings = [f for f in findings if f["file"] == "static/layout.css"]
    html_findings = [f for f in findings if f["file"] == "templates/view.html"]

    assert [f["category"] for f in css_findings] == ["text_clipping"]
    assert [f["category"] for f in html_findings] == ["duplicate_text"]


def test_run_all_ui_reviews_modified_css_shorthand_passes_end_to_end(
    tmp_path: Path,
) -> None:
    """#17 integration: Modifying a .css file with multi-axis shorthands passes run_all_ui_reviews()."""
    repo = tmp_path / "web_repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@example.com"], cwd=repo, check=True
    )
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=repo, check=True)

    (repo / "static").mkdir()
    (repo / "static" / "style.css").write_text(
        ".box { color: #fff; }\n", encoding="utf-8"
    )
    (repo / "index.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="static/style.css?v=1"></head>'
        '<body><div class="box">Hello</div></body></html>\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)

    subprocess.run(["git", "checkout", "-q", "-b", "feat"], cwd=repo, check=True)
    (repo / "static" / "style.css").write_text(
        ".box { color: #fff; background-size: 14px 14px; border-radius: 10px 10px 0 0; }\n",
        encoding="utf-8",
    )
    (repo / "index.html").write_text(
        '<!DOCTYPE html><html><head><link rel="stylesheet" href="static/style.css?v=2"></head>'
        '<body><div class="box">Hello</div></body></html>\n',
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "css shorthand"], cwd=repo, check=True)

    res = run_all_ui_reviews(repo_root=repo, base_ref="main")
    assert res["status"] == "PASS", f"Expected PASS, got {res}"
    assert res["findings"] == []
