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
    from tools.ats.complete import extract_hop_destination_from_url, extract_offsite_from_text
except Exception:  # pragma: no cover
    def extract_hop_destination_from_url(url):
        return ""

    def extract_offsite_from_text(blob, *, reject_hosts=("linkedin.com",)):
        return ""

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

try:
    from tools.linkedin.safety import pause_status, safe_int
except Exception:
    from safety import pause_status, safe_int  # type: ignore

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
REPORT_IN = Path(os.environ.get("LINKEDIN_APPLY_REPORT", str(_ART / "apply-report.json")))
REPORT_OUT = Path(
    os.environ.get("LINKEDIN_EXTERNAL_REPORT", str(_ART / "external-apply-report.json"))
)
SCREEN_DIR = _ART

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
    "4443293962",  # Palo Alto Principal Software Architect Hyd
    "4448608798",  # Convatec Solution Architect Hyd
    "4400708113",  # ModMed Senior Software Architect Hyd
    "4451327394",  # Quik Hire .NET Remote
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


def external_candidates_from_report(data) -> list[dict]:
    """Normalize current and legacy Easy Apply report shapes."""
    if isinstance(data, dict):
        candidates = data.get("external_candidates", [])
    elif isinstance(data, list):
        candidates = [
            item
            for item in data
            if isinstance(item, dict)
            and item.get("job_id")
            and str(item.get("path", "")).lower() in {"external", "company", "ats", "company_website"}
        ]
    else:
        raise TypeError(f"unsupported LinkedIn report shape: {type(data).__name__}")
    return [c for c in candidates if isinstance(c, dict)]

SKIP_COMPANY_LOC = re.compile(
    r"pune|noida|bengaluru|bangalore|delhi|chennai|mumbai|gurgaon|gurugram|"
    r"indore|بنغالور|مومباي|دلهي|تشيناي|بوني|إندور",
    re.I,
)
MAX_EXTERNAL = int(os.environ.get("LINKEDIN_MAX_EXTERNAL", str(safe_int("maxExternal", 5))))
ATS_TIME_CAP_S = int(os.environ.get("LINKEDIN_ATS_TIME_CAP_S", "390"))  # Workday needs ~6.5m
INCLUDE_PRIORITY_IDS = (os.environ.get("LINKEDIN_INCLUDE_PRIORITY_IDS") or "").strip().lower() in (
    "1",
    "true",
    "yes",
)


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


def write_safety_pause_report(status) -> None:
    row = ExtResult(
        status="blocked",
        reason="linkedin_safety_pause",
        url=status.pause_until_utc or "",
        path=status.source,
    )
    out = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "submitted": [],
        "blocked": [asdict(row)],
        "skipped": [],
        "all": [asdict(row)],
        "safety": {
            "active": True,
            "reason": status.reason,
            "pauseUntilUtc": status.pause_until_utc,
            "secondsRemaining": status.seconds_remaining,
            "source": status.source,
        },
    }
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps(out, indent=2))
    print(
        f"LINKEDIN SAFETY PAUSE: {status.reason} "
        f"(until {status.pause_until_utc or 'manual re-enable'})",
        flush=True,
    )
    print(f"wrote {REPORT_OUT}", flush=True)


def shot(page: Page, name: str) -> None:
    try:
        page.screenshot(path=str(SCREEN_DIR / name), full_page=False)
    except Exception:
        pass


def _complete_ats(page: Page, time_cap_s: int) -> tuple[str, str]:
    try:
        from tools.ats.complete import complete_ats
    except Exception:
        from ats.complete import complete_ats  # type: ignore
    return complete_ats(page, time_cap_s=time_cap_s)


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


