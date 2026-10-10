"""scratch_luminance.py -- measure a scratch render against a reference BEFORE
spending an iteration tag (lighting / world / exposure / view-transform changes).

Generalised from two job scripts (a scratch-render read-back and a region
brightness read-back). What it reports, for one render:

  1. Instrument check: file size, pixel size, unique grey levels, suspect_blank
     (fewer than 8 distinct levels = a blank or flat frame is a valid PNG of
     plausible size).
  2. Per-box mean luma (0-255, the same PIL "L" the reference was measured
     with) and mean linear luminance, for the render and for the reference,
     signed delta (render minus reference, or minus a stated per-box target)
     and pass/fail against a tolerance.
  3. Feature checks, because a small mean box can pass by coincidence:
       - brightest-1% centroid and p5-p95 bounding box of BOTH images, and the
         distance between the centroids (fraction of the image diagonal);
       - optional per-event checks from the boxes JSON ("features"):
           kind "patch": mask IoU inside a search box, peak (99th percentile
             luma) and peak-minus-background contrast;
           kind "line":  thin groove / seam / joint -- contrast against its
             flanks, as a ratio of the reference contrast; a small ratio is
             reported as "not visible" up front.
  4. A JSON result (--out) with every number above.

Boxes JSON (normalised 0-1 coords, x0 y0 x1 y1, origin top-left):
    {"boxes": {"wall_left": [0.03, 0.22, 0.06, 0.67],
               "skylight":  {"box": [0.4, 0.0, 0.6, 0.1], "target": 113, "tolerance": 15}},
     "features": [
        {"name": "bright_opening", "kind": "patch", "box": [0.35, 0.0, 0.65, 0.2],
         "mask_threshold": 155, "min_iou": 0.3, "peak_tol": 25,
         "background_box": "wall_left", "contrast_tol": 25},
        {"name": "wall_joint", "kind": "line", "box": [0.074, 0.2, 0.078, 0.8],
         "flank": 0.02, "min_ratio": 0.25}]}
A top-level {"name": [x0,y0,x1,y1]} dict, or a "boxes" list of
{"name":..., "box":[...]} objects, is accepted too. If the boxes were authored in
pixels add "pixel_size": [width, height] and they are normalised for you.
Without --boxes a COLSxROWS grid (default 4x3) is used.

Image inputs: PNG/JPG/etc (8-bit sRGB), .npy (float, linear), .exr (linear;
needs the OpenEXR python package -- optional, a clear error is printed if it is
missing). The reference is cropped (--crop, reference pixels) and fitted to the
render size with the same black letterbox compare_views.py uses (--fit
letterbox, default) or stretched (--fit stretch).

Exit codes: 0 = everything within tolerance, 1 = measured but outside tolerance
or the render looks blank (JSON still written), 2 = input / usage error.

Usage:
    python scratch_luminance.py --render scratch03_hero.png --reference ref_hero.png \\
        --boxes lighting_boxes.json --tolerance 12 --out scratch03_luminance.json
"""
import argparse
import json
import math
import os
import sys
import time
from datetime import datetime, timezone

try:
    import numpy as np
except ImportError:
    sys.stderr.write("ERROR: scratch_luminance.py needs numpy (pip install numpy).\n")
    sys.exit(2)
from PIL import Image, ImageOps

BLANK_THRESHOLD = 8          # distinct 8-bit luma levels below this = suspect blank (as compare_views.py)
DEFAULT_TOLERANCE = 12.0     # luma levels (0-255) a box may differ from its target
DEFAULT_CENTROID_TOL = 0.10  # brightest-percent centroid distance, fraction of the image diagonal
DEFAULT_GRID = "4x3"

LUMA_W = np.array([0.299, 0.587, 0.114], dtype=np.float64)     # PIL convert("L") weights, on encoded values
Y_W = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)     # Rec.709 luminance, on linear values


class InputError(Exception):
    """Bad input or usage -> exit code 2."""


# ----------------------------------------------------------------------------
# colour transfer helpers (shared with solve_light_mix.py)
# ----------------------------------------------------------------------------

def srgb_encode(lin):
    """Linear -> sRGB transfer, 0..1, clipped."""
    x = np.clip(lin, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1.0 / 2.4) - 0.055)


