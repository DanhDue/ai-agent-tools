# Release Notes: d3nexus v1.33.1

**Release Date:** November 19, 2026  
**Version:** `1.33.1`  
**Git Tag:** `v1.33.1`, `d3nexus--v1.33.1`

---

## Executive Summary

`v1.33.1` aligns the built-in Antigravity (`agy`) model catalogue in `dev-config` with live `agy` CLI model IDs so `orchestrator-argon` (`gemini-pro-orchestrator-g1-pro`), `orchestrator-neon` (`gemini-pro-orchestrator-neon`), and `neon` (`gemini-4-neon-{effort}`) work out of the box, infers `argonWeekly` accurately for `orchestrator` + `g1-pro` models, and classifies invalid CLI model selections as `model_unavailable`.

---

## Key Highlights

### 1. Built-In `agy` Catalogue Alignment (`scripts/personas.default.json`)
- Updated `orchestrator-argon` from the unrecognized `gemini-pro-orchestrator-argon` ID to `gemini-pro-orchestrator-g1-pro` (`efforts: ["none"]`, `quota_pool: "argonWeekly"`).
- Replaced retired `carbon` (`gemini-4-carbon-{effort}`) and `orchestrator-carbon` (`gemini-pro-orchestrator`) aliases with `neon` (`gemini-4-neon-{effort}`, `efforts: ["low", "medium", "high", "xhigh"]`) and `orchestrator-neon` (`gemini-pro-orchestrator-neon`, `efforts: ["none"]`).

### 2. Quota Pool Inference & Failure Classification (`scripts/persona_config.py`)
- Updated `derive_quota_pool` so `agy` model IDs containing `orchestrator` and `g1-pro` automatically resolve to the `argonWeekly` pool even without an explicit `quota_pool` override.
- Added `invalid model selection` and `not recognized as a known model` patterns to `_MODEL_FAILURE_PATTERNS` so unrecognized CLI models are surfaced as `model_unavailable` instead of generic task failures.

### 3. Skill Documentation & Regression Tests (`skills/dev-config/SKILL.md`, `tests/test_agy_effortless_models.py`)
- Updated `skills/dev-config/SKILL.md` examples and quota-pool guidance for `neon`, `orchestrator-neon`, and `orchestrator-argon` (`gemini-pro-orchestrator-g1-pro`).
- Expanded `tests/test_agy_effortless_models.py` with tests covering kit defaults, `g1-pro` `argonWeekly` derivation, and `invalid model selection` classification.

---

## Verifications & Quality Gates Passed

- `ruff check scripts/persona_config.py tests/test_agy_effortless_models.py` & `ruff format --check tests/test_agy_effortless_models.py`
- `uv run pytest tests/test_agy_effortless_models.py tests/test_fpg_persona_config.py tests/test_fpg_dispatch_and_quota.py tests/test_fpg_set_provider_model_profile.py tests/test_fpg_agy_dispatch.py -q --tb=short` (`152 passed`)
- `bash scripts/verify.sh` (all structural checks & 89 Python test suites)
