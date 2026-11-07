#!/usr/bin/env python
"""Prove which engine a Karma render really used, and run a headless usdrender ROP with a log that can see.

Any python:
    karma_rop.py meta IMAGE.exr [...] [--expect xpu|cpu]     engine, delegate, GPU share, time, from the EXR header
    karma_rop.py scan HUSK_LOG [...]                         texture, GPU and licence trouble in husk's own logs
    karma_rop.py estimate REPORT_A REPORT_B --images N       time a long run from two test lengths

hython:
    karma_rop.py audit [SCENE.hip] [--expect xpu] [--fix]    every usdrender ROP and its delegate
    karma_rop.py render SCENE.hip --rop /stage/render --frames 1001 1010 --output DIR/name.$F4.exr --expect xpu

A live session can call audit_scene("xpu", fix=True) after importing this file; audit and render never save the hip.

The node that launches husk decides the renderer. A usdrender_rop renders Karma CPU unless its delegate says XPU,
whatever a Karma Render Settings node says, so the only evidence of the engine is the image's own header. Even there
"Karma (xpu)" can mean every sample came from the Embree CPU device, so meta reads the per-device share too.

With the ROP's defaults husk writes nowhere a headless run can read, so a grep of hython's output reports a clean
render whatever happened. render turns the log on, and an empty log is a failed check, not a clean one.

A short test also hides stage pre-cook, which allframesatonce pays at every time sample before husk starts. Time a
long run with estimate from two lengths, not by scaling one short test.

Exit 0 = pass, 1 = fail, 2 = bad usage.
"""
import argparse
import hashlib
import json
import os
import re
import struct
import subprocess
import sys
import time

DELEGATES = {"xpu": "BRAY_HdKarmaXPU", "cpu": "BRAY_HdKarma"}
BENIGN = ("failure_retries", "max_errors_per_file")
TROUBLE = ("unable", "fail", "cannot", "can't", "error", "missing", "not found")
TEXTURE = ("texture", "image", ".png", ".jpg", ".exr", ".tx", ".rat", ".tif")
HARD = ("licen", "out of memory", "cuda", "optix error", "device lost", "gpu error")
HEADER_BYTES = 4 * 1024 * 1024
MIN_ESTIMATE_IMAGES = 20
EXR_MAGIC = 0x01312F76
MULTIPART_FLAG = 0x1000


def read_exr_headers(path):
    """Every part's header attributes, with plain python: no OpenEXR build reads all the parts by default."""
    with open(path, "rb") as fh:
        data = fh.read(HEADER_BYTES)
    if len(data) < 8 or struct.unpack("<I", data[:4])[0] != EXR_MAGIC:
        raise ValueError("%s is not an EXR" % path)
    multipart = bool(struct.unpack("<I", data[4:8])[0] & MULTIPART_FLAG)
    pos, parts = 8, []
    try:
        while True:
            attributes = {}
            while True:
                end = data.index(b"\0", pos)
                name = data[pos:end].decode("latin-1")
                pos = end + 1
                if not name:
                    break
                end = data.index(b"\0", pos)
                kind = data[pos:end].decode("latin-1")
                pos = end + 1
                size = struct.unpack("<I", data[pos:pos + 4])[0]
                pos += 4
                attributes[name] = (kind, data[pos:pos + size])
                pos += size
            parts.append(attributes)
            if not multipart or data[pos:pos + 1] in (b"\0", b""):
                return parts
    except (ValueError, struct.error):
        raise ValueError("%s: header is damaged or longer than %d bytes" % (path, HEADER_BYTES))


def header_text(attributes, name):
    kind, value = attributes.get(name, ("", b""))
    return value.decode("utf-8", "replace") if kind == "string" else ""


def read_meta(path):
    attributes = read_exr_headers(path)[0]
    software = header_text(attributes, "Software")
    engine = re.search(r"Karma \((\w+)\)", software)
    command = header_text(attributes, "husk:command")
    delegate = re.search(r"(?:^|\s)-R\s+\"?([\w.]+)", command)
    meta = {"path": path, "software": software, "engine": engine.group(1).lower() if engine else None,
            "delegate": delegate.group(1) if delegate else None,
            "render_time": header_text(attributes, "renderTime_s"), "devices": None}
    try:
        stats = json.loads(header_text(attributes, "husk:render_stats"))
    except ValueError:
        return meta
    devices = stats.get("xpu_devices")
    if devices is not None:
        meta["devices"] = [{"type": item.get("xpu_device_type"), "label": item.get("xpu_device_label"),
                            "share": item.get("xpu_device_contrib", 0), "error": item.get("xpu_device_error", "")}
                           for item in devices]
    return meta


