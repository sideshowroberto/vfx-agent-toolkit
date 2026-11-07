#!/usr/bin/env python
"""Zero-cost gate around a paid ComfyUI run: the checks `comfy validate` cannot make.

  comfy_gate.py pre  WORKFLOW_API.json      before submitting; posts nothing, bills nothing
  comfy_gate.py post RUN.jsonl              after `comfy run --wait --json > RUN.jsonl`

pre fails on: an invalid graph or an unexplained validate warning; a print-prompt
that is not the file; unknown node classes; required inputs missing from the
running ComfyUI's object_info (templates older than the server); more than one
paid node in a prompt; sizes and reference aspects over a partner node's runtime
limit; LoadImage files outside the top of the input folder.

post fails on: an envelope with ok false or none at all; an execution_error;
unexplained validation_warnings; an expected output node that did not run; a
missing, empty or single-colour output file; more credits spent than expected.

`comfy run` can exit 0 on a failed run and `completed` can mean "something ran",
so neither is read here. Exit 0 = gate passed, 1 = gate failed, 2 = bad usage.
"""
import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_SERVER = "http://127.0.0.1:8188"
INPUT_LOADERS = ("LoadImage", "LoadVideo")
HTTP_TIMEOUT = 30

# Partner limits live in each node's execute code, where object_info cannot see them.
# They MOVE between ComfyUI versions (Seedream 5.0 Pro was 4.19 MP on 0.37 and is
# 4.62 MP on 0.43), so a version mismatch prints a NOTE. To refresh, read
# ComfyUI/comfy_api_nodes/nodes_*.py and update CAPS_VERSION with the table.
CAPS_VERSION = "0.43.0"
CAPS = [
    {"class": "ByteDanceSeedreamNodeV[23]", "model": "seedream 5.0 (pro|flash)", "preset": "model.size_preset",
     "width": "model.width", "height": "model.height",
     "min_pixels": 921600, "max_pixels": 4624220, "ref_aspect": [1.0 / 16, 16.0]},
    {"class": "ByteDanceSeedreamNodeV[23]", "model": "seedream 5.0 lite|seedream-4-5", "preset": "model.size_preset",
     "width": "model.width", "height": "model.height",
     "min_pixels": 3686400, "max_pixels": 16777216, "ref_aspect": [1.0 / 16, 16.0]},
    {"class": "ByteDanceSeedreamNode", "model": "seedream", "preset": "size_preset",
     "width": "width", "height": "height", "max_pixels": 10404496, "ref_aspect": [1.0 / 3, 3.0]},
    {"class": "OpenAIGPTImageNodeV2", "model": "gpt-image", "preset": "model.size",
     "width": "model.custom_width", "height": "model.custom_height",
     "min_pixels": 655360, "max_pixels": 8294400, "max_edge": 3840, "multiple": 16, "max_ratio": 3.0},
]


class Report(object):
    def __init__(self, label):
        self.label, self.failures, self.checks = label, [], 0

    def check(self, passed, message):
        self.checks += 1
        if not passed:
            self.failures.append(message)
            print("FAIL " + message)
        return passed

    def note(self, message):
        print("NOTE " + message)

    def finish(self):
        if self.checks == 0:
            self.check(False, "no check ran")
        verdict = "FAIL %d of %d checks" % (len(self.failures), self.checks) if self.failures \
            else "PASS %d checks" % self.checks
        print("GATE %s %s" % (self.label, verdict))
        return 1 if self.failures else 0


# ---------------------------------------------------------------- shared

def http_get(url):
    with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as response:
        return response.read()


def server_json(server, route):
    return json.loads(http_get(server.rstrip("/") + route).decode("utf-8"))


def load_workflow(path):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if "nodes" in data and "links" in data:
        raise ValueError("%s is UI format; export the API format" % path)
    nodes = dict((key, value) for key, value in data.items()
                 if isinstance(value, dict) and "class_type" in value)
    if not nodes:
        raise ValueError("%s holds no API-format nodes" % path)
    return nodes


