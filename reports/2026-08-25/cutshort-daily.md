# Cutshort daily 2026-08-25

POST_FIX_RERUN=1 on merged `main` @ `0df8822` (`fix(hitechcity): read ATS email OTPs from Gmail mailbox` #264).
This is same-day re-run **5 / 5** (IST cap). No further post-fix cloud re-run launched.

## Counts
- Scanned: **3273**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 0 | locked-empty: **0** | verify-empty: 0
- Awaiting listed: 0
- Failures (apply + locked-empty + verify-empty): **0**
- Tailored resumes: built **0** | profile uploaded **0** | upload failed 0

## Skip reasons
- `ctc_under_35`: **1216**
- `exp_max_low`: **1019**
- `skip_title`: **767**
- `location`: **225**
- `no_tier_match`: **46**

## Applied
_None_ — do not invent applies. No jobs already applied today to skip.

## Failed applies
_None_

## Login / resume / CDP
- Preflight portal run script: OK (candidate auth cookie present on the synced Chrome profile)
- Questionnaire helper: `Rafi_Resume.docx` + expected 65 LPA
- Chrome CDP :9222 with the portal profile
- Resume: `resumes/Rafi_Resume.docx` rebuilt from `Mohammed_Abdul_Rafi_Ahmed_Resume.docx` (upload 20945B)

## Near-miss check (not applied)
Live CDP dump after the runner (Hyd / remote / .NET / Azure waves). Closest cards were correctly skipped:

- Technical Architect @ Haparz — **28L** (Hyd among cities) — listed max under 35L
- Dot Net Azure Full Stack @ Workcubcle — **28L** (Hyd among cities) — listed max under 35L
- Sr .NET Lead @ Newaetate — **30L**, Chennai only
- Team Lead VB.Net @ Aanet Talent — **32L**, Tamil Nadu cities only
- Fullstack .NET Engineer @ Unique Occupational — **35L**, **Pune only**
- Senior Java Architect @ Wissen — **45L**, Bengaluru only
- Associate Technical Architect - Data @ Quantiphi — **40L**, Mumbai/Bengaluru only
- `no_tier_match` leftovers: data scientist / PHP / Salesforce / ServiceNow / UX / DB / sales / ontologist — not Architect / Tech Lead / EM / Senior .NET

No new code-fixable classifier or apply-path blocker. ATS email-OTP helper from #264 was loaded; no external ATS apply ran because qualifying=0.
