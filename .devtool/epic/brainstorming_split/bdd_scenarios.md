# BDD Scenarios — `brainstorming_split`

Epic: [brainstorming_split](brainstorming_split.en.md)

Organised by the six use cases in [HLD §4.2](brainstorming_split.en.md#42-use-cases), each covering
the five-dimension boundary matrix. Scenarios are derived from the HLD's use cases and sequence
diagram, not from any implementation.

**A note on the async dimension.** Skill markdown has no concurrency. Dimension 4 is therefore
covered here as **ordering and interleaving hazards** — the sequence in which tasks touch the same
paths, and the sequence in which a user's answers arrive — which is where this medium's equivalent
failures actually live. Writing untestable thread-race scenarios to fill a template would be
ceremony.

---

## UC1 — Enter with an ambiguous request

### Happy paths

```gherkin
Scenario: The router asks before doing anything else
  Given the user says only "brainstorm this"
  When d3nexus:brainstorming is invoked
  Then the three-option question is asked in the user's wording
  And no codebase exploration has happened yet

Scenario: Coding reaches the development variant
  Given the router has asked its question
  When the user answers "thực hiện phát triển tính năng (coding)"
  Then dev-brainstorming is invoked

Scenario: Idea development reaches the documentation variant
  Given the router has asked its question
  When the user answers "phát triển ý tưởng"
  Then doc-brainstorming is invoked

Scenario: Documentation reaches the documentation variant
  Given the router has asked its question
  When the user answers "làm tài liệu"
  Then doc-brainstorming is invoked
```

### Edge cases and boundaries

```gherkin
Scenario: An empty answer produces another question
  Given the router has asked its question
  When the user replies with nothing about the deliverable
  Then the router asks again
  And it does not pick a variant

Scenario: A request naming both a feature and a document
  Given the user asks to "document the new export feature and build the CSV writer"
  When the router applies the deliverable test
  Then it asks which of the two the session is for
  And it does not silently choose one

Scenario: A request that names source-code features but wants only prose
  Given the user asks for an architecture overview of the payments module
  When the router asks its question
  And the user answers "làm tài liệu"
  Then doc-brainstorming is invoked
  And the presence of code terms does not override the answer

Scenario: The user names a variant directly
  Given the user invokes d3nexus:dev-brainstorming themselves
  When the session starts
  Then the router is not involved
  And no disambiguating question is asked
```

### State transitions

```gherkin
Scenario: The router holds no state between answers
  Given the router asked its question and the user answered
  When the chosen variant is invoked
  Then the router's work is finished
  And it is not re-entered later in the session
```

### Ordering and interleaving hazards

```gherkin
Scenario: An answer arrives before the question is fully posed
  Given the user pre-empts with "coding" in the same breath as the request
  When the router reads the request
  Then it accepts the stated deliverable
  And it does not ask a question already answered
```

### Failures and resilience

```gherkin
Scenario: The router refuses to infer when the answer is unusable
  Given the user answers with something that maps to no option
  When the router evaluates the answer
  Then it asks again rather than defaulting
  And no default destination exists in its body
```

---

## UC2 — Enter with a known branch

### Happy paths

```gherkin
Scenario: dev-lifecycle enters its inception stage
  Given a request spanning multiple components
  When dev-lifecycle reaches Stage 1
  Then it invokes d3nexus:dev-brainstorming

Scenario: doc-lifecycle enters its inception stage
  Given a document request with several sections
  When doc-lifecycle reaches Stage 0
  Then it invokes d3nexus:doc-brainstorming
```

### Edge cases and boundaries

```gherkin
Scenario: An orchestrator must never name the router
  Given either orchestrator
  When its stage definitions are read
  Then each names a concrete variant
  And neither names d3nexus:brainstorming

Scenario: The stage is entered by invocation, not by imitation
  Given an orchestrator at an inception stage
  When it proceeds
  Then it invokes the stage's skill
  And it does not read the stage description and do that work itself
```

### State transitions

```gherkin
Scenario: Gate 1 belongs to the inception skill in both lifecycles
  Given dev-lifecycle and doc-lifecycle
  When their gate tables are compared
  Then in each, Gate 1 is approved by the user at the end of inception
```

### Ordering and interleaving hazards

```gherkin
Scenario: Task 2 must not create the router before Task 1 moves the directory
  Given skills/brainstorming/ still holds the pre-split skill
  When the router file is created before the rename runs
  Then the subsequent git mv absorbs the new file
  And the router is lost
```

### Failures and resilience

```gherkin
Scenario: An orchestrator naming a skill that does not exist
  Given doc-lifecycle names doc-brainstorming
  And skills/doc-brainstorming/ has not been created
  When verify.sh runs
  Then the relative-link check fails
```

---

## UC3 — Write a small document

### Happy paths

```gherkin
Scenario: A runbook passes through the mandatory inception stage
  Given the user asks for a runbook whose content is fully known
  When doc-lifecycle runs
  Then Stage 0 executes
  And the resulting spec may be three sentences
  And Gate 1 is the user's approval of that spec
```

### Edge cases and boundaries

```gherkin
Scenario: A one-paragraph note still passes the hard gate
  Given the user asks for a one-paragraph onboarding note
  When doc-brainstorming judges the work simple
  Then it still presents a design and waits for approval

Scenario: A single ADR is below the threshold entirely
  Given the user asks for one architecture decision record
  When doc-brainstorming assesses scale
  Then it routes directly to decision-records

Scenario: A typo fix does not enter the lifecycle at all
  Given the user asks to fix a broken link in an existing document
  When the work is assessed
  Then it is edited directly with no brief, no outline and no gate
```

### State transitions

```gherkin
Scenario: The gate count is four, not three
  Given doc-lifecycle after this epic
  When its gates are enumerated
  Then they are Spec Approved, Brief and Outline, Draft Verified, Sign-Off

Scenario: The untestable skip condition no longer exists
  Given skills/doc-lifecycle/SKILL.md
  When it is searched for a condition permitting Stage 0 to be skipped
  Then none is found
```

### Ordering and interleaving hazards

```gherkin
Scenario: The gate renumber reaches all four representations together
  Given the mermaid diagram, the prose, the gate table and the Stage Skills table
  When any one of them is updated
  Then the other three are updated in the same commit
```

### Failures and resilience

```gherkin
Scenario: A stale three-gate claim survives elsewhere
  Given any live file outside .devtool and CHANGELOG.md
  When it is searched for a three-gate claim about doc-lifecycle
  Then there are zero matches
```

---

## UC4 — Discover a misroute mid-session

### Happy paths

```gherkin
Scenario: Document work discovered inside the development variant
  Given the session is in dev-brainstorming
  And nothing the work produces will change a file that ships in the build
  When the deliverable test is applied
  Then the session stops and hands over to doc-brainstorming

Scenario: Code work discovered inside the documentation variant
  Given the session is in doc-brainstorming
  And the work will change a file that ships in the build
  When the deliverable test is applied
  Then the session stops and hands over to dev-brainstorming
```

### Edge cases and boundaries

```gherkin
Scenario: Heavy prose that still ships in the build stays on the code side
  Given the work rewrites a SKILL.md and produces almost no code
  When the deliverable test is applied
  Then it is code work
  And no correction to the documentation variant occurs

Scenario: The correction restarts inception rather than handing over a finished spec
  Given a correction fires
  When the sibling variant is entered
  Then inception begins in that variant
  And a partly written spec is not carried across as approved
```

### State transitions

```gherkin
Scenario: The correction exit is not a routine edge
  Given either variant's process-flow diagram
  When its solid edges are enumerated
  Then no solid edge leads to the sibling variant
```

### Ordering and interleaving hazards

```gherkin
Scenario: A correction after the user has already approved a design
  Given the user approved a code-oriented design
  And the deliverable is then discovered to be a document
  When the correction fires
  Then the prior approval is not treated as covering the document work
```

### Failures and resilience

```gherkin
Scenario: Without a correction exit the session has nowhere to go
  Given a variant with no correction exit
  And the deliverable is discovered to be wrong for that variant
  When the agent looks for a way out
  Then none exists
  And the pressure is to carry on rather than to stop
```

---

## UC5 — Discover the idea was never validated

### Happy paths

```gherkin
Scenario: The development variant escapes on an unnamed segment
  Given the target customer cannot be named as a specific segment
  When dev-brainstorming reaches its escape check
  Then it stops and recommends lean-product-lifecycle
  And it hands over the context already gathered

Scenario: The documentation variant escapes on an unevidenced product argument
  Given the document is a strategy paper arguing for a new market
  And no interviews, data or ranked needs support it
  When doc-brainstorming reaches its escape check
  Then it stops and recommends lean-product-lifecycle
```

### Edge cases and boundaries

```gherkin
Scenario: A runbook never triggers the documentation escape
  Given the user asks for a runbook for an existing process
  When doc-brainstorming reaches its escape check
  Then the condition does not fire

Scenario: A reference page never triggers the documentation escape
  Given the user asks for a set of API reference pages
  When doc-brainstorming reaches its escape check
  Then the condition does not fire

Scenario: The escape fires before the clarifying questions
  Given either variant
  When the escape condition holds
  Then the session stops at the escape check
  And the user is not asked the clarifying questions first
```

### State transitions

```gherkin
Scenario: Proceeding anyway records the unvalidated assumption
  Given the escape fired and the user chose to continue
  When the spec is written
  Then the unvalidated assumption appears in its risks section
```

### Ordering and interleaving hazards

```gherkin
Scenario: The lean entry node acknowledges both variants
  Given lean-product-lifecycle's mermaid entry node
  When it is read
  Then it says the escape arrives from either brainstorming variant
```

### Failures and resilience

```gherkin
Scenario: Copying the escape condition unchanged would misroute documents
  Given the development variant's escape condition applied verbatim to documents
  When a runbook request is assessed against it
  Then the target customer cannot be named
  And the runbook is wrongly pushed toward market discovery
```

---

## UC6 — Verify the kit after the change

### Happy paths

```gherkin
Scenario: The full suite passes from a normal checkout
  Given a normal checkout on the merged branch with .superpowers/ present
  When scripts/verify.sh runs in full
  Then all ten steps pass

Scenario: The new check passes against corrected orchestrators
  Given both orchestrators name concrete variants
  When verify.sh step 10 runs
  Then it reports ok
```

### Edge cases and boundaries

```gherkin
Scenario: The check has been observed failing
  Given dev-lifecycle Stage 1 is temporarily edited to name d3nexus:brainstorming
  When verify.sh step 10 runs
  Then it fails
  And its message names the offending file and line

Scenario: English prose about brainstorming does not trip the check
  Given writing-plans says "during brainstorming"
  And dev-designer says "not a full brainstorming dialogue"
  When verify.sh step 10 runs
  Then neither file is examined

Scenario: The preserved provenance path does not trip the check
  Given document-reviewer-prompt.md line 11 names a pre-1.2.0 path
  When verify.sh step 10 runs
  Then that file is not examined

Scenario: verify.sh's own comment does not trip the check
  Given scripts/verify.sh line 129 names the historical orphan path
  When step 10 runs
  Then verify.sh is not examined
```

### State transitions

```gherkin
Scenario: The skill count rises by exactly one
  Given the merged result
  When skill directories and SKILL.md files are counted
  Then both are 54
  And they are equal
```

### Ordering and interleaving hazards

```gherkin
Scenario: The check lands before the orchestrators are corrected
  Given verify.sh step 10 is added
  And dev-lifecycle still names the router
  When verify.sh runs
  Then step 10 fails
  And the epic cannot merge until the orchestrators are retargeted
```

### Failures and resilience

```gherkin
Scenario: A worktree hides a checkout-only failure
  Given the suite is run only from a worktree
  And .superpowers/ exists only in a normal checkout
  When a check reads gitignored paths
  Then the worktree run passes
  And the checkout run fails

Scenario: A stale directory survives a rename
  Given a renamed skill directory retained gitignored files
  When directory and SKILL.md counts are compared
  Then they differ
  And the stale directory is revealed
```
