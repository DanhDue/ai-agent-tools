# Local Review Checklists

The review runner inserts one section into the local review brief, chosen by the pass type. Each
item is answered in `## Analysis`, quoting the shown line it relies on.

## Task pass

1. Does each GREEN row's command exercise the Definition of Done item it backs?
2. Does each RED row fail for the missing behaviour? In a compiled language a compile failure counts.
3. Does each test import and call production code from Allowed files, or rebuild the logic locally?
4. Is any assertion vacuous: none at all, always true, or made on a mock the test itself configured?
5. Do the Given, When and Then of each covered scenario map to an arrange, act and assert in a test?
6. Does the code contradict a Decision Already Made?
7. Does any added line violate a loaded platform rule?

## Epic pass

1. Do code constants, defaults and enum values match the spec and the HLD, or has the contract drifted?
2. Is each audit disclosure justified: grader amendments, protected paths, commits outside tasks?
3. Does each commit outside tasks change what its title says, and nothing untested besides?
4. Does the traceability output reveal a scenario covered only superficially?
5. Restate the Gate 5 items from the audit for the developer, without a severity.
