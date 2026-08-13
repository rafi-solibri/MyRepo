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
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from tools.hitechcity.ats_fill import attempt_ats_apply, blocked_wall, try_click_named
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
MAX_COMPANIES = int(os.environ.get("HITECHCITY_MAX_COMPANIES", "18"))
TIME_CAP_S = int(os.environ.get("HITECHCITY_ATS_TIME_CAP_S", "180"))

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
    r"tx|wa|ca|fl|ny|il|ga|nc|ma)\b",
    re.I,
)
# Titles that match broad TITLE_OK (staff/principal/architect) but are wrong for this run.
CAREERS_TITLE_SKIP = re.compile(
    r"system\s*test|quality\s*(platform|assurance|engineering)|threat\s*detection|"
    r"project\s*analyst|industrial\s*design|hardware\s*architect|"
    r"machine\s*learning\s*hardware|gpu\s*software|embedded\s*software|"
    r"field\s*robotics|platform\s*power|network\s*hardware|"
    r"product\s*manager|network\s*architect|"
    r"chemical\s*mechanical|planarization|\bcmp\b|soc\s*compute|"
    r"memory\s*subsystem|foundry\s*solutions|"
    r"sales\s*specialist|especialista|"
    r"\bai\s*native\b|\bdata\s*&\s*ai\b|staff\s*engineer\s*\(\s*ai",
    re.I,
)
AUTH_HOST = re.compile(
    r"passport\.amazon\.jobs|login\.microsoftonline|accounts\.google|"
    r"auth\.|signin\.|sso\.|okta\.com|login\.microsoft",
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
    companies = sorted(data.get("companies", []), key=lambda c: (c.get("priority", 9), c.get("name", "")))
    return companies


def extract_job_links(page: Page, company: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    try:
        # Oracle Cloud HCM / JPMC / similar: job anchors often have empty innerText;
        # title + location live on the parent card (or aria-label / title attrs).
        raw = page.evaluate(
            """() => {
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
              const anchors = [...document.querySelectorAll('a[href]')];
              for (const a of anchors) {
                const href = a.href || '';
                const h = href.toLowerCase();
                const looksJob = /job|career|requisition|opening|position|gh_jid|lever|workday|smartrecruiters|icims|taleo|greenhouse/.test(h)
                  || /\\/jobs?\\//.test(h);
                if (!looksJob) continue;
                // Skip bare search/list hubs (no job id) that only match because of "jobs" in path.
                if (/architecture-jobs\\/?$/i.test(h) || /\\/search-jobs\\/?(\\?|$)/i.test(h)) continue;
                if (/\\/jobs\\/?(\\?|$|#)/i.test(h) && !/\\/jobs?\\/[^/?#]+/.test(h) && !/[?&](gh_jid|jobId|pid)=/i.test(h)) {
                  // allow SmartRecruiters / Experian style .../Company/744...-slug
                  if (!/smartrecruiters\\.com\\/[^/]+\\/\\d{6,}/i.test(h)) continue;
                }
                // Microsoft listing chrome sometimes becomes a fake "N jobs Sort..." card.
                const rawLabel = (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ');
                if (/^\\d+\\s+jobs?\\b/i.test(rawLabel) || /\\bturn on job alerts\\b/i.test(rawLabel)) continue;
                let text = (a.innerText || a.textContent || a.getAttribute('aria-label') || a.getAttribute('title') || '')
                  .trim().replace(/\\s+/g, ' ');
                if (!text || text.length < 8) {
                  const parent = a.closest('li, article, tr, [class*="job"], [data-qa], [data-automation-id]');
                  const parentText = parent ? (parent.innerText || '').trim().replace(/\\s+/g, ' ') : '';
                  if (parentText && parentText.length >= 8) text = parentText.slice(0, 160);
                }
                if (!text || text.length < 8 || text.length > 180) continue;
                // Prefer a short title line when parent card dumped a long blurb.
                if (text.length > 120) {
                  const first = text.split(/\\s{2,}|\\n/).map(s => s.trim()).filter(Boolean)[0] || text;
                  text = first.slice(0, 160);
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
        )
    except Exception:
        raw = []
    for item in raw or []:
        text = item.get("text") or ""
        href = item.get("href") or ""
        if re.search(r"^\d+\s+jobs?\b|turn on job alerts", text, re.I):
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
    """Decode path/query workplace tokens (e.g. Boca-Raton-FL) into readable location text."""
    if not url:
        return ""
    try:
        parts = urlparse(url)
        raw = f"{parts.path} {parts.query}".replace("-", " ").replace("_", " ").replace("%2C", " ")
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
    if AUTH_HOST.search(page.url or ""):
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        return row
    wall = blocked_wall(page)
    if wall:
        row["reason"] = wall
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
    if not card_location_ok(role, top or ""):
        row["status"] = "skipped"
        row["reason"] = "location_non_hyd_city"
        row["finalUrl"] = page.url
        return row
    # Require an explicit Hyd/campus/remote/India signal on role or top card.
    loc_blob = f"{role} {top or ''}"
    if not LOC_HINT.search(loc_blob) and not location_or_campus_ok(loc_blob, "", ""):
        row["status"] = "skipped"
        row["reason"] = "location_not_hyd_or_campus"
        row["finalUrl"] = page.url
        return row

    # Click apply if listing page
    try_click_named(page, ("Apply now", "Apply Now", "Apply", "Start application", "I'm interested"))
    time.sleep(1.5)
    if AUTH_HOST.search(page.url or ""):
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        return row
    status, reason = attempt_ats_apply(page, time_cap_s=TIME_CAP_S)
    if AUTH_HOST.search(page.url or "") or "passport.amazon.jobs" in (page.url or ""):
        row["status"] = "blocked"
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        return row
    row["status"] = status
    row["reason"] = reason
    row["finalUrl"] = page.url
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
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=75000)
                except Exception as e:
                    report.blocked.append({"company": name, "url": url, "reason": f"scan_nav:{e}"})
                    continue
                time.sleep(2.2)
                # Oracle Cloud HCM / Workday-style boards lazy-render cards; nudge into view.
                try:
                    for _ in range(3):
                        page.mouse.wheel(0, 1400)
                        time.sleep(0.7)
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(0.4)
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
                    result = apply_job(page, job, campuses)
                    if result["status"] == "applied":
                        report.applied.append(result)
                        company_applied += 1
                    elif result["status"] == "skipped":
                        report.skipped.append(result)
                    else:
                        report.blocked.append(result)
                if company_applied >= MAX_PER_COMPANY:
                    break

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(asdict(report), indent=2))
    print(json.dumps({"applied": len(report.applied), "blocked": len(report.blocked), "skipped": len(report.skipped)}))
    return report


if __name__ == "__main__":
    run()
