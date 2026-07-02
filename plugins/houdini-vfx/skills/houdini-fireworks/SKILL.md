---
name: houdini-fireworks
description: >
  Houdini fireworks effect using POP networks. Covers burst emitter setup,
  multi-stage particle systems (shell, burst, trails), VEX per-particle
  attributes (color, size, velocity variation, fade over life), and rendering
  glowing particles in Karma XPU and Mantra. Triggers: "fireworks", "POP burst",
  "particle trails", "particle emitter Houdini", "pyro sparks Houdini".
allowed-tools: Read, Write, Bash
---

# Houdini Fireworks — Skill

## Overview

Houdini offers two paths for fireworks:

1. **POP Fireworks shelf tool** — creates a `popfireworks` DOP node automatically.
   Self-contained, multi-colored burst particles out of the box. Burst starts
   around frames 60–70 by default. Good for quick reference or blocking.

2. **Custom POP network** — manual assembly of `POPSource`, `POPForce`,
   `POPDrag`, `POPWrangle`, and `Particle Trail` SOP. Production path.
   Documented fully below.

---

## Network Architecture (Custom Path)

| Stage | What it does | Primary node |
|-------|-------------|--------------|
| Shell (rocket) | Single point travels upward to burst position | Animated null/SOP point |
| Burst emitter | Emits sphere of particles at a single frame | POPSource (Impulse mode) |
| Per-particle variation | Random velocity, color, scale on birth | POPWrangle |
| Forces | Gravity + turbulence noise | POPForce x2 |
| Drag | Slows particles, creates arcs | POPDrag |
| Fade | Color + size decrease with age | POPWrangle (per-frame) |
| Trails | Streak geometry generated post-sim | Particle Trail SOP |

---

## DOP Network Node Setup

### POPSource — burst emitter

| Parameter | Setting |
|-----------|---------|
| Source Geometry | Low-poly sphere SOP (10–20 pts); particles emit from its points |
| Emission Type | All Points |
| Birth Rate (Constant) | 0 — no continuous emission |
| Impulse Activation | `$F == [burst_frame]` e.g. `$F == 50` |
| Impulse Count | 200–500 |
| Life Expectancy | 2.0–4.0 (seconds) |
| Life Variance | 0.5 |
| Initial Velocity | Set Always, then override in POPWrangle |

### POPForce — gravity

| Parameter | Value |
|-----------|-------|
| Force X/Y/Z | `0, -9.8, 0` |
| Force Type | Wind |

Add a second POPForce with small random turbulence values (0.1–0.3 per axis)
to break up uniform arcs.

### POPDrag — air resistance

| Parameter | Value |
|-----------|-------|
| Air Resistance | 0.2–0.5 (sparks); up to 0.8 (heavy embers) |
| Drag Type | Linear |

### POPWrangle — per-particle VEX

Two wrangles needed:
- `POPWrangle_onBirth` — runs conditionally for newly born particles
- `POPWrangle_perFrame` — runs every frame to fade color and size

---

## VEX Expressions

### Per-particle random color — run on birth (POPWrangle_onBirth)

```vex
// @id is stable across frames — use it as seed, not @ptnum
// Palette approach: pick from preset firework colors
int pick = int(rand(@id) * 3);
if (pick == 0) @Cd = {1.0, 0.2, 0.05};   // red-orange
if (pick == 1) @Cd = {1.0, 0.85, 0.1};   // gold
if (pick == 2) @Cd = {0.2, 0.5, 1.0};    // blue
```

For continuous hue range instead of a palette:

```vex
float hue = rand(@id) * 0.15 + 0.04;  // warm hues only (orange-gold)
@Cd = hsvtorgb(set(hue, 1.0, 1.0));
```

### Outward burst velocity — run on birth

```vex
if (@age < 0.001) {
    vector dir = normalize(rand(@id + 0.1) * 2.0 - {1,1,1});
    float speed = fit01(rand(@id + 0.2), 3.0, 8.0);  // 3–8 Houdini units/sec
    @v = dir * speed;
}
```

### Color fade + size shrink over lifetime — run every frame (POPWrangle_perFrame)

```vex
// norm_age: 0.0 = just born, 1.0 = about to die
float norm_age = @age / @life;

// Fade to black
@Cd *= (1.0 - norm_age);

// Shrink: 0.05 Houdini units at birth, zero at death
@pscale = (1.0 - norm_age) * 0.05;
```

