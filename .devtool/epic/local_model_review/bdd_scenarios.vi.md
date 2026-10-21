# Kịch bản BDD review bằng model local

## Mục lục

- [Siêu dữ liệu](#siêu-dữ-liệu)
- [Luồng thành công](#luồng-thành-công)
- [Ca biên và ranh giới](#ca-biên-và-ranh-giới)
- [Chuyển trạng thái](#chuyển-trạng-thái)
- [Bất đồng bộ và race condition](#bất-đồng-bộ-và-race-condition)
- [Lỗi và khả năng phục hồi](#lỗi-và-khả-năng-phục-hồi)

## Siêu dữ liệu

- **Epic**: `local_model_review`
- **Ngôn ngữ chuẩn**: Tiếng Anh
- **Prefix scenario**: `LMR`
- **Automation root**: `skills/dev-implementation/resources/scripts/`, `scripts/`
- **Quy tắc**: Mỗi ID scenario được gán đúng một task và xuất hiện trong một automated test.
- **Server giả**: mọi lần gọi Ollama đi tới một `http.server` trên `127.0.0.1` bên trong test.

## Luồng thành công

```gherkin
Scenario: [LMR-HP-01] [Tier C - Integration] Review Choice đưa ra ba lựa chọn

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, rules/CRITICAL_RULES.md, docs/lifecycles.en.md và docs/lifecycles.vi.md
When các contract test vòng đời đọc chúng
Then mỗi file nêu "Local model review" bên cạnh "Finish" và "Cross-model review"
And dev-implementation ghi "--cli ollama --model <model>" và bảo agent chạy "ollama list" rồi hỏi
And Red Flags của dev-lifecycle cấm chọn model Ollama thay developer

Scenario: [LMR-HP-02] [Tier C - Integration] Luật dùng chung tới được prompt của Claude và Codex

Given một repo epic tạm và một claude giả trên PATH lưu lại stdin của nó
When run_external_review.py run --cli claude ghi một round
Then prompt đã lưu chứa "Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic" và "Immutable Real Artifacts"
And prompt đã lưu không chứa chuỗi "$rules"

Scenario: [LMR-HP-03] [Tier C - Integration] Review local một epic hai task ghi một round

Given một epic tạm có hai commit task và một server Ollama giả trả lời mọi chat bằng "Verdict: PASS"
When run --cli ollama --model qwen38-reviewer --host <server giả> chạy
Then server nhận đúng 3 request chat
And review_results.md có thêm "## Round 1" với "- **CLI**: ollama", "- **Model**: qwen38-reviewer", "- **Passes**: 3", "- **Status**: completed" và "- **Verdict**: PASS"
And lần chạy exit 0

Scenario: [LMR-HP-04] [Tier C - Integration] Lát cắt task mang mọi thứ reviewer được đánh giá

Given một commit task có file task ghi "Covers: DEMO-HP-01" và row verify trong evidence có 40 dòng output_tail
When build_slices và render_user chạy
Then user message có "## Task file", "## Scenarios covered", "## Evidence" và "## Diff of <short sha>" theo đúng thứ tự
And "## Scenarios covered" chứa khối Gherkin của DEMO-HP-01 và không chứa scenario nào khác
And row evidence hiện đúng 15 dòng cuối trong 40 dòng output
And diff không chứa đường dẫn nào dưới ".devtool/"

Scenario: [LMR-HP-05] [Tier C - Integration] System message khớp với loại pass

Given một lát cắt task có diff chạm "lib/a.dart"
When render_system chạy
Then message chứa "Decisions Already Made", "No Reconstructed Logic", nội dung section "## Flutter", checklist "## Task pass" và "Verdict: PASS"
And nó không chứa "$rules", "$platform_rules" hay "$checklist"
And một lát cắt epic nhận checklist "## Epic pass" thay cho checklist task

Scenario: [LMR-HP-06] [Tier C - Integration] Modelfile quyết định context

Given /api/show báo "num_ctx 65536" trong parameters
When probe chạy và chat_options(65536, None, 30000) chạy
Then probe trả về 65536
And chat_options trả về {"num_predict": 35536} không có khóa "num_ctx"

Scenario: [LMR-HP-07] [Tier C - Integration] Mọi luật nền tảng được trích đều có trong kit

Given references/local-review-platforms.md
When test thu thập ID luật của các section Flutter, Android và iOS cùng tên luật in đậm của các section Rust và Python
Then mỗi ID xuất hiện trong một row đánh dấu "Blocker" của SKILL.md thuộc architecture-audit, code-health-audit hoặc security-audit
And mỗi tên Rust xuất hiện trong rust-architecture-governance.md và mỗi tên Python trong python-architecture-governance.md

Scenario: [LMR-HP-08] [Tier C - Integration] Triage liệt kê mọi finding của round mới nhất

Given một round đã ghi có "[Important] a.py:3 — missing guard" và "[Minor] b.py:5 — wording"
When run_external_review.py triage --epic-dir demo chạy
Then nó exit 0 và in "# Review Triage: demo, Round 1"
And bảng "## Findings" của nó có row 1 và 2 với severity, location và problem của round, và "?" ở Assessment, Evidence và Proposed action
And nó kết thúc bằng một section "## Next Steps"

Scenario: [LMR-HP-09] [Tier C - Integration] Workflow bắt buộc triage trước khi xử lý finding

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md và rules/CRITICAL_RULES.md
When các contract test vòng đời đọc chúng
Then mỗi file nêu "run_external_review.py triage"
And dev-implementation link tới references/review-triage.md và chờ quyết định của developer trước mọi Fix commit
And Red Flags của dev-lifecycle cấm xử lý finding review trước khi trình bày triage

Scenario: [LMR-HP-10] [Tier C - Integration] Triage so sánh mọi round

Given một Round 1 của claude có finding Important đã quyết "fixed in abc1234" và một Round 2 của ollama có một finding Minor
When triage chạy
Then bảng "## Round Comparison" có mỗi round một row với CLI / Model, Status, Verdict, Critical, Important, Minor, Fixed, Dismissed và Undecided
And Round 1 hiện Important 1 và Fixed 1, còn Round 2 hiện Minor 1
```

## Ca biên và ranh giới

```gherkin
Scenario: [LMR-EC-01] [Tier C - Integration] Review local thiếu model dừng ngay từ đầu

Given một repo epic tạm
When run --cli ollama chạy không có --model
Then nó exit 2 với "--cli ollama needs --model" trên stderr
And stderr không bao giờ hiện "[Pre-check] audit_epic.py"
And không có review_results.md nào

Scenario: [LMR-EC-02] [Tier C - Integration] Mặc định và ghi đè context

Given một model có Modelfile không đặt num_ctx
When chat_options(None, None, 1000) chạy
Then nó trả về {"num_ctx": 32768, "num_predict": 31768}
And chat_options(65536, 16384, 1000) trả về {"num_ctx": 16384, "num_predict": 15384}

Scenario: [LMR-EC-03] [Tier C - Integration] Diff task quá lớn bỏ file lớn nhất trước

Given một commit task thêm 9000 byte vào "big.py" và 300 byte vào "small.py"
When fit chạy với ngân sách vừa mọi thứ trừ diff của big.py
Then user message giữ diff của small.py và bỏ diff của big.py
And "## Not shown" liệt kê "big.py"
And omitted của lát cắt sau khi fit là ("big.py",)

Scenario: [LMR-EC-04] [Tier C - Integration] Phần không được cắt lớn hơn ngân sách

Given một lát cắt task mà riêng file task đã ước lượng hơn 1000 token
When fit chạy với ngân sách 1000
Then nó raise LocalReviewError nêu id task và "raise --num-ctx"

Scenario: [LMR-EC-05] [Tier C - Integration] Section nền tảng theo đuôi file được chạm tới

Given các đường dẫn "app/lib/a.dart" và "native/src/b.rs"
When platform_sections chạy
Then nó trả về đúng section Flutter rồi tới section Rust
And với các đường dẫn "README.md" và "web/x.ts" nó trả về danh sách rỗng
And render_system cho lát cắt đó chứa "No platform rules apply to this slice."

Scenario: [LMR-EC-06] [Tier C - Integration] Task legacy nhập vào lát cắt epic

Given một commit task có evidence và một commit sửa "src/legacy.py" mà không chạm file evidence nào
When build_slices chạy
Then nó trả về một lát cắt task rồi tới lát cắt epic
And "## Commits outside tasks" của lát cắt epic chứa diff của src/legacy.py

Scenario: [LMR-EC-07] [Tier C - Integration] Thinking nằm trong content không bao giờ được parse

Given content "draft [Critical] a.py:1 — x\nVerdict: CHANGES REQUIRED\n</think>\n## Analysis\nfine\nVerdict: PASS"
When answer_text chạy
Then nó trả về "## Analysis\nfine\nVerdict: PASS"

Scenario: [LMR-EC-08] [Tier C - Integration] Finding nháp trong Analysis không phải finding

Given một pass ollama có out là "## Analysis\n- [Critical] a.py:1 — draft\nVerdict: PASS" với code 0 và done_reason "stop"
When record_round chạy
Then round không có row finding nào, có "- **Status**: completed" và "- **Verdict**: PASS"
And record_round trả về 0

Scenario: [LMR-EC-09] [Tier C - Integration] File bị bỏ tới được metadata của round

Given một pass ollama "task_1" có omitted ("big.py",) và một pass epic không bỏ gì
When record_round chạy
Then round hiện "- **Omitted**: task_1: big.py"

Scenario: [LMR-EC-10] [Tier C - Integration] Triage đánh dấu pass không có verdict

Given một round ollama có pass 2 không có dòng verdict và pass 3 lỗi với "HTTP 500: boom"
When triage chạy
Then bảng "## Passes" hiện pass 2 với verdict "none" và pass 3 với error "HTTP 500: boom"

Scenario: [LMR-EC-11] [Tier C - Integration] Finding đã sửa bị báo lại ở cùng đường dẫn được đánh dấu

Given Round 1 có "[Important] src/a.py:3 — missing guard" và "[Important] src/b.py:9 — weak", cả hai đã quyết "fixed in abc1234"
And Round 2 báo "[Minor] src/a.py:40 — still unguarded"
When triage chạy
Then "## Since Round 1" liệt kê src/a.py:3 là bị báo lại ở cùng đường dẫn, kèm "check the fix"
And liệt kê src/b.py:9 là không bị báo lại
```

## Chuyển trạng thái

```gherkin
Scenario: [LMR-ST-01] [Tier C - Integration] Finding blocking từ review local chặn check tới khi được quyết định

Given một round ollama đã ghi có "[Important] lib/a.py:3 — missing guard" trong đó lib/a.py đã được đưa vào
When check chạy
Then nó exit 1 và in "undecided: #1 Important lib/a.py:3"
And sau khi ô Decision thành "dismissed: false positive" thì check exit 0

Scenario: [LMR-ST-02] [Tier C - Integration] Đánh số round dùng chung giữa các reviewer

Given review_results.md đã có "## Round 1" completed của Claude với một finding Critical chưa quyết định
When một round ollama không có finding được ghi
Then nó là "## Round 2" với "- **CLI**: ollama"
And check exit 0 vì chỉ round completed mới nhất quản lý nó

Scenario: [LMR-ST-03] [Tier C - Integration] Local model review quay về Gate 4 đầy đủ

Given skills/dev-implementation/SKILL.md, skills/dev-lifecycle/SKILL.md, docs/lifecycles.en.md và docs/lifecycles.vi.md
When các contract test vòng đời đọc chúng
Then mỗi file định tuyến Local model review qua cạnh ghi nhận round ("round recorded", hoặc "đã ghi nhận round" trong tiếng Việt) quay về Phase 4 hoặc Gate 4 đầy đủ
And không file nào định tuyến nó thẳng tới Gate 5

Scenario: [LMR-ST-04] [Tier C - Integration] Triage đọc round mới nhất, completed hay không

Given một Round 1 completed và một Round 2 "no verdict"
When triage chạy
Then nó in "Round 2" và chỉ các finding của Round 2 trong bảng Findings
```

## Bất đồng bộ và race condition

```gherkin
Scenario: [LMR-AR-01] [Tier C - Integration] Các pass chạy lần lượt theo thứ tự commit

Given hai commit task và một server giả ghi lại lúc mỗi request chat bắt đầu và kết thúc
When run --cli ollama chạy
Then không có hai request nào chồng lên nhau
And các request mang task_1, rồi task_2, rồi lát cắt epic
And stderr hiện "[Pass 1/3]", "[Pass 2/3]" và "[Pass 3/3]" theo đúng thứ tự

Scenario: [LMR-AR-02] [Tier C - Integration] Timeout áp dụng cho từng pass

Given một server giả trả lời mỗi chat sau 2 giây bằng "Verdict: PASS"
When run --cli ollama --timeout 3 chạy qua ba pass
Then cả ba pass đều hoàn thành
And round là "- **Status**: completed"
```

## Lỗi và khả năng phục hồi

```gherkin
Scenario: [LMR-FR-01] [Tier C - Integration] Lỗi thăm dò nêu rõ nguyên nhân

Given không có server nào lắng nghe trên một port local đã đóng
When probe chạy tới port đó
Then nó raise LocalReviewError "Ollama server not reachable at http://127.0.0.1:<port>"
And với một server giả có /api/show trả 404, nó raise "model ghost is not installed (ollama list)"

Scenario: [LMR-FR-02] [Tier C - Integration] Server không phản hồi dừng lần chạy trước bước facts

Given một repo epic tạm và không có server nào trên port của --host
When run --cli ollama --model m chạy
Then stderr hiện "WAS NOT INVOKED" và "Ollama server not reachable"
And stderr không bao giờ hiện "[Pre-check] audit_epic.py"
And lần chạy exit 2 và không có review_results.md nào

Scenario: [LMR-FR-03] [Tier C - Integration] Lỗi kênh truyền thành reply

Given một server giả có /api/chat trả HTTP 500 với body "boom"
When chat chạy
Then nó trả về content "" và error "HTTP 500: boom"
And với một server trả lời sau 3 giây, chat với timeout 1 trả về error "timed out after 1 seconds"

Scenario: [LMR-FR-04] [Tier C - Integration] Pass lỗi dừng lần chạy và ghi những gì đã có

Given một server giả trả lời chat đầu tiên bằng "Verdict: PASS" và chat thứ hai bằng HTTP 500
When run --cli ollama chạy qua ba lát cắt
Then server nhận đúng 2 request chat
And round có "- **Status**: no verdict", raw output có "### Pass 1" và chữ "HTTP 500"
And lần chạy exit 2

Scenario: [LMR-FR-05] [Tier C - Integration] Output bị cắt là no verdict

Given một pass ollama có code 0, done_reason "length" và out "Verdict: PASS"
When record_round chạy
Then round có "- **Status**: no verdict"
And record_round trả về 2

Scenario: [LMR-FR-06] [Tier C - Integration] Finding blocking ở đường dẫn chưa được đưa vào bị chú thích

Given một pass ollama có phần đã đưa vào không bao giờ chứa "ghost.py" và out là "Verdict: CHANGES REQUIRED\n[Critical] ghost.py:9 — broken\n[Important] seen.py:2 — weak"
When record_round chạy
Then row ghost.py giữ Severity "Critical" và ô Problem kết thúc bằng "(location not shown to reviewer)"
And row seen.py, có đường dẫn đã được đưa vào, không bị chú thích

Scenario: [LMR-FR-07] [Tier C - Integration] Lát cắt không vừa dừng lần chạy trước mọi lần chat

Given --num-ctx 1000 và một file task lớn hơn 1800 byte
When run --cli ollama chạy
Then nó exit 2 với thông báo nêu id task và "raise --num-ctx"
And server giả nhận 0 request chat
And không có review_results.md nào

Scenario: [LMR-FR-08] [Tier C - Integration] Triage khi chưa có round review thì dừng

Given một thư mục epic không có review_results.md
When triage chạy
Then nó exit 2 và in "no review round recorded for demo" ra stderr
```
