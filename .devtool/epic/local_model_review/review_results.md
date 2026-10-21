# Cross-Model Review: local_model_review

## Round 1

- **Date**: 2026-10-21T11:28:36Z
- **SHA**: 55edbafd018091585cb22c27f172797e389e2e86
- **Base**: main
- **CLI**: ollama
- **Model**: qwen38-reviewer
- **Status**: no verdict
- **Verdict**: CHANGES REQUIRED
- **Passes**: 8
- **Context**: 65536

| # | Severity | Location | Problem | Decision |
|---|----------|----------|---------|----------|
| 1 | Important | skills/dev-implementation/resources/scripts/test_local_review.py:13 | `from test_run_external_review import ReviewCase` contradicts the binding decision "`test_local_review.py` imports only `run_external_review` in this task" and couples the new suite to a protected path the task explicitly avoided ("in a new file because that suite is a protected path") | dismissed: developer: "Có thể dismiss" — reusing the fixture by import leaves the protected suite unchanged; copying it would duplicate about 60 lines |
| 2 | Minor | skills/dev-implementation/resources/scripts/test_local_review.py:22 | the task's "Target test coverage threshold: the rendered prompt is asserted for all six rule titles" is not met; only three titles are asserted, so rules 2–4 could drop from review-rules.md undetected by this test | fixed in 78a09c8 |
| 3 | Important | skills/dev-implementation/resources/scripts/local_review.py:Slice dataclass hunk | `sections: tuple[str, ...] = ()` and `parts: tuple[Part, ...] = ()` are public fields, contradicting the binding decision "Further fields are private." (should be `_sections`/`_parts`) | dismissed: developer: "Có thể dismiss" — "private" in the HLD means outside the frozen contract; no caller outside local_review.py uses these fields |
| 4 | Minor | skills/dev-implementation/resources/scripts/local_review.py:probe() and chat() hunks | incidental resource-cleanup edits (`error.close()`, `with error:`) go beyond the slicing half this task describes |  |
| 5 | Minor | skills/dev-implementation/resources/scripts/test_local_review.py:index 324d960..fde294f | the task file marks both Allowed files "(new)" but the diff shows pre-existing content (prior index hashes, existing TransportTest/SharedRulesTest) |  |
| 6 | Minor | skills/dev-implementation/references/local-review-prompt.md:not-shown | external-review-prompt.md is not shown, so the decision that the verdict block keeps "exactly the grammar" of it cannot be confirmed |  |
| 7 | Minor | skills/dev-implementation/references/local-review-checklists.md:not-shown | the spec's Pass Checklists section in 2026-10-21-local-model-review-design.en.md is not shown, so "verbatim in meaning" cannot be confirmed |  |

Raw output:

```text
### Pass 1: task_1_share_verification_rules

## Analysis

1. **GREEN rows vs. Definition of Done.** V2 runs `python3 -m unittest ... test_local_review.py -k test_lmr_hp_02` and backs "LMR-HP-02 is covered by `test_lmr_hp_02_shared_rules_reach_the_external_prompt` and passes in the JUnit report. (V2, V6)"; V3 backs "The existing runner suite passes unchanged. (V3)" with evidence showing `Ran 31 tests ... OK`; V4/V5 back "Lint and strict type checking report zero issues on the touched Python files. (V4, V5)" with `All checks passed!` and `Success: no issues found in 2 source files`; V6 produces the named JUnit report (`--junitxml build/test-results/task_1.xml`, exit 0, `OK`). Each command exercises the item it backs at task scope.

2. **RED row fails for the missing behaviour.** V1 exited 1 with `AssertionError: 'No Reconstructed Logic' not found in ...`, and the rendered prompt in the traceback still carries the old inline rules 1–4 under `## Verification Hierarchy & Process Rules` with no `$rules` substitution — i.e. it fails precisely because the new shared rules were not yet inserted, which is the behaviour this task adds. Valid RED.

