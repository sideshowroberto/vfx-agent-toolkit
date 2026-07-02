---
name: magnific-nuke-node
description: MagnificAI Nuke Group node — complete reference for building, modifying, debugging, or extending the MagnificAI.nk ToolSet. Node sends prompts and Nuke input images to Magnific AI and returns results as a Read node inside the group. Uses Chrome browser cookies (no API key). Installed at ~/.nuke/ToolSets/MagnificAI.nk. Use when asked about: MagnificAI node, Magnific inside Nuke, ExportWrite, GeneratedResult, postage stamp refresh, cookie extraction, Windows DPAPI, install_deps, refresh_cookies, Magnific API flow, WebP conversion, resolution knob, model list, cancel pattern, or thumbnail arrows.
allowed-tools: Read,Write,Edit,Bash
---

# Rob's install path
- **ToolSet:** `~/.nuke/ToolSets/MagnificAI.nk`
- **Dependencies:** `~/.nuke/Python/site-packages/py{major}{minor}/` (run `install_deps` once per Nuke version)
- **Cookie refresh:** Click "Login / Refresh Session" in the Setup tab after Chrome session expires

# MagnificAI Nuke Node — Complete Reference

## Overview

A Nuke **Group node** that:
1. Exports Nuke input frames via an internal `ExportWrite` Write node (JPEG, 85% quality)
2. Uploads optional image reference inputs to Magnific
3. Calls Magnific's AI image generation API using browser session cookies (no API key)
4. Saves the generated image to disk
5. Loads it back via an internal `GeneratedResult` Read node
6. Updates the node's postage stamp thumbnail automatically

**Toolset file location (Windows):** `C:/Users/vcerquei/.nuke/ToolSets/MagnificAI.nk`
**Toolset file location (macOS):** `~/.nuke/ToolSets/MagnificAI.nk`

**Dependencies path (version-specific):** `~/.nuke/Python/site-packages/py{major}{minor}/`  
- e.g. Nuke 17 (Python 3.11) → `py311/`, Nuke 16 (Python 3.10) → `py310/`  
- Prevents compiled-extension conflicts when multiple Nuke versions share a machine  
- Each Nuke version installs into its own isolated dir; run `install_deps` once per version

---

## Internal Node Structure

Inside the group:
- **`Input`** nodes — Nuke inputs (Input 0 = main image optional, Input 1+ = image references)
- **`ExportWrite`** — Write node (JPEG, 85% quality)
- **`GeneratedResult`** — Read node (JPEG) displaying AI output
- **`Output`** — passes GeneratedResult downstream

---

## Knobs on the Group

| Knob name | Type | Purpose |
|---|---|---|
| `icon_header` | Label (HTML) | Magnific icon + title + "Image Generator" subtitle |
| `icon_data` | String (hidden) | Base64-encoded Magnific favicon PNG |
| `add_input` | PyScript_Knob | Add an image reference input |
| `remove_input` | PyScript_Knob | Remove last image reference input |
| `div_ref_hint` | Label | " " (space label for alignment) + hint text about @img1, @img2… |
| `prompt` | Multiline_Eval_String_Knob | Text prompt |
| `model` | Enumeration | **Same row**: Model → Aspect Ratio → Size (no labels on AR/Size) |
| `aspect_ratio` | Enumeration | `-STARTLINE`, no label. Options: 1:1, 16:9, 9:16, 4:3, 3:4 |
| `size` | Enumeration | `-STARTLINE`, no label. Options change per model (see Size Knob section) |
| `smart_prompt` | Boolean | Enable Magnific's smart prompt enhancement |
| `seed` | Int_Knob | Generation seed (INVISIBLE) |
| `seed_control` | Enumeration | "randomize" / "fixed" / "increment" / "decrement" |
| `generate` | PyScript_Knob | Main generate button (green) |
| `gen_count` | Int_Knob | Number of generations to queue (same row as generate) |
| `status` | Label (HTML) | Status message. Default: "Ready". Resets to Ready 4s after completion |
| `progress` | String_Knob | e.g. "42%" |
| `cancel_btn` | PyScript_Knob | Cancel — sets `_cancel` True |
| `export_colorspace` | **Link_Knob** → `ExportWrite.colorspace` | Colorspace for input export |
| `output_path` | File_Knob | Where to save generated images |
| `open_folder` | PyScript_Knob | Opens output folder in Explorer/Finder |
| `thumb_img` | Label (HTML) | Thumbnail of current result, or placeholder if no image yet |
| `thumb_counter` | String_Knob (hidden) | e.g. "3 / 7" |
| `thumb_prev` | PyScript_Knob | ◀ — go to previous result |
| `thumb_next` | PyScript_Knob | ▶ — go to next result |
| `thumb_read` | PyScript_Knob | Add current thumbnail as Read node to graph |
| `setup_group` | Tab_Knob | **Collapsible group** (`TABBEGINCLOSEDGROUP`, closed by default, no title) |
| `install_deps` | PyScript_Knob | Install cryptography + Chrome registry fix + opens Chrome for login (Windows only chains into login) |
| `refresh_cookies` | PyScript_Knob | "Login / Refresh Session" — closes Chrome, reads cookies, reopens Chrome |
| `setup_group_end` | Tab_Knob | `TABENDGROUP` |
| `_cancel` | Boolean_Knob (hidden) | Cancel flag for background thread |
| `_result_file` | EvalString_Knob (INVISIBLE) | Current output path |
| `cookie_path` | File_Knob (hidden) | Fallback shared cookie file path |

