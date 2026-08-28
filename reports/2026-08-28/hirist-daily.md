# Hirist daily — 2026-08-28 (post-fix re-run after #282)

- Agent: https://cursor.com/agents/bc-26917e39-3057-43df-87c2-b754a268f051
- Head: `05787d4` `fix(hirist): Gmail password fill + hirist_seeker_enc session (#282)`
- Login: `hirist_seeker_enc` on `/home/ubuntu/chrome-hirist-profile` — `login_ok url=https://www.hirist.tech/jobfeed` (no Google SSO needed this run)
- Resume: `/workspace/resumes/Rafi_Resume.docx` (52 → 65 LPA)
- Runner: `node tools/hirist/daily_apply.js` via CDP :9222 — **exit 0**, not invented

## Counts

| applied | external | rejected | blocked | skipped | seen | candidates |
| ------: | -------: | -------: | ------: | ------: | ---: | ---------: |
| **40**  | 0        | 0        | 0       | 389     | 497  | 108        |

Hit `HIRIST_MAX_APPLIES=40`. Remaining 68 eligible candidates left unapplied because of the cap (not skipped by filters). All 40 were in-app `POST /job/apply-multiple` (`hirist_apply`). No company-ATS redirects in this batch.

## Skip reasons

| n | reason |
| ---: | --- |
| 262 | location_not_hyd_remote |
| 44 | pure_ai_data_without_dotnet |
| 31 | java_primary |
| 22 | wrong_stack_title |
| 21 | generic_engineering_without_dotnet_cloud |
| 2 | qa_quality_engineering |
| 2 | exp_max_5 |
| 2 | frontend_without_dotnet |
| 1 | already_applied_or_closed |
| 1 | ctc_max_28 |
| 1 | junior_title |

One already-applied skip: Talkdesk Solution Architect / Hurix Digital.

## Applied (40, confirmed Hirist in-app)

