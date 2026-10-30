# Kịch Bản BDD Cho Sync Shared Contracts

## Mục lục

- [Chiều 1: Tuyến thực thi thành công](#chiều-1-tuyến-thực-thi-thành-công)
- [Chiều 2: Trường hợp biên và ranh giới](#chiều-2-trường-hợp-biên-và-ranh-giới)
- [Chiều 3: Chuyển đổi trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và đồng thời đa repo](#chiều-4-bất-đồng-bộ-và-đồng-thời-đa-repo)
- [Chiều 5: Lỗi và khả năng phục hồi lưu trữ](#chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

## Chiều 1: Tuyến thực thi thành công

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Phân tích cú pháp Contract có cấu trúc và kết xuất báo cáo Requirements Brief
  Given một Hub repository đã khởi tạo với domain lyrics-sync chứa api_contract.md, architecture_and_flow.md, và gaps_and_rfcs.md
  When kỹ sư thực thi lệnh sync_contracts.py brief --domain lyrics-sync
  Then bộ phân tích trích xuất đúng phiên bản "1.0.0", 4 endpoints chuẩn, các authentication headers, các khóa JSON payload, 7 bước pipeline, và RFC-001
  And báo cáo Markdown đầu ra chứa đầy đủ các phần Topology Metadata, API and Schema Requirements, Architecture Invariants, Actionable RFCs, và Lifecycle Execution Rules
  And lệnh kết thúc với exit code 0

Scenario: [SYC-HP-02] [Tier C - Integration] Đồng bộ Satellite toàn trình và vượt qua kiểm tra Strict
  Given một Satellite repository được liên kết qua relative symlink shared-contracts tới ../Hub/shared-contracts/lyrics-sync
  When kỹ sư thực thi sync_contracts.py ack sau đó chạy sync_contracts.py check --strict
  Then file .agents/contract_sync.json được tạo trong Satellite repository với mode "satellite" và domain "lyrics-sync"
  And các mã băm sha256 được ghi nhận khớp với cả 3 file canonical trong Hub
  And lệnh sync_contracts.py check --strict xuất trạng thái "IN_SYNC" và kết thúc với exit code 0

Scenario: [SYC-HP-03] [Tier C - Integration] Xác thực định nghĩa Skill và thực thi bộ kiểm tra phát hành
  Given thư mục skill sync-shared-contracts đã hoàn thiện và được đăng ký trong scripts/verify.sh
  When kỹ sư chạy bộ kiểm tra xác minh cho sync-shared-contracts
  Then file skills/sync-shared-contracts/SKILL.md vượt qua kiểm tra frontmatter và liên kết nội bộ
  And toàn bộ các bài kiểm thử đơn vị và tích hợp trong test_sync_contracts.py đều đạt với exit code 0
```

## Chiều 2: Trường hợp biên và ranh giới

```gherkin
Scenario: [SYC-EC-01] [Tier A - Unit] Phát hiện trạng thái Initial Sync khi chưa có file Watermark
  Given một Satellite repository hợp lệ nhưng chưa có file .agents/contract_sync.json
  When kỹ sư thực thi sync_contracts.py check --json
  Then báo cáo JSON xác định trạng thái của domain là "INITIAL_SYNC"
  And liệt kê cả 3 file hợp đồng canonical là các thay đổi nền tảng cần đồng bộ
  And lệnh kết thúc với exit code 0 khi không truyền --strict và exit code 1 khi truyền --strict

Scenario: [SYC-EC-02] [Tier A - Unit] Bộ quét Heuristic khớp các route có tham số và trường DTO dạng CamelCase
  Given một target repository chứa file mã nguồn src/worker_client.ts có đường dẫn "/api/v1/lyrics-sync/tasks" cùng "/progress" và trường "leaseDurationMs"
  When bộ quét heuristic đánh giá các endpoints "/api/v1/lyrics-sync/tasks/{id}/progress" và "/api/v1/lyrics-sync/status" cùng khóa payload "lease_duration_ms"
  Then endpoint "/api/v1/lyrics-sync/tasks/{id}/progress" và khóa "lease_duration_ms" được phân loại là "FOUND_IN_CODE"
  And endpoint chưa được hiện thực hóa "/api/v1/lyrics-sync/status" được phân loại là "MISSING_IN_CODE"

Scenario: [SYC-EC-03] [Tier A - Unit] Tự động fallback an toàn khi thư mục Hub không có lịch sử Git
  Given một thư mục Hub được tạo trên đĩa mà không có kho chứa .git
  When kỹ sư thực thi sync_contracts.py check hoặc brief
  Then engine bỏ qua lệnh git rev-parse và git log mà không phát sinh lỗi tiến trình con
  And tính toán chính xác trạng thái đồng bộ dựa trên mã băm sha256 của file và trường Version trong contract
```

## Chiều 3: Chuyển đổi trạng thái

```gherkin
Scenario: [SYC-ST-01] [Tier C - Integration] Phát hiện thay đổi tăng dần sau khi cập nhật Contract trên Hub
  Given một Satellite repository đã chạy sync_contracts.py ack trước đó và đang ở trạng thái "IN_SYNC"
  When Hub repository cập nhật api_contract.md lên phiên bản "1.1.0" với endpoint mới POST /api/v1/lyrics-sync/tasks/{id}/cancel và thêm RFC-002 vào gaps_and_rfcs.md
  And kỹ sư chạy lệnh sync_contracts.py check --strict trong Satellite repository
  Then trạng thái chuyển từ "IN_SYNC" sang "DRIFT_DETECTED"
  And báo cáo delta chỉ rõ api_contract.md và gaps_and_rfcs.md đã thay đổi, đánh dấu endpoint cancel mới là "MISSING_IN_CODE", và liệt kê RFC-002
  And lệnh sync_contracts.py check --strict kết thúc với exit code 1

Scenario: [SYC-ST-02] [Tier C - Integration] Bảo toàn Watermark đa domain và ghi nhận mã RFC chỉ định
  Given một Hub repository có hai domain lyrics-sync và nexus trong đó lyrics-sync đã được lưu trong .agents/contract_sync.json
  When kỹ sư thực thi sync_contracts.py ack --domain nexus --rfc RFC-005
  Then file .agents/contract_sync.json giữ nguyên vẹn mục "lyrics-sync" hiện có
  And ghi nhận thêm mục "nexus" mới có chứa "RFC-005" trong danh sách acknowledged_rfcs
```

## Chiều 4: Bất đồng bộ và đồng thời đa repo

```gherkin
Scenario: [SYC-AR-01] [Tier A - Unit] Cập nhật file Watermark nguyên tử ngăn chặn đọc phải JSON dở dang
  Given một file .agents/contract_sync.json đang tồn tại trong target repository
  When lệnh sync_contracts.py ack ghi dữ liệu đồng bộ mới
  Then engine ghi vào một file tạm trong thư mục .agents/ và thay thế nguyên tử file .agents/contract_sync.json
  And không để sót lại bất kỳ file tạm nào trong .agents/ sau khi hoàn tất

Scenario: [SYC-AR-02] [Tier A - Unit] Bảo vệ chống vòng lặp Symlink khi phân giải Topology
  Given một repository nơi đường dẫn shared-contracts nằm trong một chuỗi symbolic link trỏ vòng tròn vượt quá 10 bước nhảy
  When kỹ sư thực thi sync_contracts.py check
  Then quá trình duyệt symlink dừng lại một cách xác định tại giới hạn 10 bước nhảy
  And thoát với exit code 1 kèm thông báo lỗi phát hiện vòng lặp symbolic link
```

## Chiều 5: Lỗi và khả năng phục hồi lưu trữ

```gherkin
Scenario: [SYC-FR-01] [Tier A - Unit] Từ chối thực thi khi thiếu thư mục hoặc symlink Shared Contracts
  Given một target repository không có thư mục hay symlink shared-contracts
  When kỹ sư thực thi lệnh sync_contracts.py check, brief, hoặc ack
  Then lệnh dừng ngay với exit code 1
  And in ra thông báo lỗi hướng dẫn người dùng khởi tạo hoặc liên kết contracts bằng setup_contracts.py

Scenario: [SYC-FR-02] [Tier A - Unit] Từ chối thực thi khi Symlink bị đứt hoặc thiếu file Canonical
  Given một Satellite repository có symlink shared-contracts trỏ tới đường dẫn Hub không tồn tại hoặc thiếu file architecture_and_flow.md
  When kỹ sư thực thi lệnh sync_contracts.py check
  Then lệnh dừng ngay với exit code 1
  And in ra thông báo chẩn đoán nêu rõ đường dẫn đích bị đứt hoặc tên file canonical bị thiếu

Scenario: [SYC-FR-03] [Tier A - Unit] Khả năng phục hồi khi file Watermark JSON bị hỏng
  Given một target repository có file .agents/contract_sync.json chứa nội dung JSON không hợp lệ "{corrupt"
  When kỹ sư chạy lệnh sync_contracts.py check sau đó chạy sync_contracts.py ack
  Then lệnh sync_contracts.py check ghi nhận cảnh báo JSON lỗi và chuyển về trạng thái "INITIAL_SYNC" mà không bị văng lỗi
  And lệnh sync_contracts.py ack ghi đè sạch sẽ .agents/contract_sync.json bằng cấu trúc JSON schema_version 1 hợp lệ
```

