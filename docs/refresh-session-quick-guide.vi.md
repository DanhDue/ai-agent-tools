# Cẩm Nang Tra Cứu Nhanh: `/refresh-session` & Lập Lịch Quota

Cẩm nang tra cứu và bảng cheat-sheet hoàn chỉnh cho việc pre-warm, quản lý và lập lịch chu kỳ 5 giờ cho Claude Code CLI (`claude`) và OpenAI Codex CLI (`codex`).

---

## 1. Chiến Thuật: Lệch Pha Chu Kỳ (Rolling Window Staggering)

Cả Claude Code và Codex đều áp dụng **cửa sổ giới hạn cuốn 5 giờ** kích hoạt ngay từ prompt đầu tiên. Nếu bạn bắt đầu làm việc lúc 08:00 AM mà không pre-warm, việc dùng nhiều có thể khiến bạn chạm trần lúc 10:00 AM và bị khóa tới 01:00 PM (13:00).

Bằng cách lập lịch tự động gửi ping 1-token lúc **05:00 AM** (hoặc trước giờ làm việc 2–3 tiếng):

```text
05:00 AM                 08:00 AM                      10:00 AM                      03:00 PM (15:00)
   │                        │                             │                                 │
   ▼                        ▼                             ▼                                 ▼
[Ping Tự Động]       [Bắt Đầu Làm Việc]            [KHỐI 1 HẾT HẠN]                  [Khối 2 Kết Thúc]
Khối 1 Kích Hoạt     Dùng Quota Khối 1             Khối 2 Mở Ra                      Làm việc liên tục
(cửa sổ 5h)          (Dung lượng đầy 100%)         (Dung lượng đầy 100% mới)         không bị gián đoạn
                     ────────────────────────►     ─────────────────────────────────────────►
                          2h tập trung cao                       5h tập trung cao
```

- **05:00 AM**: Ping tự động kích hoạt Khối 1 ($05:00 \rightarrow 10:00$).
- **08:00 AM**: Bạn bắt đầu làm việc với trọn vẹn hạn mức Khối 1 trong 2 tiếng đầu.
- **10:00 AM**: Đúng 5 giờ sau ping lúc 05:00 AM, Khối 1 hết hạn. Khối 2 tự động mở ra với 100% hạn mức mới!
- **Kết quả**: Bạn làm việc liên tục từ **08:00 AM đến 03:00 PM (7 tiếng liền mạch)** mà không bao giờ bị khựng lại giữa buổi sáng.

---

## 2. Bảng Tra Cứu Toàn Bộ Câu Lệnh (Command Cheat-Sheet)

Bạn có thể chạy các lệnh này dưới dạng Slash Command trong IDE (`/refresh-session ...`) hoặc trực tiếp qua Terminal CLI.

### 2.1. Bảng Tra Cứu Slash Command Trong Chat

| Cú Pháp Lệnh | Chế Độ | Hành Vi Thực Thi |
|:---|:---:|:---|
| `/refresh-session` *(hoặc `/refresh-session providers`)* | **Thủ công** | **Mặc định**: Chỉ ping các AI Providers (Claude Code và OpenAI Codex) ngay lập tức. |
| `/refresh-session profiles` | **Thủ công** | Ping toàn bộ tất cả 23 profiles Antigravity. |
| `/refresh-session danhdue, claude, codex` | **Thủ công** | Chỉ ping đúng danh sách profiles và providers được chỉ định. |
| `/refresh-session all` | **Thủ công** | Ping đồng thời cả Claude, Codex VÀ toàn bộ 23 profiles Antigravity. |
| `/refresh-session claude` | **Thủ công** | Chỉ ping riêng Claude Code ngay lập tức. |
| `/refresh-session codex` | **Thủ công** | Chỉ ping riêng OpenAI Codex ngay lập tức. |
| `/refresh-session schedule <time>` | **Lập lịch** | Cài đặt daemon hệ điều hành chạy hàng ngày vào mốc giờ chỉ định (`5h`, `05:00`, `6am`, `06:30`) với bộ đệm trễ mặc định 30s. |
| `/refresh-session schedule <time> --target <tgt>` | **Lập lịch** | Lập lịch hàng ngày cho riêng một target (`claude`, `codex`, `all`). |
| `/refresh-session schedule <time> --delay <giây>` | **Lập lịch** | Lập lịch hàng ngày với bộ đệm trễ tùy chọn (`--offset <giây>`). |
| `/refresh-session schedule status` | **Kiểm tra** | Kiểm tra daemon có đang hoạt động không và hiển thị mốc giờ cùng bộ đệm trễ. |
| `/refresh-session schedule remove` *(hoặc `uninstall`)* | **Hủy lịch** | Tắt và xóa daemon hệ điều hành đã lập lịch. |

