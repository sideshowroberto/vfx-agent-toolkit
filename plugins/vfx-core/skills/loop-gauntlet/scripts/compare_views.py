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
     preview no wider than 2064px. This file name and shape are unchanged
     from earlier versions so existing consumers keep working.
  5. Builds a SEPARATE 5-panel instrument image, compare/<tag>_<view>_5.png
     (plus a capped JPEG preview): the same reference | blend | render three
     panels, PLUS an edge overlay panel and an absolute-difference panel.
     A 5-panel row routinely exceeds the 2064px preview width at normal
     render sizes, so it is its own file rather than replacing the 3-panel
     one -- see observation 0042.
       - EDGE OVERLAY: FIND_EDGES (after a small Gaussian blur) on the
         letterboxed reference and the render, each thresholded to a binary
         edge mask. Reference-only edges are cyan, render-only edges are
         red, edges that coincide within a 2px dilation are white,
         background is black. This is the silhouette/alignment instrument:
         it separates "the edges line up" from "the exposure matches",
         which a 50 percent blend cannot (observation 0042).
       - DIFFERENCE: absolute difference of the two luminance images mapped
         through a black -> blue -> red -> yellow heat ramp, with the
         signed mean difference (render minus reference, 0-255 scale)
         printed in its header strip. This is the exposure instrument.
  6. Writes compare/<tag>_readback.json: path, byte size, modified time
     (ISO UTC), pixel size, comparison path, unique_values (distinct 8-bit
     grey levels in the render sampled at 256px wide), suspect_blank
     (unique_values < 8), and the edge/difference metrics below.

IMPORTANT: the comparison image is the judge. A human or agent scores the
rubric by LOOKING at compare/<tag>_<view>_5.png (or the 3-panel image if the
5-panel has not been generated). The edge overlay panel is the instrument
for silhouette; the difference panel is the instrument for exposure. The
blend panel stays only as a quick glance aid -- quote the edge/difference
numbers in the review JSON's gaps when they matter, rather than describing
the blend. The optional --metric value (edge_similarity) is a separate,
older tie-breaker and drift alarm ONLY -- it is never the score, and a high
or low value proves nothing about the render on its own.

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

from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageStat

HEADER_H = 28
JPEG_MAX_W = 2064
BLANK_THRESHOLD = 8

# Edge-instrument defaults (observation 0042): a small blur suppresses
# single-pixel sensor/render noise before FIND_EDGES, the threshold keeps
# only edges with real contrast, and the 2px dilation is the "close enough
# to count as aligned" tolerance for both the overlay and the metrics.
EDGE_BLUR_RADIUS = 1.0
EDGE_THRESHOLD = 32
EDGE_DILATE_PX = 2

EDGE_CYAN = (0, 255, 255)
EDGE_RED = (255, 0, 0)
EDGE_WHITE = (255, 255, 255)


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


def binary_edge_mask(gray_img, blur_radius=EDGE_BLUR_RADIUS, threshold=EDGE_THRESHOLD):
    """Full-resolution binary (0/255, mode L) edge mask for one greyscale image."""
    blurred = gray_img.filter(ImageFilter.GaussianBlur(blur_radius))
    edges = blurred.filter(ImageFilter.FIND_EDGES)
    return edges.point(lambda p: 255 if p >= threshold else 0)


def dilate_mask(mask, px=EDGE_DILATE_PX):
    """Grow a binary mask by px pixels using a square max filter."""
    size = 2 * px + 1
    return mask.filter(ImageFilter.MaxFilter(size))


def mask_and(a, b):
    """Pixelwise AND of two binary (0/255) L-mode masks."""
    return ImageChops.multiply(a, b)


def mask_or(a, b):
    """Pixelwise OR of two binary (0/255) L-mode masks."""
    return ImageChops.lighter(a, b)


def mask_and_not(a, b):
    """Pixelwise (a AND NOT b) of two binary (0/255) L-mode masks."""
    return ImageChops.subtract(a, b)


def count_on(mask):
    """Count of 255-valued pixels in a binary (0/255) L-mode mask."""
    return mask.histogram()[255]


def heat_ramp_luts():
    """Three 256-entry LUTs (R, G, B) mapping 0-255 to a black -> blue ->
    red -> yellow heat ramp, for use with Image.point()."""
    lut_r = [0] * 256
    lut_g = [0] * 256
    lut_b = [0] * 256
    for v in range(256):
        if v < 85:
            t = v / 85.0
            r, g, b = 0, 0, int(255 * t)
        elif v < 170:
            t = (v - 85) / 85.0
            r, g, b = int(255 * t), 0, int(255 * (1 - t))
        else:
            t = (v - 170) / 85.0
            r, g, b = 255, int(255 * t), 0
        lut_r[v] = r
        lut_g[v] = g
        lut_b[v] = b
    return lut_r, lut_g, lut_b


HEAT_LUT_R, HEAT_LUT_G, HEAT_LUT_B = heat_ramp_luts()


def difference_heatmap(ref_gray, render_gray):
    diff_l = ImageChops.difference(ref_gray, render_gray)
    r = diff_l.point(HEAT_LUT_R)
    g = diff_l.point(HEAT_LUT_G)
    b = diff_l.point(HEAT_LUT_B)
    return Image.merge("RGB", (r, g, b)), diff_l


