#!/usr/bin/env python3
"""Scan company career portals for Hyd senior .NET/architect roles and apply."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from playwright.sync_api import Page, sync_playwright

from tools.hitechcity.ats_fill import (
    attempt_ats_apply,
    auth_wall_url,
    blocked_wall,
    looks_workday_page,
    try_click_named,
)
from tools.ats.complete import classify_ats_host
from tools.hitechcity.filters import (
    location_or_campus_ok,
    prefer_dotnet,
    skip_reason,
    title_matches_senior_stack,
)
from tools.hitechcity.apply_notify import notify_application_result


def _safe_print(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc, errors="replace"), flush=True)

CDP = os.environ.get("HITECHCITY_CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))
MAX_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_PER_COMPANY", "8"))
# Raised for discovery-expanded campus tenant list (still priority-sorted).
MAX_COMPANIES = int(os.environ.get("HITECHCITY_MAX_COMPANIES", "60"))
# Tight default: SSO / Sign-In walls must fail fast so more campus tenants are tried.
TIME_CAP_S = int(os.environ.get("HITECHCITY_ATS_TIME_CAP_S", os.environ.get("HITECHCITY_EXT_ATS_TIME_CAP_S", "90")))
MAX_WALLS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_WALLS", "3"))
# Soft incompletes must not starve remaining matching roles at the same company.
MAX_ATTEMPTS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_ATTEMPTS", "16"))
# Headed/owner-available runs get a longer ATS budget so forms can be finished.
# Owner-asleep keeps the short cron cap even on headed CDP.
if (
    (os.environ.get("HITECHCITY_OWNER_ASLEEP") or "").strip().lower()
    not in ("1", "true", "yes")
) and (
    (os.environ.get("HOME_LOCAL") or "").strip().lower() in ("1", "true", "yes")
    or (os.environ.get("CHROME_HEADLESS") or "1").strip() in ("0", "false", "no")
):
    if not (os.environ.get("HITECHCITY_ATS_TIME_CAP_S") or os.environ.get("HITECHCITY_EXT_ATS_TIME_CAP_S")):
        TIME_CAP_S = max(TIME_CAP_S, 120)

# Portal search terms — lead/staff/manager first (companies.json often baked "architect" only).
CAREERS_SEARCH_KEYWORDS = [
    "Engineering Manager",
    "Technical Lead",
    "Solution Architect",
    "Principal Software Engineer",
    "Software Development Manager",
    "Staff Software Engineer",
    ".NET Architect",
    "Lead Software Engineer",
]
MAX_CAREERS_KEYWORD_SEARCHES = int(os.environ.get("HITECHCITY_CAREERS_KEYWORD_SEARCHES", "4"))

_SEARCH_PARAM_KEYS = (
    "keywords",
    "keyword",
    "q",
    "search",
    "query",
    "searchKeyword",
    "base_query",
)
_LOCATION_PARAM_KEYS = (
    "location",
    "locations",
    "loc",
    "loc_query",
    "locationsearch",
    "city",
)
CAREERS_LOCATION = os.environ.get("HITECHCITY_CAREERS_LOCATION", "Hyderabad")
CAREERS_LOCATION_FULL = os.environ.get(
    "HITECHCITY_CAREERS_LOCATION_FULL", "Hyderabad, Telangana, India"
)

TITLE_HINT = re.compile(
    r"architect|technical lead|tech lead|technology lead|engineering manager|"
    r"engineering lead|development manager|software (development )?manager|"
    r"principal|staff|lead (software|development|engineer)|"
    r"\.net|dotnet|azure|cloud architect|solution|"
    r"director.*eng|head of eng",
    re.I,
)
LOC_HINT = re.compile(
    r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg|"
    r"\bindia\b|\bremote\b|\bwfh\b|work from home",
    re.I,
)
# Explicit non-Hyd workplace signals on the card / title (never rely on page footer "India").
BAD_LOC_HINT = re.compile(
    r"\b(austin|seattle|sunnyvale|redmond|boca\s*raton|st\.?\s*louis|london|new york|"
    r"toronto|dublin|san\s*francisco|mountain\s*view|cupertino|menlo\s*park|"
    r"united\s*states|united\s*kingdom|\busa\b|\buk\b|berkshire|reading|"
    r"romania|bucharest|poland|warsaw|germany|berlin|munich|amsterdam|netherlands|"
    r"washington,\s*redmond|multiple\s*locations|"
    r"canada|nova\s*scotia|maryland|ontario|british\s*columbia|quebec|"
    r"bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|gurugram|"
    r"brazil|s[aã]o\s*carlos|malaysia|cyberjaya|costa\s*rica|heredia|nottingham|"
    r"kuala\s*lumpur|mexico|colombia|chile|argentina|"
    # Middle East / APAC / other foreign workplaces (Oracle multi-location cards).
    r"dubai|abu\s*dhabi|united\s*arab\s*emirates|\buae\b|saudi|riyadh|jeddah|"
    r"qatar|doha|kuwait|bahrain|oman|muscat|"
    r"singapore|hong\s*kong|tokyo|japan|seoul|korea|sydney|melbourne|australia|"
    r"auckland|new\s*zealand|manila|philippines|jakarta|indonesia|bangkok|thailand|"
    r"israel|tel\s*aviv|haifa|switzerland|zurich|geneva|france|paris|sweden|stockholm|"
    r"us[- ](?:texas|oregon|california|washington|arizona|colorado|massachusetts|"
    r"florida|georgia|illinois|new[- ]york)|india[- ](?:bangalore|bengaluru)|"
    r"hillsboro|santa[- ]clara|folsom|"
    r"tx|wa|ca|fl|ny|il|ga|nc|ma)\b",
    re.I,
)
# Titles that match broad TITLE_OK (staff/principal/architect) but are wrong for this run.
CAREERS_TITLE_SKIP = re.compile(
    r"system\s*test|quality\s*(platform|assurance|engineering)|threat\s*detection|"
    r"project\s*analyst|project\s*manager|industrial\s*design|hardware\s*architect|"
    r"machine\s*learning|gpu\s*software|gpu\s*/\s*cpu|kernel\s*optimization|embedded\s*software|"
    r"field\s*robotics|platform\s*power|network\s*hardware|"
    r"product\s*manager|network\s*architect|"
    r"chemical\s*mechanical|planarization|\bcmp\b|soc\s*compute|"
    r"memory\s*subsystem|foundry\s*solutions|"
    # Silicon / chip design (Principal Physical Design matched TITLE_HINT via Principal).
    r"physical\s*design|silicon\s*design|silicon\s*engineer|product\s*design\s*manager|"
    r"chiplet|\basic\b|\bvlsi\b|rtl\s*design|dft\s*engineer|"
    r"analog\s*design|digital\s*design\s*engineer|verification\s*engineer|"
    r"sales\s*specialist|especialista|"
    r"program\s*manager|technical\s*program\s*manager|\btpm\b|"
    r"\bai\s*native\b|\bdata\s*&\s*ai\b|staff\s*engineer\s*\(\s*ai|"
    r"\bai\s*/\s*ml\b|\bai\s*&\s*ml\b|\baiml\b|\bai-ml\b|"
    r"\bdeep\s*learning\b|\bgen(?:erative)?\s*ai\b|\bllm\b|"
    r"\bai\s*engineer\b|\bml\s*engineer\b|\bai\s*architect\b|\bml\s*architect\b|"
    r"\bartificial\s*intelligence\b|\bcuda\b|\brocm\b|"
    r"engineer in test|\bsdet\b|cyber\s*security|cybersecurity|"
    r"database engineer",
    re.I,
)
# JD snippets that mean the role is wrong-stack even when the TITLE is generic Architect.
JD_WRONG_STACK = re.compile(
    r"salesforce solutions|sfdc development|sfdc lightning|omnistudio|"
    r"mobile architect|ionic capacitor|network security architect|zscaler|"
    r"mandatory[:\s]+(java|python|node|salesforce)|"
    r"required[:\s]+(java|python|node|salesforce)|"
    r"only\s+(java|python|node|salesforce)\b",
    re.I,
)
# Kept for callers; prefer auth_wall_url() which also covers Indeed OAuth.
# These listings never expose a guest ATS form — skip the company so Workday/iCIMS
# inventory is not starved by Amazon/Microsoft/Qualcomm SSO walls.
SSO_ONLY_CAREERS_RE = re.compile(
    r"amazon\.jobs|passport\.amazon\.jobs|apply\.careers\.microsoft\.com|"
    r"careers\.microsoft\.com|careers\.qualcomm\.com",
    re.I,
)
# Heavy SPAs that hang extract_job_links (no guest ATS form anyway).
HANG_SCAN_HOST_RE = re.compile(
    r"higher\.gs\.com|metacareers\.com|jobs\.apple\.com|"
    r"pwc\.com/.*/careers|tcs\.com/careers$",
    re.I,
)
GUEST_ATS_HOST_RE = re.compile(
    r"myworkdayjobs|icims\.com|oraclecloud\.com|taleo\.net|smartrecruiters\.com|"
    r"greenhouse\.io|lever\.co|myworkdaysite",
    re.I,
)
# DataDome / reCAPTCHA boards burn the run if scanned first (Experian/Blackbaud/PAN).
CAPTCHA_PRONE_HOST_RE = re.compile(
    r"smartrecruiters\.com|careers\.blackbaud\.com|jobs\.paloaltonetworks\.com",
    re.I,
)
AUTH_HOST = re.compile(
    r"passport\.amazon\.jobs|login\.microsoftonline|accounts\.google|"
    r"secure\.indeed\.com|indeed\.com/auth|okta\.com|login\.microsoft|"
    r"auth\.|signin\.|sso\.|login\.cognizant|cognizant\.okta|"
    r"talent\.cognizant\.com/[^?\s]*(?:login|login2)|"
    r"eightfold\.ai/(?:login|signin|auth)|"
    r"uhg\.taleo\.net/.*/(login|accessmanagement)",
    re.I,
)
# Optum / UHG Taleo login tabs poison pages[0] and starve other portals.
UHG_HOST_RE = re.compile(r"unitedhealthgroup\.com|uhg\.taleo\.net", re.I)
UHG_NAME_RE = re.compile(r"^(optum|unitedhealth\s*group|uhg|united\s*health)$", re.I)


def _close_auth_popups(page: Page) -> None:
    """Close Indeed/Google SSO tabs spawned by SmartRecruiters OneClick Apply."""
    try:
        ctx = page.context
        keep = page
        for p in list(ctx.pages):
            if p is keep:
                continue
            try:
                if auth_wall_url(p.url or ""):
                    p.close()
            except Exception:
                continue
    except Exception:
        pass


def _context_hit_auth_wall(page: Page) -> bool:
    try:
        if auth_wall_url(page.url or ""):
            return True
        for p in page.context.pages:
            if auth_wall_url(p.url or ""):
                return True
    except Exception:
        return False
    return False
NAV_CHROME_RE = re.compile(
    r"skip to (main )?content|^jobs?\s+\d+|turn on job alerts|go to home|"
    r"^sitemap$|^manage profile$|^sign in$|^careers home$|^see all jobs$",
    re.I,
)
JOB_ID_HREF_RE = re.compile(
    r"/jobs?/\d|/job/\d|gh_jid=|[?&](jobId|pid|reqId)=\d|/jobs/\d{4,}|"
    r"smartrecruiters\.com/[^/]+/\d{6,}|myworkdayjobs\.com/.+/job/|"
    r"icims\.com/jobs/\d+|jobdetails\?id=|/careers/jobdetails",
    re.I,
)


@dataclass
class CareersReport:
    startedAt: str
    finishedAt: str = ""
    applied: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    scanned: list[dict[str, Any]] = field(default_factory=list)


def load_companies() -> list[dict[str, Any]]:
    data = json.loads(COMPANIES_PATH.read_text())
    companies = sorted(
        data.get("companies", []),
        key=lambda c: (_company_ats_rank(c), c.get("priority", 9), c.get("name", "")),
    )
    return companies


def rewrite_careers_search_keyword(url: str, keyword: str) -> str:
    """Replace baked search terms (often 'architect') with the requested role keyword."""
    if not url or not keyword:
        return url
    parts = urlparse(url)
    qs = parse_qs(parts.query, keep_blank_values=True)
    hit = False
    for key in _SEARCH_PARAM_KEYS:
        if key in qs and qs[key]:
            qs[key] = [keyword]
            hit = True
    if not hit:
        # Prefer 'keywords' when the portal has no search param yet.
        qs["keywords"] = [keyword]
    # Flatten for urlencode
    flat: list[tuple[str, str]] = []
    for k, vals in qs.items():
        for v in vals:
            flat.append((k, v))
    return urlunparse(parts._replace(query=urlencode(flat, doseq=True)))


def pin_careers_hyderabad_location(url: str) -> str:
    """HARD: every careers search URL must carry Hyderabad.

    Always set/overwrite location-like query params. Invent `location=Hyderabad`
    when missing. Host-specific keys: loc_query (Amazon), locationsearch
    (Blackbaud), loc (IBM), lc (Accenture), city+country (Salesforce),
    searchLocation (iCIMS). Path hubs like `/search-jobs/Hyderabad/` stay.
    Workday still gets location= for consistency; UI facet pin is separate.
    """
    if not url:
        return url
    parts = urlparse(url)
    path = parts.path or ""
    host = (parts.netloc or "").lower()
    if re.search(r"/search-jobs/[^/]*hyderabad|/job/hyderabad|/jobs/hyderabad", path, re.I):
        return url

    qs = parse_qs(parts.query, keep_blank_values=True)
    target_short = CAREERS_LOCATION
    target_full = CAREERS_LOCATION_FULL

    def _set(key: str, value: str) -> None:
        qs[key] = [value]

    if "amazon.jobs" in host:
        _set("loc_query", target_full)
    elif "blackbaud.com" in host:
        _set("locationsearch", target_short)
    elif "ibm.com" in host:
        _set("loc", target_short)
    elif "accenture.com" in host:
        _set("lc", target_short)
    elif "salesforce.com" in host:
        _set("city", target_short)
        _set("country", "India")
    elif "apple.com" in host:
        cur = (qs.get("location") or [""])[0]
        if not (re.search(r"hyderabad", cur, re.I) and "-" in cur and len(cur) > 12):
            _set("location", "hyderabad-HST430090")
    elif "icims.com" in host:
        _set("searchLocation", target_full)
        _set("location", target_short)
    elif "oraclecloud.com" in host or "careers.oracle.com" in host:
        _set("location", target_full)
    else:
        hit = False
        for key in _LOCATION_PARAM_KEYS:
            if key not in qs or qs[key] is None:
                continue
            cur = (qs[key][0] or "").strip()
            if re.search(r"hyderabad", cur, re.I) and "-" in cur and len(cur) > 12:
                hit = True
                continue
            if key in ("loc_query",) or "," in cur or re.search(r"telangana|india", cur, re.I):
                _set(key, target_full)
            else:
                _set(key, target_short)
            hit = True
        if not hit:
            _set("location", target_short)

    if "city" in qs and qs["city"]:
        if not re.search(r"hyderabad", qs["city"][0] or "", re.I):
            _set("city", target_short)
        if "country" in qs or "salesforce.com" in host:
            _set("country", "India")

    flat: list[tuple[str, str]] = []
    for k, vals in qs.items():
        for v in vals:
            flat.append((k, v))
    return urlunparse(parts._replace(query=urlencode(flat, doseq=True)))


def pin_portal_location_ui(page: Page) -> dict[str, Any]:
    """Best-effort: set Hyderabad in on-page location filters after navigation."""
    try:
        url = page.url or ""
    except Exception:
        url = ""
    if re.search(r"myworkdayjobs\.com", url, re.I):
        return workday_pin_hyderabad_location_ui(page)

    out: dict[str, Any] = {"pinned": False, "available": False, "note": "generic_ui"}
    selectors = [
        'input[placeholder*="Location" i]',
        'input[aria-label*="Location" i]',
        'input[name*="location" i]',
        'input[id*="location" i]',
        'input[data-automation-id*="location" i]',
        'input[placeholder*="City" i]',
        'input[aria-label*="City" i]',
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if not loc.count() or not loc.first.is_visible():
                continue
            loc.first.click(timeout=1500)
            loc.first.fill("")
            loc.first.fill(CAREERS_LOCATION, timeout=2000)
            time.sleep(0.8)
            opt = page.get_by_role("option", name=re.compile(r"Hyderabad", re.I))
            if opt.count():
                opt.first.click(timeout=2000)
                out.update(pinned=True, available=True, note=f"selected_option:{sel}")
                time.sleep(1.0)
                return out
            loc.first.press("Enter")
            out.update(pinned=True, available=True, note=f"typed_enter:{sel}")
            time.sleep(1.0)
            return out
        except Exception:
            continue
    try:
        btn = page.get_by_role("button", name=re.compile(r"^Location", re.I))
        if btn.count() and btn.first.is_visible():
            btn.first.click(timeout=2000)
            time.sleep(0.6)
            inp = page.locator(
                'input[type="text"], input[type="search"], input[placeholder*="Search" i]'
            )
            if inp.count():
                inp.first.fill(CAREERS_LOCATION, timeout=2000)
                time.sleep(0.8)
                hyd = page.get_by_text(re.compile(r"Hyderabad", re.I))
                if hyd.count():
                    hyd.first.click(timeout=2000)
                    out.update(pinned=True, available=True, note="button_menu_hyd")
                    time.sleep(1.0)
                    return out
                out.update(note="button_menu_no_hyd", available=False)
    except Exception as e:
        out["note"] = f"generic_failed:{e}"
    return out


def workday_pin_hyderabad_location_ui(page: Page) -> dict[str, Any]:
    """Open Workday Location filter and select Hyderabad when present.

    Returns {pinned: bool, available: bool, note: str}. When Hyderabad is not in
    the location list (e.g. Intel today), available=False — caller should skip
    non-Hyd roles rather than open Haifa/Bangalore/US cards.
    """
    out: dict[str, Any] = {"pinned": False, "available": False, "note": ""}
    try:
        url = page.url or ""
    except Exception:
        url = ""
    if not re.search(r"myworkdayjobs\.com", url, re.I):
        out["note"] = "not_workday"
        return out
    try:
        btn = page.locator('[data-automation-id="distanceLocation"]')
        if not btn.count() or not btn.first.is_visible():
            out["note"] = "no_location_button"
            return out
        btn.first.click(timeout=4000)
        time.sleep(1.0)
    except Exception as e:
        out["note"] = f"open_failed:{e}"
        return out
    try:
        menu = page.locator('[data-automation-id="filterMenu"]')
        menu.wait_for(state="visible", timeout=4000)
        menu_text = (menu.inner_text(timeout=2000) or "")
        if re.search(r"hyderabad|telangana|madhapur", menu_text, re.I):
            out["available"] = True
        inp = menu.locator(
            'input[type="text"], input[type="search"], '
            '[data-automation-id="searchBox"] input, '
            'input[placeholder*="Search" i]'
        )
        if inp.count():
            inp.first.fill(CAREERS_LOCATION, timeout=2500)
            time.sleep(1.2)
            menu_text = (menu.inner_text(timeout=2000) or "")
            if re.search(r"hyderabad|telangana|madhapur", menu_text, re.I):
                out["available"] = True
        if out["available"]:
            opt = menu.get_by_text(re.compile(r"Hyderabad", re.I)).first
            if opt.count():
                opt.click(timeout=3000)
                out["pinned"] = True
                out["note"] = "selected_hyderabad"
                time.sleep(1.5)
            else:
                out["note"] = "hyd_visible_not_clickable"
        else:
            out["note"] = "no_hyderabad_in_location_filter"
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
    except Exception as e:
        out["note"] = f"filter_failed:{e}"
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
    return out


def workday_card_location_blob(role: str, url: str) -> str:
    """Combine title + Workday path workplace (e.g. /job/Israel-Haifa/)."""
    return f"{role or ''} {url_loc_hint(url or '')}".strip()


def expand_careers_scan_urls(urls: list[str]) -> list[str]:
    """Emit role-diverse Hyd-scoped scan URLs (EM/Lead/Staff first) per careers link."""
    base = [u for u in (urls or []) if u]
    if not base:
        return []
    keywords = CAREERS_SEARCH_KEYWORDS[:MAX_CAREERS_KEYWORD_SEARCHES]
    out: list[str] = []
    seen: set[str] = set()
    for kw in keywords:
        for url in base:
            rewritten = pin_careers_hyderabad_location(rewrite_careers_search_keyword(url, kw))
            if rewritten in seen:
                continue
            seen.add(rewritten)
            out.append(rewritten)
    return out


def _company_ats_rank(company: dict[str, Any]) -> int:
    """Guest-completable ATS first; known SSO-only hosts last."""
    urls = " ".join(company.get("careersUrls") or [])
    if not urls:
        return 8
    if SSO_ONLY_CAREERS_RE.search(urls):
        return 9
    if HANG_SCAN_HOST_RE.search(urls):
        return 8
    if CAPTCHA_PRONE_HOST_RE.search(urls):
        return 4
    if GUEST_ATS_HOST_RE.search(urls):
        return 0
    return int(company.get("priority", 5) or 5)


def is_sso_only_careers_url(url: str) -> bool:
    return bool(url and SSO_ONLY_CAREERS_RE.search(url))


def is_hang_scan_url(url: str) -> bool:
    return bool(url and HANG_SCAN_HOST_RE.search(url))


def _env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).strip().lower() in ("1", "true", "yes")


def skip_company_name_set() -> set[str]:
    names = {
        n.strip().lower()
        for n in os.environ.get("HITECHCITY_SKIP_COMPANIES", "").split(",")
        if n.strip()
    }
    # Default on: owner asked to skip UHG/Optum Taleo until they unset this.
    if _env_flag("HITECHCITY_SKIP_UHG", "1"):
        names.update({"optum", "unitedhealth group", "uhg", "united health", "unitedhealth"})
    return names


def is_uhg_skip_url(url: str) -> bool:
    if not url or not _env_flag("HITECHCITY_SKIP_UHG", "1"):
        return False
    return bool(UHG_HOST_RE.search(url))


def company_skip_reason(company: dict[str, Any]) -> str | None:
    name = (company.get("name") or "").strip()
    lowered = name.lower()
    if lowered in skip_company_name_set():
        if _env_flag("HITECHCITY_SKIP_UHG", "1") and (
            UHG_NAME_RE.search(name) or lowered in {"optum", "unitedhealth group", "uhg", "united health", "unitedhealth"}
        ):
            return "skip_uhg"
        return "skip_company"
    urls = " ".join(company.get("careersUrls") or [])
    if is_uhg_skip_url(urls):
        return "skip_uhg"
    return None


def adopt_ats_tab(page: Page, before_pages: set) -> Page:
    """If Apply opened Workday/Greenhouse/iCIMS in a new tab, switch to it.

    SSO/OAuth popups are closed so we can still guest-apply on the JD tab.
    """
    try:
        for p2 in list(page.context.pages):
            u2 = p2.url or ""
            if classify_ats_host(u2) == "sso" or auth_wall_url(u2):
                if p2 is not page:
                    try:
                        p2.close()
                    except Exception:
                        pass
                continue
            if p2 in before_pages:
                continue
            if classify_ats_host(u2) in ("workday", "greenhouse") or GUEST_ATS_HOST_RE.search(u2):
                return p2
    except Exception:
        pass
    return page


def extract_job_links(page: Page, company: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    try:
        # Oracle Cloud HCM / JPMC / similar: job anchors often have empty innerText;
        # title + location live on the parent card (or aria-label / title attrs).
        raw = []
        frames = []
        try:
            frames = list(page.frames)
        except Exception:
            frames = []
        if not frames:
            frames = [page]
        def _frame_rank(fr) -> int:
            u = getattr(fr, "url", "") or ""
            if "in_iframe=1" in u:
                return 0
            if "about:blank" in u or not u:
                return 3
            return 1
        try:
            frames = sorted(frames, key=_frame_rank)
        except Exception:
            pass
        js = """() => {
              const out = [];
              const seen = new Set();
              const locRe = /([A-Z][A-Za-z .'-]+,\\s*(?:India|United States|USA|UK|United Kingdom|Malaysia|Brazil|Costa Rica|Romania|Poland|Germany|Netherlands|Ireland|Canada)(?:\\s*\\d+\\s*jobs?)?)/;
              const nearestLoc = (el) => {
                let n = el;
                for (let i = 0; i < 10 && n; i++, n = n.parentElement) {
                  const block = (n.innerText || '').split('\\n').map(s => s.trim()).filter(Boolean).slice(0, 8);
                  for (const line of block) {
                    if (line.length < 6 || line.length > 80) continue;
                    if (/hyderabad|madhapur|telangana|bengaluru|bangalore|remote|united states|malaysia|brazil|costa rica/i.test(line)) {
                      return line.replace(/\\s*\\d+\\s*jobs?$/i, '').trim();
                    }
                    const m = line.match(locRe);
                    if (m) return m[1].replace(/\\s*\\d+\\s*jobs?$/i, '').trim();
                  }
                }
                return '';
              };
              const wdTitles = [...document.querySelectorAll(
                'a[data-automation-id="jobTitle"], [data-automation-id="jobTitle"] a, [data-automation-id="jobTitle"]'
              )];
              for (const a of wdTitles) {
                const href = a.href || a.closest('a')?.href || '';
                let text = (a.innerText || a.textContent || a.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
                // Workday lists workplace under data-automation-id="locations" near the title.
                try {
                  const row = a.closest('li') || a.closest('[data-automation-id="jobTitle"]')?.parentElement || a.parentElement;
                  const locEl = row && row.querySelector('[data-automation-id="locations"]');
                  const loc = (locEl && (locEl.innerText || '').trim().replace(/^locations\\s*/i, '')) || '';
                  if (loc && loc.length >= 3 && loc.length < 80 && !text.toLowerCase().includes(loc.toLowerCase().split(',')[0])) {
                    text = (text + ' · ' + loc).replace(/\\s+/g, ' ').slice(0, 180);
                  }
                } catch (e) {}
                if (href && text && text.length >= 8 && !seen.has(href)) {
                  seen.add(href);
                  out.push({ href, text: text.slice(0, 180) });
                }
              }
              const anchors = [...document.querySelectorAll('a[href]')];
              for (const a of anchors) {
                const href = a.href || '';
                const h = href.toLowerCase();
                const looksJobId = /\\/jobs?\\/\\d+|\\/job\\/\\d+|gh_jid=|[?&](?:jobId|pid|reqId)=\\d+|smartrecruiters\\.com\\/[^/]+\\/\\d{6,}|myworkdayjobs\\.com\\/.+\\/job\\/|icims\\.com\\/jobs\\/\\d+|jobdetails\\?id=|\\/careers\\/jobdetails/i.test(h);
                // Path job slugs only — do NOT treat vendor hostnames (icims/career) as jobs.
                // Parent iCIMS chrome has 40+ marketing links on careers-*.icims.com and
                // used to fill the 40-cap before the in_iframe=1 listing was evaluated.
                const looksJobPath = /\\/(?:jobs|job)\\/(?!search|login|intro|home|cart)[^/?#]+/i.test(h);
                const looksJob = looksJobId || looksJobPath || /[?&](?:gh_jid|jobId|pid)=\\d/i.test(h);
                if (!looksJob) continue;
                // Skip bare search/list hubs (no job id) that only match because of "jobs" in path.
                if (/architecture-jobs\\/?$/i.test(h) || /\\/search-jobs\\/?(\\?|$)/i.test(h)) continue;
                if (!looksJobId && /\\/jobs\\/?(\\?|$|#)/i.test(h) && !/\\/jobs?\\/[^/?#]+/.test(h) && !/[?&](gh_jid|jobId|pid)=/i.test(h)) {
                  // allow SmartRecruiters / Experian style .../Company/744...-slug
                  if (!/smartrecruiters\\.com\\/[^/]+\\/\\d{6,}/i.test(h)) continue;
                }
                // Microsoft listing chrome sometimes becomes a fake "N jobs Sort..." card.
                const rawLabel = (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ');
                if (/^\\d+\\s+jobs?\\b/i.test(rawLabel) || /\\bturn on job alerts\\b/i.test(rawLabel)) continue;
                let text = (a.innerText || a.textContent || a.getAttribute('aria-label') || a.getAttribute('title') || '')
                  .trim().replace(/\\s+/g, ' ').replace(/^job title\\s+/i, '');
                if (!text || text.length < 8) {
                  // Accenture jobdetails anchors are often icon-only; title lives in ?title=.
                  try {
                    const u = new URL(href);
                    const qt = u.searchParams.get('title');
                    if (qt && qt.trim().length >= 8) text = qt.trim().replace(/\\+/g, ' ');
                  } catch (e) {}
                }
                if (!text || text.length < 8) {
                  // Oracle Cloud HCM / JPMC: <a class="job-grid-item__link"> has empty innerText.
                  // closest('[class*="job"]') matches the anchor itself — walk parents instead.
                  let n = a.parentElement;
                  let parentText = '';
                  for (let i = 0; i < 8 && n; i++, n = n.parentElement) {
                    const t = (n.innerText || '').trim().replace(/\\s+/g, ' ');
                    if (t && t.length >= 12 && t.length < 600) {
                      parentText = t;
                      break;
                    }
                  }
                  if (parentText) text = parentText.slice(0, 180);
                }
                if (/skip to (main )?content|go to home page|^sitemap$|^manage profile$|^sign in$/i.test(text)) continue;
                if (!text || text.length < 8 || text.length > 220) continue;
                // Prefer a short title + workplace when parent card dumped a long blurb.
                if (text.length > 120) {
                  const locM = text.match(/(.{8,100}?)\\s+((?:Hyderabad|Bengaluru|Bangalore|Remote|United States)[^,]{0,48})/i);
                  if (locM) {
                    text = (locM[1] + ' ' + locM[2]).replace(/\\s+/g, ' ').slice(0, 160);
                  } else {
                    const first = text.split(/\\s{2,}|\\n/).map(s => s.trim()).filter(Boolean)[0] || text;
                    text = first.slice(0, 160);
                  }
                }
                // iCIMS Job Locations header (titles omit city; /jobs/12345/job path is not a workplace).
                if (/icims\\.com/i.test(href) || /icims\\.com/i.test(location.hostname || '')) {
                  let loc = '';
                  const card = a.closest('li') || a.closest('.iCIMS_JobCardItem');
                  if (card) {
                    for (const tag of [...card.querySelectorAll('.iCIMS_JobHeaderTag')]) {
                      const field = (tag.querySelector('.iCIMS_JobHeaderField')?.innerText || '');
                      if (/location/i.test(field)) {
                        loc = (tag.querySelector('.iCIMS_JobHeaderData')?.innerText || '').trim();
                        if (loc) break;
                      }
                    }
                  }
                  if (!loc) loc = nearestLoc(a);
                  const locCity = (loc.split(',')[0] || loc.split('|')[0] || '').trim();
                  if (loc && locCity && !text.toLowerCase().includes(locCity.toLowerCase().slice(0, 18))) {
                    text = (text + ' · ' + loc).slice(0, 180);
                  }
                } else if (/smartrecruiters\\.com/i.test(href) || /smartrecruiters\\.com/i.test(location.hostname || '')) {
                  // SmartRecruiters location groups only — global pages can mention Hyd in chrome.
                  const loc = nearestLoc(a);
                  const locCity = (loc.split(',')[0] || '').trim().toLowerCase();
                  if (loc && locCity && !text.toLowerCase().includes(locCity)) {
                    text = (text + ' · ' + loc).slice(0, 180);
                  }
                }
                if (/^\\d+\\s+jobs?\\b/i.test(text) || /\\bturn on job alerts\\b/i.test(text)) continue;
                if (seen.has(href)) continue;
                seen.add(href);
                out.push({ href, text });
                if (out.length >= 40) break;
              }
              return out;
            }"""
        for fr in frames:
            try:
                # Frame.evaluate has no timeout kwarg (TypeError was emptying every scan).
                part = fr.evaluate(js)
            except Exception:
                continue
            raw.extend(part or [])
            # Keep scanning iframes even after chrome links; job-id rows win later.
    except Exception:
        raw = []
    for item in raw or []:
        text = re.sub(r"^job title\s+", "", item.get("text") or "", flags=re.I)
        href = item.get("href") or ""
        if re.search(r"^\d+\s+jobs?\b|turn on job alerts", text, re.I):
            continue
        if NAV_CHROME_RE.search(text.strip()):
            continue
        if not TITLE_HINT.search(text):
            continue
        reason = skip_reason(text, company)
        if reason:
            continue
        if CAREERS_TITLE_SKIP.search(text):
            continue
        if not title_matches_senior_stack(text) and not prefer_dotnet(text):
            continue
        # Card text + URL path — skip clear non-Hyd cities even when search URL said Hyderabad.
        # URL workplace tokens win over noisy card/chrome text (e.g. Boca-Raton-FL in Workday).
        hint = url_loc_hint(href)
        hydish = re.compile(
            r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg|"
            r"\bremote\b|\bwfh\b|work from home|india remote|fully remote",
            re.I,
        )
        if hint and BAD_LOC_HINT.search(hint) and not hydish.search(hint):
            continue
        if not card_location_ok(text, hint):
            continue
        jobs.append({"role": text, "url": href, "company": company})
    return jobs


def url_loc_hint(url: str) -> str:
    """Decode path workplace tokens (e.g. Boca-Raton-FL). Ignore listing query ?location=."""
    if not url:
        return ""
    try:
        parts = urlparse(url)
        # Path only: Oracle/JPMC job links inherit the search `?location=Hyderabad`
        # even when the card is Bengaluru. Workday/PAN encode city in the path.
        raw = parts.path.replace("-", " ").replace("_", " ").replace("%2C", " ")
        return re.sub(r"[+/]+", " ", raw)
    except Exception:
        return url


def _has_explicit_workplace(blob: str) -> bool:
    """True when card/title/URL names a city, country, or remote workplace."""
    if not (blob or "").strip():
        return False
    if BAD_LOC_HINT.search(blob):
        return True
    if re.search(
        r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg|"
        r"\bremote\b|\bwfh\b|work from home|\bindia\b",
        blob,
        re.I,
    ):
        return True
    # "City, Region" pills — not job-id paths like "jobs 13991 senior software architect job".
    if re.search(
        r"[A-Za-z][A-Za-z .'-]{2,},\s*(?:India|United States|USA|UK|United Kingdom|"
        r"Canada|Telangana|Karnataka|Maharashtra|Tamil Nadu|Texas|Florida|California|"
        r"Washington|Oregon|Ohio)",
        blob,
        re.I,
    ):
        return True
    return False


def card_location_ok(role_text: str, top_card: str = "") -> bool:
    """HARD: judge workplace from card/title/top pills/URL — never full page body/footer."""
    blob = f"{role_text or ''} {top_card or ''}".strip()
    if not blob:
        # Unknown location on card: allow open; apply_job re-checks top card.
        return True
    # Explicit non-Hyd city/country wins — including Remote Canada / Remote US / Remote UK.
    # Bare "Remote" / footer "India" must NOT rescue Bengaluru or foreign workplaces.
    # Multi-location cards that name Dubai/Bengaluru AND Hyderabad are still not Hyd-only.
    hyd_city = re.compile(
        r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg",
        re.I,
    )
    if BAD_LOC_HINT.search(blob):
        return False
    if hyd_city.search(blob) or location_or_campus_ok(blob, "", ""):
        return True
    # Vague India/Remote without a foreign city — allow; apply_job still re-checks.
    if re.search(r"\bremote\b|\bwfh\b|work from home|\bindia\b", blob, re.I):
        return True
    # iCIMS titles omit workplace and `/jobs/13991/job` paths are not cities.
    # Allow open; apply_job re-checks the JD top card (campus apply-bias).
    if not _has_explicit_workplace(blob):
        return True
    # Unknown city text (no Hyd, no known foreign) — do not assume Hyd.
    return False


def role_has_foreign_location(role: str) -> bool:
    """True when the job title/card itself names a non-Hyd city or country."""
    role = role or ""
    if re.search(
        r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg",
        role,
        re.I,
    ):
        return False
    return bool(BAD_LOC_HINT.search(role))


def dismiss_cookie_banners(page: Page) -> None:
    """Optum/Intel/Hyland cookie walls hide job cards until Accept."""
    for name in (
        "Accept All Cookies",
        "Accept Cookies",
        "Accept All",
        "Accept",
        "I Accept",
        "Agree",
    ):
        try:
            btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I))
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=1500)
                time.sleep(1.0)
                return
        except Exception:
            continue



def _browser_session_dead(err: BaseException | str) -> bool:
    s = str(err).lower()
    return any(
        x in s
        for x in (
            "has been closed",
            "target closed",
            "econnrefused",
            "browser has been closed",
            "connection refused",
        )
    )


def _close_uhg_tabs(context) -> None:
    """Drop leftover Optum/UHG Taleo tabs so they cannot become pages[0]."""
    if not _env_flag("HITECHCITY_SKIP_UHG", "1"):
        return
    try:
        for pg in list(context.pages):
            try:
                if is_uhg_skip_url(pg.url or ""):
                    pg.close()
            except Exception:
                continue
    except Exception:
        pass


def _connect_careers_cdp(p):
    """Connect (or reconnect) to Chrome CDP for careers scanning."""
    browser = p.chromium.connect_over_cdp(CDP, timeout=20_000)
    if not browser.contexts:
        raise RuntimeError("cdp_no_contexts")
    context = browser.contexts[0]
    _close_uhg_tabs(context)
    # Parallel workers always get a dedicated tab so 10 companies apply at once.
    if os.environ.get("HITECHCITY_PARALLEL_WORKER"):
        page = context.new_page()
    else:
        page = context.pages[0] if context.pages else context.new_page()
    if is_uhg_skip_url(getattr(page, "url", "") or ""):
        try:
            page = context.new_page()
        except Exception:
            pass
    page.set_default_timeout(45000)
    try:
        page.bring_to_front()
    except Exception:
        pass
    return browser, context, page


def _reset_page_nav(page: Page) -> None:
    """Stop in-flight navigations so the next company goto is not interrupted."""
    try:
        page.evaluate("window.stop()")
    except Exception:
        pass
    try:
        page.goto("about:blank", wait_until="domcontentloaded", timeout=15000)
    except Exception:
        pass


def scan_goto(page: Page, url: str, *, timeout: int = 75000, attempts: int = 3) -> None:
    """Listing-page navigate with recovery from chrome-error / interrupted redirects.

    Priority-2 boards (Accenture → Cognizant → Deloitte → Fiserv → Gartner) were
    cascading: one failed goto left a pending navigation that aborted every next
    company with 'interrupted by another navigation'.
    """
    last: Exception | None = None
    for i in range(attempts):
        try:
            if i > 0:
                _reset_page_nav(page)
                time.sleep(0.8 + i * 0.6)
            else:
                try:
                    page.evaluate("window.stop()")
                except Exception:
                    pass
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            u = (page.url or "").strip()
            if u.startswith("chrome-error://"):
                raise RuntimeError(f"chrome-error landing for {url}")
            return
        except Exception as e:
            last = e
            msg = str(e)
            retryable = any(
                x in msg
                for x in (
                    "interrupted by another navigation",
                    "net::ERR_",
                    "Timeout",
                    "chrome-error",
                    "Navigation to",
                )
            )
            if retryable and i + 1 < attempts:
                time.sleep(1.2 + i * 1.5)
                continue
            if retryable:
                break
            raise
    assert last is not None
    raise last


def apply_job(page: Page, job: dict[str, str], campus: str) -> dict[str, Any]:
    row = {
        "company": job["company"],
        "role": job["role"],
        "url": job["url"],
        "campus": campus,
        "path": "company-careers",
        "status": "blocked",
        "reason": "",
    }
    _safe_print(f"CAREERS OPEN {job['company']} | {job['role'][:80]}")
    if is_uhg_skip_url(job.get("url") or ""):
        row["status"] = "skipped"
        row["reason"] = "skip_uhg"
        return row
    # Role/title + URL path location first (before navigation wastes ATS time on US cards).
    if not card_location_ok(job.get("role") or "", url_loc_hint(job.get("url") or "")):
        row["status"] = "skipped"
        row["reason"] = "location_non_hyd_city"
        return row
    # Title itself names Dubai/Bengaluru/etc. — never open, even if search URL said Hyd.
    if role_has_foreign_location(job.get("role") or ""):
        row["status"] = "skipped"
        row["reason"] = "location_foreign_in_title"
        return row
    try:
        page.goto(job["url"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        row["reason"] = f"nav_error:{e}"
        return row
    time.sleep(2.0)
    if auth_wall_url(page.url or "") or AUTH_HOST.search(page.url or ""):
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        return row
    # JD chrome ("Sign in" / "Create an account") is not a wall. Only CAPTCHA /
    # closed reqs fail here — Workday Create Account must reach complete_ats.
    wall = blocked_wall(page)
    if wall in ("CAPTCHA/bot wall", "job_closed") and not looks_workday_page(page):
        row["reason"] = wall
        row["status"] = "skipped" if wall == "job_closed" else "blocked"
        row["finalUrl"] = page.url
        return row

    # Location from TOP CARD / workplace pills only — not full page body (footers say India).
    try:
        top = page.evaluate(
            """() => {
              const pick = (sel) => {
                const el = document.querySelector(sel);
                return el ? (el.innerText || '').trim() : '';
              };
              const chunks = [
                pick('[data-automation-id="locations"]'),
                pick('[class*="location"]'),
                pick('[class*="Location"]'),
                pick('h1'),
                pick('[data-testid="job-location"]'),
                pick('.job-location'),
              ];
              const body = (document.body && document.body.innerText) || '';
              const lines = body.split('\\n').map(s => s.trim()).filter(Boolean).slice(0, 12);
              return (chunks.filter(Boolean).join(' ') + ' ' + lines.join(' ')).slice(0, 700);
            }"""
        )
    except Exception:
        top = ""
    role = job.get("role") or ""
    try:
        page_title = page.title() or ""
    except Exception:
        page_title = ""
    if not card_location_ok(role, f"{top or ''} {page_title}"):
        row["status"] = "skipped"
        row["reason"] = "location_non_hyd_city"
        row["finalUrl"] = page.url
        return row
    # Require Hyd/campus/remote/India — never apply-bias past Dubai/UAE/Bengaluru/etc.
    # (search listings are often Hyd-scoped but Oracle multi-loc cards still name foreign cities).
    loc_blob = f"{role} {top or ''} {page_title}"
    if BAD_LOC_HINT.search(loc_blob) or role_has_foreign_location(role):
        row["status"] = "skipped"
        row["reason"] = "location_not_hyd_or_campus"
        row["finalUrl"] = page.url
        return row
    has_hyd = bool(
        re.search(
            r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg",
            loc_blob,
            re.I,
        )
        or location_or_campus_ok(loc_blob, "", "")
    )
    # Bare "India" / Remote alone is OK only when no foreign city (already checked).
    if not has_hyd and re.search(r"\bremote\b|\bwfh\b|work from home|\bindia\b", loc_blob, re.I):
        has_hyd = True
    if not has_hyd:
        # Uncertain (no Hyd pill, no foreign city) → APPLY bias per campus prompt.
        print(
            f"CAREERS LOC apply_bias_no_city_pill | {job['company']} | {role[:60]}",
            flush=True,
        )

    # Title-generic Architect roles that are clearly Salesforce/wrong-stack in the JD.
    try:
        jd_snip = (page.locator("body").inner_text(timeout=2500) or "")[:2500]
    except Exception:
        jd_snip = top or ""
    if JD_WRONG_STACK.search(jd_snip) and not prefer_dotnet(role, jd_snip):
        row["status"] = "skipped"
        row["reason"] = "jd_wrong_stack"
        row["finalUrl"] = page.url
        return row

    # Click apply if listing page (iCIMS Apply lives in #icims_content_iframe).
    try:
        from tools.ats.complete import prefer_icims_apply
        prefer_icims_apply(page)
    except Exception:
        pass
    before_pages = set(page.context.pages)
    try_click_named(
        page,
        (
            "Apply manually",
            "Apply without Indeed",
            "Apply now",
            "Apply Now",
            "Start application",
            "I'm interested",
            "Apply",
        ),
    )
    # Adopt guest ATS tabs; close SSO popups instead of bailing on the JD.
    try:
        deadline = time.time() + 6
        while time.time() < deadline:
            page = adopt_ats_tab(page, before_pages)
            u2 = page.url or ""
            if classify_ats_host(u2) == "unavailable":
                row["status"] = "skipped"
                row["reason"] = "job_unavailable"
                row["finalUrl"] = u2
                _close_auth_popups(page)
                return row
            if looks_workday_page(page) or classify_ats_host(u2) in ("workday", "greenhouse"):
                break
            time.sleep(0.45)
    except Exception:
        pass
    if auth_wall_url(page.url or "") or AUTH_HOST.search(page.url or ""):
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        _close_auth_popups(page)
        return row
    wall = blocked_wall(page)
    icims_job = bool(re.search(r"icims\.com/jobs/\d+", page.url or "", re.I))
    # iCIMS hCaptcha is solved inside complete_ats — do not abort before the solver runs.
    if wall == "job_closed" and not looks_workday_page(page):
        row["reason"] = wall
        row["status"] = "skipped"
        row["finalUrl"] = page.url
        _close_auth_popups(page)
        return row
    if (
        wall == "CAPTCHA/bot wall"
        and not looks_workday_page(page)
        and not icims_job
    ):
        row["reason"] = wall
        row["status"] = "blocked"
        row["finalUrl"] = page.url
        _close_auth_popups(page)
        return row
    status, reason = attempt_ats_apply(page, time_cap_s=TIME_CAP_S)
    if auth_wall_url(page.url or "") or "passport.amazon.jobs" in (page.url or ""):
        row["status"] = "blocked"
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        _close_auth_popups(page)
        return row
    row["status"] = status
    row["reason"] = reason
    row["finalUrl"] = page.url
    _close_auth_popups(page)
    return row


def run(companies: list[dict[str, Any]] | None = None) -> CareersReport:
    companies = companies or load_companies()
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    kept: list[dict[str, Any]] = []
    for company in companies:
        reason = company_skip_reason(company)
        if reason:
            report.skipped.append(
                {
                    "company": company.get("name"),
                    "status": "skipped",
                    "reason": reason,
                }
            )
            _safe_print(f"CAREERS SKIP {company.get('name')} | {reason}")
            continue
        kept.append(company)
    companies = kept[:MAX_COMPANIES]
    # Multi-tab fan-out (default 10) unless this process is already a worker.
    parallel_tabs = int(os.environ.get("HITECHCITY_PARALLEL_TABS", "10"))
    if (
        parallel_tabs > 1
        and len(companies) > 1
        and not os.environ.get("HITECHCITY_PARALLEL_WORKER")
    ):
        from tools.hitechcity.careers_parallel import run_parallel

        return run_parallel(companies)
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser, context, page = _connect_careers_cdp(p)
        reconnects = 0
        max_reconnects = int(os.environ.get("HITECHCITY_CAREERS_CDP_RECONNECTS", "3"))
        cdp_fatal = False

        for company in companies:
            if cdp_fatal:
                break
            name = company["name"]
            campuses = ",".join(company.get("campuses") or [])
            urls = expand_careers_scan_urls(company.get("careersUrls") or [])
            _safe_print(f"CAREERS SCAN {name} | urls={len(urls)} roles={MAX_CAREERS_KEYWORD_SEARCHES}")
            company_applied = 0
            company_walls = 0
            company_attempts = 0
            workday_no_hyd = False
            loc_ui_done = False
            for url in urls:
                if workday_no_hyd and re.search(r"myworkdayjobs\.com", url, re.I):
                    # One confirmed "no Hyderabad facet" is enough — don't burn 6–12 keyword URLs.
                    continue
                if is_sso_only_careers_url(url):
                    report.skipped.append(
                        {
                            "company": name,
                            "url": url,
                            "status": "skipped",
                            "reason": "sso_only_careers_host",
                        }
                    )
                    _safe_print(f"CAREERS SKIP {name} | sso_only_careers_host")
                    continue
                if is_hang_scan_url(url):
                    report.skipped.append(
                        {
                            "company": name,
                            "url": url,
                            "status": "skipped",
                            "reason": "hang_scan_host",
                        }
                    )
                    _safe_print(f"CAREERS SKIP {name} | hang_scan_host")
                    continue
                if is_uhg_skip_url(url):
                    report.skipped.append(
                        {
                            "company": name,
                            "url": url,
                            "status": "skipped",
                            "reason": "skip_uhg",
                        }
                    )
                    _safe_print(f"CAREERS SKIP {name} | skip_uhg")
                    continue
                try:
                    scan_goto(page, url, timeout=75000)
                except Exception as e:
                    report.blocked.append({"company": name, "url": url, "reason": f"scan_nav:{e}"})
                    if _browser_session_dead(e):
                        if reconnects >= max_reconnects:
                            _safe_print(f"CAREERS CDP dead — stop after {reconnects} reconnects")
                            cdp_fatal = True
                            break
                        reconnects += 1
                        try:
                            browser, context, page = _connect_careers_cdp(p)
                            _safe_print(f"CAREERS CDP reconnect #{reconnects} ok")
                        except Exception as re_err:
                            _safe_print(f"CAREERS CDP reconnect failed: {re_err}")
                            report.blocked.append(
                                {
                                    "company": name,
                                    "url": url,
                                    "reason": f"cdp_reconnect_failed:{re_err}",
                                }
                            )
                            cdp_fatal = True
                            break
                        continue
                    # Clear poisoned/in-flight navigations before the next company.
                    _reset_page_nav(page)
                    try:
                        page = context.new_page()
                        page.set_default_timeout(45000)
                    except Exception:
                        pass
                    continue
                time.sleep(1.0)
                dismiss_cookie_banners(page)
                # HARD: set Hyderabad in URL already; also pin on-page Location UI (once/company for speed).
                workday_loc: dict[str, Any] = {"pinned": False, "available": False, "note": "skipped_repeat"}
                try:
                    if not loc_ui_done:
                        workday_loc = pin_portal_location_ui(page)
                        loc_ui_done = True
                        _safe_print(
                            f"CAREERS LOC_UI {name} | pinned={workday_loc.get('pinned')} "
                            f"available={workday_loc.get('available')} | {workday_loc.get('note')}"
                        )
                        if (
                            re.search(r"myworkdayjobs\.com", url, re.I)
                            and not workday_loc.get("available")
                            and not workday_loc.get("pinned")
                            and workday_loc.get("note") == "no_hyderabad_in_location_filter"
                        ):
                            workday_no_hyd = True
                            _safe_print(
                                f"CAREERS SKIP {name} | workday_no_hyderabad_facet — advance to next company"
                            )
                            report.skipped.append(
                                {
                                    "company": name,
                                    "url": url,
                                    "status": "skipped",
                                    "reason": "workday_no_hyderabad_facet",
                                }
                            )
                            break
                except Exception as e:
                    workday_loc = {"pinned": False, "available": False, "note": str(e)[:120]}
                    loc_ui_done = True
                # Oracle Cloud HCM / Workday-style boards lazy-render cards; nudge into view.
                try:
                    for _ in range(3):
                        page.mouse.wheel(0, 1400)
                        time.sleep(0.7)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.4)
                except Exception:
                    pass
                # Wait for guest ATS cards (Workday / iCIMS / Oracle HCM) before extract.
                # Do not treat iCIMS skip-to-iframe chrome (`#icims_content_iframe`) as a card.
                try:
                    page.wait_for_selector(
                        'iframe[src*="in_iframe=1"], iframe#icims_content_iframe',
                        timeout=6000,
                    )
                except Exception:
                    pass
                try:
                    page.wait_for_selector(
                        '[data-automation-id="jobTitle"], a[data-automation-id="jobTitle"], '
                        'a[href*="icims.com/jobs/"][href*="/job"], '
                        'a[href*="jobdetails?id="], a[href*="/jobs/job/"], '
                        "a.job-grid-item__link, [data-qa='jobRequisitionTitle']",
                        timeout=10000,
                    )
                except Exception:
                    pass
                try:
                    for fr in page.frames:
                        if "in_iframe=1" in (getattr(fr, "url", "") or ""):
                            fr.wait_for_selector(
                                'a[href*="icims.com/jobs/"][href*="/job"]',
                                timeout=8000,
                            )
                            break
                except Exception:
                    pass
                # Experian SmartRecruiters location groups collapse job links until expanded.
                try:
                    hyd = page.get_by_text(re.compile(r"Hyderabad,\s*India", re.I))
                    if hyd.count():
                        hyd.first.click(timeout=2500)
                        time.sleep(1.2)
                except Exception:
                    pass
                jobs = extract_job_links(page, name)
                # Workday with no Hyderabad in the location filter → drop foreign cards.
                if (
                    re.search(r"myworkdayjobs\.com", url, re.I)
                    and workday_loc
                    and not workday_loc.get("available")
                    and not workday_loc.get("pinned")
                ):
                    before = len(jobs)
                    jobs = [
                        j
                        for j in jobs
                        if card_location_ok(
                            j.get("role") or "",
                            url_loc_hint(j.get("url") or ""),
                        )
                        and not role_has_foreign_location(j.get("role") or "")
                        and re.search(
                            r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|"
                            r"gachibowli|raidurg|\bremote\b",
                            f"{j.get('role') or ''} {url_loc_hint(j.get('url') or '')}",
                            re.I,
                        )
                    ]
                    _safe_print(
                        f"CAREERS WORKDAY SKIP_NON_HYD {name} | kept={len(jobs)} dropped={before - len(jobs)} "
                        f"| no Hyderabad in location filter"
                    )
                report.scanned.append({"company": name, "url": url, "jobCount": len(jobs)})
                for job in jobs:
                    if job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    if company_applied >= MAX_PER_COMPANY:
                        break
                    if company_walls >= MAX_WALLS_PER_COMPANY:
                        report.skipped.append(
                            {
                                "company": name,
                                "role": job.get("role"),
                                "url": job.get("url"),
                                "status": "skipped",
                                "reason": f"company_wall_cap_{company_walls}",
                            }
                        )
                        break
                    # Never burn matching inventory on soft incompletes — only hard walls cap.
                    result = apply_job(page, job, campuses)
                    _safe_print(
                        f"CAREERS {result.get('status', '?').upper()} {name} | "
                        f"{(result.get('reason') or '')[:60]}"
                    )
                    notify_application_result(
                        status=str(result.get("status") or ""),
                        company=str(result.get("company") or name),
                        role=str(result.get("role") or job.get("role") or ""),
                        reason=str(result.get("reason") or ""),
                        path=str(result.get("path") or "company-careers"),
                        url=str(result.get("url") or job.get("url") or ""),
                    )
                    if result["status"] == "applied":
                        report.applied.append(result)
                        company_applied += 1
                        company_attempts += 1
                    elif result["status"] == "skipped":
                        report.skipped.append(result)
                    else:
                        report.blocked.append(result)
                        why = result.get("reason") or ""
                        try:
                            from tools.ats.complete import is_hard_ats_wall
                        except Exception:
                            from ats.complete import is_hard_ats_wall  # type: ignore
                        if is_hard_ats_wall(why):
                            company_walls += 1
                            company_attempts += 1
                        elif "incomplete" not in (why or "").lower():
                            company_attempts += 1
                    if company_applied >= MAX_PER_COMPANY:
                        break
                    if company_walls >= MAX_WALLS_PER_COMPANY:
                        break
                    if company_attempts >= MAX_ATTEMPTS_PER_COMPANY:
                        break
                else:
                    continue
                break

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    out_path = REPORT
    worker = os.environ.get("HITECHCITY_PARALLEL_WORKER")
    if worker:
        out_path = REPORT.with_name(f"hitechcity-careers-w{worker}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(report), indent=2))
    print(json.dumps({"applied": len(report.applied), "blocked": len(report.blocked), "skipped": len(report.skipped), "worker": worker or ""}))
    return report


if __name__ == "__main__":
    run()
