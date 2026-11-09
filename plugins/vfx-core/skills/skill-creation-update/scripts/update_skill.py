#!/usr/bin/env python
"""Fix or bump a skill's frontmatter to SKILL_AND_AGENT_STANDARD.md; the body is never touched.

  --migrate         move retired / undocumented top-level keys under metadata:
                    (triggers -> when_to_use when that is empty), and join a folded or
                    multi-line description / when_to_use into ONE line
  --version X.Y.Z   set metadata.version and metadata.updated (lower than the current one needs --force;
                    the same version is a no-op)

Idempotent: a second run reports "no change". Frontmatter comments are not preserved
(the run says so when there were any). Runs the validator afterwards.

Usage:
    python update_skill.py <skill-name | skill-dir | SKILL.md> [--migrate] [--version X.Y.Z]
        [--force] [--dry-run] [--skills-path DIR]
ASCII only.
"""
import argparse
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate_skill  # noqa: E402

META_NAME = {"last_updated": "updated"}


def split(text):
    """Return (frontmatter_text, body_text) keeping the body byte-exact."""
    if not text.startswith("---"):
        sys.exit("[FAIL] no frontmatter block")
    m = re.search(r"\r?\n---[ \t]*(\r?\n|$)", text[3:])
    if not m:
        sys.exit("[FAIL] frontmatter is not closed with ---")
    end = 3 + m.start()
    return text[3:end].lstrip("\r\n"), text[3 + m.end():]


def semver(v):
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", str(v).strip())
    return tuple(int(x) for x in m.groups()) if m else None


def migrate(data, notes):
    meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    for key in list(data.keys()):
        if key in validate_skill.ALLOWED_KEYS:
            continue
        value = data.pop(key)
        if key == "triggers" and not data.get("when_to_use"):
            items = value if isinstance(value, list) else [value]
            data["when_to_use"] = "Triggers on " + ", ".join('"%s"' % str(t).strip() for t in items) + "."
            notes.append("triggers -> when_to_use")
            continue
        meta[META_NAME.get(key, key)] = value
        notes.append("%s -> metadata.%s" % (key, META_NAME.get(key, key)))
    for key in validate_skill.SINGLE_LINE_KEYS:
        if isinstance(data.get(key), str):
            joined = " ".join(data[key].split())
            if joined != data[key]:
                data[key] = joined
                notes.append("%s joined to one line" % key)
    if meta:
        data.pop("metadata", None)
        data["metadata"] = meta


def main():
    ap = argparse.ArgumentParser(description="Migrate or bump a skill's frontmatter")
    ap.add_argument("skill", help="skill name, skill folder, or SKILL.md path")
    ap.add_argument("--migrate", action="store_true")
    ap.add_argument("--version")
    ap.add_argument("--force", action="store_true", help="allow a version that is not higher")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skills-path", default=str(HERE.parents[1]))
    args = ap.parse_args()
    if not (args.migrate or args.version):
        ap.error("nothing to do: pass --migrate and/or --version")

    import yaml
    skill_md = validate_skill.resolve_skill(args.skill, args.skills_path)
    if skill_md is None:
        print("[FAIL] skill not found: %s" % args.skill)
        return 1
    text = skill_md.read_bytes().decode("utf-8")
    fm_text, body = split(text)
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        print("[FAIL] frontmatter is not valid YAML - fix it by hand first: %s" % str(exc).splitlines()[0])
        return 1
    notes = []
    if args.migrate:
        migrate(data, notes)
    if args.version:
        new = semver(args.version)
        if new is None:
            print("[FAIL] --version must be X.Y.Z")
            return 1
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        old = semver(meta.get("version", "0.0.0"))
        if old and new < old and not args.force:
            print("[FAIL] %s is lower than metadata.version %s (use --force)" % (args.version, meta.get("version")))
            return 1
        if str(meta.get("version")) != args.version:
            meta["version"] = args.version
            meta["updated"] = date.today()
            notes.append("metadata.version = %s" % args.version)
        data.pop("metadata", None)
        data["metadata"] = meta

    new_fm = yaml.safe_dump(data, sort_keys=False, width=100000, default_flow_style=False, allow_unicode=False)
    if not notes:
        print("[OK] no change: %s" % skill_md)
        return 0
    for n in notes:
        print("  change: " + n)
    if re.search(r"(?m)^\s*#", fm_text):
        print("  note: frontmatter comments were dropped")
    out = "---\n" + new_fm + "---\n" + body
    if args.dry_run:
        print(out[: len(new_fm) + 8])
        return 0
    skill_md.write_bytes(out.encode("utf-8"))
    res = validate_skill.validate(skill_md)
    for m in res.warns + res.fails:
        print("  " + m)
    print("[OK] wrote %s; validator %s" % (skill_md, "FAIL" if res.fails else "PASS"))
    return 1 if res.fails else 0


if __name__ == "__main__":
    sys.exit(main())
