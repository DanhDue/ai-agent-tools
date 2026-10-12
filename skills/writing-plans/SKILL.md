---
name: writing-plans
description: Use when you have a spec or requirements for a multi-step task, before touching code
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well. Crucially, plans must define bite-sized steps that not only cover unit TDD, but also **Integration Test Planning & Boundary Edge Cases** (empty states, errors, timeouts, race conditions). For any Web or UI deliverables, the plan MUST include a dedicated **Live Web Browser Verification** step using `browser_subagent` to verify actual rendering, interaction, and visual correctness before considering the work complete.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**Context:** If working in an isolated worktree, it should have been created via the `d3nexus:using-git-worktrees` skill at execution time.

**Save plans as a synchronized pair:**

- English, canonical: `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.en.md`
- Vietnamese: `docs/superpowers/plans/YYYY-MM-DD-<feature-name>.vi.md`
- (User preferences for plan location override this default)

Both variants MUST have the same structure, facts, task ordering, code samples, and a linked table
of contents covering every `##` and `### Task` section. Write and update English first, then
synchronize Vietnamese. `task_*.md` files created by other workflows remain English-only; that
exception does not apply to an implementation plan.

Both variants MUST strictly satisfy **Markdown & Diagram Lint Standards**:
- **Markdown Lint**: Single H1 title, no skipped heading levels, space after `#`, no trailing punctuation in headings, language tags on all fenced code blocks (no bare fences), and formatting hygiene (no trailing whitespace, no hard tabs).
- **Mermaid Standards**: ALWAYS use `flowchart TD/LR` (NEVER legacy `graph TD/LR`), double-quote node labels containing special characters/parentheses/brackets/colons (e.g. `node["Text (Details)"]`), use clean alphanumeric IDs, and avoid trailing semicolons.
- **Graphviz (DOT) Standards**: Follow semantic shapes (`diamond` for decisions `?`, `box` for actions, `plaintext` for commands, `ellipse` for states, `octagon` for warnings, `doublecircle` for start/complete), semicolons on every statement, and quoted labels.

## Mandatory Integration & Edge Case Testing

Unit tests in isolation are necessary but insufficient to guarantee that a feature works end-to-end. When writing implementation plans:

1. **Map Critical Use Cases to Integration Tests**:
   - If the feature introduces or modifies user flows, APIs, or database interactions, the plan MUST include an explicit integration test step or dedicated integration task that exercises the end-to-end contract.
   - Test full data paths: UI/Action -> Controller/Reducer -> Store/Repository -> Mock/Live Backend -> UI State update.

2. **Exhaustive Edge Case Verification**:
   For every feature, the plan MUST explicitly define test steps covering:
   - **Boundary inputs**: Null, undefined, empty strings/collections, zero, negative, maximum limits.
   - **Error states & resilience**: Network timeouts, 4xx/5xx HTTP errors, malformed payloads, storage failures.
   - **Concurrency & race conditions**: Rapid consecutive clicks/toggles, cancellation, debouncing, state transitions.

3. **Live Web Browser Verification (For Web / UI Deliverables)**:
   - Component unit tests and DOM mocks do not prove that a web page actually renders or behaves correctly in a real browser engine.
   - Any task that creates or modifies web pages, UI components, styling, or browser interactions MUST include a **Live Browser Verification** step.
   - Specify the exact operational steps:
     1. Build and launch the dev or preview server (e.g. `npm run dev` or `npx astro preview --port 4324`).
     2. Dispatch `browser_subagent` to open the target URL, click interactive elements, type input, and assert expected DOM text and states.
     3. Record browser interaction session as a WebP video artifact and capture screenshot artifacts.
     4. Verify visual hierarchy, CSS layout, responsiveness, and console logs (zero unexpected errors).

4. **100% BDD & Edge Case Traceability**:
   - Every use case and boundary edge case identified in the spec MUST map to an explicit automated test step (unit test step for Tier A, integration test step for Tier C).
   - Never write an edge case requirement without an accompanying executable test step.

## Reviewing a Written Plan

Before handing a plan to an executor, dispatch a reviewer subagent using
[`plan-document-reviewer-prompt.md`](plan-document-reviewer-prompt.md). A plan that reads well to
its author and is missing a step reads exactly the same either way. Review the canonical `.en.md`
plan, apply every content fix to it, and then synchronize the `.vi.md` translation.

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during `dev-brainstorming`. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

## Task Right-Sizing

