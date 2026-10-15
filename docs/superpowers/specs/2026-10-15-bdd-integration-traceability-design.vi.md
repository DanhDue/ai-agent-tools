# Thiết kế truy vết BDD sang integration test

- **Ngày**: 2026-10-15
- **Trạng thái**: Đã duyệt
- **Phạm vi**: `dev-designer`, `dev-implementation`, `dev-lifecycle`, script mới
  `dev-implementation/resources/scripts/check_bdd_traceability.py` cùng test của nó,
  `scripts/verify.sh`
- **Bước tiếp theo**: `writing-plans` (một implementation plan, không cần HLD)

## Mục lục

- [1. Bối cảnh](#1-bối-cảnh)
- [2. Mục tiêu và ngoài mục tiêu](#2-mục-tiêu-và-ngoài-mục-tiêu)
- [3. Quyết định](#3-quyết-định)
- [4. Scenario ID](#4-scenario-id)
- [5. Tham chiếu trong test](#5-tham-chiếu-trong-test)
- [6. Khai báo trong tài liệu thiết kế](#6-khai-báo-trong-tài-liệu-thiết-kế)
- [7. Script truy vết](#7-script-truy-vết)
- [8. Các điểm kiểm tra](#8-các-điểm-kiểm-tra)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Kiểm thử](#10-kiểm-thử)
- [11. Rủi ro và phụ thuộc](#11-rủi-ro-và-phụ-thuộc)
- [12. Ngoài phạm vi](#12-ngoài-phạm-vi)

## 1. Bối cảnh

Lifecycle epic đã cam kết "100% BDD-to-test traceability".
[dev-designer](../../../skills/dev-designer/SKILL.md) yêu cầu mọi scenario "map 1-to-1 or 1-to-N to an
automated test case", và [dev-implementation](../../../skills/dev-implementation/SKILL.md) cấm đánh
dấu task `done` khi chưa có 100% scenario được test pass. Không có gì kiểm tra cả hai cam kết đó.

Khảo sát các epic trong `.devtool/epic/` cho thấy cái giá phải trả:

- Scenario nằm ở hai tầng không bao giờ được nối với nhau: `bdd_scenarios.en.md` của epic — bản hợp
  đồng hành vi — và mục BDD SCENARIOS trong từng file task, gắn tag `[Tier A - Unit]` hoặc
  `[Tier C - Integration]`, không có định danh.
- Scenario ID chỉ xuất hiện ở một trong ba epic (11 trên 64 scenario), do agent tự đặt, với hai cách
  viết dimension khác nhau (`PY-HP-01`, `PY-EDGE-01`).
- Không test nào trong repo nhắc tới bất kỳ scenario ID nào.
- Coverage Matrix trong executive report của `quality_check` là code coverage, không phải scenario
  coverage.
- Scenario cấp epic được gắn tag mức unit chỉ có unit test dùng mock. Không có gì chứng minh hợp đồng
  hành vi của epic vẫn đúng khi các thành phần chạy cùng nhau.

Developer yêu cầu thêm một phần vào chuẩn BDD/TDD ba tier: automation integration test được map với
các BDD scenario, và **mỗi scenario map tới ít nhất một test**.

## 2. Mục tiêu và ngoài mục tiêu

**Mục tiêu:**

- Mọi scenario trong `bdd_scenarios.en.md` của epic được phủ bởi ít nhất một automation integration
  test.
- Việc mapping được một script kiểm tra bằng exit code, ở lúc thiết kế và lúc implementation.
- Gate 4 không thể xanh khi còn scenario chưa được phủ.
- Hoạt động giống nhau trên mọi nền tảng kit hỗ trợ: Web, Flutter, Android, iOS, Python, Rust.

**Ngoài mục tiêu:**

- Thay đổi `quality_check`, contract, schema của nó, hoặc bất kỳ provider nền tảng nào.
- Gherkin chạy trực tiếp và các framework BDD runner.
- Công việc không phải epic: `writing-plans` giữ nguyên.
- Bổ sung định danh cho các epic đã lưu trữ.
- Chứng minh rằng test thực sự kiểm tra đúng hành vi mà định danh của nó gọi tên.

## 3. Quyết định

| # | Quyết định | Lý do |
|---|------------|-------|
| D1 | Mọi scenario trong `bdd_scenarios.en.md` cấp epic cần ít nhất một automation integration test. Một test được phủ nhiều scenario | Yêu cầu của developer. "At least one" thay cho "1-to-1 or 1-to-N" ở mọi chỗ |
| D2 | Scenario `[Tier A - Unit]` cấp task vẫn giữ unit test, với cùng cách diễn đạt "at least one" | Unit coverage và integration coverage trả lời hai câu hỏi khác nhau; thay đổi này thêm cái thứ hai mà không bỏ cái thứ nhất |
| D3 | Không có miễn trừ. Scenario không tự động hóa được thì viết lại ở Gate 2 | Một danh sách miễn trừ sẽ dựng lại đúng cơ chế tự giác mà thay đổi này loại bỏ |
| D4 | Yêu cầu mới là phần bắt buộc của Tier C, tên là BDD Automation, không phải Tier D | Tier C vốn là tier integration; chuẩn ba tier giữ nguyên đánh số và mọi tham chiếu tới nó vẫn đúng |
| D5 | Scenario ID bắt buộc, ID nằm trong tên test, và một script kiểm tra (Phương án A) | Ma trận ghi tay (Phương án B) chính là cơ chế tự giác đã thất bại. Gherkin chạy trực tiếp (Phương án C) ép mỗi nền tảng một runner, và Swift chưa có runner đủ tốt |
| D6 | Kiểm tra chạy ngoài `quality_check`. Gate 4 trở thành: script truy vết exit 0 **và** `quality_check` trả PASS, cả hai trên cùng candidate SHA | Phase 4 của `dev-implementation` là nơi duy nhất gọi profile `epic`, nên kiểm tra ở đó chặt ngang kiểm tra cấp orchestrator mà không đổi contract nào. Phương án chép cùng một logic vào sáu provider bị loại |
| D7 | Script chỉ kiểm tra *hình dạng* định danh, và nhận diện scenario theo mọi từ khóa scenario của Gherkin, tiếng Anh hoặc tiếng Việt | Các epic hiện có đã dùng hơn một mã dimension, và file `.vi.md` dịch cả từ khóa (`Kịch bản:`) |
| D8 | Test nhắc tới một định danh không còn trong tài liệu làm kiểm tra đầy đủ thất bại | Buộc tài liệu và test luôn đồng bộ, cùng tinh thần với quy tắc "docs stay truthful" |

## 4. Scenario ID

Mọi dòng scenario trong khối `gherkin` của `bdd_scenarios.en.md` và `bdd_scenarios.vi.md` bắt đầu
bằng một định danh trong ngoặc vuông. Tag tier, nếu có, đứng sau nó:

```gherkin
Scenario: [PY-HP-01] [Tier C - Integration] Auto-detect Python workspace and scaffold manifest
```

- **Từ khóa scenario được nhận diện:** `Scenario`, `Scenario Outline`, `Scenario Template`, `Example`,
  `Tình huống`, `Kịch bản`, `Khung tình huống`, `Khung kịch bản`.
- **Hình dạng:** các đoạn chữ hoa và số nối bằng `-`, kết thúc bằng một dãy số —
  `[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+`. Quy ước khuyến nghị: `<EPIC>-<DIM>-<NN>` với `HP`, `EC`, `ST`,
  `AR`, `FR` cho năm dimension. Script không ép quy ước này.
- **Tính duy nhất:** mỗi định danh xuất hiện một lần trong tài liệu.
- **Đồng bộ ngôn ngữ:** `bdd_scenarios.vi.md` mang đúng cùng tập định danh. Định danh không bao giờ
  được dịch.
- **Prefix:** đoạn đầu tiên. Mọi định danh cùng prefix thuộc epic này, và không epic nào khác trong
  project được dùng lại nó: các thư mục integration test chứa test của mọi epic, nên một prefix dùng
  chung sẽ khiến test của epic này phủ nhầm — hoặc bị coi là stale — đối với epic kia. Prefix là thứ
  mà kiểm tra stale tìm kiếm (§7).

## 5. Tham chiếu trong test

Một integration test phủ một định danh khi định danh đó xuất hiện trong một file test nằm dưới một
trong các thư mục integration test đã khai báo (§6) — ở tên test, mô tả hoặc tag. Việc so khớp không
phân biệt hoa thường, coi `-` và `_` là như nhau, và yêu cầu không có chữ cái hay chữ số nào đứng sát
ngay trước hoặc ngay sau chuỗi khớp. Nhờ vậy mỗi nền tảng dùng được cách viết quen thuộc của nó:

| Nền tảng | Ví dụ |
|----------|-------|
| Python | `def test_py_hp_01_scaffold_manifest():` |
| Rust | `fn py_hp_01_scaffold_manifest()` |
| Flutter | `testWidgets('[PY-HP-01] scaffolds the manifest', ...)` |
| Web | `test('[PY-HP-01] scaffolds the manifest', ...)` |
| iOS | `@Test("[PY-HP-01] scaffolds the manifest")` |
| Android | ``@Test fun `PY-HP-01 scaffolds the manifest`()`` |

- Một test có thể mang nhiều định danh; mỗi định danh cần ít nhất một test (D1).
- File markdown dưới các thư mục này bị bỏ qua, và file không phải UTF-8 hợp lệ cũng vậy.
- **Tham chiếu stale (D8)** chỉ được phát hiện ở dạng chuẩn — một token viết hoa, có gạch nối, khớp
  `<PREFIX>(-[A-Z0-9]+)*-[0-9]+` mà không phải định danh trong tài liệu. Dạng snake_case và chữ thường
  được tính cho coverage nhưng không tính cho stale: trong `test_py_hp_01_retry_2`, script không phân
  biệt được định danh kết thúc ở đâu và tên test bắt đầu ở đâu, và một prefix ngắn như `PY` sẽ bắt
  nhầm những chuỗi chữ thường không liên quan như `py-3`.

## 6. Khai báo trong tài liệu thiết kế

`dev-designer` thêm ba thứ vào các tài liệu nó vốn đã viết.

1. **Thư mục integration test.** Mục Integration Test Plan của HLD có thêm một dòng bắt buộc, ở cả
   hai bản ngôn ngữ:

   ```text
   Integration test roots: tests/integration/, tests/e2e/
   ```

   Giá trị mặc định theo nền tảng lấy từ danh sách sẵn có ở Rule 2 về chạy song song của
   dev-designer: `tests/e2e/` cho Web, `integration_test/` cho Flutter, `app/src/test/` và
   `shell/src/test/` cho Android, `App/Tests/` và `Shell/Tests/` cho iOS, `tests/integration/` cho
   Python, `tests/` cho Rust.
2. **`Covers:` trong file task.** Mục BDD SCENARIOS của mỗi task có thêm một dòng liệt kê các định
   danh scenario cấp epic mà task đó phải viết integration test:

   ```text
   Covers: PY-HP-01, PY-EDGE-02
   ```

   Task không có scenario cấp epic nào — ví dụ một task tooling Tier B — thì bỏ dòng này. Mọi định
   danh phải xuất hiện trong `Covers:` của ít nhất một task. Task Tier C cuối cùng thường nhận các
   định danh mà chưa task nào trước đó phủ.
3. **Bản tóm tắt ở Gate 2.** Checkpoint chia task liệt kê mỗi task đề xuất cùng các định danh
   `Covers:` của nó, để developer duyệt mapping cùng lúc với cách chia task.

## 7. Script truy vết

`skills/dev-implementation/resources/scripts/check_bdd_traceability.py`, chỉ dùng thư viện chuẩn, có
`test_check_bdd_traceability.py` đi kèm theo kiểu `unittest` của các script cùng thư mục.

```bash
check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]
```

`--roots` và `--ids` nhận giá trị phân tách bằng dấu cách hoặc dấu phẩy, nên có thể chép nguyên văn
dòng roots của HLD và dòng `Covers:` của task.

**Cả hai chế độ** đều kiểm tra tài liệu scenario trước: mọi dòng scenario có định danh, mọi định danh
đúng hình dạng và chỉ xuất hiện một lần, và — khi có file `.vi.md` đi kèm — hai tập định danh bằng
nhau.

**Chế độ `plan`** đọc mọi dòng `Covers:` trong các file task được truyền vào, kể cả dạng mục danh sách
và dạng in đậm (`- **Covers**: ...`). Nó thất bại khi có định danh không thuộc task nào, hoặc khi một
dòng `Covers:` nêu định danh mà tài liệu không có.

**Chế độ `tests`** duyệt các thư mục và thất bại khi có định danh không được file nào phủ. Với
`--ids`, nó chỉ kiểm tra các định danh đó và bỏ qua kiểm tra stale, để lần chạy theo từng task không bị
công việc của task khác chặn. Không có `--ids`, nó chạy thêm kiểm tra stale (§5).

Thư mục chưa tồn tại được báo dưới dạng cảnh báo và bị bỏ qua; định danh chưa được phủ vẫn làm lần chạy
thất bại.

**Output:** ma trận từ định danh tới task phủ nó (`plan`) hoặc tới `file:line` (`tests`), ghi `(none)`
ở chỗ chưa được phủ, kèm một dòng tổng kết:

```text
PY-HP-01    tests/integration/test_scaffold.py:12
PY-HP-02    (none)
Result: 10/11 covered — FAIL
```

**Exit code:** `0` là phủ đủ; `1` là lỗi truy vết — định danh chưa phủ, stale, lạ, thiếu, sai hình
dạng, trùng hoặc lệch; `2` là lỗi sử dụng, ví dụ thiếu file scenario hoặc file task, hoặc không thư mục
nào tồn tại.

`dev-designer` và `dev-lifecycle` gọi script qua thư mục skill của chính chúng, giống cách
`dev-implementation` đang làm với `integrate_branch.py`:

```bash
TRACE="$SKILL_DIR/../dev-implementation/resources/scripts/check_bdd_traceability.py"
```

## 8. Các điểm kiểm tra

| Ở đâu | Kiểm tra |
|-------|----------|
| `dev-designer`, sau khi Step 2 ghi các file task và trước commit Step 3 | `plan` trên `.devtool/epic/<epic_dir>/task_*.md` — các bản mirror của chính epic, không bao giờ dùng `.devtool/features/` vì nơi đó có thể chứa task của epic khác — phải exit 0 |
| `dev-designer`, chuẩn ba tier | Một đoạn dùng chung cho mọi nền tảng, "Tier C — BDD Automation", đặt sau danh sách tier theo nền tảng; các khối theo nền tảng giữ nguyên |
| `dev-designer`, template task | Mục BDD SCENARIOS mô tả dòng `Covers:`; Zero Uncovered Scenarios Rule dùng cách diễn đạt "at least one" |
| `dev-implementation`, quy tắc truy vết dùng chung sau các khối Tri-Persona | Integration persona viết ít nhất một integration test cho mỗi định danh trong `Covers:` của task, với định danh nằm trong tên hoặc mô tả test. Áp dụng cho cả sáu nền tảng mà không phải sửa từng khối |
| `dev-implementation`, Gate to Done của mỗi task | `tests --ids <Covers của task>` exit 0 |
| `dev-implementation`, Phase 4 | `tests` đầy đủ exit 0 **trước** khi chạy `quality_check`; thất bại thì quay lại Phase 2. Ma trận là một phần của báo cáo Gate 5 |
| `dev-lifecycle`, Gate 4 | Người duyệt trở thành "`check_bdd_traceability.py` + `quality_check`". Gate 4 chỉ 🟢 khi script exit 0 và `quality_check` trả PASS trên cùng SHA. Quy tắc candidate immutability áp dụng cho cả hai: commit mới làm cả hai hết hiệu lực |

## 9. Xử lý lỗi

| Lỗi | Chặn bằng |
|-----|-----------|
| Scenario không có định danh, hoặc định danh sai hình dạng hay bị trùng | Cả hai chế độ thất bại trước khi kiểm tra coverage |
| Định danh của `.vi.md` lệch khỏi `.en.md` | Kiểm tra đồng bộ ngôn ngữ |
| Một định danh không được giao cho task nào | `plan` thất bại trước commit thiết kế |
| Dòng `Covers:` nêu định danh đã xóa hoặc gõ sai | `plan` thất bại |
| Một định danh không có integration test | `tests --ids` theo từng task ở Gate to Done; `tests` đầy đủ ở Phase 4 và Gate 4 |
| Test vẫn nhắc tới scenario đã bị xóa khỏi tài liệu | Kiểm tra stale của `tests` đầy đủ |
| Thư mục đã khai báo chưa tồn tại, khi chưa có integration test nào được viết | Cảnh báo nêu đường dẫn; chỉ exit 2 khi không thư mục nào tồn tại. Task tạo ra thư mục chạy kiểm tra của nó sau khi tạo |
| Epic thiết kế trước thay đổi này không có định danh | Cả hai chế độ thất bại ngay ở dòng scenario đầu tiên. Khi tiếp tục, định danh và dòng `Covers:` được bổ sung ở Gate 3, trước khi chạy task nào |
| Gate 4 được cấp chỉ dựa trên `quality_check` | Red Flag trong `dev-lifecycle`: "Granting Gate 4 without a passing traceability check on the same SHA" |

## 10. Kiểm thử

1. Unit test trong `test_check_bdd_traceability.py`, mỗi tình huống có fixture riêng trong thư mục tạm:
   - kiểm tra tài liệu: thiếu định danh, sai hình dạng, trùng, tập định danh của `.vi.md` lệch, nhận
     diện từ khóa tiếng Việt, chấp nhận tag tier đứng sau định danh, bỏ qua dòng scenario nằm ngoài
     khối `gherkin`;
   - `plan`: phủ đủ; một định danh không thuộc task nào; một định danh lạ trong `Covers:`; các dạng
     `Covers:` kiểu mục danh sách và in đậm;
   - `tests`: tham chiếu dạng gạch nối, snake_case và chữ thường đều được tính; dãy số dài hơn không
     khớp (`PY-HP-010` không phủ `PY-HP-01`); file `.md` bị bỏ qua; `--ids` giới hạn phạm vi và bỏ qua
     stale; tham chiếu stale dạng gạch nối làm lần chạy đầy đủ thất bại; một thư mục thiếu thì cảnh
     báo trong khi các thư mục khác vẫn được quét; không thư mục nào tồn tại thì exit 2.
2. `scripts/verify.sh` chạy file test mới và đạt.
3. Chạy thử `tests` trên `.devtool/epic/python_quality_provider_and_onboarding/`: tài liệu hợp lệ và
   script báo 11 định danh chưa được phủ — đúng lỗ hổng mà thay đổi này lấp lại.
4. Quality gate là `@quality_check`, vì script và các file `SKILL.md` được phát hành trong plugin. Plan
   làm theo `writing-skills` khi sửa skill và `test-driven-development` khi viết script.

## 11. Rủi ro và phụ thuộc

- **Có tên mà không có thực chất.** Một test có thể mang định danh mà không kiểm tra hành vi đó. Script
  chứng minh mapping tồn tại, không chứng minh nó có ý nghĩa; spec review trong
  `subagent-driven-development` và việc developer review ở Gate 5 đánh giá điều đó.
- **Chi phí integration test.** Scenario async và race chậm hơn và dễ vỡ hơn khi viết thành
  integration test. Chấp nhận được: đây là yêu cầu rõ ràng của developer.
- **Trùng chuỗi ngẫu nhiên.** Một định danh có thể xuất hiện trong một chuỗi không liên quan. Quy tắc
  ranh giới ở §5 làm việc này khó xảy ra; một lần khớp nhầm chỉ làm báo thiếu một lỗ hổng, không bao
  giờ chặn.
- **Liên quan tới spec bàn giao epic.** Nếu
  [2026-10-15-epic-handoff-choice-design.vi.md](2026-10-15-epic-handoff-choice-design.vi.md) cũng được
  triển khai, preflight đóng gói của nó nên chạy thêm `plan`. Plan nào được triển khai sau sẽ thêm
  bước đó.

## 12. Ngoài phạm vi

- Mọi thay đổi với `quality_check`, contract, schema hay executive report của nó, và với các provider
  nền tảng.
- Gherkin chạy trực tiếp, BDD runner, và Tier D.
- `writing-plans` và các công việc không phải epic.
- Bổ sung định danh cho các epic đã lưu trữ.
- Xác minh rằng assertion của test khớp với scenario của nó.
