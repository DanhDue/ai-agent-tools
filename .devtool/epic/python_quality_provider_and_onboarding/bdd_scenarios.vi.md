# Kịch Bản BDD: Python Quality Provider và Onboarding

## Mục Lục

- [1. Tổng Quan và Ma Trận Ranh Giới](#1-tổng-quan-và-ma-trận-ranh-giới)
- [2. Chiều 1: Kịch Bản Thành Công](#2-chiều-1-kịch-bản-thành-công)
- [3. Chiều 2: Trường Hợp Biên và Giới Hạn](#3-chiều-2-trường-hợp-biên-và-giới-hạn)
- [4. Chiều 3: Chuyển Đổi Trạng Thái và Bất Biến](#4-chiều-3-chuyển-đổi-trạng-thái-và-bất-biến)
- [5. Chiều 4: Đồng Thời và Tính Tất Định](#5-chiều-4-đồng-thời-và-tính-tất-định)
- [6. Chiều 5: Lỗi và Khả Năng Phục Hồi Lưu Trữ](#6-chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

---

## 1. Tổng Quan và Ma Trận Ranh Giới

Tài liệu này chuẩn hóa đặc tả Behavior-Driven Development (BDD) cho Python Quality Provider và hệ thống khởi tạo tự động dựa trên Ma trận Ranh giới 5 Chiều:

| Chiều | Phạm Vi Kiểm Thử | Mã Lỗi / Cam Kết Mục Tiêu |
|---|---|---|
| **1. Kịch Bản Thành Công** | Tự động khám phá, khởi tạo mẫu, thực thi provider, tổng hợp kết quả | `status: PASS`, chứng từ gắn với SHA |
| **2. Trường Hợp Biên** | Mảng lệnh rỗng, tỷ lệ coverage sát ngưỡng | `command_array_empty`, `coverage_deficit` |
| **3. Chuyển Đổi Trạng Thái** | Hạ cấp False-PASS, tính nhất quán trạng thái check | `contract_violation` -> `BLOCKED` |
| **4. Đồng Thời** | Thứ tự thực thi song song không làm thay đổi kết quả | Thứ tự báo cáo ổn định tất định |
| **5. Lỗi & Phục Hồi** | SHA bị lệch, cây làm việc bị bẩn, thiếu công cụ CLI | `repository_sha_mismatch`, `ALREADY_EXISTS` |

---

## 2. Chiều 1: Kịch Bản Thành Công

```gherkin
Tính năng: Kiểm thực kịch bản thành công của Python Quality Provider

  Kịch bản: [PY-HP-01] Tự động phát hiện workspace Python và khởi tạo manifest
    Cho một kho mã nguồn chứa "pyproject.toml" và "uv.lock"
    Khi scaffold_quality_manifest.py thực thi tại thư mục gốc
    Thì .agents/quality/check_quality.json khai báo provider "python-core"
    Và .agents/quality/python-quality.json được tạo với schema_version 1
    Và toàn bộ capability khai báo đều vượt qua xác thực của validate_python_quality.py

  Kịch bản: [PY-HP-02] Thực thi toàn bộ bộ kiểm tra chất lượng Python với kết quả xanh
    Cho một kho mã nguồn Python sạch với định dạng chuẩn, không lỗi lint, type nghiêm ngặt và test pass
    Khi python-quality-check thực thi profile "pr"
    Thì ruff format, ruff check, mypy và pytest chạy thành công không lỗi
    Và provider-result.json được phát ra với trạng thái "PASS"
    Và provider-result.json được gắn kết mật mã với commit SHA hiện tại

  Kịch bản: [PY-HP-03] Tổng hợp đa provider hỗn hợp giữa Python và nền tảng di động
    Cho check_quality.json khai báo cả "python-core" và "flutter-core"
    Khi cả hai provider đều trả về provider-result.json hợp lệ với trạng thái "PASS"
    Thì aggregate_quality_results.py tạo ra kết luận tổng hợp "PASS"
    Và báo cáo điều hành hiển thị trạng thái và độ bao phủ của cả hai provider
```

---

## 3. Chiều 2: Trường Hợp Biên và Giới Hạn

```gherkin
Tính năng: Kiểm thực các trường hợp biên và giới hạn

  Kịch bản: [PY-EDGE-01] Từ chối capability khai báo với mảng lệnh rỗng
    Cho một file python-quality.json có capability "lint" là mảng rỗng []
    Khi validate_python_quality.py xác thực cấu hình
    Thì quá trình xác thực thất bại với mã lỗi "command_array_empty"
    Và provider dừng thực thi trước khi gọi bất kỳ tiến trình nào

  Kịch bản: [PY-EDGE-02] Thực thi nghiêm ngặt ngưỡng ranh giới độ bao phủ dòng
    Cho python-quality.json với ngưỡng coverage yêu cầu là 0.80
    Khi báo cáo coverage của pytest ghi nhận tỷ lệ đo được là 0.799
    Thì python-quality-check ghi nhận lỗi "coverage_deficit"
    Và trạng thái của provider bị hạ cấp về "BLOCKED"
```

---

## 4. Chiều 3: Chuyển Đổi Trạng Thái và Bất Biến

```gherkin
Tính năng: Chuyển đổi trạng thái và phòng vệ bất biến False-PASS

  Kịch bản: [PY-ST-01] Hạ cấp kết quả mâu thuẫn về BLOCKED (Phòng vệ F1)
    Cho kết quả provider Python có trạng thái cấp cao nhất là "PASS"
    Và một check con "unit_test" báo cáo trạng thái "FAIL"
    Khi validate_provider_result xác thực kết quả đầu ra
    Thì phát hiện lỗi "contract_violation" được ghi nhận
    Và kết quả tổng hợp hạ cấp provider về trạng thái "BLOCKED"

  Kịch bản: [PY-ST-02] Chặn provider báo cáo PASS khi coverage dưới ngưỡng (Phòng vệ F2)
    Cho kết quả provider Python báo cáo trạng thái "PASS"
    Và coverage đo được là 0.65 trong khi ngưỡng yêu cầu là 0.80
    Khi validate_provider_result xác thực kết quả đầu ra
    Thì phát hiện lỗi "coverage_deficit" được ghi nhận
    Và provider bị đánh dấu "BLOCKED" trong báo cáo điều hành cuối cùng
```

---

## 5. Chiều 4: Đồng Thời và Tính Tất Định

```gherkin
Tính năng: Đồng thời và tính tất định trong báo cáo

  Kịch bản: [PY-CONC-01] Thứ tự hoàn thành bất đồng bộ không làm thay đổi báo cáo
    Cho các provider "python-core" và "rust-core" hoàn thành không theo thứ tự cố định
    Khi aggregate_quality_results.py xử lý mảng [python, rust] so với [rust, python]
    Thì báo cáo markdown điều hành đầu ra giống nhau từng byte
    Và các hàng provider tuân theo thứ tự sắp xếp chữ cái ổn định theo ID provider
```

---

## 6. Chiều 5: Lỗi và Khả Năng Phục Hồi Lưu Trữ

```gherkin
Tính năng: Xử lý lỗi và khả năng phục hồi lưu trữ

  Kịch bản: [PY-FAIL-01] Từ chối kết quả bị trôi dạt commit SHA ứng viên (Phòng vệ F3)
    Cho một phiên chạy chất lượng bắt đầu tại commit SHA "aaaa1111"
    Khi python-quality-check phát ra provider-result.json gắn với SHA "bbbb2222"
    Thì kết quả bị từ chối với mã lỗi "repository_sha_mismatch"
    Và pipeline trả về trạng thái "BLOCKED"

  Kịch bản: [PY-FAIL-02] Bảo vệ tất định chống ghi đè cấu hình hiện hữu
    Cho .agents/quality/check_quality.json đã tồn tại trong kho mã nguồn mục tiêu
    Khi scaffold_quality_manifest.py chạy mà không có tùy chọn --force
    Thì quá trình dừng lại với mã lỗi 1 và thông báo "already exists"
    Và không có file cấu hình hiện hữu nào bị thay đổi

  Kịch bản: [PY-FAIL-03] Báo cáo BLOCKED khi công cụ CLI bắt buộc bị thiếu
    Cho một hệ thống chưa cài đặt hoặc không tìm thấy "uv" trong biến môi trường PATH
    Khi python-quality-check thực hiện chạy capability
    Thì provider phát ra trạng thái "BLOCKED" kèm lý do cản trở "tool_missing: uv"
```
