#!/usr/bin/env python3
"""
test_audit_account_block.py
Unit tests for audit_account_block.py
"""

import os
import sys
import json
import sqlite3
import tempfile
import unittest

# Add script directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import audit_account_block as auditor


class TestAuditAccountBlock(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.homes_dir = os.path.join(self.test_dir.name, "antigravity_homes")
        os.makedirs(self.homes_dir, exist_ok=True)

    def tearDown(self):
        self.test_dir.cleanup()

    def _create_mock_profile(self, name, machine_id="mid_1", dev_id="dev_1", conv_ids=None, local_convs=None, has_leaked_workspaces=False):
        p_dir = os.path.join(self.homes_dir, name)
        # Storage
        storage_dir = os.path.join(p_dir, "data/User/globalStorage")
        os.makedirs(storage_dir, exist_ok=True)
        storage_data = {
            "telemetry.machineId": machine_id,
            "telemetry.devDeviceId": dev_id,
        }
        if has_leaked_workspaces:
            storage_data["backupWorkspaces"] = {"folders": [{"folderUri": "file:///Users/mock/proj"}]}
            storage_data["profileAssociations"] = {"workspaces": {"file:///Users/mock/proj": "default"}}

        with open(os.path.join(storage_dir, "storage.json"), "w") as f:
            json.dump(storage_data, f)

        # Conversations
        gemini_dir = os.path.join(p_dir, ".gemini/antigravity")
        conv_dir = os.path.join(gemini_dir, "conversations")
        os.makedirs(conv_dir, exist_ok=True)

        if local_convs:
            for cid in local_convs:
                with open(os.path.join(conv_dir, f"{cid}.db"), "w") as f:
                    f.write("mock")

        # SQLite DB
        db_path = os.path.join(gemini_dir, "conversation_summaries.db")
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE conversation_summaries (conversation_id TEXT PRIMARY KEY, title TEXT)")
        if conv_ids:
            for cid in conv_ids:
                cur.execute("INSERT INTO conversation_summaries VALUES (?, ?)", (cid, f"Title {cid}"))
        conn.commit()
        conn.close()

        return p_dir

    def test_audit_detects_duplicate_machine_ids(self):
        # Two profiles with identical machine IDs
        self._create_mock_profile("prof1", machine_id="shared_mid_123")
        self._create_mock_profile("prof2", machine_id="shared_mid_123")
        self._create_mock_profile("prof3", machine_id="unique_mid_456")

        report = auditor.audit_all_profiles(self.homes_dir)
        self.assertIn("shared_mid_123", report["duplicate_machine_ids"])
        self.assertEqual(len(report["duplicate_machine_ids"]["shared_mid_123"]), 2)
        self.assertIn("prof1", report["duplicate_machine_ids"]["shared_mid_123"])
        self.assertIn("prof2", report["duplicate_machine_ids"]["shared_mid_123"])

        # Check vulnerability flags
        self.assertTrue(report["profiles"]["prof1"]["vulnerabilities"]["cloned_machine_id"])
        self.assertTrue(report["profiles"]["prof2"]["vulnerabilities"]["cloned_machine_id"])
        self.assertFalse(report["profiles"]["prof3"]["vulnerabilities"]["cloned_machine_id"])

    def test_audit_detects_stale_trajectory_leaks(self):
        # Profile has 3 conversations in DB but only 1 local file
        self._create_mock_profile(
            "prof_leak",
            machine_id="mid_leak",
            conv_ids=["conv_1", "conv_foreign_2", "conv_foreign_3"],
            local_convs=["conv_1"]
        )

        report = auditor.audit_all_profiles(self.homes_dir)
        prof_data = report["profiles"]["prof_leak"]
        self.assertEqual(prof_data["stale_conversation_count"], 2)
        self.assertTrue(prof_data["vulnerabilities"]["stale_trajectories"])

    def test_audit_detects_workspace_path_leaks(self):
        self._create_mock_profile("prof_clean", has_leaked_workspaces=False)
        self._create_mock_profile("prof_leaky", has_leaked_workspaces=True)

        report = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report["profiles"]["prof_clean"]["vulnerabilities"]["leaked_workspaces"])
        self.assertTrue(report["profiles"]["prof_leaky"]["vulnerabilities"]["leaked_workspaces"])

    def test_audit_detects_keychain_leak_and_identity_bleed(self):
        p_dir = self._create_mock_profile("prof_keychain_leak", machine_id="mid_kc")
        # Add leaked plist
        plist_dir = os.path.join(p_dir, "Library/Preferences")
        os.makedirs(plist_dir, exist_ok=True)
        with open(os.path.join(plist_dir, "com.apple.security.plist"), "w") as f:
            f.write('<key>DbName</key><string>/Users/danhdueexoictif/Library/Keychains/login.keychain</string>')

        # Add identity bleed in state.vscdb
        vscdb_dir = os.path.join(p_dir, "data/User/globalStorage")
        vscdb_path = os.path.join(vscdb_dir, "state.vscdb")
        conn = sqlite3.connect(vscdb_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
        cur.execute("INSERT INTO ItemTable VALUES ('google.google-antigravity', '{\"antigravity-storage\": {\"agy.onboarding.lastLoginUsername\": \"danhdue@gmail.com\"}}')")
        cur.execute("INSERT INTO ItemTable VALUES ('antigravityUnifiedStateSync.oauthToken', '{\"state\": \"signedOut\"}')")
        conn.commit()
        conn.close()

        report = auditor.audit_all_profiles(self.homes_dir)
        prof_data = report["profiles"]["prof_keychain_leak"]
        self.assertTrue(prof_data["vulnerabilities"]["keychain_leak"])
        self.assertTrue(prof_data["vulnerabilities"]["identity_bleed"])
        self.assertEqual(prof_data["risk_level"], "HIGH")

    def test_remediation_fixes_all_vulnerabilities(self):
        # Create 2 leaky, cloned profiles with keychain leaks
        p1 = self._create_mock_profile("p1", machine_id="shared", dev_id="dev_shared", conv_ids=["c1", "c2"], local_convs=["c1"], has_leaked_workspaces=True)
        p2 = self._create_mock_profile("p2", machine_id="shared", dev_id="dev_shared", conv_ids=["c1", "c2"], local_convs=["c2"], has_leaked_workspaces=True)

        for p in [p1, p2]:
            plist_dir = os.path.join(p, "Library/Preferences")
            os.makedirs(plist_dir, exist_ok=True)
            with open(os.path.join(plist_dir, "com.apple.security.plist"), "w") as f:
                f.write('<key>DbName</key><string>/Users/danhdueexoictif/Library/Keychains/login.keychain</string>')

        # Before remediation: audit should fail clean check
        report_before = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report_before["is_healthy"])

        # Run remediation
        auditor.remediate_all_profiles(self.homes_dir)

        # After remediation: audit should pass clean check
        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertTrue(report_after["is_healthy"])
        self.assertEqual(len(report_after["duplicate_machine_ids"]), 0)
        self.assertEqual(report_after["profiles"]["p1"]["stale_conversation_count"], 0)
        self.assertEqual(report_after["profiles"]["p2"]["stale_conversation_count"], 0)
        self.assertFalse(report_after["profiles"]["p1"]["vulnerabilities"]["leaked_workspaces"])
        self.assertFalse(report_after["profiles"]["p2"]["vulnerabilities"]["leaked_workspaces"])
        self.assertFalse(report_after["profiles"]["p1"]["vulnerabilities"]["keychain_leak"])
        self.assertFalse(report_after["profiles"]["p2"]["vulnerabilities"]["keychain_leak"])
        self.assertNotEqual(
            report_after["profiles"]["p1"]["machine_id"],
            report_after["profiles"]["p2"]["machine_id"]
        )


if __name__ == "__main__":
    unittest.main()

