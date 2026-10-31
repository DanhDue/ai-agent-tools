---
name: refresh-session
description: Pings Claude Code and Codex CLIs or configures daily scheduled daemons to refresh and pre-warm 5-hour rolling session windows with minimum token consumption and zero skill initialization. Use when pre-warming rolling quota windows, setting up daily auto-refresh schedules, or resetting session timers without loading repository context.
---

# Refresh Session

Send a minimal 1-token ping to Claude Code CLI (`claude`) and OpenAI Codex CLI (`codex`) to pre-warm or refresh the rolling 5-hour rate-limit / quota window without loading repository files, skills, plugins, or tools. Also supports configuring native OS daemon schedules (`launchd` on macOS, `cron` on Linux) to trigger automatic daily pre-warming (Shift-Left Quota Staggering) for uninterrupted workflow.

## When to Use

- At the start of a workday to initialize the 5-hour rolling quota window early.
- Automatically at a custom morning hour (e.g. 5:00 AM) so you have full 100% quota resetting right into deep work hours.
- Before stepping away or taking a break to ensure rate-limits reset by the time you return.
- Whenever you need to refresh CLI sessions without burning tokens on codebase indexing or skills discovery.

## Usage & Invocations

### 1. Instant Session Refresh (On-Demand)

| Invocation | Target |
|---|---|
| `/refresh-session` or `/refresh-session all` | Pings both Claude and Codex |
| `/refresh-session claude` | Pings Claude Code only |
| `/refresh-session codex` | Pings Codex CLI only |

Execute the bundled standalone engine:

```bash
python3 skills/refresh-session/resources/scripts/refresh_session.py [claude|codex|all]
```

To emit structured JSON report:

```bash
python3 skills/refresh-session/resources/scripts/refresh_session.py [target] --json
```

### 2. Daily Scheduled Pre-Warming (Daemon Automation)

Configure OS native daemons (`launchd` on macOS, `cron` on Linux) without third-party services.

| Natural Language Request | CLI Command |
|---|---|
| "Setup refresh lúc 5h", "Hẹn giờ refresh 05:00" | `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00` |
| "Schedule Claude refresh at 6am" | `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 6am --target claude` |
| "Kiểm tra lịch refresh session" | `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --status` |
| "Hủy lịch refresh session", "Tắt auto refresh" | `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --uninstall` |

Time input supports flexible formats:
- 24-hour format: `05:00`, `5:00`, `14:30`, `09:15`
- Short hour format: `5h`, `6H`, `14h`, `5`, `6`
- 12-hour AM/PM format: `5am`, `5:30am`, `6pm`, `12pm`

For a complete reference and quick lookup table, see:
- English Quick Guide: [docs/refresh-session-quick-guide.en.md](../../docs/refresh-session-quick-guide.en.md)
- Vietnamese Quick Guide: [docs/refresh-session-quick-guide.vi.md](../../docs/refresh-session-quick-guide.vi.md)

## Sandboxing & Zero-Skill Guarantees

The execution engine guarantees that no repository context or customizations are scanned:

1. **Filesystem Isolation**: Commands run inside a clean temporary directory (`tempfile.TemporaryDirectory`) outside repository roots.
2. **Claude Code Isolation**:
   - `--safe-mode`: Disables `CLAUDE.md`, skills, plugins, hooks, MCP servers, and custom workflows.
   - `--disable-slash-commands`: Explicitly turns off all skill discovery.
   - `--tools ""`: Disables all tools so tool schemas are not injected into the prompt.
   - `--model haiku`: Forces lightweight Claude 3.5 Haiku to minimize latency and token costs.
   - `-p "1"`: Non-interactive print mode with a 1-character prompt.
3. **Codex CLI Isolation**:
   - `--disable plugins --disable apps --disable hooks`: Deactivates all plugins and integrations.
   - `--ephemeral`: Runs without persisting session or rollout state to disk.
   - `--skip-git-repo-check`: Allows running outside a git working tree.
   - `--ignore-user-config --ignore-rules`: Bypasses `config.toml` and `.rules` files.
   - `-c model_reasoning_effort=low`: Caps reasoning budget to `low`.
