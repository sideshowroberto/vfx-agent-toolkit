# Updating an Asset in Place

**Part of:** houdini-hda-creation skill
**Loaded:** On-demand (progressive disclosure)
**Last Updated:** 2026-10-30

Rule for the whole page: an update that "landed" in the definition is not proof that the
scene uses it. Read the OUTPUT of the live instance.

---

## 0. Dry-run the change before it can reach anything (obs 187, 210)

The house rebuild (build_network into an unlocked instance, `setParmTemplateGroup`,
`updateFromNode`) writes the definition file the moment it runs, and every live instance
takes the new internals at once. A VEX compile error or an unintended geometry change
lands in the production scene before anything was measured.

1. Build the new network into a plain SOP subnet in a scratch object, with the new
   interface appended as spare parms (output SOPs give the same output indices), and copy
   a live instance's values in.
2. Content-digest every output against the live instance with the new feature OFF
   (md5 over P, every vertex list, every point / prim / vertex / detail attribute, group
   sizes). All must be identical. Hash attributes BY NAME in sorted order and per
   component: creation order changes between cooks and fakes a difference
   (`houdini-python-automation/scripts/geo_digest.py`).
3. Prove the digest can fail: change a dimension by 1 mm and see it flip, restore and see
   it match. A comparison that cannot fail proves nothing.
4. Test the feature itself in the subnet (clamps, clearances, part counts), then back up
   the .hda files and run `updateFromNode`.

**A NEW asset for a live or shared scene:** build it headless first and install the
finished file; the scene never holds a scratch subnet or an untested asset. The build
script creates its own throwaway container and refuses to overwrite an existing .hda;
run it to a scratch path and test there (force-cook every case, closure / winding /
dimension read-back); build the real file the same way; the live session only does
`hou.hda.installFile(...)` and `createNode(type, exact_type_name=True)` in one undo group.
Keep the in-scene subnet route for interactive authoring.

## 1. An unlocked live instance misses the update (obs 176)

If the live output did not change, check `instance.matchesCurrentDefinition()` on EVERY
live instance. An instance whose contents were unlocked at some point keeps its own copy
of the internals and ignores new links; nothing in the UI says so.

Compare its contents with a fresh UNLOCKED scratch instance (a locked instance lists only
a fraction of its nodes, so that comparison is meaningless). If the only differences are
the missing definition changes, call `matchCurrentDefinition()` on that ONE instance:
this is a deliberate revert after a diff, not a bulk refresh remedy (see "HDA
Parameters Not Updating" in this skill).

## 2. Find tab folders and multi-column labels by what they contain

- A folder appended as `fld_x` can be stored under another name (`fld_layout_7`) and
  `ptg.find("fld_x")` returns None. Use `ptg.containingFolder("<a parm the folder
  holds>")`.
- A Label parm with three columns shows up as `name1..3`, but its template is named
  `name`; `ptg.find("name1")` is None.

## 3. A copied interface is a second source of truth (obs 191, 176)

- A wrapper asset that copies an inner asset's parm templates (and links them down with
  `ch("../name")`) keeps the OLD help when the inner asset changes meaning. Nothing
  errors; the values still flow.
- After any inner change to a promoted parm's meaning, help, default or range: keep a
  list of every wrapper that copied it, assert the same type, label and default (only the
  help may differ), replace the wrapper's templates with the current ones
  (`ptg.replace`, `setParmTemplateGroup`), and read back that the help matches. Better,
  promote by reference to one source of truth so the copies cannot drift.
- A template instance with LOCAL parms plus a "Push to production" button drifted (the
  operator skipped the push, then hand-edited production; 7 of 15 values differed).
  Link production to the template with `ch()` / `chs()` so the template is the master.

## 4. Before making a dimension a master control (obs 202)

An expression search only finds dependents that were already wired. Run a scene-wide
parm walk that reports (a) every expression or string mentioning the parm or its derived
attributes and (b) every float parm whose value equals the current value (or its
negative); link or justify each hit. In the case that found this, 12 assets held the
value as a typed number (an asset's own default). For an asset that takes a dimension as
a default, prefer reading it from the upstream geometry (a detail attribute) over a
literal default.

## 5. Test the combination that switches downstream nodes on

When an asset gains geometry in an existing Boolean (a second cutter, a hole), test the
parameter combinations that turn on downstream slicers or bends, not only the defaults.
See [text_and_engraving.md](text_and_engraving.md), section 3.
