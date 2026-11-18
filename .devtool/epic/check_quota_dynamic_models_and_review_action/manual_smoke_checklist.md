# Manual Smoke Walkthrough Checklist: Check Quota Dynamic Models And Review Action

> [!NOTE]
> 2-minute manual sanity check extracted automatically from canonical BDD Happy Path scenarios.
> Run through these 3–5 high-leverage user journeys before final sign-off.

| Step | Target (URL / CLI) | Action | Observable Outcome |
| :---: | :--- | :--- | :--- |
| 1 | `/usage` | `fetch_quota_for_profile("nguyenhieu000690")` and `format_profile_for_dashboard("nguyenhieu000690", result)` execute | `groupModels["gemini"]` equals `["Gemini 4 Carbon", "Gemini 4 Argon", "Gemini 4 Hydrogen", "Orchestrator (Carbon)", "Orchestrator (Argon)", "Gemini 3.8 Flash"]` and `groupModels["claude"]` equals `["Claude Sonnet 4.6", "Claude Opus 4.6", "GPT-OSS 120B"]` |
| 2 | `/usage` | `fetch_quota_for_profile("danhdue")` and `format_profile_for_dashboard("danhdue", result)` execute | `capabilities["argonMode"]` equals `"separate"`, `capabilities["tier"]` equals `"PRO"`, `capabilities["hasOrchestrator"]` is `True`, top-level `tier` equals `"PRO"`, and `groupModels["claude"]` contains `"Claude Opus 5.5"`, `"Claude Sonnet 5.5"`, and `"GPT-OSS 120B"` |
| 3 | `skills/check-quota/resources/dashboard/quota_dashboard.html` | headless Chrome loads the dashboard page and opens the profile info modal for "nguyenhieu000690" | the card header displays dynamic badges matching `capabilities["badges"]` (`Carbon`, `Argon`, `Orchestrator`) and zero uncaught browser console errors occur |
| 4 | `skills/dev-implementation/references/external-review-prompt.md` | `run_external_review.py` renders `review_results.md` via `render_round()`, validates it via `check()`, and prints triage tables via `top_risk_findings_section()` and `triage()` stdout | every row in `review_results.md` contains strictly 5 pipe-delimited columns (`\| # \| Severity \| Location \| Problem \| Decision \|`) passing `check()` with exit code `0` |
| 5 | `TasksServer` | `GET /api/epic/history?repo=demo&epic=duet_harmonize&round_cross=1` and `round_cross=2` are fetched and rendered in `tasks_dashboard.html` under headless Chrome | finding `#1` in Round 1 carries `"Enforce script > doc > sidecar precedence in ingest"` in `proposed_action`, finding `#1` in Round 2 carries `"add early return"` in `proposed_action`, and both render in the `PROPOSED ACTION` cell of the Cross-Model Review table with zero `"—"` placeholder |

## Sign-off
- [ ] All steps completed manually with expected outcomes verified.
- **Reviewer / Date:** __________________
