# Lighting match - a DCC-independent method

Lighting is where reference-match loops burn iterations: every light reaches
every measured region, so trimming them one at a time by eye only moves the error
around. This page is the method, in the order you use it. It applies to any
renderer; the DCC-specific part is only how you isolate a light group and how
you read back what you set (see your DCC's pattern file).

Scripts (all in `scripts/`, numpy + Pillow, `--help` on each; OpenEXR is optional
and only needed to read .exr passes):

| Script | Job |
|---|---|
| `scratch_luminance.py` | per-box mean luma vs reference, brightest-1% centroid, per-event feature checks, blank gate |
| `solve_light_mix.py` | additivity check, non-negative least-squares light mix, post-render prediction check |
| `test_lighting_scripts.py` | offline self-test with synthetic images (run it after any edit) |

Exit codes for both tools: 0 ok, 1 measured but outside tolerance (JSON still
written), 2 input error. Read the JSON, not just the exit code.

## 1. Feasibility trace - before iteration 1 (contract step 2)

"The key light can reach the lit surface" (normal dot light) is necessary, not
sufficient. A painted or composited reference is not obliged to have one sun.

1. List every lit EVENT the reference shows: a floor/ground patch, a wall
   streak, a beam, a glow, a bright opening, each practical.
2. For each event, ray-cast its pixels from the matched camera to world points
   (scene intersect in the DCC, using the solved camera).
3. From those points trace toward candidate light directions THROUGH the real
   openings - both rim heights of an opening that has depth. Project each
   opening into the camera as well, so you know which part of it is on screen.
4. Record, in the spec before iteration 1, the set of directions that can reach
   each event. If the sets do not intersect, decide NOW which events get their
   own light (same colour and intensity, nearest feasible direction). A fit for
   one event alone can send its beam across a region the reference keeps dark.
5. Size matters as much as direction: an unshaped sun through a large opening
   lights a footprint the size of the opening, not the painted patch. Fit each
   spot's aim and cone to the event's MASK (footprint IoU), never by eyeballing
   a cone angle, and read back what the renderer actually received - a DCC cone
   parameter can arrive in the renderer as a different angle (one did, and lit
   the whole visible floor). Check with the group's isolation pass (section 5).
6. Store each fit as a read-back JSON plus an overlay image in the readback folder.

## 2. Value study - greys that survive the instrument

Give every rubric element a grey chosen so its contrast with its neighbour is of
the same order as in the reference. Thin NEGATIVE features - wall joints, grooves,
seams, panel gaps, inlay or engraved lines - get their own named part and their
own (dark) grey: geometry that is correct but shaded like its neighbour is
invisible to the comparison, and an element the instrument cannot see is
unverifiable, not verified. Before the iteration render, sample across each such
element (a column- or row-averaged profile is enough) and log its render
contrast next to the reference's. `scratch_luminance.py` does this with a
`"kind": "line"` feature; a ratio under `min_ratio` (default 0.25) prints
"NOT VISIBLE" up front instead of letting the scorer discover it.

## 3. Lighting targets - boxes for balance, features for placement

The spec's lighting target has TWO parts, because a small mean-luminance box can
pass by coincidence and hide a feature that is wrong or in the wrong place:

- **Boxes** (8-12, normalised 0-1, covering the darkest to the brightest regions)
  measure the overall value balance: mean luma 0-255, measured on the reference
  with the same instrument as the render (PIL "L" on 8-bit sRGB, same crop and
  letterbox as `compare_views.py`). Typical tolerance 12 luma.
- **Feature checks**, one per NAMED lit event, measure placement and shape:
  brightest-1% centroid of the whole frame (default tolerance 0.10 of the image
  diagonal), mask IoU of the event inside a search box, peak (99th percentile)
  and peak-minus-background contrast, and the line check from section 2.
  A box is never the only evidence for a named event.

```json
{"boxes": {"floor_left": [0.05, 0.70, 0.30, 0.95],
           "opening":    {"box": [0.40, 0.00, 0.60, 0.10], "target": 113, "tolerance": 15}},
 "features": [
   {"name": "bright_opening", "kind": "patch", "box": [0.35, 0.00, 0.65, 0.20],
    "mask_threshold": 155, "min_iou": 0.3, "peak_tol": 25,
    "background_box": "floor_left", "contrast_tol": 25},
   {"name": "wall_joint", "kind": "line", "box": [0.074, 0.20, 0.078, 0.80],
    "flank": 0.02, "min_ratio": 0.25}],
 "global_target": 95.4}
```

## 4. Scratch-measure before every iteration render

Any light, world, exposure, view transform, emission or haze change is
scratch-rendered for ALL matched views at reduced samples and READ before the
iteration tag is spent. A lighting value is a guess until a scratch frame has
been measured against the reference; measure first and the iteration render
becomes a confirmation instead of an experiment.

```
python scratch_luminance.py --render scratch03_hero.png --reference ref_hero.png \
    --boxes lighting_boxes.json --tolerance 12 --out readback/scratch03_hero_luminance.json
```

Rules that came out of skipped scratch tests: world light is global - it pours
through every opening, so in a scene that mixes an enclosed room with open
corridors keep the world low and fill zones with local area lights; give the
camera its own dim sky (camera-ray-only sky in the renderer) so visible sky does
not dominate the luminance read of an exterior-facing view. Check the instrument
too: the tool's blank gate (fewer than 8 distinct grey levels) and the file size
and pixel size it prints are part of the evidence.

## 5. Solve the mix from isolation passes (instead of trial renders)

A path tracer is linear in emission, so a mix renders as the sum of its light
groups, each scaled by its intensity. Measure each group's contribution once and
solve; do not trial-and-error.

**Render.** One pass per light group, that group ALONE, everything else off
(other lights, world light, emissive practicals unless they are their own
group). Same camera, resolution, samples and seed; linear float (EXR or .npy);
no view transform; denoiser off, or the same setting as the all-on render and
expect a little noise. Typical groups: key (sun/spot), sky fill, "fixed" (the
camera-visible sky plus emissive practicals), bounce card. If the scene has haze
or a volume, keep it ON in every pass (it scatters each light linearly) and add
a haze-free twin of each pass; the haze density then becomes a variable too. A
renderer with light-group outputs can give all passes from one render; the checks
below are identical. Look at every pass: a group that lights the wrong region
(a "spot" that floods the floor, a beam crossing the wrong box) is a structural
fault no weight can fix, and the pass shows it at once.

**Additivity check first - the instrument check.** Render ONE all-on frame at the
nominal intensities; the passes mixed at those weights must reproduce its box
values.

```
python solve_light_mix.py --pass key=key.exr --pass sky=sky.exr --pass fixed=fixed.exr \
    --all-on allon.png --reference ref_hero.png --boxes lighting_boxes.json \
    --additivity-tol 2 --out readback/light_mix.json
```

Default tolerance 2 luma; a healthy setup measured 0.2 to 1.1. Add
`--clear NAME=PATH` (every group) when a volume is present. If the all-on render
used other weights, say so (repeat the flag per group, `k=1.2` for haze):
`--all-on-weights key=0.5 --all-on-weights k=1.2`. While
additivity fails the JSON says `"trusted": false` and the exit code is 1 - do not
act on the weights.

**Solve.** The same command solves: non-negative least squares on linear box
means (each row scaled so a linear residual approximates the encoded-luma
residual the score uses), optional global-mean row, haze multiplier k when twins
are given, `--fix NAME=W` to hold a value, `--per-channel` for colour,
`--fit-space encoded` to polish on the true encoded residual. Read the printed
table: predicted vs target per box, what each group contributes to each box, the
condition number (large = the boxes cannot tell two groups apart), and the
warnings. A group the solver drives to weight 0 is a diagnosis, not a result:
double-sided, blocked, mis-linked, or simply not needed - find out which.

**Apply and verify - one render.** Set the lights to the solved multipliers and
READ THEM BACK before launching (an edit that failed inside a parallel batch once
let a render go out with the old value). Render once, then:

```
python solve_light_mix.py --pass key=key.exr --pass sky=sky.exr --pass fixed=fixed.exr \
    --verify iter03_hero.png --weights-from readback/light_mix.json
```

Report the prediction error (predicted vs rendered box luma) in the iteration log.
In the run this method came from, one solve predicted the iteration render within
about 3 luma (1.1 to 2.8 over three renders) where five trial scratch renders had
not converged. Default `--verify-tol` is 4. A larger error means a fault in the
passes, the all-on state or the applied values - go back to the additivity check,
do not iterate on the weights.

## When additivity fails

| Symptom | Likely cause | Check / fix |
|---|---|---|
| Small, near-uniform error in every box | tone curve or view transform on the PNG, exposure, 8-bit clip | compare linear EXR to linear EXR, or set the identity view transform; confirm the PNG is plain sRGB |
| Error concentrated in a few boxes | a light is not truly isolated (emissive geometry, world light, light linking, a default dome) | render ALL OFF: it must be black or a known fixed term; assign the leftover to a group |
| Noisy differences | denoiser on in one render only, different samples or seed | same denoiser, samples, seed for passes and all-on |
| Passes sum brighter than all-on | indirect clamp, firefly filter, adaptive-sampling threshold, caustics differ | make the render settings identical; clamps are not linear in emission |
| Sum darker than all-on | a light present in all-on but in no group | list every light/emitter; each belongs to exactly one group |
| Error grows with intensity | the light knob is not linear energy (exposure stops, normalise toggles) | render one group at 2x; it must equal 2x its pass |
| Only hazed frames fail | haze/volume state differs between passes and all-on | keep the volume identical; use haze-free twins |

Until the check passes the solve is a guess in a nicer format.
