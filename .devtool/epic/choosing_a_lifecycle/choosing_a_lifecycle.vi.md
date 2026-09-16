# Tài liệu: Chọn lifecycle nào

> Bản dịch của [choosing_a_lifecycle.en.md](choosing_a_lifecycle.en.md). Bản tiếng Anh là nguồn sự
> thật cho tooling và agent; bản này phục vụ trao đổi trong nhóm và phải luôn đồng bộ.

## 1. Meta Data

```
Kind: document
Audience: Người làm việc trong repo này, đang cầm một việc cụ thể và không biết nên vào lifecycle
          nào. Họ đã biết miền vấn đề — họ làm ở đây — nên cần chỉ dẫn hành động, không cần dạy lại.
Diátaxis mode: how-to guide
Non-goals: Giải thích vì sao các lifecycle tồn tại, dạy từng skill, hay mô tả điều gì diễn ra bên
           trong một lifecycle sau khi đã vào. Mỗi skill tự tài liệu hóa phần của nó.
Acceptance: Người cầm một việc tới được đúng lifecycle, và biết nó tốn bao nhiêu cổng, mà không phải
            hỏi ai.
Deliverable: docs/choosing-a-lifecycle.md
Source Spec: không có — tài liệu này được tạo ra như bài nghiệm thu Tier C của epic
             document_lifecycle_suite.
```

## 2. Vì sao có tài liệu này

Trước epic này chỉ có một lifecycle. Giờ có ba, và không có gì chỉ cho người đọc biết việc của họ
thuộc nhánh nào. `README.md` nêu tên chúng; nó không định tuyến.

## 3. Phân loại Diátaxis

Câu hỏi của người đọc là *"giờ tôi nên làm gì"* — nó **informs action** và phục vụ việc **application**
của kỹ năng họ đã có. Theo compass của Procida, đó là **how-to guide**, và đúng một mode áp dụng:
không phần nào dạy người mới (tutorial), liệt kê tham số (reference), hay bảo vệ một luận điểm
(explanation).

## 4. Outline

| # | Section | Mục đích |
|---|---|---|
| 1 | Bắt đầu từ đây | Đưa người đọc tới đúng nhánh bằng một câu hỏi |
| 2 | Nếu bạn viết code | Chỉ sang dev-lifecycle hoặc writing-plans theo số mảnh review được, và nêu ai thực thi plan |
| 3 | Nếu bạn viết tài liệu | Chỉ sang doc-lifecycle, kèm ngưỡng dưới đó thì không áp dụng |
| 4 | Nếu chưa biết nên xây gì | Chỉ ngược lên lean-product-lifecycle, kèm chi phí cổng thật đầu-cuối |
| 5 | Nếu việc quá nhỏ | Cho phép bỏ mọi lifecycle, nhưng vẫn giữ cổng chất lượng |
| 6 | Bàn giao giữa các lifecycle | Chuyển nhánh mà không mất việc và không làm một cổng bị coi là đã qua |

## 5. Xác minh

Cổng 2 là `doc_quality_check`. Nó fail hai lần trước khi pass; các vòng và những gì bắt được ghi tại
[`../document_lifecycle_suite/task_10_tier_c_acceptance.md`](../document_lifecycle_suite/task_10_tier_c_acceptance.md).

## 6. Phân rã task Kanban

Không có. Luật Concurrent-Epic Backlog áp dụng: `document_lifecycle_suite` đang có task hoạt động, nên
mọi task file sinh ra ở đây sẽ mang `status: "backlog"` và không làm được. Sáu section được viết trực
tiếp, mỗi section một commit, và phần phân rã chính là outline ở trên.
