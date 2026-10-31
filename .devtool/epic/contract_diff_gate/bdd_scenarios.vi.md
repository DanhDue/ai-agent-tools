# Kịch Bản BDD Cho Contract Diff Gate

## Mục lục

- [Chiều 1: Tuyến thực thi thành công](#chiều-1-tuyến-thực-thi-thành-công)
- [Chiều 2: Trường hợp biên và ranh giới](#chiều-2-trường-hợp-biên-và-ranh-giới)
- [Chiều 3: Chuyển đổi trạng thái](#chiều-3-chuyển-đổi-trạng-thái)
- [Chiều 4: Bất đồng bộ và đồng thời đa repo](#chiều-4-bất-đồng-bộ-và-đồng-thời-đa-repo)
- [Chiều 5: Lỗi và khả năng phục hồi lưu trữ](#chiều-5-lỗi-và-khả-năng-phục-hồi-lưu-trữ)

## Chiều 1: Tuyến thực thi thành công

```gherkin
Scenario: [CDG-HP-01] [Tier C - Integration] Thay đổi file được map trên Hub được bao phủ bởi cập nhật file Contract chuẩn
  Given một Hub repository đã khởi tạo trên nhánh develop có file .agents/contract_map.json ánh xạ "crates/**/routes/**" và "crates/**/dto/**" (loại trừ "**/tests/**") vào domain "lyrics-sync"
  When một nhánh tính năng đã commit sửa đổi "crates/api/routes/worker.rs" cùng "shared-contracts/lyrics-sync/api_contract.md" trên cây làm việc sạch
  And kỹ sư thực thi lệnh sync_contracts.py diff-check --base-ref develop --json
  Then báo cáo JSON chứa status "PASS", mode "hub", violations [], và blockers []
  And lệnh kết thúc với exit code 0

Scenario: [CDG-HP-02] [Tier C - Integration] Thay đổi file được map trên Satellite được bao phủ bởi Domain Ack mới khớp Snapshot hiện hành
  Given một Satellite repository liên kết qua relative symlink shared-contracts tới ../Hub/shared-contracts/lyrics-sync có file .agents/contract_map.json ánh xạ "src/api/dto/**" vào domain "lyrics-sync"
  When một nhánh tính năng đã commit sửa đổi "src/api/dto/worker.py" và cập nhật domains["lyrics-sync"] trong .agents/contract_sync.json qua lệnh sync_contracts.py ack --snapshot <live_snapshot_id> --all-rfcs
  And kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then diff-check xác nhận domains["lyrics-sync"].snapshot_id tại HEAD bằng đúng snapshot_id hiện hành tính từ shared-contracts
  And báo cáo JSON chứa status "PASS", mode "satellite", và violations []
  And lệnh kết thúc với exit code 0

Scenario: [CDG-HP-03] [Tier C - Integration] Xác minh Schema của 5 Quality Providers, Placeholders và Ánh xạ mã thoát 2
  Given các file *-quality.schema.json và tài liệu SKILL.md đã cập nhật trên cả năm quality providers gồm rust, python, flutter, android, và ios
  When kỹ sư chạy cả năm bộ kiểm thử test_validate_*_quality.py
  Then mọi schema provider cho phép các capabilities "contracts", "contract_diff", cùng biểu thức "^contracts_[a-z0-9_]+$" (và rust-quality.schema.json cho phép thêm "db_hygiene")
  And mọi validator chấp nhận mảng lệnh chứa placeholder "{skills_dir}" cùng "{base_ref}" và tài liệu hóa quy tắc ánh xạ exit code 2 sang trạng thái "BLOCKED"
  And cả năm bộ kiểm thử validator đều kết thúc với exit code 0

Scenario: [CDG-HP-04] [Tier C - Integration] Xác minh Ràng buộc Tài liệu Lifecycle, Template Mẫu và Bộ kiểm tra Verify Harness
  Given file mẫu contract_map.json.tmpl trong setup-shared-contracts cùng các file SKILL.md đã cập nhật tại setup-shared-contracts, sync-shared-contracts, dev-brainstorming, và dev-designer
  When kỹ sư thực thi scripts/test_lifecycle_document_contract.py và scripts/verify.sh
  Then dev-brainstorming thực thi quy tắc chỉ đọc check/brief để cảnh báo, bắt buộc con người xác nhận từng cảnh báo, và lưu mục song ngữ "## Shared Contract Warnings" / "## Cảnh báo Shared Contract"
  And dev-designer thực thi việc đọc "## Shared Contract Warnings", giữ thứ tự Contract-First ở task_01 của Hub, và khai báo .agents/contract_sync.json cùng .agents/contract_map.json trong Allowed files của task cuối
  And setup-shared-contracts tài liệu hóa contract_map.json.tmpl và scripts/verify.sh kết thúc với exit code 0
```

## Chiều 2: Trường hợp biên và ranh giới

```gherkin
Scenario: [CDG-EC-01] [Tier A - Unit] Khớp Glob POSIX đa tầng có neo và thứ tự ưu tiên Exclude
  Given file .agents/contract_map.json cấu hình domain "lyrics-sync" với paths ["crates/**/routes/**", "src/*/dto/*.py"] và exclude ["**/tests/**"]
  When bộ khớp glob POSIX có neo đánh giá "crates/routes/v1.rs", "crates/core/http/routes/v1/tasks.rs", "src/worker/dto/job.py", "crates/api/routes/tests/mock.rs", và "other/crates/routes/v1.rs"
  Then "crates/routes/v1.rs", "crates/core/http/routes/v1/tasks.rs", và "src/worker/dto/job.py" khớp với domain "lyrics-sync"
  And đường dẫn bị loại trừ "crates/api/routes/tests/mock.rs" cùng đường dẫn sai tiền tố gốc "other/crates/routes/v1.rs" không khớp với domain "lyrics-sync"

Scenario: [CDG-EC-02] [Tier A - Unit] Diff rỗng tại Merge-Base hoặc chỉ thay đổi file ngoài Map đều vượt qua kiểm tra
  Given một Hub hoặc Satellite repository đã khởi tạo có .agents/contract_map.json trong đó merge-base(base_ref, HEAD) bằng đúng HEAD hoặc các commit trong M..HEAD chỉ sửa file "README.md"
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then báo cáo JSON chứa status "PASS", violations [], và active_waivers []
  And lệnh kết thúc với exit code 0

Scenario: [CDG-EC-03] [Tier A - Unit] Thứ tự ưu tiên ghi đè Base-Ref từ CLI và kiểm tra bộ lọc lặp Domain
  Given file .agents/contract_map.json khai báo base_ref "main" cùng hai domain "lyrics-sync" và "nexus" trong đó "nexus" có thay đổi file chưa bao phủ so với nhánh "develop" còn "lyrics-sync" không có file thay đổi
  When kỹ sư chạy lệnh sync_contracts.py diff-check --base-ref develop --domain lyrics-sync sau đó chạy tiếp sync_contracts.py diff-check --domain nonexistent_domain
  Then lệnh thứ nhất đánh giá khoảng diff merge-base(develop, HEAD)..HEAD giới hạn cho "lyrics-sync" và kết thúc với exit code 0
  And lệnh thứ hai ghi nhận lỗi domain không xác định "nonexistent_domain" trong blockers và kết thúc với exit code 2

Scenario: [CDG-EC-04] [Tier C - Integration] Waiver mới theo đường dẫn với Gap rỗng hoặc GAP-XX có thật vượt qua kiểm tra kèm báo cáo Kiểm toán
  Given một repository có commit trong M..HEAD sửa file được map "src/routes/tts.py" không kèm sửa contract hay ack nhưng thêm mới waiver "W-001" cho domain "lyrics-sync" khớp ["src/routes/tts.py"] với gap null hoặc gap "GAP-08" có mặt trong gaps_and_rfcs.md
  When kỹ sư thực thi sync_contracts.py diff-check --json và sync_contracts.py diff-check
  Then cả hai lệnh đều kết thúc với exit code 0
  And trường active_waivers trong JSON lẫn văn bản stdout đều in rõ id "W-001", domain "lyrics-sync", paths ["src/routes/tts.py"], reason, và giá trị gap để duyệt tại Gate 4 và Gate 5
```

## Chiều 3: Chuyển đổi trạng thái

```gherkin
Scenario: [CDG-ST-01] [Tier C - Integration] Thay đổi file được map chưa bao phủ và Waiver một phần chuyển kết luận sang FAIL
  Given một Hub repository có commit trong M..HEAD sửa hai file được map "crates/a/routes/x.rs" và "crates/a/dto/y.rs" mà không sửa shared-contracts/lyrics-sync/ và chỉ thêm waiver mới "W-010" bao phủ ["crates/a/routes/x.rs"]
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then báo cáo JSON chuyển sang status "FAIL" và liệt kê "crates/a/dto/y.rs" thuộc domain "lyrics-sync" trong violations trong khi không báo lỗi file đã bao phủ "crates/a/routes/x.rs"
  And lệnh kết thúc với exit code 1

Scenario: [CDG-ST-02] [Tier C - Integration] Waiver lịch sử không che thay đổi mới, từ chối sửa đổi Waiver cũ và cho phép xóa Waiver hết hạn
  Given một repository có file .agents/contract_map.json tại merge-base M đã chứa sẵn waiver "W-OLD" cho domain "lyrics-sync" và đường dẫn ["crates/a/routes/x.rs"]
  When nhánh A sửa file "crates/a/routes/x.rs" và giữ nguyên "W-OLD", nhánh B sửa đổi trường paths hoặc reason của "W-OLD" tại HEAD, và nhánh C xóa bỏ "W-OLD" khi không có thay đổi file chưa bao phủ
  Then lệnh sync_contracts.py diff-check trên nhánh A kết thúc với exit code 1 báo "crates/a/routes/x.rs" chưa được bao phủ do "W-OLD" không phải waiver mới thêm trong M..HEAD
  And lệnh sync_contracts.py diff-check trên nhánh B kết thúc với exit code 1 báo lỗi sửa đổi trái phép waiver lịch sử "W-OLD"
  And lệnh sync_contracts.py diff-check trên nhánh C kết thúc với exit code 0

Scenario: [CDG-ST-03] [Tier C - Integration] Cô lập Ack khác Domain trên Satellite, từ chối Snapshot cũ và báo lỗi thiếu GAP-XX
  Given một Satellite repository có thay đổi file được map thuộc domain "lyrics-sync" trong đó hoặc .agents/contract_sync.json trong M..HEAD chỉ cập nhật domain lân cận "nexus", hoặc domains["lyrics-sync"].snapshot_id tại HEAD khác với snapshot_id hiện hành trên Hub, hoặc waiver mới trích dẫn gap "GAP-999" không có trong gaps_and_rfcs.md
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then báo cáo JSON chứa status "FAIL" và ghi nhận rõ đường dẫn vi phạm hoặc lỗi thiếu "GAP-999"
  And lệnh kết thúc với exit code 1
```

## Chiều 4: Bất đồng bộ và đồng thời đa repo

```gherkin
Scenario: [CDG-AR-01] [Tier C - Integration] Phân giải Symlink bên trong Epic Worktree lồng nhau khi chạy Satellite Diff-Check
  Given một Satellite repository có symlink gốc shared-contracts trỏ tương đối tới ../Hub/shared-contracts/lyrics-sync và một git worktree cô lập tại .worktrees/cdg_epic chứa commit sửa file được map kèm domain ack mới
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --repo-root .worktrees/cdg_epic --json
  Then diff-check phân giải outbound relative symlink thông qua thư mục gốc của repo chính mà không làm thay đổi file tracked trong .worktrees/cdg_epic
  And xuất kết quả status "PASS", mode "satellite", và kết thúc với exit code 0

Scenario: [CDG-AR-02] [Tier A - Unit] Cây làm việc có file Tracked bẩn dừng an toàn với mã thoát 2
  Given một Hub hoặc Satellite repository đang có chỉnh sửa unstaged hoặc staged trên file tracked trong khi vẫn có các file build untracked dưới thư mục build/
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then diff-check kiểm tra git status --porcelain --untracked-files=no, xuất status "BLOCKED" kèm thông báo cây làm việc bẩn trong blockers, và kết thúc với exit code 2
```

## Chiều 5: Lỗi và khả năng phục hồi lưu trữ

```gherkin
Scenario: [CDG-FR-01] [Tier A - Unit] Thiếu hoặc lỗi định dạng Contract Map tại HEAD hoặc Merge-Base dừng an toàn với BLOCKED
  Given một repository thiếu file .agents/contract_map.json tại HEAD, vi phạm schema_version 1 tại HEAD (domains rỗng, trùng id waiver, hoặc domain của waiver không tồn tại), hoặc chứa JSON hỏng cú pháp tại merge-base M
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then báo cáo JSON chứa status "BLOCKED" kèm chẩn đoán chi tiết trong blockers nêu rõ file bị thiếu hoặc lỗi schema
  And lệnh kết thúc với exit code 2

Scenario: [CDG-FR-02] [Tier A - Unit] Không phân giải được Base-Ref hoặc hỏng Topology Shared-Contracts dừng an toàn với BLOCKED
  Given một repository mà effective_base_ref không phân giải được sang commit git hoặc đường dẫn shared-contracts bị thiếu, đứt symlink, hay rơi vào vòng lặp symlink 12 bước nhảy
  When kỹ sư thực thi lệnh sync_contracts.py diff-check --json
  Then báo cáo JSON chứa status "BLOCKED" và ghi nhận lỗi git merge-base hoặc lỗi topology vào blockers
  And lệnh kết thúc với exit code 2
```

