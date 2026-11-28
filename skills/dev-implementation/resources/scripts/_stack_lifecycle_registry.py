#!/usr/bin/env python3
"""Declarative 6-stack lifecycle registry and four Open-Closed contracts.

Implements:
- TierBContractAdapter: polyglot Tier B static gate resolution and validation
- PoolWorkspaceStrategy: symlink vs APFS/copytree cow_copy slot mount management
- TriageSurfaceRegistry: suffix-scoped Tier 1 risk triage and polyglot test detection
- TierCTaxonomy: explicit Tier C2 Needs enforcement, heuristic warnings, and HLD root checks

Python 3 standard library only; zero imports from check_task_contract.py or
manage_worker_pool.py to prevent circular imports.
"""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Literal

TIER1_TRIGGER_ORDER: tuple[str, ...] = (
    "NON_TEST_DIFF_OVER_30_LINES",
    "PUBLIC_SIGNATURE_CHANGED",
    "API_ROUTE_OR_SCHEMA_CHANGED",
    "DB_OR_PERSISTENCE_CHANGED",
    "CONCURRENCY_OR_LOCKING_CHANGED",
    "TEST_ASSERTION_WEAKENED",
)

SURFACE_CATEGORIES: tuple[str, ...] = (
    "signature",
    "api_wire",
    "persistence",
    "concurrency",
    "test_weakening",
)

DEFAULT_SYMLINK_MOUNTS: tuple[str, ...] = (
    "target",
    "node_modules",
    ".astro",
    ".venv",
    ".gradle",
    ".build",
    "Pods",
)

DEFAULT_COW_COPY_MOUNTS: tuple[str, ...] = (
    ".dart_tool",
    "packages/*/.dart_tool",
    "features/*/.dart_tool",
    "bricks/*/hooks/.dart_tool",
    "secureFiles",
    "local.properties",
    "android/local.properties",
    "*.xcconfig",
    "ios/Flutter/*.xcconfig",
    "macos/Flutter/*.xcconfig",
)

EXPLICIT_TIER_C2_RE: re.Pattern[str] = re.compile(r"#\s*tier:\s*C2\b", re.IGNORECASE)

_GLOB_CHARS_RE = re.compile(r"[*?\[\]]")
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_ANNOTATION_TRAIL_RE = re.compile(
    r"\s*(?:\(new\)|\(existing\)|\(L\d+(?:\s*[-–:]\s*L?\d+)?\)|::\s*`?[A-Za-z_][\w.]*`?|[—–-]\s+.*)$"
)
_SEQUENTIAL_CHAIN_TOKENS = frozenset({"&&", ";"})
_CONDITIONAL_OR_PIPE_TOKENS = frozenset({"||", "|"})
_VALUE_TAKING_FORMAT_FLAGS = frozenset(
    {
        "-o",
        "--output",
        "-l",
        "--line-length",
        "--indent",
        "--language-version",
        "--summary",
        "-c",
        "--config",
        "-p",
        "--project",
    }
)
_FULL_REPO_TARGETS = frozenset({".", "src", "tests"})
_MONOREPO_DIR_FLAGS = frozenset({"--directory", "--project", "--prefix"})
_VALUE_TAKING_PATH_FLAGS = frozenset(
    {
        "--target-dir",
        "--directory",
        "--project",
        "--prefix",
        "--root",
        "--dir",
        "--config",
        "--config-file",
        "-c",
        "-p",
        "-C",
        "--chdir",
        "--output",
        "-o",
        "--path",
    }
)
_VALUE_TAKING_CLI_FLAGS = _VALUE_TAKING_FORMAT_FLAGS | frozenset(
    {
        "--config-file",
        "--extend-select",
        "--select",
        "--ignore",
        "--extend-ignore",
        "--per-file-ignores",
        "--target-version",
        "--python-version",
        "--target-dir",
        "--directory",
        "--prefix",
        "--format",
        "--output-format",
        "--cache-dir",
        "--exclude",
        "--extend-exclude",
        "--reporter",
        "--filter",
    }
)
_TEST_DIR_MARKERS = frozenset(
    {
        "tests",
        "test",
        "__tests__",
        "integration_test",
        "androidTest",
        "UnitTests",
        "UITests",
    }
)
_BOUNDARY_KEYWORD_PREFIXES = frozenset(
    {
        "boundaries",
        "architecture",
        "xtask",
        "konsist",
        "bcv",
        "apicheck",
    }
)


@dataclass(frozen=True)
class TierBPolicy:
    """Static verification policy enforced on TIER-B rows for one stack."""

    format_prefixes: tuple[str, ...] = ()
    lint_prefixes: tuple[str, ...] = ()
    typecheck_prefixes: tuple[str, ...] = ()
    boundary_prefixes: tuple[str, ...] = ()
    boundary_triggers: tuple[str, ...] = ()
    require_all_allowed_files_in_format: bool = False
    require_clippy_deny_warnings: bool = False
    manifest_files: tuple[str, ...] = ()


@dataclass(frozen=True)
class SurfaceRuleSet:
    """Compiled regex rules for one stack or baseline risk triage category set."""

    signature: tuple[re.Pattern[str], ...] = ()
    api_wire: tuple[re.Pattern[str], ...] = ()
    persistence: tuple[re.Pattern[str], ...] = ()
    concurrency: tuple[re.Pattern[str], ...] = ()
    test_weakening: tuple[re.Pattern[str], ...] = ()
    test_assertion: tuple[re.Pattern[str], ...] = ()


@dataclass(frozen=True)
class TierCPolicy:
    """Tier C1 subcutaneous examples and Tier C2 heavy-runtime command patterns."""

    tier_c1_examples: tuple[str, ...] = ()
    tier_c2_command_patterns: tuple[re.Pattern[str], ...] = ()
    default_needs_hint: str = ""


@dataclass(frozen=True)
class PoolMountRule:
    """Declarative cache or gitignored config mount rule for worker pool slots."""

    path: str
    mode: Literal["symlink", "cow_copy"]
    optional: bool = True


@dataclass(frozen=True)
class TestRoutingPolicy:
    """Optional manifest-driven test routing and cache-busting policy for one stack."""

    canonical_test_globs: tuple[str, ...] = ()
    forbidden_test_globs: tuple[str, ...] = ()
    paired_source_globs: tuple[str, ...] = ()
    lcov_unit_test_globs: tuple[str, ...] = ()
    cache_bust_extensions: tuple[str, ...] = ()


@dataclass(frozen=True)
class StackDescriptor:
    """Immutable lifecycle descriptor for a built-in or custom stack family."""

    stack_id: str
    extensions: tuple[str, ...]
    test_path_patterns: tuple[str, ...]
    default_tier_b: TierBPolicy
    default_surfaces: SurfaceRuleSet
    tier_c_policy: TierCPolicy
    test_routing: TestRoutingPolicy = TestRoutingPolicy()


BASELINE_SURFACES: SurfaceRuleSet = SurfaceRuleSet(
    signature=(
        re.compile(
            r"^\s*(?:abstract\s+|final\s+|sealed\s+|open\s+|data\s+)?class\s+[A-Za-z]"
        ),
    ),
    api_wire=(),
    persistence=(
        re.compile(
            r"\b(?:SELECT|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM"
            r"|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE)\b"
        ),
    ),
    concurrency=(re.compile(r"\b(?:Lock|RLock|Semaphore|Condition|Event)\s*\("),),
    test_weakening=(),
    test_assertion=(
        re.compile(r"(?:\bassert\b|\bself\.assert|\bpytest\.raises|\bexpect\()"),
    ),
)


