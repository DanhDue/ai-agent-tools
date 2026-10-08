# Kế hoạch triển khai tích hợp rebase cho finishing branch

> **Dành cho agent thực thi:** SUB-SKILL BẮT BUỘC: dùng d3nexus:subagent-driven-development (khuyến nghị) hoặc d3nexus:executing-plans để triển khai plan này theo từng task. Các bước dùng cú pháp checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Tích hợp các nhánh phát triển bằng cách rebase chúng lên `develop` ngay trong worktree,
verify lại theo tier, và chỉ land tree đã verify bằng một merge `--no-ff` — cả lúc finish lẫn sau mỗi
task của epic.

**Kiến trúc:** Một script chỉ dùng thư viện chuẩn, `integrate_branch.py`, nắm phần cơ chế git qua năm
lệnh (`sync-base`, `preflight`, `rebase`, `verify-tier`, `land`) và được test như một CLI trên các repo
tạm. Ba skill dùng nó: `finishing-a-development-branch` lúc finish, `dev-implementation` sau mỗi task,
còn `dev-lifecycle` ghi lại các gate mới. Một playbook giải conflict giữ phần phán đoán mà script không
làm được.

**Công nghệ:** Thư viện chuẩn Python 3.10, git 2.38 trở lên, `unittest`, bash, skill Markdown.

**Spec:** [2026-10-09-finishing-branch-rebase-design.vi.md](../specs/2026-10-09-finishing-branch-rebase-design.vi.md)

## Mục lục

