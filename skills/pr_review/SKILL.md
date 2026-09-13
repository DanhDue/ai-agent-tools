---
name: pr_review
description: Performs comprehensive Pull Request reviews by orchestrating the platform-aware 3-Tier testing standard and the 4 specialized Category Audit Skills (Security, Architecture, UI, Code Health) via quality_check across Android, Flutter, and iOS projects.
---

# Pull Request Review Skill

> [!IMPORTANT]
> **Unified Architecture**: PR Review is powered by the Central Orchestrator **[`@quality_check`](../quality_check/SKILL.md)**.
> It combines the automated **3-Tier Testing Standard** (Flutter Melos / Android Gradle / iOS Tuist & SwiftPM) with the **4 Specialized Category Audit Skills** executed in parallel.

---

## 📑 Table of Contents

1. [Platform-Aware Inspection Matrix & Category Audit Delegation](#-platform-aware-inspection-matrix--category-audit-delegation)
2. [PR Review Lifecycle Diagram](#-pr-review-lifecycle-diagram)
3. [Input Methods](#-input-methods)
4. [Review Workflow](#-review-workflow)
5. [Unified Executive Quality Report Format](#-unified-executive-quality-report-format)

---

## 🔍 Platform-Aware Inspection Matrix & Category Audit Delegation

PR review delegates semantic code inspection to 4 focused specialist skills while concurrently validating the platform's 3-Tier suite:

| Inspection Pillar | Delegated Skill | Target Area & Focus | Severity |
| :--- | :--- | :--- | :--- |
| **Fintech & Security** | **[`@security-audit`](../security-audit/SKILL.md)** | OWASP Mobile Top 10 (2024), strictly `Decimal` (Dart/Swift) / `BigDecimal` (Kotlin), no PII in logs, secure storage, TLS/Cert pinning. | 🔴 Blocker |
| **Clean Architecture** | **[`@architecture-audit`](../architecture-audit/SKILL.md)** | Domain layer purity (zero framework imports), feature package isolation, MVI state immutability, concurrency discipline. | 🔴 Blocker |
| **UI & Performance** | **[`@flutter-ui-audit`](../flutter-ui-audit/SKILL.md)** (Flutter)<br>**[`@android-ui-audit`](../android-ui-audit/SKILL.md)** (Android)<br>**[`@ios-ui-audit`](../ios-ui-audit/SKILL.md)** (iOS) | Rebuild / recomposition / re-evaluation optimization, state hoisting, controller/.task disposal, design system tokens. | 🔴 Blocker / 🟡 Warning |
| **Code Health & Safety** | **[`@code-health-audit`](../code-health-audit/SKILL.md)** | Function sizing (<20 lines), param limits (<=2), strict ban on `!` / `!!` / `try!` force unwraps, clean logging. | 🔴 Blocker / 🟡 Warning |
| **Automated 3-Tier Gates** | **[`@quality_check`](../quality_check/SKILL.md)** | Tier A (Unit Tests), Tier B (Architecture Boundaries, AST & Linter), Tier C (Acceptance Harness & Integration Tests). | 🔴 Blocker |

---

## 📊 PR Review Lifecycle Diagram

```mermaid
flowchart TD
    START(["Trigger: @pr_review (Commit / PR Diff)"]) --> ROUTE["Route to @quality_check Engine"]

    ROUTE --> DETECT{"Detect Platform<br/>pubspec.yaml vs build.gradle vs Project.swift"}

    %% Flutter Track
    DETECT -->|Flutter Project| F_DISPATCH{"Flutter Dispatch"}
    subgraph F_TRACK_TESTS["Track 1: Flutter 3-Tier Automated Tests (Background)"]
        direction TB
        FT1["Tier A: melos test"]
        FT2["Tier B: melos analyze + check_module_boundaries.sh + check_license_header.sh"]
        FT3["Tier C: integration_test / acceptance"]
        FT1 --> FT2 --> FT3
    end

    subgraph F_TRACK_AUDITS["Track 2: Flutter Category Audits (Parallel Subagents)"]
        direction TB
        FA1["@security-audit (Flutter)"]
        FA2["@architecture-audit (Flutter)"]
        FA3["@flutter-ui-audit"]
        FA4["@code-health-audit (Dart)"]
    end

    F_DISPATCH ==> F_TRACK_TESTS
    F_DISPATCH ==> F_TRACK_AUDITS

    %% Android Track
    DETECT -->|Android Project| A_DISPATCH{"Android Dispatch"}
    subgraph A_TRACK_TESTS["Track 1: Android Gradle 3-Tier Automated Tests (Background)"]
        direction TB
        AT1["./gradlew check (Spotless auto-fix + Detekt + Tier A Tests)"]
        AT2["./gradlew :konsist-test:test apiCheck (Tier B Konsist & BCV)"]
        AT3["./scripts/acceptance_check.sh (Tier C Acceptance Harness)"]
        AT1 --> AT2 --> AT3
    end

    subgraph A_TRACK_AUDITS["Track 2: Android Category Audits (Parallel Subagents)"]
        direction TB
        AA1["@security-audit (Android)"]
        AA2["@architecture-audit (Android)"]
        AA3["@android-ui-audit"]
        AA4["@code-health-audit (Kotlin)"]
    end

    A_DISPATCH ==> A_TRACK_TESTS
    A_DISPATCH ==> A_TRACK_AUDITS

    %% iOS Track
    DETECT -->|iOS Project| I_DISPATCH{"iOS Dispatch"}
    subgraph I_TRACK_TESTS["Track 1: iOS 3-Tier Automated Tests (Background)"]
        direction TB
        IT1["Tier A: swift test across Packages/* and Features/*"]
        IT2["Tier B: swiftlint + swiftformat + check_module_boundaries.sh + ArchTests"]
        IT3["Tier C: tuist generate + xcodebuild test"]
        IT1 --> IT2 --> IT3
    end

    subgraph I_TRACK_AUDITS["Track 2: iOS Category Audits (Parallel Subagents)"]
        direction TB
        IA1["@security-audit (iOS)"]
        IA2["@architecture-audit (iOS)"]
        IA3["@ios-ui-audit"]
        IA4["@code-health-audit (Swift)"]
    end

    I_DISPATCH ==> I_TRACK_TESTS
    I_DISPATCH ==> I_TRACK_AUDITS

    %% Aggregation
    F_TRACK_TESTS ==> SYNTHESIZE["Quality & Security Aggregator"]
    F_TRACK_AUDITS ==> SYNTHESIZE
    A_TRACK_TESTS ==> SYNTHESIZE
    A_TRACK_AUDITS ==> SYNTHESIZE
    I_TRACK_TESTS ==> SYNTHESIZE
    I_TRACK_AUDITS ==> SYNTHESIZE

    SYNTHESIZE --> REPORT["Render Unified Executive Quality Report"]
    REPORT --> CLEANUP{"Platform Cleanup"}
    CLEANUP -->|Android| C_JAVA["cleanup-java (pkill -9 java)"]
    CLEANUP -->|Flutter / iOS| C_DONE["Cleanup Done"]
    C_JAVA --> END(["Review Complete"])
    C_DONE --> END
```

---

## 📥 Input Methods

PR Review supports multiple input channels:

| Input Type | Description | Command / Usage |
| :--- | :--- | :--- |
| **Working Diff** | Review staged or uncommitted local changes | `@pr_review` (analyzes current `git diff`) |
| **Commit ID** | Review changes introduced by a specific commit | `git show <COMMIT_ID>` or `@pr_review commit=<COMMIT_ID>` |
| **PR Number / Diff** | Review Pull Request changes via GitHub CLI | `gh pr diff <PR_NUMBER> \| pbcopy` |
| **Branch Range** | Review changes against the base branch | `git diff origin/main...HEAD` or `git diff origin/develop...HEAD` |

---

## 🔄 Review Workflow

1. **Detect Platform**:
   - Check if workspace is Flutter (`pubspec.yaml`/`melos.yaml`), Android (`build.gradle.kts`/`settings.gradle.kts`), or iOS (`Project.swift`/`Tuist.swift`/`Package.swift`).
2. **Invoke Quality Orchestration via `@quality_check`**:
   - Run the automated 3-Tier suite in the background.
   - Concurrently inspect the diff with the 4 Category Audit skills via `dispatching-parallel-agents`:
     - `@security-audit`
     - `@architecture-audit`
     - **Flutter**: `@flutter-ui-audit` | **Android**: `@android-ui-audit` | **iOS**: `@ios-ui-audit`
     - `@code-health-audit`
3. **Run Acceptance Verification (Tier C)**:
   - For all PRs targeting `main`, `develop`, or release branches.
4. **Synthesize & Report**:
   - Aggregate test status, OWASP compliance, architectural gates, and code health metrics.
   - Assign clear verdict: 🟢 LGTM / 🟡 NEEDS WORK / 🔴 BLOCKED.
5. **Resource Cleanup**:
   - If Android: run `cleanup-java` (`pkill -9 java`).

---

## 📤 Unified Executive Quality Report Format

Refer to **[`@quality_check` Output Format](../quality_check/SKILL.md#-unified-executive-quality-report-format)** for the comprehensive report structure required for all Pull Request reviews.