BUILTIN_STACKS: dict[str, StackDescriptor] = {
    "python": StackDescriptor(
        stack_id="python",
        extensions=(".py",),
        test_path_patterns=("tests/**", "test_*.py", "*_test.py"),
        default_tier_b=TierBPolicy(
            format_prefixes=("ruff format --check",),
            lint_prefixes=("ruff check",),
            typecheck_prefixes=("mypy", "pyright", "ty"),
            boundary_prefixes=("lint-imports", "architecture"),
            boundary_triggers=("pyproject.toml",),
            require_all_allowed_files_in_format=True,
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(
                re.compile(r"^\s*(?:async\s+)?def\s+[A-Za-z][A-Za-z0-9_]*\s*\("),
                re.compile(r"^\s*class\s+[A-Za-z]"),
            ),
            api_wire=(
                re.compile(
                    r"@(?:router|app)\.(?:get|post|put|patch|delete|websocket)\b"
                ),
                re.compile(
                    r"\b(?:FastAPI|APIRouter|BaseModel|TypedDict|openapi|json_schema)\b"
                ),
            ),
            persistence=(
                re.compile(
                    r"\b(?:SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|CREATE\s+TABLE|ALTER\s+TABLE)\b"
                ),
                re.compile(r"\bsession\.(?:execute|commit|rollback|query)\b"),
                re.compile(r"\b(?:alembic|migration|sqlite3|atomic_write)\b"),
            ),
            concurrency=(
                re.compile(r"\b(?:Lock|RLock|Semaphore|Condition|Event)\s*\("),
                re.compile(
                    r"\b(?:asyncio|threading|multiprocessing|concurrent\.futures)\."
                ),
                re.compile(r"\bfcntl\.flock\b"),
                re.compile(r"\bos\.(?:setpgrp|killpg)\b"),
                re.compile(r"\bcancel_event\b"),
            ),
            test_weakening=(
                re.compile(
                    r"(?:pytest\.mark\.(?:skip|xfail)|@unittest\.skip|\.skip\()"
                ),
            ),
            test_assertion=(
                re.compile(
                    r"(?:\bassert\b|\bself\.assert|\bpytest\.raises|\bexpect\()"
                ),
            ),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=(
                "python3 -m pytest -q --tb=short --maxfail=3 tests/integration/",
            ),
            tier_c2_command_patterns=(),
            default_needs_hint="DOCKER_LIVE",
        ),
    ),
    "flutter": StackDescriptor(
        stack_id="flutter",
        extensions=(".dart",),
        test_path_patterns=("test/**", "integration_test/**", "*_test.dart"),
        default_tier_b=TierBPolicy(
            format_prefixes=("dart format", "melos run format"),
            lint_prefixes=("dart analyze", "flutter analyze", "melos run analyze"),
            typecheck_prefixes=(),
            boundary_prefixes=(
                "boundaries",
                "architecture",
                "melos run boundaries",
                "melos run check:boundaries",
                "melos run architecture",
                "dart run import_lint",
            ),
            boundary_triggers=("domain/", "pubspec.yaml"),
            require_all_allowed_files_in_format=True,
            manifest_files=("pubspec.yaml",),
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(
                re.compile(r"MethodChannel|EventChannel|@HostApi|@FlutterApi|ffi\."),
            ),
            api_wire=(re.compile(r"@RestApi|@GET|@POST|fromJson"),),
            persistence=(re.compile(r"DriftDatabase|outbox_entries"),),
            concurrency=(re.compile(r"Isolate\.|Completer<"),),
            test_weakening=(re.compile(r"""skip:\s*(?:true|['"])"""),),
            test_assertion=(
                re.compile(
                    r"(?:\bexpect\s*\(|\bexpectLater\s*\(|\bverify\s*\(|\bassert\s*\()"
                ),
            ),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=("flutter test test/integration/*_integration_test.dart",),
            tier_c2_command_patterns=(
                re.compile(
                    r"""\bflutter\s+test\b.*(?:^|[\s/"'])integration_test(?:/|[\s"'&;]|$)""",
                    re.IGNORECASE,
                ),
            ),
            default_needs_hint="FLUTTER_DEVICE",
        ),
    ),
    "rust": StackDescriptor(
        stack_id="rust",
        extensions=(".rs",),
        test_path_patterns=("tests/**", "*_test.rs"),
        default_tier_b=TierBPolicy(
            format_prefixes=("cargo fmt --check",),
            lint_prefixes=("cargo clippy",),
            typecheck_prefixes=(),
            boundary_prefixes=(
                "cargo xtask",
                "xtask",
                "cargo deny",
                "architecture",
                "boundaries",
            ),
            boundary_triggers=("Cargo.toml", "domain/"),
            require_all_allowed_files_in_format=False,
            require_clippy_deny_warnings=True,
            manifest_files=("Cargo.toml",),
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(re.compile(r"pub\s+(?:async\s+)?(?:fn|struct|enum|trait)"),),
            api_wire=(re.compile(r'unsafe\b|extern\s+"C"'),),
            persistence=(re.compile(r"sqlx::query|SELECT|INSERT\s+INTO"),),
            concurrency=(re.compile(r"tokio::spawn|Mutex|RwLock"),),
            test_weakening=(re.compile(r"#\[ignore\b"),),
            test_assertion=(
                re.compile(r"(?:\bassert(?:_eq|_ne)?!|\bdebug_assert(?:_eq|_ne)?!)"),
            ),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=("cargo nextest run --test '*'", "cargo test --test '*'"),
            tier_c2_command_patterns=(),
            default_needs_hint="DOCKER_LIVE",
        ),
    ),
    "web": StackDescriptor(
        stack_id="web",
        extensions=(".ts", ".tsx", ".js", ".mjs", ".astro"),
        test_path_patterns=("__tests__/**", "*.test.*", "*.spec.*"),
        default_tier_b=TierBPolicy(
            format_prefixes=(),
            lint_prefixes=(
                "eslint",
                "biome",
                "npm run lint",
                "pnpm lint",
                "pnpm run lint",
                "yarn lint",
                "bun run lint",
                "check_vanilla_js.py",
            ),
            typecheck_prefixes=(
                "tsc --noEmit",
                "astro check",
                "npm run check",
                "npm run typecheck",
                "pnpm check",
                "pnpm run check",
                "pnpm typecheck",
                "yarn check",
                "yarn typecheck",
                "bun run check",
                "check_vanilla_js.py",
            ),
            boundary_prefixes=(),
            boundary_triggers=(),
            require_all_allowed_files_in_format=False,
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(
                re.compile(r"export\s+(?:async\s+)?(?:function|class|interface|type)"),
            ),
            api_wire=(re.compile(r"fetch\(|WebSocket|EventSource"),),
            persistence=(re.compile(r"indexedDB|localStorage"),),
            concurrency=(re.compile(r"Worker\(|SharedArrayBuffer"),),
            test_weakening=(re.compile(r"\.(?:skip|fixme)\("),),
            test_assertion=(re.compile(r"(?:\bexpect\s*\(|\bassert\b)"),),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=("npx --no-install vitest run",),
            tier_c2_command_patterns=(
                re.compile(r"\bplaywright\s+test\b", re.IGNORECASE),
            ),
            default_needs_hint="PLAYWRIGHT_BROWSER",
        ),
    ),
    "android": StackDescriptor(
        stack_id="android",
        extensions=(".kt", ".kts"),
        test_path_patterns=(
            "test/**",
            "androidTest/**",
            "*Test.kt",
            "*Tests.kt",
            "*Spec.kt",
        ),
        default_tier_b=TierBPolicy(
            format_prefixes=(
                "spotlessCheck",
                "./gradlew spotlessCheck",
                "gradle spotlessCheck",
            ),
            lint_prefixes=("detekt", "./gradlew detekt", "gradle detekt"),
            typecheck_prefixes=(),
            boundary_prefixes=(
                ":konsist-test:test",
                "konsist",
                "apiCheck",
                "architecture",
                "bcv",
            ),
            boundary_triggers=("domain/", ".api"),
            require_all_allowed_files_in_format=False,
            manifest_files=(".api",),
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(
                re.compile(
                    r"^\s*(?!private\b|protected\b)"
                    r"(?:(?:public|internal|override|open|final|inline|operator|infix|tailrec)\s+)*"
                    r"(?:suspend\s+)?fun\s+"
                    r"|^\s*(?!private\b|protected\b)"
                    r"(?:(?:public|internal|sealed|fun)\s+)*interface\s+"
                ),
            ),
            api_wire=(
                re.compile(r"@(?:GET|POST|PUT|DELETE|Entity|Dao)\b|MethodChannel"),
            ),
            persistence=(re.compile(r"RoomDatabase|SQLiteDatabase"),),
            concurrency=(re.compile(r"Mutex|CoroutineScope|Dispatchers\."),),
            test_weakening=(re.compile(r"@(?:Ignore|Disabled)\b"),),
            test_assertion=(
                re.compile(
                    r"(?:\bassertEquals\b|\bassertTrue\b|\bassertFalse\b|\bassertNull\b"
                    r"|\bassertNotNull\b|\bassertThrows\b|\bassertThat\b|\bassert\b|\bverify\s*\()"
                ),
            ),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=("./gradlew testDebugUnitTest",),
            tier_c2_command_patterns=(re.compile(r"\bconnected\w*AndroidTest\b"),),
            default_needs_hint="ANDROID_DEVICE",
        ),
    ),
    "ios": StackDescriptor(
        stack_id="ios",
        extensions=(".swift",),
        test_path_patterns=(
            "UnitTests/**",
            "UITests/**",
            "*Test.swift",
            "*Tests.swift",
        ),
        default_tier_b=TierBPolicy(
            format_prefixes=("swiftformat --lint",),
            lint_prefixes=("swiftlint lint --strict", "swiftlint --strict"),
            typecheck_prefixes=(),
            boundary_prefixes=(
                "ArchTests",
                "check_module_boundaries.sh",
                "architecture",
                "boundaries",
            ),
            boundary_triggers=("domain/", "Project.swift", "Package.swift"),
            require_all_allowed_files_in_format=False,
        ),
        default_surfaces=SurfaceRuleSet(
            signature=(
                re.compile(r"public\s+(?:func|struct|class|protocol|enum|actor)"),
            ),
            api_wire=(re.compile(r"Codable|URLSession|FlutterMethodChannel"),),
            persistence=(re.compile(r"@Model|NSManagedObject|sqlite3"),),
            concurrency=(re.compile(r"\bactor\s+|Task\.detached|NSLock"),),
            test_weakening=(re.compile(r"XCTSkip|@Test\([^)]*\.disabled"),),
            test_assertion=(
                re.compile(r"(?:\bXCTAssert\w*|#expect\s*\(|\bassert\s*\()"),
            ),
        ),
        tier_c_policy=TierCPolicy(
            tier_c1_examples=("swift test --filter FlowTests",),
            tier_c2_command_patterns=(re.compile(r"\bxcodebuild\b.*\btest\b"),),
            default_needs_hint="IOS_SIMULATOR",
        ),
    ),
}


