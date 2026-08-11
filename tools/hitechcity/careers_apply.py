#!/usr/bin/env python3
"""Scan company career portals for Hyd senior .NET/architect roles and apply."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from playwright.sync_api import Page, sync_playwright

from tools.hitechcity.ats_fill import attempt_ats_apply, blocked_wall, try_click_named
from tools.hitechcity.filters import (
    location_or_campus_ok,
    prefer_dotnet,
    skip_reason,
    title_matches_senior_stack,
)

CDP = os.environ.get("HITECHCITY_CDP") or os.environ.get("LINKEDIN_CDP", "http://127.0.0.1:9222")
COMPANIES_PATH = Path(__file__).with_name("companies.json")
REPORT = Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))
MAX_PER_COMPANY = int(os.environ.get("HITECHCITY_MAX_PER_COMPANY", "4"))
MAX_COMPANIES = int(os.environ.get("HITECHCITY_MAX_COMPANIES", "18"))
TIME_CAP_S = int(os.environ.get("HITECHCITY_ATS_TIME_CAP_S", "180"))

TITLE_HINT = re.compile(
    r"architect|technical lead|tech lead|engineering manager|principal|staff|"
    r"\.net|dotnet|azure|cloud architect|solution",
    re.I,
)
LOC_HINT = re.compile(
    r"hyderabad|telangana|madhapur|hitec|hitech|gachibowli|raidurg|india|remote|wfh",
    re.I,
)
BAD_LOC_HINT = re.compile(
    r"\b(austin|seattle|sunnyvale|st\.?\s*louis|london|new york|toronto|dublin|"
    r"bengaluru|bangalore|pune|chennai|mumbai|noida|gurgaon)\b",
    re.I,
)
AUTH_HOST = re.compile(
    r"passport\.amazon\.jobs|login\.microsoftonline|accounts\.google|"
    r"auth\.|signin\.|sso\.|okta\.com|login\.microsoft",
    re.I,
)


@dataclass
class CareersReport:
    startedAt: str
    finishedAt: str = ""
    applied: list[dict[str, Any]] = field(default_factory=list)
    blocked: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    scanned: list[dict[str, Any]] = field(default_factory=list)


def load_companies() -> list[dict[str, Any]]:
    data = json.loads(COMPANIES_PATH.read_text())
    companies = sorted(data.get("companies", []), key=lambda c: (c.get("priority", 9), c.get("name", "")))
    return companies


def extract_job_links(page: Page, company: str) -> list[dict[str, str]]:
    jobs: list[dict[str, str]] = []
    try:
        raw = page.evaluate(
            """() => {
              const out = [];
              const seen = new Set();
              const anchors = [...document.querySelectorAll('a[href]')];
              for (const a of anchors) {
                const href = a.href || '';
                const text = (a.innerText || a.textContent || '').trim().replace(/\\s+/g, ' ');
                if (!text || text.length < 8 || text.length > 140) continue;
                const h = href.toLowerCase();
                const looksJob = /job|career|requisition|opening|position|gh_jid|lever|workday|smartrecruiters|icims|taleo|greenhouse/.test(h)
                  || /\\/jobs?\\//.test(h);
                if (!looksJob) continue;
                if (seen.has(href)) continue;
                seen.add(href);
                out.push({ href, text });
                if (out.length >= 40) break;
              }
              return out;
            }"""
        )
    except Exception:
        raw = []
    for item in raw or []:
        text = item.get("text") or ""
        href = item.get("href") or ""
        if not TITLE_HINT.search(text):
            continue
        reason = skip_reason(text, company)
        if reason:
            continue
        if not title_matches_senior_stack(text) and not prefer_dotnet(text):
            continue
        # Prefer Hyd/India/remote signals in card text; skip clear non-Hyd cities.
        if BAD_LOC_HINT.search(text) and not LOC_HINT.search(text):
            continue
        jobs.append({"role": text, "url": href, "company": company})
    return jobs


def apply_job(page: Page, job: dict[str, str], campus: str) -> dict[str, Any]:
    row = {
        "company": job["company"],
        "role": job["role"],
        "url": job["url"],
        "campus": campus,
        "path": "company-careers",
        "status": "blocked",
        "reason": "",
    }
    print(f"CAREERS OPEN {job['company']} | {job['role'][:80]}", flush=True)
    try:
        page.goto(job["url"], wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        row["reason"] = f"nav_error:{e}"
        return row
    time.sleep(2.0)
    if AUTH_HOST.search(page.url or ""):
        row["reason"] = "login/account wall"
        row["finalUrl"] = page.url
        return row
    wall = blocked_wall(page)
    if wall:
        row["reason"] = wall
        row["finalUrl"] = page.url
        return row

    # Location / campus check from page top
    try:
        snip = page.locator("body").inner_text()[:2500]
    except Exception:
        snip = ""
    role_loc = f"{job.get('role','')} {snip[:500]}"
    if BAD_LOC_HINT.search(role_loc) and not LOC_HINT.search(role_loc):
        row["status"] = "skipped"
        row["reason"] = "location_non_hyd_city"
        row["finalUrl"] = page.url
        return row
    if not location_or_campus_ok(snip[:400], "", snip):
        # Still allow if company is on our campus list and page mentions India / Hyderabad weakly
        if not re.search(r"hyderabad|telangana|india|madhapur|hitec|hitech|gachibowli|remote|wfh", snip, re.I):
            row["status"] = "skipped"
            row["reason"] = "location_not_hyd_or_campus"
            row["finalUrl"] = page.url
            return row

    # Click apply if listing page
    try_click_named(page, ("Apply now", "Apply Now", "Apply", "Start application", "I'm interested"))
    time.sleep(1.5)
    status, reason = attempt_ats_apply(page, time_cap_s=TIME_CAP_S)
    row["status"] = status
    row["reason"] = reason
    row["finalUrl"] = page.url
    return row


def run(companies: list[dict[str, Any]] | None = None) -> CareersReport:
    companies = companies or load_companies()
    companies = companies[:MAX_COMPANIES]
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    seen_urls: set[str] = set()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        page.set_default_timeout(45000)

        for company in companies:
            name = company["name"]
            campuses = ",".join(company.get("campuses") or [])
            urls = company.get("careersUrls") or []
            print(f"CAREERS SCAN {name}", flush=True)
            company_applied = 0
            for url in urls:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=75000)
                except Exception as e:
                    report.blocked.append({"company": name, "url": url, "reason": f"scan_nav:{e}"})
                    continue
                time.sleep(2.2)
                jobs = extract_job_links(page, name)
                report.scanned.append({"company": name, "url": url, "jobCount": len(jobs)})
                for job in jobs:
                    if job["url"] in seen_urls:
                        continue
                    seen_urls.add(job["url"])
                    if company_applied >= MAX_PER_COMPANY:
                        break
                    result = apply_job(page, job, campuses)
                    if result["status"] == "applied":
                        report.applied.append(result)
                        company_applied += 1
                    elif result["status"] == "skipped":
                        report.skipped.append(result)
                    else:
                        report.blocked.append(result)
                if company_applied >= MAX_PER_COMPANY:
                    break

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(asdict(report), indent=2))
    print(json.dumps({"applied": len(report.applied), "blocked": len(report.blocked), "skipped": len(report.skipped)}))
    return report


if __name__ == "__main__":
    run()
