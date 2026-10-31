# Thiết Kế Header Báo Cáo Review Triage và Cấu Hình Mặc Định Theo Provider

## Mục Lục

- [Tóm Tắt](#tóm-tắt)
- [Mục Tiêu và Phạm Vi Ngoài Mục Tiêu](#mục-tiêu-và-phạm-vi-ngoài-mục-tiêu)
- [Cảnh Báo Hợp Đồng Dùng Chung](#cảnh-báo-hợp-đồng-dùng-chung)
- [Quyết Định Đã Thống Nhất](#quyết-định-đã-thống-nhất)
- [Thiết Kế Chi Tiết](#thiết-kế-chi-tiết)
  - [Cấu Trúc Tệp Cấu Hình Review](#cấu-trúc-tệp-cấu-hình-review)
  - [Đặc Tả Định Dạng Header Chuẩn](#đặc-tả-định-dạng-header-chuẩn)
  - [Ma Trận Ánh Xạ Thinking Level và Cờ Thực Thi CLI](#ma-trận-ánh-xạ-thinking-level-và-cờ-thực-thi-cli)
  - [Thuật Toán Phân Giải và Lưu Trữ Bền Vững Trong run_external_review.py](#thuật-toán-phân-giải-và-lưu-trữ-bền-vững-trong-run_external_reviewpy)
  - [Tích Hợp Skills và Quy Trình](#tích-hợp-skills-và-quy-trình)
- [Chiến Lược Kiểm Thử](#chiến-lược-kiểm-thử)
- [Danh Sách Tệp Thay Đổi](#danh-sách-tệp-thay-đổi)
- [Rủi Ro và Giảm Thiểu](#rủi-ro-và-giảm-thiểu)

## Tóm Tắt

Tài liệu này chuẩn hóa cách trình bày phần tóm tắt kết quả review triage trên cả hai quy trình **Principal Review** (kiểm định kiến trúc Shift-Left) và **Cross-Model Review** (kiểm định mã nguồn Shift-Right), bắt buộc xuất hiện header đồng nhất gồm đúng 4 gạch đầu dòng: Candidate SHA, Reviewer (`CLI ( Model )`), Thinking Level, và Verdict kèm số lượng findings. Đồng thời, tài liệu thiết kế cơ chế lưu trữ cấu hình theo từng provider trong `.devtool/review_config.json` có tính năng ghi nhớ tự động (sticky memory), với các giá trị khởi điểm: `Opus 5.5` (high) cho Claude, `gpt-6.1-sol` (high) cho Codex, `Gemini 4 Argon (Medium)` (medium) cho Antigravity (`agy`), và `qwen38-fast:latest` (high) cho Ollama.

## Mục Tiêu và Phạm Vi Ngoài Mục Tiêu

### Mục Tiêu

- Chuẩn hóa header gồm đúng 4 gạch đầu dòng trên tất cả các chế độ review (`triage`, `run`, `run_adhoc_code`, và báo cáo giao tiếp của AI Assistant).
- Lưu cấu hình mặc định độc lập theo từng provider (`model`, `thinking_level`, `last_used_provider`) vào `.devtool/review_config.json` với cơ chế ghi nguyên tử và tự động khôi phục.
- Hỗ trợ tham số `--thinking-level` (`none`, `light`, `low`, `medium`, `high`, `extra-high`) kèm tự động ánh xạ cờ thực thi cho từng CLI:
  - Codex: `-c model_reasoning_effort="<level>"`
  - Claude: các cờ định mức thinking budget
  - Antigravity: tham số `--model` / hồ sơ suy luận
  - Ollama: điều chỉnh định mức token và ngữ cảnh
- Cơ chế ghi nhớ bền vững (sticky memory): khi lập trình viên truyền cờ CLI mới, hệ thống tự cập nhật cấu hình đã lưu của provider đó cho các lần chạy sau.
- Lưu vết `- **Thinking**: <level>` trong metadata của các tệp markdown kết quả (`principal_review.md` và `review_results.md`).

### Phạm Vi Ngoài Mục Tiêu

- Không bỏ qua các điểm dừng phê duyệt thủ công của lập trình viên hoặc tự động hóa các cổng duyệt.
- Không ghi đè các tệp cấu hình không thuộc phạm vi review trong `.devtool/` hoặc `.agents/`.
- Không hạn chế việc ghi đè thủ công tham số dòng lệnh khi lập trình viên cần.

## Cảnh Báo Hợp Đồng Dùng Chung

Không có cảnh báo hợp đồng dùng chung (`ai-agent-tools` là kho chứa bộ công cụ plugin và không có thư mục `shared-contracts/`; đã kiểm tra lúc bắt đầu phiên làm việc).

## Quyết Định Đã Thống Nhất

| # | Quyết Định | Lý Do |
|---|---|---|
| 1 | Chuẩn hóa header đúng 4 gạch đầu dòng: Candidate SHA, Reviewer, Thinking Level, Verdict. | Loại bỏ sự không nhất quán giữa kết quả dòng lệnh CLI, bảng triage, và tin nhắn trò chuyện. |
| 2 | Phân tách cấu hình theo từng provider dưới `providers.<cli>` kèm `last_used_provider` trong `.devtool/review_config.json`. | Tránh xung đột tên model khi chuyển đổi giữa các provider (ví dụ tên model của Codex bị truyền sang Claude). |
| 3 | Thiết lập cấu hình mặc định ban đầu: Claude: `Opus 5.5` (high), Codex: `gpt-6.1-sol` (high), agy: `Gemini 4 Argon (Medium)` (medium), Ollama: `qwen38-fast:latest` (high). | Quy chuẩn hóa các lựa chọn production do lập trình viên chỉ định cho cả 4 công cụ review. |
| 4 | Áp dụng thứ tự ưu tiên phân giải: Tham số dòng lệnh tường minh > Metadata round trước của epic hiện tại > Cấu hình provider trong `review_config.json` > Giá trị mặc định toàn cục. | Giúp thực thi lại không ma sát, không cần gõ lại các tham số dài dòng mỗi lần review. |
| 5 | Ghi nhận thinking level vào các tệp markdown review theo định dạng `- **Thinking**: <level>`. | Đảm bảo tính minh bạch kiểm toán và khả năng truy vết lịch sử qua các vòng review liên tiếp. |

## Thiết Kế Chi Tiết

### Cấu Trúc Tệp Cấu Hình Review

Tệp cấu hình cấp repository được đặt tại `.devtool/review_config.json`:

```json
{
  "last_used_provider": "codex",
  "providers": {
    "claude": {
      "model": "Opus 5.5",
      "thinking_level": "high"
    },
    "codex": {
      "model": "gpt-6.1-sol",
      "thinking_level": "high"
    },
    "agy": {
      "model": "Gemini 4 Argon (Medium)",
      "thinking_level": "medium"
    },
    "ollama": {
      "model": "qwen38-fast:latest",
      "thinking_level": "high",
      "host": "http://localhost:11434"
    }
  }
}
```

### Đặc Tả Định Dạng Header Chuẩn

Mọi phần tóm tắt review triage (dù xuất ra từ lệnh `run_external_review.py triage`, dòng lệnh `run_adhoc_code`, hay do AI Assistant trình bày trong chat) BẮT BUỘC bắt đầu bằng khối header chuẩn:

```markdown
Cross-Model Review Triage: Round <N> (<CLI>)
*(hoặc `Principal Review Triage: Round <N> (<CLI>)`)*

• Candidate SHA: <commit_sha>
• Reviewer: <CLI> ( <model> )
• Thinking Level: <Light | Low | Medium | High | Extra High | None>
• Verdict: <VERDICT> (<count> <Severity> findings)
```

### Ma Trận Ánh Xạ Thinking Level và Cờ Thực Thi CLI

Tham số `--thinking-level` tiếp nhận các mức: `none`, `light`, `low`, `medium`, `high`, `extra-high`. Bộ thực thi ánh xạ từng mức sang cú pháp CLI của từng engine:

| Thinking Level | Codex (`codex exec`) | Claude (`claude -p`) | Antigravity (`agy`) | Ollama (`local_review`) |
|---|---|---|---|---|
| **none** | `-c model_reasoning_effort="none"` | *(không truyền thinking)* | *(tiêu chuẩn)* | *(không suy luận)* |
| **light / low** | `-c model_reasoning_effort="low"` | `--thinking` (ngắn) | Flash / Low | Định mức token thấp |
| **medium** | `-c model_reasoning_effort="medium"` | `--thinking` (mặc định) | Argon Balanced | Token cân bằng |
| **high** | `-c model_reasoning_effort="high"` | `--thinking` (mở rộng) | Argon High | Suy luận mở rộng |
| **extra-high** | `-c model_reasoning_effort="extra-high"` | `--thinking` (tối đa) | Max reasoning | Token tối đa |

### Thuật Toán Phân Giải và Lưu Trữ Bền Vững Trong run_external_review.py

1. **Giai Đoạn Phân Giải**:
   - Nếu thiếu `--cli`, đọc `last_used_provider` từ `.devtool/review_config.json` (mặc định `"codex"` nếu tệp chưa tồn tại).
   - Nếu thiếu `--model`, đọc `providers[cli].model` từ cấu hình (khôi phục về giá trị mặc định chuẩn nếu chưa có).
   - Nếu thiếu `--thinking-level`, kiểm tra metadata round gần nhất trong `review_results.md` / `principal_review.md`; nếu không có, đọc `providers[cli].thinking_level` từ cấu hình (khôi phục về giá trị mặc định chuẩn nếu chưa có).
2. **Giai Đoạn Thực Thi**:
   - Khởi tạo danh sách tham số dòng lệnh CLI bao gồm cờ thinking/reasoning tương ứng.
   - Ghi `- **Thinking**: <level>` vào metadata của round review.
3. **Giai Đoạn Lưu Trữ**:
   - Ghi cấu hình đã cập nhật và `last_used_provider` trở lại tệp `.devtool/review_config.json` bằng kỹ thuật ghi nguyên tử (ghi tệp `.tmp` và đổi tên).

### Tích Hợp Skills và Quy Trình

- **Skills `principal-review` & `cross-model-review`**:
  - Bổ sung hướng dẫn yêu cầu AI Assistant luôn in khối header 4 gạch đầu dòng chuẩn khi trình bày bảng triage cho lập trình viên.
- **Handoff Choice trong `dev-lifecycle` và Cổng Gate 4**:
  - Hiển thị cấu hình mặc định hiện hành trong câu nhắc lựa chọn review (ví dụ: `Option 2: Cross-model review (Mặc định hiện tại: Codex / gpt-6.1-sol / Thinking: High)`).

## Chiến Lược Kiểm Thử

- **Kiểm Thử Đơn Vị (`test_run_external_review.py`)**:
  - Kiểm tra khởi tạo `.devtool/review_config.json` với 4 provider chuẩn.
  - Kiểm tra thứ tự ưu tiên phân giải (Cờ CLI > Metadata round trước > Tệp cấu hình > Giá trị mặc định).
  - Kiểm tra cập nhật ghi nhớ (sticky update) khi truyền cờ CLI mới.
  - Kiểm tra định dạng đầu ra của header trong `triage`, `run_adhoc_code`, và các round được ghi nhận.
- **Kiểm Thử Tích Hợp Phát Hành (`scripts/verify.sh`)**:
  - Đảm bảo toàn bộ 15 phân đoạn kiểm thử của bộ công cụ đều vượt qua với trạng thái xanh.

## Danh Sách Tệp Thay Đổi

- `skills/dev-implementation/resources/scripts/run_external_review.py`
- `skills/dev-implementation/resources/scripts/test_run_external_review.py`
- `skills/principal-review/SKILL.md`
- `skills/principal-review/references/document-triage.md`
- `skills/cross-model-review/SKILL.md`
- `skills/cross-model-review/references/review-triage.md`
- `skills/dev-implementation/references/review-triage.md`
- `skills/dev-lifecycle/references/principal-review.md`

## Rủi Ro và Giảm Thiểu

| Rủi Ro | Biện Pháp Giảm Thiểu |
|---|---|
| Model không hỗ trợ mức reasoning effort được yêu cầu. | Codex CLI tự động bỏ qua an toàn; bộ chạy ghi log cảnh báo và tiếp tục với giá trị mặc định của provider. |
| Tệp cấu hình bị lỗi do ghi đồng thời. | Sử dụng cơ chế ghi tệp tạm `.tmp` rồi đổi tên nguyên tử; bắt lỗi cú pháp JSON và tự động khôi phục về giá trị mặc định chuẩn. |