def _split_sequential_subcommands(command: str) -> list[list[str]]:
    """Split a shell command into unconditionally sequenced subcommands (`&&` / `;`).

    Subcommands following `||` (failure-only fallback) or `|` (pipe consumer) are
    excluded until the next `&&` or `;` so conditional/piped tails cannot satisfy
    required static verification gates.
    """
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        tokens = command.split()

    subcommands: list[list[str]] = []
    current: list[str] = []
    skip_until_seq = False
    for token in tokens:
        if token in _SEQUENTIAL_CHAIN_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = False
        elif token in _CONDITIONAL_OR_PIPE_TOKENS:
            if current and not skip_until_seq:
                subcommands.append(current)
            current = []
            skip_until_seq = True
        elif not skip_until_seq:
            current.append(token)
    if current and not skip_until_seq:
        subcommands.append(current)
    return subcommands


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a POSIX-style glob supporting `*`, `**`, `?`, and `[...]`."""
    norm = pattern.replace("\\", "/").removeprefix("./")
    out: list[str] = ["^"]
    idx = 0
    length = len(norm)
    while idx < length:
        ch = norm[idx]
        if ch == "*":
            if idx + 1 < length and norm[idx + 1] == "*":
                if idx + 2 < length and norm[idx + 2] == "/":
                    out.append("(?:.*/)?")
                    idx += 3
                else:
                    out.append(".*")
                    idx += 2
            else:
                out.append("[^/]*")
                idx += 1
        elif ch == "?":
            out.append("[^/]")
            idx += 1
        elif ch == "[":
            end = norm.find("]", idx + 1)
            if end == -1:
                out.append(re.escape(ch))
                idx += 1
            else:
                body = norm[idx + 1 : end]
                if body.startswith("!"):
                    body = "^" + body[1:]
                out.append(f"[{body}]")
                idx = end + 1
        else:
            out.append(re.escape(ch))
            idx += 1
    out.append("$")
    return re.compile("".join(out))


def _glob_matches(pattern: str, path: str) -> bool:
    norm_path = path.replace("\\", "/").removeprefix("./")
    return bool(_glob_to_regex(pattern).match(norm_path))


def _target_covers_path(target_tok: str, file_path: str) -> bool:
    clean_tok = target_tok.split("::", 1)[0].strip().removeprefix("./").rstrip("/")
    clean_file = file_path.strip().removeprefix("./")
    if not clean_tok or clean_tok.startswith("-"):
        return False
    if clean_tok in (".", clean_file):
        return True
    if _GLOB_CHARS_RE.search(clean_tok) and _glob_matches(clean_tok, clean_file):
        return True
    return clean_file.startswith(clean_tok + "/")


def _strip_version_manager_wrappers(tokens: Sequence[str]) -> list[str]:
    """Strip leading env assignments, env invocations, and mise exec/x prefixes."""
    toks = list(tokens)
    while toks:
        head = toks[0]
        if _ENV_ASSIGN_RE.match(head):
            toks = toks[1:]
            continue
        base = Path(head).name
        if base == "env":
            idx = 1
            while idx < len(toks):
                tok = toks[idx]
                if tok in (
                    "-u",
                    "--unset",
                    "-C",
                    "--chdir",
                    "-S",
                    "--split-string",
                ) and idx + 1 < len(toks):
                    idx += 2
                elif tok.startswith("-") or _ENV_ASSIGN_RE.match(tok):
                    idx += 1
                else:
                    break
            toks = toks[idx:]
            continue
        if (
            base == "mise"
            and len(toks) >= 3
            and toks[1] in ("exec", "x")
            and "--" in toks[2:]
        ):
            dash_idx = toks.index("--", 2)
            toks = toks[dash_idx + 1 :]
            continue
        break
    return toks


def _normalize_dir_value(raw: str) -> str | None:
    cleaned = raw.strip().replace("\\", "/").removeprefix("./").rstrip("/")
    return cleaned or None


def _extract_monorepo_dir_wrapper(tokens: Sequence[str]) -> str | None:
    """Extract normalized --directory/--project/--prefix value from uv/npm wrappers."""
    toks = _strip_version_manager_wrappers(tokens)
    if not toks:
        return None
    base = Path(toks[0]).name
    if base == "uv":
        idx = 1
        seen_run = False
        while idx < len(toks):
            tok = toks[idx]
            if not seen_run and tok == "run":
                seen_run = True
                idx += 1
                continue
            if tok in ("--directory", "--project") and idx + 1 < len(toks):
                return _normalize_dir_value(toks[idx + 1])
            if tok.startswith(("--directory=", "--project=")):
                return _normalize_dir_value(tok.split("=", 1)[1])
            if tok == "--":
                break
            if tok.startswith("-"):
                if tok in (
                    "--extra",
                    "--group",
                    "--python",
                    "--with",
                    "--config-file",
                    "--cache-dir",
                    "-C",
                    "-p",
                    "--package",
                ) and idx + 1 < len(toks):
                    idx += 2
                else:
                    idx += 1
                continue
            break
        return None
    if base == "npm":
        idx = 1
        seen_sub = False
        while idx < len(toks):
            tok = toks[idx]
            if not seen_sub and tok in ("exec", "run"):
                seen_sub = True
                idx += 1
                continue
            if tok == "--prefix" and idx + 1 < len(toks):
                return _normalize_dir_value(toks[idx + 1])
            if tok.startswith("--prefix="):
                return _normalize_dir_value(tok.split("=", 1)[1])
            if tok == "--":
                break
            if tok.startswith("-"):
                if tok in ("-C", "--package", "-p") and idx + 1 < len(toks):
                    idx += 2
                else:
                    idx += 1
                continue
            break
    return None


def _strip_monorepo_dir_flags(tokens: Sequence[str]) -> list[str]:
    """Strip --directory/--project/--prefix flag pairs from leading uv/npm wrappers."""
    toks = list(tokens)
    if not toks:
        return toks
    base = Path(toks[0]).name
    if base not in ("uv", "npm"):
        return toks
    target_flags = ("--directory", "--project") if base == "uv" else ("--prefix",)
    result = [toks[0]]
    idx = 1
    seen_sub = False
    while idx < len(toks):
        tok = toks[idx]
        if not seen_sub and tok in ("run", "exec"):
            seen_sub = True
            result.append(tok)
            idx += 1
            continue
        if tok in target_flags and idx + 1 < len(toks):
            idx += 2
            continue
        if any(tok.startswith(f"{flag}=") for flag in target_flags):
            idx += 1
            continue
        if tok == "--" or (seen_sub and not tok.startswith("-")):
            result.extend(toks[idx:])
            break
        result.append(tok)
        idx += 1
    return result


def _strip_command_wrappers(tokens: Sequence[str]) -> list[str]:
    """Strip common shell/tool wrappers while keeping tool/runner subcommands intact."""
    toks = list(tokens)
    while toks:
        unwrapped_vm = _strip_version_manager_wrappers(toks)
        if unwrapped_vm != toks:
            toks = unwrapped_vm
            continue
        base = Path(toks[0]).name
        if base in ("fvm", "bunx"):
            toks = toks[1:]
            continue
        if base == "npx":
            idx = 1
            while idx < len(toks) and toks[idx] in (
                "--no-install",
                "-y",
                "--yes",
                "-q",
                "--quiet",
            ):
                idx += 1
            toks = toks[idx:]
            continue
        if base == "uv" and len(toks) >= 2:
            idx = 1
            while idx < len(toks) and toks[idx] != "run" and toks[idx].startswith("-"):
                tok = toks[idx]
                if tok in (
                    "--directory",
                    "--project",
                    "--python",
                    "--config-file",
                    "--cache-dir",
                    "-C",
                ) and idx + 1 < len(toks):
                    idx += 2
                elif tok.startswith(("--directory=", "--project=")) or tok in (
                    "-q",
                    "--quiet",
                    "--frozen",
                    "--offline",
                    "--no-sync",
                    "--locked",
                    "-v",
                    "--verbose",
                    "--no-config",
                    "--no-project",
                ):
                    idx += 1
                else:
                    break
            if idx < len(toks) and toks[idx] == "run":
                idx += 1
                while idx < len(toks) and toks[idx].startswith("-"):
                    if toks[idx] == "--":
                        idx += 1
                        break
                    if toks[idx] in (
                        "--extra",
                        "--group",
                        "--python",
                        "--with",
                        "--directory",
                        "--project",
                        "-p",
                        "--package",
                    ) and idx + 1 < len(toks):
                        idx += 2
                    else:
                        idx += 1
                toks = toks[idx:]
                continue
        if (
            base in ("poetry", "bundle")
            and len(toks) >= 2
            and toks[1] in ("run", "exec")
        ):
            toks = toks[2:]
            continue
        if base == "pnpm" and len(toks) >= 2 and toks[1] == "exec":
            toks = toks[2:]
            continue
        if base == "npm" and len(toks) >= 2:
            idx = 1
            while idx < len(toks) and toks[idx] != "exec" and toks[idx].startswith("-"):
                tok = toks[idx]
                if tok in ("--prefix", "-C") and idx + 1 < len(toks):
                    idx += 2
                elif tok.startswith("--prefix=") or tok in (
                    "-s",
                    "--silent",
                    "-q",
                    "--quiet",
                    "--no-audit",
                    "--no-fund",
                ):
                    idx += 1
                else:
                    break
            if idx < len(toks) and toks[idx] == "exec":
                idx += 1
                while idx < len(toks) and toks[idx].startswith("-"):
                    if toks[idx] == "--":
                        idx += 1
                        break
                    if toks[idx] in ("--prefix", "--package", "-p") and idx + 1 < len(
                        toks
                    ):
                        idx += 2
                    else:
                        idx += 1
                toks = toks[idx:]
                continue
        if base in ("python", "python3") and len(toks) >= 3 and toks[1] == "-m":
            toks = toks[2:]
            continue
        if (
            base == "melos"
            and len(toks) >= 3
            and toks[1] == "exec"
            and "--" in toks[2:]
        ):
            dash_idx = toks.index("--", 2)
            toks = toks[dash_idx + 1 :]
            continue
        break
    return toks


def _normalize_extensions(raw_exts: Any) -> tuple[str, ...]:
    if not isinstance(raw_exts, list):
        return ()
    result: list[str] = []
    for item in raw_exts:
        if not isinstance(item, str):
            continue
        cleaned = item.strip().lower()
        if not cleaned.startswith(".") or len(cleaned) < 2:
            continue
        if cleaned not in result:
            result.append(cleaned)
    return tuple(result)


def _normalize_allowed_entry(entry: Any) -> tuple[str, bool]:
    if isinstance(entry, str):
        is_new = "(new)" in entry
        cleaned = entry.strip().strip("`")
        cleaned = _ANNOTATION_TRAIL_RE.sub("", cleaned).strip().strip("`")
        return cleaned.replace("\\", "/").removeprefix("./"), is_new
    raw_pattern = str(getattr(entry, "pattern", "")).strip().strip("`")
    is_new = bool(getattr(entry, "new", False)) or "(new)" in raw_pattern
    cleaned = _ANNOTATION_TRAIL_RE.sub("", raw_pattern).strip().strip("`")
    return cleaned.replace("\\", "/").removeprefix("./"), is_new


def _is_safe_relative_path(
    raw_path: str, repo_root: Path, *, allow_symlink_leaf: bool = False
) -> bool:
    if not isinstance(raw_path, str):
        return False
    cleaned = raw_path.strip()
    if not cleaned or "\x00" in cleaned:
        return False
    if cleaned.startswith(("/", "\\", "~")):
        return False
    posix = cleaned.replace("\\", "/").rstrip("/")
    if not posix or posix == ".":
        return False
    parts = posix.split("/")
    if ":" in parts[0]:
        return False
    if any(part in ("..", "") for part in parts):
        return False
    static_parts: list[str] = []
    for part in parts:
        if _GLOB_CHARS_RE.search(part):
            break
        static_parts.append(part)
    root_resolved = repo_root.resolve()
    probe = root_resolved.joinpath(*static_parts) if static_parts else root_resolved
    target_to_check = (
        probe.parent
        if allow_symlink_leaf and static_parts and len(static_parts) == len(parts)
        else probe
    )
    try:
        return target_to_check.resolve(strict=False).is_relative_to(root_resolved)
    except OSError:
        return False


def _read_json_dict(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return None, f"malformed {path.name}: {exc}"
    if not isinstance(data, dict):
        return None, f"invalid {path.name}: root must be a JSON object"
    return data, None


def _string_list(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, list):
        return ()
    return tuple(item.strip() for item in raw if isinstance(item, str) and item.strip())


def _join_shell_tokens(tokens: Sequence[str]) -> str:
    parts: list[str] = []
    for tok in tokens:
        if "$D3NEXUS_KIT" in tok and not any(ch in tok for ch in ('"', "`", "\\")):
            parts.append(f'"{tok}"')
        else:
            parts.append(shlex.quote(tok))
    return " ".join(parts)


def _cap_command_str(capabilities: Mapping[str, Any], *keys: str) -> tuple[str, ...]:
    found: list[str] = []
    for key in keys:
        cmd = capabilities.get(key)
        if (
            isinstance(cmd, list)
            and cmd
            and all(isinstance(x, str) and x.strip() for x in cmd)
        ):
            normalized: list[str] = []
            raw_tokens = [x.strip() for x in cmd]
            idx = 0
            while idx < len(raw_tokens):
                tok = raw_tokens[idx]
                if (
                    tok == "--base-ref"
                    and idx + 1 < len(raw_tokens)
                    and raw_tokens[idx + 1] == "{base_ref}"
                ):
                    idx += 2
                    continue
                if tok == "--base-ref={base_ref}":
                    idx += 1
                    continue
                normalized.append(tok.replace("{skills_dir}", "$D3NEXUS_KIT/skills"))
                idx += 1
            while (
                len(normalized) > 1
                and normalized[-1] in _FULL_REPO_TARGETS
                and normalized[-2] not in _VALUE_TAKING_PATH_FLAGS
            ):
                normalized.pop()
            if not normalized:
                continue
            joined = _join_shell_tokens(normalized)
            if joined not in found:
                found.append(joined)
    return tuple(found)


def _merge_tier_b_policy(
    base: TierBPolicy,
    raw_override: Any,
    capabilities: Mapping[str, Any] | None,
) -> TierBPolicy:
    override: Mapping[str, Any] = (
        raw_override if isinstance(raw_override, Mapping) else {}
    )
    caps: Mapping[str, Any] = capabilities if isinstance(capabilities, Mapping) else {}

    def _resolve_prefixes(
        key: str,
        default_vals: tuple[str, ...],
        cap_keys: tuple[str, ...],
    ) -> tuple[str, ...]:
        if key in override and isinstance(override[key], list):
            return _string_list(override[key])
        merged = list(default_vals)
        for cap_cmd in _cap_command_str(caps, *cap_keys):
            if cap_cmd not in merged:
                merged.append(cap_cmd)
        return tuple(merged)

    format_prefixes = _resolve_prefixes(
        "format_prefixes", base.format_prefixes, ("format",)
    )
    lint_prefixes = _resolve_prefixes(
        "lint_prefixes", base.lint_prefixes, ("lint", "analyze", "clippy")
    )
    typecheck_prefixes = _resolve_prefixes(
        "typecheck_prefixes", base.typecheck_prefixes, ("type_check",)
    )
    boundary_prefixes = _resolve_prefixes(
        "boundary_prefixes",
        base.boundary_prefixes,
        ("boundaries", "architecture", "bcv"),
    )

    if "boundary_triggers" in override and isinstance(
        override["boundary_triggers"], list
    ):
        boundary_triggers = _string_list(override["boundary_triggers"])
    else:
        boundary_triggers = base.boundary_triggers

    if "require_all_allowed_files_in_format" in override and isinstance(
        override["require_all_allowed_files_in_format"], bool
    ):
        require_all_fmt = override["require_all_allowed_files_in_format"]
    else:
        require_all_fmt = base.require_all_allowed_files_in_format

    require_clippy_deny = (
        base.require_clippy_deny_warnings and "lint_prefixes" not in override
    )

    return TierBPolicy(
        format_prefixes=format_prefixes,
        lint_prefixes=lint_prefixes,
        typecheck_prefixes=typecheck_prefixes,
        boundary_prefixes=boundary_prefixes,
        boundary_triggers=boundary_triggers,
        require_all_allowed_files_in_format=require_all_fmt,
        require_clippy_deny_warnings=require_clippy_deny,
        manifest_files=base.manifest_files,
    )


def _merge_surface_ruleset(
    base: SurfaceRuleSet,
    raw_surfaces: Any,
    source_name: str,
) -> tuple[SurfaceRuleSet, list[str]]:
    errors: list[str] = []
    if raw_surfaces is None:
        return base, errors
    if not isinstance(raw_surfaces, dict):
        errors.append(
            f"{source_name}:triage_surfaces: must be a category-keyed JSON object, got {type(raw_surfaces).__name__}"
        )
        return base, errors

    compiled_extra: dict[str, list[re.Pattern[str]]] = {
        cat: [] for cat in SURFACE_CATEGORIES
    }
    for category, raw_patterns in raw_surfaces.items():
        if category not in SURFACE_CATEGORIES:
            errors.append(
                f"{source_name}:triage_surfaces: unknown category {category!r} "
                f"(expected one of {', '.join(SURFACE_CATEGORIES)})"
            )
            continue
        if not isinstance(raw_patterns, list):
            errors.append(
                f"{source_name}:triage_surfaces.{category}: expected list of regex patterns"
            )
            continue
        for pat in raw_patterns:
            if not isinstance(pat, str) or not pat:
                errors.append(
                    f"{source_name}:triage_surfaces.{category}: pattern must be a non-empty string"
                )
                continue
            try:
                compiled_extra[category].append(re.compile(pat))
            except re.error as exc:
                errors.append(
                    f"{source_name}:triage_surfaces.{category}: invalid regex {pat!r} ({exc})"
                )

    merged = SurfaceRuleSet(
        signature=base.signature + tuple(compiled_extra["signature"]),
        api_wire=base.api_wire + tuple(compiled_extra["api_wire"]),
        persistence=base.persistence + tuple(compiled_extra["persistence"]),
        concurrency=base.concurrency + tuple(compiled_extra["concurrency"]),
        test_weakening=base.test_weakening + tuple(compiled_extra["test_weakening"]),
        test_assertion=base.test_assertion,
    )
    return merged, errors


def _parse_test_routing_policy(
    raw_routing: Any, base: TestRoutingPolicy
) -> TestRoutingPolicy:
    if not isinstance(raw_routing, Mapping):
        return base
    return TestRoutingPolicy(
        canonical_test_globs=_string_list(raw_routing.get("canonical_test_globs")),
        forbidden_test_globs=_string_list(raw_routing.get("forbidden_test_globs")),
        paired_source_globs=_string_list(raw_routing.get("paired_source_globs")),
        lcov_unit_test_globs=_string_list(raw_routing.get("lcov_unit_test_globs")),
        cache_bust_extensions=_normalize_extensions(
            raw_routing.get("cache_bust_extensions")
        ),
    )


def _load_repo_manifests(
    repo_root: Path,
) -> tuple[dict[str, StackDescriptor], dict[str, Path], list[str]]:
    """Load built-in + custom stack descriptors from `.agents/quality/*-quality.json`."""
    descriptors: dict[str, StackDescriptor] = {}
    manifest_paths: dict[str, Path] = {}
    errors: list[str] = []

    quality_dir = repo_root / ".agents" / "quality"
    if not quality_dir.is_dir():
        return descriptors, manifest_paths, errors

    for manifest_path in sorted(quality_dir.glob("*-quality.json")):
        if not manifest_path.is_file():
            continue
        stack_id = manifest_path.name.removesuffix("-quality.json")
        if not stack_id:
            continue
        manifest_paths[stack_id] = manifest_path
        data, err = _read_json_dict(manifest_path)
        if err is not None or data is None:
            if err is not None:
                errors.append(err)
            continue

        builtin = BUILTIN_STACKS.get(stack_id)
        declared_exts = _normalize_extensions(data.get("extensions"))
        if builtin is None:
            if not declared_exts:
                continue
            base_exts = declared_exts
            base_test_pats: tuple[str, ...] = ()
            base_tier_b = TierBPolicy()
            base_surfaces = SurfaceRuleSet()
            base_tier_c = TierCPolicy()
            base_test_routing = TestRoutingPolicy()
        else:
            combined_exts = list(builtin.extensions)
            for ext in declared_exts:
                if ext not in combined_exts:
                    combined_exts.append(ext)
            base_exts = tuple(combined_exts)
            base_test_pats = builtin.test_path_patterns
            base_tier_b = builtin.default_tier_b
            base_surfaces = builtin.default_surfaces
            base_tier_c = builtin.tier_c_policy
            base_test_routing = builtin.test_routing

        merged_tier_b = _merge_tier_b_policy(
            base_tier_b,
            data.get("task_tier_b"),
            data.get("capabilities")
            if isinstance(data.get("capabilities"), Mapping)
            else None,
        )
        merged_surfaces, surf_errors = _merge_surface_ruleset(
            base_surfaces,
            data.get("triage_surfaces"),
            manifest_path.name,
        )
        errors.extend(surf_errors)
        test_routing = _parse_test_routing_policy(
            data.get("test_routing"), base_test_routing
        )

        descriptors[stack_id] = StackDescriptor(
            stack_id=stack_id,
            extensions=base_exts,
            test_path_patterns=base_test_pats,
            default_tier_b=merged_tier_b,
            default_surfaces=merged_surfaces,
            tier_c_policy=base_tier_c,
            test_routing=test_routing,
        )

    return descriptors, manifest_paths, errors


def _path_matches_stack(rel_path: str, desc: StackDescriptor) -> bool:
    norm = rel_path.replace("\\", "/").removeprefix("./")
    suffix = PurePosixPath(norm).suffix.lower()
    if suffix and suffix in desc.extensions:
        return True
    name = PurePosixPath(norm).name
    for mf in desc.default_tier_b.manifest_files:
        if mf.startswith("."):
            if norm.lower().endswith(mf.lower()):
                return True
        elif name == mf:
            return True
    return False


def _path_matches_boundary_trigger(rel_path: str, trigger: str) -> bool:
    norm = rel_path.replace("\\", "/").removeprefix("./")
    if trigger.endswith("/"):
        return norm.startswith(trigger) or f"/{trigger}" in f"/{norm}"
    if trigger.startswith("."):
        return norm.lower().endswith(trigger.lower())
    return PurePosixPath(norm).name == trigger or trigger in norm


def _has_clippy_deny_warnings(sub: Sequence[str]) -> bool:
    for idx, tok in enumerate(sub):
        if tok in ("-Dwarnings", "--deny=warnings"):
            return True
        if (
            tok in ("-D", "--deny")
            and idx + 1 < len(sub)
            and sub[idx + 1] == "warnings"
        ):
            return True
    return False


def _is_script_interpreter(token: str) -> bool:
    prog = Path(token).name.lower()
    return prog in ("sh", "bash", "zsh", "dash") or prog.startswith(("python", "pypy"))


def _extract_unwrapped_positional_targets(remaining_args: Sequence[str]) -> list[str]:
    """Extract positional file/dir arguments without defaulting empty args to '.'."""
    targets: list[str] = []
    idx = 0
    in_positional = False
    while idx < len(remaining_args):
        tok = remaining_args[idx]
        if in_positional:
            targets.append(tok)
            idx += 1
            continue
        if tok == "--":
            in_positional = True
            idx += 1
            continue
        if tok in _VALUE_TAKING_CLI_FLAGS:
            idx += 2
            continue
        if tok.startswith("-"):
            idx += 1
            continue
        targets.append(tok)
        idx += 1
    return targets


def _match_prefix_on_tokens(
    cand: Sequence[str],
    ptoks: Sequence[str],
    *,
    is_boundary: bool = False,
    allow_historical_prefix: bool = False,
) -> tuple[bool, int]:
    """Match a tokenized prefix against a candidate subcommand; return (matched, consumed_count)."""
    if not cand or not ptoks:
        return False, 0

    plen = len(ptoks)
    # 1. Exact or basename leading prefix match
    if len(cand) >= plen and list(cand[:plen]) == list(ptoks):
        return True, plen
    if (
        len(cand) >= plen
        and Path(cand[0]).name == Path(ptoks[0]).name
        and list(cand[1:plen]) == list(ptoks[1:])
    ):
        return True, plen

    # 2. Tool head + required flags anywhere in the same subcommand (e.g., cargo fmt --all -- --check, tsc -p x --noEmit)
    head_end = 0
    while head_end < plen and not ptoks[head_end].startswith("-"):
        head_end += 1
    head_nonflags = list(ptoks[:head_end])
    req_flags = [
        tok
        for tok in ptoks[head_end:]
        if tok.startswith("-") and tok.split("=", 1)[0] not in _MONOREPO_DIR_FLAGS
    ]
    if head_nonflags and req_flags and len(cand) >= len(head_nonflags):
        head_match = (
            Path(cand[0]).name == Path(head_nonflags[0]).name
            and list(cand[1 : len(head_nonflags)]) == head_nonflags[1:]
        )
        if head_match and all(flag in cand[len(head_nonflags) :] for flag in req_flags):
            return True, len(head_nonflags)

    # 3. Gradle task matching (e.g., ./gradlew :feature:wallet:spotlessCheck :feature:wallet:detekt)
    cand_prog = Path(cand[0]).name
    if cand_prog in ("gradlew", "gradlew.bat", "gradle"):
        if plen == 1:
            target_task = ptoks[0]
            if any(
                arg == target_task or arg.endswith(":" + target_task)
                for arg in cand[1:]
            ):
                return True, len(cand)
        elif Path(ptoks[0]).name in ("gradlew", "gradlew.bat", "gradle"):
            req_tasks = [t for t in ptoks[1:] if not t.startswith("-")]
            if req_tasks and all(
                any(arg == task or arg.endswith(":" + task) for arg in cand[1:])
                for task in req_tasks
            ):
                return True, len(cand)

    # 4. Script filename + required flags match (e.g., python3 $D3NEXUS_KIT/.../check_vanilla_js.py --target-dir src/preview)
    script_idx = next(
        (
            i
            for i, tok in enumerate(ptoks)
            if not tok.startswith("-")
            and tok.endswith((".py", ".sh"))
            and (i == 0 or _is_script_interpreter(ptoks[0]))
        ),
        None,
    )
    if script_idx is not None:
        script_basename = Path(ptoks[script_idx]).name
        cand_script_idx = next(
            (
                i
                for i, tok in enumerate(cand)
                if not tok.startswith("-")
                and Path(tok).name == script_basename
                and (i == 0 or _is_script_interpreter(cand[0]))
            ),
            None,
        )
        if cand_script_idx is not None:
            ignored_script_flags = _MONOREPO_DIR_FLAGS | frozenset({"--base-ref"})
            req_script_flags = [
                tok.split("=", 1)[0]
                for tok in ptoks[script_idx + 1 :]
                if tok.startswith("--")
                and len(tok) > 2
                and tok.split("=", 1)[0] not in ignored_script_flags
            ]
            cand_flag_names = {
                tok.split("=", 1)[0]
                for tok in cand[cand_script_idx + 1 :]
                if tok.startswith("--") and len(tok) > 2
            }
            if all(flag in cand_flag_names for flag in req_script_flags):
                return True, len(cand)

    # 5. Boundary-specific filter or keyword matches (e.g. ArchTests, xtask, boundaries, konsist)
    if is_boundary and plen == 1:
        needle = ptoks[0]
        if needle == "ArchTests" and any("ArchTests" in tok for tok in cand):
            return True, len(cand)
        if needle.lower() in _BOUNDARY_KEYWORD_PREFIXES:
            low = needle.lower()
            if any(low in tok.lower() for tok in cand):
                return True, len(cand)

    # 6. Historical/manifest capability prefix tolerance (drop final target arg from manifest cmd)
    if allow_historical_prefix and plen > 1:
        trimmed = list(ptoks[:-1])
        if (
            len(cand) >= len(trimmed)
            and Path(cand[0]).name == Path(trimmed[0]).name
            and list(cand[1 : len(trimmed)]) == trimmed[1:]
        ):
            return True, len(trimmed)

    return False, 0


def _subcommand_matches_prefix(
    sub: Sequence[str],
    prefix: str,
    *,
    is_boundary: bool = False,
    allow_historical_prefix: bool = False,
) -> tuple[bool, list[str]]:
    """Return (matched, remaining_args_after_prefix) for one sequential subcommand."""
    try:
        ptoks = shlex.split(prefix)
    except ValueError:
        ptoks = prefix.split()
    if not ptoks:
        return False, []

    raw_sub = _strip_version_manager_wrappers(sub)
    raw_ptoks = _strip_version_manager_wrappers(ptoks)
    if not raw_sub or not raw_ptoks:
        return False, []

    sub_dir = _extract_monorepo_dir_wrapper(raw_sub)
    ptoks_dir = _extract_monorepo_dir_wrapper(raw_ptoks)
    if sub_dir is not None and ptoks_dir != sub_dir:
        return False, []

    def _dedupe_variants(tokens: list[str]) -> list[list[str]]:
        variants: list[list[str]] = []
        for candidate in (
            tokens,
            _strip_monorepo_dir_flags(tokens),
            _strip_command_wrappers(tokens),
        ):
            if candidate and candidate not in variants:
                variants.append(candidate)
        return variants

    sub_candidates = _dedupe_variants(raw_sub)
    ptoks_candidates = _dedupe_variants(raw_ptoks)

    for cand in sub_candidates:
        for p_cand in ptoks_candidates:
            matched, consumed = _match_prefix_on_tokens(
                cand,
                p_cand,
                is_boundary=is_boundary,
                allow_historical_prefix=allow_historical_prefix,
            )
            if not matched:
                continue
            remaining = cand[consumed:]
            if ptoks_dir is not None and sub_dir is None:
                pos_targets = _extract_unwrapped_positional_targets(remaining)
                if not pos_targets:
                    continue
                if not all(
                    (
                        (
                            clean := target.split("::", 1)[0]
                            .strip()
                            .replace("\\", "/")
                            .removeprefix("./")
                            .rstrip("/")
                        )
                        == ptoks_dir
                        or clean.startswith(ptoks_dir + "/")
                    )
                    for target in pos_targets
                ):
                    continue
            return True, remaining
    return False, []


def _extract_format_targets(
    remaining_args: Sequence[str], full_sub: Sequence[str]
) -> list[str]:
    """Extract positional file/dir targets from a matched format subcommand."""
    targets: list[str] = []
    idx = 0
    in_positional = False
    while idx < len(remaining_args):
        tok = remaining_args[idx]
        if in_positional:
            targets.append(tok)
            idx += 1
            continue
        if tok == "--":
            in_positional = True
            idx += 1
            continue
        if tok in _VALUE_TAKING_FORMAT_FLAGS:
            idx += 2
            continue
        if tok.startswith("-"):
            idx += 1
            continue
        targets.append(tok)
        idx += 1

    if targets:
        return targets
    # Subshell expressions like $(git diff ...) do not cover untracked (new) files
    if any("$(" in tok or "`" in tok for tok in full_sub):
        return []
    return ["."]


class TierBContractAdapter:
    """Open-Closed Tier B static gate adapter keyed by active manifests and file suffixes."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root: Path | None = repo_root
        self.descriptors: dict[str, StackDescriptor]
        self.validation_errors: tuple[str, ...]
        if repo_root is None:
            self.descriptors = dict(BUILTIN_STACKS)
            self.validation_errors = ()
        else:
            loaded, _, errors = _load_repo_manifests(repo_root)
            merged = dict(BUILTIN_STACKS)
            merged.update(loaded)
            self.descriptors = merged
            self.validation_errors = tuple(errors)

    @classmethod
    def from_repo(cls, repo_root: Path) -> TierBContractAdapter:
        return cls(repo_root)

    @classmethod
    def has_provider_manifests(cls, repo_root: Path) -> bool:
        quality_dir = repo_root / ".agents" / "quality"
        if not quality_dir.is_dir():
            return False
        return any(p.is_file() for p in quality_dir.glob("*-quality.json"))

    @classmethod
    def resolve_active_stacks(
        cls, repo_root: Path, allowed_paths: Sequence[str]
    ) -> list[StackDescriptor]:
        loaded, _, _ = _load_repo_manifests(repo_root)
        if not loaded or not allowed_paths:
            return []
        normalized_paths = [_normalize_allowed_entry(p)[0] for p in allowed_paths]
        active: list[StackDescriptor] = []
        for stack_id in sorted(loaded.keys()):
            desc = loaded[stack_id]
            if any(_path_matches_stack(path, desc) for path in normalized_paths):
                active.append(desc)
        return active

    @classmethod
    def validate_tier_b(
        cls,
        repo_root: Path,
        stem: str,
        allowed_entries: Sequence[Any],
        rows: Sequence[Any],
        *,
        allow_historical_prefix: bool = False,
    ) -> list[tuple[str, str]]:
        """Validate TIER-B rows for active non-Python stacks plus custom extension manifests."""
        normalized_entries = [_normalize_allowed_entry(e) for e in allowed_entries]
        allowed_paths = [path for path, _ in normalized_entries if path]
        if not allowed_paths:
            return []

        loaded, manifest_paths, manifest_errors = _load_repo_manifests(repo_root)
        problems: list[tuple[str, str]] = []
        where = f"{stem}:Verification"

        # Surface malformed manifests only when touched files belong to that built-in stack
        for stack_id, mpath in sorted(manifest_paths.items()):
            if stack_id in loaded or stack_id == "python":
                continue
            builtin = BUILTIN_STACKS.get(stack_id)
            if builtin is not None and any(
                _path_matches_stack(p, builtin) for p in allowed_paths
            ):
                matching_err = next(
                    (e for e in manifest_errors if mpath.name in e), None
                )
                if matching_err:
                    problems.append((where, f"invalid .agents/quality/{matching_err}"))

        active_stacks = [
            loaded[sid]
            for sid in sorted(loaded.keys())
            if sid != "python"
            and any(_path_matches_stack(p, loaded[sid]) for p in allowed_paths)
        ]
        if not active_stacks:
            return problems

        tier_b_rows = [r for r in rows if getattr(r, "phase", "") == "TIER-B"]
        subcommands: list[list[str]] = [
            sub
            for row in tier_b_rows
            for sub in _split_sequential_subcommands(str(getattr(row, "command", "")))
        ]

        for desc in active_stacks:
            policy = desc.default_tier_b
            stack_all_paths = [p for p in allowed_paths if _path_matches_stack(p, desc)]
            stack_concrete_ext_files = [
                p
                for p in stack_all_paths
                if not _GLOB_CHARS_RE.search(p)
                and PurePosixPath(p).suffix.lower() in desc.extensions
            ]

            # 1. Format check (+ optional full Allowed-files coverage for new & existing files)
            if policy.format_prefixes:
                matched_fmt_targets: list[str] = []
                has_format = False
                for sub in subcommands:
                    for prefix in policy.format_prefixes:
                        ok, rem = _subcommand_matches_prefix(
                            sub,
                            prefix,
                            allow_historical_prefix=allow_historical_prefix,
                        )
                        if ok:
                            has_format = True
                            matched_fmt_targets.extend(
                                _extract_format_targets(rem, sub)
                            )
                            break
                if not has_format:
                    problems.append(
                        (
                            where,
                            f"{desc.stack_id} task missing TIER-B format check "
                            f"(expected one of: {', '.join(policy.format_prefixes)})",
                        )
                    )
                elif (
                    policy.require_all_allowed_files_in_format
                    and stack_concrete_ext_files
                    and not allow_historical_prefix
                ):
                    missing_fmt = [
                        path
                        for path in stack_concrete_ext_files
                        if not any(
                            _target_covers_path(t, path) for t in matched_fmt_targets
                        )
                    ]
                    if missing_fmt:
                        problems.append(
                            (
                                where,
                                f"{desc.stack_id} task TIER-B format check must cover all Allowed "
                                f"{desc.stack_id} files (including (new) files); "
                                f"missing: {', '.join(missing_fmt)}",
                            )
                        )

            # 2. Lint check (including Rust clippy -D warnings enforcement)
            if policy.lint_prefixes:
                has_lint = False
                clippy_missing_deny = False
                for sub in subcommands:
                    for prefix in policy.lint_prefixes:
                        ok, _ = _subcommand_matches_prefix(
                            sub,
                            prefix,
                            allow_historical_prefix=allow_historical_prefix,
                        )
                        if not ok:
                            continue
                        if (
                            policy.require_clippy_deny_warnings
                            and "clippy" in prefix
                            and not _has_clippy_deny_warnings(sub)
                        ):
                            clippy_missing_deny = True
                            continue
                        has_lint = True
                        break
                    if has_lint:
                        break
                if not has_lint:
                    if clippy_missing_deny:
                        problems.append(
                            (
                                where,
                                f"{desc.stack_id} task TIER-B cargo clippy must pass -D warnings",
                            )
                        )
                    else:
                        problems.append(
                            (
                                where,
                                f"{desc.stack_id} task missing TIER-B lint check "
                                f"(expected one of: {', '.join(policy.lint_prefixes)})",
                            )
                        )

            # 3. Typecheck check
            if policy.typecheck_prefixes:
                has_typecheck = any(
                    _subcommand_matches_prefix(
                        sub,
                        prefix,
                        allow_historical_prefix=allow_historical_prefix,
                    )[0]
                    for sub in subcommands
                    for prefix in policy.typecheck_prefixes
                )
                if not has_typecheck:
                    problems.append(
                        (
                            where,
                            f"{desc.stack_id} task missing TIER-B type-check "
                            f"(expected one of: {', '.join(policy.typecheck_prefixes)})",
                        )
                    )

            # 4. Conditional boundary / architecture check
            if policy.boundary_triggers and policy.boundary_prefixes:
                triggered_files = [
                    path
                    for path in stack_all_paths
                    if any(
                        _path_matches_boundary_trigger(path, trig)
                        for trig in policy.boundary_triggers
                    )
                ]
                if triggered_files:
                    has_boundary = any(
                        _subcommand_matches_prefix(
                            sub,
                            prefix,
                            is_boundary=True,
                            allow_historical_prefix=allow_historical_prefix,
                        )[0]
                        for sub in subcommands
                        for prefix in policy.boundary_prefixes
                    )
                    if not has_boundary:
                        problems.append(
                            (
                                where,
                                f"{desc.stack_id} task touches boundary files "
                                f"({', '.join(triggered_files)}) and requires a TIER-B "
                                f"boundary/architecture check "
                                f"(expected one of: {', '.join(policy.boundary_prefixes)})",
                            )
                        )

        return problems