### Knob Layout Note
`model`, `aspect_ratio`, and `size` are all on the **same row**:
- `model`: normal label "Model", starts its own line
- `aspect_ratio`: `-STARTLINE`, label `""` (empty)
- `size`: `-STARTLINE`, label `""` (empty)

---

## Model List

```python
_MODEL_MAP = {
    'Auto':            'auto',           # Magnific picks best model; shown in filename/status
    'Nano Banana 2':   'imagen-nano-banana-2',
    'Seedream 5 Lite': 'seedream-5-lite',
}
```

Other models (Nano Banana 2 Flash, Mystic, Seedream 4.5, etc.) are accessible via **Auto** — Magnific
selects them automatically. When Auto is used, the actual model is captured from
`_s['metadata']['mode']` at completion and shown in:
- The output **filename**: `output_v001_seedream-4-5.jpg`
- The **status bar**: `Done: output_v001_seedream-4-5.jpg [seedream-4-5]`

---

## Size Knob — Per-Model Options

The `size` dropdown updates automatically when the user changes the `model` knob (via `knobChanged`).
If the current size is invalid for the new model, it snaps to `2K ∞`.

| Model | Size options |
|---|---|
| **Auto** | `1K ∞`, `2K ∞`, `3K ∞`, `4K` |
| **Nano Banana 2** | `1K ∞`, `2K ∞`, `4K` |
| **Seedream 5 Lite** | `2K ∞`, `3K ∞`, `4K ∞` |

∞ = unlimited (no credits). `4K` without ∞ = costs credits.

### knobChanged model→size logic

```python
if _nk.thisKnob().name() == 'model':
    _m = _n['model'].value()
    _inf = chr(0x221e)
    _cur = _n['size'].value()
    if _m == 'Nano Banana 2':
        _n['size'].setValues(['1K ' + _inf, '2K ' + _inf, '4K'])
        if '3K' in _cur: _n['size'].setValue('2K ' + _inf)
    elif _m == 'Seedream 5 Lite':
        _n['size'].setValues(['2K ' + _inf, '3K ' + _inf, '4K ' + _inf])
        if '1K' in _cur: _n['size'].setValue('2K ' + _inf)
    else:
        _n['size'].setValues(['1K ' + _inf, '2K ' + _inf, '3K ' + _inf, '4K'])
```

### Resolution calculation (in generate script)

Uses **constant-area formula** — same as the Magnific website. Dimensions floored to nearest 64px.

```python
_size_val   = node['size'].value() if node.knob('size') else '1K'
_res        = (2048 if '2K' in _size_val else 3072 if '3K' in _size_val
               else 4096 if '4K' in _size_val else 1024)
_resolution = ('2k' if '2K' in _size_val else '3k' if '3K' in _size_val
               else '4k' if '4K' in _size_val else '1k')
_ar_dims    = {'1:1':(1,1),'16:9':(16,9),'9:16':(9,16),'4:3':(4,3),'3:4':(3,4)}
_arw, _arh  = _ar_dims.get(_ar, (1,1))
import math as _math
_area       = _res * _res
_long_raw   = _math.sqrt(_area * max(_arw,_arh) / min(_arw,_arh))
_short_raw  = _area / _long_raw
_long_px    = int(_long_raw  / 64) * 64
_short_px   = int(_short_raw / 64) * 64
_width      = _long_px  if _arw >= _arh else _short_px
_height     = _short_px if _arw >= _arh else _long_px
```

