# Kịch Bản BDD: Điều Phối Đa Epic và Quản Trị (Multi-Epic Orchestration and Governance)

## Mục Lục

- [1. Chiều 1 — Luồng Thành Công (Happy Paths)](#1-chiều-1--luồng-thành-công-happy-paths)
- [2. Chiều 2 — Trường Hợp Biên & Giới Hạn (Edge Cases & Boundaries)](#2-chiều-2--trường-hợp-biên--giới-hạn-edge-cases--boundaries)
- [3. Chiều 3 — Chuyển Đổi Trạng Thái (State Transitions)](#3-chiều-3--chuyển-đổi-trạng-thái-state-transitions)
- [4. Chiều 4 — Bất Đồng Bộ & Đồng Thời (Async & Concurrency)](#4-chiều-4--bất-đồng-bộ--đồng-thời-async--concurrency)
- [5. Chiều 5 — Lỗi & Khả Năng Phục Hồi (Failures & Resilience)](#5-chiều-5--lỗi--khả-năng-phục-hồi-failures--resilience)

---

## 1. Chiều 1 — Luồng Thành Công (Happy Paths)

```gherkin
Feature: Multi-Epic Orchestration and Governance — Happy Paths

  Scenario: [MEO-HP-01] [Tier C - Integration] Epic phụ thuộc có khai báo Depends on epic vượt qua kiểm tra hợp đồng lúc thiết kế cùng R5 và tự động phát lại các task tiên quyết
    Given một epic tiên quyết đã đóng gói "epic_alpha" có các task tạo ra "src/alpha_helper.py" với symbol "compute_alpha"
    And một epic phụ thuộc "epic_beta" có HLD khai báo "- **Depends on epic**: epic-alpha"
    And các task của "epic_beta" liệt kê "src/alpha_helper.py" trong "Read-only context" và tham chiếu "compute_alpha" trong "Target Files & Symbols"
    When "check_epic_readiness.py epic_beta" thực thi trước khi "epic_alpha" được merge vào HEAD
    Then R1, R5 và R7 đều đạt với 0 lỗi vì "src/alpha_helper.py" và "compute_alpha" được phân giải từ "epic_alpha"
    And khi "replay_epic_in_worktree()" chạy cho "epic_beta"
    Then nó phát lại các task của "epic_alpha" trước trong worktree tạm thời rồi tiếp nối bằng các task của "epic_beta" và thoát mã 0

  Scenario: [MEO-HP-02] [Tier C - Integration] Lệnh check-conflicts và promote chuyển trạng thái một epic không giao nhau từ backlog sang todo chỉ bằng một lệnh
    Given một epic đang hoạt động "epic_alpha" có các task ở trạng thái "todo" chạm vào "src/alpha.py"
    And một epic đang xếp hàng "epic_gamma" có các task ở trạng thái "backlog" chạm vào "src/gamma.py" và không có epic tiên quyết nào chưa hoàn tất
    When "sync_task_status.py check-conflicts epic_gamma" chạy
    Then nó báo cáo "0 conflicts — safe for concurrent execution" và thoát với mã 0
    And khi "sync_task_status.py promote epic_gamma" chạy
    Then toàn bộ các task "backlog" của "epic_gamma" trong ".devtool/epic/epic_gamma/" và ".devtool/features/" đều chuyển sang "todo"

  Scenario: [MEO-HP-03] [Tier C - Integration] package_epic.py đóng gói epic, xác thực Spec Errata song ngữ và neo lại handoff.md khi chạy --revise
    Given một epic có các tệp HLD ".en.md" và ".vi.md" khai báo mục "## Spec Errata" khớp nhau "[SE-01]"
    When "package_epic.py <epic_dir>" chạy khi kiểm tra sẵn sàng đạt
    Then nó ghi ".devtool/epic/<epic_dir>/handoff.md" neo vào commit HEAD hiện tại
    And khi có một commit sửa đổi sau đóng gói và "package_epic.py <epic_dir> --revise --reason 'Clarify SE-01 contract'" chạy
    Then "handoff.md" cập nhật "Design commit" sang mã SHA HEAD mới và nối thêm dòng lịch sử vào dưới mục "## Revisions"

  Scenario: [MEO-HP-04] [Tier C - Integration] Sổ cái phê duyệt cổng ghi nhận các phê duyệt Gate 1-5 có cấu trúc và trả lời truy vấn --check-gate
    Given một kho lưu trữ có bộ nhớ dự án ".devtool/"
    When "scripts/resume_context.py --gate 2 --epic sample-epic --approved 'HLD and 5 Kanban tasks' --deviations 'SE-01'" được thực thi
    Then ".devtool/state/gate_ledger.jsonl" ghi nhận một dòng JSON chứa "epic": "sample-epic", "gate": 2, "approved": "HLD and 5 Kanban tasks", "deviations": "SE-01" cùng mã SHA commit hiện tại
    And ".devtool/GATE_LEDGER.md" được kết xuất có dòng phê duyệt Gate 2
    And "scripts/resume_context.py --check-gate 2 --epic sample-epic" in ra bản ghi phê duyệt và thoát với mã 0
```

---

## 2. Chiều 2 — Trường Hợp Biên & Giới Hạn (Edge Cases & Boundaries)

```gherkin
Feature: Multi-Epic Orchestration and Governance — Edge Cases & Boundaries

  Scenario: [MEO-EC-01] [Tier A - Unit] Chuỗi phụ thuộc bắc cầu Depends on epic được phân giải theo thứ tự topo và khử trùng lặp tệp cùng symbol tiên quyết
    Given "epic_c" phụ thuộc vào "epic_b" và "epic_b" phụ thuộc vào "epic_a"
    When "resolve_prerequisite_epic_dirs()" và "collect_prerequisite_artifacts()" kiểm tra "epic_c"
    Then "resolve_prerequisite_epic_dirs()" trả về ["epic_a", "epic_b"] theo đúng thứ tự topo
    And "collect_prerequisite_artifacts()" trả về hợp của các tệp và symbol tạo mới trên cả "epic_a" và "epic_b"

  Scenario: [MEO-EC-02] [Tier A - Unit] check_epic_file_conflicts bỏ qua các task đã done của epic khác trong khi phát hiện giao nhau giữa glob và đường dẫn cụ thể trên các task đang hoạt động
    Given "epic_done" chỉ có các task đã "done" chạm vào "src/shared/core.py"
    And "epic_active" có một task đang "in-progress" với mẫu Allowed file glob "src/shared/*.py"
    When "check_epic_file_conflicts()" đánh giá "epic_candidate" có task chạm vào "src/shared/core.py"
    Then nó bỏ qua "epic_done" và chỉ báo cáo xung đột với "epic_active" trên "src/shared/core.py"
```

---

## 3. Chiều 3 — Chuyển Đổi Trạng Thái (State Transitions)

```gherkin
Feature: Multi-Epic Orchestration and Governance — State Transitions

  Scenario: [MEO-ST-01] [Tier A - Unit] sync_task_status.py promote chặn khi epic tiên quyết chưa hoàn tất hoặc có xung đột tệp đang hoạt động trừ khi truyền --force
    Given "epic_beta" phụ thuộc vào "epic_alpha" đang có trạng thái "In Progress"
    When "sync_task_status.py promote epic_beta" được thực thi không kèm "--force"
    Then nó thoát với mã 1 và giữ nguyên các task của "epic_beta" ở trạng thái "backlog"
    And khi "epic_alpha" chuyển sang "Done" (hoặc khi truyền "--force"), "sync_task_status.py promote epic_beta" chuyển toàn bộ các task của "epic_beta" sang "todo" và thoát mã 0

  Scenario: [MEO-ST-02] [Tier A - Unit] package_epic.py --revise giữ nguyên nội dung Open Notes tùy chỉnh trong khi cập nhật Design commit, mã SHA git log kiểm tra lỗi thời và mục Revisions
    Given một tệp "handoff.md" hiện có chứa các gạch đầu dòng tùy chỉnh dưới "## Open Notes" và "Design commit: `aaa1111`"
    When "package_epic.py <epic_dir> --revise --reason 'Align task 02 CLI flags'" chạy tại commit "bbb2222"
    Then "## Open Notes" giữ nguyên toàn bộ các gạch đầu dòng tùy chỉnh
    And "Design commit" cùng lệnh kiểm tra lỗi thời "git log" được cập nhật sang "bbb2222"
    And "## Revisions" liệt kê "`aaa1111` -> `bbb2222`" kèm lý do "Align task 02 CLI flags"
```

---

## 4. Chiều 4 — Bất Đồng Bộ & Đồng Thời (Async & Concurrency)

```gherkin
Feature: Multi-Epic Orchestration and Governance — Async & Concurrency

  Scenario: [MEO-AR-01] [Tier A - Unit] Các lệnh gọi resume_context.py --gate đồng thời được tuần tự hóa dưới fcntl.flock mà không làm mất bản ghi phê duyệt
    Given 4 tiến trình con song song gọi "scripts/resume_context.py --gate <n> --epic concurrent-epic --approved 'Gate <n> scope'" cùng lúc
    When cả 4 tiến trình con hoàn tất
    Then ".devtool/state/gate_ledger.jsonl" chứa đủ 4 dòng JSON hợp lệ mà không có bản ghi nào bị đan xen hay cắt cụt
    And ".devtool/GATE_LEDGER.md" chứa đủ 4 dòng phê duyệt cổng

  Scenario: [MEO-AR-02] [Tier A - Unit] sync_task_status.py promote đồng bộ trạng thái task trên cả thư mục epic và bản sao features trong mọi checkout
    Given một epic đang xếp hàng có 3 task ở trạng thái "backlog" được nhân bản tại cả ".devtool/epic/<epic_dir>/" và ".devtool/features/"
    When "sync_task_status.py promote <epic_dir>" thực thi
    Then cả 6 tệp task trên ".devtool/epic/<epic_dir>/" và ".devtool/features/" đều được cập nhật nguyên tử sang "status: \"todo\"" kèm dấu thời gian "modified" mới
```

---

## 5. Chiều 5 — Lỗi & Khả Năng Phục Hồi (Failures & Resilience)

```gherkin
Feature: Multi-Epic Orchestration and Governance — Failures & Resilience

  Scenario: [MEO-FR-01] [Tier A - Unit] R7 thất bại khi Depends on epic tham chiếu tới thư mục epic không tồn tại hoặc tạo thành chu trình phụ thuộc
    Given một HLD của epic có dòng "Depends on epic:" trỏ tới một epic không tồn tại "missing-epic" hoặc tạo chu trình "epic_a -> epic_b -> epic_a"
    When "check_epic_readiness.py" chạy bước xác minh metadata R7
    Then R7 thất bại và báo cáo chính xác epic tiên quyết bị thiếu hoặc chu trình phụ thuộc

  Scenario: [MEO-FR-02] [Tier A - Unit] R7 và package_epic.py thất bại khi mã Spec Errata lệch nhau giữa .en.md và .vi.md hoặc khi --revise thiếu --reason
    Given một epic trong đó ".en.md" khai báo "[SE-01]" và "[SE-02]" dưới "## Spec Errata" trong khi ".vi.md" chỉ khai báo "[SE-01]"
    When "check_epic_readiness.py" đánh giá R7
    Then R7 thất bại và báo cáo mã Spec Errata bất đối xứng "[SE-02]"
    And khi "package_epic.py <epic_dir> --revise" được gọi mà không có "--reason"
    Then nó thoát với mã 2 và báo lỗi rằng "--reason" là bắt buộc khi dùng "--revise"

  Scenario: [MEO-FR-03] [Tier A - Unit] resume_context.py từ chối --gate có chuỗi --approved rỗng và thoát mã 1 khi gọi --check-gate cho cổng chưa được phê duyệt
    Given một kho lưu trữ trong đó Gate 3 chưa được phê duyệt cho "sample-epic"
    When "scripts/resume_context.py --check-gate 3 --epic sample-epic" được thực thi
    Then nó thoát với mã 1 và báo cáo rằng Gate 3 chưa được ghi nhận cho "sample-epic"
    And khi "scripts/resume_context.py --gate 3 --epic sample-epic --approved ''" được thực thi với chuỗi phạm vi rỗng
    Then nó thoát với mã 2 mà không làm thay đổi ".devtool/state/gate_ledger.jsonl"
```
