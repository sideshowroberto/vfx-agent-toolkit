---
name: magnific-local-upload
description: "Upload local images to Magnific as references for generation, then download outputs to a local folder. Use when user wants to upload photos from a local folder or drive, use local files as image/style references in Magnific, batch upload from a directory, move uploads to a Magnific folder, or save/download Magnific generated images to a local path. Triggers: \"upload local images\", \"use local photos as reference\", \"upload from folder\", \"upload these images to magnific\", \"download magnific output\", \"save generated image to folder\", \"local ref upload\"."
allowed-tools: mcp__magnific__creations_request_upload,mcp__magnific__creations_finalize_upload,mcp__magnific__creations_move,mcp__magnific__creations_get,mcp__magnific__creations_show,mcp__magnific__creations_wait,mcp__magnific__images_generate,mcp__magnific__images_variations,mcp__magnific__folders_list,Bash,Glob,Write
---

# Magnific Local Upload Skill

**Version:** 1.1.0
**Last Updated:** 2026-06-09

Handles the full pipeline: local folder → upload to Magnific → move to folder → use as generation references → download output to local folder.

---

## Upload Architecture

Magnific does **not** accept file paths directly. Local files require a 3-step presigned upload:

```
1. creations_request_upload(mimeType, count=N)  →  N presigned PUT URLs + temp paths
2. Python: PUT each file's bytes to its directUploadUrl (GCS)
3. creations_finalize_upload(uploads=[...paths])  →  creation identifiers
```

`creations_upload_file` is for host-attached files (ChatGPT-style uploads) — it does **not** work for local disk files. Always use the 3-step flow.

---

## Critical: Use directUploadUrl, NOT proxyUploadUrl

Each `creations_request_upload` response includes two PUT targets:
- `directUploadUrl` — GCS (`storage.googleapis.com`) — **use this always**
- `proxyUploadUrl` — Magnific proxy — **unreliable, returns 503/404 in batch operations**

Always PUT to `directUploadUrl`.

---

## MIME Type Map

| Extension | mimeType |
|-----------|----------|
| `.jpg` / `.jpeg` | `image/jpeg` |
| `.png` | `image/png` |
| `.webp` | `image/webp` |
| `.mp4` | `video/mp4` |
| `.mov` | `video/quicktime` |
| `.webm` | `video/webm` |

---

## Workflow 1 — Batch Upload from Folder

**Step 1: Scan folder with Glob**
```
Glob(pattern="D:/path/to/folder/*.png")
```

**Step 2: Request all presigned URLs in one call**
```python
creations_request_upload(mimeType="image/png", count=8)
# Returns: { uploads: [ {directUploadUrl, path}, ... ] }
```

Request the full batch count upfront — all URLs expire in 1 hour, so get them all before starting uploads.

**Step 3: Write and run a Python upload script**

Write to `tmp/magnific_upload.py`, execute immediately:

```python
import urllib.request, pathlib, sys

# Pair each local file with its directUploadUrl and temp path
pairs = [
    (r"D:\path\to\file1.png", "<directUploadUrl_1>", "temp-files/<uuid1>.png"),
    (r"D:\path\to\file2.png", "<directUploadUrl_2>", "temp-files/<uuid2>.png"),
    # ... one entry per file
]

paths = []
for filepath, url, path in pairs:
    name = pathlib.Path(filepath).name
    data = pathlib.Path(filepath).read_bytes()
    req = urllib.request.Request(url, data=data, method="PUT")
    req.add_header("Content-Type", "image/png")
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"OK {resp.status}  {name}")
            paths.append(path)
    except Exception as e:
        print(f"FAIL  {name}  {e}", file=sys.stderr)

print("\nPATHS:")
for p in paths: print(p)
```

Run with: `python tmp/magnific_upload.py`

All successful files print `OK 200`. Failed files print to stderr. Only pass 200-OK paths to finalize.

**Step 4: Batch finalize**
```python
creations_finalize_upload(uploads=[
    {"path": "temp-files/<uuid1>.png"},
    {"path": "temp-files/<uuid2>.png"},
    # ... all OK paths
])
# Returns: { results: [ {identifier, status: "completed"}, ... ] }
```

**Step 5: Move to a Magnific folder**
```python
creations_move(
    creationIdentifiers=["id1", "id2", ...],
    targetFolderReference="<folder_ref>"
)
```

`creations_finalize_upload` has no folder targeting — uploads land in root. Always call `creations_move` immediately after. See the `magnific-image-gen` skill for known folder references.

---

## Workflow 2 — Single File Upload

For one file, use an inline heredoc instead of writing a script:

```python
# Request 1 URL (omit count)
creations_request_upload(mimeType="image/jpeg")
```