def _git_output(repo_dir: Path, *args: str) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None


def _is_untracked_and_gitignored(repo_dir: Path, rel_path: str) -> bool:
    """Return True iff `rel_path` has zero tracked files and is ignored by git."""
    inside = _git_output(repo_dir, "rev-parse", "--is-inside-work-tree")
    if inside is None or inside.returncode != 0 or inside.stdout.strip() != "true":
        return False

    tracked = _git_output(repo_dir, "ls-files", "--", rel_path)
    if tracked is None or tracked.returncode != 0 or tracked.stdout.strip():
        return False

    ignored = _git_output(repo_dir, "check-ignore", "-q", "--", rel_path)
    if ignored is not None and ignored.returncode == 0:
        return True

    target = repo_dir / rel_path
    if target.is_dir():
        ignored_dir = _git_output(
            repo_dir, "check-ignore", "-q", "--", rel_path.rstrip("/") + "/"
        )
        if ignored_dir is not None and ignored_dir.returncode == 0:
            return True
        # Handle patterns like `secureFiles/*` where all children are ignored and none unignored
        unignored_children = _git_output(
            repo_dir, "ls-files", "--others", "--exclude-standard", "--", rel_path
        )
        ignored_children = _git_output(
            repo_dir,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "--",
            rel_path,
        )
        if (
            unignored_children is not None
            and unignored_children.returncode == 0
            and not unignored_children.stdout.strip()
            and ignored_children is not None
            and ignored_children.returncode == 0
            and bool(ignored_children.stdout.strip())
        ):
            return True

    return False


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
    elif path.is_dir():
        shutil.rmtree(path, ignore_errors=True)


