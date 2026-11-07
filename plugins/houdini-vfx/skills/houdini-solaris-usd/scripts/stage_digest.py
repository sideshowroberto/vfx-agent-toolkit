#!/usr/bin/env python
"""Prove two composed USD stages match, and name the prims that differ.

hython:
    stage_digest.py digest SCENE.hip /stage/OUT --frame 1006 --canary-frame 1050 --out before.json
Any python:
    stage_digest.py compare before.json after.json

A live session can import this file and call digest_stage(node.stage(), frame); digest never saves the hip.

An md5 of stage.ExportToString() is not an equality instrument: on a production stage the string stopped at exactly
2^31-1 characters, took 87 to 101 s, and four stages that matched gave four md5s. This hashes per prim instead: path,
type, every authored attribute at the frame, relationship targets, prototype subtrees included. It took 4 to 5 s on
9,591 prims.

USD numbers /__Prototype_N afresh per load, so the same hip digested twice differed on thousands of prims until
prototypes were keyed by content. A changed prototype therefore lists as its whole subtree under ONLY BEFORE and
ONLY AFTER, not as the one mesh that moved.

An "identical" verdict needs proof the instrument can fail. A small in-memory stage is edited on every run, one kind of
value at a time, and each edit must show. Digesting the same hip twice is the opposite check, and it should be run
once on any new kind of stage. The canary then digests the real stage at another frame and must see prims change; a
stage with nothing animated cannot pass that, so say --no-canary and report that it was skipped.

Metadata, variant selections and layer structure are not hashed: only the composed values they produce.
Exit 0 = identical or digest done, 1 = different or failed, 2 = bad usage.
"""
import argparse
import hashlib
import json
import re
import sys
import time

VOLATILE = re.compile(rb"anon:[0-9a-fA-Fx]+(:[^\s'\"\]]*)?|/__Prototype_\d+")
LISTED = 20


def value_bytes(value, np, Sdf):
    if value is None:
        return b"None"
    if isinstance(value, Sdf.AssetPath):
        return ("asset:" + value.path).encode("utf-8", "replace")
    if hasattr(value, "__len__") and not isinstance(value, (str, bytes)):
        try:
            array = np.asarray(value)
        except (TypeError, ValueError):
            return repr(value).encode("utf-8", "replace")
        if array.dtype.kind not in "OUS":  # an object array would hash pointers
            return array.tobytes() + repr(array.shape).encode()
        return repr(list(value)).encode("utf-8", "replace")
    return repr(value).encode("utf-8", "replace")


def digest_stage(stage, frame):
    """prim path -> md5. Anything that changes between loads with no content change is left out of the hash:
    anonymous layer ids, and prototype numbers, which USD deals out afresh per load. A prototype is keyed by its
    content, and an instance hashes the key of the prototype it points at."""
    import numpy as np
    from pxr import Sdf, Usd
    time_code, digests, keys, members = Usd.TimeCode(frame), {}, {}, {}

    def prototype_key(prototype):
        root = str(prototype.GetPath())
        if root not in keys:
            subtree = {}
            for prim in Usd.PrimRange(prototype):
                subtree[str(prim.GetPath())[len(root):] or "/"] = prim_digest(prim, str(prim.GetPath())[len(root):])
            keys[root] = hashlib.md5(repr(sorted(subtree.items())).encode()).hexdigest()
            members[root] = subtree
        return keys[root]

    def prim_digest(prim, name):
        md5 = hashlib.md5()
        md5.update(name.encode() + b"|" + str(prim.GetTypeName()).encode())
        if prim.IsInstance():
            md5.update(b"|instance of " + prototype_key(prim.GetPrototype()).encode())
        for attribute in sorted(prim.GetAuthoredAttributes(), key=lambda item: item.GetName()):
            md5.update(b"\0" + attribute.GetName().encode() + b"\0")
            md5.update(VOLATILE.sub(b"", value_bytes(attribute.Get(time_code), np, Sdf)))
        for relationship in sorted(prim.GetAuthoredRelationships(), key=lambda item: item.GetName()):
            md5.update(b"\0" + relationship.GetName().encode() + b"\0")
            targets = "|".join(str(target) for target in relationship.GetTargets()).encode()
            md5.update(VOLATILE.sub(b"", targets))
        return md5.hexdigest()

    for prim in stage.Traverse():
        digests[str(prim.GetPath())] = prim_digest(prim, str(prim.GetPath()))
    seen = {}
    for prototype in stage.GetPrototypes():
        key = prototype_key(prototype)
        seen[key] = seen.get(key, 0) + 1  # two prototypes can hold the same content
        for name, value in members[str(prototype.GetPath())].items():
            digests["/<prototype %s.%d>%s" % (key[:12], seen[key], name)] = value
    return digests


