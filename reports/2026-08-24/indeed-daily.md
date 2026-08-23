# Indeed Daily — 2026-08-24 (post-fix re-run)

Same-day re-run on `main` after #245 (Mohammed_Abdul_Rafi_Ahmed_Resume master refresh).
Earlier 2026-08-23 cron did not apply with the new resume. This run used
`/workspace/resumes/Rafi_Resume.docx` (JD-tailored per job).

## Counts
- **Submitted (Easy Apply):** 2
- **External ATS confirmed:** 1
- **Rejected incomplete:** 4
- **Blocked:** 17
- **Skipped:** 35 (including already-applied + 5 bot-detection Sign In pages misclassified as `title_not_target`)
- **Seen:** 59
- **ok:** True
- **source:** cloud-warp-uc (WARP SOCKS + UC Turnstile)

## Applied (Easy Apply)
- **Genpact India Pvt. Ltd.** — Sr. Tech Lead - Application Development Microsoft N 4D — Hyderabad
- **Genpact India Pvt. Ltd.** — Architect - Enterprise Application - Oracle N 4D — Hyderabad

## External ATS confirmed
- **NTT Ltd** — Senior Application Architect — Hyderabad (confirmation)

## Blocked highlights
- Infor / NTT Phenom / ABSYZ Salesforce careers: `external_incomplete_or_timeout` or `no_ats_form` (reCAPTCHA / form cap)
- Wells Fargo / Medtronic Workday: `ats_login_wall`
- Some company sites: `ERR_SOCKS_CONNECTION_FAILED` through WARP
- Late inventory: Indeed `bot-detection-anonymous` Sign In hops (real jk= in continue2) were skipped as `title_not_target` instead of session restore

## Notes
- Preflight: WARP+UC cleared CF (exit 0). Session restored via `secure.indeed.com/settings/account`.
- Resume tailor ran; upload filename stayed `Rafi_Resume.docx`.
- Follow-up helper fix (this PR): do not treat Sign In / bot-detection as `title_not_target`; restore Passport and retry continue2; stamp report `date` as IST so Notification Job matches 2026-08-24.
- PRs: https://github.com/rafi-solibri/MyRepo/pull/245
