# Dynamic Google Profile Data Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch and normalize live Google subscription tiers (`ULTRA` / `PRO` / `FREE`), official plan display names (`Google AI Ultra`, `Google AI Pro`, `Antigravity Starter Quota`), authenticated OAuth emails, and AI credits for every Antigravity profile directly from Google APIs (`aicode.googleapis.com/v1alpha:fetchLicenses`), Keychain OAuth tokens, and `state.vscdb`.

**Architecture:** After `agy --output-format json -p /usage` refreshes the profile's OAuth session in Keychain, `scripts/agy_quota.py` reads the profile's OAuth record (`read_antigravity_oauth_record`) to extract the in-memory `access_token`, `id_token_email`, and `auth_method`, queries `GET https://aicode.googleapis.com/v1alpha:fetchLicenses` (`fetch_antigravity_google_license`), and optionally queries `/credits` (`_query_agy_credits`) when the 24-hour hybrid discovery cache is cold. The normalized metadata is surfaced in `normalize_antigravity_account`, terminal CLI cards, and the Web Dashboard (`quota_dashboard.html`).

**Tech Stack:** Python 3 (`urllib.request`, `sqlite3`, `subprocess`, `json`, `base64`), Vanilla JavaScript + Tailwind CSS (`quota_dashboard.html`), `pytest`.

**Spec:** `docs/superpowers/specs/2026-11-24-dynamic-google-profile-data-design.md`

## Table of Contents

