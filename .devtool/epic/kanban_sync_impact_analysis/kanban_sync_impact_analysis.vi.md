# Epic: Đồng bộ Kanban Hai Chiều & Đánh giá Tác động Trước khi Sửa Code

## 1. Meta Data
- **Epic**: kanban-sync-impact-analysis
- **Status**: Done
- **Target Release**: v1.1.0
- **Platform**: Cross-Platform Tooling (Flutter, Android Native, iOS Native)
- **Source Spec**: [2026-09-15-epic-kanban-sync-and-impact-analysis-design.md](2026-09-15-epic-kanban-sync-and-impact-analysis-design.md)

---

## 2. Bối cảnh (Background)
Trong quy trình phát triển phần mềm di động quy mô lớn với nhiều agent và git worktrees trên **Flutter**, **Android Native**, và **iOS Native**:
1. **Lệch pha giữa các Workspace**: Khi thực thi trong worktree cô lập (`.worktrees/<epic_dir>`), file task ở workspace chính bị đóng băng ở `todo`. Bảng Kanban của kỹ sư mở trên IDE chính bị cũ. Các timestamp (`modified`, `completedAt`) không được duy trì tự động.
2. **Sửa code mù & Nguy cơ Hồi quy**: Kỹ sư hoặc AI Agent khi sửa mã nguồn thường gặp rủi ro rẽ nhánh xung đột với `<base_ref>` (như `develop`), làm vỡ các component phụ thuộc ở module khác, vi phạm hợp đồng ABI công khai, hoặc làm crash cầu nối Native (như `MethodChannel` giữa Flutter và Kotlin/Swift).
3. **Vùng tối thiếu Test Coverage**: Sửa logic ở các hàm có 0% coverage mà không có lưới an toàn, hoặc bỏ sót các nhánh rẽ biên (null, timeout, mất mạng, race condition) trong BDD/TDD.

---

## 3. Mục tiêu & Giới hạn (Goals & Non-Goals)

### Mục tiêu
- **Đồng bộ trạng thái Kanban 2 chiều theo thời gian thực**: Đồng bộ hóa mọi bước chuyển trạng thái (`backlog`, `todo`, `in-progress`, `review`, `done`) trên tất cả checkout qua `git worktree list --porcelain`, duy trì timestamp chuẩn ISO-8601 UTC Zulu (`created`, `modified`, `completedAt`).
- **Skill chuyên trách `impact-analysis` & Tool Pre-Edit Check**: Cung cấp pipeline kiểm tra 4 tầng tự động (`check_code_impact.py` kèm cẩm nang `references/impact-mechanisms.md`):
  1. *Tầng 1 (Git Conflicts)*: Phát hiện rẽ nhánh với `<base_ref>` và va chạm uncommitted ở các worktree khác.
  2. *Tầng 2 (Vùng ảnh hưởng Blast Radius)*: Quét tìm tất cả callers và kiểm tra ranh giới module bằng `ripgrep`.
  3. *Tầng 3 (Cầu nối Native Bridge)*: Quét xuyên biên giới tìm `MethodChannel` và `EventChannel` giữa Dart và Native.
  4. *Tầng 4 (Test Impact Analysis & Coverage)*: Ánh xạ test tương ứng, cảnh báo code chưa có test (0% coverage), và phát hiện case logic bị bỏ sót.
- **Tích hợp Quy trình & Cổng chất lượng**:
  - `epic-designer`: Bắt buộc mục `### Impact Analysis & Blast Radius` và mục tiêu coverage trong từng task và sơ đồ quy trình.
  - `epic-implementation`: Bắt buộc Bước 0 Pre-Edit check trước khi sửa code, cập nhật sơ đồ Phase 2, và lật trạng thái live qua script.
  - `quality_check`: Đo test coverage theo từng nền tảng và đối chiếu ngược với 4 Semantic Audits (Security 100%, Architecture $\ge 85\%$, UI, Code Health).
  - `epic-lifecycle`: Cập nhật các Gate 2, Gate 3, và Gate 4.
- **Dọn dẹp an toàn**: Tự động revert bản sao mirror ở workspace chính tại Phase 4 trước khi merge nhánh.

