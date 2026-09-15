#!/usr/bin/env bash
# Publish edited skills so installed machines pick them up.
#
#   scripts/release.sh            # bump patch (1.0.1 -> 1.0.2)
#   scripts/release.sh 1.1.0      # set an explicit version
#
# A version bump is REQUIRED: `claude plugin update` compares the version in
# plugin.json and does nothing when it is unchanged, leaving every machine on the
# old cached copy.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

CURRENT=$(python3 -c "import json;print(json.load(open('.claude-plugin/plugin.json'))['version'])")

if [ $# -ge 1 ]; then
  NEW="$1"
else
  NEW=$(python3 -c "
major, minor, patch = '$CURRENT'.split('.')
print(f'{major}.{minor}.{int(patch)+1}')")
fi

echo "== 1. Verify =="
bash scripts/verify.sh

echo
echo "== 2. Bump $CURRENT -> $NEW =="
python3 - "$NEW" <<'PY'
import json, pathlib, sys
new = sys.argv[1]
p = pathlib.Path(".claude-plugin/plugin.json"); d = json.loads(p.read_text())
d["version"] = new; p.write_text(json.dumps(d, indent=2) + "\n")
p = pathlib.Path(".claude-plugin/marketplace.json"); d = json.loads(p.read_text())
d["plugins"][0]["version"] = new; p.write_text(json.dumps(d, indent=2) + "\n")
print(f"  plugin.json and marketplace.json -> {new}")
PY

echo
echo "== 3. Commit and push =="
git add -A
if git diff --cached --quiet; then
  echo "  nothing to commit"
else
  git commit -q -m "[RELEASE] Release $NEW"
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

