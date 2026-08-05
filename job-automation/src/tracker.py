"""SQLite tracker to avoid re-surfacing the same jobs every day."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from utils.models import Job, utc_now_iso


class JobTracker:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    company TEXT,
                    url TEXT,
                    source TEXT,
                    first_seen TEXT,
                    last_seen TEXT,
                    match_score REAL,
                    status TEXT DEFAULT 'new',
                    payload TEXT
                )
                """
            )
            conn.commit()

    def known_ids(self) -> set[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT id FROM jobs").fetchall()
        return {r["id"] for r in rows}

    def upsert_seen(self, jobs: list[Job]) -> list[Job]:
        """Insert new jobs; update last_seen for known ones. Returns newly seen jobs."""
        known = self.known_ids()
        new_jobs: list[Job] = []
        now = utc_now_iso()
        with self._connect() as conn:
            for job in jobs:
                if job.id in known:
                    conn.execute(
                        "UPDATE jobs SET last_seen=?, match_score=? WHERE id=?",
                        (now, job.match_score, job.id),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO jobs (id, title, company, url, source, first_seen, last_seen, match_score, status, payload)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new', ?)
                        """,
                        (
                            job.id,
                            job.title,
                            job.company,
                            job.url,
                            job.source,
                            now,
                            now,
                            job.match_score,
                            json.dumps(job.to_dict()),
                        ),
                    )
                    new_jobs.append(job)
            conn.commit()
        return new_jobs

    def mark_status(self, job_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET status=? WHERE id=?", (status, job_id))
            conn.commit()
