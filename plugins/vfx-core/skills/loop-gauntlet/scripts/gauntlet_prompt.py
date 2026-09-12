"""Generate a paste-ready loop-gauntlet prompt from a spec file.

The spec (templates/gauntlet_spec.example.json) holds the contract the human
authored: references, matched views, rubric, priority order, stop rules and
constraints. This script turns it into the instructions a builder agent runs,
so the checks in the prompt are always the checks in the spec - never the
builder's own.

Usage:
  python gauntlet_prompt.py --spec D:/work/loop/gauntlet_spec.json --harness codex
  python gauntlet_prompt.py --spec ... --harness claude --out D:/work/loop/PROMPT.md
  python gauntlet_prompt.py --spec ... --scripts-dir D:/tools/loop-gauntlet/scripts

--harness   codex | claude | opencode  (default codex). Adds the harness rules.
--scripts-dir  where compare_views.py / log_iteration.py / stop_check.py live
            on the machine that runs the loop. Default: this file's folder.
            The effective value is printed and written into the prompt.
--out       write the prompt to this file (ASCII) instead of stdout only.

Optional spec fields (v1.1.0): "tools" - a list of strings naming the tools
the builder may use beyond the DCC (rendered as a section); "spend_cap_usd" -
a number that switches on the spend contract (zero-cost gate, balance
read-back, GEN_LEDGER.md, no real marks). Absent = round-1 prompt unchanged.

ASCII only. No paths are assumed; everything comes from the spec or flags.
"""
import argparse
import json
import sys
from pathlib import Path

HARNESS_RULES = {
    "codex": (
        "Work in the {dcc} session that is already open and connected through the "
        "{dcc} MCP server so the operator can watch the scene change; do not launch "
        "extra {dcc} instances (the policy hook refuses app launches anyway). {script_note} "
        "Keep those scripts ASCII-only with raw-string Windows paths. For any shell step use cmd.exe or "
        "python, not PowerShell. The reference images are attached to this message "
        "and also on disk at the paths below; re-open them with your image viewer "
        "whenever you need to. Infer intent from this brief and see the task through; "
        "if a question is genuinely blocking, ask it and keep working on everything "
        "that does not depend on the answer."
    ),
    "claude": (
        "You are running this loop yourself, now, in the live {dcc} session through "
        "the {dcc} MCP server so the operator can watch. Save a version increment "
        "after every completed iteration and before every render or heavy operation "
        "(house rule: {dcc} can hang under agent control). Use the scripts named below "
        "for comparison, logging and the stop decision; do not re-implement them."
    ),
    "opencode": (
        "Run this loop as a packaged workflow in the live {dcc} session through its "
        "MCP plugin. Shell steps go through python. Save increments before renders."
    ),
}


def load_spec(path):
    try:
        spec = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        sys.stderr.write("spec could not be read: %s (%s)\n" % (path, exc))
        sys.exit(2)
    for key in ("name", "working_folder", "dcc", "reference_dir", "render_size",
                "views", "rubric", "priority_order", "stop", "constraints"):
        if key not in spec:
            sys.stderr.write("spec is missing the '%s' field: %s\n" % (key, path))
            sys.exit(2)
    return spec


def read_brief(spec, spec_path):
    brief_file = spec.get("brief_file")
    if not brief_file:
        return "(no brief_file in the spec - describe the scene here before pasting)"
    p = Path(brief_file)
    if not p.is_absolute():
        p = Path(spec_path).parent / p
    if not p.exists():
        sys.stderr.write("brief_file not found: %s\n" % p)
        sys.exit(2)
    return p.read_text(encoding="utf-8").strip()


def fmt_path(p):
    return str(p).replace("/", "\\") if "\\" in str(p) or ":" in str(p) else str(p)


