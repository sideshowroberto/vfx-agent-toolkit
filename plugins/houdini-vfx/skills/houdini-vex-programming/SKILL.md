---
name: houdini-vex-programming
description: Verified Houdini VEX traps for wrangles - find() return value, deferred set*attrib writes, empty group patterns, nearpoints self-hits, stale chs() after spare parms, bare globals from Python. Use when writing or debugging a wrangle whose result looks wrong with a clean cook.
when_to_use: Triggers on "vex", "wrangle", "attribute wrangle", "point wrangle", "detail wrangle", "chs", "spare parm", "nearpoints", "wrangle does nothing", "wrong point count".
metadata:
  version: 2.0.0
  updated: 2026-11-08
---

# houdini-vex-programming

Traps below were each measured in Houdini (H20.5/H21). Traps 1-5 cook cleanly and give a
quietly wrong result; trap 6 is an error you only see if you ask. Details, proofs, snippets:
`reference/wrangle_traps.md`.

## Trap rules

1. **Test `find(...) >= 0` (or `< 0`), never `== -1`.** In H21 `find()` on an array
   returns `-(len+1)` for a missing value (-2 for a one-element array), not -1.
2. **`set*attrib()` writes are deferred until the wrangle finishes.** `point()`/`prim()`/
   `detail()` in the same wrangle read the INPUT. Keep multi-pass state in local arrays and
   write once at the end, or split the passes into chained wrangles.
3. **An empty group pattern selects ALL elements** (`expandpointgroup(0, "")`, SOP group
   fields). Guard parameter-driven patterns with `if (pat != "")`.
4. **`nearpoints()` includes the point itself.** Skip `pt == @ptnum` when
   counting or averaging neighbours, or the count is one too high and the average is pulled
   towards the point.
5. **`chs()`/`chf()` read stale values when spare parms are added after the wrangle has
   cooked** (e.g. `build_network` then `create_spare_parameters`). Create the spare parms
   first, or re-set the snippet / force a recook after adding them, then re-read the result.
6. **A wrangle built from code fails silently from the caller's side.** A compile error
   (e.g. bare `P.y = 1;` - "Reference to undefined variable", always write `@P`) shows only
   in `node.errors()` or `cook(force=True)`, so force-cook and check errors on every node you
   build before saving or reporting.

## How to check your result

- **Read the result back from Houdini before reporting it:** point/prim counts, attribute
  value histograms (not one sample), and two or three values worked out by hand. A
  plausible-looking viewport is not a check.
- **After adding or changing parms on a node that already cooked, recook and read again**
  before diagnosing anything (trap 5).
- **When a wrangle "does nothing":** write each intermediate value to a debug attribute and
  read them back; compare against the input to spot trap 2.
- **Never report a cause you have not tested.** If the first fix did not change the
  measured result, the diagnosis is still open - say so. In the 2026-11 eval, 5 of 9 runs
  told the user an invented cause for what was really trap 5.

## Reference

- `reference/wrangle_traps.md` - each trap with the incident, fix snippet and the
  read-back that proves it.
- SideFX docs through the Houdini MCP: `search_help` / `get_help_page` (fxhoudinimcp, port
  8100). Build wrangles with `build_network` and check them with `verify_network`.

## Version history

- **2.0.0** (2026-11-08) - Cut to a traps list after a no-skill baseline showed no lift
  (ClaudeCode/evals/houdini-vex-v2, 21 voluntary runs never opened the skill; forcing it cost
  +33%). General VEX tutorial removed; buggy nearpoints snippet replaced by trap 4; added
  stale chs() after spare parms (observation 442). Dropped the ternary string-type trap: it
  did not reproduce in H20.5.613 or H21.0.596 (hython re-test 2026-11-08).
