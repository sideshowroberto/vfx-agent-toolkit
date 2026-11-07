#!/usr/bin/env python
"""Version a Nuke script up as TEXT so the diff is the proof, and check the result.

A headless scriptOpen + new nodes + scriptSaveAs passes every count and error check
yet silently changes old blocks. These commands never re-serialise what must not
change. Stdlib only, runs outside Nuke (except `verify`, which launches it).

  append   OLD NEW SNIPPET   OLD bytes + Root name line + cleaned nodeCopy snippet
  compose  OLD SAVED NEW     repair a re-save: put every original block back
  diff     OLD NEW           block diff: every OLD block unchanged in NEW?
  lint     SCRIPT.py ...     build scripts: createNode without a deselect, re-saves
  outputs  --differ A B      hash outputs against each other (also --same)
  reads    SCRIPT.nk         Reads whose files do not exist yet
  verify   OLD NEW --nuke X  every knob compared in a fresh Nuke process

Exit 0 = pass, 1 = a check failed, 2 = bad usage or unreadable input.
Method and traps: reference/version_up_method.md
"""
import argparse
import ast
import glob
import hashlib
import itertools
import os
import re
import subprocess
import sys
from collections import Counter

# Blocks whose children follow them in the file, closed by an end_group line.
GROUP_CLASSES = ("Group", "LiveGroup")
# Display and state knobs a class-swapped block must carry from the old block.
CARRY_KNOBS = ("tile_color", "gl_color", "note_font", "note_font_size", "note_font_color",
               "disable", "hide_input", "label", "xpos", "ypos")
# Top-level brace statements that are not node blocks.
NOT_BLOCKS = ("define_window_layout_xml", "add_layer")


class CheckFailed(Exception):
    """The input was read but a check on it failed (exit 1)."""


# ---------------------------------------------------------------- .nk parsing

def read_text(path):
    # latin-1 maps every byte to one character, so slices stay byte-exact.
    with open(path, "rb") as fh:
        return fh.read().decode("latin-1")


def statement_end(text, pos):
    """Index just past the statement starting at pos.

    A closing brace can sit in column 0 in the middle of a block (multi-line knob
    values do this in real scripts), so line matching loses sync: count braces.
    Quotes only protect braces at command level, as in Tcl.
    """
    if text.startswith("#", pos):
        end = text.find("\n", pos)
        return len(text) if end < 0 else end + 1
    depth, quoted, word_start, size = 0, False, True, len(text)
    while pos < size:
        char = text[pos]
        if char == "\\":
            pos += 2
            word_start = False
            continue
        if quoted:
            quoted = char != '"'
        elif char == '"' and word_start and depth <= 1:
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        elif char == "\n" and depth <= 0:
            return pos + 1
        word_start = char in " \t\r\n{"
        pos += 1
    return size


def statements(text):
    """Split text into (start, end) statement spans covering every byte."""
    spans, pos = [], 0
    while pos < len(text):
        end = statement_end(text, pos)
        spans.append((pos, end))
        pos = end
    return spans


def body_statements(block):
    """Knob statements of one block, stripped, without the header and closing brace."""
    first = block.find("\n") + 1
    last = block.rstrip().rfind("}")
    body = block[first:last]
    return [body[s:e].strip().replace("\r\n", "\n") for s, e in statements(body) if body[s:e].strip()]


def knob_name(statement):
    return statement.split(None, 1)[0] if statement else ""


def knob_value(knobs, name):
    for statement in knobs:
        parts = statement.split(None, 1)
        if parts and parts[0] == name:
            return parts[1] if len(parts) > 1 else ""
    return None


class Block(object):
    def __init__(self, cls, name, path, start, end, text):
        self.cls, self.name, self.path = cls, name, path
        self.start, self.end, self.text = start, end, text
        self.knobs = body_statements(text)

    @property
    def key(self):
        return (self.path, self.name)


