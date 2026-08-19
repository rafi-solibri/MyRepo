#!/usr/bin/env python3
"""Daily Hitech City / Knowledge City / Madhapur premium-campus apply orchestrator.

Priority order:
0) Discover / refresh campus software tenants → companies.json
1) Official company career portals in PARALLEL (PRIMARY) — default 10 Chrome tabs
2) LinkedIn company-targeted Easy Apply + external ATS + referrals (PRIMARY)
3) Board browse with campus allowlist: Naukri, Foundit, Cutshort, Instahyre, Indeed

Every daily/cron run uses multi-tab careers apply (HITECHCITY_PARALLEL_TABS=10)
unless explicitly set to 1. Owner only solves captchas; workers keep submitting.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))


def _owner_asleep_bootstrap() -> bool:
    """Detect overnight / unattended cron before importing apply modules."""
    if (os.environ.get("HITECHCITY_OWNER_ASLEEP") or "").strip().lower() in ("1", "true", "yes"):
        return True
    if Path("/tmp/hitechcity-owner-asleep").exists():
        return True
    return False


def _cloud_headless_unattended() -> bool:
    """True on cloud VMs — the owner is not sitting at this Chrome.

    HOME_LOCAL and Windows system Chrome are headed. Cloud Xvfb often sets
    DISPLAY=:1 which previously skipped the cap and burned Oracle persist_retry.
    """
    if (os.environ.get("HOME_LOCAL") or "").strip().lower() in ("1", "true", "yes"):
        return False
    if (os.environ.get("CHROME_CDP_MODE") or "").strip().lower() == "system":
        return False
    if os.name == "nt" or (os.environ.get("OS") or "") == "Windows_NT":
        return False
    return True


# ---- Every-run defaults (cron + headed + home) — set before importing apply modules ----
os.environ.setdefault("HITECHCITY_PARALLEL_TABS", "10")
os.environ.setdefault("HITECHCITY_MAX_PER_COMPANY", "6")
os.environ.setdefault("HITECHCITY_MAX_COMPANIES", "60")
os.environ.setdefault("HITECHCITY_MAX_EXT_WALLS", "3")
os.environ.setdefault("HITECHCITY_MAX_EXT_ATTEMPTS", "12")
os.environ.setdefault("HITECHCITY_CAREERS_KEYWORD_SEARCHES", "4")
os.environ.setdefault("HITECHCITY_DISCOVERY", "1")
os.environ.setdefault("HITECHCITY_DISCOVERY_LINKEDIN", "0")
os.environ.setdefault("HITECHCITY_DISCOVERY_WEB", "1")
os.environ.setdefault("ATS_CAPTCHA_POLL_SEC", "0.4")
os.environ.setdefault("ATS_OWNER_FOCUS_EVERY_SEC", "2")

# Overnight / owner-asleep: short park on captcha/forms, skip long persist retries,
# and cap soft incompletes per company so LinkedIn volume reaches Easy Apply + boards.
if _owner_asleep_bootstrap():
    os.environ["HITECHCITY_OWNER_ASLEEP"] = "1"
    os.environ.setdefault("ATS_OWNER_FORM_WAIT_SEC", "12")
    os.environ.setdefault("ATS_CAPTCHA_WAIT_SEC", "12")
    os.environ.setdefault("HITECHCITY_EXT_ATS_TIME_CAP_S", "45")
    os.environ.setdefault("HITECHCITY_ATS_TIME_CAP_S", "45")
    os.environ.setdefault("HITECHCITY_ATS_PERSIST_RETRY", "0")
    os.environ.setdefault("HITECHCITY_MAX_SOFT_INCOMPLETE", "2")
    print(
        "OWNER_ASLEEP=1 — short ATS waits (45s), ASK_OWNER 12s, no persist_retry, "
        "soft-incomplete cap=2/company",
        flush=True,
    )
elif _cloud_headless_unattended():
    # Morning cloud cron is also unattended: Oracle persist_retry + infinite
    # soft incompletes burned LinkedIn (4+ EXT timeouts, 0 submits) before
    # later campus Easy Apply / boards ran.
    os.environ.setdefault("HITECHCITY_ATS_PERSIST_RETRY", "0")  # pragma: allowlist secret
    os.environ.setdefault("HITECHCITY_MAX_SOFT_INCOMPLETE", "2")  # pragma: allowlist secret
    os.environ.setdefault("ATS_OWNER_FORM_WAIT_SEC", "12")
    os.environ.setdefault("ATS_CAPTCHA_WAIT_SEC", "12")
    print(
        "CLOUD_HEADLESS — no persist_retry, soft-incomplete cap=2/company, "
        "short ASK_OWNER (owner cannot see this Chrome)",
        flush=True,
    )


from tools.hitechcity.board_campus_apply import run as run_boards
from tools.hitechcity.careers_apply import load_companies, run as run_careers
from tools.hitechcity.discover_tenants import run as run_discovery
from tools.hitechcity.linkedin_target_apply import run as run_linkedin

OUT_DEFAULT_CLOUD = Path("/opt/cursor/artifacts/hitechcity-daily.json")
OUT_DEFAULT_LOCAL = _root / "artifacts" / "hitechcity-daily.json"


def configure_windows_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles (job titles with ā etc.)."""
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def default_report_path() -> Path:
    if os.environ.get("HITECHCITY_REPORT"):
        return Path(os.environ["HITECHCITY_REPORT"])
    if OUT_DEFAULT_CLOUD.parent.is_dir():
        return OUT_DEFAULT_CLOUD
    return OUT_DEFAULT_LOCAL


