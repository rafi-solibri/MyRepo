# Cutshort daily report — 2026-08-05 (cron run ~11:25 UTC)

## Counts (this run)
| Metric | Count |
|--------|------:|
| Scanned (unique jobs) | ~800+ |
| **Applied** | **11** |
| Already applied | 0 |
| Failed/blocked | 0 |
| Questionnaires fully filled (API) | 1 |
| Questionnaires locked empty (API mark-only) | 9 |
| Screening follow-up messages sent | 11 |
| Login required | No |

## Applied (newest → this session)
1. **FullStack Developer @ Recro** — remote_only, 55L (hide) — Tier 2
2. IAM Support Engineer @ Majoris — Hyderabad, 40L hide — weak IAM fit (.NET skill)
3. GCP Bigquery @ Leinex — Hyderabad — stretch/weak
4. Mac Administrator @ Techsophy — Hyderabad — weak (false “platform” tier match)
5. Python GCP @ Leinex — Hyderabad — stretch
6. Data Science Engineer @ J&F — remote_okay — GenAI stretch
7. Senior Product Manager - FDT @ KnackLabs — Hyderabad, 50L — weak PM fit (questionnaire **correctly filled**, pay No)
8. **FORWARD DEPLOYED ENGINEER (FDE) @ KnackLabs** — Hyderabad, 40L
9. **Sr Software Engineer @ Technogen** — Hyderabad, 40L
10. **Lead API Engineer @ Gradera** — Hyderabad, 40L
11. **Angular Developer, Java Full stack @ VY Systems** — Hyd/Bangalore — notice answered; pay Q empty (locked)

## Questionnaire notes
- Working `POST /update-message/{id}` shape (must use **before** `screeningSubmitted`):
  - Body includes `messageId`
  - Each question uses `"question": "<questionIdString>"` (not full object)
  - `responseStringArray: ["<optionId>"]`
  - Then submit with `screeningSubmitted: true`
- Posting full question objects + `screeningSubmitted:true` returns 200 but **persists empty answers** and locks further edits (400).
- For locked threads, sent chat follow-ups with explicit screening answers + 15–20 min call / HM referral ask.
- Salary “does this work?” → **No** when listed max &lt; 55 LPA (always state expected **65 LPA**).

## Inventory
- Tier-1 Solutions/Tech Lead/EM at Hyd/remote + ≥50L remains scarce.
- Best callback bets this run: Recro FullStack, Lead API Engineer, Sr Software Engineer, FDE.
- Weak applies (Mac Admin / GCP Bigquery / Python GCP / IAM / PM) came from overly broad tier matching; tightened for next run.

## Profile used
- 52 → **65 LPA**, Hyderabad/remote, immediate joinee
- Proof: Nemetschek/Solibri, Infosys, EPAM
