# Kịch bản BDD: Modal Lịch sử Epic và Telemetry Append-Only trong Check-Tasks

## Mục lục

- [1. Kịch bản Luồng chính (HP)](#1-kịch-bản-luồng-chính-hp)
- [2. Kịch bản Trường hợp biên (EC)](#2-kịch-bản-trường-hợp-biên-ec)
- [3. Kịch bản Chuyển đổi Trạng thái (ST)](#3-kịch-bản-chuyển-đổi-trạng-thái-st)
- [4. Kịch bản Kiến trúc và Đồng thời (AR)](#4-kịch-bản-kiến-trúc-và-đồng-thời-ar)
- [5. Kịch bản Phục hồi Lỗi (FR)](#5-kịch-bản-phục-hồi-lỗi-fr)

---

## 1. Kịch bản Luồng chính (HP)

```gherkin
Scenario: [CEHM-HP-01] [Tier A - Unit] Luồng sự kiện append-only không bị cắt ngắn ghi hơn 20 bước và lưu trữ heartbeat kép gạch nối gạch dưới
Given một git repository độc lập với epic "alpha_epic" bên trong `.devtool/state/`
When `update_epic_heartbeat` được gọi 25 lần với các giá trị `last_event` phân biệt `"step-01"` đến `"step-25"` và `resume_context.py --complete alpha_epic "Completed alpha"` chạy trong khi `.devtool/state/alpha_epic.heartbeat.json` cũng tồn tại
Then `.devtool/state/alpha-epic.heartbeat.json` lưu tối đa 20 sự kiện trước khi lưu trữ trong khi `.devtool/archive/events_alpha-epic_*.jsonl` giữ lại đầy đủ 25 sự kiện `"step-01"` đến `"step-25"`
And `.devtool/state/` không còn tệp mồ côi `alpha-epic.heartbeat.json`, `alpha_epic.heartbeat.json`, hoặc `logs/events_alpha-epic.jsonl`

Scenario: [CEHM-HP-02] [Tier C - Integration] Trình tổng hợp lịch sử chắp nối các tệp đa nguồn trên các biến thể gạch nối và gạch dưới cho epic Done
Given một repository với epic đã hoàn tất "alignment_flow_hardening" trong `PROJECT_LEDGER.md`, `.devtool/state/alignment-flow-hardening.heartbeat.json`, `.devtool/archive/heartbeat_alignment_flow_hardening_20261114_1200.json`, `.devtool/state/gate_ledger.jsonl`, `.devtool/archive/activity_alignment_flow_hardening_20261114_1200.log`, `task_01_alpha.md`, và `evidence/task_01_alpha.json`
When `harvest_epic_history(repo_path, "alignment_flow_hardening")` được thực thi
Then giá trị `epic["status"]` trả về bằng `"done"` và `pipeline_telemetry["stages"][5]["status"]` bằng `"done"`
And `tasks` bao gồm `"task_01_alpha"` kèm tóm tắt `evidence` gồm `passed_rows`, `total_rows`, và SHA `head`
And `timeline` chứa các sự kiện gộp theo trình tự thời gian từ `gate_ledger`, `heartbeat`, `activity_log`, và `evidence` sắp xếp theo mốc thời gian UTC

Scenario: [CEHM-HP-03] [Tier C - Integration] Endpoint HTTP lịch sử trả về tóm tắt 6 stage, tasks, timeline, cùng cả Principal và Cross-Model review
Given một `TasksServer` đang chạy trên workspace tạm thời chứa repository "demo_repo" và epic "hist_epic" với `principal_review.md` (Round 1 và Round 2) cùng `review_results.md` (Round 1)
When client gửi yêu cầu `GET /api/epic/history?repo=demo_repo&epic=hist_epic&round_principal=2&round_cross=1`
Then mã trạng thái HTTP là 200 và trường JSON `reviews["principal"]["round"]` bằng 2 với `available_rounds == [1, 2]`
And `reviews["cross_model"]["round"]` bằng 1 với `present is True` và các dòng `findings` đã được phân tích
And `pipeline_telemetry["stages"]` chứa 6 stage khớp với `compute_pipeline_telemetry`

Scenario: [CEHM-HP-04] [Tier C - Integration] Nhấp vào bất kỳ dòng epic Roadmap nào sẽ mở modal-epic-history giữ nguyên Section II và chuyển tab mượt mà
Given `tasks_dashboard.html` hiển thị với epic đang chạy trong Section II và các dòng Roadmap trong Section III cho `"done_epic"`, `"in_prog_epic"`, và `"backlog_epic"`
When người dùng nhấp vào dòng `.roadmap-epic-row` của `"done_epic"`
Then `#modal-epic-history` mở ra với `style.display === "flex"` và hiển thị pipeline stepper 6 stage trong khi Section II phía dưới tiếp tục hiển thị epic đang chạy mà không suy suyển
And việc nhấp vào các tab trong modal sẽ chuyển đổi trực tiếp giữa `Timeline & Step Logs`, `Tasks & Evidence`, `Principal Review`, và `Cross-Model Review`, đồng thời chuyển từ Round 1 sang Round 2 bên trong Review mà không mở thêm modal xếp chồng thứ hai
```

---

## 2. Kịch bản Trường hợp biên (EC)

```gherkin
Scenario: [CEHM-EC-01] [Tier A - Unit] Các epic Backlog và Packaged chưa bắt đầu không có log, task, hoặc review sẽ trả về cấu trúc lịch sử rỗng sạch sẽ
Given một repository chứa `.devtool/epic/draft_epic/2026-11-15-draft-epic-design.en.md` không có `task_*.md`, không có bản ghi `gate_ledger.jsonl`, không có `events_*.jsonl`, và không có tài liệu review
When `harvest_epic_history(repo_path, "draft_epic")` chạy và `/api/epic/history?repo=<repo>&epic=draft_epic` được truy vấn
Then mã trạng thái HTTP là 200 với `tasks == []`, `timeline == []`, `log_completeness == "none"`, cùng `reviews["principal"]["present"] is False` và `reviews["cross_model"]["present"] is False`
And `pipeline_telemetry["stages"]` trả về đầy đủ 6 stage mà không có bất kỳ ngoại lệ nào chưa được xử lý

Scenario: [CEHM-EC-02] [Tier A - Unit] Truy vấn review epic nghiêm ngặt từ chối fallback về các tệp review không liên quan ở thư mục gốc repo
Given một repository có tệp `.devtool/principal_review.md` và `.devtool/review_results.md` ở gốc repo của `"other_epic"`, trong khi `.devtool/epic/legacy_oct_epic/` không có tệp markdown review nào
When `parse_review_results(repo_path, active_epic="legacy_oct_epic", kind="cross-model", strict_epic=True)` được thực thi
Then `result["present"]` bằng `False` và `result["findings"]` bằng `[]` và `result["verdict"]` bằng `"UNKNOWN"`
And nội dung `review_results.md` ở gốc repo của `"other_epic"` không bao giờ bị rò rỉ sang `"legacy_oct_epic"`

Scenario: [CEHM-EC-03] [Tier C - Integration] Thay đổi dropdown PIC nội dòng trong hàng Roadmap cập nhật PIC mà không mở modal-epic-history
Given `tasks_dashboard.html` hiển thị với dòng `.roadmap-epic-row` có thể nhấp chứa thành phần điều khiển `renderPicSelect` `<select>` trong cột 5
When sự kiện click và change kích hoạt trên phần tử `<select>` đó để gán `@phungthuy8901`
Then lan truyền sự kiện không kích hoạt `openEpicHistoryModal` và `#modal-epic-history` vẫn ở trạng thái ẩn
```

---

## 3. Kịch bản Chuyển đổi Trạng thái (ST)

```gherkin
Scenario: [CEHM-ST-01] [Tier A - Unit] Dòng thời gian hợp nhất khử trùng lặp giao nhau giữa ring buffer và JSONL sự kiện, đồng thời dán nhãn tính toàn vẹn của luồng
Given một epic `"stream_epic"` có tệp `events_stream-epic_*.jsonl` đã lưu trữ chứa 22 mục (`e01`..`e22`) và bản chụp `heartbeat` lặp lại các mục đuôi `e15`..`e22`, bên cạnh một epic kế thừa riêng biệt `"snap_epic"` chỉ có tệp `.heartbeat.json` với 3 sự kiện
When `harvest_epic_history` tổng hợp `"stream_epic"` và `"snap_epic"`
Then `"stream_epic"` báo cáo `log_completeness == "full_stream"` và chứa đầy đủ 22 mục bước phân biệt mà không có mục `e15`..`e22` nào bị trùng lặp
And `"snap_epic"` báo cáo `log_completeness == "snapshot_and_ledger"` và giữ nguyên cả 3 mục heartbeat được sắp xếp theo mốc thời gian UTC

Scenario: [CEHM-ST-02] [Tier C - Integration] Modal đang mở kiểm tra epic In Progress ưu tiên task worktree và duy trì tab hiện hoạt qua chu kỳ làm mới thăm dò 5s
Given một `"in_prog_epic"` đang hoạt động có `.worktrees/in_prog_epic/.devtool/features/task_01_live.md` ở trạng thái `"in-progress"` trong khi `.devtool/epic/in_prog_epic/task_01_live.md` ở gốc ghi `"todo"`
When người dùng mở `#modal-epic-history` cho `"in_prog_epic"`, chuyển sang tab `"Cross-Model Review"`, và `pollDashboard()` thực thi một nhịp sau khi dữ liệu server cập nhật
Then `tasks[0]["status"]` phản ánh đúng `"in-progress"` từ nguồn worktree
And quá trình làm mới ngầm cập nhật telemetry trong khi vẫn giữ `"Cross-Model Review"` là tab được chọn hiện hoạt bên trong `#modal-epic-history`

Scenario: [CEHM-ST-03] [Tier C - Integration] Đóng modal-epic-history qua nút đóng, backdrop hoặc Escape khôi phục khóa cuộn và tách ngắt làm mới trực tiếp
Given `#modal-epic-history` hiện đang mở (`style.display === "flex"` và `document.body.style.overflow === "hidden"`)
When người dùng đóng nó qua nút `✕`, hoặc nhấp vào `.modal-backdrop`, hoặc kích hoạt `KeyboardEvent("keydown", { key: "Escape" })`
Then `#modal-epic-history` ẩn đi (`style.display === "none"`), `document.body.style.overflow` đặt lại thành `""`, và các nhịp `pollDashboard()` tiếp theo không fetch lại `/api/epic/history`
```

---

## 4. Kịch bản Kiến trúc và Đồng thời (AR)

```gherkin
Scenario: [CEHM-AR-01] [Tier A - Unit] Các caller update_epic_heartbeat đồng thời ghi các dòng hợp lệ không đan xen vào JSONL sự kiện dưới khóa giao dịch
Given 6 luồng worker dùng chung một git repo độc lập với các thư mục mirror `.devtool` ở gốc và worktree cho epic `"concurrent_epic"`
When mỗi luồng gọi `update_epic_heartbeat` 8 lần đồng thời với chuỗi `last_event` được gắn thẻ worker phân biệt
Then mọi dòng trong `.devtool/logs/events_concurrent-epic.jsonl` trên cả hai mirror đều phân tích thành công với `json.loads()`
And tất cả 48 sự kiện worker duy nhất đều được bảo toàn mà không bị cắt ngắn hay hỏng JSON từng phần

Scenario: [CEHM-AR-02] [Tier C - Integration] Các lần nhấp liên tiếp nhanh vào Epic A rồi Epic B sẽ loại bỏ phản hồi HTTP Epic A bị chậm qua token yêu cầu
Given `fetch()` giả lập trong đó `/api/epic/history?repo=R&epic=epic_a` phản hồi sau 120ms và `/api/epic/history?repo=R&epic=epic_b` phản hồi sau 10ms
When người dùng nhấp vào dòng `"epic_a"` và 5ms sau nhấp vào dòng `"epic_b"`
Then `#modal-epic-history` hiển thị siêu dữ liệu và task của `"epic_b"`
And khi promise của `"epic_a"` bị hoãn phân giải sau đó, nội dung của `"epic_a"` không ghi đè lên `"epic_b"` bên trong DOM của modal

Scenario: [CEHM-AR-03] [Tier C - Integration] Trình xử lý HTTP lịch sử từ chối các tham số truy vấn thiếu với mã 400 và từ chối duyệt thư mục với mã 400 hoặc 404
Given một `TasksServer` đang chạy gắn với `workspace_root` tạm thời độc lập
When các yêu cầu đến cho `/api/epic/history?repo=demo` (thiếu `epic`), `/api/epic/history?repo=../etc&epic=passwd`, và `/api/epic/history?repo=demo&epic=../../secret`
Then server phản hồi với payload lỗi JSON HTTP 400 hoặc 404 và không truy cập tệp nào ngoài `workspace_root`
```

---

## 5. Kịch bản Phục hồi Lỗi (FR)

```gherkin
Scenario: [CEHM-FR-01] [Tier A - Unit] Các dòng JSONL sai định dạng hoặc JSON evidence bị hỏng xử lý lỗi mềm trên từng bản ghi mà không hủy lịch sử epic
Given một epic `"corrupt_epic"` chứa một dòng sự kiện hợp lệ và một dòng JSON bị cắt ngắn `{bad` trong `.devtool/logs/events_corrupt-epic.jsonl`, cùng một tệp `evidence/task_01_broken.json` bị lỗi định dạng bên cạnh `task_01_broken.md`
When `harvest_epic_history(repo_path, "corrupt_epic")` được thực thi
Then các sự kiện dòng thời gian hợp lệ và siêu dữ liệu markdown `task_01_broken` vẫn được trả về sạch sẽ với `evidence: null` trên task bị hỏng và không có ngoại lệ nào phát sinh

Scenario: [CEHM-FR-02] [Tier C - Integration] Headless Chrome CDP đầu cuối xác minh toàn bộ quy trình điều tra modal, bộ lọc, thử lại lỗi và không có lỗi console
Given một `TasksServer` thực tế chạy trên các repository giả lập chứa `"done_epic"` (11 task kèm evidence, sổ cái gate, luồng events, và review Principal + Cross-Model 2 vòng), `"in_prog_epic"`, và `"backlog_epic"`
When Playwright / Chrome CDP kiểm thử tương tác nhấp Roadmap, phân lập chọn PIC, chip lọc danh mục Timeline (`All`, `Gates`, `Steps`, `Activity`, `Evidence`), các dòng xác minh task có thể mở rộng, chuyển tab & vòng review trực tiếp giữa Principal và Cross-Model, khôi phục banner Thử lại khi gặp HTTP 500, và đóng modal bằng phím `ESC`
Then mọi bảng điều khiển DOM được xác nhận đều hiển thị các giá trị lịch sử chính xác không rỗng trong khi Section II phía dưới vẫn giữ nguyên
And `cdp.consoleErrors` cùng `cdp.runtimeExceptions` đều là `[]`
```

<!-- sync-en-sha256: dbe52b6920e82f82 -->