3. **Production code invoked, not rebuilt.** The test file shows `from test_run_external_review import ReviewCase`, `self.install("claude")` and `code, _, _ = self.run_review(cli="claude")`; the RED traceback contains a fully rendered prompt with dynamic content (commit SHAs, audit output, `git diff --stat`), which only the real `run_external_review` runner can produce, so no production logic is reconstructed locally. However, the import source deviates from the binding decision "`test_local_review.py` imports only `run_external_review` in this task" — flagged under item 6.

4. **Vacuous assertions.** None: `self.assertIn(title, prompt)` over the three titles and `self.assertNotIn("$rules", prompt)` are all falsifiable (the RED run proves the first class fails pre-implementation), and they are made against `prompt = self.stdin.read_text(encoding="utf-8")`, the genuine stdin saved by the fake `claude` during a real runner invocation, not a mock the test configured to pass.

5. **Given/When/Then mapping.** Given ("a throwaway epic repository and a fake claude on PATH that saves its stdin") maps to `self.install("claude")` plus the fixture's repo (the RED traceback shows `.devtool/epic/demo` artefacts); When ("run_external_review.py run --cli claude records a round") maps to `code, _, _ = self.run_review(cli="claude")` with `self.assertEqual(code, 0)`; Then maps to the `for title in ("Task-Level vs. Gate 4 Workspace Scope", "No Reconstructed Logic", "Immutable Real Artifacts"):` loop; And maps to `self.assertNotIn("$rules", prompt)`. Full GWT coverage of LMR-HP-02.

6. **Decisions Already Made.** The constant `RULES = SCRIPTS.parent.parent / "references" / "review-rules.md"`, the kwarg `rules=RULES.read_text(encoding="utf-8").strip(),`, the verbatim move (removed prompt lines match added `review-rules.md` lines 1–11 exactly, heading kept, body replaced by `$rules`, no H1 in the fragment), and the three ruff fixes (`old mode 100644 / new mode 100755`, `re.MULTILINE`, `datetime.now(UTC)`) all match. Two deviations: (a) the new test's `from test_run_external_review import ReviewCase` contradicts the binding decision "`test_local_review.py` imports only `run_external_review` in this task" and couples the new suite to a protected path the task deliberately avoided ("in a new file because that suite is a protected path"); (b) "Target test coverage threshold: the rendered prompt is asserted for all six rule titles" is not met — only three titles are asserted, though the binding scenario requires exactly those three. Rules 5–6 wording matches the canonical Phase 4 rule text verbatim, so the unshown `SKILL.md` is not needed to judge it.

7. **Platform rules.** Added production lines in `run_external_review.py` are confined to an import (`from datetime import UTC, datetime`), a path constant, a regex flag, a template kwarg and a timezone call — no layer boundary inversion, feature isolation breach, or forbidden dependency; the test file's only non-stdlib import is the sibling test fixture, which is a test-coupling issue already captured under item 6 rather than a platform layer violation.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/test_local_review.py:13 — `from test_run_external_review import ReviewCase` contradicts the binding decision "`test_local_review.py` imports only `run_external_review` in this task" and couples the new suite to a protected path the task explicitly avoided ("in a new file because that suite is a protected path")
[Minor] skills/dev-implementation/resources/scripts/test_local_review.py:22 — the task's "Target test coverage threshold: the rendered prompt is asserted for all six rule titles" is not met; only three titles are asserted, so rules 2–4 could drop from review-rules.md undetected by this test

### Pass 2: task_2_ollama_transport

")[2].strip()`. rpartition on absent separator returns ("", "", content), so [2] is content → stripped ✓. With separator, [2] is the part after the last occurrence ✓.
- `local_review.py` never imports run_external_review.py ✓ — imports are json, os, urllib.error, urllib.request, dataclasses, typing. The task's Requirement Analysis says "Standard library only (urllib.request, json, dataclasses, math, os)". The implementation imports urllib.error additionally (needed for HTTPError) and typing.Any. `math` is listed but not imported — that's fine, the list is what's allowed, not required. urllib.error is stdlib; typing is stdlib. No violation.

