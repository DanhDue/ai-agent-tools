#!/bin/bash

# Setup keybindings for IDE user profiles (e.g., ~/antigravity-profile-2)

# Function to detect user-data-dir from running IDE processes
detect_user_data_dir() {
  echo "🔍 Detecting IDE user data directory from running processes..."
  echo ""
  
  local found_dirs=()
  
  # Check for Antigravity
  local antigravity_dirs=$(ps aux | grep "antigravity" | grep "user-data-dir" | grep -v grep | sed -n 's/.*--user-data-dir=\([^ ]*\).*/\1/p' | sort -u)
  if [ -n "$antigravity_dirs" ]; then
    while IFS= read -r dir; do
      found_dirs+=("$dir (Antigravity)")
    done <<< "$antigravity_dirs"
  fi
  
  # Check for VS Code
  local vscode_dirs=$(ps aux | grep "Visual Studio Code" | grep "user-data-dir" | grep -v grep | sed -n 's/.*--user-data-dir=\([^ ]*\).*/\1/p' | sort -u)
  if [ -n "$vscode_dirs" ]; then
    while IFS= read -r dir; do
      found_dirs+=("$dir (VS Code)")
    done <<< "$vscode_dirs"
  fi
  
  # Check for Cursor
  local cursor_dirs=$(ps aux | grep "Cursor" | grep "user-data-dir" | grep -v grep | sed -n 's/.*--user-data-dir=\([^ ]*\).*/\1/p' | sort -u)
  if [ -n "$cursor_dirs" ]; then
    while IFS= read -r dir; do
      found_dirs+=("$dir (Cursor)")
    done <<< "$cursor_dirs"
  fi
  
  # Check for Windsurf
  local windsurf_dirs=$(ps aux | grep "Windsurf" | grep "user-data-dir" | grep -v grep | sed -n 's/.*--user-data-dir=\([^ ]*\).*/\1/p' | sort -u)
  if [ -n "$windsurf_dirs" ]; then
    while IFS= read -r dir; do
      found_dirs+=("$dir (Windsurf)")
    done <<< "$windsurf_dirs"
  fi
  
  if [ ${#found_dirs[@]} -eq 0 ]; then
    echo "❌ No IDE processes found with --user-data-dir argument."
    echo ""
    return 1
  fi
  
  echo "✅ Found ${#found_dirs[@]} IDE profile(s):"
  echo ""
  for i in "${!found_dirs[@]}"; do
    echo "  $((i+1)). ${found_dirs[$i]}"
  done
  echo ""
  
  if [ ${#found_dirs[@]} -eq 1 ]; then
    # Extract just the directory path (remove IDE name)
    PROFILE_DIR="${found_dirs[0]%% (*}"
    echo "📍 Auto-selected: $PROFILE_DIR"
    echo ""
    return 0
  else
    echo "Multiple profiles detected. Please specify which one to use."
    echo ""
    return 1
  fi
}

# Check if profile path is provided
if [ -z "$1" ]; then
  # Try to auto-detect
  if ! detect_user_data_dir; then
    echo "Error: Profile directory path required."
    echo ""
    echo "Usage: bash setup.sh <profile-directory>"
    echo "Example: bash setup.sh ~/antigravity-profile-2"
    echo ""
    echo "💡 Tip: Launch your IDE with --user-data-dir first, then run this script."
    echo "   Example: antigravity --user-data-dir ~/antigravity-profile-2"
    exit 1
  fi
else
  PROFILE_DIR="$1"
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SOURCE_KEYBINDINGS="$SCRIPT_DIR/resources/keybindings.json"

# Expand tilde to home directory
PROFILE_DIR="${PROFILE_DIR/#\~/$HOME}"

# Validate source keybindings file
if [[ ! -f "$SOURCE_KEYBINDINGS" ]]; then
  echo "Error: Source keybindings file not found at $SOURCE_KEYBINDINGS"
  exit 1
fi

# Validate profile directory exists
if [[ ! -d "$PROFILE_DIR" ]]; then
  echo "Error: Profile directory not found at $PROFILE_DIR"
  echo "Please provide a valid IDE profile directory path."
  exit 1
fi

# Create User directory if it doesn't exist
USER_DIR="$PROFILE_DIR/User"
if [[ ! -d "$USER_DIR" ]]; then
  mkdir -p "$USER_DIR"
  echo "Created User directory at $USER_DIR"
fi

TARGET_PATH="$USER_DIR/keybindings.json"

echo "Applying keybindings to: $TARGET_PATH"

# Backup existing file if it exists
if [[ -f "$TARGET_PATH" ]]; then
  cp "$TARGET_PATH" "$TARGET_PATH.bak"
  echo "  Backed up to $TARGET_PATH.bak"
else
  echo "[]" > "$TARGET_PATH"
  echo "  Created new empty keybindings file."
fi

# Merge using python3
python3 - "$SOURCE_KEYBINDINGS" "$TARGET_PATH" <<'PYEOF'
import json
import sys
import os

try:
    # Get paths from command-line arguments
    source_keybindings = sys.argv[1]
    target_path = sys.argv[2]
    
    with open(source_keybindings, 'r') as f:
        # Strip comments manually since standard json lib doesn't support them
        content = f.read()
        lines = [l for l in content.splitlines() if not l.strip().startswith('//')]
        source_data = json.loads('\n'.join(lines))

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
PYEOF

echo ""
echo "✅ Keybindings setup complete!"
echo "Please reload your IDE window for changes to take effect."
echo "   (Cmd+Shift+P → Reload Window)"
