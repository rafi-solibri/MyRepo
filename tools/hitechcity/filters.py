#!/usr/bin/env python3
"""Eligibility filters for Hitech City / Knowledge City campus targeting."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

try:
    from tools.linkedin.filters import (  # noqa: F401
        TITLE_BLACKLIST,
        JD_HARD_BLACKLIST,
        TITLE_OK,
        HYD_OK,
        REMOTE_OK,
        BAD_CITY,
        location_allowed,
        jd_blacklist,
        skip_reason as linkedin_skip_reason,
    )
except Exception:
    from linkedin.filters import (  # type: ignore  # noqa: F401
        TITLE_BLACKLIST,
        JD_HARD_BLACKLIST,
        TITLE_OK,
        HYD_OK,
        REMOTE_OK,
        BAD_CITY,
        location_allowed,
        jd_blacklist,
        skip_reason as linkedin_skip_reason,
    )

CAMPUS_OK = re.compile(
    r"knowledge\s*city|knowledge\s*park|mindspace|madhapur|hitech\s*city|hitec\s*city|"
    r"gachibowli|raidurg|raidurgam|cyber\s*pearl|the\s*v\b|ascendas|dlf\s*cyber|"
    r"divyasree|\borion\b|sattva|\boctave\b|cyberabad|financial\s*district|"
    r"\brmz\b|\bnexity\b|sky\s*view|skyview|\bfutura\b|\braheja\b",
    re.I,
)

DOTNETISH = re.compile(r"\.net|dotnet|\bc#\b|asp\.net|azure", re.I)

# Owner: do not apply to AI/ML roles (campus .NET/EM/Staff track only).
AIML_TITLE_SKIP = re.compile(
    r"\bai\s*/\s*ml\b|\bai\s*&\s*ml\b|\baiml\b|\bai-ml\b|"
    r"\bmachine\s*learning\b|\bdeep\s*learning\b|\bneural\s*net|"
    r"\bgen(?:erative)?\s*ai\b|\bllm\b|\blarge\s*language\s*model\b|"
    r"\bnlp\b|\bcomputer\s*vision\b|\bdata\s*scientist\b|"
    r"\bai\s*engineer\b|\bml\s*engineer\b|\bai\s*scientist\b|"
    r"\bai\s*architect\b|\bml\s*architect\b|\bai\s*technical\b|"
    r"\bartificial\s*intelligence\b|"
    r"\brocm\b|\bcuda\b|gpu\s*/\s*cpu|kernel\s*optimization|"
    r"\bai\s*native\b|\bdata\s*&\s*ai\b|\(\s*ai\b|\bai\s*\)",
    re.I,
)


def skip_reason(role: str, company: str = "", jd: str = "") -> str | None:
    title = role or ""
    if AIML_TITLE_SKIP.search(title):
        return "title: AI/ML excluded"
    return linkedin_skip_reason(role, company, jd)


def title_matches_senior_stack(role: str) -> bool:
    if AIML_TITLE_SKIP.search(role or ""):
        return False
    return bool(TITLE_OK.search(role or ""))


def location_or_campus_ok(loc: str, workplace: str = "", jd_snip: str = "") -> bool:
    if location_allowed(loc, workplace):
        return True
    blob = f"{loc} {workplace} {jd_snip}"
    if CAMPUS_OK.search(blob) and not (BAD_CITY.search(blob) and not REMOTE_OK.search(blob)):
        return True
    return False


def _norm_company(s: str) -> str:
    s = (s or "").lower()
    s = s.replace("j.p.", "jp").replace("j p ", "jp ")
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def company_name_match(target: str, found: str) -> bool:
    t = _norm_company(target)
    f = _norm_company(found)
    if not t or not f:
        return False
    if t == f:
        return True
    t_tokens = set(t.split())
    f_tokens = set(f.split())
    short = min(len(t), len(f)) <= 3
    if short:
        # Short codes (EY, GE, …): whole-token only — never "ey" ⊂ "blueyonder".
        if (len(t) <= 3 and t in f_tokens) or (len(f) <= 3 and f in t_tokens):
            return True
    else:
        if t in f or f in t:
            return True
        # Collapse jpmorganchase style
        t_compact = t.replace(" ", "")
        f_compact = f.replace(" ", "")
        if t_compact in f_compact or f_compact in t_compact:
            return True
    aliases = [
        ({"jpmorgan", "jp", "chase", "jpmc", "jpmorganchase"}, {"jpmorgan", "jp", "chase", "jpmc", "morgan"}),
        ({"meta", "facebook"}, {"meta", "facebook"}),
        ({"amd", "xilinx"}, {"amd", "xilinx"}),
        ({"gevernova", "ge", "vernova"}, {"gevernova", "ge", "vernova"}),
        ({"larsen", "toubro", "lt"}, {"larsen", "toubro", "lt"}),
        ({"goldman", "sachs"}, {"goldman", "sachs"}),
        ({"palo", "alto", "networks"}, {"palo", "alto", "networks"}),
    ]
    for left, right in aliases:
        if t_tokens & left and f_tokens & right:
            return True
    if short:
        return False
    return len(t_tokens & f_tokens) >= max(1, min(2, len(t_tokens)))


def campus_company_matches(target: str, found: str, body_head: str = "") -> bool:
    """Match the LinkedIn company pill to a campus tenant.

    Never treat JD/title `bodyHead` as the company when a distinct pill is
    present — e.g. insightsoftware "Lead Software Engineer (Oracle/BI/.Net)"
    must not match campus target Oracle.
    """
    pill = (found or "").strip()
    if pill:
        return company_name_match(target, pill)
    # Empty pill: do not scrape stack words out of the title/JD blob.
    _ = body_head
    return False


def prefer_dotnet(role: str, jd: str = "") -> bool:
    return bool(DOTNETISH.search(f"{role} {jd}"))
