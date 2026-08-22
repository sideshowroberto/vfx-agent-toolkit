---
name: magnific-image-gen
description: "Magnific MCP image generation skill. Use when generating ANY images, concept art, product shots, reference images, or visual assets - Magnific is the default image generation tool. Also use for selecting models, resolution/aspect ratio, adding references, browsing/creating folders, upscaling, or generating variations. Triggers on: \"generate image\", \"generate images\", \"generate refs\", \"generate reference\", \"reference images\", \"image refs\", \"generate concept\", \"product shot\", \"concept art\", \"make me an image\", \"make references\", \"generate with magnific\", \"magnific image\", \"nb2\", \"nano banana\", \"magnific folder\", \"upscale\", \"magnific variations\", \"render me\", \"create an image\", \"hero shots\"."
allowed-tools: mcp__magnific__images_generate,mcp__magnific__images_models_list,mcp__magnific__images_models_show,mcp__magnific__creations_show,mcp__magnific__creations_wait,mcp__magnific__creations_search,mcp__magnific__creations_get,mcp__magnific__folders_list,mcp__magnific__folders_create,mcp__magnific__images_upscale,mcp__magnific__images_variations,mcp__magnific__account_balance,mcp__magnific__library_list,mcp__magnific__library_show,mcp__magnific__creations_upload_image
---

# Magnific Image Generation Skill

## Account Context

- **Preferred models:** Nano Banana 2 Pro and Flash - use these by default for concept work
- Check balance and plan coverage with `account_balance` if the user asks or before heavy batch runs (Pro unlimited plans cover NB2 at 1K/2K with no credit burn; 4K costs credits)

## Two Rules Before Any Generation

1. **Confirm the destination folder.** Team workspaces often have multiple similarly-named project folders (several people may each have created one for the same show). Before a batch run, state which folder you are generating into and confirm it - including the right subfolder (e.g. a per-artist subfolder). Never generate into the workspace root.
2. **On an auth/re-authorization error, stop - do not retry.** Magnific MCP sessions expire mid-task. The error is not transient: tell the user to run `/mcp` and re-authenticate, then resume from where you left off (re-request any presigned upload URLs, which go stale).

---

## Model Selection Protocol

**Always check models before generating if the user has not specified one.**

```
1. Call images_models_list (optionally with search= to filter)
2. Read agentRecommendation fields
3. Default to NB2 Pro (high quality) or NB2 Flash (faster iteration)
4. Only use other models if the user has a specific reason
```

### Priority Models for This Account

**Default: NB2 Pro (`imagen-nano-banana-2`) for everything. Only drop to Flash if the user explicitly asks for faster iteration.**

| Model | Slug | Speed | Best For |
|-------|------|-------|----------|
| **Nano Banana 2 Pro** [OK] DEFAULT | `imagen-nano-banana-2` | ~50s | All concept and final work - default choice |
| Nano Banana 2 Flash | `imagen-nano-banana-2-flash` | ~34s | When user wants faster iteration or batch drafts |
| Cinematic | `cinematic` | ~46s | Cinematic stills, when 4k quality is the priority |
| GPT 2 | `gpt-2` | ~69s | Text/typography/infographics (not photorealistic) |
| Flux.1 Kontext Max | `flux-kontext-high` | ~13s | Quick edits with image refs when speed matters |

**Never use `auto` mode** - it picks random models (e.g. Seedream) instead of NB2. Always specify a slug explicitly.

---

## Nano Banana 2 - Capabilities Reference

### Resolutions
`1k` | `2k` | `4k`
- Default to `2k` for concept work (unlimited plan covers it)
- Use `4k` for final/hero assets

### Aspect Ratios
**NB2 Pro:** `auto` `1:1` `21:9` `16:9` `9:16` `4:3` `4:5` `5:4` `3:4` `3:2` `2:3`
**NB2 Flash:** `auto` `1:1` `21:9` `8:1` `4:1` `16:9` `9:16` `1:4` `1:8` `4:3` `4:5` `5:4` `3:4` `3:2` `2:3`

Common VFX ratios:
- Widescreen: `16:9`
- Anamorphic: `21:9`
- Portrait/social: `9:16`
- Square concept: `1:1`

### Reference Types (NB2 Pro and Flash both support all 5)
| Type | What it does | Source |
|------|-------------|--------|
| `image` | Carries composition, mood, and color palette from source - confirmed strong influence | creation identifier |
| `style` | Style/look transfer | creation identifier or library style LoRA id |
| `character` | Character consistency across generations | library asset numeric `id` |
| `product` | Product/object consistency | library asset numeric `id` |
| `composition` | Layout/structure reference | creation identifier |

**Important:** `character`, `product`, and `locations` use the numeric `id` from `library_list`, NOT a creation identifier. `image`, `style`, and `composition` use creation identifiers.

**Model support varies:** not every model accepts every reference type - NB2 has rejected `composition` references with "The selected references.N.type is invalid". When passing structural refs (depth maps, layout frames) to NB2, send them as plain `image` type instead.

**Confirmed workflow:** You can use any prior generation as an `image` reference in the next pass - even cross-model (e.g. Seedream output -> NB2 Pro). NB2 Pro picks up composition and mood well from the reference.

---

## Generation Workflow

### Basic generation
```python
images_generate(
    prompt="...",
    mode="imagen-nano-banana-2",        # NB2 Pro
    aspectRatio="16:9",
    resolution="2k",
    count=1,
    folderReference="<confirmed_folder_ref>"  # see Two Rules: always confirm destination first
)
```