### Giới hạn (Non-Goals)
- Không thay thế compiler hay linter: `check_code_impact.py` đóng vai trò cảnh báo sớm; compiler và Tier C integration test vẫn là người gác cổng động cuối cùng.
- Giữ nguyên enum 5 cột Kanban: `backlog | todo | in-progress | review | done`.

---

## 4. Kiến trúc & Thiết kế Kỹ thuật

### Sơ đồ Kiến trúc Tổng quan (High-Level Architecture)
```mermaid
flowchart TD
    subgraph KANBAN_SYNC["Đồng bộ Kanban Hai Chiều (Dual-Workspace Sync)"]
        SYNC_TOOL["sync_task_status.py"]
        WT_DISCOVER["git worktree list --porcelain"]
        WT_DISCOVER --> SYNC_TOOL
        SYNC_TOOL -->|Ghi mirror| F_MAIN[".devtool/features/*.md (Main)"]
        SYNC_TOOL -->|Ghi mirror| E_MAIN[".devtool/epic/*/*.md (Main)"]
        SYNC_TOOL -->|Ghi mirror| F_WT[".devtool/features/*.md (Worktree)"]
        SYNC_TOOL -->|Ghi mirror| E_WT[".devtool/epic/*/*.md (Worktree)"]
    end

    subgraph IMPACT_ENGINE["Engine Skill @impact-analysis (check_code_impact.py)"]
        direction LR
        L1["Tầng 1: Xung đột Git & Worktree"] --> L2["Tầng 2: Vùng ảnh hưởng Callers (ripgrep)"] --> L3["Tầng 3: Cầu nối Cross-Platform Bridge"] --> L4["Tầng 4: Test Impact & Coverage (TIA)"]
        L4 --> REPORT["Báo cáo Unified Impact Report"]
    end

    subgraph WORKFLOW_INTEGRATION["Vòng đời Epic với CƠ CHẾ CHECK KÉP (DOUBLE-CHECK)"]
        STAGE2["1. CHECK 1: Khâu Thiết Kế (Shift-Left)<br/>Stage 2: epic-designer<br/>(Dự báo Blast Radius, Khóa Hợp đồng & DoD Coverage)"]
        STAGE3["2. TRUNG GIAN: Trước khi Sửa Code<br/>Stage 3: epic-implementation<br/>(Bước 0: Pre-Edit Check & Live Sync Kanban)"]
        STAGE4["3. CHECK 2: Khâu Nghiệm Thu (Shift-Right)<br/>Stage 4: quality_check (Gate 4)<br/>(Đối chiếu Diff thực tế, develop divergence & Ma trận Coverage)"]
        
        STAGE2 -->|Chuyển giao Spec & Tasks| STAGE3
        STAGE3 -->|Chuyển giao Code hoàn thành| STAGE4
    end

    %% Các đường liên kết Check Kép thể hiện rõ ràng
    REPORT ==>|"CHECK 1 (Shift-Left): Quét dự báo phạm vi & sinh Task"| STAGE2
    REPORT -.->|"Intermediate Check: Khóa an toàn trước khi gõ code"| STAGE3
    REPORT ==>|"CHECK 2 (Shift-Right): Nghiệm thu Diff thực tế so với base_ref"| STAGE4

    SYNC_TOOL -.->|"Lật trạng thái live 2 chiều"| STAGE3
```

