#!/usr/bin/env python
"""Prove a flat colour-ID pass shows the right subject, framed as designed, before a paid reskin.

    check_id_pass.py ID.png LEGEND.json [--other-colour 808080] [--background 000000]
        [--expect KEY:left:277.3] [--surround 505050 --opening ROW,LEFT,RIGHT]
        [--grey GREY.png] [--depth D.exr --depth-at X,Y,METRES]

LEGEND is {"key": "#FF0000", ...}. A value may be {"colour": "#FF0000", "optional": true}
for an item that may be hidden from this camera. --subject picks one sub-table from a
legend written per subject ({"items": {"subject": {...}}}).

A check is only worth running if a wrong render would fail it. A blank or mis-aimed
frame fails here, and so does:
  - a key with no pixels, or a legend key that is empty (a Boolean or merge can hand an
    owner attribute to faces that are not an item; every later colour then shifts)
  - any pixel of the flat colour used for everything that is not the subject
  - a flat colour the legend does not know (a new decal, helper or cutter)
  - a legend key outside --registry (palettes repeat between subjects, so colours alone
    cannot tell one subject's legend from another's of the same length)
  - a feature away from the position predicted from the camera design
  - a depth away from the designed distance
  - ID edges that do not sit on the grey render's edges

Colours are classified, not read. Renderers offset every channel slightly, so exact
matching finds almost nothing, and an anti-aliased edge between two palette colours can
sit on a third. So a pixel counts only in the CORE of a flat area (all four neighbours
within 3 levels) plus 1 px of dilation; anything else is reported as edge. Items
thinner than about 3 px have no core and read as missing.

Exit 0 = pass, 1 = fail, 2 = bad usage.
"""
import argparse
import json
import os
import re
import sys

os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2  # noqa: E402
import numpy as np  # noqa: E402

CORE_LEVELS = 3
SHIFTED_CONTROL_PX = 40


def parse_colour(value):
    text = str(value).strip().lstrip("#")
    if not re.fullmatch(r"[0-9a-fA-F]{6}", text):
        raise ValueError("not a colour: %r" % value)
    return np.array([int(text[index:index + 2], 16) for index in (0, 2, 4)], np.float32)


def read_rgb(path):
    """RGB as float 0..255 from any bit depth."""
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("cannot read " + path)
    if image.ndim == 2:
        image = np.dstack([image] * 3)
    rgb = image[:, :, 2::-1].astype(np.float32)
    if image.dtype == np.uint16:
        rgb /= 257.0
    elif image.dtype != np.uint8:
        rgb *= 255.0
    return rgb


def read_legend(path, subject):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data.get("legend"), dict):
        data = data["legend"]
    table = data.get("items", data)
    if subject:
        if subject not in table:
            raise ValueError("subject %s is not in %s" % (subject, path))
        table = table[subject]
    entries = {}
    for key, value in table.items():
        optional = isinstance(value, dict) and value.get("optional", False)
        colour = value["colour"] if isinstance(value, dict) else value
        entries[key] = (parse_colour(colour), bool(optional))
    return entries


def flat_mask(rgb):
    """Pixels whose four neighbours all sit within CORE_LEVELS of them."""
    flat = np.ones(rgb.shape[:2], bool)
    for axis in (0, 1):
        step = np.abs(np.diff(rgb, axis=axis)).max(axis=2) <= CORE_LEVELS
        if axis == 0:
            flat[:-1, :] &= step
            flat[1:, :] &= step
        else:
            flat[:, :-1] &= step
            flat[:, 1:] &= step
    return flat


def colour_mask(rgb, colour, tolerance):
    return np.abs(rgb - colour).max(axis=2) <= tolerance


def classified(rgb, colour, tolerance, flat):
    """(pixels counted as this colour, edge pixels only near the colour)."""
    near = colour_mask(rgb, colour, tolerance)
    core = near & flat
    grown = cv2.dilate(np.uint8(core), np.ones((3, 3), np.uint8)).astype(bool)
    counted = grown & near
    return counted, near & ~counted


def key_measure(mask, side):
    """Edge position of a mask's bounding box, in pixels."""
    rows, cols = np.where(mask)
    if not len(rows):
        return None
    return {"left": float(cols.min()), "right": float(cols.max() + 1),
            "top": float(rows.min()), "bottom": float(rows.max() + 1)}[side]


def edge_overlap(labels, grey_edges, shift=0):
    """Share of ID edges with a grey edge within 2 px."""
    boundary = np.zeros(labels.shape, bool)
    boundary[:-1, :] |= labels[:-1, :] != labels[1:, :]
    boundary[:, :-1] |= labels[:, :-1] != labels[:, 1:]
    if not boundary.any():
        return 0.0
    moved = np.roll(grey_edges, shift, axis=1) if shift else grey_edges
    near = cv2.dilate(np.uint8(moved), np.ones((5, 5), np.uint8)).astype(bool)
    return float((boundary & near).sum()) / boundary.sum()