def srgb_decode(enc):
    """sRGB 0..1 -> linear, clipped."""
    x = np.clip(enc, 0.0, 1.0)
    return np.where(x <= 0.04045, x / 12.92, np.power((x + 0.055) / 1.055, 2.4))


def luma_of_enc(enc255):
    """PIL 'L' style luma of encoded 0..255 RGB (last axis = 3)."""
    return enc255[..., 0] * LUMA_W[0] + enc255[..., 1] * LUMA_W[1] + enc255[..., 2] * LUMA_W[2]


# ----------------------------------------------------------------------------
# image loading
# ----------------------------------------------------------------------------

class Img(object):
    """One image in every form the scripts need: encoded 0..255, linear, luma."""

    def __init__(self, path, lin, enc, luma, kind, space, notes=None, nonfinite=0, parts=None):
        self.path = path
        self.lin = lin.astype(np.float32)
        self.enc = enc.astype(np.float32)
        self.luma = luma.astype(np.float32)
        self.lin_y = (self.lin.astype(np.float64) @ Y_W).astype(np.float32)
        self.kind = kind          # "8bit" or "float"
        self.space = space        # "srgb" or "linear" -- how the file's numbers were interpreted
        self.notes = notes or []
        self.nonfinite = nonfinite
        self.parts = parts or []
        self.size = (self.enc.shape[1], self.enc.shape[0])   # (w, h)
        self.nbytes = os.path.getsize(path) if path and os.path.isfile(path) else 0


def _pick_rgb(channels, layer):
    """Return a float32 HxWx3 array from an OpenEXR 3.x channel dict, or None."""
    names = sorted(channels.keys())

    def stack(r, g, b):
        return np.stack([np.asarray(channels[n].pixels, dtype=np.float32) for n in (r, g, b)], axis=-1)

    if layer:
        trio = [layer + "." + c for c in "RGB"]
        if all(t in channels for t in trio):
            return stack(*trio)
        for combined in (layer, layer + ".RGBA", layer + ".RGB"):
            if combined in channels:
                px = np.asarray(channels[combined].pixels, dtype=np.float32)
                if px.ndim == 3 and px.shape[2] >= 3:
                    return px[..., :3]
        return None
    for combined in ("RGBA", "RGB"):
        if combined in channels:
            px = np.asarray(channels[combined].pixels, dtype=np.float32)
            if px.ndim == 3 and px.shape[2] >= 3:
                return px[..., :3]
    if all(c in channels for c in ("R", "G", "B")):
        return stack("R", "G", "B")
    prefixes = sorted(set(n.rsplit(".", 1)[0] for n in names if n.endswith((".R", ".G", ".B"))))
    prefixes = [p for p in prefixes if all((p + "." + c) in channels for c in "RGB")]
    if prefixes:
        prefixes.sort(key=lambda p: (0 if "combined" in p.lower() else 1, p))
        return stack(*[prefixes[0] + "." + c for c in "RGB"])
    return None


def _load_exr(path, layer):
    try:
        import OpenEXR
    except ImportError:
        raise InputError("EXR input needs the OpenEXR python package (pip install OpenEXR). "
                         "Without it, save the pass as .npy (float32 HxWx3, linear) or 16-bit PNG: " + path)
    if not hasattr(OpenEXR, "File"):
        raise InputError("this OpenEXR python package is too old (no OpenEXR.File); pip install -U OpenEXR")
    f = OpenEXR.File(path)
    rgb, parts = None, []
    for i, part in enumerate(f.parts):          # list EVERY part: never read only part 0 silently
        names = sorted(part.channels.keys())
        parts.append({"index": i, "channels": names})
        if rgb is None:
            rgb = _pick_rgb(part.channels, layer)
            if rgb is not None:
                parts[-1]["used"] = True
    if rgb is None:
        raise InputError("no RGB channels found in %s (use --exr-layer for layered files); parts: %s" % (path, parts))
    return rgb, parts


