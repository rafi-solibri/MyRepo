# Naukri — issues & fixes

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
