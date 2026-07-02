---
name: magnific-video-gen
description: Magnific MCP video generation skill. Use when generating video via Magnific, selecting video models, animating stills, using start/end keyframes, camera motion, audio/lipsync, multishot, or video upscale. Triggers on: "generate video with magnific", "magnific video", "animate this image", "magnific camera motion", "seedance", "kling video", "veo video", "video from still".
allowed-tools: mcp__magnific__video_plan,mcp__magnific__video_generate,mcp__magnific__video_models_list,mcp__magnific__video_models_show,mcp__magnific__video_concatenate,mcp__magnific__video_upscale,mcp__magnific__creations_wait,mcp__magnific__creations_show,mcp__magnific__creations_get,mcp__magnific__folders_list,mcp__magnific__folders_create,mcp__magnific__account_balance
---

# Magnific Video Generation Skill

## Before Generating — Routing and Session Rules

1. **Routing check:** on production jobs with ComfyUI API-node credits, video generation is usually cheaper via ComfyUI (`comfy generate --api-key` headless, or the workflow UI) — Magnific video is for tests, personal work, or when its models/features are specifically wanted. Confirm the route if a production job is active.
2. **Confirm the destination folder** before generating (teams accumulate multiple similarly-named project folders). Never generate into the workspace root.
3. **On an auth/re-authorization error, stop — don't retry.** Tell the user to run `/mcp` to re-authenticate, then resume. Presigned upload URLs go stale across re-auth; re-request them.
4. **Default audio OFF** — audio generation costs significantly more; only enable when the user asks.

## Skill Pairing — Seedance Prompt System

The `seedance-20` skill ecosystem handles **prompt writing and shot direction**. Use it before generating via Magnific for better results.

| Goal | Use first |
|------|-----------|
| Vague idea, need creative direction | `seedance-interview` or `seedance-interview-short` |
| Write/improve a Seedance prompt | `seedance-prompt` or `seedance-prompt-short` |
| Camera move / shot language | `seedance-camera` |
| Remove generic AI filler from prompt | `seedance-antislop` |
| VFX effects in the video | `seedance-vfx` |
| Bad result, diagnosing | `seedance-troubleshoot` |

**Workflow:** Seedance skills → polished prompt → `magnific-video-gen` for MCP execution.

---

## Mandatory First Step

**Always call `video_plan` before `video_generate`.** Skip only if the user explicitly says "just generate" or "one-shot".

`video_plan` returns: brief summary, open questions, recommended model slug, prompt draft, and multi-clip instructions for videos >15s.

```python
video_plan(
    prompt="raw user idea — pass verbatim",
    aspectRatioHint="16:9",
    durationHint=6,
    styleHint="cinematic photorealistic",
    referenceIdentifiers=["<creation_id>"]  # if attaching refs
)
```

---

## Priority Models for VFX Work

| Model | Slug | Speed | Best For |
|-------|------|-------|----------|
| **Seedance 2.0** ✅ DEFAULT | `bytedance-seedance-pro-2.0` | ~5 min | Best overall — camera controls, audio, lipsync, multishot, image/video refs |
| Seedance 2.0 Fast | `bytedance-seedance-fast-2.0` | ~5 min | Draft rounds — same controls as Pro, 720p max |
| Kling 3.0 | `kling-30` | ~10 min | 4K, 15s, character/product refs, multishot (6) |
| Kling 3.0 Omni | `kling-omni3` | ~10 min | 4K, video-to-video reference (style from existing footage) |
| Kling 2.5 | `kling-25` | ~10 min | Best value, reliable start+end frame control |
| LTX 2 Fast | `ltx-ltx2-fast` | ~60s | Fastest option, up to 2160p, 20s max, 16:9 only |
| Veo 3.1 | `google-veo3_1` | ~5 min | Start+end keyframes, image refs, 1080p, sound effects |
| MiniMax 2.3 | `minimax-video-2_3` | ~10 min | Precise camera motion keywords, 1080p |

---

## Seedance 2.0 — Full Capabilities

### Specs
- **Resolutions:** 1080p, 720p, 480p
- **Durations:** 4–15 seconds
- **Aspect ratios:** `21:9` `16:9` `4:3` `1:1` `3:4` `9:16`
- **Multishot:** up to 6 shots (use `multi_prompt` array)
- **Sound effects:** OFF by default — only enable if user explicitly requests audio (`withSoundEffects: true`). Audio generation is significantly more expensive.
- **Native audio/lipsync:** pass audio as `references[]` with `type: "audio"` — also requires explicit user request

### Camera Motion (52 values)
**Lateral:** `truckLeft` `truckRight` `panLeft` `panRight` `moveLeft` `moveRight`
**Push/Pull:** `pushIn` `pullOut` `superDollyIn` `superDollyOut` `crashZoomIn` `doubleDolly`
**Vertical:** `pedestalUp` `pedestalDown` `tiltUp` `tiltDown` `moveUp` `moveDown` `jibUp` `jibDown` `craneUp` `craneDown` `craneOverTheHead` `upwardTilt` `downwardTilt`
**Zoom:** `zoomIn` `zoomOut`
**Orbit/Rotate:** `orbitLeft` `orbitRight` `360Orbit` `leftCircling` `rightCircling`
**Specialty:** `fisheye` `overhead` `objectPov` `whipPan` `dutchAngle` `fpvDrone` `handheld` `headTracking` `snorricam`
**Lens FX:** `dirtyLens` `lensCrack` `lensFlare` `focusChange` `lowShutter`
**Walk:** `leftWalking` `rightWalking`
**Other:** `static` `stageLeft` `stageRight` `scenicShot`

