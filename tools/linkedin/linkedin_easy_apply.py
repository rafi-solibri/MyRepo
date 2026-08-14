#!/usr/bin/env python3
"""LinkedIn Easy Apply batch for Rafi Ahmed — Hyderabad / Remote India only."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

try:
    from tools.linkedin.filters import (
        TITLE_BLACKLIST,
        JD_HARD_BLACKLIST,
        BLACKLIST,
        TITLE_OK,
        HYD_OK,
        REMOTE_OK,
        INDIA_ONLY,
        BAD_CITY,
        location_allowed,
        jd_blacklist,
        skip_reason,
    )
except Exception:
    from filters import (  # type: ignore
        TITLE_BLACKLIST,
        JD_HARD_BLACKLIST,
        BLACKLIST,
        TITLE_OK,
        HYD_OK,
        REMOTE_OK,
        INDIA_ONLY,
        BAD_CITY,
        location_allowed,
        jd_blacklist,
        skip_reason,
    )

CDP = os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
_ROOT = Path(__file__).resolve().parents[2]


def _artifacts_dir() -> Path:
    if os.environ.get("LINKEDIN_ARTIFACTS"):
        return Path(os.environ["LINKEDIN_ARTIFACTS"])
    # Windows: Git Bash `/opt/cursor` ≠ Python `C:\opt\cursor`. Prefer repo artifacts.
    if (
        os.name == "nt"
        or os.environ.get("OS") == "Windows_NT"
        or bool(os.environ.get("MSYSTEM"))
    ):
        d = _ROOT / "artifacts"
        d.mkdir(parents=True, exist_ok=True)
        return d
    cloud = Path("/opt/cursor/artifacts")
    if cloud.is_dir():
        return cloud
    d = _ROOT / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


_ART = _artifacts_dir()
OUT = Path(os.environ.get("LINKEDIN_APPLY_REPORT", str(_ART / "apply-report.json")))
SCREEN_DIR = _ART
RESUME_LABEL = "Rafi_Resume"

# Ensure resume exists before apply batch
try:
    import sys
    from pathlib import Path as _P
    _root = _P(__file__).resolve().parents[2]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))
    from tools.resume_paths import ensure_resume_aliases, RESUME_LABEL as _RL
    ensure_resume_aliases()
    RESUME_LABEL = _RL
except Exception as _e:
    print("resume bootstrap warning:", _e)

PROFILE = {
    "phone": "8790251698",
    "email": "rafi.success@gmail.com",
    "linkedin": "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "current_ctc_lakhs": "52",
    "expected_ctc_lakhs": "65",
    "notice": "0",
    "experience_years": "15",
    "engineers_managed": "8",
    "dob_day": "16",
    "dob_month": "January",
    "dob_month_num": "01",
    "dob_year": "1989",
    "city": "Hyderabad",
    "country": "India",
    "education_school": "Acharya Nagarjuna University",
    "education_degree": "B.Tech",
    "education_field": "Information Technology",
    "edu_start_month": "July",
    "edu_start_year": "2006",
    "edu_end_month": "May",
    "edu_end_year": "2010",
    "employer": "Nemetschek",
    "title": "Principal Analyst",
}

TITLES = [
    "Solution Architect",
    "Technical Architect",
    "Software Architect",
    "Technical Lead",
    "Engineering Manager",
    "Principal .NET",
    "Staff .NET",
    ".NET Architect",
    "Azure Architect",
    "Cloud Architect",
]

MAX_APPLY = int(os.environ.get("LINKEDIN_MAX_APPLY", "50"))
MAX_SCAN_PER_SEARCH = int(os.environ.get("LINKEDIN_MAX_SCAN", "60"))
# Past 24h, then 3 days, then 7 days, then 14 days (thin-inventory expand)
TPR_WINDOWS = ("r86400", "r259200", "r604800", "r1209600")
# After Easy Apply pass, also search without f_AL so company-site / Apply jobs are visible.
EASY_APPLY_ONLY = os.environ.get("LINKEDIN_EASY_APPLY_ONLY", "0") == "1"
NON_EA_IF_BELOW = int(os.environ.get("LINKEDIN_NON_EA_IF_BELOW", "20"))
SEEN_IDS_PATH = Path(
    os.environ.get(
        "LINKEDIN_SEEN_IDS_PATH",
        "/opt/cursor/artifacts/linkedin-seen-ids.json",
    )
)


@dataclass
class JobResult:
    status: str
    company: str = ""
    role: str = ""
    job_id: str = ""
    location: str = ""
    reason: str = ""
    url: str = ""
    path: str = ""  # Easy Apply | company/ATS URL


def shot(page: Page, name: str) -> None:
    try:
        page.screenshot(path=str(SCREEN_DIR / name), full_page=False)
    except Exception:
        pass


def close_overlays(page: Page, *, keep_easy_apply: bool = True) -> None:
    # Discard "Save this application?" only if Easy Apply is NOT the active intent
    try:
        save_dlg = page.get_by_text("Save this application?")
        if save_dlg.count() and save_dlg.first.is_visible():
            # Prefer continuing apply: press Escape won't help — click Discard then reopen later
            d = page.get_by_role("button", name="Discard")
            if d.count() and d.first.is_visible():
                d.first.click(timeout=1500)
                time.sleep(0.4)
    except Exception:
        pass

    # Close "New message" compose modal (not Easy Apply)
    try:
        new_msg = page.locator(
            ".msg-overlay-conversation-bubble--is-active, "
            ".msg-form, div[aria-label='New message'], "
            ".msg-overlay-bubble-header:has-text('New message')"
        )
        if page.get_by_text("New message", exact=True).count():
            for sel in [
                "button[aria-label='Close your conversation with']",
                "button[data-test-modal-close-btn]",
                ".msg-overlay-bubble-header__control",
            ]:
                try:
                    b = page.locator(sel).first
                    if b.is_visible():
                        b.click(timeout=1000)
                        time.sleep(0.3)
                except Exception:
                    pass
            # X on new message
            try:
                page.locator(".msg-overlay-bubble-header").filter(has_text="New message").locator("button").first.click(timeout=1000)
            except Exception:
                pass
    except Exception:
        pass

    # Collapse messaging list
    try:
        for sel in [
            "button.msg-overlay-bubble-header__control--close",
            "button[aria-label*='Close your conversation']",
            "button[aria-label='Minimize compose form']",
        ]:
            for b in page.locator(sel).all()[:4]:
                try:
                    if b.is_visible():
                        b.click(timeout=800)
                        time.sleep(0.2)
                except Exception:
                    pass
        # Click Messaging header to collapse if expanded
        msg = page.locator(".msg-overlay-list-bubble").first
        if msg.count() and msg.is_visible():
            # if it's tall/open, click header
            hdr = page.locator(".msg-overlay-list-bubble .msg-overlay-bubble-header").first
            if hdr.count() and hdr.is_visible():
                box = msg.bounding_box()
                if box and box.get("height", 0) > 200:
                    hdr.click(timeout=1000)
    except Exception:
        pass

    # Close non-apply artdeco modals (not Easy Apply)
    if not keep_easy_apply:
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

    # Do NOT press Escape here — it dismisses Easy Apply when Simplify sidebar is open.


def ensure_english_ui(page: Page) -> None:
    """Force LinkedIn English so location/title filters stay reliable."""
    try:
        page.goto(
            "https://www.linkedin.com/mypreferences/d/language/",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(2)
        # Prefer select/dropdown for English
        for sel in [
            "select",
            "button:has-text('English')",
            "div[role='combobox']",
        ]:
            try:
                el = page.locator(sel).first
                if el.count() and el.is_visible():
                    tag = el.evaluate("e => e.tagName.toLowerCase()")
                    if tag == "select":
                        try:
                            el.select_option(label=re.compile(r"English", re.I))
                        except Exception:
                            el.select_option(value="en_US")
                        time.sleep(1)
                        break
            except Exception:
                pass
        # Cookie / lang query fallback
        page.context.add_cookies(
            [
                {
                    "name": "lang",
                    "value": "v=2&lang=en-us",
                    "domain": ".linkedin.com",
                    "path": "/",
                }
            ]
        )
    except Exception as e:
        print("ensure_english_ui warning:", e, flush=True)
    try:
        page.goto(
            "https://www.linkedin.com/feed/?locale=en_US",
            wait_until="domcontentloaded",
            timeout=45000,
        )
        time.sleep(1.5)
    except Exception:
        pass


def search_url(
    keywords: str, location: str, remote: bool = False, tpr: str = "r86400", easy_apply: bool = True
) -> str:
    # sortBy=DD latest; f_AL Easy Apply; f_TPR recency window
    geo = quote(location)
    kw = quote(keywords)
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={kw}"
        f"&location={geo}&sortBy=DD&f_TPR={tpr}"
    )
    if easy_apply:
        url += "&f_AL=true"
    if remote:
        url += "&f_WT=2"  # remote workplace type
    return url


def extract_job_id(url: str) -> str:
    m = re.search(r"currentJobId=(\d+)", url) or re.search(r"/jobs/view/(\d+)", url)
    return m.group(1) if m else ""


def _is_ai_job_search(page: Page) -> bool:
    u = page.url or ""
    return "search-results" in u or "ai-job-search" in u


def ai_job_card_buttons(page: Page):
    """LinkedIn AI job search cards: div[role=button] inside data-display-contents wrappers."""
    return page.locator(
        'div[data-display-contents="true"] div[role="button"]'
    ).filter(
        has_text=re.compile(
            r"(Easy Apply|Applied|ago|Remote|Hybrid|On-site|Hyderabad|India|WFH)",
            re.I,
        )
    )


def detail_panel_text(page: Page) -> str:
    """Top-card / detail pane text only — never full page chrome (filters say Remote)."""
    try:
        title_a = page.locator('a[href*="/jobs/view/"]').first
        if title_a.count():
            # Climb to a bounded detail root around the selected job title.
            txt = title_a.evaluate(
                """(a) => {
                  let el = a;
                  for (let i = 0; i < 10 && el; i++) {
                    const t = (el.innerText || '').trim();
                    if (t.length > 80 && t.length < 4000 &&
                        /Easy Apply|Apply|About the job|Hybrid|Remote|On-site/i.test(t)) {
                      return t.slice(0, 3500);
                    }
                    el = el.parentElement;
                  }
                  return (a.innerText || '').slice(0, 500);
                }"""
            )
            if txt:
                return txt
    except Exception:
        pass
    # Classic fallbacks
    for sel in [
        ".job-details-jobs-unified-top-card__container",
        ".jobs-unified-top-card",
        ".job-details-jobs-unified-top-card",
        ".jobs-details",
        ".scaffold-layout__detail",
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count():
                t = (loc.inner_text(timeout=1500) or "")[:3500]
                if t.strip():
                    return t
        except Exception:
            continue
    return ""


def top_card_workplace_text(page: Page, card_text: str = "") -> str:
    """Location/workplace signal from top card only (strip people/JD chrome)."""
    detail = detail_panel_text(page)
    # Cut before sections that often mention other cities (network, JD body)
    cut = re.split(
        r"\n\s*(?:People you can reach out to|Meet the hiring team|About the job|Show match details|BETA)\b",
        detail,
        maxsplit=1,
        flags=re.I,
    )[0]
    # Keep a short head: title, company, location line, workplace pills
    head = "\n".join(cut.splitlines()[:18])[:700]
    if card_text:
        # Card line like "Hyderabad (On-site)" is the most reliable AI-UI signal
        head = f"{card_text[:400]}\n{head}"
    return head[:900]


def fill_apply_radios_and_selects(page: Page) -> None:
    """Fill Yes/No radio groups + proficiency selects on classic modal OR new Apply page."""
    try:
        page.evaluate(
            r"""() => {
              const heading = [...document.querySelectorAll('h1,h2,h3')]
                .find(e => /Apply to /i.test(e.innerText || ''));
              let root = heading;
              for (let i = 0; i < 12 && root; i++) {
                if (root.querySelectorAll('input[type=radio], select').length > 0) break;
                root = root.parentElement;
              }
              root = root || document;
              const questionNear = (el) => {
                let cur = el;
                for (let i = 0; i < 8 && cur; i++) {
                  const t = (cur.innerText || '').replace(/\s+/g, ' ').trim();
                  if (t.length > 12 && t.length < 500 &&
                      !/^(Yes|No)(\s+(Yes|No))?$/i.test(t)) {
                    return t;
                  }
                  // Prefer previous sibling blocks for question text
                  let sib = cur.previousElementSibling;
                  while (sib) {
                    const st = (sib.innerText || '').replace(/\s+/g, ' ').trim();
                    if (st.length > 12 && st.length < 400 &&
                        !/^(Yes|No)$/i.test(st) &&
                        !/this field is required/i.test(st)) {
                      return st;
                    }
                    sib = sib.previousElementSibling;
                  }
                  cur = cur.parentElement;
                }
                return '';
              };
              // Group radios by name
              const radios = [...root.querySelectorAll('input[type=radio]')];
              const byName = new Map();
              for (const r of radios) {
                const n = r.name || r.id || Math.random().toString();
                if (!byName.has(n)) byName.set(n, []);
                byName.get(n).push(r);
              }
              for (const group of byName.values()) {
                if (group.some(r => r.checked)) continue;
                const q = questionNear(group[0]).toLowerCase();
                let wantYes = true;
                if (/sponsorship|visa sponsorship|require sponsorship|need sponsorship/.test(q)) {
                  wantYes = false;
                }
                // Map Yes/No via adjacent label text or following text
                const pick = group.find(r => {
                  const lab = (r.labels && r.labels[0] && r.labels[0].innerText || '').trim().toLowerCase();
                  const wrap = (r.closest('label') || r.parentElement);
                  const wt = (wrap && wrap.innerText || '').trim().toLowerCase();
                  const marker = lab || wt || '';
                  return wantYes ? /^yes\b/.test(marker) : /^no\b/.test(marker);
                }) || (wantYes ? group[0] : group[group.length - 1]);
                try {
                  pick.click();
                  pick.checked = true;
                  pick.dispatchEvent(new Event('input', {bubbles: true}));
                  pick.dispatchEvent(new Event('change', {bubbles: true}));
                } catch (e) {}
              }
              // Selects: country code, English proficiency, Yes/No, etc.
              for (const s of root.querySelectorAll('select')) {
                const lab = (s.labels && s.labels[0] && s.labels[0].innerText || '') + ' ' + questionNear(s);
                const blob = lab.toLowerCase();
                const cur = (s.options[s.selectedIndex] && s.options[s.selectedIndex].text || '').trim();
                let opt = null;
                if (/country code|phone country|dial/.test(blob) ||
                    /\(\+91\)|\(\+376\)|\(\+1\)/.test([...s.options].slice(0,8).map(o=>o.text).join(' '))) {
                  // Always prefer India (+91) when this looks like a phone country list
                  const looksPhone = [...s.options].some(o => /\(\+\d+\)/.test(o.text));
                  if (looksPhone || /country code|phone country/.test(blob)) {
                    opt = [...s.options].find(o => /india\s*\(\+91\)/i.test(o.text)) ||
                          [...s.options].find(o => /\+91/.test(o.text));
                  }
                }
                if (!opt && (/english|proficiency|language/.test(blob))) {
                  if (/select/i.test(cur) || !s.value) {
                    opt = [...s.options].find(o => /professional|native|bilingual/i.test(o.text));
                  }
                }
                if (!opt && (/notice|availability/.test(blob)) && (/select/i.test(cur) || !s.value)) {
                  opt = [...s.options].find(o => /^0$|immediate|immediately|yes/i.test(o.text.trim()));
                }
                if (!opt && (/select/i.test(cur) || !s.value)) {
                  opt = [...s.options].find(o => /^yes$/i.test(o.text.trim()));
                }
                // Force-correct wrong country codes even if already selected
                if (!opt && /country code|phone country/.test(blob)) {
                  opt = [...s.options].find(o => /india\s*\(\+91\)/i.test(o.text));
                }
                if (opt && s.value !== opt.value) {
                  s.value = opt.value;
                  s.dispatchEvent(new Event('input', {bubbles: true}));
                  s.dispatchEvent(new Event('change', {bubbles: true}));
                }
              }
            }"""
        )
    except Exception:
        pass
    # Also click visible Yes/No text next to unanswered required questions (AI UI)
    try:
        for qpat, answer in [
            (r"background check", "Yes"),
            (r"bachelor.?s degree|level of education", "Yes"),
            (r"comfortable commuting", "Yes"),
            (r"hybrid setting", "Yes"),
            (r"legally authorized to work", "Yes"),
            (r"require sponsorship|visa sponsorship", "No"),
            (r"willing to relocate", "Yes"),
            (r"hyderabad", "Yes"),
            (r"work model|5 days a week|office \d+ days", "Yes"),
            (r"start immediately|fill this position urgently", "Yes"),
            (r"on-?site|work from (our|the) .* office", "Yes"),
        ]:
            q = page.get_by_text(re.compile(qpat, re.I)).first
            if not (q.count() and q.is_visible()):
                continue
            # Scope to a nearby container that includes Yes/No
            box = q.locator(
                "xpath=ancestor::div[.//text()[normalize-space()='Yes'] and "
                ".//text()[normalize-space()='No']][1]"
            )
            if not box.count():
                box = q.locator("xpath=ancestor::div[3]")
            try:
                # Prefer associated radio input
                lab = box.locator(f"label:has-text('{answer}')").first
                if lab.count() and lab.is_visible():
                    lab.click(timeout=800, force=True)
                    continue
            except Exception:
                pass
            try:
                box.get_by_text(answer, exact=True).first.click(timeout=800, force=True)
            except Exception:
                pass
        # English proficiency
        sel = page.locator("select").filter(
            has=page.locator("option:has-text('Professional')")
        ).first
        if sel.count():
            try:
                sel.select_option(label=re.compile(r"Professional|Native", re.I))
            except Exception:
                pass
    except Exception:
        pass


def fill_inputs(page: Page) -> None:
    """Best-effort fill of Easy Apply form fields."""
    # Radios/selects first — new Apply UI often has unlabeled radio groups
    fill_apply_radios_and_selects(page)

    # Text/select/textarea with labels (modal OR new full-page Apply UI)
    labels = page.locator(
        ".jobs-easy-apply-modal label, .jobs-easy-apply-content label, "
        "[role='dialog'] label, .artdeco-modal label, form label"
    )
    # If classic scopes empty, use any visible labels under Apply heading root
    try:
        if labels.count() == 0 and page.get_by_role(
            "heading", name=re.compile(r"Apply to ", re.I)
        ).count():
            labels = page.locator("label")
    except Exception:
        pass
    try:
        count = min(labels.count(), 40)
    except Exception:
        count = 0
    for i in range(count):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=500) or "").strip().lower()
        except Exception:
            continue
        if not text:
            continue
        # Find associated control
        control = None
        try:
            for_id = lab.get_attribute("for")
            if for_id:
                # IDs often contain ':', '(', ')' — use attribute selector, not #id
                control = page.locator(f'[id="{for_id}"]').first
            else:
                control = lab.locator(
                    "xpath=following::*[self::input or self::select or self::textarea][1]"
                ).first
        except Exception:
            continue
        try:
            if not control or control.count() == 0:
                continue
        except Exception:
            continue
        try:
            tag = control.evaluate("e => e.tagName.toLowerCase()")
            itype = (control.get_attribute("type") or "").lower()
            if itype == "file":
                continue
            name = (control.get_attribute("name") or "").lower()
            aria = (control.get_attribute("aria-label") or "").lower()
            blob = f"{text} {name} {aria}"
        except Exception:
            continue

        def set_val(v: str) -> None:
            try:
                if tag == "select":
                    control.select_option(label=v)
                else:
                    control.fill(v)
            except Exception:
                try:
                    control.click()
                    control.fill(v)
                except Exception:
                    pass

        if any(k in blob for k in ("phone", "mobile", "contact number")) and "country" not in blob:
            set_val(PROFILE["phone"])
        elif "email" in blob and tag == "select":
            try:
                control.select_option(label=re.compile(r"rafi\.success@gmail\.com", re.I))
            except Exception:
                pass
        elif "email" in blob:
            set_val(PROFILE["email"])
        elif any(k in blob for k in ("linkedin profile", "linkedin url", "profile url", "linkedin.com")):
            set_val(PROFILE["linkedin"])
        elif any(
            k in blob
            for k in (
                "institution",
                "university",
                "college",
                "bachelor's degree from",
                "bachelors degree from",
                "school name",
                "where did you study",
            )
        ):
            set_val(PROFILE["education_school"])
        elif any(
            k in blob
            for k in (
                "specialization",
                "field of study",
                "major",
                "discipline",
                "branch of engineering",
            )
        ):
            set_val(PROFILE["education_field"])
        elif any(
            k in blob
            for k in (
                "engineers do you currently manage",
                "engineers managed",
                "direct reports",
                "team size",
                "people managed",
                "manage directly",
            )
        ):
            set_val(PROFILE["engineers_managed"])
        elif "country code" in blob or ( "phone" in blob and "country" in blob):
            try:
                control.select_option(label=re.compile(r"India \(\+91\)", re.I))
            except Exception:
                try:
                    control.select_option(label=re.compile(r"india|\+91", re.I))
                except Exception:
                    pass
        elif any(
            k in blob
            for k in (
                "current ctc",
                "current salary",
                "current annual salary",
                "current compensation",
                "present ctc",
                "confirm your current ctc",
                "annual salary",
                "fixed ctc",
                "salary(fixed)",
                "salary (fixed)",
            )
        ):
            # Forms often ask Lakhs
            if "lakh" in blob:
                set_val(PROFILE["current_ctc_lakhs"])
            else:
                set_val(PROFILE["current_ctc"])
        elif any(
            k in blob
            for k in (
                "expected ctc",
                "expected salary",
                "expected annual salary",
                "expected compensation",
                "desired salary",
                "expected fixed",
            )
        ):
            if "lakh" in blob:
                set_val(PROFILE["expected_ctc_lakhs"])
            else:
                set_val(PROFILE["expected_ctc"])
        elif "notice" in blob:
            # Some forms reject 0 ("larger than 0.0") — use 1 day when numeric
            set_val("1" if tag != "select" else PROFILE["notice"])
        elif any(k in blob for k in ("years of experience", "total experience", "how many years", "years of work experience")):
            set_val(PROFILE["experience_years"])
        elif "hyderabad" in blob and tag == "select":
            try:
                control.select_option(label=re.compile(r"^yes$", re.I))
            except Exception:
                pass
        elif tag == "select":
            # Generic Yes for experience / belong questions
            try:
                opts = control.locator("option").all_inner_texts()
                texts = [o.strip() for o in opts]
                if any(t.lower() == "yes" for t in texts) and any(
                    k in blob
                    for k in (
                        "experience",
                        "worked",
                        "belong",
                        "willing",
                        "relocate",
                        "authorize",
                        "available",
                        "presales",
                        "government",
                        "hyderabad",
                    )
                ):
                    control.select_option(label=re.compile(r"^yes$", re.I))
            except Exception:
                pass
        elif "date of birth" in blob or blob.strip() == "dob" or "birth" in blob:
            if "day" in blob:
                set_val(PROFILE["dob_day"])
            elif "month" in blob:
                set_val(PROFILE["dob_month"])
            elif "year" in blob:
                set_val(PROFILE["dob_year"])
            else:
                set_val("16/01/1989")
        elif "city" in blob and "company" not in blob:
            set_val(PROFILE["city"])
        elif "country" in blob and "code" not in blob:
            try:
                control.select_option(label="India")
            except Exception:
                set_val("India")

    # Artdeco / custom dropdowns showing "Select an option"
    try:
        triggers = page.locator("button:has-text('Select an option')")
        for i in range(min(triggers.count(), 6)):
            t = triggers.nth(i)
            if not t.is_visible():
                continue
            t.click(timeout=2000)
            time.sleep(0.35)
            yes = page.locator(
                "[role='listbox'] [role='option']:has-text('Yes'), "
                ".artdeco-dropdown__content [role='option']:has-text('Yes'), "
                "div.artdeco-dropdown__item:has-text('Yes')"
            ).first
            if yes.count() and yes.is_visible():
                yes.click(timeout=2000)
            else:
                opt = page.locator("[role='listbox'] [role='option']").nth(1)
                if opt.count():
                    opt.click(timeout=2000)
            time.sleep(0.3)
    except Exception:
        pass

    # Native selects still on Select an option — Playwright select_option is more
    # reliable than dispatching change events for LinkedIn Easy Apply validation.
    try:
        form = apply_form_root(page)
        for sel in form.locator("select").all()[:12]:
            try:
                if not sel.is_visible():
                    continue
                opts = [
                    re.sub(r"\s+", " ", (t or "")).strip()
                    for t in sel.locator("option").all_inner_texts()
                ]
                lower = [o.lower() for o in opts]
                cur = ""
                try:
                    cur = (sel.evaluate("s => (s.options[s.selectedIndex]?.text || '')") or "").strip()
                except Exception:
                    cur = ""
                # Yes/No additional questions (not email/country lists)
                if "yes" in lower and "no" in lower and len(opts) <= 5:
                    if not cur or re.search(r"select", cur, re.I):
                        try:
                            sel.select_option(label=re.compile(r"^\s*Yes\s*$", re.I))
                        except Exception:
                            try:
                                sel.select_option(value="Yes")
                            except Exception:
                                sel.evaluate(
                                    """s => {
                                      const yes=[...s.options].find(o=>/^yes$/i.test((o.text||'').trim()));
                                      if(!yes) return;
                                      s.selectedIndex=[...s.options].indexOf(yes);
                                      s.value=yes.value;
                                      s.dispatchEvent(new Event('input',{bubbles:true}));
                                      s.dispatchEvent(new Event('change',{bubbles:true}));
                                    }"""
                                )
                    continue
                # Email select → profile email
                if any("rafi.success@gmail.com" in o.lower() for o in opts):
                    if not cur or re.search(r"select", cur, re.I):
                        sel.select_option(label=re.compile(r"rafi\.success@gmail\.com", re.I))
                    continue
                # Phone country → India (+91)
                if any(re.search(r"\(\+\d+\)", o) for o in opts):
                    if not cur or re.search(r"select|andorra|\+376", cur, re.I):
                        try:
                            sel.select_option(label=re.compile(r"India\s*\(\+91\)", re.I))
                        except Exception:
                            pass
            except Exception:
                continue
    except Exception:
        pass

    # Also fill unlabeled / aria-label / near-text inputs (Greenhouse Easy Apply)
    try:
        for inp in page.locator(
            "input[type='text'], input:not([type]), textarea, input[type='url'], input[type='number']"
        ).all()[:40]:
            try:
                if not inp.is_visible():
                    continue
                val = inp.input_value()
                if val:
                    continue
                near = inp.evaluate(
                    """e => {
                      const aria = e.getAttribute('aria-label') || '';
                      const ph = e.getAttribute('placeholder') || '';
                      const lab = e.labels && e.labels[0] ? e.labels[0].innerText : '';
                      const wrap = (e.closest('fieldset, .fb-dash-form-element, .jobs-easy-apply-form-element, div') || e.parentElement);
                      const t = (wrap && wrap.innerText) ? wrap.innerText.slice(0, 220) : '';
                      return (aria + ' ' + ph + ' ' + lab + ' ' + t).toLowerCase();
                    }"""
                )
                if re.search(r"linkedin|profile url", near):
                    inp.fill(PROFILE["linkedin"])
                elif re.search(r"institution|university|college|bachelor.?s degree from|school name", near):
                    inp.fill(PROFILE["education_school"])
                elif re.search(r"specialization|field of study|major|discipline", near):
                    inp.fill(PROFILE["education_field"])
                elif re.search(r"manage directly|engineers managed|direct reports|team size|people managed", near):
                    inp.fill(PROFILE["engineers_managed"])
                elif re.search(r"(current|present).*(ctc|salary)|annual salary|salary\s*\(?fixed\)?", near) and "expect" not in near:
                    inp.fill(PROFILE["current_ctc_lakhs"] if "lakh" in near else PROFILE["current_ctc"])
                elif re.search(r"(expected|desired).*(ctc|salary)|expected annual", near):
                    inp.fill(PROFILE["expected_ctc_lakhs"] if "lakh" in near else PROFILE["expected_ctc"])
                elif "ctc" in near and "lakh" in near and "current" in near:
                    inp.fill(PROFILE["current_ctc_lakhs"])
                elif "ctc" in near and "lakh" in near and "expect" in near:
                    inp.fill(PROFILE["expected_ctc_lakhs"])
                elif "lakh" in near and "salary" in near and "expect" not in near:
                    inp.fill(PROFILE["current_ctc_lakhs"])
                elif "notice" in near:
                    inp.fill("1")
                elif ("years" in near or "experience" in near) and "php" not in near:
                    inp.fill("15")
                elif re.search(r"\bphone\b|\bmobile\b", near) and "country" not in near:
                    inp.fill(PROFILE["phone"])
                elif "email" in near:
                    inp.fill(PROFILE["email"])
            except Exception:
                pass
    except Exception:
        pass

    # Multi-select checkboxes (Turing/Greenhouse role & responsibility groups)
    checkbox_picks = [
        (r"best describes your current role", ["Principal Engineer", "Technical Lead", "Engineering Manager"]),
        (
            r"part of your current responsibilities",
            [
                "Technical Roadmap",
                "Architecture Reviews",
                "System Design",
                "Mentoring Engineers",
                "Hiring",
            ],
        ),
        (
            r"areas have you worked on extensively",
            [
                "Backend Engineering",
                "Platform Engineering",
                "Distributed Systems",
                "Cloud Infrastructure",
                "Event-driven Systems",
            ],
        ),
    ]
    for qpat, choices in checkbox_picks:
        try:
            q = page.get_by_text(re.compile(qpat, re.I)).first
            if not (q.count() and q.is_visible()):
                continue
            container = q.locator(
                "xpath=ancestor::fieldset|ancestor::div[contains(@class,'fb-dash') or contains(@class,'jobs-easy-apply')][1]"
            )
            if not container.count():
                container = q.locator("xpath=ancestor::div[1]")
            for choice in choices:
                try:
                    opt = container.get_by_label(choice, exact=False)
                    if opt.count():
                        el = opt.first
                        try:
                            if not el.is_checked():
                                el.check(force=True)
                        except Exception:
                            el.click(timeout=800, force=True)
                        continue
                    txt = container.get_by_text(choice, exact=True).first
                    if txt.count() and txt.is_visible():
                        txt.click(timeout=800, force=True)
                except Exception:
                    continue
        except Exception:
            pass

    # Radio / yes-no common
    for pair in [
        (r"authorized|work authorization|legally", "Yes"),
        (r"require sponsorship|visa sponsorship", "No"),
        (r"willing to relocate", "Yes"),
        (r"immediate join|available to join", "Yes"),
        (r"hyderabad", "Yes"),
        (r"presales", "Yes"),
        (r"government|psu|smart cities", "Yes"),
        (r"background check", "Yes"),
        (r"bachelor.?s degree|level of education", "Yes"),
        (r"comfortable commuting", "Yes"),
        (r"hybrid setting", "Yes"),
    ]:
        try:
            q = page.get_by_text(re.compile(pair[0], re.I)).first
            if q.count() and q.is_visible():
                container = q.locator(
                    "xpath=ancestor::fieldset|ancestor::div[contains(@class,'fb-dash') or contains(@class,'jobs-easy-apply')][1]"
                )
                if not container.count():
                    container = q.locator(
                        "xpath=ancestor::div[.//input[@type='radio'] or .//select][1]"
                    )
                # native select nearby
                sel = container.locator("select").first
                if sel.count():
                    try:
                        sel.select_option(label=re.compile(rf"^{pair[1]}$", re.I))
                        continue
                    except Exception:
                        pass
                btn = container.get_by_label(pair[1], exact=True)
                if btn.count():
                    btn.first.click(timeout=1000)
                else:
                    container.get_by_text(pair[1], exact=True).first.click(timeout=1000)
        except Exception:
            pass

    # New LinkedIn Apply page: unlabeled radio groups + proficiency selects
    fill_apply_radios_and_selects(page)


def select_resume(page: Page) -> None:
    try:
        # Click card/label containing resume name
        cand = page.get_by_text(re.compile(r"Rafi_Resume(?:_Architect)?|Rafi_Resume\.docx|Architect\.docx|Rafi.*Architect", re.I))
        if cand.count():
            cand.first.click(timeout=2000)
            return
        # radio near Documents
        radios = page.locator("input[type='radio'][name*='resume'], input[type='radio'][name*='document']")
        if radios.count():
            radios.first.check(force=True)
    except Exception:
        pass


def dismiss_apply_form(page: Page) -> None:
    """Close Easy Apply modal OR new inline Apply page; discard save prompt if shown."""
    for sel in [
        ".jobs-easy-apply-modal button.artdeco-modal__dismiss",
        "[role='dialog']:has-text('Apply to') button.artdeco-modal__dismiss",
        "button[aria-label='Dismiss']",
        "button[aria-label*='Dismiss']",
    ]:
        try:
            b = page.locator(sel).first
            if b.count() and b.is_visible():
                # Prefer dismiss near Apply heading
                b.click(timeout=1500)
                time.sleep(0.4)
                break
        except Exception:
            continue
    try:
        if page.get_by_text("Save this application?").count() and page.get_by_text(
            "Save this application?"
        ).first.is_visible():
            page.get_by_role("button", name="Discard").click(timeout=2000)
            time.sleep(0.3)
    except Exception:
        pass


def _application_submitted(page: Page) -> bool:
    """True when LinkedIn confirms the application (modal toast OR job detail status)."""
    try:
        detail = detail_panel_text(page)
    except Exception:
        detail = ""
    try:
        body = page.locator("body").inner_text()[:6000]
    except Exception:
        body = ""
    text = f"{detail}\n{body}"
    if re.search(
        r"application (was )?submitted|"
        r"application status\s*application submitted|"
        r"applied to .+ ago|\byou applied\b|"
        r"applied \d+ (second|minute|hour|day)s? ago|"
        r"\bapplication sent\b",
        text,
        re.I,
    ):
        # Avoid false positive from unrelated cards saying Applied
        if re.search(
            r"application (was )?submitted|application status|applied \d+ |"
            r"applied to |\byou applied\b|application sent",
            detail or body[:2500],
            re.I,
        ):
            return True
    # Detail pane status chip
    try:
        if page.get_by_text(re.compile(r"^Application submitted$", re.I)).count():
            return True
    except Exception:
        pass
    return False


def _easy_apply_modal_ancestor(heading_loc):
    """Full Easy Apply modal — never artdeco-modal__header (substring false match)."""
    # Token-match 'artdeco-modal' so artdeco-modal__header / __content are skipped.
    return heading_loc.locator(
        "xpath=ancestor::div["
        "@role='dialog' or "
        "contains(@class,'jobs-easy-apply-modal') or "
        "contains(@class,'easy-apply-modal') or "
        "contains(concat(' ', normalize-space(@class), ' '), ' artdeco-modal ')"
        "][1]"
    )


def apply_form_root(page: Page):
    """Locator for the active Easy Apply form (modal OR new inline Apply page)."""
    heading = page.get_by_role("heading", name=re.compile(r"Apply to ", re.I))
    try:
        if heading.count() and heading.first.is_visible():
            modal = _easy_apply_modal_ancestor(heading.first)
            if modal.count():
                return modal.first
            # Prefer smallest ancestor that contains Next/Review/Submit *with visible text*
            rooted = heading.first.locator(
                "xpath=ancestor::div[.//button[normalize-space()='Next' or normalize-space()='Review' "
                "or normalize-space()='Submit' or normalize-space()='Submit application' "
                "or normalize-space()='Continue']][1]"
            )
            if rooted.count():
                return rooted.first
            return heading.first.locator("xpath=ancestor::div[4]")
    except Exception:
        pass
    for sel in [
        ".jobs-easy-apply-modal",
        "[role='dialog']:has-text('Apply to')",
        "div.artdeco-modal:has-text('Apply to')",
    ]:
        loc = page.locator(sel).first
        try:
            if loc.count() and loc.is_visible():
                return loc
        except Exception:
            continue
    return page.locator("body")


def _apply_modal(page: Page):
    # New LinkedIn modals may lack .jobs-easy-apply-modal / role=dialog
    heading = page.get_by_role("heading", name=re.compile(r"Apply to ", re.I))
    try:
        if heading.count() and heading.first.is_visible():
            modal = _easy_apply_modal_ancestor(heading.first)
            if modal.count():
                return modal
            return heading.first.locator(
                "xpath=ancestor::div[.//button[normalize-space()='Next' or normalize-space()='Review' "
                "or normalize-space()='Submit' or normalize-space()='Submit application']][1]"
            )
    except Exception:
        pass
    for sel in [
        ".jobs-easy-apply-modal",
        "[role='dialog']:has-text('Apply to')",
        "div.artdeco-modal:has-text('Apply to')",
    ]:
        loc = page.locator(sel).first
        try:
            if loc.count() and loc.is_visible():
                return loc
        except Exception:
            continue
    return page.locator("[role='dialog']").first


def _easy_apply_daily_limit_hit(page: Page) -> bool:
    """Account cap — CTA still renders but LinkedIn shows a limit toast instead of the form."""
    try:
        body = (page.locator("body").inner_text(timeout=2000) or "")[:2500]
    except Exception:
        body = ""
    return bool(
        re.search(
            r"You reached today.?s Easy Apply limit|limit Easy Apply submissions|"
            r"continue applying tomorrow",
            body,
            re.I,
        )
    )


def _dismiss_easy_apply_limit_toast(page: Page) -> None:
    for sel in ("button:has-text('Got it')", "button:has-text('Got It')"):
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible():
                loc.click(timeout=1500)
                time.sleep(0.4)
                return
        except Exception:
            continue


def _easy_apply_cta(scope, page: Page):
    """2026 job view uses <a aria-label='Easy Apply to this job'>, not only buttons."""
    selectors = [
        "a[aria-label*='Easy Apply to this job']",
        "a[aria-label*='Easy Apply']",
        "button.jobs-apply-button",
        "button:has-text('Easy Apply')",
        "button[aria-label*='Easy Apply']",
    ]
    for root in (scope, page):
        for sel in selectors:
            loc = root.locator(sel).first
            try:
                if loc.count() and loc.is_visible():
                    label = (
                        (loc.inner_text() or "")
                        + " "
                        + (loc.get_attribute("aria-label") or "")
                    ).lower()
                    if "easy apply" in label:
                        return loc
            except Exception:
                continue
    return None


def easy_apply_flow(page: Page, job: JobResult) -> JobResult:
    close_overlays(page)
    # Stable CTA is on classic /jobs/view/{id} (AI search split-pane often hides it)
    if job.job_id and "/jobs/view/" not in (page.url or ""):
        try:
            page.goto(
                f"https://www.linkedin.com/jobs/view/{job.job_id}/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            time.sleep(2.5)
            close_overlays(page)
        except Exception:
            pass

    if _easy_apply_daily_limit_hit(page):
        _dismiss_easy_apply_limit_toast(page)
        job.status = "blocked"
        job.reason = "easy_apply_daily_limit"
        return job

    btn = None
    details = page.locator(
        ".jobs-details, .scaffold-layout__detail, .job-view-layout, "
        "main a[href*='/jobs/view/']"
    ).first
    scope = page
    try:
        if details.count():
            scope_candidate = details.locator(
                "xpath=ancestor::div[.//a[contains(@aria-label,'Easy Apply')] | "
                ".//button[contains(., 'Easy Apply') or contains(@aria-label,'Easy Apply')]][1]"
            )
            if scope_candidate.count():
                scope = scope_candidate.first
            elif page.locator(".jobs-details, .scaffold-layout__detail").count():
                scope = page.locator(".jobs-details, .scaffold-layout__detail").first
    except Exception:
        scope = page

    btn = _easy_apply_cta(scope, page)
    if not btn:
        # External / company-website Apply
        try:
            ext = page.locator(
                "button:has-text('Apply'), a:has-text('Apply'), "
                "button[aria-label*='Apply to'], a[aria-label*='Apply'], "
                "a[aria-label*='Apply on company website']"
            ).first
            if ext.count() and ext.is_visible():
                label = ((ext.inner_text() or "") + " " + (ext.get_attribute("aria-label") or "")).lower()
                if "easy apply" not in label and "apply" in label:
                    job.status = "skipped"
                    job.reason = "external/non-Easy Apply"
                    job.path = "external"
                    return job
        except Exception:
            pass
        detail = detail_panel_text(page)
        if re.search(r"(?:^|\n)\s*Applied\s*(?:\n|$)|application submitted", detail, re.I):
            job.status = "skipped"
            job.reason = "already applied"
            return job
        job.status = "skipped"
        job.reason = "no Easy Apply button"
        return job

    try:
        btn.click(timeout=5000, force=True)
    except Exception:
        try:
            box = btn.bounding_box()
            if box:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            else:
                btn.evaluate("el => el.click()")
        except Exception as e:
            job.status = "blocked"
            job.reason = f"Easy Apply click failed: {e}"
            return job

    time.sleep(1.5)
    close_overlays(page)

    if _easy_apply_daily_limit_hit(page):
        _dismiss_easy_apply_limit_toast(page)
        job.status = "blocked"
        job.reason = "easy_apply_daily_limit"
        return job

    modal = _apply_modal(page)
    try:
        modal.wait_for(state="visible", timeout=10000)
    except PWTimeout:
        # Full-page apply chrome (no classic modal) OR empty detail — retry once
        try:
            body = (page.locator("body").inner_text(timeout=2000) or "")[:3000]
            if re.search(r"Apply to |Contact info|Submit application", body, re.I):
                pass
            else:
                page.reload(wait_until="domcontentloaded")
                time.sleep(2)
                close_overlays(page)
                cta = _easy_apply_cta(page, page)
                if cta:
                    cta.click(timeout=5000, force=True)
                    time.sleep(1.5)
                if _easy_apply_daily_limit_hit(page):
                    _dismiss_easy_apply_limit_toast(page)
                    job.status = "blocked"
                    job.reason = "easy_apply_daily_limit"
                    return job
                modal = _apply_modal(page)
                modal.wait_for(state="visible", timeout=8000)
        except Exception:
            job.status = "blocked"
            job.reason = "Easy Apply modal did not open"
            shot(page, f"blocked-no-modal-{job.job_id}.png")
            return job

    flow_deadline = time.time() + int(os.environ.get("LINKEDIN_EASY_APPLY_CAP_S", "180"))
    last_err = ""
    for step in range(14):
        if time.time() > flow_deadline:
            job.status = "blocked"
            job.reason = f"Easy Apply time-cap: {last_err or 'timeout'}"
            shot(page, f"blocked-timeout-{job.job_id}.png")
            dismiss_apply_form(page)
            return job
        # If save dialog appeared mid-flow, discard and reopen apply
        try:
            if page.get_by_text("Save this application?").count() and page.get_by_text("Save this application?").first.is_visible():
                page.get_by_role("button", name="Discard").click(timeout=2000)
                time.sleep(0.8)
                try:
                    cta = _easy_apply_cta(scope, page)
                    if cta:
                        cta.click(timeout=4000, force=True)
                        time.sleep(1)
                except Exception:
                    pass
        except Exception:
            pass

        # Mid-form stack mismatch (e.g. PHP/Laravel questions)
        try:
            modal_text = page.locator("[role='dialog'], .jobs-easy-apply-modal").first.inner_text(timeout=1000)
            bad = jd_blacklist(modal_text)
            if bad and re.search(r"php|laravel|salesforce|servicenow|java|python|node", bad, re.I):
                job.status = "skipped"
                job.reason = f"form blacklist: {bad}"
                try:
                    page.locator(
                        ".jobs-easy-apply-modal button.artdeco-modal__dismiss, "
                        "[role='dialog']:has-text('Apply to') button.artdeco-modal__dismiss"
                    ).first.click(timeout=2000)
                    time.sleep(0.3)
                    if page.get_by_text("Save this application?").count():
                        page.get_by_role("button", name="Discard").click(timeout=2000)
                except Exception:
                    pass
                return job
        except Exception as e:
            last_err = str(e)[:120]
            pass

        close_overlays(page)
        select_resume(page)
        fill_inputs(page)

        # Footer actions MUST be scoped to Apply form — page-level get_by_role('Next')
        # matches jobs-list pagination (aria-label=Next) and abandons the form.
        form = apply_form_root(page)
        form_ok = False
        try:
            cls = (form.get_attribute("class") or "") + " " + (form.get_attribute("role") or "")
            form_ok = bool(
                re.search(r"jobs-easy-apply-modal|easy-apply-modal|\bartdeco-modal\b|dialog", cls, re.I)
            ) or bool(page.get_by_role("heading", name=re.compile(r"Apply to ", re.I)).count())
            # Reject body fallback / header-only
            if form.evaluate("el => el === document.body"):
                form_ok = False
            if re.search(r"artdeco-modal__header", cls):
                form_ok = False
        except Exception:
            form_ok = False
        if not form_ok:
            # Modal closed mid-flow — do NOT click jobs pagination Next
            last_err = "Easy Apply modal lost"
            if _application_submitted(page):
                job.status = "submitted"
                job.reason = "Application submitted"
                job.path = "Easy Apply"
                shot(page, f"submitted-{job.job_id}.png")
                return job
            time.sleep(0.6)
            continue

        advanced = False
        for name in ("Submit application", "Submit", "Review", "Next", "Continue"):
            try:
                # Prefer visible button text inside the apply form (not aria-only Next)
                if name == "Next":
                    sel = (
                        "button:text-is('Next'), button[aria-label='Next'], "
                        "button[aria-label='Continue to next step']"
                    )
                else:
                    sel = f"button:text-is('{name}'), button[aria-label='{name}']"
                btn = form.locator(sel)
                # Exclude empty-text pagination-style controls when name is Next
                candidates = []
                for i in range(min(btn.count(), 6)):
                    b = btn.nth(i)
                    try:
                        if not (b.is_visible() and b.is_enabled()):
                            continue
                        txt = (b.inner_text() or "").strip()
                        aria = (b.get_attribute("aria-label") or "").strip()
                        if name == "Next":
                            # Must be form Next (text Next or Continue to next step) — never pagination
                            if not (
                                re.search(r"^next$", txt, re.I)
                                or re.search(r"continue to next step", aria, re.I)
                            ):
                                continue
                        if txt or aria:
                            candidates.append(b)
                    except Exception:
                        continue
                if not candidates:
                    # Fallback: role within form only
                    role_btn = form.get_by_role("button", name=name, exact=True)
                    for i in range(min(role_btn.count(), 3)):
                        b = role_btn.nth(i)
                        try:
                            txt = (b.inner_text() or "").strip()
                            aria = (b.get_attribute("aria-label") or "").strip()
                            if not (b.is_visible() and b.is_enabled()):
                                continue
                            if name == "Next" and not re.search(r"^next$", txt, re.I):
                                continue
                            candidates.append(b)
                        except Exception:
                            continue
                for b in candidates[:2]:
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    time.sleep(1.6)
                    advanced = True
                    if _application_submitted(page):
                        job.status = "submitted"
                        job.reason = "Application submitted"
                        job.path = "Easy Apply"
                        try:
                            page.get_by_role("button", name=re.compile(r"^done$|dismiss", re.I)).first.click(
                                timeout=2000
                            )
                        except Exception:
                            pass
                        shot(page, f"submitted-{job.job_id}.png")
                        return job
                    break
                if advanced:
                    break
            except Exception:
                continue

        if advanced:
            # Form may close after submit without matching earlier — recheck
            if _application_submitted(page):
                job.status = "submitted"
                job.reason = "Application submitted"
                job.path = "Easy Apply"
                shot(page, f"submitted-{job.job_id}.png")
                return job
            continue

        try:
            primary = form.locator(
                "button.artdeco-button--primary:has-text('Next'), "
                "button.artdeco-button--primary:has-text('Review'), "
                "button.artdeco-button--primary:has-text('Submit'), "
                "button[aria-label='Continue to next step']"
            ).first
            if primary.count() and primary.is_visible():
                txt = (primary.inner_text() or "").lower()
                aria = (primary.get_attribute("aria-label") or "").lower()
                if any(x in txt or x in aria for x in ("next", "review", "submit", "continue")):
                    primary.click(timeout=3000, force=True)
                    time.sleep(1.4)
                    if _application_submitted(page):
                        job.status = "submitted"
                        job.reason = "Application submitted"
                        job.path = "Easy Apply"
                        shot(page, f"submitted-{job.job_id}.png")
                        return job
                    continue
        except Exception:
            pass

        # Success may appear without clicking our Submit handler
        try:
            if _application_submitted(page):
                job.status = "submitted"
                job.reason = "Application submitted"
                job.path = "Easy Apply"
                shot(page, f"submitted-{job.job_id}.png")
                try:
                    page.get_by_role("button", name=re.compile(r"^done$|dismiss", re.I)).first.click(timeout=2000)
                except Exception:
                    pass
                return job
        except Exception:
            pass

        err = ""
        try:
            err = " | ".join(
                page.locator(
                    ".artdeco-inline-feedback__message, .fb-form-element__error, "
                    ".artdeco-inline-feedback--error"
                ).all_inner_texts()
            )[:300]
        except Exception:
            pass
        # only abandon after a few retries with same state
        if step < 3:
            fill_inputs(page)
            time.sleep(0.8)
            continue
        job.status = "blocked"
        job.reason = f"stuck on Easy Apply step {step}: {err or 'no Next/Submit'}"
        shot(page, f"blocked-step-{job.job_id}.png")
        dismiss_apply_form(page)
        return job

    job.status = "blocked"
    job.reason = "exceeded Easy Apply steps"
    dismiss_apply_form(page)
    return job


def parse_card_meta(page: Page) -> tuple[str, str, str]:
    role = company = location = ""
    try:
        role = page.locator(
            ".job-details-jobs-unified-top-card__job-title, h1.t-24, "
            ".jobs-unified-top-card__job-title, a[href*='/jobs/view/']"
        ).first.inner_text(timeout=3000).strip()
        role = re.sub(r"\s+", " ", role).strip()
    except Exception:
        pass
    try:
        company = page.locator(
            ".job-details-jobs-unified-top-card__company-name a, "
            ".job-details-jobs-unified-top-card__company-name, "
            ".jobs-unified-top-card__company-name a, "
            "a[href*='/company/']"
        ).first.inner_text(timeout=3000).strip()
        company = re.sub(r"\s+", " ", company).strip()
    except Exception:
        pass
    try:
        location = page.locator(
            ".job-details-jobs-unified-top-card__tertiary-description-container, "
            ".jobs-unified-top-card__bullet, "
            ".job-details-jobs-unified-top-card__primary-description-container"
        ).first.inner_text(timeout=3000).strip()
        location = re.sub(r"\s+", " ", location)[:200]
    except Exception:
        pass
    # AI job-search detail pane: parse from bounded detail text when classic nodes missing
    if not location or not company or not role:
        detail = detail_panel_text(page)
        if detail:
            lines = [ln.strip() for ln in detail.splitlines() if ln.strip()]
            if not role:
                for ln in lines[:8]:
                    if re.search(
                        r"architect|lead|manager|principal|staff|director|\.net|engineer",
                        ln,
                        re.I,
                    ) and len(ln) < 160:
                        role = ln
                        break
            if not company:
                for ln in lines[:12]:
                    if ln == role:
                        continue
                    if re.search(
                        r"ago|applicant|promoted|hybrid|remote|on-site|easy apply|about the job|verified job",
                        ln,
                        re.I,
                    ):
                        continue
                    if 1 < len(ln) < 80:
                        company = ln
                        break
            if not location:
                for ln in lines[:15]:
                    if "·" in ln or re.search(
                        r"hyderabad|telangana|india|remote|hybrid|on-site", ln, re.I
                    ):
                        location = re.sub(r"\s+", " ", ln)[:200]
                        break
    return role, company, location


def _ids_from_report_obj(data: Any) -> set[str]:
    out: set[str] = set()
    if isinstance(data, list):
        for row in data:
            if isinstance(row, dict):
                jid = str(row.get("job_id") or row.get("jobId") or "").strip()
                if jid.isdigit():
                    out.add(jid)
        return out
    if not isinstance(data, dict):
        return out
    for key in ("submitted", "applied", "all", "blocked", "skipped", "external_candidates"):
        rows = data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            jid = str(row.get("job_id") or row.get("jobId") or "").strip()
            if jid.isdigit():
                out.add(jid)
            # Only treat submitted/applied as hard-seen when scanning "all"
            if key in ("submitted", "applied") and jid.isdigit():
                out.add(jid)
    for jid in data.get("ids") or data.get("jobIds") or []:
        s = str(jid).strip()
        if s.isdigit():
            out.add(s)
    return out


def load_prior_seen_ids(seed: set[str] | None = None) -> set[str]:
    """Merge artifact/report job IDs with optional bootstrap seed (legacy hardcodes)."""
    seen: set[str] = set(seed or ())
    candidates = [
        SEEN_IDS_PATH,
        Path("/opt/cursor/artifacts/apply-report.json"),
        Path("/opt/cursor/artifacts/linkedin-apply-report.json"),
        Path(os.environ.get("LINKEDIN_APPLY_REPORT", "")),
    ]
    # Same-day + recent markdown companions are optional; prefer JSON artifacts.
    reports_root = Path(__file__).resolve().parents[2] / "reports"
    if reports_root.is_dir():
        for day_dir in sorted(reports_root.glob("20*"), reverse=True)[:5]:
            candidates.append(day_dir / "linkedin-daily.json")
    for path in candidates:
        if not path or not str(path).strip():
            continue
        try:
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            before = len(seen)
            seen |= _ids_from_report_obj(data)
            added = len(seen) - before
            if added:
                print(f"DEDUP loaded +{added} job ids from {path}", flush=True)
        except Exception as e:
            print(f"DEDUP skip {path}: {e}", flush=True)
    return seen


def persist_seen_ids(seen: set[str], results: list[JobResult]) -> None:
    """Rolling artifact so tomorrow's run does not rely on hardcoded IDs alone."""
    for r in results:
        if r.status in ("submitted", "blocked") and (r.job_id or "").isdigit():
            seen.add(r.job_id)
    try:
        SEEN_IDS_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updatedAt": datetime.now(timezone.utc).isoformat(),
            "ids": sorted(seen),
            "count": len(seen),
        }
        SEEN_IDS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"DEDUP wrote {len(seen)} ids → {SEEN_IDS_PATH}", flush=True)
    except Exception as e:
        print(f"DEDUP persist failed: {e}", flush=True)


