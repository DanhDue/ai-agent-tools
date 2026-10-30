# Kịch bản BDD Quản lý Bộ nhớ Ngữ cảnh

## Table of Contents

- [Chiều 1: Luồng Thành công](#chiều-1-luồng-thành-công)
- [Chiều 2: Trường hợp Biên](#chiều-2-trường-hợp-biên)
- [Chiều 3: Chuyển đổi Trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và Đa luồng Đa Agent](#chiều-4-bất-đồng-bộ-và-đa-luồng-đa-agent)
- [Chiều 5: Xử lý Lỗi và Độ bền Lưu trữ](#chiều-5-xử-lý-lỗi-và-độ-bền-lưu-trữ)

## Chiều 1: Luồng Thành công

```gherkin
Scenario: [CMM-HP-01] [Tier C - Integration] Thu hoạch Ngữ cảnh Hai Tầng, Cô lập Đa Epic và Nén Feature Hoàn thành
  Given một không gian làm việc đa repository nơi cả epic-alpha và epic-beta đều ghi nhận trạng thái đang chạy qua resume_context.py --state và nhật ký lập trình qua resume_context.py --log
  When kỹ sư chạy resume_context.py sau đó chạy tiếp resume_context.py --complete epic-alpha "Delivered alpha engine"
  Then lần thu hoạch đầu tiên in đủ 6 phần chuẩn (0. PROJECT ARCHITECTURAL LEDGER, 1. ACTIVE EPIC STATE, 2. RECENT PROGRAMMER ACTIVITY, 3. GIT WORKING TREE STATUS, 4. OPEN CONTRACT GAPS & RFCS, 5. ACTIVE TASKS) bao gồm cả epic-alpha và epic-beta
  And sau lệnh --complete epic-alpha, cột mốc "- **[YYYY-MM-DD] `epic-alpha`**: Delivered alpha engine" được ghi nối tiếp vào .devtool/PROJECT_LEDGER.md
  And state cùng activity log của epic-alpha được chuyển vào .devtool/archive/ trong khi state (.devtool/state/epic-beta.md) và activity log (.devtool/logs/activity_epic-beta.log) của epic-beta vẫn giữ nguyên trạng thái active trong .devtool/assistant_state.md và .devtool/activity_stream.log

Scenario: [CMM-HP-02] [Tier C - Integration] Đồng bộ Môi trường Zshrc Đa Profile, Lịch sử Terminal Dùng chung và Aliases
  Given một môi trường máy chủ có file .zshrc gốc và nhiều thư mục profile Antigravity dưới antigravity_homes/<profile>
  When kỹ sư chạy lệnh resume_context.py --sync-zshrc
  Then file .zshrc định nghĩa REAL_HOME, WORKSPACE_ROOT, HISTFILE="$REAL_HOME/.zsh_history", SHARE_HISTORY, INC_APPEND_HISTORY, và đủ 2 aliases (resume và save-context)
  And mảng sync_items trong hàm ag_run() bao gồm AllProjects, Projects, và .zsh_history
  And mỗi thư mục profile đều có các symlink Projects, AllProjects, và .zsh_history trỏ về thư mục gốc sau khi đã gộp các dòng lịch sử lệnh riêng lẻ

Scenario: [CMM-HP-03] [Tier C - Integration] Định nghĩa Skills, Điểm chạm Dev-Lifecycle và Bộ Kiểm thử Phát hành Toàn diện
  Given hai skills resume-context và save-context đã hoàn thiện, Rule 7 trong CRITICAL_RULES.md, các điểm chạm trong chuỗi skills dev-lifecycle, và đăng ký trong scripts/verify.sh
  When kỹ sư chạy bộ kiểm thử xác minh cho context_memory_management
  Then skills/resume-context/SKILL.md và skills/save-context/SKILL.md vượt qua kiểm tra YAML frontmatter và liên kết tương đối
  And dev-brainstorming, dev-designer, dev-lifecycle, principal-review, dev-implementation, cross-model-review, và finishing-a-development-branch đều chứa các điểm chạm tích hợp resume_context.py bắt buộc
  And scripts/verify.sh thực thi scripts/test_resume_context.py thành công với mã thoát 0
```

## Chiều 2: Trường hợp Biên

```gherkin
Scenario: [CMM-EC-01] [Tier A - Unit] Kiểm soát Giới hạn Tối đa 20 Dòng trên Snapshot Trạng thái Từng Epic
  Given một epic đang hoạt động tên là context-memory được gọi lệnh --state với phần quyết định và ghi chú custom prompt dài quá 25 dòng
  When resume_context.py --state --epic context-memory ghi ra file .devtool/state/context-memory.md
  Then file .devtool/state/context-memory.md được ghi ra có tối đa không quá 20 dòng
  And bảo toàn đầy đủ cả 4 trường bắt buộc (Active Epic, Recent Decisions Locked, Repo/Task Status, Next Immediate Step)

Scenario: [CMM-EC-02] [Tier A - Unit] Định tuyến Nhận biết Worktree từ Bên trong Thư mục .worktrees/<epic_dir>
  Given một git repository có worktree lồng bên trong tại .worktrees/context_memory_management trên nhánh epic/context-memory-management
  When một AI Programmer gọi lệnh resume_context.py --state hoặc --log từ bên trong .worktrees/context_memory_management mà không truyền --repo
  Then engine phân giải đúng thư mục gốc của repository chính thông qua git rev-parse --git-common-dir
  And ghi các file state và log vào thư mục .devtool/ của repository chính thay vì thư mục worktree tạm thời

Scenario: [CMM-EC-03] [Tier A - Unit] Tính toán Tiến độ Kanban Task qua Thư mục Active và Thư mục Done
  Given một repository có 2 tasks trong .devtool/features/ (trạng thái todo và in-progress) và 3 tasks đã hoàn thành trong .devtool/features/done/ (trạng thái done) thuộc epic context-memory-management
  When hàm scan_active_tasks thực thi trong quá trình thu hoạch của resume_context.py
  Then Phần 5 liệt kê các tasks đang ở trạng thái todo và in-progress đồng thời báo cáo tóm tắt tiến độ hoàn thành epic là "3/5 done"
```

## Chiều 3: Chuyển đổi Trạng thái

```gherkin
Scenario: [CMM-ST-01] [Tier C - Integration] Khung Quản trị Ba Vai trò và Xuất Prompt Bàn giao cho 4 Kịch bản
  Given một epic đang hoạt động tên là context-memory-management trong .devtool/
  When resume_context.py được gọi với --role assistant, --role programmer (hoặc bí danh implementer), và --emit-prompt cho principal-review, implement, cross-review, finish, và assistant
  Then --role assistant xuất ra khung "[PERSONA: AI ASSISTANT — TECHNICAL ADVISOR & CO-ARCHITECT]" kèm giới hạn cứng "NO IMPLEMENTATION"
  And --role programmer xuất ra khung "[PERSONA: AI PROGRAMMER — SENIOR TDD SOFTWARE ENGINEER]" bắt buộc tuân thủ TDD, Clean Code và ranh giới Allowed files
  And mỗi chế độ --emit-prompt xuất ra một khối prompt bàn giao hoàn chỉnh chứa persona mục tiêu, lệnh khởi động resume_context.py, và hướng dẫn chuyên biệt cho từng giai đoạn

Scenario: [CMM-ST-02] [Tier A - Unit] Lưu Checkpoint Không Phá hủy qua --complete --checkpoint Kèm Custom Prompt
  Given một epic đang chạy dở tên là context-memory-management đã có các dòng nhật ký trong .devtool/logs/activity_context-memory-management.log
  When kỹ sư hoặc agent chạy lệnh save-context --checkpoint context-memory-management "Locked multi-epic storage model; next write task_01"
  Then .devtool/state/context-memory-management.md và .devtool/logs/activity_context-memory-management.log được cập nhật kèm ghi chú custom prompt
  And .devtool/PROJECT_LEDGER.md không bị thay đổi đồng thời .devtool/logs/activity_context-memory-management.log không bị di chuyển vào .devtool/archive/
```

## Chiều 4: Bất đồng bộ và Đa luồng Đa Agent

```gherkin
Scenario: [CMM-AR-01] [Tier A - Unit] Khóa File Độc quyền Ngăn chặn Ghi Đan xen Giữa Các Agents Song song
  Given 4 tiến trình worker chạy đồng thời cùng gọi resume_context.py --log và --state trên epic-alpha và epic-beta trong cùng một repository
  When cả 4 tiến trình hoàn tất thực thi dưới sự đồng bộ của khóa .devtool/.memory.lock
  Then mọi dòng nhật ký đều được ghi nguyên vẹn không bị hỏng dòng hay mất dữ liệu trong .devtool/logs/activity_epic-alpha.log và .devtool/logs/activity_epic-beta.log
  And .devtool/assistant_state.md chứa đầy đủ bản chụp hợp lệ của cả hai epics

Scenario: [CMM-AR-02] [Tier A - Unit] Gộp Lịch sử Zsh Bất biến Bảo toàn Lệnh mà Không Nhân đôi Symlink
  Given một thư mục profile đã có .zsh_history là symlink trỏ về $REAL_HOME/.zsh_history và một thư mục profile khác có file .zsh_history thông thường chứa 3 lệnh mới
  When hàm sync_shell_env chạy hai lần liên tiếp
  Then 3 lệnh mới chỉ được ghi nối tiếp đúng một lần vào $REAL_HOME/.zsh_history
  And cả hai thư mục profile đều giữ symlink hợp lệ trỏ về $REAL_HOME/.zsh_history với mã thoát 0
```

## Chiều 5: Xử lý Lỗi và Độ bền Lưu trữ

```gherkin
Scenario: [CMM-FR-01] [Tier A - Unit] Tự động Di trú Các File assistant_state.md và activity_stream.log Cấu trúc Cũ
  Given một repository đang có sẵn .devtool/assistant_state.md và .devtool/activity_stream.log theo cấu trúc phẳng cũ nhưng chưa có thư mục .devtool/state/ hay .devtool/logs/
  When resume_context.py chạy thu hoạch ngữ cảnh hoặc ghi một trạng thái epic mới
  Then nội dung cũ được bảo toàn và di trú tự động vào .devtool/state/general.md và .devtool/logs/activity_general.log mà không mất dữ liệu
  And lệnh kết thúc thành công với mã thoát 0

Scenario: [CMM-FR-02] [Tier A - Unit] Xử lý An toàn Khi Thiếu Thư mục Shared Contracts hoặc Thiếu Thư mục .git
  Given một workspace root nơi D3Nexus/shared-contracts chưa tồn tại và một thư mục repository trong danh sách cấu hình chưa có thư mục .git
  When resume_context.py thực thi thu hoạch toàn bộ ngữ cảnh
  Then hàm scan_open_rfcs in ra "(D3Nexus/shared-contracts not initialized yet.)" và hàm scan_git_status bỏ qua thư mục không có .git một cách an toàn
  And lệnh hoàn tất cả 6 phần với mã thoát 0
```

