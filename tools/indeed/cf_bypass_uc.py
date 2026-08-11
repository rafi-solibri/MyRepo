#!/usr/bin/env python3
"""Clear Indeed Cloudflare Turnstile on cloud VMs via WARP SOCKS + SeleniumBase UC.

Prereq:
  bash scripts/start-warp-proxy.sh   # SOCKS5 on 127.0.0.1:40000

What works (empirically):
  Cloudflare WARP proxy mode + SeleniumBase UC Chrome + Turnstile GUI click
  on "Additional Verification Required". Plain Chrome clicks / cloudscraper /
  WARP alone do not clear Turnstile.

Intermittent failures (widget visible but click does not clear) are handled by:
  - waiting for the Turnstile iframe/checkbox
  - multi-strategy clicks (uc_gui_click_cf / retry / handle / blind)
  - outer rounds that rotate the WARP exit IP + rebuild the hybrid profile

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
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.indeed.filelock_patch import (  # noqa: E402
    patch_filelock_singleton,
    rebind_seleniumbase_filelock,
)

# MUST run before SeleniumBase imports FileLock into its modules.
patch_filelock_singleton(ROOT)


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


def is_local_warp(proxy: str) -> bool:
    return bool(
        proxy
        and ("127.0.0.1:40000" in proxy or "localhost:40000" in proxy)
    )


def warp_exit_ip(proxy: str) -> str | None:
    """Best-effort WARP/public exit IP via Cloudflare trace through the SOCKS proxy."""
    try:
        px = proxy
        if px.startswith("socks5://"):
            px = "socks5h://" + px[len("socks5://") :]
        res = subprocess.run(
            [
                "curl",
                "-sS",
                "--max-time",
                "20",
                "-x",
                px,
                "https://www.cloudflare.com/cdn-cgi/trace",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        for line in (res.stdout or "").splitlines():
            if line.startswith("ip="):
                return line.split("=", 1)[1].strip() or None
    except Exception:
        return None
    return None


def rotate_warp(proxy: str) -> dict:
    """Disconnect/reconnect WARP (or re-register) to get a fresh exit IP."""
    info: dict = {"rotated": False, "beforeIp": warp_exit_ip(proxy)}
    if not is_local_warp(proxy):
        info["skipped"] = "external_proxy"
        return info
    script = ROOT / "scripts" / "start-warp-proxy.sh"
    if not script.exists():
        info["error"] = "start-warp-proxy.sh missing"
        return info
    # Prefer dedicated rotate command; fall back to stop+start.
    res = subprocess.run(
        ["bash", str(script), "rotate"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if res.returncode != 0:
        subprocess.run(
            ["bash", str(script), "stop"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        time.sleep(2)
        res = subprocess.run(
            ["bash", str(script), "start"],
            capture_output=True,
            text=True,
            timeout=120,
        )
    info["exitCode"] = res.returncode
    info["log"] = ((res.stdout or "") + "\n" + (res.stderr or ""))[-600:]
    # Give the new exit a moment to settle.
    time.sleep(3)
    info["afterIp"] = warp_exit_ip(proxy)
    info["rotated"] = res.returncode == 0 and socks_up(proxy)
    info["ipChanged"] = bool(
        info.get("beforeIp")
        and info.get("afterIp")
        and info["beforeIp"] != info["afterIp"]
    )
    return info


def prepare_hybrid(src: str, dst: str) -> dict:
    prep = Path(__file__).with_name("prepare_uc_profile.py")
    res = subprocess.run(
        ["python3", str(prep), "--src", src, "--dst", dst],
        capture_output=True,
        text=True,
        timeout=60,
    )
    try:
        return json.loads(res.stdout or "{}")
    except Exception:
        return {"error": (res.stderr or res.stdout or "")[:400]}


def page_snapshot(sb) -> tuple[str, str, str]:
    title = sb.get_title() or ""
    url = sb.get_current_url() or ""
    try:
        text = sb.get_text("body") or ""
    except Exception:
        try:
            text = sb.get_page_source()[:4000]
        except Exception:
            text = ""
    return title, url, text


def wait_for_turnstile(sb, timeout: float = 12.0) -> dict:
    """Wait until a Turnstile iframe/checkbox is present (or timeout)."""
    selectors = (
        "iframe[src*='turnstile']",
        "iframe[src*='challenges.cloudflare']",
        ".cf-turnstile iframe",
        ".cf-turnstile-wrapper iframe",
        ".cf-turnstile",
        ".cf-turnstile-wrapper",
        "[data-callback='onCaptchaSuccess']",
        "#challenge-stage",
        "iframe",
        "input[name*='cf-turnstile']",
    )
    deadline = time.time() + timeout
    found = None
    while time.time() < deadline:
        for sel in selectors:
            try:
                if sb.is_element_present(sel):
                    found = sel
                    break
            except Exception:
                continue
        if found:
            break
        time.sleep(0.35)
    # Extra settle time so the checkbox is interactable.
    if found:
        time.sleep(1.5)
    return {"found": found, "waited": True}


def focus_browser_window() -> None:
    """Bring the Indeed Chrome window to the front for PyAutoGUI clicks."""
    try:
        subprocess.run(
            [
                "xdotool",
                "search",
                "--name",
                "Indeed",
                "windowactivate",
                "--sync",
            ],
            timeout=5,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def manual_turnstile_click(sb) -> dict:
    """Coordinate click the Turnstile checkbox when SB helpers miss."""
    import pyautogui

    info: dict = {"strategy": "manual_xy"}
    focus_browser_window()
    rect = None
    try:
        rect = sb.execute_script(
            """
            const sels = [
              "iframe[src*='turnstile']",
              "iframe[src*='challenges.cloudflare']",
              ".cf-turnstile iframe",
              ".cf-turnstile-wrapper iframe",
              "iframe",
            ];
            let ifr = null;
            for (const s of sels) { ifr = document.querySelector(s); if (ifr) break; }
            if (!ifr) {
              const box = document.querySelector('.cf-turnstile, .cf-turnstile-wrapper, #challenge-stage');
              if (!box) return null;
              const r = box.getBoundingClientRect();
              return {
                x:r.x, y:r.y, w:r.width, h:r.height,
                wx: window.screenX, wy: window.screenY,
                ow: window.outerWidth, oh: window.outerHeight,
                iw: window.innerWidth, ih: window.innerHeight,
                kind: 'box'
              };
            }
            const r = ifr.getBoundingClientRect();
            return {
              x:r.x, y:r.y, w:r.width, h:r.height,
              wx: window.screenX, wy: window.screenY,
              ow: window.outerWidth, oh: window.outerHeight,
              iw: window.innerWidth, ih: window.innerHeight,
              kind: 'iframe'
            };
            """
        )
    except Exception as e:
        info["error"] = f"rect:{e}"[:200]
        return info
    info["rect"] = rect
    if not rect:
        return info
    chrome_h = max(0, float(rect["oh"]) - float(rect["ih"]))
    # Checkbox is near the left of the widget (~28–34 px).
    cx = int(float(rect["wx"]) + float(rect["x"]) + 30)
    cy = int(float(rect["wy"]) + chrome_h + float(rect["y"]) + 34)
    info["xy"] = [cx, cy]
    try:
        sb.disconnect()
    except Exception:
        pass
    try:
        pyautogui.moveTo(cx, cy, duration=0.25)
        pyautogui.click()
        time.sleep(0.4)
        pyautogui.click()
        info["ok"] = True
    except Exception as e:
        info["ok"] = False
        info["error"] = str(e)[:200]
    try:
        sb.reconnect(5)
    except Exception as e:
        info["reconnectError"] = str(e)[:200]
    return info


def try_clear_strategies(sb) -> list[dict]:
    """Run Turnstile clear strategies; stop early if page looks healthy.

    Requires filelock singleton patch so retry/handle nesting does not deadlock.
    """
    results: list[dict] = []

    def healthy() -> bool:
        t, u, x = page_snapshot(sb)
        return looks_healthy(t, x, u)

    strategies = [
        ("uc_gui_click_cf", lambda: sb.uc_gui_click_cf()),
        ("uc_gui_click_cf_retry", lambda: sb.uc_gui_click_cf(retry=True)),
        ("uc_gui_handle_cf", lambda: sb.uc_gui_handle_cf()),
        ("uc_gui_click_captcha", lambda: sb.uc_gui_click_captcha()),
        ("uc_gui_click_cf_blind", lambda: sb.uc_gui_click_cf(blind=True)),
        ("manual_xy", lambda: manual_turnstile_click(sb)),
    ]
    for name, fn in strategies:
        entry: dict = {"strategy": name}
        try:
            wait = wait_for_turnstile(sb, timeout=10.0)
            entry["turnstile"] = wait
            focus_browser_window()
            time.sleep(0.3)
            out = fn()
            if isinstance(out, dict):
                entry.update({k: v for k, v in out.items() if k != "strategy"})
            entry["ok"] = True
        except Exception as e:
            entry["ok"] = False
            entry["error"] = str(e)[:300]
        # Turnstile often needs several seconds after the GUI click.
        time.sleep(6)
        try:
            sb.uc_open_with_reconnect(sb.get_current_url() or DEFAULT_URL, 4)
        except Exception:
            try:
                sb.uc_open_with_reconnect(DEFAULT_URL, 4)
            except Exception as e2:
                entry["reloadError"] = str(e2)[:200]
        time.sleep(2)
        title, url, text = page_snapshot(sb)
        entry["afterTitle"] = title
        entry["afterUrl"] = url
        entry["afterTextSample"] = text[:400]
        entry["cleared"] = looks_healthy(title, text, url)
        results.append(entry)
        if entry["cleared"] or healthy():
            break
    return results


def run_browser_round(
    *,
    url: str,
    proxy: str,
    user_data: str,
    attempts: int,
) -> tuple[bool, list[dict], str, str, str]:
    """One SB session: open Indeed and try to clear CF up to `attempts` times."""
    from seleniumbase import SB

    last_title = last_url = last_text = ""
    attempts_log: list[dict] = []
    cleared = False

    with _stdout_to_stderr():
        with SB(
            uc=True,
            headed=True,
            proxy=sb_proxy_arg(proxy),
            user_data_dir=user_data,
            chromium_arg="--no-sandbox,--disable-dev-shm-usage",
        ) as sb:
            for i in range(1, attempts + 1):
                attempt: dict = {"n": i}
                try:
                    sb.uc_open_with_reconnect(url, 6)
                    time.sleep(2.5)
                    title, cur_url, text = page_snapshot(sb)
                    attempt.update(
                        {
                            "title": title,
                            "url": cur_url,
                            "textSample": text[:500],
                        }
                    )
                    last_title, last_url, last_text = title, cur_url, text

                    if looks_healthy(title, text, cur_url):
                        attempt["result"] = "clear"
                        attempts_log.append(attempt)
                        cleared = True
                        break

                    if blocked_blob(title, text, cur_url):
                        attempt["result"] = "challenge"
                        strategies = try_clear_strategies(sb)
                        attempt["strategies"] = strategies
                        title, cur_url, text = page_snapshot(sb)
                        attempt["afterTitle"] = title
                        attempt["afterUrl"] = cur_url
                        attempt["afterTextSample"] = text[:500]
                        last_title, last_url, last_text = title, cur_url, text
                        if looks_healthy(title, text, cur_url):
                            attempt["result"] = "cleared"
                            attempts_log.append(attempt)
                            cleared = True
                            break
                    else:
                        attempt["result"] = "unknown"
                    attempts_log.append(attempt)
                except Exception as e:
                    attempt["error"] = str(e)[:500]
                    attempts_log.append(attempt)

            try:
                SCREENSHOT.parent.mkdir(parents=True, exist_ok=True)
                sb.save_screenshot(str(SCREENSHOT))
            except Exception:
                pass

    return cleared, attempts_log, last_title, last_url, last_text


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
    ap.add_argument(
        "--attempts",
        type=int,
        default=int(os.environ.get("INDEED_CF_ATTEMPTS", "4")),
        help="Inner open/click attempts per browser session",
    )
    ap.add_argument(
        "--rounds",
        type=int,
        default=int(os.environ.get("INDEED_CF_ROUNDS", "3")),
        help="Outer rounds; rotate WARP + rebuild profile between rounds",
    )
    ap.add_argument(
        "--prepare-hybrid",
        action="store_true",
        default=os.environ.get("INDEED_PREPARE_HYBRID", "1") != "0",
        help="Copy auth cookies from seed profile and strip burned CF cookies",
    )
    ap.add_argument(
        "--rotate-warp",
        action="store_true",
        default=os.environ.get("INDEED_ROTATE_WARP", "1") != "0",
        help="Rotate WARP exit IP between failed outer rounds",
    )
    args = ap.parse_args()

    report: dict = {
        "startedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "url": args.url,
        "proxy": args.proxy,
        "userDataDir": args.user_data_dir,
        "ok": False,
        "rounds": [],
        "attempts": [],
    }

    def emit(payload: dict) -> None:
        print(json.dumps(payload, indent=2), file=sys.__stdout__, flush=True)

    if not socks_up(args.proxy):
        # Auto-start local WARP if this looks like the default SOCKS endpoint.
        if is_local_warp(args.proxy):
            script = ROOT / "scripts" / "start-warp-proxy.sh"
            subprocess.run(
                ["bash", str(script), "start"],
                capture_output=True,
                text=True,
                timeout=120,
            )
        if not socks_up(args.proxy):
            report["error"] = "warp_socks_down"
            report["hint"] = "Run: bash scripts/start-warp-proxy.sh"
            OUT.parent.mkdir(parents=True, exist_ok=True)
            OUT.write_text(json.dumps(report, indent=2))
            emit(report)
            return 2

    try:
        import seleniumbase  # noqa: F401
    except ImportError:
        report["error"] = "seleniumbase_missing"
        report["hint"] = "pip install --user seleniumbase PyAutoGUI"
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(report, indent=2))
        emit(report)
        return 2

    rebind_seleniumbase_filelock()
    report["filelockSingleton"] = True
    os.environ.setdefault("DISPLAY", ":1")
    user_data = args.user_data_dir
    Path(user_data).mkdir(parents=True, exist_ok=True)

    last_title = last_url = last_text = ""
    cleared = False

    for round_n in range(1, max(1, args.rounds) + 1):
        round_info: dict = {"n": round_n, "exitIp": warp_exit_ip(args.proxy)}
        if args.prepare_hybrid:
            prep = prepare_hybrid(args.seed_profile, user_data)
            report["profilePrep"] = prep
            round_info["profilePrep"] = {
                "cfCookiesDeleted": prep.get("cfCookiesDeleted"),
                "hasAuth": prep.get("hasAuth"),
            }

        try:
            ok, attempts_log, last_title, last_url, last_text = run_browser_round(
                url=args.url,
                proxy=args.proxy,
                user_data=user_data,
                attempts=args.attempts,
            )
        except Exception as e:
            ok = False
            attempts_log = [{"error": str(e)[:500]}]
        round_info["ok"] = ok
        round_info["attempts"] = attempts_log
        report["rounds"].append(round_info)
        # Flatten for backward-compatible consumers that only read attempts[].
        report["attempts"].extend(attempts_log)
        if ok:
            cleared = True
            break

        if round_n < args.rounds and args.rotate_warp:
            rot = rotate_warp(args.proxy)
            round_info["warpRotate"] = rot
            report.setdefault("warpRotations", []).append(rot)
            # Brief cool-down so Cloudflare does not immediately re-challenge.
            time.sleep(5)

    report["finishedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report["finalTitle"] = last_title
    report["finalUrl"] = last_url
    report["finalTextSample"] = last_text[:800]
    report["screenshot"] = str(SCREENSHOT) if SCREENSHOT.exists() else None
    report["ok"] = bool(cleared and looks_healthy(last_title, last_text, last_url))
    if not report["ok"]:
        report["reason"] = "indeed_cloudflare_still_blocked"
        report["hint"] = (
            "Tried multi-strategy Turnstile clicks + WARP IP rotation. "
            "If this keeps failing, set residential INDEED_HTTP_PROXY or run "
            "scripts/indeed-home-daily.sh on home Wi‑Fi."
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2))
    emit(report)
    return 0 if report["ok"] else 5


if __name__ == "__main__":
    sys.exit(main())
