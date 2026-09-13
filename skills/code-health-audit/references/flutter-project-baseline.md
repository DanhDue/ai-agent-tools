# Flutter Project Baseline — Conventions

House conventions that go **beyond** the `HLT-FLUTTER-*` rules in `SKILL.md`. Function sizing,
argument limits, the `!` ban, naming semantics and Effective Dart are already covered there — do
not re-check them here.

## Import paths

Never use a relative import for a file under `lib/`. Relative imports break under refactoring and
invite import cycles.

```dart
import '../../core/utils.dart';                          // ❌
import 'package:<project_name>/core/utils.dart';         // ✅
```

## Models and entities (Freezed)

All data classes use `freezed`, and:

- **One object, one file.** Every class — root or nested — gets its own `.dart` file.
- Declared as an `abstract class`.
- `@JsonKey(name: 'field_name')` on **every** field, so backend renames never silently break
  deserialisation.
- `@JsonSerializable(includeIfNull: false)`, via `build.yaml` or an explicit annotation.
- Imports `package:freezed_annotation/freezed_annotation.dart`.

```dart
@freezed
class Token with _$Token {
  const factory Token({
    @JsonKey(name: 'token_id') required String tokenId,
    @JsonKey(name: 'is_active') @Default(false) bool isActive,
  }) = _Token;

  factory Token.fromJson(Map<String, dynamic> json) => _$TokenFromJson(json);
}
```

## Naming

| Kind | Convention |
|---|---|
| Files | `snake_case.dart` |
| Classes | `PascalCase` |
| Variables, methods | `camelCase` |
| Constants | `lowerCamelCase` (`kDefaultTimeout`), or `SCREAMING_SNAKE` for strict config |

## Formatting

- **Line length 99** — `dart format -l 99`. Neither the 80 default nor 100+.
- Trailing commas everywhere in widget trees, so the formatter breaks them predictably.
- Member order: imports (Dart → package → project), constants, fields, constructor, lifecycle
  methods, public methods, private methods.

## Dart style

- Prefer `final` over `var`; never `dynamic` where a type is known.
- `async`/`await` rather than raw `.then()`.
- Use dot shorthands where the type is inferred: `.infinity`, `.maxFinite`, `.zero` — not
  `double.infinity`, `Offset.zero`.
