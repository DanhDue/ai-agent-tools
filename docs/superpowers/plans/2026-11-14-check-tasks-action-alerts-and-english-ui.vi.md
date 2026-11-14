# Kế hoạch Triển khai Cảnh báo Xác nhận & Giao diện Tiếng Anh cho Check-Tasks

> **Dành cho agent thực thi:** BẮT BUỘC SỬ DỤNG KỸ NĂNG `d3nexus:subagent-driven-development` để thực thi kế hoạch này theo từng tác vụ. Dùng hộp kiểm (`- [ ]`) để theo dõi tiến độ.

- **Ngày**: 2026-11-14
- **PIC**: phungthuy8901
- **Tài liệu Thiết kế**: [2026-11-14-check-tasks-action-alerts-and-english-ui-design.vi.md](../specs/2026-11-14-check-tasks-action-alerts-and-english-ui-design.vi.md)
- **Phạm vi**: `skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `tests/test_ltsp_harvester_pipeline.py`, `tests/test_ltsp_dashboard_ui.py`, `tests/test_lifecycle_telemetry_and_stage_progress.py`

## Mục lục

- [1. Ràng buộc Toàn cục](#1-ràng-buộc-toàn-cục)
- [2. Bản đồ Kiến trúc & Tệp tin](#2-bản-đồ-kiến-trúc--tệp-tin)
- [3. Task 1: Ưu tiên Active Epic & Tổng hợp Action Blockers Đa Epic ở Backend](#3-task-1-ưu-tiên-active-epic--tổng-hợp-action-blockers-đa-epic-ở-backend)
- [4. Task 2: Thống nhất Cảnh báo Frontend, Chữ ký Cache & Chuẩn hóa Giao diện Tiếng Anh](#4-task-2-thống-nhất-cảnh-báo-frontend-chữ-ký-cache--chuẩn-hóa-giao-diện-tiếng-anh)
- [5. Task 3: Kiểm thử Trình duyệt Trực tiếp & Cổng Chất lượng Đầy đủ](#5-task-3-kiểm-thử-trình-duyệt-trực-tiếp--cổng-chất-lượng-đầy-đủ)
- [6. Bàn giao Thực thi](#6-bàn-giao-thực-thi)

---

## 1. Ràng buộc Toàn cục

1. **Mở rộng Schema Tương thích Ngược**: `ai-agent-tools` không có thư mục `shared-contracts/`. Mọi trường bổ sung trên `RepoMetadata` (`action_blockers: list[dict[str, str]]`) và từng epic (`active_stage: str`) chỉ thêm mới với giá trị mặc định để bảo toàn tương thích ngược với API/CLI và kiểm thử hiện hữu.
2. **Giữ Tương thích Dò Từ khóa State Cũ**: Khi chuẩn hóa nhãn giao diện `tasks_dashboard.html` sang tiếng Anh, **không xóa** danh sách từ khóa tiếng Việt bên trong `hasPromptActionWords` (`Phê duyệt`, `Lựa chọn`, `Chờ Bạn Chọn`), `isWaitingFinish` (`Chờ /finish`), `normalizeEpicStatus` (`hoàn thành`, `hủy`), hay bộ kiểm thông báo `updateMetrics` (`L4105`); đồng thời giữ nguyên chuỗi `prompt` / `("triage", "Lập bảng triage")` trong `check_tasks.py` để không phá vỡ `test_check_tasks_fsm.py` và `test_rsdh_tasks_dashboard_ui.py`.
3. **Tuyệt đối Chỉ Đọc với Repo Ngoài**: Không chỉnh sửa các tệp `.devtool/` bên trong các repository khác như `lyrics-sync`. Mọi bài kiểm thử phải dùng fixture tạm hoặc server giả lập.
4. **Kỷ luật Vai trò & Git**: Cấm `--no-verify` hoặc `git push`. Tuân thủ định dạng commit `[CHECK_TASKS_ALERTS] <tiêu đề ngắn>` và tuyệt đối không thêm dòng trailer (`Co-Authored-By:`, v.v.).
5. **Không Tải lại Trang & Polling Sạch**: Mọi cập nhật cảnh báo trên cả 4 vị trí UI phải render mượt qua `renderRepoTabs`, `renderKanbanDashboard`, `renderEpicsOverviewAndApprovalGate` và `renderExecutionEpics` trong chu kỳ polling 5 giây mà không tải lại trang và không phát sinh lỗi console.

---

## 2. Bản đồ Kiến trúc & Tệp tin

| Thành phần | Tệp đích | Trách nhiệm |
|---|---|---|
| Harvester Backend | `skills/check-tasks/resources/scripts/check_tasks.py` | Sửa thứ tự ưu tiên `resolve_active_epic()`; thêm `RepoMetadata.action_blockers`; tính `active_stage` cho từng epic và tổng hợp blockers đa epic trong `_scan_repo_impl()`. |
| Giao diện Dashboard | `skills/check-tasks/resources/dashboard/tasks_dashboard.html` | Thêm `collectRepoActionBlockers(repo)`; đồng bộ cảnh báo ở tab Repo (`⚠️ <N> Confirm` pill + chấm đỏ), thẻ `Approval Blockers`, sidebar `EPICS PROGRESS` và banner thẻ Execution; cập nhật `tabsSig` + `buildOverviewSig`; chuyển toàn bộ ~160 chuỗi giao diện tiếng Việt sang tiếng Anh. |
| Kiểm thử Harvester | `tests/test_ltsp_harvester_pipeline.py` | Bổ sung TDD test tái hiện backlog worktree cũ che khuất `pending_decision.json` và tổng hợp blocker ở epic phụ. |
| Kiểm thử UI Dashboard | `tests/test_ltsp_dashboard_ui.py` | Cập nhật assertion `Hoàn thành` -> `Completed` (`L173`, `L252`) và thêm test Chrome CDP kiểm chứng đủ 4 vị trí cảnh báo, chuyển trạng thái clear và giao diện tiếng Anh. |
| Kiểm thử Telemetry CDP | `tests/test_lifecycle_telemetry_and_stage_progress.py` | Cập nhật assertion `Hoàn thành` -> `Completed` (`L315`, `L325`, `L361`, `L671`, `L672`) sau khi tiếng Anh hóa dòng `Task Progress` trong `renderExecutionEpics()`. |

---

## 3. Task 1: Ưu tiên Active Epic & Tổng hợp Action Blockers Đa Epic ở Backend

**Tệp liên quan:**
- Sửa: `skills/check-tasks/resources/scripts/check_tasks.py`
- Kiểm thử: `tests/test_ltsp_harvester_pipeline.py`

### Các bước thực hiện

- [ ] **Bước 1: Viết kiểm thử thất bại (TDD Red) trong `tests/test_ltsp_harvester_pipeline.py`**

Bổ sung 2 bài kiểm thử tái hiện lỗi gốc và trường hợp biên đa epic:
1. `test_resolve_active_epic_prefers_pending_decision_over_stale_worktree_backlog(tmp_path: Path)`:
   - Tạo repo git tạm có `.worktrees/acr-live/.devtool/features/task_01_old.md` (`epic: mac_mini_to_cloud_roadmap`, `status: todo`), trong khi `.devtool/state/pending_decision.json` đang kích hoạt quyết định cho `alignment_flow_hardening` (`"Resolve Principal Review blocker (FIX_LOOP on task_07_step3_retry_and_repeated_lines.md)"`) kèm HLD và sổ cái Gate 1/2.
   - Xác nhận `scan_repo(tmp_path)` chọn `active_epic == "alignment_flow_hardening"`, `is_human_action_required is True`, và `action_blockers` chứa `alignment_flow_hardening` với đúng lý do và `stage` (không chọn `mac_mini_to_cloud_roadmap`).
2. `test_scan_repo_aggregates_secondary_epic_action_blockers_and_stages(tmp_path: Path)`:
   - Tạo repo 2 epic: `primary_auto_epic` chạy tự động trong worktree (`.worktrees/primary_auto_epic`, `Stage 3`, `is_human_action_required == False`) còn `blocked_secondary_epic` (`in_progress`) đang chờ xác nhận trong `pending_decision.json` (`decisions["blocked_secondary_epic"]` với lý do `"Confirm Gate 3 task ordering"`).
   - Kèm thêm 1 epic `done` cũ để chứng minh epic đã hoàn thành không lọt vào `action_blockers`.
   - Xác nhận `repo.is_human_action_required is False` (bảo toàn cách ly quyết định theo `active_epic` của `RSDH-AR-03`), `repo.action_blockers == [{"epic": "blocked_secondary_epic", "stage": ..., "reason": "Confirm Gate 3 task ordering"}]`, và epic `blocked_secondary_epic` mang `active_stage`, `is_action_required is True`, `action_prompt == "Confirm Gate 3 task ordering"`.

- [ ] **Bước 2: Chạy pytest mục tiêu xác nhận FAIL**

Chạy:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py -k "prefers_pending_decision or aggregates_secondary_epic" -v
```
Kỳ vọng: FAIL (`mac_mini_to_cloud_roadmap` bị chọn nhầm hoặc thiếu `action_blockers`).

