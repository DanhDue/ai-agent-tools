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

SOURCE_EXTENSIONS = {
    ".py",
    ".rs",
    ".dart",
    ".kt",
    ".kts",
    ".swift",
    ".ts",
    ".tsx",
    ".js",
    ".go",
    ".java",
    ".yaml",
    ".yml",
    ".json",
}

EXCLUDED_DIRS = {
    ".git",
    ".worktrees",
    "shared-contracts",
    ".devtool",
    ".agents",
    "node_modules",
    "build",
    "dist",
    "target",
    ".dart_tool",
    "__pycache__",
}

PENDING_STATUSES = {"OPEN", "PROPOSED", "DRAFT", "IN REVIEW", "IN_REVIEW"}
ACTIVE_STATUSES = {"ACCEPTED", "APPROVED", "IMPLEMENTED"}
INACTIVE_STATUSES = {"SUPERSEDED", "REJECTED"}


class ContractFormatError(Exception):
    """Raised when a shared contract file cannot be recognized or parsed."""


class TopologyError(Exception):
    """Raised when shared-contracts topology is missing, broken, or cyclic."""


def to_camel_case(snake_str: str) -> str:
    """Convert snake_case string to camelCase."""
    parts = snake_str.split("_")
    if len(parts) <= 1:
        return snake_str
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


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

    for m in re.finditer(r"(?:^|\n)([A-Za-z0-9_-]+Token|[A-Za-z0-9_-]+ID|Authorization|X-[A-Za-z0-9_-]+):", content):
        headers.add(m.group(1))

    # 3. Endpoints extraction
    endpoints: set[str] = set()
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

    for m in re.finditer(r"###\s+.*?\(\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^\s\)]+)\s*\)", content):
        method = m.group(1).upper()
        path = m.group(2)
        if path.startswith("/"):
            endpoints.add(f"{method} {path}")

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
        sanitized = re.sub(r'\$([a-zA-Z0-9_]+)', r'\1', j_text)
        try:
            parsed_json = json.loads(sanitized)
            keys, fields = extract_json_fields(parsed_json)
            payload_keys.update(keys)
            payload_fields.update(fields)
        except json.JSONDecodeError:
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
    for line in content.splitlines():
        line_s = line.strip()
        m_step = re.match(r"^\d+\.\s+\*\*([^*]+)\*\*:", line_s)
        if m_step:
            steps.append(m_step.group(1).strip())
        else:
            m_hstep = re.match(r"^###?\s+Step\s+\d+:\s*(.*)", line_s, re.IGNORECASE)
            if m_hstep:
                steps.append(m_hstep.group(1).strip())

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


def find_primary_repo_root(worktree_root: Path) -> Path | None:
    """Locate primary git checkout root when invoked inside a git worktree."""
    git_entry = worktree_root / ".git"
    if git_entry.is_file():
        # Read gitdir line
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
            m = re.match(r"^gitdir:\s*(.*)", content)
            if m:
                gitdir = Path(m.group(1).strip())
                # If gitdir is like /repo/.git/worktrees/<name>, primary root is /repo
                if ".git" in gitdir.parts:
                    git_idx = gitdir.parts.index(".git")
                    return Path(*gitdir.parts[:git_idx])
        except OSError:
            pass

    # Check if .worktrees is an ancestor directory
    for parent in [worktree_root] + list(worktree_root.parents):
        if parent.name == ".worktrees" and parent.parent.is_dir():
            return parent.parent

    return None


