---
name: nuke-shot-setup
description: >
  Batch shot setup for Nuke comp projects. Parses a ShotGrid CSV export, reads plate metadata
  from a plates CSV (or scans plates on disk), creates per-shot folder structures, generates
  Nuke v001 visdev/comp files with plates auto-connected (Read + Stamp/Anchor with proper
  ACES colorspace), and produces a Google Sheets-ready CSV shot tracker. Supports multiple
  sequences at once, show-specific config (OCIO, LUT, compression), and configurable work
  context (visdev, comp). Use when the user wants to set up shots, run a batch shot setup,
  start a new sequence, onboard plates, build a shot tracker CSV, or create comps from a CSV.
  Triggers on "set up shots", "batch shot setup", "new sequence", "onboard plates", "shot tracker
  csv", "create comps from csv", "shot setup from ShotGrid", "visdev setup".
allowed-tools: Read,Write,Edit,Bash,Glob,Grep,mcp__nuke__runPythonScript,mcp__nuke__loadScript,mcp__nuke__listNodes,mcp__nuke__getNode
---

# Nuke Shot Setup

Batch setup of Nuke comp/visdev files, folder structures, and shot tracking CSV.

## Script Location

`Nuke/scripts/batch_shot_setup.py`

## Show Configs

`Nuke/configs/<show_name>.json` -- per-show overrides for OCIO, LUTs, viewer, format, etc.
Only values that differ from the script's built-in defaults need to be in the JSON.

**Built-in defaults:** Nuke 15.0 v5, ACEScg in/out, DWAA compression, 4608x3164, 23.976fps. Point the script at your team's OCIO config via the show JSON (`ocio_config` key) - never hardcode a personal or network path in the script itself.

## Network-Drive Policy (adapt to your studio)

Many studios block agent shells from network drives. If yours does, run this
script against a local mirror of the show tree and sync results back through
your studio's approved channel. All paths passed to the script (`--shared`,
`--csv`, `--plates-csv`, `--out`) must be readable from the agent shell -
if plates are missing under the local mirror, the sync has not happened yet;
ask the pipeline owner rather than reaching for the network path directly.

**Show configs:** one JSON per show under `Nuke/configs/`, e.g.
`Nuke/configs/example_show.json` -- override only what differs from the
defaults (a common case: `viewer_process` set to a client-specific Rec.709
output transform).

## Quick Start

Ask the user for:
1. **ShotGrid CSV path**
2. **Project shared path** (root of `05_asset/` and `06_seq/`)
3. **Plates CSV path** (or plates directory for file scanning)
4. **Output directory** for CSV tracker + thumbnails
5. **Show config** (if project-specific OCIO/viewer settings exist)
6. **Shots to skip** (ones that already have files)

### Full run (all sequences, visdev context):

```bash
python Nuke/scripts/batch_shot_setup.py \
  --csv "path/to/ShotGrid.csv" \
  --shared "PROJECT_ROOT/shared" \
  --plates-csv "path/to/plates_metadata.csv" \
  --show-config "Nuke/configs/show_name.json" \
  --out "path/to/output/docs"
```

### Single sequence, comp context (legacy):

```bash
python Nuke/scripts/batch_shot_setup.py \
  --csv "path/to/ShotGrid.csv" \
  --shared "PROJECT_ROOT/shared" \
  --seq ac030 \
  --context comp \
  --plate-prefix source_plate \
  --out "path/to/output/docs"
```

### CLI arguments:

| Arg | Default | Description |
|-----|---------|-------------|
| `--csv` | required | ShotGrid CSV export path |
| `--shared` | required | Project shared root (containing `06_seq/`) |
| `--out` | required | Output directory for CSV tracker |
| `--context` | `visdev` | Work context (`visdev`, `comp`, etc.) |
| `--plates-csv` | none | Plates metadata CSV (avoids file scanning) |
| `--plates-dir` | auto | Plates root dir (defaults to dirname of `--plates-csv`) |
| `--plate-prefix` | `processed_plate` | Subdir/filename prefix for file scanning |
| `--show-config` | none | Show-specific config JSON |
| `--seq` | all | Filter to one sequence |
| `--skip` | none | Shot codes to skip |
| `--csv-only` | false | Only generate CSV tracker |
| `--format-w/h` | from config | Resolution override |
| `--fps` | from config | Frame rate override |
| `--ocio-config` | from config | OCIO config path override |

