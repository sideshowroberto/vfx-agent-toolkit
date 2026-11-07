#!/usr/bin/env python
"""Record what a saved scene really was, so a later question is answered from the record and not from a path.

Any python:
    hip_provenance.py stamp A.hip B.hip --out record.json      bytes, time and sha256 of each file
    hip_provenance.py check record.json                        fail if any file is no longer what was recorded
    hip_provenance.py camdiff RECORD_A RECORD_B                how far each recorded camera moved
hython:
    hip_provenance.py stamp SCENE.hip --cameras /obj/cam1 /obj/cam2 --frames 1001 1050 --out record.json

A live session or render script can import this file and put provenance(path) and camera_samples(...) in its record.

A file path is not provenance: artists save over versioned names. One record said "v091" and the v091 on disk the next
morning was another file, so dumping its camera read "no change" when the framing had moved. Stamp the hip and its
cameras at the moment of the render.

An empty diff says two files match; it does not say the work is missing. An artist re-saved v107 over the agent's copy,
so v107 and v108 matched, and an older v106 to v107 result was already stale. Run check before reusing an old diff
result, and when two versions match, diff against the last version from before the work in question.

Exit 0 = pass, 1 = fail, 2 = bad usage.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

DEFAULT_TOLERANCE = 0.0005
FOCAL_TOLERANCE = 0.001


def provenance(path):
    """bytes, mtime and sha256 of a file, read now."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    status = os.stat(path)
    return {"path": os.path.abspath(path), "bytes": status.st_size, "sha256": digest.hexdigest(),
            "mtime": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(status.st_mtime))}


def camera_samples(paths, frames):
    """World matrix, focal, aperture and resolution of each camera at each frame. Needs a loaded scene."""
    import hou
    samples = {}
    for path in paths:
        node = hou.node(path)
        if node is None or node.parm("focal") is None:
            raise ValueError("%s is not a camera in this scene" % path)
        samples[path] = [{"frame": frame,
                          "world": [round(value, 9) for value in node.worldTransformAtTime(hou.frameToTime(frame)).asTuple()],
                          "focal": node.parm("focal").evalAtFrame(frame),
                          "aperture": node.parm("aperture").evalAtFrame(frame),
                          "res": [node.evalParm("resx"), node.evalParm("resy")]} for frame in frames]
    return samples


def same_size_pairs(stamps):
    """Same size is the clue that counts: two saves of one scene can match in content and differ in sha256."""
    return [(first, second) for index, first in enumerate(stamps) for second in stamps[index + 1:]
            if first["bytes"] == second["bytes"]]


def cmd_stamp(args):
    stamps = []
    for path in args.files:
        stamps.append(provenance(path))
        print("STAMP %s %d bytes %s %s" % (
            os.path.basename(path), stamps[-1]["bytes"], stamps[-1]["mtime"], stamps[-1]["sha256"][:12]))
    for first, second in same_size_pairs(stamps):
        print("NOTE %s and %s are the same %s: if they diff empty that says nothing about the work, "
              "diff against the last version from before it" % (
                  os.path.basename(first["path"]), os.path.basename(second["path"]),
                  "file" if first["sha256"] == second["sha256"] else "size"))
    record = {"stamped": time.strftime("%Y-%m-%dT%H:%M:%S"), "files": stamps}
    if args.cameras:
        import hou
        hou.hipFile.load(args.files[0], suppress_save_prompt=True, ignore_load_warnings=True)
        record["cameras"] = camera_samples(args.cameras, args.frames)
        print("CAMERAS %d at %d frames" % (len(args.cameras), len(args.frames)))
        if provenance(args.files[0])["sha256"] != stamps[0]["sha256"]:
            print("FAIL the hip changed while it was stamped")
            return 1
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
    return 0


def cmd_check(args):
    with open(args.record, encoding="utf-8") as fh:
        record = json.load(fh)
    failed = 0
    for stamp in record["files"]:
        path, name = stamp["path"], os.path.basename(stamp["path"])
        if not os.path.exists(path):
            print("FAIL %s is gone" % path)
            failed += 1
            continue
        now = provenance(path)
        if now["sha256"] == stamp["sha256"]:
            print("SAME %s" % name)
            continue
        failed += 1
        print("FAIL %s was saved over: %d bytes at %s when recorded, %d bytes at %s now" % (
            name, stamp["bytes"], stamp["mtime"], now["bytes"], now["mtime"]))
    print("CHECK %s" % ("FAIL %d" % failed if failed else "PASS"))
    return 1 if failed else 0


def camera_moves(before, after, tolerance):
    """Lines describing cameras that moved, and whether anything could not be compared."""
    lines, blind = [], []
    for path in sorted(set(before) | set(after)):
        if path not in before or path not in after:
            blind.append("%s is in one record only" % path)
            continue
        by_frame = {sample["frame"]: sample for sample in after[path]}
        for sample in before[path]:
            other = by_frame.get(sample["frame"])
            if other is None:
                blind.append("%s has no frame %s in both records" % (path, sample["frame"]))
                continue
            shift = math.sqrt(sum((sample["world"][index] - other["world"][index]) ** 2 for index in (12, 13, 14)))
            turn = max(abs(a - b) for a, b in zip(sample["world"][:12], other["world"][:12]))
            focal = abs(sample["focal"] - other["focal"])
            if shift > tolerance or turn > tolerance or focal > FOCAL_TOLERANCE:
                lines.append("%s frame %s moved %.4f, rotation term %.5f, focal %.3f" % (
                    path, sample["frame"], shift, turn, focal))
    return lines, blind


def cmd_camdiff(args):
    records = []
    for path in (args.record_a, args.record_b):
        with open(path, encoding="utf-8") as fh:
            records.append(json.load(fh))
    if not records[0].get("cameras") or not records[1].get("cameras"):
        print("FAIL a record holds no camera samples: nothing was compared")
        return 1
    lines, blind = camera_moves(records[0]["cameras"], records[1]["cameras"], args.tolerance)
    for line in lines:
        print("MOVED " + line)
    for line in blind:
        print("FAIL " + line)
    print("CAMDIFF %s" % ("FAIL %d" % (len(lines) + len(blind)) if lines or blind else "SAME"))
    return 1 if lines or blind else 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    stamp = sub.add_parser("stamp")
    stamp.add_argument("files", nargs="+")
    stamp.add_argument("--cameras", nargs="+", help="OBJ cameras, sampled from the first file; needs hython")
    stamp.add_argument("--frames", nargs="+", type=float, default=[1.0])
    stamp.add_argument("--out", required=True)
    stamp.set_defaults(run=cmd_stamp)
    check = sub.add_parser("check")
    check.add_argument("record")
    check.set_defaults(run=cmd_check)
    camdiff = sub.add_parser("camdiff")
    camdiff.add_argument("record_a")
    camdiff.add_argument("record_b")
    camdiff.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, help="scene units")
    camdiff.set_defaults(run=cmd_camdiff)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except (OSError, ValueError, KeyError) as exc:
        print("ERROR %s" % exc)
        return 2


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.exit(code)
