# Contract authoring - what the human settles before iteration one

SKILL.md lists the five contract items. This file holds the long bodies:
how to prepare the reference set, what to check in the spec, and which
subjects a capped loop should be given at all. Everything here is an
authoring step: it costs minutes before the loop and saves iterations
inside it. The recurring shape is the same one the skill is built on - an
instrument or convention the comparison cannot see must be stated by the
human and read back as a value.

## 1. Plan and layout drawings are measuring references, not views (obs 59)

A plan, section, elevation or layout drawing has no camera. Left in `views`
it is scored on lighting and materials, which are meaningless for a diagram;
left out it is decoration. Matched hero views alone never constrain
circulation, so a builder can score 4 on every view and still have built a
plan nobody approved. Treat the drawing as a MEASURING instrument:

1. **Dimension table.** Before iteration one the human measures the drawing
   (radial or axis-aligned pixel scans are enough) into a table of
   proportions and fixes the scale with ONE human-stated real-world anchor
   (for example "corridor clear width 4.5 m"). Every other number follows
   from the anchor and the pixel ratios. The table goes into the brief as
   facts; the builder does not re-derive it.
2. **Plan conformance in the rubric.** Add it to the `constraints` criterion
   with a numeric tolerance (within 2 percent of the table), and require the
   per-row numbers read back from geometry bounding boxes each iteration,
   not eyeballed.
3. **Orthographic final.** Require a final render in the SAME projection as
   the drawing (top, front), compared against it, with the per-row
   measured-versus-table error printed.

A view reference is matched by a camera and judged by eye; a plan reference
is measured into numbers and judged by read-back. Mixing the two is how a
loop converges on pictures that are right and a building that is wrong.

## 2. A generated "orthographic" elevation still carries perspective cues (obs 114)

An AI-generated image labelled orthographic is a hypothesis about the
camera. It can show things no orthographic camera can: a bright band above a
ledge (really its top face), a glossy floor band, a base that sits lower
than the wall beside it. A first pass that reads the ledge band as its front
face puts everything above it measurably high in the edge overlay; reading
it as a 45 degree top chamfer put the same edges within 1 px a few
iterations later, while the floor band and the lowered base stayed
unmatchable by construction.

Before any number from such an image becomes a dimension:

- List every horizontal and vertical band.
- Classify each as **geometry** (a chamfer, return, reveal - a real surface
  an orthographic camera would see) or **projection** (a top face, a floor,
  a receding jamb - only visible in perspective).
- Record the verdict in that view's `notes` in the spec. Dimensions come
  only from geometry bands; the scorer is told which edges are
  projection-only so they are not counted as misses.

## 3. Preparing a lead-supplied reference set (obs 91)

When the lead's agent gathers references instead of the builder finding
them, the folder is part of the instrument: anything the builder can open,
it may treat as truth. Curate by allowlist, never by directory listing.

- **Allowlist the context images.** Research folders hold rejected downloads
  next to kept ones (wrong variant, wrong format, an adjacent listing). On a
  no-delete share a stray file cannot be removed, so copy ONLY the kept files
  into the builder's context folder and add a `USE_ONLY.txt` naming them.
- **Crop hand-held photos to the object.** When the only photo is an event
  or hand-held shot, the matched view is a fractional crop of it (pick it on
  a gridded thumbnail board) and the view `notes` say hands and people are
  not part of the object.
- **Pad to the render aspect in the photo's own colour.** `compare_views.py`
  letterboxes a reference with black bars; a square-padded copy using the
  photo's border colour avoids the aspect cap in section 4 and a black bar
  the render cannot match.
- **Client-supplied images are legitimate views.** A client deck's own
  render or clean close-up is often a better matched view than any web photo.
- Keep a `SOURCE.txt` with provenance (file, origin, crop box) next to the
  prepared refs.

## 4. Aspect check: a reference whose aspect differs from render_size caps the view (obs 61)

`compare_views.py` letterboxes each reference into `render_size` and refuses
to stretch it. If a reference is 2.26:1 and `render_size` is 1.79:1, the
reference content fills about 79 percent of the frame height while the
render fills all of it, so edge alignment cannot reach its target. One run
saw `edge_iou` sit flat across four iterations, including two where the
builder refit the camera, while aspect-matched views climbed on the same
work. Nothing warns: the comparison looks normal at panel size.

Authoring check, for every view before the loop starts:

- Compare the reference aspect (after `crop`) with `render_size`.
- Resolve a mismatch: crop the reference with the `crop` field, set
  `render_size` to the references' aspect, or pad the reference (section 3).
