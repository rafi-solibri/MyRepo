#!/usr/bin/env python3
"""Daily job hunt runner — discover, match, package, notify."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(__file__).resolve().parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from matcher import filter_and_rank  # noqa: E402
from notify import send_email, send_webhook, write_digest  # noqa: E402
from packager import write_application_packs  # noqa: E402
from portals import portal_search_links  # noqa: E402
from sources.fetchers import collect_jobs  # noqa: E402
from tracker import JobTracker  # noqa: E402


def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily Hyderabad + Remote job hunt automation")
    parser.add_argument("--root", type=Path, default=ROOT, help="job-automation root directory")
    parser.add_argument("--include-seen", action="store_true", help="Package previously seen matches too")
    args = parser.parse_args()

    root: Path = args.root
    profile = load_yaml(root / "config" / "profile.yaml")
    search = load_yaml(root / "config" / "search.yaml")
    resume_path = root / "data" / "resume.txt"
    resume_text = resume_path.read_text(encoding="utf-8") if resume_path.exists() else ""

    queries = search.get("search_queries") or profile.get("target_titles") or ["Software Engineer"]
    enabled = search.get("sources") or {}

    print(f"[run] collecting jobs for queries={queries}")
    raw_jobs = collect_jobs(enabled, queries)
    print(f"[run] fetched {len(raw_jobs)} unique listings")

    matched = filter_and_rank(raw_jobs, profile, search)
    print(f"[run] matched {len(matched)} after scoring")

    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    tracker = JobTracker(out_dir / "jobs.sqlite")
    new_jobs = tracker.upsert_seen(matched)
    print(f"[run] newly seen: {len(new_jobs)}")

    pack_source = matched if args.include_seen else (new_jobs or matched[:5])
    packs = write_application_packs(
        pack_source,
        profile,
        resume_text,
        out_dir / "applications",
        limit=int(search.get("max_application_packs") or 15),
    )

    portal_links = portal_search_links(queries, search.get("portals"))
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    digest_path = write_digest(
        out_dir / f"digest-{day}.md",
        matched,
        new_jobs,
        portal_links,
        packs,
        profile,
    )

    # Machine-readable snapshot for CI artifacts
    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "matched": [j.to_dict() for j in matched],
        "new_ids": [j.id for j in new_jobs],
        "portal_links": portal_links,
        "packs": [p.as_posix() for p in packs],
    }
    (out_dir / f"digest-{day}.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

    notify_cfg = search.get("notify") or {}
    if notify_cfg.get("webhook"):
        send_webhook(digest_path, len(matched), len(new_jobs))
    if notify_cfg.get("email"):
        send_email(digest_path)

    print(f"[run] digest → {digest_path}")
    print(f"[run] packs  → {len(packs)} files in {out_dir / 'applications'}")
    print(
        "[run] Reminder: apply manually via portal links / Easy Apply. "
        "Auto-submit bots violate portal ToS and risk bans."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
