#!/usr/bin/env python3
"""Secondary board browse for Hitech City campus companies.

Runs Naukri / Foundit / Cutshort / Instahyre / Indeed with a company allowlist
derived from tools/hitechcity/companies.json. Official careers + LinkedIn remain
PRIMARY in daily_apply.py; this phase is capped and best-effort per portal login.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
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


def _preflight_and_launch(portal: str) -> dict[str, Any]:
    pre = subprocess.run(
        ["bash", str(ROOT / "scripts/preflight-portal-run.sh"), portal],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    launch = subprocess.run(
        ["bash", str(ROOT / "scripts/launch-chrome-cdp.sh"), portal],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    return {
        "preflightRc": pre.returncode,
        "launchRc": launch.returncode,
        "preflightTail": (pre.stdout or "")[-500:],
        "launchTail": (launch.stdout or launch.stderr or "")[-800:],
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
    setup = _preflight_and_launch(portal)
    row["setup"] = {k: setup[k] for k in ("preflightRc", "launchRc")}
    if setup["preflightRc"] not in (0,):
        # preflight 3 = missing auth — continue others
        row["reason"] = f"preflight_rc_{setup['preflightRc']}"
        row["setupTail"] = setup.get("preflightTail", "")[-300:]
        return row
    if setup["launchRc"] not in (0,):
        # hitechcity-style continue: some launches warn but still serve CDP
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
