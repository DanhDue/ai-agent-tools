# Epic: Bộ Kỹ Năng Vòng Đời Khám Phá Sản Phẩm Tinh Gọn (Lean Product Lifecycle Suite)

## 1. Meta Data
- **Epic**: `lean_product_suite`
- **Status**: In-Progress
- **Target Release**: `1.1.0`
- **Platform**: `Agent Tools (Markdown, YAML, Shell)`
- **Source Spec**: [2026-09-16-lean-product-lifecycle-suite-design.md](2026-09-16-lean-product-lifecycle-suite-design.md)
- **BDD Scenarios**: [bdd_scenarios.md](bdd_scenarios.md)
- **Rà Soát Độ Trung Thực Nguồn**: [source_fidelity_review.md](source_fidelity_review.md)
- **Nguồn Gốc**: *The Lean Product Playbook*, Dan Olsen (Wiley, 2015)
- **Created**: 2026-09-16
- **Author**: Antigravity AI Pair & DanhDue ExOICTIF

---

## 2. Bối Cảnh (Background)
Phát triển phần mềm ở giai đoạn sớm thường xuyên rơi vào **"Cái bẫy Xây dựng" (Build Trap)**: các lập trình viên và nhà sáng lập vội vã lao vào Solution Space (Không gian Giải pháp) — viết mã nguồn, thiết kế cơ sở dữ liệu, dựng giao diện UI — mà chưa kiểm chứng xem nhu cầu người dùng có thực sự tồn tại hay có đang bị bỏ quên (Underserved) hay không. Các mô hình LLM thông thường càng làm trầm trọng hóa vấn đề này khi vội vàng đề xuất danh sách tính năng cồng kềnh, kiến trúc phức tạp và các giao diện nông cạn.

Dựa trên tác phẩm kinh điển *The Lean Product Playbook* của Dan Olsen, Epic này thiết lập **Vòng đời Thượng nguồn Khám phá & Xác thực Sản phẩm Tinh gọn (Upstream Product Discovery & Validation Lifecycle)** dưới dạng một bộ AI Agent Skills chuẩn hóa. Bộ kỹ năng đảm bảo sự tách biệt kỷ luật giữa Problem Space và Solution Space, thực thi 5 rào chắn chống ảo giác (Anti-hallucination guardrails), hóa thân thành các chuyên gia sản phẩm huyền thoại, và xuất ra các tài liệu đặc tả có cấu trúc thông qua các cổng phê duyệt (Gates) trước khi kỹ thuật bắt đầu.

---

## 3. Mục Tiêu & Giới Hạn (Goals & Non-Goals)

### Mục Tiêu (Goals)
1. **Master Orchestrator Skill (`lean-product-lifecycle`)**:
   - Persona: **Dan Olsen** (CPO / Lean Product Co-Founder).
   - Mang hai mô hình tách bạch: **Kim tự tháp PMF 5 tầng** (Target Customer → Underserved Needs →
     Value Proposition | Feature Set → UX) dùng để chẩn đoán và lùi tầng, và **Quy trình Lean Product
     6 bước** dùng để điều tuyến. Việc gộp hai mô hình này chính là sai sót trung tâm của bản phân
     tích trước.
   - Thực thi 5 Rào chắn Chống Ảo giác cứng.
   - Triển khai Giao thức phục hồi Mảng Kiến tạo (Tectonic Plates Fallback Protocol) khi Gate thất bại.
2. **Stage 1 Micro-Skill (`lean-market-discovery`)**:
   - Persona: **Steve Blank & Anthony Ulwick**.
   - Trọng tâm: Personas theo nhu cầu, Benefit Laddering (5 Whys), thiết kế khảo sát Importance/
     Satisfaction (thang 5 điểm đơn cực / 7 điểm lưỡng cực kèm bước chuẩn hóa), và tính song song hai
     công thức điểm cơ hội — Gate 1 đòi hỏi ít nhất một nhu cầu đạt $OS > 15$ trên thang Ulwick 0–20.
   - Sản phẩm bàn giao: `.devtool/product/<slug>/01_problem_space_spec.md`.
3. **Stage 2 Micro-Skill (`lean-value-strategy`)**:
   - Persona: **GS. Noriaki Kano & Michael Porter**.
   - Trọng tâm: Phân loại Kano (Must-haves, Performance, Delighters), bảng so sánh đối thủ có tính cả
     giải pháp thay thế hiện tại của khách hàng, chọn **đúng một** Performance Benefit để chiến thắng
     (các tiêu chí còn lại chỉ cần ngang bằng), Differentiator cốt lõi, và Non-Goals.
   - Sản phẩm bàn giao: `.devtool/product/<slug>/02_value_proposition_spec.md`.