def process_search(
    page: Page,
    keywords: str,
    location: str,
    remote: bool,
    results: list[JobResult],
    seen: set[str],
    tpr: str = "r86400",
    easy_apply: bool = True,
) -> None:
    if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
        return
    url = search_url(keywords, location, remote=remote, tpr=tpr, easy_apply=easy_apply)
    ea = "easy" if easy_apply else "all-apply"
    print(f"SEARCH [{ea}] {keywords!r} loc={location!r} remote={remote} tpr={tpr} -> {url}")
    navigated = False
    last_nav_err = ""
    nav_tries = 5
    for nav_try in range(nav_tries):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            navigated = True
            break
        except Exception as e:
            last_nav_err = str(e)[:200]
            # LinkedIn rate-limit / transient HTTP failures (e.g. 429/999)
            print(
                f"  WARN: search goto failed (try {nav_try + 1}/{nav_tries}): {last_nav_err}",
                flush=True,
            )
            time.sleep(5 + nav_try * 8)
            try:
                page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=45000)
                time.sleep(2)
            except Exception:
                pass
    if not navigated:
        print(f"  SKIP search: navigation failed: {last_nav_err}", flush=True)
        return
    time.sleep(3)
    close_overlays(page)
    shot(page, f"search-{keywords.replace(' ','_')[:30]}-{('remote' if remote else 'hyd')}-{tpr}.png")

    # Classic list items OR LinkedIn AI job-search cards (hashed classes / search-results)
    list_items = page.locator(
        "li.scaffold-layout__list-item, li.jobs-search-results__list-item, div.job-card-container"
    )
    ai_cards = ai_job_card_buttons(page)
    use_ai = False
    try:
        n = min(list_items.count(), MAX_SCAN_PER_SEARCH)
    except Exception as e:
        print(f"  WARN: card count failed: {e}", flush=True)
        n = 0
    if n == 0:
        try:
            n = min(ai_cards.count(), MAX_SCAN_PER_SEARCH)
            use_ai = n > 0
        except Exception:
            n = 0
            use_ai = False
    try:
        print(f"  cards={n} ai={use_ai or _is_ai_job_search(page)}", flush=True)
    except Exception:
        print(f"  cards={n} ai={use_ai}", flush=True)
    if n == 0:
        # wait/reload once — never crash the whole batch on a detached frame
        time.sleep(3)
        try:
            page.reload(wait_until="domcontentloaded")
        except Exception as e:
            print(f"  WARN: search reload failed: {e}", flush=True)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e2:
                print(f"  SKIP search: reload/goto failed: {e2}", flush=True)
                return
        time.sleep(4)
        list_items = page.locator(
            "li.scaffold-layout__list-item, li.jobs-search-results__list-item, div.job-card-container"
        )
        ai_cards = ai_job_card_buttons(page)
        try:
            n = min(list_items.count(), MAX_SCAN_PER_SEARCH)
        except Exception as e:
            print(f"  WARN: card count after reload failed: {e}", flush=True)
            n = 0
        use_ai = False
        if n == 0:
            try:
                n = min(ai_cards.count(), MAX_SCAN_PER_SEARCH)
                use_ai = n > 0
            except Exception:
                n = 0
                use_ai = False
        print(f"  cards after reload={n} ai={use_ai}", flush=True)

    for i in range(n):
        if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
            break
        item = ai_cards.nth(i) if use_ai else list_items.nth(i)
        card_text = ""
        try:
            card_text = (item.inner_text(timeout=2000) or "")[:500]
        except Exception:
            card_text = ""

        # Skip already-applied from list card text (AI UI shows Applied on the card)
        if re.search(r"(?:^|\n)\s*Applied\s*(?:\n|$)", card_text, re.I):
            results.append(
                JobResult(
                    status="skipped",
                    role=card_text.split("\n")[0][:120],
                    reason="already applied",
                )
            )
            print(f"  SKIP applied (card) {card_text.splitlines()[0][:80]}", flush=True)
            continue

        clicked = False
        for attempt in range(3):
            try:
                item.scroll_into_view_if_needed(timeout=2000)
                item.click(timeout=3000)
                time.sleep(1.5)
                clicked = True
                break
            except Exception as e:
                if attempt == 2:
                    results.append(JobResult(status="skipped", reason=f"card click failed: {e}"))
                else:
                    time.sleep(0.6)
        if not clicked:
            continue

        close_overlays(page)
        job_url = page.url
        jid = extract_job_id(job_url)
        if jid and jid in seen:
            continue
        if jid:
            seen.add(jid)

        role, company, loc = parse_card_meta(page)
        # Prefer location from selected card text when detail loc is empty/noisy
        if card_text and (not loc or len(loc) < 4):
            for ln in card_text.splitlines():
                ln = ln.strip()
                if re.search(r"hyderabad|telangana|remote|hybrid|on-site|\bindia\b", ln, re.I):
                    loc = ln[:200]
                    break

        # Workplace type ONLY from job top-card (never full page / filter chips /
        # People-you-can-reach chrome — those false-pass Remote or false-skip Hyd).
        workplace = top_card_workplace_text(page, card_text)
        # Classic workplace pills (scoped) when present
        try:
            pills = page.locator(
                ".job-details-jobs-unified-top-card__workplace-type, "
                ".jobs-unified-top-card__workplace-type"
            )
            bits = []
            for pi in range(min(pills.count(), 6)):
                bits.append(pills.nth(pi).inner_text(timeout=500))
            if bits:
                workplace = " ".join(bits) + " " + workplace
        except Exception:
            pass

        job = JobResult(
            status="pending",
            company=company,
            role=role,
            job_id=jid,
            location=loc,
            url=job_url,
        )

        # Already applied badge (detail)
        try:
            detail = workplace or detail_panel_text(page)
            if (
                re.search(r"(?:^|\n)\s*Applied\s*(?:\n|$)", detail or "", re.I)
                or page.locator(".jobs-s-apply button:has-text('Applied')").count()
            ):
                job.status = "skipped"
                job.reason = "already applied"
                results.append(job)
                print(f"  SKIP applied {company} | {role}")
                continue
        except Exception:
            pass

        if not location_allowed(loc, workplace[:800], remote_search=remote):
            job.status = "skipped"
            job.reason = f"location filter: {loc[:120]}"
            results.append(job)
            print(f"  SKIP location {loc[:80]}", flush=True)
            continue

        # JD text — prefer About the job from detail pane; never whole body
        jd = ""
        try:
            jd = page.locator(
                "#job-details, .jobs-description__content, .jobs-box__html-content, "
                ".jobs-description-content__text"
            ).first.inner_text(timeout=3000)
        except Exception:
            detail = detail_panel_text(page)
            if "About the job" in detail:
                jd = detail.split("About the job", 1)[-1][:8000]
            else:
                jd = detail[:8000]

        bl = skip_reason(role, company, jd)
        if bl:
            job.status = "skipped"
            job.reason = f"blacklist: {bl}"
            results.append(job)
            print(f"  SKIP blacklist {bl} | {company} | {role}", flush=True)
            continue

        if role and not TITLE_OK.search(role):
            job.status = "skipped"
            job.reason = f"title mismatch: {role}"
            results.append(job)
            print(f"  SKIP title {role}", flush=True)
            continue

        print(f"  APPLY? {company} | {role} | {loc[:60]} | id={jid}", flush=True)
        job = easy_apply_flow(page, job)
        results.append(job)
        print(f"  -> {job.status}: {job.reason}", flush=True)
        if job.reason == "easy_apply_daily_limit":
            print("  STOP: LinkedIn Easy Apply daily limit reached", flush=True)
            return
        # easy_apply_flow often navigates to /jobs/view/{id}. Stale search-card
        # locators then hang (ep_poll) on the next iteration — restore the list.
        try:
            on_view = "/jobs/view/" in (page.url or "")
            list_alive = False
            try:
                list_alive = list_items.count() > 0 and not on_view
            except Exception:
                list_alive = False
            if on_view or not list_alive:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(2.2)
                close_overlays(page)
                list_items = page.locator(
                    "li.scaffold-layout__list-item, li.jobs-search-results__list-item, "
                    "div.job-card-container"
                )
                ai_cards = ai_job_card_buttons(page)
                if use_ai or list_items.count() == 0:
                    use_ai = ai_cards.count() > 0
                n = min(
                    (ai_cards.count() if use_ai else list_items.count()),
                    MAX_SCAN_PER_SEARCH,
                )
        except Exception as e:
            print(f"  WARN: restore search after apply failed: {e}", flush=True)
        time.sleep(1.5)


