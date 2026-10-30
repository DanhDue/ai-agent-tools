#!/usr/bin/env python3
"""Sync Shared Contracts CLI engine.

Automates continuous contract delta detection (check), requirements brief generation (brief),
and snapshot-bound / scope-bound watermark acknowledgement (ack) across Satellite and Hub repositories.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from string import Template
from typing import Any

CANONICAL_FILES = (
    "api_contract.md",
    "architecture_and_flow.md",
    "gaps_and_rfcs.md",
)

MAX_SYMLINK_HOPS = 10

PENDING_STATUSES = {"OPEN", "PROPOSED", "DRAFT", "IN REVIEW", "IN_REVIEW"}
ACTIVE_STATUSES = {"ACCEPTED", "APPROVED", "IMPLEMENTED"}
INACTIVE_STATUSES = {"SUPERSEDED", "REJECTED"}


class ContractFormatError(Exception):
    """Raised when a shared contract file cannot be recognized or parsed."""


def normalize_rfc_status(status_raw: str) -> tuple[str, str]:
    """Normalize raw RFC / Gap status into ACTIONABLE_PENDING, ACKNOWLEDGED_ACTIVE, or INACTIVE."""
    cleaned = status_raw.strip().strip("`").strip().upper()
    cleaned = cleaned.replace("-", "_")
    if cleaned in PENDING_STATUSES:
        return "ACTIONABLE_PENDING", cleaned
    if cleaned in ACTIVE_STATUSES:
        return "ACKNOWLEDGED_ACTIVE", cleaned
    if cleaned in INACTIVE_STATUSES:
        return "INACTIVE", cleaned
    return "ACTIONABLE_PENDING", cleaned


def extract_json_fields(data: Any, prefix: str = "") -> tuple[list[str], dict[str, str]]:
    """Extract flat keys and dotted field paths with normalized JSON types from parsed JSON."""
    flat_keys: set[str] = set()
    dotted_fields: dict[str, str] = {}

    if isinstance(data, dict):
        for k, v in data.items():
            flat_keys.add(k)
            curr_path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, bool):
                dotted_fields[curr_path] = "boolean"
            elif isinstance(v, int):
                dotted_fields[curr_path] = "integer"
            elif isinstance(v, float):
                dotted_fields[curr_path] = "number"
            elif isinstance(v, str):
                dotted_fields[curr_path] = "string"
            elif isinstance(v, list):
                dotted_fields[curr_path] = "array"
                # If list of dicts, inspect first element for structure
                if v and isinstance(v[0], dict):
                    child_keys, child_fields = extract_json_fields(v[0], curr_path)
                    flat_keys.update(child_keys)
                    dotted_fields.update(child_fields)
            elif isinstance(v, dict):
                dotted_fields[curr_path] = "object"
                child_keys, child_fields = extract_json_fields(v, curr_path)
                flat_keys.update(child_keys)
                dotted_fields.update(child_fields)
            else:
                dotted_fields[curr_path] = "unknown"
    return sorted(flat_keys), dotted_fields


def parse_api_contract(content: str) -> dict[str, Any]:
    """Parse api_contract.md supporting both table and narrative formats."""
    # 1. Version extraction
    version = "1.0.0"
    m_comment = re.search(r"<!--.*?Version:\s*([0-9]+\.[0-9]+\.[0-9]+).*?-->", content, re.DOTALL | re.IGNORECASE)
    if m_comment:
        version = m_comment.group(1)
    else:
        m_bullet = re.search(r"[-*]\s+\*\*Version\*\*:\s*[`']?([0-9]+\.[0-9]+\.[0-9]+)[`']?", content)
        if m_bullet:
            version = m_bullet.group(1)

    # 2. Authentication headers
    headers: set[str] = set()
    # Table headers: | Header | Type | Required | Description |
    in_header_table = False
    for line in content.splitlines():
        line_s = line.strip()
        if re.search(r"^\|\s*Header\s*\|\s*Type\s*\|", line_s, re.IGNORECASE):
            in_header_table = True
            continue
        if in_header_table:
            if line_s.startswith(("|---", "|:--")):
                continue
            if line_s.startswith("|"):
                parts = [p.strip().strip("`") for p in line_s.split("|")[1:-1]]
                if parts and parts[0]:
                    headers.add(parts[0])
            else:
                in_header_table = False

    # HTTP blocks: Authorization: ..., X-Worker-Token: ...
    for m in re.finditer(r"(?:^|\n)([A-Za-z0-9_-]+Token|[A-Za-z0-9_-]+ID|Authorization|X-[A-Za-z0-9_-]+):", content):
        headers.add(m.group(1))

    # 3. Endpoints extraction
    endpoints: set[str] = set()
    # Table endpoints: | Method | Endpoint | Auth | Purpose |
    in_endpoint_table = False
    for line in content.splitlines():
        line_s = line.strip()
        if re.search(r"^\|\s*Method\s*\|\s*(?:Endpoint|Path)\s*\|", line_s, re.IGNORECASE):
            in_endpoint_table = True
            continue
        if in_endpoint_table:
            if line_s.startswith(("|---", "|:--")):
                continue
            if line_s.startswith("|"):
                parts = [p.strip().strip("`") for p in line_s.split("|")[1:-1]]
                if len(parts) >= 2 and parts[0] and parts[1]:
                    method = parts[0].upper()
                    path = parts[1]
                    if method in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"} and path.startswith("/"):
                        endpoints.add(f"{method} {path}")
            else:
                in_endpoint_table = False

    # Narrative endpoints:
    # Heading: ### ... (POST /api/v1/...)
    for m in re.finditer(r"###\s+.*?\(\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^\s\)]+)\s*\)", content):
        method = m.group(1).upper()
        path = m.group(2)
        if path.startswith("/"):
            endpoints.add(f"{method} {path}")

    # Narrative bullets: * **Method**: POST \n * **Path**: /api/v1/...
    blocks = re.split(r"\n(?=###?\s)", content)
    for block in blocks:
        method_match = re.search(r"[-*]\s+\*\*Method\*\*:\s*[`']?(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)[`']?", block, re.IGNORECASE)
        path_match = re.search(r"[-*]\s+\*\*Path\*\*:\s*[`']?(/[^`'\s]+)[`']?", block)
        if method_match and path_match:
            endpoints.add(f"{method_match.group(1).upper()} {path_match.group(1)}")

    if not endpoints:
        raise ContractFormatError("UNSUPPORTED_CONTRACT_FORMAT: zero recognizable endpoints found in api_contract.md")

    # 4. JSON payload schemas
    payload_keys: set[str] = set()
    payload_fields: dict[str, str] = {}

    json_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    for j_text in json_blocks:
        # Sanitize template variables before parsing (e.g. "$domain" -> "domain")
        sanitized = re.sub(r'\$([a-zA-Z0-9_]+)', r'\1', j_text)
        try:
            parsed_json = json.loads(sanitized)
            keys, fields = extract_json_fields(parsed_json)
            payload_keys.update(keys)
            payload_fields.update(fields)
        except json.JSONDecodeError:
            # Fallback regex for keys in malformed json blocks
            for k in re.findall(r'"([a-zA-Z0-9_]+)"\s*:', sanitized):
                payload_keys.add(k)

    return {
        "version": version,
        "headers": sorted(headers),
        "endpoints": sorted(endpoints),
        "payload_keys": sorted(payload_keys),
        "payload_fields": dict(sorted(payload_fields.items())),
    }


def parse_architecture_and_flow(content: str) -> dict[str, Any]:
    """Parse architecture_and_flow.md extracting canonical pipeline steps and state transitions."""
    steps: list[str] = []
    # 1. Numbered pipeline steps: e.g. "1. **Lease Acquisition**: ..." or "1. **Step**: ..."
    for line in content.splitlines():
        line_s = line.strip()
        m_step = re.match(r"^\d+\.\s+\*\*([^*]+)\*\*:", line_s)
        if m_step:
            steps.append(m_step.group(1).strip())
        else:
            m_hstep = re.match(r"^###?\s+Step\s+\d+:\s*(.*)", line_s, re.IGNORECASE)
            if m_hstep:
                steps.append(m_hstep.group(1).strip())

    # State transitions from mermaid blocks
    transitions: list[str] = []
    for line in content.splitlines():
        line_s = line.strip()
        m_trans = re.search(r"([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)(?::\s*(.*))?", line_s)
        if m_trans:
            src = m_trans.group(1)
            dst = m_trans.group(2)
            desc = f" ({m_trans.group(3).strip()})" if m_trans.group(3) else ""
            if src != "[*]" and dst != "[*]":
                transitions.append(f"{src} -> {dst}{desc}")

    return {
        "pipeline_steps": steps,
        "state_transitions": transitions,
    }


def parse_gaps_and_rfcs(content: str) -> dict[str, Any]:
    """Parse gaps_and_rfcs.md extracting RFC and Gap entries with normalized statuses."""
    rfcs: dict[str, dict[str, str]] = {}

    # 1. Table format: | RFC ID | Title | Proposing Repo | Status | Target Release | Breaking? |
    in_table = False
    for line in content.splitlines():
        line_s = line.strip()
        if re.search(r"^\|\s*RFC\s+ID\s*\|\s*Title\s*\|", line_s, re.IGNORECASE):
            in_table = True
            continue
        if in_table:
            if line_s.startswith(("|---", "|:--")):
                continue
            if line_s.startswith("|"):
                parts = [p.strip().strip("`") for p in line_s.split("|")[1:-1]]
                if len(parts) >= 4 and parts[0] and parts[1]:
                    rfc_id = parts[0]
                    title = parts[1]
                    raw_status = parts[3]
                    norm_status, raw_norm = normalize_rfc_status(raw_status)
                    rfcs[rfc_id] = {
                        "status": norm_status,
                        "raw_status": raw_norm,
                        "title": title,
                    }
            else:
                in_table = False

    # 2. Narrative format: ### GAP-XX: Title or ### RFC-XXX: Title
    sections = re.split(r"\n(?=###?\s+(?:GAP|RFC)[-_A-Za-z0-9]+)", content)
    for sec in sections:
        header_match = re.search(r"^###?\s+((?:GAP|RFC)[-_A-Za-z0-9]+):\s*(.*)", sec.strip(), re.MULTILINE)
        if header_match:
            rfc_id = header_match.group(1).strip()
            title = header_match.group(2).strip()
            status_match = re.search(r"[-*]\s+\*\*Status\*\*:\s*[`']?([^`'\n]+)[`']?", sec, re.IGNORECASE)
            raw_status = status_match.group(1).strip() if status_match else "OPEN"
            norm_status, raw_norm = normalize_rfc_status(raw_status)
            rfcs[rfc_id] = {
                "status": norm_status,
                "raw_status": raw_norm,
                "title": title,
            }

    return {"rfcs": rfcs}


def compute_file_hash(path: Path) -> str:
    """Compute sha256 checksum for a file."""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def compute_snapshot_id(file_hashes: dict[str, str]) -> str:
    """Compute composite snapshot_id from canonical file hashes."""
    combined = ":".join(file_hashes.get(fn, "") for fn in sorted(CANONICAL_FILES))
    digest = hashlib.sha256(combined.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def render_brief(
    template_path: Path,
    domain: str,
    mode: str,
    sync_status: str,
    snapshot_id: str,
    previous_version: str,
    current_version: str,
    hub_commit_range: str,
    changed_files: list[str],
    endpoints: list[str],
    payload_keys: list[str],
    payload_fields: dict[str, str],
    pipeline_steps: list[str],
    rfcs: dict[str, dict[str, str]],
    heuristic_results: dict[str, str] | None = None,
) -> str:
    """Render canonical delta brief using string.Template."""
    if not template_path.is_file():
        raise FileNotFoundError(f"Template not found at {template_path}")

    template_content = template_path.read_text(encoding="utf-8")
    tmpl = Template(template_content)

    # Changed files summary
    if changed_files:
        changed_summary = "\n".join(f"- `{f}`" for f in changed_files)
    else:
        changed_summary = "- _None (all canonical files identical)_"

    # Endpoints section
    ep_lines: list[str] = []
    for ep in endpoints:
        status_tag = f" — `{heuristic_results.get(ep, 'UNVERIFIED')}`" if heuristic_results else ""
        ep_lines.append(f"- `{ep}`{status_tag}")
    endpoints_section = "\n".join(ep_lines) if ep_lines else "- _No endpoints declared_"

    # Payload keys section
    pk_lines: list[str] = []
    for k in payload_keys:
        f_type = payload_fields.get(k, "any")
        status_tag = f" — `{heuristic_results.get(k, 'UNVERIFIED')}`" if heuristic_results else ""
        pk_lines.append(f"- `{k}` (`{f_type}`){status_tag}")
    payload_keys_section = "\n".join(pk_lines) if pk_lines else "- _No payload fields declared_"

    # Pipeline steps
    ps_lines: list[str] = [f"{i+1}. **{step}**" for i, step in enumerate(pipeline_steps)]
    pipeline_steps_section = "\n".join(ps_lines) if ps_lines else "- _No pipeline steps declared_"

    # RFCs section
    rfc_lines: list[str] = []
    for rfc_id, info in rfcs.items():
        rfc_lines.append(f"- **{rfc_id}**: {info.get('title', '')} [`{info.get('raw_status', '')}` -> `{info.get('status', '')}`]")
    rfcs_section = "\n".join(rfc_lines) if rfc_lines else "- _No active RFCs or gaps logged_"

    # Lifecycle rules section
    rules = [
        "1. **dev-brainstorming (Stage 1)**: Ground spec on this brief's API & Schema Requirements without re-opening settled contracts.",
        "2. **dev-designer (Stage 2)**: If in Hub mode, enforce task_01 contract-first update followed by post-task_01 snapshot refresh; if in Satellite mode, treat shared-contracts as read-only.",
        f"3. **dev-implementation (Stage 3)**: Verify completion with `sync_contracts.py ack --snapshot {snapshot_id} [--rfc <ID> ... | --all-rfcs]` followed by `check --strict`.",
        "4. **finishing-a-development-branch (Stage 4)**: Archive completed epic artifacts into `.devtool/epic/<epic_slug>/` upon merge.",
    ]
    lifecycle_rules_section = "\n".join(rules)

    return tmpl.substitute(
        domain=domain,
        mode=mode,
        sync_status=sync_status,
        snapshot_id=snapshot_id,
        previous_version=previous_version,
        current_version=current_version,
        hub_commit_range=hub_commit_range,
        changed_files_summary=changed_summary,
        endpoints_section=endpoints_section,
        payload_keys_section=payload_keys_section,
        pipeline_steps_section=pipeline_steps_section,
        rfcs_section=rfcs_section,
        lifecycle_rules_section=lifecycle_rules_section,
    )


def cmd_check(args: argparse.Namespace) -> int:
    """Execute check subcommand."""
    repo_root = Path(args.repo_root or os.getcwd()).resolve()
    domain = args.domain or "default"
    strict = getattr(args, "strict", False)
    as_json = getattr(args, "json", False)

    shared_contracts = repo_root / "shared-contracts"
    if not shared_contracts.exists():
        msg = f"ERROR: shared-contracts not found in {repo_root}. Run setup_contracts.py first."
        if as_json:
            print(json.dumps({"status": "ERROR", "error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1

    # Check canonical contract files
    contract_dir = shared_contracts / domain if (shared_contracts / domain).is_dir() else shared_contracts
    for fn in CANONICAL_FILES:
        fp = contract_dir / fn
        if not fp.is_file():
            msg = f"ERROR: canonical contract file {fn} missing in {contract_dir}"
            if as_json:
                print(json.dumps({"status": "ERROR", "error": msg}))
            else:
                print(msg, file=sys.stderr)
            return 1

    # Compute hashes & parse
    file_hashes: dict[str, str] = {}
    for fn in CANONICAL_FILES:
        file_hashes[fn] = compute_file_hash(contract_dir / fn)
    snapshot_id = compute_snapshot_id(file_hashes)

    try:
        api_data = parse_api_contract((contract_dir / "api_contract.md").read_text(encoding="utf-8"))
        arch_data = parse_architecture_and_flow((contract_dir / "architecture_and_flow.md").read_text(encoding="utf-8"))
        gaps_data = parse_gaps_and_rfcs((contract_dir / "gaps_and_rfcs.md").read_text(encoding="utf-8"))
    except ContractFormatError as exc:
        msg = f"ERROR: {exc}"
        if as_json:
            print(json.dumps({"status": "ERROR", "error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1

    watermark_path = repo_root / ".agents" / "contract_sync.json"
    if not watermark_path.is_file():
        # INITIAL_SYNC state
        report: dict[str, Any] = {
            "status": "INITIAL_SYNC",
            "domain": domain,
            "snapshot_id": snapshot_id,
            "version": api_data["version"],
            "deltas": {
                "changed_files": list(CANONICAL_FILES),
                "endpoints": api_data["endpoints"],
                "payload_keys": api_data["payload_keys"],
                "payload_fields": api_data["payload_fields"],
                "pipeline_steps": arch_data["pipeline_steps"],
                "rfcs": gaps_data["rfcs"],
            },
        }
        if as_json:
            print(json.dumps(report, indent=2))
        else:
            print(f"Domain '{domain}' status: INITIAL_SYNC (watermark absent)")
            print(f"Snapshot ID: {snapshot_id}")
            print(f"Contract Version: {api_data['version']}")
            print(f"Unsynced files: {', '.join(CANONICAL_FILES)}")
        return 1 if strict else 0

    # Load watermark
    try:
        watermark = json.loads(watermark_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Corrupted JSON fallback
        if as_json:
            print(json.dumps({"status": "INITIAL_SYNC", "warning": "Corrupted watermark JSON"}))
        else:
            print("Warning: corrupted watermark JSON, falling back to INITIAL_SYNC", file=sys.stderr)
        return 1 if strict else 0

    dom_data = watermark.get("domains", {}).get(domain)
    if not dom_data:
        return 1 if strict else 0

    # In Task 1 baseline check
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    """Execute brief subcommand."""
    repo_root = Path(args.repo_root or os.getcwd()).resolve()
    domain = args.domain or "default"
    shared_contracts = repo_root / "shared-contracts"
    contract_dir = shared_contracts / domain if (shared_contracts / domain).is_dir() else shared_contracts

    if not contract_dir.is_dir():
        print(f"ERROR: contract directory {contract_dir} not found", file=sys.stderr)
        return 1

    file_hashes: dict[str, str] = {}
    for fn in CANONICAL_FILES:
        fp = contract_dir / fn
        if not fp.is_file():
            print(f"ERROR: canonical file {fn} missing", file=sys.stderr)
            return 1
        file_hashes[fn] = compute_file_hash(fp)
    snapshot_id = compute_snapshot_id(file_hashes)

    try:
        api_data = parse_api_contract((contract_dir / "api_contract.md").read_text(encoding="utf-8"))
        arch_data = parse_architecture_and_flow((contract_dir / "architecture_and_flow.md").read_text(encoding="utf-8"))
        gaps_data = parse_gaps_and_rfcs((contract_dir / "gaps_and_rfcs.md").read_text(encoding="utf-8"))
    except ContractFormatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    template_path = Path(__file__).parent.parent / "templates" / "contract_delta_brief.md.tmpl"
    brief_md = render_brief(
        template_path=template_path,
        domain=domain,
        mode="hub" if not shared_contracts.is_symlink() else "satellite",
        sync_status="INITIAL_SYNC",
        snapshot_id=snapshot_id,
        previous_version="none",
        current_version=api_data["version"],
        hub_commit_range="HEAD",
        changed_files=list(CANONICAL_FILES),
        endpoints=api_data["endpoints"],
        payload_keys=api_data["payload_keys"],
        payload_fields=api_data["payload_fields"],
        pipeline_steps=arch_data["pipeline_steps"],
        rfcs=gaps_data["rfcs"],
    )

    if args.output:
        out_path = Path(args.output).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(brief_md, encoding="utf-8")
        print(f"Requirements brief written to {out_path}")
    else:
        print(brief_md)

    return 0


def cmd_ack(args: argparse.Namespace) -> int:
    """Execute ack subcommand (stub for Task 1, full in Task 3)."""
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI main entrypoint."""
    parser = argparse.ArgumentParser(description="Sync Shared Contracts CLI")
    subparsers = parser.add_subparsers(dest="command")

    # check
    p_check = subparsers.add_parser("check", help="Check contract drift")
    p_check.add_argument("--repo-root", type=str, help="Repository root path")
    p_check.add_argument("--domain", type=str, default="lyrics-sync", help="Contract domain name")
    p_check.add_argument("--json", action="store_true", help="Emit JSON output")
    p_check.add_argument("--strict", action="store_true", help="Exit 1 if drift detected")
    p_check.add_argument("--rfc", action="append", help="Target RFC ID for scoped check")

    # brief
    p_brief = subparsers.add_parser("brief", help="Generate Contract Requirements Brief")
    p_brief.add_argument("--repo-root", type=str, help="Repository root path")
    p_brief.add_argument("--domain", type=str, default="lyrics-sync", help="Contract domain name")
    p_brief.add_argument("--output", type=str, help="Output markdown path")

    # ack
    p_ack = subparsers.add_parser("ack", help="Acknowledge contract watermark")
    p_ack.add_argument("--repo-root", type=str, help="Repository root path")
    p_ack.add_argument("--domain", type=str, default="lyrics-sync", help="Contract domain name")
    p_ack.add_argument("--snapshot", type=str, help="Expected snapshot ID")
    p_ack.add_argument("--rfc", action="append", help="RFC ID to acknowledge")
    p_ack.add_argument("--all-rfcs", action="store_true", help="Acknowledge all RFCs")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1

    if args.command == "check":
        return cmd_check(args)
    if args.command == "brief":
        return cmd_brief(args)
    if args.command == "ack":
        return cmd_ack(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
