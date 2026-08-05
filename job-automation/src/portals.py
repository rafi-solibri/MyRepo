"""Pre-built search URLs for major Indian + global job portals.

These open filtered search pages so you can Easy Apply while logged in yourself.
Automated credentialed apply on these sites violates their Terms of Service and
risks account bans — this module intentionally does not log in or submit forms.
"""

from __future__ import annotations

from urllib.parse import quote_plus


def portal_search_links(
    queries: list[str],
    portals: list[str] | None = None,
) -> dict[str, list[dict[str, str]]]:
    enabled = set(portals or [])
    primary = queries[0] if queries else "Senior Software Engineer"
    q = quote_plus(primary)
    hyd = quote_plus("Hyderabad")
    remote = quote_plus("Remote")

    catalog: dict[str, list[dict[str, str]]] = {
        "naukri": [
            {
                "label": "Naukri — Hyderabad",
                "url": f"https://www.naukri.com/{quote_plus(primary.replace(' ', '-').lower())}-jobs-in-hyderabad-secunderabad",
            },
            {
                "label": "Naukri — Remote / WFH",
                "url": f"https://www.naukri.com/{quote_plus(primary.replace(' ', '-').lower())}-jobs?workModeFilter=2%2C3",
            },
        ],
        "linkedin": [
            {
                "label": "LinkedIn — Hyderabad",
                "url": f"https://www.linkedin.com/jobs/search/?keywords={q}&location={hyd}&f_TPR=r86400",
            },
            {
                "label": "LinkedIn — Remote (past 24h)",
                "url": f"https://www.linkedin.com/jobs/search/?keywords={q}&f_WT=2&f_TPR=r86400",
            },
        ],
        "indeed": [
            {
                "label": "Indeed — Hyderabad",
                "url": f"https://in.indeed.com/jobs?q={q}&l={hyd}&fromage=1",
            },
            {
                "label": "Indeed — Remote India",
                "url": f"https://in.indeed.com/jobs?q={q}+remote&l=India&fromage=1",
            },
        ],
        "cutshort": [
            {
                "label": "Cutshort search",
                "url": f"https://cutshort.io/profile/recommended-jobs?search={q}",
            }
        ],
        "foundit": [
            {
                "label": "Foundit — Hyderabad",
                "url": f"https://www.foundit.in/srp/results?query={q}&locations={hyd}",
            },
            {
                "label": "Foundit — Remote",
                "url": f"https://www.foundit.in/srp/results?query={q}&locations={remote}",
            },
        ],
        "instahyre": [
            {
                "label": "Instahyre opportunities",
                "url": "https://www.instahyre.com/candidate/opportunities/",
            }
        ],
        "wellfound": [
            {
                "label": "Wellfound (AngelList) remote",
                "url": f"https://wellfound.com/role/r/software-engineer?remote=true&query={q}",
            }
        ],
        "hirist": [
            {
                "label": "Hirist search",
                "url": f"https://www.hirist.tech/search/?q={q}&loc=Hyderabad",
            }
        ],
    }

    if enabled:
        return {k: v for k, v in catalog.items() if k in enabled}
    return catalog
