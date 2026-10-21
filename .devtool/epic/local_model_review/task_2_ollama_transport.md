---
id: "task_2_ollama_transport"
status: "done"
priority: "high"
assignee: null
epic: "local_model_review"
dueDate: null
created: "2026-10-21T09:10:00Z"
modified: "2026-10-21T09:28:37Z"
completedAt: "2026-10-21T09:28:37Z"
labels: ["review", "ollama", "transport"]
order: "a2"
---

# Task 2: Add the Ollama Transport

Epic: [local_model_review](local_model_review.en.md)

## Requirement Analysis

Create `local_review.py` with the transport half of the HLD contract: find the host, probe the
server and model, build the request options from the Modelfile's context, call `/api/chat`, and
keep only the answer after any inline thinking. Standard library only (`urllib.request`, `json`,
`dataclasses`, `math`, `os`). Add a fake Ollama server to `test_local_review.py`: an
`http.server.ThreadingHTTPServer` on `127.0.0.1` port 0, whose handlers for `GET /api/version`,
`POST /api/show` and `POST /api/chat` each test configures, and which records every request body.

## Files

Allowed files:
- `skills/dev-implementation/resources/scripts/local_review.py` (new)
- `skills/dev-implementation/resources/scripts/test_local_review.py` (new)

Read-only context:
- `.devtool/epic/local_model_review/local_model_review.en.md` — Module Contracts
- `.devtool/epic/local_model_review/2026-10-21-local-model-review-design.en.md` — decisions D2, D5, D6, D8

## Design Rationale

The transport has no caller yet; Task 6 wires it. Keeping it free of `run_external_review.py`
imports avoids a cycle when the runner imports it. Sampling is never sent (spec D5): the reference
model's Modelfile already tunes temperature, and Qwen in thinking mode degrades under greedy
decoding. Applicable skills: `d3nexus:test-driven-development`, `d3nexus:python-quality-check`.

## Impact Analysis & Blast Radius

- **Target files and symbols**: `local_review.DEFAULT_HOST`, `DEFAULT_NUM_CTX`, `LocalReviewError`,
  `Reply`, `host_from_env`, `probe`, `chat_options`, `chat`, `answer_text`.
- **Downstream callers**: none in this task; `run_external_review.run` from Task 6.
- **Cross-platform bridges**: HTTP to a local Ollama server, faked in tests.
- **Target test coverage threshold**: every public function above is exercised by a named test.

### BDD SCENARIOS

Covers: LMR-HP-06, LMR-EC-02, LMR-EC-07, LMR-FR-01, LMR-FR-03

```gherkin
Scenario: [LMR-HP-06] [Tier C - Integration] The Modelfile governs the context
  Given /api/show reports "num_ctx 65536" in its parameters
  When probe runs and chat_options(65536, None, 30000) runs
  Then probe returns 65536
  And chat_options returns {"num_predict": 35536} with no "num_ctx" key

Scenario: [LMR-EC-02] [Tier C - Integration] Context defaults and overrides
  Given a model whose Modelfile sets no num_ctx
  When chat_options(None, None, 1000) runs
  Then it returns {"num_ctx": 32768, "num_predict": 31768}
  And chat_options(65536, 16384, 1000) returns {"num_ctx": 16384, "num_predict": 15384}

Scenario: [LMR-EC-07] [Tier C - Integration] Inline thinking is never parsed
  Given the content "draft [Critical] a.py:1 — x\nVerdict: CHANGES REQUIRED\n</think>\n## Analysis\nfine\nVerdict: PASS"
  When answer_text runs
  Then it returns "## Analysis\nfine\nVerdict: PASS"

Scenario: [LMR-FR-01] [Tier C - Integration] Probe failures name their cause
  Given no server listens on a closed local port
  When probe runs against it
  Then it raises LocalReviewError "Ollama server not reachable at http://127.0.0.1:<port>"
  And against a fake server whose /api/show answers 404 it raises "model ghost is not installed (ollama list)"

Scenario: [LMR-FR-03] [Tier C - Integration] Transport failures become replies
  Given a fake server whose /api/chat answers HTTP 500 with the body "boom"
  When chat runs
  Then it returns content "" and error "HTTP 500: boom"
  And against a server that answers after 3 seconds, chat with timeout 1 returns error "timed out after 1 seconds"
```

