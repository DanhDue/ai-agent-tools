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
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
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
INACTIVE_STATUSES = {"SUPERSEDED", "REJECTED", "INACTIVE"}


class ContractFormatError(Exception):
    """Raised when a shared contract file cannot be recognized or parsed."""


class TopologyError(Exception):
    """Raised when shared-contracts topology is missing, broken, or cyclic."""


def utc_now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def compile_glob(pattern: str) -> re.Pattern[str]:
    """Compile POSIX-normalized repository-relative glob into anchored regex."""
    pattern = pattern.strip()
    regex = ""
    index = 0
    length = len(pattern)
    while index < length:
        if pattern.startswith("/**", index) and index + 3 == length:
            regex += r"(?:/.*)?"
            index += 3
        elif pattern.startswith("**/", index):
            regex += r"(?:[^/]+/)*"
            index += 3
        elif pattern.startswith("**", index):
            regex += r".*"
            index += 2
        elif pattern[index] == "*":
            regex += r"[^/]*"
            index += 1
        elif pattern[index] == "?":
            regex += r"[^/]"
            index += 1
        else:
            regex += re.escape(pattern[index])
            index += 1
    return re.compile(rf"\A{regex}\Z")


def path_matches_domain(path: str, domain_cfg: dict[str, Any]) -> bool:
    """Check if normalized relative path belongs to domain config."""
    normalized = path.replace("\\", "/").lstrip("/")
    normalized = normalized.removeprefix("./")

    for excl in domain_cfg.get("exclude") or []:
        if compile_glob(excl).search(normalized):
            return False

    for inc in domain_cfg.get("paths") or []:
        if compile_glob(inc).search(normalized):
            return True

    return False


def validate_contract_map(data: Any) -> tuple[bool, str]:
    """Validate .agents/contract_map.json schema structure."""
    if not isinstance(data, dict):
        return False, "Root of contract_map.json must be a JSON object"
    if data.get("schema_version") != 1:
        return False, f"Expected schema_version 1, got {data.get('schema_version')}"
    base_ref = data.get("base_ref")
    if not isinstance(base_ref, str) or not base_ref.strip():
        return False, "base_ref must be a non-empty string"
    domains = data.get("domains")
    if not isinstance(domains, dict) or not domains:
        return False, "domains must be a non-empty object"

    for domain_name, domain_cfg in domains.items():
        if not isinstance(domain_name, str) or not domain_name.strip():
            return False, "Domain names must be non-empty strings"
        if not isinstance(domain_cfg, dict):
            return False, f"Domain configuration for '{domain_name}' must be an object"
        paths = domain_cfg.get("paths")
        if not isinstance(paths, list) or not paths:
            return False, f"Domain '{domain_name}' must have a non-empty list of paths"
        for p in paths:
            if not isinstance(p, str) or not p.strip():
                return False, f"Domain '{domain_name}' paths must be non-empty strings"
        exclude = domain_cfg.get("exclude")
        if exclude is not None:
            if not isinstance(exclude, list):
                return False, f"Domain '{domain_name}' exclude must be a list of strings"
            for e in exclude:
                if not isinstance(e, str) or not e.strip():
                    return False, f"Domain '{domain_name}' exclude entries must be non-empty strings"

    waivers = data.get("waivers")
    if waivers is not None:
        if not isinstance(waivers, list):
            return False, "waivers must be a list of waiver objects"
        waiver_ids: set[str] = set()
        for idx, waiver in enumerate(waivers):
            if not isinstance(waiver, dict):
                return False, f"Waiver at index {idx} must be an object"
            wid = waiver.get("id")
            if not isinstance(wid, str) or not wid.strip():
                return False, f"Waiver at index {idx} must have a non-empty string 'id'"
            if wid in waiver_ids:
                return False, f"Duplicate waiver id '{wid}' at index {idx}"
            waiver_ids.add(wid)

            wdomain = waiver.get("domain")
            if not isinstance(wdomain, str) or wdomain not in domains:
                return False, f"Waiver '{wid}' domain '{wdomain}' is not declared in domains"

            wpaths = waiver.get("paths")
            if not isinstance(wpaths, list) or not wpaths:
                return False, f"Waiver '{wid}' must have a non-empty list of paths"
            for wp in wpaths:
                if not isinstance(wp, str) or not wp.strip():
                    return False, f"Waiver '{wid}' paths must be non-empty strings"

            wreason = waiver.get("reason")
            if not isinstance(wreason, str) or not wreason.strip():
                return False, f"Waiver '{wid}' must have a non-empty string 'reason'"

            wgap = waiver.get("gap")
            if wgap is not None and (not isinstance(wgap, str) or not wgap.strip()):
                return False, f"Waiver '{wid}' gap must be null or a non-empty string"

    return True, ""


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


