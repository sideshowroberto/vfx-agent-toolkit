"""log_iteration.py -- append one loop-gauntlet iteration to LOOP_LOG.md.

Reads compare/<tag>_review.json and compare/<tag>_readback.json (exit 2,
naming the missing file, if either is absent -- an iteration without a
readback file was never actually measured and must not be logged).
Refuses to append a tag that is already in LOOP_LOG.md (exit 2).

Creates LOOP_LOG.md with a header naming the spec and the rubric if the log
does not exist yet, then appends a section: a markdown score table (rows =
views, columns = rubric names), the readback list (path, bytes, modified,
pixels, SUSPECT BLANK flag), the gaps as bullets, the "next" line, and
finally the continue/stop decision. The decision is computed by importing
stop_check as a module and calling its compute() function -- the dual
stall rule lives in exactly one place, never copied here.

Usage:
    python log_iteration.py --spec gauntlet_spec.json --tag iter03

Flags:
    --spec PATH   path to the gauntlet spec JSON (required)
    --tag TAG     iteration tag, e.g. iter03 (required)
"""
import argparse
import json
import sys
from pathlib import Path

# stop_check.py lives next to this script -- import it as a module so the
# stop/continue decision is computed in exactly one place.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import stop_check  # noqa: E402


def load_spec(spec_path):
    if not spec_path.exists():
        print("ERROR: spec file not found: {0}".format(spec_path), file=sys.stderr)
        sys.exit(2)
    try:
        with open(spec_path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as exc:
        print("ERROR: spec file is not valid JSON: {0} ({1})".format(spec_path, exc), file=sys.stderr)
        sys.exit(2)


def validate_review(review, views, rubric, path):
    """Shape check only (views present, correct length, 1..5 ints) -- the
    stop/continue decision itself is stop_check's job, not this one."""
    for key in ("scores", "gaps", "next"):
        if key not in review:
            print("ERROR: malformed review file {0}: missing field '{1}'".format(path, key), file=sys.stderr)
            sys.exit(2)
    if not isinstance(review["scores"], dict):
        print("ERROR: malformed review file {0}: field 'scores' is not an object".format(path), file=sys.stderr)
        sys.exit(2)
    rubric_len = len(rubric)
    for view in views:
        vname = view["name"]
        if vname not in review["scores"]:
            print(
                "ERROR: malformed review file {0}: field 'scores.{1}' is missing".format(path, vname),
                file=sys.stderr,
            )
            sys.exit(2)
        row = review["scores"][vname]
        if not isinstance(row, list) or len(row) != rubric_len:
            print(
                "ERROR: malformed review file {0}: field 'scores.{1}' must have {2} ints, got {3}".format(
                    path, vname, rubric_len, row
                ),
                file=sys.stderr,
            )
            sys.exit(2)
        for i, s in enumerate(row):
            if not isinstance(s, int) or isinstance(s, bool) or not (1 <= s <= 5):
                print(
                    "ERROR: malformed review file {0}: field 'scores.{1}[{2}]' must be an int in 1..5, got {3!r}".format(
                        path, vname, i, s
                    ),
                    file=sys.stderr,
                )
                sys.exit(2)


def build_section(spec, tag, review, readback):
    views = spec["views"]
    rubric = spec["rubric"]
    lines = []
    lines.append("## {0}".format(tag))
    lines.append("")
    lines.append("| view | " + " | ".join(r["name"] for r in rubric) + " |")
    lines.append("|" + "---|" * (len(rubric) + 1))
    for view in views:
        vname = view["name"]
        row = review["scores"][vname]
        lines.append("| {0} | {1} |".format(vname, " | ".join(str(s) for s in row)))
    lines.append("")
    lines.append("### Readback")
    lines.append("")
    by_view = {entry.get("view"): entry for entry in readback}
    for view in views:
        vname = view["name"]
        entry = by_view.get(vname)
        if entry is None:
            lines.append("- **{0}**: no readback entry found".format(vname))
            continue
        w, h = entry.get("pixel_size", [0, 0])
        flag = " **SUSPECT BLANK**" if entry.get("suspect_blank") else ""
        lines.append(
            "- **{0}**: `{1}` -- {2} bytes, modified {3}, {4}x{5} px{6}".format(
                vname, entry.get("render_path"), entry.get("bytes"), entry.get("modified"), w, h, flag
            )
        )
    lines.append("")
    lines.append("### Gaps")
    lines.append("")
    for gap in review.get("gaps", []):
        lines.append("- {0}".format(gap))
    lines.append("")
    lines.append("**Next:** {0}".format(review.get("next", "")))
    lines.append("")
    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Append one loop-gauntlet iteration (review + readback) to LOOP_LOG.md."
    )
    parser.add_argument("--spec", required=True, help="path to the gauntlet spec JSON")
    parser.add_argument("--tag", required=True, help="iteration tag, e.g. iter03")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    spec = load_spec(spec_path)
    working_folder = Path(spec["working_folder"])
    compare_dir = working_folder / "compare"
    log_path = working_folder / "LOOP_LOG.md"

    print("working_folder: {0}".format(working_folder))
    print("log_path:       {0}".format(log_path))
    print("tag:            {0}".format(args.tag))

    review_path = compare_dir / "{0}_review.json".format(args.tag)
    readback_path = compare_dir / "{0}_readback.json".format(args.tag)
    missing = [p for p in (review_path, readback_path) if not p.exists()]
    if missing:
        print("ERROR: missing input file(s):", file=sys.stderr)
        for m in missing:
            print("  {0}".format(m), file=sys.stderr)
        sys.exit(2)

    try:
        with open(review_path, "r", encoding="utf-8") as fh:
            review = json.load(fh)
    except json.JSONDecodeError as exc:
        print("ERROR: review file is not valid JSON: {0} ({1})".format(review_path, exc), file=sys.stderr)
        sys.exit(2)
    try:
        with open(readback_path, "r", encoding="utf-8") as fh:
            readback = json.load(fh)
    except json.JSONDecodeError as exc:
        print("ERROR: readback file is not valid JSON: {0} ({1})".format(readback_path, exc), file=sys.stderr)
        sys.exit(2)

    validate_review(review, spec["views"], spec["rubric"], review_path)

    tag_heading = "## {0}".format(args.tag)
    if log_path.exists():
        existing_text = log_path.read_text(encoding="utf-8")
        if any(line.strip() == tag_heading for line in existing_text.splitlines()):
            print("ERROR: tag '{0}' is already logged in {1}".format(args.tag, log_path), file=sys.stderr)
            sys.exit(2)
    else:
        header = ["# Loop Gauntlet Log: {0}".format(spec.get("name", "")), "", "Rubric:", ""]
        for r in spec["rubric"]:
            header.append("- **{0}**: {1}".format(r["name"], r["desc"]))
        header.append("")
        header.append("---")
        header.append("")
        log_path.write_text("\n".join(header) + "\n", encoding="utf-8")

    section_lines = build_section(spec, args.tag, review, readback)

    # Decision logic lives in stop_check.py only -- call it, don't copy it.
    result = stop_check.compute(spec)
    decision_line = "**Decision:** {0} -- {1} (streak={2})".format(
        result["decision"].upper(), result["reason"], result["streak"]
    )
    section_lines.append(decision_line)
    section_lines.append("")
    section_lines.append("---")
    section_lines.append("")

    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(section_lines) + "\n")

    print("appended to {0}:".format(log_path))
    for line in section_lines:
        print(line)

    sys.exit(0)


if __name__ == "__main__":
    main()
