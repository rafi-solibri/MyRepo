#!/usr/bin/env python3
"""Secondary board browse for Hitech City campus companies.

Runs Naukri / Foundit / Cutshort / Instahyre / Indeed with a company allowlist
derived from tools/hitechcity/companies.json. Official careers + LinkedIn remain
PRIMARY in daily_apply.py; this phase is capped and best-effort per portal login.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.hitechcity.campus_allowlist import write_allowlist_artifact
from tools.hitechcity.careers_apply import load_companies

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(
    os.environ.get(
        "HITECHCITY_BOARDS_REPORT",
        "/opt/cursor/artifacts/hitechcity-boards.json",
    )
)

# Default order: CDP Playwright boards first; Indeed UC last (heavier).
DEFAULT_BOARDS = ("naukri", "foundit", "cutshort", "instahyre", "indeed")


def _artifact_dir() -> Path:
    if REPORT.parent.is_dir():
        return REPORT.parent
    p = ROOT / "artifacts"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _boards() -> list[str]:
    raw = os.environ.get("HITECHCITY_BOARDS", ",".join(DEFAULT_BOARDS))
    return [b.strip().lower() for b in raw.split(",") if b.strip()]


def _max_for(portal: str) -> str:
    defaults = {
        "naukri": "12",
        "foundit": "12",
        "cutshort": "10",
        "instahyre": "10",
        "indeed": "6",
    }
    env_key = f"HITECHCITY_{portal.upper()}_MAX"
    return os.environ.get(env_key, defaults.get(portal, "10"))


def resolve_bash() -> str:
    """Prefer Git Bash on Windows — bare `bash` can hit the WSL MSI stub (REGDB_E_CLASSNOTREG)."""
    override = (os.environ.get("GIT_BASH") or os.environ.get("BASH_PATH") or "").strip()
    if override and Path(override).is_file():
        return override

    local = os.environ.get("LOCALAPPDATA") or ""
    roots = [
        Path(local) / "Programs" / "Git" if local else None,
        Path(os.environ.get("ProgramFiles") or r"C:\Program Files") / "Git",
        Path(os.environ.get("ProgramFiles(x86)") or r"C:\Program Files (x86)") / "Git",
    ]
    candidates: list[Path] = []
    for root in roots:
        if root is None:
            continue
        candidates.extend([root / "bin" / "bash.exe", root / "usr" / "bin" / "bash.exe"])

    seen: set[str] = set()
    for c in candidates:
        key = str(c).lower()
        if key in seen:
            continue
        seen.add(key)
        if c.is_file():
            return str(c)

    which = shutil.which("bash")
    if which:
        # Avoid WindowsApps / System32 WSL stubs that raise REGDB_E_CLASSNOTREG.
        low = which.lower().replace("/", "\\")
        if "windowsapps" in low or low.endswith(r"\system32\bash.exe"):
            raise FileNotFoundError(
                "bash resolved to WSL/WindowsApps stub; install Git for Windows or set GIT_BASH"
            )
        return which
    raise FileNotFoundError("bash not found — install Git for Windows or set GIT_BASH")


def _cdp_up(port: int = 9222) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _preflight_and_launch(portal: str) -> dict[str, Any]:
    bash = resolve_bash()
    # Reuse already-running system Chrome CDP on home (careers phase left :9222 up).
    reuse = os.environ.get("HITECHCITY_BOARD_REUSE_CDP", "1") == "1"
    system = (os.environ.get("CHROME_CDP_MODE") or "").lower() == "system"
    if reuse and system and _cdp_up():
        return {
            "preflightRc": 0,
            "launchRc": 0,
            "preflightTail": "skipped_preflight_reuse_cdp",
            "launchTail": "skipped_launch_reuse_cdp",
            "bash": bash,
            "reusedCdp": True,
        }

    env = {
        **os.environ,
        "CHROME_CDP_MODE": os.environ.get(
            "CHROME_CDP_MODE", "system" if os.name == "nt" else ""
        ),
    }
    pre = subprocess.run(
        [bash, str(ROOT / "scripts/preflight-portal-run.sh"), portal],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )
    launch = subprocess.run(
        [bash, str(ROOT / "scripts/launch-chrome-cdp.sh"), portal],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    return {
        "preflightRc": pre.returncode,
        "launchRc": launch.returncode,
        "preflightTail": ((pre.stdout or "") + (pre.stderr or ""))[-500:],
        "launchTail": ((launch.stdout or "") + (launch.stderr or ""))[-800:],
        "bash": bash,
        "reusedCdp": False,
    }


def _run_portal(portal: str, allowlist: Path, env_base: dict[str, str]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "portal": portal,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "status": "blocked",
        "applied": 0,
        "blocked": 0,
        "skipped": 0,
    }
    try:
        setup = _preflight_and_launch(portal)
    except FileNotFoundError as e:
        row["reason"] = "bash_not_found"
        row["setupTail"] = str(e)[:300]
        return row
    row["setup"] = {
        k: setup[k]
        for k in ("preflightRc", "launchRc", "reusedCdp", "bash")
        if k in setup
    }
    # preflight 0 = ok; 3 = missing auth (skip this portal, continue others).
    # Other non-zero (e.g. broken bash stub rc 1) previously masked all boards.
    if setup["preflightRc"] not in (0,) and not setup.get("reusedCdp"):
        row["reason"] = f"preflight_rc_{setup['preflightRc']}"
        row["setupTail"] = setup.get("preflightTail", "")[-300:]
        return row
    if setup["launchRc"] not in (0,) and not setup.get("reusedCdp"):
        # hitechcity-style continue: some launches warn but still serve CDP
        if not _cdp_up():
            row["reason"] = f"launch_rc_{setup['launchRc']}"
            row["launchWarning"] = setup.get("launchTail", "")[-300:]
            return row
        row["launchWarning"] = setup.get("launchTail", "")[-300:]

    env = dict(env_base)
    env["HITECHCITY_COMPANY_ALLOWLIST"] = str(allowlist)
    env["HITECHCITY_BOARD_MODE"] = "1"
    max_n = _max_for(portal)
    cmd: list[str]
    if portal == "naukri":
        env["NAUKRI_MAX_APPLIES"] = max_n
        env["NAUKRI_SKIP_PROFILE_REFRESH"] = env.get("NAUKRI_SKIP_PROFILE_REFRESH", "1")
        cmd = ["node", str(ROOT / "tools/naukri/daily_apply.js")]
    elif portal == "foundit":
        env["FOUNDIT_MAX_APPLIES"] = max_n
        cmd = ["node", str(ROOT / "tools/foundit/daily_apply.js")]
    elif portal == "cutshort":
        env["CUTSHORT_MAX_APPLIES"] = max_n
        cmd = ["node", str(ROOT / "tools/cutshort/daily_apply.js")]
    elif portal == "instahyre":
        env["INSTAHYRE_MAX_APPLIES"] = max_n
        cmd = ["node", str(ROOT / "tools/instahyre/daily_apply.js")]
    elif portal == "indeed":
        env["INDEED_MAX_APPLIES"] = max_n
        # Prefer the node wrapper which calls UC python
        cmd = ["node", str(ROOT / "tools/indeed/daily_apply.js")]
    else:
        row["reason"] = "unknown_portal"
        return row

    timeout_s = int(os.environ.get("HITECHCITY_BOARD_TIMEOUT_S", "900"))
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        row["rc"] = proc.returncode
        row["stdoutTail"] = (proc.stdout or "")[-1200:]
        row["stderrTail"] = (proc.stderr or "")[-600:]
        row["status"] = "ok" if proc.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        row["status"] = "timeout"
        row["reason"] = f"timeout_{timeout_s}s"
        return row
    except Exception as e:
        row["status"] = "error"
        row["reason"] = str(e)[:300]
        return row

    # Best-effort count scrape from known report paths
    report_guess = {
        "naukri": "naukri-daily-apply.json",
        "foundit": "foundit-apply-report.json",
        "cutshort": "cutshort-daily-run.json",
        "instahyre": "instahyre-apply-report.json",
        "indeed": "indeed-daily-run.json",
    }.get(portal)
    if report_guess:
        rp = _artifact_dir() / report_guess
        row["report"] = str(rp)
        if rp.is_file():
            try:
                data = json.loads(rp.read_text(encoding="utf-8"))
                if isinstance(data.get("applied"), list):
                    row["applied"] = len(data["applied"])
                elif isinstance(data.get("counts"), dict):
                    row["applied"] = int(data["counts"].get("applied") or 0)
                    row["blocked"] = int(data["counts"].get("blocked") or 0)
                    row["skipped"] = int(data["counts"].get("skipped") or 0)
                if isinstance(data.get("skipped"), list):
                    row["skipped"] = len(data["skipped"])
                if isinstance(data.get("blocked"), list):
                    row["blocked"] = len(data["blocked"])
            except Exception:
                pass
    row["finishedAt"] = datetime.now(timezone.utc).isoformat()
    return row


def run(companies: list[dict] | None = None) -> dict[str, Any]:
    if os.environ.get("HITECHCITY_BOARD_BROWSE", "1") != "1":
        return {"ok": True, "skipped": True, "reason": "HITECHCITY_BOARD_BROWSE=0"}

    companies = companies or load_companies()
    allowlist = write_allowlist_artifact(companies, _artifact_dir() / "hitechcity-company-allowlist.json")
    env_base = os.environ.copy()
    # Ensure node can resolve local modules
    env_base["NODE_PATH"] = str(ROOT) + (os.pathsep + env_base["NODE_PATH"] if env_base.get("NODE_PATH") else "")

    report: dict[str, Any] = {
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "allowlist": str(allowlist),
        "companyCount": len(companies),
        "portals": [],
        "totals": {"applied": 0, "blocked": 0, "skipped": 0},
    }

    for portal in _boards():
        print(f"=== HitechCity board browse: {portal} ===", flush=True)
        t0 = time.time()
        row = _run_portal(portal, allowlist, env_base)
        row["elapsedSec"] = round(time.time() - t0, 1)
        report["portals"].append(row)
        report["totals"]["applied"] += int(row.get("applied") or 0)
        report["totals"]["blocked"] += int(row.get("blocked") or 0)
        report["totals"]["skipped"] += int(row.get("skipped") or 0)
        print(
            json.dumps(
                {
                    "board": portal,
                    "status": row.get("status"),
                    "applied": row.get("applied"),
                    "rc": row.get("rc"),
                    "reason": row.get("reason"),
                }
            ),
            flush=True,
        )

    report["finishedAt"] = datetime.now(timezone.utc).isoformat()
    report["ok"] = True
    out = REPORT if REPORT.parent.is_dir() else _artifact_dir() / "hitechcity-boards.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report["report"] = str(out)
    print(json.dumps({"boardsTotals": report["totals"], "report": str(out)}), flush=True)
    return report


if __name__ == "__main__":
    run()
