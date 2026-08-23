# Hitech City / Knowledge City daily — 2026-08-23 (post-fix re-run)

Same-day `POST_FIX_RERUN=1` after merged [#243](https://github.com/rafi-solibri/MyRepo/pull/243) (`0d0f5ed` skip Optum on LinkedIn + harden `f_C`). Pulled `origin/main`, then ran careers-only with 10 parallel tabs. Resume: `resumes/Rafi_Resume.docx`. Success = confirmation text only. No invented applies.

## Totals (confirmation only)
- **Submitted: 0**
- Referrals: 0 (LinkedIn phase skipped — careers-first; do not wait on LinkedIn CAPTCHA)
- Boards: skipped (careers-only)
- Discovery: 92 campus tenants (0 added)

## Careers passes
| Pass | Result |
| --- | --- |
| 1 (merged #243 only) | 0 applied / 6 blocked / 14 skipped. Almost every scan `jobCount=0` (Hyland iframe + title-only Hyd cards dropped). |
| 2 (extract + listing Hyd bias) | Hyland/.NET opened then **false-skipped** in `apply_job` (no `listingLoc`). Oracle Hyd roles reached ASK_OWNER then **`ats_otp_wall`**; fingerprint churn extended ASK_OWNER indefinitely until the process was stopped. |
| 3 (`listingLoc` + skip Oracle + persist_retry=0) | 0 `CHAT_NOTIFY SUBMITTED`. Hyland iCIMS **`owner_captcha_unsolved`** ×3 (wall cap) before Senior Software Architect - .NET. JPMC/Experian CAPTCHA, ModMed login, Blue Yonder post-nav city skip. IBM/GE ASK_OWNER incomplete. |

## Owner-only walls (not code-fixable)
1. Oracle careers email OTP (`Confirm Your Identity`)
2. Hyland / JPMC / AMD / Experian hCaptcha or bot wall (owner click; no paid solver)
3. ModMed / Gartner Workday Sign In
4. LinkedIn CAPTCHA — not waited (careers-first instruction)

## Code fixes shipped this re-run (feature branch)
1. Rank `icims_content_iframe` by name; Hyd listing apply-bias for title-only cards
2. Honor `listingLoc` in `apply_job` pre-nav and top-card checks
3. ASK_OWNER fail-fast on `ats_otp_wall` + cap progress-extends
4. Skip Performance-and-Scalability / Account Executive titles; sort `.NET` cards first so captcha walls do not burn the best match

Branch: `cursor/hitech-city-knowledge-city-daily-post-fix-re-run-2026-08-23-65d0`  
This is post-fix re-run **1 of 5** for this portal on 2026-08-23 IST. A further in-session Hyland-only pass can use fix (4) once pass 3 workers exit.

## Artifacts
- `/opt/cursor/artifacts/` campus daily JSON, careers JSON, apply logs, and chat JSONL from this re-run
