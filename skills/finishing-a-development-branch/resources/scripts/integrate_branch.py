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

# Never hand-merged: taken from the base during the rebase, regenerated once afterwards.
REGENERATE_PATTERNS = (
    "*.g.dart", "*.freezed.dart", "*.mocks.dart", "*.gr.dart", "pubspec.lock", "Podfile.lock",
    "Package.resolved", "gradle.lockfile", "*.lockfile", "package-lock.json", "yarn.lock",
)
# A change to any of these upstream means the worktree needs a fresh bootstrap.
MANIFEST_PATTERNS = (
    "pubspec.yaml", "melos.yaml", "build.gradle", "build.gradle.kts", "settings.gradle",
    "settings.gradle.kts", "gradle/libs.versions.toml", "Package.swift", "Project.swift", "Podfile",
)


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


def merge_base(a: str, b: str) -> str:
    return out("merge-base", a, b)


def changed_files(a: str, b: str) -> list[str]:
    return [line for line in out("diff", "--name-only", a, b).splitlines() if line]


def git_path(name: str, cwd: Path | None = None) -> Path:
    path = Path(out("rev-parse", "--git-path", name, cwd=cwd))
    return path if path.is_absolute() else (cwd or Path.cwd()) / path


def rebase_in_progress(cwd: Path | None = None) -> bool:
    return git_path("rebase-merge", cwd).exists() or git_path("rebase-apply", cwd).exists()


def branch_name() -> str:
    """The branch being integrated -- read from the rebase state while HEAD is detached mid-rebase."""
    result = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    for state in ("rebase-merge", "rebase-apply"):
        head_name = git_path(state) / "head-name"
        if head_name.exists():
            return head_name.read_text().strip().removeprefix("refs/heads/")
    raise Refusal("HEAD is detached; check out the branch to integrate")


def integrating_branch(base: str) -> str:
    """The branch to integrate -- never the base itself, which has nothing to integrate."""
    branch = branch_name()
    if branch == base:
        raise Refusal(f"the current branch is the base '{base}'; run this from the branch's worktree")
    return branch


def pushed(branch: str) -> bool:
    """True when the branch tracks a remote branch; a local upstream (remote '.') is not a push."""
    remote = git("config", f"branch.{branch}.remote", check=False).stdout.strip()
    return remote not in ("", ".")


def dirty_files(cwd: Path | None = None, untracked: bool = True) -> list[str]:
    mode = "-uall" if untracked else "-uno"
    entries = git("status", "--porcelain", "-z", mode, cwd=cwd).stdout.split("\0")
    files, index = [], 0
    while index < len(entries):
        entry = entries[index]
        if entry:
            files.append(entry[3:])
            if entry[0] in "RC":  # a rename or copy carries its source path as the next entry
                index += 1
                files.append(entries[index])
        index += 1
    return files


def matches(path: str, patterns: tuple[str, ...]) -> bool:
    name = Path(path).name
    return any(fnmatch.fnmatch(path if "/" in pattern else name, pattern) for pattern in patterns)


def tag(path: str) -> str:
    return "regenerate" if matches(path, REGENERATE_PATTERNS) else "review"


def backup_ref(branch: str) -> str:
    return f"backup/{branch}"


def ref_exists(ref: str) -> bool:
    return succeeds("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")


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


# --- reports ------------------------------------------------------------------------------

def upstream_commits(since: str, until: str) -> list[str]:
    return [line for line in out("log", "--reverse", "--format=%h %s", f"{since}..{until}").splitlines() if line]


def upstream_epics(since: str, until: str) -> list[dict]:
    """Epic directories changed upstream, each with its BDD scenarios when present."""
    paths = changed_files(since, until)
    epic_dirs = sorted({Path(p).parts[2] for p in paths
                        if p.startswith(".devtool/epic/") and len(Path(p).parts) > 3})
    epics = []
    for epic_dir in epic_dirs:
        bdd = f".devtool/epic/{epic_dir}/bdd_scenarios.en.md"
        epics.append({"epic_dir": epic_dir,
                      "bdd": bdd if succeeds("cat-file", "-e", f"{until}:{bdd}") else None})
    return epics


def upstream_context(since: str, onto: str, head: str) -> dict:
    upstream_files = changed_files(since, onto)
    branch_files = set(changed_files(onto if is_ancestor(onto, head) else since, head))
    return {
        "upstream_commits": upstream_commits(since, onto),
        "upstream_epics": upstream_epics(since, onto),
        "overlap_files": sorted(branch_files.intersection(upstream_files)),
        "bootstrap_required": any(matches(p, MANIFEST_PATTERNS) for p in upstream_files),
    }


def predict(target: str, head: str) -> tuple[str, list[str]]:
    if is_ancestor(target, head):
        return "noop", []
    result = git("merge-tree", "--write-tree", "--name-only", "--no-messages", target, head, check=False)
    if result.returncode == 0:
        return "clean", []
    if result.returncode == 1:
        return "conflicts", sorted({line for line in result.stdout.splitlines()[1:] if line})
    raise GitError(f"git merge-tree failed: {result.stderr.strip()}")


# --- commands -----------------------------------------------------------------------------

def cmd_sync_base(args) -> tuple[int, dict]:
    state = sync_base(args.base, args.fetch)
    return EXIT_OK, {"command": "sync-base", "base": state.base, "upstream": state.upstream,
                     "relation": state.relation, "fast_forwarded": state.fast_forwarded,
                     "warnings": state.warnings}


