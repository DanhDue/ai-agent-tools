#!/usr/bin/env python3
"""CLI Engine for managing multi-repo shared contracts across Hub and Satellite repositories."""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import string
import sys
import uuid
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
MAX_SYMLINK_DEPTH = 10
DOMAIN_REGEX = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CANONICAL_CONTRACT_FILES = (
    "api_contract.md",
    "architecture_and_flow.md",
    "gaps_and_rfcs.md",
)


def normalize_domain(domain: str) -> str:
    """Normalize domain name by stripping whitespace and lowercasing."""
    return domain.strip().lower()


def validate_domain(domain: str) -> str:
    """Normalize and validate domain name for safe single-component path containment."""
    normalized = normalize_domain(domain)
    if not normalized:
        raise ValueError("Domain name cannot be empty.")
    if "/" in normalized or "\\" in normalized or ".." in normalized or normalized == ".":
        raise ValueError(
            f"Domain name '{domain}' cannot contain path separators or directory traversal."
        )
    if not DOMAIN_REGEX.match(normalized):
        raise ValueError(
            f"Domain name '{domain}' is invalid: must start with alphanumeric and contain only [a-z0-9_-]."
        )
    return normalized


def atomic_write_text(target_path: Path, content: str) -> None:
    """Write content to target_path atomically using a temporary swap file."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.parent / f".tmp_{target_path.name}_{uuid.uuid4().hex}"
    try:
        tmp_path.write_text(content, encoding="utf-8")
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def resolve_symlink_safe(path: Path) -> tuple[Path, bool]:
    """Resolve a symlink safely with cycle detection and depth boundaries."""
    current = path
    visited: set[tuple[int, int] | str] = set()
    depth = 0

    while current.is_symlink() or os.path.islink(current):
        if depth >= MAX_SYMLINK_DEPTH:
            return current, False
        try:
            st = os.lstat(current)
            node_key: tuple[int, int] | str = (
                (st.st_dev, st.st_ino) if st.st_ino != 0 else str(current.absolute())
            )
            if node_key in visited:
                return current, False
            visited.add(node_key)

            raw_link = os.readlink(current)
            if not os.path.isabs(raw_link):
                next_path = current.parent / raw_link
            else:
                next_path = Path(raw_link)
            current = Path(os.path.normpath(next_path))
        except (OSError, RuntimeError):
            return current, False
        depth += 1

    try:
        final_target = current.resolve()
        return final_target, final_target.exists()
    except (OSError, RuntimeError):
        return current, False


def _get_timestamp() -> str:
    """Return ISO-8601 UTC timestamp."""
    utc_tz = getattr(datetime, "UTC", datetime.timezone.utc)  # noqa: UP017
    return datetime.datetime.now(utc_tz).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_template(name: str) -> string.Template:
    """Load a template file and return string.Template instance."""
    path = TEMPLATES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Canonical template not found: {path}")
    return string.Template(path.read_text(encoding="utf-8"))


def _update_readme_table(readme_path: Path, domain: str) -> None:
    """Ensure domain is registered in the Outbound Symlink Mappings table."""
    normalized = normalize_domain(domain)
    content = readme_path.read_text(encoding="utf-8")
    if f"| {normalized} " in content or f"|{normalized}|" in content:
        return

    table_header = "| Domain | Target Path | Target Satellites | Status |"
    table_separator = "|---|---|---|---|"
    new_row = f"| {normalized} | shared-contracts/{normalized} | {normalized} | Active |"

    if table_separator in content:
        parts = content.split(table_separator, 1)
        updated = f"{parts[0]}{table_separator}\n{new_row}{parts[1]}"
        atomic_write_text(readme_path, updated)
    elif table_header in content:
        parts = content.split(table_header, 1)
        updated = f"{parts[0]}{table_header}\n{table_separator}\n{new_row}{parts[1]}"
        atomic_write_text(readme_path, updated)
    else:
        table_block = (
            f"\n## Outbound Symlink Mappings\n\n"
            f"{table_header}\n{table_separator}\n{new_row}\n"
        )
        atomic_write_text(readme_path, content + table_block)


def cmd_init_hub(repo_root: Path, domain: str | None = None, force: bool = False) -> int:
    """Initialize a physical Hub repository with canonical contract files and rules."""
    shared_contracts_dir = repo_root / "shared-contracts"

    # 1. Validation: Hub must NEVER be a symlink
    if shared_contracts_dir.is_symlink() or os.path.islink(shared_contracts_dir):
        sys.stderr.write(
            "ERROR [SSC-FR-01]: Target 'shared-contracts' is an existing symbolic link (symlink).\n"
            "Hub repositories must maintain a physical directory as the Single Source of Truth (SSOT).\n"
        )
        return 1

    shared_contracts_dir.mkdir(parents=True, exist_ok=True)
    hub_repo_name = repo_root.resolve().name or "D3Nexus"
    timestamp = _get_timestamp()
    norm_domain = None
    if domain is not None:
        try:
            norm_domain = validate_domain(domain)
        except ValueError as exc:
            sys.stderr.write(f"ERROR: {exc}\n")
            return 1
    primary_domain = norm_domain if norm_domain else "general"

    template_vars = {
        "hub_repo": hub_repo_name,
        "domain": primary_domain,
        "timestamp": timestamp,
    }

    # 2. Render shared-contracts/README.md
    readme_path = shared_contracts_dir / "README.md"
    if not readme_path.exists() or force:
        tmpl = _load_template("hub_readme.md.tmpl")
        atomic_write_text(readme_path, tmpl.substitute(template_vars))
    elif norm_domain:
        _update_readme_table(readme_path, norm_domain)

    # 3. Create domain subfolder with 3 canonical files
    if norm_domain:
        domain_dir = shared_contracts_dir / norm_domain
        if domain_dir.is_symlink() or os.path.islink(domain_dir):
            sys.stderr.write(
                f"ERROR: Domain directory '{domain_dir}' is an existing symbolic link; "
                "Hub domains must be physical directories.\n"
            )
            return 1

        shared_contracts_resolved = shared_contracts_dir.resolve()
        if domain_dir.exists() and not domain_dir.resolve().is_relative_to(shared_contracts_resolved):
            sys.stderr.write(
                f"ERROR: Domain directory '{domain_dir}' resolves outside '{shared_contracts_resolved}'.\n"
            )
            return 1

        domain_dir.mkdir(parents=True, exist_ok=True)

        canonical_files = (
            ("api_contract.md", "api_contract.md.tmpl"),
            ("architecture_and_flow.md", "architecture_and_flow.md.tmpl"),
            ("gaps_and_rfcs.md", "gaps_and_rfcs.md.tmpl"),
        )
        for filename, tmpl_name in canonical_files:
            target_file = domain_dir / filename
            if not target_file.exists() or force:
                tmpl = _load_template(tmpl_name)
                atomic_write_text(target_file, tmpl.substitute(template_vars))

    # 4. Install Hub local rule .agents/rules/contract_rules.md
    rules_dir = repo_root / ".agents" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    contract_rules_path = rules_dir / "contract_rules.md"
    if not contract_rules_path.exists() or force:
        rule_tmpl = _load_template("hub_rule.md.tmpl")
        atomic_write_text(contract_rules_path, rule_tmpl.substitute(template_vars))

    sys.stdout.write(
        f"SUCCESS: Hub repository initialized at '{shared_contracts_dir}'\n"
        f"SSOT Local Rule: '{contract_rules_path}'\n"
    )
    return 0


def cmd_link_satellite(
    hub: Path,
    domain: str,
    satellite_root: Path,
    force: bool = False,
) -> int:
    """Link a satellite repository to a Hub domain contracts directory via relative symlink."""
    try:
        norm_domain = validate_domain(domain)
    except ValueError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1

    # 1. Validate Hub directory and domain presence
    hub_resolved = hub.resolve()
    shared_contracts_hub = (hub_resolved / "shared-contracts").resolve()
    hub_domain_dir = shared_contracts_hub / norm_domain

    if not hub_domain_dir.is_dir():
        sys.stderr.write(
            f"ERROR [SSC-FR-02]: Target domain '{norm_domain}' not found in Hub at '{hub_resolved}'.\n"
            f"Expected directory: '{hub_domain_dir}'\n"
        )
        return 1

    hub_domain_resolved = hub_domain_dir.resolve()
    if not hub_domain_resolved.is_relative_to(shared_contracts_hub):
        sys.stderr.write(
            f"ERROR: Target domain '{norm_domain}' resolves outside Hub shared-contracts: '{hub_domain_resolved}'.\n"
        )
        return 1

    satellite_root_resolved = satellite_root.resolve()
    shared_contracts_link = satellite_root_resolved / "shared-contracts"

    # 2. Check existing path at target
    if shared_contracts_link.is_symlink() or os.path.islink(shared_contracts_link):
        shared_contracts_link.unlink()
    elif shared_contracts_link.is_dir():
        has_entries = any(shared_contracts_link.iterdir())
        if has_entries and not force:
            sys.stderr.write(
                "ERROR [SSC-FR-03]: Target 'shared-contracts' is an existing non-empty physical directory.\n"
                "Refusing overwrite without --force to prevent uncommitted file loss.\n"
            )
            return 1
        shutil.rmtree(shared_contracts_link)
    elif shared_contracts_link.exists():
        if not force:
            sys.stderr.write(
                "ERROR [SSC-FR-03]: Target 'shared-contracts' exists and is not a symlink.\n"
                "Refusing overwrite without --force.\n"
            )
            return 1
        shared_contracts_link.unlink()

    # 3. Compute relative target and create symlink
    rel_target = os.path.relpath(hub_domain_dir, satellite_root_resolved)
    os.symlink(rel_target, shared_contracts_link)

    if not shared_contracts_link.exists():
        sys.stderr.write(
            f"ERROR: Created symbolic link is dangling: '{shared_contracts_link}' -> '{rel_target}'.\n"
        )
        return 1

    # 4. Install Satellite local rule .agents/rules/contract_rules.md
    rules_dir = satellite_root_resolved / ".agents" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    contract_rules_path = rules_dir / "contract_rules.md"
    template_vars = {
        "hub_repo": hub_resolved.name or "D3Nexus",
        "domain": norm_domain,
        "timestamp": _get_timestamp(),
    }
    rule_tmpl = _load_template("satellite_rule.md.tmpl")
    atomic_write_text(contract_rules_path, rule_tmpl.substitute(template_vars))

    # 5. Check if AGENTS.md exists and append reference if needed
    agents_md_path = satellite_root_resolved / "AGENTS.md"
    if agents_md_path.is_file():
        agents_content = agents_md_path.read_text(encoding="utf-8")
        rule_reference = "@.agents/rules/contract_rules.md"
        if rule_reference not in agents_content:
            updated_content = agents_content.rstrip() + f"\n\n{rule_reference}\n"
            atomic_write_text(agents_md_path, updated_content)

    sys.stdout.write(
        f"SUCCESS: Satellite repository linked successfully.\n"
        f"Symlink: '{shared_contracts_link}' -> '{rel_target}'\n"
        f"Local Rule: '{contract_rules_path}'\n"
    )
    return 0


def cmd_verify(repo_root: Path) -> int:
    """Audit shared contracts configuration in Hub or Satellite workspace."""
    repo_root_resolved = repo_root.resolve()
    shared_contracts_path = repo_root_resolved / "shared-contracts"

    if (
        not shared_contracts_path.exists()
        and not shared_contracts_path.is_symlink()
        and not os.path.islink(shared_contracts_path)
    ):
        sys.stderr.write(
            f"ERROR: 'shared-contracts' does not exist in workspace: '{repo_root_resolved}'\n"
            "Run 'setup_contracts.py init-hub' or 'setup_contracts.py link-satellite' first.\n"
        )
        return 1

    errors: list[str] = []
    is_satellite = shared_contracts_path.is_symlink() or os.path.islink(shared_contracts_path)

    if not is_satellite:
        mode = "Hub"
        if not shared_contracts_path.is_dir():
            errors.append(f"Hub 'shared-contracts' must be a physical directory: '{shared_contracts_path}'")

        readme_file = shared_contracts_path / "README.md"
        if not readme_file.is_file():
            errors.append(f"Missing Hub topology README: '{readme_file}'")
        else:
            readme_text = readme_file.read_text(encoding="utf-8")
            if "Outbound Symlink Mappings" not in readme_text:
                errors.append(f"Hub README missing Outbound Symlink Mappings table: '{readme_file}'")

        domain_dirs = [
            d for d in shared_contracts_path.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
        for d in domain_dirs:
            for canonical in CANONICAL_CONTRACT_FILES:
                c_file = d / canonical
                if not c_file.is_file():
                    errors.append(f"Missing canonical file '{canonical}' in domain '{d.name}'")

        hub_rule = repo_root_resolved / ".agents" / "rules" / "contract_rules.md"
        if not hub_rule.is_file():
            errors.append(f"Missing Hub local contract rules: '{hub_rule}'")
        else:
            try:
                hub_rule_text = hub_rule.read_text(encoding="utf-8")
                if "single source of truth" not in hub_rule_text.lower():
                    errors.append(
                        f"Hub contract rule '{hub_rule}' missing Single Source of Truth (SSOT) constraints"
                    )
            except OSError as exc:
                errors.append(f"Unable to read Hub contract rule '{hub_rule}': {exc}")
    else:
        mode = "Satellite"
        try:
            raw_link = os.readlink(shared_contracts_path)
        except OSError as exc:
            errors.append(f"Cannot read symbolic link: {exc}")
            raw_link = ""

        if os.path.isabs(raw_link):
            errors.append(
                f"Satellite symlink MUST be a relative path, but is absolute: '{raw_link}'"
            )

        resolved_target, is_valid = resolve_symlink_safe(shared_contracts_path)
        if not is_valid:
            errors.append(
                f"Satellite symlink is broken, cyclical, or exceeds max depth (10 hops): "
                f"'{shared_contracts_path}' -> '{raw_link}'"
            )
        else:
            for canonical in CANONICAL_CONTRACT_FILES:
                c_file = resolved_target / canonical
                if not c_file.is_file():
                    errors.append(
                        f"Resolved satellite target missing canonical file '{canonical}' at '{c_file}'"
                    )

        sat_rule = repo_root_resolved / ".agents" / "rules" / "contract_rules.md"
        if not sat_rule.is_file():
            errors.append(f"Missing Satellite local contract rules: '{sat_rule}'")
        else:
            try:
                sat_rule_text = sat_rule.read_text(encoding="utf-8")
                required_markers = ("Satellite Consumer", "read-only", "NEVER stage")
                missing_markers = [
                    m for m in required_markers if m.lower() not in sat_rule_text.lower()
                ]
                if missing_markers:
                    errors.append(
                        f"Satellite contract rule '{sat_rule}' missing required Git read-only boundary constraints: "
                        f"{', '.join(missing_markers)}"
                    )
            except OSError as exc:
                errors.append(f"Unable to read Satellite contract rule '{sat_rule}': {exc}")

    if errors:
        sys.stderr.write(f"FAILED: Shared contracts verification found {len(errors)} error(s) ({mode} mode):\n")
        for err in errors:
            sys.stderr.write(f"  - {err}\n")
        return 1

    sys.stdout.write(
        f"PASS: Shared contracts verification succeeded for '{repo_root_resolved}' ({mode} mode)\n"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="setup_contracts.py",
        description="CLI engine for multi-repo shared contracts management.",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # init-hub
    parser_init = subparsers.add_parser(
        "init-hub",
        help="Initialize a physical Hub repository with canonical contract files.",
    )
    parser_init.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the Hub repository (default: current directory).",
    )
    parser_init.add_argument(
        "--domain",
        type=str,
        default=None,
        help="Domain name to register (e.g. lyrics-sync, nexus).",
    )
    parser_init.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing contract files if present.",
    )

    # link-satellite
    parser_link = subparsers.add_parser(
        "link-satellite",
        help="Link a satellite repository to Hub domain contracts via relative symlink.",
    )
    parser_link.add_argument(
        "--hub",
        type=Path,
        required=True,
        help="Path to the Hub repository root directory.",
    )
    parser_link.add_argument(
        "--domain",
        type=str,
        required=True,
        help="Domain name to link against (e.g. lyrics-sync).",
    )
    parser_link.add_argument(
        "--satellite-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the Satellite repository (default: current directory).",
    )
    parser_link.add_argument(
        "--force",
        action="store_true",
        help="Replace existing directory or symlink.",
    )

    # verify
    parser_verify = subparsers.add_parser(
        "verify",
        help="Verify shared contracts setup and integrity in Hub or Satellite mode.",
    )
    parser_verify.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory of the workspace (default: current directory).",
    )

    return parser


def main() -> int:
    """Entry point for CLI engine."""
    parser = build_parser()
    args = parser.parse_args()

    if args.subcommand == "init-hub":
        return cmd_init_hub(
            repo_root=args.repo_root,
            domain=args.domain,
            force=args.force,
        )
    if args.subcommand == "link-satellite":
        return cmd_link_satellite(
            hub=args.hub,
            domain=args.domain,
            satellite_root=args.satellite_root,
            force=args.force,
        )
    if args.subcommand == "verify":
        return cmd_verify(
            repo_root=args.repo_root,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
