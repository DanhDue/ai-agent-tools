# Check-Quota Dynamic Provider Account Tiers and Unified UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Normalize dynamic account tiers, deterministic `priority` scores, available model rosters, and `AccountMeta` across all four LLM providers (`Antigravity`, `Claude`, `Codex`, `Kiro`) in `scripts/agy_quota.py` and render unified badges, provider-aware Account Info modals, Ultra `Gemini 4 Carbon & Argon Weekly` shared rows, and priority-sorted cards in `skills/check-quota/resources/dashboard/quota_dashboard.html`.

**Architecture:** Define `AccountMeta` in `scripts/types/quota_dashboard.types.ts` and implement four pure provider normalizers (`normalize_antigravity_account`, `normalize_claude_account`, `normalize_codex_account`, `normalize_kiro_account`) plus JWT offline claim decoding, `state.vscdb` email enrichment, live `/usage` description prefix/prose filtering, dynamic CLI tags, and daemon `server_code_mtime` auto-reload in `scripts/agy_quota.py`. Consume this unified SSOT in `quota_dashboard.html` for card headers, model roster subtitles, `openProfileInfoModal()`, `DEFAULT` priority sorting, and search filtering.

**Tech Stack:** Python 3.11+ (stdlib `sqlite3`, `base64`, `json`, `urllib`), TypeScript declarations, HTML5 / Tailwind CSS / Vanilla JavaScript (ES2020), `pytest`, Node.js `vm` harness, Chrome DevTools (`browser` subagent).

**Spec:** [2026-11-18-check-quota-dynamic-provider-account-tiers-design.md](../specs/2026-11-18-check-quota-dynamic-provider-account-tiers-design.md)

## Table of Contents

