# Naukri daily — 2026-08-16 (post-fix re-run, merged #194)

## Summary
- Ran on `main` at `f8139c4` / later `39cc3e9` (includes `fix(naukri): skip Gemini titles and harden apply confirmation (#194)`).
- Profile resume refreshed: **yes** after the hydration fix (`Rafi_Resume.docx`, verify `Uploaded today` / `profileUpdated: true`). First `daily_apply` pass failed STEP 0 (`resume_file_input_not_found` on an empty profile SPA); `update_profile_resume.js` then succeeded on the same CDP session.
- **Real applies this session: 0** (do not invent applies).
- External / company-site completed: **0**
- Blocked: 1 · Skipped: 2952 · Seen: 206

## False apply (discarded — not counted)
- Sarthee Consultancy / “Hiring for a Beauty & Personal Care company” — Deputy Head of Manufacturing  
  `cta: view_applied_jobs` — persistent nav widget, not a per-job Applied CTA.

## Already applied (skipped, not re-counted)
- i2e Consulting — Solution Architect (`Applied`)
- Clean Harbors — .Net Fullstack Tech Lead (`Applied`)

## Blocked
- Principal Financial Group — Associate Director - Engineering (`apply_unconfirmed` / `chat_steps_exhausted`)

## Eligible .NET/SA cards correctly CTC-skipped (listed max &lt; 35 LPA)
- Valuelabs — .NET Architect (30)
- Incedo — .Net Lead (30)
- Sonata Software — Azure Solution Architect (31)
- Highradius — Senior Design Consultant/Solution Architect (30)
- Watania Solutions — Solution Architect (30)

## Code fix this run
- `confirmApplied` never treats `view_applied_jobs` as success
- Skip manufacturing / non-tech Head titles; `Head of Engineering` still applies
- Profile resume: wait for SPA hydration; keep last successful upload

## Artifacts
- `/opt/cursor/artifacts/naukri-daily-apply.json`
- `/opt/cursor/artifacts/naukri-profile-resume.json`
- Branch: `cursor/naukri-daily-post-fix-re-run-2026-08-16-b389`
