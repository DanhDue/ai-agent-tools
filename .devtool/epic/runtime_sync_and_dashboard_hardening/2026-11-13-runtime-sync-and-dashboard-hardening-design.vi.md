# Thiết kế Đồng bộ Trạng thái Runtime, Hybrid Heartbeat và Gia cố Dashboard

- **Ngày**: 2026-11-13
- **Trạng thái**: Đã phê duyệt (Gate 1)
- **Thư mục Epic**: `runtime_sync_and_dashboard_hardening`
- **Epic Slug**: `runtime-sync-and-dashboard-hardening`
- **Phạm vi**: `scripts/_state_envelope.py`, `scripts/estimate_heartbeat.py`, `scripts/resume_context.py`, `scripts/verify.sh`, `.agents/quality/python-quality.json`, `skills/quality_check/resources/scripts/verify_polyglot_registry.py`, `skills/quality_check/SKILL.md`, `skills/dev-lifecycle/references/handoff-template.md`, `skills/dev-implementation/SKILL.md`, `skills/dev-implementation/resources/scripts/package_epic.py`, `skills/dev-implementation/resources/scripts/check_epic_readiness.py`, `skills/dev-implementation/resources/scripts/check_task_contract.py`, `skills/dev-implementation/resources/scripts/sync_task_status.py`, `skills/dev-implementation/resources/scripts/manage_worker_pool.py`, `skills/finishing-a-development-branch/SKILL.md`, `skills/finishing-a-development-branch/resources/scripts/integrate_branch.py`, `skills/dev-brainstorming/SKILL.md`, `skills/dev-designer/SKILL.md`, `skills/principal-review/SKILL.md`, `skills/cross-model-review/SKILL.md`, `skills/check-tasks/resources/scripts/check_tasks.py`, `skills/check-tasks/resources/scripts/tasks_server.py`, `skills/check-tasks/resources/dashboard/tasks_dashboard.html`, `skills/check-quota/resources/dashboard/quota_dashboard.html`, `rules/CRITICAL_RULES.md`, `tests/`
- **Bước tiếp theo**: `dev-designer` (Stage 2)

## Mục lục

