#!/usr/bin/env python
"""Two-way self-test for validate_skill.py, create_skill.py and update_skill.py.

Builds throwaway skills in a temp folder and runs the REAL command lines:
  - must PASS: clean skills, a long body (WARN only), create_skill.py output,
    an old-format skill after update_skill.py --migrate (and a 2nd run = no change)
  - must FAIL: folded / literal / continued descriptions (eval case sk2), retired and
    undocumented top-level keys, a YAML parse error, no frontmatter, a missing path,
    a non-ASCII script, '<' in a description
Every case checks the exit code AND a message substring, so a validator that fails
everything (or passes everything) cannot score full marks.

Usage: python selftest_validate.py      Exit 0 = all cases behaved. ASCII only.
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
GOOD_DESC = "Exports comp-ready Alembic from a scene. Use when a comp needs geo from Blender."


def skill(root, name, frontmatter, body="# x\n\nbody\n", extra=None):
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(("---\n" + frontmatter + "---\n" + body).encode("ascii"))
    for rel, data in (extra or {}).items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return d


def run(script, *args, cwd=None):
    p = subprocess.run([PY, str(HERE / script)] + [str(a) for a in args], cwd=cwd,
                       capture_output=True, text=True, encoding="ascii", errors="replace")
    return p.returncode, p.stdout + p.stderr


def main():
    tmp = Path(tempfile.mkdtemp(prefix="sk_selftest_"))
    cases = []  # (label, exit_expected, substring_expected, actual_exit, output)
    try:
        r = tmp / "skills"
        good = "name: %s\ndescription: " + GOOD_DESC + "\n"

        # ---- must PASS ----
        d = skill(r, "clean-one", good % "clean-one")
        cases.append(("clean skill", 0, "Overall: PASS") + run("validate_skill.py", d))
        d = skill(r, "clean-two", 'name: clean-two\ndescription: "Builds X: fast. Use when Y."\n'
                  'when_to_use: Triggers on "make x".\npaths: ["**/*.nk"]\n'
                  "metadata:\n  version: 1.2.0\n  updated: 2026-11-09\n")
        cases.append(("clean, quoted colon + metadata", 0, "Overall: PASS") + run("validate_skill.py", d))
        d = skill(r, "rel-path", good % "rel-path", body="# x\n\nReplace every `FILL:` line.\n")
        code, out = run("validate_skill.py", ".", cwd=d)
        clean = code == 0 and "differs from folder" not in out and "FILL" not in out
        cases.append(("'.' path + inline FILL: mention, no false WARN", 0, "Overall: PASS",
                      0 if clean else 1, out))
        d = skill(r, "long-body", good % "long-body", body="line\n" * 520)
        cases.append(("520-line body is WARN not FAIL", 0, "[WARN] SKILL.md body is 520 lines")
                     + run("validate_skill.py", d))
        code, out = run("create_skill.py", "made-by-create", "--description", GOOD_DESC,
                        "--when-to-use", "Triggers on 'abc export'.", "--reference", "--skills-path", r)
        cases.append(("create_skill.py output validates", 0, "Validator: PASS", code, out))
        code, out = run("validate_skill.py", r / "made-by-create")
        cases.append(("create_skill.py output, standalone run", 0, "Overall: PASS", code, out))
        cases.append(("...and it WARNs on unfilled placeholders", 0, "unfilled 'FILL:'", code, out))
        old = ("name: old-format\ndescription: >\n  Exports things for comp\n  and more. Use when needed.\n"
               "version: 1.3.2\nlast_updated: 2026-10-30\nstatus: production\ntriggers:\n  - abc export\n")
        d = skill(r, "old-format", old, body="\n# old\n\nbody stays\n")
        body_before = (d / "SKILL.md").read_bytes().split(b"\n---\n", 1)[1]
        cases.append(("old format fails before migrate", 1, "retired top-level key 'version'")
                     + run("validate_skill.py", d))
        cases.append(("update_skill --migrate fixes it", 0, "validator PASS") + run("update_skill.py", d, "--migrate"))
        cases.append(("migrated skill validates", 0, "Overall: PASS") + run("validate_skill.py", d))
        cases.append(("second --migrate is a no-op", 0, "no change") + run("update_skill.py", d, "--migrate"))
        body_after = (d / "SKILL.md").read_bytes().split(b"\n---\n", 1)[1]
        cases.append(("migrate left the body byte-identical", 0, "", 0 if body_before == body_after else 1, ""))
        cases.append(("--version bump", 0, "metadata.version = 1.4.0") + run("update_skill.py", d, "--version", "1.4.0"))
        cases.append(("--version lower is refused", 1, "lower than") + run("update_skill.py", d, "--version", "1.0.0"))

        # ---- must FAIL ----
        folded = "name: folded\ndescription: >\n  Exports comp geo.\n  Use when a comp needs geo.\n"
        d = skill(r, "folded", folded)
        try:
            import yaml
            parsed = yaml.safe_load(folded)
            ok = isinstance(parsed.get("description"), str)
        except Exception:
            ok = False
        cases.append(("instrument: folded fixture is VALID yaml", 0, "", 0 if ok else 1, ""))
        cases.append(("folded description: >", 1, "block scalar") + run("validate_skill.py", d))
        d = skill(r, "folded-strip", "name: folded-strip\ndescription: >-\n  Exports comp geo. Use when x.\n")
        cases.append(("folded description: >-", 1, "block scalar") + run("validate_skill.py", d))
        d = skill(r, "literal", "name: literal\ndescription: |\n  Exports comp geo. Use when x.\n")
        cases.append(("literal description: |", 1, "block scalar") + run("validate_skill.py", d))
        d = skill(r, "continued", "name: continued\ndescription: Exports comp geo.\n  Use when x.\n")
        cases.append(("plain scalar continued on next line", 1, "continues onto the next line")
                     + run("validate_skill.py", d))
        d = skill(r, "retired", good % "retired" + "version: 1.0.0\nlast_updated: 2026-11-01\nstatus: active\n")
        cases.append(("top-level version/last_updated/status", 1, "retired top-level key 'last_updated'")
                     + run("validate_skill.py", d))
        d = skill(r, "unknown-key", good % "unknown-key" + "owner: rob\n")
        cases.append(("undocumented top-level key", 1, "undocumented top-level key 'owner'")
                     + run("validate_skill.py", d))
        d = skill(r, "bad-yaml", "name: bad-yaml\ndescription: Exports geo. NOTE: needs Blender. Use when x.\n")
        cases.append(("unquoted ': ' is a YAML error", 1, "not valid YAML") + run("validate_skill.py", d))
        d = r / "no-front"
        d.mkdir()
        (d / "SKILL.md").write_bytes(b"# no frontmatter\n")
        cases.append(("no frontmatter", 1, "no frontmatter block") + run("validate_skill.py", d))
        cases.append(("missing path is FAIL, not 0/0 PASS", 1, "nothing was checked")
                     + run("validate_skill.py", r / "does-not-exist"))
        d = skill(r, "bad-script", good % "bad-script",
                  extra={"scripts/x.py": b"print('a \xe2\x80\x94 b')\n"})
        cases.append(("non-ASCII script", 1, "non-ASCII bytes") + run("validate_skill.py", d))
        d = skill(r, "angle", "name: angle\ndescription: Exports [x] for <shot>. Use when x.\n")
        cases.append(("'<' in description", 1, "contains '<' or '>'") + run("validate_skill.py", d))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    bad = 0
    for label, want, sub, got, out in cases:
        good_case = (got == want) and (sub in out)
        bad += 0 if good_case else 1
        print("%s  %-45s want exit %d, got %d%s" % ("ok  " if good_case else "BAD ", label, want, got,
              "" if good_case else "  [missing: %r]" % sub))
        if not good_case:
            print("      " + out.strip().replace("\n", "\n      "))
    print("\n%d/%d cases behaved" % (len(cases) - bad, len(cases)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
