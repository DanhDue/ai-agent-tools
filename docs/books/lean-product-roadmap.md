# LEAN PRODUCT ROADMAP & ANTI-HALLUCINATION GUARDRAILS
> **A Comprehensive System Manual & Execution Roadmap based on *The Lean Product Playbook* by Dan Olsen**  
> *Target Audience: AI Agents, Product Managers, & Startup Founders*

> [!IMPORTANT]
> **Tài liệu phái sinh (Derivative).** Đây là bản tóm tắt được soạn lại từ cuốn sách, **không phải nguồn
> gốc**. Nơi nào tài liệu này mâu thuẫn với cuốn sách, **cuốn sách thắng**. Các điểm đã được đối chiếu
> với nguyên văn của tác giả và sửa lại ngày 2026-09-16; toàn bộ bằng chứng được ghi tại
> [source_fidelity_review.md](../../.devtool/epic/lean_product_suite/source_fidelity_review.md).

---

## 📑 MỤC LỤC
1. [Triết Lý Cốt Lõi & Kiến Trúc Không Gian (Core Philosophy)](#1-triết-lý-cốt-lõi--kiến-trúc-không-gian)
2. [Roadmap Quy Trình 6 Bước (The Lean Product Process Workflow)](#2-roadmap-quy-trình-6-bước)
   - [Bước 1: Determine Target Customer](#bước-1-determine-target-customer)
   - [Bước 2: Identify Underserved Customer Needs](#bước-2-identify-underserved-customer-needs)
   - [Bước 3: Define Value Proposition](#bước-3-define-value-proposition)
   - [Bước 4: Specify MVP Feature Set](#bước-4-specify-mvp-feature-set)
   - [Bước 5: Create MVP Prototype](#bước-5-create-mvp-prototype)
   - [Bước 6: Test MVP with Customers](#bước-6-test-mvp-with-customers)
3. [Khung Toán Học & Thuật Toán Ra Quyết Định (Decision Frameworks)](#3-khung-toán-học--thuật-toán-ra-quyết-định)
4. [Vòng Lặp Tối Ưu & Định Lượng PMF (Iteration & Analytics)](#4-vòng-lặp-tối-ưu--định-lượng-pmf)
5. [Bộ Quy Tắc Chống Hallucination Cho AI Agents (Anti-Hallucination Guardrails)](#5-bộ-quy-tắc-chống-hallucination-cho-ai-agents)

---

## 1. TRIẾT LÝ CỐT LÕI & KIẾN TRÚC KHÔNG GIAN

### 1.1. Tách Biệt Tuyệt Đối: Problem Space vs. Solution Space

```
+-------------------------------------------------------------------+
|                        SOLUTION SPACE                             |
|  - UX (User Experience)                                          |
|  - Feature Set (Tập tính năng, mã nguồn, thuật toán, UI/UX)       |
+-------------------------------------------------------------------+
======================= INTERFACE / BOUNDARY ========================
+-------------------------------------------------------------------+
|                         PROBLEM SPACE                             |
|  - Value Proposition (Định vị giá trị, chiến lược cạnh tranh)     |
|  - Underserved Needs (Nhu cầu chưa được đáp ứng đủ)               |
|  - Target Customer (Khách hàng mục tiêu & Personas)               |
+-------------------------------------------------------------------+
```

* **Problem Space (Không gian Vấn đề)**: Nơi chứa đựng nhu cầu, nỗi đau, mong muốn và mục tiêu của khách hàng ("CÁI GÌ" & "TẠI SAO"). Khách hàng sở hữuProblem Space.
* **Solution Space (Không gian Giải pháp)**: Nơi chứa sản phẩm, thiết kế, công nghệ, giao diện và dòng code ("THẾ NÀO"). Doanh nghiệp sở hữu Solution Space.
* **Quy tắc vàng**: **Khách hàng quan tâm đến vấn đề của họ, không quan tâm đến giải pháp của bạn.** Mọi quyết định thiết kế tính năng phải bắt nguồn từ Problem Space và đi ngược ra Solution Space.

### 1.2. Kim Tự Tháp Product-Market Fit (The PMF Pyramid)

PMF được định nghĩa là **mức độ sản phẩm (3 tầng trên) thỏa mãn thị trường (2 tầng dưới)**.

1. **UX (User Experience)** *(Solution Space)*: Giao diện, trải nghiệm trực tiếp đưa tính năng đến người dùng.
2. **Feature Set** *(Solution Space)*: Bó tính năng cụ thể giải quyết nhu cầu.
3. **Value Proposition** *(Problem Space - Interface)*: Tuyên bố chiến lược xác định sản phẩm sẽ giỏi hơn đối thủ ở điểm nào.
4. **Underserved Needs** *(Problem Space)*: Các nhu cầu có tầm quan trọng cao nhưng độ hài lòng hiện tại thấp.
5. **Target Customer** *(Problem Space)*: Phân đoạn khách hàng cụ thể có cùng bộ nhu cầu.

> [!WARNING]
> **Kim tự tháp có 5 TẦNG; Quy trình có 6 BƯỚC. Đây là hai đối tượng khác nhau.**
> "MVP Prototype" và "Test with Customers" là **bước** của Lean Product Process, **không phải tầng** của
> Kim tự tháp PMF. Gộp hai mô hình lại sẽ làm biến mất tầng **UX** — đúng tầng mà quy trình lùi-tầng
> (Tectonic Plates) thường cần gọi tên nhất.

---

## 2. ROADMAP QUY TRÌNH 6 BƯỚC

```
[Target Customer] ➔ [Underserved Needs] ➔ [Value Proposition] ➔ [MVP Feature Set] ➔ [MVP Prototype] ➔ [Customer Test]
     (Tầng 1)              (Tầng 2)             (Tầng 3)            (Tầng 4)          (Tầng 5)          (Tầng 6)
```

---

### Bước 1: Determine Target Customer

* **Mục tiêu**: Xác định rõ ràng phân đoạn khách hàng mục tiêu và nhóm người dùng trải nghiệm sớm (Early Adopters).
* **Quy trình xử lý**:
  1. Phân đoạn thị trường theo: Demographics, Psychographics, Behavioral, và đặc biệt là **Needs-Based Segmentation** (Phân đoạn theo Nhu cầu).
  2. Xác định vai trò: Phân biệt **Users** (Người trực tiếp dùng) và **Buyers** (Người trả tiền).
  3. Định vị trên biểu đồ **Technology Adoption Life Cycle** (Innocators, Early Adopters, Early Majority, Late Majority, Laggards). Tập trung vào **Early Adopters**.
  4. Tạo **Personas** giả định chứa: Tên, Chức danh, Hành vi, Mục tiêu cốt lõi, Nỗi đau lớn nhất.
* **Rules / Validation**:
  - ⛔ *Không được tạo Persona chung chung kiểu "Tất cả mọi người".*
  - ⛔ *Phải kiểm chứng xem các thành viên trong cùng 1 Persona có thực sự chia sẻ cùng một cấu trúc nhu cầu hay không.*

---

### Bước 2: Identify Underserved Customer Needs

* **Mục tiêu**: Đào sâu Problem Space để tìm ra những nhu cầu chưa được các giải pháp hiện tại đáp ứng tốt.
* **Quy trình xử lý**:
  1. Tiến hành phỏng vấn khám phá khách hàng (Customer Discovery Interviews).
  2. Dùng kỹ thuật **Customer Benefit Laddering** (Hỏi "Tại sao" nhiều lần để đẩy từ thuộc tính cơ bản lên giá trị cốt lõi).
  3. Đo lường theo Khung **Importance vs. Satisfaction**:
     - **Importance (Tầm quan trọng)**: Nhu cầu này quan trọng như thế nào với khách hàng? (Thang 1-5 hoặc 0-100%).
     - **Satisfaction (Mức độ hài lòng)**: Khách hàng hài lòng thế nào với các giải pháp hiện có trên thị trường? (Thang 1-7 hoặc 0-100%).
  4. **Chuẩn hóa thang đo trước khi tính (bước bắt buộc, không được bỏ qua)**:
     - *Vì sao hai thang khác nhau*: Satisfaction có cực âm (hài lòng / không hài lòng) nên dùng thang
       **lưỡng cực (bipolar) 7 điểm**; Importance chỉ là mức độ, không có giá trị âm, nên dùng thang
       **đơn cực (unipolar) 5 điểm**. Thang lưỡng cực luôn dùng số điểm lẻ để có mốc trung tính ở giữa.
     - *Giới hạn thiết kế thang*: quá 11 lựa chọn sẽ làm khách hàng quá tải; dưới 5 lựa chọn thì mất độ phân giải.
     - *Bảng quy đổi của Olsen*: thang 5 điểm → 0 / 25 / 50 / 75 / 100 (hoặc 0 / 2.5 / 5 / 7.5 / 10);
       thang 7 điểm → 0 / 16.7 / 33.3 / 50 / 66.7 / 83.3 / 100.
     - ⛔ *Đưa thẳng điểm thô 1-5 và 1-7 vào công thức mà chưa quy đổi sẽ cho ra con số vô nghĩa.*
  5. Xác định **Opportunity Score** (Điểm cơ hội) để chọn bài toán đáng giải nhất.
* **Rules / Validation**:
  - ⛔ *Không mô tả nhu cầu bằng tên tính năng. Ví dụ: Đúng = "Muốn di chuyển nhanh từ A đến B", Sai = "Muốn có ứng dụng gọi xe Uber".*
  - ⛔ *Tập trung vào góc phần tư phía trên bên trái: Importance Cao (High) & Satisfaction Thấp (Low).*

---

### Bước 3: Define Value Proposition

* **Mục tiêu**: Xây dựng ma trận định vị chiến lược để thắng đối thủ cạnh tranh.
* **Quy trình xử lý**:
  1. Áp dụng **Mô hình Kano** để phân loại các lợi ích khách hàng thành 3 nhóm:
     - **Must-Haves (Bắt buộc phải có)**: Thiếu sẽ gây thất vọng nặng nề; có thì khách hàng coi là hiển nhiên.
     - **Performance Benefits (Lợi ích hiệu năng)**: Tỷ lệ thuận tuyến tính — càng nhiều/càng tốt thì khách hàng càng hài lòng.
     - **Delighters (Yếu tố gây bất ngờ/thích thú)**: Khách hàng không kỳ vọng trước, nhưng khi có sẽ tạo ra sự hào hứng vượt trội (Wow factor).
  2. Lập **Bảng Lập Chiến Lược Giá Trị (Value Proposition Template)** so sánh với các đối thủ chính:
     - Must-Haves: Tất cả sản phẩm phải đạt "Yes".
     - Performance Benefits: Đánh giá High / Medium / Low hoặc số liệu cụ thể.
     - Delighters: Xác định 1-2 yếu tố độc nhất mà đối thủ chưa có.
  3. Xác định **Key Differentiator**: Chọn ra đúng 1-2 Performance Benefits mà sản phẩm quyết định ĐÁNH BẠI đối thủ, cùng với Delighter cốt lõi.
* **Rules / Validation**:
  - ⛔ *Không thể thắng đối thủ ở tất cả các khía cạnh. Chiến lược là biết nói "KHÔNG" với các khía cạnh không ưu tiên.*
  - ⛔ *Sản phẩm "Me-too" (bản sao) không có Delighter hoặc không giỏi hơn ở bất kỳ Performance Benefit nào chắc chắn thất bại.*

---

### Bước 4: Specify MVP Feature Set

* **Mục tiêu**: Chọn ra tập tính năng nhỏ nhất (Minimum Viable Feature Set) đủ để kiểm chứng Value Proposition.
* **Quy trình xử lý**:
  1. Viết **User Stories** cho các nhu cầu đã chọn trong Value Proposition: `As a [user], I want to [action], so that [benefit]`.
  2. Chia nhỏ tính năng (**Feature Chunking**): Tách các User Story lớn thành các mảnh nhỏ đủ khả năng ước lượng chính xác.
  3. Ước lượng Chi phí/Nỗ lực (**Investment / Developer-Weeks / Story Points**).
  4. Ước lượng Giá trị tạo ra (**Return / Customer Value Created**).
  5. **Sắp xếp ưu tiên bằng ROI định lượng (phương pháp chính)**:
     $$\text{ROI} = \frac{\text{Customer Value Created}}{\text{Development Effort (developer-weeks)}}$$
     - Giá trị khách hàng phải chấm trên **thang tỷ lệ (ratio scale)**: điểm 10 phải thực sự gấp đôi điểm 5.
     - Sắp xếp toàn bộ feature chunk thành **danh sách xếp hạng**. Mục đích không phải là con số ROI
       chính xác mà là **thứ tự so sánh giữa chúng**.
     - *Quy tắc phá hòa*: hai chunk cùng ROI thì **ưu tiên chunk nhỏ hơn**, vì giao giá trị sớm hơn.
     - *Nước đi của đội giỏi*: thay vì loại một ý tưởng giá trị cao nhưng tốn công, hãy chia nhỏ nó, cắt
       bỏ phần ít giá trị, và tìm cách giao cùng giá trị với ít công sức hơn — đẩy nó sang trái trên biểu đồ.
     - **Ma trận ROI 3x3 (Value vs. Effort Grid) chỉ là phương án DỰ PHÒNG** — chính Olsen gọi đây là cách
       dùng "kém chặt chẽ hơn", dành cho khi không ước lượng được bằng số. Khi dùng, phải nói rõ là đang dùng dự phòng.
  6. Chọn ứng viên **MVP Candidate** theo **quy tắc cấu thành**, không theo ngưỡng cắt thứ hạng:
     1. **Toàn bộ** Must-Haves đã xác định — bắt buộc, **bất kể thứ hạng ROI**.
     2. Đủ số chunk của **đúng một** Performance Benefit được chọn để thắng, đủ để khách hàng thấy được sự khác biệt.
     3. **Delighter hàng đầu** — chỉ được bỏ khi lợi thế Performance đã đủ lớn để tự đứng vững.
     - ⛔ *Olsen nói rõ: "đôi khi bạn không thể đi theo đúng thứ tự xếp hạng để tạo ra một MVP hoàn chỉnh;
       bạn có thể cần **nhảy xuống** để đưa vào những tính năng quan trọng." Một Must-Have tốn công vẫn
       phải nằm trong v1 — ROI xếp thứ tự công việc, ROI không quyết định tư cách thành viên của MVP.*
  7. Lập **lưới Lợi ích × Feature Chunk** (Hình 6.3/6.4): mỗi hàng là một lợi ích (`M1`, `M2`, `P1`…, `D1`…),
     các chunk của lợi ích đó xếp theo thứ tự ưu tiên từ trái sang. **Cột trái nhất là v1**; các chunk bị
     đẩy sang phải trở thành v1.1, v1.2. Không lập kế hoạch quá **một đến hai** phiên bản phụ.
* **Rules / Validation**:
  - ⛔ *MVP không được cắt gọt theo chiều ngang chất lượng (chỉ làm tính năng chạy được mà bỏ qua trải nghiệm/độ tin cậy).*
  - ⛔ *Cắt MVP theo lát cắt dọc hẹp: hẹp về phạm vi tính năng nhưng **trọn vẹn** qua cả bốn thuộc tính
    **Functional, Reliable, Usable, Delightful**.*
  - 📖 *Nguồn chính xác*: đây là **Kim tự tháp Thuộc tính MVP** (Hình 7.1, "Building an MVP"). Olsen ghi rõ
    ông phỏng theo hình của nhà thiết kế UX **Jussi Pasanen** (Volkside), người ghi công **Aarron Walter,
    Ben Tollady và Ben Rowe**. Ẩn dụ "cupcake / bánh cưới" là của **Brandon Schauer**, **không có trong
    cuốn sách này** — không được gán cho Olsen.

---

### Bước 5: Create MVP Prototype

* **Mục tiêu**: Biến MVP Feature Set trong Solution Space thành một artifact có thể đưa cho khách hàng tương tác và nhận phản hồi mà chưa cần tốn chi phí lập trình hoàn thiện.
* **Quy trình xử lý**:
  1. Lựa chọn dạng MVP Test phù hợp trong Ma trận 2x2 (Qualitative/Quantitative x Product/Marketing):
     - **Qualitative Product Test**: Wireframes, Interactive Prototypes (Figma/InVision), Wizard of Oz, Concierge.
     - **Quantitative Product Test**: Fake door page, Product analytics on live beta.
     - **Qualitative Marketing Test**: Landing page mockups, Sales collateral.
     - **Quantitative Marketing Test**: Smoke test landing page, Ad campaign, Crowdfunding (Kickstarter).
  2. Áp dụng các nguyên tắc **UX Design** chuẩn mực: Visual Hierarchy, Clear Information Architecture, Navigation, Affordance, Reducing Cognitive Load.
* **Rules / Validation**:
  - ⛔ *Phân biệt rõ: Landing Page/Smoke test chỉ kiểm thử MARKETING (nhu cầu quan tâm), KHÔNG kiểm thử được PRODUCT-MARKET FIT thực sự.*
  - ⛔ *Để kiểm thử Product-Market Fit, phải cho người dùng tương tác với sản phẩm hoặc Prototype trải nghiệm tính năng.*

---

### Bước 6: Test MVP with Customers

* **Mục tiêu**: Thu thập phản hồi thực tế từ khách hàng mục tiêu để kiểm chứng các giả thuyết.
* **Quy trình xử lý**:
  1. Lập kịch bản phỏng vấn & bài kiểm thử sử dụng (Usability & PMF Testing Script).
  2. Tuyển chọn chính xác nhóm khách hàng theo đúng Persona (Screener Questions).
  3. Chạy testing theo từng **Wave (Làn sóng)**:
     - Mỗi làn sóng gồm **5 đến 8 khách hàng** — đủ để nhận diện pattern phản hồi.
     - ⚠️ *Con số "5 người dùng phát hiện 85% lỗi UX" là của **Jakob Nielsen**, không phải của Olsen; đừng
       gán nó cho cuốn sách này.*
  4. Tổng hợp bài học sau mỗi wave: Phân loại phản hồi thành (1) Vấn đề UX, (2) Thiếu hụt tính năng, (3) Sai lệch Value Proposition, (4) Sai Target Customer.
  5. Thực hiện Vòng lặp **Hypothesize - Design - Test - Learn Loop**.
* **Rules / Validation**:
  - ⛔ *Phỏng vấn SAI đối tượng khách hàng mục tiêu sẽ dẫn đến dữ liệu rác (Bad Data) cực kỳ nguy hiểm.*
  - ⛔ *Không dẫn dắt câu hỏi (Leading questions). Hãy quan sát hành vi thực tế của họ thay vì chỉ nghe lời họ nói.*

---

## 3. KHUNG TOÁN HỌC & THUẬT TOÁN RA QUYẾT ĐỊNH

### 3.1. Thuật Toán Tính Điểm Cơ Hội (Opportunity Score)

Được áp dụng ở **Bước 2** để ưu tiên giải quyết các nhu cầu của khách hàng.

* **Công thức Dan Olsen (Visual Customer Value)**:
  $$\text{Customer Value Delivered} = \text{Importance} \times \text{Satisfaction}$$
  $$\text{Opportunity to Add Value} = \text{Importance} \times (1 - \text{Satisfaction})$$
  *(Trường hợp đo bằng tỷ lệ 0% - 100% hay 0.0 - 1.0)*

* **Công thức Anthony Ulwick (Jobs-to-be-Done / Outcome-Driven Innovation)**:
  $$\text{Opportunity Score} = \text{Importance} + \max(\text{Importance} - \text{Satisfaction}, 0)$$
  *(Thang điểm 0 - 10: Điểm $> 15$ là cơ hội vô cùng hấp dẫn; Điểm $< 10$ là không hấp dẫn).*

---

### 3.2. Quy Tắc Sắp Xếp Ưu Tiên ROI 3x3 Grid

Được áp dụng ở **Bước 4** để sắp xếp thứ tự phát triển tính năng:

| Value \ Effort | Low Effort | Medium Effort | High Effort |
| :--- | :---: | :---: | :---: |
| **High Value** | **Ưu tiên 1** (ROI Cao nhất) | **Ưu tiên 3** | **Ưu tiên 6** |
| **Medium Value** | **Ưu tiên 2** | **Ưu tiên 5** | **Ưu tiên 8** |
| **Low Value** | **Ưu tiên 4** | **Ưu tiên 7** | **Ưu tiên 9** (Bỏ qua) |

---

### 3.3. Ma Trận Đánh Giá Đối Thủ Cạnh Tranh (Kano Matrix)

Được áp dụng ở **Bước 3** để chốt Value Proposition:

```text
[Bảng Giá Trị Sản Phẩm / Value Proposition Grid]

HẠNG MỤC BENIFIT          DỐI THỦ A      ĐỐI THỦ B      SẢN PHẨM CỦA TÔI
-------------------------------------------------------------------------
Must-Haves:
  - Feature A1            Yes            Yes            Yes
  - Feature A2            Yes            Yes            Yes

Performance Benefits:
  - Benefit B1 (Tốc độ)   Low            High           MEDIUM
  - Benefit B2 (Chính xác)High           Low            HIGH (Differentiator)

Delighters:
  - Delighter C1          Yes            No             No
  - Delighter C2 (Mới)    No             No             YES (Unique Wow)
```

---

## 4. VÒNG LẶP TẤI ƯU & ĐỊNH LƯỢNG PMF

### 4.1. Vòng Lặp Hypothesize - Design - Test - Learn Loop

Thay thế cho mô hình Build-Measure-Learn cổ điển để tránh cái bẫy "phải code sản phẩm thật mới đo lường được":

```
       +--------------------+
       |    HYPOTHESIZE     | <---+ (Chỉnh sửa giả thuyết)
       +--------------------+     |
                 |                |
                 v                |
       +--------------------+     |
       |       DESIGN       |     | (Chuyển sang Solution Space)
       +--------------------+     |
                 |                |
                 v                |
       +--------------------+     |
       |        TEST        |     | (Thu thập quan sát)
       +--------------------+     |
                 |                |
                 v                |
       +--------------------+     |
       |       LEARN        | ----+ (Rút ra Validated Learning)
       +--------------------+
```

---

### 4.2. Thước Đo Định Lượng PMF (Sean Ellis Metric)

Gửi khảo sát cho những người đã trải nghiệm sản phẩm với câu hỏi cốt lõi:
> *"Bạn sẽ cảm thấy thế nào nếu không còn được sử dụng sản phẩm này nữa?"*

* **A. Rất thất vọng (Very disappointed)**
* **B. Hơi thất vọng (Somewhat disappointed)**
* **C. Không thất vọng (Not disappointed)**
* **D. N/A - Không còn sử dụng nữa**

👉 **Quy tắc Benchmark PMF**: Nếu **$\ge 40\%$** người dùng chọn **"Rất thất vọng"**, sản phẩm đã đạt **Product-Market Fit**. Bạn đã sẵn sàng để scale/grow.

---

### 4.3. Mô Hình AARRR & MTMM (Metric That Matters Most)

Sau khi ra mắt sản phẩm live, tối ưu hóa theo phễu Pirating Metrics:

1. **Acquisition**: Lượng truy cập/Thu hút người dùng.
2. **Activation**: Tỷ lệ người dùng đạt trải nghiệm "Aha Moment" đầu tiên.
3. **Retention**: Tỷ lệ giữ chân người dùng theo thời gian (Retention Curve đi ngang = dấu hiệu PMF).
4. **Referral**: Tỷ lệ người dùng giới thiệu người dùng mới (Viral coefficient).
5. **Revenue**: Lợi nhuận & Doanh thu (LTV > 3x CAC).

👉 **Nguyên tắc MTMM**: Tại mỗi thời điểm, chỉ tập trung vào **DUY NHẤT 1 chỉ số** mang lại ROI cải thiện doanh nghiệp cao nhất.
- *Ví dụ*: Nếu Activation Rate chỉ đạt 10%, việc đổ tiền chạy Ads (Acquisition) là hoàn toàn lãng phí. MTMM lúc này bắt buộc phải là Activation Rate.

---

## 5. BỘ QUY TẮC CHỐNG HALLUCINATION CHO AI AGENTS

Khi đóng vai trò AI Agent tư vấn hoặc phát triển sản phẩm theo Lean Product, Agent **BẮT BUỘC** phải tuân thủ các điều kiện logic (Guardrails) sau đây để không đưa ra tư vấn sai lệch:

### 🛡️ Guardrail 1: Tách Biệt Hai Không Gian — Ghi Nhận, Quy Đổi, Tạm Gác
* **Lỗi AI thường gặp**: Khi người dùng đưa ra một ý tưởng, AI lập tức đề xuất danh sách tính năng, giao diện app, hay sơ đồ cơ sở dữ liệu.
* **Luật bắt buộc**: Nếu chưa xác định rõ **Target Customer** và **Underserved Need**, AI **KHÔNG ĐƯỢC**
  đề xuất danh sách tính năng chi tiết, schema hay wireframe.
* **Nhưng AI cũng KHÔNG ĐƯỢC từ chối người dùng.** Luật của Olsen là **tách biệt và luân phiên**, không
  phải cấm đoán: *"học hỏi tốt nhất về Problem Space thường đến từ phản hồi của khách hàng trên chính các
  artifact Solution Space mà bạn đã tạo ra."* Bản thân Lean Product Process cố ý bước vào Solution Space
  ở Bước 4, 5 và 6.
* **Hành vi đúng — ba nhịp**:
  1. **Ghi nhận**: chép nguyên văn ý tưởng giải pháp vào mục *Solution Space Parking Lot*.
  2. **Quy đổi**: chuyển nó thành nhu cầu Problem Space mà nó hàm ý, rồi nhờ người dùng xác nhận bản quy đổi.
  3. **Tạm gác**: tiếp tục bước hiện tại, và **mang mục đã gác trở lại ở Bước 4**.
* **Điều thực sự cần chặn** là một ý tưởng giải pháp **thay thế cho** một giả thuyết nhu cầu đã kiểm chứng
  — không phải sự tồn tại của ý tưởng đó.

### 🛡️ Guardrail 2: Kiểm Tra Tectonic Plates (Sự Thay Đổi Đáy Kim Tự Tháp)
* **Lỗi AI thường gặp**: Khi thử nghiệm thất bại, AI cố gắng sửa lỗi bằng cách gợi ý đổi màu nút bấm, đổi giao diện (UX).
* **Luật bắt buộc**: Nhắc nhở người dùng rằng các tầng đáy (Target Customer, Value Proposition) giống như các mảng kiến tạo (Tectonic plates). Nếu vấn đề nằm ở Target Customer sai, sửa UX là vô nghĩa. AI phải hướng dẫn kiểm tra từ đáy kim tự tháp lên đỉnh.

### 🛡️ Guardrail 3: Phân Biệt Rõ Giữa "Nhu Cầu" Và "Tính Năng"
* **Lỗi AI thường gặp**: AI nhầm lẫn giữa lời nói của khách hàng về một giải pháp với nhu cầu thực sự.
* **Luật bắt buộc**: Khi người dùng nói "Khách hàng muốn có tính năng AI Chatbot", AI phải chuyển đổi sang Problem Space: "Nhu cầu cốt lõi ở đây là *muốn nhận phản hồi hỗ trợ ngay lập tức mà không phải chờ đợi lâu*".

### 🛡️ Guardrail 4: Yêu Cầu Cân Bằng Trong MVP
* **Lỗi AI thường gặp**: AI đề xuất MVP chỉ có mỗi tính năng sơ khai không dùng được hoặc ngược lại, đề xuất làm quá nhiều thứ.
* **Luật bắt buộc**: Mọi MVP do AI thiết kế phải tuân thủ nguyên tắc lát cắt dọc (Slice): Phải đạt đồng thời 4 tầng **Functional, Reliable, Usable, Delightful** trên đúng tập tính năng tối thiểu đã chọn.

### 🛡️ Guardrail 5: Đưa Ra Công Thức Cụ Thể, Không Đoán Mờ
* **Lỗi AI thường gặp**: AI đưa ra các nhận định chung chung như "Nhu cầu này rất lớn" hay "Tính năng này rất quan trọng".
* **Luật bắt buộc**: AI phải sử dụng các khung lượng hóa: Yêu cầu đánh giá Importance (1-10) và Satisfaction (1-10), sau đó tự động tính toán **Opportunity Score** và xếp vị trí trên **Ma trận ROI 3x3**.

---
*Tài liệu này là bản Roadmap quy chuẩn được trích xuất trực tiếp từ các nguyên lý cốt lõi của Dan Olsen trong "The Lean Product Playbook", dùng làm khung tham chiếu cho con người và AI Agents trong quá trình xây dựng sản phẩm tinh gọn.*
