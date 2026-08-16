#!/usr/bin/env python3
"""Parallel multi-tab careers apply — one Chrome tab per worker.

Workers pull from a shared company queue so all tabs stay busy. One ASK_OWNER
wait must not idle the other nine tabs. Owner solves captchas; workers fill/submit.
"""

from __future__ import annotations

import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from multiprocessing import Manager
from pathlib import Path
from typing import Any

PARALLEL_TABS = int(os.environ.get("HITECHCITY_PARALLEL_TABS", "10"))
REPORT = Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))


def _workable_companies(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer tenants that have careers URLs so tabs do not sit on urls=0."""
    with_urls: list[dict[str, Any]] = []
    without: list[dict[str, Any]] = []
    for c in companies:
        if c.get("careersUrls"):
            with_urls.append(c)
        else:
            without.append(c)
    # urls=0 companies are LinkedIn-only — do not occupy a careers tab.
    return with_urls or without


def _worker_loop(payload: tuple[int, Any]) -> dict[str, Any]:
    """Pull companies from the shared queue until empty; keep this tab applying."""
    worker_id, queue = payload
    os.environ["HITECHCITY_PARALLEL_WORKER"] = str(worker_id)
    os.environ.setdefault("HITECHCITY_MAX_CHROME_TABS", "10")
    os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
    started = datetime.now(timezone.utc).isoformat()
    out: dict[str, Any] = {
        "workerId": worker_id,
        "startedAt": started,
        "companies": [],
        "applied": [],
        "blocked": [],
        "skipped": [],
        "scanned": [],
        "error": "",
    }
    print(f"CAREERS PARALLEL worker={worker_id} ready — pulling next company", flush=True)
    from tools.hitechcity.careers_apply import run as run_careers

    while True:
        try:
            company = queue.get(timeout=3)
        except Exception:
            break
        if company is None:
            break
        name = (company.get("name") or "?")[:40]
        out["companies"].append(company.get("name"))
        print(f"CAREERS PARALLEL worker={worker_id} NEXT {name}", flush=True)
        try:
            rep = run_careers([company])
            out["applied"].extend(list(rep.applied or []))
            out["blocked"].extend(list(rep.blocked or []))
            out["skipped"].extend(list(rep.skipped or []))
            out["scanned"].extend(list(rep.scanned or []))
            print(
                f"CAREERS PARALLEL worker={worker_id} done {name} "
                f"applied={len(rep.applied or [])} blocked={len(rep.blocked or [])}",
                flush=True,
            )
        except Exception as e:
            out["error"] = (out.get("error") or "") + f"{name}:{e}; "
            print(f"CAREERS PARALLEL worker={worker_id} ERROR {name} {e}", flush=True)
            print(traceback.format_exc()[-800:], flush=True)
    out["finishedAt"] = datetime.now(timezone.utc).isoformat()
    print(
        f"CAREERS PARALLEL worker={worker_id} queue_empty "
        f"applied={len(out['applied'])} blocked={len(out['blocked'])} "
        f"skipped={len(out['skipped'])}",
        flush=True,
    )
    return out


def run_parallel(companies: list[dict[str, Any]]) -> Any:
    """Fan out companies across PARALLEL_TABS Chrome tabs (shared queue)."""
    from tools.hitechcity.careers_apply import CareersReport

    work = _workable_companies(companies)
    n = max(1, int(os.environ.get("HITECHCITY_PARALLEL_TABS", str(PARALLEL_TABS))))
    n = max(1, min(n, len(work), 12))
    print(
        f"CAREERS PARALLEL start tabs={n} companies={len(work)} "
        f"(queue — idle tabs steal next company) target≈50 submits/day",
        flush=True,
    )
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    if n <= 1:
        from tools.hitechcity.careers_apply import run as run_careers

        os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
        return run_careers(work)

    # Parent-only: close leftover tabs before workers start (hard cap 10 apply + LinkedIn).
    try:
        from playwright.sync_api import sync_playwright
        from tools.hitechcity.careers_apply import CDP, prune_surplus_tabs

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(CDP, timeout=15_000)
            if browser.contexts:
                prune_surplus_tabs(browser.contexts[0])
    except Exception as e:
        print(f"CAREERS TABS pre-prune skipped: {e}", flush=True)

    mgr = Manager()
    queue = mgr.Queue()
    for c in work:
        queue.put(c)
    for _ in range(n):
        queue.put(None)

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=n) as pool:
        futs = {pool.submit(_worker_loop, (i, queue)): i for i in range(n)}
        for fut in as_completed(futs):
            wid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                print(f"CAREERS PARALLEL worker={wid} future_error {e}", flush=True)
                results.append(
                    {
                        "workerId": wid,
                        "applied": [],
                        "blocked": [{"company": "?", "reason": f"worker_crash:{e}"}],
                        "skipped": [],
                        "scanned": [],
                        "error": str(e),
                    }
                )

    for r in sorted(results, key=lambda x: int(x.get("workerId") or 0)):
        report.applied.extend(r.get("applied") or [])
        report.blocked.extend(r.get("blocked") or [])
        report.skipped.extend(r.get("skipped") or [])
        report.scanned.extend(r.get("scanned") or [])

    report.finishedAt = datetime.now(timezone.utc).isoformat()
    payload = asdict(report)
    payload["parallel"] = {
        "tabs": n,
        "queue": True,
        "workers": [
            {
                "workerId": r.get("workerId"),
                "companies": r.get("companies"),
                "applied": len(r.get("applied") or []),
                "blocked": len(r.get("blocked") or []),
                "error": r.get("error") or "",
            }
            for r in results
        ],
    }
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass
    print(
        json.dumps(
            {
                "parallel": True,
                "queue": True,
                "tabs": n,
                "applied": len(report.applied),
                "blocked": len(report.blocked),
                "skipped": len(report.skipped),
            }
        ),
        flush=True,
    )
    return report
