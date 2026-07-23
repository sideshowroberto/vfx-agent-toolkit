---
name: previs-anchor-keyframes
description: Generate photoreal anchor keyframes from CG previs for reference-guided video generation (Seedance-class models). Covers previs shading for AI readability, anchor frame selection, bootstrapping action-pose reference sets from a single reference, lighting-accurate prompt language, and validation. Use when converting previs/CG animation to photoreal video, preparing anchor/reference frames for a video model, or when generations ignore CG placement or pose. Triggers on "anchor keyframes", "anchor frames", "previs to photoreal video", "reference frames for video gen", "generations not following the CG".
allowed-tools: Read,Write,Bash
---

# Previs Anchor Keyframes

Reference-guided video models (Seedance 2.0 and similar) stay dramatically
closer to a CG previs when you feed them photoreal ANCHOR KEYFRAMES: still
images generated from previs frames at key story beats, supplied as image
references alongside the driving video. This skill is the production recipe
for building anchors that actually match the CG.

The pipeline: previs render (driving video) -> image-model edits of selected
previs frames (anchors) -> video model in reference mode (driving video +
anchors + prompt).

---

## 1. Shade the previs for AI readability

Image and video models follow the CG far better when they can read its form:

- **Wireframe-over-clay shading** on the CG subjects beats flat silhouettes.
  A black or unlit subject only constrains outline - the model invents form,
  orientation and lighting. Wireframe lines communicate topology and pose.
- **Tint the subjects a flat saturated color** (e.g. red) when they risk
  blending into the environment (grey subjects on concrete). Then name that
  color in the prompt: "replace the red CG horse with..." - it gives the
  model an unambiguous edit target.
- Keep the environment photoreal if you have it (projected plate or stills);
  the contrast between "obviously CG subject" and "finished environment"
  focuses the edit.

## 2. Pick anchor frames at event beats

- Anchor at each subject's first CLEAN appearance (fully in frame), plus the
  moments the composition changes (second subject enters, action peaks).
- The shot's first frame works as a no-cost anchor if it is empty of
  subjects: use the raw plate/render directly - it pixel-locks the
  environment.
- **Never anchor on a frame where a subject is partially out of frame.**
  Image models refuse half-objects at frame edges and "complete" them into
  full subjects in the wrong place - repeatedly, regardless of prompt
  language. Slide to the nearest fully-entered frame instead.

## 3. Build an action-pose reference set

The single biggest cause of generations ignoring the CG pose: **reference
images whose pose or orientation contradicts the shot action**. One standing
reference will pull every generation toward standing, even over an obviously
mid-stride CG input.

Fix it by bootstrapping more references with the image model itself:

1. Crop the best correctly-oriented reference you have (e.g. the one
   rear-view image on a character sheet).
2. Generate a pose set from it: "this exact same [subject], photoreal, full
   body, mid-[action] pose seen from [the shot's viewing angle], plain
   neutral grey background, soft even lighting". Make several: direct rear,
   three-quarter rear, a different phase of the motion cycle.
3. Feed the winners (2-3) plus the original crop as references for the
   anchor generations.

Run one **reference-free control** generation early: it shows what the base
model does alone. Expect correct-ish pose but identity drift (generic
subject, wrong markings) - that is the evidence for keeping references.

## 4. Prompt structure for anchor edits

Template (adapt bracketed parts):

    The first image is a film plate of [scene] with [N] [color] wireframe
    low-poly CG [subjects] [doing action]. The other images are references
    of the exact same photoreal [subject] in [action] poses. Replace the
    [color] wireframe CG [subjects] with this photoreal [subject], seen from
    [angle] as they [action], matching each wireframe's exact placement,
    scale, silhouette and mid-[action] pose - do not move them, do not add
    or remove [subjects], do not turn them sideways. Lighting: [describe the
    ACTUAL plate lighting]. Keep everything else in the first image exactly
    unchanged. Photorealistic, seamless integration.

- State the subject COUNT explicitly and per-frame ("there are two...").
  Wrong counts are a common failure, and leftover multi-subject prompt text
  from a previous frame will happily conjure extra subjects.
- **Describe the lighting the plate actually has.** If the ground is in open
  shade lit by bounce, say so and ask for "soft, very diffuse contact
  shadows - no hard-edged cast shadow". Defaulting to "sunny day" language
  makes the model paint fake hard shadows that fight the plate.

## 5. Validate before spending on video

- Check pose, orientation, count, placement against the CG frame.
- Zoom the contact points: feet/wheels grounded, shadow direction sane.
- Expect the anchors' BACKGROUNDS to drift slightly per generation (signage
  text mutates) - anchors are identity/placement guides only; the driving
  video owns the environment. Never let comp reference anchor backgrounds.
- Model choice is empirical per shot: strict-silhouette models track the CG
  literally but may integrate worse; looser models integrate beautifully but
  hallucinate. Generate one benchmark frame on each candidate before
  committing the set.

## 6. Send to the video model

Reference mode: driving video (the previs render) + the anchor stills as
image references + a motion prompt that reuses the anchor language and adds:
"keep the camera motion and the environment exactly as the input video",
plus the subjects' entry order/timing. Run a cheap low-res pass first;
re-run at delivery res only after the look is approved.

Watch for: entry timing vs the CG schedule, footfall/contact sync (retime
tricks apply if the action floats), temporal stability of signage, popping
at frame edges.

## 7. Match the model's aspect ratio (applies to everything above)

Generation models output standard aspects only — 1:1, 3:4, 4:3, 16:9, 9:16.
If your plate/render aspect is non-standard (full-aperture formats often
are, e.g. ~1.46), the model resamples the input to its grid and the whole
background SHIFTS subtly in every output. It looks like model drift; it is
resampling.

- Pick the nearest standard aspect and reformat the INPUT to it before
  generating, fitting by the dimension whose framing must stay locked
  (usually width). In a 2D app, that means letterboxing and cropping the
  bars off afterward. When rendering from a 3D scene, skip the letterbox:
  enlarge the render canvas to the standard aspect with the camera set to
  horizontal sensor fit — horizontal framing stays identical and the extra
  rows are real scene content, which gives the model better context than
  black bars.
- Set the generation tool's aspect parameter to the SAME aspect so input
  and output grids agree.
- Record the crop-back fraction (extra rows / canvas height) at setup time;
  it applies at any generation resolution.

---

## Pitfalls quick list

| Symptom | Cause | Fix |
|---------|-------|-----|
| Subjects standing/static | Standing/wrong-pose references | Bootstrap action-pose ref set (sec. 3) |
| Subject faces wrong way | References face the wrong way | Only use refs matching the shot's viewing angle |
| Half-entered subject becomes full | Frame-edge completion behavior | Do not anchor partial-entry frames |
| Wrong subject count | Count not stated / stale prompt text | State count per frame, rewrite per anchor |
| Hard fake shadows | Generic sunny-day prompt language | Describe the plate's real light; ask for diffuse shadows |
| Generic-looking subject | No/weak identity references | Keep character refs; run ref-free control only as a test |
| Anchors disagree with each other | Independent generations drift | Expected; anchors guide subjects only |
| Background shifts subtly in every output | Input aspect is non-standard | Reformat to the nearest standard aspect first (sec. 7) |

---

## Version History

**v1.1.0** (2026-07-23)
- Added aspect-ratio matching section (sec. 7) + pitfalls row: non-standard
  input aspects cause background shift via resampling

**v1.0.0** (2026-07-23)
- Initial release: production-validated recipe (previs shading, anchor
  selection, reference bootstrapping, lighting-accurate prompting,
  validation, video-model handoff)
