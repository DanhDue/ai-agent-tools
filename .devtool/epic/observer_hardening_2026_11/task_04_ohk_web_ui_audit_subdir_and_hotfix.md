---
id: "task_04_ohk_web_ui_audit_subdir_and_hotfix"
status: "done"
priority: "high"
assignee: null
epic: "observer-hardening-2026-11"
dueDate: null
created: "2026-11-26T22:10:00Z"
modified: "2026-11-26T17:16:54Z"
completedAt: "2026-11-26T17:16:54Z"
labels: ["architecture", "web-quality"]
order: "a4"
review_tier: "full"
---

# Task 4: Fix Subdirectory `git show` and Uncommitted Diff Merge in `audit_ui_state_and_styles.py` and Fold Live Plugin Exclusions/Scoping Hotfix

Epic: [observer-hardening-2026-11](observer_hardening_2026_11.md)

## Requirement Analysis

Fix observation `#8` and cleanly fold the live plugin hotfix into `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py` so a future `scripts/release.sh` preserves it with full test coverage:

1. **Subdirectory `git show` Fix (`#8`)**:
   - Update `_get_base_file_content(repo_root, base_ref, rel_path)` to normalize `rel_path` to POSIX form without leading `./` and execute `git show f"{base_ref}:./{norm_rel}"` with `cwd=str(repo_root)` so subdirectory `--project-root` invocations resolve relative to `repo_root` rather than git top-level.
2. **Uncommitted Diff Merge (`#8`)**:
   - Update `get_git_diff_files(repo_root, base_ref)` to union (preserving order and deduplicating) committed branch diff (`git diff --name-only {base_ref}...HEAD`, falling back to 2-dot `{base_ref}` if 3-dot fails) PLUS uncommitted working-tree tracked modifications (`git diff --name-only HEAD`), staged changes (`git diff --name-only --cached`), and non-ignored untracked files (`git ls-files --others --exclude-standard`), all normalized relative to `repo_root`.
3. **Folded Live Plugin Hotfix**:
   - Expand `_is_excluded(p, repo_root)` to exclude: `node_modules`, `build`, `.worktrees`, `.git`, `dist`, `.astro`, `.devtool`, `docs`, `target`, `tests`.
   - In `run_all_ui_reviews()`: filter `ui_modified` with `not _is_excluded(root / f, root)`, return `NOT_APPLICABLE` (`scope_unmodified`) when `modified_files` is non-empty and `ui_modified` is empty, pass `target_files=ui_modified` to Invariants 2, 3, and 4 when `_git_base_ref_exists(root, base_ref)` is True, and filter out pre-existing base-ref findings using `_get_base_file_content(root, base_ref, rel_f)` (computing base `unstyled_default` messages once per file rather than per finding).

## Files

Allowed files:
- `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py`
- `tests/test_audit_ui_state_and_styles.py`
- `tests/test_ohk_web_ui_audit.py` (new)

Read-only context:
- `.devtool/epic/observer_hardening_2026_11/2026-11-26-observer-hardening-design.md`
- `.devtool/epic/observer_hardening_2026_11/observer_hardening_2026_11.md`

## Design Rationale & Applicable Skills

- Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`, `d3nexus:web-quality-check`.
- Notice that `audit_ui_state_and_styles.py` sits inside `skills/web-quality-check`, which is covered by `.agents/quality/python-quality.json`'s `format` (`ruff format --check`) and `lint` (`ruff check`). Keep formatting and typing clean.

## Impact Analysis & Blast Radius

- **Target Files & Symbols**:
  - `skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py`: `get_git_diff_files` (L83-L156), `_is_excluded` (L158-L169), `_get_base_file_content` (L171-L185), `run_all_ui_reviews` (L600-L651).
  - `tests/test_audit_ui_state_and_styles.py`: UI audit regression tests (L1-L280).
- **Downstream Callers**: `tests/test_audit_ui_state_and_styles.py`, `tests/test_web_quality_provider.py`.
- **Target Coverage**: 100% of modified branches in `audit_ui_state_and_styles.py`.

### BDD SCENARIOS

Covers: OHK-HP-04, OHK-EC-04, OHK-AR-01

```gherkin
Scenario: [OHK-HP-04] [Tier C - Integration] Subdirectory UI audit resolves base templates and merges uncommitted template edits
Given a git repository whose web preview lives in subdirectory "src/app/preview"
And commit HEAD modifies "src/app/preview/static/style.css" while base ref "main" holds "static/search.html" with "style.css?v=1" and ".well-known/portal.html" with "style.css?v=1"
And the working tree has an uncommitted edit bumping "src/app/preview/static/search.html" to "style.css?v=2" and ".well-known/portal.html" to "style.css?v=2"
When "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" executes
Then "_get_base_file_content" resolves both "main:./static/search.html" and "main:./.well-known/portal.html" cleanly without stripping leading dots and rejects "../outside.html"
And "get_git_diff_files" includes "static/style.css", uncommitted "static/search.html", and uncommitted ".well-known/portal.html"
And the JSON report returns status "PASS" with 0 cache_bust findings
When ".well-known/portal.html" is modified without bumping "?v=1"
Then "audit_ui_state_and_styles.py --project-root src/app/preview --base-ref main --json" returns status "FAIL" with a "cache_bust" finding on ".well-known/portal.html"

