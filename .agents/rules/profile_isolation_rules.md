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

## 3. Host OS Keychain Protection
- NEVER execute `security default-keychain` globally in `~/.zshrc`. The host default keychain MUST always remain `/Users/<user>/Library/Keychains/login.keychain-db` so AirDrop, Apple ID, and Wi-Fi services remain intact.
- Multi-profile GUI launches use the **Atomic Launch Window**: temporary 2.5s search-list promotion of `<profile>.keychain-db` followed by automatic rollback to `login.keychain-db`.

## 4. Symlink Boundary Protection
- In shell scripts and `.zshrc`, never use unanchored wildcards like `antigravity)` in directory matchers. Always use `*antigravity*) ;;` to preserve independent physical directories for `.gemini/antigravity*`.

## 5. Automated Execution
- Whenever diagnosing identity bleed or repairing profiles, execute the certified engine:
  ```bash
  python3 scripts/remediate_profiles.py
  ```
- Detailed reference: `skills/audit-account-block/references/profile-isolation-and-remediation.md`.
