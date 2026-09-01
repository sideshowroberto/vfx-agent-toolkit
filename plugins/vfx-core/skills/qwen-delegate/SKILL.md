---
name: qwen-delegate
description: Delegate tasks from a Claude Code session to the local Qwen model on Ollama (port 11434) - the same model the team's OpenCode / Qwen Code installs use. Use when user says "ask Qwen", "have Qwen do this", "delegate to local model", "use local LLM", "keep this NDA-safe", "do this locally". Also use proactively for NDA-sensitive file analysis, large-file summarization, boilerplate generation, BlinkScript drafts, or batch text transforms where privacy and Claude-token savings matter more than deep reasoning.
allowed-tools: Bash,Read
---

# Qwen Delegate

Routes a task to the **local Qwen model served by Ollama**. The prompt, any files
the model reads, and the answer never leave the machine, and the file content
never enters Claude's context - only the model's reply comes back. NDA-safe by
design, and cheap on Claude tokens.

## What you have installed

The team Qwen installer created ONE of these tags, chosen by GPU memory:

| Tag | Card | Context | Vision | Tools |
|-----|------|---------|--------|-------|
| `vfx-qwen38-27b-262k` | 24 GB+ (workstation) | 262K | yes | yes |
| `vfx-qwen3-14b-16k` | under 24 GB | 16K | **no** | yes |

The scripts **auto-detect** whichever is present, so the commands below are the
same on every machine. Override with `--model <tag>` or the `LOCAL_LLM_MODEL`
env var. A different server (vLLM, llama-server, LM Studio) works via
`--url` / `LOCAL_LLM_URL` with `--model local`.

**On the 14B variant:** no `--image` (the script refuses with a clear message),
and one file read is capped at roughly 24K characters so it fits the 16K
context. Point the agent at a folder and ask about ONE file at a time.

---

## When to delegate vs keep in Claude

| Delegate to Qwen | Keep in Claude |
|------------------|----------------|
| NDA-protected files (comp scripts, shot files, pipeline code on studio drives) | Multi-step reasoning, planning, architecture decisions |
| Summarizing large .nk / .py / .hip files | Tasks needing MCP tools (Nuke / Houdini / Unreal control) |
| Boilerplate and first-draft code | Complex debugging needing full conversation context |
| First-draft BlinkScript kernels | Editing files in the workspace |
| Text transformation, batch reformatting | Web search, library docs |
| Reference-image first pass (27B variant only) | Anything needing several MCP servers |

---

## Preflight - run this first

```bash
python <skill-dir>/scripts/query_local.py --check
```

Prints the server status, the tag that will be used, its capabilities and
context length. If Ollama is down: `ollama serve`, then `ollama list` to confirm
a `vfx-qwen*` tag exists (if not, run the team Qwen installer).

`<skill-dir>` is this skill's own directory - resolve the path against it.
Scripts are pure stdlib, no pip installs.

**After a reboot** check `ollama ps` shows `100% GPU`, not `100% CPU`. The
Ollama app can race the NVIDIA driver and silently serve on CPU, which looks
like "the model hangs".

---

## Two scripts, two jobs

| Script | Reads files? | Use for |
|--------|-------------|---------|
| `scripts/query_local.py` | **No.** Prompt text, `--stdin` pipe, optional `--image`. | One-shot prompts, drafts, image analysis |
| `scripts/agent_local.py` | **Yes.** Tool loop with read / list / search confined to `--dir`. | Anything where the model must open a file |

Neither script has a `--file` flag. To summarize a file, give `agent_local.py`
the folder via `--dir` and name the file in the prompt. To transform text,
pipe it into `query_local.py` on stdin.

---

## Invocation patterns

### One-shot prompt
```bash
python <skill-dir>/scripts/query_local.py "Write a Python function that parses a Nuke .nk file for Read node paths"
```

### Pipe text in (transform / reformat)
```bash
cat notes.txt | python <skill-dir>/scripts/query_local.py --stdin "Rewrite as a numbered checklist"
```
`--stdin` is required for piped input; without it the script never touches
stdin (an idle pipe from a harness would otherwise block it forever).

### Summarize a file (NDA-safe - model reads it locally)
```bash
python <skill-dir>/scripts/agent_local.py --dir "path/to/shot/comp" \
  "Read shot_040.nk and summarize: inputs, main operations, final output"
```

### Multi-file analysis
```bash
python <skill-dir>/scripts/agent_local.py --verbose --dir "path/to/pipeline" \
  "Find every hardcoded absolute path in the Python files and list file:line"
```
`--verbose` shows each tool call on stderr so you can see what it read.

### Image analysis (27B variant only)
```bash
python <skill-dir>/scripts/query_local.py --image "ref_plate.png" \
  "Describe the camera angle, lighting, and key subjects"
```
Accepts png / jpg / webp. Convert EXR or TIFF plates to PNG first (Nuke or ffmpeg).

### Force a specific tag or a bigger answer
```bash
python <skill-dir>/scripts/query_local.py --model qwen3:8b --max-tokens 8000 "..."
```

---

## Prompting the local model

- **Be explicit and bounded.** Say what to read, what to output, and the format.
  "Summarize shot_040.nk as: inputs / operations / output" beats "look at the comp".
- **One file per question on the 14B**; the 27B can take a folder.
- **Thinking is off by default** for speed. Add `--think` to `query_local.py`
  for harder reasoning (BlinkScript, tricky refactors).
- **The model has no MCP, no internet, no write access.** It can only read
  inside `--dir` and answer. Claude does the editing.

---

## After getting the output

1. **Review the draft** - the local model is good at summaries and boilerplate,
   weaker at subtle correctness. Treat code as a first draft.
2. **Paste the useful parts** into the Claude session to refine or apply.
3. **Or use directly** if it is a summary or boilerplate that reads correctly.

For BlinkScript drafts: hand the output to the `nuke-blinkscript` skill for a
GPU-correctness review.

---

## Network-drive policy

The same PreToolUse hook that guards Claude's own tools guards these scripts.
`--dir` and `--image` may point at C: / D:, the approved sandbox subtree, and
any active job grant. Anything else on the network is blocked before the model
ever sees it - rephrase inside the allowed paths rather than working around it.

## Limitations

- No MCP tools, no internet, no file writes.
- Vision quality is below Claude's; use it as an NDA-safe first pass.
- `agent_local.py` stops after 10 tool turns (`--max-turns` to raise).
- Ollama unloads the model after ~5 minutes idle; the first call after that
  takes 10-20 s to reload. That is normal, not a hang.
