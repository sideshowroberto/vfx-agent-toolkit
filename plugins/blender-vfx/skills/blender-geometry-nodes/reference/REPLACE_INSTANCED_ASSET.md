# Replacing an asset a geometry-nodes scatter instances (obs 245)

An instanced asset's convention (origin, facing, ground offset) lives in the
INSTANCER, not in the asset: the object's bbox and dimensions do not give it.
Read it from the instancer and the evaluated placement, then prove the swap
through the shot camera, not with turnarounds alone. Do the reads in a headless
duplicate of the scene.

## Read the contract (four reads)

1. **Object Info transform space.** With `ORIGINAL`, only local mesh
   coordinates matter, not the object's own transform.
2. **Switch wiring.** Which Index Switch input selects the object, and which
   LOD or variant inputs are actually used (unused ones can be ignored).
3. **Instance matrices.** Read evaluated matrices from
   `depsgraph.object_instances`: rotation tells you which local axis faces
   which way (for example an unrotated instance means local -Y faces forward).
4. **Placement by ray-cast.** Cast from each instance origin down to the host's
   EVALUATED mesh to get the origin height above the surface it sits on, per
   section if the host varies. Use no x filter: long quads have vertices only at
   their ends, so a probe filtered by x returns nothing.

## Build, then swap-test

- Build the replacement to that contract (origin, facing, offset).
- Swap-test in the duplicate: point the switch at the new object, count the
  evaluated instances (it must equal the old count), and render CG-only through
  the shot camera.
- If the render is overscan, crop it to the plate's display window and mix it
  50/50 with the plate: a like-for-like old / new / plate comparison shows layout
  phase issues that turnarounds cannot.
- Remap the appended material back to the scene's own copy.
