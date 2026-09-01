#!/usr/bin/env python3
"""
Local LLM agent with a tool-calling loop. The local model reads files itself,
so file content stays on-machine and out of Claude's context window.

Tools the model gets: read_file, list_dir, search_files - all confined to --dir.

Default: Ollama on port 11434, model auto-detected from the team installer
tags (see ollama_common.resolve_model). No pip dependencies.

Usage:
    python agent_local.py --dir path/to/shot "Summarize shot_040.nk"
    python agent_local.py --dir path/to/pipeline "Explain the architecture of this project"
    python agent_local.py --verbose --dir . "Find all hardcoded paths"
    python agent_local.py --image ref.png "Describe the lighting in this reference"
"""

import argparse
import glob
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ollama_common import (  # noqa: E402
    DEFAULT_URL, check_vision, encode_image, health_check, model_info, resolve_model,
)

# Ensure UTF-8 output on Windows (Qwen outputs Unicode characters)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MAX_TURNS = 10
DEFAULT_MAX_TOKENS = 4096
HARD_FILE_CAP = 500_000  # chars; never return more than this from one read

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a text file. Returns the full text content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative or absolute file path to read"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories at a given path. Directories carry a '/' suffix.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory to list (default: working directory)"},
                    "pattern": {"type": "string", "description": "Optional glob filter, e.g. '*.py' or '**/*.nk'"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for a text/regex pattern across files. Returns file:line: matches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Text or regex pattern to search for"},
                    "path": {"type": "string", "description": "Directory to search (default: working directory)"},
                    "file_pattern": {"type": "string", "description": "Glob filter for files, e.g. '*.py'"},
                },
                "required": ["pattern"],
            },
        },
    },
]


