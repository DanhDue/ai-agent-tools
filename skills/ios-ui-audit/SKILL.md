---
name: ios-ui-audit
description: Audits SwiftUI and iOS UI code for body re-evaluation efficiency, state hoisting, Task lifecycle cancellation, AppUIKit design tokens, and Slang-style localization.
---

# iOS UI Audit Skill (SwiftUI)

> [!IMPORTANT]
> **Role**: You are a Senior iOS UI & Performance Architect. Your mandate is to ensure that all SwiftUI Views adhere to the highest rendering performance and architecture standards: eliminating unnecessary body re-evaluations, enforcing state hoisting (dumb views), ensuring deterministic async `Task` cancellation, adhering strictly to `AppUIKit` design tokens, and consuming typed Slang-style localization accessors.

---

## 📑 Table of Contents

1. [Inspection Matrix](#-inspection-matrix)
2. [Execution Workflow & Diagram](#-execution-workflow--diagram)
3. [Core iOS UI Rules](#-core-ios-ui-rules)
   - [UI-IOS-01: Body Re-evaluation & View Decomposition](#ui-ios-01-body-re-evaluation--view-decomposition)
   - [UI-IOS-02: State Hoisting & Dumb Presentation](#ui-ios-02-state-hoisting--dumb-presentation)
   - [UI-IOS-03: Task Lifecycle & Cancellation](#ui-ios-03-task-lifecycle--cancellation)
   - [UI-IOS-04: Design System Token Adherence (`AppUIKit`)](#ui-ios-04-design-system-token-adherence-appuikit)
   - [UI-IOS-05: Typed Localization & String Hygiene](#ui-ios-05-typed-localization--string-hygiene)
4. [Input Specifications](#-input-specifications)
5. [Output Format](#-output-format)

---

## 🔍 Inspection Matrix

| Rule ID | Category | What It Actually Checks | Severity |
| :--- | :--- | :--- | :--- |
| **UI-IOS-01** | **Body Performance** | Flags expensive computations, allocations, or DateFormatter instantiation inside `var body`. Mandates subview extraction into dedicated `struct: View` (not private helper methods returning `some View`). | 🔴 Blocker / 🟡 Warning |
| **UI-IOS-02** | **State Hoisting** | Mandates separation of ViewModel and Dumb View. Views observe `State` and dispatch `Action` via `onAction(_:)`. Views must not execute business logic or mutate data directly. | 🔴 Blocker |
| **UI-IOS-03** | **Task Cancellation** | Enforces `.task` modifier for view-tied async operations. ViewModel running effect tasks must be retained in a cancellable `Task` and cancelled when superseded by a new action. | 🔴 Blocker |
| **UI-IOS-04** | **Theming & Design Tokens** | Strictly bans hardcoded hex colors (`Color(hex: ...)`), arbitrary font sizes, and ad-hoc styling. Mandates semantic tokens from `Packages/AppUIKit` (`Color.app...`, `Font.app...`). | 🟡 Warning |
| **UI-IOS-05** | **Typed Localization** | Strictly bans hardcoded raw string literals for user-facing UI text. Enforces `@Environment(\.t) private var t: Translations` or `t.[feature].[key]`. Keys must be `camelCase`. | 🔴 Blocker |

---

## 📊 Execution Workflow & Diagram

```mermaid
flowchart TD
    START(["Input: SwiftUI View Files in Diff"]) --> SCAN["Scan struct: View Declarations & var body"]

    SCAN --> CHECK_LOGIC{"Contains Business Logic or<br/>Direct Model Mutation?"}
    CHECK_LOGIC -->|Yes| FLAG_LOGIC["🔴 Flag: State Hoisting Breach (UI-IOS-02)"]
    CHECK_LOGIC -->|Pure Presentation| CHECK_TASK

    FLAG_LOGIC --> CHECK_TASK

    CHECK_TASK{"Async Work without Task Cancellation?<br/>(Task.init without lifecycle hook)"}
    CHECK_TASK -->|Uncancelled Task| FLAG_TASK["🔴 Flag: Task Lifecycle Leak (UI-IOS-03)"]
    CHECK_TASK -->|Safe .task / cancelled| CHECK_STRINGS

    FLAG_TASK --> CHECK_STRINGS

    CHECK_STRINGS{"Contains Raw String Literals<br/>(Text('Hello World'))?"}
    CHECK_STRINGS -->|Raw String in UI| FLAG_STRINGS["🔴 Flag: Missing Typed Localization (UI-IOS-05)"]
    CHECK_STRINGS -->|Uses t.[module].[key]| CHECK_THEME

    FLAG_STRINGS --> CHECK_THEME

    CHECK_THEME{"Scan for Hardcoded Colors<br/>(Color(hex: ...) or Color(red:...))"}
    CHECK_THEME -->|Found Hardcoded Color| FLAG_THEME["🟡 Flag: Design Token Violation (UI-IOS-04)"]
    CHECK_THEME -->|Uses AppUIKit Tokens| CHECK_BODY

    FLAG_THEME --> CHECK_BODY

    CHECK_BODY{"Heavy Computation or Helper Methods<br/>returning some View inside body?"}
    CHECK_BODY -->|Found View Smells| FLAG_BODY["🟡 Flag: Body Performance Smell (UI-IOS-01)"]
    CHECK_BODY -->|Clean Subview Structs| SYNTHESIZE

    FLAG_BODY --> SYNTHESIZE["Synthesize iOS UI Audit Findings"]
    SYNTHESIZE --> REPORT["Generate iOS UI Audit Report"]
    REPORT --> END(["Audit Complete"])
```

---

## 🎨 Core iOS UI Rules

### UI-IOS-01: Body Re-evaluation & View Decomposition

> [!CAUTION]
> In SwiftUI, `var body` can be called 60 to 120 times per second during animations or scrolling. Any object allocation or heavy calculation inside `body` causes frame drops.

```swift
// ❌ BAD - Heavy computation in body; helper method prevents SwiftUI render caching
struct WalletView: View {
    let transactions: [Transaction]

    var body: some View {
        VStack {
            let total = transactions.reduce(Decimal.zero) { $0 + $1.amount } // ❌ Computation in body
            Text("Total: \(total)")
            transactionRowView // ❌ Helper method returning some View
        }
    }

    private var transactionRowView: some View { // ❌ Re-evaluates on every parent change
        ForEach(transactions) { item in Text(item.title) }
    }
}

// ✅ CORRECT - Isolated subview struct allows SwiftUI to memoize body diffing
struct WalletView: View {
    let state: WalletState

    var body: some View {
        VStack {
            WalletTotalHeader(total: state.formattedTotal)
            TransactionListView(transactions: state.transactions)
        }
    }
}

struct TransactionListView: View {
    let transactions: [Transaction]

    var body: some View {
        ForEach(transactions) { item in
            TransactionRow(item: item)
        }
    }
}
```

---

### UI-IOS-02: State Hoisting & Dumb Presentation

SwiftUI Views must be purely presentational ("dumb"). User intent flows outward via `onAction(_:)`.

```swift
// ❌ BAD - View creates UseCase and performs side-effects directly
struct TransferView: View {
    @State private var amount = ""

    var body: some View {
        Button("Transfer") {
            // Direct repository/network call inside View
            Task { await TransferRepositoryImpl().transfer(amount) }
        }
    }
}

// ✅ CORRECT - Dumb view binds to State and forwards Action
struct TransferView: View {
    let state: TransferState
    let onAction: (TransferAction) -> Void

    var body: some View {
        Button(t.transfer.actionTitle) {
            onAction(.submitTransfer)
        }
    }
}
```

---

### UI-IOS-03: Task Lifecycle & Cancellation

> [!CAUTION]
> Asynchronous operations triggered by views must be bound to the SwiftUI view lifecycle via `.task` to ensure automatic cancellation when the user navigates away.

```swift
// ❌ BAD - Detached Task continues running even after view is dismissed
struct AccountView: View {
    @StateObject var viewModel: AccountViewModel

    var body: some View {
        Text(viewModel.state.balance)
            .onAppear {
                Task { await viewModel.fetchBalance() } // ❌ Leaks if user pops back
            }
    }
}

// ✅ CORRECT - .task modifier automatically cancels when View disappears
struct AccountView: View {
    @StateObject var viewModel: AccountViewModel

    var body: some View {
        Text(viewModel.state.balance)
            .task {
                await viewModel.fetchBalance()
            }
    }
}
```

---

### UI-IOS-04: Design System Token Adherence (`AppUIKit`)

Never hardcode arbitrary hex colors or font sizes. Always reference `AppUIKit` design tokens.

```swift
// ❌ BAD - Hardcoded hex colors and font sizes break Dark Mode and branding
Text("Account Balance")
    .foregroundColor(Color(hex: "1E88E5")) // ❌ Hardcoded color
    .font(.system(size: 16)) // ❌ Hardcoded typography

// ✅ CORRECT - Semantic tokens from AppUIKit
Text(t.wallet.balanceTitle)
    .foregroundColor(Color.app.textPrimary)
    .font(Font.app.titleMedium)
```

---

### UI-IOS-05: Typed Localization & String Hygiene

User-facing strings must never be hardcoded as raw string literals. Consume typed accessors generated from `.xcstrings`.

```swift
// ❌ BAD - Raw string literal
Text("Send Money") // ❌ VIOLATION

// ✅ CORRECT - Slang-style typed translation accessor
@Environment(\.t) private var t: Translations

Text(t.transfer.sendMoney)
```

---

## 📥 Input Specifications

This skill accepts:
1. **Git Diff**: A diff stream containing SwiftUI `.swift` files (`git diff origin/develop...HEAD`).
2. **Commit ID**: A specific commit hash (`git show <COMMIT_ID>`).
3. **File Path**: Direct path to any SwiftUI View file (`Packages/AppUIKit/...` or `Features/.../Presentation/...`).

---

## 📤 Output Format

Your audit response **MUST** follow this standardized structure:

```markdown
### 🎨 iOS UI Audit Report (SwiftUI)

**Audit Status**: ✅ PASSED / ❌ FAILED (Blockers Found)

#### 📋 SwiftUI Performance & Design Check Table

| Check Area | Status | Target View / Area | Details |
| :--- | :--- | :--- | :--- |
| **UI-IOS-01: Body Performance** | ✅ / ❌ | | Subview structs, zero computations in body |
| **UI-IOS-02: State Hoisting** | ✅ / ❌ | | Dumb view, actions dispatched via onAction |
| **UI-IOS-03: Task Cancellation** | ✅ / ❌ | | .task modifier, lifecycle cancellation |
| **UI-IOS-04: AppUIKit Tokens** | ✅ / ❌ | | Semantic Color.app, Font.app tokens |
| **UI-IOS-05: Typed Localization**| ✅ / ❌ | | t.[module].[key], zero raw string literals |

#### 🚨 iOS UI Blockers (🔴 Must Fix Immediately)
- **[File:Line]**: [Re-evaluation / Task leak / Hardcoded string defect] → [Required remediation]

#### 💡 iOS UI Optimizations (🟡 Suggestions)
- **[File:Line]**: [Layout or theming improvement recommendation]
```
