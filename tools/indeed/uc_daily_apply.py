#!/usr/bin/env python3
"""Indeed Easy Apply via SeleniumBase UC + WARP SOCKS (cloud Cloudflare path).

Plain Chrome CDP through WARP still gets Request Blocked. UC mode works.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@contextlib.contextmanager
def _stdout_to_stderr():
    """Keep final report JSON clean when SeleniumBase prints driver downloads."""
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2), file=sys.__stdout__, flush=True)


def _patch_filelock_singleton() -> None:
    """SeleniumBase nests FileLock(pyautogui.lock); filelock 3.20+ deadlocks without singleton."""
    try:
        sys.path.insert(0, str(ROOT))
        from tools.indeed.filelock_patch import patch_filelock_singleton

        patch_filelock_singleton(ROOT)
        print("  filelock_singleton=1", flush=True)
    except Exception as exc:
        print(f"  filelock_patch_error={exc!s}"[:180], flush=True)


OUT = Path(
    os.environ.get(
        "INDEED_DAILY_REPORT",
        str(
            Path("/opt/cursor/artifacts/indeed-daily-run.json")
            if Path("/opt/cursor/artifacts").is_dir()
            else ROOT / "artifacts" / "indeed-daily-run.json"
        ),
    )
)
RESUME = Path(
    os.environ.get(
        "RAFI_RESUME",
        str(ROOT / "resumes" / "Rafi_Resume.docx"),
    )
)
PROXY = os.environ.get("INDEED_HTTP_PROXY", "socks5://127.0.0.1:40000")
# Hybrid UC profile (auth cookies, CF cookies stripped) — see prepare_uc_profile.py
PROFILE = os.environ.get("INDEED_UC_PROFILE", "/tmp/cursor/indeed-uc-hybrid")


def _job_id_from_url(url: str) -> str:
    m = re.search(r"[?&]jk=([a-f0-9]+)", url or "", re.I)
    return m.group(1) if m else ""


def prepare_resume_for_job(item: dict, jd_text: str) -> Path:
    """JD-tailor Rafi_Resume.docx and point Easy Apply / ATS uploads at it."""
    title = str(item.get("title") or "")
    company = str(item.get("company") or "")
    url = str(item.get("url") or "")
    jid = _job_id_from_url(url) or "indeed"
    try:
        from tools.resume_paths import clear_active_resume, set_active_resume
        from tools.resume_tailor import tailor_resume_for_job

        tailored = tailor_resume_for_job(
            job_id=jid, title=title, company=company, jd=jd_text or ""
        )
        set_active_resume(tailored)
        os.environ["RESUME_UPLOAD_PATH"] = str(tailored)
        os.environ["RAFI_RESUME"] = str(tailored)
        item["tailoredResume"] = str(tailored)
        return Path(tailored)
    except Exception as exc:
        print(f"  resume_tailor_error={exc!s}"[:200], flush=True)
        try:
            from tools.resume_paths import clear_active_resume

            clear_active_resume()
        except Exception:
            pass
        return RESUME


def clear_job_resume() -> None:
    try:
        from tools.resume_paths import clear_active_resume

        clear_active_resume()
    except Exception:
        pass
    for key in ("RESUME_UPLOAD_PATH",):
        if key in os.environ and "/tailored-resumes/" in os.environ.get(key, ""):
            os.environ.pop(key, None)
    # Restore canonical RAFI_RESUME if we overwrote it with a tailored path.
    if "/tailored-resumes/" in os.environ.get("RAFI_RESUME", ""):
        canonical = ROOT / "resumes" / "Rafi_Resume.docx"
        if canonical.is_file():
            os.environ["RAFI_RESUME"] = str(canonical)


def _default_seed_profile() -> str:
    env = os.environ.get("INDEED_SEED_PROFILE")
    if env:
        return env
    win = Path.home() / ".cursor" / "chrome-cdp-profiles" / "indeed"
    linux = Path("/home/ubuntu/chrome-indeed-profile")
    if win.exists():
        return str(win)
    return str(linux)


SEED_PROFILE = _default_seed_profile()


def warm_passport_session(sb) -> None:
    """Touch Indeed Passport so applystart/rc/clk hops inherit the logged-in session."""
    try:
        sb.uc_open_with_reconnect("https://secure.indeed.com/settings/account", 4)
        time.sleep(2.0)
        sb.uc_open_with_reconnect("https://in.indeed.com/", 3)
        time.sleep(1.0)
        print("PASSPORT_WARM ok", flush=True)
    except Exception as exc:
        print(f"PASSPORT_WARM skip {exc}"[:160], flush=True)


def _sb_call_timeout(fn, timeout_s: float, default=None):
    """Run a Selenium call in a worker thread; abandon if it exceeds timeout_s.

    UC Chrome can wedge on page-load waits after "Apply on company site". A hung
    get_current_url must not freeze the whole daily inventory.
    """
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(fn)
        try:
            return fut.result(timeout=timeout_s)
        except Exception:
            return default


def complete_external_ats(url: str, time_cap_s: int | None = None) -> tuple[str, str, str]:
    """Finish a company-site ATS after Indeed opens it. Confirmation only.

    Indeed "Apply on company site" often leaves us on applystart/rc/clk —
    the completer follows that hop. Only fail if we never leave Indeed.

    Always runs in a **subprocess** with ``ATS_CDP=0`` (owned Chromium). Attaching
    Playwright to UC's ``:9222`` deadlocks SeleniumBase mid-inventory.
    """
    if not url:
        return "blocked", "did_not_leave_indeed", ""
    cap = int(time_cap_s or os.environ.get("INDEED_ATS_TIME_CAP_S") or 390)
    hard = max(cap + 45, 90)
    env = os.environ.copy()
    env["ATS_CDP"] = "0"
    env["ATS_TIME_CAP_S"] = str(cap)
    # Don't inherit WARP SOCKS for employer ATS — many corp sites fail through it.
    for k in ("ALL_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "all_proxy"):
        env.pop(k, None)
    helper = (
        "import json,sys\n"
        "from tools.ats.complete import complete_ats_url\n"
        "u,c=sys.argv[1],int(sys.argv[2])\n"
        "s,r,f=complete_ats_url(u,time_cap_s=c,cdp='0')\n"
        "print(json.dumps({'status':s,'reason':r,'finalUrl':f}))\n"
    )
    try:
        res = subprocess.run(
            [sys.executable, "-c", helper, url, str(cap)],
            capture_output=True,
            text=True,
            timeout=hard,
            env=env,
            cwd=str(ROOT),
        )
    except subprocess.TimeoutExpired:
        print(f"EXTERNAL ats_subprocess_timeout cap={cap}s url={url[:120]}", flush=True)
        return "blocked", "external_incomplete_or_timeout", url
    except Exception as exc:
        return "blocked", f"ats_helper_error:{exc}"[:180], url
    raw = (res.stdout or "").strip()
    if res.returncode != 0 and not raw:
        err = (res.stderr or "")[:160].replace("\n", " ")
        return "blocked", f"ats_helper_error:{err or f'exit {res.returncode}'}"[:180], url
    try:
        # Last JSON object on stdout (playwright may noise).
        idx = raw.rfind("{")
        payload = json.loads(raw[idx:] if idx >= 0 else raw)
        return (
            str(payload.get("status") or "blocked"),
            str(payload.get("reason") or "ats_helper_error")[:180],
            str(payload.get("finalUrl") or url),
        )
    except Exception as exc:
        err = (res.stderr or raw or str(exc))[:160].replace("\n", " ")
        return "blocked", f"ats_helper_error:{err}"[:180], url


def _record_external_result(item, report, status, reason, final_url, ats_url=""):
    item["atsUrl"] = final_url or ats_url
    item["reason"] = reason
    item["path"] = "company_ATS"
    if status == "applied":
        item["confirmed"] = True
        report["external"].append(item)
        report["counts"]["external"] += 1
        print("EXTERNAL submitted", (item.get("title") or "")[:80], flush=True)
    else:
        report["blocked"].append(item)
        report["counts"]["blocked"] += 1
        print("EXTERNAL blocked", reason, flush=True)


def finish_company_site(sb, item, report, handles_before=None) -> None:
    """Wait for Indeed tracking hops, then complete the employer ATS."""
    # Bound page-load waits so a stuck employer tab cannot freeze Selenium forever.
    try:
        sb.driver.set_page_load_timeout(25)
        sb.driver.set_script_timeout(25)
    except Exception:
        pass
    time.sleep(2.0)
    ats_url = ""

    def _read_ats_url() -> str:
        handles_after = list(sb.driver.window_handles)
        new_h = [h for h in handles_after if h not in (handles_before or [])]
        if new_h:
            sb.switch_to_window(new_h[-1])
        return sb.get_current_url() or ""

    ats_url = _sb_call_timeout(_read_ats_url, 30, "") or ""
    if not ats_url:
        # Prefer any non-Indeed tab URL via a second timed probe.
        def _any_external() -> str:
            for h in list(sb.driver.window_handles):
                try:
                    sb.switch_to_window(h)
                    u = sb.get_current_url() or ""
                    if u.startswith("http") and "indeed.com" not in u.lower():
                        return u
                except Exception:
                    continue
            return ""

        ats_url = _sb_call_timeout(_any_external, 20, "") or ""
    if ats_url and "indeed.com" in ats_url.lower():
        dest = ""
        try:
            sys.path.insert(0, str(ROOT))
            from tools.ats.complete import extract_hop_destination_from_url

            dest = extract_hop_destination_from_url(ats_url)
        except Exception:
            dest = ""
        if dest:
            ats_url = dest
        else:
            for _ in range(8):
                time.sleep(1.0)
                nxt = _sb_call_timeout(lambda: sb.get_current_url() or "", 10, "") or ""
                if nxt:
                    ats_url = nxt
                if ats_url and "indeed.com" not in ats_url.lower():
                    break
                try:
                    dest = extract_hop_destination_from_url(ats_url)
                except Exception:
                    dest = ""
                if dest:
                    ats_url = dest
                    break
    print(f"EXTERNAL ats_url={ats_url[:160]!r}", flush=True)
    status, reason, final_url = complete_external_ats(ats_url)
    _record_external_result(item, report, status, reason, final_url, ats_url)

    def _close_extra_tabs() -> None:
        handles = list(sb.driver.window_handles)
        if len(handles) <= 1:
            return
        for h in handles[1:]:
            try:
                sb.switch_to_window(h)
                sb.driver.close()
            except Exception:
                pass
        try:
            sb.switch_to_window(handles[0])
        except Exception:
            pass

    _sb_call_timeout(_close_extra_tabs, 20, None)
    try:
        sb.driver.set_page_load_timeout(60)
    except Exception:
        pass
# Volume: cron used to stop at 8 applies / 40 seen — raise so each run
# exhausts Hyd/remote inventory instead of soft-stopping early.
MAX_APPLIES = int(os.environ.get("INDEED_MAX_APPLIES", "40"))
MAX_SEEN = int(os.environ.get("INDEED_MAX_SEEN", "120"))

TITLE_OK = re.compile(
    # Require azure/cloud stack tokens — not Salesforce "service cloud" product.
    r"(architect|tech(?:nical)?\s*lead|engineering\s*manager|\bEM\b|"
    r"principal|staff|senior).{0,40}(\.?\s*net|c#|azure|(?<!service\s)cloud)|"
    r"(\.?\s*net|c#|azure).{0,40}(architect|tech(?:nical)?\s*lead|"
    r"engineering\s*manager|principal|staff)|"
    r"(solutions?\s*architect|technical\s*architect|software\s*architect|"
    r"cloud\s*architect|application\s*architect|enterprise\s*architect|"
    r"system\s*architect|platform\s*architect)",
    re.I,
)
TITLE_SKIP = re.compile(
    r"\b(java|python|node\.?js|golang|ruby|php)\b.{0,20}\b(only|mandatory|must)\b|"
    r"\b(qa|sdet|quality\s*analyst|intern|junior|graduate|trainee)\b|"
    # Salesforce / ServiceNow / SAP product-primary titles (incl. Success Architect + Service Cloud).
    r"\b(salesforce|servicenow|\bsap\b|sfdc|service\s*cloud|sales\s*cloud|"
    r"experience\s*cloud|marketing\s*cloud|commerce\s*cloud)\b|"
    r"\b(android|ios|flutter|react\s*native)\b.{0,20}\b(developer|engineer)\b",
    re.I,
)
LOC_OK = re.compile(
    r"hyderabad|telangana|\bhyd\b|remote|work\s*from\s*home|\bwfh\b|india\s*remote",
    re.I,
)
# Non-Hyd city/state without a remote/WFH signal → skip (HARD location rule).
# Include Kochi/Kerala etc. — empty SERP location + city-in-title used to slip through.
LOC_HARD_SKIP = re.compile(
    r"\b(bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|gurugram|"
    r"delhi|kolkata|ahmedabad|kochi|cochin|coimbatore|madurai|jaipur|"
    r"chandigarh|indore|lucknow|mysore|mysuru|trivandrum|thiruvananthapuram|"
    r"vizag|visakhapatnam|nagpur|surat|vadodara|patna|bhubaneswar|"
    r"kerala|karnataka|maharashtra|tamil\s*nadu|gujarat|rajasthan|"
    r"west\s*bengal|odisha|punjab|haryana)\b(?!.{0,40}(remote|wfh|hybrid))",
    re.I,
)


def ensure_warp() -> str:
    if os.environ.get("INDEED_SKIP_WARP") == "1":
        # Home / residential: apply on the machine IP (no WARP SOCKS).
        proxy = os.environ.get("INDEED_HTTP_PROXY", "")
        if proxy and "127.0.0.1:40000" in proxy:
            proxy = ""
        os.environ["INDEED_HTTP_PROXY"] = proxy
        print(f"  warp_skipped=1 proxy={proxy or 'direct'}", flush=True)
        return proxy
    existing = os.environ.get("INDEED_HTTP_PROXY", "")
    if existing and "127.0.0.1:40000" not in existing and "localhost:40000" not in existing:
        return existing
    script = ROOT / "scripts" / "ensure-indeed-warp.sh"
    res = subprocess.run(
        ["bash", str(script)], capture_output=True, text=True, timeout=120
    )
    m = re.search(r"export INDEED_HTTP_PROXY=(.+)", res.stdout or "")
    if res.returncode != 0 or not m:
        # Windows home fallback: continue without proxy rather than abort.
        if os.name == "nt" or os.environ.get("OS") == "Windows_NT" or os.environ.get("MSYSTEM"):
            print("  warp_unavailable_home_fallback=1", flush=True)
            os.environ["INDEED_HTTP_PROXY"] = ""
            return ""
        raise SystemExit(f"WARP not ready: {res.stderr or res.stdout}")
    proxy = m.group(1).strip().strip("'\"")
    os.environ["INDEED_HTTP_PROXY"] = proxy
    return proxy


def prepare_profile() -> dict:
    script = ROOT / "tools" / "indeed" / "prepare_uc_profile.py"
    res = subprocess.run(
        [
            sys.executable,
            str(script),
            "--src",
            SEED_PROFILE,
            "--dst",
            PROFILE,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return json.loads(res.stdout or "{}")
    except Exception:
        return {"error": (res.stderr or res.stdout or "")[:400], "exit": res.returncode}


def clear_cf(sb, attempts: int = 4) -> bool:
    """Clear Indeed Cloudflare / Turnstile using the same path as preflight.

    Important: after a Turnstile GUI click we must reload (uc_open_with_reconnect).
    Returning True on title-only "not blocked" without reload leaves an anonymous
    homepage ("Get Started") even when Passport cookies are valid — preflight's
    cf_bypass_uc.try_clear_strategies always reloads and restores Welcome.
    """
    try:
        from tools.indeed.cf_bypass_uc import (
            blocked_blob,
            looks_healthy,
            page_snapshot,
            try_clear_strategies,
        )
    except Exception:
        blocked_blob = None  # type: ignore[assignment]
        looks_healthy = None  # type: ignore[assignment]
        page_snapshot = None  # type: ignore[assignment]
        try_clear_strategies = None  # type: ignore[assignment]

    if try_clear_strategies is not None:
        for _ in range(max(1, attempts)):
            title, cur_url, text = page_snapshot(sb)
            if looks_healthy(title, text, cur_url) and not blocked_blob(
                title, text, cur_url
            ):
                return True
            if blocked_blob(title, text, cur_url) or blocked(title, text):
                try_clear_strategies(sb)
                title, cur_url, text = page_snapshot(sb)
                if looks_healthy(title, text, cur_url) and not blocked_blob(
                    title, text, cur_url
                ):
                    return True
            else:
                # Not a CF interstitial but not healthy either — hard reload once.
                try:
                    sb.uc_open_with_reconnect(
                        cur_url or "https://in.indeed.com/", 4
                    )
                except Exception:
                    pass
                time.sleep(2)
                title, cur_url, text = page_snapshot(sb)
                if looks_healthy(title, text, cur_url) and not blocked_blob(
                    title, text, cur_url
                ):
                    return True
        title, cur_url, text = page_snapshot(sb)
        return bool(
            looks_healthy(title, text, cur_url)
            and not blocked_blob(title, text, cur_url)
        )

    # Fallback if cf_bypass helpers cannot be imported.
    strategies = (
        ("uc_gui_click_cf", lambda: sb.uc_gui_click_cf()),
        ("uc_gui_click_cf_retry", lambda: sb.uc_gui_click_cf(retry=True)),
        ("uc_gui_handle_cf", lambda: sb.uc_gui_handle_cf()),
        ("uc_gui_click_captcha", lambda: sb.uc_gui_click_captcha()),
        ("uc_gui_click_cf_blind", lambda: sb.uc_gui_click_cf(blind=True)),
        ("uc_gui_handle_captcha", lambda: sb.uc_gui_handle_captcha()),
    )
    for _ in range(attempts):
        title = sb.get_title() or ""
        try:
            text = sb.get_text("body") or ""
        except Exception:
            text = ""
        if not blocked(title, text):
            # Mirror preflight: reload so Passport session paints Welcome.
            try:
                sb.uc_open_with_reconnect(
                    sb.get_current_url() or "https://in.indeed.com/", 4
                )
            except Exception:
                pass
            time.sleep(2)
            return True
        for _name, fn in strategies:
            try:
                fn()
            except Exception:
                continue
            time.sleep(6)
            try:
                sb.uc_open_with_reconnect(
                    sb.get_current_url() or "https://in.indeed.com/", 4
                )
            except Exception:
                pass
            time.sleep(2)
            title = sb.get_title() or ""
            try:
                text = sb.get_text("body") or ""
            except Exception:
                text = ""
            if not blocked(title, text):
                return True
    title = sb.get_title() or ""
    try:
        text = sb.get_text("body") or ""
    except Exception:
        text = ""
    return not blocked(title, text)


def blocked(title: str, text: str) -> bool:
    blob = f"{title}\n{text}".lower()
    return any(
        x in blob
        for x in (
            "request blocked",
            "additional verification required",
            "just a moment",
            "security check - indeed",
            "you have been blocked",
        )
    )


def _campus_allowlist_blocks(company: str) -> bool:
    """When Hitech City board mode sets HITECHCITY_COMPANY_ALLOWLIST, enforce it."""
    if not os.environ.get("HITECHCITY_COMPANY_ALLOWLIST"):
        return False
    try:
        from tools.hitechcity.campus_allowlist import company_allowed

        return not company_allowed(company or "")
    except Exception:
        return False


def skip_reason(title: str, company: str, location: str, snippet: str) -> str | None:
    t = title or ""
    if _campus_allowlist_blocks(company):
        return "hitechcity_campus_allowlist"
    if TITLE_SKIP.search(t):
        return "title_skip"
    # Company is Salesforce/ServiceNow product shop unless title clearly .NET/Azure.
    if re.search(r"salesforce|servicenow", company or "", re.I) and not re.search(
        r"\.net|dotnet|\bc#\b|azure", t, re.I
    ):
        return "company_wrong_stack"
    if not TITLE_OK.search(t):
        # Bias: when uncertain on architect/lead/.NET titles → apply.
        # Only skip clear non-matches (no senior/architect/lead/.net signal).
        if not re.search(
            r"architect|tech(?:nical)?\s*lead|engineering\s*manager|principal|staff|senior|\.net|\bc#\b",
            t,
            re.I,
        ):
            return "title_not_target"
    loc_field = location or ""
    # Job location + title decide Hyd/Remote. Do not let SERP chrome
    # ("Find remote jobs") in the snippet override a Bengaluru-only posting.
    loc_blob = f"{loc_field} {t}"
    if LOC_HARD_SKIP.search(loc_blob) and not LOC_OK.search(loc_blob):
        return "location"
    if loc_field and not LOC_OK.search(loc_blob):
        if re.search(
            r"bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon|delhi|"
            r"kochi|cochin|coimbatore|madurai|kerala|karnataka|maharashtra|"
            r"tamil\s*nadu",
            loc_field,
            re.I,
        ):
            return "location"
    return None


ACCOUNT_SETTINGS_URL = "https://secure.indeed.com/settings/account"


def job_dedupe_key(href: str, jk: str = "") -> str:
    """Stable key so the same listing is not Easy-Applied / ATS-opened twice.

    SERP cards often omit data-jk and use unique pagead/clk hrefs; extract jk=
    from the URL so BytesEdge-style repeats do not burn the ATS time cap.
    Also accept vjk= / %26jk%3D (encoded continueUrl) used by pagead/rc hops.
    """
    raw = href or ""
    for pat in (
        r"[?&]jk=([a-f0-9]+)",
        r"[?&]vjk=([a-f0-9]+)",
        r"[?&]job[_-]?key=([a-f0-9]+)",
        r"%26jk%3D([a-f0-9]+)",
        r"%3Fjk%3D([a-f0-9]+)",
        r"/jk/([a-f0-9]+)",
        r"jk%3D([a-f0-9]+)",
    ):
        m = re.search(pat, raw, re.I)
        if m:
            return m.group(1).lower()
    if jk and re.fullmatch(r"[a-f0-9]+", jk.strip(), re.I):
        return jk.strip().lower()
    # Unique pagead paths without an extractable jk still collide on path alone
    # less often than full href — keep query-stripped path as last resort.
    return raw.split("?")[0]


def looks_signed_in(body: str, url: str = "") -> bool:
    """True when nav/account chrome shows an authenticated jobseeker session.

    in.indeed.com marketing home still says "Get Started" / "Sign in" while
    logged in — do not use that copy. Account settings and SERP nav (Messages)
    are the reliable signals.
    """
    blob = f"{url}\n{body}"
    return bool(
        re.search(
            r"account settings|messages unread|manage your account security|"
            r"change account type|device management|privacy settings|"
            r"welcome,\s*\w+|sign out|unread count|sign out of indeed",
            blob,
            re.I,
        )
    )


def looks_login_wall(body: str, url: str = "") -> bool:
    """Indeed auth interstitial only — never company ATS cookie/email gates.

    HCLTech/SAP SuccessFactors careers pages often say "enter your email" /
    cookie consent; those must stay company_ATS (external), not indeed_login_required.
    """
    u = (url or "").lower()
    if u.startswith("http") and "indeed.com" not in u and "indeedapply" not in u:
        return False
    blob = f"{url}\n{body}"
    return bool(
        re.search(
            r"sign in \| indeed accounts|ready to take the next step|"
            r"continue with apple|enter your email address",
            blob,
            re.I,
        )
    ) and not looks_signed_in(body, url)


def looks_anonymous_marketing_home(body: str) -> bool:
    """India homepage marketing hero — shown to signed-in and anonymous users."""
    return bool(
        re.search(
            r"create an account or sign in|get started|"
            r"sign in to see your personalised|your next job starts here",
            body,
            re.I,
        )
    ) and not looks_signed_in(body)


def restore_signed_in(sb) -> dict:
    """Attach Passport cookies after CF leaves the marketing homepage.

    A homepage reload alone is not enough: Turnstile clearance on a new WARP
    IP often keeps "Get Started" until we hit Sign-in / account / myjobs.
    """
    info: dict = {"tried": [], "ok": False}

    def _snap() -> tuple[str, str, str]:
        try:
            return (
                (sb.get_text("body") or "")[:2500],
                sb.get_title() or "",
                sb.get_current_url() or "",
            )
        except Exception:
            return "", "", ""

    def _done(body: str, url: str, via: str) -> bool:
        if looks_signed_in(body, url):
            info["ok"] = True
            info["via"] = via
            return True
        return False

    for sel in (
        "a[data-gnav-element-name='SignIn']",
        "a[href*='account/login']",
        "a[href*='secure.indeed.com/auth']",
        "a[href*='login']",
    ):
        try:
            if sb.is_element_visible(sel):
                sb.click(sel)
                time.sleep(3)
                clear_cf(sb)
                dismiss_indeed_cookie_banner(sb)
                body, _title, url = _snap()
                info["tried"].append({"click": sel, "signedIn": looks_signed_in(body, url)})
                if _done(body, url, f"click:{sel}"):
                    return info
        except Exception as exc:
            info["tried"].append({"click": sel, "error": str(exc)[:120]})

    for url in (
        ACCOUNT_SETTINGS_URL,
        "https://secure.indeed.com/settings",
        "https://in.indeed.com/myjobs",
        "https://secure.indeed.com/auth?hl=en_IN&co=IN"
        "&continue=https%3A%2F%2Fin.indeed.com%2F",
        "https://www.indeed.com/account/login"
        "?continue=https%3A%2F%2Fin.indeed.com%2F",
        "https://in.indeed.com/",
    ):
        try:
            sb.uc_open_with_reconnect(url, 5)
            time.sleep(3)
            clear_cf(sb)
            dismiss_indeed_cookie_banner(sb)
            body, title, cur = _snap()
            info["tried"].append(
                {
                    "url": url,
                    "signedIn": looks_signed_in(body, cur),
                    "loginWall": looks_login_wall(body, cur),
                    "title": title[:80],
                }
            )
            if _done(body, cur, url):
                try:
                    sb.uc_open_with_reconnect("https://in.indeed.com/", 4)
                    time.sleep(2)
                    clear_cf(sb)
                except Exception:
                    pass
                return info
            if looks_login_wall(body, cur):
                info["loginWall"] = True
                info["via"] = url
                return info
        except Exception as exc:
            info["tried"].append({"url": url, "error": str(exc)[:120]})
    return info


def already_applied(body: str, url: str = "") -> bool:
    """True when job-view or SmartApply shows this listing was already submitted.

    SmartApply duplicate interstitial: "You have already applied to this job".
    Do not treat bare "application submitted" (post-submit success) as already-applied —
    that phrase is handled by _is_submitted. Match "application submitted on <date>" only.
    """
    b = (body or "").lower()
    return bool(
        re.search(
            r"you applied to this job|already applied to this|"
            r"you have already applied|application submitted on",
            b,
        )
    )


def search_queries() -> list[tuple[str, str]]:
    # Prefer homepage form submit (deep /jobs links re-trigger hard CF blocks).
    return [
        ("Solutions Architect .NET", "Hyderabad, Telangana"),
        ("Technical Architect C#", "Hyderabad, Telangana"),
        ("Engineering Manager .NET", "Hyderabad, Telangana"),
        ("Principal .NET", "Hyderabad, Telangana"),
        ("Technical Lead .NET", "Hyderabad, Telangana"),
        ("Software Architect .NET", "Hyderabad, Telangana"),
        ("Enterprise Architect", "Hyderabad, Telangana"),
        ("Staff Engineer .NET", "Hyderabad, Telangana"),
        (".NET Architect", "Remote"),
        ("Solutions Architect", "Remote"),
        ("Technical Lead C#", "Remote"),
    ]


def run_homepage_search(sb, query: str, location: str) -> bool:
    sb.uc_open_with_reconnect("https://in.indeed.com/", 5)
    time.sleep(2)
    if not clear_cf(sb):
        return False
    typed = False
    for qsel in ("#text-input-what", "input[name='q']"):
        try:
            if sb.is_element_visible(qsel):
                sb.type(qsel, query)
                typed = True
                break
        except Exception:
            continue
    for lsel in ("#text-input-where", "input[name='l']"):
        try:
            if sb.is_element_visible(lsel):
                sb.type(lsel, location)
                break
        except Exception:
            continue
    if not typed:
        # Fallback deep link (may need captcha again)
        params = urllib.parse.urlencode(
            {"q": query, "l": location, "fromage": "7", "sort": "date"}
        )
        sb.uc_open_with_reconnect("https://in.indeed.com/jobs?" + params, 5)
        time.sleep(2)
        return clear_cf(sb)
    for sel in (
        "button.yosegi-InlineWhatWhere-primaryButton",
        "button[type='submit']",
        "//button[contains(., 'Find jobs')]",
    ):
        try:
            sb.click(sel)
            break
        except Exception:
            continue
    time.sleep(3)
    return clear_cf(sb)


def smartapply_surface_ready(url: str = "", body: str = "") -> bool:
    """True only on a real SmartApply module — not the job-view listing.

    2026-09-04: waiting for bare "continue" matched cookie/JD copy on viewjob,
    so Easy Apply filled the listing (no file input) and never opened SmartApply.
    """
    u = (url or "").lower()
    b = (body or "").lower()
    if "smartapply.indeed.com" in u or "indeedapply" in u:
        return True
    if re.search(
        r"resume-selection|review-module|questions-module|contact-info",
        u,
    ):
        return True
    if re.search(
        r"contact information|add a resume|upload (your )?resume|"
        r"review your application|answer these questions from the employer",
        b,
    ):
        return True
    return False


def wait_for_smartapply_surface(sb, seconds: float = 12.0) -> bool:
    """After Apply with Indeed, wait for SmartApply URL/iframe — not viewjob."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        _switch_smartapply_frame(sb)
        try:
            cur = sb.get_current_url() or ""
            txt = sb.get_text("body") or ""
        except Exception:
            cur, txt = "", ""
        if smartapply_surface_ready(cur, txt):
            print(f"  smartapply_ready url={cur[:120]}", flush=True)
            return True
        time.sleep(0.6)
    try:
        cur = sb.get_current_url() or ""
        print(f"  smartapply_not_ready url={cur[:120]}", flush=True)
    except Exception:
        pass
    return False


