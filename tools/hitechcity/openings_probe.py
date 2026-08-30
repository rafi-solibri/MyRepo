#!/usr/bin/env python3
"""Probe preferred home-campus companies for live Hyderabad openings.

Merges curated careers URL hints, scans listing pages via CDP, and stamps
`hasOpenings` / `openingsCount` / `sampleOpenings` onto companies.json so
careers + LinkedIn apply those employers first.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from tools.hitechcity.campus_tenant_catalog import (  # noqa: E402
    PREFERRED_HOME_CAMPUSES,
    campus_preference_rank,
)
from tools.hitechcity.filters import (  # noqa: E402
    location_or_campus_ok,
    title_matches_senior_stack,
)

COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(
    os.environ.get(
        "HITECHCITY_OPENINGS_REPORT",
        "/opt/cursor/artifacts/hitechcity-openings.json",
    )
)

# Curated careers search URLs (Hyderabad-biased) for preferred / RMZ tenants
# that discovery often adds without careersUrls.
CAREERS_URL_HINTS: dict[str, list[str]] = {
    "CGI": [
        "https://cgi.njoyn.com/corp/xweb/XWeb.asp?NTKN=c&clid=21001&Page=SearchResults"
        "&lang=1&Keyword=Engineering+Manager&CountryID=IN&CountryDesc=India"
    ],
    "Electronic Arts": [
        "https://jobs.ea.com/en_US/careers/SearchJobs/?3_47_3=%2C7622%2C&3_47_3_format=448"
        "&listFilterMode=1&jobRecordsPerPage=20"
    ],
    "EY": [
        "https://careers.ey.com/ey/search/?q=Engineering+Manager&locationsearch=Hyderabad"
    ],
    "KPMG": [
        "https://ejof.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/requisitions"
        "?keyword=Engineering+Manager&location=Hyderabad%2C+Telangana%2C+India",
    ],
    "Providence": [
        "https://www.providenceindia.com/careers",
        "https://careers.providence.org/us/en/search-results?keywords=Engineering%20Manager",
    ],
    "Zenoti": [
        "https://job-boards.greenhouse.io/zenoti",
        "https://boards.greenhouse.io/zenoti",
    ],
    "Flutter Entertainment": [
        "https://careers.flutter.com/search/?q=Engineering+Manager&locationsearch=Hyderabad"
    ],
    "Darwinbox": [
        "https://darwinbox.darwinbox.in/ms/candidate/careers",
        "https://www.darwinbox.com/careers",
    ],
    "Infor": [
        "https://careers.infor.com/en-US/careers/SearchJobs/?listFilterMode=1"
        "&jobRecordsPerPage=20&keywords=Engineering+Manager"
    ],
    "Micron Technology": [
        "https://careers.micron.com/careers?query=Engineering%20Manager&location=Hyderabad"
    ],
    "LTIMindtree": [
        "https://careers.ltimindtree.com/search/?q=Engineering+Manager&locationsearch=Hyderabad"
    ],
    "Mphasis": [
        "https://careers.mphasis.com/home/careers/jobsearch.html?q=Engineering+Manager&loc=Hyderabad"
    ],
    "S&P Global": [
        "https://careers.spglobal.com/jobs?keywords=Engineering%20Manager&location=Hyderabad"
    ],
    "TTEC": [
        "https://www.ttecjobs.com/en/careers?search=Engineering+Manager&country=IN"
    ],
    "HighRadius": [
        "https://highradius.wd1.myworkdayjobs.com/HighRadius?q=Engineering%20Manager"
    ],
    "Vanguard": [
        "https://www.vanguardjobs.com/job-search-results/?keyword=Engineering+Manager"
        "&location=Hyderabad"
    ],
    "Cotelligent": [
        "https://www.cotelligent.com/careers/",
    ],
}


def openings_preference_rank(company: dict[str, Any]) -> int:
    """0 = known live openings (apply first within campus tier); 1 = unknown/none."""
    if company.get("hasOpenings") or int(company.get("openingsCount") or 0) > 0:
        return 0
    return 1


def ensure_careers_url_hints(companies: list[dict[str, Any]]) -> list[str]:
    """Attach curated careers URLs to preferred companies missing them."""
    touched: list[str] = []
    for c in companies:
        name = (c.get("name") or "").strip()
        hints = CAREERS_URL_HINTS.get(name)
        if not hints:
            continue
        camps = set(c.get("campuses") or [])
        if not (camps & PREFERRED_HOME_CAMPUSES):
            continue
        urls = list(c.get("careersUrls") or [])
        added = False
        for u in hints:
            if u and u not in urls:
                urls.append(u)
                added = True
        if added:
            c["careersUrls"] = urls
            touched.append(name)
    return touched


def _qualifying_jobs(raw: list[dict[str, str]]) -> list[dict[str, str]]:
    try:
        from .careers_apply import CAREERS_TITLE_SKIP
    except Exception:
        from careers_apply import CAREERS_TITLE_SKIP  # type: ignore

    out: list[dict[str, str]] = []
    seen: set[str] = set()
    for j in raw:
        role = (j.get("role") or j.get("text") or "").strip()
        url = (j.get("url") or j.get("href") or "").strip()
        loc = (j.get("location") or "").strip()
        if not role or not url:
            continue
        if url in seen:
            continue
        if not title_matches_senior_stack(role):
            continue
        # Same silicon / wrong-stack skip as careers extract — do not boost
        # preferred campuses for Physical/Layout/HBM/DV titles.
        if CAREERS_TITLE_SKIP.search(role):
            continue
        if not location_or_campus_ok(loc or role, "", role):
            # Title/card may embed Hyd — accept when role blob has Hyd/campus
            if not location_or_campus_ok(role, "", ""):
                continue
        seen.add(url)
        out.append({"role": role[:160], "url": url, "location": loc[:80]})
    return out


def probe_company(page: Any, company: dict[str, Any], max_urls: int = 2) -> dict[str, Any]:
    from tools.hitechcity.careers_apply import (
        expand_careers_scan_urls,
        extract_job_links,
        pin_portal_location_ui,
    )

    name = company.get("name") or ""
    urls = expand_careers_scan_urls(company.get("careersUrls") or [])[:max_urls]
    if not urls:
        return {
            "company": name,
            "openingsCount": 0,
            "hasOpenings": False,
            "reason": "no_careers_urls",
            "sampleOpenings": [],
        }
    found: list[dict[str, str]] = []
    last_err = ""
    for url in urls:
        try:
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                last_err = str(e)[:160]
                # Interrupted navigations often still land on a usable listing.
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=15000)
                except Exception:
                    pass
            page.wait_for_timeout(2200)
            try:
                pin_portal_location_ui(page)
            except Exception:
                pass
            page.wait_for_timeout(900)
            raw = extract_job_links(page, name)
            norm = []
            for r in raw:
                norm.append(
                    {
                        "role": r.get("role") or r.get("text") or "",
                        "url": r.get("url") or r.get("href") or "",
                        "location": r.get("location") or "",
                    }
                )
            found.extend(_qualifying_jobs(norm))
            if found:
                break
        except Exception as e:
            last_err = str(e)[:160]
            continue
    uniq: list[dict[str, str]] = []
    seen: set[str] = set()
    for j in found:
        if j["url"] in seen:
            continue
        seen.add(j["url"])
        uniq.append(j)
    return {
        "company": name,
        "openingsCount": len(uniq),
        "hasOpenings": len(uniq) > 0,
        "sampleOpenings": uniq[:8],
        "scannedUrls": urls,
        "error": last_err or None,
    }


def run(persist: bool = True, max_companies: int | None = None) -> dict[str, Any]:
    if os.environ.get("HITECHCITY_OPENINGS_PROBE", "1") != "1":
        return {"ok": True, "skipped": True, "reason": "HITECHCITY_OPENINGS_PROBE=0"}

    data = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
    companies = list(data.get("companies") or [])
    hints_touched = ensure_careers_url_hints(companies)

    preferred = [
        c
        for c in companies
        if campus_preference_rank(c) == 0 and (c.get("careersUrls") or [])
    ]
    # Probe RMZ / Knowledge / Raheja with URLs first; cap for runtime.
    def _probe_order(c: dict[str, Any]) -> tuple[int, int, str]:
        camps = set(c.get("campuses") or [])
        rmz = 0 if camps & {"rmz-nexity", "rmz-skyview", "rmz-futura"} else 1
        home = 0 if camps & PREFERRED_HOME_CAMPUSES else 1
        return (rmz, home, (c.get("name") or "").lower())

    preferred = sorted(preferred, key=_probe_order)
    cap = max_companies or int(os.environ.get("HITECHCITY_OPENINGS_PROBE_MAX", "28"))
    preferred = preferred[:cap]

    results: list[dict[str, Any]] = []
    with_openings: list[str] = []

    from playwright.sync_api import sync_playwright
    from tools.hitechcity.careers_apply import _connect_careers_cdp

    with sync_playwright() as p:
        _browser, _context, page = _connect_careers_cdp(p)
        for company in preferred:
            row = probe_company(page, company)
            results.append(row)
            # Stamp onto company row
            for c in companies:
                if c.get("name") == company.get("name"):
                    c["hasOpenings"] = bool(row.get("hasOpenings"))
                    c["openingsCount"] = int(row.get("openingsCount") or 0)
                    c["sampleOpenings"] = list(row.get("sampleOpenings") or [])[:5]
                    c["openingsProbedAt"] = datetime.now(timezone.utc).isoformat()
                    if c["hasOpenings"]:
                        # Boost numeric priority so LinkedIn/boards also prefer them
                        c["priority"] = min(int(c.get("priority") or 9), 1)
                        with_openings.append(c["name"])
                    break
            print(
                f"OPENINGS {row['company']}: count={row.get('openingsCount')} "
                f"has={row.get('hasOpenings')} err={row.get('error')}",
                flush=True,
            )

    data["companies"] = companies
    data.setdefault("meta", {})["lastOpeningsProbeAt"] = datetime.now(timezone.utc).isoformat()
    if persist:
        COMPANIES_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    report = {
        "ok": True,
        "probed": len(results),
        "withOpenings": sorted(set(with_openings)),
        "hintsAttached": hints_touched,
        "results": results,
        "finishedAt": datetime.now(timezone.utc).isoformat(),
    }
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report"] = str(REPORT)
    except Exception:
        local = _root / "artifacts" / "hitechcity-openings.json"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report"] = str(local)
    print(
        json.dumps(
            {
                "openingsProbe": True,
                "probed": report["probed"],
                "withOpenings": report["withOpenings"],
                "hintsAttached": hints_touched,
            }
        ),
        flush=True,
    )
    return report


if __name__ == "__main__":
    run(persist=True)
