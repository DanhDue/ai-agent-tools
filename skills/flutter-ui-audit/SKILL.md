---
name: flutter-ui-audit
description: Audits Flutter UI code for widget rebuild optimization, const discipline, state hoisting, controller disposal, and design token adherence.
---

# Flutter UI Audit Skill

> [!IMPORTANT]
> **Role**: You are a Senior Flutter UI & Performance Architect. Your mandate is to ensure that all Flutter Widgets adhere to the highest rendering performance standards: eliminating unnecessary widget rebuilds, enforcing `const` constructors, hoisting state away from presentation, ensuring 100% controller disposal, and strictly adhering to centralized design tokens.

---

## 📑 Table of Contents

1. [Inspection Matrix](#-inspection-matrix)
2. [Execution Workflow & Diagram](#-execution-workflow--diagram)
3. [Core Flutter UI Rules](#-core-flutter-ui-rules)
   - [UI-FLUTTER-01: Rebuild Optimization & `const` Discipline](#ui-flutter-01-rebuild-optimization--const-discipline)
   - [UI-FLUTTER-02: State Hoisting & Dumb Presentation](#ui-flutter-02-state-hoisting--dumb-presentation)
   - [UI-FLUTTER-03: Controller & Resource Disposal](#ui-flutter-03-controller--resource-disposal)
   - [UI-FLUTTER-04: Theming & Design System Token Adherence](#ui-flutter-04-theming--design-system-token-adherence)
   - [UI-FLUTTER-05: Layout Hygiene & Overflow Protection](#ui-flutter-05-layout-hygiene--overflow-protection)
4. [Input Specifications](#-input-specifications)
5. [Output Format](#-output-format)

---

## 🔍 Inspection Matrix

| Rule ID | Category | What It Actually Checks | Severity |
| :--- | :--- | :--- | :--- |
| **UI-FLUTTER-01** | **Rebuild Optimization** | Flags missing `const` constructors on immutable widgets. Flags monolithic `build()` methods; enforces `BlocBuilder(buildWhen: ...)` or `BlocSelector` to isolate subtree rebuilds. | 🔴 Blocker / 🟡 Warning |
| **UI-FLUTTER-02** | **State Hoisting** | Mandates separation of Container (receives BLoC state) and Presentational Widget `(onAction: () -> Unit)`. Widgets must NOT instantiate BLoCs in `build()` or perform business logic. | 🔴 Blocker |
| **UI-FLUTTER-03** | **Resource Disposal** | Enforces `.dispose()` inside `State.dispose()` for `TextEditingController`, `AnimationController`, `ScrollController`, `PageController`, `FocusNode`, and `StreamSubscription`. | 🔴 Blocker |
| **UI-FLUTTER-04** | **Theming & Design Tokens** | Strictly bans hardcoded hex colors (`Color(0xFF...)`) and ad-hoc inline text styling. Mandates `Theme.of(context)`, `ThemeTailor`, or centralized `AppColors` / `AppTextStyles`. | 🟡 Warning |
| **UI-FLUTTER-05** | **Layout Hygiene** | Flags unconstrained flex layouts (`ListView` inside `Column` without `Expanded`/`Flexible`). Mandates `SafeArea` and scrollable wrappers (`SingleChildScrollView`) for forms to prevent overflow. | 🟡 Warning |

---

## 📊 Execution Workflow & Diagram

```mermaid
flowchart TD
    START(["Input: Flutter Widget Files in Diff"]) --> SCAN["Scan Widget Classes & build() Methods"]

    SCAN --> CHECK_DISPOSE{"Is Widget a StatefulWidget?"}
    CHECK_DISPOSE -->|Yes| EVAL_DISPOSE{"Are all Controllers & FocusNodes<br/>disposed in dispose()?"}
    EVAL_DISPOSE -->|Missing dispose()| FLAG_DISPOSE["🔴 Flag: Resource Leak (UI-FLUTTER-03)"]
    EVAL_DISPOSE -->|All Disposed| CHECK_HOIST
    CHECK_DISPOSE -->|No| CHECK_HOIST

    FLAG_DISPOSE --> CHECK_HOIST

    CHECK_HOIST{"Is Business Logic in Widget?<br/>(BLoC creation / API calls in build)"}
    CHECK_HOIST -->|Found Business Logic| FLAG_HOIST["🔴 Flag: State Hoisting Violation (UI-FLUTTER-02)"]
    CHECK_HOIST -->|Pure Presentation| CHECK_CONST

    FLAG_HOIST --> CHECK_CONST

    CHECK_CONST{"Are Immutable Widgets<br/>marked with const?"}
    CHECK_CONST -->|Missing const on literals| FLAG_CONST["🟡 Flag: Missing const Constructor (UI-FLUTTER-01)"]
    CHECK_CONST -->|Compliant const| CHECK_THEME

    FLAG_CONST --> CHECK_THEME

    CHECK_THEME{"Scan for Hardcoded Colors<br/>(Color(0xFF...))"}
    CHECK_THEME -->|Found Hardcoded Colors| FLAG_THEME["🟡 Flag: Design Token Breach (UI-FLUTTER-04)"]
    CHECK_THEME -->|Uses Theme Tokens| CHECK_LAYOUT

    FLAG_THEME --> CHECK_LAYOUT

    CHECK_LAYOUT{"Check Layout Boundaries<br/>(Flex overflows, missing SafeArea)"}
    CHECK_LAYOUT -->|Unbounded Layout Hazard| FLAG_LAYOUT["🟡 Flag: Layout Overflow Hazard (UI-FLUTTER-05)"]
    CHECK_LAYOUT -->|Safe Layout| SYNTHESIZE

    FLAG_LAYOUT --> SYNTHESIZE["Synthesize Flutter UI Audit Findings"]
    SYNTHESIZE --> REPORT["Generate Flutter UI Audit Report"]
    REPORT --> END(["Audit Complete"])
```

---

## 🎨 Core Flutter UI Rules

### UI-FLUTTER-01: Rebuild Optimization & `const` Discipline

> [!CAUTION]
> Widgets without `const` are re-instantiated on every single parent rebuild, creating unnecessary GC pressure and causing performance hitches on 120Hz displays.

```dart
// ❌ BAD - Re-instantiated on every build pass; BlocBuilder rebuilds entire page
@override
Widget build(BuildContext context) {
  return BlocBuilder<WalletBloc, WalletState>(
    builder: (context, state) {
      return Column(
        children: [
          Padding(
            padding: EdgeInsets.all(16.0), // ❌ Missing const
            child: Text('Recent Transactions'), // ❌ Missing const
          ),
          TransactionList(items: state.items),
        ],
      );
    },
  );
}

// ✅ CORRECT - const on all static widgets; buildWhen isolates rebuilds
@override
Widget build(BuildContext context) {
  return Column(
    children: [
      const Padding(
        padding: EdgeInsets.all(16.0),
        child: Text('Recent Transactions'),
      ),
      BlocBuilder<WalletBloc, WalletState>(
        buildWhen: (previous, current) => previous.items != current.items,
        builder: (context, state) => TransactionList(items: state.items),
      ),
    ],
  );
}
```

---

### UI-FLUTTER-02: State Hoisting & Dumb Presentation

Widgets should be purely presentational ("dumb") and decoupled from business logic or direct asynchronous operations.

```dart
// ❌ BAD - Widget creates BLoC and calls API directly inside build
class WalletScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () async {
        // Direct repository call inside UI
        await sl<WalletRepository>().transferMoney(...);
      },
      child: const Text('Transfer'),
    );
  }
}

// ✅ CORRECT - Stateful container routes action to BLoC, pure presentation emits event
class WalletScreen extends StatelessWidget {
  const WalletScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return WalletContent(
      onTransfer: () => context.read<WalletBloc>().add(const TransferAction()),
    );
  }
}

class WalletContent extends StatelessWidget {
  final VoidCallback onTransfer;

  const WalletContent({super.key, required this.onTransfer});

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: onTransfer,
      child: const Text('Transfer'),
    );
  }
}
```

---

### UI-FLUTTER-03: Controller & Resource Disposal

> [!CAUTION]
> Undisposed controllers (`TextEditingController`, `AnimationController`, `ScrollController`, `FocusNode`) leak listeners and retain the entire widget element tree in memory indefinitely.

```dart
// ❌ CRITICAL - Leaking controller when widget is removed from tree
class InputWidget extends StatefulWidget {
  const InputWidget({super.key});

  @override
  State<InputWidget> createState() => _InputWidgetState();
}

class _InputWidgetState extends State<InputWidget> {
  final _controller = TextEditingController();
  final _focusNode = FocusNode();
  // ❌ Missing dispose() method! Memory leak!
}

// ✅ CORRECT - Deterministic resource cleanup in dispose()
class _InputWidgetState extends State<InputWidget> {
  late final TextEditingController _controller;
  late final FocusNode _focusNode;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    _focusNode = FocusNode();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }
}
```

---

### UI-FLUTTER-04: Theming & Design System Token Adherence

Never hardcode hex colors or custom font sizes directly in widgets. Always use centralized theme tokens (`Theme.of(context)` or `AppColors`).

```dart
// ❌ BAD - Hardcoded hex colors break dynamic branding and Dark Mode
Container(
  color: const Color(0xFF1E88E5), // ❌ Hardcoded color
  child: const Text(
    'Balance',
    style: TextStyle(fontSize: 16, color: Color(0xFF000000)), // ❌ Hardcoded style
  ),
)

// ✅ CORRECT - Themed tokens from ThemeData / ThemeTailor
Container(
  color: Theme.of(context).colorScheme.primary,
  child: Text(
    'Balance',
    style: Theme.of(context).textTheme.titleMedium,
  ),
)
```

---

### UI-FLUTTER-05: Layout Hygiene & Overflow Protection

Layouts must guard against screen size variations, orientation shifts, and soft keyboard appearance.

```dart
// ❌ BAD - Direct Column causes RenderFlex overflow on small screens or when keyboard opens
class LoginForm extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Column( // ❌ May overflow with keyboard
      children: [
        TextField(),
        TextField(),
        ElevatedButton(...),
      ],
    );
  }
}

// ✅ CORRECT - SafeArea and SingleChildScrollView protect against layout overflows
class LoginForm extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const TextField(),
            const SizedBox(height: 16),
            const TextField(),
            const SizedBox(height: 24),
            ElevatedButton(...),
          ],
        ),
      ),
    );
  }
}
```

---

## 📥 Input Specifications

This skill accepts:
1. **Git Diff**: A diff stream containing Flutter Widget `.dart` files (`git diff origin/develop...HEAD`).
2. **Commit ID**: A specific commit hash (`git show <COMMIT_ID>`).
3. **File Path**: Direct path to any Widget or Screen file (`packages/ui_kit/lib/widgets/...` or `features/.../presentation/...`).

---

## 📤 Output Format

Your audit response **MUST** follow this standardized structure:

```markdown
### 🎨 Flutter UI Audit Report

**Audit Status**: ✅ PASSED / ❌ FAILED (Blockers Found)

#### 📋 Flutter UI Performance & Design Check Table

| Check Area | Status | Target Widget / Area | Details |
| :--- | :--- | :--- | :--- |
| **UI-FLUTTER-01: Rebuild & const** | ✅ / ❌ | | const constructors, buildWhen isolation |
| **UI-FLUTTER-02: State Hoisting** | ✅ / ❌ | | Dumb widgets, BLoC event delegation |
| **UI-FLUTTER-03: Controller Disposal** | ✅ / ❌ | | All controllers & focus nodes disposed |
| **UI-FLUTTER-04: Theme Token Adherence** | ✅ / ❌ | | Theme.of(context), zero hardcoded colors |
| **UI-FLUTTER-05: Layout & Overflow Safety**| ✅ / ❌ | | SafeArea, SingleChildScrollView |

#### 🚨 Flutter UI Blockers (🔴 Must Fix Immediately)
- **[File:Line]**: [Rebuild / Disposal / Hoisting defect] → [Required remediation]

#### 💡 Flutter UI Optimizations (🟡 Suggestions)
- **[File:Line]**: [Theming or layout enhancement recommendation]
```
