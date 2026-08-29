"""SmartApply question intent — keep in sync with fill_common_questions JS.

Crowe / similar employer modules (2026-08-29): a Yes-default radio plus
current-employer text matching blocked Continue on relationship / client
questions. Negative-intent and "if none, N/A" must win over those defaults.
"""
from __future__ import annotations

import re


def want_from_question(text: str) -> str | None:
    """Return the value SmartApply should submit for a question label/body."""
    t = (text or "").lower()
    if not t.strip():
        return None
    if _is_relationship_conflict(t):
        return "no"
    if _is_none_na(t):
        return "N/A"
    if _is_client_employer(t):
        return "No"
    if _is_current_employer(t):
        return "Nemetschek / Solibri"
    return None


def prefer_no_radio(text: str) -> bool:
    """True when an unanswered Yes/No group should pick No, not Yes."""
    t = (text or "").lower()
    return _is_relationship_conflict(t) or _is_client_employer(t)


def _is_relationship_conflict(t: str) -> bool:
    return bool(
        re.search(
            r"familial|romantic|close personal relationship|"
            r"relationship with.{0,60}(employee|applicant|staff)|"
            r"relative (who )?(work|employed)|conflict of interest",
            t,
        )
    )


def _is_none_na(t: str) -> bool:
    return bool(
        re.search(
            r"identify the individual|describe the relationship|"
            r"if none[,.]?\s*(write|enter|type|put)\s*n/?a",
            t,
        )
    )


def _is_client_employer(t: str) -> bool:
    return bool(
        re.search(r"currently work at.{0,80}client|work (at|for) (a )?(crowe |our |the )?client", t)
        and re.search(r"if no|reply no|provide the company", t)
    )


def _is_current_employer(t: str) -> bool:
    if re.search(r"salary|ctc|compensation|pay", t):
        return False
    if _is_client_employer(t) or re.search(r"if no[,.]?\s*reply no|if yes[,.]?\s*provide the company", t):
        return False
    return bool(
        re.search(
            r"current.*(employer|company|organization)|present.*(employer|company)|where.*(work|employed)",
            t,
        )
    )
