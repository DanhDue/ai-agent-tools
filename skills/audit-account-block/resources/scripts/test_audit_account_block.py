#!/usr/bin/env python3
"""
test_audit_account_block.py
Unit tests for audit_account_block.py
"""

import base64
import os
import sys
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

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

    def test_audit_ignores_non_profile_directories(self):
        # Create a valid profile
        self._create_mock_profile("valid_prof", machine_id="mid_valid")

        # Create a symlink (e.g. AllProjects -> temp dir)
        target_dir = os.path.join(self.test_dir.name, "target_projects")
        os.makedirs(target_dir, exist_ok=True)
        symlink_path = os.path.join(self.homes_dir, "AllProjects")
        os.symlink(target_dir, symlink_path)

        # Create hidden directory
        hidden_dir = os.path.join(self.homes_dir, ".gemini")
        os.makedirs(hidden_dir, exist_ok=True)

        # Create reserved system directory
        library_dir = os.path.join(self.homes_dir, "Library")
        os.makedirs(library_dir, exist_ok=True)

        report = auditor.audit_all_profiles(self.homes_dir)
        self.assertEqual(report["total_profiles"], 1)
        self.assertIn("valid_prof", report["profiles"])
        self.assertNotIn("AllProjects", report["profiles"])
        self.assertNotIn(".gemini", report["profiles"])
        self.assertNotIn("Library", report["profiles"])

    def test_audit_detects_proto_summaries_and_missing_terminal_env(self):
        p_dir = self._create_mock_profile("prof_proto", machine_id="mid_proto")
        # Add stale proto summaries file
        pb_path = os.path.join(p_dir, ".gemini/antigravity/agyhub_summaries_proto.pb")
        with open(pb_path, "w") as f:
            f.write("mock_proto_data")

        # Create settings.json without AGY_PROFILE
        settings_dir = os.path.join(p_dir, "data/User")
        os.makedirs(settings_dir, exist_ok=True)
        settings_path = os.path.join(settings_dir, "settings.json")
        with open(settings_path, "w") as f:
            json.dump({
                "terminal.integrated.env.osx": {
                    "HOME": "/Users/mock",
                    "USER": "mock"
                }
            }, f)

        report_before = auditor.audit_all_profiles(self.homes_dir)
        prof_data = report_before["profiles"]["prof_proto"]
        self.assertTrue(prof_data["vulnerabilities"]["stale_proto_summaries"])
        self.assertTrue(prof_data["vulnerabilities"]["missing_terminal_profile_env"])
        self.assertEqual(prof_data["risk_level"], "HIGH")

        # Remediate
        auditor.remediate_all_profiles(self.homes_dir)

        # Verify proto removed
        self.assertFalse(os.path.exists(pb_path))

        # Verify settings repaired with AGY_PROFILE
        with open(settings_path) as f:
            repaired_settings = json.load(f)
            self.assertEqual(
                repaired_settings.get("terminal.integrated.env.osx", {}).get("AGY_PROFILE"),
                "prof_proto"
            )

        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report_after["profiles"]["prof_proto"]["vulnerabilities"]["stale_proto_summaries"])
        self.assertFalse(report_after["profiles"]["prof_proto"]["vulnerabilities"]["missing_terminal_profile_env"])

    def test_audit_detects_and_remediates_credential_user_scopes(self):
        # Create 2 profiles with shared user scope
        p1 = self._create_mock_profile("prof_scope_1", machine_id="mid_s1")
        p2 = self._create_mock_profile("prof_scope_2", machine_id="mid_s2")
        # Create 1 profile with missing user scope
        p3 = self._create_mock_profile("prof_scope_3", machine_id="mid_s3")

        shared_scope = "u1122334455667788"
        for p in [p1, p2]:
            s_dir = os.path.join(p, "Library/Application Support/antigravity")
            os.makedirs(s_dir, exist_ok=True)
            with open(os.path.join(s_dir, "credential-user-scope"), "w") as f:
                f.write(shared_scope)

        report_before = auditor.audit_all_profiles(self.homes_dir)
        self.assertIn(shared_scope, report_before["duplicate_user_scopes"])
        self.assertTrue(report_before["profiles"]["prof_scope_1"]["vulnerabilities"]["cloned_user_scope"])
        self.assertTrue(report_before["profiles"]["prof_scope_2"]["vulnerabilities"]["cloned_user_scope"])
        self.assertTrue(report_before["profiles"]["prof_scope_3"]["vulnerabilities"]["missing_user_scope"])
        self.assertFalse(report_before["is_healthy"])

        # Remediate
        auditor.remediate_all_profiles(self.homes_dir)

        # Audit after remediation
        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertEqual(len(report_after["duplicate_user_scopes"]), 0)
        self.assertFalse(report_after["profiles"]["prof_scope_1"]["vulnerabilities"]["cloned_user_scope"])
        self.assertFalse(report_after["profiles"]["prof_scope_2"]["vulnerabilities"]["cloned_user_scope"])
        self.assertFalse(report_after["profiles"]["prof_scope_3"]["vulnerabilities"]["missing_user_scope"])

        scope1 = report_after["profiles"]["prof_scope_1"]["user_scope"]
        scope2 = report_after["profiles"]["prof_scope_2"]["user_scope"]
        scope3 = report_after["profiles"]["prof_scope_3"]["user_scope"]
        self.assertTrue(scope1.startswith("u"))
        self.assertTrue(scope2.startswith("u"))
        self.assertTrue(scope3.startswith("u"))
        self.assertNotEqual(scope1, scope2)
        self.assertNotEqual(scope1, scope3)
        self.assertNotEqual(scope2, scope3)

    def test_audit_detects_and_remediates_nested_rogue_symlinks(self):
        p_dir = self._create_mock_profile("prof_rogue", machine_id="mid_r1")
        ag_dir = os.path.join(p_dir, ".gemini/antigravity")
        os.makedirs(os.path.join(ag_dir, "log"), exist_ok=True)
        legit_link = os.path.join(ag_dir, "cli.log")
        os.symlink("log/cli-2026.log", legit_link)
        nested_rogue = os.path.join(ag_dir, "antigravity")
        os.symlink("/Users/danhdueexoictif/.gemini/antigravity", nested_rogue)

        report_before = auditor.audit_all_profiles(self.homes_dir)
        prof_before = report_before["profiles"]["prof_rogue"]
        self.assertTrue(prof_before["vulnerabilities"]["rogue_symlinks"])
        self.assertEqual(prof_before["risk_level"], "HIGH")

        auditor.remediate_all_profiles(self.homes_dir)
        self.assertFalse(os.path.islink(nested_rogue))
        self.assertTrue(os.path.islink(legit_link))

        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report_after["profiles"]["prof_rogue"]["vulnerabilities"]["rogue_symlinks"])
        self.assertEqual(report_after["profiles"]["prof_rogue"]["risk_level"], "CLEAN")

    def test_audit_detects_and_remediates_missing_login_keychain_symlink(self):
        p_dir = self._create_mock_profile("prof_kc", machine_id="mid_kc_link")
        kc_dir = os.path.join(p_dir, "Library/Keychains")
        os.makedirs(kc_dir, exist_ok=True)
        with open(os.path.join(kc_dir, "prof_kc.keychain-db"), "w") as f:
            f.write("mock_kc")

        report_before = auditor.audit_all_profiles(self.homes_dir)
        self.assertTrue(report_before["profiles"]["prof_kc"]["vulnerabilities"]["missing_keychain_symlink"])

        auditor.remediate_all_profiles(self.homes_dir)
        self.assertEqual(os.readlink(os.path.join(kc_dir, "login.keychain")), "prof_kc.keychain-db")
        self.assertEqual(os.readlink(os.path.join(kc_dir, "login.keychain-db")), "prof_kc.keychain-db")

        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report_after["profiles"]["prof_kc"]["vulnerabilities"]["missing_keychain_symlink"])

    def test_audit_detects_base64_signed_out_oauth_token(self):
        p_dir = self._create_mock_profile("prof_b64", machine_id="mid_b64")
        vscdb_path = os.path.join(p_dir, "data/User/globalStorage/state.vscdb")
        conn = sqlite3.connect(vscdb_path)
        encoded = base64.b64encode(b'\n\x1fauthState{"state":"signedOut"}').decode()
        conn.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT)")
        conn.execute(
            "INSERT INTO ItemTable VALUES ('antigravityUnifiedStateSync.oauthToken', ?)",
            (encoded,),
        )
        conn.commit()
        conn.close()

        report = auditor.audit_all_profiles(self.homes_dir)
        self.assertTrue(report["profiles"]["prof_b64"]["vulnerabilities"]["identity_bleed"])

    def test_audit_detects_and_converts_absolute_symlinks_to_relative(self):
        p_dir = self._create_mock_profile("prof_abs", machine_id="mid_abs")
        real_home = os.path.dirname(self.homes_dir)
        os.makedirs(os.path.join(real_home, ".cache"), exist_ok=True)
        os.makedirs(os.path.join(real_home, "Library/Caches"), exist_ok=True)
        os.makedirs(os.path.join(p_dir, "Library"), exist_ok=True)
        top_link = os.path.join(p_dir, ".cache")
        nested_link = os.path.join(p_dir, "Library/Caches")
        os.symlink(os.path.join(real_home, ".cache"), top_link)
        os.symlink(os.path.join(real_home, "Library/Caches"), nested_link)

        report_before = auditor.audit_all_profiles(self.homes_dir)
        self.assertTrue(report_before["profiles"]["prof_abs"]["vulnerabilities"]["absolute_symlinks"])

        auditor.remediate_all_profiles(self.homes_dir)
        self.assertEqual(os.readlink(top_link), "../../.cache")
        self.assertEqual(os.readlink(nested_link), "../../../Library/Caches")
        self.assertTrue(os.path.isdir(top_link) and os.path.isdir(nested_link))

        report_after = auditor.audit_all_profiles(self.homes_dir)
        self.assertFalse(report_after["profiles"]["prof_abs"]["vulnerabilities"]["absolute_symlinks"])

    def test_terminate_profile_processes_protects_active_session(self):
        with patch.dict("os.environ", {"AGY_PROFILE": "active_prof"}):
            with patch("os.kill") as mock_kill:
                killed, skipped = auditor.terminate_profile_processes("active_prof")
                self.assertTrue(skipped)
                self.assertEqual(killed, [])
                mock_kill.assert_not_called()


if __name__ == "__main__":
    unittest.main()

