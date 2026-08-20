"""Campus company allowlist helpers (Python side — Indeed + discovery)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from tools.hitechcity.filters import company_name_match

_COMPANIES_PATH = Path(__file__).with_name("companies.json")
_UNSET = object()
_cache: list[str] | None | object = _UNSET


def allowlist_path() -> str | None:
    return os.environ.get("HITECHCITY_COMPANY_ALLOWLIST") or None


def load_allowlist_names() -> list[str] | None:
    """Return original company names when allowlist env is set; None = no filter."""
    global _cache
    if _cache is not _UNSET:
        return _cache  # type: ignore[return-value]
    p = allowlist_path()
    if not p:
        _cache = None
        return None
    try:
        raw = json.loads(Path(p).read_text(encoding="utf-8"))
        names: list[str] = []
        if isinstance(raw, list):
            names = [x if isinstance(x, str) else (x or {}).get("name") for x in raw]
        elif isinstance(raw, dict):
            if isinstance(raw.get("companies"), list):
                names = [c.get("name") for c in raw["companies"] if isinstance(c, dict)]
            elif isinstance(raw.get("names"), list):
                names = list(raw["names"])
        _cache = [n for n in names if n]
    except Exception:
        _cache = None
    return _cache  # type: ignore[return-value]


def reset_allowlist_cache() -> None:
    global _cache
    _cache = _UNSET


def company_allowed(company_name: str) -> bool:
    names = load_allowlist_names()
    if names is None:
        return True
    if not names:
        return False
    for target in names:
        if company_name_match(target, company_name or ""):
            return True
    return False


def _skip_uhg_enabled() -> bool:
    raw = (os.environ.get("HITECHCITY_SKIP_UHG") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


_UHG_ALLOWLIST_SKIP = {
    "optum",
    "unitedhealth group",
    "united health",
    "unitedhealth",
    "uhg",
}


def write_allowlist_artifact(companies: list[dict], dest: Path | None = None) -> Path:
    """Write name-only allowlist JSON for board subprocesses.

    When HITECHCITY_SKIP_UHG is on (default), drop Optum / UnitedHealth Group so
    Naukri/Foundit/etc. do not burn the board cap on Taleo login walls.
    """
    out = dest or Path(
        os.environ.get(
            "HITECHCITY_ALLOWLIST_OUT",
            "/opt/cursor/artifacts/hitechcity-company-allowlist.json",
        )
    )
    if not out.parent.is_dir():
        out = Path(__file__).resolve().parents[2] / "artifacts" / "hitechcity-company-allowlist.json"
    names: set[str] = set()
    for c in companies:
        name = (c.get("name") or "").strip()
        if not name:
            continue
        if _skip_uhg_enabled() and name.lower() in _UHG_ALLOWLIST_SKIP:
            continue
        names.add(name)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"names": sorted(names)}, indent=2), encoding="utf-8")
    return out


def load_companies_file(path: Path | None = None) -> dict:
    p = path or _COMPANIES_PATH
    return json.loads(p.read_text(encoding="utf-8"))
