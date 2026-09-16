# Changelog

Notable changes per release. Starts at 1.1.0 — earlier versions were released without notes.

Versions follow `MAJOR.MINOR.PATCH`. A bump is **required** for any release: `claude plugin update`
compares the version in `.claude-plugin/plugin.json` and does nothing when it is unchanged, leaving
every installed machine on the old cached copy.

---

## 1.1.1 — 2026-09-17

Strengthens the `quality_check` master governance skill by making Tier B zero-tolerance explicit and introducing Tier C2 Native Build Smoke Testing.

### Changed — quality_check

- **Tier B Zero-Tolerance Enforcement**: Formally documents that all analyzer errors, compiler warnings, module boundary leaks, formatting issues, and license headers must be 100% resolved (0 errors, 0 warnings).
- **Tier C2 Native Build Smoke Gate**: Adds an explicit binary compilation check (`flutter build apk --debug`, `./gradlew assembleDebug`, `xcodebuild build`) to Tier C before merging, closing the blind spot where headless tests pass but native binary assembly fails.
- **Reporting**: Updates the 3-Tier Automated Test Results table to track Tier C1 (Integration Flows) and Tier C2 (Native Build Smoke Gate) separately.

---

## 1.1.0 — 2026-09-16

Adds the **Lean Product Lifecycle Suite**: four skills covering upstream product discovery, for
deciding *what to build and for whom* before `epic-lifecycle` takes over the engineering. Also adds
a reusable harness for measuring whether a skill changes agent behaviour at all.

### Added — Lean Product Lifecycle Suite

Four skills implementing Dan Olsen's Lean Product Process, grounded in *The Lean Product Playbook*
(Wiley, 2015).

| Skill | Covers | Produces |
|---|---|---|
| `lean-product-lifecycle` | Orchestration, three human gates, five guardrails | routes the other three |
| `lean-market-discovery` | Steps 1–2: target customer, underserved needs | `01_problem_space_spec.md` |
| `lean-value-strategy` | Step 3: Kano classification, competitive grid | `02_value_proposition_spec.md` |
| `lean-mvp-scoping` | Step 4: chunking, ROI, MVP candidate grid | `03_mvp_feature_backlog.md` |

Artefacts land in `.devtool/product/<slug>/`. The Gate 3 backlog is consumed directly by
`epic-designer`.

Process steps 5 (build an MVP test) and 6 (test with customers) are **not implemented**. The
orchestrator says so at Gate 3 rather than implying the journey is complete.

### Added — skill ablation harness (`evals/`)

Measures whether a skill changes behaviour, rather than whether an agent holding it can recite it.
Each scenario runs with the skill, without it, and optionally with the pre-correction rules; a third
agent grades all arms blind against a rubric that cites the book rather than the skill.

Five reusable cases, a protocol, and pre-correction fixtures. Not wired into `verify.sh` — each run
costs real agent invocations, so it belongs at release time or after a skill is edited.

### Added — source-fidelity regression gate

`scripts/check_source_fidelity.py`, wired into `scripts/verify.sh` as step 7. Fails the build if any
of six corrected errors reappears in `skills/lean-*/` or `docs/books/`. Every rule was confirmed to
fire on an injected regression.

### Fixed — six errors in the documentation this suite was derived from

The suite was originally specified from three LLM-written summaries in `docs/books/`, not from the
book. Reading the primary source found six behaviour-changing errors that had propagated through
four layers of artefacts. All are corrected in `docs/books/` at source, with provenance headers
naming the book as the authority. Evidence with the author's wording:
`.devtool/epic/lean_product_suite/source_fidelity_review.md`.

| Was | Is |
|---|---|
| "MVP = ROI cells 1–3" | All must-haves enter v1 regardless of ROI rank |
| Guardrail 1 forbids solution-space talk | Capture, convert, park — Olsen's rule is *separate and alternate* |
| 6-layer PMF Pyramid | 5-layer Pyramid **and** a separate 6-step Process; UX is the top layer |
| Gate 1 bar `OS >= 10` | `> 15` attractive · `10–15` marginal · `< 10` unattractive |
| Importance and Satisfaction both 1–10 | 5-point unipolar / 7-point bipolar, normalized before use |
| 3×3 grid is the ROI method | Numeric ROI is primary; the grid is Olsen's declared fallback |

"Cupcake MVP" was also removed as an attribution error — Figure 7.1 is adapted from **Jussi
Pasanen**; the cupcake metaphor is Brandon Schauer's and does not appear in the book.

### Known limitations

Stated because they change how much to trust this suite, not as boilerplate.

- **No measured advantage over an unaided agent.** Two scenarios were ablated with a blind judge.
  Both scored **0 delta** — a competent agent without the skill reached the same decisions. The
  process layer (gates, artefacts, session resumption) is untested and is where the value plausibly
  sits, but that is a belief, not a measurement.
- **One correction has measured value, one does not.** Against an arm carrying the pre-correction
  rules: the `OS >= 10` and scale corrections scored **+3**; the `cells 1–3` correction scored
  **0**, because the agent overrode the broken rule unprompted.
- **`lean-value-strategy` and `lean-product-lifecycle` have never been ablated.** Three of five
  cases are unrun.
- **n = 1 per arm.** `evals/protocol.md` requires three runs before a result is cited as settled.
- Results and full reasoning: `evals/results/2026-09-16-baseline/report.md`.

### Notes

- Skill count 42 → 47.
- `evals/` must stay outside `check_source_fidelity.py`'s glob — its fixtures deliberately contain
  the corrected errors.