def grey_edges_of(path):
    grey = cv2.cvtColor(np.clip(read_rgb(path), 0, 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    return cv2.Canny(cv2.GaussianBlur(grey, (0, 0), 1.0), 30, 90) > 0


def read_depth(path, value_range):
    """One channel of scene depth, decoded from 0..1 through value_range when given."""
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError("cannot read depth " + path)
    if image.ndim == 3:
        if np.ptp(image[:, :, :3].astype(np.float64), axis=2).max() > 1e-6:
            raise ValueError("%s holds colour, not depth (a multi-part EXR reads as its first part only)" % path)
        image = image[:, :, 0]
    depth = image.astype(np.float64)
    if not value_range:
        return depth
    if image.dtype == np.uint16:
        depth /= 65535.0
    elif image.dtype == np.uint8:
        depth /= 255.0
    return value_range[0] + depth * (value_range[1] - value_range[0])


def opening_edges(surround, row):
    """First and last column in a row that are not the surround."""
    cols = np.where(~surround[row])[0]
    return (float(cols[0]), float(cols[-1] + 1)) if len(cols) else (None, None)


def opening_top(surround, col):
    rows = np.where(~surround[:, col])[0]
    return float(rows[0]) if len(rows) else None


class Report(object):
    def __init__(self):
        self.failures, self.checks = [], 0

    def check(self, passed, message):
        self.checks += 1
        if not passed:
            self.failures.append(message)
            print("FAIL " + message)
        return passed


def parse_expect(text, default_tolerance):
    parts = text.rsplit(":", 3) if text.count(":") >= 3 else text.rsplit(":", 2)
    if len(parts) == 3:
        parts.append(default_tolerance)
    key, side, value, tolerance = parts
    if side not in ("left", "right", "top", "bottom"):
        raise ValueError("--expect side must be left, right, top or bottom: " + text)
    return key, side, float(value), float(tolerance)


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("id_pass")
    parser.add_argument("legend")
    parser.add_argument("--subject", help="sub-table of a per-subject legend")
    parser.add_argument("--other-colour", help="flat colour of everything that is not the subject")
    parser.add_argument("--other-max", type=int, default=0, help="pixels of that colour allowed")
    parser.add_argument("--background", action="append", default=[], metavar="HEX",
                        help="flat colours that are not items (repeat)")
    parser.add_argument("--tolerance", type=float, default=8.0, help="colour match, levels of 255")
    parser.add_argument("--unknown-min", type=int, default=25,
                        help="smallest flat area of an unknown colour to report, px")
    parser.add_argument("--expect", action="append", default=[], metavar="KEY:SIDE:PX[:TOL]",
                        help="predicted edge of a key's bounding box (left, right, top, bottom)")
    parser.add_argument("--expect-tolerance", type=float, default=2.0)
    parser.add_argument("--registry", help="JSON list (or object) of the keys this subject really has")
    parser.add_argument("--surround", action="append", default=[], metavar="HEX",
                        help="flat colours of what frames an opening, for the two options below (repeat)")
    parser.add_argument("--opening", action="append", default=[], metavar="ROW,LEFT,RIGHT",
                        help="predicted first and last column that are not the surround on this row")
    parser.add_argument("--opening-top", action="append", default=[], metavar="COL,ROW",
                        help="predicted first row that is not the surround in this column")
    parser.add_argument("--grey", help="grey render of the same camera")
    parser.add_argument("--min-overlap", type=float, default=0.5, help="ID edges on grey edges, 0..1")
    parser.add_argument("--depth", help="single-channel depth, or 0..1 depth with --depth-range")
    parser.add_argument("--depth-range", nargs=2, type=float, metavar=("NEAR", "FAR"),
                        help="scene depth at 0 and at 1 of a normalised depth image")
    parser.add_argument("--depth-at", action="append", default=[], metavar="X,Y,VALUE[,TOL]")
    parser.add_argument("--json", help="write the pixel counts here")
    return parser


def run(args):
    report = Report()
    rgb = read_rgb(args.id_pass)
    legend = read_legend(args.legend, args.subject)
    height, width = rgb.shape[:2]
    report.check(bool(legend), "the legend is empty")
    for key in legend:
        report.check(bool(key.strip()), "the legend has an empty key: an owner attribute reached something "
                                        "that is not an item, and later colours may have shifted")
    if args.registry:
        with open(args.registry, encoding="utf-8") as fh:
            registry = set(json.load(fh))
        for key in sorted(set(legend) - registry):
            report.check(False, "legend key %s is not in the registry: wrong subject or a key nobody declared" % key)
    tolerance, flat = args.tolerance, flat_mask(rgb)
    known = np.zeros((height, width), bool)
    labels = np.zeros((height, width), np.int32)
    masks, counts = {}, {}
    for index, (key, (colour, optional)) in enumerate(sorted(legend.items())):
        counted, edge = classified(rgb, colour, tolerance, flat)
        masks[key], counts[key] = counted, int(counted.sum())
        known |= counted | edge
        labels[counted] = index + 1
        print("KEY %-28s %8d px, edge %6d" % (key, counts[key], int(edge.sum())))
        if optional:
            continue
        report.check(counts[key] > 0, "key %s has no pixels (hidden, thinner than 3 px, or the wrong frame)" % key)

    if args.other_colour:
        other, edge = classified(rgb, parse_colour(args.other_colour), tolerance, flat)
        known |= other | edge
        labels[other] = len(legend) + 1
        print("OTHER %d px" % int(other.sum()))
        report.check(int(other.sum()) <= args.other_max, "%d px of the other-subject colour: this frame shows "
                                                         "someone else's items" % int(other.sum()))
    for value in args.background:
        background = classified(rgb, parse_colour(value), tolerance, flat)
        known |= background[0] | background[1]

    unknown = flat & ~known
    if unknown.any():
        packed = np.round(rgb[unknown] / 8.0).astype(np.int64) * 8
        colours, tally = np.unique(packed, axis=0, return_counts=True)
        for colour, count in sorted(zip(colours.tolist(), tally.tolist()), key=lambda item: -item[1])[:6]:
            if count >= args.unknown_min:
                report.check(False, "%d flat px of a colour the legend does not know: rgb %s" % (count, colour))

    for text in args.expect:
        key, side, predicted, allowed = parse_expect(text, args.expect_tolerance)
        if not report.check(key in masks, "--expect names unknown key %s" % key):
            continue
        measured = key_measure(masks[key], side)
        print("FEATURE %s %s predicted %.1f, measured %s" % (key, side, predicted, measured))
        report.check(measured is not None and abs(measured - predicted) <= allowed,
                     "%s %s is at %s, predicted %.1f (+-%.1f): the camera is not as designed"
                     % (key, side, measured, predicted, allowed))

    if (args.opening or args.opening_top) and not args.surround:
        raise ValueError("--opening needs --surround")
    surround = np.zeros((height, width), bool)
    for value in args.surround:
        surround |= colour_mask(rgb, parse_colour(value), tolerance)
    # A one pixel anti-aliased rim between two surround colours is still surround.
    surround = cv2.morphologyEx(np.uint8(surround), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)).astype(bool)
    for text in args.opening:
        row, left, right = [float(item) for item in text.split(",")]
        measured = opening_edges(surround, int(row))
        print("OPENING row %d predicted %.1f..%.1f, measured %s" % (row, left, right, measured))
        report.check(None not in measured and abs(measured[0] - left) <= args.expect_tolerance
                     and abs(measured[1] - right) <= args.expect_tolerance,
                     "opening on row %d is %s, predicted %.1f..%.1f: the camera is not as designed"
                     % (row, measured, left, right))
    for text in args.opening_top:
        col, predicted = [float(item) for item in text.split(",")]
        measured = opening_top(surround, int(col))
        print("OPENING column %d predicted top %.1f, measured %s" % (col, predicted, measured))
        report.check(measured is not None and abs(measured - predicted) <= args.expect_tolerance,
                     "opening top in column %d is %s, predicted %.1f: the camera is not as designed"
                     % (col, measured, predicted))

    if args.grey:
        grey_edges = grey_edges_of(args.grey)
        if not report.check(grey_edges.shape == (height, width), "the grey render is another size"):
            return report
        overlap = edge_overlap(labels, grey_edges)
        control = edge_overlap(labels, grey_edges, SHIFTED_CONTROL_PX)
        print("OVERLAP ID edges on grey edges %.3f (the same grey shifted %d px: %.3f)"
              % (overlap, SHIFTED_CONTROL_PX, control))
        report.check(overlap >= args.min_overlap, "ID edges miss the grey render: overlap %.3f" % overlap)
        report.check(overlap > control, "the overlap does not fall when the grey is shifted: the check saw nothing")

    if args.depth_at and not args.depth:
        raise ValueError("--depth-at needs --depth")
    for text in args.depth_at:
        depth = read_depth(args.depth, args.depth_range)
        parts = [float(item) for item in text.split(",")]
        x, y, wanted = int(parts[0]), int(parts[1]), parts[2]
        allowed = parts[3] if len(parts) > 3 else 0.01
        value = float(depth[y, x])
        print("DEPTH at %d,%d is %.4f, designed %.4f" % (x, y, value, wanted))
        report.check(abs(value - wanted) <= allowed, "depth %.4f at %d,%d, designed %.4f" % (value, x, y, wanted))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump({"size": [width, height], "pixels": counts}, fh, indent=1)
    return report


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        report = run(args)
    except (OSError, ValueError, KeyError, IndexError) as exc:
        print("ERROR %s" % exc)
        return 2
    verdict = "FAIL %d of %d" % (len(report.failures), report.checks) if report.failures else "PASS %d" % report.checks
    print("IDPASS %s checks" % verdict)
    return 1 if report.failures else 0


if __name__ == "__main__":
    sys.exit(main())