def self_test():
    """Names of the edits the digest failed to see; empty means it can see all of them."""
    from pxr import Gf, Sdf, Usd, UsdGeom, Vt

    def build():
        stage = Usd.Stage.CreateInMemory()
        mesh = UsdGeom.Mesh.Define(stage, "/world/mesh")
        mesh.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(float(index), 0, 0) for index in range(20)]))
        prim = mesh.GetPrim()
        prim.CreateAttribute("note", Sdf.ValueTypeNames.String).Set("a")
        prim.CreateAttribute("tags", Sdf.ValueTypeNames.TokenArray).Set(Vt.TokenArray(["t%d" % i for i in range(20)]))
        prim.CreateAttribute("names", Sdf.ValueTypeNames.StringArray).Set(Vt.StringArray(["n%d" % i for i in range(20)]))
        prim.CreateAttribute("map", Sdf.ValueTypeNames.Asset).Set(Sdf.AssetPath("a.png"))
        prim.CreateRelationship("link").SetTargets([Sdf.Path("/world")])
        UsdGeom.Xform.Define(stage, "/world/spare")
        return stage, prim

    edits = {
        "float array": lambda prim, stage: prim.GetAttribute("points").Set(
            Vt.Vec3fArray([Gf.Vec3f(float(index) + (index == 19), 0, 0) for index in range(20)])),
        "string": lambda prim, stage: prim.GetAttribute("note").Set("b"),
        "token array": lambda prim, stage: prim.GetAttribute("tags").Set(
            Vt.TokenArray(["t%d" % i for i in range(19)] + ["changed"])),
        "string array": lambda prim, stage: prim.GetAttribute("names").Set(
            Vt.StringArray(["n%d" % i for i in range(19)] + ["changed"])),
        "asset": lambda prim, stage: prim.GetAttribute("map").Set(Sdf.AssetPath("b.png")),
        "relationship": lambda prim, stage: prim.GetRelationship("link").SetTargets([Sdf.Path("/world/spare")]),
        "new prim": lambda prim, stage: UsdGeom.Xform.Define(stage, "/world/extra"),
    }
    base = digest_stage(build()[0], 1)
    missed = [] if digest_stage(build()[0], 1) == base else ["same content read as different"]
    for name, edit in edits.items():
        stage, prim = build()
        edit(prim, stage)
        if digest_stage(stage, 1) == base:
            missed.append(name)

    def instanced(order, swap=False, size=2.0):
        """Two instances of two class prims, so their content is reachable only through the prototypes."""
        stage = Usd.Stage.CreateInMemory()
        for name in order:
            stage.CreateClassPrim("/_src/" + name)
            cube = UsdGeom.Cube.Define(stage, "/_src/%s/shape" % name)
            cube.CreateSizeAttr(size if name == "b" else 1.0)
        for name in order:
            other = {"a": "b", "b": "a"}[name] if swap else name
            prim = UsdGeom.Xform.Define(stage, "/world/" + name).GetPrim()
            prim.GetReferences().AddInternalReference("/_src/" + other)
            prim.SetInstanceable(True)
        return digest_stage(stage, 1)

    reference = instanced("ab")
    if not any("<prototype" in path for path in reference):
        missed.append("no prototypes in the instancing test")
    if instanced("ba") != reference:
        missed.append("prototype order read as different")
    if instanced("ab", swap=True) == reference:
        missed.append("instances swapped between prototypes")
    if instanced("ab", size=3.0) == reference:
        missed.append("prototype content")
    return missed


