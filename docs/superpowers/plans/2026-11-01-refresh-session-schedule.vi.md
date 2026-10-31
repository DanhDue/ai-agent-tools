# Kế Hoạch Triển Khai Lập Lịch & Tự Động Hóa Daemon Cho Refresh Session

> **Dành cho agent thực thi:** SUB-SKILL BẮT BUỘC: Sử dụng d3nexus:subagent-driven-development (khuyến nghị) hoặc d3nexus:executing-plans để triển khai kế hoạch này theo từng tác vụ. Các bước sử dụng cú pháp checkbox (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu:** Nâng cấp `refresh_session.py` và `skills/refresh-session/SKILL.md` để hỗ trợ lập lịch chạy tự động hàng ngày qua macOS `launchd` (với cơ chế dự phòng `crontab` trên Linux), cho phép lập trình viên lệch pha chu kỳ cuốn 5 giờ (ví dụ: lúc 05:00 AM hoặc 06:00 AM) trong khi vẫn duy trì tương thích ngược 100% cho các lệnh ping thủ công tức thì.

**Kiến trúc:** Bổ sung subcommand `schedule` trong `skills/refresh-session/resources/scripts/refresh_session.py` để phân tích các định dạng giờ linh hoạt (`05:00`, `5h`, `6am`), tạo và đăng ký daemon hệ điều hành native (`~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` qua `launchctl` trên macOS, user crontab trên Linux), truy vấn trạng thái daemon hoạt động, và hủy lịch sạch sẽ. Mọi luồng chạy thủ công hiện có được giữ nguyên 100%.

**Tech Stack:** Python 3.10+ (Standard Library: `argparse`, `pathlib`, `re`, `subprocess`, `sys`, `unittest`), macOS `launchd`, Linux `cron`, bash, markdown.

**Bản đặc tả:** [2026-11-01-refresh-session-schedule-design.vi.md](../specs/2026-11-01-refresh-session-schedule-design.vi.md)  
**Cẩm nang tra cứu:** [docs/refresh-session-quick-guide.vi.md](../../refresh-session-quick-guide.vi.md)

## Mục Lục

- [Ràng Buộc Toàn Cục](#ràng-buộc-toàn-cục)
- [Cấu Trúc Tệp Tin](#cấu-trúc-tệp-tin)
- [Các Tác Vụ](#các-tác-vụ)
  - [Tác vụ 1: Bộ Phân Tích Giờ Linh Hoạt, Trình Tạo Dịch Vụ và Unit Tests Toàn Diện](#tác-vụ-1-bộ-phân-tích-giờ-linh-hoạt-trình-tạo-dịch-vụ-và-unit-tests-toàn-diện)
  - [Tác vụ 2: Cập Nhật Tài Liệu Kỹ Năng và Xác Thực Thực Tế](#tác-vụ-2-cập-nhật-tài-liệu-kỹ-năng-và-xác-thực-thực-tế)
- [Xác Thực Cuối Cùng](#xác-thực-cuối-cùng)

---

## Ràng Buộc Toàn Cục

- **Tương Thích Ngược 100%**: Tất cả các lệnh gọi hiện có (`refresh_session.py [all|claude|codex]`, `--json`, `--timeout`) BẮT BUỘC tiếp tục hoạt động mà không cần sửa đổi.
- **Chỉ Dùng Thư Viện Tiêu Chuẩn Python**: Không cài thêm bất kỳ pip dependency bên ngoài nào.
- **Hệ Thống Init Native Của OS**: Sử dụng `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` với `launchctl` trên macOS (`darwin`); dùng user `crontab` trên Linux (`linux`).
- **Không Đòi Hỏi Quyền Sudo**: Phải chạy hoàn toàn trong user space mà không yêu cầu quyền root/sudo.
- **Phân Giải Đường Dẫn Tuyệt Đối**: Cấu hình daemon phải phân giải đường dẫn tuyệt đối chuẩn xác (`pathlib.Path(__file__).resolve()`) để lệnh chạy thành công từ bất kỳ thư mục làm việc nào.
- **Tiêu Chuẩn Frontmatter SKILL.md**:
  - Đúng 2 key: `name` và `description` (không thêm key khác).
  - `name`: `refresh-session`.
- **Định Dạng Commit**:
  - Định dạng: `[REFRESH_SESSION] <tiêu đề>` kèm danh sách gạch đầu dòng các thay đổi.
  - Tuyệt đối không thêm dòng trailer hay ghi nhận công cụ (`Co-Authored-By:`, `Generated with`).
- **Cổng Kiểm Tra Chất Lượng**:
  - Tất cả các test phải vượt qua qua `scripts/verify.sh`.

---

## Cấu Trúc Tệp Tin

| Tệp Tin | Hành Động | Trách Nhiệm |
|---|---|---|
| `skills/refresh-session/resources/scripts/refresh_session.py` | Chỉnh sửa | Cài đặt `parse_flexible_time`, `build_darwin_plist`, các hàm xử lý install/status/uninstall và bộ phân tích CLI `schedule`. |
| `skills/refresh-session/resources/scripts/test_refresh_session.py` | Chỉnh sửa | Bổ sung unit tests toàn diện cho parsing giờ, tạo plist, cài đặt lịch, kiểm tra trạng thái và hủy lịch. |
| `skills/refresh-session/SKILL.md` | Chỉnh sửa | Cập nhật tài liệu kỹ năng với subcommand `schedule`, các tham số và câu lệnh ngôn ngữ tự nhiên. |

---

## Các Tác Vụ

### Tác vụ 1: Bộ Phân Tích Giờ Linh Hoạt, Trình Tạo Dịch Vụ và Unit Tests Toàn Diện

**Tệp tin:**
- Chỉnh sửa: `skills/refresh-session/resources/scripts/test_refresh_session.py`
- Chỉnh sửa: `skills/refresh-session/resources/scripts/refresh_session.py`

- [ ] **Bước 1: Viết unit tests kiểm tra tính năng lập lịch (RED)**
  Bổ sung các test case trong `skills/refresh-session/resources/scripts/test_refresh_session.py`:
  - `test_parse_flexible_time_24h`: Xác nhận `"05:00" -> (5, 0)`, `"14:30" -> (14, 30)`, `"9:15" -> (9, 15)`.
  - `test_parse_flexible_time_short`: Xác nhận `"5h" -> (5, 0)`, `"6h" -> (6, 0)`, `"14h" -> (14, 0)`, `"5" -> (5, 0)`.
  - `test_parse_flexible_time_ampm`: Xác nhận `"5am" -> (5, 0)`, `"5:30am" -> (5, 30)`, `"6pm" -> (18, 0)`, `"12pm" -> (12, 0)`, `"12am" -> (0, 0)`.
  - `test_parse_flexible_time_invalid`: Đảm bảo ném `ValueError` đối với `"25:00"`, `"-1h"`, `"abc"`, `""`, `"5:65"`.
  - `test_build_darwin_plist`: Xác nhận XML sinh ra chứa label `com.d3nexus.refresh-session`, đúng giờ, phút, python executable, đường dẫn script và file log tuyệt đối.
  - `test_schedule_install_darwin`: Mock `subprocess.run` và hệ thống tệp để kiểm tra ghi plist và `launchctl load`.
  - `test_schedule_status_darwin_active`: Kiểm tra báo cáo trạng thái khi plist tồn tại và `launchctl list` tìm thấy label.
  - `test_schedule_status_darwin_inactive`: Kiểm tra báo cáo trạng thái khi chưa cài đặt lịch.
  - `test_schedule_uninstall_darwin`: Kiểm tra gọi lệnh `launchctl unload` và xóa file plist.
  - `test_parse_arguments_schedule_subcommand`: Kiểm tra parsing CLI đối với `schedule --time 05:00`, `schedule --status`, `schedule --uninstall`, `--remove`, và `--target`.

- [ ] **Bước 2: Chạy unit tests để xác nhận lỗi ban đầu (RED)**
  Chạy: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Xác nhận các hàm test mới báo lỗi.

- [ ] **Bước 3: Triển khai bộ phân tích giờ, sinh daemon và xử lý CLI (GREEN)**
  Trong `skills/refresh-session/resources/scripts/refresh_session.py`:
  - Triển khai `parse_flexible_time(time_str: str) -> tuple[int, int]`:
    - Hỗ trợ các mẫu regex cho `HH:MM`, `Hh`, `H`, `H[:MM]am|pm`.
    - Kiểm tra tính hợp lệ `0 <= hour <= 23` và `0 <= minute <= 59`.
  - Triển khai `build_darwin_plist(script_path: str, hour: int, minute: int, target: str) -> str`:
    - Mở rộng `~` thành đường dẫn tuyệt đối qua `Path.home()` (launchd không mở rộng dấu ngã).
    - Bảo đảm tạo thư mục cha `~/.devtool/logs` và `~/Library/LaunchAgents`.
    - Chèn `<key>EnvironmentVariables</key><dict><key>PATH</key><string>...</string></dict>` sử dụng `os.environ.get("PATH")` hoặc các thư mục binary chuẩn (`/opt/homebrew/bin:/usr/local/bin:~/.local/bin:/usr/bin:/bin`) để `claude` và `codex` luôn được tìm thấy.
    - Sinh XML launchd chuẩn với `StartCalendarInterval`, ghi log ra `{HOME}/.devtool/logs/refresh_session_daemon.{log,err}`.
  - Triển khai `install_schedule(hour: int, minute: int, target: str) -> dict[str, Any]`:
    - Nếu `darwin`: Ghi plist vào `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`, chạy `launchctl unload` nếu có từ trước, rồi chạy `launchctl load`.
    - Nếu `linux`: Quản lý các dòng crontab với cặp thẻ phân tách.
  - Triển khai `get_schedule_status() -> dict[str, Any]`:
    - Kiểm tra sự tồn tại của plist / crontab và trạng thái qua `launchctl list`.
  - Triển khai `uninstall_schedule() -> dict[str, Any]`:
    - Gọi unload và xóa plist / gỡ bỏ khối crontab.
  - Cập nhật `parse_args()`:
    - Hỗ trợ subcommand `schedule [...]` song song với cú pháp cũ `refresh_session.py [target]`.
    - Hỗ trợ cờ `--remove` tương đương `--uninstall`, và cờ `--target [all|claude|codex]` cho `schedule`.
  - Cập nhật `main()`:
    - Điều phối các hành động của `schedule` hoặc chạy `run_refresh()` cho các target thủ công.

- [ ] **Bước 4: Chạy lại unit tests để xác nhận toàn bộ xanh (GREEN)**
  Chạy: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Xác nhận tất cả bài test đều PASS.

- [ ] **Bước 5: Kiểm tra chất lượng mã nguồn và linting**
  - Chạy `ruff check skills/refresh-session/resources/scripts/`
  - Đảm bảo không có cảnh báo hay vi phạm phong cách mã.

- [ ] **Bước 6: Commit các thay đổi của Tác vụ 1**
  ```bash
  git add skills/refresh-session/resources/scripts/
  git commit -m "[REFRESH_SESSION] Implement flexible scheduling engine and unit tests" -m "- Add flexible time parser supporting 24h, short hour, and am/pm formats
  - Add native macOS launchd plist generation, installation, status, and uninstall handlers
  - Add unit tests covering time parsing, plist building, and lifecycle management"
  ```

---

### Tác vụ 2: Cập Nhật Tài Liệu Kỹ Năng và Xác Thực Thực Tế

**Tệp tin:**
- Chỉnh sửa: `skills/refresh-session/SKILL.md`

- [ ] **Bước 1: Cập nhật tài liệu kỹ năng**
  Cập nhật `skills/refresh-session/SKILL.md`:
  - Mô tả bảng lệnh đầy đủ gồm cả chế độ thủ công và lập lịch.
  - Giải thích chiến thuật lệch pha chu kỳ lúc 05:00 AM.
  - Bổ sung ví dụ câu lệnh ngôn ngữ tự nhiên.
  - Trích dẫn liên kết tới `docs/refresh-session-quick-guide.en.md` và `.vi.md`.
  - Bảo đảm frontmatter giữ đúng 2 key: `name` và `description`.

- [ ] **Bước 2: Smoke test thực tế trên máy host**
  - Thử cài đặt lịch: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00`
  - Kiểm tra output trạng thái: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --status`
  - Xác thực file plist tồn tại: `test -f ~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`
  - Thử gỡ lịch: `python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --uninstall`
  - Xác thực file plist đã bị xóa: `! test -f ~/Library/LaunchAgents/com.d3nexus.refresh-session.plist`
  - Xác thực lệnh thủ công cũ vẫn hoạt động: `python3 skills/refresh-session/resources/scripts/refresh_session.py --json`

- [ ] **Bước 3: Chạy bộ kiểm tra chất lượng repository**
  Chạy: `bash scripts/verify.sh`
  Xác nhận toàn bộ 16 section đều PASS.

- [ ] **Bước 4: Commit các thay đổi của Tác vụ 2**
  ```bash
  git add skills/refresh-session/SKILL.md
  git commit -m "[REFRESH_SESSION] Update skill documentation with scheduling reference" -m "- Document schedule subcommand in SKILL.md
  - Add natural language prompts and quick-guide references
  - Pass all 16 sections in verify.sh"
  ```

---

## Xác Thực Cuối Cùng

1. `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py` $\rightarrow$ Toàn bộ tests pass.
2. `bash scripts/verify.sh` $\rightarrow$ `PASS — safe to publish`.
3. Lệnh thủ công `python3 skills/refresh-session/resources/scripts/refresh_session.py claude` $\rightarrow$ Hoạt động tốt.
4. Quy trình cài đặt / kiểm tra / gỡ lịch $\rightarrow$ Hoạt động trơn tru trên macOS.
