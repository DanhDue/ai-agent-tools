---
name: setup_local_keybindings
description: Merges workspace keybindings into IDE user profile configurations (e.g., ~/antigravity-profile-2/User/keybindings.json).
---

# Setup Local Keybindings

This skill applies the project's recommended keybindings to IDE user profiles (custom profile directories).

Unlike `setup_keybindings` which targets global IDE configurations, this skill targets specific user profiles like `~/antigravity-profile-2`.

> [!IMPORTANT]
> **User Data Directory Mapping**: The profile directory you provide MUST match the `--user-data-dir` argument used when launching the IDE.
> 
> For example:
> - If you launch with: `antigravity --user-data-dir ~/antigravity-profile-2`
> - Then use this skill with: `bash setup.sh ~/antigravity-profile-2`
> - Keybindings will be placed in: `~/antigravity-profile-2/User/keybindings.json`

## Prerequisites

- Python3 must be installed (for JSON merging).
- The keybindings resource file must exist at `resources/keybindings.json`.

## Features

### 🎯 Auto-Detection (New!)

The script can automatically detect the `--user-data-dir` from running IDE processes:

- ✅ Detects Antigravity, VS Code, Cursor, and Windsurf
- ✅ Shows all detected profiles with IDE names
- ✅ Auto-selects if only one profile is found
- ✅ Prompts for selection if multiple profiles are found

### Manual Mode

You can also specify the profile directory manually if auto-detection doesn't work or if the IDE isn't running.

## Instructions

### Option 1: Auto-Detection (Recommended)

1. **Launch your IDE with `--user-data-dir`**:
   ```bash
   antigravity --user-data-dir ~/antigravity-profile-2
   ```

2. **Run the script without arguments**:
   ```bash
   bash .agents/skills/setup_local_keybindings/setup.sh
   ```

3. The script will automatically detect and use the running IDE's user data directory.

### Option 2: Manual Path

1. **Run the script with the profile directory path**:
   ```bash
   bash .agents/skills/setup_local_keybindings/setup.sh ~/antigravity-profile-2
   ```

2. The script will:
   - Validate the profile directory exists.
     - Create `User/keybindings.json` if it doesn't exist.
     - Backup existing keybindings to `.bak` files.
     - Merge `resources/keybindings.json` into the profile's configuration.

3. **Verify Output**
   - Check the output for success messages (e.g., "Successfully added X keybindings" or "All keybindings already exist").
   - If errors occur, verify the profile path is correct.

4. **Reload Window**
   - Remind the user to reload their IDE window (`Cmd+Shift+P` → `Reload Window`) for changes to take effect.

## Usage Examples

### Example 1: Antigravity with Custom Profile

If you launch Antigravity with:
```bash
antigravity --user-data-dir ~/antigravity-profile-2
```

Then apply keybindings with:
```bash
bash .agents/skills/setup_local_keybindings/setup.sh ~/antigravity-profile-2
```

This will place keybindings in: `~/antigravity-profile-2/User/keybindings.json`

---

### Example 2: VS Code with Custom Profile

If you launch VS Code with:
```bash
code --user-data-dir ~/my-custom-vscode-profile
```

Then apply keybindings with:
```bash
bash .agents/skills/setup_local_keybindings/setup.sh ~/my-custom-vscode-profile
```

This will place keybindings in: `~/my-custom-vscode-profile/User/keybindings.json`

## Notes

- **Critical**: The profile directory path MUST match the `--user-data-dir` argument used when launching your IDE.
- The script creates backups automatically (`.bak` files).
- Only new keybindings are added; existing ones are preserved.
- The merge is idempotent - running it multiple times is safe.
- Keybindings are placed in `<profile-dir>/User/keybindings.json`.

## Verification

To verify the keybindings were applied to the correct location:

1. Check the script output for the target path
2. Verify the file exists: `ls -la ~/antigravity-profile-2/User/keybindings.json`
3. Launch your IDE with the matching `--user-data-dir` argument
4. Check that keybindings are active in the IDE