class Script(object):
    """A parsed .nk: blocks keyed by group path and name, plus everything else."""

    def __init__(self, path):
        self.path = path
        self.text = read_text(path)
        self.parse()

    def parse(self):
        self.blocks, self.loose, self.root, group = [], [], None, []
        seen = Counter()
        for start, end in statements(self.text):
            item = self.text[start:end]
            head = item.split("\n", 1)[0].rstrip("\r")
            stripped = head.strip()
            if stripped == "end_group":
                if not group:
                    raise CheckFailed("%s: end_group with no open group" % self.path)
                group.pop()
                self.loose.append(item)
                continue
            # Children of nested groups are indented, so an indented header is a real block.
            is_block = stripped.endswith("{") and not stripped.startswith(("#",) + NOT_BLOCKS)
            if not is_block:
                self.loose.append(item)
                continue
            words = stripped[:-1].split()
            cls = words[-1] if words else ""
            knobs = body_statements(item)
            name = knob_value(knobs, "name")
            # Root is keyed by class: its name knob is the file path, which changes.
            name = "Root" if cls == "Root" else name.strip('"') if name else None
            path = "/".join(group)
            seen[(path, name)] += 1
            if name is None or seen[(path, name)] > 1:
                name = "%s#%d" % (name or cls, seen[(path, name)])
            block = Block(cls, name, path, start, end, item)
            self.blocks.append(block)
            if cls == "Root" and self.root is None:
                self.root = block
            if cls in GROUP_CLASSES:
                group.append(name)
        if group:
            raise CheckFailed("%s: unclosed group %s" % (self.path, "/".join(group)))
        self.by_key = dict((block.key, block) for block in self.blocks)

    @property
    def header(self):
        return self.text[:self.root.start] if self.root else ""


def parse_text(text, label):
    script = Script.__new__(Script)
    script.path, script.text = label, text
    script.parse()
    return script


def require_root(script):
    if script.root is None:
        raise CheckFailed("%s has no Root block" % script.path)


def script_eol(text):
    return "\r\n" if text.count("\r\n") * 2 > text.count("\n") else "\n"


def quote_name(value):
    return '"%s"' % value if re.search(r"\s", value) else value


def renamed_root(script, root_name):
    """Root block text with only its name line changed (the new line, the old line)."""
    block = script.root.text
    matches = list(re.finditer(r"^ name [^\r\n]*", block, re.M))
    if len(matches) != 1:
        raise CheckFailed("%s: expected one Root name line, found %d" % (script.path, len(matches)))
    match = matches[0]
    new_line = " name " + quote_name(root_name)
    return block[:match.start()] + new_line + block[match.end():], match.group(0), new_line


def clean_snippet(path):
    """Turn a nodeCopy file into text fit to append. Returns (text, notes)."""
    with open(path, "rb") as fh:
        text = fh.read().decode("latin-1").replace("\r\n", "\n")
    kept, notes, seen_block, pastes = [], [], False, 0
    for line in text.split("\n"):
        if line.startswith("set cut_paste_input") or re.match(r"version \d", line):
            continue
        if line == " selected true":
            continue
        if line == "push $cut_paste_input":
            pastes += 1
            if seen_block:
                raise CheckFailed("push $cut_paste_input after the first node: a wire leaves the "
                                  "copied set mid-graph, which append cannot keep")
            line = "push 0"
        if line.endswith(" {") and not line.startswith((" ", "#", "add_layer")):
            seen_block = True
        kept.append(line)
    cleaned = "\n".join(kept)
    if pastes > 1 or "cut_paste_input" in cleaned:
        raise CheckFailed("%d cut_paste inputs in the snippet; only the first node may have one" % pastes)
    if pastes:
        notes.append("the first node's input 0 is now UNCONNECTED. nodeCopy writes the same line for a "
                     "wire to an uncopied node, so if it fed from an old node that wire is gone")
    return cleaned.rstrip("\n") + "\n", notes


def write_exclusive(path, text):
    with open(path, "xb") as fh:
        fh.write(text.encode("latin-1"))


# ---------------------------------------------------------------- block diff

