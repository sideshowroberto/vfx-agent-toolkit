"""test_lighting_scripts.py -- offline self-test for scratch_luminance.py and
solve_light_mix.py. Takes no arguments, needs no renders and no network.

Builds SYNTHETIC images in a fresh temp directory (smooth linear "light group"
passes with and without a haze term, references and renders derived from a known
mix) and drives both scripts through subprocess exactly as the lighting ritual
does. It asserts:

  scratch_luminance
    - --help works
    - a known delta is reported (render 15 levels under the reference in one box)
      and that box fails a 12-level tolerance while the others pass
    - a box that passes by coincidence (same mean) but whose bright feature sits
      elsewhere FAILS on the brightest-1% centroid and on the patch feature check
    - a thin groove that is geometrically present but rendered with ~no contrast
      is reported "NOT VISIBLE" by a line feature
    - a flat render is flagged suspect_blank (exit 1)
    - a missing file / out-of-range box exit with code 2
  solve_light_mix
    - --help works
    - Lawson-Hanson NNLS: matches a known solution, never returns a negative
      weight, satisfies the KKT conditions, agrees with SciPy when installed
    - additivity: the sum of the isolation passes reproduces a synthetic all-on
      render (float and 8-bit PNG); a non-additive all-on render is caught (exit 1)
    - the solver recovers known multipliers (no haze; with haze twins and the
      haze multiplier; with a held --fix value; from an 8-bit PNG reference;
      from numeric per-box targets with --fit-space encoded)
    - verify mode: a render at the solved weights is predicted within tolerance,
      a render at wrong weights exits 1
    - an all-black pass is refused (exit 2)
  EXR round trip (SKIPPED, not failed, when the OpenEXR package is missing)

Run directly: python test_lighting_scripts.py
Exit code 0 if every assertion passes (skips are reported), 1 otherwise.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

import numpy as np
from PIL import Image

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

RESULTS = []
SKIPS = []
W, H = 96, 54
TRUE_W = {"sun": 0.7, "sky": 1.8, "fixed": 1.0}
TRUE_K = 1.4
TINT = {"sun": (1.0, 0.85, 0.6), "sky": (0.7, 0.85, 1.0), "fixed": (1.0, 0.9, 0.8)}


def check(description, condition):
    status = "PASS" if condition else "FAIL"
    print("[{0}] {1}".format(status, description))
    RESULTS.append(bool(condition))


def skip(description, why):
    print("[SKIP] {0} ({1})".format(description, why))
    SKIPS.append(description)


def run_script(name, args):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run([sys.executable, str(SCRIPTS_DIR / name)] + [str(a) for a in args],
                          capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


# ---- synthetic scene (test-local colour maths, independent of the scripts) ----

YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)


def blob(cx, cy, sx, sy):
    return np.exp(-(((XX - cx) / sx) ** 2 + ((YY - cy) / sy) ** 2) / 2.0)


def tinted(lum, tint):
    return (lum[..., None] * np.array(tint)[None, None, :]).astype(np.float32)


BASE = {
    "sun": tinted(6.0 * blob(25, 15, 10, 8) + 0.02, TINT["sun"]),
    "sky": tinted(0.05 + 0.10 * (1.0 - YY / H), TINT["sky"]),
    "fixed": tinted(0.5 * blob(72, 40, 9, 7) + 0.01, TINT["fixed"]),
}
HAZE = {
    "sun": tinted(0.8 * blob(40, 20, 22, 12), TINT["sun"]),
    "sky": tinted(0.03 * (0.5 + XX / W), TINT["sky"]),
    "fixed": tinted(0.10 * blob(60, 30, 25, 14), TINT["fixed"]),
}


def enc(x):
    x = np.clip(x, 0.0, 1.0)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1.0 / 2.4) - 0.055)


def mix_true(weights, k=None, hazed=False):
    tot = 0.0
    for g, base in BASE.items():
        p = base + (k * HAZE[g] if (hazed and k is not None) else 0.0)
        tot = tot + weights[g] * p
    return tot


def save_png(path, lin):
    Image.fromarray((enc(lin) * 255.0 + 0.5).astype(np.uint8)).save(str(path))


def enc_luma_mean(lin, box):
    x0, y0, x1, y1 = box
    e = enc(lin[y0:y1, x0:x1]) * 255.0
    return float((e[..., 0] * 0.299 + e[..., 1] * 0.587 + e[..., 2] * 0.114).mean())


def write_grid_boxes(path, cols=3, rows=3):
    boxes = {}
    for r in range(rows):
        for c in range(cols):
            boxes["r%dc%d" % (r, c)] = [c / float(cols), r / float(rows), (c + 1) / float(cols), (r + 1) / float(rows)]
    Path(path).write_text(json.dumps({"boxes": boxes}))
    return boxes


def pass_args(d, clear=False):
    out = []
    for g in BASE:
        out += ["--pass", "{0}={1}".format(g, d / "{0}.npy".format(g))]
        if clear:
            out += ["--clear", "{0}={1}".format(g, d / "{0}_clear.npy".format(g))]
    return out


def load_json(path):
    return json.loads(Path(path).read_text())


def rel_err(a, b):
    return abs(a - b) / max(abs(b), 1e-12)


# ---- tests ----

def test_helps():
    for name in ("scratch_luminance.py", "solve_light_mix.py"):
        code, out, err = run_script(name, ["--help"])
        check("{0} --help exits 0 and prints usage".format(name), code == 0 and "usage" in out.lower())


def test_nnls():
    import solve_light_mix as slm
    rng = np.random.RandomState(7)
    A = rng.rand(30, 4) + 0.1
    x_true = np.array([1.5, 0.0, 2.0, 0.0])
    x = slm.lawson_hanson_nnls(A, A @ x_true)
    check("NNLS recovers a known sparse non-negative solution (max err < 1e-8)", np.abs(x - x_true).max() < 1e-8)
    b = A @ np.array([2.0, -1.5, 1.0, 0.5])               # unconstrained solution has a negative entry
    unc = np.linalg.lstsq(A, b, rcond=None)[0]
    x = slm.lawson_hanson_nnls(A, b)
    check("NNLS never returns a negative weight where least squares would", unc.min() < 0 and x.min() >= 0.0)
    grad = A.T @ (b - A @ x)
    check("NNLS satisfies KKT (grad <= 1e-8 where x = 0, ~0 where x > 0)",
          (grad[x == 0] <= 1e-8).all() and np.abs(grad[x > 0]).max() < 1e-8)
    badly_scaled = A * np.array([1e3, 1.0, 1e-3, 1.0])
    xs = slm.lawson_hanson_nnls(badly_scaled, badly_scaled @ x_true)
    check("NNLS copes with columns 6 orders of magnitude apart", np.abs(badly_scaled @ xs - badly_scaled @ x_true).max() < 1e-6)
    try:
        from scipy.optimize import nnls
        xr = nnls(A, b)[0]
        check("NNLS agrees with scipy.optimize.nnls", np.abs(x - xr).max() < 1e-7)
    except ImportError:
        skip("NNLS vs scipy.optimize.nnls", "scipy not installed")


def make_scene(d, clear):
    for g in BASE:
        np.save(str(d / "{0}.npy".format(g)), (BASE[g] + HAZE[g]) if clear else BASE[g])
        if clear:
            np.save(str(d / "{0}_clear.npy".format(g)), BASE[g])


def test_additivity(d):
    make_scene(d, False)
    write_grid_boxes(d / "boxes.json")
    ones = {g: 1.0 for g in BASE}
    allon = mix_true(ones)
    np.save(str(d / "allon.npy"), allon.astype(np.float32))
    save_png(d / "allon.png", allon)
    ref_png = d / "ref_add.png"
    save_png(ref_png, mix_true(TRUE_W))
    common = pass_args(d) + ["--reference", ref_png, "--boxes", d / "boxes.json"]
    code, out, err = run_script("solve_light_mix.py", common + ["--all-on", d / "allon.npy", "--out", d / "add_npy.json"])
    r = load_json(d / "add_npy.json")
    check("additivity holds for synthetic passes vs a float all-on render (max box diff < 0.05 luma)",
          code == 0 and r["additivity"]["pass"] and r["additivity"]["max_abs_diff"] < 0.05)
    code, out, err = run_script("solve_light_mix.py", common + ["--all-on", d / "allon.png", "--out", d / "add_png.json"])
    r = load_json(d / "add_png.json")
    check("additivity holds against an 8-bit PNG all-on render (max box diff < 1.0 luma)",
          code == 0 and r["additivity"]["pass"] and r["additivity"]["max_abs_diff"] < 1.0)
    w2 = {"sun": 0.5, "sky": 2.0, "fixed": 1.0}
    np.save(str(d / "allon_w.npy"), mix_true(w2).astype(np.float32))
    code, out, err = run_script("solve_light_mix.py", common + ["--all-on", d / "allon_w.npy", "--all-on-weights", "sun=0.5",
                                                                  "--all-on-weights", "sky=2.0", "--out", d / "add_w.json"])
    check("additivity respects --all-on-weights", code == 0 and load_json(d / "add_w.json")["additivity"]["pass"])
    broken = mix_true(ones) + 0.3 * BASE["sun"]            # a non-additive all-on (e.g. stray extra light / bounce)
    np.save(str(d / "allon_bad.npy"), broken.astype(np.float32))
    code, out, err = run_script("solve_light_mix.py", common + ["--all-on", d / "allon_bad.npy", "--out", d / "add_bad.json"])
    r = load_json(d / "add_bad.json")
    check("a non-additive all-on render exits 1 and marks the solve untrusted",
          code == 1 and r["additivity"]["pass"] is False and r["trusted"] is False and r["additivity"]["max_abs_diff"] > 2.0)


def test_solver_no_haze(d):
    ref = mix_true(TRUE_W)
    np.save(str(d / "ref_exact.npy"), ref.astype(np.float32))
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--reference", d / "ref_exact.npy", "--boxes", d / "boxes.json",
                                                                       "--out", d / "solve_exact.json"])
    r = load_json(d / "solve_exact.json")
    w = r["fit"]["weights"]
    check("solver recovers known multipliers from an exact linear reference (no haze, < 0.1 percent)",
          code == 0 and all(rel_err(w[g], TRUE_W[g]) < 1e-3 for g in TRUE_W))
    check("exact reference predicts every box within 0.5 luma", r["summary"]["max_abs_residual"] < 0.5)
    check("result JSON lists contribution of each group per box and per-pass diagnostics",
          set(r["predicted"][0]["contribution_luma"]) == set(TRUE_W) and "brightest_1pct" in r["passes"]["sun"])
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--reference", d / "ref_exact.npy", "--boxes", d / "boxes.json",
                                                                       "--fix", "sky=1.8", "--out", d / "solve_fix.json"])
    w = load_json(d / "solve_fix.json")["fit"]["weights"]
    check("--fix holds a value and the others still converge", code == 0 and w["sky"] == 1.8 and
          rel_err(w["sun"], 0.7) < 1e-3 and rel_err(w["fixed"], 1.0) < 1e-3)
    save_png(d / "ref_srgb.png", ref)
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--reference", d / "ref_srgb.png", "--boxes", d / "boxes.json",
                                                                       "--fit-space", "encoded", "--out", d / "solve_png.json"])
    r = load_json(d / "solve_png.json")
    w = r["fit"]["weights"]
    refine = r["fit"]["fit_space"]["refine"]
    check("solver recovers multipliers from an 8-bit PNG reference within 5 percent (encoded polish)",
          code == 0 and all(rel_err(w[g], TRUE_W[g]) < 0.05 for g in TRUE_W))
    check("encoded polish never raises the cost and the png fit predicts boxes within 3 luma",
          refine["end_cost"] <= refine["start_cost"] + 1e-9 and r["summary"]["max_abs_residual"] < 3.0)
    boxes = write_grid_boxes(d / "boxes_tmp.json")
    spec = {"boxes": {n: {"box": b, "target": enc_luma_mean(ref, (int(b[0] * W), int(b[1] * H), int(b[2] * W), int(b[3] * H)))}
                      for n, b in boxes.items()}}
    (d / "boxes_targets.json").write_text(json.dumps(spec))
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--boxes", d / "boxes_targets.json", "--global-weight", "0",
                                                                       "--fit-space", "encoded", "--out", d / "solve_targets.json"])
    r = load_json(d / "solve_targets.json")
    w = r["fit"]["weights"]
    start = r["fit"]["fit_space"]["refine"]["start_cost"]
    check("solver recovers multipliers from numeric per-box targets within 1 percent (no reference image)",
          code == 0 and all(rel_err(w[g], TRUE_W[g]) < 0.01 for g in TRUE_W))
    check("encoded polish actually moves off the linear start (finite-difference steps are not flattened)",
          start > 1e-6 and r["fit"]["fit_space"]["refine"]["accepted_steps"] >= 1)
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--reference", d / "ref_exact.npy", "--boxes", d / "boxes.json",
                                                                       "--per-channel", "--out", d / "solve_pc.json"])
    w = load_json(d / "solve_pc.json")["fit"]["weights"]
    check("--per-channel (R,G,B rows) recovers the same multipliers", code == 0 and all(rel_err(w[g], TRUE_W[g]) < 1e-3 for g in TRUE_W))


def test_solver_haze(d):
    make_scene(d, True)
    ref = mix_true(TRUE_W, TRUE_K, hazed=True)
    np.save(str(d / "ref_haze.npy"), ref.astype(np.float32))
    code, out, err = run_script("solve_light_mix.py", pass_args(d, clear=True) + [
        "--reference", d / "ref_haze.npy", "--boxes", d / "boxes.json", "--out", d / "solve_haze.json"])
    r = load_json(d / "solve_haze.json")
    w, k = r["fit"]["weights"], r["fit"]["haze_k"]
    check("solver recovers weights (< 1 percent) and haze multiplier (< 0.03) with haze-free twins",
          code == 0 and all(rel_err(w[g], TRUE_W[g]) < 0.01 for g in TRUE_W) and abs(k - TRUE_K) < 0.03)
    # a verification render at the solved weights is predicted; the same render at wrong weights is not
    solved = {g: r["fit"]["weights"][g] for g in TRUE_W}
    render_ok = mix_true(solved, k, hazed=True)
    save_png(d / "verify_ok.png", render_ok)
    code, out, err = run_script("solve_light_mix.py", pass_args(d, clear=True) + [
        "--boxes", d / "boxes.json", "--verify", d / "verify_ok.png", "--weights-from", d / "solve_haze.json",
        "--out", d / "verify_ok.json"])
    v = load_json(d / "verify_ok.json")["verification"]
    check("verify mode: a render at the solved weights is predicted within 1.5 luma (exit 0)",
          code == 0 and v["pass"] and v["max_abs_diff"] < 1.5)
    wrong = dict(solved)
    wrong["sun"] *= 1.35
    save_png(d / "verify_bad.png", mix_true(wrong, k, hazed=True))
    code, out, err = run_script("solve_light_mix.py", pass_args(d, clear=True) + [
        "--verify", d / "verify_bad.png", "--weights-from", d / "solve_haze.json", "--out", d / "verify_bad.json"])
    v = load_json(d / "verify_bad.json")["verification"]
    check("verify mode: a render at wrong weights exits 1 and reports the error (boxes read from the solve JSON)",
          code == 1 and (not v["pass"]) and v["max_abs_diff"] > 4.0 and len(v["boxes"]) == 9)


def test_solver_inputs(d):
    np.save(str(d / "black.npy"), np.zeros((H, W, 3), dtype=np.float32))
    args = ["--pass", "sun={0}".format(d / "black.npy"), "--pass", "sky={0}".format(d / "sky.npy"),
            "--reference", d / "ref_exact.npy", "--out", d / "black.json"]
    code, out, err = run_script("solve_light_mix.py", args)
    check("an all-black pass is refused with exit 2 naming the group", code == 2 and "sun" in err and "black" in err)
    code, out, err = run_script("solve_light_mix.py", ["--out", d / "none.json"])
    check("no --pass exits 2", code == 2)
    code, out, err = run_script("solve_light_mix.py", pass_args(d) + ["--clear", "sun={0}".format(d / "sun.npy"), "--reference", d / "ref_exact.npy"])
    check("--clear covering only some groups exits 2", code == 2)


def make_flat(path, size, grey):
    Image.new("RGB", size, (grey, grey, grey)).save(str(path))


def textured(base, size=(200, 100)):
    """Constant-grey regions plus a vertical ramp (0..14 levels) so the frame is not 'flat': the
    blank-frame gate (fewer than 8 distinct grey levels) must not trip on a valid test image."""
    w, h = size
    arr = np.zeros((h, w, 3), dtype=np.float64) + np.linspace(0, 14, h)[:, None, None]
    return arr + base


def save_u8(path, arr):
    Image.fromarray(np.clip(arr + 0.5, 0, 255).astype(np.uint8)).save(str(path))


def test_scratch_luminance(d):
    size = (200, 100)
    # reference: left half 100, right half 140; render: left 100, right 125 (right box is 15 under)
    ref = np.zeros((100, 200, 1)) + 100.0
    ref[:, 100:] = 140.0
    ren = np.zeros((100, 200, 1)) + 100.0
    ren[:, 100:] = 125.0
    save_u8(d / "sl_ref.png", textured(ref))
    save_u8(d / "sl_render.png", textured(ren))
    Path(d / "sl_boxes.json").write_text(json.dumps({"boxes": {"left": [0.05, 0.1, 0.45, 0.9], "right": [0.55, 0.1, 0.95, 0.9]}}))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--reference", d / "sl_ref.png",
                                                         "--boxes", d / "sl_boxes.json", "--tolerance", 12, "--out", d / "sl1.json"])
    r = load_json(d / "sl1.json")
    rows = {b["name"]: b for b in r["boxes"]}
    check("scratch_luminance reports the known delta (-15 +/- 0.5) in the right box",
          abs(rows["right"]["delta"] - (-15.0)) < 0.5 and abs(rows["left"]["delta"]) < 0.5)
    check("test image is not flagged blank (so the failure below comes from the tolerance, not the blank gate)",
          r["suspect_blank"] is False and r["unique_values"] >= 8)
    check("scratch_luminance applies the tolerance per box (left ok, right fails) and exits 1",
          rows["left"]["pass"] and not rows["right"]["pass"] and code == 1 and r["pass"] is False)
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--reference", d / "sl_ref.png",
                                                         "--boxes", d / "sl_boxes.json", "--tolerance", 20, "--out", d / "sl2.json"])
    r2 = load_json(d / "sl2.json")
    check("the same render passes a 20-level tolerance (exit 0) and reports linear values too",
          code == 0 and r2["pass"] is True and r2["boxes"][0]["render_linear"] > 0)
    Path(d / "sl_target_boxes.json").write_text(json.dumps({"boxes": {"right": {"box": [0.55, 0.1, 0.95, 0.9], "target": 147.0}}}))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--boxes", d / "sl_target_boxes.json",
                                                         "--out", d / "sl3.json"])
    r3 = load_json(d / "sl3.json")
    check("a per-box target works without a reference (delta = 132 - 147 = -15 +/- 0.5, fails)",
          abs(r3["boxes"][0]["delta"] - (-15.0)) < 0.5 and code == 1)

    # coincidence: identical box means, but the bright event sits elsewhere
    ref2 = np.zeros((100, 200, 1)) + 60.0
    ref2[10:30, 150:190] = 255.0                     # bright event top-right
    ref3 = np.zeros((100, 200, 1)) + 60.0
    ref3[70:90, 10:50] = 255.0                       # same event bottom-left (same area, so same global mean)
    save_u8(d / "co_ref.png", np.where(ref2 > 200, ref2, textured(ref2)))
    save_u8(d / "co_render.png", np.where(ref3 > 200, ref3, textured(ref3)))
    spec = {"boxes": {"whole_frame": [0.0, 0.0, 1.0, 1.0]},
            "features": [{"name": "bright_event", "kind": "patch", "box": [0.6, 0.0, 1.0, 0.45],
                          "mask_threshold": 200, "min_iou": 0.3, "peak_tol": 30}]}
    Path(d / "co_boxes.json").write_text(json.dumps(spec))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "co_render.png", "--reference", d / "co_ref.png",
                                                         "--boxes", d / "co_boxes.json", "--out", d / "co.json"])
    r = load_json(d / "co.json")
    check("coincidence case: the box mean passes (delta ~0) on a non-blank image",
          r["boxes"][0]["pass"] and abs(r["boxes"][0]["delta"]) < 0.5 and r["suspect_blank"] is False)
    check("coincidence case: brightest-1% centroid check FAILS", r["brightest_percent"]["pass"] is False)
    check("coincidence case: the patch feature check FAILS (IoU 0) and the run exits 1",
          r["features"][0]["pass"] is False and r["features"][0]["iou"] == 0.0 and code == 1)

    # thin groove: reference has a dark 2 px line, render shows it at ~2 percent contrast
    g_ref = np.zeros((100, 200, 1)) + 150.0
    g_ref[:, 99:101] = 40.0
    g_ren = np.zeros((100, 200, 1)) + 150.0
    g_ren[:, 99:101] = 148.0
    save_u8(d / "gr_ref.png", textured(g_ref))
    save_u8(d / "gr_render.png", textured(g_ren))
    Path(d / "gr_boxes.json").write_text(json.dumps({
        "boxes": {"wall": [0.1, 0.1, 0.4, 0.9]},
        "features": [{"name": "wall_joint", "kind": "line", "box": [0.495, 0.1, 0.505, 0.9], "flank": 0.03, "min_ratio": 0.25}]}))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "gr_render.png", "--reference", d / "gr_ref.png",
                                                         "--boxes", d / "gr_boxes.json", "--out", d / "gr.json"])
    f = load_json(d / "gr.json")["features"][0]
    check("thin groove with ~no render contrast is reported NOT VISIBLE (ratio < 0.25) and fails",
          f["pass"] is False and f["ratio"] < 0.1 and "NOT VISIBLE" in f["reasons"][0] and code == 1)
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "gr_ref.png", "--reference", d / "gr_ref.png",
                                                         "--boxes", d / "gr_boxes.json", "--out", d / "gr2.json"])
    r = load_json(d / "gr2.json")
    f = r["features"][0]
    check("the same groove rendered like the reference passes (ratio 1.0, not blank, exit 0)",
          f["pass"] and abs(f["ratio"] - 1.0) < 1e-6 and r["suspect_blank"] is False and code == 0)

    make_flat(d / "flat.png", size, 90)
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "flat.png", "--reference", d / "flat.png", "--out", d / "flat.json"])
    r = load_json(d / "flat.json")
    check("a flat render is flagged suspect_blank even when it equals the reference (exit 1)",
          r["suspect_blank"] is True and code == 1)
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "does_not_exist.png", "--reference", d / "sl_ref.png"])
    check("a missing render exits 2", code == 2)
    Path(d / "bad_boxes.json").write_text(json.dumps({"boxes": {"oops": [10, 10, 50, 50]}}))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--reference", d / "sl_ref.png",
                                                         "--boxes", d / "bad_boxes.json"])
    check("boxes authored in pixels without pixel_size exit 2 with a hint", code == 2 and "pixel_size" in err)
    Path(d / "px_boxes.json").write_text(json.dumps({"pixel_size": [200, 100], "boxes": {"left": [10, 10, 90, 90]}}))
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--reference", d / "sl_ref.png",
                                                         "--boxes", d / "px_boxes.json", "--out", d / "px.json"])
    check("pixel_size normalises pixel boxes", code == 0 and load_json(d / "px.json")["boxes"][0]["box_px"] == [10, 10, 90, 90])
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--out", d / "grid.json"])
    check("no reference and no targets exits 2 (nothing to compare)", code == 2 and "nothing to compare" in err)
    code, out, err = run_script("scratch_luminance.py", ["--render", d / "sl_render.png", "--reference", d / "sl_ref.png",
                                                         "--out", d / "grid.json", "--report-only", "--tolerance", 1])
    check("default 4x3 grid yields 12 boxes and --report-only exits 0", code == 0 and len(load_json(d / "grid.json")["boxes"]) == 12)


def test_exr(d):
    try:
        import OpenEXR
        from scratch_luminance import load_image
    except ImportError:
        skip("EXR round trip", "OpenEXR package not installed")
        return
    arr = (BASE["sun"] * 0.5).astype(np.float32)
    path = str(d / "rt.exr")
    try:
        header = {"compression": OpenEXR.ZIP_COMPRESSION, "type": OpenEXR.scanlineimage}
        OpenEXR.File(header, {"RGB": arr}).write(path)
    except Exception as exc:                                  # API differs between OpenEXR releases
        skip("EXR round trip", "cannot write EXR with this OpenEXR build: {0}".format(exc))
        return
    img = load_image(path)
    check("EXR round trip: linear values read back within 1e-2 relative (half/float storage)",
          img.space == "linear" and np.abs(img.lin - arr).max() <= 1e-2 * max(float(arr.max()), 1.0) and len(img.parts) >= 1)


def main():
    d = Path(tempfile.mkdtemp(prefix="lighting_scripts_test_"))
    print("temp dir: {0}".format(d))
    try:
        test_helps()
        test_nnls()
        test_additivity(d)
        test_solver_no_haze(d)
        test_solver_haze(d)
        test_solver_inputs(d)
        test_scratch_luminance(d)
        test_exr(d)
    finally:
        shutil.rmtree(str(d), ignore_errors=True)
    passed, failed = sum(1 for r in RESULTS if r), sum(1 for r in RESULTS if not r)
    print("")
    print("{0} passed, {1} failed, {2} skipped".format(passed, failed, len(SKIPS)))
    return 0 if failed == 0 and passed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