def extract_linkedin_offsite_url(page: Page, apply_href: str = "", current_url: str = "") -> str:
    """Resolve the employer ATS URL when Apply does not leave LinkedIn."""
    href = (apply_href or "").strip()
    if href.startswith("http") and "linkedin.com" not in href.lower():
        return href
    hop = extract_hop_destination_from_url(href or current_url)
    if hop:
        return hop
    try:
        opened = page.evaluate("() => (window.__liOpenedUrls || []).slice()") or []
        for u in opened:
            u = str(u or "").strip()
            if u.startswith("http") and "linkedin.com" not in u.lower():
                return u
    except Exception:
        pass
    try:
        hrefs = page.evaluate(
            """() => {
              const out = [];
              const sels = [
                "a[data-tracking-control-name*='apply']",
                "a[aria-label*='Apply on company']",
                "a.jobs-apply-button[href]",
                "a[href*='companyApply']",
              ];
              for (const sel of sels) {
                for (const a of document.querySelectorAll(sel)) {
                  const h = a.href || a.getAttribute("href") || "";
                  if (h.startsWith("http") && !/linkedin\\.com/i.test(h)) out.push(h);
                }
              }
              for (const a of document.querySelectorAll("a[href^='http']")) {
                const h = a.href || "";
                const label = ((a.innerText || "") + " " + (a.getAttribute("aria-label") || "")).toLowerCase();
                if (!h || /linkedin\\.com/i.test(h)) continue;
                if (/apply|career|workday|greenhouse|lever|smartrecruiters|ashby|icims/i.test(h + " " + label))
                  out.push(h);
              }
              return out;
            }"""
        ) or []
        for h in hrefs:
            h = str(h or "").strip()
            if h.startswith("http") and "linkedin.com" not in h.lower():
                return h
    except Exception:
        pass
    try:
        blob = page.evaluate("() => document.documentElement.innerHTML.slice(0, 500000)") or ""
    except Exception:
        blob = ""
    return extract_offsite_from_text(blob, reject_hosts=("linkedin.com",))


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
    navigated = False
    last_err = ""
    for nav_try in range(3):
        try:
            page.goto(view, wait_until="domcontentloaded", timeout=60000)
            navigated = True
            break
        except Exception as e:
            last_err = str(e)[:220]
            print(f"  WARN: job view goto failed (try {nav_try + 1}/3): {last_err}", flush=True)
            time.sleep(3 + nav_try * 5)
            try:
                page.goto(
                    "https://www.linkedin.com/feed/",
                    wait_until="domcontentloaded",
                    timeout=45000,
                )
                time.sleep(2)
            except Exception:
                pass
    if not navigated:
        res.status = "blocked"
        res.reason = f"goto failed: {last_err}"
        print(f"  -> blocked: {res.reason}", flush=True)
        return res
    time.sleep(2.5)

    url_l = (page.url or "").lower()
    if re.search(r"/login|authwall|/checkpoint|uas/login", url_l):
        res.status = "blocked"
        res.reason = "linkedin_login_required"
        print(f"  -> blocked: {res.reason} ({(page.url or '')[:120]})", flush=True)
        return res

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

    # Click Apply (not Easy Apply) — 2026 UI uses hashed <a aria-label="Apply on company website">
    apply_btn = None
    for sel in [
        "a[aria-label*='Apply on company website']",
        "button[aria-label*='Apply on company website']",
        "a[data-tracking-control-name*='apply']",
        "button[data-tracking-control-name*='apply']",
        "button.jobs-apply-button",
        "a.jobs-apply-button",
        "button:has-text('Apply')",
        "a:has-text('Apply')",
        "a[aria-label*='Apply']",
        "button[aria-label*='Apply']",
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

    apply_href = ""
    try:
        apply_href = (apply_btn.get_attribute("href") or "").strip()
    except Exception:
        apply_href = ""

    try:
        page.evaluate(
            """() => {
              if (window.__liOpenHooked) return;
              window.__liOpenHooked = true;
              window.__liOpenedUrls = window.__liOpenedUrls || [];
              const orig = window.open;
              window.open = function (url, ...rest) {
                try { if (url) window.__liOpenedUrls.push(String(url)); } catch (_) {}
                return orig.apply(this, [url, ...rest]);
              };
            }"""
        )
    except Exception:
        pass

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

    if "linkedin.com" in (ats_url or "") and "jobs" in (ats_url or ""):
        # 2026 UI often keeps the job view and puts the real ATS on href / JSON / window.open.
        offsite = extract_linkedin_offsite_url(page, apply_href, ats_url)
        if offsite:
            try:
                ats.goto(offsite, wait_until="domcontentloaded", timeout=60000)
                time.sleep(1.5)
                ats_url = ats.url
                res.path = ats_url
                print(f"  ATS href {ats_url[:140]}", flush=True)
            except Exception as e:
                res.status = "blocked"
                res.reason = f"did not leave LinkedIn ({e})"
                return res
        if "linkedin.com" in (ats_url or ""):
            res.status = "blocked"
            res.reason = "did not leave LinkedIn"
            return res

    # JD-tailor resume before ATS upload (tools.ats.complete uses resume_upload_path)
    try:
        from tools.resume_paths import clear_active_resume, set_active_resume
        from tools.resume_tailor import tailor_resume_for_job

        jd = ""
        try:
            jd = page.locator(
                "#job-details, .jobs-description__content, .jobs-box__html-content, "
                ".jobs-description-content__text"
            ).first.inner_text(timeout=2500)
        except Exception:
            jd = ""
        if not res.role:
            try:
                res.role = (
                    page.locator("h1, .job-details-jobs-unified-top-card__job-title").first.inner_text(
                        timeout=1500
                    )
                    or ""
                ).strip()[:160]
            except Exception:
                pass
        tailored = tailor_resume_for_job(
            job_id=jid,
            title=res.role or job.get("role", ""),
            company=res.company or job.get("company", ""),
            jd=jd,
        )
        set_active_resume(tailored)
    except Exception as tailor_err:
        print(f"  WARN: resume tailor skipped: {str(tailor_err)[:120]}", flush=True)

    try:
        status, reason = _complete_ats(ats, ATS_TIME_CAP_S)
    finally:
        try:
            from tools.resume_paths import clear_active_resume

            clear_active_resume()
        except Exception:
            pass
    if status == "applied":
        res.status = "submitted"
        res.reason = reason or "ATS confirmation"
        shot(ats, f"ext-submitted-{jid}.png")
        print("  -> submitted", flush=True)
        return res
    if status == "skipped":
        res.status = "skipped"
        res.reason = reason
        print(f"  -> skipped: {res.reason}", flush=True)
        return res

    res.status = "blocked"
    res.reason = reason or f"stuck/time cap on {urlparse(ats_url).netloc}"
    shot(ats, f"ext-blocked-{jid}.png")
    print(f"  -> blocked: {res.reason}", flush=True)
    try:
        if ats != page and not ats.is_closed():
            ats.close()
    except Exception:
        pass
    return res


def main() -> None:
    safety = pause_status()
    if safety.active:
        write_safety_pause_report(safety)
        return

    if REPORT_IN.is_file():
        data = json.loads(REPORT_IN.read_text())
    else:
        print(f"NOTE: missing {REPORT_IN} — no external candidates loaded", flush=True)
        data = {"external_candidates": []}
    by_id = {c["job_id"]: c for c in external_candidates_from_report(data) if c.get("job_id")}
    # Priority first (even if missing from today's Easy Apply scan), then remaining externals
    ordered: list[str] = []
    if INCLUDE_PRIORITY_IDS:
        for jid in PRIORITY_IDS:
            if jid not in ordered:
                ordered.append(jid)
    for jid in by_id:
        if jid not in ordered:
            ordered.append(jid)
    results: list[ExtResult] = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP)
        except Exception as e:
            results.append(
                ExtResult(status="blocked", reason=f"CDP connect failed: {str(e)[:180]}")
            )
            out = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "submitted": [],
                "blocked": [asdict(r) for r in results],
                "skipped": [],
                "all": [asdict(r) for r in results],
            }
            REPORT_OUT.write_text(json.dumps(out, indent=2))
            print(f"BLOCKED: CDP connect failed: {e}", flush=True)
            raise SystemExit(5)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.bring_to_front()
        # Auth gate — do not burn PRIORITY_IDS as false "no external Apply button"
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
        except Exception:
            pass
        url_l = (page.url or "").lower()
        body = ""
        try:
            body = page.locator("body").inner_text()[:2000]
        except Exception:
            body = ""
        try:
            has_li_at = any(c.get("name") == "li_at" for c in context.cookies(["https://www.linkedin.com"]))
        except Exception:
            has_li_at = False
        login_wall = bool(re.search(r"/login|authwall|/checkpoint|uas/login", url_l)) or (
            bool(re.search(r"Sign in\n|Email or phone|Welcome Back", body))
            and not re.search(r"Start a post|My Network|Notifications", body, re.I)
        )
        if login_wall or not has_li_at:
            results.append(
                ExtResult(
                    status="blocked",
                    reason="linkedin_login_required",
                    url=page.url or "",
                )
            )
            out = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "submitted": [],
                "blocked": [asdict(r) for r in results],
                "skipped": [],
                "all": [asdict(r) for r in results],
            }
            REPORT_OUT.write_text(json.dumps(out, indent=2))
            print("BLOCKED: not signed in (linkedin_login_required)", flush=True)
            raise SystemExit(5)
        done = 0
        for jid in ordered:
            if done >= MAX_EXTERNAL:
                break
            job = by_id.get(jid)
            if not job:
                # Only try static priority IDs when explicitly enabled.
                if INCLUDE_PRIORITY_IDS and jid in PRIORITY_IDS:
                    job = {
                        "job_id": jid,
                        "company": "",
                        "role": "",
                        "location": "",
                        "url": f"https://www.linkedin.com/jobs/view/{jid}/",
                    }
                else:
                    continue
            try:
                r = process_external(page, job)
                results.append(r)
                if r.status in ("submitted", "blocked", "skipped"):
                    done += 1
            except Exception as e:
                results.append(
                    ExtResult(
                        status="blocked",
                        job_id=str(job.get("job_id") or jid),
                        reason=f"uncaught: {e}",
                    )
                )
                done += 1
                print(f"  -> blocked uncaught: {e}", flush=True)
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