def resolve_topology(repo_root: Path, domain: str = "lyrics-sync") -> dict[str, Any]:
    """Resolve shared-contracts topology across Satellite symlinks, worktrees, and Hub physical mode."""
    shared_contracts = repo_root / "shared-contracts"

    if not shared_contracts.exists() and not shared_contracts.is_symlink():
        raise TopologyError(f"shared-contracts not found in {repo_root}. Initialize or link contracts with setup_contracts.py")

    mode = "hub"
    contract_dir: Path | None = None

    if shared_contracts.is_symlink():
        mode = "satellite"
        # Check circular symlink chain
        curr = shared_contracts
        hops = 0
        visited: set[str] = set()
        while curr.is_symlink():
            hops += 1
            if hops > MAX_SYMLINK_HOPS:
                raise TopologyError(f"Symbolic link loop detected: exceeded {MAX_SYMLINK_HOPS} hops resolving {shared_contracts}")
            try:
                target_raw = os.readlink(curr)
            except OSError as err:
                raise TopologyError(f"Cannot read symlink {curr}: {err}") from err

            resolved_path = (curr.parent / target_raw).resolve()
            if str(resolved_path) in visited:
                raise TopologyError(f"Symbolic link loop detected: cycle at {resolved_path}")
            visited.add(str(resolved_path))

            # Next hop if target is another symlink
            if resolved_path.is_symlink():
                curr = resolved_path
            else:
                break

        # Check if direct resolution exists
        raw_target = os.readlink(shared_contracts)
        direct_target = (repo_root / raw_target).resolve()
        if direct_target.is_dir():
            contract_dir = direct_target
        else:
            # Fallback: Worktree-Aware relative symlink resolution via primary repo root
            primary_root = find_primary_repo_root(repo_root)
            if primary_root:
                fallback_target = (primary_root / raw_target).resolve()
                if fallback_target.is_dir():
                    contract_dir = fallback_target
                else:
                    raise TopologyError(f"Dangling symlink: {shared_contracts} -> {raw_target} does not resolve in {repo_root} or primary root {primary_root}")
            else:
                raise TopologyError(f"Dangling symlink: {shared_contracts} -> {raw_target} does not resolve")
    else:
        # Hub physical directory
        mode = "hub"
        if (shared_contracts / domain).is_dir():
            contract_dir = (shared_contracts / domain).resolve()
        else:
            contract_dir = shared_contracts.resolve()

    if not contract_dir or not contract_dir.is_dir():
        raise TopologyError(f"Contract directory could not be resolved in {repo_root}")

    # Validate 3 canonical contract files exist
    for fn in CANONICAL_FILES:
        fp = contract_dir / fn
        if not fp.is_file():
            raise TopologyError(f"Missing canonical contract file: {fn} in {contract_dir}")

    # Validate recognizable contract format
    api_text = (contract_dir / "api_contract.md").read_text(encoding="utf-8")
    try:
        parse_api_contract(api_text)
    except ContractFormatError as exc:
        raise TopologyError(str(exc)) from exc

    return {
        "mode": mode,
        "contract_dir": contract_dir,
        "domain": domain,
        "repo_root": repo_root,
    }


def scan_target_codebase(
    repo_root: Path,
    endpoints: list[str],
    headers: list[str],
    payload_keys: list[str],
) -> dict[str, str]:
    """Scan target codebase source files to classify endpoints, headers, and keys as FOUND_IN_CODE or MISSING_IN_CODE."""
    # Pre-parse endpoints to extract static route segments
    # e.g. "POST /api/v1/lyrics-sync/tasks/{id}/progress" -> static segments ["/api/v1/lyrics-sync/tasks", "/progress"]
    endpoint_segments: dict[str, list[str]] = {}
    for ep in endpoints:
        path = ep.split()[1] if " " in ep else ep
        # Split on param templates like {id}
        parts = [seg.strip("/") for seg in re.split(r"\{[^}]+\}", path) if seg.strip("/")]
        endpoint_segments[ep] = parts

    # Build key variants (snake_case and camelCase)
    key_variants: dict[str, set[str]] = {}
    for k in payload_keys:
        variants = {k, to_camel_case(k)}
        key_variants[k] = variants

    found_segments: set[str] = set()
    found_headers: set[str] = set()
    found_keys: set[str] = set()

    for root, dirs, files in os.walk(repo_root):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

        for file in files:
            ext = Path(file).suffix.lower()
            if ext not in SOURCE_EXTENSIONS:
                continue

            fp = Path(root) / file
            try:
                content = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            # Check headers
            for h in headers:
                if h in content:
                    found_headers.add(h)

            # Check keys
            for orig_key, var_set in key_variants.items():
                if orig_key not in found_keys:
                    for var in var_set:
                        if var in content:
                            found_keys.add(orig_key)
                            break

            # Check endpoint segments
            for seg_list in endpoint_segments.values():
                for seg in seg_list:
                    if seg in content:
                        found_segments.add(seg)

    results: dict[str, str] = {}
    for ep, seg_list in endpoint_segments.items():
        if seg_list and all(seg in found_segments for seg in seg_list):
            results[ep] = "FOUND_IN_CODE"
        else:
            results[ep] = "MISSING_IN_CODE"

    for h in headers:
        results[h] = "FOUND_IN_CODE" if h in found_headers else "MISSING_IN_CODE"

    for k in payload_keys:
        results[k] = "FOUND_IN_CODE" if k in found_keys else "MISSING_IN_CODE"

    return results


