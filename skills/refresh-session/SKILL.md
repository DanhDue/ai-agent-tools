---
name: refresh-session
description: Pings Claude Code and Codex CLIs to refresh or pre-initialize 5-hour rolling session windows with minimum token consumption and zero skill initialization. Use when pre-warming rolling quota windows or resetting session timers without loading repository context.
---

# Refresh Session

Send a minimal 1-token ping to Claude Code CLI (`claude`) and OpenAI Codex CLI (`codex`) to pre-warm or refresh the rolling 5-hour rate-limit / quota window without loading repository files, skills, plugins, or tools.

## When to Use

- At the start of a workday to initialize the 5-hour rolling quota window early.
- Before stepping away or taking a break to ensure rate-limits reset by the time you return.
- Whenever you need to refresh CLI sessions without burning tokens on codebase indexing or skills discovery.

## Usage

When the user runs `/refresh-session`, determine the requested target:

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

