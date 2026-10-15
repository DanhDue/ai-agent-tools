# Implementation Plan cho truy vết BDD sang integration test

> **Dành cho agent thực thi:** BẮT BUỘC dùng sub-skill d3nexus:subagent-driven-development (khuyến nghị) hoặc d3nexus:executing-plans để thực hiện plan này theo từng task. Các bước dùng cú pháp checkbox (`- [ ]`) để theo dõi.

**Mục tiêu:** Chứng minh được rằng mọi scenario trong `bdd_scenarios.en.md` của một epic đều được phủ bởi ít nhất một automation integration test, và việc này được một script kiểm tra ở lúc thiết kế, ở từng task, và ở Gate 4.

**Kiến trúc:** Một script chỉ dùng thư viện chuẩn, `check_bdd_traceability.py`, kiểm tra định danh scenario và hai loại mapping — định danh sang task (chế độ `plan`, qua dòng `Covers:`) và định danh sang file integration test (chế độ `tests`, theo chuỗi định danh). `dev-designer` bắt buộc có định danh, dòng `Covers:` và thư mục integration test, và chạy `plan` trước khi commit. `dev-implementation` chạy `tests` theo từng task và trước `quality_check`. `dev-lifecycle` đưa exit 0 của script vào Gate 4.

**Công nghệ:** Thư viện chuẩn Python 3 (`argparse`, `re`, `pathlib`), `unittest`, các file skill Markdown, `scripts/verify.sh`.

**Spec:** [2026-10-15-bdd-integration-traceability-design.vi.md](../specs/2026-10-15-bdd-integration-traceability-design.vi.md)

## Mục lục

