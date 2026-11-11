#!/usr/bin/env bash
# Pre-release checks for the agent kit. Run before publishing — a broken skill
# propagates to every project on every machine that has the plugin installed.
# Usage:
#   bash scripts/verify.sh          # Fast parallel check + smart 2-tier content-hash cache
#   bash scripts/verify.sh --full   # Force full re-run of all Python unit & pytest suites
set -uo pipefail

FORCE_FULL=0
if [ "${1:-}" = "--full" ]; then
  FORCE_FULL=1
fi

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KIT_DIR"
FAILED=0
note() { printf '%s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1"; FAILED=1; }

note "== 1. JSON manifests parse & 1b. Runtime versions and Codex marketplace agree =="
python3 - <<'PY' || FAILED=1
import json, pathlib, re, sys

MANIFEST_PATHS = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
)
parsed = {}
for p in MANIFEST_PATHS:
    try:
        parsed[p] = json.loads(pathlib.Path(p).read_text())
        print(f"  ok   {p}")
    except Exception as exc:
        print(f"  FAIL {p} is not valid JSON: {exc}")
        sys.exit(1)

try:
    manifests = [parsed[p] for p in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json")]
    claude = parsed[".claude-plugin/marketplace.json"]
    catalog = parsed[".agents/plugins/marketplace.json"]
    entry, = [p for p in catalog["plugins"] if p["name"] == "d3nexus"]
    claude_entry, = [p for p in claude["plugins"] if p["name"] == "d3nexus"]
    versions = {m["version"] for m in manifests} | {claude_entry["version"]}
    assert all(m["name"] == "d3nexus" for m in manifests), "plugin names must agree"
    assert len(versions) == 1, f"release versions differ: {sorted(versions)}"
    version, = versions
    assert re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version), "invalid release version"
    assert re.search(r'^## ' + re.escape(version) + r' — \d{4}-\d{2}-\d{2}\n\n\S',
                     pathlib.Path("CHANGELOG.md").read_text(), re.M), "missing dated release notes"
    assert catalog["name"] == claude["name"] == "danhdue-agent-tools", "marketplace names differ"
    assert entry["source"] == {"source": "local", "path": "./"}, "marketplace must load the repo root"
    assert entry["policy"] == {"installation": "AVAILABLE", "authentication": "ON_INSTALL"}, "invalid policy"
    assert entry["category"] == "Developer Tools", "missing marketplace category"
    codex = manifests[2]
    assert codex["skills"] == "./skills/" and pathlib.Path(codex["skills"]).is_dir(), "missing shared skills"
    assert not ({"apps", "mcpServers", "hooks"} & codex.keys()), "unexpected Codex components"
    for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        assert codex["interface"][field].strip(), f"missing Codex interface.{field}"
    print(f"  ok   d3nexus {version}, shared skills, and repo marketplace")
except (AssertionError, KeyError, ValueError, OSError, TypeError) as error:
    print(f"  FAIL {error}")
    sys.exit(1)
PY

note "== 2. Skill frontmatter is exactly name + description =="
python3 - <<'PY' || FAILED=1
import pathlib, re, sys
bad = 0
for p in sorted(pathlib.Path("skills").glob("*/SKILL.md")):
    text = p.read_text()
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not m:
        print(f"  FAIL {p}: missing YAML frontmatter"); bad = 1; continue
    keys = re.findall(r'^([A-Za-z_][\w-]*):', m.group(1), re.M)
    if set(keys) != {"name", "description"}:
        print(f"  FAIL {p}: frontmatter keys {keys} (expected exactly name, description)")
        bad = 1
    else:
        name = re.search(r'^name:\s*(.+)$', m.group(1), re.M).group(1).strip().strip('"\'')
        if name != p.parent.name:
            print(f"  WARN {p}: name '{name}' differs from directory '{p.parent.name}'")
print(f"  checked {len(list(pathlib.Path('skills').glob('*/SKILL.md')))} skills")
sys.exit(bad)
PY