- [ ] **Bước 3: Hiện thực thay đổi backend trong `skills/check-tasks/resources/scripts/check_tasks.py`**

1. Trong `RepoMetadata` (`L263-287`): thêm `action_blockers: list[dict[str, str]] = field(default_factory=list)`.
2. Trong `resolve_active_epic()` (`L877-1055`):
   - Giữ ưu tiên hàng đầu cho nhánh worktree (`epic/` hoặc `feat/`), tệp dirty `.devtool/epic/<slug>`, và tên thư mục worktree khớp `_strip_slot_suffix(d.name)`.
   - Khi quét `wt_feat = d / ".devtool" / "features"`: chỉ trả về ngay nếu `t.epic` chuẩn hóa khớp `_strip_slot_suffix(d.name)` HOẶC `t.status == "in_progress"`; ngược lại giữ làm `unrelated_wt_feature_fallback` để Bước 3, 4, Bước 5.5 (`pending_decision.json`) và Bước 7 (`stage12_candidates`: `gate >= 1`, `heartbeat`, epic `in_progress`) được đánh giá trước khi fallback về tên thư mục worktree chưa xác thực ở Bước 5 hay backlog cũ.
3. Trong `_scan_repo_impl()` (`L3230-3323`):
   - Gán `ep["active_stage"]` cho mọi epic trong `epics_summary["epics"]` (`decision.stage.value` với active epic, `ep_decision.stage.value` với non-done epic).
   - Loại trừ `status == "done"` khỏi blocker; bảo đảm mọi epic non-done đang cần xác nhận đều có `is_action_required = True` và `action_prompt` không rỗng (`ep_prompt or ep.get("action_prompt") or ep_decision.prompt`).
   - Tổng hợp `action_blockers` không trùng lặp theo slug chuẩn hóa (gồm cả `active_epic` và các epic phụ đang bị chặn).
   - Giữ `is_human_action_required=decision.is_human_action_required` và `prompt=decision.prompt` giới hạn theo `active_epic` (bảo toàn cách ly `RSDH-AR-03`), đồng thời truyền `action_blockers=action_blockers` vào `RepoMetadata(...)` để `collectRepoActionBlockers(repo)` tổng hợp toàn bộ epic bị chặn.