def load_image(path, input_space="auto", exr_layer=None):
    """Load any supported image; raises InputError. input_space: auto|srgb|linear."""
    if not path or not os.path.isfile(path):
        raise InputError("file not found: %s" % path)
    ext = os.path.splitext(path)[1].lower()
    notes, parts, pil_luma, kind = [], [], None, "float"
    if ext == ".exr":
        arr, parts = _load_exr(path, exr_layer)
        default_space = "linear"
    elif ext == ".npy":
        arr = np.load(path).astype(np.float32)
        if arr.ndim == 2:
            arr = np.stack([arr] * 3, axis=-1)
        if arr.ndim != 3 or arr.shape[2] < 3:
            raise InputError("%s: expected a float array of shape HxW or HxWx3, got %s" % (path, arr.shape))
        arr = arr[..., :3]
        default_space = "linear"
    else:
        try:
            im = Image.open(path)
            im.load()
        except Exception as exc:        # PIL raises many types for a bad file
            raise InputError("cannot read image %s (%s)" % (path, exc))
        default_space = "srgb"
        if im.mode in ("I;16", "I;16L", "I;16B", "I"):
            g = np.asarray(im).astype(np.float32) / 65535.0
            arr = np.stack([g] * 3, axis=-1)
            notes.append("16-bit grey image divided by 65535")
        else:
            kind = "8bit"
            arr = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
            pil_luma = np.asarray(im.convert("L")).astype(np.float32)
    space = default_space if input_space == "auto" else input_space
    bad = ~np.isfinite(arr)
    nonfinite = int(bad.any(axis=-1).sum()) if bad.any() else 0
    if nonfinite:
        arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        notes.append("%d non-finite pixels set to 0" % nonfinite)
        if nonfinite > 0.001 * arr.shape[0] * arr.shape[1]:
            raise InputError("%s: %d non-finite pixels (more than 0.1%% of the frame): fix the render first" % (path, nonfinite))
    if space == "srgb":
        enc = arr * 255.0
        lin = srgb_decode(arr)
    else:
        lin = arr
        enc = srgb_encode(arr) * 255.0
    luma = pil_luma if (pil_luma is not None and space == "srgb") else luma_of_enc(enc)
    return Img(path, lin, enc, luma, kind, space, notes, nonfinite, parts)


def fit_to_size(img, size, crop=None, fit="letterbox"):
    """Crop (reference pixels) then letterbox/stretch img to size=(w,h); returns an Img.

    Same black letterbox compare_views.py applies to references. No-op when the
    image already has the right size and no crop is requested.
    """
    if crop is None and img.size == tuple(size):
        return img
    pil = Image.fromarray(np.clip(img.enc + 0.5, 0, 255).astype(np.uint8))
    if crop is not None:
        pil = pil.crop(tuple(int(c) for c in crop))
    if fit == "letterbox":
        pil = ImageOps.pad(pil, tuple(size), method=Image.LANCZOS, color=(0, 0, 0))
    else:
        pil = pil.resize(tuple(size), Image.LANCZOS)
    rgb = np.asarray(pil.convert("RGB")).astype(np.float32) / 255.0
    out = Img(img.path, srgb_decode(rgb), rgb * 255.0, np.asarray(pil.convert("L")).astype(np.float32),
              "8bit", "srgb", list(img.notes) + ["fitted to %dx%d (%s)" % (size[0], size[1], fit)])
    out.nbytes = img.nbytes
    return out


def wait_for_file(path, timeout):
    """True once the file exists and its size is stable for two polls."""
    last, stable, t0 = -1, 0, time.time()
    while time.time() - t0 < timeout:
        if os.path.exists(path):
            size = os.path.getsize(path)
            stable = stable + 1 if (size > 0 and size == last) else 0
            last = size
            if stable >= 2:
                return True
        time.sleep(1.0)
    return False


# ----------------------------------------------------------------------------
# boxes
# ----------------------------------------------------------------------------

def parse_grid(text):
    try:
        cols, rows = [int(v) for v in text.lower().split("x")]
        if cols < 1 or rows < 1:
            raise ValueError
    except ValueError:
        raise InputError("--grid must look like 4x3, got %r" % text)
    return cols, rows


