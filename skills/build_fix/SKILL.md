---
name: build_fix
description: Use this skill to systematically clear Flutter build and analyzer errors. Captures the full analyzer report, groups errors by cause (missing imports, missing codegen, type mismatch, lint), then fixes and re-runs until clean.
---

# Build & Fix Workflow

Use this workflow to systematic fix build errors.

## 1. Run Analysis
Capture all errors:
```bash
fvm flutter analyze --no-fatal-infos > analysis_report.txt
```

## 2. Categorize Errors
Group errors by type:
- **Missing Imports**: Run `melos bootstrap` or fix path.
- **Code Gen Missing**: Run `melos genAlls`.
- **Type Mismatch**: Fix specific line.
- **Lint Rule**: Fix or ignore (if justified).

## 3. Fix Loop
For each category:
1.  Apply fix.
2.  Run `fvm flutter analyze` again.
3.  Repeat until "No issues found!".
