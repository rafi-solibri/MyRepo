#!/usr/bin/env python3
"""Discover software / IT tenants at Madhapur / HITEC premium campuses.

Sources (best-effort; never wipe curated Priority-1 rows):
1. Full campus tenant catalog (Raheja / Knowledge City / Knowledge Park /
   RMZ Nexity·Skyview·Futura / Madhapur–HITEC peer parks) — every daily run
2. Live scrape of Mindspace REIT + Cityinfo Knowledge City / RMZ Skyview directories
3. Legacy DISCOVERY_SEEDS merge (subset / aliases)
4. LinkedIn *company-name* slug resolve when enabled (off by default)
5. Optional board-surface companies passed via env JSON

Writes:
  - merges new rows into tools/hitechcity/companies.json
  - /opt/cursor/artifacts/hitechcity-discovery.json
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from tools.hitechcity.campus_tenant_catalog import (
    CAMPUS_DEFINITIONS,
    catalog_candidates,
    fetch_web_directory_tenants,
)
from tools.hitechcity.filters import company_name_match

COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(
    os.environ.get(
        "HITECHCITY_DISCOVERY_REPORT",
        "/opt/cursor/artifacts/hitechcity-discovery.json",
    )
)
CDP = os.environ.get("HITECHCITY_CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")

# Known / commonly cited tenants to merge when missing (priority 2 unless noted).
# These are real employers at Madhapur / HITEC Grade-A campuses — NOT campus strings
# to paste into LinkedIn search ( "Knowledge City" / "Raheja" return nothing useful ).
DISCOVERY_SEEDS: list[dict[str, Any]] = [
    # Knowledge City / Octave
    {"name": "ServiceNow", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "servicenow", "priority": 2},
    {"name": "Wells Fargo", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "wells-fargo", "priority": 2},
    {"name": "Invesco", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "invesco", "priority": 2},
    {"name": "ValueLabs", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "valuelabs", "priority": 2},
    {"name": "Micron Technology", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "micron-technology", "priority": 2},
    {"name": "RealPage", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "realpage", "priority": 2},
    {"name": "Homes.com", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "homes-com", "priority": 2},
    {"name": "Darwinbox", "campuses": ["sattva-knowledge-city"], "linkedinSlug": "darwinbox", "priority": 2},
    # Knowledge Park
    {"name": "Virtusa", "campuses": ["sattva-knowledge-park", "mindspace-madhapur"], "linkedinSlug": "virtusa", "priority": 2},
    {"name": "Hexaware", "campuses": ["sattva-knowledge-park"], "linkedinSlug": "hexaware-technologies", "priority": 2},
    {"name": "Tech Mahindra", "campuses": ["sattva-knowledge-park", "mindspace-madhapur"], "linkedinSlug": "tech-mahindra", "priority": 2},
    # Raheja Mindspace Madhapur
    {"name": "ADP", "campuses": ["mindspace-madhapur"], "linkedinSlug": "adp", "priority": 2},
    {"name": "HighRadius", "campuses": ["mindspace-madhapur"], "linkedinSlug": "highradius", "priority": 1},
    {"name": "Progress Software", "campuses": ["mindspace-madhapur"], "linkedinSlug": "progress-software", "priority": 2},
    {"name": "OpenText", "campuses": ["mindspace-madhapur"], "linkedinSlug": "opentext", "priority": 2},
    {"name": "NCR Voyix", "campuses": ["mindspace-madhapur"], "linkedinSlug": "ncr-voyix", "priority": 2},
    {"name": "Broadridge", "campuses": ["mindspace-madhapur"], "linkedinSlug": "broadridge", "priority": 2},
    {"name": "S&P Global", "campuses": ["mindspace-madhapur"], "linkedinSlug": "s-and-p-global", "priority": 2},
    {"name": "Uber", "campuses": ["mindspace-madhapur"], "linkedinSlug": "uber-com", "priority": 2},
    {"name": "PayPal", "campuses": ["mindspace-madhapur"], "linkedinSlug": "paypal", "priority": 2},
    {"name": "Thomson Reuters", "campuses": ["mindspace-madhapur"], "linkedinSlug": "thomson-reuters", "priority": 2},
    {"name": "Infor", "campuses": ["mindspace-madhapur"], "linkedinSlug": "infor", "priority": 2},
    {"name": "Kony / Temenos", "campuses": ["mindspace-madhapur"], "linkedinSlug": "temenos", "priority": 3},
    {"name": "Capgemini", "campuses": ["mindspace-madhapur", "the-v"], "linkedinSlug": "capgemini", "priority": 2},
    {"name": "Infosys", "campuses": ["mindspace-madhapur"], "linkedinSlug": "infosys", "priority": 3},
    {"name": "Wipro", "campuses": ["mindspace-madhapur"], "linkedinSlug": "wipro", "priority": 3},
    {"name": "HCLTech", "campuses": ["mindspace-madhapur"], "linkedinSlug": "hcltech", "priority": 3},
    {"name": "Deloitte", "campuses": ["mindspace-madhapur", "the-v"], "linkedinSlug": "deloitte", "priority": 2},
    {"name": "Accenture", "campuses": ["mindspace-madhapur"], "linkedinSlug": "accenture", "priority": 2},
    {"name": "Cognizant", "campuses": ["mindspace-madhapur"], "linkedinSlug": "cognizant", "priority": 2},
    {"name": "IBM", "campuses": ["mindspace-madhapur"], "linkedinSlug": "ibm", "priority": 2},
    {"name": "LTIMindtree", "campuses": ["mindspace-madhapur"], "linkedinSlug": "ltimindtree", "priority": 2},
    {"name": "Mphasis", "campuses": ["mindspace-madhapur"], "linkedinSlug": "mphasis", "priority": 2},
    {"name": "Persistent Systems", "campuses": ["mindspace-madhapur"], "linkedinSlug": "persistent-systems", "priority": 2},
    {"name": "Cyient", "campuses": ["mindspace-madhapur"], "linkedinSlug": "cyient", "priority": 2},
    # The V / Cyber Pearl / peer
    {"name": "UnitedHealth Group", "campuses": ["dlf-cyber-city", "divyasree-orion"], "linkedinSlug": "unitedhealth-group", "priority": 2},
    {"name": "Novartis", "campuses": ["mindspace-madhapur"], "linkedinSlug": "novartis", "priority": 2},
    {"name": "Verizon", "campuses": ["the-v", "cyber-pearl"], "linkedinSlug": "verizon", "priority": 2},
    {"name": "Computer Sciences Corporation / DXC", "campuses": ["cyber-pearl"], "linkedinSlug": "dxc-technology", "priority": 3},
]

# LinkedIn company search by *employer name* (never campus / park / Raheja strings).
# Used only to resolve/refresh linkedinSlug for known tenants.
LI_COMPANY_NAME_QUERIES: list[str] = [
    "HighRadius Hyderabad",
    "ValueLabs Hyderabad",
    "ServiceNow Hyderabad",
    "Micron Technology Hyderabad",
    "ADP Hyderabad",
    "OpenText Hyderabad",
    "Broadridge Hyderabad",
    "Progress Software Hyderabad",
    "Darwinbox Hyderabad",
    "LTIMindtree Hyderabad",
    "Persistent Systems Hyderabad",
    "Cyient Hyderabad",
    "Mphasis Hyderabad",
    "RealPage Hyderabad",
]

SOFTWAREISH = re.compile(
    r"software|technology|technologies|systems|digital|cloud|cyber|data|"
    r"solutions|consulting|semiconductor|fintech|saas|platform|networks|"
    r"information|services|labs|electronics|computing",
    re.I,
)

# LinkedIn company-search noise: directories, communities, geo keywords mistaken for tenants.
JUNK_TENANT_RE = re.compile(
    r"(?i)^software\s+companies?\b|"
    r"\b(tech\s+)?community\b|"
    r"\b(meetup|user\s*group|chamber\s+of\s+commerce)\b|"
    r"\b(erbil|kurdistan)\b|"
    r"\bhiring\s+for\b|"
    r"^companies?\s+in\b|"
    r"^\d+$|"
    r"city\s*scanner|city\s*tech\s*consultants|knowledge\s*bridge\s*solutions|"
    r"software\s*development\s*aegona|coenterprise|\bsofteq\b"
)


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s[:64]


def _is_junk_tenant(name: str, slug: str = "") -> bool:
    """Reject LinkedIn directory / community hits that are not campus employers."""
    blob = f"{name or ''} {slug or ''}".strip()
    if not blob:
        return True
    if JUNK_TENANT_RE.search(name or "") or JUNK_TENANT_RE.search(slug or ""):
        return True
    # Slug-shaped search leftovers: software-companies-*, *-tech-community
    if re.search(r"(?i)software-companies|tech-community|user-group", slug or ""):
        return True
    return False


def _already_listed(companies: list[dict], name: str, slug: str = "") -> bool:
    for c in companies:
        if company_name_match(name, c.get("name") or ""):
            return True
        if slug and (c.get("linkedinSlug") or "").lower() == slug.lower():
            return True
    return False


def _merge_candidate(companies: list[dict], cand: dict[str, Any], source: str) -> str | None:
    name = (cand.get("name") or "").strip()
    if not name or len(name) < 2:
        return None
    slug = (cand.get("linkedinSlug") or _slugify(name)).strip()
    # Never add junk from LinkedIn/board discovery; seeds may still curate intentionally.
    if source != "seed" and _is_junk_tenant(name, slug):
        return None
    if _already_listed(companies, name, slug):
        # Expand campuses if we learn new ones. Fill empty careersUrls from
        # catalog seeds — never wipe Priority-1 curated portals.
        for c in companies:
            if company_name_match(name, c.get("name") or "") or (
                slug and (c.get("linkedinSlug") or "").lower() == slug.lower()
            ):
                camps = list(c.get("campuses") or [])
                for x in cand.get("campuses") or []:
                    if x not in camps:
                        camps.append(x)
                c["campuses"] = camps
                incoming = [u for u in (cand.get("careersUrls") or []) if isinstance(u, str) and u.strip()]
                if incoming and not (c.get("careersUrls") or []):
                    c["careersUrls"] = incoming
                return "updated"
        return None
    row = {
        "name": name,
        "campuses": list(cand.get("campuses") or ["mindspace-madhapur"]),
        "linkedinSlug": slug,
        # Empty until a real careers URL is curated — LinkedIn company jobs still work.
        "careersUrls": list(cand.get("careersUrls") or []),
        "priority": int(cand.get("priority") or 2),
        "source": source,
        "discoveredAt": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    companies.append(row)
    return "added"


def discover_from_seeds(companies: list[dict]) -> dict[str, list[str]]:
    added, updated = [], []
    for seed in DISCOVERY_SEEDS:
        status = _merge_candidate(companies, seed, "seed")
        if status == "added":
            added.append(seed["name"])
        elif status == "updated":
            updated.append(seed["name"])
    return {"added": added, "updated": updated}


def discover_from_campus_catalog(companies: list[dict]) -> dict[str, list[str]]:
    """Merge full Raheja / KC / KP / Madhapur–HITEC tenant catalog every run."""
    added, updated = [], []
    for cand in catalog_candidates():
        status = _merge_candidate(companies, cand, "campus_catalog")
        if status == "added":
            added.append(cand["name"])
        elif status == "updated":
            updated.append(cand["name"])
    return {"added": added, "updated": updated}


def discover_from_web_directories(companies: list[dict]) -> dict[str, Any]:
    """Live-scrape Mindspace + Cityinfo directories (soft-fail)."""
    if os.environ.get("HITECHCITY_DISCOVERY_WEB", "1") != "1":
        return {"added": [], "updated": [], "skipped": True}
    found, meta = fetch_web_directory_tenants()
    added, updated = [], []
    for cand in found:
        status = _merge_candidate(companies, cand, "web_directory")
        if status == "added":
            added.append(cand["name"])
        elif status == "updated":
            updated.append(cand["name"])
    return {
        "added": added,
        "updated": updated,
        "sources": meta.get("sources") or [],
        "errors": meta.get("errors") or [],
    }


def discover_from_linkedin(companies: list[dict]) -> dict[str, Any]:
    """Resolve tenants via LinkedIn *company-name* search when session is live.

    Never search campus strings (Knowledge City / Raheja / Mindspace park names) —
    those queries do not return employer pages. Seeds + employer-name queries only.
    """
    out: dict[str, Any] = {"added": [], "updated": [], "searches": 0, "error": None}
    if os.environ.get("HITECHCITY_DISCOVERY_LINKEDIN", "0") != "1":
        out["skipped"] = True
        out["reason"] = "HITECHCITY_DISCOVERY_LINKEDIN=0 (seed-only; avoid company-search without job clicks)"
        return out
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        out["error"] = f"playwright:{e}"
        return out

    # Prefer exact employer names from seeds (slug refresh) + curated name queries.
    queries: list[tuple[str, list[str]]] = []
    for seed in DISCOVERY_SEEDS:
        name = (seed.get("name") or "").strip()
        if not name:
            continue
        # Drop slash aliases for search ("Kony / Temenos" → "Temenos")
        q = re.split(r"\s*/\s*", name)[-1].strip()
        queries.append((q, list(seed.get("campuses") or ["mindspace-madhapur"])))
    for q in LI_COMPANY_NAME_QUERIES:
        queries.append((q, ["mindspace-madhapur"]))

    # Dedupe queries (keep first campus tagging).
    seen_q: set[str] = set()
    uniq: list[tuple[str, list[str]]] = []
    for q, campuses in queries:
        key = q.lower()
        if key in seen_q:
            continue
        seen_q.add(key)
        uniq.append((q, campuses))

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP, timeout=20_000)
            context = browser.contexts[0]
            page = context.new_page()
            page.set_default_timeout(45000)
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(1.5)
            if re.search(r"/login|/checkpoint|sign.in", page.url or "", re.I):
                out["error"] = "linkedin_login_required"
                page.close()
                return out

            for q, campuses in uniq[:24]:
                out["searches"] += 1
                # Pin Hyderabad HQ geo so company hits stay India/Hyd-relevant.
                url = (
                    "https://www.linkedin.com/search/results/companies/"
                    f"?keywords={quote(q)}&origin=GLOBAL_SEARCH_HEADER"
                    f"&companyHqGeo={quote('[\"105556991\"]')}"
                )
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    time.sleep(2.0)
                except Exception:
                    continue
                try:
                    rows = page.evaluate(
                        """() => {
                          const out = [];
                          const seen = new Set();
                          for (const a of document.querySelectorAll('a[href*="/company/"]')) {
                            const href = a.href || '';
                            const m = href.match(/\\/company\\/([^/?#]+)/i);
                            if (!m) continue;
                            const slug = decodeURIComponent(m[1]).replace(/\\/$/, '');
                            if (!slug || seen.has(slug)) continue;
                            let name = (a.innerText || a.getAttribute('aria-label') || '').trim().split('\\n')[0];
                            name = name.replace(/\\s+/g, ' ').slice(0, 80);
                            if (!name || name.length < 2) name = slug.replace(/-/g, ' ');
                            seen.add(slug);
                            out.push({ name, slug });
                            if (out.length >= 8) break;
                          }
                          return out;
                        }"""
                    )
                except Exception:
                    rows = []
                # Prefer the first hit that name-matches the query (not random geo noise).
                q_core = re.sub(r"\bhyderabad\b", "", q, flags=re.I).strip()
                picked = []
                for r in rows or []:
                    name = (r.get("name") or "").strip()
                    slug = (r.get("slug") or "").strip()
                    if _is_junk_tenant(name, slug):
                        continue
                    if company_name_match(q_core, name) or company_name_match(q_core, slug.replace("-", " ")):
                        picked.append(r)
                if not picked and rows:
                    # Fall back to top hit only when query already looks like a brand.
                    top = rows[0]
                    if not _is_junk_tenant(top.get("name") or "", top.get("slug") or ""):
                        picked = [top]
                for r in picked[:2]:
                    name = (r.get("name") or "").strip()
                    slug = (r.get("slug") or "").strip()
                    status = _merge_candidate(
                        companies,
                        {
                            "name": name,
                            "linkedinSlug": slug,
                            "campuses": campuses,
                            "priority": 2,
                        },
                        "linkedin_company_name",
                    )
                    if status == "added":
                        out["added"].append(name)
                    elif status == "updated":
                        out["updated"].append(name)
            page.close()
    except Exception as e:
        out["error"] = str(e)[:400]
    return out


def discover_from_board_hints(companies: list[dict]) -> dict[str, list[str]]:
    """Merge companies surfaced by boards in a prior artifact (optional)."""
    added, updated = [], []
    hint = os.environ.get("HITECHCITY_BOARD_DISCOVERY_JSON")
    if not hint or not Path(hint).is_file():
        return {"added": added, "updated": updated}
    try:
        data = json.loads(Path(hint).read_text(encoding="utf-8"))
    except Exception:
        return {"added": added, "updated": updated}
    for row in data if isinstance(data, list) else data.get("companies") or []:
        if not isinstance(row, dict):
            continue
        status = _merge_candidate(companies, row, "board_hint")
        if status == "added":
            added.append(row.get("name") or "")
        elif status == "updated":
            updated.append(row.get("name") or "")
    return {"added": added, "updated": updated}


def prune_junk_tenants(companies: list[dict]) -> list[str]:
    """Drop previously merged LinkedIn junk (never remove priority-1 curated rows)."""
    removed: list[str] = []
    keep: list[dict] = []
    for c in companies:
        name = c.get("name") or ""
        slug = c.get("linkedinSlug") or ""
        priority = int(c.get("priority") or 9)
        source = (c.get("source") or "").lower()
        if priority <= 1:
            keep.append(c)
            continue
        # Auto-prune discovery noise; never remove priority-1 curated rows.
        if _is_junk_tenant(name, slug) and (
            source in (
                "linkedin_search",
                "linkedin_company_name",
                "board_hint",
                "web_directory",
                "campus_catalog",
                "seed",
                "",
            )
            or priority >= 2
        ):
            removed.append(name)
            continue
        keep.append(c)
    companies[:] = keep
    return removed


def run(persist: bool = True) -> dict[str, Any]:
    if os.environ.get("HITECHCITY_DISCOVERY", "1") != "1":
        return {"ok": True, "skipped": True, "reason": "HITECHCITY_DISCOVERY=0"}

    data = json.loads(COMPANIES_PATH.read_text(encoding="utf-8"))
    companies = list(data.get("companies") or [])
    before = len(companies)
    pruned = prune_junk_tenants(companies)

    catalog = discover_from_campus_catalog(companies)
    web = discover_from_web_directories(companies)
    seed = discover_from_seeds(companies)
    li = discover_from_linkedin(companies)
    board = discover_from_board_hints(companies)
    # Second prune after merges (web/LI may reintroduce junk aliases).
    pruned2 = prune_junk_tenants(companies)
    pruned = sorted(set(pruned + pruned2))

    # Stable sort: priority then name
    companies.sort(key=lambda c: (int(c.get("priority") or 9), (c.get("name") or "").lower()))
    data["companies"] = companies
    # Keep campus metadata in sync (RMZ Nexity / Skyview / Futura + preferred parks).
    data["campuses"] = [dict(row) for row in CAMPUS_DEFINITIONS]
    data.setdefault("meta", {})["lastDiscoveryAt"] = datetime.now(timezone.utc).isoformat()
    data["meta"]["focus"] = (
        "Premium Madhapur / HITEC City campuses — Knowledge City, Knowledge Park, "
        "Raheja Mindspace, RMZ Nexity / Skyview / Futura, The V, Cyber Pearl and peer Grade-A"
    )
    data["meta"]["preferredHomeCampuses"] = [
        "sattva-knowledge-city",
        "sattva-knowledge-park",
        "mindspace-madhapur",
        "rmz-nexity",
        "rmz-skyview",
        "rmz-futura",
    ]
    data["meta"]["discoveryMode"] = (
        "campus_catalog+web_directories+seeds"
        "+linkedin_optional+board_hints"
    )

    if persist:
        COMPANIES_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    added_all = (
        catalog["added"]
        + web.get("added", [])
        + seed["added"]
        + li.get("added", [])
        + board["added"]
    )
    updated_all = (
        catalog["updated"]
        + web.get("updated", [])
        + seed["updated"]
        + li.get("updated", [])
        + board["updated"]
    )
    report = {
        "ok": True,
        "startedAt": datetime.now(timezone.utc).isoformat(),
        "beforeCount": before,
        "afterCount": len(companies),
        "prunedJunk": pruned,
        "campusCatalog": {"added": catalog["added"], "updated": catalog["updated"]},
        "webDirectories": {
            "added": web.get("added") or [],
            "updated": web.get("updated") or [],
            "sources": web.get("sources") or [],
            "errors": web.get("errors") or [],
            "skipped": web.get("skipped"),
        },
        "seed": seed,
        "linkedin": {k: v for k, v in li.items() if k != "error" or v},
        "linkedinError": li.get("error"),
        "boardHints": board,
        "added": sorted(set(added_all)),
        "updated": sorted(set(updated_all)),
        "companiesPath": str(COMPANIES_PATH),
    }
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    except Exception:
        local = Path(__file__).resolve().parents[2] / "artifacts" / "hitechcity-discovery.json"
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(json.dumps(report, indent=2), encoding="utf-8")
        report["report"] = str(local)
    else:
        report["report"] = str(REPORT)
    print(
        json.dumps(
            {
                "discovery": True,
                "added": len(report["added"]),
                "updated": len(report["updated"]),
                "total": report["afterCount"],
                "linkedinError": report.get("linkedinError"),
            }
        ),
        flush=True,
    )
    return report


if __name__ == "__main__":
    run()