4. **Stage 3 Micro-Skill (`lean-mvp-scoping`)**:
   - Persona: **Eric Ries & Jeff Patton**.
   - Trọng tâm: User story mapping, chia nhỏ tính năng (Feature Chunking), ưu tiên bằng ROI định lượng
     (lưới 3x3 chỉ là phương án dự phòng được tuyên bố rõ), **Lưới Ứng Viên MVP** (Lợi ích × Feature
     Chunk), và kiểm tra tính trọn vẹn theo Kim tự tháp Thuộc tính MVP (Functional, Reliable, Usable,
     Delightful).
   - Sản phẩm bàn giao: `.devtool/product/<slug>/03_mvp_feature_backlog.md`.
5. **Cầu Nối Kỹ Thuật sang `d3nexus:epic-designer`**:
   - Chuyển giao trực tiếp file `03_mvp_feature_backlog.md` đã được duyệt cho `epic-designer` để dựng HLD, sơ đồ C4 và các task Kanban lập trình.
6. **Tài Liệu Tham Khảo & Templates Tự Quản**:
   - Trang bị cho mỗi skill thư mục `references/` (công thức toán, kịch bản phỏng vấn, hướng dẫn kano, quy tắc roi) và `templates/` (khung đặc tả hợp đồng).

### Giới Hạn (Non-Goals)
- Các kỹ năng Giai đoạn 2 (`lean-ux-testing` và `lean-analytics-optimization`) nằm ngoài phạm vi của epic này và được dời sang bản phát hành 1.2.0.
- Không sử dụng phụ thuộc runtime của bên thứ ba (mọi skill đều tuân theo chuẩn markdown/YAML frontmatter của Agent Skill).

---

## 4. Kiến Trúc & Thiết Kế Kỹ Thuật

### 4.1 Kiến Trúc Tổng Thể (High-Level Architecture)
```mermaid
graph TD
    subgraph ORCHESTRATOR["Nhạc Trưởng Điều Phối: lean-product-lifecycle"]
        DAN["Persona: Dan Olsen<br/>(CPO &amp; Lean Co-Founder)"]
        GUARD["5 Rào Chắn Chống Ảo Giác"]
        ROUTER["Bộ Điều Tuyến Kim Tự Tháp PMF &amp; Quản Lý Trạng Thái"]
    end

    subgraph STAGE1["Stage 1: lean-market-discovery"]
        STEVE["Persona: Steve Blank &amp; Anthony Ulwick"]
        DISC["Customer Benefit Laddering &amp; Tính Điểm Cơ Hội"]
        ART1[("01_problem_space_spec.md")]
    end

    subgraph STAGE2["Stage 2: lean-value-strategy"]
        KANO["Persona: Noriaki Kano &amp; Michael Porter"]
        GRID["Phân Loại Kano &amp; Ma Trận Cạnh Tranh"]
        ART2[("02_value_proposition_spec.md")]
    end

    subgraph STAGE3["Stage 3: lean-mvp-scoping"]
        RIES["Persona: Eric Ries &amp; Jeff Patton"]
        ROI["Chia Nhỏ Tính Năng &amp; Ưu Tiên Theo ROI"]
        ART3[("03_mvp_feature_backlog.md")]
    end

    subgraph DOWNSTREAM["Hạ Tầng Kỹ Thuật (d3nexus)"]
        EPIC_DES["d3nexus:epic-designer"]
        EPIC_IMP["d3nexus:epic-implementation"]
    end

    DAN --> ROUTER
    GUARD --> ROUTER
    ROUTER -->|Kích hoạt Stage 1| STEVE
    STEVE --> DISC --> ART1
    ART1 -->|Gate 1 Đạt| KANO
    KANO --> GRID --> ART2
    ART2 -->|Gate 2 Đạt| RIES
    RIES --> ROI --> ART3
    ART3 -->|Gate 3 Bàn Giao| EPIC_DES
    EPIC_DES --> EPIC_IMP
```

### 4.2 Trường Hợp Sử Dụng (Use Cases)
```mermaid
flowchart TD
    FOUNDER(["Founder / Giám Đốc Sản Phẩm"])
    UC1["UC1: Khám phá trọn vẹn (Từ Ý Tưởng đến MVP Backlog)"]
    UC2["UC2: Khám phá Thị trường Độc lập (Chỉ Problem Space)"]
    UC3["UC3: Định vị Giá trị &amp; Phân tích Kano Độc lập"]
    UC4["UC4: Chia nhỏ Tính năng &amp; Lượng hóa ROI Độc lập"]
    UC5["UC5: Bàn giao Liền mạch cho Kỹ Sư Thiết Kế Epic"]

    FOUNDER --> UC1
    FOUNDER --> UC2
    FOUNDER --> UC3
    FOUNDER --> UC4
    FOUNDER --> UC5

    UC1 --> ORCH["lean-product-lifecycle"]
    UC2 --> S1["lean-market-discovery"]
    UC3 --> S2["lean-value-strategy"]
    UC4 --> S3["lean-mvp-scoping"]
    UC5 --> BRIDGE["epic-designer"]
```