def diff_scripts(old, new, allow_swap=False):
    """Compare every OLD block in NEW. Returns (problem lines, summary dict)."""
    require_root(old)
    require_root(new)
    problems, same, swapped = [], 0, []
    if old.header.replace("\r\n", "\n") != new.header.replace("\r\n", "\n"):
        problems.append("HEADER differs (everything before Root: layout, write_info, version)")
    for block in old.blocks:
        other = new.by_key.get(block.key)
        if other is None:
            problems.append("MISSING %s %s" % (block.cls, "/".join(filter(None, block.key))))
            continue
        label = "%s %s" % (block.cls, "/".join(filter(None, block.key)))
        if other.cls != block.cls:
            lost = carry_problems(block, other)
            swapped.append(block.name)
            if not allow_swap:
                problems.append("CLASS %s became %s" % (label, other.cls))
            for item in lost:
                problems.append("CARRY %s: %s" % (label, item))
            continue
        only_old, only_new = knob_delta(block, other)
        if not only_old and not only_new:
            same += 1
            continue
        problems.append("CHANGED %s" % label)
        problems.extend("    only old: %s" % line[:150] for line in only_old)
        problems.extend("    only new: %s" % line[:150] for line in only_new)
    old_loose, new_loose = loose_lines(old), loose_lines(new)
    for line in sorted((old_loose - new_loose).elements()):
        problems.append("LOOSE line lost: %s" % line[:150])
    summary = {"old_blocks": len(old.blocks), "new_blocks": len(new.blocks), "same": same,
               "swapped": len(swapped), "added": len([b for b in new.blocks if b.key not in old.by_key])}
    return problems, summary


def knob_delta(old_block, new_block):
    old_set, new_set = Counter(old_block.knobs), Counter(new_block.knobs)
    if old_block.cls == "Root":
        for counter in (old_set, new_set):
            for statement in list(counter):
                if knob_name(statement) == "name":
                    del counter[statement]
    return sorted((old_set - new_set).elements()), sorted((new_set - old_set).elements())


def carry_problems(old_block, new_block):
    lost = []
    for knob in CARRY_KNOBS:
        was, now = knob_value(old_block.knobs, knob), knob_value(new_block.knobs, knob)
        if was != now:
            lost.append("%s was %s, now %s" % (knob, was, now))
    return lost


def loose_lines(script):
    """Non-block statements after Root, without stack lines: Nuke renumbers those on
    a save, and wiring is compared node by node in the fresh-process verify."""
    found = Counter()
    for item in script.loose:
        line = item.strip().replace("\r\n", "\n")
        if not line or line.startswith(("push ", "set ", "end_group", "version ", "#")):
            continue
        if script.root and line in script.header.replace("\r\n", "\n"):
            continue
        found[line] += 1
    return found


def print_diff(old, new, allow_swap):
    problems, summary = diff_scripts(old, new, allow_swap)
    for line in problems:
        print(line)
    print("DIFF old %(old_blocks)d blocks, new %(new_blocks)d: %(same)d unchanged, "
          "%(swapped)d swapped, %(added)d added" % summary)
    print("DIFF %s" % ("FAIL %d problem lines" % len(problems) if problems else "PASS"))
    return 1 if problems else 0


# ---------------------------------------------------------------- commands

def cmd_append(args):
    old = Script(args.old)
    require_root(old)
    if os.path.exists(args.new):
        raise CheckFailed("refusing to overwrite %s" % args.new)
    snippet, notes = clean_snippet(args.snippet)
    root_block, old_line, new_line = renamed_root(old, args.root_name or args.new.replace("\\", "/"))
    added = parse_text(snippet, args.snippet).blocks
    if not added:
        raise CheckFailed("the snippet holds no node blocks")
    clashes = sorted(b.name for b in added if b.key in old.by_key)
    if clashes:
        raise CheckFailed("snippet names already used in OLD: %s" % ", ".join(clashes))
    eol = script_eol(old.text)
    new_text = old.text[:old.root.start] + root_block + old.text[old.root.end:]
    if not new_text.endswith("\n"):
        new_text += eol
    new_text += snippet.replace("\n", eol)
    write_exclusive(args.new, new_text)

    back = read_text(args.new)
    undone = back.replace(new_line, old_line, 1)
    if not undone.startswith(old.text):
        raise CheckFailed("PROOF failed: NEW minus the Root name line does not start with OLD")
    print("PROOF NEW minus the Root name line starts with OLD (%d of %d bytes)" % (len(old.text), len(back)))
    print("ADDED %d blocks: %s" % (len(added), ", ".join(b.name for b in added[:12])))
    for note in notes:
        print("NOTE " + note)
    return print_diff(old, Script(args.new), False)


