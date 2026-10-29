# Thiết Kế Skill Thiết Lập Thư Mục Shared Contracts

- **Ngày**: 2026-10-30
- **Trạng thái**: Đã phê duyệt
- **Phạm vi**: Skill mới `skills/setup-shared-contracts/`, CLI engine `setup_contracts.py`, các template chuẩn hóa, bộ test hermetic, tích hợp vào `scripts/verify.sh`
- **Bước tiếp theo**: `d3nexus:dev-implementation` (Stage 3 — Thực thi dựa trên Kiểm thử)

## Mục lục

- [1. Bối cảnh và Động lực](#1-bối-cảnh-và-động-lực)
- [2. Mục tiêu và Ngoài phạm vi](#2-mục-tiêu-và-ngoài-phạm-vi)
- [3. Quyết định Kiến trúc và Cấu trúc Topology](#3-quyết-định-kiến-trúc-và-cấu-trúc-topology)
- [4. Cấu trúc Thư mục và các Thành phần](#4-cấu-trúc-thư-mục-và-các-thành-phần)
- [5. Đặc tả Kỹ thuật CLI Engine](#5-đặc-tả-kỹ-thuật-cli-engine)
- [6. Bộ Template Chuẩn hóa](#6-bộ-template-chuẩn-hóa)
- [7. Chiến lược Kiểm thử và Xác minh](#7-chiến-lược-kiểm-thử-và-xác-minh)
- [8. Tích hợp Vòng đời và Trải nghiệm Agent](#8-tích-hợp-vòng-đời-và-trải-nghiệm-agent)
- [9. Xử lý Lỗi và các Trường hợp Biên](#9-xử-lý-lỗi-và-các-trường-hợp-biên)
- [10. Rủi ro và Biện pháp Giảm thiểu](#10-rủi-ro-và-biện-pháp-giảm-thiểu)

## 1. Bối cảnh và Động lực

Trong các kiến trúc đa repository (multi-repo) hiện đại (chẳng hạn như hệ sinh thái D3Nexus kết nối control plane `D3Nexus` với các worker node như `lyrics-sync` và ứng dụng di động như `nexus`), việc giao tiếp liên dịch vụ phụ thuộc vào một thư mục hợp đồng dùng chung (`shared-contracts/`).

Trước đây, việc thiết lập `shared-contracts/` là một quy trình thủ công và dễ phát sinh sai sót:
- Kỹ sư phải tự tạo các thư mục con và viết tay 3 file canonical (`api_contract.md`, `architecture_and_flow.md`, `gaps_and_rfcs.md`).
- Các repository vệ tinh (satellite) tạo symlink thủ công. Các agent thường xuyên tạo symlink bằng đường dẫn tuyệt đối (absolute path), gây gãy liên kết khi chuyển sang máy khác hoặc chạy trong CI/CD.
- Các quy tắc quản trị quan trọng (như ranh giới Git tracking, lệnh cấm worker kết nối trực tiếp database, và cam kết không phá vỡ schema) thường bị bỏ sót hoặc cấu hình không đồng nhất trong `.agents/rules/` cục bộ.

Để loại bỏ các nút thắt cổ chai này và bảo đảm tuân thủ 100% Rule 7 của `CRITICAL_RULES.md`, chúng tôi xây dựng skill `setup-shared-contracts` và CLI engine đi kèm.

## 2. Mục tiêu và Ngoài phạm vi

### Mục tiêu
- Cung cấp script CLI (`setup_contracts.py`) viết hoàn toàn bằng Python tiêu chuẩn, không phụ thuộc vào bất kỳ thư viện bên thứ ba nào.
- Hỗ trợ **Khởi tạo Hub (`init-hub`)**: Tạo thư mục vật lý `shared-contracts/`, sinh các thư mục domain, tạo 3 file canonical từ template chuẩn hóa, cập nhật `README.md` gốc, và cài đặt rule cục bộ cho Hub repo.
- Hỗ trợ **Liên kết Vệ tinh (`link-satellite`)**: Tự động tính toán relative symlink chuẩn xác (`os.path.relpath`), kiểm tra chống dangling symlink, cài đặt rule cục bộ cho Satellite repo, và cập nhật `AGENTS.md`.
- Hỗ trợ **Kiểm tra Toàn vẹn (`verify`)**: Tự động nhận diện chế độ repo (Hub vs Satellite), kiểm tra tính hợp lệ của symlink, bảo đảm đủ 3 file canonical, và kiểm tra ranh giới Git tracking.
- Cung cấp bộ unit test hermetic đầy đủ (`test_setup_contracts.py`) kiểm thử mọi chức năng trong thư mục tạm cô lập.

### Ngoài phạm vi
- Không sinh code DTO ứng dụng cụ thể theo từng ngôn ngữ lập trình (Rust, Dart, Python). Nhiệm vụ đó thuộc về các bộ sinh code hoặc `dev-implementation`.
- Không thực hiện các thao tác Git remote hoặc push code lên server (bị nghiêm cấm theo Rule 3).

## 3. Quyết định Kiến trúc và Cấu trúc Topology

1. **Topology Hình sao (Star Topology SSOT)**:
   - Hub repository (`D3Nexus`) nắm giữ thư mục vật lý `shared-contracts/` và đóng vai trò là Nguồn Chân lý Duy nhất (SSOT).
   - Các Satellite repository (`lyrics-sync`, `nexus`) liên kết qua symbolic link tương đối một chiều tới domain tương ứng.
2. **Tiêu chuẩn Relative Symlink**:
   - Symlink BẮT BUỘC phải là đường dẫn tương đối (ví dụ `../D3Nexus/shared-contracts/lyrics-sync`), không bao giờ dùng đường dẫn tuyệt đối (`/Users/...`). Điều này bảo đảm tính di động trên nhiều máy và CI runners.
3. **Bộ ba Hợp đồng Canonical (Canonical Triad)**:
   - Mỗi thư mục domain trong `shared-contracts/<domain>/` BẮT BUỘC chứa đúng 3 file canonical:
     - `api_contract.md`: Endpoints, payload schemas, telemetry heartbeats, và error contracts.
     - `architecture_and_flow.md`: Pipeline steps, chuyển đổi trạng thái, cancellation fencing, và ranh giới cách ly.
     - `gaps_and_rfcs.md`: Sổ cái RFC và theo dõi các đề xuất thay đổi bất đồng bộ.
4. **Kiến trúc Luật Phân tầng 2 lớp (Two-Tier Rule Architecture)**:
   - Quy tắc khung toàn hệ thống nằm ở `CRITICAL_RULES.md` (Tầng Plugin).
   - Quy tắc kỹ thuật đặc thù nằm ở `.agents/rules/contract_rules.md` (Tầng Local Workspace), được cấu hình riêng cho Hub vs Satellite.

## 4. Cấu trúc Thư mục và các Thành phần

Skill mới được tổ chức như sau trong `ai-agent-tools`:

```text
skills/setup-shared-contracts/
├── SKILL.md
└── resources/
    ├── scripts/
    │   ├── setup_contracts.py
    │   └── test_setup_contracts.py
    └── templates/
        ├── api_contract.md.tmpl
        ├── architecture_and_flow.md.tmpl
        ├── gaps_and_rfcs.md.tmpl
        ├── hub_readme.md.tmpl
        ├── hub_rule.md.tmpl
        └── satellite_rule.md.tmpl
```

## 5. Đặc tả Kỹ thuật CLI Engine

Script CLI `setup_contracts.py` hỗ trợ 3 lệnh chính:

### 5.1 Lệnh: `init-hub`
```bash
python3 setup_contracts.py init-hub [--repo-root <hub_root>] [--domain <domain_name>] [--force]
```
- **Xác thực**: Kiểm tra bảo đảm `shared-contracts` không phải là một symlink (Hub bắt buộc là thư mục vật lý).
- **Hành động**:
  1. Tạo thư mục vật lý `<hub_root>/shared-contracts/`.
  2. Tạo `<hub_root>/shared-contracts/README.md` từ template `hub_readme.md.tmpl`.
  3. Nếu có tham số `--domain`:
     - Tạo thư mục `<hub_root>/shared-contracts/<domain>/`.
     - Tạo 3 file `api_contract.md`, `architecture_and_flow.md`, và `gaps_and_rfcs.md` từ template mẫu.
     - Thêm domain vào bảng Outbound Symlink Mappings trong `README.md`.
  4. Cài đặt `<hub_root>/.agents/rules/contract_rules.md` từ `hub_rule.md.tmpl`.

### 5.2 Lệnh: `link-satellite`
```bash
python3 setup_contracts.py link-satellite --hub <path_to_hub> --domain <domain_name> [--satellite-root <sat_root>] [--force]
```
- **Xác thực**:
  - Xác thực `<path_to_hub>` tồn tại và chứa thư mục `shared-contracts/<domain_name>/`.
  - Hủy bỏ nếu `<sat_root>/shared-contracts` là một thư mục vật lý không rỗng trừ khi có cờ `--force`.
- **Hành động**:
  1. Tính toán đường dẫn tương đối: `rel_target = os.path.relpath(hub_domain_dir, sat_root)`.
  2. Tạo symbolic link: `<sat_root>/shared-contracts -> rel_target`.
  3. Kiểm tra symlink phân giải an toàn trên đĩa (không bị dangling link).
  4. Cài đặt `<sat_root>/.agents/rules/contract_rules.md` từ `satellite_rule.md.tmpl`.
  5. Thêm hoặc cập nhật ghi chú luật SSOT Contract vào `<sat_root>/AGENTS.md` nếu file tồn tại.

### 5.3 Lệnh: `verify`
```bash
python3 setup_contracts.py verify [--repo-root <path>]
```
- **Hành động**:
  - Tự động nhận diện `<path>` là Hub Mode hay Satellite Mode.
  - Ở Hub Mode: Xác minh `shared-contracts/` là thư mục vật lý, `README.md` tồn tại, các thư mục domain chứa đủ 3 file canonical, và file `.agents/rules/contract_rules.md` hiện diện.
  - Ở Satellite Mode: Xác minh `shared-contracts` là symlink hợp lệ, trỏ tới thư mục chứa đủ 3 file canonical, và file `.agents/rules/contract_rules.md` hiện diện.
  - Thoát mã `0` khi thành công; thoát mã `1` kèm thông báo hướng dẫn sửa chữa khi thất bại.

## 6. Bộ Template Chuẩn hóa

Mỗi template trong `resources/templates/` sử dụng cú pháp `string.Template` chuẩn của Python với các biến định danh thay thế (ví dụ `$domain`, `$hub_repo`, `$timestamp`):

1. **`hub_readme.md.tmpl`**:
   - Định nghĩa tổng quan Star Topology và bảng Outbound Symlink Mappings.
   - Nhúng các điều luật bắt buộc cho AI Agents & Kỹ sư (Cấm thay đổi breaking đơn phương, Quy trình Contract-First, Sổ cái RFC).
2. **`api_contract.md.tmpl`**:
   - Đặc tả endpoints REST / SSE / IPC, headers (`X-Worker-Token`), và telemetry heartbeat.
   - Schema dữ liệu kết quả với cam kết tương thích ngược (giá trị mặc định an toàn).
3. **`architecture_and_flow.md.tmpl`**:
   - 7 Bước Pipeline Chuẩn, chuyển đổi State Machine, cancellation fencing (< 50ms), và dọn dẹp scratch file.
   - Ranh giới tính toán độc lập không trạng thái (stateless).
4. **`gaps_and_rfcs.md.tmpl`**:
   - Bảng theo dõi RFC Ledger và mẫu ghi nhận các đề xuất/gaps mới.
5. **`hub_rule.md.tmpl`**:
   - File rule cục bộ cho Hub repo thực thi quyền sở hữu SSOT, ưu tiên `task_01`, và phát hành Parallel Handoff.
6. **`satellite_rule.md.tmpl`**:
   - File rule cục bộ cho Satellite repo thực thi ranh giới Git chỉ đọc, cấm kết nối trực tiếp database, và quy trình Asynchronous RFC.

## 7. Chiến lược Kiểm thử và Xác minh

Bộ kiểm thử trong `resources/scripts/test_setup_contracts.py` thực thi dưới nền tảng `unittest` của Python:
- **Kiểm thử Khởi tạo Hub**: Xác minh cấu trúc thư mục, nội dung file, và tính bất biến khi chạy lặp lại (idempotency).
- **Kiểm thử Liên kết Satellite**: Tạo các thư mục giả lập anh em, tạo symlink, xác minh tính chuẩn xác của relative path và khả năng đọc file xuyên symlink.
- **Kiểm thử Phát hiện Dangling Link**: Xác minh đường dẫn Hub không hợp lệ hoặc thiếu domain sẽ kích hoạt lỗi thoát rõ ràng.
- **Kiểm thử Lệnh Verify**: Kiểm thử lệnh `verify` trên cả các thiết lập hợp lệ và bị hỏng, bảo đảm trả về đúng mã thoát.
- **Tích hợp Liên tục**: Tích hợp trực tiếp vào `scripts/verify.sh` như một phần của bộ kiểm tra phát hành repository.

## 8. Tích hợp Vòng đời và Trải nghiệm Agent

- **Điểm kích hoạt**: Kích hoạt khi lập trình viên yêu cầu khởi tạo contracts, kết nối các repo, hoặc gọi `/setup-shared-contracts`.
- **Tự động nhận diện**: Skill kiểm tra thư mục hiện tại và các thư mục cha để tự đề xuất khởi tạo Hub hay liên kết Satellite.
- **Phát hành Handoff**: Sau khi hoàn tất `link-satellite`, công cụ xuất ra các bước tiếp theo chính xác cho lập trình viên (chạy `verify` và tiến hành thiết kế với `dev-designer`).

## 9. Xử lý Lỗi và các Trường hợp Biên

| Kịch bản | Được xử lý bởi | Hành vi |
|---|---|---|
| Người dùng chạy `init-hub` trong satellite repo | `init-hub` | Phát hiện `islink('shared-contracts')`, dừng với lỗi: "Không thể init hub trên một symlink". |
| Người dùng chạy `link-satellite` với hub không tồn tại | `link-satellite` | Xác thực đường dẫn đích, dừng với lỗi: "Không tìm thấy thư mục domain của Hub". |
| Thư mục `shared-contracts` ở satellite là thư mục thật | `link-satellite` | Dừng với lỗi trừ khi có cờ `--force`. |
| Các file đã tồn tại có nguy cơ bị ghi đè | Tất cả lệnh | Mặc định giữ nguyên file cũ trừ khi truyền cờ `--force`. |

## 10. Rủi ro và Biện pháp Giảm thiểu

- **Rủi ro: Phá vỡ các contract đang có khi chạy lại lệnh.**
  *Biện pháp*: CLI không bao giờ tự ý ghi đè các file contract đã tồn tại; file cũ luôn được bảo toàn trừ khi chỉ định rõ `--force`.
- **Rủi ro: Đường dẫn tuyệt đối bị ghi cứng vào symlink.**
  *Biện pháp*: Script sử dụng độc quyền hàm `os.path.relpath()` để tính toán đường dẫn tương đối, bảo đảm tính di động tuyệt đối trên mọi máy.
- **Rủi ro: Sai lệch so với CRITICAL_RULES.**
  *Biện pháp*: Các template tích hợp trực tiếp nội dung chính xác từ Rule 7 của `CRITICAL_RULES.md`.

