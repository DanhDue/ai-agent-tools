#!/usr/bin/env bash
# Publish edited skills so installed machines pick them up.
#
#   scripts/release.sh            # bump patch (1.0.1 -> 1.0.2)
#   scripts/release.sh 1.1.0      # set an explicit version
#
# Add a dated CHANGELOG.md entry for the target version before running this script.
# All runtime manifests share the version used by installed plugin caches.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

CURRENT=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")

if [ $# -ge 1 ]; then
  NEW="$1"
else
  NEW=$(python3 -c 'import sys; major, minor, patch = sys.argv[1].split("."); print(f"{major}.{minor}.{int(patch)+1}")' "$CURRENT")
fi

python3 - "$CURRENT" "$NEW" <<'PY'
import pathlib, re, sys
current, new = sys.argv[1:]
if not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', new):
    sys.exit("error: release version must be MAJOR.MINOR.PATCH")
if tuple(map(int, new.split('.'))) <= tuple(map(int, current.split('.'))):
    sys.exit(f"error: release version must be newer than {current}")
notes = pathlib.Path('CHANGELOG.md').read_text()
if not re.search(r'^## ' + re.escape(new) + r' — \d{4}-\d{2}-\d{2}\n\n\S', notes, re.M):
    sys.exit(f"error: add dated release notes for {new} to CHANGELOG.md first")
PY

if [ "$(git branch --show-current)" != main ]; then
  echo "error: release from main so the verified commit is the one pushed" >&2
  exit 1
fi

echo "== 1. Verify =="
bash scripts/verify.sh

echo
echo "== 2. Bump $CURRENT -> $NEW =="
python3 - "$NEW" <<'PY'
import json, pathlib, sys
new = sys.argv[1]
for filename in ("plugin.json", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
    p = pathlib.Path(filename); d = json.loads(p.read_text())
    d["version"] = new; p.write_text(json.dumps(d, indent=2) + "\n")
p = pathlib.Path(".claude-plugin/marketplace.json"); d = json.loads(p.read_text())
for plugin in d["plugins"]:
    if plugin["name"] == "d3nexus":
        plugin["version"] = new
p.write_text(json.dumps(d, indent=2) + "\n")
print(f"  all plugin manifests and Claude marketplace -> {new}")
PY
bash scripts/verify.sh

echo
echo "== 3. Commit and push =="
git add -A
if git diff --cached --quiet; then
  echo "  nothing to commit"
else
  git commit -q -m "[RELEASE] Release $NEW" -m "- Publish the changes documented in CHANGELOG.md
- Synchronize plugin manifests at $NEW"
  echo "  committed Release $NEW"
fi
git push -q origin main
echo "  pushed"

echo
echo "== 4. Refresh this machine =="
if command -v claude >/dev/null 2>&1; then
  claude plugin marketplace update danhdue-agent-tools 2>/dev/null || true
  claude plugin update d3nexus@danhdue-agent-tools 2>/dev/null || true
fi

if [ -d "$HOME/.gemini/config/plugins/d3nexus/.git" ]; then
  echo "  pulling updates into ~/.gemini/config/plugins/d3nexus"
  git -C "$HOME/.gemini/config/plugins/d3nexus" pull -q origin main || true
fi

echo
echo "Done. Restart the session (or reload the IDE window) to load $NEW."
echo "On any other machine, run only step 4."
echo "For Codex, refresh the registered marketplace and reinstall:"
echo "  codex plugin marketplace upgrade danhdue-agent-tools"
echo "  codex plugin add d3nexus@danhdue-agent-tools"
