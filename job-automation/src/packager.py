"""Generate per-job application packs (cover note + screening answers)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from utils.models import Job, safe_filename, utc_now_iso


def _cover_note(job: Job, profile: dict[str, Any], resume_excerpt: str) -> str:
    name = profile.get("name") or "Candidate"
    expected = profile.get("expected_ctc_lpa", 65)
    skills = ", ".join((profile.get("skills") or [])[:8])
    reason = (profile.get("screening") or {}).get("reason_for_change", "")
    return f"""Dear Hiring Team,

I am writing to express interest in the {job.title} role at {job.company}.
I am based in {profile.get('location', 'Hyderabad')} and open to Hyderabad / remote WFH opportunities.

Highlights relevant to this role:
- Target seniority aligned with expected CTC of {expected} LPA
- Core skills: {skills}
- {reason}

I have attached / linked my resume for your review and would welcome a conversation.

Regards,
{name}
{profile.get('email', '')}
{profile.get('phone', '')}
{profile.get('linkedin_url', '')}

---
Resume excerpt:
{resume_excerpt[:1200]}
"""


def _screening_block(profile: dict[str, Any]) -> str:
    s = profile.get("screening") or {}
    lines = [
        f"Expected CTC: {s.get('expected_ctc') or profile.get('expected_ctc_lpa')} LPA",
        f"Current CTC: {s.get('current_ctc') or 'N/A'}",
        f"Notice period: {s.get('notice_period_days', 30)} days",
        f"Current location: {s.get('current_location') or profile.get('location')}",
        f"Willing to relocate: {s.get('willing_to_relocate', False)}",
        f"Preferred modes: {', '.join(s.get('preferred_work_modes') or [])}",
        f"Reason for change: {s.get('reason_for_change', '')}",
    ]
    return "\n".join(lines)


def write_application_packs(
    jobs: list[Job],
    profile: dict[str, Any],
    resume_text: str,
    out_dir: Path,
    limit: int,
) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for job in jobs[:limit]:
        fname = f"{safe_filename(job.company)}__{safe_filename(job.title)}__{job.id}.md"
        path = out_dir / fname
        body = f"""# Application pack — {job.title} @ {job.company}

- Generated: {utc_now_iso()}
- Source: {job.source}
- Match score: {job.match_score}
- Reasons: {'; '.join(job.match_reasons)}
- Location: {job.location}
- Salary text: {job.salary_text or 'Not disclosed'}
- Apply URL: {job.url}

## Status
- [ ] Opened listing
- [ ] Applied (manual Easy Apply / portal form)
- [ ] Recruiter followed up

## Screening answers
{_screening_block(profile)}

## Suggested cover note
{_cover_note(job, profile, resume_text)}

## Job description (truncated)
{job.description[:2500]}
"""
        path.write_text(body, encoding="utf-8")
        written.append(path)
    return written
