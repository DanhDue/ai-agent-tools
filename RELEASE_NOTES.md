# Release Notes: d3nexus v1.28.3

**Release Date:** November 11, 2026  
**Version:** `1.28.3`  
**Git Tag:** `v1.28.3`, `d3nexus--v1.28.3`

---

## Executive Summary

`v1.28.3` delivers significant multi-profile storage optimizations and hardened token isolation safeguards: reclaiming ~12 GB of disk space via the new `clean-cache` command, enforcing a synchronous 1.5s atomic launch lock with zero host keychain fallback to prevent cross-profile account bleed during token rotation, decoupling `credential-user-scope` across profiles, and streamlining the autonomous lifecycle pipeline with automated cross-model review convergence.

---

## Key Highlights

### 1. Multi-Profile Cache Cleaner (`d3nexus clean-cache`)
- **Space Recovery**: Safely targets Chromium bytecode (`CachedData`), Webview storage (`CacheStorage`), HTTP caches, stale `.vsix` installer archives, and Docker installation leftovers across all Antigravity profiles, reclaiming ~12 GB of host disk space without touching user settings, keychains, or sessions.
- **Safety Protocol**: Implements dry-run previews, automated process termination fencing (`pkill`), and post-clean verification.

### 2. Synchronous 1.5s Atomic Launch Lock & Zero Host Fallback
- **Zero Host Keychain Fallback**: Removes `login.keychain-db` from `security list-keychains` during non-root profile launches, ensuring unauthenticated or expired profiles never silently fall back to `danhdue@gmail.com`.
- **Synchronous Launch Lock**: Uses `/tmp/ag_launch.lock` with a synchronous 1.5-second foreground wait in `ag_run()`, serializing concurrent profile launches and blocking CLI/background calls (`agy`, `agy_quota.py`) during the keychain transition window.
- **Background Token Protection**: Profiles running with isolated `com.apple.security.plist` remain anchored to their dedicated keychains, eliminating token cross-contamination during automatic 1-hour OAuth rotation.

### 3. Credential User Scope & Identity Bleed Purge
- **Vector 8 Isolation**: Detects and repairs cloned `credential-user-scope` files, provisioning unique `u<16_hex_chars>` identifiers for each profile.
- **Keychain Parity Enforcement**: Audits OAuth tokens stored in the `gemini` generic-password keychain service and automatically deletes poisoned credentials in non-root profiles.

### 4. Streamlined Autonomous Lifecycle & Cross-Model Review
- **Zero Confirmation Pauses**: Automates Gate 3 execution order calculation, worktree bootstrapping, and transition from Gate 4 local PASS into Cross-Model Review.
- **Stage 4 Finish Gate**: Relocates the manual Finish decision and Gate 5 sign-off strictly to Stage 4 (`finishing-a-development-branch`) after review convergence.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish**
- `test_audit_account_block.py`: 🟢 **PASS** (8/8 unit tests passing)
- `test_lifecycle_document_contract.py` & `test_lifecycle_signals.py`: 🟢 **PASS** (28/28 contract tests passing)
- `test_agy_quota.py` & `test_kiro_quota.py`: 🟢 **PASS** (22/22 tests passing)
