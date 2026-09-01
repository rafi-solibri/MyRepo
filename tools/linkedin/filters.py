#!/usr/bin/env python3
"""LinkedIn eligibility filters — title-first blacklist (never incidental JD hits)."""

from __future__ import annotations

import re

# TITLE-only hard rejects. Do NOT run against full JD — incidental mentions
# (e.g. "data engineer peers", "Salesforce integration") false-skip good roles.
TITLE_BLACKLIST = re.compile(
    r"salesforce|servicenow|guidewire|splunk|\bpega\b|oracle\s*erp|sitecore|"
    r"oracle\s*cloud\s*(scm|erp|hcm|financials|ebs)|oracle\s*scm|"
    r"finance functional|functional\s*[-–—]?\s*solution architect|"
    r"\bmean\b|devops engineer|sre engineer|site reliability engineer|gcp.?presales|workato|mulesoft|"
    r"blockchain|mandarin|biztalk|firmware|\bmes\b|\bror\b|ruby on rails|"
    r"\bsap\b|dynamics\s*365|\bd365\b|esri|\bgis\b|"
    r"java full[- ]?stack|java[- ]?(mandatory|only|required|backend)|"
    r"\bjava\b(?!.*(?:\.net|dotnet|c#))|"  # Java primary titles (allow if .NET also on title)
    r"node\.?js[- ]?(mandatory|only)|"
    r"python[- ]?(mandatory|only)|principal engineer\s*\(\s*python|"
    # Data Engineer / Data Engineering* without .NET on the same title
    r"\bdata engineer(?:ing)?\b(?!.*(?:\.net|dotnet|c#))|"
    r"\bmachine learning engineer\b|"
    r"big data architect|\bdata architect\b|data warehouse architect|data platform|"
    r"implementation specialist|"
    r"\bphp\b|laravel|"
    r"interior designer|civil engineer|electrical engineering|electrical design|"
    r"\bjunior\b|\bintern\b|\bfresher\b|"
    r"\bbim\b|business development|"
    r"golang &|golang and|"
    r"bpo|call center|marketing cloud|success architect|"
    r"non-?it staffing|us non-?it|staffing recruiter|talent acquisition|"
    r"\brevit\b|\bbarch\b|hubspot|m365 architect|microsoft 365 architect|"
    r"solutions engineer|presales|pre-sales|"
    r"\binfor\b|\berp\b.?primary|dft architect|\beda\b|"
    r"ai compiler|gen[- ]?ai architect|ai/?\s*ml architect|ai architect(?!.*\.net)|"
    r"ai technical (lead|architect)|"
    r"quality engineering|quality assurance|qa engineer|\bsdet\b|"
    r"netsuite|nice cxone|"
    # Hardware / chip (not software architect/director)
    r"\bsoc\b|system[- ]?on[- ]?chip|\basic\b|rtl design|physical design|"
    r"silicon|semiconductor|fpga|verilog|vhdl|"
    r"layout\s*design|scribe\s*layout|standard\s*cell|"
    r"design\s*verification|\bhbm\b|\bdram\b|power\s*integrity|"
    r"\bnvm\b|\bnvmqra\b|circuit\s*design|mask\s*design",
    re.I,
)

# JD / form text: only reject when another stack is clearly mandatory/required.
JD_HARD_BLACKLIST = re.compile(
    r"(?:java|python|node\.?js|golang|go lang|ruby on rails|\bror\b|\bphp\b|laravel|"
    r"salesforce|servicenow|\bpega\b|guidewire|coupa)"
    r"[- /]*(?:is[- ]+)?(?:mandatory|only|required|must[- ]have|must have)|"
    r"(?:mandatory|required|must[- ]have|must have)[- /]+"
    r"(?:java|python|node\.?js|golang|salesforce|servicenow|\bpega\b)|"
    r"java full[- ]?stack developer|"
    r"principal engineer\s*\(\s*python",
    re.I,
)

BLACKLIST = TITLE_BLACKLIST  # alias

TITLE_OK = re.compile(
    r"architect|technical lead|tech lead|technology lead|engineering manager|engineering lead|"
    r"principal|staff|solution architect|software architect|application architect|"
    r"cloud architect|azure architect|platform architect|technical architect|"
    r"\.net|dotnet|c#|software (development )?manager|"
    # "Manager of Software Engineering" / "Director of Engineering" (JPMC-style titles)
    r"manager of (software|engineering)|director of (software|engineering)|"
    r"software engineering manager|"
    r"lead (software|development|engineer)|director|head of eng|"
    r"senior engineering|engineering director|"
    # Senior IC titles (campus .NET / platform runs) — not junior Software Engineer II
    r"senior software engineer|sr\.?\s*software engineer|senior (dotnet|\.net|c#)|"
    r"senior (application|platform|backend) engineer",
    re.I,
)

