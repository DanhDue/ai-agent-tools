# Local Model Review Setup

Review Choice option 3 sends the finished epic to a model served by a local Ollama:

```bash
python3 skills/dev-implementation/resources/scripts/run_external_review.py run \
  --epic-dir <epic_dir> --base <base_ref> --cli ollama --model <model>
```

The developer picks the model from `ollama list`; the agent never picks it.

## What the runner sends

- One pass per task commit, then one pass for the epic. Each pass is self-contained, because the
  model has no tools and cannot open a file.
- A system message built from `local-review-prompt.md`: the workflow primer, `review-rules.md`, the
  platform rules for the languages that pass touches, and its checklist. It replaces any `SYSTEM`
  block of the Modelfile for the duration of the call.
- No sampling option and no `think` field. Temperature and the other sampling parameters come from
  the Modelfile. The context is the Modelfile's `num_ctx`; `--num-ctx` overrides it, and 32768 is
  used when the Modelfile sets none.
- `--host` defaults to `$OLLAMA_HOST`, then `http://localhost:11434`. `--timeout` applies to each
  pass.

## A reviewer Modelfile

The reference model used while designing this option, on a 64 GB Mac:

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

Create it with `ollama create qwen38-reviewer -f <path to the Modelfile>`.

- It has no `SYSTEM` block: the runner sends the system message.
- Its template opens `<think>` without closing it, so the model reasons before it answers. Ollama
  returns that reasoning in `message.thinking`, which the runner ignores; when a template puts it in
  `content` instead, the runner keeps only the text after the last `</think>`.

## Thinking turned off by a template

Some imported templates pre-fill an empty `<think>` and `</think>` pair after the assistant turn
opens. That is how Qwen's non-thinking mode is selected: the model starts after the reasoning block
has already closed. Removing a `<think>` stop token does not change it. Check with
`ollama show <model> --modelfile`; if the empty pair is there, override `TEMPLATE` as above.

The review still works with thinking off, because the prompt asks for an `## Analysis` section
before the verdict block.

## Expect

- Several minutes per pass at about 12 output tokens per second; a five-task epic takes 20 to 40
  minutes.
- Loading the model needs its full size in memory and may evict another loaded model.
- More false positives than a frontier model. Critical and Important findings require a quote, a
  finding at a path the pass never showed is marked `(location not shown to reviewer)`, and every
  blocking finding still needs the developer's decision.
