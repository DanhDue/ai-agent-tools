# Thiết kế gia cố xác minh cơ học và tinh gọn lifecycle

- **Ngày**: 2026-10-19
- **Trạng thái**: Bản nháp chờ duyệt Gate 1
- **Phạm vi**: Xác minh cơ học trong `dev-implementation`, tinh gọn runtime skill, tài liệu
  lifecycle cho con người và regression coverage
- **Bước tiếp theo sau khi duyệt**: `dev-designer` (phân rã task quy mô epic)

## Mục lục

- [1. Bối cảnh](#1-bối-cảnh)
- [2. Mục tiêu và ngoài mục tiêu](#2-mục-tiêu-và-ngoài-mục-tiêu)
- [3. Phạm vi](#3-phạm-vi)
- [4. Quyết định thiết kế](#4-quyết-định-thiết-kế)
- [5. Tính toàn vẹn của pytest RED](#5-tính-toàn-vẹn-của-pytest-red)
- [6. Tính toàn vẹn của Python TIER-B](#6-tính-toàn-vẹn-của-python-tier-b)
- [7. Ranh giới chính sách test integrity](#7-ranh-giới-chính-sách-test-integrity)
- [8. Tinh gọn lifecycle skill](#8-tinh-gọn-lifecycle-skill)
- [9. Tài liệu lifecycle cho con người](#9-tài-liệu-lifecycle-cho-con-người)
- [10. Xác minh và kiểm thử](#10-xác-minh-và-kiểm-thử)
- [11. Xử lý lỗi](#11-xử-lý-lỗi)
- [12. Rủi ro và phụ thuộc](#12-rủi-ro-và-phụ-thuộc)
- [13. Cấu trúc bàn giao](#13-cấu-trúc-bàn-giao)

## 1. Bối cảnh

Workflow `dev-implementation` ghi các lệnh RED và verification của task thành evidence đã commit,
sau đó audit evidence ở Gate 4. Hai khoảng trống cho phép agent thỏa hình thức của contract mà không
chứng minh hành vi mong muốn:

- Một pytest RED row có `expect: exit non-zero` có thể trỏ tới file không tồn tại (pytest exit 4)
  hoặc không chọn test nào (pytest exit 5).
- Một Python task có thể tuyên bố lint và type safety trong Definition of Done trong khi các row
  `TIER-B` chỉ chạy `ruff check`.

Phần prose bao quanh các kiểm tra này cũng đã phình to. `dev-implementation/SKILL.md` hiện khoảng
7.744 từ và `dev-lifecycle/SKILL.md` khoảng 3.990 từ. Cả hai chứa diagram hoặc chi tiết nền tảng đã có
trong lifecycle documentation, các implementation skill được ủy quyền hoặc quality provider đã đăng
ký. Thêm nhiều prohibition vào runtime skill làm tăng gánh nặng chú ý của model nhỏ mà không biến
quy tắc thành ràng buộc cơ học.

Vì vậy thiết kế này coi gia cố và tinh gọn là một thay đổi độ tin cậy duy nhất: script sở hữu invariant
xác định được, provider sở hữu verification đặc thù nền tảng, runtime skill chỉ giữ orchestration và
quyết định của con người, còn diagram cho con người nằm trong tài liệu bền vững.

## 2. Mục tiêu và ngoài mục tiêu

**Mục tiêu:**

- Từ chối pytest RED giả cả lúc ghi evidence và lúc audit evidence đã commit.
- Yêu cầu Python `TIER-B` chứng minh cả linting lẫn type checking.
- Để audit tự tính lại tính hợp lệ của RED thay vì tin trường `PASS` đã ghi.
- Nêu quy tắc production-code và real-artifact test integrity mà không tuyên bố sai rằng đã có
  enforcement cơ học đa ngôn ngữ.
- Giảm cognitive load của runtime skill mà không bỏ entry-point recovery, approval gate, exact
  validator command hay fail-closed behavior.
- Giữ lifecycle diagram và giải thích cho developer trong cặp tài liệu tiếng Anh và tiếng Việt hiện
  có.
- Thêm regression coverage bền vững cho mọi quy tắc cơ học mới và cho việc tách skill/document.

**Ngoài mục tiêu:**

- Xây một AST analyzer dùng chung cho Python, Dart, Kotlin, Swift, Rust và TypeScript.
- Thêm capability provider mới `test_integrity` hoặc đổi schema của quality provider trong epic này.
  Việc đó cần một thiết kế riêng tập trung vào provider.
- Ký task evidence bằng mật mã. Agent có thể sửa cả evidence lẫn verifier thì không thể bị chặn bằng
  chữ ký nằm trong repository nếu không có trust boundary bên ngoài.
- Viết lại trình tự lifecycle, đổi quyền sở hữu gate hay làm yếu bất kỳ user approval nào.
- Tạo thêm lifecycle overview document trong khi `docs/lifecycles.en.md` và `.vi.md` đã đảm nhiệm vai
  trò đó.

## 3. Phạm vi

Developer đã mở rộng rõ ràng phạm vi bốn file ban đầu trong quá trình phân tích Gate 1. Phạm vi thiết
kế được duyệt gồm:

**Xác minh cơ học:**

- `skills/dev-implementation/resources/scripts/run_task_checks.py`
- `skills/dev-implementation/resources/scripts/audit_epic.py`
- `skills/dev-implementation/resources/scripts/check_task_contract.py`
- Ba file regression test nằm cạnh các script trên

**Tinh gọn runtime skill và policy:**

- `skills/dev-implementation/SKILL.md`
- `skills/dev-lifecycle/SKILL.md`

**Tài liệu cho con người và kiểm tra chống drift:**

- `docs/lifecycles.en.md`
- `docs/lifecycles.vi.md`
- `scripts/test_lifecycle_document_contract.py`

Epic này không sửa provider skill, provider schema, quality orchestrator chung hay lifecycle document
không liên quan.

## 4. Quyết định thiết kế

| # | Quyết định | Lý do |
|---|------------|-------|
| D1 | Dùng allowlist cho exit code của pytest RED: chỉ 1 hoặc 2 được xét hợp lệ | Denylist chỉ gồm 4 và 5 vẫn để lộ internal error, command-not-found wrapper và các failure không phải hành vi |
| D2 | Áp dụng negative output marker và yêu cầu bằng chứng dương về pytest failure | Wrapper có thể đổi exit code; ngữ nghĩa output cung cấp tín hiệu độc lập thứ hai |
| D3 | Gate 4 tính lại tính hợp lệ của pytest RED từ task row và evidence record | Evidence cũ hoặc bị sửa không được qua chỉ vì ghi `outcome: PASS` |
| D4 | Đọc command lint và type-check Python từ capability manifest đã đăng ký khi có, kèm fallback tool được nhận diện | Provider manifest là nguồn sự thật của project; fallback hỗ trợ project chưa đăng ký mà không chấp nhận riêng `ruff` |
| D5 | Nhận diện Python từ evidence cục bộ của task, không chỉ từ `pyproject.toml` cấp repository | Repository polyglot không được biến mọi task thành Python task |
| D6 | Giữ test integrity đa ngôn ngữ thành quy tắc review Gate 4 bắt buộc nhưng không gọi là hoàn tất cơ học | Phân tích import/call và artifact provenance đáng tin cậy là đặc thù ngôn ngữ và thuộc provider |
| D7 | Bỏ diagram và procedure nền tảng trùng lặp khỏi runtime skill | Đây là giải thích cho con người hoặc chi tiết provider sở hữu, không phải executable agent contract |
| D8 | Dùng lại cặp song ngữ `docs/lifecycles.*.md` làm nơi phục vụ con người | Tránh nguồn lifecycle diagram thứ ba và giữ parity Anh/Việt |
| D9 | Bảo vệ gate và recovery rule bằng positive contract test thay vì giữ prose trùng lặp | Skill ngắn hơn chỉ an toàn khi invariant bắt buộc vẫn được assert cơ học |

## 5. Tính toàn vẹn của pytest RED

### 5.1 Nhận diện lệnh pytest

Một RED row gọi pytest khi shell tokenization nhận diện một trong các dạng sau, gồm cả executable path
có basename khớp:

- `pytest`
- `python -m pytest` hoặc `python3 -m pytest`
- wrapper môi trường phổ biến như `uv run pytest`, `poetry run pytest` hoặc `pipenv run pytest`

Nhận diện theo token tránh tính nhầm text không liên quan như `echo pytest`. Shell syntax không hợp lệ
vốn đã là command failure và không thể được tính là pytest RED hợp lệ.

### 5.2 Verdict lúc ghi evidence

Sau khi pytest RED command kết thúc, `run_task_checks.py` đánh giá toàn bộ stdout/stderr đã gộp.
Record là `FAIL` khi có bất kỳ điều kiện nào sau đây:

- Exit code không phải 1 hoặc 2, gồm exit 4 và 5.
- Output khớp `ERROR: file or directory not found`.
- Output khớp `collected 0 items`.
- Output khớp `/ 0 selected` với whitespace linh hoạt và không phân biệt hoa thường.
- Output không có positive failure summary, chẳng hạn số lượng test failed hoặc error lớn hơn 0.

Quy tắc fail-closed `collected 0 items` cố ý từ chối một số import error lúc collection. Khi import
failure là hành vi cần test, test phải được collect rồi thực hiện import trong test body, tạo assertion
hoặc test error thay vì dựa vào zero collection. Cách này loại bỏ mơ hồ giữa import contract thật và
test selection rỗng.

Mọi trường hợp từ chối dùng nguyên văn reason bắt buộc:

```text
Invalid pytest RED phase: must fail on a collected test (exit 1 or 2), not missing file (exit 4) or zero selected tests (exit 5).
```

Reason được ghi vào evidence, in trong row result và làm recorder exit 1.

### 5.3 Verdict audit ở Gate 4

`audit_epic.py` tìm evidence record của mọi pytest RED row và chạy lại cùng semantic validation trên
các field đã commit:

- command và phase đã ghi;
- exit code đã ghi;
- output tail đã ghi;
- outcome đã ghi.

Kết quả sai ngữ nghĩa thêm reason bắt buộc vào mục Evidence và làm Gate 4 fail, kể cả khi JSON outcome
ghi `PASS`. Pytest summary được kỳ vọng ở cuối output nên evidence tail hiện có chứa positive và
negative marker mà audit cần.

Recorder và audit dùng chung một pure validator để tránh lệch quy tắc. Audit vẫn sở hữu finding và
failure status cuối cùng của Gate 4; nó không chỉ lặp lại outcome đã ghi.

## 6. Tính toàn vẹn của Python TIER-B

### 6.1 Nhận diện Python task

Một task liên quan Python khi contract của chính nó có ít nhất một tín hiệu cục bộ:

- Allowed file là Python source hoặc tên file project Python như `.py`, `pyproject.toml`, `setup.py`
  hay `requirements.txt`.
- Verification row gọi pytest, ruff, mypy, pyright hoặc ty.
- `TIER-B` row gọi command đã đăng ký trong `.agents/quality/python-quality.json`.

Chỉ có Python file ở repository root là chưa đủ.

### 6.2 Capability TIER-B bắt buộc

Với Python task, toàn bộ `TIER-B` rows được xét cùng nhau và phải trực tiếp gọi:

- một linter; và
- một type checker.

Fallback tool được nhận diện là `ruff` cho linting và `mypy`, `pyright` hoặc `ty` cho type checking.
Dạng wrapper và `python -m <tool>` được nhận diện qua shell token thay vì substring matching.

Khi `.agents/quality/python-quality.json` tồn tại, validator đọc `capabilities.lint` và
`capabilities.type_check`. Một row chỉ thỏa capability đã đăng ký khi normalized command trực tiếp gọi
registered argument sequence. Không suy đoán generic shell script có gọi type checker bên trong.

Không phụ thuộc các Python signal khác, bất kỳ `TIER-B` row nào gọi ruff cũng kích hoạt yêu cầu type
checker. Thiếu lint hoặc type-check coverage là contract problem và làm `check_task_contract.py` exit
1 trước khi Gate 2 hoặc Gate 3 có thể pass.

Registered capability JSON sai được báo thành contract problem thay vì âm thầm fallback. Manifest bị
thiếu dùng recognized-tool fallback vì registration không phải prerequisite của task design trong mọi
consuming repository.

## 7. Ranh giới chính sách test integrity

`dev-implementation/SKILL.md` giữ hai quy tắc Gate 4 ngắn gọn:

- **Không dựng lại logic trong test**: unit và integration test import và gọi production function
  hoặc class thật từ Allowed files của task. Viết lại retry wrapper, progress math hoặc config
  resolution trong test là Gate 4 failure.
- **Artifact thật bất biến**: test kiểm tra repository artifact thật phải copy input vào temporary
  directory của test trước khi chạy và giữ nguyên anchor value của scenario trừ khi scenario cho phép
  rõ ràng việc thay bằng synthetic data.

Đây là yêu cầu semantic review. Platform provider và specialist audit phải báo vi phạm phát hiện được
là `FAIL`, khiến aggregated quality verdict fail. Epic này không thêm required provider-result field
chứng minh check đã chạy, nên tài liệu không được mô tả hai quy tắc là enforcement cơ học hoàn chỉnh.

Một provider epic tiếp theo có thể thêm capability `test_integrity` bắt buộc với implementation đặc
thù ngôn ngữ. Cho tới lúc đó, universal script chỉ enforce những gì suy ra đáng tin cậy từ command,
exit, output, evidence và task contract.

## 8. Tinh gọn lifecycle skill

### 8.1 `dev-lifecycle/SKILL.md`

Runtime orchestrator giữ:

- Quyền sở hữu stage và routing.
- Năm gate cùng approver.
- Handoff Choice và packaging command.
- Gate 4 acceptance và Review Choice loop.
- Resume routing, failure routing và user STOP point.
- Bilingual document contract ở mức cần để route công việc.

Nó bỏ:

- Mermaid lifecycle diagram đã có trong `docs/lifecycles.*.md`.
- Tutorial viết Mermaid và Graphviz chi tiết; thay vào đó durable document phải pass contract
  `doc_quality_check` hiện có.
- Prose và red flag lặp lại một hard gate có sẵn mà không thêm stop condition riêng.

Mục tiêu tối đa 2.500 từ, với điều kiện giữ mọi lifecycle invariant đã được assert cơ học.

### 8.2 `dev-implementation/SKILL.md`

Implementation orchestrator giữ:

- Epic resolution, Entry-Point Detection và Resume Procedure.
- Gate 3 và exact preflight command.
- Per-task status, RED/verify/status evidence command, commit và integration sequence.
- Gate 4, Review Choice, Gate 5 và handoff hoàn tất nhánh.
- Non-mechanical STOP condition như semantic merge conflict và user decision.

Nó bỏ:

- Mermaid process diagram.
- Các Tri-Persona prompt block Flutter, Android, iOS, Web và Rust lặp lại.
- Platform-specific Quick Reference table bỏ sót Python, Rust và Web.
- Common Mistakes và Red Flags trùng nhau sau khi hợp nhất unique stop condition.
- Platform command đã thuộc registered provider hoặc required sub-skill.

Tri-Persona block được thay bằng platform-neutral dispatch contract cung cấp task, Allowed files, HLD,
Covers identifier, integration roots, yêu cầu TDD và registered provider context. Mục tiêu tối đa 4.500
từ, vẫn phụ thuộc điều kiện giữ nguyên behavior đã assert.

Cả hai runtime skill liên kết thụ động tới human lifecycle overview; link không yêu cầu agent load tài
liệu trong execution bình thường.

## 9. Tài liệu lifecycle cho con người

Cặp lifecycle document tiếng Anh và tiếng Việt hiện có trở thành nơi duy nhất chứa lifecycle diagram.
Tiếng Anh vẫn canonical; tiếng Việt giữ cùng cấu trúc và sự kiện.

Mục `dev-lifecycle` chứa:

- Diagram end-to-end từ Stage 1 tới Stage 4.
- Five-gate matrix ngắn gọn.
- Các nhánh Handoff Choice.
- Vòng Gate 4 → Review Choice → Gate 5 hoặc cross-model review.
- State diagram interrupted/resume giải thích trạng thái fresh, packaged, interrupted, completed và
  inconsistent.
- Artifact tạo ra ở mỗi stage.

Không lặp lại provider internals. Tài liệu liên kết tới các trang kiến trúc quality-provider song ngữ
hiện có để xem chi tiết đó.

Tài liệu nói rõ nó mô tả lifecycle cho con người, còn runtime skill và script là operational source of
truth.

## 10. Xác minh và kiểm thử

### 10.1 Mechanical regression test

Các unit test nằm cạnh script thêm case cho:

- pytest exit 4 và 5;
- từng forbidden output marker;
- wrapper đổi pytest failure thành exit 1;
- exit 1 không có positive failure evidence;
- evidence exit 1 hợp lệ và exit 2 được phép;
- audit từ chối committed evidence có outcome bị đổi thành `PASS`;
- Python `TIER-B` chỉ có ruff bị từ chối;
- command mypy, pyright và ty được nhận diện;
- registered custom lint và type-check command;
- manifest sai và polyglot task không có Python signal cục bộ.

Test tạo repository và command dùng một lần; chúng không phụ thuộc pytest được cài trong kit checkout.

### 10.2 Lifecycle document contract

`scripts/test_lifecycle_document_contract.py` kiểm tra thêm:

- Runtime lifecycle skill không chứa Mermaid hoặc DOT fenced block.
- Cả hai lifecycle document chứa diagram mong đợi.
- Document tiếng Anh và tiếng Việt giữ invariant Gate 4, Review Choice, Gate 5 và cross-model rerun.
- Runtime skill giữ required gate, evidence, resume và approval token sau khi tinh gọn.

Document quality checker xác minh cả lifecycle document lẫn cặp design mới về mục lục, cấu trúc song
ngữ, link, Markdown và diagram syntax.

### 10.3 Skill behavior test

Trước và sau khi tinh gọn, cùng một nhóm pressure scenario bao phủ:

- entry của epic fresh so với interrupted;
- từ chối tạo worktree trước Gate 3;
- một pytest RED command giả;
- Gate 4 PASS theo sau bởi Review Choice;
- cross-model review quay lại Gate 4 đầy đủ;
- Gate 5 từ chối archive trước user approval.

Skill rút gọn chỉ pass khi behavior được giữ hoặc cải thiện. Mechanical repository test là regression
gate bền vững; model sample là evidence bổ sung, không thay thế.

Verification cuối chạy targeted unit suite, sau đó `scripts/verify.sh` và registered quality gate phù
hợp với thay đổi code và skill.

## 11. Xử lý lỗi

| Lỗi | Verdict và hành động |
|-----|----------------------|
| Pytest RED exit ngoài 1 hoặc 2 | Recorder `FAIL`; audit `FAIL` với reason bắt buộc |
| Pytest RED chứa forbidden marker zero-test hoặc missing-file | Recorder `FAIL`; audit `FAIL` với reason bắt buộc |
| Pytest RED không có positive failure summary | Recorder và audit fail closed |
| Python task không có `TIER-B` linter | Task contract `FAIL` |
| Python task không có `TIER-B` type checker | Task contract `FAIL` |
| Registered Python manifest sai | Task contract `FAIL`, nêu rõ lỗi manifest |
| Runtime skill mất lifecycle invariant khi tinh gọn | Lifecycle contract regression test `FAIL` |
| Human diagram mất required edge hoặc một ngôn ngữ bị drift | Lifecycle/document contract `FAIL` |
| Provider phát hiện test logic dựng lại hoặc artifact substitution | Provider `FAIL`; aggregated Gate 4 `FAIL` |
| Provider chưa có mechanical test-integrity capability | Epic này không tuyên bố hoàn chỉnh cơ học; follow-up vẫn được nêu rõ |

## 12. Rủi ro và phụ thuộc

- **Pytest output đa dạng**: plugin có thể đổi summary. Positive pattern phải cover output pytest
  concise và verbose chuẩn mà không chấp nhận empty run. Output lạ fail closed và yêu cầu task author
  dùng reporting form được hỗ trợ.
- **Shell phức tạp**: không thể diễn giải tĩnh mọi shell program. Nhận diện theo token cộng runtime
  output validation cover direct invocation được hỗ trợ; wrapper script cố tình opaque không được
  tính là bằng chứng trực tiếp.
- **Sửa evidence**: semantic recomputation bắt field không nhất quán nhưng không thể cung cấp
  cryptographic provenance nếu thiếu external trust boundary.
- **Tinh gọn quá mức**: xóa recovery hoặc approval instruction duy nhất có thể làm yếu lifecycle.
  Positive contract test và pressure scenario trước/sau bảo vệ invariant được giữ.
- **Documentation drift**: chuyển diagram tạo representation thứ hai của runtime behavior. Kiểm tra
  song ngữ lấy tiếng Anh làm canonical và semantic invariant test giới hạn rủi ro đó.
- **Provider follow-up**: enforcement test integrity đa ngôn ngữ đầy đủ phụ thuộc provider contract
  và language-specific analyzer trong tương lai.

## 13. Cấu trúc bàn giao

Đây là một epic có hai work package theo thứ tự:

1. **Gia cố xác minh cơ học**: test trước, sau đó recorder, audit, task-contract validation và policy
   test integrity ngắn gọn.
2. **Tinh gọn lifecycle và loại bỏ tài liệu trùng lặp**: contract test trước, sau đó giảm runtime skill
   và đồng bộ human documentation.

Gia cố cơ học land trước để phần prose được giảm sau đó có thể trỏ tới enforcement chạy được. Hai
package vẫn là hai task group và commit riêng. Gate 4 chỉ chạy sau khi cả hai hoàn tất và verify toàn
bộ candidate SHA cuối cùng.
