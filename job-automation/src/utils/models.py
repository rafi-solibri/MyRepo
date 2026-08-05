"""Shared types and helpers for job automation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Job:
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str = ""
    salary_text: str = ""
    tags: list[str] = field(default_factory=list)
    remote: bool = False
    posted_at: str = ""
    match_score: float = 0.0
    match_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_job_id(source: str, url: str, title: str, company: str) -> str:
    raw = f"{source}|{url}|{title}|{company}".lower().strip()
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(n.lower() in lower for n in needles if n)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def safe_filename(value: str, max_len: int = 60) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return (cleaned or "job")[:max_len]