def file_char_budget(num_ctx):
    """How many characters one read_file may return. Roughly 3 chars per token,
    leaving half the context for the conversation and the answer."""
    if not num_ctx:
        return HARD_FILE_CAP
    return max(8_000, min(HARD_FILE_CAP, (num_ctx // 2) * 3))


def execute_tool(name, arguments, working_dir, char_budget):
    try:
        if name == "read_file":
            path = arguments["path"]
            if not os.path.isabs(path):
                path = os.path.join(working_dir, path)
            path = os.path.realpath(path)
            if not os.path.isfile(path):
                return f"Error: File not found: {path}"
            with open(path, "r", errors="replace") as f:
                text = f.read(char_budget + 1)
            if len(text) > char_budget:
                return (text[:char_budget]
                        + f"\n\n[TRUNCATED at {char_budget} chars to fit the model's context. "
                          "Use search_files to locate specific sections.]")
            return text

        elif name == "list_dir":
            path = arguments.get("path") or "."
            if not os.path.isabs(path):
                path = os.path.join(working_dir, path)
            path = os.path.realpath(path)
            if not os.path.isdir(path):
                return f"Error: Directory not found: {path}"
            pattern = arguments.get("pattern")
            if pattern:
                matches = glob.glob(os.path.join(path, pattern), recursive=True)
                entries = sorted(os.path.relpath(m, path) for m in matches)
            else:
                entries = []
                for e in sorted(os.listdir(path)):
                    if e.startswith("."):
                        continue
                    full = os.path.join(path, e)
                    entries.append(e + "/" if os.path.isdir(full) else e)
            if not entries:
                return "(empty directory)"
            return "\n".join(entries[:200])

        elif name == "search_files":
            import re
            pattern = arguments["pattern"]
            search_path = arguments.get("path") or "."
            if not os.path.isabs(search_path):
                search_path = os.path.join(working_dir, search_path)
            search_path = os.path.realpath(search_path)
            file_pattern = arguments.get("file_pattern") or "*"
            matches = []
            for filepath in glob.glob(os.path.join(search_path, "**", file_pattern), recursive=True):
                if not os.path.isfile(filepath) or os.path.getsize(filepath) > HARD_FILE_CAP:
                    continue
                try:
                    with open(filepath, "r", errors="replace") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                rel = os.path.relpath(filepath, working_dir)
                                matches.append(f"{rel}:{i}: {line.rstrip()}")
                                if len(matches) >= 50:
                                    break
                except (OSError, UnicodeDecodeError):
                    continue
                if len(matches) >= 50:
                    break
            if not matches:
                return f"No matches found for '{pattern}'"
            return "\n".join(matches)

        return f"Error: Unknown tool '{name}'"
    except Exception as e:
        return f"Error executing {name}: {e}"


def agent_loop(prompt, working_dir, url=DEFAULT_URL, model=None, max_turns=DEFAULT_MAX_TURNS,
               system=None, max_tokens=DEFAULT_MAX_TOKENS, verbose=False, image_path=None):
    ok, detail = health_check(url)
    if not ok:
        return f"ERROR: {detail}"
    try:
        model, why = resolve_model(url, model)
    except RuntimeError as e:
        return f"ERROR: {e}"
    info = model_info(url, model)
    char_budget = file_char_budget(info["num_ctx"])
    print(f"[qwen-delegate] model: {model} ({why}); context: {info['num_ctx'] or 'unknown'}; "
          f"read_file budget: {char_budget} chars", file=sys.stderr)

    if image_path:
        reason = check_vision(url, model)
        if reason:
            return f"ERROR: {reason}"

    default_system = (
        f"You are a helpful coding assistant analyzing files in: {working_dir}\n"
        "Use the provided tools to read files and explore the project as needed.\n"
        "Be concise and direct in your responses.\n"
        "When you have enough information, provide your final answer without calling more tools."
    )

    if image_path:
        b64, mime = encode_image(image_path)
        user_content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ]
    else:
        user_content = prompt

    messages = [
        {"role": "system", "content": system or default_system},
        {"role": "user", "content": user_content},
    ]

    for turn in range(max_turns):
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0.3,
            "max_tokens": max_tokens,
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{url}/v1/chat/completions", data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return f"ERROR: HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}"
        except Exception as e:
            return f"ERROR: {e}"

        choice = data["choices"][0]
        message = choice["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            return message.get("content") or "(no content returned)"

        for call in tool_calls:
            fn = call["function"]
            name = fn["name"]
            try:
                arguments = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                arguments = {}
            if verbose:
                print(f"  [turn {turn + 1}] -> {name}({json.dumps(arguments)})", file=sys.stderr)
            result = execute_tool(name, arguments, working_dir, char_budget)
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", name),
                "content": result,
            })

    return f"ERROR: Agent hit the {max_turns}-turn limit without a final answer. Narrow the task or raise --max-turns."


def main():
    parser = argparse.ArgumentParser(description="Local LLM agent with file tools (Ollama by default)")
    parser.add_argument("prompt", help="Task description for the agent")
    parser.add_argument("--dir", "-d", default=".", help="Working directory the model may read")
    parser.add_argument("--image", "-i", default=None, help="png/jpg/webp image for multimodal analysis")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Server URL (default {DEFAULT_URL})")
    parser.add_argument("--model", "-m", default=None,
                        help="Model tag. Default: auto-detect the team installer tag on the server")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS)
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS)
    parser.add_argument("--system", "-s", default=None, help="Custom system prompt")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show tool calls on stderr")
    args = parser.parse_args()

    working_dir = os.path.realpath(args.dir)
    if not os.path.isdir(working_dir):
        print(f"Error: Directory not found: {working_dir}", file=sys.stderr)
        sys.exit(1)
    if args.image and not os.path.isfile(args.image):
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = agent_loop(
        args.prompt, working_dir, url=args.url, model=args.model,
        max_turns=args.max_turns, system=args.system, max_tokens=args.max_tokens,
        verbose=args.verbose, image_path=args.image,
    )
    print(result)
    if result.startswith("ERROR:"):
        sys.exit(1)


if __name__ == "__main__":
    main()
