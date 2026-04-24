"""
Extract the __BUN.__bun section from a Bun --compile Mach-O 64-bit binary.

Walks LC_SEGMENT_64 load commands to find the __BUN segment, slices its bytes,
and writes the extracted bundle to disk along with its SHA-256.

For the specific review target, the values at commit 8ace1d9c were:
  __BUN segment:  fileoff=59,588,608  filesize=3,112,960
  __BUN.__bun:    offset=59,588,608   size=3,098,213
  bundle sha256:  fd189159fc07898ec428524721702ec2712dcb0c92471fd0f09c1c69aa367829

Standard library only. Python 3.9+. Works on any platform (does not require
llvm-objdump or otool).

Usage:
  python extract_bun_section.py BINARY [--out bun-section.bin]
"""

from __future__ import annotations
import argparse
import hashlib
import struct
import sys
from pathlib import Path


MH_MAGIC_64 = 0xFEEDFACF
LC_SEGMENT_64 = 0x19


def parse_mach_o(data: bytes) -> list[dict]:
    magic = struct.unpack_from("<I", data, 0)[0]
    if magic != MH_MAGIC_64:
        raise ValueError(f"unexpected magic {magic:#x} — expected 64-bit Mach-O {MH_MAGIC_64:#x}")
    ncmds = struct.unpack_from("<I", data, 16)[0]
    segments = []
    off = 32
    for _ in range(ncmds):
        cmd, cmdsize = struct.unpack_from("<II", data, off)
        if cmd == LC_SEGMENT_64:
            segname = data[off + 8 : off + 8 + 16].rstrip(b"\x00").decode("utf-8", errors="replace")
            fileoff = struct.unpack_from("<Q", data, off + 40)[0]
            filesize = struct.unpack_from("<Q", data, off + 48)[0]
            nsects = struct.unpack_from("<I", data, off + 64)[0]
            sections = []
            sec_off = off + 72
            for _ in range(nsects):
                sectname = data[sec_off : sec_off + 16].rstrip(b"\x00").decode("utf-8", errors="replace")
                ssegname = data[sec_off + 16 : sec_off + 32].rstrip(b"\x00").decode("utf-8", errors="replace")
                ssize = struct.unpack_from("<Q", data, sec_off + 40)[0]
                soffset = struct.unpack_from("<I", data, sec_off + 48)[0]
                sections.append({"name": sectname, "segname": ssegname,
                                 "offset": soffset, "size": ssize})
                sec_off += 80
            segments.append({"segname": segname, "fileoff": fileoff,
                             "filesize": filesize, "sections": sections})
        off += cmdsize
    return segments


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("binary")
    ap.add_argument("--out", default="bun-section.bin")
    args = ap.parse_args()

    data = Path(args.binary).read_bytes()
    segments = parse_mach_o(data)

    print(f"total segments: {len(segments)}")
    for s in segments:
        print(f"  {s['segname']:<16}  fileoff={s['fileoff']:>12}  filesize={s['filesize']:>12}  nsects={len(s['sections'])}")
        for sec in s["sections"]:
            print(f"    {s['segname']}.{sec['name']:<18}  off={sec['offset']:>12}  size={sec['size']:>12}")

    bun = next((s for s in segments if s["segname"] == "__BUN"), None)
    if not bun:
        print("ERROR: no __BUN segment found — is this a Bun --compile binary?", file=sys.stderr)
        return 1
    bun_section = next((sec for sec in bun["sections"] if sec["name"] == "__bun"), None)
    if not bun_section:
        print("ERROR: __BUN segment has no __bun section", file=sys.stderr)
        return 1

    off = bun_section["offset"]
    size = bun_section["size"]
    bundle = data[off : off + size]
    sha = hashlib.sha256(bundle).hexdigest()

    Path(args.out).write_bytes(bundle)
    print(f"\nextracted {size:,} bytes from __BUN.__bun")
    print(f"  source offset: {off:,}")
    print(f"  output:        {args.out}")
    print(f"  sha256:        {sha}")

    # Peek the header so the reader can see it's really JS
    head = bundle[:256].decode("latin-1").translate(str.maketrans({c: "." for c in map(chr, list(range(0, 32)) + list(range(127, 256)))}))
    print(f"\nfirst 256 bytes (non-printable → '.'):")
    print(f"  {head}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
