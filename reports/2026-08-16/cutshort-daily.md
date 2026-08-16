# Cutshort daily 2026-08-16

## Counts
- Scanned: **3193**
- Qualifying: **5**
- Applied: **5**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **5** | already-submitted: 45 | locked-empty: **322** | verify-empty: 0
- Awaiting listed: 372
- Failures (apply + locked-empty + verify-empty): **322**

## Applied
- T1 AWS Cloud Engineer @ TalentXO (35L) `69d2abf1cd2a926b7c87d29a` via=api_no_ui_button
- T1 Cloud AI Engineer @ Market Research Future Reports (35L) `6a326450fd1eea95398caae7` via=api_no_ui_button
- T3 Software Developer @ CipherSonic Labs (50L) `69bb49609b1b1b8f90b29902` via=api_no_ui_button
- T3 Software Engineer, Agent Infrastructure @ Terrabase (50L) `6a3a7dc61cdd426889d1186a` via=api_no_ui_button
- T3 Frontend Engineer @ Certa (45L) `69c3df50e901ab6a16b79dd7` via=api_no_ui_button

## Failed applies
_None_

## Questionnaires
- Answered this run: **5** (4 per-apply + 1 final audit; TalentXO had no pending Q on first pass)
- Already submitted (non-empty): 45
- Locked-empty (historical; cannot unlock in code): **322** — counted in failure total, not same-day apply failures
- Verify-empty: 0

## Pre-fix vs post-fix (this session)
- First pass on merged `main` (CDP disconnect/`process.exit` fix): scanned 3202, **qualifying=0**, hung no longer — runner exited 0
- Skip taxonomy that pass: `ctc_under_35=1161` `exp_max_low=1024` `skip_title=755` `location=214` `no_tier_match=48`
- Filter fix then re-ran apply: scanned 3193, **qualifying=5**, **applied=5**, Q answered=5
- Resume: `resumes/Rafi_Resume.docx` | Expected 65 LPA | Current 52 LPA | Hyd + Remote

## Code fix (this run)
- Classifier required senior/lead in title, so AWS Cloud Engineer (Hyd) and SWE+React/AWS/GenAI were `no_tier_match`
- Also rejected Almaty-only `remote_okay` and title-skipped marketing/data/IAM/Salesforce-primary
- Branch pushed: current post-fix re-run feature branch
- PR create: GitHub token `403 Resource not accessible by integration`; ManagePullRequest waiting on user approval
- Artifact: `/opt/cursor/artifacts/` daily-run JSON
