# ai-agent-tools

Shared AI agent tooling for mobile app projects — **Flutter**, **Android Native**, and
**iOS Native**. One repository, installed once per machine, serving every project.

Works in **Antigravity** and **Claude Code** from a single source: `skills/` and `rules/` are
written once, and each runtime gets a thin manifest pointing at them.

| | |
|---|---|
| **42 skills** | Epic lifecycle orchestration · 3-tier quality gates · security / architecture / UI / code-health audits · TDD and debugging process · build-environment and secure-file setup · Flutter and Android feature/API scaffolding |
| **2 rules** | `CRITICAL_RULES.md` (mandatory `quality_check` after every workflow) and `coding-guidelines.md` (think first, simplicity, surgical changes, verify) |
| **Templates** | Per-project `AGENTS.md` and shared editor guardrails |

Start with the **`epic-lifecycle`** skill for anything epic-scale — it owns the stage sequence and
the four approval gates, and routes to the right skill at each step.

---

## Contents

- [1. Installation](#1-installation)
  - [1.1. Claude Code](#11-claude-code)
  - [1.2. Antigravity](#12-antigravity)
  - [1.3. Per-project setup](#13-per-project-setup)
- [2. Daily workflow](#2-daily-workflow)
  - [2.1. Where the single source of truth is](#21-where-the-single-source-of-truth-is)
  - [2.2. Editing a skill and republishing](#22-editing-a-skill-and-republishing)
  - [2.3. Updating another machine](#23-updating-another-machine)
  - [2.4. Command reference](#24-command-reference)
- [3. Reference](#3-reference)
  - [3.1. Repository layout](#31-repository-layout)
  - [3.2. How the runtimes differ](#32-how-the-runtimes-differ)
  - [3.3. The session-start hook](#33-the-session-start-hook)
  - [3.4. Authoring a skill](#34-authoring-a-skill)
  - [3.5. Rules vs audit criteria](#35-rules-vs-audit-criteria)
- [4. License](#4-license)
---

## 1. Installation

Install once per machine; it applies to **every project** on that machine. You only need to clone
this repository if you intend to *edit* the skills.

### 1.1. Claude Code

```bash
claude plugin marketplace add DanhDue/ai-agent-tools
claude plugin install d3nexus@danhdue-agent-tools
```

Skills then appear as `d3nexus:<skill-name>` — for example `/d3nexus:epic-lifecycle`.

**Restart the session afterwards.** Reload the IDE window (`Cmd+Shift+P` → *Developer: Reload
Window*) or start a new CLI session. Skills are read at session start, and a new chat in the same
window is not always enough.

### 1.2. Antigravity

Antigravity loads a plugin from any directory under its customization root that contains a
**root-level** `plugin.json`. Clone this repository straight into the global plugins folder:

```bash
git clone https://github.com/DanhDue/ai-agent-tools.git ~/.gemini/config/plugins/d3nexus
```

That is all — `plugin.json`, `skills/` and `rules/` sit at the repo root, which is exactly the
shape Antigravity expects. Skills are namespaced automatically.

> [!IMPORTANT]
> **Check for stale global skills first.** Anything already in `~/.gemini/config/skills/` is
> discovered independently of the plugin and competes with it — an old copy of a skill will
> quietly shadow the one you just installed.
>
> ```bash
> ls ~/.gemini/config/skills/    # move aside any directory this kit now supplies
> ```

Antigravity also ranks **workspace over global**: a project's own `.agents/skills/` outranks this
plugin. If a project vendors its own copy, that copy wins there — remove it to let the plugin
serve every project uniformly.

### 1.3. Per-project setup

Skills and rules arrive with the plugin. Each project still needs an entry point:

```bash
scripts/init-project.sh /path/to/project "Project Name"
```

This writes an `AGENTS.md` from the template, symlinks `CLAUDE.md → AGENTS.md` so one file serves
both runtimes and they cannot drift, and prints the editor guardrails to merge into
`.vscode/settings.json`.

> [!NOTE]
> **Overlap with `superpowers`**: 13 of these skills began as forks of
> [superpowers](https://github.com/obra/superpowers) and have since diverged. Both are namespaced
> plugins so they can be installed side by side, but running both means two answers to the same
> question — `claude plugin disable superpowers` to avoid ambiguity.

---

## 2. Daily workflow

### 2.1. Where the single source of truth is

**This git repository.** Everything else is a derived copy you must never edit:

```
DanhDue/ai-agent-tools (GitHub)                              ← THE source
 └─ ~/AllProjects/ai-agent-tools/                            ← your working clone: EDIT HERE
     ├─ ~/.claude/plugins/marketplaces/danhdue-agent-tools/  ← git clone, pulled by `marketplace update`
     │   └─ ~/.claude/plugins/cache/.../d3nexus/<version>/   ← what Claude Code actually reads
     └─ ~/.gemini/config/plugins/d3nexus/                    ← what Antigravity reads (its own clone)
```

An edit to a copy works until the next update, then silently vanishes. Quick test: if the path
contains `.claude/plugins` or `.gemini/config`, it is a copy.

To read what a skill currently says, open it in your working clone (`skills/<name>/SKILL.md`), or
run `claude plugin details d3nexus` for the installed inventory. Opening the project together with
this repository in one editor window — see the multi-root workspace in a consuming project — keeps
the source one click away.

### 2.2. Editing a skill and republishing

> [!WARNING]
> A version bump is **required** for Claude Code. `claude plugin update` compares the version in
> `plugin.json`; if it is unchanged it reports *"already at the latest version"* and leaves every
> machine on the old cached copy — the edit silently never lands.

```bash
cd ~/AllProjects/ai-agent-tools
$EDITOR skills/epic-lifecycle/SKILL.md     # 1. edit
scripts/release.sh                         # 2. verify + bump + commit + push + refresh this machine
```

`release.sh` runs `verify.sh` first and refuses to publish if it fails. For anything bigger than a
patch, pass the version explicitly: `scripts/release.sh 1.1.0`.

Then restart the session, as in [1.1](#11-claude-code).

Antigravity needs no bump — it reads its clone's working tree directly:

```bash
git -C ~/.gemini/config/plugins/d3nexus pull
```

### 2.3. Updating another machine

**Claude Code** — both steps are needed: the first pulls the repo, the second copies it into the
versioned cache Claude Code reads.

```bash
claude plugin marketplace update danhdue-agent-tools
claude plugin update d3nexus@danhdue-agent-tools
```

**Antigravity**:

```bash
git -C ~/.gemini/config/plugins/d3nexus pull
```

### 2.4. Command reference

| Command | Purpose |
|---|---|
| `scripts/verify.sh` | Manifests, frontmatter, links, anchors, stale namespaces |
| `scripts/release.sh [version]` | Verify → bump → commit → push → refresh this machine |
| `scripts/init-project.sh <path> <name>` | Scaffold a consuming project |
| `claude plugin list` | What is installed and enabled |
| `claude plugin details d3nexus` | Skill inventory and projected token cost |
| `claude plugin validate <path>` | Check manifests before publishing |
| `claude plugin disable d3nexus` / `enable` | Toggle without uninstalling |
| `claude plugin uninstall d3nexus` | Remove it |

---

## 3. Reference

### 3.1. Repository layout

```
skills/<name>/SKILL.md           # single source of truth for all runtimes
rules/                           # always-on behavioural constraints
templates/                       # per-project scaffolding
scripts/verify.sh                # pre-publish checks
scripts/release.sh               # the publish loop
scripts/init-project.sh          # per-project scaffolding

hooks/session-start              # injects using-superpowers at conversation start
hooks/hooks.json                 # Claude Code hook config (SessionStart)
hooks.json                       # Antigravity hook config (PreInvocation, root level)

plugin.json                      # Antigravity plugin manifest (root level — required)
.claude-plugin/plugin.json       # Claude Code plugin manifest
.claude-plugin/marketplace.json  # Claude Code marketplace
.agents/plugins/marketplace.json # Antigravity marketplace
```

`skills/<name>/SKILL.md` is simultaneously the Antigravity and the Claude Code skill format, so
nothing is duplicated between runtimes — only the thin manifests differ.

### 3.2. How the runtimes differ

Worth knowing, because it explains why the layout looks the way it does:

| | Antigravity | Claude Code |
|---|---|---|
| Plugin manifest | `plugin.json` at the plugin root | `.claude-plugin/plugin.json` |
| Distribution | clone into `~/.gemini/config/plugins/` | marketplace + versioned cache |
| Picking up an edit | `git pull` — reads the working tree | needs a **version bump** |
| A project's `.agents/skills/` | ✅ native, and outranks a global plugin | ❌ not a load path |
| A project's `.agents/rules/*.md` | ✅ native | ❌ — reaches them via root `CLAUDE.md` imports |
| Rule frontmatter `trigger: always_on` | ✅ honoured | ignored |
| Symlinked skill folders | followed | ❌ **skipped** (`unsafe or symlinked skill folder`) |

Both load skills by **progressive disclosure**: only `name` and `description` enter the context
window; the body is read when the skill activates. Keep `SKILL.md` concise and push bulk into the
skill's own `references/`, `scripts/`, `resources/` or `examples/` subdirectory.

### 3.3. The session-start hook

Skills activate on `description` matching, which is probabilistic. The hook makes it
deterministic: at the start of a conversation it injects the `using-superpowers` skill, which
instructs the agent to reach for a skill before answering.

The two runtimes need different wiring, so one script serves both:

| | Event | Output | Fires |
|---|---|---|---|
| Claude Code | `SessionStart` (`hooks/hooks.json`) | `hookSpecificOutput.additionalContext` | once per session |
| Antigravity | `PreInvocation` (root `hooks.json`) | `injectSteps[].ephemeralMessage` | **every turn** |

Antigravity has no `SessionStart` event — `PreInvocation` is the only place to inject context,
and it runs before *every* model call. The script therefore gates on `invocationNum == 1`, and
**fails closed**: if the payload cannot be parsed it injects nothing, because guessing "first
turn" would re-inject on every turn for the rest of the session.

`scripts/verify.sh` step 6 exercises all four paths.

### 3.4. Authoring a skill

A skill is a directory under `skills/` containing `SKILL.md` with YAML frontmatter of exactly two
fields:

```yaml
---
name: my-skill                 # lowercase, hyphenated, matches the directory name
description: Use this skill when …   # what it does AND when to use it — drives activation
---
```

`description` is the field both runtimes read to decide whether to activate the skill, so it
carries more weight than anything in the body. All 42 skills use these two fields and nothing
else — adding non-standard keys risks a frontmatter parse failure with no error surfaced.

Use the `writing-skills` skill when creating or editing one, and run `scripts/verify.sh` before
publishing.

### 3.5. Rules vs audit criteria

Rules stay deliberately thin and runtime-agnostic — they are constraints that hold in every
context, not checklists.

House conventions that are really *audit criteria* — Clean Architecture wiring, the Freezed
contract, naming and formatting, the security baseline — live in
`references/flutter-project-baseline.md` inside the audit skill that enforces them. That way
`quality_check` loads them only when it actually audits a Flutter project, and each reference
holds only what its `SKILL.md` does not already cover.

---

## 4. License

MIT
