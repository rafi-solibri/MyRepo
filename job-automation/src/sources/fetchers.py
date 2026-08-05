"""Fetch jobs from public, keyless (or optional-key) APIs."""

from __future__ import annotations

import os
from typing import Callable

import requests

from utils.models import Job, normalize_text, stable_job_id

USER_AGENT = "RafiJobHuntBot/1.0 (+personal daily digest; contact via repo owner)"
TIMEOUT = 30


def _get_json(url: str, params: dict | None = None, headers: dict | None = None):
    hdrs = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    resp = requests.get(url, params=params, headers=hdrs, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_remotive(queries: list[str], limit: int = 50) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    for q in queries:
        try:
            data = _get_json(
                "https://remotive.com/api/remote-jobs",
                params={"search": q, "limit": limit},
            )
        except Exception as exc:  # noqa: BLE001 — isolate per-source failures
            print(f"[remotive] query={q!r} failed: {exc}")
            continue
        for item in data.get("jobs", []):
            url = item.get("url") or ""
            title = normalize_text(item.get("title"))
            company = normalize_text(item.get("company_name"))
            jid = stable_job_id("remotive", url, title, company)
            if jid in seen:
                continue
            seen.add(jid)
            jobs.append(
                Job(
                    id=jid,
                    title=title,
                    company=company,
                    location=normalize_text(item.get("candidate_required_location") or "Remote"),
                    url=url,
                    source="remotive",
                    description=normalize_text(item.get("description")),
                    salary_text=normalize_text(item.get("salary")),
                    tags=[normalize_text(t) for t in (item.get("tags") or [])],
                    remote=True,
                    posted_at=normalize_text(item.get("publication_date")),
                )
            )
    return jobs


def fetch_remoteok(queries: list[str]) -> list[Job]:
    try:
        data = _get_json("https://remoteok.com/api")
    except Exception as exc:  # noqa: BLE001
        print(f"[remoteok] failed: {exc}")
        return []

    jobs: list[Job] = []
    needles = [q.lower() for q in queries]
    for item in data:
        if not isinstance(item, dict) or "position" not in item:
            continue
        title = normalize_text(item.get("position"))
        company = normalize_text(item.get("company"))
        description = normalize_text(item.get("description"))
        tags = [normalize_text(t) for t in (item.get("tags") or [])]
        blob = " ".join([title, company, description, " ".join(tags)]).lower()
        if needles and not any(n in blob for n in needles):
            continue
        url = normalize_text(item.get("url") or item.get("apply_url"))
        jid = stable_job_id("remoteok", url, title, company)
        jobs.append(
            Job(
                id=jid,
                title=title,
                company=company,
                location=normalize_text(item.get("location") or "Remote"),
                url=url,
                source="remoteok",
                description=description,
                salary_text=normalize_text(str(item.get("salary_max") or item.get("salary") or "")),
                tags=tags,
                remote=True,
                posted_at=normalize_text(str(item.get("date") or "")),
            )
        )
    return jobs


def fetch_arbeitnow(queries: list[str], pages: int = 2) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    needles = [q.lower() for q in queries]
    for page in range(1, pages + 1):
        try:
            data = _get_json(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"page": page},
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[arbeitnow] page={page} failed: {exc}")
            break
        for item in data.get("data", []):
            title = normalize_text(item.get("title"))
            company = normalize_text(item.get("company_name"))
            description = normalize_text(item.get("description"))
            tags = [normalize_text(t) for t in (item.get("tags") or [])]
            blob = " ".join([title, company, description, " ".join(tags)]).lower()
            if needles and not any(n in blob for n in needles):
                continue
            url = normalize_text(item.get("url"))
            jid = stable_job_id("arbeitnow", url, title, company)
            if jid in seen:
                continue
            seen.add(jid)
            remote = bool(item.get("remote"))
            jobs.append(
                Job(
                    id=jid,
                    title=title,
                    company=company,
                    location=normalize_text(item.get("location") or ("Remote" if remote else "")),
                    url=url,
                    source="arbeitnow",
                    description=description,
                    tags=tags,
                    remote=remote,
                    posted_at=normalize_text(str(item.get("created_at") or "")),
                )
            )
    return jobs


def fetch_adzuna(queries: list[str], where: str = "Hyderabad") -> list[Job]:
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
    if not app_id or not app_key:
        print("[adzuna] skipped — set ADZUNA_APP_ID and ADZUNA_APP_KEY for India listings")
        return []

    jobs: list[Job] = []
    seen: set[str] = set()
    for q in queries:
        try:
            data = _get_json(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": 20,
                    "what": q,
                    "where": where,
                    "max_days_old": 7,
                    "content-type": "application/json",
                },
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[adzuna] query={q!r} failed: {exc}")
            continue
        for item in data.get("results", []):
            title = normalize_text(item.get("title"))
            company = normalize_text((item.get("company") or {}).get("display_name"))
            url = normalize_text(item.get("redirect_url"))
            jid = stable_job_id("adzuna", url, title, company)
            if jid in seen:
                continue
            seen.add(jid)
            sal_min = item.get("salary_min")
            sal_max = item.get("salary_max")
            salary_text = ""
            if sal_min or sal_max:
                salary_text = f"INR {sal_min or '?'} - {sal_max or '?'}"
            loc = normalize_text((item.get("location") or {}).get("display_name"))
            desc = normalize_text(item.get("description"))
            remote = "remote" in f"{title} {loc} {desc}".lower() or "work from home" in desc.lower()
            jobs.append(
                Job(
                    id=jid,
                    title=title,
                    company=company,
                    location=loc or where,
                    url=url,
                    source="adzuna",
                    description=desc,
                    salary_text=salary_text,
                    remote=remote,
                    posted_at=normalize_text(item.get("created")),
                )
            )
    return jobs


SOURCE_FETCHERS: dict[str, Callable[..., list[Job]]] = {
    "remotive": fetch_remotive,
    "remoteok": fetch_remoteok,
    "arbeitnow": fetch_arbeitnow,
    "adzuna": fetch_adzuna,
}


def collect_jobs(enabled: dict[str, bool], queries: list[str]) -> list[Job]:
    all_jobs: list[Job] = []
    seen: set[str] = set()
    if enabled.get("remotive"):
        all_jobs.extend(fetch_remotive(queries))
    if enabled.get("remoteok"):
        all_jobs.extend(fetch_remoteok(queries))
    if enabled.get("arbeitnow"):
        all_jobs.extend(fetch_arbeitnow(queries))
    if enabled.get("adzuna"):
        all_jobs.extend(fetch_adzuna(queries, where="Hyderabad"))
        all_jobs.extend(fetch_adzuna(queries, where="India"))

    unique: list[Job] = []
    for job in all_jobs:
        if job.id in seen or not job.url:
            continue
        seen.add(job.id)
        unique.append(job)
    return unique
