# Review Triage

Every review round — Claude CLI, Codex CLI, Antigravity CLI or a local Ollama model — is triaged with the developer
before anyone acts on it. A reviewer's finding is a claim to check, not an instruction: some are
real, some are false positives, and some only say that a file was not shown.

## Steps

1. Print the skeleton for the latest round:

   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --epic-dir <epic_dir>
   ```

2. Read `## Passes`. A pass with verdict `none` or an error never reviewed its slice; say so in Next
   Steps rather than reading its silence as approval.
3. Verify every row of `## Findings` against the code at the round's SHA, with the discipline of
   `d3nexus:receiving-code-review`: open the file and line it names, check the claim, and never accept
   or reject it on the reviewer's word alone.
4. Fill the three empty columns of each row:
   - **Assessment** — `Valid` (the claim holds), `Debatable` (it holds by the letter, not clearly by
     intent), `False positive` (it does not hold), or `Not shown` (the reviewer could not see what it
     needed).
   - **Evidence** — the file and line you checked, with a short quote.
   - **Proposed action** — `fix`, `dismiss: <reason>`, or `none` for a Minor finding that needs no
     change.
5. Read `## Round Comparison` and `## Since Round <n>`. Fewer Critical and Important findings, and
   fixed findings that are not re-reported, show the fixes worked. A fixed finding re-reported at the
   same path says `check the fix`: look at it again before deciding.
6. Replace the Next Steps line with numbered actions: the Fix commits, the decisions to record, and,
   when blocking findings will be fixed, a confirmation round whose triage measures the improvement.
7. Evaluate the `## Auto-Triage Gate` section emitted by `run_external_review.py triage` (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, `AUTO_FIX_ELIGIBLE`, `AUTO_PASS_FINAL_SWEEP`, or `CIRCUIT_BREAKER_HALT` for `SHARED_CONTRACT_CONFLICT`, `FIX_LOOP`, or `MAX_ROUNDS_CRITICAL_REMAINING`) and present the filled triage. For Stage 2 `/principal-review`, follow [document-triage.md](../../principal-review/references/document-triage.md): in both interactive and autonomous modes, auto-apply verified `Valid` document fixes and advance to Round `N+1`, halting only on `CRITICAL_CONFLICT`, `Debatable` trade-offs, or `CIRCUIT_BREAKER_HALT`. For Stage 3 code reviews (`/cross-model-review`), in interactive mode (or on any `CIRCUIT_BREAKER_HALT` / `Debatable` finding), stop and wait until the developer decides each finding; in autonomous `/dev-lifecycle` mode, `AUTO_PASS_FINAL_MINOR_SWEEP` (and `AUTO_PASS_FINAL_SWEEP` at Round 3 when `0 Critical` findings remain) fixes valid items once, runs full Gate 4 machine acceptance green, and completes without re-invoking the reviewer, while `AUTO_FIX_ELIGIBLE` applies verified `Valid` fixes, validates via **scoped tests only** (fast static checks and explicitly targeted unit tests covering modified modules; repo-wide pytest and Playwright E2E suites forbidden), and triggers the next convergence round (up to max 3 rounds, guarded by the 4 Anti-Fix-Loop Prompt Strategies: Exhaustive Round 1 Pass, Universal Anti-Ping-Pong Guardrail, Previously Fixed Locations Registry, and Diff-Hunk Isolation). Full Gate 4 is reserved strictly for the Final Convergence Gate.

## ⚡ Remediation Loop & Test Execution Protocol (HARD CONSTRAINTS)

To prevent multi-minute test hangs, token waste, and incomplete/evasive fixes during review-remediation cycles, both the Orchestrator and Fixer/Implementer agents MUST strictly obey the following rules:

1. **SCOPED TESTS ONLY DURING INTERMEDIATE FIX ROUNDS (Round 1, Round 2...):**
   - While fixing findings in intermediate rounds, run **ONLY** fast static/architecture checks (`ruff`, `mypy`, `lint-imports`, AST invariants) and **explicitly targeted test files** that directly cover the modified modules:
     `uv run pytest <explicit_test_file_1.py> <explicit_test_file_2.py>`
   - **STRICTLY FORBIDDEN IN INTERMEDIATE ROUNDS:** Do NOT run repo-wide `pytest` discoveries (even with `-m "not slow..."`), do NOT run `tests/e2e/` browser suites, and do NOT pipe unfiltered repo-wide test runs into `| tail` (which hides hanging browser/SSE sockets).
   - **FINAL GATE ONLY:** Reserve the full regression suite, Playwright E2E browser harness, and full `quality_check` artifact regeneration strictly for the **Final Convergence Gate** after all code findings are resolved.

2. **ZERO-TOLERANCE ANTI-EVASION RULES (NO SHORTCUT FIXES):**
   - **No Dependency/Artifact Deletion:** Never resolve an unlocked dependency finding by removing the required package from `pyproject.toml`, and never resolve a stale quality report finding by simply deleting the report without regenerating it. If `uv.lock` is blocked by task scope rules, explicitly add `uv.lock` to the task's `Allowed files` and run `uv lock`.
   - **No Synthesized Fallback Fixtures:** When a finding flags fake/generated test data, do not replace it with another runtime generator. Load genuine immutable fixtures from disk and fail hard when missing.
   - **Browser Binary Synchronization:** Whenever `playwright` is added or upgraded in `pyproject.toml` / `uv.lock`, immediately run `uv run playwright install chromium` before invoking any browser E2E check.

## After the developer decides

- Make each fix as its own commit titled `[EPIC_NAME] Fix <what>`.
- Write each Decision cell in `review_results.md`: `fixed in <sha>`, or `dismissed: <reason>` in the
  developer's own words. Never write a dismissal the developer did not give.
- Commit the decisions: `[<EPIC_NAME>] Record review decisions for round <n>`.
- **Intermediate rounds**: validate fixes using **scoped tests only** (`uv run pytest <explicit_test_file.py>` and fast static checks; no repo-wide pytest, no `tests/e2e/`).
- **Final convergence only**: re-run Phase 4 / Gate 4 in full on the candidate SHA.