### Sơ đồ Trường hợp Sử dụng (Use Cases Flowchart)
```mermaid
flowchart TB
    ACTOR["Kỹ sư Di động / AI Agent"]

    subgraph UC3["3. Use Case 3: Nghiệm thu Cuối Epic & Đối chiếu Coverage"]
        direction TB
        UC3_START["Hoàn thành tất cả các task"] --> UC3_RUN["Chạy @quality_check đo Coverage"]
        UC3_RUN --> UC3_REVERSE["Đối chiếu ngược Coverage với 4 Audits"]
        UC3_REVERSE --> UC3_GATE{"Test Pass & Đạt ngưỡng Coverage?"}
        UC3_GATE -->|Đạt| UC3_MERGE["Gate 4 🟢 LGTM: Dọn dẹp & Merge"]
        UC3_GATE -->|Chưa đạt| UC3_FAIL["Sửa lỗi / Bổ sung test"]
    end

    subgraph UC2["2. Use Case 2: Kiểm tra Tác động Trước khi Sửa Code"]
        direction TB
        UC2_START["Nhận task để thực hiện"] --> UC2_CHECK["Chạy check_code_impact.py"]
        UC2_CHECK --> UC2_VERIFY{"Có xung đột hoặc Rủi ro cao?"}
        UC2_VERIFY -->|Có| UC2_HALT["Dừng lại & cảnh báo kỹ sư"]
        UC2_VERIFY -->|Không| UC2_CONT["Tiến hành TDD Red-Green-Refactor"]
    end

    subgraph UC1["1. Use Case 1: Chuyển Trạng thái Task"]
        direction TB
        UC1_START["Kích hoạt chuyển trạng thái"] --> UC1_EXEC["Chạy sync_task_status.py task [id] [status]"]
        UC1_EXEC --> UC1_FANOUT["Ghi đồng thời vào Main & Worktree"]
        UC1_FANOUT --> UC1_TIME["Cập nhật timestamp modified & completedAt"]
    end

    ACTOR --> UC1_START
    ACTOR --> UC2_START
    ACTOR --> UC3_START
```

### Sơ đồ Trình tự Chính (Primary Sequence Diagram)
```mermaid
sequenceDiagram
    autonumber
    participant Agent as Lead Agent / Developer
    participant Sync as sync_task_status.py
    participant Impact as @impact-analysis (check_code_impact.py)
    participant Disk as Dual Workspace Disk
    participant TDD as Tri-Persona TDD Engine
    participant QC as @quality_check (Gate 4)

    Note over Agent, Disk: Phase 2: Thực thi Task tuần tự
    Agent->>Sync: task <task_id> in-progress
    Sync->>Disk: Đồng bộ status & modified sang toàn bộ worktrees
    Sync-->>Agent: Báo cáo đã ghi 4 bản sao + bảng thống kê board

    Agent->>Impact: --files <target_files> --base-ref develop
    Impact->>Disk: Kiểm tra git log base_ref...HEAD
    Impact->>Disk: Quét callers của symbol qua ripgrep
    Impact->>Disk: Quét chuỗi MethodChannel trên Dart/Kotlin/Swift
    Impact->>Disk: Ánh xạ file test & đo lường baseline coverage
    Impact-->>Agent: Unified Impact Report (🟢 An toàn để code)

    Agent->>TDD: Viết test & code theo BDD Scenarios (RED -> GREEN -> REFACTOR)
    TDD-->>Agent: Unit tests pass và đạt coverage mục tiêu

    Agent->>Sync: task <task_id> review
    Sync->>Disk: Đồng bộ trạng thái review
    Agent->>Sync: task <task_id> done
    Sync->>Disk: Đồng bộ trạng thái done & ghi completedAt

    Note over Agent, QC: Phase 4: Nghiệm thu cuối Epic
    Agent->>QC: Chạy quality check toàn diện & đo coverage
    QC->>Disk: Chạy testWithCoverage.sh / Jacoco / xccov
    QC->>QC: Đối chiếu ngược coverage với Security/Arch/UI/CodeHealth
    QC-->>Agent: 🟢 LGTM (Ma trận Coverage-Audit đạt chuẩn)
    Agent->>Disk: git restore bản sao mirror ở workspace chính
    Agent->>Disk: Merge nhánh epic vào develop
```

---

## 5. Cập nhật Quy trình & Sơ đồ theo từng Skill (Process Flow & Diagrams)

### 5.1 Cập nhật Quy trình `skills/epic-lifecycle/SKILL.md`
Quy trình điều phối vòng đời Epic được nâng cấp để áp dụng kiểm tra tác động tại Gate 2, xác nhận base-ref tại Gate 3, và đối chiếu Coverage ngược tại Gate 4:

```mermaid
flowchart TD
    S1["Stage 1 — Inception & Spec<br/>(brainstorming)"]
    G1{"Gate 1<br/>Spec được duyệt?"}
    ROUTE{"Quy mô Epic?"}
    PLANS(["writing-plans<br/>(rời khỏi workflow)"])
    S2["Stage 2 — Kiến trúc & Tasks<br/>(epic-designer)"]
    G2{"Gate 2<br/>HLD & Task Breakdown được duyệt?<br/><b>* Gồm Ma trận Tác động & DoD Coverage</b>"}
    S3["Stage 3 — Thực thi Cô lập<br/>(epic-implementation)"]
    G3{"Gate 3<br/>Xác nhận Thứ tự & Base Ref?<br/><b>* Xác minh không có xung đột Git</b>"}
    EXEC["Phase 2: Pre-Edit Impact Check + Task TDD<br/>Đồng bộ 2 chiều live, mỗi task 1 commit"]
    G4{"Gate 4<br/>quality_check 🟢 LGTM?<br/><b>* Đạt 3-Tier + 4 Audits + Ma trận Coverage</b>"}
    S4["Stage 4 — Đóng Nhánh<br/>(finishing-a-development-branch)"]

    S1 --> G1
    G1 -->|chưa, sửa lại| S1
    G1 -->|rồi| ROUTE
    ROUTE -->|không| PLANS
    ROUTE -->|có| S2
    S2 --> G2
    G2 -->|chưa, điều chỉnh| S2
    G2 -->|rồi| S3
    S3 --> G3
    G3 -->|chưa, chọn lại ref| G3
    G3 -->|rồi| EXEC
    EXEC --> G4
    G4 -->|chưa, sửa lỗi| EXEC
    G4 -->|rồi| S4
```

### 5.2 Cập nhật Quy trình Phase 2 trong `skills/epic-implementation/SKILL.md`
Vòng lặp Phase 2 được tích hợp Bước 0 (Kiểm tra tác động trước khi code) và lật trạng thái live:

```mermaid
flowchart TB
    T_START["Nhận task tiếp theo theo thứ tự"] --> SYNC_INP["1. sync_task_status.py task <id> in-progress<br/>(Ghi đồng thời 4 bản sao trên các checkout)"]
    SYNC_INP --> STEP0["2. Bước 0: Pre-Edit Impact & Conflict Check<br/>(@impact-analysis / check_code_impact.py)"]
    STEP0 --> CHK_RES{"Có rủi ro Git / Thiếu test?"}
    CHK_RES -->|🔴 Xung đột Git / Code chưa có test| HALT["Tạm dừng & Báo cáo Kỹ sư/Lead Agent"]
    CHK_RES -->|🟢 An toàn / Đã xác nhận| RED["3. RED: Viết test fail dựa trên BDD Scenarios"]
    RED --> GREEN["4. GREEN: Viết code tính năng tối thiểu"]
    GREEN --> REFACTOR["5. REFACTOR: Làm sạch code, đảm bảo ngưỡng coverage"]
    REFACTOR --> SYNC_REV["6. sync_task_status.py task <id> review"]
    SYNC_REV --> REVIEWS{"Review code đã thông qua?"}
    REVIEWS -->|Cần chỉnh sửa| STEP0
    REVIEWS -->|Đã duyệt| SYNC_DONE["7. sync_task_status.py task <id> done<br/>(Tự động ghi timestamp completedAt)"]
    SYNC_DONE --> COMMIT["8. Git Commit: [EPIC] Task title (Chỉ commit bản sao worktree)"]
    COMMIT --> NEXT_TASK{"Còn task trong danh sách?"}
    NEXT_TASK -->|Còn| T_START
    NEXT_TASK -->|Hết| PHASE4["Phase 4: @quality_check & Dọn dẹp Workspace chính"]
```

### 5.3 Cập nhật Quy trình Dual-Track trong `skills/quality_check/SKILL.md`
Sơ đồ điều phối `@quality_check` được bổ sung đường chạy đo lường test coverage và ma trận đối chiếu ngược:

```mermaid
flowchart TD
    START(["Kích hoạt: @quality_check"]) --> DETECT{"Nhận diện Nền tảng<br/>(Flutter / Android / iOS)"}

    subgraph TRACK1["Track 1: Bộ công cụ 3-Tier Nền tảng + Đo Coverage"]
        T1["Tier A: Package / Unit Tests"]
        T2["Tier B: Quy tắc Kiến trúc & Linters"]
        T3["Tier C: Acceptance & Integration Harness"]
        COV["Thu thập Dữ liệu Coverage<br/>(Flutter: lcov.info / Android: Jacoco/Kover / iOS: xccov)"]
        T1 --> T2 --> T3 --> COV
    end

    subgraph TRACK2["Track 2: 4 Semantic Audits Chuyên sâu chạy song song"]
        A_SEC["@security-audit (Fintech & OWASP)"]
        A_ARCH["@architecture-audit (Ranh giới Clean Arch)"]
        A_UI["@ui-audit (Hiệu năng UI & Vòng đời)"]
        A_CODE["@code-health-audit (Clean Code & Null-safety)"]
    end

    DETECT --> TRACK1
    DETECT --> TRACK2

    subgraph REVERSE_VERIFY["Đối chiếu ngược: Ma trận Coverage theo Danh mục Audit"]
        COV & A_SEC --> V_SEC["Kiểm tra Code Bảo mật: Bắt buộc 100% Coverage"]
        COV & A_ARCH --> V_ARCH["Kiểm tra Domain/Repositories: Bắt buộc >= 85% Coverage"]
        COV & A_UI --> V_UI["Kiểm tra State Hoisting & Giải phóng Tài nguyên"]
        COV & A_CODE --> V_CODE["Kiểm tra Độ phủ nhánh (Branch Coverage) ở hàm phức tạp"]
        V_SEC & V_ARCH & V_UI & V_CODE --> MATRIX["Ma trận Coverage-by-Audit Category"]
    end

    MATRIX --> REPORT["Báo cáo Unified Executive Quality Report"]
    REPORT --> VERDICT{"3 Tiers Xanh +<br/>4 Audits Xanh +<br/>Đạt chuẩn Coverage?"}
    VERDICT -->|Đạt| PASS["🟢 LGTM (Cho phép Merge)"]
    VERDICT -->|Không đạt| FAIL["🔴 Bị chặn (Cần khắc phục)"]
```

### 5.4 Cơ chế Check Kép (Bookend Verification: Kiểm tra ở Đầu Design & Kiểm tra ở Cuối Merge)

Để bảo đảm an toàn tuyệt đối và triệt tiêu toàn bộ điểm mù, `@impact-analysis` được áp dụng như một **Cơ chế Check Kép (Double-Check / Bookend Mechanism)** hoạt động tại cả hai đầu vòng đời phát triển:

```mermaid
flowchart LR
    subgraph CHECK1["CHECK 1: Khâu Thiết Kế (Shift-Left)"]
        D1["Brainstorming & epic-designer"]
        D1 -->|Kích hoạt impact-analysis| R1["Dự báo Blast Radius, Bản đồ Callers,<br/>Cảnh báo Native Bridge & Lưới Coverage"]
    end

    subgraph CHECK_MID["TRUNG GIAN: Trước khi Sửa Code"]
        M1["epic-implementation (Phase 2)"]
        M1 -->|Bước 0 Kiểm tra tức thì| R2["Xác nhận an toàn file trước khi code"]
    end

    subgraph CHECK2["CHECK 2: Khâu Nghiệm Thu Merge (Shift-Right)"]
        Q1["quality_check (Gate 4)"]
        Q1 -->|Kích hoạt impact-analysis trên git diff| R3["Xác minh Diff thực tế so với Spec,<br/>Kiểm tra lệch nhánh develop & Ma trận Coverage"]
    end

    CHECK1 --> CHECK_MID --> CHECK2
```

