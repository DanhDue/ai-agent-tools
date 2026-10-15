# Thiết kế các điểm vá tiếp theo của lifecycle

- **Ngày**: 2026-10-15
- **Trạng thái**: Đã duyệt
- **Phạm vi**: `check_bdd_traceability.py` cùng test của nó, `dev-designer`, `dev-implementation`,
  `dev-lifecycle`, `dev-lifecycle/references/handoff-template.md`,
  `scripts/test_lifecycle_document_contract.py`
- **Bước tiếp theo**: `writing-plans` (một implementation plan, không cần HLD)

## Mục lục

- [1. Bối cảnh](#1-bối-cảnh)
- [2. Mục tiêu và ngoài mục tiêu](#2-mục-tiêu-và-ngoài-mục-tiêu)
- [3. Các mục](#3-các-mục)
- [4. Thay đổi script](#4-thay-đổi-script)
- [5. Thay đổi skill và template](#5-thay-đổi-skill-và-template)
- [6. Điều chỉnh các spec trước](#6-điều-chỉnh-các-spec-trước)
- [7. Kiểm thử](#7-kiểm-thử)
- [8. Rủi ro](#8-rủi-ro)
- [9. Ngoài phạm vi](#9-ngoài-phạm-vi)

## 1. Bối cảnh

Ngày 2026-10-15 có hai branch được merge vào `main`: truy vết BDD sang integration test (merge
`bde3493`) và lựa chọn bàn giao epic (merge `5b37dcc`). Buổi review cuối của mỗi branch đã hoãn lại
tổng cộng mười một mục nhỏ, được ghi trong memory của dự án. Trước khi viết spec này, từng mục đã được
kiểm tra lại trên `main`; ba mục được tái hiện trên script thật, và một mục hóa ra nghiêm trọng hơn
mức đã ghi:

- **B4** — `check_bdd_traceability.py tests` duyệt các thư mục bằng `rglob`, nên file bị ignore, file
  vendored và file được sinh ra đều được tính là coverage. Chỉ một file trong `node_modules/` đã cho ra
  `Result: 2/2 covered — PASS`. Một báo cáo Playwright cũ trong `tests/e2e/` sẽ giữ định danh của một
  test đã bị xóa ở trạng thái "được phủ" và làm Gate 4 xanh giả.
- **H1** — khi chưa fetch, `git branch -r` không cho thấy gì về một epic branch mà clone khác đã push,
  trong khi `git ls-remote --heads` tìm thấy nó.
- **H3** — trong epic worktree, `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` liệt kê cả commit
  task của chính epic, nên mọi agent nhận đều được báo rằng bản bàn giao có thể đã cũ; so với base
  branch thì chỉ có commit đóng gói xuất hiện.

Developer đã duyệt sửa toàn bộ các mục được đề xuất trong một patch.

## 2. Mục tiêu và ngoài mục tiêu

**Mục tiêu:**

- Loại bỏ PASS giả (B4) và cảnh báo "đã cũ" giả (H3).
- Ngăn một epic được tiếp tục tạo trùng một branch chỉ tồn tại trên remote (H1).
- Gỡ các điểm gây vướng không cần thiết: chú thích trong dòng `Covers:` (B1), thư mục e2e của Python
  (B2), lỗi đầu vào bị báo như lỗi truy vết (B3).
- Lấp các khoảng trống nhỏ trong văn bản: B5, B6, H2, H4a, H4b và H5.

**Ngoài mục tiêu:**

- Script mới, gate mới, hoặc thay đổi `quality_check` và các provider của nó.
- Ngắt lại các dòng dài sẵn có; `dev-lifecycle` vốn đã có 54 dòng dài hơn 100 cột.
- Lỗi crash có từ trước của `validate_quality_contract.py` khi thiếu registry.
- Bổ sung cho các epic đã lưu trữ.

## 3. Các mục

| ID | Thay đổi | Ở đâu |
|----|----------|-------|
| B1 | Đọc định danh trong `Covers:` theo hình dạng, bỏ qua chú thích và dấu câu ở cuối | script |
| B2 | Thư mục integration test mặc định của Python trở thành `tests/integration/` và `tests/e2e/` | dev-designer |
| B3 | File scenario hoặc file task không phải UTF-8 hợp lệ là lỗi sử dụng, exit 2 | script |
| B4 | Liệt kê file integration test bằng `git ls-files`, bỏ qua file bị ignore; ngoài git thì quay về duyệt thư mục | script |
| B5 | Nói rõ `--roots` và `--ids` nhận giá trị phân tách bằng dấu cách hoặc dấu phẩy | dev-implementation |
| B6 | Điều kiện 4 của Gate 4 nêu cả việc chạy lại kiểm tra truy vết | dev-lifecycle |
| H1 | Phát hiện epic branch trên remote bằng `git ls-remote --heads` | dev-implementation |
| H2 | Epic đang xếp hàng được đóng gói thành `Packaged (queued behind <epic>)` | dev-lifecycle, dev-implementation |
| H3 | Kiểm tra "đã cũ" so với base branch; ghi `uncommitted` khi `auto_commit` là false | template |
| H4a | Commit bổ sung định danh có thể kèm trường trạng thái của task bị ngắt; nói rõ điều đó là bình thường | dev-implementation |
| H4b | Vào lại Phase 2 tại một task đang `review` thì tiếp tục review, không implement lại | dev-implementation |
| H5 | `<N>` trong template là số task từ preflight | dev-lifecycle |

## 4. Thay đổi script

Tất cả nằm trong `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`.

**B1.** `covers_of` lấy định danh từ phần văn bản sau `Covers:` theo hình dạng định danh —
`[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+`, không đứng ngay sau chữ cái, chữ số hay `-`, không đứng ngay
trước chữ cái hay chữ số — thay vì cắt theo dấu phẩy và khoảng trắng. `Covers: PY-HP-01 (happy path),
PY-EC-02.` cho ra `PY-HP-01` và `PY-EC-02`. Một định danh đúng hình dạng nhưng không có trong tài liệu
vẫn bị báo là lạ.

**B3.** Khi đọc tài liệu scenario, bản tiếng Việt đi kèm, hoặc file task, script bắt
`UnicodeDecodeError` và ném lỗi sử dụng kèm đường dẫn file, nên lần chạy exit 2 với
`error: <path> is not valid UTF-8`. File integration test giữ hành vi hiện tại: file không giải mã
được thì bị bỏ qua.

**B4.** Với mỗi thư mục tồn tại, `integration_files` chạy
`git -C <root> ls-files --cached --others --exclude-standard -z`. Nó giữ mọi đường dẫn được liệt kê là
file và không kết thúc bằng `.md`, nối vào thư mục gốc. Khi không có git hoặc thư mục không nằm trong
repo nào, nó quay về cách duyệt `rglob` hiện tại cho thư mục đó. File đã track và file test mới chưa bị
ignore đều được tính; mọi thứ khớp `.gitignore` thì không.

## 5. Thay đổi skill và template

**B2 — dev-designer, bullet Integration Test Roots.** Mặc định của Python thành
`tests/integration/` và `tests/e2e/` (Python). Tier C của chính Python đã chạy cả hai bộ test, và một
thư mục chưa tồn tại chỉ gây cảnh báo.

**B5 — dev-implementation, Phase 4.** Sau đoạn văn đi sau lệnh kiểm tra truy vết đầy đủ, thêm:
`--roots` và `--ids` nhận giá trị phân tách bằng dấu cách hoặc dấu phẩy, nên dòng roots của HLD và
dòng `Covers:` của task có thể dán nguyên văn.

**B6 — dev-lifecycle, điều kiện 4 của Gate 4.** "a fresh epic quality run is required before landing"
thành "a fresh traceability check and epic quality run are required before landing".

**H1 — dev-implementation, Entry-Point Detection.** Tín hiệu
`git branch -r --list '*/epic/<epic_slug>'` thành
`for remote in $(git remote); do git ls-remote --heads "$remote" "epic/<epic_slug>"; done`. Câu giải
thích thành: `git ls-remote` hỏi trực tiếp từng remote, nên epic branch được push từ clone khác hiện ra
ngay cả khi chưa fetch; nếu không kết nối được tới một remote, nói rõ trong lời thông báo và quay về
`git branch -r --list '*/epic/<epic_slug>'`.

**H2 — dev-lifecycle bước đóng gói 4, và dev-implementation.** Nếu trước khi đóng gói Status của
overview là `Queued (backlog) — behind <epic>`, script trạng thái được chạy với
`"Packaged (queued behind <epic>)"` và dòng đó được chép vào Open Notes; lệnh `grep` vẫn khớp vì nó
neo vào `: Packaged`. Câu hỏi Handoff Choice nhắc tới hàng đợi khi có. Trong dev-implementation, hai
kiểm tra "if the overview Status is `Packaged`" (Resume Procedure bước 5 và Phase 1 bước 4) thành
"if the overview Status begins with `Packaged`". Các dòng điểm vào giữ nguyên: task `backlog` của epic
đang xếp hàng vẫn dừng ở dòng 2.

**H3 — template bàn giao.** Dòng design commit trong mục Status thêm "or `uncommitted` when
`auto_commit` is false". Quy tắc "đã cũ" thành: trừ khi design commit là `uncommitted`, nếu
`git log <sha>..<base_branch> -- .devtool/epic/<epic_dir>` có commit nào khác ngoài commit
`Package epic for handoff`, tài liệu đã thay đổi sau khi đóng gói; tài liệu thắng và file này có thể đã
cũ. So với base branch giúp loại các commit task của chính epic branch khỏi phép kiểm tra, và lệnh chạy
được từ mọi checkout.

**H4a — dev-implementation, Resume Procedure bước 4.** Sau quy tắc stage theo đường dẫn, thêm: trường
trạng thái của chính task bị ngắt có thể đi kèm trong commit đó; điều này là bình thường.

**H4b — dev-implementation, Resume Procedure bước 6.** "Enter Phase 2 at the interrupted task, or at
the first remaining task." thành: vào Phase 2 tại task bị ngắt — task ở `review` vào lại tại Phase 2
bước 2 và được review trên các thay đổi hiện có; task ở `in-progress` tiếp tục implement với các thay
đổi đã giữ lại ở Gate 3 (tiếp tục) — hoặc tại task còn lại đầu tiên.

**H5 — dev-lifecycle bước đóng gói 2.** Sau "fill every placeholder", thêm rằng `<N>` là số task mà
preflight đã in ra.

**Contract test.** `scripts/test_lifecycle_document_contract.py` khóa `git ls-remote --heads` cho
dev-implementation và `a fresh traceability check and epic quality run` cho dev-lifecycle.

## 6. Điều chỉnh các spec trước

Spec này thay thế, mà không sửa trực tiếp, các phần sau của những spec trước:

| Spec trước | Mục | Được thay bởi |
|------------|-----|---------------|
| `2026-10-15-bdd-integration-traceability-design` | §5 quét file, §6 thư mục mặc định của Python, §7 đọc `Covers:` và exit code | B4, B2, B1 và B3 |
| `2026-10-15-epic-handoff-choice-design` | §6 hàng Status và quy tắc "đã cũ" | H3 |
| `2026-10-15-epic-handoff-choice-design` | §7 bước 4, §8.2 tín hiệu branch trên remote, §8.4 bước 3 và 5 | H2, H1, H4a và H4b |

## 7. Kiểm thử

1. Unit test mới trong `test_check_bdd_traceability.py`, viết trước và thấy thất bại:
   - B1: chú thích và dấu câu ở cuối dòng `Covers:` vẫn cho ra 2/2 covered;
   - B3: một file task và một tài liệu scenario không phải UTF-8 đều exit 2;
   - B4, trong một repo git tạm: file test khớp `.gitignore` không được tính; file test chưa track và
     không bị ignore thì được tính; file test đã track thì được tính.

   26 test hiện có vẫn pass; thư mục tạm của chúng không phải repo git, nên chúng kiểm tra nhánh quay về
   duyệt thư mục.
2. Chạy thử trong các repo dùng một lần, không bao giờ trong repo này:
   - H1: một remote bare có epic branch được push từ clone thứ hai — `git branch -r` không in gì, còn
     vòng lặp `git ls-remote` in ra branch;
   - H3: sau khi đóng gói, một commit task trong epic worktree — `git log <sha>..HEAD` liệt kê nó, còn
     `git log <sha>..<base_branch>` chỉ liệt kê commit đóng gói.
3. Kiểm thử hành vi bằng subagent mới, trước và sau khi sửa: tiếp tục một epic mà epic branch chỉ có
   trên `origin` (kỳ vọng: tín hiệu `ls-remote` và dòng 7, không phải dòng 3), tiếp tục một task đang
   `review` (kỳ vọng: Phase 2 bước 2), và đóng gói một epic đang xếp hàng (kỳ vọng:
   `Packaged (queued behind <epic>)` và một ghi chú trong Open Notes).
4. `scripts/verify.sh` đạt. Quality gate là `scripts/verify.sh`; `@quality_check` trả `BLOCKED` trong
   repo này vì không có quality registry.

## 8. Rủi ro

- **`git ls-files` thay đổi thứ được tính.** Test bị `.gitignore` bỏ qua sẽ không còn được tính. Đó là
  chủ ý, nhưng một project lỡ ignore một thư mục test thật sẽ thấy định danh mới chưa được phủ. Lỗi báo
  to và nêu rõ định danh.
- **Mạng khi tiếp tục epic.** `git ls-remote` liên hệ từng remote. Khi không có mạng, skill nói rõ và
  quay về ref ở local, không tệ hơn hiện nay.
- **Tiền tố Status.** Các kiểm tra chuyển từ "là `Packaged`" sang "bắt đầu bằng `Packaged`"; không có
  giá trị trạng thái nào khác bắt đầu bằng từ đó.

## 9. Ngoài phạm vi

- Ngắt lại các dòng dài trong `dev-lifecycle` và các skill khác.
- Lỗi crash của `validate_quality_contract.py` khi thiếu registry (lỗi tooling số 6 của kit).
- Các mục thẩm mỹ được hoãn nhưng không ghi trong memory: vị trí heading Tier C BDD Automation, câu
  "below" không có link, và script nằm trong bảng Stage Skills.
