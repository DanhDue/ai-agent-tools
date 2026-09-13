---
name: melos_sync
description: Use this skill when dependencies change, after pulling changes, or when "file not found" or missing generated-code errors appear in a Flutter melos workspace. Syncs packages and re-runs code generation in the correct order.
---

# Melos Sync Workflow

Use this workflow when dependencies change or when "file not found" errors occur after pulling changes.

## 1. Bootstrap
Link local packages and install dependencies.
```bash
melos bootstrap
```

## 2. Code Generation (Selective)
If you only changed one package, run build_runner there:
```bash
cd packages/<package_name> && flutter pub run build_runner build --delete-conflicting-outputs
```

## 3. Code Generation (Global)
To regenerate everything (slow but safe):
```bash
melos genAlls
```

## 4. Analysis
Check for issues across the entire workspace:
```bash
melos run analyze
```
