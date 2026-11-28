# Sổ tay Nhanh (Quick-Guide): dev-config

> Bản dịch của [dev-config-quick-guide.en.md](dev-config-quick-guide.en.md).

## Mục lục

- [Meta Data](#meta-data)
- [1. Bảng Tra nhanh 10 Giây](#1-bảng-tra-nhanh-10-giây)
- [2. Nơi lưu Cấu hình và Tầng nào Thắng](#2-nơi-lưu-cấu-hình-và-tầng-nào-thắng)
- [3. Chọn Provider, Model và Effort](#3-chọn-provider-model-và-effort)
- [4. Dùng Nhiều Profile agy](#4-dùng-nhiều-profile-agy)
- [5. Khi Cạn Quota](#5-khi-cạn-quota)
- [6. Xử lý Sự cố](#6-xử-lý-sự-cố)
- [7. Tham chiếu Lệnh và Mã Thoát](#7-tham-chiếu-lệnh-và-mã-thoát)

## Meta Data

- **Kind**: `document`
- **Audience**: Human Architect (Role 1.0)
- **Diátaxis mode**: `how-to`
- **Non-goals**: Không đi sâu vào mã cài đặt Python bên trong `scripts/persona_config.py`, `scripts/agy_profile_pool.py`, `scripts/agy_dispatch.py` hay `scripts/dev_config.py`
- **Acceptance**: Trong vòng 30 giây, Human Architect chọn và chạy được đúng lệnh `/d3nexus:dev-config` để kiểm tra binding các vai trò, đổi provider/model/effort, cấu hình pool profile `agy`, xử lý khi cạn quota hoặc gỡ lỗi ghi đè giữa các tầng mà không gặp lỗi cú pháp CLI
- **Source Spec**: [2026-11-17-four-persona-governance-design.en.md](../.devtool/epic/four_persona_governance/2026-11-17-four-persona-governance-design.en.md)

## 1. Bảng Tra nhanh 10 Giây

| Mục tiêu | Lệnh chính xác |
| :--- | :--- |
| Xem binding đang áp dụng, nguồn tầng, turn budget và cảnh báo | `/d3nexus:dev-config status` |
| Gắn cả ba vai trò sang Claude (global) | `/d3nexus:dev-config --provider claude` |
| Gắn cả ba vai trò sang Codex (project) | `/d3nexus:dev-config --provider codex --scope project` |
| Chuyển Programmer sang Kiro Sonnet (`claude-sonnet-5.5`, `high`) | `/d3nexus:dev-config set programmer kiro-sonnet high` |
| Chuyển Programmer sang Codex trong phạm vi project | `/d3nexus:dev-config set programmer codex-gpt xhigh --scope project` |
| Khám phá các profile Antigravity chưa nằm trong pool | `/d3nexus:dev-config profiles discover` |
| Thêm profile của riêng bạn vào pool `agy` toàn cục | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| Cập nhật độ ưu tiên và mức đồng thời cho `profile_a` trong pool `agy` | `/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2` |
| Xem lease đang giữ, thời gian reset và cache quota của pool | `/d3nexus:dev-config profiles list` |
| Bật chế độ tiết kiệm quota theo profile (mặc định 5h, giảm nửa turns) | `/d3nexus:dev-config low-quota on` |
| Chạy cổng kiểm tra quota trước wave cho mọi vai trò | `/d3nexus:dev-config quota-check` |
| Xem cả bốn giới hạn số vòng duyệt (`limits`) và tầng nguồn | `/d3nexus:dev-config limits` |
| Đặt giới hạn vòng Principal (2) và Cross-Model (4) độc lập ở global | `/d3nexus:dev-config limits --principal-review 2 --cross-model-review 4 --scope global` |
| Đặt giới hạn task-review (3) và tắt vòng sửa lỗi (0) ở project | `/d3nexus:dev-config limits --task-review 3 --fix 0 --scope project` |
| Xem thứ tự ưu tiên, model provider và ngưỡng quota review ngoài | `/d3nexus:dev-config review status` |
| Đặt thứ tự ưu tiên review ngoài dùng chung ở global | `/d3nexus:dev-config review priority codex,claude,kiro,agy --scope global` |
| Đặt model cho provider review ngoài (bí danh hoặc ID gốc) | `/d3nexus:dev-config review set agy --model argon --effort medium --scope global` |
| Tinh chỉnh ngưỡng quota cho review ngoài, `quota-check` và `agy` dispatch | `/d3nexus:dev-config review thresholds --5h 0.25 --kiro-credits 25.0 --scope global` |

## 2. Nơi lưu Cấu hình và Tầng nào Thắng

`/d3nexus:dev-config` phân giải cấu hình cho ba vai trò AI (`ai_architect_reviewer` Role 2.1, `orchestrator` Role 2.2 và `programmer` Role 2.3), cả bốn giới hạn vòng duyệt (`max_task_review_passes`, `max_fix_passes`, `max_principal_review_passes`, `max_cross_model_review_passes`) và cấu hình review ngoài (`review.provider_priority`, `review.providers`, `review.quota_thresholds`) qua năm tầng ưu tiên, hợp nhất theo từng khóa để tầng cao hơn thắng:

| Tầng | Đường dẫn | Cờ phạm vi | Mục đích |
| :--- | :--- | :--- | :--- |
| 1. Mặc định kit | `scripts/personas.default.json` | — | Danh mục model sẵn có, bảy preset chuẩn, turn budget (`8`), giới hạn vòng mặc định (`2`, `1`, `3`, `3`) và cấu hình review mặc định |
| 2. Dự phòng cũ | `.devtool/review_config.json` | — | Dự phòng chỉ đọc (read-only) cho các khóa review ngoài chưa có ở tầng global và project (không tự tạo mới hay ghi đè) |
| 3. Global | `$REAL_HOME/.d3nexus/personas.json` | `--scope global` *(mặc định)* | Cấu hình vai trò, giới hạn vòng và review ngoài của người dùng dùng chung qua mọi repository |
| 4. Project | `.agents/config/personas.json` | `--scope project` | Ghi đè riêng cho một repository (kể cả các worktree) |
| 5. Lệnh chạy | Cờ CLI (`--programmer-model`, `--provider-priority`, `--max-rounds`, v.v.) | — | Ghi đè cho một lần chạy tự động hoặc phiên review |

Thứ tự phân giải: hợp nhất sâu các tầng (`CLI > project > global > legacy > kit`) -> chọn `active_preset` hiệu lực -> áp dụng `overrides.<persona>` cùng `review` / giới hạn vòng đã hợp nhất -> áp dụng cờ CLI lúc gọi. Trạng thái runtime của review ngoài (`last_used_provider`) được tách riêng vào `.devtool/state/review_runtime.json` để giữ nguyên `.devtool/review_config.json` trên đĩa. Các khóa cũ `overrides.<persona>.profile` trong `personas.json`, `.devtool/review_config.json["providers"]["programmer"|"assistant"]`, các khóa review cũ trong `.devtool/review_config.json` và biến môi trường `AGY_PROGRAMMER_MODEL`, `AGY_PROGRAMMER_EFFORT`, `AGY_ASSISTANT_MODEL` hiển thị thành cảnh báo không chặn trong `status`.

Kiểm tra bảng phân giải và nguồn gốc từng trường bằng `status`:

```bash
/d3nexus:dev-config status
/d3nexus:dev-config status --json
```

## 3. Chọn Provider, Model và Effort

### Dạng vị trí `set`, dạng cờ `set` và lệnh tắt `--provider`

Dùng `set` để ghi đè một vai trò (`ai_architect_reviewer`, `orchestrator` hoặc `programmer`), hoặc `--provider` để chuyển cả ba vai trò theo preset của provider đó:

```bash
/d3nexus:dev-config --provider agy
/d3nexus:dev-config --provider claude
/d3nexus:dev-config --provider codex --scope project
/d3nexus:dev-config preset gemini-saver --scope global
/d3nexus:dev-config set programmer kiro-sonnet high
/d3nexus:dev-config set programmer codex-gpt xhigh --scope project
/d3nexus:dev-config set programmer --provider kiro --model claude-sonnet-5.5 --effort high
/d3nexus:dev-config set programmer hydrogen xhigh --fallback claude-sonnet --scope global
/d3nexus:dev-config reset programmer --scope project
/d3nexus:dev-config reset --scope global
/d3nexus:dev-config preset default --scope project
```

- **Dạng vị trí vs dạng cờ**: `set PERSONA MODEL [EFFORT]` nhận tên bí danh trong danh mục (`kiro-sonnet`, `codex-gpt`, `hydrogen`, `orchestrator-argon`). Dạng cờ nhận `--provider` (`agy`, `claude`, `codex`, `kiro`), `--model` (bí danh hoặc `id` trong danh mục như `claude-sonnet-5.5`) và `--effort` (bắt buộc với model chọn được effort và bỏ qua với model cố định effort có `efforts: ["none"]`). Trộn tham số vị trí với `--model` hoặc `--effort` sẽ thoát mã `1`.
- **Lệnh tắt `--provider`**: Cờ cấp cao `--provider agy|claude|codex` chỉ ghi `active_preset` (`default`, `all-claude` hoặc `all-codex`) mà không xóa `overrides` đang có, và cảnh báo trên `stderr` nếu một override hoặc tầng project đang che phủ vai trò. `kiro` không có lệnh tắt `--provider` cấp cao; hãy dùng `set` hoặc `preset codex-kiro`.
- **Đưa preset của project về `default`**: `reset` chỉ xóa `overrides` và giữ nguyên `active_preset` cho các vai trò còn lại, nên sau `--provider codex --scope project` và `reset programmer --scope project`, hãy chạy `/d3nexus:dev-config preset default --scope project` để trả preset của tầng project về `default`.
- **Chọn tương tác**: Trong khung chat, `/d3nexus:dev-config --models` (hoặc `--models --persona programmer`) hiển thị bảng danh mục và hỏi lần lượt để chọn model và effort cho từng vai trò.

### Các Preset sẵn có và Quy tắc Effort

| Preset | `ai_architect_reviewer` (2.1) | `orchestrator` (2.2) | `programmer` (2.3) |
| :--- | :--- | :--- | :--- |
| `default` (`--provider agy`) | `argon` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `gemini-saver` | `argon` `medium` | `hydrogen` `medium` | `hydrogen` `high` |
| `claude-hybrid` | `claude-opus` `high` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `all-hydrogen` | `hydrogen` `xhigh` | `hydrogen` `high` | `hydrogen` `xhigh` |
| `codex-kiro` | `kiro-opus` `high` | `codex-gpt` `medium` | `codex-gpt` `xhigh` |
| `all-claude` (`--provider claude`) | `claude-opus` `high` | `claude-sonnet` `high` | `claude-sonnet` `high` |
| `all-codex` (`--provider codex`) | `codex-gpt` `high` | `codex-terra` `medium` | `codex-terra` `medium` |

- **Kiểm tra effort & thay thế `{effort}`**: Mỗi bí danh trong danh mục khai báo tập `efforts` hợp lệ (`argon`: `low|medium|high`; `hydrogen`: `low|medium|high|xhigh`; `claude-opus`/`codex-gpt`/`codex-terra`: `medium|high|xhigh`; `claude-sonnet`: `medium|high`; `kiro-sonnet`/`kiro-opus`: `high`). Với model `agy`, `{effort}` trong `id` được thay bằng effort đã chọn (ví dụ `gemini-4-hydrogen-xhigh`).
- **Quản lý bí danh danh mục**: Xem hoặc thêm bớt bí danh ngay lúc chạy mà không phải sửa tay JSON:

```bash
/d3nexus:dev-config models
/d3nexus:dev-config models --persona programmer --json
/d3nexus:dev-config models add custom-sonnet --cli claude --id sonnet-custom --efforts medium,high --quota-pool provider --scope global
/d3nexus:dev-config models remove custom-sonnet --scope global
```

- **Điều phối pool `agy` thuần theo độ ưu tiên**: `set` chỉ gán provider, model, effort và `--fallback` tùy chọn cho vai trò — không gắn cứng tài khoản Antigravity. Việc chọn tài khoản cho các vai trò `agy` được điều khiển hoàn toàn bởi `priority` và `max_concurrent` của pool qua `/d3nexus:dev-config profiles set` hoặc bảng `🔑 Agy Profile Pool` trên Task Dashboard; các khóa cũ `overrides.<persona>.profile` trong `personas.json` bị bỏ qua và hiển thị cảnh báo trong `status`.

## 4. Dùng Nhiều Profile agy

Khai báo danh sách profile ưu tiên rõ ràng trong `$REAL_HOME/.d3nexus/agy_profiles.json` để các phiên điều phối chạy song song chia sẻ tài khoản Antigravity an toàn qua `$REAL_HOME/.d3nexus/agy_profile_leases.json`:

```bash
/d3nexus:dev-config profiles discover
/d3nexus:dev-config profiles discover --json
/d3nexus:dev-config profiles probe profile_a
/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1
/d3nexus:dev-config profiles add profile_b --priority 2 --max-concurrent 1
/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2
/d3nexus:dev-config profiles list
/d3nexus:dev-config profiles list --json
/d3nexus:dev-config profiles probe
/d3nexus:dev-config profiles release profile_a --force
/d3nexus:dev-config profiles remove profile_b
/d3nexus:dev-config profiles clear profile_a
/d3nexus:dev-config profiles clear
```

- **Khám phá, probe trước khi thêm và chỉ thêm các profile do bạn sở hữu**: `profiles discover` liệt kê các thư mục Antigravity không phải symlink từ `check-quota` (`agy_quota.get_all_profiles()`) chưa nằm trong pool mà không fetch quota hay mở khóa keychain, đồng thời in gợi ý các bước tiếp theo (`profiles probe <name>` rồi `profiles add <name>`). `profiles probe NAME` chạy được **trước** khi thêm vào pool: lệnh chỉ fetch quota của duy nhất một profile đó, in cửa sổ 5 giờ và theo tuần kèm kết luận so với `quota_thresholds`, kiểm tra xem có tiến trình thường trú đang giữ không, gợi ý `/d3nexus:dev-config profiles add NAME` nếu dùng được, và không ghi gì vào `agy_profiles.json` hay `agy_profile_leases.json`. Lệnh `probe` chỉ dùng phiên đăng nhập của đúng profile bạn nêu tên, không bao giờ dùng phiên của các profile khác. Với một profile ngoài pool dùng được, lệnh in ra:

```text
Probed 'profile_a' (not in the pool): status=ACTIVE
  Quota: 5H=85.0% (>= 15.0%), 7D=65.0% (> 2.0%) -> pass
  Resident process: no
  Verdict: usable
  Next step: /d3nexus:dev-config profiles add profile_a
```

  Nếu một cửa sổ không đạt ngưỡng, lệnh in `-> fail (5h ... vs 15.0%)` hoặc `-> fail (weekly ... vs 2.0%)` và `Verdict: not usable (5h below floor)` / `Verdict: not usable (weekly below floor)`. Một profile đang có tiến trình thường trú (IDE hoặc CLI đang mở dưới profile đó) báo `Resident process: yes (held by a running process)` và `Verdict: not usable (held by resident process)` *(hoặc `yes (host profile)` nếu là profile đang host phiên)* — profile đó sẽ không được `dispatch` ngoài host khởi chạy lên và phải được đóng trước. Hãy thêm **duy nhất các profile của chính bạn** (`profile_a`, `profile_b`) sau khi probe, và đặt mọi lệnh cần trạng thái pool (`profiles set`, `release`, `remove`, `clear`, `dispatch`) sau `profiles add`. Khi gọi `profiles probe` với profile đã ở trong pool hoặc không truyền tên, lệnh làm mới cache quota trong `agy_profile_leases.json` và in `Probed '<name>': status=<status>`.
- **Điều phối pool thuần theo độ ưu tiên**: `dispatch` và `quota-check` xét các profile trong pool `agy` nghiêm ngặt theo thứ tự `--priority` (số nhỏ hơn được ưu tiên trước) tới trần `--max-concurrent` của từng profile, rồi tự xoay sang bậc ưu tiên kế tiếp khi profile đã chạm trần lease, đang bận hoặc cạn quota. Điều chỉnh trực tiếp trên bảng `🔑 Agy Profile Pool` của Task Dashboard hoặc bằng `/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2`.
- **Lease và cô lập phiên**: Các profile khác máy chủ chỉ giữ tối đa 1 lease `ag_run` tại một thời điểm (`zsh -ic 'ag_run ...'`, được kiểm tra preflight); profile đang host phiên hiện tại cho phép tối đa `--max-concurrent` (mặc định `2`) lease trực tiếp. Lease quá hạn (`lease_ttl_seconds = 180s`) hoặc có PID cục bộ đã tắt sẽ tự động hết hiệu lực.
- **Cửa sổ quota 5 giờ và theo tuần**: Với nhóm `gemini5h` (`hydrogen`), `acquire` và `quota-check` kiểm tra **đồng thời** `5h >= 15%` (`5h_min_fraction = 0.15`) **và** `weekly > 2%` (`7d_min_fraction = 0.02`). Với `argonWeekly` (`argon`), kiểm tra `argonWeekly >= 10%` (`agy_argon_min_fraction = 0.10`). Profile trượt một trong hai cửa sổ khi `acquire` (dispatch) sẽ bị đánh dấu cạn quota tới thời điểm reset tương ứng (và làm `quota-check` thoát mã `2`).

## 5. Khi Cạn Quota

Dùng chế độ tiết kiệm quota theo profile (`low-quota`, bí danh `--low-quota`) khi thấy thanh 5 giờ gần chạm đáy, và dựa vào `quota-check` trước mỗi wave và vòng sửa lỗi:

```bash
/d3nexus:dev-config low-quota on
/d3nexus:dev-config low-quota on --for 3 --profile profile_a
/d3nexus:dev-config low-quota off --profile profile_a
/d3nexus:dev-config checkpoint --turns 6 --scope global
/d3nexus:dev-config quota-check
/d3nexus:dev-config quota-check --personas orchestrator,programmer --json
```

- **Chế độ Low-quota**: Lưu theo từng profile dưới khóa `low_quota` ở tầng global với thời hạn mặc định 5 giờ (`--for HOURS`). Chế độ này giảm một nửa `max_orchestrator_turns_before_checkpoint` (mặc định `8` -> `4`), cắt bớt lời dẫn không thiết yếu, hoàn thành nốt wave đang chạy, ghi `--checkpoint low_quota_stop`, in prompt tiếp tục, ghi pending decision và dừng an toàn.
- **`quota-check` & `review thresholds`**: `quota-check` đánh giá pool quota mà từng vai trò tiêu thụ (`argonWeekly`, `gemini5h` + `geminiWeekly`, hoặc quota của provider `claude`/`codex`/`kiro`) so với `review.quota_thresholds` đã phân giải (tùy chỉnh qua `/d3nexus:dev-config review thresholds --5h 0.25 --7d 0.05 --kiro-frac 0.03 --kiro-credits 25.0 --argon 0.10 --scope global`). Thoát `0` nếu đủ hoặc không đọc được (`quota_unknown`, không chặn); thoát `2` nếu thiếu quota.
- **Báo cáo dừng & không tự ý đổi model**: Khi toàn bộ pool `agy` cạn quota (`no_profile`, thoát `2`) hoặc `quota-check` thất bại, Orchestrator/runner ghi `--checkpoint quota_low`, ghi pending decision loại `quota` hiển thị trên `/d3nexus:check-tasks`, liệt kê từng profile cùng cửa sổ bị trượt, mốc reset sớm nhất, và các lệnh khôi phục cụ thể (`/d3nexus:dev-config profiles clear`, `/d3nexus:dev-config set programmer codex-gpt xhigh`, `/d3nexus:dev-config set programmer kiro-sonnet high`). **Kit không bao giờ tự động chuyển sang model khác** — Role 1.0 quyết định chờ, nạp thêm, clear hay chuyển model.

## 6. Xử lý Sự cố

| Triệu chứng | Nguyên nhân | Lệnh xử lý |
| :--- | :--- | :--- |
| `Error: unrecognized arguments: --profile` khi chạy `dev-config set` | Cờ `set ... --profile` theo từng vai trò đã ngừng hỗ trợ (`--profile` chỉ còn dùng cho `low-quota`); việc chọn tài khoản `agy` nay hoàn toàn theo độ ưu tiên và mức đồng thời của pool | `/d3nexus:dev-config profiles set profile_a --priority 1 --max-concurrent 2` *(hoặc chỉnh trên bảng `🔑 Agy Profile Pool` của Task Dashboard)* |
| `Legacy setting '... personas.json overrides.<persona>.profile' is ignored` trong `status` | `personas.json` vẫn còn mục `overrides.<persona>.profile` từ phiên bản cũ | Chạy lại `/d3nexus:dev-config set <persona> <model> <effort>` *(hoặc `/d3nexus:dev-config reset <persona>`)* ở phạm vi đó để ghi lại override sạch |
| `warning: programmer is still bound to ... by the project layer` sau `--provider` hoặc `preset` | Override ở tầng cao hơn hoặc `active_preset` của project đang che phủ thay đổi ở global | `/d3nexus:dev-config reset programmer --scope project` |
| `Error: Profile 'profile_a' is not in the agy pool` (hoặc `is not in the pool`) | `profiles set`/`remove`/`release`/`clear` phải trỏ tới một profile đã đăng ký trong `$REAL_HOME/.d3nexus/agy_profiles.json` | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| `profiles probe profile_a` báo lỗi `neither in the pool (...) nor in discovered profiles (...)` | `profile_a` không nằm trong pool và không phải thư mục profile mà `check-quota` liệt kê | `/d3nexus:dev-config profiles discover` |
| `profiles remove` bị từ chối vì còn live lease | Đang có orchestrator hoạt động hoặc lease chưa hết hạn trong `agy_profile_leases.json` | `/d3nexus:dev-config profiles release profile_a --force` |
| `Stopped: all agy profiles are out of quota.` (`no_profile`, thoát `2`) | Mọi profile trong pool đều không đạt ngưỡng 5 giờ hoặc theo tuần | Chờ/nạp quota rồi chạy `/d3nexus:dev-config profiles clear`, hoặc chuyển sang `/d3nexus:dev-config set programmer kiro-sonnet high` |
| Dừng `MODEL_UNAVAILABLE` hoặc thấy `(!)` cạnh CLI trong `status` | Thiếu binary CLI trên `PATH` hoặc chưa đăng nhập xác thực | Cài/đăng nhập lại CLI hoặc đổi qua `/d3nexus:dev-config set programmer claude-sonnet high` |
| `Cannot remove model alias ... referenced by ...` | Preset, override, fallback hoặc `review.providers.<cli>.model` vẫn đang tham chiếu tới bí danh đó | `/d3nexus:dev-config reset --scope global` hoặc `/d3nexus:dev-config review reset <provider> --scope global`, rồi xóa bí danh |
| `Warning: project override in .agents/config/personas.json masks global ...` | Lệnh ghi `limits` hoặc `review` ở global đã thành công nhưng `.agents/config/personas.json` đang ghi đè cùng khóa đó trong repo này | `/d3nexus:dev-config limits reset <target> --scope project` hoặc `/d3nexus:dev-config review reset <target> --scope project` |
| Cảnh báo `.devtool/review_config.json` cũ trong `status` | Repository vẫn còn tệp `.devtool/review_config.json` cũ (chỉ đọc dự phòng; `last_used_provider` runtime nay lưu ở `.devtool/state/review_runtime.json`) | Di chuyển các khóa sang `/d3nexus:dev-config review` và `/d3nexus:dev-config limits` |
| Cảnh báo `quota_unknown` khi chạy `quota-check` (thoát `0`) | Fetcher không trả dữ liệu hoặc CLI chưa hỗ trợ đọc quota trực tiếp | Cảnh báo không chặn; kiểm tra trực tiếp bằng `/d3nexus:check-quota` |

## 7. Tham chiếu Lệnh và Mã Thoát

Mọi lệnh con đều có thể gọi trực tiếp qua `python3 scripts/dev_config.py ...` (riêng `dispatch` yêu cầu `--prompt-file` và thư mục `--cwd` đã tồn tại):

```bash
python3 scripts/dev_config.py status
python3 scripts/dev_config.py models
python3 scripts/dev_config.py profiles discover
python3 scripts/dev_config.py profiles probe profile_a
python3 scripts/dev_config.py profiles probe
python3 scripts/dev_config.py resolve programmer --format json --mode write
python3 scripts/dev_config.py resolve ai_architect_reviewer --format argv --mode read-only
python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file .devtool/prompt.md --cwd . --log .devtool/dispatch.log --epic demo --task task_01 --slot 1 --role orchestrator --wait 30
```

- **Giới hạn số vòng duyệt (`dev-config limits`)**: Hỗ trợ bốn trần độc lập (`max_task_review_passes` mặc định `2`, `max_fix_passes` mặc định `1` và cho phép `0`, `max_principal_review_passes` mặc định `3`, `max_cross_model_review_passes` mặc định `3`):
  - Xem: `/d3nexus:dev-config limits` hoặc `/d3nexus:dev-config limits --json`
  - Cập nhật: `/d3nexus:dev-config limits [--task-review N] [--fix N] [--principal-review N] [--cross-model-review N] [--scope global|project]`
  - Đặt lại: `/d3nexus:dev-config limits reset [task|fix|principal|cross-model|all] [--scope global|project]`
- **Review ngoài (`dev-config review`)**: Dùng chung `provider_priority` cho `/principal-review` và `/cross-model-review`, hỗ trợ model theo bí danh danh mục hoặc ID gốc (bí danh danh mục kiểm tra quyền sở hữu CLI, mở rộng `{effort}` và tự điền `effort: "none"` cho bí danh cố định effort như `orchestrator-argon`; ID gốc và tag Ollama được giữ nguyên; `--host` chỉ áp dụng cho `ollama`), dùng chung `quota_thresholds` và cô lập `last_used_provider` vào `.devtool/state/review_runtime.json`:
  - Xem: `/d3nexus:dev-config review status` hoặc `/d3nexus:dev-config review status --json`
  - Thứ tự ưu tiên: `/d3nexus:dev-config review priority codex,claude,kiro,agy [--scope global|project]`
  - Model của provider: `/d3nexus:dev-config review set <claude|codex|kiro|agy|ollama> --model <alias-or-id> [--effort <level>] [--host <http(s)://url>] [--scope global|project]`
  - Ngưỡng quota: `/d3nexus:dev-config review thresholds [--5h F] [--7d F] [--kiro-frac F] [--kiro-credits N] [--argon F] [--scope global|project]`
  - Đặt lại: `/d3nexus:dev-config review reset [priority|providers|claude|codex|kiro|agy|ollama|thresholds|all] [--scope global|project]`

- **`profiles probe [NAME]`**: Khi `NAME` là profile ngoài pool do `profiles discover` trả về, lệnh chỉ fetch quota của `NAME`, in kiểm tra ngưỡng 5H/7D, kiểm tra tiến trình thường trú và `Verdict: usable` / `not usable (...)` mà không ghi vào `agy_profiles.json` hay `agy_profile_leases.json` (thoát mã `0`); khi `NAME` đã ở trong pool hoặc bỏ trống, lệnh làm mới cache quota trong `agy_profile_leases.json` và in `Probed '<name>': status=<status>`; thoát mã `1` khi `NAME` không nằm trong pool lẫn danh sách khám phá.

| Mã thoát | Ý nghĩa |
| :--- | :--- |
| `0` | Thành công (kể cả `profiles probe NAME` ngay cả khi kết luận `not usable`); hoặc `quota-check` đủ quota / `quota_unknown` |
| `1` | Lỗi dữ liệu cấu hình, lỗi tham số CLI, tên không tồn tại trong `profiles probe`, `task_failure`, `model_unavailable` hoặc `preflight_failed` |
| `2` | Cổng quota không đủ (`quota-check`), `no_profile` (toàn bộ pool cạn/bận) hoặc `quota_midrun` |
