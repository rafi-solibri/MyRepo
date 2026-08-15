# Naukri — issues & fixes

## 15 Aug 2026 (cloud)

| Issue | Fix |
| --- | --- |
| PwC apply_unconfirmed: military-service chatbot chips (Never served) ignored | daily_apply.js collects .chatbot_Chip; score Never served over Currently/Previously served |
| Jade/PwC apply_unconfirmed: chatbot Save disabled on .Net/Java multiselect checkboxes (mcc__checkbox) | daily_apply.js answers multiselect skill checkboxes preferring .NET; chatbot_answers.js + tests; also skip D365/cyber architecture titles |


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
