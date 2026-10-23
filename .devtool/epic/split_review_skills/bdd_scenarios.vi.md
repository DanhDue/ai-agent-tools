# Kịch Bản Phát Triển Hướng Hành Vi: Tách Hai Kỹ Năng Đánh Giá

## Mục lục

- [Use Case 1: Principal Review Trong Vòng Đời và Tùy Biến](#use-case-1-principal-review-trong-vòng-đời-và-tùy-biến)
- [Use Case 2: Cross-Model Review Trong Vòng Đời và Tùy Biến](#use-case-2-cross-model-review-trong-vòng-đời-và-tùy-biến)
- [Use Case 3: Chuyển Đổi Trạng Thái và Bất Biến Của Gate](#use-case-3-chuyển-đổi-trạng-thái-và-bất-biến-của-gate)
- [Use Case 4: Khả Năng Phục Hồi Bất Đồng Bộ và Dự Phòng Công Cụ](#use-case-4-khả-năng-phục-hồi-bất-đồng-bộ-và-dự-phòng-công-cụ)
- [Use Case 5: Xử Lý Thất Bại và Cổng Tiền Điều Kiện](#use-case-5-xử-lý-thất-bại-và-cổng-tiền-điều-kiện)
- [Use Case 6: Tài Liệu Vòng Đời và Đảm Bảo Hợp Đồng](#use-case-6-tài-liệu-vòng-đời-và-đảm-bảo-hợp-đồng)

## Use Case 1: Principal Review Trong Vòng Đời và Tùy Biến

### Đường dẫn chuẩn (Happy Paths)

```gherkin
Scenario: [SRS-HP-01] [Tier C - Integration] In-lifecycle Principal Review invocation from dev-lifecycle
  Given một epic "sample_epic" đã vượt qua Gate 2 và tiền kiểm tra đóng gói thành công
  When nhà phát triển chọn phương án 2 "Principal Review" với CLI "codex"
  Then skill "d3nexus:principal-review" được kích hoạt
  And lệnh "run_external_review.py run --kind principal" thực thi đối chiếu các tài liệu epic
  And vòng 1 được ghi nhận vào ".devtool/epic/sample_epic/principal_review.md"

Scenario: [SRS-HP-02] [Tier C - Integration] Ad-hoc Principal Review invocation on standalone design document
  Given một tài liệu thiết kế độc lập "docs/rfc/feature-architecture.md" tồn tại
  When nhà phát triển gọi "/principal-review docs/rfc/feature-architecture.md" với base "main" và CLI "claude"
  Then skill "principal-review" xác thực cấu trúc tài liệu
  And kích hoạt reviewer bên ngoài với nội dung tài liệu và ngữ cảnh codebase
  And xuất ra bảng triage đánh giá trực quan mà không yêu cầu thư mục epic
```

### Các trường hợp biên và ngoại lệ (Edge Cases and Boundaries)

```gherkin
Scenario: [SRS-EC-01] [Tier A - Unit] Ad-hoc review invocation with non-existent document
  Given một đường dẫn mục tiêu được yêu cầu "docs/rfc/missing-doc.md" không tồn tại trên đĩa
  When người dùng chạy "/principal-review docs/rfc/missing-doc.md"
  Then skill lập tức từ chối với thông báo lỗi nêu rõ đường dẫn bị thiếu
  And không có tiến trình CLI bên ngoài nào được khởi tạo

Scenario: [SRS-EC-04] [Tier A - Unit] Standalone document without required structure
  Given một tài liệu độc lập "docs/rfc/broken.md" chứa lỗi cú pháp hoặc thiếu các tiêu đề bắt buộc
  When tiền kiểm tra của principal review độc lập thực thi
  Then bộ kiểm tra báo cáo lỗi định dạng
  And nhắc tác giả khắc phục cấu trúc trước khi chạy đánh giá mô hình bên ngoài
```

## Use Case 2: Cross-Model Review Trong Vòng Đời và Tùy Biến

### Đường dẫn chuẩn (Happy Paths)

```gherkin
Scenario: [SRS-HP-03] [Tier C - Integration] In-lifecycle Cross-Model Review invocation from dev-implementation
  Given tất cả các task trong epic "sample_epic" được đánh dấu done và Gate 4 trả về PASS
  When nhà phát triển chọn phương án 2 "Cross-model review" với CLI "claude"
  Then skill "d3nexus:cross-model-review" được kích hoạt
  And lệnh "run_external_review.py run --kind epic" đánh giá các commit task và diff đối chiếu với base
  And vòng 1 được ghi nhận vào ".devtool/epic/sample_epic/review_results.md"

Scenario: [SRS-HP-04] [Tier C - Integration] Ad-hoc Cross-Model Review invocation on git branch
  Given một feature branch "feature/payment-flow" có các commit rẽ nhánh từ "main"
  When nhà phát triển gọi "/cross-model-review --base main"
  Then skill "cross-model-review" tính toán phạm vi commit và diff đối chiếu với "main"
  And thực thi đánh giá bằng mô hình bên ngoài trên diff
  And xuất ra báo cáo triage định dạng chuẩn cùng các đề xuất sửa chữa

Scenario: [SRS-HP-05] [Tier C - Integration] Local model review invocation through cross-model-review skill
  Given server Ollama cục bộ đang chạy và hiển thị mô hình "qwen2.5-coder:32b"
  When nhà phát triển chọn phương án 3 "Local model review" chỉ định mô hình "qwen2.5-coder:32b"
  Then skill "cross-model-review" gọi runner với cờ "--cli ollama --model qwen2.5-coder:32b"
  And ghi nhận vòng đánh giá vào "review_results.md"
```

### Các trường hợp biên và ngoại lệ (Edge Cases and Boundaries)

```gherkin
Scenario: [SRS-EC-02] [Tier A - Unit] Cross-model review refuses execution on dirty working tree
  Given working tree của kho chứa có các thay đổi chưa stage hoặc chưa track
  When "cross-model-review" bắt đầu thực thi runner
  Then runner từ chối thực thi với thông báo lỗi tiền điều kiện yêu cầu cây làm việc sạch
  And nhắc người dùng commit hoặc stash các thay đổi trước khi review

Scenario: [SRS-EC-03] [Tier A - Unit] Missing external CLI tool triggers actionable guidance
  Given cả hai binary "claude" và "codex" đều không được cài đặt trên PATH người dùng
  When một vòng review bên ngoài được yêu cầu
  Then skill phát hiện thiếu binary CLI
  And in hướng dẫn cài đặt cụ thể cho Claude Code CLI và OpenAI Codex CLI mà không làm dừng đột ngột hệ thống
```

## Use Case 3: Chuyển Đổi Trạng Thái và Bất Biến Của Gate

### Chuyển đổi trạng thái (State Transitions)

```gherkin
Scenario: [SRS-ST-01] [Tier C - Integration] Principal Review revision loop enforces commit ordering
  Given vòng 1 của principal review báo cáo các phát hiện mức Important
  When nhà phát triển phê duyệt các chỉnh sửa tài liệu
  Then các tài liệu chỉnh sửa được commit trước với tiêu đề "[EPIC] Revise epic after Principal Review round 1"
  And các quyết định tham chiếu SHA của commit chỉnh sửa được ghi nhận vào "principal_review.md"
  And quy trình đóng gói epic chạy lại để làm mới metadata của handoff

Scenario: [SRS-ST-02] [Tier C - Integration] Cross-Model Review fix loop enforces Gate 4 re-verification
  Given vòng 1 của cross-model review báo cáo các phát hiện mức Important
  When các bản sửa code được commit và quyết định được ghi nhận trong "review_results.md"
  Then bộ kiểm tra máy Gate 4 phải được chạy lại toàn bộ trên commit SHA ứng viên mới
  And Lựa chọn Review chỉ được hiển thị lại sau khi Gate 4 trả về PASS

Scenario: [SRS-ST-03] [Tier A - Unit] Gate 3 execution order enforces zero undecided principal findings
  Given tệp ".devtool/epic/sample_epic/principal_review.md" chứa các phát hiện chặn chưa được quyết định
  When "dev-implementation" khởi chạy xác thực thứ tự thực thi Gate 3
  Then kiểm tra Gate 3 thoát với mã 1 và từ chối chuyển sang tạo worktree

Scenario: [SRS-ST-04] [Tier A - Unit] Gate 5 Kanban sign-off enforces zero undecided code findings
  Given tệp ".devtool/epic/sample_epic/review_results.md" chứa các phát hiện chặn chưa được quyết định
  When nhà phát triển chọn "Finish" tại Review Choice
  Then bước tiền kiểm tra finish thoát với mã 1
  And yêu cầu nhà phát triển đưa ra quyết định cho mọi phát hiện trước khi tiến vào Gate 5
```

## Use Case 4: Khả Năng Phục Hồi Bất Đồng Bộ và Dự Phòng Công Cụ

### Bất đồng bộ và Phục hồi (Async and Resilience)

```gherkin
Scenario: [SRS-AR-01] [Tier A - Unit] Streaming timeout handling during model execution
  Given một lần gọi CLI bên ngoài vượt quá thời gian timeout tiến trình đã cấu hình
  When sự kiện timeout được kích hoạt
  Then runner chấm dứt tiến trình con một cách an toàn
  And báo cáo phát hiện timeout mang tính mô tả mà không để lại tiến trình nền mồ côi

Scenario: [SRS-AR-02] [Tier A - Unit] Sequential round numbering prevents collision
  Given một epic đã có vòng 1 được ghi nhận trong log review
  When một vòng review tiếp theo hoàn thành
  Then vòng mới được gán số thứ tự nghiêm ngặt là vòng 2
  And lịch sử cùng các quyết định của các vòng trước được bảo toàn bất biến
```

## Use Case 5: Xử Lý Thất Bại và Cổng Tiền Điều Kiện

### Thất bại và Phục hồi (Failures and Resilience)

```gherkin
Scenario: [SRS-FR-01] [Tier C - Integration] Principal review runner halts on failed readiness preflight
  Given thư mục epic có liên kết tài liệu bị gãy hoặc thiếu cặp tài liệu song ngữ
  When "principal-review" thực thi "check_epic_readiness.py"
  Then bước tiền kiểm tra sẵn sàng thất bại với mã thoát khác 0
  And in biểu ngữ tiền điều kiện mà không gọi mô hình CLI bên ngoài

Scenario: [SRS-FR-02] [Tier A - Unit] Triage parser isolates malformed model responses
  Given một reviewer bên ngoài xuất ra văn bản thiếu các điểm mốc đánh giá hoặc mức độ nghiêm trọng hợp lệ
  When "run_external_review.py triage" xử lý kết quả đầu ra của vòng review
  Then bộ phân tích cách ly lỗi phân tích cú pháp thành một cảnh báo rõ ràng
  And nhắc nhà phát triển kiểm tra log thô mà không làm đổ vỡ quy trình vòng đời
```

## Use Case 6: Tài Liệu Vòng Đời và Đảm Bảo Hợp Đồng

### Đường dẫn chuẩn (Happy Paths)

```gherkin
Scenario: [SRS-HP-06] [Tier C - Integration] Document contracts enforce new review skills exposure
  Given thư mục skill của kho chứa chứa "principal-review" và "cross-model-review"
  When "test_lifecycle_document_contract.py" kiểm tra tất cả các producer vòng đời
  Then cả hai skills hiển thị các từ khóa hợp đồng và YAML frontmatter mong đợi
  And "scripts/verify.sh" hoàn thành với 0 lỗi hồi quy hợp đồng

Scenario: [SRS-HP-07] [Tier C - Integration] Lifecycle diagrams reflect two standalone review stages
  Given tài liệu vòng đời dành cho con người "docs/lifecycles.en.md" và "docs/lifecycles.vi.md"
  When các sơ đồ flowchart hiện đại được kiểm tra
  Then Giai đoạn 2 hiển thị việc chuyển giao rõ ràng sang "principal-review"
  And Giai đoạn 3 hiển thị việc chuyển giao rõ ràng sang "cross-model-review"
```
