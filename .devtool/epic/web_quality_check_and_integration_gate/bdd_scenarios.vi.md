# Kịch bản Kiểm thử BDD: Web Quality Check Provider và Integration Quality Gate

## Mục lục

- [Mục lục](#mục-lục)
- [Chiều 1: Happy Paths](#chiều-1-happy-paths)
- [Chiều 2: Edge Cases và Biên Giới hạn](#chiều-2-edge-cases-và-biên-giới-hạn)
- [Chiều 3: Chuyển đổi Trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và Đồng thời](#chiều-4-bất-đồng-bộ-và-đồng-thời)
- [Chiều 5: Thất bại và Khả năng Phục hồi](#chiều-5-thất-bại-và-khả-năng-phục-hồi)

## Chiều 1: Happy Paths

```gherkin
Scenario: [WQG-HP-01] [Tier C - Integration] Web quality provider certification on Astro TypeScript repository
  Given một kho lưu trữ chứa dự án Astro có file .agents/quality/web-quality.json
  When Gate 4 gọi d3nexus:web-quality-check với profile epic
  Then provider thực thi type_check, lint, và test_e2e qua Playwright headless
  And xuất ra Tài liệu Kết quả Provider hợp lệ với trạng thái PASS gắn với commit SHA

Scenario: [WQG-HP-02] [Tier C - Integration] Vanilla JavaScript type-checking via JSDoc configuration
  Given một kho lưu trữ chứa các file Vanilla JavaScript trong preview/static/
  And file jsconfig.json được cấu hình "checkJs": true
  When web-quality-check thực thi capability type_check
  Then trình biên dịch TypeScript kiểm tra toàn bộ file JavaScript mà không phát sinh lỗi
  And vượt qua mà không yêu cầu đổi tên bất kỳ file nào sang .ts

Scenario: [WQG-HP-03] [Tier C - Integration] Playwright headless execution with wiremock and Zero-Console-Error
  Given một trang web Astro có các controller tương tác phía client
  And Playwright được cấu hình với fixture bộ chặn Zero-Console-Error
  When bài test giả lập điều hướng, click nút của người dùng và mock mạng qua page.route()
  Then trang web render mà không phát sinh bất kỳ lỗi console.error hay ngoại lệ chưa xử lý nào
  And bộ test hoàn thành thành công

Scenario: [WQG-HP-04] [Tier A - Unit] Automated generation of 3-5 step manual smoke checklist
  Given tất cả các task trong một epic đạt trạng thái done và Phase 4 thực thi
  When bộ sinh checklist phân tích các kịch bản BDD Happy Path chính
  Then nó xuất ra file .devtool/epic/<epic_dir>/manual_smoke_checklist.md trước khi Gate 4 xác thực
  And checklist chứa từ 3 đến 5 bước kiểm tra thực tế kèm Mục tiêu (URL hoặc Lệnh CLI), Hành động và Kết quả trực quan quan sát được
```

## Chiều 2: Edge Cases và Biên Giới hạn

```gherkin
Scenario: [WQG-EC-01] [Tier A - Unit] Web quality manifest with empty or optional capabilities
  Given một kho lưu trữ có .agents/quality/web-quality.json chỉ cấu hình type_check và test_unit
  When web-quality-check được gọi với profile pr
  Then nó chỉ phân giải các capability đã được khai báo
  And chứng thực thành công kho lưu trữ mà không báo lỗi về các capability tùy chọn bị thiếu

Scenario: [WQG-EC-02] [Tier A - Unit] Benign console warnings filtered by allowlist
  Given một trang web phát ra cảnh báo deprecation đã biết từ thư viện bên thứ ba
  And một biểu thức chính quy allowlist được cấu hình trong .agents/quality/web-quality.json
  When bài test Playwright thực thi
  Then bộ chặn Zero-Console-Error lọc bỏ các cảnh báo khớp trong danh sách cho phép
  And không đánh trượt nhầm bộ test
```

## Chiều 3: Chuyển đổi Trạng thái

```gherkin
Scenario: [WQG-ST-01] [Tier A - Unit] Transition from BLOCKED to PASS upon fixing invalid configuration
  Given một kho lưu trữ có file .agents/quality/web-quality.json sai cú pháp
  When validate_web_quality.py đánh giá manifest
  Then nó báo cáo trạng thái BLOCKED kèm các phát hiện lỗi cấu hình
  And khi lập trình viên sửa đúng schema JSON
  Then validator chuyển đổi trạng thái sang PASS

Scenario: [WQG-ST-02] [Tier C - Integration] Task status progression under Anti-Rationalization audit
  Given một tác vụ Kanban bao phủ kịch bản Tier C [WQG-HP-01]
  When bộ chạy xác thực đánh giá việc hoàn tất task khi thiếu bằng chứng tích hợp Tier C hoặc chỉ có mock đơn vị
  Then task_contract.py và script đồng bộ trạng thái từ chối chuyển sang done do vi phạm điều kiện 6
  And khi bằng chứng thực thi test tích hợp Playwright headless thật được cung cấp trong kết quả xác thực
  Then tác vụ chuyển đổi suôn sẻ sang trạng thái done
```

## Chiều 4: Bất đồng bộ và Đồng thời

```gherkin
Scenario: [WQG-AR-01] [Tier C - Integration] Concurrent multi-provider fan-out in Gate 4
  Given một kho lưu trữ đa nền tảng (D3Nexus) với 2 provider rust-core và learning-web
  When Gate 4 quality_check thực thi profile epic
  Then cả hai provider chạy đồng thời mà không can thiệp vào output của nhau
  And Gate 4 tổng hợp phán quyết cuối cùng theo độ ưu tiên FAIL > BLOCKED > PASS

Scenario: [WQG-AR-02] [Tier C - Integration] Playwright webServer lifecycle management
  Given Playwright được cấu hình với lệnh webServer là npm run preview
  When Playwright khởi động test runner
  Then nó chờ đợi port healthcheck của server trước khi phát lệnh chạy trình duyệt
  And dọn dẹp sạch tiến trình webServer khi hoàn tất
```

## Chiều 5: Thất bại và Khả năng Phục hồi

```gherkin
Scenario: [WQG-FR-01] [Tier C - Integration] Immediate test failure on uncaught JavaScript console error
  Given một web component có lỗi runtime phát ra console.error("Uncaught TypeError")
  When Playwright thực thi bộ test
  Then bộ chặn Zero-Console-Error lập tức dừng lại và đánh trượt bài test
  And ghi lại toàn bộ thông báo console, stack trace và URL mục tiêu làm bằng chứng

Scenario: [WQG-FR-02] [Tier A - Unit] Missing node_modules or binary execution blocker
  Given một môi trường thiếu binary playwright hoặc astro trong PATH
  When web-quality-check cố gắng spawn tiến trình
  Then nó bắt lỗi spawn thất bại và xuất ra trạng thái BLOCKED kèm hướng dẫn khắc phục cụ thể
```