Scenario: [OHK-EC-04] [Tier C - Integration] UI auditor excludes build directories, ignores pre-existing base-ref orphans, and catches CSS-only class removals including layout-inherited templates
Given a web project containing compiled HTML with orphaned classes inside "dist/", ".astro/", ".devtool/", "docs/", "target/", and "tests/"
And "src/layout.html" links "src/style.css" while unchanged child page "src/page.html" inherits "src/layout.html" without a direct stylesheet link and carries pre-existing orphaned class "legacy-unmapped" plus styled class "active-card" defined in "src/style.css" at base ref "main"
And HEAD edits only text on "src/page.html" without touching "src/style.css"
When "audit_ui_state_and_styles.py --base-ref main --json" executes
Then files under "dist/", ".astro/", ".devtool/", "docs/", "target/", and "tests/" produce zero findings
And pre-existing "legacy-unmapped" on "src/page.html" is filtered out so status is "PASS"
When HEAD instead modifies only "src/style.css" to delete ".active-card" while leaving both "src/layout.html" and child "src/page.html" untouched
Then "audit_ui_state_and_styles.py --base-ref main --json" scans all non-excluded templates for Invariant 2 and returns status "FAIL" with an "orphaned_class" finding for "active-card" on "src/page.html" while still suppressing pre-existing "legacy-unmapped"
And adding a brand-new undefined class "new-orphan-cls" on "src/page.html" also returns status "FAIL" with category "orphaned_class"

Scenario: [OHK-AR-01] [Tier C - Integration] Non-UI changes return NOT_APPLICABLE when only excluded paths contain HTML or CSS
Given a git branch diff against "main" that modifies "src/backend.py" and compiled "dist/index.html" with zero non-excluded UI source edits
When "audit_ui_state_and_styles.py --base-ref main --json" executes
Then status is "NOT_APPLICABLE" with reason code "scope_unmodified" and "ui_modified_files_count" equal to 0
```

## Verification

| ID | Phase | Command | Expect | Needs |
|---|---|---|---|---|
| V1 | RED | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_web_ui_audit.py::test_ohk_hp_04_subdir_base_and_uncommitted_merge` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_web_ui_audit.py` | exit 0; contains "passed" | — |
| V3 | REGRESSION | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_audit_ui_state_and_styles.py tests/test_web_quality_provider.py` | exit 0; contains "passed" | — |
| V4 | TIER-B | `ruff check skills/web-quality-check tests skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && ruff format --check skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py tests/test_audit_ui_state_and_styles.py tests/test_ohk_web_ui_audit.py` | exit 0 | — |
| V5 | TIER-B | `mypy skills/web-quality-check/resources/scripts/validate_web_quality.py skills/web-quality-check/resources/scripts/run_playwright_harness.py skills/quality_check/resources/scripts/verify_polyglot_registry.py skills/web-quality-check/resources/scripts/check_vanilla_js.py skills/dev-implementation/resources/scripts/generate_smoke_checklist.py scripts/_state_envelope.py scripts/estimate_heartbeat.py && mypy --ignore-missing-imports --follow-imports=silent skills/web-quality-check/resources/scripts/audit_ui_state_and_styles.py tests/test_audit_ui_state_and_styles.py tests/test_ohk_web_ui_audit.py` | exit 0 | — |
| V6 | TIER-C | `python3 -m pytest -q --tb=short --maxfail=3 tests/test_ohk_web_ui_audit.py --junitxml=build/test-results/task_04.xml` | exit 0; results build/test-results/task_04.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done criteria (ticking `- [x]` with result notes after verify is expected), Allowed files or Covers line.
- A variable named in the Needs column is unset.

## Decisions Already Made

