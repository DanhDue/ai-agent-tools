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
| Ưu tiên `profile_a` cho Programmer dùng `agy` và tự xoay khi bận/cạn | `/d3nexus:dev-config set programmer --provider agy --profile profile_a --model hydrogen --effort xhigh` |
| Khám phá các profile Antigravity chưa nằm trong pool | `/d3nexus:dev-config profiles discover` |
| Thêm profile của riêng bạn vào pool `agy` toàn cục | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| Xem lease đang giữ, thời gian reset và cache quota của pool | `/d3nexus:dev-config profiles list` |
| Bật chế độ tiết kiệm quota theo profile (mặc định 5h, giảm nửa turns) | `/d3nexus:dev-config low-quota on` |
| Chạy cổng kiểm tra quota trước wave cho mọi vai trò | `/d3nexus:dev-config quota-check` |

## 2. Nơi lưu Cấu hình và Tầng nào Thắng

`/d3nexus:dev-config` phân giải cấu hình cho ba vai trò AI (`ai_architect_reviewer` Role 2.1, `orchestrator` Role 2.2 và `programmer` Role 2.3) qua bốn tầng, hợp nhất tuần tự để tầng sau ghi đè theo từng khóa:

| Tầng | Đường dẫn | Cờ phạm vi | Mục đích |
| :--- | :--- | :--- | :--- |
| 1. Mặc định kit | `scripts/personas.default.json` | — | Danh mục model sẵn có, bảy preset chuẩn, turn budget mặc định (`8`) |
| 2. Global | `$REAL_HOME/.d3nexus/personas.json` | `--scope global` *(mặc định)* | Cấu hình người dùng dùng chung qua mọi repository |
| 3. Project | `.agents/config/personas.json` | `--scope project` | Ghi đè riêng cho một repository (kể cả các worktree) |
| 4. Lệnh chạy | Cờ CLI của runner (`--programmer-model`, v.v.) | — | Ghi đè cho một lần chạy tự động |

