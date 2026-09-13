#!/bin/bash

# Ensure we are on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
  echo "This script currently supports macOS only."
  exit 1
fi

PROJECT_ROOT=$(pwd)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_KEYBINDINGS="$SCRIPT_DIR/resources/keybindings.json"

if [[ ! -f "$SOURCE_KEYBINDINGS" ]]; then
  echo "Error: Source keybindings file not found at $SOURCE_KEYBINDINGS"
  exit 1
fi

# List of potential IDE paths
IDE_PATHS=(
  "$HOME/Library/Application Support/Code/User/keybindings.json"
  "$HOME/Library/Application Support/Code - Insiders/User/keybindings.json"
  "$HOME/Library/Application Support/Cursor/User/keybindings.json"
  "$HOME/Library/Application Support/Windsurf/User/keybindings.json"
  "$HOME/Library/Application Support/VSCodium/User/keybindings.json"
  "$HOME/Library/Application Support/Antigravity/User/keybindings.json"
)

PATHS_FOUND=0

for TARGET_PATH in "${IDE_PATHS[@]}"; do
  TARGET_DIR=$(dirname "$TARGET_PATH")
  
  if [[ -d "$TARGET_DIR" ]]; then
    PATHS_FOUND=$((PATHS_FOUND + 1))
    echo "Found IDE configuration at: $TARGET_PATH"
    
    # Backup existing file if it exists
    if [[ -f "$TARGET_PATH" ]]; then
      cp "$TARGET_PATH" "$TARGET_PATH.bak"
      echo "  Backed up to $TARGET_PATH.bak"
    else
      echo "[]" > "$TARGET_PATH"
      echo "  Created new empty keybindings file."
    fi

    # Merge using python3
    python3 -c "
import json
import sys
import os

try:
    with open('$SOURCE_KEYBINDINGS', 'r') as f:
        # Strip comments manually since standard json lib doesn't support them
        content = f.read()
        lines = [l for l in content.splitlines() if not l.strip().startswith('//')]
        source_data = json.loads('\n'.join(lines))

    target_path = '$TARGET_PATH'
    if os.path.exists(target_path):
        with open(target_path, 'r') as f:
            content = f.read()
            lines = [l for l in content.splitlines() if not l.strip().startswith('//')]
            target_data = json.loads('\n'.join(lines))
    else:
        target_data = []

    added_count = 0
    for new_binding in source_data:
        exists = False
        for existing in target_data:
            if (existing.get('command') == new_binding.get('command') and 
                existing.get('key') == new_binding.get('key')):
                # Check when clause
                new_when = new_binding.get('when')
                existing_when = existing.get('when')
                if new_when == existing_when:
                    exists = True
                    break
        
        if not exists:
            target_data.append(new_binding)
            added_count += 1

    if added_count > 0:
        with open(target_path, 'w') as f:
            json.dump(target_data, f, indent=4)
        print(f'  Successfully added {added_count} keybindings.')
    else:
        print('  All keybindings already exist.')

except Exception as e:
    print(f'  Error merging keybindings: {e}')
    sys.exit(1)
"
  fi
done

if [[ $PATHS_FOUND -eq 0 ]]; then
  echo "No compatible IDE configurations found in standard paths."
fi
