#!/usr/bin/env bash
# Scaffold a project for Codex, Antigravity, and Claude Code.
# Usage: scripts/init-project.sh /path/to/project "Project Name"
set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${1:?usage: init-project.sh <project-path> [project-name]}"
NAME="${2:-$(basename "$PROJECT")}"

[ -d "$PROJECT" ] || { echo "error: no such directory: $PROJECT" >&2; exit 1; }
cd "$PROJECT"

# 1. AGENTS.md — the shared entry point (Claude Code via the CLAUDE.md symlink).
if [ -e AGENTS.md ]; then
  echo "skip   AGENTS.md already exists"
else
  sed "s/{{PROJECT_NAME}}/$NAME/" "$KIT_DIR/templates/AGENTS.md" > AGENTS.md
  echo "create AGENTS.md (fill in the {{...}} placeholders)"
fi

# 2. CLAUDE.md -> AGENTS.md, so the entry points cannot drift.
if [ -e CLAUDE.md ] && [ ! -L CLAUDE.md ]; then
  echo "WARN   CLAUDE.md exists as a real file — merge it into AGENTS.md, then re-run"
elif [ -L CLAUDE.md ]; then
  echo "skip   CLAUDE.md symlink already present"
else
  ln -s AGENTS.md CLAUDE.md
  echo "create CLAUDE.md -> AGENTS.md"
fi

# 3. Editor guardrails: printed, not merged — settings.json usually holds project-specific paths.
echo
echo "next   merge these keys into .vscode/settings.json:"
sed 's/^/         /' "$KIT_DIR/templates/vscode-settings.fragment.json"

echo
echo "done   skills and rules come from the installed d3nexus plugin."
echo "       Codex       : codex plugin marketplace add DanhDue/ai-agent-tools"
echo "                     codex plugin add d3nexus@danhdue-agent-tools"
echo "       Claude Code : /plugin marketplace add DanhDue/ai-agent-tools"
echo "       Antigravity : clone into ~/.gemini/config/plugins/d3nexus"
