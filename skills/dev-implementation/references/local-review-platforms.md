# Local Review Platform Rules

The review runner inserts the sections whose file extensions occur in a slice's diff: `.dart`
Flutter, `.kt` and `.kts` Android, `.swift` iOS, `.rs` Rust, `.py` Python. Every rule below is quoted
from a kit skill at its Blocker level; nothing here is a new rule.

## Flutter

Sources: `skills/architecture-audit/SKILL.md`, `skills/code-health-audit/SKILL.md` and
`skills/security-audit/SKILL.md`. These rules apply to added lines of production files; tests are
judged by the checklist. Report a violation as `Important` with the rule ID in its Problem.

- `ARCH-FLUTTER-01` **Domain Layer Purity** — `domain/` is pure Dart: no `package:flutter/*`, Material, Cupertino or UI package import.
- `ARCH-FLUTTER-02` **Feature Package Isolation** — feature packages never import each other; cross-feature communication goes through `packages/platform` (`AppEventBus`, `AppRoutes`); no deep import into `data/` or `*_impl.dart`.
- `ARCH-FLUTTER-03` **BLoC MVI Immutability** — View sends Action, BLoC calls UseCase, RepoInterface, RepoImpl, then emits State and Event; States are immutable (`@freezed`, or `Equatable` with `@immutable`).
- `ARCH-FLUTTER-04` **Stream Hygiene** — every `StreamSubscription` is cancelled in `close()` or `dispose()`; event handlers use transformers (`restartable()`, `droppable()`, `debounce()`).
- `ARCH-FLUTTER-05` **Data Layer Mapping** — DTOs are mapped to Domain Entities before a Repository returns them; implementations live in `data/` and implement `domain/` interfaces.
- `HLT-FLUTTER-03` **Null-Safety (`!` Ban)** — no force-unwrap `!`; use `?.`, `??` or an explicit null check.
- `SEC-FLUTTER-01` **Financial Precision** — no `double` or `num` for currency, balance or fees; use `Decimal` or `BigInt` cents.
- `SEC-FLUTTER-02` **OWASP M1: Credentials** — no hardcoded API key, bearer token or secret in Dart files or `pubspec.yaml`.
- `SEC-FLUTTER-03` **OWASP M5: Communication** — TLS 1.2+ with certificate pinning; never `badCertificateCallback: (_, __, ___) => true`.
- `SEC-FLUTTER-04` **OWASP M6: Privacy / PII** — no logging of card, PIN or token data; app switcher screen masking stays on.
- `SEC-FLUTTER-05` **OWASP M9: Data Storage** — no raw `SharedPreferences` for auth tokens; use `flutter_secure_storage`.
- `SEC-FLUTTER-06` **OWASP M10: Cryptography** — AES-256-GCM and SHA-256+; no MD5 or SHA-1.

## Android

Sources: `skills/architecture-audit/SKILL.md`, `skills/code-health-audit/SKILL.md` and
`skills/security-audit/SKILL.md`. These rules apply to added lines of production files; tests are
judged by the checklist. Report a violation as `Important` with the rule ID in its Problem.

- `ARCH-01` **Domain Layer Purity** — no `android.*`, `androidx.*`, Compose or third-party import in the Domain layer; only `@Inject` is allowed.
- `ARCH-02` **Feature Module Isolation** — a feature never imports another feature's classes; cross-feature routing goes through `:packages:platform` (`AppRoutes`, `AppEventBus`).
- `ARCH-03` **MVI Immutability** — MVI States are `data class` with `val` properties only, updated atomically through `reduce {}` or `copy()`; Effects go through `SharedFlow`.
- `ARCH-04` **Dispatcher Discipline** — no hardcoded `Dispatchers.IO` or `Dispatchers.Default`; inject `DispatcherProvider`; no `GlobalScope` or `runBlocking`.
- `ARCH-06` **Data Layer Mapping** — DTOs are mapped to Domain Entities before a Repository returns them; Repositories implement Domain interfaces.
- `HLT-03` **Null-Safety (`!!` Ban)** — no force-unwrap `!!`; use `requireNotNull()`, `checkNotNull()` or Elvis `?:`.
- `SEC-01` **Financial Precision** — no `Double` or `Float` for money; use `BigDecimal` or `Long` cents.
- `SEC-02` **OWASP M1: Credentials** — no hardcoded API key, JWT, private key or password in source code.
- `SEC-03` **OWASP M5: Communication** — TLS 1.2+ with `CertificatePinner`; no cleartext HTTP and no SSL bypass such as `TrustAllCerts`.
- `SEC-04` **OWASP M6: Privacy / PII** — no logging of card numbers, CVV, PIN or tokens; `FLAG_SECURE` on financial screens.
- `SEC-05` **OWASP M9: Data Storage** — no unencrypted `SharedPreferences`; use `SecureCacheStore`, `EncryptedSharedPreferences` or the Keystore.
- `SEC-06` **OWASP M10: Cryptography** — no MD5, SHA-1 or DES; use AES-256-GCM, SHA-256+ and the Android Keystore.

