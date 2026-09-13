---
name: setup_variants
description: Automates the setup of build variants (flavors) for Android and iOS in a default Flutter project, including signing and VS Code launch configuration.
---

# Setup Variants Skill

This skill configures `dev`, `stg`, and `prd` build variants for both Android and iOS in a standard Flutter project.

**Reference Guide:** [Setup Development Environments Guide](https://viblo.asia/p/setup-development-environmentsdevelopstagingproduction-for-the-flutter-project-bJzKmd9659N#_1-parse-properties-from-the-flutter-command-arguments-6)

## Prerequisites
- A standard Flutter project structure
- `secureFiles` directory with signing keys and flavor configurations (json)

## Steps

### 1. Android Setup
1.  **Modify `android/app/build.gradle.kts`**:
    -   Apply the flavor and signing configuration.
    -   Use the template from local resources: `.agents/skills/setup_variants/resources/android/build_gradle_flavors.kts`.
    -   Ensure `signingConfigs` map to `secureFiles` correctly.
2.  **Update .gitignore**:
    -   Add `keystore.properties` to `android/.gitignore` (defensive, in case it is copied locally).
3.  **Verify Android Build**:
    -   Run `./gradlew bundleRelease` (or `assembleRelease`) to ensure gradle syncs and builds correctly.

### 2. iOS Setup
1.  **Clean Default Scheme**:
    -   Remove `ios/Runner.xcodeproj/xcshareddata/xcschemes/Runner.xcscheme`.
2.  **Copy Scripts**:
    -   Copy `extract_dart_defines.sh` to `ios/scripts/`.
    -   Copy `update_project.py` and `update_project_runner_tests.py` to `ios/scripts/`.
    -   Copy `copy_google_service_plist.sh` to `ios/scripts/`.
    -   Make `extract_dart_defines.sh` and `copy_google_service_plist.sh` executable (`chmod +x`).
3.  **Run Automation Scripts**:
    -   Run `python3 ios/scripts/update_project.py --app-name <your_app_name>` (e.g. `python3 ios/scripts/update_project.py --app-name Wallet`) to create Build Configurations.
    -   Run `python3 ios/scripts/update_project_runner_tests.py` to fix RunnerTests targets.
4.  **Create XCConfigs**:
    -   Create `ios/Flutter/{app_name}-defaults.xcconfig` using the resource template `App-defaults.xcconfig`.
    -   Create flavor `.xcconfig` files (e.g. `{app_name}-dev.xcconfig`, `{app_name}.xcconfig`) in `ios/Flutter/` that import `{app_name}.xcconfig` and generated Pods configs.
    -   *Note*: Ensure your Xcode Build Phase that runs `extract_dart_defines.sh` passes `{app_name}` as the first argument.
5.  **Update .gitignore**:
    -   Add `Flutter/{app_name}.xcconfig` to `ios/.gitignore` as it is a generated file.
6.  **Update Info.plist**:
    -   Set `CFBundleDisplayName` to `$(DART_DEFINES_APP_NAME)`.
    -   Set `CFBundleIdentifier` to `$(PRODUCT_BUNDLE_IDENTIFIER)$(DART_DEFINES_APP_ID_SUFFIX)`.
7.  **Create Schemes**:
    -   (Already handled by `update_project.py` logic or manual xml creation if needed - *Note: current script does not create schemes xml, only config. You may need to create scheme XMLs defined in previous steps if not present*).
    -   Actually, for this skill, ensure `dev`, `stg`, `prd` schemes exist in `xcshareddata`.
8.  **Update Podfile**:
    -   Map the new configurations to `:debug` and `:release`.
    -   Ensure `platform :ios, '13.0'` (or higher) is set.
    -   Enforce `IPHONEOS_DEPLOYMENT_TARGET` in `post_install`.
9.  **GoogleService-Info.plist Setup**:
    -   **Prerequisite**: Run the `@copy_secure_configurations` skill first to copy your valid `GoogleService-Info.plist` files to `ios/Runner/Firebase/`.
        -   This ensures files like `GoogleService-Info.dev.plist` exist.
    -   In Xcode, add a new "Run Script" Build Phase *after* "Copy Bundle Resources".
    -   Name it "Copy GoogleService-Info.plist".
    -   Script: `"${SRCROOT}/scripts/copy_google_service_plist.sh"`
10. **Verify iOS Build**:
    -   Run `pod install` in `ios/`.

### 3. VS Code Configuration
1.  **Create `launch.json`**:
    -   Create `.vscode/launch.json` using the template from resources.

### 4. Verification


Run the following commands to verify the setup for each environment. These match the configurations in `.vscode/launch.json`.

**Dev Environment:**
```bash
flutter run --flavor dev --dart-define-from-file=secureFiles/dev/environment-configs.json
```

**Staging Environment:**
```bash
flutter run --flavor stg --dart-define-from-file=secureFiles/stg/environment-configs.json
```

**Production Environment:**
```bash
flutter run --flavor prd --dart-define-from-file=secureFiles/prd/environment-configs.json
```