HYD_OK = re.compile(
    r"hyderabad|telangana|secunderabad|greater hyderabad|gachibowli|hitech city|"
    r"madhapur|kondapur|banjara hills|"
    r"حيدر\s*أ?باد|حيدرآباد|تلنگانہ|تلنغانا|تيلانجانا|سکندرآباد",
    re.I,
)
REMOTE_OK = re.compile(
    r"\bremote\b|\bwfh\b|work from home|india remote|fully remote|remote[, ]*india|"
    r"remote \(india\)|anywhere in india|"
    r"عن بعد|العمل من المنزل|العمل عن بعد|من المنزل",
    re.I,
)
INDIA_ONLY = re.compile(r"^(greater\s+)?india\b|^الهند\b", re.I)
BAD_CITY = re.compile(
    r"bengaluru|bangalore|pune|chennai|mumbai|delhi|noida|gurgaon|gurugram|"
    r"ahmedabad|kolkata|jaipur|kochi|trivandrum|thiruvananthapuram|coimbatore|"
    r"indore|nagpur|panchgani|"
    r"\bmaharashtra\b|\bkarnataka\b|\btamil nadu\b|\bharyana\b|"
    r"united states|\busa\b|\buk\b|london|singapore|dubai|"
    r"toronto|canada|australia|germany|netherlands|"
    r"بنغالور|بنجالور|بانجلور|بوني|بونة|تشيناي|مومباي|دلهي|نويدا|جورجاون|"
    r"أحمد آباد|كولكاتا|جايبور|كوتشي|كوتشي|إندور|اندور|ناجبور|"
    r"ماهاراشترا|تاميل نادو|كارناتاكا|كارناتاكا|ماديا براديش",
    re.I,
)


def _primary_location_line(loc: str) -> str:
    """First location segment before ·/| and applicants noise — never full page chrome."""
    loc_s = (loc or "").strip()
    if not loc_s:
        return ""
    primary = re.split(r"\s*[·|]\s*", loc_s, maxsplit=1)[0].strip()
    primary = primary.splitlines()[0].strip() if primary else ""
    return primary[:160]


def location_allowed(loc: str, workplace: str = "", *, remote_search: bool = False) -> bool:
    """HARD filter: primary job location line + short workplace pills.

    Never let profile chrome 'Hyderabad' in a long workplace scrape false-allow
    Bengaluru/Mumbai. Empty primary location → reject.
    """
    loc_s = (loc or "").strip()
    work_s = (workplace or "").strip()
    if not loc_s and not work_s:
        return False

    loc_primary = _primary_location_line(loc_s)
    # Workplace pills only — truncate so People/JD chrome cannot inject cities.
    work_pills = "\n".join(work_s.splitlines()[:8])[:220]
    remoteish = bool(REMOTE_OK.search(f"{loc_primary} {work_pills}")) or remote_search

    # Hyderabad / Telangana on the primary location line (dual-city Hyd+BLR OK).
    if loc_primary and HYD_OK.search(loc_primary):
        return True

    # Non-Hyd city on the primary line → reject even if chrome mentions Hyd/Remote.
    if loc_primary and BAD_CITY.search(loc_primary) and not HYD_OK.search(loc_primary):
        return False

    # India-remote / bare Remote / WFH (primary loc must not be a bad city — checked above).
    if remoteish:
        if loc_primary and (
            INDIA_ONLY.search(loc_primary)
            or REMOTE_OK.search(loc_primary)
            or re.search(r"\bindia\b", loc_primary, re.I)
        ):
            return True
        if REMOTE_OK.search(work_pills) and (
            not loc_primary
            or INDIA_ONLY.search(loc_primary)
            or re.search(r"\bindia\b", loc_primary, re.I)
        ):
            # Empty primary with Remote pill alone is ambiguous — reject (prompt: empty → no).
            if not loc_primary:
                return False
            return True
        if remote_search and loc_primary and re.search(r"\bindia\b", loc_primary, re.I):
            return True
        return False

    return False


def jd_blacklist(text: str) -> str | None:
    """Form/JD hard mandatory patterns only (not title laundry list)."""
    m = JD_HARD_BLACKLIST.search(text or "")
    return m.group(0) if m else None


def skip_reason(role: str, company: str = "", jd: str = "") -> str | None:
    """Return skip reason or None. Title blacklist first; JD only for hard mandatory stacks."""
    title = role or ""
    company = company or ""
    if re.search(
        r"\b(ai/?\s*ml architect|ai architect|ai engineer|ml engineer|genai|"
        r"ai technical (lead|architect)|data scientist|data engineer(?:ing)?)\b",
        title,
        re.I,
    ) and not re.search(r"\.net|dotnet|\bc#\b", title, re.I):
        return "title: pure AI/data without .NET"
    # Company-primary wrong stacks (title alone may say System Architect)
    if re.search(r"pegasystems|\bpega\b", company, re.I) and not re.search(
        r"\.net|dotnet|\bc#\b", title, re.I
    ):
        return "company: Pega/Pegasystems"
    m = TITLE_BLACKLIST.search(title)
    if m:
        return f"title: {m.group(0)}"
    m = JD_HARD_BLACKLIST.search(jd or "")
    if m:
        return f"jd: {m.group(0)}"
    if company:
        m = TITLE_BLACKLIST.search(company)
        if m:
            return f"company: {m.group(0)}"
    return None