#### Tại sao cơ chế Check Kép lại mang lại hiệu quả vượt trội:
1. **Khép kín vòng lặp kiểm soát (Closed-Loop Feedback)**:
   - *Check 1 (Lúc Design/Planning)*: Lập giả thuyết vùng ảnh hưởng, định hướng phân rã task chính xác và phát hiện các case logic bị thiếu trước khi viết bất kỳ dòng code nào (sửa lỗi lúc này có chi phí rẻ nhất).
   - *Check 2 (Tại Gate 4 / Merge-Time)*: Soi chiếu trực tiếp trên `git diff` thực tế so với nhánh base. Phát hiện ngay các file bị sửa phát sinh ngoài kế hoạch (scope creep) hoặc các nhánh rẽ code bị thiếu test.
2. **Loại bỏ hoàn toàn rủi ro xung đột Git trong các Epic dài ngày**:
   - Khi làm Epic trong nhiều ngày, nhánh `develop` liên tục có commit mới từ các thành viên khác. Check 2 kiểm tra lại rẽ nhánh với commit mới nhất của `develop` ngay trước khi merge, bảo đảm không bị merge conflict.
3. **Tính minh bạch & Trách nhiệm giải trình**:
   - Khẳng định một cách định lượng rằng những gì đã cam kết và dự báo ở Check 1 đều được thực hiện trọn vẹn và an toàn ở Check 2.

---

## 6. Hợp đồng Hành vi BDD trong Thư mục Epic (`bdd_scenarios.md`)
Một file hợp đồng hành vi riêng được lưu trữ tại `bdd_scenarios.md` chuẩn hóa:
1. Tính đối xứng của việc chuyển trạng thái và tính toàn vẹn của timestamp.
2. Từ chối các trạng thái nằm ngoài enum 5 cột chuẩn.
3. Cảnh báo sớm xung đột Git và rẽ nhánh với `<base_ref>`.
4. Rà soát callers và bảo vệ ranh giới module.
5. Định danh cầu nối MethodChannel giữa Flutter và Native.
6. Cảnh báo vùng tối thiếu test (0% coverage) và case logic bị bỏ sót.
7. Dọn dẹp sạch sẽ workspace chính và bảo đảm an toàn khi merge.

---

## 7. Chiến lược Triển khai & Giảm thiểu Rủi ro (Rollout Strategy)
- **Triển khai theo giai đoạn**:
  - Giai đoạn 1: Triển khai `sync_task_status.py` và `test_sync_task_status.py` ổn định việc đồng bộ Kanban.
  - Giai đoạn 2: Triển khai `check_code_impact.py` và `test_check_code_impact.py` tự động hóa việc kiểm tra tác động.
  - Giai đoạn 3: Phát hành `skills/impact-analysis/` và tài liệu hướng dẫn.
  - Giai đoạn 4: Tích hợp quy trình trên `epic-designer`, `epic-implementation`, `quality_check`, và `epic-lifecycle`.
- **Dự phòng & Khắc phục**:
  - `sync_task_status.py` giữ nguyên nội dung văn bản nếu gặp định dạng lạ, không bao giờ tự ý sửa sai cấu trúc file HLD.
  - `check_code_impact.py` là công cụ đọc tĩnh, không làm thay đổi file mã nguồn. Nếu repo chưa có file báo cáo coverage, nó tự động hạ cấp xuống kiểm tra file test tĩnh mà không làm gián đoạn luồng làm việc.
  - Lệnh restore ở Phase 4 không dùng `--staged`, giữ an toàn các thay đổi dev đã stage thủ công.

---

## 8. Phân rã Tasks Kanban (Kanban Tasks Breakdown)
- [Task 1: Hoàn thiện và tích hợp công cụ Đồng bộ Trạng thái Kanban](task_1_kanban_sync_status.md)
- [Task 2: Xây dựng công cụ Kiểm tra Tác động và Xung đột trước khi sửa code](task_2_pre_edit_impact_checker.md)
- [Task 3: Soạn thảo Skill chuyên trách Impact Analysis và Tài liệu Hướng dẫn](task_3_impact_analysis_skill.md)
- [Task 4: Tích hợp Cổng Quy trình vào Epic Designer và Epic Implementation](task_4_workflow_integration.md)
- [Task 5: Tích hợp Đo lường Coverage và Cổng Đối chiếu Ngược vào Quality Check](task_5_quality_check_coverage_gate.md)
