"""test_loop_scripts.py -- self-test for compare_views.py, stop_check.py and
log_iteration.py. Takes no arguments.

Builds a synthetic spec (two views, a six-entry rubric) in a fresh
tempfile.mkdtemp() directory, generates synthetic reference and render PNGs
(including one deliberately flat render), drives all three scripts via
subprocess exactly as the skill's per-iteration ritual does, and asserts:

  - every compare_views output file exists for every tag
  - the deliberately flat render is flagged suspect_blank
  - LOOP_LOG.md ends up with four "## iterNN" sections
  - re-logging an already-logged tag is refused with exit code 2
  - comparing a tag with no render files is refused with exit code 2
  - a hand-built stall sequence (min stuck at 2, total flat, for three
    iterations after first reaching 2) yields decision=stop reason=STALLED
  - a hand-built sequence where total improves while the minimum stays flat
    yields decision=continue (this is the case the minimum-only rule used
    to get wrong)

Run directly: python test_loop_scripts.py
Exit code 0 if every assertion passes, 1 otherwise.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

SCRIPTS_DIR = Path(__file__).resolve().parent
RENDER_SIZE = [240, 120]

RESULTS = []


def check(description, condition):
    status = "PASS" if condition else "FAIL"
    print("[{0}] {1}".format(status, description))
    RESULTS.append(bool(condition))


def run_script(name, args):
    cmd = [sys.executable, str(SCRIPTS_DIR / name)] + args
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def make_ref_image(path, size, rects):
    img = Image.new("RGB", size, (10, 10, 10))
    draw = ImageDraw.Draw(img)
    for box, grey in rects:
        draw.rectangle(box, fill=(grey, grey, grey))
    img.save(path)


def make_shifted_render(path, size, shift, rects):
    img = Image.new("RGB", size, (10, 10, 10))
    draw = ImageDraw.Draw(img)
    for (x0, y0, x1, y1), grey in rects:
        draw.rectangle((x0 + shift, y0, x1 + shift, y1), fill=(grey, grey, grey))
    img.save(path)


def make_flat_render(path, size, grey=64):
    img = Image.new("RGB", size, (grey, grey, grey))
    img.save(path)


def build_spec(working_folder):
    reference_dir = working_folder / "refs"
    spec = {
        "name": "selftest_loop",
        "working_folder": str(working_folder).replace("\\", "/"),
        "dcc": "blender",
        "reference_dir": str(reference_dir).replace("\\", "/"),
        "render_size": RENDER_SIZE,
        "views": [
            {"name": "hero", "camera": "CAM_hero", "reference": "hero.png", "crop": None, "notes": "wide view"},
            {
                "name": "detail",
                "camera": "CAM_detail",
                "reference": "detail.png",
                "crop": [0, 0, 200, 120],
                "notes": "cropped tile",
            },
        ],
        "rubric": [
            {"name": "composition", "desc": "framing matches"},
            {"name": "scale", "desc": "human scale holds"},
            {"name": "inventory", "desc": "elements present"},
            {"name": "lighting", "desc": "key direction matches"},
            {"name": "materials", "desc": "value and hue match"},
            {"name": "constraints", "desc": "nothing forbidden present"},
        ],
        "priority_order": ["composition", "scale", "inventory", "lighting", "materials", "detail"],
        "stop": {"pass_score": 4, "consecutive_passes": 2, "max_iterations": 10, "no_improvement_streak": 3},
        "constraints": ["no screens or projections"],
        "brief_file": str(working_folder / "SCENE_BRIEF.md").replace("\\", "/"),
    }
    return spec


def write_review(compare_dir, tag, hero_scores, detail_scores, gaps, next_step):
    review = {
        "tag": tag,
        "scores": {"hero": hero_scores, "detail": detail_scores},
        "gaps": gaps,
        "next": next_step,
    }
    with open(compare_dir / "{0}_review.json".format(tag), "w", encoding="utf-8") as fh:
        json.dump(review, fh, indent=2)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="loop_gauntlet_selftest_"))
    print("self-test working folder: {0}".format(tmp))

    working_folder = tmp / "loop"
    reference_dir = working_folder / "refs"
    renders_dir = working_folder / "renders"
    compare_dir = working_folder / "compare"
    for d in (reference_dir, renders_dir):
        d.mkdir(parents=True, exist_ok=True)

    spec = build_spec(working_folder)
    spec_path = tmp / "gauntlet_spec.json"
    with open(spec_path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)

    hero_rects = [((20, 20, 100, 90), 180), ((120, 30, 200, 80), 90)]
    detail_rects = [((10, 10, 120, 100), 200), ((140, 20, 220, 110), 60)]
    make_ref_image(reference_dir / "hero.png", RENDER_SIZE, hero_rects)
    # detail reference is intentionally larger than the crop box so the
    # [0,0,200,120] crop in the spec actually trims something.
    make_ref_image(reference_dir / "detail.png", (260, 140), detail_rects)

    tags = ["iter01", "iter02", "iter03", "iter04"]
    for i, tag in enumerate(tags):
        shift = i * 2
        make_shifted_render(renders_dir / "{0}_hero.png".format(tag), RENDER_SIZE, shift, hero_rects)
        make_shifted_render(renders_dir / "{0}_detail.png".format(tag), RENDER_SIZE, shift, detail_rects)

    # A deliberately flat render on its own tag, to prove suspect_blank fires
    # without disturbing the stall sequence above.
    make_shifted_render(renders_dir / "iterblank_hero.png".format(), RENDER_SIZE, 0, hero_rects)
    make_flat_render(renders_dir / "iterblank_detail.png", RENDER_SIZE)

    # 1. compare_views for each real iteration tag, via subprocess.
    for tag in tags + ["iterblank"]:
        code, out, err = run_script("compare_views.py", ["--spec", str(spec_path), "--tag", tag, "--metric"])
        check("compare_views succeeds for {0}".format(tag), code == 0)
        if code != 0:
            print("  stderr: {0}".format(err))

    # 2. every compare_views output file exists for every tag.
    all_outputs_exist = True
    for tag in tags + ["iterblank"]:
        for view in ("hero", "detail"):
            for suffix in (".png", ".jpg"):
                p = compare_dir / "{0}_{1}{2}".format(tag, view, suffix)
                if not p.exists():
                    all_outputs_exist = False
                    print("  missing expected output: {0}".format(p))
        if not (compare_dir / "{0}_contactsheet.jpg".format(tag)).exists():
            all_outputs_exist = False
        if not (compare_dir / "{0}_readback.json".format(tag)).exists():
            all_outputs_exist = False
    check("all compare_views outputs exist for every tag", all_outputs_exist)

    # 3. the deliberately flat render is flagged suspect_blank; the normal one is not.
    with open(compare_dir / "iterblank_readback.json", "r", encoding="utf-8") as fh:
        blank_readback = json.load(fh)
    by_view = {e["view"]: e for e in blank_readback}
    check("flat render flagged suspect_blank", by_view["detail"]["suspect_blank"] is True)
    check("normal render not flagged suspect_blank", by_view["hero"]["suspect_blank"] is False)
    check("edge_similarity present with --metric", "edge_similarity" in by_view["hero"])

    # 4. compare_views on a tag with no renders exits 2.
    code, out, err = run_script("compare_views.py", ["--spec", str(spec_path), "--tag", "itermissing"])
    check("compare_views exits 2 for missing renders", code == 2)

    # 5. review JSONs designed to STALL at iter04: min stuck at 2 for three
    #    iterations (02,03,04) after first reaching 2 at iter02, total flat
    #    across those same three iterations.
    write_review(
        compare_dir, "iter01",
        hero_scores=[3, 4, 4, 4, 4, 4], detail_scores=[4, 4, 4, 4, 4, 4],
        gaps=["composition slightly off"], next_step="nudge hero camera",
    )
    write_review(
        compare_dir, "iter02",
        hero_scores=[2, 4, 4, 4, 4, 4], detail_scores=[4, 4, 4, 4, 4, 4],
        gaps=["composition regressed"], next_step="re-check hero anchor points",
    )
    write_review(
        compare_dir, "iter03",
        hero_scores=[2, 4, 4, 4, 4, 4], detail_scores=[4, 4, 4, 4, 4, 4],
        gaps=["composition still stuck"], next_step="try a different anchor",
    )
    write_review(
        compare_dir, "iter04",
        hero_scores=[2, 4, 4, 4, 4, 4], detail_scores=[4, 4, 4, 4, 4, 4],
        gaps=["composition unchanged for three iterations"], next_step="park this view, revisit plan",
    )

    # 6. log_iteration per tag.
    log_ok = True
    for tag in tags:
        code, out, err = run_script("log_iteration.py", ["--spec", str(spec_path), "--tag", tag])
        if code != 0:
            log_ok = False
            print("  log_iteration failed for {0}: {1}".format(tag, err))
    check("log_iteration succeeds for all four tags", log_ok)

    log_path = working_folder / "LOOP_LOG.md"
    log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    section_count = sum(1 for line in log_text.splitlines() if line.strip().startswith("## iter"))
    check("LOOP_LOG.md has four iteration sections", section_count == 4)

    # 7. re-logging an already-logged tag is refused.
    code, out, err = run_script("log_iteration.py", ["--spec", str(spec_path), "--tag", "iter01"])
    check("log_iteration refuses a duplicate tag with exit code 2", code == 2)

    # 8. log_iteration on a tag with no readback file is refused. Use a tag
    #    that does NOT match iter\d+ so it cannot leak into stop_check's
    #    trajectory (it never gets a readback file, so it must never log).
    write_review(compare_dir, "orphan01", [4, 4, 4, 4, 4, 4], [4, 4, 4, 4, 4, 4], [], "n/a")
    code, out, err = run_script("log_iteration.py", ["--spec", str(spec_path), "--tag", "orphan01"])
    check("log_iteration refuses a tag with no readback file (exit code 2)", code == 2)

    # 9. stop_check --json reports STALLED.
    code, out, err = run_script("stop_check.py", ["--spec", str(spec_path), "--json"])
    check("stop_check exits 0", code == 0)
    decision = {}
    try:
        json_start = out.index("{")
        decision = json.loads(out[json_start:])
    except (ValueError, json.JSONDecodeError):
        print("  could not parse stop_check --json output:\n{0}".format(out))
    check("stop_check decision is stop", decision.get("decision") == "stop")
    check("stop_check reason is STALLED", decision.get("reason") == "STALLED")
    check("stop_check streak is 3", decision.get("streak") == 3)

    # 10. unit check on stop_check.decide(): total improves while min stays
    #     flat must reset the streak and yield CONTINUE (the case a
    #     minimum-only rule gets wrong).
    sys.path.insert(0, str(SCRIPTS_DIR))
    import stop_check  # noqa: E402

    improving_total_iterations = [
        {
            "tag": "iterA", "num": 1,
            "scores": {"hero": [2, 3, 3, 3, 3, 3], "detail": [3, 3, 3, 3, 3, 3]},
            "global_min": 2, "total": 35,
        },
        {
            "tag": "iterB", "num": 2,
            "scores": {"hero": [2, 4, 4, 4, 4, 4], "detail": [4, 4, 4, 4, 4, 4]},
            "global_min": 2, "total": 46,
        },
    ]
    stop_cfg = spec["stop"]
    decision2, reason2, streak2, best_min2, best_total2 = stop_check.decide(improving_total_iterations, stop_cfg)
    check(
        "min flat + total improving yields CONTINUE with streak reset to 0",
        decision2 == "continue" and streak2 == 0,
    )

    failures = RESULTS.count(False)
    print("")
    print("{0}/{1} assertions passed".format(RESULTS.count(True), len(RESULTS)))
    if failures:
        print("SELF-TEST FAILED ({0} failure(s))".format(failures))
        sys.exit(1)
    print("SELF-TEST PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()
