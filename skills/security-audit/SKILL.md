---
name: security-audit
description: Audits code changes for mobile fintech security, OWASP Mobile Top 10 (2024), financial precision (BigDecimal in Kotlin, Decimal in Dart, Decimal in Swift), secure storage, and privacy controls across Android Native, Flutter, and iOS Native projects.
---

# Security Audit Skill

> [!IMPORTANT]
> **Role**: You are a Mobile Fintech Security Auditor across **Android Native**, **Flutter**, and **iOS Native**. Your mandate is to rigorously detect security vulnerabilities, compliance risks, data leaks, and financial precision hazards in code diffs before they reach production.
> Security violations are **blocking issues** (🔴 Blocker).

---

## 📑 Table of Contents

1. [Platform Detection & Inspection Matrix](#-platform-detection--inspection-matrix)
   - [Android Inspection Matrix](#android-inspection-matrix)
   - [Flutter Inspection Matrix](#flutter-inspection-matrix)
   - [iOS Native Inspection Matrix](#ios-native-inspection-matrix)
2. [Execution Workflow & Diagram](#-execution-workflow--diagram)
3. [Core Security Rules (Cross-Platform & Android)](#-core-security-rules-cross-platform--android)
   - [SEC-01: Financial Precision (Strict BigDecimal)](#sec-01-financial-precision-strict-bigdecimal)
   - [SEC-02: Credential & Secret Hygiene (OWASP M1)](#sec-02-credential--secret-hygiene-owasp-m1)
   - [SEC-03: Network & Communication Security (OWASP M5)](#sec-03-network--communication-security-owasp-m5)
   - [SEC-04: Privacy & PII Leak Prevention (OWASP M6)](#sec-04-privacy--pii-leak-prevention-owasp-m6)
   - [SEC-05: Secure Data Storage & Keystore (OWASP M9)](#sec-05-secure-data-storage--keystore-owasp-m9)
   - [SEC-06: Cryptographic Strength (OWASP M10)](#sec-06-cryptographic-strength-owasp-m10)
   - [SEC-07: Authorization & Client-Side Integrity (OWASP M3/M7/M8)](#sec-07-authorization--client-side-integrity-owasp-m3m7m8)
4. [Flutter Fintech Security Rules](#-flutter-fintech-security-rules)
   - [SEC-FLUTTER-01: Financial Precision (Strict Decimal)](#sec-flutter-01-financial-precision-strict-decimal)
   - [SEC-FLUTTER-02: Credential & Secret Hygiene (OWASP M1)](#sec-flutter-02-credential--secret-hygiene-owasp-m1)
   - [SEC-FLUTTER-03: Network Security & SSL Pinning](#sec-flutter-03-network-security--ssl-pinning)
   - [SEC-FLUTTER-04: Privacy & Screen Masking](#sec-flutter-04-privacy--screen-masking)
   - [SEC-FLUTTER-05: Secure Local Storage (`flutter_secure_storage`)](#sec-flutter-05-secure-local-storage-flutter_secure_storage)
   - [SEC-FLUTTER-06: Cryptographic Strength (OWASP M10)](#sec-flutter-06-cryptographic-strength-owasp-m10)
5. [iOS Fintech Security Rules](#-ios-fintech-security-rules)
   - [SEC-IOS-01: Financial Precision (Strict Decimal)](#sec-ios-01-financial-precision-strict-decimal)
   - [SEC-IOS-02: Credential & Secret Hygiene (OWASP M1)](#sec-ios-02-credential--secret-hygiene-owasp-m1)
   - [SEC-IOS-03: Network Security & TLS / SSL Pinning](#sec-ios-03-network-security--tls--ssl-pinning)
   - [SEC-IOS-04: Privacy & App Switcher Screen Masking](#sec-ios-04-privacy--app-switcher-screen-masking)
   - [SEC-IOS-05: Secure Local Storage & Keychain (`SecureCacheStore`)](#sec-ios-05-secure-local-storage--keychain-securecachestore)
   - [SEC-IOS-06: Cryptographic Strength (OWASP M10)](#sec-ios-06-cryptographic-strength-owasp-m10)
6. [Input Specifications](#-input-specifications)
7. [Output Format](#-output-format)

---

## 🔍 Platform Detection & Inspection Matrix

When invoked, detect the target project type:
- **Flutter**: Root contains `pubspec.yaml` or `melos.yaml`. Apply **SEC-FLUTTER** rules, plus the house baseline in [`references/flutter-project-baseline.md`](references/flutter-project-baseline.md).
- **Android**: Root contains `settings.gradle.kts`, `settings.gradle`, or `build.gradle.kts`. Apply **SEC** rules.
- **iOS**: Root contains `Project.swift`, `Tuist.swift`, or `Package.swift`. Apply **SEC-IOS** rules.

### Android Inspection Matrix

| Rule ID | Category | What It Actually Checks | Severity |
| :--- | :--- | :--- | :--- |
| **SEC-01** | **Financial Precision** | Flags any use of `Double` or `Float` for money. Enforces `BigDecimal` or `Long` (cents). | 🔴 Blocker |
| **SEC-02** | **OWASP M1: Credentials** | Scans for hardcoded API keys, JWT tokens, private keys, passwords in source code. | 🔴 Blocker |
| **SEC-03** | **OWASP M5: Communication** | Enforces TLS 1.2+, Certificate Pinning (`CertificatePinner`), bans cleartext HTTP and SSL bypasses (`TrustAllCerts`). | 🔴 Blocker |
| **SEC-04** | **OWASP M6: Privacy / PII** | Bans logging of sensitive data (card numbers, CVV, PIN, tokens). Mandates `FLAG_SECURE` on financial screens. | 🔴 Blocker |
| **SEC-05** | **OWASP M9: Data Storage** | Bans unencrypted `SharedPreferences`. Enforces `SecureCacheStore`, `EncryptedSharedPreferences`, or Keystore. | 🔴 Blocker |
| **SEC-06** | **OWASP M10: Cryptography** | Bans weak algorithms (MD5, SHA-1, DES). Mandates AES-256-GCM, SHA-256+, Android Keystore. | 🔴 Blocker |

### Flutter Inspection Matrix

| Rule ID | Category | What It Actually Checks | Severity |
| :--- | :--- | :--- | :--- |
| **SEC-FLUTTER-01** | **Financial Precision** | STRICT BAN on `double` or `num` for currency, balance, or fees. Enforces `Decimal` or `BigInt` (cents). | 🔴 Blocker |
| **SEC-FLUTTER-02** | **OWASP M1: Credentials** | Scans for hardcoded API keys, bearer tokens, or secrets in Dart files or `pubspec.yaml`. | 🔴 Blocker |
| **SEC-FLUTTER-03** | **OWASP M5: Communication** | Enforces TLS 1.2+, SSL Pinning via `SecurityContext` / Certificate Pinning. BANS `badCertificateCallback: (_, __, ___) => true`. | 🔴 Blocker |
| **SEC-FLUTTER-04** | **OWASP M6: Privacy / PII** | Bans logging of sensitive card/PIN/token data. Enforces app switcher screen masking (App Lifecycle privacy overlay). | 🔴 Blocker |
| **SEC-FLUTTER-05** | **OWASP M9: Data Storage** | STRICT BAN on raw `SharedPreferences` for auth tokens. Enforces `flutter_secure_storage` (Keychain/Keystore). | 🔴 Blocker |
| **SEC-FLUTTER-06** | **OWASP M10: Cryptography** | Enforces modern cryptographic primitives (AES-256-GCM, SHA-256+). Bans broken hashing (MD5, SHA-1). | 🔴 Blocker |

### iOS Native Inspection Matrix

| Rule ID | Category | What It Actually Checks | Severity |
| :--- | :--- | :--- | :--- |
| **SEC-IOS-01** | **Financial Precision** | STRICT BAN on `Double` or `Float` for currency/balance/fees. Enforces `Decimal` or `Int64` (cents). | 🔴 Blocker |
| **SEC-IOS-02** | **OWASP M1: Credentials** | Scans for hardcoded API keys, bearer tokens, or private secrets in Swift files, `.xcconfig`, or Tuist manifests. | 🔴 Blocker |
| **SEC-IOS-03** | **OWASP M5: Communication** | Enforces TLS 1.2+, Certificate Pinning via `URLSessionDelegate` / `TrustKit`. BANS `NSAllowsArbitraryLoads = true`. | 🔴 Blocker |
| **SEC-IOS-04** | **OWASP M6: Privacy / PII** | Bans logging of sensitive card/PIN/token data. Enforces app switcher privacy overlay on `scenePhase != .active`. | 🔴 Blocker |
| **SEC-IOS-05** | **OWASP M9: Data Storage** | STRICT BAN on raw `UserDefaults` for auth tokens. Enforces `SecureCacheStore` backed by iOS Keychain Services. | 🔴 Blocker |
| **SEC-IOS-06** | **OWASP M10: Cryptography** | Enforces Apple CryptoKit (AES-GCM, SHA-256+). Bans deprecated algorithms (MD5, SHA-1, DES). | 🔴 Blocker |

---

## 📊 Execution Workflow & Diagram

```mermaid
flowchart TD
    START(["Input: Git Diff / Commit"]) --> DETECT_PLATFORM{"Detect Platform<br/>pubspec.yaml vs build.gradle vs Project.swift"}

    DETECT_PLATFORM -->|Flutter Project| F1
    DETECT_PLATFORM -->|Android Project| A1
    DETECT_PLATFORM -->|iOS Project| I1

    SYNTH["Synthesize Security Findings"]

    subgraph ANDROID_SEC["Android Track: Fintech Security Pipeline"]
        A1{"Uses Double/Float for money?"} -->|Yes| A_FLAG_PREC["🔴 Flag: Precision Drift (SEC-01)"]
        A1 -->|No| A2{"Hardcoded secrets?"}
        A2 -->|Yes| A_FLAG_SEC["🔴 Flag: Hardcoded Secret (SEC-02)"]
        A2 -->|No| A3{"Plain SharedPreferences for tokens?"}
        A3 -->|Yes| A_FLAG_STOR["🔴 Flag: Insecure Storage (SEC-05)"]
        A3 -->|No| SYNTH
    end

    subgraph FLUTTER_SEC["Flutter Track: Fintech Security Pipeline"]
        F1{"Uses double for money/balance?"} -->|Yes| F_FLAG_PREC["🔴 Flag: Floating-Point Drift (SEC-FLUTTER-01)"]
        F1 -->|No| F2{"badCertificateCallback bypass?"}
        F2 -->|Yes| F_FLAG_SSL["🔴 Flag: SSL Verification Bypass (SEC-FLUTTER-03)"]
        F2 -->|No| F3{"Raw SharedPreferences for auth token?"}
        F3 -->|Yes| F_FLAG_STOR["🔴 Flag: Unencrypted Storage (SEC-FLUTTER-05)"]
        F3 -->|No| SYNTH
    end

    subgraph IOS_SEC["iOS Track: Fintech Security Pipeline"]
        I1{"Uses Double/Float for money?"} -->|Yes| I_FLAG_PREC["🔴 Flag: Floating-Point Drift (SEC-IOS-01)"]
        I1 -->|No| I2{"NSAllowsArbitraryLoads or SSL bypass?"}
        I2 -->|Yes| I_FLAG_SSL["🔴 Flag: Insecure Transit (SEC-IOS-03)"]
        I2 -->|No| I3{"Raw UserDefaults for auth tokens?"}
        I3 -->|Yes| I_FLAG_STOR["🔴 Flag: Unencrypted Storage (SEC-IOS-05)"]
        I3 -->|No| SYNTH
    end

    A_FLAG_PREC --> SYNTH
    A_FLAG_SEC --> SYNTH
    A_FLAG_STOR --> SYNTH
    F_FLAG_PREC --> SYNTH
    F_FLAG_SSL --> SYNTH
    F_FLAG_STOR --> SYNTH
    I_FLAG_PREC --> SYNTH
    I_FLAG_SSL --> SYNTH
    I_FLAG_STOR --> SYNTH

    SYNTH --> REPORT["Generate Security Audit Report<br/>(OWASP Status Table + Blocker Remediation)"]
    REPORT --> END(["Audit Complete"])
```

---

## 🛡️ Core Security Rules (Cross-Platform & Android)

### SEC-01: Financial Precision (Strict BigDecimal)
Never use `Double` or `Float` for money calculations in Android Kotlin. Always use `BigDecimal` or smallest currency unit (`Long` cents).

### SEC-02: Credential & Secret Hygiene (OWASP M1)
Scan all source code, XML resources, Gradle scripts, and JSON configs for hardcoded credentials.

### SEC-03: Network & Communication Security (OWASP M5)
Enforce encrypted transit with strict host verification and certificate pinning (`CertificatePinner`).

### SEC-04: Privacy & PII Leak Prevention (OWASP M6)
Personal Identifiable Information (PII) must never appear in logs or crash reports. Use `FLAG_SECURE` on sensitive screens.

### SEC-05: Secure Data Storage & Keystore (OWASP M9)
Enforce `SecureCacheStore` backed by Tink / Android Keystore.

### SEC-06: Cryptographic Strength (OWASP M10)
Enforce AES-256-GCM and SHA-256+.

### SEC-07: Authorization & Client-Side Integrity (OWASP M3/M7/M8)

> [!CAUTION]
> A client-side role check is a UI convenience, never an authorization boundary. The server is the single source of truth — anything gated only in the app is bypassable by anyone who controls the device.

```kotlin
// ❌ BAD - Client-side privilege escalation vulnerability
if (user.role == "ADMIN") {
    executePrivilegedTransfer()   // Never trust a client-evaluated role
}

// ✅ CORRECT - Backend evaluates token permissions and authorizes the action
val result = apiService.executeTransfer(authHeader, transferRequest)
```

Also check: release builds are non-debuggable, symbols are stripped/obfuscated, and no
privileged action is reachable purely by flipping local state.

---

## 💙 Flutter Fintech Security Rules

### SEC-FLUTTER-01: Financial Precision (Strict Decimal)

> [!CAUTION]
> **Never use `double` or `num` for money calculations in Dart.** IEEE-754 floating-point arithmetic introduces silent rounding errors (e.g. `100.05 - 0.10 = 99.95000000000002`).

```dart
// ❌ CRITICAL - Precision loss in financial calculation
double balance = 100.05;
double fee = 0.10;
double total = balance - fee; // 99.95000000000002 ❌ VIOLATION

// ✅ CORRECT - Exact arithmetic using Decimal package
import 'package:decimal/decimal.dart';

final balance = Decimal.parse('100.05');
final fee = Decimal.parse('0.10');
final total = balance - fee; // 99.95 ✅ Exact precision

// ✅ CORRECT - Integer smallest currency unit (e.g. cents)
final balanceCents = 10005; // 100.05 USD
final feeCents = 10;
final totalCents = balanceCents - feeCents; // 9995 cents
```

### SEC-FLUTTER-02: Credential & Secret Hygiene (OWASP M1)

> [!CAUTION]
> Dart code is compiled into the app bundle but string literals remain trivially recoverable with `strings` or a decompiler. Anything committed to the repository must be assumed public.

```dart
// ❌ CRITICAL - Hardcoded secrets in Dart source
class ApiConfig {
  static const apiKey = 'sk_live_51H8xQ2eZvKYlo2C'; // ❌ Extractable from the binary
  static const basicAuth = 'Basic ZGVtbzpwQHNzdzByZA=='; // ❌ Base64 is not encryption
}

// ❌ CRITICAL - Secrets committed to pubspec.yaml or .env tracked by git
// pubspec.yaml
//   sentry_dsn: https://abc123@o1.ingest.sentry.io/456  ❌ VIOLATION

// ✅ CORRECT - Injected at build time, never committed
// flutter build apk --dart-define-from-file=secureFiles/env.prod.json
class ApiConfig {
  static const apiKey = String.fromEnvironment('API_KEY');
  static const baseUrl = String.fromEnvironment('BASE_URL');
}

// ✅ CORRECT - Runtime secrets fetched after authentication, held only in secure storage
final token = await secureStorage.read(key: 'jwt_token');
```

**Audit checklist**: scan `lib/**/*.dart`, `pubspec.yaml`, `*.json`, and `android/app/src/**` for
high-entropy literals, `sk_`/`pk_`/`AIza`/`ghp_` prefixes, JWTs (`eyJ...`), private key blocks, and
credentials embedded in URLs. Verify `secureFiles/` is listed in `.gitignore`.

### SEC-FLUTTER-03: Network Security & SSL Pinning

> [!CAUTION]
> Disabling certificate verification via `badCertificateCallback` leaves the application vulnerable to Man-In-The-Middle (MITM) attacks.

```dart
// ❌ CRITICAL - SSL verification bypass in production code
(dio.httpClientAdapter as IOHttpClientAdapter).onHttpClientCreate = (client) {
  client.badCertificateCallback = (cert, host, port) => true; // ❌ CRITICAL VULNERABILITY!
  return client;
};

// ✅ CORRECT - Enforce Certificate Pinning via SecurityContext
final SecurityContext context = SecurityContext(withTrustedRoots: false);
final List<int> certBytes = await rootBundle.load('assets/certs/api_cert.pem').then((b) => b.buffer.asUint8List());
context.setTrustedCertificatesBytes(certBytes);

final HttpClient httpClient = HttpClient(context: context);
```

### SEC-FLUTTER-04: Privacy & Screen Masking

Mask sensitive data in logs and blur the application screen when moving to the background to prevent sensitive balance or card snapshots in the OS App Switcher.

```dart
// ❌ CRITICAL - PII leakage in logger
AppLogger.d('Auth success token: $accessToken, card: $cardNumber'); // ❌ PII in log!

// ✅ CORRECT - Masked logging
AppLogger.d('Transaction processed for card: ${cardNumber.maskCardNumber()}');

// ✅ CORRECT - App Switcher privacy overlay when app is paused
@override
void didChangeAppLifecycleState(AppLifecycleState state) {
  if (state == AppLifecycleState.inactive || state == AppLifecycleState.paused) {
    _showPrivacyShieldOverlay();
  } else if (state == AppLifecycleState.resumed) {
    _removePrivacyShieldOverlay();
  }
}
```

### SEC-FLUTTER-05: Secure Local Storage (`flutter_secure_storage`)

> [!CAUTION]
> `SharedPreferences` stores data in unencrypted plaintext on disk (XML on Android, Plist on iOS). Any rooted device or local backup can extract sensitive tokens immediately.

```dart
// ❌ CRITICAL - Plaintext SharedPreferences for access tokens
final prefs = await SharedPreferences.getInstance();
await prefs.setString('jwt_token', token); // ❌ VIOLATION!

// ✅ CORRECT - Hardware-backed secure storage (Keystore on Android, Keychain on iOS)
final secureStorage = const FlutterSecureStorage(
  aOptions: AndroidOptions(encryptedSharedPreferences: true),
  iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
);

await secureStorage.write(key: 'jwt_token', value: token);
```

### SEC-FLUTTER-06: Cryptographic Strength (OWASP M10)

> [!CAUTION]
> MD5 and SHA-1 are collision-broken and must never be used for integrity, signatures, or password derivation. ECB mode leaks plaintext structure. A static or hardcoded IV destroys the security of CBC and GCM alike.

```dart
// ❌ CRITICAL - Broken hashing and unauthenticated, deterministic encryption
import 'package:crypto/crypto.dart';

final digest = md5.convert(utf8.encode(pin)).toString(); // ❌ MD5 is collision-broken
final sha1Sig = sha1.convert(payload).toString();        // ❌ SHA-1 is deprecated

final encrypter = Encrypter(AES(key, mode: AESMode.ecb)); // ❌ ECB leaks patterns
final iv = IV.fromUtf8('0000000000000000');               // ❌ Static IV

// ✅ CORRECT - AES-256-GCM with a fresh random IV per operation
final iv = IV.fromSecureRandom(12);                        // ✅ Unique per encryption
final encrypter = Encrypter(AES(key, mode: AESMode.gcm));  // ✅ Authenticated encryption
final encrypted = encrypter.encrypt(plaintext, iv: iv);

// ✅ CORRECT - SHA-256+ for integrity
final digest = sha256.convert(utf8.encode(payload)).toString();

// ✅ CORRECT - Never roll your own key derivation; use a memory-hard KDF
//    and never derive keys from device identifiers or timestamps.
```

**Audit checklist**: ban `md5`, `sha1`, `DES`, `RC4`, `AESMode.ecb`. Require IVs from
`IV.fromSecureRandom` (never a literal). Keys must originate from the platform keystore or a
proper KDF, never from `DateTime.now()`, a device id, or a hardcoded string.

---

## 🍎 iOS Fintech Security Rules

### SEC-IOS-01: Financial Precision (Strict Decimal)

> [!CAUTION]
> **Never use `Double` or `Float` for money or currency calculations in Swift.** Binary floating-point representation causes arithmetic inaccuracy (e.g., `100.05 - 0.10 != 99.95`). Always use `Decimal` or integer cents (`Int64`).

```swift
// ❌ CRITICAL - IEEE-754 precision loss
let balance: Double = 100.05
let fee: Double = 0.10
let total = balance - fee // ❌ 99.95000000000000284217...

// ✅ CORRECT - Exact arithmetic using Foundation.Decimal
let balance = Decimal(string: "100.05")!
let fee = Decimal(string: "0.10")!
let total = balance - fee // ✅ Exact 99.95

// ✅ CORRECT - Smallest currency unit (cents)
let balanceCents: Int64 = 10005
let feeCents: Int64 = 10
let totalCents = balanceCents - feeCents // ✅ 9995 cents
```

### SEC-IOS-02: Credential & Secret Hygiene (OWASP M1)

> [!CAUTION]
> Swift string literals survive compilation and are recoverable from the `__TEXT` segment with `strings` or Hopper. `.xcconfig` files and Tuist manifests are plain text in the repository.

```swift
// ❌ CRITICAL - Hardcoded secrets in Swift source
enum ApiConfig {
    static let apiKey = "sk_live_51H8xQ2eZvKYlo2C"   // ❌ Recoverable from __TEXT
    static let hmacSecret = "s3cr3t_signing_key"     // ❌ VIOLATION
}

// ❌ CRITICAL - Secrets committed in build configuration
// Config/Release.xcconfig
//   SENTRY_DSN = https://abc123@o1.ingest.sentry.io/456   ❌ VIOLATION

// ✅ CORRECT - Injected at build time from an untracked xcconfig, surfaced via Info.plist
enum ApiConfig {
    static var apiKey: String {
        guard let value = Bundle.main.object(forInfoDictionaryKey: "API_KEY") as? String else {
            fatalError("API_KEY missing — check secureFiles/ bootstrap")
        }
        return value
    }
}

// ✅ CORRECT - Runtime credentials live only in the Keychain, never in source
let token = try keychain.read(key: "auth_token")
```

**Audit checklist**: scan `**/*.swift`, `*.xcconfig`, `Project.swift`, `Tuist.swift`, and
`Info.plist` for high-entropy literals, `sk_`/`AIza`/`ghp_` prefixes, JWTs (`eyJ...`),
`-----BEGIN PRIVATE KEY-----` blocks, and credentials in URLs. Verify that any `.xcconfig`
carrying secrets is git-ignored and sourced from `secureFiles/`.

### SEC-IOS-03: Network Security & TLS / SSL Pinning

> [!CAUTION]
> Bypassing SSL validation via `serverTrustPolicy` closures or disabling ATS (`NSAllowsArbitraryLoads = true`) introduces severe MITM vulnerabilities.

```swift
// ❌ CRITICAL - Disabling ATS or trusting invalid certificates
// Info.plist: NSAllowsArbitraryLoads = true ❌ VIOLATION
func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge) async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
    return (.useCredential, URLCredential(trust: challenge.protectionSpace.serverTrust!)) // ❌ Blind trust!
}

// ✅ CORRECT - Strict public key / certificate pinning using URLSessionDelegate or TrustKit
func urlSession(_ session: URLSession, didReceive challenge: URLAuthenticationChallenge) async -> (URLSession.AuthChallengeDisposition, URLCredential?) {
    guard let serverTrust = challenge.protectionSpace.serverTrust else {
        return (.cancelAuthenticationChallenge, nil)
    }
    let isValid = CertificatePinner.shared.validate(serverTrust: serverTrust, domain: challenge.protectionSpace.host)
    return isValid ? (.useCredential, URLCredential(trust: serverTrust)) : (.cancelAuthenticationChallenge, nil)
}
```

### SEC-IOS-04: Privacy & App Switcher Screen Masking

Mask sensitive data in logs (zero card numbers, CVVs, or unmasked PINs) and obscure the UI in the App Switcher when the app transitions out of `.active`.

```swift
// ❌ CRITICAL - Sensitive auth token or card leaked in log
logger.debug("Received token: \(authToken), card: \(cardPan)") // ❌ PII in log!

// ✅ CORRECT - Masked log
logger.debug("Payment processed for card: \(cardPan.maskPan())")

// ✅ CORRECT - App Switcher privacy shield in SwiftUI root
struct MainAppView: View {
    @Environment(\.scenePhase) private var scenePhase
    @State private var showPrivacyShield = false

    var body: some View {
        RootContentView()
            .overlay {
                if showPrivacyShield {
                    PrivacyShieldOverlayView()
                }
            }
            .onChange(of: scenePhase) { _, newPhase in
                showPrivacyShield = (newPhase != .active)
            }
    }
}
```

### SEC-IOS-05: Secure Local Storage & Keychain (`SecureCacheStore`)

> [!CAUTION]
> `UserDefaults` stores unencrypted plist data in application sandboxes, vulnerable to jailbreak extraction or unencrypted device backups. Auth tokens, keys, and biometrics must live in the iOS Keychain.

```swift
// ❌ CRITICAL - Plaintext UserDefaults for auth credentials
UserDefaults.standard.set(jwtToken, forKey: "auth_token") // ❌ VIOLATION

// ✅ CORRECT - SecureCacheStore backed by iOS Keychain Services
import Security

public final class KeychainSecureCacheStore: SecureCacheStoreProtocol {
    public func save(key: String, data: Data) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
        SecItemDelete(query as CFDictionary)
        let status = SecItemAdd(query as CFDictionary, nil)
        guard status == errSecSuccess else { throw KeychainError.saveFailed(status) }
    }
}
```

### SEC-IOS-06: Cryptographic Strength (OWASP M10)

> [!CAUTION]
> CommonCrypto's `CC_MD5` and `CC_SHA1` are collision-broken and deprecated. Prefer Apple CryptoKit, which offers authenticated encryption by default and makes nonce reuse hard to express.

```swift
// ❌ CRITICAL - Broken hashing and unauthenticated, deterministic encryption
import CommonCrypto

var digest = [UInt8](repeating: 0, count: Int(CC_MD5_DIGEST_LENGTH))
CC_MD5(data.bytes, CC_LONG(data.count), &digest)          // ❌ MD5 is collision-broken

CCCrypt(UInt32(kCCEncrypt), UInt32(kCCAlgorithmAES),
        UInt32(kCCOptionECBMode), ...)                     // ❌ ECB leaks plaintext structure

// ✅ CORRECT - CryptoKit AES-GCM with a fresh nonce per operation
import CryptoKit

let key = SymmetricKey(size: .bits256)
let nonce = AES.GCM.Nonce()                                // ✅ Unique per encryption
let sealed = try AES.GCM.seal(plaintext, using: key, nonce: nonce)
let reopened = try AES.GCM.open(sealed, using: key)        // ✅ Authenticated — tampering throws

// ✅ CORRECT - SHA-256+ for integrity
let hash = SHA256.hash(data: payload)

// ✅ CORRECT - Keys generated in, and never leaving, the Secure Enclave where possible
let privateKey = try SecureEnclave.P256.Signing.PrivateKey()
```

**Audit checklist**: ban `CC_MD5`, `CC_SHA1`, `kCCAlgorithmDES`, `kCCAlgorithmRC4`, and
`kCCOptionECBMode`. Require `AES.GCM.Nonce()` per operation — never a stored or constant nonce.
Keys must come from `SymmetricKey(size:)`, the Keychain, or the Secure Enclave, never from a
literal, a device identifier, or a timestamp.

---

## 📥 Input Specifications

This skill accepts:
1. **Git Diff**: A diff stream between branches or commits (`git diff origin/main...HEAD` or `git diff origin/develop...HEAD`).
2. **Commit ID**: A specific commit hash (`git show <COMMIT_ID>`).
3. **Pasted Code Snippet**: Code block for pre-commit verification.

---

## 📤 Output Format

Your audit response **MUST** follow this standardized structure:

```markdown
### 🛡️ Security Audit Report

**Target Platform**: 🤖 Android Native / 💙 Flutter / 🍎 iOS Native
**Audit Status**: ✅ PASSED / ❌ FAILED (Blockers Found)

#### ⚠️ OWASP Mobile Top 10 (2024) Compliance Table

| Risk Category | Status | Target File / Area | Notes |
| :--- | :--- | :--- | :--- |
| **M1: Improper Credential Usage** | ✅ / ❌ | | Zero hardcoded keys or secrets |
| **M2: Inadequate Supply Chain** | ✅ / ❌ | | Pinned dependency versions |
| **M3: Insecure Auth/Authorization** | ✅ / ❌ | | Server-side authorization |
| **M4: Insufficient Input Validation** | ✅ / ❌ | | Sanitized inputs, deeplink validation |
| **M5: Insecure Communication** | ✅ / ❌ | | TLS 1.2+, SSL Pinning, no bypasses |
| **M6: Inadequate Privacy Controls** | ✅ / ❌ | | Zero PII in logs, screen privacy overlay |
| **M7: Insufficient Binary Protections**| ✅ / ❌ | | Symbol stripping / Obfuscation enabled |
| **M8: Security Misconfiguration** | ✅ / ❌ | | Non-debuggable release, no cleartext ATS |
| **M9: Insecure Data Storage** | ✅ / ❌ | | `flutter_secure_storage` / Keystore / Keychain |
| **M10: Insufficient Cryptography** | ✅ / ❌ | | AES-256-GCM, SHA-256+, Decimal precision |

#### 🚨 Security Blockers (🔴 Must Fix Immediately)
- **[File:Line]**: [Vulnerability description] → [Required remediation]

#### 💡 Security Recommendations (🟡 Best Practices)
- **[File:Line]**: [Suggestion for defense-in-depth]
```