- [ ] **Bước 4: Chạy lại bộ test harvester & FSM xác nhận PASS**

Chạy:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py tests/test_check_tasks_harvester.py tests/test_check_tasks_fsm.py -q
```
Kỳ vọng: Toàn bộ PASS.

- [ ] **Bước 5: Commit Task 1**

```bash
git add skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py
git commit -m "[CHECK_TASKS_ALERTS] Fix active epic priority and multi-epic blocker aggregation"
```

---

## 4. Task 2: Thống nhất Cảnh báo Frontend, Chữ ký Cache & Chuẩn hóa Giao diện Tiếng Anh

**Tệp liên quan:**
- Sửa: `skills/check-tasks/resources/dashboard/tasks_dashboard.html`
- Cập nhật / Kiểm thử: `tests/test_ltsp_dashboard_ui.py`, `tests/test_lifecycle_telemetry_and_stage_progress.py`

### Danh mục Việt -> Anh & Đồng bộ 4 Vị trí Cảnh báo

Bảo toàn nhận diện từ khóa tiếng Việt cũ trong `hasPromptActionWords`, `isWaitingFinish`, `normalizeEpicStatus` và kiểm tra thông báo `updateMetrics` (`L4105`); đồng thời chuyển toàn bộ nhãn hiển thị, tiêu đề, banner, nút, tooltip, hộp thoại modal, bình luận mẫu và toast trong `tasks_dashboard.html` sang tiếng Anh:

1. **Thanh trên & trạng thái tải (`L863-897`)**: `Detected Repositories`, `Running Active Epics`, `Completed Kanban Tasks`, `Active Worktrees`, `5 Isolated`, `Refresh`, `Loading repository and worktree data from server...`, `Open Antigravity Quota Dashboard (Dialog)`.
2. **Hộp thoại Modal & Toast (`L908-1785`, `L3854-4070`)**: `Project Epics List (From Root Repo)`, `Kanban Tasks Board (Modal Dialog)`, `Two-Tier Memory: PROJECT_LEDGER vs Assistant State`, `Principal Review Results`, `Review Results`, `6-Column Triage Table`, `Evidence / Raw Output`, `Notification`, `+ Assign PIC...`, các thông báo clipboard/PIC/launch bằng tiếng Anh.
3. **Top Repo Selector Tab (`L2013-2045`)**: Dùng `collectRepoActionBlockers(r)` để bật `needsConfirm`, thêm danh sách blocker vào `tabsSig`, giữ `.tab-notification-badge` với tooltip `"Confirmation / approval required"` và thêm thẻ pill `.tab-badge-confirm` (`⚠️ ${blockers.length} Confirm`) ngay trong `.tab-badges`.
4. **Thẻ Thực thi & Telemetry (`L2316-2720`)**: Dùng `collectRepoActionBlockers(repo)` + `epicMeta.active_stage` + `epicMeta.action_prompt` (thay thế hoàn toàn `'Đang xử lý theo worktree...'` và `'Stage 3'` gán cứng); đổi `'Lập bảng triage'` -> `'Create Triage Table'`, `'Chờ /finish'` -> `'Waiting /finish'`, `'Nhật ký thực thi'` -> `'Execution Logs'`, `'Bước tiếp theo con người cần quyết định:'` -> `'Human Decision Required:'`, `'Task hiện tại:'` -> `'Current Task:'`, `'Tiến độ Tasks: X / Y Hoàn thành'` -> `'Task Progress: X / Y Completed'`, `'Mở IDE'` -> `'Open IDE'`.
5. **Sidebar `EPICS PROGRESS` & Bảng Kanban (`L2846-3060`)**: `EPICS PROGRESS`, `Filter by Epic:`, `All Epics`, tooltip `"Epic requires user confirmation / approval"`, giữ viền `#ef4444` + chấm nhấp nháy.
6. **Khối Tổng quan & Điểm Nghẽn Phê duyệt (`L3089-3593`, `L4119-4184`)**: Cập nhật `buildOverviewSig` chứa chữ ký blockers; dùng `collectRepoActionBlockers(repo)` trong `renderEpicsOverviewAndApprovalGate` để chuyển thẻ `Approval Blockers` sang trạng thái đỏ `Action Required` / `Confirmation Required` liệt kê từng epic bị chặn và lý do (hoặc `Passed` / `✓ Clear` / `No blocking gates` khi thông suốt); chuẩn hóa toàn bộ tiêu đề Mục I (`I. Project Overview & Roadmap`, `Epics Overview`, `Epics Roadmap (from .devtool/epic/)`, `Strategic Notes (Human Architect)`) và Mục II (`II. Worktree & Profile Execution (PIC)`).

