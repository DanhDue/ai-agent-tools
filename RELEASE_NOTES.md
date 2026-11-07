# Release Notes: d3nexus v1.26.3

**Release Date:** November 08, 2026  
**Version:** `1.26.3`  
**Git Tag:** `v1.26.3`, `d3nexus--v1.26.3`

---

## Executive Summary

`v1.26.3` delivers full integration of **Kiro CLI Quota Provider** (`check-quota kiro`), establishes the **Local Profile Isolation & Remediation Rules** (preventing Attention Dilution / "Lost in the Middle" while protecting host macOS services and eliminating stale RAM process overwrites), brings the **Dreamy Purple Theme & Mascot 👻** for Kiro, and introduces **4-Category Account Filtering** with streamlined statistics across both the Web Dashboard and Terminal CLI.

---

## Key Highlights

### 1. Kiro CLI Quota Provider Integration
- **3rd Core AI Provider**: Integrates `kiro-cli` alongside Claude Code and OpenAI Codex in multi-profile quota management.
- **AWS Token & Credits Extraction**: Directly parses AWS CodeWhisperer `GetUsageLimits` tokens, Monthly Credits Pool (used, limit, remaining, countdown timer, model tier, and overages).
- **Commands**:
  - `check-quota kiro`: Prints interactive terminal card with progress bar, remaining quota, and model details.
  - `check-quota all --providers`: Displays summary across all 3 AI Providers (Claude, Codex, Kiro).
- **Unit Test Suite**: 7 unit tests in `tests/test_kiro_quota.py` verifying response parsing, color thresholds, offline fallback, and unauthenticated state handling.

### 2. Local Profile Isolation & Anti-Contamination Rules
- **Anti-Attention Dilution Architecture**: Rules for profile remediation and OS Keychain boundaries are kept localized in `.agents/rules/profile_isolation_rules.md` and `skills/audit-account-block/references/profile-isolation-and-remediation.md` (progressive disclosure) to prevent context pollution and "Lost in the Middle" during regular coding tasks.
- **Process Fencing (Zero Stale RAM Overwrites)**: Automatically checks and terminates resident Antigravity IDE / agy processes (`pkill -9 -f antigravity_homes/<profile>`) before modifying `state.vscdb`, eliminating stale Electron RAM from continually overwriting repaired database state.
- **Stale `signedOut` Token Elimination**: Purges `antigravityUnifiedStateSync.oauthToken` in `ItemTable` to prevent silent fallback to the root/default profile.
- **Atomic Launch Window**: Establishes safe launch isolation in `ag_run()` via temporary 2.5s search-list promotion of profile keychain followed by automated rollback to `login.keychain-db`, preserving macOS host daemons (AirDrop, Apple ID, Wi-Fi, browser cookies).
- **Rogue Symlink Defense**: Outlaws unanchored wildcard `antigravity)` in favor of `*antigravity*) ;;`, preserving `.gemini/antigravity*` physical directory independence.

### 3. Dreamy Purple Theme & Mascot 👻 for Kiro
- **Kiro Brand Identity**: Dresses Kiro CLI in a dreamy purple theme (`text-purple-300`, glow effects) with Kiro's cute ghost mascot 👻 in the title, tier badges (`👻 KIRO STUDENT`, `AI PROVIDER`), and monthly credits pool bar.
- **ANSI Terminal Styling**: Synchronizes matching purple ANSI colors and mascot icon in terminal CLI outputs.

### 4. 4-Category Account Filtering & Streamlined Statistics
- **Clear Categorization**: Groups all 26 accounts into 4 distinct groups:
  1. `3 Providers` (Claude, Codex, Kiro)
  2. `12 Active Profiles`
  3. `4 Needed Login Profiles`
  4. `7 Blocked Profiles`
- **Streamlined Badges**: Header buttons and badges show clean, concise counts without redundant name listings.
- **Terminal CLI Flags**: Supports `--providers`, `--active`, `--login`, `--blocked` in `check-quota all`.

---

## Verifications & Quality Gates Passed

- `bash scripts/verify.sh`: 🟢 **PASS — safe to publish** (Sections 1–17, all 41 test suites green)
- `tests/test_kiro_quota.py`: 🟢 **PASS** (7/7 unit tests passing)
- `tests/test_agy_quota.py`: 🟢 **PASS** (9/9 unit tests passing)
