# Check-Tasks Action Alerts & English UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `d3nexus:subagent-driven-development` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

- **Date**: 2026-11-14
- **PIC**: phungthuy8901
- **Design Spec**: [2026-11-14-check-tasks-action-alerts-and-english-ui-design.en.md](../specs/2026-11-14-check-tasks-action-alerts-and-english-ui-design.en.md)
- **Scope**: `skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `tests/test_ltsp_harvester_pipeline.py`, `tests/test_ltsp_dashboard_ui.py`, `tests/test_lifecycle_telemetry_and_stage_progress.py`

## Table of Contents

- [1. Global Constraints](#1-global-constraints)
- [2. Architecture & File Map](#2-architecture--file-map)
- [3. Task 1: Backend Active Epic Priority & Multi-Epic Action Blockers](#3-task-1-backend-active-epic-priority--multi-epic-action-blockers)
- [4. Task 2: Frontend Unified Action Alerts, Cache Signatures & English UI Localization](#4-task-2-frontend-unified-action-alerts-cache-signatures--english-ui-localization)
- [5. Task 3: Live Web Browser Verification & Full Quality Gate](#5-task-3-live-web-browser-verification--full-quality-gate)
- [6. Execution Handoff](#6-execution-handoff)

---

## 1. Global Constraints

1. **Additive Backward-Compatible Schema**: `ai-agent-tools` contains no `shared-contracts/` directory. Additions to `RepoMetadata` (`action_blockers: list[dict[str, str]]`) and per-epic metadata (`active_stage: str`) must be purely additive with defaults so existing API/CLI consumers and tests remain valid.
2. **Preserve Legacy State Keyword Matching**: When standardizing `tasks_dashboard.html` UI labels to English, **do not remove** Vietnamese keyword matching inside `hasPromptActionWords` (`Phê duyệt`, `Lựa chọn`, `Chờ Bạn Chọn`), `isWaitingFinish` (`Chờ /finish`), `normalizeEpicStatus` (`hoàn thành`, `hủy`), or alert polling check (`L4105`), and keep `check_tasks.py` prompt strings / `("triage", "Lập bảng triage")` untouched so `test_check_tasks_fsm.py` and `test_rsdh_tasks_dashboard_ui.py` remain backward-compatible with persisted fixtures.
3. **External Repos Strictly Read-Only**: Never edit `.devtool/` files inside external repositories such as `lyrics-sync`. All tests must use temporary fixtures or synthetic servers.
4. **Role & Git Hygiene**: Never use `--no-verify` or `git push`. Follow commit format `[CHECK_TASKS_ALERTS] <imperative title>` with zero trailer lines (`Co-Authored-By:` etc.).
5. **No Page Reloads & Clean Polling**: All confirmation alert updates across the 4 UI locations must re-render cleanly via `renderRepoTabs`, `renderKanbanDashboard`, `renderEpicsOverviewAndApprovalGate`, and `renderExecutionEpics` during 5-second polling without full page reload and with zero console errors.

---

## 2. Architecture & File Map

| Component | Target File | Responsibility |
|---|---|---|
| Backend Harvester | `skills/check-tasks/resources/scripts/check_tasks.py` | Fix `resolve_active_epic()` worktree-feature priority; add `RepoMetadata.action_blockers`; derive per-epic `active_stage` and multi-epic blocker aggregation in `_scan_repo_impl()`. |
| Dashboard Frontend | `skills/check-tasks/resources/dashboard/tasks_dashboard.html` | Add `collectRepoActionBlockers(repo)`; unify confirmation detection across Repo tabs (`⚠️ <N> Confirm` pill + red dot), Overview Blockers card (`Action Required` / `Confirmation Required`), Kanban sidebar (`EPICS PROGRESS`), and Execution card banner; update `tabsSig` + `buildOverviewSig`; standardize all ~160 Vietnamese UI strings to English. |
| Harvester Unit Tests | `tests/test_ltsp_harvester_pipeline.py` | TDD tests reproducing stale worktree `unstarted` backlog masking `pending_decision.json` and multi-epic secondary blockers. |
| Dashboard UI Tests | `tests/test_ltsp_dashboard_ui.py` | Update `Hoàn thành` -> `Completed` assertions (`L173`, `L252`) and add headless Chrome CDP test covering all 4 alert locations, clearing transitions, and English UI verification. |
| Lifecycle CDP Tests | `tests/test_lifecycle_telemetry_and_stage_progress.py` | Update `Hoàn thành` -> `Completed` assertions (`L315`, `L325`, `L361`, `L671`, `L672`) after localization of `Progress` line in `renderExecutionEpics()`. |

---

## 3. Task 1: Backend Active Epic Priority & Multi-Epic Action Blockers

**Files:**
- Modify: `skills/check-tasks/resources/scripts/check_tasks.py`
- Test: `tests/test_ltsp_harvester_pipeline.py`

### Steps

- [ ] **Step 1: Write failing unit & edge-case tests in `tests/test_ltsp_harvester_pipeline.py`**

Add two TDD tests covering the root causes and multi-epic edge cases:
1. `test_resolve_active_epic_prefers_pending_decision_over_stale_worktree_backlog(tmp_path: Path)`:
   - Create a synthetic git repo with `.worktrees/acr-live/.devtool/features/task_01_old.md` (`epic: mac_mini_to_cloud_roadmap`, `status: todo`), while `.devtool/state/pending_decision.json` contains an active decision for `alignment_flow_hardening` (`"Resolve Principal Review blocker (FIX_LOOP on task_07_step3_retry_and_repeated_lines.md)"`) with `alignment_flow_hardening` HLD and Gate 1/2 ledger entries.
   - Assert `scan_repo(tmp_path)` resolves `active_epic == "alignment_flow_hardening"`, `is_human_action_required is True`, and `action_blockers` contains `alignment_flow_hardening` with the exact blocker reason and accurate `stage` (not `mac_mini_to_cloud_roadmap`).
2. `test_scan_repo_aggregates_secondary_epic_action_blockers_and_stages(tmp_path: Path)`:
   - Create a two-epic repo where `primary_auto_epic` is in active worktree (`.worktrees/primary_auto_epic`, autonomous `Stage 3`, `is_human_action_required == False`), and sibling `blocked_secondary_epic` (status `in_progress`, Gate 2 in ledger or `pending_decision.json` multi-decision map `decisions["blocked_secondary_epic"]`) requires human confirmation (`"Confirm Gate 3 task ordering"`).
   - Also include a `done` historical epic with a stale flag to prove completed epics are excluded from `action_blockers`.
   - Assert `repo.is_human_action_required is True`, `repo.action_blockers == [{"epic": "blocked_secondary_epic", "stage": ..., "reason": "Confirm Gate 3 task ordering"}]`, `blocked_secondary_epic` in `repo.epics_summary["epics"]` carries non-empty `active_stage`, `is_action_required is True`, `action_prompt == "Confirm Gate 3 task ordering"`, and `repo.prompt` reflects the active blocker rather than `"Idle"` or misleading non-action status.

- [ ] **Step 2: Run targeted pytest to confirm FAIL**

Run:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py -k "prefers_pending_decision or aggregates_secondary_epic" -v
```
Expected: FAIL (`mac_mini_to_cloud_roadmap` selected instead of `alignment_flow_hardening`, `RepoMetadata` missing `action_blockers`).

