#!/usr/bin/env python3
"""Parallel multi-tab careers apply — one Chrome tab per worker.

Workers pull from a shared company queue so all 10 tabs stay busy. One JPMC
captcha wait must not idle the other nine. After careers URLs are exhausted,
workers keep applying via LinkedIn company searches on the same tabs.
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


def _workable_careers(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only tenants with a real careers URL that is not a known hang-scan host."""
    from tools.hitechcity.careers_apply import HANG_SCAN_HOST_RE, is_hang_scan_url

    out: list[dict[str, Any]] = []
    for c in companies:
        urls = [u for u in (c.get("careersUrls") or []) if u]
        if not urls:
            continue
        if all(is_hang_scan_url(u) for u in urls):
            continue
        if HANG_SCAN_HOST_RE.search(" ".join(urls)):
            # Still include if any URL is not a hang host.
            urls = [u for u in urls if not is_hang_scan_url(u)]
            if not urls:
                continue
            c = dict(c)
            c["careersUrls"] = urls
        out.append(c)
    return out


def _linkedin_queue(companies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in companies if (c.get("linkedinSlug") or "").strip()]


def _worker_loop(payload: tuple[int, Any, Any]) -> dict[str, Any]:
    worker_id, careers_q, linkedin_q = payload
    os.environ["HITECHCITY_PARALLEL_WORKER"] = str(worker_id)
    os.environ.setdefault("HITECHCITY_MAX_CHROME_TABS", "10")
    os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
    out: dict[str, Any] = {
        "workerId": worker_id,
        "startedAt": datetime.now(timezone.utc).isoformat(),
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
            company = careers_q.get(timeout=2)
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
            print(traceback.format_exc()[-600:], flush=True)

    # Keep the tab busy: LinkedIn company applies after careers inventory.
    if linkedin_q is not None and os.environ.get("HITECHCITY_SKIP_LINKEDIN", "").strip() not in (
        "1",
        "true",
        "yes",
    ):
        from tools.hitechcity.linkedin_target_apply import run as run_linkedin

        while True:
            try:
                company = linkedin_q.get(timeout=2)
            except Exception:
                break
            if company is None:
                break
            name = (company.get("name") or "?")[:40]
            print(f"CAREERS PARALLEL worker={worker_id} LI NEXT {name}", flush=True)
            try:
                rep = run_linkedin([company])
                out["applied"].extend(list(getattr(rep, "applied", None) or []))
                out["blocked"].extend(list(getattr(rep, "blocked", None) or []))
                out["skipped"].extend(list(getattr(rep, "skipped", None) or []))
            except Exception as e:
                print(f"CAREERS PARALLEL worker={worker_id} LI ERROR {name} {e}", flush=True)

    out["finishedAt"] = datetime.now(timezone.utc).isoformat()
    print(
        f"CAREERS PARALLEL worker={worker_id} queue_empty "
        f"applied={len(out['applied'])} blocked={len(out['blocked'])}",
        flush=True,
    )
    return out


def run_parallel(companies: list[dict[str, Any]]) -> Any:
    """Fan out companies across PARALLEL_TABS Chrome tabs (shared queue)."""
    from tools.hitechcity.careers_apply import CareersReport

    work = _workable_careers(companies)
    li_work = _linkedin_queue(companies)
    n = max(1, int(os.environ.get("HITECHCITY_PARALLEL_TABS", str(PARALLEL_TABS))))
    n = max(1, min(n, max(len(work), 1), 12))
    print(
        f"CAREERS PARALLEL start tabs={n} careers={len(work)} linkedin={len(li_work)} "
        f"(shared queue — every tab keeps pulling work)",
        flush=True,
    )
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    if n <= 1:
        from tools.hitechcity.careers_apply import run as run_careers

        os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
        return run_careers(work or companies)

    mgr = Manager()
    careers_q = mgr.Queue()
    linkedin_q = mgr.Queue()
    for c in work:
        careers_q.put(c)
    for _ in range(n):
        careers_q.put(None)
    for c in li_work:
        linkedin_q.put(c)
    for _ in range(n):
        linkedin_q.put(None)

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=n) as pool:
        futs = {pool.submit(_worker_loop, (i, careers_q, linkedin_q)): i for i in range(n)}
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
