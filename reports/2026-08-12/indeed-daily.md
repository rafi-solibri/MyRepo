# Indeed daily — 2026-08-12

Source: cloud WARP + SeleniumBase UC (`cloud-warp-uc`)  
Resume: `resumes/Rafi_Resume.docx` (Expected 65 LPA / Current 52 LPA; Hyd + Remote)

## Totals

| Metric | Count |
| --- | ---: |
| Applied (Easy Apply submitted) | 9 |
| External ATS completed | 0 |
| Rejected / incomplete | 8 |
| Blocked (reCAPTCHA) | 2 |
| Skipped | 27 |
| Seen (unique across sessions) | 46 |

Preflight: WARP SOCKS + UC Turnstile clear → **exit 0** (`uc_bypass_cleared`). Logged in as Mohammed.

## Applied (Easy Apply)

1. **Innobiz** — Software Engineer – .NET Core, Angular & Azure (contract) — Gopanpalli
2. **Recruise** — Senior Software Engineer - .Net — Hyderabad
3. **JUARA IT SOLUTIONS** — Technical Solution Architect – ERP Architect — Hyderabad
4. **Fairground** — Technical Lead — Hyderabad
5. **Acads360 India Private Limited** — Technical Lead - Angular Fullstack — Hyderabad
6. **SmartDocs** — Engineering Manager — Hyderabad
7. **Hire3global** — Engineering Manager — Hyderabad
8. **Hire3 Labs** — Engineering Manager AI SaaS — HITEC City, Hyderabad
9. **Acads360 India Private Limited** — Sr. Software Engineer - Full Stack (.Net) — Hyderabad

## Blocked

- Google reCAPTCHA Enterprise audio rate-limit on review (no CapSolver/2Captcha secrets): SR Private Ltd (.NET Senior Developer AI-Augmented); Two95 (.Net Developer with PLANISWARE). Marked `easy_apply_recaptcha` and continued.

## Rejected / incomplete (sample)

Demographic / voluntary self-ID validation walls (e.g. Mattel privacy acks, TechVedika, Egnify, Axiado, CENTROID, ProArch) — CTA sometimes clicked without navigation when required selects remain empty.

## Code fixes (branch `cursor/indeed-fix-recaptcha-submit-c8ce`)

- Stop 240s reCAPTCHA audio cooldown sleeps that hung `review-module`.
- GUI-click Submit when captcha already cleared.
- Match **Review your application** + tick privacy/ack checkboxes.
- Abort when the same CTA repeats on the same module (demographic stuck loop).

PR: branch pushed; `gh pr create` failed (`Resource not accessible by integration` — token read-only). Owner: open/merge PR from that branch, or re-run `bash scripts/auto-merge-fix-pr.sh` with write creds.

## Artifacts

- `/opt/cursor/artifacts/indeed-daily-run.json`
- `/opt/cursor/artifacts/indeed-preflight.json`
- `/opt/cursor/artifacts/indeed-cf-bypass.png`
- `/opt/cursor/artifacts/indeed-uc-apply2.log`
