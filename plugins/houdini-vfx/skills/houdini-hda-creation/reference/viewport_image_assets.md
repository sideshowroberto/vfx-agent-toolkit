# Assets That Show Images in the OBJ Viewport

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Camera-attached tools, reference cards, image planes (obs 159, measured on 21.0.596).

**Principle:** the OBJ viewport is a separate renderer with its own material model. A
material that renders correctly proves nothing about how it displays. Test the display
path with known pixel values and give it its own material when they differ.

1. **Transform carriers keep their display flag off.** A Fetch OBJ copying a camera's
   transform draws a camera icon at the camera; looking through that camera the icon
   filled the frame and seven captures with different materials were byte-identical.
   Hide the Fetch (or null) display flag; its children still display.
2. **MaterialX in the OBJ GL viewport is unreliable.** Opacity from texture alpha worked,
   but emission was black (unlit) or about 0.34x with a blue tint (standard_surface).
   A time-dependent file path expression freezes on one frame ("Cannot have channels
   which depend on time"), and `ogl_*` spare parms on a MaterialX node are ignored.
3. **Hand-made `ogl_*` spare parms:** texture layers are a MULTIPARM (`ogl_numtex`), so
   `ogl_tex1` alone is ignored; take the official templates from
   `hou.properties.parmTemplate("material", name)`. With `ogl_light` = 0 the base
   texture's alpha is ignored and the opacity map is read from colour channels.
4. **Working display recipe:** a Principled Shader used as a display-only material,
   basecolor black, reflect 0, `emitcolor` = gain with `emitcolor_texture` =
   `op:<COP RGBA>`, `opaccolor_texture` = `op:<COP layer with R=G=B=A=opacity>`, plus an
   official `ogl_light` spare set to 0. Measured: a subject within 3-8 levels of the
   analytic linear blend at 50 % over CG; sequence frames update per frame.
5. **Image sequences reach the viewport through an `op:` Copernicus File node**, never a
   time-dependent texture path.
6. **Split display and render with SOP flags.** Display branch = recipe above. Render
   branch = COP Preview Material with PREMULTIPLIED emission (rgb x opacity): Karma adds
   emission without scaling it by opacity (a 50 % region came out source/0.5), behind a
   default-off "Visible in Renders" switch.
7. **Verify colour by sampling captures against source pixels**, not by eye (reading
   captures: `houdini-python-automation/reference/verify_through_display_node.md`).
