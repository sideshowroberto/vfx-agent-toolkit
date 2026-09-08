"""
Batch Shot Setup -- General Purpose (v2)
Creates folder structures, Nuke v001 visdev/comp files with plates auto-connected
(Read + Stamp/Anchor), and a Google Sheets-ready CSV tracker.

Usage:
    # All sequences, visdev context, using plates CSV. --show-config may be
    # repeated: studio/team defaults first, then the show's own overrides
    # (later files win). Built-in defaults carry NO OCIO config - supply one.
    python batch_shot_setup.py \
      --csv SHOTGRID.csv --shared /path/to/shared \
      --plates-csv /path/to/plates.csv \
      --show-config Nuke/configs/studio_defaults.json \
      --show-config Nuke/configs/show.json \
      --out /path/to/output

    # Single sequence, comp context (legacy mode):
    python batch_shot_setup.py \
      --csv SHOTGRID.csv --shared /path/to/shared --seq sq010 \
      --context comp --plate-prefix source_plate --out /path/to/output

    # Skip existing shots:
    python batch_shot_setup.py ... --skip ac030_0110 ac030_0120

ShotGrid CSV columns:
    Shot Code, Head In, Cut In, Cut Out, Tail Out, Working Duration, Status, etc.

Plates CSV (optional, from processed plates delivery):
    Filename, Context, First Frame, Last Frame, Duration

If --plates-csv is not provided, plates are scanned from disk at:
    {plates-dir}/{shot}/{plate-prefix}/

Nuke files are created at:
    {shared}/06_seq/{sequence}/{shot}/work/{context}/nuke/
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path


# -- Defaults (ACEScg / K1S1 standard, Nuke 17) -------------------------
# Override with one or more --show-config JSON files (studio defaults, then
# the show), or per-run with CLI args. LUT / display / view names must
# match your OCIO config. "ocio_config" is deliberately EMPTY here: a
# built-in path is always somebody's personal path on somebody else's
# machine. Put the team's config in a studio_defaults.json and pass it.

DEFAULTS = {
    "format_w": 4608,
    "format_h": 3164,
    "fps": "23.976",
    "nuke_version": "17.0 v2",
    "nuke_dll": "C:/Program Files/Nuke17.0v2/nuke-17.0.2.dll",
    "ocio_config": "",
    "monitor_lut": "ACES/sRGB",
    "monitor_out_lut": "sRGB (ACES)",
    "viewer_process": "Output - K1S1-like - Rec.709",
    "write_display": "FS",
    "write_view": "Output - K1S1-like - Rec.709",
    "write_compression": "DWAA",
    "read_colorspace": "ACES - ACEScg",
    "write_colorspace": "ACES - ACEScg",
}


# -- Helpers -------------------------------------------------------------

def make_anchor_id(shot: str, plate_name: str) -> str:
    h = hashlib.md5(f"{shot}_{plate_name}".encode()).hexdigest()[:10]
    return f"Anchor_{h}"


def make_stack_var(shot: str, plate_name: str) -> str:
    h = hashlib.md5(f"stack_{shot}_{plate_name}".encode()).hexdigest()[:8]
    return f"N{h}"


def sequence_from_shot(shot_code: str) -> str:
    """Derive sequence code from shot code: ac030_0110 -> ac030."""
    return shot_code.rsplit("_", 1)[0]


# -- CSV Parsing ---------------------------------------------------------

def parse_csv(csv_path: str, sequence_filter: str = None) -> list[dict]:
    """Parse ShotGrid CSV export. Returns list of shot dicts, deduplicated."""
    shots = []
    seen_codes = set()
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if "Shot Code" in line:
            header_idx = i
            break

    if header_idx is None:
        print("ERROR: Could not find 'Shot Code' column in CSV")
        sys.exit(1)

    reader = csv.DictReader(lines[header_idx:])
    for row in reader:
        code = row.get("Shot Code", "").strip()
        if not code or code in seen_codes:
            continue
        seen_codes.add(code)

        head_in = row.get("Head In", "").strip()
        if not head_in:
            shots.append({
                "code": code,
                "has_frames": False,
                "status": row.get("Status", "").strip().upper() or "WTG",
                "retime": row.get("Editorial Info", row.get("Retime", "")).strip(),
                "description": row.get("Description", "").strip(),
                "head_in": "", "cut_in": "", "cut_out": "",
                "tail_out": "", "working_dur": "",
            })
            continue

        shots.append({
            "code": code,
            "has_frames": True,
            "head_in": int(head_in),
            "cut_in": int(row.get("Cut In", "").strip() or 0),
            "cut_out": int(row.get("Cut Out", "").strip() or 0),
            "tail_out": int(row.get("Tail Out", "").strip() or 0),
            "working_dur": int(row.get("Working Duration", "").strip() or 0),
            "status": row.get("Status", "").strip().upper() or "WTG",
            "retime": row.get("Editorial Info", row.get("Retime", "")).strip(),
            "description": row.get("Description", "").strip(),
        })

    if sequence_filter:
        shots = [s for s in shots if s["code"].startswith(sequence_filter)]

    return shots


# -- Plate Scanning ------------------------------------------------------

def scan_plates_from_csv(plates_csv_path: str, plates_dir: Path) -> dict[str, list[dict]]:
    """Parse plates metadata CSV. Returns {shot: [{name, first, last, path}, ...]}."""
    all_plates = {}
    with open(plates_csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["Filename"].strip()
            shot = row["Context"].strip()
            first = int(row["First Frame"].strip())
            last = int(row["Last Frame"].strip())

            # Derive plate name and subdir from filename using known shot code
            # e.g. processed_plate_ac030_0110_bg01_raw_v002.%04d.exr
            parts = filename.split(f"_{shot}_", 1)
            if len(parts) != 2:
                continue
            prefix = parts[0]
            plate_name = parts[1].split("_raw_")[0]

            plate_path = str(plates_dir / shot / prefix / filename).replace("\\", "/")

            all_plates.setdefault(shot, []).append({
                "name": plate_name,
                "first": first,
                "last": last,
                "path": plate_path,
            })

    for shot in all_plates:
        all_plates[shot].sort(key=lambda p: p["name"])

    return all_plates


def scan_plates(plates_dir: Path, shot: str,
                plate_prefix: str = "source_plate") -> list[dict]:
    """Scan disk for plates. Picks highest version per plate group."""
    plate_dir = plates_dir / shot / plate_prefix
    if not plate_dir.exists():
        return []

    files = sorted(os.listdir(plate_dir))
    if not files:
        return []

    plate_groups: dict[str, list[tuple]] = {}
    pattern = re.compile(
        rf"{re.escape(plate_prefix)}_\w+_(bg\d+)_raw_v(\d+)\.(\d+)\.exr"
    )
    for f in files:
        m = pattern.match(f)
        if m:
            plate_name = m.group(1)
            version = int(m.group(2))
            frame = int(m.group(3))
            plate_groups.setdefault(plate_name, []).append((f, version, frame))

    plates = []
    for name in sorted(plate_groups.keys()):
        entries = plate_groups[name]
        max_version = max(e[1] for e in entries)
        version_entries = sorted(
            [(f, v, fr) for f, v, fr in entries if v == max_version],
            key=lambda e: e[2],
        )
        first_frame = version_entries[0][2]
        last_frame = version_entries[-1][2]
        sample = version_entries[0][0]
        plate_path = str(
            plate_dir / re.sub(r"\.\d+\.exr$", ".%04d.exr", sample)
        ).replace("\\", "/")

        plates.append({
            "name": name, "first": first_frame,
            "last": last_frame, "path": plate_path,
        })

    return plates


# -- .nk Generation -----------------------------------------------------

WINDOW_LAYOUT = """<?xml version="1.0" encoding="UTF-8"?>
<layout version="1.0">
    <window x="0" y="0" w="2237" h="1180" screen="0">
        <splitter orientation="1">
            <split size="40"/>
            <dock id="" hideTitles="1" activePageId="Toolbar.1">
                <page id="Toolbar.1"/>
            </dock>
            <split size="1574" stretch="1"/>
            <splitter orientation="2">
                <split size="668"/>
                <dock id="" activePageId="Viewer.1">
                    <page id="Viewer.1"/>
                </dock>
                <split size="470"/>
                <dock id="" activePageId="DAG.1" focus="true">
                    <page id="DAG.1"/>
                    <page id="Curve Editor.1"/>
                    <page id="DopeSheet.1"/>
                </dock>
            </splitter>
            <split size="615"/>
            <dock id="" activePageId="Properties.1">
                <page id="Properties.1"/>
                <page id="uk.co.thefoundry.backgroundrenderview.1"/>
                <page id="Scenegraph.1"/>
                <page id="uk.co.thefoundry.scripteditor.1"/>
            </dock>
        </splitter>
    </window>
