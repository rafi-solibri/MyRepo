#!/usr/bin/env python3
"""Self-test: owner master .docx shrinks under Easy Apply 2MB cap."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.resume_paths import UPLOAD_MAX_BYTES, ensure_upload_size_limit

CANON = _ROOT / "resumes" / "Rafi_Resume.docx"


def main() -> None:
    assert CANON.is_file(), f"missing {CANON}"
    raw = CANON.stat().st_size
    slim = ensure_upload_size_limit(CANON)
    assert slim.is_file(), "slim resume missing"
    assert slim.name == "Rafi_Resume.docx", slim.name
    assert slim.stat().st_size <= UPLOAD_MAX_BYTES, slim.stat().st_size
    assert slim.stat().st_size > 1000, slim.stat().st_size
    with zipfile.ZipFile(slim) as z:
        names = z.namelist()
        assert "word/document.xml" in names
        assert not any(n.startswith("word/fonts/") for n in names)
        xml = z.read("word/document.xml")
        assert b"document" in xml
    print(
        f"resume compress OK raw={raw} slim={slim.stat().st_size} path={slim}"
    )


if __name__ == "__main__":
    main()
