# Local Rule: Antigravity Profile Isolation & Remediation Boundaries

> [!IMPORTANT]
> This is a localized rule governing Antigravity multi-profile isolation, Keychain boundaries, and remediation procedures. It is scoped specifically to prevent profile cross-contamination without polluting general coding context.

## 1. Process Fencing Before Database Edits
- **Never edit a profile database while its IDE/CLI process is running**: Before modifying `state.vscdb`, `storage.json`, or Keychain credentials for profile `<profile>`, always check and terminate resident Electron / agy processes:
  ```bash
  pkill -9 -f "antigravity_homes/<profile>"
  ```
- Resident processes hold SQLite state in memory and will overwrite your disk changes on exit.

## 2. Token Parity & Stale Cache Elimination
- Always purge `antigravityUnifiedStateSync.oauthToken` from `ItemTable` in `state.vscdb` to prevent stale `signedOut` flags from forcing fallback to the root default account.
- Always verify parity between `id_token_email` inside `<profile>.keychain-db` and `agy.onboarding.lastLoginUsername` in `state.vscdb`.

## 3. Host OS Keychain Protection & AirDrop Safeguard
- **Zero Global Mutation**: NEVER execute `security default-keychain` or `security list-keychains -s` globally in `~/.zshrc` or shell startup scripts. The host default keychain MUST always remain `/Users/<user>/Library/Keychains/login.keychain-db` so AirDrop (`sharingd`), Apple ID (`identityservicesd`), and Wi-Fi credentials are never disrupted.
- **Zero CLI Mutation**: CLI commands (`ag_run <profile> cli`, `{profile}-cli`) must NEVER mutate `security default-keychain`. Scoped keychain unlock inside the profile subshell (`HOME="$ag_home"`) provides all required access via `~/Library/Preferences/com.apple.security.plist`.
- **Atomic Launch Window for GUI**: Multi-profile GUI IDE launches use a brief atomic window (temporary 1.5s search-list promotion of `<profile>.keychain-db` followed by automatic background rollback to `login.keychain-db`).

## 4. Hardware Fingerprint Decoupling & Anti-Abuse Isolation
- **Unique Machine ID**: Every profile's `data/User/globalStorage/storage.json` MUST contain a cryptographically unique SHA-256 `telemetry.machineId` and UUIDv4 `telemetry.devDeviceId`. Never clone `storage.json` without regenerating these keys.
- **Mandatory Telemetry Opt-Out**: Every profile's `data/User/settings.json` MUST configure `"telemetry.telemetryLevel": "off"` to prevent leaking workspace paths (`backupWorkspaces`) and hardware fingerprints to Google Cloud Code Assist.
- **Trajectory Isolation**: Never copy `conversation_summaries.db` or `agyhub_summaries_proto.pb` between profiles. All profile trajectory databases must only reference conversations created natively by that profile.

## 5. Symlink Boundary Protection
- In shell scripts and `.zshrc`, never use unanchored wildcards like `antigravity)` in directory matchers. Always use `*antigravity*) ;;` to preserve independent physical directories for `.gemini/antigravity*`.

## 6. Automated Execution
- Whenever diagnosing identity bleed or repairing profiles, execute the certified audit & remediation engine:
  ```bash
  python3 skills/audit-account-block/resources/scripts/audit_account_block.py --fix
  ```
- Detailed reference: `skills/audit-account-block/references/profile-isolation-and-remediation.md`.