def _copy_cow_tree(src: Path, dst: Path) -> None:
    """Copy `src` to `dst` using APFS clone (`cp -c -R`) on Darwin with shutil fallback."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "darwin":
        res = subprocess.run(
            ["cp", "-c", "-R", str(src), str(dst)],
            check=False,
            capture_output=True,
        )
        if res.returncode == 0 and dst.exists() and not dst.is_symlink():
            return
        if dst.exists() or dst.is_symlink():
            _remove_path(dst)

    if src.is_dir():
        shutil.copytree(src, dst, symlinks=False, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def _expand_rule_paths(
    base_dir: Path, rule_path: str, *, allow_symlink_leaf: bool = False
) -> list[Path]:
    """Expand a validated relative rule path or glob strictly within `base_dir`."""
    if not _is_safe_relative_path(
        rule_path, base_dir, allow_symlink_leaf=allow_symlink_leaf
    ):
        return []
    root_resolved = base_dir.resolve()
    raw_matches = (
        sorted(base_dir.glob(rule_path))
        if _GLOB_CHARS_RE.search(rule_path)
        else [base_dir / rule_path]
    )
    safe: list[Path] = []
    for candidate in raw_matches:
        exists = candidate.is_symlink() if allow_symlink_leaf else candidate.exists()
        if not exists and not candidate.exists():
            continue
        try:
            rel = candidate.relative_to(base_dir)
        except ValueError:
            continue
        if any(part == ".." for part in rel.parts):
            continue
        if allow_symlink_leaf and candidate.is_symlink():
            if not candidate.parent.resolve(strict=False).is_relative_to(root_resolved):
                continue
        else:
            if not candidate.resolve(strict=False).is_relative_to(root_resolved):
                continue
        safe.append(candidate)
    return safe


def _load_pool_mounts_with_errors(
    main_wt: Path,
) -> tuple[list[PoolMountRule], list[str]]:
    by_path: dict[str, PoolMountRule] = {}
    order: list[str] = []
    for rel in DEFAULT_SYMLINK_MOUNTS:
        by_path[rel] = PoolMountRule(path=rel, mode="symlink", optional=True)
        order.append(rel)
    for rel in DEFAULT_COW_COPY_MOUNTS:
        by_path[rel] = PoolMountRule(path=rel, mode="cow_copy", optional=True)
        order.append(rel)

    errors: list[str] = []
    config_path = main_wt / ".agents" / "quality" / "check_quality.json"
    if not config_path.is_file():
        return [by_path[p] for p in order], errors

    data, read_err = _read_json_dict(config_path)
    if read_err is not None or data is None:
        if read_err is not None:
            errors.append(read_err)
        return [by_path[p] for p in order], errors

    raw_mounts = data.get("pool_mounts")
    if raw_mounts is None:
        return [by_path[p] for p in order], errors
    if not isinstance(raw_mounts, list):
        errors.append("check_quality.json:pool_mounts must be a JSON array")
        return [by_path[p] for p in order], errors

    for idx, item in enumerate(raw_mounts):
        if not isinstance(item, dict):
            errors.append(f"check_quality.json:pool_mounts[{idx}] must be an object")
            continue
        raw_path = item.get("path")
        raw_mode = item.get("mode")
        if raw_mode not in ("symlink", "cow_copy"):
            errors.append(
                f"check_quality.json:pool_mounts[{idx}] invalid mode {raw_mode!r} "
                f"(expected 'symlink' or 'cow_copy')"
            )
            continue
        if not isinstance(raw_path, str) or not _is_safe_relative_path(
            raw_path, main_wt
        ):
            errors.append(
                f"check_quality.json:pool_mounts[{idx}] unsafe path {raw_path!r} "
                f"(path traversal or outside repo root)"
            )
            continue
        norm_path = raw_path.strip().replace("\\", "/").rstrip("/")
        mode_lit: Literal["symlink", "cow_copy"] = (
            "symlink" if raw_mode == "symlink" else "cow_copy"
        )
        optional = bool(item.get("optional", True))
        if norm_path not in by_path:
            order.append(norm_path)
        by_path[norm_path] = PoolMountRule(
            path=norm_path, mode=mode_lit, optional=optional
        )

    return [by_path[p] for p in order], errors


class PoolWorkspaceStrategy:
    """Two-mode slot mount strategy (`symlink` vs `apfs_cow_tree` / `cow_copy`)."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root: Path | None = repo_root
        if repo_root is None:
            default_rules = [
                *(
                    PoolMountRule(path=p, mode="symlink")
                    for p in DEFAULT_SYMLINK_MOUNTS
                ),
                *(
                    PoolMountRule(path=p, mode="cow_copy")
                    for p in DEFAULT_COW_COPY_MOUNTS
                ),
            ]
            self.rules: tuple[PoolMountRule, ...] = tuple(default_rules)
            self.validation_errors: tuple[str, ...] = ()
        else:
            rules, errors = _load_pool_mounts_with_errors(repo_root)
            self.rules = tuple(rules)
            self.validation_errors = tuple(errors)

    @classmethod
    def from_repo(cls, repo_root: Path) -> PoolWorkspaceStrategy:
        return cls(repo_root)

    @classmethod
    def resolve_mounts(cls, main_wt: Path) -> list[PoolMountRule]:
        rules, _ = _load_pool_mounts_with_errors(main_wt)
        return rules

    @classmethod
    def materialize_mounts(cls, main_wt: Path, slot_path: Path) -> dict[str, list[str]]:
        """Materialize symlink and untracked+gitignored cow_copy mounts into `slot_path`."""
        result: dict[str, list[str]] = {"symlink": [], "cow_copy": []}
        if not main_wt.is_dir() or not slot_path.is_dir():
            return result

        rules = cls.resolve_mounts(main_wt)
        symlink_set: set[str] = set()
        cow_set: set[str] = set()

        for rule in rules:
            candidates = _expand_rule_paths(
                main_wt, rule.path, allow_symlink_leaf=False
            )
            for src in candidates:
                rel = src.relative_to(main_wt).as_posix()
                dst = slot_path / rel
                if rule.mode == "symlink":
                    if dst.is_symlink():
                        symlink_set.add(rel)
                        continue
                    if dst.exists():
                        continue
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        dst.symlink_to(src)
                        symlink_set.add(rel)
                    except OSError:
                        continue
                else:
                    if not _is_untracked_and_gitignored(main_wt, rel):
                        continue
                    if dst.is_symlink():
                        dst.unlink(missing_ok=True)
                    if dst.exists():
                        cow_set.add(rel)
                        continue
                    _copy_cow_tree(src, dst)
                    if dst.exists() and not dst.is_symlink():
                        cow_set.add(rel)

        result["symlink"] = sorted(symlink_set)
        result["cow_copy"] = sorted(cow_set)
        return result

    @classmethod
    def get_excluded_relpaths(cls, main_wt: Path, slot_path: Path) -> list[str]:
        """Return ONLY paths actually materialized in `slot_path` as active mounts."""
        if not slot_path.is_dir():
            return []

        rules = cls.resolve_mounts(main_wt if main_wt.is_dir() else slot_path)
        excluded: set[str] = set()

        for rule in rules:
            candidates = _expand_rule_paths(
                slot_path, rule.path, allow_symlink_leaf=(rule.mode == "symlink")
            )
            for candidate in candidates:
                rel = candidate.relative_to(slot_path).as_posix()
                if rule.mode == "symlink":
                    if candidate.is_symlink():
                        excluded.add(rel)
                else:
                    if (
                        candidate.exists()
                        and not candidate.is_symlink()
                        and _is_untracked_and_gitignored(slot_path, rel)
                    ):
                        excluded.add(rel)

        return sorted(excluded)


