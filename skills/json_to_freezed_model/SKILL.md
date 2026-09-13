---
name: json_to_freezed_model
description: Parse JSON and create freezed object classes following project conventions.
---

# JSON to Freezed Object Skill

Parse JSON and generate freezed object classes in the data layer.

> [!IMPORTANT]
> **Execute Immediately**: When this skill is requested, skip the `PLANNING` phase and `implementation_plan.md` creation. Proceed directly to `EXECUTION`.

> [!IMPORTANT]
> **Import Convention**: Always use **full package paths** (e.g., `import 'package:bloc_digital_wallet/core/network/app_uri.dart';`) instead of **relative imports** (e.g., `import '../../core/network/app_uri.dart';`).

> [!IMPORTANT]
> **Always use `abstract class` for Freezed models**

> [!IMPORTANT]
> **Always include private constructor**: `const ClassName._();`

## 1. Analyze JSON Structure

1. **Identify root object** and nested objects
2. **Map types**: `string` → `String?`, `number` → `int?`/`double?`, `boolean` → `bool?`, `object` → nested object
3. **Note snake_case keys** that need `@JsonKey` mapping
4. **Naming**: Add `Object` suffix to nested object class names (e.g., `user` → `UserObject`). **Do not add prefix for nested json object.**

## 2. Create Model Files

> [!CRITICAL]
> **ONE OBJECT, ONE FILE RULE**
> 
> Each class (Root or Nested) **MUST** have its own dedicated `.dart` file.
> - ❌ **NEVER** define multiple classes in a single file
> - ❌ **NEVER** put nested objects in the same file as the parent
> - ✅ **ALWAYS** create a separate file for each object, even if it's small
> 
> **Example**: If JSON has `user` and `address` objects, create:
> - `user_object.dart` (contains only `UserObject`)
> - `address_object.dart` (contains only `AddressObject`)

For each object in the JSON hierarchy, create a separated file in the target data layer:

```
lib/features/{module}/data/models/
├── {root_object}.dart
├── {nested_object_1}.dart
└── {nested_object_2}.dart
```

## 3. Model Template

```dart
// Copyright (c) 2026, one of DanhDue ExOICTIF projects. All rights reserved.

// coverage:ignore-file
// ignore_for_file: invalid_annotation_target

import 'package:flutter/foundation.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

// Import nested models if any
import 'package:bloc_digital_wallet/features/{module}/data/models/nested_object.dart';

part '{model_name}.freezed.dart';
part '{model_name}.g.dart';

@freezed
abstract class {ModelName} with _${ModelName} {
  const {ModelName}._();

  @JsonSerializable(includeIfNull: false)
  const factory {ModelName}({
    @JsonKey(name: 'field_name') String? fieldName,
    @JsonKey(name: 'count') int? count,
    @JsonKey(name: 'snake_case_field') String? camelCaseField,
    @JsonKey(name: 'nested') NestedObject? nested,
  }) = _{ModelName};

  factory {ModelName}.fromJson(Map<String, Object?> json) =>
      _${ModelName}FromJson(json);
}
```

## 4. Key Rules

| JSON | Dart | Notes |
|------|------|-------|
| `snake_case` key | `camelCase` property | Use `@JsonKey(name: 'snake_case')` |
| Same name | Same name | **Always use `@JsonKey(name: 'field_name')`** |
| Nested object | `{Name}Object` class | Auto-add `Object` suffix. **No prefix.** |
| All fields | Nullable (`?`) | Use `int?`, `String?`, etc. |
| **Class** | **`abstract class`** | **Always use `abstract class` for Freezed models** |
| **`includeIfNull`** | **`false`** | **Always use `@JsonSerializable(includeIfNull: false)`** |
| **Constructor** | **`const Class._();`** | **Always include private constructor** |
| **Imports** | **`foundation.dart` + `freezed_annotation`** | **Both required for `debugFillProperties` support** |

> **Important**: Always add `@JsonKey` annotation for **every field**, even when the JSON key matches the Dart property name exactly.

## 5. Example

**Input JSON:**
```json
{
  "refresh": "token123",
  "access": "token456",
  "user": {
    "id": 1,
    "username": "john"
  }
}
```

**Output:**

`user_object.dart`:
```dart
@freezed
abstract class UserObject with _$UserObject {
  const UserObject._();

  const factory UserObject({
    @JsonKey(name: 'id') int? id,
    @JsonKey(name: 'username') String? username,
  }) = _UserObject;

  factory UserObject.fromJson(Map<String, Object?> json) =>
      _$UserObjectFromJson(json);
}
```

`sign_in_object.dart`:
```dart
@freezed
abstract class SignInObject with _$SignInObject {
  const SignInObject._();

  const factory SignInObject({
    @JsonKey(name: 'refresh') String? refresh,
    @JsonKey(name: 'access') String? access,
    @JsonKey(name: 'user') UserObject? user,
  }) = _SignInObject;

  factory SignInObject.fromJson(Map<String, Object?> json) =>
      _$SignInObjectFromJson(json);
}
```

## 6. After Creation

```bash
# Generate code
melos genAlls

# Verify
fvm flutter analyze --no-fatal-infos
```
