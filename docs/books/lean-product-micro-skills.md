# KIẾN TRÚC MẠNG LƯỚI MICRO-SKILLS CHO AI AGENTS
## Dựa trên cuốn sách "The Lean Product Playbook" - Dan Olsen

> [!IMPORTANT]
> **Tài liệu phái sinh (Derivative).** Đây là bản tóm tắt soạn từ cuốn sách, **không phải nguồn gốc**.
> Nơi nào mâu thuẫn với cuốn sách, **cuốn sách thắng**. Đã đối chiếu và sửa ngày 2026-09-16; bằng chứng
> tại [source_fidelity_review.md](../../.devtool/epic/lean_product_suite/source_fidelity_review.md).

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
  * **Khung Importance vs. Satisfaction** — thiết kế thang đo trước, tính sau:
    * **Importance**: thang **đơn cực (unipolar) 5 điểm** (Không quan trọng → Cực kỳ quan trọng).
    * **Satisfaction**: thang **lưỡng cực (bipolar) 7 điểm** (Hoàn toàn không hài lòng → Hoàn toàn hài lòng).
    * *Vì sao khác nhau*: Satisfaction có cực âm, Importance thì không. Thang lưỡng cực dùng số điểm lẻ
      để có mốc trung tính. Quá 11 lựa chọn gây quá tải; dưới 5 lựa chọn mất độ phân giải.
    * **Chuẩn hóa bắt buộc**: 5 điểm → 0 / 25 / 50 / 75 / 100 (hoặc 0 / 2.5 / 5 / 7.5 / 10);
      7 điểm → 0 / 16.7 / 33.3 / 50 / 66.7 / 83.3 / 100.
  * **Tính điểm cơ hội — chạy cả hai công thức, mỗi công thức trên đúng thang của nó**:
    * *Olsen* (đầu vào 0–1, kết quả 0–1), so sánh tương đối:
      $$\text{Opportunity to Add Value} = \text{Importance} \times (1 - \text{Satisfaction})$$
    * *Ulwick* (đầu vào 0–10, kết quả 0–20), có ngưỡng tuyệt đối:
      $$\text{Opportunity Score} = \text{Importance} + \max(\text{Importance} - \text{Satisfaction}, 0)$$
      **`> 15` rất hấp dẫn · `10–15` ở mức biên · `< 10` không hấp dẫn.**
    * ⛔ *Không bao giờ đối chiếu con số của công thức này với ngưỡng của công thức kia.*
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
  * **Lập lưới Định vị Giá trị (Value Proposition Grid)**: So sánh sản phẩm dự kiến với 2-3 đối thủ hiện tại.
    * *"Đối thủ" không chỉ là đối thủ trực tiếp*: nếu không có đối thủ trực tiếp, cột đối thủ phải là
      **giải pháp thay thế khách hàng đang dùng hôm nay** (giấy bút từng là đối thủ của TurboTax).
      Không bao giờ chấp nhận tập đối thủ rỗng.
    * *Quy ước chấm điểm*: Must-haves chấm Yes/No; Performance Benefits chấm High/Medium/Low hoặc số
      liệu cụ thể; mỗi Delighter một hàng, đánh dấu Yes ở nơi có. Differentiator in **đậm**.
  * **Quy tắc thắng-một / giữ-ngang-bằng**: chọn **đúng một** Performance Benefit để thắng; các tiêu chí
    còn lại chỉ cần **ngang bằng**, không cần vượt trội. Được phép — và nên — chấm mình **Low** ở tiêu
    chí không cạnh tranh. Chấm High ở mọi tiêu chí là né tránh chiến lược và phải bị từ chối.
    * *Ca Google*: các search engine đầu tiên cạnh tranh ở số lượng, độ tươi và độ liên quan của kết quả.
      Khi số lượng và độ tươi bão hòa, độ liên quan thành tiêu chí quan trọng nhất — Google thắng vì giỏi
      nhất ở đúng tiêu chí đó **trong khi vẫn ngang bằng hoặc tốt hơn ở các chiều còn lại**.
* **Sản phẩm bàn giao (Hand-off Gate 2)**: `value-proposition-spec.md` (Bảng phân loại Kano và tuyên ngôn giá trị độc nhất).

---

### 📦 SKILL 3: `lean-mvp-scoping`
* **Tên kỹ năng**: MVP Feature Scoper & ROI Prioritizer
* **Phạm vi sách**: Chương 6 (Specify MVP Feature Set).
* **Nhiệm vụ chính**: Cắt gọt tính năng để xây dựng phiên bản MVP tối thiểu nhưng vẫn đem lại giá trị tối đa.
* **Core Rules & Constraints**:
  * **Quy tắc Chunking**: Chia nhỏ các epic thành các User Stories nhỏ nhất có thể kiểm thử độc lập.
  * **Quy tắc ROI**: Ưu tiên bằng **ROI định lượng** (`Customer Value / Developer-Weeks`) trước; lưới 3x3
    High/Med/Low chỉ là **phương án dự phòng** Olsen gọi là "kém chặt chẽ hơn", dùng khi không ước lượng
    được bằng số. Hai chunk cùng ROI thì ưu tiên chunk **nhỏ hơn**.
  * **Quy tắc cấu thành MVP (thay cho mọi ngưỡng cắt thứ hạng)**: v1 gồm (1) **toàn bộ** Must-Haves — bắt
    buộc, **bất kể thứ hạng ROI**; (2) đủ chunk của **đúng một** Performance Benefit được chọn để thắng;
    (3) **Delighter hàng đầu**, chỉ bỏ được khi lợi thế Performance đủ lớn để tự đứng vững.
    * ⛔ *Olsen nói rõ có lúc phải **nhảy xuống** khỏi thứ tự xếp hạng để MVP được hoàn chỉnh. Một
      Must-Have tốn công vẫn phải nằm trong v1 — ROI xếp thứ tự công việc, không quyết định tư cách
      thành viên của MVP. Nếu quá tốn công thì chia nhỏ nó ra, đừng cắt nó đi.*
* **Workflows & Tools**:
  * **Chuẩn hóa User Stories**: `As a [Persona], I want to [Action], so that [Benefit]`.
  * **Ma trận Ưu tiên ROI 3x3 (Value vs. Effort)**.
  * **Lưới Ứng Viên MVP (Hình 6.3/6.4)**: mỗi hàng là một lợi ích (`M1`, `M2`, `P1`…, `D1`…), các chunk của
    lợi ích đó xếp theo thứ tự ưu tiên từ trái sang; **cột trái nhất là v1**, các chunk bị đẩy sang phải
    thành v1.1, v1.2. Không lập kế hoạch quá **một đến hai** phiên bản phụ.
  * **Kiểm tra tính trọn vẹn** theo **Kim tự tháp Thuộc tính MVP** — Functional, Reliable, Usable,
    Delightful (Hình 7.1, Olsen phỏng theo **Jussi Pasanen**; ẩn dụ "cupcake" là của Brandon Schauer,
    **không có trong sách này**).
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
  * **Quy mô mỗi làn sóng: 5 đến 8 khách hàng.** (Con số "5 người phát hiện 85% lỗi UX" là của Jakob
    Nielsen, không phải của Olsen.)
  * **Chấm điểm bán định lượng khi kết thúc mỗi buổi test**: thang 0–10 cho *mức độ giá trị*, *khả năng
    sẽ dùng*, *mức độ dễ dùng*; theo dõi xu hướng qua từng làn sóng.
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
