# Houdini: HDA contents and persistence

Provenance: audited 2026-09 in the vfx-agent-toolkit-codex repository; its docs/,
codex/tests/ and codex/recipes/ hold the evidence records and probes named below.

Checked 2026-09-07 against SideFX's current Houdini 22.0 reference. Native
save/match/reopen and intentional revert passed on Houdini 21.0.596 on
2026-09-08; see Windows runtime evidence.
Forced native save failure/recovery also passed on Windows; broader HDA behavior
remains scoped to continuation evidence.

Unlock the instance with `allowEditingOfContents()`. Save its edited contents
with `definition.updateFromNode(instance)`. Only after that succeeds, use
`matchCurrentDefinition()` to relock. Calling match alone discards unsaved
contents. `setIsPreferred(True)` chooses between definitions; it grants no write
permission. Locked instances follow definition updates; unlocked ones retain
local edits. Avoid bulk matching or destroying instances as a refresh remedy.

Given an explicitly chosen editable test instance:

```python
instance.allowEditingOfContents()
# Apply the intended internal edits here.
definition = instance.type().definition()
if definition is None:
    raise ValueError("Selected node has no HDA definition")
definition.updateFromNode(instance)  # Failure must stop before the next line.
instance.matchCurrentDefinition()
```

Check the definition's library target before saving; it can be embedded. A
read-only/published library needs the project's writable/versioned workflow.
[SideFX definition API](https://www.sidefx.com/docs/houdini/hom/hou/HDADefinition.html),
[instance API](https://www.sidefx.com/docs/houdini/hom/hou/OpNode.html).

Work-desktop check: edit one disposable HDA, save, reopen and inspect the internal
change. Separately make an unsaved change and verify intentional match reverts it.

Other unresolved HDA recipes, callbacks and missing helpers remain tracked in
H1-H5 of the audit. Do not infer working
callbacks merely from PythonModule function names or claim a parameter affects
the graph without reading back its connection and resulting geometry.

Copy to Points recipe uses source
input zero, targets input one, float pscale and quaternion orient. Its native
probe verifies bounds, a nonparallel fallback frame, a VEX array, a registered
runtime callback, a connected scale control and a reopened USD variant reference.

HDA lifecycle probe verifies explicit
OnCreated/OnLoaded sections marked IsPython. Save the parameter interface with
definition.setParmTemplateGroup; an instance-only spare parameter is not enough
for future instances. Set expressions on individual parms in a ParmTuple.
