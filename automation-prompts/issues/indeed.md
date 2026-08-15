# Indeed — issues & fixes

## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply 'tell us unique' matched tel and got phone; start date and Yes I certify left empty | Stop matching tel inside tell; fill start date 15/08/2026; tick Yes I certify |
| SmartApply full name got Yes leftover; years combobox stayed Select an option | Map full name to Mohammed Abdul Rafi Ahmed; open education/years listboxes and pick B.Tech / 10+ |
| India homepage Get Started treated as signed-out after CF (false indeed_login_required; Passport cookies valid) | Confirm session on secure.indeed.com/settings/account; copy Local State into UC hybrid; fill known DOB 16/01/1989 |
| Indeed applystart/rc/clk still counted as company-site (did_not_leave_indeed) and Easy Apply 'external' credited a click | Follow applystart hops; complete_ats_url waits off Indeed; finish_company_site on both company-site click and Easy Apply flip; confirmation only |
| Company-site clicks counted as external without ATS submit (28 opened / 0 completed) | complete_external_ats via Playwright; only count confirmation; do not credit external_opened |
| uc_daily_apply clear_cf returned True without post-Turnstile reload → anonymous Get Started / false indeed_login_required after preflight Welcome | Reuse cf_bypass_uc.try_clear_strategies (wait+focus+reload) in clear_cf; retry reload once before login_required |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| login-failed report counted as same-day coverage so ensure-missing skipped re-run | ensure-missing only treats usable apply/scan reports as coverage; force-restore sessions before launch |
| UC CF cleared but anonymous Sign-in home → 0 seen silent fail | Detect unsigned-in home after clear_cf; exit 5 with indeed_login_required |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh indeed "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

_No entries yet for this portal on the new per-portal log._