### Các bước thực hiện

- [ ] **Bước 1: Cập nhật assertion `"Hoàn thành"` -> `"Completed"` & viết test Chrome CDP `test_four_location_confirmation_alerts_and_english_ui()`**

1. Đổi `"Hoàn thành"` -> `"Completed"` trong:
   - `tests/test_ltsp_dashboard_ui.py` (`L173`, `L252`)
   - `tests/test_lifecycle_telemetry_and_stage_progress.py` (`L315`, `L325`, `L361`, `L671`, `L672`)
2. Bổ sung `test_four_location_confirmation_alerts_and_english_ui()` trong `tests/test_ltsp_dashboard_ui.py`:
   - Chạy `TasksServer` với dữ liệu giả lập `lyrics-sync` có epic chính chạy tự động và epic phụ `alignment_flow_hardening` bị chặn chờ xác nhận.
   - Mở trang qua Chrome CDP và kiểm tra đồng thời cả **4 vị trí cảnh báo**: (1) banner thẻ Execution hiển thị đúng `reason` + `active_stage`, (2) mục trong `EPICS PROGRESS` có viền đỏ + chấm nhấp nháy, (3) tab `lyrics-sync` có chấm đỏ + pill `.tab-badge-confirm`, (4) thẻ `Approval Blockers` hiển thị `Action Required` / `Confirmation Required` cùng danh sách `alignment_flow_hardening`.
   - Kiểm tra tiêu đề tiếng Anh sạch, không sót tiêu đề tiếng Việt (`Điểm Nghẽn`, `Thông Suốt`, `TIẾN ĐỘ EPICS`, `Đang xử lý theo worktree`), sau đó xóa blocker và chạy `pollDashboard()` để xác nhận chuyển mượt về `✓ Clear` / `No blocking gates` với 0 lỗi console.

