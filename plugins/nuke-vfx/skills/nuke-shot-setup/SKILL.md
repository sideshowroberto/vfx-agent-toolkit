---
name: nuke-shot-setup
description: >
  Batch shot setup for Nuke comp projects. Parses a ShotGrid CSV export, scans plates on disk,
  creates per-shot folder structures, generates Nuke v001 comp files with plates auto-connected
  (Read + Stamp/Anchor), extracts first-frame thumbnails via Nuke MCP, and produces a Google
  Sheets-ready CSV shot tracker. Use when the user wants to set up shots, run a batch shot setup,
  start a new sequence, onboard plates, build a shot tracker CSV, or create comps from a CSV.
  Triggers on "set up shots", "batch shot setup", "new sequence", "onboard plates", "shot tracker
  csv", "create comps from csv", "shot setup from ShotGrid".
allowed-tools: Read,Write,Edit,Bash,Glob,Grep,mcp__nuke__runPythonScript,mcp__nuke__loadScript,mcp__nuke__listNodes,mcp__nuke__getNode
---

# Nuke Shot Setup

Batch setup of Nuke comp files, folder structures, thumbnails, and shot tracking CSV.

## Script Location

`Nuke/scripts/batch_shot_setup.py` — the reusable CLI tool. The generated .nk layout is a static template based on your show's template comp (edit the `gen_*` functions to match yours).

## Quick Start

Ask the user for:
1. **ShotGrid CSV path**
2. **Project shared path** (root of `05_asset/` and `06_seq/`)
3. **Sequence code** (e.g. `sq010`)
4. **Output directory** for CSV + thumbnails
5. **Shots to skip** (ones that already have comps)

Then run three steps:

### Step 1: Nuke Files + Folders + CSV

```bash
python Nuke/scripts/batch_shot_setup.py \
  --csv "path/to/Shot.csv" \
  --shared "PROJECT_ROOT/shared" \
  --seq sq010 \
  --out "path/to/output/docs" \
  --skip sq010_0010
```

Optional overrides: `--format-w`, `--format-h`, `--fps`, `--ocio-config`

### Step 2: Thumbnails (via Nuke MCP)

Thumbnails require Nuke running with MCP. Run this Python script inside Nuke:

```python
# Use mcp__nuke__runPythonScript with this script:
import nuke, os, glob

PLATES_DIR = "PROJECT_ROOT/shared/05_asset/plates"
OUT_DIR = "path/to/output/docs/thumbnails"
THUMB_W, THUMB_H = 960, 660

shots = [...]  # list of shot codes

for shot in shots:
    pattern = os.path.join(PLATES_DIR, shot, "source_plate",
                           "source_plate_{}_bg01_raw_v001.*.exr".format(shot))
    files = sorted(glob.glob(pattern))
    if not files:
        continue
    first_frame = int(files[0].split(".")[-2])
    seq_path = os.path.join(PLATES_DIR, shot, "source_plate",
                            "source_plate_{}_bg01_raw_v001.%04d.exr".format(shot)).replace("\\", "/")
    out_path = os.path.join(OUT_DIR, "{}_bg01_thumb.png".format(shot)).replace("\\", "/")

    nuke.scriptClear()
    read = nuke.createNode("Read", inpanel=False)
    read["file"].setValue(seq_path)
    read["first"].setValue(first_frame)
    read["last"].setValue(first_frame)
    read["origfirst"].setValue(first_frame)
    read["origlast"].setValue(first_frame)

    reformat = nuke.createNode("Reformat", inpanel=False)
    reformat["type"].setValue("to box")
    reformat["box_width"].setValue(THUMB_W)
    reformat["box_height"].setValue(THUMB_H)
    reformat["box_fixed"].setValue(True)
    reformat["filter"].setValue("Lanczos6")

    write = nuke.createNode("Write", inpanel=False)
    write["file"].setValue(out_path)
    write["file_type"].setValue("png")
    write["datatype"].setValue("8 bit")

    nuke.execute(write, first_frame, first_frame)
```

### Step 3: Verify

1. Spot-check folder structures: `ls` a few `06_seq/{seq}/{shot}/work/comp/nuke/`
2. Load 1-2 .nk files via `mcp__nuke__loadScript`, check `mcp__nuke__listNodes` and `mcp__nuke__getNode` on Read nodes
3. Confirm thumbnails exist and are non-zero: `ls -la {out}/thumbnails/`

## What the Script Does

### CSV Parsing
- Finds the "Shot Code" header row (handles ShotGrid's department grouping header)
- Extracts: Shot Code, Head In, Cut In, Cut Out, Tail Out, Working Duration, Status, Retime, Description
- Shots without frame data are included in the CSV tracker but skipped for Nuke setup
- **ShotGrid export gotcha:** some columns (e.g. "Retime") are checkboxes in ShotGrid and export
  as True/False — the actual human-readable data often lives in a different column (e.g.
  "Editorial Info"). The parser prefers "Editorial Info" and falls back to "Retime". Inspect the
  CSV before trusting column names.

### Plate Scanning
- Scans `{shared}/05_asset/plates/{shot}/source_plate/`
- Groups files by plate name via regex: `source_plate_{shot}_(bg\d+)_raw_v\d+\.(\d+)\.exr`
- Extracts first/last frame from actual files on disk

### Nuke File Generation
Static template based on a reference show comp — adapt it to your show's template comp. Each .nk has:
- **Root**: OCIO/ACES, frame range from bg01 plate on disk
- **Per plate**: BackdropNode + Read + Anchor (Stamps v1.2) + PostageStamp
- **Processing chain**: PostageStamp (bg01) → Dot → Crop → Write (TCL path) → Viewer
- Plate groups at 292px horizontal spacing
- Unique anchor IDs via md5 hash

### CSV Output
Columns match Google Sheets layout:
```
Shot Code | Thumbnail | Sequence | Status | Artist | Notes | Description |
Head In | Cut In | Cut Out | Tail Out | Working Duration | Plates | Plate First | Plate Last | Retime
```

## Adapting for Other Projects

Things that change per project (use CLI args):
- `--format-w`, `--format-h` — resolution
- `--fps` — frame rate
- `--ocio-config` — OCIO config path
- `--skip` — shots that already exist

Things that are baked into the template (edit `Nuke/scripts/batch_shot_setup.py` DEFAULTS dict):
- Nuke version/DLL path
- Monitor LUT names
- Write display/view names
- Viewer process name

If a project uses a different plate naming convention, edit the `scan_plates()` regex.