note "== 3. Relative links resolve =="
python3 - <<'PY' || FAILED=1
import pathlib, re, sys
bad = 0
targets = list(pathlib.Path("skills").glob("*/SKILL.md")) \
        + list(pathlib.Path("skills").glob("*/**/*.md")) \
        + list(pathlib.Path("rules").glob("*.md")) \
        + [pathlib.Path("README.md"), pathlib.Path("CLAUDE.md"), pathlib.Path("CHANGELOG.md")]
targets = sorted(set(targets))
def strip_fences(s):
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    return re.sub(r'`[^`\n]*`', '', s)

for p in targets:
    if not p.exists():
        continue
    for link in re.findall(r'\]\(([^)#][^)]*)\)', strip_fences(p.read_text())):
        if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
            continue
        if not (p.parent / link.split('#')[0]).exists():
            print(f"  FAIL {p} -> {link}"); bad = 1
print(f"  checked {len(targets)} files")
sys.exit(bad)
PY

note "== 4. ToC anchors match headings =="
python3 - <<'PY' || FAILED=1
import pathlib, re, sys
def anchor(h):
    h = h.lower(); h = re.sub(r'[^\w\s-]', '', h); return '#' + h.replace(' ', '-')
bad = 0
for p in sorted(pathlib.Path("skills").glob("*/SKILL.md")) + [pathlib.Path("README.md")]:
    s = p.read_text(); fence = False; heads = []
    for ln in s.split("\n"):
        if ln.startswith("```"): fence = not fence; continue
        if not fence and re.match(r'^#{2,6} ', ln):
            heads.append(anchor(re.sub(r'^#+ ', '', ln).rstrip()))
    for link in re.findall(r'\]\((#[^)]+)\)', s):
        if link.lower() not in heads:
            print(f"  FAIL {p} -> {link}"); bad = 1
sys.exit(bad)
PY

note "== 5. No stale cross-namespace references =="
if grep -rq "superpowers:" skills rules 2>/dev/null; then
  grep -rn "superpowers:" skills rules | head -5
  fail "skills still reference the superpowers namespace"
else
  note "  ok   none"
fi

