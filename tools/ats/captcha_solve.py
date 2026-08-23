#!/usr/bin/env python3
"""hCaptcha helpers for guest ATS (iCIMS, reCAPTCHA widgets).

Free path: headed Chrome waits for the owner to click
(`ATS_CAPTCHA_WAIT_SEC` / `HOME_LOCAL=1` / `CHROME_HEADLESS=0`).
Paid path (optional): CapSolver / 2Captcha token inject via
`CAPSOLVER_API_KEY` or `TWOCAPTCHA_API_KEY`.

DataDome / Cloudflare Turnstile sliders are not token widgets and stay
owner/residential.
"""

from __future__ import annotations

import json
import os
import re
import signal
import time
import urllib.error
import urllib.parse
import urllib.request

SITEKEY_RE = re.compile(
    r'data-sitekey=["\']([A-Za-z0-9_-]{8,})["\']|'
    r"[?&]sitekey=([A-Za-z0-9_-]{8,})|"
    r"""sitekey["']?\s*[:=]\s*["']([A-Za-z0-9_-]{8,})["']""",
    re.I,
)


def captcha_solver_configured() -> bool:
    return bool(capsolver_key() or twocaptcha_key())


def capsolver_key() -> str:
    return (os.environ.get("CAPSOLVER_API_KEY") or "").strip()


def twocaptcha_key() -> str:
    return (
        os.environ.get("TWOCAPTCHA_API_KEY")
        or os.environ.get("TWO_CAPTCHA_API_KEY")
        or ""
    ).strip()


def extract_sitekey_from_text(blob: str) -> str:
    m = SITEKEY_RE.search(blob or "")
    if not m:
        return ""
    return next((g for g in m.groups() if g), "") or ""


def extract_hcaptcha_sitekey(page) -> str:
    """Read hCaptcha sitekey from frames / widget markup."""
    js = """() => {
      const keys = [];
      const push = (k) => { if (k && !keys.includes(k)) keys.push(k); };
      for (const el of document.querySelectorAll('[data-sitekey]')) push(el.getAttribute('data-sitekey'));
      for (const iframe of document.querySelectorAll('iframe[src*="hcaptcha"]')) {
        const src = iframe.getAttribute('src') || '';
        const m = src.match(/[?&]sitekey=([^&]+)/i);
        if (m) push(decodeURIComponent(m[1]));
      }
      return keys[0] || '';
    }"""
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    targets = frames or [page]
    for fr in targets:
        try:
            key = (fr.evaluate(js) or "").strip()
            if key:
                return key
        except Exception:
            continue
        try:
            html = fr.content()
        except Exception:
            html = ""
        key = extract_sitekey_from_text(html)
        if key:
            return key
    return ""


# Ad / challenge iframes: evaluate/inner_text on these wedges Playwright after a
# JS dialog protocol error and starves the 180s owner-captcha deadline.
_SKIP_POLL_FRAME_RE = re.compile(
    r"hcaptcha\.com|newassets\.hcaptcha|google\.com/recaptcha|"
    r"doubleclick\.net|adsrvr\.org|casalemedia\.com|"
    r"linkedin\.com/talentwidgets|linkedin\.com/pages-extensions|"
    r"challenges\.cloudflare\.com|^blob:|^about:",
    re.I,
)
_MAX_CAPTCHA_POLL_FRAMES = 5


def _captcha_poll_frames(page) -> list:
    """Parent page first; skip captcha/ad iframes (evaluate hangs). Cap count."""
    targets: list = [page]
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames:
        if fr is page or fr in targets:
            continue
        try:
            u = (getattr(fr, "url", None) or "").lower()
        except Exception:
            u = ""
        if _SKIP_POLL_FRAME_RE.search(u):
            continue
        targets.append(fr)
        if len(targets) >= _MAX_CAPTCHA_POLL_FRAMES:
            break
    return targets


class _HangTimeout(Exception):
    """Raised when SIGALRM fires around a wedged Playwright call."""


