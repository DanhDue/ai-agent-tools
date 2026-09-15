# BDD Scenarios: Robust Epic Slug Sanitization & Normalization

- **Epic**: `epic_slug_sanitization`
- **Topic**: Slug Sanitization across `slug_utils.py`, `sync_task_status.py`, and `compute_execution_order.py`
- **Created**: 2026-09-15

---

## Scenario 1: Sanitizing Backticks in Epic Identifiers
- **Tag**: `[Tier A - Unit]`
- **Given**: A raw epic string wrapped in markdown backticks: `` `flutter_super_app_template` ``
- **When**: `sanitize_slug(raw)` is invoked
- **Then**: It returns `"flutter_super_app_template"` without backticks or whitespace.

---

## Scenario 2: Sanitizing Straight and Smart Quotes
- **Tag**: `[Tier A - Unit]`
- **Given**: Raw epic strings wrapped in:
  - Double quotes: `"logging-refactor"`
  - Single quotes: `'logging-refactor'`
  - Curly quotes: `“super_app_governance”` and `‘super_app_governance’`
- **When**: `sanitize_slug(raw)` is invoked on each
- **Then**: It returns the clean unquoted slug for each variant.

---

## Scenario 3: Sanitizing Markdown Links and Code Blocks
- **Tag**: `[Tier A - Unit]`
- **Given**: A raw epic string formatted as:
  - Markdown link: `[my_epic](path/to/hld.md)`
  - Markdown link with backtick: `[`my_epic`](path/to/hld.md)`
  - HTML code tag: `<code>my_epic</code>`
- **When**: `sanitize_slug(raw)` is invoked
- **Then**: It extracts and returns `"my_epic"`.

---

## Scenario 4: Sanitizing HTML Comments and Trailing Annotations
- **Tag**: `[Tier A - Unit]`
- **Given**: Raw strings containing:
  - HTML comments: `my_epic <!-- core epic -->`
  - Parenthetical notes: `my_epic (Super App Core)`
  - Trailing punctuation: `my_epic:` or `my_epic,`
- **When**: `sanitize_slug(raw)` is invoked
- **Then**: It isolates and returns `"my_epic"`.

---

## Scenario 5: Handling Empty, None, and Whitespace Inputs
- **Tag**: `[Tier A - Unit]`
- **Given**: Input values of `None`, `""`, or `"   "`
- **When**: `sanitize_slug(raw)` is invoked
- **Then**: It returns `None`.

---

## Scenario 6: Parsing Frontmatter with Varied Quotation Styles
- **Tag**: `[Tier A - Unit]`
- **Given**: Task YAML frontmatter blocks:
  - Block A: `epic: "my_epic"`
  - Block B: `epic: 'my_epic'`
  - Block C: `epic: `my_epic``
- **When**: `parse_frontmatter(text)` is invoked on each block
- **Then**: `fm["epic"]` equals `"my_epic"` across all three blocks.

---

## Scenario 7: Archiving Tasks with Backtick-Formatted HLD Overview
- **Tag**: `[Tier C - Integration]`
- **Given**: An epic overview `.en.md` specifying `- **Epic**: `my_epic``
- **And**: A completed task in `.devtool/features/done/task_1.md` with `epic: "my_epic"`
- **When**: `sync_task_status.py archive-done` is executed
- **Then**: The task is recognized as matching `my_epic`
- **And**: It is relocated to `.devtool/epic/my_epic/task_1.md`
- **And**: It is deleted from `.devtool/features/done/`.

---

## Scenario 8: Ordering Tasks with Formatted CLI Arguments
- **Tag**: `[Tier C - Integration]`
- **Given**: Tasks in `.devtool/features/` with `epic: "my_epic"`
- **When**: A developer invokes `compute_execution_order.py `my_epic``
- **Then**: The CLI sanitizes the argument to `"my_epic"`
- **And**: Matches all tasks without reporting them as skipped
- **And**: Outputs deterministic execution layers.
