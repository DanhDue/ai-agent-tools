# Antigravity Profile Isolation & Cross-Configuration Remediation Protocol

> [!CRITICAL]
> **This protocol defines mandatory operational boundaries for isolating Antigravity profiles without breaking host macOS system services (AirDrop, Apple ID, Wi-Fi, Keychain, Web Browsers) or allowing profile states to contaminate one another.**

---

## 1. Problem Statement: The Cross-Contamination Dilemma

When managing 20+ isolated Antigravity user profiles on a single machine:
1. **Modifying Host Configs Breaks Profiles**: Changing shell variables, Keychain search lists, or toolchain symlinks globally causes satellite profiles to fall back to the root account (`danhdue@gmail.com`).
2. **Modifying Profile Configs Breaks Host Services**: Setting a profile keychain as the system default (`security default-keychain <profile>.keychain-db`) immediately cripples macOS background system daemons, notably `sharingd` (AirDrop failures), `identityservicesd` (Apple ID / Messages desync), and Wi-Fi credential lookups.
3. **Silent Reversion via Stale RAM ("Ghost Electron Process")**: When editing `state.vscdb` while a background Antigravity IDE process (`PID`) of that profile remains resident, Electron holds the old in-memory state and periodically flushes `danhdue@gmail.com` back into the SQLite database, silently undoing any manual or scripted remediation.
4. **Fallback on `signedOut` Tokens**: If `ItemTable` in `state.vscdb` retains `antigravityUnifiedStateSync.oauthToken` marked as `signedOut`, Antigravity treats the session as unauthenticated and falls back to the default host profile.

---

## 2. The 5 Core Isolation Rules

```
                      ┌───────────────────────────────────────────────┐
                      │            macOS Host Environment             │
                      │  Default Keychain: login.keychain-db (Fixed)  │
                      │  HOME: /Users/<user>                          │
                      └───────────────────────┬───────────────────────┘
                                              │
                      ┌───────────────────────▼───────────────────────┐
                      │    Launcher: ag_run() / profile-cli           │
                      │  1. Terminate stale PIDs of this profile      │
                      │  2. Strip parent Electron / IPC env vars       │
                      │  3. Atomic 2.5s Keychain promotion window      │
                      │  4. Auto-rollback default to login.keychain    │
                      └───────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
┌────────▼────────┐                  ┌────────▼────────┐                  ┌────────▼────────┐
│ Profile: hau    │                  │ Profile: tess   │                  │ Profile: molt   │
│ • hau.keychain  │                  │ • tess.keychain │                  │ • molt.keychain │
│ • state.vscdb   │                  │ • state.vscdb   │                  │ • state.vscdb   │
│ • No symlink to │                  │ • No symlink to │                  │ • No symlink to │
│   .gemini/root  │                  │   .gemini/root  │                  │   .gemini/root  │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
```

### Rule 2.1: Pre-Remediation Process Fencing (Zero Stale RAM Overwrite)
Before inspecting, editing, or remediating any profile database (`state.vscdb`, `storage.json`, `conversation_summaries.db`) or Keychain token:
- **MUST** search for resident processes associated with that profile home:
  ```bash
  ps aux | grep -E "antigravity_homes/<profile>|AGY_PROFILE=<profile>" | grep -v grep
  ```
- **MUST** terminate all matching PIDs before performing any database edits:
  ```bash
  pkill -9 -f "antigravity_homes/<profile>"
  ```
- Failure to kill resident Electron processes will result in the process flushing stale RAM state back to disk on exit or timer.

### Rule 2.2: Stale `signedOut` OAuth Token Elimination
In `~/antigravity_homes/<profile>/data/User/globalStorage/state.vscdb`:
- Antigravity IDE checks `ItemTable` for `antigravityUnifiedStateSync.oauthToken`.
- If this key contains `"signedOut": true` or stale credentials, the IDE marks the profile as logged out and silently adopts the host/default identity from `login.keychain-db`.
- **Enforcement**: Remediation scripts and repair procedures MUST execute:
  ```sql
  DELETE FROM ItemTable WHERE key = 'antigravityUnifiedStateSync.oauthToken';
  ```
  This forces the IDE on startup to query the dedicated profile Keychain rather than relying on a stale sign-out cache.

