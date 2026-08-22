# Indeed Daily — 2026-08-22 (post-fix re-run on #236)

SAME-DAY POST-FIX RE-RUN after merge of [#236](https://github.com/rafi-solibri/MyRepo/pull/236)
(`fix(indeed): fill bare Date and harden Title Mr SmartApply recovery`).
Ran on `main` @ `cf56100` with `POST_FIX_RERUN=1`. Resume: `resumes/Rafi_Resume.docx`.

## Counts (this re-run only — do not invent applies)

| Metric | Count |
| --- | ---: |
| **Submitted (Easy Apply)** | **6** |
| External ATS completed | 0 |
| Rejected incomplete | 6 |
| Blocked | 32 |
| Skipped | 46 |
| Seen | 90 |
| ok | true |

Source: `cloud-warp-uc`. Preflight exit 0 (`uc_bypass_cleared`). Session restored via `secure.indeed.com/settings/account`.

Morning cron ([bc-38397b17](https://cursor.com/agents/bc-38397b17-d8a3-414d-8802-43fb6b42c4f3)) already submitted 4 Easy Applies before the #236 merge (Experian EM, Aliqan Senior .NET, Mattel Data Architect, WSA Solution Architect). This re-run skipped those via `already_applied` (18 already-applied skips total).

## Submitted this re-run (Easy Apply)

1. **Ashra Technology** — Dell Boomi Architect (Hyderabad)
2. **Genpact India Pvt. Ltd.** — Architect - Enterprise Application - Oracle N 4D (Hyderabad)
3. **Genpact India Pvt. Ltd.** — Technical Architect 4C (Hyderabad)
4. **Mattel** — Solutions Architect - Enterprise (Hyderabad)
5. **TTEC Digital** — Solutions Architect- IP (Hyderabad)
6. **Task Staffing** — .Net Software Design Engineer (Hyderabad)

## Rejected incomplete (residual after #236)

- **ValGenesis** Senior Software Engineer, Fullstack — education "India - Standard"
- **ValGenesis** Senior Software Engineer, Database — education "India - Engineer"
- **WSA APAC** Senior Platform Architect — "Are you based in"
- **UST** .Net Fullstack Developer — Phone No * + Date (shared wrap still poisoned Date)
- **Experian** Solutions Architect — contact-info "There was an error, please try again" (server/reCAPTCHA)
- **LTIMindtree** Senior Principal - Architecture — Title * Mr./Ms.

## Skipped / blocked (not invented)

- Skipped: already_applied 18, title_not_target 20, location 5, title_skip 2, no_apply_button 1
- Blocked: external_incomplete_or_timeout 9, easy_apply_recaptcha 9, SOCKS ATS helper 6, no_ats_form 5, CAPTCHA 2, ats_login_wall 1

Artifacts: `/opt/cursor/artifacts/indeed-daily-run.json`, `indeed-apply-report.json`.
