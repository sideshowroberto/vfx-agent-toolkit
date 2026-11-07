"""Known-good and known-bad cases for nk_version_up.py.

    python test_nk_version_up.py
Set NUKE_EXE to also run the fresh-process cases in a real Nuke; they are reported
as skipped without it. Everything runs in a temp folder, so this works from a
relocated copy of the skill.
"""
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nk_version_up as tool  # noqa: E402

# The shapes a re-save damages: layout header, write_info, a viewerProcess, a group
# with a child sharing a name with a top-level node, a multi-line knob that closes
# in column 0, a quoted brace, a dotted class, and stack lines.
OLD_NK = """#! /opt/nuke/nuke -nx
#write_info Write1 file:"/show/a.####.exr" format:"1920 1080 1"
version 15.1 v10
define_window_layout_xml {<?xml version="1.0" encoding="UTF-8"?>
<layout version="1.0">
    <window x="0" y="0" w="1920" h="1080"/>
</layout>
}
Root {
 inputs 0
 name /show/shot_v001.nk
 frame 1001
 first_frame 1001
 last_frame 1010
}
add_layer {mylayer mylayer.red mylayer.green}
Read {
 inputs 0
 file /show/plate.####.exr
 name Read1
 label "a { brace"
 xpos 100
 ypos -200
}
set N1a2b3c [stack 0]
Dot {
 name Dot1
 tile_color 0xff0000ff
 xpos 134
 ypos -120
}
Group {
 name Group1
 xpos 100
 ypos -60
}
 Input {
  inputs 0
  name Input1
 }
 Dot {
  name Dot1
  note_font Verdana
 }
 Output {
  name Output1
 }
end_group
OFXuk.co.thefoundry.keylight.keylight_v201 {
 screenColour {0 1 0}
 name Keylight1
 xpos 100
 ypos 0
}
Write {
 file /show/a.####.exr
 mov64_opts {
a 1
}
 name Write1
 xpos 100
 ypos 60
}
Viewer {
 frame 1001
 viewerProcess "Output - Rec.709"
 name Viewer1
 xpos 100
 ypos 120
}
"""

SNIPPET = ("set cut_paste_input [stack 0]\r\nversion 15.1 v10\r\npush $cut_paste_input\r\n"
           "Grade {\r\n name NewGrade\r\n selected true\r\n}\r\n"
           "add_layer {extra extra.red}\r\n"
           "Shuffle {\r\n in extra\r\n name NewShuffle\r\n selected true\r\n}\r\n")


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = tool.main(list(argv))
    return code, out.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="nkvu_")
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.old = self.put("old.nk", OLD_NK)
        self.snippet = self.put("snip.nk", SNIPPET)
        self.new = os.path.join(self.dir, "new.nk")

    def put(self, name, text):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(text.encode("latin-1"))
        return path

    def bytes_of(self, path):
        with open(path, "rb") as fh:
            return fh.read()


class Parser(Base):
    def test_every_byte_is_kept_and_blocks_resync_after_column_zero_brace(self):
        script = tool.Script(self.old)
        joined = "".join(script.text[a:b] for a, b in tool.statements(script.text))
        self.assertEqual(joined, script.text)
        names = [block.name for block in script.blocks]
        self.assertIn("Viewer1", names)
        self.assertEqual(script.by_key[("", "Viewer1")].cls, "Viewer")

    def test_same_name_in_a_group_is_a_different_block(self):
        script = tool.Script(self.old)
        self.assertEqual(script.by_key[("", "Dot1")].cls, "Dot")
        self.assertEqual(tool.knob_value(script.by_key[("Group1", "Dot1")].knobs, "note_font"), "Verdana")

    def test_dotted_ofx_class(self):
        block = tool.Script(self.old).by_key[("", "Keylight1")]
        self.assertTrue(block.cls.startswith("OFXuk.co"))

    def test_quoted_brace_does_not_swallow_the_next_block(self):
        self.assertIn(("", "Dot1"), tool.Script(self.old).by_key)