- [Global Constraints](#global-constraints)
- [Task 1: Dynamic Google OAuth Email, License Tier, and Credits Discovery in agy_quota.py](#task-1-dynamic-google-oauth-email-license-tier-and-credits-discovery-in-agy_quotapy)
- [Task 2: Dashboard UI Info Modal & Live Profile Cache Refresh](#task-2-dashboard-ui-info-modal--live-profile-cache-refresh)

## Global Constraints

- Never persist or log `access_token`, `refresh_token`, or `id_token` in `accountMeta`, `PROFILES_DATA`, or terminal/HTTP responses.
- Preserve existing mock compatibility in `tests/test_check_quota_dynamic_provider_tiers.py` (where `subprocess.run` is monkeypatched and `fake_run` only expects `security`, `agy models`, `agy -p /usage`, or `agy -p /credits`).
- Fall back gracefully to cached `accountMeta` or `plan_name` / `has_5h` heuristics when offline or when `fetchLicenses` returns an HTTP/network error.

---

### Task 1: Dynamic Google OAuth Email, License Tier, and Credits Discovery in agy_quota.py

**Files:**
- Modify: `scripts/agy_quota.py:680-766`
- Modify: `scripts/agy_quota.py:1390-1566`
- Modify: `scripts/agy_quota.py:3952-4266`
- Test: `tests/test_check_quota_dynamic_provider_tiers.py`

**Interfaces:**
- Produces:
  - `read_antigravity_oauth_record(profile: str) -> dict`
  - `read_antigravity_vscdb_email(profile: str) -> str | None`
  - `fetch_antigravity_google_license(profile: str, access_token: str | None = None) -> dict`
  - `_query_agy_credits(env: dict[str, str], cwd: str) -> dict | None`
  - `normalize_antigravity_account(profile: str, capabilities: dict | None, argon_mode: str = "none", email: str | None = None, license_info: dict | None = None, oauth_info: dict | None = None, credits_info: dict | None = None) -> dict`

- [ ] **Step 1: Write the failing unit tests in `tests/test_check_quota_dynamic_provider_tiers.py`**

```python
def test_dynamic_google_oauth_license_and_vscdb_discovery(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify Keychain go-keyring-base64 decoding, dual-path state.vscdb email, and live Google fetchLicenses tier resolution."""
    _setup_isolated_env(tmp_path, monkeypatch, ["tess", "brother", "phungthuy8901"])

    # 1. Populate modern data/User/globalStorage/state.vscdb for 'brother'
    modern_vscdb = (
        tmp_path
        / "antigravity_homes"
        / "brother"
        / "data"
        / "User"
        / "globalStorage"
        / "state.vscdb"
    )
    modern_vscdb.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(modern_vscdb))
    con.execute("CREATE TABLE ItemTable (key TEXT PRIMARY KEY, value TEXT);")
    con.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?);",
        (
            "google.google-antigravity",
            json.dumps(
                {
                    "antigravity-storage": {
                        "agy.onboarding.lastLoginUsername": "dvtung0868377966@gmail.com"
                    }
                }
            ),
        ),
    )
    con.commit()
    con.close()

    assert (
        agy_quota.read_antigravity_vscdb_email("brother")
        == "dvtung0868377966@gmail.com"
    )

    # 2. Simulate go-keyring-base64 Keychain payload for 'tess'
    kc_payload = {
        "token": {
            "access_token": "ya29.tess_live_token",
            "refresh_token": "1//tess_refresh",
            "expiry": "2026-12-01T00:00:00Z",
        },
        "auth_method": "consumer",
        "id_token_email": "ldejong322@gmail.com",
    }
    encoded_kc = "go-keyring-base64:" + base64.b64encode(
        json.dumps(kc_payload).encode("utf-8")
    ).decode("ascii")

    kc_file = (
        tmp_path
        / "antigravity_homes"
        / "tess"
        / "Library"
        / "Keychains"
        / "tess.keychain-db"
    )
    kc_file.parent.mkdir(parents=True, exist_ok=True)
    kc_file.write_text("dummy", encoding="utf-8")

    usage_stdout = json.dumps(
        {
            "command": {
                "data": {
                    "groups": [
                        {
                            "name": "Gemini Models",
                            "description": "Models within this group: Gemini 4 Carbon, Gemini 4 Argon, Gemini 3.8 Flash",
                            "buckets": [
                                {
                                    "window": "5h",
                                    "remaining_fraction": 0.95,
                                    "reset_time": "2026-11-24T20:00:00Z",
                                },
                                {
                                    "window": "weekly",
                                    "remaining_fraction": 0.92,
                                    "reset_time": "2026-11-30T20:00:00Z",
                                },
                            ],
                        }
                    ]
                }
            }
        }
    )
    credits_stdout = json.dumps(
        {
            "command": {
                "name": "credits",
                "data": {"remaining_credits": 250},
            }
        }
    )

    def fake_run(cmd: list[str], **_kw: Any) -> MagicMock:
        if cmd and cmd[0] == "security":
            if "find-generic-password" in cmd and "-w" in cmd:
                return MagicMock(returncode=0, stdout=encoded_kc, stderr="")
            return MagicMock(returncode=0, stdout="", stderr="")
        if len(cmd) >= 2 and cmd[1] == "models":
            return MagicMock(returncode=0, stdout="gemini-4-argon-high\n", stderr="")
        if "/credits" in cmd:
            return MagicMock(returncode=0, stdout=credits_stdout, stderr="")
        if "/usage" in cmd:
            return MagicMock(returncode=0, stdout=usage_stdout, stderr="")
        raise AssertionError(f"Unexpected command: {cmd}")

    class _FakeResp:
        status = 200

        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *_a: Any) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "licenses": [
                        {
                            "userTier": "g1-ultra-tier",
                            "tierDisplayName": "Google AI Ultra",
                            "upgradeSubscription": {
                                "text": "You are subscribed to the best Google AI plan."
                            },
                        }
                    ]
                }
            ).encode("utf-8")

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda req, timeout=4.0: _FakeResp(),
    )

    res = agy_quota.fetch_quota_for_profile("tess")
    assert res["success"] is True
    assert res["tier"] == "ULTRA"
    assert res["priority"] == 80
    formatted = agy_quota.format_profile_for_dashboard("tess", res)
    assert formatted["tier"] == "ULTRA"
    assert formatted["planLabel"] == "ULTRA"
    assert formatted["priority"] == 80
    assert formatted["email"] == "ldejong322@gmail.com"
    assert formatted["accountMeta"]["userTier"] == "g1-ultra-tier"
    assert formatted["accountMeta"]["tierDisplayName"] == "Google AI Ultra"
    assert formatted["accountMeta"]["authMethod"] == "consumer"
    assert formatted["accountMeta"]["remainingCredits"] == 250
    _assert_zero_secret_leakage(
        formatted, ["ya29.tess_live_token", "1//tess_refresh"]
    )
```

- [ ] **Step 2: Run pytest to verify the new test fails**

Run: `pytest tests/test_check_quota_dynamic_provider_tiers.py -k test_dynamic_google_oauth_license_and_vscdb_discovery -v`
Expected: FAIL (`brother` vscdb email returns `None` and `tess` tier defaults to `"PRO"` instead of `"ULTRA"`).

- [ ] **Step 3: Implement `read_antigravity_oauth_record`, dual-path `read_antigravity_vscdb_email`, `fetch_antigravity_google_license`, and `_query_agy_credits` in `scripts/agy_quota.py`**

Update `scripts/agy_quota.py` around lines 680-766, 1390-1566, and 3952-4266 so that:
1. `read_antigravity_vscdb_email(profile)` checks both `data/User/globalStorage/state.vscdb` and `Library/Application Support/Antigravity/User/globalStorage/state.vscdb` for `antigravityAuthStatus` and `google.google-antigravity` (`antigravity-storage.agy.onboarding.lastLoginUsername`).
2. `read_antigravity_oauth_record(profile)` reads the profile Keychain (`security find-generic-password -s gemini -a antigravity -w <kc>`) or fallback OAuth token files, decodes `go-keyring-base64:`, and extracts `access_token`, `email` (`id_token_email`), `auth_method`, and `expiry`.
3. `fetch_antigravity_google_license(profile, access_token=None)` calls `GET https://aicode.googleapis.com/v1alpha:fetchLicenses` with `Authorization: Bearer <access_token>` (`timeout=4.0`) and returns `{"userTier": ..., "tierDisplayName": ..., "upgradeText": ..., "upgradeUrl": ...}`.
4. `_query_agy_credits(env, cwd)` calls `[AGY_BIN, "--output-format", "json", "-p", "/credits"]` only when `/credits` is supported, returning `{"remainingCredits": int, "upgradeUrl": str}` (and ignoring unexpected command errors in unit tests that mock `subprocess.run`).
5. `_derive_profile_capabilities` and `normalize_antigravity_account` incorporate `license_info`, `oauth_info`, and `credits_info` so `g1-ultra-tier` / `Google AI Ultra` resolves to `tier="ULTRA"`, `priority=80`, `g1-pro-tier` resolves to `tier="PRO"`, `priority=60|50`, and `free-tier` resolves to `tier="FREE"`, `priority=20`.

- [ ] **Step 4: Run pytest to verify all unit tests pass**

Run: `pytest tests/test_check_quota_dynamic_provider_tiers.py tests/test_cqra_quota_discovery.py -v`
Expected: PASS.

---

### Task 2: Dashboard UI Info Modal & Live Profile Cache Refresh

**Files:**
- Modify: `skills/check-quota/resources/dashboard/quota_dashboard.html:8765-8798`
- Test: `tests/test_check_quota_dynamic_provider_tiers.py`

**Interfaces:**
- Consumes: `data.accountMeta.tierDisplayName`, `data.accountMeta.userTier`, `data.accountMeta.remainingCredits`, `data.accountMeta.creditsSummary`, `data.priority`
- Produces: Rich dynamic Google plan summary in `#infoModalTier` inside `openProfileInfoModal(profile)`

- [ ] **Step 1: Update `openProfileInfoModal` in `quota_dashboard.html`**

In `skills/check-quota/resources/dashboard/quota_dashboard.html` around lines 8766-8773, enrich the Antigravity profile branch of `openProfileInfoModal(profile)` so `#infoModalTier` displays:
- `displayTier` (`ULTRA`, `PRO`, `FREE`)
- `meta.tierDisplayName` and `meta.userTier` when present (e.g., `ULTRA • Google AI Ultra (g1-ultra-tier) • Priority 80`)
- `argonSuffix` and `meta.creditsSummary` when present.

- [ ] **Step 2: Refresh live Antigravity profiles and verify full test suite**

Run a refresh across configured profiles so `PROFILES_DATA` in `quota_dashboard.html` reflects live Google license tiers (`tess` -> `ULTRA`, real Google emails from Keychain / `state.vscdb`), then run:
Run: `pytest tests/test_check_quota_dynamic_provider_tiers.py tests/test_cqra_quota_discovery.py tests/test_cqra_quota_ui.py tests/test_agy_quota.py -v`
Expected: PASS with zero errors.

- [ ] **Step 3: Commit changes**

```bash
git add docs/superpowers/plans/2026-11-24-dynamic-google-profile-data.md scripts/agy_quota.py skills/check-quota/resources/dashboard/quota_dashboard.html tests/test_check_quota_dynamic_provider_tiers.py
git commit -m "[CHECK_QUOTA] Fetch dynamic Google tier, email, and license metadata for Antigravity profiles" -m "- query aicode.googleapis.com/v1alpha:fetchLicenses for live g1-ultra-tier/g1-pro-tier/free-tier" -m "- decode Keychain go-keyring-base64 OAuth id_token_email and dual-path state.vscdb email" -m "- enrich normalize_antigravity_account and profileInfoModal with live Google plan metadata"
```
