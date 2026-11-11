# Kịch Bản BDD Bảng Điều Khiển Tasks & Context Đa Repo

## Mục lục

- [Thông tin Meta](#thông-tin-meta)
- [Luồng Hoạt động Chuẩn](#luồng-hoạt-động-chuẩn)
- [Trường hợp Biên và Ngoại lệ](#trường-hợp-biên-và-ngoại-lệ)
- [Chuyển dịch Trạng thái](#chuyển-dịch-trạng-thái)
- [Bất đồng bộ và Xung đột Tiến trình](#bất-đồng-bộ-và-xung-đột-tiến-trình)
- [Xử lý Lỗi và Khả năng Phục hồi](#xử-lý-lỗi-và-khả-năng-phục-hồi)

## Thông tin Meta

- **Epic**: `check_tasks_dashboard`
- **Ngôn ngữ chuẩn**: Tiếng Việt (bản dịch từ tiếng Anh)
- **Tiền tố Kịch bản**: `CTD`
- **Thư mục Tự động hóa**: `tests/`
- **Quy tắc**: Mỗi mã kịch bản được gán cho đúng một task và phải xuất hiện trong một bài kiểm thử tự động.
- **Giả lập (Mocking)**: Các lệnh gọi tiến trình con (`git worktree`, `ag_run`) và duyệt thư mục được cô lập qua hệ thống tập tin giả lập và fixtures trong unit/integration tests.

## Luồng Hoạt động Chuẩn

```gherkin
Kịch bản: [CTD-HP-01] [Tier C - Tích hợp] Thu thập dữ liệu đa repo khám phá toàn bộ dự án, worktree và metadata giao diện

Cho một thư mục gốc chứa nhiều kho lưu trữ "ai-agent-tools", "lyrics-sync", "nexus", và "D3Nexus"
Và mỗi kho lưu trữ chứa .vscode/settings.json với window.title và workbench.colorCustomizations
Khi bộ thu thập quét thư mục gốc qua hàm harvest_dashboard_graph
Thì đồ thị trả về chứa các đối tượng metadata cho toàn bộ 4 kho lưu trữ
Và mỗi kho lưu trữ phản ánh chính xác màu chủ đạo, các worktree đang hoạt động và nhánh git
Và số lượng tasks Kanban cho done, in-progress, và todo khớp chính xác với trạng thái đĩa cứng

Kịch bản: [CTD-HP-02] [Tier C - Tích hợp] Động cơ FSM vòng đời tất định suy luận chính xác bước quyết định của con người

Cho một epic có Gate 4 PASS được ghi nhận trong .devtool/GATE_LEDGER.md
Và toàn bộ các tasks Kanban trong .devtool/features/ đều có trạng thái done
Và Gate 5 chưa được ghi nhận trong sổ cái
Khi động cơ vòng đời đánh giá hàm derive_lifecycle_state cho epic
Thì tên giai đoạn được suy luận là "Stage 3 Phase 4 (Review)"
Và bước hành động tiếp theo của con người chứa rõ ràng nội dung "Review Choice (Rule 5)"

Kịch bản: [CTD-HP-03] [Tier C - Tích hợp] Giao diện CLI dòng lệnh hiển thị bảng mã màu ANSI tổng quan đa repo

Cho nhiều kho lưu trữ đã được quét với tiến độ Kanban khác nhau
Khi lập trình viên chạy lệnh check_tasks.py với tham số "all"
Thì CLI in ra bảng mã màu ANSI định dạng chuẩn với huy hiệu màu nhận diện repo
Và nội dung hiển thị tên repo, nhánh hoặc worktree đang hoạt động, epic đang chạy và % tiến độ tasks
Và bước tiếp theo của con người cho từng epic đang chạy được hiển thị rõ ràng trong bảng

Kịch bản: [CTD-HP-04] [Tier C - Tích hợp] Daemon web server khởi động an toàn và phục vụ REST API

Cho cổng 8766 đang chưa bị chiếm dụng
Khi tasks_server.py khởi động với tham số "--daemon"
Thì tiến trình ghi mã định danh PID vào tệp /tmp/agy_tasks_server.pid
Và yêu cầu GET tới http://localhost:8766/api/tasks trả về HTTP 200 kèm dữ liệu đồ thị JSON hợp lệ
Và yêu cầu POST tới http://localhost:8766/api/shutdown dừng server an toàn và dọn dẹp tệp PID

Kịch bản: [CTD-HP-05] [Tier C - Tích hợp] Giao diện web tương tác hiển thị thẻ dự án và modal review

Cho web server đang chạy và phục vụ tệp tasks_dashboard.html
Khi người dùng truy cập dashboard trên trình duyệt
Thì giao diện hiển thị các thẻ Dark Mode cho toàn bộ các kho lưu trữ
Và nhấp vào nút review sẽ mở modal hiển thị commit SHA ứng viên, model reviewer và bảng triage 7 cột
Và nhấp vào nút mở IDE kích hoạt yêu cầu POST tới /api/launch/ide mà không sinh lỗi
```

## Trường hợp Biên và Ngoại lệ

```gherkin
Kịch bản: [CTD-EC-01] [Tier A - Đơn vị] Rơi về an toàn khi thiếu tập tin .vscode/settings.json

Cho một thư mục kho lưu trữ không có tập tin .vscode/settings.json
Khi scan_repo thu thập metadata cho kho lưu trữ này
Thì màu chủ đạo của repo tự động rơi về bảng màu chữ ký tất định
Và tiêu đề cửa sổ mặc định lấy theo tên thư mục của repo
Và quá trình quét hoàn tất thành công mà không gây lỗi FileNotFoundError

Kịch bản: [CTD-EC-02] [Tier A - Đơn vị] Xử lý an toàn các kho lưu trữ không có epic đang hoạt động

Cho một kho lưu trữ với working tree sạch và không có thư mục .devtool/epic/
Khi bộ thu thập trích xuất metadata cho kho lưu trữ này
Thì tên epic đang hoạt động được báo cáo là "None"
Và số lượng tasks Kanban là 0 trên 0 với trạng thái rảnh 100%
Và giai đoạn vòng đời được báo cáo là "Idle"

Kịch bản: [CTD-EC-03] [Tier A - Đơn vị] Phân tích worktree bẩn và commit detached HEAD

Cho một git worktree đang đứng ở trạng thái detached HEAD với các tập tin chưa được stage
Khi scan_repo thực thi phân tích worktree git
Thì metadata của worktree lưu trữ commit SHA dạng rút gọn
Và cờ dirty được đặt là true kèm số lượng tập tin bị chỉnh sửa

Kịch bản: [CTD-EC-04] [Tier A - Đơn vị] Terminal CLI tự động loại bỏ mã màu khi stdout bị chuyển hướng

Cho luồng xuất stdout bị chuyển hướng vào ống dẫn pipe hoặc tập tin không phải TTY
Khi check_tasks.py định dạng bảng hiển thị
Thì toàn bộ mã màu ANSI escape codes được tự động loại bỏ khỏi nội dung
Và nội dung giữ nguyên định dạng văn bản thuần căn lề chuẩn xác
```

## Chuyển dịch Trạng thái

```gherkin
Kịch bản: [CTD-ST-01] [Tier A - Đơn vị] FSM chuyển dịch từ Stage 2 Architecture sang Stage 2 Exit Handoff

Cho một epic có Gate 1 PASS và Gate 2 vừa được ghi nhận trong GATE_LEDGER.md
Và tập tin đóng gói handoff.md đã xuất hiện trong thư mục epic
Khi derive_lifecycle_state đánh giá kho lưu trữ
Thì trạng thái chuyển dịch sang "Stage 2 Exit (Handoff)"
Và bước tiếp theo gợi ý lập trình viên lựa chọn giữa Principal Review và Implementation

Kịch bản: [CTD-ST-02] [Tier A - Đơn vị] FSM chuyển dịch sang Stage 3 Phase 2 TDD khi tasks chuyển sang in-progress

Cho một epic có Gate 3 PASS được ghi nhận trong GATE_LEDGER.md
Và có ít nhất một task Kanban trong .devtool/features/ có trạng thái "in-progress"
Khi derive_lifecycle_state đánh giá kho lưu trữ
Thì trạng thái chuyển dịch sang "Stage 3 Phase 2 (TDD)"
Và bước tiếp theo hiển thị AI Programmer đang tự động triển khai tasks mà không cần can thiệp
```

## Bất đồng bộ và Xung đột Tiến trình

```gherkin
Kịch bản: [CTD-AR-01] [Tier C - Tích hợp] Daemon server tự động tăng cổng an toàn khi bị va chạm cổng

Cho cổng 8766 đã bị chiếm dụng bởi một tiến trình bên thứ ba không liên quan
Khi tasks_server.py thử khởi động dịch vụ dashboard
Thì server phát hiện cổng 8766 đang bị chiếm bởi một PID lạ
Và server tự động tăng cổng lắng nghe lên 8767 an toàn
Và server cập nhật tệp PID và in ra URL hoạt động trên cổng 8767
```

## Xử lý Lỗi và Khả năng Phục hồi

```gherkin
Kịch bản: [CTD-FR-01] [Tier A - Đơn vị] Thực thi Quy tắc 9 cho launcher ngăn ngừa nhiễm bẩn môi trường

Cho một yêu cầu khởi chạy CLI hoặc IDE nhắm tới profile Antigravity "hau"
Khi tasks_server.py xây dựng lệnh khởi chạy
Thì lệnh được gán tiền tố thực thi qua subshell cô lập "ag_run hau"
Và lệnh loại bỏ các biến môi trường VSCODE_GIT_IPC_HANDLE và ELECTRON_RUN_AS_NODE
Và lệnh không bao giờ chạy security default-keychain hay làm thay đổi ~/.zshrc toàn cục

Kịch bản: [CTD-FR-02] [Tier A - Đơn vị] Server phục hồi an toàn khi gặp tập tin PID cũ hoặc mồ côi

Cho một tệp PID cũ /tmp/agy_tasks_server.pid trỏ tới một tiến trình không còn sống
Khi tasks_server.py kiểm tra trạng thái daemon hoặc tiến hành khởi động
Thì verify_pid phát hiện tiến trình không còn tồn tại qua tín hiệu signal 0
Và tệp PID cũ được xóa an toàn và thay thế bằng PID của tiến trình mới
```
