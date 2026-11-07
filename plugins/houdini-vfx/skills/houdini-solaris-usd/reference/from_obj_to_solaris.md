# From /obj to Solaris - defaults that wake up in the new context

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Moving an /obj scene into LOPs for Karma passes. Each item was found by a read-back, not by looking at the image.
Common principle: a default that was harmless in the old context (a camera f-stop never rendered by OpenGL, packed
prims never instanced in SOPs) becomes active in the new one. Read back the attributes the new renderer consumes
before judging a render. Measured on Houdini 21.0.596.

---

## 1. Imported cameras carry depth of field

**Rule:** for grey or reference passes, set `enabledof` off on the Karma Render Settings (or zero the camera fStop)
and read `fStop`, `focusDistance` and `enabledof` back from the stage.

**Why:** Scene Import carries the Houdini camera defaults (f-stop 5.6, focus 5 m) into USD and Karma Render Settings
has `enabledof` on by default. A subject 19 m away came out soft all over, while the /obj OpenGL pass of the same
camera was sharp, so nothing pointed at DOF until the attributes were read.

---

## 2. SOP Import makes packed prims native instances: bind materials at an ancestor

**Rule:** assign materials on the ancestor prim, not on `/root/**`, then verify with `ComputeBoundMaterial` over
`Usd.TraverseInstanceProxies()` (count unbound; expect 0).

**Why:** Assign Material with a `/root/**`-style wildcard errored "authoring to an instance proxy is not allowed"
and broke every node downstream. Binding at the ancestor bound 14,547 meshes including instance proxies. Unpacking
before the import is the other route.

---

## 3. Hundreds of lights from SOP points

**Rule:** Instancer LOP, method Reference, Location Source External SOP, Set Orientation from N/up, prototype from
the first input (it needs a Prototypes area). The instancer aims +Z along N while a USD light emits down -Z, so the
prototype light needs a 180 degree flip (a Transform LOP on the light under an Xform rig).

**Check:** read back that the instances are visible and the source prototype and the Prototypes copy are invisible,
and that every light's world -Z agrees with its point N (measured within 1e-5 degrees over 396 lights).
`node.stage()` returns None until the LOP has cooked.

---

## 4. A spot light needs its "Spot Light" toggle

**Rule:** turn on `spotlightenable` on the Light LOP and read `inputs:shaping:cone:angle` back from an instance
before judging any render.

**Why:** the cone and softness parms are written only when the toggle is on. With it off the UI still shows 15 degrees,
no ShapingAPI is applied, the attribute is not authored (reads None) and every "spot" renders as an unshaped sphere
light. Two review renders went out that way. The tell: a grid where aim and cone changes left the image unchanged
(mean abs diff 1.2 levels, which is noise).

---

## 5. Camera LOP and render settings values are time samples

**Rule:** read Camera LOP lens values and the Karma render settings resolution at `Usd.TimeCode(hou.frame())`, never
at default time (see stage_readback.md). The Camera LOP aspect comes from `aperture` = setratio (aspectratiox / y),
which overrides a typed vertical aperture.

**Why:** a default-time read showed the schema fallbacks (focal 50, vertical aperture 15.29) and a render product of
2048 x 1080 while the settings prim at the current frame held 768 x 527.

---

## 6. Many-light stages: cost is the lights, and instrument before tuning

- In the Karma XPU viewport the cost of a stage with hundreds of lights was the LIGHTS, not the geometry. A grain
  metric (mean abs horizontal pixel difference over floor and wall regions, fixed 20 s settle) read 4.52 for the full
  stage, 4.44 with props pruned (3634 meshes) and 2.14 with the 484 spot lights pruned, which equalled the full stage
  at 60 s. The metric was validated first: two 20 s captures read 4.47 and 4.52, a 60 s capture 2.22.
- Recipe for interactive lighting: a Light Mixer in the final chain (collections made on /lights beforehand), then a
  preview branch = Prune (deactivate) of the many-light group, bypassed to restore, followed by a copy of the final
  Karma settings at lower resolution with the display flag there.
- Tuning aims by render grid cost about 2 min per full-scene render and once returned noise. A cone-ray coverage
  instrument (a Python replica of the light placement, checked against the real output to 1e-6 m, casting each cone's
  rays at tagged geometry and counting landings and rays that clip within 12 cm of the source) scored a layout in
  seconds; renders on a one-item template stage with everything else pruned (31 s) only confirmed the winner.

See karma_lights.md for sphere-light radius and cone half-angle facts, and verification_instruments.md for the
control and noise-floor rules.
