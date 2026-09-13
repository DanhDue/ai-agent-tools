---
name: create_new_feature
description: Guide for creating a new feature or subfeature following the project's Clean Architecture + MVI pattern.
---

# Create New Feature Skill

This skill guides the agent through the process of creating a new feature (New Module) or adding a subfeature to an existing module (Subfeature).

> [!IMPORTANT]
> **Import Convention**: Always use **full package paths** (e.g., `import 'package:bloc_digital_wallet/core/network/app_uri.dart';`) instead of relative imports (e.g., `import '../../core/network/app_uri.dart';`).

## 1. Analyze Request & Codebase

**Goal**: Determine the context and type of feature requested.

1.  **Analyze User Request**: Identify keywords (e.g., "add forgot password", "create notifications").
2.  **Check Existing Modules**:
    - List directories in `lib/features/`.
    - Determine if the requested feature belongs to an existing module.
3.  **Determine Type**:
    - **Subfeature**: Adds functionality to an existing module (e.g., adding `forgot_password` to `authentication`).
    - **New Module**: Introduces a completely new domain concept (e.g., `notifications`, `chat`).

## 2. Prepare & Confirm (CRITICAL STEP)

**Goal**: Validate the plan with the user before generating code.

**Action**: Present a plan and ask for confirmation using the following template:

```markdown
To proceed, I need to confirm:

MODULE INFORMATION:
- Feature Type: [New Module / Subfeature]
- [If Subfeature] Target Module: [existing_module_name]
- [If New Module] Module Name: [suggested_name]
- Feature Functionality: [brief description]
- UI Requirements: [screen/widgets needed]
- API Endpoints: [list key endpoints if known]

CONFIRMATION:
Should I proceed with creating this as a [New Module/Subfeature]?
```

**WAIT** for user confirmation before proceeding to Step 3.

## 3. Generate Structure (Mason)

**Goal**: Generate the boilerplate structure.

- **If New Module**:
  ```bash
  mason make mvi_feature --feature_name [feature_name]
  ```
- **If Subfeature**:
  ```bash
  mason make mvi_subfeature --module_name [module_name] --subfeature_name [subfeature_name]
  ```

## 4. Implement Domain Layer

**Goal**: Define business logic interfaces.

1.  **Entity**: Create `[feature]_entity.dart` with `@freezed` and `@JsonKey` annotations.
    - Use `abstract class` with `_$ClassName` mixin pattern
    - Import `freezed_annotation` and `foundation.dart`
    - Use `@JsonKey(name: 'field_name')` for each field
    - ⚠️ **IMPORTANT**: All entities and models will use freezed with `@JsonKey` annotations.
    
    ```dart
    import 'package:freezed_annotation/freezed_annotation.dart';
    import 'package:flutter/foundation.dart';
    part '[feature]_entity.freezed.dart';
    part '[feature]_entity.g.dart';

    @freezed
    abstract class [Feature]Entity with _$[Feature]Entity {
      const factory [Feature]Entity({
        @JsonKey(name: 'id') int? id,
        @JsonKey(name: 'name') String? name,
      }) = _[Feature]Entity;

      factory [Feature]Entity.fromJson(Map<String, Object?> json) =>
          _$[Feature]EntityFromJson(json);
    }
    ```
2.  **Repository Interface**: Define `[feature]_repository.dart`.
3.  **Use Cases**: Create use cases for each business action (e.g., `get_data_usecase.dart`).

## 5. Implement Data Layer

**Goal**: Implement data handling.

1.  **Model**: Create `[feature]_model.dart` with `@freezed`, `@JsonKey`, and `json_serializable`.
    - Same pattern as Entity with `abstract class` and `_$ClassName` mixin
2.  **Remote DataSource**: Implement `[feature]_remote_datasource.dart` (use `SafeCallApiMixin`).
3.  **Repository Impl**: Implement `[feature]_repository_impl.dart`.

## 6. Implement Presentation Layer (MVI)

**Goal**: Build the UI and State Management.

1.  **Defines**:
    - **Actions**: User intents (e.g., `LoadDataAction`).
    - **States**: UI states (e.g., `Loading`, `Loaded`).
    - **Events**: One-time effects (e.g., `ShowDetailsEvent`).
2.  **BLoC**: Implement logic in `[feature]_bloc.dart`.
3.  **UI Pages**: Implement `[feature]_page.dart`.
    - **Style**: Use `context.appThemes`.
    - **Text**: Use `context.t` (i18n).
    - **Figma**: If provided, use `figma-dev-mode-mcp-server` to fetch specs.

## 7. Configuration & Verification

**Goal**: Wire everything up and verify.

1.  **Routes**: Add new routes to `lib/app_router.dart` and `AppRoutes` constants.
2.  **Translations**: Add keys to `en.i18n.json` and `vi.i18n.json`.
3.  **Generate Code**:
    ```bash
    melos genAlls
    ```
4.  **Format & Analyze**:
    ```bash
    dart format lib/
    fvm flutter analyze --no-fatal-infos
    ```
5.  **Final Check**: Verify "No issues found!" and functionality matches requirements.
