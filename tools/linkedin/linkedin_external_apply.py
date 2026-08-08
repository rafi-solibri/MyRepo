#!/usr/bin/env python3
"""Follow LinkedIn external Apply redirects and complete company ATS when possible."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import Page, TimeoutError as PWTimeout, sync_playwright
import sys

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
try:
    from tools.resume_paths import resume_upload_path
except Exception:
    def resume_upload_path():
        for c in [
            "/workspace/resumes/Rafi_Resume.docx",
            "/home/ubuntu/resumes/Rafi_Resume.docx",
            "/home/ubuntu/Documents/Rafi_Resume.docx",
        ]:
            if Path(c).is_file():
                return c
        raise FileNotFoundError("Rafi_Resume.docx missing")

CDP = os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
REPORT_IN = Path("/opt/cursor/artifacts/apply-report.json")
REPORT_OUT = Path("/opt/cursor/artifacts/external-apply-report.json")
SCREEN_DIR = Path("/opt/cursor/artifacts")

PROFILE = {
    "first": "Mohammed Abdul Rafi",
    "last": "Ahmed",
    "full": "Mohammed Abdul Rafi Ahmed",
    "phone": "8790251698",
    "email": "rafi.success@gmail.com",
    "linkedin": "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "notice": "0",
    "experience_years": "15",
}

# Prefer .NET/architect Hyderabad or Remote India; skip known bad cities unless remote-only listing.
PRIORITY_IDS = [
    "4405159441",  # Blackbaud Laureate .NET Architecture Hyd
    "4442580526",  # Experian Lead SWE .NET + AWS Hyd
    "4415350173",  # Hyland Senior Software Architect .NET
    "4433879078",  # Hyland Senior Software Architect Hyd
    "4270943974",  # Storable Technical Architect Hyd
    "4442700522",  # GE Vernova Lead Software Solution Architect Hyd
    "4438407299",  # Palo Alto Senior Principal Software Architect Hyd
    "4446911955",  # Cognizant Technology Architect Hyd
    "4444948388",  # Agivant Principal Software Engineer Hyd
    "4450205567",  # Hire Feed Backend C#/.NET Remote
    "4450682491",  # Netrolynx AI Associate Technical Lead
    "4450035921",  # Quik Hire .NET Engineer Remote
    "4398091856",  # Willspired Professional Services Solutions Architect Hyd
    "3963509343",  # Rise Services Senior Principal Solution Engineer Hyd
    "4401736196",  # StarRez Technical Lead Hyd
    "4437577980",  # RSM Digital Solutions Architect Hyd
    "4447521118",  # Microsoft Architect Apps & AI Hyd
    "4440898082",  # Experian .NET Hyd
    "4440227307",  # Solera Principal SWE Hyd
    "4404747227",  # Brady Principal .NET Azure India
    "4441511168",  # MCO Engineering Manager Hyd
    "4448938075",  # Hire Feed Solutions Architect Remote
]

SKIP_COMPANY_LOC = re.compile(
    r"pune|noida|bengaluru|bangalore|delhi|chennai|mumbai|gurgaon|gurugram|"
    r"indore|بنغالور|مومباي|دلهي|تشيناي|بوني|إندور",
    re.I,
)
MAX_EXTERNAL = 12
ATS_TIME_CAP_S = 210  # ~3.5 minutes


@dataclass
class ExtResult:
    status: str
    company: str = ""
    role: str = ""
    job_id: str = ""
    location: str = ""
    reason: str = ""
    url: str = ""
    path: str = ""


def shot(page: Page, name: str) -> None:
    try:
        page.screenshot(path=str(SCREEN_DIR / name), full_page=False)
    except Exception:
        pass


def fill_common(page: Page) -> None:
    pairs = [
        (r"first name|given name", PROFILE["first"]),
        (r"last name|surname|family name", PROFILE["last"]),
        (r"^full name$|legal name|your name", PROFILE["full"]),
        (r"email|e-mail", PROFILE["email"]),
        (r"phone|mobile|tel", PROFILE["phone"]),
        (r"linkedin|profile url", PROFILE["linkedin"]),
        (r"city|current city", PROFILE["city"]),
        (r"state|province|region", PROFILE["state"]),
        (r"country", PROFILE["country"]),
        (r"current (ctc|salary|compensation)|present ctc", PROFILE["current_ctc"]),
        (r"expected (ctc|salary|compensation)|desired salary", PROFILE["expected_ctc"]),
        (r"notice", PROFILE["notice"]),
        (r"years of experience|total experience", PROFILE["experience_years"]),
    ]
    labels = page.locator("label, [data-automation-id], .form-group label")
    n = min(labels.count(), 50)
    for i in range(n):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=400) or "").strip().lower()
        except Exception:
            continue
        if not text or len(text) > 80:
            continue
        for pat, val in pairs:
            if re.search(pat, text, re.I):
                try:
                    for_id = lab.get_attribute("for")
                    ctrl = (
                        page.locator(f'[id="{for_id}"]').first
                        if for_id
                        else lab.locator("xpath=following::*[self::input or self::textarea or self::select][1]").first
                    )
                    if not ctrl.count():
                        continue
                    tag = ctrl.evaluate("e => e.tagName.toLowerCase()")
                    if tag == "select":
                        try:
                            ctrl.select_option(label=re.compile(re.escape(val), re.I))
                        except Exception:
                            pass
                    else:
                        ctrl.fill(val)
                except Exception:
                    pass
                break


def looks_submitted(page: Page) -> bool:
    body = ""
    try:
        body = page.locator("body").inner_text()[:6000]
    except Exception:
        return False
    return bool(
        re.search(
            r"application (has been )?submitted|thank you for (your )?appl|"
            r"we (have )?received your (application|appl)|application received|"
            r"successfully applied|your application was sent",
            body,
            re.I,
        )
    )


def blocked_wall(page: Page) -> str | None:
    body = ""
    try:
        body = page.locator("body").inner_text()[:4000]
    except Exception:
        return None
    if re.search(r"captcha|verify you are human|cloudflare", body, re.I):
        return "CAPTCHA/bot wall"
    if re.search(r"sign in to continue|log in to apply|create an account|sign in with", body, re.I):
        # Greenhouse/Lever often need account — still try as guest first
        if page.locator("input[type='email'], input[name*='email']").count() == 0:
            return "login/account wall"
    return None


def try_submit(page: Page) -> bool:
    for name in (
        "Submit application",
        "Submit Application",
        "Submit",
        "Apply",
        "Send application",
        "Continue",
        "Next",
        "Save and Continue",
    ):
        try:
            btn = page.get_by_role("button", name=re.compile(rf"^{re.escape(name)}$", re.I))
            for i in range(min(btn.count(), 3)):
                b = btn.nth(i)
                if b.is_visible() and b.is_enabled():
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    time.sleep(1.5)
                    return True
        except Exception:
            continue
    return False


def process_external(page: Page, job: dict) -> ExtResult:
    res = ExtResult(
        status="blocked",
        company=job.get("company", ""),
        role=job.get("role", ""),
        job_id=job.get("job_id", ""),
        location=job.get("location", ""),
        url=job.get("url", ""),
    )
    jid = res.job_id
    view = f"https://www.linkedin.com/jobs/view/{jid}/"
    print(f"EXTERNAL {res.company} | {res.role} | {jid}", flush=True)
    page.goto(view, wait_until="domcontentloaded", timeout=60000)
    time.sleep(2.5)

    # Location hard check again
    loc = res.location or ""
    try:
        top = page.locator(".job-details-jobs-unified-top-card__container, .jobs-unified-top-card").first
        if top.count():
            loc = (top.inner_text(timeout=2000) or "")[:400]
            res.location = loc
    except Exception:
        pass
    if SKIP_COMPANY_LOC.search(loc) and not re.search(r"\bremote\b|\bwfh\b", loc, re.I):
        res.status = "skipped"
        res.reason = f"location filter: {loc[:100]}"
        print(f"  SKIP location {loc[:80]}", flush=True)
        return res

    # Click Apply (not Easy Apply). LinkedIn 2026 may drop .jobs-apply-button classes.
    apply_btn = None
    try:
        ea = page.get_by_role("button", name=re.compile(r"Easy Apply", re.I))
        if ea.count() and ea.first.is_visible():
            res.status = "skipped"
            res.reason = "became Easy Apply"
            return res
    except Exception:
        pass
    try:
        role_apply = page.get_by_role("button", name=re.compile(r"^Apply$", re.I))
        if role_apply.count() and role_apply.first.is_visible():
            apply_btn = role_apply.first
    except Exception:
        pass
    if not apply_btn:
        for sel in [
            "button[aria-label*='Apply to']",
            "button.jobs-apply-button",
            "a.jobs-apply-button",
            "button:has-text('Apply')",
            "a:has-text('Apply')",
        ]:
            locb = page.locator(sel).first
            try:
                if locb.count() and locb.is_visible():
                    label = ((locb.inner_text() or "") + " " + (locb.get_attribute("aria-label") or "")).lower()
                    if "easy apply" in label:
                        res.status = "skipped"
                        res.reason = "became Easy Apply"
                        return res
                    if "apply" in label:
                        apply_btn = locb
                        break
            except Exception:
                continue
    if not apply_btn:
        res.status = "skipped"
        res.reason = "no external Apply button"
        return res

    before = {p for p in page.context.pages}
    try:
        with page.context.expect_page(timeout=8000) as new_page_info:
            apply_btn.click(timeout=5000)
        ats = new_page_info.value
    except Exception:
        # Same-tab redirect
        time.sleep(2)
        ats = page
        # Or find newly opened
        after = page.context.pages
        for p in after:
            if p not in before and p != page:
                ats = p
                break

    try:
        ats.wait_for_load_state("domcontentloaded", timeout=30000)
    except Exception:
        pass
    time.sleep(2)
    ats_url = ats.url
    res.path = ats_url
    print(f"  ATS {ats_url[:140]}", flush=True)

    if "linkedin.com" in ats_url and "jobs" in ats_url:
        res.status = "blocked"
        res.reason = "did not leave LinkedIn"
        return res

    t0 = time.time()
    wall = blocked_wall(ats)
    if wall and "login" in wall:
        # try once more after short wait
        time.sleep(1.5)
        wall = blocked_wall(ats)
    if wall == "CAPTCHA/bot wall":
        res.status = "blocked"
        res.reason = wall
        shot(ats, f"ext-blocked-{jid}.png")
        return res

    steps = 0
    while time.time() - t0 < ATS_TIME_CAP_S and steps < 12:
        if looks_submitted(ats):
            res.status = "submitted"
            res.reason = "ATS confirmation"
            shot(ats, f"ext-submitted-{jid}.png")
            print("  -> submitted", flush=True)
            return res
        wall = blocked_wall(ats)
        if wall == "CAPTCHA/bot wall":
            res.status = "blocked"
            res.reason = wall
            shot(ats, f"ext-blocked-{jid}.png")
            return res
        fill_common(ats)
        # Upload canonical resume when ATS file input appears
        try:
            resume = resume_upload_path()
            for sel in ("#resume", "input[type=file]", "input[name*=resume i]", "input[accept*='pdf']"):
                floc = ats.locator(sel).first
                if floc.count():
                    try:
                        floc.set_input_files(resume, timeout=15000)
                        break
                    except Exception:
                        continue
        except Exception as e:
            print("resume upload note:", e)
        # file upload skip if required without resume on disk
        advanced = try_submit(ats)
        steps += 1
        if not advanced:
            # click primary-looking buttons
            try:
                primary = ats.locator("button[type='submit'], input[type='submit']").first
                if primary.count() and primary.is_visible():
                    primary.click(timeout=3000)
                    time.sleep(1.5)
                    advanced = True
            except Exception:
                pass
        if not advanced:
            break
        time.sleep(1.2)

    if looks_submitted(ats):
        res.status = "submitted"
        res.reason = "ATS confirmation"
        shot(ats, f"ext-submitted-{jid}.png")
        print("  -> submitted", flush=True)
        return res

    res.status = "blocked"
    res.reason = f"stuck/time cap after {steps} steps on {urlparse(ats_url).netloc}"
    shot(ats, f"ext-blocked-{jid}.png")
    print(f"  -> blocked: {res.reason}", flush=True)
    # Close ATS tab if separate
    try:
        if ats != page and not ats.is_closed():
            ats.close()
    except Exception:
        pass
    return res


def main() -> None:
    data = json.loads(REPORT_IN.read_text())
    by_id = {c["job_id"]: c for c in data.get("external_candidates", []) if c.get("job_id")}
    # Priority IDs always (even if not in today's Easy Apply scan), then today's externals
    ordered: list[str] = []
    for jid in PRIORITY_IDS:
        if jid not in ordered:
            ordered.append(jid)
    for jid in by_id:
        if jid not in ordered:
            ordered.append(jid)
    results: list[ExtResult] = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.bring_to_front()
        done = 0
        for jid in ordered:
            if done >= MAX_EXTERNAL:
                break
            job = by_id.get(jid)
            if not job:
                # Still try priority IDs even if not in today's scan
                if jid in PRIORITY_IDS:
                    job = {"job_id": jid, "company": "", "role": "", "location": "", "url": f"https://www.linkedin.com/jobs/view/{jid}/"}
                else:
                    continue
            r = process_external(page, job)
            results.append(r)
            if r.status in ("submitted", "blocked", "skipped"):
                done += 1
            time.sleep(1)

    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "submitted": [asdict(r) for r in results if r.status == "submitted"],
        "blocked": [asdict(r) for r in results if r.status == "blocked"],
        "skipped": [asdict(r) for r in results if r.status == "skipped"],
        "all": [asdict(r) for r in results],
    }
    REPORT_OUT.write_text(json.dumps(out, indent=2))
    print("=== EXTERNAL SUMMARY ===")
    print("submitted", len(out["submitted"]))
    print("blocked", len(out["blocked"]))
    print("skipped", len(out["skipped"]))
    print("wrote", REPORT_OUT)


if __name__ == "__main__":
    main()
