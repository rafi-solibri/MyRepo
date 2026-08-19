#!/usr/bin/env python3
"""LinkedIn apply + referral outreach for premium Madhapur / Knowledge City companies."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from playwright.sync_api import Page, sync_playwright

from tools.hitechcity.ats_fill import attempt_ats_apply, resume_path
from tools.hitechcity.filters import (
    company_name_match,
    location_or_campus_ok,
    skip_reason,
    title_matches_senior_stack,
)
from tools.hitechcity.apply_notify import notify_application_result

try:
    from tools.linkedin.filters import location_allowed
except Exception:
    from linkedin.filters import location_allowed  # type: ignore

CDP = os.environ.get("HITECHCITY_CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(
    os.environ.get("HITECHCITY_LINKEDIN_REPORT", "/opt/cursor/artifacts/hitechcity-linkedin.json")
)
MAX_APPLY = int(os.environ.get("HITECHCITY_MAX_APPLY", "35"))
MAX_REFERRALS = int(os.environ.get("HITECHCITY_MAX_REFERRALS", "12"))
MAX_SCAN = int(os.environ.get("HITECHCITY_MAX_SCAN", "40"))
TPR = os.environ.get("HITECHCITY_TPR", "r1209600")  # 14 days

# LinkedIn location filter — text alone is unreliable; geoId pins Hyderabad metro.
LI_LOCATION = os.environ.get("HITECHCITY_LI_LOCATION", "Hyderabad, Telangana, India")
LI_GEO_ID = os.environ.get("HITECHCITY_LI_GEO_ID", "105556991")  # Hyderabad, Telangana, India
LI_DISTANCE = os.environ.get("HITECHCITY_LI_DISTANCE", "25")

# Company-jobs keyword searches — lead/staff/manager first (not architect-only).
# LinkedIn company /jobs/?keywords= is a free-text field; keep phrases short.
SEARCH_KEYWORDS = [
    "Engineering Manager",
    "Technical Lead",
    "Tech Lead",
    "Staff Software Engineer",
    "Staff Engineer",
    "Principal Software Engineer",
    "Lead Software Engineer",
    "Software Development Manager",
    "Solution Architect",
    "Technical Architect",
    "Principal .NET",
    ".NET",
    "Azure",
]
# Back-compat alias used by referral copy / tests.
TITLES = SEARCH_KEYWORDS

# Cap per-company LinkedIn keyword searches (breadth over architect-only).
MAX_TITLE_SEARCHES = int(os.environ.get("HITECHCITY_LI_TITLE_SEARCHES", "10"))

# Title matches TITLE_OK via architect/principal/staff but are wrong for this .NET campus run.
LI_TITLE_SKIP = re.compile(
    r"product\s*manager|network\s*architect|system\s*test|quality\s*(platform|assurance|engineering)|"
    r"threat\s*detection|industrial\s*design|hardware\s*architect|"
    r"machine\s*learning|gpu\s*software|embedded\s*software|field\s*robotics|platform\s*power|network\s*hardware|"
    r"kernel\s*optimization|rtl\s*design|physical\s*design|silicon\s*design|"
    r"silicon\s*engineer|product\s*design\s*manager|"
    r"\bai\s*/\s*ml\b|\bai\s*&\s*ml\b|\baiml\b|\bai-ml\b|"
    r"\bdeep\s*learning\b|\bgen(?:erative)?\s*ai\b|\bllm\b|"
    r"\bai\s*engineer\b|\bml\s*engineer\b|\bai\s*architect\b|\bml\s*architect\b|"
    r"\bartificial\s*intelligence\b|\bcuda\b|\brocm\b|"
    r"\bdata\s*scientist\b|\bcomputer\s*vision\b",
    re.I,
)

REFERRAL_NOTE = (
    "Hi {first} — I'm a Principal Analyst (.NET/Azure, ~15 yrs) targeting senior architect/"
    "tech-lead roles in Hyderabad (Madhapur / Knowledge City). I applied for {role} at {company}. "
    "If you're open to it, I'd appreciate a referral or a brief 15–20 min screen. Thanks!"
)
# After this many CAPTCHA/login walls on company-website ATS, skip further EXT for that company.
MAX_EXT_WALLS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_WALLS", "1"))
# Soft incompletes must not starve remaining matching LinkedIn externals.
MAX_EXT_ATTEMPTS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_ATTEMPTS", "8"))
# Overnight / owner-asleep: after N soft incompletes, move to next company (0 = unlimited).
MAX_SOFT_INCOMPLETE_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_SOFT_INCOMPLETE", "0"))
EXT_ATS_TIME_CAP_S = int(os.environ.get("HITECHCITY_EXT_ATS_TIME_CAP_S", "90"))
if (os.environ.get("HOME_LOCAL") or "").strip().lower() in ("1", "true", "yes") or (
    os.environ.get("CHROME_HEADLESS") or "1"
).strip() in ("0", "false", "no"):
    # Owner-asleep keeps the short cron cap even on headed CDP.
    if not os.environ.get("HITECHCITY_EXT_ATS_TIME_CAP_S") and (
        os.environ.get("HITECHCITY_OWNER_ASLEEP") or ""
    ).strip().lower() not in ("1", "true", "yes"):
        EXT_ATS_TIME_CAP_S = max(EXT_ATS_TIME_CAP_S, 180)


@dataclass
class LiReport:
    startedAt: str
    finishedAt: str = ""
    applied: list[dict[str, Any]] = field(default_factory=list)
    external: list[dict[str, Any]] = field(default_factory=list)
    referrals: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)


def load_companies() -> list[dict[str, Any]]:
    data = json.loads(COMPANIES_PATH.read_text())
    return sorted(data.get("companies", []), key=lambda c: (c.get("priority", 9), c.get("name", "")))


def persist_linkedin_company_ids(updates: dict[str, str]) -> int:
    """Write resolved f_C ids back to companies.json (matched by linkedinSlug)."""
    if not updates:
        return 0
    data = json.loads(COMPANIES_PATH.read_text())
    saved = 0
    for row in data.get("companies", []):
        slug = (row.get("linkedinSlug") or "").strip()
        f_c = updates.get(slug) or ""
        if not f_c:
            continue
        if (row.get("linkedinCompanyId") or "").strip() == f_c:
            continue
        row["linkedinCompanyId"] = f_c
        saved += 1
    if saved:
        COMPANIES_PATH.write_text(json.dumps(data, indent=2) + "\n")
    return saved


def goto_retry(page: Page, url: str, *, timeout: int = 70000, attempts: int = 3) -> None:
    """Navigate with backoff on LinkedIn HTTP throttle / transient failures."""
    last: Exception | None = None
    for i in range(attempts):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            # Soft throttle signal in URL/title
            u = (page.url or "").lower()
            if any(x in u for x in ("/authwall", "/checkpoint/challenge", "unavailable")):
                time.sleep(2.5 + i * 2.0)
            return
        except Exception as e:
            last = e
            msg = str(e)
            if "ERR_HTTP_RESPONSE_CODE_FAILURE" in msg or "Timeout" in msg or "net::ERR_" in msg:
                time.sleep(3.0 + i * 3.5)
                continue
            raise
    assert last is not None
    raise last


def attach_js_dialog_guard(page: Page) -> None:
    """Dismiss native JS dialogs without crashing CDP sessions.

    Playwright's default auto-dismiss races with Chrome when a dialog is already
    gone → ProtocolError Page.handleJavaScriptDialog / No dialog is showing.
    """
    if getattr(page, "_hitechcity_dialog_guard", False):
        return

    def _on_dialog(dialog) -> None:  # type: ignore[no-untyped-def]
        try:
            dialog.dismiss()
        except Exception:
            try:
                dialog.accept()
            except Exception:
                pass

    try:
        page.on("dialog", _on_dialog)
        setattr(page, "_hitechcity_dialog_guard", True)
    except Exception:
        pass


def dismiss(page: Page) -> None:
    attach_js_dialog_guard(page)
    for sel in (
        "button.artdeco-modal__dismiss",
        "button[aria-label='Dismiss']",
        "button:has-text('Not now')",
        "button:has-text('No thanks')",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(timeout=800)
        except Exception:
            pass
    # "Did you finish applying?" tracker modal — dismiss so Apply is not blocked.
    try:
        body = page.locator("body").inner_text()[:1200]
        if re.search(r"did you finish applying|you'?ll find this job under In progress", body, re.I):
            no_btn = page.get_by_role("button", name=re.compile(r"^No$", re.I)).first
            if no_btn.count() and no_btn.is_visible():
                no_btn.click(timeout=800)
    except Exception:
        pass


def resolve_company_f_c(page: Page, slug: str) -> str:
    """Resolve LinkedIn numeric company id(s) for f_C= jobs search filter.

    Company /jobs/ pages no longer expose /jobs/view/ anchors — searchable results
    live on /jobs/search/?f_C=<id>. Pull id from company page urn or Show-all link.
    """
    slug = (slug or "").strip().strip("/")
    if not slug:
        return ""
    try:
        goto_retry(page, f"https://www.linkedin.com/company/{slug}/jobs/", timeout=60000)
        time.sleep(2.0)
        dismiss(page)
    except Exception:
        return ""
    try:
        found = page.evaluate(
            """() => {
              const ids = [];
              const push = (v) => {
                const s = String(v || '');
                for (const m of s.matchAll(/(?:f_C=|fsd_company:|organization:|company:)(\\d{3,})/g)) {
                  if (!ids.includes(m[1])) ids.push(m[1]);
                }
                for (const m of s.matchAll(/[?&]f_C=([^&]+)/g)) {
                  for (const part of decodeURIComponent(m[1]).split(',')) {
                    const id = part.trim();
                    if (/^\\d{3,}$/.test(id) && !ids.includes(id)) ids.push(id);
                  }
                }
              };
              push(document.documentElement.innerHTML.slice(0, 500000));
              for (const a of document.querySelectorAll('a[href*="f_C="], a[href*="search-results"]')) {
                push(a.href || '');
              }
              return ids.slice(0, 8);
            }"""
        )
    except Exception:
        found = []
    ids = [str(x) for x in (found or []) if str(x).isdigit()]
    if not ids:
        return ""
    # Prefer classic short org ids (e.g. 1068) — long marketing urns are noisier.
    ids_sorted = sorted(ids, key=lambda x: (len(x), x))
    return ids_sorted[0]


def company_jobs_url(slug: str, title: str, *, company_f_c: str = "") -> str:
    """Hyderabad jobs search for one campus employer.

    Always use /jobs/search/?keywords=…&geoId=… (has /jobs/view/ cards).
    Add f_C when resolved. Never use company /jobs/ — those pages lack cards.
    Always pin Hyderabad via location + geoId so results stay campus-relevant.
    """
    loc_q = (
        f"&location={quote(LI_LOCATION)}"
        f"&geoId={quote(LI_GEO_ID)}"
        f"&distance={quote(LI_DISTANCE)}"
    )
    # Always use /jobs/search — company /jobs/ pages have no clickable cards
    # (Solera ID-miss returned n=0 on every keyword). Without f_C, Hyd+keyword
    # cards still extract; company_name_match drops other employers.
    url = (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={quote(title)}"
        f"{loc_q}"
    )
    if company_f_c:
        url += f"&f_C={company_f_c}"
    return url


def extract_job_ids(page: Page) -> list[str]:
    """Backward-compatible id list — prefers title-filtered cards when available."""
    cards = extract_job_cards(page)
    if cards:
        return [c["id"] for c in cards][:MAX_SCAN]
    try:
        html = page.content()
    except Exception:
        html = ""
    ids = []
    seen = set()
    for m in re.finditer(
        r"(?:jobPosting:|/jobs/view/|currentJobId=|data-occludable-job-id=\"|originToLandingJobPostings=)(\d{6,})",
        html,
    ):
        jid = m.group(1)
        if jid not in seen:
            seen.add(jid)
            ids.append(jid)
    return ids[:MAX_SCAN]


def extract_job_cards(page: Page) -> list[dict[str, str]]:
    """Parse LinkedIn job result cards (id + title + location) and drop junk early.

    Prefer /jobs/search result list (/jobs/view/ + data-occludable-job-id). Company
    /jobs/ square cards only link to search-results clusters — still harvest title
    + originToLandingJobPostings when needed.
    """
    try:
        raw = page.evaluate(
            """() => {
              const out = [];
              const seen = new Set();
              const push = (id, title, loc) => {
                if (!id || seen.has(id)) return;
                seen.add(id);
                out.push({
                  id: String(id),
                  title: (title || '').trim().replace(/\\s+/g, ' ').slice(0, 180),
                  location: (loc || '').trim().replace(/\\s+/g, ' ').slice(0, 120),
                });
              };
              const cleanTitle = (t) => {
                t = (t || '').trim();
                t = t.replace(/^Job Title\\s+/i, '');
                const lines = t.split('\\n').map(s => s.trim()).filter(Boolean);
                // Prefer first non-meta line.
                for (const l of lines) {
                  if (/^(company name|with verification|\\d+ (school|connect))/i.test(l)) continue;
                  return l.slice(0, 180);
                }
                return (lines[0] || t).slice(0, 180);
              };

              // 1) Standard jobs search results (clickable /jobs/view/).
              for (const a of document.querySelectorAll('a[href*="/jobs/view/"]')) {
                const m = (a.href || '').match(/\\/jobs\\/view\\/(\\d+)/);
                if (!m) continue;
                const card = a.closest('li') || a.closest('[data-occludable-job-id]') || a.parentElement;
                let title = cleanTitle(a.innerText || a.getAttribute('aria-label') || '');
                if (!title || title.length < 4) {
                  const tEl = card && card.querySelector(
                    '.base-search-card__title, .job-card-list__title, strong, h3, h4'
                  );
                  if (tEl) title = cleanTitle(tEl.innerText || '');
                }
                let loc = '';
                if (card) {
                  const locEl = card.querySelector(
                    '.job-search-card__location, .artdeco-entity-lockup__caption, '
                    + '.base-search-card__metadata, [class*="location"]'
                  );
                  if (locEl) loc = (locEl.innerText || '').trim().split('\\n')[0];
                }
                if (/^\\d+\\s+jobs?\\b/i.test(title) || /see all jobs|show more|show all jobs/i.test(title)) continue;
                push(m[1], title, loc);
                if (out.length >= 40) break;
              }

              // 2) Occludable job cards (jobs search layout).
              for (const el of document.querySelectorAll('[data-occludable-job-id]')) {
                const id = el.getAttribute('data-occludable-job-id');
                if (!id || seen.has(id)) continue;
                const tEl = el.querySelector('a[href*="/jobs/view/"], strong, h3, .job-card-list__title, .artdeco-entity-lockup__title');
                const title = cleanTitle(tEl ? (tEl.innerText || '') : (el.innerText || ''));
                let loc = '';
                const locEl = el.querySelector('.job-search-card__location, .artdeco-entity-lockup__caption, [class*="location"]');
                if (locEl) loc = (locEl.innerText || '').trim().split('\\n')[0];
                push(id, title, loc);
                if (out.length >= 40) break;
              }

              // 3) Company-page square cards: title in text, id in originToLandingJobPostings.
              if (out.length < 3) {
                for (const a of document.querySelectorAll('a.job-card-square__link, a[class*="job-card-square"]')) {
                  const title = cleanTitle(a.innerText || '');
                  const href = a.href || '';
                  const m = href.match(/originToLandingJobPostings=([^&]+)/i);
                  let id = '';
                  if (m) {
                    id = decodeURIComponent(m[1]).split(',')[0].trim();
                  }
                  if (!id) {
                    const m2 = href.match(/\\/jobs\\/view\\/(\\d+)/);
                    if (m2) id = m2[1];
                  }
                  if (!id || !title) continue;
                  let loc = '';
                  if (/hyderabad|bengaluru|bangalore|mumbai|remote|india/i.test(a.innerText || '')) {
                    const lm = (a.innerText || '').match(/Hyderabad|Bengaluru|Bangalore|Mumbai|Remote[^\\n]{0,20}|India/i);
                    if (lm) loc = lm[0];
                  }
                  push(id, title, loc);
                  if (out.length >= 40) break;
                }
              }
              return out;
            }"""
        )
    except Exception:
        raw = []
    cards: list[dict[str, str]] = []
    for row in raw or []:
        jid = str(row.get("id") or "").strip()
        title = (row.get("title") or "").strip()
        loc = (row.get("location") or "").strip()
        if not jid:
            continue
        if title:
            if skip_reason(title):
                continue
            if LI_TITLE_SKIP.search(title):
                continue
            if not title_matches_senior_stack(title):
                continue
            if loc and not location_allowed(loc) and not location_or_campus_ok(loc, "", ""):
                continue
        cards.append({"id": jid, "title": title, "location": loc})
    titled = [c for c in cards if c.get("title")]
    return (titled or cards)[:MAX_SCAN]


def card_meta(page: Page) -> dict[str, str]:
    try:
        return page.evaluate(
            """() => {
              const pick = (sel) => {
                const el = document.querySelector(sel);
                return el ? (el.innerText || '').trim().replace(/\\s+/g, ' ') : '';
              };
              // TOP CARD only for location — never full page body (sidebar/footer contaminate).
              const topCard =
                pick('.job-details-jobs-unified-top-card__container') ||
                pick('.jobs-unified-top-card') ||
                pick('.job-view-layout') ||
                '';
              const topPrimary =
                pick('.job-details-jobs-unified-top-card__primary-description-container') ||
                pick('.jobs-unified-top-card__primary-description') ||
                pick('.job-details-jobs-unified-top-card__tertiary-description-container') ||
                '';
              const bodyHead = (topCard || (document.body.innerText || '')).slice(0, 1800);
              const lines = bodyHead.split('\\n').map(s => s.trim()).filter(Boolean);
              const skip = /^(home|my network|jobs|messaging|notifications|more|me|for business|learning|\\d+|\\d+ notifications?)$/i;
              const content = lines.filter(l => !skip.test(l) && !/^skip to\\b/i.test(l) && l.length > 1);
              let role = '';
              let company = '';
              // Title format: "Role | Company | LinkedIn"
              const dt = (document.title || '').replace(/\\s*\\|\\s*LinkedIn\\s*$/i, '');
              const parts = dt.split('|').map(s => s.trim()).filter(Boolean);
              if (parts.length >= 2) {
                role = parts[0];
                company = parts[1];
              }
              const a = document.querySelector(
                '.job-details-jobs-unified-top-card__company-name a, .jobs-unified-top-card__company-name a'
              );
              if (a && (a.innerText || '').trim()) company = (a.innerText || '').trim();
              if (!company && content[0] && content[0].length < 80) company = content[0];
              if (!role && content[1] && content[1].length < 160) role = content[1];
              if (!role) {
                const hit = content.find(l => /architect|engineer|manager|lead|principal|staff|director|consultant/i.test(l));
                if (hit) role = hit;
              }
              let locText = '';
              const locBlob = (topPrimary || content.slice(0, 12).join(' \\n ')).slice(0, 400);
              const locMatch = locBlob.match(
                /([A-Za-z .]+(?:,\\s*)?(?:Telangana|Karnataka|Maharashtra|Tamil Nadu|Haryana|India)[^·\\n]{0,60}|\\bRemote\\b[^·\\n]{0,40}|\\bWFH\\b[^·\\n]{0,40})/i
              );
              if (locMatch) locText = locMatch[0].trim().slice(0, 220);
              if (!locText) {
                for (const l of (topPrimary ? [topPrimary] : []).concat(content.slice(0, 12))) {
                  if (/(hyderabad|telangana|madhapur|bengaluru|bangalore|chennai|pune|gachibowli|gurugram|gurgaon|noida|\\bremote\\b|\\bwfh\\b|\\bindia\\b)/i.test(l)
                      && l.length < 180) {
                    locText = l.slice(0, 220);
                    break;
                  }
                }
              }
              const easy = /easy apply/i.test(bodyHead);
              const m = window.location.href.match(/\\/jobs\\/view\\/(\\d+)/);
              return {
                role: role || '',
                company: company || '',
                location: locText,
                easy: easy ? '1' : '0',
                job_id: m ? m[1] : '',
                url: window.location.href,
                bodyHead: bodyHead.slice(0, 500)
              };
            }"""
        )
    except Exception:
        return {}


def fill_easy_apply(page: Page) -> tuple[str, str]:
    """Minimal Easy Apply walker — confirm submitted only."""
    # Prefer existing durable helper if importable as subprocess would be heavy; keep local.
    try:
        from tools.resume_paths import ensure_resume_aliases

        ensure_resume_aliases()
    except Exception:
        pass

    start = time.time()
    time_cap = int(os.environ.get("HITECHCITY_EASY_TIME_CAP_S", "120"))
    for _ in range(8):
        if time.time() - start >= time_cap:
            return "blocked", "easy_apply_time_cap"
        dismiss(page)
        # LinkedIn Easy Apply sometimes embeds reCAPTCHA in the modal.
        try:
            for fr in page.frames:
                u = (fr.url or "").lower()
                if "/recaptcha/" in u or "hcaptcha.com" in u:
                    return "blocked", "easy_apply_recaptcha"
        except Exception:
            pass
        body = ""
        try:
            body = page.locator("body").inner_text()[:5000]
        except Exception:
            pass
        if re.search(r"application (sent|submitted)|applied to ", body, re.I):
            return "applied", "easy_apply_submitted"

        # Resume choose / upload
        try:
            if page.get_by_text(re.compile(r"Rafi_Resume", re.I)).count():
                page.get_by_text(re.compile(r"Rafi_Resume", re.I)).first.click(timeout=1000)
        except Exception:
            pass
        try:
            for inp in page.locator("input[type='file']").all()[:2]:
                inp.set_input_files(resume_path())
        except Exception:
            pass

        # Common fields
        for label, val in (
            (r"phone|mobile", "8790251698"),
            (r"email", (os.environ.get("APPLY_EMAIL") or os.environ.get("LINKEDIN_EMAIL") or "").strip()),
            (r"current.*(ctc|salary|compensation)", "5200000"),
            (r"expected.*(ctc|salary|compensation)", "6500000"),
            (r"notice", "0"),
            (r"years of experience|total experience", "15"),
            (r"linkedin", "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba"),
            (r"city", "Hyderabad"),
        ):
            try:
                labs = page.locator("label")
                for i in range(min(labs.count(), 25)):
                    t = (labs.nth(i).inner_text(timeout=200) or "").strip().lower()
                    if re.search(label, t, re.I):
                        fid = labs.nth(i).get_attribute("for")
                        ctrl = (
                            page.locator(f"#{fid}").first
                            if fid
                            else labs.nth(i).locator("xpath=following::input[1]").first
                        )
                        if ctrl.count():
                            ctrl.fill(val)
                        break
            except Exception:
                pass

        # Next / Review / Submit
        clicked = False
        for name in ("Submit application", "Review", "Next", "Continue", "Send application"):
            try:
                btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I))
                if btn.count() and btn.first.is_visible() and btn.first.is_enabled():
                    btn.first.click(timeout=2500, force=True)
                    clicked = True
                    time.sleep(1.0)
                    break
            except Exception:
                continue
        if not clicked:
            break
    body = ""
    try:
        body = page.locator("body").inner_text()[:5000]
    except Exception:
        pass
    if re.search(r"application (sent|submitted)|applied to ", body, re.I):
        return "applied", "easy_apply_submitted"
    try:
        from tools.ats.complete import wait_owner_finish_apply
    except Exception:
        from ats.complete import wait_owner_finish_apply  # type: ignore
    owner = wait_owner_finish_apply(page, hint="LinkedIn Easy Apply required fields / Submit")
    if owner:
        return owner
    return "blocked", "easy_apply_incomplete"


def follow_external(page: Page, meta: dict[str, str]) -> dict[str, Any]:
    row = {
        "company": meta.get("company", ""),
        "role": meta.get("role", ""),
        "job_id": meta.get("job_id", ""),
        "url": meta.get("url", ""),
        "path": "linkedin-external-ats",
        "status": "blocked",
        "reason": "",
    }
    apply_btn = None
    # New LinkedIn job view often uses <a aria-label="Apply on company website">Apply</a>.
    for sel in (
        "a[aria-label*='Apply on company website']",
        "button[aria-label*='Apply on company website']",
        "button.jobs-apply-button",
        "a.jobs-apply-button",
        "button.artdeco-button--primary:has-text('Apply')",
        "a:text-is('Apply')",
    ):
        locb = page.locator(sel).first
        try:
            if locb.count() and locb.is_visible():
                label = ((locb.inner_text() or "") + " " + (locb.get_attribute("aria-label") or "")).strip().lower()
                if "easy apply" in label and "company website" not in label:
                    row["status"] = "skipped"
                    row["reason"] = "easy_apply_not_external"
                    return row
                if "apply" in label:
                    apply_btn = locb
                    break
        except Exception:
            continue
    if not apply_btn:
        try:
            exact = page.get_by_role("link", name=re.compile(r"^Apply$", re.I))
            if exact.count() and exact.first.is_visible():
                apply_btn = exact.first
        except Exception:
            pass
    if not apply_btn:
        try:
            exact = page.get_by_role("button", name=re.compile(r"^Apply$", re.I))
            if exact.count() and exact.first.is_visible():
                apply_btn = exact.first
        except Exception:
            pass
    if not apply_btn:
        row["status"] = "skipped"
        row["reason"] = "no_apply_button"
        return row

    before = set(page.context.pages)
    try:
        with page.context.expect_page(timeout=8000) as ni:
            apply_btn.click(timeout=4000)
        ats = ni.value
    except Exception:
        time.sleep(2)
        ats = page
        for p2 in page.context.pages:
            if p2 not in before and p2 != page:
                ats = p2
                break
    try:
        ats.wait_for_load_state("domcontentloaded", timeout=30000)
    except Exception:
        pass
    time.sleep(1.5)
    status, reason = attempt_ats_apply(ats, time_cap_s=EXT_ATS_TIME_CAP_S)
    row["status"] = status
    row["reason"] = reason
    row["atsUrl"] = ats.url
    if ats != page:
        try:
            ats.close()
        except Exception:
            pass
    return row


def message_poster(page: Page, company: str, role: str) -> dict[str, Any]:
    row = {"company": company, "role": role, "status": "blocked", "reason": "", "path": "poster-message"}
    try:
        # Poster / hiring team message CTA near job
        btn = page.locator(
            "button:has-text('Message'), a:has-text('Message'), "
            ".jobs-poster__name button, .hirer-card button:has-text('Message')"
        ).first
        if not (btn.count() and btn.is_visible()):
            row["status"] = "skipped"
            row["reason"] = "no_poster_message"
            return row
        btn.click(timeout=3000)
        time.sleep(1.2)
        first = "there"
        note = REFERRAL_NOTE.format(first=first, role=role, company=company)
        box = page.locator("div.msg-form__contenteditable, div[role='textbox']").first
        if not box.count():
            row["reason"] = "no_compose_box"
            return row
        box.click()
        box.fill(note[:280] if len(note) > 280 else note)
        send = page.locator("button.msg-form__send-button, button:has-text('Send')").first
        if send.count() and send.is_enabled():
            send.click(timeout=2500)
            time.sleep(1.0)
            row["status"] = "sent"
            row["reason"] = "poster_message"
            return row
        row["reason"] = "send_disabled"
        return row
    except Exception as e:
        row["reason"] = f"message_error:{e}"
        return row


def referral_people_search(page: Page, company: str, role: str) -> dict[str, Any]:
    """Send one connection note to a senior engineer / recruiter at company (soft referral)."""
    row = {
        "company": company,
        "role": role,
        "status": "blocked",
        "reason": "",
        "path": "people-referral",
    }
    q = f"{company} Hyderabad (Engineering Manager OR Architect OR Recruiter OR Talent)"
    url = f"https://www.linkedin.com/search/results/people/?keywords={quote(q)}&origin=GLOBAL_SEARCH_HEADER"
    try:
        goto_retry(page, url, timeout=60000)
    except Exception as e:
        row["reason"] = f"people_nav:{e}"
        return row
    time.sleep(2.5)
    dismiss(page)
    # Prefer Connect with note
    try:
        connect = page.get_by_role("button", name=re.compile(r"^Connect$", re.I)).first
        if not (connect.count() and connect.is_visible()):
            # Try More → Connect on first result
            more = page.get_by_role("button", name=re.compile(r"More", re.I)).first
            if more.count() and more.is_visible():
                # Overlay intercepts the visible More control (all 18 referral rows this run).
                more.click(timeout=2500, force=True)
                time.sleep(0.5)
            connect = page.get_by_role("button", name=re.compile(r"Connect", re.I)).first
        if not (connect.count() and connect.is_visible()):
            row["status"] = "skipped"
            row["reason"] = "no_connect_cta"
            return row
        connect.click(timeout=2500, force=True)
        time.sleep(1.0)
        add_note = page.get_by_role("button", name=re.compile(r"Add a note", re.I)).first
        if add_note.count() and add_note.is_visible():
            add_note.click(timeout=1500)
            time.sleep(0.6)
        note = REFERRAL_NOTE.format(first="there", role=role or "a senior role", company=company)
        ta = page.locator("textarea[name='message'], textarea#custom-message, textarea").first
        if ta.count():
            ta.fill(note[:300])
        send = page.get_by_role("button", name=re.compile(r"^Send$", re.I)).first
        if send.count() and send.is_enabled():
            send.click(timeout=2500)
            time.sleep(1.0)
            row["status"] = "sent"
            row["reason"] = "connection_note"
            return row
        # Without premium, Send without note may be only option
        send2 = page.get_by_role("button", name=re.compile(r"^Send$", re.I)).first
        if send2.count() and send2.is_enabled():
            send2.click(timeout=2000)
            row["status"] = "sent"
            row["reason"] = "connection_no_note"
            return row
        row["reason"] = "invite_incomplete"
        return row
    except Exception as e:
        row["reason"] = f"referral_error:{e}"
        return row


def run(companies: list[dict[str, Any]] | None = None) -> LiReport:
    companies = companies or load_companies()
    # Focus priority 1–2 first (raised after discovery expands tenant list)
    max_co = int(os.environ.get("HITECHCITY_LI_MAX_COMPANIES", "30"))
    companies = [c for c in companies if int(c.get("priority", 9)) <= 2][:max_co]
    report = LiReport(startedAt=datetime.now(timezone.utc).isoformat())
    seen_jobs: set[str] = set()
    applied = 0
    referrals = 0

    f_c_updates: dict[str, str] = {}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP, timeout=20_000)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45000)
        attach_js_dialog_guard(page)
        for pg in list(context.pages):
            attach_js_dialog_guard(pg)

        goto_retry(page, "https://www.linkedin.com/feed/", timeout=60000)
        time.sleep(2.5)
        url_l = (page.url or "").lower()
        logged_in = bool(
            page.locator(
                "img.global-nav__me-photo, button.global-nav__primary-link-me-menu-trigger, "
                ".global-nav__me, a[data-control-name='identity_welcome_message']"
            ).count()
        ) or bool(re.search(r"/feed|/in/", url_l))
        login_wall = any(
            x in url_l for x in ("/login", "/uas/login", "/checkpoint", "authwall", "/signup")
        )
        if login_wall or not logged_in:
            # Avoid false positives from footer "Sign in" text when already authenticated.
            body_head = ""
            try:
                body_head = page.locator("body").inner_text()[:500]
            except Exception:
                pass
            if login_wall or re.search(r"sign in to linkedin|join linkedin|welcome back", body_head, re.I):
                report.blocked.append({"reason": "linkedin_login_required", "url": page.url})
                report.finishedAt = datetime.now(timezone.utc).isoformat()
                REPORT.write_text(json.dumps(asdict(report), indent=2))
                print(json.dumps({"error": "linkedin_login_required", "url": page.url}))
                return report

        for company in companies:
            if applied >= MAX_APPLY:
                break
            name = company["name"]
            slug = company.get("linkedinSlug") or ""
            if not slug:
                report.skipped.append({"company": name, "reason": "missing_linkedin_slug"})
                continue
            ext_walls = 0
            ext_attempts = 0
            soft_incompletes = 0

            # Resolve numeric company id once — /jobs/search/?f_C= has clickable cards.
            company_f_c = (company.get("linkedinCompanyId") or "").strip()
            if not company_f_c:
                company_f_c = resolve_company_f_c(page, slug)
                if company_f_c:
                    company["linkedinCompanyId"] = company_f_c
                    f_c_updates[slug] = company_f_c
                    print(f"LI COMPANY ID {name} | f_C={company_f_c}", flush=True)
                else:
                    print(f"LI COMPANY ID miss {name} | slug={slug} (fallback jobs/search no f_C)", flush=True)

            job_ids: list[str] = []
            # Search lead/staff/manager/.NET keywords via jobs/search + company filter.
            for title in SEARCH_KEYWORDS[:MAX_TITLE_SEARCHES]:
                if len(job_ids) >= MAX_SCAN:
                    break
                url = company_jobs_url(slug, title, company_f_c=company_f_c)
                print(f"LI COMPANY JOBS {name} | {title}", flush=True)
                try:
                    goto_retry(page, url, timeout=70000)
                except Exception as e:
                    report.blocked.append({"company": name, "title": title, "reason": f"search_nav:{e}"})
                    continue
                time.sleep(2.5)
                dismiss(page)
                try:
                    for _ in range(2):
                        page.mouse.wheel(0, 1200)
                        time.sleep(0.6)
                except Exception:
                    pass
                cards = extract_job_cards(page)
                print(f"LI CARDS {name} | {title} | n={len(cards)}", flush=True)
                for card in cards:
                    jid = card.get("id") or ""
                    if jid and jid not in seen_jobs:
                        job_ids.append(jid)
                        seen_jobs.add(jid)
                # Fallback: raw ids only when card parse empty (still better than nothing).
                if not cards:
                    for jid in extract_job_ids(page):
                        if jid not in seen_jobs:
                            job_ids.append(jid)
                            seen_jobs.add(jid)

            job_ids = job_ids[: min(len(job_ids), MAX_SCAN)]
            print(f"LI IDS {name} count={len(job_ids)}", flush=True)
            for jid in job_ids:
                if applied >= MAX_APPLY:
                    break
                view = f"https://www.linkedin.com/jobs/view/{jid}/"
                try:
                    goto_retry(page, view, timeout=60000)
                except Exception as e:
                    report.blocked.append({"company": name, "job_id": jid, "reason": f"view_nav:{e}"})
                    continue
                time.sleep(2.0)
                dismiss(page)
                meta = card_meta(page) or {}
                company_found = meta.get("company") or name
                role = meta.get("role") or ""
                loc = meta.get("location") or ""
                meta["job_id"] = jid
                meta["url"] = view

                if not company_name_match(name, company_found) and not company_name_match(
                    name, meta.get("bodyHead") or ""
                ):
                    print(f"LI SKIP company_mismatch {company_found!r} | {role[:60]}", flush=True)
                    report.skipped.append(
                        {
                            "target": name,
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": "company_mismatch",
                        }
                    )
                    continue
                reason = skip_reason(role, company_found)
                if reason:
                    print(f"LI SKIP {reason} | {role[:60]}", flush=True)
                    report.skipped.append(
                        {"company": company_found, "role": role, "job_id": jid, "reason": reason}
                    )
                    continue
                if LI_TITLE_SKIP.search(role or ""):
                    print(f"LI SKIP wrong_title_stack | {role[:60]}", flush=True)
                    report.skipped.append(
                        {
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": "wrong_title_stack",
                        }
                    )
                    continue
                # Empty title parse → apply bias (do not invent title_not_senior).
                if (role or "").strip() and not title_matches_senior_stack(role):
                    print(f"LI SKIP title_not_senior | {role[:60]}", flush=True)
                    report.skipped.append(
                        {
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": "title_not_senior",
                        }
                    )
                    continue
                if not (role or "").strip():
                    print(f"LI WARN empty_title_apply_bias | {jid}", flush=True)
                # HARD: top-card location only — never bodyHead (sidebar/footer contaminate).
                # Empty location → apply bias (uncertain between skip and apply → APPLY).
                if (loc or "").strip():
                    if not location_allowed(loc) and not location_or_campus_ok(loc, "", ""):
                        print(f"LI SKIP location | {loc[:80]} | {role[:50]}", flush=True)
                        report.skipped.append(
                            {
                                "company": company_found,
                                "role": role,
                                "location": loc,
                                "job_id": jid,
                                "reason": "location",
                            }
                        )
                        continue

                try:
                    top = page.locator("body").inner_text()[:1800]
                    if re.search(r"\bApplied\b", top) and not re.search(r"Easy Apply", top[:500], re.I):
                        report.skipped.append(
                            {
                                "company": company_found,
                                "role": role,
                                "job_id": jid,
                                "reason": "already_applied",
                            }
                        )
                        continue
                except Exception:
                    pass

                easy = page.locator(
                    "button.jobs-apply-button:has-text('Easy Apply'), "
                    "button[aria-label*='Easy Apply'], button:has-text('Easy Apply')"
                ).first
                if easy.count() and easy.is_visible():
                    print(f"LI EASY {company_found} | {role} | {jid}", flush=True)
                    try:
                        easy.click(timeout=3000)
                    except Exception:
                        report.blocked.append(
                            {
                                "company": company_found,
                                "role": role,
                                "job_id": jid,
                                "reason": "easy_click_failed",
                            }
                        )
                        continue
                    time.sleep(1.2)
                    status, why = fill_easy_apply(page)
                    row = {
                        "company": company_found or name,
                        "role": role,
                        "job_id": jid,
                        "location": loc,
                        "url": view,
                        "path": "linkedin-easy-apply",
                        "status": status,
                        "reason": why,
                        "campusCompany": name,
                    }
                    notify_application_result(
                        status=status,
                        company=str(row["company"]),
                        role=str(role),
                        reason=str(why),
                        path="linkedin-easy-apply",
                        url=view,
                    )
                    if status == "applied":
                        report.applied.append(row)
                        applied += 1
                        if referrals < MAX_REFERRALS:
                            msg = message_poster(page, company_found or name, role)
                            report.referrals.append(msg)
                            if msg.get("status") == "sent":
                                referrals += 1
                            elif referrals < MAX_REFERRALS:
                                ref = referral_people_search(page, company_found or name, role)
                                report.referrals.append(ref)
                                if ref.get("status") == "sent":
                                    referrals += 1
                    else:
                        report.blocked.append(row)
                    dismiss(page)
                    try:
                        page.keyboard.press("Escape")
                    except Exception:
                        pass
                    continue

                if ext_walls >= MAX_EXT_WALLS_PER_COMPANY:
                    print(
                        f"LI SKIP ext_wall_cap | {company_found} | {role[:50]} | {jid}",
                        flush=True,
                    )
                    report.skipped.append(
                        {
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": "ext_wall_cap",
                            "location": loc,
                        }
                    )
                    continue
                if (
                    MAX_SOFT_INCOMPLETE_PER_COMPANY > 0
                    and soft_incompletes >= MAX_SOFT_INCOMPLETE_PER_COMPANY
                ):
                    print(
                        f"LI SKIP soft_incomplete_cap | {company_found} | {role[:50]} | {jid}",
                        flush=True,
                    )
                    report.skipped.append(
                        {
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": "soft_incomplete_cap",
                            "location": loc,
                        }
                    )
                    continue

                print(f"LI EXT {company_found} | {role} | {jid}", flush=True)
                ext = follow_external(page, meta)
                ext["campusCompany"] = name
                ext["location"] = loc
                notify_application_result(
                    status=str(ext.get("status") or ""),
                    company=str(ext.get("company") or company_found or name),
                    role=str(ext.get("role") or role),
                    reason=str(ext.get("reason") or ""),
                    path="linkedin-external-ats",
                    url=str(ext.get("url") or view),
                )
                if ext["status"] == "applied":
                    report.external.append(ext)
                    report.applied.append(ext)
                    applied += 1
                    ext_attempts += 1
                    if referrals < MAX_REFERRALS:
                        ref = referral_people_search(page, company_found or name, role)
                        report.referrals.append(ref)
                        if ref.get("status") == "sent":
                            referrals += 1
                elif ext["status"] == "skipped":
                    report.skipped.append(ext)
                else:
                    report.blocked.append(ext)
                    why = ext.get("reason") or ""
                    try:
                        from tools.ats.complete import is_hard_ats_wall
                    except Exception:
                        from ats.complete import is_hard_ats_wall  # type: ignore
                    if is_hard_ats_wall(why):
                        ext_walls += 1
                        ext_attempts += 1
                        print(
                            f"LI EXT WALL {company_found} walls={ext_walls}/{MAX_EXT_WALLS_PER_COMPANY} "
                            f"attempts={ext_attempts}/{MAX_EXT_ATTEMPTS_PER_COMPANY} | {why}",
                            flush=True,
                        )
                    elif "incomplete" in why.lower():
                        soft_incompletes += 1
                        print(
                            f"LI EXT SOFT {company_found} soft={soft_incompletes}/"
                            f"{MAX_SOFT_INCOMPLETE_PER_COMPANY or '∞'} | {why}",
                            flush=True,
                        )
                    else:
                        ext_attempts += 1

        # Extra referral sweep for priority-1 companies even if thin inventory
        for company in companies:
            if referrals >= MAX_REFERRALS:
                break
            if int(company.get("priority", 9)) > 1:
                continue
            ref = referral_people_search(page, company["name"], "Solution Architect / Technical Lead")
            report.referrals.append(ref)
            if ref.get("status") == "sent":
                referrals += 1

    n_saved = persist_linkedin_company_ids(f_c_updates)
    if n_saved:
        print(f"LI COMPANY ID persisted={n_saved}", flush=True)

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(asdict(report), indent=2))
    print(
        json.dumps(
            {
                "applied": len(report.applied),
                "external": len(report.external),
                "referrals": sum(1 for r in report.referrals if r.get("status") == "sent"),
                "blocked": len(report.blocked),
                "skipped": len(report.skipped),
            }
        )
    )
    return report


if __name__ == "__main__":
    run()
