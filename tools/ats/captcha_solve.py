#!/usr/bin/env python3
"""Optional CapSolver / 2Captcha helpers for guest ATS (iCIMS hCaptcha, reCAPTCHA).

Same secret contract as Indeed SmartApply (`CAPSOLVER_API_KEY` or
`TWOCAPTCHA_API_KEY`). Token CAPTCHAs can be completed; DataDome / Cloudflare
Turnstile sliders are not token widgets and stay owner/residential.
"""

from __future__ import annotations

import json
import os
import re
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
    try:
        frames = list(getattr(page, "frames", []) or [])
    except Exception:
        frames = []
    for fr in frames or [page]:
        try:
            if fr.evaluate(js):
                return True
        except Exception:
            continue
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


def try_clear_hcaptcha(page) -> bool:
    """Click checkbox, then CapSolver/2Captcha if a sitekey is present."""
    if hcaptcha_token_present(page):
        return True
    try_click_hcaptcha_checkbox(page)
    time.sleep(1.0)
    if hcaptcha_token_present(page):
        print("hcaptcha=checkbox_passed", flush=True)
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