def _call_with_hang_timeout(fn, timeout_s: float, default=None):
    """Run fn on the current thread; return (value, hung).

    Playwright sync API is greenlet-bound — do NOT call it from another thread
    (that prints 'cannot switch to a different thread' forever). Use SIGALRM
    so a wedged inner_text/evaluate cannot starve the owner-captcha deadline.
    """
    if os.name == "nt":
        try:
            return fn(), False
        except Exception:
            return default, False

    def _on_alarm(_signum, _frame):
        raise _HangTimeout()

    prev = signal.getsignal(signal.SIGALRM)
    hung = False
    val = default
    try:
        signal.signal(signal.SIGALRM, _on_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(0.2, float(timeout_s)))
        try:
            val = fn()
        except _HangTimeout:
            hung = True
            val = default
        except Exception:
            val = default
    finally:
        try:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
        except Exception:
            pass
        try:
            signal.signal(signal.SIGALRM, prev)
        except Exception:
            pass
    return val, hung


def hcaptcha_token_present(page) -> bool:
    js = """() => {
      const sels = [
        'textarea[name="h-captcha-response"]',
        'textarea[name="g-recaptcha-response"]',
        '[name="h-captcha-response"]',
        '[name="g-recaptcha-response"]',
      ];
      for (const sel of sels) {
        const el = document.querySelector(sel);
        if (el && (el.value || '').length > 20) return true;
      }
      return false;
    }"""
    # Polls must not inherit a 45s page default — one stuck frame starved careers.
    try:
        page.set_default_timeout(2500)
    except Exception:
        pass
    try:
        for fr in _captcha_poll_frames(page):
            try:
                if fr.evaluate(js):
                    return True
            except Exception:
                continue
    finally:
        try:
            page.set_default_timeout(45000)
        except Exception:
            pass
    return False


def inject_hcaptcha_token(page, token: str) -> bool:
    """Write the solver token into hCaptcha response fields and fire callbacks."""
    if not token or len(token) < 20:
        return False
    js = """(token) => {
      const names = ['h-captcha-response', 'g-recaptcha-response'];
      for (const name of names) {
        let el = document.querySelector('[name="' + name + '"]');
        if (!el) {
          el = document.createElement('textarea');
          el.name = name;
          el.id = name;
          el.style.display = 'none';
          document.body.appendChild(el);
        }
        el.value = token;
        el.innerHTML = token;
        el.dispatchEvent(new Event('input', { bubbles: true }));
        el.dispatchEvent(new Event('change', { bubbles: true }));
      }
      try {
        if (window.hcaptcha && typeof window.hcaptcha.getResponse === 'function') {
          // Best-effort: invoke registered callbacks.
        }
        const cfg = window.hcaptcha || {};
        if (cfg && cfg.listeners) { /* no-op */ }
      } catch (e) {}
      try {
        document.querySelectorAll('[data-callback]').forEach((el) => {
          const name = el.getAttribute('data-callback');
          if (name && typeof window[name] === 'function') window[name](token);
        });
      } catch (e) {}
      return true;
    }"""
    ok = False
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames or [page]:
        try:
            fr.evaluate(js, token)
            ok = True
        except Exception:
            continue
    return ok or hcaptcha_token_present(page)


def _http_json(url: str, *, data: dict | None = None, params: dict | None = None, timeout: int = 60) -> dict:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    body = None
    headers = {"User-Agent": "rafi-job-apply/1.0"}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {"raw": (raw or "")[:300]}