class TriageSurfaceRegistry:
    """Suffix-scoped Tier 1 risk triage registry over a language-neutral baseline."""

    def __init__(
        self,
        suffix_rules: Mapping[str, SurfaceRuleSet],
        *,
        baseline: SurfaceRuleSet = BASELINE_SURFACES,
        validation_errors: Sequence[str] = (),
    ) -> None:
        self._suffix_rules: dict[str, SurfaceRuleSet] = dict(suffix_rules)
        self._baseline: SurfaceRuleSet = baseline
        self.validation_errors: tuple[str, ...] = tuple(validation_errors)

    @classmethod
    def default(cls) -> TriageSurfaceRegistry:
        suffix_map: dict[str, SurfaceRuleSet] = {}
        for desc in BUILTIN_STACKS.values():
            for ext in desc.extensions:
                suffix_map[ext.lower()] = desc.default_surfaces
        return cls(suffix_map)

    @classmethod
    def from_repo(cls, repo_root: Path) -> TriageSurfaceRegistry:
        suffix_map: dict[str, SurfaceRuleSet] = {}
        for desc in BUILTIN_STACKS.values():
            for ext in desc.extensions:
                suffix_map[ext.lower()] = desc.default_surfaces

        loaded, _, errors = _load_repo_manifests(repo_root)
        for desc in loaded.values():
            for ext in desc.extensions:
                suffix_map[ext.lower()] = desc.default_surfaces

        return cls(suffix_map, validation_errors=errors)

    @staticmethod
    def is_test_file(rel_path: str) -> bool:
        """Classify polyglot test files across Python, Dart, Rust, Web, Kotlin, and Swift."""
        norm = rel_path.replace("\\", "/").lstrip("./")
        if not norm:
            return False
        posix = PurePosixPath(norm)
        dir_parts = posix.parts[:-1]
        if any(
            part in _TEST_DIR_MARKERS or part.lower() in _TEST_DIR_MARKERS
            for part in dir_parts
        ):
            return True
        name = posix.name
        if name.startswith("test_") and name.endswith(".py"):
            return True
        if name.endswith(("_test.py", "_test.dart", "_test.rs")):
            return True
        if ".test." in name or ".spec." in name:
            return True
        return name.endswith(
            ("Test.kt", "Tests.kt", "Spec.kt", "Test.swift", "Tests.swift")
        )

    def rules_for_path(self, rel_path: str) -> SurfaceRuleSet | None:
        suffix = PurePosixPath(rel_path.replace("\\", "/")).suffix.lower()
        if not suffix:
            return None
        return self._suffix_rules.get(suffix)

    def match_test_line(self, rel_path: str, sign: str, line: str) -> tuple[bool, bool]:
        """Return (is_assertion_line, is_added_skip_weakening) for one diff line in a test file."""
        if sign not in ("+", "-"):
            return False, False
        suffix_rules = self.rules_for_path(rel_path)
        assertion_patterns = (
            suffix_rules.test_assertion
            if suffix_rules is not None and suffix_rules.test_assertion
            else self._baseline.test_assertion
        )
        weakening_patterns = self._baseline.test_weakening + (
            suffix_rules.test_weakening if suffix_rules is not None else ()
        )
        matched_assertion = any(pat.search(line) for pat in assertion_patterns)
        matched_skip = sign == "+" and any(
            pat.search(line) for pat in weakening_patterns
        )
        return matched_assertion, matched_skip

    def match_line(self, rel_path: str, sign: str, line: str) -> set[str]:
        """Return fired Tier 1 trigger codes for one added/removed diff line."""
        if sign not in ("+", "-"):
            return set()
        if self.is_test_file(rel_path):
            _, is_skip = self.match_test_line(rel_path, sign, line)
            return {"TEST_ASSERTION_WEAKENED"} if is_skip else set()

        fired: set[str] = set()
        suffix_rules = self.rules_for_path(rel_path)
        rule_sets = (
            (self._baseline, suffix_rules)
            if suffix_rules is not None
            else (self._baseline,)
        )

        for rset in rule_sets:
            if any(pat.search(line) for pat in rset.signature):
                fired.add("PUBLIC_SIGNATURE_CHANGED")
            if any(pat.search(line) for pat in rset.api_wire):
                fired.add("API_ROUTE_OR_SCHEMA_CHANGED")
            if any(pat.search(line) for pat in rset.persistence):
                fired.add("DB_OR_PERSISTENCE_CHANGED")
            if any(pat.search(line) for pat in rset.concurrency):
                fired.add("CONCURRENCY_OR_LOCKING_CHANGED")

        return fired


