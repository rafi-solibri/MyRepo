# Indeed Daily — 2026-08-15 (post-fix re-run)

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`)  
Resume: `resumes/Rafi_Resume.docx`  
Main at start: `ce373d6` (#160 ATS complete). Also pulled #161–#163 ATS helpers mid-run.  
Session: warmed via account settings (India homepage Get Started is not signed-out).

## Counts (no invented applies)

| Metric | Count |
| --- | ---: |
| Applied (Easy Apply submitted) | 0 |
| External ATS completed | 0 |
| Rejected / incomplete | 6 |
| Blocked | 12 |
| Skipped | 22 |
| Seen | 41 |

## What ran
- `node tools/indeed/preflight.js` — WARP+UC cleared Turnstile (exit 0).
- First `daily_apply.js` exited `indeed_login_required` on marketing-home Get Started while account settings + SERP Messages were logged in (false positive).
- Fixes on `cursor/indeed-daily-post-fix-re-run-2026-08-15-8a11`: session warm, education/years combobox, URL `jk=` dedupe, notice 1-30 Days, title Mr.
- Re-ran `uc_daily_apply.py` logged-in. Easy Apply reached review (Frontline) then reCAPTCHA Enterprise. Company-site ATS followed Indeed applystart hops but did not reach confirmation (generic careers pages / timeouts / one CAPTCHA).

## Residual (not invented)
- SmartApply review reCAPTCHA Enterprise (audio attempted; submit did not confirm).
- Employer question walls (notice radios, work-auth, title/DOB) — later commits map more of these.
- Company careers listings without a completable apply form.

## Branch
Pushed `cursor/indeed-daily-post-fix-re-run-2026-08-15-8a11`. `gh pr create` is not permitted for this integration; open the PR from the branch when ready.
