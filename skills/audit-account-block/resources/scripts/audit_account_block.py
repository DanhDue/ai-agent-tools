#!/usr/bin/env python3
"""
audit_account_block.py
Comprehensive Security & Anti-Abuse Audit for Antigravity Profiles.
Detects, scores, and remediates vulnerabilities leading to account blocks / 403 Terms of Service suspensions.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
import uuid

# Terminal ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"


CANONICAL_SECURITY_PLIST = """<?xml version="1.0" encoding="UTF-8"?>
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


def get_default_homes_dir() -> str:
    current = os.path.expanduser("~")
    if "antigravity_homes" in current:
        real_home = current.split("/antigravity_homes")[0]
    else:
        real_home = current
    return f"{real_home}/antigravity_homes"


def audit_profile(p_dir: str, profile_name: str, duplicate_mid_map: dict[str, list[str]]) -> dict:
    storage_path = os.path.join(p_dir, "data/User/globalStorage/storage.json")
    db_path = os.path.join(p_dir, ".gemini/antigravity/conversation_summaries.db")
    conv_dir = os.path.join(p_dir, ".gemini/antigravity/conversations")
    tos_path = os.path.join(p_dir, ".gemini/antigravity/tos_disabled.json")

    # 1. Inspect Storage & Machine ID
    machine_id = "MISSING"
    dev_device_id = "MISSING"
    has_leaked_workspaces = False

    if os.path.exists(storage_path):
        try:
            with open(storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                machine_id = data.get("telemetry.machineId", "MISSING")
                dev_device_id = data.get("telemetry.devDeviceId", "MISSING")

                # Check leaked folders
                folders = data.get("backupWorkspaces", {}).get("folders", [])
                workspaces = data.get("profileAssociations", {}).get("workspaces", {})
                if folders or workspaces:
                    has_leaked_workspaces = True
        except Exception:
            pass

    # 2. Inspect Conversation Summaries & Trajectory Leaks
    total_convs_in_db = 0
    stale_conv_count = 0
    local_conv_count = 0

    local_convs = set()
    if os.path.exists(conv_dir):
        try:
            for f in os.listdir(conv_dir):
                if f.endswith(".db"):
                    local_convs.add(f[:-3])
        except Exception:
            pass
    local_conv_count = len(local_convs)

    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            total_convs_in_db = c.execute("SELECT count(*) FROM conversation_summaries").fetchone()[0]
            if profile_name != "danhdue":
                rows = c.execute("SELECT conversation_id FROM conversation_summaries").fetchall()
                stale_conv_count = sum(1 for r in rows if r[0] not in local_convs)
            conn.close()
        except Exception:
            pass

    # 3. Inspect Block Status
    is_tos_disabled = os.path.exists(tos_path)
    tos_details = None
    if is_tos_disabled:
        try:
            with open(tos_path, "r", encoding="utf-8") as f:
                tos_details = json.load(f)
        except Exception:
            pass

    # 4. Inspect Keychain & Identity Isolation
    plist_path = os.path.join(p_dir, "Library/Preferences/com.apple.security.plist")
    has_keychain_leak = False
    has_identity_bleed = False

    if profile_name != "danhdue":
        # Check com.apple.security.plist for host path leaks
        if os.path.exists(plist_path):
            try:
                with open(plist_path, "r", encoding="utf-8", errors="ignore") as f:
                    cnt = f.read()
                    if "/Library/Keychains/login.keychain" in cnt and "~/Library/Keychains" not in cnt:
                        has_keychain_leak = True
                    elif "DefaultKeychain" in cnt and "login.keychain" in cnt:
                        has_keychain_leak = True
            except Exception:
                pass

        # Check state.vscdb identity parity
        vscdb_path = os.path.join(p_dir, "data/User/globalStorage/state.vscdb")
        if os.path.exists(vscdb_path):
            try:
                conn = sqlite3.connect(vscdb_path)
                c = conn.cursor()
                c.execute("SELECT value FROM ItemTable WHERE key='google.google-antigravity'")
                row = c.fetchone()
                if row:
                    v_data = json.loads(row[0])
                    last_user = v_data.get("antigravity-storage", {}).get("agy.onboarding.lastLoginUsername", "")
                    if last_user == "danhdue@gmail.com":
                        has_identity_bleed = True
                c.execute("SELECT value FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'")
                row2 = c.fetchone()
                if row2 and "signedOut" in row2[0]:
                    has_identity_bleed = True
                conn.close()
            except Exception:
                pass

    # Evaluate Vulnerabilities
    is_cloned_mid = len(duplicate_mid_map.get(machine_id, [])) > 1
    has_missing_mid = machine_id in ("MISSING", "")
    has_stale_trajectories = stale_conv_count > 0

    # Risk Level Calculation
    if is_tos_disabled:
        risk_level = "BLOCKED"
    elif is_cloned_mid and has_stale_trajectories:
        risk_level = "CRITICAL"
    elif is_cloned_mid or has_stale_trajectories or has_missing_mid or has_keychain_leak or has_identity_bleed:
        risk_level = "HIGH"
    elif has_leaked_workspaces:
        risk_level = "MEDIUM"
    else:
        risk_level = "CLEAN"

    return {
        "profile": profile_name,
        "path": p_dir,
        "risk_level": risk_level,
        "machine_id": machine_id,
        "dev_device_id": dev_device_id,
        "total_convs_in_db": total_convs_in_db,
        "local_conv_count": local_conv_count,
        "stale_conversation_count": stale_conv_count,
        "is_tos_disabled": is_tos_disabled,
        "tos_details": tos_details,
        "vulnerabilities": {
            "cloned_machine_id": is_cloned_mid,
            "missing_machine_id": has_missing_mid,
            "stale_trajectories": has_stale_trajectories,
            "leaked_workspaces": has_leaked_workspaces,
            "keychain_leak": has_keychain_leak,
            "identity_bleed": has_identity_bleed,
            "tos_suspended": is_tos_disabled,
        },
    }


def audit_all_profiles(homes_dir: str | None = None) -> dict:
    if not homes_dir:
        homes_dir = get_default_homes_dir()

    profile_paths = sorted(glob.glob(f"{homes_dir}/*"))
    profiles = [p for p in profile_paths if os.path.isdir(p)]

    # Pass 1: Collect Machine IDs to detect duplicates
    mid_to_profiles: dict[str, list[str]] = {}
    for p_path in profiles:
        p_name = os.path.basename(p_path)
        storage_path = os.path.join(p_path, "data/User/globalStorage/storage.json")
        if os.path.exists(storage_path):
            try:
                with open(storage_path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    mid = d.get("telemetry.machineId", "MISSING")
                    if mid and mid != "MISSING":
                        mid_to_profiles.setdefault(mid, []).append(p_name)
            except Exception:
                pass

    duplicate_mids = {mid: plist for mid, plist in mid_to_profiles.items() if len(plist) > 1}

    # Pass 2: Audit each profile
    profile_results = {}
    blocked_count = 0
    critical_count = 0
    high_count = 0
    medium_count = 0
    clean_count = 0

    for p_path in profiles:
        p_name = os.path.basename(p_path)
        res = audit_profile(p_path, p_name, duplicate_mids)
        profile_results[p_name] = res

        lvl = res["risk_level"]
        if lvl == "BLOCKED":
            blocked_count += 1
        elif lvl == "CRITICAL":
            critical_count += 1
        elif lvl == "HIGH":
            high_count += 1
        elif lvl == "MEDIUM":
            medium_count += 1
        elif lvl == "CLEAN":
            clean_count += 1

    is_healthy = (critical_count == 0 and high_count == 0 and len(duplicate_mids) == 0)

    return {
        "timestamp": time.time(),
        "homes_dir": homes_dir,
        "total_profiles": len(profiles),
        "is_healthy": is_healthy,
        "duplicate_machine_ids": duplicate_mids,
        "summary": {
            "blocked": blocked_count,
            "critical": critical_count,
            "high": high_count,
            "medium": medium_count,
            "clean": clean_count,
        },
        "profiles": profile_results,
    }


def remediate_single_profile(p_path: str, profile_name: str, seen_machine_ids: set[str], timestamp: str) -> dict:
    storage_dir = os.path.join(p_path, "data/User/globalStorage")
    storage_path = os.path.join(storage_dir, "storage.json")
    os.makedirs(storage_dir, exist_ok=True)

    data = {}
    if os.path.exists(storage_path):
        try:
            shutil.copy2(storage_path, f"{storage_path}.bak.{timestamp}")
            with open(storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    while True:
        new_mid = hashlib.sha256(os.urandom(32) + f"{profile_name}-{time.time()}".encode()).hexdigest()
        if new_mid not in seen_machine_ids:
            seen_machine_ids.add(new_mid)
            break

    new_dev_id = str(uuid.uuid4())
    data["telemetry.machineId"] = new_mid
    data["telemetry.devDeviceId"] = new_dev_id

    if "backupWorkspaces" in data:
        data["backupWorkspaces"]["folders"] = []
        data["backupWorkspaces"]["workspaces"] = []
    if "profileAssociations" in data:
        data["profileAssociations"]["workspaces"] = {}

    tmp_path = f"{storage_path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_path, storage_path)

    # Sanitize SQLite
    db_path = os.path.join(p_path, ".gemini/antigravity/conversation_summaries.db")
    conv_dir = os.path.join(p_path, ".gemini/antigravity/conversations")
    purged_count = 0

    if os.path.exists(db_path) and profile_name != "danhdue":
        try:
            local_convs = set()
            if os.path.exists(conv_dir):
                for f in os.listdir(conv_dir):
                    if f.endswith(".db"):
                        local_convs.add(f[:-3])

            shutil.copy2(db_path, f"{db_path}.bak.{timestamp}")
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            before_count = c.execute("SELECT count(*) FROM conversation_summaries").fetchone()[0]

            if local_convs:
                placeholders = ",".join("?" for _ in local_convs)
                c.execute(f"DELETE FROM conversation_summaries WHERE conversation_id NOT IN ({placeholders})", list(local_convs))
            else:
                c.execute("DELETE FROM conversation_summaries")

            after_count = c.execute("SELECT count(*) FROM conversation_summaries").fetchone()[0]
            purged_count = before_count - after_count
            conn.commit()
            c.execute("VACUUM")
            conn.close()
        except Exception:
            pass

    # Sanitize agyhub_summaries_proto.pb (prevents agy from restoring foreign cloned summaries on startup)
    pb_path = os.path.join(p_path, ".gemini/antigravity/agyhub_summaries_proto.pb")
    if os.path.exists(pb_path) and profile_name != "danhdue":
        try:
            shutil.copy2(pb_path, f"{pb_path}.bak.{timestamp}")
            os.remove(pb_path)
        except Exception:
            pass

    # Sanitize com.apple.security.plist (Keychain isolation)
    plist_dir = os.path.join(p_path, "Library/Preferences")
    plist_path = os.path.join(plist_dir, "com.apple.security.plist")
    repaired_plist = False
    if profile_name != "danhdue":
        os.makedirs(plist_dir, exist_ok=True)
        need_plist_repair = False
        if not os.path.exists(plist_path):
            need_plist_repair = True
        else:
            try:
                with open(plist_path, "r", encoding="utf-8", errors="ignore") as f:
                    cnt = f.read()
                    if "/Library/Keychains/login.keychain" in cnt and "~/Library/Keychains" not in cnt:
                        need_plist_repair = True
                    elif "DefaultKeychain" in cnt and "login.keychain" in cnt:
                        need_plist_repair = True
            except Exception:
                need_plist_repair = True

        if need_plist_repair:
            if os.path.exists(plist_path):
                shutil.copy2(plist_path, f"{plist_path}.bak.{timestamp}")
            with open(plist_path, "w", encoding="utf-8") as f:
                f.write(CANONICAL_SECURITY_PLIST)
            repaired_plist = True

    # Sanitize state.vscdb identity parity
    vscdb_path = os.path.join(p_path, "data/User/globalStorage/state.vscdb")
    repaired_vscdb = False
    if os.path.exists(vscdb_path) and profile_name != "danhdue":
        try:
            conn = sqlite3.connect(vscdb_path)
            c = conn.cursor()
            c.execute("DELETE FROM ItemTable WHERE key='antigravityUnifiedStateSync.oauthToken'")
            c.execute("SELECT value FROM ItemTable WHERE key='google.google-antigravity'")
            row = c.fetchone()
            if row:
                vd = json.loads(row[0])
                st = vd.get("antigravity-storage", {})
                if st.get("agy.onboarding.lastLoginUsername") == "danhdue@gmail.com":
                    token_file = os.path.join(p_path, ".gemini/jetski-standalone-oauth-token")
                    actual_email = None
                    if os.path.exists(token_file):
                        try:
                            with open(token_file) as tf:
                                actual_email = json.load(tf).get("id_token_email")
                        except Exception:
                            pass
                    if actual_email:
                        st["agy.onboarding.lastLoginUsername"] = actual_email
                        vd["antigravity-storage"] = st
                        c.execute("UPDATE ItemTable SET value=? WHERE key='google.google-antigravity'", (json.dumps(vd),))
                        repaired_vscdb = True
            conn.commit()
            conn.close()
        except Exception:
            pass

    return {
        "profile": profile_name,
        "new_machine_id": new_mid,
        "new_dev_id": new_dev_id,
        "purged_trajectories": purged_count,
        "repaired_plist": repaired_plist,
        "repaired_vscdb": repaired_vscdb,
    }


def remediate_all_profiles(homes_dir: str | None = None, target: str | None = None) -> list[dict]:
    if not homes_dir:
        homes_dir = get_default_homes_dir()

    profile_paths = sorted(glob.glob(f"{homes_dir}/*"))
    profiles = [p for p in profile_paths if os.path.isdir(p)]

    if target:
        profiles = [p for p in profiles if os.path.basename(p) == target]

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    seen_machine_ids: set[str] = set()
    results = []

    for p_path in profiles:
        p_name = os.path.basename(p_path)
        res = remediate_single_profile(p_path, p_name, seen_machine_ids, timestamp)
        results.append(res)

    return results


def print_audit_report(report: dict):
    print(f"\n{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║                    ANTIGRAVITY ACCOUNT BLOCK & ANTI-ABUSE AUDIT REPORT                           ║{RESET}")
    print(f"{BOLD}{CYAN}╚══════════════════════════════════════════════════════════════════════════════════════════════════╝{RESET}")
    print(f"Directory: {report['homes_dir']}")
    print(f"Total Profiles: {report['total_profiles']} | Overall Status: {'✅ HEALTHY' if report['is_healthy'] else '⚠️ VULNERABILITIES DETECTED'}\n")

    summary = report["summary"]
    print(f"{BOLD}Summary:{RESET} "
          f"{RED}[BLOCKED: {summary['blocked']}]{RESET}  "
          f"{RED}[CRITICAL: {summary['critical']}]{RESET}  "
          f"{YELLOW}[HIGH: {summary['high']}]{RESET}  "
          f"{BLUE}[MEDIUM: {summary['medium']}]{RESET}  "
          f"{GREEN}[CLEAN: {summary['clean']}]{RESET}\n")

    if report["duplicate_machine_ids"]:
        print(f"{BOLD}{RED}🚨 DUPLICATE MACHINE IDs DETECTED (Sybil / Farming Risk):{RESET}")
        for mid, plist in report["duplicate_machine_ids"].items():
            print(f"  • {YELLOW}{mid[:20]}...{RESET} shared by {len(plist)} profiles: {plist}")
        print()

    # Table format
    header = f"{'PROFILE':<20} | {'RISK':<10} | {'MACHINE ID':<18} | {'TRAJECTORY LEAK':<18} | {'STATUS / FINDINGS'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * 100)

    for p_name, data in report["profiles"].items():
        risk = data["risk_level"]
        if risk == "BLOCKED":
            risk_badge = f"{BG_RED}{WHITE} BLOCKED  {RESET}"
        elif risk == "CRITICAL":
            risk_badge = f"{RED}{BOLD} CRITICAL {RESET}"
        elif risk == "HIGH":
            risk_badge = f"{YELLOW}{BOLD} HIGH     {RESET}"
        elif risk == "MEDIUM":
            risk_badge = f"{BLUE} MEDIUM   {RESET}"
        else:
            risk_badge = f"{GREEN} CLEAN    {RESET}"

        mid_short = data["machine_id"][:14] + "..." if len(data["machine_id"]) > 14 else data["machine_id"]
        stale_txt = f"{RED}{data['stale_conversation_count']} stale items{RESET}" if data["stale_conversation_count"] > 0 else f"{GREEN}0 (Clean){RESET}"

        findings = []
        if data["is_tos_disabled"]:
            findings.append("403 ToS Disabled (Appeal required)")
        if data["vulnerabilities"]["cloned_machine_id"]:
            findings.append("Cloned Machine ID")
        if data["vulnerabilities"]["stale_trajectories"]:
            findings.append(f"{data['stale_conversation_count']} foreign trajectories")
        if data["vulnerabilities"]["leaked_workspaces"]:
            findings.append("Leaked workspace paths")
        if data["vulnerabilities"].get("keychain_leak"):
            findings.append("Keychain host path leak")
        if data["vulnerabilities"].get("identity_bleed"):
            findings.append("Identity bleed (state.vscdb points to host)")
        if not findings:
            findings.append("No vulnerabilities found")

        findings_str = "; ".join(findings)
        print(f"{p_name:<20} | {risk_badge} | {mid_short:<18} | {stale_txt:<27} | {findings_str}")

    print("-" * 100)
    if not report["is_healthy"]:
        print(f"\n{BOLD}{YELLOW}Recommendation:{RESET} Run {CYAN}audit-account-block --fix{RESET} to decouple Machine IDs and purge foreign trajectory summaries.")
    else:
        print(f"\n{BOLD}{GREEN}✓ All active profiles have decoupled hardware fingerprints and clean databases.{RESET}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Antigravity Account Block & Anti-Abuse Audit Tool")
    parser.add_argument("--audit", action="store_true", default=True, help="Run audit inspection (default)")
    parser.add_argument("--fix", action="store_true", help="Automatically remediate detected vulnerabilities")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    parser.add_argument("--target", type=str, default=None, help="Target a specific profile")
    parser.add_argument("--homes-dir", type=str, default=None, help="Custom antigravity_homes directory")

    args = parser.parse_args()

    if args.fix:
        remed_results = remediate_all_profiles(args.homes_dir, args.target)
        if args.json:
            print(json.dumps({"success": True, "remediated": remed_results}, indent=2))
        else:
            print(f"{GREEN}{BOLD}✓ Remediation complete for {len(remed_results)} profiles:{RESET}")
            for r in remed_results:
                print(f"  • {r['profile']}: new mid={r['new_machine_id'][:16]}..., purged {r['purged_trajectories']} trajectories")
        return 0

    # Default: Audit mode
    report = audit_all_profiles(args.homes_dir)
    if args.target and args.target in report["profiles"]:
        report["profiles"] = {args.target: report["profiles"][args.target]}

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_audit_report(report)

    return 0 if report["is_healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
