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
from urllib.parse import quote

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

CDP = os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
OUT = Path("/opt/cursor/artifacts/apply-report.json")
SCREEN_DIR = Path("/opt/cursor/artifacts")
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
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "current_ctc_lakhs": "52",
    "expected_ctc_lakhs": "65",
    "notice": "0",
    "experience_years": "15",
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
    "Technical Lead",
    "Engineering Manager",
    "Principal .NET",
    "Staff .NET",
    ".NET Architect",
]

BLACKLIST = re.compile(
    r"salesforce|servicenow|guidewire|splunk|\bpega\b|oracle\s*erp|sitecore|"
    r"\bmean\b|devops engineer|sre engineer|site reliability engineer|gcp.?presales|workato|mulesoft|"
    r"blockchain|mandarin|biztalk|firmware|\bmes\b|\bror\b|ruby on rails|"
    r"\bsap\b|dynamics\s*365|\bd365\b|esri|\bgis\b|"
    r"java[- ]?(mandatory|only|required|backend)|node\.?js[- ]?(mandatory|only)|"
    r"python[- ]?(mandatory|only)|data engineer|machine learning engineer|"
    r"big data architect|data architect|data warehouse architect|implementation specialist|"
    r"\bphp\b|laravel|ruby on rails|\bror\b|"
    r"interior designer|civil engineer|electrical engineering|golang &|golang and|"
    r"bpo|call center|marketing cloud|success architect|"
    r"non-?it staffing|us non-?it|staffing recruiter|talent acquisition",
    re.I,
)

TITLE_OK = re.compile(
    r"architect|technical lead|tech lead|engineering manager|engineering lead|"
    r"principal|staff|solution|\.net|dotnet|c#|software (development )?manager",
    re.I,
)

HYD_OK = re.compile(
    r"hyderabad|telangana|secunderabad|greater hyderabad|gachibowli|hitech city|"
    r"madhapur|kondapur|banjara hills|"
    # Arabic / Urdu LinkedIn UI (locale drift)
    r"حيدر\s*أ?باد|حيدرآباد|تلنگانہ|تلنغانا|تيلانجانا|سکندرآباد",
    re.I,
)
REMOTE_OK = re.compile(
    r"\bremote\b|\bwfh\b|work from home|india remote|fully remote|remote[, ]*india|"
    r"remote \(india\)|anywhere in india|"
    # Arabic remote / WFH
    r"عن بعد|العمل من المنزل|العمل عن بعد|من المنزل",
    re.I,
)
# India alone (EN/AR) — only with remote workplace filter or REMOTE_OK
INDIA_ONLY = re.compile(r"^(greater\s+)?india\b|^الهند\b", re.I)
BAD_CITY = re.compile(
    r"bengaluru|bangalore|pune|chennai|mumbai|delhi|noida|gurgaon|gurugram|"
    r"ahmedabad|kolkata|jaipur|kochi|trivandrum|thiruvananthapuram|coimbatore|"
    r"indore|nagpur|united states|\busa\b|\buk\b|london|singapore|dubai|"
    r"toronto|canada|australia|germany|netherlands|"
    # Arabic / Urdu city names
    r"بنغالور|بنجالور|بانجلور|بوني|بونة|تشيناي|مومباي|دلهي|نويدا|جورجاون|"
    r"أحمد آباد|كولكاتا|جايبور|كوتشي|كوتشي|إندور|اندور|ناجبور|"
    r"ماهاراشترا|تاميل نادو|كارناتاكا|كارناتاكا|ماديا براديش",
    re.I,
)

MAX_APPLY = 30
MAX_SCAN_PER_SEARCH = 40
# Past 24h, then 3 days, then 7 days
TPR_WINDOWS = ("r86400", "r259200", "r604800")


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


