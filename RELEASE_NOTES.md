# Release Notes: d3nexus v1.36.0

**Release Date:** November 28, 2026  
**Version:** `1.36.0`  
**Git Tag:** `v1.36.0`, `d3nexus--v1.36.0`

---

## Executive Summary

`v1.36.0` promotes the **Open-Closed 6-Stack Polyglot Lifecycle & Quality Architecture**, the **Shift-Left `QualityPlanResolver` (`d3nexus resolve-quality`)**, **Fail-Closed Gate 2 & Standalone Plan Contract Guards**, **Unified Layered External Review Configuration (`/d3nexus:dev-config review`)**, and **Priority-Only Pool Routing** into the shared `d3nexus` plugin across Antigravity, Claude Code, Codex, and Kiro CLI.

---

## Key Highlights

### 1. Shift-Left `QualityPlanResolver` & Fail-Closed Pre-Code Guards (`skills/dev-implementation/`, `bin/d3nexus`)
- **On-Demand Mechanical Quality Brief (`d3nexus resolve-quality --files ...`)**: Resolves planned file lists in `< 0.10s` (Python 3 stdlib, zero LLM tokens) into 5–10 stack-filtered lines covering canonical/forbidden test directories, source-to-test pairing rules, Web V8 LCOV unit + Playwright `# tier: C2` requirements, monotonic `coverage_floors.json` ratchets, referencing `?v=` cache-bust templates, and `$D3NEXUS_KIT/skills`-interpolated `<allowed_files>`-scoped `TIER-B` commands.
- **Fail-Closed Contract Enforcement (`check_task_contract.py --design` & `--check-plan`)**: Rejects unexpanded `{skills_dir}`/`{base_ref}` placeholders, bare `npx` without `--no-install`, full-repo Python `ruff`/`mypy` commands on intermediate tasks (`Task 1..N-1`), missing JS LCOV unit tests, malformed `*-quality.json` manifests, `test_routing` violations, and missing `?v=` template co-edits before any subagent starts coding.

### 2. Open-Closed 6-Stack Polyglot Quality Providers & Monotonic Floor Ratchets (`skills/quality_check/`, `skills/*-quality-check/`)
- **Six-Stack Schema & Registry Parity**: Standardizes `TierBContractAdapter`, `PoolWorkspaceStrategy` (symlinked binary caches + macOS APFS copy-on-write `.dart_tool/` trees), suffix-scoped `TriageSurfaceRegistry`, `TierCTaxonomy` (`Tier C1` `< 5s` vs `Tier C2`), `test_routing`, and `coverage.package_floors` across Python, Flutter, Rust, Web, Android, and iOS.
- **Portable Hunk Diff Coverage & Receipt Hygiene**: `check_diff_coverage.py` validates LCOV, Cobertura XML, and JaCoCo XML workspace/package/hunk thresholds plus `--package-floors <coverage_floors.json>` (`enforced_coverage_pct`); `verify_polyglot_registry.py` automatically deletes stale `build/quality/gate4_receipt.json` on non-passing `epic`/`release` runs; `scaffold_quality_manifest.py` emits deduplicated 4-profile manifests (`pr_*` in `pr` only; `workspace_*` in `epic`/`scheduled`/`release`).

### 3. Unified Review Config, Priority-Only Pool Routing & Dashboard Portability (`scripts/`, `skills/check-tasks/`)
- **Unified External Review Config**: `/d3nexus:dev-config review`, `limits`, and `thresholds` manage external reviewer priority, round caps, and auto-triage thresholds across global and per-repo configs.
- **Priority-Only Pool Acquisition & Hot Reload**: Retires `dev-config set --profile` overrides in favor of strict priority-order pool routing and hot-reloads kit modules in `tasks_server.py` with zero hardcoded host paths.

---

## Verifications & Quality Gates Passed

- `python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc docs/architecture/polyglot-quality-lifecycle-handoff.md docs/architecture/shift_left_upgrade_and_ecosystem_coverage_report.md` (`0 findings`)
- `python3 -m pytest -q tests/test_slqr_*.py tests/test_plq_*.py tests/test_urc_*.py` (`PASS`)
- `bash scripts/verify.sh` (all manifest, frontmatter, link, anchor, fidelity, reachability, and parallel Python test suites: `PASS — safe to publish`)
