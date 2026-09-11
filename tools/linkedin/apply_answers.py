"""Easy Apply question → profile value mapping (no browser)."""

from __future__ import annotations

import re
from typing import Any

FIT_BLURB = (
    "15 years as a .NET / cloud architect and engineering lead: .NET Core "
    "microservices, AWS/Azure, Kafka, Kubernetes, Angular/React. Principal "
    "Analyst at Nemetschek (Solibri/Spacewell); immediate joiner in Hyderabad."
)

ESSAY_RE = re.compile(
    r"few words|tell us about|why (you|you'd|you would|do you)|great fit|"
    r"cover letter|additional information|summarize your|briefly describe|"
    r"experience related to (this|the) (position|role|job)|why you.?d be",
    re.I,
)
YEARS_NUMERIC_RE = re.compile(
    r"how many years|years of (work )?experience|total experience|"
    r"years have you (spent|worked|been)|years of work",
    re.I,
)
EXPECTED_CTC_RE = re.compile(
    r"expected (ctc|salary|compensation|fixed|annual)|desired salary|"
    r"salary expectation",
    re.I,
)
CURRENT_CTC_RE = re.compile(
    r"current (ctc|salary|annual salary|compensation)|present ctc|"
    r"confirm your current ctc|annual salary|fixed ctc|salary\s*\(?fixed\)?",
    re.I,
)
LOCATION_RE = re.compile(
    r"location in india|advise your location|your location|current location|"
    r"\bcity\b|based in|where are you (located|based)",
    re.I,
)

DEFAULT_PROFILE = {
    "phone": "8790251698",
    "current_ctc": "5200000",
    "expected_ctc": "6500000",
    "current_ctc_lakhs": "52",
    "expected_ctc_lakhs": "65",
    "experience_years": "15",
    "city": "Hyderabad",
}


def answer_for_apply_field(
    blob: str, *, tag: str = "input", profile: dict[str, str] | None = None
) -> str | None:
    """Map Easy Apply question text to a profile value.

    Cyara-style labels (salary expectation, location in India, few-words essay)
    must not stay empty or get filled with a bare 15.
    """
    p = {**DEFAULT_PROFILE, **(profile or {})}
    text = re.sub(r"\s+", " ", (blob or "")).strip()
    if not text:
        return None
    low = text.lower()
    if tag == "select":
        return None
    if ESSAY_RE.search(low):
        return FIT_BLURB
    if EXPECTED_CTC_RE.search(low):
        return p["expected_ctc_lakhs"] if "lakh" in low else p["expected_ctc"]
    if CURRENT_CTC_RE.search(low) and "expect" not in low:
        return p["current_ctc_lakhs"] if "lakh" in low else p["current_ctc"]
    if "notice" in low:
        return "1"
    if YEARS_NUMERIC_RE.search(low) and not ESSAY_RE.search(low):
        return p["experience_years"]
    if LOCATION_RE.search(low) and "company" not in low and "country code" not in low:
        return p["city"]
    if re.search(r"\bphone\b|\bmobile\b|contact number", low) and "country" not in low:
        return p["phone"]
    email = (p.get("email") or "").strip()
    if "email" in low and email:
        return email
    return None


def submitted_ids_from_report(data: Any) -> set[str]:
    """Hard-seen IDs are submitted applies only (fill-step blocks stay retryable)."""
    out: set[str] = set()
    if isinstance(data, list):
        for row in data:
            if not isinstance(row, dict):
                continue
            status = str(row.get("status") or "").lower()
            jid = str(row.get("job_id") or row.get("jobId") or "").strip()
            if jid.isdigit() and status in ("submitted", "applied"):
                out.add(jid)
        return out
    if not isinstance(data, dict):
        return out
    for key in ("submitted", "applied"):
        rows = data.get(key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            jid = str(row.get("job_id") or row.get("jobId") or "").strip()
            if jid.isdigit():
                out.add(jid)
    rows = data.get("all")
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            status = str(row.get("status") or "").lower()
            jid = str(row.get("job_id") or row.get("jobId") or "").strip()
            if jid.isdigit() and status in ("submitted", "applied"):
                out.add(jid)
    for jid in data.get("ids") or data.get("jobIds") or []:
        s = str(jid).strip()
        if s.isdigit():
            out.add(s)
    return out
