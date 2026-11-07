---
name: check-quota
description: Shows the interactive Antigravity Multi-Profile Quota Dashboard (Dark Mode Visual Companion) or prints terminal quota cards with model details, countdowns, and quick actions across all configured accounts.
---

# Check Quota (Antigravity Multi-Profile Dashboard)

Displays an executive, interactive Dark Mode dashboard and terminal status cards for all Antigravity profile accounts (`danhdue`, `huynhminhtien0510`, `tess`, etc.) configured in `~/.zshrc`.

## When to Use

- Whenever you want to check real-time rate limits, reset timers, and remaining quotas for Gemini 3.8/Pro, Claude 5.5/GPT, and Gemini 4 Argon.
- To inspect multi-profile account statuses side-by-side in a responsive 2-column grid.
- Before running heavy workflows to select the account profile with the highest available quota.
- When configuring batch daily pre-warming schedules (`/refresh-session schedule`) or running quick 1-token session resets.

## Invocations & Commands

### 1. In AI Agent Chat (Skill Invocations)

When this skill is invoked via `/check-quota` or natural language (e.g., *"check quota"*, *"hiển thị dashboard quota"*), the AI assistant will:
1. Render the interactive Dark Mode Visual Companion HTML dashboard inline:
   ```html
   <agent-embed src="file:///Users/danhdueexoictif/Projects/ai-agent-tools/skills/check-quota/resources/dashboard/quota_dashboard.html"></agent-embed>
   ```
2. Present a brief summary of the active profile quota state.

### 2. Terminal CLI Commands

The `check-quota` executable CLI is available globally in PATH:

| Command | Description |
|---|---|
| `check-quota` | View detailed model cards for current active profile |
| `check-quota <profile>` | View detailed model cards for specific profile or provider (e.g. `check-quota danhdue`, `check-quota kiro`, `check-quota claude`) |
| `check-quota all` | Scan all accounts and AI providers in parallel and print tabular multi-profile summary |
| `check-quota refresh <profile>` | Instant pre-warm ping / token refresh to synchronize session quota (supports Antigravity profiles, Claude, Codex, and Kiro) |
| `check-quota --ui` or `check-quota --web` | Open the interactive Dark Mode HTML dashboard in default browser as a detached daemon (can safely close Terminal) |
| `check-quota --ui -f` | Run Quota Dashboard in foreground terminal mode (useful for debugging) |
| `check-quota --stop` | Stop the running background Quota Dashboard web server |
| `check-quota --status` | Check running state, PID, URL, and log path of the Quota Web Server |
| `check-quota -h` | Display help and usage options |

## Quota Thresholds & Visual Indicators

- **Emerald Green (`>= 50%`)**: Healthy quota level.
- **Amber Orange (`10% - 49%`)**: Medium quota level.
- **Crimson Red (`< 10%`)**: Quota low / critical.
- **Argon Badge (`✣ Argon`)**: Rendered only on profiles where Argon is available. Omitted on accounts where Argon is inactive.
- **Countdown Timer (`⏱`)**: Shows remaining duration until the 5-hour rolling window or weekly cycle resets.

## Integrated Quick Actions

- **⚡ Refresh nhanh**: Pings 1-token (`agy -p /usage`) via profile sandbox in ~110ms with zero token waste.
- **⏰ Lên lịch đầu ngày**: Configures daily automated OS pre-warm daemon via `/refresh-session schedule --time 07:00 --delay 30`.

