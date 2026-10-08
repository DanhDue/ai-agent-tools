#!/usr/bin/env python3
"""Integrate a development branch with its base: rebase it, measure the result, land it.

`finishing-a-development-branch` and `dev-implementation` both rebase a branch onto
`develop` and must do it identically. This script owns the git mechanics; the skills own
the judgement -- how to classify a conflict, which verification a tier calls for.

    integrate_branch.py sync-base   [--base develop] [--no-fetch]
    integrate_branch.py preflight   [--base develop] [--no-fetch]
    integrate_branch.py rebase      [--base develop] [--no-fetch] [--continue | --abort]
    integrate_branch.py verify-tier [--base develop]
    integrate_branch.py land --verified <sha> --title "[SCOPE] Title" [--base develop] [--no-fetch]

Every command takes --format markdown|json. Exit codes: 0 success, 1 unexpected git
failure, 2 rebase stopped on conflicts, 3 precondition failed, 4 postcondition failed
after merging (rolled back).

Standard library only, like the kit's other scripts.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

EXIT_OK, EXIT_GIT, EXIT_CONFLICT, EXIT_PRECONDITION, EXIT_POSTCONDITION = 0, 1, 2, 3, 4
MIN_GIT = (2, 38)  # git merge-tree --write-tree


class GitError(Exception):
    """A git command failed where failure was not expected."""


class Refusal(Exception):
    """A precondition or postcondition failed; the message says what to do."""

    def __init__(self, message: str, code: int = EXIT_PRECONDITION):
        super().__init__(message)
        self.code = code


# --- git plumbing -------------------------------------------------------------------------

def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    env = dict(os.environ, GIT_EDITOR="true")  # rebase --continue must never open an editor
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env)
    if check and result.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result


def out(*args: str, cwd: Path | None = None) -> str:
    return git(*args, cwd=cwd).stdout.strip()


def succeeds(*args: str, cwd: Path | None = None) -> bool:
    return git(*args, cwd=cwd, check=False).returncode == 0


def rev(ref: str, cwd: Path | None = None) -> str:
    return out("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}", cwd=cwd)


def is_ancestor(ancestor: str, descendant: str) -> bool:
    return succeeds("merge-base", "--is-ancestor", ancestor, descendant)


def check_git_version() -> None:
    match = re.search(r"(\d+)\.(\d+)", out("--version"))
    if not match or (int(match.group(1)), int(match.group(2))) < MIN_GIT:
        raise Refusal(f"git {MIN_GIT[0]}.{MIN_GIT[1]} or newer is required for merge-tree --write-tree")


def upstream_of(branch: str) -> str | None:
    result = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{branch}@{{upstream}}",
                 check=False)
    return result.stdout.strip() if result.returncode == 0 else None


def checkout_of(branch: str) -> Path | None:
    """The checkout that has `branch` checked out, or None."""
    current: dict[str, str] = {}
    for line in out("worktree", "list", "--porcelain").splitlines() + [""]:
        if line:
            key, _, value = line.partition(" ")
            current[key] = value
            continue
        if current.get("branch") == f"refs/heads/{branch}":
            return Path(current["worktree"])
        current = {}
    return None


# --- resolve base -------------------------------------------------------------------------

@dataclass
class BaseState:
    base: str
    upstream: str | None
    relation: str  # local-only | equal | ahead | behind | diverged
    fast_forwarded: bool = False
    warnings: list[str] = field(default_factory=list)


def fetch_upstream(branch: str) -> str | None:
    """Fetch the branch's upstream; return a warning instead of failing when offline."""
    remote = git("config", f"branch.{branch}.remote", check=False).stdout.strip()
    merge = git("config", f"branch.{branch}.merge", check=False).stdout.strip()
    if not remote or not merge or remote == ".":
        return None
    result = git("fetch", "--quiet", remote, merge, check=False)
    if result.returncode != 0:
        return f"fetch from {remote} failed, using the last known {remote} state: {result.stderr.strip()}"
    return None


def read_base(base: str, fetch: bool) -> BaseState:
    """Fetch and compare -- never moves a local branch."""
    if not succeeds("rev-parse", "--verify", "--quiet", f"refs/heads/{base}"):
        raise Refusal(f"base branch '{base}' does not exist")
    upstream = upstream_of(base)
    if upstream is None:
        return BaseState(base, None, "local-only")
    warnings = []
    if fetch:
        warning = fetch_upstream(base)
        if warning:
            warnings.append(warning)
    local, remote = rev(base), rev(upstream)
    if local == remote:
        relation = "equal"
    elif is_ancestor(remote, local):
        relation = "ahead"
    elif is_ancestor(local, remote):
        relation = "behind"
    else:
        relation = "diverged"
    return BaseState(base, upstream, relation, warnings=warnings)


def sync_base(base: str, fetch: bool) -> BaseState:
    """Resolve the base, fast-forwarding a local base that is strictly behind its upstream."""
    state = read_base(base, fetch)
    if state.relation == "diverged":
        raise Refusal(f"{base} and {state.upstream} have diverged; reconcile {base} before integrating")
    if state.relation == "behind":
        fast_forward(base, state.upstream)
        state.fast_forwarded = True
    return state


def fast_forward(base: str, upstream: str) -> None:
    checkout = checkout_of(base)
    if checkout is None:  # no working tree to keep in step: move the ref atomically
        git("update-ref", f"refs/heads/{base}", rev(upstream), rev(base))
        return
    result = git("merge", "--ff-only", "--quiet", upstream, cwd=checkout, check=False)
    if result.returncode != 0:
        raise Refusal(f"cannot fast-forward {base} in {checkout}: {result.stderr.strip()}")


# --- commands -----------------------------------------------------------------------------

def cmd_sync_base(args) -> tuple[int, dict]:
    state = sync_base(args.base, args.fetch)
    return EXIT_OK, {"command": "sync-base", "base": state.base, "upstream": state.upstream,
                     "relation": state.relation, "fast_forwarded": state.fast_forwarded,
                     "warnings": state.warnings}


# --- entry point --------------------------------------------------------------------------

def to_markdown(report: dict) -> str:
    lines = [f"## integrate_branch {report['command']}", ""]
    for key, value in report.items():
        if key == "command":
            continue
        label = key.replace("_", " ")
        if isinstance(value, list):
            lines.append(f"- **{label}**:" + ("" if value else " none"))
            for item in value:
                text = ", ".join(f"{k}: {v}" for k, v in item.items()) if isinstance(item, dict) else item
                lines.append(f"  - {text}")
        elif isinstance(value, dict):
            lines.append(f"- **{label}**:")
            lines.extend(f"  - {k}: {v}" for k, v in value.items())
        else:
            lines.append(f"- **{label}**: {value}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebase, measure and land a development branch.")
    commands = parser.add_subparsers(dest="command", required=True)

    def add(name: str, fetch: bool = True) -> argparse.ArgumentParser:
        sub = commands.add_parser(name)
        sub.add_argument("--base", default="develop")
        sub.add_argument("--format", choices=("markdown", "json"), default="markdown")
        if fetch:
            sub.add_argument("--no-fetch", dest="fetch", action="store_false")
        return sub

    add("sync-base")
    return parser


COMMANDS = {"sync-base": cmd_sync_base}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        check_git_version()
        code, report = COMMANDS[args.command](args)
    except Refusal as refusal:
        print(f"error: {refusal}", file=sys.stderr)
        return refusal.code
    except GitError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_GIT
    print(json.dumps(report, indent=2) if args.format == "json" else to_markdown(report))
    return code


if __name__ == "__main__":
    sys.exit(main())
