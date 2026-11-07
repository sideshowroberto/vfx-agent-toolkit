# Versioning up a shot script without re-saving it

Task shape: "the same script plus new nodes, nothing else changed". A headless `scriptOpen` + new nodes + `scriptSaveAs` passes every count and error check yet changes old blocks (see api_traps.md, "Saving over an opened shot script"). Do not let the tool re-serialise what you must not change; produce the new file as TEXT so the diff is the proof.

## Method

The steps below are scripted: `scripts/nk_version_up.py` does 2, 3 and 5 (`append`, `compose`) and everything under Verify (`diff`, `verify`). Run `python scripts/nk_version_up.py --help`. Step 4 (a class swap) has no writer, only the check: `diff --allow-swap` and `verify --allow-swap`.

1. Build the new nodes inside the opened (never saved) old version, select them, and `nuke.nodeCopy(path)` the snippet.
2. Normalise the snippet: it is CRLF, and the new file must keep the OLD file's line ends (usually LF, but 25 of 255 real shot scripts were CRLF). Drop the `set cut_paste_input [stack 0]` and `version` lines and `selected true`. The FIRST node's input 0 is written as `push $cut_paste_input` both when it is unconnected AND when it is wired to a node outside the copy, so `push 0` cuts that second kind of wire: check the added node's inputs afterwards (`verify` prints them). Assert the line occurs nowhere else. The copy includes the `add_layer` lines for custom layers.
3. Write the new file as: the old file's bytes, with only the Root `name` line pointed at the new version, plus the appended snippet block. Use exclusive create so nothing is overwritten.
4. Swapping node classes works the same way: replace each old block in place with the new class's block, keeping name, xpos and ypos; wiring comes from the stack position. The replacement must CARRY the old block's state knobs (tile_color, gl_color, note_font*, disable, hide_input). Compare those knobs explicitly on swapped nodes, because an every-knob diff that excludes the swapped nodes misses them.
5. If a tool already re-saved the script, repair by composing: take the saved file, replace every block whose (class, name) exists in the original by the ORIGINAL block text, restore the original header (everything before `Root {`), and rewrite only the Root `name` line.

## Verify

- Prove `new minus the Root name line starts with old` (byte prefix) for the append method, or a block diff for the compose method (compare knob lines as a set, since Nuke reorders knobs; ignore the Root name).
- Verify in a FRESH process, opening the new script first, before anything has defined the custom layers (a builder session would mask a missing `add_layer`). A knob naming an undefined layer loads as `none` with no error, only a stdout warning (Nuke 15.1 and 17.1), so compare warnings as well as knobs. Then open the old script in the same process and compare every knob of every node. The only expected difference was Root `frame`, caused by the verifier's own `nuke.frame()` call: take the dump before moving the frame.
- When comparing two representations (for example two cameras), report the difference distribution rather than a count over a tiny threshold; a 1e-6 relative test flagged float32 noise on 1.5 million pixels whose median difference was 2e-7.