Thứ tự phân giải: hợp nhất sâu các tầng -> chọn `active_preset` hiệu lực -> áp dụng `overrides.<persona>` đã hợp nhất -> áp dụng cờ CLI lúc gọi. Các khóa cũ `.devtool/review_config.json["providers"]["programmer"|"assistant"]` và biến môi trường `AGY_PROGRAMMER_MODEL`, `AGY_PROGRAMMER_EFFORT`, `AGY_ASSISTANT_MODEL` bị bỏ qua và hiển thị thành cảnh báo.

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
```

- **Dạng vị trí vs dạng cờ**: `set PERSONA MODEL EFFORT` nhận tên bí danh trong danh mục (`kiro-sonnet`, `codex-gpt`, `hydrogen`). Dạng cờ nhận `--provider` (`agy`, `claude`, `codex`, `kiro`), `--model` (bí danh hoặc `id` trong danh mục như `claude-sonnet-5.5`), `--effort` và `--profile`. Khi dùng cờ, cả `--model` và `--effort` đều bắt buộc; trộn tham số vị trí với `--model` hoặc `--effort` sẽ thoát mã `1`.
- **Lệnh tắt `--provider`**: Cờ cấp cao `--provider agy|claude|codex` chỉ ghi `active_preset` (`default`, `all-claude` hoặc `all-codex`) mà không xóa `overrides` đang có, và cảnh báo trên `stderr` nếu một override hoặc tầng project đang che phủ vai trò. `kiro` không có lệnh tắt `--provider` cấp cao; hãy dùng `set` hoặc `preset codex-kiro`.
- **Chọn tương tác**: Trong khung chat, `/d3nexus:dev-config --models` (hoặc `--models --persona programmer`) hiển thị bảng danh mục và hỏi lần lượt để chọn model và effort cho từng vai trò.

### Các Preset sẵn có, Quy tắc Effort và Kế thừa `--profile`

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

- **Ưu tiên `--profile` và quy tắc kế thừa từ tầng thấp**: `--profile` chỉ áp dụng cho model `agy` và phải là tên profile đã nằm trong pool (`--profile auto` xóa ưu tiên này). Mỗi lệnh `set` ghi lại trọn vẹn mục override của vai trò đó ở tầng đích. Khi một tầng thấp hơn (ví dụ `global`) lưu override `agy` kèm `--profile` và một tầng cao hơn (ví dụ `project` hoặc CLI) gán model không phải `agy` (`set programmer codex-gpt xhigh --scope project`), `profile` kế thừa từ tầng thấp được bỏ qua tự động và xóa khỏi binding đã phân giải lẫn `sources`. Tuy nhiên, đặt `profile` trong **cùng** một tầng với model không phải `agy`, hoặc truyền `--profile` chung với model không phải `agy` trong một lệnh, vẫn báo lỗi và thoát mã `1`.

## 4. Dùng Nhiều Profile agy

Khai báo danh sách profile ưu tiên rõ ràng trong `$REAL_HOME/.d3nexus/agy_profiles.json` để các phiên điều phối chạy song song chia sẻ tài khoản Antigravity an toàn qua `$REAL_HOME/.d3nexus/agy_profile_leases.json`:

```bash
/d3nexus:dev-config profiles discover
/d3nexus:dev-config profiles discover --json
/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1
/d3nexus:dev-config profiles add profile_b --priority 2 --max-concurrent 1
/d3nexus:dev-config profiles probe profile_a
/d3nexus:dev-config set programmer --provider agy --profile profile_a --model hydrogen --effort xhigh
/d3nexus:dev-config set programmer --provider agy --model hydrogen --effort xhigh --profile auto
/d3nexus:dev-config profiles list
/d3nexus:dev-config profiles list --json
/d3nexus:dev-config profiles release profile_a --force
/d3nexus:dev-config profiles remove profile_b
/d3nexus:dev-config profiles clear profile_a
/d3nexus:dev-config profiles clear
```

- **Chỉ thêm các profile do bạn sở hữu**: `profiles discover` đọc các thư mục Antigravity không phải symlink chưa nằm trong pool mà không fetch quota hay mở khóa keychain, đồng thời in gợi ý các bước tiếp theo (`profiles probe <name>` rồi `profiles add <name>`). Hãy thêm **duy nhất các profile của chính bạn** (`profile_a`, `profile_b`) và probe chúng sau khi thêm. Lệnh `profiles probe` chỉ hoạt động với các profile đã nằm trong pool, nên gợi ý `profiles probe <name>` do `profiles discover` in ra chỉ áp dụng sau khi bạn chạy `profiles add`.
- **Thử ưu tiên rồi xoay vòng**: Đặt `--profile profile_a` cho vai trò `agy` giúp `dispatch` thử `profile_a` trước, sau đó xoay sang các profile còn lại trong pool theo thứ tự `--priority` nếu `profile_a` đang bị giữ lease, bận hoặc cạn quota.
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
- **`quota-check`**: Đánh giá pool quota mà từng vai trò tiêu thụ (`argonWeekly`, `gemini5h` + `geminiWeekly`, hoặc quota của provider `claude`/`codex`/`kiro`) so với `quota_thresholds`. Thoát `0` nếu đủ hoặc không đọc được (`quota_unknown`, không chặn); thoát `2` nếu thiếu quota.
- **Báo cáo dừng & không tự ý đổi model**: Khi toàn bộ pool `agy` cạn quota (`no_profile`, thoát `2`) hoặc `quota-check` thất bại, Orchestrator/runner ghi `--checkpoint quota_low`, ghi pending decision loại `quota` hiển thị trên `/d3nexus:check-tasks`, liệt kê từng profile cùng cửa sổ bị trượt, mốc reset sớm nhất, và các lệnh khôi phục cụ thể (`/d3nexus:dev-config profiles clear`, `/d3nexus:dev-config set programmer codex-gpt xhigh`, `/d3nexus:dev-config set programmer kiro-sonnet high`). **Kit không bao giờ tự động chuyển sang model khác** — Role 1.0 quyết định chờ, nạp thêm, clear hay chuyển model.

## 6. Xử lý Sự cố

| Triệu chứng | Nguyên nhân | Lệnh xử lý |
| :--- | :--- | :--- |
| Chạy `set programmer codex-gpt xhigh --scope project` sau khi đặt `--profile` ở global | Model không phải `agy` ở tầng cao hơn kế thừa `profile` từ tầng thấp hơn: `profile` ở tầng thấp được bỏ qua tự động (SE-15); chỉ báo lỗi khi `--profile` nằm **cùng** tầng hoặc cùng lệnh với model không phải `agy` | `/d3nexus:dev-config set programmer codex-gpt xhigh --scope project` *(chạy trực tiếp được; hoặc xóa override global bằng `/d3nexus:dev-config reset programmer --scope global`)* |
| `Error: --profile applies only to agy models` | Truyền `--profile` trong cùng lệnh hoặc cùng tầng với model `claude`, `codex` hoặc `kiro` | `/d3nexus:dev-config set programmer kiro-sonnet high` |
| `warning: programmer is still bound to ... by the project layer` sau `--provider` hoặc `preset` | Override ở tầng cao hơn hoặc `active_preset` của project đang che phủ thay đổi ở global | `/d3nexus:dev-config reset programmer --scope project` |
| `Error: Profile 'profile_a' is not in the agy pool` (hoặc `is not in the pool`) | `--profile` hoặc `profiles probe`/`remove`/`release`/`clear` phải trỏ tới một profile đã đăng ký trong `$REAL_HOME/.d3nexus/agy_profiles.json` | `/d3nexus:dev-config profiles add profile_a --priority 1 --max-concurrent 1` |
| `profiles remove` bị từ chối vì còn live lease | Đang có orchestrator hoạt động hoặc lease chưa hết hạn trong `agy_profile_leases.json` | `/d3nexus:dev-config profiles release profile_a --force` |
| `Stopped: all agy profiles are out of quota.` (`no_profile`, thoát `2`) | Mọi profile trong pool đều không đạt ngưỡng 5 giờ hoặc theo tuần | Chờ/nạp quota rồi chạy `/d3nexus:dev-config profiles clear`, hoặc chuyển sang `/d3nexus:dev-config set programmer kiro-sonnet high` |
| Dừng `MODEL_UNAVAILABLE` hoặc thấy `(!)` cạnh CLI trong `status` | Thiếu binary CLI trên `PATH` hoặc chưa đăng nhập xác thực | Cài/đăng nhập lại CLI hoặc đổi qua `/d3nexus:dev-config set programmer claude-sonnet high` |
| `Cannot remove model alias ... referenced by ...` | Preset, override hoặc fallback hiện hành vẫn đang tham chiếu tới bí danh đó | `/d3nexus:dev-config reset --scope global` rồi xóa bí danh |
| Cảnh báo `quota_unknown` khi chạy `quota-check` (thoát `0`) | Fetcher không trả dữ liệu hoặc CLI chưa hỗ trợ đọc quota trực tiếp | Cảnh báo không chặn; kiểm tra trực tiếp bằng `/d3nexus:check-quota` |

## 7. Tham chiếu Lệnh và Mã Thoát

Mọi lệnh con đều có thể gọi trực tiếp qua `python3 scripts/dev_config.py ...` (riêng `dispatch` yêu cầu `--prompt-file` và thư mục `--cwd` đã tồn tại):

```bash
python3 scripts/dev_config.py status
python3 scripts/dev_config.py models
python3 scripts/dev_config.py resolve programmer --format json --mode write
python3 scripts/dev_config.py resolve ai_architect_reviewer --format argv --mode read-only
python3 scripts/dev_config.py dispatch --persona programmer --mode write --prompt-file .devtool/prompt.md --cwd . --log .devtool/dispatch.log --epic demo --task task_01 --slot 1 --role orchestrator --wait 30
```

| Mã thoát | Ý nghĩa |
| :--- | :--- |
| `0` | Thành công; hoặc `quota-check` đủ quota / `quota_unknown` |
| `1` | Lỗi dữ liệu cấu hình, lỗi tham số CLI, `task_failure`, `model_unavailable` hoặc `preflight_failed` |
| `2` | Cổng quota không đủ (`quota-check`), `no_profile` (toàn bộ pool cạn/bận) hoặc `quota_midrun` |
