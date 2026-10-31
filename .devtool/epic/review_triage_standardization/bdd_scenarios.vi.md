# Các Kịch Bản BDD Chuẩn Hóa Triage Đánh Giá (Review Triage Standardization)

## Mục lục

- [Thông tin Meta](#thông-tin-meta)
- [Luồng Hoạt động Chuẩn (Happy Paths)](#luồng-hoạt-động-chuẩn-happy-paths)
- [Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)](#trường-hợp-biên-và-giới-hạn-edge-cases-and-boundaries)
- [Chuyển đổi Trạng thái (State Transitions)](#chuyển-đổi-trạng-thái-state-transitions)
- [Bất đồng bộ và Xung đột Tài nguyên (Async and Race Conditions)](#bất-đồng-bộ-và-xung-đột-tài-nguyên-async-and-race-conditions)
- [Xử lý Lỗi và Khả năng Phục hồi (Failure and Resilience)](#xử-lý-lỗi-và-khả-năng-phục-hồi-failure-and-resilience)

## Thông tin Meta

- **Epic**: `review_triage_standardization`
- **Ngôn ngữ chuẩn đối chiếu**: Tiếng Anh
- **Tiền tố kịch bản**: `RTS`
- **Thư mục tự động hóa gốc**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Quy tắc**: Mỗi mã kịch bản được phân bổ cho đúng một task và xuất hiện trong kiểm thử tự động.

## Luồng Hoạt động Chuẩn (Happy Paths)

```gherkin
Scenario: [RTS-HP-01] [Tier C - Integration] Triage format renders standardized 4-bullet header

Given một vòng đánh giá hoàn thành trong review_results.md
When hàm triage() định dạng bản tóm tắt
Then kết quả bắt đầu bằng "# Review Triage: <epic>, Round <N>"
And chứa "• Candidate SHA: <sha>"
And chứa "• Reviewer: <cli> ( <model> )"
And chứa "• Thinking Level: <level>"
And chứa "• Verdict: <verdict> (<count> findings)"

Scenario: [RTS-HP-02] [Tier C - Integration] Canonical provider defaults are automatically seeded

Given chưa có tệp .devtool/review_config.json
When hàm load_review_config() được thực thi
Then tệp .devtool/review_config.json được tạo với các giá trị chuẩn mặc định:
  | Provider | Model                   | Thinking Level |
  | codex    | gpt-6.1-sol             | high           |
  | claude   | Opus 5.5                | high           |
  | agy      | Gemini 4 Argon (Medium) | medium         |
  | ollama   | qwen38-fast:latest      | high           |
And default_provider được đặt là "codex"

Scenario: [RTS-HP-03] [Tier C - Integration] Sticky memory updates on subsequent runs

Given tệp .devtool/review_config.json đã tồn tại
When chạy đánh giá với "--cli claude --model custom-claude --thinking-level medium"
Then .devtool/review_config.json cập nhật default_provider thành "claude"
And providers.claude.model cập nhật thành "custom-claude"
And providers.claude.thinking_level cập nhật thành "medium"
And cấu hình các provider khác giữ nguyên không đổi

Scenario: [RTS-HP-04] [Tier C - Integration] Thinking level translates to provider-specific CLI flags

Given cấu hình provider có thinking level là "high"
When hàm cli_command được xây dựng cho "claude"
Then tham số "--effort high" được truyền vào
When hàm cli_command được xây dựng cho "codex"
Then tham số "-c model_reasoning_effort=high" được truyền vào

Scenario: [RTS-HP-05] [Tier C - Integration] Claude CLI receives dangerously-skip-permissions

When hàm cli_command được xây dựng cho "claude"
Then danh sách tham số chứa "--dangerously-skip-permissions"
And danh sách tham số không chứa "--permission-mode plan"

Scenario: [RTS-HP-06] [Tier C - Integration] Mandatory dynamic probing rule and 5-layer senior verification rules are present in prompts

Given các tệp prompt và rules đánh giá
When kiểm tra external-review-prompt.md, principal-review-prompt.md, review-rules.md và principal-review-rules.md
Then các tệp prompt chứa "## Mandatory Dynamic Probing Rule"
And các tệp quy tắc chứa "5-Layer Deep Verification Checklist"
```

## Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)

```gherkin
Scenario: [RTS-EC-01] [Tier C - Integration] Ollama requires explicit model when no previous round exists

Given không gian làm việc trống chưa có .devtool/review_config.json và chưa có vòng đánh giá trước
When chạy run_external_review.py run --cli ollama mà không truyền --model
Then lệnh thoát kèm thông báo lỗi chỉ ra rằng "--cli ollama needs --model"

Scenario: [RTS-EC-02] [Tier C - Integration] Missing or corrupted review_config.json falls back to canonical defaults

Given tệp .devtool/review_config.json chứa JSON sai định dạng
When hàm load_review_config() được gọi
Then ghi log cảnh báo và trả về cấu hình mặc định chuẩn mà không làm văng ngoại lệ

Scenario: [RTS-EC-03] [Tier C - Integration] Zero findings in review verdict displays 0 findings

Given một vòng đánh giá có kết luận "PASS" và không có phát hiện nào
When format_triage_header() được thực thi
Then dòng verdict hiển thị "• Verdict: PASS (0 Critical, 0 Major, 0 Minor findings)"
```

## Chuyển đổi Trạng thái (State Transitions)

```gherkin
Scenario: [RTS-ST-01] [Tier C - Integration] Provider switching preserves distinct per-provider memory

Given tệp .devtool/review_config.json lưu claude model "Opus 5.5" và codex model "gpt-6.1-sol"
When kỹ sư chạy đánh giá với cờ "--cli codex"
Then model "gpt-6.1-sol" của codex được chọn
When kỹ sư tiếp tục chạy đánh giá với cờ "--cli claude"
Then model "Opus 5.5" của claude được chọn mà không bị ghi đè hay xung đột với tên model codex

Scenario: [RTS-ST-02] [Tier C - Integration] Incomplete review round reflects non-completed status

Given một vòng đánh giá có trạng thái "failed" hoặc "no verdict"
When hàm triage() xuất kết quả tóm tắt
Then dòng "- **Status**: <status>" được nối vào cuối kết quả triage
```

## Bất đồng bộ và Xung đột Tài nguyên (Async and Race Conditions)

```gherkin
Scenario: [RTS-AR-01] [Tier C - Integration] Atomic review_config.json write protects against partial writes

When hàm save_review_config() ghi tệp cấu hình
Then hàm ghi vào tệp tạm thời .devtool/review_config.json.tmp
And thay thế tệp đích bằng hàm nguyên tử os.replace
```

## Xử lý Lỗi và Khả năng Phục hồi (Failure and Resilience)

```gherkin
Scenario: [RTS-FR-01] [Tier C - Integration] Tree change guard aborts if reviewer modifies working tree

Given một tiến trình CLI reviewer chỉnh sửa hoặc tạo tệp mới trong kho mã
When hàm tree_changes(root, before, sha) kiểm tra sau khi chạy xong
Then phát hiện đường dẫn bị sửa đổi và từ chối ghi nhận vòng đánh giá

Scenario: [RTS-FR-02] [Tier C - Integration] Unknown thinking level gracefully defaults to high

Given giá trị thinking level không hợp lệ hoặc chưa được xác định
When giải quyết tham số cấu hình
Then hàm resolve_review_settings() chọn mặc định an toàn là "high"
```