class TierCTaxonomy:
    """Enforces explicit Tier C2 Needs gating, heuristic warnings, and HLD root validation."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root: Path | None = repo_root
        self.policies: dict[str, TierCPolicy] = {
            sid: desc.tier_c_policy for sid, desc in BUILTIN_STACKS.items()
        }

    @classmethod
    def from_repo(cls, repo_root: Path) -> TierCTaxonomy:
        return cls(repo_root)

    @classmethod
    def check_tier_c_rows(
        cls,
        stem: str,
        rows: Sequence[Any],
        active_stacks: Sequence[StackDescriptor] | None = None,
    ) -> tuple[list[tuple[str, str]], list[str]]:
        """Validate TIER-C rows; return (hard_problems, non_blocking_warnings)."""
        problems: list[tuple[str, str]] = []
        warnings: list[str] = []

        ordered_stacks: list[StackDescriptor] = []
        seen_ids: set[str] = set()
        for stack in active_stacks or ():
            if stack.stack_id not in seen_ids:
                ordered_stacks.append(stack)
                seen_ids.add(stack.stack_id)
        for sid, stack in BUILTIN_STACKS.items():
            if sid not in seen_ids:
                ordered_stacks.append(stack)
                seen_ids.add(sid)

        for row in rows:
            if getattr(row, "phase", "") != "TIER-C":
                continue
            row_id = str(getattr(row, "id", "TIER-C"))
            command = str(getattr(row, "command", ""))
            needs = tuple(getattr(row, "needs", ()) or ())
            if needs:
                continue

            if EXPLICIT_TIER_C2_RE.search(command):
                problems.append(
                    (
                        f"{stem}:Verification:{row_id}",
                        f"Explicit Tier C2 row {row_id} (`# tier: C2`) must declare a non-empty "
                        f"Needs variable (e.g., FLUTTER_DEVICE, ANDROID_DEVICE, IOS_SIMULATOR, "
                        f"PLAYWRIGHT_BROWSER, DOCKER_LIVE)",
                    )
                )
                continue

            for stack in ordered_stacks:
                c_policy = stack.tier_c_policy
                if any(
                    pat.search(command) for pat in c_policy.tier_c2_command_patterns
                ):
                    hint = c_policy.default_needs_hint or "LIVE_ENV"
                    warnings.append(
                        f"{stem}:Verification:{row_id}: TIER-C command looks like a heavy "
                        f"{stack.stack_id} Tier C2 runtime without Needs; consider gating with "
                        f"Needs: {hint} and `# tier: C2`"
                    )
                    break

        return problems, warnings

    @classmethod
    def validate_integration_test_roots(
        cls,
        repo_root: Path,
        roots: Sequence[str],
        tracked_files: Iterable[str],
        created_files: Iterable[str],
    ) -> list[str]:
        """Validate HLD `Integration test roots:` paths against traversal and known/planned files."""
        problems: list[str] = []
        candidates = sorted(
            {
                p.strip().replace("\\", "/").removeprefix("./")
                for p in (*tracked_files, *created_files)
                if p and p.strip()
            }
        )

        for raw_root in roots:
            root = raw_root.strip()
            if not root:
                continue
            if not _is_safe_relative_path(root, repo_root):
                problems.append(
                    f"Integration test root {raw_root!r} is unsafe "
                    f"(path traversal or escapes repository root)"
                )
                continue

            norm = root.replace("\\", "/").removeprefix("./").rstrip("/")
            if _GLOB_CHARS_RE.search(norm):
                matched = any(
                    _glob_matches(norm, path) or _glob_matches(norm + "/**", path)
                    for path in candidates
                )
            else:
                matched = any(
                    path == norm or path.startswith(norm + "/") for path in candidates
                )

            if not matched:
                problems.append(
                    f"Integration test root {raw_root!r} matches no tracked or planned (new) files"
                )

        return problems
