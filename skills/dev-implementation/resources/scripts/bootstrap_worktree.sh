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
SECURE_CONFIG_STATUS=0
SECURE_CONFIG_OUTPUT="$(cd "$WORKTREE_PATH" && sh .agents/skills/copy_secure_configurations/resources/scripts/copy_secure_files.sh 2>&1)" || SECURE_CONFIG_STATUS=$?
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
