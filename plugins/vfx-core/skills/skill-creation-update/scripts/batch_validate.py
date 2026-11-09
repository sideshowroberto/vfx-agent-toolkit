#!/usr/bin/env python
"""Validate every skill under a skills folder and flag retired folders that still load.

Usage:
    python batch_validate.py [--skills-path DIR] [--quiet]
Prints one line per skill (PASS / FAIL with the fail messages), then a summary.
Also FAILS on a folder named 'archive' holding a SKILL.md under the skills root: it is scanned,
so retired skills belong outside .claude/ (standard, section 5).
Exit 1 when anything failed. ASCII only.
"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_skill  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Validate all skills in a folder")
    ap.add_argument("--skills-path", default=str(HERE.parents[1]))
    ap.add_argument("--quiet", action="store_true", help="print failing skills only")
    args = ap.parse_args()
    root = Path(args.skills_path)

    failed, warned, total = [], 0, 0
    for skill_md in sorted(root.glob("*/SKILL.md")):
        total += 1
        res = validate_skill.validate(skill_md)
        warned += 1 if res.warns else 0
        if res.fails:
            failed.append(skill_md.parent.name)
            print("FAIL %s" % skill_md.parent.name)
            for m in res.fails:
                print("     - " + m)
        elif not args.quiet:
            print("PASS %s%s" % (skill_md.parent.name, " (%d warn)" % len(res.warns) if res.warns else ""))

    archives = [p for p in root.rglob("*") if p.is_dir() and p.name.lower() == "archive"
                and any(p.rglob("SKILL.md"))]
    for p in archives:
        print("FAIL archive folder with retired skills inside the skills tree (still loads): %s" % p)

    print("\n%d skills: %d PASS, %d FAIL, %d with warnings; %d archive folder(s)"
          % (total, total - len(failed), len(failed), warned, len(archives)))
    if total == 0:
        print("FAIL: no skills found under %s" % root)
        return 1
    return 1 if failed or archives else 0


if __name__ == "__main__":
    sys.exit(main())
