# Indeed — issues & fixes

## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply resume-selection: We could not upload your resume file then Continue stuck (5 easy_apply_incomplete); cloud ATS parked 10m+ on NTT ASK_OWNER headed wait | Retry/fallback SmartApply resume upload (tailored then master <5MB); do not Continue on upload error; cloud sets ATS_OWNER_ASLEEP so ATS does not park 6-12m |


## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| pagead SERP repeats same jk (PanApps 11x); Title/Phone/Date/Address/India-Standard SmartApply still incomplete; UC runner killed ~90m without finishedAt | Post-open jk dedupe + vjk/encoded jk; address/postal/+91 phone fills; Title/Phone/Date/India-Standard validation recovery; UC timeout 120m + atexit flush |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |


## 2026-08-22 (cloud)

| Issue | Fix |
| --- | --- |
| UST/LTM SmartApply stuck: bare Date + Title Mr radios still incomplete | Map bare Date→available (ISO via setNative); harden Title Mr input/label click; based-in→yes |


## 2026-08-21 (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply education combobox + Title Mr/Ms left on Select an option (ValGenesis/LTIMindtree easy_apply_incomplete) | Label scan includes education/degree; recover_required_selects open→wait→pick for education/Title/Country; validation recovery for Choose an option |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Indeed still uploaded static resume; ATS/AI screening rejected keyword-mismatched applies | Wire tools/resume_tailor.tailor_resume_for_job into uc_daily_apply before Easy Apply/ATS; upload via RESUME_UPLOAD_PATH |
| SmartApply incomplete: company ATS misclassified as indeed_login_required; bare Date→DOB poisoned UST; questions Continue stuck without reCAPTCHA attempt | looks_login_wall requires indeed host; off-Indeed EA→external; ISO date inputs; Available Date not DOB; questions CTA streak tries clear_recaptcha |


## 2026-08-17 (cloud)

| Issue | Fix |
| --- | --- |
| SmartApply Notice Period (in days) filled as Immediate; Country phone dial combobox left on Select an option → easy_apply_incomplete | fill_common_questions: numeric notice→0; Country/+91 combobox + validation recovery for Choose an option on Country |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
| Kochi/Kerala title with empty SERP location Easy-Applied; SmartApply 'already applied' misclassified as incomplete; mid-run secure.indeed.com/auth became incomplete | Expand LOC_HARD_SKIP for non-Hyd cities/states; detect already_applied + login_required inside easy_apply_flow and reclassify incomplete samples |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| SERP pagead repeats + SmartApply name/certify/start-date/tel=tell | job_dedupe_key from jk=; fill full name/start date/certify; stop tel matching tell |
| SmartApply put Yes into Date of birth / PAN and stalled on required employer questions | Fill DOB 16/01/1989 and title Mr.; never invent PAN/Aadhaar; stop defaulting leftover required text to Yes |
| UC CF cleared but India Get Started home false indeed_login_required (Passport cookies present; Local State not copied so v10 cookies could not decrypt) | Copy Local State into UC hybrid profile; restore session via Sign-in/account/myjobs; only exit login_required on a real Sign-in wall |
| applystart/rc/clk hops returned did_not_leave_indeed after 18s wait; company-site apply lost Passport session | extract hop dest from continueUrl/meta/outbound apply; warm_passport_session via secure.indeed.com/settings/account |
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
