# Thiết kế tổng thể Runner Vòng đời Tự động (Autonomous Lifecycle Runner)

## Mục lục

- [Siêu dữ liệu](#siêu-dữ-liệu)
- [Bối cảnh](#bối-cảnh)
- [Mục tiêu và Phi mục tiêu](#mục-tiêu-và-phi-mục-tiêu)
- [Kiến trúc và Thiết kế Kỹ thuật](#kiến-trúc-và-thiết-kế-kỹ-thuật)
- [Cảnh báo Shared Contract](#cảnh-báo-shared-contract)
- [Kế hoạch Kiểm thử Tích hợp và Ma trận Biên](#kế-hoạch-kiểm-thử-tích-hợp-và-ma-trận-biên)
- [Môi trường Kiểm thử](#môi-trường-kiểm-thử)
- [Độ bao phủ Kịch bản BDD Toàn diện](#độ-bao-phủ-kịch-bản-bdd-toàn-diện)
- [Chiến lược Phát hành và Giảm thiểu Rủi ro](#chiến-lược-phát-hành-và-giảm-thiểu-rủi-ro)
- [Phân rã Công việc Kanban](#phân-rã-công-việc-kanban)
- [Đính chính Đặc tả](#đính-chính-đặc-tả)

## Siêu dữ liệu

- **Tên Epic**: `autonomous_lifecycle_runner`
- **Trạng thái**: Đã đóng gói (2026-11-10)
- **Bản phát hành mục tiêu**: Bản phát hành plugin tiếp theo
- **Nền tảng**: Bộ công cụ Python / agent skill kit
- **Phụ thuộc vào epic**: không
- **Đặc tả nguồn**: [Thiết kế runner vòng đời tự động đã duyệt](2026-11-10-autonomous-lifecycle-runner-design.vi.md)

## Bối cảnh

Vòng đời phát triển phần mềm trong `dev-lifecycle` hiện tại yêu cầu can thiệp thủ công có tính tương tác tại nhiều cổng quyết định:
1. Menu bàn giao Giai đoạn 2 (prompt Handoff Choice hỏi chạy Principal Review hay tiếp tục trực tiếp).
2. Menu vào Giai đoạn 3 (xác nhận thứ tự thực thi Gate 3).
3. Menu sau triển khai Giai đoạn 3 (prompt Review Choice để Hoàn thành, Cross-model review, hoặc Local model review).
4. Phân loại (triage) phát hiện review (dừng lại xác nhận các hành động đề xuất ngay cả khi các phát hiện là thứ yếu hoặc không nghiêm trọng).

Để hỗ trợ phát triển epic tự động hóa đầu-cuối hoàn toàn trong khi vẫn giữ vững kỷ luật quản trị kiến trúc nghiêm ngặt, một bộ điều phối máy trạng thái hợp nhất (`lifecycle_runner.py`) được giới thiệu. Runner này điều phối ba tác nhân riêng biệt:
- **Human Architect (Vai trò 2.1)**: Định hướng brainstorming ban đầu, phê duyệt Gate 1 & Gate 2, rà soát các đề xuất sửa chữa của Principal Review, và đưa ra quyết định hoàn thành Gate 5 cuối cùng.
- **AI Assistant (Vai trò 2.2)**: Phân loại phát hiện review, xây dựng danh sách đề xuất sửa chữa trong Principal Review, và đánh giá/phê duyệt kế hoạch sửa lỗi của AI Programmer trong Cross-Model Review.
- **AI Programmer (Vai trò 2.3)**: Lập trình viên chạy headless được điều phối qua `agy --model gemini-3.8-flash --effort high --mode auto`, triển khai các task code trong worktree biệt lập, chạy quality check, và soạn thảo kế hoạch sửa lỗi.

Tiến trình tự động hóa loại bỏ các bước dừng menu không cần thiết nhưng bảo toàn tuyệt đối việc dừng khẩn cấp (circuit breaker) trước các xung đột kiến trúc (`SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`).

## Mục tiêu và Phi mục tiêu

### Mục tiêu

- Cung cấp CLI điều phối máy trạng thái chạy headless, có khả năng phục hồi sau sự cố tại `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`, dẫn dắt epic qua review Giai đoạn 2, triển khai Giai đoạn 3, và cross-model review Giai đoạn 3.
- Điều phối AI Programmer sử dụng lệnh headless `agy --model gemini-3.8-flash --effort high --mode auto` trong worktree git biệt lập với giám sát nhóm tiến trình và giới hạn timeout.
- Tự động hóa việc tính toán thứ tự thực thi task ở Gate 3 thông qua `compute_execution_order.py`.
- Thực thi trạm dừng kiểm tra của con người (Human checkpoint) trong Principal Review: AI Assistant xác minh các phát hiện, gom cụm các sửa chữa đề xuất, và dừng lại chờ con người xác nhận trước khi áp dụng thay đổi.
- Hiện thực hóa vòng lặp sửa lỗi và kiểm chứng tự động cho Cross-Model Review: AI Programmer lập kế hoạch sửa lỗi, AI Assistant đánh giá và phê duyệt/điều chỉnh kế hoạch, AI Programmer áp dụng sửa đổi, và Gate 4 tự động kiểm chứng lại mà không cần dừng hỏi con người.
- Duy trì trạng thái bền vững trong `.devtool/state/<epic>.pipeline.json` đồng bộ với `.devtool/GATE_LEDGER.md` để khôi phục tức thì khi bị ngắt quãng.
- Đảm bảo chế độ tương tác (interactive mode) tương thích ngược 100% (`/dev-lifecycle --autonomous` hoặc gọi runner trực tiếp hoàn toàn là lựa chọn tùy chọn).

### Phi mục tiêu

- Chỉnh sửa luồng vòng đời tương tác hoặc thay đổi cách nhà phát triển tương tác với các prompt thủ công khi không có cờ `--autonomous`.
- Bỏ qua phê duyệt của con người tại Gate 1 (duyệt spec), Gate 2 (xác nhận phân rã task), hoặc Gate 5 (quyết định hoàn thành & merge cuối cùng).
- Tự động push code lên kho từ xa hoặc tự động merge nhánh tính năng vào nhánh gốc mà không có chỉ định rõ ràng từ nhà phát triển.
- Tăng giới hạn hội tụ review quá 3 vòng hoặc nới lỏng ba Circuit Breakers bắt buộc.

## Kiến trúc và Thiết kế Kỹ thuật

### Kiến trúc Mức cao

```mermaid
flowchart TD
    subgraph CLI["CLI & Điểm vào Runner"]
        RUNNER["lifecycle_runner.py<br/>(Máy trạng thái có thể phục hồi)"]
        PROBE["Thăm dò model khởi động<br/>(agy probe gemini-3.8-flash & assistant)"]
        CONF[".devtool/review_config.json"]
    end

    subgraph STATE["Lưu trữ Trạng thái & Khôi phục"]
        PIPE_STATE[".devtool/state/<epic>.pipeline.json"]
        GATE_LEDGER[".devtool/GATE_LEDGER.md"]
        PROJ_LEDGER[".devtool/PROJECT_LEDGER.md"]
    end

    subgraph STAGE2["Giai đoạn 2: Tự động hóa Principal Review"]
        PR_RUN["run_external_review.py run --stage principal"]
        PR_TRIAGE["Assistant tự động phân loại & đề xuất sửa lỗi"]
        PR_HUMAN{"Điểm dừng Con người:<br/>Xác nhận sửa lỗi?"}
        PR_REVISE["Assistant chỉnh sửa & đóng gói lại Epic"]
    end

    subgraph STAGE3["Giai đoạn 3: Triển khai Headless"]
        ORDER["compute_execution_order.py<br/>(Tự động xác nhận thứ tự Gate 3)"]
        DISPATCH["Bộ điều phối Headless<br/>(agy --model gemini-3.8-flash --effort high)"]
        GATE4["Cổng chất lượng nội bộ Giai đoạn 4 / Gate 4"]
    end

    subgraph CMR["Giai đoạn 3: Vòng lặp Cross-Model Review"]
        CMR_RUN["run_external_review.py run (auto-quota)"]
        PROG_PLAN["Programmer soạn Kế hoạch Sửa lỗi<br/>(fix_plan_roundN.md)"]
        ASST_EVAL{"Assistant đánh giá:<br/>APPROVED / ADJUSTED / CONFLICT"}
        PROG_FIX["Programmer áp dụng Sửa lỗi & Gate 4"]
    end

    subgraph CB["Circuit Breakers (Dừng Ngay lập tức & Báo cáo)"]
        HALT_SCC["HALT: SHARED_CONTRACT_CONFLICT"]
        HALT_FL["HALT: FIX_LOOP"]
        HALT_MR["HALT: MAX_ROUNDS_CRITICAL_REMAINING"]
        HALT_CC["HALT: Assistant CRITICAL_CONFLICT"]
    end

    subgraph FINAL["Giai đoạn 4: Developer Review & Hoàn thành"]
        REPORT["Hiển thị Báo cáo Điều hành Cuối cùng"]
        HUMAN_FINISH{"Con người quyết định:<br/>/finishing-a-development-branch"}
        FINISH_BRANCH["Tích hợp Nhánh & Kiểm thử Toàn bộ"]
    end

    CONF --> PROBE --> RUNNER
    RUNNER <--> PIPE_STATE
    RUNNER <--> GATE_LEDGER

    RUNNER --> PR_RUN
    PR_RUN --> PR_TRIAGE
    PR_TRIAGE -->|Có phát hiện cần sửa| PR_HUMAN
    PR_TRIAGE -->|0 phát hiện| ORDER
    PR_HUMAN -->|Đã xác nhận| PR_REVISE --> PR_RUN

    ORDER --> DISPATCH --> GATE4
    GATE4 -->|PASS| CMR_RUN
    CMR_RUN -->|Tồn tại phát hiện| PROG_PLAN
    PROG_PLAN --> ASST_EVAL
    ASST_EVAL -->|APPROVED / ADJUSTED| PROG_FIX --> GATE4
    CMR_RUN -->|Hội tụ (0 Blocker)| REPORT

    REPORT --> HUMAN_FINISH
    HUMAN_FINISH -->|Hoàn thành| FINISH_BRANCH

    PR_TRIAGE -.->|Lệch Contract| HALT_SCC
    CMR_RUN -.->|Lệch Contract| HALT_SCC
    CMR_RUN -.->|Lặp lại lỗi ở file cũ| HALT_FL
    CMR_RUN -.->|Vòng >= 3 còn Critical| HALT_MR
    ASST_EVAL -.->|Vi phạm Thiết kế| HALT_CC
```

### Biểu đồ Tuần tự

```mermaid
sequenceDiagram
    autonumber
    actor Human as Human Architect (Vai trò 2.1)
    participant Runner as lifecycle_runner.py
    participant Reviewer as External Reviewer (Claude/Codex/Kiro)
    participant Assistant as AI Assistant (Vai trò 2.2)
    participant Programmer as AI Programmer (Vai trò 2.3 Gemini 3.8)

    Note over Human,Assistant: Gate 1 & Gate 2 Đã phê duyệt
    Human->>Runner: /dev-lifecycle --autonomous
    Runner->>Runner: probe_models() [kiểm tra agy & các model]
    Runner->>Runner: record_state(stage="principal_review")

    rect rgb(240, 248, 255)
    Note over Runner,Assistant: Giai đoạn 2: Tự động hóa Principal Review
    loop Principal Review (Tối đa 3 vòng)
        Runner->>Reviewer: run_external_review.py run --stage principal
        Reviewer-->>Runner: Ghi nhận phát hiện review
        Runner->>Assistant: Phân loại phát hiện theo HLD & mã nguồn
        Assistant-->>Runner: Danh sách đề xuất sửa lỗi
        alt Phát hiện cần sửa chữa
            Runner->>Human: Trình bày đề xuất & chờ xác nhận
            Human-->>Runner: Xác nhận đề xuất sửa lỗi
            Runner->>Assistant: Áp dụng sửa chữa & package_epic.py --revise
        else 0 phát hiện
            Runner->>Runner: Chuyển sang Giai đoạn Triển khai
        end
    end
    end

    rect rgb(245, 255, 250)
    Note over Runner,Programmer: Giai đoạn 3: Triển khai Tự động Headless
    Runner->>Runner: compute_execution_order.py -> Ghi nhận Gate 3
    loop Cho từng task theo thứ tự thực thi
        Runner->>Programmer: agy --model gemini-3.8-flash --effort high --mode auto (Task N)
        Programmer-->>Runner: Chỉnh sửa mã, unit test, bằng chứng task
    end
    Runner->>Runner: Thực thi đầy đủ Gate 4 (kiểm tra nội bộ tất định)
    end

    rect rgb(255, 250, 240)
    Note over Runner,Assistant: Giai đoạn 3: Vòng lặp Cross-Model Review
    loop Cross-Model Review (Tối đa 3 vòng)
        Runner->>Reviewer: run_external_review.py run (auto-quota)
        Reviewer-->>Runner: Ghi nhận phát hiện
        alt Đã hội tụ (0 Blocker)
            Runner->>Runner: Thoát vòng lặp -> Chuyển sang Báo cáo Cuối cùng
        else Còn tồn tại Blocker
            Runner->>Programmer: Soạn kế hoạch sửa lỗi (fix_plan_roundN.md)
            Programmer-->>Runner: Đã viết fix_plan_roundN.md
            Runner->>Assistant: Đánh giá kế hoạch sửa lỗi theo HLD đã duyệt
            Assistant-->>Runner: Phán quyết (APPROVED / ADJUSTED / CRITICAL_CONFLICT)
            alt CRITICAL_CONFLICT
                Runner->>Human: HALT: Báo cáo xung đột thiết kế
            else APPROVED hoặc ADJUSTED
                Runner->>Programmer: Áp dụng kế hoạch sửa lỗi đã duyệt
                Programmer-->>Runner: Commit sửa chữa
                Runner->>Runner: Chạy lại đầy đủ Gate 4
            end
        end
    end
    end

    Runner->>Human: Xuất Báo cáo Điều hành Cuối cùng
    Human->>Runner: Kích hoạt /finishing-a-development-branch
```

### Bản đồ Duy trì Tính năng ("Chỉ mục Hướng dẫn Bảo trì")

| Khả năng | Đường dẫn Nguồn Chuẩn & Điểm vào | Bất biến Cốt lõi & Tùy chọn Trạng thái/Cấu hình | Hướng dẫn Mở rộng & Xử lý Sự cố |
|---|---|---|---|
| **State Machine Runner** | `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` | Tệp trạng thái `.devtool/state/<epic>.pipeline.json` phải được cập nhật nguyên tử thông qua đổi tên `.tmp`. Schema trạng thái tuân thủ dataclass `PipelineState`. | Kiểm tra file trạng thái để xem stage, vòng review và SHA gần nhất. Dùng `--resume` hoặc `--reset-stage <stage>` để khôi phục. |
| **Model Prober & Dispatcher** | `lifecycle_runner.py::ModelDispatcher` | Tiến trình headless phải dùng `agy --print "<prompt>" --model <model> --effort <effort> --mode <mode>`. Giới hạn timeout qua `subprocess.run(timeout=...)` và cô lập process group (`start_new_session=True`). | Nếu model bị đổi tên hoặc không hỗ trợ, kiểm tra `.devtool/review_config.json` hoặc cấu hình mặc định. Thăm dò ban đầu dừng ngay trước khi sửa đổi file. |
| **Điểm dừng Principal Review** | `lifecycle_runner.py::stage_principal_review` | Tạm dừng để trình bày bảng đề xuất sửa lỗi và chờ người dùng nhập khi số lượng phát hiện > 0. Tự động đi tiếp khi có 0 phát hiện. Phát hiện minor được gom chung vào đợt xác nhận. | Kiểm tra `review_results.md` và kết quả triage. Xác nhận cho phép Assistant chạy `package_epic.py --revise`. |
| **Tự động hóa Gate 3** | `lifecycle_runner.py::resolve_gate3_order` | Thứ tự thực thi phải tuân thủ nghiêm ngặt sắp xếp topo từ `compute_execution_order.py`. Bản ghi Gate 3 được lưu vào `.devtool/GATE_LEDGER.md`. | Nếu có chu trình phụ thuộc, `compute_execution_order.py` sẽ báo lỗi rõ ràng; runner tạm dừng để người dùng xử lý. |
| **Vòng lặp Cross-Model Fix** | `lifecycle_runner.py::stage_cross_model_review` | Programmer soạn thảo `.devtool/epic/<epic>/fix_plan_round<N>.md`. Assistant phản hồi bằng `APPROVED`, `ADJUSTED`, hoặc `CRITICAL_CONFLICT`. Gate 4 chạy lại sau mỗi vòng sửa lỗi. Các vòng trung gian không dừng hỏi con người. | Xem `fix_plan_round<N>.md` để kiểm tra các sửa chữa được đề xuất. Phán quyết của Assistant được lưu vào `.devtool/state/<epic>.pipeline.json`. |
| **Báo cáo Điều hành Đa vòng & Dừng Cuối** | `lifecycle_runner.py::render_final_executive_report` | Chỉ kết xuất ở vòng cuối cùng khi review đã hội tụ và Gate 4 PASS. Tổng hợp Top 3 Phát hiện Rủi ro Cao nhất của cả quá trình review qua nhiều vòng. Dừng chờ xác nhận Merge hoặc hành động khác. | Gom toàn bộ các vòng từ `review_results.md`. Hiển thị phát hiện, commit sửa lỗi, và SHA đạt chuẩn Gate 4 trước khi gợi ý prompt `/finishing-a-development-branch`. |
| **Circuit Breakers** | `lifecycle_runner.py::evaluate_circuit_breakers` | Dừng ngay lập tức không thử lại khi gặp: `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, `MAX_ROUNDS_CRITICAL_REMAINING`, hoặc Assistant `CRITICAL_CONFLICT`. | Đọc banner cảnh báo trên console để biết nguyên nhân và hướng dẫn khắc phục. Khôi phục yêu cầu giải quyết xung đột rồi chạy `--resume`. |

### Hợp đồng Mô-đun

Các chữ ký và cấu trúc này được đóng băng cho việc triển khai tại `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py`:

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

class StageName(str, Enum):
    INITIALIZED = "initialized"
    PRINCIPAL_REVIEW = "principal_review"
    IMPLEMENTATION = "implementation"
    CROSS_MODEL_REVIEW = "cross_model_review"
    AWAITING_FINISH = "awaiting_finish"
    COMPLETED = "completed"
    HALTED = "halted"

class FixPlanVerdict(str, Enum):
    APPROVED = "APPROVED"
    ADJUSTED = "ADJUSTED"
    CRITICAL_CONFLICT = "CRITICAL_CONFLICT"

@dataclass
class RunnerConfig:
    programmer_model: str = "gemini-3.8-flash"
    programmer_effort: str = "high"
    assistant_model: str = "claude-3-7-sonnet"
    assistant_effort: str = "high"
    timeout_seconds: int = 1800
    max_review_rounds: int = 3

@dataclass
class PipelineState:
    epic_slug: str
    active_stage: StageName
    principal_round: int = 0
    cross_model_round: int = 0
    last_commit_sha: str = ""
    last_verdict: str = ""
    halt_reason: Optional[str] = None
    task_order: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineState": ...

class ModelDispatcher:
    def __init__(self, config: RunnerConfig): ...
    def probe_model(self, model: str) -> bool: ...
    def dispatch(
        self,
        prompt: str,
        model: str,
        effort: str,
        mode: str,
        worktree_root: Path,
        timeout: Optional[int] = None,
    ) -> Tuple[int, str, str]: ...

class LifecycleRunner:
    def __init__(self, root: Path, epic_slug: str, config: Optional[RunnerConfig] = None): ...
    def load_or_init_state(self) -> PipelineState: ...
    def save_state(self) -> None: ...
    def run(self, resume: bool = False) -> int: ...
    def step_principal_review(self) -> bool: ...
    def step_implementation(self) -> bool: ...
    def step_cross_model_review(self) -> bool: ...
    def evaluate_circuit_breakers(self, stage: str, round_num: int) -> Optional[str]: ...
    def prompt_human_principal_fixes(self, triage_summary: str) -> bool: ...
    def evaluate_programmer_fix_plan(self, round_num: int) -> Tuple[FixPlanVerdict, str]: ...
    def render_final_executive_report(self) -> str: ...
```

### Phân tích Tác động

Phân tích tác động được thực thi qua `check_code_impact.py` so với nhánh `main`:
- Phân tích Xung đột Git Ngược dòng: 🟢 **SẠCH** (Không có commit chưa merge với `main`).
- Vùng ảnh hưởng và Đối tượng gọi: `lifecycle_runner.py` là một điểm vào độc lập mới. Nơi tiêu thụ sẽ là slash command `dev-lifecycle` và các lệnh CLI.
- Không chạm tới bất kỳ hợp đồng bridge đa nền tảng hoặc native nào.

## Cảnh báo Shared Contract

Không có — tính năng hoàn toàn tự chứa (self-contained feature).

## Kế hoạch Kiểm thử Tích hợp và Ma trận Biên

Integration test roots: tests/, skills/dev-lifecycle/resources/scripts/

Protected paths: .agents/quality/**, .devtool/epic/autonomous_lifecycle_runner/bdd_scenarios.en.md, .devtool/epic/autonomous_lifecycle_runner/bdd_scenarios.vi.md, tests/test_lifecycle_runner.py

Integration results: python3 scripts/run_unittest_junit.py --junitxml build/test-results/autonomous-lifecycle-runner.xml tests/test_lifecycle_runner.py -> build/test-results/autonomous-lifecycle-runner.xml

| Ranh giới | Thành phần thực tế | Cách cô lập hoặc fixture | Khẳng định bắt buộc |
|---|---|---|---|
| **Thăm dò Model** | `ModelDispatcher.probe_model` | Script `agy` giả lập trên `PATH` mô phỏng các mã thoát thành công và thất bại | Trả về mã 0 với model hợp lệ; trả về lỗi rõ ràng và dừng pipeline khi model bị từ chối. |
| **Giám sát Nhóm Tiến trình** | `ModelDispatcher.dispatch` | Script chạy giả lập thời gian dài | Tiến trình chạy trong process group riêng biệt (`start_new_session=True`); tín hiệu SIGTERM được gửi sạch sẽ khi quá thời gian timeout. |
| **Lưu trữ và Khôi phục Trạng thái** | `LifecycleRunner.save_state`, `load_or_init_state` | Hệ thống tệp tạm thời với thư mục `.devtool/state` giả lập | Đổi tên nguyên tử `.tmp` chống hỏng file; runner khôi phục chính xác từ giai đoạn đã lưu. |
| **Tự động hóa Thứ tự Gate 3** | `LifecycleRunner.step_implementation` | `compute_execution_order.py` giả lập | Thứ tự được bóc tách từ kết quả JSON/text và ghi nhận vào `.devtool/GATE_LEDGER.md`. |
| **Điểm dừng Con người Principal Review** | `step_principal_review` | Lớp bọc prompt stdin/stdout giả lập | Dừng và hỏi người dùng khi số phát hiện > 0; tự động đi tiếp khi số phát hiện == 0. |
| **Đánh giá Kế hoạch Sửa lỗi Cross-Model** | `evaluate_programmer_fix_plan` | Dispatcher Assistant giả lập trả về `APPROVED`, `ADJUSTED`, `CRITICAL_CONFLICT` | Xử lý chính xác cả 3 phán quyết; kích hoạt Programmer sửa lỗi hoặc dừng pipeline. |
| **Circuit Breakers** | `evaluate_circuit_breakers` | Fixture `review_results.md` tổng hợp | Dừng ngay lập tức khi phát hiện `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, và `MAX_ROUNDS_CRITICAL_REMAINING`. |
| **Báo cáo Điều hành Cuối cùng** | `LifecycleRunner.run` | Trạng thái pipeline đã hoàn thành | Kết xuất báo cáo markdown điều hành và dừng lại kèm hướng dẫn `/finishing-a-development-branch`. |

## Môi trường Kiểm thử

- Mọi bài kiểm thử đơn vị và tích hợp chạy trong các thư mục tạm biệt lập (`tempfile.TemporaryDirectory`).
- Kiểm thử giả lập CLI `agy` bằng các script giả lập thực thi được hoặc `unittest.mock.patch`, không yêu cầu API key bên ngoài hay mạng internet.
- Timeout tiến trình và việc ngắt tín hiệu được kiểm thử với khoảng thời gian ngắn (< 2.0s).
- Báo cáo JUnit XML được ghi vào `build/test-results/autonomous-lifecycle-runner.xml`.

## Độ bao phủ Kịch bản BDD Toàn diện

Các định nghĩa Gherkin chuẩn nằm tại [Kịch bản BDD](bdd_scenarios.en.md), cùng bản dịch đồng bộ [Tiếng Việt](bdd_scenarios.vi.md).

| Chiều kiểm thử | Mã kịch bản | Mục đích bao phủ |
|---|---|---|
| **Luồng thành công** | `ALR-HP-01` đến `ALR-HP-04` | Chạy toàn bộ pipeline tự động, điều phối Programmer Gemini 3.8 không giao diện, con người xác nhận Principal Review, Assistant duyệt kế hoạch sửa lỗi. |
| **Trường hợp biên và dữ liệu bất thường** | `ALR-EC-01` đến `ALR-EC-04` | 0 phát hiện trong Principal Review bỏ qua prompt, gom cụm phát hiện minor, Assistant điều chỉnh kế hoạch, tự động xác nhận Gate 3. |
| **Chuyển đổi trạng thái và bất biến** | `ALR-ST-01` đến `ALR-ST-03` | Lưu trạng thái qua sự cố, đồng bộ Gate Ledger, thăm dò tính năng model trước khi chạy. |
| **Bất đồng bộ và điều kiện tranh chấp** | `ALR-AR-01` đến `ALR-AR-02` | Cách ly process group và ngắt SIGTERM theo timeout, khóa file trạng thái chống tranh chấp. |
| **Lỗi và khả năng phục hồi** | `ALR-FR-01` đến `ALR-FR-04` | Dừng khi xung đột shared contract, dừng khi lặp lỗi fix loop, dừng khi hết vòng review còn critical, dừng khi Assistant báo CRITICAL_CONFLICT. |

## Chiến lược Phát hành và Giảm thiểu Rủi ro

1. Hiện thực hóa máy trạng thái cốt lõi, models và lưu trữ trạng thái tại `skills/dev-lifecycle/resources/scripts/lifecycle_runner.py` kèm unit tests toàn diện.
2. Hiện thực hóa dispatcher `agy` headless với ranh giới process group và thăm dò model.
3. Tích hợp tự động hóa Giai đoạn 2 Principal Review với điểm dừng con người xác nhận sửa lỗi.
4. Tích hợp vòng lặp đánh giá kế hoạch sửa lỗi Cross-Model Review ở Giai đoạn 3.
5. Cập nhật `rules/CRITICAL_RULES.md`, `skills/dev-lifecycle/SKILL.md`, `skills/dev-implementation/SKILL.md`, và tài liệu hướng dẫn hành vi chế độ tự động.
6. Xác minh toàn bộ bộ test bằng `scripts/run_unittest_junit.py` và `scripts/verify.sh`.

Giảm thiểu rủi ro: Chế độ tự động hoàn toàn là tùy chọn qua cờ `/dev-lifecycle --autonomous` hoặc gọi trực tiếp `lifecycle_runner.py`. Hành vi tương tác mặc định của vòng đời phát triển vẫn được bảo toàn trọn vẹn.

## Phân rã Công việc Kanban

1. [Task 1: Máy Trạng thái Pipeline, Lưu trữ Trạng thái và Thăm dò Model](task_1_pipeline_state_machine_and_probing.md)
2. [Task 2: Bộ Điều phối Tiến trình con và Headless agy Runner](task_2_subprocess_dispatcher_and_headless_agy.md)
3. [Task 3: Tự động hóa Principal Review và Điểm dừng Con người](task_3_principal_review_automation_and_checkpoint.md)
4. [Task 4: Vòng lặp Kế hoạch Sửa lỗi Cross-Model Review và Bộ Đánh giá Assistant](task_4_cross_model_review_fix_plan_loop.md)
5. [Task 5: Điều phối viên Toàn trình, Tích hợp CLI và Quy tắc Quản trị](task_5_orchestrator_cli_and_governance_rules.md)

## Đính chính Đặc tả

Không có.