## Verification

| ID | Phase | Command | Expect | Needs |
|----|-------|---------|--------|-------|
| V1 | RED | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k TransportTest` | exit 1; contains "FAILED" | — |
| V2 | GREEN | `python3 -m unittest skills/dev-implementation/resources/scripts/test_local_review.py -k TransportTest` | exit 0; contains "OK" | — |
| V3 | TIER-B | `ruff check skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V4 | TIER-B | `mypy --strict --follow-imports=silent skills/dev-implementation/resources/scripts/local_review.py skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0 | — |
| V5 | TIER-C | `python3 scripts/run_unittest_junit.py --junitxml build/test-results/task_2.xml skills/dev-implementation/resources/scripts/test_local_review.py` | exit 0; results build/test-results/task_2.xml | — |

## Stop and Report If

- A command, path, symbol or anchor named in this task does not match the repository.
- A Verification row fails for a reason other than its Expect.
- The work needs a change to a file outside Allowed files, or to a protected path.
- The work needs a change to this task's Verification table, Definition of Done, Allowed files or
  Covers line.
- A variable named in the Needs column is unset.
- A test would need a real Ollama server, network beyond `127.0.0.1`, or a model download.

## Decisions Already Made

- Frozen constants: `DEFAULT_HOST = "http://localhost:11434"`, `DEFAULT_NUM_CTX = 32768`.
- `class LocalReviewError(Exception)`; `str(error)` is the reason shown to the developer.
- `@dataclass(frozen=True) class Reply: content: str; done_reason: str | None; error: str | None`.
- `def host_from_env() -> str`: `OLLAMA_HOST` when set, else `DEFAULT_HOST`; a value without `://`
  gets `http://` prepended; a trailing `/` is removed.
- `def probe(host: str, model: str, timeout: int = 10) -> int | None`: `GET <host>/api/version`;
  any `URLError` or `OSError` raises `LocalReviewError(f"Ollama server not reachable at {host}")`.
  Then `POST <host>/api/show` with `{"model": model}`; HTTP 404 raises
  `LocalReviewError(f"model {model} is not installed (ollama list)")`. Returns the integer on the
  `num_ctx` line of the response's `parameters` string, or `None` when absent.
- `def chat_options(model_ctx: int | None, flag_ctx: int | None, prompt_tokens: int) -> dict[str, int]`:
  `effective = flag_ctx or model_ctx or DEFAULT_NUM_CTX`; always `num_predict = effective - prompt_tokens`;
  `num_ctx = effective` only when `flag_ctx is not None or model_ctx is None`. No other key.
- `def chat(host: str, model: str, system: str, user: str, options: dict[str, int], timeout: int) -> Reply`:
  posts `{"model": model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "stream": False, "options": options}`
  and never sends `think`. Success returns `Reply(answer_text(message.content), data.get("done_reason"), None)`.
  A socket timeout returns `Reply("", None, f"timed out after {timeout} seconds")`; an `HTTPError`
  returns `Reply("", None, f"HTTP {code}: {body[:500]}")`; any other `URLError` or `OSError` returns
  `Reply("", None, str(error))`. `chat` never raises.
- `def answer_text(content: str) -> str`: the text after the last `</think>`, stripped; without one,
  the content stripped.
- `local_review.py` never imports `run_external_review.py`.

## Definition of Done

- All five covered scenarios have a `test_lmr_*` method in `TransportTest` and pass in the JUnit
  report. (V2, V5)
- No test reaches anything but the in-process fake server. (V2)
- Lint and strict type checking report zero issues. (V3, V4)

## Dependencies & Blockers

None. Blocks [Task 6](task_6_wire_local_review_into_runner.md).

## References & Rollback

- [Epic HLD](local_model_review.en.md), Module Contracts.
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md) — `/api/version`, `/api/show`, `/api/chat`.
- **Rollback**: revert the commit; nothing calls the module yet.
