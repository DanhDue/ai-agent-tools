"""Unit and integration tests for sync-shared-contracts skill and CLI engine."""

from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Enable direct import of sync_contracts module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_contracts import (
    CANONICAL_FILES,
    TopologyError,
    compute_file_hash,
    compute_semantic_delta,
    compute_snapshot_id,
    main,
    parse_api_contract,
    parse_architecture_and_flow,
    parse_gaps_and_rfcs,
    path_matches_domain,
    render_brief,
    resolve_topology,
    scan_target_codebase,
    to_camel_case,
    utc_now_iso,
)


class TestSyncContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _scaffold_table_contracts(self, target_dir: Path, domain: str = "lyrics-sync") -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        api_content = f"""# API Contract: {domain}

- **Domain**: `{domain}`
- **Version**: `1.2.0`

## 2. Authentication and Headers
| Header | Type | Required | Description |
|---|---|---|---|
| Authorization | String | Yes | Bearer token |
| X-Worker-Token | String | Yes | Worker token |
| X-Correlation-ID | String | Yes | UUID trace |

## 3. Endpoints Matrix
| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/{domain}/tasks/claim | X-Worker-Token | Worker claims lease |
| POST | /api/v1/{domain}/tasks/{{id}}/progress | X-Worker-Token | Worker progress |
| GET | /api/v1/{domain}/status | Public | Capability check |

## 4. Payload Schemas
```json
{{
  "task_id": "tsk_01",
  "domain": "{domain}",
  "lease_duration_ms": 30000,
  "payload": {{
    "parameters": {{}},
    "config": {{}}
  }},
  "metrics": {{
    "execution_time_ms": 1250
  }}
}}
```
"""
        (target_dir / "api_contract.md").write_text(api_content, encoding="utf-8")

        arch_content = f"""# Architecture and Flow: {domain}

## 2. Seven Canonical Pipeline Steps
1. **Lease Acquisition**: Worker claims task lease.
2. **Input Validation**: Sanity checks.
3. **Core Compute**: Execute algorithm.
4. **Scratch Teardown**: Purge temp directory.

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Leased: Claim Task
    Leased --> Completed: Finish
```
"""
        (target_dir / "architecture_and_flow.md").write_text(arch_content, encoding="utf-8")

        gaps_content = f"""# Gaps and RFCs Ledger: {domain}

## 2. Active RFC Ledger
| RFC ID | Title | Proposing Repo | Status | Target Release | Breaking? |
|---|---|---|---|---|---|
| RFC-001 | Canonical baseline | Hub | Approved | 1.0.0 | No |
| RFC-002 | Cancellation support | Satellite | Draft | 1.1.0 | No |
| RFC-003 | Deprecated route | Hub | Rejected | 1.0.0 | Yes |
"""
        (target_dir / "gaps_and_rfcs.md").write_text(gaps_content, encoding="utf-8")

    def _scaffold_narrative_contracts(self, target_dir: Path, domain: str = "lyrics-sync") -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        api_content = f"""<!-- Version: 3.1.0 -->
# Live Pilot API: {domain}

```http
Authorization: Bearer token
X-Worker-Token: secret
X-Correlation-ID: uuid
```

### 2.1. Claim Task (POST /api/v1/{domain}/tasks/claim)
* **Method**: POST
* **Path**: /api/v1/{domain}/tasks/claim
* **Auth**: X-Worker-Token

### 2.2. Cancel Task
* **Method**: POST
* **Path**: /api/v1/{domain}/tasks/{{id}}/cancel

### 2.3. Health Status (GET /api/v1/{domain}/status)

```json
{{
  "task_id": "tsk_02",
  "lease_duration_ms": 15000,
  "payload": {{
    "nested_param": "val"
  }}
}}
```
"""
        (target_dir / "api_contract.md").write_text(api_content, encoding="utf-8")

        arch_content = f"""# Architecture: {domain}

### Step 1: Claim Lease
### Step 2: Validate
### Step 3: Compute
"""
        (target_dir / "architecture_and_flow.md").write_text(arch_content, encoding="utf-8")

        gaps_content = f"""# Ledger: {domain}

### GAP-01: Auto-detection of BPM
- **Status**: `OPEN`
- **Author**: worker

### GAP-02: GPU acceleration
* **Status**: PROPOSED

### GAP-03: Realtime progress websocket
- **Status**: ACCEPTED
"""
        (target_dir / "gaps_and_rfcs.md").write_text(gaps_content, encoding="utf-8")

    def test_syc_hp_01_parse_and_render_brief(self) -> None:
        """[SYC-HP-01] Dual-Format Contract Parsing and Requirements Brief Rendering."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        api_text = (hub_domain / "api_contract.md").read_text(encoding="utf-8")
        api_data = parse_api_contract(api_text)
        self.assertEqual(api_data["version"], "1.2.0")
        self.assertIn("Authorization", api_data["headers"])
        self.assertIn("X-Worker-Token", api_data["headers"])
        self.assertIn("POST /api/v1/lyrics-sync/tasks/claim", api_data["endpoints"])
        self.assertIn("GET /api/v1/lyrics-sync/status", api_data["endpoints"])
        self.assertIn("task_id", api_data["payload_keys"])
        self.assertEqual(api_data["payload_fields"].get("lease_duration_ms"), "integer")
        self.assertEqual(api_data["payload_fields"].get("metrics.execution_time_ms"), "integer")
        self.assertEqual(api_data["payload_fields"].get("payload.parameters"), "object")

        arch_text = (hub_domain / "architecture_and_flow.md").read_text(encoding="utf-8")
        arch_data = parse_architecture_and_flow(arch_text)
        self.assertIn("Lease Acquisition", arch_data["pipeline_steps"])
        self.assertIn("Core Compute", arch_data["pipeline_steps"])

        gaps_text = (hub_domain / "gaps_and_rfcs.md").read_text(encoding="utf-8")
        gaps_data = parse_gaps_and_rfcs(gaps_text)
        self.assertEqual(gaps_data["rfcs"]["RFC-001"]["status"], "ACKNOWLEDGED_ACTIVE")
        self.assertEqual(gaps_data["rfcs"]["RFC-002"]["status"], "ACTIONABLE_PENDING")
        self.assertEqual(gaps_data["rfcs"]["RFC-003"]["status"], "INACTIVE")

        # Narrative contract parsing
        narrative_dir = self.repo_root / "narrative"
        self._scaffold_narrative_contracts(narrative_dir, "lyrics-sync")
        n_api_text = (narrative_dir / "api_contract.md").read_text(encoding="utf-8")
        n_api_data = parse_api_contract(n_api_text)
        self.assertEqual(n_api_data["version"], "3.1.0")
        self.assertIn("POST /api/v1/lyrics-sync/tasks/claim", n_api_data["endpoints"])
        self.assertIn("POST /api/v1/lyrics-sync/tasks/{id}/cancel", n_api_data["endpoints"])
        self.assertIn("GET /api/v1/lyrics-sync/status", n_api_data["endpoints"])

        n_gaps_text = (narrative_dir / "gaps_and_rfcs.md").read_text(encoding="utf-8")
        n_gaps_data = parse_gaps_and_rfcs(n_gaps_text)
        self.assertEqual(n_gaps_data["rfcs"]["GAP-01"]["status"], "ACTIONABLE_PENDING")
        self.assertEqual(n_gaps_data["rfcs"]["GAP-02"]["status"], "ACTIONABLE_PENDING")
        self.assertEqual(n_gaps_data["rfcs"]["GAP-03"]["status"], "ACKNOWLEDGED_ACTIVE")

        # Brief rendering
        template_path = Path(__file__).resolve().parent.parent / "templates" / "contract_delta_brief.md.tmpl"
        brief = render_brief(
            template_path=template_path,
            domain="lyrics-sync",
            mode="hub",
            sync_status="DRIFT_DETECTED",
            snapshot_id="sha256:test123456",
            previous_version="1.0.0",
            current_version="1.2.0",
            hub_commit_range="a1b2c3..d4e5f6",
            changed_files=list(CANONICAL_FILES),
            endpoints=api_data["endpoints"],
            payload_keys=api_data["payload_keys"],
            payload_fields=api_data["payload_fields"],
            pipeline_steps=arch_data["pipeline_steps"],
            rfcs=gaps_data["rfcs"],
        )
        self.assertIn("# Contract Requirements Brief: lyrics-sync", brief)
        self.assertIn("## 1. Topology & Sync Metadata", brief)
        self.assertIn("sha256:test123456", brief)
        self.assertIn("## 2. API & Schema Requirements", brief)
        self.assertIn("POST /api/v1/lyrics-sync/tasks/claim", brief)

        # Brief CLI check
        brief_out = self.repo_root / "brief.md"
        exit_code = main(["brief", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--output", str(brief_out)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(brief_out.is_file())

        # Repeat brief CLI check on already-synced repository
        main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])
        repeat_brief_out = self.repo_root / "repeat_brief.md"
        repeat_exit = main(["brief", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--output", str(repeat_brief_out)])
        self.assertEqual(repeat_exit, 0)
        repeat_text = repeat_brief_out.read_text(encoding="utf-8")
        self.assertIn("- **Sync Status**: `IN_SYNC`", repeat_text)
        self.assertIn("- **Contract Version**: `1.2.0` -> `1.2.0`", repeat_text)
        self.assertIn("- _None (all canonical files identical)_", repeat_text)

    def test_syc_ec_01_initial_sync_absent_watermark(self) -> None:
        """[SYC-EC-01] Initial Sync Detection When Watermark File Is Absent."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        watermark = self.repo_root / ".agents" / "contract_sync.json"
        self.assertFalse(watermark.exists())

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--json"])
        self.assertEqual(exit_code, 0)

        output_json = json.loads(stdout_buf.getvalue())
        self.assertEqual(output_json["status"], "INITIAL_SYNC")
        self.assertEqual(output_json["domain"], "lyrics-sync")
        self.assertEqual(output_json["deltas"]["changed_files"], list(CANONICAL_FILES))
        self.assertIn("POST /api/v1/lyrics-sync/tasks/claim", output_json["deltas"]["endpoints"])

        strict_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"])
        self.assertEqual(strict_exit, 1)

    def test_syc_ec_02_heuristic_snake_and_camel_scan(self) -> None:
        """[SYC-EC-02] Heuristic Codebase Scanner Matches Parameterized Routes and CamelCase DTO Fields."""
        src_dir = self.repo_root / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        worker_code = """
        export class WorkerClient {
            readonly progressRoute = "/api/v1/lyrics-sync/tasks";
            readonly progressSuffix = "/progress";
            leaseDurationMs: number = 30000;
        }
        """
        (src_dir / "worker_client.ts").write_text(worker_code, encoding="utf-8")

        endpoints = [
            "POST /api/v1/lyrics-sync/tasks/{id}/progress",
            "GET /api/v1/lyrics-sync/status",
        ]
        headers = ["X-Worker-Token"]
        payload_keys = ["lease_duration_ms", "missing_token_key"]

        results = scan_target_codebase(self.repo_root, endpoints, headers, payload_keys)
        self.assertEqual(results["POST /api/v1/lyrics-sync/tasks/{id}/progress"], "FOUND_IN_CODE")
        self.assertEqual(results["GET /api/v1/lyrics-sync/status"], "MISSING_IN_CODE")
        self.assertEqual(results["lease_duration_ms"], "FOUND_IN_CODE")
        self.assertEqual(results["missing_token_key"], "MISSING_IN_CODE")

    def test_syc_ec_03_semantic_baseline_diffing(self) -> None:
        """[SYC-EC-03] Semantic Baseline Diffing When Hub Has No Git History or Field Types Change."""
        baseline_snapshot = {
            "endpoints": ["POST /api/v1/lyrics-sync/tasks/claim"],
            "headers": ["Authorization"],
            "payload_keys": ["task_id", "metrics.execution_time_ms"],
            "payload_fields": {
                "task_id": "string",
                "metrics.execution_time_ms": "integer",
            },
            "pipeline_steps": ["Lease Acquisition", "Input Validation"],
        }

        current_data = {
            "endpoints": ["POST /api/v1/lyrics-sync/tasks/claim"],
            "headers": ["Authorization"],
            "payload_keys": ["task_id", "metrics.execution_time_ms", "retry_after_ms"],
            "payload_fields": {
                "task_id": "string",
                "metrics.execution_time_ms": "string",
                "retry_after_ms": "integer",
            },
            "pipeline_steps": ["Lease Acquisition", "Input Validation", "Core Compute"],
        }

        deltas = compute_semantic_delta(current_data, baseline_snapshot)
        self.assertIn("retry_after_ms", deltas["added_keys"])
        self.assertIn("metrics.execution_time_ms: integer -> string", deltas["modified_field_types"])
        self.assertTrue(len(deltas["modified_pipeline_steps"]) > 0)

    def test_syc_ec_04_worktree_aware_symlink_resolution(self) -> None:
        """[SYC-EC-04] Worktree-Aware Relative Symlink Resolution Inside Nested Epic Worktree."""
        primary_satellite = self.repo_root / "primary_satellite"
        primary_satellite.mkdir(parents=True, exist_ok=True)

        hub_repo = self.repo_root / "Hub" / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_repo, "lyrics-sync")

        rel_to_hub = os.path.relpath(hub_repo, primary_satellite)
        os.symlink(rel_to_hub, primary_satellite / "shared-contracts")

        worktree_dir = primary_satellite / ".worktrees" / "sync_epic"
        worktree_dir.mkdir(parents=True, exist_ok=True)
        os.symlink(rel_to_hub, worktree_dir / "shared-contracts")

        (worktree_dir / ".git").write_text(f"gitdir: {primary_satellite}/.git/worktrees/sync_epic\n", encoding="utf-8")

        topo = resolve_topology(worktree_dir, "lyrics-sync")
        self.assertEqual(topo["mode"], "satellite")
        self.assertEqual(topo["contract_dir"].resolve(), hub_repo.resolve())
        self.assertEqual(os.readlink(worktree_dir / "shared-contracts"), rel_to_hub)

    def test_syc_ar_02_circular_symlink_loop_protection(self) -> None:
        """[SYC-AR-02] Circular Symlink Loop Protection During Topology Resolution."""
        link_a = self.repo_root / "shared-contracts"
        link_b = self.repo_root / "link_b"
        os.symlink("link_b", link_a)
        os.symlink("shared-contracts", link_b)

        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("Symbolic link loop detected", str(ctx.exception))

    def test_syc_fr_01_refuse_when_shared_contracts_missing(self) -> None:
        """[SYC-FR-01] Refusing Execution When Shared Contracts Directory Is Missing."""
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("shared-contracts not found", str(ctx.exception))

        exit_code = main(["check", "--repo-root", str(self.repo_root)])
        self.assertEqual(exit_code, 1)

    def test_syc_fr_02_refuse_on_dangling_or_unsupported_contract(self) -> None:
        """[SYC-FR-02] Refusing Execution on Dangling Symlink, Missing Canonical Files, or Unsupported Contract Format."""
        os.symlink("../non_existent_hub", self.repo_root / "shared-contracts")
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("Dangling symlink", str(ctx.exception))
        os.unlink(self.repo_root / "shared-contracts")

        (self.repo_root / "shared-contracts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "shared-contracts" / "api_contract.md").write_text("# API\n", encoding="utf-8")
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("Missing canonical contract file", str(ctx.exception))

        (self.repo_root / "shared-contracts" / "architecture_and_flow.md").write_text("# Arch\n", encoding="utf-8")
        (self.repo_root / "shared-contracts" / "gaps_and_rfcs.md").write_text("# Gaps\n", encoding="utf-8")
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("UNSUPPORTED_CONTRACT_FORMAT", str(ctx.exception))

    def test_to_camel_case(self) -> None:
        """Test snake_case to camelCase conversion helper."""
        self.assertEqual(to_camel_case("lease_duration_ms"), "leaseDurationMs")
        self.assertEqual(to_camel_case("task_id"), "taskId")
        self.assertEqual(to_camel_case("status"), "status")

    def test_syc_hp_03_skill_and_verify_harness(self) -> None:
        """[SYC-HP-03] Skill Definition and Release Verify Harness Execution."""
        # Find skill directory in current repo
        skill_file = Path(__file__).resolve().parent.parent.parent / "SKILL.md"
        self.assertTrue(skill_file.is_file(), f"SKILL.md not found at {skill_file}")

        content = skill_file.read_text(encoding="utf-8")
        # Validate frontmatter has exactly name and description
        self.assertTrue(content.startswith("---\n"))
        end_idx = content.find("\n---\n", 4)
        self.assertNotEqual(end_idx, -1)
        fm_lines = [line.strip() for line in content[4:end_idx].splitlines() if line.strip()]
        fm_keys = [line.split(":")[0].strip() for line in fm_lines if ":" in line]
        self.assertEqual(sorted(fm_keys), ["description", "name"])
        self.assertIn("name: sync-shared-contracts", content)

        # Validate scripts/verify.sh registers test_sync_contracts.py
        verify_sh = Path(__file__).resolve().parents[4] / "scripts" / "verify.sh"
        self.assertTrue(verify_sh.is_file(), f"verify.sh not found at {verify_sh}")
        verify_content = verify_sh.read_text(encoding="utf-8")
        self.assertIn("skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py", verify_content)

    def test_syc_hp_02_satellite_worktree_and_hub_check(self) -> None:
        """[SYC-HP-02] End-to-End Satellite and Nested Worktree Synchronization Pass."""
        primary_satellite = self.repo_root / "satellite"
        primary_satellite.mkdir(parents=True, exist_ok=True)

        hub_repo = self.repo_root / "Hub" / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_repo, "lyrics-sync")

        rel_to_hub = os.path.relpath(hub_repo, primary_satellite)
        os.symlink(rel_to_hub, primary_satellite / "shared-contracts")

        # Create nested git worktree
        worktree_dir = primary_satellite / ".worktrees" / "sync_epic"
        worktree_dir.mkdir(parents=True, exist_ok=True)
        os.symlink(rel_to_hub, worktree_dir / "shared-contracts")
        (worktree_dir / ".git").write_text(f"gitdir: {primary_satellite}/.git/worktrees/sync_epic\n", encoding="utf-8")

        # 1. Run ack --all-rfcs from inside worktree
        ack_exit = main(["ack", "--repo-root", str(worktree_dir), "--domain", "lyrics-sync", "--all-rfcs"])
        self.assertEqual(ack_exit, 0)

        # Verify .agents/contract_sync.json is created in worktree
        state_file = worktree_dir / ".agents" / "contract_sync.json"
        self.assertTrue(state_file.is_file())
        state = json.loads(state_file.read_text(encoding="utf-8"))
        self.assertEqual(state["mode"], "satellite")
        dom_entry = state["domains"]["lyrics-sync"]
        self.assertTrue(dom_entry["snapshot_id"].startswith("sha256:"))
        self.assertEqual(dom_entry["pending_rfcs"], [])
        self.assertIn("RFC-001", dom_entry["acknowledged_rfcs"])
        self.assertIn("lease_duration_ms", dom_entry["baseline_snapshot"]["payload_fields"])

        # 2. Run check --strict from inside worktree
        check_exit = main(["check", "--repo-root", str(worktree_dir), "--domain", "lyrics-sync", "--strict"])
        self.assertEqual(check_exit, 0)

        # Ensure tracked symlink in worktree was unchanged
        self.assertEqual(os.readlink(worktree_dir / "shared-contracts"), rel_to_hub)

    def test_syc_st_01_ack_snapshot_and_incremental_drift(self) -> None:
        """[SYC-ST-01] Hub Snapshot Refresh and Incremental Drift Detection After Upstream Update."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        # Initial baseline without RFC-002 so it can be added upstream
        gaps_init = """# Gaps and RFCs Ledger: lyrics-sync

