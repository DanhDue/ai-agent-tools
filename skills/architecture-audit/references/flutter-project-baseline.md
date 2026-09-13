# Flutter Project Baseline — Architecture

House conventions that go **beyond** the `ARCH-FLUTTER-*` rules in `SKILL.md`. Layering, domain
purity, MVI immutability, stream hygiene and DTO mapping are already covered there — do not
re-check them here.

## Navigation (AutoRoute)

- Routes declared in `app_router.dart`; every screen widget annotated `@RoutePage()`.
- Navigate via `context.router.push(...)`, never by constructing a route ad hoc.

## Dependency injection (GetIt + Injectable)

- Services and repositories annotated `@singleton` or `@lazySingleton`; clients supplied through
  `@module` providers.
- **Constructor injection only.** `GetIt.I.get()` inside a class body is a finding — it hides the
  dependency and defeats testability.
- Every BLoC is registered in `lib/di/` and supplied via `BlocProvider`. A BLoC constructed
  inline in a widget is a finding.

## MVI naming split

`Action` carries user intent; `Event` carries a one-time side effect (navigation, toast). Using
one where the other belongs is a finding.

## Retrofit clients

Never instantiate a Retrofit client without an explicit `baseUrl` — Dio's default may point at a
different microservice.

```dart
TokenClient(dio)                                                    // ❌
TokenClient(dio, baseUrl: AppUri.tokenAccounts.buildAppUri()!)      // ✅ resolved in NetworkModule
```

## Expected libraries

`flutter_bloc` · `freezed` / `json_serializable` · `auto_route` · `retrofit` / `dio` ·
`slang` (i18n)

A new dependency duplicating one of these warrants a finding — ask why the house library was not
used.
