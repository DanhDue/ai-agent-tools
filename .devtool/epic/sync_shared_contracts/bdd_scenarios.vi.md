# Kịch Bản BDD Cho Sync Shared Contracts

## Mục lục

- [Chiều 1: Tuyến thực thi thành công](#chiều-1-tuyến-thực-thi-thành-công)
- [Chiều 2: Trường hợp biên và ranh giới](#chiều-2-trường-hợp-biên-và-ranh-giới)
- [Chiều 3: Chuyển đổi trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và đồng thời đa repo](#chiều-4-bất-đồng-bộ-và-đồng-thời-đa-repo)
- [Chiều 5: Lỗi và khả năng phục hồi lưu trữ](#chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

## Chiều 1: Tuyến thực thi thành công

```gherkin
Scenario: [SYC-HP-01] [Tier C - Integration] Phân tích cú pháp Contract kép và kết xuất báo cáo Requirements Brief
  Given một Hub repository đã khởi tạo với domain lyrics-sync chứa các file hợp đồng dạng bảng canonical hoặc dạng narrative thực tế (Version trong HTML comment, bullets Method/Path, và các mục GAP-XX với trạng thái OPEN/PROPOSED/ACCEPTED)
  When kỹ sư thực thi lệnh sync_contracts.py brief --domain lyrics-sync
  Then bộ phân tích trích xuất đúng phiên bản contract, toàn bộ các endpoints, authentication headers, các khóa JSON payload, các bước pipeline, và các mục RFC/GAP đã chuẩn hóa trạng thái
  And báo cáo Markdown đầu ra chứa đầy đủ các phần Topology Metadata (kèm snapshot_id), API and Schema Requirements, Architecture Invariants, Actionable RFCs, và Lifecycle Execution Rules
  And lệnh kết thúc với exit code 0

Scenario: [SYC-HP-02] [Tier C - Integration] Đồng bộ Satellite và Worktree lồng nhau toàn trình vượt qua kiểm tra Strict
  Given một Satellite repository được liên kết qua relative symlink shared-contracts tới ../Hub/shared-contracts/lyrics-sync và một git worktree lồng tại .worktrees/sync_epic
  When kỹ sư thực thi sync_contracts.py ack sau đó chạy sync_contracts.py check --strict từ thư mục gốc Satellite hoặc từ bên trong .worktrees/sync_epic
  Then relative symlink shared-contracts phân giải thành công tới domain trên Hub mà không làm thay đổi nội dung symlink được git theo dõi
  And file .agents/contract_sync.json được tạo trong checkout hiện hành với mode "satellite", domain "lyrics-sync", snapshot_id, và baseline_snapshot
  And lệnh sync_contracts.py check --strict xuất trạng thái "IN_SYNC" khi không còn pending_rfcs và kết thúc với exit code 0

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

Scenario: [SYC-EC-03] [Tier A - Unit] So sánh Semantic Baseline khi thư mục Hub không có Git hoặc khi đổi kiểu dữ liệu trường
  Given một thư mục Hub không có kho chứa .git nơi Satellite trước đó đã chạy sync_contracts.py ack lưu lại baseline_snapshot kèm payload_fields
  When một chỉnh sửa chưa commit trên Hub cập nhật api_contract.md thêm khóa payload "retry_after_ms", đổi kiểu trường "metrics.execution_time_ms" từ integer sang string, và thay đổi một bước pipeline
  And kỹ sư thực thi sync_contracts.py check hoặc brief
  Then engine bỏ qua lệnh git rev-parse và git log mà không phát sinh lỗi tiến trình con
  And đối chiếu contract hiện tại với baseline_snapshot để chỉ ra chính xác "retry_after_ms", thay đổi kiểu dữ liệu "metrics.execution_time_ms: integer -> string", và bước pipeline vừa thay đổi

Scenario: [SYC-EC-04] [Tier A - Unit] Phân giải Relative Symlink nhận biết Worktree bên trong Epic Worktree lồng nhau
  Given một Satellite repository có symlink gốc shared-contracts trỏ tương đối tới ../Hub/shared-contracts/lyrics-sync và một git worktree lồng tại .worktrees/sync_epic
  When hàm resolve_topology được gọi với repo_root trỏ vào worktree lồng .worktrees/sync_epic
  Then engine phát hiện thư mục gốc của repo chính thông qua metadata .git của worktree và phân giải relative symlink dựa trên thư mục gốc đó
  And trả về đúng thư mục contract trên Hub mà không làm thay đổi symlink được git theo dõi trong worktree
```

## Chiều 3: Chuyển đổi trạng thái

```gherkin
Scenario: [SYC-ST-01] [Tier C - Integration] Làm mới Snapshot ở Hub và phát hiện thay đổi tăng dần sau khi cập nhật trên Hub
  Given một Hub hoặc Satellite repository đã chạy sync_contracts.py ack --all-rfcs trước đó và đang ở trạng thái "IN_SYNC"
  When task_01 trên Hub cập nhật api_contract.md lên phiên bản "1.1.0" với endpoint mới POST /api/v1/lyrics-sync/tasks/{id}/cancel và thêm RFC-002 vào gaps_and_rfcs.md
  And kỹ sư chạy lệnh sync_contracts.py check --strict trước khi ack, sau đó làm mới snapshot_id qua sync_contracts.py brief và chạy sync_contracts.py ack --snapshot <refreshed_snapshot_id> --all-rfcs
  Then lệnh sync_contracts.py check --strict trước khi ack báo "DRIFT_DETECTED", chỉ ra endpoint cancel mới cùng RFC-002, và kết thúc với exit code 1
  And lệnh sync_contracts.py ack --snapshot <refreshed_snapshot_id> --all-rfcs thành công và lệnh check --strict tiếp theo kết thúc với exit code 0

Scenario: [SYC-ST-02] [Tier C - Integration] Chọn RFC tường minh theo phạm vi, kiểm tra Scoped Strict, và bảo toàn Watermark đa domain
  Given một Hub repository có hai domain lyrics-sync và nexus trong đó gaps_and_rfcs.md của nexus chứa GAP-01 ở trạng thái "OPEN" và GAP-03 ở trạng thái "ACCEPTED"
  When kỹ sư thực thi sync_contracts.py ack --domain nexus --rfc GAP-03, chạy lệnh check --domain nexus --strict --rfc GAP-03 cùng lệnh toàn cục check --domain nexus --strict, sau đó thực thi tiếp sync_contracts.py ack --domain nexus --rfc GAP-01
  Then sau lần ack đầu tiên, file .agents/contract_sync.json giữ nguyên mục "lyrics-sync", chỉ đưa "GAP-03" vào acknowledged_rfcs, giữ "GAP-01" trong pending_rfcs, lệnh theo phạm vi check --strict --rfc GAP-03 kết thúc với exit code 0, và lệnh toàn cục check --strict kết thúc với exit code 1
  And sau lần ack thứ hai có --rfc GAP-01, "GAP-01" được chuyển sang acknowledged_rfcs, pending_rfcs trở thành rỗng, và lệnh toàn cục check --strict kết thúc với exit code 0

Scenario: [SYC-ST-03] [Tier A - Unit] Từ chối khi Snapshot bị lệch do Contract thay đổi trước thời điểm Ack
  Given một target repository nơi sync_contracts.py brief đã ghi nhận snapshot_id là "sha256:stale"
  When một file contract canonical bị chỉnh sửa trên đĩa trước khi lệnh sync_contracts.py ack --snapshot sha256:stale được thực thi
  Then lệnh sync_contracts.py ack dừng ngay với exit code 1 và in ra "SNAPSHOT_MISMATCH" mà không làm thay đổi file .agents/contract_sync.json
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

Scenario: [SYC-FR-02] [Tier A - Unit] Từ chối thực thi khi Symlink bị đứt, thiếu file Canonical, hoặc định dạng Contract không hỗ trợ
  Given một Satellite repository có symlink shared-contracts trỏ tới đường dẫn Hub không tồn tại, thiếu file architecture_and_flow.md, hoặc chứa file api_contract.md không có bất kỳ endpoint hợp lệ nào
  When kỹ sư thực thi lệnh sync_contracts.py check
  Then lệnh dừng ngay với exit code 1
  And in ra thông báo chẩn đoán nêu rõ đường dẫn đích bị đứt, tên file canonical bị thiếu, hoặc lỗi "UNSUPPORTED_CONTRACT_FORMAT"

Scenario: [SYC-FR-03] [Tier A - Unit] Khả năng phục hồi khi file Watermark JSON bị hỏng
  Given một target repository có file .agents/contract_sync.json chứa nội dung JSON không hợp lệ "{corrupt"
  When kỹ sư chạy lệnh sync_contracts.py check sau đó chạy sync_contracts.py ack
  Then lệnh sync_contracts.py check ghi nhận cảnh báo JSON lỗi và chuyển về trạng thái "INITIAL_SYNC" mà không bị văng lỗi
  And lệnh sync_contracts.py ack ghi đè sạch sẽ .agents/contract_sync.json bằng cấu trúc JSON schema_version 1 hợp lệ
```
