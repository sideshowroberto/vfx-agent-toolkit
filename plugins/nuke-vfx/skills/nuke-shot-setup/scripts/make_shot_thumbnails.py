r"""Headless shot thumbnails - runs INSIDE Nuke, no MCP, no GUI, no ~/.nuke.

Renders one PNG per plate (first frame of the plate) so a shot tracker or
PROJECT.md can show what each shot looks like. Companion to
batch_shot_setup.py: same plates CSV, same plates-dir derivation, same
thumbnail naming ({shot}_{plate}_thumb.png, which is what the tracker CSV's
Thumbnail column already expects).

Invocation (PowerShell or cmd; quote every path):

    & "C:\Program Files\Nuke17.0v2\Nuke17.0.exe" -t --safe make_shot_thumbnails.py ^
        --plates-csv <plates.csv> --plates-dir <plates root> --out <out dir>

    Optional: --size 960x660   --force   --only <shot> [<shot> ...]
              --ocio-config <config.ocio> --out-colorspace "Output - sRGB"

Why --safe: it loads no plugins and no ~/.nuke, so this never starts the
MCP bridge or fights a GUI Nuke on port 8765. It also means NO OCIO unless
you pass --ocio-config; without it Nuke's built-in colour management reads
EXR as linear and writes PNG as sRGB, which is fine for thumbnails.

Every render is read back (file exists, PNG header parses, dimensions
match); the script exits 1 if any thumbnail failed, so an agent cannot
read a partial run as success. ASCII only.
"""
import argparse
import csv
import os
import re
import struct
import sys

try:
    import nuke  # noqa: F401 - only importable inside Nuke
except ImportError:  # pragma: no cover
    sys.stderr.write("make_shot_thumbnails.py must run inside Nuke: "
                     "Nuke17.0.exe -t --safe make_shot_thumbnails.py ...\n")
    sys.exit(2)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Headless plate thumbnails")
    parser.add_argument("--plates-csv", required=True,
                        help="Plates metadata CSV: Filename, Context, First Frame, Last Frame, Duration")
    parser.add_argument("--plates-dir", required=True,
                        help="Plates root: files live at {plates-dir}/{shot}/{prefix}/{filename}")
    parser.add_argument("--out", required=True, help="Output directory for PNGs")
    parser.add_argument("--size", default="960x660", help="WxH box the thumbnail fits in (default 960x660)")
    parser.add_argument("--force", action="store_true", help="Re-render thumbnails that already exist")
    parser.add_argument("--only", nargs="*", default=[], help="Limit to these shot codes")
    parser.add_argument("--ocio-config", default="",
                        help="OCIO config.ocio to use (default: none, Nuke built-in colour management)")
    parser.add_argument("--out-colorspace", default="Output - sRGB",
                        help="Write colorspace when --ocio-config is set (default: Output - sRGB)")
    return parser.parse_args(argv)


def read_plates(plates_csv, plates_dir):
    """Mirror of batch_shot_setup.scan_plates_from_csv - one entry per plate."""
    plates = []
    with open(plates_csv, "r", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            filename = row["Filename"].strip()
            shot = row["Context"].strip()
            first = int(row["First Frame"].strip())
            parts = filename.split("_%s_" % shot, 1)
            if len(parts) != 2:
                continue
            prefix = parts[0]
            plate_name = parts[1].split("_raw_")[0]
            path = os.path.join(plates_dir, shot, prefix, filename).replace("\\", "/")
            plates.append({"shot": shot, "name": plate_name, "first": first, "path": path})
    return plates


def png_dimensions(path):
    """Return (w, h) from the PNG IHDR chunk, or None if the file is not a PNG."""
    with open(path, "rb") as handle:
        head = handle.read(24)
    if len(head) < 24 or head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", head[16:24])


def set_ocio(config_path):
    root = nuke.root()
    root["colorManagement"].setValue("OCIO")
    root["OCIO_config"].setValue("custom")
    root["customOCIOConfigPath"].setValue(config_path.replace("\\", "/"))


def render_one(plate, out_path, box_w, box_h, out_colorspace, use_ocio):
    nuke.scriptClear()
    if use_ocio:
        set_ocio(use_ocio)
    read = nuke.createNode("Read", inpanel=False)
    read["file"].setValue(plate["path"])
    for knob in ("first", "last", "origfirst", "origlast"):
        read[knob].setValue(plate["first"])
    reformat = nuke.createNode("Reformat", inpanel=False)
    reformat["type"].setValue("to box")
    reformat["box_width"].setValue(box_w)
    reformat["box_height"].setValue(box_h)
    reformat["box_fixed"].setValue(True)
    reformat["filter"].setValue("Lanczos6")
    write = nuke.createNode("Write", inpanel=False)
    write["file"].setValue(out_path)
    write["file_type"].setValue("png")
    write["datatype"].setValue("8 bit")
    if use_ocio:
        try:
            write["colorspace"].setValue(out_colorspace)
        except Exception as exc:  # noqa: BLE001 - name not in this config
            print("  WARN out colorspace '%s' not accepted (%s); using default" % (out_colorspace, exc))
    nuke.execute(write, plate["first"], plate["first"])


def main(argv):
    args = parse_args(argv)
    match = re.match(r"^(\d+)x(\d+)$", args.size)
    if not match:
        print("bad --size %r, expected WxH" % args.size)
        return 2
    box_w, box_h = int(match.group(1)), int(match.group(2))
    os.makedirs(args.out, exist_ok=True)

    plates = read_plates(args.plates_csv, args.plates_dir)
    if args.only:
        plates = [p for p in plates if p["shot"] in args.only]
    print("make_shot_thumbnails: %d plate(s) from %s" % (len(plates), args.plates_csv))
    print("  plates dir: %s" % args.plates_dir)
    print("  out: %s  box: %dx%d  ocio: %s" % (args.out, box_w, box_h, args.ocio_config or "(none)"))

    rendered = skipped = failed = 0
    for plate in plates:
        out_path = os.path.join(args.out, "%s_%s_thumb.png" % (plate["shot"], plate["name"])).replace("\\", "/")
        if os.path.exists(out_path) and not args.force:
            skipped += 1
            print("  [-] %s %s: exists" % (plate["shot"], plate["name"]))
            continue
        first_file = plate["path"] % plate["first"] if "%" in plate["path"] else plate["path"]
        if not os.path.exists(first_file):
            failed += 1
            print("  [!] %s %s: plate frame missing: %s" % (plate["shot"], plate["name"], first_file))
            continue
        try:
            render_one(plate, out_path, box_w, box_h, args.out_colorspace, args.ocio_config)
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            failed += 1
            print("  [!] %s %s: render error: %s" % (plate["shot"], plate["name"], exc))
            continue
        dims = png_dimensions(out_path) if os.path.exists(out_path) else None
        if not dims or dims[0] > box_w or dims[1] > box_h or os.path.getsize(out_path) == 0:
            failed += 1
            print("  [!] %s %s: read-back failed (%s)" % (plate["shot"], plate["name"], dims))
            continue
        rendered += 1
        print("  [+] %s %s: %dx%d %d bytes" % (plate["shot"], plate["name"], dims[0], dims[1],
                                              os.path.getsize(out_path)))

    print("\nThumbnails: %d rendered, %d skipped (exist), %d FAILED" % (rendered, skipped, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    # Under "nuke -t script.py a b c", sys.argv is [script.py, a, b, c].
    sys.exit(main(sys.argv[1:]))