def read_events(path):
    """JSON lines of a comfy run log, plus the count of lines that were not JSON."""
    events, junk = [], 0
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except ValueError:
                junk += 1
                continue
            if isinstance(item, dict):
                events.append(item)
    return events, junk


def last_envelope(events):
    found = [event for event in events if event.get("type") == "envelope"]
    return found[-1] if found else None


def comfy_exe():
    return shutil.which("comfy")


def comfy_json(*arguments):
    exe = comfy_exe()
    if not exe:
        raise ValueError("comfy is not on PATH; pass the saved JSON instead")
    result = subprocess.run([exe] + list(arguments), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            stdin=subprocess.DEVNULL, universal_newlines=True, encoding="utf-8", errors="replace")
    events = []
    for line in result.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return events


# ---------------------------------------------------------------- pre

def union_warning_is_false(warning):
    """comfy validate compares a type union as one string; the produced type being a
    member of the expected union is the known false edge_type_mismatch."""
    if warning.get("code") != "edge_type_mismatch":
        return False
    match = re.search(r"expects (\S+) but .* produces (\S+)", warning.get("message", ""))
    return bool(match) and "," in match.group(1) and match.group(2) in match.group(1).split(",")


def check_validate(report, envelope):
    data = envelope.get("data") if envelope else None
    if not report.check(bool(data), "no comfy validate envelope to read"):
        return
    report.check(data.get("valid") is True and data.get("error_count") == 0,
                 "comfy validate: valid=%s, %s errors: %s" % (data.get("valid"), data.get("error_count"),
                                                              json.dumps(data.get("errors", []))[:300]))
    for warning in data.get("warnings", []):
        if union_warning_is_false(warning):
            report.note("known false union warning on node %s" % warning.get("node_id"))
        else:
            report.check(False, "unread validate warning on node %s: %s"
                         % (warning.get("node_id"), warning.get("message")))


def check_preview(report, nodes, events):
    previews = [event.get("prompt") for event in events if event.get("type") == "prompt_preview"]
    if not report.check(bool(previews), "no prompt_preview to compare with the file"):
        return
    report.check(previews[-1] == nodes, "print-prompt differs from the workflow file: the CLI would "
                                        "submit a different graph")


def object_info_for(nodes, server, saved):
    classes = sorted(set(node["class_type"] for node in nodes.values()))
    if saved:
        with open(saved, encoding="utf-8") as fh:
            info = json.load(fh)
        return dict((name, info[name]) for name in classes if name in info)
    info = {}
    for name in classes:
        reply = server_json(server, "/object_info/" + urllib.parse.quote(name))
        info.update(reply)
    return info


def check_inputs(report, nodes, info):
    for node_id, node in sorted(nodes.items()):
        cls = node["class_type"]
        if not report.check(cls in info, "node %s: class %s is not installed" % (node_id, cls)):
            continue
        inputs = node.get("inputs", {})
        for name in info[cls].get("input", {}).get("required", {}):
            # DynamicCombo and autogrow inputs arrive as dotted keys (model.width).
            present = name in inputs or any(key.startswith(name + ".") for key in inputs)
            report.check(present, "node %s %s: required input '%s' is missing (a template older "
                                  "than this ComfyUI?)" % (node_id, cls, name))


def paid_nodes(nodes, info):
    return sorted(key for key, node in nodes.items() if info.get(node["class_type"], {}).get("api_node"))


def cap_for(node, table):
    model = str(node.get("inputs", {}).get("model", ""))
    for entry in table:
        if re.fullmatch(entry["class"], node["class_type"]) and re.search(entry["model"], model):
            return entry
    return None


