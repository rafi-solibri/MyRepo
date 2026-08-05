# Application Playbook — >60 LPA | Hyderabad + Remote
**Last refreshed:** 2026-08-05 06:39 UTC cron

## Why applications were not submitted by the agent

Configured automation actions = **automation_memory** + **open_git_pr** (this repo). No LinkedIn, Naukri, email, Slack, or browser-login apply tools are attached. Submitting resume/PII to external ATS from this agent is **not an allowed delivery destination**.

**To enable auto-apply:** open https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441 and add job-board / authenticated browser / email + a Slack or email notification action. Provide LinkedIn/Naukri credentials as environment secrets if required.

## Manual apply checklist (60–90 min)

1. Export resumes to PDF (strip HTML comments / target notes):
   - `Rafi_Ahmed_Solutions_Architect_AWS_DotNet.pdf`
   - `Rafi_Ahmed_Solutions_Architect_Azure_DotNet.pdf`
   - `Rafi_Ahmed_Principal_Platform_Architect.pdf`
2. Apply Priority A in `SHORTLIST.md` (Deloitte×2, Experian, UHG×2, ServiceNow).
3. LinkedIn: headline + About below; Open to Work → Recruiters only.
4. Easy Apply 15–20 matching roles; paste matching resume each time.
5. Naukri: update resume → 10 product-MNC architect roles only.
6. Message 5–10 recruiters/HMs after each Priority A apply.
7. Log each submission in `tracker/APPLICATION_LOG.md`.

## LinkedIn

**Headline:**  
Solutions Architect | .NET Core • AWS • Azure • Microservices • Kafka | 15+ Yrs | Hyderabad / Remote | Open to Principal / Staff roles

**About:**  
Solutions Architect with 15+ years designing distributed, cloud-native platforms on .NET, AWS, and Azure. Recently architected 20+ microservices and 50+ APIs for multi-product platforms; previously led a 10-engineer healthcare platform at UnitedHealth Group. Seeking Principal/Staff Solutions Architect roles in Hyderabad or remote (India), target CTC 60 LPA+.

## ATS practices baked into resume variants

- Title mirrors JD (Solutions Architect / Principal)
- First third packs JD keywords naturally
- Metrics first: 20+ services, 50+ APIs, 20% perf, 20% cost, 87.5% deploy improvement, team of 10
- Last ~10 years detailed; earlier roles compressed
- No CTC on resume; forms: “60 LPA+ fixed, negotiable on TC”

## CTC negotiation (>60 LPA)

- Anchor on **TC** (base + bonus + RSUs/joining).
- First screen: “Targeting **60 LPA+ fixed**, flexible on structure if TC is competitive.”
- Walk from caps at 40–45 unless ESOP/TC clearly crosses 60.
- Best band clearance: Experian, ServiceNow Staff, Microsoft, Amazon Principal, Verisk product architect; Deloitte senior SA if negotiated hard.
- Skip posted 30–35 LPA (e.g. Crew Kraftorz).

## Interview prep focus

1. Multi-tenant partner API platform — AWS vs Azure trade-offs  
2. Kafka vs RabbitMQ vs Service Bus for payments/POS  
3. Story: 20% cost reduction — what changed  
4. Story: 2h → 15m CI/CD  
5. Architecture review conflict + mentoring without authority  
6. UHG return narrative (why back / what changed since 2023)

## High-ROI certifications (optional)

- AWS Solutions Architect Associate/Professional  
- Azure Solutions Architect Expert (AZ-305)
