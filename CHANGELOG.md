# Changelog

Notable changes per release. Starts at 1.1.0 — earlier versions were released without notes.

Versions follow `MAJOR.MINOR.PATCH`. A bump is **required** for any release: `claude plugin update`
compares the version in `.claude-plugin/plugin.json` and does nothing when it is unchanged, leaving
every installed machine on the old cached copy.

---

## 1.4.2 — 2026-10-03

Makes bilingual, navigable design documentation a verified contract across the development and
document lifecycles.

### Added

- **Bilingual lifecycle artefacts**: specs, HLD/overview documents, BDD scenario documents,
  non-epic implementation plans, document outlines, and published documents now require a
  canonical English `.en.md` file and a synchronized Vietnamese `.vi.md` translation.
- **Complete table-of-contents contract** for every lifecycle document regardless of length.
  Implementation plans must also link every `### Task` heading.
- **Lifecycle document regression tests** covering missing translations, omitted variants,
  heading-structure drift, incomplete tables of contents, short documents, and decorated ToC
  headings.

### Changed

- **`dev-designer`** now generates bilingual HLD and BDD scenario pairs; `writing-plans` generates
  bilingual implementation-plan pairs. Kanban `task_*.md` files remain English-only.
- **`dev-brainstorming`, `doc-brainstorming`, `doc-designer`, and `doc-implementation`** now create,
  synchronize, and mechanically verify both language variants before their approval gates.
- **`dev-lifecycle` and `doc-lifecycle`** explicitly carry the bilingual and ToC requirements in
  their handoff contracts and red flags.
- **`doc_quality_check`** now requires both variants in the same run, checks heading-shape parity,
  verifies complete ToC coverage, and audits semantic translation parity.
- **`dev-implementation`** consumes `bdd_scenarios.en.md` as the canonical behavioral contract.

### Verification

- `scripts/verify.sh` now runs the lifecycle document contract suite as a release gate.

---

## 1.4.1 — 2026-10-02

Adds a mandatory critical rule prohibiting unauthorized remote git push operations and improves worktree bootstrapping resilience.

### Added

- **Git push operations guard** in `rules/CRITICAL_RULES.md`, strictly prohibiting agents from running `git push` to remote repositories without explicit user permission or confirmation.

### Fixed

- **Worktree bootstrap script** (`bootstrap_worktree.sh`) now falls back to locating `copy_secure_files.sh` directly within the installed plugin directory when not vendored in `.agents/`.
- **Kanban task status synchronizer** (`sync_task_status.py`) falls back to `sanitize_slug(epic_dir)` to prevent lookup failures during task synchronization.

---

## 1.4.0 — 2026-09-28

Adds Codex distribution while keeping one shared skill library for Codex, Claude Code, and
Antigravity.

### Added

- **Codex plugin manifest** at `.codex-plugin/plugin.json`, with discovery metadata, starter
  prompts, and the existing `skills/` directory as its skill source.
- **Codex installation and update instructions** in the README, including the distinction
  between GitHub marketplace distribution and submission to OpenAI's public Plugins Directory.
- **Codex tool mapping** in `using-superpowers`, covering skill loading, file and shell tools,
  optional subagents, and explicit rule loading through a project's `AGENTS.md`.

### Changed

- The shared `.agents/plugins/marketplace.json` uses a local source path at the repository root,
  so Codex resolves the plugin from the checked-out marketplace.
- Project scaffolding includes Codex installation commands and explicit instructions to read
  rules from the project or installed plugin. The bootstrap hook directs agents to the runtime
  tool mapping instead of assuming Claude's `Skill` tool exists.
- `release.sh` requires dated release notes and a newer version, releases from `main`, and keeps
  the root, Claude, and Codex manifests plus Claude marketplace versions synchronized. It
  verifies again after the bump and prints Codex refresh commands.
- `verify.sh` checks Codex metadata, shared skill paths, marketplace identity, version agreement,
  dated release notes, and README anchors in addition to the existing checks.