def check_size(report, node_id, inputs, cap):
    preset = inputs.get(cap["preset"])
    if preset is not None and preset != "Custom":
        return True  # the node's own presets are in range
    width, height = inputs.get(cap["width"]), inputs.get(cap["height"])
    if not isinstance(width, int) or not isinstance(height, int):
        report.note("node %s: %s / %s not readable as sizes, size not checked" % (node_id, cap["width"], cap["height"]))
        return False
    pixels, label = width * height, "node %s %dx%d (%.2f MP)" % (node_id, width, height, width * height / 1e6)
    report.check(pixels <= cap["max_pixels"], "%s is over the %.2f MP limit" % (label, cap["max_pixels"] / 1e6))
    report.check(pixels >= cap.get("min_pixels", 0), "%s is under the %.2f MP minimum"
                 % (label, cap.get("min_pixels", 0) / 1e6))
    if "max_edge" in cap:
        report.check(max(width, height) <= cap["max_edge"], "%s is over the %d px edge" % (label, cap["max_edge"]))
    if "multiple" in cap:
        report.check(width % cap["multiple"] == 0 and height % cap["multiple"] == 0,
                     "%s is not a multiple of %d" % (label, cap["multiple"]))
    if "max_ratio" in cap:
        report.check(max(width, height) / float(min(width, height)) <= cap["max_ratio"],
                     "%s is over the %.0f:1 aspect" % (label, cap["max_ratio"]))
    return True


def image_size(name, input_dir, server):
    """(width, height) of an input image, or None when it cannot be read."""
    try:
        from PIL import Image
    except ImportError:
        return None
    if input_dir:
        with Image.open(os.path.join(input_dir, name)) as image:
            return image.size
    query = urllib.parse.urlencode({"filename": name, "type": "input"})
    data = http_get("%s/view?%s" % (server.rstrip("/"), query))
    with Image.open(io.BytesIO(data)) as image:
        return image.size


def linked_loaders(node, nodes):
    """Loader nodes wired directly into this node's inputs."""
    found = []
    for value in node.get("inputs", {}).values():
        if isinstance(value, list) and len(value) == 2 and str(value[0]) in nodes:
            source = nodes[str(value[0])]
            if source["class_type"] == "LoadImage":
                found.append(source)
    return found


def check_references(report, node_id, node, nodes, cap, input_dir, server):
    low, high = cap["ref_aspect"]
    for loader in linked_loaders(node, nodes):
        name = loader["inputs"].get("image", "")
        try:
            size = image_size(name, input_dir, server)
        except (OSError, urllib.error.URLError) as exc:
            report.check(False, "node %s reference %s cannot be read: %s" % (node_id, name, exc))
            continue
        if size is None:
            report.note("Pillow is missing, reference aspect not checked")
            return
        aspect = size[0] / float(size[1])
        report.check(low <= aspect <= high, "node %s reference %s is %dx%d (aspect %.3f), outside %.3f .. %.3f"
                     % (node_id, name, size[0], size[1], aspect, low, high))


def check_loaders(report, nodes):
    for node_id, node in sorted(nodes.items()):
        if node["class_type"] not in INPUT_LOADERS:
            continue
        for key in ("image", "file"):
            value = node.get("inputs", {}).get(key)
            if isinstance(value, str):
                report.check("/" not in value and "\\" not in value,
                             "node %s: %s is in a subfolder; upload to the top of the input folder"
                             % (node_id, value))


