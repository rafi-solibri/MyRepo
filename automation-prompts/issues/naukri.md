# Naukri — issues & fixes

## 2026-09-01 (cloud)

| Issue | Fix |
| --- | --- |
| False Quick Apply TCS Azure Infra Architect - S (AWS/GCP/Cloud Infra already skipped) | Title-skip azure infra(structure)? architect in SKIP_TITLE (with aws) and PURE_AI_DATA (with aws/gcp/cloud); Azure Architect .NET still applies |
| False Quick Applies: Oracle PaaS/HCM/ERP, Fusion HCM, IMDS, IT Shared Services; DFT/ATPG ATS burn; Data Architecture / Cloud Infra Architect not title-skipped | Expand NON_DOTNET_PRIMARY (oracle paas/hcm/erp/ebs, fusion hcm), SKIP_TITLE (imds, dft/atpg/jtag/mbist/tessent/testmax, it shared services), PURE_AI_DATA (data architecture, cloud infra architect) |


## 2026-08-31 (cloud)

| Issue | Fix |
| --- | --- |
| Blackbaud Workday Create Account returned ats_password_policy and aborted without Sign In (missed existing tenant account) | workday_apply: on Create Account password_policy/login_wall fall through to Sign In; tighten authFailureReason to ignore static Password Requirements checklist |


## 2026-08-29 (cloud)

| Issue | Fix |
| --- | --- |
| False Quick Apply Teamcenter/Windchill/AWS Infra Architect (TCS 2026-08-29) | Title-skip teamcenter\|windchill\|plm\|aws infra architect in resume_and_filters.js |


## 2026-08-28 (cloud)

| Issue | Fix |
| --- | --- |
| Broadcom Workday: fillFieldInput matched wrapper div so phone stayed +91… and names ALL-CAPS; empty companyName / multi-row degree Select One blocked My Experience | Prefer nested input in fillFieldInput; normalizeWorkdayPhone strips +91; fillWorkExperience from title/desc; per-row 70-Bachelor degree + Siddhartha school; title-skips for BigData/Copilot/Oracle EPM/Meraki/UI/Security/Tableau/Sharepoint/SD-WAN false Quick Applies |


## 2026-08-26 (cloud)

| Issue | Fix |
| --- | --- |
| Netcool Architect + Cadence Principal Design Engineer burned Quick Apply/ATS (not .NET / EDA IC) | skip Netcool titles; skip Cadence company; skip Design Engineer without software/.NET |


## 2026-08-25 (cloud)

| Issue | Fix |
| --- | --- |
| Naukri still uploading stale/old Rafi_Resume.docx instead of latest Mohammed_Abdul master | ensure_upload_resume.py always rebuilds Rafi_Resume from owner master on bootstrap + STEP 0 + daily_apply; never trust committed upload copy |
| Naukri profile STEP 0 silent-fail: master resume ~3.9MB (embedded fonts) exceeds TopTier 2MB client reject; sync-chrome-sessions DESTS[] missing hirist/linkedin_alt entries (unbound variable); Update confirmSave re-opened filepicker | compress_resume_docx.py strips embeds in bootstrap; update_profile_resume TopTier filechooser+#resume+Uploaded today/DD-MM-YYYY verify; sync-chrome-sessions DESTS/COOKIE_SETS/REQUIRED aligned to 8 portals |


## 2026-08-24 (cloud)

| Issue | Fix |
| --- | --- |
| Fullstack Developer Lead / Fullstack Lead / Software Development Manager false skip_no_dotnet (isArchLeadTitle miss) + Node.js SA / Full Stack AI Manager burns | Expand ARCH_LEAD_RE for developer/fullstack lead + software development manager; add node.js to NON_DOTNET_PRIMARY; Full Stack AI Manager to PURE_AI_DATA |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-24) | Replaced master + Rafi_Resume.docx alias; JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 late) | Replaced master + Rafi_Resume.docx alias (~3.9MB); JD tailor still on top; upload label stays Rafi_Resume |
| Owner refreshed master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx (2026-08-23 evening) | Replaced resumes/Mohammed_Abdul_Rafi_Ahmed_Resume.docx + Rafi_Resume.docx alias; JD tailor still runs on top; upload filename stays Rafi_Resume |


## 2026-08-23 (cloud)

| Issue | Fix |
| --- | --- |
| Owner supplied new master resume Mohammed_Abdul_Rafi_Ahmed_Resume.docx | Synced into resumes/Rafi_Resume.docx (+ Architect alias); bootstrap prefers owner-named file; JD tailor still runs on top; upload filename/label stays Rafi_Resume |
| Globallogic Senior Architect AI/Java JD false-apply + apply_unconfirmed on disabled dual-layer CTA | shouldSkipNonDotNetPrimaryJd on detail + readVisibleApplyCta treats disabled Quick apply Applied as applied |


## 2026-08-22 (cloud)

| Issue | Fix |
| --- | --- |
| False-applied Mulesoft Architect, MS Fabric/Synapse/Databricks, and DevOps Architect titles (2026-08-22 morning) | SKIP_TITLE_RE: mulesoft\|mule soft\|ms fabric\|microsoft fabric\|synapse\|databricks\|datalake\|data lake\|devops architect (+ tests) |


## 2026-08-21 (cloud)

| Issue | Fix |
| --- | --- |
| False-applies Observability/Datadog + Infrastructure Engineer + Analog IC + Digital Verification; Data and AI not skipped; end-of-run profile restore timed out with 14 mnjuser/profile tabs | Skip observability/datadog/infrastructure engineer/analog IC/digital verification/VLSI/ASIC/FPGA titles; match data and AI; prune excess profile tabs in daily_apply + reuse profile tab + goto retries in update_profile_resume |


