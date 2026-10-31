# Kế hoạch Triển khai Refresh Session

> **Dành cho các agent thực thi:** KỸ NĂNG PHỤ BẮT BUỘC: Sử dụng d3nexus:subagent-driven-development (khuyến nghị) hoặc d3nexus:executing-plans để triển khai kế hoạch này theo từng tác vụ. Các bước sử dụng cú pháp ô đánh dấu (`- [ ]`) để theo dõi tiến độ.

**Mục tiêu:** Cung cấp skill `/refresh-session` cùng công cụ thực thi độc lập (`refresh_session.py`) để gửi tín hiệu ping tối thiểu 1 ký tự đến Claude Code CLI và Codex CLI nhằm khởi tạo sớm hoặc làm mới chu kỳ hạn mức rolling 5 giờ với lượng token gần như bằng 0 và triệt tiêu hoàn toàn việc khởi tạo skill/plugin/MCP.

**Kiến trúc:** Một script Python độc lập (`skills/refresh-session/resources/scripts/refresh_session.py`) tạo thư mục tạm thời độc lập bên ngoài cây mã nguồn dự án, thực thi các lệnh CLI trong môi trường sandbox với các cờ triệt tiêu context mạnh mẽ, phân tích số lượng token và độ trễ, đồng thời xuất báo cáo rõ ràng. Một tài liệu skill chuẩn hóa (`skills/refresh-session/SKILL.md`) điều hướng lệnh `/refresh-session [claude|codex|all]` đến engine xử lý.

**Công nghệ sử dụng:** Python 3.10+ (Thư viện chuẩn: `argparse`, `shutil`, `subprocess`, `tempfile`, `time`, `json`, `unittest`), bash, markdown.

**Tài liệu thiết kế:** [2026-11-01-refresh-session-design.vi.md](../specs/2026-11-01-refresh-session-design.vi.md)

## Mục lục