class Append(Base):
    def test_good_lf(self):
        code, text = run("append", self.old, self.new, self.snippet, "--root-name", "/show/shot_v002.nk")
        self.assertEqual(code, 0, text)
        self.assertIn("PROOF", text)
        self.assertIn("DIFF PASS", text)
        new = self.bytes_of(self.new)
        self.assertNotIn(b"\r", new)
        self.assertNotIn(b"cut_paste_input", new)
        self.assertNotIn(b"selected true", new)
        self.assertNotIn(b"version 15.1 v10\npush 0", new)
        self.assertEqual(new.count(b" name /show/shot_v002.nk\n"), 1)
        self.assertIn(b"add_layer {extra extra.red}\n", new)

    def test_good_crlf_keeps_the_old_files_line_ends(self):
        crlf = self.put("crlf.nk", OLD_NK.replace("\n", "\r\n"))
        code, text = run("append", crlf, self.new, self.snippet, "--root-name", "x.nk")
        self.assertEqual(code, 0, text)
        new = self.bytes_of(self.new)
        self.assertEqual(new.count(b"\n"), new.count(b"\r\n"))

    def test_good_old_without_final_newline(self):
        cut = self.put("cut.nk", OLD_NK.rstrip("\n"))
        code, text = run("append", cut, self.new, self.snippet, "--root-name", "x.nk")
        self.assertEqual(code, 0, text)
        self.assertIn(b"}\npush 0\nGrade {", self.bytes_of(self.new))

    def test_note_says_the_first_input_is_cut(self):
        self.assertIn("UNCONNECTED", run("append", self.old, self.new, self.snippet)[1])

    def test_bad_new_exists_is_left_alone(self):
        existing = self.put("new.nk", "artist work\n")
        code, text = run("append", self.old, existing, self.snippet)
        self.assertEqual(code, 1, text)
        self.assertEqual(self.bytes_of(existing), b"artist work\n")

    def test_bad_second_paste_input(self):
        bad = self.put("two.nk", SNIPPET + "push $cut_paste_input\r\nBlur {\r\n name B\r\n}\r\n")
        code, text = run("append", self.old, self.new, bad)
        self.assertEqual(code, 1, text)
        self.assertFalse(os.path.exists(self.new))

    def test_bad_name_clash(self):
        bad = self.put("clash.nk", "Blur {\n name Dot1\n}\n")
        code, text = run("append", self.old, self.new, bad)
        self.assertEqual(code, 1, text)
        self.assertIn("Dot1", text)

    def test_bad_empty_snippet(self):
        bad = self.put("empty.nk", "set cut_paste_input [stack 0]\nversion 15.1 v10\n")
        self.assertEqual(run("append", self.old, self.new, bad)[0], 1)


class Diff(Base):
    def changed(self, before, after):
        self.assertIn(before, OLD_NK)
        return self.put("changed.nk", OLD_NK.replace(before, after, 1))

    def test_good_identical(self):
        code, text = run("diff", self.old, self.old)
        self.assertEqual(code, 0, text)
        self.assertIn("10 unchanged", text)
        self.assertIn("DIFF PASS", text)

    def test_good_root_name_and_knob_order_are_ignored(self):
        moved = self.changed(" name /show/shot_v001.nk\n frame 1001\n", " frame 1001\n name /show/v2.nk\n")
        self.assertEqual(run("diff", self.old, moved)[0], 0)

    def test_bad_lost_viewer_process(self):
        code, text = run("diff", self.old, self.changed(' viewerProcess "Output - Rec.709"\n', ""))
        self.assertEqual(code, 1, text)
        self.assertIn("viewerProcess", text)

    def test_bad_lost_window_layout(self):
        code, text = run("diff", self.old, self.changed('    <window x="0" y="0" w="1920" h="1080"/>\n', ""))
        self.assertEqual(code, 1, text)
        self.assertIn("HEADER", text)

    def test_bad_change_inside_group_with_duplicate_name(self):
        code, text = run("diff", self.old, self.changed("  note_font Verdana\n", ""))
        self.assertEqual(code, 1, text)
        self.assertIn("Group1/Dot1", text)

    def test_bad_change_after_column_zero_brace(self):
        code, text = run("diff", self.old, self.changed(" name Write1\n xpos 100\n", " name Write1\n xpos 999\n"))
        self.assertEqual(code, 1, text)

    def test_bad_missing_block(self):
        code, text = run("diff", self.old, self.put("gone.nk", OLD_NK.split("Viewer {")[0]))
        self.assertEqual(code, 1, text)
        self.assertIn("MISSING Viewer", text)

    def test_bad_lost_add_layer(self):
        code, text = run("diff", self.old, self.changed("add_layer {mylayer mylayer.red mylayer.green}\n", ""))
        self.assertEqual(code, 1, text)
        self.assertIn("LOOSE", text)

    def test_swap_needs_the_flag_and_the_carried_knobs(self):
        swap = (" Dot {\n name Dot1\n tile_color 0xff0000ff\n xpos 134\n ypos -120\n}\n"[1:],
                "Kronos {\n name Dot1\n tile_color 0xff0000ff\n xpos 134\n ypos -120\n}\n")
        carried = self.changed(swap[0], swap[1])
        self.assertEqual(run("diff", self.old, carried)[0], 1)
        self.assertEqual(run("diff", self.old, carried, "--allow-swap")[0], 0)
        dropped = self.put("drop.nk", self.bytes_of(carried).decode("latin-1").replace(" tile_color 0xff0000ff\n", ""))
        code, text = run("diff", self.old, dropped, "--allow-swap")
        self.assertEqual(code, 1, text)
        self.assertIn("CARRY", text)


