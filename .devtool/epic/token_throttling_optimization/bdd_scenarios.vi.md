# Kịch Bản BDD Tối Ưu Hóa Tiêu Hao Token

## Mục lục

- [Thông tin Meta](#thông-tin-meta)
- [Luồng chính](#luồng-chính)
- [Trường hợp biên và ranh giới](#trường-hợp-biên-và-ranh-giới)
- [Chuyển đổi trạng thái và bất biến](#chuyển-đổi-trạng-thái-và-bất-biến)
- [Bất đồng bộ và đồng thời](#bất-đồng-bộ-và-đồng-thời)
- [Xử lý lỗi và khả năng phục hồi](#xử-lý-lỗi-và-khả-năng-phục-hồi)

## Thông tin Meta

- **Epic**: `token_throttling_optimization`
- **Ngôn ngữ gốc**: Tiếng Anh
- **Tiền tố kịch bản**: `TTO`
- **Thư mục tự động hóa**: `tests`
- **Quy tắc**: Mỗi mã kịch bản được gán cho đúng một task và xuất hiện trong một bài kiểm thử tự động.
- **Giả lập (Mocking)**: Các CLI con (`claude`, `codex`, `kiro`, `agy`, `pytest`, `git`) và thao tác ghi đĩa được cô lập hoàn toàn trong thư mục tạm (`tmp_path` / `tempfile.TemporaryDirectory`) với binary giả trên `PATH`.

## Luồng chính

```gherkin
Scenario: [TTO-HP-01] [Tier C - Integration] Review ngoài chỉ dùng diff -U5 ở Round 1 và bỏ qua diff base đầy đủ ở Round 2

Cho một git repository cô lập có epic chứa nhiều commit mã nguồn cùng tài liệu đồng hành .vi.md
Và một mục Round 1 đã được ghi nhận sẵn trong review_results.md cho SHA trước đó
Khi run_external_review.py dựng prompt Round 1 rồi dựng tiếp prompt Round 2 sau một commit sửa lỗi gia tăng
Thì phần diff Round 1 được tạo với ngữ cảnh -U5 và loại bỏ toàn bộ đường dẫn tài liệu *.vi.md
Và prompt Round 2 chứa delta_round_context cho khoảng prev_sha..curr_sha kèm tham chiếu một dòng cumulative diff --stat
Và prompt Round 2 không đính kèm khối diff base...curr_sha đầy đủ trừ khi truyền cờ --full

Scenario: [TTO-HP-02] [Tier C - Integration] Trình chạy Gate 4 rút gọn chỉ in một dòng GATE_PASS và lưu log đầy đủ vào build/quality

Cho một dự án có tệp .agents/quality/check_quality.json hợp lệ với các provider thoát bằng mã 0
Khi verify_polyglot_registry.py chạy kèm cờ --compact
Thì đầu ra chuẩn chỉ in các dòng đơn "GATE_PASS: <provider_or_cap>" thay cho các khối JSON dài dòng
Và toàn bộ log chi tiết của từng capability được ghi vào build/quality/<provider>/<cap>.log
Và kết quả tổng hợp cuối cùng trả về PASS

Scenario: [TTO-HP-03] [Tier C - Integration] Kiểm tra sẵn sàng mặc định Option A chấp nhận sai lệch tạm thời của .vi.md và hoãn bdd_scenarios.vi.md

Cho một thư mục epic có đầy đủ tài liệu thiết kế *.en.md mới nhất và bdd_scenarios.en.md
Và chưa tồn tại bdd_scenarios.vi.md trong khi một bản .vi.md đồng hành chưa đồng bộ trong lúc Principal Review
Khi check_epic_readiness.py chạy mà không có cờ --strict-bilingual
Thì cổng sẵn sàng trả về PASS trên R1, R3, R7 và không báo lỗi vì lệch .vi.md hay thiếu bdd_scenarios.vi.md
Và check_bdd_traceability.py đối chiếu độ phủ task thuần túy dựa trên bdd_scenarios.en.md

Scenario: [TTO-HP-04] [Tier A - Unit] RunnerConfig phân giải model và effort cho Role 2.3 theo thứ tự ưu tiên cấu hình

Cho tệp .devtool/review_config.json cấu hình providers.programmer.model là "gemini-4-hydrogen-xhigh" và thinking_level là "extra" (hoặc bản cũ "gemini-3.8-flash-high" trên đĩa)
Và biến môi trường AGY_PROGRAMMER_MODEL chưa được đặt
Khi lifecycle_runner.RunnerConfig phân giải model/effort hoặc gọi agy mà không truyền cờ CLI
Thì resolve_programmer_model trả về "gemini-4-hydrogen-xhigh", resolve_programmer_effort trả về "xhigh", và lệnh agy nhận "--model gemini-4-hydrogen-xhigh --effort xhigh" qua bảng alias dùng chung
Và truyền cờ --programmer-model "gemini-4-pro-high" qua CLI ghi đè cả .devtool/review_config.json lẫn biến môi trường

Scenario: [TTO-HP-05] [Tier C - Integration] Quy tắc và kỹ năng đã tinh gọn đáp ứng ngưỡng byte và các kiểm tra hợp đồng phát hành

Cho các tệp rules/CRITICAL_RULES.md, skills/dev-designer/SKILL.md, skills/dev-lifecycle/SKILL.md, skills/dev-implementation/SKILL.md và skills/task-observer/SKILL.md đã cập nhật trong repository
Khi chạy scripts/test_lifecycle_document_contract.py và đo kích thước byte/từ trên đĩa
Thì rules/CRITICAL_RULES.md có dung lượng tối đa 8192 bytes, giữ nguyên mục §9 Shell Configuration và thêm §10 Zero-Fluff Output Cap
Và skills/dev-designer/SKILL.md <= 22528 bytes, skills/dev-lifecycle/SKILL.md <= 2500 từ, skills/dev-implementation/SKILL.md <= 4500 từ đồng thời giữ đủ các mục bắt buộc và liên kết references trích xuất
Và skills/task-observer/SKILL.md đặt <SUBAGENT-STOP> ngay sau YAML frontmatter hợp lệ và sửa description loại trừ subagent/worker chạy nền
Và scripts/test_lifecycle_document_contract.py thoát với mã 0 và không có lỗi khẳng định nào

Scenario: [TTO-HP-06] [Tier C - Integration] Khôi phục ngữ cảnh rút gọn giới hạn tối đa 4096 bytes và đọc động cấu hình programmer

Cho workspace đa repo có metadata epic đang chạy, danh sách task và các RFC đang mở
Và .devtool/review_config.json đặt providers.programmer là "gemini-4-hydrogen-xhigh" với thinking_level "xhigh"
Khi scripts/resume_context.py chạy với --compact --epic token_throttling_optimization và --emit-prompt implement
Thì payload ngữ cảnh rút gọn có dung lượng tối đa 4096 bytes gồm ảnh chụp nhanh epic, trạng thái git repo hiện tại, các task khớp epic và RFC liên quan
Và prompt bàn giao được sinh ra hiển thị đúng "gemini-4-hydrogen-xhigh" và "xhigh" đọc động từ .devtool/review_config.json

Scenario: [TTO-HP-07] [Tier C - Integration] Vòng Cross-model review tối ưu đi thẳng vào sửa mã rõ ràng và điền kết quả thật vào Executive Report

Cho một kết luận CHANGES_REQUIRED ở Round 1 chỉ gồm các lỗi mã nguồn đã xác minh và không xung đột shared-contracts
Khi lifecycle_runner.step_cross_model_review chạy một vòng khắc phục rồi hội tụ
Thì các lỗi mã nguồn rõ ràng bỏ qua _draft_fix_plan và evaluate_programmer_fix_plan để đi thẳng vào _apply_code_fixes
Và render_final_executive_report điền bảng Top 3 Highest-Risk Findings trực tiếp từ dữ liệu phân tích trong review_results.md và principal_review.md thay cho chuỗi giữ chỗ

Scenario: [TTO-HP-08] [Tier C - Integration] Đường ống tối ưu token đầu-cuối áp dụng đồng bộ prompt gọn, cô lập review và cấu hình programmer

Cho một workspace epic cô lập được khởi tạo cùng .devtool/review_config.json, các tệp task có vùng dòng mục tiêu và bộ CLI review/agy giả lập
Khi đường ống lifecycle thực thi lần lượt kiểm tra sẵn sàng, review ngoài, điều phối worker, Gate 4 rút gọn và báo cáo tổng kết
Thì mọi prompt review đều tuân thủ ngân sách diff-only -U5 và tách log thô ra khỏi tài liệu markdown
Và mọi prompt worker đều bỏ qua việc nhúng toàn văn tệp nguồn đồng thời gọi gemini-4-hydrogen-xhigh với --effort xhigh
Và Gate 4 rút gọn chỉ xuất các dòng trạng thái GATE_PASS khi mọi kiểm tra đạt chuẩn
```

## Trường hợp biên và ranh giới

```gherkin
Scenario: [TTO-EC-01] [Tier A - Unit] Diff vượt ngân sách tự động cắt gọn về bảng --stat kèm tiêu đề hunk @@ theo từng tệp

Cho một git diff giả lập vượt quá MAX_DIFF_LINES (1500 dòng) hoặc MAX_DIFF_BYTES (60000 bytes)
Khi build_diff_section dựng phần nội dung diff cho review ngoài
Thì chuỗi trả về nằm gọn trong ngân sách byte mà vẫn giữ nguyên ranh giới cấu trúc từng tệp
Và phần nội dung rút gọn bao gồm rõ ràng thống kê git diff --stat kèm tiêu đề tệp và các dòng tiêu đề hunk @@ của tệp thay đổi

Scenario: [TTO-EC-02] [Tier A - Unit] Trình chạy task giới hạn đuôi 25 dòng và cấu hình Python chèn bộ cờ pytest yên lặng

Cho đầu ra thất bại của một lệnh kiểm tra task gồm 120 dòng stdout/stderr
Và .agents/quality/python-quality.json cùng manifest được sinh từ scaffold_quality_manifest.py
Khi run_task_checks.py định dạng bằng chứng lỗi và lệnh kiểm thử Python được kiểm tra
Thì run_task_checks.TAIL_LINES bằng 25 và đoạn trích xuất chỉ giữ lại 25 dòng khác rỗng cuối cùng
Và cả .agents/quality/python-quality.json lẫn manifest Python mới sinh đều gọi pytest kèm "-q", "--tb=short" và "--maxfail=3"

Scenario: [TTO-EC-03] [Tier C - Integration] Trình kiểm tra hợp đồng thiết kế từ chối tệp đã theo dõi trên 200 dòng thiếu ký hiệu hoặc vùng dòng

Cho một tệp task tham chiếu tệp mã nguồn Python không phải tệp mới dài hơn 200 dòng trong Allowed files
Và các mục Files và Impact Analysis của task bỏ sót tên symbol mục tiêu hoặc vùng dòng (L<start>-L<end>) cho tệp đó
Khi check_task_contract.py chạy kèm cờ --design trên tệp task
Thì check_task_contract.py thoát khác 0 và báo lỗi thiếu symbol hoặc vùng dòng cho tệp >200 dòng đó
Và bổ sung neo hợp lệ "path :: Symbol (L10-L85)" sẽ xóa bỏ vi phạm và trả về mã thoát 0

Scenario: [TTO-EC-04] [Tier A - Unit] Chuẩn hóa effort của programmer ánh xạ các biến thể "extra" thành xhigh

Cho các giá trị effort thô "extra", "EXTRA", "extra-high", "extra_high" và "xhigh"
Khi lifecycle_runner.normalize_agy_effort chuẩn hóa từng mức cấu hình
Thì mọi biến thể đều trả về giá trị chuẩn "xhigh"
Và trình dựng lệnh agy đưa cặp tham số "--effort", "xhigh" vào danh sách đối số

Scenario: [TTO-EC-05] [Tier C - Integration] Cơ chế lọc task-reviewer bỏ qua task đơn giản và kích hoạt trên task rủi ro cao hoặc đa module

Cho một task tài liệu hoặc tiện ích một tệp thông thường không gắn nhãn rủi ro cao và chưa đặt review_tier
Và một task phức tạp có review_tier: "full" hoặc nhãn ["security", "concurrency"] hoặc sửa 3 module không phải test
Khi áp dụng tiêu chí chọn lọc task-reviewer được định nghĩa trong dev-designer, dev-implementation và subagent-driven-development
Thì task một tệp đơn giản bỏ qua lượt subagent task-reviewer dư thừa
Và task phức tạp hoặc rủi ro cao bắt buộc kích hoạt lượt kiểm duyệt task-reviewer chuyên biệt trước khi chốt task

Scenario: [TTO-EC-06] [Tier C - Integration] Cờ verify.sh --quiet tóm tắt gọn từng mục trong khi --full chạy đủ 17 bộ kiểm tra

Cho bộ script công cụ và tài liệu skill dưới sự kiểm soát của scripts/verify.sh
Khi chạy bash scripts/verify.sh --quiet và khi chạy bash scripts/verify.sh --full
Thì chế độ --quiet chỉ in một dòng trạng thái ngắn gọn cho mỗi mục đạt chuẩn và không xả log thừa
Và chế độ --full thực thi đầy đủ các mục kiểm tra từ §1 đến §17 và thoát với mã 0
```

## Chuyển đổi trạng thái và bất biến

```gherkin
Scenario: [TTO-ST-01] [Tier A - Unit] load_review_config tự nâng cấp mặc định gemini-3.8-flash cũ nhưng giữ nguyên model tùy chỉnh

Cho một tệp .devtool/review_config.json có sẵn đặt providers.programmer.model là "gemini-3.8-flash-high"
Và tệp cấu hình thứ hai nơi người dùng tự chỉnh providers.programmer.model thành "claude-sonnet-4-6"
Khi run_external_review.load_review_config nạp từng tệp cấu hình
Thì khóa "gemini-3.8-flash-high" cũ được nâng cấp trong bộ nhớ thành "gemini-4-hydrogen-xhigh" kèm thinking_level "xhigh"
Và giá trị tùy chỉnh "claude-sonnet-4-6" được giữ nguyên hoàn toàn không bị ghi đè

Scenario: [TTO-ST-02] [Tier C - Integration] Gói handoff và mẫu handoff chỉ liệt kê tài liệu SSOT tiếng Anh và loại bỏ .vi.md

Cho một thư mục epic có đủ spec.en.md, spec.vi.md, epic.en.md, epic.vi.md, bdd_scenarios.en.md và bdd_scenarios.vi.md
Khi package_epic.py sinh tệp handoff.md từ skills/dev-lifecycle/references/handoff-template.md
Thì mục Read First được sinh ra chỉ chứa các tệp *.en.md và không có bất kỳ đường dẫn *.vi.md nào
Và handoff-template.md không còn dòng gán cứng model cũ mâu thuẫn với cơ chế chọn Role 2.3 theo cấu hình

Scenario: [TTO-ST-03] [Tier C - Integration] Cổng sẵn sàng Stage 4 với --strict-bilingual bắt buộc khớp hoàn toàn giữa .en.md và .vi.md

Cho một thư mục epic có bản HLD .vi.md giữ nguyên heading nhưng nội dung bị lệch sau khi .en.md chỉnh sửa, hoặc thiếu tệp bdd_scenarios.vi.md
Khi chạy check_epic_readiness.py --strict-bilingual và check_bdd_traceability.py plan --scenarios bdd_scenarios.en.md --tasks task_*.md --strict-bilingual
Thì check_epic_readiness.py --strict-bilingual thoát khác 0 do lệch watermark Spec/HLD hoặc thiếu bdd_scenarios.vi.md trong khi check_bdd_traceability.py kiểm tra khớp ID kịch bản BDD
Và sau khi đồng bộ watermark Spec/HLD .vi.md cùng tạo bdd_scenarios.vi.md khớp mã kịch bản và mục lục, cả hai lệnh --strict-bilingual đều thoát mã 0

Scenario: [TTO-ST-04] [Tier C - Integration] Cross-model review chuyển lên Role 2.2 khi xuất hiện xung đột shared-contracts hoặc mơ hồ kiến trúc

Cho một phát hiện ở Round 1 của cross-model review liên quan tới shared-contracts/api_contract.md hoặc thay đổi chuyển trạng thái kiến trúc mơ hồ
Khi lifecycle_runner.step_cross_model_review phân loại các phát hiện của vòng review
Thì luồng sửa nhanh không được phép chạy và hệ thống dừng khẩn với CRITICAL_CONFLICT hoặc chuyển fix_plan_round1.md qua Role 2.2 thẩm định trước khi sửa mã

Scenario: [TTO-ST-05] [Tier C - Integration] Hook Pre-Finish của finishing-a-development-branch ở Stage 4 đồng bộ .vi.md trước khi merge

Cho tệp skills/finishing-a-development-branch/SKILL.md đã được cập nhật trong bộ công cụ
Khi kiểm tra quy trình kết thúc nhánh Stage 4 và chạy verify.sh §3 cùng §8
Thì bước đồng bộ song ngữ Pre-Finish ở Stage 4 yêu cầu cập nhật phần sai lệch cho Spec và HLD .vi.md, sinh bdd_scenarios.vi.md và chạy check_epic_readiness.py --strict-bilingual trước khi merge
Và toàn bộ liên kết chéo cùng hợp đồng tài liệu đều vượt qua verify.sh không lỗi
```

## Bất đồng bộ và đồng thời

```gherkin
Scenario: [TTO-AR-01] [Tier C - Integration] Điều phối theo wave song song chạy đồng thời các task độc lập với prompt chỉ chứa đường dẫn và Zero-Fluff

Cho một đồ thị DAG của epic gồm hai task Wave 1 độc lập và một task Wave 2 bị chặn bởi cả hai task trên
Và một pool worker cô lập được khởi tạo bằng manage_worker_pool.py
Khi lifecycle_runner.step_implementation thực thi giai đoạn lập trình qua mock dispatcher ghi nhận an toàn luồng
Thì cả hai task Wave 1 chạy song song trong các slot tách biệt với sync trạng thái và git commit thực hiện trong cwd=slot_path (mỗi commit chỉ chứa file của task đó) trước khi serialize merge_slot
Và prompt mỗi task không nhúng toàn văn file task, cấm gọi d3nexus:task-observer, chỉ truyền đường dẫn tệp cùng vùng dòng mục tiêu và kèm quy tắc Zero-Fluff

Scenario: [TTO-AR-02] [Tier C - Integration] Ngữ cảnh sạch từng task và log thô tách biệt theo từng vòng ngăn rò rỉ lịch sử giữa các phiên

Cho các vòng Principal Review và Cross-Model Review nối tiếp cùng các lượt điều phối task liên tiếp trong cùng một epic
Khi run_external_review.render_round ghi log và lifecycle_runner khởi chạy Task N+1 sau khi Task N đã commit
Thì mỗi vòng review ghi bản log thô cô lập vào đường dẫn riêng build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log không ghi đè giữa principal và code hoặc ghép vào file vòng khác
Và prompt của Task N+1 hoàn toàn không mang theo đầu ra công cụ hay stderr tích tụ từ Task N
```

## Xử lý lỗi và khả năng phục hồi

```gherkin
Scenario: [TTO-FR-01] [Tier A - Unit] collect_facts xuất một dòng cho lệnh đạt, giới hạn lỗi 25 dòng và tách log thô ra khỏi markdown

Cho một lệnh đạt chuẩn trả về 180 dòng stdout với mã thoát 0 và một lệnh lỗi trả về 90 dòng stderr với mã thoát 1
Khi run_external_review.fact tạo bằng chứng cho prompt và render_round lưu kết quả vòng review
Thì lệnh đạt chuẩn chỉ tạo đúng một dòng "PASS: <label>" và bỏ qua stdout
Và lệnh thất bại chỉ đính kèm nhãn lệnh cùng tối đa 25 dòng cuối khác rỗng
Và phần thân dài và --- stderr --- của CLI được ghi vào build/reviews/<epic>_<kind>_round<n>_<sha7>.raw.log trong khi Raw output: vẫn giữ tiêu đề pass, Verdict và dòng đầu lỗi để round_passes(round_output(lines)) trả về đúng verdict

Scenario: [TTO-FR-02] [Tier C - Integration] Gate 4 rút gọn hiển thị tiêu đề provider lỗi và 25 dòng đuôi khi gặp sự cố

Cho một cấu hình chất lượng gồm một capability đạt chuẩn và một capability lỗi in 80 dòng chẩn đoán ra stderr
Khi chạy verify_polyglot_registry.py kèm cờ --compact
Thì tiến trình thoát khác 0 với kết luận FAIL
Và stdout chỉ in "GATE_PASS:" cho capability đạt, tiêu đề capability lỗi và tối đa 25 dòng cuối lấy từ build/quality/
Và đầy đủ 80 dòng gốc vẫn được lưu an toàn trên đĩa tại build/quality/<provider>/<cap>.log

Scenario: [TTO-FR-03] [Tier A - Unit] lifecycle_runner._tail_lines cắt thông báo lỗi Gate 4 và kiểm tra trung gian tối đa 25 dòng

Cho một lỗi tiến trình con từ run_gate4 hoặc run_intermediate_check phát ra 120 dòng traceback
Khi lifecycle_runner định dạng đoạn tóm tắt lỗi qua _tail_lines(output, 25)
Thì đoạn trích trả về có tối đa 25 dòng kết thúc ngay tại tóm tắt assertion lỗi cuối cùng
Và chuỗi lỗi lưu trong ngoại lệ hoặc trạng thái truyền sang bước sau không bao giờ vượt quá 25 dòng traceback

Scenario: [TTO-FR-04] [Tier C - Integration] Bộ kiểm thử hồi quy định lượng báo lỗi rõ ràng nếu kích thước quy tắc, kỹ năng, ngữ cảnh hoặc prompt vượt trần

Cho các tệp thực tế trong repository và harness epic giả lập bên trong tests/test_token_throttling_acceptance.py
Khi chạy bộ kiểm thử chấp nhận định lượng dưới pytest
Thì các assertion kiểm tra tường minh trần dung lượng byte (CRITICAL_RULES.md <= 8192, dev-designer/SKILL.md <= 22528, resume_context --compact <= 4096) và ngân sách prompt review
Và mọi vi phạm trần đều báo lỗi kèm thông số đo thực tế thay cho các phép kiểm tra boolean chung chung
```

<!-- sync-en-sha256: be7c992ac8a39186 -->