def get_git_commit_sha(contract_dir: Path) -> str | None:
    """Get latest git commit affecting contract_dir, or None if git history is unavailable."""
    try:
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", "."],
            cwd=contract_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def find_primary_repo_root(worktree_root: Path) -> Path | None:
    """Locate primary git checkout root when invoked inside a git worktree."""
    git_entry = worktree_root / ".git"
    if git_entry.is_file():
        try:
            content = git_entry.read_text(encoding="utf-8").strip()
            m = re.match(r"^gitdir:\s*(.*)", content)
            if m:
                gitdir = Path(m.group(1).strip())
                if ".git" in gitdir.parts:
                    git_idx = gitdir.parts.index(".git")
                    return Path(*gitdir.parts[:git_idx])
        except OSError:
            pass

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

            if resolved_path.is_symlink():
                curr = resolved_path
            else:
                break

        raw_target = os.readlink(shared_contracts)
        direct_target = (repo_root / raw_target).resolve()
        if direct_target.is_dir():
            contract_dir = direct_target
        else:
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
        mode = "hub"
        if (shared_contracts / domain).is_dir():
            contract_dir = (shared_contracts / domain).resolve()
        else:
            contract_dir = shared_contracts.resolve()

    if not contract_dir or not contract_dir.is_dir():
        raise TopologyError(f"Contract directory could not be resolved in {repo_root}")

    for fn in CANONICAL_FILES:
        fp = contract_dir / fn
        if not fp.is_file():
            raise TopologyError(f"Missing canonical contract file: {fn} in {contract_dir}")

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
    endpoint_segments: dict[str, list[str]] = {}
    for ep in endpoints:
        path = ep.split()[1] if " " in ep else ep
        parts = [seg.strip("/") for seg in re.split(r"\{[^}]+\}", path) if seg.strip("/")]
        endpoint_segments[ep] = parts

    key_variants: dict[str, set[str]] = {}
    for k in payload_keys:
        variants = {k, to_camel_case(k)}
        key_variants[k] = variants

    found_segments: set[str] = set()
    found_headers: set[str] = set()
    found_keys: set[str] = set()

    for root, dirs, files in os.walk(repo_root):
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

            for h in headers:
                if h in content:
                    found_headers.add(h)

            for orig_key, var_set in key_variants.items():
                if orig_key not in found_keys:
                    for var in var_set:
                        if var in content:
                            found_keys.add(orig_key)
                            break

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

    cur_rfcs: dict[str, dict[str, str]] = current_data.get("rfcs", {})
    base_rfcs: dict[str, dict[str, str]] = baseline_snapshot.get("rfcs", {})
    cur_rfc_ids = set(cur_rfcs.keys())
    base_rfc_ids = set(base_rfcs.keys())
    added_rfcs = sorted(cur_rfc_ids - base_rfc_ids)
    removed_rfcs = sorted(base_rfc_ids - cur_rfc_ids)
    modified_rfcs: list[str] = []
    for rfc_id in sorted(cur_rfc_ids & base_rfc_ids):
        cur_st = cur_rfcs[rfc_id].get("status")
        base_st = base_rfcs[rfc_id].get("status")
        if cur_st != base_st:
            modified_rfcs.append(f"{rfc_id}: {base_st} -> {cur_st}")

    return {
        "added_endpoints": added_ep,
        "removed_endpoints": removed_ep,
        "added_keys": added_keys,
        "removed_keys": removed_keys,
        "modified_field_types": modified_fields,
        "modified_pipeline_steps": modified_steps,
        "added_rfcs": added_rfcs,
        "removed_rfcs": removed_rfcs,
        "modified_rfcs": modified_rfcs,
    }


def load_sync_state(repo_root: Path) -> dict[str, Any]:
    """Load sync state from .agents/contract_sync.json, or return fresh schema template on missing/corrupt."""
    state_file = repo_root / ".agents" / "contract_sync.json"
    if not state_file.is_file():
        return {
            "schema_version": 1,
            "mode": "satellite",
            "domains": {},
        }
    try:
        content = state_file.read_text(encoding="utf-8")
        data = json.loads(content)
        if not isinstance(data, dict):
            raise TypeError("Root JSON must be object")
        return data
    except (json.JSONDecodeError, OSError, TypeError):
        print(f"Warning: malformed watermark file at {state_file}, falling back to initial state", file=sys.stderr)
        return {
            "schema_version": 1,
            "mode": "satellite",
            "domains": {},
        }


def save_sync_state_atomic(repo_root: Path, state_data: dict[str, Any]) -> None:
    """Atomically write synchronization metadata into .agents/contract_sync.json using temporary file."""
    agents_dir = repo_root / ".agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    target_file = agents_dir / "contract_sync.json"
    json_bytes = (json.dumps(state_data, indent=2) + "\n").encode("utf-8")

    fd, tmp_path_str = tempfile.mkstemp(dir=agents_dir, prefix="contract_sync_", suffix=".tmp")
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(json_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target_file)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


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


