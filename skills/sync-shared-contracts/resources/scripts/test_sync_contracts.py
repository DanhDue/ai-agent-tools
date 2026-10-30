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
    compute_file_hash,
    compute_semantic_delta,
    compute_snapshot_id,
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

        # Initial ack --all-rfcs -> IN_SYNC
        exit_code = main(["ack", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--all-rfcs"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"]), 0)

        # Hub updates api_contract.md and gaps_and_rfcs.md
        api_text = (hub_domain / "api_contract.md").read_text(encoding="utf-8")
        api_text = api_text.replace("1.2.0", "1.3.0") + "\n| POST | /api/v1/lyrics-sync/tasks/{id}/cancel | X-Worker-Token | Cancel task |\n"
        (hub_domain / "api_contract.md").write_text(api_text, encoding="utf-8")

        gaps_text = (hub_domain / "gaps_and_rfcs.md").read_text(encoding="utf-8")
        gaps_text += "| RFC-004 | Live websocket sync | Satellite | Open | 1.3.0 | No |\n"
        (hub_domain / "gaps_and_rfcs.md").write_text(gaps_text, encoding="utf-8")

        # check --strict reports DRIFT_DETECTED and exits 1
        strict_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"])
        self.assertEqual(strict_exit, 1)

        # Refresh snapshot ID
        refreshed_hashes = {fn: compute_file_hash(hub_domain / fn) for fn in CANONICAL_FILES}
        refreshed_snapshot_id = compute_snapshot_id(refreshed_hashes)

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


if __name__ == "__main__":
    unittest.main()