## iOS

Sources: `skills/architecture-audit/SKILL.md`, `skills/code-health-audit/SKILL.md` and
`skills/security-audit/SKILL.md`. These rules apply to added lines of production files; tests are
judged by the checklist. Report a violation as `Important` with the rule ID in its Problem.

- `ARCH-IOS-01` **Domain Layer Purity** — `Sources/*/Domain/` is pure Swift: no `SwiftUI`, `UIKit` or `Combine` import; only the standard library and Foundation.
- `ARCH-IOS-02` **Feature Package Isolation** — packages under `Features/*` never import each other; cross-feature routing goes through `Platform` (`AppRoutes`, `AppEventBus`, `RouteProvider`); no deep import into `Data/`.
- `ARCH-IOS-03` **MVI State Immutability** — View sends Action, ViewModel calls UseCase, RepoProtocol, RepoImpl, then yields State and emits Event; States are immutable `struct`s with `let` properties.
- `ARCH-IOS-04` **Structured Concurrency** — ViewModels are `@MainActor`; Tasks are cancelled in `deinit` or lifecycle hooks; no unconfined detached task without a cancellation token.
- `ARCH-IOS-05` **Composition Root & Mapping** — the DI graph resolves only in `App/`; Data repositories implement Domain protocols, map DTOs to Domain Entities, and stay `internal` to the package.
- `HLT-IOS-03` **Null-Safety (`!` & `try!` Ban)** — no force-unwrap `!` and no `try!`; use `guard let`, `if let`, `??` or a thrown error.
- `SEC-IOS-01` **Financial Precision** — no `Double` or `Float` for currency, balance or fees; use `Decimal` or `Int64` cents.
- `SEC-IOS-02` **OWASP M1: Credentials** — no hardcoded API key, bearer token or secret in Swift files, `.xcconfig` or Tuist manifests.
- `SEC-IOS-03` **OWASP M5: Communication** — TLS 1.2+ with certificate pinning through `URLSessionDelegate` or `TrustKit`; never `NSAllowsArbitraryLoads = true`.
- `SEC-IOS-04` **OWASP M6: Privacy / PII** — no logging of card, PIN or token data; a privacy overlay covers the app switcher when `scenePhase != .active`.
- `SEC-IOS-05` **OWASP M9: Data Storage** — no raw `UserDefaults` for auth tokens; use `SecureCacheStore` backed by the Keychain.
- `SEC-IOS-06` **OWASP M10: Cryptography** — Apple CryptoKit (AES-GCM, SHA-256+); no MD5, SHA-1 or DES.

## Rust

Source: `skills/rust-quality-check/references/rust-architecture-governance.md`, the policies its
`xtask` architecture check enforces. These rules apply to added lines of production files; tests are
judged by the checklist. Report a violation as `Important` with the policy name in its Problem.

- **Feature Module Isolation** — sibling feature crates never import each other directly.
- **Layer Boundary Inversion** — Domain crates hold pure business logic with no framework or driver dependency.
- **Application & Infrastructure Direction** — Presentation and Infrastructure layers depend inward on Domain abstractions.
- **MVI State Immutability** — intents, reducers and states exported by a crate follow unidirectional data flow.
- **Forbidden Dependencies** — dependency deny-lists hold across sensitive crates, for example no async runtime in a pure domain crate.

## Python

Source: `skills/python-quality-check/references/python-architecture-governance.md`, the contracts its
`lint-imports` check enforces. These rules apply to added lines of production files; tests are judged
by the checklist. Report a violation as `Important` with the policy name in its Problem.

- **Layer Boundary Inversion** — Domain layers hold pure domain logic with no dependency on presentation, CLI or infrastructure layers.
- **Feature Module Isolation** — independent feature packages never import internal implementations from sibling features.
- **Application & Infrastructure Direction** — Presentation (CLI or API) and Infrastructure (network, database, storage) depend inward on Domain abstractions.
- **Forbidden Dependencies** — dependency ban lists hold, for example no network or async runtime package inside pure domain models.