- [ ] **Step 3: Implement backend changes in `skills/check-tasks/resources/scripts/check_tasks.py`**

1. In `RepoMetadata` (`L263-287`):
   - Add `action_blockers: list[dict[str, str]] = field(default_factory=list)`.
2. In `resolve_active_epic()` (`L877-1055`):
   - Keep Step 1 (`wt.branch` matching `epic/` or `feat/`), Step 2a (dirty `.devtool/epic/<slug>` inside worktree), and Step 2c (`_strip_slot_suffix(d.name)` matching a known epic) ahead of fallback states.
   - In Step 2b (`wt_feat = d / ".devtool" / "features"`): only return immediately if the task's normalized `epic` matches `_strip_slot_suffix(d.name)` OR the task has `status == "in_progress"`. Otherwise store the first `wt_feat` epic in `unrelated_wt_feature_fallback` and let Steps 3 (`assistant_state.md`), 4 (`.devtool/state/*.md`), 5 (`.worktrees/` directory names), 5.5 (`_resolve_active_epic_from_pending_decision`), and 7 (`stage12_candidates`: `gate >= 1`, `heartbeat`, active `in_progress` epics) resolve before falling back to `unrelated_wt_feature_fallback` or Step 6 root `.devtool/features/`.
3. In `_scan_repo_impl()` (`L3230-3323`):
   - Track `ep["active_stage"]` for every epic in `epics_summary["epics"]`:
     - For `active_epic`: set `ep["active_stage"] = decision.stage.value`.
     - For non-primary epics (`else` branch around `L3254`): call `ep_decision = derive_lifecycle_state(repo_path, slug, pending_decision=ep_pd)` when `ep.get("status") != "done"`; set `ep["active_stage"] = ep_decision.stage.value`.
     - For non-done epics, if `ep_pd` has `active: True` or `ep_decision.is_human_action_required` is `True` or `st_lower` flagged confirmation, set `ep["is_action_required"] = True` and ensure `ep["action_prompt"]` falls back cleanly (`ep_prompt or ep.get("action_prompt") or ep_decision.prompt`) whenever empty. Never mark `status == "done"` epics as action-required.
   - Build `action_blockers: list[dict[str, str]] = []` deduplicated by `_normalize_slug(slug)`:
     - Include primary `active_epic` if `decision.is_human_action_required` (reason = `matched_pending.get("reason")` if active else `decision.prompt`, stage = `decision.stage.value`).
     - Append each non-done epic in `epics_summary["epics"]` with `ep.get("is_action_required") is True` and not yet seen (`stage = ep.get("active_stage") or "Stage 1 (Inception)"`, `reason = ep.get("action_prompt") or "Confirmation required"`).
   - Compute `repo_action_required = bool(decision.is_human_action_required or action_blockers)`.
   - Compute `repo_prompt = decision.prompt`: if `not decision.is_human_action_required and action_blockers`, format `first = action_blockers[0]`; `repo_prompt = f"{first['epic']}: {first['reason']}"` so top-level `repo.prompt` is actionable.
   - Pass `is_human_action_required=repo_action_required`, `prompt=repo_prompt`, and `action_blockers=action_blockers` into `RepoMetadata(...)`.