def compare(before, after):
    only_before = sorted(set(before) - set(after))
    only_after = sorted(set(after) - set(before))
    changed = sorted(path for path in set(before) & set(after) if before[path] != after[path])
    return changed, only_before, only_after


def cmd_digest(args):
    import hou
    if args.canary_frame is None and not args.no_canary:
        raise ValueError("--canary-frame is required: an identical verdict needs a change it has seen, or say --no-canary")
    missed = self_test()
    print("SELFTEST %s" % ("FAIL, did not see: %s" % missed if missed else "PASS"))
    hou.hipFile.load(args.hip, suppress_save_prompt=True, ignore_load_warnings=True)
    node = hou.node(args.node)
    if node is None or not hasattr(node, "stage"):
        raise ValueError("%s is not a LOP node in %s" % (args.node, args.hip))
    hou.setFrame(args.frame)
    started = time.time()
    stage = node.stage()
    if stage is None:
        raise ValueError("%s has no stage: %s" % (args.node, node.errors()))
    cooked = time.time()
    digests = digest_stage(stage, args.frame)
    print("DIGEST %d prims, cook %.1f s, digest %.1f s" % (len(digests), cooked - started, time.time() - cooked))
    failed = len(missed) + (0 if digests else 1)
    canary_changed = None
    if args.canary_frame is not None:
        hou.setFrame(args.canary_frame)
        changed, gone, new = compare(digests, digest_stage(node.stage(), args.canary_frame))
        canary_changed = len(changed) + len(gone) + len(new)
        print("CANARY frame %s changed %d prims, first %s" % (args.canary_frame, canary_changed, changed[:3]))
        if not canary_changed:
            print("FAIL the canary saw nothing: animate something or pick another frame, then trust the verdict")
            failed += 1
    else:
        print("NOTE canary skipped: report that this digest has not been shown to fail on this stage")
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"hip": args.hip, "node": args.node, "frame": args.frame, "canary_changed": canary_changed,
                   "prims": digests}, fh, indent=0, sort_keys=True)
    print("DIGEST %s" % ("FAIL %d" % failed if failed else "PASS"))
    return 1 if failed else 0


def cmd_compare(args):
    with open(args.before, encoding="utf-8") as fh:
        before = json.load(fh)
    with open(args.after, encoding="utf-8") as fh:
        after = json.load(fh)
    if before.get("frame") != after.get("frame"):
        print("NOTE the digests are from frames %s and %s" % (before.get("frame"), after.get("frame")))
    if not before["prims"] or not after["prims"]:
        print("FAIL a digest holds no prims: nothing was compared")
        return 1
    if not before.get("canary_changed") or not after.get("canary_changed"):
        print("NOTE a side has no canary that saw a change, so IDENTICAL here is weaker evidence")
    changed, only_before, only_after = compare(before["prims"], after["prims"])
    for label, paths in (("CHANGED", changed), ("ONLY BEFORE", only_before), ("ONLY AFTER", only_after)):
        for path in paths[:LISTED]:
            print("%s %s" % (label, path))
        if len(paths) > LISTED:
            print("%s ... and %d more" % (label, len(paths) - LISTED))
    total = len(changed) + len(only_before) + len(only_after)
    print("COMPARE %s (%d and %d prims; %d changed, %d only before, %d only after)" % (
        "DIFFERENT" if total else "IDENTICAL", len(before["prims"]), len(after["prims"]),
        len(changed), len(only_before), len(only_after)))
    return 1 if total else 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    digest = sub.add_parser("digest")
    digest.add_argument("hip")
    digest.add_argument("node")
    digest.add_argument("--frame", type=float, default=1.0)
    digest.add_argument("--canary-frame", type=float)
    digest.add_argument("--no-canary", action="store_true")
    digest.add_argument("--out", required=True)
    digest.set_defaults(run=cmd_digest)
    comparison = sub.add_parser("compare")
    comparison.add_argument("before")
    comparison.add_argument("after")
    comparison.set_defaults(run=cmd_compare)
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
