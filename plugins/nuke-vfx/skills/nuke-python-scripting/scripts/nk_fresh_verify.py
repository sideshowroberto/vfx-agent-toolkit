"""Compare every knob of every node of two Nuke scripts in one fresh process.

Run inside Nuke, normally through `nk_version_up.py verify`:
    nuke -t --safe nk_fresh_verify.py OLD.nk NEW.nk [--ignore=Node.knob] [--allow-swap]

NEW is opened FIRST, before anything has defined its custom layers, so a missing
add_layer shows up here where a builder session would hide it. Each dump is taken
before any frame is moved: nuke.frame() changes the Root frame knob.

Prints one `NK_VERIFY PASS ...` or `NK_VERIFY FAIL ...` line. The caller must look
for that line: the exit code alone does not prove this script ran.
"""
import re
import sys

import nuke

ALWAYS_IGNORED = {"Root.name"}


def dump_script():
    """fullName -> class, input names, knob scripts, error flag."""
    dump = {}
    for node in [nuke.root()] + nuke.allNodes(recurseGroups=True):
        is_root = node.Class() == "Root"
        key = "Root" if is_root else node.fullName()
        knobs = {}
        for name, knob in node.knobs().items():
            try:
                knobs[name] = knob.toScript()
            except Exception:
                knobs[name] = "<unreadable>"
        inputs = []
        for index in range(0 if is_root else node.inputs()):  # inputs() raises on Root
            source = node.input(index)
            inputs.append(source.fullName() if source is not None else None)
        error = False if is_root else bool(node.hasError())
        dump[key] = {"class": node.Class(), "inputs": inputs, "knobs": knobs, "error": error}
    return dump


def open_script(path):
    """Open a script; nodes still load when it reports errors, so return the error."""
    try:
        nuke.scriptOpen(path)
    except RuntimeError as exc:
        return str(exc)
    return ""


def phase(name):
    print("NK_PHASE %s" % name)
    sys.stdout.flush()


def custom_layers(path):
    with open(path, "rb") as handle:
        text = handle.read().decode("latin-1")
    return re.findall(r"^add_layer \{(\S+)", text, re.M)


def compare(old, new, ignored, allow_swap):
    problems, knobs_compared = [], 0
    for key, was in sorted(old.items()):
        now = new.get(key)
        if now is None:
            problems.append("MISSING %s" % key)
            continue
        if was["class"] != now["class"]:
            if not allow_swap:
                problems.append("CLASS %s %s became %s" % (key, was["class"], now["class"]))
            continue
        if was["inputs"] != now["inputs"]:
            problems.append("INPUTS %s %s became %s" % (key, was["inputs"], now["inputs"]))
        if now["error"] and not was["error"]:
            problems.append("ERROR %s has a new error" % key)
        for knob, value in sorted(was["knobs"].items()):
            if "%s.%s" % (key, knob) in ignored:
                continue
            knobs_compared += 1
            if now["knobs"].get(knob, "<absent>") != value:
                problems.append("KNOB %s.%s %.60r became %.60r" % (key, knob, value, now["knobs"].get(knob)))
    return problems, knobs_compared


def main(argv):
    paths = [item for item in argv if not item.startswith("--")]
    ignored = set(ALWAYS_IGNORED)
    ignored.update(item.split("=", 1)[1] for item in argv if item.startswith("--ignore="))
    allow_swap = "--allow-swap" in argv
    if len(paths) != 2:
        print("NK_VERIFY FAIL usage: OLD.nk NEW.nk")
        return 1
    old_path, new_path = paths
    if nuke.allNodes():
        print("NK_VERIFY FAIL the process is not fresh: nodes exist before NEW was opened")
        return 1

    # A knob naming an undefined layer loads as "none" with no error and only a stdout
    # warning. These markers let the caller tell warnings of NEW from warnings of OLD.
    phase("new")
    new_error = open_script(new_path)
    layers_now = set(nuke.layers())
    missing_layers = [name for name in custom_layers(new_path) if name not in layers_now]
    new_dump = dump_script()
    nuke.scriptClear()
    phase("old")
    old_error = open_script(old_path)
    old_dump = dump_script()
    phase("done")

    problems, knobs_compared = compare(old_dump, new_dump, ignored, allow_swap)
    problems.extend("LAYER %s not defined after opening NEW" % name for name in missing_layers)
    if new_error and new_error != old_error:
        problems.append("OPEN NEW reports an error OLD does not: %s" % new_error[:200])
    added = sorted(set(new_dump) - set(old_dump))
    for key in added:
        print("NEW %s %s inputs=%s" % (key, new_dump[key]["class"], new_dump[key]["inputs"]))
    for line in problems:
        print(line[:300])
    if knobs_compared == 0 or len(old_dump) < 2:
        problems.append("nothing compared: OLD loaded %d nodes" % len(old_dump))
    summary = "old_nodes=%d new_nodes=%d added=%d knobs_compared=%d problems=%d" % (
        len(old_dump), len(new_dump), len(added), knobs_compared, len(problems))
    print("NK_VERIFY %s %s" % ("FAIL" if problems else "PASS", summary))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