- If it must stay, state in the view `notes` that the render must match the
  LETTERBOXED reference: the content lands in the central band, and the extra
  rows above and below are correct, not a miss. Fix only the horizontal
  framing; a pinhole camera at a fixed render size ties vertical field of
  view to horizontal through the aspect, so "widen the vertical field of
  view only" is impossible.

`compare_views.py` prints each view's reference aspect against `render_size`
and sets a `ref_aspect_mismatch` flag in the readback next to
`suspect_blank`. Treat the flag as a cap announcement, not a builder failure.

## 5. Up axis and units are stated by the human (obs 60)

"Report which up axis you used" is not a specification: it guarantees only
that a wrong choice will be wrong everywhere. The rendered comparison cannot
catch it either - a scene built on the wrong axis, seen through a camera
built on the same wrong axis, is pixel-identical to a correct one. The cost
lands downstream (USD or Alembic arrives on its side in the next package).

- Put one line in the brief's hard constraints, written by the human:
  "+Z is up, metres" (Blender), "+Y is up, floors in XZ, metres" (Houdini),
  "+Z up, centimetres" (Unreal).
- Put the same facts in the spec's optional `scene` block:
  `"scene": {"up_axis": "+Z", "units": "m"}` with `up_axis` of `+Z` or `+Y`
  and `units` of `m` or `cm`. Defaults when the block is absent: Blender
  `+Z` / `m`, Houdini `+Y` / `m`, Unreal `+Z` / `cm`. The prompt generator
  reads this block, so the generated ground rules state the axis for the DCC
  actually in use instead of one fixed wording.
- Add the axis to the iteration-one read-back list and check it as a value:
  a wrong axis found at iteration one costs nothing; found by the lead two
  iterations later it costs the operator-note round trip.

## 6. Repeated-element hero views: solve before iteration one (obs 65)

When a matched view shows a regular repeated element on a circle or a line
(niches, columns, ribs, windows), equal elements at known ratios
over-determine the camera and the room. Tabulate landmarks and solve radius,
pitch, camera distance, focal length and horizon BEFORE building, then
record the solve in the brief. Method and code live in the DCC pattern files
("fit before render"); the authoring rules are:

- Fit every measurable of the element - centre, height AND width; the
  foreshortening carries the wall angle. A fit on centres and heights alone
  agreed with its own verifying instrument for eleven iterations while the
  edge elements were 21 percent too narrow, because the instrument measured
  only what the solve had fitted.
- Verify with an instrument that measures something the solve did NOT fit,
  and keep one plain full-size reference-over-render look every few
  iterations beside the 5-panel.
- Include every major line the rubric scores (opening edge, wall-to-ceiling
  line) in the fit. A fit from the repeated elements alone can put a scored
  feature off-frame.
- When the lines cannot all fit one camera, report the trade-off with a
  render per candidate camera instead of choosing silently. Two findings the
  human must settle if a solve returns them: a camera position outside the
  room, and a plan feature that cannot be hidden from the view.

## 7. Which subjects to loop (obs 92)

A capped loop converges only where its tools can express the form. Decide
the subject's class, and therefore its route, before spending iterations.
Evidence: a production run of two dozen objects at a cap of 6 split cleanly
by class.

| Subject class | Route |
|---|---|
| Turned, lathe, extruded, bevelled forms; lettered or engraved hard surfaces | Loop. A cap of 6 is enough for a stand-in; these reached near-final in about 6 iterations. |
| Relief on a panel | Loop, with a depth-map displacement step named in the brief (a local monocular-depth model costs nothing). |
| Organic bodies (gloves, cloth, figures) | Generate the base mesh BEFORE the loop (best single-image route measured: an image-to-3D service; a local TRELLIS-class model for cloth drape), then loop only on placement, scale and the hard parts around it. A looped organic build stayed flat in self-score and generated attempts failed the builder's own shape checks. |
| Parts no photograph shows | State the assumption in the brief AND flag it in the verdict. Never score it as matched. |

In stand-in (grey-pass) mode every leg stops at the cap and none stalls:
the cap, not the rubric, is the intended stop, so a MAX_ITERATIONS stop is
not a failure (see SKILL.md, Stand-in / grey-pass production mode).

## 8. Lighting contract (obs 116, 117)

- **Feasibility pre-check, traced.** "Key light can reach the lit surface"
  (normal dot light) is necessary, not sufficient. For each lit EVENT the
  reference shows (floor patch, wall streak, beam, glow, bright opening),
  ray-cast its pixels to world points, then trace toward candidate light
  directions through the real openings (both rim heights of an opening with
  depth). Project each opening into the camera so you know which part is on
  screen. Record, before iteration one, the set of directions that can reach
  each event. If the sets do not intersect, decide then which events get
  their own light (same colour and intensity, nearest feasible direction):
  a painted reference is not obliged to have one sun. Fit each spot's aim
  and cone to the event's mask (footprint IoU) instead of eyeballing a cone
  angle, and store the fits as read-back JSON with an overlay image. An
  unshaped sun through a large opening lights a footprint far larger than a
  painted patch, and a cone angle can change meaning between the DCC and the
  USD that carries it - check the footprint on the render.