- [ ] **Bước 2: Chạy test UI mục tiêu xác nhận FAIL**

Chạy:
```bash
python3 -m pytest tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py -k "four_location or ltsp_hp_05 or ltsp_hp_06" -v
```
Kỳ vọng: FAIL trước khi sửa `tasks_dashboard.html`.

- [ ] **Bước 3: Hiện thực thay đổi trong `skills/check-tasks/resources/dashboard/tasks_dashboard.html`**

Thực hiện đủ 6 hạng mục trong danh mục trên: CSS `.tab-badge-confirm`, hàm `collectRepoActionBlockers(repo)`, cập nhật `renderRepoTabs`, `renderExecutionEpics`, `buildOverviewSig`, `renderEpicsOverviewAndApprovalGate` và thay toàn bộ nhãn hiển thị tiếng Việt sang tiếng Anh.

- [ ] **Bước 4: Chạy toàn bộ bộ test Harvester & UI Regression xác nhận PASS**

Chạy:
```bash
python3 -m pytest tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py tests/test_rsdh_tasks_dashboard_ui.py tests/test_rsdh_quota_modal_stack.py -q
```
Kỳ vọng: Toàn bộ PASS, 0 skipped.

- [ ] **Bước 5: Quét kiểm tra không còn chuỗi UI tiếng Việt rò rỉ trong `tasks_dashboard.html`**

Chạy script Python kiểm tra regex ký tự tiếng Việt trong `tasks_dashboard.html`, bảo đảm chỉ còn các danh sách từ khóa khớp tương thích ngược (`hasPromptActionWords`, `isWaitingFinish`, `normalizeEpicStatus`, kiểm tra `prompt` ở `updateMetrics`).

- [ ] **Bước 6: Commit Task 2**

```bash
git add skills/check-tasks/resources/dashboard/tasks_dashboard.html tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
git commit -m "[CHECK_TASKS_ALERTS] Unify 4-location confirmation alerts and English dashboard UI"
```

---

## 5. Task 3: Kiểm thử Trình duyệt Trực tiếp & Cổng Chất lượng Đầy đủ

**Tệp liên quan:** không chỉnh sửa mã nguồn (chỉ kiểm chứng)

- [ ] **Bước 1: Chạy `TasksServer` từ worktree ở cổng `8776` & kiểm tra bằng `browser` subagent**

1. Khởi chạy `python3 skills/check-tasks/resources/scripts/tasks_server.py --root /Users/danhdueexoictif/AllProjects --port 8776` để render trạng thái thực tế của `lyrics-sync` (`alignment_flow_hardening`).
2. Giao `browser` subagent mở `http://127.0.0.1:8776`, chọn tab `lyrics-sync`, kiểm chứng đủ 4 vị trí cảnh báo xác nhận + toàn bộ tiêu đề tiếng Anh + 0 lỗi console, sau đó tắt server tạm cổng `8776` ngay lập tức.

- [ ] **Bước 2: Chạy đầy đủ các cổng chất lượng trước khi bàn giao**

```bash
python3 -m ruff format --check skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
python3 -m ruff check skills/check-tasks/resources/scripts/check_tasks.py tests/test_ltsp_harvester_pipeline.py tests/test_ltsp_dashboard_ui.py tests/test_lifecycle_telemetry_and_stage_progress.py
python3 -m mypy skills/check-tasks/resources/scripts/check_tasks.py
bash scripts/verify.sh --full
```
Kỳ vọng: Mọi lệnh trả về mã thoát `0`.

---

## 6. Bàn giao Thực thi

Kế hoạch đã hoàn tất và lưu tại `docs/superpowers/plans/2026-11-14-check-tasks-action-alerts-and-english-ui.en.md` và `.vi.md`.

Thực thi thông qua `d3nexus:subagent-driven-development`:
- Khởi tạo workspace SDD cô lập bằng `scripts/sdd-workspace init`.
- Triển khai tuần tự qua subagent (`self`) cho từng tác vụ trong worktree hiện tại.
- Chạy review gói diff (`scripts/review-package`), kiểm chứng trình duyệt thực tế với `browser` subagent, review toàn nhánh cuối cùng, chạy `scripts/verify.sh --full`, và kết thúc qua `d3nexus:finishing-a-development-branch` để Human Architect chọn phương thức gộp nhánh ở Gate 5.