note "== 5b. Rule files start with frontmatter =="
for f in rules/*.md; do
  if head -1 "$f" | grep -qx -- '---'; then
    note "  ok   $f"
  else
    fail "$f has no frontmatter — Antigravity will refuse to load it"
  fi
done

note "== 6. Session-start hook emits valid JSON for both runtimes =="
hook_case() {
  local label="$1" expect="$2" env="$3" payload="$4" out
  out=$(printf '%s' "$payload" | env $env bash hooks/session-start 2>/dev/null) || {
    fail "hook exited non-zero: $label"; return; }
  printf '%s' "$out" | python3 -c "
import json,sys
d=json.load(sys.stdin)
got='inject' if ('hookSpecificOutput' in d or 'injectSteps' in d) else ('silent' if d=={} else 'other')
sys.exit(0 if got=='$expect' else 1)
" 2>/dev/null && note "  ok   $label" || fail "$label — expected $expect"
}
hook_case "Claude Code SessionStart"        inject "CLAUDE_PLUGIN_ROOT=$KIT_DIR" '{}'
hook_case "Antigravity first invocation"    inject "X=1" '{"invocationNum":0}'
hook_case "Antigravity second invocation"   silent "X=1" '{"invocationNum":1}'
hook_case "Antigravity later invocation"    silent "X=1" '{"invocationNum":7}'
hook_case "Antigravity unreadable payload"  silent "X=1" 'not json'

note "== 7. Methodology skills stay faithful to their sources =="
python3 scripts/check_source_fidelity.py || FAILED=1

note "== 8. Every supporting skill file is referenced by something =="
# Driven from `git ls-files` instead of `rglob("*")` so untracked caches, .venv, and .devtool
# archives never pollute or slow down the scan.
python3 - <<'PY' || FAILED=1
import pathlib, subprocess, sys

ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
LEGAL_PREFIXES = ("LICENSE", "COPYING", "NOTICE")
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ""}

def is_skill_content(p: pathlib.Path) -> bool:
    if p.name == "SKILL.md" or "__pycache__" in p.parts:
        return False
    if p.suffix.lower() in ASSET_SUFFIXES:
        return False
    if p.name.upper().startswith(LEGAL_PREFIXES):
        return False
    return not any(part.startswith(".") for part in p.parts)

tracked = [
    pathlib.Path(line)
    for line in subprocess.check_output(["git", "ls-files"], text=True).splitlines()
    if line
]

supporting = [p for p in tracked if len(p.parts) >= 3 and p.parts[0] == "skills" and p.is_file() and is_skill_content(p)]
corpus = [p for p in tracked if p.is_file() and p.suffix in TEXT_SUFFIXES]

texts = {}
for c in corpus:
    try:
        texts[c] = c.read_text(errors="ignore")
    except OSError:
        pass

bad = 0
for f in sorted(supporting):
    name = f.name
    if any(other != f and name in body for other, body in texts.items()):
        continue
    print(f"  FAIL {f} is referenced by nothing")
    bad = 1
print(f"  checked {len(supporting)} supporting files across {len(texts)} tracked files")
sys.exit(bad)
PY

note "== 9. The dev-* rename is complete =="
if hits=$(git ls-files \
          | grep -v -e '^\.devtool/' -e '^CHANGELOG\.md$' -e '^scripts/verify\.sh$' \
          | tr '\n' '\0' \
          | xargs -0 grep -n "epic-lifecycle\|epic-designer\|epic-implementation" 2>/dev/null) \
   && [ -n "$hits" ]; then
  printf '%s\n' "$hits" | head -5
  fail "live files still reference the pre-rename skill names"
else
  note "  ok   no live file names epic-lifecycle, epic-designer or epic-implementation"
fi

echo
note "== 10. Orchestrators route to a variant, never the router =="
if hits=$(git ls-files 'skills/dev-lifecycle/*' 'skills/doc-lifecycle/*' \
          | tr '\n' '\0' \
          | xargs -0 grep -n 'd3nexus:brainstorming\|`brainstorming`' 2>/dev/null) \
   && [ -n "$hits" ]; then
  printf '%s\n' "$hits" | head -5
  fail "an orchestrator stage names the brainstorming router instead of a variant"
else
  note "  ok   both orchestrators name a concrete brainstorming variant"
fi

# ==============================================================================
# Sections 11–16: Parallel Python Test Execution + Two-Tier Content-Hash Cache
# ==============================================================================
echo
GIT_DIR_PATH="$(git rev-parse --git-dir 2>/dev/null || echo ".git")"
CACHE_FILE="$GIT_DIR_PATH/.verify_tests_tree_cache"

# Compute exact content hashes (including uncommitted diffs & untracked files):
# - FULL_HASH: all files under skills/, scripts/, hooks/, rules/, tests/, bin/
# - CODE_HASH: only executable/code files (*.py, *.sh, bin/*, hooks/*, *.json)
FULL_HASH=$(
  {
    git rev-parse HEAD:skills HEAD:scripts HEAD:hooks HEAD:rules HEAD:tests HEAD:bin 2>/dev/null
    git diff HEAD -- skills scripts hooks rules tests bin 2>/dev/null
    git ls-files --others --exclude-standard -- skills scripts hooks rules tests bin 2>/dev/null \
      | sort | xargs shasum -a 256 2>/dev/null
  } | shasum -a 256 | awk '{print $1}'
)

CODE_HASH=$(
  {
    git ls-files -s -- 'skills/**.py' 'skills/**.sh' 'scripts/**.py' 'scripts/**.sh' 'hooks/*' 'tests/**.py' 'bin/*' '.agents/quality/*.json' 2>/dev/null
    git diff HEAD -- 'skills/**.py' 'skills/**.sh' 'scripts/**.py' 'scripts/**.sh' 'hooks/*' 'tests/**.py' 'bin/*' '.agents/quality/*.json' 2>/dev/null
    git ls-files --others --exclude-standard -- 'skills/**.py' 'skills/**.sh' 'scripts/**.py' 'scripts/**.sh' 'hooks/*' 'tests/**.py' 'bin/*' 2>/dev/null \
      | sort | xargs shasum -a 256 2>/dev/null
  } | shasum -a 256 | awk '{print $1}'
)

CACHED_LINE="$(cat "$CACHE_FILE" 2>/dev/null || true)"
CACHED_FULL="${CACHED_LINE%%:*}"
CACHED_CODE="${CACHED_LINE#*:}"

RUN_MODE="full"
if [ "$FORCE_FULL" -eq 0 ] && [ -n "$CACHED_LINE" ]; then
  if [ "$CACHED_FULL" = "$FULL_HASH" ]; then
    RUN_MODE="skip"
  elif [ "$CACHED_CODE" = "$CODE_HASH" ]; then
    RUN_MODE="doc_only"
  fi
fi

if [ "$RUN_MODE" = "skip" ]; then
  note "== 11–16. Python test suites (CACHED) =="
  note "  ok   skills/, scripts/, hooks/, rules/, tests/, and bin/ unchanged since last passed run (use --full to force)"
else
  if [ "$RUN_MODE" = "doc_only" ]; then
    note "== 11–16. Running Document Contract test suites (Python code unchanged; use --full for all) =="
  else
    note "== 11–16. Running Python test suites in parallel (Longest-Job-First) =="
  fi
  VerifyRunMode="$RUN_MODE" python3 - <<'PY' || FAILED=1
import concurrent.futures
import os
import pathlib
import subprocess
import sys
import time

run_mode = os.environ.get("VerifyRunMode", "full")

# Tuple format: (section, mode, path_or_label, priority_weight, affects_doc_only)
# Higher priority_weight is scheduled first in the worker pool (Longest-Job-First)
# while output is still printed in canonical SUITES order.
SUITES = [
    # Section 11: Lifecycle document contracts & implementation engines
    ("11", "unittest", "skills/doc_quality_check/resources/scripts/test_check_document.py", 1, True),
    ("11", "script",   "scripts/test_lifecycle_document_contract.py", 2, True),
    ("11", "unittest", "scripts/test_lifecycle_signals.py", 2, True),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_audit_epic.py", 50, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py", 3, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_epic_readiness.py", 45, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_check_task_contract.py", 35, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_result_reports.py", 1, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_run_external_review.py", 100, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_local_review.py", 95, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_run_task_checks.py", 60, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_sync_task_status.py", 40, False),
    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_inter_epic_dependencies.py", 10, False),
    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_concurrent_epic_backlog.py", 10, False),
    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_package_and_revise_epic.py", 30, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_compute_execution_order.py", 5, False),
    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_failure_baseline.py", 5, False),
    ("11", "pytest",   "skills/dev-implementation/resources/scripts/test_replay_and_measure.py", 15, False),
    ("11", "unittest", "skills/dev-implementation/resources/scripts/test_slug_utils.py", 2, False),
    ("11", "unittest", "skills/impact-analysis/resources/scripts/test_check_code_impact.py", 5, False),
    ("11", "unittest", "scripts/test_run_unittest_junit.py", 2, False),
    ("11", "unittest", "scripts/test_verifiable_handoff_text.py", 1, True),
    ("11", "unittest", "scripts/test_verifiable_handoff.py", 15, True),
    ("11", "unittest", "tests/test_lifecycle_runner.py", 20, False),
    # Section 12: Branch integration script
    ("12", "unittest", "skills/finishing-a-development-branch/resources/scripts/test_integrate_branch.py", 80, False),
    # Section 13: Quality provider contracts, schemas, aggregation, and platform capabilities
    ("13", "unittest", "skills/quality_check/resources/scripts/test_validate_quality_contract.py", 1, False),
    ("13", "unittest", "skills/quality_check/resources/scripts/test_aggregate_quality_results.py", 1, False),
    ("13", "unittest", "skills/rust-quality-check/resources/scripts/test_validate_rust_quality.py", 1, False),
    ("13", "unittest", "skills/python-quality-check/resources/scripts/test_validate_python_quality.py", 1, False),
    ("13", "unittest", "skills/flutter-quality-check/resources/scripts/test_validate_flutter_quality.py", 1, False),
    ("13", "unittest", "skills/android-quality-check/resources/scripts/test_validate_android_quality.py", 1, False),
    ("13", "unittest", "skills/ios-quality-check/resources/scripts/test_validate_ios_quality.py", 1, False),
    ("13", "unittest", "skills/web-quality-check/resources/scripts/test_validate_web_quality.py", 1, False),
    ("13", "pytest",   "tests/test_web_quality_provider.py", 5, False),
    ("13", "pytest",   "tests/test_audit_ui_state_and_styles.py", 2, False),
    ("13", "unittest", "skills/setup_quality_check/resources/scripts/test_scaffold_quality_manifest.py", 1, False),
    ("13", "unittest", "skills/quality_check/resources/scripts/test_quality_provider_acceptance.py", 20, True),
    # 14. Shared contracts CLI engine is enforced
    ("14", "unittest", "skills/setup-shared-contracts/resources/scripts/test_setup_contracts.py", 15, False),
    ("14", "unittest", "skills/sync-shared-contracts/resources/scripts/test_sync_contracts.py", 25, False),
    # 15. Context memory management CLI and Tri-Role governance are enforced
    ("15", "unittest", "scripts/test_resume_context.py", 25, False),
    # 16. Session refresh CLI engine and isolation contracts are enforced
    ("16", "unittest", "skills/refresh-session/resources/scripts/test_refresh_session.py", 2, False),
    # 17. Quota Dashboard & Kiro CLI provider tests
    ("17", "unittest", "tests/test_kiro_quota.py", 2, True),
    ("17", "unittest", "tests/test_agy_quota.py", 2, True),
]

active_suites = [
    (idx, s)
    for idx, s in enumerate(SUITES)
    if pathlib.Path(s[2]).exists() and (run_mode == "full" or s[4])
]

# Schedule heaviest suites first (Longest-Job-First)
scheduled_suites = sorted(active_suites, key=lambda item: -item[1][3])

def run_suite(indexed_item):
    orig_idx, (sec, mode, path, _prio, _doc) = indexed_item
    t0 = time.monotonic()
    if mode == "unittest":
        cmd = [sys.executable, "-m", "unittest", path]
    elif mode == "pytest":
        cmd = [sys.executable, "-m", "pytest", path, "-q"]
    else:
        cmd = [sys.executable, path]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.monotonic() - t0
    return orig_idx, sec, path, proc.returncode, elapsed, proc.stdout, proc.stderr

t_start = time.monotonic()
max_workers = min(len(scheduled_suites), (os.cpu_count() or 4))
raw_results = []
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
    futures = [pool.submit(run_suite, item) for item in scheduled_suites]
    for fut in concurrent.futures.as_completed(futures):
        raw_results.append(fut.result())

# Sort back to canonical Section 11 -> 16 order for deterministic output
results = sorted(raw_results, key=lambda r: r[0])

failed = 0
for _idx, sec, path, rc, elapsed, out, err in results:
    status = "ok  " if rc == 0 else "FAIL"
    print(f"  {status} [§{sec}] {path} ({elapsed:.2f}s)")
    if rc != 0:
        failed = 1
        if out.strip():
            print(out.rstrip())
        if err.strip():
            print(err.rstrip())

total_elapsed = time.monotonic() - t_start
print(f"\n  Ran {len(results)} test suites in {total_elapsed:.2f}s across {max_workers} workers.")
sys.exit(failed)
PY

  if [ "$FAILED" -eq 0 ] && [ -n "$GIT_DIR_PATH" ]; then
    printf '%s:%s\n' "$FULL_HASH" "$CODE_HASH" > "$CACHE_FILE"
  fi
fi

echo
if [ "$FAILED" -eq 0 ]; then
  echo "PASS — safe to publish"
else
  echo "FAILED — fix the above before publishing"
fi
exit "$FAILED"
