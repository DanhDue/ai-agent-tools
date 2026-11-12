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

## 2. The 6 Core Isolation Rules

```
                      ┌───────────────────────────────────────────────┐
                      │            macOS Host Environment             │
                      │  Default Keychain: login.keychain-db (Fixed)  │
                      │  HOME: /Users/<user>                          │
                      │  AirDrop Daemon: sharingd (Uninterrupted)     │
                      └───────────────────────┬───────────────────────┘
                                              │
                      ┌───────────────────────▼───────────────────────┐
                      │    Launcher: ag_run() / profile-cli           │
                      │  1. Terminate stale PIDs of this profile      │
                      │  2. Strip parent Electron / IPC env vars      │
                      │  3. CLI: ZERO global keychain mutation        │
                      │  4. GUI: Atomic 1.5s window + auto-rollback   │
                      │  5. Auto-generate unique Machine ID & UUID    │
                      │  6. Auto-disable telemetry (telemetryLevel)   │
                      └───────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
┌────────▼────────┐                  ┌────────▼────────┐                  ┌────────▼────────┐
│ Profile: hau    │                  │ Profile: tess   │                  │ Profile: molt   │
│ • hau.keychain  │                  │ • tess.keychain │                  │ • molt.keychain │
│ • state.vscdb   │                  │ • state.vscdb   │                  │ • state.vscdb   │
│ • storage.json  │                  │ • storage.json  │                  │ • storage.json  │
│   (Unique MID)  │                  │   (Unique MID)  │                  │   (Unique MID)  │
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

### Rule 2.4: Synchronous 1.5s Atomic Launch Lock & Zero Host Fallback
To avoid contaminating host OS services, breaking AirDrop (`sharingd`), or causing cross-profile token collisions during startup:
- **Global Mutation Prohibited**: NEVER invoke `security default-keychain` globally in `~/.zshrc` or global login hooks. The host default keychain MUST always remain `/Users/<user>/Library/Keychains/login.keychain-db`.
- **Zero Mutation for CLI**: When running CLI commands (`ag_run <profile> cli` or `{profile}-cli`), NEVER alter `security default-keychain` or `security list-keychains`. The CLI binary runs in a subshell with `HOME="$ag_home"` and reads the scoped profile keychain via `~/Library/Preferences/com.apple.security.plist` and `login.keychain-db -> <profile>.keychain-db` symlink directly after scoped `security unlock-keychain`. This guarantees AirDrop (`sharingd`) is never interrupted or crashed by background CLI quota refreshes.
- **Zero Host Fallback in Search List**: When launching the GUI IDE for a non-root profile, the search list MUST strictly contain only `"$profile_kc"` and `"/Library/Keychains/System.keychain"`. NEVER include `login.keychain-db` in the search list, ensuring that an unauthenticated or expired profile never silently falls back to `danhdue@gmail.com`.
- **Synchronous 1.5s Launch Lock (`/tmp/ag_launch.lock`)**:
  To prevent race conditions when opening multiple IDE windows or when an existing background profile refreshes its token:
  1. `ag_run()` acquires the atomic filesystem lock `/tmp/ag_launch.lock`.
  2. Sets `security list-keychains -d user -s "$profile_kc" "/Library/Keychains/System.keychain"` and `security default-keychain -s "$profile_kc"`.
  3. Launches Electron IDE via `open -n -a "Antigravity IDE"`.
  4. **Waits synchronously in the foreground for 1.5 seconds** (blocking any subsequent command in the current terminal, while other terminals or `agy()` / quota calls wait on `/tmp/ag_launch.lock`).
  5. Restores `default-keychain` and `list-keychains` to `login.keychain-db` + `System.keychain`.
  6. Releases `/tmp/ag_launch.lock`.
  ```bash
  # Atomic launch lock & zero fallback implementation:
  local lock_dir="/tmp/ag_launch.lock"
  while ! mkdir "$lock_dir" 2>/dev/null; do sleep 0.2; done
  echo "$profile ($$)" > "$lock_dir/owner"

  security list-keychains -d user -s "$profile_kc" "/Library/Keychains/System.keychain"
  security default-keychain -s "$profile_kc"
  open -n -a "Antigravity IDE" --args --user-data-dir="$ag_home/data" ...

  sleep 1.5 # Synchronous blocking wait
  security default-keychain -s "$REAL_HOME/Library/Keychains/login.keychain-db"
  security list-keychains -d user -s "$REAL_HOME/Library/Keychains/login.keychain-db" "/Library/Keychains/System.keychain"
  rm -rf "$lock_dir"
  ```

### Rule 2.5: Hardware Fingerprint & Telemetry Decoupling (Anti-Sybil Defense)
To prevent Google Cloud Code Assist and Clearcut Telemetry from correlating multiple accounts as a Sybil farm:
1. **Mandatory Unique Machine ID & Device ID**:
   Every profile MUST have a cryptographically independent SHA-256 hash in `data/User/globalStorage/storage.json`:
   ```python
   data["telemetry.machineId"] = hashlib.sha256(os.urandom(32) + f"{profile}-{time.time()}".encode()).hexdigest()
   data["telemetry.devDeviceId"] = str(uuid.uuid4())
   ```
   Never clone `storage.json` between profiles without regenerating these values immediately.
2. **Mandatory Telemetry Opt-Out (`telemetryLevel: "off"`)**:
   Every profile's `data/User/settings.json` MUST configure:
   ```json
   "telemetry.telemetryLevel": "off"
   ```
   This prevents Antigravity IDE from transmitting host machine hardware fingerprints, open folder URIs (`backupWorkspaces`), and project paths back to telemetry collection endpoints.
3. **Trajectory Leak Elimination**:
   Never clone `conversation_summaries.db` or `agyhub_summaries_proto.pb`. On profile initialization, ensure `conversation_summaries.db` only references conversation UUIDs residing in that profile's own `.gemini/antigravity/conversations/` directory.
4. **Credential User Scope Decoupling**:
   Every profile MUST have a unique `Library/Application Support/antigravity/credential-user-scope` (`u<16_hex_chars>`). This file is directly read by Google's native `language_server` binary; sharing it across profiles causes Cloud Code completions and telemetry to cross-link accounts.

### Rule 2.6: Rogue Symlink Elimination & Strict State Independence
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

### Rule 2.7: Relative Symlinks Only
- Every symlink in a profile home MUST be relative to its own directory (e.g. `~/antigravity_homes/hau/.android -> ../../.android`, `Library/Caches -> ../../../Library/Caches`). Absolute `/Users/<user>/...` targets are flagged as `absolute_symlinks` and rewritten by `--fix` using an atomic `os.replace`.
- `ag_run` uses `_ag_rel_link` / `_ag_link_ok` so a re-launch also repairs stale absolute links.
- Nested rogue links (`.gemini/antigravity/antigravity -> host`) and missing `login.keychain` / `login.keychain-db` links are also detected and repaired.

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