Example — 9:16 at 2K: `_long_px=2688, _short_px=1536` → `width=1536, height=2688` ✓

The `resolution` string (`"2k"`, `"3k"`, `"4k"`, `"1k"`) is sent as a separate field in the render body
alongside the actual pixel `width`/`height`. Both are required.

---

## Auth Strategy — No API Key, No Browser Tab Required

Both platforms read Chrome cookies directly from disk. The user only needs to be logged into
`magnific.com` in Chrome at least once. When the session expires, click **Login / Refresh Session**.

### macOS — Direct Cookie Extraction

```python
def _get_cookies_mac():
    # 1. Get key from macOS Keychain
    pw = subprocess.check_output(
        ['security', 'find-generic-password', '-w', '-s', 'Chrome Safe Storage', '-a', 'Chrome'],
        stderr=subprocess.DEVNULL
    ).strip()
    # 2. Derive AES key via PBKDF2-SHA1
    key = hashlib.pbkdf2_hmac('sha1', pw, b'saltysalt', 1003, 16)
    # 3. Decrypt: strip v10 header, AES-CBC decrypt, strip 32-byte Chrome prefix, strip PKCS7
    def _dec(enc_val):
        if enc_val[:3] == b'v10':
            raw = (Cipher(AES(key), CBC(b' '*16)).decryptor()
                   .update(enc_val[3:]) + decryptor.finalize())[32:]
            return raw[:-raw[-1]].decode('utf-8', errors='replace')
```

**Key insight:** Chrome prepends a 32-byte random prefix → strip `raw[32:]` after AES-CBC.

### Windows — DPAPI + AES-GCM (ctypes, no pywin32)

```python
def _get_cookies_windows():
    # 1. Read encrypted AES key from Local State
    enc_key = base64.b64decode(ls['os_crypt']['encrypted_key'])[5:]  # strip 'DPAPI'

    # 2. Decrypt with DPAPI via ctypes (no pywin32 needed)
    class _BLOB(ctypes.Structure):
        _fields_ = [('cbData', DWORD), ('pbData', POINTER(c_char))]
    ib = _BLOB(len(enc_key), cast(c_char_p(enc_key), POINTER(c_char)))
    ob = _BLOB()
    ctypes.windll.crypt32.CryptUnprotectData(byref(ib), None, None, None, None, 0, byref(ob))
    key = string_at(ob.pbData, ob.cbData)

    # 3. Decrypt cookies with AES-GCM; strip 32-byte prefix
    raw = AESGCM(key).decrypt(ev[3:15], ev[15:], None)
    value = raw[32:].decode('utf-8')  # strip 32-byte prefix (same as macOS)
```

**One-time registry fix required** (done by `install_deps`):
```
reg add "HKLM\SOFTWARE\Policies\Google\Chrome" /v ApplicationBoundEncryptionEnabled /t REG_DWORD /d 0 /f
```
Without this, Chrome's Application-Bound Encryption blocks DPAPI decryption.

**Fallback:** If SQLite read fails, falls back to shared cookie file at:
`<COOKIE_DIR>/magnific_cookies.txt`

### Session Expiry

```python
def _check_auth_error(e):
    if hasattr(e, 'code') and e.code in (401, 403):
        raise RuntimeError('Magnific session expired.\n\nPlease log in via Login / Refresh Session.')
```

---

## Setup Buttons

### `install_deps` (Windows flow)
1. `pip install cryptography` → `~/.nuke/Python/site-packages/py{major}{minor}/`
2. `pip install Pillow` → same path (enables WebP→JPEG conversion; non-fatal if it fails)
3. Applies Chrome registry fix — **skipped** if `ApplicationBoundEncryptionEnabled=0` already set
4. Opens Chrome at `magnific.com`
5. Shows dialog: "Log in then click OK"
6. On OK → automatically executes `refresh_cookies` button

### `refresh_cookies` ("Login / Refresh Session")
1. Closes Chrome gracefully (taskkill, waits up to 15s)
2. Reads + decrypts cookies from Chrome SQLite on disk
3. Saves to `<COOKIE_DIR>/magnific_cookies.txt`
   and `~/.nuke/magnific_cookies.txt`
4. Reopens Chrome if it was open

Both buttons live inside a **collapsed Tab group** (`TABBEGINCLOSEDGROUP`) with no title.
In `.nk` format: `addUserKnob {20 setup_group l "" -STARTLINE n 2}` / `n -1`