def compute_semantic_delta(
    current_data: dict[str, Any],
    baseline_snapshot: dict[str, Any],
) -> dict[str, Any]:
    """Compute semantic diff between current contract structures and baseline_snapshot."""
    cur_ep: set[str] = set(current_data.get("endpoints", []))
    base_ep: set[str] = set(baseline_snapshot.get("endpoints", []))
    added_ep = sorted(cur_ep - base_ep)
    removed_ep = sorted(base_ep - cur_ep)

    cur_keys: set[str] = set(current_data.get("payload_keys", []))
    base_keys: set[str] = set(baseline_snapshot.get("payload_keys", []))
    added_keys = sorted(cur_keys - base_keys)
    removed_keys = sorted(base_keys - cur_keys)

    cur_fields: dict[str, str] = current_data.get("payload_fields", {})
    base_fields: dict[str, str] = baseline_snapshot.get("payload_fields", {})

    modified_fields: list[str] = []
    for k, cur_type in cur_fields.items():
        if k in base_fields:
            base_type = base_fields[k]
            if base_type != cur_type:
                modified_fields.append(f"{k}: {base_type} -> {cur_type}")

    cur_steps: list[str] = current_data.get("pipeline_steps", [])
    base_steps: list[str] = baseline_snapshot.get("pipeline_steps", [])
    modified_steps: list[str] = []
    if cur_steps != base_steps:
        modified_steps = [f"Pipeline steps changed from {len(base_steps)} to {len(cur_steps)} step(s)"]

    return {
        "added_endpoints": added_ep,
        "removed_endpoints": removed_ep,
        "added_keys": added_keys,
        "removed_keys": removed_keys,
        "modified_field_types": modified_fields,
        "modified_pipeline_steps": modified_steps,
    }


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

    if changed_files:
        changed_summary = "\n".join(f"- `{f}`" for f in changed_files)
    else:
        changed_summary = "- _None (all canonical files identical)_"

    ep_lines: list[str] = []
    for ep in endpoints:
        status_tag = f" — `{heuristic_results.get(ep, 'UNVERIFIED')}`" if heuristic_results else ""
        ep_lines.append(f"- `{ep}`{status_tag}")
    endpoints_section = "\n".join(ep_lines) if ep_lines else "- _No endpoints declared_"

    pk_lines: list[str] = []
    for k in payload_keys:
        f_type = payload_fields.get(k, "any")
        status_tag = f" — `{heuristic_results.get(k, 'UNVERIFIED')}`" if heuristic_results else ""
        pk_lines.append(f"- `{k}` (`{f_type}`){status_tag}")
    payload_keys_section = "\n".join(pk_lines) if pk_lines else "- _No payload fields declared_"

    ps_lines: list[str] = [f"{i+1}. **{step}**" for i, step in enumerate(pipeline_steps)]
    pipeline_steps_section = "\n".join(ps_lines) if ps_lines else "- _No pipeline steps declared_"

    rfc_lines: list[str] = []
    for rfc_id, info in rfcs.items():
        rfc_lines.append(f"- **{rfc_id}**: {info.get('title', '')} [`{info.get('raw_status', '')}` -> `{info.get('status', '')}`]")
    rfcs_section = "\n".join(rfc_lines) if rfc_lines else "- _No active RFCs or gaps logged_"

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
    domain = args.domain or "lyrics-sync"
    strict = getattr(args, "strict", False)
    as_json = getattr(args, "json", False)

    try:
        topo = resolve_topology(repo_root, domain)
    except TopologyError as exc:
        msg = f"ERROR: {exc}"
        if as_json:
            print(json.dumps({"status": "ERROR", "error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1

    contract_dir = topo["contract_dir"]
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

    try:
        watermark = json.loads(watermark_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        if as_json:
            print(json.dumps({"status": "INITIAL_SYNC", "warning": "Corrupted watermark JSON"}))
        else:
            print("Warning: corrupted watermark JSON, falling back to INITIAL_SYNC", file=sys.stderr)
        return 1 if strict else 0

    dom_data = watermark.get("domains", {}).get(domain)
    if not dom_data:
        return 1 if strict else 0

    # Semantic comparison against baseline_snapshot
    baseline_snapshot = dom_data.get("baseline_snapshot", {})
    current_contract_snapshot = {
        "endpoints": api_data["endpoints"],
        "headers": api_data["headers"],
        "payload_keys": api_data["payload_keys"],
        "payload_fields": api_data["payload_fields"],
        "pipeline_steps": arch_data["pipeline_steps"],
        "rfcs": gaps_data["rfcs"],
    }
    semantic_deltas = compute_semantic_delta(current_contract_snapshot, baseline_snapshot)

    has_drift = (
        snapshot_id != dom_data.get("snapshot_id")
        or bool(semantic_deltas["added_endpoints"])
        or bool(semantic_deltas["removed_endpoints"])
        or bool(semantic_deltas["added_keys"])
        or bool(semantic_deltas["modified_field_types"])
        or bool(semantic_deltas["modified_pipeline_steps"])
        or bool(dom_data.get("pending_rfcs", []))
    )

    if as_json:
        out = {
            "status": "DRIFT_DETECTED" if has_drift else "IN_SYNC",
            "domain": domain,
            "snapshot_id": snapshot_id,
            "deltas": semantic_deltas,
        }
        print(json.dumps(out, indent=2))
    else:
        status_str = "DRIFT_DETECTED" if has_drift else "IN_SYNC"
        print(f"Domain '{domain}' status: {status_str}")

    return 1 if (strict and has_drift) else 0


def cmd_brief(args: argparse.Namespace) -> int:
    """Execute brief subcommand."""
    repo_root = Path(args.repo_root or os.getcwd()).resolve()
    domain = args.domain or "lyrics-sync"

    try:
        topo = resolve_topology(repo_root, domain)
    except TopologyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    contract_dir = topo["contract_dir"]
    file_hashes: dict[str, str] = {}
    for fn in CANONICAL_FILES:
        file_hashes[fn] = compute_file_hash(contract_dir / fn)
    snapshot_id = compute_snapshot_id(file_hashes)

    try:
        api_data = parse_api_contract((contract_dir / "api_contract.md").read_text(encoding="utf-8"))
        arch_data = parse_architecture_and_flow((contract_dir / "architecture_and_flow.md").read_text(encoding="utf-8"))
        gaps_data = parse_gaps_and_rfcs((contract_dir / "gaps_and_rfcs.md").read_text(encoding="utf-8"))
    except ContractFormatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    # Run heuristic scan across repo_root
    heuristic_results = scan_target_codebase(
        repo_root=repo_root,
        endpoints=api_data["endpoints"],
        headers=api_data["headers"],
        payload_keys=api_data["payload_keys"],
    )

    template_path = Path(__file__).parent.parent / "templates" / "contract_delta_brief.md.tmpl"
    brief_md = render_brief(
        template_path=template_path,
        domain=domain,
        mode=topo["mode"],
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
        heuristic_results=heuristic_results,
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
    """Execute ack subcommand (stub for Task 2, completed in Task 3)."""
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI main entrypoint."""
    parser = argparse.ArgumentParser(description="Sync Shared Contracts CLI")
    subparsers = parser.add_subparsers(dest="command")

    p_check = subparsers.add_parser("check", help="Check contract drift")
    p_check.add_argument("--repo-root", type=str, help="Repository root path")
    p_check.add_argument("--domain", type=str, default="lyrics-sync", help="Contract domain name")
    p_check.add_argument("--json", action="store_true", help="Emit JSON output")
    p_check.add_argument("--strict", action="store_true", help="Exit 1 if drift detected")
    p_check.add_argument("--rfc", action="append", help="Target RFC ID for scoped check")

    p_brief = subparsers.add_parser("brief", help="Generate Contract Requirements Brief")
    p_brief.add_argument("--repo-root", type=str, help="Repository root path")
    p_brief.add_argument("--domain", type=str, default="lyrics-sync", help="Contract domain name")
    p_brief.add_argument("--output", type=str, help="Output markdown path")

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
