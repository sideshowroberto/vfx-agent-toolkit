"""Known-good and known-bad cases for karma_rop.py.

    python test_karma_rop.py
Set HYTHON to a hython.exe to add a real render: a tiny scene, good, CPU delegate, and a missing texture.
That run uses a Houdini licence and a little GPU memory, and is skipped without HYTHON.
"""
import contextlib
import glob
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import karma_rop as tool  # noqa: E402

GPU = {"xpu_device_contrib": 100, "xpu_device_error": "", "xpu_device_label": "Test GPU", "xpu_device_type": "Optix"}
CPU_DEVICE = {"xpu_device_contrib": 0, "xpu_device_error": "", "xpu_device_label": "Embree CPU device",
              "xpu_device_type": "EmbreeCPU"}
XPU_SOFTWARE = "Karma (xpu) 21.0.596"
XPU_COMMAND = "husk -f 1 -R BRAY_HdKarmaXPU scene.usd"
BUILD_SCENE = r'''
import sys
import hou
hip, texture = sys.argv[1], sys.argv[2]
stage = hou.node("/stage")
script = stage.createNode("pythonscript", "scene")
script.parm("python").set("""
from pxr import Gf, Sdf, UsdGeom, UsdLux, UsdShade
stage = hou.pwd().editableStage()
plane = UsdGeom.Mesh.Define(stage, "/world/plane")
plane.CreatePointsAttr([(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)])
plane.CreateFaceVertexCountsAttr([4])
plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
uv = UsdGeom.PrimvarsAPI(plane).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying)
uv.Set([(0, 0), (1, 0), (1, 1), (0, 1)])
material = UsdShade.Material.Define(stage, "/world/look")
surface = UsdShade.Shader.Define(stage, "/world/look/surface")
surface.CreateIdAttr("UsdPreviewSurface")
reader = UsdShade.Shader.Define(stage, "/world/look/st")
reader.CreateIdAttr("UsdPrimvarReader_float2")
reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
image = UsdShade.Shader.Define(stage, "/world/look/map")
image.CreateIdAttr("UsdUVTexture")
image.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(%r)
image.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(reader.ConnectableAPI(), "result")
surface.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(
    image.ConnectableAPI().CreateOutput("rgb", Sdf.ValueTypeNames.Float3))
material.CreateSurfaceOutput().ConnectToSource(surface.ConnectableAPI(), "surface")
UsdShade.MaterialBindingAPI.Apply(plane.GetPrim()).Bind(material)
light = UsdLux.DistantLight.Define(stage, "/world/sun")
light.CreateIntensityAttr(3)
camera = UsdGeom.Camera.Define(stage, "/world/cam")
camera.AddTranslateOp().Set(Gf.Vec3d(0, 0, 4))
""" % texture)
settings = stage.createNode("karmarenderproperties", "settings")
settings.setInput(0, script)
settings.parm("camera").set("/world/cam")
settings.parm("resolutionx").set(640)  # a render under a second can end on Embree before the GPU joins
settings.parm("convergence_mode").set("Path Traced")
settings.parm("pathtracedsamples").set(256)
rop = stage.createNode("usdrender_rop", "render")
rop.setInput(0, settings)
hou.hipFile.save(hip)
print("BUILT", rop.path(), rop.parm("renderer").evalAsString())
'''


def attribute(name, kind, value):
    return name.encode() + b"\0" + kind.encode() + b"\0" + struct.pack("<I", len(value)) + value


def string(name, text):
    return attribute(name, "string", text.encode())


def exr(path, software=XPU_SOFTWARE, command=XPU_COMMAND, devices=(GPU, CPU_DEVICE), multipart=True):
    header = string("Software", software) + string("husk:command", command) + string("renderTime_s", "0:00:11")
    if devices is not None:
        header += string("husk:render_stats", json.dumps({"xpu_devices": list(devices)}))
    second = string("name", "depth") + b"\0" if multipart else b""
    body = struct.pack("<II", tool.EXR_MAGIC, 2 | (tool.MULTIPART_FLAG if multipart else 0)) + header + b"\0" + second
    with open(path, "wb") as fh:
        fh.write(body + (b"\0" if multipart else b"") + b"\xff" * 64)
    return path