- [ ] **Step 4: Run targeted & harvester test suite to verify PASS**

Run:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py tests/test_check_tasks_harvester.py tests/test_check_tasks_fsm.py -q
```
Expected: All PASS (including both new TDD tests).

- [ ] **Step 5: Commit Task 1**

```bash
git add skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py
git commit -m "[CHECK_TASKS_ALERTS] Fix active epic priority and multi-epic blocker aggregation"
```

---

## 4. Task 2: Frontend Unified Action Alerts, Cache Signatures & English UI Localization

**Files:**
- Modify: `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- Test / Update assertions: `tests/test_ltsp_dashboard_ui.py`, `tests/test_lifecycle_telemetry_and_stage_progress.py`

### Complete UI Translation & Alert Checklist

Preserve backward-compatible keyword matching inside `hasPromptActionWords` (`Approve`, `Phê duyệt`, `Review Choice`, `Lựa chọn`, `Chờ Bạn Chọn`, `Confirm`, `Confirm?`, `Action Required`, `Gate`), `isWaitingFinish` (`Waiting /finish`, `Chờ /finish`), `normalizeEpicStatus` (`hoàn thành`, `hủy`), and `updateMetrics` notification trigger (`L4105`), while standardizing all rendered HTML text, attributes, buttons, banners, modals, comments, and toasts in `tasks_dashboard.html` to English:

| UI Area (approx lines in `tasks_dashboard.html`) | Old Vietnamese Text | Standardized English Text |
|---|---|---|
| CSS / Topbar stats (`L863-897`) | `Repositories Đã Phát Hiện`, `Active Epics Đang Chạy`, `Kanban Tasks Hoàn Thành`, `Worktrees Hoạt Động`, `5 Phân lập`, `Cập nhật`, `Đang tải dữ liệu repository...`, `Mở Antigravity Quota Dashboard` | `Detected Repositories`, `Running Active Epics`, `Completed Kanban Tasks`, `Active Worktrees`, `5 Isolated`, `Refresh`, `Loading repository and worktree data from server...`, `Open Antigravity Quota Dashboard (Dialog)` |
| Modals (`L908-1089`, `L3854-4070`) | `Danh Sách Epics Dự Án (Đọc từ Repo Gốc)`, `Bảng Kanban Tasks`, `Bộ Nhớ Hai Tầng...`, `Tầng 1... (Vĩnh viễn)`, `Bất biến`, `Tầng 2...`, `Kết Quả Principal Review`, `Kết Quả Review`, `Bảng Triage 6 cột`, `Bằng chứng nguyên văn`, `Thông báo`, `Không có dữ liệu...`, `Trạng Thái`, `Tên Epic / Slug`, `Tiêu Đề (HLD)`, `Cập Nhật`, `Chưa có cột mốc`, `Chưa thiết lập`, `Bước tiếp theo`, `Chưa có yêu cầu` | `Project Epics List (From Root Repo)`, `Kanban Tasks Board (Modal Dialog)`, `Two-Tier Memory: PROJECT_LEDGER vs Assistant State`, `Tier 1: PROJECT_LEDGER.md (Permanent)`, `Invariants`, `Tier 2: In-Flight State & Gate Ledger`, `Principal Review Results (Stage 2 HLD/Tasks Triage)`, `Review Results`, `6-Column Triage Table`, `Evidence / Raw Output`, `Notification`, `No data...`, `Status`, `Epic Name / Slug`, `Title (HLD)`, `Updated`, `No milestones yet`, `Not configured`, `Next Step`, `None` |
| Toasts & PIC selector (`L1100-1785`) | `Đã lưu ✓`, `Không có ghi chú...`, `Đã copy`, `Đã xoá ghi chú...`, `Đã đưa ... lên đầu`, `Đã mở IDE/CLI`, `Lỗi khởi chạy`, `Đang kích hoạt...`, `Đang làm mới...`, `+ Gán PIC...`, `Người phụ trách (PIC)...`, `Chưa có PIC...`, `Đang gán PIC...`, `Đã gán PIC...`, `Lỗi gán PIC...`, `Không thể kết nối...`, `Không thể copy tự động` | `Saved ✓`, `No notes to copy`, `Copied`, `Cleared notes for ...`, `Pinned ... to top`, `Launched IDE/CLI`, `Launch failed`, `Launching IDE/CLI...`, `Refreshing Quota Dashboard...`, `+ Assign PIC...`, `Person In Charge (PIC): @... • Click to change`, `Unassigned • Click to assign PIC`, `Assigning PIC @...`, `Assigned PIC @...`, `Failed to assign PIC...`, `Cannot connect to server to assign PIC`, `Failed to copy automatically` (also localize sample `DEFAULT_QUICK_NOTES` placeholders) |
| Repo Tabs (`L2013-2045`) | `.tab-notification-badge` only with Vietnamese tooltip; missing pill on crimson tabs | Trigger `needsConfirm` when `collectRepoActionBlockers(r).length > 0`; include `tabsSig` blocker count/reasons; keep pulsing dot + tooltip `"Confirmation / approval required"` AND add visible `<span class="tab-badge-confirm">⚠️ ${blockerCount} Confirm</span>` badge pill inside `.tab-badges` (matching `.repo-tab-btn` styling). |
| Telemetry & Execution Card (`L2316-2720`) | `Lập bảng triage`, `Chờ /finish`, `Nhật ký thực thi`, `Xem tất cả N logs`, `Thu gọn` (check fold toggle), `Hiện tại không có Epic nào đang triển khai worktree`, `Human Architect có thể lên ý tưởng...`, `Tất cả tasks hoàn thành ✓`, `Đang khởi tạo tasks...`, `Đang thực thi...`, `Đang xử lý theo worktree...`, `Copy đường dẫn worktree`, `Bước tiếp theo con người cần quyết định:`, `Task hiện tại:`, `Bước tiếp theo:`, `Trạng thái: Tạm dừng chờ quyết định`, `Tiến độ Tasks: X / Y Hoàn thành`, `Mở IDE (@pic)`, `Mở Terminal CLI`, `Xem kết quả Principal Review`, `Xem kết quả Cross-Model Review` | `Create Triage Table`, `Waiting /finish`, `Execution Logs`, `View all N logs`, `Collapse`, `No epics currently executing in worktrees`, `Human Architect can draft ideas and create a new epic in Section I above.`, `All tasks completed ✓`, `Setting up tasks...`, `Executing...`, `Active worktree task`, `Copy worktree path`, `Human Decision Required:`, `Current Task:`, `Next Step:`, `Status: Waiting for decision`, `Task Progress: X / Y Completed`, `Open IDE (@pic)`, `Open Terminal CLI`, `View Principal Review results`, `View Cross-Model Review results` |
| Kanban Sidebar & Roadmap (`L2846-3318`) | `⚠️ Chờ /finish`, `Lọc Kanban theo...`, `TIẾN ĐỘ EPICS`, `Lọc theo Epic:`, `Tất cả Epics`, `Cần xác nhận` dot tooltip, `Quá tải...` if any | `⚠️ Waiting /finish`, `Filter Kanban by: ...`, `EPICS PROGRESS`, `Filter by Epic:`, `All Epics`, tooltip `"Epic requires user confirmation / approval"` |
| Overview, Approval Card & Section I/II (`L3203-3593`, `L4119-4184`) | `Kho lưu trữ đang ở trạng thái nghỉ (Idle)`, `Tổng Quan Về Epics`, `Đang thực hiện`, `Chưa làm / Hàng đợi`, `Đã hoàn thành`, `Đã gác lại / Hủy`, `Điểm Nghẽn Cần Phê Duyệt`, `Cần Bạn Xác Nhận`, `✓ Thông Suốt`, `Có gate chờ duyệt`, `Không có gate nghẽn`, `I. Quản Trị Dự Án...`, `Branch gốc:`, `Copy đường dẫn thư mục`, `Xem Epics`, `Xem Contexts`, `Mở IDE`, `📋 Lộ Trình Epics Dự Án...`, `Trạng Thái`, `Cập Nhật`, `📝 Ghi Chú Chiến Lược...`, `Xoá`, `Tự động lưu...`, `Ý tưởng chiến lược...`, `🚀 II. Triển khai thực thi theo Worktrees & Profiles (PIC)`, `Phân lập`, `Đã làm mới trạng thái` | `Repository is Idle`, `Epics Overview`, `In progress`, `Backlog / Queued`, `Completed`, `Paused / Cancelled`, `Approval Blockers`, `Confirmation Required`, `✓ Clear`, `Gate awaiting approval`, `No blocking gates`, `I. Project Overview & Roadmap`, `Root branch:`, `Copy folder path`, `View Epics`, `View Contexts`, `Open IDE`, `📋 Epics Roadmap (from .devtool/epic/)`, `Status`, `Updated`, `📝 Strategic Notes (Human Architect)`, `Clear`, `Auto-saved • Enter continues 1., 2., ... • Tab indents`, `1. Strategic roadmap notes...`, `🚀 II. Worktree & Profile Execution (PIC)`, `Isolated`, `Refreshed status` |

