---
name: nuke-particle-blinkscript
description: Verified ParticleBlinkScript and procedural-particle traps in Nuke - loads kernels via kernelFile + loadKernelFile and makes no param knobs headless, bundled Particle* gizmo params have no kernel prefix (paDirection), ParticleEmitter takes emit geo on input 1, image y points up. Use for custom Nuke particles, Particle* gizmos, or BlinkScript snow, embers, dust or sparks overlays.
metadata:
  version: 2.0.0
  updated: 2026-11-09
---

# Nuke ParticleBlinkScript - traps

Measured on NukeX 17.0v2 and the install folders here (nuke-round3 probes and evals, 2026-11-08/09;
ClaudeCode/evals/nuke-round3/ANALYSIS.md) unless a trap says otherwise. Kernel compile and knob-naming traps
for plain BlinkScript (modal compile-error dialog, kernelSource.setValue no-op, `<Kernel>_<param>`) are in
`nuke-blinkscript` - they apply to the procedural route below.

1. **A standard force is a bundled gizmo, not a new kernel.** Wrong: writing a ParticleBlinkScript kernel, or
   assuming the node is "NukeX 16+". Right: `ParticleBlinkScript.dll` and the same 14 gizmos ship in every
   install here from 12.2v4 to 17.0v2: ParticleAttractToSphere, ColorByAge, ConstrainToSphere, CylinderFlow,
   Direction, DistributeSphere, Flock, Fuse, Grid, HelixFlow, Kill, ProjectDisplace, ProjectImage, ShockWave
   (all `Particle` + name). There is no gadget-picker knob. Verify: `nuke.createNode('ParticleDirection')`
   succeeds and contains a ParticleBlinkScript node.

2. **Gizmo params have NO kernel prefix.** Wrong: `ParticleDirection_direction` or guessing from the
   BlinkScript `<Kernel>_<param>` rule. Right: the bundled gizmos expose `paDirection`, `paStrength`, ...
   Verify: read `node.knobs()` first, then read the value back after setting (e.g. paDirection (0, 1, 0)).

3. **ParticleEmitter: emit geometry goes on input 1.** Wrong: wiring a Card into input 0 - it refuses; input
   0 is the particle stream. Right: `emitter.setInput(1, card)`. Verify: `emitter.input(1)` is the geo node.

4. **Custom kernel loading differs from BlinkScript.** Wrong: `kernelSourceFile` / `reloadKernelSourceFile`
   (not on this node) or `kernelSource.setValue` (a PythonCustomKnob here). Right: `node['kernelFile']` +
   `node['loadKernelFile'].execute()`. Headless (`-t`) it created NO param knobs by any route - set and check
   params in the GUI, and compile-test the kernel on a plain BlinkScript headless first so a compile error
   does not raise the modal dialog in the artist's session. Verify: the param knobs exist in the GUI.

5. **Particle kernel syntax.** Wrong: `ParticleBlinkKernel<eParticleWise>`, `process(int)`, knobs `time` or
   `count`. Right (from the bundled gizmos' kernelSource): `kernel K : ImageComputationKernel<ePixelWise>` with
   attributes as images - `Image<eRead> p_position; Image<eReadWrite> p_velocity;` (also p_mass, p_color,
   p_life, p_size, p_orientation, p_start, p_conditions), a `_dt` step param and a no-argument `process()`;
   random access is per attribute (`Image<eReadWrite, eAccessRandom> p_velocity`). Verify: copy the structure
   from a bundled gizmo's kernelSource, e.g. plugins/ParticleAttractToSphere.gizmo.

6. **Procedural (BlinkScript) particles: drive time with an expression on the prefixed knob.** Wrong: a static
   `time` value, `frame` alone, or a knob named `time`. Right:
   `node['<Kernel>_time'].setExpression('frame / fps')`. Verify: 0.5 at frame 12 and 2.0 at frame 48 (24 fps).

7. **Nuke image y points UP.** Wrong: decreasing y to make embers rise (round-2 probes: that moves them down).
   Right: rising = increasing y; falling snow = decreasing y. Verify: sample a particle's position on two
   frames.
