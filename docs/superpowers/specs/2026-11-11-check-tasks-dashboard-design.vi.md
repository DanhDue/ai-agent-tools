# Thiết kế Cross-Repo Tasks & Context Dashboard

## Mục lục
- [Tổng quan](#tổng-quan)
- [Bối cảnh và Mục tiêu](#bối-cảnh-và-mục-tiêu)
- [Cảnh báo Shared Contract](#cảnh-báo-shared-contract)
- [Kiến trúc Hệ thống và Cấu trúc Tập tin](#kiến-trúc-hệ-thống-và-cấu-trúc-tập-tin)
- [Động cơ Thu thập Dữ liệu và Quét Đa Kho lưu trữ](#động-cơ-thu-thập-dữ-liệu-và-quét-đa-kho-lưu-trữ)
- [Web Server, REST API và Cơ chế Kích hoạt](#web-server-rest-api-và-cơ-chế-kích-hoạt)
- [Kiến trúc Giao diện UI và UX với Modal Dialogs](#kiến-trúc-giao-diện-ui-và-ux-với-modal-dialogs)
- [Giao diện Dòng lệnh CLI và Tích hợp Slash Command](#giao-diện-dòng-lệnh-cli-và-tích-hợp-slash-command)
- [Xử lý Lỗi, An toàn và Đồng thời](#xử-lý-lỗi-an-toàn-và-đồng-thời)
- [Kế hoạch Kiểm thử và Tiêu chí Nghiệm thu](#kế-hoạch-kiểm-thử-và-tiêu-chí-nghiệm-thu)

---

## Tổng quan

**Cross-Repo Tasks & Context Dashboard** (`check-tasks`) là công cụ dòng lệnh điều hành và bảng theo dõi tương tác thời gian thực chuẩn Dark Mode, được thiết kế để theo dõi và điều phối các epic phát triển song song trên toàn bộ các kho lưu trữ trong thư mục tổng `/Users/danhdueexoictif/AllProjects`.

Kế thừa kiến trúc hiệu năng cao của `check-quota`, `check-tasks` cung cấp cả bộ định dạng terminal CLI tốc độ cao và daemon Web Dashboard nền cục bộ (mặc định cổng `8766`). Hệ thống tự động thu thập và đồng bộ:
1. Giao diện màu sắc và tiêu đề cửa sổ trực tiếp từ `.vscode/settings.json` của từng dự án.
2. Danh sách Git worktrees và các epic đang triển khai song song giữa các repo.
3. Tiến độ thực tế và trạng thái Kanban chi tiết của từng task từ `.devtool/epic/` và `.devtool/features/`.
4. Bộ nhớ dự án hai tầng đã được kiểm chứng (Two-Tier Project Memory từ `/save-context` và `/resume-context`) gồm `.devtool/PROJECT_LEDGER.md` (Tầng 1) và `.devtool/assistant_state.md` / `activity_stream.log` (Tầng 2).
5. Bảng tổng hợp kết quả triage qua từng vòng (Rounds) và trạng thái Gate từ `/principal-review` và `/cross-model-review`.
6. Các nút kích hoạt native một chạm để mở Profile Antigravity CLI và Antigravity IDE trực tiếp tại thư mục worktree tương ứng.

## Bối cảnh và Mục tiêu

### Vấn đề Hiện tại
Trong hệ sinh thái đa kho lưu trữ nơi các lập trình viên đồng thời duy trì nhiều dự án (`ai-agent-tools`, `lyrics-sync`, `D3Nexus`, `nexus`, `digital_wallet`), mỗi repo thường xuyên triển khai nhiều epic song song bên trong các Git worktree độc lập (`.worktrees/<epic_slug>`).

Hiện tại:
- Lập trình viên thiếu một giao diện tập trung duy nhất để nắm bắt repo nào đang có worktree hoạt động, epic nào đang được xử lý, task cụ thể nào đang được lập trình (`status: "in_progress"`), và Gate nào đã được thông qua.
- Việc kiểm tra ngữ cảnh đòi hỏi phải duyệt thủ công qua các thư mục `.devtool/`, `PROJECT_LEDGER.md`, và `GATE_LEDGER.md` trên nhiều thư mục khác nhau.
- Kết quả đánh giá từ `/principal-review` (Giai đoạn 2) và `/cross-model-review` (Giai đoạn 3) nằm rải rác trong các tệp Markdown lớn (`principal_review.md`, `review_results.md`), khiến việc quét nhanh các lỗi Critical/Important chưa xử lý qua từng vòng trở nên cồng kềnh.
- Việc chuyển đổi giữa các terminal worktree và mở đúng profile cô lập của Antigravity CLI hoặc IDE đòi hỏi phải nhớ và gõ các lệnh shell thủ công (`ag_run <profile> ...`).

### Mục tiêu Cốt lõi
1. **Khả năng Quan sát Hợp nhất**: Tổng hợp và hiển thị toàn bộ các repo và các epic chạy song song trên một màn hình Dark Mode duy nhất.
2. **Đồng bộ Nhận diện Dự án Động**: Tự động áp dụng màu viền thẻ, hiệu ứng phát sáng (glow), và nhãn tiêu đề tương ứng với `workbench.colorCustomizations` và `window.title` khai báo trong `.vscode/settings.json` của mỗi repo.
3. **Bộ Kích hoạt Native Một Chạm**: Cung cấp các nút tinh gọn `[ 💻 Mở CLI ]` và `[ 🚀 Mở IDE ]` trên mỗi thẻ epic để mở terminal CLI hoặc IDE theo đúng profile và đúng worktree.
4. **Tương tác Modal Dialog (Không Chuyển Trang)**: Giữ người dùng luôn ở màn hình Overview chính. Các thao tác chi tiết được mở dưới dạng Dialog Pop-up không gián đoạn:
   - **Kanban Board Dialog**: Bảng Kanban 5 cột (`Backlog`, `To Do`, `In Progress`, `Review`, `Done`) chuẩn theo giao diện Antigravity gốc.
   - **Two-Tier Contexts Dialog**: Màn hình đối chiếu Tầng 1 (Bất biến vĩnh viễn) và Tầng 2 (Trạng thái hiện thời).
   - **Review Triage Dialogs**: Dialog chuyên dụng cho `/principal-review` và `/cross-model-review` hiển thị trọn vẹn metadata của vòng (Round, Candidate SHA, Reviewer, Thinking / Effort Level, Verdict) cùng bảng triage 7 cột với tags phân loại mức độ và highlight mã nguồn.
5. **Đồng bộ Giao diện Kép**: Hỗ trợ đầy đủ cả dòng lệnh terminal (`check-tasks`, `check-tasks all`) lẫn web daemon nền (`check-tasks --ui`, `check-tasks --stop`).

## Cảnh báo Shared Contract

Xác nhận không áp dụng `shared-contracts/`: `ai-agent-tools` là kho lưu trữ bộ công cụ chia sẻ và không liên kết trực tiếp với các hợp đồng chia sẻ domain. Tất cả các bước kiểm tra hợp đồng tại các repo vệ tinh/hub hạ nguồn đều được thực thi ở chế độ chỉ đọc trong quá trình thu thập trạng thái nhiệm vụ.

## Kiến trúc Hệ thống và Cấu trúc Tập tin

Tính năng tuân thủ cấu trúc phân tách rõ ràng được thiết lập bởi `check-quota`:

```text
ai-agent-tools/
├── bin/
│   └── check-tasks                              # Entrypoint thực thi toàn cục trong PATH
├── scripts/
│   └── agy_tasks.py                             # Engine trung tâm: Harvester + Terminal CLI + HTTP Daemon Server
└── skills/
    └── check-tasks/
        ├── SKILL.md                             # Tài liệu đặc tả skill và lệnh slash command
        └── resources/
            └── dashboard/
                └── tasks_dashboard.html         # Giao diện Single-Page Dark Mode với Tailwind CSS & Modal Dialogs
```

### Luồng Hoạt động Thành phần

```mermaid
flowchart TD
    CLI["Người dùng gọi check-tasks / check-tasks --ui"] --> AGY["scripts/agy_tasks.py"]
    AGY --> HARVEST["Động cơ Thu thập Dữ liệu (Harvester)"]
    
    subgraph DataSources["Nguồn Dữ liệu Đa Kho lưu trữ"]
        VS[".vscode/settings.json (Màu sắc & Title)"]
        WT[".worktrees/ & git worktree list"]
        DEV[".devtool/ (assistant_state, GATE_LEDGER)"]
        TASKS[".devtool/epic/*/task_*.md"]
        REV[".devtool/epic/*/(principal_review, review_results).md"]
    end
    
    HARVEST --> VS
    HARVEST --> WT
    HARVEST --> DEV
    HARVEST --> TASKS
    HARVEST --> REV
    
    HARVEST --> FORMAT["Bộ Định dạng CLI (Terminal Table)"]
    HARVEST --> API["HTTP API /api/tasks (Cổng 8766)"]
    API --> WEB["Giao diện Web Dashboard (tasks_dashboard.html)"]
    
    WEB --> LAUNCH["POST /api/launch"]
    LAUNCH --> OS_CLI["AppleScript: Terminal / iTerm (ag_run profile cli)"]
    LAUNCH --> OS_IDE["Tiến trình Con: ag_run profile <worktree>"]
```

## Động cơ Thu thập Dữ liệu và Quét Đa Kho lưu trữ

`scripts/agy_tasks.py` triển khai bộ quét tệp bất đồng bộ, phản hồi nhanh dưới 150ms:

1. **Khám phá Kho lưu trữ**:
   - Quét thư mục gốc `WORKSPACE_ROOT` (mặc định là `/Users/danhdueexoictif/AllProjects`).
   - Quét danh sách các repo đã biết: `ai-agent-tools`, `lyrics-sync`, `D3Nexus`, `nexus`, `digital_wallet`, cùng các repo con phát hiện động.
2. **Trích xuất Cấu hình Nhận diện (`.vscode/settings.json`)**:
   - Đọc `workbench.colorCustomizations["titleBar.activeBackground"]` (ví dụ: `#7f1d1d` cho lyrics-sync, `#065f46` cho D3Nexus, `#0d47a1` cho nexus, `#b45309` cho ai-agent-tools).
   - Đọc `window.title` để bóc tách profile tài khoản đang hoạt động (`@hau`, `@buivantrong8901`, `@danhdue`), tên Epic tiếng Việt, và giai đoạn hiện thời.
3. **Lập Bản đồ Worktrees và Epics**:
   - Chạy lệnh `git -C <repo> worktree list` và duyệt thư mục `<repo>/.worktrees/`.
   - Khớp nối các thư mục worktree với các epic trong `<repo>/.devtool/epic/<slug>/`.
4. **Nhận diện Task Hiện thời và Tiến độ Thực tế**:
   - Quét các tệp `task_*.md` trong `.devtool/features/` và `.devtool/epic/<slug>/`.
   - Phân tích frontmatter: `id`, `status` (`backlog`, `todo`, `in_progress`, `review`, `done`), `priority`, `order`, `labels`.
   - Xác định Task hiện tại: mục đầu tiên mang `status: "in_progress"` (hoặc `todo` đầu tiên nếu chưa bắt đầu).
   - Tính toán tỷ lệ hoàn thành: `done_count / total_count * 100`.
5. **Thu thập Sổ cái Gate và Bộ nhớ Ngữ cảnh**:
   - Phân tích `.devtool/GATE_LEDGER.md` để lấy bản ghi Gate mới nhất (Gate 1–5).
   - Đọc `.devtool/PROJECT_LEDGER.md` cho các bất biến và cột mốc Tầng 1 vĩnh viễn.
   - Đọc `.devtool/assistant_state.md` và `.devtool/activity_stream.log` cho trạng thái Tầng 2 hiện thời.
6. **Bộ phân tích Kết quả Đánh giá (Review Findings Parser)**:
   - Đọc `principal_review.md` và `review_results.md`.
   - Tách các phân đoạn vòng (`## Round 1`, `## Round 2`, `## Round 3`).
   - Trích xuất thông tin header: `Date`, `SHA`, `CLI`, `Model`, `Thinking`, `Verdict`.
   - Phân tích các hàng bảng Markdown thành các đối tượng có cấu trúc (`#`, `Severity`, `Location`, `Problem`, `Assessment`, `Evidence`, `Proposed action`).

## Web Server, REST API và Cơ chế Kích hoạt

Daemon server tích hợp sử dụng thư viện chuẩn `http.server` của Python trên cổng `8766`, ghi PID vào `/tmp/agy_tasks_server.pid`:

### Các Endpoints API
- `GET /`: Phục vụ tệp giao diện `tasks_dashboard.html`.
- `GET /api/tasks`: Trả về JSON hoàn chỉnh của toàn bộ repos, worktrees, active epics, tasks, màu sắc và reviews. Bộ nhớ đệm 3 giây giúp loại bỏ đọc đĩa dư thừa.
- `POST /api/launch`: Thực thi hành vi hệ thống dựa trên payload JSON:
  ```json
  {
    "action": "cli",
    "profile": "hau",
    "worktree": "/Users/danhdueexoictif/AllProjects/ai-agent-tools/.worktrees/autonomous_lifecycle_runner"
  }
  ```
  - **Hành động `cli`**: Mở cửa sổ Terminal hoặc iTerm2 độc lập qua AppleScript:
    ```bash
    osascript -e 'tell application "Terminal"
      do script "cd \"<worktree>\" && source ~/.zshrc && ag_run <profile> cli"
      activate
    end tell'
    ```
  - **Hành động `ide`**: Mở ứng dụng Electron Antigravity IDE cô lập:
    ```bash
    zsh -i -c "ag_run <profile> \"<worktree>\""
    ```

### Các Lệnh Quản trị Server
- `check-tasks --ui`: Khởi động daemon nền (nếu chưa chạy) và tự động mở trình duyệt mặc định.
- `check-tasks --ui -f`: Khởi chạy ở chế độ foreground phục vụ gỡ lỗi trực tiếp.
- `check-tasks --stop`: Dừng server daemon nền an toàn qua PID.
- `check-tasks --status`: Kiểm tra trạng thái cổng `8766` và tệp PID.

## Kiến trúc Giao diện UI và UX với Modal Dialogs

Giao diện Web (`tasks_dashboard.html`) được xây dựng dưới dạng ứng dụng đơn trang phản ứng nhanh với Tailwind CSS và hệ màu tối:

### 1. Màn hình Overview Chính
- **Thẻ Repository**: Viền và bóng đổ đồng bộ theo màu nhận diện dự án (`border-color`, `box-shadow`, `accent-badge`).
- **Danh sách Worktrees**: Hiển thị các worktree đang hoạt động kèm tên nhánh Git.
- **Vùng Nổi bật Task Hiện tại**: Làm nổi bật rõ ràng task đang ở trạng thái `in_progress`.
- **Thanh Tiến độ Phân đoạn**: Biểu thị trực quan tỷ lệ Done (xanh lá), In Progress (cam), và Todo (xám).
- **Các Nút Thao tác Nhanh**:
  - `[ 💻 Mở CLI ]`: Kích hoạt CLI theo profile tại worktree.
  - `[ 🚀 Mở IDE ]`: Kích hoạt Antigravity IDE tại worktree.
  - `[ 📊 Xem Kanban ]`: Mở Dialog Modal Bảng Kanban.
  - `[ 🧠 Xem Contexts ]`: Mở Dialog Modal Bộ nhớ 2 Tầng.
  - `[ 🛡️ Principal Review ]`: Mở Dialog Modal Kết quả Đánh giá Kiến trúc.
  - `[ 🔬 Cross-Model Review ]`: Mở Dialog Modal Kết quả Đánh giá Đa mô hình.

### 2. Dialog Modal Bảng Kanban
- Hiển thị cấu trúc 5 cột:
  - `● Backlog`
  - `● To Do`
  - `● In Progress`
  - `● Review`
  - `● Done`
- Thẻ task gồm: Tiêu đề task, Nhãn độ ưu tiên (`High`, `Med`, `Low`), Tài liệu tham chiếu, Nhãn nhánh (`⎇ <epic_slug>`), và các thẻ chuyên mục (`docs`, `reference`, `telemetry`).
- Các cột trống hiển thị dòng chữ `No features` mờ ở giữa.

### 3. Dialog Modal Bộ nhớ Hai Tầng (Two-Tier Context)
- Bố cục so sánh 2 cột:
  - **Cột Trái (Tầng 1 - Sổ cái Vĩnh viễn)**: Bất biến Hệ thống và Cột mốc hoàn thành từ `PROJECT_LEDGER.md`.
  - **Cột Phải (Tầng 2 - Trạng thái Hiện thời)**: Quyết định đã chốt, Trạng thái Gate Ledger, và Dòng nhật ký hoạt động gần nhất.

### 4. Dialog Modal Kết quả Review (Principal & Cross-Model)
- Tuân thủ phong cách tối giản thanh lịch:
  - **Header Metadata**:
    - `Candidate SHA`: Mã commit đầy đủ trong thẻ code.
    - `Reviewer`: Tên người đánh giá và model (ví dụ: `Claude (model sonnet)`).
    - `Effort / Thinking Level`: `High`.
    - `Verdict`: Kết luận và tổng hợp số lượng lỗi (ví dụ: `CHANGES REQUIRED (3 Critical, 1 Important findings)`).
  - **Bộ Chọn Vòng (Round Selector)**: Chuyển đổi giữa `Round 1`, `Round 2`, và `Round 3`.
  - **Bảng Triage 7 Cột**:
    - `#`: Số thứ tự lỗi.
    - `Severity`: Thẻ tag màu sắc theo mức độ (`Critical` màu đỏ, `Important` màu cam, `Minor` màu xanh).
    - `Location`: Đường dẫn tệp monospace kèm số dòng in đậm.
    - `Problem`: Mô tả vấn đề kèm highlight các từ khóa mã nguồn.
    - `Assessment`: Đánh giá (`Valid`, `Debatable`, `False Positive`).
    - `Evidence`: Khung code monospace chứa kết quả kiểm chứng động.
    - `Proposed action`: Đề xuất sửa đổi với tiền tố `fix:` và thẻ commit `✓ fixed in <sha>`.

## Giao diện Dòng lệnh CLI và Tích hợp Slash Command

### Cách Sử dụng CLI
```bash
# Hiển thị tóm tắt cho repo hiện tại hoặc worktree đang đứng
check-tasks

# Hiển thị bảng tổng hợp toàn bộ các repo trong /AllProjects
check-tasks all

# Hiển thị chi tiết cho một repo cụ thể
check-tasks lyrics-sync

# Khởi động web dashboard chạy ngầm
check-tasks --ui

# Dừng web dashboard server đang chạy
check-tasks --stop

# Kiểm tra trạng thái server daemon
check-tasks --status
```

### Tích hợp Slash Command `/check-tasks`
Khi được kích hoạt trong khung chat, Antigravity sẽ nhúng:
```html
<agent-embed src="file:///Users/danhdueexoictif/AllProjects/ai-agent-tools/skills/check-tasks/resources/dashboard/tasks_dashboard.html"></agent-embed>
```
Kèm theo thẻ tóm tắt dòng lệnh ngắn gọn về các worktree đang chạy, epic dở dang, và trạng thái Gate gần nhất.

## Xử lý Lỗi, An toàn và Đồng thời

1. **An toàn Biên giới Hệ điều hành Đa Profile (Rule 9)**:
   - Việc mở CLI hoặc IDE tuyệt đối diễn ra trong subshell cục bộ (`ag_run <profile>`), không thay đổi Keychain mặc định của OS hay biến `$HOME` toàn cục.
2. **Thoái lui Mượt mà khi Thiếu Tệp**:
   - Nếu thiếu `.vscode/settings.json`, tự động dùng màu mặc định chuẩn (`#7f1d1d`, `#065f46`, `#0d47a1`, `#b45309`) hoặc bảng màu băm định trước.
   - Nếu chưa có `review_results.md` hoặc `principal_review.md`, nút tương ứng sẽ hiển thị trạng thái vô hiệu hóa `No reviews yet`.
   - Nếu không có worktree nào, thẻ hiển thị `Clean working tree (no active worktree)`.
3. **An toàn Tránh Xung đột Cổng**:
   - Nếu cổng `8766` đã có tiến trình khác chiếm dụng, script kiểm tra xem có phải của `check-tasks` không. Nếu thuộc ứng dụng khác, tự động tăng an toàn lên `8767`.
4. **Bảo vệ Tệp PID**:
   - Lưu tại `/tmp/agy_tasks_server.pid`. Luôn kiểm tra sự tồn tại của tiến trình bằng `kill -0 <pid>` trước khi phát lệnh dừng hoặc khởi động lại.

## Kế hoạch Kiểm thử và Tiêu chí Nghiệm thu

| ID | Chuyên mục | Bước Kiểm thử | Tiêu chí Thành công |
|---|---|---|---|
| **V1** | Quét dữ liệu | Chạy `scripts/agy_tasks.py --scan` trên `/Users/danhdueexoictif/AllProjects` | Phát hiện chính xác toàn bộ repos, worktrees, active epics và mã màu `.vscode/settings.json` không gặp lỗi |
| **V2** | Terminal CLI | Chạy `check-tasks all` trong terminal | Hiển thị bảng ANSI màu sắc liệt kê repos, epics, tasks hiện tại và Gates |
| **V3** | Vòng đời Daemon | Chạy `check-tasks --ui`, kiểm tra `curl http://localhost:8766/api/tasks`, chạy `check-tasks --stop` | Server khởi động, API trả về JSON hợp lệ trong < 200ms, server dừng sạch sẽ |
| **V4** | Kanban Modal | Mở Web UI, click `[ 📊 Xem Kanban ]` | Dialog modal mở tức thì, hiển thị đủ 5 cột với thẻ task thực tế khớp ảnh mẫu |
| **V5** | Context Modal | Click `[ 🧠 Xem Contexts ]` | Dialog modal hiển thị Sổ cái Tầng 1 và Trạng thái Tầng 2 |
| **V6** | Review Modal | Click `[ 🔬 Cross-Model Review ]` trên `ai-agent-tools` | Dialog hiển thị Bộ chọn Round, Candidate SHA, Reviewer, Thinking Level, Verdict, và bảng triage 7 cột với tags độ nghiêm trọng |
| **V7** | Bộ Kích hoạt | Click `[ 💻 Mở CLI ]` và `[ 🚀 Mở IDE ]` | CLI mở tab terminal mới với môi trường profile; IDE mở cửa sổ Antigravity trỏ đúng worktree |
| **V8** | Document QA | Chạy `check_document.py` kiểm tra cặp tài liệu song ngữ | Đạt kết quả PASS không có lỗi lint, lỗi liên kết ToC hay lệch cấu trúc song ngữ |
