"""Known-good and known-bad cases for geo_digest.py and hip_provenance.py.

    python test_digest_tools.py
Set HYTHON to a hython.exe to add real Houdini cases: attribute creation order, one change per component, a real
camera move. They use a Houdini licence and are skipped without HYTHON.
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geo_digest  # noqa: E402
import hip_provenance  # noqa: E402

CAMERA = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
SCENE = r'''
import json
import sys
import hou
sys.path.insert(0, sys.argv[1])
import geo_digest


def wrangle(parent, name, upstream, code, klass=1):
    node = parent.createNode("attribwrangle", name)
    node.setInput(0, upstream)
    node.parm("class").set(klass)
    node.parm("snippet").set(code)
    return node


def digest(node):
    return geo_digest.digest_node(node)


root = hou.node("/obj").createNode("geo", "g")
box = root.createNode("box", "box")
# the same two attributes, created in opposite orders
order_a = wrangle(root, "order_a", box, 's@name = "x"; s@shop_materialpath = "m";')
order_b = wrangle(root, "order_b", box, 's@shop_materialpath = "m"; s@name = "x";')
base = order_a
packed = root.createNode("pack", "packed")
packed.setInput(0, base)
xform = root.createNode("xform", "moved_pack")
xform.setInput(0, packed)
xform.parm("tx").set(2)
edits = {
    "positions": wrangle(root, "e_p", base, "@P.x += 0.5;", 2),
    "attr:point:Cd": wrangle(root, "e_pt", base, "v@Cd = {1, 0, 0};", 2),
    "attr:prim:name": wrangle(root, "e_pr", base, 'if (@primnum == 0) s@name = "y";'),
    "attr:vertex:uvw": wrangle(root, "e_v", base, "v@uvw = {0, 0, 1};", 3),
    "attr:detail:version": wrangle(root, "e_d", base, "i@version = 2;", 0),
    "group:prim:top": wrangle(root, "e_g", base, 'if (@primnum == 0) setprimgroup(0, "top", 0, 1);'),
    "group:point:corner": wrangle(root, "e_gp", base, 'if (@ptnum == 0) setpointgroup(0, "corner", 0, 1);', 2),
    "attr:vertex:label": wrangle(root, "e_vs", base, 's@label = "a";', 3),
    "attr:prim:ids": wrangle(root, "e_arr", base, "i[]@ids = array(1, 2);"),
    "attr:point:meta": wrangle(root, "e_dict", base, 'd@meta = set("a", 1);', 2),
}
tiny = root.createNode("attribwrangle", "tiny")
tiny.setInput(0, base)
tiny.parm("class").set(2)
tiny.parm("snippet").set("@P.x += 1e-9;")
out = {"order": geo_digest.compare({"n": digest(order_a)}, {"n": digest(order_b)}),
       "tiny": geo_digest.compare({"n": digest(base)}, {"n": digest(tiny)}),
       "repeat": geo_digest.compare({"n": digest(base)}, {"n": digest(base)}),
       "packed": geo_digest.compare({"n": digest(packed)}, {"n": digest(xform)}),
       "canary": geo_digest.canary(hou, base.geometry()), "edits": {}}
reference = {"n": digest(base)}
for name, node in edits.items():
    out["edits"][name] = geo_digest.compare(reference, {"n": digest(node)})
print("RESULT " + json.dumps(out))
camera = hou.node("/obj").createNode("cam", "shot")
camera.parm("tx").set(1)
hou.hipFile.save(sys.argv[2])
camera.parm("tx").set(1.25)
hou.hipFile.save(sys.argv[3])
'''


def call(module, *argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = module.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="digest_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def write(self, name, body):
        with open(self.path(name), "w", encoding="utf-8") as fh:
            fh.write(body if isinstance(body, str) else json.dumps(body))
        return self.path(name)


class Compare(Base):
    def digests(self, name, frame, nodes):
        return self.write(name, {"frame": frame, "nodes": nodes})

    def test_good_identical(self):
        one = self.digests("a.json", 1, {"/n": {"positions": "x", "attr:prim:name": "y"}})
        two = self.digests("b.json", 1, {"/n": {"attr:prim:name": "y", "positions": "x"}})
        code, text = call(geo_digest, "compare", one, two)
        self.assertEqual(code, 0, text)
        self.assertIn("IDENTICAL", text)

    def test_bad_names_the_component(self):
        one = self.digests("a.json", 1, {"/n": {"positions": "x", "attr:prim:name": "y"}})
        two = self.digests("b.json", 1, {"/n": {"positions": "x", "attr:prim:name": "z"}})
        code, text = call(geo_digest, "compare", one, two)
        self.assertEqual(code, 1, text)
        self.assertIn("DIFFERENT /n attr:prim:name", text)
        self.assertNotIn("DIFFERENT /n positions", text)

    def test_bad_attribute_gone(self):
        code, text = call(geo_digest, "compare", self.digests("a.json", 1, {"/n": {"a": "1", "b": "2"}}),
                          self.digests("b.json", 1, {"/n": {"a": "1"}}))
        self.assertEqual(code, 1, text)
        self.assertIn("ONLY BEFORE /n b", text)

    def test_bad_node_missing(self):
        code, text = call(geo_digest, "compare", self.digests("a.json", 1, {"/n": {"a": "1"}, "/m": {"a": "1"}}),
                          self.digests("b.json", 1, {"/n": {"a": "1"}}))
        self.assertEqual(code, 1, text)
        self.assertIn("(whole node)", text)

    def test_bad_empty_digests_are_not_identical(self):
        code, text = call(geo_digest, "compare", self.digests("a.json", 1, {}), self.digests("b.json", 1, {}))
        self.assertEqual(code, 1, text)
        self.assertIn("nothing was compared", text)

    def test_note_on_another_frame(self):
        same = {"/n": {"a": "1"}}
        code, text = call(geo_digest, "compare", self.digests("a.json", 1, same), self.digests("b.json", 2, same))
        self.assertEqual(code, 0, text)
        self.assertIn("NOTE", text)

    def test_usage_missing_file(self):
        self.assertEqual(call(geo_digest, "compare", self.path("a"), self.path("b"))[0], 2)


class Provenance(Base):
    def test_good_unchanged(self):
        hip = self.write("a.hip", "one")
        record = self.path("r.json")
        self.assertEqual(call(hip_provenance, "stamp", hip, "--out", record)[0], 0)
        code, text = call(hip_provenance, "check", record)
        self.assertEqual(code, 0, text)
        self.assertIn("SAME a.hip", text)

    def test_bad_saved_over_with_the_same_name(self):
        hip = self.write("a.hip", "one")
        record = self.path("r.json")
        call(hip_provenance, "stamp", hip, "--out", record)
        self.write("a.hip", "two")
        code, text = call(hip_provenance, "check", record)
        self.assertEqual(code, 1, text)
        self.assertIn("was saved over", text)

    def test_bad_same_size_other_content(self):
        hip = self.write("a.hip", "abc")
        record = self.path("r.json")
        call(hip_provenance, "stamp", hip, "--out", record)
        stat = os.stat(hip)
        self.write("a.hip", "abd")
        os.utime(hip, (stat.st_atime, stat.st_mtime))
        self.assertEqual(call(hip_provenance, "check", record)[0], 1)

    def test_bad_file_gone(self):
        hip = self.write("a.hip", "one")
        record = self.path("r.json")
        call(hip_provenance, "stamp", hip, "--out", record)
        os.remove(hip)
        code, text = call(hip_provenance, "check", record)
        self.assertEqual(code, 1, text)
        self.assertIn("is gone", text)

    def test_note_when_two_versions_match(self):
        one, two = self.write("v107.hip", "same"), self.write("v108.hip", "same")
        code, text = call(hip_provenance, "stamp", one, two, "--out", self.path("r.json"))
        self.assertEqual(code, 0, text)
        self.assertIn("are the same file", text)

    def test_note_when_two_versions_are_the_same_size(self):
        one, two = self.write("v107.hip", "abc"), self.write("v108.hip", "abd")
        code, text = call(hip_provenance, "stamp", one, two, "--out", self.path("r.json"))
        self.assertEqual(code, 0, text)
        self.assertIn("are the same size", text)

    def test_no_note_when_sizes_differ(self):
        one, two = self.write("v106.hip", "ab"), self.write("v107.hip", "abc")
        code, text = call(hip_provenance, "stamp", one, two, "--out", self.path("r.json"))
        self.assertEqual(code, 0, text)
        self.assertNotIn("NOTE", text)

    def record(self, name, x, focal=50.0, frame=1.0):
        world = list(CAMERA)
        world[12] = x
        return self.write(name, {"cameras": {"/obj/cam": [{"frame": frame, "world": world, "focal": focal}]}})

    def test_good_camera_same(self):
        code, text = call(hip_provenance, "camdiff", self.record("a.json", 1.0), self.record("b.json", 1.0))
        self.assertEqual(code, 0, text)

    def test_bad_camera_moved(self):
        code, text = call(hip_provenance, "camdiff", self.record("a.json", 1.0), self.record("b.json", 1.053))
        self.assertEqual(code, 1, text)
        self.assertIn("moved 0.0530", text)

    def test_bad_focal_changed(self):
        code, text = call(hip_provenance, "camdiff", self.record("a.json", 1.0), self.record("b.json", 1.0, 55.0))
        self.assertEqual(code, 1, text)

    def test_bad_frames_do_not_overlap_is_not_same(self):
        code, text = call(hip_provenance, "camdiff", self.record("a.json", 1.0), self.record("b.json", 1.0, frame=2.0))
        self.assertEqual(code, 1, text)
        self.assertIn("no frame", text)

    def test_bad_record_without_cameras_is_not_same(self):
        code, text = call(hip_provenance, "camdiff", self.write("a.json", {"files": []}), self.record("b.json", 1.0))
        self.assertEqual(code, 1, text)
        self.assertIn("nothing was compared", text)


@unittest.skipUnless(os.environ.get("HYTHON"), "HYTHON not set")
class RealHoudini(Base):
    def hython(self, *argv):
        env = dict(os.environ)
        env.pop("HFS", None)
        result = subprocess.run([os.environ["HYTHON"]] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, errors="replace", env=env)
        return result.returncode, result.stdout

    def test_real_digest_and_cameras(self):
        one, two = self.path("one.hip").replace("\\", "/"), self.path("two.hip").replace("\\", "/")
        code, text = self.hython(self.write("scene.py", SCENE), HERE, one, two)
        self.assertEqual(code, 0, text)
        lines = [line for line in text.splitlines() if line.startswith("RESULT ")]
        self.assertEqual(len(lines), 1, text)
        result = json.loads(lines[0][7:])
        self.assertEqual(result["order"], [[], [], []], "creation order faked a change")
        self.assertEqual(result["tiny"], [[], [], []], "noise below the precision read as a change")
        self.assertEqual(result["repeat"], [[], [], []])
        self.assertTrue(result["canary"])
        self.assertIn(["n", "packed_transforms"], result["packed"][0], text)
        for name, (different, _before, after) in result["edits"].items():
            self.assertIn(["n", name], different + after, name)
        for name in ("one", "two"):
            code, text = self.hython(os.path.join(HERE, "hip_provenance.py"), "stamp", self.path(name + ".hip"),
                                     "--cameras", "/obj/shot", "--frames", "1", "--out", self.path(name + ".json"))
            self.assertEqual(code, 0, text)
        code, text = call(hip_provenance, "camdiff", self.path("one.json"), self.path("two.json"))
        self.assertEqual(code, 1, text)
        self.assertIn("moved 0.2500", text)
        code, text = self.hython(os.path.join(HERE, "geo_digest.py"), "digest", one, "/obj/g/box", "--out",
                                 self.path("saved.json"))
        self.assertEqual(code, 0, text)
        code, text = self.hython(os.path.join(HERE, "geo_digest.py"), "digest", one, "/obj/g/nope", "--out",
                                 self.path("missing.json"))
        self.assertEqual(code, 1, text)
        self.assertIn("no node /obj/g/nope", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
