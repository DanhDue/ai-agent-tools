# Kịch bản BDD Runner Vòng đời Tự động (Autonomous Lifecycle Runner)

## Mục lục

- [Siêu dữ liệu](#siêu-dữ-liệu)
- [Luồng thành công](#luồng-thành-công)
- [Trường hợp biên và dữ liệu bất thường](#trường-hợp-biên-và-dữ-liệu-bất-thường)
- [Chuyển đổi trạng thái](#chuyển-đổi-trạng-thái)
- [Bất đồng bộ và điều kiện tranh chấp](#bất-đồng-bộ-và-điều-kiện-tranh-chấp)
- [Lỗi và khả năng phục hồi](#lỗi-và-khả-năng-phục-hồi)

## Siêu dữ liệu

- **Epic**: `autonomous_lifecycle_runner`
- **Ngôn ngữ chuẩn**: Tiếng Anh
- **Prefix scenario**: `ALR`
- **Automation roots**: `tests/`, `skills/dev-lifecycle/resources/scripts/`
- **Quy tắc**: Mỗi ID scenario được gán đúng một task và xuất hiện trong một automated test.
- **Giả lập**: Lệnh gọi tiến trình `agy` và các CLI review ngoài được giả lập bằng stub thực thi hoặc test fixture trong kiểm thử đơn vị/tích hợp.

## Luồng thành công

```gherkin
Scenario: [ALR-HP-01] [Tier C - Integration] Toàn bộ pipeline tự động thực thi từ bàn giao đến báo cáo điều hành cuối cùng

Given một epic có đặc tả Gate 1 và phân rã task Gate 2 đã được phê duyệt trong git worktree
And cấu hình các model runner trong .devtool/review_config.json
When lifecycle_runner.py chạy với --epic autonomous_lifecycle_runner
Then runner thực thi Principal Review, tiến vào triển khai Giai đoạn 3, và hoàn thành Cross-Model Review mà không dừng menu trung gian
And chỉ tại vòng cuối cùng sau khi hội tụ và Gate 4 PASS, runner kết xuất báo cáo điều hành tổng kết tổng hợp Top 3 Phát hiện Rủi ro Cao nhất của cả quá trình qua các vòng
And runner dừng lại sạch sẽ, trình bày prompt cho /finishing-a-development-branch (merge vào nhánh base hoặc hành động khác) tới Human Architect

Scenario: [ALR-HP-02] [Tier C - Integration] Điều phối headless AI Programmer với Gemini 3.8 Flash High

Given một task triển khai đang chờ xử lý tại .devtool/features/task_1_pipeline_state_machine_and_probing.md
When lifecycle_runner.py điều phối AI Programmer để thực thi task
Then lệnh được điều phối chạy "agy" với "--model gemini-3.8-flash"
And câu lệnh chỉ định "--effort high" và "--mode auto"
And việc thực thi diễn ra bên trong git worktree biệt lập với giám sát nhóm tiến trình chuyên dụng

Scenario: [ALR-HP-03] [Tier C - Integration] AI Assistant đề xuất sửa lỗi và dừng chờ Human xác nhận trong Principal Review

Given Principal Review trả về hai phát hiện Important trên tài liệu đặc tả HLD ứng viên
When AI Assistant phân loại các phát hiện trong step_principal_review
Then Assistant xác minh các phát hiện theo tài liệu nguồn HLD và soạn thảo bảng sửa lỗi có cấu trúc
And lifecycle_runner.py tạm dừng thực thi để hỏi xác nhận từ Con người
And sau khi Con người xác nhận, Assistant áp dụng các chỉnh sửa, chạy package_epic.py --revise, và tiến vào vòng tiếp theo

Scenario: [ALR-HP-04] [Tier C - Integration] AI Assistant duyệt kế hoạch sửa lỗi của AI Programmer trong Cross-Model Review không dừng hỏi Con người

Given Cross-Model Review trả về các phát hiện cần điều chỉnh mã nguồn trong Vòng 1
When AI Programmer soạn thảo kế hoạch sửa lỗi đề xuất trong fix_plan_round1.md
Then AI Assistant đánh giá kế hoạch sửa lỗi theo HLD đã duyệt và phát ra phán quyết "APPROVED"
And AI Programmer áp dụng các thay đổi mã nguồn đã duyệt và chạy lại Phase 4 Gate 4
And chu trình tiến vào Vòng 2 mà không hỏi xác nhận trung gian từ Human Architect
```

## Trường hợp biên và dữ liệu bất thường

```gherkin
Scenario: [ALR-EC-01] [Tier C - Integration] 0 phát hiện trong Principal Review bỏ qua bước xác nhận của Con người

Given Principal Review hoàn thành Vòng 1 với phán quyết PASS và 0 phát hiện
When step_principal_review xử lý kết quả review
Then runner ghi log "AUTO_PASS_CLEAN: 0 findings"
And runner bỏ qua hoàn toàn prompt xác nhận của Con người
And trạng thái pipeline chuyển thẳng sang Giai đoạn 3 Triển khai

Scenario: [ALR-EC-02] [Tier C - Integration] Gom cụm các phát hiện minor trong Principal Review vào một lần xác nhận duy nhất

Given Principal Review Vòng 1 trả về 0 Critical, 0 Important, và 2 phát hiện định dạng Minor
When step_principal_review đánh giá báo cáo phân loại triage
Then 2 phát hiện Minor được gom cụm vào một prompt xác nhận sửa đổi duy nhất cho Human Architect
And sau khi xác nhận, các sửa đổi được áp dụng trong một lần và package_epic.py --revise thực thi trơn tru

Scenario: [ALR-EC-03] [Tier C - Integration] AI Assistant điều chỉnh kế hoạch sửa lỗi của AI Programmer mà không từ chối

Given AI Programmer đề xuất kế hoạch sửa lỗi bị thiếu một khẳng định ca biên bắt buộc
When AI Assistant đánh giá kế hoạch sửa lỗi trong Cross-Model Review
Then Assistant trả về phán quyết "ADJUSTED" kèm theo nội dung kế hoạch sửa lỗi đã bổ sung
And AI Programmer nhận kế hoạch đã điều chỉnh, áp dụng bản vá kết hợp, và kích hoạt kiểm chứng lại Gate 4

Scenario: [ALR-EC-04] [Tier C - Integration] Thứ tự thực thi Gate 3 được tự động xác nhận qua compute_execution_order

Given nhiều tệp task có liên kết phụ thuộc rõ ràng trong .devtool/features/
When runner tiến vào Giai đoạn 3 Triển khai
Then compute_execution_order.py được thực thi để giải quyết tuần tự thực thi theo topo
And trình tự task kết quả được tự động xác nhận và ghi vào .devtool/GATE_LEDGER.md dưới Gate 3
And việc thực thi task bắt đầu ngay lập tức mà không hiển thị prompt tương tác
```

## Chuyển đổi trạng thái

```gherkin
Scenario: [ALR-ST-01] [Tier C - Integration] Lưu trữ và khôi phục trạng thái sau sự cố ngắt quãng ở giai đoạn trung gian

Given runner bị ngắt quãng bởi SIGINT trong khi đang thực thi task ở Giai đoạn 3
When lifecycle_runner.py được gọi lại với cờ --resume
Then runner đọc tệp .devtool/state/<epic>.pipeline.json
And runner khôi phục giai đoạn đang chạy "implementation", danh sách task đã hoàn thành, và vòng hiện tại
And việc thực thi tiếp tục từ đúng task bị ngắt quãng mà không chạy lại các task đã hoàn thành

Scenario: [ALR-ST-02] [Tier C - Integration] Đồng bộ Gate Ledger trên các chuyển đổi trạng thái tự động

Given pipeline tiến triển tự động qua Giai đoạn 2 và Giai đoạn 3
When mỗi cột mốc cổng (Gate 3, Gate 4, ứng viên Gate 5) đạt được
Then .devtool/GATE_LEDGER.md được cập nhật dấu thời gian, candidate SHA, và siêu dữ liệu tự động duyệt
And trạng thái ledger duy trì sự đồng bộ nghiêm ngặt với .devtool/state/<epic>.pipeline.json

Scenario: [ALR-ST-03] [Tier C - Integration] Thăm dò xác minh năng lực model trước khi khởi tạo trạng thái

Given chuỗi model không hợp lệ hoặc đã lỗi thời được chỉ định trong cấu hình
When lifecycle_runner.py bắt đầu bước thăm dò năng lực khởi động
Then ModelDispatcher.probe_model thực thi một lệnh agy headless tối thiểu
And khi gặp mã thoát khác 0 hoặc lỗi, runner hủy bỏ trước khi ghi trạng thái pipeline hoặc chỉnh sửa tệp
And một thông báo lỗi mô tả model bị từ chối được in ra stderr
```

## Bất đồng bộ và điều kiện tranh chấp

```gherkin
Scenario: [ALR-AR-01] [Tier C - Integration] Cô lập process group và ngắt SIGTERM sạch sẽ khi quá thời gian timeout

Given tiến trình agy programmer headless vượt quá giới hạn timeout đã cấu hình
When bộ đếm thời gian giám sát trong ModelDispatcher hết hạn
Then tín hiệu SIGTERM được gửi tới toàn bộ nhóm tiến trình con qua os.killpg
And sau khoảng thời gian ân hạn 1.0s, tín hiệu SIGKILL được nâng cấp nếu các tiến trình con vẫn còn sống
And runner ghi nhận lỗi timeout vào trạng thái pipeline mà không để lại các tiến trình mồ côi

Scenario: [ALR-AR-02] [Tier C - Integration] Khóa tệp trong quá trình cập nhật trạng thái chống xung đột đồng thời

Given các tiến trình đồng thời hoặc các chuyển đổi trạng thái liên tiếp diễn ra nhanh
When LifecycleRunner ghi cập nhật vào .devtool/state/<epic>.pipeline.json
Then các cập nhật trạng thái được tuần tự hóa bằng khóa tệp và thay thế nguyên tử tệp tạm (.tmp)
And tệp trạng thái pipeline luôn là JSON hợp lệ và không bị hỏng tại mọi thời điểm
```

## Lỗi và khả năng phục hồi

```gherkin
Scenario: [ALR-FR-01] [Tier C - Integration] Circuit Breaker dừng ngay lập tức khi xung đột Shared Contract

Given một vòng external review báo cáo phát hiện xung đột với shared-contracts/
When evaluate_circuit_breakers kiểm tra báo cáo phân loại triage
Then runner kích hoạt CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)
And pipeline dừng ngay lập tức, bảo toàn toàn bộ log và trạng thái
And màn hình console hiển thị banner cảnh báo điều hành hướng dẫn nhà phát triển tham vấn Human Architect

Scenario: [ALR-FR-02] [Tier C - Integration] Circuit Breaker dừng ngay lập tức khi lặp lỗi fix loop

Given một phát hiện trong Vòng N chạm vào cùng đường dẫn tệp đã được đánh dấu là sửa trong Vòng N-1
When evaluate_circuit_breakers đánh giá so sánh giữa các vòng
Then runner kích hoạt CIRCUIT_BREAKER_HALT (FIX_LOOP)
And pipeline ngừng gọi công cụ và trình bày phát hiện tái diễn tới Human Architect

Scenario: [ALR-FR-03] [Tier C - Integration] Circuit Breaker dừng khi hết số vòng tối đa mà vẫn còn lỗi Critical

Given Cross-Model Review đạt tới Vòng 3 mà vẫn còn ít nhất 1 phát hiện Critical chưa được xử lý
When evaluate_circuit_breakers kiểm tra bộ đếm vòng và số lượng mức độ nghiêm trọng
Then runner kích hoạt CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)
And runner dừng lại mà không khởi chạy vòng thứ 4, xuất ra Top 3 Phát hiện Rủi ro Cao nhất

Scenario: [ALR-FR-04] [Tier C - Integration] AI Assistant từ chối kế hoạch sửa lỗi với CRITICAL_CONFLICT và dừng pipeline

Given AI Programmer soạn kế hoạch sửa lỗi cố gắng đảo ngược đơn phương một quyết định kiến trúc đã duyệt
When AI Assistant đánh giá kế hoạch sửa lỗi
Then Assistant trả về phán quyết "CRITICAL_CONFLICT" kèm lý do chi tiết
And lifecycle_runner.py dừng lại ngay lập tức, ngăn Programmer chỉnh sửa mã nguồn
And một cảnh báo được hiển thị tới Human Architect nêu bật xung đột kiến trúc
```