---

## HTTP Helpers

```python
_HEADERS = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip, deflate, br',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 ...',
    'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
    'sec-fetch-dest': 'empty', 'sec-fetch-mode': 'cors', 'sec-fetch-site': 'same-origin',
    ...
}
```

Without `sec-ch-ua` / `sec-fetch-*`, Magnific's Akamai WAF returns 403.

---

## Magnific API Flow

### Step 1 — Start (`POST start-tti-v2`)
```
POST https://www.magnific.com/app/api/start-tti-v2?lang=en_US&user_id={uid}
Body: { aspect_ratio, color_palette: null, force_credits: false, mode, num_images: 1,
        prompt, references: [], variations: false }
Returns: { family, request_tokens: [...] }
```

### Step 2 — Render (`POST render/v4`)
```
POST https://ak-data.magnific.com/app/api/render/v4
Body:
{
  tool: "text-to-image",  mode,  family,
  prompt,  negative_prompt: null,
  width,  height,                          ← actual pixels (constant-area formula)
  seed,  aspect_ratio,  resolution,        ← "1k"/"2k"/"3k"/"4k" — REQUIRED field
  thinking_level: "minimal",  use_google_search_tool: false,
  request_token,  force_credits: false,
  metadata: { aspectRatio, inputPrompt, mode, unlimited: true, smartPrompt },
  smart_prompt,  image_index: 0,  num_images: 1,
}
Returns: { creation: { id } }
```

**Critical:** `resolution` field is required. Without it the API ignores width/height and returns
wrong dimensions.

### Step 3 — Poll (`GET creation/{id}`)
```
GET https://www.magnific.com/app/api/creation/{id}?lang=en_US&user_id={uid}
```
Poll every 2s until `status == "completed"`.
Returns `{ url: "https://..." }` — CDN URL, publicly downloadable (no auth needed).

**Auto model detection:**
```python
if _s.get('status') == 'completed':
    _actual_model = (_s.get('metadata') or {}).get('mode') or _model
```

---

## Image Reference Upload

```python
def _upload_ref(tmp_jpg, uid, cookie_str, xsrf):
    boundary, body = _make_multipart(
        [('tool', 'upload-reference')],
        [('file', 'input.jpg', 'image/jpeg', img_data)]
    )
    # POST to https://ak-data.magnific.com/app/api/creations
    # Returns { identifier: "abc123" }
    # Use as "creation:abc123" in body['image_references'][].image
```

---

## Auto Model Detection + Filename/Status

When model is set to **Auto**, the actual model chosen by Magnific is read from the API response
and shown in the filename and status bar:

```python
_model_suffix = ''
if node['model'].value() == 'Auto' and _actual_model not in ('auto', 'Auto', ''):
    _model_suffix = '_' + _actual_model
# → output_v001_seedream-4-5.jpg

_done_msg = 'Done: ' + os.path.basename(_out_file)
if node['model'].value() == 'Auto' and _actual_model not in ('auto', 'Auto', ''):
    _done_msg += ' [' + _actual_model + ']'
```

---

## Status Reset

After generation completes, the status bar shows "Done: filename [model]" for **4 seconds** then
resets to "Ready". Uses a daemon thread + `nuke.executeInMainThread`.

**Critical:** The node reference becomes stale after postage stamp repaste (delete+paste cycle).
Must re-fetch by name:

```python
_node_name = node.name()
def _reset_status():
    import time as _t; _t.sleep(4)
    def _do():
        _n = nuke.toNode(_node_name)   # re-fetch — node reference stale after repaste
        if _n:
            _n['status'].setValue('Ready')
            _n['progress'].setValue('')
    nuke.executeInMainThread(_do)
threading.Thread(target=_reset_status, daemon=True).start()
```

---

## Placeholder Thumbnail

Shown in `thumb_img` when panel opens and no image generated yet (`_result_file` is empty).
Set in `knobChanged` on `showPanel`:

```python
if _nk.thisKnob().name() == 'showPanel':
    if not _n['_result_file'].value().strip():
        _n['thumb_img'].setValue('<div style="background:#111;...">✦ No image generated yet</div>')
```

**Critical:** In `.nk` knobChanged strings, `[` must be `\[` or TCL parser silently breaks it.

---

## Postage Stamp Refresh

Runs after each generation via `nuke.executeInMainThread(_refresh_stamp)`:

```python
def _refresh_stamp():
    nuke.root().begin()
    # select node, nodeCopy('%clipboard%'), delete, nodePaste('%clipboard%')
    # restore xpos/ypos, inputs, outputs, reopen panel
    nuke.root().end()
    _new.showControlPanel()
```

---

## Cancel Pattern

```python
node['_cancel'].setValue(False)   # reset before starting loop
def _run_loop():
    for _li in range(_n_times):
        if node['_cancel'].value(): break
        _run(_li, _n_times)
    if node['_cancel'].value():
        _prog('Cancelled', 0)
        node['_cancel'].setValue(False)   # only clear here, never inside _run()
threading.Thread(target=_run_loop, daemon=True).start()
```

---

## Saving the .nk

Only reliable method from within Nuke (nodeCopy silently fails in group context):

```python
flags = nuke.TO_SCRIPT | nuke.WRITE_ALL | nuke.WRITE_USER_KNOB_DEFS
outer = mag_node.writeKnobs(flags)
inner = ''
mag_node.begin()
try:
    for n in nuke.allNodes():
        inner += ' ' + n.Class() + ' {\n'
        for line in n.writeKnobs(nuke.TO_SCRIPT | nuke.WRITE_ALL).strip().splitlines():
            inner += '  ' + line + '\n'
        inner += ' }\n'
finally:
    mag_node.end()
nk_content = ('set cut_paste_input [stack 0]\nversion 17.0 v1\npush $cut_paste_input\nGroup {\n'
              + outer + '}\n' + inner + 'end_group\n')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(nk_content)
```

---

## WebP Detection and Conversion

Magnific CDN sometimes serves images as WebP even when the URL ends in `.jpg`.
Nuke 16 and 17 do **not** support WebP natively (`webp` is not in Nuke's `file_type` list).

The generate script detects the actual format from magic bytes and converts via Pillow if available:

```python
def _detect_fmt(data):
    if data[:3] == b'\xff\xd8\xff': return 'jpg'
    if data[:4] == b'\x89PNG':      return 'png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP': return 'webp'
    return ''
_fmt = _detect_fmt(_img_data)
if _fmt == 'webp':
    try:
        import io as _io
        from PIL import Image as _Img
        _buf = _io.BytesIO()
        _Img.open(_io.BytesIO(_img_data)).convert('RGB').save(_buf, format='JPEG', quality=95)
        _img_data = _buf.getvalue()
        _fmt = 'jpg'
    except ImportError:
        pass  # PIL not available — file saved as .webp, Nuke will error on it
_base, _ext = os.path.splitext(_out)
_ext = ('.' + _fmt) if _fmt else (_ext or '.jpg')
```

**Install Pillow** via the `install_deps` button — it pip-installs into the version-specific
site-packages path so Nuke can import it. Pillow install failures are non-fatal (warn only).

## Known Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| 4K square output | Missing `resolution` field in API body | Add `resolution: "4k"` alongside pixel `width`/`height` |
| Wrong output dimensions | Sending equal `width=height=res` regardless of aspect ratio | Use constant-area formula: `long = sqrt(res² × long_ratio/short_ratio)`, floor to 64 |
| 403 on API call | Akamai WAF blocking | Add `sec-ch-ua`, `sec-fetch-*` headers |
| Session expired | 401/403 response | `_check_auth_error()` → friendly message |
| Windows cookie decrypt fails | Chrome Application-Bound Encryption | Registry fix: `ApplicationBoundEncryptionEnabled=0` |
| Placeholder not showing | `[` not escaped in knobChanged | Use `\[` and `\]` in all `.nk` knobChanged strings |
| Status stuck on "Done" | Node reference stale after postage stamp repaste | Re-fetch node by name with `nuke.toNode(_node_name)` |
| macOS cookie garbled | Chrome 32-byte random prefix | Strip `raw[32:]` after AES-CBC decrypt |
| `loadToolset` error on opening from ToolSets menu | Empty `""` option appended to `aspect_ratio` enum (external edit leaves `M {1:1 16:9 9:16 4:3 3:4 ""}`) | Remove the trailing `""` from the enum list in the `.nk` file |
| `.jpg` file error in Nuke ("not a .jpg file") | Magnific CDN served WebP but URL ended in `.jpg`; Nuke 16/17 don't support WebP | Magic-byte detection + Pillow converts to JPEG automatically (install via `install_deps`) |

---

## Icon

Magnific favicon PNG, stored base64 in `icon_data` knob. Always use `data:image/png;base64,` URI —
never a file path (breaks on macOS / shared drives).
