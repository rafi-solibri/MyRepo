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
from .careers_apply import card_location_ok, url_loc_hint
from tools.hitechcity.filters import (
    company_name_match,
    location_or_campus_ok,
    skip_reason,
    title_matches_senior_stack,
)

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

TITLES = [
    "Solution Architect",
    "Technical Architect",
    "Software Architect",
    "Technical Lead",
    "Engineering Manager",
    "Principal .NET",
    ".NET Architect",
    "Azure Architect",
]

# Title matches TITLE_OK via architect/principal/staff but are wrong for this .NET campus run.
LI_TITLE_SKIP = re.compile(
    r"product\s*manager|network\s*architect|system\s*test|quality\s*(platform|assurance|engineering)|"
    r"threat\s*detection|industrial\s*design|hardware\s*architect|machine\s*learning\s*hardware|"
    r"gpu\s*software|embedded\s*software|field\s*robotics|platform\s*power|network\s*hardware|"
    r"kernel\s*optimization|rtl\s*design|physical\s*design",
    re.I,
)

REFERRAL_NOTE = (
    "Hi {first} — I'm a Principal Analyst (.NET/Azure, ~15 yrs) targeting senior architect/"
    "tech-lead roles in Hyderabad (Madhapur / Knowledge City). I applied for {role} at {company}. "
    "If you're open to it, I'd appreciate a referral or a brief 15–20 min screen. Thanks!"
)
# After this many CAPTCHA/login walls on company-website ATS, skip further EXT for that company.
MAX_EXT_WALLS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_WALLS", "1"))
# Hard cap on external ATS attempts per company (incomplete Phenom/guest forms burn the run).
MAX_EXT_ATTEMPTS_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_EXT_ATTEMPTS", "2"))
EXT_ATS_TIME_CAP_S = int(os.environ.get("HITECHCITY_EXT_ATS_TIME_CAP_S", "45"))


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


def is_linkedin_url(url: str) -> bool:
    u = (url or "").lower()
    return "linkedin.com" in u and "/uas/login" not in u and "authwall" not in u


def close_stray_ats_pages(keep: Page) -> None:
    """Drop leftover Workday/Greenhouse tabs so CDP is not stuck off LinkedIn."""
    try:
        ctx = keep.context
        pages = list(ctx.pages)
    except Exception:
        return
    for p2 in pages:
        if p2 == keep:
            continue
        try:
            u = (p2.url or "").lower()
        except Exception:
            u = ""
        if "linkedin.com" in u or u.startswith("about:blank"):
            continue
        try:
            p2.close()
        except Exception:
            pass


def ensure_linkedin_page(page: Page, fallback_url: str = "https://www.linkedin.com/feed/") -> Page:
    """Recover after same-tab company-website ATS (Workday) swallows LinkedIn navigation."""
    close_stray_ats_pages(page)
    try:
        if is_linkedin_url(page.url or ""):
            return page
    except Exception:
        pass
    try:
        for p2 in list(page.context.pages):
            try:
                if is_linkedin_url(p2.url or ""):
                    close_stray_ats_pages(p2)
                    return p2
            except Exception:
                continue
    except Exception:
        pass
    try:
        page.goto("about:blank", wait_until="domcontentloaded", timeout=15000)
        page.goto(fallback_url, wait_until="domcontentloaded", timeout=45000)
        if is_linkedin_url(page.url or ""):
            return page
    except Exception:
        pass
    try:
        fresh = page.context.new_page()
        fresh.set_default_timeout(45000)
        fresh.goto(fallback_url, wait_until="domcontentloaded", timeout=45000)
        try:
            if page != fresh:
                page.close()
        except Exception:
            pass
        return fresh
    except Exception:
        return page


def goto_retry(page: Page, url: str, *, timeout: int = 70000, attempts: int = 3) -> None:
    """Navigate with backoff on LinkedIn HTTP throttle / transient failures."""
    last: Exception | None = None
    want_linkedin = "linkedin.com" in (url or "").lower()
    for i in range(attempts):
        try:
            if want_linkedin:
                u0 = ""
                try:
                    u0 = (page.url or "").lower()
                except Exception:
                    u0 = ""
                if u0 and "linkedin.com" not in u0:
                    try:
                        page.goto("about:blank", wait_until="domcontentloaded", timeout=15000)
                    except Exception:
                        pass
            page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            # Soft throttle signal in URL/title
            u = (page.url or "").lower()
            if want_linkedin and "linkedin.com" not in u:
                raise RuntimeError(f"goto_swallowed expected linkedin got {page.url}")
            if any(x in u for x in ("/authwall", "/checkpoint/challenge", "unavailable")):
                time.sleep(2.5 + i * 2.0)
            return
        except Exception as e:
            last = e
            msg = str(e)
            if (
                "ERR_HTTP_RESPONSE_CODE_FAILURE" in msg
                or "Timeout" in msg
                or "net::ERR_" in msg
                or "goto_swallowed" in msg
            ):
                time.sleep(3.0 + i * 3.5)
                continue
            raise
    assert last is not None
    raise last


