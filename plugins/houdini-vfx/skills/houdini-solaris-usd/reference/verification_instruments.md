# Verification instruments for Solaris and Karma work

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Instrument faults found while verifying lighting and review renders, each caught before a wrong claim went out.
Common principle: when an instrument says "nothing", find out whether it could have seen anything - include every
parameter of the projection, prove light and camera separately, run a positive control through the same path, and
start every timing from the same state. Measured on Houdini 21.0.596 (Karma XPU).

---

## 1. Project into a USD camera with its aperture offsets, and score samples, not centres

**Rule:** to test whether a surface is visible from a stage camera, project every sample point with
`horizontalApertureOffset` / `verticalApertureOffset` applied, and test each sample in frame. Report both "in frame
with the offsets" and "visible from the camera position, any framing"; they are different numbers.

**Why:** filtering by object centre dropped the close-up cameras (centre off screen, light on screen) and all 12
crop cameras (they use aperture offsets). Per-sample scoring gave 0 visible on every existing camera and 282 of 592 on
the review camera. The missing close-up camera in the results was the tell.

---

## 2. A hit rule must not depend on the angle

**Rule:** a ray-visibility rule is "the first hit is that surface and no nearer than the tolerance before the target",
not "hit within N mm of the sample".

**Why:** a ray offset 1 mm along the normal travels offset / cos(angle) further at grazing angles, so "within 3 mm"
rejected rays that did hit (18 of 1,260 passed; the angle-free rule gave 1,221). Earlier "0 visible" results at oblique
views could have been undercounts. The control point caught it.

---

## 3. Weight a lighting instrument by camera visibility

A 2D section instrument chose a design change by the share of a light landing ON a wall (+44% at a 45 degree tilt).
Built and rendered, the stage cameras showed the wall no brighter (line peak 118 -> 112). A camera placed inside the
niche showed the gain was real (148 -> 200) but sat in the first few cm behind the lip, which no stage camera sees.
Weight by camera visibility, or render the stage cameras on a quick test, before building on the number.

---

## 4. A black Karma render: split it with a known-good light and an inside camera

**Rule:** render an exported copy of the stage with a dome light added, and a copy with the camera beside the light,
before changing the light.

**Why:** a template rig rendered pure black in viewport and in husk (XPU and CPU) with a correctly authored light. A
dome made the frame grey (camera and geometry fine); a camera inside the niche saw the light glow (light fine); the
dome render then showed a wall across the opening - a preview-wall boolean that had stopped cutting two asset versions
earlier. Without the split, four test renders of the obvious suspects changed nothing.

---

## 5. Viewport cost comparisons: recook, restart the delegate, then settle

**Rule:** after a change, let the stage recook, restart the Hydra delegate (switch renderer and back), then time a
fixed settle. The first capture otherwise includes the recook and the first IPR passes (grain 30.9, void). Measured
afterwards: 12.4 vs 0.49.

---

## 6. A parameter that exists is not proof the renderer honours it

**Rule:** when a light parameter "does nothing", run a positive control through the SAME authoring path and a repeat
baseline for the noise floor before concluding.

**Why:** on a Geometry Light, Spread 0.1 changed the frame by mean abs diff 0.62, USD shaping focus 30 by 0.61, and
two identical baseline renders differed by 0.61 (noise). A control through the same override layer (exposure 4 -> 2)
changed it by 19.2, so the override reached the light and the shaping attributes were ignored (see karma_lights.md).

---

## 7. A viewport screenshot reads the darks low

**Rule:** before comparing shadow levels or contrast with a reference, stash the viewport render's C once (Slap Comp
Import COP -> ROP Image, raw EXR). Compare a plain sRGB encode of it with the capture, binned by linear value; if the
bottom bins differ, quote darks from the data. Settle which a final render matches with a husk render of the same
frame.

**Measured:** linear 0.0057 read 7/255 in the capture against 17 from the data, 0.0114 read 21 against 28, and from
about 0.04 up they agreed (about 0.003 linear lower). A husk render of the same frame matched the render DATA in every
linear bin from 0.003 up (ratios 0.96 - 1.04, whole-frame mean 0.0992 vs 0.1002), so the screenshot is the instrument
that is off.

**Aspect trap:** the viewport render covers the VIEWPORT aspect (2304 x 1582 here, aperture expanded); the camera's
16:9 frame is only the centre 1296 rows. Stats from the capture or stash include about 18% of image outside the
camera frame; a grade tuned on them came out about 15 levels low in the highlights. Measure look stats on a husk
render, or crop the stash to the camera aspect, centred.

---

## 8. Review captures: frame with a look-at Camera LOP, light the branch

- **Framing:** the free viewport camera driven through HOM (`useDefaultCamera`, `defaultCamera().setRotation` /
  `setTranslation` / `setPivot`, `setDefaultCamera`) read back values that disagreed with what was set and took three
  tries. A Camera LOP leaf appended after the chosen branch (`t` + `lookatenable` / `lookatposition`, focalLength 18,
  fStop 0), display flag on it, `set_viewport_camera` to its prim, was exact first time and repeatable. Save and
  restore the user's display node and viewport camera around it; never drive GeometryViewportCamera by numbers.
- **Lighting:** an isolation rig lit only by the lights under test renders everything outside their reach black.
  Check the branch actually lights the region under review (a room-lit branch with the many lights and dressings
  pruned showed it in ~30 s settles).

---

## 9. Check where a procedural pattern lands with an exaggerated render

**Rule:** temporarily exaggerate the pattern (e.g. joint width 8 mm -> 60 mm, joint value 0), take one short capture,
revert the parms and read them back, then measure positions in the IMAGE alone using a symmetry the scene gives you.

**Why:** a projected-overlay check (USD frustum, view x projection) was about 40 px low vertically against the viewport
framing, which looked like a shader phase bug; the 8 mm joints were also too faint to read. With the camera on a slot
centre line, boundary joints had to straddle the centre column at +-4 and +-12 degrees (offset ratio tan 12 / tan 4 =
3.04; measured 2.99) with no joint down the middle. An overlay is evidence only after it has been checked against known
geometry in BOTH axes.

## 10. Leaving a look-through restores the wrong view (obs 179)

**Looking through a USD camera in a Solaris viewport loses the free view.** After
`viewport.setCamera('/cameras/...')` for a capture, restoring a stashed default camera
with `setDefaultCamera` and then `useDefaultCamera()` left the viewport at the CAMERA's
view: leaving look-through copies the camera into the default camera. Before switching,
record `viewTransform()` and the tumble pivot. Restore by solving rotation + translation
about the unchanged pivot (rotation passed transposed), then read `viewTransform()` back
and require a match (here 2e-6 m). Any UI state an agent changes for a capture needs a
restore path that is read back.