class Compose(Base):
    def resave(self):
        """What a headless save does to a script, plus one new node."""
        text = OLD_NK.split("Root {")[0].split("version 15.1 v10\n")[0] + "version 15.1 v10\n" + "Root {" \
            + OLD_NK.split("Root {")[1]
        text = text.replace(' viewerProcess "Output - Rec.709"\n', "")
        text = text.replace("  note_font Verdana\n", "")
        return self.put("saved.nk", text + "Blur {\n name AddedBlur\n}\n")

    def test_good_restores_old_blocks_and_keeps_the_new_one(self):
        code, text = run("compose", self.old, self.resave(), self.new, "--root-name", "/show/shot_v002.nk")
        self.assertEqual(code, 0, text)
        new = self.bytes_of(self.new)
        self.assertIn(b"viewerProcess", new)
        self.assertIn(b"note_font Verdana", new)
        self.assertIn(b"define_window_layout_xml", new)
        self.assertIn(b"AddedBlur", new)

    def test_bad_saved_lost_a_block(self):
        lost = self.put("lost.nk", OLD_NK.split("Viewer {")[0])
        code, text = run("compose", self.old, lost, self.new)
        self.assertEqual(code, 1, text)
        self.assertFalse(os.path.exists(self.new))


class Lint(Base):
    def lint(self, source):
        path = self.put("build.py", source)
        return run("lint", path)

    def test_good_nodes_and_inputs(self):
        self.assertEqual(self.lint("import nuke\na = nuke.nodes.Grade()\nb = nuke.nodes.Blur(inputs=[a])\n")[0], 0)

    def test_good_deselect_between_creates(self):
        source = ("import nuke\ndef deselect_all():\n    pass\n"
                  "a = nuke.createNode('Grade')\ndeselect_all()\nb = nuke.createNode('Blur')\n")
        self.assertEqual(self.lint(source)[0], 0)

    def test_good_set_selected_false_in_a_loop(self):
        source = ("import nuke\nfor cls in names:\n"
                  "    for n in nuke.selectedNodes():\n        n.setSelected(False)\n"
                  "    nuke.createNode(cls)\n")
        self.assertEqual(self.lint(source)[0], 0)

    def test_bad_second_create_steals_outputs(self):
        source = "import nuke\na = nuke.createNode('LensA')\nb = nuke.createNode('LensB')\nb.setInput(0, c)\n"
        code, text = self.lint(source)
        self.assertEqual(code, 1, text)
        self.assertIn(":3:", text)

    def test_bad_create_in_a_loop(self):
        self.assertEqual(self.lint("import nuke\nfor c in names:\n    nuke.createNode(c)\n")[0], 1)

    def test_bad_create_in_a_helper(self):
        self.assertEqual(self.lint("import nuke\ndef make(c):\n    return nuke.createNode(c)\n")[0], 1)

    def test_bad_aliases(self):
        self.assertEqual(self.lint("import nuke as nk\ndef f():\n    nk.createNode('A')\n")[0], 1)
        self.assertEqual(self.lint("from nuke import createNode as cn\ndef f():\n    cn('A')\n")[0], 1)

    def test_bad_hasattr_factory(self):
        self.assertEqual(self.lint("import nuke\nok = hasattr(nuke.nodes, 'Foo')\n")[0], 1)

    def test_bad_resave_of_an_opened_script(self):
        code, text = self.lint("import nuke\nnuke.scriptOpen('a')\nnuke.scriptSaveAs('b')\n")
        self.assertEqual(code, 1, text)
        self.assertIn("re-saving", text)

    def test_waiver_comment(self):
        source = "import nuke\na = nuke.createNode('A')\nb = nuke.createNode('B')  # nk-lint: ok\n"
        self.assertEqual(self.lint(source)[0], 0)


