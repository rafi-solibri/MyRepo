#!/usr/bin/env python3
"""Complete company-website / ATS applications (Workday, Greenhouse, generic).

Used by LinkedIn, Hitech City, Indeed, and any Playwright page that lands on
an employer ATS. Never invents success — confirmation text only.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from tools.resume_paths import resume_upload_path
except Exception:  # pragma: no cover
    def resume_upload_path():
        for c in (
            "/workspace/resumes/Rafi_Resume.docx",
            "/home/ubuntu/resumes/Rafi_Resume.docx",
            "/home/ubuntu/Documents/Rafi_Resume.docx",
        ):
            if Path(c).is_file():
                return c
        raise FileNotFoundError("Rafi_Resume.docx missing")


PROFILE = {
    "first": "Mohammed Abdul Rafi",
    "last": "Ahmed",
    "full": "Mohammed Abdul Rafi Ahmed",
    "email": "",
    "phone": "8790251698",
    "linkedin": "https://linkedin.com/in/rafi-ahmed-mohammed-abdul-151644ba",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "postal": "500032",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "notice": "0",
    "experience_years": "15",
    "school": "Acharya Nagarjuna University",
    # Preferred answers for Source / How did you hear dropdowns (try in order).
    "source": "LinkedIn",
}

# Source / "how did you hear" option matchers — LinkedIn first (owner preference).
SOURCE_OPTION_PATTERNS = [
    r"^LinkedIn$",
    r"\bLinkedIn\b",
    r"^Job Board$",
    r"\bNaukri\b",
    r"\bIndeed\b",
    r"Company Websites?",
    r"^Internet$",
    r"^Online$",
    r"Social Media",
    r"^Other$",
]
SOURCE_LABEL_RE = re.compile(
    r"^(source|candidate source|application source)$|"
    r"how did you (hear|find|learn)|hear about (us|this|the)|"
    r"where did you hear|referral source|sourcing channel|"
    r"how were you referred",
    re.I,
)

SUBMITTED_RE = re.compile(
    r"application (has been )?submitted|thank you for (your )?appl|"
    r"we (have )?received your (application|appl)|application received|"
    r"successfully (applied|submitted)|your application was sent|"
    r"application complete|you have successfully applied|"
    r"thanks for (your )?interest|application has been received|"
    r"you('re| are) all set|applied successfully|"
    r"application was successfully submitted|thanks for applying|"
    r"we('ve| have) got your application|"
    r"application was submitted successfully|"
    r"you are currently submitted to this job",
    re.I,
)

UNAVAILABLE_RE = re.compile(
    r"maintenance-page|scheduled maintenance|we('ll| will) be back|"
    r"this site is temporarily unavailable|community\.workday\.com/maintenance|"
    r"this job is no longer|position has been filled|"
    r"no longer accepting applications|requisition is closed|"
    r"job is no longer available|"
    r"403 forbidden|\berror 403\b|access denied",
    re.I,
)

BOARD_TRACKING_RE = re.compile(
    r"indeed\.com/(?:applystart|rc/clk|pagead|viewjob|clk)|"
    r"linkedin\.com/jobs/(?:view|search)|"
    r"naukri\.com/job-listings|"
    r"foundit\.in/job/",
    re.I,
)

SSO_HOST_RE = re.compile(
    r"b2clogin\.com|login\.microsoftonline|accounts\.google\.com|okta\.com|"
    r"auth0\.com|passport\.amazon\.jobs|secure\.indeed\.com/(?:auth|account|oauth)|"
    r"signin\.aws|login\.microsoft|oneclick\.smartrecruiters|"
    r"login\.cognizant|cognizant\.okta|talent\.cognizant\.com/[^?\s]*(?:login|login2)|"
    r"eightfold\.ai/(?:login|signin|auth)",
    re.I,
)

WORKDAY_HOST_RE = re.compile(
    r"myworkdayjobs\.com|myworkdaysite\.com|workdayjobs|wd\d*\.myworkday",
    re.I,
)

GREENHOUSE_HOST_RE = re.compile(
    r"greenhouse\.io|job-boards\.greenhouse|smartrecruiters\.com|lever\.co|"
    r"ashbyhq\.com|icims\.com|taleo\.net|successfactors|oraclecloud\.com|"
    r"phenompeople|eightfold\.ai",
    re.I,
)

FALSE_APPLY_CTA_RE = re.compile(
    r"view applied|applied jobs|already applied|my applications|"
    r"see (all )?applied|applications? sent",
    re.I,
)

BROCHURE_URL_RE = re.compile(
    r"/careers\.html(?:$|[?#])|/about(?:-us)?(?:/|$)|/life-at|/why[- ]join|"
    r"/join[- ]us(?:\.html)?(?:$|[?#])|/our[- ]team|/culture(?:/|$)|"
    r"/careers/?$|/careers/?[?#]|/jobs/?$|/job-openings/?$",
    re.I,
)

JOB_DETAIL_URL_RE = re.compile(
    r"/job/|/jobs/\d|gh_jid=|requisition|reqid=|pid=\d|"
    r"myworkdayjobs|greenhouse\.io|lever\.co|smartrecruiters|ashbyhq|icims|eightfold",
    re.I,
)

BROCHURE_TEXT_RE = re.compile(
    r"join our (growing )?team|life at |why (work|join) (at|us)|"
    r"we('re| are) hiring|see (all )?(open )?(roles|positions|jobs)|"
    r"explore (our )?(careers|opportunities)|view (all )?openings",
    re.I,
)

ATS_FORM_HINT_RE = re.compile(
    r"submit application|apply for this job|upload (your )?resume|"
    r"cover letter|work history|autofill with resume|apply manually|"
    r"first name|email address",
    re.I,
)

HOP_QUERY_KEYS = (
    "continueUrl",
    "continue_url",
    "dest",
    "destination",
    "redirect_url",
    "redirectUrl",
    "url",
    "u",
    "r",
    "continue",
    "target",
)

CAPTCHA_CHALLENGE_HOSTS = (
    "hcaptcha.com",
    "challenges.cloudflare.com",
    "funcaptcha",
    "captcha-delivery.com",
    "datadome.co",
)

DEFAULT_TIME_CAP_S = int(os.environ.get("ATS_TIME_CAP_S", "390"))


def _alias_owner_secrets() -> None:
    """Copy the one env password/email onto the names every helper reads."""
    pw = ""
    for key in (
        "WORKDAY_PASSWORD",
        "ATS_PASSWORD",
        "NAUKRI_WORKDAY_PASSWORD",
        "NAUKRI_ATS_PASSWORD",
        "LINKEDIN_PASSWORD",
    ):
        pw = (os.environ.get(key) or "").strip()
        if pw:
            break
    if pw:
        os.environ.setdefault("WORKDAY_PASSWORD", pw)
        os.environ.setdefault("ATS_PASSWORD", pw)
    email = ""
    for key in ("APPLY_EMAIL", "NAUKRI_APPLY_EMAIL", "LINKEDIN_EMAIL"):
        email = (os.environ.get(key) or "").strip()
        if email and "@" in email:
            break
        email = ""
    if email:
        os.environ.setdefault("APPLY_EMAIL", email)
        os.environ.setdefault("NAUKRI_APPLY_EMAIL", email)


_alias_owner_secrets()


def ats_email() -> str:
    _alias_owner_secrets()
    for key in ("APPLY_EMAIL", "NAUKRI_APPLY_EMAIL", "LINKEDIN_EMAIL"):
        val = (os.environ.get(key) or "").strip()
        if val and "@" in val:
            return val
    return (PROFILE.get("email") or "").strip()


def ats_password() -> str:
    _alias_owner_secrets()
    for key in (
        "WORKDAY_PASSWORD",
        "ATS_PASSWORD",
        "NAUKRI_WORKDAY_PASSWORD",
        "NAUKRI_ATS_PASSWORD",
        "LINKEDIN_PASSWORD",
    ):
        val = (os.environ.get(key) or "").strip()
        if val:
            return val
    return ""


def workday_compliant_password(raw: str) -> str:
    """Deterministic Workday-safe password (12+, upper, lower, digit, special).

    Same input always yields the same output so Sign In matches Create Account
    across runs. If the secret already meets common tenant rules, return it.
    """
    pw = (raw or "").strip()
    if (
        len(pw) >= 12
        and re.search(r"[A-Z]", pw)
        and re.search(r"[a-z]", pw)
        and re.search(r"[0-9]", pw)
        and re.search(r"[^A-Za-z0-9]", pw)
    ):
        return pw
    extra = ""
    if not re.search(r"[A-Z]", pw):
        extra += "A"
    if not re.search(r"[a-z]", pw):
        extra += "a"
    if not re.search(r"[0-9]", pw):
        extra += "1"
    if not re.search(r"[^A-Za-z0-9]", pw):
        extra += "!"
    pw = pw + extra
    if len(pw) < 12:
        pw = (pw + "Aa1!")[:12] if len(pw) + 4 >= 12 else pw + "Aa1!"
        while len(pw) < 12:
            pw += "x"
    return pw


def owner_asleep() -> bool:
    """True when the owner cannot solve captchas / finish forms right now.

    Cloud overnight / cron runs set ``HITECHCITY_OWNER_ASLEEP=1`` or touch
    ``/tmp/hitechcity-owner-asleep``. Short waits + no long persist retries so
    volume moves to the next campus company / Easy Apply / boards.
    """
    for key in ("HITECHCITY_OWNER_ASLEEP", "ATS_OWNER_ASLEEP"):
        if (os.environ.get(key) or "").strip().lower() in ("1", "true", "yes"):
            return True
    for path in ("/tmp/hitechcity-owner-asleep", "/tmp/ats-owner-asleep"):
        try:
            if Path(path).exists():
                return True
        except Exception:
            continue
    return False


def persist_retry_burst_sec() -> int:
    """Seconds for post-ASK_OWNER fill bursts. Owner-asleep → brief park only."""
    raw = (os.environ.get("ATS_PERSIST_RETRY_SEC") or "").strip()
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return 0
    if owner_asleep() or (os.environ.get("HITECHCITY_ATS_PERSIST_RETRY") or "1").strip() in (
        "0",
        "false",
        "no",
    ):
        return 12
    return 45


def is_hard_ats_wall(reason: str | None) -> bool:
    """True only for walls that will repeat for the same company this run.

    Timeouts / incomplete forms must NOT trip a per-company wall cap — that
    previously stopped all remaining externals after the first Workday miss.
    """
    why = (reason or "").lower()
    if not why:
        return False
    if any(
        x in why
        for x in (
            "incomplete",
            "timeout",
            "time_cap",
            "stuck",
            "errors found",
            "job_closed",
            "unavailable",
            "maintenance",
            "did_not_leave",
            "no_ats_form",
            "brochure",
        )
    ):
        return False
    return any(
        x in why
        for x in (
            "captcha",
            "login",
            "account wall",
            "ats_login_wall",
            "ats_password_missing",
            "ats_email_missing",
            "sso",
            "email_otp",
            "otp_wall",
        )
    )


def is_submitted_text(text: str | None) -> bool:
    return bool(SUBMITTED_RE.search(text or ""))


ALREADY_APPLIED_RE = re.compile(
    r"you have already applied|already applied to this (job|position|requisition)|"
    r"you previously applied|application is already (in progress|submitted)|"
    r"you applied for this job|this requisition is already|"
    r"you are currently submitted to this job|currently submitted to this job",
    re.I,
)


def looks_already_applied(page) -> bool:
    return bool(ALREADY_APPLIED_RE.search(_body(page, 4000)))


def looks_like_apply_cta(label: str | None) -> bool:
    """True for a real Apply/Submit CTA — not 'View applied jobs' chrome."""
    t = re.sub(r"\s+", " ", label or "").strip()
    if not t:
        return False
    if FALSE_APPLY_CTA_RE.search(t):
        return False
    if re.search(r"sign in|log in|create account", t, re.I) and not re.search(r"^apply", t, re.I):
        return False
    if re.search(r"with (indeed|linkedin|google|microsoft|facebook|apple)", t, re.I) and not re.search(
        r"without indeed", t, re.I
    ):
        return False
    return bool(re.search(r"\bapply\b|i'?m interested|start application|submit application", t, re.I))


def is_brochure_or_dead_end(
    url: str | None,
    text: str | None,
    *,
    has_file: bool = False,
    has_wd: bool = False,
    has_email: bool = False,
    has_password: bool = False,
    has_apply_cta: bool = False,
) -> bool:
    """Marketing /careers.html pages with no ATS form — fail fast, do not burn 6.5m."""
    if has_file or has_wd or has_email or has_password or has_apply_cta:
        return False
    u = url or ""
    t = text or ""
    if JOB_DETAIL_URL_RE.search(u) and ATS_FORM_HINT_RE.search(t):
        return False
    if BROCHURE_URL_RE.search(u):
        return True
    if BROCHURE_TEXT_RE.search(t) and not ATS_FORM_HINT_RE.search(t):
        return True
    if re.search(r"careers|jobs|join-us|about", u, re.I) and not ATS_FORM_HINT_RE.search(t) and not JOB_DETAIL_URL_RE.search(u):
        return True
    return False


def unescape_json_url(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except Exception:
        return (raw or "").replace("\\u002f", "/").replace("\\/", "/")


def extract_offsite_from_text(
    blob: str | None,
    *,
    reject_hosts: tuple[str, ...] = ("linkedin.com",),
) -> str:
    """Pull companyApplyUrl / applyUrl from LinkedIn (or similar) page JSON."""
    text = blob or ""
    if not text:
        return ""
    keys = (
        "companyApplyUrl",
        "companyApplyURL",
        "offsiteApplyUrl",
        "externalApplyUrl",
        "companyJobApplyUrl",
    )
    for key in keys:
        m = re.search(rf'"{key}"\s*:\s*"(https?:[^"]+)"', text, re.I)
        if not m:
            continue
        url = unescape_json_url(m.group(1))
        if not url.startswith("http"):
            continue
        low = url.lower()
        if any(h in low for h in reject_hosts):
            continue
        return url
    return ""


def extract_hop_destination_from_url(url: str | None) -> str:
    """Indeed/LinkedIn tracking hops often stash the real ATS in a query param."""
    raw = url or ""
    if not raw:
        return ""
    try:
        q = parse_qs(urlparse(raw).query)
    except Exception:
        return ""
    for key in HOP_QUERY_KEYS:
        vals = q.get(key) or []
        for val in vals:
            dest = unquote(val or "")
            if not dest.startswith("http"):
                continue
            if is_board_tracking_url(dest):
                continue
            if re.search(r"indeed\.com/|linkedin\.com/jobs|naukri\.com|foundit\.in", dest, re.I):
                continue
            return dest
    return ""


def extract_hop_destination(page) -> str:
    """Resolve the employer ATS URL from a board tracking hop page."""
    dest = extract_hop_destination_from_url(getattr(page, "url", "") or "")
    if dest:
        return dest
    try:
        content = page.locator("meta[http-equiv='refresh']").first.get_attribute("content") or ""
        m = re.search(r"url\s*=\s*(.+)", content, re.I)
        if m:
            cand = m.group(1).strip().strip("'\"")
            if cand.startswith("http") and not is_board_tracking_url(cand):
                return cand
    except Exception:
        pass
    try:
        cand = page.evaluate(
            """() => {
              const opened = window.__atsOpenedUrls || window.__naukriOpenedUrls || window.__liOpenedUrls || [];
              for (const u of opened) {
                if (u && /^https?:/i.test(u) && !/indeed\\.com\\/(?:applystart|rc\\/clk)|linkedin\\.com\\/jobs|naukri\\.com/i.test(u))
                  return u;
              }
              const meta = document.querySelector("meta[http-equiv='refresh']");
              if (meta) {
                const m = /url\\s*=\\s*(.+)/i.exec(meta.getAttribute("content") || "");
                if (m && /^https?:/i.test(m[1].trim())) return m[1].trim().replace(/^['"]|['"]$/g, "");
              }
              const cands = [...document.querySelectorAll("a[href^='http']")];
              for (const a of cands) {
                const href = a.href || "";
                const label = ((a.innerText || "") + " " + (a.getAttribute("aria-label") || "")).toLowerCase();
                if (/indeed\\.com|linkedin\\.com|naukri\\.com|foundit\\.in/i.test(href)) continue;
                if (/apply|career|workday|greenhouse|lever|smartrecruiters|ashby|icims|eightfold/i.test(href + " " + label))
                  return href;
              }
              return "";
            }"""
        )
        if cand and str(cand).startswith("http") and not is_board_tracking_url(str(cand)):
            return str(cand)
    except Exception:
        pass
    return ""


def classify_ats_host(url: str | None) -> str:
    u = url or ""
    if UNAVAILABLE_RE.search(u):
        return "unavailable"
    if WORKDAY_HOST_RE.search(u):
        return "workday"
    if GREENHOUSE_HOST_RE.search(u):
        return "greenhouse"
    if SSO_HOST_RE.search(u):
        return "sso"
    if re.search(r"linkedin\.com", u, re.I):
        return "linkedin"
    if re.search(r"indeed\.com", u, re.I):
        return "indeed"
    return "generic"


def is_board_tracking_url(url: str | None) -> bool:
    return bool(BOARD_TRACKING_RE.search(url or ""))


def is_unavailable_text(text: str | None) -> bool:
    return bool(UNAVAILABLE_RE.search(text or ""))


def frame_url_is_captcha_challenge(url: str | None) -> bool:
    u = (url or "").lower()
    if any(x in u for x in CAPTCHA_CHALLENGE_HOSTS):
        return True
    if "recaptcha" in u and ("/bframe" in u or "challenge" in u):
        return True
    return False


def iframe_box_is_onscreen(box: dict | None) -> bool:
    if not box:
        return False
    return float(box.get("width") or 0) >= 20 and float(box.get("height") or 0) >= 20


def auth_wall_reason(
    url: str | None,
    text: str | None,
    *,
    has_password: bool = False,
    has_file: bool = False,
    has_workday_apply: bool = False,
    has_email_field: bool = False,
) -> str | None:
    """Return a wall reason, or None when guest/Workday apply can continue."""
    host = classify_ats_host(url)
    if host == "sso":
        return "ats_login_wall"
    blob = f"{url or ''}\n{text or ''}"
    if host == "unavailable" or is_unavailable_text(blob):
        return "job_unavailable"
    # Oracle Careers email OTP — check BEFORE has_file. The verification page still
    # exposes a hidden file input, which previously short-circuited this to None
    # and left persist_retry looping on "Confirm Your Identity".
    if re.search(
        r"confirm your identity|"
        r"verification code was sent|"
        r"the verification code field is required|"
        r"when you get the code, type the code|"
        r"type the code into the field to confirm your identity|"
        r"enter (the )?(one[- ]time|otp|verification) code",
        text or "",
        re.I,
    ):
        return "email_otp_wall"
    if host == "workday" or has_workday_apply:
        # Workday Create Account / Sign In is completable when we have a password
        # and an email field — do NOT treat it as a hard wall.
        if has_workday_apply or has_file or (has_email_field and ats_password()):
            return None
        if has_password and not has_file and not has_email_field:
            return "ats_login_wall"
        return None
    if has_file:
        return None
    # Email-only Eightfold/Phenom SSO (Qualcomm careers/apply) has an email
    # box + "Sign in using Google" and no resume upload — not guest-applyable.
    if re.search(
        r"select a method below to sign in|"
        r"sign in to (continue|apply)|log in to apply|"
        r"sign in using (microsoft|google|linkedin|facebook|apple)|"
        r"if you are a microsoft employee|"
        r"employees must sign in|"
        r"current \w+ employees must sign in|"
        r"we don't recognize this email",
        text or "",
        re.I,
    ):
        return "ats_login_wall"
    return None


def _body(page, limit: int = 4500) -> str:
    chunks: list[str] = []
    try:
        chunks.append(page.locator("body").inner_text(timeout=4000) or "")
    except Exception:
        pass
    try:
        for fr in getattr(page, "frames", []) or []:
            u = (getattr(fr, "url", "") or "").lower()
            if "icims.com" not in u and "in_iframe=1" not in u:
                continue
            try:
                chunks.append(fr.inner_text("body") or "")
            except Exception:
                continue
    except Exception:
        pass
    return "\n".join(chunks)[:limit]


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def page_fingerprint(page) -> str:
    """URL + short body so Apply clicks that do not change the page count as stuck."""
    try:
        url = getattr(page, "url", "") or ""
    except Exception:
        url = ""
    return f"{url}|{_body(page, 600)}"


def looks_submitted(page) -> bool:
    text = _body(page, 7000)
    if is_submitted_text(text):
        return True
    url = getattr(page, "url", "") or ""
    # Oracle Cloud Candidate Experience lands on My Profile after apply.
    if re.search(r"oraclecloud\.com|.*/my-profile", url, re.I) and re.search(
        r"under consideration|active job applications.*applied on",
        text,
        re.I | re.S,
    ):
        return True
    return False


def visible_captcha_challenge(page) -> bool:
    """True only for an on-screen challenge — not invisible widgets or footer badges.

    Invisible hCaptcha always injects ``hcaptcha.com`` frames, and iCIMS footers say
    "Protected by hCaptcha". Treating those as walls caused multi-minute false waits
    and left the real apply form (AMD profile, Oracle sections) abandoned.
    """
    try:
        for fr in getattr(page, "frames", []) or []:
            fu = (getattr(fr, "url", None) or "").lower()
            # Challenge documents only — skip api.js / static checkbox shells.
            if "recaptcha" in fu and ("/bframe" in fu or "challenge" in fu):
                return True
            if "hcaptcha.com" in fu and "challenge" in fu:
                return True
        for sel in (
            "iframe[src*='recaptcha/bframe']",
            "iframe[src*='hcaptcha.com'][src*='challenge']",
            "iframe[src*='challenges.cloudflare.com']",
            "iframe[src*='captcha-delivery.com']",
        ):
            loc = page.locator(sel)
            n = min(loc.count(), 6)
            for i in range(n):
                el = loc.nth(i)
                try:
                    box = el.bounding_box()
                except Exception:
                    box = None
                # Real challenge widgets are large; ignore tiny/invisible hosts.
                if box and float(box.get("width") or 0) >= 100 and float(box.get("height") or 0) >= 60:
                    return True
        # Broad hcaptcha iframes only when clearly on-screen (checkbox / challenge).
        loc = page.locator("iframe[src*='hcaptcha.com']")
        n = min(loc.count(), 8)
        for i in range(n):
            el = loc.nth(i)
            try:
                box = el.bounding_box()
            except Exception:
                box = None
            if box and float(box.get("width") or 0) >= 200 and float(box.get("height") or 0) >= 50:
                return True
        blob = _frames_text(page, 1500)
        if re.search(
            r"verify you are human|press and hold|i'?m not a robot|"
            r"complete the captcha|solve the captcha|attention required",
            blob,
            re.I,
        ):
            return True
    except Exception:
        return False
    return bool(
        re.search(
            r"verify you are human|press and hold|i'?m not a robot",
            _body(page, 1500),
            re.I,
        )
    )


def _frames_text(page, limit: int = 2000) -> str:
    """Main body plus same-origin frame bodies (iCIMS apply lives in iframe)."""
    chunks = [_body(page, limit)]
    try:
        for fr in getattr(page, "frames", []) or []:
            try:
                chunks.append((fr.locator("body").inner_text(timeout=800) or "")[:limit])
            except Exception:
                continue
    except Exception:
        pass
    return "\n".join(chunks)


def prefer_icims_apply(page) -> bool:
    """Click iCIMS 'Apply for this job online' inside #icims_content_iframe."""
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames:
        u = getattr(fr, "url", "") or ""
        if "icims.com" not in u.lower():
            continue
        try:
            link = fr.locator("a[href*='mode=apply']").first
            if link.count():
                link.click(timeout=4000)
                _sleep(2.0)
                return True
        except Exception:
            pass
        try:
            link = fr.get_by_role("link", name=re.compile(r"Apply for this job online", re.I))
            if link.count() and link.first.is_visible():
                link.first.click(timeout=4000)
                _sleep(2.0)
                return True
        except Exception:
            continue
    return False


def icims_logged_in(page) -> bool:
    """True after iCIMS candidate login (Dashboard / Log Out in the apply iframe)."""
    return bool(re.search(r"\bLog Out\b|Dashboard\s*\|", _body(page, 4000), re.I))


def icims_should_wait_captcha(page) -> bool:
    """Wait for a human/solver only on the GDPR /login wall, not mid-form hCaptcha chrome."""
    if icims_hcaptcha_login(page):
        return True
    if icims_logged_in(page):
        return False
    return visible_captcha_challenge(page)


def fill_icims_questions(page) -> bool:
    """Answer Hyland iCIMS Candidate Questions (relocate / salary / work auth)."""
    target = icims_active_frame(page)
    clicked = False
    pairs = (
        (r"willing to relocate", r"^Yes$"),
        (r"worked for Hyland|ever worked for", r"^No$"),
        (r"Thoma Bravo", r"^No$"),
        (r"work authorization|authori[sz]ed to work", r"^Yes$"),
    )
    for q_re, a_re in pairs:
        try:
            block = target.locator("fieldset, div, li, tr, section, table").filter(
                has_text=re.compile(q_re, re.I)
            ).first
            if not block.count():
                continue
            ans = block.get_by_text(re.compile(a_re, re.I)).first
            if ans.count() and ans.is_visible():
                ans.click(timeout=2500)
                clicked = True
                _sleep(0.25)
        except Exception:
            continue
    for box in (
        target.get_by_label(re.compile(r"salary|languages", re.I)),
        target.locator("textarea"),
        target.locator("input[type='text']"),
    ):
        try:
            n = min(box.count(), 6)
        except Exception:
            continue
        for i in range(n):
            el = box.nth(i)
            try:
                if not el.is_visible():
                    continue
                name = ((el.get_attribute("name") or "") + " " + (el.get_attribute("aria-label") or "")).lower()
                nearby = ""
                try:
                    nearby = (el.evaluate("e => (e.closest('tr,fieldset,div')||e.parentElement).innerText") or "")[:200]
                except Exception:
                    nearby = name
                if re.search(r"salary|ctc|compensation", nearby, re.I):
                    el.fill(PROFILE["expected_ctc"], timeout=3000)
                    clicked = True
                elif re.search(r"language", nearby, re.I):
                    el.fill("English, Hindi", timeout=3000)
                    clicked = True
            except Exception:
                continue
    # Source / how-did-you-hear selects inside the iCIMS iframe.
    try:
        if fill_source_fields(target):
            clicked = True
    except Exception:
        pass
    try:
        selects = target.locator("select")
        for i in range(min(selects.count(), 20)):
            sel = selects.nth(i)
            if not sel.is_visible():
                continue
            meta = ""
            try:
                meta = sel.evaluate(
                    "e => ((e.name||'')+' '+(e.id||'')+' '+(e.getAttribute('aria-label')||'')+' '+"
                    "((e.labels&&e.labels[0]&&e.labels[0].innerText)||'')).slice(0,160)"
                )
            except Exception:
                continue
            if re.search(r"source|hear about|how did you|referral", meta or "", re.I):
                if _select_matching_option(sel, SOURCE_OPTION_PATTERNS):
                    clicked = True
    except Exception:
        pass
    # Years-of-experience / skill matrix required selects (AMD job-specific questions).
    if icims_fill_required_selects(page):
        clicked = True
    return clicked


def icims_empty_required_fields(page) -> list[str]:
    """Return labels/names of empty required selects in the active iCIMS frame."""
    target = icims_active_frame(page)
    try:
        return list(
            target.evaluate(
                """() => {
                  const bad = [];
                  for (const sel of document.querySelectorAll('select')) {
                    const near = ((sel.closest('tr,fieldset,li,div,td,section') || sel.parentElement)
                      .innerText || '').slice(0, 180);
                    const req = sel.required || sel.getAttribute('i_required') === 'true' ||
                      /iCIMS_Forms_RequiredField/i.test(sel.className || '') ||
                      /years of professional|work experience with/i.test(near);
                    if (!req) continue;
                    const cur = (sel.selectedOptions[0] && sel.selectedOptions[0].text || '').trim();
                    if (!sel.value || /^make a selection|^select|^—/i.test(cur)) {
                      bad.push((near.split('\\n').find(Boolean) || sel.name || 'required').slice(0, 80));
                    }
                  }
                  return bad;
                }"""
            )
            or []
        )
    except Exception:
        return []


def icims_fill_required_selects(page) -> bool:
    """Fill empty required iCIMS selects (skill years, etc.) before any Submit click."""
    target = icims_active_frame(page)
    try:
        n = int(
            target.evaluate(
                """() => {
                  let filled = 0;
                  const yearPrefs = [/^more than 8/i, /^10\\+/i, /^7-10/i, /^6-8/i, /^4-6/i, /^3-5/i];
                  for (const sel of document.querySelectorAll('select')) {
                    const near = ((sel.closest('tr,fieldset,li,div,td,section') || sel.parentElement)
                      .innerText || '').slice(0, 200);
                    const req = sel.required || sel.getAttribute('i_required') === 'true' ||
                      /iCIMS_Forms_RequiredField/i.test(sel.className || '') ||
                      /years of professional|work experience with/i.test(near);
                    if (!req) continue;
                    const cur = (sel.selectedOptions[0] && sel.selectedOptions[0].text || '').trim();
                    if (sel.value && !/^make a selection|^select|^—/i.test(cur)) continue;
                    let hit = null;
                    for (const pref of yearPrefs) {
                      hit = [...sel.options].find(o => pref.test((o.text || '').trim()) && o.value);
                      if (hit) break;
                    }
                    if (!hit) hit = [...sel.options].filter(o => o.value).slice(-1)[0];
                    if (hit) {
                      sel.value = hit.value;
                      sel.dispatchEvent(new Event('change', { bubbles: true }));
                      filled++;
                    }
                  }
                  return filled;
                }"""
            )
            or 0
        )
        if n:
            print(f"icims=filled_required_selects n={n}", flush=True)
        return n > 0
    except Exception:
        return False


def icims_click_submit_if_ready(page) -> bool:
    """Click Submit/Next only when no required selects are still empty."""
    target = icims_active_frame(page)
    icims_fill_required_selects(page)
    empty = icims_empty_required_fields(page)
    if empty:
        print(
            f"icims=skip_submit empty_required={len(empty)} sample={empty[:3]}",
            flush=True,
        )
        return False
    return _click_text(
        target,
        ("Submit Profile", "Submit Application", "Submit", "Next", "Continue", "Save and Continue"),
    )


def advance_icims_us_forms(page) -> bool:
    """Skip US-only EEO / self-ID packets (India applicants)."""
    target = icims_active_frame(page)
    moved = False
    for name in (
        r"I Don.?t Wish To Answer",
        r"I do not wish to answer",
        r"Decline to (self-)?identify",
        r"I don't wish to answer",
    ):
        try:
            loc = target.get_by_text(re.compile(name, re.I))
            for i in range(min(loc.count(), 6)):
                el = loc.nth(i)
                if el.is_visible():
                    el.click(timeout=2500)
                    moved = True
                    _sleep(0.3)
        except Exception:
            continue
    if _click_text(
        target,
        (
            "Advance to next form",
            "Next form",
            "Continue",
            "Submit",
            "Next",
        ),
    ):
        return True
    return moved


def icims_hcaptcha_login(page) -> bool:
    """True when iCIMS apply opened the GDPR/email login that is gated by hCaptcha."""
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames:
        u = getattr(fr, "url", "") or ""
        if not re.search(r"icims\.com/.+/login", u, re.I):
            continue
        try:
            text = (fr.locator("body").inner_text(timeout=1500) or "")[:2500]
        except Exception:
            text = ""
        if re.search(r"hcaptcha|i accept|enter your information", text, re.I):
            return True
    try:
        url = getattr(page, "url", "") or ""
    except Exception:
        url = ""
    return bool(re.search(r"icims\.com/.+/login", url, re.I))


def page_flags(page) -> dict:
    url = getattr(page, "url", "") or ""
    text = _body(page, 2500)
    has_password = False
    has_file = False
    has_email = False
    has_wd = False
    try:
        has_password = page.locator("input[type='password']").count() > 0
        has_file = page.locator("input[type='file']").count() > 0
        has_email = (
            page.locator("[data-automation-id='email'], input[type='email']").count() > 0
        )
        has_wd = bool(
            page.locator("[data-automation-id]").count()
            or re.search(r"Autofill with Resume|Apply Manually", text, re.I)
        )
    except Exception:
        pass
    has_apply_cta = bool(
        re.search(
            r"\bapply (now|for this job)|start application|i'?m interested|submit application",
            text,
            re.I,
        )
    )
    return {
        "url": url,
        "text": text,
        "has_password": has_password,
        "has_file": has_file,
        "has_email": has_email,
        "has_wd": has_wd,
        "has_apply_cta": has_apply_cta,
    }


def blocked_wall(page) -> str | None:
    if visible_captcha_challenge(page):
        return "CAPTCHA/bot wall"
    flags = page_flags(page)
    return auth_wall_reason(
        flags["url"],
        flags["text"],
        has_password=flags["has_password"],
        has_file=flags["has_file"],
        has_workday_apply=flags["has_wd"],
        has_email_field=flags["has_email"],
    )


def upload_resume(page) -> bool:
    path = resume_upload_path()
    print(f"  ats_resume={path}", flush=True)
    uploaded = False
    for sel in ("input[type='file']", "input[accept*='pdf']", "input[accept*='doc']"):
        try:
            inputs = page.locator(sel)
            for i in range(min(inputs.count(), 4)):
                try:
                    inputs.nth(i).set_input_files(path, timeout=8000)
                    uploaded = True
                    _sleep(0.6)
                except Exception:
                    continue
        except Exception:
            continue
    return uploaded


def _click_text(page, labels: tuple[str, ...]) -> bool:
    for name in labels:
        try:
            btn = page.get_by_role("button", name=re.compile(rf"{re.escape(name)}", re.I))
            for i in range(min(btn.count(), 3)):
                b = btn.nth(i)
                if b.is_visible() and b.is_enabled():
                    label = ((b.inner_text() or "") + " " + (b.get_attribute("aria-label") or "")).strip()
                    if re.search(r"apply", name, re.I) and not looks_like_apply_cta(label):
                        continue
                    try:
                        b.click(timeout=3000, force=True)
                    except Exception:
                        b.evaluate("el => el.click()")
                    _sleep(1.2)
                    return True
        except Exception:
            continue
        try:
            link = page.get_by_role("link", name=re.compile(rf"{re.escape(name)}", re.I))
            if link.count() and link.first.is_visible():
                label = (
                    (link.first.inner_text() or "")
                    + " "
                    + (link.first.get_attribute("aria-label") or "")
                    + " "
                    + (link.first.get_attribute("href") or "")
                ).strip()
                if re.search(r"apply", name, re.I) and not looks_like_apply_cta(label):
                    continue
                link.first.click(timeout=3000)
                _sleep(1.2)
                return True
        except Exception:
            continue
        try:
            loc = page.get_by_text(name, exact=False).first
            if loc.is_visible():
                label = (loc.inner_text() or "").strip()
                if re.search(r"apply", name, re.I) and not looks_like_apply_cta(label):
                    continue
                loc.click(timeout=2500, force=True)
                _sleep(1.2)
                return True
        except Exception:
            continue
    return False


def dismiss_cookies(page) -> None:
    _click_text(
        page,
        ("Accept All Cookies", "Accept Cookies", "Accept all", "Accept"),
    )
    for sel in (
        "[data-automation-id='legalNoticeAcceptButton']",
        "button[id*='cookie' i]",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click(force=True)
                _sleep(0.3)
        except Exception:
            continue


def fill_labeled_fields(page) -> None:
    email = ats_email()
    pairs = [
        (r"first name|given name", PROFILE["first"]),
        (r"last name|surname|family name", PROFILE["last"]),
        (r"^full name$|legal name|your name", PROFILE["full"]),
        (r"email|e-mail", email),
        (r"phone|mobile|tel", PROFILE["phone"]),
        (r"linkedin|profile url", PROFILE["linkedin"]),
        (r"city|current city", PROFILE["city"]),
        (r"state|province|region", PROFILE["state"]),
        (r"country", PROFILE["country"]),
        (r"postal|zip", PROFILE["postal"]),
        (r"current (ctc|salary|compensation)|present ctc", PROFILE["current_ctc"]),
        (r"expected (ctc|salary|compensation)|desired salary", PROFILE["expected_ctc"]),
        (r"notice", PROFILE["notice"]),
        (r"years of experience|total experience", PROFILE["experience_years"]),
    ]
    try:
        labels = page.locator("label, [data-automation-id], .form-group label")
        n = min(labels.count(), 70)
    except Exception:
        return
    for i in range(n):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=350) or "").strip().lower()
        except Exception:
            continue
        if not text or len(text) > 90:
            continue
        if re.search(
            r"robots only|beecatcher|honey.?pot|do not enter if you.re human",
            text,
            re.I,
        ):
            continue
        for pat, val in pairs:
            if not re.search(pat, text, re.I):
                continue
            try:
                for_id = lab.get_attribute("for")
                ctrl = (
                    page.locator(f'[id="{for_id}"]').first
                    if for_id
                    else lab.locator(
                        "xpath=following::*[self::input or self::textarea or self::select][1]"
                    ).first
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


def fill_yes_no(page) -> None:
    pairs = [
        (r"authorized to work|legally authori[sz]ed", r"^Yes$"),
        (r"require sponsorship|visa sponsorship", r"^No$"),
        (r"previously (worked|employed)|former employee", r"^No$"),
        (r"relatives? (employed|work)", r"^No$"),
        (r"at least 18", r"^Yes$"),
        (r"willing to relocate", r"^Yes$"),
        (r"military|armed forces|served in the", r"^No$"),
        (r"need (any )?visa|require (a )?visa", r"^No$"),
    ]
    for q_re, a_re in pairs:
        try:
            block = page.locator("fieldset, div, li, section").filter(has_text=re.compile(q_re, re.I)).first
            if not block.count() or not block.is_visible():
                continue
            ans = block.get_by_text(re.compile(a_re, re.I)).first
            if ans.count() and ans.is_visible():
                ans.click(force=True)
                _sleep(0.2)
        except Exception:
            continue


def tick_consents(page) -> None:
    for sel in (
        "input[type='checkbox'][name*='consent' i]",
        "input[type='checkbox'][id*='consent' i]",
        "input[type='checkbox'][name*='terms' i]",
        "[data-automation-id='createAccountCheckbox']",
    ):
        try:
            boxes = page.locator(sel)
            for i in range(min(boxes.count(), 4)):
                b = boxes.nth(i)
                if b.is_visible() and not b.is_checked():
                    b.check(force=True)
        except Exception:
            continue
    try:
        label = page.locator("label").filter(
            has_text=re.compile(r"I have (reviewed|read).{0,40}consent|I agree|I acknowledge", re.I)
        ).first
        if label.count() and label.is_visible():
            label.click(force=True)
    except Exception:
        pass
    # Oracle Careers terms overlay is a submit button labeled AGREE (not a checkbox).
    try:
        agree = page.get_by_role("button", name=re.compile(r"^(agree|i agree)$", re.I))
        if agree.count() and agree.first.is_visible():
            agree.first.click(timeout=2500, force=True)
            _sleep(0.8)
    except Exception:
        pass


def skip_advance_label(label: str | None) -> bool:
    """True when a submit/next control is dismiss/back chrome, not Apply/Next.

    Oracle Careers /apply/email puts Close + AGREE + Back as type=submit *before*
    NEXT (type=button). Clicking .first() Close left the form stuck in persist_retry.
    """
    lab = (label or "").strip().lower()
    if not lab:
        return False
    if re.search(r"sign in with (google|microsoft|linkedin|apple)", lab):
        return True
    if re.search(r"^(close|cancel|back|go back)$", lab):
        return True
    if re.search(r"\bback to\b|\bgo back\b", lab):
        return True
    return False


def click_advance(page) -> bool:
    for sel in (
        "[data-automation-id='pageFooterNextButton']",
        "button[data-automation-id='bottom-navigation-next-button']",
        "[data-automation-id='createAccountSubmitButton']",
        "[data-automation-id='signInSubmitButton']",
        "button[type='submit']",
        "input[type='submit']",
    ):
        try:
            loc = page.locator(sel)
            n = min(loc.count(), 8)
        except Exception:
            continue
        for i in range(n):
            el = loc.nth(i)
            try:
                if not (el.is_visible() and el.is_enabled()):
                    continue
                label = ((el.inner_text() or "") + " " + (el.get_attribute("aria-label") or "")).lower()
                if skip_advance_label(label):
                    continue
                # Password-rule reject: do not keep submitting Create Account.
                if "createAccountSubmit" in sel and workday_password_alert(page):
                    continue
                el.click(timeout=3000, force=True)
                _sleep(1.6)
                return True
            except Exception:
                continue
    return _click_text(
        page,
        (
            "Submit application",
            "Submit Application",
            "Send application",
            "Advance to next form",
            "Save and Continue",
            "Create Account",
            "I'm interested",
            "Submit",
            "Continue",
            "Next",
            "Apply Manually",
            "Apply for this job online",
            "Apply",
        ),
    )


def prefer_guest_apply(page) -> bool:
    """Open the guest/manual apply form. Never click OneClick / Indeed OAuth."""
    for name in (
        "Apply without Indeed",
        "Apply manually",
        "Apply with resume",
        "I'm interested",
        "Apply for this job online",
        "Apply for this job",
        "Start application",
        "Apply Now",
        "Apply",
    ):
        try:
            btn = page.get_by_role("button", name=re.compile(rf"{re.escape(name)}", re.I))
            for i in range(min(btn.count(), 4)):
                b = btn.nth(i)
                if not (b.is_visible() and b.is_enabled()):
                    continue
                label = ((b.inner_text() or "") + " " + (b.get_attribute("aria-label") or "")).strip()
                if re.search(r"oneclick|with indeed|with linkedin|with google|with microsoft", label, re.I):
                    continue
                if re.search(r"apply", name, re.I) and not looks_like_apply_cta(label):
                    continue
                try:
                    b.click(timeout=3000, force=True)
                except Exception:
                    b.evaluate("el => el.click()")
                _sleep(1.2)
                return True
        except Exception:
            continue
        try:
            link = page.get_by_role("link", name=re.compile(rf"{re.escape(name)}", re.I))
            if link.count() and link.first.is_visible():
                label = ((link.first.inner_text() or "") + " " + (link.first.get_attribute("href") or "")).strip()
                if re.search(r"oneclick|indeed\.com/oauth|with indeed", label, re.I):
                    continue
                if re.search(r"apply", name, re.I) and not looks_like_apply_cta(label):
                    continue
                link.first.click(timeout=3000)
                _sleep(1.2)
                return True
        except Exception:
            continue
    return False


def leave_oneclick_oauth(page) -> None:
    """SmartRecruiters OneClick often dumps us on Indeed OAuth — go back to guest apply."""
    url = getattr(page, "url", "") or ""
    if not re.search(r"oneclick|indeed\.com/oauth|secure\.indeed\.com/(?:auth|oauth)", url, re.I):
        return
    try:
        page.go_back(wait_until="domcontentloaded", timeout=8000)
        _sleep(1.0)
    except Exception:
        pass
    prefer_guest_apply(page)


def _type_automation(page, automation_id: str, value: str) -> bool:
    try:
        el = page.locator(
            f"[data-automation-id='{automation_id}'] input, [data-automation-id='{automation_id}']"
        ).first
        if not el.count() or not el.is_visible():
            return False
        el.click(force=True)
        el.fill("")
        el.fill(value)
        return True
    except Exception:
        return False


def workday_password_rejected(text: str | None) -> bool:
    """True when Workday Create Account rejects the typed password rules.

    Do not match the static "Password Requirements:" help list — only the
    live error ("Password must include" / "does not meet the password").
    """
    return bool(
        re.search(
            r"password must include|does not meet (the )?password|"
            r"error:\s*password|password (is )?too weak",
            text or "",
            re.I,
        )
    )


def workday_on_standalone_login(url: str | None) -> bool:
    """True for Workday /login (not the in-flow Create Account/apply steps)."""
    return bool(re.search(r"myworkdayjobs\.com/.+/login(?:\?|$)", url or "", re.I))


def workday_stuck_on_sign_in(page) -> bool:
    """True when Workday shows only a Sign In form (no guest application fields).

    Some tenants (e.g. Gartner) keep the URL on `/apply/applyManually` while the
    document title is ``Sign In - …`` and only ``signInSubmitButton`` is present.
    That must fail-fast as ``ats_login_wall`` — otherwise click_advance burns the
    full ATS time cap and ``external_incomplete_or_timeout`` never trips the
    per-company hard-wall budget.
    """
    try:
        title = (page.title() or "").strip()
    except Exception:
        title = ""
    if re.search(r"^sign\s*in\b", title, re.I):
        return True
    try:
        sign = page.locator("[data-automation-id='signInSubmitButton']").first
        if not (sign.count() and sign.is_visible()):
            return False
        for sel in (
            "[data-automation-id='legalNameSection']",
            "[data-automation-id='formField-name']",
            "[data-automation-id='file-upload-input-ref']",
            "input[type='file']",
            "[data-automation-id='applyManually']",
            "[data-automation-id='adventureButton']",
            "[data-automation-id='createAccountSubmitButton']",
            "[data-automation-id='verifyPassword']",
        ):
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                return False
        return True
    except Exception:
        return False


def workday_password_alert(page) -> bool:
    """True when the live Create Account form shows a password-rule error.

    Workday progress-bar chrome often exceeds a 1500-char body slice, so the
    visible ``inputAlert`` (or a longer body) must be checked — otherwise
    complete_workday burns the 390s cap re-clicking Create Account.
    """
    try:
        alert = page.locator("[data-automation-id='inputAlert']").first
        if alert.count() and alert.is_visible():
            if workday_password_rejected(alert.inner_text(timeout=800) or ""):
                return True
    except Exception:
        pass
    return workday_password_rejected(_body(page, 8000))


def workday_open_apply(page) -> None:
    dismiss_cookies(page)
    for sel in (
        "a[data-automation-id='adventureButton']",
        "button[data-automation-id='adventureButton']",
    ):
        try:
            el = page.locator(sel).first
            if el.count() and el.is_visible():
                el.click()
                _sleep(1.4)
                break
        except Exception:
            continue
    else:
        _click_text(page, ("Apply",))
    autofill = page.get_by_text("Autofill with Resume", exact=False).first
    manual = page.get_by_text("Apply Manually", exact=False).first
    try:
        if autofill.count() and autofill.is_visible():
            autofill.click(force=True)
            _sleep(1.8)
    except Exception:
        pass
    try:
        still = autofill.count() and autofill.is_visible()
        if (still or not autofill.count()) and manual.count() and manual.is_visible():
            manual.click(force=True)
            _sleep(1.6)
    except Exception:
        pass
    dismiss_cookies(page)


def workday_auth(page) -> str | None:
    """Create account or sign in. None = continue; string = hard wall."""
    password = ats_password()
    email = ats_email()
    if not email or "@" not in email:
        return "ats_email_missing"
    try:
        email_el = page.locator("[data-automation-id='email']").first
        if not (email_el.count() and email_el.is_visible()):
            _click_text(page, ("Sign in with email", "Use email", "Continue with email"))
            create = page.locator(
                "[data-automation-id='createAccountLink'], button:has-text('Create Account'), a:has-text('Create Account')"
            ).first
            if create.count() and create.is_visible():
                create.click(force=True)
                _sleep(1.2)
    except Exception:
        pass
    try:
        email_ready = page.locator("[data-automation-id='email']").first
        if not (email_ready.count() and email_ready.is_visible()):
            return None
    except Exception:
        return None
    if not password:
        return "ats_password_missing"
    create_password = workday_compliant_password(password)
    # Prefer Sign In — prior runs often already created the tenant account.
    # Create Account is what Solera rejects on password-complexity rules.
    chose_sign_in = False
    try:
        sign = page.locator(
            "[data-automation-id='signInLink'], [data-automation-id='utilityButtonSignIn']"
        ).first
        if sign.count() and sign.is_visible():
            sign.click(force=True)
            chose_sign_in = True
            # Wait for Sign In form — do not bounce back to Create Account.
            for _ in range(8):
                _sleep(0.35)
                try:
                    if page.locator("[data-automation-id='signInSubmitButton']").first.is_visible():
                        break
                except Exception:
                    pass
    except Exception:
        pass
    verify = page.locator("[data-automation-id='verifyPassword']").first
    try:
        if not (verify.count() and verify.is_visible()):
            sign_in = page.locator("[data-automation-id='signInSubmitButton']").first
            if not (sign_in.count() and sign_in.is_visible()) and not chose_sign_in:
                create = page.locator("[data-automation-id='createAccountLink']").first
                if create.count() and create.is_visible():
                    create.click(force=True)
                    _sleep(1.2)
    except Exception:
        pass
    creating = False
    try:
        creating = page.locator("[data-automation-id='verifyPassword']").first.is_visible()
    except Exception:
        creating = False
    use_pw = create_password if creating else password
    _type_automation(page, "email", email)
    _type_automation(page, "password", use_pw)
    try:
        if creating:
            _type_automation(page, "verifyPassword", create_password)
            tick_consents(page)
            submit = page.locator(
                "[data-automation-id='createAccountSubmitButton'], button:has-text('Create Account')"
            ).first
            if submit.count() and submit.is_visible():
                submit.click(force=True)
                _sleep(2.8)
        else:
            submit = page.locator(
                "[data-automation-id='signInSubmitButton'], button:has-text('Sign In')"
            ).first
            if submit.count() and submit.is_visible():
                submit.click(force=True)
                _sleep(2.8)
    except Exception:
        pass
    text = _body(page, 2000)
    if re.search(r"already have an account|already exists|sign in instead", text, re.I):
        _click_text(page, ("Sign In",))
        _type_automation(page, "email", email)
        _type_automation(page, "password", password)
        _click_text(page, ("Sign In",))
        _sleep(2.0)
    if workday_password_alert(page):
        # Raw secret failed complexity — retry Create Account with compliant
        # password, then Sign In. Do not burn the 390s cap looping Create.
        try:
            if page.locator("[data-automation-id='verifyPassword']").first.is_visible():
                _type_automation(page, "password", create_password)
                _type_automation(page, "verifyPassword", create_password)
                tick_consents(page)
                submit = page.locator(
                    "[data-automation-id='createAccountSubmitButton']"
                ).first
                if submit.count() and submit.is_visible():
                    submit.click(force=True)
                    _sleep(2.8)
        except Exception:
            pass
        if workday_password_alert(page):
            try:
                sign = page.locator(
                    "[data-automation-id='signInLink'], [data-automation-id='utilityButtonSignIn']"
                ).first
                if sign.count() and sign.is_visible():
                    sign.click(force=True)
                    _sleep(1.2)
                    _type_automation(page, "email", email)
                    _type_automation(page, "password", password)
                    _click_text(page, ("Sign In",))
                    _sleep(2.0)
                    if re.search(
                        r"wrong email address or password|incorrect email or password",
                        _body(page, 1500),
                        re.I,
                    ) and create_password != password:
                        _type_automation(page, "password", create_password)
                        _click_text(page, ("Sign In",))
                        _sleep(2.0)
            except Exception:
                pass
        if workday_password_alert(page) and page.locator(
            "[data-automation-id='createAccountSubmitButton']"
        ).count():
            return "ats_login_wall"
    if re.search(
        r"wrong email address or password|incorrect email or password|invalid email or password",
        _body(page, 1500),
        re.I,
    ):
        return "ats_login_wall"
    return None


def _pick_workday_option(page, form_field_id: str, patterns: list[str]) -> bool:
    """Open a Workday select/multiselect and pick the first matching option.

    Verifies the widget text actually changed — never claim success on a blind
    typeahead Enter (that left Source empty and abandoned submits).
    """
    try:
        root = page.locator(f"[data-automation-id='{form_field_id}']").first
        if not root.count() or not root.is_visible():
            return False
        before = (root.inner_text(timeout=800) or "").strip()
        if before and not re.search(r"select one|0 items selected|^$", before, re.I):
            if any(re.search(p, before, re.I) for p in patterns):
                return True
        opener = root.locator(
            "button[aria-haspopup='listbox'], [data-automation-id='selectWidget'], "
            "[data-automation-id='multiselectInputContainer'], button, input"
        ).first
        if opener.count() and opener.is_visible():
            opener.click(force=True)
            _sleep(0.55)
        for pat in patterns:
            opt = page.locator(
                "[data-automation-id='promptOption'], [role='option'], "
                "[data-automation-id='promptLeafNode'], li[role='option']"
            ).filter(has_text=re.compile(pat, re.I)).first
            if opt.count() and opt.is_visible():
                opt.click(force=True)
                _sleep(0.35)
                page.keyboard.press("Escape")
                after = (root.inner_text(timeout=800) or "").strip()
                if after and (
                    any(re.search(p, after, re.I) for p in patterns)
                    or (after != before and not re.search(r"select one|0 items selected", after, re.I))
                ):
                    return True
            # Typeahead fallback — still verify the widget accepted a match.
            hint = re.sub(r"[^A-Za-z0-9 ]", " ", pat)
            hint = re.sub(r"\s+", " ", hint).strip()[:18]
            if not hint or hint in ("^",):
                continue
            try:
                page.keyboard.type(hint, delay=25)
                _sleep(0.35)
                opt2 = page.locator(
                    "[data-automation-id='promptOption'], [role='option']"
                ).filter(has_text=re.compile(pat, re.I)).first
                if opt2.count() and opt2.is_visible():
                    opt2.click(force=True)
                else:
                    page.keyboard.press("Enter")
                _sleep(0.35)
                page.keyboard.press("Escape")
                after = (root.inner_text(timeout=800) or "").strip()
                if after and any(re.search(p, after, re.I) for p in patterns):
                    return True
                if after and after != before and not re.search(r"select one|0 items selected", after, re.I):
                    return True
            except Exception:
                try:
                    page.keyboard.press("Escape")
                except Exception:
                    pass
                continue
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
    except Exception:
        return False
    return False


def _select_matching_option(ctrl, patterns: list[str]) -> bool:
    """Fill a native <select> from option label patterns."""
    try:
        tag = ctrl.evaluate("e => e.tagName.toLowerCase()")
        if tag != "select":
            return False
        options = ctrl.evaluate(
            """e => Array.from(e.options||[]).map(o => ({v:o.value, t:(o.text||o.label||'').trim()}))"""
        )
        for pat in patterns:
            for opt in options or []:
                text = opt.get("t") or ""
                if re.search(pat, text, re.I) and text and not re.search(r"^select|choose|—|-+\s*$", text, re.I):
                    try:
                        ctrl.select_option(label=text)
                    except Exception:
                        ctrl.select_option(value=opt.get("v"))
                    return True
    except Exception:
        return False
    return False


def fill_source_fields(page) -> bool:
    """Fill Source / How did you hear — required on many Workday/iCIMS/GH forms.

    Owner often has to pick these manually; leaving them empty causes
    external_incomplete_or_timeout without submitting.
    """
    filled = False
    # Workday automation-id widgets (common variants).
    for fid in (
        "formField-source",
        "formField-sourceType",
        "formField-candidateSource",
        "formField-howDidYouHear",
        "formField-howDidYouHearAboutUs",
        "sourceDropdown",
        "candidateSource",
        "howDidYouHear",
    ):
        if _pick_workday_option(page, fid, SOURCE_OPTION_PATTERNS):
            filled = True

    # Native <select> by name/id/aria/nearby label.
    try:
        selects = page.locator("select")
        n = min(selects.count(), 25)
    except Exception:
        n = 0
    for i in range(n):
        sel = selects.nth(i)
        try:
            if not sel.is_visible():
                continue
            meta = sel.evaluate(
                """e => {
                  const lab = e.labels && e.labels[0] ? e.labels[0].innerText : '';
                  const near = (e.closest('fieldset,tr,div,li,section')||e.parentElement);
                  return [e.name||'', e.id||'', e.getAttribute('aria-label')||'', lab||'',
                          (near && near.innerText||'').slice(0,120)].join(' | ');
                }"""
            )
            if not SOURCE_LABEL_RE.search(meta or ""):
                # Also catch loose "Source*" labels in nearby text.
                if not re.search(r"\bsource\b|how did you hear|hear about", meta or "", re.I):
                    continue
            if _select_matching_option(sel, SOURCE_OPTION_PATTERNS):
                filled = True
        except Exception:
            continue

    # Label → combobox / following control (Greenhouse, SmartRecruiters, generic).
    try:
        labels = page.locator("label, legend, [data-automation-id*='formField']")
        ln = min(labels.count(), 80)
    except Exception:
        ln = 0
    for i in range(ln):
        lab = labels.nth(i)
        try:
            text = (lab.inner_text(timeout=300) or "").strip()
        except Exception:
            continue
        if not text or len(text) > 100:
            continue
        if not (SOURCE_LABEL_RE.search(text) or re.search(r"\bsource\b|how did you hear", text, re.I)):
            continue
        try:
            for_id = lab.get_attribute("for")
            ctrl = (
                page.locator(f'[id="{for_id}"]').first
                if for_id
                else lab.locator(
                    "xpath=following::*[self::input or self::select or self::button or @role='combobox'][1]"
                ).first
            )
            if not ctrl.count():
                # Workday: label node IS the formField container
                aid = lab.get_attribute("data-automation-id") or ""
                if aid.startswith("formField-") and _pick_workday_option(page, aid, SOURCE_OPTION_PATTERNS):
                    filled = True
                continue
            tag = ""
            try:
                tag = ctrl.evaluate("e => (e.tagName||'').toLowerCase()")
            except Exception:
                tag = ""
            if tag == "select":
                if _select_matching_option(ctrl, SOURCE_OPTION_PATTERNS):
                    filled = True
                continue
            # Custom dropdown / combobox
            ctrl.click(force=True)
            _sleep(0.35)
            preferred = PROFILE.get("source") or "LinkedIn"
            page.keyboard.type(preferred, delay=20)
            _sleep(0.35)
            opt = page.locator("[role='option']:visible, [data-automation-id='promptOption']").filter(
                has_text=re.compile(r"LinkedIn|Job Board|Naukri|Indeed|Internet|Other", re.I)
            ).first
            if opt.count() and opt.is_visible():
                opt.click(force=True)
                filled = True
            else:
                page.keyboard.press("Enter")
                filled = True
            _sleep(0.2)
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
        except Exception:
            continue
    return filled


def fill_validation_gaps(page) -> bool:
    """After 'Errors Found' / required blanks — fill leftover required controls."""
    progressed = False
    if fill_source_fields(page):
        progressed = True
    # Required empty native selects: pick first non-placeholder option when label known.
    try:
        empties = page.evaluate(
            """() => {
              const out = [];
              for (const s of document.querySelectorAll('select')) {
                const req = s.required || s.getAttribute('aria-required') === 'true';
                const bad = s.getAttribute('aria-invalid') === 'true';
                const val = (s.value || '').trim();
                const t = (s.options[s.selectedIndex] && s.options[s.selectedIndex].text || '').trim();
                const empty = !val || /select|choose|^-$/i.test(t);
                if ((req || bad || empty) && s.offsetParent !== null) {
                  const lab = s.labels && s.labels[0] ? s.labels[0].innerText : (s.name||s.id||'');
                  out.push({name: s.name||'', id: s.id||'', label: (lab||'').slice(0,80), empty});
                }
              }
              return out.slice(0, 15);
            }"""
        )
    except Exception:
        empties = []
    for row in empties or []:
        label = row.get("label") or ""
        sid = row.get("id") or ""
        name = row.get("name") or ""
        try:
            ctrl = (
                page.locator(f"select#{sid}").first
                if sid
                else page.locator(f"select[name='{name}']").first
                if name
                else None
            )
            if not ctrl or not ctrl.count():
                continue
            if re.search(r"source|hear about|how did you", f"{label} {name} {sid}", re.I):
                if _select_matching_option(ctrl, SOURCE_OPTION_PATTERNS):
                    progressed = True
                continue
            if re.search(r"country", f"{label} {name}", re.I):
                if _select_matching_option(ctrl, [r"^India$", r"\bIndia\b"]):
                    progressed = True
                continue
            if re.search(r"state|province|region", f"{label} {name}", re.I):
                if _select_matching_option(ctrl, [r"Telangana", r"Andhra", r"^Other$", r"N/A", r"Not Applicable"]):
                    progressed = True
                continue
            if re.search(r"phone\s*type|type of phone", f"{label} {name}", re.I):
                if _select_matching_option(ctrl, [r"Mobile", r"Cell", r"Home"]):
                    progressed = True
        except Exception:
            continue
    return progressed


def workday_fill_core(page) -> None:
    # Prefer India when the tenant defaults to United States.
    try:
        country = page.locator(
            "[data-automation-id='formField-country'] button, [data-automation-id='countryDropdown']"
        ).first
        if country.count() and country.is_visible():
            c_text = (country.inner_text(timeout=800) or "").strip()
            if re.search(r"united states|select one|^$", c_text, re.I) and not re.search(r"india", c_text, re.I):
                country.click(force=True)
                _sleep(0.5)
                india = page.get_by_text(re.compile(r"^India$"), exact=True).first
                if india.count() and india.is_visible():
                    india.click(force=True)
                    _sleep(0.6)
    except Exception:
        pass
    _type_automation(page, "legalNameSection_firstName", PROFILE["first"])
    _type_automation(page, "legalNameSection_lastName", PROFILE["last"])
    _type_automation(page, "formField-legalName--firstName", PROFILE["first"])
    _type_automation(page, "formField-legalName--lastName", PROFILE["last"])
    _type_automation(page, "addressSection_city", PROFILE["city"])
    _type_automation(page, "formField-addressLine1", "Hyderabad, Telangana")
    _type_automation(page, "formField-city", PROFILE["city"])
    _type_automation(page, "formField-postalCode", PROFILE["postal"])
    _type_automation(page, "phone", PROFILE["phone"])
    _type_automation(page, "formField-phoneNumber", PROFILE["phone"])
    _pick_workday_option(page, "formField-phoneType", [r"^Mobile$", r"Cell", r"Mobile"])
    _pick_workday_option(page, "formField-source", SOURCE_OPTION_PATTERNS)
    fill_source_fields(page)
    _pick_workday_option(page, "formField-degree", [r"^BS$", r"Bachelor of Science", r"B\.?\s*Tech", r"^Bachelor"])
    _pick_workday_option(
        page,
        "formField-fieldOfStudy",
        [r"Information Technology", r"Computer Science", r"Computer Engineering"],
    )
    try:
        school = page.locator("[data-automation-id='formField-schoolName']").first
        if school.count() and school.is_visible():
            st = school.inner_text(timeout=600) or ""
            if not re.search(r"Acharya Nagarjuna|University", st, re.I):
                opener = school.locator("input, button, [data-automation-id='multiselectInputContainer']").first
                if opener.count():
                    opener.click(force=True)
                    page.keyboard.type(PROFILE["school"], delay=20)
                    _sleep(0.7)
                    opt = page.locator("[data-automation-id='promptOption']").filter(
                        has_text=re.compile(r"Acharya Nagarjuna", re.I)
                    ).first
                    if opt.count() and opt.is_visible():
                        opt.click(force=True)
                    else:
                        _type_automation(page, "formField-schoolName", PROFILE["school"])
                    page.keyboard.press("Escape")
    except Exception:
        pass
    try:
        prev = page.locator("[data-automation-id='formField-candidateIsPreviousWorker']").first
        if prev.count() and prev.is_visible():
            prev.get_by_text(re.compile(r"^No$"), exact=True).first.click(force=True)
    except Exception:
        pass
    fill_labeled_fields(page)
    fill_yes_no(page)
    fill_source_fields(page)
    tick_consents(page)


def complete_workday(page, time_cap_s: int) -> tuple[str, str]:
    start = time.time()
    if is_unavailable_text(f"{getattr(page, 'url', '')}\n{_body(page, 1500)}"):
        return "skipped", "job_unavailable"
    if looks_already_applied(page):
        return "skipped", "already_applied"
    workday_open_apply(page)
    if looks_submitted(page):
        return "applied", "confirmation"
    if looks_already_applied(page):
        return "skipped", "already_applied"
    auth = workday_auth(page)
    if auth:
        return "blocked", auth
    if workday_password_alert(page):
        return "blocked", "ats_login_wall"
    try:
        login_url = getattr(page, "url", "") or ""
    except Exception:
        login_url = ""
    if workday_on_standalone_login(login_url) or workday_stuck_on_sign_in(page):
        # Sign In navigated to /login OR tenant kept applyManually URL with a
        # Sign In document. One more credential pass, then fail-fast so empty
        # Sign In + click_advance cannot burn the ATS time cap.
        auth = workday_auth(page)
        if auth:
            return "blocked", auth
        try:
            login_url = getattr(page, "url", "") or ""
        except Exception:
            login_url = ""
        if (
            workday_on_standalone_login(login_url)
            or workday_stuck_on_sign_in(page)
            or workday_password_alert(page)
        ):
            return "blocked", "ats_login_wall"
    stuck = 0
    while time.time() - start < time_cap_s and stuck < 14:
        if looks_submitted(page):
            return "applied", "confirmation"
        if workday_password_alert(page):
            return "blocked", "ats_login_wall"
        try:
            if workday_on_standalone_login(getattr(page, "url", "") or ""):
                return "blocked", "ats_login_wall"
        except Exception:
            pass
        if workday_stuck_on_sign_in(page):
            return "blocked", "ats_login_wall"
        wall = blocked_wall(page)
        if wall == "CAPTCHA/bot wall":
            return "blocked", wall
        if wall in ("job_closed", "job_unavailable"):
            return "skipped", wall
        text = _body(page, 2000)
        if re.search(r"^\s*Loading\b", text, re.I) and not re.search(r"First Name|My Information", text, re.I):
            _sleep(2.0)
            continue
        try:
            if not re.search(r"successfully uploaded|Rafi_Resume", text, re.I):
                upload_resume(page)
        except Exception:
            pass
        workday_fill_core(page)
        if click_advance(page):
            stuck = 0
            _sleep(1.8)
            continue
        if looks_submitted(page):
            return "applied", "confirmation"
        body_now = _body(page, 1800)
        if re.search(r"Errors Found|is required and must have a value|this field is required", body_now, re.I):
            # Do not abandon — fill Source / required blanks and retry advance.
            progressed = fill_validation_gaps(page)
            workday_fill_core(page)
            if click_advance(page):
                stuck = 0
                _sleep(1.8)
                continue
            if progressed:
                stuck = max(0, stuck - 1)
            else:
                stuck += 1
            _sleep(0.8)
            continue
        stuck += 1
        _sleep(1.2)
    if looks_submitted(page):
        return "applied", "confirmation"
    owner = wait_owner_finish_apply(
        page, hint="Source / required fields / Submit on this Workday apply"
    )
    if owner:
        return owner
    if apply_form_still_open(page):
        burst = persist_retry_burst_sec()
        if burst <= 0:
            return "blocked", "external_incomplete_or_timeout"
        print(
            f"workday=persist_retry — form still open after owner wait; continuing ({burst}s)",
            flush=True,
        )
        burst_start = time.time()
        while time.time() - burst_start < burst:
            if looks_submitted(page):
                return "applied", "confirmation"
            try:
                upload_resume(page)
                workday_fill_core(page)
                fill_source_fields(page)
                fill_validation_gaps(page)
                click_advance(page)
            except Exception:
                pass
            _sleep(1.0)
        if looks_submitted(page):
            return "applied", "confirmation"
    return "blocked", "external_incomplete_or_timeout"


def owner_form_wait_sec() -> int:
    """Seconds to wait for the owner to finish a matching-job form (Source, login, etc.).

    Headed / HOME_LOCAL defaults to the same budget as captcha waits so we never
    abandon a criteria-matching apply without asking the owner first.
    Owner-asleep / overnight: short park (~12s) then continue elsewhere.
    """
    raw = (os.environ.get("ATS_OWNER_FORM_WAIT_SEC") or "").strip()
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return 0
    if owner_asleep():
        return 12
    # Reuse captcha wait budget when set; else headed defaults.
    try:
        from tools.ats.captcha_solve import owner_captcha_wait_sec

        cap = owner_captcha_wait_sec()
        if cap > 0:
            return cap
    except Exception:
        pass
    if (os.environ.get("HOME_LOCAL") or "").strip().lower() in ("1", "true", "yes"):
        return 360
    if (os.environ.get("CHROME_HEADLESS") or "1").strip() in ("0", "false", "no"):
        return 360
    return 0


def apply_form_still_open(page) -> bool:
    """True when the page still looks like an unfinished apply (do not abandon)."""
    try:
        url = getattr(page, "url", "") or ""
    except Exception:
        url = ""
    if re.search(
        r"/apply|/candidate|/questions|/login|mode=apply|mode=submit|"
        r"oraclecloud\.com/.*/(?:job|apply)|greenhouse\.io/.*/application|"
        r"myworkdayjobs\.com/.*/apply",
        url,
        re.I,
    ):
        return True
    text = _frames_text(page, 2500)
    if re.search(
        r"candidate profile|submit profile|submit application|required field|"
        r"how did you hear|upload your resume|personal info|work experience|"
        r"please be sure to fill|enter your information|i accept",
        text,
        re.I,
    ):
        return True
    try:
        if page.locator("input[type='file']").count() > 0:
            return True
    except Exception:
        pass
    return False


def wait_owner_finish_apply(page, *, hint: str = "") -> tuple[str, str] | None:
    """Ask the owner to finish required fields / submit; do not abandon matching jobs.

    Returns (status, reason) when submitted / already-applied, else None after timeout.
    Keeps auto-filling Source and other gaps while waiting. Extends once if the form
    is still open after owner activity (captcha/login) so we never walk away mid-apply.
    """
    wait = owner_form_wait_sec()
    if wait <= 0:
        return None
    # Overnight / owner-asleep: brief park only — do not extend or burn inventory.
    asleep = owner_asleep()
    if asleep:
        wait = min(wait, 12)
    msg = hint or "required fields (e.g. Source / How did you hear), login, or Submit"
    try:
        from tools.ats.captcha_solve import focus_page_for_owner, owner_focus_interval_sec

        focus_page_for_owner(page, reason="ask_owner_start")
        focus_every = owner_focus_interval_sec()
    except Exception:
        focus_page_for_owner = None  # type: ignore
        focus_every = 2.0
    print(
        f"ASK_OWNER wait={wait}s{' (owner_asleep)' if asleep else ''} — finish {msg} in the focused Chrome tab, then Submit. "
        f"Helper keeps filling Source/required blanks and resumes on confirmation.",
        flush=True,
    )
    deadline = time.time() + wait
    last_beat = 0.0
    last_focus = 0.0
    last_fp = page_fingerprint(page)
    extended = asleep  # skip extend loop when owner cannot respond
    poll = float(os.environ.get("ATS_CAPTCHA_POLL_SEC", "0.4") or "0.4")
    poll = min(1.0, max(0.25, poll))
    while True:
        while time.time() < deadline:
            if looks_submitted(page):
                print("ASK_OWNER resolved=submitted", flush=True)
                return "applied", "confirmation"
            if looks_already_applied(page):
                print("ASK_OWNER resolved=already_applied", flush=True)
                return "skipped", "already_applied"
            now = time.time()
            if focus_page_for_owner and now - last_focus >= focus_every:
                try:
                    focus_page_for_owner(page, reason="ask_owner_hold")
                except Exception:
                    pass
                last_focus = now
            try:
                # Prefer the iCIMS nested form document when present.
                target = page
                if re.search(r"icims\.com", getattr(page, "url", "") or "", re.I):
                    target = icims_active_frame(page)
                    icims_fill_gdpr_gate(page)
                    fill_icims_candidate_profile(page)
                try:
                    upload_resume(target)
                except Exception:
                    try:
                        upload_resume(page)
                    except Exception:
                        pass
                fill_source_fields(target)
                fill_validation_gaps(target)
                # Skip slow label crawl on iCIMS — fast name fill already ran.
                if not re.search(r"icims\.com", getattr(page, "url", "") or "", re.I):
                    fill_labeled_fields(target)
                    fill_yes_no(target)
                tick_consents(target)
                try:
                    fill_icims_questions(page)
                except Exception:
                    pass
                click_advance(target)
                click_advance(page)
            except Exception:
                pass
            fp = page_fingerprint(page)
            if fp != last_fp:
                # Owner or helper progressed — keep working; nudge deadline forward once.
                last_fp = fp
                if not extended and time.time() + 90 > deadline:
                    deadline = max(deadline, time.time() + 120)
                    print("ASK_OWNER progress — extending while form still open", flush=True)
            now = time.time()
            if now - last_beat >= 8.0:
                left = max(0, int(deadline - now))
                print(f"ASK_OWNER waiting {left}s left — tab kept focused for you", flush=True)
                last_beat = now
            _sleep(poll)
        if looks_submitted(page):
            return "applied", "confirmation"
        if looks_already_applied(page):
            return "skipped", "already_applied"
        if not extended and apply_form_still_open(page):
            extended = True
            extra = max(120, min(wait, 360))
            deadline = time.time() + extra
            print(
                f"ASK_OWNER extend={extra}s — form still open after owner action; "
                f"continuing fill/submit (will not abandon)",
                flush=True,
            )
            last_beat = 0.0
            last_focus = 0.0
            if focus_page_for_owner:
                try:
                    focus_page_for_owner(page, reason="ask_owner_extend")
                except Exception:
                    pass
            continue
        print("ASK_OWNER timeout — form still incomplete", flush=True)
        return None


def fill_greenhouse_combos(page) -> None:
    """Greenhouse / Lever / SmartRecruiters react-select required answers."""
    pairs = [
        (r"country of residence|current country", "India"),
        (r"^state", "N/A"),
        (r"authorized to work|legally authori[sz]ed", "Yes"),
        (r"require sponsorship|visa sponsorship", "No"),
        (r"ever been employed|previously employed", "No"),
        (r"gender", "Male"),
        (r"how did you hear|source|where did you hear", "LinkedIn"),
        (r"willing to relocate", "Yes"),
        (r"candidate source|application source", "LinkedIn"),
    ]
    for label_re, answer in pairs:
        try:
            lab = page.locator("label").filter(has_text=re.compile(label_re, re.I)).first
            if not lab.count() or not lab.is_visible():
                continue
            for_id = lab.get_attribute("for")
            combo = page.locator(f'[id="{for_id}"]').first if for_id else lab.locator("xpath=following::*[@role='combobox'][1]").first
            if not combo.count():
                continue
            combo.click(force=True)
            _sleep(0.25)
            page.keyboard.type(str(answer), delay=15)
            _sleep(0.35)
            opt = page.locator("[role='option']:visible").filter(has_text=re.compile(rf"^{re.escape(answer)}", re.I)).first
            if opt.count() and opt.is_visible():
                opt.click(force=True)
            else:
                page.keyboard.press("Enter")
            _sleep(0.2)
        except Exception:
            continue
    fill_source_fields(page)


def complete_generic(page, time_cap_s: int) -> tuple[str, str]:
    start = time.time()
    stuck = 0
    leave_oneclick_oauth(page)
    prefer_guest_apply(page)
    flags = page_flags(page)
    if is_brochure_or_dead_end(
        flags["url"],
        flags["text"],
        has_file=flags["has_file"],
        has_wd=flags["has_wd"],
        has_email=flags["has_email"],
        has_password=flags["has_password"],
        has_apply_cta=flags.get("has_apply_cta", False),
    ):
        return "skipped", "no_ats_form"
    last_fp = page_fingerprint(page)
    while time.time() - start < time_cap_s and stuck < 8:
        if looks_submitted(page):
            return "applied", "confirmation"
        if is_unavailable_text(f"{getattr(page, 'url', '')}\n{_body(page, 1200)}"):
            return "skipped", "job_unavailable"
        wall = blocked_wall(page)
        if wall == "CAPTCHA/bot wall":
            if icims_logged_in(page) and not icims_hcaptcha_login(page):
                wall = None
            else:
                try:
                    from tools.ats.captcha_solve import hcaptcha_token_present, try_clear_hcaptcha
                    if hcaptcha_token_present(page) or try_clear_hcaptcha(page):
                        wall = None
                    else:
                        return "blocked", wall
                except Exception:
                    return "blocked", wall
        if wall in ("job_closed", "job_unavailable"):
            return "skipped", wall
        if wall == "email_otp_wall":
            return "blocked", wall
        if wall == "ats_login_wall":
            guest = page.get_by_text(re.compile(r"Continue as guest|Apply without|Don't have an account", re.I)).first
            try:
                if guest.count() and guest.is_visible():
                    guest.click()
                    _sleep(1.0)
                else:
                    return "blocked", wall
            except Exception:
                return "blocked", wall
        try:
            upload_resume(page)
        except Exception:
            pass
        fill_labeled_fields(page)
        fill_yes_no(page)
        fill_greenhouse_combos(page)
        fill_source_fields(page)
        fill_validation_gaps(page)
        tick_consents(page)
        advanced = click_advance(page)
        _sleep(1.4 if advanced else 1.0)
        fp = page_fingerprint(page)
        if advanced and fp != last_fp:
            stuck = 0
            last_fp = fp
            continue
        # Validation errors — fill gaps and retry instead of abandoning.
        if re.search(r"required|please (select|complete|fill)|errors? found", _body(page, 1200), re.I):
            if fill_validation_gaps(page) or fill_source_fields(page):
                if click_advance(page):
                    stuck = 0
                    last_fp = page_fingerprint(page)
                    continue
        stuck += 1
        last_fp = fp
    if looks_submitted(page):
        return "applied", "confirmation"
    owner = wait_owner_finish_apply(
        page, hint="Source / How did you hear / required fields / Submit"
    )
    if owner:
        return owner
    if apply_form_still_open(page):
        burst = persist_retry_burst_sec()
        if burst <= 0:
            return "blocked", "external_incomplete_or_timeout"
        print(
            f"generic=persist_retry — ASK_OWNER timed out but form still open; fill again ({burst}s)",
            flush=True,
        )
        # Short aggressive burst — do not nest another full owner wait.
        burst_start = time.time()
        while time.time() - burst_start < burst:
            if looks_submitted(page):
                return "applied", "confirmation"
            if looks_already_applied(page):
                return "skipped", "already_applied"
            wall = blocked_wall(page)
            if wall == "email_otp_wall":
                return "blocked", wall
            try:
                upload_resume(page)
                fill_labeled_fields(page)
                fill_source_fields(page)
                fill_validation_gaps(page)
                fill_yes_no(page)
                tick_consents(page)
                click_advance(page)
            except Exception:
                pass
            _sleep(1.0)
        if looks_submitted(page):
            return "applied", "confirmation"
        wall = blocked_wall(page)
        if wall == "email_otp_wall":
            return "blocked", wall
    return "blocked", "external_incomplete_or_timeout"


def icims_active_frame(page):
    """Prefer the nested ``in_iframe=1`` apply/login document (has Email / I accept).

    Outer ``/jobs/N/login`` chrome often matches first but has no form fields —
    always scan for ``in_iframe=1`` (or a frame that actually exposes email) first.
    """
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []

    def _frame_has_gdpr_form(fr) -> bool:
        try:
            return bool(
                fr.evaluate(
                    """() => {
                      const email = document.querySelector(
                        "input[type='email'], input[name*='email' i], input[id*='email' i]"
                      );
                      const t = (document.body && document.body.innerText || '');
                      return !!(email || /I accept/i.test(t));
                    }"""
                )
            )
        except Exception:
            return False

    # 1) Explicit in_iframe=1 apply/login documents
    for fr in frames:
        u = getattr(fr, "url", "") or ""
        if "in_iframe=1" in u and re.search(r"icims\.com/jobs/\d+", u, re.I):
            return fr
    # 2) Any icims frame that actually has Email / I accept
    for fr in frames:
        u = getattr(fr, "url", "") or ""
        if re.search(r"icims\.com/jobs/\d+", u, re.I) and _frame_has_gdpr_form(fr):
            return fr
    # 3) Fallback: login/apply/questions URLs
    for fr in frames:
        u = getattr(fr, "url", "") or ""
        if re.search(r"icims\.com/jobs/\d+", u, re.I) and (
            "/login" in u
            or "mode=apply" in u
            or "/questions" in u
            or "/form" in u
            or "/eeo" in u
            or "/candidate" in u
        ):
            return fr
    return page


def fill_icims_candidate_profile(page) -> bool:
    """Fast-path iCIMS Candidate Profile fill by field name (not slow label crawl).

    Post-captcha profiles were taking minutes because ``fill_labeled_fields`` walks
    ~70 labels with per-label timeouts. iCIMS exposes stable ``PersonProfileFields.*``
    names — fill those in one frame.evaluate.
    """
    target = icims_active_frame(page)
    email = ats_email()
    payload = {
        "email": email,
        "first": PROFILE["first"],
        "last": PROFILE["last"],
        "phone": PROFILE["phone"],
        "linkedin": PROFILE["linkedin"],
        "city": PROFILE["city"],
        "state": PROFILE["state"],
        "country": PROFILE["country"],
        "postal": PROFILE.get("postal") or "500081",
        "school": PROFILE.get("school") or "JNTU Hyderabad",
        "sourceText": "LinkedIn",
    }
    try:
        ok = target.evaluate(
            """(p) => {
              const setter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
              ).set;
              let n = 0;
              const text = (name, val) => {
                const el = document.querySelector('[name=\"' + name + '\"]');
                if (!el || val == null || val === '') return;
                try {
                  el.focus();
                  setter.call(el, String(val));
                  el.dispatchEvent(new Event('input', { bubbles: true }));
                  el.dispatchEvent(new Event('change', { bubbles: true }));
                  n++;
                } catch (e) {}
              };
              const sel = (name, prefs) => {
                const el = document.querySelector('[name=\"' + name + '\"]');
                if (!el || !el.options) return;
                const opts = Array.from(el.options);
                for (const pref of prefs) {
                  const hit =
                    opts.find(o => (o.text || '').trim().toLowerCase() === pref.toLowerCase()) ||
                    opts.find(o => (o.text || '').toLowerCase().includes(pref.toLowerCase()));
                  if (hit) {
                    el.value = hit.value;
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    n++;
                    return;
                  }
                }
              };
              const flag = document.querySelector('[name=icimsCookiesEnabledCheck]');
              if (flag) flag.value = 'true';
              text('PersonProfileFields.Login', p.email);
              text('PersonProfileFields.FirstName', p.first);
              text('PersonProfileFields.LastName', p.last);
              text('PersonProfileFields.Email', p.email);
              text('rcf2268', p.linkedin);
              sel('-1_PersonProfileFields.PhoneType', ['Mobile', 'Cell', 'Home']);
              text('-1_PersonProfileFields.PhoneNumber', p.phone);
              sel('-1_PersonProfileFields.AddressType', ['Home', 'Mailing']);
              text('-1_PersonProfileFields.AddressStreet1', p.city);
              text('-1_PersonProfileFields.AddressCity', p.city);
              text('-1_PersonProfileFields.AddressZip', p.postal);
              sel('-1_PersonProfileFields.AddressCountry', [p.country, 'India']);
              sel('-1_PersonProfileFields.AddressState', [p.state, 'Telangana', 'Andhra Pradesh']);
              sel('rcf3048', ['Internet Job Board', 'Job Board', 'LinkedIn', 'Company Website']);
              text('rcf3049_Text', p.sourceText);
              text('-1_CandProfileFields.OtherSchool', p.school);
              sel('-1_CandProfileFields.IsGraduated', ['Received', 'Yes']);
              sel('-1_CandProfileFields.GraduationDate_Month', ['May', '5']);
              text('-1_CandProfileFields.GraduationDate_Year', '2008');
              // iCIMS ajax dropdowns (Degree/Major) — type into sibling search + click result.
              const ajaxPick = (selectName, query, pickRe) => {
                const selEl = document.querySelector('[name="' + selectName + '"]');
                if (!selEl) return;
                let box = selEl.parentElement;
                for (let i = 0; i < 6 && box; i++) {
                  if (box.querySelector && box.querySelector('input.dropdown-search')) break;
                  box = box.parentElement;
                }
                if (!box) return;
                const search = box.querySelector('input.dropdown-search');
                if (!search) return;
                search.focus();
                search.value = query;
                search.dispatchEvent(new Event('input', { bubbles: true }));
                search.dispatchEvent(new Event('keyup', { bubbles: true }));
                const results = box.querySelector('.dropdown-results') || document.querySelector('.dropdown-results');
                if (!results) return;
                results.style.display = 'block';
                const pre = new RegExp(pickRe, 'i');
                const hit = [...results.querySelectorAll('div, li, a, span')].find(
                  (k) => pre.test((k.innerText || '').trim()) && (k.innerText || '').trim().length < 90
                );
                if (hit) {
                  hit.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                  hit.click();
                  n++;
                }
              };
              ajaxPick('-1_CandProfileFields.Degree', 'Bachelor', 'Bachelor');
              ajaxPick('-1_CandProfileFields.Major', 'Computer Science', 'Computer Science|Computer Eng');
              return n > 0;
            }""",
            payload,
        )
        if ok:
            print(f"icims=fast_profile_fill fields_ok", flush=True)
        return bool(ok)
    except Exception as exc:
        print(f"icims=fast_profile_fill_err {exc!s}"[:180], flush=True)
        return False


def icims_fill_gdpr_gate(page) -> bool:
    """Fill Email + check I accept + click Next on iCIMS GDPR/login gate."""
    target = icims_active_frame(page)
    email = ats_email()
    progressed = False
    if email:
        try:
            box = target.locator(
                "input[type='email'], input[name*='email' i], input[id*='email' i]"
            ).first
            if box.count() and box.is_visible():
                box.click(timeout=2000)
                box.fill(email, timeout=4000)
                progressed = True
                _sleep(0.3)
        except Exception:
            pass
    # Checkbox + "I accept" label (Next stays disabled until checked).
    try:
        cbs = target.locator("input[type='checkbox']")
        for i in range(min(cbs.count(), 6)):
            cb = cbs.nth(i)
            if not cb.is_visible():
                continue
            near = ""
            try:
                near = cb.evaluate(
                    "e => ((e.closest('label,div,li,tr,fieldset')||e.parentElement).innerText||'')"
                )
            except Exception:
                near = ""
            if re.search(r"accept|privacy|notice|consent|agree", near or "", re.I) or cbs.count() == 1:
                if not cb.is_checked():
                    try:
                        cb.check(force=True)
                    except Exception:
                        cb.click(force=True)
                if cb.is_checked():
                    progressed = True
                break
    except Exception:
        pass
    try:
        acc = target.get_by_text(re.compile(r"^I accept$", re.I)).first
        if acc.count() and acc.is_visible():
            acc.click(timeout=2500, force=True)
            progressed = True
            _sleep(0.3)
    except Exception:
        pass
    try:
        lab = target.locator("label").filter(has_text=re.compile(r"I accept", re.I)).first
        if lab.count() and lab.is_visible():
            lab.click(force=True)
            progressed = True
            _sleep(0.3)
    except Exception:
        pass
    if _click_text(target, ("Next", "Continue", "Submit", "I accept")):
        progressed = True
        _sleep(0.8)
    return progressed


def complete_icims(page, time_cap_s: int) -> tuple[str, str]:
    """Click iframe Apply, clear hCaptcha (owner click, checkbox, or paid solver), then fill."""
    from tools.ats.captcha_solve import (
        captcha_solver_configured,
        owner_captcha_wait_sec,
        try_clear_hcaptcha,
    )

    prefer_icims_apply(page)
    _sleep(1.6)
    # Always fill GDPR gate in the nested in_iframe=1 document first.
    icims_fill_gdpr_gate(page)
    target = icims_active_frame(page)
    if icims_should_wait_captcha(page):
        cleared = try_clear_hcaptcha(page)
        if not cleared:
            # Owner may have finished apply during the wait; confirmation beats wall.
            if looks_submitted(page) or looks_already_applied(page):
                return (
                    ("applied", "confirmation")
                    if looks_submitted(page)
                    else ("skipped", "already_applied")
                )
            if owner_captcha_wait_sec() > 0:
                return "blocked", "owner_captcha_unsolved"
            if not captcha_solver_configured():
                return "blocked", "captcha_needs_owner_or_solver"
            return "blocked", "CAPTCHA/bot wall"
        # After owner captcha — stay on this application and finish profile/submit.
        print("icims=post_captcha_continue — filling profile through submit", flush=True)
        dismiss_cookies(page)
        icims_fill_gdpr_gate(page)
        target = icims_active_frame(page)
        try:
            _click_text(
                target,
                ("Continue", "Next", "Submit", "I accept", "Apply"),
            )
            _sleep(0.6)
        except Exception:
            pass
    if looks_submitted(page) or looks_submitted(target):
        return "applied", "confirmation"
    start = time.time()
    stuck = 0
    last_fp = page_fingerprint(page)
    while time.time() - start < max(20, int(time_cap_s) - 10) and stuck < 14:
        target = icims_active_frame(page)
        if looks_submitted(page) or looks_submitted(target):
            return "applied", "confirmation"
        if looks_already_applied(page):
            return "skipped", "already_applied"
        # Re-assert GDPR fields if the wall reappears mid-flow.
        if icims_hcaptcha_login(page) or re.search(r"/login", getattr(target, "url", "") or "", re.I):
            icims_fill_gdpr_gate(page)
            target = icims_active_frame(page)
        progressed = False
        # Fast name-based profile fill first (seconds, not minutes).
        if fill_icims_candidate_profile(page):
            progressed = True
        try:
            upload_resume(target)
            progressed = True
        except Exception:
            try:
                upload_resume(page)
            except Exception:
                pass
        try:
            fill_source_fields(target)
            fill_validation_gaps(target)
            tick_consents(target)
            progressed = True
        except Exception:
            pass
        if fill_icims_questions(page):
            progressed = True
        if advance_icims_us_forms(page):
            stuck = 0
            last_fp = page_fingerprint(page)
            _sleep(0.5)
            continue
        # Never Submit while required selects are still empty.
        if icims_click_submit_if_ready(page):
            stuck = 0
            last_fp = page_fingerprint(page)
            _sleep(0.7)
            continue
        fp = page_fingerprint(page)
        if fp != last_fp or progressed:
            stuck = max(0, stuck - 1)
            last_fp = fp
        else:
            stuck += 1
        _sleep(0.4)
    if looks_submitted(page):
        return "applied", "confirmation"
    remaining = max(60, int(time_cap_s) - int(time.time() - start) - 5)
    status, reason = complete_generic(page, remaining)
    if status == "blocked" and "incomplete" in (reason or "") and apply_form_still_open(page):
        print("icims=persist_retry — form still open after owner wait; one more fill pass", flush=True)
        # One more fast profile + submit burst before giving up.
        fill_icims_candidate_profile(page)
        try:
            upload_resume(icims_active_frame(page))
        except Exception:
            pass
        icims_fill_required_selects(page)
        icims_click_submit_if_ready(page)
        status, reason = complete_generic(page, max(90, remaining))
    return status, reason


def complete_ats(page, time_cap_s: int | None = None) -> tuple[str, str]:
    """Fill + submit the current ATS page. Returns (status, reason)."""
    cap = int(time_cap_s or DEFAULT_TIME_CAP_S)
    if looks_submitted(page):
        return "applied", "confirmation"
    if looks_already_applied(page):
        return "skipped", "already_applied"
    flags = page_flags(page)
    host = classify_ats_host(flags["url"])
    icims_url = bool(re.search(r"icims\.com/jobs/\d+", flags["url"], re.I))
    if not icims_url:
        try:
            icims_url = any(
                re.search(r"icims\.com/jobs/\d+", getattr(fr, "url", "") or "", re.I)
                for fr in getattr(page, "frames", []) or []
            )
        except Exception:
            icims_url = False
    if icims_url:
        return complete_icims(page, cap)
    if visible_captcha_challenge(page):
        return "blocked", "CAPTCHA/bot wall"
    if host == "unavailable" or is_unavailable_text(f"{flags['url']}\n{flags['text']}"):
        return "skipped", "job_unavailable"
    if host == "sso":
        return "blocked", "ats_login_wall"
    if host == "linkedin":
        return "blocked", "did_not_leave_linkedin"
    if host == "indeed" and is_board_tracking_url(flags["url"]):
        return "blocked", "did_not_leave_indeed"
    wall = auth_wall_reason(
        flags["url"],
        flags["text"],
        has_password=flags["has_password"],
        has_file=flags["has_file"],
        has_workday_apply=flags["has_wd"],
        has_email_field=flags["has_email"],
    )
    if wall in ("job_closed", "job_unavailable"):
        return "skipped", wall
    if wall and host != "workday" and not flags["has_wd"]:
        return "blocked", wall
    if host == "workday" or flags["has_wd"]:
        return complete_workday(page, cap)
    if is_brochure_or_dead_end(
        flags["url"],
        flags["text"],
        has_file=flags["has_file"],
        has_wd=flags["has_wd"],
        has_email=flags["has_email"],
        has_password=flags["has_password"],
        has_apply_cta=flags.get("has_apply_cta", False),
    ):
        prefer_guest_apply(page)
        flags = page_flags(page)
        if is_brochure_or_dead_end(
            flags["url"],
            flags["text"],
            has_file=flags["has_file"],
            has_wd=flags["has_wd"],
            has_email=flags["has_email"],
            has_password=flags["has_password"],
            has_apply_cta=flags.get("has_apply_cta", False),
        ):
            return "skipped", "no_ats_form"
    return complete_generic(page, cap)


def complete_ats_url(url: str, time_cap_s: int | None = None, cdp: str | None = None) -> tuple[str, str, str]:
    """Open an ATS URL in Playwright and complete it. Returns (status, reason, final_url)."""
    from playwright.sync_api import sync_playwright

    cap = int(time_cap_s or DEFAULT_TIME_CAP_S)
    cdp_url = cdp or os.environ.get("ATS_CDP") or os.environ.get("LINKEDIN_CDP") or "http://127.0.0.1:9222"
    with sync_playwright() as p:
        owned = False
        browser = None
        try:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.new_page()
        except Exception:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            owned = True
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            _sleep(1.2)
            # Indeed/LinkedIn/Naukri "Apply on company site" often lands on a
            # tracking hop (applystart / rc/clk). Follow dest query / meta /
            # outbound apply link instead of waiting 18s then giving up.
            deadline = time.time() + 18
            while time.time() < deadline and is_board_tracking_url(getattr(page, "url", "") or ""):
                dest = extract_hop_destination(page)
                if dest:
                    try:
                        page.goto(dest, wait_until="domcontentloaded", timeout=45000)
                        _sleep(1.0)
                        break
                    except Exception:
                        pass
                _sleep(0.8)
            if is_unavailable_text(f"{getattr(page, 'url', '')}\n{_body(page, 1200)}"):
                return "skipped", "job_unavailable", page.url or url
            if is_board_tracking_url(getattr(page, "url", "") or ""):
                dest = extract_hop_destination(page)
                if dest:
                    try:
                        page.goto(dest, wait_until="domcontentloaded", timeout=45000)
                        _sleep(1.0)
                    except Exception:
                        dest = ""
                if is_board_tracking_url(getattr(page, "url", "") or ""):
                    host = classify_ats_host(page.url or url)
                    if host == "indeed":
                        return "blocked", "did_not_leave_indeed", page.url or url
                    if host == "linkedin":
                        return "blocked", "did_not_leave_linkedin", page.url or url
            status, reason = complete_ats(page, time_cap_s=cap)
            return status, reason, page.url or url
        finally:
            try:
                if not owned:
                    page.close()
            except Exception:
                pass
            if owned and browser is not None:
                browser.close()


def host_label(url: str | None) -> str:
    try:
        return urlparse(url or "").netloc or "unknown"
    except Exception:
        return "unknown"
