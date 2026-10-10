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

Wave-2 additions (observations 0047, 0060, 0061, 0066, 0120):
  - gauntlet_prompt: the up axis and unit scale line is DCC-aware (blender +Z
    m, houdini +Y m, unreal +Z cm), a spec "scene" block overrides it, an
    unknown DCC with no block says the convention must be stated in the spec
    and an invalid axis is refused
  - gauntlet_prompt: a numbered "Read <absolute path>/reference/<dcc>_loop_
    patterns.md before iteration one" step; the path is absolute, exists and
    follows --scripts-dir
  - gauntlet_prompt: the Codex launch rule is conditioned on the sandbox mode
  - compare_views: ref_aspect_mismatch true/false (plus both aspects) in the
    readback, and an aspect line per view at startup
  - stop_check: a re-run tag such as iter06b is accepted, ordered after
    iter06, supersedes it in the decision, and an unmatched iter* review
    file is reported instead of ignored
  - log_iteration still accepts a readback written before the new keys

Run directly: python test_loop_scripts.py
Exit code 0 if every assertion passes, 1 otherwise.
"""
import copy
import json
import os
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


def gen_prompt(tmp, spec, label, harness="codex", extra=()):
    """Write spec to tmp/<label>.json and run gauntlet_prompt.py on it."""
    path = tmp / "{0}.json".format(label)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
    return run_script("gauntlet_prompt.py", ["--spec", str(path), "--harness", harness] + list(extra))


def read_step_path(prompt):
    """The path named by the numbered 'Read <path> before iteration one' step, or None."""
    for line in prompt.splitlines():
        if line.startswith("1. Read ") and " before iteration one." in line:
            return line[len("1. Read "):line.index(" before iteration one.")]
    return None


def all_pass_scores(rubric_len, value=5):
    return [value] * rubric_len


def wave2_prompt_checks(tmp, base_spec):
    """gauntlet_prompt.py: scene convention, absolute reference step, launch rule."""
    import gauntlet_prompt  # noqa: E402

    def variant(dcc, scene=None):
        s = copy.deepcopy(base_spec)
        s["dcc"] = dcc
        if scene is not None:
            s["scene"] = scene
        return s

    # Scene convention (observation 0060): DCC defaults, then the spec override.
    code, blender, err = gen_prompt(tmp, variant("blender"), "p_blender")
    check("gauntlet_prompt succeeds for blender", code == 0)
    check("blender default is +Z up, XY floors, metres",
          "+Z is up" in blender and "XY plane" in blender and "1 unit = 1 metre" in blender)
    check("old hardcoded 'Z up' line is gone", "Real-world metres, Z up." not in blender)
    code, houdini, err = gen_prompt(tmp, variant("houdini"), "p_houdini")
    check("houdini default is +Y up, XZ floors, metres",
          code == 0 and "+Y is up" in houdini and "XZ plane" in houdini
          and "1 unit = 1 metre" in houdini and "+Z is up" not in houdini)
    code, unreal, err = gen_prompt(tmp, variant("unreal"), "p_unreal")
    check("unreal default is +Z up, centimetres",
          code == 0 and "+Z is up" in unreal and "1 unit = 1 centimetre" in unreal)
    code, over, err = gen_prompt(tmp, variant("houdini", {"up_axis": "+Z", "units": "cm"}), "p_override")
    check("spec scene block overrides the DCC default",
          code == 0 and "+Z is up" in over and "1 unit = 1 centimetre" in over and "+Y is up" not in over)
    code, partial, err = gen_prompt(tmp, variant("houdini", {"up_axis": "Z"}), "p_partial")
    check("scene block with only up_axis keeps the DCC default units",
          code == 0 and "+Z is up" in partial and "1 unit = 1 metre" in partial)
    code, unknown, err = gen_prompt(tmp, variant("maya"), "p_maya")
    check("unknown DCC without a scene block says the axis must be stated in the spec",
          code == 0 and "must be stated in the spec" in unknown and "is up, floors lie" not in unknown)
    check("unknown DCC prints a warning on stderr", "warning" in err and "maya" in err)
    code, bad, err = gen_prompt(tmp, variant("blender", {"up_axis": "+X", "units": "m"}), "p_badaxis")
    check("an invalid scene.up_axis is refused with exit code 2", code == 2)

    # Absolute reference path (observation 0047).
    expected = {
        "blender": SCRIPTS_DIR.parent / "reference" / "blender_loop_patterns.md",
        "houdini": SCRIPTS_DIR.parent / "reference" / "houdini_loop_patterns.md",
    }
    for dcc, prompt in (("blender", blender), ("houdini", houdini)):
        named = read_step_path(prompt)
        ok = bool(named) and os.path.isabs(named) and os.path.exists(named) and os.path.samefile(named, str(expected[dcc]))
        check("{0} prompt has a numbered step naming the absolute, existing reference file".format(dcc), ok)
    check("the reference step comes before the SCENE_BRIEF step",
          "Before iteration one, in this order:" in blender
          and blender.index("1. Read ") < blender.index("2. Write SCENE_BRIEF.md"))
    check("no relative reference/ pointer is left in the prompt",
          "see reference/" not in blender and "see reference/" not in houdini)
    check("a DCC with no reference file emits no Read step and keeps the SCENE_BRIEF opener",
          read_step_path(unknown) is None and "Start by writing SCENE_BRIEF.md" in unknown)
    # The path follows --scripts-dir (the runner machine's copy of the skill).
    fake_skill = tmp / "runner_copy"
    for sub in ("scripts", "reference"):
        (fake_skill / sub).mkdir(parents=True, exist_ok=True)
    (fake_skill / "reference" / "blender_loop_patterns.md").write_text("# stub\n", encoding="ascii")
    for name in ("compare_views.py", "log_iteration.py", "stop_check.py"):
        (fake_skill / "scripts" / name).write_text("# stub\n", encoding="ascii")
    code, moved, err = gen_prompt(tmp, variant("blender"), "p_moved", extra=["--scripts-dir", str(fake_skill / "scripts")])
    named = read_step_path(moved)
    check("reference path follows --scripts-dir",
          code == 0 and bool(named) and os.path.isabs(named)
          and os.path.samefile(named, str(fake_skill / "reference" / "blender_loop_patterns.md")))

    # Codex launch rule, conditioned on the sandbox mode (observation 0120).
    check("codex prompt carries both branches of the launch rule",
          "sandboxed profile (-s read-only or workspace-write)" in blender
          and "unsandboxed profile" in blender and "call operator" in blender
          and "cmd /c breaks" in blender)
    check("codex prompt pins a headless launch to ONE direct shell line and never names the exe",
          "ONE direct shell line" in blender and "never name the blender executable" in blender
          and ".exe\"" not in blender)
    check("old blanket 'not PowerShell' rule is gone", "not PowerShell" not in blender)
    code, claude_prompt, err = gen_prompt(tmp, variant("blender"), "p_claude", harness="claude")
    check("claude prompt does not carry the codex launch rule",
          code == 0 and "unsandboxed profile" not in claude_prompt and "+Z is up" in claude_prompt)
    check("generated prompts are pure ASCII", all(
        all(ord(c) < 128 for c in p) for p in (blender, houdini, unreal, over, unknown, moved, claude_prompt)))
    # The module-level helper agrees with what the subprocess printed.
    check("fmt_path of the expected file equals the printed path (same spelling)",
          read_step_path(blender) is not None
          and os.path.normcase(read_step_path(blender)) == os.path.normcase(gauntlet_prompt.fmt_path(expected["blender"].absolute())))


def wave2_aspect_checks(compare_dir, compare_stdout):
    """compare_views.py: ref_aspect_mismatch (observation 0061)."""
    import compare_views  # noqa: E402

    with open(compare_dir / "iter01_readback.json", "r", encoding="utf-8") as fh:
        by_view = {e["view"]: e for e in json.load(fh)}
    check("readback carries ref_aspect, render_aspect and ref_aspect_mismatch for every view",
          all(k in e for e in by_view.values() for k in ("ref_aspect", "render_aspect", "ref_aspect_mismatch")))
    check("matching aspect (240x120 ref in 240x120) -> ref_aspect_mismatch false",
          by_view["hero"].get("ref_aspect_mismatch") is False and by_view["hero"].get("ref_aspect") == 2.0)
    check("mismatched aspect (200x120 crop in 240x120) -> ref_aspect_mismatch true",
          by_view["detail"].get("ref_aspect_mismatch") is True and by_view["detail"].get("ref_aspect") == 1.6667
          and by_view["detail"].get("render_aspect") == 2.0)
    out = compare_stdout["iter01"]
    check("startup prints one aspect line per view, flagging only the mismatch",
          "aspect hero: reference 2.0000 vs render_size 2.0000 -> ok" in out
          and "aspect detail: reference (cropped) 1.6667 vs render_size 2.0000 -> MISMATCH" in out)
    # Unit checks on the helper, including the real-world case from the observation.
    check("2752x1536 reference in a 1376x768 frame is not a mismatch",
          compare_views.aspect_info((2752, 1536), None, (1376, 768))[2] is False)
    check("2924x1296 reference in a 1376x768 frame is a mismatch",
          compare_views.aspect_info((2924, 1296), None, (1376, 768))[2] is True)
    check("a crop 0.8 percent off the frame aspect is inside the tolerance",
          compare_views.aspect_info((3000, 2000), (0, 0, 1820, 1024), (1376, 768))[2] is False)
    check("the crop box, not the file, sets the aspect",
          compare_views.aspect_info((2924, 1296), (0, 0, 1376, 768), (1376, 768))[2] is False)


def wave2_rerun_checks(tmp, base_spec):
    """stop_check.py re-run tags (observation 0066) and old-readback compatibility."""
    import stop_check  # noqa: E402

    rubric_len = len(base_spec["rubric"])
    ok = all_pass_scores(rubric_len, 5)
    mid = all_pass_scores(rubric_len, 3)
    bad = all_pass_scores(rubric_len, 2)

    # Scenario A: iteration 6 was burnt and re-run as iter06b. Without the
    # re-run rule iter06b is ignored and the last two iterations are
    # iter06 (bad) + iter07, so the target is NOT met; with it they are
    # iter06b + iter07, which both pass.
    folder_a = tmp / "rerun_a"
    compare_a = folder_a / "compare"
    compare_a.mkdir(parents=True)
    spec_a = copy.deepcopy(base_spec)
    spec_a["working_folder"] = str(folder_a).replace("\\", "/")
    spec_a_path = tmp / "spec_rerun_a.json"
    spec_a_path.write_text(json.dumps(spec_a), encoding="utf-8")
    for n in range(1, 6):
        write_review(compare_a, "iter{0:02d}".format(n), mid, mid, ["g"], "n")
    write_review(compare_a, "iter06", bad, bad, ["burnt render"], "re-run")
    write_review(compare_a, "iter06b", ok, ok, ["re-run"], "n")
    write_review(compare_a, "iter07", ok, ok, ["g"], "n")

    recs = stop_check.collect_reviews(compare_a, spec_a["views"], spec_a["rubric"])
    check("iter06b is accepted and ordered after iter06",
          [r["tag"] for r in recs] == ["iter01", "iter02", "iter03", "iter04", "iter05", "iter06", "iter06b", "iter07"])
    by_tag = {r["tag"]: r for r in recs}
    check("iter06b is a re-run of iteration 6 (num 6, suffix b) and iter06 is superseded by it",
          by_tag["iter06b"]["num"] == 6 and by_tag["iter06b"]["suffix"] == "b"
          and by_tag["iter06"]["superseded"] is True and by_tag["iter06"]["superseded_by"] == "iter06b"
          and by_tag["iter06b"]["superseded"] is False)
    code, out, err = run_script("stop_check.py", ["--spec", str(spec_a_path), "--json"])
    decision = {}
    try:
        decision = json.loads(out[out.index("{"):])
    except (ValueError, json.JSONDecodeError):
        print("  could not parse stop_check --json output:\n{0}".format(out))
    check("stop_check on a re-run folder exits 0", code == 0)
    check("the re-run (iter06b + iter07) meets the target; the burnt iter06 does not count",
          decision.get("decision") == "stop" and decision.get("reason") == "TARGET_MET")
    check("a re-run does not use up an iteration (7 iteration numbers, iter06 listed as superseded)",
          decision.get("iterations") == 7 and decision.get("superseded") == ["iter06"])
    code, out, err = run_script("stop_check.py", ["--spec", str(spec_a_path)])
    check("the human table still lists iter06 and marks it superseded",
          code == 0 and "iter06 " in out and "(superseded by iter06b)" in out and "iter06b" in out)

    # Scenario B: latest suffix wins across several re-runs; unmatched iter*
    # review files are reported; same-suffix duplicates are not re-runs.
    folder_b = tmp / "rerun_b"
    compare_b = folder_b / "compare"
    compare_b.mkdir(parents=True)
    spec_b = copy.deepcopy(base_spec)
    spec_b["working_folder"] = str(folder_b).replace("\\", "/")
    spec_b_path = tmp / "spec_rerun_b.json"
    spec_b_path.write_text(json.dumps(spec_b), encoding="utf-8")
    write_review(compare_b, "iter01", mid, mid, ["g"], "n")
    write_review(compare_b, "iter02", bad, bad, ["g"], "n")
    write_review(compare_b, "iter02a", mid, mid, ["g"], "n")
    write_review(compare_b, "iter02b", ok, ok, ["g"], "n")
    write_review(compare_b, "iter03", mid, mid, ["g"], "n")
    write_review(compare_b, "iter3", mid, mid, ["g"], "n")
    write_review(compare_b, "iter04bb", ok, ok, ["g"], "n")
    recs_b = stop_check.collect_reviews(compare_b, spec_b["views"], spec_b["rubric"])
    sup = {r["tag"]: r["superseded_by"] for r in recs_b if r["superseded"]}
    check("the latest suffix wins across several re-runs (iter02, iter02a -> iter02b)",
          sup == {"iter02": "iter02b", "iter02a": "iter02b"})
    check("same-suffix duplicates (iter03 and iter3) are both kept, neither superseded",
          {"iter03", "iter3"} <= {r["tag"] for r in recs_b if not r["superseded"]})
    code, out, err = run_script("stop_check.py", ["--spec", str(spec_b_path), "--json"])
    check("an unmatched iter* review file is reported on stderr, not ignored silently",
          code == 0 and "iter04bb_review.json" in err and "skipped" in err)

    # Old-format readback (written before the aspect keys existed) still logs.
    write_review(compare_a, "iter09", ok, ok, ["g"], "n")
    old_readback = [
        {"view": v["name"], "render_path": "x.png", "bytes": 1, "modified": "2026-01-01T00:00:00+00:00",
         "pixel_size": [240, 120], "unique_values": 20, "suspect_blank": False}
        for v in spec_a["views"]
    ]
    (compare_a / "iter09_readback.json").write_text(json.dumps(old_readback), encoding="utf-8")
    code, out, err = run_script("log_iteration.py", ["--spec", str(spec_a_path), "--tag", "iter09"])
    check("log_iteration accepts a readback without the aspect keys", code == 0)


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
    compare_stdout = {}
    for tag in tags + ["iterblank"]:
        code, out, err = run_script("compare_views.py", ["--spec", str(spec_path), "--tag", tag, "--metric"])
        compare_stdout[tag] = out
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

    # 11. Wave-2 additions: prompt generator, aspect flag, re-run tags.
    (working_folder / "SCENE_BRIEF.md").write_text("A test chamber with a table.\n", encoding="ascii")
    wave2_prompt_checks(tmp, spec)
    wave2_aspect_checks(compare_dir, compare_stdout)
    wave2_rerun_checks(tmp, spec)

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
