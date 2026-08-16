#!/usr/bin/env python3
"""Parallel multi-tab careers apply — one Chrome tab per worker.

Owner solves captchas in whichever tab is waiting; other workers keep applying.
Target: ~10 companies in flight, ~50 submits/day across Madhapur / HITEC campus list.
"""

from __future__ import annotations

import json
import os
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PARALLEL_TABS = int(os.environ.get("HITECHCITY_PARALLEL_TABS", "10"))
REPORT = Path(os.environ.get("HITECHCITY_CAREERS_REPORT", "/opt/cursor/artifacts/hitechcity-careers.json"))


def _chunk(items: list[Any], n: int) -> list[list[Any]]:
    n = max(1, min(n, len(items) or 1))
    buckets: list[list[Any]] = [[] for _ in range(n)]
    for i, item in enumerate(items):
        buckets[i % n].append(item)
    return [b for b in buckets if b]


def _worker(payload: tuple[int, list[dict[str, Any]]]) -> dict[str, Any]:
    """Process one company chunk in an isolated process + dedicated Chrome tab."""
    worker_id, companies = payload
    os.environ["HITECHCITY_PARALLEL_WORKER"] = str(worker_id)
    # Avoid nested parallel fan-out inside the worker.
    os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
    started = datetime.now(timezone.utc).isoformat()
    out: dict[str, Any] = {
        "workerId": worker_id,
        "startedAt": started,
        "companies": [c.get("name") for c in companies],
        "applied": [],
        "blocked": [],
        "skipped": [],
        "scanned": [],
        "error": "",
    }
    print(
        f"CAREERS PARALLEL worker={worker_id} companies={len(companies)} "
        f"| {', '.join((c.get('name') or '?')[:24] for c in companies[:8])}",
        flush=True,
    )
    try:
        from tools.hitechcity.careers_apply import run as run_careers

        rep = run_careers(companies)
        out["applied"] = list(rep.applied or [])
        out["blocked"] = list(rep.blocked or [])
        out["skipped"] = list(rep.skipped or [])
        out["scanned"] = list(rep.scanned or [])
        out["finishedAt"] = rep.finishedAt
    except Exception as e:
        out["error"] = f"{e}"
        out["trace"] = traceback.format_exc()[-2000:]
        print(f"CAREERS PARALLEL worker={worker_id} ERROR {e}", flush=True)
    out["finishedAt"] = out.get("finishedAt") or datetime.now(timezone.utc).isoformat()
    print(
        f"CAREERS PARALLEL worker={worker_id} done "
        f"applied={len(out['applied'])} blocked={len(out['blocked'])} "
        f"skipped={len(out['skipped'])}",
        flush=True,
    )
    return out


def run_parallel(companies: list[dict[str, Any]]) -> Any:
    """Fan out companies across PARALLEL_TABS Chrome tabs (separate processes)."""
    from tools.hitechcity.careers_apply import CareersReport

    n = max(1, int(os.environ.get("HITECHCITY_PARALLEL_TABS", str(PARALLEL_TABS))))
    # Cap workers to company count and a hard ceiling (Chrome stability).
    n = max(1, min(n, len(companies), 12))
    chunks = _chunk(companies, n)
    print(
        f"CAREERS PARALLEL start tabs={len(chunks)} companies={len(companies)} "
        f"target≈50 submits/day — solve captchas in any waiting tab",
        flush=True,
    )
    report = CareersReport(startedAt=datetime.now(timezone.utc).isoformat())
    # Sequential fallback for a single chunk.
    if len(chunks) <= 1:
        from tools.hitechcity.careers_apply import run as run_careers

        os.environ["HITECHCITY_PARALLEL_TABS"] = "1"
        return run_careers(companies)

    results: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=len(chunks)) as pool:
        futs = {
            pool.submit(_worker, (i, chunk)): i
            for i, chunk in enumerate(chunks)
        }
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
        "tabs": len(chunks),
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
                "tabs": len(chunks),
                "applied": len(report.applied),
                "blocked": len(report.blocked),
                "skipped": len(report.skipped),
            }
        ),
        flush=True,
    )
    return report
