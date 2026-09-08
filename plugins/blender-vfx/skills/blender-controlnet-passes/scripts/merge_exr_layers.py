"""Inspect multi-part EXRs and merge EXR files into ONE single-part
multilayer EXR (modern OpenEXR 3 API).

READ THIS FIRST (2026-08-21): Blender 5.x writes "multilayer" EXRs as
MULTI-PART files - one part per layer (part 0 = Combined, part 1 =
CryptoObject00, ...). The OpenEXR python module's File.channels() and
File.header() report PART 0 ONLY, so every such file looks like it holds
just Combined RGBA. That misreading produced a false "Blender 5.1.x drops
all but the first File Output item" bug report; the files were intact.
Iterate File.parts. `--inspect` below does that and is the instrument to
use before declaring any EXR hollow.

Why the merge exists: some consumers want a SINGLE-PART multilayer EXR,
and separately rendered passes (one EXR each) sometimes need combining.
The old python merge idiom (InputFile.channel + Imath, OpenEXR 2.x API)
raises "Invalid PixelType" on OpenEXR 3.4 - this tool uses the modern
OpenEXR.File API, verified by roundtrip on 3.4.13.

Usage:
  python merge_exr_layers.py --inspect shot_crypto_0001.exr [more.exr ...]
      Print every part and its channels. Exit 0.

  python merge_exr_layers.py --out merged.exr ^
      --layer "Combined=path\\sep_combined.exr" ^
      --layer "Depth=path\\sep_depth.exr" ^
      --rename "Depth.V=Depth.Z" --rename "Mist.V=Mist.Z"

  python merge_exr_layers.py --flatten multipart.exr --out single.exr
      Copy every part of a multi-part file into one single-part file,
      channel names unchanged (header attributes carried per --meta-prefix).

  --layer NAME=PATH   For every channel in EVERY part of PATH, keep the
                      part after the LAST dot as the suffix and emit
                      "NAME.<suffix>" (a channel with no dot gets suffix =
                      its whole name).
  --rename OLD=NEW    Applied to the FINAL channel names after prefixing
                      (File Output float items write "<item>.V"; Nuke
                      expects Depth.Z / Mist.Z - rename them here).
  --meta-prefix P     Copy every header attribute whose name starts with P
                      from the inputs into the output (repeatable).
                      DEFAULT: "cryptomatte/" - Blender writes the
                      Cryptomatte manifest (name/hash/conversion/manifest)
                      into the EXR header, and Nuke's Cryptomatte gizmo
                      cannot find the layers without it. --no-meta writes
                      a bare header.
  --selftest          Write synthetic inputs to a temp dir, merge, verify
                      the roundtrip, exit 0/1. No arguments needed.

Verification is built in: after writing, the tool RE-OPENS the output and
compares the channel list, per-channel pixel data and the copied header
attributes against the inputs. Exit 0 only when the read-back matches.
ASCII only; python (never python3).
"""
import argparse
import os
import sys
import tempfile

import numpy as np
import OpenEXR

DEFAULT_META_PREFIXES = ("cryptomatte/",)


def iter_parts(path):
    """Yield (part_index, part_name, header_dict, channels_dict) for EVERY
    part of an EXR. A single-part file yields once."""
    f = OpenEXR.File(path, separate_channels=True)
    for i, part in enumerate(f.parts):
        yield i, part.header.get("name"), part.header, part.channels


def read_channels(path):
    """Return {channel_name: float32 ndarray} across ALL parts of an EXR."""
    out = {}
    for _, _, _, channels in iter_parts(path):
        for name, chan in channels.items():
            if name in out:
                raise SystemExit("duplicate channel across parts: %s in %s"
                                 % (name, path))
            # np.array with copy + explicit float32: chan.pixels can be a
            # proxy/half view whose buffer does not outlive the File.
            out[name] = np.array(chan.pixels, dtype=np.float32, copy=True)
    return out


def read_meta(path, prefixes):
    """Return {attr: value} for header attributes (any part) matching any
    prefix. Conflicting values between parts are an error."""
    if not prefixes:
        return {}
    meta = {}
    for _, _, header, _ in iter_parts(path):
        for k, v in header.items():
            if any(k.startswith(p) for p in prefixes):
                if k in meta and meta[k] != v:
                    raise SystemExit(
                        "header attribute %s differs between parts of %s"
                        % (k, path))
                meta[k] = v
    return meta


