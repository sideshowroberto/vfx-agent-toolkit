#!/usr/bin/env python
"""Prove two SOP outputs hold the same geometry, and name the component that differs.

hython:
    geo_digest.py digest SCENE.hip /obj/a/OUT [/obj/b/OUT ...] --frame 1001 --out before.json
Any python:
    geo_digest.py compare before.json after.json

A live session can import this file and call digest_node(hou.node("/obj/a/OUT")); digest never saves the hip.

An identity check has to ignore everything that is not content. Hashing attributes in creation order made an
unchanged Material SOP read DIFFERENT, because it created shop_materialpath before name on a later cook. So each
component hashes separately, attributes by name: positions, topology, packed transforms, each attribute, each group.
Point, vertex, primitive and detail classes are all read, because a change on any of them is a change.

When an identity proof suddenly fails with nothing changed, digest the saved hip headless before blaming the change.
Every digest also moves a point on a private copy and fails unless the positions digest notices.

Volumes and VDB voxels are not read, so a voxel-only change is invisible: only their primitive count and attributes.
Exit 0 = identical or digest done, 1 = different or failed, 2 = bad usage.
"""
import argparse
import hashlib
import json
import sys

PRECISION = 6
CANARY_SHIFT = 1.0


def md5_bytes(data):
    return hashlib.md5(data).hexdigest()


def rounded(raw):
    """Fixed-precision bytes, so noise below the precision and -0.0 cannot read as a change."""
    import numpy as np
    values = np.frombuffer(raw, dtype=np.float32)
    return (np.round(values.astype(np.float64), PRECISION) + 0.0).tobytes()


def text_digest(values):
    return md5_bytes("\0".join(str(value) for value in values).encode("utf-8", "replace"))


def element_values(geo, attribute, element_class):
    """Slow path for array and dictionary attributes, which have no bulk read."""
    if element_class == "point":
        return [item.attribValue(attribute) for item in geo.points()]
    if element_class == "prim":
        return [item.attribValue(attribute) for item in geo.prims()]
    return [vertex.attribValue(attribute) for prim in geo.prims() for vertex in prim.vertices()]


def attribute_digest(hou, geo, attribute, element_class):
    kind = attribute.dataType()
    if element_class == "detail":
        return text_digest([repr(geo.attribValue(attribute))])
    if attribute.isArrayType() or kind == hou.attribData.Dict:
        return text_digest(repr(value) for value in element_values(geo, attribute, element_class))
    name = attribute.name()
    if kind == hou.attribData.Float:
        return md5_bytes(rounded(getattr(geo, element_class + "FloatAttribValuesAsString")(name)))
    if kind == hou.attribData.Int:
        return md5_bytes(getattr(geo, element_class + "IntAttribValuesAsString")(name))
    return text_digest(getattr(geo, element_class + "StringAttribValues")(name))


def digest_geometry(hou, geo):
    """component name -> digest. Comparing two of these names what changed."""
    prims = geo.prims()
    result = {"count:points": len(geo.points()), "count:prims": len(prims),
              "positions": md5_bytes(rounded(geo.pointFloatAttribValuesAsString("P"))),
              "topology": text_digest("%s:%s" % (prim.type().name(), ",".join(
                  str(vertex.point().number()) for vertex in prim.vertices())) for prim in prims)}
    packed = [prim for prim in prims if isinstance(prim, hou.PackedPrim)]
    if packed:
        result["packed_transforms"] = text_digest(
            ",".join("%.6f" % value for value in prim.fullTransform().asTuple()) for prim in packed)
    for element_class, attributes in (("point", geo.pointAttribs()), ("prim", geo.primAttribs()),
                                      ("vertex", geo.vertexAttribs()), ("detail", geo.globalAttribs())):
        for attribute in sorted(attributes, key=lambda item: item.name()):
            if element_class == "point" and attribute.name() == "P":
                continue
            result["attr:%s:%s" % (element_class, attribute.name())] = attribute_digest(
                hou, geo, attribute, element_class)
    for element_class, groups, members in (("point", geo.pointGroups(), lambda group: group.points()),
                                           ("prim", geo.primGroups(), lambda group: group.prims())):
        for group in sorted(groups, key=lambda item: item.name()):
            result["group:%s:%s" % (element_class, group.name())] = text_digest(
                item.number() for item in members(group))
    for group in sorted(geo.edgeGroups(), key=lambda item: item.name()):
        result["group:edge:" + group.name()] = text_digest(
            sorted(tuple(sorted(point.number() for point in edge.points())) for edge in group.edges()))
    return result