## 2026-08-20 (cloud)

| Issue | Fix |
| --- | --- |
| Applications rejected by AI/manual screening despite applies | Per-job truthful JD tailor (headline/summary) + profile sync before Quick Apply + ATS upload of tailored Rafi_Resume.docx |
| Mainframe Architect band titles false-applied (no .NET stack) | NON_DOTNET_PRIMARY_RE: skip mainframe/cobol/as400/ibm i without .NET on title |


## 2026-08-17 (cloud)

| Issue | Fix |
| --- | --- |
| Pega LSA / AI Engineering Manager / Data Architect / GCP Infra attempted; 3 apply_unconfirmed (no_chat) + Principal Financial chat_steps_exhausted; thin Hyd/.NET inventory | resume_and_filters: skip Lead System Architect + AI EM + Data/GCP Infra Architect; shouldSkipCompany for Pega/Coupa/Salesforce/SAP; daily_apply Escape+re-read Applied after no_chat |


## 2026-08-16 (cloud)

| Issue | Fix |
| --- | --- |
| 0 applies: Gemini Platform Architect attempted + apply_unconfirmed (empty CTA/no_chat); Principal Financial chat_steps_exhausted; thin eligible inventory (CTC<35 skips Valuelabs/Sonata/Highradius/Watania) | resume_and_filters: skip gemini/llm GenAI titles; daily_apply: longer Applied poll + disabled CTA + drawer Submit/Continue recovery + Escape re-read after chat_steps_exhausted |


## 2026-08-15 (home)

| Issue | Fix |
| --- | --- |
| Overlapping home portals killed shared system Chrome: Git Bash /proc never matched chrome.exe so every launch-chrome-cdp restart wiped mid-apply; also PowerShell -File on MSYS /tmp .ps1 never started Chrome | launch-chrome-cdp.sh: Windows PowerShell Win32_Process reuse for system :9222; write launch .ps1 under artifacts/ + cygpath -w; inline Start-Process fallback |
| Git Bash mangled taskkill /F so system Chrome never died; Start-Process handed off without remote-debugging → Playwright cdp_connect_failed / stale :9222 | launch-chrome-cdp.sh: PowerShell multi-retry Stop-Process + Singleton* clear + wait until :9222 down before relaunch |


## 2026-08-15 (cloud)

| Issue | Fix |
| --- | --- |
| Workday Create Account rejected stored secret (same Solera wall as careers) | Create Account uses deterministic 12+ complexity password shared with tools/ats/complete.py |
| homepage card role parse; Manager SW/CTO; chatbot .Net+Java; View applied jobs | parseNaukriCardLines; ARCH_LEAD SW/CTO; prefer .NET-only multiselect; View applied = applied |
| button:has-text('Apply') clicked View applied jobs (20+) → apply_unconfirmed; brochure careers.html burned 6.5m as external_incomplete_or_timeout | isFalseApplyCta skips View applied/applied jobs; brochure fail-fast no_ats_form; handleExternal uses completeExternalPage |
| SmartRecruiters/Workday timeouts + Lloyds maintenance + chatbot ignored .NET/Java checkboxes and Never served | Fail-fast unavailable; skip D365/cyber architecture; chatbot stack checkboxes + military No |
| Workday Python/JS password miss when only LINKEDIN_PASSWORD/NAUKRI_WORKDAY_PASSWORD set | Password chain includes NAUKRI_WORKDAY_PASSWORD + LINKEDIN_PASSWORD; richer Workday fill |
| external_incomplete_or_timeout — hidden reCAPTCHA treated as wall; GH questions only on some hosts; one Next then bail | Visible-challenge CAPTCHA only; always fillCommonAtsQuestions; retry 4x; 6.5m budget; shared WORKDAY_PASSWORD |


## 2026-08-14 (home)

| Issue | Fix |
| --- | --- |
| Wrong applies: TOSCA Automation Architect, Embedded Technical Architect, Artificial Intelligence Architect | resume_and_filters.js: skip tosca/embedded/firmware + artificial intelligence architect |
| Node /opt vs Git Bash /opt split on Windows — apply JSON not dual-written to repo artifacts | Wire daily_apply/update_profile_resume/home_run_report through tools/artifact_path.js dual-write |


## 2026-08-14 (cloud)

| Issue | Fix |
| --- | --- |
| Applied Senior Manager Attack Surface Reduction (cyber) via Senior Manager arch-lead waiver | SKIP_TITLE_RE: attack surface / cybersecurity / infosec / SOC / MDR |


Portal-scoped log. Each daily agent (cloud or home) must append **only** to this file via
`bash scripts/append-issue-fix.sh naukri "issue" "fix"` — never edit `ISSUES_AND_FIXES.md` for same-day rows.

## 2026-08-14 (cloud cron)

| Issue | Fix |
| --- | --- |
| 13× `apply_unconfirmed` with `chat_steps_exhausted` / delayed drawer (Save no-op under overlay; narrow chips) | `daily_apply.js`: Playwright force Save, stuck detection, broader chips/select/textarea answers, late thanks confirm |
| Wrong applies/attempts: Gen AI SA, Agentforce, Network Support, Civil/Structural EM, QE Architect, Data Engineering Manager | `resume_and_filters.js` + `test_filters.js`: expand `SKIP_TITLE_RE` / `PURE_AI_DATA_RE` (`gen ai`, `ai agent`, Architect…AI/ML) |
