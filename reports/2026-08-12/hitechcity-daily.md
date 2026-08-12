# Hitech City / Knowledge City daily 2026-08-12

## Counts
- Applied (confirmed): **0**
- Referrals sent: **0** (19 attempted; Connect CTA skipped / people-search soft-fails)
- LinkedIn blocked: **16** (ATS incomplete 11, HTTP throttle 3, Easy Apply reCAPTCHA 1, CAPTCHA 1)
- LinkedIn skipped: **217** (title_not_senior 143, ext_wall/attempt caps 26, location 16, wrong_title_stack 7, …)
- Careers blocked: **7** (Amazon login wall 3, Qualcomm reCAPTCHA 3, Optum incomplete 1)
- Careers skipped: **8** (non-Hyd / Romania-Bucharest / missing Hyd signal)
- Careers scanned: **18** company portals
- Resume: `resumes/Rafi_Resume.docx` | CTC **52 → 65 LPA** | notice 0
- Artifacts: `/opt/cursor/artifacts/hitechcity-daily.json`, `hitechcity-daily-run.json`, `hitechcity-linkedin.json`, `hitechcity-careers.json`

## Applied
None confirmed (Application submitted / ATS confirmation). Do not invent applies.

## Campuses targeted
Sattva Knowledge City / Knowledge Park, Mindspace Madhapur, The V, Cyber Pearl, DLF Cyber City, Divyasree Orion — via `tools/hitechcity/companies.json` tenants (Microsoft, Amazon, Apple, AMD, Blackbaud, Blue Yonder, Experian, GE Vernova, Goldman Sachs, Hyland, Intel, JPMorgan, Meta, ModMed, Optum, Oracle, Palo Alto, Qualcomm, …).

## Blockers (owner)
- LinkedIn Easy Apply **reCAPTCHA** (AMD Director AI Systems)
- Qualcomm careers **reCAPTCHA** on Hyd apply (`careers.qualcomm.com/.../apply`)
- Amazon **passport / login** wall on Solutions Architect applies
- LinkedIn intermittent `ERR_HTTP_RESPONSE_CODE_FAILURE` (mitigated with `goto_retry`; still some view failures)

## Code fixes shipped (`cursor/hitechcity-daily-apply-c8ce`)
- CAPTCHA iframe detect before ATS fill; drop bare `[data-sitekey]` false walls
- Per-company EXT wall + attempt caps (stop Phenom/Blackbaud grind)
- Top-card-only LinkedIn location; empty loc → apply bias
- `LI_TITLE_SKIP` for Product Manager / GPU / Network Architect / RTL / etc.
- LinkedIn `goto_retry` backoff; Easy Apply 120s time cap + recaptcha reason
- Careers `BAD_LOC_HINT`: United Kingdom / Berkshire / Reading / Romania / Bucharest

## PR / merge
Branch pushed: `cursor/hitechcity-daily-apply-c8ce`. `gh pr create` failed (`Resource not accessible by integration` — gh read-only here). Ready for parent/ManagePullRequest + `bash scripts/auto-merge-fix-pr.sh`.