def check_meta(meta, expect):
    """Reasons this image is not what was expected; empty means it is."""
    problems = []
    if meta["engine"] is None:
        return ["no Karma engine in the header (Software: %r): not a Karma image, or the header was rewritten"
                % meta["software"]]
    if expect and meta["engine"] != expect:
        problems.append("rendered on %s, expected %s: check the ROP delegate, not the settings node"
                        % (meta["engine"], expect))
    if expect and meta["delegate"] and meta["delegate"] != DELEGATES[expect]:
        problems.append("husk ran with -R %s" % meta["delegate"])
    if meta["engine"] == "xpu":
        devices = meta["devices"]
        if devices is None:
            problems.append("no xpu_devices in the header: the GPU share cannot be read")
        elif not sum(item["share"] for item in devices if item["type"] != "EmbreeCPU"):
            problems.append("XPU in name only: no GPU device contributed a sample (a render of a second or "
                            "less can end on Embree before the GPU joins; judge on a real frame)")
        for item in devices or []:
            if item["error"]:
                problems.append("device %s reported: %s" % (item["label"], item["error"]))
    return problems


def find_tool(name):
    roots = [os.path.join(os.environ.get("HFS", ""), "bin"), os.path.dirname(sys.executable)]
    for root in roots:
        for candidate in (name + ".exe", name):
            if os.path.isfile(os.path.join(root, candidate)):
                return os.path.join(root, candidate)
    return None


