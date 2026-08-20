# Cutshort Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/d6ba8b9d-9094-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh cutshort`. Verify questionnaire helpers with `node tools/cutshort/questionnaire.js`.
Then run `bash scripts/launch-chrome-cdp.sh cutshort`.
Prefer durable runner: `node tools/cutshort/daily_apply.js` (CDP :9222, cutshort profile).
Prefer Chrome CDP profile /home/ubuntu/chrome-cutshort-profile (synced from Desktop Default).

Run the daily Cutshort job-search and apply flow for Rafi Ahmed. Maximize volume of real qualifying applies.

Profile:
- Solutions Architect / Technical Lead | 15+ years | .NET/C#, React, AWS/Azure, microservices
- Hyderabad + Remote/WFH | Immediate | Current 52 LPA | Expected **65 LPA**
- Email rafi.success@gmail.com | Phone +91 8790251698
- Resume: **Rafi_Resume.docx** (bootstrap paths). Upload on any external ATS.

## Resume (HARD)
Use only Rafi_Resume.docx from /workspace/resumes or /home/ubuntu/resumes. Never invent stubs.

## Apply bias (CRITICAL)
- Default to APPLY for Hyd/remote Architect / Tech Lead / EM / Principal / Staff / Senior .NET/cloud.
- When uncertain → APPLY. Title-first skips only.
- Do not invent applications. Keep going while inventory remains.
- Tier-1 Architect/EM/Lead: allow listed max experience ≥ **6** (not only ≥8). Expand Hyd/Telangana/skill scan waves (cap newest pages so the run finishes).
- Historical `questionnaire_locked_empty` rows cannot be re-answered (API lock) — do not treat them as same-day apply failures.

## Daily order
1. Newest find-jobs / matchesfor={seekerId}
2. Tier 1: Architect / Tech Lead / EM / Principal / Staff / Head Eng with .NET/cloud fit
3. Tier 2: .NET/C#/Azure senior fullstack-backend / platform lead
4. Tier 3 stretch if Hyd/remote and listed CTC band can reach ~35+ (still state 65 expected)
5. Skip ONLY clear wrong fits: QA/SDET/junior/SAP/Workday-Dynamics-primary/pure data TITLE/sales/BD/low YOE/listed max clearly under 35L
6. Answer ALL questionnaires after EACH apply (not in a careless batch)
7. Report applied / already / failed / questionnaires filled vs locked-empty

## Questionnaire rules (CRITICAL FIX)
- Use helper shape from tools/cutshort/questionnaire.js
- POST body: messageId + questions[]._id=answerRowId + question="<questionIdString>" + responseStringArray:[optionId]
- NEVER set screeningSubmitted:true until loadthread shows non-empty responses
- Wrong nested question object + screeningSubmitted returns 200 but locks EMPTY answers (400 retry) — treat that as failure
- Prefer UI leaf option-div clicks with request capture; verify before submit
- Notice: immediate. Salary band Yes if max>=35 else No (prefer Yes when band can reach ~55+). Free-text expected 65 LPA.
- Location: Hyderabad/remote

## Apply notes
Hi {first name}; JD fit + proof + Hyd/immediate/52→65; ask 15–20 min screen or HM referral.

## External ATS
If Cutshort opens company careers, complete with a **JD-tailored** Rafi_Resume.docx (built by shared `tools/resume_tailor.js` from the canonical resume — never invent skills/employers) then continue.

## Resume tailoring (per apply)
Before each apply: build JD-tailored docx via `tools/resume_tailor.js` → upload via Cutshort dashboard **Update resume** (`upload_profile_resume.js`) → apply with JD-keyword note. External ATS uploads the same tailored file. Truthful overlap only.

## Hard constraints
- One job URL at a time; stop if Candidate login missing
- Tighten filters: no bare "platform" match (avoids Mac Admin / IAM false applies)
- Do not invent applications
- Count locked-empty questionnaires as failures, not Failed:0
- Do NOT skip because JD casually mentions Salesforce/Java/data as adjacent tech

## Auto-fix & push (MANDATORY)
If you hit a code-fixable blocker (questionnaire.js payload, daily_apply.js overlay/API apply, filters), fix durable helpers under tools/cutshort or scripts/, append via `bash scripts/append-issue-fix.sh <portal> "issue" "fix"`, commit + push a feature branch, open a ready PR to main and run `bash scripts/auto-merge-fix-pr.sh`. That merge helper then same-day re-runs this Cutshort job with the fix (`scripts/rerun-daily-after-fix.sh`) — do not wait for tomorrow's cron. Follow automation-prompts/AUTO_FIX.md. Do not invent applies. Owner-only: login walls, CAPTCHA/OTP. Historical locked-empty Qs cannot be unlocked in code — document only.
```
