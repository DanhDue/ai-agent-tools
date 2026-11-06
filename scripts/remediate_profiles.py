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

        # 2. Sanitize conversation_summaries.db
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

    print(f"\n=== SUMMARY ===")
    print(f"Total storage.json files updated: {remediated_storage} (All IDs unique: {len(seen_machine_ids)} unique machine IDs)")
    print(f"Total stale cloned conversation records purged: {remediated_convs}")
    print("Remediation complete successfully.")

if __name__ == "__main__":
    remediate()