### 4.3 Sơ Đồ Tuần Tự (Sequence Diagram)
```mermaid
sequenceDiagram
    autonumber
    actor F as Founder
    participant O as lean-product-lifecycle (Dan Olsen)
    participant S1 as lean-market-discovery (Steve Blank)
    participant S2 as lean-value-strategy (Noriaki Kano)
    participant S3 as lean-mvp-scoping (Eric Ries)
    participant ED as epic-designer

    F->>O: Kích hoạt với Ý tưởng Sản phẩm
    O->>O: Áp Rào chắn 1 (Ghi nhận & quy đổi ý tưởng giải pháp về nhu cầu)
    O->>S1: Ủy quyền Stage 1
    S1->>F: Thực hiện Phỏng vấn Benefit Laddering & Chấm điểm Cơ hội
    S1->>S1: Tạo file 01_problem_space_spec.md
    S1-->>F: Yêu cầu Phê duyệt Gate 1
    F->>O: Gate 1 Được duyệt
    O->>S2: Ủy quyền Stage 2 kèm 01_problem_space_spec.md
    S2->>F: Phân tích Đối thủ & Phân loại Lợi ích Kano
    S2->>S2: Tạo file 02_value_proposition_spec.md
    S2-->>F: Yêu cầu Phê duyệt Gate 2
    F->>O: Gate 2 Được duyệt
    O->>S3: Ủy quyền Stage 3 kèm 02_value_proposition_spec.md
    S3->>F: Chia nhỏ Feature Chunks & Dựng Lưới Ứng Viên MVP
    S3->>S3: Tạo file 03_mvp_feature_backlog.md
    S3-->>F: Yêu cầu Phê duyệt Gate 3
    F->>O: Gate 3 Được duyệt
    O->>ED: Bàn giao 03_mvp_feature_backlog.md để bắt đầu dựng HLD Kỹ thuật
```

### 4.4 Kiểm Soát Độ Trung Thực Nguồn
Mọi luận điểm phương pháp luận mà bộ kỹ năng này hiện thực hóa đều được truy vết trực tiếp về cuốn *The
Lean Product Playbook*, không phải về các bản tóm tắt trong `docs/books/`. Các bản tóm tắt đó là tài liệu
phái sinh và chứa 6 sai sót làm thay đổi hành vi, được liệt kê kèm nguyên văn của tác giả tại
[source_fidelity_review.md](source_fidelity_review.md). Task 0 sửa chúng tại gốc để sai sót không thể tái
lan truyền vào các bản chỉnh sửa kỹ năng sau này.

### 4.5 Phân Tích Tác Động Tả Ngạn (Shift-Left Impact Analysis)
- **Vùng ảnh hưởng (Blast Radius)**: Không ảnh hưởng đến mã nguồn ứng dụng di động (`digital_wallet`). Các kỹ năng mới nằm gọn trong thư mục `skills/` và được đồng bộ tới `.gemini/config/plugins/d3nexus/skills/`.
- **Khả năng tương thích**: Tuân thủ 100% chuẩn `agentskills.io` và phối hợp nhịp nhàng với orchestrator `epic-lifecycle`.

### 4.6 Kịch Bản BDD Tham Chiếu
Toàn bộ kịch bản Gherkin chi tiết trải rộng trên 5 chiều kiểm thử được lưu trữ tại [bdd_scenarios.md](bdd_scenarios.md).

---

## 5. Chiến Lược Triển Khai & Kiểm Thử
- **Triển khai từng phần**: Xây dựng các kỹ năng lõi, biểu mẫu (templates) và tài liệu tham khảo trong `skills/`.
- **Kiểm chứng**: Chạy 3 kịch bản thử thách TDD (Pressure tests) đã được định nghĩa trong Design Spec.
- **Đồng bộ**: Đồng bộ vào `~/.gemini/config/plugins/d3nexus/skills/` để mọi agent trong IDE đều kích hoạt được.

---

## 6. Phân Rã Các Công Việc Kanban (Kanban Tasks Breakdown)

Quá trình hiện thực hóa Epic này được phân rã thành 6 nhiệm vụ nguyên tử:

- [Task 0: Sửa Các Tài Liệu Phái Sinh trong `docs/books/`](task_0_book_reference_corrections.md)
- [Task 1: Master Orchestrator (`lean-product-lifecycle`) & Rào Chắn Guardrails](task_1_lean_product_lifecycle_orchestrator.md)
- [Task 2: Stage 1 (`lean-market-discovery`), Chấm Điểm Cơ Hội & Gate 1](task_2_lean_market_discovery_skill.md)
- [Task 3: Stage 2 (`lean-value-strategy`), Mô Hình Kano & Gate 2](task_3_lean_value_strategy_skill.md)
- [Task 4: Stage 3 (`lean-mvp-scoping`), Ưu Tiên ROI & Gate 3](task_4_lean_mvp_scoping_skill.md)
- [Task 5: Tích Hợp Toàn Diện Bộ Suite, Đồng Bộ Plugin & Kiểm Thử TDD](task_5_suite_integration_and_verification.md)
