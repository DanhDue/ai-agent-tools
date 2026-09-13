---
name: copy_secure_configurations
description: Copies secure configuration files (google-services.json, GoogleService-Info.plist) from the secureFiles directory to Android and iOS project paths.
---

# Copy Secure Configurations Skill

This skill automates the process of copying sensitive configuration files from a secured location (`secureFiles/`) to their respective platform directories within the project. This is typically run after setting up the project environment or when secure files change.

> [!NOTE]
> This skill is **safe to auto-run**. If this skill is mentioned or detected, execute the copy script immediately without requesting user confirmation.

## Prerequisites

- `secureFiles` directory at the project root with the following structure:
    - `dev/google-services.json`
    - `dev/GoogleService-Info.plist`
    - `stg/google-services.json`
    - `stg/GoogleService-Info.plist`
    - `prd/google-services.json`
    - `prd/GoogleService-Info.plist`

## Usage

1.  **Run the copy script**:
    - The script will copy files to `android/app/src/<flavor>/` and `ios/Runner/Firebase/`.
    - Run the following command from the project root:

    ```bash
    sh .agents/skills/copy_secure_configurations/resources/scripts/copy_secure_files.sh
    ```

2.  **Verify Output**:
    - Check the terminal output for success messages (`✅ Copied ...`).
    - Verify files exist in `android/app/src/` and `ios/Runner/Firebase/`.
