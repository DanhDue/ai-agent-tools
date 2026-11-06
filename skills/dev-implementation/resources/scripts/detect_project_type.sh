#!/usr/bin/env bash
# detect_project_type.sh
# Detects whether a repository is a Flutter, Android Native, iOS Native, Web, Python, or Rust project.
#
# Usage:
#   detect_project_type.sh [--all] [path_to_project_root]
#
# Output:
#   "flutter", "android", "ios", "web", "python", "rust", or "unknown"
#   With --all: space-separated list of all detected platforms (e.g. "python web")
# Exit code:
#   0 if recognized, 1 if "unknown"

set -euo pipefail

SHOW_ALL=0
TARGET_DIR=""

for arg in "$@"; do
  if [ "$arg" = "--all" ]; then
    SHOW_ALL=1
  elif [ -z "$TARGET_DIR" ]; then
    TARGET_DIR="$arg"
  fi
done

TARGET_DIR="${TARGET_DIR:-.}"
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# Helper to check for Xcode bundles
shopt -s nullglob
xcode_projects=("$TARGET_DIR"/*.xcodeproj "$TARGET_DIR"/*.xcworkspace)
shopt -u nullglob

is_ios() {
  [ -f "$TARGET_DIR/Project.swift" ] || [ -f "$TARGET_DIR/Workspace.swift" ] || \
  [ -f "$TARGET_DIR/Tuist.swift" ] || [ ${#xcode_projects[@]} -gt 0 ]
}

is_flutter() {
  [ -f "$TARGET_DIR/pubspec.yaml" ] || [ -f "$TARGET_DIR/melos.yaml" ]
}

is_android() {
  [ -f "$TARGET_DIR/settings.gradle.kts" ] || [ -f "$TARGET_DIR/settings.gradle" ] || \
  [ -f "$TARGET_DIR/build.gradle.kts" ]
}

is_python() {
  [ -f "$TARGET_DIR/pyproject.toml" ] || [ -f "$TARGET_DIR/setup.py" ] || \
  [ -f "$TARGET_DIR/Pipfile" ] || [ -f "$TARGET_DIR/requirements.txt" ]
}

is_web() {
  if [ ! -f "$TARGET_DIR/package.json" ]; then
    return 1
  fi
  if [ "$SHOW_ALL" -eq 1 ]; then
    return 0
  fi
  [ -f "$TARGET_DIR/astro.config.mjs" ] || [ -f "$TARGET_DIR/astro.config.ts" ] || \
  [ -f "$TARGET_DIR/vite.config.ts" ] || [ -f "$TARGET_DIR/vite.config.js" ] || \
  [ -f "$TARGET_DIR/next.config.js" ] || [ -f "$TARGET_DIR/next.config.mjs" ] || [ -f "$TARGET_DIR/next.config.ts" ] || \
  [ -f "$TARGET_DIR/nuxt.config.ts" ] || [ -f "$TARGET_DIR/svelte.config.js" ] || \
  [ -d "$TARGET_DIR/apps/learning-web" ] || [ -d "$TARGET_DIR/apps/web" ] || \
  [ -d "$TARGET_DIR/tests/js" ]
}

is_rust() {
  [ -f "$TARGET_DIR/Cargo.toml" ]
}

if [ "$SHOW_ALL" -eq 1 ]; then
  DETECTED=()
  if is_flutter; then DETECTED+=("flutter"); fi
  if is_ios; then DETECTED+=("ios"); fi
  if is_android; then DETECTED+=("android"); fi
  if is_python; then DETECTED+=("python"); fi
  if is_web; then DETECTED+=("web"); fi
  if is_rust; then DETECTED+=("rust"); fi

  if [ ${#DETECTED[@]} -gt 0 ]; then
    echo "${DETECTED[*]}"
    exit 0
  fi
  echo "unknown"
  exit 1
fi

# Single-platform detection (preserved order: flutter, ios, android, web, python, rust)
if is_flutter; then
  echo "flutter"
  exit 0
fi

# Guard against subdirectories of a Flutter project
if [ -f "$TARGET_DIR/../pubspec.yaml" ]; then
  echo "unknown"
  exit 1
fi

if is_ios; then
  echo "ios"
  exit 0
fi

if is_android; then
  echo "android"
  exit 0
fi

if is_web; then
  echo "web"
  exit 0
fi

if is_python; then
  echo "python"
  exit 0
fi

if is_rust; then
  echo "rust"
  exit 0
fi

echo "unknown"
exit 1
