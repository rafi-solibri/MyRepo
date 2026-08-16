#!/usr/bin/env python3
"""Curated + live campus tenant catalogs for Madhapur / HITEC City.

Every daily run merges these into companies.json so Raheja Mindspace,
Knowledge City, Knowledge Park, and peer Madhapur / HITEC Grade-A parks
stay covered — we do not rely on LinkedIn campus-name searches.

Sources:
  - Static research catalog (REIT top tenants, Cityinfo parcel directories, news)
  - Live HTTP scrape of Mindspace REIT Madhapur page + Cityinfo KC parcels
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from html import unescape
from typing import Any

# Canonical employer display name → LinkedIn slug hint (optional).
SLUG_HINTS: dict[str, str] = {
    "HighRadius": "highradius",
    "Larsen & Toubro": "larsen-toubro",
    "BA Continuum": "bank-of-america",
    "Bank of America": "bank-of-america",
    "WeWork": "wework",
    "Smartworks": "smartworks",
    "Tablespace": "tablespace",
    "PwC": "pwc",
    "BluJay Solutions": "blujay-solutions",
    "MTX Group": "mtx",
    "Silicon Labs": "silicon-laboratories",
    "MathWorks": "mathworks",
    "Chubb": "chubb",
    "Vanguard": "vanguard",
    "InvoiceCloud": "invoicecloud",
    "Bayer": "bayer",
    "Rackspace": "rackspace",
    "Postman": "postman",
    "Macquarie": "macquarie",
    "Southwest Airlines": "southwest-airlines",
    "Pegasystems": "pegasystems",
    "Parexel": "parexel",
    "UTC": "rtx",
    "NTT DATA": "ntt-data",
    "Salesforce": "salesforce",
    "ZenQ": "zenq",
    "Winshuttle": "winshuttle",
}

# Normalize scraped / seed aliases → one company row name.
NAME_ALIASES: dict[str, str] = {
    "highradius": "HighRadius",
    "l&t": "Larsen & Toubro",
    "larsen & toubro": "Larsen & Toubro",
    "ba continuum": "BA Continuum",
    "wework": "WeWork",
    "w e work": "WeWork",
    "pricewaterhousecoopers service delivery center (bangalore)": "PwC",
    "pricewaterhousecoopers": "PwC",
    "pwc": "PwC",
    "xilinx india technology services": "AMD",
    "xilinx": "AMD",
    "blue yonder india (jda software)": "Blue Yonder",
    "blue yonder india": "Blue Yonder",
    "blujay solutions (india)": "BluJay Solutions",
    "blujay solutions": "BluJay Solutions",
    "mtx it consulting services": "MTX Group",
    "mtx": "MTX Group",
    "jones lang lasalle property consultants india (jll)": "JLL",
    "jones lang lasalle": "JLL",
    "intel technology india": "Intel",
    "apple india": "Apple",
    "gartner india research & advisory services": "Gartner",
    "mcafee software india": "McAfee",
    "qentelli solutions": "Qentelli",
    "mathworks india": "MathWorks",
    "mathworks": "MathWorks",
    "silabs india (redpine signals)": "Silicon Labs",
    "silabs india": "Silicon Labs",
    "redpine signals": "Silicon Labs",
    "redbrick offices co-working": "Redbrick Offices",
    "j.p. morgan india": "JPMorgan Chase",
    "j.p. morgan": "JPMorgan Chase",
    "jpmorgan chase": "JPMorgan Chase",
    "chubb business services india": "Chubb",
    "chubb business services india pvt ltd": "Chubb",
    "unitedhealth group": "UnitedHealth Group",
    "uhg": "UnitedHealth Group",
    "ncr": "NCR Voyix",
    "ncr voyix": "NCR Voyix",
    "qualcomm": "Qualcomm",
    "cognizant": "Cognizant",
    "verizon": "Verizon",
    "ibm": "IBM",
    "amd": "AMD",
    "wipro": "Wipro",
    "accenture": "Accenture",
    "parexel": "Parexel",
    "pegasystems": "Pegasystems",
    "pega": "Pegasystems",
}

# Skip non-employer / non-IT noise from directories.
SKIP_TENANT_RE = re.compile(
    r"(?i)^(otis|elevator|atm|bank branch|food\s*court|creche|medical|"
    r"on the basis|total tenants|committed occupancy|leasable|"
    r"and\s+\d+\s+more)\b|"
    r"\b(coworking only)\b"
)

# Software / GCC / product / consulting — prefer these when pruning noise.
SOFTWAREISH = re.compile(
    r"(?i)software|technolog|systems|digital|cloud|cyber|data|solutions|"
    r"consulting|semiconductor|fintech|saas|platform|networks|labs|"
    r"electronics|computing|bank|capital|insurance|pharma|health|"
    r"analytics|services|group|corp|inc|ltd|llc|pvt|voyix|radius|"
    r"works|space|page|box|now|soft|ware|com$"
)


def canonicalize_tenant_name(raw: str) -> str | None:
    name = re.sub(r"\s+", " ", (raw or "").strip(" ,.;|"))
    if not name or len(name) < 2:
        return None
    if SKIP_TENANT_RE.search(name):
        return None
    key = name.lower()
    if key in NAME_ALIASES:
        return NAME_ALIASES[key]
    # Strip trailing India / Pvt Ltd noise for alias lookup.
    stripped = re.sub(
        r"(?i)\s*(india|pvt\.?\s*ltd\.?|private\s+limited|ltd\.?)\s*$",
        "",
        name,
    ).strip()
    if stripped.lower() in NAME_ALIASES:
        return NAME_ALIASES[stripped.lower()]
    return name


def tenant_row(name: str, campuses: list[str], priority: int = 2) -> dict[str, Any]:
    canon = canonicalize_tenant_name(name) or name
    slug = SLUG_HINTS.get(canon) or re.sub(r"[^a-z0-9]+", "-", canon.lower()).strip("-")[:64]
    return {
        "name": canon,
        "campuses": list(campuses),
        "linkedinSlug": slug,
        "priority": priority,
    }


# ---------------------------------------------------------------------------
# Static catalog — refreshed from REIT / Cityinfo / leasing news research.
# Merged every daily run; never wipes Priority-1 curated careers URLs.
# ---------------------------------------------------------------------------

CAMPUS_TENANT_CATALOG: list[dict[str, Any]] = [
    # —— Raheja Mindspace Madhapur (REIT top tenants + valuation roster) ——
    tenant_row("Cognizant", ["mindspace-madhapur"], 1),
    tenant_row("Verizon", ["mindspace-madhapur", "the-v", "cyber-pearl"], 1),
    tenant_row("BA Continuum", ["mindspace-madhapur"], 2),
    tenant_row("Tablespace", ["mindspace-madhapur"], 3),
    tenant_row("Smartworks", ["mindspace-madhapur"], 3),
    tenant_row("Qualcomm", ["mindspace-madhapur"], 1),
    tenant_row("Larsen & Toubro", ["mindspace-madhapur"], 2),
    tenant_row("AMD", ["mindspace-madhapur", "sattva-knowledge-city"], 1),
    tenant_row("HighRadius", ["mindspace-madhapur"], 1),
    tenant_row("WeWork", ["mindspace-madhapur"], 3),
    tenant_row("IBM", ["mindspace-madhapur"], 1),
    tenant_row("UnitedHealth Group", ["mindspace-madhapur", "dlf-cyber-city", "divyasree-orion"], 2),
    tenant_row("NCR Voyix", ["mindspace-madhapur"], 2),
    tenant_row("Parexel", ["mindspace-madhapur"], 2),
    tenant_row("Pegasystems", ["mindspace-madhapur"], 2),
    tenant_row("UTC", ["mindspace-madhapur"], 3),
    tenant_row("Wipro", ["mindspace-madhapur"], 2),
    tenant_row("Accenture", ["mindspace-madhapur"], 2),
    tenant_row("ADP", ["mindspace-madhapur"], 2),
    tenant_row("OpenText", ["mindspace-madhapur"], 2),
    tenant_row("Broadridge", ["mindspace-madhapur"], 2),
    tenant_row("Progress Software", ["mindspace-madhapur"], 2),
    tenant_row("S&P Global", ["mindspace-madhapur"], 2),
    tenant_row("Uber", ["mindspace-madhapur"], 2),
    tenant_row("PayPal", ["mindspace-madhapur"], 2),
    tenant_row("Thomson Reuters", ["mindspace-madhapur"], 2),
    tenant_row("Infor", ["mindspace-madhapur"], 2),
    tenant_row("Deloitte", ["mindspace-madhapur", "the-v"], 2),
    tenant_row("Capgemini", ["mindspace-madhapur", "the-v"], 2),
    tenant_row("Infosys", ["mindspace-madhapur"], 3),
    tenant_row("HCLTech", ["mindspace-madhapur"], 3),
    tenant_row("LTIMindtree", ["mindspace-madhapur"], 2),
    tenant_row("Mphasis", ["mindspace-madhapur"], 2),
    tenant_row("Persistent Systems", ["mindspace-madhapur"], 2),
    tenant_row("Cyient", ["mindspace-madhapur"], 2),
    tenant_row("Novartis", ["mindspace-madhapur", "sattva-knowledge-city"], 2),
    tenant_row("Amazon", ["mindspace-madhapur"], 1),
    tenant_row("Microsoft", ["mindspace-madhapur", "sattva-knowledge-city", "the-v"], 1),
    tenant_row("JPMorgan Chase", ["mindspace-madhapur", "sattva-knowledge-city"], 1),
    tenant_row("Salesforce", ["mindspace-madhapur", "cyber-pearl"], 1),
    tenant_row("Meta", ["mindspace-madhapur"], 1),
    # —— Sattva Knowledge City / Octave / Argus ——
    tenant_row("Apple", ["sattva-knowledge-city"], 1),
    tenant_row("Oracle", ["sattva-knowledge-city"], 1),
    tenant_row("Intel", ["sattva-knowledge-city"], 1),
    tenant_row("ServiceNow", ["sattva-knowledge-city"], 1),
    tenant_row("Wells Fargo", ["sattva-knowledge-city"], 2),
    tenant_row("Invesco", ["sattva-knowledge-city"], 2),
    tenant_row("ValueLabs", ["sattva-knowledge-city"], 2),
    tenant_row("Micron Technology", ["sattva-knowledge-city"], 2),
    tenant_row("RealPage", ["sattva-knowledge-city"], 2),
    tenant_row("Homes.com", ["sattva-knowledge-city"], 2),
    tenant_row("Darwinbox", ["sattva-knowledge-city"], 2),
    tenant_row("Blue Yonder", ["sattva-knowledge-city"], 1),
    tenant_row("BluJay Solutions", ["sattva-knowledge-city"], 2),
    tenant_row("MTX Group", ["sattva-knowledge-city"], 2),
    tenant_row("JLL", ["sattva-knowledge-city"], 3),
    tenant_row("PwC", ["sattva-knowledge-city"], 2),
    tenant_row("Gartner", ["sattva-knowledge-city"], 2),
    tenant_row("McAfee", ["sattva-knowledge-city"], 2),
    tenant_row("Qentelli", ["sattva-knowledge-city"], 2),
    tenant_row("MathWorks", ["sattva-knowledge-city"], 2),
    tenant_row("Silicon Labs", ["sattva-knowledge-city"], 2),
    tenant_row("Redbrick Offices", ["sattva-knowledge-city"], 3),
    tenant_row("Goldman Sachs", ["sattva-knowledge-city"], 1),
    tenant_row("Bayer", ["sattva-knowledge-city"], 2),
    tenant_row("Rackspace", ["sattva-knowledge-city"], 2),
    tenant_row("Chubb", ["sattva-knowledge-city"], 2),
    tenant_row("Postman", ["sattva-knowledge-city"], 2),
    tenant_row("Macquarie", ["sattva-knowledge-city"], 2),
    tenant_row("Celonis", ["sattva-knowledge-city"], 2),
    # —— Sattva Knowledge Park ——
    tenant_row("Virtusa", ["sattva-knowledge-park", "mindspace-madhapur"], 2),
    tenant_row("Hexaware", ["sattva-knowledge-park"], 2),
    tenant_row("Tech Mahindra", ["sattva-knowledge-park", "mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("Vanguard", ["sattva-knowledge-park"], 1),
    tenant_row("InvoiceCloud", ["sattva-knowledge-park"], 2),
    # —— The V / Cyber Pearl / peer Madhapur–HITEC ——
    tenant_row("TCS", ["the-v"], 2),
    tenant_row("NTT DATA", ["cyber-pearl"], 2),
    tenant_row("ZenQ", ["cyber-pearl"], 3),
    tenant_row("Winshuttle", ["cyber-pearl"], 3),
    tenant_row("DXC Technology", ["cyber-pearl", "mindspace-madhapur"], 3),
    tenant_row("Optum", ["dlf-cyber-city", "divyasree-orion"], 2),
    tenant_row("Palo Alto Networks", ["dlf-cyber-city", "divyasree-orion"], 1),
    tenant_row("GE Vernova", ["dlf-cyber-city", "mindspace-madhapur"], 2),
    tenant_row("Blackbaud", ["mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("Hyland", ["mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("ModMed", ["mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("Solera", ["mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("Experian", ["mindspace-madhapur", "cyber-pearl"], 2),
    tenant_row("Fiserv", ["mindspace-madhapur"], 2),
    tenant_row("Storable", ["mindspace-madhapur"], 2),
]

# Live directory endpoints scraped every daily discovery run.
WEB_DIRECTORY_SOURCES: list[dict[str, Any]] = [
    {
        "id": "mindspace-madhapur-reit",
        "url": "https://www.mindspacereit.com/portfolio/hyderabad-mindspace-madhapur",
        "campuses": ["mindspace-madhapur"],
        "kind": "mindspace_top_tenants",
        "priority": 2,
    },
    {
        "id": "kc-octave-4a",
        "url": (
            "https://properties.cityinfoservices.com/"
            "salarpuria-sattva-knowledge-city-parcel-4a-octave-hitec-city-hyderabad/mjfoaj4/pjd"
        ),
        "campuses": ["sattva-knowledge-city"],
        "kind": "cityinfo_tenants_sentence",
        "priority": 2,
    },
    {
        "id": "kc-octave-4b",
        "url": (
            "https://properties.cityinfoservices.com/"
            "salarpuria-sattva-knowledge-city-parcel-4b-octave-hitec-city-hyderabad/r2vg43i/pjd"
        ),
        "campuses": ["sattva-knowledge-city"],
        "kind": "cityinfo_tenants_sentence",
        "priority": 2,
    },
]


def _http_get(url: str, timeout: float = 25.0) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; HitechCityCampusDiscovery/1.0)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")


def _parse_mindspace_top_tenants(html: str) -> list[str]:
    m = re.search(
        r"Top Tenants(.*?)(?:Location Highlights|About Us|Facilities/Amenities)",
        html,
        re.I | re.S,
    )
    chunk = m.group(1) if m else ""
    text = re.sub(r"<script[\s\S]*?</script>", " ", chunk)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = unescape(text)
    out: list[str] = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip(" ,.;")
        if not line or len(line) > 60:
            continue
        if re.search(r"(?i)gross rental|basis of|%|amenit", line):
            continue
        canon = canonicalize_tenant_name(line)
        if canon:
            out.append(canon)
    return out


def _parse_cityinfo_tenants(html: str) -> list[str]:
    text = unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)))
    m = re.search(
        r"current tenants? of this building (?:is|are)\s+([^.]+)",
        text,
        re.I,
    )
    if not m:
        return []
    blob = m.group(1)
    # Split on commas / " and " (incl. Oxford comma ", and ").
    parts = re.split(r"\s*,\s*|\s+and\s+", blob)
    out: list[str] = []
    for p in parts:
        p = re.sub(r"(?i)^\s*and\s+", "", p).strip()
        canon = canonicalize_tenant_name(p)
        if canon:
            out.append(canon)
    return out


def fetch_web_directory_tenants() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Scrape public campus directory pages. Soft-fail per URL."""
    found: list[dict[str, Any]] = []
    meta: dict[str, Any] = {"sources": [], "errors": []}
    for src in WEB_DIRECTORY_SOURCES:
        entry: dict[str, Any] = {"id": src["id"], "url": src["url"], "names": []}
        try:
            html = _http_get(src["url"])
            if src["kind"] == "mindspace_top_tenants":
                names = _parse_mindspace_top_tenants(html)
            else:
                names = _parse_cityinfo_tenants(html)
            entry["names"] = names
            for name in names:
                found.append(
                    tenant_row(name, list(src["campuses"]), int(src.get("priority") or 2))
                )
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
            entry["error"] = str(e)[:240]
            meta["errors"].append(entry)
        meta["sources"].append(entry)
    return found, meta


def catalog_candidates() -> list[dict[str, Any]]:
    """Static catalog rows for daily merge."""
    return [dict(row) for row in CAMPUS_TENANT_CATALOG]