1. Engineering Manager - Java/.Net — Adecco Group — https://www.hirist.tech/j/engineering-manager-java-net-1645840
2. Techgrit - .Net Development Lead/Technical Lead — TechGrit — https://www.hirist.tech/j/techgrit-net-development-leadtechnical-lead-1652340
3. Senior Tech Architect & Product Manager — GoodPeople Consulting LLP — https://www.hirist.tech/j/senior-tech-architect-product-manager-1652998
4. Technical Architect  - .Net — Tidyhire — https://www.hirist.tech/j/technical-architect-net-8-15-yrs-1660067
5. Engineering Manager — Seventh Contact Hiring Solutions — https://www.hirist.tech/j/engineering-manager-1651528
6. Engineering Manager — Time Hack Consulting — https://www.hirist.tech/j/engineering-manager-1659705
7. Senior Solution Architect - Google Cloud — HR Works Consultancy — https://www.hirist.tech/j/senior-solution-architect-google-cloud-1660936
8. Senior Solution Architect - Google Cloud — Talent Pro — https://www.hirist.tech/j/senior-solution-architect-google-cloud-1660850
9. Senior Principal Engineer - Validation — Randstand — https://www.hirist.tech/j/senior-principal-engineer-validation-1651273
10. Senior Staff Software Engineer - IoT Projects — Watson Search Partners — https://www.hirist.tech/j/senior-staff-software-engineer-iot-projects-1663997
11. Solution Architect - Data Engineering — Avisoft — https://www.hirist.tech/j/solution-architect-data-engineering-1666215
12. Solution Architect - Data Engineering — HiringBlaze — https://www.hirist.tech/j/solution-architect-data-engineering-8-12-yrs-1663700
13. Presales Solution Architect — Agile Ventures — https://www.hirist.tech/j/presales-solution-architect-1663578
14. Digital Solution Architect - Azure/AWS — Lykora Consulting Services — https://www.hirist.tech/j/digital-solution-architect-azureaws-1665319
15. Cloud Solution Architect - Data & AI — Clarus- Impact Network — https://www.hirist.tech/j/cloud-solution-architect-data-ai-1665273
16. Solution Architect - AWS Cognito — Ai Adept Consulting — https://www.hirist.tech/j/solution-architect-aws-cognito-1658903
17. AI Solution Architect — The Reliable Jobs — https://www.hirist.tech/j/ai-solution-architect-1660429
18. Solution Architect - Microsoft Dynamics 365 — Digivance Solution — https://www.hirist.tech/j/solution-architect-microsoft-dynamics-365-1657804
19. Solution Architect - Azure — HumanXcel — https://www.hirist.tech/j/solution-architect-azure-1654890
20. AI Solution Architect — Pylon Management Consulting — https://www.hirist.tech/j/ai-solution-architect-1656218
21. Azure Databricks Architect - Apache Spark — Vy Systems — https://www.hirist.tech/j/azure-databricks-architect-apache-spark-1657323
22. Technical Architect - Artificial Intelligence — Pacemaker — https://www.hirist.tech/j/technical-architect-artificial-intelligence-1665411
23. Azure Solution Architect — ResourceTree Global Services Pvt Ltd — https://www.hirist.tech/j/azure-solution-architect-10-12-yrs-1650206
24. Cloud Architect - Azure — Strategic HR Solutions — https://www.hirist.tech/j/cloud-architect-azure-1663501
25. Azure DevOps Architect - CI/CD Pipeline — Coders Brain — https://www.hirist.tech/j/azure-devops-architect-cicd-pipeline-1652626
26. Azure Solution Architect - Data Platform — ResourceTree Global Services Pvt Ltd — https://www.hirist.tech/j/azure-solution-architect-data-platform-8-12-yrs-1650207
27. Technical Architect - Generative AI — ResourceTree Global Services Pvt Ltd — https://www.hirist.tech/j/technical-architect-generative-ai-1651553
28. Lead Diagnostic Software Engineer - C#/.Net — Basebiz Private Limited — https://www.hirist.tech/j/lead-diagnostic-software-engineer-c-net-1665900
29. Software Architect - MLOps Platform — Whitetable — https://www.hirist.tech/j/software-architect-mlops-platform-5-10-yrs-1643431
30. Lead .Net Full Stack Developer — Acharya Consulting Services and Sales — https://www.hirist.tech/j/lead-net-full-stack-developer-10-14-yrs-1655920
31. Candescent - Principal Engineer - Check Imaging Services — Grassik Search — https://www.hirist.tech/j/candescent-principal-engineer-check-imaging-services-1666570
32. Principal Engineer - Assisted Banking Platform — Watson Search Partners — https://www.hirist.tech/j/principal-engineer-assisted-banking-platform-1664505
33. Principal Backend Engineer - Python — Kairahire Solutions — https://www.hirist.tech/j/principal-backend-engineer-python-1652716
34. First American - Staff Engineer - AWS/Azure — First American (India) — https://www.hirist.tech/j/first-american-staff-engineer-awsazure-1657256
35. Cloud Solutions Architect - Azure — TechStar Group — https://www.hirist.tech/j/cloud-solutions-architect-azure-1663362
36. Cloud Architect - AWS/Azure/Google Cloud Platform — Michael Page International — https://www.hirist.tech/j/cloud-architect-awsazuregoogle-cloud-platform-1661772
37. Smart IMS - Cloud Architect - Azure Platform — Smart IMS — https://www.hirist.tech/j/smart-ims-cloud-architect-azure-platform-1661970
38. Saxon Global - Cloud Solution Architect - Azure — Saxon Global — https://www.hirist.tech/j/saxon-global-cloud-solution-architect-azure-1659578
39. Sonata Software - Cloud Architect - Azure — SONATA SOFTWARE LTD — https://www.hirist.tech/j/sonata-software-cloud-architect-azure-1642882
40. Azure Cloud Architect — ADP Private Limited — https://www.hirist.tech/j/azure-cloud-architect-1642196

## Blocked

None. Earlier same-day run without #282 hung on Gmail password / missed `hirist_seeker_enc`. This re-run used merged main and applied.

## Automation UUID (now live)

https://cursor.com/automations/566599f1-a2a4-11f1-b532-320a589b8025 — **Hirist Daily 9 AM** (enabled). Wired into `09-hirist.md`, `07-notification.md`, `ONE_TIME_LOADERS.md`, and `scripts/rerun-daily-after-fix.sh`.

Artifact: `/opt/cursor/artifacts/hirist-apply-report.json` (copy: `reports/2026-08-28/hirist-apply-report.json`)