- [Global Constraints](#global-constraints)
- [File Structure](#file-structure)
- [Implementation Tasks](#implementation-tasks)
  - [Task 1: AccountMeta Contract, 4-Provider Normalizers, Live Usage Parser Fix, CLI Dynamic Priority, and Daemon Code-Sync in agy_quota.py](#task-1-accountmeta-contract-4-provider-normalizers-live-usage-parser-fix-cli-dynamic-priority-and-daemon-code-sync-in-agy_quotapy)
  - [Task 2: Unified 4-Provider Card Headers, Provider-Aware Info Modal, Ultra Carbon and Argon Row, Priority Sort, and Live Browser Verification in quota_dashboard.html](#task-2-unified-4-provider-card-headers-provider-aware-info-modal-ultra-carbon-and-argon-row-priority-sort-and-live-browser-verification-in-quota_dashboardhtml)

## Global Constraints

- Always invoke `pytest` as `python3 -m pytest` from the repository/worktree root.
- Zero Secret Leakage: NEVER include `accessToken`, `refreshToken`, `id_token`, `kas_token`, or raw authorization headers in `accountMeta`, `PROFILES_DATA`, `/api/status`, or logs.
- Deterministic Priority Matrix (exact values from spec):
  - **Claude**: `CLAUDE MAX 20X = 110`, `CLAUDE MAX 5X / CLAUDE MAX / CLAUDE ENTERPRISE = 105`, `CLAUDE TEAM = 102`, `CLAUDE PRO = 100`, `CLAUDE API = 98`, `CLAUDE FREE = 40`.
  - **Codex**: `CHATGPT PRO / CHATGPT ENTERPRISE = 98`, `CHATGPT TEAM / CHATGPT EDU = 96`, `CHATGPT PLUS = 95`, `OPENAI API = 92`, `CHATGPT FREE = 35`.
  - **Kiro**: `KIRO POWER = 94`, `KIRO PRO+ = 92`, `KIRO PRO / KIRO STUDENT = 90`, `KIRO FREE = 30`.
  - **Antigravity**: `ULTRA = 80`, `PRO` with `argonMode == "separate"` `= 60`, `PRO` standard `= 50`, `FREE = 20`.
- Follow Universal Commit Message Format (`[CHECK_QUOTA] Imperative title` + `- bullet` lines, zero trailers). Never run `git push`.

---

## File Structure

- Modify: `scripts/types/quota_dashboard.types.ts` — Add `AccountMeta` interface and optional `planLabel`, `vendorLabel`, `accountMeta` fields on `ProfileQuotaState`.
- Modify: `scripts/agy_quota.py` — Fix `parse_usage_group_models()` prefix/prose handling; add `_decode_jwt_claims_unverified()`, `read_antigravity_vscdb_email()`, `normalize_antigravity_account()`, `normalize_claude_account()`, `normalize_codex_account()`, `normalize_kiro_account()`; wire into `fetch_claude_quota()`, `fetch_codex_quota()`, `parse_kiro_usage_limits()`, `fetch_kiro_quota()`, `format_profile_for_dashboard()`, `_preserve_cached_model_meta()`, `execute_ping_profile()`, CLI `print_*_card` functions, `load_cached_profiles()` HTML `mtime` tracking, and `SERVER_STARTUP_MTIME` daemon reload check.
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html` — Unified 4-provider header pills (`[Vendor]`, `[Dynamic Plan Badge]`, `[Priority: X]`), `ℹ` modal button for all 4 providers, `Gemini 4 Carbon & Argon Weekly` row on `ULTRA` (`hasCarbon && sharedPool`), roster subtitles on `Gemini Models 5H` + `Gemini Weekly` + `Codex` + `Claude`, provider-aware `openProfileInfoModal()`, `DEFAULT` sort (`claude -> codex -> kiro`, then Antigravity by `priority DESC, profile ASC`), and `searchInput` tier/model matching.
- Create: `tests/test_check_quota_dynamic_provider_tiers.py` — Grounded TDD unit tests (using verbatim live CLI/API payload shapes) and Node.js `vm` UI tests.

## Implementation Tasks

### Task 1: AccountMeta Contract, 4-Provider Normalizers, Live Usage Parser Fix, CLI Dynamic Priority, and Daemon Code-Sync in agy_quota.py

**Files:**
- Modify: `scripts/types/quota_dashboard.types.ts:80-105`
- Modify: `scripts/agy_quota.py:230-285`
- Modify: `scripts/agy_quota.py:609-625`
- Modify: `scripts/agy_quota.py:1555-1585`
- Modify: `scripts/agy_quota.py:1743-1840`
- Modify: `scripts/agy_quota.py:2208-2850`
- Modify: `scripts/agy_quota.py:2879-3425`
- Modify: `scripts/agy_quota.py:3565-3625`
- Modify: `scripts/agy_quota.py:4180-4202`
- Modify: `scripts/agy_quota.py:4595-4610`
- Create: `tests/test_check_quota_dynamic_provider_tiers.py`

**Interfaces:**
- Consumes: `parse_usage_group_models`, `_derive_profile_capabilities`, `fetch_claude_quota`, `fetch_codex_quota`, `parse_kiro_usage_limits`, `fetch_kiro_quota`, `format_profile_for_dashboard` in `scripts/agy_quota.py`.
- Produces:
  - `AccountMeta` in `scripts/types/quota_dashboard.types.ts`
  - `normalize_antigravity_account(...)`, `normalize_claude_account(...)`, `normalize_codex_account(...)`, `normalize_kiro_account(...)`, `_decode_jwt_claims_unverified(token)`, `read_antigravity_vscdb_email(profile)` in `scripts/agy_quota.py`
  - Top-level `tier`, `planLabel`, `vendorLabel`, `priority`, `availableModels`, and `accountMeta` populated across all 4 providers
  - `SERVER_STARTUP_MTIME` in `/api/status` and stale-daemon auto-restart in `start_server_daemon()`.

- [ ] **Step 1: Write the failing backend unit tests grounded in verbatim live payloads**

Create `tests/test_check_quota_dynamic_provider_tiers.py` with module-scoped `agy_quota` import and parametrized tests covering:
1. `test_parse_usage_group_models_strips_live_prefix_and_skips_argon_prose`:
   - Ultra live description `"Models within this group: Gemini 4 Carbon, Gemini 4 Argon, Gemini 4 Hydrogen, Orchestrator (Carbon), Orchestrator (Argon), Gemini 3.8 Flash"` -> `groupModels["gemini"][0] == "Gemini 4 Carbon"` (zero `"Models within this group:"` prefix).
   - Pro dedicated Argon group `"For paid Pro plans, Argon quota is separate. Higher Argon quota (included as part of the larger Gemini quota bucket) is available on Ultra plans."` -> `groupModels["argon"] == []` before `_reconcile_group_models`, and `_reconcile_group_models` produces `["Gemini 4 Argon"]` with zero prose clauses.
2. `test_antigravity_tier_and_priority_matrix` (`@pytest.mark.parametrize`):
   - `ULTRA` (`nguyenhieu000690` live groups) -> `tier == "ULTRA"`, `priority == 80`, `argonWeekly["name"] == "Gemini 4 Carbon & Argon Weekly"`.
   - `PRO` with dedicated Argon (`danhdue` live groups) -> `tier == "PRO"`, `priority == 60`, `planLabel == "PRO"`.
   - `PRO` without Argon (`d3molt` live groups) -> `tier == "PRO"`, `priority == 50`.
   - `FREE` (`buivantrong8901` live groups) -> `tier == "FREE"`, `priority == 20`.
   - Disabled / Auth-Needed preservation keeps cached `tier="ULTRA"`, `priority=80`, and `accountMeta`.
   - `execute_ping_profile` fallback treats `tier == "ULTRA"` as having 5H buckets available (`default_available=True`).
3. `test_claude_tier_and_priority_matrix` (`@pytest.mark.parametrize`):
   - `subscriptionType="max", rateLimitTier="default_claude_max_20x"` -> `tier == "CLAUDE MAX 20X"`, `priority == 110`.
   - `subscriptionType="max", rateLimitTier="default_claude_max_5x"` -> `tier == "CLAUDE MAX 5X"`, `priority == 105`.
   - `organizationType="claude_team"` -> `tier == "CLAUDE TEAM"`, `priority == 102`.
   - `subscriptionType="pro", organizationType="claude_pro"` -> `tier == "CLAUDE PRO"`, `priority == 100`, `vendorLabel == "ANTHROPIC"`, `accountMeta["organizationName"]` populated, zero tokens leaked.
   - `subscriptionType="free"` -> `tier == "CLAUDE FREE"`, `priority == 40`.
4. `test_codex_online_and_offline_jwt_tier_matrix` (`@pytest.mark.parametrize`):
   - Online `wham/usage` with `plan_type="pro"` -> `tier == "CHATGPT PRO"`, `priority == 98`; `plan_type="team"` -> `CHATGPT TEAM`, `96`; `plan_type="plus"` + `model_usage={"gpt-6-astra": {"available": True}}` -> `CHATGPT PLUS`, `95`, `availableModels == ["gpt-6-astra"]`; `plan_type="free"` -> `CHATGPT FREE`, `35`.
   - Offline fallback with valid synthetic base64url JWT in `~/.codex/auth.json` (`{"email": "dev@example.com", "https://api.openai.com/auth": {"chatgpt_plan_type": "pro"}}`) -> decodes `email == "dev@example.com"`, `tier == "CHATGPT PRO"`, `priority == 98` without network calls and without exposing the JWT string in the returned dict.
5. `test_kiro_tier_matrix_and_offline_cache_preservation` (`@pytest.mark.parametrize`):
   - `KIRO POWER` (`10000` credits) -> `94`; `KIRO PRO+` (`2000` credits) -> `92`; `KIRO STUDENT` (`1000` credits) -> `90`; `KIRO FREE` (`50` credits) -> `30`.
   - Offline fallback preserves cached `tier="KIRO STUDENT"`, `email="Elenor.Zulaufell001@mymdc.net"`, `creditsPool.used=988.32`, `creditsPool.limit=1000.0`.
6. `test_types_file_declares_account_meta`:
   - `scripts/types/quota_dashboard.types.ts` declares `export interface AccountMeta` and `accountMeta?: AccountMeta`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_check_quota_dynamic_provider_tiers.py -v`
Expected: FAIL on missing normalizers, `"Models within this group:"` prefix retention, hardcoded `tier="PRO"` / `priority=50` on Ultra, hardcoded `"ANTHROPIC"` / `"OPENAI"`, and missing `AccountMeta`.

- [ ] **Step 3: Update `scripts/types/quota_dashboard.types.ts` and implement normalizers in `scripts/agy_quota.py`**

1. In `scripts/types/quota_dashboard.types.ts`:
   - Add `export interface AccountMeta` with fields `provider`, `vendorLabel`, `planType`, `planLabel`, `organizationName?`, `organizationType?`, `billingType?`, `rateLimitTier?`, `authSource?`, `cliCommand?`, `configPath?`, `secondaryPath?`, `extraUsageEnabled?`, `extraUsageSummary?`, `resetCredits?`, `creditsSummary?`, `overageStatus?`, `overageRateSummary?`, and add `planLabel?: string; vendorLabel?: string; accountMeta?: AccountMeta;` onto `ProfileQuotaState`.
2. In `scripts/agy_quota.py`:
   - **Fix `parse_usage_group_models()` (`L231-282`)**:
     ```python
     _GROUP_MODELS_PREFIX_RE = re.compile(r"^models\s+within\s+this\s+group\s*:\s*", re.IGNORECASE)
     _PROSE_DESC_MARKERS = (
         "for paid ",
         "quota is ",
         "available on ",
         "within each group",
         "limits will last",
         "you have used",
     )
     ```
     Strip `_GROUP_MODELS_PREFIX_RE.sub("", norm_desc)` before splitting on commas; if `any(marker in norm_desc.lower() for marker in _PROSE_DESC_MARKERS)` and not `_GROUP_MODELS_PREFIX_RE.match(norm_desc)`, skip token extraction for that prose description while still recording `groupDescriptions[family]` and `sig_pairs`.
   - **Add `format_priority_tag(priority: int) -> str`** (`L612`) so CLI cards render `Priority: {priority}` dynamically instead of static `Priority: 50` / `100` / `95` / `90`.
   - **Add `_decode_jwt_claims_unverified(token: str) -> dict`**:
     ```python
     def _decode_jwt_claims_unverified(token: object) -> dict:
         if not isinstance(token, str) or token.count(".") != 2:
             return {}
         try:
             seg = token.split(".")[1]
             seg += "=" * (-len(seg) % 4)
             import base64
             raw = base64.urlsafe_b64decode(seg.encode("ascii")).decode("utf-8")
             parsed = json.loads(raw)
             return parsed if isinstance(parsed, dict) else {}
         except Exception:
             return {}
     ```
   - **Add `read_antigravity_vscdb_email(profile: str) -> str | None`**: open `~/antigravity_homes/<profile>/Library/Application Support/Antigravity/User/globalStorage/state.vscdb` in read-only SQLite URI mode (`?mode=ro`, timeout `1.0s`), read `ItemTable` where `key = 'antigravityAuthStatus'`, parse JSON `email`, and return non-empty email string or `None`.
   - **Add the 4 deterministic normalizers**:
     - `normalize_antigravity_account(profile, capabilities, argon_mode, email)`: maps `ULTRA -> ("ULTRA", "ULTRA", 80)`, `PRO + separate -> ("PRO", "PRO", 60)`, `PRO -> ("PRO", "PRO", 50)`, `FREE -> ("FREE", "FREE", 20)`, building `accountMeta` (`provider="antigravity"`, `vendorLabel="GOOGLE"`, `cliCommand=f"{profile}-cli"`, `configPath=f"~/antigravity_homes/{profile}"`, `secondaryPath=f"~/antigravity_homes/{profile}/Library/Keychains/{profile}.keychain-db"`). Also on `ULTRA` (`argon_mode == "shared_gemini"` and `capabilities.get("hasCarbon")`), set `argonWeekly["name"] = "Gemini 4 Carbon & Argon Weekly"` (and mirror in CLI `print_dashboard_cards`).
     - `normalize_claude_account(oauth_hints, oauth_acc, api_data, is_live)`: inspects `subscriptionType`, `rateLimitTier`, `organizationType`, `organizationRateLimitTier`, `userRateLimitTier`, `has_claude_max`, `has_claude_pro`; maps to `CLAUDE MAX 20X (110)`, `CLAUDE MAX 5X / CLAUDE MAX / CLAUDE ENTERPRISE (105)`, `CLAUDE TEAM (102)`, `CLAUDE PRO (100)`, `CLAUDE API (98)`, `CLAUDE FREE (40)` (defaulting to `CLAUDE PRO (100)` when logged in without explicit free/max markers), builds `accountMeta` (`vendorLabel="ANTHROPIC"`, `organizationName`, `billingType`, `rateLimitTier`, `authSource`, `cliCommand="claude"`, `configPath="~/.claude.json"`, `extraUsageEnabled`, `extraUsageSummary`), and derives `availableModels` from scoped buckets or tier family (`Claude Opus 4.6, Claude Sonnet 4.6, Claude Haiku 4.5`). Extend `get_claude_oauth_token()` (with backward-compatible 3-tuple return, plus `_read_claude_oauth_hints()` helper) to read non-secret `subscriptionType` & `rateLimitTier` from Keychain / `.credentials.json`.
     - `normalize_codex_account(api_data, auth_data)`: resolves `plan_type` from `api_data.get("plan_type")` or JWT `https://api.openai.com/auth` -> `chatgpt_plan_type` (or `auth_mode == "apikey"`), resolves `email` from `api_data.get("email")` or JWT `email` / `https://api.openai.com/profile` -> `email`, maps to `CHATGPT PRO / CHATGPT ENTERPRISE (98)`, `CHATGPT TEAM / CHATGPT EDU (96)`, `CHATGPT PLUS (95)`, `OPENAI API (92)`, `CHATGPT FREE (35)`, extracts `availableModels` from `api_data.get("model_usage")` (`[m for m, info in model_usage.items() if isinstance(info, dict) and info.get("available")]`), and builds `accountMeta` (`vendorLabel="OPENAI"`, `cliCommand="codex"`, `configPath="~/.codex/auth.json"`, `resetCredits`, `creditsSummary`).
     - `normalize_kiro_account(api_data, email, cached_entry, whoami_auth="")`: inspects `subscriptionInfo.subscriptionTitle`, `subscriptionInfo.type`, and `limit` (`POWER` or `limit >= 10000` -> `94`; `PRO_PLUS` / `PRO+` or `limit >= 2000` -> `92`; `FREE` or `0 < limit <= 100` -> `30`; `PRO` / `STUDENT` -> `90`), extracts `bonuses` and `overageRate`, and preserves cached `tier`, `planLabel`, `priority`, `email`, and `creditsPool` on offline fallback.
   - **Update `_preserve_cached_model_meta()`** (`L3107`): also preserve `"planLabel"`, `"vendorLabel"`, `"accountMeta"` and keep cached `"tier"` / `"priority"`.
   - **Update `execute_ping_profile()`** (`L3616, L3619`): change `default_available=(tier == "PRO" or not tier)` to `default_available=(tier != "FREE")`.
   - **Daemon & Cache Mtime Sync**:
     - Record `SERVER_STARTUP_MTIME = int(Path(__file__).stat().st_mtime)` at module import; include `"server_code_mtime": SERVER_STARTUP_MTIME` in `/api/status`.
     - Track `CACHED_HTML_MTIME: float = 0.0` in `load_cached_profiles()` / `update_cached_profile()` so external disk updates to `quota_dashboard.html` reload `CACHED_PROFILES_DATA` automatically.
     - In `start_server_daemon(port)`: when `is_server_alive(port)` is True, check `/api/status` `server_code_mtime`; if missing or `!= int(Path(__file__).stat().st_mtime)`, call `stop_server(port)` and spawn a fresh daemon automatically.

- [ ] **Step 4: Run tests to verify GREEN and zero regressions**

Run: `python3 -m pytest tests/test_check_quota_dynamic_provider_tiers.py tests/test_cqra_quota_discovery.py tests/test_cqra_refresh_session_argon.py -q --tb=short`
Expected: PASS (`0 failures`).

- [ ] **Step 5: Commit Task 1**

```bash
git add scripts/types/quota_dashboard.types.ts scripts/agy_quota.py tests/test_check_quota_dynamic_provider_tiers.py
git commit -m "[CHECK_QUOTA] Normalize dynamic account tiers, priorities, and metadata across 4 providers" \
  -m "- Add AccountMeta contract and normalizers for Antigravity, Claude, Codex, and Kiro" \
  -m "- Strip live usage group prefix and skip prose descriptions on Pro Argon groups" \
  -m "- Support offline Codex JWT plan claims, Kiro cache preservation, Ultra 5H ping, and daemon mtime reload"
```

---

### Task 2: Unified 4-Provider Card Headers, Provider-Aware Info Modal, Ultra Carbon and Argon Row, Priority Sort, and Live Browser Verification in quota_dashboard.html

**Files:**
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:2410-2565`
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:2745-2795`
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:2975-3080`
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:3120-3210`
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:3430-3450`
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:4615-4695`
- Modify: `tests/test_check_quota_dynamic_provider_tiers.py`

**Interfaces:**
- Consumes: `tier`, `planLabel`, `vendorLabel`, `priority`, `availableModels`, `accountMeta`, and `capabilities` produced by Task 1.
- Produces:
  - `getProviderHeaderBadgesHTML(profile, data)` and `getCarbonArgonOrchestratorModels(data)` in `quota_dashboard.html`
  - Unified header rendering (`[ℹ]`, `[Vendor Pill]`, `[Plan Badge]`, `[Priority: X]`, `[Status]`) across all 4 providers
  - `Gemini 4 Carbon & Argon Weekly` (`Shared w/ Gemini Pool`) row + `Gemini Weekly` model subtitle on Antigravity `ULTRA` cards
  - Provider-aware `openProfileInfoModal(profile)` supporting `claude`, `codex`, `kiro`, and Antigravity profiles
  - `DEFAULT` sort ordering `claude -> codex -> kiro`, then Antigravity profiles by `priority DESC, profile ASC`.

- [ ] **Step 1: Write the failing Node VM UI tests in `tests/test_check_quota_dynamic_provider_tiers.py`**

Append Node VM UI tests (following the `vm.createContext` harness pattern in `tests/test_cqra_quota_ui.py`) asserting:
1. Provider cards (`claude`, `codex`, `kiro`) render their vendor pill (`ANTHROPIC`, `OPENAI`, `KIRO`), dynamic plan badge (`CLAUDE PRO` / `CLAUDE MAX 20X`, `CHATGPT PLUS` / `CHATGPT PRO`, `KIRO STUDENT` / `KIRO PRO+`), dynamic `Priority: 100` / `95` / `90` badge, `openProfileInfoModal('claude')` `ℹ` button, dynamic Codex model subtitle (`Available models: gpt-6-astra`), and reset credit pill without hardcoded `"02/12"`.
2. Antigravity `ULTRA` profile (`nguyenhieu000690`, `tier: "ULTRA"`, `priority: 80`, `capabilities.hasCarbon: true`, `argonMode: "shared_gemini"`) renders `✦ ULTRA`, `Priority: 80`, `◈ Carbon`, `✣ Argon`, `⌘ Orchestrator`, roster subtitles on both `Gemini Models 5H` and `Gemini Weekly`, and Row 3 titled `Gemini 4 Carbon & Argon Weekly` with `Shared w/ Gemini Pool` and Carbon + Argon + Orchestrator models.
3. `getOrderedProfiles()` under `DEFAULT` sort returns `["claude", "codex", "kiro", "nguyenhieu000690" (80), "danhdue" (60), "d3molt" (50), "buivantrong8901" (20)]` (with `A-Z` tie-breaking within the same priority).
4. `openProfileInfoModal('claude')` and `openProfileInfoModal('codex')` populate email, dynamic tier + priority, organization / billing / credits metadata, `claude` / `codex` CLI command, and `~/.claude.json` / `~/.codex/auth.json` config path while hiding Antigravity-only keychain rows; `searchInput` filters by `"chatgpt plus"`, `"claude pro"`, `"ultra"`, and `"gpt-6-astra"`.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_check_quota_dynamic_provider_tiers.py -v`
Expected: FAIL on missing provider plan/priority badges, missing provider `ℹ` button, `DEFAULT` alphabetical sort, and `openProfileInfoModal` Antigravity-only paths.

- [ ] **Step 3: Implement unified UI updates in `skills/check-quota/resources/dashboard/quota_dashboard.html`**

1. Add `getCarbonArgonOrchestratorModels(data)` near `getArgonOrchestratorModels(data)` (`L2425`): when `data?.capabilities?.hasCarbon && isSharedArgonPool(data)`, collect Carbon + Argon + Orchestrator labels from `groupModels` and `modelCatalog` so the shared Ultra row displays both Carbon and Argon families cleanly.
2. Add `getProviderPlanBadgeHTML(profile, data)` (`L2490`) rendering a styled `[data-tier-badge="..."]` pill for `planLabel || data.tier` (e.g. `CLAUDE MAX 20X`, `CLAUDE PRO`, `CHATGPT PRO`, `CHATGPT PLUS`, `KIRO STUDENT`, `KIRO PRO+`).
3. Update `renderProfileCard(profile, rawData)` (`L2752-2793`):
   - Enable the `ℹ` `openProfileInfoModal('${profile}')` button for ALL cards (both Providers and Antigravity profiles).
   - For `data.isProvider`, render:
     - Vendor pill (`✺ ANTHROPIC` for `claude`, `✱ OPENAI` for `codex`, `👻 KIRO` for `kiro`)
     - `${getProviderPlanBadgeHTML(profile, data)}`
     - `${getPriorityBadgeHTML(data.priority ?? (profile === 'claude' ? 100 : (profile === 'codex' ? 95 : 90)))}`
     - Dynamic `${data.resetCredits ? ...}` pill on `codex` with tooltip `"Có ${escapeHtml(data.resetCredits)} vé Full Reset khả dụng"` (removing hardcoded `"02/12"`).
4. Update card body (`L2975-3078`):
   - On `claude`: pass `extraUsageSummary` (from `data.accountMeta?.extraUsageSummary`) as `subtitle` on the first session bucket when enabled.
   - On `codex`: compute `codexRoster = Array.isArray(data.availableModels) && data.availableModels.length > 0 ? 'Available models: ' + data.availableModels.join(', ') : ''` and pass as `subtitle` to `Codex 5-Hour Limit`.
   - On `kiro`: display `data.accountMeta?.creditsSummary` or `Used: ${data.creditsPool?.used ?? 0} / ${data.creditsPool?.limit ?? 1000} credits` and `Overages: ${data.overageStatus ?? 'DISABLED'}`.
   - On `Antigravity`:
     - Pass `geminiRoster` as `subtitle` to `Gemini Weekly` (`L3073`) as well as `Gemini Models 5H`.
     - When `argonMode === "shared_gemini" || sharedPool`: if `data.capabilities?.hasCarbon`, default Row 3 title to `"Gemini 4 Carbon & Argon Weekly"` (or `aWeekly.name` when already `"Gemini 4 Carbon & Argon Weekly"`) and pass `getCarbonArgonOrchestratorModels(data).join(", ")` as `subtitle`.
5. Update `getOrderedProfiles()` (`L3204-3206`):
   ```javascript
   // DEFAULT: Pin providers (claude -> codex -> kiro) at top, then satellite profiles by Priority DESC, A-Z
   const sortedSatellites = nonProviders.sort((a, b) => {
     const pa = Number(PROFILES_DATA[a]?.priority ?? 50);
     const pb = Number(PROFILES_DATA[b]?.priority ?? 50);
     if (pa !== pb) return pb - pa;
     return a.localeCompare(b);
   });
   return [...providers, ...sortedSatellites];
   ```
6. Extend `searchInput` matching in `renderAllProfiles()` (`L3440-3446`) to match `data.tier`, `data.planLabel`, `data.vendorLabel`, `data.accountMeta?.organizationName`, and `data.availableModels`.
7. Make `openProfileInfoModal(profile)` (`L4617-4692`) provider-aware:
   - Read `meta = data.accountMeta || {}`.
   - Set `#infoModalEmail` to `data.email || (data.isProvider ? profile : `${profile}@gmail.com`)`.
   - Set `#infoModalTier` to `${displayPlan} (Priority ${data.priority ?? 50})${extraTierSuffix}` (including `meta.organizationName`, `meta.rateLimitTier`, or `meta.creditsSummary` when present).
   - Set `#infoModalCliCmd` to `meta.cliCommand || (data.isProvider ? (profile === 'kiro' ? 'kiro-cli' : profile) : `${profile}-cli`)`.
   - Set `#infoModalHomePath` to `meta.configPath || `~/antigravity_homes/${profile}`` and `#infoModalKeychainPath` to `meta.secondaryPath || (data.isProvider ? (meta.authSource || 'Local OAuth / CLI Credentials') : `~/antigravity_homes/${profile}/Library/Keychains/${profile}.keychain-db`)`.
   - Populate `#infoModalBadges` and `#infoModalGeminiModels` with provider `availableModels` / `quotaBuckets` scopes when `data.isProvider` is true.

- [ ] **Step 4: Run automated tests to verify GREEN**

Run: `python3 -m pytest tests/test_check_quota_dynamic_provider_tiers.py tests/test_cqra_quota_ui.py tests/test_cqra_quota_discovery.py -q --tb=short`
Expected: PASS (`0 failures`).

- [ ] **Step 5: Live Web Browser Verification (`browser` subagent)**

Refresh cached provider & key profile entries (`claude`, `codex`, `kiro`, `nguyenhieu000690`, `danhdue`, `d3molt`, `buivantrong8901`) using the worktree's `scripts/agy_quota.py`, launch a temporary server on port `18765`, and invoke `browser` subagent to open `http://127.0.0.1:18765`:
1. Verify `claude`, `codex`, `kiro` cards show dynamic plan badges (`CLAUDE PRO`, `CHATGPT PLUS`, `KIRO STUDENT`), `Priority: 100` / `95` / `90`, and working `ℹ` Account Info modal.
2. Verify `nguyenhieu000690` sits at the top of Antigravity profiles under `DEFAULT` sort with `✦ ULTRA`, `Priority: 80`, `◈ Carbon`, `✣ Argon`, `⌘ Orchestrator`, clean model subtitles (zero `"Models within this group:"` prefix), and `Gemini 4 Carbon & Argon Weekly` (`Shared w/ Gemini Pool`).
3. Verify `danhdue` displays `◆ PRO`, `Priority: 60`, `✣ Argon` (`100%`) with clean model subtitle (zero prose leakage), zero console errors, capture screenshot artifact, and stop the temporary server (restoring `quota_dashboard.html` `PROFILES_DATA` before committing code-only changes).

- [ ] **Step 6: Commit Task 2**

```bash
git add skills/check-quota/resources/dashboard/quota_dashboard.html tests/test_check_quota_dynamic_provider_tiers.py
git commit -m "[CHECK_QUOTA] Render dynamic 4-provider badges, info modal, Ultra Carbon-Argon row, and priority sort" \
  -m "- Display vendor pill, dynamic plan badge, priority pill, and info modal across Claude, Codex, and Kiro" \
  -m "- Render Gemini 4 Carbon and Argon Weekly shared row on Ultra profiles and dynamic model subtitles" \
  -m "- Order Antigravity profiles by priority descending in DEFAULT sort and expand search matching"
```
