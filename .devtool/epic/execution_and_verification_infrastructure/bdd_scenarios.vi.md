# Kịch Bản BDD: Hạ Tầng Thực Thi và Xác Minh (Execution and Verification Infrastructure)

## Mục Lục

- [1. Chiều 1 — Luồng Thành Công (Happy Paths)](#1-chiều-1--luồng-thành-công-happy-paths)
- [2. Chiều 2 — Trường Hợp Biên & Giới Hạn (Edge Cases & Boundaries)](#2-chiều-2--trường-hợp-biên--giới-hạn-edge-cases--boundaries)
- [3. Chiều 3 — Chuyển Đổi Trạng Thái (State Transitions)](#3-chiều-3--chuyển-đổi-trạng-thái-state-transitions)
- [4. Chiều 4 — Bất Đồng Bộ & Đồng Thời (Async & Concurrency)](#4-chiều-4--bất-đồng-bộ--đồng-thời-async--concurrency)
- [5. Chiều 5 — Lỗi & Khả Năng Phục Hồi (Failures & Resilience)](#5-chiều-5--lỗi--khả-năng-phục-hồi-failures--resilience)

---

## 1. Chiều 1 — Luồng Thành Công (Happy Paths)

```gherkin
Feature: Execution and Verification Infrastructure — Happy Paths

  Scenario: [EVI-HP-01] [Tier C - Integration] Worktree bootstrap thực thi các lệnh bootstrap trong python-quality.json và cài đặt phụ thuộc đa ngôn ngữ (polyglot)
    Given một kho lưu trữ git đa ngôn ngữ chứa cả "pyproject.toml" và "package.json"
    And ".agents/quality/python-quality.json" định nghĩa "bootstrap" là [["pip", "install", "-e", ".[dev]"]]
    When "detect_project_type.sh --all" được thực thi trên kho lưu trữ
    Then nó xuất ra "python web"
    And khi "bootstrap_worktree.sh" chạy trên một worktree của kho lưu trữ
    Then nó thực thi cả pha bootstrap Python (bao gồm các mảng lệnh "bootstrap" từ ".agents/quality/python-quality.json") và pha cài đặt phụ thuộc Web

  Scenario: [EVI-HP-02] [Tier C - Integration] Ghi nhận baseline tập lỗi và so sánh hồi quy đạt khi không có lỗi mới xuất hiện
    Given một luồng đầu ra pytest chứa 2 node ID kiểm thử thất bại có sẵn trong khối tóm tắt cuối "=== short test summary info ==="
    When "record_failure_baseline.py --out baseline.txt" phân tích luồng đầu ra
    Then "baseline.txt" chứa 2 node ID lỗi đã sắp xếp
    And khi "compare_failure_sets.py --baseline baseline.txt --current current.txt" chạy với danh sách lỗi hiện tại là tập con của 2 node ID đó
    Then nó báo cáo 0 lỗi mới và thoát với mã 0

  Scenario: [EVI-HP-03] [Tier C - Integration] Bảng kết quả tích hợp live tùy chọn thỏa mãn độ phủ R6, bỏ qua sạch khi thiếu biến môi trường và thực thi khi biến môi trường được đặt
    Given một HLD của epic chứa cả "Integration results:" và "Integration results (live, needs: EVI_LIVE_MODEL):"
    And "bdd_scenarios.en.md" khai báo một kịch bản "[Tier C - Integration]" có tệp kiểm thử nằm trong lệnh tích hợp live
    When "check_epic_readiness.py" đánh giá độ phủ R6 cho epic
    Then R6 đạt với 0 tệp kiểm thử Tier C bị thiếu
    And khi "collect_facts()" trong "run_external_review.py" chạy với "EVI_LIVE_MODEL" không được đặt trong môi trường
    Then dòng tích hợp live được ghi nhận là "SKIPPED (missing env: EVI_LIVE_MODEL)" mà không làm trượt Gate 4
    And khi "collect_facts()" trong "run_external_review.py" chạy với "EVI_LIVE_MODEL=1" được đặt trong môi trường
    Then dòng tích hợp live được thực thi và mã thoát của nó được cưỡng chế

  Scenario: [EVI-HP-04] [Tier C - Integration] Bộ phát lại văn bản task áp dụng các chỉ thị code block trong worktree nháp và pha MEASURE thực thi cùng ghi nhận bằng chứng
    Given một tệp task chứa các khối mã "Create", "Replace in" và "Insert in", các dòng "Phase: MEASURE" và "Evidence files: .devtool/epic/sample_epic/evidence/bench.json"
    When "replay_task_text.py" phát lại task bên trong một git worktree tạm thời
    Then các chỉ thị test được áp dụng trước dòng "RED", chỉ thị sản phẩm áp dụng trước dòng "MEASURE" và tất cả lệnh Verification đều đạt
    And khi "run_task_checks.py measure" thực thi task
    Then các dòng "MEASURE" chạy, tạo ra ".devtool/epic/sample_epic/evidence/bench.json" và ghi nhận mục "measure" đạt vào tệp JSON bằng chứng của task
```

---

## 2. Chiều 2 — Trường Hợp Biên & Giới Hạn (Edge Cases & Boundaries)

```gherkin
Feature: Execution and Verification Infrastructure — Edge Cases & Boundaries

  Scenario: [EVI-EC-01] [Tier A - Unit] Bộ phân tích tập lỗi bỏ qua các dòng log ERROR trước short test summary info và ghi dòng đánh dấu khi có 0 lỗi
    Given một luồng đầu ra pytest chứa các dòng log "ERROR logger:module.py:42" trong stdout trước "=== short test summary info ==="
    When "record_failure_baseline.py" trích xuất các ID lỗi từ luồng đầu ra
    Then nó bỏ qua các dòng logger đã bắt và chỉ trích xuất các dòng "FAILED <nodeid>" và "ERROR <nodeid>" từ khối tóm tắt cuối
    And khi có 0 kiểm thử thất bại hoặc lỗi trong khối tóm tắt cuối
    Then "record_failure_baseline.py" ghi "# 0 failures\n" vào tệp đầu ra để tệp không bị rỗng

  Scenario: [EVI-EC-02] [Tier A - Unit] Trình chạy task tự động tạo thư mục cha cho cờ đầu ra JUnit XML trước khi thực thi các dòng Verification
    Given một dòng Verification của task chứa "--junitxml=.devtool/evidence/nested/junit/report.xml" trong đó ".devtool/evidence/nested/junit" chưa tồn tại
    When "run_task_checks.py" thực thi dòng Verification
    Then "ensure_output_dirs()" tạo ".devtool/evidence/nested/junit" trước khi gọi tiến trình con để trình chạy kiểm thử ghi báo cáo XML không gặp lỗi

  Scenario: [EVI-EC-03] [Tier A - Unit] Kiểm tra trôi lệch route R5b khớp các chuỗi route cụ thể với mẫu route có tham số mà không cảnh báo sai
    Given một tệp task tham chiếu đến chuỗi route cụ thể "http://localhost/api/align/stream/job_plt"
    And codebase đích định nghĩa route có tham số "http://localhost/api/align/stream/{job_id}" (hoặc "<job_id>" hoặc ":job_id")
    When "check_epic_readiness.py" chạy kiểm tra trôi lệch route R5b
    Then "route_matches_codebase()" khớp route cụ thể với mẫu có tham số và phát ra 0 cảnh báo R5b
```

---

## 3. Chiều 3 — Chuyển Đổi Trạng Thái (State Transitions)

```gherkin
Feature: Execution and Verification Infrastructure — State Transitions

  Scenario: [EVI-ST-01] [Tier A - Unit] So sánh tập lỗi với --rerun-new phân loại lỗi đạt cô lập so với lỗi bền vững và yêu cầu cờ tường minh để bỏ qua lỗi đạt cô lập
    Given một tệp baseline có 0 lỗi và một tệp lỗi hiện tại có 2 node ID lỗi mới tiềm năng (bao gồm ID có tham số chứa khoảng trắng)
    When "compare_failure_sets.py --baseline baseline.txt --current current.txt --rerun-new" chạy
    And ứng viên đầu tiên đạt khi được chạy lại cô lập qua "--rerun-cmd" trong khi ứng viên thứ hai thất bại
    Then ứng viên đầu tiên được phân loại là "ISOLATED_PASS" và ứng viên thứ hai là "PERSISTENT_FAILURE" đồng thời lệnh thoát với mã 1
    And khi tất cả ứng viên đều đạt khi chạy cô lập, "compare_failure_sets.py --rerun-new" vẫn thoát với mã 1 trừ khi "--allow-isolated-pass" được truyền tường minh

  Scenario: [EVI-ST-02] [Tier C - Integration] run_task_checks.py measure --resume chỉ tái sử dụng kết quả MEASURE đã lưu khi tree, hợp đồng dòng và mã băm tệp bằng chứng khớp
    Given một tệp task có các dòng "Phase: MEASURE" và "Evidence files: .devtool/epic/sample_epic/evidence/bench.json"
    And một lần chạy "run_task_checks.py measure" trước đó đã ghi nhận "runs.measure.passed = true" kèm worktree tree, lệnh/expect của dòng và mã băm SHA-256 của ".devtool/epic/sample_epic/evidence/bench.json" khớp
    When "run_task_checks.py measure <task.md> --resume" được gọi trên tree và tệp bằng chứng không thay đổi
    Then nó bỏ qua việc thực thi lại các lệnh tiến trình con "MEASURE" và thoát với mã 0
    And khi worktree tree, lệnh của dòng hoặc nội dung ".devtool/epic/sample_epic/evidence/bench.json" bị sửa đổi, "--resume" hủy hiệu lực bộ nhớ đệm và thực thi lại các dòng "MEASURE"
```

---

## 4. Chiều 4 — Bất Đồng Bộ & Đồng Thời (Async & Concurrency)

```gherkin
Feature: Execution and Verification Infrastructure — Async & Concurrency

  Scenario: [EVI-AR-01] [Tier C - Integration] check_epic_readiness.py --replay thực thi văn bản task trong worktree nháp cô lập và dọn dẹp mà không làm thay đổi cây làm việc chính
    Given một epic có các task chứa các chỉ thị "Create", "Replace in" và "Insert in" hợp lệ
    When "check_epic_readiness.py <epic> --replay" được thực thi
    Then nó tạo một git worktree tạm thời, phát lại tuần tự các chỉnh sửa của từng task, chạy các lệnh Verification và xóa worktree tạm thời khi hoàn tất
    And "git status --porcelain" trên kho lưu trữ chính hoàn toàn không thay đổi

  Scenario: [EVI-AR-02] [Tier A - Unit] record_failure_baseline.py --restore khôi phục các tệp được theo dõi bị làm bẩn do tác dụng phụ của quá trình chạy kiểm thử
    Given một lệnh bộ kiểm thử làm thay đổi tệp được theo dõi "config/sample.json" trong quá trình thực thi
    When "record_failure_baseline.py --cmd '<test_cmd>' --out baseline.txt --restore config/sample.json" chạy
    Then sau khi lệnh kiểm thử hoàn tất, "record_failure_baseline.py" thực thi "git checkout -- config/sample.json" để tệp được theo dõi khôi phục về trạng thái HEAD sạch
```

---

## 5. Chiều 5 — Lỗi & Khả Năng Phục Hồi (Failures & Resilience)

```gherkin
Feature: Execution and Verification Infrastructure — Failures & Resilience

  Scenario: [EVI-FR-01] [Tier A - Unit] validate_python_quality.py từ chối các cấu hình bootstrap sai định dạng với mã invalid_bootstrap_format
    Given một tệp ".agents/quality/python-quality.json" trong đó "bootstrap" không phải là một danh sách khác rỗng chứa các mảng đối số chuỗi khác rỗng
    When "validate_python_quality.py" xác thực cấu hình
    Then nó báo lỗi xác thực và phát ra lỗi với mã "invalid_bootstrap_format"

  Scenario: [EVI-FR-02] [Tier A - Unit] Xác minh điểm neo tĩnh R5 thất bại khi điểm neo Replace in hoặc Insert in bị thiếu hoặc mơ hồ trong tệp đích
    Given một tệp task chứa chỉ thị "Replace in <path>:" hoặc "Insert in <path>:" có đoạn văn bản điểm neo xuất hiện 0 lần hoặc từ 2 lần trở lên trong "<path>"
    When "verify_task_edit_anchors()" trong "check_epic_readiness.py" kiểm tra task
    Then R5 thất bại và báo cáo chính xác đường dẫn tệp cùng đoạn điểm neo bị thiếu hoặc mơ hồ

  Scenario: [EVI-FR-03] [Tier A - Unit] evaluate_done_gate thất bại khi một task chứa các dòng MEASURE bị thiếu, thất bại hoặc lỗi thời so với tree và mã băm bằng chứng hiện tại
    Given một tệp task chứa ít nhất một dòng Verification có "Phase: MEASURE"
    And tệp JSON bằng chứng của task thiếu "runs.measure", có "runs.measure.passed == false", hoặc có "tree", hợp đồng dòng hay mã băm SHA-256 của tệp bằng chứng không khớp
    When "evaluate_done_gate()" đánh giá task để chuyển sang trạng thái "done"
    Then nó trả về danh sách lỗi khác rỗng chặn việc chuyển sang "done" cho đến khi một lần chạy "run_task_checks.py measure" mới đạt
```

