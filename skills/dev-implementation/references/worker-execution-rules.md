# Worker Execution Rules

Read when: you are a Role 2.3 `task-implementer`, or you dispatch one, and need the test-health rules, the Tri-Persona model or the anti-rationalization table.

## Test Assertion Health, Anti-Bloat & Tiered Execution

Never assert only inside `if path.exists()`; always assert `found > 0`. Enforce:
- **Mandatory Parametrization**: Never copy-paste `def test_*` functions across input variations; consolidate into `@pytest.mark.parametrize` (or table tests).
- **No Trivial Boilerplate Tests**: Ban tests asserting only Python language features, Pydantic defaults, or trivial getters/setters; verify distinct Spec/HLD contracts.
- **Fixture Scope Discipline**: Read-only fixtures (JSON snapshots, AST trees, mock servers, headless browsers) MUST use `scope="module"` or `scope="session"`, never `scope="function"`.
- **Tier 1 (Task & Fix Rounds)**: Static checks + scoped parallel files (`uv run pytest <changed_test_files> -n auto --timeout=30 -q --tb=short`); never `tests/e2e` or repo-wide pytest. **Tier 2 (Pre-Gate)**: `uv run pytest --ignore=tests/e2e -m "not slow and not acceptance and not live_llm" -n auto --dist loadscope --timeout=30 -q --tb=short`. **Tier 3 (Final Gate Convergence Only)**: Tier 2 + session-scoped `tests/e2e` + `audit_epic.py` / `@quality_check`.

## Tri-Persona Subagent Execution Model

Operate across the 3-Tier Testing Standard:
1. **Expert QA (Red Team)**: Authors adversarial BDD scenarios (`HP`, `EC`, `ST`, `AR`, `FR`) split cleanly between `[Tier A - Unit]` and `[Tier C - Integration]`.
2. **Principal Engineer (TDD Master — Tier A)**: Executes RED failing test -> minimal GREEN code -> REFACTOR/lint/strict types in task files only.
3. **System Integration & E2E Engineer (Tier C)**: Authors integration/browser suites (`integration_test/`, `*FlowTest.kt`, `App/Tests`, `tests/e2e/`, `tests/integration/`) exercising real DI, navigation, and persistence.

## Anti-Rationalization and Doubt-Driven Verification

Reject rationalizations that cut testing corners:
- **"Node test is sufficient for web UI"**: REJECTED. Node tests prove only pure data logic. Web defects occur in DOM queries and CSS rendering. Tier C requires headless Playwright with Zero-Console-Error watchdog.
- **"Mock data in stub is enough"**: REJECTED. Method stubs bypass JSON deserialization and network interceptors. Wire fixtures from `shared-contracts/` are mandatory.
- **"Red console errors are harmless warnings"**: REJECTED. Zero-Console-Error rule fails Gate 4 on any browser console error.
- **"Cannot launch simulator, unit test instead"**: REJECTED. Mobile Tier C requires Subcutaneous testing with real DI and in-memory persistence.
- **"HTML ported from mockup, selectors match"**: REJECTED. Tier C2 UI tests MUST assert `getComputedStyle` and `getBoundingClientRect` properties against the Visual Companion design.

**Doubt-Driven Verification Protocol**:
Before claiming done on any task: `CLAIM` Tier C coverage -> `EXTRACT` test reports -> `DOUBT` mock isolation -> `RECONCILE` real headless/subcutaneous tests.