def grid_boxes(text):
    cols, rows = parse_grid(text)
    out = []
    for r in range(rows):
        for c in range(cols):
            out.append({"name": "r%dc%d" % (r, c), "box": [c / float(cols), r / float(rows),
                                                          (c + 1) / float(cols), (r + 1) / float(rows)],
                        "target": None, "tolerance": None})
    return out


def _norm_box(name, box, pixel_size):
    if not isinstance(box, (list, tuple)) or len(box) != 4:
        raise InputError("box %r must be [x0, y0, x1, y1], got %r" % (name, box))
    b = [float(v) for v in box]
    if pixel_size:
        b = [b[0] / pixel_size[0], b[1] / pixel_size[1], b[2] / pixel_size[0], b[3] / pixel_size[1]]
    if max(b) > 1.0 + 1e-9 or min(b) < -1e-9:
        raise InputError("box %r has coordinates outside 0..1 (%s); boxes are normalised -- "
                         "add \"pixel_size\": [w, h] to the boxes JSON if they were authored in pixels" % (name, box))
    if not (b[2] > b[0] and b[3] > b[1]):
        raise InputError("box %r is empty or inverted: %s" % (name, box))
    return [min(max(v, 0.0), 1.0) for v in b]


def load_boxes(path, grid):
    """Return {"boxes": [...], "features": [...], "global_target": float|None, "source": str}."""
    if not path:
        return {"boxes": grid_boxes(grid), "features": [], "global_target": None, "source": "grid " + grid}
    if not os.path.isfile(path):
        raise InputError("boxes file not found: %s" % path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        raise InputError("boxes file is not valid JSON: %s (%s)" % (path, exc))
    if not isinstance(data, dict):
        raise InputError("boxes file must be a JSON object: %s" % path)
    wrapper = "boxes" in data
    raw = data["boxes"] if wrapper else data
    pixel_size = data.get("pixel_size") if wrapper else None
    items = []
    if isinstance(raw, dict):
        for name, val in raw.items():
            items.append((name, val))
    elif isinstance(raw, list):
        for val in raw:
            if not isinstance(val, dict) or "name" not in val:
                raise InputError("each entry of a boxes list needs a \"name\"")
            items.append((val["name"], val))
    else:
        raise InputError("\"boxes\" must be an object or a list")
    boxes = []
    for name, val in items:
        if isinstance(val, dict):
            b, target, tol = val.get("box"), val.get("target"), val.get("tolerance")
        else:
            b, target, tol = val, None, None
        boxes.append({"name": str(name), "box": _norm_box(name, b, pixel_size),
                      "target": None if target is None else float(target),
                      "tolerance": None if tol is None else float(tol)})
    if not boxes:
        raise InputError("boxes file lists no boxes: %s" % path)
    names = [b["name"] for b in boxes]
    if len(set(names)) != len(names):
        raise InputError("duplicate box names in %s" % path)
    features = []
    for feat in (data.get("features") or []) if wrapper else []:
        f = dict(feat)
        f["box"] = _norm_box(f.get("name", "?"), f.get("box"), pixel_size)
        if isinstance(f.get("background_box"), list):
            f["background_box"] = _norm_box(f.get("name", "?"), f["background_box"], pixel_size)
        features.append(f)
    gt = data.get("global_target") if wrapper else None
    return {"boxes": boxes, "features": features, "global_target": None if gt is None else float(gt),
            "source": path}


def to_px(box, w, h):
    """Normalised box -> integer pixel box (x0, y0, x1, y1), never empty, inside the image."""
    x0 = min(max(int(math.floor(box[0] * w)), 0), w - 1)
    y0 = min(max(int(math.floor(box[1] * h)), 0), h - 1)
    x1 = min(max(int(math.ceil(box[2] * w)), x0 + 1), w)
    y1 = min(max(int(math.ceil(box[3] * h)), y0 + 1), h)
    return x0, y0, x1, y1


# ----------------------------------------------------------------------------
# measurements
# ----------------------------------------------------------------------------

def brightest_percent(values, percent):
    """Centroid and p5-p95 bounding box of the brightest `percent` of pixels (normalised coords)."""
    h, w = values.shape
    thr = float(np.percentile(values, 100.0 - percent))
    ys, xs = np.nonzero(values >= thr)
    return {"percent": percent, "threshold": round(thr, 3), "pixels": int(len(xs)),
            "centroid_norm": [round(float((xs.mean() + 0.5) / w), 4), round(float((ys.mean() + 0.5) / h), 4)],
            "bbox_p5_p95_norm": [round(float(np.percentile(xs, 5)) / w, 4), round(float(np.percentile(ys, 5)) / h, 4),
                                 round(float(np.percentile(xs, 95) + 1) / w, 4), round(float(np.percentile(ys, 95) + 1) / h, 4)]}


def unique_levels(luma):
    return int(len(np.unique(np.clip(np.round(luma), 0, 255).astype(np.uint8))))


def _mean(arr, px):
    x0, y0, x1, y1 = px
    return float(arr[y0:y1, x0:x1].mean())


def _r(v, n=2):
    return None if v is None else round(float(v), n)


def check_patch(feat, render, ref, boxes_px, w, h, tol):
    """Event placement: mask IoU in a search box, peak, and peak-minus-background contrast."""
    px = to_px(feat["box"], w, h)
    x0, y0, x1, y1 = px
    rl, fl = render.luma[y0:y1, x0:x1], ref.luma[y0:y1, x0:x1]
    if feat.get("mask_threshold") is not None:
        thr_r = thr_f = float(feat["mask_threshold"])
        mask_desc = "luma >= %.1f in both" % thr_r
    else:
        pct = float(feat.get("mask_top_percent", 10.0))
        thr_r, thr_f = float(np.percentile(rl, 100.0 - pct)), float(np.percentile(fl, 100.0 - pct))
        mask_desc = "brightest %.1f%% of the box in each image" % pct
    mr, mf = rl >= thr_r, fl >= thr_f
    union = int((mr | mf).sum())
    iou = float((mr & mf).sum()) / union if union else 0.0
    peak_r, peak_f = float(np.percentile(rl, 99)), float(np.percentile(fl, 99))
    out = {"name": feat.get("name", "?"), "kind": "patch", "box_px": list(px), "mask": mask_desc,
           "mask_px_render": int(mr.sum()), "mask_px_reference": int(mf.sum()), "iou": _r(iou, 3),
           "peak_render": _r(peak_r), "peak_reference": _r(peak_f), "peak_delta": _r(peak_r - peak_f)}
    reasons = []
    min_iou = float(feat.get("min_iou", 0.3))
    if int(mf.sum()) == 0:
        reasons.append("reference mask is empty: the feature definition does not describe the reference")
    if iou < min_iou:
        reasons.append("mask IoU %.3f < min_iou %.2f (event missing or misplaced)" % (iou, min_iou))
    peak_tol = float(feat.get("peak_tol", 2.0 * tol))
    if abs(peak_r - peak_f) > peak_tol:
        reasons.append("peak differs by %+.1f (tolerance %.1f)" % (peak_r - peak_f, peak_tol))
    bg = feat.get("background_box")
    if bg is not None:
        if isinstance(bg, str):
            if bg not in boxes_px:
                raise InputError("feature %r: background_box %r is not a named box" % (out["name"], bg))
            bpx = boxes_px[bg]
        else:
            bpx = to_px(bg, w, h)
        con_r, con_f = peak_r - _mean(render.luma, bpx), peak_f - _mean(ref.luma, bpx)
        out.update({"contrast_render": _r(con_r), "contrast_reference": _r(con_f), "contrast_delta": _r(con_r - con_f)})
        contrast_tol = float(feat.get("contrast_tol", 2.0 * tol))
        if abs(con_r - con_f) > contrast_tol:
            reasons.append("peak-to-background contrast differs by %+.1f (tolerance %.1f)" % (con_r - con_f, contrast_tol))
    out["pass"] = not reasons
    out["reasons"] = reasons
    return out


def check_line(feat, render, ref, w, h):
    """Thin groove / seam / joint: contrast against its flanks, render vs reference."""
    px = to_px(feat["box"], w, h)
    x0, y0, x1, y1 = px
    flank = max(1, int(round(float(feat.get("flank", 0.01)) * (w if (x1 - x0) <= (y1 - y0) else h))))
    if (x1 - x0) <= (y1 - y0):                      # vertical element: flanks left and right
        sides = [(max(0, x0 - flank), y0, x0, y1), (x1, y0, min(w, x1 + flank), y1)]
    else:                                           # horizontal element: flanks above and below
        sides = [(x0, max(0, y0 - flank), x1, y0), (x0, y1, x1, min(h, y1 + flank))]
    sides = [s for s in sides if s[2] > s[0] and s[3] > s[1]]
    if not sides:
        raise InputError("feature %r: no room for flanks inside the image" % feat.get("name", "?"))

    def contrast(img):
        flank_mean = float(np.mean([_mean(img.luma, s) for s in sides]))
        return flank_mean - _mean(img.luma, px)      # positive = element darker than its surroundings

    con_r, con_f = contrast(render), contrast(ref)
    min_ratio = float(feat.get("min_ratio", 0.25))
    ratio = con_r / con_f if abs(con_f) >= 1.0 else None
    reasons = []
    if ratio is None:
        reasons.append("reference contrast %.1f is below 1 level: the box does not sit on the element" % con_f)
    elif ratio < min_ratio:
        reasons.append("NOT VISIBLE: render contrast %.1f is %.0f%% of the reference's %.1f (needs >= %.0f%%)"
                       % (con_r, 100.0 * ratio, con_f, 100.0 * min_ratio))
    return {"name": feat.get("name", "?"), "kind": "line", "box_px": list(px), "flank_px": flank,
            "contrast_render": _r(con_r), "contrast_reference": _r(con_f),
            "ratio": _r(ratio, 3), "min_ratio": min_ratio, "pass": not reasons, "reasons": reasons}


def measure(render, reference, spec, tolerance, centroid_tol, bright_percent):
    """Core of the script; returns the result dict (no I/O)."""
    w, h = render.size
    boxes_px = {b["name"]: to_px(b["box"], w, h) for b in spec["boxes"]}
    rows, warnings = [], []
    for b in spec["boxes"]:
        px = boxes_px[b["name"]]
        rl, rlin = _mean(render.luma, px), _mean(render.lin_y, px)
        row = {"name": b["name"], "box_norm": [round(v, 4) for v in b["box"]], "box_px": list(px),
               "render_luma": _r(rl), "render_linear": round(rlin, 5),
               "reference_luma": None, "reference_linear": None, "target": b["target"],
               "delta_vs_reference": None, "delta_vs_target": None, "delta": None,
               "tolerance": b["tolerance"] if b["tolerance"] is not None else tolerance, "pass": None}
        if reference is not None:
            fl, flin = _mean(reference.luma, px), _mean(reference.lin_y, px)
            row.update({"reference_luma": _r(fl), "reference_linear": round(flin, 5), "delta_vs_reference": _r(rl - fl)})
        if b["target"] is not None:
            row["delta_vs_target"] = _r(rl - b["target"])
        row["delta"] = row["delta_vs_target"] if b["target"] is not None else row["delta_vs_reference"]
        if row["delta"] is not None:
            row["pass"] = bool(abs(row["delta"]) <= row["tolerance"])
        rows.append(row)
    judged = [r for r in rows if r["pass"] is not None]
    if not judged:
        raise InputError("nothing to compare: give --reference or a per-box \"target\" in the boxes JSON")
    deltas = [abs(r["delta"]) for r in judged]
    summary = {"n_boxes": len(rows), "n_judged": len(judged), "n_pass": sum(1 for r in judged if r["pass"]),
               "max_abs_delta": _r(max(deltas)), "mean_abs_delta": _r(sum(deltas) / len(deltas)),
               "global_mean_render": _r(render.luma.mean()),
               "global_mean_reference": None if reference is None else _r(reference.luma.mean())}
    if reference is not None:
        summary["global_delta"] = _r(render.luma.mean() - reference.luma.mean())
    uv = unique_levels(render.luma)
    result = {"unique_values": uv, "suspect_blank": bool(uv < BLANK_THRESHOLD), "boxes": rows, "summary": summary}
    if result["suspect_blank"]:
        warnings.append("render has only %d distinct grey levels: blank or flat frame, the numbers mean nothing" % uv)

    result["brightest_percent"] = None
    if reference is not None:
        br, bf = brightest_percent(render.luma, bright_percent), brightest_percent(reference.luma, bright_percent)
        dx = (br["centroid_norm"][0] - bf["centroid_norm"][0]) * w
        dy = (br["centroid_norm"][1] - bf["centroid_norm"][1]) * h
        dist = math.hypot(dx, dy) / math.hypot(w, h)
        result["brightest_percent"] = {"render": br, "reference": bf, "centroid_distance_diag": round(dist, 4),
                                       "tolerance": centroid_tol, "pass": bool(dist <= centroid_tol)}
    feats = []
    if spec["features"]:
        if reference is None:
            raise InputError("feature checks need --reference")
        for feat in spec["features"]:
            kind = feat.get("kind", "patch")
            if kind == "patch":
                feats.append(check_patch(feat, render, reference, boxes_px, w, h, tolerance))
            elif kind == "line":
                feats.append(check_line(feat, render, reference, w, h))
            else:
                raise InputError("feature %r: unknown kind %r (use patch or line)" % (feat.get("name"), kind))
    result["features"] = feats
    ok = (not result["suspect_blank"]) and all(r["pass"] for r in judged)
    if result["brightest_percent"] is not None:
        ok = ok and result["brightest_percent"]["pass"]
    ok = ok and all(f["pass"] for f in feats)
    result["pass"] = bool(ok)
    result["warnings"] = warnings
    return result


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        description="Measure a scratch render against a reference: per-box mean luma, deltas, brightest-1%% "
                    "centroid, optional per-event feature checks. Run it after every light / world / exposure "
                    "change and BEFORE the iteration render. Exit 0 = within tolerance, 1 = outside tolerance "
                    "or blank render, 2 = input error.")
    ap.add_argument("--render", required=True, help="the scratch render (png/jpg/exr/npy)")
    ap.add_argument("--reference", help="reference image the render is compared with")
    ap.add_argument("--boxes", help="boxes JSON (normalised 0-1); default is a --grid")
    ap.add_argument("--grid", default=DEFAULT_GRID, help="COLSxROWS grid when no --boxes (default %s)" % DEFAULT_GRID)
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE,
                    help="max |render - target| per box, luma levels 0-255 (default %g)" % DEFAULT_TOLERANCE)
    ap.add_argument("--centroid-tol", type=float, default=DEFAULT_CENTROID_TOL,
                    help="max brightest-percent centroid distance as a fraction of the image diagonal (default %g)"
                         % DEFAULT_CENTROID_TOL)
    ap.add_argument("--bright-percent", type=float, default=1.0, help="percent of brightest pixels used for the centroid")
    ap.add_argument("--crop", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"),
                    help="crop the reference first (reference pixels), as a view's crop in the spec")
    ap.add_argument("--fit", choices=("letterbox", "stretch"), default="letterbox",
                    help="how the reference is fitted to the render size (default letterbox, as compare_views.py)")
    ap.add_argument("--render-space", choices=("auto", "srgb", "linear"), default="auto",
                    help="how to read the render's numbers (auto: exr/npy linear, others sRGB)")
    ap.add_argument("--reference-space", choices=("auto", "srgb", "linear"), default="auto")
    ap.add_argument("--exr-layer", help="channel prefix for layered EXRs, e.g. ViewLayer.Combined")
    ap.add_argument("--wait", type=float, default=0.0,
                    help="seconds to wait for the render file to exist and stop growing")
    ap.add_argument("--out", help="result JSON path (default: <render>_luminance.json next to the render)")
    ap.add_argument("--report-only", action="store_true", help="exit 0 even when outside tolerance")
    return ap