def cmd_compose(args):
    old, saved = Script(args.old), Script(args.saved)
    require_root(old)
    require_root(saved)
    if os.path.exists(args.new):
        raise CheckFailed("refusing to overwrite %s" % args.new)
    missing = [b.name for b in old.blocks if b.key not in saved.by_key]
    if missing:
        raise CheckFailed("SAVED lost %d OLD blocks: %s" % (len(missing), ", ".join(missing[:12])))
    root_block = renamed_root(old, args.root_name or args.new.replace("\\", "/"))[0]
    eol = script_eol(old.text)
    parts, restored, pos = [old.header, root_block], 0, saved.root.end
    for block in (b for b in saved.blocks if b.start >= saved.root.end):
        parts.append(to_eol(saved.text[pos:block.start], eol))
        original = old.by_key.get(block.key)
        if original is None:
            parts.append(to_eol(block.text, eol))
        else:
            parts.append(original.text)
            restored += 1
        pos = block.end
    parts.append(to_eol(saved.text[pos:], eol))
    write_exclusive(args.new, "".join(parts))
    print("COMPOSE restored %d original blocks plus Root and the header" % restored)
    return print_diff(old, Script(args.new), False)


def to_eol(text, eol):
    return text.replace("\r\n", "\n").replace("\n", eol)


def cmd_diff(args):
    return print_diff(Script(args.old), Script(args.new), args.allow_swap)


class LintVisitor(ast.NodeVisitor):
    """Walks one scope in source order and records what each createNode follows."""

    def __init__(self, names):
        self.names = names
        self.findings = []
        self.state = "clear"     # "clear" = nothing is known to be selected

    def call_name(self, node):
        func = node.func
        if isinstance(func, ast.Attribute):
            owner = func.value.id if isinstance(func.value, ast.Name) else ""
            return owner, func.attr
        return "", func.id if isinstance(func, ast.Name) else ""

    def is_deselect(self, node):
        owner, name = self.call_name(node)
        if re.search(r"deselect|clear_?selection", name, re.I):
            return True
        if name in ("setSelected", "setValue") and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and arg.value is False:
                if name == "setSelected":
                    return True
                value = node.func.value
                return isinstance(value, ast.Subscript) and "selected" in ast.dump(value)
        return owner == "nuke" and name == "invertSelection"

    def visit_FunctionDef(self, node):
        lint_scope(node, self.names, self.findings)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        lint_scope(node, self.names, self.findings)

    def creates(self, node):
        return any(isinstance(item, ast.Call) and (self.call_name(item) in self.names
                                                   or ("", self.call_name(item)[1]) in self.names)
                   for item in ast.walk(node))

    def visit_For(self, node):
        if self.creates(node):
            self.state = "selected"  # the second pass runs after the body's last createNode
        for child in node.body:
            self.visit(child)
        for child in node.orelse:
            self.visit(child)

    visit_While = visit_For

    def visit_Call(self, node):
        for child in ast.iter_child_nodes(node):
            self.visit(child)
        owner, name = self.call_name(node)
        if self.is_deselect(node):
            self.state = "clear"
        elif (owner, name) in self.names or ("", name) in self.names:
            if self.state != "clear":
                self.findings.append((node.lineno, "createNode with a node still selected: it takes over "
                                      "that node's outputs. Use nuke.nodes.X(inputs=[...]) or deselect first"))
            self.state = "selected"


def lint_scope(tree, names, findings):
    visitor = LintVisitor(names)
    visitor.findings = findings
    if not isinstance(tree, ast.Module):
        visitor.state = "selected"  # a caller may leave anything selected
    for child in tree.body:
        visitor.visit(child)