### Rule 2.3: Keychain-to-DB Identity Parity Verification
For every non-root profile:
1. Extract the actual token identity from the profile's dedicated Keychain:
   ```bash
   security unlock-keychain -p "$KC_PASS" ~/antigravity_homes/<profile>/Library/Keychains/<profile>.keychain-db
   security find-generic-password -s "gemini" -a "antigravity" -g ~/antigravity_homes/<profile>/Library/Keychains/<profile>.keychain-db
   ```
   Decode the `go-keyring-base64` payload to extract `id_token_email`.
2. Inspect `agy.onboarding.lastLoginUsername` in `state.vscdb`:
   ```sql
   SELECT value FROM ItemTable WHERE key = 'google.google-antigravity';
   ```
3. If `agy.onboarding.lastLoginUsername` differs from `id_token_email`, update `state.vscdb` to match `id_token_email` immediately.

### Rule 2.4: Atomic Launch Window in `ag_run()` (No Global Keychain Mutation)
To avoid contaminating host OS services or other profiles:
- **Global Mutation Prohibited**: NEVER invoke `security default-keychain` globally in `~/.zshrc` or global login hooks. The host default keychain MUST always remain `/Users/<user>/Library/Keychains/login.keychain-db`.
- **Atomic Launch Window**: When launching a profile via `ag_run()`, isolate Keychain access exclusively via:
  1. Setting `com.apple.security.plist` in `~/antigravity_homes/<profile>/Library/Preferences/`.
  2. For non-root GUI launches, temporarily promote `<profile>.keychain-db` ahead of `login.keychain-db` in the search list and set default, spawn the IDE via stripped environment, and immediately schedule an atomic rollback back to `login.keychain-db` after 2.5 seconds:
     ```bash
     security list-keychains -d user -s "$profile_kc" "$REAL_HOME/Library/Keychains/login.keychain-db" "/Library/Keychains/System.keychain"
     security default-keychain -s "$profile_kc"
     # Launch detached IDE process...
     ( sleep 2.5 && security list-keychains -d user -s "$REAL_HOME/Library/Keychains/login.keychain-db" "/Library/Keychains/System.keychain" && security default-keychain -s "$REAL_HOME/Library/Keychains/login.keychain-db" ) >/dev/null 2>&1 &!
     ```
  3. For CLI invocations (`{profile}-cli`), run inside an isolated subshell where keychain unlock is scoped and no global list mutation occurs.

### Rule 2.5: Rogue Symlink Elimination & Strict State Independence
- **Wildcard Danger**: In shell functions and provisioning scripts, NEVER use imprecise wildcards such as `antigravity)` in case statements. An unanchored match will catch `.gemini/antigravity*` and replace profile-specific directories with symlinks to root!
- **Safe Match Pattern**: Use explicit exclusion:
  ```zsh
  *antigravity*) ;; # Exclude ALL Antigravity internal agent runtime directories
  ```
- **Physical Directory Isolation**: Every profile MUST have physical, non-symlinked directories for:
  - `.gemini/antigravity/`
  - `.gemini/antigravity/conversations/`
  - `.gemini/antigravity/conversation_summaries.db`
  - `data/User/globalStorage/state.vscdb`
  - `data/User/globalStorage/storage.json`

---

## 3. Standard Remediation Workflow

When any profile displays identity bleed or opens under `danhdue@gmail.com`:

```bash
# Step 1: Kill all running processes of the profile
pkill -9 -f "antigravity_homes/<profile>"

# Step 2: Run automated remediation engine
python3 scripts/remediate_profiles.py

# Step 3: Verify identity parity
python3 -c "
import sqlite3, json, subprocess, base64
profile = '<profile>'
home = f'/Users/danhdue/antigravity_homes/{profile}'
kc = f'{home}/Library/Keychains/{profile}.keychain-db'
subprocess.run(['security', 'unlock-keychain', '-p', 'H@No!a@12345', kc], capture_output=True)
res = subprocess.run(['security', 'find-generic-password', '-s', 'gemini', '-a', 'antigravity', '-g', kc], capture_output=True, text=True)
b64 = res.stderr.split('password: \"go-keyring-base64:')[1].split('\"')[0]
kc_email = json.loads(base64.b64decode(b64).decode())['id_token_email']

conn = sqlite3.connect(f'{home}/data/User/globalStorage/state.vscdb')
row = conn.cursor().execute(\"SELECT value FROM ItemTable WHERE key='google.google-antigravity'\").fetchone()
db_email = json.loads(row[0])['antigravity-storage']['agy.onboarding.lastLoginUsername']
print(f'Keychain: {kc_email} | DB: {db_email} | Parity: {kc_email == db_email}')
"

# Step 4: Test isolated CLI launch
<profile>-cli models
```
