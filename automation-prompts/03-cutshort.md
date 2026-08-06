# Cutshort Daily 9 AM — paste into Agent instructions

Automation: https://cursor.com/automations/d6ba8b9d-9094-11f1-ba66-0e7d0216e441

Copy everything inside the block below:

```text
FIRST: run `bash scripts/preflight-portal-run.sh cutshort`. Verify questionnaire helpers with `node tools/cutshort/questionnaire.js`.
Then run `bash scripts/launch-chrome-cdp.sh cutshort` if using browser/CDP.
Prefer Chrome CDP profile /home/ubuntu/chrome-cutshort-profile (synced from Desktop Default).

Run the daily Cutshort job-search and apply flow for Rafi Ahmed.

Profile:
- Solutions Architect / Technical Lead | 15+ years | .NET/C#, React, AWS/Azure, microservices
- Hyderabad + Remote/WFH | Immediate | Current 52 LPA | Expected **65 LPA**
- Email rafi.success@gmail.com | Phone +91 8790251698
- Resume: **Rafi_Resume.docx** (bootstrap paths). Upload on any external ATS.

## Resume (HARD)
Use only Rafi_Resume.docx from /workspace/resumes or /home/ubuntu/resumes. Never invent stubs.

## Daily order
1. Newest find-jobs / matchesfor={seekerId}
2. Tier 1: Architect / Tech Lead / EM / Principal / Staff / Head Eng with .NET/cloud fit
3. Tier 2: .NET/C#/Azure senior fullstack-backend / platform lead
4. Tier 3 stretch only if Hyd/remote and CTC band can reach ~55+ (still state 65 expected)
5. Skip QA/SDET/junior/SAP/Workday-Dynamics-primary/pure data/sales/BD/low YOE/listed max <50L
6. Answer ALL questionnaires after EACH apply (not in a careless batch)
7. Report applied / already / failed / questionnaires filled vs locked-empty

## Questionnaire rules (CRITICAL FIX)
- Use helper shape from tools/cutshort/questionnaire.js
- POST body: messageId + questions[]._id=answerRowId + question="<questionIdString>" + responseStringArray:[optionId]
- NEVER set screeningSubmitted:true until loadthread shows non-empty responses
- Wrong nested question object + screeningSubmitted returns 200 but locks EMPTY answers (400 retry) — treat that as failure
- Prefer UI leaf option-div clicks with request capture; verify before submit
- Notice: immediate. Salary band Yes only if max>=55 else No. Free-text expected 65 LPA.
- Location: Hyderabad/remote

## Apply notes
Hi {first name}; JD fit + proof + Hyd/immediate/52→65; ask 15–20 min screen or HM referral.

## External ATS
If Cutshort opens company careers, complete with Rafi_Resume.docx then continue.

## Hard constraints
- One job URL at a time; stop if Candidate login missing
- Tighten filters: no bare "platform" match (avoids Mac Admin / IAM false applies)
- Do not invent applications
- Count locked-empty questionnaires as failures, not Failed:0
```
