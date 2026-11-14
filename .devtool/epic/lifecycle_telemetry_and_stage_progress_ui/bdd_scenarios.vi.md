# Kịch bản BDD: Telemetry Lifecycle, Bước con Từng Stage & Giao diện Thanh Tiến trình

## Mục lục

- [1. Kịch bản Luồng chính (HP)](#1-kịch-bản-luồng-chính-hp)
- [2. Kịch bản Trường hợp biên (EC)](#2-kịch-bản-trường-hợp-biên-ec)
- [3. Kịch bản Chuyển đổi Trạng thái (ST)](#3-kịch-bản-chuyển-đổi-trạng-thái-st)
- [4. Kịch bản Kiến trúc và Đồng thời (AR)](#4-kịch-bản-kiến-trúc-và-đồng-thời-ar)
- [5. Kịch bản Phục hồi Lỗi (FR)](#5-kịch-bản-phục-hồi-lỗi-fr)

---

## 1. Kịch bản Luồng chính (HP)

```gherkin
Scenario: [LTSP-HP-01] [Tier A - Unit] Vỏ heartbeat duy trì ring buffer log sự kiện giới hạn 20 mục và review_state có cấu trúc
Given một git repository có thư mục `.devtool/state/` đã khởi tạo cho epic "demo_epic"
When `update_epic_heartbeat` được gọi 25 lần với các chuỗi `last_event` khác nhau và `review_state={"kind": "code", "round": 1, "max_rounds": 3, "cli": "codex", "model": "gpt-6.1-sol", "phase": "reviewing"}`
Then `.devtool/state/demo_epic.heartbeat.json` chứa danh sách `events` có độ dài 20
And `events[0]["message"]` bằng `"event-06"` và `events[-1]["message"]` bằng `"event-25"`
And `review_state["phase"]` bằng `"reviewing"` và `review_state["cli"]` bằng `"codex"`

Scenario: [LTSP-HP-02] [Tier A - Unit] Trình chạy quality đa ngôn ngữ ánh xạ nhãn capability và ghi trạng thái từng bước cùng sự kiện bắt đầu/kết thúc tách biệt
Given một quality manifest cho provider "python-qa" với các capability `["lint", "typecheck", "pycore", "integration", "e2e"]`
When `_QualityRunCoordinator` bắt đầu bước 1 (`"lint"`), hoàn tất ở trạng thái `"passed"`, và bắt đầu bước 3 (`"pycore"`)
Then `format_capability_label("python-qa", "pycore")` trả về `"PyCore / Unit Test"`
And `format_capability_label("python-qa", "integration")` trả về `"Integration Test"`
And `format_capability_label("python-qa", "e2e")` trả về `"UI / E2E Test"`
And `runs[run_id]["steps"]` của `quality_active.json` chứa 5 mục với bước `"lint"` có trạng thái `"passed"` và bước `"pycore"` có trạng thái `"running"` cùng nhãn `"PyCore / Unit Test"`
And `events` của `<epic_slug>.heartbeat.json` giữ riêng cả sự kiện bắt đầu (`"running..."`) lẫn sự kiện hoàn tất (`"-> passed"`) của `"lint"` mà không bị gộp khử trùng lặp

Scenario: [LTSP-HP-03] [Tier A - Unit] Harvester Check-Tasks kích hoạt epic ngay sau khi phê duyệt Gate 1 và trích xuất telemetry Stage 1-2
Given một git repository chứa `.devtool/epic/early_epic/2026-11-14-early-epic-design.en.md` với `- **PIC**: phungthuy8901` và Gate 1 đã được ghi vào `GATE_LEDGER.md` khi chưa có thư mục `.worktrees/early_epic`
When `scan_repo` thu thập metadata của repository
Then `meta.active_epic` bằng `"early_epic"`
And `meta.account_id` bằng `"phungthuy8901"`
And mục epic tương ứng trong `meta.epics_summary.epics` có `status` bằng `"in_progress"`
And `meta.pipeline_telemetry["lifecycle_progress_pct"]` nằm trong khoảng từ 10 đến 25
And `meta.pipeline_telemetry["stages"][0]["status"]` bằng `"done"` và `meta.pipeline_telemetry["stages"][1]["status"]` bằng `"running"`

Scenario: [LTSP-HP-04] [Tier A - Unit] Harvester tách rời mức hoàn thành 100% Task Implementation khỏi tiến trình lifecycle 6-stage theo trọng số
Given một epic đang chạy "full_tasks_epic" đã duyệt Gate 1, Gate 2, Gate 3 và hoàn thành 9/9 tasks với `status: "done"` trước khi hội tụ Gate 4
When `scan_repo` tính toán `task_progress` và `pipeline_telemetry`
Then `meta.task_progress.done_tasks` bằng 9 và `meta.task_progress.total_tasks` bằng 9
And `meta.task_progress.task_completion_pct` bằng 100.0
And `meta.pipeline_telemetry["task_completion_pct"]` bằng 100.0
And `meta.pipeline_telemetry["stages"][2]["status"]` bằng `"done"` và `meta.pipeline_telemetry["stages"][2]["summary"]` chứa `"9/9 (100%)"`
And `meta.pipeline_telemetry["lifecycle_progress_pct"]` nằm trong khoảng từ 80 đến 96

Scenario: [LTSP-HP-05] [Tier C - Integration] Tasks dashboard render stepper 6-stage, vi bước đang chạy, huy hiệu 100% task, log cuộn và tổng quan stage Kanban TIẾN ĐỘ EPICS
Given một payload repository có 9/9 tasks `"done"`, Cross-Model Review Round 1 (`codex / gpt-6.1-sol`) đang ở pha `"triage"`, và `heartbeat.events` có 5 mục kèm timestamp
When `renderExecutionEpics` và `renderKanbanDashboard` render Phần II và bảng Kanban trong `tasks_dashboard.html`
Then HTML Phần II sau render chứa `"9 / 9 Hoàn thành"` và `"100%"` cho Task Implementation
And `[data-telemetry="pipeline-stepper"]` render đủ 6 stage lifecycle với `"Tasks"` đã hoàn thành (`100%`) và `"Cross-Review"` đang chạy
And `[data-telemetry="sub-steps"]` render 4 vi bước review `"Reviewing"`, `"Lập bảng triage"`, `"Fix findings"`, và `"Verifying"` cùng `"Round 1/3"` và `"codex"`
And `[data-telemetry="event-logs"]` render các sự kiện heartbeat mới nhất kèm timestamp
And thẻ sidebar `"TIẾN ĐỘ EPICS"` trên Kanban hiển thị phần trăm tiến trình lifecycle theo trọng số, `"9/9 Tasks (100%)"`, và `[data-telemetry="kanban-epic-stage"]` chỉ rõ stage và vi bước hiện tại

Scenario: [LTSP-HP-06] [Tier C - Integration] Kiểm thử đầu-cuối trên Chrome CDP headless xác minh chuyển đổi stage và vi bước trực tiếp từ Tasks sang Quality Check sang Cross-Model Review
Given một máy chủ `TasksServer` đang phục vụ `tasks_dashboard.html` trong phiên Chrome CDP headless
When trạng thái máy chủ lần lượt chuyển từ Wave 2 Task Implementation (`8/9 tasks`) sang All Tasks Done (`9/9 · 100%`) đang chạy Quality Check (`PyCore / Unit Test 3/5`) sang Cross-Model Review Round 1 (`codex reviewing -> Lập bảng triage -> Fix findings -> Verifying`)
Then `pollDashboard()` cập nhật Phần II tại chỗ mà không tải lại trang
And chỉ báo Task Implementation hiển thị `"9 / 9 Hoàn thành"` và `"100%"`
And dải vi bước hiển thị `"PyCore / Unit Test"` trong lúc Quality Check và `"Round 1/3"` kèm `"Lập bảng triage"` và `"Fix findings"` trong lúc Cross-Model Review
And cả `cdp.consoleErrors` lẫn `cdp.runtimeExceptions` đều bằng `[]`
```

---

## 2. Kịch bản Trường hợp biên (EC)

```gherkin
Scenario: [LTSP-EC-01] [Tier A - Unit] Các sự kiện heartbeat giống hệt liên tiếp được khử trùng lặp trong ring buffer events
Given tệp heartbeat của epic `.devtool/state/dedup_epic.heartbeat.json`
When `update_epic_heartbeat` được gọi 5 lần liên tiếp với cùng `last_event="wave 1 polling"`
Then `heartbeat["events"]` chứa đúng 1 mục có `message == "wave 1 polling"` với `ts` được cập nhật theo timestamp mới nhất

Scenario: [LTSP-EC-02] [Tier A - Unit] Các thư mục epic backlog ngủ đông và epic đã bị hủy không kích hoạt active_epic ngay cả khi còn lưu Gate 1 hoặc heartbeat
Given một repository chứa `.devtool/epic/dormant_backlog/dormant_backlog.en.md` với `- **Status**: Backlog` và `.devtool/epic/abandoned_old/abandoned_old.en.md` với `- **Status**: Abandoned` cùng một bản ghi Gate 1 còn sót và `.devtool/state/abandoned_old.heartbeat.json`
When `resolve_active_epic` và `harvest_epics_overview` kiểm tra repository
Then `resolve_active_epic` trả về `None`
And mục `"dormant_backlog"` trong `epics_summary.epics` có `status` bằng `"unstarted"` và `"abandoned_old"` có `status` bằng `"abandoned"`

Scenario: [LTSP-EC-03] [Tier C - Integration] Dashboard suy giảm mượt mà khi payload cũ không có pipeline_telemetry hoặc events
Given một payload `/api/tasks` cũ của repository không có `pipeline_telemetry` hoặc `heartbeat.events` với `done_tasks == 4` và `total_tasks == 4`
When `renderExecutionEpics` và `renderKanbanDashboard` thực thi trong DOM harness
Then không có ngoại lệ JavaScript nào bị ném ra
And `computeEpicProgressState` tổng hợp được `taskPct == 100` cho tiến độ task và một `pct` hợp lệ cho tiến trình lifecycle

Scenario: [LTSP-EC-04] [Tier C - Integration] Khung log sự kiện đóng/mở giữ nguyên trạng thái đã mở qua các nhịp pollDashboard trực tiếp
Given một thẻ repository trong `tasks_dashboard.html` có 8 sự kiện heartbeat mà người dùng đã bấm nút mở rộng toàn bộ nhật ký
When `pollDashboard()` chạy ở nhịp poll tiếp theo với sự kiện heartbeat thứ 9 mới
Then vùng log sự kiện vẫn ở trạng thái mở rộng và hiển thị đủ 9 sự kiện thay vì tự thu gọn về bản xem trước 4 dòng
```

---

## 3. Kịch bản Chuyển đổi Trạng thái (ST)

```gherkin
Scenario: [LTSP-ST-01] [Tier A - Unit] Trình chạy external review chuyển đổi review_state qua các pha reviewing, triage, fixing và verifying
Given thư mục epic `.devtool/epic/rev_epic` có Round 1 đã hoàn tất trong `review_results.md` chứa 1 finding mức Important
When gọi tuần tự `run_external_review.py triage --epic-dir rev_epic`, `run_external_review.py status --epic-dir rev_epic --phase fixing` và `run_external_review.py status --epic-dir rev_epic --phase verifying`
Then `.devtool/state/rev_epic.heartbeat.json` ghi nhận `review_state["phase"]` chuyển từ `"triage"` (`action == "AUTO_FIX_ELIGIBLE"`) sang `"fixing"` sang `"verifying"`
And `events` ghi lại từng bước chuyển pha theo đúng thứ tự thời gian

Scenario: [LTSP-ST-02] [Tier A - Unit] Phần trăm tiến trình lifecycle tăng đơn điệu qua cả 6 stage và đòi hỏi Gate 4 đầy đủ trên SHA mới nhất trước 98% Finish
Given một epic đi tuần tự qua: (1) Stage 1 Spec, (2) Stage 2 HLD + Principal Review Round 1, (3) Stage 3 Tasks 2/4 Done, (4) Stage 3 Tasks 4/4 Done + quality_check pass nhưng chưa có Epic Audit/BDD (`87%`), (5) Gate 4 đầy đủ PASS (`88%`) + Cross-Model Review Round 2 + đang tái xác minh Gate 4 sau review (`96%`), (6) Review Hội tụ VÀ Gate 4 PASS trên HEAD SHA mới nhất (`98%` Chờ Finish), và (7) Gate 5 Done (`100%`)
When `build_epic_pipeline_telemetry` tính toán `(task_completion_pct, lifecycle_progress_pct)` ở mỗi trạng thái
Then `lifecycle_progress_pct` tăng ngặt qua từng trạng thái `(1) < (2) < (3) < (4) < (5) < (6) < (7)` kết thúc tại `100.0`
And `task_completion_pct` bằng `0.0` ở `(1)-(2)`, `50.0` ở `(3)`, và `100.0` cho mọi trạng thái từ `(4)` đến `(7)`

Scenario: [LTSP-ST-03] [Tier C - Integration] Các bước con Quality Check chuyển trạng thái trực quan từ Static Lint sang Typecheck sang PyCore/Unit Test sang UI/E2E Test
Given `quality_active.json` có phiên chạy `python-qa` với mảng `steps` chuyển từ bước 1 (`Static Lint`: `passed`), bước 2 (`Typecheck`: `passed`), bước 3 (`PyCore / Unit Test`: `running`), sang bước 4 (`UI / E2E Test`: `pending`)
When `renderExecutionEpics` render thẻ epic
Then `[data-telemetry="quality"]` hiển thị dấu đạt cho `"Static Lint"` và `"Typecheck"`, huy hiệu đang chạy cho `"PyCore / Unit Test"`, và chỉ báo chờ cho `"UI / E2E Test"`

Scenario: [LTSP-ST-04] [Tier C - Integration] Suy diễn sửa lỗi và tái xác minh theo commit nhận ra fixing sau commit và chỉ chuyển verifying khi quá trình kiểm tra thực thi
Given một epic worktree có `review_results.md` Round 1 ghi `SHA: <sha1>` với `Verdict: CHANGES REQUIRED` và 1 finding mức Important
When tạo commit mới `<sha2>` với tiêu đề `"[REV_EPIC] Fix validation edge case"` trong worktree và ghi `fixed in <sha2>` vào `review_results.md`, sau đó một phiên kiểm chứng (`quality_active.json` hoặc `run_external_review.py status --phase verifying`) chạy trên `<sha2>`
Then `build_epic_pipeline_telemetry` suy diễn vi bước Cross-Model Review Round 1 là `"fixing"` ngay sau `<sha2>` và chuyển sang `"verifying"` ngay khi phiên xác minh chạy trên `<sha2>`
```

---

## 4. Kịch bản Kiến trúc và Đồng thời (AR)

```gherkin
Scenario: [LTSP-AR-01] [Tier A - Unit] Cập nhật sự kiện heartbeat đồng thời từ nhiều tiến trình vẫn bảo toàn toàn bộ sự kiện riêng biệt dưới khóa flock
Given 4 tiến trình worker chạy song song cùng gọi `update_epic_heartbeat` với các chuỗi `last_event` khác nhau trên cùng repository
When cả 4 tiến trình hoàn tất
Then `.devtool/state/<epic>.heartbeat.json` ở cả repo gốc và bản sao worktree có cùng `generation` và danh sách `events` chứa đủ cả 4 sự kiện mà không bị lỗi dữ liệu

Scenario: [LTSP-AR-02] [Tier C - Integration] tier2Sig Phần II phát hiện thay đổi bước con, review_state, bước quality và log sự kiện mà không làm mất focus ở bảng Roadmap bên cạnh
Given dashboard được render trên Chrome CDP headless với focus đang giữ trên một thẻ `<select>` PIC của Roadmap
When `/api/tasks` chỉ cập nhật `heartbeat.review_state.phase` từ `"triage"` sang `"fixing"` và nối thêm một mục vào `heartbeat.events`
Then `pollDashboard()` cập nhật ngay Phần II hiển thị `"Fix findings"` trong khi `document.activeElement` vẫn nằm nguyên trên thẻ `<select>` của Roadmap đang focus

Scenario: [LTSP-AR-03] [Tier C - Integration] Workspace nhiều epic cô lập pipeline_telemetry theo từng epic giữa epic chính và epic thứ cấp đang chạy
Given một repository có `active_epic` chính `"epic_alpha"` ở Stage 3 Cross-Model Review (`4/4 tasks · 100%`) và epic thứ cấp `"epic_beta"` đang `in_progress` ở Stage 2 Principal Review (`0/3 tasks · 0%`)
When `scan_repo` và `renderExecutionEpics` render cả hai thẻ epic
Then `"epic_alpha"` hiển thị `100%` hoàn thành task và Stage 5 Cross-Model Review đang chạy, trong khi `"epic_beta"` hiển thị `0%` hoàn thành task và Stage 2 HLD & Principal Review đang chạy mà không rò rỉ trạng thái chéo giữa các epic
```

---

## 5. Kịch bản Phục hồi Lỗi (FR)

```gherkin
Scenario: [LTSP-FR-01] [Tier A - Unit] Lỗi ghi telemetry bên trong run_external_review.py hoặc audit_epic.py không bao giờ làm sập lệnh CLI chính
Given một repository có thư mục `.devtool/state/` tạm thời bị đặt chỉ đọc (`chmod 0555`)
When thực thi `audit_epic.py` hoặc `run_external_review.py triage`
Then lệnh vẫn kết thúc với exit code `0` và in đầy đủ báo cáo stdout chuẩn mà không ném ngoại lệ `PermissionError` chưa bắt

Scenario: [LTSP-FR-02] [Tier C - Integration] Bước quality lỗi hoặc dừng do Circuit Breaker khi review hiển thị huy hiệu cảnh báo rõ ràng trên stage stepper
Given một payload repository có `quality_active` với `status: "failed"` tại capability `"integration"` (`"Integration Test"`) hoặc `review_state` có `action: "CIRCUIT_BREAKER_HALT"`
When `renderExecutionEpics` render thẻ
Then stage tương ứng và chip vi bước render trạng thái cảnh báo lỗi/tạm dừng kèm đúng capability bị lỗi hoặc lý do circuit-breaker với zero lỗi console

Scenario: [LTSP-FR-03] [Tier C - Integration] Tệp review_results.md / heartbeat.json bị hỏng hoặc cắt cụt vẫn phục hồi sạch khi harvester thu thập pipeline
Given một epic worktree chứa JSON bị cắt cụt trong `.heartbeat.json` và các dòng bảng markdown lỗi định dạng trong `review_results.md`
When `scan_repo` thu thập thông tin repository
Then `scan_repo` hoàn tất mà không ném ngoại lệ và trả về cấu trúc `pipeline_telemetry` 6 stage hợp lệ
```

<!-- sync-en-sha256: b44e9f3ffe48e79c -->
