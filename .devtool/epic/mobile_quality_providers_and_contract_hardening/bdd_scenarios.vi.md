# Kịch Bản Kiểm Thử BDD: Gia Cố Hợp Đồng Và Bộ Provider Kiểm Thử Di Động

## Mục Lục

- [1. Tổng Quan và Ma Trận Ranh Giới 5 Chiều](#1-tổng-quan-và-ma-trận-ranh-giới-5-chiều)
- [2. Use Case 1: Khởi Tạo Dự Án và Sinh Mẫu Manifest](#2-use-case-1-khởi-tạo-dự-án-và-sinh-mẫu-manifest)
  - [2.1. Chiều 1: Happy Paths](#21-chiều-1-happy-paths)
  - [2.2. Chiều 2: Các Tình Huống Biên và Giới Hạn](#22-chiều-2-các-tình-huống-biên-và-giới-hạn)
  - [2.3. Chiều 3: Chuyển Đổi Trạng Thái](#23-chiều-3-chuyển-đổi-trạng-thái)
  - [2.4. Chiều 4: Bất Đồng Bộ và Đồng Thời](#24-chiều-4-bất-đồng-bộ-và-đồng-thời)
  - [2.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường](#25-chiều-5-lỗi-và-khả-năng-chống-chịu-môi-trường)
- [3. Use Case 2: Phê Duyệt Gate 4 Cuối Epic](#3-use-case-2-phê-duyệt-gate-4-cuối-epic)
  - [3.1. Chiều 1: Happy Paths](#31-chiều-1-happy-paths)
  - [3.2. Chiều 2: Các Tình Huống Biên và Giới Hạn](#32-chiều-2-các-tình-huống-biên-và-giới-hạn)
  - [3.3. Chiều 3: Chuyển Đổi Trạng Thái](#33-chiều-3-chuyển-đổi-trạng-thái)
  - [3.4. Chiều 4: Bất Đồng Bộ và Đồng Thời](#34-chiều-4-bất-đồng-bộ-và-đồng-thời)
  - [3.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường](#35-chiều-5-lỗi-và-khả-năng-chống-chịu-môi-trường)
- [4. Use Case 3: Đánh Giá Pull Request Theo Profile](#4-use-case-3-đánh-giá-pull-request-theo-profile)
  - [4.1. Chiều 1: Happy Paths](#41-chiều-1-happy-paths)
  - [4.2. Chiều 2: Các Tình Huống Biên và Giới Hạn](#42-chiều-2-các-tình-huống-biên-và-giới-hạn)
  - [4.3. Chiều 3: Chuyển Đổi Trạng Thái](#43-chiều-3-chuyển-đổi-trạng-thái)
  - [4.4. Chiều 4: Bất Đồng Bộ và Đồng Thời](#44-chiều-4-bất-đồng-bộ-và-đồng-thời)
  - [4.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường](#45-chiều-5-lỗi-và-khả-năng-chống-chịu-môi-trường)
- [5. Use Case 4: Gia Cố Hợp Đồng Engine và Chặn Đứng False-PASS](#5-use-case-4-gia-cố-hợp-đồng-engine-và-chặn-đứng-false-pass)
  - [5.1. Chiều 1: Happy Paths](#51-chiều-1-happy-paths)
  - [5.2. Chiều 2: Các Tình Huống Biên và Giới Hạn](#52-chiều-2-các-tình-huống-biên-và-giới-hạn)
  - [5.3. Chiều 3: Chuyển Đổi Trạng Thái](#53-chiều-3-chuyển-đổi-trạng-thái)
  - [5.4. Chiều 4: Bất Đồng Bộ và Đồng Thời](#54-chiều-4-bất-đồng-bộ-và-đồng-thời)
  - [5.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường](#55-chiều-5-lỗi-và-khả-năng-chống-chịu-môi-trường)

---

## 1. Tổng Quan và Ma Trận Ranh Giới 5 Chiều

Tài liệu này định nghĩa toàn bộ kịch bản kiểm thử BDD bằng cú pháp Gherkin cho epic `mobile_quality_providers_and_contract_hardening`. Mọi kịch bản đều tuân thủ chặt chẽ **Ma Trận Ranh Giới 5 Chiều Bắt Buộc**:
1. **Happy Paths**: Các luồng thực thi danh định với dữ liệu chuẩn và trạng thái thành công như mong đợi.
2. **Các Tình Huống Biên & Giới Hạn**: Ngưỡng biên, cấu trúc rỗng/bằng không, và tích hợp đa nền tảng.
3. **Chuyển Đổi Trạng Thái**: Các bước chuyển trạng thái hợp lệ và không hợp lệ qua các khâu gọi lệnh, thực thi và tổng hợp.
4. **Bất Đồng Bộ & Đồng Thời**: Thực thi provider song song, tranh chấp tài nguyên, và bảo vệ tính ổn định SHA.
5. **Lỗi & Khả Năng Chống Chịu Môi Trường**: Thiếu file thực thi, cấu hình sai schema, và timeout tiến trình.

---

## 2. Use Case 1: Khởi Tạo Dự Án và Sinh Mẫu Manifest

### 2.1. Chiều 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Tự động sinh manifest cho dự án Flutter
  Given thư mục gốc của một dự án Flutter sạch chứa pubspec.yaml với cấu hình workspace
  When lập trình viên thực thi setup_quality_check
  Then file .agents/quality/check_quality.json được tạo với provider flutter-core
  And file .agents/quality/flutter-quality.json được tạo khai báo các capability format, analyze, boundaries, test, và audits
  And lần chạy kiểm chuẩn baseline ban đầu thành công với trạng thái PASS
```

```gherkin
Scenario: [Tier C - Integration] Tự động sinh manifest cho dự án Android
  Given thư mục gốc của một dự án Android sạch chứa build.gradle.kts và settings.gradle.kts
  When lập trình viên thực thi setup_quality_check
  Then file .agents/quality/check_quality.json được tạo với provider android-core
  And file .agents/quality/android-quality.json được tạo khai báo các capability Konsist, BCV, Detekt, và test
  And lần chạy kiểm chuẩn baseline ban đầu thành công với trạng thái PASS
```

### 2.2. Chiều 2: Các Tình Huống Biên và Giới Hạn

```gherkin
Scenario: [Tier A - Unit] Sinh manifest cho repository đa ngôn ngữ composite
  Given một repository chứa đồng thời Cargo.toml và pubspec.yaml
  When lệnh setup_quality_check được thực thi
  Then file .agents/quality/check_quality.json khai báo cả 2 provider rust-core và flutter-core
  And cả 2 provider đều có required=true cho profile epic
```

### 2.3. Chiều 3: Chuyển Đổi Trạng Thái

```gherkin
Scenario: [Tier C - Integration] Tính lũy thừa khi chạy lại setup mà không ghi đè cấu hình cũ
  Given một repository đã tồn tại .agents/quality/check_quality.json với các ngưỡng tùy chỉnh
  When lệnh setup_quality_check được chạy lại mà không có cờ --force
  Then các file manifest hiện tại được giữ nguyên vẹn
  And thông báo hiển thị cho người dùng biết cấu hình đã tồn tại sẵn
```

### 2.4. Chiều 4: Bất Đồng Bộ và Đồng Thời

```gherkin
Scenario: [Tier A - Unit] Xử lý tranh chấp khi có hai agent cùng khởi tạo setup đồng thời
  Given hai subagent cùng gọi lệnh setup_quality_check song song
  When các thao tác ghi file được thực hiện qua cơ chế ghi và thay thế nguyên tử
  Then các file manifest cuối cùng hợp lệ và không chứa nội dung JSON bị hỏng
```

### 2.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường

```gherkin
Scenario: [Tier A - Unit] Dừng lại khi không nhận diện được loại nền tảng repository
  Given một repository không chứa bất kỳ dấu hiệu nền tảng nào nhận biết được
  When lệnh setup_quality_check được thực thi
  Then công cụ dừng lại với trạng thái BLOCKED
  And thông báo lỗi liệt kê rõ ràng các nền tảng được hỗ trợ (Rust, Flutter, Android, iOS)
```

---

## 3. Use Case 2: Phê Duyệt Gate 4 Cuối Epic

### 3.1. Chiều 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Cấp phê duyệt Gate 4 thành công trên dự án Flutter
  Given một worktree epic đã hoàn thành trên dự án Flutter
  And file .agents/quality/check_quality.json khai báo provider bắt buộc flutter-core
  When @quality_check được gọi với profile="epic" và commit SHA ứng viên
  Then flutter-quality-check thực thi format, analyze, boundaries, unit tests, coverage, và 4 audits
  And tất cả các check đều trả về trạng thái PASS với coverage vượt 80%
  And quality_check cấp phê duyệt 🟢 LGTM gắn với SHA ứng viên
```

```gherkin
Scenario: [Tier C - Integration] Cấp phê duyệt Gate 4 thành công trên dự án Android
  Given một worktree epic đã hoàn thành trên dự án Android
  And file .agents/quality/check_quality.json khai báo provider bắt buộc android-core
  When @quality_check được gọi với profile="epic" và commit SHA ứng viên
  Then android-quality-check thực thi Konsist K1-K10, BCV apiCheck, Detekt, unit tests, và acceptance harness
  And tất cả các check đều trả về trạng thái PASS
  And lệnh cleanup-java giải phóng toàn bộ Gradle daemon nền
  And quality_check cấp phê duyệt 🟢 LGTM gắn với SHA ứng viên
```

### 3.2. Chiều 2: Các Tình Huống Biên và Giới Hạn

```gherkin
Scenario: [Tier A - Unit] Repo composite yêu cầu đồng thuận tuyệt đối trên mọi nền tảng
  Given một workspace composite khai báo cả rust-core và android-core
  When @quality_check chạy cho profile="epic"
  And rust-core trả về PASS
  Nhưng android-core trả về FAIL do vi phạm ranh giới kiến trúc Konsist
  Then kết luận tổng hợp chung bắt buộc là FAIL
  And phê duyệt Gate 4 bị từ chối
```

### 3.3. Chiều 3: Chuyển Đổi Trạng Thái

```gherkin
Scenario: [Tier C - Integration] Từ chối yêu cầu thiếu profile trong xác thực Gate 4 chính thức
  Given một caller tự động gọi @quality_check trong quy trình lifecycle
  When tham số profile bị bỏ trống
  Then orchestrator từ chối yêu cầu với trạng thái BLOCKED
  And yêu cầu phải truyền rõ profile="epic" cho khâu xác thực lifecycle
```

### 3.4. Chiều 4: Bất Đồng Bộ và Đồng Thời

```gherkin
Scenario: [Tier A - Unit] Từ chối bằng chứng quá hạn khi SHA ứng viên bị trôi lệch
  Given một phiên kiểm chuẩn bắt đầu trên commit SHA ứng viên "1111111"
  When một tiến trình nền hoặc agent commit thay đổi làm HEAD chuyển thành "2222222" trước khi provider chạy xong
  Then orchestrator phát hiện hiện tượng SHA drift
  And bác bỏ toàn bộ bằng chứng thu thập được là quá hạn với trạng thái BLOCKED
```

### 3.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường

```gherkin
Scenario: [Tier A - Unit] Thiếu trình biên dịch hoặc công cụ CLI bắt buộc
  Given một dự án iOS khai báo capability swiftformat
  When swiftformat vắng mặt trên biến môi trường PATH của máy
  Then ios-quality-check trả về trạng thái BLOCKED
  And báo cáo liệt kê rõ "missing executable: swiftformat" trong danh sách blockers
```

---

## 4. Use Case 3: Đánh Giá Pull Request Theo Profile

### 4.1. Chiều 1: Happy Paths

```gherkin
Scenario: [Tier C - Integration] Thực thi review PR nhanh trên phạm vi bị chạm
  Given diff của nhánh tính năng trỏ vào develop
  When @pr_review gọi @quality_check với profile="pr"
  Then provider được chọn thực thi nhanh format, biên dịch, lint, và unit test bị chạm
  And các bộ test tích hợp toàn diện tốn kém được bỏ qua
  And báo cáo review PR súc tích được kết xuất kèm vị trí lỗi cụ thể
```

### 4.2. Chiều 2: Các Tình Huống Biên và Giới Hạn

```gherkin
Scenario: [Tier A - Unit] Ngăn chặn việc dùng bằng chứng PR để thỏa mãn Gate 4
  Given bằng chứng đã thu thập từ một lần chạy profile="pr" trước đó
  When @dev-implementation Gate 4 yêu cầu profile="epic"
  Then orchestrator từ chối tái sử dụng bằng chứng pr
  And yêu cầu một lần chạy profile epic toàn diện mới
```

### 4.3. Chiều 3: Chuyển Đổi Trạng Thái

```gherkin
Scenario: [Tier C - Integration] Review PR chuyển từ PASS sang CHANGES REQUESTED khi có lỗi lint
  Given một PR đưa vào một code smell Detekt mới
  When @pr_review chạy với profile="pr"
  Then android-quality-check báo cáo trạng thái check FAIL cho Detekt
  And pr_review xuất kết luận 🔴 CHANGES REQUESTED chi tiết số dòng vi phạm
```

### 4.4. Chiều 4: Bất Đồng Bộ và Đồng Thời

```gherkin
Scenario: [Tier A - Unit] Phân luồng provider song song trong review PR
  Given một repository có 2 provider độc lập được chọn cho profile="pr"
  When @quality_check phân luồng thực thi
  Then cả hai provider cùng chạy song song
  And kết quả đầu ra được sắp xếp xác định theo provider ID
```

### 4.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường

```gherkin
Scenario: [Tier A - Unit] Thất bại khi phân giải base ref
  Given một lệnh review PR được gọi mà không có base_ref rõ ràng và git không tìm được merge-base
  When @quality_check chạy
  Then orchestrator dừng lại với trạng thái BLOCKED
  And yêu cầu người gọi cung cấp base_ref tường minh
```

---

## 5. Use Case 4: Gia Cố Hợp Đồng Engine và Chặn Đứng False-PASS

### 5.1. Chiều 1: Happy Paths

```gherkin
Scenario: [Tier A - Unit] Kết quả provider hợp lệ vượt qua khâu xác thực gia cố
  Given một file kết quả provider khớp với provider-result.schema.json
  And tất cả các check đều báo cáo trạng thái PASS kèm tham chiếu bằng chứng khớp
  And line coverage đạt 0.88 với ngưỡng cấu hình là 0.80
  When validate_quality_contract.py xác thực kết quả
  Then việc xác thực thành công với exit code 0
```

### 5.2. Chiều 2: Các Tình Huống Biên và Giới Hạn

```gherkin
Scenario: [Tier A - Unit] Chặn False-PASS: Provider PASS nhưng có check FAIL bị từ chối triệt để
  Given một file kết quả provider khai báo status="PASS" cấp cao nhất
  Nhưng một check bên trong mảng checks báo cáo status="FAIL"
  When validate_quality_contract.py xác thực kết quả
  Then bộ xác thực bác bỏ file kết quả với lỗi "CONTRACT_VIOLATION"
  And trạng thái của kết quả bị chuyển thành BLOCKED
```

```gherkin
Scenario: [Tier A - Unit] Chặn False-PASS: Provider PASS nhưng coverage dưới ngưỡng bị từ chối triệt để
  Given một file kết quả provider khai báo status="PASS" cấp cao nhất
  And ngưỡng coverage được cấu hình là 0.85
  Nhưng coverage đo được thực tế là 0.10
  When validate_quality_contract.py xác thực kết quả
  Then bộ xác thực bác bỏ file kết quả với lỗi "COVERAGE_DEFICIT"
  And trạng thái cấp cao nhất không thể giữ nguyên là PASS
```

### 5.3. Chiều 3: Chuyển Đổi Trạng Thái

```gherkin
Scenario: [Tier A - Unit] Lệnh reconcile từ chối SHA cũ trong file kết quả
  Given một kế hoạch thực thi hướng tới SHA "aaaaaaa"
  When lệnh reconcile được gọi với một file kết quả chứa started_head="bbbbbbb"
  Then reconcile dừng lại với lỗi "SHA_MISMATCH" và exit code khác 0
```

### 5.4. Chiều 4: Bất Đồng Bộ và Đồng Thời

```gherkin
Scenario: [Tier A - Unit] Engine tổng hợp xử lý kết quả xung đột một cách xác định
  Given Provider A báo cáo FAIL trên unit tests
  And Provider B báo cáo BLOCKED do thiếu công cụ tùy chọn
  When aggregate_quality_results.py tổng hợp các kết luận
  Then trạng thái chung là FAIL vì FAIL có độ ưu tiên cao hơn BLOCKED
  And cả lỗi test lẫn blocker thiếu công cụ đều hiển thị rõ ràng trên báo cáo
```

### 5.5. Chiều 5: Lỗi và Khả Năng Chống Chịu Môi Trường

```gherkin
Scenario: [Tier A - Unit] Schema capability từ chối mảng lệnh rỗng
  Given một file capability JSON khai báo capability "test" với mảng lệnh rỗng []
  When validate_quality_contract.py xác thực manifest capability
  Then bộ xác thực dừng lại với lỗi schema "COMMAND_ARRAY_EMPTY"
```
