# KIẾN TRÚC MẠNG LƯỚI MICRO-SKILLS CHO AI AGENTS
## Dựa trên cuốn sách "The Lean Product Playbook" - Dan Olsen

---

## 1. TỔNG QUAN KIẾN TRÚC (ARCHITECTURE OVERVIEW)

Để xây dựng một hệ thống AI Agents phát triển sản phẩm tinh gọn mà **không bị ngợp context (context limit) hoặc nảy sinh sinh hoang tưởng (hallucinations)**, quy trình trong *The Lean Product Playbook* được chia nhỏ thành **5 Micro-Skills chuyên biệt** và **1 Skill Điều phối tổng thể (Orchestrator)**.

```
                    ┌─────────────────────────────────────────┐
                    │      lean-product-orchestrator          │
                    │      (Điều phối & Chuyển giao)          │
                    └────────────────────┬────────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    │                                    │                                    │
    ▼                                    ▼                                    ▼
[Skill 1]                            [Skill 2]                            [Skill 3]
lean-market-discovery                lean-value-strategy                  lean-mvp-scoping
(Problem Space & Needs)              (Kano & Value Prop)                  (User Stories & ROI)
    │                                    │                                    │
    └────────────────────────────────────┼────────────────────────────────────┘
                                         │
                                         ▼
                                     [Skill 4]
                                 lean-ux-testing
                             (Prototypes & PMF Loops)
                                         │
                                         ▼
                                     [Skill 5]
                            lean-analytics-optimization
                              (Retention & AARRR)
```

---

## 2. CHI TIẾT CÁC MICRO-SKILLS

### 🤖 SKILL DIỀU PHỐI TỔNG THỂ: `lean-product-orchestrator`
* **Mục tiêu**: Làm vai trò "Trưởng ban cố vấn" điều hướng người dùng qua đúng các giai đoạn của Kim tự tháp PMF.
* **Quy tắc điều phối**:
  1. Luôn bắt đầu từ Tầng đáy (Market) -> Tầng đỉnh (Product).
  2. Kiểm tra điều kiện bàn giao (Hand-off Gates) trước khi chuyển đổi Skill.
  3. Duy trì hồ sơ sản phẩm chung (`product-spec.md`) để truyền ngữ cảnh giữa các Skills.

---

### 🎯 SKILL 1: `lean-market-discovery`
* **Tên kỹ năng**: Customer Discovery & Problem Space Explorer
* **Phạm vi sách**: Chương 3 (Target Customer) & Chương 4 (Underserved Needs).
* **Nhiệm vụ chính**: Làm rõ ai là khách hàng mục tiêu và vấn đề thực sự của họ trong Problem Space.
* **Core Rules & Constraints**:
  * **Cấm giải pháp**: Từ chối mọi thảo luận về tính năng, công nghệ hoặc giao diện ở giai đoạn này.
  * **Chỉ tập trung vào Nhu cầu (Needs)**: Chuyển đổi mọi ý tưởng tính năng thành "Nhu cầu cốt lõi" (Problem Statement).
* **Workflows & Tools**:
  * **Phân đoạn dựa trên Nhu cầu (Needs-based Segmentation)**.
  * **Tạo Needs-based Personas**: Định nghĩa rõ *Goals*, *Pains*, *Triggers*, và *Current Workarounds*.
  * **Khung Importance vs. Satisfaction**: Thu thập dữ liệu đánh giá độ quan trọng và mức độ hài lòng.
  * **Tính điểm cơ hội (Opportunity Score)**:
    $$\text{Opportunity Score} = \text{Importance} \times (1 - \text{Satisfaction})$$
* **Sản phẩm bàn giao (Hand-off Gate 1)**: `problem-space-spec.md` (Gồm danh sách Personas và Top 3-5 Opportunity Gaps có điểm số cao nhất).

---

### ⚖️ SKILL 2: `lean-value-strategy`
* **Tên kỹ năng**: Competitive Positioning & Kano Model Strategist
* **Phạm vi sách**: Chương 5 (Define Value Proposition).
* **Nhiệm vụ chính**: Định vị sản phẩm khác biệt với đối thủ cạnh tranh trên thị trường.
* **Core Rules & Constraints**:
  * **Bắt buộc chọn điểm chiến thắng**: Không được cố gắng giỏi hơn đối thủ ở mọi điểm. Bắt buộc phải chọn tối đa 1-2 tính năng làm *Delighters* hoặc *Performance Leaders*.
  * **Quy tắc Must-haves**: Phải đáp ứng chuẩn mực tối thiểu của ngành nhưng không tốn quá nhiều tài nguyên vào đó.
* **Workflows & Tools**:
  * **Phân loại nhu cầu theo Mô hình Kano**:
    1. *Must-haves* (Bắt buộc phải có - không tạo sự hài lòng nhưng thiếu sẽ thất bại).
    2. *Performance Benefits* (Càng nhiều càng tốt - so sánh trực tiếp với đối thủ).
    3. *Delighters* (Gây bất ngờ, thích thú - tạo sự khác biệt đột phá).
  * **Lập lưới Định vị Giá trị (Value Proposition Grid)**: So sánh sản phẩm dự kiến với Top 2-3 đối thủ hiện tại.
* **Sản phẩm bàn giao (Hand-off Gate 2)**: `value-proposition-spec.md` (Bảng phân loại Kano và tuyên ngôn giá trị độc nhất).

---