def pixel_range(path, tool):
    """(lowest, highest) channel value of the first part, or None when the tool could not say."""
    out = subprocess.run([tool, "--stats", path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, errors="replace").stdout
    low = re.search(r"Stats Min:\s*([-\d.e+ ]+?)\s*\(float", out)
    high = re.search(r"Stats Max:\s*([-\d.e+ ]+?)\s*\(float", out)
    if not low or not high:
        return None
    return min(float(item) for item in low.group(1).split()), max(float(item) for item in high.group(1).split())


def scan_logs(paths):
    """Trouble in husk's own logs. log_lines 0 means the check saw nothing, which is a failure."""
    found = {"log_lines": 0, "texture": [], "hard": [], "other": []}
    for path in paths:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                found["log_lines"] += 1
                low = line.lower()
                if any(word in low for word in BENIGN):
                    continue  # husk echoes option names that hold error words at verbose 2
                bad = any(word in low for word in TROUBLE)
                if bad and any(word in low for word in TEXTURE):
                    found["texture"].append(line.strip()[:240])
                elif any(word in low for word in HARD):
                    found["hard"].append(line.strip()[:240])
                elif bad:
                    found["other"].append(line.strip()[:240])
    return found


class Report(object):
    def __init__(self):
        self.failures = []

    def check(self, passed, message):
        if not passed:
            self.failures.append(message)
            print("FAIL " + message)
        return passed

    def finish(self, label):
        print("%s %s" % (label, "FAIL %d" % len(self.failures) if self.failures else "PASS"))
        return 1 if self.failures else 0


def report_scan(report, found):
    print("SCAN %d lines, %d texture, %d GPU or licence, %d other" % (
        found["log_lines"], len(found["texture"]), len(found["hard"]), len(found["other"])))
    report.check(found["log_lines"] > 0, "the husk log is empty: this check saw nothing")
    report.check(not found["texture"], "%d texture errors, first: %s" % (len(found["texture"]), found["texture"][:1]))
    report.check(not found["hard"], "%d GPU or licence lines, first: %s" % (len(found["hard"]), found["hard"][:1]))
    for line in found["other"][:5]:
        print("NOTE " + line)


def report_meta(report, path, expect):
    meta = read_meta(path)
    shares = ", ".join("%s %s" % (item["type"], item["share"]) for item in meta["devices"] or [])
    print("META %s: %s, delegate %s, time %s, devices [%s]" % (
        os.path.basename(path), meta["software"], meta["delegate"], meta["render_time"], shares))
    for problem in check_meta(meta, expect):
        report.check(False, "%s: %s" % (os.path.basename(path), problem))
    return meta


def cmd_meta(args):
    report, tool = Report(), find_tool("hoiiotool")
    for path in args.images:
        report_meta(report, path, args.expect)
        limits = pixel_range(path, tool) if tool else None
        if limits:
            report.check(limits[1] > limits[0], "%s is one flat value" % os.path.basename(path))
    return report.finish("META")


def cmd_scan(args):
    report = Report()
    report_scan(report, scan_logs(args.logs))
    return report.finish("SCAN")


def cmd_estimate(args):
    report = Report()
    runs = []
    for path in (args.report_a, args.report_b):
        with open(path, encoding="utf-8") as fh:
            runs.append(json.load(fh)["timing"])
    runs.sort(key=lambda item: item["images"])
    short, long_run = runs
    extra = long_run["images"] - short["images"]
    if not report.check(extra > 0, "both reports hold %d images: two lengths are needed" % short["images"]):
        return report.finish("ESTIMATE")
    report.check(long_run["images"] >= MIN_ESTIMATE_IMAGES, "the longer run has %d images, under %d: per-sample "
                 "pre-cook will not show" % (long_run["images"], MIN_ESTIMATE_IMAGES))
    per_image = (long_run["seconds"] - short["seconds"]) / float(extra)
    launch = short["seconds"] - per_image * short["images"]
    total = launch + per_image * args.images
    print("ESTIMATE %.1f s per image, %.1f s launch, %d images = %.1f min" % (per_image, launch, args.images, total / 60))
    report.check(per_image > 0, "the longer run was not slower: these two runs do not measure a rate")
    return report.finish("ESTIMATE")


def usd_rops():
    import hou
    return [node for node in hou.node("/").allSubChildren() if "usdrender" in node.type().name()
            and node.parm("renderer") is not None]


def audit_scene(expect="xpu", fix=False):
    """List every usdrender ROP's delegate. fix sets it in memory and reads it back; nothing is saved."""
    wanted, wrong = DELEGATES[expect], []
    for node in usd_rops():
        parm = node.parm("renderer")
        state = parm.evalAsString()
        if state != wanted and fix:
            parm.set(wanted)
            state = parm.evalAsString()
            print("SET %s to %s" % (node.path(), state))
        print("ROP %s %s" % (node.path(), state))
        if state != wanted:
            wrong.append(node.path())
    return wrong


def cmd_audit(args):
    import hou
    report = Report()
    if args.hip:
        hou.hipFile.load(args.hip, suppress_save_prompt=True, ignore_load_warnings=True)
    rops = usd_rops()
    report.check(bool(rops), "no usdrender ROP in this scene")
    for path in audit_scene(args.expect, args.fix):
        report.check(False, "%s does not render on %s" % (path, args.expect))
    return report.finish("AUDIT")


def file_digest(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def gpu_free_mib():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True).stdout
        return int(out.split()[0])
    except (OSError, ValueError, IndexError):
        return None


def set_parm(node, name, value):
    parm = node.parm(name)
    if parm is None:
        raise ValueError("%s has no parm %s: not a usdrender ROP this tool knows" % (node.path(), name))
    parm.deleteAllKeyframes()
    parm.set(value)


def settings_node(rop):
    """The nearest upstream node that sets the image path, for a run with one husk process."""
    for node in rop.inputAncestors():
        if node.parm("picture") is not None:
            return node
    raise ValueError("--all-at-once needs a Karma settings node with a picture parm above %s" % rop.path())


def timing_from(files, started, seconds):
    times = sorted(os.path.getmtime(path) for path in files)
    gaps = sorted(later - earlier for earlier, later in zip(times, times[1:]))
    timing = {"images": len(files), "seconds": round(seconds, 1),
              "first_image_s": round(times[0] - started, 1) if times else None,
              "per_image_median_s": round(gaps[len(gaps) // 2], 2) if gaps else None}
    if timing["per_image_median_s"] is not None:
        timing["before_first_image_s"] = round(timing["first_image_s"] - timing["per_image_median_s"], 1)
    return timing


def cmd_render(args):
    import hou
    report = Report()
    free = gpu_free_mib()
    if args.expect == "xpu" and args.min_gpu_free_mib:
        print("GPU %s MiB free" % free)
        if not report.check(free is None or free >= args.min_gpu_free_mib, "only %s MiB of GPU memory free, need %d"
                            % (free, args.min_gpu_free_mib)):
            return report.finish("RENDER")
    log_dir = os.path.abspath(args.log_dir or os.path.dirname(args.output.replace("$F4", "0")) or ".")
    os.makedirs(log_dir, exist_ok=True)
    stem = os.path.join(log_dir, "husk_%s" % time.strftime("%Y%m%d_%H%M%S")).replace("\\", "/")
    logs = [stem + "_stdout.txt", stem + "_stderr.txt"]
    before = file_digest(args.hip)
    hou.hipFile.load(args.hip, suppress_save_prompt=True, ignore_load_warnings=True)
    rop = hou.node(args.rop)
    if rop is None or rop.parm("renderer") is None:
        raise ValueError("%s is not a usdrender ROP in %s" % (args.rop, args.hip))
    first, last, step = args.frames[0], args.frames[1], args.step
    for name, value in (("renderer", DELEGATES[args.expect]), ("husk_log", 1), ("husk_logappend", 0),
                        ("husk_stdout", logs[0]), ("husk_stderr", logs[1]), ("verbose", 2), ("alfprogress", 1),
                        ("trange", 1), ("f1", first), ("f2", last), ("f3", step),
                        ("allframesatonce", 1 if args.all_at_once else 0)):
        set_parm(rop, name, value)
    print("ROP %s delegate read back %s" % (rop.path(), rop.parm("renderer").evalAsString()))
    # One husk process ignores the ROP's output override: the path has to be on the stage.
    target = settings_node(rop) if args.all_at_once else rop
    name = "picture" if args.all_at_once else "outputimage"
    set_parm(target, name, args.output)
    count = int(round((last - first) / step)) + 1
    frames = [first + index * step for index in range(count)]
    files = [target.parm(name).evalAtFrame(frame) for frame in frames]
    if not report.check(len(set(files)) == count, "%d samples write only %d file names: the pattern loses the "
                        "fractional frames" % (count, len(set(files)))):
        return report.finish("RENDER")
    stale = [path for path in files if os.path.exists(path)]
    if not report.check(not stale, "%d output files exist already, first %s: an old image would pass every check"
                        % (len(stale), stale[:1])):
        return report.finish("RENDER")
    started = time.time()
    try:
        rop.render(frame_range=(first, last, step), verbose=False)
    except hou.OperationFailed as exc:
        report.check(False, "the ROP raised: %s" % str(exc)[:300])
    seconds = time.time() - started
    report.check(not rop.errors(), "ROP errors: %s" % (rop.errors(),))
    found = scan_logs(logs)
    report_scan(report, found)
    written = [path for path in files if os.path.exists(path)]
    report.check(len(written) == count, "%d of %d images written" % (len(written), count))
    tool = find_tool("hoiiotool")
    report.check(tool is not None, "hoiiotool not found: frames cannot be checked for content")
    metas = []
    for path in written:
        if path.lower().endswith(".exr"):
            metas.append(report_meta(report, path, args.expect))
        else:
            report.check(False, "%s is not an EXR: the engine cannot be proved" % path)
        limits = pixel_range(path, tool) if tool else None
        report.check(limits is not None and limits[1] > limits[0], "%s reads %s: a blank frame"
                     % (os.path.basename(path), limits))
    timing = timing_from(written, started, seconds)
    print("TIMING %s" % json.dumps(timing))
    if len(written) < MIN_ESTIMATE_IMAGES:
        print("NOTE under %d images: pre-cook per sample does not show, use estimate with a second length"
              % MIN_ESTIMATE_IMAGES)
    report.check(file_digest(args.hip) == before, "the hip changed on disk during this run")
    with open(stem + "_report.json", "w", encoding="utf-8") as fh:
        json.dump({"hip": args.hip, "rop": args.rop, "frames": frames, "logs": logs, "timing": timing,
                   "scan": found, "meta": metas, "failures": report.failures}, fh, indent=1)
    print("REPORT " + stem + "_report.json")
    return report.finish("RENDER")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    meta = sub.add_parser("meta")
    meta.add_argument("images", nargs="+")
    meta.add_argument("--expect", choices=sorted(DELEGATES))
    meta.set_defaults(run=cmd_meta)
    scan = sub.add_parser("scan")
    scan.add_argument("logs", nargs="+")
    scan.set_defaults(run=cmd_scan)
    estimate = sub.add_parser("estimate")
    estimate.add_argument("report_a")
    estimate.add_argument("report_b")
    estimate.add_argument("--images", type=int, required=True)
    estimate.set_defaults(run=cmd_estimate)
    audit = sub.add_parser("audit")
    audit.add_argument("hip", nargs="?")
    audit.add_argument("--expect", choices=sorted(DELEGATES), default="xpu")
    audit.add_argument("--fix", action="store_true", help="set the delegate in memory; nothing is saved")
    audit.set_defaults(run=cmd_audit)
    render = sub.add_parser("render")
    render.add_argument("hip")
    render.add_argument("--rop", required=True)
    render.add_argument("--frames", nargs=2, type=float, required=True, metavar=("FIRST", "LAST"))
    render.add_argument("--step", type=float, default=1.0)
    render.add_argument("--output", required=True, help="image path, with $F4 for whole frames")
    render.add_argument("--expect", choices=sorted(DELEGATES), default="xpu")
    render.add_argument("--all-at-once", action="store_true", help="one husk process for the whole range")
    render.add_argument("--log-dir", help="default: beside the output")
    render.add_argument("--min-gpu-free-mib", type=int, default=4000, help="0 skips the check")
    render.set_defaults(run=cmd_render)
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