OUT = default_report_path()


def main() -> int:
    configure_windows_stdio()
    started = datetime.now(timezone.utc).isoformat()
    parallel_tabs = os.environ.get("HITECHCITY_PARALLEL_TABS", "10")
    print(
        f"HitechCity daily_apply defaults: PARALLEL_TABS={parallel_tabs} "
        f"MAX_PER_COMPANY={os.environ.get('HITECHCITY_MAX_PER_COMPANY')} "
        f"MAX_COMPANIES={os.environ.get('HITECHCITY_MAX_COMPANIES')} "
        f"MAX_EXT_WALLS={os.environ.get('HITECHCITY_MAX_EXT_WALLS')}",
        flush=True,
    )
    summary: dict = {
        "startedAt": started,
        "focus": "Knowledge City / Knowledge Park / Mindspace Madhapur / premium HITEC buildings",
        "parallelTabs": int(parallel_tabs) if str(parallel_tabs).isdigit() else parallel_tabs,
        "discovery": {},
        "careers": {},
        "linkedin": {},
        "boards": {},
        "totals": {},
        "errors": [],
    }

    careers_rep = None
    linkedin_rep = None
    companies = None

    # 0) Discover campus tenants first so LinkedIn/careers/boards share a fresh list.
    try:
        print("=== HitechCity discovery (campus tenants) ===", flush=True)
        disc = run_discovery(persist=True)
        summary["discovery"] = {
            "added": len(disc.get("added") or []),
            "updated": len(disc.get("updated") or []),
            "total": disc.get("afterCount"),
            "prunedJunk": disc.get("prunedJunk") or [],
            "campusCatalogAdded": len((disc.get("campusCatalog") or {}).get("added") or []),
            "webDirectoryAdded": len((disc.get("webDirectories") or {}).get("added") or []),
            "webDirectoryErrors": len((disc.get("webDirectories") or {}).get("errors") or []),
            "linkedinError": disc.get("linkedinError"),
            "report": disc.get("report"),
            "addedNames": (disc.get("added") or [])[:40],
        }
        companies = load_companies()
    except Exception as e:
        summary["errors"].append({"phase": "discovery", "error": str(e), "trace": traceback.format_exc()[-1500:]})
        print("DISCOVERY ERROR", e, flush=True)
        try:
            companies = load_companies()
        except Exception:
            companies = None

    careers_only = os.environ.get("HITECHCITY_CAREERS_ONLY", "").strip() in ("1", "true", "yes")
    skip_linkedin = careers_only or os.environ.get("HITECHCITY_SKIP_LINKEDIN", "").strip() in (
        "1",
        "true",
        "yes",
    )

    # 1) Official career portals FIRST — LinkedIn CAPTCHA must not starve ATS time.
    try:
        print("=== HitechCity careers portals (PRIMARY) ===", flush=True)
        careers_rep = run_careers(companies)
        summary["careers"] = {
            "applied": len(careers_rep.applied),
            "blocked": len(careers_rep.blocked),
            "skipped": len(careers_rep.skipped),
            "scanned": len(careers_rep.scanned),
            "report": str(Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))),
        }
    except Exception as e:
        summary["errors"].append({"phase": "careers", "error": str(e), "trace": traceback.format_exc()[-1500:]})
        print("CAREERS ERROR", e, flush=True)

    # 2) LinkedIn company-targeted applies + referrals (after careers)
    if skip_linkedin:
        summary["linkedin"] = {"skippedPhase": "careers_only"}
        print("=== HitechCity LinkedIn skipped (careers-only) ===", flush=True)
    else:
        try:
            print("=== HitechCity LinkedIn + referrals ===", flush=True)
            linkedin_rep = run_linkedin(companies)
            summary["linkedin"] = {
                "applied": len(linkedin_rep.applied),
                "external": len(linkedin_rep.external),
                "referralsSent": sum(1 for r in linkedin_rep.referrals if r.get("status") == "sent"),
                "blocked": len(linkedin_rep.blocked),
                "skipped": len(linkedin_rep.skipped),
                "report": str(
                    Path(os.environ.get("HITECHCITY_LINKEDIN_REPORT", "/opt/cursor/artifacts/hitechcity-linkedin.json"))
                ),
            }
        except Exception as e:
            summary["errors"].append({"phase": "linkedin", "error": str(e), "trace": traceback.format_exc()[-1500:]})
            print("LINKEDIN ERROR", e, flush=True)

    # 3) Job boards — campus allowlist (secondary). Skip when careers-only.
    if careers_only:
        summary["boards"] = {"skippedPhase": "careers_only"}
        print("=== HitechCity boards skipped (careers-only) ===", flush=True)
    else:
        try:
            print("=== HitechCity board browse (Naukri/Foundit/Cutshort/Instahyre/Indeed) ===", flush=True)
            boards_rep = run_boards(companies)
            summary["boards"] = {
                "applied": (boards_rep.get("totals") or {}).get("applied") or 0,
                "blocked": (boards_rep.get("totals") or {}).get("blocked") or 0,
                "skipped": (boards_rep.get("totals") or {}).get("skipped") or 0,
                "portals": [
                    {
                        "portal": p.get("portal"),
                        "status": p.get("status"),
                        "applied": p.get("applied"),
                        "reason": p.get("reason"),
                        "rc": p.get("rc"),
                    }
                    for p in (boards_rep.get("portals") or [])
                ],
                "report": boards_rep.get("report"),
                "skippedPhase": boards_rep.get("skipped"),
            }
        except Exception as e:
            summary["errors"].append({"phase": "boards", "error": str(e), "trace": traceback.format_exc()[-1500:]})
            print("BOARDS ERROR", e, flush=True)

    applied = (
        (summary.get("careers", {}).get("applied") or 0)
        + (summary.get("linkedin", {}).get("applied") or 0)
        + (summary.get("boards", {}).get("applied") or 0)
    )
    blocked = (
        (summary.get("careers", {}).get("blocked") or 0)
        + (summary.get("linkedin", {}).get("blocked") or 0)
        + (summary.get("boards", {}).get("blocked") or 0)
    )
    skipped = (
        (summary.get("careers", {}).get("skipped") or 0)
        + (summary.get("linkedin", {}).get("skipped") or 0)
        + (summary.get("boards", {}).get("skipped") or 0)
    )
    summary["totals"] = {
        "applied": applied,
        "referralsSent": summary.get("linkedin", {}).get("referralsSent") or 0,
        "blocked": blocked,
        "skipped": skipped,
        "discoveryAdded": summary.get("discovery", {}).get("added") or 0,
    }
    # ensure-missing / coverage detectors look for counts + ok (not only nested totals)
    summary["counts"] = {
        "applied": applied,
        "blocked": blocked,
        "skipped": skipped,
        "seen": blocked + skipped + applied,
    }
    summary["ok"] = True
    summary["finishedAt"] = datetime.now(timezone.utc).isoformat()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary["totals"]))
    print(f"REPORT {OUT}", flush=True)

    # Exit 3 if LinkedIn login missing and zero applies
    if applied == 0 and any("linkedin_login_required" in str(e) for e in summary["errors"]):
        return 3
    if applied == 0 and linkedin_rep and linkedin_rep.blocked and linkedin_rep.blocked[0].get("reason") == "linkedin_login_required":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
