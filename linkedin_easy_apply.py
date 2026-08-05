#!/usr/bin/env python3
"""LinkedIn Easy Apply batch for Rafi Ahmed — Hyderabad / Remote India only."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

CDP = "http://127.0.0.1:9222"
OUT = Path("/opt/cursor/artifacts/apply-report.json")
SCREEN_DIR = Path("/opt/cursor/artifacts")
RESUME_LABEL = "Rafi_Resume_Architect"

PROFILE = {
    "phone": "8790251698",
    "email": "rafi.success@gmail.com",
    "current_ctc": "5200000",
    "expected_ctc": "6000000",
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
    r"java[- ]?(mandatory|only|required)|node\.?js[- ]?(mandatory|only)|"
    r"python[- ]?(mandatory|only)|data engineer|machine learning engineer|"
    r"big data architect|data architect|implementation specialist|"
    r"\bphp\b|laravel|ruby on rails|\bror\b|"
    r"bpo|call center|marketing cloud|success architect",
    re.I,
)

TITLE_OK = re.compile(
    r"architect|technical lead|tech lead|engineering manager|engineering lead|"
    r"principal|staff|solution|\.net|dotnet|c#|software (development )?manager",
    re.I,
)

HYD_OK = re.compile(
    r"hyderabad|telangana|secunderabad|greater hyderabad|gachibowli|hitech city|"
    r"madhapur|kondapur",
    re.I,
)
REMOTE_OK = re.compile(
    r"\bremote\b|\bwfh\b|work from home|india remote|fully remote|remote[, ]*india|"
    r"remote \(india\)|anywhere in india",
    re.I,
)
BAD_CITY = re.compile(
    r"bengaluru|bangalore|pune|chennai|mumbai|delhi|noida|gurgaon|gurugram|"
    r"ahmedabad|kolkata|jaipur|kochi|trivandrum|thiruvananthapuram|coimbatore|"
    r"indore|nagpur|united states|\busa\b|\buk\b|london|singapore|dubai|"
    r"toronto|canada|australia|germany|netherlands",
    re.I,
)

MAX_APPLY = 8
MAX_SCAN_PER_SEARCH = 25


@dataclass
class JobResult:
    status: str
    company: str = ""
    role: str = ""
    job_id: str = ""
    location: str = ""
    reason: str = ""
    url: str = ""


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


def location_allowed(loc: str, workplace: str = "") -> bool:
    text = f"{loc} {workplace}"
    if REMOTE_OK.search(text):
        return True
    if HYD_OK.search(text):
        return True
    # Explicit non-hyd onsite
    if BAD_CITY.search(text) and not REMOTE_OK.search(text):
        return False
    return False


def jd_blacklist(text: str) -> str | None:
    m = BLACKLIST.search(text or "")
    return m.group(0) if m else None


def search_url(keywords: str, location: str, remote: bool = False) -> str:
    # f_AL=true Easy Apply, sortBy=DD latest, f_TPR=r86400 last 24h optional wider
    geo = quote(location)
    kw = quote(keywords)
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={kw}"
        f"&location={geo}&f_AL=true&sortBy=DD&f_TPR=r604800"
    )
    if remote:
        url += "&f_WT=2"  # remote workplace type
    return url


def extract_job_id(url: str) -> str:
    m = re.search(r"currentJobId=(\d+)", url) or re.search(r"/jobs/view/(\d+)", url)
    return m.group(1) if m else ""


def fill_inputs(page: Page) -> None:
    """Best-effort fill of Easy Apply form fields."""
    # Text/select/textarea with labels
    labels = page.locator(
        ".jobs-easy-apply-modal label, .jobs-easy-apply-content label, "
        "[role='dialog'] label, form label"
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
                set_val("52")
            else:
                set_val(PROFILE["current_ctc"])
        elif any(k in blob for k in ("expected ctc", "expected salary", "expected compensation", "desired salary")):
            if "lakh" in blob:
                set_val("60")
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

    # Artdeco / custom dropdowns showing "Select an option"
    try:
        triggers = page.locator(
            "[role='dialog'] button:has-text('Select an option'), "
            ".jobs-easy-apply-modal button:has-text('Select an option')"
        )
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
                # choose first non-placeholder option
                opt = page.locator("[role='listbox'] [role='option']").nth(1)
                if opt.count():
                    opt.click(timeout=2000)
            time.sleep(0.3)
    except Exception:
        pass

    # Native selects still on Select an option
    try:
        for s in page.locator("[role='dialog'] select, .jobs-easy-apply-modal select").all()[:10]:
            try:
                val = s.input_value()
                if val and "select" not in val.lower():
                    continue
                opts = [o.strip() for o in s.locator("option").all_inner_texts()]
                if any(o.lower() == "yes" for o in opts):
                    s.select_option(label=re.compile(r"^yes$", re.I))
            except Exception:
                pass
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

    # Also fill unlabeled numeric errors: decimal > 0 near CTC/notice
    try:
        for inp in page.locator("[role='dialog'] input[type='text'], [role='dialog'] input:not([type])").all()[:20]:
            try:
                if not inp.is_visible():
                    continue
                val = inp.input_value()
                if val:
                    continue
                # nearby text
                near = inp.evaluate(
                    """e => (e.closest('div')?.innerText || '').slice(0,180).toLowerCase()"""
                )
                if "ctc" in near and "lakh" in near and "current" in near:
                    inp.fill("52")
                elif "ctc" in near and "lakh" in near and "expect" in near:
                    inp.fill("60")
                elif "notice" in near:
                    inp.fill("1")
                elif "years" in near or "experience" in near:
                    inp.fill("15")
                elif "month" in near and ("experience" in near or "php" in near or "laravel" in near):
                    # wrong stack — leave empty so we can skip; mark via blacklist earlier
                    pass
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
        cand = page.get_by_text(re.compile(r"Rafi_Resume_Architect|Architect\.docx|Rafi.*Architect", re.I))
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
    # Find Easy Apply button in job details (not list)
    btn = None
    details = page.locator(".jobs-details, .scaffold-layout__detail, .job-view-layout").first
    scope = details if details.count() else page
    for sel in [
        "button.jobs-apply-button",
        "button:has-text('Easy Apply')",
        "button[aria-label*='Easy Apply']",
    ]:
        loc = scope.locator(sel).first
        try:
            if loc.count() and loc.is_visible():
                label = ((loc.inner_text() or "") + " " + (loc.get_attribute("aria-label") or "")).lower()
                if "easy apply" in label:
                    btn = loc
                    break
                if "apply" in label and "easy" not in label:
                    job.status = "skipped"
                    job.reason = "external/non-Easy Apply"
                    return job
        except Exception:
            continue
    if not btn:
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

    modal = _apply_modal(page)
    try:
        modal.wait_for(state="visible", timeout=10000)
    except PWTimeout:
        # reload once if empty
        page.reload(wait_until="domcontentloaded")
        time.sleep(2)
        close_overlays(page)
        try:
            scope.locator("button:has-text('Easy Apply')").first.click(timeout=5000)
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
                    scope.locator("button:has-text('Easy Apply')").first.click(timeout=4000)
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

        # Scope buttons to apply modal footer
        footer = page.locator(
            ".jobs-easy-apply-modal footer, .artdeco-modal__actionbar, "
            "[role='dialog'] footer, .jobs-easy-apply-footer"
        ).first
        btn_scope = footer if footer.count() else page.locator("[role='dialog']").first

        submit = btn_scope.get_by_role("button", name=re.compile(r"submit application|submit", re.I))
        next_btn = btn_scope.get_by_role("button", name=re.compile(r"^next$|^review$|^continue$", re.I))
        # fallback text locators
        if not submit.count():
            submit = page.locator("button[aria-label*='Submit application'], button:has-text('Submit application')")
        if not next_btn.count():
            next_btn = page.locator("button[aria-label*='Continue to next'], button[aria-label*='Next'], button:has-text('Next'), button:has-text('Review')")

        # Submit first
        try:
            s = submit.first
            if s.count() and s.is_visible():
                try:
                    s.click(timeout=3000, force=True)
                except Exception:
                    s.evaluate("el => el.click()")
                time.sleep(2.2)
                body = page.locator("body").inner_text()[:5000]
                if re.search(
                    r"application (was )?submitted|applied to .+ ago|\byou applied\b|"
                    r"applied \d+ (second|minute|hour|day)s? ago|\bapplication sent\b",
                    body,
                    re.I,
                ):
                    job.status = "submitted"
                    job.reason = "Application submitted"
                    try:
                        page.get_by_role("button", name=re.compile(r"^done$|dismiss", re.I)).first.click(timeout=2000)
                    except Exception:
                        try:
                            page.keyboard.press("Escape")
                        except Exception:
                            pass
                    shot(page, f"submitted-{job.job_id}.png")
                    return job
                # follow-up next if still open
        except Exception:
            pass

        # Next / Review
        advanced = False
        try:
            n = next_btn.first
            if n.count() and n.is_visible():
                disabled = n.get_attribute("disabled")
                aria_dis = n.get_attribute("aria-disabled")
                if disabled or aria_dis == "true":
                    # try fill again
                    fill_inputs(page)
                    select_resume(page)
                    time.sleep(0.5)
                try:
                    n.click(timeout=3000, force=True)
                except Exception:
                    n.evaluate("el => el.click()")
                time.sleep(1.4)
                advanced = True
        except Exception:
            pass

        if advanced:
            continue

        # One more attempt: any primary blue button in modal
        try:
            primary = page.locator(
                "[role='dialog'] button.artdeco-button--primary, "
                ".jobs-easy-apply-modal button.artdeco-button--primary"
            ).first
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


def process_search(page: Page, keywords: str, location: str, remote: bool, results: list[JobResult], seen: set[str]) -> None:
    if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
        return
    url = search_url(keywords, location, remote=remote)
    print(f"SEARCH {keywords!r} loc={location!r} remote={remote} -> {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3)
    close_overlays(page)
    shot(page, f"search-{keywords.replace(' ','_')[:30]}-{('remote' if remote else 'hyd')}.png")

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
        # workplace type from top card
        workplace = ""
        try:
            workplace = page.locator("body").inner_text()[:500]
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

        # Already applied badge
        try:
            if page.get_by_text(re.compile(r"^Applied$", re.I)).count() or page.locator(".jobs-s-apply button:has-text('Applied')").count():
                job.status = "skipped"
                job.reason = "already applied"
                results.append(job)
                print(f"  SKIP applied {company} | {role}")
                continue
        except Exception:
            pass

        if not location_allowed(loc, workplace[:800]):
            job.status = "skipped"
            job.reason = f"location filter: {loc[:120]}"
            results.append(job)
            print(f"  SKIP location {loc[:80]}")
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
    seen: set[str] = {'4448545122', '4448935949'}  # PRE_SEEN submitted earlier this run
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

        # Hyderabad first
        for title in TITLES:
            process_search(page, title, "Hyderabad, Telangana, India", remote=False, results=results, seen=seen)
            if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                break

        # Remote India
        if len([r for r in results if r.status == "submitted"]) < MAX_APPLY:
            for title in TITLES[:4]:
                process_search(page, title, "India", remote=True, results=results, seen=seen)
                if len([r for r in results if r.status == "submitted"]) >= MAX_APPLY:
                    break

    report = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "submitted": [asdict(r) for r in results if r.status == "submitted"],
        "skipped": [asdict(r) for r in results if r.status == "skipped"],
        "blocked": [asdict(r) for r in results if r.status == "blocked"],
        "all": [asdict(r) for r in results],
    }
    OUT.write_text(json.dumps(report, indent=2))
    print("=== SUMMARY ===")
    print("submitted", len(report["submitted"]))
    print("skipped", len(report["skipped"]))
    print("blocked", len(report["blocked"]))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
