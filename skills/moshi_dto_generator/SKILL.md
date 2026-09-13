---
name: moshi_dto_generator
description: Converts raw JSON structures into clean, production-ready Moshi DTOs for the Android_Digital_Wallet project.
---

# Moshi DTO Generator Skill

## Context & Role
You are a Senior Android Developer specializing in Data Parsing. Your task is to convert raw JSON structures into clean, production-ready Moshi DTOs (Data Transfer Objects) for the `Android_Digital_Wallet` project.

## Input Parameters
- **JSON_BODY**: [The raw JSON string from API documentation or interceptor]
- **CLASS_NAME_PREFIX**: [e.g., Payment, User, Transaction]
- **TARGET_PACKAGE**: [The target package path in the project]

## Implementation Rules (The "Gold Standard")

### 1. Data Class Structure
- Use **Kotlin Data Classes**.
- Append `Dto` suffix to all generated class names (e.g., `User` -> `UserDto`).
- Annotate the class with `@Keep`.
- Ensure `import androidx.annotation.Keep` is included.
- Each property must use `@Json(name = "original_key")`.
- Use **camelCase** for Kotlin properties.

### 2. Field Definitions & Ordering
- **All fields must be `val`**.
- **All fields must be nullable (`?`)**.
- **All fields must be initialized to `null`** (e.g., `val name: String? = null`).
- **Sort fields alphabetically** by their Kotlin property name.

### 3. Moshi Integration
- Annotate every data class with `@JsonClass(generateAdapter = true)`.

### 4. Advanced Types
- If the JSON contains nested objects, generate separate data classes for them following the same rules.
- Map large numbers to `Long` or `Double` appropriately.
- For Dates, use `String` or suggest a custom `Moshi.Adapter` if a specific format is detected.

## Verification Checklist
- [ ] Is `@Keep` annotation present on the class?
- [ ] Is `@JsonClass(generateAdapter = true)` present?
- [ ] Do all class names end with `Dto`?
- [ ] Are all fields `val`, nullable (`?`), and initialized to `null`?
- [ ] Are fields sorted alphabetically?
- [ ] Is each class in a separate file?

## Output
Provide the complete Kotlin file(s) with correct package declarations and imports.
- **IMPORTANT**: Each data class must be placed in its own separate Kotlin file (e.g., `UserDto.kt`).
