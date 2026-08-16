#!/usr/bin/env python3
"""LinkedIn eligibility filters — title-first blacklist (never incidental JD hits)."""

from __future__ import annotations

import re

# TITLE-only hard rejects. Do NOT run against full JD — incidental mentions
# (e.g. "data engineer peers", "Salesforce integration") false-skip good roles.
TITLE_BLACKLIST = re.compile(
    r"salesforce|servicenow|guidewire|splunk|\bpega\b|oracle\s*erp|sitecore|"
    r"\bmean\b|devops engineer|sre engineer|site reliability engineer|gcp.?presales|workato|mulesoft|"
    r"blockchain|mandarin|biztalk|firmware|\bmes\b|\bror\b|ruby on rails|"
    r"\bsap\b|dynamics\s*365|\bd365\b|esri|\bgis\b|"
    r"java full[- ]?stack|java[- ]?(mandatory|only|required|backend)|"
    r"\bjava\b(?!.*(?:\.net|dotnet|c#))|"  # Java primary titles (allow if .NET also on title)
    r"node\.?js[- ]?(mandatory|only)|"
    r"python[- ]?(mandatory|only)|principal engineer\s*\(\s*python|"
    r"\bdata engineer\b|\bmachine learning engineer\b|"
    r"big data architect|\bdata architect\b|data warehouse architect|implementation specialist|"
    r"\bphp\b|laravel|"
    r"interior designer|civil engineer|electrical engineering|electrical design|"
    r"golang &|golang and|"
    r"bpo|call center|marketing cloud|success architect|"
    r"non-?it staffing|us non-?it|staffing recruiter|talent acquisition|"
    r"\brevit\b|\bbarch\b|hubspot|m365 architect|microsoft 365 architect|"
    r"solutions engineer|presales|pre-sales|"
    r"\binfor\b|\berp\b.?primary|dft architect|\beda\b|"
    r"ai compiler|gen[- ]?ai architect|ai/?\s*ml architect|ai architect(?!.*\.net)|"
    r"ai technical (lead|architect)|"
    r"quality engineering|quality assurance|qa engineer|\bsdet\b|"
    r"netsuite|nice cxone",
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
    r"lead (software|development|engineer)|director|head of eng|"
    r"senior engineering|engineering director",
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
    r"indore|nagpur|united states|\busa\b|\buk\b|london|singapore|dubai|"
    r"toronto|canada|australia|germany|netherlands|"
    r"بنغالور|بنجالور|بانجلور|بوني|بونة|تشيناي|مومباي|دلهي|نويدا|جورجاون|"
    r"أحمد آباد|كولكاتا|جايبور|كوتشي|كوتشي|إندور|اندور|ناجبور|"
    r"ماهاراشترا|تاميل نادو|كارناتاكا|كارناتاكا|ماديا براديش",
    re.I,
)


def location_allowed(loc: str, workplace: str = "", *, remote_search: bool = False) -> bool:
    """HARD filter: only job location/workplace strings — never page chrome/profile text."""
    text = f"{loc} {workplace}".strip()
    if not text:
        return False
    remoteish = bool(REMOTE_OK.search(text)) or remote_search
    # Hyderabad (even dual-city "Delhi & Hyderabad") is allowed.
    if HYD_OK.search(text):
        return True
    # India-remote / bare Remote / WFH is OK — but Remote Canada/US/UK is not.
    if REMOTE_OK.search(text):
        if BAD_CITY.search(text) and not HYD_OK.search(text):
            return False
        return True
    # Non-Hyd bad cities without Remote → reject
    if BAD_CITY.search(text) and not REMOTE_OK.search(text):
        return False
    if remoteish and INDIA_ONLY.search((loc or "").strip()):
        return True
    if remoteish and re.search(r"\bالهند\b", text) and not BAD_CITY.search(text):
        return True
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
        r"ai technical (lead|architect)|data scientist|data engineer)\b",
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