- **Targets: boxes measure balance, features measure placement.** A small
  mean-luminance box can agree with the target for many wrong pictures: one
  run matched ten of ten boxes while the brightest feature was dim, grey and
  in the wrong place. Add a `lighting_target` block to the spec: `boxes` for
  the overall value balance, and one `features` entry per named lit event
  with a check that FAILS when the event is missing or misplaced - the
  centroid of the brightest 1 percent of pixels against the reference's, the
  event's mask IoU at a stated threshold, or the event's peak and its
  contrast to an adjacent background box; for a thin groove or seam, its
  contrast against its flanks as a ratio of the reference's. A box is never
  the only evidence for a named event. Each per-view entry of the block has
  the boxes-JSON shape `scripts/scratch_luminance.py` reads with `--boxes`
  (normalised 0-1 coordinates), so it can be saved out as that file. The
  method, the free scratch tooling and the light solver are in
  `reference/lighting_match.md`, `scripts/scratch_luminance.py` and
  `scripts/solve_light_mix.py`.

## 9. Rubric instruments - an element nothing can fail is not scored (obs 49, 66, 112)

Every rubric element needs an instrument that can FAIL. If the comparison
cannot show an element, the element is unverifiable, not verified.

- **Reflective and mirror-finish subjects: separate form from finish.**
  Dark or bright patches in a photo of polished metal, glass or gloss are
  reflections of the environment and of the object itself. Match them with
  materials and lighting, never by adding or cutting geometry. Run a grey
  clay pass of every matched view EVERY iteration and read openings and
  voids off the clay only. Both directions occur: a reflection looks like a
  hole in colour (a clay pass shows the solid), and a dark fill looks like a
  void in colour while the clay shows a solid slab. Before scoring geometry
  detail 4, read back that solid parts are continuous where the photo's tone
  changes.
- **Thin negative features** (joints, grooves, seams, panel gaps, inlays)
  need their own named part and their own grey in the value study, chosen so
  the contrast against the neighbour is of the same order as in the
  reference. Geometry that is correct but rendered in the same grey as its
  neighbour dips about 2 levels out of 255 and cannot be verified. In the
  scratch-render step, sample the render across the element at its expected
  position (a column- or row-averaged profile is enough), log that contrast
  next to the reference's, and report an element whose render contrast is a
  small fraction of the reference's as "not visible" up front.
- **Unscored survey cameras for spaces no reference covers.** Matched views
  verify the frames, not the scene. When the scene is the deliverable, add 3
  to 5 survey cameras (one per uncovered zone plus an aerial) and look at a
  scratch sheet of them every 3 to 4 iterations. They are never scored; they
  find defects no metric sees (a mass breaking through a wall, towers
  rendered default white for a dozen iterations because of an empty material
  slot, an element explained away by the lighting).
- **An element counts only when a pixel or a ray shows it.** For anything
  the build log claims present, cast a ray from the camera and name the
  object it hits. A window scored present for five iterations from the log
  was a sealed cavity behind a wall.
- **Gate the iteration render on the geometry read-back.** The render step
  runs the geometry checks itself and refuses to render on a fault. Never
  chain build and render in one call without that gate: the evidence rule
  forbids overwriting a burnt tag, and a re-run costs an iteration number.

## 10. Sizing the stop rule (obs 63)

A stop counted in iterations is only a proxy for the budget that actually
stops the run.

- Estimate cost per iteration for the SUBJECT CLASS before launch. Measured
  on one Codex-class runner: roughly 30k tokens per iteration for a prop,
  roughly 75k for a whole architectural environment (826k by iteration 11 of
  a cap of 15, ending on the account usage limit with no finals made). Check
  the estimate against the runner's remaining budget (tokens or credits for
  Codex, USD for a Claude leg), set `max_iterations` to what the budget
  affords, and record BOTH numbers in the bench record as run conditions. A
  run that cannot afford its own cap is mis-specified before it starts.
- **Deliverables floor.** Name the artefacts the run exists to produce and
  require them at a stated iteration: a first full set of finals at the
  halfway point, refreshed if the loop continues, so an interrupted run
  still hands over what it was for. Never leave the deliverable behind the
  last iteration of a run whose end you do not control.
- **Resume document.** `RESUME.md` in the working folder names the last
  saved scene, the last logged iteration, any half-finished iteration and the
  open items, so a stopped run can be continued by another session.