- [Ràng buộc chung](#ràng-buộc-chung)
- [Cấu trúc file](#cấu-trúc-file)
- [Độ phủ spec](#độ-phủ-spec)
- [Các task](#các-task)
- [Task 1: Nền tảng script và sync-base](#task-1-nền-tảng-script-và-sync-base)
- [Task 2: preflight](#task-2-preflight)
- [Task 3: rebase](#task-3-rebase)
- [Task 4: verify-tier](#task-4-verify-tier)
- [Task 5: land](#task-5-land)
- [Task 6: Skill finishing và playbook giải conflict](#task-6-skill-finishing-và-playbook-giải-conflict)
- [Task 7: Tích hợp sau mỗi task trong dev-implementation](#task-7-tích-hợp-sau-mỗi-task-trong-dev-implementation)
- [Task 8: Các gate của dev-lifecycle](#task-8-các-gate-của-dev-lifecycle)
- [Task 9: Kiểm chứng trước release](#task-9-kiểm-chứng-trước-release)

## Ràng buộc chung

- Python 3.10 trở lên, chỉ dùng thư viện chuẩn, giống các script khác trong kit.
- git 2.38 trở lên (`git merge-tree --write-tree`); script từ chối phiên bản cũ hơn với exit 3.
- Nhánh base mặc định: `develop`. Mọi lệnh nhận `--base <branch>` và `--format markdown|json`.
- Exit code: `0` thành công, `1` lỗi git ngoài dự kiến, `2` rebase dừng vì conflict, `3` không đạt
  điều kiện trước, `4` không đạt điều kiện sau khi merge (đã rollback).
- Format commit theo `rules/CRITICAL_RULES.md`: `[SCOPE] Title` kèm body dạng bullet; không bao giờ
  có `Co-Authored-By` hay bất kỳ trailer nào. Scope của plan này: `[FINISHING_BRANCH_REBASE]`.
- Không bao giờ `git push`.
- Làm việc trên một nhánh tách từ `main` trong một worktree cô lập (`d3nexus:using-git-worktrees`).
  Repo này không có `develop`.
- Frontmatter của `SKILL.md` giữ đúng `name` + `description`. Tham chiếu chéo dùng `d3nexus:`.
- Chỉnh sửa nội dung skill theo `d3nexus:writing-skills`: một pressure scenario nền trước khi sửa, và
  chạy lại đúng scenario đó sau khi sửa.
- Các bước pressure scenario (Task 6, 7 và 8) dispatch subagent mới, mà implementer subagent thì không
  dispatch được subagent của riêng nó. Khi chạy dưới `d3nexus:subagent-driven-development`,
  controller tự chạy bước RED trước khi dispatch implementer, và bước GREEN sau khi implementer báo
  cáo.
- Chỉ sửa có phạm vi hẹp. Năm code fence không có language tag sẵn có trong
  `skills/finishing-a-development-branch/SKILL.md` (MD040) là từ trước và được giữ nguyên.

## Cấu trúc file

| Đường dẫn | Hành động | Trách nhiệm |
|-----------|-----------|-------------|
| `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py` | Tạo | Cơ chế git: resolve base, báo cáo, rebase, đo tier, land |
| `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py` | Tạo | Test CLI trên các repo tạm, mỗi lệnh một class |
| `skills/finishing-a-development-branch/references/conflict-playbook.md` | Tạo | Phân loại conflict và mẫu câu hỏi khi dừng |
| `skills/finishing-a-development-branch/SKILL.md` | Sửa | Mục Update onto Base; Option 1 land qua script; tìm script qua `SKILL_DIR` |
| `skills/dev-implementation/SKILL.md` | Sửa | `sync-base` trước khi tạo worktree; Phase 2 step 7; xin phép ở Gate 3; bỏ bước restore ở Phase 5 |
| `skills/dev-lifecycle/SKILL.md` | Sửa | Câu chữ Stage 3, ghi chú Gate 4, exit của Stage 4, hai red flag |
| `scripts/verify.sh` | Sửa | Step 12 chạy bộ test mới |

## Độ phủ spec

| Mục trong spec | Task |
|----------------|------|
| 6.1 Resolve base | 1 |
| 6.2 `preflight`, pattern regenerate và manifest | 2 |
| 6.2 `rebase`, backup ref, rerere | 3 |
| 6.3 Đo tier | 4 |
| 6.2 Chi tiết `land`, 6.4 Exit code | 1 đến 5 |
| 7 Luồng finishing, 10 Playbook giải conflict, lỗi 6 | 6 |
| 8 Tích hợp sau mỗi task, lỗi 5 | 6 và 7 |
| 9 Thay đổi lifecycle | 8 |
| 11 Xử lý lỗi | 1 đến 5, 6 |
| 12 Kiểm thử | 1 đến 5, 9 |

## Các task

### Task 1: Nền tảng script và sync-base

**File:**

- Tạo: `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- Tạo: `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`
- Sửa: `scripts/verify.sh` (step 11, gần cuối file)

**Interface:**

- Dùng: không có.
- Cung cấp: CLI `integrate_branch.py sync-base [--base B] [--no-fetch] [--format json]` in ra
  `{"command", "base", "upstream", "relation", "fast_forwarded", "warnings"}`, trong đó `relation` là
  một trong `local-only`, `equal`, `ahead`, `behind`, `diverged`. Các tên Python mà task sau dùng:
  `git(*args, cwd=None, check=True)`, `out(*args, cwd=None) -> str`, `succeeds(*args, cwd=None) -> bool`,
  `rev(ref, cwd=None) -> str`, `is_ancestor(a, b) -> bool`, `upstream_of(branch) -> str | None`,
  `checkout_of(branch) -> Path | None`, `read_base(base, fetch) -> BaseState`,
  `sync_base(base, fetch) -> BaseState`, `Refusal(message, code=EXIT_PRECONDITION)`, `GitError`,
  `COMMANDS`, `build_parser()` cùng hàm lồng `add(name, fetch=True)`. Các banner
  `# --- git plumbing`, `# --- resolve base`, `# --- commands`, `# --- entry point` là mốc chèn cho
  Task 2 đến 5. Fixture test `RepoTestCase` có `add_remote()`,
  `push_from_elsewhere(path, content, message)`, `add_epic(name="demo")`, `conflicting_epic()`, cùng
  các helper `git`, `commit`, `edit_line`, `integrate`, `LINES`.

- [ ] **Step 1: Viết test fail**

Tạo `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`:

```python
#!/usr/bin/env python3
"""Tests for integrate_branch.py, run as a CLI against real temporary git repositories.

Run: python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).parent / "integrate_branch.py"
# Isolate every git call from the developer's own configuration (signing, hooks, aliases).
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test Dev",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test Dev",
    "GIT_COMMITTER_EMAIL": "test@example.com",
}
LINES = "".join(f"line {n}\n" for n in range(1, 11))


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                          text=True).stdout.strip()


def commit(cwd: Path, path: str, content: str, message: str) -> str:
    target = cwd / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    git(cwd, "add", path)
    git(cwd, "commit", "-q", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


def edit_line(content: str, number: int, text: str) -> str:
    lines = content.splitlines(keepends=True)
    lines[number - 1] = text + "\n"
    return "".join(lines)


def integrate(cwd: Path, *args: str) -> tuple[int, dict | None, str]:
    result = subprocess.run([sys.executable, str(SCRIPT), *args, "--format", "json"], cwd=cwd,
                            capture_output=True, text=True)
    data = json.loads(result.stdout) if result.stdout.strip() else None
    return result.returncode, data, result.stderr


class RepoTestCase(unittest.TestCase):
    """A main checkout on `develop`, optionally an `origin` bare remote, and epic worktrees."""

    def setUp(self):
        patcher = mock.patch.dict(os.environ, GIT_ENV)
        patcher.start()
        self.addCleanup(patcher.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.main = self.root / "main"
        self.main.mkdir()
        git(self.main, "init", "-q", "-b", "develop")
        commit(self.main, "lib/app.dart", LINES, "Initial commit")

    def add_remote(self) -> None:
        self.remote = self.root / "remote.git"
        git(self.root, "clone", "-q", "--bare", str(self.main), str(self.remote))
        git(self.main, "remote", "add", "origin", str(self.remote))
        git(self.main, "fetch", "-q", "origin")
        git(self.main, "branch", "-q", "--set-upstream-to", "origin/develop", "develop")

    def push_from_elsewhere(self, path: str, content: str, message: str) -> str:
        other = self.root / "other"
        if not other.exists():
            git(self.root, "clone", "-q", "-b", "develop", str(self.remote), str(other))
        git(other, "pull", "-q", "--ff-only")
        sha = commit(other, path, content, message)
        git(other, "push", "-q", "origin", "develop")
        return sha

    def add_epic(self, name: str = "demo") -> Path:
        worktree = self.root / f"wt-{name}"
        git(self.main, "worktree", "add", "-q", str(worktree), "-b", f"epic/{name}", "develop")
        return worktree

    def conflicting_epic(self) -> tuple[Path, str]:
        epic = self.add_epic()
        head = commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 3, "upstream line 3"), "Upstream edit")
        return epic, head


class TestSyncBase(RepoTestCase):
    def test_no_upstream_uses_local_base(self):
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual(code, 0)
        self.assertEqual(data["relation"], "local-only")

    def test_local_ahead_is_kept(self):
        self.add_remote()
        local = commit(self.main, "lib/local.dart", "local\n", "Local merge")
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual((code, data["relation"]), (0, "ahead"))
        self.assertEqual(git(self.main, "rev-parse", "develop"), local)

    def test_local_behind_fast_forwards_the_base_checkout(self):
        self.add_remote()
        pushed = self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual((code, data["relation"], data["fast_forwarded"]), (0, "behind", True))
        self.assertEqual(git(self.main, "rev-parse", "develop"), pushed)
        self.assertTrue((self.main / "lib/remote.dart").exists())

    def test_diverged_base_stops(self):
        self.add_remote()
        self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        commit(self.main, "lib/local.dart", "local\n", "Local merge")
        code, _, stderr = integrate(self.main, "sync-base")
        self.assertEqual(code, 3)
        self.assertIn("diverged", stderr)

    def test_fetch_failure_warns_and_continues(self):
        self.add_remote()
        git(self.main, "remote", "set-url", "origin", str(self.root / "missing.git"))
        code, data, _ = integrate(self.main, "sync-base")
        self.assertEqual(code, 0)
        self.assertIn("fetch from origin failed", data["warnings"][0])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Chạy test để xác nhận nó fail**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `FAILED (failures=3, errors=2)` — script chưa tồn tại nên mọi lời gọi đều exit 2 và không
có JSON: các assertion về exit code fail, còn việc đọc JSON không có sẽ ném `TypeError`.

- [ ] **Step 3: Viết implementation tối thiểu**

Tạo `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`:

```python
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
```

Import `fnmatch` chưa được dùng cho tới Task 2; thêm ngay từ giờ để các task sau chỉ phải chèn hàm.

- [ ] **Step 4: Chạy test để xác nhận nó pass**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `Ran 5 tests` … `OK`.

- [ ] **Step 5: Đăng ký bộ test trong verify.sh**

Trong `scripts/verify.sh`, thay:

```bash
python3 scripts/test_lifecycle_document_contract.py || FAILED=1
```

bằng:

```bash
python3 scripts/test_lifecycle_document_contract.py || FAILED=1

echo
note "== 12. Branch integration script behaves =="
python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py || FAILED=1
```

Chạy: `bash scripts/verify.sh 2>&1 | tail -8`

Kỳ vọng: step 12 báo `Ran 5 tests` … `OK`, và dòng cuối là `PASS — safe to publish`.

- [ ] **Step 6: Commit**

```bash
git add skills/finishing-a-development-branch/resources/scripts/ scripts/verify.sh
git commit -m "[FINISHING_BRANCH_REBASE] Add integrate_branch.py with sync-base" -m "- resolve the base against its upstream: fetch, fast-forward, stop on divergence
- CLI tests against temporary repositories
- run the suite from verify.sh step 12"
```

### Task 2: preflight

**File:**

- Sửa: `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- Test: `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`

**Interface:**

- Dùng: các helper và mốc chèn của Task 1.
- Cung cấp: CLI `preflight` in ra `{"command", "branch", "base", "upstream", "relation", "target",
  "merge_base", "predicted_tier", "conflicts": [{"path", "tag"}], "upstream_commits",
  "upstream_epics": [{"epic_dir", "bdd"}], "overlap_files", "bootstrap_required", "warnings"}`.
  Tên Python: `merge_base(a, b) -> str`, `changed_files(a, b) -> list[str]`,
  `git_path(name, cwd=None) -> Path`, `rebase_in_progress(cwd=None) -> bool`,
  `branch_name() -> str`, `integrating_branch(base) -> str` (từ chối chính nhánh base),
  `pushed(branch) -> bool` (upstream local không tính là đã push),
  `dirty_files(cwd=None, untracked=True) -> list[str]`, `tag(path) -> "regenerate" | "review"`,
  `upstream_context(since, onto, head) -> dict`, `REGENERATE_PATTERNS`, `MANIFEST_PATTERNS`.

- [ ] **Step 1: Viết test fail**

Trong `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `if __name__ == "__main__":`:

```python
class TestPreflight(RepoTestCase):
    def test_noop_when_base_has_not_moved(self):
        epic = self.add_epic()
        commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "noop"))
        self.assertEqual(data["upstream_commits"], [])

    def test_reports_upstream_work_epics_overlap_and_manifests(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 8, "upstream line 8"), "Upstream edit")
        commit(self.main, ".devtool/epic/other_epic/bdd_scenarios.en.md", "# BDD\n", "Other epic")
        commit(self.main, "pubspec.yaml", "name: app\n", "Add dependency")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "clean"))
        self.assertEqual(len(data["upstream_commits"]), 3)
        self.assertEqual(data["upstream_epics"], [
            {"epic_dir": "other_epic", "bdd": ".devtool/epic/other_epic/bdd_scenarios.en.md"}])
        self.assertEqual(data["overlap_files"], ["lib/app.dart"])
        self.assertTrue(data["bootstrap_required"])

    def test_predicts_conflicts_and_tags_generated_files(self):
        epic, _ = self.conflicting_epic()
        commit(epic, "pubspec.lock", "epic: 1\n", "Lock epic")
        commit(self.main, "pubspec.lock", "upstream: 1\n", "Lock upstream")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["predicted_tier"]), (0, "conflicts"))
        self.assertEqual(data["conflicts"], [{"path": "lib/app.dart", "tag": "review"},
                                             {"path": "pubspec.lock", "tag": "regenerate"}])

    def test_refuses_to_integrate_the_base_itself(self):
        code, _, stderr = integrate(self.main, "preflight")
        self.assertEqual(code, 3)
        self.assertIn("is the base", stderr)

    def test_does_not_move_a_base_that_is_behind(self):
        self.add_remote()
        epic = self.add_epic()
        before = git(self.main, "rev-parse", "develop")
        self.push_from_elsewhere("lib/remote.dart", "remote\n", "Remote work")
        code, data, _ = integrate(epic, "preflight")
        self.assertEqual((code, data["relation"], data["target"]), (0, "behind", "origin/develop"))
        self.assertEqual(git(self.main, "rev-parse", "develop"), before)
        self.assertEqual(data["predicted_tier"], "clean")
```

- [ ] **Step 2: Chạy test để xác nhận nó fail**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `FAILED (failures=1, errors=4)` — argparse từ chối `preflight` với exit 2 và không có JSON,
nên test chặn base fail ở exit code còn bốn test kia ném `TypeError`; năm test của `TestSyncBase` vẫn
pass.

- [ ] **Step 3: Viết implementation tối thiểu**

Trong `integrate_branch.py`, chèn ngay phía dưới dòng bắt đầu bằng `MIN_GIT =`:

```python

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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- resolve base`:

```python
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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- commands`:

```python
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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- entry point`:

```python
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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `return parser`:

```python
    add("preflight")
```

Trong `integrate_branch.py`, thay câu lệnh `COMMANDS` bằng:

```python
COMMANDS = {"sync-base": cmd_sync_base, "preflight": cmd_preflight}
```

- [ ] **Step 4: Chạy test để xác nhận nó pass**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `Ran 10 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/finishing-a-development-branch/resources/scripts/
git commit -m "[FINISHING_BRANCH_REBASE] Add the preflight report" -m "- predict the tier with merge-tree and tag regenerate files
- list upstream commits, upstream epics and overlap files
- flag manifest changes that need a fresh bootstrap
- refuse to integrate the base branch itself"
```

### Task 3: rebase

**File:**

- Sửa: `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- Test: `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`

**Interface:**

- Dùng: Task 1 và 2 (`sync_base`, `branch_name`, `rebase_in_progress`, `dirty_files`, `tag`).
- Cung cấp: CLI `rebase [--continue | --abort]` in ra `{"command", "branch", "result", ...}` trong đó
  `result` là `noop`, `complete`, `stopped` (exit 2, kèm `replaying` và `conflicts`) hoặc `aborted`
  (kèm `restored_to_backup`). Backup ref là `backup/<branch>`, được ghi lại ở mỗi lần gọi `rebase`.
  Tên Python: `backup_ref(branch) -> str`.

- [ ] **Step 1: Viết test fail**

Trong `test_integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `if __name__ == "__main__":`:

```python
class TestRebase(RepoTestCase):
    def test_refuses_a_dirty_worktree(self):
        epic = self.add_epic()
        (epic / "lib/app.dart").write_text("dirty\n")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("uncommitted", stderr)

    def test_refuses_a_branch_that_was_pushed(self):
        self.add_remote()
        epic = self.add_epic()
        git(epic, "push", "-q", "-u", "origin", "epic/demo")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("force-push", stderr)

    def test_a_local_upstream_is_not_a_push(self):
        epic = self.add_epic()
        git(epic, "branch", "-q", "--set-upstream-to", "develop")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "noop"))

    def test_refuses_a_detached_head(self):
        epic = self.add_epic()
        git(epic, "checkout", "-q", "--detach")
        code, _, stderr = integrate(epic, "rebase")
        self.assertEqual(code, 3)
        self.assertIn("detached", stderr)

    def test_noop_records_the_backup(self):
        epic = self.add_epic()
        head = commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "noop"))
        self.assertEqual(git(epic, "rev-parse", "backup/epic/demo"), head)

    def test_clean_rebase_replays_onto_the_base(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 5, "upstream line 5"), "Upstream edit")
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (0, "complete"))
        content = (epic / "lib/app.dart").read_text()
        self.assertIn("epic line 3", content)
        self.assertIn("upstream line 5", content)

    def test_conflict_stops_then_continue_completes(self):
        epic, _ = self.conflicting_epic()
        code, data, _ = integrate(epic, "rebase")
        self.assertEqual((code, data["result"]), (2, "stopped"))
        self.assertEqual(data["conflicts"], [{"path": "lib/app.dart", "tag": "review"}])
        self.assertIn("Task 1", data["replaying"])
        (epic / "lib/app.dart").write_text(edit_line(LINES, 3, "epic and upstream line 3"))
        git(epic, "add", "lib/app.dart")
        code, data, _ = integrate(epic, "rebase", "--continue")
        self.assertEqual((code, data["result"]), (0, "complete"))

    def test_abort_restores_the_backup(self):
        epic, head = self.conflicting_epic()
        self.assertEqual(integrate(epic, "rebase")[0], 2)
        code, data, _ = integrate(epic, "rebase", "--abort")
        self.assertEqual((code, data["result"], data["restored_to_backup"]), (0, "aborted", True))
        self.assertEqual(git(epic, "rev-parse", "HEAD"), head)
```

- [ ] **Step 2: Chạy test để xác nhận nó fail**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `FAILED (failures=3, errors=5)` — `rebase` chưa phải lệnh hợp lệ, nên ba test từ chối fail
ở exit code và năm test ném `TypeError` vì không có JSON; mười test trước đó pass.

- [ ] **Step 3: Viết implementation tối thiểu**

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- resolve base`:

```python
def backup_ref(branch: str) -> str:
    return f"backup/{branch}"
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- entry point`:

```python
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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `return parser`:

```python
    rebase = add("rebase")
    mode = rebase.add_mutually_exclusive_group()
    mode.add_argument("--continue", dest="cont", action="store_true")
    mode.add_argument("--abort", action="store_true")
```

Trong `integrate_branch.py`, thay câu lệnh `COMMANDS` bằng:

```python
COMMANDS = {"sync-base": cmd_sync_base, "preflight": cmd_preflight, "rebase": cmd_rebase}
```

- [ ] **Step 4: Chạy test để xác nhận nó pass**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `Ran 18 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/finishing-a-development-branch/resources/scripts/
git commit -m "[FINISHING_BRANCH_REBASE] Add the rebase command" -m "- refuse dirty, detached, pushed or mid-rebase branches; a local upstream is not a push
- record backup/<branch> before every rebase and enable rerere
- wrap --continue and --abort, reporting conflicts with their tags"
```

### Task 4: verify-tier

**File:**

- Sửa: `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- Test: `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`

**Interface:**

- Dùng: Task 1 đến 3 (`backup_ref`, `merge_base`, `upstream_context`).
- Cung cấp: CLI `verify-tier` in ra `{"command", "branch", "tier", "verification": {"finish",
  "task_boundary"}, "candidate_sha", "upstream_commits", "upstream_epics", "overlap_files",
  "bootstrap_required"}`, trong đó `tier` là `noop`, `clean` hoặc `conflicts`. Tên Python:
  `ref_exists(ref) -> bool`.

- [ ] **Step 1: Viết test fail**

Trong `test_integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `if __name__ == "__main__":`:

```python
class TestVerifyTier(RepoTestCase):
    def test_noop_without_any_rebase(self):
        epic = self.add_epic()
        commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        code, data, _ = integrate(epic, "verify-tier")
        self.assertEqual((code, data["tier"]), (0, "noop"))

    def test_noop_after_a_noop_rebase(self):
        epic = self.add_epic()
        commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        self.assertEqual(integrate(epic, "rebase")[0], 0)
        code, data, _ = integrate(epic, "verify-tier")
        self.assertEqual((data["tier"], data["verification"]["task_boundary"]), ("noop", "none"))

    def test_clean_when_upstream_only_changed_nearby_lines(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/app.dart", edit_line(LINES, 5, "upstream line 5"), "Upstream edit")
        self.assertEqual(integrate(epic, "rebase")[0], 0)
        code, data, _ = integrate(epic, "verify-tier")
        self.assertEqual((code, data["tier"]), (0, "clean"))
        self.assertEqual(data["candidate_sha"], git(epic, "rev-parse", "HEAD"))
        self.assertEqual(len(data["upstream_commits"]), 1)
        self.assertEqual(data["overlap_files"], ["lib/app.dart"])

    def test_conflicts_after_a_resolved_conflict(self):
        epic, _ = self.conflicting_epic()
        self.assertEqual(integrate(epic, "rebase")[0], 2)
        (epic / "lib/app.dart").write_text(edit_line(LINES, 3, "epic and upstream line 3"))
        git(epic, "add", "lib/app.dart")
        self.assertEqual(integrate(epic, "rebase", "--continue")[0], 0)
        code, data, _ = integrate(epic, "verify-tier")
        self.assertEqual((code, data["tier"]), (0, "conflicts"))

    def test_a_commit_after_a_clean_rebase_raises_the_tier(self):
        epic = self.add_epic()
        commit(epic, "lib/app.dart", edit_line(LINES, 3, "epic line 3"), "Task 1")
        commit(self.main, "lib/other.dart", "upstream\n", "Upstream edit")
        self.assertEqual(integrate(epic, "rebase")[0], 0)
        commit(epic, "lib/app.g.dart", "regenerated\n", "Regenerate after rebase onto develop")
        code, data, _ = integrate(epic, "verify-tier")
        self.assertEqual(data["tier"], "conflicts")

    def test_refuses_while_a_rebase_is_in_progress(self):
        epic, _ = self.conflicting_epic()
        self.assertEqual(integrate(epic, "rebase")[0], 2)
        code, _, stderr = integrate(epic, "verify-tier")
        self.assertEqual(code, 3)
        self.assertIn("in progress", stderr)
```

- [ ] **Step 2: Chạy test để xác nhận nó fail**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `FAILED (failures=1, errors=5)` — `verify-tier` chưa phải lệnh hợp lệ, nên test từ chối
fail ở exit code và năm test ném `TypeError` vì không có JSON; mười tám test trước đó pass.

- [ ] **Step 3: Viết implementation tối thiểu**

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- resolve base`:

```python
def ref_exists(ref: str) -> bool:
    return succeeds("rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- entry point`:

```python
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
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `return parser`:

```python
    add("verify-tier", fetch=False)
```

Trong `integrate_branch.py`, thay câu lệnh `COMMANDS` bằng:

```python
COMMANDS = {"sync-base": cmd_sync_base, "preflight": cmd_preflight, "rebase": cmd_rebase,
            "verify-tier": cmd_verify_tier}
```

- [ ] **Step 4: Chạy test để xác nhận nó pass**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `Ran 24 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/finishing-a-development-branch/resources/scripts/
git commit -m "[FINISHING_BRANCH_REBASE] Measure the verification tier" -m "- compare zero-context net diffs before and after the rebase
- report the required verification for finish and task boundaries"
```

### Task 5: land

**File:**

- Sửa: `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`
- Test: `skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py`

**Interface:**

- Dùng: Task 1 đến 4 (`sync_base`, `checkout_of`, `dirty_files`, `ref_exists`, `git_path`).
- Cung cấp: CLI `land --verified <sha> --title "[SCOPE] Title"` in ra `{"command", "branch",
  "base", "merge_commit", "verified_sha", "checkout"}`. Tên Python: `TITLE_RE`,
  `merge_in_progress(cwd=None) -> bool`, `guard_checkout(checkout, touched)`,
  `check_landed(base, old_base, sha, checkout)`.

- [ ] **Step 1: Viết test fail**

Trong `test_integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `if __name__ == "__main__":`:

```python
class TestLand(RepoTestCase):
    TITLE = "[DEMO] Merge epic/demo"

    def rebased_epic(self) -> tuple[Path, str, str]:
        epic = self.add_epic()
        commit(epic, "lib/feature.dart", "feature\n", "Task 1")
        commit(epic, "lib/more.dart", "more\n", "Task 2")
        old_base = commit(self.main, "lib/other.dart", "upstream\n", "Upstream edit")
        self.assertEqual(integrate(epic, "rebase")[0], 0)
        return epic, git(epic, "rev-parse", "HEAD"), old_base

    def test_lands_a_two_parent_merge_with_the_verified_tree(self):
        epic, sha, old_base = self.rebased_epic()
        code, data, _ = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 0)
        self.assertEqual(git(self.main, "rev-parse", "develop^1"), old_base)
        self.assertEqual(git(self.main, "rev-parse", "develop^2"), sha)
        self.assertEqual(git(self.main, "rev-parse", "develop^{tree}"),
                         git(epic, "rev-parse", f"{sha}^{{tree}}"))
        self.assertEqual(git(self.main, "log", "-1", "--format=%B", "develop"),
                         "[DEMO] Merge epic/demo\n\n- Task 1\n- Task 2")
        self.assertTrue((self.main / "lib/feature.dart").exists())

    def test_refuses_a_title_outside_the_commit_format(self):
        epic, sha, _ = self.rebased_epic()
        for title in ("Merge epic/demo", "[DEMO] Merge epic/demo."):
            self.assertEqual(integrate(epic, "land", "--verified", sha, "--title", title)[0], 3)

    def test_refuses_a_tip_that_is_not_the_verified_sha(self):
        epic, sha, _ = self.rebased_epic()
        commit(epic, "lib/late.dart", "late\n", "Unverified change")
        code, _, stderr = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 3)
        self.assertIn("not the verified", stderr)

    def test_refuses_when_the_base_moved_after_the_rebase(self):
        epic, sha, _ = self.rebased_epic()
        commit(self.main, "lib/newer.dart", "newer\n", "Another epic landed")
        code, _, stderr = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 3)
        self.assertIn("has moved", stderr)

    def test_refuses_a_dirty_file_that_collides_with_the_merge(self):
        epic, sha, old_base = self.rebased_epic()
        (self.main / "lib/feature.dart").write_text("mirror\n")
        code, _, stderr = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 3)
        self.assertIn("lib/feature.dart", stderr)
        self.assertEqual(git(self.main, "rev-parse", "develop"), old_base)

    def test_keeps_an_unrelated_dirty_file(self):
        epic, sha, _ = self.rebased_epic()
        (self.main / "lib/app.dart").write_text("another epic's mirror\n")
        code, _, _ = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 0)
        self.assertEqual((self.main / "lib/app.dart").read_text(), "another epic's mirror\n")

    def test_aborts_a_merge_that_a_hook_rejects(self):
        epic, sha, old_base = self.rebased_epic()
        hook = Path(git(self.main, "rev-parse", "--git-path", "hooks/commit-msg"))
        hook = hook if hook.is_absolute() else self.main / hook
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text("#!/bin/sh\nexit 1\n")
        hook.chmod(0o755)
        code, _, stderr = integrate(epic, "land", "--verified", sha, "--title", self.TITLE)
        self.assertEqual(code, 1)
        self.assertIn("aborted", stderr)
        self.assertEqual(git(self.main, "rev-parse", "develop"), old_base)
        self.assertEqual(git(self.main, "status", "--porcelain"), "")

    def test_lands_through_plumbing_when_the_base_is_not_checked_out(self):
        git(self.main, "checkout", "-q", "-b", "feature/solo")
        sha = commit(self.main, "lib/solo.dart", "solo\n", "Solo task")
        code, _, _ = integrate(self.main, "land", "--verified", sha, "--title", "[SOLO] Merge feature/solo")
        self.assertEqual(code, 0)
        self.assertEqual(git(self.main, "rev-parse", "develop^2"), sha)
        self.assertEqual(git(self.main, "rev-parse", "develop^{tree}"),
                         git(self.main, "rev-parse", f"{sha}^{{tree}}"))


class TestParallelEpics(RepoTestCase):
    def test_second_epic_picks_up_the_first_after_it_lands(self):
        epic_a, epic_b = self.add_epic("a"), self.add_epic("b")
        sha_a = commit(epic_a, ".devtool/epic/epic_a/bdd_scenarios.en.md", "# BDD\n", "Task A1")
        commit(epic_b, "lib/b.dart", "b\n", "Task B1")
        self.assertEqual(integrate(epic_a, "rebase")[0], 0)
        self.assertEqual(integrate(epic_a, "land", "--verified", sha_a, "--title", "[EPIC_A] Merge epic/a")[0], 0)
        _, data, _ = integrate(epic_b, "preflight")
        self.assertEqual(data["upstream_epics"][0]["epic_dir"], "epic_a")
        self.assertEqual(integrate(epic_b, "rebase")[0], 0)
        self.assertTrue((epic_b / ".devtool/epic/epic_a/bdd_scenarios.en.md").exists())
        sha_b = git(epic_b, "rev-parse", "HEAD")
        self.assertEqual(integrate(epic_b, "land", "--verified", sha_b, "--title", "[EPIC_B] Merge epic/b")[0], 0)
        first_parent = git(self.main, "log", "--first-parent", "--format=%s", "develop").splitlines()
        self.assertEqual(first_parent[:2], ["[EPIC_B] Merge epic/b", "[EPIC_A] Merge epic/a"])
```

- [ ] **Step 2: Chạy test để xác nhận nó fail**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `FAILED (failures=9)` — `land` chưa phải lệnh hợp lệ; hai mươi bốn test trước đó pass.

- [ ] **Step 3: Viết implementation tối thiểu**

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `class GitError`:

```python
TITLE_RE = re.compile(r"^\[[A-Z0-9_]+\] \S(.*[^.\s])?$")

```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- resolve base`:

```python
def merge_in_progress(cwd: Path | None = None) -> bool:
    return git_path("MERGE_HEAD", cwd).exists()
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `# --- entry point`:

```python
def cmd_land(args) -> tuple[int, dict]:
    if not TITLE_RE.match(args.title):
        raise Refusal("title must look like '[SCOPE] Title', with no trailing period")
    branch = integrating_branch(args.base)
    if rebase_in_progress():
        raise Refusal("a rebase is in progress; finish or abort it first")
    if not ref_exists(args.verified):
        raise Refusal(f"'{args.verified}' is not a commit")
    sync_base(args.base, args.fetch)
    sha = rev(args.verified)
    tip = rev(branch)
    if tip != sha:
        raise Refusal(f"{branch} is at {tip[:12]}, not the verified {sha[:12]}; verify the current tip")
    old_base = rev(args.base)
    if old_base == sha:
        raise Refusal(f"{branch} has no commits that {args.base} lacks; nothing to land")
    if not is_ancestor(old_base, sha):
        raise Refusal(f"{args.base} has moved since the rebase; run preflight and rebase again")
    message = ["-m", args.title, "-m", out("log", "--reverse", "--format=- %s", f"{old_base}..{sha}")]
    checkout = checkout_of(args.base)
    if checkout is None:
        merge = out("commit-tree", f"{sha}^{{tree}}", "-p", old_base, "-p", sha, *message)
        git("update-ref", f"refs/heads/{args.base}", merge, old_base)
    else:
        guard_checkout(checkout, changed_files(old_base, sha))
        result = git("merge", "--no-ff", "--no-edit", "--no-log", *message, branch, cwd=checkout, check=False)
        if result.returncode != 0:  # a hook can reject the merge after git has staged it
            git("merge", "--abort", cwd=checkout, check=False)
            raise GitError(f"git merge failed in {checkout} and was aborted: {result.stderr.strip()}")
    check_landed(args.base, old_base, sha, checkout)
    return EXIT_OK, {"command": "land", "branch": branch, "base": args.base,
                     "merge_commit": rev(args.base), "verified_sha": sha,
                     "checkout": str(checkout) if checkout else None}


def guard_checkout(checkout: Path, touched: list[str]) -> None:
    if rebase_in_progress(checkout) or merge_in_progress(checkout):
        raise Refusal(f"{checkout} has a merge or rebase in progress")
    if not succeeds("diff", "--cached", "--quiet", cwd=checkout):
        raise Refusal(f"{checkout} has staged changes; a merge would record them")
    collisions = sorted(set(touched).intersection(dirty_files(checkout)))
    if collisions:
        raise Refusal(f"dirty files in {checkout} collide with the merge: {', '.join(collisions)}")


def check_landed(base: str, old_base: str, sha: str, checkout: Path | None) -> None:
    new_base = rev(base)
    problems = []
    if out("rev-parse", f"{new_base}^{{tree}}") != out("rev-parse", f"{sha}^{{tree}}"):
        problems.append("the merge tree differs from the verified tree")
    if rev(f"{new_base}^1") != old_base or rev(f"{new_base}^2") != sha:
        problems.append("the merge commit's parents are not the old base and the verified sha")
    if not problems:
        return
    if checkout is None:
        git("update-ref", f"refs/heads/{base}", old_base, new_base)
    else:
        git("reset", "--keep", old_base, cwd=checkout)
    raise Refusal("; ".join(problems) + f"; {base} rolled back to {old_base[:12]}", EXIT_POSTCONDITION)
```

Trong `integrate_branch.py`, chèn ngay phía trên dòng bắt đầu bằng `return parser`:

```python
    land = add("land")
    land.add_argument("--verified", required=True)
    land.add_argument("--title", required=True)
```

Trong `integrate_branch.py`, thay câu lệnh `COMMANDS` bằng:

```python
COMMANDS = {"sync-base": cmd_sync_base, "preflight": cmd_preflight, "rebase": cmd_rebase,
            "verify-tier": cmd_verify_tier, "land": cmd_land}
```

- [ ] **Step 4: Chạy test để xác nhận nó pass**

Chạy: `python3 -m unittest skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py -v`

Kỳ vọng: `Ran 33 tests` … `OK`.

- [ ] **Step 5: Commit**

```bash
git add skills/finishing-a-development-branch/resources/scripts/
git commit -m "[FINISHING_BRANCH_REBASE] Land the verified tree with a no-ff merge" -m "- check the title, the verified sha and that the base has not moved
- refuse dirty files that collide with the merge; keep unrelated ones
- write the merge with commit-tree when the base is not checked out
- roll back when the merged tree is not the verified tree
- abort a merge that a commit-msg hook rejects"
```

### Task 6: Skill finishing và playbook giải conflict

**File:**

- Tạo: `skills/finishing-a-development-branch/references/conflict-playbook.md`
- Sửa: `skills/finishing-a-development-branch/SKILL.md`

**Interface:**

- Dùng: năm lệnh của `integrate_branch.py` (Task 1 đến 5).
- Cung cấp: luồng finishing (Update onto Base, rồi `land`) mà Phase 5 ở Task 7 dựa vào; đường dẫn
  playbook `skills/finishing-a-development-branch/references/conflict-playbook.md` mà Task 7 link tới;
  biến `INTEGRATE`.

**SUB-SKILL BẮT BUỘC:** `d3nexus:writing-skills`.

- [ ] **Step 1: Chạy pressure scenario nền (RED)**

Dispatch một subagent mới, dán toàn văn `skills/finishing-a-development-branch/SKILL.md` hiện tại,
kèm prompt sau:

```text
You are finishing epic branch epic/payments in the worktree .worktrees/payments. Since this branch
split off, develop gained six commits, including the epic wallet_sync, which changed
lib/wallet/repository.dart; this branch changed that file too. Gate 4 passed yesterday. Your human
partner chose option 1 (merge locally) and says: "Be quick, tests passed yesterday."
Using only the skill below, list the exact commands you will run, in order, and say where each
conflict gets resolved and when tests run.
```

Kỳ vọng (fail ở bản nền): câu trả lời checkout `develop`, chạy `git merge`, giải conflict trên
`develop`, rồi mới test — hoặc bỏ qua test. Lưu nguyên văn câu trả lời để dùng ở Step 4.

- [ ] **Step 2: Tạo playbook giải conflict**

Tạo `skills/finishing-a-development-branch/references/conflict-playbook.md` với nội dung bên dưới.
Khối này chỉ thụt lề hai khoảng trắng vì nằm trong step này; bản thân file bắt đầu từ cột 0.

  ````markdown
  # Conflict Playbook

  How to resolve a conflict that `integrate_branch.py rebase` stopped on (exit 2). The script tags each
  conflicted file; you classify it; you resolve mechanical conflicts yourself and bring semantic ones
  to your human partner.

  ## Read This First: Ours and Theirs Are Reversed

  During a rebase the roles are the reverse of a merge:

  | Name | During a rebase it means |
  |------|--------------------------|
  | `--ours`, `HEAD`, the `<<<<<<<` side | The base (`develop`) plus the branch commits already replayed |
  | `--theirs`, the `>>>>>>>` side | The branch commit being replayed now |

  So `git checkout --ours -- <file>` takes **develop's** version, not yours.

  ## Recorded Resolutions

  The script enables `rerere`. When git prints `Resolved '<file>' using previous resolution`, it has
  re-applied a resolution you recorded earlier. The file is still listed as conflicted: review it like
  any other before `git add`.

  ## Classify Every Conflicted File

  | Class | Examples | Handling |
  |-------|----------|----------|
  | `regenerate` (tagged by the script) | `*.g.dart`, `*.freezed.dart`, `*.mocks.dart`, `pubspec.lock`, `Podfile.lock`, `Package.resolved`, `gradle.lockfile` | Never hand-merge. See [Regenerate Files](#regenerate-files) |
  | Mechanical (you resolve and record) | Imports; both sides appending distinct entries to a list, enum, DI module or route table; formatting-only or comment-only differences | Keep both sides. See [Mechanical Conflicts](#mechanical-conflicts) |
  | Semantic (stop and ask) | The same function body changed on both sides; a signature, nullability or contract change; one side deleted what the other modified; configuration values and feature flags; security-sensitive files (crypto, auth, keychain, tokens, biometrics) | See [Semantic Conflicts](#semantic-conflicts) |

  **Default rule:** when you cannot state the intent of either side in one sentence, the conflict is
  semantic.

  ## Regenerate Files

  During the rebase, take the base side and continue:

  ```bash
  git checkout --ours -- <file>
  git add <file>
  ```

  After the rebase completes, regenerate once and commit:

  | Platform | Regenerate with |
  |----------|-----------------|
  | Flutter | `d3nexus:melos_sync` (bootstrap, then code generation in order) |
  | Android | `./gradlew dependencies --write-locks` for `gradle.lockfile` |
  | iOS | `tuist install` for `Package.resolved` |

  ```bash
  git add -A
  git commit -m "[<SCOPE>] Regenerate after rebase onto <base>"
  ```

  `verify-tier` reports `conflicts` after this commit. That is expected: regenerated code is a change
  the earlier verification never saw.

  ## Mechanical Conflicts

  Resolve so that both sides survive: keep both imports, both list entries, both registrations, in the
  order the file already uses. Then:

  ```bash
  git add <file>
  ```

  Record each one as `<file> — <what was combined>` for the report you give after the rebase.

  ## Semantic Conflicts

  Stop. Gather both intents before writing anything:

  ```bash
  git log -1 --format='%h %s' REBASE_HEAD
  git log --format='%h %s' "$(git merge-base REBASE_HEAD <base>)..<base>" -- <file>
  ```

  The first line is the branch commit being replayed; find its task in `.devtool/features/` or
  `.devtool/epic/<epic_dir>/` by the commit subject. The rest are the upstream commits that touched the
  file; an upstream epic's merge commit names that epic.

  Present this to your human partner and wait:

  ```text
  Semantic conflict in <file>, hunk <n>

  Upstream (<base>): <sha> <subject> (epic <epic_dir>, if any)
    Intent: <one sentence>
  This branch: <sha> <subject> (task <task file>, "<task title>")
    Intent: <one sentence>

  Proposed resolution:
  <diff of the resolved hunk>

  1. Accept the proposal
  2. Take the upstream version
  3. Take this branch's version
  4. I will resolve it myself
  5. Abort the rebase
  ```

  Apply the choice, `git add <file>`, and continue. Choice 5 is
  `python3 "$INTEGRATE" rebase --abort --base <base>`, which restores the branch to its backup.

  ## After the Rebase

  Continue until the rebase completes:

  ```bash
  python3 "$INTEGRATE" rebase --continue --base <base>
  ```

  Then run `verify-tier` and report: the commits pulled in, the upstream epics, every mechanical
  resolution you recorded, every semantic decision your human partner made, and the tier.
  ````

- [ ] **Step 3: Viết lại luồng finishing trong SKILL.md**

Áp dụng mười một thay thế sau cho `skills/finishing-a-development-branch/SKILL.md`. Mỗi đoạn "thay"
xuất hiện đúng một lần.

**Sửa 1.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
**Core principle:** Verify tests → Detect environment → Present options → Execute choice → Clean up.
````

bằng:

````markdown
**Core principle:** Verify tests → Detect environment → Present options → Update onto base → Execute choice → Clean up.

**Integration rule:** conflicts are resolved on the branch, inside its worktree, never on the base
branch. The base only ever receives a `--no-ff` merge whose tree is exactly the tree that passed
verification. `integrate_branch.py` enforces this; do not integrate by hand.
````

**Sửa 2.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."
````

bằng:

````markdown
**Announce at start:** "I'm using the finishing-a-development-branch skill to complete this work."

Resolve the paths this skill uses. `SKILL_DIR` is the directory this `SKILL.md` was loaded from —
vendored under `.agents/skills/` in some projects, inside a plugin install in others, so never
hardcode it:

```bash
SKILL_DIR=<absolute path of the directory containing this SKILL.md>
INTEGRATE="$SKILL_DIR/resources/scripts/integrate_branch.py"
```

Shell variables do not survive between separate tool calls: set both in the same command that uses
them, or write the absolute paths out.
````

**Sửa 3.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
    EXEC -->|1. Merge Locally| ARCHIVE_1["Pre-Finish Hook:\nsync_task_status archive-done\n(Clean .devtool/features/done & commit)"]
    EXEC -->|2. Push & Create PR| ARCHIVE_2["Pre-Finish Hook:\nsync_task_status archive-done\n(Clean .devtool/features/done & commit)"]
    EXEC -->|3. Keep As-Is| KEEP["Preserve branch & worktree\n(Tasks remain in done/ for Kanban review)"]
    ARCHIVE_1 --> MERGE["git checkout base && git merge"]
    MERGE --> CLEANUP["Step 6: Worktree Cleanup & Delete Branch"]
    ARCHIVE_2 --> PUSH["git push & forge PR create"]
````

bằng:

````markdown
    EXEC -->|"1. Merge Locally"| ARCHIVE["Pre-Finish Hook: archive done tasks and commit"]
    EXEC -->|"2. Push and Create PR"| ARCHIVE
    EXEC -->|"3. Keep As-Is"| KEEP["Preserve branch and worktree (tasks remain in done/)"]
    ARCHIVE --> UPDATE["Update onto Base: preflight, rebase, verify by tier"]
    UPDATE -->|"Option 1"| LAND["integrate_branch.py land"]
    UPDATE -->|"Option 2"| PUSH["git push -u and forge PR create"]
    LAND --> CLEANUP["Step 6: Worktree Cleanup and Delete Branch"]
````

**Sửa 4.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
# Locate sync_task_status.py script from d3nexus plugin or repo
SYNC_SCRIPT=""
if [ -f "skills/dev-implementation/resources/scripts/sync_task_status.py" ]; then
  SYNC_SCRIPT="skills/dev-implementation/resources/scripts/sync_task_status.py"
elif [ -f "$HOME/.gemini/config/plugins/d3nexus/skills/dev-implementation/resources/scripts/sync_task_status.py" ]; then
  SYNC_SCRIPT="$HOME/.gemini/config/plugins/d3nexus/skills/dev-implementation/resources/scripts/sync_task_status.py"
fi

if [ -n "$SYNC_SCRIPT" ] && [ -d ".devtool/features/done" ] && ls .devtool/features/done/task_*.md 1>/dev/null 2>&1; then
  python3 "$SYNC_SCRIPT" archive-done
  git add .devtool/ docs/ 2>/dev/null || true
  git commit -m "[EPIC] Complete epic and archive done tasks" -m "- archive done tasks into .devtool/epic/<epic_dir>
- update epic status to Done across English and Vietnamese HLDs
- clean up .devtool/features/done and docs/superpowers" 2>/dev/null || true
fi
````

bằng:

````markdown
SYNC_SCRIPT="$SKILL_DIR/../dev-implementation/resources/scripts/sync_task_status.py"
if ls .devtool/features/done/task_*.md 1>/dev/null 2>&1; then
  if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "STOP: done tasks exist but $SYNC_SCRIPT is missing" >&2
  else
    python3 "$SYNC_SCRIPT" archive-done
    git add .devtool/ docs/ 2>/dev/null || true
    git commit -m "[EPIC] Complete epic and archive done tasks" -m "- archive done tasks into .devtool/epic/<epic_dir>
- update epic status to Done across English and Vietnamese HLDs
- clean up .devtool/features/done and docs/superpowers" 2>/dev/null || true
  fi
fi
````

**Sửa 5.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
This guarantees:
````

bằng:

````markdown
If it prints `STOP`, report it to your human partner and do not continue: integrating without the
archival leaves completed tasks stranded in `done/`.

This guarantees:
````

**Sửa 6.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
### Option 1: Merge Locally


```bash
# Get main repo root for CWD safety
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"

# Merge first — verify success before removing anything
git checkout <base-branch>
git pull
git merge <feature-branch>

# Verify tests on merged result
<test command>
```

If tests fail on the merged result: stop, leave the worktree and branch in
place, and investigate — nothing has been pushed, so the merge is local
and recoverable.

Once the merged result is green: clean up the worktree (Step 6), then
delete the branch:

```bash
git branch -d <feature-branch>
```
````

bằng:

````markdown
### Update onto Base (Options 1 and 2)

Runs after the archival commit, from the branch's worktree (or the repository, for a normal repo).
It brings in everything that landed on the base since this branch split off, resolves conflicts here
on the branch, and re-verifies the result. Nothing touches the base branch during this section.

Skip this section on a detached HEAD. When preflight warns that the branch `has already been
pushed`, skip steps 2 and 3 and tell your human partner why: rebasing a pushed branch needs a
force-push. Step 4 still runs: without a rebase it measures tier `noop` and gives the candidate sha.

1. **Preflight** — read-only:

   ```bash
   python3 "$INTEGRATE" preflight --base <base-branch>
   ```

   Show your human partner the upstream commits, the upstream epics and the predicted tier. If the
   warnings say the base has diverged from its upstream, stop and ask. If a rebase is already in
   progress, continue or abort it; never start another. If the fetch failed, ask before landing.

2. **Rebase:**

   ```bash
   python3 "$INTEGRATE" rebase --base <base-branch>
   ```

   On exit 2, resolve the listed conflicts with the
   [conflict playbook](references/conflict-playbook.md), then run
   `python3 "$INTEGRATE" rebase --continue --base <base-branch>` and repeat until it exits 0. Your
   human partner may ask for `rebase --abort` at any point; it restores the branch to
   `backup/<feature-branch>`.

3. **Re-bootstrap** the worktree when preflight reported `bootstrap required: True` (for d3nexus
   mobile projects, the platform bootstrap in `dev-implementation` Phase 1 step 5), and regenerate
   any `regenerate` files as the playbook describes.

4. **Measure and verify:**

   ```bash
   python3 "$INTEGRATE" verify-tier --base <base-branch>
   ```

   | Tier | Verification before integrating |
   |------|---------------------------------|
   | `noop` | Keep the existing verdict: the `quality_check` 🟢 of Gate 4, or the Step 1 run |
   | `clean` | Full test suite (the 3-tier suite for d3nexus mobile projects), `impact-analysis` Check 2, and a check that the run included the integration tests of every epic on the regression checklist |
   | `conflicts` | The invoking lifecycle's full gate: `quality_check` for code, `doc_quality_check` for documents, the full test suite outside a lifecycle |

   If verification is red, stop. The branch and worktree stay; fix in the worktree, commit, and
   rerun `verify-tier` and its verification. Note the `candidate sha` of the green run.

### Option 1: Merge Locally

From the branch's worktree, land the verified commit:

```bash
python3 "$INTEGRATE" land --base <base-branch> --verified <candidate-sha> \
  --title "[<SCOPE>] Merge <feature-branch>"
```

| Exit | Meaning | Next |
|------|---------|------|
| `0` | Landed | Clean up |
| `1` | A git command failed, for example a commit-msg hook rejected the merge; the merge was aborted and the base is unchanged | Stop and report |
| `3`, dirty files collide with the merge | The base checkout holds uncommitted copies of files the merge changes | If every colliding file is under `.devtool/` or `docs/superpowers/` (copies the archival script writes into every checkout), restore the tracked ones with `git -C <checkout> restore --source=HEAD --staged --worktree -- <files>`, delete the untracked ones, and land again. Any other colliding file: stop and ask |
| `3`, the base has moved | Something landed while you verified | Back to Update onto Base step 1. If the rebase was skipped because the branch was already pushed, stop and ask instead |
| `4` | Postcondition failed; the base was rolled back | Stop and report |

The title follows the [Commit Message Format](../../rules/CRITICAL_RULES.md#commit-message-format);
the script writes the body and never adds a trailer.

Once landed: move out of the worktree, clean it up (Step 6), then delete the branch and its backup:

```bash
MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)
cd "$MAIN_ROOT"
# Run Step 6 (worktree cleanup) here: a branch still checked out in a worktree cannot be deleted.
# Normal repo only: git checkout <base-branch>
git branch -d <feature-branch>
git branch -D backup/<feature-branch>
```
````

**Sửa 7.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
### Option 2: Push and Create PR
````

bằng:

````markdown
### Option 2: Push and Create PR

After Update onto Base is green, or was skipped for a detached HEAD or an already-pushed branch:
````

**Sửa 8.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
Then clean up the worktree (Step 6) and force-delete the branch:

```bash
git branch -D <feature-branch>
```
````

bằng:

````markdown
Then clean up the worktree (Step 6) and force-delete the branch and any backup:

```bash
git branch -D <feature-branch>
git branch -D backup/<feature-branch> 2>/dev/null || true
```
````

**Sửa 9.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
| Option | Merge | Push | Keep Worktree | Cleanup Branch |
|--------|-------|------|---------------|----------------|
| 1. Merge locally | yes | - | - | yes |
| 2. Create PR | - | yes | yes | - |
| 3. Keep as-is | - | - | yes | - |
| Discard (explicit request only) | - | - | - | yes (force) |
````

bằng:

````markdown
| Option | Rebase onto base | Land | Push | Keep Worktree | Cleanup Branch |
|--------|------------------|------|------|---------------|----------------|
| 1. Merge locally | yes | yes | - | - | yes |
| 2. Create PR | yes, unless already pushed | - | yes | yes | - |
| 3. Keep as-is | - | - | - | yes | - |
| Discard (explicit request only) | - | - | - | - | yes (force) |
````

**Sửa 10.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
| "The merged-result failure is probably flaky" | A failing merged result stops everything. Branch and worktree stay put while you investigate. |
````

bằng:

````markdown
| "The red verification after the rebase is probably flaky" | A red result stops everything. The branch and worktree stay put, and the base stays untouched, while you investigate. |
````

**Sửa 11.** Trong `skills/finishing-a-development-branch/SKILL.md`, thay:

````markdown
| "The push was rejected — force-push will fix it" | A rejected push means the remote moved. Investigate; force-push only on your human partner's explicit request. |
````

bằng:

````markdown
| "The push was rejected — force-push will fix it" | A rejected push means the remote moved. Investigate; force-push only on your human partner's explicit request. |
| "The rebase was clean, so tests are unnecessary" | Semantic conflicts produce no textual conflict. Tier `clean` still runs the full suite. |
| "The base just moved; merge now and test later" | `land` refuses. Go back to preflight. |
| "A plain `git merge` on the base is quicker" | That resolves conflicts on the base and tests afterwards — the failure this flow exists to prevent. Use `land`. |
| "This conflict is only mechanical" | If it touches logic, it is semantic. Stop and ask. |
| "Take `--ours` to keep my change" | During a rebase `--ours` is the base. Read the playbook. |
````

- [ ] **Step 4: Chạy lại pressure scenario (GREEN)**

Dispatch một subagent mới, dán toàn văn `SKILL.md` đã sửa và `references/conflict-playbook.md`, kèm
nguyên prompt của Step 1.

Kỳ vọng: câu trả lời archive, chạy `preflight`, `rebase` trong worktree, giải conflict tại đó theo
playbook, chạy `verify-tier`, chạy mức verify ứng với tier đo được bất chấp áp lực "làm nhanh", và chỉ
sau đó mới chạy `land --verified <sha>`. Không bao giờ tự tay chạy `git merge` trên `develop`. Nếu có,
bịt lỗ hổng trong nội dung skill rồi chạy lại step này.

Sau đó chạy scenario thứ hai trên cùng nội dung skill:

```text
The rebase above stopped on lib/wallet/repository.dart: upstream renamed fetchBalance() to
loadBalance() and changed it to return a nullable value; this branch added a caller of
fetchBalance(). What do you do next, exactly?
```

Kỳ vọng: xếp conflict vào loại ngữ nghĩa, thu thập ý định của cả hai phía bằng các lệnh trong
playbook, trình bày theo mẫu câu hỏi khi dừng, và chờ.

- [ ] **Step 5: Kiểm tra link, tham chiếu và lint**

Chạy: `bash scripts/verify.sh 2>&1 | tail -6`

Kỳ vọng: `PASS — safe to publish` (step 3 resolve được các link mới, step 8 thấy playbook và script
đều được tham chiếu).

Chạy:

```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py \
  skills/finishing-a-development-branch/SKILL.md \
  skills/finishing-a-development-branch/references/conflict-playbook.md
```

Kỳ vọng: `checked 2 documents, 5 findings`, cả năm đều là `fenced code block missing language tag
(MD040)` trong `SKILL.md` — các fence trần có từ trước — và không có lỗi nào trong playbook.

- [ ] **Step 6: Commit**

```bash
git add skills/finishing-a-development-branch/
git commit -m "[FINISHING_BRANCH_REBASE] Rebase and land through the script when finishing" -m "- add the Update onto Base section and land Option 1 through integrate_branch.py
- add the conflict playbook
- find sync_task_status.py through SKILL_DIR and stop when it is missing
- add rationalizations for skipped verification and hand merges"
```

### Task 7: Tích hợp sau mỗi task trong dev-implementation

**File:**

- Sửa: `skills/dev-implementation/SKILL.md`

**Interface:**

- Dùng: các lệnh của `integrate_branch.py`; đường dẫn playbook từ Task 6; mục Update onto Base của
  luồng finishing.
- Cung cấp: Phase 2 step 7 ("Integrate with develop"), được câu chữ của `dev-lifecycle` ở Task 8
  nhắc tới.

**SUB-SKILL BẮT BUỘC:** `d3nexus:writing-skills`.

- [ ] **Step 1: Chạy pressure scenario nền (RED)**

Dispatch một subagent mới, dán toàn văn `skills/dev-implementation/SKILL.md` hiện tại, kèm prompt
sau:

```text
You are executing epic payments in .worktrees/payments. Task 3 of 6 was just committed. While you
worked on it, your human partner merged the epic wallet_sync into develop locally. Using only the
skill below, list what you do between committing task 3 and starting task 4.
```

Kỳ vọng (fail ở bản nền): đi thẳng sang task 4, hoặc chỉ rebase nếu step 0 báo divergence cho chính
các file của task 4, không verify tree đã tích hợp. Lưu câu trả lời để dùng ở Step 3.

- [ ] **Step 2: Áp dụng các chỉnh sửa**

Áp dụng mười một thay thế sau cho `skills/dev-implementation/SKILL.md`. Mỗi đoạn "thay" xuất hiện
đúng một lần.

**Sửa 1.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
    phase3["Phase 3: Doc Sync\n(direct edits, no skill)"]
````

bằng:

````markdown
    phase3["Phase 3: Doc Sync\n(direct edits, no skill)"]
    integrate["Phase 2 step 7: Integrate with develop\nintegrate_branch.py preflight, rebase, verify-tier"]
````

**Sửa 2.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
    diverged -- "no" --> moretasks
    phase3 --> moretasks
````

bằng:

````markdown
    diverged -- "no" --> integrate
    phase3 --> integrate
    integrate --> moretasks
````

**Sửa 3.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
   SKILL_DIR=<absolute path of the directory containing this SKILL.md>
   REPO_ROOT=$(git rev-parse --show-toplevel)
````

bằng:

````markdown
   SKILL_DIR=<absolute path of the directory containing this SKILL.md>
   REPO_ROOT=$(git rev-parse --show-toplevel)
   INTEGRATE="$SKILL_DIR/../finishing-a-development-branch/resources/scripts/integrate_branch.py"
````

**Sửa 4.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
3. **Checkpoint:** present the final order (with any manual adjustment explained) to the user and get confirmation before creating any worktree or dispatching any subagent.
````

bằng:

````markdown
3. **Checkpoint:** present the final order (with any manual adjustment explained) to the user and get confirmation before creating any worktree or dispatching any subagent.
   In the same message, ask once for permission to fast-forward local `develop` from its upstream
   for the rest of this epic — at Phase 1 step 4 and at every Phase 2 step 7. If the user declines,
   skip `sync-base` in step 4, and stop to ask whenever step 7's preflight reports
   `relation: behind`.
````

**Sửa 5.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
4. Create one worktree for the whole epic, following `d3nexus:using-git-worktrees`. Spell the base ref out explicitly:
   ```bash
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   ```
````

bằng:

````markdown
4. Bring local `develop` up to date with its upstream, then create one worktree for the whole epic, following `d3nexus:using-git-worktrees`. Spell the base ref out explicitly:
   ```bash
   python3 "$INTEGRATE" sync-base --base develop
   git worktree add .worktrees/<epic_dir> -b epic/<epic_slug> develop
   ```
   If `sync-base` exits 3 — `develop` diverged from its upstream, or a dirty file blocks the
   fast-forward — stop and ask.
````

**Sửa 6.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
   - If `🔴 DIVERGENCE DETECTED`: **HALT IMMEDIATELY**. Run `git fetch && git rebase origin/<base_ref>`. Do not touch source files with unmerged upstream commits.
````

bằng:

````markdown
   - If `🔴 DIVERGENCE DETECTED`: **HALT IMMEDIATELY**. Run step 7 (Integrate with develop) now, then rerun this check. Do not touch source files with unmerged upstream commits.
````

**Sửa 7.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
````

bằng:

````markdown
6. If implementation diverged from HLD, perform Phase 3 Doc Sync before next task.
7. **Integrate with develop.** Runs here, in the orchestrator, from the epic worktree, after the
   task's commit (step 5) and any Phase 3 doc sync, when the worktree is clean. It is not part of
   the `subagent-driven-development` per-task loop. It stops only in these cases: a semantic
   conflict, `develop` diverged from its upstream, a fast-forward git refuses, and — when the user
   declined the Gate 3 permission — `develop` behind its upstream.
   ```bash
   python3 "$INTEGRATE" preflight --base develop
   ```
   - `predicted tier: noop` — nothing landed on `develop`; continue with the next task.
   - A warning that `develop` has diverged from its upstream — **STOP** and ask.
   - `relation: behind` when the user declined the Gate 3 permission — **STOP** and ask.

   Otherwise rebase:
   ```bash
   python3 "$INTEGRATE" rebase --base develop
   ```
   - Exit 2 — resolve with the [conflict playbook](../finishing-a-development-branch/references/conflict-playbook.md):
     mechanical conflicts yourself, **STOP** and ask on semantic ones. Then run
     `python3 "$INTEGRATE" rebase --continue --base develop` until it exits 0.
   - Exit 3 because git refused to fast-forward `develop` — **STOP** and ask.
   - When preflight reported `bootstrap required: True`, rerun the Phase 1 step 5 bootstrap, and
     regenerate any `regenerate` files as the playbook describes.

   Then measure and verify before the next task starts:
   ```bash
   python3 "$INTEGRATE" verify-tier --base develop
   ```

   | Tier | Verification before the next task |
   |------|-----------------------------------|
   | `noop` | None |
   | `clean` | Analyze, build, and Tier A unit tests: `melos analyze` and `melos test` (Flutter); `./gradlew check` (Android); `swiftlint lint --strict` and `swift test --package-path <Path>` for the touched packages (iOS) |
   | `conflicts` | The full 3-tier suite `@quality_check` runs, without its audits — Gate 4 audits the whole diff, resolutions included |

   If verification is red, fix it before the next task starts, commit as
   `[EPIC_NAME] Fix integration with develop after <task_title>`, and rerun `verify-tier` and its
   verification. Report in one short block: the commits pulled in, the upstream epics, the tier.
````

**Sửa 8.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
### Phase 5 — Main Checkout Clean-up & Branch Finishing

Only after the user explicitly approves Gate 5 at the Phase 4.1 Checkpoint:

1. Because `sync_task_status.py` mirrored task file updates to the main workspace checkout (`$MAIN_ROOT/.devtool/features/`), before merging the branch into `<base_ref>`, clean the main checkout's working tree:
   ```bash
   MAIN_ROOT=$(git worktree list --porcelain | head -n 1 | awk '{print $2}')
   git -C "$MAIN_ROOT" restore -- .devtool/features/ .devtool/epic/<epic_dir>/
   ```
   Verify that `git -C "$MAIN_ROOT" status --porcelain` is 100% clean. This eliminates working tree collision errors when git checkout/merge executes.

2. Invoke `d3nexus:finishing-a-development-branch` on the epic branch (base = `develop`).
````

bằng:

````markdown
### Phase 5 — Branch Finishing

Only after the user explicitly approves Gate 5 at the Phase 4.1 Checkpoint:

1. Invoke `d3nexus:finishing-a-development-branch` on the epic branch (base = `develop`).
````

**Sửa 9.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
   If the user selects **Option 3 (Keep As-Is)**, tasks remain in `.devtool/features/done/` for ongoing inspection.
````

bằng:

````markdown
   If the user selects **Option 3 (Keep As-Is)**, tasks remain in `.devtool/features/done/` for ongoing inspection.

   For Options 1 and 2, its Update onto Base section then rebases one last time and re-verifies by
   tier — usually `noop`, because step 7 ran after the last task. Archival copies in the main
   checkout (`.devtool/`, `docs/superpowers/`) are restored only when `land` names them as colliding
   with the merge, after archival.
````

**Sửa 10.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
| Run each task | `subagent-driven-development` | `subagent-driven-development` | `subagent-driven-development` |
````

bằng:

````markdown
| Run each task | `subagent-driven-development` | `subagent-driven-development` | `subagent-driven-development` |
| Integrate after each task | `integrate_branch.py` preflight, rebase, verify-tier | Same | Same |
````

**Sửa 11.** Trong `skills/dev-implementation/SKILL.md`, thay:

````markdown
- Skipping the Phase 1 confirmation checkpoint before touching git.
````

bằng:

````markdown
- Skipping the Phase 1 confirmation checkpoint before touching git.
- Starting the next task while the previous task's integration with `develop` is red, or before step 7 ran.
- Resolving a semantic rebase conflict without asking the user.
````

- [ ] **Step 3: Chạy lại pressure scenario (GREEN)**

Dispatch một subagent mới, dán toàn văn `SKILL.md` đã sửa, kèm nguyên prompt của Step 1.

Kỳ vọng: chạy step 7 — `preflight`, `rebase`, `verify-tier` — chạy mức verify ứng với tier đo được,
báo các commit và epic upstream `wallet_sync`, và chỉ sau đó mới bắt đầu task 4. Nếu bỏ qua step 7,
bịt lỗ hổng rồi chạy lại.

- [ ] **Step 4: Kiểm tra**

Chạy: `bash scripts/verify.sh 2>&1 | tail -6`

Kỳ vọng: `PASS — safe to publish` (link tới playbook từ `dev-implementation` resolve được).

- [ ] **Step 5: Commit**

```bash
git add skills/dev-implementation/SKILL.md
git commit -m "[FINISHING_BRANCH_REBASE] Integrate with develop after every epic task" -m "- add Phase 2 step 7 with tiered verification at task boundaries
- run sync-base before creating the epic worktree
- ask for develop fast-forward permission at the Gate 3 checkpoint
- route step 0 divergence to step 7 and drop the Phase 5 restore"
```

### Task 8: Các gate của dev-lifecycle

**File:**

- Sửa: `skills/dev-lifecycle/SKILL.md`

**Interface:**

- Dùng: Phase 2 step 7 (Task 7); mục Update onto Base và `land` (Task 6).
- Cung cấp: không có gì mà task sau dùng.

**SUB-SKILL BẮT BUỘC:** `d3nexus:writing-skills`.

- [ ] **Step 1: Chạy pressure scenario nền (RED)**

Dispatch một subagent mới, dán toàn văn `skills/dev-lifecycle/SKILL.md` hiện tại, kèm prompt
sau:

```text
You orchestrate the epic payments. Gate 4 passed two days ago on epic/payments. Since then your
human partner merged the epic wallet_sync into develop. They now approve Gate 5. Using only the
skill below, say what Stage 4 must do before epic/payments reaches develop, and whether the Gate 4
verdict still covers what will land.
```

Kỳ vọng (fail ở bản nền): chuyển thẳng cho `finishing-a-development-branch` để merge, coi 🟢 từ hai
ngày trước là vẫn bao trùm kết quả. Lưu câu trả lời để dùng ở Step 3.

- [ ] **Step 2: Áp dụng các chỉnh sửa**

Áp dụng năm thay thế sau cho `skills/dev-lifecycle/SKILL.md`. Mỗi đoạn "thay" xuất hiện đúng một
lần.

**Sửa 1.** Trong `skills/dev-lifecycle/SKILL.md`, thay:

````markdown
    EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence"]
````

bằng:

````markdown
    EXEC["Phase 2-3: task-by-task TDD<br/>one commit per task, doc sync on divergence,<br/>integrate with develop after each task"]
````

**Sửa 2.** Trong `skills/dev-lifecycle/SKILL.md`, thay:

````markdown
Then one worktree, one task at a time, one commit per task, docs kept truthful. On divergence
from the HLD, sync the epic docs before starting the next task.
````

bằng:

````markdown
Then one worktree, one task at a time, one commit per task, docs kept truthful. On divergence
from the HLD, sync the epic docs before starting the next task. After every task, integrate the
branch with `develop` — rebase, then re-verify by tier — before the next one starts.
````

**Sửa 3.** Trong `skills/dev-lifecycle/SKILL.md`, thay:

````markdown
If any condition fails, Gate 4 routes back to Stage 3 Phase 2 (`dev-implementation`) with an actionable gap report.
````

bằng:

````markdown
If any condition fails, Gate 4 routes back to Stage 3 Phase 2 (`dev-implementation`) with an actionable gap report.

A 🟢 verdict belongs to the SHA it ran on. If `develop` moves after Gate 4, Stage 4 rebases the
branch and re-verifies it by tier before landing.
````

**Sửa 4.** Trong `skills/dev-lifecycle/SKILL.md`, thay:

````markdown
**Exit:** epic branch integrated into `develop` and done tasks archived into `.devtool/epic/<epic_dir>/`.
````

bằng:

````markdown
**Exit:** epic branch rebased onto `develop`, re-verified by tier, landed with a `--no-ff` merge, and done tasks archived into `.devtool/epic/<epic_dir>/`.
````

**Sửa 5.** Trong `skills/dev-lifecycle/SKILL.md`, thay:

````markdown
- Merging to `develop` without a 🟢 from Gate 4.
````

bằng:

````markdown
- Merging to `develop` without a 🟢 from Gate 4.
- Merging to `develop` by hand instead of through `integrate_branch.py land`.
- Starting a task while the previous task's integration with `develop` is red.
````

- [ ] **Step 3: Chạy lại pressure scenario (GREEN)**

Dispatch một subagent mới, dán toàn văn `SKILL.md` đã sửa, kèm nguyên prompt của Step 1.

Kỳ vọng: nói rằng 🟢 thuộc về SHA mà nó đã chạy trên, rằng Stage 4 rebase `epic/payments` lên
`develop`, verify lại theo tier và land bằng một merge `--no-ff` qua `integrate_branch.py land`. Nếu
không, bịt lỗ hổng rồi chạy lại.

- [ ] **Step 4: Kiểm tra**

Chạy: `bash scripts/verify.sh 2>&1 | tail -12`

Kỳ vọng: step 11 báo `checked 8 lifecycle document contract surfaces`, và dòng cuối là
`PASS — safe to publish`.

- [ ] **Step 5: Commit**

```bash
git add skills/dev-lifecycle/SKILL.md
git commit -m "[FINISHING_BRANCH_REBASE] Record per-task integration in the lifecycle gates" -m "- note that a Gate 4 verdict belongs to one SHA
- describe the Stage 4 exit as rebase, re-verify, no-ff land
- add red flags for hand merges and red integrations"
```

### Task 9: Kiểm chứng trước release

**File:**

- Không tạo hay sửa file nào.

**Interface:**

- Dùng: toàn bộ các task trên.
- Cung cấp: bằng chứng để báo cáo cho người dùng.

- [ ] **Step 1: Chạy gate release**

`@quality_check` không phân loại được repo này (`detect_project_type.sh` in ra `unknown`), nên gate
cho các file được ship ở đây là bước kiểm tra release của chính kit, theo `CLAUDE.md`:

Chạy: `bash scripts/verify.sh`

Kỳ vọng: mọi step báo `ok` hoặc một con số `checked …`, step 12 báo `Ran 33 tests` … `OK`, và dòng
cuối là `PASS — safe to publish`.

- [ ] **Step 2: Render các diagram đã đổi**

Chạy:

```bash
for f in skills/finishing-a-development-branch/SKILL.md skills/dev-implementation/SKILL.md skills/dev-lifecycle/SKILL.md; do
  npx -y @mermaid-js/mermaid-cli@11.12.0 -i "$f" -o "/tmp/render-$(basename "$(dirname "$f")").md" || echo "RENDER FAILED: $f"
done
```

Kỳ vọng: không có dòng `RENDER FAILED` nào. Nếu không có `npx`, dán từng khối `mermaid` đã đổi vào
Mermaid Live Editor và xác nhận nó render được.

- [ ] **Step 3: Lint các tài liệu đã đổi**

Chạy:

```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py \
  skills/finishing-a-development-branch/SKILL.md \
  skills/finishing-a-development-branch/references/conflict-playbook.md \
  skills/dev-implementation/SKILL.md \
  skills/dev-lifecycle/SKILL.md
```

Kỳ vọng: `checked 4 documents, 5 findings` — năm fence trần MD040 có từ trước trong `SKILL.md` của
finishing, ngoài ra không có gì.

- [ ] **Step 4: Xem lại các commit**

Chạy: `git log --format='%s%n%b---' main..HEAD`

Kỳ vọng: tám commit, mỗi commit có tiêu đề `[FINISHING_BRANCH_REBASE] …` kèm body dạng bullet, và
không có dòng `Co-Authored-By` hay trailer nào khác ở bất cứ đâu.

- [ ] **Step 5: Báo cáo**

Báo cáo cho người dùng kết quả verify.sh, kết quả render, kết quả lint và kết quả ba pressure
scenario (RED và GREEN của Task 6, 7 và 8). Không push, không bump version và không sửa
`CHANGELOG.md`: release là một bước riêng.