### Reference Types
| Type | Limit | Notes |
|------|-------|-------|
| `image` | 9 | Prohibited with keyframes |
| `video` | 3 | Prohibited with keyframes |
| `character` | 1 | Library asset |
| `product` | 1 | Library asset |
| `style` | 1 | Style reference image |
| `color` | — | Color reference |
| `effect` | — | Effect reference |
| `audio` | 3 | For lipsync/voiceover — requires a visual reference too |

---

## Critical: Keyframes vs References

**Keyframes (start/end frames) ALWAYS go in `keyframes.{start,end}`, NEVER in `references[]`.**

```python
# CORRECT — image-to-video with start frame
video_generate(video={"clips": [{
    "slug": "bytedance-seedance-pro-2.0",
    "prompt": "...",
    "aspectRatio": "16:9",
    "duration": 6,
    "resolution": "1080p",
    "cameraMotion": "pushIn",
    # withSoundEffects omitted — OFF by default, only add if user requests audio
    "keyframes": {
        "start": {"type": "image", "url": "<creation_id or asset URL>"}
    }
}]})

# WRONG — never put keyframes in references[]
```

For Seedance 2.0: if using `keyframes`, you cannot also use `image` or `video` in `references[]` — they are mutually exclusive.

---

## Generation Patterns

### Image-to-video (I2V) — most common VFX use
```python
video_generate(video={"clips": [{
    "slug": "bytedance-seedance-pro-2.0",
    "prompt": "Slow cinematic push-in...",
    "aspectRatio": "16:9",
    "duration": 6,
    "resolution": "1080p",
    "cameraMotion": "pushIn",
    "keyframes": {
        "start": {"type": "image", "url": "<NB2_Pro_creation_id>"}
    }
}]}, folderReference="61610b02-59bc-460b-a3af-73739f0f2b32")  # audio OFF by default
```

### Text-to-video (T2V)
```python
video_generate(video={"clips": [{
    "slug": "bytedance-seedance-pro-2.0",
    "prompt": "...",
    "aspectRatio": "16:9",
    "duration": 8,
    "resolution": "1080p",
    "cameraMotion": "handheld"
    # withSoundEffects omitted — only add if user explicitly requests audio
}]})
```

### Multishot (up to 6 shots in one clip)
```python
video_generate(video={"clips": [{
    "slug": "bytedance-seedance-pro-2.0",
    "aspectRatio": "16:9",
    "resolution": "1080p",
    "multi_prompt": [
        {"index": 1, "prompt": "Wide establishing shot...", "duration": 4},
        {"index": 2, "prompt": "Medium shot pushing in...", "duration": 4},
        {"index": 3, "prompt": "Close detail on marquee...", "duration": 4}
    ]
}]})
```

### With audio reference (lipsync/voiceover)
Requires a visual reference (keyframe or image ref):
```python
references=[
    {"type": "audio", "url": "<audio_creation_id_or_url>"}
],
keyframes={"start": {"type": "image", "url": "<face_image_id>"}}
```

### Video-to-video (Kling 3.0 Omni)
```python
video_generate(video={"clips": [{
    "slug": "kling-omni3",
    "prompt": "...",
    "aspectRatio": "16:9",
    "duration": 5,
    "resolution": "1080p",
    "references": [
        {"type": "video", "url": "<source_video_creation_id>"}
    ]
}]})
```

---

## Long Videos (>15s) — Multi-Clip

`video_plan` auto-generates a split plan. Then:
1. Generate each clip separately with `video_generate`
2. Use `creations_wait` to get final asset URLs
3. Stitch with `video_concatenate`

---

## Folder Structure (claude code tests)

| Path | Reference |
|------|-----------|
| claude code tests/video | `61610b02-59bc-460b-a3af-73739f0f2b32` |

Always save video to the project's video folder via `folderReference`.

---

## Post-Generation

### Wait for asset URL (needed for chaining)
```python
creations_wait(identifiers=["<id>"], timeoutSeconds=25)
# Returns asset URL when complete — use for video_concatenate or upscale
```

### Upscale
```python
video_upscale(creationIdentifier="<id>")
```

---

## VFX Previs Workflow

1. **Generate still** — NB2 Pro via `magnific-image-gen` skill
2. **Plan video** — `video_plan` with still as `referenceIdentifiers`
3. **Generate** — Seedance 2.0, start keyframe = NB2 Pro result, choose camera motion
4. **Review** — share `webUrl`, check motion and consistency
5. **Iterate** — adjust prompt/camera, or use result as input for next shot
6. **Upscale** — `video_upscale` on approved clip
7. **Concatenate** — `video_concatenate` if multi-clip
8. **Export** — asset URL for Nuke composite or Kling downstream
