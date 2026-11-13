# Local Model Review Setup

Runs local Ollama review passes when selected (`--cli ollama --model <model>`, chosen by the developer from `ollama list`):

```bash
python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
  --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>
```

For triage and finding rules, see [review-triage.md](review-triage.md) and [review-rules.md](../../dev-implementation/references/review-rules.md).

## What the Runner Sends

- One self-contained pass per task commit plus one epic pass (model has no filesystem tools).
- System message built from `local-review-prompt.md`, [review-rules.md](../../dev-implementation/references/review-rules.md), language rules, and checklist (overriding Modelfile `SYSTEM` for that call).
- Temperature/sampling come from the Modelfile; context defaults to Modelfile `num_ctx` (`32768` fallback, overridden via `--num-ctx`).
- `--host` defaults to `$OLLAMA_HOST` or `http://localhost:11434`; `--timeout` bounds each pass.

## Watching a Review

Live logs stream to `build/local-review/<epic_dir>/<n>-<label>.log` (when `build/` is gitignored; otherwise inside `.git`): `tail -f build/local-review/<epic_dir>/1-<first task id>.log`. Only text after `--- answer ---` reaches `review_results.md`.

## Reference Reviewer Modelfile (64 GB Mac)

```text
FROM hf.co/unsloth/Qwen3.8-27B-GGUF:Q8_0

PARAMETER draft_num_predict 1
PARAMETER num_ctx 65536
PARAMETER num_batch 1024
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER top_k 20
PARAMETER min_p 0.05
PARAMETER repeat_penalty 1.05
PARAMETER stop "<|im_start|>"
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|im_start|>user"

TEMPLATE """{{- if .System }}<|im_start|>system
Reasoning effort is set to xhigh. Please think carefully through the task, validate key assumptions, consider plausible alternatives, and prioritize correctness, consistency, and clarity in the final answer.

{{ .System }}<|im_end|>
{{ end }}{{- range .Messages }}{{- if eq .Role "user" }}<|im_start|>user
{{ .Content }}<|im_end|>
{{ else if eq .Role "assistant" }}<|im_start|>assistant
{{ .Content }}<|im_end|>
{{ end }}{{- end }}<|im_start|>assistant
<think>
"""
```

Create with `ollama create qwen38-reviewer -f <Modelfile>`. No `SYSTEM` block is needed; if an imported template pre-fills empty `<think></think>`, override `TEMPLATE` as above (`ollama show <model> --modelfile` to check).

## Expectations & Guidance

- Passes take ~10–26 minutes at ~11 tok/s (raise `--timeout` from `1800` if needed) and require full model size in memory.
- Critical/Important findings require a quote; unshown locations carry `(location not shown to reviewer)`. Triage per [review-triage.md](review-triage.md).