A task is the smallest unit that carries its own test cycle and is worth a
fresh reviewer's gate. When drawing task boundaries: fold setup,
configuration, scaffolding, and documentation steps into the task whose
deliverable needs them; split only where a reviewer could meaningfully
reject one task while approving its neighbor. Each task ends with an
independently testable deliverable.

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use d3nexus:subagent-driven-development (recommended) or d3nexus:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Spec:** [path to the spec/design doc this plan implements — the plan
argues from the spec, so the spec travels with it; executors read both]

## Table of Contents

[A linked entry for every major section and every `### Task` heading]

## Global Constraints

[The spec's project-wide requirements — version floors, dependency limits,
naming and copy rules, platform requirements — one line each, with exact
values copied verbatim from the spec. Every task's requirements implicitly
include this section.]

---
```

## Task Structure

````markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Interfaces:**
- Consumes: [what this task uses from earlier tasks — exact signatures]
- Produces: [what later tasks rely on — exact function names, parameter
  and return types. A task's implementer sees only their own task; this
  block is how they learn the names and types neighboring tasks use.]

- [ ] **Step 1: Write the failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Integration & Edge Case Test (if touching workflows/data/APIs)**

Write & run integration test exercising multi-component flow and boundary edge cases (empty payload, timeout, error fallback):
Run: `npm test tests/integration/test_flow.test.ts` (or `pytest tests/integration/...`)
Expected: PASS with 100% boundary coverage

- [ ] **Step 6: Live Web Browser Verification (for Web / UI Tasks)**

Launch preview/dev server and dispatch `browser_subagent` to verify live behavior:
1. Open URL `http://localhost:<port>/<route>`
2. Test user interaction flow, click controls, verify state transitions
3. Save video recording (`.webp`) and capture screenshot artifact
4. Assert expected DOM text and zero console exceptions

- [ ] **Step 7: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "[SCOPE] Add specific feature" -m "- <what this step changed>"
```
````

## No Placeholders

Every step must contain the actual content an engineer needs. These are **plan failures** — never write them:
- `TBD`, `TODO`, "implement later", "fill in details"
- "Add appropriate error handling" / "add validation" / "handle edge cases"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — the engineer may be reading tasks out of order)
- Steps that describe what to do without showing how (code blocks required for code steps)
- References to types, functions, or methods not defined in any task

## Self-Review

After writing the complete plan, look at the spec with fresh eyes and check the canonical English
plan against it. This is a checklist you run yourself — not a subagent dispatch.

**1. Spec coverage:** Skim each section/requirement in the spec. Can you point to a task that implements it? List any gaps.

**2. Placeholder scan:** Search your plan for red flags — any of the patterns from the "No Placeholders" section above. Fix them.

**3. Type consistency:** Do the types, method signatures, and property names you used in later tasks match what you defined in earlier tasks? A function called `clearLayers()` in Task 3 but `clearFullLayers()` in Task 7 is a bug.

**4. Markdown & Diagram lint check:** Does the plan strictly adhere to markdown lint standards (all code blocks tagged with language, no skipped headings, clean formatting)? Do any embedded Mermaid diagrams use modern `flowchart` instead of legacy `graph`, with quoted special-character labels? Do any DOT diagrams follow standard semantic shapes and statement semicolons?

**5. Integration & Edge Case Verification Check:** Does the plan specify tests for boundary edge cases (empty states, errors, race conditions)? If the plan touches Web/UI code, does it mandate Live Browser Verification using `browser_subagent` with visual recording and screenshots?

If you find issues, fix them inline. No need to re-review — just fix and move on. If you find a spec requirement with no task, add the task.

Synchronize the Vietnamese plan after all English fixes, then verify both files mechanically:

```bash
python3 skills/doc_quality_check/resources/scripts/check_document.py \
  --require-toc --require-bilingual \
  docs/superpowers/plans/YYYY-MM-DD-<feature-name>.en.md \
  docs/superpowers/plans/YYYY-MM-DD-<feature-name>.vi.md
```

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/superpowers/plans/<filename>.en.md` and
`docs/superpowers/plans/<filename>.vi.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?"**

**If Subagent-Driven chosen:**
- **REQUIRED SUB-SKILL:** Use d3nexus:subagent-driven-development
- Fresh subagent per task + two-stage review

**If Inline Execution chosen:**
- **REQUIRED SUB-SKILL:** Use d3nexus:executing-plans
- Batch execution with checkpoints for review
