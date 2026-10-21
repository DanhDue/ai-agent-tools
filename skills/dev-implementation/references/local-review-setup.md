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

## Watching a review

The runner streams every pass and prints `Live logs: <directory>` before the first one. Each pass
writes `<n>-<label>.log` there as the model produces it: its thinking first, then a
`--- answer ---` line, then the analysis and verdict block. Open a file in the editor, or follow it:

```bash
tail -f build/local-review/<epic_dir>/1-<first task id>.log
```

The directory is `build/local-review/<epic_dir>` when Git ignores `build/`; otherwise it sits inside
the Git directory, at `git rev-parse --git-path local-review/<epic_dir>`. Neither place changes
`git status`, so watching never discards a round. Only the answer reaches `review_results.md`.

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

Measured with the Modelfile above on a 64 GB Mac mini M4 Pro, reviewing this kit's own
`local_model_review` epic:

| Pass | Prompt tokens | Prompt processing | Generated tokens | Pass time |
|---|---|---|---|---|
| task 1 | 8,113 | 80 s | 12,271 | 1,203 s |
| task 2 | 7,040 | 63 s | 6,064 | 634 s |
| task 3 | about 11,500 | 77 s | not recorded | 1,421 s |
| task 4 | not recorded | not recorded | not recorded | 1,546 s |

- Generation runs at about 11 tokens per second and thinking is most of what is generated, so a
  pass takes 10 to 26 minutes and an eight-pass round several hours. A pass can exceed the default
  `--timeout 1800`; raise it, or turn thinking off.
- To turn thinking off, create a second model from the same Modelfile whose template ends with an
  empty `<think>` and `</think>` pair after the assistant turn opens, as described above. The model
  then writes only the `## Analysis` section and the verdict block.
- Loading the model needs its full size in memory and may evict another loaded model.
- More false positives than a frontier model. Critical and Important findings require a quote, a
  finding at a path the pass never showed is marked `(location not shown to reviewer)`, and every
  blocking finding still needs the developer's decision.