def cmd_preflight(args) -> tuple[int, dict]:
    branch = integrating_branch(args.base)
    state = read_base(args.base, args.fetch)
    target = state.upstream if state.relation == "behind" else args.base
    head = rev("HEAD")
    since = merge_base(head, target)
    tier, conflicts = predict(target, head)
    warnings = list(state.warnings)
    if state.relation == "diverged":
        warnings.append(f"{args.base} and {state.upstream} have diverged; reconcile {args.base} first")
    if rebase_in_progress():
        warnings.append("a rebase is in progress; run rebase --continue or rebase --abort")
    if dirty_files(untracked=False):
        warnings.append("the worktree has uncommitted changes")
    if pushed(branch):
        warnings.append(f"{branch} has already been pushed; it will not be rebased")
    return EXIT_OK, {"command": "preflight", "branch": branch, "base": args.base,
                     "upstream": state.upstream, "relation": state.relation, "target": target,
                     "merge_base": since, "predicted_tier": tier,
                     "conflicts": [{"path": p, "tag": tag(p)} for p in conflicts],
                     **upstream_context(since, target, head), "warnings": warnings}


def rebase_outcome(branch: str, result: subprocess.CompletedProcess) -> tuple[int, dict]:
    if rebase_in_progress():
        conflicted = out("diff", "--name-only", "--diff-filter=U").splitlines()
        replaying = git("log", "-1", "--format=%h %s", "REBASE_HEAD", check=False).stdout.strip()
        return EXIT_CONFLICT, {"command": "rebase", "branch": branch, "result": "stopped",
                               "replaying": replaying,
                               "conflicts": [{"path": p, "tag": tag(p)} for p in conflicted if p]}
    if result.returncode != 0:
        raise GitError(f"git rebase failed: {result.stderr.strip()}")
    return EXIT_OK, {"command": "rebase", "branch": branch, "result": "complete", "head": rev("HEAD")}


def cmd_rebase(args) -> tuple[int, dict]:
    branch = integrating_branch(args.base)
    if args.abort or args.cont:
        if not rebase_in_progress():
            raise Refusal("no rebase is in progress")
        if args.abort:
            git("rebase", "--abort")
            restored = rev("HEAD") == rev(backup_ref(branch))
            return EXIT_OK, {"command": "rebase", "branch": branch, "result": "aborted",
                             "restored_to_backup": restored}
        result = git("-c", "rerere.enabled=true", "rebase", "--continue", check=False)
        return rebase_outcome(branch, result)
    if rebase_in_progress():
        raise Refusal("a rebase is already in progress; use rebase --continue or rebase --abort")
    if dirty_files(untracked=False):
        raise Refusal("the worktree has uncommitted changes; commit them before rebasing")
    if pushed(branch):
        raise Refusal(f"{branch} has already been pushed; rebasing it would need a force-push")
    sync_base(args.base, args.fetch)
    head = rev("HEAD")
    git("branch", "--force", backup_ref(branch), head)
    if is_ancestor(args.base, head):
        return EXIT_OK, {"command": "rebase", "branch": branch, "result": "noop", "head": head}
    result = git("-c", "rerere.enabled=true", "rebase", args.base, check=False)
    return rebase_outcome(branch, result)


def normalised_diff(a: str, b: str) -> list[str]:
    """A zero-context diff without blob ids or line numbers: what changed, not where."""
    lines = []
    for line in git("diff", "-U0", "--no-color", "--no-ext-diff", a, b).stdout.splitlines():
        if line.startswith("index "):
            continue
        lines.append("@@" if line.startswith("@@") else line)
    return lines


VERIFICATION = {
    "noop": {"finish": "keep the existing verdict",
             "task_boundary": "none"},
    "clean": {"finish": "full test suite, impact-analysis Check 2, regression checklist",
              "task_boundary": "analyze, build, Tier A unit tests"},
    "conflicts": {"finish": "the invoking lifecycle's full gate",
                  "task_boundary": "full 3-tier test suite"},
}


def cmd_verify_tier(args) -> tuple[int, dict]:
    branch = integrating_branch(args.base)
    if rebase_in_progress():
        raise Refusal("a rebase is in progress; finish or abort it first")
    head = rev("HEAD")
    onto = merge_base(head, args.base)
    backup = backup_ref(branch)
    if not ref_exists(backup) or rev(backup) == head:
        tier, since = "noop", onto
    else:
        since = merge_base(backup, onto)
        same = normalised_diff(since, backup) == normalised_diff(onto, head)
        tier = "clean" if same else "conflicts"
    return EXIT_OK, {"command": "verify-tier", "branch": branch, "tier": tier,
                     "verification": VERIFICATION[tier], "candidate_sha": head,
                     **upstream_context(since, onto, head)}


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
    add("preflight")
    rebase = add("rebase")
    mode = rebase.add_mutually_exclusive_group()
    mode.add_argument("--continue", dest="cont", action="store_true")
    mode.add_argument("--abort", action="store_true")
    add("verify-tier", fetch=False)
    return parser


COMMANDS = {"sync-base": cmd_sync_base, "preflight": cmd_preflight, "rebase": cmd_rebase,
            "verify-tier": cmd_verify_tier}


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