def inspect(paths):
    """Print every part + channel list. The instrument for 'is it hollow'."""
    for path in paths:
        if not os.path.isfile(path):
            print("%s: MISSING" % path)
            continue
        parts = list(iter_parts(path))
        print("%s: %d part(s)" % (path, len(parts)))
        for i, name, header, channels in parts:
            crypto = sorted(k for k in header if k.startswith("cryptomatte/"))
            print("  part %d name=%r channels=%s%s" % (
                i, name, sorted(channels.keys()),
                " cryptomatte-meta=%d" % len(crypto) if crypto else ""))


def _write_verified(merged, meta, out_path, meta_prefixes):
    shapes = set(p.shape[:2] for p in merged.values())
    if len(shapes) != 1:
        raise SystemExit("input resolutions differ: %s" % sorted(shapes))
    header = {"compression": OpenEXR.ZIP_COMPRESSION,
              "type": OpenEXR.scanlineimage}
    header.update(meta)
    # OpenEXR.File(header, channels).write() MUTATES the passed dict
    # (ndarrays become OpenEXR.Channel objects) - hand it a shallow copy
    # so `merged` stays comparable for the read-back verification.
    OpenEXR.File(header, dict(merged)).write(out_path)
    # read-back verification (rule: verify content, not existence)
    back = read_channels(out_path)
    if sorted(back.keys()) != sorted(merged.keys()):
        raise SystemExit("VERIFY FAIL: channel list mismatch after write")
    for name in merged:
        if not np.allclose(back[name], merged[name], atol=1e-6):
            raise SystemExit("VERIFY FAIL: pixel mismatch in %s" % name)
    back_meta = read_meta(out_path, meta_prefixes)
    if back_meta != meta:
        raise SystemExit("VERIFY FAIL: header attributes did not round-trip")
    return sorted(merged.keys())


def merge(layer_specs, renames, out_path, meta_prefixes=DEFAULT_META_PREFIXES):
    merged = {}
    meta = {}
    for layer_name, src_path in layer_specs:
        if not os.path.isfile(src_path):
            raise SystemExit("input missing: %s" % src_path)
        for k, v in read_meta(src_path, meta_prefixes).items():
            if k in meta and meta[k] != v:
                raise SystemExit(
                    "header attribute %s differs between inputs" % k)
            meta[k] = v
        for cname, pixels in read_channels(src_path).items():
            suffix = cname.rsplit(".", 1)[-1]
            final = "%s.%s" % (layer_name, suffix)
            final = renames.get(final, final)
            if final in merged:
                raise SystemExit(
                    "channel collision: %s (from %s)" % (final, src_path))
            merged[final] = pixels
    return _write_verified(merged, meta, out_path, meta_prefixes)


def flatten(src_path, out_path, meta_prefixes=DEFAULT_META_PREFIXES):
    """Multi-part -> single-part, channel names unchanged."""
    if not os.path.isfile(src_path):
        raise SystemExit("input missing: %s" % src_path)
    merged = read_channels(src_path)
    meta = read_meta(src_path, meta_prefixes)
    return _write_verified(merged, meta, out_path, meta_prefixes)


