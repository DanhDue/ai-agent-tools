"""Unit and integration tests for sync-shared-contracts skill and CLI engine."""

from __future__ import annotations

import io
import json
import os
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
    compute_semantic_delta,
    main,
    parse_api_contract,
    parse_architecture_and_flow,
    parse_gaps_and_rfcs,
    render_brief,
    resolve_topology,
    scan_target_codebase,
    to_camel_case,
)


class TestSyncContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _scaffold_table_contracts(self, target_dir: Path, domain: str = "lyrics-sync") -> None:
        target_dir.mkdir(parents=True, exist_ok=True)
        # 1. api_contract.md (table format)
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

        # 2. architecture_and_flow.md
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

        # 3. gaps_and_rfcs.md (table format)
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
        # 1. api_contract.md (narrative format with HTML comment version and bullet endpoints)
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

        # 2. architecture_and_flow.md
        arch_content = f"""# Architecture: {domain}

### Step 1: Claim Lease
### Step 2: Validate
### Step 3: Compute
"""
        (target_dir / "architecture_and_flow.md").write_text(arch_content, encoding="utf-8")

        # 3. gaps_and_rfcs.md (narrative format)
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
        # Create src/worker_client.ts
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

        # Current contract has new key "retry_after_ms", type change integer -> string, and changed pipeline steps
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
        # Setup: primary repo satellite
        primary_satellite = self.repo_root / "primary_satellite"
        primary_satellite.mkdir(parents=True, exist_ok=True)

        hub_repo = self.repo_root / "Hub" / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_repo, "lyrics-sync")

        # Relative symlink from primary satellite root to Hub
        rel_to_hub = os.path.relpath(hub_repo, primary_satellite)
        os.symlink(rel_to_hub, primary_satellite / "shared-contracts")

        # Create nested worktree at .worktrees/sync_epic
        worktree_dir = primary_satellite / ".worktrees" / "sync_epic"
        worktree_dir.mkdir(parents=True, exist_ok=True)
        # In git worktrees, shared-contracts is checked out with identical symlink bytes
        os.symlink(rel_to_hub, worktree_dir / "shared-contracts")

        # Fake .git file in worktree pointing to primary
        (worktree_dir / ".git").write_text(f"gitdir: {primary_satellite}/.git/worktrees/sync_epic\n", encoding="utf-8")

        # Resolve topology from inside worktree
        topo = resolve_topology(worktree_dir, "lyrics-sync")
        self.assertEqual(topo["mode"], "satellite")
        self.assertEqual(topo["contract_dir"].resolve(), hub_repo.resolve())
        # Ensure tracked symlink inside worktree is not altered
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
        # 1. Dangling symlink
        os.symlink("../non_existent_hub", self.repo_root / "shared-contracts")
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("Dangling symlink", str(ctx.exception))
        os.unlink(self.repo_root / "shared-contracts")

        # 2. Missing canonical files
        (self.repo_root / "shared-contracts").mkdir(parents=True, exist_ok=True)
        (self.repo_root / "shared-contracts" / "api_contract.md").write_text("# API\n", encoding="utf-8")
        with self.assertRaises(TopologyError) as ctx:
            resolve_topology(self.repo_root, "lyrics-sync")
        self.assertIn("Missing canonical contract file", str(ctx.exception))

        # 3. Unsupported contract format (0 endpoints)
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


if __name__ == "__main__":
    unittest.main()
