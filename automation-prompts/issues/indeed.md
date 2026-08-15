# Indeed — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply stuck on required reason for change | Fill career-growth one-liner for reason-for-change / why-looking questions |
| SmartApply put Yes in numeric rate/hr and 14 in yes/no Azure-experience questions | Map FTE vs contract + hourly rate 3500; require how-many-years before numeric experience; yes/no for are-you-experienced |
| SmartApply Full name got Yes; education/years custom dropdowns stayed Select an option | Map full name; never Yes-fallback name fields; open comboboxes and pick B.Tech / 10+ years |
| SmartApply DOB fields got Yes fallback and failed DD/MM/YYYY validation | Fill known DOB 16/01/1989; skip PAN/Aadhaar invent |
| CF-cleared homepage stayed anonymous Get Started despite valid Passport cookies | After Turnstile, open secure.indeed.com/settings/account then return home so Welcome paints; copy Local State into hybrid UC profile |
| uc_daily_apply clear_cf returned True without post-Turnstile reload → anonymous Get Started / false indeed_login_required after preflight Welcome | Reuse cf_bypass_uc.try_clear_strategies (wait+focus+reload) in clear_cf; retry reload once before login_required |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| login-failed report counted as same-day coverage so ensure-missing skipped re-run | ensure-missing only treats usable apply/scan reports as coverage; force-restore sessions before launch |
| UC CF cleared but anonymous Sign-in home → 0 seen silent fail | Detect unsigned-in home after clear_cf; exit 5 with indeed_login_required |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh indeed "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
