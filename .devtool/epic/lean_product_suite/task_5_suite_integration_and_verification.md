---
id: "task_5_suite_integration_and_verification"
status: "todo"
priority: "high"
assignee: null
epic: "lean_product_suite"
dueDate: null
created: "2026-09-16T16:34:00Z"
modified: "2026-09-16T16:34:00Z"
completedAt: null
labels: ["integration", "plugin-sync", "tdd-verification", "quality-gate"]
order: "e1"
---

# Task 5: End-to-End Suite Integration, Plugin Sync, & TDD Verification

Epic: [lean_product_suite](lean_product_suite.en.md)

## Requirement Analysis
To operationalize the newly created skills across the entire IDE and development environment, this task handles the plugin registration, global synchronization to `~/.gemini/config/plugins/d3nexus/skills/`, documentation updates, and rigorous TDD scenario verification following `writing-skills`.

This task requires:
1. **Plugin & Docs Registration**:
   - Update `README.md` to document the Lean Product Lifecycle Suite in the skills catalog.
   - Update `skills/find-skills/` or plugin manifests if applicable.
2. **Plugin Synchronization**:
   - Sync the newly created skills (`lean-product-lifecycle`, `lean-market-discovery`, `lean-value-strategy`, `lean-mvp-scoping`) and their `references/` and `templates/` to `~/.gemini/config/plugins/d3nexus/skills/`.
3. **TDD Scenario Verification (Pressure Testing)**:
   - Verify **Scenario 1 (The Solution-Obsessed Founder)**: Ensure Guardrail 1 intercepts tech stack/coding discussions during Stage 1.
   - Verify **Scenario 2 (The Me-Too Clone)**: Ensure the Noriaki Kano persona rejects value propositions lacking Delighters at Gate 2.
   - Verify **Scenario 3 (The 30-Feature MVP Bloat)**: Ensure the 3x3 ROI matrix enforces strict cutoff, pushing non-v1 stories to roadmap backlog.
4. **Quality & Formatting Check**:
   - Run quality checks on all markdown files, links, and YAML frontmatter.

## Relevant Files & Context Pointers
- `plugin.json`: Plugin manifest.
- `README.md`: Workspace skills documentation.
- `skills/writing-skills/SKILL.md`: TDD mapping for agent skills.
- `.devtool/epic/lean_product_suite/bdd_scenarios.md`: Scenarios 1.1, 2.1, 2.2, 2.3, 3.1, 3.2, 4.1, 5.1.

## Acceptance Criteria
- `README.md` documents the 4 new Lean Product skills with triggering descriptions.
- All 4 skills exist and are synchronized in both `skills/` and `~/.gemini/config/plugins/d3nexus/skills/`.
- All 3 baseline TDD pressure test scenarios pass with zero guardrail breaches.
- Quality report indicates clean markdown, valid YAML frontmatter, and resolving links.
