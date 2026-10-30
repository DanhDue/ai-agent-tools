"""Unit and integration tests for sync-shared-contracts skill and CLI engine."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Enable direct import of sync_contracts module
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_contracts import (
    CANONICAL_FILES,
    ContractFormatError,
    main,
    parse_api_contract,
    parse_architecture_and_flow,
    parse_gaps_and_rfcs,
    render_brief,
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
        # 1. Test table format contract parsing
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

        # 2. Test narrative format contract parsing
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

        # 3. Test brief rendering
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
        self.assertIn("## 3. Architecture & Pipeline Invariants", brief)
        self.assertIn("Lease Acquisition", brief)
        self.assertIn("## 4. Actionable RFCs & Gaps Ledger", brief)
        self.assertIn("RFC-001", brief)
        self.assertIn("## 5. Lifecycle Execution Rules", brief)

        # 4. Test brief CLI command exits 0
        brief_out = self.repo_root / "brief.md"
        exit_code = main(["brief", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--output", str(brief_out)])
        self.assertEqual(exit_code, 0)
        self.assertTrue(brief_out.is_file())
        self.assertIn("Contract Requirements Brief: lyrics-sync", brief_out.read_text(encoding="utf-8"))

    def test_syc_ec_01_initial_sync_absent_watermark(self) -> None:
        """[SYC-EC-01] Initial Sync Detection When Watermark File Is Absent."""
        hub_domain = self.repo_root / "shared-contracts" / "lyrics-sync"
        self._scaffold_table_contracts(hub_domain, "lyrics-sync")

        # Verify .agents/contract_sync.json does not exist
        watermark = self.repo_root / ".agents" / "contract_sync.json"
        self.assertFalse(watermark.exists())

        # check --json without --strict should exit 0
        stdout_buf = io.StringIO()
        with patch("sys.stdout", stdout_buf):
            exit_code = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--json"])
        self.assertEqual(exit_code, 0)

        output_json = json.loads(stdout_buf.getvalue())
        self.assertEqual(output_json["status"], "INITIAL_SYNC")
        self.assertEqual(output_json["domain"], "lyrics-sync")
        self.assertEqual(output_json["deltas"]["changed_files"], list(CANONICAL_FILES))
        self.assertIn("POST /api/v1/lyrics-sync/tasks/claim", output_json["deltas"]["endpoints"])

        # check with --strict when absent should exit 1
        strict_exit = main(["check", "--repo-root", str(self.repo_root), "--domain", "lyrics-sync", "--strict"])
        self.assertEqual(strict_exit, 1)

    def test_unsupported_contract_format_raises(self) -> None:
        """Reject files with zero endpoints with exit 1."""
        unsupported_content = "# Empty contract with no endpoints\n"
        with self.assertRaises(ContractFormatError):
            parse_api_contract(unsupported_content)


if __name__ == "__main__":
    unittest.main()
