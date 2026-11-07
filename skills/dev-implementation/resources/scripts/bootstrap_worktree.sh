#!/usr/bin/env bash
# Bootstrap a freshly created git worktree so it can actually build/run
# this project. Run this after using-git-worktrees has created the
# worktree. It can be run from ANY checkout of this repo (main checkout
# or any worktree) -- REPO_ROOT below always resolves to the MAIN
# checkout via the shared git common dir, never to whichever worktree
# happens to be the current directory.
#
# This project uses Swift Package Manager, not CocoaPods, so there is no
# `pod install` step -- SPM resolves automatically on the first iOS build.
#
# Usage: bootstrap_worktree.sh <worktree_path>
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <worktree_path>" >&2
  exit 1
fi

WORKTREE_PATH="$1"
# --git-common-dir points at the MAIN checkout's .git directory from every
# worktree, so its parent is the main checkout. --show-toplevel would give
# whichever worktree is the current directory instead -- and since
# using-git-worktrees ends by cd-ing into the NEW worktree, that is the
# common case and it has no secureFiles/ yet.
REPO_ROOT="$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")"

if [ ! -d "$WORKTREE_PATH" ]; then
  echo "Worktree path does not exist: $WORKTREE_PATH" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
WORKTREE_ABS="$(cd "$WORKTREE_PATH" && pwd)"
WORKTREE_NAME="$(basename "$WORKTREE_ABS")"

# 0. Synchronize IDE window title & persistent repo bar colors (.vscode/settings.json)
# and copy gitignored local environment files (.env, .env.local) if present in REPO_ROOT.
if [ -f "$REPO_ROOT/.vscode/settings.json" ] && [ ! -f "$WORKTREE_ABS/.vscode/settings.json" ]; then
  mkdir -p "$WORKTREE_ABS/.vscode"
  cp "$REPO_ROOT/.vscode/settings.json" "$WORKTREE_ABS/.vscode/settings.json"
fi
if [ -f "$KIT_ROOT/scripts/resume_context.py" ]; then
  python3 "$KIT_ROOT/scripts/resume_context.py" \
    --workspace-root "$WORKTREE_ABS" \
    --sync-title \
    --epic "$WORKTREE_NAME" >/dev/null 2>&1 || true
elif command -v d3nexus &>/dev/null; then
  d3nexus resume-context \
    --workspace-root "$WORKTREE_ABS" \
    --sync-title \
    --epic "$WORKTREE_NAME" >/dev/null 2>&1 || true
fi

for env_file in .env .env.local .env.development; do
  if [ -f "$REPO_ROOT/$env_file" ] && [ ! -f "$WORKTREE_ABS/$env_file" ]; then
    echo "Copying gitignored $env_file from main checkout into worktree..."
    cp "$REPO_ROOT/$env_file" "$WORKTREE_ABS/$env_file"
  fi
done

BOOTSTRAPPED=0

if [ -f "$WORKTREE_PATH/pyproject.toml" ] || [ -f "$WORKTREE_PATH/requirements.txt" ]; then
  echo "Detected Python project in worktree..."
  EXECUTED_CUSTOM_BOOTSTRAP=0
  if [ -f "$WORKTREE_PATH/.agents/quality/python-quality.json" ]; then
    python3 -c "
import json, subprocess, sys
manifest_path = '$WORKTREE_PATH/.agents/quality/python-quality.json'
try:
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    bootstrap = data.get('bootstrap')
    if bootstrap is not None:
        if not isinstance(bootstrap, list) or len(bootstrap) == 0:
            print('Error: bootstrap must be a non-empty list of command arrays', file=sys.stderr)
            sys.exit(2)
        for cmd in bootstrap:
            if not isinstance(cmd, list) or not all(isinstance(x, str) for x in cmd):
                print(f'Error: invalid bootstrap command format: {cmd}', file=sys.stderr)
                sys.exit(2)
            print(f'Running configured bootstrap command: {cmd}')
            subprocess.run(cmd, cwd='$WORKTREE_PATH', check=True)
        sys.exit(0)
    sys.exit(1)
except subprocess.CalledProcessError as err:
    print(f'Error: configured bootstrap command failed: {err}', file=sys.stderr)
    sys.exit(2)
except Exception:
    sys.exit(1)
"
    STATUS=$?
    if [ "$STATUS" -eq 0 ]; then
      EXECUTED_CUSTOM_BOOTSTRAP=1
    elif [ "$STATUS" -eq 2 ]; then
      echo "Configured bootstrap failed. Aborting worktree bootstrap." >&2
      exit 1
    fi
  fi

  if [ "$EXECUTED_CUSTOM_BOOTSTRAP" -eq 0 ]; then
    if command -v uv &>/dev/null; then
      echo "Running uv sync (fast dependency sync)..."
      (cd "$WORKTREE_PATH" && uv sync)
    elif command -v poetry &>/dev/null && [ -f "$WORKTREE_PATH/poetry.lock" ]; then
      echo "Running poetry install..."
      (cd "$WORKTREE_PATH" && poetry install)
    elif [ -f "$WORKTREE_PATH/requirements.txt" ]; then
      echo "Running pip install -r requirements.txt..."
      (cd "$WORKTREE_PATH" && pip install -r requirements.txt)
    fi
  fi
  BOOTSTRAPPED=1
