# Implementation Plan cho lựa chọn bàn giao epic

> **Dành cho agent thực thi:** BẮT BUỘC dùng sub-skill d3nexus:subagent-driven-development (khuyến nghị) hoặc d3nexus:executing-plans để thực hiện plan này theo từng task. Các bước dùng cú pháp checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Sau Gate 2, cho developer đóng gói epic để làm sau hoặc giao cho LLM khác, và để `dev-implementation` tự suy ra từ đĩa một epic đang ở đâu rồi tiếp tục đúng điểm.

**Kiến trúc:** Chỉ sửa văn bản skill, cộng một template. `dev-lifecycle` có thêm Handoff Choice, quy trình đóng gói và quy tắc Resuming an Epic; `dev-designer` trả quyền điều khiển về lựa chọn đó; `dev-implementation` có thêm phần xác định tên epic, Entry-Point Detection và Resume Procedure. Các script sẵn có của kit làm mọi bước cơ học.

**Công nghệ:** Các file skill Markdown; các script sẵn có `compute_execution_order.py`, `check_bdd_traceability.py`, `sync_task_status.py` và `check_document.py`; git; bash.

**Spec:** [2026-10-15-epic-handoff-choice-design.vi.md](../specs/2026-10-15-epic-handoff-choice-design.vi.md)

## Mục lục

