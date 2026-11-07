# Interface Design for Assets Whose Size Keeps Changing

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

**Principle:** put the controls where people keep changing their minds, make each one mean
exactly one thing, and keep the last approved answer selectable (obs 217).

An asset that exposed every station as an absolute height could not say "the same table,
10 % bigger", and its controls sat two dives below the network the artist works in. The
rebuilt version fixed all three, proven headless over 11 cases:

1. **One member absorbs a height change.** Height = floor to top; only the pedestal
   stretches (heights 0.9 / 1.1 / 1.3 m gave pedestals 0.562 / 0.762 / 0.962 m, top and
   band thickness unchanged); everything else derives from fixed thicknesses.
2. **Uniform Scale multiplies every input size BEFORE the UV pass**, inside the build,
   not as a Transform afterwards (which scales the texture with it). Textures stay
   metric.
3. **Promote the 3-5 controls that keep changing** to the node the artist actually works
   at, and have the inner asset read them by channel reference. Never copy values.
4. **Version the asset and keep the previous approved design behind a Switch** (a
   Design parm), one click away.
5. **Test every control by changing it on the PROMOTED node** and reading back the
   result geometry, not the parm.
