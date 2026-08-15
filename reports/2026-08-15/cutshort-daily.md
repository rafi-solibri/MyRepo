# Daily apply 2026-08-15 (post-fix re-run)

POST_FIX_RERUN=1 on merged `main` @ `2140d75` (`fix(ats): submit company-site applies instead of timing out on hops` #162).
Earlier original daily (`927d926`) also applied **0** (scanned 1191, pageSize=5 era). This re-run used the merged helpers (`pageSize=50`, Associate Technical Architect allow, `completeExternalPage`).

## Counts
- Scanned: **3212**
- Qualifying: **0**
- Applied: **0**
- Already: 0
- Failed/blocked (apply): 0
- External: 0
- Q answered: **0** | already-submitted: 33 | locked-empty: **323** | verify-empty: 0
- Awaiting listed: 359
- Failures (apply + locked-empty + verify-empty): **323**
- Same-day apply failures: **0** (locked-empty rows are historical API locks, not new applies)

## Skip taxonomy (classify)
`location=213` `no_tier_match=56` `skip_title=756` `ctc_under_35=1161` `exp_max_low=1026`

## Why 0 applies (not invented)
Login OK (CDP `:9222`, candidate dashboard live). Resume `Rafi_Resume.docx`.

Hyd/remote Architect / Tech Lead / EM / .NET cards exist, but **listed max CTC is 12–25 LPA** (e.g. Hyd Tech Lead 18L, Hyd Engineering Leader 25L, remote Technical Lead 18L, Partner Solutions Architect 12L). Prompt hard-skips listed max clearly under 35L.

`ctc>=35` + Hyd/remote leftovers are wrong-fit titles (Data Architect, Workday, ShopPay, PHP, pre-sales, MDM, Customer Success, CAD/CAM, audio/ML) — title-first skips, not apply inventory.

`matchesfor` personalized feed returned **0** results (API total_count=0). Skill waves `.NET`/`Azure` were thin (23 / 44).

No new code-fixable apply blocker. Did not loosen the 35L floor. Did not launch another post-fix re-run.

## Applied
_None_

## Failed applies
_None_