### Velocity-to-color diagnostic (optional artistic use)

```vex
float spd = length(@v);
float t = clamp(spd / 10.0, 0.0, 1.0);
@Cd = set(t, 1.0 - t, 0.0);  // red = fast, green = slow
```

### Kill particles by condition

```vex
// Remove particles that fall below world y = -5
if (@P.y < -5.0) {
    i@dead = 1;  // POP solver reads dead=1 and removes the particle
}
```

---

## Emission Timing — Burst at a Specific Frame

### Method 1: Impulse Activation (recommended for clean single-frame burst)

In POPSource, set:
- **Impulse Activation**: `$F == 50`
- **Impulse Count**: 400

Births exactly 400 particles on frame 50 only.

### Method 2: Short Birth Window (soft burst over 2–3 frames)

In POPSource **Constant Birth Rate**:
```
if($F >= 50 && $F <= 52, 500, 0)
```

Births 500 particles per frame for frames 50–52. Gives a slightly more
natural staggered appearance than a single-frame burst.

---

## Particle Trail SOP (Post-Sim, SOP Level)

`Particle Trail` is a SOP-level geometry node. Connect it after a
`DOP Import` node that brings the simulation into SOPs.

| Parameter | Value |
|-----------|-------|
| Method | Velocity (reads @v to extrapolate trail backward) |
| Trail Length | 0.5–2.0 seconds |
| Divisions | 8–16 (curve smoothness) |
| Split Trails | Enable for bursting-spark look |
| Attribute Interpolation | Enable (lets @Cd and @pscale interpolate along trail) |

Particle Trail generates polylines or curves — these are the streak/glow
geometry you render. They are not simulated; they are computed from
velocity each frame.

**Gotcha:** `@v` must exist on the DOP-imported points. Verify in the
Geometry Spreadsheet before connecting Particle Trail.

---

## Rendering — Karma XPU

Karma XPU runs in Solaris (LOP context) and uses MaterialX shaders.

### Critical: `@widths` attribute required

Karma XPU does **not** read `@pscale` for particle rendering — it reads `@widths`.
Without `@widths`, particles are completely invisible in the render. No error is
thrown. Add a SOP-level wrangle before the SOP Import LOP:

```vex
// Run in a Point Wrangle after DOP Import, before SOP Import LOP
f@widths = f@pscale * ch("width_mult");  // width_mult = 1.0 default
```

Note: Karma XPU does **not** support sprite rendering (textured disc particles).
Sprites require Karma CPU or Mantra. For glowing streaks/sparks, use the curve
geometry from Particle Trail SOP — this renders correctly in Karma XPU.

### Setup
1. Add a SOP Wrangle after DOP Import to write `@widths` from `@pscale` (see above).
2. Add a **SOP Import LOP** to bring particle/trail geometry into Solaris.
3. Create a **Material Library LOP** and build a **Karma MaterialX** material.
4. Inside the material, use **MtlX Standard Surface**:
   - Diffuse Weight: 0
   - Emission Weight: 1.0–5.0
   - Emission Color: connect a **MtlX Geometry Property Value** node
     set to property name `Cd`, type `color3`
5. Optionally, add a **MtlX Multiply** between the Cd value and Emission Color
   to scale brightness independently.

### Reading @Cd in MaterialX

```
[MtlX Geometry Property Value]
  Geometry Property Name: Cd
  Output Type: color3
        |
[MtlX Multiply]
  In2: emission_scale (float, 3.0–8.0)
        |
[Standard Surface: emission_color input]
```

### Bloom

Karma XPU has no built-in bloom. Render an emission AOV (use an LPE AOV in
the **Karma Render Properties LOP** set to `lpe:emission`) and apply bloom
in Nuke compositing.

---

## Rendering — Mantra

Mantra reads `@Cd` natively on particles. It renders particles as discs
or spheres depending on object render properties.

### Setup
1. In the particle object's **Render Properties**, set:
   - `vm_renderpoints = sprites` (soft disc, good for sparks) or
   - `vm_renderpoints = spheres` (volumetric, good for embers)
2. Apply a **Constant** SHOP shader — it reads `@Cd` automatically with
   no extra setup.
3. For a glow/emission look, use a **Principled Shader** SHOP:
   - Set Diffuse Intensity to 0
   - Set Emission Color to `@Cd` via a **Parameter VOP** or **Global Variables**
     node inside the VOP network

