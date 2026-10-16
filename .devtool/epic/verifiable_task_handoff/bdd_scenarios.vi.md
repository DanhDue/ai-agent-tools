# Kịch bản BDD: Handoff task kiểm chứng được

## Mục lục

- [1. Tổng quan và ma trận biên](#1-tổng-quan-và-ma-trận-biên)
- [2. UC-1 Hợp đồng task của designer được kiểm](#2-uc-1-hợp-đồng-task-của-designer-được-kiểm)
- [3. UC-2 Các check của executor được ghi lại](#3-uc-2-các-check-của-executor-được-ghi-lại)
- [4. UC-3 Gate done chỉ tin evidence đã được ghi](#4-uc-3-gate-done-chỉ-tin-evidence-đã-được-ghi)
- [5. UC-4 Truy vết đọc kết quả test](#5-uc-4-truy-vết-đọc-kết-quả-test)
- [6. UC-5 Gate 4 audit epic](#6-uc-5-gate-4-audit-epic)
- [7. UC-6 Văn bản skill nêu rõ hợp đồng](#7-uc-6-văn-bản-skill-nêu-rõ-hợp-đồng)
- [8. UC-7 Cả vòng đời chạy trọn từ đầu đến cuối](#8-uc-7-cả-vòng-đời-chạy-trọn-từ-đầu-đến-cuối)
- [9. UC-8 Một model thứ hai review epic đã xong](#9-uc-8-một-model-thứ-hai-review-epic-đã-xong)

## 1. Tổng quan và ma trận biên

Hợp đồng hành vi của epic `verifiable_task_handoff`. Mỗi scenario mang một định danh `VTH-` và cần ít
nhất một integration test tự động, nằm dưới các thư mục integration test của HLD, có tên test case
chứa định danh đó và pass trong báo cáo JUnit.

| Chiều | Scenario | Bảo đảm |
|-------|----------|---------|
| 1. Happy path | VTH-HP-01 đến VTH-HP-13 | Một task đúng hợp đồng đi từ thiết kế tới audit với mọi script trả exit 0; một review sạch được ghi lại; các skill nêu rõ hợp đồng |
| 2. Edge case và biên | VTH-EC-01 đến VTH-EC-07 | Hợp đồng sai dạng, path không khớp repo, biến chưa đặt và báo cáo test gây hiểu nhầm đều bị bắt kèm tên; finding review mức Minor không chặn |
| 3. Chuyển trạng thái | VTH-ST-01 đến VTH-ST-11 | `done` chỉ đạt được từ một lần verify khớp, đã được ghi và đúng phạm vi; audit bắt mọi con đường khác; finding review chặn giữ Phase 4 lại |
| 4. Async và race condition | VTH-AR-01, VTH-AR-02 | Nhánh base bị dịch chuyển, và gate chạy nhầm checkout, đều xuống cấp an toàn |
| 5. Lỗi và khả năng chống chịu | VTH-FR-01 đến VTH-FR-08 | Timeout, báo cáo cũ, đầu vào sai và CLI review lỗi hoặc can thiệp đều fail an toàn với đúng exit code đã quy định |

## 2. UC-1 Hợp đồng task của designer được kiểm

```gherkin
Tính năng: check_task_contract.py và plan kiểm những gì designer đã viết

  Kịch bản: [VTH-HP-01] [Tier C - Integration] Một epic đúng hợp đồng qua được check lúc thiết kế
    Cho một repo git có HLD khai báo Protected paths, Integration results và Verification Environment
    Và hai file task có đủ các mục Files, Verification, Definition of Done, Stop and Report If và Decisions Already Made
    Khi check_task_contract.py chạy với --design
    Thì nó trả exit 0
    Và nó in ra các chương trình được track mà các dòng Verification chạy, như protected path ngầm định

  Kịch bản: [VTH-EC-01] [Tier C - Integration] Các path không khớp với repo bị nêu tên
    Cho một task có Allowed files liệt kê một path chưa track mà không có "(new)"
    Và một path "(new)" đã tồn tại
    Và một path Read-only context không tồn tại
    Và một Command nêu một path repo mà không task nào tạo ra
    Khi check_task_contract.py chạy với --design
    Thì nó trả exit 1 và nêu từng path kèm task của nó
    Và khi không có --design thì path "(new)" đã tồn tại của một task đã done không bị báo

  Kịch bản: [VTH-EC-02] [Tier C - Integration] Mục Definition of Done không có lệnh bị từ chối
    Cho một bullet Definition of Done kết thúc mà không có tham chiếu dòng lẫn "(Gate 5)"
    Và một bullet tham chiếu dòng V9 mà bảng không có
    Khi check_task_contract.py chạy
    Thì nó trả exit 1 và nêu cả hai bullet

  Kịch bản: [VTH-EC-03] [Tier C - Integration] Bảng Verification sai dạng bị từ chối theo từng dòng
    Cho một bảng có ID trùng, phase lạ, mệnh đề Expect ngoài ngữ pháp và "results" trên một dòng GREEN
    Và một task không có dòng RED lẫn lý do "RED: n/a"
    Và một task có dòng Covers nhưng không có dòng TIER-C mang "results"
    Khi check_task_contract.py chạy
    Thì nó trả exit 1 và nêu mọi lỗi dạng "<task>:<row>: <problem>"

  Kịch bản: [VTH-EC-04] [Tier C - Integration] Thiếu khai báo trong HLD bị từ chối
    Cho một HLD không có dòng Protected paths, không có dòng Integration results hoặc có mục Verification Environment rỗng
    Và một biến Needs mà mục Verification Environment không nêu
    Và một path results mà git không ignore
    Khi check_task_contract.py chạy
    Thì nó trả exit 1 và nêu từng khai báo thiếu hoặc sai

  Kịch bản: [VTH-ST-01] [Tier C - Integration] Một định danh có hai task sở hữu làm fail plan
    Cho một tài liệu scenario có VTH-HP-01
    Và hai file task mà dòng Covers đều nêu VTH-HP-01
    Khi check_bdd_traceability.py plan chạy
    Thì nó trả exit 1 và nêu cả hai task cho VTH-HP-01

  Kịch bản: [VTH-FR-04] [Tier C - Integration] Check hợp đồng báo lỗi cách gọi bằng exit 2
    Cho một file task không đọc được, hoặc một thư mục làm việc nằm ngoài mọi repo git
    Khi check_task_contract.py chạy
    Thì nó trả exit 2 kèm lý do trên stderr
```

## 3. UC-2 Các check của executor được ghi lại

```gherkin
Tính năng: run_task_checks.py chạy các dòng đã khai báo và ghi evidence

  Kịch bản: [VTH-HP-02] [Tier C - Integration] Red rồi verify trên một thay đổi đúng ghi lại evidence pass
    Cho một worktree của epic với một task có dòng RED fail trước thay đổi và dòng GREEN pass sau thay đổi
    Khi run_task_checks.py red chạy, thay đổi được thực hiện, rồi run_task_checks.py verify chạy
    Thì cả hai lệnh trả exit 0
    Và file evidence chứa cả hai lần chạy với head, tree, patch_id, outcome PASS của mọi dòng và phần cuối output của nó
    Và lần chạy verify kết thúc bằng một dòng SCOPE là PASS

  Kịch bản: [VTH-EC-05] [Tier C - Integration] Dòng có biến Needs chưa đặt bị BLOCKED, không chạy
    Cho một dòng TIER-C có cột Needs nêu TEST_DATABASE_URL
    Và TEST_DATABASE_URL chưa được đặt
    Khi run_task_checks.py verify chạy
    Thì dòng đó là BLOCKED và lệnh của nó không bao giờ được thực thi
    Và lần chạy trả exit 1, evidence vẫn được ghi

  Kịch bản: [VTH-ST-02] [Tier C - Integration] Scope từ chối thay đổi ngoài Allowed files hoặc vào chương trình được bảo vệ
    Cho một task có Allowed files liệt kê "scripts/**"
    Và một dòng Verification chạy chương trình được track "scripts/verify_coverage.py"
    Khi thay đổi sửa một file ngoài Allowed files và sửa "scripts/verify_coverage.py"
    Và run_task_checks.py verify chạy
    Thì dòng SCOPE là FAIL và nêu cả hai file
    Và chương trình được bảo vệ bị báo là không được nêu đích danh trong Allowed files

  Kịch bản: [VTH-FR-01] [Tier C - Integration] Dòng chạy chậm và báo cáo cũ đều fail an toàn
    Cho một dòng có lệnh chạy lâu hơn timeout
    Và một dòng TIER-C có file results được ghi trước khi dòng đó bắt đầu
    Khi run_task_checks.py verify chạy với --timeout ngắn
    Thì dòng chạy chậm là FAIL với lý do timeout
    Và dòng TIER-C là FAIL với "results not produced by this run"

  Kịch bản: [VTH-FR-05] [Tier C - Integration] File task bị bộ parse từ chối thì không ghi evidence
    Cho một file task có bảng Verification thiếu cột Expect
    Khi run_task_checks.py verify chạy
    Thì nó trả exit 2 kèm lỗi parse trên stderr
    Và không file evidence nào được tạo
```

## 4. UC-3 Gate done chỉ tin evidence đã được ghi

```gherkin
Tính năng: sync_task_status.py task done từ chối trừ khi evidence đã ghi khớp

  Kịch bản: [VTH-HP-03] [Tier C - Integration] Evidence khớp cho phép task thành done
    Cho một task của epic code có lần chạy red và verify đã được ghi và khớp với cây hiện tại
    Khi run_task_checks.py status chạy
    Thì nó báo gate done sẽ pass và trả exit 0
    Khi sync_task_status.py task done chạy trong worktree của epic
    Thì các trường status, modified và completedAt được ghi ở mọi checkout

  Kịch bản: [VTH-ST-03] [Tier C - Integration] Done khi không có evidence bị từ chối
    Cho một task của epic code không có file evidence
    Khi sync_task_status.py task done chạy
    Thì nó trả exit 1 và nêu việc thiếu evidence
    Và status của task không đổi ở mọi checkout

  Kịch bản: [VTH-ST-04] [Tier C - Integration] Sửa đổi sau khi verify bị từ chối
    Cho một task có lần chạy verify đã pass
    Khi một file nguồn bị sửa sau đó và sync_task_status.py task done chạy
    Thì nó trả exit 1 vì tree của verify khác cây hiện tại
    Khi thay vào đó Expect của dòng V2 bị sửa sau đó và sync_task_status.py task done chạy
    Thì nó trả exit 1 vì expect đã ghi của V2 khác với bảng

  Kịch bản: [VTH-ST-05] [Tier C - Integration] Lần chạy RED không đi trước thay đổi bị từ chối
    Cho một task có lần chạy red được ghi trên cùng cây với lần chạy verify
    Khi sync_task_status.py task done chạy
    Thì nó trả exit 1 và nêu điều kiện thứ tự RED
    Và điều tương tự xảy ra khi lần chạy red kết thúc sau khi lần chạy verify bắt đầu

  Kịch bản: [VTH-ST-06] [Tier C - Integration] Chỉ epic code bị gate
    Cho một task của epic code có overview khai "Integration test roots:" và file task không có mục Verification
    Khi sync_task_status.py task done chạy
    Thì nó trả exit 1 với "retrofit required"
    Cho thay vào đó một task của epic tài liệu có overview không khai "Integration test roots:"
    Khi sync_task_status.py task done chạy
    Thì status được ghi như trước đây

  Kịch bản: [VTH-ST-07] [Tier C - Integration] Định danh được cover mà không có case pass bị từ chối
    Cho một task có dòng Covers nêu VTH-HP-01 và VTH-EC-01
    Và evidence có digest kết quả chỉ chứa case passed cho VTH-HP-01
    Khi sync_task_status.py task done chạy
    Thì nó trả exit 1 và nêu VTH-EC-01

  Kịch bản: [VTH-AR-02] [Tier C - Integration] Gate chạy từ checkout không có evidence thì không ghi gì
    Cho một checkout chính và một worktree của epic, evidence chỉ nằm trong worktree
    Khi sync_task_status.py task done chạy từ checkout chính
    Thì nó trả exit 1 và nói gate phải chạy trong worktree của epic
    Và không bản sao task nào ở bất kỳ checkout nào bị đổi
```

## 5. UC-4 Truy vết đọc kết quả test

```gherkin
Tính năng: check_bdd_traceability.py tests --results chứng minh mỗi định danh đã chạy và pass

  Kịch bản: [VTH-HP-04] [Tier C - Integration] Báo cáo JUnit và Dart chứng minh mọi định danh
    Cho một file JUnit có case passed "test_vth_hp_01_compliant_epic"
    Và một thư mục file JUnit kiểu Gradle có case passed cho VTH-EC-01
    Và một file Dart JSON reporter có test passed "[VTH-ST-01] plan rejects" nằm trong một group
    Khi chế độ tests chạy với --results nêu file, thư mục và file Dart
    Thì mọi định danh được chọn đều pass và lần chạy trả exit 0

  Kịch bản: [VTH-EC-06] [Tier C - Integration] Coverage gây hiểu nhầm bị từ chối kèm lý do
    Cho một định danh chỉ xuất hiện trong comment của một file test
    Và một định danh mà case duy nhất của nó bị skip
    Và một định danh có một case passed và một case failed
    Khi chế độ tests chạy với --results
    Thì định danh thứ nhất fail với "no test case in results", thứ hai với "skipped" và thứ ba với "failed in"
    Và lần chạy trả exit 1

  Kịch bản: [VTH-FR-02] [Tier C - Integration] Báo cáo không thuộc định dạng nào là lỗi cách gọi
    Cho một file results không bắt đầu bằng "<" hay "{"
    Khi chế độ tests chạy với --results nêu file đó
    Thì nó trả exit 2 và nêu tên file
```

## 6. UC-5 Gate 4 audit epic

```gherkin
Tính năng: audit_epic.py audit mọi task done và hiển thị mọi thay đổi grader

  Kịch bản: [VTH-HP-05] [Tier C - Integration] Một epic sạch qua được audit
    Cho một nhánh epic mà mỗi task done đều commit evidence pass cùng với code của nó
    Khi audit_epic.py chạy so với nhánh base
    Thì patch-id của commit mỗi task bằng patch_id của lần verify
    Và audit trả exit 0

  Kịch bản: [VTH-HP-10] [Tier C - Integration] Các mục hiển thị được liệt kê mà không làm fail audit
    Cho một task có dòng Verification bị sửa sau khi file task được tạo
    Và một commit trên nhánh epic không thuộc task nào mà đụng tới file ngoài .devtool
    Và một bullet Definition of Done đánh dấu "(Gate 5)"
    Và một task done mà commit của nó không có mục Verification
    Khi audit_epic.py chạy
    Thì báo cáo liệt kê sửa đổi kèm tiêu đề commit, commit ngoài task, mục Gate 5 và task legacy
    Và audit trả exit 0

  Kịch bản: [VTH-ST-08] [Tier C - Integration] Status done sửa bằng tay làm fail audit
    Cho một task có mục Verification mà status được đặt thành done bằng cách sửa frontmatter
    Và không có file evidence nào cho nó trên nhánh epic
    Khi audit_epic.py chạy
    Thì nó trả exit 1 và nêu việc task thiếu evidence

  Kịch bản: [VTH-ST-09] [Tier C - Integration] Thay đổi protected ngoài task fail khi ngoài .devtool và được hiển thị khi trong đó
    Cho một commit ngoài mọi task đổi "scripts/verify.sh", một protected path
    Và một commit doc sync thêm một scenario identifier vào bdd_scenarios.en.md
    Khi audit_epic.py chạy
    Thì nó trả exit 1 và nêu thay đổi ở scripts/verify.sh
    Và nó liệt kê định danh được thêm như một mục hiển thị

  Kịch bản: [VTH-AR-01] [Tier C - Integration] Nhánh base dịch chuyển làm đổi cây nhưng không đổi verdict
    Cho một nhánh epic được rebase lên một nhánh base đã dịch chuyển sau khi các task của nó được verify
    Khi lần rebase không có conflict và audit_epic.py chạy
    Thì mọi patch-id vẫn khớp và audit trả exit 0
    Khi việc giải conflict làm đổi patch của một task và audit_epic.py chạy
    Thì task đó được liệt kê là "patch changed after verify" và audit vẫn trả exit 0

  Kịch bản: [VTH-FR-03] [Tier C - Integration] Tham chiếu base không tồn tại là lỗi cách gọi
    Cho một tham chiếu base mà git không phân giải được
    Khi audit_epic.py chạy
    Thì nó trả exit 2 và nêu tên tham chiếu
```

## 7. UC-6 Văn bản skill nêu rõ hợp đồng

```gherkin
Tính năng: các skill và prompt nêu rõ hợp đồng mới mà agent nhận phải tuân theo

  Kịch bản: [VTH-HP-06] [Tier C - Integration] dev-designer nêu rõ hợp đồng task
    Cho skills/dev-designer/SKILL.md và references/verification-rows.md của nó
    Khi văn bản được đọc
    Thì template task nêu các mục Files, Verification, Definition of Done, Stop and Report If và Decisions Already Made
    Và nó yêu cầu mỗi định danh nằm trên dòng Covers của đúng một task
    Và Step 3 chạy check_task_contract.py --design cạnh plan
    Và verification-rows.md đưa lệnh sinh báo cáo cho Python, Android, Web, iOS, Rust và Flutter

  Kịch bản: [VTH-HP-07] [Tier C - Integration] dev-implementation nêu rõ recorder và gate
    Cho skills/dev-implementation/SKILL.md
    Khi văn bản được đọc
    Thì Phase 2 chạy run_task_checks.py red trước implementation và verify sau đó
    Và commit của task stage file evidence
    Và Phase 4 chạy audit_epic.py, các lệnh Integration results, tests --results và quality_check theo đúng thứ tự đó

  Kịch bản: [VTH-HP-08] [Tier C - Integration] dev-lifecycle và handoff template nêu rõ các quy tắc
    Cho skills/dev-lifecycle/SKILL.md và references/handoff-template.md của nó
    Khi văn bản được đọc
    Thì Gate 4 nêu audit và traceability dựa trên kết quả
    Và preflight đóng gói chạy check_task_contract.py --design
    Và các quy tắc handoff cấm sửa bảng Verification, Allowed files hay protected path

  Kịch bản: [VTH-HP-09] [Tier C - Integration] Các prompt SDD coi evidence, không phải prose, là bằng chứng
    Cho các prompt implementer và task reviewer của subagent-driven-development
    Khi văn bản được đọc
    Thì implementer chạy recorder và dẫn file evidence
    Và reviewer chạy run_task_checks.py status và coi thiếu evidence là Critical

  Kịch bản: [VTH-HP-13] [Tier C - Integration] Lựa chọn review được nêu ở đúng chỗ nó được hỏi
    Cho skills/dev-implementation/SKILL.md và skills/dev-lifecycle/SKILL.md
    Khi văn bản được đọc
    Thì dev-implementation hỏi Lựa chọn review, "Finish" hay "Cross-model review", sau task cuối
    Và developer chọn Claude CLI hoặc Codex CLI
    Và Phase 4 bắt đầu bằng run_external_review.py check khi có review_results.md
    Và Red Flags của dev-lifecycle nêu việc chọn CLI review thay developer
```

## 8. UC-7 Cả vòng đời chạy trọn từ đầu đến cuối

```gherkin
Tính năng: một task đi hết vòng đời trên một repo dùng một lần

  Kịch bản: [VTH-HP-11] [Tier C - Integration] Từ thiết kế tới audit, mọi bước trả exit 0
    Cho một repo git dùng một lần có HLD và một file task đúng hợp đồng
    Khi check_task_contract.py --design và plan chạy
    Và run_task_checks.py red chạy, thay đổi được thực hiện và run_task_checks.py verify chạy
    Và sync_task_status.py task done chạy và task được commit cùng evidence
    Và audit_epic.py chạy so với nhánh base
    Thì mọi lệnh đều trả exit 0
```

## 9. UC-8 Một model thứ hai review epic đã xong

```gherkin
Tính năng: run_external_review.py chạy CLI do developer chọn và ghi lại từng round

  Kịch bản: [VTH-HP-12] [Tier C - Integration] Một round review sạch được ghi lại
    Cho một worktree sạch của epic có mọi task đã done
    Và một "codex" giả trên PATH lưu stdin của nó và in "Verdict: PASS"
    Khi run_external_review.py run chạy với --cli codex --model gpt-test
    Thì nó trả exit 0
    Và prompt nó gửi nêu SHA ứng viên, base, thư mục evidence và checklist review
    Và review_results.md có thêm "## Round 1" với trạng thái completed, CLI codex, model gpt-test và verdict PASS

  Kịch bản: [VTH-EC-07] [Tier C - Integration] Chỉ có finding Minor thì không chặn
    Cho một "claude" giả in "Verdict: CHANGES REQUIRED" và một finding "[Minor]"
    Khi run_external_review.py run chạy với --cli claude
    Thì nó trả exit 0
    Và finding Minor được liệt kê trong bảng finding của round

  Kịch bản: [VTH-ST-10] [Tier C - Integration] Finding chặn giữ Phase 4 lại cho tới khi mỗi cái có Decision
    Cho một CLI giả in "Verdict: CHANGES REQUIRED" với một finding "[Critical]" và một finding "[Important]"
    Khi run_external_review.py run chạy
    Thì nó trả exit 1 và round liệt kê cả hai finding với Decision trống
    Khi run_external_review.py check chạy
    Thì nó trả exit 1 và nêu cả hai finding
    Khi cột Decision ghi "fixed in <sha>" cho một cái và "dismissed: <reason>" cho cái kia
    Và run_external_review.py check chạy
    Thì nó trả exit 0

  Kịch bản: [VTH-ST-11] [Tier C - Integration] Round hoàn tất mới nhất quyết định check
    Cho review_results.md có round 1 với một finding Critical chưa có Decision
    Và một round 2, hoàn tất mà không có finding chặn
    Và một round 3 được ghi là "no verdict"
    Khi run_external_review.py check chạy
    Thì nó trả exit 0 vì round 2 là round hoàn tất mới nhất
    Và round 1 và round 3 vẫn còn nguyên, không đổi

  Kịch bản: [VTH-FR-06] [Tier C - Integration] Thiếu CLI hoặc cây bẩn thì review dừng trước khi chạy
    Cho không có "claude" trên PATH
    Khi run_external_review.py run chạy với --cli claude
    Thì nó trả exit 2 và nêu CLI bị thiếu
    Và review_results.md không được tạo
    Cho thay vào đó một thay đổi chưa commit trong worktree
    Khi run_external_review.py run chạy
    Thì nó trả exit 2, yêu cầu cây sạch, và không ghi gì

  Kịch bản: [VTH-FR-07] [Tier C - Integration] Reviewer sửa cây thì bị loại
    Cho một CLI giả tạo một file trong repo và in "Verdict: PASS"
    Khi run_external_review.py run chạy
    Thì nó trả exit 2
    Và round được ghi là "discarded: tree modified", nêu file đã được tạo

  Kịch bản: [VTH-FR-08] [Tier C - Integration] CLI lỗi, im lặng hoặc chạy chậm thì ghi no verdict
    Cho một CLI giả trả exit 1 và in "credit balance is too low"
    Khi run_external_review.py run chạy
    Thì nó trả exit 2 và ghi round là "no verdict" kèm output của CLI
    Và điều tương tự xảy ra với CLI có output thiếu dòng Verdict, và với CLI chạy quá --timeout
```
