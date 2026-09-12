---
name: nuke-shot-setup
description: Batch shot setup for Nuke comp projects. Parses a ShotGrid CSV export, reads plate metadata from a plates CSV (or scans plates on disk), creates per-shot folder structures, generates Nuke v001 visdev/comp files with plates auto-connected (Read + Stamp/Anchor with proper ACES colorspace), and produces a Google Sheets-ready CSV shot tracker. Supports multiple sequences at once, show-specific config (OCIO, LUT, compression), and configurable work context (visdev, comp). Use when the user wants to set up shots, run a batch shot setup, start a new sequence, onboard plates, build a shot tracker CSV, or create comps from a CSV. Triggers on "set up shots", "batch shot setup", "new sequence", "onboard plates", "shot tracker csv", "create comps from csv", "shot setup from ShotGrid", "visdev setup".
allowed-tools: Read,Write,Edit,Bash,Glob,Grep,mcp__nuke__runPythonScript,mcp__nuke__loadScript,mcp__nuke__listNodes,mcp__nuke__getNode
---

# Nuke Shot Setup

**Version:** 1.1.0

Batch setup of Nuke comp/visdev files, folder structures, and shot tracking CSV.

## Script Location

`scripts/batch_shot_setup.py` (paths in this skill are relative to the skill directory)

## Show Configs

`configs/<show_name>.json` -- per-show overrides for OCIO, LUTs, viewer, format, etc.
Only values that differ from the script's built-in defaults need to be in the JSON.
`--show-config` may be repeated and is applied in order, so the standard call is
`--show-config configs/studio_defaults.json --show-config configs/<show>.json`
(team defaults first, show overrides second; later files win). Start a show
file from `configs/show_template.json`.

**Built-in defaults:** Nuke 17.0 v2, ACEScg in/out, DWAA compression, 4608x3164, 23.976fps, and **no OCIO config**. The script prints the effective Nuke version and OCIO path at the top of every run and warns when OCIO is unset - point it at your team's config via `studio_defaults.json` (`ocio_config` key). A path baked into the script is always somebody's personal path on somebody else's machine.

**An empty `ocio_config` is not neutral by itself.** The warning only covers
the `ocio_config` key - the other colour keys (`ACES - ACEScg` read/write
colorspace, the `Output - K1S1-like - Rec.709` viewer process, monitor LUTs)
still default to ACES-specific names even when no OCIO config is set to
resolve them. A run with `ocio_config` empty therefore still writes those
ACES names, and the generated comp opens with "Bad value for viewerProcess"
and every Read in error ("Invalid LUT selected : ACES - ACEScg") under
plain `nuke-default`. Interim rule until this is fixed in the script: EITHER
always pass a real `ocio_config` (never run with it empty), OR set
`colorManagement` to `Nuke` and the Read/Write colorspaces to a linear
default by hand in your show config when no studio config exists yet.
**Read-back step, every run:** open one generated `.nk` with
`nuke -t --safe <script.nk>` and assert `Read1.error()` is False before
calling the run done - a correct node count and correct plate paths do not
prove the comp opens without a colour error. Open follow-up: make
`batch_shot_setup.py` fall back to a coherent nuke-default colour set
(no ACES names) when `ocio_config` is empty, instead of leaving the other
keys ACES-specific.

## Network-Drive Policy (adapt to your studio)

Many studios block agent shells from network drives. If yours does, run this
script against a local mirror of the show tree and sync results back through
your studio's approved channel. All paths passed to the script (`--shared`,
`--csv`, `--plates-csv`, `--out`) must be readable from the agent shell -
if plates are missing under the local mirror, the sync has not happened yet;
ask the pipeline owner rather than reaching for the network path directly.

**Show configs:** one JSON per show under `configs/`, e.g.
`configs/example_show.json` -- override only what differs from the
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
python scripts/batch_shot_setup.py \
  --csv "path/to/ShotGrid.csv" \
  --shared "PROJECT_ROOT/shared" \
  --plates-csv "path/to/plates_metadata.csv" \
  --show-config "configs/<show_name>.json" \
  --out "path/to/output/docs"
```

### Single sequence, comp context (legacy):

```bash
python scripts/batch_shot_setup.py \
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
| `--show-config` | none | Config JSON; repeatable, applied in order (studio defaults, then show) |
| `--seq` | all | Filter to one sequence |
| `--skip` | none | Shot codes to skip |
| `--csv-only` | false | Only generate CSV tracker |
| `--format-w/h` | from config | Resolution override |
| `--fps` | from config | Frame rate override |
| `--ocio-config` | from config | OCIO config path override |

### Thumbnails (headless, no MCP needed):

`scripts/make_shot_thumbnails.py` runs inside `nuke -t --safe`, takes the
same plates CSV and plates dir, writes `{shot}_{plate}_thumb.png` (the name the
tracker's Thumbnail column expects), reads every PNG back, and exits 1 if any
failed:

```
"C:\Program Files\Nuke17.0v2\Nuke17.0.exe" -t --safe scripts/make_shot_thumbnails.py --plates-csv <plates.csv> --plates-dir <plates root> --out <out>/thumbnails [--ocio-config <config.ocio>]
```

### Thumbnails (alternative, via Nuke MCP):

If you prefer to drive a GUI Nuke over MCP, run this Python inside Nuke:

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