### Thumbnails (via Nuke MCP):

Thumbnails require Nuke running with MCP. Run this Python script inside Nuke:

```python
# Use mcp__nuke__runPythonScript with this script:
import nuke, os, glob

PLATES_DIR = "path/to/plates/root"
OUT_DIR = "path/to/output/docs/thumbnails"
THUMB_W, THUMB_H = 960, 660
PLATE_PREFIX = "processed_plate"

shots = [...]  # list of shot codes

for shot in shots:
    pattern = os.path.join(PLATES_DIR, shot, PLATE_PREFIX,
                           "{}_{}_{}_raw_v*.*.exr".format(PLATE_PREFIX, shot, "bg01"))
    files = sorted(glob.glob(pattern))
    if not files:
        continue
    first_frame = int(files[0].split(".")[-2])
    # Use the first file to derive the sequence pattern
    sample = os.path.basename(files[0])
    import re
    seq_path = os.path.join(PLATES_DIR, shot, PLATE_PREFIX,
                            re.sub(r'\.\d+\.exr$', '.%04d.exr', sample)).replace("\\", "/")
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

### Verify:

1. Spot-check folder structures: `ls` a few `06_seq/{seq}/{shot}/work/{context}/nuke/`
2. Load 1-2 .nk files via `mcp__nuke__loadScript`, check `mcp__nuke__listNodes` and `mcp__nuke__getNode` on Read nodes
3. Confirm the Write node TCL expression resolves correctly
4. Check Read node colorspace is set to "ACES - ACEScg"

## What the Script Does

### Config Layering

`DEFAULTS` (built-in) <- `--show-config` JSON <- CLI args. Only override what differs.

### CSV Parsing
- Finds the "Shot Code" header row (handles ShotGrid's department grouping header)
- Deduplicates by shot code (ShotGrid exports multiple task rows per shot)
- Extracts: Shot Code, Head In, Cut In, Cut Out, Tail Out, Working Duration, Status, Retime, Description
- Shots without frame data are included in the CSV tracker but skipped for Nuke setup

### Plate Loading
Two modes:
1. **Plates CSV** (`--plates-csv`): reads metadata CSV with columns `Filename, Context, First Frame, Last Frame, Duration`. Derives plate name and subdir from filename pattern. Plates dir defaults to the CSV's parent directory.
2. **File scanning** (fallback): scans `{plates-dir}/{shot}/{plate-prefix}/`, groups by plate name via regex, picks highest version per plate group.

### Sequence Derivation
Sequence code is derived from each shot code: `ac030_0110` -> `ac030`. No `--seq` required for multi-sequence shows. If `--seq` is provided, it filters.

### Nuke File Generation
Each .nk file has:
- **Root**: OCIO/ACES, frame range from bg01 plate, custom OCIO config path
- **Per plate**: BackdropNode + Read (with colorspace) + Anchor (Stamps v1.2) + PostageStamp
- **Processing chain**: PostageStamp (bg01) -> Dot -> Crop -> Write (TCL path) -> Viewer
- **Write node**: 16-bit half EXR, DWAA compression, ACEScg colorspace, TCL expression derives render path from script name (seq + shot + context)
- File saved at: `{shared}/06_seq/{seq}/{shot}/work/{context}/nuke/{shot}_{context}_main_v001.nk`

### CSV Output
Columns match Google Sheets layout:
```
Shot Code | Thumbnail | Sequence | Status | Artist | Notes | Description |
Head In | Cut In | Cut Out | Tail Out | Working Duration | Plates | Plate First | Plate Last | Retime
```

## Adapting for Other Projects

**Per-show (create a JSON show config):**
- `viewer_process` -- what artists see in the viewport
- `ocio_config` -- OCIO config path (if different from team default)
- `write_view` -- Write node display view
- `format_w`, `format_h` -- resolution
- Any other value from DEFAULTS

**Per-run (CLI args):**
- `--context` -- visdev vs comp
- `--plates-csv` / `--plates-dir` / `--plate-prefix` -- plate source
- `--seq` -- sequence filter
- `--skip` -- shots to skip

**Baked into the template (edit `batch_shot_setup.py`):**
- Node graph layout / positioning
- Stamps v1.2 knob structure
- Write node TCL expression pattern
