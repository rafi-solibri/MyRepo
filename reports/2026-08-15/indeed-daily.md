# Indeed daily — 2026-08-15 (post-fix re-run on #162)

## Status
**Blocked this session — false `indeed_login_required` after CF clear.**
Preflight WARP+UC exited 0. Apply on merged `2140d75` (#162 ATS hops) did not invent applies.

## This re-run (bc-e05fed1a, main + #162)
- Preflight: **ok** (`uc_bypass_cleared`, WARP SOCKS `127.0.0.1:40000`)
- Resume: `/workspace/resumes/Rafi_Resume.docx`
- Session cookies present (`hasAuth=true`, Passport bearer + CTK)
- Homepage after Turnstile: anonymous **Get Started** / Sign in
- Homepage reload alone did not paint Welcome
- Counts: applied 0 / external 0 / seen 0 / skipped 0 / blocked 1 (`indeed_login_required`)

## Code fix this run
Morning apply on an unmerged branch already proved the warmup:
open `https://secure.indeed.com/settings/account` then return home so Welcome paints.
That change never reached `main` (`gh createPullRequest denied`).

Landed here:
- `warm_passport_session()` after signed-out homepage
- copy `Local State` + `First Run` into the hybrid UC profile
- `signed_out_home()` unit test

Do not treat this as missing cookies. Same seed worked after settings warmup earlier today.

## Same-day re-run
After this fix merges, `scripts/auto-merge-fix-pr.sh` / `rerun-daily-after-fix.sh` launches the next Indeed job (cap 5). Skip jobs already submitted today.
