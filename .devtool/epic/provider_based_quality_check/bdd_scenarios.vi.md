# Kịch Bản BDD Cho Quality Check Dựa Trên Provider

## Mục Lục

- [Mục Đích Và Quy Tắc Test](#mục-đích-và-quy-tắc-test)
- [UC1 Chạy Quality PR Trực Tiếp](#uc1-chạy-quality-pr-trực-tiếp)
- [UC2 Chứng Nhận Gate Của Epic](#uc2-chứng-nhận-gate-của-epic)
- [UC3 Assurance Cho Scheduled Và Release](#uc3-assurance-cho-scheduled-và-release)
- [UC4 Đăng Ký Provider Của Project](#uc4-đăng-ký-provider-của-project)
- [UC5 Thực Thi Rust Quality](#uc5-thực-thi-rust-quality)
- [UC6 Author Provider Và Aggregation](#uc6-author-provider-và-aggregation)
- [Ma Trận Truy Vết](#ma-trận-truy-vết)

## Mục Đích Và Quy Tắc Test

Đây là behavioral contract chuẩn cho epic `provider_based_quality_check`. Scenario được suy ra từ
thiết kế và HLD đã duyệt, không dựa trên sự thuận tiện khi implementation. Mỗi use case bao phủ năm
chiều bắt buộc: happy path, edge và boundary, state transition, concurrency hoặc race, cùng failure
hoặc resilience.

Ý nghĩa tag:

- `[Tier A - Unit]` map tới unit test cho validator, aggregator, schema và provider.
- `[Tier C - Integration]` map tới acceptance test bằng temporary repository hoặc lifecycle.
- Một scenario có thể mang cả hai tag khi cùng invariant cần chứng minh cục bộ và end-to-end.

## UC1 Chạy Quality PR Trực Tiếp

```gherkin
Tính năng: Chạy quality profile PR trực tiếp

  Kịch bản: [Tier C - Integration] Happy path dùng profile PR mặc định
    Biết rằng lời gọi trực tiếp bỏ profile và cung cấp base reference hợp lệ
    Và registry có hai provider bắt buộc hỗ trợ pr
    Khi quality_check chuẩn hóa và thực thi request
    Thì cả hai provider nhận profile pr và cùng repository SHA
    Và report hợp nhất có tính xác định chứa cả hai result

  Kịch bản: [Tier A - Unit] Edge case từ chối profile không biết
    Biết rằng invocation yêu cầu profile quick
    Khi invocation contract được kiểm tra
    Thì request bị BLOCKED với lý do profile không hỗ trợ
    Và không provider nào được gọi

  Kịch bản: [Tier A - Unit] State transition không pass trước khi kiểm tra result
    Biết rằng provider execution đã hoàn tất
    Nhưng một result chưa pass schema và identity validation
    Khi aggregation được yêu cầu
    Thì run vẫn BLOCKED
    Và không thể chuyển sang PASS

  Kịch bản: [Tier C - Integration] Provider đồng thời hoàn tất theo thứ tự khác nhau
    Biết rằng hai provider chạy độc lập cho profile pr
    Khi chúng hoàn tất theo thứ tự ngược nhau trong hai run tương đương
    Thì cả hai report sắp provider theo stable provider ID
    Và cả hai run tạo cùng verdict cuối

  Kịch bản: [Tier C - Integration] Không resolve được base reference phải hiển thị
    Biết rằng lời gọi trực tiếp cung cấp base reference không tồn tại
    Khi quality_check chuẩn hóa changed-file scope
    Thì run bị BLOCKED
    Và report nêu base reference không resolve được
```

## UC2 Chứng Nhận Gate Của Epic

```gherkin
Tính năng: Chứng nhận candidate SHA của epic

  Kịch bản: [Tier C - Integration] Happy path cấp LGTM cho SHA được chứng nhận
    Biết rằng dev-implementation yêu cầu profile epic cùng base reference và candidate SHA
    Và mọi provider bắt buộc được chọn trả PASS cho SHA đó
    Khi quality_check kiểm tra HEAD cuối và aggregate result
    Thì overall verdict là PASS
    Và Gate 4 chỉ có thể render LGTM cho candidate SHA

  Kịch bản: [Tier A - Unit] Boundary từ chối evidence PR rẻ hơn
    Biết rằng Gate 4 yêu cầu profile epic
    Và provider result khai profile pr
    Khi result identity được kiểm tra
    Thì result đó bị từ chối
    Và overall verdict là BLOCKED

  Kịch bản: [Tier A - Unit] State transition sai không thể tái dùng SHA xanh cũ
    Biết rằng một epic result trước đã pass cho SHA A
    Và candidate hiện tại là SHA B
    Khi result cũ được cấp cho run hiện tại
    Thì validation đánh dấu nó đã cũ
    Và Gate 4 vẫn BLOCKED

  Kịch bản: [Tier C - Integration] Repository HEAD thay đổi trong khi thực thi
    Biết rằng mọi provider bắt đầu trên candidate SHA được yêu cầu
    Khi process khác đổi HEAD trước final validation
    Thì mọi result thu được bị từ chối vì đã cũ
    Và không phát ra LGTM

  Kịch bản: [Tier C - Integration] Provider timeout chặn Gate 4
    Biết rằng provider epic bắt buộc không trả về trước timeout đã cấu hình
    Khi orchestrator đóng run
    Thì nó tạo result BLOCKED cho provider đó
    Và report giữ finding đã hoàn tất từ provider khác
```

## UC3 Assurance Cho Scheduled Và Release

```gherkin
Tính năng: Chạy profile scheduled và release sâu hơn

  Kịch bản: [Tier C - Integration] Scheduled run thành công gồm check tốn thời gian đã cấu hình
    Biết rằng provider hỗ trợ scheduled và khai báo dependency cùng vulnerability check
    Khi profile scheduled chạy
    Thì các check đó chạy ngoài requirement của epic
    Và evidence của chúng xuất hiện trong provider result

  Kịch bản: [Tier A - Unit] Tập release capability rỗng không phải false pass
    Biết rằng provider bắt buộc được đăng ký cho release
    Và cấu hình không khai báo release check
    Khi provider kiểm tra độ đầy đủ của profile
    Thì nó trả BLOCKED
    Và xác định release capability bị thiếu

  Kịch bản: [Tier A - Unit] Profile state không được nâng bằng evidence tái sử dụng
    Biết rằng cached evidence thỏa epic nhưng không thỏa release
    Khi release run xem xét evidence đó
    Thì requirement release-only vẫn pending
    Và run không thể chuyển sang PASS

  Kịch bản: [Tier C - Integration] Check tốn thời gian chạy song song vẫn có output xác định
    Biết rằng scheduled dependency và security check hoàn tất đồng thời
    Khi check record được kết hợp
    Thì record được sắp theo stable check ID
    Và thứ tự thời gian không đổi status precedence

  Kịch bản: [Tier C - Integration] Release API check không thể chạy
    Biết rằng API compatibility là bắt buộc cho release
    Và executable đã cấu hình không khả dụng
    Khi provider chạy
    Thì check và provider là BLOCKED thay vì NOT_APPLICABLE
    Và report cuối nêu executable bị thiếu
```

## UC4 Đăng Ký Provider Của Project

```gherkin
Tính năng: Đăng ký quality provider của project

  Kịch bản: [Tier A - Unit] Registry hợp lệ chọn mọi provider phù hợp
    Biết rằng registry hợp lệ có Rust và service provider cho profile epic
    Khi registry được kiểm tra và filter
    Thì cả hai provider xuất hiện đúng một lần trong execution plan
    Và plan được sắp theo provider ID

  Kịch bản: [Tier A - Unit] Provider ID trùng bị từ chối
    Biết rằng hai registry entry dùng cùng provider ID
    Khi schema và semantic validation chạy
    Thì registry bị BLOCKED
    Và không provider nào được gọi

  Kịch bản: [Tier A - Unit] Registry state sai khi selection rỗng
    Biết rằng registry hợp lệ không có provider hỗ trợ profile yêu cầu
    Khi execution plan được tạo
    Thì việc tạo plan trả BLOCKED
    Và nó liệt kê profile được yêu cầu

  Kịch bản: [Tier C - Integration] Composite registration không bao giờ dùng first-match detection
    Biết rằng repository chứa file có thể nhận diện cho hai hệ sinh thái
    Và registry đăng ký rõ hai provider
    Khi quality_check chạy
    Thì cả hai provider đã đăng ký đều được gọi
    Và thứ tự file trong repository không ảnh hưởng

  Kịch bản: [Tier C - Integration] Thiếu registry thì fail closed
    Biết rằng consumer repository không có check_quality registry
    Khi quality_check bắt đầu
    Thì run bị BLOCKED
    Và không thử legacy platform fallback
```

## UC5 Thực Thi Rust Quality

```gherkin
Tính năng: Thực thi Rust quality provider

  Kịch bản: [Tier C - Integration] Profile epic thành công chạy Rust capability đã khai báo
    Biết rằng cấu hình rust-quality khai báo command format, check, lint, test, architecture và coverage bắt buộc
    Và mọi command thành công ở mức threshold yêu cầu hoặc cao hơn
    Khi rust-quality-check chạy profile epic
    Thì nó trả PASS với evidence cho mọi capability bắt buộc
    Và working tree cùng HEAD không đổi

  Kịch bản: [Tier A - Unit] Command array sai bị từ chối
    Biết rằng Rust capability được cấu hình bằng shell string có interpolation thay vì argument array
    Khi configuration validation chạy
    Thì provider trả BLOCKED
    Và command không được thực thi

  Kịch bản: [Tier A - Unit] Defect đã phát hiện chuyển sang FAIL
    Biết rằng Clippy chạy đầy đủ ở cấp process và báo denied warning
    Khi provider phân loại outcome
    Thì check status là FAIL
    Và không bị phân loại là infrastructure blocker

  Kịch bản: [Tier C - Integration] Repository identity race làm Rust evidence mất hiệu lực
    Biết rằng Rust command bắt đầu trên SHA được yêu cầu
    Khi HEAD đổi trước lúc provider ghi finished_head
    Thì provider trả BLOCKED
    Và command exit thành công không thể khôi phục PASS

  Kịch bản: [Tier C - Integration] Architecture command bắt buộc bị thiếu
    Biết rằng profile epic yêu cầu enforcement architecture feature-first
    Và không cấu hình architecture command xtask của project
    Khi rust-quality-check kiểm tra capability
    Thì nó trả BLOCKED
    Và không thay cargo-modules, ArchUnitRust hoặc syn làm nguồn có thẩm quyền
```

## UC6 Author Provider Và Aggregation

```gherkin
Tính năng: Author provider và aggregate result

  Kịch bản: [Tier A - Unit] Provider result hợp lệ thỏa contract chung
    Biết rằng provider trả mọi field bắt buộc cho identity được yêu cầu
    Và mọi evidence reference đúng định dạng
    Khi result validation chạy
    Thì result được chấp nhận để aggregate
    Và check được sắp theo stable check ID

  Kịch bản: [Tier A - Unit] Field result lạ bị từ chối ở contract version một
    Biết rằng provider result chứa status field viết sai và một field thay thế không biết
    Khi schema validation chạy
    Thì result trở thành BLOCKED
    Và field viết sai không thể bị bỏ qua âm thầm

  Kịch bản: [Tier A - Unit] Status precedence bảo toàn failure
    Biết rằng một provider hợp lệ trả FAIL
    Và provider hợp lệ khác trả BLOCKED
    Khi status được reduce
    Thì overall verdict là FAIL
    Và chi tiết của cả hai provider vẫn hiện diện

  Kịch bản: [Tier C - Integration] Result trùng do concurrent delivery bị từ chối
    Biết rằng một provider được chọn trả hai result document
    Khi result set được đối chiếu với execution plan
    Thì provider đó bị BLOCKED do identity trùng
    Và aggregation không thể tùy ý chọn một document

  Kịch bản: [Tier A - Unit] Result bắt buộc toàn not-applicable bị chặn
    Biết rằng provider bắt buộc chỉ trả check NOT_APPLICABLE
    Khi applicability evidence được đánh giá
    Thì provider được chuyển thành BLOCKED
    Và verdict cuối không thể là PASS
```

## Ma Trận Truy Vết

| Requirement | Scenario |
|-------------|----------|
| Lời gọi trực tiếp mặc định `pr` | UC1 happy path |
| Profile không biết hoặc bị hạ cấp fail closed | UC1 edge, UC2 boundary, UC3 state |
| Mọi provider phù hợp đều chạy | UC1 happy path, UC4 happy và composite path |
| Thiếu manifest hoặc tool là `BLOCKED` | UC4 failure, UC3 và UC5 failure |
| Verdict gắn với SHA bất biến | UC2 happy, state và race; UC5 race |
| Thứ tự xác định khi concurrent | UC1 concurrency, UC3 concurrency, UC6 happy path |
| `FAIL > BLOCKED > PASS` | UC6 precedence |
| `NOT_APPLICABLE` bắt buộc không thể pass | UC6 applicability boundary |
| Rust architecture authority do project sở hữu | UC5 architecture failure |
| Provider output có version và strict | UC6 happy và unknown-field path |
