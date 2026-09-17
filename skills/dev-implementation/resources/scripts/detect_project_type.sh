#!/usr/bin/env bash
# detect_project_type.sh
# Detects whether a repository is a Flutter, Android Native, or iOS Native project.
#
# Usage:
#   detect_project_type.sh [path_to_project_root]
#
# Output:
#   "flutter", "android", "ios", or "unknown"
# Exit code:
#   0 if recognized ("flutter", "android", "ios"), 1 if "unknown"

set -euo pipefail

TARGET_DIR="${1:-.}"

# Resolve absolute path
TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

# 1. Flutter Project Check
if [ -f "$TARGET_DIR/pubspec.yaml" ] || [ -f "$TARGET_DIR/melos.yaml" ]; then
  echo "flutter"
  exit 0
fi

# Guard against subdirectories of a Flutter project
if [ -f "$TARGET_DIR/../pubspec.yaml" ]; then
  echo "unknown"
  exit 1
fi

# 2. iOS Native Project Check (Tuist / Xcode)
if [ -f "$TARGET_DIR/Project.swift" ] || [ -f "$TARGET_DIR/Workspace.swift" ] || [ -f "$TARGET_DIR/Tuist.swift" ]; then
  echo "ios"
  exit 0
fi

# Check for Xcode project/workspace bundles at the root
shopt -s nullglob
xcode_projects=("$TARGET_DIR"/*.xcodeproj "$TARGET_DIR"/*.xcworkspace)
shopt -u nullglob

if [ ${#xcode_projects[@]} -gt 0 ]; then
  echo "ios"
  exit 0
fi

# 3. Android Native Project Check (Gradle)
if [ -f "$TARGET_DIR/settings.gradle.kts" ] || [ -f "$TARGET_DIR/settings.gradle" ] || [ -f "$TARGET_DIR/build.gradle.kts" ]; then
  echo "android"
  exit 0
fi

echo "unknown"
exit 1
