# Principal Review Loop Procedure

Principal Review is a cross-model review of an epic's architecture and task designs against the source repository before implementation begins. It catches grounded misunderstandings, missing contracts, and scope regressions while fixing them in documents is cheap.

## Procedure

1. **End of Stage 2 — Provider/Model Priority Choice (No Packaging Yet)**:
   Once Gate 2 passes and readiness checks (`check_epic_readiness.py <epic_dir>`) succeed (design docs & tasks committed when `auto_commit: true`, Gate 2 recorded, and `resume_context.py --state --epic <epic_slug> --status "Stage 2: Ready for Principal Review"` saved), do **NOT** run `package_epic.py` or create `handoff.md` yet.
   Read `.devtool/review_config.json` (auto-seeded from `DEFAULT_REVIEW_CONFIG` with `provider_priority: ["claude", "codex", "kiro", "agy"]` and `max_rounds: 3`), display each provider's configured `model` and `thinking_level` (`Claude CLI`, `Codex CLI`, `Kiro CLI`, `Antigravity CLI`), stop calling tools, and ask the developer for the **provider/model priority order** for `/principal-review`:

   > Gate 2 passed and Stage 2 design is saved (`/save-context`). What provider/model priority order should `/principal-review` use?
   > - **Default priority**: `Claude -> Codex -> Kiro -> Argon` (showing configured models/thinking levels from `.devtool/review_config.json`).
   > - **Custom priority / model override**: e.g., `Codex -> Claude -> Kiro -> Argon` or a specific `--cli <provider> --model <model>`.

   Add the recommendation when it applies:
   - When the epic was designed by a different or fast model (judged from the HLD's `Author` line or the developer's word), cross-model review is strongly recommended before committing to implementation. Recommend using each CLI's strongest reasoning model (for Antigravity CLI: `agy --model "Gemini 4 Argon (Medium)"`; for Kiro CLI: `claude-opus-5.5` or `gpt-5.6-sol`).
   - Never choose for the developer. Always wait for explicit priority/model confirmation.

2. **Automatic `/principal-review` Invocation**:
   As soon as the developer confirms or provides the provider/model priority order, persist any custom priority/model override in `.devtool/review_config.json` (or pass `--provider-priority <list>` / `--cli <provider> --model <model>`), and **automatically invoke `d3nexus:principal-review`**.

3. **Run Principal Review & Auto-Convergence Loop (Max 3 Rounds, No Mid-Loop Packaging)**:
   Round 1 runs Full Scope; Round 2 runs Delta Verification; Round 3 runs Blocker-Only Convergence Mode:
   ```bash
   python3 "$SKILL_DIR"/resources/scripts/run_external_review.py run --kind principal --epic-dir <epic_dir> --base <base_branch> [--auto-quota [--provider-priority <order>] | --cli <claude|codex|kiro|agy>]
   ```
   - A readiness FAIL prints the precondition banner (`handoff.md` is NOT required before packaging): the CLI is never invoked. Fix the named failures as an epic revision and re-run.
   - On completion of each round, commit the recorded round in `.devtool/epic/<epic_dir>/principal_review.md`:
     ```bash
     git commit -m "[<EPIC_NAME>] Record Principal Review round <n>"
     ```
   - Run triage and evaluate `## Auto-Triage Gate`:
     ```bash
     python3 "$SKILL_DIR"/resources/scripts/run_external_review.py triage --kind principal --epic-dir <epic_dir>
     ```
     Verify every finding against source at the round's SHA and approved Spec/HLD per [document-triage.md](../../principal-review/references/document-triage.md). In **both** interactive and autonomous modes, auto-apply verified `Valid` fixes and advance cleanly to Round `N+1` without pausing — stop calling tools and escalate to the Human Architect **only** on `CRITICAL_CONFLICT`, `Debatable` trade-offs, `CIRCUIT_BREAKER_HALT (SHARED_CONTRACT_CONFLICT)`, `CIRCUIT_BREAKER_HALT (FIX_LOOP)`, or `CIRCUIT_BREAKER_HALT (MAX_ROUNDS_CRITICAL_REMAINING)`.
   - If the round produces revisions (`AUTO_FIX_ELIGIBLE`, `AUTO_PASS_FINAL_*` sweep, or escalated fixes confirmed by the developer):
     - Commit the document revisions first:
       ```bash
       git commit -m "[<EPIC_NAME>] Revise epic after Principal Review round <n>"
       ```
     - Record decisions in `.devtool/epic/<epic_dir>/principal_review.md` using the revision commit SHA (`fixed in <sha>` or `dismissed: <developer's rationale>`) and commit:
       ```bash
       git commit -m "[<EPIC_NAME>] Record Principal Review decisions for round <n>"
       ```
     - Run `python3 skills/dev-implementation/resources/scripts/check_epic_readiness.py <epic_dir>` and **automatically proceed to the next review round** (`Round n+1`). Do **NOT** run `package_epic.py` mid-loop.

4. **Post-Review Packaging, `/save-context` & Implementation Prompt**:
   Once Principal Review converges (`AUTO_PASS_CLEAN`, `AUTO_PASS_FINAL_MINOR_SWEEP`, or `AUTO_PASS_FINAL_SWEEP` after any final sweep commits):
   - Run packaging (initial package creates `handoff.md`; pass `--revise --reason "Revise after Principal Review"` only if `handoff.md` already exists):
     ```bash
     python3 skills/dev-implementation/resources/scripts/package_epic.py <epic_dir> [--revise --reason "Revise after Principal Review"]
     ```
   - Commit if `auto_commit: true`: `[<EPIC_NAME>] Package epic for handoff`.
   - Persist `/save-context` and emit/print the implementation prompt and `handoff.md` path:
     ```bash
     python3 scripts/resume_context.py --state --epic <epic_slug> --status "Stage 2: Packaged & Ready"
     python3 scripts/resume_context.py --emit-prompt implement --epic <epic_slug>
     ```

5. **Post-Package Launch Decision (`Triển khai (tự động)` vs `Dừng lại`)**:
   Stop calling tools and present the two options with the printed implementation prompt above:
   > `/principal-review` passed and `<epic_slug>` is packaged (`handoff.md`). How do you want to proceed?
   > 1. **Triển khai (tự động)** — automatically enter Stage 3 (`d3nexus:dev-implementation`, automated Gate 3 & TDD).
   > 2. **Dừng lại** — Dừng lại ở đây để tôi lấy prompt cho một AI Agents khác triển khai.

   - If the developer picks **1. Triển khai (tự động)**:
     Verify `python3 "$SKILL_DIR"/resources/scripts/run_external_review.py check --kind principal --epic-dir <epic_dir>` exits 0 and confirm via `git log -1 --format=%s -- .devtool/epic/<epic_dir>` that no un-packaged epic commit landed after `[<EPIC_NAME>] Package epic for handoff` (re-run `package_epic.py <epic_dir> --revise` if needed), then **automatically invoke `d3nexus:dev-implementation`**.
   - If the developer picks **2. Dừng lại** (or anything else):
     Stop cleanly here; keep the printed implementation prompt and `handoff.md` path for another AI Agent.

## Guidelines and References

For detailed guidelines on how to verify reviewer claims, assess validity, and record decisions, refer to [review-triage.md](../../dev-implementation/references/review-triage.md).
