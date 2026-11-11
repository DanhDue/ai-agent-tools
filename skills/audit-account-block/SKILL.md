---
name: audit-account-block
description: Use when auditing Antigravity profiles for account block vulnerabilities, cloned machine IDs, cross-account trajectory leaks, rate-limit risks, or remediating profile security to prevent 403 Terms of Service suspensions.
---

# Antigravity Account Block & Anti-Abuse Audit Skill

Comprehensive diagnostic, scoring, and remediation engine for Antigravity multi-profile environments. Protects accounts against automatic 403 `PERMISSION_DENIED: Violation of Terms of Service` suspensions enforced by Google Cloud Code Assist and Google Clearcut telemetry.

---

## 1. When to Use This Skill

Activate this skill whenever you need to:
1. **Investigate Account Bans**: Diagnose why an account or profile received 403 `This service has been disabled in this account for violation of Terms of Service. Please submit an appeal`.
2. **Prevent Cascade Bans**: Audit all existing profiles for cloned hardware fingerprints before launching Antigravity CLI or IDE.
3. **Verify Profile Isolation**: Ensure new profiles cloned from templates have decoupled Machine IDs, unique Device IDs, and clean trajectory databases.
4. **Remediate Vulnerabilities**: Automatically decouple cloned telemetry IDs and purge foreign trajectory summaries across all accounts.

---

## 2. Core Detection Vectors (The 7 Anti-Abuse Loopholes)

| Vulnerability Vector | Risk Level | Root Cause | Google Detection Mechanism |
|---|---|---|---|
| **Cloned Machine ID** (`telemetry.machineId`) | **CRITICAL** | Profiles cloned from templates share identical 64-char hex SHA-256 hashes in `data/User/globalStorage/storage.json`. | Google Cloud Code Assist (`daily-cloudcode-pa.googleapis.com`) and Telemetry (`play.googleapis.com/log`) correlate multiple accounts sending the exact same `machineId` from 1 IP, flagging **Account Farming / Sybil Attacks**. |
| **Cross-Account Trajectory Leaks** | **CRITICAL** | Cloned `conversation_summaries.db` contains trajectories belonging to the master account. | Background `conversationsearch` tries to index foreign trajectory UUIDs, generating repeated 403 `PERMISSION_DENIED` errors logged as **Unauthorized Cross-Account Access / Scraping**. |
| **Keychain Host Leak & Identity Bleed** | **HIGH** | `com.apple.security.plist` points to host `/Library/Keychains/login.keychain` instead of `~/...`, causing `state.vscdb` to adopt host identity. | Extension host queries host keychain, sending master account OAuth tokens alongside satellite trajectory IDs or vice versa, causing immediate 403s and session hijacking flags. |
| **Burst Concurrency Rate Limit** | **HIGH** | `ThreadPoolExecutor(max_workers=6)` querying all accounts simultaneously without delay. | Burst spikes of 23 accounts connecting concurrently from the same residential IP trigger IP-level anti-bot throttling. |
| **Artificial Keep-Alive Prompts** | **HIGH** | Scripted activation or refresh using constant 1-character prompts (`agy -p "1"`). | Google AI Abuse models detect repetitive single-token requests without IDE context, typing latency, or code edit telemetry. |
| **Zero-Jitter Periodic Schedules** | **MEDIUM** | Scheduled tasks triggering at the exact second `00` (e.g. `05:30:00`). | Clock-synchronized machine periodicity without human jitter. |
| **Leaked Project File Paths** | **MEDIUM** | `backupWorkspaces` and `profileAssociations` in `storage.json` leaking absolute paths (e.g. `/Users/danhdueexoictif/...`). | Telemetry reports identical local filesystem paths across distinct Google identities. |

---

## 3. Tool Commands & Usage

The audit tool is located at `skills/audit-account-block/resources/scripts/audit_account_block.py`.

### A. Run Full Audit Inspection
Audits all profiles in `~/antigravity_homes/` and outputs a colored terminal report card:
```bash
python3 skills/audit-account-block/resources/scripts/audit_account_block.py
```
Or via binary entrypoint:
```bash
bin/d3nexus audit-account-block
```

### B. Automatically Remediate Vulnerabilities (`--fix`)
Generates unique cryptographically random SHA-256 `machineId` and UUIDv4 `devDeviceId` for each profile, clears leaked workspace paths, and purges stale cloned conversation records:
```bash
python3 skills/audit-account-block/resources/scripts/audit_account_block.py --fix
```

### C. Target a Single Profile
```bash
python3 skills/audit-account-block/resources/scripts/audit_account_block.py --target khe
python3 skills/audit-account-block/resources/scripts/audit_account_block.py --target khe --fix
```

### D. JSON Output (For Automation & CI/CD)
```bash
python3 skills/audit-account-block/resources/scripts/audit_account_block.py --json
```

---

## 4. Verification & Testing

Always verify the audit suite passes unit tests before and after modifying audit rules:
```bash
python3 skills/audit-account-block/resources/scripts/test_audit_account_block.py
```
All 4 unit tests (`test_audit_detects_duplicate_machine_ids`, `test_audit_detects_stale_trajectory_leaks`, `test_audit_detects_workspace_path_leaks`, `test_remediation_fixes_all_vulnerabilities`) must return `OK`.

---

## 5. Safe Multi-Profile Provisioning Checklist

When creating or provisioning a new Antigravity profile:
1. **Use automated initialization**: Run `ag_run <profile> init` in terminal. It automatically generates a unique `telemetry.machineId` (SHA-256), `telemetry.devDeviceId` (UUIDv4), configures `"telemetry.telemetryLevel": "off"`, and purges any cloned trajectories.
2. **Never copy `storage.json` blindly**: If manually copying from a template, run `audit-account-block --fix` immediately to decouple hardware fingerprints.
3. **Never clone `conversation_summaries.db`**: Initialize an empty SQLite database or let Antigravity create it natively on first run to prevent cross-account 403 trajectory sync errors.
4. **Stagger Cron Jobs**: Add random sleep jitter (1–60s) before executing automated refresh tasks.
5. **Use Scoped Keychain Unlock & Zero CLI Global Mutation**: Always unlock `<profile>.keychain-db` locally without mutating macOS global default keychain (`login.keychain-db`) to protect AirDrop (`sharingd`) and Apple ID services.

---

## 6. Profile Isolation & Identity Parity Protocol

To prevent profile identity bleed, stale RAM database overwrites, or breaking host macOS services (AirDrop, Apple ID, Keychain), all profile troubleshooting and remediation MUST follow the [Profile Isolation and Remediation Protocol](references/profile-isolation-and-remediation.md).


