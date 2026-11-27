# Unified External Review Configuration and Pass Limits — Adversarial BDD Scenarios

- **Epic**: `unified_review_config`
- **Prefix**: `URC`
- **Dimensions**: Happy Path (`HP`), Edge Cases (`EC`), State Transitions (`ST`), Architecture and Isolation (`AR`), Fault Resilience (`FR`)

## Table of Contents

- [Dimension 1 Happy Path Scenarios](#dimension-1-happy-path-scenarios)
- [Dimension 2 Edge Cases and Boundary Conditions](#dimension-2-edge-cases-and-boundary-conditions)
- [Dimension 3 State Transitions and Idempotency](#dimension-3-state-transitions-and-idempotency)
- [Dimension 4 Architecture Isolation and Precedence](#dimension-4-architecture-isolation-and-precedence)
- [Dimension 5 Fault Resilience and Validation Guards](#dimension-5-fault-resilience-and-validation-guards)

## Dimension 1 Happy Path Scenarios

```gherkin
Scenario: [URC-HP-01] [Tier C - Integration] Kit defaults resolve all four independent pass limits and external review settings
Given a clean temporary repository and isolated fake REAL_HOME containing no global, project, or legacy review config files
When persona_config.resolve_review_limits and persona_config.resolve_review_config are called
Then max_task_review_passes equals 2, max_fix_passes equals 1, max_principal_review_passes equals 3, and max_cross_model_review_passes equals 3 with source "kit"
And provider_priority equals ("claude", "codex", "kiro", "agy") with source "kit"
And providers resolve "claude" to model_id "opus" (effort "high"), "codex" to "gpt-6.1-sol" (effort "high"), "kiro" to "claude-opus-5.5" (effort "high"), "agy" to "gemini-4-argon-high" (effort "high"), and "ollama" to "gemma4:31b-it-qat" with host "http://localhost:11434"
And quota_thresholds match 5h_min_fraction=0.15, 7d_min_fraction=0.02, kiro_min_fraction=0.03, kiro_min_credits=15.0, and agy_argon_min_fraction=0.10

Scenario: [URC-HP-02] [Tier C - Integration] dev-config limits independently reads and updates all four pass caps across global and project scopes
Given a clean temporary repository and isolated fake REAL_HOME
When dev_config.py runs "limits --principal-review 2 --cross-model-review 4 --scope global" followed by "limits --task-review 3 --fix 0 --scope project"
Then "$REAL_HOME/.d3nexus/personas.json" persists max_principal_review_passes=2 and max_cross_model_review_passes=4 without writing max_task_review_passes or max_fix_passes
And ".agents/config/personas.json" persists max_task_review_passes=3 and max_fix_passes=0
And "dev_config.py limits --json" returns task=3 (project), fix=0 (project), principal=2 (global), cross_model=4 (global)
And "dev_config.py status --json" preserves task_review_limits (3, 0) while adding review_limits (3, 0, 2, 4)

Scenario: [URC-HP-03] [Tier C - Integration] dev-config review configures shared priority, provider models, and quota thresholds across global and project scopes
Given a clean temporary repository and isolated fake REAL_HOME
When dev_config.py runs "review priority codex,claude,kiro,agy --scope global", "review set agy --model gemini-4-carbon-high --effort high --scope global", "review set ollama --model qwen2.5-coder:32b --host http://127.0.0.1:11434 --scope project", and "review thresholds --5h 0.25 --kiro-credits 25.0 --scope global"
Then "dev_config.py review status --json" reports provider_priority ["codex", "claude", "kiro", "agy"] with source "global"
And provider "agy" resolves model_id "gemini-4-carbon-high" (effort "high", source "global") while provider "ollama" resolves model_id "qwen2.5-coder:32b" with host "http://127.0.0.1:11434" (source "project")
And quota_thresholds report 5h_min_fraction=0.25 and kiro_min_credits=25.0 (source "global")
And both dev_config._load_quota_thresholds and agy_dispatch._load_thresholds return 5h_min_fraction=0.25 and kiro_min_credits=25.0

Scenario: [URC-HP-04] [Tier C - Integration] run_external_review applies separate principal and cross-model pass limits and shared global provider_priority
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude", "kiro", "agy"]
When run_external_review.resolve_effective_max_rounds runs for kind "principal" and kind "code" with cli_max_rounds=None
Then kind "principal" resolves to 2 rounds and kind "code" resolves to 4 rounds
And run_external_review.load_review_config returns provider_priority ["codex", "claude", "kiro", "agy"]
And passing explicit cli_max_rounds=5 overrides both kinds to 5

Scenario: [URC-HP-05] [Tier C - Integration] LifecycleRunner honors separate principal and cross-model round caps and layered provider_priority
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude", "kiro", "agy"]
When LifecycleRunner initializes with RunnerConfig leaving max_review_rounds, max_principal_review_rounds, max_cross_model_review_rounds, and provider_priority unset
Then _resolve_external_review_bounds("principal") returns 2 and _resolve_external_review_bounds("code") returns 4
And _resolve_review_provider_priority() returns ["codex", "claude", "kiro", "agy"]

Scenario: [URC-HP-06] [Tier C - Integration] End-to-end dev-config changes propagate cleanly to external review, runner, docs, and verify.sh registry
Given a clean temporary repository and isolated fake REAL_HOME where global and project settings are written exclusively via dev_config.py CLI commands
When dev_config.py status, run_external_review.load_review_config, run_external_review.resolve_effective_max_rounds, and LifecycleRunner resolve settings against that workspace
Then all consumers agree on the exact same provider_priority, resolved provider model IDs, quota_thresholds, and four independent pass caps
And skills/dev-config/SKILL.md, skills/principal-review/SKILL.md, skills/cross-model-review/SKILL.md, skills/dev-lifecycle/SKILL.md, rules/CRITICAL_RULES.md (<= 1000 words), docs/dev-config-quick-guide.en.md, and scripts/verify.sh all document and register the unified review config and all 5 URC test suites
```

## Dimension 2 Edge Cases and Boundary Conditions

```gherkin
Scenario: [URC-EC-01] [Tier C - Integration] Review provider model accepts both catalogue aliases with effort expansion and raw model IDs
Given a temporary repository whose global personas.json sets review.providers.agy to {"model": "argon", "effort": "medium"} and review.providers.claude to {"model": "claude-sonnet-4-6", "thinking_level": "low"}
When persona_config.resolve_review_config runs
Then provider "agy" expands alias "argon" + effort "medium" into model_id "gemini-4-argon-medium" with effort "medium"
And provider "claude" accepts the raw ID "claude-sonnet-4-6" verbatim and normalizes legacy key "thinking_level" to effort "low"

Scenario: [URC-EC-02] [Tier C - Integration] Legacy review_config.json serves as read-only fallback only for keys absent from both project and global layers
Given a repository containing ".devtool/review_config.json" with provider_priority=["kiro", "agy"], max_rounds=5, quota_thresholds={"5h_min_fraction": 0.30}, and providers.codex={"model": "gpt-legacy", "thinking_level": "medium"}
And no global or project personas.json defines those keys
When persona_config.resolve_review_config runs
Then provider_priority resolves to ("kiro", "agy") with source "legacy"
And both max_principal_review_passes and max_cross_model_review_passes resolve to 5 with source "legacy"
And quota_thresholds["5h_min_fraction"] resolves to 0.30 with source "legacy" and providers["codex"].model_id resolves to "gpt-legacy" with effort "medium" and source "legacy"
And detect_legacy_warnings includes a non-blocking migration warning naming ".devtool/review_config.json"

Scenario: [URC-EC-03] [Tier C - Integration] Global write emits masking warning when project personas.json overrides the same review or limit key
Given a temporary repository where ".agents/config/personas.json" sets max_principal_review_passes=1 and review.provider_priority=["kiro", "claude"]
When dev_config.py runs "limits --principal-review 4 --scope global" and "review priority codex,claude --scope global"
Then both commands succeed (exit 0) and write to "$REAL_HOME/.d3nexus/personas.json"
And stderr prints a masking warning identifying the project override in ".agents/config/personas.json"
And effective resolution in that repository remains max_principal_review_passes=1 and provider_priority=("kiro", "claude")

Scenario: [URC-EC-04] [Tier C - Integration] Custom layered quota_thresholds control select_provider_by_quota decisions in run_external_review
Given a temporary repository with "$REAL_HOME/.d3nexus/personas.json" setting review.quota_thresholds.5h_min_fraction=0.50 and review.provider_priority=["claude", "codex"]
And a stubbed quota fetcher reporting claude ACTIVE with 5H=0.35 (7D=0.80) and codex ACTIVE with 5H=0.70 (7D=0.80)
When run_external_review.resolve_review_settings runs with auto_quota=True
Then claude is skipped because 0.35 < 0.50 (resolved threshold, not hardcoded 0.15)
And codex is selected as the active reviewer

Scenario: [URC-EC-05] [Tier C - Integration] Fixed-effort catalogue alias in review.providers resolves effort to "none" and preserves zero-cap fix passes
Given a temporary repository with global personas.json setting review.providers.agy={"model": "orchestrator-argon"} and max_fix_passes=0
When persona_config.resolve_review_config and dev_config.py limits --json execute
Then provider "agy" resolves model_id "gemini-pro-orchestrator-g1-pro" with effort "none"
And max_fix_passes resolves cleanly to 0 without raising validation errors
```

## Dimension 3 State Transitions and Idempotency

```gherkin
Scenario: [URC-ST-01] [Tier C - Integration] Resetting project review or limit overrides restores global layer without disturbing sibling keys
Given a temporary repository with global max_principal_review_passes=2, global review.provider_priority=["codex", "claude"], project max_principal_review_passes=1, project max_fix_passes=0, and project review.provider_priority=["kiro", "agy"]
When dev_config.py runs "limits reset principal --scope project" and "review reset priority --scope project"
Then max_principal_review_passes falls back to 2 (source "global") and provider_priority falls back to ("codex", "claude") (source "global")
And project max_fix_passes remains 0 (source "project") untouched

Scenario: [URC-ST-02] [Tier C - Integration] Resetting all review overrides in a scope prunes empty review objects cleanly
Given a temporary repository whose ".agents/config/personas.json" contains active_preset="default" plus review.provider_priority, review.providers.claude, and review.quota_thresholds
When dev_config.py runs "review reset all --scope project"
Then ".agents/config/personas.json" no longer contains a "review" key while retaining active_preset="default"
And running "review reset all --scope project" a second time exits 0 idempotently

Scenario: [URC-ST-03] [Tier C - Integration] update_sticky_review_config persists last_used_provider to .devtool/state/review_runtime.json without mutating .devtool/review_config.json
Given a temporary repository containing a pre-existing ".devtool/review_config.json" with exact bytes B0
When run_external_review.load_review_config and run_external_review.update_sticky_review_config(root, "codex", "gpt-custom", "medium") execute
Then ".devtool/review_config.json" remains byte-identical to B0 (never auto-seeded or overwritten)
And ".devtool/state/review_runtime.json" records last_used_provider="codex"
And subsequent run_external_review.load_review_config returns last_used_provider="codex" while keeping configured provider models intact

Scenario: [URC-ST-04] [Tier C - Integration] Explicit RunnerConfig overrides take precedence over global and project persona_config limits
Given a temporary repository with project personas.json setting max_principal_review_passes=2, max_cross_model_review_passes=4, and review.provider_priority=["codex", "claude"]
When LifecycleRunner is constructed with RunnerConfig(max_principal_review_rounds=1, max_cross_model_review_rounds=5, provider_priority=["kiro", "agy"])
Then _resolve_external_review_bounds("principal") returns 1, _resolve_external_review_bounds("code") returns 5, and _resolve_review_provider_priority() returns ["kiro", "agy"]
And constructing RunnerConfig(max_review_rounds=6) overrides both principal and code bounds to 6 for legacy caller compatibility
```

## Dimension 4 Architecture Isolation and Precedence

```gherkin
Scenario: [URC-AR-01] [Tier C - Integration] Global personas.json beats auto-seeded legacy .devtool/review_config.json while project personas.json beats global
Given a temporary repository containing legacy ".devtool/review_config.json" with provider_priority=["claude", "codex", "kiro", "agy"] and max_rounds=3
And "$REAL_HOME/.d3nexus/personas.json" sets review.provider_priority=["codex", "kiro"] and max_principal_review_passes=2
When persona_config.resolve_review_config runs before and after adding ".agents/config/personas.json" with review.provider_priority=["agy", "claude"] and max_principal_review_passes=1
Then before project config is added, global wins over legacy: provider_priority=("codex", "kiro") (source "global") and max_principal_review_passes=2 (source "global") while max_cross_model_review_passes=3 (source "legacy")
And after project config is added, project wins over global: provider_priority=("agy", "claude") (source "project") and max_principal_review_passes=1 (source "project")

Scenario: [URC-AR-02] [Tier C - Integration] run_external_review loads persona_config relative to its plugin install path when run inside a satellite repository
Given a temporary satellite repository containing no "scripts/persona_config.py" and an isolated fake REAL_HOME with global personas.json setting max_principal_review_passes=2 and review.provider_priority=["kiro", "claude"]
When run_external_review.py executes from its kit location with cwd set to the satellite repository
Then load_review_config and resolve_effective_max_rounds resolve the satellite repository's project layer plus fake REAL_HOME global layer cleanly without ImportError

Scenario: [URC-AR-03] [Tier C - Integration] LifecycleRunner isolates Principal Review cap from Cross-Model Review cap during execution
Given a temporary repository where global personas.json sets max_principal_review_passes=1 and max_cross_model_review_passes=3
When LifecycleRunner evaluates circuit-breaker round exhaustion for stage "principal" at round 1 and stage "code" at round 1 with Critical findings present
Then stage "principal" triggers "CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)" at round 1
And stage "code" does not trigger max-rounds halt at round 1 because its cap is 3
```

## Dimension 5 Fault Resilience and Validation Guards

```gherkin
Scenario: [URC-FR-01] [Tier C - Integration] Invalid pass limits, duplicate or unknown priorities, out-of-range thresholds, and CLI-mismatched aliases are rejected with PersonaConfigError
Given malformed persona config layers testing max_principal_review_passes=0, max_cross_model_review_passes=True, max_fix_passes=-1, review.provider_priority=["claude", "claude"], review.provider_priority=["ollama"], review.quota_thresholds.5h_min_fraction=1.5, review.providers.claude={"model": "codex-gpt", "effort": "high"}, and review.providers.claude={"model": "opus", "host": "http://localhost:11434"}
When persona_config.load_persona_config or persona_config.resolve_review_config validates each case
Then every invalid case raises PersonaConfigError with an actionable message naming the offending field or provider

Scenario: [URC-FR-02] [Tier C - Integration] dev_config models remove refuses deleting an alias referenced by review.providers and rejects invalid CLI flags atomically
Given a temporary repository with custom alias "custom-claude" in global models referenced by global review.providers.claude.model
When dev_config.py runs "models remove custom-claude --scope global"
Then the command exits 1 with an error citing "review.providers.claude.model" and leaves global personas.json unchanged
And running "review set ollama --model gemma4 --host ftp://bad-host" or "limits --principal-review 0" exits 1 without corrupting or partially writing personas.json

Scenario: [URC-FR-03] [Tier C - Integration] Corrupted legacy .devtool/review_config.json and .devtool/state/review_runtime.json fall back cleanly without crashing external review
Given a temporary repository containing truncated invalid JSON in both ".devtool/review_config.json" and ".devtool/state/review_runtime.json"
When persona_config.resolve_review_config and run_external_review.load_review_config execute
Then neither raises JSONDecodeError
And configuration falls back cleanly to global/kit defaults with last_used_provider="claude"

Scenario: [URC-FR-04] [Tier C - Integration] Running dev_config limits or review commands on missing directories creates parent folders atomically without leaving .tmp artifacts
Given an isolated fake REAL_HOME where "$REAL_HOME/.d3nexus" does not exist yet and a temporary repository where ".agents/config" does not exist yet
When dev_config.py writes global limits and project review priority
Then both target JSON files are created atomically with valid JSON and schema_version=1
And zero ".tmp" files remain in either directory
```