def main() -> None:
    results: list[JobResult] = []
    # Bootstrap seed (legacy hardcodes) + artifact-driven IDs from prior reports
    seed_seen: set[str] = {
        # Prior automation runs
        "4448545122",
        "4448935949",
        "4446632306",
        "4447903215",
        "4445081709",
        "4449442963",
        "4447361050",
        "4446643678",
        "4446651098",
        "4446252379",
        "4449489116",  # Blue Yonder Hyd
        "4448834059",  # Infosys Finacle Bengaluru — wrongly submitted; skip revisit
        "4448876456",  # Avtex blocked
        "4444107986",
        "4443041801",
        "4448848620",
        "4448954474",
        "4448954715",
        "4448953152",
        # 2026-08-05 submitted
        "4442582798",
        "4442589503",
        "4449476472",
        "4447381958",
        "4448875176",
        "4447389879",
        "4447500027",
        "4446210548",
        "4449101332",
        "4430575398",
        "4448528071",
        "4448858320",
        "4449494440",
        "4448990793",
        "4447296353",
        "4447285103",
        "4446749238",
        "4445834680",
        "4447061211",
        "4448032024",
        # 2026-08-05 blocked Easy Apply
        "4449459735",
        "4449485007",
        "4447984186",
        "4447298642",
        "4377950713",
        # 2026-08-07 partial run (before Arabic locale fix)
        "4448440792",
        "4449792167",
        "4449760452",
        "4442011506",
        "4448438234",
        "4441207759",
        "4449388429",
        "4450284449",
        "4437050474",
        "4405159441",
        "4442580526",
        "4450205567",
        "4450682491",
        "4415350173",
        "4270943974",
        # 2026-08-12 partial run (before stale-search-card restore fix)
        "4451697452",  # ANSR submitted
        "4450121325",  # Evernorth submitted
        "4452362389",  # aha submitted
        "4453067852",  # NationsBenefits blocked / exceeded steps
        # 2026-08-12 resumed batch (before nav-retry fix)
        "4453072505",
        "4453079159",
        "4452356075",
        "4451675940",
        "4452367116",
        "4451660547",
        "4452335747",
        "4449839825",
        "4451673152",
        "4451900087",
        "4452360082",
        "4452414600",
        "4452452320",
        "4452192346",
        "4452440592",
        "4452357739",
        "4452372538",
        "4452419731",
        "4449874108",
        "4453035603",
        "4453048524",
        "4453053540",
        "4451664963",
        "4452483183",
        "4451659579",
        "4453055195",
        "4451931992",
        "4444523612",  # Cyara blocked
        "4452340803",  # MyCareernet blocked
    }
    seen = load_prior_seen_ids(seed_seen)
    print(f"DEDUP seen ids={len(seen)} (seed={len(seed_seen)})", flush=True)
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP)
        except Exception as e:
            results.append(
                JobResult(status="blocked", reason=f"CDP connect failed: {str(e)[:180]}")
            )
            OUT.write_text(json.dumps([asdict(r) for r in results], indent=2))
            print(f"BLOCKED: CDP connect failed: {e}")
            raise SystemExit(5)
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "linkedin.com" in (pg.url or ""):
                page = pg
                break
        if page is None:
            page = context.new_page()
        page.bring_to_front()
        try:
            page.set_default_timeout(20000)
        except Exception:
            pass

        # Auth check (retry once — first paint can look like a login wall)
        signed_in = False
        for auth_try in range(2):
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2 + auth_try)
            url_l = (page.url or "").lower()
            if re.search(r"/login|authwall|/checkpoint|uas/login", url_l):
                time.sleep(2)
                continue
            body = page.locator("body").inner_text()[:2000]
            has_feed = bool(
                re.search(
                    r"Start a post|Me\n|My Network|Notifications|linkedin\.com/in/",
                    body,
                    re.I,
                )
            ) or ("/feed" in url_l and "login" not in url_l and "checkpoint" not in url_l)
            login_wall = bool(re.search(r"Sign in\n|Email or phone|Welcome Back", body)) and not has_feed
            # Cookie presence is a strong signal when feed chrome is present
            try:
                cookies = context.cookies(["https://www.linkedin.com"])
                has_li_at = any(c.get("name") == "li_at" for c in cookies)
            except Exception:
                has_li_at = False
            if has_feed and has_li_at and not login_wall:
                signed_in = True
                break
            if (
                has_li_at
                and "login" not in url_l
                and "checkpoint" not in url_l
                and not re.search(r"Email or phone", body)
            ):
                signed_in = True
                break
            time.sleep(2)
        if not signed_in:
            results.append(JobResult(status="blocked", reason="Not signed in"))
            # Preserve any earlier same-day batch; never clobber a dict report
            # with a one-row login-wall list (resume after crash used to wipe submits).
            payload: dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "ok": False,
                "counts": {
                    "applied": 0,
                    "submitted": 0,
                    "skipped": 0,
                    "blocked": 1,
                    "seen": 1,
                },
                "applied": [],
                "submitted": [],
                "skipped": [],
                "blocked": [asdict(r) for r in results],
                "all": [asdict(r) for r in results],
                "blocker": "Not signed in",
            }
            if OUT.is_file():
                try:
                    prev = json.loads(OUT.read_text(encoding="utf-8"))
                    if isinstance(prev, dict):
                        prev_sub = prev.get("submitted") or prev.get("applied") or []
                        if isinstance(prev_sub, list) and prev_sub:
                            payload["applied"] = prev_sub
                            payload["submitted"] = prev_sub
                            payload["skipped"] = prev.get("skipped") or []
                            payload["counts"]["applied"] = len(prev_sub)
                            payload["counts"]["submitted"] = len(prev_sub)
                            payload["counts"]["skipped"] = len(payload["skipped"])
                            payload["preservedFrom"] = prev.get("ts")
                            print(
                                f"PRESERVE {len(prev_sub)} earlier submitted rows in {OUT}",
                                flush=True,
                            )
                except Exception as e:
                    print(f"PRESERVE skip: {e}", flush=True)
            OUT.write_text(json.dumps(payload, indent=2))
            print("BLOCKED: not signed in")
            raise SystemExit(5)

        ensure_english_ui(page)

        def hit_daily_limit() -> bool:
            return any(r.reason == "easy_apply_daily_limit" for r in results)

        def write_report() -> None:
            submitted = [asdict(r) for r in results if r.status == "submitted"]
            skipped = [asdict(r) for r in results if r.status == "skipped"]
            blocked = [asdict(r) for r in results if r.status == "blocked"]
            report = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "ok": not any(
                    "not signed in" in (r.reason or "").lower() for r in results if r.status == "blocked"
                ),
                "counts": {
                    "applied": len(submitted),
                    "submitted": len(submitted),
                    "skipped": len(skipped),
                    "blocked": len(blocked),
                    "seen": len(results),
                },
                "applied": submitted,  # ensure-missing / coverage detectors
                "submitted": submitted,
                "skipped": skipped,
                "blocked": blocked,
                "external_candidates": [
                    asdict(r)
                    for r in results
                    if r.status == "skipped" and "external" in (r.reason or "").lower()
                ],
                "all": [asdict(r) for r in results],
            }
            OUT.write_text(json.dumps(report, indent=2))
            persist_seen_ids(seen, results)
            print("=== SUMMARY ===")
            print("submitted", len(report["submitted"]))
            print("skipped", len(report["skipped"]))
            print("blocked", len(report["blocked"]))
            print("external_candidates", len(report["external_candidates"]))
            print("wrote", OUT)

        def submitted_n() -> int:
            return len([r for r in results if r.status == "submitted"])

        def run_search_wave(*, easy_apply: bool, tpr: str) -> None:
            titles_hyd = TITLES if easy_apply else TITLES[:6]
            titles_remote = TITLES[:5] if easy_apply else TITLES[:3]
            for title in titles_hyd:
                process_search(
                    page,
                    title,
                    "Hyderabad, Telangana, India",
                    remote=False,
                    results=results,
                    seen=seen,
                    tpr=tpr,
                    easy_apply=easy_apply,
                )
                if submitted_n() >= MAX_APPLY or hit_daily_limit():
                    return
            if submitted_n() >= MAX_APPLY or hit_daily_limit():
                return
            for title in titles_remote:
                process_search(
                    page,
                    title,
                    "India",
                    remote=True,
                    results=results,
                    seen=seen,
                    tpr=tpr,
                    easy_apply=easy_apply,
                )
                if submitted_n() >= MAX_APPLY or hit_daily_limit():
                    return

        try:
            for tpr in TPR_WINDOWS:
                if submitted_n() >= MAX_APPLY or hit_daily_limit():
                    break
                # Hyderabad + Remote Easy Apply first
                run_search_wave(easy_apply=True, tpr=tpr)
                # Non-Easy Apply pass so company-site / Apply jobs are not invisible
                if (
                    not EASY_APPLY_ONLY
                    and submitted_n() < MAX_APPLY
                    and submitted_n() < NON_EA_IF_BELOW
                    and not hit_daily_limit()
                ):
                    print(
                        f"=== NON-EASY-APPLY SEARCH PASS (submitted={submitted_n()} < {NON_EA_IF_BELOW}) ===",
                        flush=True,
                    )
                    run_search_wave(easy_apply=False, tpr=tpr)
        finally:
            write_report()


if __name__ == "__main__":
    main()