def dismiss(page: Page) -> None:
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


def company_jobs_url(slug: str, title: str) -> str:
    return (
        f"https://www.linkedin.com/company/{slug}/jobs/"
        f"?keywords={quote(title)}&location={quote('Hyderabad')}"
    )


def extract_job_ids(page: Page) -> list[str]:
    try:
        html = page.content()
    except Exception:
        html = ""
    ids = []
    seen = set()
    for m in re.finditer(r"(?:jobPosting:|/jobs/view/|currentJobId=)(\d{6,})", html):
        jid = m.group(1)
        if jid not in seen:
            seen.add(jid)
            ids.append(jid)
    return ids[:MAX_SCAN]


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
            (r"email", "rafi.success@gmail.com"),
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
    row["atsUrl"] = ats.url
    ats_hint = url_loc_hint(ats.url or "")
    if not card_location_ok("", ats_hint):
        row["status"] = "skipped"
        row["reason"] = "ats_url_location"
        if ats != page:
            try:
                ats.close()
            except Exception:
                pass
        else:
            try:
                page.goto("about:blank", wait_until="domcontentloaded", timeout=15000)
            except Exception:
                pass
        return row
    status, reason = attempt_ats_apply(ats, time_cap_s=EXT_ATS_TIME_CAP_S)
    row["status"] = status
    row["reason"] = reason
    row["atsUrl"] = ats.url
    if ats != page:
        try:
            ats.close()
        except Exception:
            pass
    else:
        # Same-tab ATS (Workday) — blank so later LinkedIn searches are not swallowed.
        try:
            page.goto("about:blank", wait_until="domcontentloaded", timeout=15000)
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
                more.click(timeout=1500)
                time.sleep(0.5)
            connect = page.get_by_role("button", name=re.compile(r"Connect", re.I)).first
        if not (connect.count() and connect.is_visible()):
            row["status"] = "skipped"
            row["reason"] = "no_connect_cta"
            return row
        connect.click(timeout=2500)
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

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45000)

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
            page = ensure_linkedin_page(page)

            job_ids: list[str] = []
            for title in TITLES[:5]:
                if len(job_ids) >= MAX_SCAN:
                    break
                url = company_jobs_url(slug, title)
                print(f"LI COMPANY JOBS {name} | {title}", flush=True)
                page = ensure_linkedin_page(page, url)
                try:
                    goto_retry(page, url, timeout=70000)
                except Exception as e:
                    print(f"LI SEARCH NAV FAIL {name} | {title} | {e}", flush=True)
                    report.blocked.append({"company": name, "title": title, "reason": f"search_nav:{e}"})
                    page = ensure_linkedin_page(page)
                    continue
                time.sleep(2.5)
                dismiss(page)
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
                if not title_matches_senior_stack(role):
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

                if ext_walls >= MAX_EXT_WALLS_PER_COMPANY or ext_attempts >= MAX_EXT_ATTEMPTS_PER_COMPANY:
                    reason_cap = (
                        "ext_wall_cap"
                        if ext_walls >= MAX_EXT_WALLS_PER_COMPANY
                        else "ext_attempt_cap"
                    )
                    print(
                        f"LI SKIP {reason_cap} | {company_found} | {role[:50]} | {jid}",
                        flush=True,
                    )
                    report.skipped.append(
                        {
                            "company": company_found,
                            "role": role,
                            "job_id": jid,
                            "reason": reason_cap,
                            "location": loc,
                        }
                    )
                    continue

                print(f"LI EXT {company_found} | {role} | {jid}", flush=True)
                ext_attempts += 1
                ext = follow_external(page, meta)
                page = ensure_linkedin_page(page)
                ext["campusCompany"] = name
                ext["location"] = loc
                if ext["status"] == "applied":
                    report.external.append(ext)
                    report.applied.append(ext)
                    applied += 1
                    if referrals < MAX_REFERRALS:
                        ref = referral_people_search(page, company_found or name, role)
                        report.referrals.append(ref)
                        if ref.get("status") == "sent":
                            referrals += 1
                elif ext["status"] == "skipped":
                    report.skipped.append(ext)
                else:
                    report.blocked.append(ext)
                    why = (ext.get("reason") or "").lower()
                    if (
                        "captcha" in why
                        or "login" in why
                        or "account wall" in why
                        or "incomplete" in why
                        or "time_cap" in why
                        or "stuck" in why
                    ):
                        ext_walls += 1
                        print(
                            f"LI EXT WALL {company_found} walls={ext_walls}/{MAX_EXT_WALLS_PER_COMPANY} "
                            f"attempts={ext_attempts}/{MAX_EXT_ATTEMPTS_PER_COMPANY} | {why}",
                            flush=True,
                        )

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