def canary(hou, geo):
    """Move one point on a private copy: an identity check nobody has seen fail proves nothing."""
    if not geo.points():
        return False
    copy = hou.Geometry()
    copy.merge(geo)
    before = md5_bytes(rounded(copy.pointFloatAttribValuesAsString("P")))
    point = copy.points()[0]
    position = point.position()
    point.setPosition(hou.Vector3(position[0] + CANARY_SHIFT, position[1], position[2]))
    return md5_bytes(rounded(copy.pointFloatAttribValuesAsString("P"))) != before


def digest_node(node):
    import hou
    geo = node.geometry()
    if geo is None:
        raise ValueError("%s has no geometry" % node.path())
    return digest_geometry(hou, geo)


def compare(before, after):
    """Lists of (node, component) that differ, or that one side lacks."""
    different, only_before, only_after = [], [], []
    for node in sorted(set(before) | set(after)):
        if node not in after:
            only_before.append((node, "(whole node)"))
            continue
        if node not in before:
            only_after.append((node, "(whole node)"))
            continue
        left, right = before[node], after[node]
        only_before += [(node, name) for name in sorted(set(left) - set(right))]
        only_after += [(node, name) for name in sorted(set(right) - set(left))]
        different += [(node, name) for name in sorted(set(left) & set(right)) if left[name] != right[name]]
    return different, only_before, only_after


def cmd_digest(args):
    import hou
    hou.hipFile.load(args.hip, suppress_save_prompt=True, ignore_load_warnings=True)
    hou.setFrame(args.frame)
    digests, failed = {}, 0
    for path in args.nodes:
        node = hou.node(path)
        if node is None:
            print("FAIL no node %s in %s" % (path, args.hip))
            failed += 1
            continue
        digests[path] = digest_node(node)
        print("DIGEST %s: %d components, %d points, %d prims" % (
            path, len(digests[path]), digests[path]["count:points"], digests[path]["count:prims"]))
        if not canary(hou, node.geometry()):
            print("FAIL canary: moving a point did not change the digest of %s" % path)
            failed += 1
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"hip": args.hip, "frame": args.frame, "nodes": digests}, fh, indent=1, sort_keys=True)
    print("DIGEST %s" % ("FAIL %d" % failed if failed else "PASS"))
    return 1 if failed else 0


def cmd_compare(args):
    with open(args.before, encoding="utf-8") as fh:
        before = json.load(fh)
    with open(args.after, encoding="utf-8") as fh:
        after = json.load(fh)
    if before.get("frame") != after.get("frame"):
        print("NOTE the digests are from frames %s and %s" % (before.get("frame"), after.get("frame")))
    if not before["nodes"] or not after["nodes"]:
        print("FAIL a digest holds no nodes: nothing was compared")
        return 1
    different, only_before, only_after = compare(before["nodes"], after["nodes"])
    for node, name in different:
        print("DIFFERENT %s %s" % (node, name))
    for node, name in only_before:
        print("ONLY BEFORE %s %s" % (node, name))
    for node, name in only_after:
        print("ONLY AFTER %s %s" % (node, name))
    total = len(different) + len(only_before) + len(only_after)
    components = sum(len(value) for value in before["nodes"].values())
    print("COMPARE %s (%d nodes, %d components)" % (
        "DIFFERENT %d" % total if total else "IDENTICAL", len(before["nodes"]), components))
    return 1 if total else 0


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command")
    sub.required = True
    digest = sub.add_parser("digest")
    digest.add_argument("hip")
    digest.add_argument("nodes", nargs="+")
    digest.add_argument("--frame", type=float, default=1.0)
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
