# Karma Lights Through USD

**Part of:** houdini-solaris-usd skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

How Houdini light and ROP parameters land on the USD stage Karma renders, as measured on
Houdini 21.0.596. Only what was measured is listed; each item was read back from the
authored USD attribute or from a render, not taken from documentation. Common principle:
read the authored USD value, because the Houdini parameter name and the number Karma uses
are not the same thing.

---

## How to read the authored value

A Karma ROP builds its own LOP stage internally. Read the light prim from the node that
ends that network (here `<rop>/lopnet/OUT`), not from the parameters on the OBJ-level light.

```python
import hou

rop = hou.node("/out/my_karma_rop")
stage = hou.node(rop.path() + "/lopnet/OUT").stage()
prim = stage.GetPrimAtPath("/lights/my_light")   # the prim path your lights land at
for name in ("inputs:intensity", "shaping:cone:angle",
             "shaping:cone:softness", "karma:light:singlesided"):
    attr = prim.GetAttribute(name)
    print(name, attr.Get() if attr and attr.IsValid() else None)
```

If the prim path is unknown, list `stage.Traverse()` first and look for the light prim.

---

## 1. A cone on an OBJ point light becomes a SphereLight with ShapingAPI, and the numbers change

**Rule:** to get a fitted cone half-angle `A` (degrees) and softness `s`, author
`coneangle = A / (0.5 + s)` and `conedelta = s * coneangle`, then read
`shaping:cone:angle` and `shaping:cone:softness` back from the stage.

**Why:** an OBJ `hlight::2.0` point light with `coneenable` on becomes a UsdLux
SphereLight with the ShapingAPI applied, and the cone is re-expressed:

- `shaping:cone:angle = coneangle / 2 + conedelta` - a HALF-angle, not the Houdini cone
  angle.
- `shaping:cone:softness = conedelta / coneangle`.

Measured: `coneangle` 8 with `conedelta` 3 authored a 7 degree half-angle with softness
0.375. The inversion above follows from those two measured formulas (7 / 0.875 = 8,
0.375 * 8 = 3); confirm it by reading the attributes back after you set the parameters.

---

## 2. Karma falls off with distance squared, whatever `atten_type` says

**Rule:** for a light placed far from its target (a "sun" spot), compensate with
`light_exposure = log2(d^2)`, where `d` is the distance in scene units, and check the
result against the irradiance you wanted.

**Why:** a spot light placed 55 m out made no visible patch at its default intensity
because the distance-squared falloff applies regardless of the `atten_type` setting.
Setting `light_exposure = log2(d^2)` restored the target irradiance (for 55 m, log2 of
3025, about 11.6). Read the patch back from the render as a pixel box mean; the exposure
formula is the compensation, the measurement is the proof.

---

## 3. Area lights are double-sided by default

**Rule:** for a one-sided area light (grid, disk), turn `singlesided` on and read
`karma:light:singlesided` back from the stage as True before judging the lighting.

**Why:** grid and disk lights default to double-sided (`singlesided` off; USD
`karma:light:singlesided` False). An uplight disk 5 cm above a floor, meant to wash the
ceiling above it, lit the floor 5 times more than the ceiling, because it emits from
both faces.

---

## 4. Intensities arrive multiplied by 2 pi

**Rule:** compare intensities in the USD, not in the Houdini parameter, when matching a
light to a measurement or to another renderer.

**Why:** a Houdini intensity of 1.2 was authored as 7.54 on the stage (1.2 * 2 pi).
Compare in the USD.

---

## 5. An environment light is invisible to the camera until Render Light Geometry is on

**Rule:** if the sky or environment must be visible in frame, turn on `light_contribprimary`
("Render Light Geometry") on the environment light and read the frame back; do not stand
in an emissive disc.

**Why:** an `envlight` lights the scene but does not appear to camera until
`light_contribprimary` is on. An emissive sky-cap disc used instead is opaque geometry: it
shadowed the sun and the environment light for the whole interior (frame mean fell from 35
to 30 while the opening region still matched).

---

## 6. Karma ROP defaults that change a lighting read

The ROP ships with `causticsenable` off, `diffuselimit` 3, `volumelimit` 0, and a
`denoiser` menu (off / optix / oidn). Measured with OptiX at 128 samples: flat-region
noise fell from 4.69 to 0.14, and box means stayed within 2.8 luma of the undenoised
prediction, so a denoised scratch frame is a fair luminance read. The numbers are from one
scene; read the defaults back from your own ROP.

---

## 7. A Light Mixer downstream overrides the light LOP (obs 291)

**Rule:** before changing any light value, read it on the COMPOSED stage at the display / render node
(`prim.GetAttribute('inputs:exposure').Get(frame)`) and compare with the light LOP's parm. If they differ, walk the
chain for a `lightmixer` (its overrides are the `xn__<primpath>inputs...` parms) or a later Light / Edit LOP, edit
where the value wins, and read it back after the edit.

**Why:** a sun LOP showed exposure 3.45 and a sky dome LOP 10.0, but Karma rendered the sun at 7.0 and the sky at 1.0
because a Light Mixer further down carried its own overrides; editing the light LOP changed nothing and raised no
error. Only the overridden parms are affected (the sun's angle and colour still came from the light LOP).

---

## 8. Geometry (mesh) lights ignore Spread and shaping focus (obs 205)

**Rule:** a Geometry Light LOP (MeshLightAPI) emits Lambertian from its faces; Spread, USD shaping focus, cone and
barn doors do not apply. Aim it by orienting the emitting faces (and occluders), or use a rect / disk light where a
beam must be shaped. Before concluding a parameter "does nothing", run the positive-control test in
verification_instruments.md section 6.

**Why:** measured with husk XPU: Spread 0.1 and focus 30 each changed the frame by about 0.6 (the noise floor), while
an exposure change through the same override changed it by 19.2. Spread is documented only for rect / disk lights and
the Geometry Light LOP exposes no shaping parameters. A 2D first-hit section showed turning a strip 45 degrees toward a
wall moved the share landing on the jamb from 50% to 72%, while a baffle only removed light (x1.01).

---

## 9. Spot lights, sphere radius and cone angle (obs 174)

- **Spot Light toggle:** the Light LOP writes cone / softness only when `spotlightenable` is on; with it off there is
  no ShapingAPI and `inputs:shaping:cone:angle` reads None. Read it back before any render is judged.
- **A sphere light's RADIUS is geometry.** A 3 cm fill 0.01 mm behind a 1.67 cm lip lit a bright speck at the edge
  (120 px over 150 in the viewport); 1.2 cm was still a dot (9 over 100), 0.8 cm none. Keep the radius under about half
  the occluder's thickness and re-check after any size change.
- **`inputs:shaping:cone:angle` is degrees OFF THE AXIS** (half the spread): a "70 degree" fill reached nearly
  horizontal and grazed the arch head (7.7% of cone rays clipped within 12 cm; 55 = 1.5%, 45 = 0).
