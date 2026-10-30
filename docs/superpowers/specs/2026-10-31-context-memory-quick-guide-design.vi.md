# Đặc tả Nội dung Quick-Guide Quy trình Bộ nhớ Ngữ cảnh và Ba Vai trò

## Table of Contents

- [1. Mục đích và Luận điểm Cốt lõi](#1-mục-đích-và-luận-điểm-cốt-lõi)
- [2. Phạm vi và Nội dung Bắt buộc](#2-phạm-vi-và-nội-dung-bắt-buộc)
- [3. Phạm vi Ngoài Mục tiêu](#3-phạm-vi-ngoài-mục-tiêu)
- [4. Tiêu chí Nghiệm thu Thực tế](#4-tiêu-chí-nghiệm-thu-thực-tế)
- [5. Phụ thuộc và Sự kiện Cập nhật](#5-phụ-thuộc-và-sự-kiện-cập-nhật)

## 1. Mục đích và Luận điểm Cốt lõi

Lập trình viên và các AI Agent làm việc trên không gian đa repository (`ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`) và đa tài khoản Antigravity (`antigravity_homes/<profile>`) cần một tài liệu hướng dẫn thực hành ngắn gọn, tra cứu được ngay (`docs/context-memory-quick-guide.en.md` và `docs/context-memory-quick-guide.vi.md`).

Nếu thiếu một sổ tay kịch bản thực chiến (Quick-Guide), mỗi lần đổi tài khoản hoặc chuyển pha giữa thiết kế, review và code thực thi, lập trình viên phải tự gõ lại prompt theo trí nhớ hoặc dễ gọi nhầm vai trò cho Agent (ví dụ: để Agent tư vấn tự ý sửa production code, hoặc làm mất trạng thái khi chạy nhiều epics song song).

Tài liệu này khẳng định mọi bước chuyển giao trong dự án có áp dụng Two-Tier Project Memory đều ánh xạ tường minh vào một trong ba vai trò quản trị (**Human Architect**, **AI Assistant**, **AI Programmer**) và năm kịch bản vận hành chuẩn thông qua `resume` / `save-context` (`scripts/resume_context.py`).

## 2. Phạm vi và Nội dung Bắt buộc

Cặp tài liệu Quick-Guide (`docs/context-memory-quick-guide.en.md` và `docs/context-memory-quick-guide.vi.md`) bao gồm:

1. **Ma trận Quản trị Ba Vai trò & Bảng Cheat-Sheet Lệnh 10 Giây**:
   - Ranh giới quyền hạn rõ ràng giữa **2.1 Human Architect**, **2.2 AI Assistant (`--role assistant`)**, và **2.3 AI Programmer (`--role programmer`)**.
   - Bảng tra cứu nhanh các shell aliases (`resume`, `save-context`), slash skills (`/resume-context`, `/save-context`), và 5 chế độ `--emit-prompt` (`principal-review`, `implement`, `cross-review`, `finish`, `assistant`).
2. **Sơ đồ Luồng Vận hành Toàn trình**:
   - Biểu đồ Mermaid `flowchart TD` và `sequenceDiagram` minh họa cách Tier 1 (`.devtool/PROJECT_LEDGER.md`) và Tier 2 (`.devtool/state/<epic_slug>.md` cùng `.devtool/logs/activity_<epic_slug>.log`) kết nối ba vai trò qua toàn bộ các cổng phê duyệt.
3. **Kịch bản 1: Sau bước Đóng gói Epic (`Package`) → Gọi AI Assistant thực hiện Principal Review**:
   - Điểm kích hoạt: Epic vừa được đóng gói (`handoff.md` đã commit ở cuối Stage 2).
   - Lệnh và prompt cụ thể để nạp ngữ cảnh dưới vai trò **AI Assistant**, chạy `d3nexus:principal-review`, phân loại (triage) findings cùng Human Architect, lưu trạng thái (`--state`), và xuất **Prompt Lập trình cho AI Programmer** (`--emit-prompt implement`).
4. **Kịch bản 2: Sau khi Review PASS → Giao Prompt cho AI Programmer thực thi `/dev-implementation`**:
   - Điểm kích hoạt: Principal Review đạt `PASS` và bạn giao **Prompt cho AI Programmer** (`/dev-implementation`).
   - Cách **AI Programmer** tự nạp ngữ cảnh bên trong `.worktrees/<epic_dir>` (`--role programmer`), lập trình từng task theo TDD, tự động ghi nhật ký (`--log` + `--state`), và xuất **Prompt cho Cross-Model Review** (`--emit-prompt cross-review`) khi Gate 4 `PASS`.
5. **Kịch bản 3: Sau khi Implementation hoàn tất (Gate 4 PASS) → Gọi AI Assistant thực hiện Cross-Model Review**:
   - Điểm kích hoạt: Gate 4 đạt `PASS` và bạn chọn Cross-Model Review hoặc Local Model Review.
   - Cách **AI Assistant** nạp ngữ cảnh (`--role assistant`), chạy `d3nexus:cross-model-review`, trình bày bảng triage đã đối chiếu code thật, và xuất **Prompt Fix cho AI Programmer** (`--emit-prompt implement`) hoặc **Prompt Đóng nhánh** (`--emit-prompt finish`).
6. **Kịch bản 4: Gọi AI Assistant Đọc hiểu Context chỉ để Trao đổi Technicals / Giải pháp / Debug (Ad-Hoc)**:
   - Điểm kích hoạt: Bạn mở phiên mới hoặc đổi tài khoản chỉ để trao đổi bài toán kỹ thuật, phân tích nguyên nhân gốc rễ, hoặc đánh giá giải pháp mà không sửa code.
   - Cách gọi **AI Assistant** (`resume --role assistant` hoặc `/resume-context`), khóa cứng quy tắc cấm sửa production code, và lưu lại kết luận thảo luận hoặc ghi chú tùy chỉnh bất kỳ lúc nào qua `/save-context` (`save-context --checkpoint <epic_slug> "<custom_note>"` hoặc `--state --prompt "<note>"`).
7. **Kịch bản 5: Chạy Đa Epic Song song, Đổi Tài khoản Antigravity & Đóng nhánh Stage 4 (`/finish`)**:
   - Cách nhiều Agents làm việc đồng thời trên `epic-a` và `epic-b` mà không ghi đè trạng thái hay làm mất log của nhau.
   - Cách đổi tài khoản Antigravity vẫn giữ nguyên lịch sử terminal dùng chung (`~/.zsh_history`) và khôi phục toàn bộ ngữ cảnh chỉ bằng một lệnh `resume`.
   - Cách `/finish` chạy `resume_context.py --complete <epic_slug> "<milestone_summary>"` để ghi cột mốc vĩnh viễn vào `PROJECT_LEDGER.md` và chỉ đóng gói lưu trữ riêng state/log của epic đó vào `.devtool/archive/`.

## 3. Phạm vi Ngoài Mục tiêu

- Không đi sâu vào mã nguồn cài đặt Python của `scripts/resume_context.py` hay chi tiết cơ chế khóa `fcntl.flock` ở mức hệ điều hành (đã có trong `docs/architecture/save_resume_rules.md`).
- Không hướng dẫn chi tiết cách viết unit test/BDD cho từng ngôn ngữ lập trình (Flutter, Android, iOS, Python, Rust).
- Không bao gồm quy trình khám phá thị trường và kiểm chứng ý tưởng sản phẩm (`d3nexus:lean-product-lifecycle`).

## 4. Tiêu chí Nghiệm thu Thực tế

Sau khi đọc tài liệu Quick-Guide này, tại bất kỳ thời điểm nào trong dự án (vừa đổi tài khoản Antigravity, vừa đóng gói xong epic ở Stage 2, vừa vượt qua Gate 4, hoặc muốn mở một phiên thảo luận kỹ thuật độc lập), lập trình viên có thể chọn đúng kịch bản trong vòng chưa đầy 30 giây, chạy đúng lệnh CLI hoặc copy-paste khối prompt chuẩn để triệu hồi đúng vai trò (**AI Assistant** hoặc **AI Programmer**), và lưu/khôi phục ngữ cảnh mà không bao giờ gặp lỗi vượt quyền hay đè mất dữ liệu giữa các epics.

## 5. Phụ thuộc và Sự kiện Cập nhật

- **Phụ thuộc**: `scripts/resume_context.py`, `skills/resume-context/SKILL.md`, `skills/save-context/SKILL.md`, `rules/CRITICAL_RULES.md` (Rule 8), và bộ alias trong `/Users/danhdueexoictif/.zshrc` (`resume`, `save-context`).
- **Sự kiện cần cập nhật tài liệu**: Khi có thay đổi về tên chế độ `--emit-prompt`, tham số dòng lệnh của `scripts/resume_context.py`, hoặc thứ tự các cổng (Gates) trong `d3nexus:dev-lifecycle`.
