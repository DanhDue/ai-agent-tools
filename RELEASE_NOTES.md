# Release Notes: d3nexus v1.28.2

**Release Date:** November 10, 2026  
**Version:** `1.28.2`  
**Git Tag:** `v1.28.2`, `d3nexus--v1.28.2`

---

## Executive Summary

`v1.28.2` delivers comprehensive multi-profile anti-abuse isolation and remediation safeguards: cryptographically decoupling hardware fingerprints (`telemetry.machineId`) and device IDs, enforcing telemetry opt-out to prevent workspace path leaks, safeguarding host macOS AirDrop (`sharingd`) and Apple ID via Zero CLI Keychain mutations, and synchronizing profile isolation rules across `CRITICAL_RULES.md` and safe provisioning workflows.

---

## Key Highlights

### 1. Hardware Fingerprint Decoupling & Telemetry Opt-Out
- **Cryptographic Device Isolation**: Mandates unique SHA-256 `telemetry.machineId` and UUIDv4 `telemetry.devDeviceId` in `storage.json` for all Antigravity profiles, preventing Google Cloud / Clearcut telemetry correlation across multi-account setups.
- **Workspace Path Privacy**: Configures `"telemetry.telemetryLevel": "off"` in `settings.json`, preventing IDE telemetry from broadcasting open repository paths (`backupWorkspaces`) to Google/Microsoft telemetry endpoints.
- **Trajectory Isolation**: Eliminates foreign trajectory leaks in `conversation_summaries.db`, stopping repetitive 403 `PERMISSION_DENIED` background indexing errors.

### 2. AirDrop & Host OS Keychain Safeguards (Zero CLI Mutation)
- **Zero CLI Mutation**: Eliminates `security default-keychain` and `list-keychains` manipulation during CLI commands (`ag_run <profile> cli` and `{profile}-cli`). CLI invocations resolve credentials strictly through subshells (`HOME="$ag_home"`) and `com.apple.security.plist`.
- **AirDrop Protection**: Guarantees that host macOS system daemons (`sharingd`, `identityservicesd`, `trustd`) retain continuous, uninterrupted access to host `login.keychain-db`, preventing AirDrop discovery degradation (error code -15).
- **Hardened GUI Atomic Window**: Limits GUI IDE keychain promotion to 1.5s with automatic rollback verification.

### 3. Automated Profile Provisioning & Rule Governance
- **Automated Initialization (`ag_run init`)**: Provisions new profiles cleanly with automatic machine ID generation, devDeviceId creation, telemetry opt-out, and trajectory purge.
- **Critical Rules & Skill Sync**: Updates `rules/CRITICAL_RULES.md` (Sections 9.2, 9.6), `.agents/rules/profile_isolation_rules.md`, and `skills/audit-account-block/references/profile-isolation-and-remediation.md` with The 6 Core Isolation Rules.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish**
- `test_audit_account_block.py`: 🟢 **PASS** (4/4 unit tests passing)
- `test_refresh_session.py` & `test_agy_quota.py`: 🟢 **PASS** (53/53 unit tests passing)
- `test_lifecycle_document_contract.py` & `test_verifiable_handoff_text.py`: 🟢 **PASS** (26/26 contract tests passing)