def run(args):
    if args.wait and not wait_for_file(args.render, args.wait):
        raise InputError("render not written after %.0f s: %s" % (args.wait, args.render))
    render = load_image(args.render, args.render_space, args.exr_layer)
    reference = None
    if args.reference:
        reference = load_image(args.reference, args.reference_space, args.exr_layer)
    spec = load_boxes(args.boxes, args.grid)
    fit_notes = []
    if reference is not None:
        raspect, fasp = render.size[0] / float(render.size[1]), reference.size[0] / float(reference.size[1])
        crop_aspect = fasp
        if args.crop:
            cw, ch = args.crop[2] - args.crop[0], args.crop[3] - args.crop[1]
            if cw <= 0 or ch <= 0:
                raise InputError("--crop is empty: %s" % args.crop)
            crop_aspect = cw / float(ch)
        if abs(crop_aspect - raspect) / raspect > 0.01:
            fit_notes.append("reference aspect %.3f differs from render %.3f: %s fit applied; box coordinates "
                             "refer to the fitted frame" % (crop_aspect, raspect, args.fit))
        reference = fit_to_size(reference, render.size, args.crop, args.fit)
    print("render:     %s  %dx%d  %d bytes  read as %s" % (args.render, render.size[0], render.size[1], render.nbytes, render.space))
    print("reference:  %s" % (args.reference or "none (targets only)"))
    print("boxes:      %d from %s | tolerance %g luma | brightest %g%% centroid tolerance %g of diagonal"
          % (len(spec["boxes"]), spec["source"], args.tolerance, args.bright_percent, args.centroid_tol))
    for part in render.parts:
        print("EXR part %d channels: %s%s" % (part["index"], ", ".join(part["channels"]), "  <- used" if part.get("used") else ""))
    result = measure(render, reference, spec, args.tolerance, args.centroid_tol, args.bright_percent)
    result.update({"tool": "scratch_luminance", "created_utc": datetime.now(timezone.utc).isoformat(),
                   "render": os.path.abspath(args.render), "render_size": list(render.size), "render_bytes": render.nbytes,
                   "reference": os.path.abspath(args.reference) if args.reference else None,
                   "tolerance": args.tolerance, "boxes_source": spec["source"]})
    result["warnings"] = result["warnings"] + fit_notes + render.notes + (reference.notes if reference else [])
    return result


