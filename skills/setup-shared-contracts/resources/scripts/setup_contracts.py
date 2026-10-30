#!/usr/bin/env python3
"""CLI Engine for managing multi-repo shared contracts across Hub and Satellite repositories."""

from __future__ import annotations

import argparse
import datetime
import os
import string
import sys
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def _get_timestamp() -> str:
    """Return ISO-8601 UTC timestamp."""
    return datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_template(name: str) -> string.Template:
    """Load a template file and return string.Template instance."""
    path = TEMPLATES_DIR / name
    if not path.is_file():
        raise FileNotFoundError(f"Canonical template not found: {path}")
    return string.Template(path.read_text(encoding="utf-8"))


def _update_readme_table(readme_path: Path, domain: str) -> None:
    """Ensure domain is registered in the Outbound Symlink Mappings table."""
    content = readme_path.read_text(encoding="utf-8")
    if f"| {domain} " in content or f"|{domain}|" in content:
        return

    table_header = "| Domain | Target Path | Target Satellites | Status |"
    table_separator = "|---|---|---|---|"
    new_row = f"| {domain} | shared-contracts/{domain} | {domain} | Active |"

    if table_separator in content:
        parts = content.split(table_separator, 1)
        updated = f"{parts[0]}{table_separator}\n{new_row}{parts[1]}"
        readme_path.write_text(updated, encoding="utf-8")
    elif table_header in content:
        parts = content.split(table_header, 1)
        updated = f"{parts[0]}{table_header}\n{table_separator}\n{new_row}{parts[1]}"
        readme_path.write_text(updated, encoding="utf-8")
    else:
        # Append table if missing
        table_block = (
            f"\n## Outbound Symlink Mappings\n\n"
            f"{table_header}\n{table_separator}\n{new_row}\n"
        )
        readme_path.write_text(content + table_block, encoding="utf-8")


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
    primary_domain = domain if domain else "general"

    template_vars = {
        "hub_repo": hub_repo_name,
        "domain": primary_domain,
        "timestamp": timestamp,
    }

    # 2. Render shared-contracts/README.md
    readme_path = shared_contracts_dir / "README.md"
    if not readme_path.exists() or force:
        tmpl = _load_template("hub_readme.md.tmpl")
        readme_path.write_text(tmpl.substitute(template_vars), encoding="utf-8")
    elif domain:
        _update_readme_table(readme_path, domain)

    # 3. Create domain subfolder with 3 canonical files
    if domain:
        domain_dir = shared_contracts_dir / domain
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
                target_file.write_text(tmpl.substitute(template_vars), encoding="utf-8")

    # 4. Install Hub local rule .agents/rules/contract_rules.md
    rules_dir = repo_root / ".agents" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    contract_rules_path = rules_dir / "contract_rules.md"
    if not contract_rules_path.exists() or force:
        rule_tmpl = _load_template("hub_rule.md.tmpl")
        contract_rules_path.write_text(rule_tmpl.substitute(template_vars), encoding="utf-8")

    sys.stdout.write(
        f"SUCCESS: Hub repository initialized at '{shared_contracts_dir}'\n"
        f"SSOT Local Rule: '{contract_rules_path}'\n"
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