## 2. Active RFC Ledger
| RFC ID | Title | Proposing Repo | Status | Target Release | Breaking? |
|---|---|---|---|---|---|
| RFC-001 | Canonical baseline | Hub | Approved | 1.0.0 | No |
| RFC-003 | Deprecated route | Hub | Rejected | 1.0.0 | Yes |
"""
        (hub_domain / "gaps_and_rfcs.md").write_text(gaps_init, encoding="utf-8")

        # Initial ack --all-rfcs -> IN_SYNC
        exit_code = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"]), 0)

        # Hub updates api_contract.md and gaps_and_rfcs.md
        api_text = (hub_domain / "api_contract.md").read_text(encoding="utf-8")
        api_text = api_text.replace("1.2.0", "1.3.0")
        cancel_row = "| POST | /api/v1/lyrics-sync/tasks/{id}/cancel | X-Worker-Token | Cancel task |\n"
        api_text = api_text.replace(
            "| GET | /api/v1/lyrics-sync/status | Public | Capability check |\n",
            f"| GET | /api/v1/lyrics-sync/status | Public | Capability check |\n{cancel_row}",
        )
        (hub_domain / "api_contract.md").write_text(api_text, encoding="utf-8")

        gaps_text = (hub_domain / "gaps_and_rfcs.md").read_text(encoding="utf-8")
        gaps_text += "| RFC-002 | Cancellation support | Satellite | Open | 1.3.0 | No |\n"
        (hub_domain / "gaps_and_rfcs.md").write_text(gaps_text, encoding="utf-8")

        # check --strict in human text mode reports DRIFT_DETECTED, surfaces RFC-002 and cancel endpoint, exits 1
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            strict_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"])
        self.assertEqual(strict_exit, 1)
        check_out = stdout_buf.getvalue()
        self.assertIn("DRIFT_DETECTED", check_out)
        self.assertIn("/api/v1/lyrics-sync/tasks/{id}/cancel", check_out)
        self.assertIn("RFC-002", check_out)

        # check --strict in JSON mode surfaces pending_rfcs and delta additions
        json_buf = io.StringIO()
        with patch("sys.stdout", json_buf):
            json_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict", "--json"])
        self.assertEqual(json_exit, 1)
        check_json = json.loads(json_buf.getvalue())
        self.assertEqual(check_json["status"], "DRIFT_DETECTED")
        self.assertIn("RFC-002", check_json["pending_rfcs"])
        self.assertIn("RFC-002", check_json["deltas"]["added_rfcs"])
        self.assertIn("POST /api/v1/lyrics-sync/tasks/{id}/cancel", check_json["deltas"]["added_endpoints"])

        # Refresh snapshot via sync_contracts.py brief
        brief_file = self.repo_root / "brief_refreshed.md"
        brief_exit = main(["brief", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--output", str(brief_file)])
        self.assertEqual(brief_exit, 0)
        self.assertTrue(brief_file.is_file())
        brief_text = brief_file.read_text(encoding="utf-8")
        self.assertIn("- **Sync Status**: `DRIFT_DETECTED`", brief_text)
        self.assertIn("- **Contract Version**: `1.2.0` -> `1.3.0`", brief_text)
        self.assertIn("api_contract.md", brief_text)
        self.assertIn("gaps_and_rfcs.md", brief_text)
        self.assertIn("RFC-002", brief_text)

        snapshot_match = re.search(r"-\s+\*\*Snapshot ID\*\*:\s+`([^`]+)`", brief_text)
        self.assertIsNotNone(snapshot_match)
        assert snapshot_match is not None
        refreshed_snapshot_id = snapshot_match.group(1)

        # ack with refreshed snapshot ID and --all-rfcs
        ack_exit = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--snapshot", refreshed_snapshot_id, "--all-rfcs"])
        self.assertEqual(ack_exit, 0)

        # Subsequent check --strict passes with exit 0
        self.assertEqual(main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"]), 0)

    def test_syc_st_02_explicit_scope_bound_rfc_selection(self) -> None:
        """[SYC-ST-02] Explicit Scope-Bound RFC Selection, Scoped Strict Check, and Multi-Domain Watermark Preservation."""
        hub_shared = self.repo_root / "shared-contracts"
        self._scaffold_table_contracts(hub_shared / "lyrics-sync", "lyrics-sync")
        self._scaffold_narrative_contracts(hub_shared / "nexus", "nexus")

        # 1. Sync lyrics-sync first
        main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])

        # 2. Ack nexus partially: only GAP-03 (while GAP-01 and GAP-02 remain in contract)
        ack_exit = main(["ack", "--repo-root", str(self.repo_root), "--domain", "nexus", "--rfc", "GAP-03"])
        self.assertEqual(ack_exit, 0)

        state = json.loads((self.repo_root / ".agents" / "contract_sync.json").read_text(encoding="utf-8"))
        # Preserves lyrics-sync entry
        self.assertIn("lyrics-sync", state["domains"])
        nexus_data = state["domains"]["nexus"]
        self.assertIn("GAP-03", nexus_data["acknowledged_rfcs"])
        self.assertIn("GAP-01", nexus_data["pending_rfcs"])

        # Scoped check for GAP-03 exits 0
        scoped_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "nexus", "--strict", "--rfc", "GAP-03"])
        self.assertEqual(scoped_exit, 0)

        # Global check for nexus reports drift and exits 1
        global_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "nexus", "--strict"])
        self.assertEqual(global_exit, 1)

        # 3. Ack remaining RFCs
        main(["ack", "--repo-root", str(self.repo_root), "--domain", "nexus", "--rfc", "GAP-01", "--rfc", "GAP-02"])
        state_after = json.loads((self.repo_root / ".agents" / "contract_sync.json").read_text(encoding="utf-8"))
        self.assertEqual(state_after["domains"]["nexus"]["pending_rfcs"], [])
        self.assertEqual(main(["check", "--repo-root", str(self.repo_root), "--domain", "nexus", "--strict"]), 0)

    def test_syc_st_03_snapshot_mismatch_rejection(self) -> None:
        """[SYC-ST-03] Snapshot Mismatch Rejection When Contract Changes Before Ack."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            exit_code = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--snapshot", "sha256:stale_mismatch_hash"])
        self.assertEqual(exit_code, 1)
        self.assertIn("SNAPSHOT_MISMATCH", stderr_buf.getvalue())
        self.assertFalse((self.repo_root / ".agents" / "contract_sync.json").exists())

    def test_syc_ar_01_atomic_watermark_update(self) -> None:
        """[SYC-AR-01] Atomic Watermark File Update Prevents Partial JSON Reads."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        exit_code = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])
        self.assertEqual(exit_code, 0)

        agents_dir = self.repo_root / ".agents"
        self.assertTrue((agents_dir / "contract_sync.json").is_file())
        # Check no temporary files left in .agents
        tmp_files = list(agents_dir.glob("*.tmp"))
        self.assertEqual(tmp_files, [])

    def test_syc_fr_03_corrupted_watermark_recovery(self) -> None:
        """[SYC-FR-03] Resilience Against Corrupted Watermark JSON File."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        # Write corrupted JSON
        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "contract_sync.json").write_text("{corrupt_json_payload...", encoding="utf-8")

        # check logs warning and treats as INITIAL_SYNC without crashing
        stderr_buf = io.StringIO()
        with patch("sys.stderr", stderr_buf):
            check_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync"])
        self.assertEqual(check_exit, 0)
        self.assertIn("corrupted watermark JSON", stderr_buf.getvalue())

        # ack overwrites cleanly with valid JSON
        ack_exit = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])
        self.assertEqual(ack_exit, 0)

        clean_state = json.loads((agents_dir / "contract_sync.json").read_text(encoding="utf-8"))
        self.assertEqual(clean_state["schema_version"], 1)
        self.assertIn("lyrics-sync", clean_state["domains"])

    def _init_git_repo(self, repo_dir: Path, branch: str = "develop") -> None:
        subprocess.run(["git", "init", "-b", branch], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True, capture_output=True)

    def _commit_all(self, repo_dir: Path, message: str) -> None:
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], cwd=repo_dir, check=True, capture_output=True)

    def test_cdg_hp_01_hub_mapped_file_change_covered_by_contract_edit(self) -> None:
        """[CDG-HP-01] Hub Mapped File Change Covered by Canonical Contract Edit."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {
                    "paths": ["crates/**/routes/**", "crates/**/dto/**"],
                    "exclude": ["**/tests/**"],
                }
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit")

        subprocess.run(["git", "checkout", "-b", "feat/worker-routes"], cwd=self.repo_root, check=True, capture_output=True)
        worker_file = self.repo_root / "crates" / "api" / "routes" / "worker.rs"
        worker_file.parent.mkdir(parents=True, exist_ok=True)
        worker_file.write_text("// worker routes implementation", encoding="utf-8")

        contract_file = hub_domain / "api_contract.md"
        contract_file.write_text(contract_file.read_text(encoding="utf-8") + "\n<!-- edit -->\n", encoding="utf-8")

        self._commit_all(self.repo_root, "Add worker route and update contract")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--base-ref", "develop", "--json"])

        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["mode"], "hub")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["blockers"], [])

    def test_cdg_hp_02_satellite_mapped_file_change_covered_by_fresh_ack(self) -> None:
        """[CDG-HP-02] Satellite Mapped File Change Covered by Fresh Domain Ack Matching Live Snapshot."""
        hub_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="hub_hp02_"))
        self._init_git_repo(hub_dir, "main")
        hub_domain = hub_dir / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        self._commit_all(hub_dir, "Hub init")

        sat_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="sat_hp02_"))
        self._init_git_repo(sat_dir, "develop")
        rel_target = os.path.relpath(hub_domain, sat_dir)
        os.symlink(rel_target, sat_dir / "shared-contracts")

        sat_agents = sat_dir / ".agents"
        sat_agents.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]}
            },
            "waivers": [],
        }
        (sat_agents / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        main(["ack", "--repo-root", str(sat_dir), "--domain", "lyrics-sync", "--all-rfcs"])
        # Set earlier last_synced_at on base commit to represent prior sync
        sync_json = sat_agents / "contract_sync.json"
        state = json.loads(sync_json.read_text(encoding="utf-8"))
        state["domains"]["lyrics-sync"]["last_synced_at"] = "2026-10-01T00:00:00Z"
        sync_json.write_text(json.dumps(state, indent=2), encoding="utf-8")
        self._commit_all(sat_dir, "Base commit on develop")

        subprocess.run(["git", "checkout", "-b", "feat/worker"], cwd=sat_dir, check=True, capture_output=True)
        dto_file = sat_dir / "src" / "api" / "dto" / "worker.py"
        dto_file.parent.mkdir(parents=True, exist_ok=True)
        dto_file.write_text("# worker dto", encoding="utf-8")

        hashes = {f: compute_file_hash(hub_domain / f) for f in CANONICAL_FILES}
        live_snapshot = compute_snapshot_id(hashes)

        ack_exit = main(["ack", "--repo-root", str(sat_dir), "--domain", "lyrics-sync", "--snapshot", live_snapshot, "--all-rfcs"])
        self.assertEqual(ack_exit, 0)
        self._commit_all(sat_dir, "Update dto and refresh ack")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(sat_dir), "--json"])

        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["mode"], "satellite")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["domains"][0]["proof"], "ack")

    def test_cdg_ec_01_anchored_posix_glob_matching(self) -> None:
        """[CDG-EC-01] Anchored Multi-Level POSIX Glob Matching and Exclude Precedence."""
        domain_cfg = {
            "paths": ["crates/**/routes/**", "src/*/dto/*.py"],
            "exclude": ["**/tests/**"],
        }
        self.assertTrue(path_matches_domain("crates/routes/v1.rs", domain_cfg))
        self.assertTrue(path_matches_domain("crates/core/http/routes/v1/tasks.rs", domain_cfg))
        self.assertTrue(path_matches_domain("src/worker/dto/job.py", domain_cfg))
        self.assertFalse(path_matches_domain("crates/api/routes/tests/mock.rs", domain_cfg))
        self.assertFalse(path_matches_domain("other/crates/routes/v1.rs", domain_cfg))

    def test_cdg_ec_02_empty_diff_or_unmapped_changes(self) -> None:
        """[CDG-EC-02] Empty Diff at Merge-Base or Unmapped File Changes Pass Cleanly."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")
        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["crates/**/routes/**"]}
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["violations"], [])
        self.assertEqual(report["active_waivers"], [])

        subprocess.run(["git", "checkout", "-b", "feat/docs"], cwd=self.repo_root, check=True, capture_output=True)
        (self.repo_root / "README.md").write_text("# Documentation\n", encoding="utf-8")
        self._commit_all(self.repo_root, "Update docs")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code2, 0)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "PASS")
        self.assertEqual(report2["violations"], [])
        self.assertEqual(report2["active_waivers"], [])
        self.assertEqual(report2["domains"][0]["proof"], "none")

    def test_cdg_ec_03_base_ref_override_and_domain_filter(self) -> None:
        """[CDG-EC-03] Base-Ref CLI Override Precedence and Repeatable Domain Filter Validation."""
        self._init_git_repo(self.repo_root, "main")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        nexus_domain = self.repo_root / "shared-contracts" / "nexus"
        self._scaffold_table_contracts(nexus_domain, "nexus")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "main",
            "domains": {
                "lyrics-sync": {"paths": ["crates/lyrics/**"]},
                "nexus": {"paths": ["crates/nexus/**"]},
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Main commit")

        subprocess.run(["git", "checkout", "-b", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feat/nexus-only"], cwd=self.repo_root, check=True, capture_output=True)
        nexus_file = self.repo_root / "crates" / "nexus" / "a.rs"
        nexus_file.parent.mkdir(parents=True, exist_ok=True)
        nexus_file.write_text("// nexus", encoding="utf-8")
        self._commit_all(self.repo_root, "Edit nexus")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--base-ref", "develop", "--domain", "lyrics-sync", "--json"])
        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["domains"]), 1)
        self.assertEqual(report["domains"][0]["domain"], "lyrics-sync")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(self.repo_root), "--domain", "nonexistent_domain", "--json"])
        self.assertEqual(exit_code2, 2)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "BLOCKED")
        self.assertTrue(any("nonexistent_domain" in b for b in report2["blockers"]))

    def test_cdg_ec_04_new_waiver_with_null_and_valid_gap(self) -> None:
        """[CDG-EC-04] Newly Added Path-Scoped Waivers With Null Gap and Documented GAP-XX Pass With Audit Output."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/routes/**"]}
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit")

        subprocess.run(["git", "checkout", "-b", "feat/waiver-null"], cwd=self.repo_root, check=True, capture_output=True)
        tts_file = self.repo_root / "src" / "routes" / "tts.py"
        tts_file.parent.mkdir(parents=True, exist_ok=True)
        tts_file.write_text("# tts route", encoding="utf-8")

        contract_map["waivers"] = [
            {
                "id": "W-001",
                "domain": "lyrics-sync",
                "paths": ["src/routes/tts.py"],
                "reason": "Temporary exception while awaiting API contract freeze",
                "gap": None,
            }
        ]
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Waiver with null gap")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["active_waivers"]), 1)
        self.assertEqual(report["active_waivers"][0]["id"], "W-001")
        self.assertEqual(report["active_waivers"][0]["gap"], None)

        stdout_buf_text = io.StringIO()
        with patch("sys.stdout", stdout_buf_text):
            exit_code_text = main(["diff-check", "--repo-root", str(self.repo_root)])
        self.assertEqual(exit_code_text, 0)
        self.assertIn("W-001", stdout_buf_text.getvalue())

        subprocess.run(["git", "checkout", "-b", "feat/waiver-gap"], cwd=self.repo_root, check=True, capture_output=True)
        contract_map["waivers"] = [
            {
                "id": "W-002",
                "domain": "lyrics-sync",
                "paths": ["src/routes/tts.py"],
                "reason": "Waiting for GAP-08 implementation",
                "gap": "GAP-08",
            }
        ]
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Waiver with GAP-08")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code2, 0)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "PASS")
        self.assertEqual(report2["active_waivers"][0]["gap"], "GAP-08")

    def test_cdg_ec_05_nul_rename_out_and_git_quoted_filename(self) -> None:
        """[CDG-EC-05] NUL-Delimited Rename-Out Detection and Git-Quoted Filename Matching Across Hub and Satellite."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]}
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        worker_file = self.repo_root / "src" / "api" / "dto" / "worker.py"
        worker_file.parent.mkdir(parents=True, exist_ok=True)
        worker_file.write_text("# worker", encoding="utf-8")
        self._commit_all(self.repo_root, "Initial worker dto")

        subprocess.run(["git", "checkout", "-b", "feat/rename-and-quoted"], cwd=self.repo_root, check=True, capture_output=True)
        dest_internal = self.repo_root / "src" / "internal" / "worker.py"
        dest_internal.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "mv", "src/api/dto/worker.py", "src/internal/worker.py"], cwd=self.repo_root, check=True, capture_output=True)

        quoted_file = self.repo_root / "src" / "api" / "dto" / "worker v2 (draft).py"
        quoted_file.write_text("# draft", encoding="utf-8")
        self._commit_all(self.repo_root, "Rename out and add quoted file")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code, 1)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "FAIL")
        violation_files = [v["file"] for v in report["violations"]]
        self.assertIn("src/api/dto/worker.py", violation_files)
        self.assertIn("src/api/dto/worker v2 (draft).py", violation_files)

        (hub_domain / "api_contract.md").write_text((hub_domain / "api_contract.md").read_text(encoding="utf-8") + "\n<!-- edit -->\n", encoding="utf-8")
        self._commit_all(self.repo_root, "Canonical contract edit")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code2, 0)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "PASS")

    def test_cdg_st_01_uncovered_mapped_file_and_partial_waiver(self) -> None:
        """[CDG-ST-01] Uncovered Mapped File Changes and Partial Waivers Transition Verdict to FAIL."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["crates/**/routes/**", "crates/**/dto/**"]}
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit")

        subprocess.run(["git", "checkout", "-b", "feat/partial-waiver"], cwd=self.repo_root, check=True, capture_output=True)
        f_x = self.repo_root / "crates" / "a" / "routes" / "x.rs"
        f_y = self.repo_root / "crates" / "a" / "dto" / "y.rs"
        f_x.parent.mkdir(parents=True, exist_ok=True)
        f_y.parent.mkdir(parents=True, exist_ok=True)
        f_x.write_text("// x", encoding="utf-8")
        f_y.write_text("// y", encoding="utf-8")

        contract_map["waivers"] = [
            {
                "id": "W-010",
                "domain": "lyrics-sync",
                "paths": ["crates/a/routes/x.rs"],
                "reason": "Only covers x",
                "gap": None,
            }
        ]
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Partial waiver and edits")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code, 1)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "FAIL")
        violation_files = [v["file"] for v in report["violations"]]
        self.assertIn("crates/a/dto/y.rs", violation_files)
        self.assertNotIn("crates/a/routes/x.rs", violation_files)

    def test_cdg_st_02_historical_waiver_non_masking_and_mutation(self) -> None:
        """[CDG-ST-02] Historical Waiver Non-Masking, Mutation Rejection, and Obsolete Waiver Deletion."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["crates/**/routes/**"]}
            },
            "waivers": [
                {
                    "id": "W-OLD",
                    "domain": "lyrics-sync",
                    "paths": ["crates/a/routes/x.rs"],
                    "reason": "Historical waiver",
                    "gap": None,
                }
            ],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Base with W-OLD")

        subprocess.run(["git", "checkout", "-b", "branch-a", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        fx = self.repo_root / "crates" / "a" / "routes" / "x.rs"
        fx.parent.mkdir(parents=True, exist_ok=True)
        fx.write_text("// edit on branch a", encoding="utf-8")
        self._commit_all(self.repo_root, "Branch A edit")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code_a = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code_a, 1)

        subprocess.run(["git", "checkout", "-b", "branch-b", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        contract_map["waivers"] = [
            {
                "id": "W-OLD",
                "domain": "lyrics-sync",
                "paths": ["crates/a/routes/x.rs"],
                "reason": "Mutated reason",
                "gap": None,
            }
        ]
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Branch B mutate waiver")

        stdout_buf_b = io.StringIO()
        with patch("sys.stdout", stdout_buf_b):
            exit_code_b = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code_b, 1)
        report_b = json.loads(stdout_buf_b.getvalue())
        self.assertTrue(any("Illegal mutation" in v["message"] for v in report_b["violations"]))

        subprocess.run(["git", "checkout", "-b", "branch-c", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        contract_map["waivers"] = []
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Branch C delete waiver")

        stdout_buf_c = io.StringIO()
        with patch("sys.stdout", stdout_buf_c):
            exit_code_c = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code_c, 0)

    def test_cdg_st_03_satellite_sibling_domain_and_stale_snapshot_or_inactive_gap(self) -> None:
        """[CDG-ST-03] Satellite Sibling-Domain Ack Isolation, Stale Snapshot Rejection, and Missing or INACTIVE GAP-XX Failure."""
        hub_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="hub3_"))
        self._init_git_repo(hub_dir, "main")
        hub_lyrics = hub_dir / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_lyrics, "lyrics-sync")
        self._commit_all(hub_dir, "Hub init")

        sat_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="sat3_"))
        self._init_git_repo(sat_dir, "develop")
        rel_target = os.path.relpath(hub_lyrics, sat_dir)
        os.symlink(rel_target, sat_dir / "shared-contracts")

        sat_agents = sat_dir / ".agents"
        sat_agents.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]}
            },
            "waivers": [],
        }
        (sat_agents / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        main(["ack", "--repo-root", str(sat_dir), "--domain", "lyrics-sync", "--all-rfcs"])
        self._commit_all(sat_dir, "Sat base")

        subprocess.run(["git", "checkout", "-b", "feat/sibling", "develop"], cwd=sat_dir, check=True, capture_output=True)
        f_dto = sat_dir / "src" / "api" / "dto" / "worker.py"
        f_dto.parent.mkdir(parents=True, exist_ok=True)
        f_dto.write_text("# worker", encoding="utf-8")

        sync_state = json.loads((sat_agents / "contract_sync.json").read_text(encoding="utf-8"))
        sync_state["domains"]["nexus"] = {"snapshot_id": "sha256:nexus", "last_synced_at": utc_now_iso()}
        (sat_agents / "contract_sync.json").write_text(json.dumps(sync_state, indent=2), encoding="utf-8")
        self._commit_all(sat_dir, "Update sibling domain only")

        stdout_buf1 = io.StringIO()
        with patch("sys.stdout", stdout_buf1):
            exit_code1 = main(["diff-check", "--repo-root", str(sat_dir), "--json"])
        self.assertEqual(exit_code1, 1)

        subprocess.run(["git", "checkout", "-b", "feat/stale", "develop"], cwd=sat_dir, check=True, capture_output=True)
        f_dto.parent.mkdir(parents=True, exist_ok=True)
        f_dto.write_text("# worker stale", encoding="utf-8")
        sync_state2 = json.loads((sat_agents / "contract_sync.json").read_text(encoding="utf-8"))
        sync_state2["domains"]["lyrics-sync"]["snapshot_id"] = "sha256:stale_fake_hash"
        sync_state2["domains"]["lyrics-sync"]["last_synced_at"] = utc_now_iso()
        (sat_agents / "contract_sync.json").write_text(json.dumps(sync_state2, indent=2), encoding="utf-8")
        self._commit_all(sat_dir, "Stale snapshot ack")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(sat_dir), "--json"])
        self.assertEqual(exit_code2, 1)

        subprocess.run(["git", "checkout", "-b", "feat/bad-gap", "develop"], cwd=sat_dir, check=True, capture_output=True)
        contract_map["waivers"] = [
            {
                "id": "W-999",
                "domain": "lyrics-sync",
                "paths": ["src/api/dto/worker.py"],
                "reason": "Missing gap",
                "gap": "GAP-999",
            }
        ]
        (sat_agents / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(sat_dir, "Waiver with GAP-999")

        stdout_buf3 = io.StringIO()
        with patch("sys.stdout", stdout_buf3):
            exit_code3 = main(["diff-check", "--repo-root", str(sat_dir), "--json"])
        self.assertEqual(exit_code3, 1)

    def test_cdg_st_04_baseline_union_domain_mapping(self) -> None:
        """[CDG-ST-04] Baseline-Union Domain Mapping Prevents Self-Exemption While Allowing Bootstrap and Untouched Domain Retirement."""
        self._init_git_repo(self.repo_root, "develop")
        hub_lyrics = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_lyrics, "lyrics-sync")
        hub_legacy = self.repo_root / "shared-contracts" / "legacy-domain"
        self._scaffold_table_contracts(hub_legacy, "legacy-domain")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]},
                "legacy-domain": {"paths": ["crates/legacy/**"]},
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        dto_file = self.repo_root / "src" / "api" / "dto" / "worker.py"
        dto_file.parent.mkdir(parents=True, exist_ok=True)
        dto_file.write_text("# worker", encoding="utf-8")
        self._commit_all(self.repo_root, "Base with lyrics and legacy")

        subprocess.run(["git", "checkout", "-b", "branch-a-excl", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        dto_file.write_text("# worker modified", encoding="utf-8")
        map_a = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {
                    "paths": ["src/api/dto/**"],
                    "exclude": ["src/api/dto/worker.py"],
                },
                "legacy-domain": {"paths": ["crates/legacy/**"]},
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(map_a, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Self-exempt via exclude")

        stdout_buf_a = io.StringIO()
        with patch("sys.stdout", stdout_buf_a):
            exit_code_a = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code_a, 1)

        subprocess.run(["git", "checkout", "-b", "branch-b-retire", "develop"], cwd=self.repo_root, check=True, capture_output=True)
        map_b = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]},
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(map_b, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Retire legacy domain")

        stdout_buf_b = io.StringIO()
        with patch("sys.stdout", stdout_buf_b):
            exit_code_b = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code_b, 0)

        boot_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="boot_"))
        self._init_git_repo(boot_dir, "develop")
        boot_hub = boot_dir / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(boot_hub, "lyrics-sync")
        self._commit_all(boot_dir, "M commit without contract_map")

        subprocess.run(["git", "checkout", "-b", "feat/bootstrap"], cwd=boot_dir, check=True, capture_output=True)
        boot_agents = boot_dir / ".agents"
        boot_agents.mkdir(parents=True, exist_ok=True)
        (boot_agents / "contract_map.json").write_text(json.dumps(map_b, indent=2), encoding="utf-8")
        self._commit_all(boot_dir, "Introduce contract_map.json")

        stdout_buf_c = io.StringIO()
        with patch("sys.stdout", stdout_buf_c):
            exit_code_c = main(["diff-check", "--repo-root", str(boot_dir), "--json"])
        self.assertEqual(exit_code_c, 0)

    def test_cdg_ar_01_nested_worktree_satellite_symlink(self) -> None:
        """[CDG-AR-01] Nested Epic Worktree Symlink Resolution During Satellite Diff-Check."""
        hub_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="hub_ar01_"))
        self._init_git_repo(hub_dir, "main")
        hub_domain = hub_dir / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        self._commit_all(hub_dir, "Hub init")

        sat_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="sat_ar01_"))
        self._init_git_repo(sat_dir, "develop")
        rel_target = os.path.relpath(hub_domain, sat_dir)
        os.symlink(rel_target, sat_dir / "shared-contracts")

        sat_agents = sat_dir / ".agents"
        sat_agents.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/api/dto/**"]}
            },
            "waivers": [],
        }
        (sat_agents / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        main(["ack", "--repo-root", str(sat_dir), "--domain", "lyrics-sync", "--all-rfcs"])
        sync_json = sat_agents / "contract_sync.json"
        state = json.loads(sync_json.read_text(encoding="utf-8"))
        state["domains"]["lyrics-sync"]["last_synced_at"] = "2026-10-01T00:00:00Z"
        sync_json.write_text(json.dumps(state, indent=2), encoding="utf-8")
        self._commit_all(sat_dir, "Sat base commit")

        worktree_path = sat_dir / ".worktrees" / "cdg_epic"
        worktree_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "worktree", "add", str(worktree_path), "-b", "epic/cdg_epic", "develop"], cwd=sat_dir, check=True, capture_output=True)

        wt_dto = worktree_path / "src" / "api" / "dto" / "worker.py"
        wt_dto.parent.mkdir(parents=True, exist_ok=True)
        wt_dto.write_text("# worker in worktree", encoding="utf-8")

        hashes = {f: compute_file_hash(hub_domain / f) for f in CANONICAL_FILES}
        live_snapshot = compute_snapshot_id(hashes)
        main(["ack", "--repo-root", str(worktree_path), "--domain", "lyrics-sync", "--snapshot", live_snapshot, "--all-rfcs"])
        self._commit_all(worktree_path, "Worktree commit")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(worktree_path), "--json"])

        self.assertEqual(exit_code, 0)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["mode"], "satellite")

    def test_cdg_ar_02_dirty_tracked_working_tree_blocked(self) -> None:
        """[CDG-AR-02] Dirty Tracked Working Tree Fails Closed With Exit Code 2."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "lyrics-sync": {"paths": ["src/**"]}
            },
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        tracked_file = self.repo_root / "src" / "tracked.py"
        tracked_file.parent.mkdir(parents=True, exist_ok=True)
        tracked_file.write_text("# tracked", encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit")

        build_file = self.repo_root / "build" / "out.txt"
        build_file.parent.mkdir(parents=True, exist_ok=True)
        build_file.write_text("build artifact", encoding="utf-8")

        tracked_file.write_text("# dirty modification", encoding="utf-8")

        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])

        self.assertEqual(exit_code, 2)
        report = json.loads(stdout_buf.getvalue())
        self.assertEqual(report["status"], "BLOCKED")
        self.assertTrue(any("tracked" in b for b in report["blockers"]))

    def test_cdg_fr_01_missing_or_malformed_contract_map(self) -> None:
        """[CDG-FR-01] Missing or Malformed Contract Map at HEAD or Merge-Base Fails Closed With BLOCKED."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")
        self._commit_all(self.repo_root, "Initial commit without map")

        stdout_buf1 = io.StringIO()
        with patch("sys.stdout", stdout_buf1):
            exit_code1 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code1, 2)
        report1 = json.loads(stdout_buf1.getvalue())
        self.assertEqual(report1["status"], "BLOCKED")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        bad_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {"lyrics-sync": {"paths": ["src/**"]}},
            "waivers": [
                {"id": "DUP", "domain": "lyrics-sync", "paths": ["a"], "reason": "r1"},
                {"id": "DUP", "domain": "lyrics-sync", "paths": ["b"], "reason": "r2"},
            ],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(bad_map), encoding="utf-8")
        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code2, 2)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "BLOCKED")

        (agents_dir / "contract_map.json").write_text("{truncated_json...", encoding="utf-8")
        self._commit_all(self.repo_root, "Corrupt map at M")

        subprocess.run(["git", "checkout", "-b", "feat/corrupt-base"], cwd=self.repo_root, check=True, capture_output=True)
        valid_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {"lyrics-sync": {"paths": ["src/**"]}},
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(valid_map), encoding="utf-8")
        (self.repo_root / "src" / "a.py").parent.mkdir(parents=True, exist_ok=True)
        (self.repo_root / "src" / "a.py").write_text("# a", encoding="utf-8")
        self._commit_all(self.repo_root, "Fix map at HEAD and add file")

        stdout_buf3 = io.StringIO()
        with patch("sys.stdout", stdout_buf3):
            exit_code3 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code3, 2)
        report3 = json.loads(stdout_buf3.getvalue())
        self.assertEqual(report3["status"], "BLOCKED")

    def test_cdg_fr_02_unresolvable_base_ref_unlinked_domain_or_broken_topology(self) -> None:
        """[CDG-FR-02] Unresolvable Base-Ref, Satellite Unlinked Domain, or Broken Shared-Contracts Topology Fails Closed With BLOCKED."""
        self._init_git_repo(self.repo_root, "develop")
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")
        # Ensure GAP-08 is documented in gaps_and_rfcs.md
        gaps_file = hub_domain / "gaps_and_rfcs.md"
        gaps_content = gaps_file.read_text(encoding="utf-8") + "| GAP-08 | Telemetry metric | Satellite | Actionable Pending | 1.1.0 | No |\n"
        gaps_file.write_text(gaps_content, encoding="utf-8")

        agents_dir = self.repo_root / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        contract_map = {
            "schema_version": 1,
            "base_ref": "nonexistent_branch_12345",
            "domains": {"lyrics-sync": {"paths": ["src/**"]}},
            "waivers": [],
        }
        (agents_dir / "contract_map.json").write_text(json.dumps(contract_map, indent=2), encoding="utf-8")
        self._commit_all(self.repo_root, "Bad base_ref commit")

        stdout_buf1 = io.StringIO()
        with patch("sys.stdout", stdout_buf1):
            exit_code1 = main(["diff-check", "--repo-root", str(self.repo_root), "--json"])
        self.assertEqual(exit_code1, 2)
        report1 = json.loads(stdout_buf1.getvalue())
        self.assertEqual(report1["status"], "BLOCKED")

        sat_dir = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="sat_fr02_"))
        self._init_git_repo(sat_dir, "develop")
        rel_target = os.path.relpath(hub_domain, sat_dir)
        os.symlink(rel_target, sat_dir / "shared-contracts")

        sat_agents = sat_dir / ".agents"
        sat_agents.mkdir(parents=True, exist_ok=True)
        sat_bad_map = {
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {
                "different_domain": {"paths": ["src/**"]}
            },
            "waivers": [],
        }
        (sat_agents / "contract_map.json").write_text(json.dumps(sat_bad_map), encoding="utf-8")
        self._commit_all(sat_dir, "Satellite unlinked domain map")

        stdout_buf2 = io.StringIO()
        with patch("sys.stdout", stdout_buf2):
            exit_code2 = main(["diff-check", "--repo-root", str(sat_dir), "--json"])
        self.assertEqual(exit_code2, 2)
        report2 = json.loads(stdout_buf2.getvalue())
        self.assertEqual(report2["status"], "BLOCKED")

        dangling_sat = Path(tempfile.mkdtemp(dir=self.temp_dir.name, prefix="dang_sat_"))
        self._init_git_repo(dangling_sat, "develop")
        os.symlink("../nonexistent_hub_target", dangling_sat / "shared-contracts")
        dang_agents = dangling_sat / ".agents"
        dang_agents.mkdir(parents=True, exist_ok=True)
        (dang_agents / "contract_map.json").write_text(json.dumps({
            "schema_version": 1,
            "base_ref": "develop",
            "domains": {"lyrics-sync": {"paths": ["src/**"]}},
            "waivers": [],
        }), encoding="utf-8")
        self._commit_all(dangling_sat, "Dangling symlink init")

        stdout_buf3 = io.StringIO()
        with patch("sys.stdout", stdout_buf3):
            exit_code3 = main(["diff-check", "--repo-root", str(dangling_sat), "--json"])
        self.assertEqual(exit_code3, 2)
        report3 = json.loads(stdout_buf3.getvalue())
        self.assertEqual(report3["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