- [Ràng buộc chung](#ràng-buộc-chung)
- [Cấu trúc file](#cấu-trúc-file)
- [Các task](#các-task)
  - [Task 1: Script truy vết](#task-1-script-truy-vết)
  - [Task 2: dev-designer khai báo mapping](#task-2-dev-designer-khai-báo-mapping)
  - [Task 3: dev-implementation thực thi mapping](#task-3-dev-implementation-thực-thi-mapping)
  - [Task 4: Gate 4 của dev-lifecycle](#task-4-gate-4-của-dev-lifecycle)
- [Kiểm tra cuối cùng](#kiểm-tra-cuối-cùng)

## Ràng buộc chung

- Mọi scenario trong `bdd_scenarios.en.md` cần **ít nhất một** automation integration test; một test được phủ nhiều scenario. Không có miễn trừ.
- Hình dạng định danh: `[A-Z][A-Z0-9]*(-[A-Z0-9]+)*-[0-9]+`, nằm trong ngoặc vuông, đứng đầu dòng scenario, trước mọi tag tier. Quy ước `<EPIC>-<DIM>-<NN>` được khuyến nghị, không bị ép.
- Từ khóa scenario được nhận diện: `Scenario`, `Scenario Outline`, `Scenario Template`, `Example`, `Tình huống`, `Kịch bản`, `Khung tình huống`, `Khung kịch bản` — chỉ trong khối `gherkin`.
- So khớp coverage: không phân biệt hoa thường, coi `-` và `_` như nhau, không có chữ cái hay chữ số đứng sát trước hoặc sau. Phát hiện stale: chỉ dạng viết hoa có gạch nối, chỉ ở lần chạy đầy đủ.
- Exit code: `0` là phủ đủ; `1` là lỗi truy vết; `2` là lỗi sử dụng (thiếu file scenario hoặc file task, hoặc không thư mục nào tồn tại).
- Chỉ dùng thư viện chuẩn. Không thay đổi `quality_check`, contract, schema, provider của nó, và không thay đổi `writing-plans`.
- Frontmatter của `SKILL.md` giữ đúng `name` + `description`.
- Commit: `[SKILLS] <title>` kèm phần thân dạng bullet khi có nhiều hơn một thay đổi; không bao giờ có dòng trailer.
- File task vẫn chỉ viết tiếng Anh.
- `--roots` và `--ids` nhận giá trị phân tách bằng dấu cách hoặc dấu phẩy, nên chép nguyên văn dòng từ HLD hoặc dòng `Covers:` vẫn chạy được.
- Bước 1 và 5 của Task 2 đến 4 dispatch subagent mới để kiểm tra câu chữ của skill. Implementer không dispatch được subagent thì báo lại, và controller sẽ chạy hai bước đó.

## Cấu trúc file

| File | Trách nhiệm |
|------|-------------|
| `skills/dev-implementation/resources/scripts/check_bdd_traceability.py` | Tạo mới. Phân tích định danh scenario, dòng `Covers:` và file test; in ma trận; trả exit code |
| `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py` | Tạo mới. 24 test `unittest` |
| `scripts/verify.sh` | Sửa. Chạy test mới ở bước 11 |
| `scripts/test_lifecycle_document_contract.py` | Sửa. Khóa các cụm từ mới trong ba skill |
| `skills/dev-designer/SKILL.md` | Sửa. Định danh, thư mục test, `Covers:`, Tier C BDD Automation, kiểm tra `plan` trước commit |
| `skills/dev-implementation/SKILL.md` | Sửa. Quy tắc cho Integration persona, `tests --ids` theo từng task, `tests` đầy đủ trước `quality_check` |
| `skills/dev-lifecycle/SKILL.md` | Sửa. Gate 4 bao gồm kiểm tra truy vết |

## Các task

### Task 1: Script truy vết

**File:**

- Tạo mới: `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`
- Tạo mới: `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
- Sửa: `scripts/verify.sh` (bước 11)

**Giao diện:**

- Dùng: không có.
- Cung cấp: CLI mà Task 2 đến 4 sử dụng —
  `check_bdd_traceability.py plan --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>` và
  `check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]`,
  in một dòng `ID    places` cho mỗi định danh và một dòng cuối `Result: N/M covered — PASS|FAIL`.

- [ ] **Bước 1: Viết các test sẽ thất bại**

Tạo `skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`:

```python
#!/usr/bin/env python3
"""Tests for check_bdd_traceability.py.

Run: python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check_bdd_traceability import main

TICKS = "`" * 3
TWO = ("Scenario: [PY-HP-01] [Tier C - Integration] First",
       "Scenario Outline: [PY-EC-02] Second")


def gherkin(*scenario_lines: str) -> str:
    body = "\n".join(f"  {line}\n    Given a precondition\n" for line in scenario_lines)
    return f"# BDD Scenarios\n\n{TICKS}gherkin\nFeature: Sample\n\n{body}{TICKS}\n"


class TraceabilityCase(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, relative: str, text: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def scenarios(self, *lines: str) -> Path:
        return self.write("epic/bdd_scenarios.en.md", gherkin(*lines))

    def run_cli(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main([str(arg) for arg in argv])
            except SystemExit as exit_:
                code = exit_.code
        return code, out.getvalue(), err.getvalue()

    def plan(self, scenarios: Path, *tasks: Path) -> tuple[int, str, str]:
        return self.run_cli("plan", "--scenarios", scenarios, "--tasks", *tasks)

    def covering_task(self) -> Path:
        return self.write("epic/task_1_all.md", "Covers: PY-HP-01, PY-EC-02\n")


class DocumentValidationTest(TraceabilityCase):
    def test_scenario_without_identifier_fails(self) -> None:
        scenarios = self.scenarios("Scenario: [PY-HP-01] First", "Scenario: Second")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("scenario has no identifier", out)

    def test_tier_tag_in_identifier_position_is_malformed(self) -> None:
        scenarios = self.scenarios("Scenario: [Tier A - Unit] First")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("malformed identifier [Tier A - Unit]", out)

    def test_duplicate_identifier_fails(self) -> None:
        scenarios = self.scenarios("Scenario: [PY-HP-01] First", "Scenario: [PY-HP-01] Again")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("duplicate identifier PY-HP-01", out)

    def test_vietnamese_sibling_with_same_identifiers_passes(self) -> None:
        scenarios = self.scenarios(*TWO)
        self.write("epic/bdd_scenarios.vi.md", gherkin(
            "Kịch bản: [PY-HP-01] Thứ nhất", "Khung tình huống: [PY-EC-02] Thứ hai"))
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 0, out)

    def test_vietnamese_sibling_missing_identifier_fails(self) -> None:
        scenarios = self.scenarios(*TWO)
        self.write("epic/bdd_scenarios.vi.md", gherkin("Kịch bản: [PY-HP-01] Thứ nhất"))
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("missing identifiers PY-EC-02", out)

    def test_scenario_lines_outside_gherkin_fences_are_ignored(self) -> None:
        text = gherkin(*TWO) + "\nScenario: prose without an identifier\n" \
            + f"{TICKS}text\nScenario: also outside gherkin\n{TICKS}\n"
        scenarios = self.write("epic/bdd_scenarios.en.md", text)
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 0, out)

    def test_document_without_scenarios_fails(self) -> None:
        scenarios = self.write("epic/bdd_scenarios.en.md", "# BDD Scenarios\n")
        code, out, _ = self.plan(scenarios, self.covering_task())
        self.assertEqual(code, 1)
        self.assertIn("no scenarios found", out)

    def test_missing_scenario_document_exits_2(self) -> None:
        code, _, err = self.plan(self.root / "absent.en.md", self.covering_task())
        self.assertEqual(code, 2)
        self.assertIn("scenario document not found", err)


class PlanModeTest(TraceabilityCase):
    def test_every_identifier_in_a_task_passes(self) -> None:
        first = self.write("epic/task_1_first.md", "Covers: PY-HP-01\n")
        second = self.write("epic/task_2_second.md", "Covers: PY-EC-02\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first, second)
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def test_identifier_in_no_task_fails(self) -> None:
        first = self.write("epic/task_1_first.md", "Covers: PY-HP-01\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first)
        self.assertEqual(code, 1)
        self.assertRegex(out, r"PY-EC-02\s+\(none\)")

    def test_unknown_identifier_in_covers_fails(self) -> None:
        task = self.write("epic/task_1_all.md", "Covers: PY-HP-01, PY-EC-02, PY-HP-99\n")
        code, out, _ = self.plan(self.scenarios(*TWO), task)
        self.assertEqual(code, 1)
        self.assertIn("Covers names unknown identifier PY-HP-99", out)

    def test_list_item_and_bold_covers_variants_are_read(self) -> None:
        first = self.write("epic/task_1_first.md", "- **Covers**: `PY-HP-01`\n")
        second = self.write("epic/task_2_second.md", "**Covers:** PY-EC-02\n")
        code, out, _ = self.plan(self.scenarios(*TWO), first, second)
        self.assertEqual(code, 0, out)

    def test_missing_task_file_exits_2(self) -> None:
        code, _, err = self.plan(self.scenarios(*TWO), self.root / "epic/task_9_absent.md")
        self.assertEqual(code, 2)
        self.assertIn("task file not found", err)


class TestsModeTest(TraceabilityCase):
    def run_tests_mode(self, *extra: object, roots: tuple[str, ...] = ("tests/integration",)) -> tuple[int, str, str]:
        return self.run_cli("tests", "--scenarios", self.scenarios(*TWO),
                            "--roots", *(self.root / root for root in roots), *extra)

    def test_hyphenated_snake_and_lowercase_references_count(self) -> None:
        self.write("tests/integration/flow_test.dart", "testWidgets('[PY-HP-01] first', () {});\n")
        self.write("tests/integration/test_flow.py", "def test_py_ec_02_second():\n    pass\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)
        self.assertIn("flow_test.dart:1", out)
        self.assertIn("test_flow.py:1", out)

    def test_longer_digit_run_does_not_cover(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-010] other', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-01")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"PY-HP-01\s+\(none\)")

    def test_markdown_files_are_ignored(self) -> None:
        self.write("tests/integration/README.md", "PY-HP-01 and PY-EC-02 are covered elsewhere\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("Result: 0/2 covered — FAIL", out)

    def test_ids_limits_the_check_and_skips_staleness(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-HP-07] first', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-01")
        self.assertEqual(code, 0, out)
        self.assertNotIn("PY-EC-02", out)

    def test_stale_reference_fails_the_full_run(self) -> None:
        self.write("tests/integration/flow_test.ts",
                   "test('[PY-HP-01] [PY-EC-02] [PY-HP-07] all', () => {});\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 1)
        self.assertIn("stale reference PY-HP-07", out)

    def test_snake_and_lowercase_tokens_are_never_stale(self) -> None:
        self.write("tests/integration/test_flow.py",
                   "def test_py_hp_01_retry_2():\n    pass\n\n"
                   "def test_py_ec_02_second():\n    assert 'py-3' != 'PY-HP'\n")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)

    def test_missing_root_warns_while_others_are_scanned(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, err = self.run_tests_mode(roots=("tests/integration", "tests/e2e"))
        self.assertEqual(code, 0, out)
        self.assertIn("integration test root not found", err)

    def test_no_existing_root_exits_2(self) -> None:
        code, _, err = self.run_tests_mode(roots=("tests/e2e",))
        self.assertEqual(code, 2)
        self.assertIn("none of the integration test roots exists", err)

    def test_comma_separated_roots_and_ids_are_accepted(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        code, out, _ = self.run_cli("tests", "--scenarios", self.scenarios(*TWO),
                                    "--roots", f"{self.root / 'tests/integration'},", self.root / "tests/e2e",
                                    "--ids", "PY-HP-01,", "PY-EC-02")
        self.assertEqual(code, 0, out)
        self.assertIn("Result: 2/2 covered — PASS", out)

    def test_unknown_identifier_in_ids_fails(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] first', () => {});\n")
        code, out, _ = self.run_tests_mode("--ids", "PY-HP-99")
        self.assertEqual(code, 1)
        self.assertIn("--ids names unknown identifier PY-HP-99", out)

    def test_undecodable_file_is_skipped(self) -> None:
        self.write("tests/integration/flow_test.ts", "test('[PY-HP-01] [PY-EC-02] all', () => {});\n")
        (self.root / "tests/integration/fixture.bin").write_bytes(b"\xff\xfe\x00PY-HP-07")
        code, out, _ = self.run_tests_mode()
        self.assertEqual(code, 0, out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Bước 2: Chạy test để xác nhận chúng thất bại**

Chạy: `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
Kỳ vọng: ERROR — `ModuleNotFoundError: No module named 'check_bdd_traceability'`.

- [ ] **Bước 3: Viết script**

Tạo `skills/dev-implementation/resources/scripts/check_bdd_traceability.py`:

```python
#!/usr/bin/env python3
"""Check that every epic BDD scenario is assigned to a task and covered by an integration test.

Usage:
  check_bdd_traceability.py plan  --scenarios <bdd_scenarios.en.md> --tasks <task_*.md ...>
  check_bdd_traceability.py tests --scenarios <bdd_scenarios.en.md> --roots <dir ...> [--ids <ID ...>]

Exit codes: 0 all covered; 1 traceability failure; 2 usage error.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ID_SHAPE = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-[0-9]+")
SCENARIO_KEYWORDS = (
    "Scenario Outline", "Scenario Template", "Scenario", "Example",
    "Khung tình huống", "Khung kịch bản", "Tình huống", "Kịch bản",
)
SCENARIO_LINE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(keyword) for keyword in SCENARIO_KEYWORDS) + r")\s*:\s*(.*)$"
)
LEADING_TAG = re.compile(r"^\[([^\]]*)\]")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*(\S*)")
COVERS_LINE = re.compile(r"^\s*(?:[-*]\s+)?\**Covers\**\s*:\**\s*(.*)$")


class UsageError(Exception):
    """Missing input: exit 2."""


def scenario_ids(path: Path) -> tuple[list[str], list[str]]:
    """Identifiers in document order, and the problems found, for one scenario document."""
    ids: list[str] = []
    problems: list[str] = []
    fence_marker: str | None = None
    in_gherkin = False
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        fence = FENCE.match(line)
        if fence and fence_marker is None:
            fence_marker, in_gherkin = fence.group(1), fence.group(2).lower() == "gherkin"
            continue
        if fence and fence.group(1) == fence_marker and not fence.group(2):
            fence_marker, in_gherkin = None, False
            continue
        match = SCENARIO_LINE.match(line) if in_gherkin else None
        if not match:
            continue
        tag = LEADING_TAG.match(match.group(1).strip())
        if not tag:
            problems.append(f"{path}:{number}: scenario has no identifier")
        elif not ID_SHAPE.fullmatch(tag.group(1)):
            problems.append(f"{path}:{number}: malformed identifier [{tag.group(1)}]")
        elif tag.group(1) in ids:
            problems.append(f"{path}:{number}: duplicate identifier {tag.group(1)}")
        else:
            ids.append(tag.group(1))
    return ids, problems


def load_scenarios(path: Path) -> tuple[list[str], list[str]]:
    """Validate the English document and, when present, its Vietnamese sibling."""
    if not path.is_file():
        raise UsageError(f"scenario document not found: {path}")
    ids, problems = scenario_ids(path)
    if not ids and not problems:
        problems.append(f"{path}: no scenarios found inside gherkin fences")
    if path.name.endswith(".en.md"):
        sibling = path.with_name(path.name[: -len(".en.md")] + ".vi.md")
        if sibling.is_file():
            vi_ids, vi_problems = scenario_ids(sibling)
            problems.extend(vi_problems)
            missing = sorted(set(ids) - set(vi_ids))
            extra = sorted(set(vi_ids) - set(ids))
            if missing:
                problems.append(f"{sibling}: missing identifiers {', '.join(missing)}")
            if extra:
                problems.append(f"{sibling}: identifiers not in {path.name}: {', '.join(extra)}")
    return ids, problems


def covers_of(path: Path) -> list[str]:
    """Identifiers named on every Covers: line of one task file."""
    found: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = COVERS_LINE.match(line)
        if match:
            tokens = (token.strip("`[]*") for token in re.split(r"[,\s]+", match.group(1)))
            found.extend(token for token in tokens if token)
    return found


def check_plan(ids: list[str], task_paths: list[Path]) -> tuple[dict[str, list[str]], list[str]]:
    coverage: dict[str, list[str]] = {identifier: [] for identifier in ids}
    problems: list[str] = []
    for path in task_paths:
        if not path.is_file():
            raise UsageError(f"task file not found: {path}")
        for identifier in covers_of(path):
            if identifier not in coverage:
                problems.append(f"{path}: Covers names unknown identifier {identifier}")
            elif path.name not in coverage[identifier]:
                coverage[identifier].append(path.name)
    return coverage, problems


def reference_pattern(identifier: str) -> re.Pattern[str]:
    """Match an identifier in any case, with - and _ interchangeable, not inside a longer token."""
    body = "[-_]".join(re.escape(part) for part in identifier.split("-"))
    return re.compile(r"(?<![A-Za-z0-9])" + body + r"(?![A-Za-z0-9])", re.IGNORECASE)


def stale_pattern(ids: list[str]) -> re.Pattern[str]:
    """Uppercase hyphenated tokens that share a prefix with this document's identifiers."""
    prefixes = "|".join(sorted({re.escape(identifier.split("-")[0]) for identifier in ids}))
    return re.compile(r"(?<![A-Za-z0-9-])(?:" + prefixes + r")(?:-[A-Z0-9]+)*-[0-9]+(?![A-Za-z0-9-])")


def integration_files(roots: list[Path]) -> tuple[list[Path], list[str]]:
    existing = [root for root in roots if root.is_dir()]
    warnings = [f"warning: integration test root not found, skipped: {root}"
                for root in roots if not root.is_dir()]
    if not existing:
        raise UsageError("none of the integration test roots exists: " + ", ".join(map(str, roots)))
    files = [path for root in existing for path in sorted(root.rglob("*"))
             if path.is_file() and path.suffix.lower() != ".md"]
    return files, warnings


def check_tests(ids: list[str], selected: list[str], roots: list[Path],
                check_stale: bool) -> tuple[dict[str, list[str]], list[str], list[str]]:
    patterns = {identifier: reference_pattern(identifier) for identifier in selected}
    coverage: dict[str, list[str]] = {identifier: [] for identifier in selected}
    stale = stale_pattern(ids)
    known = set(ids)
    problems: list[str] = []
    files, warnings = integration_files(roots)
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(lines, start=1):
            for identifier, pattern in patterns.items():
                if pattern.search(line):
                    coverage[identifier].append(f"{path}:{number}")
            if check_stale:
                problems.extend(f"{path}:{number}: stale reference {token}"
                                for token in stale.findall(line) if token not in known)
    return coverage, problems, warnings


def split_values(values: list[str] | None) -> list[str]:
    """Accept space- or comma-separated values, as copied from an HLD or Covers: line."""
    return [part.strip() for value in values or [] for part in value.split(",") if part.strip()]


def report(coverage: dict[str, list[str]], problems: list[str], warnings: list[str]) -> int:
    width = max((len(identifier) for identifier in coverage), default=0)
    for identifier, places in coverage.items():
        print(f"{identifier.ljust(width)}    {', '.join(places) if places else '(none)'}")
    for warning in warnings:
        print(warning, file=sys.stderr)
    for problem in problems:
        print(problem)
    covered = sum(1 for places in coverage.values() if places)
    failed = bool(problems) or covered < len(coverage)
    print(f"Result: {covered}/{len(coverage)} covered — {'FAIL' if failed else 'PASS'}")
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    modes = parser.add_subparsers(dest="mode", required=True)
    plan = modes.add_parser("plan", help="every scenario is assigned to at least one task")
    plan.add_argument("--scenarios", required=True, type=Path)
    plan.add_argument("--tasks", required=True, nargs="+", type=Path)
    tests = modes.add_parser("tests", help="every scenario has at least one integration test")
    tests.add_argument("--scenarios", required=True, type=Path)
    tests.add_argument("--roots", required=True, nargs="+")
    tests.add_argument("--ids", nargs="+")
    args = parser.parse_args(argv)
    try:
        ids, problems = load_scenarios(args.scenarios)
        if problems:
            print("\n".join(problems))
            print("Result: scenario document invalid — FAIL")
            return 1
        if args.mode == "plan":
            coverage, problems = check_plan(ids, args.tasks)
            return report(coverage, problems, [])
        roots = [Path(value) for value in split_values(args.roots)]
        selected = split_values(args.ids) or ids
        unknown = [f"--ids names unknown identifier {identifier}"
                   for identifier in selected if identifier not in ids]
        known_selected = [identifier for identifier in selected if identifier in ids]
        coverage, problems, warnings = check_tests(ids, known_selected, roots, not args.ids)
        return report(coverage, unknown + problems, warnings)
    except UsageError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

Sau đó cấp quyền chạy: `chmod +x skills/dev-implementation/resources/scripts/check_bdd_traceability.py`.

- [ ] **Bước 4: Chạy test để xác nhận chúng pass**

Chạy: `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`
Kỳ vọng: `Ran 24 tests` và `OK`.

- [ ] **Bước 5: Chạy tích hợp và edge case trên một epic thật**

24 unit test đã phủ ma trận biên: định danh thiếu, sai hình dạng và trùng, từ khóa tiếng Việt và đồng bộ ngôn ngữ, tài liệu rỗng, task lạ và task thiếu, từng dạng tham chiếu, biên của dãy số, file bị bỏ qua và file không giải mã được, thư mục thiếu, và stale. Bước này chạy CLI từ đầu đến cuối trên một epic thật đã lưu trữ:

Chạy:

```bash
python3 skills/dev-implementation/resources/scripts/check_bdd_traceability.py tests \
  --scenarios .devtool/epic/python_quality_provider_and_onboarding/bdd_scenarios.en.md \
  --roots skills/python-quality-check/resources/scripts
echo "exit=$?"
```

Kỳ vọng: mười một dòng `(none)` từ `PY-HP-01` đến `PY-FAIL-03`, rồi `Result: 0/11 covered — FAIL` và `exit=1`. Bản tiếng Việt đi kèm qua được kiểm tra đồng bộ, nên không có dòng `scenario document invalid`. Đây chính là lỗ hổng mà thay đổi này lấp lại; epic đã lưu trữ không bị sửa.

- [ ] **Bước 6: Nối test vào verify.sh**

Trong `scripts/verify.sh`, bước 11, chèn sau dòng `python3 scripts/test_lifecycle_document_contract.py || FAILED=1`:

```bash
python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py || FAILED=1
```

Chạy: `scripts/verify.sh`
Kỳ vọng: dòng cuối `PASS — safe to publish`; bước 11 hiện `Ran 24 tests` và `OK`.

- [ ] **Bước 7: Commit**

```bash
git add skills/dev-implementation/resources/scripts/check_bdd_traceability.py \
  skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py scripts/verify.sh
git commit -m "[SKILLS] Add BDD traceability check script" -m "- add check_bdd_traceability.py with plan and tests modes
- add 24 unittest cases and run them from verify.sh step 11"
```

### Task 2: dev-designer khai báo mapping

**File:**

- Sửa: `skills/dev-designer/SKILL.md`
- Sửa: `scripts/test_lifecycle_document_contract.py`

**Giao diện:**

- Dùng: CLI `plan` từ Task 1.
- Cung cấp: các quy ước mà Task 3 dựa vào — định danh scenario trong `bdd_scenarios.*.md`, dòng
  HLD `Integration test roots: <dir>, <dir>`, và dòng trong file task `Covers: <ID>, <ID>`.

- [ ] **Bước 1: Scenario baseline (RED)**

Trước khi sửa bất cứ thứ gì, chạy `git rev-parse --show-toplevel` trong checkout đang thực thi plan này — là worktree, không phải main checkout — và thay kết quả vào chỗ `<ROOT>` bên dưới. Dùng cùng giá trị đó ở Bước 5. Sau đó dispatch một subagent general-purpose mới với prompt này và giữ lại câu trả lời:

```text
You are in the repository <ROOT>. Read
skills/dev-designer/SKILL.md and follow it. Approved spec, Python project, epic directory
todo_export, epic slug todo-export: "Add a CLI command `todo export --format csv|json` that writes
all todos to stdout. An empty list prints only the CSV header or `[]`. An unknown format exits 2
with an error message." Do not create or edit any file. Reply with exactly four parts:
(1) the first two scenarios of bdd_scenarios.en.md as they would appear;
(2) the Integration Test Plan lines of the HLD;
(3) the first five lines of the BDD SCENARIOS section of the final Tier C task file;
(4) every command you would run between writing the task files and the Step 3 commit.
```

Kỳ vọng ở baseline: phần 1 có thể có hoặc không có định danh trong ngoặc vuông; phần 2 không có dòng `Integration test roots:`; phần 3 không có dòng `Covers:`; phần 4 không nhắc tới `check_bdd_traceability.py`. Ghi lại những phần còn thiếu — Bước 5 chạy lại đúng prompt này.

- [ ] **Bước 2: Khóa contract mới (test thất bại)**

Trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "Task files are English-only",
    ),
```

bằng:

```python
        "Task files are English-only",
        "check_bdd_traceability.py plan",
        "Covers:",
        "Integration test roots:",
        "at least one automated integration test",
    ),
```

Chạy: `python3 scripts/test_lifecycle_document_contract.py`
Kỳ vọng: exit 1 với `FAIL skills/dev-designer/SKILL.md: missing check_bdd_traceability.py plan` và thêm ba dòng `missing` cho các token mới còn lại.

- [ ] **Bước 3: Sửa skills/dev-designer/SKILL.md**

Áp dụng tám chỗ sửa sau.

Edit A — chèn một dòng mới ngay sau bullet bắt đầu bằng `- **Integration Test Plan & Boundary Matrix**:` (Step 1, mục 5):

```markdown
   - **Integration Test Roots**: The Integration Test Plan MUST contain the line `Integration test roots: <dir>, <dir>` naming every directory that holds integration tests. Defaults: `tests/e2e/` (Web), `integration_test/` (Flutter), `app/src/test/` and `shell/src/test/` (Android), `App/Tests/` and `Shell/Tests/` (iOS), `tests/integration/` (Python), `tests/` (Rust). `check_bdd_traceability.py` scans exactly these directories.
```

Edit B — chèn một dòng mới ngay sau bullet `- Both files MUST organize scenarios by Use Case, exhaustively covering all 5 dimensions above in Gherkin syntax.` (Step 1, mục 6):

```markdown
   - **Scenario IDs**: Every `Scenario:` or `Scenario Outline:` line starts with a unique identifier in brackets, before any tier tag: `Scenario: [PY-HP-01] [Tier C - Integration] ...`. Shape: uppercase segments joined by `-`, ending in digits; convention `<EPIC>-<DIM>-<NN>` with `HP`, `EC`, `ST`, `AR`, `FR` for the five dimensions. The `.vi.md` file carries exactly the same identifiers, untranslated. The first segment is this epic's prefix and MUST NOT be used by any other epic in the project, because integration test roots hold every epic's tests; list the prefixes already taken with `grep -ho '\[[A-Z][A-Z0-9]*-' .devtool/epic/*/bdd_scenarios.en.md | sort -u`.
```

Edit C — chèn một dòng trống rồi đoạn sau ngay sau đoạn văn dưới `### Checkpoint: Confirm Task Breakdown Before Writing Task Files` (đoạn kết thúc bằng `Only proceed to write task files once the user confirms or adjusts the list.`):

```markdown
Beside each proposed task, list the epic scenario identifiers it will cover (its future `Covers:` line, see Tier C — BDD Automation below), so the user approves the scenario-to-task mapping together with the split.
```

Edit D — chèn một dòng trống rồi khối sau ngay sau dòng Rust bắt đầu bằng `- **Tier C (Acceptance & App Tests)**: Every Epic MUST include an explicit final integration task verifying composition roots, WASM bindings`:

```markdown
##### 🔗 Tier C — BDD Automation (All Platforms)
- Every scenario in `bdd_scenarios.en.md` MUST be covered by **at least one automated integration test**, whatever its tier tag. One test may cover several scenarios. There are no waivers: a scenario that cannot be automated is rewritten before Gate 2.
- The test carries the scenario identifier in its name, description or tag (`test_py_hp_01_...`, `testWidgets('[PY-HP-01] ...')`, ``@Test fun `PY-HP-01 ...`()``) and lives under one of the HLD's `Integration test roots`.
- Each identifier is assigned to at least one task through that task's `Covers:` line. The final Tier C task takes every identifier no earlier task covers.
```

Edit E — trong mục 8 của file task, chèn một dòng mới ngay sau dòng này:

```markdown
   Document this section under the markdown heading `### BDD SCENARIOS`.
```

Dòng mới:

```markdown
   Directly under that heading, write the line `Covers: <ID>, <ID>` naming the epic scenario identifiers from `bdd_scenarios.en.md` whose integration tests this task writes. Omit the line only when the task covers no epic scenario, for example a Tier B tooling task.
```

Edit F — cũng trong mục 8, thay `MUST map 1-to-1 or 1-to-N to an automated test case.` bằng `MUST map to at least one automated test case.`

Edit G — chèn khối sau, theo sau là một dòng trống, ngay trước dòng bắt đầu bằng `After the Epic Overview and all confirmed task files are written (or updated), commit them to git:` trong Step 3:

~~~~markdown
Before committing — and whether or not `auto_commit` is enabled — confirm that every epic scenario is assigned to a task. `SKILL_DIR` is the directory containing this `SKILL.md`:

```bash
python3 "$SKILL_DIR"/../dev-implementation/resources/scripts/check_bdd_traceability.py plan \
  --scenarios .devtool/epic/<epic_name>/bdd_scenarios.en.md \
  --tasks .devtool/epic/<epic_name>/task_*.md
```

It must exit 0. Exit 1 names the unassigned, unknown or malformed identifiers: fix the task files or the scenario documents and run it again. Pass the epic directory's task mirrors, never `.devtool/features/task_*.md`, which can hold other epics' tasks.
~~~~

Edit H — thêm hai dòng vào cuối `## Red Flags - STOP and Start Over`, sau `- Violating markdown lint standards (e.g. untagged code blocks, heading skips, trailing whitespace).`:

```markdown
- Writing a scenario in `bdd_scenarios.*.md` without a bracketed identifier, or a task that writes integration tests without its `Covers:` line.
- Committing the epic before `check_bdd_traceability.py plan` exits 0.
```

- [ ] **Bước 4: Chạy contract test và lint**

Chạy: `python3 scripts/test_lifecycle_document_contract.py && python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-designer/SKILL.md`
Kỳ vọng: `checked 11 lifecycle document contract surfaces`, rồi `checked 1 documents, 0 findings`.

- [ ] **Bước 5: Chạy lại scenario (GREEN)**

Dispatch một subagent mới khác với prompt của Bước 1, giữ nguyên. Kỳ vọng: các dòng scenario ở phần 1 bắt đầu bằng định danh trong ngoặc vuông; phần 2 có `Integration test roots:`; phần 3 có dòng `Covers:` nêu các định danh đó; phần 4 có `check_bdd_traceability.py plan` với các bản mirror `.devtool/epic/todo_export/task_*.md`. Nếu còn phần nào thiếu, siết lại câu chữ của chỗ sửa tương ứng và chạy lại cho tới khi cả bốn phần đạt.

- [ ] **Bước 6: Chạy verify.sh**

Chạy: `scripts/verify.sh`
Kỳ vọng: `PASS — safe to publish`.

- [ ] **Bước 7: Commit**

```bash
git add skills/dev-designer/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Require scenario IDs and Covers mapping in dev-designer" -m "- require bracketed scenario identifiers and integration test roots
- add the Covers: line to task files and the Gate 2 summary
- add Tier C BDD Automation and run the plan check before committing
- lock the new phrases in the lifecycle contract test"
```

### Task 3: dev-implementation thực thi mapping

**File:**

- Sửa: `skills/dev-implementation/SKILL.md`
- Sửa: `scripts/test_lifecycle_document_contract.py`

**Giao diện:**

- Dùng: CLI `tests` từ Task 1; `Covers:` và `Integration test roots:` từ Task 2.
- Cung cấp: thứ tự ở Phase 4 mà Task 4 dựa vào — kiểm tra truy vết đầy đủ, rồi `@quality_check`,
  trên cùng một SHA.

- [ ] **Bước 1: Scenario baseline (RED)**

Trước khi sửa, thay kết quả của `git rev-parse --show-toplevel` trong checkout đang thực thi vào chỗ `<ROOT>` bên dưới, và dùng cùng giá trị đó ở Bước 5. Sau đó dispatch một subagent general-purpose mới với prompt này và giữ lại câu trả lời:

```text
You are in the repository <ROOT>. Read
skills/dev-implementation/SKILL.md. Situation: epic slug todo-export, epic directory todo_export,
Python project. The HLD says "Integration test roots: tests/integration/". Task 3's BDD SCENARIOS
section says "Covers: TE-HP-01, TE-EC-02". Do not run anything. Reply with exactly three parts:
(a) every command that must succeed before task 3 may be marked done;
(b) every command, in order, between "all tasks are done" and presenting the Gate 5 summary;
(c) @quality_check returned an aggregated PASS on SHA abc123 and nothing else ran: is Gate 4 green?
```

Kỳ vọng ở baseline: (a) và (b) không nhắc tới `check_bdd_traceability.py`; (c) trả lời có. Ghi lại câu trả lời.

- [ ] **Bước 2: Khóa contract mới (test thất bại)**

Trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "aggregated verdict of **PASS**",
    ),
```

bằng:

```python
        "aggregated verdict of **PASS**",
        "check_bdd_traceability.py tests",
        "--ids",
    ),
```

Chạy: `python3 scripts/test_lifecycle_document_contract.py`
Kỳ vọng: exit 1 với `FAIL skills/dev-implementation/SKILL.md: missing check_bdd_traceability.py tests` và `missing --ids`.

- [ ] **Bước 3: Sửa skills/dev-implementation/SKILL.md**

Áp dụng tám chỗ sửa sau.

Edit A — trong khối có tiêu đề `MANDATORY 100% BDD-TO-TEST TRACEABILITY RULE (ZERO UNCOVERED SCENARIOS)`, thay dòng:

```markdown
   > 4. **Gate to Done**: A task CANNOT be marked `done` (`sync_task_status.py task <id> done`) unless 100% of its BDD scenarios have passing automated tests and verified outputs.
```

bằng:

~~~~markdown
   > 4. **BDD Automation (Tier C, all platforms)**: For every identifier on the task's `Covers:` line, the Integration Persona writes at least one integration test under the HLD's `Integration test roots`, carrying the identifier in the test's name, description or tag (`test_py_hp_01_...`, `testWidgets('[PY-HP-01] ...')`, ``@Test fun `PY-HP-01 ...`()``).
   > 5. **Gate to Done**: A task CANNOT be marked `done` (`sync_task_status.py task <id> done`) unless 100% of its BDD scenarios have passing automated tests and verified outputs, and — when the task has a `Covers:` line — this exits 0 when run in the epic worktree:
   >    ```bash
   >    python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
   >      --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
   >      --roots <Integration test roots from the HLD> \
   >      --ids <identifiers on the task's Covers: line>
   >    ```
~~~~

Edit B — trong `### Phase 4 — End of Epic Verification (@quality_check)`, thay đoạn:

```markdown
Once every task is `done`, resolve the candidate commit SHA (`git rev-parse HEAD`) and run the provider-based **`@quality_check`** orchestrator on the epic worktree before finishing the branch:
```

bằng:

~~~~markdown
Once every task is `done`, resolve the candidate commit SHA (`git rev-parse HEAD`) and, in the epic worktree, run the full BDD traceability check first:

```bash
python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py tests \
  --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
  --roots <Integration test roots from the HLD>
```

It must exit 0: every scenario in `bdd_scenarios.en.md` is covered by at least one integration test, and no test references a removed scenario. On exit 1 or 2, route back to Phase 2 and do not run `@quality_check` yet. Then run the provider-based **`@quality_check`** orchestrator on the same SHA before finishing the branch:
~~~~

Edit C — cũng trong phase đó, thay:

```markdown
3. Only an aggregated verdict of **PASS** bound to that exact SHA qualifies for Gate 4 `🟢 LGTM`.
```

bằng:

```markdown
3. Only an aggregated verdict of **PASS** bound to that exact SHA, on which the traceability check also exited 0, qualifies for Gate 4 `🟢 LGTM`.
```

Edit D — trong Phase 4.1, chèn một dòng mới ngay sau dòng này:

```markdown
   - The `@quality_check` verdict (3-Tier test results, 4 semantic audits, coverage matrix, Check 2 impact diff).
```

Dòng mới:

```markdown
   - The BDD traceability matrix printed by `check_bdd_traceability.py tests`.
```

Edit E — trong `## Quick Reference`, chèn một hàng mới ngay trước hàng bắt đầu bằng `| End-of-epic verification |`:

```markdown
| BDD traceability (per task with `--ids`, then full) | `check_bdd_traceability.py tests` | Same | Same |
```

Edit F — trong mục Red Flags, chèn hai dòng ngay sau dòng này:

```markdown
- Merging to `develop` without passing `@quality_check` (🟢 LGTM).
```

Các dòng mới:

```markdown
- Marking a task `done` while `check_bdd_traceability.py tests --ids <its Covers identifiers>` fails.
- Running `@quality_check` for Gate 4 before the full traceability check exits 0, or on a commit that check did not see.
```

Edit G — trong Phase 1 bước 3 (checkpoint Gate 3), chèn một dòng trống rồi một đoạn mới ngay sau dòng kết thúc bước đó:

```markdown
   `relation: behind`.
```

Đoạn mới, thụt lề để vẫn nằm trong bước 3:

~~~~markdown
   Before presenting the order, run the mapping check from dev-designer Step 3:

   ```bash
   python3 "$SKILL_DIR"/resources/scripts/check_bdd_traceability.py plan \
     --scenarios .devtool/epic/<epic_dir>/bdd_scenarios.en.md \
     --tasks .devtool/epic/<epic_dir>/task_*.md
   ```

   An epic designed before BDD traceability fails it. Add bracketed identifiers with a prefix no other epic uses to both `bdd_scenarios` variants, `Covers:` lines to the task files and their mirrors, and the `Integration test roots:` line to both HLD variants. Re-run the check until it exits 0, commit the result as `[EPIC_NAME] Add BDD scenario identifiers` before creating the worktree, and show the mapping in the checkpoint message.
~~~~

Edit H — trong Phase 2, thay:

```markdown
4. Only once both reviews pass, update status to `done`:
```

bằng:

```markdown
4. Only once both reviews pass and the task's Gate to Done traceability check (`check_bdd_traceability.py tests --ids`, run in the epic worktree) exits 0, update status to `done`:
```

- [ ] **Bước 4: Chạy contract test và lint**

Chạy: `python3 scripts/test_lifecycle_document_contract.py && python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-implementation/SKILL.md`
Kỳ vọng: `checked 11 lifecycle document contract surfaces`, rồi `checked 1 documents, 0 findings`.

- [ ] **Bước 5: Chạy lại scenario (GREEN)**

Dispatch một subagent mới khác với prompt của Bước 1, giữ nguyên. Kỳ vọng: (a) có `check_bdd_traceability.py tests` với `--ids TE-HP-01 TE-EC-02`; (b) chạy `check_bdd_traceability.py tests` đầy đủ trước `@quality_check`; (c) trả lời rằng chỉ `@quality_check` là chưa đủ — Phase 4 cần kiểm tra truy vết exit 0 trên `abc123` trước. Nếu phần nào không đạt, siết lại chỗ sửa tương ứng và chạy lại.

- [ ] **Bước 6: Chạy verify.sh**

Chạy: `scripts/verify.sh`
Kỳ vọng: `PASS — safe to publish`.

- [ ] **Bước 7: Commit**

```bash
git add skills/dev-implementation/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Enforce BDD traceability in dev-implementation" -m "- make the Integration persona write a test per Covers identifier
- gate each task's done flip on check_bdd_traceability.py tests --ids
- run the full traceability check before quality_check in Phase 4
- check the mapping at Gate 3 so epics designed earlier gain identifiers
- lock the new phrases in the lifecycle contract test"
```

### Task 4: Gate 4 của dev-lifecycle

**File:**

- Sửa: `skills/dev-lifecycle/SKILL.md`
- Sửa: `scripts/test_lifecycle_document_contract.py`

**Giao diện:**

- Dùng: thứ tự ở Phase 4 từ Task 3.
- Cung cấp: định nghĩa Gate 4 mà mọi lần chạy lifecycle sau này tuân theo.

- [ ] **Bước 1: Scenario baseline (RED)**

Trước khi sửa, thay kết quả của `git rev-parse --show-toplevel` trong checkout đang thực thi vào chỗ `<ROOT>` bên dưới, và dùng cùng giá trị đó ở Bước 5. Sau đó dispatch một subagent general-purpose mới với prompt này và giữ lại câu trả lời:

```text
You are in the repository <ROOT>. Read
skills/dev-lifecycle/SKILL.md. Every task of epic todo-export is done. @quality_check, invoked with
profile epic, base_ref develop and repository_sha abc123, returned an aggregated PASS. Nothing else
has run. May you grant Gate 4 and move to Gate 5? Answer yes or no first, then cite the rule you
relied on.
```

Kỳ vọng ở baseline: "yes", dẫn Gate 4 Machine Acceptance Criteria. Ghi lại câu trả lời.

- [ ] **Bước 2: Khóa contract mới (test thất bại)**

Trong `scripts/test_lifecycle_document_contract.py`, thay:

```python
        "FAIL > BLOCKED > PASS",
    ),
```

bằng:

```python
        "FAIL > BLOCKED > PASS",
        "check_bdd_traceability.py tests",
        "Granting Gate 4 without a passing traceability check",
    ),
```

Chạy: `python3 scripts/test_lifecycle_document_contract.py`
Kỳ vọng: exit 1 với hai dòng `FAIL skills/dev-lifecycle/SKILL.md: missing ...`.

- [ ] **Bước 3: Sửa skills/dev-lifecycle/SKILL.md**

Áp dụng chín chỗ sửa sau.

Edit A — trong sơ đồ mermaid, thay:

```text
    G4{"Gate 4<br/>quality_check 🟢 LGTM?"}
```

bằng:

```text
    G4{"Gate 4<br/>BDD traceability + quality_check 🟢 LGTM?"}
```

Edit B — trong `## The Five Gates`, thay hàng:

```markdown
| **4** | Quality LGTM & Check 2 | `quality_check` | `dev-implementation` Phase 4 | 🟢 report + coverage matrix + merge-ready branch |
```

bằng:

```markdown
| **4** | Quality LGTM & Check 2 | `check_bdd_traceability.py` + `quality_check` | `dev-implementation` Phase 4 | 🟢 report + coverage matrix + BDD traceability matrix + merge-ready branch |
```

Edit C — trong mục Stage 3, thay phần đầu của dòng Exit:

```markdown
**Exit (Gate 5):** `quality_check` reports 🟢 LGTM (Gate 4) AND
```

bằng:

```markdown
**Exit (Gate 5):** Gate 4 is 🟢 LGTM (BDD traceability and `quality_check`) AND
```

Edit D — thay câu dưới `**Gate 4 Machine Acceptance Criteria:**`:

```markdown
Gate 4 grants `🟢 LGTM` only when the provider-based quality orchestrator (`@quality_check`) returns an aggregated verdict of **PASS** bound to the exact candidate commit SHA (`git rev-parse HEAD`), evaluating all registered providers declared in `.agents/quality/check_quality.json` with profile `epic` against `<base_ref>`.
```

bằng:

```markdown
Gate 4 grants `🟢 LGTM` only when `check_bdd_traceability.py tests` exits 0 — every scenario in `bdd_scenarios.en.md` covered by at least one integration test, no test referencing a removed scenario — **and** the provider-based quality orchestrator (`@quality_check`) returns an aggregated verdict of **PASS**, both bound to the exact candidate commit SHA (`git rev-parse HEAD`), with `@quality_check` evaluating all registered providers declared in `.agents/quality/check_quality.json` with profile `epic` against `<base_ref>`.
```

Edit E — trong điều kiện 4 của Gate 4, thay `A 🟢 verdict belongs strictly to the SHA on which quality check ran.` bằng `A 🟢 verdict belongs strictly to the SHA on which the traceability check and quality check ran.`

Edit F — thay phần đầu của câu định tuyến:

```markdown
If `@quality_check` reports `FAIL` or `BLOCKED`, Gate 4 routes back
```

bằng:

```markdown
If the traceability check exits non-zero, or `@quality_check` reports `FAIL` or `BLOCKED`, Gate 4 routes back
```

Edit G — trong bảng When a Gate Fails, thay hàng:

```markdown
| 4 | Stage 3 Phase 2 — fix findings in the worktree, then re-run `quality_check` in full |
```

bằng:

```markdown
| 4 | Stage 3 Phase 2 — fix findings in the worktree, then re-run the traceability check and `quality_check` in full |
```

Edit H — trong mục Red Flags, chèn một dòng mới ngay sau dòng này:

```markdown
- Merging to `develop` without a 🟢 from Gate 4.
```

Dòng mới:

```markdown
- Granting Gate 4 without a passing traceability check on the same SHA.
```

Edit I — trong bảng Stage Skills, thay hàng:

```markdown
| 3 (verification) | `quality_check` | 4 |
```

bằng:

```markdown
| 3 (verification) | `quality_check` + `check_bdd_traceability.py` | 4 |
```

- [ ] **Bước 4: Chạy contract test, lint và render mermaid**

Chạy: `python3 scripts/test_lifecycle_document_contract.py && python3 skills/doc_quality_check/resources/scripts/check_document.py skills/dev-lifecycle/SKILL.md`
Kỳ vọng: `checked 11 lifecycle document contract surfaces`, rồi `checked 1 documents, 0 findings`.

Render sơ đồ đã sửa:

```bash
MMD_DIR=$(mktemp -d)
awk '/^```mermaid/{f=1;next} /^```/{f=0} f' skills/dev-lifecycle/SKILL.md > "$MMD_DIR/lifecycle.mmd"
npx -y @mermaid-js/mermaid-cli -i "$MMD_DIR/lifecycle.mmd" -o "$MMD_DIR/lifecycle.svg" && ls -l "$MMD_DIR/lifecycle.svg"
```

Kỳ vọng: file SVG tồn tại và lệnh exit 0. Nếu `npx` không tải được package (không có mạng), ghi lại điều đó trong báo cáo của task và dựa vào lint mermaid của `check_document.py` ở trên.

- [ ] **Bước 5: Chạy lại scenario (GREEN)**

Dispatch một subagent mới khác với prompt của Bước 1, giữ nguyên. Kỳ vọng: "no", dẫn ra rằng Gate 4 còn yêu cầu `check_bdd_traceability.py tests` exit 0 trên `abc123`. Nếu nó vẫn trả lời yes, siết lại Edit D và chạy lại.

- [ ] **Bước 6: Chạy verify.sh**

Chạy: `scripts/verify.sh`
Kỳ vọng: `PASS — safe to publish`.

- [ ] **Bước 7: Commit**

```bash
git add skills/dev-lifecycle/SKILL.md scripts/test_lifecycle_document_contract.py
git commit -m "[SKILLS] Make BDD traceability part of Gate 4" -m "- require check_bdd_traceability.py tests exit 0 alongside quality_check PASS on one SHA
- update the diagram, gate table, failure routing, red flags and stage skills
- lock the new phrases in the lifecycle contract test"
```

## Kiểm tra cuối cùng

- [ ] Chạy `scripts/verify.sh` thêm một lần trên commit cuối. Kỳ vọng: `PASS — safe to publish`.
- [ ] Chạy `python3 -m unittest skills/dev-implementation/resources/scripts/test_check_bdd_traceability.py`. Kỳ vọng: `Ran 24 tests`, `OK`.
- [ ] Đối chiếu từng yêu cầu của spec với diff: định danh và thư mục test (Task 2 Edit A và B), `Covers:` và bản tóm tắt Gate 2 (Edit C và E), Tier C BDD Automation (Edit D), cách diễn đạt "at least one" (Edit F), `plan` trước commit (Edit G), `tests` theo từng task và ở Phase 4 cùng kiểm tra mapping ở Gate 3 cho epic cũ (Task 3), Gate 4 (Task 4).
- [ ] Quality gate: gọi `@quality_check` theo yêu cầu của `CRITICAL_RULES`. Repo này không có `.agents/quality/check_quality.json`, nên kỳ vọng `BLOCKED`; báo cáo đúng như vậy. Release gate của chính kit là `scripts/verify.sh` (xem `CLAUDE.md`), và nó phải pass.
- [ ] Không push. Báo cáo bốn commit và chờ developer.