- **Source (`audit_ui_state_and_styles.py:171-185`)**: `_get_base_file_content` runs `["git", "show", f"{base_ref}:{rel_path}"]` with `cwd=str(repo_root)`.
  - **New contract**: Normalize `rel_path` to POSIX form (`raw_posix = Path(rel_path).as_posix()`) by stripping ONLY exact leading `./` segments (`while norm_rel.startswith("./"): norm_rel = norm_rel[2:]`), never `.lstrip("./")` so dot-prefixed directories like `.well-known/portal.html` stay intact. Reject empty paths, absolute paths, or any path containing `..` parent-traversal parts (returning `None`). Invoke `["git", "show", f"{base_ref}:./{norm_rel}"]` with `cwd=str(repo_root)`.
- **Source (`audit_ui_state_and_styles.py:83-156`)**: `get_git_diff_files` returns immediately when 3-dot `base_ref...HEAD` is non-empty, omitting uncommitted edits.
  - **New contract**: Union ordered unique lines from: (1) `git diff --name-only {base_ref}...HEAD` (falling back to 2-dot `git diff --name-only {base_ref}` if 3-dot returns non-zero), (2) `git diff --name-only HEAD`, (3) `git diff --name-only --cached`, and (4) `git ls-files --others --exclude-standard`, normalized relative to `repo_root`.
- **Source (`audit_ui_state_and_styles.py:158-169`, `286-391`, `600-651`)**: `_is_excluded` excludes only 4 dirs; `run_all_ui_reviews` runs Invariants 2–4 with `target_files=None`.
  - **New contract**: Exclude `("node_modules", "build", ".worktrees", ".git", "dist", ".astro", ".devtool", "docs", "target", "tests")`. When `_git_base_ref_exists(root, base_ref)` is True: compute `ui_modified` excluding `_is_excluded`; short-circuit `NOT_APPLICABLE` if `modified_files` non-empty and `ui_modified` empty; when `ui_modified` is non-empty:
    - For Invariants 3 and 4, pass `target_files=ui_modified`.
    - For Invariant 2 (`audit_orphaned_classes_and_styles`), check `has_css_change = any(Path(f).suffix.lower() in {".css", ".scss"} for f in ui_modified)`: when `has_css_change` is True, pass `target_files=None` so ALL non-excluded source templates (`*.html`, `*.astro`, `*.jinja`, `*.jinja2`, `*.jsx`, `*.tsx`) are checked — catching newly orphaned classes in both directly linked and layout-inherited templates (`layout.html` -> `page.html`) without fragile link-graph heuristics; when `has_css_change` is False, pass `target_files=ui_modified`.
    - Filter out pre-existing base-ref findings across all files reported in `inv234` (not just `ui_modified`, since CSS-change Invariant 2 scans unchanged templates too!) using `_get_base_file_content(root, base_ref, rel_f)`: for `orphaned_class`, collect `base_defined_classes` from all non-excluded stylesheets and component `<style>` blocks at `base_ref` via `_get_base_file_content()` and suppress `(rel_f, cls)` ONLY when `cls` was ALREADY referenced in `base_contents[rel_f]` AND was ALREADY undefined (`cls not in base_defined_classes`) at `base_ref` — ensuring deleting `.active-card` from `style.css` flags `page.html` while pre-existing `legacy-unmapped` remains suppressed. Precompute `base_unstyled_by_file` once per file rather than per finding.
    - When `modified_files` is empty (non-git temp dir or clean checkout with zero diff against `base_ref`), pass `target_files=None` so existing full-directory unit tests in `test_audit_ui_state_and_styles.py` keep passing unchanged.

## Definition of Done

- [x] `_get_base_file_content` uses `{base_ref}:./{norm_rel}` and `get_git_diff_files` unions committed and uncommitted diffs (V2, V3, V6) — exit 0, V2/V6 11 passed, V3 18 passed
- [x] Folded live plugin exclusions (`dist`, `.astro`, `.devtool`, `docs`, `target`, `tests`), `ui_modified` scoping, and pre-existing base-ref filtering pass without regressing existing tests (V2, V3, V6) — exit 0, V2/V6 11 passed, V3 18 passed
- [x] `ruff check`, `ruff format --check`, and `mypy` pass across all Allowed files (V4, V5) — exit 0, 0 issues
- [x] Assigned BDD integration scenarios (`OHK-HP-04`, `OHK-EC-04`, `OHK-AR-01`) pass with JUnit XML evidence (V6) — exit 0, 3/3 covered in `build/test-results/task_04.xml`

## Dependencies & Blockers

None.

## References & Rollback

- Spec: [2026-11-26-observer-hardening-design.md](2026-11-26-observer-hardening-design.md)
- HLD: [observer_hardening_2026_11.md](observer_hardening_2026_11.md)
- BDD: [bdd_scenarios.md](bdd_scenarios.md)
- Rollback: Revert this task's commit on `epic/observer-hardening-2026-11`.
