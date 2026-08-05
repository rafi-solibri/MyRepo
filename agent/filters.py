"""Shared qualification filters for daily .NET leadership job hunt.

Enforce title+skills .NET proof, seniority-on-title, location, experience, CTC.
Never treat the page search query as proof of .NET.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


DOTNET_RE = re.compile(
    r"(\.net|dotnet|dot\s*net|asp\.?\s*net|c#|csharp)",
    re.I,
)
SENIORITY_RE = re.compile(
    r"\b(architect|lead|principal|staff\s+(software|engineer)|"
    r"engineering\s+manager|director|avp|head\s+of|manager)\b",
    re.I,
)
SKIP_TITLE_RE = re.compile(
    r"\b(qa|sdet|test\s*engineer|testing|project\s*manager|program\s*manager|"
    r"delivery\s*manager|tpm|presales|salesforce|servicenow|power\s*platform|"
    r"duck\s*creek)\b",
    re.I,
)
PURE_AI_RE = re.compile(
    r"\b(ai\s*engineer|ml\s*engineer|genai|generative\s*ai|data\s*scientist)\b",
    re.I,
)
LOC_OK_RE = re.compile(
    r"(hyderabad|secunderabad|\bhyd\b|remote|wfh|work from home|work-from-home)",
    re.I,
)
LOC_OTHER_METRO_RE = re.compile(
    r"(bengaluru|bangalore|pune|noida|gurgaon|gurugram|chennai|mumbai|delhi|kolkata)",
    re.I,
)
EXP_RANGE_RE = re.compile(r"(\d+)\s*-\s*(\d+)\s*Yrs?", re.I)
SAL_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*Lacs?", re.I)


def normalize_aspnet(text: str) -> str:
    """Normalize ASP.Net → DOTNET before SAP skip logic."""
    return re.sub(r"asp\.?\s*net", "DOTNET", text or "", flags=re.I)


@dataclass
class JobCard:
    title: str
    company: str = ""
    location: str = ""
    experience: str = ""
    salary: str = ""
    skills: str = ""
    url: str = ""
    posted: str = ""


@dataclass
class FilterResult:
    ok: bool
    reasons: list[str]


def parse_experience(text: str) -> tuple[Optional[int], Optional[int]]:
    m = EXP_RANGE_RE.search(text or "")
    if m:
        return int(m.group(1)), int(m.group(2))
    return None, None


def parse_salary_lpa(text: str) -> tuple[Optional[float], Optional[float]]:
    if re.search(r"not disclosed", text or "", re.I):
        return None, None
    m = SAL_RANGE_RE.search(text or "")
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def experience_ok(min_e: Optional[int], max_e: Optional[int], title: str) -> bool:
    if max_e is not None and max_e < 10:
        return False
    if min_e is not None and min_e >= 7:
        return True
    if max_e is not None and max_e >= 12:
        return True
    # Tech Lead / Architect / Principal / Staff: 8–10 / 8–12 bands
    if re.search(r"(tech\s*lead|architect|principal|staff)", title or "", re.I):
        if min_e is not None and max_e is not None and min_e >= 8 and max_e >= 10:
            return True
        if re.search(r"(staff|principal)", title or "", re.I) and max_e is not None and max_e >= 10:
            return True
    return False


def qualify(job: JobCard) -> FilterResult:
    reasons: list[str] = []
    title = job.title or ""
    skills = job.skills or ""
    title_n = normalize_aspnet(title)
    skills_n = normalize_aspnet(skills)

    has_dotnet = bool(DOTNET_RE.search(title_n) or DOTNET_RE.search(skills_n))
    if re.search(r"\bsap\b", f"{title_n} {skills_n}", re.I) and not has_dotnet:
        reasons.append("SAP without .NET")
    if not has_dotnet:
        reasons.append("no .NET in title/skills")

    if not SENIORITY_RE.search(title):
        reasons.append("seniority not on title")
    if SKIP_TITLE_RE.search(title_n):
        reasons.append("skip title category")
    if PURE_AI_RE.search(title) and not has_dotnet:
        reasons.append("pure AI without .NET")

    loc = job.location or ""
    if not LOC_OK_RE.search(loc):
        if LOC_OTHER_METRO_RE.search(loc):
            reasons.append("other metro only")
        elif loc.strip():
            reasons.append("location not Hyd/remote")
        else:
            reasons.append("location unknown")

    min_e, max_e = parse_experience(job.experience or "")
    if min_e is None and max_e is None:
        reasons.append("experience unknown")
    elif not experience_ok(min_e, max_e, title):
        reasons.append(f"exp fail {min_e}-{max_e}")

    _, sal_max = parse_salary_lpa(job.salary or "")
    if sal_max is not None and sal_max < 50:
        reasons.append(f"CTC max {sal_max}<50")

    return FilterResult(ok=not reasons, reasons=reasons)
