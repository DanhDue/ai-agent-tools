# Quick-Guide: `/refresh-session` & Staggered Quota Scheduling

A complete quick-reference guide and cheat-sheet for pre-warming, managing, and scheduling 5-hour rolling session windows for Claude Code CLI (`claude`) and OpenAI Codex CLI (`codex`).

---

## 1. The Strategy: Rolling Window Staggering

Both Claude Code and Codex enforce a **rolling 5-hour quota window** that activates upon your first prompt. If you start work at 08:00 AM without pre-warming, heavy usage can lock you out by 10:00 AM until 01:00 PM (13:00).

By scheduling an automated 1-token ping at **05:00 AM** (or 2–3 hours before your workday):

```text
05:00 AM                 08:00 AM                      10:00 AM                      03:00 PM (15:00)
   │                        │                             │                                 │
   ▼                        ▼                             ▼                                 ▼
[Automated Ping]     [Begin Workday]               [BLOCK 1 EXPIRES]                 [Block 2 Ends]
Block 1 Activates    Use Block 1 Quota             Block 2 Activates                 Continuous work
(5h window)          (Fresh 100% capacity)         (Brand new 100% capacity)         without lockouts
                     ────────────────────────►     ─────────────────────────────────────────►
                          2h deep work                           5h deep work
```

- **05:00 AM**: Automated 1-token ping initializes Block 1 (05:00–10:00).
- **08:00 AM**: You start work with 2 hours of full quota available.
- **10:00 AM**: Block 1 expires after exactly 5 hours. Block 2 immediately opens with a fresh 100% quota!
- **Result**: You work continuously from **08:00 AM to 03:00 PM (7 unbroken hours)** with zero midday lockout.

---

## 2. Complete Command Cheat-Sheet

You can invoke these commands either as IDE slash commands (`/refresh-session ...`) or directly via terminal CLI.

### 2.1. Slash Command Cheat-Sheet

| Command | Mode | Action |
|:---|:---:|:---|
| `/refresh-session` *(or `/refresh-session all`)* | **Manual** | Pings both Claude Code and OpenAI Codex immediately. |
| `/refresh-session claude` | **Manual** | Pings Claude Code only immediately. |
| `/refresh-session codex` | **Manual** | Pings OpenAI Codex only immediately. |
| `/refresh-session schedule <time>` | **Schedule** | Installs daily OS daemon for specified time (`5h`, `05:00`, `6am`, `06:30`). |
| `/refresh-session schedule <time> --target <tgt>` | **Schedule** | Installs daily schedule for specific target (`claude`, `codex`, `all`). |
| `/refresh-session schedule status` | **Inspect** | Checks whether the daily daemon is active and displays the next trigger time. |
| `/refresh-session schedule remove` *(or `uninstall`)* | **Uninstall** | Disables and deletes the scheduled OS daemon. |

---

### 2.2. Terminal CLI Cheat-Sheet

```bash
# === Instant Manual Ping ===
python3 skills/refresh-session/resources/scripts/refresh_session.py all
python3 skills/refresh-session/resources/scripts/refresh_session.py claude
python3 skills/refresh-session/resources/scripts/refresh_session.py codex
python3 skills/refresh-session/resources/scripts/refresh_session.py all --json

# === Daily Schedule Management ===
# Set daily schedule to 5:00 AM
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00

# Set daily schedule to 6:00 AM for Claude only
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 6h --target claude

# Check schedule status
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --status

# Remove daily schedule
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --uninstall
```

---

## 3. Natural Language Prompts

You can also speak naturally to your AI Agent:

- *"Pre-warm sessions now"* $\rightarrow$ Runs `/refresh-session all`
- *"Ping Claude now"* $\rightarrow$ Runs `/refresh-session claude`
- *"Schedule refresh session at 5:00 AM every day"* $\rightarrow$ Runs `schedule --time 05:00`
- *"Schedule daily refresh at 6am"* $\rightarrow$ Runs `schedule --time 6am`
- *"Check refresh session schedule status"* $\rightarrow$ Runs `schedule --status`
- *"Turn off refresh session schedule"* $\rightarrow$ Runs `schedule --uninstall`

---

## 4. Under-the-Hood System Details

- **macOS Daemon**: `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` (managed via native `launchctl`).
- **Linux Crontab**: User crontab entry wrapped in `# BEGIN d3nexus-refresh-session`.
- **Daemon Logs**:
  - Standard Output: `~/.devtool/logs/refresh_session_daemon.log`
  - Error Output: `~/.devtool/logs/refresh_session_daemon.err`
- **Zero Token Overhead Guarantee**: Every execution runs inside an ephemeral sandbox outside any repository root, suppressing skills, plugins, hooks, and MCP servers.