def solve_hcaptcha_token(pageurl: str, sitekey: str, timeout_s: int = 90) -> str:
    """Return an hCaptcha response token, or empty string."""
    if not sitekey or not pageurl:
        return ""
    token = ""
    key = capsolver_key()
    if key:
        try:
            create = _http_json(
                "https://api.capsolver.com/createTask",
                data={
                    "clientKey": key,
                    "task": {
                        "type": "HCaptchaTaskProxyLess",
                        "websiteURL": pageurl,
                        "websiteKey": sitekey,
                    },
                },
            )
            task_id = create.get("taskId")
            if task_id:
                deadline = time.time() + timeout_s
                while time.time() < deadline:
                    time.sleep(3)
                    res = _http_json(
                        "https://api.capsolver.com/getTaskResult",
                        data={"clientKey": key, "taskId": task_id},
                    )
                    if res.get("status") == "ready":
                        sol = res.get("solution") or {}
                        token = (sol.get("gRecaptchaResponse") or sol.get("token") or "").strip()
                        break
                    if res.get("status") == "failed" or res.get("errorId"):
                        print(f"hcaptcha_capsolver_fail={str(res)[:180]}", flush=True)
                        break
            else:
                print(f"hcaptcha_capsolver_create={str(create)[:180]}", flush=True)
        except Exception as exc:
            print(f"hcaptcha_capsolver={exc!s}"[:200], flush=True)
    if token:
        return token
    key2 = twocaptcha_key()
    if not key2:
        return ""
    try:
        create = _http_json(
            "https://2captcha.com/in.php",
            params={
                "key": key2,
                "method": "hcaptcha",
                "sitekey": sitekey,
                "pageurl": pageurl,
                "json": 1,
            },
        )
        if create.get("status") != 1:
            print(f"hcaptcha_2c_create={str(create)[:180]}", flush=True)
            return ""
        req_id = create.get("request")
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            time.sleep(5)
            res = _http_json(
                "https://2captcha.com/res.php",
                params={"key": key2, "action": "get", "id": req_id, "json": 1},
            )
            if res.get("status") == 1:
                return (res.get("request") or "").strip()
            if res.get("request") not in ("CAPCHA_NOT_READY", "CAPTCHA_NOT_READY"):
                print(f"hcaptcha_2c_fail={str(res)[:180]}", flush=True)
                break
    except Exception as exc:
        print(f"hcaptcha_2captcha={exc!s}"[:200], flush=True)
    return ""


def try_click_hcaptcha_checkbox(page) -> bool:
    """Some iCIMS tenants pass a simple checkbox without a challenge image."""
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames:
        u = (getattr(fr, "url", "") or "").lower()
        if "hcaptcha.com" not in u:
            continue
        for sel in ("#checkbox", "[role=checkbox]", "#anchor-state"):
            try:
                box = fr.locator(sel).first
                if box.count() and box.is_visible():
                    box.click(timeout=2500)
                    time.sleep(1.2)
                    return True
            except Exception:
                continue
    return False


def owner_captcha_wait_sec() -> int:
    """Seconds to wait for a human to click hCaptcha in headed Chrome.

    Free path: no CapSolver key. Cloud headless defaults to 0. Home / headed
    Chrome defaults to 180 unless ATS_CAPTCHA_WAIT_SEC is set.
    Owner-asleep / overnight defaults to a short park (~12s).
    """
    raw = (os.environ.get("ATS_CAPTCHA_WAIT_SEC") or "").strip()
    if raw:
        try:
            return max(0, int(raw))
        except ValueError:
            return 0
    try:
        from tools.ats.complete import owner_asleep

        if owner_asleep():
            return 12
    except Exception:
        if (os.environ.get("HITECHCITY_OWNER_ASLEEP") or "").strip().lower() in (
            "1",
            "true",
            "yes",
        ):
            return 12
    if (os.environ.get("HOME_LOCAL") or "").strip().lower() in ("1", "true", "yes"):
        return 180
    if (os.environ.get("CHROME_HEADLESS") or "1").strip() in ("0", "false", "no"):
        return 180
    return 0


def _page_url(page) -> str:
    try:
        return getattr(page, "url", "") or ""
    except Exception:
        return ""


def _safe_body_snip(page, limit: int = 2500) -> str:
    """Parent-page body only — extra frames wedge Playwright after dialog errors."""
    try:
        page.set_default_timeout(1200)
    except Exception:
        pass
    try:
        return (page.locator("body").inner_text(timeout=800) or "")[:limit]
    except Exception:
        return ""
    finally:
        try:
            page.set_default_timeout(45000)
        except Exception:
            pass


