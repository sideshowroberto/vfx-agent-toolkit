#!/usr/bin/env python
"""Validate one skill against ClaudeCode/development/SKILL_AND_AGENT_STANDARD.md.

Checks (FAIL = exit 1, WARN = reported, exit stays 0):
  FAIL  skill folder or SKILL.md not found (never a vacuous pass - obs 434)
  FAIL  frontmatter missing, or not valid YAML (a parse error drops the skill silently - obs 440)
  FAIL  description missing, empty, or written over more than one source line
        (folded '>' / literal '|' / continued plain scalar - OpenCode drops the skill,
        Claude Code may load it with an empty description; eval case sk2)
  FAIL  retired top-level keys (version, last_updated, status, triggers ...): Claude Code
        does not act on them - use metadata: or git history
  FAIL  any other undocumented top-level key
  FAIL  '<' or '>' in description / when_to_use; description + when_to_use over 1,536 chars
  FAIL  non-ASCII bytes or control bytes in shipped scripts (windows-gotchas.md)
  WARN  SKILL.md body over 500 lines; description over 400 chars; "This skill..." opening
  WARN  name differs from folder; reference file over 100 lines without a table of contents
  WARN  absolute drive / user paths inside scripts (constitution Article I)

Usage:
    python validate_skill.py <skill-name | path-to-skill-dir | path-to-SKILL.md> [--skills-path DIR]
Exit: 0 = no FAIL, 1 = at least one FAIL, 2 = PyYAML missing (cannot check, so no pass).
ASCII only.
"""
import argparse
import re
import sys
from pathlib import Path

# Documented SKILL.md frontmatter keys (Claude Code skills docs + Agent Skills spec).
# Re-check against the docs when Claude Code changes; the standard, section 3, is the source.
ALLOWED_KEYS = {
    "name", "description", "when_to_use", "argument-hint", "paths",
    "disable-model-invocation", "user-invocable", "allowed-tools", "disallowed-tools",
    "model", "effort", "context", "agent", "hooks", "shell", "background",
    "metadata", "license", "compatibility",
}
RETIRED_KEYS = {
    "version": "move to metadata.version or rely on git",
    "last_updated": "move to metadata.updated or rely on git",
    "updated": "move to metadata.updated or rely on git",
    "status": "move to metadata.status or rely on git",
    "triggers": "put trigger phrases in when_to_use",
    "dependencies": "state dependencies in the body or metadata",
    "author": "move to metadata.author",
}
# Vendored third-party skills (names or fnmatch patterns, one per line, '#' comments) in
# third_party_skills.txt next to this script. Their frontmatter belongs upstream, and Claude
# Code ignores unknown keys, so retired / undocumented keys WARN instead of FAIL for them.
# Everything that actually breaks loading (YAML, multi-line description, '<' '>', length)
# still FAILs.
THIRD_PARTY_FILE = Path(__file__).resolve().parent / "third_party_skills.txt"


def load_third_party(path=THIRD_PARTY_FILE):
    if not path.is_file():
        return []
    pats = []
    for line in path.read_text(encoding="ascii", errors="replace").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pats.append(line)
    return pats


def is_third_party(folder_name, patterns=None):
    from fnmatch import fnmatchcase
    pats = load_third_party() if patterns is None else patterns
    return any(fnmatchcase(folder_name, p) for p in pats)


SINGLE_LINE_KEYS = ("description", "when_to_use")
BODY_LINE_LIMIT = 500
DESC_SOFT_LIMIT = 400
LISTING_CAP = 1536
ABS_PATH = re.compile(r"(?<![A-Za-z])[A-Za-z]:[\\/][A-Za-z]|/Users/[a-z]|/home/[a-z]")
TOC_HINT = re.compile(r"(?im)^#+\s*(table of )?contents\b|^\s*[-*0-9.]+\s*\[[^\]]+\]\(#")


class Result:
    def __init__(self):
        self.fails = []
        self.warns = []
        self.oks = []

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)

    def ok(self, msg):
        self.oks.append(msg)


