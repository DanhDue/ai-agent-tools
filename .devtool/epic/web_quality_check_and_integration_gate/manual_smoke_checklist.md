# Manual Smoke Walkthrough Checklist: Web Quality Check And Integration Gate

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `d3nexus:web-quality-check` | Gate 4 invokes d3nexus:web-quality-check with profile epic | the provider executes type_check, lint, and test_e2e via Playwright headless |
| 2 | `web-quality-check` | web-quality-check executes the type_check capability | the TypeScript compiler validates all JavaScript files without emitting errors |
| 3 | CLI / Workspace Root | the test simulates user navigation, button clicks, and network mocking via page.route() | the page renders without emitting any console.error or uncaught exceptions |
| 4 | CLI / Workspace Root | the smoke generator parses primary BDD Happy Path scenarios | it emits .devtool/epic/<epic_dir>/manual_smoke_checklist.md before Gate 4 validation |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
