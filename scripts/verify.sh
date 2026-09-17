#!/usr/bin/env bash
# Pre-release checks for the agent kit. Run before publishing — a broken skill
# propagates to every project on every machine that has the plugin installed.
set -uo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$KIT_DIR"
FAILED=0
note() { printf '%s\n' "$1"; }
fail() { printf '  FAIL %s\n' "$1"; FAILED=1; }

note "== 1. JSON manifests parse =="
for f in plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json .agents/plugins/marketplace.json; do
  if python3 -c "import json,sys;json.load(open('$f'))" 2>/dev/null; then
    note "  ok   $f"
  else
    fail "$f is not valid JSON"
  fi
done

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
        + [pathlib.Path("README.md"), pathlib.Path("CLAUDE.md")]
targets = sorted(set(targets))
def strip_fences(s):
    # Link syntax also occurs inside code samples and inline code spans that document
    # a format. Only links in prose are real links.
    s = re.sub(r'```.*?```', '', s, flags=re.S)
    return re.sub(r'`[^`\n]*`', '', s)

for p in targets:
    if not p.exists():
        continue
    for link in re.findall(r'\]\(([^)#][^)]*)\)', strip_fences(p.read_text())):
        if link.startswith(("http://", "https://", "mailto:")) or "<" in link:
            continue  # external, or an illustrative placeholder
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
for p in sorted(pathlib.Path("skills").glob("*/SKILL.md")):
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
# Antigravity rejects a rules/*.md without frontmatter outright:
#   "Failed to parse plugin rule file ...: invalid frontmatter format"
# and the rule then silently never loads.
for f in rules/*.md; do
  if head -1 "$f" | grep -qx -- '---'; then
    note "  ok   $f"
  else
    fail "$f has no frontmatter — Antigravity will refuse to load it"
  fi
done

note "== 6. Session-start hook emits valid JSON for both runtimes =="
hook_case() {  # <label> <expect: inject|silent> <env> <payload>
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
# skills/brainstorming/spec-document-reviewer-prompt.md was 49 lines of working reviewer prompt
# that nothing in the repository referenced, for its entire life. Nothing prevented that from
# recurring. SKILL.md is exempt: it is a skill's entry point by definition, and without the
# exemption this check fires on every skill in the kit.
python3 - <<'PY' || FAILED=1
import pathlib, sys
root = pathlib.Path(".")
# The rule is that a skill's own content must be reachable from the skill. Three things are
# not that content: binary assets, legal files, and the repo furniture a vendored skill brings
# with it (CI workflows and other dotfile directories, which their own tooling invokes).
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf"}
LEGAL_PREFIXES = ("LICENSE", "COPYING", "NOTICE")
def is_skill_content(p):
    if p.name == "SKILL.md" or "__pycache__" in p.parts:
        return False
    if p.suffix.lower() in ASSET_SUFFIXES:
        return False
    if p.name.upper().startswith(LEGAL_PREFIXES):
        return False
    return not any(part.startswith(".") for part in p.parts)

supporting = [p for p in root.glob("skills/*/**/*") if p.is_file() and is_skill_content(p)]
corpus = [p for p in root.rglob("*")
          if p.is_file() and ".git/" not in str(p) and "__pycache__" not in p.parts
          and p.suffix in {".md", ".py", ".sh", ".json", ".yaml", ".yml", ""}]
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
print(f"  checked {len(supporting)} supporting files")
sys.exit(bad)
PY

note "== 9. The dev-* rename is complete =="
# The old names must survive only where they are history: archived epic records under .devtool/
# and the CHANGELOG entries that describe the rename itself.
# grep -v below drops this file: the check's own pattern necessarily contains the old names.
if hits=$(grep -rn "epic-lifecycle\|epic-designer\|epic-implementation" . \
          --exclude-dir=.git --exclude-dir=.devtool --exclude-dir=__pycache__ \
          --exclude-dir=.worktrees --exclude=CHANGELOG.md 2>/dev/null \
          | grep -v "^\./scripts/verify\.sh:") && [ -n "$hits" ]; then
  printf '%s\n' "$hits" | head -5
  fail "live files still reference the pre-rename skill names"
else
  note "  ok   no live file names epic-lifecycle, epic-designer or epic-implementation"
fi

echo
if [ "$FAILED" -eq 0 ]; then
  echo "PASS — safe to publish"
else
  echo "FAILED — fix the above before publishing"
fi
exit "$FAILED"
