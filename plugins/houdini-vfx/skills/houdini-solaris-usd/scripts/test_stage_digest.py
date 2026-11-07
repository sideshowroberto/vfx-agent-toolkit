"""Known-good and known-bad cases for stage_digest.py.

    python test_stage_digest.py
Set HYTHON to a hython.exe to add real USD cases. They use a Houdini licence and are skipped without HYTHON.
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
import stage_digest as tool  # noqa: E402

SCENE = r'''
import sys
import hou
path, moved = sys.argv[1], float(sys.argv[2])
stage = hou.node("/stage")
script = stage.createNode("pythonscript", "scene")
script.parm("python").set("""
from pxr import Gf, UsdGeom
stage = hou.pwd().editableStage()
UsdGeom.Sphere.Define(stage, "/world/ball").AddTranslateOp().Set(Gf.Vec3d(%f, 0, 0))
op = UsdGeom.Xform.Define(stage, "/world/cam").AddTranslateOp()
op.Set(Gf.Vec3d(0, 0, 1), 1)
op.Set(Gf.Vec3d(0, 0, 9), 10)
""" % moved)
still = stage.createNode("pythonscript", "still")
still.parm("python").set("""
from pxr import UsdGeom
UsdGeom.Sphere.Define(hou.pwd().editableStage(), "/world/ball")
""")
hou.hipFile.save(path)
'''


def call(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tool.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="stage_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def write(self, name, body):
        with open(self.path(name), "w", encoding="utf-8") as fh:
            fh.write(body if isinstance(body, str) else json.dumps(body))
        return self.path(name)


class Compare(Base):
    def digest(self, name, prims, canary=3):
        return self.write(name, {"frame": 1, "canary_changed": canary, "prims": prims})

    def test_good_identical(self):
        code, text = call("compare", self.digest("a", {"/a": "1"}), self.digest("b", {"/a": "1"}))
        self.assertEqual(code, 0, text)
        self.assertIn("IDENTICAL", text)
        self.assertNotIn("NOTE", text)

    def test_bad_names_the_prims(self):
        code, text = call("compare", self.digest("a", {"/a": "1", "/b": "2", "/c": "3"}),
                          self.digest("b", {"/a": "9", "/b": "2", "/d": "3"}))
        self.assertEqual(code, 1, text)
        for line in ("CHANGED /a", "ONLY BEFORE /c", "ONLY AFTER /d"):
            self.assertIn(line, text)

    def test_note_identical_without_a_canary(self):
        code, text = call("compare", self.digest("a", {"/a": "1"}, None), self.digest("b", {"/a": "1"}))
        self.assertEqual(code, 0, text)
        self.assertIn("weaker evidence", text)

    def test_bad_empty_digests_are_not_identical(self):
        code, text = call("compare", self.digest("a", {}), self.digest("b", {}))
        self.assertEqual(code, 1, text)
        self.assertIn("nothing was compared", text)

    def test_long_list_is_cut(self):
        before = {"/p%d" % index: "1" for index in range(50)}
        after = {"/p%d" % index: "2" for index in range(50)}
        code, text = call("compare", self.digest("a", before), self.digest("b", after))
        self.assertEqual(code, 1)
        self.assertIn("and 30 more", text)


@unittest.skipUnless(os.environ.get("HYTHON"), "HYTHON not set")
class RealUsd(Base):
    def hython(self, *argv):
        env = dict(os.environ)
        env.pop("HFS", None)
        result = subprocess.run([os.environ["HYTHON"]] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, errors="replace", env=env)
        return result.returncode, result.stdout

    def scene(self, name, moved):
        hip = self.path(name).replace("\\", "/")
        code, text = self.hython(self.write("build.py", SCENE), hip, str(moved))
        self.assertEqual(code, 0, text)
        return hip

    def digest(self, hip, out, *extra):
        return self.hython(os.path.join(HERE, "stage_digest.py"), "digest", hip, *extra, "--out", self.path(out))

    def test_real_stages(self):
        one, two, three = self.scene("a.hip", 1), self.scene("b.hip", 1), self.scene("c.hip", 2)
        for hip, out in ((one, "a.json"), (two, "b.json"), (three, "c.json")):
            code, text = self.digest(hip, out, "/stage/scene", "--frame", "1", "--canary-frame", "10")
            self.assertEqual(code, 0, text)
            self.assertIn("SELFTEST PASS", text)
            self.assertIn("CANARY frame 10.0 changed 1 prims", text)
        code, text = call("compare", self.path("a.json"), self.path("b.json"))
        self.assertEqual(code, 0, text)
        code, text = call("compare", self.path("a.json"), self.path("c.json"))
        self.assertEqual(code, 1, text)
        self.assertIn("CHANGED /world/ball", text)
        self.assertNotIn("CHANGED /world/cam", text)
        code, text = self.digest(one, "d.json", "/stage/still", "--canary-frame", "10")
        self.assertEqual(code, 1, text)
        self.assertIn("canary saw nothing", text)
        code, text = self.digest(one, "e.json", "/stage/still")
        self.assertEqual(code, 2, text)
        self.assertIn("--canary-frame is required", text)
        code, text = self.digest(one, "f.json", "/stage/still", "--no-canary")
        self.assertEqual(code, 0, text)
        self.assertIn("canary skipped", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
