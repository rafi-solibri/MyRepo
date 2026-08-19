# Naukri — issues & fixes

## 2026-08-19 (cloud)

| Issue | Fix |
| --- | --- |
| TCS Power Bi Architect attempted via Architect waiver (apply_unconfirmed/no_chat); power platform already skipped but power bi was not | resume_and_filters SKIP_TITLE_RE: power bi / powerbi / bi architect so Architect/Lead waiver does not burn Quick Apply on BI-only titles |


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