### With image references
```python
images_generate(
    prompt="...",
    mode="imagen-nano-banana-2-flash",
    aspectRatio="16:9",
    resolution="2k",
    references=[
        {"type": "image", "identifier": "<creation_id>"},
        {"type": "style", "identifier": "<creation_id>"}
    ]
)
```

### After generating
- Always call `creations_show(identifiers=[...])` to display results inline
- Share `webUrl` so user can open in the Magnific app
- Use `creations_wait` only when you need the asset URL for chaining (upscale, video, etc.)

---

## Folder Navigation

### Discovering Projects
Call `folders_list(onlyProjects=true)` to list projects - folder references are stable UUIDs, so once discovered for an account they can be reused. Keep a per-account project->reference map in memory (a `reference` memory file) rather than re-listing every session, and refresh it when a lookup misses.

### List contents of a folder
```python
folders_list(parentReference="<folder_ref>")
```

### Create a new project at workspace root
```python
folders_create(name="Project Name", type="project")
```

### Create a subfolder inside a project
```python
folders_create(name="Subfolder Name", parentReference="<project_ref>")
```

### Browse creations in a folder
```python
creations_search(from="folder", reference="<folder_ref>")
```

---

## Post-Generation Tools

### Upscale
```python
images_upscale(creationIdentifier="<id>", scale="2x")  # or "4x"
```
Use `creations_wait` first if the generation is still in progress.

### Variations grid
```python
images_variations(
    creationIdentifier="<id>",
    variationMode="custom",    # angles|demographics|expressions|age|storyboard|custom
    prompt="Vary lighting mood, camera angle, atmosphere - keep same location",
    gridRows=2,
    gridCols=2,
    resolution="2k"
)
```
- `storyboard` and `custom` modes require a `prompt`
- Max 9 tiles (rows x cols must be <= 9)
- **`custom` mode confirmed reliable** for environment/look exploration
- The grid is one image - download it, pick a tile visually, then use that as an `image` reference in the next generation pass
- Download with `creations_wait` -> URL -> `urllib.request.urlretrieve` (same as any generation)

### Search existing creations
```python
creations_search(from="history", query="street scene")
creations_search(from="folder", reference="<folder_ref>", fileType="image")
```

---

## Library Assets (Characters, Products, Styles)

Pre-built reusable assets for consistent references:
```python
library_list(type="character")   # character|style|element|locations
library_show()                   # Opens inline picker UI for user to browse and select
```
Pass the numeric `id` (not the string `identifier`) in `references[]` for `character`, `product`, and `locations` types.

---

## Upload External Images as References

To use a local or web-hosted image as a reference:
```python
creations_upload_image(url="<image_url>")
# Returns a creation identifier - use that in references[]
```

---

## NSFW Filter - Action/Violence Style References

The NSFW filter triggers on **`style` references** containing fighting, combat, weapons, or crowd violence (e.g. combat-sports stills, post-apocalyptic action scenes). The filter is stricter on style refs than on `image` refs.

**Workaround:** Use action/violence content as `image` type (composition lock) only - never `style`. Use calm photographic refs for style.

---

## Technical Notes (Magnific API behaviour)

### Resolution - Constant-Area Formula
Magnific uses constant-area math, not simple pixel multiplication. Dimensions are floored to 64px:
```python
area     = res * res           # e.g. 2048*2048 for 2K
long_raw = sqrt(area * long_ratio / short_ratio)
short_raw = area / long_raw
long_px  = int(long_raw  / 64) * 64
short_px = int(short_raw / 64) * 64
```
Example: 9:16 at 2K -> `width=1536, height=2688` (not 2048x2048)

### Thumbnail URLs lie about aspect ratio - check the real file first
The CDN serves two thumbnail formats: `render.png?preview=1` **crops to square**, while `render-preview.jpg` preserves the true aspect ratio. If generations "look like the wrong aspect ratio," download the actual render (via `creations_wait` URL) and check its real dimensions BEFORE debugging prompts or parameters - the renders are almost always correct and only the preview is cropped.

### The `resolution` API field is required
The `resolution` string (`"1k"`, `"2k"`, `"3k"`, `"4k"`) must be sent alongside pixel `width`/`height`.
Without it, the API ignores dimensions and returns wrong output size. The MCP handles this automatically.

### Unlimited (inf) vs Credit-burning
- NB2 Pro at 1K, 2K: unlimited (inf) - no credit cost
- NB2 Pro at 4K: costs credits
- The model list reports `inf` for sizes the plan covers as unlimited - check yours with `images_models_settings`

### WebP Output - Nuke Pipeline Warning
Magnific CDN sometimes serves WebP even when the URL ends in `.jpg`. **Nuke 16 and 17 do not support WebP natively.** If pulling Magnific outputs directly into Nuke (bypassing the MCP), you must detect and convert:
```python
if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
    # Convert via Pillow before saving
    from PIL import Image
    Image.open(io.BytesIO(data)).convert('RGB').save(out_path, format='JPEG', quality=95)
```
Build this check into any custom Read-side importer you write.

---

## VFX Concept Round Workflow

1. **Pick model** - NB2 Flash for speed, NB2 Pro for finals. Never use `auto`.
2. **Generate batch** - `count=4`, save to relevant project folder
3. **Show results** - `creations_show(identifiers=[...])`
4. **Iterate** - add references from picked results, tighten prompt, regenerate
5. **Upscale hero** - `images_upscale(scale="4x")` on the winner
6. **Export/share** - `webUrl` for review or pass asset URL to downstream tools (Nuke, ComfyUI)
