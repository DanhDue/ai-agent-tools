# Ba lifecycle

> Bản dịch của [lifecycles.en.md](lifecycles.en.md). Bản tiếng Anh là nguồn sự thật cho tooling và
> agent; bản này phục vụ trao đổi trong nhóm và phải luôn đồng bộ về cấu trúc lẫn sự kiện.

Tài liệu tra cứu về việc mỗi lifecycle trong kit này dùng để làm gì, cho ra cái gì, và chạy ra sao.

Trang này **mô tả**.
Muốn quyết định một việc cụ thể thuộc lifecycle nào, xem [choosing-a-lifecycle.vi.md](choosing-a-lifecycle.vi.md).

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [dev-lifecycle](#dev-lifecycle)
3. [doc-lifecycle](#doc-lifecycle)
4. [lean-product-lifecycle](#lean-product-lifecycle)
5. [Những thứ không phải lifecycle](#những-thứ-không-phải-lifecycle)
6. [Chúng nối với nhau thế nào](#chúng-nối-với-nhau-thế-nào)

## Tổng quan

Mỗi lifecycle được định nghĩa bằng **thứ tồn tại khi nó kết thúc**.

| | `dev-lifecycle` | `doc-lifecycle` | `lean-product-lifecycle` |
|---|---|---|---|
| **Mục đích** | Xây code đi vào build | Tạo ra tài liệu có người đọc | Quyết định nên xây gì, cho ai |
| **Cho ra** | Một nhánh đã merge | Một tài liệu đã xuất bản | Một MVP backlog đã kiểm chứng |
| **Số cổng** | 5 | 4 | 3 |
| **Ai duyệt cổng** | 4 người, 1 máy | 3 người, 1 máy | 3 người |
| **Artefact nằm ở** | `.devtool/epic/<slug>/` | `.devtool/epic/<slug>/`, thành phẩm ở `docs/` | `.devtool/product/<slug>/` |
| **Xác minh bởi** | `quality_check` | `doc_quality_check` | chỉ bằng phán đoán người |

Hai cổng chất lượng **không chia sẻ tier, audit hay tooling nào**, và không cái nào gọi cái kia.

## dev-lifecycle

**Mục đích.** Điều phối công việc code quy mô epic, từ ý tưởng tới nhánh đã merge.
Nó chỉ sở hữu trình tự và các cổng; cách làm của từng stage nằm trong skill của stage đó.

**Cho ra cái gì.** Một nhánh đã merge, cộng với một High-Level Design bằng tiếng Anh và tiếng Việt,
một bộ BDD viết bằng Gherkin, và mỗi đơn vị công việc một file task
— tất cả được archive vào `.devtool/epic/<slug>/` khi epic đóng.

**Khi nào không áp dụng.** Một thành phần đơn lẻ mà một implementation plan là đủ.
Việc đó dùng `dev-brainstorming` rồi `writing-plans`, tức là rời khỏi lifecycle này cùng các cổng còn lại của nó.

```mermaid
flowchart TD
    S1["Stage 1 — Khởi đầu &amp; Spec<br/>(dev-brainstorming)"]
    G1{"Cổng 1<br/>Spec được duyệt?"}
    ROUTE{"Quy mô epic?"}
    PLANS(["writing-plans<br/>(rời workflow này)"])
    S2["Stage 2 — Kiến trúc &amp; Task<br/>(dev-designer)"]
    G2{"Cổng 2<br/>HLD &amp; phân rã task được duyệt?"}
    HC{"Handoff choice<br/>package hay continue?"}
    PKG(["Package epic<br/>handoff.md, status Packaged, dừng"])
    S3["Stage 3 — Thực thi độc lập<br/>(dev-implementation)"]
    G3{"Cổng 3<br/>Thứ tự thực thi đã xác nhận?"}
    EXEC["Phase 2-3: TDD từng task<br/>mỗi task một commit, sync doc khi lệch,<br/>tích hợp vào develop sau mỗi task"]
    RC{"Review Choice<br/>Finish, Cross-model review hay Local model review?"}
    XR["run_external_review.py run<br/>(commit review_results.md mỗi vòng)"]
    LR["run_external_review.py run --cli ollama<br/>(commit review_results.md mỗi vòng)"]
    G4{"Cổng 4<br/>audit + BDD traceability + quality_check 🟢 LGTM?"}
    REVIEW["Phase 4.1: Developer Kanban Review<br/>(Mọi task giữ ở cột DONE để kiểm tra trực quan)"]
    G5{"Cổng 5<br/>Người dùng ký duyệt &amp; cho phép finish?"}
    S4["Stage 4 — Hoàn tất nhánh &amp; Lưu trữ<br/>(finishing-a-development-branch)"]

    S1 --> G1
    G1 -->|chưa, chỉnh sửa| S1
    G1 -->|rồi| ROUTE
    ROUTE -->|không| PLANS
    ROUTE -->|có| S2
    S2 --> G2
    G2 -->|chưa, điều chỉnh phân rã| S2
    G2 -->|rồi| HC
    HC -->|"1. package"| PKG
    HC -->|"2. continue"| S3
    PKG -.->|"phiên sau hoặc LLM khác"| S3
    S3 --> G3
    G3 -->|chưa, sắp xếp lại| G3
    G3 -->|rồi| EXEC
    EXEC --> G4
    G4 -->|"chưa, sửa bằng Fix commit"| EXEC
    G4 -->|"rồi"| RC
    RC -->|"1. Finish"| REVIEW
    RC -->|"2. Cross-model review"| XR
    XR -->|"đã ghi nhận round"| G4
    RC -->|"3. Local model review"| LR
    LR -->|"đã ghi nhận round"| G4
    REVIEW --> G5
    G5 -->|"chưa, yêu cầu đổi bằng Fix commit"| EXEC
    G5 -->|rồi| S4
```

Vòng đời trải qua bốn giai đoạn (stage) và năm cổng phê duyệt (approval gate), cùng hai điểm lựa chọn rõ ràng:
- **Routing & Handoff Choice**: Sau khi qua Cổng 1, công việc quy mô epic đi tới Stage 2 (`dev-designer`). Giữa Cổng 2 và Stage 3, nhà phát triển chọn **Package** (`handoff.md`, trạng thái `Packaged`, dừng để phiên sau hoặc LLM khác làm) hoặc **Continue** vào Stage 3 ngay.
- **Thực thi độc lập**: Stage 3 thực thi từng task độc lập trong git worktree theo phương pháp TDD và tích hợp liên tục vào `develop`. Khi mọi task đã xong, agent chạy Cổng 4 trên SHA ứng viên.
- **Vòng lặp Cổng 4 và Review Choice**: Cổng 4 là cổng máy duy nhất trên nhánh phát triển của kit này. Nó chỉ cấp 🟢 khi `audit_epic.py` exit 0, `check_bdd_traceability.py tests --results` exit 0, và `@quality_check` profile `epic` trả về PASS trên đúng commit SHA ứng viên. Mỗi lần PASS sẽ đưa ra **Review Choice**: **Finish** đi tới Cổng 5; **Cross-model review** (Claude CLI hoặc Codex CLI) và **Local model review** (một model do Ollama phục vụ ở máy local, review từng task) đều ghi nhận một round rồi quay lại chạy đầy đủ Cổng 4. Mỗi round review được triage cùng nhà phát triển (`run_external_review.py triage`) trước mọi lần sửa. Vòng lặp tiếp tục cho tới khi nhà phát triển chọn Finish.
- **Ký duyệt Kanban Cổng 5**: Tất cả task hoàn tất được giữ lại ở `.devtool/features/done/` để nhà phát triển kiểm tra trực quan trên bảng Kanban trước khi Stage 4 rebase, verify theo tier, merge `--no-ff` vào `develop`, và lưu trữ task vào `.devtool/epic/<slug>/`.

### Trạng thái ngắt quãng và khôi phục (Resume)

Khi công việc tạm dừng hoặc một epic được đóng gói, vòng đời khôi phục một cách tất định qua năm trạng thái vận hành:

```mermaid
flowchart TD
    FRESH["Epic mới<br/>(Stage 1 hoặc Stage 2, chưa có task file)"]
    PKG["Epic đã đóng gói<br/>(có handoff.md, trạng thái Packaged)"]
    INTR["Epic bị ngắt quãng<br/>(đã có task file, đang dở Stage 3)"]
    DONE_EPIC["Epic hoàn thành<br/>(mọi task done, Cổng 4 PASS)"]
    INCON["Trạng thái không nhất quán<br/>(tài liệu bị sửa sau khi đóng gói)"]

    FRESH -->|"Hoàn tất Stage 1-2"| PKG
    FRESH -->|"Continue tại Handoff Choice"| INTR
    PKG -->|"Kiểm tra git log từ khi đóng gói"| INCON
    PKG -->|"Resume tại Stage 3 Cổng 3"| INTR
    INCON -->|"Tài liệu thắng, xử lý lệch"| INTR
    INTR -->|"TDD từng task"| DONE_EPIC
    DONE_EPIC -->|"Review Choice + ký duyệt Cổng 5"| MERGED["Stage 4: Merge nhánh & Lưu trữ"]
```

Các sơ đồ và giải thích này mô tả vòng đời cho con người; các runtime skill (`dev-lifecycle`, `dev-implementation`) và script là nguồn sự thật vận hành.

## doc-lifecycle

**Mục đích.** Điều phối công việc mà sản phẩm cuối là **tài liệu**, không phải code
— runbook, sổ tay, hướng dẫn onboarding, một bộ trang tra cứu.

**Cho ra cái gì.** Tài liệu hoàn chỉnh, đặt đúng nơi nó thuộc về:
`docs/`, một README, thư mục `references/` của một skill.
Các artefact quá trình — brief, outline, mỗi section một task — ở lại `.devtool/epic/<slug>/`.
**Một thành phẩm còn nằm trong `.devtool/` là chưa ship.**

**Vì sao bốn cổng chứ không phải năm.** Code và văn bản khác nhau ở bốn chỗ làm đổi ý nghĩa của việc xác minh: đơn vị công việc là một section chứ không phải một deliverable test được độc lập;
xác minh là kiểm tra cơ học cộng phán đoán người chứ không phải máy chạy test;
ràng buộc chi phối là **độc giả** chứ không phải kiến trúc; và chi phí sai là thấp.
Vì chi phí sai thấp nên số cổng vẫn ít hơn năm cổng của phía phát triển.

Cổng đầu tiên trong bốn cổng là khởi đầu, và nó **không phải tùy chọn**.
Trước đây nó từng là, với điều kiện bỏ qua hỏi rằng nội dung đã biết hay chưa
— một câu mà agent hầu như luôn trả lời là rồi.
Thứ khiến một giai đoạn bắt buộc vẫn kham được là *độ sâu* của nó co giãn còn *sự tồn tại* thì không:
một runbook vẫn đi qua Stage 0, và spec của nó dài ba câu.
Một runbook mà tốn năm lần phê duyệt thì sẽ không được viết *qua* lifecycle
— nó sẽ được viết *vòng qua* lifecycle.

**Khi nào không áp dụng.** Một lỗi chính tả, một link hỏng, một ADR lẻ,
hay bất kỳ thay đổi nào không người review nào buồn gate.

```mermaid
flowchart TD
    S0["Stage 0 — Khởi đầu<br/>(doc-brainstorming)"]
    G1{"Cổng 1 — spec được duyệt"}
    S1["Stage 1 — Brief &amp; Outline<br/>(doc-designer)"]
    G2{"Cổng 2 — brief &amp; outline"}
    S2["Stage 2 — Viết bản thảo<br/>(doc-implementation)"]
    G3{"Cổng 3 — doc_quality_check 🟢"}
    G4{"Cổng 4 — ký duyệt"}
    S3["Stage 3 — Hoàn tất nhánh<br/>(finishing-a-development-branch)"]

    S0 --> G1 --> S1 --> G2 --> S2 --> G3 --> G4 --> S3
```

Stage 0 là bắt buộc — độ sâu co giãn, sự tồn tại thì không.
Stage 1 xác lập độc giả, phân loại tài liệu vào **đúng một** mode Diátaxis,
và biến outline thành mỗi section một task.

## lean-product-lifecycle

**Mục đích.** Quyết định nên xây gì và cho ai, **trước khi** bắt đầu bất kỳ việc kỹ thuật nào.
Nó hiện thực hóa Lean Product Process của Dan Olsen và thi hành kỷ luật problem-space:
nhu cầu phải được mô tả như nhu cầu, không phải như tính năng mà ai đó đã nghĩ sẵn trong đầu.

**Cho ra cái gì.** Ba đặc tả đã được ký duyệt trong `.devtool/product/<slug>/` — `01_problem_space_spec.md`, `02_value_proposition_spec.md`, `03_mvp_feature_backlog.md`.
Backlog là thứ mà bên kỹ thuật nhận được.

**Nó không phủ cái gì.** Bước 5 và 6 trong quy trình của Olsen
— dựng prototype MVP và đem thử với khách hàng — **chưa được hiện thực** trong bản này.
Bộ điều phối nói thẳng điều đó ở Cổng 3 thay vì để người dùng tưởng hành trình đã trọn vẹn.

```mermaid
flowchart TD
    IN(["Một ý tưởng thô, hoặc lối thoát bước 2 của một trong hai biến thể brainstorming"])
    S1["Stage 1 — Problem Space<br/>(lean-market-discovery)"]
    G1{"Cổng 1 — problem space"}
    S2["Stage 2 — Value Proposition<br/>(lean-value-strategy)"]
    G2{"Cổng 2 — value proposition"}
    S3["Stage 3 — MVP Feature Set<br/>(lean-mvp-scoping)"]
    G3{"Cổng 3 — MVP backlog"}
    OUT(["Bàn giao sang dev-designer"])

    IN --> S1 --> G1 --> S2 --> G2 --> S3 --> G3 --> OUT
    G1 -.->|"phân khúc lại"| S1
    G2 -.->|"nhu cầu vốn đã sai"| S1
    G3 -.->|"phạm vi phình"| S3
```

Các cạnh nét đứt là giao thức Tectonic Plates: khi một cổng fail,
ta **định vị giả thuyết hỏng** trên kim tự tháp Product-Market Fit năm tầng rồi kiểm chứng lại từ đó đi lên,
thay vì vá ngay tại tầng mình đang đứng.

## Những thứ không phải lifecycle

Năm thứ định tuyến công việc mà bản thân không phải lifecycle.

| | Là cái gì | Cổng |
|---|---|---|
| `brainstorming` | Router. Hỏi công việc là phát triển ý tưởng, làm tài liệu hay coding, rồi gọi biến thể tương ứng. Không giữ quy trình nào của riêng nó | Không — nó định tuyến rồi kết thúc |
| `dev-brainstorming` | Biến một ý tưởng về việc code thành design spec được duyệt. Lối ra: `dev-designer`, `writing-plans` hoặc `lean-product-lifecycle` | Một lần duyệt thiết kế và một lần soát spec, đều là người |
| `doc-brainstorming` | Biến một ý tưởng hoặc yêu cầu tài liệu thành content spec được duyệt. Lối ra: `doc-designer`, `decision-records` hoặc `lean-product-lifecycle` | Một lần duyệt thiết kế và một lần soát spec, đều là người |
| `writing-plans` + một executor | Đường code nhỏ. `writing-plans` sinh ra plan; `subagent-driven-development` hoặc `executing-plans` thực thi nó | Không có cổng riêng |
| `decision-records` | Một ADR hoặc một spike report lẻ, viết rồi commit thẳng | Không |

## Chúng nối với nhau thế nào

```mermaid
flowchart LR
    BS["brainstorming<br/>(router)"]
    DEVB["dev-brainstorming"]
    DOCB["doc-brainstorming"]
    LEAN["lean-product-lifecycle"]
    DEV["dev-lifecycle"]
    DOC["doc-lifecycle"]
    PLANS["writing-plans + executor"]

    BS -->|"coding"| DEVB
    BS -->|"ý tưởng hoặc tài liệu"| DOCB
    DEVB -->|"quy mô epic"| DEV
    DEVB -->|"một plan"| PLANS
    DOCB --> DOC
    DEVB -.->|"problem space chưa kiểm chứng"| LEAN
    DOCB -.->|"luận điểm sản phẩm không bằng chứng"| LEAN
    LEAN -->|"backlog Cổng 3"| DEV
```

Hai luật đúng cho mọi kết nối. **Sản phẩm cuối quyết định, không phải lượng chữ phải viết**
— chỉ cần việc đó đổi một file đi vào build thì đó là việc phát triển.
Và **không bao giờ gộp hai spec vào một epic**:
mỗi spec giữ dòng đời spec → thiết kế → thi công của riêng nó.
