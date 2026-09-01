#!/usr/bin/env python3
"""
One-shot query to the local LLM. Prompt text plus an optional image; this
script does NOT read files (use agent_local.py for that).

Default: Ollama on port 11434, model auto-detected from the team installer
tags (see ollama_common.resolve_model). No pip dependencies.

Usage:
    python query_local.py "What is an AOV?"
    python query_local.py --system "You are a Nuke TD" "Explain deep compositing"
    python query_local.py --image ref.png "Describe the lighting in this reference"
    echo "some text" | python query_local.py --stdin "Summarize this"
    python query_local.py --check          # server + model preflight, no generation
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ollama_common import (  # noqa: E402
    DEFAULT_URL, check_vision, encode_image, health_check, is_ollama,
    model_info, resolve_model,
)

# Ensure UTF-8 output on Windows (Qwen outputs Unicode characters)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def query(prompt, system=None, image_path=None, url=DEFAULT_URL,
          model=None, temperature=0.7, max_tokens=4096, think=False):
    ok, detail = health_check(url)
    if not ok:
        return f"ERROR: {detail}"

    try:
        model, why = resolve_model(url, model)
    except RuntimeError as e:
        return f"ERROR: {e}"
    print(f"[qwen-delegate] model: {model} ({why})", file=sys.stderr)

    if image_path:
        reason = check_vision(url, model)
        if reason:
            return f"ERROR: {reason}"

    messages = []
    if system:
        messages.append({"role": "system", "content": system})

    if image_path:
        b64, mime = encode_image(image_path)
        if is_ollama(url):
            # Ollama native API takes raw base64 in an "images" list
            messages.append({"role": "user", "content": prompt, "images": [b64]})
        else:
            messages.append({"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ]})
    else:
        messages.append({"role": "user", "content": prompt})

    if is_ollama(url):
        # Native API supports think:false, which the OpenAI-compat route ignores.
        payload = {
            "model": model,
            "messages": messages,
            "options": {"temperature": temperature, "num_predict": max_tokens},
            "stream": False,
            "think": think,
        }
        endpoint = f"{url}/api/chat"
    else:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        endpoint = f"{url}/v1/chat/completions"

    req = urllib.request.Request(
        endpoint, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
        if is_ollama(url):
            return data["message"]["content"]
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        return f"ERROR: HTTP {e.code} from {endpoint}: {body}"
    except Exception as e:
        return f"ERROR: {e}"


def main():
    parser = argparse.ArgumentParser(description="Query the local LLM (Ollama by default)")
    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--system", "-s", default=None, help="System prompt")
    parser.add_argument("--image", "-i", default=None, help="png/jpg/webp image for multimodal analysis")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Server URL (default {DEFAULT_URL})")
    parser.add_argument("--model", "-m", default=None,
                        help="Model tag. Default: auto-detect the team installer tag on the server")
    parser.add_argument("--temp", type=float, default=0.7, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=4096, help="Max tokens to generate")
    parser.add_argument("--think", action="store_true", help="Enable thinking mode (slower, deeper)")
    parser.add_argument("--stdin", action="store_true",
                        help="Append piped stdin text to the prompt (never read otherwise)")
    parser.add_argument("--check", action="store_true", help="Health-check server and model, then exit")
    args = parser.parse_args()

    if args.check:
        ok, detail = health_check(args.url)
        print(detail)
        if not ok:
            sys.exit(1)
        try:
            model, why = resolve_model(args.url, args.model)
        except RuntimeError as e:
            print(f"ERROR: {e}")
            sys.exit(1)
        info = model_info(args.url, model)
        caps = ", ".join(info["capabilities"]) or "unknown"
        ctx = info["num_ctx"] or "unknown (server default)"
        print(f"model: {model} ({why})")
        print(f"  capabilities: {caps}")
        print(f"  context:      {ctx}")
        sys.exit(0)

    # stdin is read ONLY when asked. An agent harness can hand the script an
    # open-but-idle pipe, and an unconditional read() then blocks forever.
    stdin_text = ""
    if args.stdin:
        stdin_text = sys.stdin.read().strip()

    prompt = args.prompt or ""
    if stdin_text:
        prompt = f"{prompt}\n\n{stdin_text}" if prompt else stdin_text
    if not prompt:
        print("Error: No prompt provided", file=sys.stderr)
        sys.exit(1)

    if args.image and not os.path.isfile(args.image):
        print(f"Error: Image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    result = query(prompt, system=args.system, image_path=args.image, url=args.url,
                   model=args.model, temperature=args.temp, max_tokens=args.max_tokens,
                   think=args.think)
    print(result)
    if result.startswith("ERROR:"):
        sys.exit(1)


if __name__ == "__main__":
    main()
