# Kịch bản Kiểm thử BDD: Hợp đồng Task và Tối ưu Soạn thảo (Task Contract and Authoring Ergonomics)

## Mục lục

- [Chiều 1: Luồng Thành công Chuẩn (Happy Paths)](#chiều-1-luồng-thành-công-chuẩn-happy-paths)
- [Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)](#chiều-2-trường-hợp-biên-và-giới-hạn-edge-cases-and-boundaries)
- [Chiều 3: Chuyển đổi Trạng thái (State Transitions)](#chiều-3-chuyển-đổi-trạng-thái-state-transitions)
- [Chiều 4: Bất đồng bộ và Đồng thời (Async and Concurrency)](#chiều-4-bất-đồng-bộ-và-đồng-thời-async-and-concurrency)
- [Chiều 5: Xử lý Lỗi và Phục hồi (Failures and Resilience)](#chiều-5-xử-lý-lỗi-và-phục-hồi-failures-and-resilience)

## Chiều 1: Luồng Thành công Chuẩn (Happy Paths)

```gherkin
Scenario: [TCAE-HP-01] [Tier C - Integration] Khai báo Evidence files vượt qua kiểm tra hợp đồng thiết kế và xác minh tại Done-Gate
  Given một task khai báo ".devtool/epic/sample_epic/evidence/baseline.txt (new)" dưới mục "Evidence files:" trong "## Files"
  And một dòng Verification tham chiếu tới ".devtool/epic/sample_epic/evidence/baseline.txt"
  When check_task_contract.py chạy với cờ "--design"
  Then công cụ thoát mã 0 với 0 lỗi và ghi nhận đường dẫn evidence mới trên toàn epic
  And khi run_task_checks.py verify thực thi dòng lệnh tạo ra file ".devtool/epic/sample_epic/evidence/baseline.txt"
  Then evaluate_done_gate xác nhận file evidence tồn tại trên đĩa và vượt qua mọi điều kiện Done-Gate

Scenario: [TCAE-HP-02] [Tier C - Integration] Render task từ một nguồn duy nhất tự động chèn BDD nguyên văn, nhúng code và sinh bản mirror
  Given một file task nguồn ".devtool/epic/sample_epic/task_01_setup.md" có dòng "Covers: TCAE-HP-01" và chỉ thị "<!-- @@FILE:src/helper.py@@ -->"
  And file ".devtool/epic/sample_epic/bdd_scenarios.en.md" định nghĩa kịch bản "[TCAE-HP-01]"
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then file ".devtool/epic/sample_epic/task_01_setup.md" chứa chính xác khối Gherkin nguyên văn của "[TCAE-HP-01]" và toàn bộ nội dung của "src/helper.py"
  And bản mirror ".devtool/features/task_01_setup.md" được sinh ra với các liên kết tương đối được viết lại thành "../epic/sample_epic/"
  And lệnh "check_task_contract.py --design" thoát mã 0 mà không có bất kỳ lỗi R2 hay R3 nào

Scenario: [TCAE-HP-03] [Tier C - Integration] Thực thi CLI d3nexus không cần cài đặt (Zero-Setup) bên trong dòng Verification
  Given một dòng Verification của task gọi lệnh "d3nexus check-doc --require-toc .devtool/epic/sample_epic/sample_epic.en.md"
  When lệnh "run_task_checks.py verify" thực thi task trong một kho git tạm chưa hề cấu hình sẵn biến môi trường shell
  Then "run_task_checks.py" tự động tiêm biến "D3NEXUS_KIT" và gắn "<kit_root>/bin" vào đầu "PATH"
  And lệnh "d3nexus check-doc" điều phối tới "check_document.py" và thoát mã 0

Scenario: [TCAE-HP-04] [Tier A - Unit] Ngữ pháp dòng Verification với ký tự pipe được escape, biến môi trường env và nguồn gốc implicit protected path
  Given một dòng lệnh Verification viết "env MODE=strict python3 scripts/tool.py \| grep -c ok"
  When lệnh "check_task_contract.py --design" đánh giá task
  Then "task_contract.py" tự động unescape "\|" thành "|" trong câu lệnh đã phân tích mà không báo lỗi hợp đồng
  And "check_task_contract.py" hiển thị "scripts/tool.py (task_01:V1)" trong dòng "Implicit protected paths:"
```

## Chiều 2: Trường hợp Biên và Giới hạn (Edge Cases and Boundaries)

```gherkin
Scenario: [TCAE-EC-01] [Tier A - Unit] Task không khai báo Evidence files hoặc không có dòng Covers vẫn tương thích ngược hoàn toàn
  Given một file task kiểu cũ không có tiểu mục "Evidence files:" và không có dòng "Covers:"
  When chạy "sync_task_status.py render" và "check_task_contract.py --design" trên epic đó
  Then "sync_task_status.py render" vẫn sinh bản mirror ".devtool/features/" mà không làm thay đổi mục BDD của task
  And "check_task_contract.py --design" thoát mã 0 với 0 lỗi

Scenario: [TCAE-EC-02] [Tier A - Unit] File nhúng chứa 3 dấu backtick tự động nâng rào ngoài lên 4 dấu backtick
  Given một file nguồn "docs/snippet.md" có chứa một khối code fence được bao bởi 3 dấu backtick
  And một file task chứa chỉ thị "<!-- @@FILE:docs/snippet.md@@ -->" ngay phía trên khối code fence 3 dấu backtick
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then khối code sau khi render trong cả file task của epic và bản mirror ".devtool/features/" đều sử dụng rào ngoài gồm 4 dấu backtick

Scenario: [TCAE-EC-03] [Tier A - Unit] Biểu thức tìm kiếm chứa dấu gạch chéo trong grep, rg, sed và awk không bị báo lỗi nhầm là thiếu file
  Given một dòng lệnh Verification viết "grep -E 'foo/bar/baz' README.md" trong đó "foo/bar/baz" không phải là file trên đĩa
  When "check_task_contract.py --design" kiểm tra các token của câu lệnh
  Then hàm "command_paths()" loại trừ biểu thức tìm kiếm "foo/bar/baz" khỏi bước kiểm tra sự tồn tại của file
  And "check_task_contract.py" thoát mã 0 mà không báo lỗi "foo/bar/baz does not exist"
```

## Chiều 3: Chuyển đổi Trạng thái (State Transitions)

```gherkin
Scenario: [TCAE-ST-01] [Tier A - Unit] Lệnh render dọn dẹp mirror mồ côi và bảo toàn vị trí trong thư mục done
  Given file ".devtool/features/task_99_obsolete.md" có frontmatter "epic: sample-epic" nhưng file gốc đã bị xóa khỏi ".devtool/epic/sample_epic/"
  And file ".devtool/epic/sample_epic/task_01_done.md" có frontmatter "status: \"done\""
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then file ".devtool/features/task_99_obsolete.md" bị xóa khỏi đĩa
  And bản mirror của "task_01_done.md" được ghi vào đúng ".devtool/features/done/task_01_done.md"

Scenario: [TCAE-ST-02] [Tier C - Integration] Done Gate chuyển từ FAIL sang PASS sau khi file trong Evidence files được tạo ra
  Given một task khai báo ".devtool/epic/sample_epic/evidence/summary.json (new)" dưới mục "Evidence files:"
  When hàm "evaluate_done_gate" chạy trước khi file ".devtool/epic/sample_epic/evidence/summary.json" được tạo trên đĩa
  Then "evaluate_done_gate" trả về lỗi điều kiện chỉ rõ thiếu file ".devtool/epic/sample_epic/evidence/summary.json"
  And khi lượt chạy verification ghi nội dung JSON khác rỗng vào ".devtool/epic/sample_epic/evidence/summary.json"
  Then "evaluate_done_gate" trả về danh sách lỗi rỗng
```

## Chiều 4: Bất đồng bộ và Đồng thời (Async and Concurrency)

```gherkin
Scenario: [TCAE-AR-01] [Tier A - Unit] Cô lập việc tiêm biến môi trường vào tiến trình con giữa các lượt chạy song song
  Given hai lượt gọi "run_task_checks.py" chạy đồng thời trên hai git worktree tạm riêng biệt
  When mỗi lượt gọi thực thi một dòng Verification in ra "$D3NEXUS_KIT" và "$(which d3nexus)"
  Then cả hai tiến trình con đều phân giải đúng đường dẫn gốc của bộ kit mà không làm biến đổi "os.environ" của tiến trình Python cha

Scenario: [TCAE-AR-02] [Tier C - Integration] Đảm bảo tính tất định và lũy đẳng khi chạy render nhiều lần liên tiếp
  Given một thư mục epic có nhiều task bao phủ nhiều kịch bản BDD và chỉ thị nhúng file
  When thực thi lệnh "sync_task_status.py render sample_epic" hai lần liên tiếp mà không có chỉnh sửa trung gian
  Then lần chạy thứ hai tạo ra các file giống hệt từng byte trong cả ".devtool/epic/sample_epic/" và ".devtool/features/"
```

## Chiều 5: Xử lý Lỗi và Phục hồi (Failures and Resilience)

```gherkin
Scenario: [TCAE-FR-01] [Tier A - Unit] Từ chối đường dẫn Evidence files nằm ngoài thư mục evidence của epic hoặc chứa ký tự leo thư mục
  Given một task liệt kê ".devtool/epic/sample_epic/../secret.txt (new)" hoặc "src/output.json (new)" dưới mục "Evidence files:"
  When "check_task_contract.py --design" đánh giá task
  Then công cụ thoát mã 1 và báo lỗi yêu cầu mọi mục trong "Evidence files:" phải nằm dưới ".devtool/epic/<epic_dir>/evidence/" và không chứa ".."

Scenario: [TCAE-FR-02] [Tier A - Unit] Từ chối đường dẫn tuyệt đối chứa thư mục cá nhân hoặc plugin cache và phép gán VAR=value thiếu env
  Given một task có dòng V1 gọi "/Users/alice/antigravity_homes/tess/.claude/plugins/cache/check_document.py"
  And dòng V2 gọi "FOO=bar pytest tests/unit/test_sample.py::test_ok" mà không có tiền tố "env"
  When "check_task_contract.py --design" đánh giá task
  Then công cụ thoát mã 1 báo lỗi đường dẫn tuyệt đối không khả chuyển tại V1 và phép gán biến môi trường thiếu "env" tại V2

Scenario: [TCAE-FR-03] [Tier C - Integration] Lệnh render dừng an toàn khi Covers tham chiếu tới mã scenario không tồn tại hoặc thiếu file nhúng
  Given một task trong ".devtool/epic/sample_epic/" có dòng "Covers:" liệt kê "TCAE-HP-99" không tồn tại trong "bdd_scenarios.en.md"
  When thực thi lệnh "sync_task_status.py render sample_epic"
  Then công cụ thoát mã 1 chỉ rõ mã scenario không xác định "TCAE-HP-99" và giữ nguyên các file hiện có trong ".devtool/features/"
```