def lint_file(path):
    with open(path, encoding="utf-8") as fh:
        source = fh.read()
    tree = ast.parse(source, path)
    names = {("nuke", "createNode")}
    opens, saves, hard = False, [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "nuke" and alias.asname:
                    names.add((alias.asname, "createNode"))
        elif isinstance(node, ast.ImportFrom) and node.module == "nuke":
            for alias in node.names:
                if alias.name == "createNode":
                    names.add(("", alias.asname or alias.name))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        attr = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
        if attr == "scriptOpen":
            opens = True
        elif attr in ("scriptSave", "scriptSaveAs"):
            saves.append(node.lineno)
        elif attr == "hasattr" and len(node.args) == 2 and "nodes" in ast.dump(node.args[0]):
            hard.append((node.lineno, "hasattr(nuke.nodes, X) is True for ANY name; call it and catch the error"))
    lint_scope(tree, names, hard)
    if opens:
        for line in saves:
            hard.append((line, "re-saving an opened script changes old blocks; use append or compose"))
    allowed = source.splitlines()
    return sorted(item for item in hard if "nk-lint: ok" not in allowed[item[0] - 1])


def cmd_lint(args):
    total = 0
    for path in args.scripts:
        findings = lint_file(path)
        total += len(findings)
        for line, message in findings:
            print("%s:%d: %s" % (path, line, message))
    print("LINT %s, %d files, %d findings" % ("FAIL" if total else "PASS", len(args.scripts), total))
    return 1 if total else 0


def frame_files(spec):
    if os.path.isdir(spec):
        found = [os.path.join(spec, name) for name in os.listdir(spec)]
    else:
        pattern = re.sub(r"%0?\d*d|#+", "*", glob.escape(spec).replace("[#]", "#").replace("[%]", "%"))
        found = glob.glob(pattern)
    files = [path for path in found if os.path.isfile(path)]

    def order(path):
        numbers = re.findall(r"\d+", os.path.basename(path))
        return (int(numbers[-1]) if numbers else -1, path)
    return sorted(files, key=order)


def digest(path):
    sha = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    return sha.hexdigest()


def cmd_outputs(args):
    specs = args.differ or args.same
    sets = {}
    for spec in specs:
        files = frame_files(spec)
        empty = [path for path in files if os.path.getsize(path) == 0]
        if not files or empty:
            raise CheckFailed("no usable files for %s (%d found, %d empty): nothing to compare"
                              % (spec, len(files), len(empty)))
        sets[spec] = [digest(path) for path in files]
    failed = False
    for one, two in itertools.combinations(specs, 2):
        if len(sets[one]) != len(sets[two]):
            print("LENGTH %s has %d files, %s has %d" % (one, len(sets[one]), two, len(sets[two])))
            failed = failed or bool(args.same)
        pairs = list(zip(sets[one], sets[two]))
        equal = sum(1 for a, b in pairs if a == b)
        print("PAIR %d of %d files identical: %s | %s" % (equal, len(pairs), one, two))
        if args.differ and equal == len(pairs):
            print("  these should differ and do not: a graph bug until proved otherwise")
            failed = True
        if args.same and equal != len(pairs):
            failed = True
    print("OUTPUTS %s" % ("FAIL" if failed else "PASS"))
    return 1 if failed else 0


def cmd_reads(args):
    script = Script(args.script)
    missing, skipped, checked = [], 0, 0
    for block in script.blocks:
        if block.cls not in ("Read", "DeepRead", "ReadGeo2", "GeoImport"):
            continue
        value = knob_value(block.knobs, "file")
        if value is None or knob_value(block.knobs, "disable") == "true":
            continue
        value = value.strip('"{}')
        if "[" in value or "$" in value:
            skipped += 1
            continue
        checked += 1
        if not frame_files(value) and not os.path.exists(value):
            missing.append((block.name, value))
    for name, value in missing:
        print("NOFILES %s %s" % (name, value))
    print("READS %s, %d checked, %d missing, %d use expressions (not checked)"
          % ("FAIL" if missing else "PASS", checked, len(missing), skipped))
    return 1 if missing else 0


def cmd_verify(args):
    nuke_exe = args.nuke or os.environ.get("NUKE_EXE")
    if not nuke_exe or not os.path.isfile(nuke_exe):
        raise ValueError("pass --nuke <path to the Nuke executable> or set NUKE_EXE")
    tool = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nk_fresh_verify.py")
    command = [nuke_exe, "-t", "--safe", tool, os.path.abspath(args.old), os.path.abspath(args.new)]
    command += ["--ignore=" + item for item in args.ignore]
    if args.allow_swap:
        command.append("--allow-swap")
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True, errors="replace")
    lines = result.stdout.splitlines()
    verdict = [line for line in lines if line.startswith("NK_VERIFY")]
    # NEW lines list each added node's inputs: the place a cut first input shows.
    for line in lines:
        if line.startswith("NK_VERIFY") or line.startswith("NEW "):
            print(line)
    # The marker is the result. An exit code alone does not prove the check ran.
    if not any(line.startswith("NK_VERIFY PASS") for line in verdict):
        print(result.stdout[-2000:])
        return 1
    added = new_warnings(result.stdout)
    for line in added:
        print("WARNING only in NEW: %s" % line[:200])
    print("VERIFY %s" % ("FAIL" if added else "PASS"))
    return 1 if added else 0


