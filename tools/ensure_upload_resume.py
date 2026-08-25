#!/usr/bin/env python3
"""Always rebuild resumes/Rafi_Resume.docx from the owner master CV.

Source of truth: resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx
Upload copy:     resumes/Rafi_Resume.docx (+ Architect alias)

Naukri rejects >2MB, so the upload copy is font-stripped via compress_resume_docx.
Everyday portal runs must call this (via bootstrap-job-assets.sh) so a stale
committed Rafi_Resume.docx cannot shadow a newer master.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / "resumes" / "Mohammed_Abdul_Rafi_Ahmed_Resume.docx"
UPLOAD = ROOT / "resumes" / "Rafi_Resume.docx"
ALIAS = ROOT / "resumes" / "Rafi_Resume_Architect.docx"
FINGERPRINT = ROOT / "resumes" / ".upload-resume-fingerprint.json"

sys.path.insert(0, str(ROOT / "tools"))
from compress_resume_docx import compress_docx  # noqa: E402


def _docx_text_sha(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", errors="replace")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", xml)).strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ensure_upload_resume() -> dict:
    if not OWNER.is_file():
        raise FileNotFoundError(f"missing owner master resume: {OWNER}")

    # Always rebuild upload copy from master (never trust a stale Rafi_Resume.docx).
    compress_docx(OWNER, UPLOAD)
    ALIAS.write_bytes(UPLOAD.read_bytes())

    info = {
        "owner": str(OWNER),
        "upload": str(UPLOAD),
        "ownerBytes": OWNER.stat().st_size,
        "uploadBytes": UPLOAD.stat().st_size,
        "textSha256": _docx_text_sha(OWNER),
        "uploadTextSha256": _docx_text_sha(UPLOAD),
    }
    if info["textSha256"] != info["uploadTextSha256"]:
        raise RuntimeError(
            "upload copy text diverged from master after compress — aborting"
        )
    try:
        FINGERPRINT.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    print(
        f"ensure_upload_resume: master={info['ownerBytes']}B → "
        f"upload={info['uploadBytes']}B sha={info['textSha256'][:16]}"
    )
    return info


def main() -> int:
    info = ensure_upload_resume()
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)