def evaluate_domain_sync(
    dom_data: dict[str, Any],
    snapshot_id: str,
    file_hashes: dict[str, str],
    api_data: dict[str, Any],
    arch_data: dict[str, Any],
    gaps_data: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate synchronization drift between on-disk contracts and persisted watermark."""
    prev_file_hashes = dom_data.get("file_hashes", {})
    changed_files = [fn for fn in CANONICAL_FILES if prev_file_hashes.get(fn) != file_hashes.get(fn)]
    files_changed = bool(changed_files)

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

    rfcs_dict = gaps_data.get("rfcs", {})
    contract_active_rfcs = {
        rfc_id for rfc_id, info in rfcs_dict.items()
        if info.get("status") in {"ACTIONABLE_PENDING", "ACKNOWLEDGED_ACTIVE"}
    }
    acknowledged_rfcs = set(dom_data.get("acknowledged_rfcs", []))
    pending_rfcs = sorted(contract_active_rfcs - acknowledged_rfcs)

    has_drift = (
        snapshot_id != dom_data.get("snapshot_id")
        or files_changed
        or bool(semantic_deltas["added_endpoints"])
        or bool(semantic_deltas["removed_endpoints"])
        or bool(semantic_deltas["added_keys"])
        or bool(semantic_deltas["removed_keys"])
        or bool(semantic_deltas["modified_field_types"])
        or bool(semantic_deltas["modified_pipeline_steps"])
        or bool(semantic_deltas["added_rfcs"])
        or bool(semantic_deltas["removed_rfcs"])
        or bool(semantic_deltas["modified_rfcs"])
        or bool(pending_rfcs)
    )

    return {
        "has_drift": has_drift,
        "changed_files": changed_files,
        "files_changed": files_changed,
        "semantic_deltas": semantic_deltas,
        "pending_rfcs": pending_rfcs,
        "acknowledged_rfcs": acknowledged_rfcs,
    }


def cmd_check(args: argparse.Namespace) -> int:
    """Execute check subcommand."""
    repo_root = Path(args.repo_root or os.getcwd()).resolve()
    domain = args.domain or "lyrics-sync"
    strict = getattr(args, "strict", False)
    as_json = getattr(args, "json", False)
    target_rfcs = getattr(args, "rfc", None) or []

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
        if as_json:
            print(json.dumps({"status": "INITIAL_SYNC", "domain": domain}))
        else:
            print(f"Domain '{domain}' status: INITIAL_SYNC (domain absent from watermark)")
        return 1 if strict else 0

    eval_res = evaluate_domain_sync(
        dom_data=dom_data,
        snapshot_id=snapshot_id,
        file_hashes=file_hashes,
        api_data=api_data,
        arch_data=arch_data,
        gaps_data=gaps_data,
    )
    files_changed = eval_res["files_changed"]
    semantic_deltas = eval_res["semantic_deltas"]
    pending_rfcs = eval_res["pending_rfcs"]
    acknowledged_rfcs = eval_res["acknowledged_rfcs"]
    has_drift = eval_res["has_drift"]

    # Scoped RFC check
    if target_rfcs:
        snapshot_matches = (snapshot_id == dom_data.get("snapshot_id"))
        rfcs_in_scope_valid = all((rfc in acknowledged_rfcs and rfc not in pending_rfcs) for rfc in target_rfcs)
        scoped_in_sync = snapshot_matches and rfcs_in_scope_valid and not files_changed

        if as_json:
            out_scoped = {
                "status": "IN_SYNC" if scoped_in_sync else "DRIFT_DETECTED",
                "scoped_in_sync": scoped_in_sync,
                "domain": domain,
                "snapshot_id": snapshot_id,
                "target_rfcs": target_rfcs,
            }
            print(json.dumps(out_scoped, indent=2))
        else:
            status_str = "IN_SYNC" if scoped_in_sync else "DRIFT_DETECTED"
            print(f"Domain '{domain}' scoped check for {target_rfcs}: {status_str}")
        return 0 if scoped_in_sync else (1 if strict else 0)

    # Global check
    if as_json:
        out = {
            "status": "DRIFT_DETECTED" if has_drift else "IN_SYNC",
            "domain": domain,
            "snapshot_id": snapshot_id,
            "deltas": semantic_deltas,
            "pending_rfcs": pending_rfcs,
        }
        print(json.dumps(out, indent=2))
    else:
        status_str = "DRIFT_DETECTED" if has_drift else "IN_SYNC"
        print(f"Domain '{domain}' status: {status_str}")
        if pending_rfcs:
            print(f"Pending RFCs: {', '.join(pending_rfcs)}")
        if semantic_deltas["added_endpoints"]:
            print(f"Added Endpoints: {', '.join(semantic_deltas['added_endpoints'])}")
        if semantic_deltas["removed_endpoints"]:
            print(f"Removed Endpoints: {', '.join(semantic_deltas['removed_endpoints'])}")
        if semantic_deltas["added_keys"]:
            print(f"Added Payload Keys: {', '.join(semantic_deltas['added_keys'])}")
        if semantic_deltas["removed_keys"]:
            print(f"Removed Payload Keys: {', '.join(semantic_deltas['removed_keys'])}")
        if semantic_deltas["modified_field_types"]:
            print(f"Modified Field Types: {', '.join(semantic_deltas['modified_field_types'])}")
        if semantic_deltas["modified_pipeline_steps"]:
            print(f"Modified Pipeline Steps: {', '.join(semantic_deltas['modified_pipeline_steps'])}")
        if semantic_deltas["added_rfcs"]:
            print(f"Added RFCs: {', '.join(semantic_deltas['added_rfcs'])}")
        if semantic_deltas["removed_rfcs"]:
            print(f"Removed RFCs: {', '.join(semantic_deltas['removed_rfcs'])}")
        if semantic_deltas["modified_rfcs"]:
            print(f"Modified RFCs: {', '.join(semantic_deltas['modified_rfcs'])}")

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

    sync_state = load_sync_state(repo_root)
    dom_data = sync_state.get("domains", {}).get(domain)

    if dom_data:
        eval_res = evaluate_domain_sync(
            dom_data=dom_data,
            snapshot_id=snapshot_id,
            file_hashes=file_hashes,
            api_data=api_data,
            arch_data=arch_data,
            gaps_data=gaps_data,
        )
        sync_status = "DRIFT_DETECTED" if eval_res["has_drift"] else "IN_SYNC"
        previous_version = dom_data.get("contract_version", "none")
        changed_files = eval_res["changed_files"]
        prev_commit = dom_data.get("hub_commit_sha", "HEAD")
        curr_commit = get_git_commit_sha(contract_dir) or "HEAD"
        if prev_commit and curr_commit and prev_commit not in {"HEAD", "uncommitted"} and curr_commit not in {"HEAD", "uncommitted"} and prev_commit != curr_commit:
            hub_commit_range = f"{prev_commit[:7]}..{curr_commit[:7]}"
        elif prev_commit and prev_commit not in {"HEAD", "uncommitted"}:
            hub_commit_range = prev_commit[:7]
        elif curr_commit and curr_commit not in {"HEAD", "uncommitted"}:
            hub_commit_range = curr_commit[:7]
        else:
            hub_commit_range = "HEAD"
    else:
        sync_status = "INITIAL_SYNC"
        previous_version = "none"
        hub_commit_range = "HEAD"
        changed_files = list(CANONICAL_FILES)

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
        sync_status=sync_status,
        snapshot_id=snapshot_id,
        previous_version=previous_version,
        current_version=api_data["version"],
        hub_commit_range=hub_commit_range,
        changed_files=changed_files,
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
    """Execute ack subcommand recording snapshot-and-scope-bound synchronization state."""
    repo_root = Path(args.repo_root or os.getcwd()).resolve()
    domain = args.domain or "lyrics-sync"
    expected_snapshot = getattr(args, "snapshot", None)
    explicit_rfcs = set(getattr(args, "rfc", None) or [])
    all_rfcs = getattr(args, "all_rfcs", False)

    try:
        topo = resolve_topology(repo_root, domain)
    except TopologyError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    contract_dir = topo["contract_dir"]
    file_hashes: dict[str, str] = {}
    for fn in CANONICAL_FILES:
        file_hashes[fn] = compute_file_hash(contract_dir / fn)
    current_snapshot_id = compute_snapshot_id(file_hashes)

    # Snapshot Guard check
    if expected_snapshot and expected_snapshot != current_snapshot_id:
        print(f"ERROR: SNAPSHOT_MISMATCH: expected {expected_snapshot}, got {current_snapshot_id}", file=sys.stderr)
        return 1

    try:
        api_data = parse_api_contract((contract_dir / "api_contract.md").read_text(encoding="utf-8"))
        arch_data = parse_architecture_and_flow((contract_dir / "architecture_and_flow.md").read_text(encoding="utf-8"))
        gaps_data = parse_gaps_and_rfcs((contract_dir / "gaps_and_rfcs.md").read_text(encoding="utf-8"))
    except ContractFormatError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    hub_commit = get_git_commit_sha(contract_dir) or "uncommitted"

    # Load existing sync state to preserve other domains and prior RFCs
    sync_state = load_sync_state(repo_root)
    sync_state["schema_version"] = 1
    sync_state["mode"] = topo["mode"]
    domains: dict[str, Any] = sync_state.setdefault("domains", {})

    prev_domain_data = domains.get(domain, {})
    prev_ack_rfcs: set[str] = set(prev_domain_data.get("acknowledged_rfcs", []))

    # Identify all active RFC items in contract
    rfcs_dict = gaps_data.get("rfcs", {})
    contract_active_rfcs: set[str] = {
        rfc_id for rfc_id, info in rfcs_dict.items() if info.get("status") in {"ACTIONABLE_PENDING", "ACKNOWLEDGED_ACTIVE"}
    }

    if all_rfcs or not contract_active_rfcs:
        acknowledged_rfcs = sorted(contract_active_rfcs | prev_ack_rfcs)
        pending_rfcs: list[str] = []
    else:
        # Acknowledge previously acknowledged RFCs plus explicit selections
        newly_acked = prev_ack_rfcs | explicit_rfcs
        acknowledged_rfcs = sorted(contract_active_rfcs & newly_acked)
        pending_rfcs = sorted(contract_active_rfcs - newly_acked)

    baseline_snapshot = {
        "endpoints": api_data["endpoints"],
        "headers": api_data["headers"],
        "payload_keys": api_data["payload_keys"],
        "payload_fields": api_data["payload_fields"],
        "pipeline_steps": arch_data["pipeline_steps"],
        "rfcs": gaps_data["rfcs"],
    }

    domains[domain] = {
        "snapshot_id": current_snapshot_id,
        "hub_commit_sha": hub_commit,
        "contract_version": api_data["version"],
        "last_synced_at": utc_now_iso(),
        "file_hashes": file_hashes,
        "acknowledged_rfcs": acknowledged_rfcs,
        "pending_rfcs": pending_rfcs,
        "acknowledged_endpoints": api_data["endpoints"],
        "baseline_snapshot": baseline_snapshot,
    }

    save_sync_state_atomic(repo_root, sync_state)
    print(f"Watermark acknowledged for domain '{domain}' -> {current_snapshot_id}")
    return 0


def cmd_diff_check(args: argparse.Namespace) -> int:
    """Audit diff between merge-base and HEAD against .agents/contract_map.json."""
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path.cwd().resolve()
    is_json = bool(args.json)

    def emit_blocked(
        blockers: list[str],
        mode: str | None = None,
        base_ref: str | None = None,
        merge_base: str | None = None,
        head_sha: str | None = None,
    ) -> int:
        if is_json:
            payload = {
                "status": "BLOCKED",
                "mode": mode,
                "base_ref": base_ref,
                "merge_base": merge_base,
                "head_sha": head_sha,
                "domains": [],
                "violations": [],
                "active_waivers": [],
                "blockers": blockers,
            }
            print(json.dumps(payload, indent=2))
        else:
            print("Status: BLOCKED")
            if mode:
                print(f"Mode: {mode}")
            print("Blockers:")
            for b in blockers:
                print(f"  - {b}")
        return 2

    # 1. Preconditions: Validate HEAD .agents/contract_map.json
    map_file = repo_root / ".agents" / "contract_map.json"
    if not map_file.is_file():
        return emit_blocked(["Missing .agents/contract_map.json at HEAD"])

    try:
        head_map_data = json.loads(map_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return emit_blocked([f"Malformed JSON in .agents/contract_map.json at HEAD: {exc}"])

    valid_map, map_err = validate_contract_map(head_map_data)
    if not valid_map:
        return emit_blocked([f"Invalid .agents/contract_map.json schema at HEAD: {map_err}"])

    head_domains: dict[str, Any] = head_map_data["domains"]

    # 2. Preconditions: Validate --domain filters
    if args.domain:
        for d in args.domain:
            if d not in head_domains:
                return emit_blocked([f"Unknown domain filter '{d}' not in contract_map.json domains"])

    # 3. Preconditions: Check tracked working-tree cleanliness
    proc_status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        check=False,
        cwd=repo_root,
        capture_output=True,
    )
    if proc_status.returncode != 0:
        return emit_blocked([f"git status failed: {proc_status.stderr.decode(errors='replace').strip()}"])
    if proc_status.stdout.strip():
        dirty_lines = [line.strip() for line in proc_status.stdout.decode(errors='replace').splitlines() if line.strip()]
        return emit_blocked([f"Working tree has tracked modifications: {', '.join(dirty_lines)}"])

    # 4. Preconditions: Determine effective_base_ref and resolve merge-base
    effective_base_ref: str = args.base_ref if args.base_ref else head_map_data["base_ref"]

    proc_mb = subprocess.run(
        ["git", "merge-base", effective_base_ref, "HEAD"],
        check=False,
        cwd=repo_root,
        capture_output=True,
    )
    if proc_mb.returncode != 0:
        return emit_blocked(
            [f"Failed to find git merge-base for base-ref '{effective_base_ref}': {proc_mb.stderr.decode(errors='replace').strip()}"],
            base_ref=effective_base_ref,
        )
    merge_base = proc_mb.stdout.decode().strip()

    proc_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=False,
        cwd=repo_root,
        capture_output=True,
    )
    if proc_head.returncode != 0:
        return emit_blocked([f"Failed to resolve git HEAD: {proc_head.stderr.decode(errors='replace').strip()}"])
    head_sha = proc_head.stdout.decode().strip()

    # 5. Preconditions: Topology resolution
    first_domain = next(iter(head_domains))
    try:
        topo = resolve_topology(repo_root, first_domain)
    except (TopologyError, ContractFormatError) as exc:
        return emit_blocked([str(exc)], base_ref=effective_base_ref, merge_base=merge_base, head_sha=head_sha)

    mode = topo["mode"]

    if mode == "hub":
        for d in head_domains:
            try:
                resolve_topology(repo_root, d)
            except (TopologyError, ContractFormatError) as exc:
                return emit_blocked([str(exc)], mode=mode, base_ref=effective_base_ref, merge_base=merge_base, head_sha=head_sha)
    elif mode == "satellite":
        contract_dir = topo.get("contract_dir")
        linked_domain = contract_dir.name if contract_dir else ""
        for d in head_domains:
            if d != linked_domain:
                return emit_blocked(
                    [f"Satellite contract_map.json domain '{d}' does not match linked shared-contracts domain '{linked_domain}'"],
                    mode=mode,
                    base_ref=effective_base_ref,
                    merge_base=merge_base,
                    head_sha=head_sha,
                )

    # 6. Short-circuit PASS if M == HEAD
    evaluated_domains = sorted(set(args.domain)) if args.domain else sorted(head_domains.keys())
    if merge_base == head_sha:
        early_report: list[dict[str, Any]] = [{"domain": d, "changed_files": [], "proof": "none"} for d in evaluated_domains]
        if is_json:
            payload = {
                "status": "PASS",
                "mode": mode,
                "base_ref": effective_base_ref,
                "merge_base": merge_base,
                "head_sha": head_sha,
                "domains": early_report,
                "violations": [],
                "active_waivers": [],
                "blockers": [],
            }
            print(json.dumps(payload, indent=2))
        else:
            print("Status: PASS")
            print(f"Mode: {mode}")
            print(f"Base ref: {effective_base_ref}")
            print("Domains:")
            for item in early_report:
                print(f"  - {item['domain']}: proof={item['proof']}")
        return 0

    # 7. Probe baseline contract_map.json at merge_base
    proc_ls_map = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", merge_base, "--", ".agents/contract_map.json"],
        check=False,
        cwd=repo_root,
        capture_output=True,
    )
    if proc_ls_map.returncode != 0:
        return emit_blocked(
            [f"git ls-tree failed for baseline .agents/contract_map.json at {merge_base}: {proc_ls_map.stderr.decode(errors='replace').strip()}"],
            mode=mode,
            base_ref=effective_base_ref,
            merge_base=merge_base,
            head_sha=head_sha,
        )

    baseline_domains: dict[str, Any] = {}
    baseline_waivers: dict[str, Any] = {}
    if proc_ls_map.stdout.strip():
        proc_show_map = subprocess.run(
            ["git", "show", f"{merge_base}:.agents/contract_map.json"],
            check=False,
            cwd=repo_root,
            capture_output=True,
        )
        if proc_show_map.returncode != 0:
            return emit_blocked(
                [f"git show failed for baseline .agents/contract_map.json at {merge_base}: {proc_show_map.stderr.decode(errors='replace').strip()}"],
                mode=mode,
                base_ref=effective_base_ref,
                merge_base=merge_base,
                head_sha=head_sha,
            )
        try:
            base_map_data = json.loads(proc_show_map.stdout.decode("utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            return emit_blocked(
                [f"Malformed JSON in baseline .agents/contract_map.json at {merge_base}: {exc}"],
                mode=mode,
                base_ref=effective_base_ref,
                merge_base=merge_base,
                head_sha=head_sha,
            )
        valid_base_map, base_map_err = validate_contract_map(base_map_data)
        if not valid_base_map:
            return emit_blocked(
                [f"Invalid schema in baseline .agents/contract_map.json at {merge_base}: {base_map_err}"],
                mode=mode,
                base_ref=effective_base_ref,
                merge_base=merge_base,
                head_sha=head_sha,
            )
        baseline_domains = base_map_data["domains"]
        for w in base_map_data.get("waivers") or []:
            baseline_waivers[w["id"]] = w

    violations: list[dict[str, str]] = []

    # 8. Check historical waiver immutability
    head_waivers: dict[str, Any] = {}
    for w in head_map_data.get("waivers") or []:
        head_waivers[w["id"]] = w

    invalid_waiver_ids: set[str] = set()

    for wid, w_base in baseline_waivers.items():
        if wid in head_waivers:
            w_head = head_waivers[wid]
            if (
                w_head["domain"] != w_base["domain"]
                or w_head["paths"] != w_base["paths"]
                or w_head["reason"] != w_base["reason"]
                or w_head.get("gap") != w_base.get("gap")
            ):
                invalid_waiver_ids.add(wid)
                violations.append({
                    "domain": str(w_head.get("domain", "")),
                    "path": ".agents/contract_map.json",
                    "reason": f"Illegal mutation of historical waiver '{wid}'",
                })

    newly_added_waivers = [w for wid, w in head_waivers.items() if wid not in baseline_waivers]

    for w in newly_added_waivers:
        gap = w.get("gap")
        if gap is not None:
            wdomain = w["domain"]
            if mode == "hub":
                gaps_file = repo_root / "shared-contracts" / wdomain / "gaps_and_rfcs.md"
            else:
                contract_dir_opt = topo.get("contract_dir")
                gaps_file = (contract_dir_opt / "gaps_and_rfcs.md") if contract_dir_opt else (repo_root / "shared-contracts" / "gaps_and_rfcs.md")
            if not gaps_file.is_file():
                invalid_waiver_ids.add(w["id"])
                violations.append({
                    "domain": str(wdomain),
                    "path": ".agents/contract_map.json",
                    "reason": f"Waiver '{w['id']}' cites gap '{gap}' but {gaps_file} does not exist",
                })
            else:
                try:
                    gaps_content = gaps_file.read_text(encoding="utf-8")
                    gaps_parsed = parse_gaps_and_rfcs(gaps_content)
                    rfcs_dict = gaps_parsed.get("rfcs", {})
                    if gap not in rfcs_dict:
                        invalid_waiver_ids.add(w["id"])
                        violations.append({
                            "domain": str(wdomain),
                            "path": ".agents/contract_map.json",
                            "reason": f"Waiver '{w['id']}' cites non-existent gap '{gap}'",
                        })
                    else:
                        norm_status = str(rfcs_dict[gap].get("status", ""))
                        raw_status = str(rfcs_dict[gap].get("raw_status", norm_status))
                        if norm_status not in ("ACTIONABLE_PENDING", "ACKNOWLEDGED_ACTIVE"):
                            invalid_waiver_ids.add(w["id"])
                            violations.append({
                                "domain": str(wdomain),
                                "path": ".agents/contract_map.json",
                                "reason": f"Waiver '{w['id']}' cites INACTIVE gap '{gap}' (status: {raw_status})",
                            })
                except (ContractFormatError, OSError) as exc:
                    invalid_waiver_ids.add(w["id"])
                    violations.append({
                        "domain": str(wdomain),
                        "path": ".agents/contract_map.json",
                        "reason": f"Failed to parse gaps_and_rfcs.md for waiver '{w['id']}': {exc}",
                    })

    # 9. Extract changed files via git diff --no-ext-diff --no-renames --name-only -z M..HEAD
    proc_diff = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", f"{merge_base}..HEAD"],
        check=False,
        cwd=repo_root,
        capture_output=True,
    )
    if proc_diff.returncode != 0:
        return emit_blocked(
            [f"git diff failed: {proc_diff.stderr.decode(errors='replace').strip()}"],
            mode=mode,
            base_ref=effective_base_ref,
            merge_base=merge_base,
            head_sha=head_sha,
        )

    raw_diff = proc_diff.stdout.decode("utf-8", errors="surrogateescape")
    changed_files = [f for f in raw_diff.split("\0") if f]

    # 10. Evaluate domains across union(HEAD, baseline)
    all_domains = sorted(set(head_domains) | set(baseline_domains))
    if args.domain:
        domains_to_evaluate = sorted(set(args.domain))
    else:
        domains_to_evaluate = all_domains

    # Check deleted baseline domains
    for d in sorted(set(baseline_domains) - set(head_domains)):
        if d in domains_to_evaluate:
            base_cfg = baseline_domains[d]
            matching_changed = [f for f in changed_files if path_matches_domain(f, base_cfg)]
            if matching_changed:
                violations.append({
                    "domain": d,
                    "path": ".agents/contract_map.json",
                    "reason": f"Domain '{d}' was deleted at HEAD but has changed baseline-mapped files: {', '.join(matching_changed)}",
                })

    domains_report: list[dict[str, Any]] = []
    active_waivers: list[dict[str, Any]] = []

    for d in domains_to_evaluate:
        if d not in head_domains:
            continue

        head_cfg = head_domains[d]
        base_cfg = baseline_domains.get(d)
        changed_mapped: list[str] = []
        for f in changed_files:
            matched = False
            if path_matches_domain(f, head_cfg) or (base_cfg and path_matches_domain(f, base_cfg)):
                matched = True
            if matched:
                changed_mapped.append(f)

        if not changed_mapped:
            domains_report.append({"domain": d, "changed_files": [], "proof": "none"})
            continue

        changed_mapped = sorted(set(changed_mapped))
        domain_covered = False
        domain_proof = "uncovered"

        if mode == "hub":
            prefix = f"shared-contracts/{d}/"
            canonical_edits = [
                f for f in changed_files
                if f in (f"{prefix}api_contract.md", f"{prefix}architecture_and_flow.md", f"{prefix}gaps_and_rfcs.md")
            ]
            if canonical_edits:
                domain_covered = True
                domain_proof = "contract_edit"
        elif mode == "satellite":
            proc_ls_sync = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", merge_base, "--", ".agents/contract_sync.json"],
                check=False,
                cwd=repo_root,
                capture_output=True,
            )
            if proc_ls_sync.returncode != 0:
                return emit_blocked(
                    [f"git ls-tree failed for baseline contract_sync.json: {proc_ls_sync.stderr.decode(errors='replace').strip()}"],
                    mode=mode,
                    base_ref=effective_base_ref,
                    merge_base=merge_base,
                    head_sha=head_sha,
                )
            base_sync_domains: dict[str, Any] = {}
            if proc_ls_sync.stdout.strip():
                proc_show_sync = subprocess.run(
                    ["git", "show", f"{merge_base}:.agents/contract_sync.json"],
                    check=False,
                    cwd=repo_root,
                    capture_output=True,
                )
                if proc_show_sync.returncode != 0:
                    return emit_blocked(
                        [f"git show failed for baseline contract_sync.json: {proc_show_sync.stderr.decode(errors='replace').strip()}"],
                        mode=mode,
                        base_ref=effective_base_ref,
                        merge_base=merge_base,
                        head_sha=head_sha,
                    )
                try:
                    base_sync_data = json.loads(proc_show_sync.stdout.decode("utf-8"))
                    base_sync_domains = base_sync_data.get("domains") or {}
                except (json.JSONDecodeError, OSError) as exc:
                    return emit_blocked(
                        [f"Malformed JSON in baseline contract_sync.json: {exc}"],
                        mode=mode,
                        base_ref=effective_base_ref,
                        merge_base=merge_base,
                        head_sha=head_sha,
                    )

            head_sync_file = repo_root / ".agents" / "contract_sync.json"
            if head_sync_file.is_file():
                try:
                    head_sync_data = json.loads(head_sync_file.read_text(encoding="utf-8"))
                    head_sync_domains = head_sync_data.get("domains") or {}
                except (json.JSONDecodeError, OSError) as exc:
                    return emit_blocked(
                        [f"Malformed JSON in HEAD contract_sync.json: {exc}"],
                        mode=mode,
                        base_ref=effective_base_ref,
                        merge_base=merge_base,
                        head_sha=head_sha,
                    )

                contract_dir_opt = topo.get("contract_dir")
                if not contract_dir_opt:
                    return emit_blocked(
                        ["Missing contract_dir in topology"],
                        mode=mode,
                        base_ref=effective_base_ref,
                        merge_base=merge_base,
                        head_sha=head_sha,
                    )
                try:
                    f_hashes: dict[str, str] = {}
                    for cname in CANONICAL_FILES:
                        cpath = contract_dir_opt / cname
                        if not cpath.is_file():
                            raise ContractFormatError(f"Canonical file {cname} missing from {contract_dir_opt}")
                        f_hashes[cname] = compute_file_hash(cpath)
                    live_snapshot_id = compute_snapshot_id(f_hashes)
                except (ContractFormatError, OSError) as exc:
                    return emit_blocked(
                        [f"Failed to compute live snapshot_id: {exc}"],
                        mode=mode,
                        base_ref=effective_base_ref,
                        merge_base=merge_base,
                        head_sha=head_sha,
                    )

                head_d_info = head_sync_domains.get(d)
                base_d_info = base_sync_domains.get(d)

                if head_d_info:
                    was_added_or_updated = (base_d_info is None) or (head_d_info != base_d_info)
                    snapshot_matched = head_d_info.get("snapshot_id") == live_snapshot_id
                    if was_added_or_updated and snapshot_matched:
                        domain_covered = True
                        domain_proof = "ack"

        if domain_covered:
            domains_report.append({"domain": d, "changed_files": changed_mapped, "proof": domain_proof})
        else:
            uncovered: list[str] = []
            matched_waivers_for_d: list[dict[str, Any]] = []
            for f in changed_mapped:
                covered_by_w = False
                for w in newly_added_waivers:
                    if w["domain"] == d:
                        for wp in w["paths"]:
                            if compile_glob(wp).search(f):
                                covered_by_w = True
                                if w not in matched_waivers_for_d:
                                    matched_waivers_for_d.append(w)
                                break
                    if covered_by_w:
                        break
                if not covered_by_w:
                    uncovered.append(f)

            has_invalid_waiver = any(w["id"] in invalid_waiver_ids for w in matched_waivers_for_d)
            if not uncovered and not has_invalid_waiver:
                domains_report.append({"domain": d, "changed_files": changed_mapped, "proof": "waiver"})
                for w in matched_waivers_for_d:
                    w_item = {
                        "id": w["id"],
                        "domain": w["domain"],
                        "paths": w["paths"],
                        "reason": w["reason"],
                        "gap": w.get("gap"),
                    }
                    if w_item not in active_waivers:
                        active_waivers.append(w_item)
            else:
                domains_report.append({"domain": d, "changed_files": changed_mapped, "proof": "uncovered"})
                for uf in uncovered:
                    violations.append({
                        "domain": d,
                        "path": uf,
                        "reason": f"Mapped file '{uf}' changed in domain '{d}' without canonical contract edit, fresh ack, or active waiver",
                    })

    status = "FAIL" if violations else "PASS"
    exit_code = 1 if violations else 0

    if is_json:
        payload = {
            "status": status,
            "mode": mode,
            "base_ref": effective_base_ref,
            "merge_base": merge_base,
            "head_sha": head_sha,
            "domains": domains_report,
            "violations": violations,
            "active_waivers": active_waivers,
            "blockers": [],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Status: {status}")
        print(f"Mode: {mode}")
        print(f"Base ref: {effective_base_ref}")
        print("Domains:")
        for item in domains_report:
            print(f"  - {item['domain']}: proof={item['proof']} ({len(item['changed_files'])} changed files)")
        if active_waivers:
            print("Active Waivers:")
            for w in active_waivers:
                print(f"  - [{w['id']}] {w['domain']} ({', '.join(w['paths'])}): {w['reason']} (gap: {w.get('gap')})")
        if violations:
            print("Violations:")
            for v in violations:
                print(f"  - [{v.get('domain', 'general')}] {v['path']}: {v['reason']}")

    return exit_code


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

    p_diff = subparsers.add_parser("diff-check", help="Audit diff between merge-base and HEAD against contract_map.json")
    p_diff.add_argument("--repo-root", type=str, help="Repository root path")
    p_diff.add_argument("--base-ref", type=str, help="Base git reference")
    p_diff.add_argument("--domain", action="append", help="Contract domain filter")
    p_diff.add_argument("--json", action="store_true", help="Emit JSON output")

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
    if args.command == "diff-check":
        return cmd_diff_check(args)

    return 1


if __name__ == "__main__":
    sys.exit(main())
