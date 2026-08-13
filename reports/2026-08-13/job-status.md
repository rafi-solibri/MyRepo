# Job status — 2026-08-13

Manual all-portals rerun on cloud agent [bc-7b7a3ecb-b7e8-4bc9-8b24-2ae739e5ba56](https://cursor.com/agents/bc-7b7a3ecb-b7e8-4bc9-8b24-2ae739e5ba56) after the 9 AM IST automations.

Targets: Expected CTC **65 LPA**; Hyderabad + Remote/WFH; resume `Rafi_Resume.docx`.

**Totals this rerun:** applied **63** · external opened **7** · rejected **3** · blocked **83** · skipped **3481**.

## Portal results

| Portal | Applied | External | Rejected | Blocked | Skipped | OK | Blocker |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| LinkedIn | 0 | 0 | 0 | 1 | 0 | no | CAPTCHA / Security Verification (`/checkpoint/challenge`) after WARP + Google SSO |
| Foundit | 0 | 0 | 0 | 0 | 501 | yes | Logged in; 43 already-applied duplicates; inventory exhausted |
| Cutshort | 0 | 0 | 1 | 0 | 0 | no | Logged in; scanned 1981; qualifying=0; `q_locked_empty=322` |
| Naukri | 60 | 0 | 0 | 58 | 2294 | yes | Profile resume **Uploaded today**; hit MAX_APPLIES=60; 53 `apply_unconfirmed`; 5 ATS timeouts |
| Instahyre | 2 | 0 | 0 | 0 | 673 | yes | — |
| Indeed | 1 | 7 | 2 | 0 | 12 | yes | WARP+UC Turnstile cleared; Easy Apply submitted |
| Hitech City | 0 | 0 | 0 | 23 | 19 | no | LinkedIn CAPTCHA; careers: Amazon passport + Experian/AMD CAPTCHA |

## Confirmed applies (do not invent)

**Naukri Quick Apply (60)** — includes:

- Nagarro — Principal Engineer - Dotnet Full stack Architect (Remote)
- Big 4 / Anlage Infotech — Dot Net-Engineering Manager (Hyd)
- Camp Systems — Technical Lead (Hyd)
- Fission Labs — Lead Developer (.NET and Python) (Jubilee Hills)
- Coforge — Specflow C# Lead
- Valuelabs — Azure Platform Developer/Architect (Remote)
- Koantek — Azure Solution Architect (Remote)
- Virtusa — Cloud Solution Architect
- Plus other Hyd/remote Architect / Tech Lead / EM Quick Applies (title-first). Some titles are stretch (Shopify/Optical/D365/SoC) — title-first bias, not invented.

**Instahyre (2)**

1. Goldman Sachs — Backend Engineer — Bangalore,Hyderabad — `application_sent`
2. Everest Fleet — Backend Engineer — Work From Home — `application_sent`

**Indeed Easy Apply (1)**

1. Workato — Principal Technical Architect — Hyderabad — `submitted`

**Indeed external opened (not completed):** BytesEdge, Absyz, QualiZeal, Lexicon Infotech, CGLIA, Codebees.

## Owner actions (not code-fixable)

1. Headed LinkedIn login: `bash scripts/home-headed-login.sh linkedin` (CAPTCHA checkpoint). Then Save environment snapshot.
2. Optional: Amazon.jobs / Experian SmartRecruiters / AMD headed sessions for Hitech City careers.
3. Cutshort 322 locked-empty questionnaires cannot be unlocked in code.

## Morning automations (already IDLE before this rerun)

LinkedIn, Foundit, Cutshort, Naukri, Instahyre, Indeed, Hitech City, Notification all ran at ~9 AM IST and merged filter/CDP fixes (#119–#131). This session re-executed the durable apply helpers on latest `main`.

Notification email sent via Resend MCP to rafi.success@gmail.com — id `379985d4-95b2-43e7-93dc-1ceec7850c26`. From = `Job Status <onboarding@resend.dev>` (verified domain sender not configured).
