---
name: check_secure_files
description: Enforces a checklist to verify that all required secure configuration files (google-services.json, GoogleService-Info.plist, environment-configs.json) are present for all environments (dev, stg, prd).
---

# Check Secure Files Skill

This skill ensures that the necessary secure configuration files are populated before proceeding with build variant setup or deployment.

## Steps

### 1. Initialize `secureFiles`
- **Check/Create `secureFiles`**:
    - Copy the template `secureFiles` folder from resources (`.agents/skills/setup_variants/resources/secureFiles`) to the project root if it does not exist.
    - Ensure `signing/debug.keystore` and `signing/keystore.properties.template` are present.

### 2. Verify Checklist (CRITICAL)

> [!IMPORTANT]
> **Safety Check**: You must NOT proceed until the `secureFiles` directory is populated with actual data.

ASK the user to confirm the following checklist. If the user asks to proceed without confirming ALL items, you MUST ask again.

**Checklist**:

- **Dev Environment**
    - [ ] `secureFiles/dev/google-services.json` (Android)
    - [ ] `secureFiles/dev/GoogleService-Info.plist` (iOS)
    - [ ] `secureFiles/dev/environment-configs.json` (Dart Defines)

- **Staging Environment**
    - [ ] `secureFiles/stg/google-services.json` (Android)
    - [ ] `secureFiles/stg/GoogleService-Info.plist` (iOS)
    - [ ] `secureFiles/stg/environment-configs.json` (Dart Defines)

- **Production Environment**
    - [ ] `secureFiles/prd/google-services.json` (Android)
    - [ ] `secureFiles/prd/GoogleService-Info.plist` (iOS)
    - [ ] `secureFiles/prd/environment-configs.json` (Dart Defines)

### 3. Verify Content Integrity
- **Compare with Templates**:
    - For each file in the checklist, compare its content with the corresponding template in `.agents/skills/setup_variants/resources/secureFiles`.
    - Example: Compare `secureFiles/dev/google-services.json` with `.agents/skills/setup_variants/resources/secureFiles/dev/google-services.json`.
- **Validation Logic**:
    - If a file has the **exact same content** as the template, it is considered **INVALID** (user failed to update it).
    - If a file is missing, it is **INVALID**.
- **On Failure**:
    - If any file is invalid:
        1. Notify the user specifically which files are still defaults or missing.
        2. Re-present the **Checklist** from Step 2.
        3. **Uncheck** the boxes for the invalid files.
        4. Ask the user to update the files and check the box again when done.
    - **Loop** until all files are present and different from the templates.
