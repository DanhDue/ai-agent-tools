# Kịch bản BDD — Đồng bộ Trạng thái Runtime, Hybrid Heartbeat và Gia cố Dashboard

## Mục lục

- [Luồng chính](#luồng-chính)
- [Trường hợp biên](#trường-hợp-biên)
- [Chuyển đổi trạng thái và Bất biến](#chuyển-đổi-trạng-thái-và-bất-biến)
- [Bất đồng bộ và Đồng thời](#bất-đồng-bộ-và-đồng-thời)
- [Phục hồi Lỗi](#phục-hồi-lỗi)

## Luồng chính

```gherkin
Scenario: [RSDH-HP-01] [Tier C - Integration] Vỏ trạng thái runtime atomic đồng bộ worktree, repo gốc và Bộ nhớ Hai tầng

Cho một git repository có worktree cô lập đang mở trên nhánh epic "epic/demo-sync" và các task Kanban tương ứng
Khi _state_envelope.update_epic_heartbeat ghi lại bước chuyển task và sync_task_status.py đánh dấu task_01 là "in-progress"
Thì .devtool/state/demo-sync.heartbeat.json được ghi nguyên tử qua os.replace vào cả hai thư mục .devtool/state của worktree và repo gốc
Và cả .devtool/state/demo-sync.md lẫn .devtool/assistant_state.md tự động phản ánh trạng thái task cùng dấu thời gian mà không cần gọi resume_context thủ công

Scenario: [RSDH-HP-02] [Tier A - Unit] Bộ ước lượng heartbeat theo quy tắc ánh xạ workload qua các mức light, medium và heavy

Cho các đầu vào đại diện gồm bản sửa nhỏ 1-task/1-file, một wave tính năng 2-task/5-file, lượt chạy quality profile đầy đủ (`--quality-profile full`), và lượt chạy quality E2E (`--has-e2e`)
Khi scripts/estimate_heartbeat.py đánh giá từng đầu vào qua CLI và Python API với cờ --json
Thì bản sửa nhỏ (estimated_sec 35 < 60) trả tier "light" với recommended_interval_sec null, wave tính năng (estimated_sec 80) trả tier "medium" với recommended_interval_sec 180, lượt quality đầy đủ (estimated_sec 250) trả tier "heavy" với 240, và lượt E2E trả tier "heavy" với 300

Scenario: [RSDH-HP-03] [Tier C - Integration] Trình chạy quality đa ngôn ngữ phát tiến độ 0-token ra stderr và cô lập các lần chạy song song

Cho hai lượt chạy capability của provider đã đăng ký cùng thực thi song song trên một capability qua verify_polyglot_registry.py
Khi cả hai chạy qua Popen với start_new_session=True, khoảng heartbeat rút ngắn cho kiểm thử và dùng chung thư mục .devtool/state
Thì verify_polyglot_registry.py ghi log cô lập tại build/quality/<provider>/runs/<run_id>/<capability>.log không xung đột đồng thời in định kỳ dòng "[quality_check]" ra stderr
Và .devtool/state/quality_active.json tách namespace hai mục dưới runs[run_id] (kèm pid, host, updated_at, ttl_sec) và chỉ chốt xong đúng run_id hoàn thành mà không ghi đè lượt chạy anh em

Scenario: [RSDH-HP-04] [Tier C - Integration] Prompt handoff và template theo wave hướng dẫn thực thi song song và dọn dẹp

Cho một epic đã đóng gói sẵn sàng triển khai Stage 3 trong git worktree cô lập
Khi thực thi resume_context.py --emit-prompt implement --epic demo-sync và render skills/dev-lifecycle/references/handoff-template.md
Thì cả hai đều hướng dẫn programmer orchestrator chạy compute_execution_order.py --parallel, chạy estimate_heartbeat.py mỗi wave và trước Gate 4, thực thi các wave đa task trên slots pool song song, và gọi manage_worker_pool.py cleanup sau đó
Và không bên nào phát chỉ dẫn ép buộc chạy tuần tự từng task một đối với các wave độc lập

Scenario: [RSDH-HP-05] [Tier C - Integration] Worker pool theo dõi trạng thái slot/wave sống và dọn sạch các slot đã tích hợp

Cho một git repository đã khởi tạo 2-slot worker pool (.worktrees/demo_epic-slot-1 và slot-2) được gán qua manage_worker_pool.py sync --task --wave và resume_context.py --wave
Khi quan sát chuyển trạng thái slot sống lúc đang làm và chạy manage_worker_pool.py cleanup --epic-dir demo_epic --epic-slug demo-epic sau khi tích hợp slot
Thì demo-epic.heartbeat.json ban đầu ghi nhận active_wave và slots ("working" kèm task_id) trước lúc dọn dẹp
Và các worktree cùng branch slot sạch đã tích hợp (epic/<slug>-slot-* và worker/<epic>/slot-*) bị xóa và prune, để lại bảng slots rỗng mà không xóa metadata không phải slot của epic

Scenario: [RSDH-HP-06] [Tier C - Integration] Chuyển đổi PIC đồng bộ các tệp chứa PIC giữa repo gốc và worktree mà vẫn giữ nguyên review/BDD prose

Cho một repository có tài liệu epic tại cả .devtool/epic/demo_epic/ của repo gốc và worktree .worktrees/demo_epic/, gồm handoff.md ("- **PIC / Assigned Profile**: ..."), HLD, task_*.md, bdd_scenarios.en.md, và principal_review.md
Khi tasks_server.py assign_epic_pic cập nhật PIC epic từ "mommy" sang "brother"
Thì HLD, handoff.md, task_*.md (dưới epic và features), tệp JSON pipeline/heartbeat ở cả repo gốc và worktree, cùng .vscode/settings.json của worktree đều cập nhật thành "brother"
Và bdd_scenarios.en.md cùng principal_review.md giữ nguyên từng byte mà không bị chèn dòng PIC

Scenario: [RSDH-HP-07] [Tier C - Integration] Tasks dashboard áp đặt trần 96% trước Finish và làm mới live Phần II khi state đổi

Cho tasks_dashboard.html nạp payload repo chứa epic in_progress đã hoàn thành 5/5 tasks nhưng chưa hội tụ Gate 4
Khi pollDashboard nhận payload mới cập nhật account_id, task_progress, prompt, wave đang chạy trên heartbeat hoặc trạng thái running của quality_active
Thì cả sidebar Phần I và card thực thi Phần II hiển thị 96% ("96% Review") thay vì 99%
Và tier2Sig phát hiện thay đổi để render lại Phần II kèm thanh tiến độ wave/quality sống mà không cần tải lại trang

Scenario: [RSDH-HP-08] [Tier C - Integration] Modal Stack Controller của Check-Quota giữ tối đa một modal con và reset iframe thật

Cho quota_dashboard.html chạy bên trong iframe thật của #modal-quota qua HTTP TasksServer trên headless Chrome CDP được cấp phát
Khi người dùng mở #scheduleModal rồi kích hoạt #loginModal, sau đó cửa sổ cha đóng #modal-quota
Thì mở #loginModal tự động đóng #scheduleModal sao cho tại một thời điểm tối đa chỉ có một modal con ở trạng thái mở
Và đóng #modal-quota gửi {action: "reset_quota_submodals"} qua ranh giới iframe thật khiến quota_dashboard.html đóng sạch mọi modal con

Scenario: [RSDH-HP-09] [Tier C - Integration] Điều phối đầu-cuối, đồng bộ vỏ runtime, dashboard 96%, đồng bộ PIC và modal stack Chrome CDP vượt qua cùng nhau

Cho workspace đa worktree đang chạy endpoint HTTP TasksServer sống với các cập nhật Wave 1-3 đã áp dụng
Khi một epic đi qua sync_task_status, tiến độ verify_polyglot_registry, lưu/xóa pending-decision Choice A, chuyển PIC trên repo gốc + worktree, và tương tác parent/iframe trên Chrome CDP thật
Thì /api/tasks live phản ánh tiến độ 96% trước Finish, PIC đã cập nhật, điểm nghẽn đã gỡ, và giao diện trình duyệt thật vượt qua không có lỗi console hay runtime
```

## Trường hợp biên

```gherkin
Scenario: [RSDH-EC-01] [Tier A - Unit] Trình đọc vỏ trạng thái chịu đựng file JSON thiếu, rỗng hoặc bị cắt cụt

Cho các file không tồn tại, 0 byte và JSON bị cắt cụt lỗi tại .devtool/state/broken.heartbeat.json
Khi _state_envelope.read_json_safe đọc từng đường dẫn cùng dictionary mặc định
Thì read_json_safe trả về an toàn dictionary mặc định mà không ném JSONDecodeError hay OSError

Scenario: [RSDH-EC-02] [Tier A - Unit] Bộ ước lượng heartbeat ghim đầu vào bằng không và nâng lượt E2E lên 300 giây

Cho một lần gọi scripts/estimate_heartbeat.py với --tasks-count 0 --files-count 0 và một lần khác với --quality-profile epic --has-e2e
Khi cả hai đánh giá được thực thi
Thì đầu vào rỗng cho tier "light" với recommended_interval_sec null
Và lượt E2E của epic cho tier "heavy" với recommended_interval_sec 300

Scenario: [RSDH-EC-03] [Tier C - Integration] package_epic --revise Stage 3 chấp nhận file (new) của in-progress/done nhưng chặn va chạm trên todo

Cho epic Stage 3 có task_01 là "done" và task_02 là "in-progress" tham chiếu tới các tệp "(new)" đã tạo trước, cùng epic Stage 2 chưa bắt đầu và bản chỉnh sửa Stage 3 thêm task "todo" khai báo tệp "(new)" đã tồn tại
Khi chạy package_epic.py --revise trên epic Stage 3 đang mở và chạy check_epic_readiness.py trên epic Stage 2 cùng epic todo va chạm
Thì lượt chỉnh sửa Stage 3 chấp nhận các tệp "(new)" thuộc quyền sở hữu của task done/review/in-progress và thoát mã 0
Và kiểm tra readiness Stage 2 cùng khai báo "(new)" va chạm ở task todo mới hoặc khai báo "(new)" trùng lặp thoát mã khác 0

Scenario: [RSDH-EC-04] [Tier A - Unit] Check-Tasks harvester giữ nguyên trạng thái Idle khi repo rỗi không có worktree hoặc task đang chạy

Cho một git repository chứa các thư mục chưa bắt đầu cũ dưới .devtool/epic/ (gồm choosing_a_lifecycle) với 0 worktree, 0 task trong features/ và không có pending_decision.json
Khi check_tasks.resolve_active_epic và check_tasks.derive_lifecycle_state đánh giá repository đó
Thì resolve_active_epic trả về None và derive_lifecycle_state trả Idle với is_human_action_required là False

Scenario: [RSDH-EC-05] [Tier A - Unit] Chuyển PIC kiểm tra tên profile hợp lệ và cô lập các epic anh em qua worktree

Cho một repository chứa hai epic riêng biệt (demo_epic và sibling_epic) có thư mục và worktree tách biệt sau endpoint HTTP TasksServer sống
Khi gọi trực tiếp tasks_server.assign_epic_pic và qua POST /api/epic/pic với PIC sai định dạng "../bad", sau đó gọi với PIC hợp lệ "tess" cho "demo_epic"
Thì lời gọi trực tiếp assign_epic_pic ném ValueError không sửa bất kỳ file nào và POST /api/epic/pic trả HTTP 400 kèm {"status": "error", ...} thay vì HTTP 500
Và cập nhật hợp lệ chỉ sửa demo_epic trên repo gốc lẫn worktree khớp mà giữ nguyên toàn bộ tệp của sibling_epic

Scenario: [RSDH-EC-06] [Tier C - Integration] Bảng Roadmap bỏ sắp xếp theo mtime dưới 1 ngày và giữ focus select gốc trên Chrome CDP

Cho tasks_dashboard.html chạy qua HTTP trên Chrome CDP không giao diện thật với hai epic cùng ngày có mtime khác nhau và thay đổi khi sửa PIC, khi người dùng đang focus .select-pic-roadmap mang data-row-key
Khi pollDashboard chu kỳ 5s giao về payload làm nhích mtime trong ngày của epic thứ hai trong lúc .select-pic-roadmap giữ document.activeElement, và updateEpicPic hoàn tất khi #modal-epics có computed style display === "flex"
Thì sortEpicsForRoadmap bỏ qua sai khác mtime trong cùng ngày nên hàng không bị đảo thứ tự và pollDashboard hoãn thay DOM cho đến khi blur
Và updateEpicPic nhận diện hiển thị #modal-epics qua style.display === "flex" để làm mới các hàng modal sạch mà không mất lựa chọn

Scenario: [RSDH-EC-07] [Tier C - Integration] Click backdrop con và phím Escape trong Check-Quota chỉ đóng đúng dialog con đang mở

Cho #modal-quota đang mở và bên trong quota_dashboard.html có một trong các dialog #profileInfoModal, #appealDetailModal, #scheduleModal hoặc #loginModal đang mở
Khi người dùng click vào backdrop của sub-modal hoặc nhấn phím Escape bên trong iframe
Thì chỉ có inner sub-modal đang mở bị đóng lại, bảo toàn phần còn lại của #dashboardCard và giữ #modal-quota mở

Scenario: [RSDH-EC-08] [Tier C - Integration] Profile tạo epic được tự động nhận diện và đóng dấu làm PIC ban đầu

Cho môi trường profile Antigravity đang bật AGY_PROFILE (hoặc thư mục profile /antigravity_homes/brother) chạy cùng HLD chứa "- **PIC**: brother" và workspace slug có trộn dấu "-" và "_"
Khi chạy resume_context.py --detect-profile, sync_window_title và package_epic.py sinh handoff.md từ handoff-template.md
Thì --detect-profile in ra "brother" ưu tiên tên thư mục profile hơn tiền tố email, sync_window_title ghi "[@brother]" vào .vscode/settings.json không lỗi trước sai khác "-" so với "_", và handoff.md sinh ra đóng dấu "- **PIC / Assigned Profile**: @brother" thay vì "<profile_account_id>"
```

## Chuyển đổi trạng thái và Bất biến

```gherkin
Scenario: [RSDH-ST-01] [Tier C - Integration] Cờ pending_decision theo namespace đánh dấu dừng từng epic và yêu cầu khớp sở hữu khi gỡ

Cho hai epic song song (epic-a và epic-b) đều dừng sạch qua resume_context.py --pending-decision với hai decision_id khác nhau
Khi sync_task_status.py đánh dấu một task ở epic-b là "in-progress" (hoặc --gate 2 / --clear-decision xóa epic-b) lúc check_tasks.scan_repo quét cả hai epic
Thì pending_decision.json lưu tách biệt các mục decisions[epic] nên việc tiếp tục epic-b CHỈ xóa epic-b trong khi epic-a vẫn giữ pending decision và is_human_action_required là True
Và xóa chính decision của epic-a trên repo gốc cùng worktree chuyển is_human_action_required của epic-a về False sạch sẽ

Scenario: [RSDH-ST-02] [Tier C - Integration] Hợp nhất Gate ledger trộn các mục JSONL và GATE_LEDGER.md của repo gốc và worktree

Cho repository có gate_ledger.jsonl cũ chỉ ghi Gate 1 trong khi GATE_LEDGER.md của worktree hoạt động (hoặc repo gốc) chứa các phê duyệt Gate 2 và Gate 3 mới hơn
Khi check_tasks.parse_gate_ledger_entries kiểm tra repository
Thì toàn bộ Gates 1, 2 và 3 đều được trả về đầy đủ mà không dừng sớm tại gate_ledger.jsonl

Scenario: [RSDH-ST-03] [Tier C - Integration] Tỉa worker pool lỗi thời và quá trình land nhánh dọn dẹp tài nguyên slot mồ côi an toàn

Cho repository có thư mục slot-1 bị xóa thủ công khỏi đĩa trong khi metadata admin git worktree và nhánh slot vẫn tồn tại, cùng một epic sẵn sàng chạy integrate_branch.py land
Khi manage_worker_pool.py cleanup --stale-only và integrate_branch.py cmd_land thực thi
Thì git worktree prune và dọn branch xóa sạch metadata/nhánh slot mồ côi mà không lỗi trước thư mục thiếu

Scenario: [RSDH-ST-04] [Tier A - Unit] extract_epic_pic phân giải sạch PIC qua các placeholder tại repo gốc và worktree handoff

Cho epic đang chạy có HLD ở repo gốc chưa ghi PIC nhưng handoff.md trong worktree lại ghi "- **PIC / Assigned Profile**: @danhdue" (hoặc "<unassigned>")
Khi check_tasks.extract_epic_pic kiểm tra repository
Thì PIC hợp lệ ở worktree "danhdue" được trích xuất sạch và các placeholder như "<unassigned>" trả về None

Scenario: [RSDH-ST-05] [Tier C - Integration] Tính tiến độ thực thi đúng mức 75% giữa epic, trần 95% khi chạy, trần 96% trước Finish và 100% khi hoàn tất

Cho số lượng task chuyển từ 3/4 done, 4/4 done trước hội tụ Gate 4, 4/4 done kèm Gate 4 Review Converged (Waiting Finish), và Gate 5 Done
Khi backend check_tasks và tasks_dashboard.html tính giá trị hiển thị tiến độ
Thì 3/4 done cho 75% (tỉ lệ đang chạy cao bị chặn ở 95%), 4/4 done trước hội tụ cho đúng 96%, và trạng thái Waiting Finish đã hội tụ / Done cho 100%

Scenario: [RSDH-ST-06] [Tier C - Integration] Chế độ nhúng Check-Quota gỡ bỏ khung thẻ ngoài dư thừa bên trong iframe Chrome thật

Cho quota_dashboard.html được nạp kèm "?embedded=1" trong thẻ iframe thật so với URL độc lập trên headless Chrome CDP được cấp phát
Khi window.getComputedStyle đánh giá border, boxShadow, margin và padding của #dashboardCard giữa chế độ độc lập và nhúng
Thì chế độ nhúng làm phẳng lề, viền và đổ bóng ngoài sạch sẽ trong khi chế độ độc lập giữ nguyên khung thẻ đầy đủ

Scenario: [RSDH-ST-07] [Tier C - Integration] Cleanup worker pool bảo toàn worktree bẩn, commit chưa merge và branch chưa merge bị thiếu worktree

Cho repository có slot-1 chứa thay đổi bẩn chưa commit, slot-2 có commit chưa merge với thư mục worktree đã xóa trên đĩa, và slot-3 sạch đã merge vào epic/demo-epic
Khi manage_worker_pool.py cleanup chạy ở chế độ an toàn mặc định so với cờ tường minh --discard-unmerged
Thì chế độ mặc định chỉ xóa slot-3 sạch đã merge trong khi giữ lại worktree slot-1, giữ nguyên branch mồ côi chưa merge của slot-2, báo cáo rõ tài nguyên được bảo toàn và ghi nhận trạng thái bảo toàn thay vì xóa âm thầm
Và truyền --discard-unmerged sẽ xóa sạch mọi slot và branch tạm được nhắm tới khi việc hủy bỏ được yêu cầu tường minh
```

## Bất đồng bộ và Đồng thời

```gherkin
Scenario: [RSDH-AR-01] [Tier C - Integration] Khóa giao dịch chuẩn tuần tự hóa cập nhật RMW đan xen trên slot và bản sao phiên bản hóa

Cho nhiều worker song song thực hiện đọc-sửa-ghi slot đan xen trên các mục tiêu .devtool/state/ dùng chung giữa repo gốc và worktree hoạt động
Khi 16 lượt cập nhật song song chạy dưới khóa giao dịch fcntl.flock chuẩn tại repo gốc của _state_envelope.py
Thì không có cập nhật slot nào bị rơi qua các chu kỳ RMW đồng thời và bản sao repo gốc cùng worktree mang số generation và JSON payload giống hệt nhau

Scenario: [RSDH-AR-02] [Tier C - Integration] Polling live áp dụng cập nhật Tầng 2 ngay lập tức mà không đè control đang focus hay sinh lỗi console

Cho tasks_dashboard.html nhận các snapshot pollDashboard định kỳ có wave heartbeat thay đổi, trạng thái quality_active và lựa chọn PIC
Khi các chu kỳ poll chạy cả trong lúc .select-pic-roadmap đang focus lẫn sau khi blur
Thì Phần II cập nhật ngay khi focus ổn định, các select đang focus không bao giờ mất lựa chọn người dùng, và không có lỗi console nào phát sinh

Scenario: [RSDH-AR-03] [Tier C - Integration] Check-tasks harvester cô lập quyết định đa epic, hiển thị quality_runs live và hết hạn tiến trình chết

Cho quality_active.json chứa một run đang chạy sống, một mục running quá hạn TTL/PID đã chết, kèm pending_decision.json với nhiều quyết định epic theo namespace
Khi check_tasks.scan_repo kiểm tra repository
Thì các run quá hạn/PID chết chuyển sang trạng thái "stale" mà không render banner đang chạy vĩnh viễn, các run song song sống lộ diện qua quality_runs, và active_epic chỉ phân giải đúng pending_decision theo namespace của nó
```

## Phục hồi Lỗi

```gherkin
Scenario: [RSDH-FR-01] [Tier C - Integration] Metadata heartbeat cũ không bao giờ chặn các lượt đồng bộ trạng thái task tiếp theo

Cho một file heartbeat.json cũ tham chiếu tới wave trước bị hủy và thư mục slot đã thiếu
Khi sync_task_status.py hoặc resume_context.py ghi chuyển đổi trạng thái mới
Thì heartbeat cũ được thay thế nguyên tử an toàn dưới khóa và quá trình thực thi tiếp tục sạch sẽ

Scenario: [RSDH-FR-02] [Tier C - Integration] Kiểm tra chất lượng chốt run_id thất bại mà không ghi đè các lượt chạy song song

Cho một lệnh capability bị lỗi trong verify_polyglot_registry.py chạy song song với một run_id khỏe mạnh độc lập trong quality_active.json
Khi lệnh lỗi thoát mã khác 0
Thì chỉ có runs[run_id] của chính nó chuyển sang trạng thái "failed" với finished_at khác null trong khi các run sống anh em giữ nguyên vẹn

Scenario: [RSDH-FR-03] [Tier C - Integration] Quy tắc Choice A và cleanup mới vẫn giữ CRITICAL_RULES.md trong trần 8192 bytes

Cho các chỉnh sửa bổ sung quy trình quản trị Choice A pending-decision và dọn dẹp worker-pool trên rules/CRITICAL_RULES.md và các tệp Stage 1-4 SKILL.md
Khi kiểm tra kích thước byte UTF-8 của rules/CRITICAL_RULES.md và các mục §1-§10 của scripts/verify.sh
Thì rules/CRITICAL_RULES.md vẫn nằm chặt <= 8192 UTF-8 bytes và mọi kiểm tra liên kết tĩnh, Mục lục, frontmatter, và tham chiếu mồ côi đều đạt

Scenario: [RSDH-FR-04] [Tier C - Integration] Lỗi chỉ-đọc một phần khi chuyển PIC báo cáo cảnh báo mà không làm hỏng các tệp anh em

Cho một epic chứa cả các tệp siêu dữ liệu ghi được lẫn một đường dẫn giả lập không ghi được hoặc file state tùy chọn bị thiếu lúc gán PIC
Khi tasks_server.assign_epic_pic thực thi
Thì các tệp đích ghi được vẫn cập nhật sạch sẽ, warnings chỉ rõ đường dẫn lỗi, và phản hồi JSON phản ánh đúng số lượng updated_files

Scenario: [RSDH-FR-05] [Tier C - Integration] Nhấn phím Escape khi không có modal con quota nào mở sẽ đóng sạch qua handleCardClose

Cho quota_dashboard.html với cả bốn modal con đang đóng bên trong #modal-quota
Khi người dùng nhấn phím Escape
Thì bộ xử lý phím thấy 0 modal con đang mở và gọi sạch handleCardClose mà không phát sinh lỗi runtime

Scenario: [RSDH-FR-06] [Tier C - Integration] Các suite kiểm chứng đã đăng ký bảo vệ liên tục ngân sách byte, báo giả idle và cô lập snapshot

Cho scripts/verify.sh với đầy đủ các suite của epic đã đăng ký trong SUITES và các tệp kit hiện có trên đĩa
Khi chạy bash scripts/verify.sh --quiet và các bài test hồi quy kiểm tra CRITICAL_RULES.md, dev-designer/SKILL.md và dashboard scripts
Thì CRITICAL_RULES.md giữ nguyên <= 8192 bytes, dev-designer/SKILL.md giữ nguyên <= 22528 bytes, không tồn tại fallback theo chữ cái khi idle, và toàn bộ mục kiểm chứng đã đăng ký thoát mã 0

Scenario: [RSDH-FR-07] [Tier C - Integration] Quality check bị ngắt bởi tín hiệu sẽ thu hồi tiến trình con và phục hồi các run quá hạn

Cho một nhóm tiến trình con capability đang chạy dưới verify_polyglot_registry.py cùng một lượt chạy khỏe mạnh độc lập khác
Khi SIGTERM ngắt tiến trình verify_polyglot_registry.py thứ nhất
Thì bộ xử lý tín hiệu chấm dứt và thu hồi sạch nhóm tiến trình con đang chạy, đồng thời chỉ chuyển riêng runs[run_id] của nó sang "aborted" trong khi giữ nguyên run song song
```

<!-- sync-en-sha256: 7a70b9d2b1a414cb -->
