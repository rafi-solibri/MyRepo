#!/usr/bin/env python3
"""Daily Hitech City / Knowledge City / Madhapur premium-campus apply orchestrator.

Priority order:
1) Company career portals for curated campus tenants
2) LinkedIn company-targeted Easy Apply + external ATS
3) Referral / poster outreach on LinkedIn
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

from tools.hitechcity.careers_apply import run as run_careers
from tools.hitechcity.linkedin_target_apply import run as run_linkedin

OUT = Path(os.environ.get("HITECHCITY_REPORT", "/opt/cursor/artifacts/hitechcity-daily.json"))


def main() -> int:
    started = datetime.now(timezone.utc).isoformat()
    summary: dict = {
        "startedAt": started,
        "focus": "Knowledge City / Knowledge Park / Mindspace Madhapur / premium HITEC buildings",
        "careers": {},
        "linkedin": {},
        "totals": {},
        "errors": [],
    }

    careers_rep = None
    linkedin_rep = None

    # LinkedIn company-targeted applies + referrals first (highest yield with saved session),
    # then company career portals for ATS that allow guest/session apply.
    try:
        print("=== HitechCity LinkedIn + referrals ===", flush=True)
        linkedin_rep = run_linkedin()
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

    try:
        print("=== HitechCity careers portals ===", flush=True)
        careers_rep = run_careers()
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

    applied = (summary.get("careers", {}).get("applied") or 0) + (summary.get("linkedin", {}).get("applied") or 0)
    summary["totals"] = {
        "applied": applied,
        "referralsSent": summary.get("linkedin", {}).get("referralsSent") or 0,
        "blocked": (summary.get("careers", {}).get("blocked") or 0)
        + (summary.get("linkedin", {}).get("blocked") or 0),
        "skipped": (summary.get("careers", {}).get("skipped") or 0)
        + (summary.get("linkedin", {}).get("skipped") or 0),
    }
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