- [Ràng buộc chung](#ràng-buộc-chung)
- [Cấu trúc file](#cấu-trúc-file)
- [Các task](#các-task)
  - [Task 1: Handoff Choice và đóng gói](#task-1-handoff-choice-và-đóng-gói)
  - [Task 2: Entry-Point Detection và tiếp tục](#task-2-entry-point-detection-và-tiếp-tục)
- [Kiểm tra cuối cùng](#kiểm-tra-cuối-cùng)

## Ràng buộc chung

- Năm gate giữ nguyên. Handoff Choice là một quyết định định tuyến, không phải gate thứ sáu.
- `handoff.md` chỉ viết tiếng Anh, có mục lục đầy đủ, và không bao giờ được cập nhật sau khi đóng gói.
- Đóng gói giữ nguyên trạng thái task và đặt Status của overview thành `Packaged`.
- Không bao giờ push khi chưa có sự cho phép rõ ràng của developer.
- Không thêm script mới; dùng lại các script sẵn có của kit.
- Trạng thái điểm vào lấy từ đĩa: `handoff.md`, Status của overview, trạng thái task, epic branch và worktree.
- Epic được tiếp tục phải xác nhận lại Gate 3 cho các task còn lại, và `git worktree add -b` không bao giờ chạy cho một branch đã tồn tại.
- Frontmatter của `SKILL.md` giữ đúng `name` + `description`.
- Commit: `[SKILLS] <title>` kèm phần thân dạng bullet; không bao giờ có dòng trailer.
- Bước 1 và 8 của Task 1, Bước 1 và 6 của Task 2 dispatch subagent mới để kiểm tra câu chữ của skill. Implementer không dispatch được subagent thì báo lại, và controller sẽ chạy các bước đó. `<ROOT>` trong prompt là kết quả của `git rev-parse --show-toplevel` trong checkout đang thực thi.
- Việc chạy thử diễn ra trong một repo dùng một lần dưới `mktemp -d`, không bao giờ trong repo này.

## Cấu trúc file

| File | Trách nhiệm |
|------|-------------|
| `skills/dev-lifecycle/references/handoff-template.md` | Tạo mới. Template của `handoff.md` |
| `skills/dev-lifecycle/SKILL.md` | Sửa. Handoff Choice, quy trình đóng gói, Resuming an Epic, sơ đồ, Document Contract, red flags |
| `skills/dev-designer/SKILL.md` | Sửa. Step 3 trả về Handoff Choice |
| `skills/dev-implementation/SKILL.md` | Sửa. Xác định epic, Entry-Point Detection, Resume Procedure, đổi trạng thái, sơ đồ, red flags |
| `scripts/test_lifecycle_document_contract.py` | Sửa. Khóa các cụm từ mới |

## Các task

### Task 1: Handoff Choice và đóng gói

**File:**

- Tạo mới: `skills/dev-lifecycle/references/handoff-template.md`
- Sửa: `skills/dev-lifecycle/SKILL.md`
- Sửa: `skills/dev-designer/SKILL.md`
- Sửa: `scripts/test_lifecycle_document_contract.py`

**Giao diện:**

- Dùng: `compute_execution_order.py`, `check_bdd_traceability.py plan`, `sync_task_status.py epic` và `check_document.py --require-toc`, tất cả đã có trên `main`.
- Cung cấp: template `skills/dev-lifecycle/references/handoff-template.md`, các heading `### Resuming an Epic` (anchor `#resuming-an-epic`) và `### Handoff Choice` (anchor `#handoff-choice`), và giá trị Status `Packaged` mà Task 2 phát hiện.

- [ ] **Bước 1: Scenario baseline (RED)**

Trước khi sửa bất cứ thứ gì, dispatch một subagent general-purpose mới với prompt này và giữ lại câu trả lời:

```text
You are in the repository <ROOT>. Read skills/dev-lifecycle/SKILL.md and
skills/dev-designer/SKILL.md. You are orchestrating epic slug todo-export, epic directory
todo_export. dev-designer has just written and committed the HLD, the BDD scenarios and two task
files, and the developer confirmed the task breakdown. Do not run anything. Reply with exactly two
parts:
(1) what you do next, quoting any message you would send the developer;
(2) the developer answers "1" to your question, or, if you asked none, says "Stop here; another
LLM will implement this later". List, in order, every command you would run and every file you
would write, then the last message you would send.
```

Kỳ vọng ở baseline: phần (1) đi thẳng sang Stage 3 hoặc `dev-implementation` mà không hỏi; phần (2) không có `handoff.md` tạo từ template, không có Status `Packaged` và không có preflight. Ghi lại câu trả lời — Bước 8 chạy lại đúng prompt này.

- [ ] **Bước 2: Khóa contract mới (test thất bại)**

Contract test — trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "Granting Gate 4 without a passing traceability check",
    ),
```

bằng:

```python
        "Granting Gate 4 without a passing traceability check",
        "Handoff Choice",
        "handoff-template.md",
        "Resuming an Epic",
        "Packaged",
    ),
```

Contract test — trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "at least one automated integration test",
    ),
```

bằng:

```python
        "at least one automated integration test",
        "Handoff Choice",
    ),
```

Chạy: `python3 scripts/test_lifecycle_document_contract.py`

Kỳ vọng: exit 1 với các dòng sau:

```text
  FAIL skills/dev-designer/SKILL.md: missing Handoff Choice
  FAIL skills/dev-lifecycle/SKILL.md: missing Handoff Choice
  FAIL skills/dev-lifecycle/SKILL.md: missing handoff-template.md
  FAIL skills/dev-lifecycle/SKILL.md: missing Resuming an Epic
  FAIL skills/dev-lifecycle/SKILL.md: missing Packaged
```

- [ ] **Bước 3: Tạo template bàn giao**

Chạy từ thư mục gốc của repo. Heredoc được thụt lề hai dấu cách để bước kiểm tra mục lục của chính plan này không đọc nhầm các heading của template; `sed` bỏ phần thụt lề:

````bash
mkdir -p skills/dev-lifecycle/references
sed 's/^  //' > skills/dev-lifecycle/references/handoff-template.md <<'EOF'
  # Handoff: <epic_slug>

  ## Table of Contents

  - [Status](#status)
  - [Identifiers](#identifiers)
  - [Read First](#read-first)
  - [Resume Prompt](#resume-prompt)
  - [Open Notes](#open-notes)
  - [Rules for the Receiving Agent](#rules-for-the-receiving-agent)

  ## Status

  - **Packaged**: <YYYY-MM-DD>
  - **Design commit**: `<sha>` — `HEAD` before the packaging commit
  - **Base branch**: `<base_branch>`
  - **Gates passed**: 1 (spec), 2 (HLD and task breakdown)
  - **Next**: Stage 3, `dev-implementation`. Gate 3 (execution order) still needs the developer's confirmation.

  ## Identifiers

  | Placeholder | Value |
  |-------------|-------|
  | `<epic_dir>` | `<epic_dir value>` |
  | `<epic_slug>` | `<epic_slug value>` |

  These are usually different strings. Never derive one from the other.

  ## Read First

  1. `.devtool/epic/<epic_dir>/<epic_dir>.en.md` — the HLD. Its Kanban Tasks Breakdown lists the <N> tasks.
  2. `.devtool/epic/<epic_dir>/bdd_scenarios.en.md` — the behavioural contract.
  3. `.devtool/epic/<epic_dir>/<source spec>.en.md` — the approved source spec.

  ## Resume Prompt

  ```text
  Use the d3nexus:dev-implementation skill for the `<epic_slug>` epic.
  Read .devtool/epic/<epic_dir>/handoff.md first.
  Gates 1 and 2 are passed; do not re-run brainstorming or design.
  Gate 3 is pending: present the execution order to me and wait for my confirmation.
  ```

  ## Open Notes

  <What the design session knows that the documents do not say — decisions taken in conversation, risks, doubts. Write `None` when there is nothing.>

  ## Rules for the Receiving Agent

  - Do not re-run `dev-brainstorming` or `dev-designer`. Raise a wrong or missing document at Gate 3.
  - This handoff does not pass Gate 3. The developer confirms the execution order.
  - If `git log <sha>..HEAD -- .devtool/epic/<epic_dir>` lists any commit besides the `Package epic for handoff` commit, the documents changed after packaging. The documents win, and this file may be stale.
  - This file is a dated record. It is never updated after packaging.
EOF
````

Kiểm tra: `head -1 skills/dev-lifecycle/references/handoff-template.md` in ra `# Handoff: <epic_slug>`.

- [ ] **Bước 4: Sửa skills/dev-lifecycle/SKILL.md**

Áp dụng chín chỗ sửa sau. Mỗi chuỗi neo xuất hiện đúng một lần.

A — trong sơ đồ mermaid dưới The Sequence, chèn ngay sau dòng này:

```markdown
    G2{"Gate 2<br/>HLD &amp; task breakdown approved?"}
```

Nội dung mới:

```markdown
    HC{"Handoff choice<br/>package or continue?"}
    PKG(["Package epic<br/>handoff.md, status Packaged, stop"])
```

B — trong cùng sơ đồ đó, thay:

```markdown
    G2 -->|yes| S3
```

bằng:

```markdown
    G2 -->|yes| HC
    HC -->|"1. package"| PKG
    HC -->|"2. continue"| S3
    PKG -.->|"later session or another LLM"| S3
```

C — ở đầu `## Stages`, chèn ngay trước dòng này:

```markdown
### Stage 1 — Inception & Spec → `dev-brainstorming`
```

Nội dung mới, có một dòng trống phía trước:

```markdown
### Resuming an Epic

A request to implement, continue or resume an epic whose `.devtool/epic/<epic_dir>/` already holds
`task_*.md` files is past Gate 2 — whether the epic was packaged (`handoff.md` present, Status
`Packaged`) or interrupted midway through Stage 3. Announce "Gates 1 and 2 already passed; resuming
at Stage 3", invoke `dev-implementation` with that epic name, and let its Entry-Point Detection
choose where to start. Never redo Stage 1 or Stage 2 for it. New requirements for such an epic are
not a resume: they go to dev-designer's Updating an Existing Epic.
```

D — trong Document Contract, thay:

```markdown
`task_*.md` files are the only exception and remain English-only.
```

bằng:

```markdown
`task_*.md` files and an epic's `handoff.md` are the only exceptions and remain English-only;
`handoff.md` still carries a complete table of contents.
```

E — giữa mục Stage 2 và Stage 3, chèn ngay trước dòng này:

```markdown
### Stage 3 — Isolated Execution → `dev-implementation`
```

Nội dung mới, có một dòng trống phía trước:

~~~~markdown
### Handoff Choice

Between Gate 2 and Stage 3 the developer decides when, and by whom, the epic is implemented. This
is a routing decision like Stage 1's, not a sixth gate. Ask it once `dev-designer` Step 3 has
committed the task files — or, with `auto_commit: false`, once they are written:

> Gate 2 passed: the HLD, BDD scenarios and N task files for `<epic_slug>` are written. How do you
> want to proceed?
>
> 1. **Package** — write `handoff.md`, mark the epic `Packaged`, and stop, so the work can be
>    picked up later or by another LLM.
> 2. **Continue** — enter Stage 3 now (`dev-implementation`, starting with Gate 3: execution order).

**Continue** → invoke `dev-implementation`. **Package** → run the packaging procedure below, then
stop: no worktree and no Stage 3 in this session. Resolve the paths from this skill's directory:

```bash
SKILL_DIR=<absolute path of the directory containing this SKILL.md>
SCRIPTS="$SKILL_DIR/../dev-implementation/resources/scripts"
CHECK_DOC="$SKILL_DIR/../doc_quality_check/resources/scripts/check_document.py"
```

1. **Preflight, read-only.** All of it must pass before anything is written:

   ```bash
   python3 "$SCRIPTS"/compute_execution_order.py <epic_slug>
   ls .devtool/epic/<epic_dir>/task_*.md | wc -l
   python3 "$SCRIPTS"/check_bdd_traceability.py plan \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```

   The scan summary's matched count must equal the number of task mirrors, and both scripts must
   exit 0. A smaller count means broken frontmatter or a wrong `epic:` value; exit 1 means a
   dependency cycle or a scenario no `Covers:` line names. Fix it now — the receiving agent has no
   context to diagnose it.
2. Copy this skill's `references/handoff-template.md` to `.devtool/epic/<epic_dir>/handoff.md`
   and fill every placeholder. The first column of its Identifiers table names the placeholders and
   stays as written; drop the source-spec line when the epic has no source spec. Write Open Notes from this
   session's conversation: decisions, risks and doubts the documents do not record.
3. Lint it: `python3 "$CHECK_DOC" --require-toc .devtool/epic/<epic_dir>/handoff.md`.
4. Mark the epic packaged, then confirm both overview variants changed — the script reports the
   documents it found, not the documents it wrote:

   ```bash
   python3 "$SCRIPTS"/sync_task_status.py epic <epic_dir> Packaged
   grep -n -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
     .devtool/epic/<epic_dir>/<epic_dir>.en.md .devtool/epic/<epic_dir>/<epic_dir>.vi.md
   ```

   Two matching lines are required; with fewer, set the Status line by hand in both variants. Task
   statuses stay as they are, so a packaged epic still counts as active under dev-designer's
   Concurrent-Epic Backlog Rule.
5. Commit, when `auto_commit` is `true` or absent: stage `handoff.md`, the overview pair and any task files fixed at step 1, then
   `git commit -m "[<EPIC_NAME>] Package epic for handoff"`, with no trailer. When `auto_commit` is
   `false`, skip it and warn that an agent in another clone will not see the package.
6. Offer to push, and push only on the developer's explicit permission. Say that a receiver in
   another clone or on another machine needs the push.
7. Print the `handoff.md` path and its rendered Resume Prompt, then stop.
~~~~

F — trong mục Stage 3, thay:

```markdown
**Entry:** Gate 2 passed; HLD and `task_*.md` files exist.
```

bằng:

```markdown
**Entry:** Gate 2 passed, HLD and `task_*.md` files exist, and the developer chose Continue at
the Handoff Choice — or a packaged or interrupted epic is being resumed (see
[Resuming an Epic](#resuming-an-epic)).
```

G — trong mục Red Flags, thay:

```markdown
- Creating a worktree or dispatching a subagent before Gate 3.
```

bằng:

```markdown
- Creating a worktree or dispatching a subagent before Gate 3. Recreating the worktree of an epic branch that already exists (dev-implementation's Resume Procedure) is not creating one.
- Invoking `dev-implementation` straight after `dev-designer` without asking the Handoff Choice.
- Packaging an epic without the preflight, or pushing the package without explicit permission.
- Treating a packaged epic's Gate 3 as already passed.
- Redoing the design of an epic whose task files already exist; new requirements go to dev-designer's Updating an Existing Epic.
```

H — ở cuối bảng Rationalizations, chèn ngay sau dòng này:

```markdown
| "I can combine research + spec into one step" | Stage 1 is `dev-brainstorming`'s job. Invoke the skill. |
```

Nội dung mới:

```markdown
| "The developer obviously wants to continue" | The Handoff Choice is theirs. Ask it every time Gate 2 passes. |
```

I — trong bảng The Five Gates, thay:

```markdown
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint | confirmed order + bootstrapped worktree |
```

bằng:

```markdown
| **3** | Execution Order | User | `dev-implementation` Phase 1 checkpoint, or Gate 3 (resume) in its Resume Procedure | confirmed order + bootstrapped worktree |
```

- [ ] **Bước 5: Sửa skills/dev-designer/SKILL.md**

Áp dụng hai chỗ sửa sau.

J — ở cuối Step 3: Finalize & Commit, chèn ngay sau dòng này:

```markdown
- If `auto_commit: false`: skip staging and committing entirely.
```

Nội dung mới, có một dòng trống phía trước:

```markdown
Then stop and return to the [Handoff Choice](../dev-lifecycle/SKILL.md#handoff-choice) in
`dev-lifecycle`: ask the developer whether to package the epic or continue to Stage 3. This skill
never invokes `dev-implementation` itself.
```

K — trong mục Red Flags, chèn ngay sau dòng này:

```markdown
- Committing the epic before `check_bdd_traceability.py plan` exits 0.
```

Nội dung mới:

```markdown
- Invoking `dev-implementation` after Step 3 instead of returning to the Handoff Choice.
```

- [ ] **Bước 6: Chạy contract test và lint**

```bash
python3 scripts/test_lifecycle_document_contract.py
python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md skills/dev-designer/SKILL.md
python3 skills/doc_quality_check/resources/scripts/check_document.py --require-toc skills/dev-lifecycle/references/handoff-template.md
```

Kỳ vọng: `checked 11 lifecycle document contract surfaces`, rồi `checked 2 documents, 0 findings`, rồi `checked 1 documents, 0 findings`.

- [ ] **Bước 7: Chạy thử quy trình đóng gói trên một epic dùng một lần**

Đây là integration test. Nó chạy mọi lệnh mà Handoff Choice quy định trên một epic thật gồm hai task, rồi chạy ba tình huống lỗi mà preflight và bước kiểm tra Status được tạo ra để bắt. Dựng fixture:

````bash
KIT=$(git rev-parse --show-toplevel)
FIXDIR=$(mktemp -d)
cat > "$FIXDIR/make_fixture.sh" <<'EOF'
#!/usr/bin/env bash
# Build a throwaway git repository holding one two-task epic (dir todo_export, slug todo-export),
# for dry-running the epic handoff skill text. Usage: make_fixture.sh <empty-or-new-directory>
set -euo pipefail
FIX="$1"
mkdir -p "$FIX"
cd "$FIX"
git init -q -b main
printf '.worktrees/\n' > .gitignore
EPIC=.devtool/epic/todo_export
mkdir -p "$EPIC" .devtool/features/done
touch .devtool/features/done/.gitkeep
T='```'

printf '%s\n' "# Epic: Todo Export" "" "## Meta Data" "" "- **Status**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.en.md"
printf '%s\n' "# Epic: Xuất danh sách todo" "" "## Meta Data" "" "- **Trạng thái**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.vi.md"

printf '%s\n' "# BDD Scenarios: Todo Export" "" "## Export" "" "${T}gherkin" "Feature: Export" \
  "  Scenario: [TE-HP-01] [Tier C - Integration] Export todos as CSV" "    Given two todos" \
  "  Scenario: [TE-EC-02] Unknown format exits 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.en.md"
printf '%s\n' "# Kịch bản BDD: Xuất todo" "" "## Xuất" "" "${T}gherkin" "Feature: Export" \
  "  Kịch bản: [TE-HP-01] [Tier C - Integration] Xuất todo dạng CSV" "    Given two todos" \
  "  Kịch bản: [TE-EC-02] Định dạng lạ thoát mã 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.vi.md"

task() {  # task <file-stem> <number> <title> <covers> <dependency-line>
  printf '%s\n' "---" "id: \"$1\"" "status: \"todo\"" "priority: \"high\"" "epic: \"todo-export\"" \
    "---" "# Task $2: $3" "" "### BDD SCENARIOS" "" "Covers: $4" "" "## Dependencies & Blockers" "" "$5"
}
task task_1_export_core 1 "Export core" "TE-HP-01" "- None" > "$EPIC/task_1_export_core.md"
task task_2_cli_integration 2 "CLI integration" "TE-EC-02" \
  "- Blocked by [Task 1](task_1_export_core.md)" > "$EPIC/task_2_cli_integration.md"
cp "$EPIC"/task_*.md .devtool/features/

git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: todo_export epic"
echo "fixture ready: $FIX"
EOF
bash "$FIXDIR/make_fixture.sh" "$FIXDIR/repo"
````

Sau đó chạy, trong cùng shell để `KIT` và `FIXDIR` vẫn còn giá trị:

```bash
cd "$FIXDIR/repo"
SCRIPTS="$KIT/skills/dev-implementation/resources/scripts"
CHECK_DOC="$KIT/skills/doc_quality_check/resources/scripts/check_document.py"
python3 "$SCRIPTS"/compute_execution_order.py todo-export > "$FIXDIR/order.txt"; echo "order exit=$?"
head -1 "$FIXDIR/order.txt"
ls .devtool/epic/todo_export/task_*.md | wc -l | tr -d ' '
python3 "$SCRIPTS"/check_bdd_traceability.py plan \
  --scenarios .devtool/epic/todo_export/bdd_scenarios.en.md \
  --tasks .devtool/epic/todo_export/task_*.md; echo "plan exit=$?"
cp "$KIT/skills/dev-lifecycle/references/handoff-template.md" .devtool/epic/todo_export/handoff.md
python3 "$CHECK_DOC" --require-toc .devtool/epic/todo_export/handoff.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged
grep -c -E '^- \*\*(Status|Trạng thái)\*\*: Packaged' \
  .devtool/epic/todo_export/todo_export.en.md .devtool/epic/todo_export/todo_export.vi.md
```

Kỳ vọng:

```text
order exit=0
Scanned 2 task_*.md files; 2 matched epic 'todo-export'; 0 had no parseable frontmatter or a different epic.
2
TE-HP-01    task_1_export_core.md
TE-EC-02    task_2_cli_integration.md
Result: 2/2 covered — PASS
plan exit=0
  checked 1 documents, 0 findings
Synchronized 2 epic docs for 'todo_export' -> 'Packaged'
.devtool/epic/todo_export/todo_export.en.md:1
.devtool/epic/todo_export/todo_export.vi.md:1
```

Giờ là các tình huống lỗi — frontmatter hỏng, một scenario không task nào phủ, và một overview không có dòng Status:

```bash
git checkout -q -- . && rm -f .devtool/epic/todo_export/handoff.md
sed -i.bak 's/epic: "todo-export"/epic: "todo-exprot"/' .devtool/features/task_2_cli_integration.md
python3 "$SCRIPTS"/compute_execution_order.py todo-export | head -1
git checkout -q -- . && rm -f .devtool/features/*.bak
sed -i.bak '/^Covers:/d' .devtool/epic/todo_export/task_2_cli_integration.md
python3 "$SCRIPTS"/check_bdd_traceability.py plan \
  --scenarios .devtool/epic/todo_export/bdd_scenarios.en.md \
  --tasks .devtool/epic/todo_export/task_*.md; echo "plan exit=$?"
git checkout -q -- . && rm -f .devtool/epic/todo_export/*.bak
sed -i.bak '/Status/d;/Trạng thái/d' .devtool/epic/todo_export/todo_export.en.md .devtool/epic/todo_export/todo_export.vi.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged; echo "sync exit=$?"
grep -c -E '^- \*\*Status\*\*: Packaged' .devtool/epic/todo_export/todo_export.en.md
cd "$KIT" && rm -rf "$FIXDIR"
```

Kỳ vọng:

```text
Scanned 2 task_*.md files; 1 matched epic 'todo-export'; 1 had no parseable frontmatter or a different epic.
TE-HP-01    task_1_export_core.md
TE-EC-02    (none)
Result: 1/2 covered — FAIL
plan exit=1
Synchronized 2 epic docs for 'todo_export' -> 'Packaged'
sync exit=0
0
```

Dòng đầu tiên cho `1 matched` so với 2 file task mirror, trong khi exit vẫn là 0: chính phép so sánh số lượng, không phải exit code, mới bắt được frontmatter hỏng. Các dòng cuối cho thấy script trạng thái báo thành công mà không ghi gì, và đó là lý do quy trình bắt buộc có lệnh `grep`.

- [ ] **Bước 8: Chạy lại scenario (GREEN)**

Dispatch một subagent mới khác với prompt của Bước 1, giữ nguyên. Kỳ vọng: (1) hỏi Handoff Choice với hai lựa chọn và chờ; (2) chạy `compute_execution_order.py`, phép đếm task mirror và `check_bdd_traceability.py plan`; ghi `handoff.md` từ `references/handoff-template.md` và lint nó với `--require-toc`; chạy `sync_task_status.py epic todo_export Packaged` và lệnh `grep`; commit với tiêu đề `Package epic for handoff` và không có trailer; hỏi trước khi push; kết thúc bằng việc in đường dẫn và Resume Prompt. Nếu còn phần nào thiếu, siết lại chỗ sửa tương ứng và chạy lại.

- [ ] **Bước 9: Chạy verify.sh**

Chạy: `scripts/verify.sh`
Kỳ vọng: `PASS — safe to publish`. Bước kiểm tra link của nó cũng chứng minh link `#handoff-choice` từ dev-designer trỏ đúng.

- [ ] **Bước 10: Commit**

```bash
git add skills/dev-lifecycle/SKILL.md skills/dev-lifecycle/references/handoff-template.md \
  skills/dev-designer/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Add the Handoff Choice and epic packaging" -m "- ask package-or-continue between Gate 2 and Stage 3
- add the packaging procedure and the handoff.md template
- add Resuming an Epic and point dev-designer at the Handoff Choice
- lock the new phrases in the lifecycle contract test"
```

### Task 2: Entry-Point Detection và tiếp tục

**File:**

- Sửa: `skills/dev-implementation/SKILL.md`
- Sửa: `scripts/test_lifecycle_document_contract.py`

**Giao diện:**

- Dùng: từ Task 1, `.devtool/epic/<epic_dir>/handoff.md`, giá trị Status `Packaged`, và template `skills/dev-lifecycle/references/handoff-template.md` (dùng cho lần chạy thử); từ `main`, kiểm tra mapping BDD ở Phase 1 bước 3 và `$INTEGRATE` từ Phase 0 bước 2.
- Cung cấp: Entry-Point Detection với các dòng 1 đến 7 và Resume Procedure, nơi quy tắc Resuming an Epic của dev-lifecycle chuyển quyền điều khiển tới.

- [ ] **Bước 1: Scenario baseline (RED)**

Trước khi sửa, dispatch một subagent general-purpose mới với prompt này và giữ lại câu trả lời:

```text
You are in the repository <ROOT>. Read skills/dev-implementation/SKILL.md. You were
invoked as "dev-implementation todo_export" (epic slug todo-export). Do not run anything. For each
situation, name the entry-point row and list, in order, what you do before any task code is written:
(A) .devtool/epic/todo_export/handoff.md exists; the overview Status is Packaged; there is no
epic/todo-export branch and no worktree; both tasks are todo.
(B) The branch epic/todo-export and the worktree .worktrees/todo_export exist; task_1 is done;
task_2 is in-progress and the worktree has uncommitted changes in src/export.py.
```

Kỳ vọng ở baseline: không có khái niệm dòng điểm vào; với (B), agent hoặc chạy lại Phase 1 từ đầu — kể cả `git worktree add -b`, lệnh sẽ lỗi vì branch đã tồn tại — hoặc tiếp tục mà không hỏi có giữ thay đổi chưa commit hay không. Ghi lại câu trả lời.

- [ ] **Bước 2: Khóa contract mới (test thất bại)**

Contract test — trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "--ids",
    ),
```

bằng:

```python
        "--ids",
        "Entry-Point Detection",
        "Resume Procedure",
        "handoff.md",
    ),
```

Chạy: `python3 scripts/test_lifecycle_document_contract.py`

Kỳ vọng: exit 1 với các dòng sau:

```text
  FAIL skills/dev-implementation/SKILL.md: missing Entry-Point Detection
  FAIL skills/dev-implementation/SKILL.md: missing Resume Procedure
  FAIL skills/dev-implementation/SKILL.md: missing handoff.md
```

- [ ] **Bước 3: Sửa skills/dev-implementation/SKILL.md**

Áp dụng chín chỗ sửa sau. Mỗi chuỗi neo xuất hiện đúng một lần.

A — trong When to Use, chèn ngay sau dòng này:

```markdown
- You are about to implement more than one task from that epic in this session.
```

Nội dung mới:

```markdown
- You are resuming an epic — packaged (`handoff.md` present, Status `Packaged`) or interrupted midway through Stage 3. Invoke this skill with the epic's directory name or slug; Entry-Point Detection in Phase 0 decides where to start.
```

B — trong sơ đồ Process, chèn ngay sau dòng này:

```markdown
    phase0["Phase 0: Context Reload & Platform Detection\n(detect_project_type.sh)"]
```

Nội dung mới:

```markdown
    entry{"Entry-Point Detection\n(rows 1-7)"}
    resume["Resume Procedure\nGate 3 (resume), reuse the worktree"]
```

C — trong cùng sơ đồ đó, thay:

```markdown
    phase0 --> phase1a
```

bằng:

```markdown
    phase0 --> entry
    entry -- "row 3: fresh start" --> phase1a
    entry -- "rows 4-5: interrupted" --> resume
    entry -- "row 6: tasks done" --> phase4
    resume --> phase2
```

D — ở đầu Phase 0, chèn ngay trước dòng này:

```markdown
1. Read, in full:
```

Nội dung mới:

```markdown
0. **Resolve the epic.** This skill takes one epic name, in either form:
   - If `.devtool/epic/<name>/` exists, `<epic_dir>` is `<name>`, and `<epic_slug>` is the `epic:` value of its task mirrors: `grep -h -m1 '^epic:' .devtool/epic/<name>/task_*.md`.
   - Otherwise `<name>` is a slug, and `<epic_dir>` is the directory holding the files `grep -l -F 'epic: "<name>"' .devtool/epic/*/task_*.md` lists.
   - With no name, or no match, list the epic directories whose overview Status is not `Done` and ask which one. Never guess, even when only one is listed.
```

E — trong danh sách đọc của Phase 0 bước 1, chèn ngay sau dòng này:

```markdown
   - Any spec file(s) linked from the HLD's Meta Data section.
```

Nội dung mới:

```markdown
   - `.devtool/epic/<epic_dir>/handoff.md`, when present — the packaging record. Use its Open Notes as context; it is never updated after packaging.
```

F — sau danh sách nền tảng của Phase 0 bước 3, chèn ngay sau dòng này:

```markdown
   - **`rust`**: Rust workspace (`Cargo.toml`, `xtask`, Clean Architecture + MVI, FFI/WASM).
```

Nội dung mới:

~~~~markdown
4. Run **Entry-Point Detection** (below) before Phase 1. It decides whether Phase 1 starts fresh or the Resume Procedure takes over.

#### Entry-Point Detection

Read these signals, all read-only, from the main checkout:

```bash
test -f .devtool/epic/<epic_dir>/handoff.md && echo packaged-handoff
grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/<epic_dir>/<epic_dir>.en.md
git rev-parse --verify --quiet refs/heads/epic/<epic_slug>
git branch -r --list '*/epic/<epic_slug>'
git worktree list --porcelain | grep -E '^worktree .*/\.worktrees/<epic_dir>$'
python3 "$SKILL_DIR"/resources/scripts/compute_execution_order.py <epic_slug>
```

`git branch -r` reveals an epic branch pushed from another clone. The last command's flattened order prints each task's status as `[priority, status]`; task files stay in `.devtool/features/` while `done` until Stage 4 archives them. Evaluate the rows top-down — the first match wins — and announce it: "Entry point: row N — <state>."

| # | Signals | State | Entry point |
|---|---------|-------|-------------|
| 1 | Overview Status is `Done` | Finished | Report it and stop |
| 2 | No epic branch, and any task is `backlog` | Queued behind another epic | Stop. Flipping `backlog` to `todo` is the developer's call |
| 3 | No epic branch locally or on a remote, no worktree, every task `todo` | Not started — packaged if `handoff.md` exists | Phase 1 as written: Gate 3, then a new worktree |
| 4 | Epic branch exists, no worktree, some task not `done` | Interrupted, worktree removed | Resume Procedure |
| 5 | Worktree exists, some task not `done` | Interrupted midway through Stage 3 | Resume Procedure |
| 6 | Epic branch exists, every task `done` | Tasks finished | Recreate the worktree if it is missing (`git worktree add .worktrees/<epic_dir> epic/<epic_slug>`, no `-b`) and bootstrap it (Phase 1 step 5), then Phase 4 with a full run — a verdict from another session cannot be tied to this SHA |
| 7 | Anything else — for example the epic branch only on a remote (work done in another clone), or tasks `in-progress` or `done` with no epic branch | Inconsistent | Stop, report the signals, ask |

#### Resume Procedure

For rows 4 and 5. Phase 1 step 4's `git worktree add -b` never runs here.

1. Row 4 only: recreate the worktree from the existing branch, `git worktree add .worktrees/<epic_dir> epic/<epic_slug>` with no `-b`. This restores an epic already under way; it is not the new worktree that Gate 3 guards. For rows 4 and 5, check the bootstrap with Phase 1 step 5's platform checks and re-run it if they fail.
2. In the worktree, run `python3 "$INTEGRATE" preflight --base develop`. A rebase in progress, or a base that diverged, is handled the way Phase 2 step 7 prescribes before anything else.
3. Find the interrupted task: one at `in-progress` or `review`. If the worktree has uncommitted changes, collect `git status --short`; uncommitted changes with no interrupted task are presented the same way.
4. **Gate 3 (resume).** Run Phase 1 step 3's BDD mapping check first, including its retrofit for an epic designed before scenario identifiers, and commit any retrofit on the epic branch, staging only the files it touched by path — both `bdd_scenarios` variants, both HLD variants and the task files — never `git add -A`, so the interrupted task's uncommitted work stays out of that commit. Then, in one message, present the tasks already `done` with their commits (`git log --oneline develop..epic/<epic_slug>`); the remaining order — the flattened order with `done` tasks removed, which keeps every dependency satisfied; for uncommitted changes, a choice between keeping them and continuing the task or discarding them and restarting it, discarding only on that explicit answer; and the request for permission to fast-forward `develop`, asked again because it does not carry across sessions. Wait for confirmation.
5. If the overview Status is `Packaged`, run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`.
6. Enter Phase 2 at the interrupted task, or at the first remaining task.
~~~~

G — trong Phase 1 bước 4, chèn ngay sau dòng này:

```markdown
   If `sync-base` exits 3 — `develop` diverged from its upstream, or a dirty file blocks the
   fast-forward — stop and ask.
```

Nội dung mới:

```markdown
   Once the worktree exists, if the overview Status is `Packaged` (a packaged epic starting fresh, row 3), run `python3 "$SKILL_DIR"/resources/scripts/sync_task_status.py epic <epic_dir> "In Progress"`; the change travels with the first task commit.
```

H — trong bảng Quick Reference, chèn ngay trước dòng này:

```markdown
| Create epic worktree |
```

Nội dung mới:

```markdown
| Resume an epic | Entry-Point Detection, then the Resume Procedure (no `-b`) | Same | Same |
```

I — trong mục Red Flags, chèn ngay sau dòng này:

```markdown
- Running `@quality_check` for Gate 4 before the full traceability check exits 0, or on a commit that check did not see.
```

Nội dung mới:

```markdown
- Starting Phase 1 without running Entry-Point Detection.
- Running `git worktree add -b` for an epic whose branch already exists.
- Re-implementing a task already `done`.
- Discarding an interrupted session's uncommitted changes without an explicit answer.
```

- [ ] **Bước 4: Chạy contract test và lint**

```bash
python3 scripts/test_lifecycle_document_contract.py
python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/SKILL.md
```

Kỳ vọng: `checked 11 lifecycle document contract surfaces`, rồi `checked 1 documents, 0 findings`.

- [ ] **Bước 5: Chạy thử Entry-Point Detection trên một epic dùng một lần**

Đây là integration test. Nó đưa một epic đi qua các dòng 3, 5, 4 và 6, in đúng những tín hiệu mà mục mới đọc, rồi kiểm tra cả hai dạng xác định tên epic. Dựng fixture:

````bash
KIT=$(git rev-parse --show-toplevel)
FIXDIR=$(mktemp -d)
cat > "$FIXDIR/make_fixture.sh" <<'EOF'
#!/usr/bin/env bash
# Build a throwaway git repository holding one two-task epic (dir todo_export, slug todo-export),
# for dry-running the epic handoff skill text. Usage: make_fixture.sh <empty-or-new-directory>
set -euo pipefail
FIX="$1"
mkdir -p "$FIX"
cd "$FIX"
git init -q -b main
printf '.worktrees/\n' > .gitignore
EPIC=.devtool/epic/todo_export
mkdir -p "$EPIC" .devtool/features/done
touch .devtool/features/done/.gitkeep
T='```'

printf '%s\n' "# Epic: Todo Export" "" "## Meta Data" "" "- **Status**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.en.md"
printf '%s\n' "# Epic: Xuất danh sách todo" "" "## Meta Data" "" "- **Trạng thái**: todo" \
  "- **Platform**: Python" "" "## Integration Test Plan" "" \
  "Integration test roots: tests/integration/" > "$EPIC/todo_export.vi.md"

printf '%s\n' "# BDD Scenarios: Todo Export" "" "## Export" "" "${T}gherkin" "Feature: Export" \
  "  Scenario: [TE-HP-01] [Tier C - Integration] Export todos as CSV" "    Given two todos" \
  "  Scenario: [TE-EC-02] Unknown format exits 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.en.md"
printf '%s\n' "# Kịch bản BDD: Xuất todo" "" "## Xuất" "" "${T}gherkin" "Feature: Export" \
  "  Kịch bản: [TE-HP-01] [Tier C - Integration] Xuất todo dạng CSV" "    Given two todos" \
  "  Kịch bản: [TE-EC-02] Định dạng lạ thoát mã 2" "    Given an unknown format" "$T" \
  > "$EPIC/bdd_scenarios.vi.md"

task() {  # task <file-stem> <number> <title> <covers> <dependency-line>
  printf '%s\n' "---" "id: \"$1\"" "status: \"todo\"" "priority: \"high\"" "epic: \"todo-export\"" \
    "---" "# Task $2: $3" "" "### BDD SCENARIOS" "" "Covers: $4" "" "## Dependencies & Blockers" "" "$5"
}
task task_1_export_core 1 "Export core" "TE-HP-01" "- None" > "$EPIC/task_1_export_core.md"
task task_2_cli_integration 2 "CLI integration" "TE-EC-02" \
  "- Blocked by [Task 1](task_1_export_core.md)" > "$EPIC/task_2_cli_integration.md"
cp "$EPIC"/task_*.md .devtool/features/

git add -A
git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: todo_export epic"
echo "fixture ready: $FIX"
EOF
bash "$FIXDIR/make_fixture.sh" "$FIXDIR/repo"
````

Sau đó chạy, trong cùng shell để `KIT` và `FIXDIR` vẫn còn giá trị:

```bash
cd "$FIXDIR/repo"
SCRIPTS="$KIT/skills/dev-implementation/resources/scripts"
signals() {
  test -f .devtool/epic/todo_export/handoff.md && echo "handoff: yes" || echo "handoff: no"
  grep -m1 -E '^- \*\*Status\*\*:' .devtool/epic/todo_export/todo_export.en.md
  git rev-parse --verify --quiet refs/heads/epic/todo-export > /dev/null && echo "branch: yes" || echo "branch: no"
  git branch -r --list '*/epic/todo-export' | grep -q . && echo "remote branch: yes" || echo "remote branch: no"
  git worktree list --porcelain | grep -q -E '^worktree .*/\.worktrees/todo_export$' && echo "worktree: yes" || echo "worktree: no"
  python3 "$SCRIPTS"/compute_execution_order.py todo-export | grep -E '^  [0-9]+\.'
}
cp "$KIT/skills/dev-lifecycle/references/handoff-template.md" .devtool/epic/todo_export/handoff.md
python3 "$SCRIPTS"/sync_task_status.py epic todo_export Packaged > /dev/null
git add -A && git -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "package"
echo "== row 3"; signals
git worktree add -q .worktrees/todo_export -b epic/todo-export main
python3 "$SCRIPTS"/sync_task_status.py task task_1_export_core done > /dev/null
echo "== row 5"; signals
git worktree remove --force .worktrees/todo_export
echo "== row 4"; signals
git worktree add -q .worktrees/todo_export epic/todo-export; echo "add without -b exit=$?"
python3 "$SCRIPTS"/sync_task_status.py task task_2_cli_integration done > /dev/null
echo "== row 6"; signals
echo "== name resolution"
grep -h -m1 '^epic:' .devtool/epic/todo_export/task_*.md | sort -u
grep -l -F 'epic: "todo-export"' .devtool/epic/*/task_*.md | xargs -n1 dirname | sort -u
cd "$KIT" && rm -rf "$FIXDIR"
```

Kỳ vọng:

```text
== row 3
handoff: yes
- **Status**: Packaged
branch: no
remote branch: no
worktree: no
  1. task_1_export_core - Export core [high, todo]
  2. task_2_cli_integration - CLI integration [high, todo]
== row 5
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: yes
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, todo]
== row 4
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: no
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, todo]
add without -b exit=0
== row 6
handoff: yes
- **Status**: Packaged
branch: yes
remote branch: no
worktree: yes
  1. task_1_export_core - Export core [high, done]
  2. task_2_cli_integration - CLI integration [high, done]
== name resolution
epic: "todo-export"
.devtool/epic/todo_export
```

Mỗi khối tín hiệu phải chọn đúng dòng mà tiêu đề của nó nêu trong bảng Entry-Point Detection, và `add without -b exit=0` chứng minh việc tạo lại worktree ở dòng 4 chạy được trên branch có sẵn.

- [ ] **Bước 6: Chạy lại scenario (GREEN)**

Dispatch một subagent mới khác với prompt của Bước 1, giữ nguyên. Kỳ vọng: (A) dòng 3 — Phase 1, Gate 3, worktree mới với `-b`, rồi Status chuyển từ `Packaged` sang `In Progress`; (B) dòng 5 — Resume Procedure: kiểm tra bootstrap, `integrate_branch.py preflight`, xác định task_2 bị ngắt kèm `git status --short`, Gate 3 (tiếp tục) chạy kiểm tra mapping BDD, liệt kê các task đã xong kèm commit và thứ tự còn lại, hỏi giữ hay bỏ thay đổi trong `src/export.py` và xin quyền fast-forward `develop` — không bao giờ `git worktree add -b`. Nếu còn phần nào thiếu, siết lại chỗ sửa tương ứng và chạy lại.

- [ ] **Bước 7: Chạy verify.sh**

Chạy: `scripts/verify.sh`
Kỳ vọng: `PASS — safe to publish`.

- [ ] **Bước 8: Commit**

```bash
git add skills/dev-implementation/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Add entry-point detection and resume to dev-implementation" -m "- resolve the epic from its directory name or slug
- pick the entry point from handoff.md, status, branch, worktree and task states
- add the Resume Procedure and move a packaged epic to In Progress
- lock the new phrases in the lifecycle contract test"
```

## Kiểm tra cuối cùng

- [ ] Chạy `scripts/verify.sh` trên commit cuối. Kỳ vọng: `PASS — safe to publish`.
- [ ] Đối chiếu từng mục của spec với diff: §4 luồng và câu hỏi (Task 1 Edit A, B và E), §5 thành phần (cả hai task), §6 template (Task 1 Bước 3), §7 quy trình đóng gói (Task 1 Edit E), §8.1 xác định epic (Task 2 Edit D), §8.2 và §8.3 tín hiệu và các dòng (Task 2 Edit F), §8.4 Resume Procedure (Task 2 Edit F), §8.5 đổi trạng thái khi bắt đầu mới (Task 2 Edit G), §9 red flags (Task 1 Edit G và K, Task 2 Edit I), và hàng Gate 3 (Task 1 Edit I).
- [ ] Quality gate: gọi `@quality_check` theo yêu cầu của `CRITICAL_RULES`. Repo này không có `.agents/quality/check_quality.json`, nên kỳ vọng `BLOCKED`; báo cáo đúng như vậy. Release gate của kit là `scripts/verify.sh`.
- [ ] Không push. Báo cáo hai commit và chờ developer.