### 📦 SKILL 3: `lean-mvp-scoping`
* **Tên kỹ năng**: MVP Feature Scoper & ROI Prioritizer
* **Phạm vi sách**: Chương 6 (Specify MVP Feature Set).
* **Nhiệm vụ chính**: Cắt gọt tính năng để xây dựng phiên bản MVP tối thiểu nhưng vẫn đem lại giá trị tối đa.
* **Core Rules & Constraints**:
  * **Quy tắc Chunking**: Chia nhỏ các epic thành các User Stories nhỏ nhất có thể kiểm thử độc lập.
  * **Quy tắc ROI 3x3**: Chỉ đưa vào MVP v1 các tính năng thuộc ô High Value / Low Effort hoặc High Value / Medium Effort.
* **Workflows & Tools**:
  * **Chuẩn hóa User Stories**: `As a [Persona], I want to [Action], so that [Benefit]`.
  * **Ma trận Ưu tiên ROI 3x3 (Value vs. Effort)**.
  * **Xác định MVP Candidate v1**: Đảm bảo cấu trúc MVP có đủ 3 tầng Kano (Must-have đủ xài + Performance vượt trội + 1 Delighter nhỏ).
* **Sản phẩm bàn giao (Hand-off Gate 3)**: `mvp-feature-backlog.md` (Danh sách User Stories cho MVP v1 được xếp thứ tự ưu tiên).

---

### 🧪 SKILL 4: `lean-ux-testing`
* **Tên kỹ năng**: UX Prototype & PMF Testing Specialist
* **Phạm vi sách**: Chương 7 (Create MVP Prototype) & Chương 8-10 (Test MVP & Iterate).
* **Nhiệm vụ chính**: Biến danh sách tính năng thành Prototype và kiểm thử trực tiếp với người dùng.
* **Core Rules & Constraints**:
  * **Ruy-băng vừa đủ (Minimum Fidelity)**: Chọn dạng prototype có chi phí thấp nhất nhưng đủ để kiểm chứng giả thuyết.
  * **Thiết kế kiểm thử không dẫn dắt (Unbiased Testing)**: Kịch bản phỏng vấn không được đặt câu hỏi gợi ý hay "bán" sản phẩm.
* **Workflows & Tools**:
  * **Lựa chọn loại Prototype**: *Landing Page/Smoke Test*, *Wizard of Oz*, *Clickable Wireframe*, hoặc *Concierge MVP*.
  * **Soạn bộ lọc Khách hàng (Screener Grid)**.
  * **Kịch bản phỏng vấn kiểm thử (Usability & Value Testing Script)**.
  * **Vòng lặp Hypothesize - Design - Test - Learn**: Đánh giá kết quả thu được để quyết định *Persevere* (Tiếp tục) hay *Pivot* (Xoay hướng).
* **Sản phẩm bàn giao (Hand-off Gate 4)**: `test-results-and-pivot-report.md` (Báo cáo kết quả kiểm thử và định hướng điều chỉnh).

---

### 📈 SKILL 5: `lean-analytics-optimization`
* **Tên kỹ năng**: Retention & Product Analytics Optimizer
* **Phạm vi sách**: Chương 12-14 (Measure & Optimize).
* **Nhiệm vụ chính**: Đo lường sự tăng trưởng và tối ưu hóa sản phẩm dựa trên dữ liệu sau khi ra mắt.
* **Core Rules & Constraints**:
  * **Retention là Vua**: Không tập trung vào van vanities (số người đăng ký, lượt tải) khi đường cong Retention chưa đi ngang.
  * **Chỉ tập trung vào MTMM**: Chỉ chọn 1 chỉ số quan trọng nhất làm *Metric That Matters Most* tại mỗi thời điểm.
* **Workflows & Tools**:
  * **Khảo sát PMF Sean Ellis**: Đo lường tỷ lệ người dùng nói "Rất thất vọng" nếu sản phẩm biến mất (Mục tiêu $\ge 40\%$).
  * **Phân tích Retention Cohort**: Theo dõi đường cong Retention Curve.
  * **Phễu AARRR (Pirate Metrics)**: Acquisition -> Activation -> Retention -> Referral -> Revenue.
  * **Phương trình Kinh doanh (Equation of Your Business)**:
    $$\text{Revenue} = \text{Traffic} \times \text{Conversion Rate} \times \text{LTV}$$
* **Sản phẩm bàn giao (Hand-off Gate 5)**: `growth-and-retention-dashboard.md` (Định nghĩa MTMM, phễu chuyển đổi và kế hoạch tối ưu hóa).

---

## 3. QUY TRÌNH KẾT NỐI & NẠP SKILLS VÀO AI AGENTS

### Cách thiết lập cấu trúc File trong dự án AI Agent:
```text
/skills/
├── 00-orchestrator.md
├── 01-market-discovery.md
├── 02-value-strategy.md
├── 03-mvp-scoping.md
├── 04-ux-testing.md
└── 05-analytics-optimization.md
```

### Nguyên tắc vận hành:
1. Khi người dùng nảy ra ý tưởng mới: Nạp `00-orchestrator.md` + `01-market-discovery.md`.
2. Khi hoàn thành giai đoạn kiểm chứng vấn đề: Nạp tiếp `02-value-strategy.md` và `03-mvp-scoping.md`.
3. Việc chia nhỏ này giúp AI Agent giữ **context window sạch 100%**, chỉ tập trung vào các quy tắc chuyên biệt của từng giai đoạn, triệt tiêu hoàn toàn rủi ro bị nhầm lẫn giữa Problem Space và Solution Space.