- [1. Bối cảnh](#1-bối-cảnh)
- [2. Mục tiêu và Ngoài phạm vi](#2-mục-tiêu-và-ngoài-phạm-vi)
  - [Mục tiêu](#mục-tiêu)
  - [Ngoài phạm vi](#ngoài-phạm-vi)
- [3. Kiến trúc và Luồng dữ liệu](#3-kiến-trúc-và-luồng-dữ-liệu)
- [4. Thiết kế Chi tiết Từng Thành phần](#4-thiết-kế-chi-tiết-từng-thành-phần)
  - [4.1. Vỏ Trạng thái Runtime Atomic và Đồng bộ Bộ nhớ Hai tầng](#41-vỏ-trạng-thái-runtime-atomic-và-đồng-bộ-bộ-nhớ-hai-tầng)
  - [4.2. Hybrid Heartbeat, Estimator Đơn giản và Tiến độ Quality Check](#42-hybrid-heartbeat-estimator-đơn-giản-và-tiến-độ-quality-check)
  - [4.3. Handoff Song song Theo Wave và Sửa `--revise` ở Stage 3](#43-handoff-song-song-theo-wave-và-sửa---revise-ở-stage-3)
  - [4.4. Dọn dẹp Cơ học Worker Pool và Subagent](#44-dọn-dẹp-cơ-học-worker-pool-và-subagent)
  - [4.5. Điểm nghẽn Phê duyệt (Phương án A), Trần 96% và Sync Live Phần II](#45-điểm-nghẽn-phê-duyệt-phương-án-a-trần-96-và-sync-live-phần-ii)
  - [4.6. Đồng bộ PIC Repo Gốc + Worktree và Ổn định Bảng Roadmap](#46-đồng-bộ-pic-repo-gốc--worktree-và-ổn-định-bảng-roadmap)
  - [4.7. Bộ Điều khiển Tầng Dialog cho Check-Quota](#47-bộ-điều-khiển-tầng-dialog-cho-check-quota)
- [5. Xử lý Lỗi và Khả năng Phục hồi](#5-xử-lý-lỗi-và-khả-năng-phục-hồi)
- [6. Cảnh báo Shared Contract](#6-cảnh-báo-shared-contract)
- [7. Chiến lược Kiểm thử và Xác minh](#7-chiến-lược-kiểm-thử-và-xác-minh)
- [8. Rủi ro và Biện pháp Giảm thiểu](#8-rủi-ro-và-biện-pháp-giảm-thiểu)

---

## 1. Bối cảnh

Qua các epic đa-agent gần đây sử dụng `d3nexus:dev-lifecycle`, tám lỗi và điểm nghẽn liên hoàn đã phát sinh giữa tầng điều phối thực thi và cặp giao diện `check-tasks` / `check-quota`:

1. **Thiếu hiển thị tiến độ tác vụ dài**: Các wave thực thi nhiều subagent và quá trình chạy `quality_check` kéo dài không có luồng tiến độ 0-token và chưa có bộ ước lượng để LLM chọn chu kỳ báo cáo hợp lý (`none` so với `180s`–`300s`).
2. **Trôi lệch Bộ nhớ Hai tầng & Phần II Dashboard**: Thay đổi trạng thái Kanban (`sync_task_status.py`), slot worker pool và tiến độ verify chưa tự đồng bộ vào Bộ nhớ Hai tầng và Phần II UI (`tier2Sig` trong `tasks_dashboard.html` chỉ theo dõi `[act, stg, wt]`).
3. **Handoff Tuần tự & Lỗi `--revise` ở Stage 3**: `resume_context.py --emit-prompt implement` và `handoff-template.md` vẫn hướng dẫn chạy tuần tự từng task thay vì song song theo wave, còn `package_epic.py --revise` bị lỗi khi chạy ở Stage 3 vì `check_epic_readiness.py` luôn bật `check_task_contract.py --design`, báo `<file> is marked (new) but already exists` đối với task đã hoàn thành.
4. **Rò rỉ tài nguyên Worker Slot**: Khi một wave song song kết thúc hoặc bị gián đoạn, thư mục `.worktrees/<epic>-slot-*` và nhánh tạm chưa có cơ chế dọn dẹp cơ học xuyên suốt.
5. **Báo giả Điểm nghẽn Phê duyệt**: `check_tasks.py` rơi về cơ chế quét `.devtool/epic/` theo bảng chữ cái (gắn nhầm `choosing_a_lifecycle` thành `Approve Gate 1 (Design Spec)`), đọc lệch giữa `GATE_LEDGER.md` và `gate_ledger.jsonl`, đồng thời chưa có cơ chế lưu `pending_decision` khi agent dừng hỏi người dùng và tự gỡ khi xác nhận (Phương án A).
6. **Trần tiến độ 99% trước khi Finish / Phần II chưa giới hạn**: Sidebar Phần I hiện chặn tiến độ khi xong hết tasks trước lúc Finish ở `99%` (`⚡ 99% Review`), còn Phần II (`renderExecutionEpics`) hiển thị thẳng `100%` mà chưa kiểm tra hội tụ Gate 4; cả hai cần áp dụng trần **`96%`** (`95%` khi đang chạy, `100%` chỉ khi Waiting Finish đã hội tụ Gate 4 / Done).
7. **Lỗi Chuyển PIC**: `assign_epic_pic()` trong `tasks_server.py` bỏ sót các bản sao `.devtool/epic/<epic>/` trong worktree, không khớp dòng `**PIC / Assigned Profile**` và sửa lan sang các file không liên quan (`principal_review.md`, `bdd_scenarios.*.md`); trong khi `tasks_dashboard.html` sắp xếp bảng Roadmap theo `mtime` biến động liên tục và thay thế DOM `<select>` giữa lúc thao tác, dẫn tới đổi nhầm dòng và không refresh `modal-epics`.
8. **Chồng nhiều tầng Dialog ở Check-Quota**: Nhúng `quota_dashboard.html` trong `modal-quota` tạo 3 lớp overlay lồng nhau; mở dialog con mới không đóng dialog con cũ; click nền mờ hoặc nhấn `Escape` bỏ qua `profileInfoModal`/`appealDetailModal` và đóng nhầm luôn iframe cha.

---

## 2. Mục tiêu và Ngoài phạm vi

### Mục tiêu
- Cung cấp tầng **Vỏ Trạng thái Runtime (Runtime State Envelope)** ghi atomic trong `.devtool/state/` (`<epic_slug>.heartbeat.json`, `quality_active.json`, `pending_decision.json`) dùng chung giữa CLI điều phối và `check_tasks.py`.
- Xuất dòng tiến độ 0-token ra `stderr` kèm snapshot JSON atomic khi chạy `verify_polyglot_registry.py` và từng wave thực thi, kết hợp script estimator đơn giản `scripts/estimate_heartbeat.py` trả về `null` / `180` / `240` / `300` giây.
- Tự động đồng bộ thay đổi Kanban và slot worker vào `.devtool/state/<epic_slug>.md` + `assistant_state.md` và đẩy live lên Phần II của `tasks_dashboard.html`.
- Chuyển `emit_handoff_prompt` (`implement`) và `handoff-template.md` sang thực thi song song theo wave (`compute_execution_order.py --parallel`), sửa `package_epic.py --revise` cho Stage 3, và tự động hóa dọn dẹp worker pool.
- Áp dụng cơ chế Điểm nghẽn Phê duyệt Phương án A (`--pending-decision` lúc dừng và tự gỡ khi duyệt/tiếp tục), hạ trần trước Finish từ `99%` xuống **`96%`**, sửa `assign_epic_pic()` đồng bộ repo gốc + toàn bộ worktree với khóa dòng ổn định, và gom quản lý dialog trong `quota_dashboard.html` qua một Modal Stack Controller duy nhất.

### Ngoài phạm vi
- Không dựng daemon SQLite hay server DB tập trung để giữ khóa liên tiến trình (ghi JSON atomic + `fcntl.flock` là đủ).
- Không gọi LLM API bên ngoài bên trong `estimate_heartbeat.py` hay `verify_polyglot_registry.py`.
- Không sửa mã nguồn hay `.devtool/` trong các repo đích khác (ví dụ `lyrics-sync`) trong quá trình triển khai epic này của bộ kit.

---

## 3. Kiến trúc và Luồng dữ liệu

Phương án được chọn là **Phương án B (Runtime State Envelope + Pure UI/Contract Layer)**, tách rạch ròi giữa bên ghi state 0-token (các CLI scripts) và bên đọc hiển thị (`check_tasks.py` cùng hai dashboard HTML):

```mermaid
flowchart TD
    SYNC["sync_task_status.py / manage_worker_pool.py"] -->|"fcntl.flock + os.replace"| HB["heartbeat.json & Bo nho Hai tang"]
    EST["scripts/estimate_heartbeat.py"] -->|"null / 180s / 240s-300s"| ORCH["Agent Wave & Quality Watchdog"]
    QC["verify_polyglot_registry.py"] -->|"stderr 15s + ghi atomic"| QACT["quality_active.json"]
    PAUSE["Dung hoi Human Stage 1-4"] -->|"--pending-decision / --clear-decision"| PDEC["pending_decision.json"]
    HB --> SCAN["check_tasks.py scan_repo()"]
    QACT --> SCAN
    PDEC --> SCAN
    SCAN -->|"Tran 96% + Ledger hop nhat + Live state"| UI["tasks_dashboard.html Phan II & Roadmap"]
    PIC["tasks_server.py assign_epic_pic()"] -->|"Repo goc + git worktree list"| REPO["HLD, handoff, tasks, .vscode/settings.json"]
    QUOTA["quota_dashboard.html Stack Controller"] <-->|"postMessage reset & phim Escape"| UI
```

Mọi script ghi state đều phân giải **cả** `.devtool/state/` của worktree hiện hành lẫn repo gốc (`git rev-parse --git-common-dir` / `resolve_primary_repo_root()`) để `tasks_server.py` quét từ repo gốc luôn thấy dữ liệu live dù lệnh chạy từ bất kỳ worktree nào.

---

## 4. Thiết kế Chi tiết Từng Thành phần

### 4.1. Vỏ Trạng thái Runtime Atomic và Đồng bộ Bộ nhớ Hai tầng

Tạo module dùng chung `scripts/_state_envelope.py` để cả `scripts/` lẫn các skill scripts gọi được qua `KIT_ROOT / "scripts"`:
- `resolve_shared_devtool_dirs(cwd: Path) -> list[Path]`: trả về danh sách `.devtool/` không trùng lặp gồm repo gốc trước và active worktree (nếu đang chạy trong worktree).
- **Khóa Giao dịch Tại Repo Gốc & Snapshot Phiên bản hóa**: `run_state_transaction()` giữ một khóa `fcntl.flock` duy nhất trên `.devtool/state/.state_envelope.lock` tại repo gốc bao trùm toàn bộ chu trình read -> merge -> tăng đơn điệu `generation += 1` -> ghi file tạm atomic + `os.replace()` tại repo gốc -> đồng bộ atomic sang worktree đang chạy (từ chối ghi đè bởi snapshot có `generation` thấp hơn để các cập nhật RMW đa tiến trình không làm rơi slot hoặc lệch bản sao).
- `read_json_safe(path: Path, default: T) -> T`: trả về `default` an toàn nếu thiếu file hoặc JSON hỏng (không làm sập polling của `check_tasks.py`).
- Mỗi khi `sync_task_status.py`, `manage_worker_pool.py` (`init`, `sync`, `merge`, `cleanup`), hoặc `resume_context.py` (`--state`, `--wave`) cập nhật tiến độ hoặc slots của epic, hệ thống cập nhật có giao dịch `.devtool/state/<epic_slug>.heartbeat.json` (`generation`, `epic_slug`, `stage`, `active_wave`, `active_tasks`, `slots`, `last_event`, `updated_at`) và tái tạo `<epic_slug>.md` cùng `assistant_state.md` dưới khóa.

### 4.2. Hybrid Heartbeat, Estimator Đơn giản và Tiến độ Quality Check

1. **Tiến độ Quality Check 0-Token (`verify_polyglot_registry.py`)**:
   - Cô lập từng lần chạy bằng `run_id` duy nhất (`uuid`/timestamp-pid), thực thi từng capability trong process group con (`subprocess.Popen(..., start_new_session=True)`), và ghi luồng log vào đường dẫn theo run `build/quality/<provider>/runs/<run_id>/<cap>.log`.
   - Mỗi `heartbeat_interval` giây (mặc định `15s`, tham số hóa để test nhanh), in 1 dòng gọn ra `stderr` (`[quality_check] 2/5 <provider>:<cap> (<elapsed>s elapsed)`) và cập nhật mục theo namespace `runs[run_id]` bên trong `.devtool/state/quality_active.json` (`{run_id, epic_slug, profile, status, provider, capability, step_index, step_total, pid, host, started_at, updated_at, ttl_sec, elapsed_sec}`) dưới khóa sở hữu run để các tiến trình chạy song song không ghi đè lẫn nhau.
   - Gắn bộ xử lý tín hiệu `SIGINT`/`SIGTERM` kết hợp `try ... finally` để dừng + thu hồi process group con đang chạy và chốt **riêng** `runs[run_id]` về `"passed" | "failed" | "aborted"`; phía đọc (`check_tasks.py`) hết hạn các mục có PID chết hoặc quá `updated_at + ttl_sec` thành `"stale"`.
2. **Script Estimator Quy tắc Đơn giản (`scripts/estimate_heartbeat.py`)**:
   - Nhận tham số CLI gọn nhẹ (`--tasks-count`, `--files-count`, `--epic-dir` / `--wave`, hoặc `--quality-profile fast|pr|epic|release|full`, `--has-e2e`).
   - Cộng điểm ước lượng thời lượng (`estimated_sec`) và trả về JSON 3 ngưỡng:
     - `estimated_sec < 60` -> mức `"light"`, `recommended_interval_sec: null` (không đặt timer `schedule()`, 0 token phát sinh).
     - `60 <= estimated_sec <= 240` -> mức `"medium"`, `recommended_interval_sec: 180`.
     - `estimated_sec > 240` -> mức `"heavy"`, `recommended_interval_sec: 240` (hoặc `300` khi có `--has-e2e` / `epic` full regression).
   - Bổ sung bước gọi pre-flight ngắn gọn vào `skills/dev-implementation/SKILL.md` và `skills/quality_check/SKILL.md`, giữ `rules/CRITICAL_RULES.md` nằm gọn trong giới hạn `<= 8192` bytes.

### 4.3. Handoff Song song Theo Wave và Sửa `--revise` ở Stage 3

1. **Handoff Song song Theo Wave (`resume_context.py` & `handoff-template.md`)**:
   - Cập nhật `emit_handoff_prompt()` (`mode == "implement"`) trong `scripts/resume_context.py` và phần `## Resume Prompt` trong `skills/dev-lifecycle/references/handoff-template.md`.
   - Hướng dẫn Role 2.3 Orchestrator thực hiện: (a) chạy `compute_execution_order.py <epic_slug> --parallel`, (b) chạy `estimate_heartbeat.py` trước mỗi wave / Gate 4, (c) chạy song song các task độc lập qua `manage_worker_pool.py` hoặc subagent (`workspace:"share"`) và chạy tuần tự tại worktree chính với wave 1 task hoặc chạm chung file, (d) merge từng slot, chạy verify wave và dọn slot xong.
2. **Tương thích `--revise` ở Stage 3 (`package_epic.py`, `check_epic_readiness.py`, `check_task_contract.py`)**:
   - Thêm cờ `--post-design` trên `check_epic_readiness.py` và `--allow-existing-done-new` trên `check_task_contract.py`.
   - Trong `package_epic.py --revise`: tự nhận diện nếu epic đã vào Stage 3 (có Gate 3 trong `gate_ledger.jsonl` / `GATE_LEDGER.md` HOẶC có ít nhất 1 task ở trạng thái `in-progress`, `review` hay `done`) để truyền `--post-design` cho `check_epic_readiness.py`.
   - Trong `check_task_contract.py`: khi bật `--design --allow-existing-done-new`, các task ở trạng thái `done`, `review`, hoặc `in-progress` được miễn lỗi `<pattern> is marked (new) but already exists` đối với các file Allowed/Evidence do chính task đó đã tạo trước đó (vẫn từ chối khai báo `(new)` trùng lặp giữa các task và đánh trượt task `todo` có đường dẫn `(new)` đã tồn tại). Các epic tiền-Stage-3 giữ nguyên kiểm tra `--design` chặt chẽ.

### 4.4. Dọn dẹp Cơ học Worker Pool và Subagent

- Mở rộng `cleanup_slots()` / lệnh `cleanup` trong `skills/dev-implementation/resources/scripts/manage_worker_pool.py`:
  - Gán các điểm cập nhật heartbeat slot/wave tường minh qua `init`, `sync --task --wave`, `merge`, `cleanup`, và `resume_context.py --wave`.
  - Kiểm tra từng slot worktree và branch (kể cả khi thư mục worktree đã mất) trước khi xóa: chỉ tự động xóa các slot sạch, đã tích hợp (`git status --porcelain` rỗng và đã merge vào nhánh epic/base đích) kết hợp chạy `git worktree prune`; **giữ lại và báo cáo** worktree bẩn, commit chưa merge, hoặc branch chưa merge bị thiếu worktree (cập nhật trạng thái slot rõ ràng thay vì âm thầm xóa) trừ khi truyền tường minh `--discard-unmerged` / `--force`.
  - Hỗ trợ `--stale-only`, bắt buộc chạy `manage_worker_pool.py cleanup` an toàn trước Gate 4 (`dev-implementation/SKILL.md`), và chạy dọn slot mồ côi trong `integrate_branch.py cmd_land`.

### 4.5. Điểm nghẽn Phê duyệt (Phương án A), Trần 96% và Sync Live Phần II

1. **Lưu khi dừng — Tự gỡ khi duyệt (Phương án A)**:
   - Bổ sung `--pending-decision "<lý do>"`, `--decision-kind <loại>` và `--clear-decision` vào `scripts/resume_context.py` để lưu bản ghi theo namespace epic trong `.devtool/state/pending_decision.json` (`decisions[epic_slug] = {decision_id, epic, kind, reason, stage, created_at, worktree}` kèm tóm tắt active) dưới khóa giao dịch tại repo gốc.
   - Cơ chế gỡ yêu cầu khớp đúng quyền sở hữu `epic` (và `--decision-id` tùy chọn) khi `--gate <N>`, `--clear-decision`, `--state`, `sync_task_status.py`, hoặc `package_epic.py` chạy, nhờ vậy các epic song song không xóa nhầm phê duyệt đang chờ của epic khác.
   - Cập nhật hướng dẫn tại Stage 1–4 (`dev-brainstorming`, `dev-designer`, `principal-review`, `cross-model-review`, `finishing-a-development-branch`, `CRITICAL_RULES.md`) để mỗi lần dừng hỏi Human đều ghi `--pending-decision` trước khi kết thúc lượt.
2. **Loại bỏ báo giả lúc Idle & Hợp nhất Ledger (`check_tasks.py`)**:
   - Bỏ fallback Strategy 7 quét thư mục theo chữ cái trong `resolve_active_epic()` trong khi giữ nguyên Strategy 6 (quét `features/`), và bỏ logic tự bịa `Approve Gate 1 (Design Spec)` khi chưa có `pending_decision` hoặc trạng thái thực thi đang hoạt động.
   - Sửa `parse_gate_ledger_entries()` để gộp và khử trùng dữ liệu giữa `gate_ledger.jsonl` và `GATE_LEDGER.md` của cả repo gốc lẫn active worktree, không dừng sớm khi `GATE_LEDGER.md` chứa phê duyệt mới hơn.
   - Đưa `pending_decision`, `heartbeat`, `quality_active` khớp theo epic và các `quality_runs` đang chạy đồng thời (hết hạn các mục PID chết/quá TTL thành `"stale"`) vào `RepoMetadata` / `/api/tasks`.
3. **Trần `96%` & Cập nhật Live Phần II (`tasks_dashboard.html`)**:
   - Áp dụng trần `96%` (`⚡ 96% Review`) khi đã xong hết tasks trước lúc Finish trên cả Phần I (`renderKanbanDashboard`: đổi `99`/`98` thành `96`/`95`) và Phần II (`renderExecutionEpics`: bổ sung giới hạn nhận biết `isFullyDone`/`isWaitingFinish` tại nơi đang render thô `100%`), chỉ dành `100%` cho `Waiting Finish` đã hội tụ hoặc `Done`.
   - Sửa `tier2Sig` lúc mount (`L2938`) và lúc polling (`L2724`) để theo dõi `account_id`, `prompt`, `is_human_action_required`, `task_progress` (số đếm/task đang chạy), `heartbeat`, và `quality_active`, cập nhật thanh tiến độ wave/slot/quality trực tiếp ở Phần II mà không cần tải lại trang.

### 4.6. Đồng bộ PIC Repo Gốc + Worktree và Ổn định Bảng Roadmap

1. **Backend (`tasks_server.py` & `check_tasks.py`)**:
   - Tái cấu trúc `assign_epic_pic()` dùng `git worktree list --porcelain` tìm tất cả worktree khớp epic (theo tên nhánh `epic/<slug>` hoặc thư mục/tiền tố `<epic_dir>` / `<slug>`) bên cạnh repo gốc.
   - Cập nhật PIC nguyên tử trên **cả repo gốc lẫn mọi worktree khớp epic** chỉ trong các tệp đích: HLD (`<epic>.en.md`, `<epic>.vi.md`, metadata design spec), `handoff.md` (gồm dòng `- **PIC / Assigned Profile**:`), `task_*.md` trong cả `.devtool/epic/<epic>/` và `.devtool/features/`, `.devtool/state/<slug>.pipeline.json`, `.devtool/state/<slug>.heartbeat.json`, và `.vscode/settings.json` của worktree. Không bao giờ chèn `- **PIC**:` vào tài liệu prose review/BDD (`bdd_scenarios.*`, `principal_review.md`, `review_results.md`).
   - Cập nhật `extract_epic_pic()` để đọc chính xác placeholder `**PIC / Assigned Profile**` và kiểm tra thêm `handoff.md`/HLD ở worktree đang hoạt động.
2. **Frontend (`tasks_dashboard.html`)**:
   - Ổn định `sortEpicsForRoadmap`: thay thế tường minh so sánh timestamp `mtime` dưới 1 ngày bằng nhóm trạng thái + `active_epic` + cụm ngày tạo (`YYYY-MM-DD`) + khóa phụ xác định theo slug (`a.slug.localeCompare(b.slug)`), đồng thời gắn `data-row-key="<repo>:<epic_slug>"` cho mọi dòng và `<select>`.
   - Tạm hoãn thay `roadmapTbody.innerHTML` trong nhịp polling 5 giây khi `.select-pic-roadmap` đang focus/tương tác (`document.activeElement`), căn khớp `roadmapSig` lúc mount (`L2934`) với lúc poll (`L2699`), và sửa kiểm tra hiển thị `modal-epics` trong `updateEpicPic()` (`style.display === 'flex'` thay vì `.classList.contains('active')`) cùng khớp khóa `refreshAllProfileSelects`.

### 4.7. Bộ Điều khiển Tầng Dialog cho Check-Quota

Trong `skills/check-quota/resources/dashboard/quota_dashboard.html` và `skills/check-tasks/resources/dashboard/tasks_dashboard.html`:
- Thay các hàm bật/tắt rời rạc (`openScheduleModal`, `openLoginModal`, `openProfileInfoModal`, `openAppealModal`) bằng bộ điều khiển `openQuotaSubModal(modalId)` / `closeQuotaSubModal(modalId)` / `closeAllQuotaSubModals()` với bất biến: **tại một thời điểm chỉ có tối đa một dialog con được mở trong `quota_dashboard.html`**.
- Gắn click nền mờ trực tiếp lên `#scheduleModal`, `#loginModal`, `#profileInfoModal`, `#appealDetailModal` (`if (e.target === modalEl) closeQuotaSubModal(...)`), và thêm đủ 4 ID này vào bộ lọc click của document iframe để click nền ngoài chỉ đóng **chính dialog con đó**, không đóng `#modal-quota`.
- Sửa tầng phím `Escape`: bên trong `quota_dashboard.html`, `Escape` ưu tiên đóng dialog con đang mở; chỉ khi không còn dialog con nào mở mới gọi `handleCardClose()`.
- Phía `tasks_dashboard.html`, gắn `?embedded=1` vào `#quota-iframe.src` trong `openQuotaModal` và `refreshQuotaIframe` (kèm phát hiện dự phòng `window.parent !== window` bên trong `quota_dashboard.html` để làm phẳng padding/viền ngoài lồng đôi của `#dashboardCard`), bắt phím `Escape` từ cửa sổ cha sạch sẽ, và gửi `{action: 'reset_quota_submodals'}` tới `#quota-iframe` mỗi khi `#modal-quota` mở hoặc đóng để lần mở lại không còn dialog con mồ côi.

---

## 5. Xử lý Lỗi và Khả năng Phục hồi

- **File JSON hỏng hoặc ghi dở dang**: `_state_envelope.py` ghi qua file tạm + `os.replace()` dưới `fcntl.flock`; `read_json_safe()` trả giá trị mặc định an toàn để không làm treo pipeline hoặc `/api/tasks`.
- **Worktree mồ côi hoặc verify bị ngắt ngang**: `verify_polyglot_registry.py` luôn chốt `quality_active.json` trong `finally`; `manage_worker_pool.py cleanup --stale-only` bỏ qua thư mục đã mất và chạy `git worktree prune`.
- **Iframe chưa tải xong / khác origin**: Giao tiếp `postMessage` giữa `tasks_dashboard.html` và `#quota-iframe` kiểm tra tồn tại `contentWindow` và bỏ qua thông điệp không đúng schema.
- **Bảo vệ đầu vào `assign_epic_pic()`**: Kiểm tra chặt `new_pic` khớp `^[a-zA-Z0-9_\-]+$` và chỉ thao tác file nằm trong cây thư mục repo/worktree hợp lệ.

---

## 6. Cảnh báo Shared Contract

Kho lưu trữ này (`ai-agent-tools`) là repo kit/plugin dùng chung độc lập và **không có thư mục hay symlink `shared-contracts/`**. Các repo sử dụng (`lyrics-sync`, `D3Nexus`, `nexus`) đọc dữ liệu `.devtool/` và gọi scripts từ plugin này. Do đó:
- Các schema JSON mới (`heartbeat.json`, `quality_active.json`, `pending_decision.json`) và các cờ CLI mở rộng (`--post-design`, `--pending-decision`, `--clear-decision`) đều mang tính **bổ sung tùy chọn**, tương thích ngược hoàn toàn với repo chưa có các tệp state mới.
- `tasks_dashboard.html` xử lý mặc định an toàn khi snapshot JSON cũ thiếu các trường mới.

---

## 7. Chiến lược Kiểm thử và Xác minh

Toàn bộ hành vi được kiểm thử tự động theo đơn vị, tích hợp và trình duyệt/UI tích hợp vào `scripts/verify.sh`:
- **Envelope & Estimator**: Kiểm thử đồng thời RMW giao dịch + bản sao khớp `generation`, `pending_decision`/`quality_active` theo namespace, dự phòng JSON hỏng, và 3 ngưỡng `estimate_heartbeat.py` (`light -> null`, `medium -> 180`, `heavy -> 240/300`).
- **Tiến độ Quality Check Live**: Mock capability runner xác minh dòng `stderr` mỗi `15s` (tham số hóa `0.1s` trong test), cô lập `runs/<run_id>/<cap>.log`, thu hồi tiến trình con khi `SIGINT`/`SIGTERM` -> `"aborted"`, và hết hạn `"stale"` theo `ttl_sec`/PID chết.
- **Handoff, `--revise` Stage 3 & Dọn dẹp**: `resume_context.py --emit-prompt implement` xác minh hướng dẫn wave song song, `package_epic.py --revise` pass ở Stage 3 trên task `done`/`review`/`in-progress` và chặn task `todo` va chạm, đồng thời `manage_worker_pool.py cleanup` an toàn giữ nguyên worktree bẩn/nhánh chưa merge & nhánh mồ côi thiếu worktree trừ `--discard-unmerged` trong khi ghi nhận slots `"working"` trước lúc dọn.
- **Điểm nghẽn Phương án A & Trần 96%**: Lưu/tự gỡ theo namespace epic qua `--pending-decision`, `--gate`, `--state`, `sync_task_status.py` không ghi đè epic anh em; `check_tasks.py` trả `is_human_action_required=False` cho repo rỗi kèm `quality_runs` / phục hồi stale; Phần I/II chốt trần `96%`.
- **Chuyển PIC, Roadmap & Tầng Dialog (Node Unit + Chrome CDP Thật)**: `assign_epic_pic()` cập nhật repo gốc + worktree (`handoff.md`/HLD/`task_*.md`/`.vscode/settings.json`) không chạm `principal_review.md`; unit check Node script trích xuất kết hợp **Chrome CDP không giao diện thật** (`CHROME_BIN` / Chrome cài sẵn + `node v25` WebSocket) chạy trên `TasksServer` `127.0.0.1` xác minh `getComputedStyle` (`?embedded=1` phẳng viền), giữ focus `<select>` khi polling dù `mtime` cùng ngày khác nhau, và đóng mở qua lại `Escape`/backdrop/`postMessage` giữa iframe và cha trong `#modal-quota`.

---

## 8. Rủi ro và Biện pháp Giảm thiểu

| Rủi ro | Mức ảnh hưởng | Biện pháp giảm thiểu |
| :--- | :--- | :--- |
| **`CRITICAL_RULES.md` vượt ngưỡng 8192-byte prompt budget** | Bị cắt rule trên các harness agent | Mọi bổ sung vào `rules/CRITICAL_RULES.md` thật cô đọng (`<= 8000` bytes tổng); chi tiết thao tác đặt trong `SKILL.md` và script. |
| **`--post-design` nới lỏng kiểm tra tiền-triển-khai** | Bỏ sót task mới khai báo sai ở Stage 2 | Chỉ kích hoạt `--allow-existing-done-new` khi `--revise` phát hiện dấu hiệu Stage 3 và chỉ cho task `done`/`review`/`in-progress`, đồng thời vẫn chặn khai báo `(new)` va chạm trên task `todo`. |
| **Lệch state giữa repo gốc và worktree** | `check_tasks` hiển thị phê duyệt/tiến độ cũ khi làm trong worktree | `_state_envelope.py` thực thi RMW dưới một khóa `fcntl.flock` duy nhất tại repo gốc kèm số `generation` đơn điệu và đồng bộ atomic tới repo gốc + worktree. |
| **Bảng Roadmap nhảy hàng lúc thao tác** | Đổi nhầm PIC epic khi poll 5s thay thế DOM | Ghim khóa hàng ổn định (`data-row-key`), bỏ sắp xếp theo `mtime` dưới 1 ngày trong `sortEpicsForRoadmap`, hoãn thay `tbody` khi `.select-pic-roadmap` giữ focus, và kiểm chứng trên Chrome CDP thật. |

<!-- sync-en-sha256: 4d53effc3f004876 -->
