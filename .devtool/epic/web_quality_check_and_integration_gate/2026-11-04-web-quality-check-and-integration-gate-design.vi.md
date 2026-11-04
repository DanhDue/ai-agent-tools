# Đặc tả Thiết kế Web Quality Check và Integration Gate

## Mục lục

- [Mục lục](#mục-lục)
- [Metadata](#metadata)
- [Bối cảnh và Vấn đề](#bối-cảnh-và-vấn-đề)
- [Mục tiêu và Giới hạn](#mục-tiêu-và-giới-hạn)
- [Kiến trúc và Chuẩn Kiểm thử 3 Lớp](#kiến-trúc-và-chuẩn-kiểm-thử-3-lớp)
- [Chống Ngụy biện và Cơ chế Phản biện Nghi vấn](#chống-ngụy-biện-và-cơ-chế-phản-biện-nghi-vấn)
- [Đặc tả Kỹ thuật Provider Web Quality](#đặc-tả-kỹ-thuật-provider-web-quality)
- [Tích hợp Registry Đa Repo và Gate 4 Đa Nền tảng](#tích-hợp-registry-đa-repo-và-gate-4-đa-nền-tảng)
- [Nâng cấp Dev-Designer và Dev-Implementation](#nâng-cấp-dev-designer-và-dev-implementation)
- [Tự động Sinh Kịch bản Smoke Test Bấm tay](#tự-động-sinh-kịch-bản-smoke-test-bấm-tay)
- [Rủi ro và Giải pháp Giảm thiểu](#rủi-ro-và-giải-pháp-giảm-thiểu)
- [Kế hoạch Kiểm chứng](#kế-hoạch-kiểm-chứng)

## Metadata

- **Tên Epic**: `web_quality_check_and_integration_gate`
- **Slug Epic**: `web-quality-check-and-integration-gate`
- **Ngày**: 2026-11-04
- **Tác giả**: Kiến trúc sư Con người & Trợ lý AI
- **Trạng thái**: Đã phê duyệt (Đã qua Gate 1)
- **Kho lưu trữ Mục tiêu**: `ai-agent-tools`, `D3Nexus`, `lyrics-sync`, `nexus`

## Bối cảnh và Vấn đề

Trong hệ sinh thái đa repo (`D3Nexus`, `lyrics-sync`, `nexus`), các kỹ sư thường xuyên đối mặt với khoảng cách lớn giữa thiết kế kiến trúc lý thuyết và hành vi thực tế khi chạy. Khoảng cách này buộc lập trình viên phải thực hiện quá nhiều thao tác kiểm thử thủ công (bấm tay) trên thiết bị và trình duyệt trước mỗi đợt release:

1. **Cái bẫy của Mock (Mocking Fallacy)**: Các bài kiểm thử đơn vị `[Tier A - Unit]` đạt tỷ lệ pass 100% bằng cách cô lập các thành phần bằng đối tượng mock (`when(...).thenReturn(...)`). Tuy nhiên, ứng dụng bị crash hoặc vỡ khi các thành phần được ghép nối với nhau trong runtime thật do lỗi đăng ký DI, lệch chuẩn parse JSON, hủy vòng đời component, hoặc xung đột timing trên stream event-bus.
2. **Thiếu Provider Web Quality ở Gate 4**: Hệ thống điều phối chất lượng (`d3nexus:quality_check`) đã có sẵn provider chuyên biệt cho Flutter, Android, iOS, Rust và Python, nhưng hoàn toàn thiếu provider `web-quality-check`. Dẫn đến:
   - Tại `D3Nexus`, Gate 4 chỉ xác thực `rust-core` (`d3nexus:rust-quality-check`), bỏ quên hoàn toàn ứng dụng web Astro + Vanilla TypeScript (`apps/learning-web`).
   - Tại `lyrics-sync`, Gate 4 chỉ xác thực `python-core` (`d3nexus:python-quality-check`), bỏ quên hoàn toàn 17 file Vanilla JavaScript (`src/lyrics_sync/preview/static/*.js`).
3. **Bài kiểm thử E2E giả lập chỉ chạy trong Node**: Nhiều bài test nằm dưới thư mục `tests/e2e/` thực chất chỉ chạy bằng `node:test` mà không hề render HTML thật, không kiểm tra kết nối Custom Elements, và không xác thực sự kiện DOM hay tọa độ hiển thị thực tế (`getBoundingClientRect`).
4. **Sự ngụy biện của AI (AI Rationalization)**: Các AI coding agent thường xuyên tự tìm đường tắt: khẳng định test Node là đủ, bỏ qua lỗi console trình duyệt, và né tránh việc chạy trình duyệt headless.

## Mục tiêu và Giới hạn

### Mục tiêu
- Xây dựng provider chuẩn hóa `web-quality-check` tuân thủ Hợp đồng Kết quả Provider v1 cho các dự án Astro TypeScript và Vanilla JavaScript.
- Xóa bỏ điểm mù tại Gate 4 bằng cách kích hoạt đăng ký đa provider đồng thời trong `D3Nexus` (`rust-core` + `learning-web`) và `lyrics-sync` (`python-core` + `preview-ui`).
- Thực thi nghiêm ngặt Chuẩn Kiểm thử 3 Lớp: Tier A (Unit), Tier C1 (Tích hợp Dưới da với DI thật và In-memory DB), và Tier C2 (Tích hợp Trình duyệt Headless với Playwright và Zero-Console-Error).
- Đưa Bảng Chống Ngụy biện và Cơ chế Phản biện Nghi vấn (lấy cảm hứng từ `addyosmani/agent-skills`) vào các quy trình kỹ năng.
- Tự động hóa quá trình xác nhận của con người bằng cách tự sinh tài liệu hướng dẫn 3–5 bước `manual_smoke_checklist.md` sau khi hoàn tất epic, giảm thời gian bấm tay từ 30 phút xuống còn 2 phút.

### Giới hạn
- Không migrate 17 file Vanilla JavaScript trong `lyrics-sync` sang TypeScript (việc kiểm tra kiểu dữ liệu được thực hiện tại chỗ thông qua JSDoc `// @ts-check` và `jsconfig.json`).
- Không thay thế bộ unit test hiện có trong `D3Nexus` hay `lyrics-sync` (các bài test nhanh này vẫn được giữ lại làm Tier A).
- Không yêu cầu bật emulator thiết bị nặng nề cho các cổng duyệt cục bộ PR/Epic (các bài test Tier C chạy headless qua Playwright và môi trường harness VM).

## Kiến trúc và Chuẩn Kiểm thử 3 Lớp

Kiến trúc thiết lập 3 phân tầng kiểm thử rõ ràng trên cả mobile và web:

1. **Tier A — Kiểm thử Đơn vị (Unit Testing)**:
   - Phạm vi: Thuật toán thuần, state machine toán học, bộ parse dữ liệu độc lập, và hàm tiện ích.
   - Thực thi: Trong tiến trình (Node.js, Dart VM, JVM, Python VM).
   - Mock: Cho phép mock các dependency bên ngoài. Tốc độ: <10ms mỗi test.
2. **Tier C1 — Kiểm thử Tích hợp Dưới da (Mobile & Backend)**:
   - Phạm vi: Controller giao diện (BLoC / ViewModel) xuyên suốt xuống kho lưu trữ cục bộ, bộ nhớ đệm và tuần tự hóa dữ liệu.
   - Bất biến: Zero-Domain-Mock. Nghiêm cấm mock UseCase hoặc Repository của domain. Bắt buộc dùng DI container thật và cơ sở dữ liệu in-memory (SQLite `:memory:`, Room in-memory).
   - Ranh giới mạng: Mock tại socket HTTP bằng các fixture JSON chuẩn từ `shared-contracts/`.
3. **Tier C2 — Kiểm thử Tích hợp Trình duyệt Headless (Web)**:
   - Phạm vi: Render DOM thật, Custom Elements, controller Vanilla JS/TS, thao tác click của người dùng, chuyển trang, định vị popover trực quan và tính toàn vẹn bố cục layout.
   - Bất biến: Zero-Console-And-Layout-Defect. Bên cạnh việc bắt lỗi ngoại lệ trang và `console.error`, hệ thống thực thi 3 cơ chế kiểm tra runtime bắt buộc:
     1. **Static Asset Network Trap**: Lắng nghe `page.on('response')` và đánh trượt bài test ngay lập tức nếu bất kỳ stylesheet (`.css`), script (`.js`) hoặc font nào trả về mã HTTP `>= 400`.
     2. **Trình hỗ trợ Kiểm tra Kiểu và Hình học Tính toán (`assertVisualIntegrity`)**: Xác thực các container UI cấu trúc (card, drawer, badge, thanh tiến trình) mang từ Visual Companion mockup thực sự được áp dụng style tính toán (`window.getComputedStyle(el)` không được rơi về mặc định unstyled `backgroundColor: rgba(0, 0, 0, 0)` + `borderWidth: 0px` + `padding: 0px`, và `getBoundingClientRect()` phải có `width > 0` và `height > 0`).
     3. **Bộ chặn Rò rỉ Trạng thái DOM và Trùng lặp Văn bản**: Xác nhận các phần tử trạng thái loại trừ lẫn nhau (ví dụ: spinner/tiền tố đang chạy vs badge terminal `THẤT BẠI` / `HOÀN THÀNH`, hoặc tiêu đề hiển thị vs tooltip/thẻ span ẩn hỗ trợ a11y) không được cùng hiển thị đồng thời (`display !== 'none'` và `visibility !== 'hidden'`), đồng thời phát hiện chuỗi văn bản bị trùng lặp liên tiếp trong tiêu đề card do các thẻ span ẩn không có CSS.
   - Ranh giới mạng: Chặn tại tầng socket trình duyệt thông qua `page.route()` của Playwright và trả về fixture JSON chuẩn từ hợp đồng.

## Chống Ngụy biện và Cơ chế Phản biện Nghi vấn

Học hỏi từ các nguyên tắc của `addyosmani/agent-skills`, tất cả quy trình lập trình và kiểm thử đều thực thi 5 quy tắc chống ngụy biện:

| Lời bào chữa của Agent | Quy tắc Phản biện Bắt buộc |
| :--- | :--- |
| "Một bài test Node.js là đủ để chứng minh tính năng web UI hoạt động." | **BỊ TỪ CHỐI**: Test Node chỉ chứng minh logic dữ liệu thuần. 80% lỗi web xảy ra ở truy vấn DOM, nổi bọt sự kiện và render CSS. Tier C bắt buộc phải chạy qua Playwright headless. |
| "Component này đơn giản; mock cứng dữ liệu trong stub là đủ." | **BỊ TỪ CHỐI**: Stub cấp method bỏ qua việc kiểm tra giải mã JSON và interceptor mạng. Bắt buộc phải dùng fixture cấp mạng (wire-level) từ `shared-contracts/`. |
| "Các lỗi đỏ trong console trình duyệt chỉ là cảnh báo vô hại." | **BỊ TỪ CHỐI**: Quy tắc Zero-Console-Error đánh trượt Gate 4 đối với bất kỳ lỗi console hoặc ngoại lệ chưa xử lý nào trong trình duyệt. |
| "Tôi không bật được simulator điện thoại nên tôi sẽ viết unit test thay thế." | **BỊ TỪ CHỐI**: Tier C mobile bắt buộc phải dùng Kiểm thử Dưới da với DI thật và lưu trữ in-memory. Unit test thuần túy không được gắn mác Tier C. |
| "Tôi đã mang cấu trúc HTML và logic JS từ Visual Companion mockup sang, và selector DOM khớp trong Playwright." | **BỊ TỪ CHỐI**: Mang HTML/JS mà không kiểm tra computed CSS style sẽ dẫn đến giao diện vỡ và không có style. Test Tier C2 cho UI component BẮT BUỘC phải assert các thuộc tính `getComputedStyle` và `getBoundingClientRect` (kích thước lớn hơn 0, chế độ hiển thị layout và khả năng hiển thị loại trừ lẫn nhau của các trạng thái, tôn trọng chuẩn text `.sr-only` được ẩn bằng clipping) so với thiết kế Visual Companion. |

Dưới Cơ chế Phản biện Nghi vấn (`CLAIM -> EXTRACT -> DOUBT -> RECONCILE`), Gate 4 sẽ rà soát để đảm bảo bài test Tier C thực sự kích hoạt luồng code production mà không mock hệ thống chính đang được kiểm thử.

## Đặc tả Kỹ thuật Provider Web Quality

Một kỹ năng mới `d3nexus:web-quality-check` được xây dựng tại thư mục `skills/web-quality-check/`:

1. **Hợp đồng Gọi thực thi**: Tuân thủ Hợp đồng Kết quả Provider v1, nhận `{ "profile": "<profile>", "base_ref": "<base_ref>", "repository_sha": "<sha>" }`.
2. **File Cấu hình**: Đọc file `.agents/quality/web-quality.json` từ thư mục gốc của repository.
3. **Các Khả năng (Capabilities)**:
   - `type_check`: Chạy `astro check` hoặc `tsc --noEmit` cho dự án TypeScript, hoặc `tsc --project jsconfig.json` cho dự án Vanilla JavaScript.
   - `lint`: Chạy linter của dự án (ESLint, Biome, hoặc Astro linter).
   - `test_unit`: Thực thi bộ unit test in-memory nhanh (Tier A).
   - `test_e2e`: Khởi chạy bộ Playwright headless (Tier C2) tích hợp bộ giám sát Zero-Console-And-Layout-Defect (hỗ trợ TypeScript qua `playwright-zero-error.fixture.ts` và Python qua `playwright_zero_error.py`).
   - `contracts`: Thực hiện kiểm tra chênh lệch hợp đồng đa repo.
4. **Ma trận Profile Bắt buộc**:
   - `pr`: Yêu cầu `type_check`, `lint`, và `test_unit`.
   - `epic` & `release`: Bắt buộc phải có `type_check`, `lint`, `test_unit`, VÀ `test_e2e` kèm bằng chứng thực thi watchdog (`build/test-results/playwright.xml`). Nếu thiếu `test_e2e` hoặc thiếu bằng chứng, trả về `BLOCKED`.
5. **Công cụ Xác thực**: Cung cấp script `validate_web_quality.py` để đảm bảo tính hợp lệ của schema và sự hiện diện của các binary thực thi trước khi chạy.

## Tích hợp Registry Đa Repo và Gate 4 Đa Nền tảng

Nhạc trưởng Gate 4 gốc (`d3nexus:quality_check`) thực hiện kích hoạt đa provider song song trên các kho lưu trữ. Để tôn trọng Ranh giới Độc lập Multi-Repo (Quy tắc 7), epic này trong `ai-agent-tools` bàn giao:
1. Bộ kỹ năng provider `web-quality-check` tái sử dụng và nâng cấp công cụ scaffolder.
2. Template fixture giám sát cho cả TypeScript (`playwright-zero-error.fixture.ts`) và Python (`playwright_zero_error.py`).
3. Đăng ký chất lượng cục bộ cho `ai-agent-tools` (`.agents/quality/check_quality.json` và `.agents/quality/python-quality.json`) sử dụng `python-quality-check`.
4. Tài liệu bàn giao ứng dụng (`.devtool/epic/web_quality_check_and_integration_gate/consumer_adoption_handoff.md`), ghi nhận chi tiết các mục cấu hình cho các repo hạ nguồn:
   - **`D3Nexus` (`.agents/quality/check_quality.json`)**: Provider 1: `rust-core` (`d3nexus:rust-quality-check`); Provider 2: `learning-web` (`d3nexus:web-quality-check`).
   - **`lyrics-sync` (`.agents/quality/check_quality.json`)**: Provider 1: `python-core` (`d3nexus:python-quality-check`); Provider 2: `preview-ui` (`d3nexus:web-quality-check`).
   - **`nexus` (`.agents/quality/check_quality.json`)**: Provider 1: `flutter-core` (`d3nexus:flutter-quality-check`).

## Nâng cấp Dev-Designer và Dev-Implementation

1. **`dev-designer` (Stage 2)**:
   - Khi phát hiện dự án Web, dòng `Integration results:` trong HLD bắt buộc phải trỏ tới kết quả của Playwright headless dạng JUnit XML (`build/test-results/playwright.xml`) sinh qua cờ `--reporter=junit`, đảm bảo `result_reports.py` (chỉ hỗ trợ JUnit XML hoặc Dart JSON) đọc nạp thông suốt.
   - Các bộ test Python bắt buộc phải bao gồm cờ `--junitxml=build/test-results/pytest.xml` trong lệnh thực thi.
   - Các kịch bản BDD cho Tier C phải bao gồm kỳ vọng tương tác DOM cụ thể và xác nhận qua wiremock.
2. **`dev-implementation` (Stage 3)**:
   - Nhúng Bảng Chống Ngụy biện trực tiếp vào quá trình thực thi tác vụ.
   - Kiểm tra provenance của test runner trong `task_contract.py` điều kiện 6 và `result_reports.py`: xác thực các tác vụ tuyên bố bao phủ kịch bản Tier C thực sự chạy test trình duyệt headless hoặc test dưới da thật, từ chối các báo cáo chỉ chứa unit mock.
   - Tạm dừng và báo cáo `BLOCKED` nếu code test mock chính component đang được kiểm thử.

## Tự động Sinh Kịch bản Smoke Test Bấm tay

Sau khi hoàn thành thành công tất cả tác vụ và Gate 4 trả về kết quả máy PASS, `dev-implementation` sẽ tự động sinh ra một tài liệu hỗ trợ con người:
- Đường dẫn: `.devtool/epic/<epic_dir>/manual_smoke_checklist.md`
- Nội dung: 3 đến 5 bước thủ công ngắn gọn, rõ ràng được trích xuất trực tiếp từ các kịch bản BDD Happy Path chính (gồm URL mục tiêu, hành động của người dùng, kết quả trực quan quan sát được).
- Lợi ích: Rút ngắn thời gian kiểm thử tự do của lập trình viên từ 30 phút mò mẫm xuống còn đúng 2 phút xác nhận có định hướng.

## Rủi ro và Giải pháp Giảm thiểu

| Rủi ro | Tác động | Chiến lược Giảm thiểu |
| :--- | :--- | :--- |
| Chi phí cài đặt Playwright trong CI / máy cục bộ | Gate 4 chạy chậm | Chỉ sử dụng Chromium headless; cache binary trình duyệt; profile `pr` chỉ chạy unit test, profile `epic` mới chạy Playwright. |
| Xung đột port khi khởi chạy preview server | Test không ổn định (flaky) | Cấu hình `webServer` của Playwright bind vào port động hoặc cổng chuyên dụng có probe kiểm tra healthcheck. |
| Cảnh báo console cũ của thư viện kích hoạt Zero-Console-Error | Đánh trượt nhầm (false positive) | Cho phép cấu hình danh sách loại trừ (allowlist) cho các cảnh báo bên thứ ba vô hại đã biết trong `.agents/quality/web-quality.json`. |

## Kế hoạch Kiểm chứng

1. **Kiểm chứng Hợp đồng Provider**:
   - Chạy `validate_web_quality.py` đối với file cấu hình mẫu `.agents/quality/web-quality.json`.
   - Chạy `quality_check` với profile `epic` tại `D3Nexus` và kiểm tra cả `rust-core` lẫn `learning-web` đều xuất ra phán quyết được chứng thực.
2. **Kiểm chứng Zero-Console-Error của Playwright**:
   - Cố tình chèn 1 dòng `console.error` vào trang test; xác nhận Playwright và Gate 4 báo cáo chính xác trạng thái `FAIL`.
   - Sửa lỗi và xác nhận Gate 4 chuyển sang `PASS`.
3. **Kiểm chứng Type-Checking cho Vanilla JS**:
   - Chạy `tsc --project jsconfig.json` trên thư mục `lyrics-sync/src/lyrics_sync/preview/static/` và xác nhận kết quả kiểm tra kiểu dữ liệu sạch sẽ.
4. **Kiểm chứng Tự sinh Checklist Bấm tay**:
   - Xác nhận rằng `generate_smoke_checklist.py` sinh và commit `.devtool/epic/<epic_dir>/manual_smoke_checklist.md` (3–5 bước) trong Phase 4 trước lượt chạy Gate 4 cuối cùng, bảo toàn trạng thái git sạch và tính toàn vẹn của candidate SHA đã được chứng nhận.