Wait — the module docstring says "transport, review slices, and the prompt base" — but this file only contains the transport half. The task says "Create local_review.py with the transport half of the HLD contract". The docstring mentions "review slices, and the prompt base" which are presumably added by later tasks (Task 6 wires it; other tasks add slices/prompt). Since the file is new in this commit and later tasks will extend it, the docstring describing the eventual module is acceptable. Not a finding. Hmm, but is it misleading? It's a docstring for the module as a whole; fine.

**7. Does any added line violate a loaded platform rule?**

Platform rules (Python): Layer Boundary Inversion, Feature Module Isolation, Application & Infrastructure Direction, Forbidden Dependencies. This is a scripts directory (`skills/dev-implementation/resources/scripts/`), not a layered package. The module imports only stdlib. No network/async runtime inside pure domain models — this is an infrastructure-ish script that legitimately does HTTP; the rule example is "no network or async runtime package inside pure domain models" — local_review.py is not a pure domain model, it's the transport itself. No sibling feature imports. So no violation.

Now, other things to check:

- The test file diff shows it was modified (existing). It imports `from test_run_external_review import ReviewCase` — that's pre-existing context (SharedRulesTest). The diff header shows index 8ae31c5..324d960, so the file existed. The task's Allowed files lists test_local_review.py as "(new)" but the diff shows modification. Hmm — is this a contradiction? The task file says `test_local_review.py (new)`. But the diff shows it as an existing file being modified. Wait, let me re-read: "Allowed files: - skills/dev-implementation/resources/scripts/local_review.py (new) - skills/dev-implementation/resources/scripts/test_local_review.py (new)". The diff for test_local_review.py shows `index 8ae31c5..324d960 100755` — not a new file. So the task file claimed it was new, but it already existed (presumably created by Task 1 with SharedRulesTest). Is this a finding? The "Stop and Report If" says "A command, path, symbol or anchor named in this task does not match the repository." The path matches; the "(new)" annotation is slightly off. But the audit (Gate 4) passed and scope check passed (SCOPE row: exit None PASS). The change is within Allowed files regardless of new-vs-modified. This is at most a Minor documentation nit in the task file, not in the code. Should I flag it? The finding format requires `<artefact>` to be a path shown in the user message and location a line/hunk/row. I could say [Minor] task file: Allowed files — test_local_review.py is annotated "(new)" but the diff shows it as an existing file modified by this commit. Hmm, but is that within my remit? The task file is part of the slice. It's a minor inconsistency that doesn't affect correctness. Actually wait — could this indicate the test file was created in a previous task (Task 1) and this task extends it? That's normal workflow; the "(new)" annotation is just wrong. Minor at most. Let me consider whether to include. The instructions say report missing items as Minor with "not-shown" format only for things not shown. This isn't missing — it's a visible inconsistency. I think a Minor finding is fair, but let me weigh: does it break anything? No. Gate 4 scope passed. I'll mention in analysis (item 6 or 1) and possibly raise as Minor. Hmm, actually, let me reconsider — the RED evidence shows "Ran 7 tests" at RED time, and V2 GREEN also "Ran 7 tests", V5 "Ran 8 tests". At RED, 7 tests in TransportTest? The diff adds 7 test methods to TransportTest (5 lmr + test_chat_sends... + test_host_comes...). Yes, 7. And V5 runs the whole file: 7 + 1 SharedRulesTest = 8. Consistent.

- ResourceWarning in V2 output: `ResourceWarning: Implicitly cleaning up <HTTPError 500: 'Internal Server Error'>`. This comes from the HTTPError object in chat's except branch not being closed. In CPython, HTTPError is a file-like object (it wraps the response); reading it doesn't close it. The warning appears once in V2 output. Tests pass. This is a genuine minor defect: unclosed resource. I'll raise as Minor with location at the HTTPError branch of chat in local_review.py.