---

### 2.2. Bảng Tra Cứu Lệnh Terminal CLI

```bash
# === Chạy Thủ Công Tức Thì ===
python3 skills/refresh-session/resources/scripts/refresh_session.py all
python3 skills/refresh-session/resources/scripts/refresh_session.py claude
python3 skills/refresh-session/resources/scripts/refresh_session.py codex
python3 skills/refresh-session/resources/scripts/refresh_session.py all --json

# === Quản Lý Lịch Chạy Hàng Ngày (Mặc định delay 30s) ===
# Cài lịch chạy lúc 5:00 AM mỗi ngày (ping lúc 05:00:30)
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00

# Cài lịch chạy lúc 6:00 AM riêng cho Claude
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 6h --target claude

# Cài lịch chạy với bộ đệm trễ tùy chọn 45 giây
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --time 05:00 --delay 45

# Kiểm tra trạng thái lịch
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --status

# Hủy lịch chạy hàng ngày
python3 skills/refresh-session/resources/scripts/refresh_session.py schedule --uninstall
```

---

## 3. Câu Lệnh Bằng Ngôn Ngữ Tự Nhiên

Bạn cũng có thể ra lệnh tự nhiên cho AI Agent trong khung chat:

- *"Pre-warm session ngay bây giờ"* $\rightarrow$ Chạy `/refresh-session all`
- *"Ping Claude đi"* $\rightarrow$ Chạy `/refresh-session claude`
- *"Lên lịch refresh session lúc 5h sáng mỗi ngày"* $\rightarrow$ Chạy `schedule --time 05:00` (áp dụng delay 30s)
- *"Hẹn giờ chạy refresh lúc 6am"* $\rightarrow$ Chạy `schedule --time 6am`
- *"Kiểm tra lịch refresh session"* $\rightarrow$ Chạy `schedule --status`
- *"Tắt lịch tự động refresh session"* $\rightarrow$ Chạy `schedule --uninstall`

---

## 4. Chi Tiết Kỹ Thuật Dưới Nền Tảng

- **macOS Daemon**: `~/Library/LaunchAgents/com.d3nexus.refresh-session.plist` (quản lý qua `launchctl` của macOS).
- **Linux Crontab**: Dòng lệnh crontab của user được bọc trong `# BEGIN d3nexus-refresh-session`.
- **Bộ Đệm Trễ An Toàn 30 Giây**: Tự động kích hoạt khi lên lịch (`--delay 30`). Khi daemon OS thức giấc lúc 05:00:00, script sẽ ngủ 30 giây để đảm bảo worker reset quota trên cloud hoàn tất chu kỳ trước khi gửi ping lúc 05:00:30.
- **Đường Dẫn Log**:
  - Standard Output: `~/.devtool/logs/refresh_session_daemon.log`
  - Error Output: `~/.devtool/logs/refresh_session_daemon.err`
- **Bảo Đảm Tiết Kiệm Token Tuyệt Đối**: Mọi lượt chạy đều được thực thi trong thư mục tạm cô lập nằm ngoài repository, vô hiệu hóa hoàn toàn skills, plugins, hooks và MCP servers.