def print_report(res):
    print("")
    print("%-22s %9s %9s %9s %7s  %s" % ("box", "render", "compared", "delta", "tol", ""))
    for r in res["boxes"]:
        compared = r["target"] if r["target"] is not None else r["reference_luma"]
        if r["pass"] is None:
            print("%-22s %9.1f %9s %9s %7.1f  not judged" % (r["name"], r["render_luma"], "-", "-", r["tolerance"]))
        else:
            print("%-22s %9.1f %9.1f %+9.1f %7.1f  %s" % (r["name"], r["render_luma"], compared, r["delta"], r["tolerance"],
                                                         "ok" if r["pass"] else "FAIL"))
    s = res["summary"]
    print("boxes ok %d/%d  max|delta| %.1f  mean|delta| %.1f  global mean %.1f vs %s" % (
        s["n_pass"], s["n_judged"], s["max_abs_delta"], s["mean_abs_delta"], s["global_mean_render"], s["global_mean_reference"]))
    bp = res["brightest_percent"]
    if bp:
        print("brightest %g%%: render centroid %s  reference centroid %s  distance %.3f of diagonal (tol %g)  %s" % (
            bp["render"]["percent"], bp["render"]["centroid_norm"], bp["reference"]["centroid_norm"],
            bp["centroid_distance_diag"], bp["tolerance"], "ok" if bp["pass"] else "FAIL"))
    for f in res["features"]:
        print("feature %-18s %-5s %s %s" % (f["name"], f["kind"], "ok" if f["pass"] else "FAIL", "; ".join(f["reasons"])))
    for w in res["warnings"]:
        print("WARNING: " + w)
    print("unique grey levels %d%s" % (res["unique_values"], "  SUSPECT BLANK" if res["suspect_blank"] else ""))
    print("OVERALL: %s" % ("PASS" if res["pass"] else "FAIL"))


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        res = run(args)
    except InputError as exc:
        sys.stderr.write("ERROR: %s\n" % exc)
        return 2
    out = args.out or (os.path.splitext(args.render)[0] + "_luminance.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
    except OSError as exc:
        sys.stderr.write("ERROR: cannot write %s (%s)\n" % (out, exc))
        return 2
    print_report(res)
    print("result: %s" % out)
    if res["pass"] or args.report_only:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
