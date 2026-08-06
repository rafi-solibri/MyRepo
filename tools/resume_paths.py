"""Resolve the canonical Rafi resume path for job-apply automations.

Prefer Rafi_Resume.docx. Keep Rafi_Resume_Architect.docx as a same-file alias
for LinkedIn label matching and older prompts.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

CANONICAL_NAME = "Rafi_Resume.docx"
LEGACY_ALIAS = "Rafi_Resume_Architect.docx"
RESUME_LABEL = "Rafi_Resume"  # LinkedIn Easy Apply label text

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


def resume_upload_path() -> str:
    return str(ensure_resume_aliases())


if __name__ == "__main__":
    p = ensure_resume_aliases()
    print(p)
    print("label:", RESUME_LABEL)
    print("size:", p.stat().st_size)