def owner_hcaptcha_cleared(page, *, start_url: str = "") -> str | None:
    """Return a short reason when the owner solve is done — do not wait for token alone.

    After a human click, iCIMS/Workday often navigate or show Log Out / confirmation
    without leaving a readable ``h-captcha-response`` in a same-origin frame. Treating
    only the token as success burns the full ATS_CAPTCHA_WAIT_SEC.
    """
    if hcaptcha_token_present(page):
        return "token"
    url = _page_url(page)
    url_l = url.lower()
    start_l = (start_url or "").lower()
    body = _safe_body_snip(page, 3000)
    if re.search(
        r"application (has been )?submitted|thank you for (your )?appl|"
        r"we (have )?received your (application|appl)|application received|"
        r"successfully applied|your application was sent|application complete|"
        r"application was submitted successfully|"
        r"you are currently submitted to this job|"
        r"you have already applied",
        body,
        re.I,
    ):
        return "submitted_or_already"
    if re.search(r"\bLog Out\b|Dashboard\s*\|", body, re.I):
        return "icims_logged_in"
    # Left the GDPR /login wall (parent or iframe URL).
    if "icims.com" in url_l and "/login" not in url_l:
        if "icims.com" in start_l and "/login" in start_l:
            return "left_icims_login"
        if re.search(r"mode=submit_apply|mode=apply|/questions|/eeo|/form", url_l, re.I):
            return "icims_apply_flow"
    try:
        for fr in getattr(page, "frames", []) or []:
            fu = (getattr(fr, "url", None) or "").lower()
            if "icims.com" in fu and "/login" in fu:
                break
        else:
            if "icims.com" in start_l and "/login" in start_l and "icims.com" in url_l:
                # Start was login; no login iframe remains.
                if not re.search(r"icims\.com/.+/login", url_l, re.I):
                    return "icims_login_iframe_gone"
    except Exception:
        pass
    # Guest ATS form appeared after the wall (resume / name fields).
    try:
        page.set_default_timeout(1200)
        has_file = page.locator("input[type='file']").count() > 0
        has_name = page.locator(
            "[data-automation-id='legalNameSection'], [data-automation-id='formField-name'], "
            "input[name*='first' i], input[id*='firstName' i]"
        ).count() > 0
    except Exception:
        has_file = False
        has_name = False
    finally:
        try:
            page.set_default_timeout(45000)
        except Exception:
            pass
    if (has_file or has_name) and not re.search(
        r"verify you are human|press and hold|i'?m not a robot", body, re.I
    ):
        # Only count as cleared if we are no longer on a bare login URL.
        if "/login" not in url_l or has_file:
            return "form_ready"
    # Navigated off the original challenge URL entirely — only if start looked like a wall.
    # Oracle Cloud / multi-step apply changes path without a captcha; that must NOT clear.
    start_looks_wall = bool(
        re.search(r"/login|captcha|challenge|hcaptcha|checkpoint", start_l)
        or re.search(r"icims\.com/.+/login", start_l)
    )
    if (
        start_looks_wall
        and start_l
        and url_l
        and url_l.split("?")[0] != start_l.split("?")[0]
    ):
        if "checkpoint" not in url_l and "challenge" not in url_l and "captcha" not in url_l:
            if re.search(
                r"myworkdayjobs|greenhouse|lever\.co|icims\.com|smartrecruiters",
                url_l,
            ):
                return "navigated_on"
    return None


def owner_focus_interval_sec() -> float:
    """How often to re-activate the captcha/ASK_OWNER tab while waiting.

    Parallel multi-tab careers steal focus on navigation; re-focus keeps the
    tab that needs the owner on top for every daily/cron headed run.
    """
    raw = (os.environ.get("ATS_OWNER_FOCUS_EVERY_SEC") or "2").strip()
    try:
        return min(10.0, max(0.5, float(raw)))
    except ValueError:
        return 2.0


def focus_page_for_owner(page, *, reason: str = "") -> bool:
    """Bring the page's Chrome tab to the front so the owner can click captcha/forms.

    Uses Playwright bring_to_front + CDP Page.bringToFront / Target.activateTarget
    so parallel workers cannot leave the owner staring at a random company tab.
    Safe no-op when CDP/session is unavailable (headless cloud).
    """
    ok = False
    try:
        page.bring_to_front()
        ok = True
    except Exception:
        pass
    try:
        page.evaluate("() => { try { window.focus(); } catch (e) {} }")
        ok = True
    except Exception:
        pass
    cdp = None
    try:
        context = getattr(page, "context", None)
        if context is not None and hasattr(context, "new_cdp_session"):
            cdp = context.new_cdp_session(page)
            try:
                cdp.send("Page.bringToFront")
                ok = True
            except Exception:
                pass
            try:
                info = cdp.send("Target.getTargetInfo") or {}
                tid = (info.get("targetInfo") or {}).get("targetId") or info.get("targetId")
                if tid:
                    cdp.send("Target.activateTarget", {"targetId": tid})
                    ok = True
            except Exception:
                pass
    except Exception:
        pass
    finally:
        if cdp is not None:
            try:
                cdp.detach()
            except Exception:
                pass
    if reason:
        worker = os.environ.get("HITECHCITY_PARALLEL_WORKER") or ""
        print(
            f"owner_focus={reason}"
            f"{' worker=' + worker if worker else ''}"
            f" ok={1 if ok else 0}",
            flush=True,
        )
    return ok


