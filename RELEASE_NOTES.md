# Release Notes: d3nexus v1.21.0

**Release Date:** November 01, 2026  
**Version:** `1.21.0`  
**Git Tag:** `v1.21.0`, `d3nexus--v1.21.0`

---

## Executive Summary

`v1.21.0` introduces a **30-second default safety delay buffer (offset)** for scheduled pre-warming daemons in the **Session Refresh Engine** (`refresh-session`). When a scheduled OS daemon wakes at a target reset minute (e.g., `05:00:00`), the engine sleeps for 30 seconds before sending its ping (`05:00:30`). This buffer absorbs remote AI cloud rate-limit worker clock skew and synchronization latency, guaranteeing that pre-warming pings land safely inside the fresh 100% quota window rather than burning into the expiring block. Manual on-demand pings remain instant with zero latency.

---

## Key Highlights

### 1. 30-Second Safety Delay Buffer (`skills/refresh-session/`)
- **Default 30s Buffer for Scheduled Runs**: `refresh_session.py schedule --time <time>` automatically schedules daemons with `--delay 30`.
- **Clock Skew & Quota Rollover Protection**: Remote server rate-limit workers (Anthropic/OpenAI) can experience 5–15s delays at minute boundaries. Sleeping 30s ensures the ping fires only after the fresh 5-hour rolling window is completely active.
- **Customizable Buffer**: Developers can customize the delay using `--delay <sec>` or `--offset <sec>` (e.g. `--delay 45`).
- **Immediate On-Demand Refreshes**: Manual invocations (`/refresh-session [claude|codex|all]`) default to `--delay 0` for immediate zero-latency pings.
- **Daemon Status Telemetry**: `schedule --status` inspects and reports the configured delay buffer (`• Delay buffer: 30s`).

### 2. Synchronized Documentation & Quick Guides
- **Bilingual Quick Guides**: Updated both [`docs/refresh-session-quick-guide.en.md`](docs/refresh-session-quick-guide.en.md) and [`docs/refresh-session-quick-guide.vi.md`](docs/refresh-session-quick-guide.vi.md) with delay buffer command cheat-sheets, CLI examples, natural language patterns, and architectural explanations.
- **Skill Documentation**: Updated [`skills/refresh-session/SKILL.md`](skills/refresh-session/SKILL.md) with delay buffer parameters and examples.

### 3. Expanded Unit Testing & Verification
- **31 Unit Tests**: Added 4 unit tests in [`test_refresh_session.py`](skills/refresh-session/resources/scripts/test_refresh_session.py) covering delay argument parsing defaults, custom delays, plist injection, and sleep execution.
- **16/16 Verification Sections**: Passed full repository verification in [`scripts/verify.sh`](scripts/verify.sh).

---

## Verifications & Quality Gates Passed

- `skills/refresh-session/resources/scripts/test_refresh_session.py`: 🟢 **PASS** (31/31 tests green)
- `ruff check`: 🟢 **PASS** (0 errors, 100% compliant)
- `scripts/verify.sh`: 🟢 **PASS — safe to publish** (16/16 sections green)
