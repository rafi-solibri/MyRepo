#!/usr/bin/env python3
"""SmartApply question intent — Crowe / relationship / client regressions."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.indeed.smartapply_answers import prefer_no_radio, want_from_question  # noqa: E402


CROWE_CLIENT = (
    "Do you currently work at Crowe client? If yes, provide the company name. "
    "If no, reply No."
)
CROWE_REL = (
    "Do you have a familial (by blood or marriage), romantic, or close personal "
    "relationship with a Crowe employee or applicant?"
)
CROWE_REL_DETAIL = (
    "Identify the individual(s), their role (if known) and describe the relationship "
    "(e.g., sibling, spouse, in-law, dating, roommate). If none, write N/A."
)


def test_crowe_client_is_no_not_current_employer():
    assert want_from_question(CROWE_CLIENT) == "No"
    assert prefer_no_radio(CROWE_CLIENT) is True
    assert want_from_question("Current employer / company name") == "Nemetschek / Solibri"
    assert want_from_question("Where are you currently employed?") == "Nemetschek / Solibri"


def test_crowe_relationship_is_no_and_na():
    assert want_from_question(CROWE_REL) == "no"
    assert prefer_no_radio(CROWE_REL) is True
    assert want_from_question(CROWE_REL_DETAIL) == "N/A"
    assert prefer_no_radio("Are you authorized to lawfully work in India?") is False


def test_have_you_ever_worked_at_crowe_is_no():
    assert (
        want_from_question("Have you ever worked at Crowe or a Crowe client?")
        == "no"
    )
    assert prefer_no_radio("Have you ever worked for this company?") is True
    assert want_from_question("How many years have you worked with .NET?") is None


def test_generic_current_employer_still_fills():
    assert want_from_question("Current Company / Organization") == "Nemetschek / Solibri"
    assert want_from_question("Current CTC (LPA)") is None


if __name__ == "__main__":
    test_crowe_client_is_no_not_current_employer()
    test_crowe_relationship_is_no_and_na()
    test_have_you_ever_worked_at_crowe_is_no()
    test_generic_current_employer_still_fills()
    print("ok")
