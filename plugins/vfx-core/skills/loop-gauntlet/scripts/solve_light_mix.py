"""solve_light_mix.py -- solve the light mix from per-light-group isolation passes.

A path tracer is linear in emission: the beauty of a mix is the sum of each
light group rendered ALONE (everything else off) and scaled by its intensity.
Render each group once, then fit the intensities against the reference in one
least-squares step instead of by trial scratch renders (every light reaches
every box, so adjusting them one at a time by eye only moves the error around).

    pass_i   = group i rendered alone at its nominal intensity (linear EXR/npy)
    mix(w)   = sum_i w_i * pass_i                      w_i >= 0 are the answers
    with haze-free twins (--clear NAME=PATH) the haze density is a variable too:
    pass_i(k) = clear_i + k * (hazed_i - clear_i)      (first-order in k)

Modes
  solve   (default)  fit w (and k) so the box means match the reference / targets.
                     Optional --all-on RENDER runs the ADDITIVITY CHECK first:
                     the passes mixed at the weights the all-on render used must
                     reproduce that render's box values. If it fails the solve
                     is written but marked "trusted": false and the exit code is 1.
  verify             --verify RENDER --weights-from solve.json : after rendering
                     ONCE at the solved weights, report the prediction error
                     (predicted box luma vs rendered box luma). Exit 1 above
                     --verify-tol.

Maths (what is kept from the job script this was generalised from, and what changed)
  KEPT   linear mixing of passes; the haze term pass(k) = clear + k*(hazed-clear);
         scoring through the same sRGB encode and PIL luma (0.299/0.587/0.114 on
         encoded 0-255 values) the targets were measured with; weights are
         multipliers on the values each pass was rendered with; a global-mean
         row (--global-weight, default 0.5 as in the source); --fix to hold a
         value; the instrument checks (additivity, pass diagnostics).
  CHANGED 1. The source ran scipy least_squares on the encoded-luma residual.
            This script solves NNLS on LINEAR box means first (closed form,
            deterministic, no scipy), with each row scaled by the local slope of
            the sRGB curve at its target so a linear residual approximates the
            encoded-luma residual the score uses (otherwise bright boxes
            dominate). --fit-space encoded then polishes with a projected
            Levenberg-Marquardt on the true encoded-luma residual, starting
            from the linear answer (no finite-difference cache: the source's
            cache key rounded weights to 6 decimals, which flattened its own
            finite-difference steps and returned the start point).
         2. The haze multiplier k is found by a 1-D scan + golden-section search
            with an NNLS solve inside (variable projection), not a joint
            nonlinear fit.
         3. Targets: per-box "target" luma in the boxes JSON, or the reference
            image's own box means (linearised for the linear fit). Job-specific
            parts of the source (hard-coded boxes, sun footprint IoU against a
            fixed mask, a fixed beam box and --beam-min) are dropped; use
            scratch_luminance.py feature checks for placement.
         4. --per-channel fits R,G,B rows (colour) instead of luminance only.
         5. Extra diagnostics: per-pass stats incl. brightest-1% centroid,
            per-box contribution of each group, condition number, warnings for
            weight 0 / all-black pass / hazed darker than clear.
  If SciPy is installed it is not used: Lawson-Hanson NNLS is implemented here.

Inputs
  --pass NAME=PATH   one per light group (repeat). .exr (needs OpenEXR), .npy
                     (float HxWx3, linear), or 8-bit/16-bit images read as sRGB
                     (8-bit passes clip and quantise: prefer EXR/npy).
  --clear NAME=PATH  haze-free twin of NAME (all groups or none).
  --reference IMG    target = the reference's box means (fitted to the pass size
                     like scratch_luminance.py), and/or "target" values per box
                     in --boxes JSON (see scratch_luminance.py for the format;
                     a top-level "global_target" luma is also read).

Exit codes: 0 ok, 1 a requested check failed (additivity or verify; JSON still
written), 2 input / usage error.

Usage:
    python solve_light_mix.py --pass sun=sun.exr --pass sky=sky.exr --pass fixed=fixed.exr \\
        --reference ref.png --boxes boxes.json --all-on allon.png --out solve.json
    python solve_light_mix.py --pass sun=sun.exr ... --verify iter03.png --weights-from solve.json
"""
import argparse
import json
import math
import os
import sys
from datetime import datetime, timezone

try:
    import numpy as np
except ImportError:
    sys.stderr.write("ERROR: solve_light_mix.py needs numpy (pip install numpy).\n")
    sys.exit(2)
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scratch_luminance as sl                                   # noqa: E402
from scratch_luminance import InputError, Y_W, LUMA_W            # noqa: E402

DEFAULT_ADDITIVITY_TOL = 2.0     # luma levels; the job runs read 0.2 (EXR vs PNG) up to 1.1
DEFAULT_VERIFY_TOL = 4.0         # luma levels; the job's three verification renders read 1.1, 2.4, 2.8
GLOBAL_STRIDE = 3                # global-mean row sampled every 3rd pixel inside the solver (full-res in reports)