def cmd_pre(args):
    report = Report("pre")
    nodes = load_workflow(args.workflow)
    if args.validate_json:
        validate_events = read_events(args.validate_json)[0]
    else:
        validate_events = comfy_json("--json", "validate", "--workflow", args.workflow, "--where", "local")
    check_validate(report, last_envelope(validate_events))

    if args.print_prompt_json:
        preview_events = read_events(args.print_prompt_json)[0]
    else:
        # --json after the subcommand: it streams the prompt_preview event.
        preview_events = comfy_json("run", "--workflow", args.workflow, "--print-prompt", "--json")
    check_preview(report, nodes, preview_events)

    try:
        info = object_info_for(nodes, args.server, args.object_info)
    except (OSError, urllib.error.URLError, ValueError) as exc:
        report.check(False, "object_info unavailable, nothing below can be judged: %s" % exc)
        return report.finish()
    check_inputs(report, nodes, info)
    check_loaders(report, nodes)

    paid = paid_nodes(nodes, info)
    print("PAID nodes: %s" % (", ".join("%s (%s)" % (key, nodes[key]["class_type"]) for key in paid) or "none"))
    if not args.allow_multi_paid:
        report.check(len(paid) <= 1, "%d paid nodes in one prompt: the first error cancels the rest; "
                                     "split them or pass --allow-multi-paid" % len(paid))
    table = CAPS
    if args.caps:
        with open(args.caps, encoding="utf-8") as fh:
            table = json.load(fh)
    if paid and not args.caps:
        note_caps_version(report, args)
    for key in paid:
        cap = cap_for(nodes[key], table)
        if cap is None:
            report.note("node %s %s has no limits in the table: its runtime limits are unchecked"
                        % (key, nodes[key]["class_type"]))
            continue
        check_size(report, key, nodes[key].get("inputs", {}), cap)
        if "ref_aspect" in cap:
            check_references(report, key, nodes[key], nodes, cap, args.input_dir, args.server)
    return report.finish()


def note_caps_version(report, args):
    try:
        running = server_json(args.server, "/system_stats")["system"]["comfyui_version"]
    except (OSError, urllib.error.URLError, KeyError, ValueError):
        report.note("server version unknown; limits table is from ComfyUI %s" % CAPS_VERSION)
        return
    if running != CAPS_VERSION:
        report.note("limits table is from ComfyUI %s, the server is %s: re-read comfy_api_nodes"
                    % (CAPS_VERSION, running))


# ---------------------------------------------------------------- post

def expected_outputs(args, events):
    if args.expect_node:
        return [str(item) for item in args.expect_node]
    prompt = None
    if args.workflow:
        prompt = load_workflow(args.workflow)
    else:
        previews = [event.get("prompt") for event in events if event.get("type") == "prompt_preview"]
        prompt = previews[-1] if previews else None
    if not prompt:
        return []
    return sorted(key for key, node in prompt.items()
                  if re.search(r"(^|[a-z])Save[A-Z0-9]|^Save", node.get("class_type", "")))


def output_location(url, output_dir):
    """Local path for an output URL, or the URL itself when no folder was given."""
    query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    name = query.get("filename", [""])[0]
    if output_dir and name:
        return os.path.join(output_dir, query.get("subfolder", [""])[0], name)
    return url


def read_output(location):
    if location.startswith("http"):
        return http_get(location)
    with open(location, "rb") as fh:
        return fh.read()


def blank_image(data):
    """True for an image of one colour, None when it cannot be judged."""
    try:
        from PIL import Image
    except ImportError:
        return None
    try:
        with Image.open(io.BytesIO(data)) as image:
            bands = image.convert("RGB").getextrema()
    except OSError:
        return None
    return all(low == high for low, high in bands)


def check_files(report, node_id, urls, args):
    if not report.check(bool(urls), "output node %s listed no files" % node_id):
        return
    for url in urls:
        location = output_location(url, args.output_dir)
        name = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("filename", [url])[0]
        try:
            data = read_output(location)
        except (OSError, urllib.error.URLError) as exc:
            report.check(False, "output %s cannot be read: %s" % (name, exc))
            continue
        if not report.check(len(data) > 0, "output %s is empty" % name):
            continue
        if name.lower().endswith(".glb"):
            report.check(data[:4] == b"glTF", "output %s is not a GLB file" % name)
        elif name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            blank = blank_image(data)
            if blank is None:
                report.note("output %s: pixels not checked" % name)
            else:
                report.check(not blank, "output %s is a single colour" % name)
        print("FILE %s %d bytes" % (name, len(data)))


