# Kịch bản BDD Principal Review

## Mục lục

- [Ma trận bao phủ](#ma-trận-bao-phủ)
- [Ca sử dụng 1: Kiểm tra readiness cơ học](#ca-sử-dụng-1-kiểm-tra-readiness-cơ-học)
- [Ca sử dụng 2: Round Principal Review](#ca-sử-dụng-2-round-principal-review)
- [Ca sử dụng 3: Phạm vi đồng bộ trạng thái epic](#ca-sử-dụng-3-phạm-vi-đồng-bộ-trạng-thái-epic)
- [Ca sử dụng 4: Quy trình vòng đời](#ca-sử-dụng-4-quy-trình-vòng-đời)

## Ma trận bao phủ

| Mã kịch bản | Chiều kiểm thử | Thành phần mục tiêu | Mô tả |
|---|---|---|---|
| `[PRV-HP-01]` | Happy Path | `check_epic_readiness.py` | Một epic fixture sẵn sàng qua mọi kiểm tra |
| `[PRV-HP-02]` | Happy Path | `run_external_review.py` | Một round principal được ghi vào `principal_review.md` |
| `[PRV-HP-03]` | Happy Path | `run_external_review.py` | Phát hiện kèm chỉnh sửa đề xuất thành dòng bảng và quyết định mã thoát |
| `[PRV-HP-04]` | Happy Path | `dev-lifecycle` | Đóng gói chạy một lệnh readiness và đưa ra Principal Review Choice |
| `[PRV-HP-05]` | Happy Path | `sync_task_status.py` | `epic` cập nhật checkout chính và worktree của chính epic |
| `[PRV-EC-01]` | Edge Case | `check_epic_readiness.py` | Một symbol không có trong file của nó làm R5 FAIL |
| `[PRV-EC-02]` | Edge Case | `check_epic_readiness.py` | Lệch tier làm R3 FAIL và một tag Tier B làm R4 FAIL |
| `[PRV-EC-03]` | Edge Case | `check_epic_readiness.py` | Một test TIER-C nằm ngoài mọi lệnh Integration results làm R6 FAIL |
| `[PRV-EC-04]` | Edge Case | `check_epic_readiness.py` | Mirror lệch làm R2 FAIL; khác biệt chỉ ở link phụ thuộc vị trí thì qua |
| `[PRV-EC-05]` | Edge Case | `check_epic_readiness.py` | Packaged mà không có handoff làm R7 FAIL; spec nháp cảnh báo R7b |
| `[PRV-EC-06]` | Edge Case | `check_epic_readiness.py` | Một route không có trong file source nào cảnh báo R5b mà không FAIL |
| `[PRV-EC-07]` | Edge Case | `handoff-template.md` | Read First liệt kê `principal_review.md` |
| `[PRV-ST-01]` | State Transition | `run_external_review.py` | Quyết định đưa `check --kind principal` từ 1 về 0, độc lập với các round code |
| `[PRV-ST-02]` | State Transition | `run_external_review.py` | `triage` đọc file mà `--kind` chọn |
| `[PRV-ST-03]` | State Transition | `dev-lifecycle`, tài liệu vòng đời | Vòng lặp quay về Package và Done đóng gói lại sau một round |
| `[PRV-ST-04]` | State Transition | `dev-implementation` | Gate 3 dừng khi còn phát hiện principal chặn chưa quyết |
| `[PRV-AR-01]` | Async / Race | `run_external_review.py` | Round thứ hai trước khi round đầu được commit bị từ chối; các round đánh số theo thứ tự |
| `[PRV-FR-01]` | Failure & Resilience | `check_epic_readiness.py` | Lỗi và timeout ở baseline chỉ cảnh báo, các dòng khác vẫn chạy |
| `[PRV-FR-02]` | Failure & Resilience | `check_epic_readiness.py` | Một kiểm tra con của preflight thất bại làm R1 FAIL theo tên |
| `[PRV-FR-03]` | Failure & Resilience | `run_external_review.py` | Readiness FAIL chặn CLI và không ghi gì |
| `[PRV-FR-04]` | Failure & Resilience | `run_external_review.py` | `--kind principal --cli ollama` bị từ chối trước mọi việc |
| `[PRV-FR-05]` | Failure & Resilience | `sync_task_status.py` | Worktree của epic khác giữ nguyên từng byte; đồng bộ `task` vẫn mirror ở mọi nơi |

## Ca sử dụng 1: Kiểm tra readiness cơ học

### PRV-HP-01: Epic sẵn sàng thì qua

```gherkin
Scenario: [PRV-HP-01] [Tier C - Integration] Một epic fixture sẵn sàng qua mọi kiểm tra
  Given một repo tạm có epic "demo_epic" với 2 task mang epic "demo-epic", mirror trong .devtool/features/, bản copy Gherkin đúng gốc, symbol có thật, đường dẫn TIER-C được phủ và spec đã duyệt
  When check_epic_readiness.py demo_epic chạy
  Then dòng đầu là "Epic: demo_epic (demo-epic), 2 tasks"
  And output có các dòng "R1 PASS" đến "R7 PASS" theo thứ tự, rồi "R8 SKIP"
  And dòng cuối là "Result: 0 FAIL, 0 WARN — PASS"
  And mã thoát là 0
```

### PRV-EC-01: Thiếu symbol

```gherkin
Scenario: [PRV-EC-01] [Tier C - Integration] Một symbol không có trong file của nó làm R5 FAIL
  Given epic của PRV-HP-01 có task_2 liệt kê "- `src/app.py`: `build_payload()`, new `render()`" trong Target Files & Symbols
  And src/app.py tồn tại nhưng không chứa chuỗi "build_payload"
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R5 FAIL" chứa "task_2", "build_payload" và "src/app.py"
  And không dòng R5 nào nhắc tới "render"
  And dòng cuối kết thúc bằng "— FAIL" và mã thoát là 1
```

### PRV-EC-02: Lệch tier

```gherkin
Scenario: [PRV-EC-02] [Tier C - Integration] Lệch tier làm R3 FAIL và một tag Tier B làm R4 FAIL
  Given epic của PRV-HP-01 có bdd_scenarios.en.md gắn DEMO-HP-01 là "[Tier B - Unit]" trong khi task_1 copy nó là "[Tier A - Unit]"
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R3 FAIL" chứa "task_1" và "DEMO-HP-01"
  And một dòng bắt đầu bằng "R4 FAIL" chứa "DEMO-HP-01" và "Tier B - Unit"
  And mã thoát là 1
```

### PRV-EC-03: Đường dẫn Gate 4 không được phủ

```gherkin
Scenario: [PRV-EC-03] [Tier C - Integration] Một test TIER-C nằm ngoài mọi lệnh Integration results làm R6 FAIL
  Given epic của PRV-HP-01 có dòng TIER-C của task_2 chạy "python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml tests/test_extra.py"
  And lệnh Integration results duy nhất của HLD chỉ nêu "tests/test_core.py"
  And "tests/" là một thư mục Integration test roots
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R6 FAIL" chứa "task_2" và "tests/test_extra.py"
  And mã thoát là 1
```

### PRV-EC-04: Mirror lệch

```gherkin
Scenario: [PRV-EC-04] [Tier C - Integration] Mirror lệch làm R2 FAIL và khác biệt chỉ ở link phụ thuộc vị trí thì qua
  Given epic của PRV-HP-01 có mirror task_1 trong .devtool/features/ link tới "../epic/demo_epic/demo_epic.en.md" còn bản trong epic link tới "demo_epic.en.md"
  When check_epic_readiness.py demo_epic chạy
  Then output có dòng "R2 PASS"
  When phần Requirement Analysis của mirror có thêm dòng "Stale sentence."
  And check_epic_readiness.py demo_epic chạy lại
  Then output có một dòng bắt đầu bằng "R2 FAIL" chứa "task_1" và "Stale sentence."
  And mã thoát là 1
```

### PRV-EC-05: Metadata

```gherkin
Scenario: [PRV-EC-05] [Tier C - Integration] Packaged mà không có handoff làm R7 FAIL và spec nháp cảnh báo R7b
  Given epic của PRV-HP-01 có Status của HLD là "Packaged" và thư mục không có handoff.md
  And Status của spec là "Draft, awaiting Gate 1 review"
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R7 FAIL" chứa "handoff.md"
  And một dòng bắt đầu bằng "R7b WARN" chứa "Draft, awaiting Gate 1 review"
  And mã thoát là 1
  When handoff.md được thêm với "- **Design commit**: `uncommitted`" và Status của spec vẫn là nháp
  And check_epic_readiness.py demo_epic chạy lại
  Then output có dòng "R7 PASS" và mã thoát là 0
```

### PRV-EC-06: Route không tồn tại

```gherkin
Scenario: [PRV-EC-06] [Tier C - Integration] Một route không có trong file source nào cảnh báo R5b mà không FAIL
  Given epic của PRV-HP-01 có task_1 nêu "/api/tts/ocr-upload" và file source duy nhất được git theo dõi nêu "/api/studio/extract/start"
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R5b WARN" chứa "/api/tts/ocr-upload"
  And không dòng nào nhắc tới "/api/studio/extract/start"
  And dòng cuối là "Result: 0 FAIL, 1 WARN — PASS" và mã thoát là 0
```

### PRV-FR-01: Lỗi ở baseline

```gherkin
Scenario: [PRV-FR-01] [Tier C - Integration] Lỗi và timeout ở baseline chỉ cảnh báo, các dòng khác vẫn chạy
  Given epic của PRV-HP-01 trong cây sạch có task_1 với các dòng V2 GREEN "python3 -c 'raise SystemExit(1)'" mong đợi "exit 0", V3 TIER-B "sleep 5" mong đợi "exit 0", và V4 GREEN "python3 -c 'print(1)'" mong đợi "exit 0"
  And task_2 có một dòng GREEN mà lệnh nêu một đường dẫn được đánh dấu (new)
  When check_epic_readiness.py demo_epic --baseline --row-timeout 2 chạy
  Then output có một dòng bắt đầu bằng "R8 WARN" chứa "task_1:V2"
  And một dòng bắt đầu bằng "R8 WARN" chứa "task_1:V3" và "timeout"
  And không dòng R8 nào nhắc tới "task_1:V4" hay dòng của task_2
  And mã thoát là 0
  When cây có một thay đổi chưa commit và cùng lệnh đó chạy
  Then output có dòng "R8 WARN baseline skipped: dirty tree"
```

### PRV-FR-02: Kiểm tra con của preflight thất bại

```gherkin
Scenario: [PRV-FR-02] [Tier C - Integration] Một kiểm tra con của preflight thất bại làm R1 FAIL theo tên
  Given epic của PRV-HP-01 có bdd_scenarios.en.md thêm DEMO-EC-09 mà không task nào phủ
  When check_epic_readiness.py demo_epic chạy
  Then output có một dòng bắt đầu bằng "R1 FAIL" chứa "check_bdd_traceability.py plan"
  And mã thoát là 1
  When check_epic_readiness.py chạy với một thư mục không tồn tại
  Then mã thoát là 2
```

## Ca sử dụng 2: Round Principal Review

### PRV-HP-02: Một round principal được ghi

```gherkin
Scenario: [PRV-HP-02] [Tier C - Integration] Một round principal được ghi vào principal_review.md
  Given epic của PRV-HP-01 đã commit trong cây sạch và một "claude" giả trên PATH lưu stdin của nó và in "Verdict: PASS"
  When run_external_review.py run --kind principal --epic-dir demo_epic --base main --cli claude chạy
  Then prompt đã lưu chứa "Principal Reviewer", "Result: 0 FAIL, 0 WARN — PASS", ".devtool/epic/demo_epic/demo_epic.en.md" và SHA của main
  And prompt đã lưu không chứa "audit_epic.py"
  And principal_review.md bắt đầu bằng "# Principal Review: demo_epic" và có "## Round 1" với "- **Kind**: principal", "- **CLI**: claude", "- **Status**: completed" và "- **Verdict**: PASS"
  And review_results.md không tồn tại
  And mã thoát là 0
```

### PRV-HP-03: Phát hiện kèm chỉnh sửa đề xuất

```gherkin
Scenario: [PRV-HP-03] [Tier C - Integration] Phát hiện kèm chỉnh sửa đề xuất thành dòng bảng và quyết định mã thoát
  Given một "codex" giả in "Verdict: CHANGES REQUIRED" và "[Important] task_2:Decisions Already Made — persist_track returns a dict. Proposed: keep TrackPersistResult."
  When run --kind principal --cli codex chạy
  Then principal_review.md có một dòng phát hiện với "Important", "task_2:Decisions Already Made" và "Proposed: keep TrackPersistResult."
  And round có "- **Verdict**: CHANGES REQUIRED"
  And mã thoát là 1
```

### PRV-ST-01: Quyết định mở khóa check

```gherkin
Scenario: [PRV-ST-01] [Tier C - Integration] Quyết định đưa check --kind principal từ 1 về 0, độc lập với các round code
  Given principal_review.md có round hoàn tất mới nhất với một phát hiện Important và ô Decision trống
  And review_results.md có round mới nhất không có phát hiện nào
  When run_external_review.py check --kind principal --epic-dir demo_epic chạy
  Then nó in "undecided: #1 Important" và thoát với mã 1
  And check --epic-dir demo_epic không có --kind thoát với mã 0
  When ô Decision thành "fixed in abc1234"
  Then check --kind principal thoát với mã 0
```

### PRV-ST-02: Triage đọc file được chọn

```gherkin
Scenario: [PRV-ST-02] [Tier C - Integration] triage đọc file mà --kind chọn
  Given principal_review.md có 2 round và review_results.md có 1 round
  When run_external_review.py triage --kind principal --epic-dir demo_epic chạy
  Then output bắt đầu bằng "# Review Triage: demo_epic, Round 2"
  And triage không có --kind in "Round 1"
  When principal_review.md không tồn tại
  Then triage --kind principal in "no review round recorded for demo_epic" và thoát với mã 2
```

### PRV-AR-01: Các round theo thứ tự

```gherkin
Scenario: [PRV-AR-01] [Tier C - Integration] Round thứ hai trước khi round đầu được commit bị từ chối và các round đánh số theo thứ tự
  Given round principal 1 đã hoàn tất và được ghi nhưng chưa commit
  When run --kind principal chạy lần nữa
  Then nó in "commit or stash your changes before a review" và thoát với mã 2
  And CLI giả chỉ được gọi đúng một lần tính tổng
  When round 1 được commit và run --kind principal chạy lần nữa
  Then principal_review.md có "## Round 1" rồi tới "## Round 2"
```

### PRV-FR-03: Readiness chặn CLI

```gherkin
Scenario: [PRV-FR-03] [Tier C - Integration] Readiness FAIL chặn CLI và không ghi gì
  Given epic của PRV-EC-01 đã commit trong cây sạch và một "claude" giả ghi lại mọi lần gọi
  When run --kind principal --cli claude chạy
  Then stderr hiện "WAS NOT INVOKED" và "check_epic_readiness.py"
  And stderr hiện dòng chứa "R5 FAIL"
  And CLI giả không bao giờ được gọi
  And principal_review.md không tồn tại và mã thoát là 2
```

### PRV-FR-04: Ollama bị từ chối

```gherkin
Scenario: [PRV-FR-04] [Tier C - Integration] --kind principal --cli ollama bị từ chối trước mọi việc
  Given một repo epic tạm có một thay đổi chưa commit
  When run --kind principal --cli ollama --model m chạy
  Then stderr hiện "--kind principal supports --cli claude or codex"
  And stderr không bao giờ hiện "[Pre-check]"
  And mã thoát là 2 và không có principal_review.md nào
```

## Ca sử dụng 3: Phạm vi đồng bộ trạng thái epic

### PRV-HP-05: Worktree của chính epic được cập nhật

```gherkin
Scenario: [PRV-HP-05] [Tier C - Integration] epic cập nhật checkout chính và worktree của chính epic
  Given một repo tạm có epic "demo_epic" (slug "demo-epic") và một worktree trên nhánh "epic/demo-epic"
  When sync_task_status.py epic demo_epic Packaged chạy trong checkout chính
  Then demo_epic.en.md và demo_epic.vi.md ghi "Packaged" ở cả hai checkout
```

### PRV-FR-05: Epic khác không bị đụng

```gherkin
Scenario: [PRV-FR-05] [Tier C - Integration] Worktree của epic khác giữ nguyên từng byte và đồng bộ task vẫn mirror ở mọi nơi
  Given repo của PRV-HP-05 cùng một worktree trên nhánh "epic/other-epic" cũng chứa .devtool/epic/demo_epic/
  When sync_task_status.py epic demo_epic Packaged chạy trong checkout chính
  Then git status trong worktree "epic/other-epic" rỗng
  When sync_task_status.py task task_1_demo in-progress chạy
  Then task_1_demo ghi "in-progress" ở cả ba checkout
```

## Ca sử dụng 4: Quy trình vòng đời

### PRV-HP-04: Đóng gói đưa ra lựa chọn

```gherkin
Scenario: [PRV-HP-04] [Tier C - Integration] Đóng gói chạy một lệnh readiness và đưa ra Principal Review Choice
  Given skills/dev-lifecycle/SKILL.md và skills/dev-lifecycle/references/principal-review.md
  Then skill chứa "check_epic_readiness.py <epic_dir>", "Principal Review Choice" và "references/principal-review.md"
  And skill không còn chứa "check_bdd_traceability.py plan --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md --tasks"
  And skill có tối đa 2500 từ và giữ mọi token đã ghim của dev-lifecycle
  And reference chứa "1. **Done**", "2. **Principal Review**", "Claude CLI", "Codex CLI", "Never choose for the developer" và "strongly recommended"
```

### PRV-EC-07: Read First của handoff

```gherkin
Scenario: [PRV-EC-07] [Tier C - Integration] Read First liệt kê principal_review.md
  Given skills/dev-lifecycle/references/handoff-template.md
  Then phần Read First của nó chứa ".devtool/epic/<epic_dir>/principal_review.md, when present"
  And nó giữ nguyên "`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>`"
```

### PRV-ST-03: Vòng lặp quay về Package

```gherkin
Scenario: [PRV-ST-03] [Tier C - Integration] Vòng lặp quay về Package và Done đóng gói lại sau một round
  Given docs/lifecycles.en.md, docs/lifecycles.vi.md và skills/dev-lifecycle/references/principal-review.md
  Then cả hai tài liệu chứa 'PKG --> PRC', 'PRC -->|"2. Principal Review"| PR' và 'PR -->|"revised and re-packaged"| PKG'
  And không tài liệu nào có cạnh từ PR tới S3 hay tới G3
  And reference chứa "Record Principal Review round <n>", "Revise epic after Principal Review round <n>" và "Package epic for handoff"
  And reference nói rằng Done chạy "check --kind principal" và đóng gói lại khi commit cuối cùng chạm vào thư mục epic không phải commit Package
```

### PRV-ST-04: Gate 3 dừng khi còn phát hiện chưa quyết

```gherkin
Scenario: [PRV-ST-04] [Tier C - Integration] Gate 3 dừng khi còn phát hiện principal chặn chưa quyết
  Given skills/dev-implementation/SKILL.md
  Then Entry-Point Detection chứa "run_external_review.py check --kind principal --epic-dir <epic_dir>"
  And Phase 1 bước 3 và Gate 3 khi resume đều nhắc "Principal Review" với "not run", "round <n>: PASS" và "round <n>: decided"
  And skill có tối đa 4500 từ
```