def location_allowed(loc: str, workplace: str = "", *, remote_search: bool = False) -> bool:
    """HARD filter: only job location/workplace strings — never page chrome/profile text."""
    text = f"{loc} {workplace}".strip()
    if not text:
        return False
    remoteish = bool(REMOTE_OK.search(text)) or remote_search
    # Bad city wins unless the SAME job text clearly says Remote/WFH
    # (LinkedIn remote filter alone is not enough if top-card city is Bengaluru/Pune/etc.)
    if BAD_CITY.search(text) and not REMOTE_OK.search(text):
        return False
    if REMOTE_OK.search(text):
        return True
    if HYD_OK.search(text):
        return True
    # Remote search + India-only location (EN/AR) with no bad city → allow
    if remoteish and INDIA_ONLY.search((loc or "").strip()):
        return True
    # Arabic "India" appearing in tertiary line during remote search
    if remoteish and re.search(r"\bالهند\b", text) and not BAD_CITY.search(text):
        return True
    return False


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


def jd_blacklist(text: str) -> str | None:
    m = BLACKLIST.search(text or "")
    return m.group(0) if m else None


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


def fill_inputs(page: Page) -> None:
    """Best-effort fill of Easy Apply form fields."""
    # New LinkedIn Easy Apply often uses aria-label on inputs (no <label for=>).
    try:
        for inp in page.locator("input[type='text'], textarea, input:not([type])").all()[:35]:
            try:
                if not inp.is_visible():
                    continue
                aria = (inp.get_attribute("aria-label") or "").strip().lower()
                if not aria:
                    continue
                cur = ""
                try:
                    cur = inp.input_value()
                except Exception:
                    pass
                if any(k in aria for k in ("phone", "mobile")) and "country" not in aria:
                    if not cur:
                        inp.fill(PROFILE["phone"])
                elif "email" in aria and not cur:
                    inp.fill(PROFILE["email"])
                elif "current ctc" in aria or "present ctc" in aria or "current salary" in aria:
                    inp.fill(PROFILE["current_ctc_lakhs"] if "lakh" in aria else PROFILE["current_ctc"])
                elif "expected ctc" in aria or "expected salary" in aria or "desired salary" in aria:
                    inp.fill(PROFILE["expected_ctc_lakhs"] if "lakh" in aria else PROFILE["expected_ctc"])
                elif "notice" in aria:
                    inp.fill("0")
                elif "last working date" in aria or "last day" in aria:
                    # Many forms reject prose; "0" / short token accepted when immediate
                    inp.fill("0")
                elif "years of" in aria or "how many years" in aria:
                    # Prefer 15 for general; stack-specific years use modest nonzero
                    if any(k in aria for k in ("python", "java", "node", "golang", "php")):
                        inp.fill("3")
                    elif any(k in aria for k in (".net", "c#", "csharp", "microservices", "azure", "aws", "kafka")):
                        inp.fill(PROFILE["experience_years"])
                    else:
                        inp.fill(PROFILE["experience_years"])
                elif ("city" in aria) and not cur:
                    inp.fill(PROFILE["city"])
            except Exception:
                continue
    except Exception:
        pass

    # Radio Yes/No groups: check the first option in each group (usually Yes)
    try:
        seen: set[str] = set()
        radios = page.locator("input[type='radio']")
        for i in range(min(radios.count(), 24)):
            r = radios.nth(i)
            try:
                if not r.is_visible():
                    continue
                name = r.get_attribute("name") or f"anon-{i}"
                if name in seen:
                    continue
                # Prefer explicit Yes nearby; else first radio in group
                parent = r.locator(
                    "xpath=ancestor::div[.//text()='Yes' or .//text()='No'][1]"
                )
                yes = parent.locator("input[type='radio']").first
                target = yes if yes.count() else r
                # If question looks like sponsorship/visa, prefer No (second)
                blob = ""
                try:
                    blob = (parent.inner_text(timeout=400) or "").lower()
                except Exception:
                    blob = ""
                if any(k in blob for k in ("sponsorship", "visa sponsorship", "require sponsorship")):
                    opts = parent.locator("input[type='radio']")
                    if opts.count() >= 2:
                        target = opts.nth(1)
                target.check(force=True)
                seen.add(name)
            except Exception:
                continue
    except Exception:
        pass

    # Text/select/textarea with labels
    labels = page.locator(
        ".jobs-easy-apply-modal label, .jobs-easy-apply-content label, "
        "[role='dialog'] label, .artdeco-modal label, form label, "
        "div:has(> h2:has-text('Apply to')) label"
    )
    count = min(labels.count(), 40)
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
        elif "country code" in blob or ( "phone" in blob and "country" in blob):
            try:
                control.select_option(label=re.compile(r"India \(\+91\)", re.I))
            except Exception:
                try:
                    control.select_option(label=re.compile(r"india|\+91", re.I))
                except Exception:
                    pass
        elif any(k in blob for k in ("current ctc", "current salary", "current compensation", "present ctc", "confirm your current ctc")):
            # Forms often ask Lakhs
            if "lakh" in blob:
                set_val(PROFILE["current_ctc_lakhs"])
            else:
                set_val(PROFILE["current_ctc"])
        elif any(k in blob for k in ("expected ctc", "expected salary", "expected compensation", "desired salary")):
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

    # Native selects still on Select an option
    try:
        page.evaluate(
            """() => {
              const h=[...document.querySelectorAll('h2,h1')].find(e=>/Apply to /i.test(e.innerText||''));
              const root=h ? (h.closest('.artdeco-modal') || h.parentElement?.parentElement?.parentElement) : document;
              for (const s of root.querySelectorAll('select')) {
                const yes=[...s.options].find(o=>o.text.trim().toLowerCase()==='yes');
                if(yes && (!s.value || /select/i.test(s.options[s.selectedIndex]?.text||''))) {
                  s.value=yes.value;
                  s.dispatchEvent(new Event('input',{bubbles:true}));
                  s.dispatchEvent(new Event('change',{bubbles:true}));
                }
              }
            }"""
        )
    except Exception:
        pass

    # Also fill unlabeled numeric errors: decimal > 0 near CTC/notice
    try:
        for inp in page.locator("input[type='text']").all()[:25]:
            try:
                if not inp.is_visible():
                    continue
                val = inp.input_value()
                if val:
                    continue
                near = inp.evaluate(
                    """e => (e.closest('div')?.innerText || '').slice(0,180).toLowerCase()"""
                )
                if "ctc" in near and "lakh" in near and "current" in near:
                    inp.fill(PROFILE["current_ctc_lakhs"])
                elif "ctc" in near and "lakh" in near and "expect" in near:
                    inp.fill(PROFILE["expected_ctc_lakhs"])
                elif "notice" in near:
                    inp.fill("1")
                elif ("years" in near or "experience" in near) and "php" not in near:
                    inp.fill("15")
            except Exception:
                pass
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
    ]:
        try:
            q = page.get_by_text(re.compile(pair[0], re.I)).first
            if q.count() and q.is_visible():
                container = q.locator(
                    "xpath=ancestor::fieldset|ancestor::div[contains(@class,'fb-dash') or contains(@class,'jobs-easy-apply')][1]"
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


def _apply_modal(page: Page):
    # New LinkedIn modals may lack .jobs-easy-apply-modal / role=dialog
    heading = page.get_by_role("heading", name=re.compile(r"Apply to ", re.I))
    try:
        if heading.count() and heading.first.is_visible():
            modal = heading.first.locator(
                "xpath=ancestor::div[contains(@class,'artdeco-modal') or contains(@class,'easy-apply') or @role='dialog'][1]"
            )
            if modal.count():
                return modal
            return heading.first.locator(
                "xpath=ancestor::div[.//button[contains(.,'Next') or contains(.,'Review') or contains(.,'Submit')]][1]"
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


def easy_apply_flow(page: Page, job: JobResult) -> JobResult:
    close_overlays(page)
    # Find Easy Apply — LinkedIn 2026 job-view markup often drops .jobs-apply-button
    # (hashed utility classes). Prefer role/aria text, then CSS fallbacks.
    btn = None
    try:
        role_btn = page.get_by_role("button", name=re.compile(r"Easy Apply", re.I))
        if role_btn.count() and role_btn.first.is_visible():
            btn = role_btn.first
    except Exception:
        pass
    if not btn:
        details = page.locator(
            ".jobs-details, .scaffold-layout__detail, .job-view-layout, "
            ".job-details-jobs-unified-top-card__container, main"
        ).first
        scopes = []
        if details.count():
            scopes.append(details)
        scopes.append(page)
        for scope in scopes:
            for sel in [
                "button[aria-label*='Easy Apply']",
                "button:has-text('Easy Apply')",
                "button.jobs-apply-button",
            ]:
                loc = scope.locator(sel).first
                try:
                    if loc.count() and loc.is_visible():
                        label = (
                            (loc.inner_text() or "")
                            + " "
                            + (loc.get_attribute("aria-label") or "")
                        ).lower()
                        if "easy apply" in label:
                            btn = loc
                            break
                        if "apply" in label and "easy" not in label:
                            job.status = "skipped"
                            job.reason = "external/non-Easy Apply"
                            return job
                except Exception:
                    continue
            if btn:
                break
    if not btn:
        # Distinguish external Apply vs missing button
        try:
            apply_role = page.get_by_role("button", name=re.compile(r"^Apply$", re.I))
            if apply_role.count() and apply_role.first.is_visible():
                job.status = "skipped"
                job.reason = "external/non-Easy Apply"
                return job
        except Exception:
            pass
        body = page.locator("body").inner_text()[:3000]
        if re.search(r"\bapplied\b|application submitted", body, re.I):
            job.status = "skipped"
            job.reason = "already applied"
            return job
        job.status = "skipped"
        job.reason = "no Easy Apply button"
        return job

    try:
        btn.click(timeout=5000)
    except Exception:
        try:
            btn.evaluate("el => el.click()")
        except Exception as e:
            job.status = "blocked"
            job.reason = f"Easy Apply click failed: {e}"
            return job

    time.sleep(1.5)
    close_overlays(page)

    def _reopen_easy_apply() -> None:
        try:
            page.get_by_role("button", name=re.compile(r"Easy Apply", re.I)).first.click(timeout=5000)
        except Exception:
            page.locator("button:has-text('Easy Apply')").first.click(timeout=5000)

    modal = _apply_modal(page)
    try:
        modal.wait_for(state="visible", timeout=10000)
    except PWTimeout:
        # reload once if empty
        page.reload(wait_until="domcontentloaded")
        time.sleep(2)
        close_overlays(page)
        try:
            _reopen_easy_apply()
            time.sleep(1.5)
            modal = _apply_modal(page)
            modal.wait_for(state="visible", timeout=8000)
        except Exception:
            job.status = "blocked"
            job.reason = "Easy Apply modal did not open"
            shot(page, f"blocked-no-modal-{job.job_id}.png")
            return job

    for step in range(14):
        # If save dialog appeared mid-flow, discard and reopen apply
        try:
            if page.get_by_text("Save this application?").count() and page.get_by_text("Save this application?").first.is_visible():
                page.get_by_role("button", name="Discard").click(timeout=2000)
                time.sleep(0.8)
                try:
                    _reopen_easy_apply()
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
        except Exception:
            pass

        close_overlays(page)
        select_resume(page)
        fill_inputs(page)

        # Prefer role-based footer actions (works even when role=dialog is missing)
        advanced = False
        for name in ("Submit application", "Submit", "Review", "Next", "Continue"):
            try:
                btn = page.get_by_role("button", name=name, exact=True)
                if not btn.count():
                    btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I))
                for i in range(min(btn.count(), 3)):
                    b = btn.nth(i)
                    if not (b.is_visible() and b.is_enabled()):
                        continue
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    time.sleep(1.6)
                    advanced = True
                    body = page.locator("body").inner_text()[:5000]
                    if re.search(
                        r"application (was )?submitted|applied to .+ ago|\byou applied\b|"
                        r"applied \d+ (second|minute|hour|day)s? ago|\bapplication sent\b",
                        body,
                        re.I,
                    ):
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
            continue

        try:
            primary = page.locator("button.artdeco-button--primary").first
            if primary.count() and primary.is_visible():
                txt = (primary.inner_text() or "").lower()
                if any(x in txt for x in ("next", "review", "submit", "continue")):
                    primary.click(timeout=3000, force=True)
                    time.sleep(1.4)
                    continue
        except Exception:
            pass

        # Success may appear without clicking our Submit handler
        try:
            body = page.locator("body").inner_text()[:5000]
            if re.search(
                r"application (was )?submitted|applied \d+ (second|minute|hour|day)s? ago|"
                r"\bapplication sent\b",
                body,
                re.I,
            ):
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
        try:
            dismiss = page.locator(
                ".jobs-easy-apply-modal button.artdeco-modal__dismiss, "
                "[role='dialog']:has-text('Apply to') button.artdeco-modal__dismiss"
            ).first
            if dismiss.count():
                dismiss.click(timeout=2000)
                time.sleep(0.4)
            if page.get_by_text("Save this application?").count():
                page.get_by_role("button", name="Discard").click(timeout=2000)
        except Exception:
            pass
        return job

    job.status = "blocked"
    job.reason = "exceeded Easy Apply steps"
    return job


