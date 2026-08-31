# Naukri daily — 2026-08-31

## Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **1**
- externalCompleted: **0**
- blocked: **1**
- skipped: 2737 (dup-heavy) · seen: 182 · tailoredApplies: 1

## Profile resume refresh
- ok: true · matchedToken: Uploaded today · resume: Rafi_Resume.docx
- path: toptier-filechooser `#attachCV` / Update

## Applied
| Company | Role | Path | Resume |
| --- | --- | --- | --- |
| Accion Labs | Technical Architect | Naukri Quick Apply (chatbot:responses_thanks) | tailored `/tmp/naukri-tailored/0c37417e0fc6/Rafi_Resume.docx` |

- URL: https://www.naukri.com/job-listings-technical-architect-accion-labs-hyderabad-pune-bengaluru-12-to-18-years-310826001109?src=directSearch
- Location: Hyderabad, Pune, Bengaluru · query: dotnet architect · age: 1d

## Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | ats_password_policy (Create Account abort; no Sign In fallback) | company_ATS Workday |

- https://blackbaud.wd1.myworkdayjobs.com/en-US/ExternalCareers/job/Hyderabad---India-(Skyview)/Software-Engineer--Principal---NET-DevOps_R0014448/apply/autofillWithResume

## Notable skips
- Clean Harbors — .Net TEchnical Architect — already_applied_detail
- Incedo — .Net Lead — skip_ctc_max_30 (<35 LPA floor)
- Leading Client — .NET Full Stack Developer — skip_seniority
- Rapidue — Solution Architect — hirist_login_required_skip (expected)
- Thin .NET title inventory today (4 .NET titles in 182 seen); early+age+extra query expand ran

## Code fix this run
- `tools/naukri/workday_apply.js`: Create Account `ats_password_policy` / login_wall now falls through to Sign In; `authFailureReason` ignores static Password Requirements checklist; `test_workday_auth.js` added

## Post-fix re-run #1 (main @ 688ff71 / PR #297)

Ran `daily_apply.js` on merged main so today's applies used the Sign In fallback.

### Counts
- profileUpdated: **true** (`Rafi_Resume.docx`, Uploaded today)
- applied: **0** (Accion Labs listing not in inventory this pass; no invented applies)
- externalCompleted: **0**
- blocked: **1**
- skipped: 2757 (dup-heavy) · seen: 195 · tailoredApplies: 0
- already_applied_detail: Clean Harbors .Net TEchnical Architect; Sidgs Digisol Apigee Architect

### Blocked
| Company | Role | Reason | Path |
| --- | --- | --- | --- |
| Blackbaud | Software Engineer, Principal - .NET DevOps | ats_login_wall (Sign In fallback ran; Create Account never submitted) | company_ATS Workday |

Live inspect of Blackbaud Create Account: email + password + verifyPassword + `createAccountSubmitButton` + `signInLink`. **No** `createAccountCheckbox` / consent copy. `submitCreateAccount()` required a checked consent box, so it no-op'd; Sign In then walled because no tenant account exists.

### Code fix after re-run #1
- `tools/naukri/workday_apply.js`: treat missing consent checkbox/copy as optional so Create Account actually submits (Blackbaud). Wells Fargo-style pages still require the box.

## Post-fix re-run #2 (branch `c79cbbd` — consent optional)

- profileUpdated: **true**
- applied: **0** · blocked: **1** · skipped: 2764 · seen: 182
- Blackbaud: Create Account **succeeded** (signed in; Autofill + My Information completed). Then `external_incomplete_or_timeout` on Application Questions — required Select One dropdowns (age 18, sponsorship, start, salary, non-compete) never opened.

### Code fix after re-run #2
- `workdayQuestionAnswer` + Select One listbox / salary text fill on `formField-*` prompts.

## Post-fix re-run #3 (branch `474c294` — Select One filler)

- profileUpdated: **true**
- applied: **0** · blocked: **1** · skipped: 2810 · seen: 183
- Blackbaud: signed in; stuck on My Information — previous-worker Yes left work-email required; Country = Holy See (Vatican). `external_incomplete_or_timeout`.

### Code fix after re-run #3
- Click No on previously-worked/contracted copy; `needsIndiaCountryFix` resets any non-India country.