Let me double check: in `chat`, `except urllib.error.HTTPError as error: body = error.read().decode(...)`. HTTPError supports .read() and .close(). Not closing → ResourceWarning on GC. Yes. Minor.

- The fake server's `reply` method catches OSError and passes — "the client gave up first, as in a timeout test". That's fine for a fake.

- `closed_port()` binds then closes the socket, returning the port. There's a tiny race (port could be reused), but on 127.0.0.1 with ephemeral ports it's standard practice and the scenario explicitly asks for "a closed local port". Fine.

- Timeout test: `self.fake.delay = 3` then chat with timeout 1. The fake sleeps 3s before replying; client times out at 1s. This makes the test take ~1s (plus the 500 case). V2 ran 7 tests in 4.567s — consistent (RED took 23.8s, probably due to retries or... hmm, RED took 23.8s with errors=7; maybe connection attempts to closed port with default timeout? probe's version call to closed port fails fast with ConnectionRefused. The 23.8s in RED is odd but not my concern — RED passed its expectation).

Wait, actually one more check on the timeout path: when the client times out during `urlopen` (before response), Python raises `URLError(TimeoutError('timed out'))`? Or `TimeoutError` directly? In Python 3.10+, `socket.timeout` is `TimeoutError`. `urllib.request.urlopen` → `http.client.HTTPConnection` → on timeout during connect/read, raises `socket.timeout` (i.e., TimeoutError), which urllib wraps in URLError in some paths (`_open` catches OSError? let me recall). Actually `urlopen` does not wrap all OSErrors; `AbstractHTTPHandler.do_open` catches `OSError` and raises `URLError(err)`. Hmm: in `do_open`, the try block around `h.request(...)` etc. catches `OSError as err` and raises `URLError(err)`. So a timeout during request would be URLError(TimeoutError). But a timeout during `response.read()` (after headers received) would propagate as raw TimeoutError. The fake sleeps before sending any response, so the timeout happens during read of response headers → that's inside `do_open`'s try? The `h.getresponse()` call is inside do_open's try block, so it'd be wrapped in URLError. But the implementation handles both cases anyway. The test passed with "timed out after 1 seconds", so whichever path fired, it was handled. ✓.

- Check `probe`'s version step: `urllib.request.urlopen(f"{host}/api/version", timeout=timeout).close()`. If the server returns HTTP 404 on /api/version, urlopen raises HTTPError (OSError subclass) → "not reachable". Per decision, that's exactly what's specified ("any URLError or OSError raises ... not reachable"). ✓.

- `post()` is a helper not in the decisions list — fine, internal.

- mypy --strict passed on both files, so typing is clean.

- Ruff passed.

Now, scenario coverage check: "Each ID must be covered by at least one passing integration test that carries the ID in its name." Test names: `test_lmr_hp_06_modelfile_governs_the_context` — contains "lmr_hp_06" (lowercase). The ID is LMR-HP-06. Convention here is lowercase with underscores; the DoD says "a `test_lmr_*` method". V5 ran 8 tests OK, so all pass. ✓.

DoD bullet: "All five covered scenario have a test_lmr_* method in TransportTest and pass in the JUnit report. (V2, V5)" — V5's output shows "Ran 8 tests ... OK" but doesn't show individual names or the junit xml content. The evidence tail doesn't display the XML. Is that a gap? The Expect is "exit 0; results build/test-results/task_2.xml". Exit 0 with 8 tests OK. The XML file's existence is implied by the command succeeding (the runner writes it). I can't see the XML content, but the command's expectation was met as recorded. Per rules, missing items → Minor "not-shown" only if I need something not shown. Do I need the XML to verify each scenario test passed? V2 already shows TransportTest passing (7 tests OK), which includes all five scenario tests. So the JUnit report is corroborated. I don't think I need to raise a not-shown finding; the evidence is sufficient. Hmm, but strictly, "pass in the JUnit report" — V5 exit 0 with 8 tests OK means all passed in that run which produced the report. Sufficient.

Now let me also verify the HP-06 Given: "/api/show reports 'num_ctx 65536' in its parameters". The test sets parameters to `'num_ctx                        65536\nstop                           "

### Pass 3: task_3_review_slices_and_budget

## Analysis

**1. GREEN rows vs Definition of Done.** V2's command `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k SliceTest` runs exactly the class the DoD bullet "All four covered scenarios have a `test_lmr_*` method in `SliceTest` and pass in the JUnit report. (V2, V5)" names, and the diff shows all four methods — `def test_lmr_hp_04_a_task_slice_carries_everything_the_reviewer_may_judge(self) -> None:`, `test_lmr_ec_03_...`, `test_lmr_ec_04_...`, `test_lmr_ec_06_...` — inside `SliceTest`. V5's tail "Ran 13 tests in 5.965s" / "OK" backs the JUnit-report half, and the bullet "Tests run against throwaway Git repositories only. (V2)" is exercised because `EpicRepoCase.setUp` builds `directory = tempfile.TemporaryDirectory()` and `git(self.root, "init", "-q", "-b", "main")`. V3/V4 back the lint/type bullet with "All checks passed!" and "Success: no issues found in 2 source files".

**2. RED row.** V1 failed with `AttributeError: module 'local_review' has no attribute 'build_slices'` and "FAILED (errors=5)" — every error is the missing slicing API itself, so the RED fails for the missing behaviour, not for a fixture or environment problem.

**3. Production code invoked, not rebuilt.** The tests call the Allowed-file symbols directly: `return local_review.build_slices(self.root, "demo", self.base, sha, "audit-output", "results-output", EXCLUDES)` and `fitted = local_review.fit(task, full - 2000)`. The only local helpers are fixture builders (`EpicRepoCase`) and `def section_of(text: str, heading: str) -> str:`, which merely parses rendered output for assertions; no slicing, fitting or token logic is reconstructed.

**4. Vacuity.** The key assertions can fail: `self.assertEqual([line for line in TAIL if line in evidence], TAIL[25:])` pins exactly the last 15 of 40 tail lines; `self.assertEqual(fitted.omitted, ("big.py",))` plus `self.assertLessEqual(local_review.estimate_tokens(user), full - 2000)` pin both the drop choice and the budget contract; `self.assertIn("but the budget is 1000; raise --num-ctx", str(caught.exception))` pins the error text. No assertion is always-true or made on a self-configured mock.

**5. Given/When/Then mapping.** LMR-HP-04's "evidence verify row has 40 output_tail lines" maps to `TAIL = [f"tail-{number:02d}" for number in range(1, 41)]` and the act `task, epic = self.slices()` / `user = local_review.render_user(task)`, with all four Then-clauses asserted (heading order, `self.assertNotIn("DEMO-HP-02", scenarios)`, tail-15 equality, `self.assertNotIn(".devtool/", diff)`). LMR-EC-03's 9000/300-byte Given maps to `"b = 1\n" * 1500` / `"s = 1\n" * 50`. LMR-EC-04's "task file alone estimates to more than 1000 tokens" maps to `self.write(f"{EPIC}/task_1_demo.md", TASK_FILE + "x" * 4000 + "\n")` with `local_review.fit(self.slices()[0], 1000)`. LMR-EC-06's two-commit Given maps to `self.task_commit(...)` then `self.write("src/legacy.py", ...)` / `self.commit("Legacy work")`, and the Then maps to `task, epic = self.slices()` plus the "## Commits outside tasks" assertions.

**6. Decisions Already Made.** Constants match exactly: `PROMPT_SHARE = 0.6`, `BYTES_PER_TOKEN = 3`, `TAIL_LINES = 15`, and `return math.ceil(len(text.encode("utf-8")) / BYTES_PER_TOKEN)`; the error string matches `raise --num-ctx`; heading orders, drop orders (largest diff first via `ranks = {path: rank for rank, (path, _) in enumerate(sorted(diffs, key=lambda item: -len(item[1])))}`, epic outside→spec→HLD) and the evidence-commit rule all conform. One deviation: the decision says of `Slice` "Further fields are private.", but the diff adds public fields `sections: tuple[str, ...] = ()` and `parts: tuple[Part, ...] = ()` with no underscore prefix, widening the approved API surface.

**7. Platform rules.** The added imports `from check_bdd_traceability import FENCE, LEADING_TAG, SCENARIO_LINE, covers_of` and `from task_contract import git_run` reuse the declared read-only context within the same scripts package; no domain layer depends outward, no sibling-feature internals are imported, and no network/async runtime enters pure logic. No loaded Python governance rule is violated by added lines.

Verdict: CHANGES REQUIRED
[Important] skills/dev-implementation/resources/scripts/local_review.py:Slice dataclass hunk — `sections: tuple[str, ...] = ()` and `parts: tuple[Part, ...] = ()` are public fields, contradicting the binding decision "Further fields are private." (should be `_sections`/`_parts`)
[Minor] skills/dev-implementation/resources/scripts/local_review.py:probe() and chat() hunks — incidental resource-cleanup edits (`error.close()`, `with error:`) go beyond the slicing half this task describes
[Minor] skills/dev-implementation/resources/scripts/test_local_review.py:index 324d960..fde294f — the task file marks both Allowed files "(new)" but the diff shows pre-existing content (prior index hashes, existing TransportTest/SharedRulesTest)

### Pass 4: task_4_local_review_prompt_base

## Analysis

**1. GREEN rows vs Definition of Done.** `V2` runs `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k PromptBaseTest` and the evidence shows `Ran 3 tests in 0.002s` / `OK`, which exercises the bullet `All three covered scenarios have a test_lmr_* method in PromptBaseTest and pass in the JUnit report. (V2, V5)` — `PromptBaseTest` contains exactly `test_lmr_hp_05_*`, `test_lmr_hp_07_*`, `test_lmr_ec_05_*`. `V5` produced the named report with `Ran 16 tests in 5.751s` / `OK`, and the rule-existence bullet `(V2)` is backed by `test_lmr_hp_07_every_quoted_platform_rule_exists_in_the_kit` running inside that same GREEN command. `V3` (`All checks passed!`) and `V4` (`Success: no issues found in 2 source files`) back the lint/type bullet `(V3, V4)`.

**2. RED row fails for the missing behaviour.** The `V1` evidence shows `FileNotFoundError: [Errno 2] No such file or directory: '.../skills/dev-implementation/references/local-review-platforms.md'` and `FAILED (errors=3)`. The missing file is one of this task's own new deliverables, so all three tests fail precisely because the prompt base does not exist yet — a legitimate RED for the missing behaviour, not an environmental or harness fault.

**3. Tests invoke production code.** The test module does `import local_review` and calls the real symbols: `system = local_review.render_system(task)`, `found = local_review.platform_sections(["app/lib/a.dart", "native/src/b.rs"])`, and `local_review.Slice(...)`. The added `from task_contract import section` mirrors production's own `from task_contract import git_run, section` and is used only to extract expected text from the reference files; no selection, dedup, ordering or template-substitution logic is rebuilt in the test.

**4. Vacuous assertions.** None found. `test_lmr_hp_07` guards against empty collections with `self.assertGreater(len(ids), 0, platform)` and `self.assertEqual(len(names), count, platform)` (counts 5 and 4), then checks each ID against real audit rows via `self.assertTrue(any(f"**{rule}**" in row for row in rows), f"{rule} is not a Blocker row")` where `rows` comes from the genuine `SKILLS / name / "SKILL.md"` files, and each policy name via `self.assertIn(f"**{name}**", source)`. `test_lmr_hp_05` catches failed substitution with `for placeholder in ("$rules", "$platform_rules", "$checklist"):` / `self.assertNotIn(placeholder, system)`, and asserts the full Flutter section text and both checklist bodies are present.

**5. Given/When/Then mapping.** LMR-HP-05: Given → `task = local_review.Slice("task_1_demo", "task", ("lib/a.dart",), ())`; When → `system = local_review.render_system(task)`; Then → the expected-tuple assert plus the epic-slice branch `epic = local_review.render_system(local_review.Slice("epic", "epic", (), ()))` with `self.assertNotIn("## Task pass", epic)`. LMR-HP-07: Given → `self.platforms()`; When → `ids = RULE_ID.findall(section(self.platforms(), platform) or "")` and `names = BOLD.findall(...)`; Then → the Blocker-row and governance-source membership asserts. LMR-EC-05: `self.assertEqual([text.splitlines()[0] for text in found], ["## Flutter", "## Rust"])`, `self.assertEqual(local_review.platform_sections(["README.md", "web/x.ts"]), [])`, the `.kt`/`.kts` dedup check, and `self.assertIn("No platform rules apply to this slice.", system)`. The heading-level "exactly" check is complemented by LMR-HP-07's per-section ID/name content guards, so section bodies are not untested.

**6. Decisions Already Made.** The frozen constant matches verbatim: `EXTENSIONS = {".dart": "Flutter", ".kt": "Android", ".kts": "Android",` / `.swift": "iOS", ".rs": "Rust", ".py": "Python"}`. Signatures and behaviour match: `def platform_sections(paths: Iterable[str]) -> list[str]:` with `PLATFORM_ORDER = ("Flutter", "Android", "iOS", "Rust", "Python")` and set-based dedup; `render_system` uses `Template(...).safe_substitute(rules=..., platform_rules=..., checklist=...)` with `rules=RULES.read_text(encoding="utf-8").strip()`, `platform_rules="\n\n".join(platform_sections(slice_.paths)) or "No platform rules apply to this slice."`, and `checklist = "Task pass" if slice_.kind == "task" else "Epic pass"` with heading. The template holds role/hard limits, the workflow primer (Gates 1–4, task-file sections, `run_task_checks.py` evidence, `HP`/`EC`/`ST`/`AR`/`FR` scenario IDs, `Fix` commits and protected paths), then `$rules`, `$platform_rules`, `$checklist`, then the output format with the worked example — in the decided order. Two fidelity decisions cannot be confirmed because their sources are not shown (verdict-grammar identity with `external-review-prompt.md`; checklists "verbatim in meaning" against the spec's Pass Checklists section); these are reported as Minor below, and no test contradicts them.

**7. Platform rules on added lines.** The added production lines import only stdlib (`from collections.abc import Iterable`, `from string import Template`) plus same-package kit modules (`task_contract`), so no Layer Boundary Inversion, Feature Module Isolation breach, direction violation or Forbidden Dependency is introduced; this is tooling script code, not a domain layer. `V3` and `V4` confirm zero lint and strict-type issues on both added files.

Verdict: PASS
[Minor] skills/dev-implementation/references/local-review-prompt.md:not-shown — external-review-prompt.md is not shown, so the decision that the verdict block keeps "exactly the grammar" of it cannot be confirmed
[Minor] skills/dev-implementation/references/local-review-checklists.md:not-shown — the spec's Pass Checklists section in 2026-10-21-local-model-review-design.en.md is not shown, so "verbatim in meaning" cannot be confirmed

### Pass 5: task_5_record_round_from_passes


--- error ---
HTTP 500: {"error":"an error was encountered while running the model: unexpected EOF"}
```