def edge_overlay_and_metrics(ref_img, render_img):
    """Build the cyan/red/white edge overlay and the four edge/luminance
    metrics from a pair of already letterboxed/resized RGB images.

    Returns (overlay_rgb, metrics_dict).
    """
    ref_gray = ref_img.convert("L")
    render_gray = render_img.convert("L")

    ref_edge = binary_edge_mask(ref_gray)
    render_edge = binary_edge_mask(render_gray)
    ref_dil = dilate_mask(ref_edge)
    render_dil = dilate_mask(render_edge)

    ref_count = count_on(ref_edge)
    union_dil = count_on(mask_or(ref_dil, render_dil))
    intersect_dil = count_on(mask_and(ref_dil, render_dil))
    edge_iou = round(intersect_dil / float(union_dil), 3) if union_dil else 0.0

    ref_near_render = count_on(mask_and(ref_edge, render_dil))
    edge_ref_covered = round(ref_near_render / float(ref_count), 3) if ref_count else 0.0

    coincident = mask_or(mask_and(ref_edge, render_dil), mask_and(render_edge, ref_dil))
    ref_only = mask_and_not(ref_edge, coincident)
    render_only = mask_and_not(render_edge, coincident)

    overlay = Image.new("RGB", ref_img.size, (0, 0, 0))
    overlay.paste(EDGE_CYAN, mask=ref_only)
    overlay.paste(EDGE_RED, mask=render_only)
    overlay.paste(EDGE_WHITE, mask=coincident)

    mean_signed_lum_diff = round(
        ImageStat.Stat(render_gray).mean[0] - ImageStat.Stat(ref_gray).mean[0], 2
    )

    metrics = {
        "edge_iou": edge_iou,
        "edge_ref_covered": edge_ref_covered,
        "mean_signed_lum_diff": mean_signed_lum_diff,
    }
    return overlay, metrics, ref_gray, render_gray


def scaled_preview(image, max_w=JPEG_MAX_W):
    if image.width > max_w:
        scale = max_w / float(image.width)
        return image.resize((max_w, max(1, round(image.height * scale))), Image.LANCZOS)
    return image


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

        # --- existing 3-panel comparison image (name/shape unchanged) ---
        comp = Image.new("RGB", (panel_w * 3, panel_h + HEADER_H), (0, 0, 0))
        comp.paste(stack_panel(panel_w, panel_h, "REFERENCE: {0}".format(name), ref_padded), (0, 0))
        comp.paste(stack_panel(panel_w, panel_h, "BLEND 50%: {0}".format(name), blend), (panel_w, 0))
        comp.paste(stack_panel(panel_w, panel_h, "RENDER {0}: {1}".format(args.tag, name), render_img), (panel_w * 2, 0))

        comp_path = compare_dir / "{0}_{1}.png".format(args.tag, name)
        comp.save(comp_path)

        jpeg_path = compare_dir / "{0}_{1}.jpg".format(args.tag, name)
        scaled_preview(comp).save(jpeg_path, "JPEG", quality=88)

        # --- edge overlay and difference instruments (observation 0042) ---
        overlay_img, edge_metrics, ref_gray, render_gray = edge_overlay_and_metrics(ref_padded, render_img)
        diff_img, diff_l = difference_heatmap(ref_gray, render_gray)
        mean_abs_lum_diff = round(ImageStat.Stat(diff_l).mean[0], 2)

        # --- separate 5-panel instrument image ---
        comp5 = Image.new("RGB", (panel_w * 5, panel_h + HEADER_H), (0, 0, 0))
        comp5.paste(stack_panel(panel_w, panel_h, "REFERENCE: {0}".format(name), ref_padded), (0, 0))
        comp5.paste(stack_panel(panel_w, panel_h, "BLEND 50%: {0}".format(name), blend), (panel_w, 0))
        comp5.paste(stack_panel(panel_w, panel_h, "RENDER {0}: {1}".format(args.tag, name), render_img), (panel_w * 2, 0))
        comp5.paste(
            stack_panel(panel_w, panel_h, "edge overlay (cyan=ref red=render white=both)", overlay_img),
            (panel_w * 3, 0),
        )
        diff_label = "abs difference (mean diff render-ref: {0})".format(edge_metrics["mean_signed_lum_diff"])
        comp5.paste(stack_panel(panel_w, panel_h, diff_label, diff_img), (panel_w * 4, 0))

        comp5_path = compare_dir / "{0}_{1}_5.png".format(args.tag, name)
        comp5.save(comp5_path)

        jpeg5_path = compare_dir / "{0}_{1}_5.jpg".format(args.tag, name)
        scaled_preview(comp5).save(jpeg5_path, "JPEG", quality=88)

        uv = unique_grey_values(render_img)
        suspect_blank = uv < BLANK_THRESHOLD

        entry = {
            "view": name,
            "render_path": str(rpath),
            "bytes": rpath.stat().st_size,
            "modified": datetime.fromtimestamp(rpath.stat().st_mtime, tz=timezone.utc).isoformat(),
            "pixel_size": list(original_size),
            "comparison_path": str(comp_path),
            "comparison_5_path": str(comp5_path),
            "unique_values": uv,
            "suspect_blank": suspect_blank,
            "edge_iou": edge_metrics["edge_iou"],
            "edge_ref_covered": edge_metrics["edge_ref_covered"],
            "mean_signed_lum_diff": edge_metrics["mean_signed_lum_diff"],
            "mean_abs_lum_diff": mean_abs_lum_diff,
        }
        if args.metric:
            entry["edge_similarity"] = edge_similarity(ref_padded, render_img)
        readback.append(entry)

        summary_bits = "unique_values={0} suspect_blank={1} edge_iou={2} edge_ref_covered={3} mean_signed_lum_diff={4} mean_abs_lum_diff={5}".format(
            uv, suspect_blank, entry["edge_iou"], entry["edge_ref_covered"], entry["mean_signed_lum_diff"], entry["mean_abs_lum_diff"]
        )
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