def _switch_smartapply_frame(sb) -> None:
    """SmartApply occasionally mounts the form inside an iframe."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        frames = sb.driver.find_elements("css selector", "iframe")
    except Exception:
        frames = []
    ranked = []
    for fr in frames:
        try:
            src = ((fr.get_attribute("src") or "") + " " + (fr.get_attribute("id") or "")).lower()
            ranked.append((0 if re.search(r"smartapply|indeedapply|apply", src) else 1, fr))
        except Exception:
            ranked.append((2, fr))
    ranked.sort(key=lambda x: x[0])
    for _, fr in ranked:
        try:
            sb.driver.switch_to.default_content()
            sb.driver.switch_to.frame(fr)
            body = ""
            try:
                body = (sb.get_text("body") or "").lower()
            except Exception:
                body = ""
            # Skip nested preview documents (about:srcdoc) — Submit lives on parent.
            try:
                fr_url = sb.driver.execute_script("return location.href") or ""
            except Exception:
                fr_url = ""
            if str(fr_url).startswith("about:"):
                continue
            if any(
                x in body
                for x in (
                    "continue",
                    "submit",
                    "question",
                    "resume",
                    "contact",
                    "review",
                )
            ):
                return
        except Exception:
            continue
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass


def fill_common_questions(sb) -> None:
    """Best-effort form fill for smartapply.indeed.com / Easy Apply steps."""
    _switch_smartapply_frame(sb)
    # JS fill by label/aria/placeholder — more reliable on SmartApply modules.
    try:
        filled = sb.execute_script(
            """
            const vals = {
              first: 'Mohammed Abdul Rafi',
              last: 'Ahmed',
              full: 'Mohammed Abdul Rafi Ahmed',
              phone: '8790251698',
              phoneIntl: '+918790251698',
              dob: '16/01/1989',
              title: 'Mr.',
              email: 'rafi.success@gmail.com',
              city: 'Hyderabad',
              street: 'Gachibowli Hyderabad',
              postal: '500032',
              current: '52',
              expected: '65',
              notice: 'Immediate',
              noticeDays: '0',
              experience: '14'
            };
            const setNative = (el, value) => {
              if (!el) return false;
              let v = String(value);
              const type = (el.getAttribute('type') || '').toLowerCase();
              // HTML date inputs reject dd/mm/yyyy — SmartApply UST "Date" fields.
              if (type === 'date' || el.getAttribute('data-testid') === 'date-input') {
                const m = v.match(/^(\\d{1,2})[\\/\\-](\\d{1,2})[\\/\\-](\\d{4})$/);
                if (m) {
                  const dd = m[1].padStart(2, '0');
                  const mm = m[2].padStart(2, '0');
                  const yyyy = m[3];
                  v = `${yyyy}-${mm}-${dd}`;
                }
              }
              el.focus();
              const proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
              const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
              if (setter) setter.call(el, v); else el.value = v;
              el.dispatchEvent(new InputEvent('input', {bubbles:true, cancelable:true, inputType:'insertText', data:String(v)}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
              el.blur();
              return true;
            };
            const labelFor = (el) => {
              const id = el.getAttribute('id');
              let t = '';
              if (id) {
                try {
                  const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
                  if (lab) t += ' ' + lab.innerText;
                } catch (e) {}
              }
              const wrap = el.closest('label, fieldset, [class*="question"], [data-testid*="question"], .ia-Questions-item, .ia-FormField, li, section, div');
              if (wrap) t += ' ' + (wrap.innerText || '').slice(0, 220);
              t += ' ' + (el.getAttribute('aria-label') || '');
              t += ' ' + (el.getAttribute('name') || '');
              t += ' ' + (el.getAttribute('placeholder') || '');
              t += ' ' + (el.getAttribute('autocomplete') || '');
              return t.toLowerCase();
            };
            const wantFromText = (text) => {
              const t = (text || '').toLowerCase();
              if (/current.*(position|role|title|designation)|present.*(position|role|title)|job title/.test(t)
                  && !/salary|ctc|compensation|pay/.test(t)) {
                return 'Solutions Architect';
              }
              if (/current.*(employer|company|organization)|present.*(employer|company)|where.*(work|employed)/.test(t)
                  && !/salary|ctc|compensation|pay/.test(t)) {
                return 'Nemetschek / Solibri';
              }
              if (/linkedin(\\.com)?|profile url|portfolio url/.test(t)) {
                return 'https://www.linkedin.com/in/rafi-ahmed';
              }
              if (/highest (degree|education|qualification)|degree of education|education level|degree obtained|university|college/.test(t)) {
                return 'B.Tech';
              }
              if (/full\\s*name|your\\s*name|candidate\\s*name|applicant\\s*name/.test(t)
                  && !/first|last|middle|company/.test(t)) {
                return 'Mohammed Abdul Rafi Ahmed';
              }
              if (/(date of birth|\\bdob\\b|birth date|birthday)/.test(t) && !/place of birth/.test(t)) {
                return '16/01/1989';
              }
              // UST SmartApply labels bare "Date" / "Date *" for Available Date — not DOB.
              if (/^date(\\s*\\*)?$/i.test(t.trim())
                  || (/\\bdate\\b/.test(t) && !/birth|\\bdob\\b|today|update|issue/.test(t)
                      && (/available|start|join|^date\\b/.test(t.trim()) || t.trim().length <= 12))) {
                return '15/08/2026';
              }
              if (/(^|\\s)(title|salutation|honorific)\\b/.test(t) && !/job title|current position|position\\?/.test(t)) {
                return 'Mr.';
              }
              // "Are you based in …" / location confirmation radios.
              if (/are you based|based in (india|hyderabad|telangana)|currently based/.test(t)
                  && !/relocat|willing to move|prefer/.test(t)) {
                return 'yes';
              }
              // Never invent government IDs.
              if (/\\bpan\\b|aadhaar|aadhar|passport number|national id/.test(t)) {
                return null;
              }
              if (/current.*(ctc|salary|compensation|pay)|ctc.*current|present.*ctc|current.*package|current salary/.test(t)) return '52';
              if (/expected.*(ctc|salary|compensation|pay)|ctc.*expected|desired.*(salary|compensation|ctc|pay)|expected.*package/.test(t)) return '65';
              if (/earliest start|start date|available from|joining date|when can you (start|join)/.test(t)
                  && !/salary|ctc/.test(t)) {
                return '15/08/2026';
              }
              if (/notice|joining|how soon|availability|immediate|serve notice/.test(t)
                  && !/start date|available from/.test(t)) {
                // "Notice Period (in days)" / numeric fields reject the word Immediate.
                if (/\\bin\\s*days\\b|number of days|notice period.*day|day\\(s\\)|valid number|decimals allowed/.test(t)) {
                  return '0';
                }
                return 'Immediate';
              }
              if (/certify that|i certify|details mentioned in your resume|accurate and truthful/.test(t)) {
                return 'yes';
              }
              if (/total.*(experience|exp)|years of experience|overall experience|relevant experience/.test(t)) return '14';
              // Years with a specific stack (Blazor / FHIR / .NET / Angular / Azure / C#).
              if (/how many years|years? (of |with |in )?(exp|experience)?|experience (with|in|on)/.test(t)
                  && /(\\.net|c#|asp\\.\\s*net|blazor|fhir|angular|azure|react|microservices|architect|lead|manag)/.test(t)) {
                return '10';
              }
              if (/proficien|rate your|skill level|expertise/.test(t)
                  && /(\\.net|c#|blazor|fhir|angular|azure|react)/.test(t)) {
                return 'Expert';
              }
              // Voluntary self-ID / EEO — prefer decline (required fields on Mattel etc.).
              if (/voluntary self|self.?identif|gender identity|race|ethnicity|hispanic|latino|veteran|disability|disabled|lgbt|sexual orientation|pronoun/.test(t)
                  && !/authorized|work authori|visa|citizen/.test(t)) {
                return 'decline';
              }
              if (/privacy notice|declare that you have read and agree|agree to the (privacy|terms)|consent to (the )?privacy/.test(t)
                  && !/gender identity|ethnicity|hispanic|veteran|disability/.test(t)) {
                return 'yes';
              }
              if (/relocat|willing to work|hybrid|work from office|bond|service agreement|background check|drug test/.test(t)) return 'yes';
              if (/authorized|work authori|visa|citizen|india|legally/.test(t)) return 'yes';
              if (/gender/.test(t)) return 'male';
              if (/city|current location|prefer.*location|job location|base location/.test(t)) return 'Hyderabad';
              if (/\\?/.test(t) && /(yes|no)/.test(t)) return 'yes';
              if (/what makes you unique|cover letter|why (do )?you|tell us|about yourself|summary|additional information/.test(t)) {
                return 'Solutions Architect / Tech Lead with 14+ years in .NET, Azure, microservices. Immediate joiner. Hyd/Remote. Expected 65 LPA.';
              }
              return null;
            };
            const clickMatching = (root, want) => {
              const radios = [...root.querySelectorAll('input[type=radio], input[type=checkbox], [role=radio], [role=checkbox]')];
              for (const r of radios) {
                const lab = ((r.getAttribute('aria-label')||'') + ' ' + (r.parentElement?.innerText||'') + ' ' + (r.value||'')).toLowerCase().slice(0,160);
                const hit =
                  (want === 'yes' && /\\byes\\b|yep|true|agree|available/.test(lab) && !/\\bno\\b/.test(lab)) ||
                  (want === 'male' && /\\bmale\\b/.test(lab) && !/female/.test(lab)) ||
                  (want === 'Mr.' && (/^mr\\.?$/.test(lab.trim()) || (/\\bmr\\.?\\b/.test(lab) && !/mrs|miss|\\bms\\.?\\b/.test(lab)))) ||
                  (want === 'Immediate' && /immediate|0\\s*day|1-30|0-15|less than|currently serving|serving notice/.test(lab)) ||
                  (want === '0' && /\\b0\\b|immediate|0\\s*day|0-15|less than|currently serving|serving notice/.test(lab)) ||
                  (want === 'decline' && /decline|prefer not|do not wish|don't wish|choose not|not to answer|rather not|do not want/.test(lab));
                if (hit) {
                  try { r.click(); } catch (e) {}
                  try { (r.closest('label') || r).click(); } catch (e) {}
                  return true;
                }
              }
              for (const sel of root.querySelectorAll('select')) {
                for (const opt of sel.options) {
                  const t = (opt.text||'').toLowerCase();
                  if (
                    (want === 'yes' && /\\byes\\b/.test(t)) ||
                    (want === 'Mr.' && /\\bmr\\.?\\b/.test(t) && !/mrs/.test(t)) ||
                    (want === 'Immediate' && /immediate|0\\s*day|1-30|0-15|less than/.test(t)) ||
                    (want === '0' && /\\b0\\b|immediate|0\\s*day|0-15|less than/.test(t)) ||
                    (want === 'Hyderabad' && /hyderabad/.test(t)) ||
                    (want === '52' && /\\b52\\b|50-55|45-55/.test(t)) ||
                    (want === '65' && /\\b65\\b|60-70|60-65/.test(t)) ||
                    (want === '14' && /\\b14\\b|12-15|10\\+/.test(t)) ||
                    (want === '10' && /\\b10\\b|8-10|10\\+|8\\+|7\\+|5\\+/.test(t)) ||
                    (want === 'Expert' && /expert|advanced|proficient|high/.test(t)) ||
                    (want === 'B.Tech' && /b\\.?tech|bachelor|b\\.e\\b|undergraduate|master|m\\.?tech/.test(t)) ||
                    (want === 'decline' && /decline|prefer not|do not wish|don't wish|choose not|not to answer|rather not/.test(t))
                  ) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change',{bubbles:true}));
                    return true;
                  }
                }
              }
              for (const el of root.querySelectorAll('input:not([type=radio]):not([type=checkbox]):not([type=file]):not([type=hidden]), textarea')) {
                if (el.disabled || el.readOnly) continue;
                if (want === 'decline') continue;
                if (want === 'Immediate') {
                  const type = (el.getAttribute('type') || '').toLowerCase();
                  const mode = (el.getAttribute('inputmode') || '').toLowerCase();
                  const lab = labelFor(el);
                  if (type === 'number' || /numeric|decimal/.test(mode)
                      || /\\bin\\s*days\\b|number of days|notice period.*day|day\\(s\\)/.test(lab)) {
                    setNative(el, '0');
                    return true;
                  }
                }
                if (want) { setNative(el, want); return true; }
              }
              // Custom listbox / button options (Indeed education / years are often comboboxes).
              if (want === 'B.Tech' || want === '14' || want === '10') {
                for (const btn of root.querySelectorAll('button, [role=combobox], [aria-haspopup=listbox]')) {
                  const t = ((btn.innerText||'') + ' ' + (btn.getAttribute('aria-label')||'')).toLowerCase();
                  if (/select an option|choose an option|^select$/.test(t) || btn.getAttribute('aria-expanded') === 'false') {
                    try { btn.click(); } catch (e) {}
                  }
                }
              }
              for (const el of root.querySelectorAll('button, [role=option], li, label, span')) {
                const t = ((el.innerText||'') + ' ' + (el.getAttribute('aria-label')||'')).trim().toLowerCase();
                if (!t || t.length > 80) continue;
                if (want === 'yes' && /\\byes\\b|i certify|yes, i certify/.test(t) && !/don'?t certify|\\bno,/.test(t)) { el.click(); return true; }
                // Prefer exact "Mr." / "Mr" nodes — avoid clicking a parent that contains both Mr. and Ms.
                if (want === 'Mr.' && /^mr\\.?$/.test(t.trim())) { el.click(); return true; }
                if (want === 'Mr.' && /\\bmr\\.?\\b/.test(t) && !/mrs|miss|\\bms\\.?\\b/.test(t) && t.length <= 12) { el.click(); return true; }
                if (want === 'Immediate' && /immediate|0\\s*day|1-30|0-15/.test(t)) { el.click(); return true; }
                if (want === '0' && /\\b0\\b|immediate|0\\s*day|0-15/.test(t) && !/select an option|notice period/.test(t)) { el.click(); return true; }
                if (want === 'B.Tech' && /b\\.?\\s*tech|bachelor|b\\.e\\.?(\\b|,)|undergraduate|master'?s?|m\\.?\\s*tech|graduate degree|post\\s*graduate/.test(t)
                    && !/select an option|highest degree|what is your/.test(t)) {
                  el.click(); return true;
                }
                if ((want === '14' || want === '10') && /\\b(14|12|10|8)\\+?\\b|12-15|10\\+|8-10/.test(t)
                    && !/select an option|how many years/.test(t)) {
                  el.click(); return true;
                }
                if (want === 'decline' && /decline|prefer not|do not wish|don't wish|choose not|not to answer|rather not/.test(t)) {
                  el.click(); return true;
                }
              }
              return false;
            };
            let answered = 0;
            const roots = [
              ...document.querySelectorAll('[class*="question"], fieldset, [data-testid*="question"], .ia-Questions-item, .ia-Questions, form, main, [role=main]')
            ];
            for (const root of roots) {
              const text = root.innerText || '';
              // Page/form roots mix EEO + privacy; question-sized nodes only.
              if (text.length > 800) continue;
              const want = wantFromText(text);
              if (want && clickMatching(root, want)) answered += 1;
            }
            for (const lab of document.querySelectorAll('label, legend, h1, h2, h3, p, span, div')) {
              const t = (lab.innerText||'').trim();
              // Allow short "Title *" / "Mr." labels (was >6 and missed Title alone).
              // Include education/degree — ValGenesis "highest degree of education" was skipped.
              if (t.length > 2 && t.length < 220 && /\\?|ctc|salary|notice|experience|relocat|authori|location|package|lpa|gender|hybrid|bond|veteran|disability|ethnicity|race|hispanic|voluntary|self.?ident|birth|dob|title|salutation|phone|\\bdate\\b|available date|education|degree|qualification|university|college|based in|^mr\\.?$|^ms\\.?$/.test(t.toLowerCase())) {
                const want = wantFromText(t);
                if (want && clickMatching(lab.closest('div, fieldset, li, section, [class*="question"]') || lab.parentElement || lab, want)) {
                  answered += 1;
                }
              }
            }
            // Profile / contact fields
            for (const el of document.querySelectorAll('input, textarea')) {
              const type = (el.getAttribute('type') || '').toLowerCase();
              if (['hidden','submit','button','file','checkbox','radio'].includes(type)) continue;
              if (el.disabled || el.readOnly) continue;
              const lab = labelFor(el);
              let val = null;
              if (/full\\s*name|your\\s*name|candidate\\s*name|applicant\\s*name/.test(lab)
                  && !/first|last|middle|company/.test(lab)) val = vals.full;
              else if (/first\\s*name|given\\s*name|fname/.test(lab)) val = vals.first;
              else if (/last\\s*name|surname|family\\s*name|lname/.test(lab)) val = vals.last;
              else if (/(date of birth|\\bdob\\b|birth date|birthday)/.test(lab)) val = vals.dob;
              else if (/\\bpan\\b|aadhaar|aadhar|passport number|national id/.test(lab)) val = null;
              else if (/\\bphone\\b|\\bmobile\\b|telephone|phone\\s*no/.test(lab) || type === 'tel') val = vals.phone;
              else if (/e-?mail/.test(lab) || type === 'email') val = vals.email;
              else if (/postal|zip\\s*code|pin\\s*code|pincode/.test(lab) && !/email/.test(lab)) val = vals.postal;
              else if (/(street\\s*address|address\\s*line|home\\s*address|^address\\b)/.test(lab)
                  && !/email|ip address|web address/.test(lab)) val = vals.street;
              else if (/current.*(position|role|title|designation)|job title/.test(lab) && !/salary|ctc/.test(lab)) val = 'Solutions Architect';
              else if (/current.*(employer|company|organization)|present.*(employer|company)/.test(lab) && !/salary|ctc/.test(lab)) val = 'Nemetschek / Solibri';
              else if (/linkedin|profile url|portfolio url/.test(lab)) val = 'https://www.linkedin.com/in/rafi-ahmed';
              else if (/highest (degree|education|qualification)|education|university|college|degree/.test(lab)) val = 'B.Tech';
              else if (/current.*(ctc|salary|compensation|package)|ctc.*current|current salary/.test(lab)) val = vals.current;
              else if (/expected.*(ctc|salary|compensation|package)|ctc.*expected/.test(lab)) val = vals.expected;
              else if (/earliest start|start date|available from|joining date|available date|date available/.test(lab)
                  || /^date(\\s*\\*)?$/i.test(lab.trim())
                  || (type === 'date' && /start|join|avail|\\bdate\\b/.test(lab))) val = '15/08/2026';
              else if (type === 'date' && !/birth|\\bdob\\b/.test(lab)) val = '15/08/2026';
              else if (/\\bdate\\b/.test(lab) && !/birth|\\bdob\\b|today|update/.test(lab) && lab.trim().length <= 12) val = '15/08/2026';
              else if (/notice|joining|availability/.test(lab) && !/start date|available from|available date/.test(lab)) {
                const mode = (el.getAttribute('inputmode') || '').toLowerCase();
                const numericNotice = type === 'number' || /numeric|decimal/.test(mode)
                  || /\\bin\\s*days\\b|number of days|notice period.*day|day\\(s\\)/.test(lab)
                  || /^immediate$/i.test((el.value || '').trim());
                val = numericNotice ? vals.noticeDays : vals.notice;
              }
              else if (/city|location|current\\s*location/.test(lab) && !/relocat|street|postal|address/.test(lab)) val = vals.city;
              else if (/experience|years/.test(lab)) val = vals.experience;
              else if (!(el.value || '').trim()) {
                const w = wantFromText(lab);
                if (w) val = w;
              }
              if (val != null && (!(el.value || '').trim() || /\\bphone\\b|\\bmobile\\b|telephone|phone\\s*no|first|last|full\\s*name|ctc|salary|notice|city|experience|package|linkedin|employer|company|education|degree|birth|dob|start date|available date|address|postal|zip|pin\\s*code/.test(lab) || /^(yes|no)$/i.test(el.value || ''))) {
                if (setNative(el, val)) answered += 1;
                // UST Phone No sometimes rejects bare local numbers — retry +91.
                if (/\\bphone\\b|\\bmobile\\b|telephone|phone\\s*no/.test(lab) || type === 'tel') {
                  const after = (el.value || '').trim();
                  if (!after || after.length < 10) {
                    if (setNative(el, vals.phoneIntl)) answered += 1;
                  }
                }
              }
            }
            // Unchecked radio groups → prefer Yes / Immediate / first option.
            const names = new Set(
              [...document.querySelectorAll('input[type=radio]')].map(r => r.name).filter(Boolean)
            );
            for (const name of names) {
              const group = [...document.querySelectorAll(`input[type=radio][name="${CSS.escape(name)}"]`)];
              if (!group.length || group.some(r => r.checked)) continue;
              const scored = group.map(r => {
                const lab = ((r.getAttribute('aria-label')||'') + ' ' + (r.parentElement?.innerText||'') + ' ' + (r.value||'')).toLowerCase();
                let s = 0;
                if (/decline|prefer not|do not wish|don't wish|choose not|not to answer|rather not/.test(lab)) s += 4;
                if (/\\byes\\b|immediate|agree|available|hyderabad|male\\b|\\bmr\\.?\\b/.test(lab)) s += 3;
                if (/\\bno\\b|female|not available|never/.test(lab)) s -= 2;
                return {r, s, lab};
              }).sort((a,b) => b.s - a.s);
              try { scored[0].r.click(); answered += 1; } catch (e) {}
              try { (scored[0].r.closest('label') || scored[0].r).click(); } catch (e) {}
            }
            // Required empty selects → first non-placeholder option.
            for (const sel of document.querySelectorAll('select')) {
              if (sel.disabled || (sel.value && sel.selectedIndex > 0)) continue;
              const lab = labelFor(sel);
              if (/country|dial|phone|phone.?code|calling.?code/.test(lab)) {
                for (const opt of sel.options) {
                  if (/india|\\+91|^in$/i.test(opt.text + ' ' + opt.value)) {
                    sel.value = opt.value;
                    sel.dispatchEvent(new Event('change', {bubbles:true}));
                    answered += 1;
                    break;
                  }
                }
                continue;
              }
              for (const opt of [...sel.options].slice(1)) {
                if ((opt.text || '').trim()) {
                  sel.value = opt.value;
                  sel.dispatchEvent(new Event('change', {bubbles:true}));
                  answered += 1;
                  break;
                }
              }
            }
            // SmartApply Country / dial-code comboboxes (often not native <select>).
            const pickIndiaOption = () => {
              const opts = [...document.querySelectorAll('[role=option], li, button, div, span, a')];
              for (const el of opts) {
                const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).trim();
                if (!t || t.length > 80) continue;
                if (/india|\\+\\s*91|\\+91/.test(t) && !/indiana|indianapol/i.test(t)) {
                  try { el.click(); return true; } catch (e) {}
                }
              }
              return false;
            };
            const countryTriggers = [...document.querySelectorAll(
              'button, [role=combobox], [aria-haspopup=listbox], select, [class*="dropdown"], [data-testid*="country"]'
            )];
            for (const el of countryTriggers) {
              const wrap = el.closest('fieldset, [class*="question"], [class*="Question"], li, section, label, div') || el.parentElement || el;
              const ctx = ((wrap.innerText || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '')).toLowerCase().slice(0, 280);
              const looksCountry = /\\bcountry\\b|dial.?code|calling.?code|phone.?code|country code/.test(ctx);
              const needsPick = /select an option|^select$|choose an option|select country/.test((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || ''))
                || (el.tagName === 'SELECT' && (el.selectedIndex <= 0));
              if (!looksCountry || !needsPick) continue;
              try { el.click(); } catch (e) {}
              if (pickIndiaOption()) { answered += 1; }
            }
            // If validation already shows "Choose an option" under Country, open + India.
            for (const err of document.querySelectorAll('[class*="error"], [role=alert], span, p, div')) {
              const et = (err.innerText || '').trim();
              if (!/choose an option to continue/i.test(et)) continue;
              const root = err.closest('fieldset, [class*="question"], [class*="Question"], li, section, form, div') || document.body;
              const ctx = (root.innerText || '').toLowerCase().slice(0, 400);
              if (!/\\bcountry\\b|dial|phone/.test(ctx)) continue;
              const trigger = root.querySelector('button, [role=combobox], [aria-haspopup=listbox], select');
              if (trigger) { try { trigger.click(); } catch (e) {} }
              if (pickIndiaOption()) { answered += 1; break; }
            }
            // Required acknowledgment / privacy checkboxes (Mattel / Nagarro etc.).
            // Click the input ONCE — also clicking the wrapping label unchecks it.
            for (const c of document.querySelectorAll('input[type=checkbox], [role=checkbox]')) {
              if (c.disabled) continue;
              if (c.checked || c.getAttribute('aria-checked') === 'true') continue;
              const lab = labelFor(c) + ' ' + (c.innerText || '') + ' ' + (c.value || '');
              if (/confirm|agree|privacy|notice|terms|read.*understand|i have read|by checking|consent/.test(lab)) {
                try { c.click(); answered += 1; } catch (e) {}
              }
            }
            // Remaining empty required-looking text inputs.
            for (const el of document.querySelectorAll('input:not([type=hidden]):not([type=file]):not([type=radio]):not([type=checkbox]), textarea')) {
              if (el.disabled || el.readOnly || (el.value || '').trim()) continue;
              const lab = labelFor(el);
              const itype = (el.getAttribute('type') || '').toLowerCase();
              const req = el.required || el.getAttribute('aria-required') === 'true' || /required|\\*/.test(lab);
              if (!req && !/question|ctc|salary|notice|experience|phone|date|address|postal|zip|pin/.test(lab) && itype !== 'date' && itype !== 'tel') continue;
              if (/\\bpan\\b|aadhaar|aadhar|passport number|national id/.test(lab)) continue;
              // Do NOT map bare "Date" → DOB (UST Available Date was poisoned by that).
              let w = wantFromText(lab);
              if (!w) {
                if (/how many|years|experience/.test(lab)) w = '14';
                else if (/salary|ctc|lpa|package/.test(lab)) w = '65';
                else if (/birth|\\bdob\\b|birth date|birthday/.test(lab)) w = vals.dob;
                else if (/start|join|avail|available date|date available/.test(lab)
                    || /^date(\\s*\\*)?$/i.test(lab.trim())
                    || (itype === 'date' && !/birth|\\bdob\\b/.test(lab))
                    || (/\\bdate\\b/.test(lab) && !/birth|\\bdob\\b|today|update/.test(lab) && lab.trim().length <= 12)) {
                  w = '15/08/2026';
                }
                else if (/\\bphone\\b|\\bmobile\\b|phone\\s*no|telephone/.test(lab) || itype === 'tel') w = vals.phone;
                else if (/postal|zip\\s*code|pin\\s*code|pincode/.test(lab)) w = vals.postal;
                else if (/(street\\s*address|address\\s*line|^address\\b)/.test(lab) && !/email|ip address/.test(lab)) w = vals.street;
                else if (/city|state\\/territory|state or territory/.test(lab) && !/relocat/.test(lab)) w = vals.city;
              }
              if (w && setNative(el, w)) answered += 1;
              if ((/\\bphone\\b|phone\\s*no|telephone|\\bmobile\\b/.test(lab) || itype === 'tel')
                  && (!(el.value || '').trim() || (el.value || '').trim().length < 10)) {
                if (setNative(el, vals.phoneIntl)) answered += 1;
              }
            }
            return {answered, url: location.href};
            """
        )
        if isinstance(filled, dict):
            print(f"  fill={filled}", flush=True)
    except Exception as e:
        print(f"  fill_error={e!s}"[:200], flush=True)

    # Comboboxes (education / Title / Country) often render options only after open.
    recover_required_selects(sb)

    # Resume upload — JD-tailored copy when prepare_resume_for_job ran.
    # Retries on "We could not upload your resume file" (2026-08-26 cloud flake).
    upload_smartapply_resume(sb)
    tick_required_agreements(sb)
    recover_required_selects(sb)


def _smartapply_resume_status(sb) -> dict:
    """Detect resume card selection / upload success / Indeed upload error."""
    _switch_smartapply_frame(sb)
    try:
        return sb.execute_script(
            r"""
            const body = (document.body && document.body.innerText) || '';
            const err = /we could not upload your resume|could not upload your resume|upload failed|file (is )?too large|file type (is )?not supported/i.test(body);
            const hasFileInput = !!document.querySelector('input[type=file]');
            const selected = [...document.querySelectorAll('[aria-selected=true], [class*="selected"], [data-testid*="resume"], button, label, li, div')]
              .some(el => {
                const t = (el.innerText || '').trim();
                if (!t || t.length > 180) return false;
                return /rafi_resume|rafi resume|\.docx|\.pdf/i.test(t)
                  && (el.getAttribute('aria-selected') === 'true'
                      || /selected|in use|current resume/i.test(t)
                      || (el.closest && el.closest('[aria-selected=true], [class*="selected"]')));
              });
            const uploadedName = [...document.querySelectorAll('button, label, span, div, p, li')]
              .map(el => (el.innerText || '').trim())
              .find(t => t && t.length < 120 && /rafi_resume|rafi resume|\.docx|\.pdf/i.test(t)
                && !/upload a resume|add a resume|select file|accepted file/i.test(t));
            const addResumeOnly = /add a resume|upload a resume/i.test(body)
              && /select file/i.test(body)
              && !uploadedName;
            return {
              error: err,
              hasFileInput,
              selected: !!selected,
              uploadedName: uploadedName || null,
              addResumeOnly: !!addResumeOnly,
              ok: (!err && (!!selected || !!uploadedName)),
            };
            """
        ) or {}
    except Exception as exc:
        return {"error": False, "ok": False, "exc": str(exc)[:120]}


def _click_existing_smartapply_resume(sb) -> bool:
    """Prefer an already-hosted Rafi / .docx card over a fresh upload."""
    _switch_smartapply_frame(sb)
    try:
        clicked = sb.execute_script(
            r"""
            const cards=[...document.querySelectorAll('button, [role=button], label, div, li, [data-testid*="resume"]')];
            const scored = cards.map(el => {
              const t=(el.innerText||'').trim();
              if (!t || t.length > 220) return null;
              if (/upload a resume|add a resume|select file|accepted file/i.test(t)) return null;
              let s = 0;
              if (/rafi_resume|rafi resume/i.test(t)) s += 10;
              if (/\.docx|\.pdf/i.test(t)) s += 4;
              if (/mohammed|abdul rafi|rafi ahmed/i.test(t)) s += 6;
              if (s < 4) return null;
              const r = el.getBoundingClientRect();
              if (r.width < 2 || r.height < 2) return null;
              return {el, t, s};
            }).filter(Boolean).sort((a,b) => b.s - a.s);
            if (!scored.length) return null;
            try { scored[0].el.scrollIntoView({block:'center'}); } catch (e) {}
            try { scored[0].el.click(); } catch (e) { return null; }
            return scored[0].t.slice(0, 80);
            """
        )
        if clicked:
            print(f"  resume_card_click={clicked!r}", flush=True)
            time.sleep(0.8)
            return True
    except Exception as exc:
        print(f"  resume_card_err={exc!s}"[:160], flush=True)
    return False


def _send_resume_to_file_inputs(sb, resume_path: Path) -> int:
    """Push a local DOCX/PDF onto every visible SmartApply file input."""
    _switch_smartapply_frame(sb)
    sent = 0
    path = str(resume_path.resolve())
    try:
        inputs = sb.find_elements("input[type='file']")
    except Exception:
        inputs = []
    for f in inputs:
        try:
            # Re-enable hidden inputs Indeed uses behind "Select file".
            try:
                sb.execute_script(
                    "arguments[0].style.display='block';"
                    "arguments[0].style.opacity=1;"
                    "arguments[0].removeAttribute('hidden');"
                    "arguments[0].disabled=false;",
                    f,
                )
            except Exception:
                pass
            f.send_keys(path)
            sent += 1
        except Exception as exc:
            print(f"  resume_send_keys_err={exc!s}"[:160], flush=True)
    return sent


def upload_smartapply_resume(sb, max_attempts: int = 3) -> dict:
    """Upload / select Rafi_Resume on SmartApply resume-selection with retries.

    Cloud runs often hit "We could not upload your resume file" after a single
    send_keys + 1s sleep, then burn CTA retries on Continue without re-uploading.
    Prefer an existing profile card; otherwise upload the tailored DOCX, wait for
    success, and on upload error retry with backoff — last try uses the untailored
    master at resumes/Rafi_Resume.docx.
    """
    try:
        from tools.resume_paths import resume_upload_path

        primary = Path(resume_upload_path())
    except Exception:
        primary = Path(os.environ.get("RESUME_UPLOAD_PATH") or RESUME)
    if not primary.exists():
        primary = RESUME
    master = ROOT / "resumes" / "Rafi_Resume.docx"
    if not master.exists():
        master = RESUME

    # Already good (selected card / uploaded name, no error).
    status = _smartapply_resume_status(sb)
    if status.get("ok"):
        print(f"  resume_already_ok={status}", flush=True)
        return {"ok": True, "via": "already", **status}

    if _click_existing_smartapply_resume(sb):
        status = _smartapply_resume_status(sb)
        if status.get("ok") or (status.get("selected") and not status.get("error")):
            print(f"  resume_selected={status}", flush=True)
            return {"ok": True, "via": "card", **status}

    last = dict(status or {})
    for attempt in range(1, max_attempts + 1):
        # Final attempt: fall back to untailored master (tailored DOCX can flake).
        path = primary if attempt < max_attempts or primary.resolve() == master.resolve() else master
        if not path.exists():
            path = primary if primary.exists() else master
        print(
            f"  resume_upload_attempt={attempt}/{max_attempts} path={path} bytes={path.stat().st_size if path.exists() else 0}",
            flush=True,
        )
        # Dismiss stale error state if Indeed left the dropzone red.
        try:
            _switch_smartapply_frame(sb)
            sb.execute_script(
                r"""
                const btn=[...document.querySelectorAll('button, a, [role=button]')]
                  .find(el => /try again|replace|remove|change resume|upload (a )?different/i.test((el.innerText||'').trim()));
                if (btn) btn.click();
                """
            )
        except Exception:
            pass
        sent = _send_resume_to_file_inputs(sb, path)
        if not sent:
            # Click "Select file" to surface the input, then retry once.
            try:
                _switch_smartapply_frame(sb)
                sb.execute_script(
                    r"""
                    const el=[...document.querySelectorAll('button, label, [role=button], span, div')]
                      .find(e => /^select file$/i.test((e.innerText||'').trim()) || /select file/i.test(e.getAttribute('aria-label')||''));
                    if (el) el.click();
                    """
                )
                time.sleep(0.4)
                sent = _send_resume_to_file_inputs(sb, path)
            except Exception:
                pass
        if not sent:
            print("  resume_upload_no_file_input", flush=True)
            last = _smartapply_resume_status(sb)
            time.sleep(1.2 * attempt)
            continue

        # Wait for Indeed to accept the file (or show the red upload error).
        deadline = time.time() + 18
        while time.time() < deadline:
            time.sleep(1.0)
            last = _smartapply_resume_status(sb)
            if last.get("error"):
                print(f"  resume_upload_error status={last}", flush=True)
                break
            if last.get("ok") or last.get("uploadedName") or last.get("selected"):
                print(f"  resume_upload_ok status={last}", flush=True)
                return {"ok": True, "via": "upload", "attempt": attempt, "path": str(path), **last}
            # Upload in flight: dropzone no longer "Add a resume" only.
            if not last.get("addResumeOnly") and last.get("hasFileInput"):
                # Keep waiting; name node can lag.
                continue
        if last.get("ok") or (last.get("uploadedName") and not last.get("error")):
            return {"ok": True, "via": "upload", "attempt": attempt, "path": str(path), **last}
        time.sleep(1.5 * attempt)

    print(f"  resume_upload_failed last={last}", flush=True)
    return {"ok": False, "via": "failed", **(last or {})}


def recover_required_selects(sb) -> dict:
    """Open unresolved SmartApply comboboxes and pick education / Title / Country.

    ValGenesis leaves "Select an option" on highest-degree with
    "Choose an option to continue". LTIMindtree Title Mr/Ms radios need an
    exact Mr. click. Country dial was already handled; this covers the rest
    with an open → brief wait → pick pass (listbox options hydrate async).
    """
    _switch_smartapply_frame(sb)
    opened = []
    try:
        opened = sb.execute_script(
            r"""
            const opened = [];
            const triggers = [...document.querySelectorAll(
              'button, [role=combobox], [aria-haspopup=listbox], select'
            )];
            for (const el of triggers) {
              const wrap = el.closest('fieldset, [class*="question"], [class*="Question"], li, section, label, div') || el.parentElement || el;
              const ctx = ((wrap.innerText || '') + ' ' + (el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '')).toLowerCase().slice(0, 420);
              const shown = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).trim().toLowerCase();
              const needs =
                /select an option|^select$|choose an option/.test(shown)
                || (el.tagName === 'SELECT' && (el.selectedIndex <= 0))
                || (el.getAttribute('aria-expanded') === 'false' && /highest (degree|education)|degree of education|education level|\btitle\b|salutation|\bcountry\b|dial.?code/.test(ctx));
              if (!needs) continue;
              try { el.scrollIntoView({block:'center'}); } catch (e) {}
              try { el.click(); opened.push(ctx.slice(0, 80)); } catch (e) {}
            }
            for (const err of document.querySelectorAll('[class*="error"], [role=alert], span, p, div')) {
              const et = (err.innerText || '').trim();
              if (!/choose an option to continue/i.test(et)) continue;
              const root = err.closest('fieldset, [class*="question"], [class*="Question"], li, section, form, div') || document.body;
              const trigger = root.querySelector('button, [role=combobox], [aria-haspopup=listbox], select');
              if (trigger) {
                try { trigger.click(); opened.push('validation:' + (root.innerText || '').slice(0, 60)); } catch (e) {}
              }
            }
            return opened;
            """
        ) or []
    except Exception as e:
        print(f"  recover_selects_open_err={e!s}"[:200], flush=True)
        opened = []
    if opened:
        time.sleep(0.55)
    picked = {}
    try:
        picked = sb.execute_script(
            r"""
            const clicked = [];
            const pick = (re, why) => {
              const opts = [...document.querySelectorAll('[role=option], li, button, label, span, div, a')];
              const scored = opts.map(el => {
                const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).trim();
                if (!t || t.length > 80) return null;
                if (!re.test(t)) return null;
                const r = el.getBoundingClientRect();
                if (r.width < 2 || r.height < 2) return null;
                let s = 0;
                if (/^mr\.?$/i.test(t)) s += 10;
                if (/bachelor|b\.?\s*tech|b\.e\b/i.test(t)) s += 8;
                if (/india|\+91/i.test(t)) s += 8;
                if (t.length < 24) s += 2;
                return {el, t, s};
              }).filter(Boolean).sort((a,b) => b.s - a.s);
              if (!scored.length) return false;
              try { scored[0].el.click(); clicked.push(why + ':' + scored[0].t.slice(0, 40)); return true; } catch (e) { return false; }
            };
            pick(/^mr\.?$/i, 'title-mr')
              || pick(/\bmr\.?\b/i, 'title-mr-loose');
            pick(/b\.?\s*tech|bachelor|b\.e\.?(\b|,)|undergraduate|graduate degree|master'?s?|m\.?\s*tech|post\s*graduate/i, 'education');
            pick(/^(india|\+?\s*91)\b/i, 'country')
              || pick(/india|\+\s*91|\+91/i, 'country-loose');
            // ValGenesis employment/education locale: "India - Standard" / "India - Engineer".
            pick(/india\s*[-–]\s*(standard|engineer|full\s*time)/i, 'india-standard')
              || pick(/^india\b/i, 'india-opt');
            pick(/\b(14|12|10|8)\+?\b|10\+|12-15|8-10/i, 'years');
            for (const sel of document.querySelectorAll('select')) {
              if (sel.disabled || (sel.value && sel.selectedIndex > 0)) continue;
              const lab = ((sel.getAttribute('aria-label')||'') + ' ' + (sel.closest('fieldset, [class*="question"], label, div')?.innerText||'')).toLowerCase().slice(0, 300);
              let re = null;
              let why = 'select';
              if (/highest (degree|education)|degree of education|education level|university|college|qualification/.test(lab)) {
                re = /b\.?\s*tech|bachelor|b\.e\b|undergraduate|master|m\.?\s*tech/i; why = 'select-education';
              } else if (/(^|\s)(title|salutation|honorific)\b/.test(lab) && !/job title/.test(lab)) {
                re = /^mr\.?$/i; why = 'select-title';
              } else if (/\bcountry\b|dial.?code|phone.?code/.test(lab)) {
                re = /india|\+91|^in$/i; why = 'select-country';
              } else if (/india\s*[-–]|standard|engineer|employment|work\s*location|job\s*family/.test(lab)) {
                re = /india\s*[-–]\s*(standard|engineer)|india/i; why = 'select-india-standard';
              }
              if (!re) continue;
              for (const opt of sel.options) {
                if (re.test(opt.text || '')) {
                  sel.value = opt.value;
                  sel.dispatchEvent(new Event('change', {bubbles:true}));
                  clicked.push(why + ':' + (opt.text||'').slice(0,40));
                  break;
                }
              }
            }
            const forceClick = (el) => {
              if (!el) return false;
              try { el.scrollIntoView({block:'center'}); } catch (e) {}
              try {
                el.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true}));
                el.dispatchEvent(new MouseEvent('mousedown', {bubbles:true}));
                el.dispatchEvent(new PointerEvent('pointerup', {bubbles:true}));
                el.dispatchEvent(new MouseEvent('mouseup', {bubbles:true}));
                el.dispatchEvent(new MouseEvent('click', {bubbles:true}));
              } catch (e) {
                try { el.click(); } catch (e2) {}
              }
              return true;
            };
            const titleRoots = [...document.querySelectorAll('fieldset, [class*="question"], [class*="Question"], li, section, div')]
              .filter(r => {
                const t = (r.innerText || '').slice(0, 160).toLowerCase();
                return t.length < 220 && /\btitle\b|\bsalutation\b/.test(t) && /\bmr\.?\b/.test(t) && /\bms\.?\b/.test(t);
              });
            for (const root of titleRoots) {
              const radios = [...root.querySelectorAll('input[type=radio], [role=radio], label, button, span')];
              const mr = radios.find(el => {
                const t = ((el.getAttribute('aria-label')||'') + ' ' + (el.innerText||'') + ' ' + (el.value||'')).trim();
                return /^mr\.?$/i.test(t);
              });
              if (mr) {
                forceClick(mr);
                clicked.push('title-radio-mr');
                // LTIMindtree/LTM: clicking the text node alone may not check the input.
                const inp = mr.matches && mr.matches('input[type=radio]')
                  ? mr
                  : (mr.querySelector && mr.querySelector('input[type=radio]'))
                    || [...root.querySelectorAll('input[type=radio]')].find(r =>
                         /mr\.?/i.test(((r.value||'') + ' ' + (r.getAttribute('aria-label')||'') + ' ' + (r.id||'')).trim())
                       );
                if (inp) {
                  forceClick(inp);
                  try {
                    inp.checked = true;
                    inp.setAttribute('aria-checked', 'true');
                    inp.dispatchEvent(new Event('change', {bubbles:true}));
                    inp.dispatchEvent(new Event('input', {bubbles:true}));
                    clicked.push('title-radio-input-mr');
                  } catch (e) {}
                }
                const lab = mr.closest && mr.closest('label');
                if (lab) {
                  forceClick(lab);
                  clicked.push('title-label-mr');
                }
                break;
              }
            }
            // Validation wall: "Answer this question to continue" under Title / Phone / Date.
            for (const err of document.querySelectorAll('[class*="error"], [role=alert], span, p, div')) {
              const et = (err.innerText || '').trim();
              if (!/answer this question to continue|choose an option to continue/i.test(et)) continue;
              const root = err.closest('fieldset, [class*="question"], [class*="Question"], li, section, form, div') || document.body;
              const ctx = (root.innerText || '').toLowerCase().slice(0, 400);
              if (/\btitle\b|\bsalutation\b|\bmr\.?\b/.test(ctx)) {
                const mrEl = [...root.querySelectorAll('input[type=radio], label, button, span, [role=radio]')]
                  .find(el => /^mr\.?$/i.test(((el.getAttribute('aria-label')||'') + ' ' + (el.innerText||'') + ' ' + (el.value||'')).trim()));
                if (mrEl) { forceClick(mrEl); clicked.push('validation-title-mr'); }
              }
              if (/\bphone\b|phone\s*no|\bmobile\b/.test(ctx)) {
                const phone = root.querySelector('input[type=tel], input:not([type=hidden]):not([type=radio]):not([type=checkbox])');
                if (phone && !(phone.value || '').trim()) {
                  const proto = window.HTMLInputElement.prototype;
                  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
                  const v = '8790251698';
                  if (setter) setter.call(phone, v); else phone.value = v;
                  phone.dispatchEvent(new InputEvent('input', {bubbles:true}));
                  phone.dispatchEvent(new Event('change', {bubbles:true}));
                  clicked.push('validation-phone');
                }
              }
              if (/^date|available date|\bdate\b/.test(ctx) && !/birth|dob/.test(ctx)) {
                const dateEl = root.querySelector('input[type=date], input:not([type=hidden]):not([type=radio]):not([type=checkbox])');
                if (dateEl && !(dateEl.value || '').trim()) {
                  const proto = window.HTMLInputElement.prototype;
                  const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set;
                  const type = (dateEl.getAttribute('type') || '').toLowerCase();
                  const v = type === 'date' ? '2026-08-15' : '15/08/2026';
                  if (setter) setter.call(dateEl, v); else dateEl.value = v;
                  dateEl.dispatchEvent(new InputEvent('input', {bubbles:true}));
                  dateEl.dispatchEvent(new Event('change', {bubbles:true}));
                  clicked.push('validation-date');
                }
              }
              if (/based in|are you based/.test(ctx)) {
                const yes = [...root.querySelectorAll('input[type=radio], label, button, span')]
                  .find(el => /\byes\b/i.test(((el.getAttribute('aria-label')||'') + ' ' + (el.innerText||'')).trim())
                    && !/\bno\b/i.test((el.innerText||'')));
                if (yes) { forceClick(yes); clicked.push('validation-based-in-yes'); }
              }
            }
            return {clicked, url: location.href};
            """
        ) or {}
    except Exception as e:
        print(f"  recover_selects_pick_err={e!s}"[:200], flush=True)
        picked = {}
    if opened or (isinstance(picked, dict) and picked.get("clicked")):
        print(f"  recover_selects opened={opened!r} picked={picked!r}", flush=True)
    return {"opened": opened, "picked": picked if isinstance(picked, dict) else {}}


def tick_required_agreements(sb) -> dict:
    """Tick employer privacy/EEO Agree options without double-toggling.

    Nagarro/Mattel SmartApply pages show a required 'Agree' checkbox (native,
    role=checkbox, or a short label). Clicking input then label unchecks it.
    Also recovers the 'Choose an option to continue' validation wall.
    """
    _switch_smartapply_frame(sb)
    try:
        result = sb.execute_script(
            r"""
            const clicked = [];
            const seen = new Set();
            const isOn = (el) => {
              if (!el) return false;
              if (el.checked === true) return true;
              return (el.getAttribute('aria-checked') || '').toLowerCase() === 'true';
            };
            const tick = (el, why) => {
              if (!el || seen.has(el) || isOn(el) || el.disabled) return false;
              seen.add(el);
              try { el.scrollIntoView({block:'center'}); } catch (e) {}
              try { el.click(); } catch (e) {}
              clicked.push(String(why || 'tick').slice(0, 60));
              return true;
            };
            const associatedBox = (el) => {
              if (!el) return null;
              if (el.matches?.('input[type=checkbox], input[type=radio], [role=checkbox], [role=radio]')) return el;
              return el.querySelector?.('input[type=checkbox], input[type=radio], [role=checkbox]')
                || (el.getAttribute('for') ? document.getElementById(el.getAttribute('for')) : null)
                || el.closest?.('label')?.querySelector('input[type=checkbox], input[type=radio], [role=checkbox]');
            };
            const nearby = (el) => {
              const wrap = el.closest('label, fieldset, [class*="question"], [class*="Question"], li, section, div') || el.parentElement || el;
              return ((el.getAttribute('aria-label') || '') + ' ' + (el.innerText || '') + ' ' + (el.value || '') + ' ' + (wrap.innerText || '')).toLowerCase().slice(0, 500);
            };
            for (const el of document.querySelectorAll('input[type=checkbox], input[type=radio], [role=checkbox], [role=radio]')) {
              if (isOn(el) || el.disabled) continue;
              const t = nearby(el);
              const short = ((el.getAttribute('aria-label') || '') + ' ' + (el.parentElement?.innerText || '') + ' ' + (el.value || '')).toLowerCase().slice(0, 80);
              if (/\bagree\b/.test(short) || /yes, i certify|i certify/.test(short)
                  || /privacy notice|declare that you have read|terms and conditions|i have read|by checking this|consent to|accurate and truthful/.test(t)) {
                if (!/don'?t certify|no, i/.test(short)) tick(el, 'box:' + short.slice(0, 40));
              }
            }
            for (const el of document.querySelectorAll('label, button, [role=button], [role=option]')) {
              const t = ((el.innerText || '') + ' ' + (el.getAttribute('aria-label') || '')).trim();
              if (!/^agree\b/i.test(t) || t.length > 48) continue;
              const box = associatedBox(el);
              if (box) {
                if (!isOn(box)) tick(box, 'label-for:' + t.slice(0, 40));
                continue;
              }
              tick(el, 'label:' + t.slice(0, 40));
            }
            const err = [...document.querySelectorAll('[class*="error"], [role=alert], span, p, div')]
              .find(e => /choose an option to continue/i.test(e.innerText || ''));
            if (err) {
              const root = err.closest('fieldset, [class*="question"], [class*="Question"], li, section, form, div') || document.body;
              const ctx = (root.innerText || '').toLowerCase().slice(0, 400);
              if (/\bcountry\b|dial.?code|calling.?code|phone.?code/.test(ctx)) {
                const trigger = root.querySelector('button, [role=combobox], [aria-haspopup=listbox], select');
                if (trigger) { try { trigger.click(); } catch (e) {} }
                const india = [...document.querySelectorAll('[role=option], li, button, div, span, a')]
                  .find(e => {
                    const t = ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')).trim();
                    return t && t.length <= 80 && /india|\+\s*91|\+91/.test(t) && !/indiana|indianapol/i.test(t);
                  });
                if (india) {
                  try { india.click(); clicked.push('validation-country-india'); } catch (e) {}
                }
              } else if (/highest (degree|education)|degree of education|education level|qualification|university|college/.test(ctx)) {
                const trigger = root.querySelector('button, [role=combobox], [aria-haspopup=listbox], select');
                if (trigger) { try { trigger.click(); } catch (e) {} }
                const edu = [...document.querySelectorAll('[role=option], li, button, div, span, a')]
                  .find(e => {
                    const t = ((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '')).trim();
                    return t && t.length <= 80 && /b\.?\s*tech|bachelor|b\.e\b|undergraduate|master|m\.?\s*tech/i.test(t)
                      && !/select an option|highest degree|what is your/i.test(t);
                  });
                if (edu) {
                  try { edu.click(); clicked.push('validation-education'); } catch (e) {}
                }
              } else if (/\btitle\b|\bsalutation\b/.test(ctx) && /\bmr\.?\b/.test(ctx)) {
                const mr = [...root.querySelectorAll('label, button, [role=radio], [role=option], input, span')]
                  .find(e => /^mr\.?$/i.test(((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.value || '')).trim()));
                if (mr) {
                  const box = associatedBox(mr) || mr;
                  if (!isOn(box)) tick(box, 'validation-title-mr');
                }
              } else {
                const opt = [...root.querySelectorAll('label, button, [role=option], [role=radio], [role=checkbox], input')]
                  .find(e => /^agree\b|^yes\b/i.test(((e.innerText || '') + ' ' + (e.getAttribute('aria-label') || '') + ' ' + (e.value || '')).trim()));
                if (opt) {
                  const box = associatedBox(opt) || opt;
                  if (!isOn(box)) tick(box, 'validation-agree');
                }
              }
            }
            return {clicked, url: location.href};
            """
        )
        if isinstance(result, dict) and result.get("clicked"):
            print(f"  agreements={result}", flush=True)
        return result if isinstance(result, dict) else {}
    except Exception as e:
        print(f"  agreements_error={e!s}"[:200], flush=True)
        return {}


def cookie_banner_visible_from_text(body: str) -> bool:
    """True when Indeed OneTrust/cookie strip text is on the page.

    That strip covers SmartApply Continue (WSA/Crowe questions stuck 2026-08-31).
    """
    b = (body or "").lower()
    if "accept all cookies" in b or "reject all cookies" in b:
        return True
    return ("reject all" in b or "accept all" in b) and "cookie" in b


def dismiss_indeed_cookie_banner(sb) -> str:
    """Click Accept/Reject on Indeed cookie strip so Continue is clickable."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        clicked = sb.execute_script(
            """
            const labels = [
              'accept all cookies', 'accept all', 'allow all cookies', 'allow all',
              'reject all cookies', 'reject all', 'i agree', 'got it', 'ok'
            ];
            const els = [...document.querySelectorAll(
              'button, a[role=button], [role=button], input[type=button], input[type=submit]'
            )];
            const textOf = (el) => ((el.innerText || el.value || el.getAttribute('aria-label') || '')).trim().toLowerCase();
            const scored = els.map(el => {
              const t = textOf(el);
              const r = el.getBoundingClientRect();
              const idx = labels.findIndex(l => t === l || t.startsWith(l));
              return {el, t, idx, onScreen: r.width > 0 && r.height > 0};
            }).filter(x => x.idx >= 0 && x.onScreen)
              .sort((a,b) => a.idx - b.idx);
            const hit = scored[0];
            if (!hit) return null;
            try { hit.el.scrollIntoView({block:'center'}); } catch (e) {}
            try { hit.el.click(); } catch (e) {}
            return (hit.el.innerText || hit.el.value || '').trim().slice(0, 80);
            """
        )
        if clicked:
            print(f"  cookie_banner_dismissed={clicked!r}", flush=True)
            time.sleep(0.7)
            return str(clicked)
    except Exception as exc:
        print(f"  cookie_banner_err={exc!s}"[:160], flush=True)
    return ""


def click_next_or_submit(
    sb, allow_disabled: bool = False, submit_only: bool = False
) -> str:
    # Cookie strip often covers Continue on questions/resume modules.
    dismiss_indeed_cookie_banner(sb)
    # SmartApply primary CTA via JS (visible Continue/Submit).
    _switch_smartapply_frame(sb)
    try:
        clicked = sb.execute_script(
            """
            const allowDisabled = Boolean(arguments[0]);
            const submitOnly = Boolean(arguments[1]);
            const labels = submitOnly
              ? ['submit your application','submit application','submit']
              : [
                  'submit your application','submit application','submit',
                  'review your application','continue applying','continue',
                  'next','save and continue','apply'
                ];
            const btns = [...document.querySelectorAll(
              'button, a[role=button], input[type=submit], [data-testid*="continue"], [data-testid*="submit"], .ia-continueButton'
            )];
            const textOf = (el) => ((el.innerText || el.value || el.getAttribute('aria-label') || '')).trim().toLowerCase();
            const reject = (t) => /close|cancel|report|skip to|view full|back|previous|remove|delete|preview what|employer sees|download|edit resume|save and close/.test(t);
            const score = (el) => {
              const t = textOf(el);
              // Exact / prefix match only — avoid matching "Preview..." via includes('review').
              const idx = labels.findIndex(l => t === l || t.startsWith(l + ' ') || t.startsWith(l));
              return idx === -1 ? 999 : idx;
            };
            // Include off-screen CTAs — review Submit is often below the fold.
            const candidates = btns.filter(el => {
              const r = el.getBoundingClientRect();
              const t = textOf(el);
              const disabled = el.disabled || el.getAttribute('aria-disabled') === 'true';
              const onScreen = r.width > 0 && r.height > 0;
              return t && !reject(t) && (onScreen || submitOnly)
                && (allowDisabled || !disabled);
            }).sort((a,b) => score(a)-score(b));
            let el = candidates.find(el => score(el) < 999);
            // On review, prefer an explicit Submit even if Continue also exists.
            const submitEl = candidates.find(el => /^submit/.test(textOf(el)));
            if (submitEl) el = submitEl;
            if (submitOnly && !submitEl) return null;
            if (!el && allowDisabled && !submitOnly) {
              el = btns.find(el => {
                const r = el.getBoundingClientRect();
                const t = textOf(el);
                return r.width > 0 && r.height > 0 && /submit|continue|next|apply/.test(t)
                  && !reject(t);
              });
            }
            if (!el) return null;
            if (el.disabled || el.getAttribute('aria-disabled') === 'true') {
              el.disabled = false;
              el.removeAttribute('disabled');
              el.setAttribute('aria-disabled', 'false');
            }
            el.scrollIntoView({block:'center'});
            el.click();
            return (el.innerText || el.value || '').trim().slice(0,80);
            """,
            allow_disabled,
            submit_only,
        )
        if clicked:
            return str(clicked)
    except Exception:
        pass
    for sel in (
        "button.ia-continueButton",
        "button.ia-ApplicationConfirmation-button",
        "button[type='submit']",
        "[data-testid='continue-button']",
        "[data-testid='submit-button']",
    ):
        try:
            if sb.is_element_visible(sel, timeout=1):
                sb.click(sel)
                return sel
        except Exception:
            pass
    return ""


def _is_submitted(body: str, url: str) -> bool:
    b = (body or "").lower()
    u = (url or "").lower()
    return any(
        x in b
        for x in (
            "application submitted",
            "your application was sent",
            "applied on indeed",
            "successfully submitted",
            "you applied",
            "application has been submitted",
            "thanks for applying",
            "thank you for applying",
            "we have received your application",
        )
    ) or (
        ("confirmation" in u and "review" not in u)
        or "post-apply" in u
        or "post_apply" in u
    )


def _page_has_recaptcha(sb) -> bool:
    """True only when a SmartApply checkbox widget is present (ignore footer badge text)."""
    try:
        body = (sb.get_text("body") or "").lower()
    except Exception:
        body = ""
    if "i'm not a robot" in body or "im not a robot" in body:
        return True
    # Prefer live SmartApply frames — page footer always mentions reCAPTCHA.
    frames = _recaptcha_anchor_frames(sb)
    if frames:
        return True
    try:
        return bool(
            sb.execute_script(
                """
                const frames=[...document.querySelectorAll('iframe[src*="recaptcha"][src*="anchor"]')];
                return frames.some(f => {
                  const src=(f.src||'').toLowerCase();
                  return src.includes('anchor') && !src.includes('6lcr30spaaaaa');
                });
                """
            )
        )
    except Exception:
        return False


def _recaptcha_token_present(sb) -> bool:
    try:
        return bool(
            sb.execute_script(
                """
                const ta = document.querySelector(
                  '#g-recaptcha-response, textarea[name="g-recaptcha-response"]'
                );
                return Boolean(ta && (ta.value || '').trim().length > 20);
                """
            )
        )
    except Exception:
        return False


# Indeed page footer badge sitekey — not the SmartApply review checkbox.
_FOOTER_RECAPTCHA_KEYS = (
    "6lcr30spaaaaa",  # sitewide "protected by reCAPTCHA" badge
)

# Google audio challenges rate-limit aggressively on cloud IPs.
_AUDIO_RATE_LIMITED = False
_AUDIO_RATE_LIMITED_AT = 0.0


def _recaptcha_anchor_frames(sb):
    """Find SmartApply Google reCAPTCHA checkbox iframes (skip footer badge)."""
    try:
        sb.driver.switch_to.default_content()
        frames = sb.driver.find_elements(
            "css selector",
            'iframe[title="reCAPTCHA"], '
            'iframe[src*="recaptcha/api2/anchor"], '
            'iframe[src*="recaptcha/enterprise/anchor"], '
            'iframe[src*="recaptcha.net"][src*="anchor"]',
        )
    except Exception:
        return []
    scored = []
    for fr in frames:
        try:
            src = (fr.get_attribute("src") or "").lower()
            title = (fr.get_attribute("title") or "").lower()
            if "bframe" in src or "challenge" in title:
                continue
            if "anchor" not in src and title != "recaptcha":
                continue
            if any(k in src for k in _FOOTER_RECAPTCHA_KEYS):
                continue
            rect = sb.driver.execute_script(
                "const r=arguments[0].getBoundingClientRect();"
                "return {w:r.width,h:r.height,y:r.y,x:r.x};",
                fr,
            ) or {}
            # Prefer the real checkbox widget (~74–80px tall) over tiny badges.
            h = float(rect.get("h") or 0)
            score = 0
            if 50 <= h <= 100:
                score += 5
            if "6ldn8qwp" in src:  # known SmartApply sitekey prefix
                score += 10
            # Probe for checkbox node — footer badge has no #recaptcha-anchor.
            has_anchor = False
            try:
                sb.driver.switch_to.frame(fr)
                has_anchor = bool(
                    sb.driver.find_elements("css selector", "#recaptcha-anchor, .recaptcha-checkbox, [role=checkbox]")
                )
            except Exception:
                has_anchor = False
            finally:
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
            if has_anchor:
                score += 20
            else:
                score -= 20
            scored.append((score, h, fr))
        except Exception:
            continue
    scored.sort(key=lambda t: (-t[0], -t[1]))
    # Keep only positively scored frames when available.
    good = [fr for sc, _h, fr in scored if sc > 0]
    return good if good else [fr for _sc, _h, fr in scored]



def _recaptcha_checkbox_checked(sb) -> bool:
    """Read the checkbox state from Google's cross-origin anchor iframe."""
    try:
        frames = _recaptcha_anchor_frames(sb)
        for frame in frames:
            try:
                sb.driver.switch_to.default_content()
                sb.driver.switch_to.frame(frame)
                anchor = sb.driver.find_element("css selector", "#recaptcha-anchor")
                checked = (anchor.get_attribute("aria-checked") or "").lower() == "true"
                sb.driver.switch_to.default_content()
                if checked:
                    return True
            except Exception:
                continue
    except Exception:
        pass
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    return False



def _force_recaptcha_onscreen(sb, frame) -> dict:
    """SmartApply often clips the enterprise widget past the right edge — pin it."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        sb.set_window_size(1600, 1000)
    except Exception:
        pass
    rect = sb.driver.execute_script(
        """
        const f = arguments[0];
        try { f.scrollIntoView({block:'center', inline:'center'}); } catch (e) {}
        // Walk scrollable ancestors.
        let p = f.parentElement;
        while (p) {
          try { p.scrollLeft = Math.max(0, (p.scrollWidth - p.clientWidth) / 2); } catch (e) {}
          p = p.parentElement;
        }
        const r0 = f.getBoundingClientRect();
        const clipped = r0.right > window.innerWidth - 8 || r0.left < 8
          || r0.bottom > window.innerHeight - 8 || r0.top < 8
          || r0.width < 10 || r0.height < 10;
        if (clipped) {
          f.style.setProperty('position', 'fixed', 'important');
          f.style.setProperty('left', '80px', 'important');
          f.style.setProperty('top', '180px', 'important');
          f.style.setProperty('z-index', '2147483647', 'important');
          f.style.setProperty('opacity', '1', 'important');
          f.style.setProperty('visibility', 'visible', 'important');
          f.style.setProperty('pointer-events', 'auto', 'important');
          f.style.setProperty('transform', 'none', 'important');
        }
        const r = f.getBoundingClientRect();
        return {
          x:r.x, y:r.y, width:r.width, height:r.height,
          vw: window.innerWidth, vh: window.innerHeight,
          visible: r.width>40 && r.height>40 && r.left>=0 && r.top>=0
            && r.right <= window.innerWidth && r.bottom <= window.innerHeight,
          pinned: clipped
        };
        """,
        frame,
    )
    time.sleep(0.5)
    return rect or {}


def _click_recaptcha_checkbox(sb) -> bool:
    """Click the reCAPTCHA anchor using DOM first, then a real GUI coordinate."""
    # Also search inside SmartApply child frames.
    try:
        _switch_smartapply_frame(sb)
    except Exception:
        pass
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass

    frames = _recaptcha_anchor_frames(sb)
    if not frames:
        # Nested: scan one level of iframes for enterprise anchors.
        try:
            parents = sb.driver.find_elements("css selector", "iframe")
            for parent in parents[:8]:
                try:
                    sb.driver.switch_to.default_content()
                    sb.driver.switch_to.frame(parent)
                    nested = sb.driver.find_elements(
                        "css selector",
                        'iframe[title="reCAPTCHA"], iframe[src*="anchor"]',
                    )
                    if nested:
                        # Click nested from inside parent.
                        frames = nested
                        print("  recaptcha_nested=1", flush=True)
                        break
                except Exception:
                    continue
            sb.driver.switch_to.default_content()
        except Exception:
            try:
                sb.driver.switch_to.default_content()
            except Exception:
                pass

    if not frames:
        print("  recaptcha_frame_missing=no_anchor_iframe", flush=True)
        return False

    for idx, frame in enumerate(frames):
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        # Re-query to avoid stale element after layout changes.
        frames = _recaptcha_anchor_frames(sb)
        if idx >= len(frames):
            break
        frame = frames[idx]
        rect = _force_recaptcha_onscreen(sb, frame)
        print(
            f"  recaptcha_onscreen pinned={rect.get('pinned')} "
            f"visible={rect.get('visible')} "
            f"rect=({round(rect.get('x',0))},{round(rect.get('y',0))},"
            f"{round(rect.get('width',0))}x{round(rect.get('height',0))})",
            flush=True,
        )

        # DOM click inside the checkbox iframe.
        try:
            frames = _recaptcha_anchor_frames(sb)
            frame = frames[min(idx, len(frames) - 1)]
            sb.driver.switch_to.frame(frame)
            time.sleep(0.4)
            anchor = None
            for sel in (
                "#recaptcha-anchor",
                ".recaptcha-checkbox",
                "#recaptcha-anchor-label",
                ".rc-anchor-checkbox",
                "[role=checkbox]",
            ):
                try:
                    els = sb.driver.find_elements("css selector", sel)
                    if els:
                        anchor = els[0]
                        break
                except Exception:
                    continue
            if anchor is None:
                # Dump frame HTML length for diagnosis.
                try:
                    html_len = len(sb.driver.page_source or "")
                except Exception:
                    html_len = -1
                raise RuntimeError(f"anchor checkbox missing inside frame html_len={html_len}")
            try:
                anchor.click()
            except Exception:
                sb.driver.execute_script("arguments[0].click()", anchor)
            time.sleep(2)
            checked = (anchor.get_attribute("aria-checked") or "").lower() == "true"
            sb.driver.switch_to.default_content()
            if checked or _recaptcha_token_present(sb):
                print("  recaptcha_checkbox=checked_dom", flush=True)
                return True
            # Checkbox click may open challenge without aria-checked flipping yet.
            if _solve_recaptcha_audio(sb):
                return True
        except Exception as exc:
            print(f"  recaptcha_dom_click={exc!s}"[:220], flush=True)
        finally:
            try:
                sb.driver.switch_to.default_content()
            except Exception:
                pass

    # Fallback: click the checkbox at its on-screen coordinates.
    try:
        import pyautogui

        frames = _recaptcha_anchor_frames(sb)
        if not frames:
            return False
        frame = frames[0]
        rect = _force_recaptcha_onscreen(sb, frame)
        metrics = sb.driver.execute_script(
            """
            return {
              sx: window.screenX,
              sy: window.screenY,
              chromeY: Math.max(0, window.outerHeight - window.innerHeight)
            };
            """
        )
        x = float(metrics.get("sx") or 0) + float(rect.get("x") or 0) + 28
        y = (
            float(metrics.get("sy") or 0)
            + float(metrics.get("chromeY") or 0)
            + float(rect.get("y") or 0)
            + 28
        )
        print(
            f"  recaptcha_gui_click=({round(x)},{round(y)}) "
            f"frame=({round(rect.get('x', 0))},{round(rect.get('y', 0))},"
            f"{round(rect.get('width', 0))}x{round(rect.get('height', 0))}) "
            f"visible={rect.get('visible')} pinned={rect.get('pinned')}",
            flush=True,
        )
        pyautogui.click(x=round(x), y=round(y), duration=0.2)
        time.sleep(2.5)
        if _recaptcha_checkbox_checked(sb) or _recaptcha_token_present(sb):
            print("  recaptcha_checkbox=checked_gui", flush=True)
            return True
        if _solve_recaptcha_audio(sb):
            return True
        # Last resort: SeleniumBase UC captcha helpers after pinning.
        try:
            sb.uc_gui_click_captcha()
            time.sleep(2)
            if _recaptcha_cleared(sb) or _solve_recaptcha_audio(sb):
                return True
        except Exception as exc:
            print(f"  recaptcha_uc_gui={exc!s}"[:180], flush=True)
    except Exception as exc:
        print(f"  recaptcha_gui_error={exc!s}"[:220], flush=True)
    return False


def _solve_recaptcha_audio(sb) -> bool:
    """Solve an opened reCAPTCHA audio challenge and verify its token."""
    global _AUDIO_RATE_LIMITED, _AUDIO_RATE_LIMITED_AT
    if _AUDIO_RATE_LIMITED and (time.time() - _AUDIO_RATE_LIMITED_AT) < 180:
        print("  recaptcha_audio=skip_rate_limited", flush=True)
        return False
    if _AUDIO_RATE_LIMITED and (time.time() - _AUDIO_RATE_LIMITED_AT) >= 180:
        _AUDIO_RATE_LIMITED = False
    try:
        import requests
        import speech_recognition as sr
    except Exception as exc:
        print(f"  recaptcha_audio_dependency={exc!s}"[:220], flush=True)
        return False

    challenge_selector = (
        'iframe[title*="challenge"], iframe[src*="recaptcha/api2/bframe"], '
        'iframe[src*="recaptcha/enterprise/bframe"], '
        'iframe[src*="/bframe"]'
    )
    try:
        sb.driver.switch_to.default_content()
        all_frames = sb.driver.find_elements("css selector", "iframe")
        frame_meta = []
        for iframe in all_frames:
            try:
                rect = sb.driver.execute_script(
                    """
                    const r=arguments[0].getBoundingClientRect();
                    return {x:r.x,y:r.y,w:r.width,h:r.height};
                    """,
                    iframe,
                )
                frame_meta.append(
                    {
                        "title": (iframe.get_attribute("title") or "")[:60],
                        "src": (iframe.get_attribute("src") or "")[:100],
                        "rect": rect,
                        "visible": iframe.is_displayed(),
                    }
                )
            except Exception:
                continue
        print(
            f"  recaptcha_frames={json.dumps(frame_meta, separators=(',', ':'))[:1000]}",
            flush=True,
        )
        frames = sb.driver.find_elements("css selector", challenge_selector)
    except Exception as exc:
        print(f"  recaptcha_challenge_frame={exc!s}"[:220], flush=True)
        return False
    if not frames:
        return False

    challenge = None
    for frame in frames:
        try:
            if frame.is_displayed():
                challenge = frame
                break
        except Exception:
            continue
    challenge = challenge or frames[0]

    try:
        sb.driver.switch_to.frame(challenge)
        # Switch from image tiles to the audio challenge.
        audio_button = None
        for _ in range(12):
            for selector in (
                "#recaptcha-audio-button",
                ".rc-button-audio",
                'button[title*="audio" i]',
                '[aria-label*="audio" i]',
            ):
                try:
                    candidate = sb.driver.find_element("css selector", selector)
                    if candidate.is_displayed():
                        audio_button = candidate
                        break
                except Exception:
                    continue
            if audio_button is not None:
                break
            time.sleep(0.5)
        if audio_button is None:
            raise RuntimeError("audio challenge button not found")
        try:
            audio_button.click()
        except Exception:
            sb.driver.execute_script("arguments[0].click()", audio_button)

        body = ""
        source = ""
        for _ in range(20):
            time.sleep(0.5)
            try:
                body = sb.driver.find_element("css selector", "body").text
            except Exception:
                body = ""
            if re.search(
                r"try again later|automated queries|unusual traffic", body, re.I
            ):
                print("  recaptcha_audio=rate_limited", flush=True)
                _AUDIO_RATE_LIMITED = True
                _AUDIO_RATE_LIMITED_AT = time.time()
                try:
                    # Reload captcha so the next checkbox click can pass cleanly.
                    reload_btn = sb.driver.find_element(
                        "css selector", "#recaptcha-reload-button, .rc-button-reload"
                    )
                    reload_btn.click()
                except Exception:
                    pass
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
                return False
            for selector in ("#audio-source", "audio source", "audio"):
                try:
                    media = sb.driver.find_element("css selector", selector)
                    source = (
                        media.get_attribute("src")
                        or media.get_attribute("data-src")
                        or ""
                    )
                    if source:
                        break
                except Exception:
                    continue
            if source:
                break
        if re.search(r"try again later|automated queries|unusual traffic", body, re.I):
            print("  recaptcha_audio=rate_limited", flush=True)
            return False
        if not source:
            print(
                f"  recaptcha_audio=no_source body={body[:400]!r}", flush=True
            )
            return False
    except Exception as exc:
        print(f"  recaptcha_audio_open={exc!s}"[:220], flush=True)
        return False
    finally:
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass

    audio_dir = Path("/tmp/cursor/indeed-recaptcha-audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    mp3 = audio_dir / "challenge.mp3"
    wav = audio_dir / "challenge.wav"
    proxy = os.environ.get("INDEED_HTTP_PROXY", PROXY)
    proxies = {"http": proxy, "https": proxy} if proxy else None
    try:
        response = requests.get(source, proxies=proxies, timeout=30)
        response.raise_for_status()
        mp3.write_bytes(response.content)
        converted = subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(mp3),
                "-ar",
                "16000",
                "-ac",
                "1",
                str(wav),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if converted.returncode != 0:
            print(f"  recaptcha_audio_ffmpeg={converted.stderr!s}"[:220], flush=True)
            return False
    except Exception as exc:
        print(f"  recaptcha_audio_download={exc!s}"[:220], flush=True)
        return False

    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(str(wav)) as audio_file:
            audio = recognizer.record(audio_file)
        answer = recognizer.recognize_google(audio).strip()
        answer = re.sub(r"[^A-Za-z0-9 ]+", " ", answer)
        answer = re.sub(r"\s+", " ", answer).strip()
        if not answer:
            return False
        print(f"  recaptcha_audio_answer={answer!r}", flush=True)
    except Exception as exc:
        print(f"  recaptcha_audio_transcribe={exc!s}"[:220], flush=True)
        return False

    try:
        sb.driver.switch_to.default_content()
        frames = sb.driver.find_elements("css selector", challenge_selector)
        challenge = next((f for f in frames if f.is_displayed()), frames[0])
        sb.driver.switch_to.frame(challenge)
        field = sb.driver.find_element("css selector", "#audio-response")
        field.clear()
        field.send_keys(answer)
        sb.driver.find_element(
            "css selector", "#recaptcha-verify-button"
        ).click()
        time.sleep(2.5)
    except Exception as exc:
        print(f"  recaptcha_audio_submit={exc!s}"[:220], flush=True)
        return False
    finally:
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass

    if _recaptcha_token_present(sb) or _recaptcha_checkbox_checked(sb):
        print("  recaptcha_audio=solved", flush=True)
        return True
    print("  recaptcha_audio=incorrect", flush=True)
    return False


def _recaptcha_cleared(sb) -> bool:
    return _recaptcha_token_present(sb) or _recaptcha_checkbox_checked(sb)



def _smartapply_sitekey(sb) -> str | None:
    try:
        sb.driver.switch_to.default_content()
        srcs = sb.execute_script(
            """
            return [...document.querySelectorAll('iframe[src*="recaptcha"][src*="anchor"]')]
              .map(f => f.src || '');
            """
        ) or []
    except Exception:
        srcs = []
    for src in srcs:
        low = (src or "").lower()
        if any(k in low for k in _FOOTER_RECAPTCHA_KEYS):
            continue
        m = re.search(r"[?&]k=([^&]+)", src)
        if m:
            return m.group(1)
    return None


def _solve_recaptcha_via_api(sb) -> bool:
    """Optional CapSolver / 2Captcha when audio is rate-limited on cloud IPs."""
    api_key = (
        os.environ.get("CAPSOLVER_API_KEY")
        or os.environ.get("TWOCAPTCHA_API_KEY")
        or os.environ.get("TWO_CAPTCHA_API_KEY")
        or ""
    ).strip()
    if not api_key:
        return False
    sitekey = _smartapply_sitekey(sb)
    try:
        pageurl = sb.get_current_url() or "https://smartapply.indeed.com/"
    except Exception:
        pageurl = "https://smartapply.indeed.com/"
    if not sitekey:
        print("  recaptcha_api=no_sitekey", flush=True)
        return False
    print(f"  recaptcha_api=start sitekey={sitekey[:12]}…", flush=True)
    try:
        import requests
    except Exception as exc:
        print(f"  recaptcha_api_dep={exc!s}"[:160], flush=True)
        return False

    token = None
    # CapSolver
    if os.environ.get("CAPSOLVER_API_KEY"):
        try:
            create = requests.post(
                "https://api.capsolver.com/createTask",
                json={
                    "clientKey": api_key,
                    "task": {
                        "type": "ReCaptchaV2EnterpriseTaskProxyLess",
                        "websiteURL": pageurl,
                        "websiteKey": sitekey,
                    },
                },
                timeout=60,
            ).json()
            task_id = create.get("taskId")
            if not task_id:
                print(f"  recaptcha_api_create={create}"[:220], flush=True)
            for _ in range(40):
                time.sleep(3)
                res = requests.post(
                    "https://api.capsolver.com/getTaskResult",
                    json={"clientKey": api_key, "taskId": task_id},
                    timeout=60,
                ).json()
                if res.get("status") == "ready":
                    token = (res.get("solution") or {}).get("gRecaptchaResponse")
                    break
                if res.get("status") == "failed" or res.get("errorId"):
                    print(f"  recaptcha_api_fail={res}"[:220], flush=True)
                    break
        except Exception as exc:
            print(f"  recaptcha_capsolver={exc!s}"[:200], flush=True)
    # 2Captcha fallback
    if not token and (
        os.environ.get("TWOCAPTCHA_API_KEY") or os.environ.get("TWO_CAPTCHA_API_KEY")
    ):
        try:
            create = requests.get(
                "https://2captcha.com/in.php",
                params={
                    "key": api_key,
                    "method": "userrecaptcha",
                    "googlekey": sitekey,
                    "pageurl": pageurl,
                    "enterprise": 1,
                    "json": 1,
                },
                timeout=60,
            ).json()
            if create.get("status") != 1:
                print(f"  recaptcha_2c_create={create}"[:220], flush=True)
            else:
                req_id = create.get("request")
                for _ in range(40):
                    time.sleep(5)
                    res = requests.get(
                        "https://2captcha.com/res.php",
                        params={
                            "key": api_key,
                            "action": "get",
                            "id": req_id,
                            "json": 1,
                        },
                        timeout=60,
                    ).json()
                    if res.get("status") == 1:
                        token = res.get("request")
                        break
                    if res.get("request") not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
                        print(f"  recaptcha_2c_fail={res}"[:220], flush=True)
                        break
        except Exception as exc:
            print(f"  recaptcha_2captcha={exc!s}"[:200], flush=True)

    if not token or len(token) < 20:
        return False
    try:
        sb.driver.switch_to.default_content()
        sb.execute_script(
            """
            const token = arguments[0];
            for (const sel of ['#g-recaptcha-response','textarea[name="g-recaptcha-response"]']) {
              let el = document.querySelector(sel);
              if (!el) {
                el = document.createElement('textarea');
                el.id = 'g-recaptcha-response';
                el.name = 'g-recaptcha-response';
                el.style.display = 'block';
                document.body.appendChild(el);
              }
              el.value = token;
              el.innerHTML = token;
              el.dispatchEvent(new Event('input', {bubbles:true}));
              el.dispatchEvent(new Event('change', {bubbles:true}));
            }
            try {
              if (window.___grecaptcha_cfg) {
                const clients = window.___grecaptcha_cfg.clients || {};
                // Best-effort callback invoke
                JSON.stringify(clients, (k,v) => {
                  if (v && typeof v === 'object') {
                    for (const val of Object.values(v)) {
                      if (typeof val === 'function' && val.length === 1) {
                        try { val(token); } catch (e) {}
                      }
                    }
                  }
                  return v;
                });
              }
            } catch (e) {}
            return true;
            """,
            token,
        )
        time.sleep(1)
        if _recaptcha_token_present(sb):
            print("  recaptcha_api=token_injected", flush=True)
            return True
    except Exception as exc:
        print(f"  recaptcha_api_inject={exc!s}"[:200], flush=True)
    return False


def _dismiss_recaptcha_challenge(sb) -> None:
    """Close a stuck/rate-limited bframe so the next checkbox click is clean."""
    try:
        sb.driver.switch_to.default_content()
        sb.press_keys("body", "\ue00c")  # ESC
    except Exception:
        pass
    try:
        sb.execute_script(
            """
            for (const f of document.querySelectorAll('iframe[src*="bframe"]')) {
              try { f.remove(); } catch (e) {}
            }
            """
        )
    except Exception:
        pass


def clear_recaptcha(sb, attempts: int = 3) -> bool:
    """Clear Google reCAPTCHA on SmartApply review.

    Prefer a single PyAutoGUI/DOM checkbox click + at most one audio solve.
    Nested SeleniumBase uc_gui_* FileLocks deadlock on filelock>=3.20.

    Never sleep through Google audio rate-limit cooldowns — that hung daily
    apply for 4+ minutes per review job. Bail fast so the runner can mark
    `easy_apply_recaptcha` and continue inventory.
    """
    global _AUDIO_RATE_LIMITED, _AUDIO_RATE_LIMITED_AT
    for n in range(attempts):
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        if _recaptcha_cleared(sb):
            return True
        if not _page_has_recaptcha(sb):
            return True
        print(f"  recaptcha_attempt={n+1}", flush=True)

        # Rate-limited: dismiss challenge and exit — do NOT sleep 240s.
        if _AUDIO_RATE_LIMITED:
            _dismiss_recaptcha_challenge(sb)
            elapsed = time.time() - _AUDIO_RATE_LIMITED_AT
            print(
                f"  recaptcha_rate_limited skip_cooldown elapsed={int(elapsed)}s",
                flush=True,
            )
            if _solve_recaptcha_via_api(sb):
                return True
            break

        # Direct DOM + PyAutoGUI click on the SmartApply (non-footer) widget.
        clicked = _click_recaptcha_checkbox(sb)
        if _recaptcha_cleared(sb):
            print("  recaptcha_token=ok", flush=True)
            return True
        time.sleep(1.5)
        if _recaptcha_cleared(sb):
            return True

        # One audio attempt only when a challenge is open and not rate-limited.
        if clicked or _page_has_recaptcha(sb):
            if _solve_recaptcha_audio(sb):
                return True
            if _solve_recaptcha_via_api(sb):
                return True

        if _AUDIO_RATE_LIMITED:
            _dismiss_recaptcha_challenge(sb)
            # Don't burn remaining attempts during the cool-down window.
            break
    return _recaptcha_cleared(sb)


def _gui_click_submit(sb) -> bool:
    """Trusted OS-level click on Submit when captcha is already cleared."""
    try:
        import pyautogui
    except Exception as exc:
        print(f"  review_gui_submit_dep={exc!s}"[:160], flush=True)
        return False
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    try:
        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception:
        pass
    time.sleep(0.3)
    try:
        rect = sb.execute_script(
            """
            const btns=[...document.querySelectorAll('button, a[role=button], input[type=submit]')];
            const textOf = (b) => ((b.innerText||b.value||b.getAttribute('aria-label')||'')).trim().toLowerCase();
            const el = btns
              .map(b => ({b, t: textOf(b), r: b.getBoundingClientRect()}))
              .filter(x => x.r.width>40 && x.r.height>10 && /submit/.test(x.t) && !/preview|employer sees/.test(x.t))
              .sort((a,b) => (/your application/.test(a.t)?0:1) - (/your application/.test(b.t)?0:1))
              [0];
            if (!el) return null;
            el.b.scrollIntoView({block:'center'});
            const r = el.b.getBoundingClientRect();
            return {x: r.left + r.width/2, y: r.top + r.height/2, t: el.t, w: r.width, h: r.height};
            """
        )
    except Exception as exc:
        print(f"  review_gui_submit_rect={exc!s}"[:160], flush=True)
        return False
    if not rect:
        return False
    try:
        win = sb.driver.get_window_position()
        # Chrome content offset under title bar (headed UC on Xvfb).
        chrome_y = 85
        x = int(win.get("x", 0) + rect["x"])
        y = int(win.get("y", 0) + chrome_y + rect["y"])
        print(
            f"  review_gui_submit=({x},{y}) label={rect.get('t')!r}",
            flush=True,
        )
        pyautogui.moveTo(x, y, duration=0.15)
        pyautogui.click()
        time.sleep(0.6)
        return True
    except Exception as exc:
        print(f"  review_gui_submit_err={exc!s}"[:180], flush=True)
        return False


def submit_review_application(sb, deadline: float | None = None) -> bool:
    """On review-module: solve reCAPTCHA, tick cert boxes, force Submit."""
    try:
        sb.driver.switch_to.default_content()
    except Exception:
        pass
    # Submit CTA is below the fold on many SmartApply review pages.
    try:
        sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception:
        pass
    # Always try to clear captcha on review — widget can hydrate after first paint.
    for _ in range(8):
        if deadline and time.time() > deadline:
            return False
        if _page_has_recaptcha(sb) or _smartapply_sitekey(sb):
            break
        time.sleep(0.5)
    captcha_needed = (_page_has_recaptcha(sb) or _smartapply_sitekey(sb)) and not _recaptcha_cleared(sb)
    if captcha_needed:
        # Cap attempts; never enter multi-minute cooldown sleeps.
        clear_recaptcha(sb, attempts=2)
        if not _recaptcha_cleared(sb):
            _solve_recaptcha_via_api(sb)
        if not _recaptcha_cleared(sb) and _AUDIO_RATE_LIMITED:
            print("  review_submit=abort_rate_limited", flush=True)
            return False
    try:
        sb.execute_script(
            """
            for (const c of document.querySelectorAll('input[type=checkbox], [role=checkbox]')) {
              // Skip recaptcha (cross-origin iframe, not this document).
              // Click once — input+label double-click toggles the box back off.
              if (c.disabled) continue;
              if (c.checked || c.getAttribute('aria-checked') === 'true') continue;
              try { c.click(); } catch (e) {}
            }
            window.scrollTo(0, document.body.scrollHeight);
            """
        )
    except Exception:
        pass
    # Prefer SeleniumBase click (fires trusted events) over bare JS click.
    clicked_sel = ""
    for sel in (
        "//button[normalize-space()='Submit your application']",
        "//button[contains(normalize-space(.), 'Submit your application')]",
        "//button[contains(normalize-space(.), 'Submit application')]",
        "//button[normalize-space()='Submit']",
        "button.ia-continueButton",
    ):
        try:
            if sb.is_element_present(sel):
                try:
                    sb.scroll_to(sel)
                except Exception:
                    pass
                try:
                    sb.uc_click(sel)
                except Exception:
                    try:
                        sb.click(sel)
                    except Exception:
                        continue
                clicked_sel = sel
                print(f"  review_click={sel!r}", flush=True)
                break
        except Exception:
            continue
    if not clicked_sel:
        # JS fallback — finds Submit even when off-screen / aria-disabled.
        try:
            clicked_sel = sb.execute_script(
                """
                window.scrollTo(0, document.body.scrollHeight);
                const btns=[...document.querySelectorAll('button, a[role=button], [role=button], input[type=submit]')];
                const textOf = (b) => ((b.innerText||b.value||b.getAttribute('aria-label')||'')).trim().toLowerCase();
                const el = btns
                  .map(b => ({b, t: textOf(b), r: b.getBoundingClientRect()}))
                  .filter(x => x.r.width+x.r.height > 0 && /submit/.test(x.t) && !/preview|employer sees/.test(x.t))
                  .sort((a,b) => (/your application/.test(a.t)?0:1) - (/your application/.test(b.t)?0:1))
                  [0]?.b;
                if (!el) return null;
                el.disabled=false; el.removeAttribute('disabled');
                el.setAttribute('aria-disabled','false');
                el.scrollIntoView({block:'center'});
                el.click();
                return (el.innerText||el.value||'').trim().slice(0,80);
                """
            )
            print(f"  review_js_submit={clicked_sel!r}", flush=True)
        except Exception:
            clicked_sel = None
    if not clicked_sel:
        clicked = click_next_or_submit(
            sb, allow_disabled=True, submit_only=True
        )
        print(f"  review_js_click={clicked!r}", flush=True)
        clicked_sel = clicked or ""
    # When captcha is already green-checked, JS/SB clicks often no-op —
    # use a trusted GUI click on the Submit CTA (seen 2026-08-12).
    if _recaptcha_cleared(sb) or not captcha_needed:
        if _gui_click_submit(sb):
            clicked_sel = clicked_sel or "gui_submit"
    if not clicked_sel:
        return False

    # Poll for confirmation / navigation away from review.
    for i in range(20):
        if deadline and time.time() > deadline:
            return False
        time.sleep(0.5)
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        try:
            url = sb.get_current_url() or ""
            body = (sb.get_text("body") or "")
        except Exception:
            url, body = "", ""
        if _is_submitted(body, url):
            return True
        if "review-module" not in url.lower() and "smartapply" not in url.lower():
            if not re.search(r"something went wrong|unable to submit|try again", body, re.I):
                return True
        # reCAPTCHA may reappear / remain unsolved after a dead Submit click.
        # Never re-enter a long captcha loop when audio is rate-limited.
        if (
            i in (3, 8, 14)
            and _page_has_recaptcha(sb)
            and not _recaptcha_cleared(sb)
            and not _AUDIO_RATE_LIMITED
        ):
            clear_recaptcha(sb, attempts=1)
            try:
                sb.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            except Exception:
                pass
            click_next_or_submit(sb, allow_disabled=True, submit_only=True)
            _gui_click_submit(sb)
        elif i in (3, 8) and _recaptcha_cleared(sb):
            _gui_click_submit(sb)
        try:
            sb.press_keys("body", "\ue00c")  # ESC preview overlays
        except Exception:
            pass
    return False


def easy_apply_flow(sb, max_steps: int = 24, deadline: float | None = None) -> str:
    """Returns 'submitted' | 'external' | 'failed' | 'recaptcha' | 'already_applied' | 'login_required'."""
    stuck_questions = 0
    review_submit_attempts = 0
    same_cta_streak = 0
    last_cta_key = ""
    if not wait_for_smartapply_surface(sb, seconds=4):
        print("  easy_apply_no_smartapply_surface", flush=True)
        return "failed"
    for step in range(max_steps):
        if deadline and time.time() > deadline:
            return "failed"
        time.sleep(0.8)
        # SmartApply often navigates to smartapply.indeed.com modules.
        try:
            sb.driver.switch_to.default_content()
        except Exception:
            pass
        body = ""
        url = ""
        try:
            url = sb.get_current_url() or ""
            body = (sb.get_text("body") or "").lower()
        except Exception:
            pass
        if already_applied(body, url):
            return "already_applied"
        # Left Indeed for employer ATS mid-flow — complete externally, not login_required.
        url_l = (url or "").lower()
        if url_l.startswith("http") and "indeed.com" not in url_l and "indeedapply" not in url_l:
            return "external"
        if looks_login_wall(body, url):
            return "login_required"
        if _is_submitted(body, url):
            return "submitted"
        if "apply on company site" in body and "indeed apply" not in body:
            return "external"
        # OneTrust strip covers Continue on questions/resume (WSA screenshot 2026-08-31).
        if cookie_banner_visible_from_text(body):
            dismiss_indeed_cookie_banner(sb)
        # Review page: dedicated submit path (JS click alone often no-ops).
        if "review-module" in url.lower() or (
            "review" in url.lower() and "question" not in url.lower()
        ):
            review_submit_attempts += 1
            print(f"  ea_step={step} review_submit attempt={review_submit_attempts} url={url[:90]}", flush=True)
            dismiss_indeed_cookie_banner(sb)
            if submit_review_application(sb, deadline=deadline):
                return "submitted"
            # CAPTCHA wall: don't burn the whole job budget (AUTO_FIX ~3–4 min).
            captcha_unsolved = (
                _page_has_recaptcha(sb) and not _recaptcha_cleared(sb)
            )
            # Audio rate-limit → bail after 1–2 attempts (no 240s sleeps).
            if captcha_unsolved and (
                _AUDIO_RATE_LIMITED or review_submit_attempts >= 2
            ):
                try:
                    sample = (sb.get_text("body") or "")[:500].replace("\n", " | ")
                    print(f"  review_recaptcha_blocked sample={sample!r}", flush=True)
                    sb.save_screenshot("/opt/cursor/artifacts/indeed-review-stuck.png")
                except Exception:
                    pass
                return "recaptcha"
            if review_submit_attempts >= 3 and captcha_unsolved:
                try:
                    sample = (sb.get_text("body") or "")[:500].replace("\n", " | ")
                    print(f"  review_recaptcha_blocked sample={sample!r}", flush=True)
                    sb.save_screenshot("/opt/cursor/artifacts/indeed-review-stuck.png")
                except Exception:
                    pass
                return "recaptcha"
            if review_submit_attempts >= 4:
                try:
                    sample = (sb.get_text("body") or "")[:500].replace("\n", " | ")
                    print(f"  review_stuck sample={sample!r}", flush=True)
                    sb.save_screenshot("/opt/cursor/artifacts/indeed-review-stuck.png")
                except Exception:
                    pass
                return "failed"
            continue
        # Long employer privacy / EEO walls hide fields + Continue below the fold.
        try:
            sb.execute_script(
                """
                const main = document.querySelector('main, [role=main], .ia-BasePage-content, form') || document.scrollingElement;
                if (main) main.scrollTop = main.scrollHeight;
                window.scrollBy(0, Math.min(900, document.body.scrollHeight));
                """
            )
        except Exception:
            pass
        dismiss_indeed_cookie_banner(sb)
        fill_common_questions(sb)
        # Resume card / upload: prefer existing Rafi card; retry on Indeed upload error.
        if "resume-selection" in url or "resume" in url.lower():
            st = _smartapply_resume_status(sb)
            if st.get("error") or not st.get("ok"):
                print(f"  resume_module_retry status={st}", flush=True)
                upload_smartapply_resume(sb)
        dismiss_indeed_cookie_banner(sb)
        clicked = click_next_or_submit(sb, allow_disabled=False)
        print(f"  ea_step={step} clicked={clicked!r} url={url[:90]}", flush=True)
        # Same CTA on same module without navigation → validation wall; abort early.
        cta_key = f"{(url or '').split('?')[0]}|{(clicked or '').lower()}"
        if clicked and cta_key == last_cta_key:
            same_cta_streak += 1
        else:
            same_cta_streak = 0
            last_cta_key = cta_key if clicked else ""
        if same_cta_streak >= 2:
            dismiss_indeed_cookie_banner(sb)
            tick_required_agreements(sb)
            recover_required_selects(sb)
            # Resume upload error: re-upload instead of burning Continue clicks.
            try:
                if "resume-selection" in (url or "") or "resume" in (url or "").lower():
                    st = _smartapply_resume_status(sb)
                    if st.get("error") or not st.get("ok"):
                        print(f"  cta_stuck_resume_reupload status={st}", flush=True)
                        upload_smartapply_resume(sb)
            except Exception as exc:
                print(f"  cta_stuck_resume_err={exc!s}"[:160], flush=True)
            # Questions Continue often no-ops under invisible reCAPTCHA (ValGenesis).
            try:
                if _page_has_recaptcha(sb) and not _recaptcha_cleared(sb):
                    print("  questions_recaptcha_attempt", flush=True)
                    clear_recaptcha(sb, attempts=1)
            except Exception as exc:
                print(f"  questions_recaptcha_err={exc!s}"[:160], flush=True)
        if same_cta_streak >= 3:
            try:
                sample = (sb.get_text("body") or "")[:400].replace("\n", " | ")
                print(
                    f"  cta_stuck streak={same_cta_streak} cta={clicked!r} sample={sample!r}",
                    flush=True,
                )
                sb.save_screenshot("/opt/cursor/artifacts/indeed-questions-stuck.png")
            except Exception:
                pass
            return "failed"
        if not clicked:
            # Review / questions: fill again, wait for CTA enable, then force-click.
            time.sleep(1.5)
            fill_common_questions(sb)
            time.sleep(0.8)
            if "review" in url.lower() or "question" in url.lower():
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
                try:
                    clicked = sb.execute_script(
                        """
                        const btns=[...document.querySelectorAll('button, [role=button], input[type=submit]')];
                        const textOf = (b) => ((b.innerText||b.value||b.getAttribute('aria-label')||'')).trim().toLowerCase();
                        const reject = (t) => /close|cancel|back|previous|preview|employer sees|download|edit/.test(t);
                        const scored = btns.map(b => {
                          const t=textOf(b);
                          const r=b.getBoundingClientRect();
                          let s = 999;
                          if (/^submit your application|^submit application|^submit$/.test(t)) s = 0;
                          else if (/^review your application/.test(t)) s = 1;
                          else if (/^continue/.test(t)) s = 2;
                          else if (/^next|^apply$/.test(t)) s = 3;
                          return {b,t,r,s};
                        }).filter(x => x.r.width>0 && x.r.height>0 && x.s<999 && !reject(x.t))
                          .sort((a,b) => a.s-b.s);
                        const el = scored[0]?.b;
                        if(!el) return null;
                        el.disabled=false; el.removeAttribute('disabled');
                        el.setAttribute('aria-disabled','false');
                        el.click();
                        return (el.innerText||el.value||'').trim().slice(0,80);
                        """
                    )
                except Exception:
                    clicked = None
            if not clicked:
                try:
                    sb.driver.switch_to.default_content()
                except Exception:
                    pass
                clicked = click_next_or_submit(sb, allow_disabled=True)
            if not clicked and "review" not in url.lower() and "questions" not in url.lower():
                break
            if not clicked:
                stuck_questions += 1
                if stuck_questions >= 6:
                    try:
                        sample = (sb.get_text("body") or "")[:400].replace("\n", " | ")
                        print(f"  questions_stuck sample={sample!r}", flush=True)
                        sb.save_screenshot(
                            "/opt/cursor/artifacts/indeed-questions-stuck.png"
                        )
                    except Exception:
                        pass
                    break
                continue
            stuck_questions = 0
        else:
            stuck_questions = 0
        time.sleep(1.5)
        try:
            body = sb.get_text("body") or ""
            url = sb.get_current_url() or ""
        except Exception:
            body, url = "", ""
        if _is_submitted(body, url):
            return "submitted"
        # Landed on review after Continue — dedicated submit next loop.
        if "review-module" in (url or "").lower() or (
            "review" in (url or "").lower() and "question" not in (url or "").lower()
        ):
            continue
    return "failed"


def main() -> int:
    os.environ.setdefault("DISPLAY", ":1")
    _patch_filelock_singleton()
    proxy = ensure_warp()
    if not RESUME.exists():
        _emit({"error": "resume_missing", "path": str(RESUME)})
        return 2

    from seleniumbase import SB

    # Re-assert singleton FileLock inside already-imported SB modules.
    try:
        from tools.indeed.filelock_patch import rebind_seleniumbase_filelock

        rebind_seleniumbase_filelock()
    except Exception as exc:
        print(f"  filelock_rebind={exc!s}"[:160], flush=True)

    prep = prepare_profile()
    # Persist a just-healed hybrid Passport back to the seed profile so the
    # next prepare() does not copy expired Desktop cookies over a live session.
    try:
        if (prep or {}).get("hasAuth") and Path(PROFILE).exists():
            seed = Path(SEED_PROFILE)
            hyb = Path(PROFILE)
            for rel in (
                "Default/Cookies",
                "Default/Cookies-journal",
                "Local State",
            ):
                s, d = hyb / rel, seed / rel
                if s.exists():
                    d.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, d)
            print("  seed_passport_synced_from_hybrid=1", flush=True)
    except Exception as exc:
        print(f"  seed_passport_sync_err={exc!s}"[:160], flush=True)
    report = {
        "portal": "indeed",
        "source": "home-local" if os.environ.get("INDEED_SKIP_WARP") == "1" else "cloud-warp-uc",
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "proxy": proxy or "direct",
        "resume": str(RESUME),
        "profilePrep": prep,
        "counts": {
            "applied": 0,
            "external": 0,
            "rejected": 0,
            "blocked": 0,
            "skipped": 0,
            "seen": 0,
        },
        "applied": [],
        "external": [],
        "rejected": [],
        "blocked": [],
        "skipped": [],
        "seen": [],
        "ok": False,
    }

    def _flush_report_on_exit() -> None:
        """Persist counts if spawnSync/SIGTERM kills the runner mid-inventory."""
        if report.get("finishedAt"):
            return
        try:
            report["finishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            applied_n = report["counts"]["applied"] + report["counts"]["external"]
            report["ok"] = applied_n > 0
            report["date"] = report["finishedAt"][:10]
            report["exitHint"] = "atexit_flush"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
        except Exception:
            pass

    import atexit

    atexit.register(_flush_report_on_exit)

    sb_kwargs = dict(
        uc=True,
        headed=True,
        user_data_dir=PROFILE,
        chromium_arg="--no-sandbox,--disable-dev-shm-usage",
    )
    if proxy:
        sb_kwargs["proxy"] = proxy if proxy.startswith("socks5") else proxy

    # Leftover UC Chrome from a killed run holds the profile → SessionNotCreated.
    try:
        import signal

        for rel in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
            p = Path(PROFILE) / rel
            if p.exists() or p.is_symlink():
                p.unlink(missing_ok=True)
        killed = 0
        needle = str(PROFILE)
        for line in subprocess.check_output(["ps", "-eo", "pid,cmd"], text=True).splitlines():
            if needle not in line and "uc_driver" not in line:
                continue
            if "ps -eo" in line:
                continue
            pid_s = line.strip().split(None, 1)[0]
            try:
                os.kill(int(pid_s), signal.SIGTERM)
                killed += 1
            except Exception:
                pass
        if killed:
            time.sleep(1.5)
            print(f"  leftover_chrome_killed={killed}", flush=True)
    except Exception as exc:
        print(f"  leftover_chrome_err={exc!s}"[:160], flush=True)

    with _stdout_to_stderr():
      with SB(**sb_kwargs) as sb:
        try:
            sb.set_default_timeout(4)
        except Exception:
            pass
        try:
            sb.set_window_size(1600, 1000)
            sb.set_window_position(20, 40)
        except Exception:
            pass
        sb.uc_open_with_reconnect("https://in.indeed.com/", 5)
        time.sleep(2)
        if not clear_cf(sb):
            report["blocked"].append({"reason": "still_blocked_after_uc"})
            report["counts"]["blocked"] = 1
            report["blockerSummary"] = "indeed_cloudflare_still_blocked"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
            _emit(report)
            return 5

        # in.indeed.com marketing home always shows "Get Started" / "Sign in"
        # even with a valid Passport session. Confirm on account settings
        # (and treat SERP Messages nav as signed-in). Homepage-only heuristics
        # caused a false indeed_login_required after CF clear (2026-08-15).
        try:
            home_body = (sb.get_text("body") or "")[:2500]
            home_title = sb.get_title() or ""
            home_url = sb.get_current_url() or ""
        except Exception:
            home_body, home_title, home_url = "", "", ""

        session_ok = looks_signed_in(home_body, home_url)
        if not session_ok:
            try:
                sb.uc_open_with_reconnect("https://in.indeed.com/", 5)
                time.sleep(3)
                if not clear_cf(sb):
                    pass
                home_body = (sb.get_text("body") or "")[:2500]
                home_title = sb.get_title() or ""
                home_url = sb.get_current_url() or ""
                session_ok = looks_signed_in(home_body, home_url)
            except Exception:
                pass
        if not session_ok:
            warmed = restore_signed_in(sb)
            report["sessionRestore"] = warmed
            try:
                home_body = (sb.get_text("body") or "")[:2500]
                home_title = sb.get_title() or ""
                home_url = sb.get_current_url() or ""
            except Exception:
                pass
            if warmed.get("ok") or looks_signed_in(home_body, home_url):
                session_ok = True
            elif warmed.get("loginWall") or looks_login_wall(home_body, home_url):
                # Passport expired / Sign-in wall: try Gmail SSO before hard stop.
                try:
                    from tools.indeed.google_sso import try_google_sso

                    sso = try_google_sso(sb)
                except Exception as exc:
                    sso = {
                        "ok": False,
                        "reason": "google_sso_error",
                        "error": str(exc)[:200],
                    }
                report["googleSso"] = sso
                try:
                    home_body = (sb.get_text("body") or "")[:2500]
                    home_title = sb.get_title() or ""
                    home_url = sb.get_current_url() or ""
                except Exception:
                    pass
                if looks_signed_in(home_body, home_url) or (
                    sso.get("ok") and not looks_login_wall(home_body, home_url)
                ):
                    session_ok = True
                    report["sessionRestore"] = {
                        **(warmed if isinstance(warmed, dict) else {}),
                        "via": "google_sso",
                        "ok": True,
                    }
                else:
                    hint = sso.get("hint") or (
                        "Account/auth is a Sign-in wall — Google SSO did not "
                        "open accounts.google.com. Set GOOGLE_PASSWORD (Gmail, "
                        "not LINKEDIN_PASSWORD) or refresh Indeed Passport via "
                        "Desktop Chrome + sync-chrome-sessions + Save Snapshot"
                    )
                    report["blocked"].append(
                        {
                            "reason": "indeed_login_required",
                            "title": home_title[:120],
                            "bodySample": home_body[:400],
                            "googleSsoReason": sso.get("reason"),
                            "hint": hint,
                        }
                    )
                    report["counts"]["blocked"] = 1
                    report["blockerSummary"] = "indeed_login_required"
                    OUT.parent.mkdir(parents=True, exist_ok=True)
                    OUT.write_text(json.dumps(report, indent=2))
                    _emit(report)
                    return 5
            else:
                # Marketing home alone is not proof of logout. Continue;
                # search/apply paths still skip already-applied and login walls.
                report["sessionWarm"] = "unconfirmed_continue"

        seen_keys: set[str] = set()
        for query, location in search_queries():
            if report["counts"]["applied"] + report["counts"]["external"] >= MAX_APPLIES:
                break
            if report["counts"]["seen"] >= MAX_SEEN:
                break
            if not run_homepage_search(sb, query, location):
                report["blocked"].append(
                    {"reason": "search_blocked", "query": query, "location": location}
                )
                report["counts"]["blocked"] += 1
                continue

            # Collect job cards
            cards = []
            for sel in (
                "a.jcs-JobTitle",
                "h2.jobTitle a",
                "a[data-jk]",
                "a[href*='jk=']",
            ):
                try:
                    cards = sb.find_elements(sel)
                    if cards:
                        break
                except Exception:
                    continue

            hrefs = []
            for c in cards:
                try:
                    href = c.get_attribute("href") or ""
                    jk = c.get_attribute("data-jk") or ""
                    t = (c.text or "").strip()
                    if href:
                        hrefs.append((t, href, jk))
                except Exception:
                    continue

            for title_t, href, jk in hrefs[:30]:
                if report["counts"]["applied"] + report["counts"]["external"] >= MAX_APPLIES:
                    break
                if report["counts"]["seen"] >= MAX_SEEN:
                    break
                key = job_dedupe_key(href, jk)
                if key in seen_keys:
                    continue

                try:
                    sb.uc_open_with_reconnect(href, 4)
                    time.sleep(2)
                    clear_cf(sb, attempts=2)
                except Exception as e:
                    report["rejected"].append({"title": title_t, "error": str(e)[:160]})
                    report["counts"]["rejected"] += 1
                    continue

                # Pagead/rc cards often lack jk= until after navigation. Re-key on
                # the resolved viewjob URL so PanApps-style repeats do not re-burn
                # the company-site / CF hop budget (11× same jk on 2026-08-24).
                try:
                    resolved = sb.get_current_url() or ""
                except Exception:
                    resolved = ""
                real_key = job_dedupe_key(resolved, "") or key
                if real_key in seen_keys or key in seen_keys:
                    print(f"  dedupe_skip key={real_key[:24]}", flush=True)
                    continue
                seen_keys.add(key)
                seen_keys.add(real_key)
                report["counts"]["seen"] += 1
                # Persist progress for the notification job even if interrupted.
                try:
                    OUT.parent.mkdir(parents=True, exist_ok=True)
                    OUT.write_text(json.dumps(report, indent=2))
                except Exception:
                    pass

                page_title = sb.get_title() or title_t
                try:
                    body = sb.get_text("body") or ""
                except Exception:
                    body = ""
                if blocked(page_title, body):
                    report["blocked"].append({"reason": "job_page_blocked", "title": title_t})
                    report["counts"]["blocked"] += 1
                    continue
                # location heuristic
                loc_m = re.search(
                    r"([A-Za-z].{0,40}(Hyderabad|Telangana|Remote|Bengaluru|Bangalore|Pune|Chennai|Mumbai|Noida|Gurgaon|Delhi)[^\n]{0,40})",
                    body,
                )
                location = loc_m.group(1).strip() if loc_m else ""
                company = ""
                try:
                    company = sb.get_text(
                        "[data-company-name], .jobsearch-InlineCompanyRating a, [data-testid='inlineHeader-companyName']"
                    )
                except Exception:
                    pass

                item = {
                    "title": page_title[:160],
                    "company": (company or "")[:120],
                    "location": location[:120],
                    "url": sb.get_current_url(),
                }
                report["seen"].append(item)

                if already_applied(body, item.get("url") or ""):
                    item["reason"] = "already_applied"
                    report["skipped"].append(item)
                    report["counts"]["skipped"] += 1
                    print("SKIP already_applied", page_title[:80], flush=True)
                    continue

                reason = skip_reason(page_title, company, location, body[:1500])
                if reason:
                    item["reason"] = reason
                    report["skipped"].append(item)
                    report["counts"]["skipped"] += 1
                    continue

                print(
                    f"JOB seen={report['counts']['seen']} title={page_title[:80]!r}",
                    flush=True,
                )
                prepare_resume_for_job(item, body)
                job_deadline = time.time() + int(
                    os.environ.get("INDEED_JOB_TIMEOUT_SEC", "240")
                )

                try:
                    # Prefer Easy Apply ("Apply with Indeed" is the current IN CTA).
                    applied = False
                    for sel in (
                        "button.indeed-apply-button",
                        "#indeedApplyButton",
                        "[data-indeed-apply-button]",
                        "button.ia-IndeedApplyButton",
                        "button:contains('Apply with Indeed')",
                        "button:contains('Indeed Apply')",
                        "button:contains('Easily apply')",
                        "button:contains('Easy apply')",
                        "button:contains('Apply now')",
                        "//button[contains(., 'Apply with Indeed') or contains(., 'Indeed Apply') or contains(., 'Easily apply') or contains(., 'Easy apply') or contains(., 'Apply now')]",
                        "//a[contains(., 'Apply with Indeed') or contains(., 'Indeed Apply') or contains(., 'Easily apply') or contains(., 'Easy apply') or contains(., 'Apply now')]",
                        "//button[contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply now') or contains(translate(@aria-label,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'apply with indeed')]",
                    ):
                        try:
                            if sb.is_element_visible(sel, timeout=2):
                                sb.click(sel)
                                applied = True
                                break
                        except Exception:
                            continue
                    if not applied:
                        # JS fallback — SeleniumBase text selectors miss some CTA variants.
                        try:
                            clicked = sb.execute_script(
                                """
                                const cands=[...document.querySelectorAll(
                                  'button, a, [role=button], [data-indeed-apply-button], .indeed-apply-button, .ia-IndeedApplyButton'
                                )];
                                const textOf = (e) => ((e.innerText||'') + ' ' + (e.getAttribute('aria-label')||'') + ' ' + (e.getAttribute('data-tn-element')||'')).trim();
                                const el=cands.find(e => {
                                  const s=textOf(e);
                                  if (/apply with indeed|indeed apply|easily apply|easy apply|^apply now$/i.test(s)
                                      && !/company site|company website/i.test(s)) return true;
                                  if (e.id === 'indeedApplyButton' || e.classList?.contains('indeed-apply-button')) return true;
                                  if (e.hasAttribute('data-indeed-apply-button')) return true;
                                  return false;
                                });
                                if(!el) return null;
                                el.click();
                                return textOf(el).slice(0,80);
                                """
                            )
                            if clicked:
                                applied = True
                                print("JS_APPLY_CLICK", clicked, flush=True)
                        except Exception:
                            pass
                    if not applied:
                        # Applied badge replaces Easy Apply on already-submitted jobs.
                        try:
                            badge = sb.execute_script(
                                """
                                const els=[...document.querySelectorAll('button, a, [role=button], span')];
                                const el=els.find(e => {
                                  const s=((e.innerText||'')+' '+(e.getAttribute('aria-label')||'')).trim();
                                  return /^applied$/i.test(s) || /^applied on /i.test(s);
                                });
                                return el ? ((el.innerText||el.getAttribute('aria-label')||'applied').slice(0,80)) : null;
                                """
                            )
                            if badge:
                                item["reason"] = "already_applied"
                                report["skipped"].append(item)
                                report["counts"]["skipped"] += 1
                                print("SKIP already_applied", page_title[:80], flush=True)
                                continue
                        except Exception:
                            pass
                        # Company site path — may still upload tailored resume via ATS helper.
                        handles_before = []
                        try:
                            handles_before = list(sb.driver.window_handles)
                        except Exception:
                            handles_before = []
                        for sel in (
                            "button:contains('Apply on company site')",
                            "a:contains('Apply on company site')",
                            "button:contains('Apply on company website')",
                            "a:contains('Apply on company website')",
                            "button:contains('Apply on the company site')",
                            "a:contains('Apply on the company site')",
                            "//a[contains(., 'Apply on company')]",
                            "//button[contains(., 'Apply on company')]",
                            "//a[contains(., 'Company site') or contains(., 'company website')]",
                        ):
                            try:
                                if sb.is_element_visible(sel, timeout=2):
                                    sb.click(sel)
                                    applied = True
                                    print("EXTERNAL click", page_title[:80], flush=True)
                                    break
                            except Exception:
                                continue
                        if not applied:
                            try:
                                clicked = sb.execute_script(
                                    """
                                    const cands=[...document.querySelectorAll('button, a, [role=button]')];
                                    const el=cands.find(e => /apply on company|company website|company site/i.test(
                                      ((e.innerText||'') + ' ' + (e.getAttribute('aria-label')||'')).trim()
                                    ));
                                    if(!el) return null;
                                    el.click();
                                    return (el.innerText||el.getAttribute('aria-label')||'').slice(0,80);
                                    """
                                )
                                if clicked:
                                    applied = True
                                    print("EXTERNAL click", clicked, page_title[:80], flush=True)
                            except Exception:
                                pass
                        if not applied:
                            item["reason"] = "no_apply_button"
                            report["skipped"].append(item)
                            report["counts"]["skipped"] += 1
                            continue
                        finish_company_site(sb, item, report, handles_before=handles_before)
                        applied = True
                        continue

                    # Wait for SmartApply module — do not treat job-view "Continue" as ready.
                    if not wait_for_smartapply_surface(sb, seconds=14):
                        # One more Apply-with-Indeed click, then wait again.
                        try:
                            sb.execute_script(
                                """
                                const cands=[...document.querySelectorAll(
                                  'button, a, [role=button], [data-indeed-apply-button]'
                                )];
                                const textOf = (e) => ((e.innerText||'') + ' ' + (e.getAttribute('aria-label')||'')).trim();
                                const el=cands.find(e => /apply with indeed|indeed apply|easily apply|easy apply/i.test(textOf(e))
                                  && !/company site|company website/i.test(textOf(e)));
                                if (el) el.click();
                                return el ? textOf(el).slice(0,80) : null;
                                """
                            )
                        except Exception:
                            pass
                        wait_for_smartapply_surface(sb, seconds=10)
                    result = easy_apply_flow(sb, deadline=job_deadline)
                    item["path"] = "easy_apply"
                    item["result"] = result
                    if result == "submitted":
                        report["applied"].append(item)
                        report["counts"]["applied"] += 1
                        print("APPLIED", page_title[:80], flush=True)
                    elif result == "external":
                        # Easy Apply flipped to company-site — complete ATS, do not credit a click.
                        handles_now = []
                        try:
                            handles_now = list(sb.driver.window_handles)
                        except Exception:
                            handles_now = []
                        finish_company_site(sb, item, report, handles_before=handles_now[:-1] if handles_now else [])
                    elif result == "already_applied":
                        item["reason"] = "already_applied"
                        report["skipped"].append(item)
                        report["counts"]["skipped"] += 1
                        print("SKIP already_applied", page_title[:80], flush=True)
                    elif result == "login_required":
                        item["reason"] = "indeed_login_required"
                        try:
                            item["lastUrl"] = (sb.get_current_url() or "")[:200]
                            item["sample"] = (sb.get_text("body") or "")[:350].replace("\n", " | ")
                        except Exception:
                            pass
                        report["blocked"].append(item)
                        report["counts"]["blocked"] += 1
                        print("BLOCKED login_required", page_title[:80], flush=True)
                    elif result == "recaptcha":
                        item["reason"] = "easy_apply_recaptcha"
                        report["blocked"].append(item)
                        report["counts"]["blocked"] += 1
                        print("RECAPTCHA", page_title[:80], flush=True)
                    else:
                        item["reason"] = "easy_apply_incomplete"
                        try:
                            item["lastUrl"] = (sb.get_current_url() or "")[:200]
                            item["sample"] = (sb.get_text("body") or "")[:350].replace("\n", " | ")
                        except Exception:
                            pass
                        # Reclassify SmartApply duplicate / auth walls that slipped past early checks.
                        sample_l = (item.get("sample") or "").lower()
                        if already_applied(sample_l, item.get("lastUrl") or ""):
                            item["reason"] = "already_applied"
                            report["skipped"].append(item)
                            report["counts"]["skipped"] += 1
                            print("SKIP already_applied", page_title[:80], flush=True)
                        elif looks_login_wall(sample_l, item.get("lastUrl") or ""):
                            item["reason"] = "indeed_login_required"
                            report["blocked"].append(item)
                            report["counts"]["blocked"] += 1
                            print("BLOCKED login_required", page_title[:80], flush=True)
                        else:
                            report["rejected"].append(item)
                            report["counts"]["rejected"] += 1
                            print("INCOMPLETE", page_title[:80], flush=True)
                            if item.get("lastUrl"):
                                print(f"  incomplete_url={item['lastUrl']}", flush=True)

                    # Close Easy Apply modal / extra windows so the next job is clean.
                    try:
                        sb.press_keys("body", "\ue00c")  # ESC
                    except Exception:
                        pass
                    try:
                        handles = sb.driver.window_handles
                        if len(handles) > 1:
                            current = sb.driver.current_window_handle
                            for h in handles:
                                if h != current:
                                    sb.driver.switch_to.window(h)
                                    sb.driver.close()
                            sb.driver.switch_to.window(sb.driver.window_handles[0])
                    except Exception:
                        pass
                    time.sleep(1)
                finally:
                    clear_job_resume()
                continue

    report["finishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    applied_n = report["counts"]["applied"] + report["counts"]["external"]
    # Success = at least one real apply; residual reCAPTCHA on later jobs is ok.
    report["ok"] = applied_n > 0
    report["date"] = report["finishedAt"][:10]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    # Normalize for notification job
    source = report.get("source") or (
        "home-local" if os.environ.get("INDEED_SKIP_WARP") == "1" else "cloud-warp-uc"
    )
    subprocess.run(
        [
            "node",
            str(ROOT / "tools/indeed/daily_run_report.js"),
            "write",
            "--in",
            str(OUT),
            "--source",
            source,
            "--out",
            str(OUT),
        ],
        check=False,
    )
    _emit(report)
    if applied_n > 0:
        return 0
    if report["counts"]["blocked"] > 0:
        return 5
    return 1


if __name__ == "__main__":
    sys.exit(main())
