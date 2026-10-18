# Kịch bản BDD Cải tiến Quy trình Review

## Mục lục

- [Metadata](#metadata)
- [Happy Paths](#happy-paths)
- [Edge Cases & Boundaries](#edge-cases--boundaries)
- [Chuyển đổi Trạng thái](#chuyển-đổi-trạng-thái)
- [Xử lý Lỗi và Khả năng Phục hồi](#xử-lý-lỗi-và-khả-năng-phục-hồi)

## Metadata

- **Epic**: `review_workflow_enhancements`
- **Status**: Draft
- **Tổng số Kịch bản**: 14

## Happy Paths

```gherkin
Tính năng: Cải tiến Quy trình Review

  Kịch bản: [RWE-HP-01] [Tier A - Unit] [Happy] Regex Verdict khớp các biến thể in đậm và heading Markdown
    Cho một raw output từ AI CLI kết thúc bằng "**Verdict:** PASS" hoặc "### Verdict: CHANGES REQUIRED"
    Khi runner trích xuất verdict từ output
    Thì verdict được nhận diện chính xác là "PASS" hoặc "CHANGES REQUIRED"
    Và trạng thái của round được ghi nhận là "completed"

  Kịch bản: [RWE-HP-02] [Tier A - Unit] [Happy] Các dòng finding khớp các mục danh sách có dấu gạch hoặc đầu dòng
    Cho một raw output từ AI CLI chứa các finding bắt đầu bằng "-" hoặc "*" hoặc "1."
    Khi runner phân tích các finding
    Thì mức độ nghiêm trọng, vị trí và mô tả lỗi của từng finding được trích xuất thành các phần tử có cấu trúc

  Kịch bản: [RWE-HP-03] [Tier A - Unit] [Happy] Các ô bảng được làm sạch khỏi ký tự điều khiển
    Cho nội dung lỗi finding chứa ký tự xuống dòng carriage return hoặc newline
    Khi runner định dạng bảng Markdown của round
    Thì toàn bộ ký tự carriage return bị xóa và ký tự newline bên trong được thay bằng khoảng trắng
    Và ký tự pipe được escape để mỗi finding nằm trọn vẹn trên đúng một hàng bảng

  Kịch bản: [RWE-HP-04] [Tier A - Unit] [Happy] Thu thập facts thành công thì tiếp tục gọi CLI
    Cho một epic có audit, kết quả tích hợp và kiểm tra truy xuất đều đạt
    Khi collect_facts thực thi trong giới hạn timeout của facts
    Thì các fact về audit và test được thu thập sạch sẽ và đưa vào template prompt

  Kịch bản: [RWE-HP-05] [Tier A - Unit] [Happy] Nhúng toàn bộ diff khi dưới giới hạn dòng
    Cho một diff của candidate epic chứa ít hơn giới hạn dòng (ví dụ 1500 dòng)
    Khi runner chuẩn bị review prompt
    Thì toàn bộ git diff được nhúng trực tiếp vào prompt
    Và reviewer nhận được code changes ngay lập tức mà không cần gọi tool git diff riêng


## Edge Cases & Boundaries

```gherkin
  Kịch bản: [RWE-EC-01] [Tier A - Unit] [Boundary] Văn bản tóm tắt thông thường không kích hoạt lỗi chặn unparsed
    Cho một output từ AI có kết luận "PASS" chứa đoạn "I found 0 [Critical] or [Important] issues"
    Khi runner kiểm tra các finding chặn unparsed
    Thì không có finding Critical hay Important unparsed nào được sinh ra
    Và round kết thúc với exit code 0

  Kịch bản: [RWE-EC-02] [Tier A - Unit] [Boundary] Khoảng trắng thừa và chữ hoa thường trong dòng verdict
    Cho một dòng output của AI với "  verdict:   pass   "
    Khi runner khớp dòng verdict
    Thì nó trích xuất thành công "PASS" làm kết luận cuối cùng

  Kịch bản: [RWE-EC-03] [Tier A - Unit] [Boundary] Hàng finding chứa nhiều dấu pipe đã escape
    Cho một mô tả finding chứa đoạn text như "use a | b | c syntax"
    Khi finding được kết xuất vào review_results.md và kiểm tra bởi split_row
    Thì split_row phân tách chính xác 5 ô mà không bị ngắt quãng bởi các dấu pipe đã escape

  Kịch bản: [RWE-EC-04] [Tier A - Unit] [Boundary] Timeout của facts tách biệt với timeout của CLI
    Cho timeout của facts được cấu hình là 300 giây và timeout của CLI là 1800 giây
    Khi collect_facts chạy
    Thì từng lệnh fact bị giới hạn bởi timeout của facts mà không làm cắt ngắn timeout của CLI

  Kịch bản: [RWE-EC-05] [Tier A - Unit] [Boundary] Dự phòng bằng diff stat khi diff vượt quá giới hạn
    Cho một diff của candidate epic vượt quá giới hạn dòng được cấu hình
    Khi runner chuẩn bị review prompt
    Thì bản tóm tắt git diff stat được nhúng thay cho diff đầy đủ
    Và chỉ dẫn model kiểm tra các file cụ thể được bổ sung kèm theo


## Chuyển đổi Trạng thái

```gherkin
  Kịch bản: [RWE-ST-01] [Tier A - Unit] [State] Round chuyển từ CHANGES REQUIRED sang check thành công sau quyết định
    Cho một round được ghi nhận với CHANGES REQUIRED và hai finding Important
    Khi developer ghi nhận "fixed in <sha>" hoặc "dismissed: <reason>" cho toàn bộ finding chặn
    Thì run_external_review check trả về exit code 0 và không còn finding chưa quyết định

  Kịch bản: [RWE-ST-02] [Tier A - Unit] [State] Finding chưa quyết định chặn lệnh check
    Cho một round đã hoàn tất chứa một finding Critical chưa có quyết định
    Khi run_external_review check thực thi
    Thì nó liệt kê mã định danh của finding chưa quyết định và thoát với exit code 1
```

## Xử lý Lỗi và Khả năng Phục hồi

```gherkin
  Kịch bản: [RWE-FR-01] [Tier A - Unit] [Failure] Fail-fast dừng thực thi sớm khi audit_epic thất bại
    Cho một nhánh epic nơi audit_epic.py trả về exit code 1
    Khi run_external_review run thực thi
    Thì nó dừng ngay lập tức mà không gọi AI CLI
    Và báo cáo lỗi điều kiện tiên quyết để tránh lãng phí credit AI

  Kịch bản: [RWE-FR-02] [Tier A - Unit] [Failure] Fail-fast dừng thực thi sớm khi integration test bị timeout
    Cho một bài test tích hợp bị timeout và trả về code is None
    Khi collect_facts thực thi
    Thì nó kích hoạt lỗi điều kiện tiên quyết và dừng lại trước khi gọi AI CLI
```