Then run Python inline via Bash:
```bash
python - <<'EOF'
import urllib.request, pathlib
data = pathlib.Path(r"D:\path\to\file.jpg").read_bytes()
req = urllib.request.Request("<directUploadUrl>", data=data, method="PUT")
req.add_header("Content-Type", "image/jpeg")
with urllib.request.urlopen(req) as r:
    print(f"OK {r.status}")
EOF
```

Then finalize:
```python
creations_finalize_upload(path="temp-files/<uuid>.jpg")
```

---

## Workflow 3 — Generate with Uploaded Refs + Download

**Generate:**
```python
images_generate(
    prompt="...",
    mode="imagen-nano-banana-2",
    aspectRatio="16:9",
    resolution="2k",
    count=2,
    folderReference="<output_folder_ref>",   # goes directly into Magnific folder
    references=[
        {"type": "image", "identifier": "<previs_or_comp_ref>"},  # composition lock
        {"type": "style", "identifier": "<real_photo_ref_1>"},    # photorealism look
        {"type": "style", "identifier": "<real_photo_ref_2>"},
    ]
)
```

**Wait — `creations_wait` returns the URL directly:**
```python
result = creations_wait(identifiers=["<id>"])
# result.results[0].results.url  ← full-res URL, no need to call creations_get
```

Only call `creations_get` if you need metadata beyond the URL.

**Download:**
```bash
python - <<'EOF'
import urllib.request, pathlib
url = "<url_from_creations_wait>"
out = r"D:\path\to\output\result.png"
pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
urllib.request.urlretrieve(url, out)
data = pathlib.Path(out).read_bytes()
is_webp = data[:4] == b'RIFF' and data[8:12] == b'WEBP'
print(f"Saved {len(data)/1024/1024:.1f} MB  WebP={is_webp}")
EOF
```

**WebP check:** If `WebP=True`, convert before using in Nuke:
```bash
python -c "from PIL import Image; Image.open('result.png').convert('RGB').save('result_conv.jpg', format='JPEG', quality=95)"
```

> **Nuke 16/17 does not support WebP.** Always check and convert if pulling into Nuke.

---

## Workflow 4 — Variations on a Generation

After a successful generation, run variations to explore looks:

```python
images_variations(
    creationIdentifier="<id_of_successful_generation>",
    variationMode="custom",
    prompt="Describe what to vary — lighting, mood, angle, etc.",
    gridRows=2,
    gridCols=2,    # 2x2 = 4 tiles; max 9 total
    resolution="2k"
)
# Returns a single creation identifier for the grid image
```

Wait and download the same way as a generation. The grid is one image — pick a tile visually, then use it as an `image` reference in the next generation pass.

---

## NSFW Filter — Action/Violence Content

Magnific's NSFW filter triggers on **style references** that contain:
- Fighting, brawling, combat scenes
- Weapons (chairs, ladders, bats)
- Crowd violence or chaos

**Workaround:** Use action/violence content as `image` type (composition) rather than `style`. The filter is stricter on style references. If NSFW keeps triggering, remove those refs from style and use only calm, photographic refs for style.

For combat-sports / action content specifically — use the stills as `image` refs only, never `style`.

---

## Full Pipeline Summary

```
1.  Glob local folder           → collect paths
2.  creations_request_upload    → get N presigned URLs (count=N)
3.  Write tmp/magnific_upload.py → pair files to directUploadUrls
4.  python tmp/magnific_upload.py → PUT all files, collect OK paths
5.  creations_finalize_upload   → batch finalize → get identifiers
6.  creations_move              → move to target Magnific folder
7.  images_generate             → use identifiers as references, folderReference for output
8.  creations_wait              → poll until complete, get URL from results
9.  urllib.request.urlretrieve  → download to local output folder
10. WebP check + convert if needed
```

**Ask user before running:**
- Source folder path
- Output local folder path
- Target Magnific folder (or use default `gen` folder)
- Prompt
- Reference type per image (`image` = composition/mood, `style` = look transfer)
- Model (default: `imagen-nano-banana-2`)
- Resolution (default: `2k`) / aspect ratio

---

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| PUT returns 503/404 | Using proxyUploadUrl | Switch to directUploadUrl (GCS) |
| PUT returns non-200 on GCS | Expired presigned URL (>1hr) | Re-request upload URLs, re-run |
| `creations_finalize_upload` error | PUT didn't complete before finalize | Check Python script output for FAIL lines |
| Generation fails NSFW | Style ref contains violence/weapons | Move that ref to `image` type or remove it |
| `creations_wait` never completes | Polling too short | Keep calling with timeoutSeconds=25 until `allTerminal: true` |
| Downloaded file is 0 bytes | URL expired | Call `creations_get` to get a fresh URL |
| WebP in Nuke | CDN serving WebP regardless of URL extension | Run Pillow convert |

---

## Related Skills

- **`magnific-image-gen`** — generation workflow, model selection, folder map, upscaling, variations
- **`magnific-video-gen`** — video generation with Magnific
