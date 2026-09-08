# Attribution

The Seedance skill family in this plugin (`seedance-20` and its `seedance-*`
siblings) and the `references/` corpus in this directory are derived from the
upstream open-source project:

- **seedance-2.0** by Iamemily2050 (@iamemily2050) - https://github.com/Emily2040/seedance-2.0
- License: MIT (full text in `references/LICENSE-upstream.txt`)

What was vendored on 2026-09-08:

- `references/*.md` - the upstream reference corpus that the `[ref:<name>]`
  load instructions across the skill family resolve against. Copied verbatim
  except that typographic punctuation was normalised to ASCII; multilingual
  example text is kept as-is.
- `seedance-copyright` and `seedance-filter` - the two upstream skills the
  root skill's safety gate routes to.

Not vendored (not routed to by this plugin): `seedance-audio`,
`seedance-examples-zh`, `seedance-vocab-*`. Pull them from upstream if you
need per-language vocabularies.

Resolution rule used by every skill in the family: `[ref:<name>]` is
`<this directory>/references/<name>.md`; `[skill:<name>]` is the sibling
skill of that name in the same plugin.