class Outputs(Base):
    def frames(self, folder, payloads):
        return [self.put("%s/f.%04d.exr" % (folder, 1001 + i), text) for i, text in enumerate(payloads)]

    def test_good_differ(self):
        self.frames("a", ["1", "2"])
        self.frames("b", ["1", "9"])
        code, text = run("outputs", "--differ", os.path.join(self.dir, "a"), os.path.join(self.dir, "b"))
        self.assertEqual(code, 0, text)
        self.assertIn("1 of 2", text)

    def test_good_same_with_frame_pattern(self):
        self.frames("a", ["1", "2"])
        self.frames("b", ["1", "2"])
        pattern = os.path.join(self.dir, "%s", "f.####.exr")
        self.assertEqual(run("outputs", "--same", pattern % "a", pattern % "b")[0], 0)

    def test_bad_branches_rendered_the_same_thing(self):
        self.frames("a", ["1", "2"])
        self.frames("b", ["1", "2"])
        code, text = run("outputs", "--differ", os.path.join(self.dir, "a"), os.path.join(self.dir, "b"))
        self.assertEqual(code, 1, text)
        self.assertIn("graph bug", text)

    def test_bad_same_but_changed(self):
        self.frames("a", ["1"])
        self.frames("b", ["2"])
        self.assertEqual(run("outputs", "--same", os.path.join(self.dir, "a"), os.path.join(self.dir, "b"))[0], 1)

    def test_bad_nothing_there_is_not_a_pass(self):
        os.makedirs(os.path.join(self.dir, "a"))
        self.frames("b", ["1"])
        code, text = run("outputs", "--differ", os.path.join(self.dir, "a"), os.path.join(self.dir, "b"))
        self.assertEqual(code, 1, text)
        self.assertIn("nothing to compare", text)

    def test_bad_zero_byte_frame(self):
        self.frames("a", [""])
        self.frames("b", ["1"])
        self.assertEqual(run("outputs", "--differ", os.path.join(self.dir, "a"), os.path.join(self.dir, "b"))[0], 1)


class Reads(Base):
    def script(self, file_value, extra=""):
        return self.put("r.nk", "Root {\n name r.nk\n}\nRead {\n inputs 0\n file %s\n%s name Read1\n}\n"
                        % (file_value, extra))

    def test_good(self):
        self.put("plates/p.1001.exr", "x")
        pattern = os.path.join(self.dir, "plates", "p.####.exr").replace("\\", "/")
        self.assertEqual(run("reads", self.script(pattern))[0], 0)

    def test_bad_unrendered(self):
        missing = os.path.join(self.dir, "later", "p.####.exr").replace("\\", "/")
        code, text = run("reads", self.script(missing))
        self.assertEqual(code, 1, text)
        self.assertIn("Read1", text)

    def test_disabled_and_expressions_are_not_called_missing(self):
        self.assertEqual(run("reads", self.script("/nope/p.####.exr", " disable true\n"))[0], 0)
        code, text = run("reads", self.script("[value root.name]/p.####.exr"))
        self.assertEqual(code, 0, text)
        self.assertIn("1 use expressions", text)