def new_warnings(output):
    """Warnings printed while NEW loaded that OLD does not print."""
    phases, current = {}, None
    for line in output.splitlines():
        if line.startswith("NK_PHASE "):
            current = line.split()[1]
            continue
        line = re.sub(r"^\[[\d:.]+\]\s*", "", line.strip())
        if current and re.search(r"warning|error", line, re.I):
            phases.setdefault(current, []).append(line)
    if "done" not in output:
        return ["the phase markers are incomplete, warnings could not be compared"]
    old = set(phases.get("old", []))
    return [line for line in phases.get("new", []) if line not in old]


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    item = sub.add_parser("append", help="OLD bytes + Root name line + cleaned snippet")
    item.add_argument("old")
    item.add_argument("new")
    item.add_argument("snippet")
    item.add_argument("--root-name", help="value for the Root name line (default: NEW path)")
    item.set_defaults(run=cmd_append)

    item = sub.add_parser("compose", help="put every original block back into a re-saved script")
    item.add_argument("old")
    item.add_argument("saved")
    item.add_argument("new")
    item.add_argument("--root-name")
    item.set_defaults(run=cmd_compose)

    item = sub.add_parser("diff", help="every OLD block unchanged in NEW")
    item.add_argument("old")
    item.add_argument("new")
    item.add_argument("--allow-swap", action="store_true",
                      help="accept class changes when the state knobs were carried")
    item.set_defaults(run=cmd_diff)

    item = sub.add_parser("lint", help="check build scripts")
    item.add_argument("scripts", nargs="+")
    item.set_defaults(run=cmd_lint)

    item = sub.add_parser("outputs", help="hash outputs against each other")
    group = item.add_mutually_exclusive_group(required=True)
    group.add_argument("--differ", nargs="+", metavar="OUT", help="these must not be identical")
    group.add_argument("--same", nargs="+", metavar="OUT", help="these must be identical")
    item.set_defaults(run=cmd_outputs)

    item = sub.add_parser("reads", help="Reads whose files do not exist")
    item.add_argument("script")
    item.set_defaults(run=cmd_reads)

    item = sub.add_parser("verify", help="compare every knob in a fresh Nuke process")
    item.add_argument("old")
    item.add_argument("new")
    item.add_argument("--nuke", help="Nuke executable (default: NUKE_EXE)")
    item.add_argument("--ignore", action="append", default=[], metavar="NODE.KNOB")
    item.add_argument("--allow-swap", action="store_true")
    item.set_defaults(run=cmd_verify)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except CheckFailed as exc:
        print("FAIL %s" % exc)
        return 1
    except (OSError, ValueError, SyntaxError) as exc:
        print("ERROR %s" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
