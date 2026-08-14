# Foundit daily — 2026-08-14

## Summary
- Login: **Hi, Rafi Ahmed Mohammed Abdul** (MSSOAT OK; `/home/user` confirmed)
- Resume: `resumes/Rafi_Resume.docx`
- Applied tab: **410 → 414** (+4)
- Intentional applies logged: **4**
- Duplicates: 34 | Skipped: 500 | Blocked: 0
- Artifact: `/opt/cursor/artifacts/foundit-apply-report.json`
- No `canJobApply` dry-run calls

## Applied
1. **Mphasis** — Senior Software Engineer — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4451101638` (`linkedin_no_easy_apply`) — Singapore | remote
2. **Salesforce** — Agentforce - Sucess Architect — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4452468078` (`linkedin_no_easy_apply`) — Hyderabad *(false apply — Agentforce/Salesforce skip missed; fix in progress)*
3. **Tata Consultancy Services** — Dot NET Full Stack Lead — Foundit Falcon `NORMAL` — Hyderabad
4. **Jobgether** — Senior Azure AppDev Architect (Remote) — Foundit Falcon `APPLY_REDIRECT_STAGE_ONE` + LinkedIn `4366309400` (`linkedin_no_easy_apply`) — Indonesia | Remote

## Top skip reasons
- no .NET on title+skills: 158
- no seniority keyword on title: 107
- location Bengaluru: 70+
- location Pune: 26
- junior/mid maxExp bands: ~38
- other non-Hyd cities / low CTC / WPF / PM

## LinkedIn referral drafts
1. Mphasis — Senior Software Engineer
2. Salesforce — Agentforce - Sucess Architect *(should not have applied)*
3. TCS — Dot NET Full Stack Lead

## Filter fix from this run
- `tools/foundit/filters.js`: skip `Agentforce`/`SFDC` titles; skip Salesforce employer when .NET is not on the title (skills laundry lists ignored).