BUILD_PROBE = """
import nuke
nuke.scriptOpen(r"{old}")
for node in nuke.allNodes():
    node["selected"].setValue(False)
nuke.Layer("verifylayer", ["verifylayer.red", "verifylayer.green"])
first = nuke.nodes.Grade(name="AddedGrade")
second = nuke.nodes.Shuffle(name="AddedShuffle", inputs=[first])
second["in"].setValue("verifylayer")
first["selected"].setValue(True)
second["selected"].setValue(True)
nuke.nodeCopy(r"{snip}")
"""

PLAIN_OLD = """#! nuke -nx
version 15.1 v10
Root {
 inputs 0
 name old.nk
 frame 1001
 first_frame 1001
 last_frame 1010
}
Constant {
 inputs 0
 channels rgb
 color {0.5 0.25 0.125 1}
 name BaseConstant
 xpos 0
 ypos 0
}
Grade {
 white 1.5
 name BaseGrade
 xpos 0
 ypos 100
}
Group {
 name BaseGroup
 xpos 0
 ypos 200
}
 Input {
  inputs 0
  name Input1
 }
 Blur {
  size 3
  name InnerBlur
 }
 Output {
  name Output1
 }
end_group
"""


@unittest.skipUnless(os.path.isfile(os.environ.get("NUKE_EXE", "")), "NUKE_EXE not set")
class RealNuke(Base):
    def setUp(self):
        Base.setUp(self)
        self.old = self.put("old.nk", PLAIN_OLD)
        self.snip_path = os.path.join(self.dir, "real_snip.nk")
        probe = self.put("probe.py", BUILD_PROBE.format(old=self.old.replace("\\", "/"),
                                                        snip=self.snip_path.replace("\\", "/")))
        subprocess.run([os.environ["NUKE_EXE"], "-t", "--safe", probe], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=120)
        self.assertTrue(os.path.isfile(self.snip_path), "Nuke wrote no snippet")

    def verify(self, *extra):
        return run("verify", self.old, self.new, *extra)

    def test_good_real_snippet_round_trip(self):
        code, text = run("append", self.old, self.new, self.snip_path, "--root-name", "new.nk")
        self.assertEqual(code, 0, text)
        code, text = self.verify()
        self.assertEqual(code, 0, text)
        self.assertRegex(text, r"NK_VERIFY PASS old_nodes=\d+ new_nodes=\d+ added=2 knobs_compared=[1-9]")

    def test_bad_changed_knob_is_seen_by_nuke(self):
        run("append", self.old, self.new, self.snip_path, "--root-name", "new.nk")
        text = self.bytes_of(self.new).decode("latin-1").replace(" white 1.5\n", " white 1.6\n")
        os.remove(self.new)
        self.put("new.nk", text)
        code, text = self.verify()
        self.assertEqual(code, 1, text)
        self.assertIn("BaseGrade.white", text)

    def test_bad_missing_add_layer_is_seen_only_in_a_fresh_process(self):
        run("append", self.old, self.new, self.snip_path, "--root-name", "new.nk")
        lines = self.bytes_of(self.new).decode("latin-1").split("\n")
        kept = [line for line in lines if not line.startswith("add_layer")]
        self.assertLess(len(kept), len(lines), "the real snippet held no add_layer")
        os.remove(self.new)
        self.put("new.nk", "\n".join(kept))
        code, text = self.verify()
        self.assertEqual(code, 1, text)
        self.assertIn("verifylayer", text)

    def test_bad_cut_wire_in_old_graph(self):
        run("append", self.old, self.new, self.snip_path, "--root-name", "new.nk")
        text = self.bytes_of(self.new).decode("latin-1").replace("Grade {\n white 1.5", "Grade {\n inputs 0\n white 1.5")
        os.remove(self.new)
        self.put("new.nk", text)
        code, text = self.verify()
        self.assertEqual(code, 1, text)
        self.assertIn("INPUTS", text)


if __name__ == "__main__":
    unittest.main(verbosity=1)