fi

if [ -f "$WORKTREE_PATH/Cargo.toml" ] && [ ! -f "$WORKTREE_PATH/pubspec.yaml" ]; then
  echo "Detected Rust project in worktree..."
  echo "Running cargo check --workspace (warm up compilation cache)..."
  (cd "$WORKTREE_PATH" && cargo check --workspace)
  BOOTSTRAPPED=1
fi

if [ -f "$WORKTREE_PATH/package.json" ] && [ ! -f "$WORKTREE_PATH/pubspec.yaml" ]; then
  echo "Detected Web project in worktree..."
  if command -v pnpm &>/dev/null && [ -f "$WORKTREE_PATH/pnpm-lock.yaml" ]; then
    echo "Running pnpm install..."
    (cd "$WORKTREE_PATH" && pnpm install)
  elif command -v npm &>/dev/null; then
    echo "Running npm install..."
    (cd "$WORKTREE_PATH" && npm install)
  fi
  BOOTSTRAPPED=1
fi

has_mobile_markers() {
  [ -f "$WORKTREE_PATH/pubspec.yaml" ] || [ -f "$WORKTREE_PATH/melos.yaml" ] || \
  [ -f "$WORKTREE_PATH/Project.swift" ] || [ -f "$WORKTREE_PATH/Workspace.swift" ] || \
  [ -f "$WORKTREE_PATH/Tuist.swift" ] || [ -f "$WORKTREE_PATH/settings.gradle.kts" ] || \
  [ -f "$WORKTREE_PATH/settings.gradle" ] || [ -f "$WORKTREE_PATH/build.gradle.kts" ]
}

if [ "$BOOTSTRAPPED" -eq 1 ] && ! has_mobile_markers; then
  echo "Worktree bootstrap complete at $WORKTREE_PATH"
  exit 0
fi

if [ ! -d "$REPO_ROOT/secureFiles" ]; then
  echo "secureFiles/ not found at $REPO_ROOT/secureFiles" >&2
  echo "secureFiles/ is gitignored, so it exists only where it was populated by hand --" >&2
  echo "no worktree ever gets it from 'git worktree add'. Either the main checkout at" >&2
  echo "$REPO_ROOT never had it set up, or this is not the checkout you expected." >&2
  echo "Populate $REPO_ROOT/secureFiles (the check_secure_files skill documents what it" >&2
  echo "must contain), then re-run this script." >&2
  exit 1
fi

echo "Copying secureFiles/ into worktree (untracked, so 'git worktree add' does not bring it along)..."
mkdir -p "$WORKTREE_PATH/secureFiles"
cp -R "$REPO_ROOT/secureFiles/." "$WORKTREE_PATH/secureFiles/"

echo "Placing platform config via copy_secure_configurations..."
# copy_secure_configurations exits 0 even when files are missing -- it only
# prints "⚠️  Missing ..." per file. Capture its output and fail loudly on
# any warning, otherwise this script would report success for a worktree
# that cannot actually build.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COPY_SECURE_SCRIPT=""
if [ -f "$WORKTREE_PATH/.agents/skills/copy_secure_configurations/resources/scripts/copy_secure_files.sh" ]; then
  COPY_SECURE_SCRIPT="$WORKTREE_PATH/.agents/skills/copy_secure_configurations/resources/scripts/copy_secure_files.sh"
elif [ -f "$SCRIPT_DIR/../../../copy_secure_configurations/resources/scripts/copy_secure_files.sh" ]; then
  COPY_SECURE_SCRIPT="$SCRIPT_DIR/../../../copy_secure_configurations/resources/scripts/copy_secure_files.sh"
else
  echo "copy_secure_files.sh not found in worktree or plugin directory" >&2
  exit 1
fi

SECURE_CONFIG_STATUS=0
SECURE_CONFIG_OUTPUT="$(cd "$WORKTREE_PATH" && sh "$COPY_SECURE_SCRIPT" 2>&1)" || SECURE_CONFIG_STATUS=$?
echo "$SECURE_CONFIG_OUTPUT"
if [ "$SECURE_CONFIG_STATUS" -ne 0 ]; then
  echo "copy_secure_configurations failed (exit $SECURE_CONFIG_STATUS)." >&2
  exit 1
fi
if grep -q "⚠️" <<<"$SECURE_CONFIG_OUTPUT"; then
  echo "" >&2
  echo "copy_secure_configurations reported missing files (⚠️ above)." >&2
  echo "The worktree would be only partially configured and builds for the affected" >&2
  echo "flavors would fail. Fix $REPO_ROOT/secureFiles, delete" >&2
  echo "$WORKTREE_PATH/secureFiles, and re-run this script." >&2
  exit 1
fi

echo "Running melos bootstrap (fast: ~/.pub-cache is global and already warm)..."
(cd "$WORKTREE_PATH" && melos bootstrap)

echo "Worktree bootstrap complete at $WORKTREE_PATH"
echo "Note: no 'pod install' needed (Swift Package Manager, not CocoaPods)."
echo "The first iOS build here will resolve SPM packages automatically (one-time cost)."
