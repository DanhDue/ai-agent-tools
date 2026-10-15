# Kịch bản BDD: Các điểm vá tiếp theo của lifecycle

## Mục lục

- [1. Tổng quan và ma trận biên](#1-tổng-quan-và-ma-trận-biên)
- [2. UC-1 Script truy vết đọc coverage trung thực](#2-uc-1-script-truy-vết-đọc-coverage-trung-thực)
- [3. UC-2 Tiếp tục epic đọc đúng tín hiệu](#3-uc-2-tiếp-tục-epic-đọc-đúng-tín-hiệu)
- [4. UC-3 Đóng gói ghi đủ điều người nhận cần](#4-uc-3-đóng-gói-ghi-đủ-điều-người-nhận-cần)
- [5. UC-4 Văn bản skill nêu rõ các quy tắc](#5-uc-4-văn-bản-skill-nêu-rõ-các-quy-tắc)

## 1. Tổng quan và ma trận biên

Hợp đồng hành vi của epic `lifecycle_followups`. Mỗi scenario mang một định danh `LF-` và cần ít nhất
một automation integration test nằm dưới các thư mục integration test của HLD có nêu tên nó.

| Chiều | Scenario | Bảo đảm |
|-------|----------|---------|
| 1. Happy path | LF-HP-01 đến LF-HP-05 | Chú thích trong `Covers:` được chấp nhận; các quy tắc mới được nêu trong skill |
| 2. Edge case và biên | LF-EC-01, LF-EC-02 | File bị ignore không bao giờ được tính; thư mục ngoài git vẫn chạy được |
| 3. Chuyển trạng thái | LF-ST-01 đến LF-ST-06 | Tiếp tục và đóng gói đọc đúng trạng thái thật của branch, Status và commit |
| 4. Async và race condition | không có | Không có gì trong phạm vi chạy đồng thời; chiều này cố ý để trống |
| 5. Lỗi và khả năng chống chịu | LF-FR-01 đến LF-FR-04 | Mã hóa sai thì exit 2; remote không kết nối được và thiết kế chưa commit đều xuống cấp an toàn |

## 2. UC-1 Script truy vết đọc coverage trung thực

```gherkin
Tính năng: check_bdd_traceability.py đọc dòng Covers và file test một cách trung thực

  Kịch bản: [LF-HP-01] Dòng Covers có chú thích và dấu câu ở cuối được chấp nhận
    Cho một tài liệu scenario có PY-HP-01 và PY-EC-02
    Và một file task có dòng "Covers: PY-HP-01 (happy path), PY-EC-02."
    Khi chế độ plan chạy
    Thì cả hai định danh được giao cho task
    Và không định danh nào bị báo là lạ

  Kịch bản: [LF-HP-02] File test đã track và file test mới chưa bị ignore được tính là coverage
    Cho một thư mục integration test nằm trong repo git
    Và một test đã track nêu PY-HP-01 và một test chưa track, chưa bị ignore nêu PY-EC-02
    Khi chế độ tests chạy
    Thì cả hai định danh được phủ

  Kịch bản: [LF-EC-01] Báo cáo sinh ra bị gitignore không được tính là coverage
    Cho một thư mục integration test nằm trong repo git có ignore "playwright-report/"
    Và một file báo cáo bị ignore dưới thư mục đó nêu PY-HP-01 và PY-EC-02
    Khi chế độ tests chạy
    Thì không định danh nào được phủ và lần chạy exit 1

  Kịch bản: [LF-EC-02] Thư mục nằm ngoài mọi repo git quay về cách duyệt thư mục
    Cho một thư mục integration test không nằm trong repo git nào
    Và một file test dưới đó nêu PY-HP-01 và PY-EC-02
    Khi chế độ tests chạy
    Thì cả hai định danh được phủ

  Kịch bản: [LF-FR-01] File task không phải UTF-8 hợp lệ là lỗi sử dụng
    Cho một file task có các byte không phải UTF-8 hợp lệ
    Khi chế độ plan chạy
    Thì lần chạy exit 2 với "is not valid UTF-8" trên stderr

  Kịch bản: [LF-FR-02] Tài liệu scenario không phải UTF-8 hợp lệ là lỗi sử dụng
    Cho một tài liệu scenario có các byte không phải UTF-8 hợp lệ
    Khi chế độ plan chạy
    Thì lần chạy exit 2 với "is not valid UTF-8" trên stderr
```

## 3. UC-2 Tiếp tục epic đọc đúng tín hiệu

```gherkin
Tính năng: Entry-Point Detection và Resume Procedure đọc trạng thái thật

  Kịch bản: [LF-ST-01] Epic branch được push từ clone khác hiện ra trước mọi lần fetch
    Cho một remote chứa "epic/todo-export", được push từ một clone khác
    Và một repo local chưa fetch kể từ đó
    Khi tín hiệu branch trên remote của Entry-Point Detection chạy
    Thì "git branch -r" không cho thấy gì
    Và vòng lặp "git ls-remote --heads" in ra "refs/heads/epic/todo-export"

  Kịch bản: [LF-FR-03] Remote không kết nối được thì quay về ref remote-tracking
    Cho một repo có URL remote không kết nối được
    Khi vòng lặp "git ls-remote --heads" chạy
    Thì nó exit khác 0
    Và văn bản skill bảo agent nói rõ điều đó và quay về "git branch -r"

  Kịch bản: [LF-ST-04] Task đang review thì tiếp tục review, không implement lại
    Cho một epic bị ngắt có task_2 đang ở "review"
    Khi Resume Procedure vào Phase 2
    Thì nó vào lại tại Phase 2 bước 2 và review các thay đổi hiện có

  Kịch bản: [LF-ST-06] Commit bổ sung định danh có thể kèm trường trạng thái của task bị ngắt
    Cho một epic được tiếp tục cần bổ sung định danh BDD
    Và một task bị ngắt có file mang trạng thái "in-progress" chưa commit
    Khi phần bổ sung được commit theo đường dẫn
    Thì văn bản skill nói rõ trường trạng thái của task có thể đi kèm trong commit đó
```

## 4. UC-3 Đóng gói ghi đủ điều người nhận cần

```gherkin
Tính năng: Đóng gói ghi một bản bàn giao mà người nhận tin được

  Kịch bản: [LF-ST-02] Kiểm tra "đã cũ" bỏ qua các commit task của chính epic branch
    Cho một epic được đóng gói tại design commit S trên base branch
    Và một commit task trên epic branch có sửa mirror task của epic
    Khi kiểm tra của template chạy "git log S..<base_branch> -- .devtool/epic/<epic_dir>"
    Thì chỉ có commit "Package epic for handoff" được liệt kê

  Kịch bản: [LF-FR-04] Thiết kế chưa commit thì ghi "uncommitted" và bỏ qua kiểm tra
    Cho auto_commit là false khi epic được đóng gói
    Khi người nhận đọc handoff.md
    Thì design commit ghi "uncommitted"
    Và template bảo nó bỏ qua kiểm tra "đã cũ"

  Kịch bản: [LF-ST-03] Epic đang xếp hàng giữ thông tin hàng đợi khi được đóng gói
    Cho một epic có Status của overview là "Queued (backlog) — behind logging-refactor"
    Khi nó được đóng gói với Status "Packaged (queued behind logging-refactor)"
    Thì lệnh grep của bước đóng gói tìm thấy Status đó ở cả hai bản overview

  Kịch bản: [LF-HP-05] Placeholder số task của template được giải thích
    Cho bước 2 của quy trình đóng gói
    Khi agent điền template bàn giao
    Thì văn bản skill nói "<N>" là số task mà preflight đã in ra
```

## 5. UC-4 Văn bản skill nêu rõ các quy tắc

```gherkin
Tính năng: Các skill nêu rõ những quy tắc người nhận cần

  Kịch bản: [LF-HP-03] Thư mục integration mặc định của Python có cả tests/e2e
    Cho các giá trị mặc định Integration Test Roots của dev-designer
    Khi agent thiết kế một epic Python
    Thì mặc định nêu "tests/integration/" và "tests/e2e/"

  Kịch bản: [LF-HP-04] Cách phân tách giá trị của --roots và --ids được ghi rõ
    Cho kiểm tra truy vết ở Phase 4 của dev-implementation
    Khi agent chép dòng roots của HLD hoặc dòng Covers của task
    Thì skill nói cả hai tùy chọn nhận giá trị phân tách bằng dấu cách hoặc dấu phẩy

  Kịch bản: [LF-ST-05] Gate 4 nêu kiểm tra truy vết trong quy tắc chạy lại
    Cho một verdict Gate 4 đã hết hiệu lực vì có commit mới
    Khi đọc điều kiện candidate immutability của dev-lifecycle
    Thì nó yêu cầu chạy lại kiểm tra truy vết và epic quality run
```
