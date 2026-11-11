#!/usr/bin/env python3
"""
remediate_profiles.py
Sanitize and decouple Antigravity profiles:
1. Generates unique, cryptographically random telemetry.machineId and telemetry.devDeviceId for every profile.
2. Purges stale cloned conversation summaries to eliminate 403 Cross-Account Permission Denied errors.
3. Cleans up leaked workspace file paths in storage.json.
"""

import os
import glob
import json
import uuid
import time
import shutil
import sqlite3
import hashlib

current_home = os.path.expanduser("~")
if "antigravity_homes" in current_home:
    REAL_HOME = current_home.split("/antigravity_homes")[0]
else:
    REAL_HOME = current_home
HOMES_DIR = f"{REAL_HOME}/antigravity_homes"

def remediate():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    homes = sorted(glob.glob(f"{HOMES_DIR}/*"))
    
    print(f"=== ANTIGRAVITY PROFILE REMEDIATION TOOL ===")
    print(f"Found {len(homes)} profiles in {HOMES_DIR}")
    print(f"Timestamp: {timestamp}\n")

    remediated_storage = 0
    remediated_convs = 0
    seen_machine_ids = set()

    for h in homes:
        profile = os.path.basename(h)
        print(f"[{profile}] Processing...")

        # 1. Remediate storage.json (Machine ID & Device ID & Leaked Paths)
        storage_dir = os.path.join(h, "data/User/globalStorage")
        storage_path = os.path.join(storage_dir, "storage.json")
        os.makedirs(storage_dir, exist_ok=True)

        data = {}
        if os.path.exists(storage_path):
            try:
                # Backup
                backup_path = f"{storage_path}.bak.{timestamp}"
                shutil.copy2(storage_path, backup_path)
                with open(storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                print(f"  [WARN] Error reading storage.json: {e}")
                data = {}

        # Generate unique 64-char SHA-256 machine ID
        while True:
            new_mid = hashlib.sha256(os.urandom(32) + f"{profile}-{time.time()}".encode()).hexdigest()
            if new_mid not in seen_machine_ids:
                seen_machine_ids.add(new_mid)
                break

        new_dev_id = str(uuid.uuid4())
        
        data["telemetry.machineId"] = new_mid
        data["telemetry.devDeviceId"] = new_dev_id

        # Clean up absolute file paths to prevent cross-account identity leak
        if "backupWorkspaces" in data:
            data["backupWorkspaces"]["folders"] = []
            data["backupWorkspaces"]["workspaces"] = []
        if "profileAssociations" in data:
            data["profileAssociations"]["workspaces"] = {}

        # Atomic write
        tmp_path = f"{storage_path}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, storage_path)
        print(f"  ✓ Machine ID: {new_mid[:16]}... | Device ID: {new_dev_id}")
        remediated_storage += 1

        # 2. Purge rogue symlinks in .gemini/ and .antigravity/ (ensure independent directories)
        for parent in [".gemini", ".antigravity"]:
            for rogue in ["antigravity", "antigravity-cli", "antigravity-ide", "antigravity-browser-profile", "antigravity-backup"]:
                target_path = os.path.join(h, parent, rogue)
                if os.path.islink(target_path):
                    os.unlink(target_path)
                    os.makedirs(target_path, exist_ok=True)
                    print(f"  ✓ Purged rogue symlink: {parent}/{rogue} -> converted to directory")

        # 3. Sanitize conversation_summaries.db
        db_path = os.path.join(h, ".gemini/antigravity/conversation_summaries.db")
        conv_dir = os.path.join(h, ".gemini/antigravity/conversations")

        if os.path.exists(db_path) and profile != "danhdue":
            try:
                local_convs = set()
                if os.path.exists(conv_dir):
                    for f in os.listdir(conv_dir):
                        if f.endswith(".db"):
                            local_convs.add(f[:-3])

                # Backup DB
                db_bak = f"{db_path}.bak.{timestamp}"
                shutil.copy2(db_path, db_bak)

                conn = sqlite3.connect(db_path)
                c = conn.cursor()
                before_count = c.execute("SELECT count(*) FROM conversation_summaries").fetchone()[0]

                if local_convs:
                    placeholders = ",".join("?" for _ in local_convs)
                    c.execute(f"DELETE FROM conversation_summaries WHERE conversation_id NOT IN ({placeholders})", list(local_convs))
                else:
                    c.execute("DELETE FROM conversation_summaries")

                after_count = c.execute("SELECT count(*) FROM conversation_summaries").fetchone()[0]
                deleted = before_count - after_count
                conn.commit()
                c.execute("VACUUM")
                conn.close()

                if deleted > 0:
                    print(f"  ✓ Purged {deleted} stale cloned conversation summaries (Remaining: {after_count})")
                    remediated_convs += deleted
                else:
                    print(f"  ✓ DB Clean (Entries: {after_count})")
            except Exception as e:
                print(f"  [WARN] Error cleaning conversation_summaries.db: {e}")

        # 3.1 Sanitize com.apple.security.plist (Keychain isolation)
        plist_dir = os.path.join(h, "Library/Preferences")
        plist_path = os.path.join(plist_dir, "com.apple.security.plist")
        if profile != "danhdue":
            os.makedirs(plist_dir, exist_ok=True)
            need_repair = False
            if not os.path.exists(plist_path):
                need_repair = True
            else:
                try:
                    with open(plist_path, "r", encoding="utf-8", errors="ignore") as pf:
                        pcnt = pf.read()
                        if "/Library/Keychains/login.keychain" in pcnt and "~/Library/Keychains" not in pcnt:
                            need_repair = True
                        elif "DefaultKeychain" in pcnt:
                            need_repair = True
                except Exception:
                    need_repair = True
            if need_repair:
                canonical_plist = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>DLDBSearchList</key>
\t<array>
\t\t<dict>
\t\t\t<key>DbName</key>
\t\t\t<string>~/Library/Keychains/login.keychain</string>
\t\t\t<key>GUID</key>
\t\t\t<string>{87191ca3-0fc9-11d4-849a-000502b52122}</string>
\t\t\t<key>SubserviceType</key>
\t\t\t<integer>6</integer>
\t\t</dict>
\t\t<dict>
\t\t\t<key>DbName</key>
\t\t\t<string>/Library/Keychains/System.keychain</string>
\t\t\t<key>GUID</key>
\t\t\t<string>{87191ca3-0fc9-11d4-849a-000502b52122}</string>
\t\t\t<key>SubserviceType</key>
\t\t\t<integer>6</integer>
\t\t</dict>
\t</array>
</dict>
</plist>
"""
                with open(plist_path, "w", encoding="utf-8") as pf:
                    pf.write(canonical_plist)
                print(f"  ✓ Sanitized com.apple.security.plist (Keychain isolation enforced)")

        # 4. Enforce state.vscdb identity parity with Keychain token
        vscdb_path = os.path.join(h, "data/User/globalStorage/state.vscdb")
        kc_path = os.path.join(h, "Library/Keychains", f"{profile}.keychain-db")
        if os.path.isfile(vscdb_path) and os.path.isfile(kc_path) and profile != "danhdue":
            try:
                import base64, subprocess
                # Terminate any stale resident IDE / agy processes for this profile
                # to prevent Electron RAM from overwriting SQLite changes on exit
                pids_proc = subprocess.run(["pgrep", "-f", f"antigravity_homes/{profile}"], capture_output=True, text=True)
                pids = [p.strip() for p in pids_proc.stdout.splitlines() if p.strip()]
                if pids:
                    subprocess.run(["pkill", "-9", "-f", f"antigravity_homes/{profile}"], capture_output=True)
                    print(f"  ✓ Terminated {len(pids)} stale resident processes for {profile} (PIDs: {', '.join(pids)})")

                subprocess.run(["security", "unlock-keychain", "-p", "H@No!a@12345", kc_path], capture_output=True)
                res = subprocess.run(["security", "find-generic-password", "-s", "gemini", "-a", "antigravity", "-g", kc_path], capture_output=True, text=True)
                raw_err = res.stderr or ""
                kc_email = None
                if 'password: "go-keyring-base64:' in raw_err:
                    b64 = raw_err.split('password: "go-keyring-base64:')[1].split('"')[0]
                    tdata = json.loads(base64.b64decode(b64).decode("utf-8"))
                    kc_email = tdata.get("id_token_email")

                if kc_email:
                    conn = sqlite3.connect(vscdb_path)
                    c = conn.cursor()
                    c.execute("SELECT value FROM ItemTable WHERE key='google.google-antigravity'")
                    row = c.fetchone()
                    if row:
                        d = json.loads(row[0])
                        st = d.get("antigravity-storage", {})
                        cur_email = st.get("agy.onboarding.lastLoginUsername")
                        if cur_email != kc_email:
                            st["agy.onboarding.lastLoginUsername"] = kc_email
                            d["antigravity-storage"] = st
                            c.execute("UPDATE ItemTable SET value=? WHERE key='google.google-antigravity'", (json.dumps(d),))
                            print(f"  ✓ Fixed state.vscdb username: {cur_email} -> {kc_email}")
                    # Remove stale signedOut flag if present
                    c.execute("DELETE FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'")
                    conn.commit()
                    conn.close()
            except Exception as e:
                print(f"  [WARN] Error enforcing state.vscdb identity parity: {e}")

    print(f"\n=== SUMMARY ===")
    print(f"Total storage.json files updated: {remediated_storage} (All IDs unique: {len(seen_machine_ids)} unique machine IDs)")
    print(f"Total stale cloned conversation records purged: {remediated_convs}")
    print("Remediation complete successfully.")

if __name__ == "__main__":
    remediate()
