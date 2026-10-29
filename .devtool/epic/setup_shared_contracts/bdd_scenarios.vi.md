# Kịch Bản BDD Cho Setup Shared Contracts

## Mục lục

- [Chiều 1: Tuyến thực thi thành công](#chiều-1-tuyến-thực-thi-thành-công)
- [Chiều 2: Trường hợp biên và ranh giới](#chiều-2-trường-hợp-biên-và-ranh-giới)
- [Chiều 3: Chuyển đổi trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và đồng thời đa repo](#chiều-4-bất-đồng-bộ-và-đồng-thời-đa-repo)
- [Chiều 5: Lỗi và khả năng phục hồi lưu trữ](#chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

## Chiều 1: Tuyến thực thi thành công

```gherkin
Scenario: [SSC-HP-01] [Tier C - Integration] Khởi tạo Hub repository mới
  Given một thư mục repository rỗng được chỉ định làm Hub
  When kỹ sư thực thi setup_contracts.py init-hub --domain lyrics-sync
  Then thư mục vật lý shared-contracts/ được tạo ra
  And file shared-contracts/README.md được sinh với cấu trúc liên kết hình sao (Star Topology)
  And thư mục domain shared-contracts/lyrics-sync/ chứa api_contract.md, architecture_and_flow.md, và gaps_and_rfcs.md
  And rule cục bộ cho Hub .agents/rules/contract_rules.md được tạo với hướng dẫn quyền sở hữu SSOT
  And lệnh kết thúc với exit code 0

Scenario: [SSC-HP-02] [Tier C - Integration] Tạo symlink tương đối cho Satellite repository mới
  Given một Hub repository hiện có với shared-contracts/lyrics-sync/ đã được khởi tạo
  And một thư mục repository vệ tinh độc lập nằm cùng cấp tên là lyrics-sync
  When kỹ sư thực thi setup_contracts.py link-satellite --hub ../D3Nexus --domain lyrics-sync từ bên trong lyrics-sync
  Then đường dẫn shared-contracts được tạo thành một symbolic link tương đối trỏ tới ../D3Nexus/shared-contracts/lyrics-sync
  And symlink phân giải thành công tới đủ 3 file hợp đồng chuẩn mà không có lỗi dangling
  And rule cục bộ cho vệ tinh .agents/rules/contract_rules.md được tạo với ràng buộc Git read-only
  And lệnh kết thúc với exit code 0

Scenario: [SSC-HP-03] [Tier C - Integration] Kiểm tra sức khỏe toàn diện hợp lệ
  Given một Hub repository đã khởi tạo hợp lệ và Satellite repository đã được liên kết
  When kỹ sư thực thi setup_contracts.py verify trong một trong hai repository
  Then engine tự động nhận diện chế độ repository (Hub hoặc Satellite)
  And xác thực tính hợp lệ của các file vật lý, đích đến symlink, và sự tồn tại của rule cục bộ
  And xuất báo cáo PASS màu xanh với exit code 0
```

## Chiều 2: Trường hợp biên và ranh giới

```gherkin
Scenario: [SSC-EC-01] [Tier A - Unit] Thực thi idempotent bảo toàn các chỉnh sửa tùy biến
  Given một Hub repository hiện có nơi file api_contract.md đã được chỉnh sửa bổ sung endpoint tùy biến
  When kỹ sư thực thi setup_contracts.py init-hub --domain lyrics-sync mà không có cờ --force
  Then file api_contract.md hiện có được giữ nguyên vẹn và không bị ghi đè
  And lệnh hoàn thành thành công với exit code 0

Scenario: [SSC-EC-02] [Tier A - Unit] Tính toán đường dẫn tương đối qua hệ thống phân cấp thư mục sâu
  Given một Hub nằm tại root/control-plane/hub
  And một Satellite nằm tại root/services/workers/audio/satellite
  When kỹ sư thực thi lệnh link-satellite với đường dẫn tới Hub
  Then symlink được tạo sử dụng chính xác đường dẫn tương đối ../../../../control-plane/hub/shared-contracts/<domain>
  And symlink phân giải thành công tới các file đích

Scenario: [SSC-EC-03] [Tier A - Unit] Chuẩn hóa tên domain và cắt tỉa khoảng trắng
  Given kỹ sư truyền tên domain chứa khoảng trắng đầu cuối và chữ hoa lẫn lộn "  Lyrics-Sync  "
  When CLI xử lý đối số domain
  Then tên thư mục domain được chuẩn hóa thành chuỗi chữ thường đã cắt tỉa "lyrics-sync"
  And các đường dẫn và neo tài liệu được tạo ra một cách đồng nhất
```

## Chiều 3: Chuyển đổi trạng thái

```gherkin
Scenario: [SSC-ST-01] [Tier C - Integration] Bổ sung domain tiếp theo cập nhật file README topology
  Given một Hub repository hiện có đã chứa domain lyrics-sync
  When kỹ sư thực thi setup_contracts.py init-hub --domain nexus
  Then thư mục shared-contracts/nexus/ được tạo với 3 file canonical
  And file gốc shared-contracts/README.md được cập nhật để bổ sung nexus vào bảng Outbound Symlink Mappings
  And mục lyrics-sync hiện có được giữ nguyên vẹn

Scenario: [SSC-ST-02] [Tier C - Integration] Chuyển đổi domain liên kết trên Satellite kèm cờ force
  Given một satellite repository hiện đang tạo symlink tới domain alpha
  When kỹ sư thực thi link-satellite --hub ../Hub --domain beta --force
  Then symlink hiện có được cập nhật để trỏ tới ../Hub/shared-contracts/beta
  And đích symlink cũ được thay thế sạch sẽ mà không để lại liên kết dangling
```

## Chiều 4: Bất đồng bộ và đồng thời đa repo

```gherkin
Scenario: [SSC-AR-01] [Tier A - Unit] Tạo file nguyên tử ngăn chặn ghi một phần
  Given thao tác render template ghi ra 3 file hợp đồng canonical
  When việc ghi file diễn ra trong môi trường thực thi song song
  Then các file được ghi theo cơ chế nguyên tử (atomic) sử dụng file hoán đổi tạm hoặc ghi trực tiếp không bộ đệm
  And không có file canonical nào bị ghi dở dang hoặc có kích thước 0 byte bị nhìn thấy bởi các tiến trình đồng thời

Scenario: [SSC-AR-02] [Tier A - Unit] Bảo vệ chống symlink vòng lặp và đệ quy vô hạn
  Given một workspace bất thường chứa các symbolic link vòng lặp hiện có
  When lệnh setup_contracts.py verify duyệt các đường dẫn để phân giải hợp đồng
  Then quá trình duyệt áp dụng cơ chế phát hiện chu trình và giới hạn độ sâu
  And dừng an toàn mà không rơi vào vòng lặp đệ quy vô hạn
```

## Chiều 5: Lỗi và khả năng phục hồi lưu trữ

```gherkin
Scenario: [SSC-FR-01] [Tier A - Unit] Từ chối khởi tạo Hub trên symlink hiện có
  Given một thư mục nơi shared-contracts hiện đang là một symbolic link
  When kỹ sư thực thi setup_contracts.py init-hub
  Then lệnh từ chối thực thi
  And in ra thông báo lỗi giải thích rằng Hub repository bắt buộc phải duy trì thư mục vật lý
  And thoát với exit code lỗi khác 0 là 1

Scenario: [SSC-FR-02] [Tier A - Unit] Từ chối liên kết Satellite khi domain đích không tồn tại
  Given một Hub repository hợp lệ nhưng không chứa domain unknown-service
  When kỹ sư thực thi link-satellite --hub ../Hub --domain unknown-service
  Then lệnh từ chối tạo một symlink dangling
  And in ra thông báo lỗi nêu rõ không tìm thấy domain đích trong Hub
  And thoát với exit code lỗi khác 0 là 1

Scenario: [SSC-FR-03] [Tier A - Unit] Từ chối ghi đè thư mục vật lý hiện có khi không có force
  Given một satellite repository nơi shared-contracts/ hiện là một thư mục vật lý có chứa dữ liệu
  When kỹ sư thực thi link-satellite mà không truyền cờ --force
  Then lệnh từ chối thay thế thư mục vật lý bằng một symlink
  And in ra thông báo cảnh báo về nguy cơ mất dữ liệu file chưa được commit
  And thoát với exit code lỗi khác 0 là 1
```
