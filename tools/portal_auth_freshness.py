#!/usr/bin/env python3
"""Cross-portal auth freshness — cookie *names* can outlive real sessions.

Indeed Passport OauthExpires / bearer JWT exp, Foundit MSSOAT JWT exp, and
similar traps pass SQLite name checks while Sign In walls block applies.

Usage:
  python3 tools/portal_auth_freshness.py check indeed
  python3 tools/portal_auth_freshness.py check-all
  python3 tools/portal_auth_freshness.py check foundit --json

Exit 0 = fresh (or unknown/skip), 5 = expired/stale session, 2 = usage error.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PORTAL_PROFILES = {
    "linkedin": os.environ.get("LINKEDIN_CHROME_PROFILE", "/home/ubuntu/chrome-cdp-profile"),
    "hitechcity": os.environ.get(
        "HITECHCITY_CHROME_PROFILE",
        os.environ.get("LINKEDIN_CHROME_PROFILE", "/home/ubuntu/chrome-cdp-profile"),
    ),
    "naukri": os.environ.get("NAUKRI_CHROME_PROFILE", "/home/ubuntu/.naukri-chrome-profile"),
    "foundit": os.environ.get("FOUNDIT_CHROME_PROFILE", "/home/ubuntu/.config/chrome-foundit"),
    "cutshort": os.environ.get("CUTSHORT_CHROME_PROFILE", "/home/ubuntu/chrome-cutshort-profile"),
    "instahyre": os.environ.get(
        "INSTAHYRE_CHROME_PROFILE", "/home/ubuntu/chrome-instahyre-profile"
    ),
    "indeed": os.environ.get("INDEED_CHROME_PROFILE", "/home/ubuntu/chrome-indeed-profile"),
    "hirist": os.environ.get("HIRIST_CHROME_PROFILE", "/home/ubuntu/chrome-hirist-profile"),
}

PORTAL_COOKIE_URLS = {
    "linkedin": ["https://www.linkedin.com/"],
    "hitechcity": ["https://www.linkedin.com/"],
    "naukri": ["https://www.naukri.com/"],
    "foundit": ["https://www.foundit.in/"],
    "cutshort": ["https://cutshort.io/"],
    "instahyre": ["https://www.instahyre.com/"],
    "indeed": ["https://secure.indeed.com/", "https://in.indeed.com/", "https://www.indeed.com/"],
    "hirist": ["https://www.hirist.tech/"],
}

AUTH_COOKIE_NAMES = {
    "linkedin": ["li_at"],
    "hitechcity": ["li_at"],
    "naukri": ["nauk_rt", "nauk_at"],
    "foundit": ["MSSOAT"],
    "cutshort": ["cutshort_authentication"],
    "instahyre": ["sessionid"],
    "indeed": [
        "__Secure-PassportAuthProxy-BearerToken",
        "__Secure-PassportAuthProxy-OauthExpires",
        "CTK",
        "PPID",
        "rememberMe",
    ],
    "hirist": ["hirist_seeker_enc", "token"],
}


def _jwt_payload(token: str) -> dict | None:
    if not token or token.count(".") < 2:
        return None
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return None


def jwt_exp(token: str) -> int | None:
    claims = _jwt_payload(token) or {}
    exp = claims.get("exp")
    return int(exp) if isinstance(exp, (int, float)) else None


def foundit_jwt_from_mssoat(raw: str) -> str | None:
    if not raw:
        return None
    val = raw
    try:
        from urllib.parse import unquote

        val = unquote(raw)
    except Exception:
        pass
    before = val.split("::", 1)[0] if "::" in val else val
    try:
        decoded = base64.b64decode(before).decode("utf-8", errors="ignore")
    except Exception:
        return None
    jwt = decoded.split("::", 1)[0] if "::" in decoded else decoded
    return jwt if jwt.count(".") == 2 else None


def chrome_bin() -> str | None:
    for cand in (
        os.environ.get("CHROME_BIN"),
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        if not cand:
            continue
        path = Path(cand) if "/" in cand or "\\" in cand else None
        if path and path.is_file():
            return str(path)
        import shutil

        found = shutil.which(cand)
        if found:
            return found
    return None


def read_cookies_via_chrome(
    profile: str,
    urls: list[str],
    *,
    port: int | None = None,
    timeout_s: float = 25.0,
) -> dict[str, str]:
    """Headless Chrome CDP dump of decrypted cookie values for urls."""
    chrome = chrome_bin()
    if not chrome or not Path(profile).is_dir():
        return {}
    port = int(port or os.environ.get("PORTAL_FRESHNESS_CDP_PORT", "9265"))
    work = Path(f"/tmp/cursor/portal-freshness-{os.getpid()}-{port}")
    if work.exists():
        import shutil

        shutil.rmtree(work, ignore_errors=True)
    import shutil

    shutil.copytree(profile, work, dirs_exist_ok=True)
    log = work / "chrome.log"
    proc = subprocess.Popen(
        [
            chrome,
            "--headless=new",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={work}",
            "--no-first-run",
            "--disable-gpu",
            "--no-sandbox",
            "about:blank",
        ],
        stdout=open(log, "w"),
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.time() + timeout_s
        ver = None
        while time.time() < deadline:
            try:
                ver = json.load(
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{port}/json/version", timeout=1
                    )
                )
                break
            except Exception:
                time.sleep(0.4)
        if not ver:
            return {}
        try:
            import websockets  # type: ignore
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "websockets", "-q"]
            )
            import websockets  # type: ignore

        async def _dump() -> dict[str, str]:
            import asyncio

            async with websockets.connect(
                ver["webSocketDebuggerUrl"], max_size=8_000_000
            ) as ws:
                n = 0

                async def call(method, params=None, session_id=None):
                    nonlocal n
                    n += 1
                    msg = {"id": n, "method": method}
                    if params is not None:
                        msg["params"] = params
                    if session_id:
                        msg["sessionId"] = session_id
                    await ws.send(json.dumps(msg))
                    while True:
                        resp = json.loads(await asyncio.wait_for(ws.recv(), timeout=20))
                        if resp.get("id") == n:
                            return resp

                r = await call("Target.createTarget", {"url": "about:blank"})
                r = await call(
                    "Target.attachToTarget",
                    {"targetId": r["result"]["targetId"], "flatten": True},
                )
                sid = r["result"]["sessionId"]
                await call("Network.enable", {}, sid)
                r = await call("Network.getCookies", {"urls": urls}, sid)
                out: dict[str, str] = {}
                for c in r.get("result", {}).get("cookies") or []:
                    name = str(c.get("name") or "")
                    if name:
                        out[name] = str(c.get("value") or "")
                return out

        import asyncio

        return asyncio.run(_dump())
    except Exception:
        return {}
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        try:
            import shutil

            shutil.rmtree(work, ignore_errors=True)
        except Exception:
            pass


def indeed_meta(cookies: dict[str, str], *, now: float | None = None) -> dict:
    now_ts = float(now if now is not None else time.time())
    exp_raw = (cookies.get("__Secure-PassportAuthProxy-OauthExpires") or "").strip()
    exp = int(exp_raw) if exp_raw.isdigit() else None
    bearer = cookies.get("__Secure-PassportAuthProxy-BearerToken") or ""
    jexp = jwt_exp(bearer)
    effective = jexp if jexp is not None else exp
    expired = bool(effective is not None and now_ts > effective)
    has_auth_name = bool(
        bearer
        or cookies.get("CTK")
        or cookies.get("PPID")
        or cookies.get("rememberMe")
    )
    return {
        "portal": "indeed",
        "ok": bool(has_auth_name and not expired),
        "expired": expired,
        "oauthExpires": exp,
        "jwtExp": jexp,
        "hasBearer": bool(bearer),
        "hasRefresh": bool(cookies.get("__Secure-PassportAuthProxy-RefreshToken")),
        "reason": (
            "indeed_session_expired"
            if expired
            else ("ok" if has_auth_name else "indeed_login_required")
        ),
    }


def foundit_meta(cookies: dict[str, str], *, now: float | None = None) -> dict:
    now_ts = float(now if now is not None else time.time())
    raw = cookies.get("MSSOAT") or ""
    jwt = foundit_jwt_from_mssoat(raw)
    jexp = jwt_exp(jwt) if jwt else None
    expired = bool(jexp is not None and now_ts > jexp)
    return {
        "portal": "foundit",
        "ok": bool(raw) and not expired,
        "expired": expired,
        "jwtExp": jexp,
        "hasMssoat": bool(raw),
        "reason": (
            "foundit_session_expired"
            if expired
            else ("ok" if raw else "foundit_login_required")
        ),
    }


def generic_meta(portal: str, cookies: dict[str, str]) -> dict:
    need = AUTH_COOKIE_NAMES.get(portal) or []
    present = [n for n in need if cookies.get(n)]
    # Any required cookie with non-empty *value* (not just name in SQLite).
    ok = bool(present)
    return {
        "portal": portal,
        "ok": ok,
        "expired": False,
        "present": present,
        "need": need,
        "reason": "ok" if ok else f"{portal}_login_required",
    }


def check_portal(portal: str, *, profile: str | None = None, skip_chrome: bool = False) -> dict:
    portal = (portal or "").strip().lower()
    if portal not in PORTAL_PROFILES:
        return {"ok": False, "portal": portal, "reason": "unknown_portal"}
    prof = profile or PORTAL_PROFILES[portal]
    out: dict = {
        "portal": portal,
        "profile": prof,
        "ok": False,
        "reason": "unchecked",
    }
    if not Path(prof).is_dir():
        out["reason"] = "missing_profile"
        return out

    cookies: dict[str, str] = {}
    if not skip_chrome:
        cookies = read_cookies_via_chrome(prof, PORTAL_COOKIE_URLS[portal])
        out["cookieNames"] = sorted(cookies.keys())
        out["chromeProbe"] = bool(cookies)

    if portal == "indeed":
        meta = indeed_meta(cookies)
    elif portal == "foundit":
        meta = foundit_meta(cookies)
    else:
        meta = generic_meta(portal, cookies)

    out.update(meta)
    if not cookies and not skip_chrome:
        # Chrome probe failed — do not false-fail name-based portals; Indeed/Foundit
        # expiry checks need values, so mark unverified.
        if portal in ("indeed", "foundit"):
            out["ok"] = False
            out["reason"] = f"{portal}_freshness_unverified"
            out["hint"] = "chrome cookie probe failed — re-run or headed login"
        else:
            out["ok"] = True
            out["reason"] = "freshness_skipped_no_chrome_cookies"
            out["unverified"] = True
    return out


def check_all(*, skip_chrome: bool = False) -> dict:
    portals = [
        "linkedin",
        "naukri",
        "foundit",
        "cutshort",
        "instahyre",
        "indeed",
        "hirist",
    ]
    results = {p: check_portal(p, skip_chrome=skip_chrome) for p in portals}
    ok = all(r.get("ok") for r in results.values())
    return {"ok": ok, "portals": results}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "check-all"])
    ap.add_argument("portal", nargs="?", default="")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--skip-chrome", action="store_true")
    args = ap.parse_args()
    if args.cmd == "check-all":
        report = check_all(skip_chrome=args.skip_chrome)
    else:
        if not args.portal:
            print("Usage: portal_auth_freshness.py check <portal>", file=sys.stderr)
            return 2
        report = check_portal(args.portal, skip_chrome=args.skip_chrome)
    print(json.dumps(report, indent=2))
    if not report.get("ok"):
        # Unverified soft — exit 4 so callers can distinguish from hard expired (5).
        if "unverified" in str(report.get("reason", "")):
            return 4
        if report.get("expired") or "expired" in str(report.get("reason", "")):
            return 5
        if report.get("reason") in ("unknown_portal", "missing_profile"):
            return 2
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
