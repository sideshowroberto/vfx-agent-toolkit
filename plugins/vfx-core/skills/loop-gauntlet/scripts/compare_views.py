"""compare_views.py -- render vs reference comparison for a loop-gauntlet iteration.

For every view in the spec this script:
  1. Loads renders/<tag>_<view>.png (exits 2 naming ALL missing files if any
     render or reference is absent -- an iteration cannot be judged on a
     render that does not exist).
  2. Loads the reference image, applies an optional crop, then letterboxes it
     to render_size (black padding, no stretching).
  3. Resizes the render to render_size if it is not already that size.
  4. Builds a 3-panel comparison image (reference | 50 percent blend |
     render), each panel labelled in a 28px header strip, plus a JPEG
     preview no wider than 2064px.
  5. Builds one contact sheet for the whole tag: one row per view, reference
     left / render right at half render_size, with a per-row label strip.
  6. Writes compare/<tag>_readback.json: path, byte size, modified time
     (ISO UTC), pixel size, comparison path, unique_values (distinct 8-bit
     grey levels in the render sampled at 256px wide) and suspect_blank
     (unique_values < 8).

IMPORTANT: the comparison image is the judge. A human or agent scores the
rubric by LOOKING at compare/<tag>_<view>.png. The optional --metric value
(edge_similarity) is a tie-breaker and a drift alarm ONLY -- it is never the
score, and a high or low value proves nothing about the render on its own.

Usage:
    python compare_views.py --spec gauntlet_spec.json --tag iter03 [--metric]

Flags:
    --spec PATH   path to the gauntlet spec JSON (required)
    --tag TAG     iteration tag, e.g. iter03 (required)
    --metric      also compute edge_similarity (greyscale FIND_EDGES + NCC)
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter

HEADER_H = 28
JPEG_MAX_W = 2064
BLANK_THRESHOLD = 8


def load_spec(spec_path):
    if not spec_path.exists():
        print("ERROR: spec file not found: {0}".format(spec_path), file=sys.stderr)
        sys.exit(2)
    try:
        with open(spec_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print("ERROR: spec file is not valid JSON: {0} ({1})".format(spec_path, exc), file=sys.stderr)
        sys.exit(2)


def label_strip(width, text):
    """A HEADER_H tall black strip with white text, PIL default font."""
    strip = Image.new("RGB", (width, HEADER_H), (0, 0, 0))
    draw = ImageDraw.Draw(strip)
    font = ImageFont.load_default()
    draw.text((4, 6), text, fill=(255, 255, 255), font=font)
    return strip


def stack_panel(width, height, label, image):
    panel = Image.new("RGB", (width, height + HEADER_H), (0, 0, 0))
    panel.paste(label_strip(width, label), (0, 0))
    panel.paste(image.convert("RGB"), (0, HEADER_H))
    return panel


def unique_grey_values(img, sample_width=256):
    """Distinct 8-bit grey levels in img, resized to sample_width wide.

    A blank or flat render is a valid PNG of plausible size (operating rule
    8) -- this is the instrument that catches it.
    """
    w, h = img.size
    sample_h = max(1, round(h * (sample_width / float(w))))
    small = img.convert("L").resize((sample_width, sample_h), Image.LANCZOS)
    return len(set(small.getdata()))


def ncc(a, b):
    """Normalised cross-correlation of two equal-length numeric sequences.

    Pure python, no numpy: mean-center both, then
    sum(a*b) / sqrt(sum(a*a) * sum(b*b)). Returns a float in -1..1, or 0.0
    for a degenerate (zero-variance) input.
    """
    n = len(a)
    mean_a = sum(a) / n
    mean_b = sum(b) / n
    ca = [x - mean_a for x in a]
    cb = [x - mean_b for x in b]
    num = sum(x * y for x, y in zip(ca, cb))
    den_a = sum(x * x for x in ca)
    den_b = sum(y * y for y in cb)
    den = (den_a * den_b) ** 0.5
    if den == 0.0:
        return 0.0
    return num / den


def edge_similarity(ref_img, render_img, sample_width=256):
    out = []
    for img in (ref_img, render_img):
        w, h = img.size
        sample_h = max(1, round(h * (sample_width / float(w))))
        small = img.convert("L").resize((sample_width, sample_h), Image.LANCZOS)
        edges = small.filter(ImageFilter.FIND_EDGES)
        out.append(list(edges.getdata()))
    return round(ncc(out[0], out[1]), 3)


def main():
    parser = argparse.ArgumentParser(
        description="Compare renders/<tag>_<view>.png against reference images for one loop-gauntlet iteration."
    )
    parser.add_argument("--spec", required=True, help="path to the gauntlet spec JSON")
    parser.add_argument("--tag", required=True, help="iteration tag, e.g. iter03")
    parser.add_argument(
        "--metric",
        action="store_true",
        help="also compute edge_similarity (greyscale FIND_EDGES + normalised cross-correlation); tie-breaker only, never the score",
    )
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)

    working_folder = Path(spec["working_folder"])
    reference_dir = Path(spec["reference_dir"])
    render_size = tuple(spec["render_size"])
    views = spec["views"]
    renders_dir = working_folder / "renders"
    compare_dir = working_folder / "compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    print("working_folder: {0}".format(working_folder))
    print("reference_dir:  {0}".format(reference_dir))
    print("render_size:    {0}".format(render_size))
    print("tag:            {0}".format(args.tag))

    # Collect every required input path up front -- an iteration cannot be
    # judged on a render (or reference) that does not exist.
    missing = []
    render_paths = {}
    ref_paths = {}
    for view in views:
        rpath = renders_dir / "{0}_{1}.png".format(args.tag, view["name"])
        render_paths[view["name"]] = rpath
        if not rpath.exists():
            missing.append(str(rpath))
        fpath = reference_dir / view["reference"]
        ref_paths[view["name"]] = fpath
        if not fpath.exists():
            missing.append(str(fpath))
    if missing:
        print("ERROR: missing input file(s):", file=sys.stderr)
        for m in missing:
            print("  {0}".format(m), file=sys.stderr)
        sys.exit(2)

    readback = []
    computed = {}  # view name -> (ref_padded, render_img), reused for the contact sheet
    for view in views:
        name = view["name"]
        rpath = render_paths[name]
        fpath = ref_paths[name]

        render_img = Image.open(rpath)
        render_img.load()
        original_size = render_img.size
        render_img = render_img.convert("RGB")
        if render_img.size != render_size:
            render_img = render_img.resize(render_size, Image.LANCZOS)

        ref_img = Image.open(fpath)
        ref_img.load()
        ref_img = ref_img.convert("RGB")
        if view.get("crop"):
            ref_img = ref_img.crop(tuple(view["crop"]))
        ref_padded = ImageOps.pad(ref_img, render_size, method=Image.LANCZOS, color=(0, 0, 0))
        computed[name] = (ref_padded, render_img)

        blend = Image.blend(ref_padded, render_img, 0.5)

        panel_w = render_size[0]
        panel_h = render_size[1]
        comp = Image.new("RGB", (panel_w * 3, panel_h + HEADER_H), (0, 0, 0))
        comp.paste(stack_panel(panel_w, panel_h, "REFERENCE: {0}".format(name), ref_padded), (0, 0))
        comp.paste(stack_panel(panel_w, panel_h, "BLEND 50%: {0}".format(name), blend), (panel_w, 0))
        comp.paste(stack_panel(panel_w, panel_h, "RENDER {0}: {1}".format(args.tag, name), render_img), (panel_w * 2, 0))

        comp_path = compare_dir / "{0}_{1}.png".format(args.tag, name)
        comp.save(comp_path)

        jpeg_path = compare_dir / "{0}_{1}.jpg".format(args.tag, name)
        total_w = comp.width
        if total_w > JPEG_MAX_W:
            scale = JPEG_MAX_W / float(total_w)
            preview = comp.resize((JPEG_MAX_W, max(1, round(comp.height * scale))), Image.LANCZOS)
        else:
            preview = comp
        preview.save(jpeg_path, "JPEG", quality=88)

        uv = unique_grey_values(render_img)
        suspect_blank = uv < BLANK_THRESHOLD

        entry = {
            "view": name,
            "render_path": str(rpath),
            "bytes": rpath.stat().st_size,
            "modified": datetime.fromtimestamp(rpath.stat().st_mtime, tz=timezone.utc).isoformat(),
            "pixel_size": list(original_size),
            "comparison_path": str(comp_path),
            "unique_values": uv,
            "suspect_blank": suspect_blank,
        }
        if args.metric:
            entry["edge_similarity"] = edge_similarity(ref_padded, render_img)
        readback.append(entry)

        summary_bits = "unique_values={0} suspect_blank={1}".format(uv, suspect_blank)
        if args.metric:
            summary_bits += " edge_similarity={0}".format(entry["edge_similarity"])
        print("{0}: {1} -- {2}".format(name, comp_path.name, summary_bits))

    # Contact sheet: one row per view, half-size reference left / render right.
    # Reuses the already-padded/resized images from the loop above, so the
    # sheet always matches what compare/<tag>_<view>.png actually showed.
    half_w = max(1, render_size[0] // 2)
    half_h = max(1, render_size[1] // 2)
    sheet = Image.new("RGB", (half_w * 2, (half_h + HEADER_H) * len(views)), (0, 0, 0))
    for i, view in enumerate(views):
        name = view["name"]
        ref_padded, render_img = computed[name]
        y = i * (half_h + HEADER_H)
        sheet.paste(label_strip(half_w * 2, "{0}: {1}".format(args.tag, name)), (0, y))
        sheet.paste(ref_padded.resize((half_w, half_h), Image.LANCZOS), (0, y + HEADER_H))
        sheet.paste(render_img.resize((half_w, half_h), Image.LANCZOS), (half_w, y + HEADER_H))
    sheet_path = compare_dir / "{0}_contactsheet.jpg".format(args.tag)
    sheet.save(sheet_path, "JPEG", quality=88)
    print("contact sheet: {0}".format(sheet_path.name))

    readback_path = compare_dir / "{0}_readback.json".format(args.tag)
    with open(readback_path, "w", encoding="utf-8") as fh:
        json.dump(readback, fh, indent=2)

    print(json.dumps(readback, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
