---
name: setup_keybindings
description: Merges workspace keybindings (.vscode/keybindings.json) into the user's global IDE configuration (VS Code, Cursor, Windsurf, Antigravity, etc.).
---

# Setup Keybindings

This skill applies the project's recommended keybindings to the user's IDE.
It supports multiple IDEs by checking standard configuration paths on macOS.

## Prerequisites

-   Dart must be installed and available via `fvm dart` or `dart`.
-   The script `scripts/setup_keybindings.dart` must exist in the project root.

## Instructions

1.  **Verify Script Existence**
    -   Check if `scripts/setup_keybindings.dart` exists.
    -   If not, report an error.

2.  **Run Setup Script**
    -   Execute the Bash script:
        ```bash
        bash .agents/skills/setup_keybindings/setup.sh
        ```
    -   The script will:
        -   Detect installed IDEs (VS Code, Cursor, Windsurf, Antigravity, etc.).
        -   Backup existing keybindings to `.bak` files.
        -   Merge `resources/keybindings.json` into the user's configuration.

3.  **Verify Output**
    -   Check the output for success messages (e.g., "Successfully added X keybindings" or "All keybindings already exist").
    -   If "No compatible IDE configurations found" is printed, ask the user for their specific IDE config path.

4.  **Reload Window**
    -   Remind the user to reload their IDE window (`Cmd+Shift+P` -> `Reload Window`) for changes to take effect.
