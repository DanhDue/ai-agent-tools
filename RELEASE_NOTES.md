# Release Notes: d3nexus v1.26.2

**Release Date:** November 07, 2026  
**Version:** `1.26.2`  
**Git Tag:** `v1.26.2`, `d3nexus--v1.26.2`

---

## Executive Summary

`v1.26.2` delivers **Detached Background Daemon Mode** for the Antigravity Multi-Profile Quota Dashboard (`check-quota --ui`), **Automated Argon 7D Weekly Activation with Under-7H Reset Guard**, **Anti-Bot Jitter Pacing** across multi-model pings, safe JSON extraction and atomic cache persistence in `quota_dashboard.html`, and a comprehensive unit test suite in `tests/test_agy_quota.py`.

---

## Key Highlights

### 1. Detached Background Daemon Mode (`check-quota --ui`)
- **Terminal Independence**: `check-quota --ui` (or `agy-quota ui`) spawns a detached background process (`start_new_session=True`) and returns terminal prompt control in `<0.2s`. Developers can safely close or exit the terminal while the web dashboard remains running on `http://127.0.0.1:8765`.
- **Management Commands**:
  - `check-quota --status`: Checks running state, active PID (`/tmp/agy_quota_server.pid`), URL, and log path (`/tmp/agy_quota_server.log`).
  - `check-quota --stop`: Gracefully terminates background daemon and frees port 8765.
  - `check-quota --ui -f`: Runs in traditional foreground mode for interactive debugging.
- **Pipe Resilience**: Wraps `log_message` and `send_json` in `try...except` to prevent broken stdout pipes from terminating handler threads when terminals close.

### 2. Automated Argon 7D Activation & Under-7H Reset Guard
- **Max 7D Trigger**: When pinging a profile with Argon enabled (`hasArgon: true`), if Argon weekly quota is at max 7D (`fraction >= 0.999` and not yet locked into a weekly cycle), the system automatically fires a 1-token prompt to `--model gemini-4-argon-low` to start the 7-day countdown.
- **Reset Guard (< 7h)**: If Argon is already active and its reset time is under 7 hours (`is_argon_near_reset`), Argon pings are strictly skipped to conserve quota right before weekly renewal.
- **Already Active Skip**: If Argon is already counting down mid-cycle, pings to Argon are skipped to prevent wasting tokens.

### 3. Anti-Bot Jitter Pacing (1.8s – 3.5s)
- **Natural Pacing**: When activating both Gemini and Argon in the same turn, an automated random jitter of **1.8s – 3.5s** (`random.uniform(1.8, 3.5)`) is enforced between calls.
- **Distinct Prompts**: Successive prompts are pulled from `NATURAL_PROMPTS` ensuring non-identical payloads, eliminating Google WAF / anti-abuse 429 rate limits and Terms of Service suspensions.

### 4. Resilient JSON Cache Persistence
- **Block Boundary Matching**: `load_cached_profiles()` and `update_cached_profile()` match `const PROFILES_DATA = ... \n};` instead of the first semicolon, eliminating truncation and preserving the entire dashboard HTML structure.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish** (Sections 1–16, all 39 test suites green)
- `tests/test_agy_quota.py`: 🟢 **PASS** (9/9 unit tests passing)