def parse_card_meta(page: Page) -> tuple[str, str, str]:
    role = company = location = ""
    try:
        role = page.locator(".job-details-jobs-unified-top-card__job-title, h1.t-24, .jobs-unified-top-card__job-title").first.inner_text(timeout=3000).strip()
    except Exception:
        pass
    try:
        company = page.locator(
            ".job-details-jobs-unified-top-card__company-name a, "
            ".job-details-jobs-unified-top-card__company-name, "
            ".jobs-unified-top-card__company-name a"
        ).first.inner_text(timeout=3000).strip()
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
    return role, company, location


def process_search(
    page: Page,
    keywords: str,
    location: str,
    remote: bool,
    results: list[JobResult],
    seen: set[str],
    tpr: str = "r86400",
) -> None:
    if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
        return
    url = search_url(keywords, location, remote=remote, tpr=tpr)
    print(f"SEARCH {keywords!r} loc={location!r} remote={remote} tpr={tpr} -> {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    close_overlays(page)
    shot(page, f"search-{keywords.replace(' ','_')[:30]}-{('remote' if remote else 'hyd')}-{tpr}.png")

    # Collect job cards
    cards = page.locator(
        "div.job-card-container, li.jobs-search-results__list-item, "
        "div.scaffold-layout__list-item, a.job-card-list__title--link"
    )
    # Prefer list items
    list_items = page.locator("li.scaffold-layout__list-item, li.jobs-search-results__list-item, div.job-card-container")
    n = min(list_items.count(), MAX_SCAN_PER_SEARCH)
    print(f"  cards={n}")
    if n == 0:
        # wait/reload once
        time.sleep(3)
        page.reload(wait_until="domcontentloaded")
        time.sleep(3)
        list_items = page.locator("li.scaffold-layout__list-item, li.jobs-search-results__list-item, div.job-card-container")
        n = min(list_items.count(), MAX_SCAN_PER_SEARCH)
        print(f"  cards after reload={n}")

    for i in range(n):
        if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
            break
        item = list_items.nth(i)
        try:
            item.scroll_into_view_if_needed(timeout=2000)
            item.click(timeout=3000)
            time.sleep(1.5)
        except Exception as e:
            results.append(JobResult(status="skipped", reason=f"card click failed: {e}"))
            continue

        close_overlays(page)
        job_url = page.url
        jid = extract_job_id(job_url)
        if jid and jid in seen:
            continue
        if jid:
            seen.add(jid)

        role, company, loc = parse_card_meta(page)
        # Workplace type ONLY from job top-card (never full page — profile/search chrome
        # often contains "Hyderabad" and falsely passes the location filter).
        workplace = ""
        try:
            top = page.locator(
                ".job-details-jobs-unified-top-card__container, "
                ".jobs-unified-top-card, .job-details-jobs-unified-top-card"
            ).first
            if top.count():
                workplace = (top.inner_text(timeout=2000) or "")[:600]
        except Exception:
            workplace = ""
        # Prefer explicit Remote/On-site/Hybrid pills in top card
        try:
            pills = page.locator(
                ".job-details-jobs-unified-top-card__workplace-type, "
                ".jobs-unified-top-card__workplace-type, "
                "span.tvm__text:has-text('Remote'), "
                "span.tvm__text:has-text('Hybrid'), "
                "span.tvm__text:has-text('On-site')"
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

        # Already applied badge (class names are unstable — use text/role)
        try:
            applied = False
            if page.get_by_role("button", name=re.compile(r"^Applied$", re.I)).count():
                applied = True
            elif page.get_by_text(re.compile(r"^Applied$", re.I)).count():
                applied = True
            elif page.locator("button:has-text('Applied'), .jobs-s-apply button:has-text('Applied')").count():
                applied = True
            if applied:
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

        # JD text
        jd = ""
        try:
            jd = page.locator(
                "#job-details, .jobs-description__content, .jobs-box__html-content, "
                ".jobs-description-content__text"
            ).first.inner_text(timeout=3000)
        except Exception:
            try:
                jd = page.locator("article, .jobs-details").first.inner_text(timeout=2000)[:8000]
            except Exception:
                jd = ""

        bl = jd_blacklist(f"{role}\n{company}\n{jd}")
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
        print(f"  -> {job.status}: {job.reason}")
        time.sleep(1.5)


def main() -> None:
    results: list[JobResult] = []
    # Prior-run IDs (already applied) — LinkedIn also marks Applied; keep for safety
    seen: set[str] = {
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
        # 2026-08-07 remaining submitted
        "4449004507",
        "4448045993",
        "4449743811",
        # 2026-08-08 submitted
        "4450094873",
        "4448731672",
        "4448713951",
        "4450354286",
        "4440489211",
        # 2026-08-08 blocked Easy Apply
        "4450344115",
        "4448280604",
        "4448857323",
        "4448752998",
        "4443667824",
        "4450071178",
    }
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = None
        for pg in context.pages:
            if "linkedin.com" in (pg.url or ""):
                page = pg
                break
        if page is None:
            page = context.new_page()
        page.bring_to_front()

        # Auth check
        page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
        time.sleep(2)
        body = page.locator("body").inner_text()[:1500]
        if re.search(r"Sign in\n|Email or phone", body) and "Start a post" not in body:
            results.append(JobResult(status="blocked", reason="Not signed in"))
            OUT.write_text(json.dumps([asdict(r) for r in results], indent=2))
            print("BLOCKED: not signed in")
            return

        ensure_english_ui(page)

        for tpr in TPR_WINDOWS:
            if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                break
            # Hyderabad first
            for title in TITLES:
                process_search(
                    page,
                    title,
                    "Hyderabad, Telangana, India",
                    remote=False,
                    results=results,
                    seen=seen,
                    tpr=tpr,
                )
                if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                    break

            # Remote India
            if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                break
            for title in TITLES[:5]:
                process_search(
                    page, title, "India", remote=True, results=results, seen=seen, tpr=tpr
                )
                if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                    break

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "submitted": [asdict(r) for r in results if r.status == "submitted"],
        "skipped": [asdict(r) for r in results if r.status == "skipped"],
        "blocked": [asdict(r) for r in results if r.status == "blocked"],
        "external_candidates": [
            asdict(r) for r in results if r.status == "skipped" and "external" in (r.reason or "").lower()
        ],
        "all": [asdict(r) for r in results],
    }
    OUT.write_text(json.dumps(report, indent=2))
    print("=== SUMMARY ===")
    print("submitted", len(report["submitted"]))
    print("skipped", len(report["skipped"]))
    print("blocked", len(report["blocked"]))
    print("external_candidates", len(report["external_candidates"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