### Steps

- [ ] **Step 1: Update existing hardcoded Vietnamese `"Hoàn thành"` assertions & add Chrome CDP test in `tests/test_ltsp_dashboard_ui.py` and `tests/test_lifecycle_telemetry_and_stage_progress.py`**

1. Update `"Hoàn thành"` -> `"Completed"` in:
   - `tests/test_ltsp_dashboard_ui.py` (`L173`, `L252`)
   - `tests/test_lifecycle_telemetry_and_stage_progress.py` (`L315`, `L325`, `L361`, `L671`, `L672`)
2. Add Chrome CDP integration test `test_four_location_confirmation_alerts_and_english_ui()` in `tests/test_ltsp_dashboard_ui.py`:
   - Start live `TasksServer` with a synthetic repo (`lyrics-sync`, red theme + worktrees, plus a secondary blocked epic `alignment_flow_hardening` while primary is autonomous OR with `action_blockers` populated + `pending_decision.json` multi-epic state).
   - Connect via Chrome CDP, open the dashboard, wait for `/api/tasks`, assert:
     - **Location 1 (Execution card)**: displays exact blocker reason (`Resolve Principal Review blocker...`) instead of `"Đang xử lý theo worktree..."` and real `active_stage` (e.g. `Stage 2 (HLD & Tasks)`, not hardcoded `Stage 3`), under banner `HUMAN DECISION REQUIRED:`.
     - **Location 2 (Kanban Sidebar `EPICS PROGRESS`)**: displays `#ef4444` border + `.tab-notification-badge` on the blocked epic item with English tooltip.
     - **Location 3 (Top Repo Selector Tab)**: `lyrics-sync` tab shows `.tab-notification-badge` AND `.tab-badge-confirm` (`⚠️ 1 Confirm` or `Confirm`).
     - **Location 4 (Overview Approval Blockers card)**: displays `Approval Blockers`, `Action Required`, `Confirmation Required`, and lists `alignment_flow_hardening` and its reason.
     - Key English headers (`Detected Repositories`, `Epics Overview`, `Approval Blockers`, `EPICS PROGRESS`, `Execution Logs`, `Open IDE`, `Refresh`) are rendered and zero leaked Vietnamese UI headers exist (`Điểm Nghẽn`, `Thông Suốt`, `TIẾN ĐỘ EPICS`, `Đang xử lý theo worktree`, `Bước tiếp theo con người`).
   - Mutate mock server payload to clear the blocker, invoke `pollDashboard()`, assert in-place update without page reload transitions all 4 locations cleanly back to `✓ Clear` / `No blocking gates` and removes `.tab-badge-confirm`, with `0` browser console/page errors.