def wait_for_owner_hcaptcha(page) -> bool:
    """Pause so the owner can solve hCaptcha in the visible Chrome window.

    Polls frequently and resumes as soon as a token, login, confirmation, or
    post-captcha form is visible — not only when the full wait budget expires.
    Re-focuses this tab on a timer so every daily parallel run keeps the
    captcha tab selected until the owner solves it.
    """
    wait = owner_captcha_wait_sec()
    if wait <= 0:
        return False
    start_url = _page_url(page)
    focus_page_for_owner(page, reason="hcaptcha_start")
    worker = os.environ.get("HITECHCITY_PARALLEL_WORKER") or ""
    print(
        f"hcaptcha=wait_owner {wait}s — click the captcha in the focused Chrome tab "
        f"(no paid API key){' worker=' + worker if worker else ''}",
        flush=True,
    )
    deadline = time.time() + wait
    last_beat = 0.0
    last_focus = 0.0
    focus_every = owner_focus_interval_sec()
    poll = float(os.environ.get("ATS_CAPTCHA_POLL_SEC", "0.4") or "0.4")
    poll = min(1.0, max(0.2, poll))
    hung_polls = 0
    while time.time() < deadline:
        why, hung = _call_with_hang_timeout(
            lambda: owner_hcaptcha_cleared(page, start_url=start_url),
            3.0,
            default=None,
        )
        if hung:
            hung_polls += 1
            print(
                f"hcaptcha=poll_hung n={hung_polls} — Playwright inner_text/evaluate "
                f"exceeded 3s (dialog/CDP wedge)",
                flush=True,
            )
            if hung_polls >= 2:
                print("hcaptcha=owner_wait_abort_hung", flush=True)
                return False
        elif why:
            print(f"hcaptcha=owner_solved reason={why}", flush=True)
            return True
        now = time.time()
        if now - last_focus >= focus_every:
            _call_with_hang_timeout(
                lambda: focus_page_for_owner(page, reason="hcaptcha_hold"),
                2.0,
                default=False,
            )
            last_focus = now
        if now - last_beat >= 5.0:
            left = max(0, int(deadline - now))
            print(f"hcaptcha=waiting {left}s left — tab kept focused for you", flush=True)
            last_beat = now
        time.sleep(poll)
    # Final check — owner may have solved in the last poll window.
    why = owner_hcaptcha_cleared(page, start_url=start_url)
    if why:
        print(f"hcaptcha=owner_solved reason={why}", flush=True)
        return True
    print("hcaptcha=owner_wait_timeout", flush=True)
    return False


def try_clear_hcaptcha(page) -> bool:
    """Click checkbox, wait for owner (free), then CapSolver/2Captcha if keyed."""
    if hcaptcha_token_present(page):
        return True
    try_click_hcaptcha_checkbox(page)
    time.sleep(1.0)
    if hcaptcha_token_present(page):
        print("hcaptcha=checkbox_passed", flush=True)
        return True
    if wait_for_owner_hcaptcha(page):
        return True
    if not captcha_solver_configured():
        print("hcaptcha=no_solver_key", flush=True)
        return False
    sitekey = extract_hcaptcha_sitekey(page)
    try:
        pageurl = getattr(page, "url", "") or ""
    except Exception:
        pageurl = ""
    if not pageurl:
        try:
            for fr in getattr(page, "frames", []) or []:
                u = getattr(fr, "url", "") or ""
                if "icims.com" in u:
                    pageurl = u
                    break
        except Exception:
            pass
    if not sitekey:
        print("hcaptcha=no_sitekey", flush=True)
        return False
    print(f"hcaptcha_api=start sitekey={sitekey[:10]}…", flush=True)
    token = solve_hcaptcha_token(pageurl, sitekey)
    if not token:
        print("hcaptcha_api=no_token", flush=True)
        return False
    inject_hcaptcha_token(page, token)
    time.sleep(0.8)
    ok = hcaptcha_token_present(page)
    print(f"hcaptcha_api={'token_injected' if ok else 'inject_miss'}", flush=True)
    return ok
