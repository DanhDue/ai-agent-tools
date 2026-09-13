---
name: session_init
description: Use this skill at the start of a new working session to establish the session name, focus area, and the project context the agent should load before doing anything else.
---

# Session Initialization Workflow

When starting a new conversation, use this format as your **first message** to establish context:

> [!IMPORTANT]
> **Import Convention**: Always use **full package paths** (e.g., `import 'package:bloc_digital_wallet/core/network/app_uri.dart';`) instead of relative imports (e.g., `import '../../core/network/app_uri.dart';`).

## Template

```
Session: [NAME]
Focus: [AREA]
Context: [BRIEF DESCRIPTION]
```

## Examples

### Mason Bricks Session
```
Session: Mason - Bricks
Focus: MVI brick templates and automation
Context: Working on mvi_feature, mvi_subfeature, and removal bricks
```

### UI Implementation Session
```
Session: UI - Authentication
Focus: Login and registration screens
Context: Implementing Figma designs for auth flows
```

### Feature Development Session
```
Session: Feature - Wallet
Focus: Wallet module development
Context: Building wallet feature with transactions
```

## Quick Start Templates

Copy-paste one of these to start a focused session:

**Mason/Bricks:**
> Session: Mason - Bricks. Continue work on MVI brick templates.

**Feature Development:**
> Session: Feature - [NAME]. Develop the [feature] module.

**Bug Fixing:**
> Session: Debug - [ISSUE]. Investigate and fix [description].

**Documentation:**
> Session: Docs - [AREA]. Update documentation for [topic].

## Notes

- The session name helps organize conversation history
- Be specific about the focus area to get targeted assistance
- Reference previous artifacts if resuming work