def call(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tool.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="karma_")
        self.addCleanup(shutil.rmtree, self.dir, True)

    def path(self, name):
        return os.path.join(self.dir, name)

    def text(self, name, body):
        with open(self.path(name), "w", encoding="utf-8") as fh:
            fh.write(body)
        return self.path(name)


class Meta(Base):
    def test_good_xpu_multipart(self):
        code, text = call("meta", exr(self.path("a.exr")), "--expect", "xpu")
        self.assertEqual(code, 0, text)
        self.assertIn("Optix 100", text)

    def test_good_single_part(self):
        self.assertEqual(call("meta", exr(self.path("a.exr"), multipart=False), "--expect", "xpu")[0], 0)

    def test_good_cpu_when_cpu_is_wanted(self):
        path = exr(self.path("a.exr"), "Karma (cpu) 21.0.596", "husk -R BRAY_HdKarma s.usd", devices=None)
        self.assertEqual(call("meta", path, "--expect", "cpu")[0], 0)

    def test_bad_cpu_when_xpu_is_wanted(self):
        path = exr(self.path("a.exr"), "Karma (cpu) 21.0.596", "husk -R BRAY_HdKarma s.usd", devices=None)
        code, text = call("meta", path, "--expect", "xpu")
        self.assertEqual(code, 1, text)
        self.assertIn("rendered on cpu", text)

    def test_bad_xpu_with_no_gpu_share(self):
        gone = dict(GPU, xpu_device_contrib=0)
        code, text = call("meta", exr(self.path("a.exr"), devices=(gone, dict(CPU_DEVICE, xpu_device_contrib=100))))
        self.assertEqual(code, 1, text)
        self.assertIn("XPU in name only", text)

    def test_bad_device_error(self):
        broken = dict(GPU, xpu_device_error="OptiX failed")
        code, text = call("meta", exr(self.path("a.exr"), devices=(broken, CPU_DEVICE)))
        self.assertEqual(code, 1, text)
        self.assertIn("OptiX failed", text)

    def test_bad_no_device_table(self):
        self.assertEqual(call("meta", exr(self.path("a.exr"), devices=None))[0], 1)

    def test_bad_not_karma(self):
        self.assertEqual(call("meta", exr(self.path("a.exr"), "Nuke 15.1", "", devices=None))[0], 1)

    def test_bad_delegate_disagrees_with_software(self):
        path = exr(self.path("a.exr"), command="husk -R BRAY_HdKarma s.usd")
        self.assertEqual(call("meta", path, "--expect", "xpu")[0], 1)

    def test_usage_not_an_exr(self):
        self.assertEqual(call("meta", self.text("a.exr", "not an image"))[0], 2)

    def test_usage_truncated_header(self):
        path = exr(self.path("a.exr"))
        with open(path, "r+b") as fh:
            fh.truncate(60)
        self.assertEqual(call("meta", path)[0], 2)


class Scan(Base):
    def test_good_clean_log_and_benign_echoes(self):
        code, text = call("scan", self.text("a.txt", "[1] Loading\n failure_retries : 0\n max_errors_per_file : 100\n"))
        self.assertEqual(code, 0, text)

    def test_bad_h21_wording(self):
        code, text = call("scan", self.text("a.txt", "[15:40:00] Texture missing/error: /maps/a.png\n"))
        self.assertEqual(code, 1, text)
        self.assertIn("1 texture errors", text)

    def test_bad_licence_and_gpu(self):
        self.assertEqual(call("scan", self.text("a.txt", "Licence checkout refused\n"))[0], 1)
        self.assertEqual(call("scan", self.text("b.txt", "CUDA device lost\n"))[0], 1)

    def test_bad_empty_log_saw_nothing(self):
        code, text = call("scan", self.text("a.txt", ""))
        self.assertEqual(code, 1, text)
        self.assertIn("saw nothing", text)

    def test_bad_missing_log_saw_nothing(self):
        self.assertEqual(call("scan", self.path("gone.txt"))[0], 1)

    def test_other_trouble_is_a_note(self):
        code, text = call("scan", self.text("a.txt", "something failed politely\n"))
        self.assertEqual(code, 0, text)
        self.assertIn("NOTE", text)


