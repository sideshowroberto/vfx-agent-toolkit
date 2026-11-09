#!/usr/bin/env python
"""Scaffold a new skill in the SKILL_AND_AGENT_STANDARD.md format, then validate it.

Writes <skills-path>/<name>/SKILL.md with:
  - single-line, quoted description (and optional when_to_use / paths / manual flag)
  - bookkeeping under metadata: (never top-level version/last_updated/status)
  - a traps-first body skeleton you fill in, well under 500 lines
Optional empty reference/ and scripts/ folders. Refuses to overwrite an existing skill.

Usage:
    python create_skill.py my-skill --description "Does X. Use when Y." \
        [--when-to-use "Triggers on 'a', 'b'."] [--paths "**/*.nk"] [--manual] \
        [--reference] [--scripts] [--skills-path DIR] [--dry-run]
ASCII only.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent

BODY = """
# {name}

## Rules and traps (read first)

- FILL: the things Claude gets wrong without this skill, each with how it was measured.
- FILL: the mandatory first step, if there is one.

## Steps

1. FILL: the one command or procedure most runs need.

## Reference

- FILL or delete: link reference/*.md files directly from here (one level deep).
"""


def one_line(label, value):
    if value is None:
        return None
    if "\n" in value or "\r" in value:
        sys.exit("[FAIL] --%s must be ONE line" % label)
    if any(ord(c) > 127 for c in value):
        sys.exit("[FAIL] --%s must be ASCII" % label)
    if "<" in value or ">" in value:
        sys.exit("[FAIL] --%s must not contain '<' or '>' (use [name])" % label)
    return value.strip()


def build(args):
    desc = one_line("description", args.description)
    wtu = one_line("when-to-use", args.when_to_use)
    fm = ["---", "name: " + args.name, "description: " + json.dumps(desc)]
    if wtu:
        fm.append("when_to_use: " + json.dumps(wtu))
    if args.paths:
        globs = [p.strip() for p in args.paths.split(",") if p.strip()]
        fm.append("paths: " + json.dumps(globs))
    if args.manual:
        fm.append("disable-model-invocation: true")
    fm += ["metadata:", "  version: 0.1.0", "  updated: %s" % date.today().isoformat(), "---"]
    return "\n".join(fm) + "\n" + BODY.format(name=args.name)


def main():
    ap = argparse.ArgumentParser(description="Scaffold a skill in the house standard format")
    ap.add_argument("name", help="kebab-case skill name, max 64 chars")
    ap.add_argument("--description", required=True, help="ONE line: what it does. Use when ...")
    ap.add_argument("--when-to-use", help="ONE line of trigger phrases")
    ap.add_argument("--paths", help="comma-separated globs, only for file-type skills")
    ap.add_argument("--manual", action="store_true", help="set disable-model-invocation (release/deploy workflows)")
    ap.add_argument("--reference", action="store_true", help="create an empty reference/ folder")
    ap.add_argument("--scripts", action="store_true", help="create an empty scripts/ folder")
    ap.add_argument("--skills-path", default=str(HERE.parents[1]), help="folder to create the skill in")
    ap.add_argument("--dry-run", action="store_true", help="print SKILL.md, write nothing")
    args = ap.parse_args()

    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", args.name) or len(args.name) > 64:
        sys.exit("[FAIL] name must be kebab-case, max 64 chars")
    text = build(args)
    if args.dry_run:
        print(text)
        return 0

    skill_dir = Path(args.skills_path) / args.name
    if skill_dir.exists():
        sys.exit("[FAIL] %s already exists - edit it instead (update_skill.py for metadata)" % skill_dir)
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_bytes(text.encode("ascii"))
    for flag, sub in ((args.reference, "reference"), (args.scripts, "scripts")):
        if flag:
            (skill_dir / sub).mkdir()
    print("[OK] created %s" % (skill_dir / "SKILL.md"))

    sys.path.insert(0, str(HERE))
    import validate_skill
    res = validate_skill.validate(skill_dir / "SKILL.md")
    for m in res.warns + res.fails:
        print("  " + m)
    print("Validator: %s" % ("FAIL" if res.fails else "PASS"))
    print("Next: replace every FILL line, then run the no-skill baseline eval (standard, section 7).")
    return 1 if res.fails else 0


if __name__ == "__main__":
    sys.exit(main())