# ----------------------------------------------------------------------------
# non-negative least squares (Lawson-Hanson active set), numpy only
# ----------------------------------------------------------------------------

def lawson_hanson_nnls(A, b):
    """min ||A x - b||_2 subject to x >= 0. Returns x (float64). Columns are
    normalised internally so mixed-magnitude passes (a sun at 50, a fill at
    0.01) do not upset the active-set tolerances."""
    A = np.asarray(A, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    m, n = A.shape
    out = np.zeros(n)
    cn = np.linalg.norm(A, axis=0)
    live = np.flatnonzero(cn > 0)
    bs = float(np.abs(b).max()) if b.size else 0.0
    if live.size == 0 or bs == 0.0:
        return out
    As = A[:, live] / cn[live]
    bn = b / bs
    n2 = As.shape[1]
    x = np.zeros(n2)
    passive = np.zeros(n2, dtype=bool)
    tol = 10.0 * max(m, n2) * np.finfo(float).eps
    grad = As.T @ (bn - As @ x)
    outer = 0
    while (~passive).any() and grad[~passive].max() > tol and outer < 3 * n2 + 10:
        outer += 1
        free = np.flatnonzero(~passive)
        passive[free[int(np.argmax(grad[free]))]] = True
        s = np.zeros(n2)
        s[passive] = np.linalg.lstsq(As[:, passive], bn, rcond=None)[0]
        inner = 0
        while s[passive].min() <= 0.0 and inner < 3 * n2 + 10:
            inner += 1
            neg = passive & (s <= 0.0)
            denom = x[neg] - s[neg]
            ratio = np.where(denom > 0.0, x[neg] / np.where(denom > 0.0, denom, 1.0), 0.0)
            alpha = float(ratio.min())
            x = x + alpha * (s - x)
            passive &= x > 1e-14
            x[~passive] = 0.0
            s = np.zeros(n2)
            if passive.any():
                s[passive] = np.linalg.lstsq(As[:, passive], bn, rcond=None)[0]
            else:
                break
        x = s
        grad = As.T @ (bn - As @ x)
    out[live] = x * bs / cn[live]
    return out


# ----------------------------------------------------------------------------
# small helpers
# ----------------------------------------------------------------------------

def parse_kv(items, label, allow_float=False):
    """['sun=a.exr', ...] -> ordered dict name -> str (or float when allow_float)."""
    out = {}
    for item in items or []:
        if "=" not in item:
            raise InputError("%s expects NAME=VALUE, got %r" % (label, item))
        k, v = item.split("=", 1)
        k = k.strip()
        if not k or not v.strip():
            raise InputError("%s expects NAME=VALUE, got %r" % (label, item))
        if k in out:
            raise InputError("%s: %r given twice" % (label, k))
        if allow_float:
            try:
                out[k] = float(v)
            except ValueError:
                raise InputError("%s: %r is not a number in %r" % (label, v, item))
        else:
            out[k] = v.strip()
    return out


def enc_slope(lin):
    """d(255 * srgb_encode(x))/dx: luma levels per unit linear, used to scale rows."""
    x = np.maximum(np.asarray(lin, dtype=np.float64), 0.0)
    return 255.0 * np.where(x <= 0.0031308, 12.92, 1.055 / 2.4 * np.power(np.maximum(x, 0.0031308), 1.0 / 2.4 - 1.0))


def enc_mean(lin):
    """Mean PIL-style luma (0-255) of the sRGB 8-bit encoding of a linear RGB array."""
    return float(sl.luma_of_enc(sl.srgb_encode(lin) * 255.0).mean())


def mix(parts, groups, w, k):
    """sum_g w_g * (clear_g + k*(hazed_g - clear_g)); parts[g] = (hazed, clear|None)."""
    tot = None
    for g in groups:
        hz, cl = parts[g]
        p = hz if cl is None else cl + k * (hz - cl)
        tot = w[g] * p if tot is None else tot + w[g] * p
    return tot


def crops_of(arrays, px, as64=True):
    x0, y0, x1, y1 = px
    c = arrays[y0:y1, x0:x1]
    return c.astype(np.float64) if as64 else c


def region_parts(H, N, groups, px, as64=True):
    return {g: (crops_of(H[g], px, as64), None if N is None else crops_of(N[g], px, as64)) for g in groups}


def mean_rgb(arr, px):
    x0, y0, x1, y1 = px
    return arr[y0:y1, x0:x1].reshape(-1, 3).astype(np.float64).mean(axis=0)


# ----------------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------------

def load_passes(args):
    pass_paths = parse_kv(args.passes, "--pass")
    if not pass_paths:
        raise InputError("give at least one --pass NAME=PATH (one isolation pass per light group)")
    clear_paths = parse_kv(args.clear, "--clear")
    for g in clear_paths:
        if g not in pass_paths:
            raise InputError("--clear names unknown group %r (groups: %s)" % (g, ", ".join(pass_paths)))
    if clear_paths and set(clear_paths) != set(pass_paths):
        raise InputError("--clear must cover every group or none; missing: %s"
                         % ", ".join(g for g in pass_paths if g not in clear_paths))
    groups = list(pass_paths)
    H, N, info, notes, size = {}, ({} if clear_paths else None), {}, [], None
    for g in groups:
        img = sl.load_image(pass_paths[g], args.pass_space, args.exr_layer)
        if size is None:
            size = img.size
        elif img.size != size:
            raise InputError("pass %r is %dx%d but earlier passes are %dx%d" % (g, img.size[0], img.size[1], size[0], size[1]))
        if img.kind == "8bit":
            notes.append("pass %s is 8-bit: highlights clip at 1.0 and values quantise; prefer EXR/npy" % g)
        if float(img.lin_y.max()) <= 0.0:
            raise InputError("pass %r is entirely black (%s): the group rendered nothing -- wrong group name, light "
                             "left disabled, or an instrument fault. Fix it or drop the group." % (g, pass_paths[g]))
        H[g] = img.lin
        info[g] = {"path": os.path.abspath(pass_paths[g]), "bytes": img.nbytes, "read_as": img.space,
                   "mean_linear_y": round(float(img.lin_y.mean()), 6), "p99_5_linear_y": round(float(np.percentile(img.lin_y, 99.5)), 6),
                   "max_linear_y": round(float(img.lin_y.max()), 6),
                   "brightest_1pct": sl.brightest_percent(img.lin_y, 1.0), "exr_parts": img.parts}
        notes.extend("pass %s: %s" % (g, n) for n in img.notes)
        if clear_paths:
            cimg = sl.load_image(clear_paths[g], args.pass_space, args.exr_layer)
            if cimg.size != size:
                raise InputError("clear twin of %r is %dx%d, expected %dx%d" % (g, cimg.size[0], cimg.size[1], size[0], size[1]))
            N[g] = cimg.lin
            haze_part = float(img.lin_y.mean() - cimg.lin_y.mean())
            info[g].update({"clear_path": os.path.abspath(clear_paths[g]), "haze_part_mean_linear_y": round(haze_part, 6)})
            if haze_part < 0:
                notes.append("hazed pass of %s is DARKER than its haze-free twin (mean %.6f): twins swapped or noisy" % (g, haze_part))
    return groups, H, N, size, info, notes


def load_reference(args, size):
    if not args.reference:
        return None, []
    ref = sl.load_image(args.reference, args.reference_space, args.exr_layer)
    notes = []
    if args.crop:
        cw, ch = args.crop[2] - args.crop[0], args.crop[3] - args.crop[1]
        if cw <= 0 or ch <= 0:
            raise InputError("--crop is empty: %s" % args.crop)
    src_aspect = ref.size[0] / float(ref.size[1])
    if args.crop:
        src_aspect = cw / float(ch)
    if abs(src_aspect - size[0] / float(size[1])) / (size[0] / float(size[1])) > 0.01:
        notes.append("reference aspect %.3f differs from the passes' %.3f: %s fit applied; box coordinates refer to the "
                     "fitted frame" % (src_aspect, size[0] / float(size[1]), args.fit))
    ref = sl.fit_to_size(ref, size, args.crop, args.fit)
    return ref, notes + ref.notes


# ----------------------------------------------------------------------------
# prediction error (shared by the additivity check and verify mode)
# ----------------------------------------------------------------------------

def compare_to_render(groups, H, N, weights, k, render, names, px_boxes, tol):
    """Predicted box luma (passes mixed at weights, haze k) vs the rendered box luma."""
    rows = []
    for name, px in zip(names, px_boxes):
        pred = enc_mean(mix(region_parts(H, N, groups, px), groups, weights, k))
        meas = sl._mean(render.luma, px)
        rows.append({"name": name, "predicted": round(pred, 2), "render": round(meas, 2), "diff": round(pred - meas, 2)})
    full = {g: (H[g], None if N is None else N[g]) for g in groups}
    gpred = enc_mean(mix(full, groups, weights, k))
    gmeas = float(render.luma.mean())
    diffs = [abs(r["diff"]) for r in rows]
    return {"render": os.path.abspath(render.path), "weights": {g: round(float(weights[g]), 6) for g in groups},
            "haze_k": None if N is None else round(float(k), 6), "boxes": rows,
            "max_abs_diff": round(max(diffs), 2), "mean_abs_diff": round(sum(diffs) / len(diffs), 2),
            "global_predicted": round(gpred, 2), "global_render": round(gmeas, 2), "global_diff": round(gpred - gmeas, 2),
            "tolerance": tol, "pass": bool(max(diffs) <= tol and abs(gpred - gmeas) <= tol)}


# ----------------------------------------------------------------------------
# the solve
# ----------------------------------------------------------------------------

def refine_encoded(x0, residual, lo, hi, iters=60):
    """Projected Levenberg-Marquardt on residual(x); forward-difference Jacobian, no caching."""
    x = np.clip(np.asarray(x0, dtype=np.float64), lo, hi)
    r = residual(x)
    cost0 = cost = float(r @ r)
    lam, used = 1e-2, 0
    for it in range(iters):
        jac = np.empty((r.size, x.size))
        for j in range(x.size):
            step = 1e-3 * max(abs(x[j]), 1e-3)
            xp = x.copy()
            xp[j] += step
            jac[:, j] = (residual(xp) - r) / step
        g, hm = jac.T @ r, jac.T @ jac
        improved = False
        for _ in range(8):
            try:
                dx = np.linalg.solve(hm + lam * np.diag(np.diag(hm) + 1e-12), -g)
            except np.linalg.LinAlgError:
                lam *= 10.0
                continue
            xn = np.clip(x + dx, lo, hi)
            rn = residual(xn)
            cn = float(rn @ rn)
            if cn < cost:
                improved = cost - cn > 1e-10 * max(cost, 1e-9)
                x, r, cost, lam = xn, rn, cn, max(lam / 3.0, 1e-9)
                used += 1
                break
            lam *= 4.0
        else:
            break
        if not improved:
            break
    return x, {"start_cost": round(cost0, 6), "end_cost": round(cost, 6), "accepted_steps": used}


def solve(args, groups, H, N, size, spec, reference, notes):
    w_img, h_img = size
    names = [b["name"] for b in spec["boxes"]]
    px = [sl.to_px(b["box"], w_img, h_img) for b in spec["boxes"]]
    B = len(names)
    has_clear = N is not None
    fixed = parse_kv(args.fix, "--fix", allow_float=True)
    for key in fixed:
        if key != "k" and key not in groups:
            raise InputError("--fix names unknown group %r (groups: %s, or k)" % (key, ", ".join(groups)))
    k_fixed = fixed.pop("k", None)
    if k_fixed is not None and not has_clear:
        notes.append("--fix k ignored: no --clear twins, haze density is not a variable")
    free_groups = [g for g in groups if g not in fixed]
    if not free_groups:
        raise InputError("every group is fixed with --fix: nothing to solve")

    # ---- targets: per box in encoded luma (the score) and linear (the fit) ----
    t_enc = [None] * B
    t_rgb = [None] * B                                   # linear RGB target (reference only)
    t_y = [None] * B
    for i, b in enumerate(spec["boxes"]):
        if b["target"] is not None:
            t_enc[i] = b["target"]
            t_y[i] = float(sl.srgb_decode(np.array(b["target"] / 255.0)))
            if reference is not None:
                t_rgb[i] = mean_rgb(reference.lin, px[i])
        elif reference is not None:
            t_enc[i] = sl._mean(reference.luma, px[i])
            t_rgb[i] = mean_rgb(reference.lin, px[i])
            t_y[i] = float(t_rgb[i] @ Y_W)
    g_enc = g_rgb = g_y = None
    if spec["global_target"] is not None:
        g_enc = spec["global_target"]
        g_y = float(sl.srgb_decode(np.array(g_enc / 255.0)))
    elif reference is not None:
        g_enc = float(reference.luma.mean())
        g_rgb = mean_rgb(reference.lin, (0, 0, w_img, h_img))
        g_y = float(g_rgb @ Y_W)
    fit_idx = [i for i in range(B) if t_enc[i] is not None]
    if not fit_idx:
        raise InputError("no targets: give --reference or per-box \"target\" values in the boxes JSON")
    if args.per_channel and (reference is None or any(t_rgb[i] is None for i in fit_idx)):
        raise InputError("--per-channel needs --reference (per-box numeric targets carry no colour)")

    # ---- linear system rows ----
    full_px = (0, 0, w_img, h_img)
    mrgb_h = {g: np.array([mean_rgb(H[g], p) for p in px] + [mean_rgb(H[g], full_px)]) for g in groups}
    mrgb_n = {g: np.array([mean_rgb(N[g], p) for p in px] + [mean_rgb(N[g], full_px)]) for g in groups} if has_clear else None
    rows = []                                            # (index into mrgb arrays, channel or None, target, weight)
    for i in fit_idx:
        if args.per_channel:
            for c in range(3):
                rows.append((i, c, float(t_rgb[i][c]), float(enc_slope(t_rgb[i][c])) / math.sqrt(3.0)))
        else:
            rows.append((i, None, t_y[i], float(enc_slope(t_y[i]))))
    use_global = g_enc is not None and args.global_weight > 0
    if use_global:
        if args.per_channel and g_rgb is not None:
            for c in range(3):
                rows.append((B, c, float(g_rgb[c]), args.global_weight * float(enc_slope(g_rgb[c])) / math.sqrt(3.0)))
        else:
            rows.append((B, None, g_y, args.global_weight * float(enc_slope(g_y))))

    def column(m):
        return np.array([(m[i] @ Y_W) if c is None else m[i][c] for i, c, _, _ in rows])

    A_h = np.stack([column(mrgb_h[g]) for g in groups], axis=1)
    A_n = np.stack([column(mrgb_n[g]) for g in groups], axis=1) if has_clear else None
    tvec = np.array([t for _, _, t, _ in rows])
    rw = np.array([wt for _, _, _, wt in rows])
    gi = {g: j for j, g in enumerate(groups)}
    free_j = [gi[g] for g in free_groups]
    fix_j = [gi[g] for g in groups if g in fixed]
    fix_w = np.array([fixed[g] for g in groups if g in fixed])

    def solve_k(k):
        A = A_h if not has_clear else A_n + k * (A_h - A_n)
        Aw, bw = A * rw[:, None], tvec * rw
        rhs = bw - (Aw[:, fix_j] @ fix_w if fix_j else 0.0)
        x = lawson_hanson_nnls(Aw[:, free_j], rhs)
        return x, float(np.linalg.norm(Aw[:, free_j] @ x - rhs)), Aw[:, free_j]

    k_lo, k_hi = args.k_range
    if not has_clear:
        k = 1.0
    elif k_fixed is not None:
        k = k_fixed
    else:
        grid = np.linspace(k_lo, k_hi, 41)
        errs = [solve_k(v)[1] for v in grid]
        ib = int(np.argmin(errs))
        a, b = grid[max(ib - 1, 0)], grid[min(ib + 1, len(grid) - 1)]
        phi = (math.sqrt(5.0) - 1.0) / 2.0
        c, d = b - phi * (b - a), a + phi * (b - a)
        fc, fd = solve_k(c)[1], solve_k(d)[1]
        for _ in range(40):
            if fc < fd:
                b, d, fd = d, c, fc
                c = b - phi * (b - a)
                fc = solve_k(c)[1]
            else:
                a, c, fc = c, d, fd
                d = a + phi * (b - a)
                fd = solve_k(d)[1]
        k = 0.5 * (a + b)
        if solve_k(k)[1] > errs[ib]:
            k = float(grid[ib])
    x, resnorm, Awf = solve_k(k)
    weights = dict(fixed)
    weights.update({g: float(v) for g, v in zip(free_groups, x)})
    sing = np.linalg.svd(Awf, compute_uv=False)
    cond = float(sing[0] / sing[-1]) if sing.size and sing[-1] > 0 else None
    warnings = list(notes)
    if len(rows) < len(free_groups) + (1 if (has_clear and k_fixed is None) else 0):
        warnings.append("underdetermined: %d rows for %d unknowns; add boxes" % (len(rows), len(free_groups)))
    if cond is None or cond > 1e4:
        warnings.append("passes are nearly collinear over these boxes (condition number %s): the boxes cannot tell the "
                        "groups apart, weights are not unique -- add boxes that one group lights and another does not"
                        % ("inf" if cond is None else "%.3g" % cond))

    # ---- pixel-level predictions (the real instrument) ----
    crops = [region_parts(H, N, groups, p) for p in px]
    glob_parts = {g: (H[g][::GLOBAL_STRIDE, ::GLOBAL_STRIDE].astype(np.float64),
                      None if N is None else N[g][::GLOBAL_STRIDE, ::GLOBAL_STRIDE].astype(np.float64)) for g in groups}

    def predict(wd, kk):
        return np.array([enc_mean(mix(c, groups, wd, kk)) for c in crops]), enc_mean(mix(glob_parts, groups, wd, kk))

    fit_space_info = {"space": "linear", "refine": None}
    if args.fit_space == "encoded":
        te = np.array([t_enc[i] for i in fit_idx])
        var = free_groups + (["k"] if (has_clear and k_fixed is None) else [])

        def unpack(v):
            wd = dict(fixed)
            wd.update({g: float(v[j]) for j, g in enumerate(free_groups)})
            return wd, (float(v[-1]) if "k" in var else k)

        def resid(v):
            wd, kk = unpack(v)
            pb, gb = predict(wd, kk)
            r = list(pb[fit_idx] - te)
            if use_global:
                r.append(args.global_weight * (gb - g_enc))
            return np.array(r)

        v0 = np.array([weights[g] for g in free_groups] + ([k] if "k" in var else []))
        lo = np.array([0.0] * len(free_groups) + ([k_lo] if "k" in var else []))
        hi = np.array([args.max_weight] * len(free_groups) + ([k_hi] if "k" in var else []))
        vbest, info = refine_encoded(v0, resid, lo, hi)
        wd, kk = unpack(vbest)
        weights, k = wd, kk
        fit_space_info = {"space": "encoded", "refine": info}

    pb, _ = predict(weights, k)
    full = {g: (H[g], None if N is None else N[g]) for g in groups}
    gpred = enc_mean(mix(full, groups, weights, k))
    predicted = []
    for i, name in enumerate(names):
        row = {"name": name, "box_norm": [round(v, 4) for v in spec["boxes"][i]["box"]], "box_px": list(px[i]),
               "target": None if t_enc[i] is None else round(float(t_enc[i]), 2),
               "target_linear_y": None if t_y[i] is None else round(float(t_y[i]), 6), "predicted": round(float(pb[i]), 2),
               "residual": None if t_enc[i] is None else round(float(pb[i] - t_enc[i]), 2), "fitted": i in fit_idx}
        row["contribution_luma"] = {g: round(enc_mean(weights[g] * (crops[i][g][0] if N is None else
                                    crops[i][g][1] + k * (crops[i][g][0] - crops[i][g][1]))), 2) for g in groups}
        predicted.append(row)
    res = np.array([r["residual"] for r in predicted if r["fitted"]])
    summary = {"n_fitted": int(res.size), "within_12": int((np.abs(res) <= 12).sum()), "within_20": int((np.abs(res) <= 20).sum()),
               "within_35": int((np.abs(res) <= 35).sum()), "max_abs_residual": round(float(np.abs(res).max()), 2),
               "rms_residual": round(float(np.sqrt((res ** 2).mean())), 2),
               "global_predicted": round(gpred, 2), "global_target": None if g_enc is None else round(float(g_enc), 2)}
    for g in free_groups:
        if weights[g] <= 1e-9:
            warnings.append("group %r got weight 0: it cannot help these targets -- check it is not double-sided, blocked or "
                            "wrongly isolated, or the other groups already give more light than the targets want" % g)
        elif weights[g] >= args.max_weight:
            warnings.append("group %r weight %.3g is at/over --max-weight: the pass is too dim to be the answer" % (g, weights[g]))
    if has_clear and k_fixed is None and (abs(k - k_lo) < 1e-6 or abs(k - k_hi) < 1e-6) and args.fit_space == "linear":
        warnings.append("haze k %.3f sits on the edge of --k-range %s: widen the range or re-check the clear twins" % (k, args.k_range))
    fit = {"weights": {g: round(float(weights[g]), 6) for g in groups}, "haze_k": None if not has_clear else round(float(k), 6),
           "fixed": dict(fixed, **({"k": k_fixed} if k_fixed is not None else {})), "per_channel": bool(args.per_channel),
           "global_weight": args.global_weight if use_global else 0.0, "nnls_weighted_residual_norm": round(resnorm, 6),
           "condition_number": None if cond is None else round(cond, 3), "rows": len(rows), "fit_space": fit_space_info,
           "units": "multipliers on the intensity each pass was rendered with; haze_k multiplies the haze density"}
    return {"fit": fit, "predicted": predicted, "summary": summary, "warnings": warnings}, weights, k


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def build_parser():
    ap = argparse.ArgumentParser(
        description="Solve per-light-group intensity multipliers from isolation passes (non-negative least squares on "
                    "linear values), check additivity against an all-on render, and verify a render against the "
                    "prediction. Exit 0 ok, 1 a requested check failed, 2 input error.")
    ap.add_argument("--pass", dest="passes", action="append", default=[], metavar="NAME=PATH",
                    help="isolation pass of one light group rendered alone (repeat per group)")
    ap.add_argument("--clear", action="append", default=[], metavar="NAME=PATH",
                    help="haze-free twin of a group's pass (every group or none); makes the haze density k a variable")
    ap.add_argument("--reference", help="reference image: targets are its box means")
    ap.add_argument("--boxes", help="boxes JSON (normalised 0-1, optional per-box \"target\" luma); default --grid")
    ap.add_argument("--grid", default=sl.DEFAULT_GRID, help="COLSxROWS grid when no --boxes (default %s)" % sl.DEFAULT_GRID)
    ap.add_argument("--crop", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"), help="crop the reference first (its pixels)")
    ap.add_argument("--fit", choices=("letterbox", "stretch"), default="letterbox")
    ap.add_argument("--pass-space", choices=("auto", "srgb", "linear"), default="auto",
                    help="how to read pass files (auto: exr/npy linear, others sRGB)")
    ap.add_argument("--reference-space", choices=("auto", "srgb", "linear"), default="auto")
    ap.add_argument("--exr-layer", help="channel prefix for layered EXRs, e.g. ViewLayer.Combined")
    ap.add_argument("--fix", action="append", default=[], metavar="NAME=VALUE", help="hold a group weight (or k=VALUE) fixed")
    ap.add_argument("--global-weight", type=float, default=0.5, help="weight of the global-mean row (0 disables; default 0.5)")
    ap.add_argument("--k-range", type=float, nargs=2, default=(0.1, 3.0), metavar=("LO", "HI"), help="haze multiplier range")
    ap.add_argument("--max-weight", type=float, default=200.0, help="warn when a weight reaches this (default 200)")
    ap.add_argument("--per-channel", action="store_true", help="fit R,G,B rows (colour), not luminance only")
    ap.add_argument("--fit-space", choices=("linear", "encoded"), default="linear",
                    help="linear: NNLS on linear means (default); encoded: then polish on the encoded-luma residual")
    ap.add_argument("--all-on", help="all-lights-on render for the additivity check")
    ap.add_argument("--all-on-weights", action="append", default=[], metavar="NAME=VALUE",
                    help="weights the all-on render used (default 1.0 each; k=VALUE for haze, default 1)")
    ap.add_argument("--additivity-tol", type=float, default=DEFAULT_ADDITIVITY_TOL,
                    help="max |predicted - rendered| box luma for the additivity check (default %g)" % DEFAULT_ADDITIVITY_TOL)
    ap.add_argument("--verify", metavar="RENDER", help="verify mode: compare this render with the passes mixed at --weights-from")
    ap.add_argument("--weights-from", metavar="JSON", help="result JSON of an earlier solve (weights, haze k, boxes)")
    ap.add_argument("--verify-tol", type=float, default=DEFAULT_VERIFY_TOL,
                    help="max prediction error in verify mode, luma levels (default %g)" % DEFAULT_VERIFY_TOL)
    ap.add_argument("--render-space", choices=("auto", "srgb", "linear"), default="auto", help="how to read --all-on / --verify")
    ap.add_argument("--preview", help="write the predicted mix as an sRGB PNG (solve mode)")
    ap.add_argument("--out", help="result JSON path (default: light_mix_result.json next to the first pass)")
    return ap


def echo_inputs(args, groups, size, info, spec):
    print("groups:     %s  (%dx%d)" % (", ".join(groups), size[0], size[1]))
    for g in groups:
        print("  %-12s %s  mean_lin_y %.5f  p99.5 %.5f  max %.4f  brightest-1%% centroid %s%s" % (
            g, info[g]["path"], info[g]["mean_linear_y"], info[g]["p99_5_linear_y"], info[g]["max_linear_y"],
            info[g]["brightest_1pct"]["centroid_norm"],
            ("  haze part %.5f" % info[g]["haze_part_mean_linear_y"]) if "haze_part_mean_linear_y" in info[g] else ""))
    print("boxes:      %d from %s | reference: %s | fit-space %s%s" % (
        len(spec["boxes"]), spec["source"], args.reference or "none", args.fit_space, " per-channel" if args.per_channel else ""))


def run(args):
    groups, H, N, size, info, notes = load_passes(args)
    verify = args.verify is not None
    prior = None
    if verify:
        if not args.weights_from and not args.fix:
            raise InputError("--verify needs --weights-from RESULT.json (or --fix NAME=W for every group)")
        if args.weights_from:
            if not os.path.isfile(args.weights_from):
                raise InputError("--weights-from file not found: %s" % args.weights_from)
            try:
                with open(args.weights_from, "r", encoding="utf-8") as fh:
                    prior = json.load(fh)
                prior["fit"]["weights"]
            except (ValueError, KeyError, TypeError):
                raise InputError("--weights-from is not a solve_light_mix result JSON: %s" % args.weights_from)
    if args.boxes or prior is None:
        spec = sl.load_boxes(args.boxes, args.grid)
    else:
        spec = {"boxes": [{"name": p["name"], "box": p["box_norm"], "target": None, "tolerance": None} for p in prior["predicted"]],
                "features": [], "global_target": None, "source": args.weights_from}
    echo_inputs(args, groups, size, info, spec)
    names = [b["name"] for b in spec["boxes"]]
    px = [sl.to_px(b["box"], size[0], size[1]) for b in spec["boxes"]]
    result = {"tool": "solve_light_mix", "created_utc": datetime.now(timezone.utc).isoformat(), "mode": "verify" if verify else "solve",
              "groups": groups, "image_size": list(size), "passes": info, "boxes_source": spec["source"]}

    if verify:
        weights = {}
        if prior is not None:
            weights.update({g: float(v) for g, v in prior["fit"]["weights"].items()})
        fixed = parse_kv(args.fix, "--fix", allow_float=True)
        k = fixed.pop("k", None)
        weights.update(fixed)
        if k is None:
            k = (prior or {}).get("fit", {}).get("haze_k") or 1.0
        missing = [g for g in groups if g not in weights]
        if missing:
            raise InputError("no weight for group(s) %s: pass --weights-from or --fix NAME=W" % ", ".join(missing))
        render = sl.load_image(args.verify, args.render_space, args.exr_layer)
        if render.size != size:
            raise InputError("render is %dx%d, passes are %dx%d" % (render.size[0], render.size[1], size[0], size[1]))
        cmp_ = compare_to_render(groups, H, N, weights, k if N is not None else 1.0, render, names, px, args.verify_tol)
        result.update({"verification": cmp_, "warnings": notes, "pass": cmp_["pass"]})
        print("\nVERIFY %s  weights %s  haze k %s" % (args.verify, cmp_["weights"], cmp_["haze_k"]))
        for r in cmp_["boxes"]:
            print("  %-22s predicted %6.1f  rendered %6.1f  error %+5.1f" % (r["name"], r["predicted"], r["render"], r["diff"]))
        print("  max |error| %.1f  mean |error| %.1f  global predicted %.1f rendered %.1f  (tolerance %g)  %s" % (
            cmp_["max_abs_diff"], cmp_["mean_abs_diff"], cmp_["global_predicted"], cmp_["global_render"], args.verify_tol,
            "PASS" if cmp_["pass"] else "FAIL"))
        return result

    reference, ref_notes = load_reference(args, size)
    add = None
    if args.all_on:
        wspec = parse_kv(args.all_on_weights, "--all-on-weights", allow_float=True)
        k_on = wspec.pop("k", 1.0)
        for key in wspec:
            if key not in groups:
                raise InputError("--all-on-weights names unknown group %r" % key)
        w_on = {g: wspec.get(g, 1.0) for g in groups}
        allon = sl.load_image(args.all_on, args.render_space, args.exr_layer)
        if allon.size != size:
            raise InputError("--all-on render is %dx%d, passes are %dx%d" % (allon.size[0], allon.size[1], size[0], size[1]))
        add = compare_to_render(groups, H, N, w_on, k_on if N is not None else 1.0, allon, names, px, args.additivity_tol)
    body, weights, k = solve(args, groups, H, N, size, spec, reference, notes + ref_notes)
    result.update(body)
    result["additivity"] = add
    result["trusted"] = bool(add["pass"]) if add is not None else None
    if add is not None and not add["pass"]:
        result["warnings"].append(
            "ADDITIVITY FAILED (max box error %.1f > %g luma): the passes do not sum to the all-on render, so the solve "
            "is not trusted. See reference/lighting_match.md 'When additivity fails'." % (add["max_abs_diff"], args.additivity_tol))
    result["pass"] = True if add is None else bool(add["pass"])
    f = result["fit"]
    if add is not None:
        print("\nADDITIVITY (passes mixed at %s, k=%s vs %s):" % (add["weights"], add["haze_k"], args.all_on))
        for r in add["boxes"]:
            print("  %-22s predicted %6.1f  rendered %6.1f  diff %+5.1f" % (r["name"], r["predicted"], r["render"], r["diff"]))
        print("  max |diff| %.2f  global %+.2f  (tolerance %g)  %s" % (add["max_abs_diff"], add["global_diff"], args.additivity_tol,
                                                                       "PASS" if add["pass"] else "FAIL"))
    print("\nSOLVED weights %s  haze k %s  [%s fit, condition %s]" % (f["weights"], f["haze_k"], f["fit_space"]["space"], f["condition_number"]))
    for r in result["predicted"]:
        if r["fitted"]:
            print("  %-22s predicted %6.1f  target %6.1f  residual %+6.1f   %s" % (
                r["name"], r["predicted"], r["target"], r["residual"], " ".join("%s=%.1f" % kv for kv in r["contribution_luma"].items())))
    s = result["summary"]
    print("  within 12/20/35: %d %d %d of %d | max |residual| %.1f | global %.1f vs %s" % (
        s["within_12"], s["within_20"], s["within_35"], s["n_fitted"], s["max_abs_residual"], s["global_predicted"], s["global_target"]))
    for wmsg in result["warnings"]:
        print("WARNING: " + wmsg)
    if args.preview:
        full = {g: (H[g], None if N is None else N[g]) for g in groups}
        lin = mix(full, groups, weights, k)
        Image.fromarray((sl.srgb_encode(lin) * 255.0 + 0.5).astype(np.uint8)).save(args.preview)
        result["preview"] = os.path.abspath(args.preview)
        print("preview:", args.preview)
    print("Next: set the lights to these multipliers, render ONCE, then run --verify to report the prediction error.")
    return result


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        result = run(args)
    except InputError as exc:
        sys.stderr.write("ERROR: %s\n" % exc)
        return 2
    first = (args.passes[0].split("=", 1)[1] if args.passes and "=" in args.passes[0] else ".")
    out = args.out or os.path.join(os.path.dirname(os.path.abspath(first)),
                                   "light_mix_verify.json" if args.verify else "light_mix_result.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
    except OSError as exc:
        sys.stderr.write("ERROR: cannot write %s (%s)\n" % (out, exc))
        return 2
    print("result: %s" % out)
    return 0 if result.get("pass", True) else 1


if __name__ == "__main__":
    sys.exit(main())
