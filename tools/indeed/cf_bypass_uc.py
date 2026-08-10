#!/usr/bin/env python3
"""Clear Indeed Cloudflare Turnstile on cloud VMs via WARP SOCKS + SeleniumBase UC.

Prereq:
  bash scripts/start-warp-proxy.sh   # SOCKS5 on 127.0.0.1:40000

What works (empirically):
  Cloudflare WARP proxy mode + SeleniumBase UC Chrome + uc_gui_click_captcha()
  on "Additional Verification Required". Plain Chrome clicks / cloudscraper /
  WARP alone do not clear Turnstile.

Exit codes:
  0 — page looks clear (not blocked / not stuck on verification)
  5 — still blocked after attempts
  2 — misconfiguration (WARP proxy down, missing deps)
"""
from __future__ import annotations

import argparse
import contextlib
import json
import os
import socket
import sys
import time
from pathlib import Path


@contextlib.contextmanager
def _stdout_to_stderr():
    """Keep final report JSON clean: SeleniumBase may print driver downloads to stdout."""
    old = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = old

DEFAULT_URL = os.environ.get("INDEED_PREFLIGHT_URL", "https://in.indeed.com/")
DEFAULT_PROXY = os.environ.get("INDEED_HTTP_PROXY") or os.environ.get(
    "WARP_SOCKS_PROXY", "socks5://127.0.0.1:40000"
)
OUT = Path(
    os.environ.get(
        "INDEED_CF_BYPASS_REPORT", "/opt/cursor/artifacts/indeed-cf-bypass.json"
    )
)
SCREENSHOT = Path(
    os.environ.get(
        "INDEED_CF_BYPASS_SHOT", "/opt/cursor/artifacts/indeed-cf-bypass.png"
    )
)


def proxy_host_port(proxy: str) -> tuple[str, int]:
    # socks5://127.0.0.1:40000 or socks5h://...
    p = proxy.strip()
    for prefix in ("socks5h://", "socks5://", "http://", "https://"):
        if p.startswith(prefix):
            p = p[len(prefix) :]
            break
    host, _, port_s = p.partition(":")
    return host or "127.0.0.1", int(port_s or "40000")


