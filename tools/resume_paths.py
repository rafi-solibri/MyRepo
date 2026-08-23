"""Resolve the canonical Rafi resume path for job-apply automations.

Owner source of truth: resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx (synced into
Rafi_Resume.docx). Prefer Rafi_Resume.docx for uploads. Keep
Rafi_Resume_Architect.docx as a same-file alias for LinkedIn label matching and
older prompts. JD tailor starts from this file and keeps the upload filename.
"""

from __future__ import annotations

import os
import re
import shutil
import zipfile
from pathlib import Path

CANONICAL_NAME = "Rafi_Resume.docx"
LEGACY_ALIAS = "Rafi_Resume_Architect.docx"
RESUME_LABEL = "Rafi_Resume"  # LinkedIn Easy Apply label text
# Easy Apply upload cap: "Please upload a smaller file (2 MB or less)."
UPLOAD_MAX_BYTES = int(os.environ.get("RESUME_UPLOAD_MAX_BYTES", str(2 * 1024 * 1024)))

SEARCH_DIRS = [
    Path("/workspace/resumes"),
    Path(__file__).resolve().parents[1] / "resumes",
    Path("/home/ubuntu/resumes"),
    Path("/home/ubuntu/Documents"),
    Path("/home/ubuntu/Downloads"),
    Path("/opt/cursor/artifacts"),
    Path.cwd() / "resumes",
    Path.cwd(),
]


def find_resume() -> Path | None:
    for name in (CANONICAL_NAME, LEGACY_ALIAS):
        for d in SEARCH_DIRS:
            p = d / name
            if p.is_file() and p.stat().st_size > 1000:
                return p
    return None


def ensure_resume_aliases() -> Path:
    """Return canonical path; materialize aliases in common dirs."""
    src = find_resume()
    if src is None:
        raise FileNotFoundError(
            f"Missing {CANONICAL_NAME}. Expected under /workspace/resumes/ "
            "(run scripts/bootstrap-job-assets.sh)."
        )
    # Normalize: if only legacy exists, copy to canonical next to it
    canonical = src.with_name(CANONICAL_NAME) if src.name != CANONICAL_NAME else src
    if src.name != CANONICAL_NAME:
        shutil.copy2(src, canonical)
        src = canonical

    for d in (
        Path("/workspace/resumes"),
        Path("/home/ubuntu/resumes"),
        Path("/home/ubuntu/Documents"),
        Path("/home/ubuntu/Downloads"),
    ):
        try:
            d.mkdir(parents=True, exist_ok=True)
            for name in (CANONICAL_NAME, LEGACY_ALIAS):
                dest = d / name
                if not dest.is_file() or dest.resolve() != src.resolve():
                    shutil.copy2(src, dest)
        except OSError:
            continue
    return src


# Per-job tailored resume (set by LinkedIn/ATS helpers before upload).
_ACTIVE_RESUME: Path | None = None


def set_active_resume(path: str | Path | None) -> None:
    """Prefer this path for the next ATS/Easy Apply upload (JD-tailored copy)."""
    global _ACTIVE_RESUME
    if path is None:
        _ACTIVE_RESUME = None
        return
    p = Path(path)
    _ACTIVE_RESUME = p if p.is_file() and p.stat().st_size > 1000 else None


def clear_active_resume() -> None:
    set_active_resume(None)


def _strip_embedded_fonts(src: Path, dest: Path) -> Path:
    """Rewrite a .docx without embedded font binaries (keeps text/styles).

    Owner master resume is ~3.6MB almost entirely from word/fonts/*.odttf.
    Easy Apply rejects uploads over 2MB.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    font_name_re = re.compile(r"word/fonts/|\.odttf$", re.I)
    with zipfile.ZipFile(src, "r") as zin, zipfile.ZipFile(
        dest, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for info in zin.infolist():
            name = info.filename
            if font_name_re.search(name):
                continue
            data = zin.read(name)
            if name.endswith("[Content_Types].xml"):
                data = re.sub(
                    br'<Override[^>]+(?:word/fonts/|\.odttf)[^/]*/>',
                    b"",
                    data,
                    flags=re.I,
                )
            elif name.endswith("fontTable.xml"):
                data = re.sub(
                    br'\s+w:embed(?:Regular|Bold|Italic|BoldItalic)="[^"]*"',
                    b"",
                    data,
                )
            elif name.endswith("fontTable.xml.rels"):
                data = re.sub(
                    br'<Relationship[^>]+Target="[^"]*fonts/[^"]*"[^/]*/>',
                    b"",
                    data,
                    flags=re.I,
                )
            zout.writestr(name, data)
    return dest


def ensure_upload_size_limit(
    src: str | Path | None = None,
    *,
    limit: int = UPLOAD_MAX_BYTES,
) -> Path:
    """Return a same-name Rafi_Resume.docx that is under the 2MB Easy Apply cap."""
    path = Path(src) if src else Path(resume_upload_path_raw())
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.stat().st_size <= limit:
        return path
    dest = path.parent / "upload-2mb" / CANONICAL_NAME
    if dest.is_file() and dest.stat().st_size <= limit:
        return dest
    _strip_embedded_fonts(path, dest)
    if dest.stat().st_size > limit:
        raise RuntimeError(
            f"resume still {dest.stat().st_size} bytes after font strip (limit {limit})"
        )
    return dest


def resume_upload_path_raw() -> str:
    """Return the resume file before the 2MB Easy Apply shrink."""
    env = (os.environ.get("RESUME_UPLOAD_PATH") or "").strip()
    if env and Path(env).is_file() and Path(env).stat().st_size > 1000:
        return str(Path(env).resolve())
    if _ACTIVE_RESUME is not None and _ACTIVE_RESUME.is_file():
        return str(_ACTIVE_RESUME)
    return str(ensure_resume_aliases())


def resume_upload_path() -> str:
    """Return the resume file to upload (active tailored copy, else canonical).

    Easy Apply caps uploads at 2MB; strip embedded fonts when needed.
    """
    raw = Path(resume_upload_path_raw())
    try:
        return str(ensure_upload_size_limit(raw))
    except Exception as e:
        print("resume size shrink warning:", e)
        return str(raw)


if __name__ == "__main__":
    p = ensure_resume_aliases()
    print(p)
    print("label:", RESUME_LABEL)
    print("size:", p.stat().st_size)