def check_credits(report, args):
    if args.credits_before is None or args.credits_after is None:
        report.note("no balances given, spend not reconciled")
        return
    spent = args.credits_before - args.credits_after
    print("CREDITS spent %.1f, expected %s" % (spent, args.expected_credits))
    if args.expected_credits is None:
        return
    if spent == 0 and args.expected_credits > 0:
        report.note("balance has not moved: the ledger settles late, re-read in about 30 s")
        return
    limit = args.expected_credits * (1 + args.credit_tolerance)
    report.check(spent <= limit, "spent %.1f credits, expected %.1f: on a shared account read the billing "
                                 "activity feed before concluding anything" % (spent, args.expected_credits))


def cmd_post(args):
    report = Report("post")
    events, junk = read_events(args.run_log)
    if junk:
        report.note("%d lines of the log were not JSON" % junk)
    envelope = last_envelope(events)
    if not report.check(envelope is not None, "no envelope in the log: the run did not finish or the log is cut"):
        return report.finish()

    for event in events:
        if event.get("type") == "execution_error":
            details = event.get("details", {})
            report.check(False, "execution_error at node %s %s: %s" % (
                details.get("node_id"), details.get("node_type"), str(details.get("exception_message"))[:240]))

    queued = [event for event in events if event.get("type") == "queued"]
    report.check(bool(queued), "no queued event: nothing shows the server accepted this")
    for event in queued:
        for warning in event.get("validation_warnings") or []:
            text = json.dumps(warning)
            if not any(item in text for item in args.explain_warning):
                report.check(False, "server dropped something (validation_warnings): %s" % text[:300])

    data = envelope.get("data") or {}
    report.check(envelope.get("ok") is True, "envelope ok=%s: %s" % (
        envelope.get("ok"), str((envelope.get("error") or {}).get("message"))[:240]))
    expected = expected_outputs(args, events)
    report.check(bool(expected), "no expected output node: pass --expect-node or the workflow")
    executed = set(str(item) for item in data.get("executed_node_ids") or [])
    cached = set(str(item) for item in data.get("cached_node_ids") or [])
    by_node = data.get("outputs_by_node") or {}
    for node_id in expected:
        ran = node_id in executed
        if node_id in cached and not ran:
            report.note("output node %s came from the cache: no new work was done" % node_id)
        if report.check(ran or node_id in cached, "output node %s did not run" % node_id):
            check_files(report, node_id, by_node.get(node_id, []), args)
    check_credits(report, args)
    return report.finish()


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    pre = sub.add_parser("pre", help="check a workflow before a paid run")
    pre.add_argument("workflow")
    pre.add_argument("--server", default=DEFAULT_SERVER)
    pre.add_argument("--object-info", help="saved object_info JSON instead of asking the server")
    pre.add_argument("--validate-json", help="saved `comfy --json validate` output instead of running it")
    pre.add_argument("--print-prompt-json", help="saved `comfy run --print-prompt --json` output")
    pre.add_argument("--input-dir", help="ComfyUI input folder (default: fetch through the server)")
    pre.add_argument("--caps", help="limits table JSON replacing the built-in one")
    pre.add_argument("--allow-multi-paid", action="store_true")
    pre.set_defaults(run=cmd_pre)

    post = sub.add_parser("post", help="judge a finished run from its JSON lines")
    post.add_argument("run_log")
    post.add_argument("--workflow", help="API workflow (default: the log's prompt_preview)")
    post.add_argument("--expect-node", action="append", default=[], metavar="ID",
                      help="output node the run exists to produce (default: every Save node)")
    post.add_argument("--output-dir", help="ComfyUI output folder (default: fetch by URL)")
    post.add_argument("--explain-warning", action="append", default=[], metavar="TEXT",
                      help="accept validation_warnings containing this text")
    post.add_argument("--credits-before", type=float)
    post.add_argument("--credits-after", type=float)
    post.add_argument("--expected-credits", type=float)
    post.add_argument("--credit-tolerance", type=float, default=0.05)
    post.set_defaults(run=cmd_post)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except (OSError, ValueError) as exc:
        print("ERROR %s" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