class Estimate(Base):
    def run_pair(self, short, long_run, images=258):
        one = self.text("a.json", json.dumps({"timing": {"images": short[0], "seconds": short[1]}}))
        two = self.text("b.json", json.dumps({"timing": {"images": long_run[0], "seconds": long_run[1]}}))
        return call("estimate", one, two, "--images", str(images))

    def test_good_two_lengths_show_the_real_rate(self):
        code, text = self.run_pair((4, 60), (24, 200))
        self.assertEqual(code, 0, text)
        self.assertIn("7.0 s per image", text)
        self.assertIn("32.0 s launch", text)

    def test_bad_same_length(self):
        self.assertEqual(self.run_pair((4, 60), (4, 62))[0], 1)

    def test_bad_both_too_short(self):
        self.assertEqual(self.run_pair((2, 30), (4, 40))[0], 1)

    def test_bad_longer_was_not_slower(self):
        self.assertEqual(self.run_pair((4, 60), (24, 50))[0], 1)


@unittest.skipUnless(os.environ.get("HYTHON"), "HYTHON not set")
class RealRender(Base):
    def hython(self, *argv):
        env = dict(os.environ)
        env.pop("HFS", None)
        result = subprocess.run([os.environ["HYTHON"]] + list(argv), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                universal_newlines=True, errors="replace", env=env)
        return result.returncode, result.stdout

    def build(self, name, texture):
        builder = self.text("build.py", BUILD_SCENE)
        hip = self.path(name).replace("\\", "/")
        code, text = self.hython(builder, hip, texture)
        self.assertEqual(code, 0, text)
        self.assertIn("BUILT", text)
        return hip

    def render(self, hip, folder, *extra):
        output = self.path(folder + "/f.$F4.exr").replace("\\", "/")
        return self.hython(os.path.join(HERE, "karma_rop.py"), "render", hip, "--rop", "/stage/render",
                           "--frames", "1", "2", "--output", output, *extra)

    def good_map(self):
        import zlib
        rows = b"".join(b"\0" + b"\x80\x40\x20" * 4 for _ in range(4))
        chunks = [(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0)), (b"IDAT", zlib.compress(rows)), (b"IEND", b"")]
        body = b"\x89PNG\r\n\x1a\n"
        for tag, data in chunks:
            body += struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
        path = self.path("map.png")
        with open(path, "wb") as fh:
            fh.write(body)
        return path.replace("\\", "/")

    def test_real_render_good_bad_and_audit(self):
        good = self.build("good.hip", self.good_map())
        code, text = self.hython(os.path.join(HERE, "karma_rop.py"), "audit", good, "--expect", "xpu")
        self.assertEqual(code, 1, text)  # a new ROP defaults to the CPU delegate
        code, text = self.hython(os.path.join(HERE, "karma_rop.py"), "audit", good, "--expect", "xpu", "--fix")
        self.assertEqual(code, 0, text)
        code, text = self.render(good, "good")
        self.assertEqual(code, 0, text)
        self.assertIn("Karma (xpu)", text)
        reports = glob.glob(self.path("good/*_report.json"))
        self.assertEqual(len(reports), 1, text)
        with open(reports[0], encoding="utf-8") as fh:
            self.assertGreater(json.load(fh)["scan"]["log_lines"], 0)
        code, text = self.render(good, "good")
        self.assertEqual(code, 1, text)  # the second run finds the first run's files
        self.assertIn("exist already", text)
        code, text = self.render(good, "cpu", "--expect", "cpu")
        self.assertEqual(code, 0, text)
        self.assertIn("Karma (cpu)", text)
        code, text = call("meta", sorted(glob.glob(self.path("cpu/*.exr")))[0], "--expect", "xpu")
        self.assertEqual(code, 1, text)
        code, text = self.render(good, "once", "--all-at-once")
        self.assertEqual(code, 0, text)
        self.assertEqual(len(glob.glob(self.path("once/*.exr"))), 2, text)
        code, text = self.render(good, "half", "--step", "0.5")
        self.assertEqual(code, 1, text)  # $F4 rounds 1.5, so two samples would share a file
        self.assertIn("fractional", text)
        self.assertEqual(glob.glob(self.path("half/*.exr")), [], text)
        missing = self.build("missing.hip", self.path("nothing_here.png").replace("\\", "/"))
        code, text = self.render(missing, "missing")
        self.assertEqual(code, 1, text)
        self.assertIn("texture errors", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
