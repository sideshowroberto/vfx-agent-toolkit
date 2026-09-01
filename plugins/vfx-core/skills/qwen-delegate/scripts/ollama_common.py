#!/usr/bin/env python3
"""
Shared helpers for the qwen-delegate scripts: server discovery, model
auto-detection, and capability checks. No pip dependencies.

Model resolution order (first hit wins):
  1. --model on the command line
  2. LOCAL_LLM_MODEL environment variable
  3. Non-Ollama server (vLLM / llama-server / LM Studio): "local"
  4. Ollama: the team installer tags, strongest first (PREFERRED_TAGS)
  5. Ollama: any tag whose name starts with "qwen"
  6. Ollama: the first tag on the server

The team installers create exactly one of the PREFERRED_TAGS per machine,
chosen by GPU memory (24 GB+ gets the 27B, smaller cards get the 14B), so on
a teammate's box step 4 is the one that usually fires.
"""

import json
import os
import urllib.error
import urllib.request

DEFAULT_URL = os.environ.get("LOCAL_LLM_URL", "http://localhost:11434")

# Team installer tags, strongest first. Extend here if the installer adds a variant.
PREFERRED_TAGS = [
    "vfx-qwen38-27b-262k",   # workstation variant: 24 GB+ VRAM, 262K context, vision + tools
    "vfx-qwen3-14b-16k",     # a4000 variant: <24 GB VRAM, 16K context, text + tools, NO vision
]


def is_ollama(url):
    return "11434" in url


def list_models(url=DEFAULT_URL, timeout=3):
    """Return the model names the server advertises. Raises on connection failure."""
    if is_ollama(url):
        endpoint = f"{url}/api/tags"
    else:
        endpoint = f"{url}/v1/models"
    with urllib.request.urlopen(endpoint, timeout=timeout) as resp:
        data = json.loads(resp.read())
    if is_ollama(url):
        return [m.get("name", "") for m in data.get("models", [])]
    return [m.get("id", "") for m in data.get("data", [])]


def health_check(url=DEFAULT_URL, timeout=3):
    """Fast preflight. Returns (ok, detail_string)."""
    try:
        names = list_models(url, timeout)
        return True, f"server up at {url}; models: {', '.join(names) or 'none'}"
    except Exception as e:
        return False, (
            f"Local LLM server NOT reachable at {url} ({e})\n"
            "  Ollama normally auto-starts on login. Start it manually with:  ollama serve\n"
            "  Then confirm a Qwen tag is installed with:                     ollama list\n"
            "  (The team Qwen installer creates vfx-qwen38-27b-262k or vfx-qwen3-14b-16k.)\n"
            "  Another server? Set LOCAL_LLM_URL / --url and LOCAL_LLM_MODEL / --model."
        )


def resolve_model(url=DEFAULT_URL, requested=None):
    """Pick the model to use. Returns (model_name, reason). Raises RuntimeError if none."""
    if requested:
        return requested, "from --model"
    env = os.environ.get("LOCAL_LLM_MODEL")
    if env:
        return env, "from LOCAL_LLM_MODEL"
    if not is_ollama(url):
        return "local", "non-Ollama server, using served name 'local'"

    names = list_models(url)
    for tag in PREFERRED_TAGS:
        for name in names:
            if name == tag or name.startswith(tag + ":"):
                return name, "team installer tag"
    for name in names:
        if name.lower().startswith("qwen"):
            return name, "first qwen tag on server"
    if names:
        return names[0], "first tag on server"
    raise RuntimeError(
        "Ollama is running but has no models. Run the team Qwen installer, or:\n"
        "  ollama pull qwen3:8b   (small, text-only, fine for boilerplate)"
    )


def model_info(url, model, timeout=10):
    """Capabilities and baked context length for an Ollama tag.

    Returns dict(capabilities=[...], num_ctx=int|None). Non-Ollama servers and
    lookup failures return empty capabilities so callers fail open.
    """
    info = {"capabilities": [], "num_ctx": None}
    if not is_ollama(url):
        return info
    try:
        req = urllib.request.Request(
            f"{url}/api/show",
            data=json.dumps({"model": model}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        info["capabilities"] = data.get("capabilities", []) or []
        for line in (data.get("parameters", "") or "").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[0] == "num_ctx":
                info["num_ctx"] = int(parts[1])
    except Exception:
        pass
    return info


def check_vision(url, model):
    """Return None if the model can take images, else a human-readable reason."""
    caps = model_info(url, model)["capabilities"]
    if not caps:
        return None  # unknown server or lookup failed: let the request try
    if "vision" in caps:
        return None
    return (
        f"Model '{model}' is text-only (capabilities: {', '.join(caps)}).\n"
        "  The 14B team variant cannot analyse images. Options:\n"
        "    - describe the image in words instead of attaching it\n"
        "    - use a vision-capable tag with --model (e.g. the 27B variant on a bigger card)"
    )


def encode_image(path):
    """Return (base64_data, mime_type) for an image file."""
    import base64
    ext = os.path.splitext(path)[1].lower()
    mime = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext)
    if mime is None:
        raise ValueError(
            f"Unsupported image type '{ext}'. Convert to png/jpg/webp first "
            "(EXR/TIFF plates: write a PNG from Nuke or ffmpeg)."
        )
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8"), mime
