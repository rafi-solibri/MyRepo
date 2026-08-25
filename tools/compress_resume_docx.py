#!/usr/bin/env python3
"""Shrink a .docx for portal uploads that cap at ~2MB (Naukri).

Owner master resumes often embed large .odttf fonts. Stripping
word/fonts/* (and fontTable embeds) keeps text/layout while landing
well under Naukri's client-side 2MB reject.
"""
from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path

NAUKRI_MAX_BYTES = 2 * 1024 * 1024
TARGET_BYTES = int(1.85 * 1024 * 1024)


def _strip_font_table_embeds(xml: bytes) -> bytes:
    text = xml.decode("utf-8", errors="ignore")
    # Remove embedRegular / embedBold / etc. relationships on <w:font>
    text = re.sub(r'\s+r:embed(?:Regular|Bold|Italic|BoldItalic)="[^"]*"', "", text)
    return text.encode("utf-8")


def compress_docx(src: Path, dest: Path | None = None, max_bytes: int = TARGET_BYTES) -> Path:
    src = Path(src)
    dest = Path(dest) if dest else src
    if not src.is_file():
        raise FileNotFoundError(src)

    if src.stat().st_size <= max_bytes and dest.resolve() == src.resolve():
        return dest

    buf = io.BytesIO()
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(
        buf, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zout:
        for info in zin.infolist():
            name = info.filename
            if name.startswith("word/fonts/"):
                continue
            data = zin.read(info.filename)
            if name == "word/fontTable.xml":
                data = _strip_font_table_embeds(data)
            # Drop fontTable rels that only pointed at embeds
            if name == "word/_rels/fontTable.xml.rels":
                rel = data.decode("utf-8", errors="ignore")
                rel = re.sub(
                    r'<Relationship[^>]*Target="fonts/[^"]*"[^>]*/>',
                    "",
                    rel,
                )
                data = rel.encode("utf-8")
            zi = zipfile.ZipInfo(filename=name, date_time=info.date_time)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zout.writestr(zi, data)

    out = buf.getvalue()
    if len(out) > max_bytes:
        raise RuntimeError(
            f"compressed docx still {len(out)} bytes (max {max_bytes}); "
            f"source={src} size={src.stat().st_size}"
        )

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.resolve() == src.resolve():
        # Atomic replace
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(out)
        tmp.replace(dest)
    else:
        dest.write_bytes(out)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src", nargs="?", default="resumes/Rafi_Resume.docx")
    ap.add_argument("-o", "--dest", default=None)
    ap.add_argument(
        "--max-bytes",
        type=int,
        default=TARGET_BYTES,
        help=f"default {TARGET_BYTES} (Naukri hard cap {NAUKRI_MAX_BYTES})",
    )
    args = ap.parse_args()
    dest = compress_docx(Path(args.src), Path(args.dest) if args.dest else None, args.max_bytes)
    print(f"{dest} size={dest.stat().st_size}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