- [ ] **Step 2: Run targeted UI tests to confirm FAIL**

Run:
```bash
python3 -m pytest tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py -k "four_location or ltsp_hp_05 or ltsp_hp_06" -v
```
Expected: FAIL (missing `.tab-badge-confirm`, `Approval Blockers` still shows `Thông Suốt` when secondary blocked or renders Vietnamese strings).

- [ ] **Step 3: Implement `collectRepoActionBlockers`, 4-location alert unification, signatures & English localization in `skills/check-tasks/resources/dashboard/tasks_dashboard.html`**

1. Add clean CSS rules for `.tab-badge-confirm` (matching `.tab-badge-doing` pill proportions with crisp crimson-amber warning contrast usable on active crimson tabs like `lyrics-sync` without clashing with dark red background).
2. Implement `collectRepoActionBlockers(repo)` right before `renderRepoTabs()`:
   - Normalize and aggregate blockers from `repo.action_blockers`, `repo.pending_decision?.decisions`, legacy `repo.pending_decision`, `repo.epics_summary?.epics` (`status !== 'done' && is_action_required === true`), and `repo.is_human_action_required === true`.
   - Deduplicate by normalized epic slug (`slugsMatch`) keeping non-empty `stage` and `reason`.
3. Update `renderRepoTabs()`:
   - Compute `const blockers = r ? collectRepoActionBlockers(r) : []; const needsConfirm = blockers.length > 0;`.
   - Include `blockers.map(b => `${b.epic}:${b.reason}`).join(',')` in `tabsSig`.
   - Render `.tab-badge-confirm` pill (`⚠️ ${blockers.length || 1} Confirm`) inside `.tab-badges` alongside `.tab-notification-badge` when `needsConfirm === true`.
4. Update `renderExecutionEpics()`:
   - Derive `epicBlockers = collectRepoActionBlockers(repo)` and find matching blocker via `slugsMatch(b.epic, epicSlug)`.
   - Use `epicMeta?.active_stage || (isPrimaryActive ? repo.active_stage : '') || (epicMeta?.status === 'in_progress' ? 'Stage 3 (Implementation)' : 'Stage 1 (Inception)')` for `stageName`.
   - Use `(matchingBlocker && matchingBlocker.reason) || (epicMeta && epicMeta.action_prompt) || (isPrimaryActive ? (decisionReason || repo.prompt || 'Executing...') : 'Active worktree execution')` for `promptText` — never `'Đang xử lý theo worktree...'`.
