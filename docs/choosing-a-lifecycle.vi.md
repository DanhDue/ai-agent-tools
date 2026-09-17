# Chọn lifecycle nào

> Bản dịch của [choosing-a-lifecycle.md](choosing-a-lifecycle.md). Bản tiếng Anh là nguồn sự thật cho
> tooling và agent; bản này phục vụ trao đổi trong nhóm và phải luôn đồng bộ về cấu trúc lẫn sự kiện.

Bạn đang cầm một việc và có ba lifecycle để chọn. Trang này đưa bạn tới đúng cái cần.

## Bắt đầu từ đây

Trả lời một câu hỏi: **làm xong rồi thì sẽ có cái gì?**

| Thứ bạn tạo ra | Đi tới |
|---|---|
| Code đã đổi và đi vào build | [Nếu bạn viết code](#nếu-bạn-viết-code) |
| Một tài liệu có người đọc | [Nếu bạn viết tài liệu](#nếu-bạn-viết-tài-liệu) |
| Một quyết định về việc rốt cuộc nên xây gì | [Nếu bạn chưa biết nên xây gì](#nếu-bạn-chưa-biết-nên-xây-gì) |

Số cổng nêu bên dưới là **số cổng có tên của chính lifecycle bạn bước vào**. Chỗ nào một tuyến có
phê duyệt nằm ngoài lifecycle — như phê duyệt thiết kế và soát spec của `brainstorming` trên tuyến
một-plan — thì chúng được kể riêng chứ không gộp vào con số, nên các con số trên trang này **không
so sánh trực tiếp với nhau được**.

Nếu thấy hai dòng cùng đúng một lúc, hãy chọn theo **build**: chỉ cần một file đi vào build bị đổi
thì đó là việc code, bất kể bạn phải viết bao nhiêu chữ. `d3nexus:doc_quality_check` thi hành điều
này và sẽ từ chối thẳng đường tài liệu.

Nếu cả việc còn nhỏ hơn một lượt review, nhảy tới [Nếu việc quá nhỏ](#nếu-việc-quá-nhỏ).

## Nếu bạn viết code

Chọn theo số mảnh review được của công việc.

**Nhiều thành phần độc lập, hoặc bạn sẽ muốn có sơ đồ kiến trúc và một bảng task** — chạy
`d3nexus:dev-lifecycle`. Nó đưa bạn qua năm cổng: spec, phân rã task, thứ tự thực thi,
`quality_check`, và chữ ký của chính bạn trước khi nhánh được hoàn tất.

**Một thành phần, một plan** — chạy `d3nexus:brainstorming`, rồi `d3nexus:writing-plans`. Cách này
rời khỏi epic lifecycle; các cổng còn lại của nó không áp dụng. Bạn vẫn qua hai cổng:
`brainstorming` không cho bắt đầu khi thiết kế chưa được duyệt, và nó yêu cầu bạn soát lại spec đã
viết trước khi lập plan.

**Trên tuyến một-plan, phải có thứ gì đó thực thi cái plan, và bạn phải verify trước khi nó kết
thúc.** `writing-plans` sinh ra tài liệu, không sinh ra code. Chạy
`d3nexus:subagent-driven-development` (khuyến nghị) hoặc `d3nexus:executing-plans` lên nó.

> Cả hai executor **tự gọi** `d3nexus:finishing-a-development-branch` ở bước cuối, và **không cái nào
> chạy `quality_check`**. Chúng cũng chạy liên tục không dừng, nên không có cửa sổ nào ở giữa.
>
> Cửa sổ của bạn là chỗ executor dừng lại: `finishing-a-development-branch` trình ba lựa chọn rồi
> chờ — không có gì bị merge hay push cho tới khi bạn trả lời. **Chọn phương án 3, "keep the branch
> as-is", chạy `d3nexus:quality_check`, sửa những gì nó tìm ra, rồi chạy lại
> `d3nexus:finishing-a-development-branch` và chọn merge hoặc PR.**

Tuyến epic không cần gì trong số này: `dev-implementation` điều khiển executor, giữ `quality_check`
ở Cổng 4 và chữ ký của bạn ở Cổng 5, rồi mới hoàn tất nhánh.

## Nếu bạn viết tài liệu

**Bài test là bạn có hình dung nổi một người review từ chối nó hay không, chứ không phải nó dài bao
nhiêu.** Một runbook một trang mà người ta sẽ làm theo lúc đang căng thẳng thì xứng đáng có brief và
outline; một trang không ai buồn gate thì không.

Chạy `d3nexus:doc-lifecycle` khi nó qua được bài test đó. Ba cổng: brief và outline,
`d3nexus:doc_quality_check`, và chữ ký của bạn.

Hai trường hợp nằm dưới ngưỡng đó:

- **Một quyết định kiến trúc hoặc một spike report lẻ** — chạy `d3nexus:decision-records` trực tiếp
  rồi commit hồ sơ. Đừng mở cổng quanh một file. Một *loạt* hồ sơ được tạo hoặc bổ sung ngược như
  một khối công việc thì khác: cái đó thuộc về `d3nexus:doc-lifecycle`.
- **Một thay đổi không người review nào buồn gate** — xem [Nếu việc quá nhỏ](#nếu-việc-quá-nhỏ).

Nếu bạn chưa biết tài liệu nên nói gì — một bài chiến lược, một đề xuất, một lập luận bạn chưa tranh
xong — chạy `d3nexus:brainstorming` trước. Nó kết thúc bằng việc gọi thẳng `doc-designer`, vốn là
Stage 1 của lifecycle này, nên bạn tới đây mà không phải quay lại trang này.

## Nếu bạn chưa biết nên xây gì

Chạy `d3nexus:lean-product-lifecycle`. Ba cổng: problem space, value proposition, MVP backlog. Cổng 3
bàn giao backlog sang `d3nexus:dev-designer`, nên bạn quay lại nhánh code với một thứ đáng để xây.

Hãy tính ngân sách **bảy cổng, không phải ba** — khi tới `dev-designer` là bạn đang ở Stage 2 của
`dev-lifecycle`, và các Cổng 2 đến 5 của nó vẫn áp dụng.

Hai dấu hiệu cho thấy bạn đang ở trường hợp này và nên dừng ngay tại chỗ:

- Không ai gọi được tên khách hàng mục tiêu như một phân khúc cụ thể — chỉ nói chung chung là
  "người dùng" hoặc "doanh nghiệp".
- Nhu cầu được khẳng định chứ không có bằng chứng: không phỏng vấn, không dữ liệu, không xếp hạng
  mức quan trọng đối chiếu với mức thỏa mãn.

`d3nexus:brainstorming` kiểm cả hai ở bước 2 và sẽ đẩy bạn sang đây trước khi hỏi bạn bất cứ điều gì
khác.

## Nếu việc quá nhỏ

Làm luôn. Commit luôn. Bỏ qua mọi lifecycle trên trang này.

Cụ thể: một lỗi chính tả, một link hỏng, một dòng sửa lẻ, nâng một con số phiên bản, một dòng chú
thích. Bài test là bạn có hình dung nổi một người review từ chối nó không. Nếu không, thì chẳng có
phân rã nào để duyệt và chẳng có outline nào để thống nhất, nên **các cổng lifecycle** không có việc
gì để làm.

**Cổng chất lượng là chuyện khác, và bạn vẫn phải chạy** — `d3nexus:quality_check` cho code,
`d3nexus:doc_quality_check` cho văn bản. Bỏ qua một lifecycle không có nghĩa là bỏ qua xác minh.

## Bàn giao giữa các lifecycle

Đôi lúc bạn sẽ bắt đầu nhầm chỗ. Đây là ba bước chuyển giữ được việc của bạn:

**Từ discovery sang code.** Ở Cổng 3, `lean-product-lifecycle` bàn giao `03_mvp_feature_backlog.md`
sang `d3nexus:dev-designer`. Hãy truyền đường dẫn file; đừng dựng lại backlog từ đầu.

**Từ brainstorming sang một trong hai nhánh.** `d3nexus:brainstorming` kết thúc bằng việc gọi đúng
**một** trong `dev-designer`, `writing-plans`, `doc-designer` hoặc `lean-product-lifecycle`. Trước
khi định tuyến sang `dev-designer`, nó dời spec của bạn vào `.devtool/epic/<epic_name>/` để spec,
thiết kế và các task nằm cùng một chỗ.

**Từ code ngược về discovery.** Nếu một spec hóa ra dựa trên một giả định chưa được kiểm chứng, hãy
dừng lại và chạy `d3nexus:lean-product-lifecycle`. Mang những gì bạn đã biết vào phiên làm việc dưới
dạng ngữ cảnh — phân khúc, nhu cầu, bằng chứng bạn có và bằng chứng bạn còn thiếu — để Stage 1 không
phải bắt đầu từ con số không.

> **Đừng tạo sẵn `.devtool/product/<slug>/01_problem_space_spec.md`.**
> `lean-product-lifecycle` resume dựa trên **sự tồn tại** của file: file đó có mặt sẽ khiến nó tuyên
> bố "Gate 1 is already verified" và bắt đầu từ Stage 2. Bạn tới đây chính vì problem space chưa bao
> giờ được kiểm chứng, mà Stage 1 chính là phần kiểm chứng đó. Tạo sẵn artefact là bỏ qua nó.

Cứ để nguyên thư mục epic và các file `task_*.md` của nó tại chỗ. Nếu giả định sống sót qua
discovery, bạn sẽ quay lại với chúng; nếu không, chúng là hồ sơ ghi lại thứ bạn đã không xây.

Một hệ quả cần lường trước: chừng nào các task đó còn ở `todo`, `in-progress` hoặc `review`, luật
Concurrent-Epic Backlog vẫn coi epic đó là đang hoạt động, nên mọi task của epic *kế tiếp* sẽ được
tạo với `status: "backlog"` và phải có người lật tay.

Một luật đúng cho cả ba bước: **đừng bao giờ gộp hai spec vào một epic.** Mỗi spec giữ dòng đời
spec → thiết kế → thi công của riêng nó.
