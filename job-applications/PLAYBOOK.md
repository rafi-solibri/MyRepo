# Application Playbook — >60 LPA | Hyderabad + Remote
**Last refreshed:** 2026-08-06 03:30 UTC cron

## Why applications were not submitted by this agent
Configured delivery for this automation = git PR (`open_git_pr`) + `automation_memory`. No LinkedIn/Naukri/browser-apply MCP. Chrome portal cookies on this cold VM are encrypted / incomplete (LinkedIn lacks `li_at`; Naukri absent). Owner must manually apply, or finish portal login + environment snapshot + attach apply MCP.

## Manual apply (60–90 min)
1. Export 3 PDF resumes from `job-applications/resumes/` (strip HTML comments / TARGET ROLE NOTES).
2. Also keep canonical `resumes/Rafi_Resume.docx` for ATS uploads.
3. Apply Priority A in `SHORTLIST.md` order with matching cover from `cover-letters/COVER_LETTERS.md`.
4. LinkedIn Open to Work (recruiters only) + Easy Apply ×15–20.
5. Naukri: re-upload resume for freshness, then ×10 product MNCs only.
6. Log each submit in `tracker/APPLICATION_LOG.md`.

## ATS / resume best practices used in variants
- Lead with role title matching JD (AWS SA / Azure SA / Principal Platform).
- Mirror JD keywords naturally (AKS, APIM, Service Bus, Kafka, microservices, REST/JSON).
- Put quantified outcomes near the top (20+ services, 20% perf/cost, 87.5% deploy cut, team of 10).
- Keep contact + location + Hyderabad/Remote on line 1–2.
- One page preferred for India product ATS; two pages OK for Principal stretch.
- Never claim ServiceNow CSM / Fabric / Snowflake depth you do not have — cover letter bridges gaps.

## LinkedIn
**Headline:** Solutions Architect | .NET Core • AWS • Azure • Microservices • Kafka | 15+ Yrs | Hyderabad / Remote | Open to Principal / Staff roles  
**About:** Solutions Architect with 15+ years designing distributed, cloud-native platforms on .NET, AWS, and Azure. Recently architected 20+ microservices and 50+ APIs; previously led 10-engineer healthcare platform at UHG. Seeking Principal/Staff SA roles Hyd/remote India, CTC 60 LPA+.

## CTC script
“Targeting **65 LPA fixed**, flexible on structure if TC is competitive. Current **52 LPA**.” Walk from 40–45 caps unless TC clearly ≥60. Best clearance: Experian, ServiceNow Staff/Principal, Microsoft, Amazon Principal, Verisk; Deloitte if negotiated hard; EPAM SA only with early band confirm.

## Interview prep (keep sharp)
1. Multi-tenant partner API — AWS vs Azure topology trade-offs  
2. Kafka vs RabbitMQ vs Service Bus (POS/payments concurrency)  
3. 20% cost reduction story (what you measured, what you changed)  
4. 2h→15m CI/CD story (Jenkins + K8s)  
5. Architecture review conflict / mentoring without authority  
6. UHG return narrative + why Solutions Architect next  
7. EPAM solutioning / SAD / workshop communication examples

## Owner unblockers for next cron auto-apply
1. Log into LinkedIn / Naukri / Foundit / Instahyre / Cutshort / Indeed in Desktop Chrome → Save environment snapshot  
2. Add secrets: `LINKEDIN_EMAIL`, `LINKEDIN_PASSWORD` (+ optional Naukri/Foundit/Instahyre)  
3. Attach browser/job-board apply MCP + notification channel on https://cursor.com/automations/30e2c023-9067-11f1-ba66-0e7d0216e441  
4. Optional: AWS SA Professional + AZ-305 for Experian/Deloitte/Microsoft signal