5. Update `buildOverviewSig(repo)` & `renderEpicsOverviewAndApprovalGate(repo)`:
   - Include `collectRepoActionBlockers(repo).map(b => `${b.epic}|${b.stage}|${b.reason}`).join(';')` inside `buildOverviewSig`.
   - Use `const blockers = collectRepoActionBlockers(repo); const needsConfirm = blockers.length > 0;` inside `renderEpicsOverviewAndApprovalGate`.
   - When `needsConfirm`, style Approval Blockers card with crimson alert highlight, `Action Required` / `Confirmation Required`, and render a concise list of blocked epic slugs + reasons (or `repo.prompt || 'Gate awaiting approval'` fallback). When clean, show `Passed` / `✓ Clear` / `No blocking gates`.
6. Replace all remaining Vietnamese UI labels, buttons, tooltips, modals, headers, comments, and toast notifications per the translation checklist above while leaving `hasPromptActionWords`, `isWaitingFinish`, `normalizeEpicStatus`, and `L4105` multi-lingual matchers intact.

- [ ] **Step 4: Run dashboard, harvester & existing UI regression test suites**

Run:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py tests/test_rsdh_tasks_dashboard_ui.py tests/test_rsdh_quota_modal_stack.py -q
```
Expected: All PASS, 0 skipped/relaxed assertions.

- [ ] **Step 5: Verify zero stray Vietnamese UI strings in `tasks_dashboard.html`**

Run a quick Python check scanning `skills/check-tasks/resources/dashboard/tasks_dashboard.html` for Vietnamese characters, confirming only intentional multi-lingual input-keyword arrays (`hasPromptActionWords`, `isWaitingFinish`, `normalizeEpicStatus`, `updateMetrics` prompt check) remain.

- [ ] **Step 6: Commit Task 2**

```bash
git add skills/check-tasks/resources/dashboard/tasks_dashboard.html tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
git commit -m "[CHECK_TASKS_ALERTS] Unify 4-location confirmation alerts and English dashboard UI"
```

---

## 5. Task 3: Live Web Browser Verification & Full Quality Gate

**Files:** none modified (verification only)

- [ ] **Step 1: Start isolated worktree `TasksServer` on port `8776` & verify in live browser**

1. Launch `python3 skills/check-tasks/resources/scripts/tasks_server.py --root /Users/danhdueexoictif/AllProjects --port 8776` in background (pointing at `/Users/danhdueexoictif/AllProjects` so live `lyrics-sync` `alignment_flow_hardening` blocker renders).
2. Dispatch `browser` subagent to open `http://127.0.0.1:8776`, click `lyrics-sync` tab, verify visually and in DOM:
   - Top `lyrics-sync` tab displays crimson notification dot + `Confirm` pill
   - `Approval Blockers` card displays `Action Required` / `Confirmation Required` listing `alignment_flow_hardening` and its blocker reason
   - `EPICS PROGRESS` sidebar highlights `alignment_flow_hardening` with red dot and border
   - Execution card displays `HUMAN DECISION REQUIRED:` with exact blocker reason (`Resolve Principal Review blocker...`) and English headers (`Epics Overview`, `Approval Blockers`, `Execution Logs`, `Current Task:`, `Task Progress:`, `Open IDE`, `Refresh`) with 0 console errors.
3. Stop the temporary port-8776 server immediately after `browser` subagent confirms completion.

- [ ] **Step 2: Run full quality & verification checks**

```bash
python3 -m ruff format --check skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
python3 -m ruff check skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
python3 -m mypy skills/check-tasks/resources/scripts/check_tasks.py
bash scripts/verify.sh --full
```
Expected: Exit code 0 on all commands.

---

## 6. Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-11-14-check-tasks-action-alerts-and-english-ui.en.md` and `.vi.md`.

Execute via `d3nexus:subagent-driven-development`:
- Set up isolated SDD workspace via `scripts/sdd-workspace init`.
- Dispatch fresh implementation subagents (`self`) per task in this branch worktree.
- Run per-task review packages (`scripts/review-package`), live `browser` subagent verification against `TasksServer` on port `8776`, final whole-branch review, `scripts/verify.sh --full`, and `d3nexus:finishing-a-development-branch` for Gate 5 merge strategy.