### Emission VOP setup (Mantra)

Inside a **Surface SHOP** VOP network:
```
[Global Variables: Cd output]
    |
[Bind Export: Ce (emissive color)]
```

This routes `@Cd` directly to the emissive channel, making each particle
glow its own color without receiving scene lighting.

### Particles emitting light (Mantra)

To have particles actually illuminate nearby geometry in Mantra:
- Set **Diffuse Limit** in Mantra ROP to at least 1
- Or use a **Geometry Light** on the particle object with an emissive shader
  (more efficient than relying on emission illumination directly)

---

## Full DOP Network (Text Diagram)

```
SOP Level:
  sphere_source (low-poly sphere, 20 pts)
       |
  DOP Network
       |
       POP Solver
            |
         POPSource
           Impulse Activation: $F == 50
           Impulse Count: 400
           Life: 3.0 sec, Variance: 0.5
            |
         POPWrangle_onBirth
           (random Cd, outward velocity)
            |
         POPForce_gravity
           Force: 0, -9.8, 0
            |
         POPForce_turbulence
           Force: 0.2 random per axis
            |
         POPDrag
           Air Resistance: 0.3
            |
         POPWrangle_perFrame
           (fade Cd and pscale by norm_age)
            |
  DOP Import (brings sim into SOPs)
       |
  Particle Trail SOP
    Method: Velocity, Length: 1.5 sec
       |
  OUT / cache / ROP
```

---

## Multi-Stage Burst (POPReplicate)

For a two-stage shell → burst system, use **POPReplicate** to spawn burst
particles when the shell particle dies:

| Parameter | Setting |
|-----------|---------|
| Activation | `@dead == 1` (trigger on death) |
| Num Particles | 150–400 per shell |
| Inherit Velocity | Enable (particles inherit shell velocity + burst outward velocity) |

**Cleanup required:** POPReplicate copies the dead source particle into the
replicated stream. After the sim, in SOPs:
```
DOP Import
    |
Group by Attribute (group name: shells, attribute: @generation == 0)
    |
Delete (delete group: shells)
    |
Particle Trail SOP
```
Without this, the dead shell point appears as a stray particle at the burst origin.

---

## Key Gotchas

- **`@widths` not `@pscale` for Karma XPU** — particles are silently invisible
  without it. Add a wrangle to write `f@widths = f@pscale` before SOP Import.
- `@Cd` cannot be set in a `POPVelocity` VEXpression field. Use `POPWrangle`.
- Use `@id` as the random seed for per-particle variation, not `@ptnum`.
  `@ptnum` changes as particles die; `@id` is stable.
- `@age` and `@life` are in **seconds**, not frames. Always divide for
  a normalized 0–1 value.
- Kill particles with `i@dead = 1`, not `removepoint()`. The POP solver
  reads the dead attribute at the end of each timestep.
- Karma XPU does not support legacy SHOP/VOP shaders. MaterialX only.
- Karma XPU does not support sprite particles. Use trail curves or point spheres.
- POPReplicate copies the dead source particle into the burst stream — delete it post-sim.
- Particle Trail SOP needs `@v` on points. No velocity = no trails.
- Karma bloom must be applied in comp. Plan for an emission AOV in your
  render layer setup.

---

## Reference Sources

| Resource | URL |
|----------|-----|
| POP Fireworks node | sidefx.com/docs/houdini/nodes/dop/popfireworks.html |
| POP Source | sidefx.com/docs/houdini/nodes/dop/popsource.html |
| POP Force | sidefx.com/docs/houdini/nodes/dop/popforce.html |
| POP Drag | sidefx.com/docs/houdini/nodes/dop/popdrag.html |
| POP Wrangle | sidefx.com/docs/houdini/nodes/dop/popwrangle.html |
| Particle Trail SOP | sidefx.com/docs/houdini/nodes/sop/particletrail.html |
| Pyro sparks guide | sidefx.com/docs/houdini/pyro/sparks.html |
| Fireworks shelf tool | sidefx.com/docs/houdini/shelf/dynamics_popfireworks.html |
| VEX Wrangle Cheat Sheet | mrkunz.com/blog/08_22_2018_VEX_Wrangle_Cheat_Sheet.html |
| Context7 Houdini library | /websites/sidefx_houdini (8875 snippets) |
| Context7 VEX library | /websites/sidefx_houdini_vex (29948 snippets) |