def build(spec, spec_path, harness, scripts_dir):
    dcc = spec["dcc"]
    if dcc.lower() == "houdini":
        script_note = ("Use Python (hou) scripts through the MCP execute tool for every "
                       "change; see reference/houdini_loop_patterns.md for scene layout, "
                       "camera and Karma render conventions.")
    else:
        script_note = ("Use bpy scripts through the MCP execute tool for every change; "
                       "see reference/blender_loop_patterns.md for the render-queue and "
                       "material patterns.")
    wf = spec["working_folder"]
    ref_dir = spec["reference_dir"]
    w, h = spec["render_size"]
    stop = spec["stop"]
    rubric = spec["rubric"]
    views = spec["views"]
    view_names = [v["name"] for v in views]
    lines = []
    add = lines.append

    add("You are building a scene in %s from reference images and you will keep "
        "iterating until renders from matched cameras agree with those references, "
        "or a stop rule below says stop. %s" % (dcc, HARNESS_RULES[harness].format(dcc=dcc, script_note=script_note)))
    add("")
    add("## What this is")
    add("")
    add(read_brief(spec, spec_path))
    add("")
    add("## The references")
    add("")
    add("Folder: %s" % fmt_path(ref_dir))
    add("")
    for v in views:
        crop = v.get("crop")
        crop_txt = (" (use only the tile at crop box %s of that file)" % crop) if crop else ""
        add("- %s -> view '%s', camera %s%s. %s" % (v["reference"], v["name"], v.get("camera", "CAM_" + v["name"]), crop_txt, v.get("notes", "")))
    add("")
    add("Only these files are references. Ignore soft artefacts where people were removed. "
        "Nothing else in the session (earlier renders, the viewport, other images) is a reference.")
    add("")
    add("## Where to work")
    add("")
    add("Working folder: %s" % fmt_path(wf))
    add("Create renders\\, compare\\ and scripts\\ inside it. Save the scene as a v001 file in "
        "the working folder and save a new increment after every completed iteration and "
        "before any render or heavy operation. Everything on a job share is copy-only for "
        "you: write new files inside the working folder, never delete, move or rename "
        "anything there, and never write into the reference folder.")
    add("")
    add("The loop helper scripts are at: %s" % fmt_path(scripts_dir))
    add("The spec they read is: %s" % fmt_path(spec_path))
    add("")
    add("## Ground rules for the build")
    add("")
    add("Real-world metres, Z up. One collection per zone plus CAMERAS and LIGHTS, and every "
        "object named for what it is. Before creating anything, read back what already "
        "exists so you never end up with auto-numbered duplicates; before re-running a "
        "creation script, check whether the objects are already there and update them "
        "instead. Derive dimensions from the human-scale anchors in the brief and write them "
        "down in SCENE_BRIEF.md before you model; if a reference implies something "
        "different, follow the reference and note the number you chose. Prefer clean "
        "parametric geometry that can be edited later. Blockout materials are simple "
        "shaders in the right value and hue family; refine them only after geometry and "
        "cameras match. Use the fast engine for loop renders and the hero engine only for "
        "the final pass.")
    add("")
    add("## Constraints (hard)")
    add("")
    for c in spec["constraints"]:
        add("- %s" % c)
    add("")
    # Optional round-2 fields: an explicit tool surface and a spend contract.
    # Absent fields render nothing, so a round-1 spec still produces the
    # round-1 prompt.
    tools = spec.get("tools") or []
    if tools:
        add("## Tools you may use beyond the DCC")
        add("")
        add("You are not limited to modelling by hand. Use any of the following when it "
            "gets a view closer to its reference, and say in the log which you used and "
            "why. Nothing else is in scope (no other services, no installs).")
        add("")
        for t in tools:
            add("- %s" % t)
        add("")
    cap = spec.get("spend_cap_usd")
    if cap is not None:
        add("## Spend contract")
        add("")
        add("Paid generation (partner-node or hosted-model calls) is allowed up to %s USD "
            "for this run in total. Before every paid call, state the purpose and the "
            "expected cost; run the zero-cost checks the tool offers first (workflow "
            "validation, a print of the exact graph, a balance read) and read the balance "
            "back afterwards. Keep GEN_LEDGER.md in the working folder: one line per "
            "generation with tool, model, purpose, cost, and the output path. A generation "
            "that is not in the ledger did not happen. When the cap is reached, stop "
            "generating and continue with what you have; never route around the cap "
            "through another tool. Generated content must not carry real team logos, "
            "wordmarks or sponsor marks: numbers, colours and silhouettes only."
            % cap)
        add("")
    add("## The loop")
    add("")
    add("Before planning every iteration, check %s for OPERATOR_NOTES.md and read it if "
        "present; the operator watching this run may drop a dated note in there at any time "
        "with a correction or a new priority, and it is also printed after every logged "
        "iteration. A note in that file overrides this brief where the two conflict."
        % fmt_path(Path(wf) / "OPERATOR_NOTES.md"))
    add("")
    add("Start by writing SCENE_BRIEF.md in the working folder: the plan with your chosen "
        "dimensions, the camera list (%s, each with the reference it matches), and the "
        "order you will build in. Then build the blockout in one pass, place the cameras "
        "with focal lengths and heights estimated from each reference, and enter the loop." % ", ".join("CAM_" + n for n in view_names))
    add("")
    add("Every iteration follows the same shape, tagged iter01, iter02, ...:")
    add("")
    add("1. Render every matched camera at %d x %d into renders\\<tag>_<view>.png." % (w, h))
    add("2. Run: python \"%s\" --spec \"%s\" --tag <tag>" % (fmt_path(Path(scripts_dir) / "compare_views.py"), fmt_path(spec_path)))
    add("   It writes compare\\<tag>_<view>.png (reference | 50 percent blend | render), a "
        "contact sheet, and compare\\<tag>_readback.json with the file read-back of every "
        "render. It exits 2 if a render is missing and flags a suspect-blank render; "
        "never score a flagged frame.")
    add("3. Open every comparison image with your image viewer and score it against the rubric "
        "below. Write compare\\<tag>_review.json: {\"tag\": \"<tag>\", \"scores\": {\"<view>\": "
        "[one integer 1-5 per criterion, in rubric order]}, \"gaps\": [\"three biggest gaps\"], "
        "\"next\": \"what you will change\"}.")
    add("4. Run: python \"%s\" --spec \"%s\" --tag <tag>" % (fmt_path(Path(scripts_dir) / "log_iteration.py"), fmt_path(spec_path)))
    add("   It appends the iteration to LOOP_LOG.md and prints the stop decision. It refuses "
        "a tag with no readback file: an iteration that does not end with render files "
        "you have actually read back and looked at does not count.")
    add("5. Make the changes, save an increment, and go again.")
    add("")
    add("Fix in priority order: %s. Do not polish later items while an earlier one still "
        "scores below %d." % (" > ".join(spec["priority_order"]), stop["pass_score"]))
    add("")
    add("Rubric, scored 1 to 5 per view, in this order:")
    add("")
    for i, r in enumerate(rubric, 1):
        add("%d. %s - %s" % (i, r["name"], r["desc"]))
    add("")
    floor = int(stop.get("min_iterations", 0) or 0)
    floor_txt = (" A stall cannot fire before iteration %d: the early iterations belong to "
                 "composition and scale, and the later tiers (inventory, lighting, materials) "
                 "must each get their own iterations before the loop may conclude it is stuck."
                 % floor) if floor else ""
    add("Stop when the script says stop: every view scores %d or better on every criterion "
        "for %d consecutive iterations (target met); or %d iterations are complete; or "
        "neither the lowest score nor the total has improved for %d consecutive iterations "
        "(stalled).%s When stalled, stop and tell me what is stuck and what you would need. "
        "Scores are your own judgement of the comparison image; a score that jumps without "
        "a visible change is a reason to look again. There is no numeric score: the "
        "comparison image is the judge."
        % (stop["pass_score"], stop["consecutive_passes"], stop["max_iterations"], stop["no_improvement_streak"], floor_txt))
    add("")
    add("## Finish")
    add("")
    add("When the loop stops, render all views once more with the SAME engine as the loop "
        "into renders\\final_<view>.png and compare them (tag final). Then, as a separate "
        "labelled pass, render the hero-engine versions (tag final_hero) - a renderer "
        "switch is a new variable, so report any regression rather than hiding it. Save the "
        "final increment and end LOOP_LOG.md with a short honest summary: what matches, "
        "what does not and why, the dimensions you settled on, and which objects to touch "
        "first if we continue. Report the same summary to me in plain prose, with the paths.")
    add("")
    add("If %s stops responding, do not kill it and do not start another instance; tell me. "
        "If an API call fails, test the tool with something simple you know works before "
        "concluding the connection is broken, because your own API guess is the more likely "
        "fault." % dcc)
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Generate a loop-gauntlet prompt from a spec file.")
    ap.add_argument("--spec", required=True, help="path to gauntlet_spec.json")
    ap.add_argument("--harness", choices=sorted(HARNESS_RULES), default="codex",
                    help="which agent harness will run the loop (default codex)")
    ap.add_argument("--scripts-dir", default=None,
                    help="folder holding compare_views.py / log_iteration.py / stop_check.py on the runner machine (default: this file's folder)")
    ap.add_argument("--out", default=None, help="write the prompt here as well as printing it")
    args = ap.parse_args()

    # absolute(), never resolve(): resolve() rewrites a mapped network drive
    # into its UNC form, which the runner's policy hook then refuses.
    spec_path = Path(args.spec).absolute()
    spec = load_spec(spec_path)
    scripts_dir = Path(args.scripts_dir).absolute() if args.scripts_dir else Path(__file__).absolute().parent
    for name in ("compare_views.py", "log_iteration.py", "stop_check.py"):
        if not (scripts_dir / name).exists():
            sys.stderr.write("warning: %s not found in scripts dir %s\n" % (name, scripts_dir))

    print("spec        : %s" % spec_path, file=sys.stderr)
    print("scripts dir : %s" % scripts_dir, file=sys.stderr)
    print("harness     : %s" % args.harness, file=sys.stderr)

    text = build(spec, spec_path, args.harness, scripts_dir)
    try:
        text.encode("ascii")
    except UnicodeEncodeError as exc:
        sys.stderr.write("prompt is not pure ASCII (check the brief and spec): %s\n" % exc)
        sys.exit(2)
    if args.out:
        Path(args.out).write_text(text, encoding="ascii")
        print("wrote        : %s (%d words)" % (args.out, len(text.split())), file=sys.stderr)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
