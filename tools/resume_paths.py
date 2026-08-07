"""Resolve the canonical Rafi resume path for job-apply automations.

Canonical upload file: Rafi_Resume_Technical_Architect.docx
Legacy filenames (Rafi_Resume.docx / Rafi_Resume_Architect.docx) are same-file
aliases for older prompts and LinkedIn saved-resume labels.
"""

from __future__ import annotations

import shutil
from pathlib import Path

CANONICAL_NAME = "Rafi_Resume_Technical_Architect.docx"
LEGACY_ALIASES = (
    "Rafi_Resume.docx",
    "Rafi_Resume_Architect.docx",
)
RESUME_LABEL = "Rafi_Resume_Technical_Architect"  # LinkedIn Easy Apply label text
# Also accept these labels if the portal still shows an older saved copy
RESUME_LABEL_ALIASES = (
    "Rafi_Resume_Technical_Architect",
    "Rafi_Resume_Architect",
    "Rafi_Resume",
)

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
    for name in (CANONICAL_NAME, *LEGACY_ALIASES):
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
    # Prefer/normalize to canonical filename next to the found source
    canonical = src.with_name(CANONICAL_NAME) if src.name != CANONICAL_NAME else src
    if src.name != CANONICAL_NAME:
        shutil.copy2(src, canonical)
        src = canonical
    # If a legacy file was newer somehow, still keep canonical as the bootstrap source
    # once installed under /workspace/resumes/.

    for d in (
        Path("/workspace/resumes"),
        Path("/home/ubuntu/resumes"),
        Path("/home/ubuntu/Documents"),
        Path("/home/ubuntu/Downloads"),
        Path("/opt/cursor/artifacts"),
    ):
        try:
            d.mkdir(parents=True, exist_ok=True)
            for name in (CANONICAL_NAME, *LEGACY_ALIASES):
                dest = d / name
                if not dest.is_file() or dest.resolve() != src.resolve():
                    shutil.copy2(src, dest)
        except OSError:
            continue
    return src


def resume_upload_path() -> str:
    return str(ensure_resume_aliases())


if __name__ == "__main__":
    p = ensure_resume_aliases()
    print(p)
    print("label:", RESUME_LABEL)
    print("size:", p.stat().st_size)