### Fixed

- Claude marketplace metadata still advertised `1.3.0` after the plugin reached `1.3.1`.
- The shared marketplace described `./` as a remote URL instead of a local plugin path.

### Upgrading

Install in Codex:

```bash
codex plugin marketplace add DanhDue/ai-agent-tools
codex plugin add d3nexus@danhdue-agent-tools
```

Start a new thread after installation. Existing consuming projects should merge the **Rules**
section from [templates/AGENTS.md](templates/AGENTS.md) so Codex reads the kit's rule files.
Claude Code and Antigravity users can use their existing update commands.

---

## 1.3.1 — 2026-09-18

Adds planning-mode interception guards to prevent agents from bypassing the d3nexus workflow
by writing `implementation_plan.md` directly (the Antigravity native planning artifact).

### Changed

- **`dev-lifecycle`**: Added `<HARD-GATE>` prohibiting `implementation_plan.md` creation.
  Added 2 new Red Flags (writing `implementation_plan.md`, skipping brainstorming).
  Added Rationalization Table covering 5 common bypass excuses.
- **`dev-brainstorming`**: Expanded `<HARD-GATE>` to explicitly cover `implementation_plan.md`
  as a gate bypass.

---

## 1.3.0 — 2026-09-17

Splits `brainstorming` into a development variant and a documentation variant, and makes the
document lifecycle's inception stage mandatory.

### Added

| Skill | What it does |
|---|---|
| `dev-brainstorming` | Turns an idea for code work into an approved design spec. The former `brainstorming`, with the document branch removed. Keeps the visual companion and its server scripts |
| `doc-brainstorming` | Turns an idea or a document request into an approved content spec. Written around what a document must say rather than around architecture. No visual companion |

- **`scripts/verify.sh` gains step 10.** It fails when either orchestrator names the `brainstorming`
  router instead of a concrete variant. The check is scoped to the two orchestrators and to the two
  forms that denote the skill, because `brainstorming` is also an ordinary English word and a
  repo-wide sweep like step 9's would fire on four legitimate uses.

### Changed

- **`brainstorming` is now a router.** It keeps its name and path, holds one question — idea,
  document, or coding — and invokes the matching variant. It has no default: an unclear answer is
  asked about again rather than guessed at. Everything that names `d3nexus:brainstorming` today
  keeps working, including the session-start hook and `rules/CRITICAL_RULES.md`.
- **`doc-lifecycle` Stage 0 is mandatory, and the gates renumber from three to four.** Gate 1 is now
  spec approval; the former gates 1, 2 and 3 become 2, 3 and 4. The stage was optional, and its skip
  condition asked whether the content was already known — a question an agent answers yes to
  essentially always. The stage is now required to *happen* while its depth still scales, so a
  runbook's spec is three sentences.
- **The upstream escape to `lean-product-lifecycle` splits asymmetrically.** `dev-brainstorming`
  keeps the original trigger. `doc-brainstorming` fires only when the document *is* a product
  argument whose idea has no evidence; a runbook or reference page never triggers it.
- **Each variant can correct a misroute to its sibling**, using the existing test: if the work
  changes a file that ships in the build, it is code.
- `dev-lifecycle` Stage 1 now names `dev-brainstorming`; its five gates and stage order are
  unchanged.
- Stage entry in both orchestrators is now imperative — a stage is entered by invoking its skill,
  not by reading its description and doing the work. `dev-lifecycle` had never contained the word
  "invoke", which is why agents skipped Gate 1.
- Guidance in `dev-brainstorming` that leaned toward code is no longer branch-conditional, since the
  branch is gone.

### Fixed

- Fifteen stale `doc-lifecycle` gate numbers across `doc-designer`, `doc-implementation` and
  `doc_quality_check`, left wrong by the renumber.
- A dead path in `dev-brainstorming` to `skills/brainstorming/visual-companion.md`, which the rename
  broke at exactly the point where the user had just accepted the visual companion.