def resolve_skill(arg, skills_path):
    """Return the SKILL.md path for a name or a path, or None."""
    # absolute(), not resolve(): resolve() turns a mapped drive into a UNC path (windows-gotchas.md)
    p = Path(arg).absolute()
    if p.is_file() and p.name == "SKILL.md":
        return p
    if p.is_dir() and (p / "SKILL.md").is_file():
        return p / "SKILL.md"
    cand = Path(skills_path) / p.name / "SKILL.md"
    if cand.is_file():
        return cand
    return None


def split_frontmatter(text):
    """Return (frontmatter_lines, body_lines) or (None, lines) when there is no block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, lines
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], lines[i + 1:]
    return None, lines


def check_single_line(fm_lines, key, res):
    """The value of `key` must sit entirely on its own source line."""
    pat = re.compile(r"^" + re.escape(key) + r"\s*:(.*)$")
    for i, line in enumerate(fm_lines):
        m = pat.match(line)
        if not m:
            continue
        rest = m.group(1).strip()
        if rest[:1] in (">", "|"):
            res.fail("%s uses a block scalar '%s' - write it on ONE line (OpenCode drops the "
                     "skill; Claude Code may load an empty description)" % (key, rest[:2].strip()))
            return
        if rest == "":
            res.fail("%s is empty on its line - the value must be on the same line, one line" % key)
            return
        nxt = fm_lines[i + 1] if i + 1 < len(fm_lines) else ""
        if nxt.strip() and nxt[:1] in (" ", "\t"):
            res.fail("%s continues onto the next line - join it into one line" % key)
            return
        res.ok("%s is a single line" % key)
        return


def check_frontmatter(skill_md, res):
    try:
        import yaml
    except ImportError:
        print("[FAIL] PyYAML is not importable - the frontmatter cannot be checked (pip install pyyaml)")
        sys.exit(2)

    raw = skill_md.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        res.warn("SKILL.md starts with a UTF-8 BOM - write it without one")
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace")
    fm_lines, body = split_frontmatter(text)
    if fm_lines is None:
        res.fail("no frontmatter block: SKILL.md must start with '---' and close it with '---'")
        return None, body

    for key in SINGLE_LINE_KEYS:
        check_single_line(fm_lines, key, res)

    try:
        data = yaml.safe_load("\n".join(fm_lines))
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0] if str(exc) else "parse error"
        res.fail("frontmatter is not valid YAML (%s) - quote a value that contains ': '" % first)
        return None, body
    if not isinstance(data, dict):
        res.fail("frontmatter is not a YAML mapping")
        return None, body
    res.ok("frontmatter parses as YAML")

    vendored = is_third_party(skill_md.parent.name)
    if vendored:
        res.ok("third-party skill (third_party_skills.txt): key issues are WARN, fix upstream")
    for key in data:
        if key in RETIRED_KEYS:
            msg = "retired top-level key '%s' - %s" % (key, RETIRED_KEYS[key])
        elif key not in ALLOWED_KEYS:
            msg = "undocumented top-level key '%s' - custom data goes under metadata:" % key
        else:
            continue
        (res.warn if vendored else res.fail)(msg + (" (third-party: ignored by Claude Code)" if vendored else ""))

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        res.fail("description is missing or not a string")
    else:
        desc = desc.strip()
        wtu = data.get("when_to_use") or ""
        if not isinstance(wtu, str):
            res.fail("when_to_use must be a string")
            wtu = ""
        for k, v in (("description", desc), ("when_to_use", wtu)):
            if "<" in v or ">" in v:
                res.fail("%s contains '<' or '>' (renders as &lt;) - use [name]" % k)
        total = len(desc) + len(wtu)
        if total > LISTING_CAP:
            res.fail("description + when_to_use = %d chars, over the %d listing cap" % (total, LISTING_CAP))
        elif len(desc) > DESC_SOFT_LIMIT:
            res.warn("description is %d chars (aim 150-400; long ones push other skills to name-only)" % len(desc))
        else:
            res.ok("description length %d chars" % len(desc))
        if re.match(r"(?i)(this skill|i can|i will|use this skill)\b", desc):
            res.warn("description should open with what it does, third person - not 'This skill...'")
        if not re.search(r"(?i)\buse (when|for|before|after|to)\b", desc + " " + wtu):
            res.warn("description has no 'Use when ...' clause")

    name = data.get("name")
    if name is not None:
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
            res.fail("name '%s' must be kebab-case, max 64 chars" % name)
        elif name != skill_md.parent.name:
            res.warn("name '%s' differs from folder '%s'" % (name, skill_md.parent.name))
    meta = data.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        res.fail("metadata must be a mapping")
    return data, body


def check_body(body, res):
    n = len(body)
    if n > BODY_LINE_LIMIT:
        res.warn("SKILL.md body is %d lines, over %d - move detail to reference/*.md" % (n, BODY_LINE_LIMIT))
    else:
        res.ok("body %d lines (limit %d)" % (n, BODY_LINE_LIMIT))
    fills = sum(1 for line in body if re.match(r"\s*(?:[-*]|\d+\.)\s+FILL:", line))
    if fills:
        res.warn("%d unfilled 'FILL:' placeholder line(s) from create_skill.py" % fills)


def check_files(skill_dir, res):
    for ref in sorted(skill_dir.glob("reference*/*.md")):
        text = ref.read_text(encoding="utf-8", errors="replace")
        if text.count("\n") > 100 and not TOC_HINT.search(text):
            res.warn("%s is over 100 lines with no table of contents" % ref.relative_to(skill_dir))
    for f in sorted(skill_dir.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts:
            continue
        if f.suffix.lower() not in (".py", ".ps1", ".sh", ".bat", ".cmd", ".nk", ".json", ".yaml", ".yml"):
            continue
        b = f.read_bytes()
        rel = f.relative_to(skill_dir)
        if b and max(b) > 127:
            res.fail("%s has non-ASCII bytes" % rel)
        if any(c < 32 and c not in (9, 10, 13) for c in b):
            res.fail("%s has control bytes (an escape-eaten path?)" % rel)
        if f.suffix.lower() in (".py", ".ps1", ".sh"):
            for no, line in enumerate(b.decode("ascii", errors="replace").splitlines(), 1):
                s = line.strip()
                if s.startswith("#") or not ABS_PATH.search(s):
                    continue
                res.warn("%s:%d absolute path - parameterise it (Article I)" % (rel, no))
                break


def validate(skill_md):
    res = Result()
    _data, body = check_frontmatter(skill_md, res)
    check_body(body, res)
    check_files(skill_md.parent, res)
    return res


def main():
    ap = argparse.ArgumentParser(description="Validate a skill against SKILL_AND_AGENT_STANDARD.md")
    ap.add_argument("skill", help="skill name, skill folder, or SKILL.md path")
    ap.add_argument("--skills-path", default=str(Path(__file__).resolve().parents[2]),
                    help="folder holding skills, used when a bare name is given")
    args = ap.parse_args()

    skill_md = resolve_skill(args.skill, args.skills_path)
    if skill_md is None:
        print("[FAIL] skill not found: %s (looked for a folder with SKILL.md, then %s/<name>)"
              % (args.skill, args.skills_path))
        print("Overall: FAIL (nothing was checked)")
        return 1

    print("Validating %s" % skill_md)
    res = validate(skill_md)
    for m in res.oks:
        print("  [OK]   " + m)
    for m in res.warns:
        print("  [WARN] " + m)
    for m in res.fails:
        print("  [FAIL] " + m)
    verdict = "FAIL" if res.fails else "PASS"
    print("Overall: %s (%d fail, %d warn, %d ok)" % (verdict, len(res.fails), len(res.warns), len(res.oks)))
    return 1 if res.fails else 0


if __name__ == "__main__":
    sys.exit(main())
