"""Score jobs against candidate profile and search preferences."""

from __future__ import annotations

import re
from typing import Any

from utils.models import Job, contains_any


HYDERABAD_HINTS = ["hyderabad", "hyd", "telangana", "secunderabad"]
REMOTE_HINTS = [
    "remote",
    "work from home",
    "wfh",
    "work-from-home",
    "fully remote",
    "anywhere",
    "distributed",
]
INDIA_HINTS = ["india", "ist", "indian", "apac", "asia", "bangalore", "bengaluru", "hyderabad"]


def _blob(job: Job) -> str:
    return " ".join(
        [
            job.title,
            job.company,
            job.location,
            job.description,
            job.salary_text,
            " ".join(job.tags),
        ]
    ).lower()


def parse_salary_lpa(text: str) -> float | None:
    """Best-effort extract of INR LPA / lakhs from free-text salary."""
    if not text:
        return None
    lower = text.lower().replace(",", "")
    # e.g. 65 LPA, 50-70 LPA, 65 lakhs
    m = re.search(r"(\d{2,3}(?:\.\d+)?)\s*[-–to]*\s*(\d{2,3}(?:\.\d+)?)?\s*(?:lpa|lakh|lac)", lower)
    if m:
        a = float(m.group(1))
        b = float(m.group(2)) if m.group(2) else a
        return max(a, b)
    # INR absolute like 5000000 / year ~ 50 LPA
    m = re.search(r"(?:inr|rs\.?|₹)\s*(\d{6,8})", lower)
    if m:
        return float(m.group(1)) / 100_000
    # USD yearly rough convert (~83 INR) for remote roles
    m = re.search(r"\$\s?(\d{2,3}),?(\d{3})", lower)
    if m:
        usd = float(m.group(1) + m.group(2))
        return (usd * 83) / 100_000
    return None


def _title_match_score(job_title: str, target_titles: list[str]) -> tuple[float, list[str]]:
    """Score using the job title only (avoid description false positives)."""
    title = job_title.lower()
    exact = [t for t in target_titles if t in title]
    if exact:
        return 0.45, [f"title match: {', '.join(exact[:3])}"]

    # Token overlap on meaningful words
    stop = {
        "engineer",
        "engineering",
        "software",
        "developer",
        "senior",
        "staff",
        "principal",
        "lead",
        "manager",
        "the",
        "and",
        "of",
        "in",
    }
    raw_tokens = set(re.findall(r"[a-z0-9+#.]+", title))
    eng_markers = {"engineer", "developer", "architect", "sre", "devops"}
    is_eng_title = bool(raw_tokens & eng_markers) or "engineering manager" in title
    if not is_eng_title:
        return 0.0, []

    tokens = raw_tokens - stop
    best = 0.0
    reasons: list[str] = []
    for target in target_titles:
        t_tokens = set(re.findall(r"[a-z0-9+#.]+", target)) - stop
        if not t_tokens:
            continue
        overlap = tokens & t_tokens
        # Ignore ultra-generic single-token overlaps like "product" alone
        if len(overlap) == 1 and next(iter(overlap)) in {"product", "solution", "platform", "tech"}:
            continue
        if not overlap:
            continue
        ratio = len(overlap) / len(t_tokens)
        if ratio > best:
            best = ratio
            reasons = [f"partial title overlap with '{target}': {', '.join(sorted(overlap))}"]
    if best >= 0.5:
        return 0.25 + 0.2 * best, reasons
    return 0.0, []


def score_job(job: Job, profile: dict[str, Any], search: dict[str, Any]) -> Job:
    text = _blob(job)
    reasons: list[str] = []
    score = 0.0

    excludes = profile.get("exclude_keywords") or []
    # Prefer excluding from title first (stronger signal)
    if contains_any(job.title, excludes) or contains_any(text[:500], excludes):
        job.match_score = 0.0
        job.match_reasons = ["excluded by keyword"]
        return job

    titles = [t.lower() for t in (profile.get("target_titles") or [])]
    title_score, title_reasons = _title_match_score(job.title, titles)
    score += title_score
    reasons.extend(title_reasons)

    # Require at least weak title relevance for non-zero keepers
    if title_score <= 0:
        job.match_score = 0.0
        job.match_reasons = ["no target-title overlap in job title"]
        return job

    # Skills — weight title/tags higher than long HTML descriptions
    skills = [s.lower() for s in (profile.get("skills") or [])]
    title_tag_blob = f"{job.title} {' '.join(job.tags)}".lower()
    strong_hits = [s for s in skills if s in title_tag_blob]
    soft_hits = [s for s in skills if s in text and s not in strong_hits]
    if strong_hits:
        score += min(0.25, 0.06 * len(strong_hits))
        reasons.append(f"skills (title/tags): {', '.join(strong_hits[:6])}")
    elif soft_hits:
        score += min(0.12, 0.03 * len(soft_hits))
        reasons.append(f"skills (description): {', '.join(soft_hits[:6])}")

    # Location / remote preference
    is_hyd = any(h in text for h in HYDERABAD_HINTS)
    is_remote = job.remote or any(h in text for h in REMOTE_HINTS)
    india_ok = any(h in text for h in INDIA_HINTS) or is_hyd

    if search.get("include_hyderabad") and is_hyd:
        score += 0.15
        reasons.append("Hyderabad location")
    if search.get("prefer_remote") and is_remote:
        score += 0.12
        reasons.append("remote/WFH")
    if search.get("india_timezone_friendly"):
        if india_ok or is_hyd:
            score += 0.08
            reasons.append("India/APAC friendly signal")
        elif is_remote and not india_ok:
            score -= 0.05
            reasons.append("remote but no India timezone signal")

    # Must match location preference: Hyderabad OR remote
    if not (is_hyd or is_remote):
        score *= 0.25
        reasons.append("not Hyderabad/remote — downranked")

    # Salary filter
    min_ctc = float(profile.get("min_ctc_lpa") or 0)
    expected = float(profile.get("expected_ctc_lpa") or 0)
    disclosed = parse_salary_lpa(job.salary_text) or parse_salary_lpa(job.description[:2000])
    if disclosed is not None:
        if disclosed < min_ctc:
            score *= 0.2
            reasons.append(f"salary ~{disclosed:.0f} LPA below min {min_ctc}")
        elif disclosed >= expected * 0.85:
            score += 0.10
            reasons.append(f"salary ~{disclosed:.0f} LPA near target")
        else:
            reasons.append(f"salary ~{disclosed:.0f} LPA disclosed")

    job.match_score = round(min(score, 1.0), 3)
    job.match_reasons = reasons
    return job


def filter_and_rank(
    jobs: list[Job],
    profile: dict[str, Any],
    search: dict[str, Any],
) -> list[Job]:
    scored = [score_job(j, profile, search) for j in jobs]
    min_score = float(search.get("min_match_score") or 0.35)
    matched = [j for j in scored if j.match_score >= min_score]
    matched.sort(key=lambda j: j.match_score, reverse=True)
    limit = int(search.get("max_jobs_per_run") or 40)
    return matched[:limit]
