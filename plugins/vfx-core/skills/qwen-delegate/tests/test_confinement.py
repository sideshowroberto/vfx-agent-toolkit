"""Offline regression tests; synthetic files only, no inference requests."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import agent_local


class ConfinementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / "allowed"
        self.root.mkdir()
        (self.root / "nested").mkdir()
        (self.root / "inside.txt").write_text("INSIDE_MARKER\n")
        (self.root / "nested" / "other.txt").write_text("NESTED_MARKER\n")
        self.outside = self.base / "outside.txt"
        self.outside.write_text("OUTSIDE_MARKER\n")
        self.sibling = self.base / "allowed-sibling"
        self.sibling.mkdir()
        (self.sibling / "secret.txt").write_text("OUTSIDE_MARKER\n")

    def call(self, name, **args):
        return agent_local.execute_tool(name, args, str(self.root), 1000)

    def test_valid_relative_absolute_and_normalized_reads(self):
        for path in ["inside.txt", str(self.root / "inside.txt"), "nested/../inside.txt"]:
            with self.subTest(path=path):
                self.assertEqual(self.call("read_file", path=path), "INSIDE_MARKER\n")

    def test_escape_paths_for_all_tools(self):
        for path in ["..", str(self.base), str(self.sibling)]:
            for name in ["list_dir", "search_files"]:
                with self.subTest(path=path, tool=name):
                    result = self.call(name, path=path, pattern="MARKER")
                    self.assertIn("outside the allowed directory", result)
        for path in ["../outside.txt", str(self.outside), str(self.sibling / "secret.txt")]:
            with self.subTest(path=path):
                self.assertIn("outside the allowed directory", self.call("read_file", path=path))

    def test_glob_escape_rejected(self):
        for pattern in ["../*.txt", "**/../../*.txt", str(self.base / "*.txt"),
                        r"..\*.txt", r"C:\*.txt", r"\\server\share\*", "C:*.txt"]:
            for tool, key in [("list_dir", "pattern"), ("search_files", "file_pattern")]:
                with self.subTest(pattern=pattern, tool=tool):
                    args = {key: pattern}
                    if tool == "search_files":
                        args["pattern"] = "MARKER"
                    self.assertIn("Glob must be relative", self.call(tool, **args))

    def test_normal_listing_and_recursive_globs(self):
        self.assertEqual(self.call("list_dir"), "inside.txt\nnested/")
        self.assertEqual(self.call("list_dir", pattern="*.txt"), "inside.txt")
        expected = {"inside.txt", os.path.join("nested", "other.txt")}
        self.assertEqual(set(self.call("list_dir", pattern="**/*.txt").splitlines()), expected)
        result = self.call("search_files", pattern="MARKER", file_pattern="*.txt")
        self.assertIn("INSIDE_MARKER", result)
        self.assertIn("NESTED_MARKER", result)
        self.assertNotIn("OUTSIDE_MARKER", result)
        nested = self.call("search_files", pattern="MARKER", file_pattern="nested/*.txt")
        self.assertIn("NESTED_MARKER", nested)
        self.assertNotIn("INSIDE_MARKER", nested)

    def make_link(self, path, target):
        try:
            path.symlink_to(target, target_is_directory=target.is_dir())
        except OSError as error:
            self.skipTest("Symlink creation unavailable: " + str(error))

    def test_outside_symlinks_blocked_and_not_enumerated(self):
        self.make_link(self.root / "escape.txt", self.outside)
        self.make_link(self.root / "escape-dir", self.sibling)
        for path in ["escape.txt", "escape-dir/secret.txt"]:
            self.assertIn("outside the allowed directory", self.call("read_file", path=path))
        for name in ["list_dir", "search_files"]:
            self.assertIn("outside the allowed directory", self.call(name, path="escape-dir", pattern="MARKER"))
        for pattern in [None, "*", "**/*", "escape-dir/*"]:
            self.assertNotIn("escape", self.call("list_dir", pattern=pattern))
        for pattern in ["*.txt", "**/*.txt", "escape-dir/*.txt"]:
            self.assertNotIn("OUTSIDE_MARKER", self.call("search_files", pattern="MARKER", file_pattern=pattern))

    def test_in_root_links_and_recursive_cycle(self):
        self.make_link(self.root / "alias.txt", self.root / "inside.txt")
        self.make_link(self.root / "nested" / "loop", self.root)
        self.assertEqual(self.call("read_file", path="alias.txt"), "INSIDE_MARKER\n")
        result = self.call("search_files", pattern="MARKER")
        self.assertEqual(result.count("INSIDE_MARKER"), 1)
        self.assertEqual(result.count("NESTED_MARKER"), 1)

    def test_missing_file_empty_directory_and_truncation(self):
        self.assertIn("File not found", self.call("read_file", path="missing.txt"))
        (self.root / "empty").mkdir()
        self.assertEqual(self.call("list_dir", path="empty"), "(empty directory)")
        self.assertIn("No matches", self.call("search_files", path="empty", pattern="MARKER"))
        result = agent_local.execute_tool("read_file", {"path": "inside.txt"}, str(self.root), 3)
        self.assertTrue(result.startswith("INS\n"))
        self.assertIn("TRUNCATED", result)


if __name__ == "__main__":
    unittest.main()
