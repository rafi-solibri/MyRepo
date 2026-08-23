# Jobs portal daily — 2026-08-23 (post-fix re-run)

## Status
**Completed on merged #238.** Same-day post-fix re-run (`POST_FIX_RERUN=1`) applied with the view-title / Easy Apply timeout fix. Did not invent applies. Earlier morning run handed off with 0 submits.

## Totals
- Easy Apply submitted: **22** (confirmed “Application submitted”)
- External / ATS completed: **1** (NTT DATA confirmation)
- Easy Apply skipped: **718** | blocked: **9**
- External candidates queued: **52** → attempted **40** (submitted 1 / blocked 28 / skipped 11)
- Seen / dedup IDs persisted: **554**

## Login
- Preflight OK (`li_at` in source + CDP)
- Live CDP first paint was `/uas/login`; Google SSO auto-login → feed
- Seed refresh OK after SSO
- Restriction lift from 2026-08-20 (`2026-08-23T03:30:00Z`) already past

## #238 fix observed
- View-title / location revalidation skipped bait cards (Blackbaud “Laureate - .Net Architect”, Broadridge, Sharp Brains “India” without remote pill)
- `fill_inputs` time-cap fired instead of hanging (Quantum Integrators / several “exceeded Easy Apply steps”)

## Submitted (Easy Apply)

| Company | Role | Job id | Location |
| --- | --- | --- | --- |
| NCompas Technology Solutions Inc. | Senior Enterprise Solution Architect | 4455650102 | Hyderabad |
| Ibexlabs | Senior Solutions Architect – AI Solutions | 4454970033 | Hyderabad |
| Teradata | Staff Software Engineer | 4454236005 | Hyderabad |
| Mulya Technologies | Senior Software Architect | 4455277149 | Greater Hyderabad |
| BlitzenX | Sr Software Engineer | 4455049038 | Hyderabad |
| Chubb | Global Authentication Engineering Manager | 4457591813 | Hyderabad |
| CareerXperts Consulting | Technical Lead, Payments — Full Stack Engineering (Enterprise SaaS) | 4454600085 | Hyderabad |
| ShimentoX Technologies | Senior Solution Architect – Data & AI \| Databricks | 4457097946 | Hyderabad |
| Talent500 | Senior Software Engineer [T500-28573] | 4455266108 | Hyderabad |
| Teradata | Principal Architect | 4437991428 | Hyderabad |
| Deutsche Börse Group | LAVP - IAM Engineering Manager [T500-28783] | 4457305150 | Hyderabad |
| WillWare Technologies | Workday Extend Solution Lead / Architect | 4457087275 | Hyderabad |
| Tata Consultancy Services | APex Architect | 4456693953 | Hyderabad |
| ginfracon | Shop Floor Precision Engineering Manager | 4451200625 | Hyderabad |
| Deutsche Börse Group | LAVP - Security Automation Engineering Manager [T500-28716] | 4453457452 | Hyderabad |
| Talent500 | Senior Manager, .Net Engineering [T500-28581] | 4455257744 | Hyderabad |
| Mulya Technologies | STA Lead Engineer | 4455279550 | Greater Hyderabad |
| Tata Consultancy Services | Coveo Search Architect | 4455234873 | Hyderabad |
| Chubb | SRE Lead Engineer | 4455577581 | Hyderabad |
| Tech Mahindra | Senior Software Engineer | 4443251675 | Hyderabad |
| Kanerika Inc | QE Architect | 4454240217 | Hyderabad |
| Arcesium | Business Solutions Architect | 4456700256 | Hyderabad |

## Submitted (external ATS)

| Company | Role | Job id | ATS |
| --- | --- | --- | --- |
| NTT DATA, Inc. | Senior Application Architect | 4409294028 | careers.services.global.ntt (confirmation) |

## Blocked (Easy Apply)
- 4450592955 Flow Interio Junior Architect — modal did not open
- 4452921719 Quantum Integrators Data Integration Architect — time-cap
- 4452183255 Quantium Engineering Lead — exceeded steps
- 4456200424 Seosaph-infotech Principal Solution Architect - Data, Azure & AI — exceeded steps
- 4437981573 Sonatype Staff Software Engineer - Agentic First — exceeded steps
- 4446738839 Sonatype Senior HR Systems Architect — exceeded steps
- 4452221934 Tech Mahindra Technical Architect — exceeded steps
- 4456674027 CG-VAK Senior Python Developer / Architect – AWS — exceeded steps
- 4437997176 Sonatype Staff Info Sec AI Researcher — exceeded steps

## External ATS
- Completed: **1** (NTT DATA)
- Blocked: Workday/company login walls, CAPTCHA/bot, incomplete/timeout (Palo Alto, Convatec, ModMed, Microsoft, Infosys, micro1, etc.)
- Artifacts: `/opt/cursor/artifacts/apply-report.json`, `/opt/cursor/artifacts/external-apply-report.json`

## False-allow suspects (submitted; filter tightened this re-run)
- Shop Floor Precision Engineering Manager (ginfracon `4451200625`) — manufacturing, not software EM
- STA Lead Engineer (Mulya `4455279550`) — static timing / semiconductor
- QE Architect (Kanerika `4454240217`) — quality, not software architect
- Senior Solution Architect – Data & AI \| Databricks (ShimentoX `4457097946`) — data/AI title, no .NET
- SRE Lead Engineer (Chubb `4455577581`) — SRE (blacklist had only `sre engineer`)
- APex Architect (TCS `4456693953`) — possible Salesforce/Oracle Apex (left as suspect; not auto-blacklisted)
- Coveo Search Architect / Workday Extend — adjacent product platforms; left allowed

Also skipped-by-location but title should have rejected earlier: Junior Architect, Principal DFT Engineer, BIM Architect, Architectural Designer.

## Code fix this re-run
- Title filters + unit tests: shop floor / precision, STA/DFT, QE/quality architect, junior/BIM/architectural designer, SRE word, Data&AI/Databricks without .NET
- Issues log updated under automation-prompts/issues/

## Notes
- HTTP 999 on search restore after apply still burns remaining cards on that page (existing 3-retry backoff). Not a hard stop; later titles continued.
- Inventory after 14-day expand was mostly already-applied / wrong-stack / external.
- Agent: https://cursor.com/agents/bc-902b0e1a-8586-4ff5-9a72-c4c34e6e1199
- Merged prior fix: https://github.com/rafi-solibri/MyRepo/pull/238