</layout>
"""

# TCL expression for Write node -- derives render path from script name.
# Splits filename by _ and picks elements [0]=seq [1]=shot [2]=context.
WRITE_TCL = (
    "[file dirname  [value root.name]]"
    "/render/default"
    "/default_[lrange [split [file tail [value root.name]] _ ] 0 0 ]"
    "_[lrange [split [file tail [value root.name]] _ ] 1 1 ]"
    "_[lrange [split [file tail [value root.name]] _ ] 2 2 ]"
    "_main_v001"
    "/default_[lrange [split [file tail [value root.name]] _ ] 0 0 ]"
    "_[lrange [split [file tail [value root.name]] _ ] 1 1 ]"
    "_[lrange [split [file tail [value root.name]] _ ] 2 2 ]"
    "_main_v001.%04d.exr"
)

# Same expression with \[ escaping for inside the .nk Write node
WRITE_TCL_ESCAPED = WRITE_TCL.replace("[", "\\[")


def gen_header(cfg, shot, nk_path, first_frame, last_frame):
    fw, fh = cfg["format_w"], cfg["format_h"]
    write_cs = cfg["write_colorspace"]

    ocio_lines = " colorManagement OCIO\n"
    if cfg.get("ocio_config"):
        ocio_lines += (
            " OCIO_config custom\n"
            f' customOCIOConfigPath "{cfg["ocio_config"]}"\n'
        )

    return (
        f'#! {cfg["nuke_dll"]} -nx\n'
        f'#write_info Write1 file:"{WRITE_TCL}" format:"{fw} {fh} 1"'
        f' chans:":rgba.red:rgba.green:rgba.blue:"'
        f' framerange:"{first_frame} {last_frame}" fps:"{cfg["fps"]}"'
        f' colorspace:"{write_cs}" datatype:"16 bit half"'
        f' transfer:"unknown" views:"main" colorManagement:"OCIO"\n'
        f'version {cfg["nuke_version"]}\n'
        f"define_window_layout_xml {{{WINDOW_LAYOUT}}}\n"
        f"Root {{\n"
        f" inputs 0\n"
        f" name {nk_path}\n"
        f" frame {first_frame}\n"
        f" first_frame {first_frame}\n"
        f" last_frame {last_frame}\n"
        f" lock_range true\n"
        f' format "{fw} {fh} 0 0 {fw} {fh} 1 "\n'
        f" proxy_type scale\n"
        f' proxy_format "1024 778 0 0 1024 778 1 1K_Super_35(full-ap)"\n'
        f"{ocio_lines}"
        f' defaultViewerLUT "OCIO LUTs"\n'
        f" workingSpaceLUT scene_linear\n"
        f' monitorLut "{cfg["monitor_lut"]}"\n'
        f' monitorOutLUT "{cfg["monitor_out_lut"]}"\n'
        f" int8Lut matte_paint\n"
        f" int16Lut texture_paint\n"
        f" logLut compositing_log\n"
        f" floatLut scene_linear\n"
        f"}}\n"
    )


def gen_output_backdrop():
    return (
        "BackdropNode {\n"
        " inputs 0\n"
        " name BackdropNode1\n"
        " tile_color 0x8e388e00\n"
        " label output\n"
        " note_font_size 42\n"
        " xpos -208\n"
        " ypos 946\n"
        " bdwidth 416\n"
        " bdheight 388\n"
        "}\n"
    )


def gen_plate_backdrop(index, plate_name, xpos):
    colors = ["0x71c67100", "0xaaaaaa00", "0x7171c600", "0xc6717100"]
    return (
        f"BackdropNode {{\n"
        f" inputs 0\n"
        f" name BackdropNode{index + 2}\n"
        f" tile_color {colors[index % len(colors)]}\n"
        f' label "{plate_name}\\n"\n'
        f" note_font_size 42\n"
        f" xpos {xpos - 10}\n"
        f" ypos -555\n"
        f" bdheight 309\n"
        f"}}\n"
    )


def gen_read(cfg, read_num, plate, xpos):
    fw, fh = cfg["format_w"], cfg["format_h"]
    cs = cfg["read_colorspace"]
    return (
        f"Read {{\n"
        f" inputs 0\n"
        f" file_type exr\n"
        f" file {plate['path']}\n"
        f' format "{fw} {fh} 0 0 {fw} {fh} 1 "\n'
        f" first {plate['first']}\n"
        f" last {plate['last']}\n"
        f" origfirst {plate['first']}\n"
        f" origlast {plate['last']}\n"
        f" origset true\n"
        f' colorspace "{cs}"\n'
        f" name Read{read_num}\n"
        f" xpos {xpos}\n"
        f" ypos -475\n"
        f"}}\n"
    )


def gen_anchor(anchor_id, plate_name, xpos):
    return (
        f"NoOp {{\n"
        f" name {anchor_id}\n"
        f' help "Stamps by Adrian Pueyo and Alexey Kuchinski.\\nUpdated March 3 2025"\n'
        f' onCreate "if nuke.GUI:\\n    try:\\n        import stamps;'
        f" stamps.anchorOnCreate()\\n    except:\\n        pass\"\n"
        f" knobChanged stamps.anchorKnobChanged()\n"
        f' autolabel "nuke.thisNode().knob(\\"title\\").value()"\n'
        f" tile_color 0xffffff01\n"
        f" note_font_size 20\n"
        f" xpos {xpos}\n"
        f" ypos -340\n"
        f' addUserKnob {{20 anchor_tab l "Anchor Stamp"}}\n'
        f" addUserKnob {{26 identifier -STARTLINE +HIDDEN T anchor}}\n"
        f" addUserKnob {{1 title l Title:"
        f' t "Displayed name on the Node Graph for this Stamp and its Anchor.'
        f"\\nIMPORTANT: This is only for display purposes, and is different"
        f' from the internal node name."}}\n'
        f" title {plate_name}\n"
        f' addUserKnob {{26 prev_title l "" +STARTLINE +HIDDEN T {plate_name}}}\n'
        f' addUserKnob {{26 prev_name l "" +STARTLINE +HIDDEN T {anchor_id}}}\n'
        f' addUserKnob {{3 showing l "" +STARTLINE +HIDDEN}}\n'
        f" addUserKnob {{1 tags l Tags"
        f' t "Comma-separated tags to help find this Anchor'
        f' via the Stamp Selector."}}\n'
        f" tags 2D,\n"
        f' addUserKnob {{26 line1 l "" +STARTLINE}}\n'
        f' addUserKnob {{26 stamps_label l Stamps: T " "}}\n'
        f" addUserKnob {{22 createStamp l new"
        f' t "Create a new Stamp for this Anchor."'
        f" -STARTLINE T stamps.stampCreateWired(nuke.thisNode())}}\n"
        f" addUserKnob {{22 selectStamps l select"
        f' t "Select all of this Anchor\'s Stamps."'
        f" -STARTLINE T stamps.wiredSelectSimilar(nuke.thisNode().name())}}\n"
        f" addUserKnob {{22 reconnectStamps l reconnect"
        f' t "Reconnect all of this Anchor\'s Stamps."'
        f" -STARTLINE T stamps.anchorReconnectWired()}}\n"
        f' addUserKnob {{22 zoomNext l "zoom next"'
        f' t "Navigate to this Anchor\'s next Stamp on the Node Graph."'
        f" -STARTLINE T stamps.wiredZoomNext(nuke.thisNode().name())}}\n"
        f' addUserKnob {{26 line2 l "" +STARTLINE}}\n'
        f" addUserKnob {{22 buttonHelp l Help -STARTLINE T stamps.showHelp()}}\n"
        f' addUserKnob {{26 version l " "'
        f' t "Stamps by Adrian Pueyo and Alexey Kuchinski.\\nUpdated March 3 2025."'
        f" -STARTLINE T"
        f' "<a href=\\"http://www.nukepedia.com/gizmos/other/stamps\\"'
        f' style=\\"color:#666;text-decoration: none;\\">'
        f'<span style=\\"color:#666\\"><big>Stamps v1.2</big></span></a>"}}\n'
        f"}}\n"
    )


def gen_postage_stamp(stamp_num, plate_name, anchor_id, xpos, ypos):
    return (
        f"PostageStamp {{\n"
        f" name Stamp{stamp_num}\n"
        f' help "Stamps by Adrian Pueyo and Alexey Kuchinski.\\nUpdated March 3 2025"\n'
        f' onCreate "if nuke.GUI:\\n    try:\\n        import stamps;'
        f" stamps.wiredOnCreate()\\n    except Exception:\\n        pass\\n\"\n"
        f' knobChanged "if nuke.GUI:\\n    try:\\n        import stamps;'
        f" stamps.wiredKnobChanged()\\n    except:\\n        pass\"\n"
        f' autolabel "nuke.thisNode().knob(\\"title\\").value()"\n'
        f" tile_color 0x1000001\n"
        f" note_font Verdana\n"
        f" note_font_size 20\n"
        f" xpos {xpos}\n"
        f" ypos {ypos}\n"
        f" hide_input true\n"
        f' addUserKnob {{20 wired_tab l "Wired Stamp"}}\n'
        f" addUserKnob {{26 identifier -STARTLINE +HIDDEN T wired}}\n"
        f' addUserKnob {{3 lockCallbacks l "" +STARTLINE +HIDDEN}}\n'
        f" addUserKnob {{6 toReconnect -STARTLINE +HIDDEN}}\n"
        f" addUserKnob {{1 title l Title:"
        f' t "Displayed name on the Node Graph for this Stamp and its Anchor."}}\n'
        f" title {plate_name}\n"
        f' addUserKnob {{26 prev_title l "" +STARTLINE +HIDDEN T {plate_name}}}\n'
        f" addUserKnob {{26 tags l Tags:"
        f' t "Tags of this stamp\'s Anchor.'
        f" Click 'show anchor' to change them.\""
        f" T <i>2D</i>}}\n"
        f" addUserKnob {{26 backdrops l Backdrops:"
        f' t "Labels of backdrop nodes that contain this stamp\'s Anchor."'
        f' +HIDDEN T " "}}\n'
        f' addUserKnob {{26 line1 l "" +STARTLINE}}\n'
        f' addUserKnob {{6 postageStamp_show l "postage stamp"'
        f' t "Enable the postage stamp thumbnail for this node." +STARTLINE}}\n'
        f' addUserKnob {{26 anchor_label l Anchor: T " "}}\n'
        f' addUserKnob {{22 show_anchor l " show anchor "'
        f' t "Show the properties panel for this Stamp\'s Anchor."'
        f" -STARTLINE T stamps.wiredShowAnchor()}}\n"
        f' addUserKnob {{22 zoom_anchor l "zoom anchor"'
        f' t "Navigate to this Stamp\'s Anchor on the Node Graph."'
        f" -STARTLINE T stamps.wiredZoomAnchor()}}\n"
        f' addUserKnob {{26 stamps_label l Stamps: T " "}}\n'
        f' addUserKnob {{22 zoomNext l " zoom next "'
        f' t "Navigate to this Stamp\'s next sibling on the Node Graph."'
        f" -STARTLINE T stamps.wiredZoomNext()}}\n"
        f' addUserKnob {{22 selectSimilar l " select similar "'
        f' t "Select all similar Stamps to this one on the Node Graph."'
        f" -STARTLINE T stamps.wiredSelectSimilar()}}\n"
        f' addUserKnob {{26 space_1 l "" +STARTLINE T " "}}\n'
        f" addUserKnob {{26 reconnect_label l Reconnect:"
        f' t "Reconnect by the stored Anchor name." T " "}}\n'
        f" addUserKnob {{22 reconnect_this l this"
        f' t "Reconnect this Stamp to its Anchor using the stored Anchor name."'
        f" -STARTLINE T"
        f' "n = nuke.thisNode()\\ntry:\\n    n.setInput(0,'
        f' nuke.toNode(n.knob(\\"anchor\\").value()))\\nexcept Exception:\\n'
        f'    nuke.message(\\"Unable to reconnect.\\")\\ntry:\\n'
        f"    import stamps\\n    stamps.wiredGetStyle(n)\\nexcept Exception:"
        f'\\n    pass\\n"}}\n'
        f" addUserKnob {{22 reconnect_similar l similar"
        f' t "Reconnect this Stamp and similar ones using the stored anchor name."'
        f" -STARTLINE T stamps.wiredReconnectSimilar()}}\n"
        f" addUserKnob {{22 reconnect_all l all"
        f' t "Reconnect all Stamps to their Anchors using the stored names."'
        f" -STARTLINE T stamps.wiredReconnectAll()}}\n"
        f' addUserKnob {{26 space_2 l "" +STARTLINE T " "}}\n'
        f' addUserKnob {{20 advanced_reconnection l "Advanced Reconnection" n 2}}\n'
        f' addUserKnob {{26 reconnect_by_title_label l "<font color=gold>By Title:"'
        f' t "Reconnect by searching for a matching title." T " "}}\n'
        f" addUserKnob {{22 reconnect_by_title_this l this"
        f' t "Find an Anchor that shares this Stamp\'s title and connect to it."'
        f" -STARTLINE T stamps.wiredReconnectByTitle()}}\n"
        f" addUserKnob {{22 reconnect_by_title_similar l similar"
        f' t "Find an Anchor by title and reconnect this Stamp and similar ones to it."'
        f" -STARTLINE T stamps.wiredReconnectByTitleSimilar()}}\n"
        f" addUserKnob {{22 reconnect_by_title_selected l selected"
        f' t "For each selected Stamp, reconnect using an Anchor that shares its title."'
        f" -STARTLINE T stamps.wiredReconnectByTitleSelected()}}\n"
        f' addUserKnob {{26 reconnect_by_selection_label l "<font color=orangered>By Selection:"'
        f' t "Force reconnect to a selected Anchor." T " "}}\n'
        f" addUserKnob {{22 reconnect_by_selection_this l this"
        f' t "Force reconnect this Stamp to a selected Anchor."'
        f" -STARTLINE T stamps.wiredReconnectBySelection()}}\n"
        f" addUserKnob {{22 reconnect_by_selection_similar l similar"
        f' t "Force reconnect this Stamp and similar ones to a selected Anchor."'
        f" -STARTLINE T stamps.wiredReconnectBySelectionSimilar()}}\n"
        f" addUserKnob {{22 reconnect_by_selection_selected l selected"
        f' t "Force reconnect all selected Stamps to the selected Anchor."'
        f" -STARTLINE T stamps.wiredReconnectBySelectionSelected()}}\n"
        f" addUserKnob {{1 anchor l Anchor}}\n"
        f" anchor {anchor_id}\n"
        f' addUserKnob {{6 auto_reconnect_by_title l "<font color=#ED9977>'
        f"&nbsp; auto-reconnect by title\""
        f' t "On copy-paste, auto-reconnect by title instead of stored Anchor name;'
        f' turns off automatically." +STARTLINE}}\n'
        f' addUserKnob {{20 advanced_reconnection l "Advanced Reconnection" n -1}}\n'
        f' addUserKnob {{26 line2 l "" +STARTLINE}}\n'
        f" addUserKnob {{22 buttonHelp l Help -STARTLINE T stamps.showHelp()}}\n"
        f' addUserKnob {{26 version l " "'
        f' t "Stamps by Adrian Pueyo and Alexey Kuchinski.\\nUpdated March 3 2025."'
        f" -STARTLINE T"
        f' "<a href=\\"http://www.nukepedia.com/gizmos/other/stamps\\"'
        f' style=\\"color:#666;text-decoration: none;\\">'
        f'<span style=\\"color:#666\\"><big>Stamps v1.2</big></span></a>"}}\n'
        f"}}\n"
    )


def gen_processing_chain(cfg, shot, first_frame, last_frame):
    fw, fh = cfg["format_w"], cfg["format_h"]
    write_cs = cfg["write_colorspace"]
    compression = cfg.get("write_compression", "DWAA")
    return (
        "Dot {\n"
        " name Dot1\n"
        " xpos -3\n"
        " ypos 1026\n"
        "}\n"
        f"Crop {{\n"
        f" box {{0 0 {fw} {fh}}}\n"
        f" name Crop1\n"
        f" xpos -37\n"
        f" ypos 1066\n"
        f"}}\n"
        f"Write {{\n"
        f' file "{WRITE_TCL_ESCAPED}"\n'
        f" file_type exr\n"
        f" compression {compression}\n"
        f" first_part rgba\n"
        f' colorspace "{write_cs}"\n'
        f" create_directories true\n"
        f" checkHashOnRead false\n"
        f" version 2\n"
        f" ocioColorspace scene_linear\n"
        f" display {cfg['write_display']}\n"
        f' view "{cfg["write_view"]}"\n'
        f" name Write1\n"
        f" tile_color 0x555555ff\n"
        f' note_font "Verdana Bold"\n'
        f" xpos -37\n"
        f" ypos 1140\n"
        f"}}\n"
        f"Viewer {{\n"
        f" frame {first_frame}\n"
        f" frame_range {first_frame}-{last_frame}\n"
        f' viewerProcess "{cfg["viewer_process"]}"\n'
        f' monitorOutNDISenderName "Nuke - {shot} - Viewer1"\n'
        f" name Viewer1\n"
        f" xpos -37\n"
        f" ypos 1264\n"
        f"}}\n"
    )


def generate_nk(cfg, shot, plates, nk_path):
    bg01 = plates[0]
    first_frame, last_frame = bg01["first"], bg01["last"]

    nk = gen_header(cfg, shot, nk_path, first_frame, last_frame)
    nk += gen_output_backdrop()

    x_spacing = 292
    base_x = -40
    for i, plate in enumerate(plates):
        nk += gen_plate_backdrop(i, plate["name"], base_x + i * x_spacing)

    bg01_anchor_id = make_anchor_id(shot, plates[0]["name"])
    bg01_stack_var = make_stack_var(shot, plates[0]["name"])
    stamp_num = 1

    for i, plate in enumerate(plates):
        xpos = base_x + i * x_spacing
        anchor_id = make_anchor_id(shot, plate["name"])
        nk += gen_read(cfg, i + 1, plate, xpos)
        nk += gen_anchor(anchor_id, plate["name"], xpos)
        if i == 0:
            nk += f"set {bg01_stack_var} [stack 0]\n"
        nk += gen_postage_stamp(stamp_num, plate["name"], anchor_id, xpos, -284)
        stamp_num += 1

    nk += f"push ${bg01_stack_var}\n"
    nk += gen_postage_stamp(
        stamp_num, plates[0]["name"], bg01_anchor_id, base_x, 29
    )
    nk += gen_processing_chain(cfg, shot, first_frame, last_frame)
    return nk


# -- Shot Creation -------------------------------------------------------

def create_shot(cfg, shared_dir, plates, shot, context, force=False):
    result = {"shot": shot, "status": "ok", "plates": [], "issues": []}

    seq_code = sequence_from_shot(shot)
    nuke_dir = shared_dir / "06_seq" / seq_code / shot / "work" / context / "nuke"
    (nuke_dir / "render" / "default").mkdir(parents=True, exist_ok=True)

    if not plates:
        result["status"] = "warning"
        result["issues"].append("No plates found")
        return result

    result["plates"] = [p["name"] for p in plates]
    result["plate_first"] = plates[0]["first"]
    result["plate_last"] = plates[0]["last"]

    nk_filepath = nuke_dir / f"{shot}_{context}_main_v001.nk"
    if nk_filepath.exists() and not force:
        result["status"] = "skipped"
        result["issues"].append("Nuke file already exists")
        return result

    nk_path_unix = str(nk_filepath).replace("\\", "/")
    nk_filepath.write_text(
        generate_nk(cfg, shot, plates, nk_path_unix), encoding="utf-8"
    )

    result["nk_file"] = str(nk_filepath)
    result["frame_range"] = f"{plates[0]['first']}-{plates[0]['last']}"
    return result


# -- CSV Tracker ---------------------------------------------------------

def generate_tracker_csv(out_dir, shots, plate_data):
    csv_path = out_dir / "shot_tracker.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Shot Code", "Thumbnail", "Sequence", "Status", "Artist", "Notes",
            "Description", "Head In", "Cut In", "Cut Out", "Tail Out",
            "Working Duration", "Plates", "Plate First", "Plate Last", "Retime",
        ])
        for s in shots:
            code = s["code"]
            seq = sequence_from_shot(code)
            pd = plate_data.get(code, {})
            thumb = f"{code}_bg01_thumb.png" if pd.get("plates") else ""
            plate_count = len(pd.get("plates", []))
            writer.writerow([
                code, thumb, seq,
                s.get("status", "WTG"), "", "",
                s.get("description", ""),
                s.get("head_in", ""), s.get("cut_in", ""),
                s.get("cut_out", ""), s.get("tail_out", ""),
                s.get("working_dur", ""), plate_count,
                pd.get("plate_first", ""), pd.get("plate_last", ""),
                s.get("retime", ""),
            ])
    return csv_path


# -- Main ----------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Batch Nuke shot setup from ShotGrid CSV"
    )
    parser.add_argument("--csv", required=True,
                        help="Path to ShotGrid CSV export")
    parser.add_argument("--shared", required=True,
                        help="Project shared root (containing 06_seq/)")
    parser.add_argument("--out", required=True,
                        help="Output directory for CSV tracker")
    parser.add_argument("--context", default="visdev",
                        help="Work context: visdev, comp, etc. (default: visdev)")
    parser.add_argument("--plates-csv",
                        help="Plates metadata CSV (avoids file scanning)")
    parser.add_argument("--plates-dir",
                        help="Plates root dir (default: dirname of --plates-csv,"
                             " or {shared}/05_asset/plates)")
    parser.add_argument("--plate-prefix", default="processed_plate",
                        help="Plate subdir/filename prefix for file scanning"
                             " (default: processed_plate)")
    parser.add_argument("--show-config",
                        action="append", default=[],
                        help="Config JSON (overrides defaults). May be repeated:"
                             " studio defaults first, then the show; later files win")
    parser.add_argument("--seq",
                        help="Filter to one sequence (default: process all)")
    parser.add_argument("--skip", nargs="*", default=[],
                        help="Shot codes to skip")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing Nuke files")
    parser.add_argument("--csv-only", action="store_true",
                        help="Only generate CSV tracker, skip Nuke files")
    parser.add_argument("--format-w", type=int,
                        help="Frame width (overrides show config)")
    parser.add_argument("--format-h", type=int,
                        help="Frame height (overrides show config)")
    parser.add_argument("--fps",
                        help="Frame rate (overrides show config)")
    parser.add_argument("--ocio-config",
                        help="OCIO config path (overrides show config)")
    args = parser.parse_args()

    # Build config: DEFAULTS <- each --show-config in order <- CLI args
    cfg = dict(DEFAULTS)
    for config_path in args.show_config:
        with open(config_path, "r", encoding="utf-8-sig") as f:
            cfg.update(json.load(f))
    if args.format_w:
        cfg["format_w"] = args.format_w
    if args.format_h:
        cfg["format_h"] = args.format_h
    if args.fps:
        cfg["fps"] = args.fps
    if args.ocio_config:
        cfg["ocio_config"] = args.ocio_config

    shared = Path(args.shared)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "thumbnails").mkdir(exist_ok=True)

    # Resolve plates directory
    if args.plates_dir:
        plates_dir = Path(args.plates_dir)
    elif args.plates_csv:
        plates_dir = Path(args.plates_csv).parent
    else:
        plates_dir = shared / "05_asset" / "plates"

    # Parse ShotGrid CSV
    all_shots = parse_csv(args.csv, args.seq)
    shots_with_frames = [s for s in all_shots if s["has_frames"]]
    shots_to_create = [s for s in shots_with_frames if s["code"] not in args.skip]

    print(f"Batch Shot Setup (context: {args.context})")
    print("=" * 55)
    print(f"CSV: {args.csv}")
    print(f"Shared: {shared}")
    print(f"Plates: {plates_dir}")
    # Effective config read-back: the numbers a run report should quote.
    print(f"Configs: {', '.join(args.show_config) if args.show_config else '(built-in defaults only)'}")
    print(f"Nuke: {cfg['nuke_version']} | OCIO: {cfg['ocio_config'] or '(none - Nuke default colour management)'}")
    print(f"Format: {cfg['format_w']}x{cfg['format_h']} @ {cfg['fps']} | viewer: {cfg['viewer_process']}")
    if not cfg["ocio_config"]:
        print("WARNING: no ocio_config set - .nk files will open with Nuke's default colour"
              " management, not ACES. Pass a studio/show config.")
    if args.seq:
        print(f"Sequence filter: {args.seq}")
    else:
        seqs = sorted(set(sequence_from_shot(s["code"]) for s in all_shots))
        print(f"Sequences: {', '.join(seqs)}")
    print(f"Shots in CSV: {len(all_shots)} ({len(shots_with_frames)} with frames)")
    print(f"Shots to create: {len(shots_to_create)}"
          f" (skipping: {args.skip or 'none'})")
    print()

    # Load plate data
    if args.plates_csv:
        all_plate_data = scan_plates_from_csv(args.plates_csv, plates_dir)
    else:
        all_plate_data = {}
        for s in shots_with_frames:
            plates = scan_plates(plates_dir, s["code"], args.plate_prefix)
            if plates:
                all_plate_data[s["code"]] = plates

    # Build plate summary for CSV tracker
    plate_summary = {}
    for shot_code, plates in all_plate_data.items():
        plate_summary[shot_code] = {
            "plates": [p["name"] for p in plates],
            "plate_first": plates[0]["first"],
            "plate_last": plates[0]["last"],
        }

    # Create Nuke files
    if not args.csv_only:
        results = []
        for s in shots_to_create:
            plates = all_plate_data.get(s["code"], [])
            result = create_shot(cfg, shared, plates, s["code"], args.context,
                                force=args.force)
            results.append(result)
            plates_str = ", ".join(result["plates"]) if result["plates"] else "none"
            frame_str = result.get("frame_range", "n/a")
            icon = {"ok": "+", "warning": "!", "skipped": "-"}.get(
                result["status"], "?"
            )
            print(f"  [{icon}] {s['code']}: plates={plates_str}, frames={frame_str}")
            if result["issues"]:
                print(f"      {'; '.join(result['issues'])}")

        ok = sum(1 for r in results if r["status"] == "ok")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        warnings = sum(1 for r in results if r["status"] == "warning")
        print(f"\nNuke: {ok} created, {skipped} skipped, {warnings} warnings")
    else:
        print("Skipping Nuke file generation (--csv-only)")

    # Generate CSV tracker
    csv_path = generate_tracker_csv(out_dir, all_shots, plate_summary)
    print(f"\nCSV tracker: {csv_path}")
    print(f"Thumbnails dir: {out_dir / 'thumbnails'}")


if __name__ == "__main__":
    main()