- A claim in `dev-brainstorming` that `dev-lifecycle` has four approval gates. It has five.

### Upgrading

No action is required. `d3nexus:brainstorming` still resolves, and now asks which kind of work you
want before routing. Name `d3nexus:dev-brainstorming` or `d3nexus:doc-brainstorming` directly to
skip the question. Anything that quotes `doc-lifecycle` gate numbers needs re-reading: they shifted
by one.

---

## 1.2.0 — 2026-09-17

Adds the **Document Lifecycle Suite**: work whose deliverable is a document now has its own
lifecycle, its own quality gate and its own stage skills, instead of being forced through gates
built for code.

### Added

| Skill | What it does |
|---|---|
| `doc-lifecycle` | Orchestrates document work through three gates — brief and outline, verification, sign-off |
| `doc-designer` | Establishes the audience, classifies the document into exactly one Diátaxis type, produces the outline and the section breakdown |
| `doc-implementation` | Drafts section by section, one commit each, reusing the existing Kanban machinery unchanged |
| `doc_quality_check` | The documentation quality gate: refusal rule, mechanical checks, type conformance, content audit |
| `decision-records` | Architecture Decision Records in Michael Nygard's format, plus spike reports |

- **`brainstorming` gains two exits.** It now routes to `doc-designer` for document deliverables, and
  **upstream** to `lean-product-lifecycle` when the problem space was never validated — a route that
  did not previously exist in that direction.
- **`scripts/verify.sh` gains two checks.** Step 8 fails when a skill's own supporting file is
  referenced by nothing; it found seven pre-existing orphans on its first run, including a second
  reviewer prompt that had never been wired in. Step 9 fails when a live file still names a
  pre-rename skill.
- **`docs/lifecycles.en.md`** — reference: what each lifecycle is for, what it produces, and its
  process flow. **`docs/choosing-a-lifecycle.en.md`** — how-to: picking one for a specific piece of
  work, including when to skip all of them. Both carry a Vietnamese variant.
- **`docs/adr/`** — decision records for this repository, starting with why the documentation
  quality gate is a separate skill.
- **`evals/doc-designer/mixed-mode-material`** — the first ablation case for a documentation skill.
  Arm A 5/5, arm B 2/5. The report leads with where the baseline beat the skill.

### Changed

- **`rules/CRITICAL_RULES.md`** now selects the quality gate by the kind of work: `@quality_check`
  for anything that changes a file shipping in the build, `@doc_quality_check` for prose. The
  previous mandate was unsatisfiable for a Markdown deliverable.
- **`skills/quality_check/SKILL.md` is unmodified.** The documentation gate is a separate skill
  precisely so that the gate guarding every merge in every project did not have to change.

> [!CAUTION]
> **Breaking.** Three skills are renamed. `/d3nexus:epic-lifecycle`,
> `/d3nexus:epic-designer` and `/d3nexus:epic-implementation` no longer resolve, and any
> per-project `AGENTS.md` naming them must be updated.

### Renamed — the development lifecycle

"Epic" becomes the umbrella term covering both development and documentation work, so the
development lifecycle takes a name that distinguishes it:

| Old | New |
|---|---|
| `epic-lifecycle` | `dev-lifecycle` |
| `epic-designer` | `dev-designer` |
| `epic-implementation` | `dev-implementation` |

Each renamed skill keeps the word "epic" in its `description`, so a request phrased as epic-scale
work still activates it. `finishing-a-development-branch` and the directory `.devtool/epic/` are
unchanged — both kinds of epic live there, distinguished by a `Kind:` field. There is no data
migration, and the historical epic records under `.devtool/` deliberately keep the old names.

### Changed — source fidelity

- `check_source_fidelity.py` becomes a multi-source registry instead of a Lean-Product-only guard,
  and `verify.sh` step 7 is retitled accordingly.

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