- [Ràng buộc Toàn cục](#ràng-buộc-toàn-cục)
- [Cấu trúc Tệp](#cấu-trúc-tệp)
- [Các Tác vụ](#các-tác-vụ)
  - [Tác vụ 1: Engine Python Cốt lõi và Bộ Unit Test Toàn diện](#tác-vụ-1-engine-python-cốt-lõi-và-bộ-unit-test-toàn-diện)
  - [Tác vụ 2: Định nghĩa Skill và Tích hợp vào Kịch bản Kiểm định](#tác-vụ-2-định-nghĩa-skill-và-tích-hợp-vào-kịch-bản-kiểm-định)
- [Xác thực Cuối cùng](#xác-thực-cuối-cùng)

---

## Ràng buộc Toàn cục

- **Cô lập Tuyệt đối**: Cả `claude` và `codex` phải luôn chạy bên trong một thư mục tạm thời rỗng (`tempfile.TemporaryDirectory`) để tránh quét tệp workspace hoặc nạp `.rules`.
- **Triệt tiêu Hoàn toàn Skill/Plugin/MCP**:
  - Claude: `--safe-mode --disable-slash-commands --tools "" --model haiku -p "1"`. Tuyệt đối không dùng `--bare` vì cờ này bỏ qua OAuth trong keychain của trình duyệt.
  - Codex: `--disable plugins --disable apps --disable hooks --ephemeral --skip-git-repo-check --ignore-user-config --ignore-rules -c model_reasoning_effort=low "1"`.
- **Tiêu chuẩn Mã nguồn**:
  - Chỉ sử dụng thư viện chuẩn của Python (zero third-party dependencies).
  - Khai báo kiểu nghiêm ngặt vượt qua kiểm tra `mypy --strict --follow-imports=silent`.
  - Không vi phạm linting, vượt qua `ruff check`.
- **Tiêu chuẩn Frontmatter SKILL.md**:
  - Đúng 2 khóa duy nhất: `name` và `description` (không thêm bất kỳ khóa nào khác).
  - `name`: `refresh-session`.
  - `description`: Ngôi thứ ba, nêu rõ làm gì và khi nào sử dụng.
- **Quy chuẩn Commit**:
  - Định dạng thông điệp: `[REFRESH_SESSION] <title>` kèm danh sách gạch đầu dòng các thay đổi.
  - Tuyệt đối không chèn trailer line hay ghi nhận công cụ (`Co-Authored-By:`, `Generated with`).
- **Cổng Kiểm định**:
  - Tất cả các bài kiểm tra phải vượt qua `scripts/verify.sh`.

---

## Cấu trúc Tệp

| Tệp | Trách nhiệm |
|---|---|
| `skills/refresh-session/resources/scripts/refresh_session.py` | Tạo mới. Engine CLI độc lập thực thi các lệnh ping sandbox tới Claude và Codex. |
| `skills/refresh-session/resources/scripts/test_refresh_session.py` | Tạo mới. Bộ unit test toàn diện kiểm tra phân tích tham số, lắp ráp lệnh, cô lập sandbox, bóc tách token và xử lý timeout. |
| `skills/refresh-session/SKILL.md` | Tạo mới. Tài liệu định nghĩa skill chuẩn hóa với YAML frontmatter 2 khóa. |
| `scripts/verify.sh` | Chỉnh sửa. Đăng ký `test_refresh_session.py` vào bộ test ở mục 11. |

---

## Các Tác vụ

### Tác vụ 1: Engine Python Cốt lõi và Bộ Unit Test Toàn diện

**Tệp thay đổi:**
- Tạo mới: `skills/refresh-session/resources/scripts/refresh_session.py`
- Tạo mới: `skills/refresh-session/resources/scripts/test_refresh_session.py`

- [x] **Bước 1: Viết unit test thất bại (RED)**
  Tạo `skills/refresh-session/resources/scripts/test_refresh_session.py` với các ca kiểm thử:
  - `test_parse_arguments_default`: Kiểm tra target mặc định là `"all"`, timeout mặc định là `60`, json là `False`.
  - `test_parse_arguments_targets`: Kiểm tra phân tích đúng các target `"claude"`, `"codex"`, và `"all"`.
  - `test_parse_arguments_invalid_target`: Kiểm tra trả về lỗi khi target không hợp lệ.
  - `test_build_claude_command`: Xác nhận đúng danh sách cờ: `["claude", "--safe-mode", "--disable-slash-commands", "--tools", "", "--model", "haiku", "-p", "1"]`.
  - `test_build_codex_command`: Xác nhận đúng danh sách cờ: `["codex", "exec", "--disable", "plugins", "--disable", "apps", "--disable", "hooks", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config", "--ignore-rules", "-c", "model_reasoning_effort=low", "1"]`.
  - `test_extract_token_usage`: Kiểm tra regex bóc tách lượng token từ các mẫu stdout (`tokens used <N>`, `Tokens: <N>`).
  - `test_run_ping_missing_cli`: Mock `shutil.which` trả về `None`; kiểm tra trạng thái bỏ qua an toàn mà không văng ngoại lệ.
  - `test_run_ping_success_mocked`: Mock `subprocess.run` trong thư mục tạm thời; kiểm tra việc chạy lệnh, đo độ trễ và trả về kết quả dict.
  - `test_run_ping_timeout_mocked`: Mock `subprocess.TimeoutExpired`; kiểm tra báo lỗi timeout rõ ràng.
  - `test_main_json_output`: Kiểm tra tùy chọn `--json` xuất ra chuỗi JSON đúng cấu trúc.

- [x] **Bước 2: Chạy kiểm thử để xác nhận trạng thái RED**
  Chạy: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Kỳ vọng: Lỗi ModuleNotFoundError hoặc FAILED vì chưa tạo `refresh_session.py`.

- [x] **Bước 3: Hiện thực `refresh_session.py` (GREEN)**
  Tạo `skills/refresh-session/resources/scripts/refresh_session.py`:
  - `build_claude_command(prompt: str = "1", model: str = "haiku") -> list[str]`
  - `build_codex_command(prompt: str = "1", reasoning_effort: str = "low") -> list[str]`
  - `extract_tokens(output: str) -> int | None`
  - `ping_cli(cli_name: str, timeout: int = 60) -> dict[str, Any]` thực thi trong `tempfile.TemporaryDirectory()` trả về cấu trúc chuẩn `{"cli": str, "status": "PASS" | "SKIPPED" | "FAIL", "latency_ms": float, "tokens": int | None, "error": str | None}`
  - `main(argv: list[str] | None = None) -> int` với `argparse`, tóm tắt console thân thiện và hỗ trợ JSON output.

- [x] **Bước 4: Chạy kiểm thử để xác nhận trạng thái GREEN**
  Chạy: `python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py`
  Kỳ vọng: Tất cả bài test đều PASS.

- [x] **Bước 5: Kiểm tra linting và typing**
  Chạy:
  - `ruff check skills/refresh-session/resources/scripts/`
  - `mypy --strict --follow-imports=silent skills/refresh-session/resources/scripts/refresh_session.py skills/refresh-session/resources/scripts/test_refresh_session.py`
  Kỳ vọng: Thoát mã 0 sạch sẽ.

- [x] **Bước 6: Commit Tác vụ 1**
  Stage và commit:
  ```bash
  git add skills/refresh-session/resources/scripts/
  git commit -m "[REFRESH_SESSION] Implement refresh_session.py engine and unit tests" -m "- Add sandboxed CLI command builders for Claude and Codex
  - Add TemporaryDirectory isolation ensuring zero repository context scan
  - Add comprehensive unit test suite covering argument parsing and mocking"
  ```

---

### Tác vụ 2: Định nghĩa Skill và Tích hợp vào Kịch bản Kiểm định

**Tệp thay đổi:**
- Tạo mới: `skills/refresh-session/SKILL.md`
- Chỉnh sửa: `scripts/verify.sh`

- [x] **Bước 1: Tạo `skills/refresh-session/SKILL.md`**
  Soạn thảo `skills/refresh-session/SKILL.md`:
  - Frontmatter:
    ```yaml
    ---
    name: refresh-session
    description: Ping Claude Code and Codex CLIs to refresh 5-hour rolling session windows with minimum token consumption and zero skill initialization.
    ---
    ```
  - Các phần nội dung:
    - Tổng quan và mục đích khởi động sớm chu kỳ hạn mức.
    - Hướng dẫn cú pháp `/refresh-session`, `/refresh-session claude`, `/refresh-session codex`, và `/refresh-session all`.
    - Hướng dẫn AI agent gọi `python3 skills/refresh-session/resources/scripts/refresh_session.py <target>`.
    - Giải thích cam kết sandbox cô lập và triệt tiêu token.

- [x] **Bước 2: Đăng ký vào `scripts/verify.sh`**
  Thêm Mục 16 vào `scripts/verify.sh` ngay trước mục tổng kết:
  ```bash
  echo "== 16. Session refresh CLI engine and isolation contracts are enforced =="
  python3 -m unittest skills/refresh-session/resources/scripts/test_refresh_session.py || FAILED=1
  ```

- [x] **Bước 3: Chạy kịch bản kiểm định toàn trình**
  Chạy: `bash scripts/verify.sh`
  Kỳ vọng: Toàn bộ 15 cổng kiểm tra đều PASS (`PASS — safe to publish`).

- [x] **Bước 4: Commit Tác vụ 2**
  Stage và commit:
  ```bash
  git add skills/refresh-session/SKILL.md scripts/verify.sh
  git commit -m "[REFRESH_SESSION] Add refresh-session skill and wire into verify.sh" -m "- Author refresh-session/SKILL.md with standardized 2-key frontmatter
  - Register test_refresh_session.py in scripts/verify.sh test suite"
  ```

---

## Xác thực Cuối cùng

- [x] **Kiểm thử Thực thi CLI Trực tiếp**:
  Chạy: `python3 skills/refresh-session/resources/scripts/refresh_session.py all`
  Xác nhận cả Claude và Codex đều phản hồi thành công trong thư mục tạm rỗng.
- [x] **Kiểm thử Định dạng JSON**:
  Chạy: `python3 skills/refresh-session/resources/scripts/refresh_session.py all --json`
  Xác nhận JSON hợp lệ với `status: "PASS"`, cùng các trường độ trễ và token.
- [x] **Kiểm tra Chất lượng Tài liệu**:
  Chạy: `python3 skills/doc_quality_check/resources/scripts/check_document.py docs/superpowers/plans/2026-11-01-refresh-session.en.md docs/superpowers/plans/2026-11-01-refresh-session.vi.md`
  Xác nhận 0 findings.
- [x] **Cổng Kiểm tra Cuối cùng của Kho mã nguồn**:
  Chạy: `bash scripts/verify.sh`
  Đảm bảo mã thoát 0 sạch sẽ.

