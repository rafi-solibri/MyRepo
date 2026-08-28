# Naukri daily — 2026-08-28 (post-fix re-run after #280)

Automation: https://cursor.com/automations/003b88eb-909a-11f1-ba66-0e7d0216e441
This run: https://cursor.com/agents/bc-1bd1d183-5302-4260-a396-44be5e184a4a
Earlier morning run (without #280): https://cursor.com/agents/bc-f476e01f-b101-4a14-bad0-5cfeb06aec1b
Merged fix used: https://github.com/rafi-solibri/MyRepo/pull/280 @ `93e35d6`

`POST_FIX_RERUN=1`. First Naukri same-day re-run (cap 5). In-session pass 2 used local confirmation + architecting fixes (PR not yet mergeable from this token).

## Profile resume refresh (STEP 0)
- **ok** both passes — `profileUpdated: true`
- Resume: `resumes/Rafi_Resume.docx` (rebuilt from master, 20945B)
- Verify: **Uploaded today**
- Canonical CV restored at end of each pass: **ok**

Login: live CDP `nauk_rt`/`nauk_at` + homepage OK.

## Pass 1 (main @ #280, no local patches)
Helper: applied 0 / external 0 / blocked 1 / skipped 3087 / seen 213.

| Company | Role | Path | Result |
| --- | --- | --- | --- |
| Software Company / Recruise India Consulting | Engineering Manager | Naukri Quick Apply | Helper `apply_unconfirmed` (empty CTA). Live job page after run: **disabled dual-layer Applied**. Counted as applied (verified, not invented). |
| Clean Harbors | .Net Fullstack Tech Lead | — | `already_applied_detail` (not re-counted) |

#280 Workday phone/company fill was not exercised (no eligible Workday jobs).

## Pass 2 (local confirmation + architecting fix)
Helper: applied 1 / external 0 / blocked 1 / skipped 3099 / seen 226.

| Company | Role | Path | Resume | Result |
| --- | --- | --- | --- | --- |
| GERENT | card: Solution Architecting… / listing: Salesforce Principal Architect Practice Lead | Naukri Quick Apply | tailored `Rafi_Resume.docx` | **False apply** — CTA Applied. Homepage card omitted Salesforce; listing URL is Salesforce. |
| Accenture | Packaged/SaaS App Engineering Lead | company ATS | tailored `Rafi_Resume.docx` | Blocked: Accenture IJP B2C login / MFA (`external_incomplete_or_timeout`) |
| Highradius / Anlage / Rapidue | Hirist walls | hirist | — | `hirist_login_required_skip` (not hard-blocked) |
| Incedo | .Net Lead Immediate joiner | — | — | `skip_ctc_max_30` (< 35) |

## New code fixes this re-run
1. **Empty-CTA confirmation:** reload `job-listings` URL and treat disabled dual-layer as Applied (`disabledCtaMeansApplied`).
2. **Architecting titles:** `ARCH_LEAD_RE` matches `architecting` (GERENT card was skip_no_dotnet on pass 1).
3. **Listing-title skip:** `titleFromNaukriJobUrl` + detail `h1` → `skip_title_listing` so a generic homepage card cannot burn a Salesforce/Coupa/Pega listing.

Do not invent further applies. Do not launch another cloud re-run until these commits are on `main` (would re-run #280-only code). Remaining cap: this is re-run 1 of 5; in-session pass 2 was not a cloud launch.
