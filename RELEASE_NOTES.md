# Release Notes: d3nexus v1.26.1

**Release Date:** November 07, 2026  
**Version:** `1.26.1`  
**Git Tag:** `v1.26.1`, `d3nexus--v1.26.1`

---

## Executive Summary

`v1.26.1` documents `.devtool/review_config.json` sticky provider loading across `d3nexus:principal-review`, `d3nexus:cross-model-review`, and `d3nexus:dev-lifecycle`, and upgrades `load_review_config()` in `run_external_review.py` to automatically backfill newly added `DEFAULT_REVIEW_CONFIG` providers (including `kiro`) into untracked `.devtool/review_config.json` files on disk.

---

## Key Highlights

### 1. Explicit `.devtool/review_config.json` Loading in Review Skills
- **`d3nexus:principal-review` & `d3nexus:cross-model-review`**: Explicitly instructs agents to read `.devtool/review_config.json` before prompting the developer to select a reviewer CLI (`claude`, `codex`, `agy`, `kiro`, `ollama`), surfacing `last_used_provider` and each provider's configured `model` and `thinking_level`.
- **Automatic Persistence**: Passing `--cli`, `--model`, or `--thinking-level` to `run_external_review.py run` updates `.devtool/review_config.json` atomically.

### 2. Automatic Provider Backfill on Disk (`load_review_config`)
- **`run_external_review.py`**: When reading an untracked `.devtool/review_config.json` that predates a newly added provider in `DEFAULT_REVIEW_CONFIG["providers"]` (such as `"kiro"`), `load_review_config()` now automatically backfills the missing default provider entry and saves `.devtool/review_config.json` to disk while preserving existing custom model/thinking preferences and keeping git-tracked test fixtures untouched.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish** (Sections 1–16, all 39 test suites green)
- `check_document.py`: 🟢 **PASS** (`0 findings` across updated skills and references)
