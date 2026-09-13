---
name: setup_build
description: Use this skill to make a Flutter checkout buildable - verify secure files are present, copy them into their platform locations, optionally configure dev/stg/prd build variants, and confirm the environment by building one flavor. Use it on a fresh clone, a new worktree, or after secure files change.
---

# Setup Build

Brings a checkout to the point where it can actually build and run. Two paths: the short one
when variants are already configured, and the full one when they are not.

> [!NOTE]
> The agent does **not** need permission to read the `secureFiles/` directory. Assume access
> is granted.

## 1. Check secure files

Run the `check_secure_files` skill to verify every required file is present, initialising the
`secureFiles/` template if needed.

**Do not proceed while anything is missing.** If `secureFiles/` is absent entirely, use the
`secrets_env` skill first — it decodes the `SECURE_FILES` environment variable or tells the
user exactly what to run.

## 2. Copy secure configurations

Trigger the `copy_secure_configurations` skill, which runs its own
`resources/scripts/copy_secure_files.sh` to place `google-services.json` and
`GoogleService-Info.plist` into their Android and iOS locations.

## 3. Configure variants — only if not already set up

Skip this step on a project whose flavors already exist. Otherwise trigger the
`setup_variants` skill to:

- configure Android Gradle flavors,
- configure iOS XCConfigs and schemes,
- update the VS Code `launch.json`.

## 4. Verify

Build one flavor end to end. Success here is the whole point of the skill — do not report the
environment as ready without it.

```bash
cd android && ./gradlew assembleDevDebug     # Android
cd ios && pod install                        # iOS, only if the project uses CocoaPods
```

Then run the app on the dev flavor:

```bash
fvm flutter run --flavor dev --dart-define-from-file=secureFiles/dev/environment-configs.json
```

## Related skills

| Skill | Use it for |
|---|---|
| `check_secure_files` | Verifying the `secureFiles/` contents |
| `copy_secure_configurations` | Placing config files into Android/iOS paths |
| `setup_variants` | First-time flavor configuration |
| `secrets_env` | Recovering `secureFiles/` from the `SECURE_FILES` env var |
| `melos_sync` | Dependency or generated-code errors after pulling |
