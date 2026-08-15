#!/usr/bin/env node
"use strict";
const assert = require("assert");
const {
  shouldSkipTitle,
  hasDotNet,
  isArchLeadTitle,
  parseNaukriCardLines,
} = require("./resume_and_filters");

assert.strictEqual(shouldSkipTitle("Solution Architect .NET"), false);
assert.strictEqual(shouldSkipTitle("QA Engineer"), true);
assert.strictEqual(shouldSkipTitle("AI Architect"), true, "pure AI title must skip");
assert.strictEqual(
  shouldSkipTitle("AI Architect .NET"),
  false,
  "AI Architect with .NET on title OK"
);
assert.strictEqual(
  shouldSkipTitle("Internet of Things Lead"),
  false,
  "intern must not match internet"
);
assert.strictEqual(hasDotNet("SA", "ASP.Net Core"), true);
assert.strictEqual(
  shouldSkipTitle("Aspire Systems - Solution Architect - Java (12-16 yrs)"),
  true,
  "Java-primary SA must skip"
);
assert.strictEqual(
  shouldSkipTitle("Full Stack Architect - MEAN Technologies"),
  true,
  "MEAN-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Solution Architect - Java/.NET"),
  false,
  "Java with .NET on title OK"
);
assert.strictEqual(
  isArchLeadTitle("Lead Software Engineer"),
  true,
  "Lead Software Engineer is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Senior Manager Software Engineering"),
  true,
  "Senior Manager Software Engineering is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Software Engineer Manager"),
  true,
  "Software Engineer Manager is senior apply title"
);
assert.strictEqual(
  isArchLeadTitle("Senior Manager - Technology"),
  true,
  "Senior Manager - Technology is senior apply title"
);
assert.strictEqual(
  shouldSkipTitle("SRE Engineering Manager"),
  true,
  "SRE-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Engineer - SRE"),
  true,
  "SRE suffix must skip"
);
assert.strictEqual(
  shouldSkipTitle("Appian Technical Lead - II"),
  true,
  "Appian-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Technical Lead - Network Operations"),
  true,
  "Network Operations lead must skip"
);
assert.strictEqual(
  shouldSkipTitle("Oracle Fusion Finance Solution Architect"),
  true,
  "Oracle Fusion SA must skip"
);
assert.strictEqual(
  shouldSkipTitle(
    "Oracle Cloud Infra Admin-Oracle DBA Cloud Architect-Manager"
  ),
  true,
  "Oracle DBA Cloud Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Data & AI Solution Architect"),
  true,
  "Data & AI SA without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal IS Architect, Anaplan"),
  true,
  "Anaplan-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Quality Solution Architect"),
  true,
  "Quality Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Immediate Hiring For Power Platform Architect"),
  true,
  "Power Platform must skip"
);
assert.strictEqual(
  shouldSkipTitle("Solution Architect - Gen AI - Life Sciences"),
  true,
  "Gen AI SA without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("AI Agent Architect ( Agentic AI Systems)"),
  true,
  "AI Agent Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Architect- AI ,ML"),
  true,
  "Principal Architect AI/ML without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Agentforce Technical Lead"),
  true,
  "Agentforce/Salesforce must skip"
);
assert.strictEqual(
  shouldSkipTitle("Principal Network Support Engineer"),
  true,
  "Network Support must skip"
);
assert.strictEqual(
  shouldSkipTitle(
    "Project Engineering Manager Substation (Civil & Structural)- Riyadh"
  ),
  true,
  "Civil/Structural EM must skip"
);
assert.strictEqual(
  shouldSkipTitle("QE Architect"),
  true,
  "QE Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Azure Data Engineering Manager"),
  true,
  "Data Engineering Manager without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Senior Manager - Attack Surface Reduction"),
  true,
  "Attack Surface / cyber primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Cyber Security Architect"),
  true,
  "Cyber Security Architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("TOSCA Automation Architect"),
  true,
  "TOSCA / test automation architect must skip"
);
assert.strictEqual(
  shouldSkipTitle("Embedded Technical Architect- SME"),
  true,
  "Embedded / firmware-primary must skip"
);
assert.strictEqual(
  shouldSkipTitle("Artificial Intelligence Architect"),
  true,
  "Artificial Intelligence Architect without .NET must skip"
);
assert.strictEqual(
  shouldSkipTitle("Senior Technical Consultant D365"),
  true,
  "Dynamics 365 / D365 must skip"
);
assert.strictEqual(
  shouldSkipTitle("Manager Cyber Architecture, OT & Engineering"),
  true,
  "Cyber Architecture must skip"
);
assert.strictEqual(shouldSkipTitle("Senior .NET Architect"), false);
assert.strictEqual(isArchLeadTitle("Dot Net Fullstack Developer"), false);

const homepageSalesforce = parseNaukriCardLines([
  "Salesforce",
  "3.9",
  "Software Product",
  "50001-100000 employees",
  "Senior Manager, Software Engineering",
  "Hyderabad",
  "Not Disclosed",
  "CRM, SCM, Coding, Scrum, Salesforce, Enterprise applications",
  "19d ago - On company site",
]);
assert.strictEqual(
  homepageSalesforce.role,
  "Senior Manager, Software Engineering",
  "homepage CTA-last cards must parse role"
);
assert.strictEqual(homepageSalesforce.location, "Hyderabad");
assert.strictEqual(homepageSalesforce.companySite, true);

const homepageQuick = parseNaukriCardLines([
  "Dysrupit India",
  "4.7",
  "IT Services & Consulting",
  "ServiceNow Solution Architect",
  "Remote",
  "Not Disclosed",
  "Servicenow, Servicenow Development, Solution Design, ITSM, Solution Architecting",
  "16d ago",
  "Quick apply",
]);
assert.strictEqual(homepageQuick.role, "ServiceNow Solution Architect");
assert.strictEqual(homepageQuick.location, "Remote");
assert.strictEqual(homepageQuick.quick, true);

const searchCtaFirst = parseNaukriCardLines([
  "Nagarro",
  "Quick apply",
  "Principal Engineer, Dotnet Fullstack (React)",
  "Remote",
]);
assert.strictEqual(
  searchCtaFirst.role,
  "Principal Engineer, Dotnet Fullstack (React)",
  "search CTA-then-role layout still works"
);
assert.strictEqual(searchCtaFirst.location, "Remote");
assert.strictEqual(
  isArchLeadTitle("Solution Architecture Apps & AI"),
  true,
  "Architecture titles count as arch/lead band"
);
console.log("resume_and_filters self-test OK");