def socks_up(proxy: str) -> bool:
    host, port = proxy_host_port(proxy)
    s = socket.socket()
    s.settimeout(2)
    try:
        s.connect((host, port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def blocked_blob(title: str, text: str, url: str) -> bool:
    blob = f"{title}\n{text}\n{url}".lower()
    hard = (
        "request blocked",
        "you have been blocked",
        "additional verification required",
        "security check",
        "just a moment",
        "cf-ray",
        "blocked - indeed",
    )
    return any(x in blob for x in hard)


def looks_healthy(title: str, text: str, url: str) -> bool:
    blob = f"{title}\n{text}".lower()
    if blocked_blob(title, text, url):
        return False
    good = (
        "find jobs",
        "what do you want to do?",
        "welcome",
        "indeed for employers",
        "sign in",
        "job feed",
        "recommended jobs",
    )
    return any(x in blob for x in good) or ("indeed.com" in url and len(text) > 400)


def sb_proxy_arg(proxy: str) -> str:
    """SeleniumBase wants host:port or user:pass@host:port; socks via socks5://."""
    p = proxy.strip()
    if p.startswith("socks5h://"):
        return "socks5://" + p[len("socks5h://") :]
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--proxy", default=DEFAULT_PROXY)
    ap.add_argument(
        "--user-data-dir",
        default=os.environ.get(
            "INDEED_UC_PROFILE", "/tmp/cursor/indeed-uc-hybrid"
        ),
    )
    ap.add_argument(
        "--seed-profile",
        default=os.environ.get(
            "INDEED_SEED_PROFILE", "/home/ubuntu/chrome-indeed-profile"
        ),
    )
    ap.add_argument("--attempts", type=int, default=3)
    ap.add_argument(
        "--prepare-hybrid",
        action="store_true",
        default=os.environ.get("INDEED_PREPARE_HYBRID", "1") != "0",
        help="Copy auth cookies from seed profile and strip burned CF cookies",
    )
    args = ap.parse_args()

    report: dict = {
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url": args.url,
        "proxy": args.proxy,
        "userDataDir": args.user_data_dir,
        "ok": False,
        "attempts": [],
    }

    def emit(payload: dict) -> None:
        # Always write clean JSON to the real stdout (SB may have redirected sys.stdout).
        print(json.dumps(payload, indent=2), file=sys.__stdout__, flush=True)

    if not socks_up(args.proxy):
        report["error"] = "warp_socks_down"
        report["hint"] = "Run: bash scripts/start-warp-proxy.sh"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2))
        emit(report)
        return 2

    try:
        from seleniumbase import SB
    except ImportError:
        report["error"] = "seleniumbase_missing"
        report["hint"] = "pip install --user seleniumbase PyAutoGUI"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2))
        emit(report)
        return 2

    os.environ.setdefault("DISPLAY", ":1")
    proxy = sb_proxy_arg(args.proxy)
    user_data = args.user_data_dir
    if args.prepare_hybrid:
        prep = Path(__file__).with_name("prepare_uc_profile.py")
        import subprocess

        res = subprocess.run(
            [
                "python3",
                str(prep),
                "--src",
                args.seed_profile,
                "--dst",
                user_data,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        try:
            report["profilePrep"] = json.loads(res.stdout or "{}")
        except Exception:
            report["profilePrep"] = {
                "error": (res.stderr or res.stdout or "")[:400]
            }
    Path(user_data).mkdir(parents=True, exist_ok=True)

    last_title = ""
    last_url = ""
    last_text = ""

    # headed UC on existing X display (PyAutoGUI needs a real X server).
    # Do NOT use headless=True — Turnstile GUI click will not work.
    # Redirect SB/driver chatter to stderr so Node preflight can JSON.parse stdout.
    with _stdout_to_stderr():
        with SB(
            uc=True,
            headed=True,
            proxy=proxy,
            user_data_dir=user_data,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage",
        ) as sb:
            for i in range(1, args.attempts + 1):
                attempt: dict = {"n": i}
                try:
                    sb.uc_open_with_reconnect(args.url, 5)
                    time.sleep(2)
                    title = sb.get_title() or ""
                    url = sb.get_current_url() or ""
                    try:
                        text = sb.get_text("body") or ""
                    except Exception:
                        text = sb.get_page_source()[:4000]
                    attempt.update(
                        {"title": title, "url": url, "textSample": text[:500]}
                    )
                    last_title, last_url, last_text = title, url, text

                    if looks_healthy(title, text, url):
                        attempt["result"] = "clear"
                        report["attempts"].append(attempt)
                        report["ok"] = True
                        break

                    if blocked_blob(title, text, url):
                        attempt["result"] = "challenge"
                        # Primary path that clears Turnstile on this environment.
                        try:
                            sb.uc_gui_click_captcha()
                            attempt["captchaClick"] = "uc_gui_click_captcha"
                        except Exception as e:
                            attempt["captchaClickError"] = str(e)[:300]
                            try:
                                sb.uc_gui_handle_captcha()
                                attempt["captchaClick"] = "uc_gui_handle_captcha"
                            except Exception as e2:
                                attempt["captchaClickError2"] = str(e2)[:300]
                        time.sleep(4)
                        sb.uc_open_with_reconnect(args.url, 4)
                        time.sleep(2)
                        title = sb.get_title() or ""
                        url = sb.get_current_url() or ""
                        try:
                            text = sb.get_text("body") or ""
                        except Exception:
                            text = sb.get_page_source()[:4000]
                        attempt["afterTitle"] = title
                        attempt["afterUrl"] = url
                        attempt["afterTextSample"] = text[:500]
                        last_title, last_url, last_text = title, url, text
                        if looks_healthy(title, text, url):
                            attempt["result"] = "cleared"
                            report["attempts"].append(attempt)
                            report["ok"] = True
                            break
                    else:
                        attempt["result"] = "unknown"
                    report["attempts"].append(attempt)
                except Exception as e:
                    attempt["error"] = str(e)[:500]
                    report["attempts"].append(attempt)

            try:
                SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
                sb.save_screenshot(str(SCREENSHOT))
                report["screenshot"] = str(SCREENSHOT)
            except Exception as e:
                report["screenshotError"] = str(e)[:200]

    report["finishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["finalTitle"] = last_title
    report["finalUrl"] = last_url
    report["finalTextSample"] = last_text[:800]
    report["ok"] = bool(report["ok"] and looks_healthy(last_title, last_text, last_url))
    if not report["ok"]:
        report["reason"] = "indeed_cloudflare_still_blocked"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    emit(report)
    return 0 if report["ok"] else 5


if __name__ == "__main__":
    sys.exit(main())
