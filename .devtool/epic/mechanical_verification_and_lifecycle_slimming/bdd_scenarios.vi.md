# Kịch bản BDD siết chặt xác minh cơ học và tinh gọn vòng đời

## Mục lục

- [Siêu dữ liệu](#siêu-dữ-liệu)
- [Luồng thành công](#luồng-thành-công)
- [Ca biên và ranh giới](#ca-biên-và-ranh-giới)
- [Chuyển trạng thái](#chuyển-trạng-thái)
- [Bất đồng bộ và race condition](#bất-đồng-bộ-và-race-condition)
- [Lỗi và khả năng phục hồi](#lỗi-và-khả-năng-phục-hồi)

## Siêu dữ liệu

- **Epic**: `mechanical_verification_and_lifecycle_slimming`
- **Ngôn ngữ chuẩn**: Tiếng Anh
- **Prefix scenario**: `MVLS`
- **Automation root**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Quy tắc**: Mỗi ID scenario được gán đúng một task và xuất hiện trong một automated test.

## Luồng thành công

```gherkin
Scenario: [MVLS-HP-01] [Tier C - Integration] Ghi nhận RED thật từ test đã collect

Given một hàng RED gọi trực tiếp pytest và test đã collect thất bại với exit 1
When `run_task_checks.py` ghi nhận hàng đó
Then summary lỗi dương đủ điều kiện là RED hành vi thật
And outcome bằng chứng là PASS cho phase RED mong đợi

Scenario: [MVLS-HP-02] [Tier C - Integration] Audit bằng chứng pytest RED thật

Given bằng chứng đã commit chứa lệnh pytest được hỗ trợ, exit 1 hoặc 2 và summary lỗi dương
When `audit_epic.py` audit candidate SHA
Then nó tính lại semantic RED thành công
And không phát sinh finding pytest RED không hợp lệ

Scenario: [MVLS-HP-03] [Tier C - Integration] Chấp nhận xác minh Python TIER-B đầy đủ

Given một task Python có các hàng TIER-B gọi trực tiếp linter và type checker
When `check_task_contract.py --design` xác minh task
Then hợp đồng tooling Python đi qua
And lệnh provider đã đăng ký được chấp nhận khi chuỗi argument chuẩn hóa khớp

Scenario: [MVLS-HP-04] [Tier C - Integration] Giữ orchestration triển khai trong skill cô đọng

Given `dev-implementation/SKILL.md` đã được tinh gọn
When hợp đồng tài liệu vòng đời chạy
Then entry-point detection, resume, Gate 3, evidence, Gate 4, Review Choice, Gate 5 và finishing handoff vẫn còn
And skill nêu hai quy tắc test integrity semantic
And số từ của skill không vượt 4.500

Scenario: [MVLS-HP-05] [Tier C - Integration] Giữ khả năng hiểu vòng đời trong tài liệu song ngữ

Given sơ đồ runtime đã được chuyển ra khỏi lifecycle skill
When tài liệu vòng đời tiếng Anh và tiếng Việt được kiểm tra
Then cả hai chứa sơ đồ vòng đời và resume
And cả hai mô tả Gate 4, Review Choice, Gate 5 và đường quay lại Gate 4 sau cross-model
And `dev-lifecycle/SKILL.md` không vượt 2.500 từ

Scenario: [MVLS-HP-06] [Tier C - Integration] Giữ vững quy tắc sinh task và guardrail cho LLM tiếp nhận

Given `dev-designer/SKILL.md` và `handoff-template.md` được đánh giá bởi lifecycle document contract
When các assertion hợp đồng kiểm tra quy tắc sinh task và handoff template
Then `dev-designer` giữ vững contract grounded trong Decisions Already Made, exact node ID, và cấm assertion yếu
And `handoff-template.md` giữ đủ bốn guardrail cho LLM tiếp nhận và hướng dẫn resume prompt trước Gate 3

```

## Ca biên và ranh giới

```gherkin
Scenario: [MVLS-EC-01] [Tier C - Integration] Chặn file pytest bị thiếu

Given một hàng RED gọi pytest cho đường dẫn không tồn tại
And process thoát 4 hoặc báo `ERROR: file or directory not found`
When recorder hoặc auditor Gate 4 đánh giá hàng đó
Then hàng thất bại với lý do pytest RED không hợp lệ bắt buộc

Scenario: [MVLS-EC-02] [Tier C - Integration] Chặn lựa chọn pytest rỗng

Given một hàng RED collect hoặc chọn zero test
And process thoát 5, báo `collected 0 items` hoặc báo `/ 0 selected`
When recorder hoặc auditor Gate 4 đánh giá hàng đó
Then hàng thất bại với lý do pytest RED không hợp lệ bắt buộc

Scenario: [MVLS-EC-03] [Tier C - Integration] Tránh false positive Python toàn repository

Given một repository polyglot có cấu hình Python
But Allowed files và hàng xác minh của task không có tín hiệu Python cục bộ
When hợp đồng task được xác minh
Then yêu cầu TIER-B dành riêng cho Python không bị áp lên task đó

Scenario: [MVLS-EC-04] [Tier C - Integration] Phân biệt wrapper được hỗ trợ với text không liên quan

Given các hàng lệnh gồm `uv run pytest`, `python -m pytest`, đường dẫn executable kết thúc bằng pytest và `echo pytest`
When bộ phân loại lệnh tokenize các hàng
Then ba hàng đầu được phân loại là invocation pytest
And `echo pytest` không được phân loại là invocation pytest

Scenario: [MVLS-EC-05] [Tier C - Integration] Giữ sơ đồ bên ngoài runtime skill

Given runtime skill và tài liệu vòng đời song ngữ được kiểm tra cùng nhau
When hợp đồng tài liệu vòng đời quét fenced block
Then không runtime skill nào chứa sơ đồ Mermaid hoặc Graphviz DOT
And cả hai tài liệu vòng đời chứa sơ đồ Mermaid dành cho con người như mong đợi

Scenario: [MVLS-EC-06] [Tier C - Integration] Từ chối thiếu guardrail cho LLM tiếp nhận hoặc thiếu anchor dev-designer trong lifecycle contract

Given `dev-designer/SKILL.md` thiếu quy tắc exact node ID hoặc `handoff-template.md` thiếu guardrail cho LLM tiếp nhận
When test lifecycle document contract chạy
Then test thất bại và báo cáo anchor bị thiếu
And xác minh phát hành không thể pass cho đến khi hợp đồng được khôi phục

Scenario: [MVLS-EC-07] [Tier C - Integration] Từ chối biểu thức pytest không có node ID, assertion BDD yếu hoặc decisions trống

Given một task contract đang trải qua kiểm tra design hoặc implementation
When `check_task_contract.py` kiểm tra các hàng pytest RED, assertion kịch bản BDD hoặc `Decisions Already Made`
Then lệnh pytest `-k` chung chung không có exact node ID bị từ chối
And các assertion yếu như "should be truthy", "is valid" hoặc "returns non-empty" bị từ chối
And section `Decisions Already Made` bị trống hoặc thiếu trên task có thay đổi executable bị từ chối
```

## Chuyển trạng thái

```gherkin
Scenario: [MVLS-ST-01] [Tier C - Integration] Bản ghi RED không hợp lệ chuyển thành FAIL

Given Expect thông thường của một hàng RED sẽ chấp nhận exit khác 0
But semantic pytest của nó không hợp lệ
When ghi nhận hoàn tất
Then outcome của hàng chuyển thành FAIL
And recorder thoát khác 0 với lý do bắt buộc được lưu trong bằng chứng

Scenario: [MVLS-ST-02] [Tier C - Integration] Bằng chứng PASS bị sửa chuyển Gate 4 thành FAIL

Given bằng chứng pytest RED không hợp lệ đã bị sửa thành `outcome: PASS`
When Gate 4 audit bằng chứng đã commit
Then việc tính lại semantic ghi đè outcome được lưu
And mục Evidence cùng kết luận audit cuối chuyển thành FAIL

Scenario: [MVLS-ST-03] [Tier C - Integration] Tinh gọn skill giữ đồng bộ hợp đồng tài liệu

Given prose orchestration hoặc sơ đồ di chuyển giữa runtime skill và tài liệu vòng đời
When hợp đồng vòng đời và bộ kiểm tài liệu song ngữ chạy
Then thay đổi chỉ qua nếu invariant runtime bắt buộc vẫn còn
And tài liệu cho người tiếng Anh và tiếng Việt vẫn đồng bộ cấu trúc

```

## Bất đồng bộ và race condition

```gherkin
Scenario: [MVLS-AR-01] [Tier C - Integration] Các hàng RED độc lập không rò trạng thái xác minh

Given một task chứa một hàng pytest RED hợp lệ và một hàng pytest RED không hợp lệ
When các hàng được đánh giá theo bất kỳ thứ tự nào
Then mỗi kết luận chỉ phụ thuộc vào lệnh, exit code và output của chính nó
And hàng không hợp lệ không thể kế thừa summary dương của hàng hợp lệ

Scenario: [MVLS-AR-02] [Tier C - Integration] Audit nhiều task vẫn xác định

Given một candidate SHA chứa nhiều bản ghi bằng chứng task với tính hợp lệ pytest RED hỗn hợp
When Gate 4 audit chúng nhiều lần
Then finding gắn với đúng task và hàng
And thứ tự ưu tiên tổng hợp vẫn là FAIL trên BLOCKED trên PASS bất kể thứ tự duyệt

```

## Lỗi và khả năng phục hồi

```gherkin
Scenario: [MVLS-FR-01] [Tier C - Integration] Chặn wrapper đổi exit không hợp lệ thành 1

Given một wrapper chạy pytest với file thiếu hoặc lựa chọn rỗng rồi thoát 1
When output gộp vẫn chứa marker pytest bị cấm
Then recorder và auditor chặn RED dù exit code nằm trong allowlist

Scenario: [MVLS-FR-02] [Tier C - Integration] Chặn exit 1 mơ hồ không có summary lỗi

Given một lệnh pytest RED thoát 1
But output không có summary failed-or-error khác 0 dương
When validator semantic đánh giá nó
Then xác minh fail closed với lý do pytest RED không hợp lệ bắt buộc

Scenario: [MVLS-FR-03] [Tier C - Integration] Thất bại khi manifest Python đã đăng ký sai

Given `.agents/quality/python-quality.json` tồn tại nhưng sai định dạng hoặc có dữ liệu capability lint hay type-check không dùng được
When hợp đồng task Python được xác minh
Then validator báo vấn đề của manifest
And không âm thầm fallback sang tên công cụ dựng sẵn

Scenario: [MVLS-FR-04] [Tier C - Integration] Chặn test giả về semantic tại Gate 4

Given một test tái dựng logic retry, progress hoặc configuration của production thay vì import và gọi symbol trong Allowed files
Or một artifact repository thật bị thay bằng dữ liệu tổng hợp có anchor scenario khác
When Gate 4 hoặc provider đã đăng ký audit test integrity
Then vi phạm được báo là FAIL
And không tuyên bố bao phủ cơ học đa ngôn ngữ phổ quát

Scenario: [MVLS-FR-05] [Tier C - Integration] Thất bại khi invariant vòng đời bị drift

Given việc tinh gọn xóa một gate, quy tắc recovery, vòng review hoặc invariant sơ đồ song ngữ bắt buộc
When test hợp đồng repository và tài liệu chạy
Then test liên quan thất bại với invariant bị thiếu
And xác minh release không thể qua cho đến khi hợp đồng được khôi phục

Scenario: [MVLS-FR-06] [Tier C - Integration] Thất bại khi các section cốt lõi của task active bị giả mạo

Given một file task active trong `.devtool/features/` có `Files`, `Verification`, `Definition of Done` hoặc `Covers` khác với HEAD hoặc bản mirror tại epic
When `run_task_checks.py` xác thực tính toàn vẹn của task trước khi chạy các lệnh kiểm tra
Then nó lập tức dừng với lỗi task tampered
And không bằng chứng xác minh nào được commit
```
