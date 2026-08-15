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
from urllib.parse import urlparse

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


def _safe_print(msg: str) -> None:
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(msg.encode(enc, errors="replace").decode(enc, errors="replace"), flush=True)

CDP = os.environ.get("HITECHCITY_CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))
MAX_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_PER_COMPANY", "4"))
# Raised for discovery-expanded campus tenant list (still priority-sorted).
MAX_COMPANIES = int(os.environ.get("HITECHCITY_MAX_COMPANIES", "40"))
# Tight default: SSO walls must fail fast; guest ATS rarely needs 3+ minutes.
TIME_CAP_S = int(os.environ.get("HITECHCITY_ATS_TIME_CAP_S", "390"))
MAX_WALLS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_WALLS", "4"))
MAX_ATTEMPTS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_ATTEMPTS", "10"))

TITLE_HINT = re.compile(
    r"architect|technical lead|tech lead|engineering manager|principal|staff|"
    r"\.net|dotnet|azure|cloud architect|solution",
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
    r"bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|gurugram|"
    r"brazil|s[aã]o\s*carlos|malaysia|cyberjaya|costa\s*rica|heredia|nottingham|"
    r"kuala\s*lumpur|mexico|colombia|chile|argentina|"
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
    r"machine\s*learning\s*hardware|gpu\s*software|embedded\s*software|"
    r"field\s*robotics|platform\s*power|network\s*hardware|"
    r"product\s*manager|network\s*architect|"
    r"chemical\s*mechanical|planarization|\bcmp\b|soc\s*compute|"
    r"memory\s*subsystem|foundry\s*solutions|"
    # Silicon / chip design (Principal Physical Design matched TITLE_HINT via Principal).
    r"physical\s*design|silicon\s*design|silicon\s*engineer|product\s*design\s*manager|"
    r"chiplet|\basic\b|\bvlsi\b|rtl\s*design|dft\s*engineer|"
    r"analog\s*design|digital\s*design\s*engineer|verification\s*engineer|"
    r"sales\s*specialist|especialista|"
    r"\bai\s*native\b|\bdata\s*&\s*ai\b|staff\s*engineer\s*\(\s*ai|"
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
AUTH_HOST = re.compile(
    r"passport\.amazon\.jobs|login\.microsoftonline|accounts\.google|"
    r"secure\.indeed\.com|indeed\.com/auth|okta\.com|login\.microsoft|"
    r"auth\.|signin\.|sso\.|login\.cognizant|cognizant\.okta|"
    r"talent\.cognizant\.com/[^?\s]*(?:login|login2)|"
    r"eightfold\.ai/(?:login|signin|auth)",
    re.I,
)


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
    r"icims\.com/jobs/\d+",
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


def _company_ats_rank(company: dict[str, Any]) -> int:
    """Guest-completable ATS first; known SSO-only hosts last."""
    urls = " ".join(company.get("careersUrls") or [])
    if not urls:
        return 8
    if SSO_ONLY_CAREERS_RE.search(urls):
        return 9
    if HANG_SCAN_HOST_RE.search(urls):
        return 8
    if GUEST_ATS_HOST_RE.search(urls):
        return 0
    return int(company.get("priority", 5) or 5)


def is_sso_only_careers_url(url: str) -> bool:
    return bool(url and SSO_ONLY_CAREERS_RE.search(url))


def is_hang_scan_url(url: str) -> bool:
    return bool(url and HANG_SCAN_HOST_RE.search(url))


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
                const text = (a.innerText || a.textContent || a.getAttribute('aria-label') || '').trim().replace(/\\s+/g, ' ');
                if (href && text && text.length >= 8 && !seen.has(href)) {
                  seen.add(href);
                  out.push({ href, text: text.slice(0, 180) });
                }
              }
              const anchors = [...document.querySelectorAll('a[href]')];
              for (const a of anchors) {
                const href = a.href || '';
                const h = href.toLowerCase();
                const looksJobId = /\\/jobs?\\/\\d+|\\/job\\/\\d+|gh_jid=|[?&](?:jobId|pid|reqId)=\\d+|smartrecruiters\\.com\\/[^/]+\\/\\d{6,}|myworkdayjobs\\.com\\/.+\\/job\\/|icims\\.com\\/jobs\\/\\d+/i.test(h);
                const looksJob = looksJobId
                  || /job|career|requisition|opening|position|gh_jid|lever|workday|smartrecruiters|icims|taleo|greenhouse/.test(h)
                  || /\\/jobs?\\//.test(h);
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
                  .trim().replace(/\\s+/g, ' ');
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
                // Only SmartRecruiters location groups are reliable for nearestLoc
                // (ModMed/global pages can mention Hyderabad in chrome and poison titles).
                if (/smartrecruiters\\.com/i.test(href) || /smartrecruiters\\.com/i.test(location.hostname || '')) {
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
            if len(raw) >= 40:
                break
    except Exception:
        raw = []
    for item in raw or []:
        text = item.get("text") or ""
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


def card_location_ok(role_text: str, top_card: str = "") -> bool:
    """HARD: judge workplace from card/title/top pills/URL — never full page body/footer."""
    blob = f"{role_text or ''} {top_card or ''}".strip()
    if not blob:
        # Unknown location on card: allow open; apply_job re-checks top card.
        return True
    # Explicit non-Hyd city on the card/title wins over bare "India" / footer noise.
    # (Oracle HCM: "System Architect BENGALURU, KARNATAKA, India and 2 more")
    if BAD_LOC_HINT.search(blob):
        hydish = re.compile(
            r"hyderabad|telangana|madhapur|hitec\s*city|hitech\s*city|gachibowli|raidurg|"
            r"\bremote\b|\bwfh\b|work from home|india remote|fully remote",
            re.I,
        )
        if not hydish.search(blob):
            return False
    if LOC_HINT.search(blob) or location_or_campus_ok(blob, "", ""):
        return True
    return True


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
    # Role/title + URL path location first (before navigation wastes ATS time on US cards).
    if not card_location_ok(job.get("role") or "", url_loc_hint(job.get("url") or "")):
        row["status"] = "skipped"
        row["reason"] = "location_non_hyd_city"
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
    # Require an explicit Hyd/campus/remote/India signal on role, top card, or title.
    loc_blob = f"{role} {top or ''} {page_title}"
    if not LOC_HINT.search(loc_blob) and not location_or_campus_ok(loc_blob, "", ""):
        row["status"] = "skipped"
        row["reason"] = "location_not_hyd_or_campus"
        row["finalUrl"] = page.url
        return row

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

    # Click apply if listing page
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
    if wall in ("CAPTCHA/bot wall", "job_closed") and not looks_workday_page(page):
        row["reason"] = wall
        row["status"] = "skipped" if wall == "job_closed" else "blocked"
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
    companies = companies[:MAX_COMPANIES]
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45000)

        for company in companies:
            name = company["name"]
            campuses = ",".join(company.get("campuses") or [])
            urls = company.get("careersUrls") or []
            _safe_print(f"CAREERS SCAN {name}")
            company_applied = 0
            company_walls = 0
            company_attempts = 0
            for url in urls:
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
                try:
                    scan_goto(page, url, timeout=75000)
                except Exception as e:
                    report.blocked.append({"company": name, "url": url, "reason": f"scan_nav:{e}"})
                    # Clear poisoned/in-flight navigations before the next company.
                    _reset_page_nav(page)
                    try:
                        page = context.new_page()
                        page.set_default_timeout(45000)
                    except Exception:
                        pass
                    continue
                time.sleep(2.2)
                dismiss_cookie_banners(page)
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
                try:
                    page.wait_for_selector(
                        '[data-automation-id="jobTitle"], a[data-automation-id="jobTitle"], '
                        'a[href*="/job/"], a[href*="icims.com/jobs/"], '
                        "a.job-grid-item__link, [data-qa='jobRequisitionTitle']",
                        timeout=10000,
                    )
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
                report.scanned.append({"company": name, "url": url, "jobCount": len(jobs)})
                for job in jobs:
                    if job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    if company_applied >= MAX_PER_COMPANY:
                        break
                    if company_walls >= MAX_WALLS_PER_COMPANY or company_attempts >= MAX_ATTEMPTS_PER_COMPANY:
                        report.skipped.append(
                            {
                                "company": name,
                                "role": job.get("role"),
                                "url": job.get("url"),
                                "status": "skipped",
                                "reason": (
                                    f"company_wall_cap_{company_walls}"
                                    if company_walls >= MAX_WALLS_PER_COMPANY
                                    else f"company_attempt_cap_{company_attempts}"
                                ),
                            }
                        )
                        break
                    company_attempts += 1
                    result = apply_job(page, job, campuses)
                    _safe_print(
                        f"CAREERS {result.get('status', '?').upper()} {name} | "
                        f"{(result.get('reason') or '')[:60]}"
                    )
                    if result["status"] == "applied":
                        report.applied.append(result)
                        company_applied += 1
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
                if company_applied >= MAX_PER_COMPANY:
                    break
                if company_walls >= MAX_WALLS_PER_COMPANY or company_attempts >= MAX_ATTEMPTS_PER_COMPANY:
                    break

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(asdict(report), indent=2))
    print(json.dumps({"applied": len(report.applied), "blocked": len(report.blocked), "skipped": len(report.skipped)}))
    return report


if __name__ == "__main__":
    run()