def selftest():
    tmp = tempfile.mkdtemp(prefix="exrmerge_")
    h, w = 16, 16
    a = np.random.rand(h, w, 3).astype(np.float32)
    z = (np.random.rand(h, w).astype(np.float32) * 50.0) + 1.0
    hdr = {"compression": OpenEXR.ZIP_COMPRESSION,
           "type": OpenEXR.scanlineimage}
    p1 = os.path.join(tmp, "combined.exr")
    p2 = os.path.join(tmp, "depth.exr")
    OpenEXR.File(hdr, {"Combined.R": a[:, :, 0], "Combined.G": a[:, :, 1],
                       "Combined.B": a[:, :, 2]}).write(p1)
    OpenEXR.File(hdr, {"Depth.V": z}).write(p2)
    p3 = os.path.join(tmp, "crypto.exr")
    hdr_c = dict(hdr)
    hdr_c["cryptomatte/abc1234/name"] = "CryptoObject"
    hdr_c["cryptomatte/abc1234/manifest"] = '{"Cube":"a8fce865"}'
    OpenEXR.File(hdr_c, {"CryptoObject00.r": z}).write(p3)
    out = os.path.join(tmp, "merged.exr")
    chans = merge([("Combined", p1), ("Depth", p2), ("CryptoObject00", p3)],
                  {"Depth.V": "Depth.Z"}, out)
    expect = ["Combined.B", "Combined.G", "Combined.R", "CryptoObject00.r",
              "Depth.Z"]
    if chans != expect:
        print("SELFTEST FAIL: %s" % chans)
        return 1
    back = read_channels(out)
    if not np.allclose(back["Depth.Z"], z, atol=1e-6):
        print("SELFTEST FAIL: depth pixels")
        return 1
    meta = read_meta(out, DEFAULT_META_PREFIXES)
    if meta.get("cryptomatte/abc1234/manifest") != '{"Cube":"a8fce865"}':
        print("SELFTEST FAIL: cryptomatte header attrs lost: %s" % meta)
        return 1
    # multi-part round trip: write a 2-part file, make sure read_channels
    # sees BOTH parts (the part-0-only blind spot this tool exists to
    # avoid) and flatten() carries them into one part.
    p4 = os.path.join(tmp, "multipart.exr")
    part_a = dict(hdr_c, name="Combined")
    part_b = dict(hdr_c, name="CryptoObject00")
    OpenEXR.File([OpenEXR.Part(part_a, {"Combined.R": a[:, :, 0]}),
                  OpenEXR.Part(part_b, {"CryptoObject00.r": z})]).write(p4)
    n_parts = len(list(iter_parts(p4)))
    seen = sorted(read_channels(p4).keys())
    if n_parts != 2 or seen != ["Combined.R", "CryptoObject00.r"]:
        print("SELFTEST FAIL: multipart read parts=%d chans=%s"
              % (n_parts, seen))
        return 1
    p5 = os.path.join(tmp, "flat.exr")
    flat = flatten(p4, p5)
    if flat != seen or len(list(iter_parts(p5))) != 1:
        print("SELFTEST FAIL: flatten -> %s" % flat)
        return 1
    print("SELFTEST PASS: %s (+%d cryptomatte header attrs; multipart "
          "read %d parts; flatten ok)" % (", ".join(chans), len(meta),
                                          n_parts))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inspect", nargs="+", metavar="EXR",
                    help="print every part + channel list and exit")
    ap.add_argument("--flatten", metavar="EXR",
                    help="multi-part input to copy into ONE single-part "
                         "file (--out required)")
    ap.add_argument("--out")
    ap.add_argument("--layer", action="append", default=[],
                    help="NAME=PATH (repeatable)")
    ap.add_argument("--rename", action="append", default=[],
                    help="OLD=NEW final-channel rename (repeatable)")
    ap.add_argument("--meta-prefix", action="append", default=None,
                    help="header attribute prefix to copy from inputs "
                         "(repeatable; default 'cryptomatte/')")
    ap.add_argument("--no-meta", action="store_true",
                    help="copy no header attributes at all")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if args.inspect:
        inspect(args.inspect)
        return
    if args.no_meta:
        prefixes = ()
    elif args.meta_prefix:
        prefixes = tuple(args.meta_prefix)
    else:
        prefixes = DEFAULT_META_PREFIXES
    if args.flatten:
        if not args.out:
            ap.error("--flatten needs --out")
        chans = flatten(args.flatten, args.out, meta_prefixes=prefixes)
        print("FLATTENED %d channels -> %s" % (len(chans), args.out))
        return
    if not args.out or not args.layer:
        ap.error("--out and at least one --layer are required")
    specs = []
    for item in args.layer:
        if "=" not in item:
            ap.error("bad --layer %r (want NAME=PATH)" % item)
        name, path = item.split("=", 1)
        specs.append((name.strip(), path.strip()))
    renames = {}
    for item in args.rename:
        old, new = item.split("=", 1)
        renames[old.strip()] = new.strip()
    chans = merge(specs, renames, args.out, meta_prefixes=prefixes)
    print("MERGED %d channels -> %s" % (len(chans), args.out))
    for c in chans:
        print("  " + c)


if __name__ == "__main__":
    main()
