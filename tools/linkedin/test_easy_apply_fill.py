#!/usr/bin/env python3
"""Unit checks for Easy Apply question → value mapping (no browser)."""
from __future__ import annotations

from apply_answers import (
    DEFAULT_PROFILE,
    FIT_BLURB,
    answer_for_apply_field,
    submitted_ids_from_report,
)


def assert_eq(got, want, msg):
    if got != want:
        raise AssertionError(f"{msg}: got {got!r} want {want!r}")


# Cyara 2026-09-11 — empty fields that blocked "exceeded Easy Apply steps"
assert_eq(
    answer_for_apply_field("What is your salary expectation?"),
    DEFAULT_PROFILE["expected_ctc"],
    "salary expectation must fill 65 LPA rupees",
)
assert_eq(
    answer_for_apply_field("Please advise your Location in India?"),
    DEFAULT_PROFILE["city"],
    "location in India must fill Hyderabad",
)
essay = answer_for_apply_field(
    "In just a few words please tell us about your experience related to this "
    "position, and why you'd feel you'd be a great fit?"
)
assert_eq(essay, FIT_BLURB, "few-words essay must not be 15")
assert_eq(
    answer_for_apply_field(
        "How many years have you spent designing/architecting cloud-native or distributed systems?"
    ),
    DEFAULT_PROFILE["experience_years"],
    "how many years must stay numeric 15",
)
assert_eq(
    answer_for_apply_field("What is your current salary?"),
    DEFAULT_PROFILE["current_ctc"],
    "current salary stays 52 LPA rupees",
)
assert_eq(
    answer_for_apply_field("Are you flexible working from Hyderabad location?", tag="select"),
    None,
    "Yes/No select must not get a text answer",
)

blocked_report = {
    "submitted": [{"job_id": "4464831458", "status": "submitted"}],
    "blocked": [{"job_id": "4461107562", "status": "blocked", "reason": "exceeded Easy Apply steps"}],
    "all": [
        {"job_id": "4464831458", "status": "submitted"},
        {"job_id": "4461107562", "status": "blocked"},
    ],
    "ids": ["4464831458"],
}
got = submitted_ids_from_report(blocked_report)
assert_eq("4461107562" in got, False, "blocked Cyara must not be hard-seen")
assert_eq("4464831458" in got, True, "submitted Talentgigs must stay seen")

print("easy_apply fill self-test OK")
