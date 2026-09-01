# LinkedIn daily — 2026-09-01 (post-fix re-run)

## Status
**Completed applies** on live session from merged `#306` seed. **23** confirmed Easy Applies (none invented). LinkedIn then hit **Easy Apply daily limit**. External ATS pass: **0** confirmed (23 blocked / 17 skipped — login walls, CAPTCHA, timeouts).

## Login
- First CDP launch on `#305` (`6c3961b`): stale `li_at` → Google `/challenge/pwd` misclassified as 2FA (300s) → LinkedIn password → Security Verification / reCAPTCHA.
- Restored `#306` portal-session seed with `FORCE_RESTORE_SESSIONS=1` + `LINKEDIN_AUTO_LOGIN=0`. Live check: `ok`, `/feed/`, `has_li_at`.
- `GOOGLE_PASSWORD` still unset in Cloud secrets. Do not copy `LINKEDIN_PASSWORD` into it.

## Submitted (Easy Apply, confirmed “Application submitted”)
| Company | Role | Job id | Location |
| --- | --- | --- | --- |
| Kandou AI | Customer Platform, SDK & Interoperability Architect | 4461040544 | Greater Hyderabad |
| ValueLabs | Solutions Architect | 4460020137 | Hyderabad |
| TCS | Walk in - Azure Solution Architect - Hyderabad | 4461061351 | Hyderabad |
| TCS | LeanIx Technical Architect | 4459794172 | Hyderabad |
| OvalEdge | Senior Technical Architect | 4458076988 | Hyderabad |
| Getrosoft | Senior Full Stack Developer (Tech Lead) | 4460236058 | Hyderabad |
| Marriott Tech Accelerator | Engineering Manager [T500-29023] | 4461067965 | Hyderabad |
| FMR Enterprises | Senior Software Engineer, AI Training & Evaluation (Remote, Contract) | 4458457964 | Remote India |
| Synthires | Senior Software Engineer (Remote \| $100–$150/hr) | 4456511072 | Remote India |
| SkillDzire | Business Development Manager | 4459285052 | Hyderabad — **false apply** |
| W Design Studio | Business Development Manager | 4459275798 | Hyderabad — **false apply** |
| AAA Global | Principal Manager, (Portfolio Data Services) – Core Tech | 4461571543 | Hyderabad |
| Religent Systems | Technology Architect – Axway API Management | 4457229887 | Hyderabad |
| Kandou AI | Customer Platform, SDK & Interoperability Architect | 4461065835 | Greater Hyderabad |
| Kandou AI | Program Director | 4457837168 | Greater Hyderabad |
| Realpage | Architect | 4459282509 | Hyderabad |
| Marriott Tech Accelerator | Senior Software Engineer I [T500-29058] | 4461563982 | Hyderabad |
| Playroom Early Learning Systems | Architect | 4458498244 | Hyderabad — suspect building |
| Flow Interio | Junior Architect | 4450592955 | Hyderabad — **false apply** |
| Waterleaf Architects | Junior Architect | 4456594297 | Hyderabad — **false apply** |
| Grid Dynamics | Dotnet Developer | 4460245446 | Hyderabad |
| Arth | Senior BIM Architect - Arch | 4457905817 | Hyderabad — **false apply** |
| Olympus | IT Infrastructure Solution Architect, Cloud & Datacenter, Global | 4460240582 | Hyderabad |

## Totals
| Path | Count |
| --- | --- |
| Easy Apply submitted | **23** |
| External / ATS completed | **0** (23 blocked, 17 skipped) |
| Easy Apply skipped | 661 (already applied, title/location, etc.) |
| Easy Apply blocked | 6 (5 step-cap + 1 daily limit) |

## External ATS
Tried 34 company-site hops. None reached ATS confirmation. Typical: Workday `ats_login_wall`, Greenhouse/generic timeout, CAPTCHA/bot wall. Resume: `Rafi_Resume.docx` tailored per job.

## Code fixes (this re-run)
1. `tools/google_2fa_prompt.py` — `/challenge/pwd` is **not** 2FA
2. `tools/linkedin/auto_login.py` — heal **password first**; identifier URL is not all `/signin/challenge`
3. `scripts/load-job-secrets.sh` — do **not** copy `LINKEDIN_PASSWORD` → `GOOGLE_PASSWORD`
4. `tools/linkedin/filters.py` — skip BDM (`development manager` substring), Junior/intern/fresher, BIM

Branch: `cursor/linkedin-fix-google-pwd-not-2fa-a239` (pushed). `gh pr create` returned 403 (integration token); ManagePullRequest registered for owner approval.

## Owner action
1. Approve/create the fix PR and squash-merge to `main`
2. Set Cursor secret **`GOOGLE_PASSWORD`** separately from **`LINKEDIN_PASSWORD`**
3. Headed login if Security Verification returns: `bash scripts/home-headed-login.sh linkedin`

## False-skip / false-apply
- **False applies (fixed in this branch):** BDM, Junior Architect, BIM Architect
- **Suspects:** Playroom Early Learning “Architect”; FMR AI Training contract; Synthires high-rate SSE
- Inventory after 24h was thin; 3d/7d/14d added more. Stopped at 23 because LinkedIn Easy Apply daily limit, not because inventory was empty.
